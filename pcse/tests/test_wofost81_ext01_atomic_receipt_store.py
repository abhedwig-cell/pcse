"""Research-only durable PCSE crop receipt+state transaction store.

The filesystem journal is the authority, never an in-memory updated CropTransaction.
This is a crash-injection test, NOT a power-loss/durable-filesystem qualification.
"""
import hashlib
import fcntl
from contextlib import contextmanager
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from pcse.tests.test_wofost81_ext01_real_transaction import (
    CropTransaction, RealCropTransaction, accepted_event, canon, digest
)

STORE_SCHEMA="F-WOF-EXT01/CROP-ATOMIC-RESEARCH/1"

def package(tx):
    payload={"schema":STORE_SCHEMA,"committed":tx.committed,"receipts":tx.receipts}
    return {"payload":payload,"checksum":digest(payload)}

def recover(path):
    obj=json.loads(Path(path).read_text())
    if set(obj)!={"payload","checksum"} or digest(obj["payload"])!=obj["checksum"]:
        raise ValueError("corrupted committed crop journal")
    payload=obj["payload"]
    if set(payload)!={"schema","committed","receipts"} or payload["schema"]!=STORE_SCHEMA:
        raise ValueError("incompatible committed crop journal")
    if not isinstance(payload["receipts"],dict):
        raise ValueError("invalid committed event receipts")
    tx=CropTransaction(payload["committed"])
    tx.receipts=payload["receipts"].copy()
    return tx

def atomic_save(path,tx,inject_before_replace=False):
    path=Path(path)
    fd,tmp=tempfile.mkstemp(prefix=".crop-tx-",dir=path.parent)
    try:
        with os.fdopen(fd,"w") as stream:
            stream.write(canon(package(tx))+"\n")
            stream.flush()
            os.fsync(stream.fileno())
        if inject_before_replace:
            raise RuntimeError("injected failure before atomic publication")
        os.replace(tmp,path)
        dirfd=os.open(path.parent,os.O_RDONLY)
        try: os.fsync(dirfd)
        finally: os.close(dirfd)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

@contextmanager
def journal_writer_lock(path):
    # Advisory, process-wide Linux lock; do not unlink the lock inode.
    lockfile=str(path)+".lock"
    with open(lockfile,"a+b") as stream:
        fcntl.flock(stream.fileno(),fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(),fcntl.LOCK_UN)

def durable_commit(path,event,prepared,inject_before_replace=False):
    # Lock the read/validate/replace/recover interval as a single writer
    # transaction. Without this lock two independent processes can read the
    # same preimage then silently overwrite one another's accepted receipt.
    with journal_writer_lock(path):
        tx=recover(path)
        tx.commit(event,prepared)
        atomic_save(path,tx,inject_before_replace)
        return recover(path)

class PersistentActualPCSETransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.day30=RealCropTransaction.day30 if hasattr(RealCropTransaction,"day30") else None

    def test_atomic_candidate_receipt_commit_and_crash_recovery(self):
        if self.day30 is None:
            from pcse.tests.test_wofost81_ext01_process_restart import build_engine
            from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
            model=build_engine()
            model.run(days=30)
            original=snapshot(model)
        else: original=self.day30
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"committed.json"
            atomic_save(path,CropTransaction(original))
            event=accepted_event(31)
            before=path.read_bytes()
            first=recover(path).prepare(event)
            self.assertEqual(path.read_bytes(),before)
            with self.assertRaisesRegex(RuntimeError,"injected failure"):
                durable_commit(path,event,first,inject_before_replace=True)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(recover(path).receipts,{})
            durable_commit(path,event,first)
            restored=recover(path)
            self.assertEqual(restored.committed["timer_counter"],31)
            self.assertEqual(restored.receipts[event["event_id"]],digest(event))
            with self.assertRaises(ValueError):
                restored.prepare(event)
            with self.assertRaises(ValueError):
                durable_commit(path,event,first)
            later=accepted_event(32)
            candidate=restored.prepare(later)
            durable_commit(path,later,candidate)
            self.assertEqual(recover(path).committed["timer_counter"],32)
            self.assertEqual(len(recover(path).receipts),2)
            self.assertEqual(list(Path(folder).glob(".crop-tx-*")),[])
            print("EXT01_DURABLE_CROP_STATE_RECEIPT_ATOMIC_PASS")

    def test_two_independent_writers_do_not_both_commit_stale_preimage(self):
        from concurrent.futures import ThreadPoolExecutor
        from pcse.tests.test_wofost81_ext01_process_restart import build_engine
        from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
        model=build_engine()
        model.run(days=30)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"committed.json"
            atomic_save(path,CropTransaction(snapshot(model)))
            e=accepted_event(31)
            candidate=recover(path).prepare(e)
            def writer(_):
                try:
                    return durable_commit(path,e,candidate).committed["timer_counter"]
                except ValueError:
                    return "rejected"
            with ThreadPoolExecutor(max_workers=2) as pool:
                results=list(pool.map(writer,range(2)))
            self.assertCountEqual(results,[31,"rejected"])
            recovered=recover(path)
            self.assertEqual(len(recovered.receipts),1)
            self.assertEqual(recovered.committed["timer_counter"],31)
            print("EXT01_DURABLE_CONCURRENT_STALE_WRITER_REJECTED")

    def test_two_separate_processes_racing_same_real_crop_event(self):
        from pcse.tests.test_wofost81_ext01_process_restart import build_engine
        from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
        model=build_engine()
        model.run(days=30)
        with tempfile.TemporaryDirectory() as folder:
            journal=Path(folder)/"committed.json"
            request=Path(folder)/"request.json"
            atomic_save(journal,CropTransaction(snapshot(model)))
            event=accepted_event(31)
            candidate=recover(journal).prepare(event)
            request.write_text(canon({"event":event,"candidate":candidate}))
            cmd=[sys.executable,"-m","pcse.tests.test_wofost81_ext01_atomic_receipt_store",
                 "--commit-worker",str(journal),str(request)]
            workers=[subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
                     for _ in range(2)]
            results=[p.communicate(timeout=30) for p in workers]
            statuses=sorted(p.returncode for p in workers)
            self.assertEqual(statuses,[0,3],results)
            self.assertEqual(len(recover(journal).receipts),1)
            self.assertEqual(recover(journal).committed["timer_counter"],31)
            print("EXT01_DURABLE_TWO_PROCESS_COMMIT_RACE_PASS")

    def test_native_number_research_transport_and_durable_commit(self):
        """End-to-end numerical wire test, not an accepted SWAP-PCSE joint day."""
        from pcse.tests.test_wofost81_ext01_process_restart import build_engine
        from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
        model=build_engine()
        model.run(days=30)
        witness=json.loads((Path(__file__).parent/"test_data"/
                            "ext01_swap5_native_accepted_witness_v3.json").read_text())
        self.assertFalse(witness["pcse_daily_import_permitted"])
        self.assertIsNone(witness["unit_conversion_to_cm"])
        native=witness["actual_root_uptake_native_integral"]
        self.assertEqual(native,witness["potential_transpiration_native_integral"])
        event={**accepted_event(31),
               "actual_transpiration_cm_day":native,
               "potential_transpiration_cm_day":native,"rftra":1.0}
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"committed.json"
            atomic_save(path,CropTransaction(snapshot(model)))
            original=path.read_bytes()
            proposed=recover(path).prepare(event)
            self.assertEqual(path.read_bytes(),original)
            self.assertEqual(proposed["candidate"]["published_kiosk"]["TRA"],native)
            with self.assertRaises(RuntimeError):
                durable_commit(path,event,proposed,inject_before_replace=True)
            self.assertEqual(path.read_bytes(),original)
            durable_commit(path,event,proposed)
            reopened=recover(path)
            self.assertEqual(reopened.committed["published_kiosk"]["TRA"],native)
            self.assertEqual(reopened.receipts[event["event_id"]],digest(event))
            with self.assertRaises(ValueError):
                reopened.prepare(event)
            print("EXT01_NATIVE_NUMBER_DETACHED_PCSE_ATOMIC_WIRE_TRANSPORT_PASS")

    def test_zero_water_demand_candidate_atomic_rollback_and_recovery(self):
        from pcse.tests.test_wofost81_ext01_process_restart import build_engine
        from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
        model=build_engine()
        model.run(days=30)
        with tempfile.TemporaryDirectory() as folder:
            file=Path(folder)/"committed.json"
            atomic_save(file,CropTransaction(snapshot(model)))
            e={**accepted_event(31),"actual_transpiration_cm_day":0.0,
               "potential_transpiration_cm_day":0.0,"rftra":1.0}
            proposal=recover(file).prepare(e)
            before=file.read_bytes()
            with self.assertRaises(RuntimeError):
                durable_commit(file,e,proposal,inject_before_replace=True)
            self.assertEqual(file.read_bytes(),before)
            self.assertEqual(recover(file).committed["timer_counter"],30)
            durable_commit(file,e,proposal)
            reopened=recover(file)
            self.assertEqual(reopened.committed["published_kiosk"]["TRA"],0.0)
            self.assertEqual(reopened.committed["published_kiosk"]["TRAMX"],0.0)
            self.assertEqual(reopened.committed["published_kiosk"]["RFTRA"],1.0)
            self.assertEqual(len(reopened.receipts),1)
            print("EXT01_ZERO_DEMAND_DURABLE_RESTART_PASS")

    def test_corrupt_journal_refused(self):
        from pcse.tests.test_wofost81_ext01_process_restart import build_engine
        from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot
        model=build_engine()
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"committed.json"
            atomic_save(path,CropTransaction(snapshot(model)))
            obj=json.loads(path.read_text())
            obj["payload"]["receipts"]["forged"]="fake"
            path.write_text(canon(obj))
            with self.assertRaises(ValueError): recover(path)
            print("EXT01_DURABLE_CROP_JOURNAL_TAMPER_REJECTED")
if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--commit-worker":
        try:
            payload=json.loads(Path(sys.argv[3]).read_text())
            durable_commit(sys.argv[2],payload["event"],payload["candidate"])
        except ValueError:
            sys.exit(3)
    else:
        unittest.main()

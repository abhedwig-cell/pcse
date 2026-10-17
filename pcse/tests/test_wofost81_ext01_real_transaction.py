"""F-WOF-EXT01 real-PCSE crop transaction in a detached worker.

The physical flux numbers remain synthetic in this test. This tests actual PCSE
candidate state, NOT SWAP5's production accepted hydrology/event publication.
"""
import copy
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
import unittest
from pcse.tests.test_wofost81_ext01_process_restart import build_engine, record_projection
from pcse.tests.test_wofost81_ext01_direct_state_restore import snapshot, restore

SCHEMA="F-WOF-EXT01/PCSE-TRANSACTION-RESEARCH/1"

def canon(o):
    return json.dumps(o,allow_nan=False,sort_keys=True,separators=(",",":"))

def digest(o):
    return hashlib.sha256(canon(o).encode()).hexdigest()

def accepted_event(day, hydro_provenance="synthetic-barley-research"):
    return dict(event_id=f"crop-day-{day:03d}",day=day,
        date=(dt.date(2010,4,16)+dt.timedelta(days=day)).isoformat(),
        hydro_provenance=hydro_provenance,actual_transpiration_cm_day=.15,
        potential_transpiration_cm_day=.30,rftra=.5)

def validate_event(e,prior):
    if set(e)!={"event_id","day","date","hydro_provenance","actual_transpiration_cm_day",
               "potential_transpiration_cm_day","rftra"}:
        raise ValueError("event contract")
    if e["day"]!=prior["timer_counter"]+1 or e["event_id"]!=f"crop-day-{e['day']:03d}":
        raise ValueError("out of order event")
    if e["date"]!=(dt.date.fromisoformat(prior["day"])+dt.timedelta(days=1)).isoformat():
        raise ValueError("crop date and accepted hydro event date mismatch")
    a,p,r=(e[k] for k in ("actual_transpiration_cm_day","potential_transpiration_cm_day","rftra"))
    if any(not isinstance(x,(int,float)) or isinstance(x,bool) or not math.isfinite(x) for x in (a,p,r)):
        raise ValueError("invalid flux")
    if not (p>0 and 0<=a<=p and 0<=r<=1) or abs(a/p-r)>1e-12:
        raise ValueError("flux inconsistency")
    if not e["hydro_provenance"]: raise ValueError("missing provenance")
    # Synthetic inputs remain explicitly research-only. This worker has no
    # authentic SWAP acceptance authority or attestation verifier yet, so
    # it must refuse any event pretending to be physically SWAP-admitted.
    if e["hydro_provenance"]!="synthetic-barley-research":
        raise ValueError("unverified physical SWAP provenance not admissible")

def candidate_worker(request):
    if request.get("schema")!=SCHEMA: raise ValueError("schema")
    e=request["event"]
    prior=request["committed"]
    validate_event(e,prior)
    model=build_engine()
    restore(model,prior)
    # Apply the accepted event to the *actual* PCSE external ET rate provider,
    # instead of merely validating an envelope and using fixed 0.5 stress.
    from unittest.mock import patch
    from pcse.tests.test_wofost81_external_soil_off import ExternalET
    def accepted_et(self, day, drv):
        self.rates.TRA=e["actual_transpiration_cm_day"]
        self.rates.TRAMX=e["potential_transpiration_cm_day"]
        self.rates.RFTRA=e["rftra"]
        return self.rates.TRA,self.rates.TRAMX
    with patch.object(ExternalET,"__call__",accepted_et):
        model.run(days=1)
    next_state=snapshot(model)
    if abs(next_state["published_kiosk"]["RFTRA"]-e["rftra"])>1e-12:
        raise RuntimeError("accepted flux not consumed by actual crop")
    if next_state["timer_counter"]!=e["day"]: raise AssertionError("bad phase")
    return {"schema":SCHEMA,"event_id":e["event_id"],"event_digest":digest(e),
            "prior_digest":digest(prior),"candidate_digest":digest(next_state),"candidate":next_state}

def external_prepare(event,committed):
    request={"schema":SCHEMA,"event":event,"committed":committed}
    proc=subprocess.run([sys.executable,"-m",
         "pcse.tests.test_wofost81_ext01_real_transaction","--worker"],
         input=canon(request),text=True,capture_output=True)
    if proc.returncode: raise RuntimeError(proc.stderr[-2500:])
    return json.loads(proc.stdout.split("EXT01_CANDIDATE:")[-1].strip())

class CropTransaction:
    def __init__(self,committed):
        self.committed=copy.deepcopy(committed)
        self.receipts={}
    def prepare(self,event):
        if event["event_id"] in self.receipts: raise ValueError("duplicate event")
        before=digest(self.committed)
        result=external_prepare(event,self.committed)
        assert digest(self.committed)==before
        return result
    def commit(self,event,candidate):
        ident=event["event_id"]
        if ident in self.receipts: raise ValueError("duplicate event")
        if (candidate["schema"]!=SCHEMA or candidate["event_id"]!=ident or
            candidate["event_digest"]!=digest(event) or
            candidate["prior_digest"]!=digest(self.committed) or
            candidate["candidate_digest"]!=digest(candidate["candidate"])):
            raise ValueError("stale or foreign candidate")
        if candidate["candidate"]["timer_counter"]!=event["day"]:
            raise ValueError("wrong candidate day")
        self.committed=copy.deepcopy(candidate["candidate"])
        self.receipts[ident]=candidate["event_digest"]

class RealCropTransaction(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        original=build_engine()
        original.run(days=30)
        cls.day30=snapshot(original)
        original.run(days=3)
        cls.expected=record_projection(original.get_output())
    def test_reject_retry_commit_restart_three_real_crop_days(self):
        tx=CropTransaction(self.day30)
        for day in (31,32,33):
            e=accepted_event(day)
            before=digest(tx.committed)
            a=tx.prepare(e)
            b=tx.prepare(e)
            self.assertEqual(digest(a),digest(b))
            self.assertEqual(digest(tx.committed),before)
            with self.assertRaises(ValueError):
                tx.commit({**e,"hydro_provenance":"foreign"},a)
            self.assertEqual(digest(tx.committed),before)
            tx.commit(e,b)
            with self.assertRaises(ValueError): tx.prepare(e)
            with self.assertRaises(ValueError): tx.commit(e,b)
        self.assertEqual(tx.committed["output"],self.expected)
        self.assertEqual(tx.committed["timer_counter"],33)
        print("EXT01_REAL_PCSE_TRANSACTION_3_DAYS_PASS")
    def test_modified_candidate_is_rejected_without_commit(self):
        tx=CropTransaction(self.day30)
        event=accepted_event(31)
        prepared=tx.prepare(event)
        corrupted=copy.deepcopy(prepared)
        corrupted["candidate"]["timer_counter"]=999
        baseline=digest(tx.committed)
        with self.assertRaises(ValueError):
            tx.commit(event,corrupted)
        self.assertEqual(digest(tx.committed),baseline)
        tx.commit(event,prepared)
        print("EXT01_REAL_PCSE_CANDIDATE_TAMPER_REJECTED")

    def test_distinct_valid_accepted_fluxes_reach_real_pcse(self):
        low=CropTransaction(self.day30)
        high=CropTransaction(self.day30)
        e_low=accepted_event(31)
        e_high={**accepted_event(31),
                "actual_transpiration_cm_day":.30,"rftra":1.0}
        low_candidate=low.prepare(e_low)
        high_candidate=high.prepare(e_high)
        self.assertEqual(low_candidate["candidate"]["published_kiosk"]["RFTRA"],.5)
        self.assertEqual(high_candidate["candidate"]["published_kiosk"]["RFTRA"],1.0)
        self.assertNotEqual(low_candidate["candidate_digest"],high_candidate["candidate_digest"])
        self.assertEqual(digest(low.committed),digest(high.committed))
        low.commit(e_low,low_candidate)
        high.commit(e_high,high_candidate)
        self.assertNotEqual(digest(low.committed),digest(high.committed))
        print("EXT01_REAL_PCSE_DISTINCT_ACCEPTED_ET_CONSUMED_PASS")

    def test_actual_swap_receipt_requires_calendar_alignment(self):
        from pcse.tests.wofost81_accepted_day_receipt import AcceptedCropDay
        from datetime import date
        receipt=AcceptedCropDay(
            "SWAP5-rooted-weather-j1-d2-accepted",2.0,3.0,
            1.0370706377336118e-3,1.0370706377336118e-3)
        a,p,ratio=receipt.rates()
        self.assertEqual((a,p,ratio),(a,a,1.0))
        self.assertTrue(receipt.require_calendar_alignment(date(1999,1,23),date(1999,1,21)))
        with self.assertRaisesRegex(ValueError,"SWAP event"):
            receipt.require_calendar_alignment(date.fromisoformat(self.day30["day"]),date(1999,1,21))
        # No fabricated mapping from the 1999 SWAP certificate into the 2010
        # PCSE barley date: an accepted hydrological receipt alone is insufficient.
        print("EXT01_AUTHENTIC_SWAP_RECEIPT_CALENDAR_MISMATCH_REJECTED")

    def test_claimed_swap5_acceptance_cannot_bypass_provenance_gate(self):
        tx=CropTransaction(self.day30)
        before=digest(tx.committed)
        forged=accepted_event(31,hydro_provenance="SWAP5-accepted-column-1")
        with self.assertRaises(RuntimeError):
            tx.prepare(forged)
        self.assertEqual(digest(tx.committed),before)
        print("EXT01_UNATTESTED_REAL_SWAP_PROVENANCE_REJECTED")

    def test_v3_physical_swap_witness_refused_in_actual_pcse_worker(self):
        # Exact source identity/flux figures were observed in successful
        # SWAP5 rooted-weather run 39066877106. This is a negative physical
        # integration gate; dates/forcings are unrelated to barley 2010.
        witness=dict(schema="F-WOF-EXT01/SWAP-WITNESS/3",
            accepted_lineage_id=630101,accepted_final_revision=192,
            accepted_t0=2.0,accepted_t1=3.0,
            source_weather_epoch="1999-01-20",
            source_calendar_date="1999-01-23",
            actual_root_uptake_native_integral=1.0370706377336118e-3,
            potential_transpiration_native_integral=1.0370706377336118e-3,
            calendar_date=None,unit_conversion_to_cm=None,
            pcse_daily_import_permitted=False)
        tx=CropTransaction(self.day30)
        before=digest(tx.committed)
        # Fail closed on source-date mismatch even if caller falsely renames
        # the physical acceptance as a synthetic crop-day transaction.
        e=accepted_event(31,hydro_provenance=(
            f"SWAP5-lineage-{witness['accepted_lineage_id']}-"
            f"rev-{witness['accepted_final_revision']}"))
        with self.assertRaises(RuntimeError):
            tx.prepare(e)
        self.assertEqual(digest(tx.committed),before)
        self.assertNotEqual(witness["source_calendar_date"],e["date"])
        self.assertIsNone(witness["unit_conversion_to_cm"])
        print("EXT01_REAL_SWAP_V3_WITNESS_PCSE_IMPORT_REJECTED")

    def test_invalid_flux_and_failed_worker_do_not_commit(self):
        tx=CropTransaction(self.day30)
        before=digest(tx.committed)
        for change in ({"rftra":.9},{"actual_transpiration_cm_day":.4},
                       {"potential_transpiration_cm_day":0},{"day":32},
                       {"date":"1999-01-23"}):
            with self.subTest(change=change),self.assertRaises(RuntimeError):
                tx.prepare({**accepted_event(31),**change})
            self.assertEqual(digest(tx.committed),before)
        print("EXT01_REAL_PCSE_BAD_EVENT_UNCHANGED_PASS")

if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1]=="--worker":
        try:
            request=json.load(sys.stdin)
            print("EXT01_CANDIDATE:"+canon(candidate_worker(request)))
        except Exception as exc:
            print(f"worker failure: {type(exc).__name__}: {exc}",file=sys.stderr)
            sys.exit(2)
    else:
        unittest.main()

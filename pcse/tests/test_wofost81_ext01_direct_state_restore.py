"""F-WOF-EXT01: experimental real PCSE direct in-memory continuation.

Construct a *new* Engine, transfer versioned scalar/leaf cohort state and
current rates at an accepted day boundary, then continue WITHOUT replay.
Research-only: deliberately fails if any supplied state is unsupported.
"""
import datetime as dt
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from collections import deque
from pcse.tests.test_wofost81_ext01_process_restart import build_engine, record_projection, internal_crop_projection
from pcse.tests.test_wofost81_ext01_direct_restart_inventory import COMPONENTS

SCHEMA="F-WOF-EXT01/DIRECT-RESTART-EXPERIMENT/2"
COMPONENT_PATHS=(*COMPONENTS,"n_crop_dynamics.demand_uptake")

def component(crop,path):
    obj=crop
    for name in path.split("."):
        obj=getattr(obj,name)
    return obj

def encode_value(value):
    if isinstance(value,dt.date): return {"date":value.isoformat()}
    if isinstance(value,(list,tuple,deque)): return [encode_value(v) for v in value]
    if isinstance(value,(bool,int,str)) or value is None: return value
    if isinstance(value,float) and math.isfinite(value): return value
    raise TypeError(f"unsupported state type {type(value).__name__}: {value!r}")

def decode_value(value,prior):
    if isinstance(value,dict) and set(value)=={"date"}: return dt.date.fromisoformat(value["date"])
    if isinstance(value,list):
        result=[decode_value(x,None) for x in value]
        if isinstance(prior,deque): return deque(result)
        if isinstance(prior,tuple) and hasattr(prior,"_fields"): return type(prior)(*result)
        return result
    return value

def fields(source):
    return {name:encode_value(getattr(source,name)) for name in sorted(source._valid_vars)}

def apply_fields(target,values):
    if set(values)!=set(target._valid_vars): raise ValueError("state surface drift")
    target.unlock()
    try:
        for name,value in values.items():
            setattr(target,name,decode_value(value,getattr(target,name)))
    finally:
        target.lock()
    if hasattr(target,"touch"): target.touch()

def snapshot(engine):
    crop=engine.crop
    components={}
    for name in COMPONENT_PATHS:
        child=component(crop,name)
        components[name]={kind:fields(getattr(child,kind))
                          for kind in ("states","rates") if getattr(child,kind,None) is not None}
    components["crop"]={kind:fields(getattr(crop,kind))
                        for kind in ("states","rates") if getattr(crop,kind,None) is not None}
    return {"schema":SCHEMA,"day":engine.day.isoformat(),
            "timer_counter":engine.timer.day_counter,"timer_first_call":engine.timer.first_call,
            "output":record_projection(engine.get_output()),
            "published_kiosk":{k:encode_value(v) for k,v in engine.kiosk.items()},
            "components":components,
            "leaf_reference":internal_crop_projection(engine),
            "assimilation_tmin_history":list(engine.crop.assim._TMNSAV)}

def restore(engine,payload):
    if payload["schema"]!=SCHEMA: raise ValueError("incompatible version")
    if set(payload["components"])!=set(COMPONENT_PATHS)|{"crop"}: raise ValueError("component drift")
    for name in (*COMPONENT_PATHS,"crop"):
        child=engine.crop if name=="crop" else component(engine.crop,name)
        for kind,values in payload["components"][name].items():
            apply_fields(getattr(child,kind),values)
    # WOFOST assimilation retains 7-day TMIN history outside ordinary traits.
    history=payload["assimilation_tmin_history"]
    if not isinstance(history,list) or len(history)>7 or any(
        not isinstance(x,(int,float)) or not math.isfinite(x) for x in history
    ):
        raise ValueError("invalid TMIN history")
    engine.crop.assim._TMNSAV=deque(history,maxlen=7)
    engine.day=dt.date.fromisoformat(payload["day"])
    engine.timer.current_date=engine.day
    engine.timer.day_counter=payload["timer_counter"]
    engine.timer.first_call=payload["timer_first_call"]
    engine.drv=engine._get_driving_variables(engine.day)
    # The fresh Engine cannot reconstruct rate publications just from traits.
    published=set(engine.kiosk.published_rates)|set(engine.kiosk.published_states)
    if not set(payload["published_kiosk"]).issubset(published):
        raise ValueError("foreign kiosk variables")
    engine.kiosk.flush_rates()
    engine.kiosk.flush_states()
    for name,value in payload["published_kiosk"].items():
        dict.__setitem__(engine.kiosk,name,decode_value(value,None))
    # Output history serves test comparison only; not a scientific crop state.
    engine._saved_output=[{k:dt.date.fromisoformat(v) if k=="day" else v
                          for k,v in row.items()} for row in payload["output"]]
    if internal_crop_projection(engine)!=payload["leaf_reference"]:
        raise RuntimeError("restored leaf projection mismatch")
    return engine

class ActualEngineDirectContinuation(unittest.TestCase):
    def test_direct_resume_multiple_boundaries_without_replay(self):
        for split in (30,45):
            with self.subTest(split=split):
                source=build_engine()
                source.run(days=split)
                payload=json.loads(json.dumps(snapshot(source),allow_nan=False))
                fresh=build_engine()
                self.assertEqual(fresh.timer.day_counter,0)
                restore(fresh,payload)
                self.assertEqual(fresh.timer.day_counter,split)
                source.run(days=60-split)
                fresh.run(days=60-split)
                self.assertEqual(record_projection(fresh.get_output()),
                                 record_projection(source.get_output()))
                self.assertEqual(internal_crop_projection(fresh),
                                 internal_crop_projection(source))
                print("EXT01_DIRECT_RESTART_SPLIT_EQUAL",split,61)

    def test_early_day10_direct_restore_is_not_yet_qualified(self):
        """A known negative witness: a missing early-cycle continuation dependency."""
        source=build_engine()
        source.run(days=10)
        payload=json.loads(json.dumps(snapshot(source),allow_nan=False))
        fresh=build_engine()
        restore(fresh,payload)
        source.run(days=2)
        fresh.run(days=2)
        actual=record_projection(fresh.get_output())
        expected=record_projection(source.get_output())
        self.assertEqual(actual[:11],expected[:11])
        self.assertNotEqual(actual[12],expected[12],
                            "earlier day-10 mismatch changed; review qualification")
        differences={k:(actual[12][k],expected[12][k]) for k in actual[12]
                     if actual[12][k]!=expected[12][k]}
        print("EXT01_DIRECT_RESTART_DAY10_UNQUALIFIED",json.dumps(differences,sort_keys=True))

    def test_reject_incompatible_or_foreign_state_before_continuation(self):
        source=build_engine()
        source.run(days=30)
        payload=json.loads(json.dumps(snapshot(source),allow_nan=False))
        wrong=json.loads(json.dumps(payload))
        wrong["schema"]="unknown"
        with self.assertRaises(ValueError):
            restore(build_engine(),wrong)
        wrong=json.loads(json.dumps(payload))
        wrong["published_kiosk"]["foreign_crop_state"]=1
        with self.assertRaises(ValueError):
            restore(build_engine(),wrong)
        print("EXT01_DIRECT_RESTART_FOREIGN_STATE_REJECTED")

    def test_direct_new_process_restore_at_three_splits(self):
        baseline=build_engine()
        baseline.run(days=60)
        expected=record_projection(baseline.get_output())
        for split in (10,30,45):
            with self.subTest(split=split),tempfile.TemporaryDirectory() as folder:
                command=[sys.executable,"-m","pcse.tests.test_wofost81_ext01_direct_state_restore","--worker"]
                for action in ("save","resume"):
                    proc=subprocess.run(command+[action,folder,str(split)],capture_output=True,text=True)
                    self.assertEqual(proc.returncode,0,proc.stderr[-3000:])
                result=json.loads((Path(folder)/"continued.json").read_text())
                self.assertEqual(result["output"],expected)
                self.assertEqual(result["internal"],internal_crop_projection(baseline))
                print("EXT01_DIRECT_SEPARATE_PROCESS_RESTART_PASS",split,61)

def worker(action,folder,split):
    folder=Path(folder)
    if action=="save":
        engine=build_engine()
        engine.run(days=split)
        (folder/"snapshot.json").write_text(json.dumps(snapshot(engine),allow_nan=False))
    elif action=="resume":
        saved=json.loads((folder/"snapshot.json").read_text())
        engine=build_engine()
        if engine.timer.day_counter!=0:
            raise RuntimeError("restore must begin with fresh engine")
        restore(engine,saved)
        if engine.timer.day_counter!=split:
            raise RuntimeError("restored timer mismatch")
        engine.run(days=60-split)
        (folder/"continued.json").write_text(json.dumps({
            "output":record_projection(engine.get_output()),
            "internal":internal_crop_projection(engine)},allow_nan=False))
    else:
        raise ValueError("unknown action")

if __name__=="__main__":
    if len(sys.argv)==5 and sys.argv[1]=="--worker":
        worker(sys.argv[2],sys.argv[3],int(sys.argv[4]))
    else:
        unittest.main()


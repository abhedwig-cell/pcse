"""F-WOF-EXT01: genuine separate-process checkpoint/restart feasibility.

Research-only pickle witness. Pickle is NOT a safe/stable external checkpoint
format and must never be accepted as an official restart codec. Files are
locally generated and untrusted pickle bytes must never be loaded.
"""
import datetime as dt
import json
import os
import pickle
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pcse.tests.test_wofost81_ext01_new_barley import new_barley_case


def checkpoint_worker(path):
    # New engine only; no pre-existing process-global crop state.
    rows, model = new_barley_case(split_days=30)  # currently advances through 60
    # This worker is intentionally replaced below to ensure true mid-run capture.


def record_projection(records):
    keys=("day","DVS","LAI","TAGP","TWLV","TWRT","TWST","TWSO",
          "NamountLV","NamountRT","NamountST","NamountSO","NuptakeTotal")
    return [{k:(r.get(k).isoformat() if hasattr(r.get(k),"isoformat") else r.get(k))
             for k in keys} for r in records]


def build_engine():
    import yaml
    from unittest.mock import patch
    from pcse.base import ParameterProvider
    from pcse.engine import Engine
    from pcse.crop import wofost81
    from pcse.tests.test_wofost81_external_soil_off import ExternalET
    from pcse.tests.test_wofost81_snomin_e2e import _weather,_soil_and_site
    parameters=yaml.safe_load((Path(__file__).parent/"test_data"/
                                "ext01_barley_wofost81_source.yaml").read_text())
    crop={k:v[0] for k,v in parameters["CropParameters"]["Varieties"]["Spring_barley_301"].items()
          if k!="Metadata"}
    soil,site=_soil_and_site()
    agro=[{dt.date(2010,4,16):{"CropCalendar":{
      "crop_name":"barley","variety_name":"Spring_barley_301",
      "crop_start_date":dt.date(2010,4,16),"crop_start_type":"emergence",
      "crop_end_date":dt.date(2010,9,20),"crop_end_type":"harvest",
      "max_duration":180},"TimedEvents":None,"StateEvents":None}}]
    # Patch during construction only; the initialized ET instances are pickled.
    with patch.object(wofost81,"Evapotranspiration",ExternalET):
        engine=Engine(ParameterProvider(cropdata=crop,soildata=soil,sitedata=site),
             _weather(),agro,
             config=Path(__file__).with_name("data_wofost81_external_soil_off.conf"))
    return engine


def worker(mode,folder):
    folder=Path(folder)
    if mode=="write":
        engine=build_engine()
        engine.run(days=30)
        with (folder/"engine.pickle").open("wb") as handle:
            pickle.dump(engine,handle,pickle.HIGHEST_PROTOCOL)
        (folder/"first.json").write_text(json.dumps(record_projection(engine.get_output())))
    elif mode=="resume":
        # Only load own trusted, same-run test artifact; never user-supplied data.
        with (folder/"engine.pickle").open("rb") as handle:
            engine=pickle.load(handle)
        engine.run(days=30)
        (folder/"continued.json").write_text(json.dumps(record_projection(engine.get_output())))
    else: raise ValueError(mode)


class FullEngineSeparateProcessRestart(unittest.TestCase):
    def test_real_process_restart_or_report_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            for mode in ("write","resume"):
                p=subprocess.run([sys.executable,"-m",
                  "pcse.tests.test_wofost81_ext01_process_restart",
                  "--worker",mode,folder],capture_output=True,text=True)
                if p.returncode:
                    self.fail(f"Separate-process {mode} failed: {p.stderr[-2500:]}")
            restored=json.loads((Path(folder)/"continued.json").read_text())
            original, _=new_barley_case()
            expected=record_projection(original)
            self.assertEqual(restored,expected)
            self.assertEqual(len(restored),61)
            print("EXT01_TRUE_PROCESS_RESTART_EQUAL",len(restored))


if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--worker":
        worker(sys.argv[2],sys.argv[3])
    else:
        unittest.main()

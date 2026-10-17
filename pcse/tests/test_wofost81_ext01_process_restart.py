"""F-WOF-EXT01: process-loss recovery by deterministic replay.

This is NOT a complete PCSE checkpoint or state snapshot. A previous
attempt to pickle the PCSE Engine failed on dynamically wrapped rates,
so the research fallback restarts a *fresh* engine and validates all
previous outputs before advancing. This requires a full immutable input
history and incurs replay costs.
"""
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pcse.tests.test_wofost81_ext01_new_barley import new_barley_case


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
        (folder/"first.json").write_text(json.dumps(record_projection(engine.get_output())))
    elif mode=="resume":
        # New Python process, fresh engine, deterministic replay from initial
        # condition instead of restoring hidden PCSE state.
        expected=json.loads((folder/"first.json").read_text())
        engine=build_engine()
        engine.run(days=30)
        if record_projection(engine.get_output())!=expected:
            raise RuntimeError("replayed crop diverged before resume")
        engine.run(days=30)
        (folder/"continued.json").write_text(json.dumps(record_projection(engine.get_output())))
    else: raise ValueError(mode)


class SeparateProcessRecoveryByReplay(unittest.TestCase):
    def test_separate_process_replay_recovery(self):
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
            print("EXT01_PROCESS_REPLAY_RECOVERY_EQUAL",len(restored))


if __name__=="__main__":
    if len(sys.argv)==4 and sys.argv[1]=="--worker":
        worker(sys.argv[2],sys.argv[3])
    else:
        unittest.main()

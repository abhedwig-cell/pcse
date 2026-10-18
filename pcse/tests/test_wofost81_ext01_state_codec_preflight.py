"""F-WOF-EXT01 bounded scientific state codec preflight.

Serializes a real PCSE leaf cohort and observed phenology at a day boundary.
Deliberately NOT an Engine or full WOFOST restart codec.
"""
import json
import math
import unittest

from pcse.tests.test_wofost81_ext01_process_restart import (
    build_engine, internal_crop_projection,
)

SCHEMA = "F-WOF-EXT01/LEAF-PROJECTION/1"
FIELDS = ("day","LV","SLA","LVAGE","LASUM","LAIEXP","LAIMAX",
          "WLV","DWLV","TWLV","DVS","TAGP")
ARRAYS = ("LV","SLA","LVAGE")

def encode_projection(engine):
    value=internal_crop_projection(engine)
    assert tuple(value)==FIELDS, "private state projection drift"
    payload={"schema":SCHEMA,"state":value}
    return json.dumps(payload, allow_nan=False, sort_keys=True, separators=(",",":"))

def decode_projection(data):
    obj=json.loads(data)
    if set(obj)!={"schema","state"} or obj["schema"]!=SCHEMA:
        raise ValueError("incompatible state schema")
    s=obj["state"]
    if set(s)!=set(FIELDS): raise ValueError("missing or unknown state fields")
    if not all(isinstance(s[k],list) for k in ARRAYS):
        raise ValueError("invalid leaf arrays")
    n=len(s["LV"])
    if not n or any(len(s[k])!=n for k in ARRAYS):
        raise ValueError("leaf cohort shape mismatch")
    for key in FIELDS:
        if key=="day": continue
        values=s[key] if key in ARRAYS else [s[key]]
        if any(not isinstance(v,(float,int)) or isinstance(v,bool) or
               not math.isfinite(v) for v in values):
            raise ValueError("nonfinite or invalid crop scalar")
    if any(x<0 for k in ARRAYS for x in s[k]): raise ValueError("negative leaf cohort")
    return s

class BoundedRealStateCodecPreflight(unittest.TestCase):
    def test_real_pcse_cohort_projection_roundtrip_at_three_days(self):
        for day in (10,30,45):
            with self.subTest(day=day):
                m=build_engine()
                m.run(days=day)
                encoded=encode_projection(m)
                restored=decode_projection(encoded)
                self.assertEqual(restored,internal_crop_projection(m))
                self.assertEqual(len(restored["LV"]),len(restored["SLA"]))
                self.assertEqual(len(restored["LV"]),len(restored["LVAGE"]))
                print("EXT01_REAL_LEAF_PROJECTION_CODEC_PASS",day,len(restored["LV"]))
    def test_fail_closed_malformed_and_incomplete_state(self):
        m=build_engine()
        m.run(days=30)
        base=json.loads(encode_projection(m))
        for mutation in ("schema","missing","cohorts","nan","extra"):
            candidate=json.loads(json.dumps(base))
            if mutation=="schema": candidate["schema"]="unknown"
            if mutation=="missing": del candidate["state"]["LAIEXP"]
            if mutation=="cohorts": candidate["state"]["SLA"].append(.002)
            if mutation=="nan": candidate["state"]["LV"][0]=float("nan")
            if mutation=="extra": candidate["state"]["engine_timer"]=30
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,TypeError)):
                decode_projection(json.dumps(candidate))
        print("EXT01_INCOMPLETE_STATE_FAIL_CLOSED_PASS")
if __name__=="__main__":
    unittest.main()

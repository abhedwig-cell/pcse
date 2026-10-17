"""F-WOF-EXT01: explicit 1999 physical-event identity preflight.

Research-only. This deliberately does not authorize a crop commit: native
water units, meteorology and complete crop initial state still need proof.
"""
from datetime import date, timedelta
from pathlib import Path
import hashlib
import json
import math
import unittest

FIXTURE = Path(__file__).with_name("test_data") / "ext01_swap5_native_accepted_witness_v3.json"
SCHEMA = "F-WOF-EXT01/SWAP-WITNESS/3"

def canonical_1999_preflight(raw, *, expected_date, expected_lineage,
                             expected_revision, expected_sha256):
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("physical witness bytes changed")
    w = json.loads(raw)
    if w.get("schema") != SCHEMA:
        raise ValueError("unknown receipt schema")
    if w.get("acceptance") != "observed-passing-native-test":
        raise ValueError("missing native accepted-test evidence")
    if not isinstance(expected_date, date):
        raise ValueError("explicit Gregorian crop date required")
    if w.get("accepted_lineage_id") != expected_lineage or w.get("accepted_final_revision") != expected_revision:
        raise ValueError("accepted soil lineage/revision mismatch")
    t0, t1 = w["accepted_t0"], w["accepted_t1"]
    if not (isinstance(t0, (float, int)) and isinstance(t1, (float, int))
            and math.isfinite(t0) and math.isfinite(t1) and t1 - t0 == 1):
        raise ValueError("invalid integration interval")
    epoch = date.fromisoformat(w["source_weather_epoch"])
    actual_date = epoch + timedelta(days=t1)
    if (w["source_calendar_date"] != actual_date.isoformat()
            or expected_date != actual_date):
        raise ValueError("physical event and crop calendar mismatch")
    for field in ("actual_root_uptake_native_integral",
                  "potential_transpiration_native_integral",
                  "matched_accepted_uptake_native_integral"):
        v = w[field]
        if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v) or v < 0:
            raise ValueError("invalid native flux")
    a = w["actual_root_uptake_native_integral"]
    p = w["potential_transpiration_native_integral"]
    if a > p or a != w["matched_accepted_uptake_native_integral"]:
        raise ValueError("accepted-root-uptake inconsistency")
    if w.get("pcse_daily_import_permitted") is not False or w.get("unit_conversion_to_cm") is not None:
        raise ValueError("research witness flags manipulated")
    return {"date": actual_date.isoformat(), "lineage": expected_lineage,
            "revision": expected_revision, "actual_native": a, "potential_native": p,
            "pcse_commit_permitted": False}

class TestPhysical1999Identity(unittest.TestCase):
    def setUp(self):
        self.raw = FIXTURE.read_bytes()
        self.sha = hashlib.sha256(self.raw).hexdigest()
        self.kw = dict(expected_date=date(1999, 1, 23), expected_lineage=630101,
                       expected_revision=192, expected_sha256=self.sha)

    def test_actual_1999_identity_is_checked_but_not_authorized(self):
        result = canonical_1999_preflight(self.raw, **self.kw)
        self.assertEqual(result["date"], "1999-01-23")
        self.assertFalse(result["pcse_commit_permitted"])
        print("EXT01_AUTHENTIC_1999_IDENTITY_VERIFIED_NO_CROP_ADMISSION")

    def test_2010_case_rejected(self):
        with self.assertRaisesRegex(ValueError, "calendar mismatch"):
            canonical_1999_preflight(self.raw, **{**self.kw, "expected_date": date(2010, 5, 17)})

    def test_wrong_lineage_and_revision_rejected(self):
        for key, bad in (("expected_lineage", 630102), ("expected_revision", 193)):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "lineage/revision"):
                canonical_1999_preflight(self.raw, **{**self.kw, key: bad})

    def test_modified_bytes_rejected_before_interpretation(self):
        modified = self.raw.replace(b"1999-01-23", b"2010-05-17")
        self.assertNotEqual(modified, self.raw)
        with self.assertRaisesRegex(ValueError, "bytes changed"):
            canonical_1999_preflight(modified, **self.kw)

    def test_no_false_positive_for_altered_import_authority(self):
        changed = json.loads(self.raw)
        changed["pcse_daily_import_permitted"] = True
        altered = json.dumps(changed).encode()
        with self.assertRaisesRegex(ValueError, "flags manipulated"):
            canonical_1999_preflight(altered, **{**self.kw, "expected_sha256": hashlib.sha256(altered).hexdigest()})

if __name__ == "__main__":
    unittest.main()

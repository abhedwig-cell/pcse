"""EXT01 physical SWAP5 1999 weather and accepted flux provenance cross-check.

Observed inputs are source-unit witnesses, not a reconstructed PCSE driver.
"""
from datetime import date
from pathlib import Path
import hashlib
import json
import unittest
from pcse.tests.test_wofost81_ext01_physical_1999_identity import (
    FIXTURE, EXPECTED_FIXTURE_SHA256, canonical_1999_preflight
)

OBSERVED=Path(__file__).with_name("test_data")/"ext01_swap5_1999_source_weather_observed.json"

def validate_1999_pair(weather, native):
    if weather["schema"]!="F-WOF-EXT01/SWAP-SOURCE-WEATHER/1":
        raise ValueError("weather schema")
    if weather["date"]!=native["date"]:
        raise ValueError("calendar mismatch")
    if weather["source_run_id"]!=39077771719 or weather["source_head"]!="e8798f05e3c46e702b70e98a756c0ba63f666ec9":
        raise ValueError("unknown source execution authority")
    if (weather["tmin_c"],weather["tmax_c"],weather["radiation_source_j_m2_day"])!=(-2.8,2.1,794000):
        raise ValueError("observed source weather changed")
    if weather["rain_source_units"]!=0.3 or weather["reference_et_source_units"]!=0.0797:
        raise ValueError("observed water forcing changed")
    if weather["pcse_weather_conversion_qualified"] is not False or weather["pcse_crop_day_admitted"] is not False:
        raise ValueError("unqualified positive crop coupling")
    return {"date":native["date"],"accepted_revision":native["revision"],
            "meteorology_available":True,"crop_parameter_match":False,
            "pcse_day_admitted":False}

class TestObserved1999Pair(unittest.TestCase):
    def setUp(self):
        raw=FIXTURE.read_bytes()
        self.native=canonical_1999_preflight(raw,expected_date=date(1999,1,23),
            expected_lineage=630101,expected_revision=192,
            expected_sha256=EXPECTED_FIXTURE_SHA256)
        self.weather=json.loads(OBSERVED.read_text())

    def test_authentic_native_day_and_observed_weather_are_paired_but_not_coupled(self):
        result=validate_1999_pair(self.weather,self.native)
        self.assertTrue(result["meteorology_available"])
        self.assertFalse(result["pcse_day_admitted"])
        print("EXT01_1999_OBSERVED_WEATHER_NATIVE_RECEIPT_PAIRED_RESEARCH_ONLY")

    def test_wrong_day_rejected(self):
        with self.assertRaisesRegex(ValueError,"calendar"):
            validate_1999_pair({**self.weather,"date":"2010-05-17"},self.native)

    def test_unqualified_admission_rejected(self):
        with self.assertRaisesRegex(ValueError,"unqualified"):
            validate_1999_pair({**self.weather,"pcse_crop_day_admitted":True},self.native)

    def test_changed_weather_refused(self):
        with self.assertRaisesRegex(ValueError,"observed source weather"):
            validate_1999_pair({**self.weather,"tmax_c":3.0},self.native)

if __name__=="__main__":
    unittest.main()

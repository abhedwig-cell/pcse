"""Negative admission tests for the Jan 1999 native-to-PCSE meteo boundary."""
import copy
import datetime as dt
import unittest
import json
from pathlib import Path
from pcse.tests.ext01_swap5_native_weather_sequence import (
    SCHEMA, require_native_sequence, pcse_weather_provider_from_native
)
def specimen():
    days=[]
    for i in range(7):
        days.append(dict(date=(dt.date(1999,1,20)+dt.timedelta(days=i)).isoformat(),
             tmin_c=-2.8,tmax_c=2.1,rain_native=0.3,etref_native=0.0797,
             radiation_j_m2_day=794000.0))
    return dict(schema=SCHEMA,independent_repetitions=2,records=days,
        unit_conversion_to_pcse_qualified=False,crop_initial_state_matched=False,
        physical_crop_coupling_admitted=False)
class TestSevenDays(unittest.TestCase):
    def test_seven_consecutive_days_supported_as_native_data_only(self):
        self.assertEqual(len(require_native_sequence(specimen())),7)
        with self.assertRaisesRegex(ValueError,"not scientifically established"):
            pcse_weather_provider_from_native(specimen())
        print("EXT01_SEVEN_DAY_NATIVE_HISTORY_CANNOT_PRETEND_PCSE_FORCING")
    def test_actual_seven_day_fortran_source_log_fixture(self):
        source=Path(__file__).with_name('test_data')/'ext01_swap5_native_1999_weather_sequence.json'
        rows=require_native_sequence(json.loads(source.read_text()))
        self.assertEqual(len(rows),7)
        self.assertEqual(rows[3]['date'],'1999-01-23')
        self.assertAlmostEqual(rows[3]['tmin_c'],-2.8)
        self.assertEqual(rows[3]['radiation_j_m2_day'],794000)
        print('EXT01_REAL_SEVEN_DAY_NATIVE_WEATHER_IMPORTED_WITHOUT_PCSE_SCIENCE_ADMISSION')

    def test_missing_day_or_forged_calendar_refused(self):
        w=specimen()
        w["records"].pop(2)
        with self.assertRaisesRegex(ValueError,"seven complete"):
            require_native_sequence(w)
        w=specimen()
        w["records"][2]["date"]="2010-04-18"
        with self.assertRaisesRegex(ValueError,"nonconsecutive"):
            require_native_sequence(w)
    def test_forged_conversion_and_crop_admission_refused(self):
        for flag in ("unit_conversion_to_pcse_qualified","crop_initial_state_matched",
                     "physical_crop_coupling_admitted"):
            w=specimen()
            w[flag]=True
            with self.subTest(flag=flag),self.assertRaisesRegex(ValueError,"unqualified|unsupported"):
                require_native_sequence(w)
    def test_missing_meteorology_rejected(self):
        w=specimen()
        del w["records"][0]["etref_native"]
        with self.assertRaisesRegex(ValueError,"incomplete"):
            require_native_sequence(w)
if __name__=="__main__":
    unittest.main()

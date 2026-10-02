# -*- coding: utf-8 -*-
"""Self-contained WOFOST 8.1 + MLWB + SNOMIN scientific E2E fixture.

Crop parameters are vendored from ajwdewit/WOFOST_crop_parameters,
wofost81@31b217f3958a7ff48ea875368385ebe2218f3dd4.
The soil profile is synthetic and is a qualification test stand, not a
claim of a calibrated Dutch soil.
"""
import datetime as dt
import os
import unittest

import yaml

from pcse.base import ParameterProvider, WeatherDataProvider, WeatherDataContainer
from pcse.models import Wofost81_NWLP_MLWB_SNOMIN


class FixtureWeatherProvider(WeatherDataProvider):
    def __init__(self, rows):
        super().__init__()
        for row in rows:
            row = dict(row)
            row.pop("SNOWDEPTH", None)
            wdc = WeatherDataContainer(**row)
            self._store_WeatherDataContainer(wdc, wdc.DAY)


def _value_only(parameters):
    return {key: value[0] for key, value in parameters.items() if key != "Metadata"}


def _crop_parameters():
    here = os.path.dirname(__file__)
    path = os.path.join(here, "test_data", "wofost81_authority_wheat.yaml")
    with open(path, encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    variety = data["CropParameters"]["Varieties"]["Winter_wheat_102"]
    return _value_only(variety)


def _weather():
    root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    path = os.path.join(root, "tests", "test_data", "test_potentialproduction_wofost72_01.yaml")
    with open(path, encoding="utf-8") as fp:
        data = yaml.safe_load(fp)
    return FixtureWeatherProvider(data["WeatherVariables"])


def _soil_and_site():
    sm = [-1.0, 0.50, 1.0, 0.46, 1.3, 0.42, 1.7, 0.36,
          2.0, 0.31, 2.3, 0.26, 2.7, 0.20, 3.0, 0.16,
          3.3, 0.13, 3.7, 0.10, 4.0, 0.085, 4.2, 0.075, 6.0, 0.04]
    cond = [-1.0, 1.5, 1.0, 0.7, 1.3, 0.2, 1.7, -0.7,
            2.0, -1.5, 2.3, -2.2, 2.7, -3.2, 3.0, -4.0,
            3.3, -4.8, 3.7, -5.8, 4.0, -6.7, 4.2, -7.2, 6.0, -10.0]

    def layer(thickness, fsom):
        return {
            "SMfromPF": sm, "CONDfromPF": cond, "CRAIRC": 0.08,
            "CNRatioSOMI": 10.0, "RHOD": 1.35, "Soil_pH": 6.8,
            "Thickness": thickness, "FSOMI": fsom,
        }

    profile = {
        "PFWiltingPoint": 4.2,
        "PFFieldCapacity": 2.0,
        "SurfaceConductivity": 20.0,
        "SoilLayers": [
            layer(30.0, 0.025), layer(30.0, 0.015),
            layer(30.0, 0.008), layer(30.0, 0.004),
        ],
        "GroundWater": None,
    }

    soil = {
        "SoilProfileDescription": profile,
        "IFUNRN": 0, "NOTINF": 0.0, "SSI": 0.0, "SSMAX": 2.0,
        "SMLIM": 0.31, "WAV": 25.0,
        "A0SOM": 20.0, "CNRatioBio": 8.0, "FASDIS": 0.4,
        "KDENIT_REF": 0.02, "KNIT_REF": 0.05, "KSORP": 0.0005,
        "MRCDIS": 0.001, "NO3ConcR": 0.0, "NH4ConcR": 0.0,
        "NO3I": [20.0, 15.0, 10.0, 5.0],
        "NH4I": [5.0, 3.0, 2.0, 1.0],
        "WFPS_CRIT": 0.8,
    }
    site = {"CO2": 420.0}
    return soil, site


def _agro():
    return [{
        dt.date(2010, 4, 16): {
            "CropCalendar": {
                "crop_name": "wheat",
                "variety_name": "Winter_wheat_102",
                "crop_start_date": dt.date(2010, 4, 16),
                "crop_start_type": "emergence",
                "crop_end_date": dt.date(2010, 9, 20),
                "crop_end_type": "harvest",
                "max_duration": 180,
            },
            "TimedEvents": None,
            "StateEvents": None,
        }
    }]


class TestWOFOST81SNOMINE2E(unittest.TestCase):

    def test_full_lifecycle_preserves_nonnegative_n_and_produces_crop(self):
        crop = _crop_parameters()
        soil, site = _soil_and_site()
        params = ParameterProvider(cropdata=crop, soildata=soil, sitedata=site)
        model = Wofost81_NWLP_MLWB_SNOMIN(params, _weather(), _agro())
        model.run_till_terminate()
        output = model.get_output()

        self.assertGreater(len(output), 30)
        self.assertGreater(max(row["TAGP"] for row in output if row["TAGP"] is not None), 0.0)

        for row in output:
            if row.get("NH4") is not None:
                self.assertTrue(all(v >= -1e-12 for v in row["NH4"]))
            if row.get("NO3") is not None:
                self.assertTrue(all(v >= -1e-12 for v in row["NO3"]))


if __name__ == "__main__":
    unittest.main()

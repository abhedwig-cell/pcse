"""EXT01 new, independently pinned barley case; NOT the original PP01 case001.

WOFOST81 barley YAML is copied from upstream git blob
0a850879538bd43fe7bf2973d6238ae672d49bdb.
The weather is the separately versioned synthetic 2010 qualification fixture,
not historical 2025 barley meteorology. This is a NEW reference case.
"""
import datetime as dt
from pathlib import Path
import unittest
from unittest.mock import patch
import yaml
from pcse.base import ParameterProvider
from pcse.engine import Engine
from pcse.crop import wofost81
from pcse.tests.test_wofost81_external_soil_off import ExternalET, ExternalSoilWaterOff
from pcse.tests.test_wofost81_snomin_e2e import _weather, _soil_and_site


def new_barley_case(split_days=None):
    parameters = yaml.safe_load(Path(__file__).with_name("test_data").joinpath(
        "ext01_barley_wofost81_source.yaml").read_text())
    barley = parameters["CropParameters"]["Varieties"]["Spring_barley_301"]
    crop = {k: v[0] for k,v in barley.items() if k != "Metadata"}
    soil,site = _soil_and_site()
    agro=[{dt.date(2010,4,16): {"CropCalendar":{
        "crop_name":"barley","variety_name":"Spring_barley_301",
        "crop_start_date":dt.date(2010,4,16),
        "crop_start_type":"emergence",
        "crop_end_date":dt.date(2010,9,20),
        "crop_end_type":"harvest","max_duration":180},
        "TimedEvents":None,"StateEvents":None}}]
    with patch.object(wofost81,"Evapotranspiration",ExternalET):
        m=Engine(ParameterProvider(cropdata=crop,soildata=soil,sitedata=site),
                 _weather(),agro,
                 config=Path(__file__).with_name("data_wofost81_external_soil_off.conf"))
        if split_days is None:
            m.run(days=60)
        else:
            assert 0 < split_days < 60
            m.run(days=split_days)
            m.run(days=60-split_days)
        return m.get_output(),m


class PinnedBarleyNewCase(unittest.TestCase):
    def test_new_barley_sixty_days_crop_only(self):
        rows,model = new_barley_case()
        self.assertIsInstance(model.soil,ExternalSoilWaterOff)
        self.assertIsNone(model.soil.waterbalance)
        self.assertGreater(len(rows),40)
        self.assertTrue(any(row.get("LAI") is not None and row["LAI"]>0 for row in rows))
        self.assertTrue(any(row.get("TAGP") is not None and row["TAGP"]>0 for row in rows))
        print("EXT01_NEW_BARLEY_NOT_PP01",len(rows),rows[-1]["day"])

    def test_continuation_same_live_engine(self):
        whole,_=new_barley_case()
        segmented,_=new_barley_case(split_days=30)
        self.assertEqual(whole,segmented)
        print("EXT01_BARLEY_IN_PROCESS_CONTINUATION_IDENTICAL",len(whole))

    def test_repeat_two_independent_engines(self):
        first,_=new_barley_case()
        second,_=new_barley_case()
        self.assertEqual(first,second)
        print("EXT01_BARLEY_TWO_ENGINES_IDENTICAL",len(first))

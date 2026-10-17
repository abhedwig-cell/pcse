"""Research-only crop with external daily water receipt, no PCSE soil-water model.

This deliberately patches PCSE composition within an isolated test process.
It is not an application API, nor a qualified SWAP interface.
"""
import datetime
import unittest
from unittest.mock import patch
from pcse.base import ParameterProvider, SimulationObject, RatesTemplate
from pcse.traitlets import Float
from pcse.decorators import prepare_rates
from pcse.soil.soil_wrappers import SoilModuleWrapper_PP
from pcse.crop import wofost81
from pcse.models import Wofost81_PP
from pcse.tests.test_wofost81_snomin_e2e import _crop_parameters, _soil_and_site, _weather, _agro

class ExternalET(SimulationObject):
    class RateVariables(RatesTemplate):
        TRA=Float(0.)
        TRAMX=Float(0.)
        RFTRA=Float(1.)
    def initialize(self,day,kiosk,params):
        self.rates=self.RateVariables(kiosk,publish=["TRA","TRAMX","RFTRA"])
    @prepare_rates
    def __call__(self, day, drv):
        # Static *synthetic* accepted daily SWAP receipt, units cm/day.
        # Future runtime must supply day, accepted window identity and actual
        # SWAP5 rates; constant values here isolate PCSE component ownership.
        self.rates.TRA=0.15
        self.rates.TRAMX=0.30
        self.rates.RFTRA=0.5
        return self.rates.TRA,self.rates.TRAMX

class ExternalSoilWaterOff(SoilModuleWrapper_PP):
    waterbalance_class=None

class ExternalReceiptSmoke(unittest.TestCase):
    def test_crop_calculates_without_pcse_waterbalance(self):
        crop=_crop_parameters()
        soil,site=_soil_and_site()
        params=ParameterProvider(cropdata=crop,soildata=soil,sitedata=site)
        with patch.object(wofost81,"Evapotranspiration",ExternalET), patch(
                "pcse.soil.soil_wrappers.SoilModuleWrapper_PP",ExternalSoilWaterOff):
            # Engine configuration resolved by import path in the config loader:
            # override the class attribute used by configuration at runtime.
            from pcse import soil
            from pcse.soil import soil_wrappers
            import pcse.conf.Wofost81_PP as config
            old=config.SOIL
            config.SOIL=ExternalSoilWaterOff
            try:
                engine=Wofost81_PP(params,_weather(),_agro())
                engine.run(days=10)
                rows=engine.get_output()
            finally:
                config.SOIL=old
        self.assertGreater(len(rows),0)
        self.assertIsInstance(engine.soil,ExternalSoilWaterOff)
        self.assertIsNone(engine.soil.waterbalance)
        self.assertTrue(all(r.get("TAGP") is None or r["TAGP"]>=0 for r in rows))

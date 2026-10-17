"""Research-only crop with external daily water receipt, no PCSE soil-water model.

This deliberately patches PCSE composition within an isolated test process.
It is not an application API, nor a qualified SWAP interface.
"""
from pathlib import Path
import unittest
from unittest.mock import patch
from pcse.base import ParameterProvider, SimulationObject, RatesTemplate
from pcse.traitlets import Float
from pcse.decorators import prepare_rates
from pcse.soil.soil_wrappers import SoilModuleWrapper_PP
from pcse.crop import wofost81
from pcse.engine import Engine
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
    class RateVariables(RatesTemplate):
        EVS=Float(0.)
    def initialize(self, day, kiosk, parvalues):
        super().initialize(day, kiosk, parvalues)
        self.rates=self.RateVariables(kiosk,publish=["EVS"])
        self.rates.EVS=0.0
    def calc_rates(self, day, drv):
        super().calc_rates(day,drv)
        self.rates.EVS=0.0

class ExternalReceiptSmoke(unittest.TestCase):
    def test_crop_calculates_without_pcse_waterbalance(self):
        crop=_crop_parameters()
        soil,site=_soil_and_site()
        params=ParameterProvider(cropdata=crop,soildata=soil,sitedata=site)
        with patch.object(wofost81, "Evapotranspiration", ExternalET):
            engine=Engine(params,_weather(),_agro(),
                          config=Path(__file__).with_name("data_wofost81_external_soil_off.conf"))
            engine.run(days=60)
            rows=engine.get_output()
        self.assertGreater(len(rows),40)
        self.assertTrue(any(r.get("LAI") is not None and r["LAI"] > 0 for r in rows))
        self.assertTrue(any(r.get("TAGP") is not None and r["TAGP"] > 0 for r in rows))
        self.assertIsInstance(engine.soil,ExternalSoilWaterOff)
        self.assertIsNone(engine.soil.waterbalance)
        self.assertTrue(all(r.get("TAGP") is None or r["TAGP"]>=0 for r in rows))


    def test_real_swap5_receipt_replayed_as_crop_only_input(self):
        # This exact value originates in successful SWAP5 physically accepted
        # ROOTED weather fixture run 39027378775 (case j=1,d=2).
        # SWAP event dates/meteorology differ from PCSE 2010 wheat fixture:
        # portable numeric receipt only, NOT coupled scientific equivalence.
        actual = 1.0370706377336118e-3
        potential = 1.0370706377336118e-3
        self.assertGreater(potential, 0.0)
        self.assertLessEqual(actual, potential)
        observed = []
        def receipt_call(self, day, drv):
            self.rates.TRA = actual
            self.rates.TRAMX = potential
            self.rates.RFTRA = actual / potential
            observed.append((day, self.rates.TRA, self.rates.TRAMX, self.rates.RFTRA))
            return self.rates.TRA, self.rates.TRAMX
        soil,site = _soil_and_site()
        params=ParameterProvider(cropdata=_crop_parameters(),soildata=soil,sitedata=site)
        with patch.object(ExternalET,"__call__",receipt_call):
            with patch.object(wofost81,"Evapotranspiration",ExternalET):
                engine=Engine(params,_weather(),_agro(),
                              config=Path(__file__).with_name("data_wofost81_external_soil_off.conf"))
                engine.run(days=60)
                rows=engine.get_output()
        self.assertGreater(len(observed),50)
        self.assertIsNone(engine.soil.waterbalance)
        self.assertTrue(all(t==actual and p==potential and f==1.0 for _,t,p,f in observed))
        self.assertTrue(any(row.get("TAGP") is not None and row["TAGP"]>0 for row in rows))
        print("SWAP5_ACCEPTED_RECEIPT_REPLAY", actual, potential, len(observed))

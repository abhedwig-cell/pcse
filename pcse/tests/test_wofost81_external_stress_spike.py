"""Research spike: inject a synthetic accepted transpiration ratio into real PCSE.
Still runs PCSE soil water and SNOMIN: NOT a SWAP soil replacement.
"""
import unittest
from unittest.mock import patch
from pcse.crop.evapotranspiration import EvapotranspirationWrapper
from pcse.tests.test_wofost81_snomin_e2e import _run

class ExternalStressSpike(unittest.TestCase):
    def test_stress_reaches_real_crop(self):
        reference = _run()
        original = EvapotranspirationWrapper.__call__
        seen = []
        def inject(self, day, drv):
            result = original(self, day, drv)
            if result is None:
                return None
            tra, tramx = result
            rates = self.etmodule.rates
            if tramx is not None and tramx > 0:
                rates.RFTRA = 0.5
                rates.TRA = 0.5 * rates.TRAMX
                seen.append((day, rates.TRA, rates.TRAMX))
                return rates.TRA, rates.TRAMX
            return tra, tramx
        with patch.object(EvapotranspirationWrapper, "__call__", inject):
            stressed = _run()
        self.assertGreater(len(seen), 5)
        self.assertEqual([r["day"] for r in reference], [r["day"] for r in stressed])
        vals = [(a["TAGP"],b["TAGP"]) for a,b in zip(reference,stressed)
                if a.get("TAGP") is not None and b.get("TAGP") is not None]
        self.assertTrue(any(abs(a-b)>1e-7 for a,b in vals))
        self.assertTrue(all(abs(tra-.5*tramx)<1e-10 for _,tra,tramx in seen))
        print("REAL_ET_INJECTION",len(seen),vals[-1])

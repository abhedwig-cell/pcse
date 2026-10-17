"""Research spike: inject a synthetic crop stress ratio into real PCSE.
Still runs PCSE soil water and SNOMIN; TRA stays soil-owned. NOT a SWAP soil replacement.
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
            rates = self.etmodule.rates
            tramx = rates.TRAMX
            if tramx is not None and tramx > 0:
                rates.RFTRA = 0.5
                seen.append((day, rates.TRA, rates.TRAMX, rates.RFTRA))
                return result
            return result
        with patch.object(EvapotranspirationWrapper, "__call__", inject):
            stressed = _run()
        self.assertGreater(len(seen), 5)
        self.assertEqual([r["day"] for r in reference], [r["day"] for r in stressed])
        vals = [(a["TAGP"],b["TAGP"]) for a,b in zip(reference,stressed)
                if a.get("TAGP") is not None and b.get("TAGP") is not None]
        self.assertTrue(any(abs(a-b)>1e-7 for a,b in vals))
        self.assertTrue(all(abs(rftra-.5)<1e-10 for _,tra,tramx,rftra in seen))
        print("REAL_ET_INJECTION",len(seen),vals[-1])

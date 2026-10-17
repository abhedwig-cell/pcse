"""Focused reachability probe for WOFOST81 aboveground crop N and NMAXLV.

Uses the already admitted scientific winter wheat + MLWB + SNOMIN fixture.
A passing run establishes only coverage of this fixture, not global reachability.
"""
import unittest
from math import isfinite

from pcse.tests.test_wofost81_snomin_e2e import _run, _crop_parameters


def _low_mineral_n(soil):
    soil["NH4I"] = [0.0] * 4
    soil["NO3I"] = [0.0] * 4
    for layer in soil["SoilProfileDescription"]["SoilLayers"]:
        layer["CNRatioSOMI"] = 80.0
        layer["FSOMI"] = max(layer["FSOMI"], 0.03)


class TestNStressReachability(unittest.TestCase):
    def test_authority_wheat_and_low_n_profile(self):
        crop = _crop_parameters()
        nmax = crop["NMAXLV_TB"]
        # The reference cultivar specifies a positive leaf-N maximum
        # throughout the represented DVS range. Do not infer this for
        # arbitrary externally supplied crops.
        self.assertGreater(min(nmax[1::2]), 0.0)

        for label, modifier in (("reference", None), ("low_mineral_n", _low_mineral_n)):
            with self.subTest(profile=label):
                rows = _run(modifier)
                live = [row for row in rows if row.get("NamountLV") is not None
                        and row.get("NamountST") is not None
                        and row.get("NamountSO") is not None]
                self.assertGreater(len(live), 0)
                totals = [row["NamountLV"] + row["NamountST"] + row["NamountSO"]
                          for row in live]
                self.assertTrue(all(isfinite(n) for n in totals))
                self.assertGreaterEqual(min(totals), -1e-10)
                print(f"N_STRESS_REACHABILITY profile={label} n={len(totals)} "
                      f"min_aboveground_N={min(totals):.12g} "
                      f"min_leaf_N={min(row['NamountLV'] for row in live):.12g}")


if __name__ == "__main__":
    unittest.main()

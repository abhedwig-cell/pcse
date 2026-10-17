"""Focused parameter-domain tests for WOFOST 8.1 N-stress.

No scientific response formulation is changed by these checks.
"""
import unittest

from pcse import exceptions as exc
from pcse.crop.nutrients.n_stress import N_Stress


class TestNStressGrowthRateDomain(unittest.TestCase):
    def test_valid_reference_and_bounds(self):
        for maximum, minimum in ((0.0082, 0.004), (0.0082, 0.), (0.0082, 0.0082)):
            with self.subTest(maximum=maximum, minimum=minimum):
                N_Stress._validate_growth_rates(maximum, minimum)

    def test_invalid_domain(self):
        for maximum, minimum in ((0., 0.), (0., 0.001), (0.0082, -0.001),
                                 (0.0082, 0.01), (-0.01, 0.),
                                 (float("nan"), 0.), (0.0082, float("inf"))):
            with self.subTest(maximum=maximum, minimum=minimum):
                with self.assertRaises(exc.PCSEError):
                    N_Stress._validate_growth_rates(maximum, minimum)


if __name__ == "__main__":
    unittest.main()

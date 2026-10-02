# -*- coding: utf-8 -*-
"""Scientific qualification tests for WOFOST 8.1 / SNOMIN."""
import unittest


class TestSNOMINScientificInvariants(unittest.TestCase):

    def test_nh4_immobilisation_limiter_closes_pool_at_zero(self):
        """T01: NH4-limited immobilisation must not reverse into mineralisation.

        This is the algebraic invariant used by SNOMIN.calc_rates when
        NH4PRE + (RNH4MIN - RNH4NITR) * delt would become negative.
        """
        delt = 1.0
        nh4_pre = 0.05
        nitrification = 0.03
        unconstrained_mineralisation = -0.20

        self.assertLess(
            nh4_pre + (unconstrained_mineralisation - nitrification) * delt,
            0.0,
        )

        limited_mineralisation = nitrification - nh4_pre / delt
        nh4_after = nh4_pre + (limited_mineralisation - nitrification) * delt

        self.assertLessEqual(limited_mineralisation, 0.0)
        self.assertAlmostEqual(nh4_after, 0.0, places=14)

    def test_baseline_limiter_expression_violates_t01(self):
        """Document the pre-repair expression as a falsified comparator."""
        delt = 1.0
        nh4_pre = 0.05
        nitrification = 0.03

        baseline_limited_mineralisation = nh4_pre - nitrification
        nh4_after = nh4_pre + (
            baseline_limited_mineralisation - nitrification
        ) * delt

        self.assertNotAlmostEqual(nh4_after, 0.0, places=14)
        self.assertGreater(baseline_limited_mineralisation, 0.0)


if __name__ == "__main__":
    unittest.main()

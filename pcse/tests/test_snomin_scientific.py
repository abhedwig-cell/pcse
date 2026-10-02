# -*- coding: utf-8 -*-
"""Scientific qualification tests for WOFOST 8.1 / SNOMIN."""
import unittest
from types import SimpleNamespace

import numpy as np

from pcse.soil.snomin import SNOMIN


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


    @staticmethod
    def _layer(thickness_m=0.5, rhod=1300.0):
        return SimpleNamespace(
            Thickness_m=thickness_m,
            RHOD_kg_per_m3=rhod,
        )

    def test_t02_uptake_priority_is_explicitly_nh4_before_no3(self):
        """T02 characterization: uptake consumes NH4 before NO3 in each layer."""
        model = SNOMIN.SoilInorganicNModel()
        layers = [self._layer()]
        sm = np.array([0.30])
        demand = 0.06
        nh4 = np.array([0.04])
        no3 = np.array([0.04])

        rnh4, rno3 = model.calculate_N_uptake_rates(
            layers, 1.0, 0.0, demand, nh4, no3, 0.5, sm
        )

        self.assertAlmostEqual(rnh4[0], 0.04)
        self.assertAlmostEqual(rno3[0], 0.02)
        self.assertAlmostEqual((rnh4 + rno3).sum(), demand)

    def test_t03_navail_is_invariant_to_homogeneous_layer_refinement(self):
        """T03: splitting a homogeneous fully rooted profile must preserve NAVAIL."""
        model = SNOMIN.SoilInorganicNModel()
        sm1 = np.array([0.30])
        nh41 = np.array([0.04])
        no31 = np.array([0.06])
        one = [self._layer(1.0)]

        sm2 = np.array([0.30, 0.30])
        nh42 = np.array([0.02, 0.02])
        no32 = np.array([0.03, 0.03])
        two = [self._layer(0.5), self._layer(0.5)]

        a = model.calculate_NAVAIL(one, 0.0, nh41, no31, 1.0, sm1)
        b = model.calculate_NAVAIL(two, 0.0, nh42, no32, 1.0, sm2)
        self.assertAlmostEqual(a, b, places=14)

    def test_t05_navail_is_continuous_across_layer_boundary(self):
        """T05: an infinitesimal root crossing may only expose an infinitesimal N amount."""
        model = SNOMIN.SoilInorganicNModel()
        layers = [self._layer(0.5), self._layer(0.5)]
        sm = np.array([0.30, 0.30])
        nh4 = np.zeros(2)
        no3 = np.array([0.0, 0.10])
        eps = 1.0e-6

        below = model.calculate_NAVAIL(layers, 0.0, nh4, no3, 0.5 - eps, sm)
        at = model.calculate_NAVAIL(layers, 0.0, nh4, no3, 0.5, sm)
        above = model.calculate_NAVAIL(layers, 0.0, nh4, no3, 0.5 + eps, sm)

        self.assertAlmostEqual(below, 0.0, places=14)
        self.assertAlmostEqual(at, 0.0, places=14)
        self.assertGreater(above, at)
        self.assertLess(above, 1.0e-5)

    def test_t06_vertical_n_distribution_changes_access_only_when_rooting_differs(self):
        """T06: fully rooted homogeneous profiles preserve total NAVAIL; shallow roots do not."""
        model = SNOMIN.SoilInorganicNModel()
        layers = [self._layer(0.5), self._layer(0.5)]
        sm = np.array([0.30, 0.30])
        nh4 = np.zeros(2)
        top = np.array([0.10, 0.0])
        bottom = np.array([0.0, 0.10])

        full_top = model.calculate_NAVAIL(layers, 0.0, nh4, top, 1.0, sm)
        full_bottom = model.calculate_NAVAIL(layers, 0.0, nh4, bottom, 1.0, sm)
        shallow_top = model.calculate_NAVAIL(layers, 0.0, nh4, top, 0.5, sm)
        shallow_bottom = model.calculate_NAVAIL(layers, 0.0, nh4, bottom, 0.5, sm)

        self.assertAlmostEqual(full_top, full_bottom, places=14)
        self.assertGreater(shallow_top, shallow_bottom)
        self.assertAlmostEqual(shallow_bottom, 0.0, places=14)

    def test_snomin04_no3_transport_can_exceed_finite_pool_in_baseline_algorithm(self):
        """Characterize SNOMIN-04: extreme one-day advective flux is not pool-limited."""
        nitrate = SNOMIN.SoilInorganicNModel.SoilNNitrateModel()
        layers = [self._layer(0.10)]
        sm = np.array([0.10])
        no3 = np.array([0.01])
        # 0.20 m/day drainage through only 0.01 m water storage.
        flow = np.array([0.0, 0.20])

        rin, rout = nitrate.calculate_NO3_flow_rates(layers, flow, no3, sm)

        self.assertGreater(rout[0], no3[0])
        self.assertAlmostEqual(rin[0], 0.0)


if __name__ == "__main__":
    unittest.main()

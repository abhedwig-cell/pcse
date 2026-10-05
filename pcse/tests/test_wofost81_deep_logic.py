# -*- coding: utf-8 -*-
"""Deep logic tests for WOFOST/PCSE execution ordering."""
import datetime as dt
import unittest

from pcse import signals
from pcse.agromanager import CropCalendar, StateEventsDispatcher
from pcse.base import VariableKiosk
from pcse.soil.multilayer_waterbalance import WaterBalanceLayered
from pcse.crop.nutrients.n_demand_uptake import N_Demand_Uptake
from pcse.crop.wofost81 import Wofost81
from pcse import exceptions as exc
from pcse.base.dispatcher import dispatcher


class TestCropCalendarLogic(unittest.TestCase):

    def test_harvest_precedes_max_duration_when_both_are_same_day(self):
        kiosk = VariableKiosk()
        start = dt.date(2026, 1, 1)
        finishes = []

        def on_finish(day=None, finish_type=None, crop_delete=None):
            finishes.append((day, finish_type, crop_delete))

        dispatcher.connect(on_finish, signal=signals.crop_finish)
        try:
            cc = CropCalendar(
                kiosk, crop_name="x", variety_name="x",
                crop_start_date=start, crop_start_type="emergence",
                crop_end_date=start + dt.timedelta(days=2),
                crop_end_type="harvest", max_duration=2,
            )
            cc(start)
            cc(start + dt.timedelta(days=1))
            cc(start + dt.timedelta(days=2))
        finally:
            dispatcher.disconnect(on_finish, signal=signals.crop_finish)

        # Baseline logic overwrites harvest with max_duration on equality.
        self.assertEqual(len(finishes), 1)
        self.assertEqual(finishes[0][1], "harvest")


class TestStateEventLogic(unittest.TestCase):

    def test_rising_event_fires_when_first_observed_state_is_exact_threshold(self):
        kiosk = VariableKiosk()
        owner = 99991
        kiosk.register_variable(owner, "X", "S", publish=True)
        kiosk.set_variable(owner, "X", 1.0)
        fired = []

        def on_event(**kwargs):
            fired.append(kwargs)

        dispatcher.connect(on_event, signal=signals.apply_n)
        try:
            dsp = StateEventsDispatcher(
                kiosk, event_signal="apply_n", event_state="X",
                zero_condition="rising", name="threshold", comment="",
                events_table=[{1.0: {"N_amount": 1.0, "N_recovery": 1.0}}],
            )
            dsp(dt.date(2026, 1, 1))
        finally:
            dispatcher.disconnect(on_event, signal=signals.apply_n)

        # Exact equality at first observation is a valid reached threshold.
        self.assertEqual(len(fired), 1)


    def test_first_exact_threshold_fires_once_for_all_directions(self):
        for direction in ("rising", "falling", "either"):
            with self.subTest(direction=direction):
                kiosk = VariableKiosk()
                kiosk.register_variable(99993, "Z", "S", publish=True)
                kiosk.set_variable(99993, "Z", 1.)
                fired = []
                def on_event(**kwargs):
                    fired.append(kwargs)
                dispatcher.connect(on_event, signal=signals.apply_n)
                try:
                    dsp = StateEventsDispatcher(
                        kiosk, event_signal="apply_n", event_state="Z",
                        zero_condition=direction, name="exact", comment="",
                        events_table=[{1.: {"N_amount": 1., "N_recovery": 1.}}],
                    )
                    dsp(dt.date(2026, 1, 1))
                    dsp(dt.date(2026, 1, 2))
                    self.assertEqual(len(fired), 1)
                finally:
                    dispatcher.disconnect(on_event, signal=signals.apply_n)

    def test_rising_jump_crosses_all_thresholds_once(self):
        kiosk = VariableKiosk()
        owner = 99992
        kiosk.register_variable(owner, "Y", "S", publish=True)
        kiosk.set_variable(owner, "Y", 0.0)
        fired = []

        def on_event(**kwargs):
            fired.append(kwargs["N_amount"])

        dispatcher.connect(on_event, signal=signals.apply_n)
        try:
            dsp = StateEventsDispatcher(
                kiosk, event_signal="apply_n", event_state="Y",
                zero_condition="rising", name="multi", comment="",
                events_table=[
                    {0.3: {"N_amount": 3.0, "N_recovery": 1.0}},
                    {0.6: {"N_amount": 6.0, "N_recovery": 1.0}},
                    {1.1: {"N_amount": 11.0, "N_recovery": 1.0}},
                ],
            )
            dsp(dt.date(2026, 1, 1))
            kiosk.set_variable(owner, "Y", 1.2)
            dsp(dt.date(2026, 1, 2))
            dsp(dt.date(2026, 1, 3))
        finally:
            dispatcher.disconnect(on_event, signal=signals.apply_n)

        self.assertEqual(fired, [3.0, 6.0, 11.0])


class TestSameDayManagementAccumulation(unittest.TestCase):

    def test_irrigation_handlers_accumulate_independent_same_day_events(self):
        wb = WaterBalanceLayered.__new__(WaterBalanceLayered)
        wb._RIRR = 0.0
        wb._on_IRRIGATE(2.0, 0.5)
        wb._on_IRRIGATE(3.0, 0.8)
        self.assertAlmostEqual(wb._RIRR, 3.4)



class TestNitrogenDonorTransactions(unittest.TestCase):

    def test_senescence_reserves_n_before_translocation(self):
        # 10 kg N in 100 kg living biomass, 80 kg dies today, residual
        # concentration of survivors is 0.02 kg N/kg DM.
        available = N_Demand_Uptake._available_translocatable_after_death(
            n_amount=10.0, living_biomass=100.0,
            death_biomass=80.0, residual_fraction=0.02
        )
        # Death owns 8 kg N; surviving 20 kg DM must retain 0.4 kg N.
        self.assertAlmostEqual(available, 1.6)

    def test_complete_senescence_leaves_no_translocatable_n(self):
        available = N_Demand_Uptake._available_translocatable_after_death(
            n_amount=10.0, living_biomass=100.0,
            death_biomass=100.0, residual_fraction=0.01
        )
        self.assertEqual(available, 0.0)



class TestFallowRootZoneOwnership(unittest.TestCase):

    def test_crop_finish_marks_mlwb_root_geometry_for_reset(self):
        wb = WaterBalanceLayered.__new__(WaterBalanceLayered)
        wb.rooted_layer_needs_reset = False
        wb._on_CROP_FINISH()
        self.assertTrue(wb.rooted_layer_needs_reset)



class TestRepairOracles(unittest.TestCase):

    def test_biomass_reallocation_is_donor_limited(self):
        self.assertEqual(Wofost81._limit_reallocation_request(30., 20., 5.), 15.)
        self.assertEqual(Wofost81._limit_reallocation_request(30., 20., 20.), 0.)

    def test_n_parameter_validation_exception_is_importable(self):
        self.assertTrue(issubclass(exc.PCSEError, Exception))


class TestIntegratedRepairQualification(unittest.TestCase):
    @staticmethod
    def model(crop_changes=None, agro=None):
        from .test_wofost81_snomin_e2e import (
            _crop_parameters, _soil_and_site, _weather, _agro,
        )
        from pcse.base import ParameterProvider
        from pcse.models import Wofost81_NWLP_MLWB_SNOMIN
        crop = _crop_parameters()
        crop.update(crop_changes or {})
        soil, site = _soil_and_site()
        return Wofost81_NWLP_MLWB_SNOMIN(
            ParameterProvider(cropdata=crop, soildata=soil, sitedata=site),
            _weather(), agro or _agro(),
        )

    def test_reallocation_transaction_is_activated_in_full_lifecycle(self):
        m = self.model(dict(REALLOC_DVS=1., REALLOC_LEAF_FRACTION=1.,
                            REALLOC_STEM_FRACTION=1., REALLOC_LEAF_RATE=1.,
                            REALLOC_STEM_RATE=1., REALLOC_EFFICIENCY=0.8))
        activated = False
        while m.crop is not None:
            c = m.crop
            k = m.kiosk
            r = c.rates
            lv, st = r.REALLOC_LV, r.REALLOC_ST
            activated |= lv + st > 0.
            self.assertLessEqual(lv, max(0., k.WLV - k.DRLV) + 1e-12)
            self.assertLessEqual(st, max(0., k.WST - k.DRST) + 1e-12)
            self.assertAlmostEqual(r.REALLOC_SO, 0.8 * (lv + st))
            m.run(days=1)
            if m.crop is not None:
                self.assertGreaterEqual(m.kiosk.WLV, -1e-12)
                self.assertGreaterEqual(m.kiosk.WST, -1e-12)
        self.assertTrue(activated)

    def test_irrigation_rate_consumes_accumulated_events_once(self):
        m = self.model()
        wb = m.soil.waterbalance
        wb._on_IRRIGATE(2., 0.5)
        wb._on_IRRIGATE(3., 0.8)
        wb.calc_rates(m.day, m.drv)
        self.assertAlmostEqual(wb.rates.RIRR, 3.4)
        self.assertEqual(wb._RIRR, 0.)
        wb.calc_rates(m.day, m.drv)
        self.assertEqual(wb.rates.RIRR, 0.)

    def test_configuration_rejects_invalid_crop_domains(self):
        names = ["REALLOC_STEM_FRACTION", "REALLOC_LEAF_FRACTION",
                 "REALLOC_STEM_RATE", "REALLOC_LEAF_RATE", "REALLOC_EFFICIENCY",
                 "NFIX_FR", "NMAXRT_FR", "NMAXST_FR", "NRESIDLV", "NRESIDST", "NRESIDRT"]
        for name in names:
            for value in (-0.1, 1.1):
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(exc.PCSEError, name):
                        self.model({name: value})
        with self.assertRaisesRegex(exc.PCSEError, "NMAXSO"):
            self.model({"NMAXSO": -0.1})

    def test_configuration_rejects_invalid_layered_et_switches(self):
        for name in ("IAIRDU", "IOX"):
            with self.subTest(name=name):
                with self.assertRaisesRegex(exc.PCSEError, name):
                    self.model({name: 2})

    def test_amendments_accumulate_and_invalid_events_leave_pools_unchanged(self):
        import numpy as np
        m = self.model()
        n = m.soil.nutrientbalance
        event = dict(amount=100., application_depth=30., cnratio=10.,
                     f_orgmat=0.2, f_NH4N=0.1, f_NO3N=0.2, initial_age=0.)
        before_nh4 = n._RNH4AM.copy()
        before_no3 = n._RNO3AM.copy()
        n._on_APPLY_N_SNOMIN(**event)
        first_nh4 = np.asarray(n._RNH4AM - before_nh4, dtype=float)
        first_no3 = np.asarray(n._RNO3AM - before_no3, dtype=float)
        n._on_APPLY_N_SNOMIN(**event)
        np.testing.assert_allclose(np.asarray(n._RNH4AM - before_nh4, dtype=float), 2 * first_nh4)
        np.testing.assert_allclose(np.asarray(n._RNO3AM - before_no3, dtype=float), 2 * first_no3)
        self.assertAlmostEqual(first_nh4.sum(), 0.001)
        self.assertAlmostEqual(first_no3.sum(), 0.002)
        invalid = dict(amount=-1., application_depth=0., cnratio=0.,
                       f_orgmat=1.1, f_NH4N=-0.1, f_NO3N=1.1, initial_age=-1.)
        for name, value in invalid.items():
            with self.subTest(name=name):
                old = n.states.NH4.copy()
                shape = n.states.ORGMAT.shape
                with self.assertRaises(exc.PCSEError):
                    n._on_APPLY_N_SNOMIN(**dict(event, **{name: value}))
                np.testing.assert_array_equal(n.states.NH4, old)
                self.assertEqual(n.states.ORGMAT.shape, shape)
        with self.assertRaises(exc.PCSEError):
            n._on_APPLY_N_SNOMIN(**dict(event, f_NH4N=0.6, f_NO3N=0.6))

    def test_fallow_reset_rebuilds_root_zone_without_changing_total_water(self):
        from .test_wofost81_snomin_e2e import _agro
        agro = _agro()
        agro[0][dt.date(2010, 4, 16)]["CropCalendar"]["crop_end_date"] = dt.date(2010, 5, 20)
        agro.append({dt.date(2010, 5, 25): None})
        m = self.model(agro=agro)
        while m.crop is not None:
            m.run(days=1)
        wb = m.soil.waterbalance
        self.assertGreater(wb._RDold, wb._default_RD)
        self.assertNotIn("RD", m.kiosk)
        m.run(days=1)
        self.assertEqual(wb._RDold, wb._default_RD)
        self.assertFalse(wb.rooted_layer_needs_reset)
        self.assertAlmostEqual(wb.states.W + wb.states.WLOW + wb.states.WBOT,
                               wb.states.WC.sum())
        self.assertAlmostEqual(wb.states.SM_MEAN, wb.states.W / wb._default_RD)
        m.run_till_terminate()  # invokes the full water/N balance checks

    def test_n_translocation_runtime_reserves_senescing_donors(self):
        from .test_wofost81_snomin_e2e import _crop_parameters
        k = VariableKiosk()
        values = dict(DVS=1.5, RFTRA=1., NAVAIL=0., WLV=100., WST=100., WRT=100.,
                      WSO=1000., NamountLV=10., NamountST=10., NamountRT=10.,
                      NamountSO=0., GRLV=0., GRST=0., GRRT=0., GRSO=0.,
                      DRLV=80., DRST=100., DRRT=0.)
        for name, value in values.items():
            k.register_variable(87654, name, "S", publish=True)
            k.set_variable(87654, name, value)
        p = _crop_parameters()
        p.update(TCNT=1., DVS_N_TRANSL=0., NMAXSO=0.1,
                 NRESIDLV=0.02, NRESIDST=0.02, NRESIDRT=0.02)
        obj = N_Demand_Uptake(dt.date(2010, 4, 16), k, p)
        obj.calc_rates(dt.date(2010, 4, 16), None)
        self.assertAlmostEqual(obj.rates.RNtranslocationLV, 1.6)
        self.assertEqual(obj.rates.RNtranslocationST, 0.)
        self.assertAlmostEqual(obj.rates.RNtranslocationRT, 8.)
        self.assertAlmostEqual(obj.rates.RNtranslocation, 9.6)
        self.assertAlmostEqual(obj.rates.RNuptake, 0.)
        self.assertGreaterEqual(10. - 8. - obj.rates.RNtranslocationLV, 0.4 - 1e-12)


if __name__ == "__main__":
    unittest.main()

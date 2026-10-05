# -*- coding: utf-8 -*-
"""Deep logic tests for WOFOST/PCSE execution ordering."""
import datetime as dt
import unittest

from pcse import signals
from pcse.agromanager import CropCalendar, StateEventsDispatcher
from pcse.base import VariableKiosk
from pcse.soil.multilayer_waterbalance import WaterBalanceLayered
from pcse.crop.nutrients.n_demand_uptake import N_Demand_Uptake
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


if __name__ == "__main__":
    unittest.main()

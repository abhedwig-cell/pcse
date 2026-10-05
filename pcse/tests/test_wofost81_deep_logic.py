# -*- coding: utf-8 -*-
"""Deep logic tests for WOFOST/PCSE execution ordering."""
import datetime as dt
import unittest

from pcse import signals
from pcse.agromanager import CropCalendar, StateEventsDispatcher
from pcse.base import VariableKiosk
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


if __name__ == "__main__":
    unittest.main()

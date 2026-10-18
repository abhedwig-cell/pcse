"""Experimental SWAP5 accepted-day receipt validator for external PCSE crop-only tests.

No scientific crop formulations are modified. The source values are an
observed fixture witness, not calibrated or aligned to the PCSE crop calendar.
"""
from dataclasses import dataclass
import math
import datetime


@dataclass(frozen=True)
class AcceptedCropDay:
    event_id: str
    t0: float
    t1: float
    actual_root_uptake_cm: float
    potential_transpiration_cm: float

    def rates(self):
        if not self.event_id:
            raise ValueError("missing accepted event identity")
        if not all(math.isfinite(x) for x in (self.t0, self.t1,
                         self.actual_root_uptake_cm, self.potential_transpiration_cm)):
            raise ValueError("non-finite day or flux")
        if self.t1-self.t0 != 1.0:
            raise ValueError("WOFOST daily event must span precisely one day")
        actual, potential = self.actual_root_uptake_cm, self.potential_transpiration_cm
        if actual < 0 or potential < 0:
            raise ValueError("negative integrated root uptake or transpiration")
        if actual > potential + 1e-12:
            raise ValueError("actual uptake exceeds potential")
        if potential == 0:
            if actual != 0:
                raise ValueError("nonzero uptake with zero potential")
            return 0., 0., 1.
        return actual, potential, min(1., actual/potential)

    def require_calendar_alignment(self, crop_day, swap_epoch):
        """Gate for scientific coupling, not required by portable receipt smoke.

        The SWAP qualification uses relative model days with a 1999 epoch;
        the PCSE wheat fixture starts in 2010. Refuse accidental comparison.
        """
        if not isinstance(crop_day, datetime.date) or not isinstance(swap_epoch, datetime.date):
            raise ValueError("calendar dates required")
        expected = swap_epoch + datetime.timedelta(days=self.t0)
        if crop_day != expected:
            raise ValueError(f"SWAP event {expected} != PCSE crop day {crop_day}")
        return True

# -*- coding: utf-8 -*-
"""Scientific invariants for WOFOST 8.1 biomass reallocation."""
import unittest

from pcse.crop.wofost81 import Wofost81


class TestWOFOST81ReallocationScientific(unittest.TestCase):

    def test_reallocation_cannot_exceed_post_senescence_leaf_donor(self):
        actual = Wofost81._limit_reallocation_request(
            requested=30.0, living_donor=20.0, same_day_death=5.0
        )
        self.assertEqual(actual, 15.0)

    def test_reallocation_cannot_make_stem_donor_negative(self):
        actual = Wofost81._limit_reallocation_request(
            requested=50.0, living_donor=12.0, same_day_death=12.0
        )
        self.assertEqual(actual, 0.0)

    def test_reallocation_preserves_request_when_donor_is_sufficient(self):
        actual = Wofost81._limit_reallocation_request(
            requested=4.0, living_donor=20.0, same_day_death=5.0
        )
        self.assertEqual(actual, 4.0)

    def test_storage_credit_is_based_on_committed_not_requested_transfer(self):
        requested_leaf = 30.0
        requested_stem = 20.0
        actual_leaf = Wofost81._limit_reallocation_request(requested_leaf, 20.0, 5.0)
        actual_stem = Wofost81._limit_reallocation_request(requested_stem, 10.0, 2.0)
        efficiency = 0.8

        storage_credit = (actual_leaf + actual_stem) * efficiency

        self.assertEqual(actual_leaf, 15.0)
        self.assertEqual(actual_stem, 8.0)
        self.assertAlmostEqual(storage_credit, 18.4)
        self.assertLess(storage_credit, (requested_leaf + requested_stem) * efficiency)


if __name__ == "__main__":
    unittest.main()

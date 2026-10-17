"""Run the installed WOFOST 8.1 repair qualification without template discovery.

Usage: python -m pcse.tests.qualification
"""
import unittest


def suite():
    from .test_wofost72 import suite as legacy_suite

    modules = (
        "pcse.tests.test_wofost81_deep_logic",
        "pcse.tests.test_snomin_scientific",
        "pcse.tests.test_wofost81_reallocation_scientific",
        "pcse.tests.test_wofost81_snomin_e2e",
        "pcse.tests.test_partitioning",
        "pcse.tests.test_respiration",
        "pcse.tests.test_wofost81_release",
    )
    tests = unittest.TestSuite(
        unittest.defaultTestLoader.loadTestsFromName(name) for name in modules
    )
    tests.addTests(legacy_suite())
    return tests


def main():
    result = unittest.TextTestRunner(verbosity=2).run(suite())
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()

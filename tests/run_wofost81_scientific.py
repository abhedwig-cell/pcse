# -*- coding: utf-8 -*-
"""Run the WOFOST 8.1 scientific qualification suite locally.

Usage:
    python -m tests.run_wofost81_scientific
"""
import unittest

MODULES = [
    "pcse.tests.test_snomin_scientific",
]


def main():
    loader = unittest.defaultTestLoader
    suite = unittest.TestSuite(loader.loadTestsFromName(name) for name in MODULES)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()

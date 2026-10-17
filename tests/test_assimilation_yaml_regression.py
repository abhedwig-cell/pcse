"""Regression for the first inherited WOFOST72 PGASS YAML mismatch."""
import unittest

from tests.run_tests import make_test_suite


class TestHistoricalPGASSYAML(unittest.TestCase):
    def test_assimilation_case_01(self):
        suite = make_test_suite(quick=False)
        matches = []

        def collect(tests):
            for test in tests:
                if isinstance(test, unittest.TestSuite):
                    collect(test)
                elif getattr(test, "YAML_test_input_fname", "").endswith(
                    "test_assimilation_wofost72_01.yaml"
                ):
                    matches.append(test)

        collect(suite)
        self.assertEqual(len(matches), 1, "Expected exactly one historic YAML case")
        result = unittest.TestResult()
        matches[0].run(result)
        self.assertTrue(
            result.wasSuccessful(),
            "Historic PGASS YAML case failed: " + repr(result.failures + result.errors)
        )


if __name__ == "__main__":
    unittest.main()

"""Installed-package release identity and data contracts."""
import importlib.metadata
import importlib.resources
import json
import unittest

import pcse
from pcse import models


class TestRepairRelease(unittest.TestCase):
    def test_installed_version_matches_runtime(self):
        self.assertEqual(importlib.metadata.version("pcse"), pcse.__version__)
        self.assertFalse(pcse.__stable__)

    def test_manifest_matches_runtime_and_preserves_admission_gate(self):
        info = json.loads(importlib.resources.files("pcse").joinpath("release_info.json").read_text())
        self.assertEqual(info["package_version"], pcse.__version__)
        self.assertEqual(info["implementation_revision"], pcse.__wofost81_revision__)
        self.assertFalse(info["official_model_release"])
        self.assertEqual(len(info["included_findings"]), 14)
        self.assertEqual(info["admission"]["swap_migration"], "BLOCKED_UNTIL_SOURCE_ADMISSION")

    def test_crop_parameter_version_and_entrypoints_are_unchanged(self):
        names = ("Wofost81_PP", "Wofost81_WLP_CWB", "Wofost81_WLP_MLWB",
                 "Wofost81_NWLP_CWB_CNB", "Wofost81_NWLP_MLWB_CNB",
                 "Wofost81_NWLP_MLWB_SNOMIN")
        for name in names:
            with self.subTest(model=name):
                self.assertEqual(getattr(models, name).__cropmodelversion__, "8.1")

    def test_scientific_fixtures_are_available_without_source_checkout(self):
        data = importlib.resources.files("pcse.tests.test_data")
        for name in ("wofost81_authority_wheat.yaml", "wofost81_qualification_weather.yaml"):
            with self.subTest(resource=name):
                self.assertTrue(data.joinpath(name).is_file())


if __name__ == "__main__":
    unittest.main()

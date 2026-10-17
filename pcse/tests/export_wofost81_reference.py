"""Export provisional daily WOFOST81 wheat reference traces (not admitted).

Usage: python -m pcse.tests.export_wofost81_reference --out DIR

Only existing scientific fixtures are used. Output is explicitly provisional,
because PART-01 and the formal Python source-admission gate remain open.
"""
import argparse
import datetime
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path

from pcse.tests.test_wofost81_snomin_e2e import _run
from pcse.tests.test_wofost81_nzero_reachability import _low_mineral_n


FIELDS = ("DVS", "LAI", "TAGP", "WLV", "WST", "WRT", "WSO", "RD",
          "RFTRA", "TRA", "CTRAT", "NAVAIL", "Ndemand",
          "NamountLV", "NamountST", "NamountRT", "NamountSO",
          "NuptakeTotal", "NH4", "NO3")


def _normal(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if hasattr(value, "tolist"):
        return _normal(value.tolist())
    if isinstance(value, (list, tuple)):
        return [_normal(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normal(item) for key, item in value.items()}
    if isinstance(value, (int, float)):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Non-finite value in reference output")
        return number
    if value is None or isinstance(value, (str, bool)):
        return value
    raise TypeError(f"Unsupported reference value type: {type(value).__name__}")


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def export(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    fixture_dir = Path(__file__).parent / "test_data"
    fixture_files = ("wofost81_authority_wheat.yaml", "wofost81_qualification_weather.yaml")
    inputs = {file: _digest(fixture_dir / file) for file in fixture_files}
    manifest = {
        "status": "PROVISIONAL_NOT_ADMITTED",
        "model_entrypoint": "Wofost81_NWLP_MLWB_SNOMIN",
        "pcse_version": importlib.metadata.version("pcse"),
        "input_sha256": inputs,
        "time_contract": "day labels combine post-integration states and prospective rates",
        "fields_requested": list(FIELDS),
        "cases": {},
    }
    for label, modifier in (("reference", None), ("low_mineral_n", _low_mineral_n)):
        raw = _run(modifier)
        rows = []
        for record in raw:
            selected = {"day": _normal(record["day"])}
            for field in FIELDS:
                if field in record:
                    selected[field] = _normal(record[field])
            rows.append(selected)
        assert len(rows) > 30, f"Insufficient reference rows: {label}"
        assert all(rows[i]["day"] < rows[i+1]["day"] for i in range(len(rows)-1))
        target = out / f"wofost81_wheat_{label}_provisional.json"
        target.write_text(json.dumps(rows, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        manifest["cases"][label] = {
            "rows": len(rows),
            "first_day": rows[0]["day"],
            "last_day": rows[-1]["day"],
            "sha256": _digest(target),
            "file": target.name,
            "fields_present": sorted(set().union(*(row.keys() for row in rows))),
        }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="wofost81_reference_export")
    args = parser.parse_args()
    print(json.dumps(export(args.out)["cases"], indent=2))

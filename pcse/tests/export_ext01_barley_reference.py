"""Export a reproducible *new* EXT01 barley Python crop-only research reference."""
import csv, hashlib, json, math, pathlib, subprocess
from pcse.tests.test_wofost81_ext01_new_barley import new_barley_case

ROOT=pathlib.Path(__file__).resolve().parents[2]
FILES={
 "barley_parameters":"pcse/tests/test_data/ext01_barley_wofost81_source.yaml",
 "weather":"pcse/tests/test_data/wofost81_qualification_weather.yaml",
 "experiment":"pcse/tests/test_wofost81_ext01_new_barley.py",
 "external_provider":"pcse/tests/test_wofost81_external_soil_off.py",
 "configuration":"pcse/tests/data_wofost81_external_soil_off.conf"}
COLUMNS=("day","DVS","LAI","TAGP","TRA","NuptakeTotal")

def digest(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def export(folder):
    folder=pathlib.Path(folder); folder.mkdir(parents=True,exist_ok=True)
    records,model=new_barley_case()
    rows=[]
    for r in records:
        row={}
        for k in COLUMNS:
            v=r.get(k)
            if hasattr(v,"isoformat"): v=v.isoformat()
            if isinstance(v,(float,int)) and not math.isfinite(v):
                raise ValueError(f"invalid {k} on {r.get('day')}")
            row[k]=v
        rows.append(row)
    assert len(rows)==61
    assert any((r["TAGP"] or 0)>0 for r in rows)
    assert len({r["day"] for r in rows})==len(rows)
    csv_path=folder/"ext01_barley_python_crop_only.csv"
    with csv_path.open("w",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS,lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)
    manifest={
      "admission":"RESEARCH_ONLY_NOT_SCIENTIFICALLY_ADMITTED",
      "reference_type":"NEW_EXT01_BARLEY_NOT_PP01_PP02",
      "model":"PCSE Wofost81 with test external ET and no soil water",
      "fortran_comparison":"NOT_YET_RUN",
      "crop":"Spring_barley_301",
      "upstream_parameter_blob":"0a850879538bd43fe7bf2973d6238ae672d49bdb",
      "PCSE_crop_soil_n_policy":"N_PotentialProduction (no dynamic soil N)",
      "external_flux_cm_per_day":{"TRA":0.15,"TRAMX":0.30,"RFTRA":0.5,"EVS":0.0},
      "caveat":"Synthetic fixed ET, not matching SWAP accepted weather or hydrological flux; no complete PCSE snapshot.",
      "sources_sha256":{k:digest(ROOT/v) for k,v in FILES.items()},
      "output_sha256":digest(csv_path),
      "rows":len(rows),"first_day":rows[0]["day"],"last_day":rows[-1]["day"],"columns":list(COLUMNS),
      "source_commit":subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    }
    (folder/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest

if __name__=="__main__":
    import sys
    print(json.dumps(export(sys.argv[1]),indent=2))

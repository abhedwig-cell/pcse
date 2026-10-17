"""F-WOF-EXT01, immutable new barley Python -> Fortran research input package.

Exports the FULL parameter values, original daily weather and exactly the
PCSE astronomy attributes needed by the already-existing SWAP5 WOFOST81
one-day Fortran kernel. This is a mapping/extraction contract, not a matched
Fortran WOFOST scientific PASS.  Never infer a crop checkpoint from CSV outputs.
"""
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path

import yaml
from pcse.util import astro
from pcse.tests.test_wofost81_snomin_e2e import _weather

START=dt.date(2010,4,16)
DAYS=60
FIELDS=("day","TMIN","TMAX","TEMP","IRRAD_J_M2_D",
        "ET0_CM_D","DAYL_H","DAYLP_H","SINLD","COSLD",
        "DIFPP_J_M2_S","DSINBE_S","RFTRA_EXTERNAL",
        "TRA_EXTERNAL_CM_D","TRAMX_EXTERNAL_CM_D")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract(out):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    root=Path(__file__).parent
    params_file=root/"test_data"/"ext01_barley_wofost81_source.yaml"
    weather_file=root/"test_data"/"wofost81_qualification_weather.yaml"
    source=yaml.safe_load(params_file.read_text())
    variety=source["CropParameters"]["Varieties"]["Spring_barley_301"]
    crop={key:value[0] for key,value in variety.items() if key!="Metadata"}
    crop_file=out/"crop_parameter_values.json"
    crop_file.write_text(json.dumps(crop,sort_keys=True,indent=2)+"\n")
    provider=_weather()
    lines=[]
    for i in range(DAYS+1):
        day=START+dt.timedelta(days=i)
        w=provider(day)
        sun=astro(day,w.LAT,w.IRRAD)
        row={"day":day.isoformat(),
             "TMIN":float(w.TMIN),"TMAX":float(w.TMAX),
             "TEMP":float(w.TEMP),"IRRAD_J_M2_D":float(w.IRRAD),
             "ET0_CM_D":float(w.ET0),
             "DAYL_H":sun.DAYL,"DAYLP_H":sun.DAYLP,
             "SINLD":sun.SINLD,"COSLD":sun.COSLD,
             "DIFPP_J_M2_S":sun.DIFPP,"DSINBE_S":sun.DSINBE,
             "RFTRA_EXTERNAL":0.5,"TRA_EXTERNAL_CM_D":0.15,
             "TRAMX_EXTERNAL_CM_D":0.30}
        assert all(math.isfinite(v) for k,v in row.items() if k!="day")
        lines.append(row)
    forcing=out/"pcse_daily_fortran_boundary.csv"
    with forcing.open("w",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS,lineterminator="\n")
        writer.writeheader();writer.writerows(lines)
    manifest={
       "status":"RESEARCH_ONLY_NO_MATCHED_FORTRAN_PASS",
       "source":"PCSE repair research branch, WOFOST81 Spring_barley_301",
       "original_parameter_blob":"0a850879538bd43fe7bf2973d6238ae672d49bdb",
       "raw_parameters_sha256":sha(params_file),
       "raw_weather_sha256":sha(weather_file),
       "crop_parameter_json_sha256":sha(crop_file),
       "daily_fortran_boundary_sha256":sha(forcing),
       "dates":[lines[0]["day"],lines[-1]["day"]],
       "rows":len(lines),
       "semantics":"PCSE weather and PCSE astro(day, LAT, IRRAD), before crop-day phase alignment",
       "forcing_scope":"The 61 dated rows include the initialization/output date and 60 transitions; native Fortran transition indexing must be independently verified.",
       "uncalculated_fields":["TMINRA rolling history","CO2 efficiency and AMAX scaling","N soil request/supply","initial full leaf cohorts","PCSE state-to-Fortran parity"],
       "units":"PCSE native weather IRRAD J/m2/day; ET0 cm/day; astro DIFPP J/m2/s; SWAP5 native-integral conversion not yet validated",
       "external_ET":{"TRA_cm_day":0.15,"TRAMX_cm_day":0.30,"RFTRA":0.5},
       "scientific_nonclaim":"Not historical PP01, not a completed Fortran matched-case comparison"}
    (out/"manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest


if __name__=="__main__":
    import sys
    print(json.dumps(extract(sys.argv[1]),sort_keys=True))

"""Bounded input adapter for SWAP5's authentic Jan 1999 weather sequence.

This is not a WeatherDataProvider: SWAP's five reported source fields do not
yet establish all PCSE atmospheric drivers or consistent ET conversions.
"""
from datetime import date, timedelta
import math

SCHEMA="F-WOF-EXT01/SWAP-1999-WEATHER-SEQUENCE/1"
FIELDS={"date","tmin_c","tmax_c","rain_native","etref_native","radiation_j_m2_day"}

def require_native_sequence(envelope):
    if envelope.get("schema")!=SCHEMA:
        raise ValueError("unknown native weather sequence schema")
    if (not isinstance(envelope.get("independent_repetitions"),int) or\n            isinstance(envelope.get("independent_repetitions"),bool) or\n            envelope["independent_repetitions"]<2):
        raise ValueError("independent physical repeated source proof missing")
    if envelope.get("unit_conversion_to_pcse_qualified") is not False:
        raise ValueError("unqualified conversion asserted")
    if envelope.get("crop_initial_state_matched") is not False or envelope.get("physical_crop_coupling_admitted") is not False:
        raise ValueError("unsupported crop science admission asserted")
    rows=envelope.get("records")
    if not isinstance(rows,list) or len(rows)!=7:
        raise ValueError("seven complete historical source days required")
    result=[]
    for offset,row in enumerate(rows):
        if not isinstance(row,dict) or set(row)!=FIELDS:
            raise ValueError("incomplete native meteorology")
        d=(date(1999,1,20)+timedelta(days=offset)).isoformat()
        if row["date"]!=d: raise ValueError("nonconsecutive historical date")
        values=[row[k] for k in FIELDS if k!="date"]
        if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in values):
            raise ValueError("invalid source weather value")
        if row["tmin_c"]>row["tmax_c"] or row["rain_native"]<0 or row["radiation_j_m2_day"]<0:
            raise ValueError("inconsistent native atmospheric forcing")
        result.append(dict(row))
    return result

def pcse_weather_provider_from_native(envelope):
    require_native_sequence(envelope)
    # SWAP source fields do not independently establish PCSE VAP, WIND,
    # E0/ES0/ET0, location/elevation, or full aerodynamic assumptions.
    raise ValueError("PCSE atmospheric forcing and conversions not scientifically established")

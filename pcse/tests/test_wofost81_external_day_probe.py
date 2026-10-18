"""F-WOF-EXT01 follow-on: *actual* PCSE one-day process boundary smoke.

This tests a fresh PCSE WOFOST81 crop/soil Engine for exactly one model day.
No claim of SWAP hydrology forcing, crop-only state rollback, or full PCSE restart.
"""
import hashlib
import json
import subprocess
import sys
import unittest

from pcse.base import ParameterProvider
from pcse.models import Wofost81_NWLP_MLWB_SNOMIN
from pcse.tests.test_wofost81_snomin_e2e import _crop_parameters, _soil_and_site, _weather, _agro


WORKER = """
import json,sys
from pcse.base import ParameterProvider
from pcse.models import Wofost81_NWLP_MLWB_SNOMIN
from pcse.tests.test_wofost81_snomin_e2e import _crop_parameters,_soil_and_site,_weather,_agro
request=json.load(sys.stdin)
assert request['schema']=='WOFO81-EXT01-ONE-DAY/1'
soil,site=_soil_and_site()
m=Wofost81_NWLP_MLWB_SNOMIN(ParameterProvider(cropdata=_crop_parameters(),soildata=soil,sitedata=site),_weather(),_agro())
m.run(days=1)
rows=m.get_output()
def scalar(v):
    if hasattr(v,'isoformat'): return v.isoformat()
    return float(v) if v is not None else None
out={'schema':request['schema'],'event':request['event'],
     'rows':[{k:scalar(r.get(k)) for k in ('DVS','LAI','TAGP','NuptakeTotal')} | {'day':scalar(r['day'])} for r in rows]}
sys.stdout.write('EXTERNAL_DAY_JSON:'+json.dumps(out,allow_nan=False)+'\\n')
"""


def model_once():
    soil, site = _soil_and_site()
    m = Wofost81_NWLP_MLWB_SNOMIN(
        ParameterProvider(cropdata=_crop_parameters(), soildata=soil, sitedata=site),
        _weather(), _agro())
    m.run(days=1)
    return m.get_output()


class RealPCSEBoundary(unittest.TestCase):
    def test_one_day_worker_matches_inprocess_and_does_not_touch_parent(self):
        event = "day-1"
        input_bytes = json.dumps({"schema":"WOFO81-EXT01-ONE-DAY/1","event":event}).encode()
        outputs = []
        for unused in range(2):
            p = subprocess.run([sys.executable, "-c", WORKER], input=input_bytes,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            response = json.loads(p.stdout.decode().split('EXTERNAL_DAY_JSON:')[-1].strip())
            self.assertEqual(response['event'], event)
            outputs.append(response)
        self.assertEqual(outputs[0], outputs[1])
        local = model_once()
        self.assertEqual(len(outputs[0]['rows']), len(local))
        for expected, observed in zip(local, outputs[0]['rows']):
            self.assertEqual(expected['day'].isoformat(), observed['day'])
            for key in ('DVS','LAI','TAGP','NuptakeTotal'):
                lhs = expected.get(key)
                self.assertEqual(float(lhs) if lhs is not None else None, observed[key])
        print('REAL_PCSE_ONE_DAY_MATCH',len(local),hashlib.sha256(
            json.dumps(outputs[0],sort_keys=True).encode()).hexdigest())


if __name__ == '__main__':
    unittest.main()

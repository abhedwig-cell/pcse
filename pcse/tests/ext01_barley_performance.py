"""Research-only EXT01 measured startup/throughput probe.

This is NOT a SWAP5 integrated performance claim. Measures PCSE process
and repeated isolated barley simulations, logging real measured timings.
"""
import json, os, resource, subprocess, sys, time

def run_repetitions(n):
    from pcse.tests.test_wofost81_ext01_new_barley import new_barley_case
    started=time.perf_counter()
    cases=[]
    for k in range(n):
        t=time.perf_counter()
        rows,_=new_barley_case()
        cases.append(dict(rows=len(rows),seconds=time.perf_counter()-t))
    return dict(instances=n, total_seconds=time.perf_counter()-started,
                cases=cases, peak_rss_kb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

if __name__=="__main__":
    if len(sys.argv)==2 and sys.argv[1]=="worker":
        print("EXT01_PERFORMANCE="+json.dumps(run_repetitions(3),sort_keys=True))
    else:
        started=time.perf_counter()
        p=subprocess.run([sys.executable,"-m","pcse.tests.ext01_barley_performance","worker"],
                         text=True,capture_output=True,check=True)
        payload=p.stdout.split("EXT01_PERFORMANCE=")[-1].strip()
        result=json.loads(payload)
        result["cold_worker_wall_seconds"]=time.perf_counter()-started
        result["method"]="single isolated Python process, sequential 3 crop instances"
        result["notes"]="No SWAP5 Fortran overhead or throughput scaling measured; run once per CI job"
        print("EXT01_MEASURED_PERFORMANCE="+json.dumps(result,sort_keys=True))

"""F-WOF-EXT01 real-engine direct restore dependency inventory.

Runs real PCSE engines; detects continuation dependencies without editing production.
This is not a state codec or a claim of restart success.
"""
import json
import unittest
from pcse.tests.test_wofost81_ext01_process_restart import build_engine

COMPONENTS=("pheno","part","assim","mres","evtra","lv_dynamics",
            "st_dynamics","ro_dynamics","so_dynamics","n_crop_dynamics","n_stress")

def inventory(engine):
    crop=engine.crop
    result={"day":engine.day.isoformat(), "timer":{
        "date":engine.timer.current_date.isoformat(),
        "counter":engine.timer.day_counter, "first_call":engine.timer.first_call},
        "saved_rows":len(engine.get_output()),"components":{}}
    for name in COMPONENTS:
        component=getattr(crop,name,None)
        if component is None:
            result["components"][name]={"present":False}
            continue
        state=getattr(component,"states",None)
        rates=getattr(component,"rates",None)
        result["components"][name]={
            "present":True,"has_states":state is not None,
            "has_rates":rates is not None,
            "state_traits":sorted(k for k in state.traits().keys() if not k.startswith("_")) if state is not None else [],
            "rate_traits":sorted(k for k in rates.traits().keys() if not k.startswith("_")) if rates is not None else []}
    return result

class RealEngineRestartInventory(unittest.TestCase):
    def test_inventories_are_reproducible_and_continuation_surface_is_nontrivial(self):
        for day in (10,30,45):
            first=build_engine()
            second=build_engine()
            first.run(days=day)
            second.run(days=day)
            a,b=inventory(first),inventory(second)
            self.assertEqual(a,b)
            self.assertEqual(a["timer"]["counter"],day)
            self.assertEqual(a["saved_rows"],day+1)
            self.assertTrue(a["components"]["lv_dynamics"]["has_states"])
            self.assertTrue(a["components"]["pheno"]["has_states"])
            self.assertGreater(sum(v.get("has_states",False) for v in a["components"].values()),4)
            print("EXT01_DIRECT_RESTART_INVENTORY",json.dumps({
                "day":day, "components":a["components"],"timer":a["timer"],
                "saved_rows":a["saved_rows"]},sort_keys=True))
    def test_new_engine_is_not_a_day30_checkpoint(self):
        advanced=build_engine()
        advanced.run(days=30)
        fresh=build_engine()
        self.assertNotEqual(advanced.day,fresh.day)
        self.assertNotEqual(advanced.timer.day_counter,fresh.timer.day_counter)
        self.assertNotEqual(len(advanced.get_output()),len(fresh.get_output()))
        print("EXT01_DIRECT_ENGINE_RESTORE_NOT_IMPLEMENTED")
if __name__=="__main__":
    unittest.main()

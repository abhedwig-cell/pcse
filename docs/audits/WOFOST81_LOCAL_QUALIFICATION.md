# Integrated local qualification, 2026-10-05

Branch: `audit/wofost81-deep-logic`.
Starting HEAD: `044f35788137f39a60e4d2533ace4fc56c2d6cbc` (clean checkout).
Qualified comparison base: `88e59ec0e17e879c3adbec6f7667ab332b5c2908`.
Runtime: Python 3.12.14, traitlets-pcse 5.0.0.dev0, NumPy 2.3.5.
Dependencies installed using `python -m pip install --no-build-isolation -e .`.
No GitHub Actions run was used.

## Repair-diff audit and additional fixes

All seven changed Python modules were compiled and imported. Reviewed imports,
public signatures, parameter validation before component construction, kiosk
registration/publication, rate-day buffer consumption and crop deletion timing.
No public method signature was changed.

Two concrete faults were repaired:

1. CONFIG-ET01 introduced `exc.PCSEError` without importing `exceptions as exc`.
   Invalid IAIRDU/IOX therefore raised NameError. Added the import and runtime
   rejection tests for both switches, using a real integrated model fixture.
2. LOGIC-ROT02 was ineffective because upstream MLWB assigned `_RDold =
   _default_RD`, sharing a Traitlets descriptor. Updating `_RDold` also changed
   the supposedly fixed fallow depth (50.8 cm at the test harvest). Gave the
   production layered water balance an independent `_RDold` Float descriptor.
   The integrated harvest/fallow test now returns to 10 cm, rebuilds summary
   weights and completes with water/N balance checks. This is a prerequisite
   repair of an inherited ownership defect, not a change to rooting policy.

New runtime tests cover crop-domain rejection, layered ET switches, actual
SNOMIN amendment buffer additions and mutation-free invalid-event rejection,
one-rate-day irrigation consumption, senescence-limited N translocation with
complete stem senescence, harvest/fallow geometry reset and active biomass
reallocation throughout a full model lifecycle. Exact first-observation state
events are checked for rising, falling and either directions, including no
repeat on a stationary threshold. Existing multi-threshold jump tests remain.

## Exact commands

Compile/import smoke:

```sh
python - <<'PYCODE'
import subprocess, importlib, py_compile
files = subprocess.check_output([
    'git', 'diff', '--name-only',
    '88e59ec0e17e879c3adbec6f7667ab332b5c2908', '--', '*.py'
], text=True).splitlines()
for path in files:
    py_compile.compile(path, doraise=True)
    importlib.import_module(path[:-3].replace('/', '.'))
    print('COMPILE_IMPORT_PASS', path)
PYCODE
```

Deep logic:

```sh
PYTHONWARNINGS=ignore python -m unittest -v pcse.tests.test_wofost81_deep_logic
```

Scientific/component/E2E:

```sh
PYTHONWARNINGS=ignore python -m unittest -v pcse.tests.test_snomin_scientific pcse.tests.test_wofost81_reallocation_scientific pcse.tests.test_wofost81_snomin_e2e pcse.tests.test_partitioning pcse.tests.test_respiration
```

Canonical legacy regression:

```sh
PYTHONWARNINGS=ignore python - <<'PYCODE'
import unittest
from pcse.tests.test_wofost72 import suite
r = unittest.TextTestRunner(verbosity=2).run(suite())
raise SystemExit(not r.wasSuccessful())
PYCODE
```

Repository-supported component/regression suite:

```sh
PYTHONWARNINGS=ignore python - <<'PYCODE'
import unittest
from pcse.tests import make_test_suite
r = unittest.TextTestRunner(verbosity=2).run(make_test_suite())
raise SystemExit(not r.wasSuccessful())
PYCODE
```

Broad YAML probe, run both in this checkout and the base worktree:

```sh
git worktree add --detach ../pcse-qualified-base 88e59ec0e17e879c3adbec6f7667ab332b5c2908
PYTHONWARNINGS=ignore python -m tests --full
```

The historical `python -m tests` entrypoint does not propagate test failure into
its process exit code. Qualification uses the unittest result, not that exit
code. No generic unittest discovery or abstract/template instantiation was used.

## Qualification boundary

Local qualification establishes executable repair invariants and the tested
regression envelope. It does not quantify field-scale repair effects or resolve
model-owner formulation choices. Synthetic soil and forcing fixtures remain
qualification fixtures, not calibration evidence. Existing ResourceWarnings and
Traitlets deprecation warnings were observed and left outside this repair set.

## Final results

| Check | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Changed-module compile/import | 7 | 0 | 0 | 0 |
| Deep logic, including integrated runtime oracles | 17 | 0 | 0 | 0 |
| Earlier scientific/component/E2E suite | 19 | 0 | 0 | 0 |
| Canonical legacy WOFOST72 suite() | 12 | 0 | 0 | 0 |
| Repository make_test_suite() | 30 | 0 | 0 | 0 |
| Full YAML suite, integrated branch | 392 | 64 | 0 | 0 |
| Full YAML suite, qualified base | 392 | 64 | 0 | 0 |

Counts are per invocation; suites overlap and must not be summed as unique tests.

The 64 broad-suite failures match the qualified base **exactly by YAML filename
and complete assertion text**: 44 assimilation PGASS reference mismatches and
20 LINGRA-NWLP NAVAIL reference mismatches. For example, assimilation case 01
reports PGASS 0.117225 != 0.000000 on 2010-04-30; the final LINGRA case reports
NAVAIL 7.573590 != 7.323590 on 1986-02-11. The production components and fixture
files responsible are unchanged by the repair diff. These are inherited
reference-envelope failures, not regressions introduced here. Their deeper
historical cause is outside this repair qualification and is not inferred from
matching failures alone. No reference results were regenerated or relaxed.

Exact failure/assertion records, durations and stdout hashes are persisted in
[WOFOST81_LOCAL_QUALIFICATION_RESULTS.json](WOFOST81_LOCAL_QUALIFICATION_RESULTS.json).

Admission judgement: **ADMISSION_READY_LOCAL_SCOPED**. Every repair-relevant
suite and the canonical supported regression suite is green, with no new
broad-suite failures. This is deliberately not a claim that the entire raw
repository test set is green. Maintainer admission and unresolved scientific
policy decisions remain separate. No final Actions run is necessary for this
local qualification; Git contains the reproducible commands and evidence.

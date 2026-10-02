# WOFOST 8.1 Scientific Code Review — Audit Closeout

## Scope and authority

This review evaluates scientific implementation correctness in PCSE/WOFOST 8.1,
with emphasis on equation-to-code consistency, conservation, positivity,
causality and cross-component ownership.

Code authority is pinned to upstream:
`ajwdewit/pcse@67a28e56b0e34655f8d60b0b4a254a7c81efbb2f`.

Crop parameters used for the audit E2E fixture are pinned separately to:
`ajwdewit/WOFOST_crop_parameters@31b217f3958a7ff48ea875368385ebe2218f3dd4`,
`wheat.yaml:Winter_wheat_102`.

The synthetic soil used in the E2E fixture is a qualification test stand, not a
calibrated or representative Dutch soil. No field-scale impact claim is made.

## Executive findings

The classical WOFOST crop-production core was not found to contain a comparable
mass/causality defect in the audited assimilation, respiration and basic
partitioning paths. The highest-confidence defects are concentrated in newer
WOFOST 8.1 / SNOMIN / reallocation interactions.

### Confirmed scientific implementation defects

**WOFOST81-SNOMIN-01 — NH4 immobilisation limiter**

The baseline finite-pool limiter has reversed algebra. Under NH4-limited net
immobilisation it can turn required immobilisation into mineralisation. The
repair derives the limiting rate directly from the NH4 state equation. It is
component-qualified, full-lifecycle smoke-tested and has a causal E2E effect.

An intentionally extreme low-mineral-N/high-C:N fixture produced:

- baseline TAGP: 3970.471846 kg/ha
- repaired TAGP: 1125.003215 kg/ha
- baseline NuptakeTotal: 22.351471 kg N/ha
- repaired NuptakeTotal: 0.363096 kg N/ha

These values demonstrate causal amplification when the defective branch is
active. They are explicitly **not** estimates of bias in normal field use.
Real-world prevalence and impact are left to domain/calibration assessment.

**WOFOST81-SNOMIN-04 — finite-pool inorganic-N transport**

Baseline advective NH4/NO3 export can exceed the finite donor pool for large
daily water flux relative to layer water storage. The repair donor-limits
transport and recomputes internal receiving-layer import from the committed
limited donor flux, preserving profile mass.

**WOFOST81-REALLOC-01 — non-transactional biomass reallocation**

Baseline reallocation requests are based on a fixed quota but are not limited
against living donor biomass remaining after same-day senescence. Consequences
include possible negative stem biomass and a leaf equality case where donor
removal can be skipped while storage-organ credit is still requested.

The repair makes reallocation transactional:
1. calculate requested quota transfer;
2. calculate same-day donor death;
3. limit transfer to surviving living donor biomass;
4. credit storage organs only from the committed transfer.

**WOFOST81-NBAL-01 — crop-N balance-check timing**

The crop-N balance was checked during rate calculation before the same day's
state transition was integrated. The check has been moved after integration so
it verifies the transition it is intended to guard.

## Confirmed contracts and discrepancies

**WOFOST81-TIME-01 — one-day transition contract**

WOFOST 8.1 is not a generic variable-step integrator. Multiple phenology,
vernalisation, leaf, root, stem and storage-organ state updates use daily rates
without multiplication by `delt`, while selected top-level cumulative states
do multiply by `delt`. Non-unit `delt` is therefore internally inconsistent.
The scientific production contract is a one-day transition.

**WOFOST81-PART-01 — documentation/code discrepancy**

`DVS_Partitioning_N` states that N stress modifies partitioning. The actual
implementation modifies root allocation using `RFTRA`, i.e. water/oxygen
stress, and uses no N-stress variable in this partitioning calculation.
This review does not choose which formulation is scientifically intended.

**WOFOST81-ROOT-01 — spatial root-activity assumption**

Layered water uptake and SNOMIN N uptake do not share one explicit spatial
root-activity model. This is retained as a structural assumption requiring
sensitivity interpretation, not classified as an implementation defect.

**WOFOST81-SNOMIN-03 — daily operator ordering**

Crop uptake, soil reactions and transport are serialised within the daily
transition. Competition is therefore partly operator-order dependent. This is
a structural numerical assumption.

**WOFOST81-NBAL-02 — production balance tolerance**

The aggregate crop-N balance check uses a relatively broad absolute threshold
(1 kg N/ha). The scientific qualification suite therefore uses tighter
process-level invariants rather than treating the production checksum as
sufficient evidence of correctness.

## Test architecture findings

A legacy assimilation unit fixture does not provide `TMIN` although current
WOFOST81 assimilation requires it. This is retained as a documented stale-test
finding.

The legacy full-WOFOST regression retriever used pandas positional access via
`Series[0]`, which is incompatible with current pandas label semantics. The
test harness was repaired with `.iloc[0]`, and the regression envelope invokes
the module's canonical `suite()` rather than generic unittest discovery.

## Qualification evidence

Final green qualification evidence includes:

- 19 WOFOST81 scientific/component/E2E tests;
- complete Wofost81_NWLP_MLWB_SNOMIN lifecycle fixture;
- non-negative mineral-N E2E invariant;
- explicit activation of the SNOMIN-01 limiter;
- baseline-versus-repair causal T12 comparison;
- transactional biomass-reallocation invariants;
- 12 canonical legacy full-WOFOST regression simulations.

Persisted run: GitHub Actions run `36983335139`.

## Scientific interpretation

The audit does not support a conclusion that WOFOST 8.1 as a whole is
scientifically unreliable. The older crop-production core appears substantially
more mature than the newer coupled N/reallocation paths inspected here.

The strongest general lesson is that aggregate mass-balance closure is
necessary but not sufficient. A wrong flux can remain balance-closing when a
coupled bookkeeping term is adjusted consistently. Qualification therefore
needs conservation **and** causal/process invariants.

## Deliberately unresolved

The audit does not estimate how often SNOMIN-01, SNOMIN-04 or REALLOC-01 are
activated under operational European/Dutch applications. It also does not
recalibrate WOFOST or change scientific parameterisations to reduce the
observed synthetic impacts. Those are domain/model-development decisions.

Likewise, no change is made to PART-01 until the intended scientific
partitioning formulation is resolved by the model maintainers.

## Recommendation for upstream discussion

Treat the branch as a scientific review/repair candidate, not an automatic
upstream patch set. For each proposed production repair, upstream maintainers
should review the intended formulation, then retain the invariant tests even
if the final implementation differs.

The most important upstream discussion items are:

1. confirm and repair the NH4 immobilisation limiter;
2. adopt a finite-pool policy for inorganic-N transport;
3. make biomass reallocation donor-limited and transactional;
4. place crop-N balance verification after the integrated transition;
5. document the one-day time-step contract explicitly;
6. resolve the N-stress versus RFTRA partitioning documentation/formulation;
7. retain an executable WOFOST81 + MLWB + SNOMIN E2E regression fixture.

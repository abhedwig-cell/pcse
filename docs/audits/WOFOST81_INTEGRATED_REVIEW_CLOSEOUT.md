# WOFOST 8.1 Scientific + Deep Logic Review — Integrated Closeout

## Review scope

The classical WOFOST carbon-production core is materially conserved and did not yield a comparable high-confidence implementation defect. Confirmed defects cluster in newer coupled extensions and at software ownership boundaries: SNOMIN, crop-N, biomass/N reallocation, management event composition, crop lifecycle metadata and parameter-domain contracts.

## A. Technical defects with a hard invariant

These do not require choosing a new scientific formulation:

- SNOMIN-01: NH4 immobilisation finite-pool limiter algebra.
- SNOMIN-04: finite-pool NH4/NO3 advective export.
- NBAL-01: crop-N balance check timing.
- REALLOC-01: donor-limited transactional biomass reallocation.
- LOGIC-CC01: explicit harvest overwritten by max_duration on equality.
- LOGIC-SE01: exact first-observation state threshold silently lost.
- LOGIC-AMEND02: same-day mineral-N amendments overwrite rather than accumulate.
- LOGIC-IRR01: same-day irrigation events overwrite rather than accumulate.
- LOGIC-NTRANS01: senescence and N translocation double-claim donor N.
- LOGIC-ROT02: finished-crop root geometry persists into fallow summaries.
- CONFIG-REALLOC01/N01/ET01/SN01: missing validation of hard physical/switch domains.

These are suitable as technical repair candidates, with local qualification completed and maintainer review of implementation details remaining.

## B. Model-owner decisions

These should not be silently repaired:

- PART-01 / XVER-PART01: DVS_Partitioning_N documentation says N stress/NPART/NNI; executable code instead changes root allocation using RFTRA and caps FR at 0.6.
- TIME-01 / XVER-TIME01: WOFOST81 has partial delt scaling but remains fundamentally a one-day transition model.
- ROOT-01: water and N use different implicit spatial root-activity assumptions.
- SNOMIN-03 / NCOUP01 / WCOUP01: daily explicit operator/coupling order.
- ROOT02: root depth can grow while actual root DM growth is zero, documented as legacy modelling choice.
- CONFIG-ROOT01: policy when RDI exceeds nominal crop/soil rooting maxima.

## C. Interpretation/documentation contracts

- Daily output rows mix post-integration states with prospective rates for the next transition.
- Finish-date rates can be calculated and exposed although no later crop integration realizes them.
- Event calendar dates label rate-day availability; state incorporation occurs at the next integration boundary.
- Crop start and crop finish are therefore temporally asymmetric.

These should be documented clearly even if code remains unchanged.

## D. Reviewed areas where no additional defect was established

- PGASS→RFTRA→GASS→MRES→ASRC→CVF→DMI core.
- Carbon balance formulation.
- Root-layer crossing consistency between MLWB and SNOMIN.
- Rainfall + irrigation composition after irrigation repair.
- VariableKiosk flushing/deregistration against generic stale published values.
- Reallocation cache lifetime across deleted/recreated crop objects.
- Surface-water/infiltration transaction after composition repairs.
- Multi-threshold state-event jumps.

## E. Evidence boundary

The earlier scientific branch has persisted green evidence for 19 scientific/component/E2E tests plus 12 canonical legacy WOFOST full-model regressions. The integrated repair set has now been executed locally on Python 3.12.14, including expanded runtime oracles. Exact commands, results, repair-diff checks and inherited broad-suite failures are recorded in [WOFOST81_LOCAL_QUALIFICATION.md](WOFOST81_LOCAL_QUALIFICATION.md) and WOFOST81_FINDINGS.json. No new GitHub Actions run was used. This qualification does not close field-effect estimation or model-owner decisions.

## F. Recommended upstream sequence

1. Ask the WOFOST model owner to resolve PART-01 and confirm the intended one-day time contract.
2. Review the completed local scientific + deep-logic qualification and the explicit inherited test exceptions.
3. Split hard-invariant repairs into small reviewable commits/PRs by ownership domain: SNOMIN, crop-N/reallocation, AgroManager/Engine, MLWB, validation.
4. Keep interpretation-only findings out of behavioural patches; document them separately.
5. A final persisted CI run remains optional; this session persisted local evidence in Git without using Actions.

## Review judgement

The review does not support a claim that WOFOST 8.1 is broadly unreliable. It does support a narrower conclusion: newer coupled processes and orchestration boundaries have materially weaker executable contracts and test coverage than the classical crop carbon core. Mass balance alone is insufficient; transaction ownership, event composition and temporal semantics need explicit invariants.

## Local admission status, 2026-10-05

**ADMISSION_READY_LOCAL_SCOPED** at repair-code commit `4937363`.
Seven changed modules compile/import; 17 deep-logic tests, 19 scientific tests,
12 canonical legacy regressions and the 30-test supported repository suite pass.
The full YAML probe yields 392 passed / 64 failed on both integrated and qualified
base checkouts, with identical failure names and assertion values. No new
regression was introduced. The entire raw repository suite is therefore not
claimed green; inherited assimilation/LINGRA reference failures remain explicit.

Qualification repaired CONFIG-ET01's missing exception import and the inherited
MLWB shared `_RDold`/`_default_RD` Traitlets descriptor that blocked the fallow
reset. All hard-invariant repairs listed in section A now have local QUALIFIED
evidence. REALLOC-01 additionally has an activated synthetic lifecycle test.
PART-01, dt=1-day architecture, spatial root activity, daily coupling order and
RDI/RDMCR/RDMSOL policy remain untouched for Allard/model-owner review.

See the local commands/evidence documents for complete results and limitations.
No Actions run was used, and no upstream admission or merge is claimed.

# WOFOST 8.1 Scientific + Deep Logic Review — Integrated Closeout

## Bottom line

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

These are suitable as technical repair candidates, subject to final local regression/qualification and maintainer review of implementation details.

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

The earlier scientific branch has persisted green evidence for 19 scientific/component/E2E tests plus 12 canonical legacy WOFOST full-model regressions. The later deep-logic repairs were intentionally not pushed through repeated GitHub Actions because CI queue usage was explicitly minimized. Their status must therefore remain 'repair implemented / local or final qualification pending' unless separately executed.

## F. Recommended upstream sequence

1. Ask the WOFOST model owner to resolve PART-01 and confirm the intended one-day time contract.
2. Locally run the complete scientific + deep-logic suite against the integrated branch.
3. Split hard-invariant repairs into small reviewable commits/PRs by ownership domain: SNOMIN, crop-N/reallocation, AgroManager/Engine, MLWB, validation.
4. Keep interpretation-only findings out of behavioural patches; document them separately.
5. Use one final persisted CI run only after the repair set is stable.

## Review judgement

The review does not support a claim that WOFOST 8.1 is broadly unreliable. It does support a narrower conclusion: newer coupled processes and orchestration boundaries have materially weaker executable contracts and test coverage than the classical crop carbon core. Mass balance alone is insufficient; transaction ownership, event composition and temporal semantics need explicit invariants.

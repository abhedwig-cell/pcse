# WOFOST 8.1 — Model-owner review brief

## Decisions requested

### 1. Assimilate partitioning
`DVS_Partitioning_N` is named/documented as N-stress partitioning using NPART/NNI, but executable WOFOST81 code modifies root allocation with RFTRA (water/oxygen stress), with FR capped at 0.6. Which formulation is intended for WOFOST 8.1?

### 2. Time-step contract
WOFOST81 partially introduced `delt` scaling at top-level cumulatives, while phenology and multiple organ integrations remain daily increments. Should WOFOST81 be explicitly specified as dt=1 day only, or is variable-step support intended?

### 3. Root activity
Water and mineral-N uptake do not use one common explicit spatial root-activity distribution. Is this intentional and documented, or should they be harmonised?

### 4. Daily coupling order
Crop water/N demand is calculated before the corresponding current-day soil response; soil transformations cannot revise same-rate-day crop demand. Is this explicit daily coupling the intended scientific contract?

### 5. Root-depth parameter inconsistency
If RDI exceeds min(RDMCR,RDMSOL), current root dynamics lets RDI determine rdmax. Should inconsistent input hard-fail instead?

## Technical defects not requiring a formulation decision

The audit separately identified hard-invariant defects in SNOMIN finite-pool handling, biomass/N donor ownership, same-day management-event accumulation, crop-finish collision logic, state-event equality, fallow root-zone metadata and parameter-domain validation. Candidate repairs and falsification tests are on the audit branch.

## Branch
`audit/wofost81-deep-logic`

Integrated review: `docs/audits/WOFOST81_INTEGRATED_REVIEW_CLOSEOUT.md`

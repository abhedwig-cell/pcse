# WOFOST 8.1 Scientific Qualification

Authority baseline: `ajwdewit/pcse@67a28e56b0e34655f8d60b0b4a254a7c81efbb2f`

Fork baseline: `abhedwig-cell/pcse@67a28e56b0e34655f8d60b0b4a254a7c81efbb2f`

## Purpose

Qualify WOFOST 8.1 by testing scientific process invariants in addition to regression against reference output. Distinguish published model equations, current implementation, numerical assumptions, and implementation defects.

## Finding classes

- CONFIRMED_DEFECT: code contradicts its governing balance/equation.
- THEORY_CODE_DISCREPANCY: implementation and stated model description differ.
- STRUCTURAL_ASSUMPTION: deliberate or intrinsic numerical/model choice requiring qualification.
- MODEL_LIMIT: documented simplification or omitted process.
- QUALIFIED: tested behavior consistent with the intended model.

## Initial findings

### WOFOST81-SNOMIN-01 — NH4 immobilisation limiter
Status: CONFIRMED_DEFECT
Confidence: very high

When net immobilisation would make the post-reaction NH4 pool negative, the limiter must enforce:

`NH4PRE + (RNH4MIN - RNH4NITR) * delt = 0`

therefore:

`RNH4MIN = RNH4NITR - NH4PRE / delt`

The baseline implementation instead assigns:

`RNH4MIN = NH4PRE - RNH4NITR`

for its hard-coded one-day rate step. This reverses the sign in the limiting regime and can turn required immobilisation into mineralisation.

Repair admission requires a failing-before/passing-after unit test, non-negative NH4, exact limiting equality, organic-N consistency, and preserved global N closure.

### WOFOST81-TIME-01 — daily-step contract
Status: STRUCTURAL_ASSUMPTION

WOFOST 8.1 must currently be treated as a discrete daily model. Multiple rate calculations hard-code `delt = 1.0` and several organ integration routines accept `delt` but update daily rates without multiplying by it. Sub-daily use is therefore not qualified by the API signature alone.

### WOFOST81-PART-01 — partitioning documentation
Status: THEORY_CODE_DISCREPANCY

`DVS_Partitioning_N` documents N-stress effects on partitioning, while the current modifier acts through `RFTRA` (water/oxygen stress). No implementation defect is asserted until the intended WOFOST 8.1 formulation is resolved.

### WOFOST81-ROOT-01 — water/N root activity
Status: STRUCTURAL_ASSUMPTION

Layered water uptake and SNOMIN N uptake do not use one common explicit root-activity distribution. Sensitivity to layer discretisation and root crossing must be quantified.

### WOFOST81-SNOMIN-03 — daily process ordering
Status: STRUCTURAL_ASSUMPTION

Within a daily step the implementation serialises crop uptake, soil reactions, deposition/amendments and inorganic N transport. Competition between processes is therefore order-dependent and requires adversarial tests.

### WOFOST81-SNOMIN-04 — transport positivity
Status: OPEN

Test whether large daily water fluxes and thin layers can remove more NH4 or NO3 than the finite post-reaction pool.

## Qualification matrix

| ID | Experiment | Invariants / outputs |
|---|---|---|
| T01 | NH4-limited immobilisation | NH4 >= 0; limiter equality; N closure |
| T02 | Constant total mineral N, vary NH4:NO3 | uptake, NNI, TAGP, explicit source of differences |
| T03 | Homogeneous profile at 1/2/4/10 layers | convergence of TRA, N uptake, TAGP |
| T04 | Equal profile water, change vertical distribution | TRA, RFTRA, TAGP |
| T05 | Root depth immediately below/at/above layer boundary | continuity of NAVAIL, uptake, TRA |
| T06 | Equal total N, change vertical distribution | uptake, NNI, TAGP |
| T07 | Fertilisation/rain event ordering | leaching, uptake, total N loss |
| T08 | Formal 1 d versus 2 x 0.5 d | document failure of sub-daily equivalence |
| T09 | Biological N fixation sweep | crop N closure and organ allocation |
| T10 | Biomass reallocation on/off | organ DM/N ownership and harvest index |
| T11 | Equal total water+N, different vertical distributions | combined root-interface sensitivity |
| T12 | SNOMIN-01 baseline versus repaired limiter | NH4, NORG, NNI, LAI, TAGP, N loss |

## Admission rule

No repair is scientifically admitted from regression output alone. A repair must first satisfy the local process invariant that exposed the defect, then preserve mass closure, and finally demonstrate that unrelated WOFOST behavior is not changed outside the affected regime.

# WOFOST 8.1 E2E Scientific Experiments T07-T12

All experiments compare an immutable upstream baseline
`ajwdewit/pcse@67a28e56b0e34655f8d60b0b4a254a7c81efbb2f`
with the audit branch. Inputs must be identical between comparators.

## T07 — event ordering

Purpose: quantify daily operator-order sensitivity.

Paired scenarios:
1. mineral-N amendment and high infiltration on the same model day;
2. amendment one day before infiltration;
3. amendment one day after infiltration.

Hold total amendment N and total rainfall constant.

Record daily and cumulative NH4/NO3 pools, uptake, nitrification,
denitrification and leaching. Differences are characterization, not
automatically defects. Any negative pool or balance failure is a failure.

## T08 — daily-step contract

Run an isolated process fixture with one 1-day update and a formally
equivalent pair of 0.5-day updates. This test documents non-equivalence and
must not be used to claim sub-daily validity. WOFOST 8.1 remains qualified
only at the daily step unless all state/rate modules are reformulated.

## T09 — biological N fixation

Sweep NFIX_FR over zero, intermediate and high values while keeping soil N
identical. Verify crop-N closure, non-negative organ N, and that fixation
reduces soil demand rather than creating an unbooked source.

## T10 — biomass/N reallocation

Construct a crop state crossing REALLOC_DVS. Compare reallocation disabled
and enabled. Track living/dead biomass and N in leaves, stems, roots and
storage organs. Every source decrease must map to a destination increase or
an explicitly recorded loss.

## T11 — vertical root-interface sensitivity

Create profiles with equal total water and mineral N but redistribute them
between upper and lower layers. Run shallow and fully rooted cases.
Report TRA, RFTRA, NAVAIL, N uptake, NNI, LAI, TAGP and final storage-organ
biomass. This is a sensitivity experiment, not an invariance requirement.

## T12 — impact frontier for SNOMIN-01

Compare immutable baseline and repaired limiter over a factorial synthetic
frontier:
- initial NH4: low / medium / high;
- organic amendment C:N: low / medium / high;
- temperature: cool / moderate / warm;
- soil moisture: dry / field-like / wet.

Primary trigger metric: number of layer-days entering the NH4-limited
immobilisation branch.

Impact metrics: NH4, NO3, NORG, NAVAIL, crop N uptake, NNI, LAI, TAGP,
storage-organ biomass, denitrification and leaching.

Report zero-effect cases as evidence. Do not select only cases where the
repair changes yield.

## Comparison policy

1. Baseline behavior is evidence, not ground truth.
2. A process invariant outranks regression agreement when they conflict.
3. Every changed E2E result must be causally traced to an activated repaired
   code path before attribution.
4. No repair is marked QUALIFIED until component invariants pass and E2E
   regression shows no unexplained changes outside its activation regime.

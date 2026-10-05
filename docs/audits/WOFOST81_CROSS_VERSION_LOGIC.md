# WOFOST 7.2 / 7.3 / 8.1 Cross-Version Logic Audit

## Conserved core

The main crop carbon chain is materially conserved across the three implementations: potential assimilation, RFTRA reduction, maintenance respiration limited by assimilation, net assimilates, conversion factor, DMI and the carbon-balance check. No unexplained WOFOST81 logic divergence was established in this core.

The basic lifecycle pattern is also inherited: phenology is evaluated first, pre-emergence execution returns early, phenology is integrated before organ states, TAGP is recomputed from organ totals, and crop finish is finalized through the Engine signal path.

## Major WOFOST81-specific divergence: partitioning

WOFOST81 uses `DVS_Partitioning_N`. Its documentation says nitrogen stress modifies assimilate partitioning, refers to NPART and NNI, and describes increased leaf allocation. The implementation has NPART commented out, does not use NNI, and instead modifies root partitioning from RFTRA (water/oxygen stress), capped at FR=0.6.

This is substantially different from the ordinary DVS partitioning used by the standard WOFOST72/73 crop classes. The audit does not choose which formulation is scientifically intended. The discrepancy requires model-owner review because code, class name and documentation currently describe different models.

## Time-step divergence

WOFOST72/73 top-level cumulative crop states add daily rates directly. WOFOST81 multiplies several top-level cumulative rates by `delt`. However many underlying phenology and organ state updates remain daily increments without equivalent scaling. The cross-version comparison therefore supports TIME-01: WOFOST81 contains partial `delt` modernization, not a consistently variable-step model.

## WOFOST81 additions requiring separate ownership

Reallocation and explicit crop-N dynamics are genuine WOFOST81 additions and cannot be judged by requiring numerical equality with WOFOST72/73. They are instead qualified through conservation and transaction invariants. This audit has already identified and repaired donor-ownership defects in both biomass reallocation and N translocation.

## Conclusion

The older carbon-production core is strongly conserved. The highest-value cross-version concern is not widespread drift but a small number of WOFOST81-specific extensions whose executable semantics are insufficiently aligned with their documentation, especially `DVS_Partitioning_N` and partial time-step scaling.

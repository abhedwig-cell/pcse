# WOFOST81 causal conservation contracts

## Carbon / dry matter

1. Net assimilates are `GASS - MRES >= 0`.
2. New dry matter is partitioned according to the WOFOST conversion-factor
   equation and the existing carbon-balance invariant.
3. Biomass reallocation is a transfer, not new production.
4. A storage-organ reallocation credit may only be based on biomass actually
   removed from living donor organs.
5. Same-day senescence has priority over reallocation of the same donor mass.
6. Reallocation may never make a living donor pool negative.

## Crop nitrogen

1. Initial organ N + cumulative soil uptake + cumulative biological fixation
   equals current organ N + recorded N losses.
2. The balance is checked after the state transition it is intended to verify.
3. Translocation is internal: summed donor translocation equals storage-organ
   translocation.
4. Biological fixation is an external crop-N source and reduces required soil
   uptake; it must not be counted as soil removal.
5. Process-level qualification uses tighter invariants than the production
   1 kg N/ha aggregate balance tolerance.

## Soil mineral nitrogen

1. NH4/NO3 pools remain non-negative.
2. Immobilisation cannot reverse sign merely because a finite-pool limiter is
   activated.
3. Integrated advective export cannot exceed the finite donor pool.
4. Limited internal export and receiving-layer import are the same transfer.
5. Soil uptake is limited by both crop demand and accessible mineral N.

## Water to crop causality

1. Layered water extraction cannot exceed the water-balance supply.
2. Water/oxygen stress acts on assimilation through RFTRA.
3. Root-zone geometry is explicit in both water and N access, but the two
   algorithms need not imply the same root-activity profile; sensitivity is
   therefore characterized rather than assumed invariant.

## Time

All contracts above are currently production-qualified only for the model's
one-day transition. Presence of a `delt` argument does not establish
sub-daily equivalence.

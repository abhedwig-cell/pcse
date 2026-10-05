# WOFOST 8.1 Deep Logic Audit — Tranche 3/4

## Scope

This tranche combines output/finalization semantics, crop-cycle boundaries, rotation/fallow ownership, management composition, kiosk stale-value protection, root-layer timing and N donor transactions.

## Confirmed defects repaired

1. Same-day SNOMIN mineral-N amendments accumulated organic pools but overwrote NH4/NO3 placeholders. Mineral contributions are now additive.
2. Same-day irrigation signals overwrote `_RIRR`. Irrigation is now additive.
3. N senescence and N translocation independently claimed the same pre-transition donor N. Translocation is now limited after same-day N death and residual-N reservation.
4. MLWB retained the finished crop's root-zone geometry during fallow. Crop finish now marks rooting weights for reset to the default fallow rooting depth.

## Output temporal ownership

Daily output is written after current-day rate calculation. Consequently each row combines post-integration state variables with rates for the following transition. This is internally consistent with PCSE's state/rate architecture but is an interpretation hazard. In particular, rates on a crop finish date may be visible although no subsequent crop integration realizes them.

Crop summary output is collected after crop finalize. Terminal output is collected after soil finalize. State-based final values are therefore finalized, but summary and terminal output have different component scopes.

## Rotation and kiosk ownership

VariableKiosk aggressively flushes published states/rates at integration boundaries and crop deletion deregisters variables. No generic stale-kiosk defect was established.

However, internal non-kiosk soil metadata can remain stale. MLWB rooting weights were such a case: after crop deletion the published RD vanished, but layer Wtop/Wpot and `_RDold` retained the previous crop geometry. This is now repaired for fallow periods.

## Root crossing

Root depth is integrated before soil integration. MLWB updates rooting weights from the new RD, and both crop ET and SNOMIN subsequently use that same RD on the new rate day. No water-versus-N one-day mismatch was found at a root-layer crossing.

## Management composition

AgroManager forbids duplicate dates only within a single TimedEventsDispatcher. Separate dispatchers, and timed plus state dispatchers, can legally emit the same signal on the same day. Therefore event handlers must define composition semantics explicitly. The fertilizer and irrigation overwrite defects arose from violating this contract.

## Boundary contract

Crop start and crop finish are asymmetric. Start-date rates are later integrated; finish-date rates can be calculated after the transition that ended the crop and then discarded. Daily rate output must therefore be interpreted as prospective transition rates rather than already-realized daily totals.

# WOFOST 8.1 Deep Logic Audit — Tranche 1

Base: scientific qualification closeout `88e59ec0e17e879c3adbec6f7667ab332b5c2908`.

## Execution lifecycle reconstructed

For each Engine day after initialization:

1. Timer advances the date and may emit OUTPUT/TERMINATE.
2. Engine integrates crop, then soil, using rates already calculated for the
   preceding rate day.
3. Current-day weather is loaded.
4. AgroManager executes crop-calendar, timed and state events against the
   newly integrated states.
5. Crop rates are calculated.
6. Soil rates are calculated.
7. Requested output is captured from the post-integration states.
8. Deferred crop finish is finalized after rate calculation.

This is an explicit daily state/rate architecture. Calendar event dates label
the rate day on which an event becomes available; the resulting rate is
incorporated at the next integration boundary.

## Confirmed boundary defects repaired

### LOGIC-CC01: harvest/max-duration collision

Two independent conditionals allowed an explicit harvest reached on the same
day as max_duration to be overwritten by finish_type=`max_duration`.
The repair preserves explicit harvest as the causal finish reason.

### LOGIC-SE01: exact threshold at first observation

StateEventDispatcher used the first call only to initialise its sign. If a
state first became observable exactly at an event threshold, no event was
emitted and no later crossing was guaranteed. Exact first-observation equality
now emits the threshold event once.

## Explicit coupling contracts

### Water

Crop evapotranspiration is calculated before MLWB current-day rates. Published
TRA/WTRALY is therefore a prescribed crop extraction demand to the water
balance. Soil integration updates moisture before the following day's crop
rate calculation. This is explicit daily crop-demand/soil-response coupling.

### Nitrogen

Crop N demand is calculated before SNOMIN current-day rates. It uses NAVAIL
from the already integrated soil state. SNOMIN subsequently consumes the
published RNuptake demand. Same-day soil transformations do not feed back into
crop demand until the next rate day.

This is logically coherent as an explicit coupling, but it is a scientific
ordering assumption and should not be confused with simultaneous competition.

### Amendments and management

Timed/state events are dispatched after integration and before rate
calculation. SNOMIN amendment handlers populate rate placeholders, which are
consumed by the subsequent calc_rates and incorporated at the following
integration boundary. Event-date semantics should therefore be interpreted in
the Engine's rate/state convention, not as an instantaneous mid-step state
mutation.

## Further high-value logic targets

The next tranche should focus on:
- maturity/harvest/terminate collisions and final-day output ownership;
- crop rotations and signal lifetime after crop deletion;
- state events around crop start/deletion and missing kiosk variables;
- multi-threshold jumps that cross more than one StateEvent in one daily step;
- simultaneous timed + state events of the same physical process;
- crop-root-depth changes versus soil-layer/root-status update timing;
- first-day and last-day N/water uptake ownership.

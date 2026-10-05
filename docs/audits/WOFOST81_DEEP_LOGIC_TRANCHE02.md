# WOFOST 8.1 Deep Logic Audit — Tranche 2

## Collision and boundary semantics

### Final simulation date

Timer signals OUTPUT and TERMINATE as soon as END_DATE is returned. Engine then still performs the normal daily sequence: integrate old rates, load weather, run AgroManager, calculate rates, save requested output, and finally finalize soil/terminal output.

Therefore END_DATE is best understood as the final integration boundary. Rates calculated on END_DATE itself are not followed by another integration.

### Crop finish

Crop finish is intentionally deferred. A maturity signal raised during crop integration sets an Engine flag. AgroManager then sees the finish signal and may request termination. Engine nevertheless calls crop and soil calc_rates once more before the crop is finalized/deleted.

The resulting final crop states correspond to the transition that reached maturity. The newly calculated rates on the maturity date are transient and are not realized when the crop is deleted. They should not be interpreted as an additional production day.

### CropCalendar collision

Explicit harvest now has precedence if harvest and max_duration occur on the same calendar day. Baseline behavior overwrote the causal finish reason with max_duration.

### State-event thresholds

Thresholds are evaluated independently. A large daily state jump can therefore cross several rising thresholds and should dispatch all of them once. An adversarial qualification test now guards this behavior.

The separate first-observation equality defect from tranche 1 remains repaired: a threshold that is first observed exactly at equality is no longer silently lost.

## Crop deletion / rotation

SimulationObject deletion recursively unregisters states/rates. Engine then drops the crop object and explicitly invokes garbage collection because signal subscriptions historically retained deleted crop objects. A new crop start while a crop object still exists is rejected.

No additional rotation defect was proven in this tranche. This does not yet qualify arbitrary multi-crop rotations; it only means the inspected ownership and deletion path did not yield a falsified invariant.

## Interpretation

Two distinct date concepts must not be conflated in PCSE/WOFOST:

- a date at which a state transition is integrated;
- a date for which new rates/events are calculated.

Because rates are calculated after integration, events and reported rate variables can carry a calendar date even when their physical state increment occurs at the following integration boundary. This is the central logic contract behind management, soil coupling and final-day semantics.

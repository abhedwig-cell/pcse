# WOFOST 8.1.1: Python reference contract for a future Fortran implementation

**Status: SPECIFICATION ONLY — not yet an admitted baseline or exported dataset.**
**Candidate source:** `release/wofost81-repairs-rc1-20261017` at `76b2746fc100b50b45bc5d165bc1176f6018d683`.
The code is not an official WOFOST 8.1.1 release. PART-01 remains under scientific owner review in PR #4.

## Evidence already available

- `pcse/tests/test_data/wofost81_authority_wheat.yaml`: vendored crop parameters.
- `pcse/tests/test_data/wofost81_qualification_weather.yaml`: archived forcing.
- `pcse/tests/test_wofost81_snomin_e2e.py`: executable wheat/MLWB/SNOMIN fixture, including reference and low-N/high-C:N variants.
- `pcse/tests/test_wofost81_nzero_reachability.py`: existing low-mineral-N reachability observation and source for two profiles.
- `docs/audits/WOFOST81_FINDINGS.json`, integrated closeout and release records: previous qualification boundaries.

These inputs are synthetic or archival qualification fixtures, **not independently field-validated calibration datasets**. Do not regenerate expected results silently.

## Independent reference levels

**A. Process tests**: at identical inputs compare potential assimilation, respiration, leaf-area growth, partition fractions, N demand, organ N allocation, senescence and translocation separately. Preserve existing process invariants including mass and donor limits. Distinguish scientific process agreement from shared implementation bugs.

**B. Daily crop lifecycle**: identical input, parameters and management must yield comparable states and realized transition fluxes for all supported variants. Record failures at first divergence rather than comparing only final yields.

**C. Coupled reference**: separately qualify exchanges with SWAP5/ANIMO5. This is **not** covered by A or B. External water and N delivery and the transaction boundary are future interface decisions; do not silently replace the PCSE soil physics.

## Reference scenarios (existing first; gaps remain open)

| Case | Minimum coverage | Current reusable fixture |
| --- | --- | --- |
| Potential growth | carbon core, phenology, leaf, root and storage states | canonical WOFOST legacy tests; WOFOST81-specific daily export still required |
| Water limitation | RFTRA, TRA, TRAMX, root depth and growth | wheat MLWB/SNOMIN synthetic reference; isolating water stress requires an explicit matched pair |
| N limitation | organ N, Ndemand, RNuptake, Nfixation, crop-N balance | wheat N-limited/high-C:N profile from E2E and zero reachability tests |
| Combined water + N limitation | stress interactions and growth | **gap**: independently forced paired experiment not yet qualified |
| Reallocation, senescence, harvest | same-day biomass/N donor ownership, totals, finish events | existing scoped reallocation scientific and deep-logic tests |
| Consecutive crops and fallow | crop recreation, fallow rooting geometry, state handover | deep-logic lifecycle tests; complete two-crop reference export remains a **gap** |

A table row does not assert that a complete numerical reference series has been generated.

## Minimum daily record schema

Each row records the local model date, **state_time** (post-integration boundary) and **rate_interval** (the prospective transition after current-day calc_rates). Keep them explicitly distinct.

- Crop states: `DVS`, `LAI`, `RD`, `WLV`, `WST`, `WRT`, `WSO`, `TAGP`, `NamountLV`, `NamountST`, `NamountRT`, `NamountSO`, `NuptakeTotal`, `CTRAT`.
- Daily or prospective rates: `PGASS`, `GASS`, `MRES`, `DMI`, `TRA`, `TRAMX`, `RFTRA`, `Ndemand`, `RNuptake`, `RNfixation` plus organ growth/death, translocation and committed reallocation where published.
- Soil coupling evidence: layer rooting geometry, layerwise transpiration, mineral-N stocks/fluxes and surface fluxes, when the selected configuration publishes these variables.
- Events: sowing/emergence, irrigation/amendments, maturity/harvest, deletion/restart; record actual state application and rate-day dates separately.
- Units, dimensions (including per-layer ordering), missing-value convention and any preprocessing must be recorded for each field.

The existing `Wofost81_NWLP_MLWB_SNOMIN.conf` OUTPUT_VARS does not publish every item in this list (for example PGASS and some organ rates). Extend only a **reference-export configuration**, not the scientific model, when implementing the export. Do not report unexposed variables as measured.

## Reproducibility manifest required for every data export

- Source repository, immutable commit SHA, PCSE package/revision/model entrypoint and crop-model parameter-schema version.
- Exact crop/soil/site/forcing files and content digests; management calendar and event order.
- Runtime Python and relevant dependencies; numerical precision.
- Start/end dates and crop lifecycle boundaries, complete field list, units, temporal semantics, input-output hashes.
- Qualification invocation, test result and accepted known exceptions.

## Equivalence gates (must be fixed BEFORE examining Fortran divergences)

1. Hard physical invariants: conservation of biomass/C/N (with explicitly identified sources/sinks), no donor overdraft, no duplicate external uptake, consistent restart/event transaction.
2. Rate-to-state relationships must align across the **same integration boundary**, never compare same-row prospective rates to already-integrated states.
3. Agree on absolute/relative tolerances by process and physical scale, including near-zero values; choose these from Python reproducibility and precision characterization **before** a Fortran candidate is tuned. No arbitrary numeric acceptance thresholds are approved by this document.
4. Require named scientific owner sign-off for PART-01; reference data for current executable behavior may be archived as **provisional**, but may not be declared the authoritative Fortran scientific target before source admission.

## Outstanding owner decisions and work

- PART-01 history and scientific approval (PR #4).
- Remaining possible N-stress zero denominators are not proven unreachable for all valid crop parameters; targeted wheat tests do not prove universality.
- Reproduce and reconcile historical YAML legacy exceptions without confusing LINGRA with WOFOST.
- Implement deterministic export and compare immutable results to a separately reinstalled distribution; only then freeze reference hashes.
- Define SWAP5/ANIMO5 ownership and flux coupling as a separate admission stage.

**Gate:** no official release, independent Fortran translation, or SWAP/ANIMO migration follows from this specification alone.

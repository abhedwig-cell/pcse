# WOFOST 8.1.1 PART-01: source history, decision request and admission boundary

**Status:** SCIENTIFIC_MODEL_OWNER_DECISION_PENDING. This document is an evidence dossier, not scientific approval or a release declaration.

**Candidate branch:** `release/wofost81-repairs-rc1-20261017` at `76b2746fc100b50b45bc5d165bc1176f6018d683` (verified 2026-10-17). The candidate is **not** an official WOFOST 8.1.1 release. Its code and parameter semantics remain unchanged by this dossier.

## Primary source history

- `b746c38fe47a8013ee965430c8ca7f30926d169f` (2022-04-05): the previous `DVS_Partitioning_N` branch chose between water stress and nitrogen stress using `RFTRA < NNI`. The water-stress branch increased `FR`; the nitrogen-stress branch used `FLVMOD = exp(-NPART * (1-NNI))` to reduce leaf allocation and increase stem allocation. The commit commented out both branches and retained only the water-stress root response.
- `bc66319db01509955ba451085a0cac2eafc67b5f` (2022-04-08): the `NPART` parameter was commented out.
- Current executable `pcse/crop/partitioning.py`: `FRTMOD = max(1., 1./(RFTRA + 0.5))`; `FR = min(0.6, FRTB(DVS) * FRTMOD)`; `FL`, `FS`, `FO` use their DVS tables. No NNI/NPART dependency exists in this partitioning calculation.
- The inherited class documentation still describes N stress and NPART/NNI; the candidate carries a warning identifying that mismatch.

The source history shows the behavior was deliberately changed, **not** the scientific rationale, who approved it, or whether oxygen-stress-driven RFTRA should trigger the same response.

## Requested scientific owner determination

1. Confirm whether the RFTRA-only root allocation response with FR <= 0.6 is the intended WOFOST 8.1 model specification, including cases where RFTRA reflects oxygen stress rather than drought.
2. Establish why the NNI/NPART branch was removed: scientific retirement, incomplete N implementation, or other rationale. Cite the owner decision or scientific reference.
3. If RFTRA-only is endorsed, authorize correction of the obsolete prose **without changing equations or parameter schemas**. Document applicability and limitations.
4. If not endorsed, open a separate scientific formulation proposal with calibration impact, independent stress experiments and regression criteria. Do **not** reinstate NPART as an unqualified bugfix.

**Provisional engineering recommendation:** preserve the current executable behavior pending this decision; do not silently infer scientific approval from commit history.

## Current technical evidence and limitations

- The scoped N-stress growth-rate domain repair was qualified and merged in PR #1.
- The historic WOFOST72 PGASS YAML harness correction was qualified for representative case 01 and merged in PR #2. The remaining historic YAML cases were not each independently confirmed.
- A WOFOST81 winter-wheat N reachability probe passed in PR #3: minimum aboveground crop N 1.2375 kg N/ha (reference) and 0.231996342455 kg N/ha (strongly N limited). Minimum leaf N in the latter case was zero. This does **not** establish that aboveground total N=0 is unreachable for all valid crops or that NMAXLV(DVS)=0 is safe.
- Existing WOFOST81 tests and the canonical WOFOST72 regression envelope have passing GitHub Actions evidence for these scoped changes. This is **not** independent field validation and does not resolve PART-01.

## Gate to source admission and Fortran reference

- Scientific owner records PART-01 decision (name/date/rationale/reference).
- Maintainers review the scoped repaired Python candidate and explicitly approve a pinned commit for the specified supported WOFOST81 entrypoints and crop-parameter sources.
- Confirm accepted unresolved limitations (N-zero reachability, model-time semantics, spatial root assumptions) without incorrectly marking them solved.
- Freeze traceable daily-state/rate reference fixtures, preserving the existing output time boundary (post-integration states, prospective rates); specify deterministic inputs, metrics, units and comparison tolerances.

**No formal admission, Fortran translation, or SWAP5/ANIMO5 migration is authorized by this dossier.**

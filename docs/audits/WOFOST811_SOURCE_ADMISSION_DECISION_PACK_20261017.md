# WOFOST 8.1.1: source admission decision pack (2026-10-17)

**Status: READY_FOR_SCIENTIFIC_OWNER_AND_MAINTAINER_REVIEW; NOT ADMITTED.**
Candidate branch `release/wofost81-repairs-rc1-20261017`, pinned HEAD `72098bab86e47f0f3363a3a7b56464b3c2e64911`.
The code remains PCSE `6.0.14rc1+wofost81repair`, WOFOST parameter model 8.1, proposed model label 8.1.1 only. `pcse/release_info.json` still reports `official_model_release=false`, `maintainer_review=PENDING`, and `swap_migration=BLOCKED_UNTIL_SOURCE_ADMISSION`.

## Auditable evidence already completed

- Original scientific/deep logic review: `docs/audits/WOFOST81_FINDINGS.json` (49 findings), `WOFOST81_INTEGRATED_REVIEW_CLOSEOUT.md`, `WOFOST81_LOCAL_QUALIFICATION.md`.
- Original installation-qualified repair candidate: source commit `4c69f72449b24aa99636b7762ee6c02d99292296`; see `doc/wofost81_repairs.rst`. Its original release evidence is not an assertion that all subsequent commits were rebuilt as an official wheel.
- PR #1: `RGRLAI` and `RGRLAI_MIN` parameter domain; targeted tests and existing scientific tests green (runs 38992800900, 38993377585).
- PR #2: historical WOFOST72 YAML PGASS test-harness return/rate contract; representative case and regression envelope green (run 38993759582). Do not claim each inherited YAML case independently verified.
- PR #3: winter wheat N-reachability profiles, no model formula change (run 38994393233); minimum aboveground N in reference 1.2375 and low-mineral-N 0.231996342455 kg N/ha; zero leaf N observed in the low-N case. This does **not** prove all-zero aboveground N unreachable for all valid crops.
- PR #5: a documented Python/Fortran scientific reference contract and two provisional daily wheat traces (run 39015784979). Not yet authoritative Fortran reference data.
- PR #6: byte-identical wheat traces and manifest from two fresh Python venv installations on one GitHub runner (run 39017141893). This proves limited environment-local reproducibility, not cross-platform equivalence or field validity.
- Existing full YAML exceptions were historically 44 WOFOST72 assimilation and 20 LINGRA-NWLP failures on both candidate and comparison baseline; do not infer a fully green YAML suite from the representative PGASS harness repair.

## Decisions still required

**Scientific owner: PART-01.** PR #4 holds the history from 2022-04-05/08: NNI/NPART branches deliberately disabled, RFTRA-only root-allocation rule retained. Need explicit scientific reason and endorsement or separate formulation proposal; include whether oxygen-limited RFTRA should cause the same allocation response. No owner reply or sign-off was present at the last check on 2026-10-17.

**Maintainer/source admission.** Review final candidate commit, included bugfixes, package manifests, scientific qualification boundaries, accepted parameter validity and unresolved model assumptions. Choose an official version or decline it; build/check release artifacts for the **final pinned commit**, not just the earlier RC1 source. Explicitly approve or reject the WOFOST scientific reference and its supported model entrypoints.

**Known boundaries, not secretly resolved.** All-zero aboveground N and NMAXLV(DVS)=0 remain model-domain questions outside the two wheat trajectories. The model is a discrete daily transition system; crop-soil coupling uses existing daily explicit ordering, output states and prospective rates have distinct time meanings; root-activity/spatial assumptions and rooting-depth policy remain documented limitations.

## Decision recording template

- Scientific approver / date:
- PART-01 scientific verdict and rationale (including oxygen stress):
- Accepted supported WOFOST81 entrypoints, crops and parameter domains:
- Final candidate SHA and artifact identity:
- Reproducibility/equivalence tolerance specification:
- Explicit accepted exceptions or blocking scientific defects:
- Decision: ADMITTED / CONDITIONALLY_ADMITTED_WITH_DEFINED_SCOPE / REJECTED:
- Official version assigned (if any):
- SWAP/Fortran translation gate: BLOCKED until separate explicit source admission (even if this documentation is merged).

The releasebranch must remain scientific candidate status until these entries are resolved. This pack is documentation, not release approval.

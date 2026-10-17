# WOFOST 8.1.1 final technical qualification: focused recovery record

Reference candidate: `4c69f72449b24aa99636b7762ee6c02d99292296` (`release/wofost81-repairs-rc1-20261017`).
Candidate branch: `work/wofost811-nstress-final-qualification-20261017`.

## What changed

- `N_Stress.initialize` now rejects non-finite or invalid `RGRLAI`/`RGRLAI_MIN` combinations.
- Admissible parameter domain: `0 <= RGRLAI_MIN <= RGRLAI` and `RGRLAI > 0`.
- Added focused tests in `pcse/tests/test_wofost81_nstress_domain.py`.
- No changes to N stress, assimilation, allocation, or crop-N process formulas.

## What has NOT been qualified

The first GitHub PR qualification completed successfully at commit `2bc78eb` (run `38992512544`). The workflow was then extended to run the focused N-stress tests. GitHub Actions run `38992800900` on commit `9632969` **succeeded**, including PCSE installation, the focused N-stress domain tests, existing scientific/E2E tests and the canonical WOFOST72 regressions. No full YAML run or exact before/after WOFOST81 daily-series equivalence comparison was performed. Neither this limited qualification nor the merge of this fix constitutes scientific admission of WOFOST 8.1.1 or permission for SWAP translation.

The source contains other zero denominators:
- `NamountABG`: validity/reachability of an all-zero living-aboveground crop-N pool remains unresolved; do not silently substitute an epsilon.
- `NMAXLV(DVS)`: the valid crop-development domain and admissibility of a zero concentration require model-owner determination before a behavioral patch.
- Near-zero positive N pools require actual integrated runtime coverage.

## Historical assimilation reference

The old `WOFOST72_Assimilation.__call__` returns `PGASS` directly; the generic YAML `TestSimulationObject` invokes callable components without storing their return value in the rate field. This is a source-level hypothesis explaining zero reported PGASS despite positive historical YAML expected values. **Not runtime confirmed**; do not mark the 44 inherited YAML assimilation failures closed. Keep the 20 LINGRA-NWLP reference mismatches a separate PCSE question absent proof of a shared impact.

## Required next execution evidence

1. DONE: Run the focused N-stress parameter tests and existing WOFOST81 scientific/E2E tests through PR CI (`38992800900`, success). The E2E fixture exercises a complete reference wheat lifecycle, but the CI does not compare complete daily series byte-for-byte to the parent commit.
2. OPEN: Prove strict before/after WOFOST81 daily-series preservation if exact-equivalence admission is required; note the added validation is inactive for the known valid reference parameters.
3. Reproduce one historical assimilation YAML case and compare direct return, exposed rate, and stored output across the wrapper. Fix the test harness only after causal confirmation.
4. Construct valid reachable zero/near-zero crop-N cases and define their scientific contract; obtain owner decision before implementing a zero-N behavior.
5. Run only affected tests, then use the existing admission review; preserve PART-01 as a model-owner decision.

Status: **UNQUALIFIED_WORK_BRANCH**, not a new model release. No modifications to the original release branch.

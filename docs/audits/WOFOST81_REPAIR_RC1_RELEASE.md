# WOFOST 8.1 repair candidate 1, 2026-10-17

## Result

An executable, installable Python repair distribution is available, not merely
an audit report. Package: `pcse==6.0.14rc1+wofost81repair`; implementation
revision: `repair-rc1`. Proposed model release name: WOFOST 8.1.1, **not yet
officially assigned or admitted**. The crop-parameter version stays 8.1.

Source repository: `abhedwig-cell/pcse`.
Branch: `release/wofost81-repairs-rc1-20261017`.
Qualified audit base: `498326bead686d531e03d06d939cb02aa2f07e01`.
Candidate code commit: `7bd331ce617fcd0cd484ae2b2e4bd0f37e5f5e04`.
Candidate code tree: `ed47e3cfba06c002cce625eeb58f55606df0bb32`.
The remote tree exactly matches local code commit
`1c9073a7eb1642cb135f91831dae192435d2718a` used to build the distribution.

## Implemented, retained and changed

All 14 locally qualified technical repair findings are included, as enumerated
in `pcse/release_info.json`. They were already executable on the audit branch;
they have not been replaced by a fresh scientific formulation or an alternative
crop implementation. Packaging now distinguishes this fork from upstream PCSE.

The E2E tests previously depended on the root-level checkout's weather fixture,
and the wheel manifest did not include the authority wheat YAML. Both resources
are now part of the installed package. The weather fixture is a byte-identical
copy of the existing repository-owned YAML, not new or altered weather data.
The packaged qualification runner uses canonical suite entrypoints and returns
nonzero on failure. Four additional installed-release identity/resource tests
are included.

Production changes relative to the audit base are limited to package identity
and documentation. Four touched scientific modules were compared by Python AST
after removing docstrings: all match the qualified audit base exactly. No
requalification of unchanged numerical algorithms or repeat of the historical
456-test broad YAML run was required for this packaging/documentation step.

## Current qualification

| Check | Passed | Failed | Errors | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Source packaged qualification | 52 | 0 | 0 | 0 |
| Final wheel installed outside the source checkout | 52 | 0 | 0 | 0 |
| Source archive installation: release identity/resources + scientific E2E | 7 | 0 | 0 | 0 |

The 52-test gate comprises 17 deep-logic tests, 19 scientific/component/E2E
tests, 4 installed-release tests and 12 canonical WOFOST72 regressions. Counts
across invocations overlap. Compilation succeeds; wheel and sdist builds
succeed. The full HTML documentation builds with warnings treated as errors
(`-W --keep-going`). These are local results, not new GitHub Actions evidence.

The earlier full YAML result remains explicitly inherited: 392 passed and
64 failed, matching the qualified base by test name and assertion. Those
reference mismatches are not relabelled as harmless or silently skipped here.
Neither technical qualification nor packaging establishes field validation.

## Reproducible commands

In the candidate checkout:

```sh
python -m pip install --no-build-isolation -e . sphinx sphinx-rtd-theme build
python -m pip install --no-build-isolation --no-deps -e .
PYTHONWARNINGS=ignore python -m pcse.tests.qualification
python -m compileall -q pcse
python -m build --no-isolation
PYTHONWARNINGS=ignore python -m sphinx -W --keep-going -E -b html doc /tmp/wofost-rc-html
```

The wheel was installed with `--no-deps --force-reinstall` into a separate
`venv --system-site-packages`. Execution was from `/tmp`, with an assertion
that `pcse.__file__` is inside that environment's prefix, not the checkout.
The source archive was then installed with
`--no-build-isolation --no-deps --force-reinstall` and checked using
`python -m unittest -v pcse.tests.test_wofost81_release pcse.tests.test_wofost81_snomin_e2e`.

For a separate user environment, installation can instead use the immutable
code commit directly:

```sh
python -m pip install "git+https://github.com/abhedwig-cell/pcse.git@7bd331ce617fcd0cd484ae2b2e4bd0f37e5f5e04"
python -m pcse.tests.qualification
```

See the companion JSON for exact package versions, test-log hashes, artifact
hashes and the installed test-environment path. No published PyPI version is
claimed and the ordinary `pip install pcse` does not select this candidate.

## Documentation and admission

The Sphinx implementation guide, installation guide, release notes, catalogue,
reference guide, API context/docstrings and landing page have been updated.
The generated HTML is supplied as a preview. The documentation-change map
separately identifies the official PCSE, WOFOST theory and WUR page updates.
No official website was edited or deployed, and the separate theory PDF was
not silently rewritten.

Allard/model maintainers retain the decisions on PART-01, time architecture,
spatial root activity, crop-soil ordering and RDI/RDMCR/RDMSOL policy. Official
version assignment, source admission, upstream merge and documentation
publication remain pending. **SWAP migration is blocked until that source
admission exists**, followed by separate translation/integration qualification.

# WOFOST 8.1 repair candidate: documentation change map

Checked 2026-10-17. Candidate source is in `abhedwig-cell/pcse`, branch
`release/wofost81-repairs-rc1-20261017`. The official sites below have NOT been
edited or deployed by this work.

## Publication surfaces and prepared changes

| Surface | Source / URL | Change prepared | Publication gate |
| --- | --- | --- | --- |
| PCSE implementation supplement | `doc/wofost81_repairs.rst` -> `wofost81_repairs.html` | Executed repair contracts, equations, input domains, daily timing, installation, test limits, owner decisions and SWAP gate | Maintainer acceptance and RTD deployment |
| PCSE what's new | `doc/whatsnew.rst` -> https://pcse.readthedocs.io/en/stable/whatsnew.html | Repair-candidate release note; links to supplement; no official 8.1.1 claim | Same |
| PCSE installation | `doc/installing.rst` -> https://pcse.readthedocs.io/en/stable/user_guide.html | Replace outdated dependencies/Python 2 examples and historical pip transcripts; distinguish upstream PyPI from candidate install; document exit-status-safe qualification | Same; installing.rst is included in the user guide |
| PCSE model catalogue | `doc/available_models.rst` | Preserve 8.1 parameter schema and class names; distinguish package and implementation versions | Same |
| PCSE API documentation | `doc/code.rst` and changed class docstrings -> https://pcse.readthedocs.io/en/stable/code.html | Add ownership context; flag PART-01 rather than silently declaring the old N-stress description correct; expand SNOMIN name correctly | Same |
| PCSE reference guide | `doc/reference_guide.rst` | Exact first threshold, multiple daily threshold crossings, event accumulation and state/rate interpretation links | Same |
| PCSE landing page/build identity | `doc/index.rst`, `doc/conf.py` | Link candidate guide; current minimum Python; full candidate release string instead of truncated release | Same |
| WOFOST theory/system description | https://wofost.readthedocs.io/en/latest/ | Link the implementation supplement from the theory landing page if accepted; no theory replacement asserted | Separate documentation owner review |
| WUR WOFOST product page | https://www.wur.nl/en/research/products-services/wofost-world-food-studies | Replacement paragraph below, to be used only after source admission and official version assignment | WUR page owner and model maintainer |

## External documentation boundary

The WOFOST theory landing page explicitly describes its PDF as independent of
any WOFOST implementation. Its PDF/LaTeX source was not modified or reviewed
cover-to-cover here. No unverified page numbers, new citations or theoretical
formulations are introduced. Technical implementation invariants are documented
in the PCSE supplement. PART-01 and other open scientific choices require owner
decisions before changing any authoritative theory description.

The WUR page currently calls WOFOST 8.1 the most recent version and points users
towards the PCSE implementation. Do not change that claim to 8.1.1 merely because
an independently named candidate wheel exists.

## Proposed WUR paragraph after admission (not yet published)

The Python implementation of WOFOST 8.1 has received a maintenance update that
corrects nitrogen-pool limits, biomass and nitrogen transfers, the combination
of same-day management events and the transition from a crop to fallow soil.
The update also adds checks for invalid parameter and amendment inputs. These
corrections improve consistency at the affected process boundaries; they do
not constitute a new field validation or a redesign of the daily crop-soil
coupling. The versioned PCSE release notes describe compatibility, qualification
and remaining model assumptions.

Before use, insert the actual admitted model/package versions and immutable
release link. The paragraph is conditional copy, not an announcement that an
official release or admission already happened.

## Acceptance sequence

1. Maintainer reviews the 14 implemented technical repair findings and the
   executable qualification evidence. Owner-choice findings remain separate.
2. Maintainer assigns official model and package versions; confirms which
   inherited broad-suite reference failures can remain outside this release.
3. Admit/merge the source and build distributions from that exact commit.
4. Publish the corresponding Sphinx documentation; update external WUR/theory
   landing-page links only through their own authorized publication routes.
5. Register that admitted commit as source authority for a separate SWAP
   migration/translation qualification. The current candidate is not that gate.

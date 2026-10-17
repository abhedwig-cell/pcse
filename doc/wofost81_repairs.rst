.. _wofost81-repair-candidate:

WOFOST 8.1 repair candidate: implementation and migration guide
=============================================================

Release identity and status
---------------------------

This distribution is PCSE ``6.0.14rc1+wofost81repair``, implementing the
WOFOST 8.1 repair revision ``repair-rc1``. It contains executable corrections,
not just audit findings. The name **WOFOST 8.1.1** is a proposed future model
release name, subject to maintainer agreement. This fork is not an official
WOFOST 8.1.1 or 8.2 release and is not admitted for migration into SWAP.

The Python package version, implementation revision and crop-parameter version
have different purposes. All six ``Wofost81_*`` model entrypoints retain
``__cropmodelversion__ = "8.1"``. Do not rename them to ``Wofost811`` or change
the crop-parameter schema merely to label the repairs. Such a change would
affect automatic parameter selection. Record the package version, Git commit,
model class, parameter source and forcing alongside simulation results.

The installed package exposes its identity without a source checkout::

    import json
    from importlib.resources import files
    import pcse

    print(pcse.__version__)
    print(pcse.__wofost81_revision__)
    info = json.loads(files("pcse").joinpath("release_info.json").read_text())
    print(info["status"])

Corrections to soil mineral nitrogen
------------------------------------

**SNOMIN-01: ammonium immobilisation.** When the unconstrained combined
reaction would exhaust the available ammonium pool, the limiter must close
that pool at zero, not change immobilisation into a spurious source. With
pre-reaction pool :math:`A`, nitrification rate :math:`r_{nit}` and daily
interval :math:`\Delta t`, the limited mineralisation rate is

.. math::

   r_{min} = r_{nit} - A / \Delta t,
   \qquad A + (r_{min} - r_{nit})\Delta t = 0.

This states the implemented limiter contract, not a new reaction model.
The synthetic low-N/high-C:N experiment demonstrates that the correction can
materially affect crop N uptake and biomass. Its magnitude is not an estimate
of the effect in a field or calibrated application.

**SNOMIN-04: mineral-N transport.** Production NH4 and NO3 advective export is
limited by the donor's available pool. An internal transfer uses the same
committed amount at its donor and receiver, so clipping an export cannot
silently create or destroy N between layers. The raw low-level tracer formula
is not the production finite-pool contract; use the production transport
entrypoint when testing or integrating the component.

Corrections to crop biomass and nitrogen
----------------------------------------

**REALLOC-01: transactional biomass reallocation.** Leaves and stems cannot
donate more than their same-day surviving biomass. A requested daily transfer
:math:`R`, living donor biomass :math:`B` and same-day senescence :math:`D`
therefore give

.. math::

   R_{committed} = \min(\max(R, 0), \max(B-D, 0)).

The existing reallocation quota still applies. Newly produced biomass is not
made immediately available to satisfy the old donor request. Storage organs
receive the sum of committed leaf and stem transfers multiplied by
``REALLOC_EFFICIENCY``; they are not credited with an unfulfilled request.
The tests include an activated, full synthetic lifecycle, not only a test of
the limiter helper.

**LOGIC-NTRANS01: senescence owns its N before translocation.** Both processes
draw from the same living-organ N pool. With donor N :math:`N`, living biomass
:math:`B>0`, dying biomass :math:`D` and residual concentration :math:`c_r`,
the available translocatable amount is

.. math::

   N_{available} = \max(0, N - (N/B)D - \max(B-D,0)c_r).

Each organ's requested transfer is capped at its available amount; the total
storage transfer is recomputed from those committed organ transfers. Complete
senescence leaves no translocatable donor N. For zero living biomass the
available donor amount is zero, avoiding division by zero. The existing
translocation demand and time coefficient are otherwise retained.

**NBAL-01: balance-check timing.** Crop N balance is checked after integrating
the organ N pools and cumulative uptake, fixation and losses. The check then
verifies the transition just performed, rather than only the preceding state.
A closed balance does not by itself establish correct allocation or field
performance, which is why donor-ownership tests are also included.

Management events and fallow transitions
----------------------------------------

**LOGIC-CC01.** When explicit harvest and maximum crop duration coincide,
``harvest`` is retained as the finish reason. The maximum-duration condition
no longer overwrites an already established finish reason.

**LOGIC-SE01.** If the first observed state equals an event threshold exactly,
the event fires for rising, falling and either conditions. It does not fire
again merely because the state remains equal. A daily jump across several
thresholds dispatches each crossed threshold; it is not limited to one event
per day. An initial observation already beyond a threshold is not equivalent
to exact equality and is not retrospectively treated as an observed crossing.

**LOGIC-IRR01 and LOGIC-AMEND02.** Multiple irrigation events on the same rate
day add their effective amounts, ``amount * efficiency``, in the layered water
balance. Multiple SNOMIN amendments add their mineral NH4 and NO3 contributions;
organic amendment cohorts remain separate. Rate calculation consumes the
pending buffers and resets them. This is a one-rate-day accumulation contract,
not a promise about arbitrary ordering of management actions or every legacy
water-balance implementation.

**LOGIC-ROT02.** After crop deletion removes ``RD`` from the kiosk, the next
layered-water-balance integration resets fallow rooting geometry to the fixed
default of 10 cm and rebuilds root-zone water summaries. ``_RDold`` and
``_default_RD`` now use independent Traitlets descriptors, so previous crop
root growth cannot change the fallow default. Resetting summary geometry does
not redistribute the actual layer-water pools or change maximum-root-depth
policy for the next crop.

Input validation and compatibility
----------------------------------

Invalid configurations now raise ``PCSEError`` at initialization or at the
amendment-event boundary. Existing valid parameter names and units are retained.

.. list-table:: Validated domains
   :header-rows: 1
   :widths: 65 35

   * - Parameter or event property
     - Accepted domain
   * - REALLOC_STEM_FRACTION, REALLOC_LEAF_FRACTION, REALLOC_STEM_RATE,
       REALLOC_LEAF_RATE, REALLOC_EFFICIENCY
     - [0, 1]
   * - NFIX_FR, NMAXRT_FR, NMAXST_FR, NRESIDLV, NRESIDST, NRESIDRT
     - [0, 1]
   * - NMAXSO
     - Non-negative
   * - Layered ET IAIRDU, IOX
     - Exactly 0 or 1
   * - SNOMIN amendment amount, initial_age
     - Non-negative
   * - SNOMIN amendment application_depth, cnratio
     - Strictly positive
   * - SNOMIN amendment f_orgmat, f_NH4N, f_NO3N
     - Each in [0, 1]; f_NH4N + f_NO3N at most 1

This table describes the implemented checks. It is not a claim that every
possible malformed/non-finite input or every scientific parameter relationship
has been validated. For example, no extra combined organic/mineral composition
constraint or new rooting-depth policy is imposed by this candidate.

Daily timing and interpretation of output
-----------------------------------------

The WOFOST 8.1 implementation remains a **one-day transition model**.
Changing ``delt`` does not make it a qualified subdaily integrator. The crop-soil
coupling order has not been redesigned. Within the Engine's daily cycle,
previous rates are integrated, management for the current day is dispatched,
and rates for the next transition are calculated.

A daily output row can therefore contain post-integration states together with
prospective rates. A finish-date rate can be exposed even when crop deletion
prevents a subsequent crop integration. Event dates identify rate-day
availability, not an assertion that all resulting state changes have already
been integrated into that day's output. Crop start and crop finish are not
temporally symmetric. Check the intended state/rate boundary before comparing
daily observations, aggregating rates or designing a coupling interface.

Installation, testing and acceptance
------------------------------------

Install the candidate into a separate environment, not over a production setup::

    python -m venv .venv-wofost-repairs
    # Activate the environment using the command appropriate to your OS.
    python -m pip install "git+https://github.com/abhedwig-cell/pcse.git@release/wofost81-repairs-rc1-20261017"
    python -m pcse.tests.qualification

For reproducible work, replace the branch name in the install URL with the
specific Git commit recorded in the release evidence. The qualification
entrypoint works from the installed wheel, returns a failing process status
when a test fails, and invokes the canonical WOFOST72 ``suite()`` rather than
discovering abstract/template classes. It includes crop and weather fixtures;
no online parameter download is needed for these tests.

The prior integrated audit qualified 17 logic tests, 19 scientific/component/
E2E tests and 12 canonical legacy regressions. Its full YAML probe had 392
passed and 64 failed on both candidate and baseline, with matching failure
names and assertion values: 44 assimilation and 20 LINGRA-NWLP comparisons.
These are recorded inherited failures, not silently skipped tests or a claim
that the entire raw suite is green. The release adds installed-package checks;
the current counts and artifact hashes are recorded in its release evidence.

Before promoting this candidate, maintainers must review the repair set,
assign the official PCSE/WOFOST versions and admit the source. Only after that
may SWAP migration use the admitted source commit, with its own translation
and integration qualification. A Python package build or an audit finding
does not constitute that admission.

Unresolved choices remain visible: PART-01 (the documented N-stress
partitioning description versus the executed RFTRA-based root allocation),
spatial root activity, the daily coupling order and RDI/RDMCR/RDMSOL policy.
No new scientific formulation for those questions is selected here.

Documentation scope
--------------------

The PCSE implementation documentation is available at
https://pcse.readthedocs.io/en/stable/. This candidate updates its Sphinx
sources, release notes, API context and migration guidance. Publishing those
changes on the official service requires its maintainers' deployment.

The separate theory document at https://wofost.readthedocs.io/en/latest/
explicitly describes itself as independent of any implementation. These
technical corrections do not justify silently rewriting its scientific
formulations. The implementation supplement above documents the new executable
contracts. The accompanying documentation-change map identifies external
publication steps and outstanding owner decisions separately.

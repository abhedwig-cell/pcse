Installing PCSE
===============

Requirements
------------

This distribution requires Python 3.9 or later. The tested runtime for a
specific candidate is recorded in its qualification evidence; the minimum
requirement does not mean every Python/OS combination has been tested.

Runtime dependencies are declared in ``pyproject.toml`` and installed by pip:
PyDispatcher, PyYAML, openpyxl, requests, pandas, traitlets-pcse and dotmap.
The modified traitlets-pcse is required; normal Traitlets is not a qualified
substitution. NumPy is also used and is installed through pandas' requirements.

Separate environments
---------------------

Use a separate environment so the repair candidate cannot silently replace
the installation used for production simulations::

    python -m venv .venv-pcse

Activate it on Linux or macOS::

    source .venv-pcse/bin/activate

Or in Windows PowerShell, subject to your organization's execution policy::

    .venv-pcse\Scripts\Activate.ps1

Check the selected interpreter and installer::

    python --version
    python -m pip --version

Upstream package versus repair candidate
---------------------------------------

To install the package published by the upstream maintainers::

    python -m pip install pcse

That command does **not** select this fork's WOFOST 8.1 repairs. Install the
candidate from its branch instead (Git must be installed)::

    python -m pip install "git+https://github.com/abhedwig-cell/pcse.git@release/wofost81-repairs-rc1-20261017"

For repeatable experiments replace the branch name with the chosen full commit
SHA. A branch can move. Alternatively install a wheel built from that commit::

    python -m pip install "pcse-6.0.14rc1+wofost81repair-py3-none-any.whl"

Check the identity after installation::

    import pcse
    print(pcse.__version__)
    print(pcse.__wofost81_revision__)

The candidate intentionally reports a development version. It is not an
official new WOFOST release. The Wofost81 entrypoints and 8.1 crop-parameter
schema are unchanged. Read :doc:`wofost81_repairs` before updating applications.

Development and documentation
-----------------------------

Inside a checkout of the candidate branch::

    python -m pip install -e ".[docs,release]"
    python -m sphinx -b html doc build/html
    python -m build

Generated HTML is a local preview, not an update of the official Read the Docs
or WUR sites. Building a wheel does not publish it to PyPI or imply admission.

Qualification
-------------

The packaged qualification works from a checkout or wheel installation::

    python -m pcse.tests.qualification

It exits nonzero on failure and invokes canonical legacy regressions without
discovering template classes. The historical pcse.test() and python -m tests
entrypoints do not consistently propagate failures into process exit status,
so they are not release gates. The broad YAML suite has inherited assimilation
and LINGRA reference mismatches: consult the qualification record rather than
treating those as new repair regressions or established harmless discrepancies.


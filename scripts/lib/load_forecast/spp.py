"""SPP load-forecast spec — 2025 ITP Assessment Report v1.0, Figure 2.1.

SPP publishes **no standalone long-term load forecast**: its forward load view
lives inside the Integrated Transmission Planning (ITP) cycle, and the 2025 ITP
Assessment Report prints it as ONE bar chart — Figure 2.1 "Coincident Peak Load
by Model Year", printed p. 43 — with **four Base Reliability study years**:

    2026  61.7 GW      2029  66.5 GW      2034  69.8 GW      2044  76.4 GW

Those four rows, and nothing else, are what SPP-12 transcribed into
``data/raw/load-forecast/spp/spp.csv`` (edition ``2025 ITP``, vintage 2025),
read by the package's default :func:`~scripts.lib.load_forecast.parse_unified_csv`.
Three properties of the source are stated here because a consumer would
otherwise have to infer them (SPP-12's ``SOURCES.md`` says the same):

* **There is NO energy series.** Every SPP load-growth constant derived from
  this datatype is a PEAK-growth constant; ``constants.DEMAND_GROWTH_RATES["SPP"]``
  says so on its row (the table's uniform energy basis cannot be honoured for
  SPP, and the divergence is disclosed, not smoothed — rule 14 ``[R-ACCURATE]``).
* **The year<->value pairing is a chart vector read** — ``pdfminer`` recovers the
  data labels and the axis categories but not their pairing; the ascending-to-
  ascending assignment is the only one consistent with a growth forecast and is
  corroborated twice in ``SOURCES.md``. MISO's rows carry the same class of
  read. Replace with tabulated values if the ITP model data ever lands.
* **The published peak definition is "coincident"** (SPP's system coincident
  peak, one of the metrics the datatype's ``METRIC_UNITS`` deliberately leaves in
  the publisher's own vocabulary). The datatype's ``basis`` key admits only
  ``net`` / ``gross`` / ``unspecified``, and SPP draws no net/gross distinction
  for this series, so the spec's ``default_basis`` is ``"unspecified"`` — the
  honest label the package reserves for exactly that case.

THE INTERPOLATION RULE, DECLARED ONCE, HERE. Four study years are not an annual
series, and every consumer that needs a peak for an intermediate year — the
``DEMAND_GROWTH_RATES`` era CAGRs first among them — uses
:func:`interpolate_peak_mw`: **piecewise-linear in calendar year between adjacent
study years, flat-hold outside the published span**. Piecewise-linear because
the ITP's own §3 growth narrative (printed pp. 88-92) describes monotone growth
between study years and publishes no curvature; flat-hold because extending a
forecast past its own horizon is an invention the DATACENTER_ADDITIONS_MW /
ELECTRIFICATION_LAYERS tables already refuse. This is a modelling choice and it
is labelled as one wherever its output is written down (the ``DEMAND_GROWTH_RATES``
row carries the worked arithmetic: interpolated 2031 peak 67.82 GW; near CAGR
2026->2031 0.019095; long CAGR 2031->2044 0.009206). Nothing interpolated is
written into the curated datatype itself — it carries the four published rows
only, so the published-vs-derived line stays visible.

Rule 13 ``[R-MEASURED]`` posture is the package's: a forward-looking published
input that regenerates from the next ITP vintage (the 2023 / 2024 ITP reports
carry earlier vintages of the same series — ``SOURCES.md`` follow-ups) and
responds to changed conditions; never a measured outcome, never a target.

Registered 2026-09-06 by lane SPP-20 (docs/multi-iso/spp-addition-plan-2026-09.md
§5, gate G12 — a spec needs a real edition and a vintage >= 2020, which the
SPP-12 intake supplied).
"""

from __future__ import annotations

from bisect import bisect_left

from . import IsoSpec, register

# The published Base Reliability study years (documentary — the VALUES live in
# the CSV, never here; this tuple only names the knots the interpolation rule
# below joins).
STUDY_YEARS: tuple[int, ...] = (2026, 2029, 2034, 2044)


def interpolate_peak_mw(year: int, peaks_by_year: dict[int, float]) -> float:
    """Return the SPP coincident peak (MW) for ``year`` under the declared rule.

    Piecewise-linear in calendar year between the two adjacent published study
    years; flat-hold at the first / last published value outside the span. The
    single place the "four study years -> any year" step is defined, so every
    consumer derives on one rule.

    Args:
        year: Calendar year to evaluate.
        peaks_by_year: ``{study_year: peak_mw}`` — the ``annual_peak_mw`` rows of
            ``spp.csv`` (at least one entry).

    Returns:
        The interpolated (or held) peak in MW.

    Raises:
        ValueError: if ``peaks_by_year`` is empty.
    """
    if not peaks_by_year:
        raise ValueError("interpolate_peak_mw: no published peak rows supplied")
    years = sorted(peaks_by_year)
    if year <= years[0]:
        return float(peaks_by_year[years[0]])
    if year >= years[-1]:
        return float(peaks_by_year[years[-1]])
    hi = bisect_left(years, year)
    y0, y1 = years[hi - 1], years[hi]
    p0, p1 = float(peaks_by_year[y0]), float(peaks_by_year[y1])
    return p0 + (p1 - p0) * (year - y0) / (y1 - y0)


SPEC = register(
    IsoSpec(
        iso="SPP",
        edition="2025 ITP",
        vintage=2025,
        default_basis="unspecified",
    )
)

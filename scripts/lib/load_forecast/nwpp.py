"""NWPP load-forecast spec — a participant-IRP ASSEMBLY, because the pool publishes none.

The Northwest Power Pool is a pool of seventeen balancing authorities, not an
ISO, and issues no Gold Book / CELT / LTLF / ITP equivalent. Lane NWPP-12
(``docs/handoffs/FINDING-nwpp-12-2026-09-13.md`` §0.1, gate G12) therefore
ASSEMBLED ``data/raw/load-forecast/nwpp/nwpp.csv`` (83 rows) from the
participants' own filed plans, and documented the assembly rule, its coverage
and every publisher that supplies no row in that directory's ``SOURCES.md``:

* **PacifiCorp 2025 IRP** — Vol. 1 printed p. 114, Table 6.1, system summer
  coincident peak before EE, 2025–2044 (PACE + PACW, 25.40 % of 2024 demand);
* **Idaho Power 2025 IRP** — printed p. 89, Table 8.2, annual peak 2024
  actual + 2026–2045 at the 10th / 50th / 95th percentile (IPCO, 6.43 %);
* **PSE 2023 Electric Progress Report** — Ch. 6 printed p. 6.1, base peak
  before additional DSR, 2024 and 2045 (PSEI, 8.53 %).

**Coverage is the load-bearing caveat and it is NOT closed here: 4 of 17 BAs,
40.36 % of 2024 footprint demand.** BPAT — the largest BA at 20.26 % — files no
IRP (a federal power marketing administration), and NorthWestern, NV Energy,
PGE and Avista publish their series only as images. Nothing in the datatype is
scaled, summed or interpolated to the footprint; the CSV carries the published
rows only, one ``edition`` / ``vintage`` per row so the mixed vintages (2025,
2025, 2023) stay visible.

Registered strings (declared by NWPP-12 for this spec, used verbatim):
``edition = "Participant IRP assembly (2025 cycle)"``, ``vintage = 2025`` (the
newest constituent publication that actually supplies a row), ``default_basis
= "unspecified"`` (no publisher draws the net/gross distinction for these
series; PacifiCorp's is a coincident summer peak, PSE's a 1-in-2 seasonal peak,
Idaho Power's an annual peak — three peak definitions in one file, carried in
the publishers' own vocabulary).

THE INTERPOLATION / ASSEMBLY RULE, DECLARED ONCE, HERE. Any consumer needing a
footprint-covered peak for a calendar year — ``constants.DEMAND_GROWTH_RATES
["NWPP"]``'s era CAGRs first among them — uses :func:`covered_peak_mw`: for
each publisher's ``mid`` series, **piecewise-linear in calendar year between
adjacent published years, flat-hold outside the published span** (the SPP rule,
``scripts/lib/load_forecast/spp.py``), then **summed over the three covering
publishers**. It is a COVERED-PUBLISHER peak, not a footprint peak — 40 % of
load — and a growth RATE derived from it is a rate of the covered 40 %, which
is stated on the ``DEMAND_GROWTH_RATES`` row rather than smoothed away
(rule 14 ``[R-ACCURATE]``). PSE's two published points (2024, 2045) make its
contribution a single straight line by construction. Worked arithmetic (the
``mid`` series: PacifiCorp 2025–2044, Idaho Power 50th percentile 2026–2045,
PSE 2024/2045): covered peak 2026 = 11,270.0 + 3,934.0 + 4,940.0 = 20,144.0 MW;
2031 = 12,104.0 + 4,949.0 + 5,407.7 = 22,460.7; 2044 = 15,518.0 + 5,484.0 +
6,623.5 = 27,625.5 → near CAGR 2026→2031 = (22,460.7 / 20,144.0)^(1/5) − 1 =
0.022010; long CAGR 2031→2044 = (27,625.5 / 22,460.7)^(1/13) − 1 = 0.016048.
Nothing interpolated is written into the datatype itself.

Rule 13 ``[R-MEASURED]`` posture is the package's: a forward-looking published
input that regenerates from each participant's next IRP vintage and responds to
changed conditions; never a measured outcome, never a target.

Registered 2026-09-14 by lane NWPP-20 (docs/multi-iso/nwpp-addition-plan-2026-09.md
§5, gate G12 — a spec needs a real edition and a vintage >= 2020, which the
NWPP-12 assembly supplied).
"""

from __future__ import annotations

from bisect import bisect_left

from . import IsoSpec, register

# The covering publishers' ``area`` labels in nwpp.csv (documentary — the VALUES
# live in the CSV, never here).
COVERING_PUBLISHERS: tuple[str, ...] = (
    "PacifiCorp",
    "Idaho Power",
    "Puget Sound Energy",
)


def interpolate_peak_mw(year: int, peaks_by_year: dict[int, float]) -> float:
    """Return one publisher's peak (MW) for ``year`` under the declared rule.

    Piecewise-linear in calendar year between the two adjacent published years;
    flat-hold at the first / last published value outside the span. Identical
    to the SPP rule so both assemblies derive on one construction.

    Args:
        year: Calendar year to evaluate.
        peaks_by_year: ``{published_year: peak_mw}`` for ONE publisher's ``mid``
            series (at least one entry).

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


def covered_peak_mw(
    year: int, peaks_by_publisher: dict[str, dict[int, float]]
) -> float:
    """Return the covered-publisher peak (MW) for ``year``: the sum of each
    publisher's :func:`interpolate_peak_mw`.

    Args:
        year: Calendar year to evaluate.
        peaks_by_publisher: ``{publisher: {published_year: peak_mw}}`` — the
            ``mid`` rows of ``nwpp.csv`` grouped by ``area``.

    Returns:
        The summed peak in MW over the publishers supplied (40.36 % of the
        footprint when all three are present — never a footprint peak).

    Raises:
        ValueError: if no publisher is supplied.
    """
    if not peaks_by_publisher:
        raise ValueError("covered_peak_mw: no publisher series supplied")
    return sum(interpolate_peak_mw(year, s) for s in peaks_by_publisher.values())


SPEC = register(
    IsoSpec(
        iso="NWPP",
        edition="Participant IRP assembly (2025 cycle)",
        vintage=2025,
        default_basis="unspecified",
    )
)

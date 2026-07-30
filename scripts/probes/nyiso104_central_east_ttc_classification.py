"""nyiso-104: is the Central-East monthly TTC envelope an OVERLAY or a MECHANISM?

Rule 13 [R-MEASURED] classification instrument for
``pipeline/ttc.py::apply_iso_monthly_ttc`` (+ its sibling ``apply_iso_year_ttc``),
which apply ``constants.NYISO_INTERFACE_TTC_BY_MONTH`` /
``NYISO_INTERFACE_TTC_BY_YEAR`` to the ``Upstate_West -> Capital_Hudson`` link
in the backcast only. **No LP.** Neither helper carries a D-5 registry row, so
D-5 parity is blind to the whole family.

The fork the charter poses
--------------------------
(a) a MEASURED series with no forward analogue -> a genuine backcast overlay:
    declare it, and give it a ``D5_REGISTRY`` row with ``declared=True``; or
(b) forward-reproducible market design (a *published seasonal rating* that
    regenerates for a forward year) -> a MECHANISM under rule 13, in which case
    declaring it is wrong and it must be wired into ``runner.py`` instead, as
    nyiso-102 did for the three downstate mechanisms.

The charter forbids settling this by analogy to nyiso-102. So it is settled
here on the source data's own forward reproducibility, with a falsifiable test.

The test (T1) and why it discriminates
--------------------------------------
A *published seasonal rating* is a deterministic engineering quantity: an
ambient-adjusted conductor/stability rating recomputed the same way every year.
On an unchanged network it must therefore repeat — the same months derate, by
the same relative amount, every year. A *realized operational posting* embeds
that year's own approved transmission-outage schedule, which is idiosyncratic
per year.

So: normalize each year's 12 monthly means by that year's own annual mean
(removing the level, which is not in dispute) and correlate the residual shapes
across the two years that share an unchanged topology.

* **Hypothesis (b)** — published seasonal rating -> shape correlation high
  (r ~ 0.9+) between same-topology years, and the derate lands in the same
  months.
* **Hypothesis (a)** — realized postings -> shape correlation ~0, and the
  deepest-derate month moves between years.

2024 and 2025 are the two fully post-upgrade years (NY Transco AC Transmission
Segment A energized Dec 2023), so they share one topology and are the clean
same-topology pair. 2023 is pre-upgrade for Jan-Nov and is reported for context
only.

T2 decomposes the variance into the between-year (level/step) component and the
within-year (monthly shape) component, because the two components have
*different* rule-13 answers and the classification only turns on the second.

T3 tests the specific claim in the ``constants.py`` provenance comment — "a
recurring late-summer/shoulder derate" — since that claim, if true, would be
evidence for (b).

Sources
-------
``constants.NYISO_INTERFACE_TTC_BY_MONTH`` / ``_BY_YEAR``, derived by
``scripts/data/derive_nyiso_central_east_ttc.py`` from the ``TTC (DAM)`` column
of NYISO's MIS ``ATC_TTC`` postings for the ``CENT EAST`` interface, aggregated
to a calendar-month arithmetic mean and rounded to 25 MW.

    uv run python scripts/probes/nyiso104_central_east_ttc_classification.py
"""

from __future__ import annotations

import itertools
import statistics as st
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
)

LINK = ("Upstate_West", "Capital_Hudson")
# NY Transco "AC Transmission" Segment A energized December 2023, so Jan-Nov
# 2023 sits on the pre-upgrade network and 2024/2025 share the post-upgrade one.
POST_UPGRADE_YEARS = (2024, 2025)
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
# constants.py provenance comment claims "a recurring late-summer/shoulder
# derate"; T3 tests exactly those months against the rest of the year.
LATE_SUMMER_SHOULDER = (8, 9, 10, 11)  # Aug-Nov, 1-indexed


def _pearson(a: list[float], b: list[float]) -> float:
    ma, mb = st.mean(a), st.mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = (sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b)) ** 0.5
    return num / den if den else float("nan")


def _rank(vals: list[float]) -> list[float]:
    """Average-tie ranks (the postings round to 25 MW, so ties are real)."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    ranks = [0.0] * len(vals)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and vals[order[j + 1]] == vals[order[i]]:
            j += 1
        avg = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = avg
        i = j + 1
    return ranks


def _spearman(a: list[float], b: list[float]) -> float:
    return _pearson(_rank(a), _rank(b))


def _shape(vals: list[float]) -> list[float]:
    """Monthly index = month mean / that year's own annual mean (level removed)."""
    mu = st.mean(vals)
    return [v / mu for v in vals]


def _perm_p(a: list[float], b: list[float], observed: float) -> float:
    """One-sided p for ``observed`` against the dihedral calendar null.

    The null family is the 24 relabelings of ``b`` that preserve its
    month-to-month structure but break its calendar alignment with ``a`` — the
    12 rotations and their reflections. It answers the question the seasonal-
    rating hypothesis actually makes: does the shape agree *at the true month
    alignment* better than it would against a shifted or reversed calendar? A
    real seasonal rating aligns only one way, so it should sit at p ~ 0.
    """
    n = len(b)
    null = []
    for shift in range(n):
        rot = b[shift:] + b[:shift]
        null.append(_pearson(a, rot))
        null.append(_pearson(a, rot[::-1]))
    ge = sum(1 for r in null if r >= observed)
    return ge / len(null)


def main() -> None:
    by_month = {
        y: NYISO_INTERFACE_TTC_BY_MONTH[y][LINK] for y in NYISO_INTERFACE_TTC_BY_MONTH
    }
    by_year = {
        y: NYISO_INTERFACE_TTC_BY_YEAR[y][LINK] for y in NYISO_INTERFACE_TTC_BY_YEAR
    }
    years = sorted(by_month)

    print("=" * 78)
    print("nyiso-104 — Central-East monthly TTC: overlay (a) or mechanism (b)?")
    print("=" * 78)
    print(f"link: {LINK[0]} -> {LINK[1]}   source: NYISO MIS ATC_TTC 'TTC (DAM)'")
    print()

    print("--- levels (MW) ---")
    print("year  " + "  ".join(f"{m:>5}" for m in MONTHS) + "   annual")
    for y in years:
        row = "  ".join(f"{v:5.0f}" for v in by_month[y])
        print(f"{y}  {row}   {by_year[y]:6.0f}")
    print()

    # -- T1: same-topology shape reproducibility ---------------------------
    print("--- T1: does the monthly SHAPE repeat on an unchanged network? ---")
    shapes = {y: _shape(by_month[y]) for y in years}
    print("year  " + "  ".join(f"{m:>5}" for m in MONTHS))
    for y in years:
        print(f"{y}  " + "  ".join(f"{v:5.3f}" for v in shapes[y]))
    print()
    a, b = POST_UPGRADE_YEARS
    r_post = _pearson(shapes[a], shapes[b])
    rho_post = _spearman(shapes[a], shapes[b])
    print(
        f"SAME-TOPOLOGY pair {a} vs {b}:  Pearson r = {r_post:+.3f}   "
        f"Spearman rho = {rho_post:+.3f}"
    )
    print(
        f"  dihedral-null one-sided p = {_perm_p(shapes[a], shapes[b], r_post):.3f} "
        "(vs rotated/reflected calendars)"
    )
    for y1, y2 in itertools.combinations(years, 2):
        if (y1, y2) == POST_UPGRADE_YEARS:
            continue
        # 2023 is pre-upgrade Jan-Nov; compare only those months, and only for
        # context — a cross-topology pair cannot test rating reproducibility.
        r = _pearson(shapes[y1][:11], shapes[y2][:11])
        print(f"  (context, CROSS-topology, Jan-Nov) {y1} vs {y2}: r = {r:+.3f}")
    print()
    for y in POST_UPGRADE_YEARS:
        lo = min(range(12), key=lambda i: shapes[y][i])
        hi = max(range(12), key=lambda i: shapes[y][i])
        print(
            f"  {y}: deepest derate = {MONTHS[lo]} ({shapes[y][lo]:.3f}), "
            f"peak = {MONTHS[hi]} ({shapes[y][hi]:.3f})"
        )
    print()

    # -- T2: variance decomposition ---------------------------------------
    print("--- T2: how much of the variation is LEVEL vs SHAPE? ---")
    all_vals = [v for y in years for v in by_month[y]]
    grand = st.mean(all_vals)
    ss_total = sum((v - grand) ** 2 for v in all_vals)
    ss_between = sum(12 * (st.mean(by_month[y]) - grand) ** 2 for y in years)
    ss_within = sum((v - st.mean(by_month[y])) ** 2 for y in years for v in by_month[y])
    print(f"  total SS                       {ss_total:12.0f}")
    print(
        f"  between-year (LEVEL / step)    {ss_between:12.0f}  "
        f"{100 * ss_between / ss_total:5.1f}%"
    )
    print(
        f"  within-year  (monthly SHAPE)   {ss_within:12.0f}  "
        f"{100 * ss_within / ss_total:5.1f}%"
    )
    post_within = sum(
        (v - st.mean(by_month[y])) ** 2 for y in POST_UPGRADE_YEARS for v in by_month[y]
    )
    print(
        f"  ...of which post-upgrade only  {post_within:12.0f}  "
        f"{100 * post_within / ss_total:5.1f}%  (the part in dispute)"
    )
    for y in POST_UPGRADE_YEARS:
        sd = st.pstdev(by_month[y])
        print(
            f"  {y} within-year sd = {sd:5.0f} MW ({100 * sd / by_year[y]:.1f}% of level)"
        )
    print()

    # -- T3: is the "recurring late-summer/shoulder derate" claim true? ----
    print("--- T3: constants.py claims 'a recurring late-summer/shoulder derate' ---")
    tag = "/".join(MONTHS[m - 1] for m in LATE_SUMMER_SHOULDER)
    for y in POST_UPGRADE_YEARS:
        s = shapes[y]
        late = st.mean([s[m - 1] for m in LATE_SUMMER_SHOULDER])
        rest = st.mean([s[i] for i in range(12) if i + 1 not in LATE_SUMMER_SHOULDER])
        print(
            f"  {y}: {tag} index {late:.3f} vs rest {rest:.3f}  "
            f"-> derate {100 * (rest - late) / rest:+5.1f}%"
        )
    print()

    # -- verdict ----------------------------------------------------------
    print("=" * 78)
    reproducible = r_post >= 0.9
    print("VERDICT:", "(b) MECHANISM" if reproducible else "(a) OVERLAY")
    if not reproducible:
        print(
            f"  The same-topology shape correlation is r = {r_post:+.3f}, not the\n"
            "  r ~ 0.9+ a published seasonal rating recomputed the same way each\n"
            "  year would produce. The deepest-derate month MOVES between two\n"
            "  years of identical topology. The monthly envelope is therefore a\n"
            "  REALIZED operational series (that year's own approved transmission\n"
            "  outages), not a forward-reproducible rating: rule 13's test — could\n"
            "  this quantity be produced for a forward year from forward drivers? —\n"
            "  fails for the SHAPE.\n"
            "  The LEVEL is a different matter and already HAS its forward channel\n"
            "  (data/raw/transmission-expansion/nyiso.csv + the static 2,850 MW,\n"
            "  which is itself the measured post-upgrade DAM mean), so nothing is\n"
            "  missing from the forecast that declaring this would supply."
        )
    print("=" * 78)


if __name__ == "__main__":
    main()

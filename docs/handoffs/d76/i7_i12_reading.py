#!/usr/bin/env python3
"""capx D76 phase 0 — the I7/I12 HIT/MISS reading. Zero LP, committed artifacts only.

**Why this script exists.** The D76 charter asks whether "the sign of the
position error the delta implies matches the FC-1 I7/I12 residual on the
board". It does not, because there IS no such board residual: FC-1 reads
**SKIPPED — "no committed invariant record"** on every one of the 49 T1-H
entries in ``frontend/data/forecast/ff-verdicts.json``, all six ISOs. The
residual is therefore RECONSTRUCTED here from each bundle's own committed
per-year ledger, using the shipped checker's own formulae:

* **I7** (``check_forecast_invariants.check_i7_reliability_floor``, capacity-
  market branch): ``accredited_firm = peak x (1 + reserve_margin)`` must clear
  ``resolve_adequacy_requirement_mw(config, iso, peak, year)``. Both operands
  are already committed in the ledger — ``peak_demand_mw`` (the LP's, i.e.
  MEASURED, peak) x ``reserve_margin``, against ``adequacy_requirement_mw``
  (the same resolver on the same measured peak) — so the residual is read, not
  re-derived. ERCOT is energy-only: its I7 is the retirement-bounded nameplate
  floor, computed here on ``fleet_by_fuel_before/after`` exactly as the checker
  does.
* **I12**: ``reserve_margin`` inside ``[requirement/peak - 1, + 15.0 pp]`` for a
  capacity-market ISO; the scalar ``planning_reserve_margin`` floor for ERCOT.

**The prediction being graded.** The seam peak the screens consumed is
``screen_peak_demand_mw``; the peak the checker grades on is
``peak_demand_mw``. Where the seam ran BELOW the measured load the screens
tested a bar that was too low, so they under-retained / under-built and the
fleet should read SHORT against the checker's bar (I7 FAIL / I12 below band).
Where it ran ABOVE, they over-procured and the fleet should read LONG. HIT
when the observed residual's sign matches; MISS when it does not. **This is a
reading, not a gate** — it tells the director whether the defect explains a
board row, and is reported either way.

``screen_peak_demand_mw`` is a capx D52 ledger field, so a pre-D52 bundle
cannot show the delta its OWN screens saw. Those ISOs are reported
``UNOBSERVABLE`` rather than graded against the HEAD delta, which is a
different recipe's number.

Output: ``docs/handoffs/d76/i7_i12_reading.json`` + a printed table.
"""

import json
import sys
from pathlib import Path

sys.path[:0] = ["src", "."]

# ruff: noqa: E402  (sys.path must be set before market_sim resolves)

from market_sim.config.constants import MARKET_DESIGN
from scripts.check_forecast_invariants import (
    FIRM_CLEAN_FUELS,
    Thresholds,
    _thermal_mw,
)

# The checker's own thresholds and fuel sets, IMPORTED rather than restated, so
# this reading can never drift from the gate it reconstructs (rule 5).
T = Thresholds()

# The frontier bare T1-H bundle per ISO — the directory carrying the cache key
# the board's ``<iso>-t1h`` entry (or its newest successor) was scored on.
BUNDLES = {
    "CAISO": "caiso-2021-2025-realized-t1h-d46",
    "ERCOT": "ercot-2021-2025-realized-t1h-d46",
    "MISO": "miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio",
    "NEISO": "neiso-2021-2025-realized-t1h-d46",
    "NYISO": "nyiso-2021-2025-realized-t1h-d52-devintage",
    "PJM": "pjm-2021-2025-realized-t1h-d74-nodefaultcap",
}


def ledgers(iso: str, bundle: str) -> dict[int, dict]:
    """Load a bundle's committed per-year evolution ledgers.

    Args:
        iso: ISO code (the bundle's ISO subdirectory).
        bundle: Bundle directory name under ``results/hindcast/``.

    Returns:
        ``{year: ledger dict}``.
    """
    root = Path("results/hindcast") / bundle / iso
    key_dirs = [p for p in root.iterdir() if p.is_dir()]
    if len(key_dirs) != 1:
        raise RuntimeError(f"{bundle}/{iso}: expected one cache-key dir, got {key_dirs}")
    return {
        int(p.name[len("evolution_"):-len(".json")]): json.loads(p.read_text())
        for p in sorted(key_dirs[0].glob("evolution_*.json"))
    }


def read_year(iso: str, year: int, led: dict) -> dict | None:
    """Reproduce the shipped I7/I12 measurement for one committed ledger year.

    Args:
        iso: ISO code.
        year: Ledger year.
        led: The committed ledger dict.

    Returns:
        The measured row, or ``None`` for a bridge year (no solve, no floor).
    """
    peak = led.get("peak_demand_mw")
    rm = led.get("reserve_margin")
    if peak is None or not peak > 0.0:
        return None  # bridge year — the checker `continue`s here too
    design = MARKET_DESIGN.get(iso)
    capacity_market = bool(design.capacity_market) if design else True
    row = {
        "measured_peak_mw": round(float(peak), 3),
        "screen_peak_mw": led.get("screen_peak_demand_mw"),
        "reserve_margin": rm,
    }
    row["seam_delta_mw"] = (
        round(float(row["screen_peak_mw"]) - float(peak), 3)
        if row["screen_peak_mw"] is not None
        else None
    )
    if capacity_market:
        if rm is None:
            return None
        firm = float(peak) * (1.0 + float(rm))
        # The ledger's own ``adequacy_requirement_mw`` IS
        # resolve_adequacy_requirement_mw(config, iso, measured peak, year) —
        # the identical call the checker makes (runner.py:4808).
        req = led.get("adequacy_requirement_mw")
        if req is None:
            return None
        slack = firm - float(req)
        floor = float(req) / float(peak) - 1.0
        row.update(
            accredited_firm_mw=round(firm, 3),
            requirement_mw=round(float(req), 3),
            i7_slack_mw=round(slack, 3),
            i7=("FAIL" if slack < -T.reliability_slack_mw else "PASS"),
            i12_floor=round(floor, 6),
            i12_band_hi=round(floor + T.reserve_margin_band_pp, 6),
            i12=(
                "BELOW" if float(rm) < floor - 1e-6
                else "ABOVE" if float(rm) > floor + T.reserve_margin_band_pp + 1e-6
                else "IN-BAND"
            ),
        )
    else:
        # Energy-only (ERCOT): the retirement-bounded nameplate floor.
        after = led.get("fleet_by_fuel_after") or {}
        before = led.get("fleet_by_fuel_before") or {}
        firm_clean = sum(mw for f, mw in after.items() if f in FIRM_CLEAN_FUELS)
        th_after = _thermal_mw(after)
        th_before = _thermal_mw(before)
        floor_mw = (float(peak) - firm_clean) * (1.0 + T.reliability_reserve_margin)
        bound = min(floor_mw, th_before) if th_before > 0 else floor_mw
        row.update(
            thermal_after_mw=round(th_after, 3),
            retirement_bounded_floor_mw=round(bound, 3),
            i7_slack_mw=round(th_after - bound, 3),
            i7=("FAIL" if th_after < bound - T.reliability_slack_mw else "PASS"),
            i12_floor=None,
            i12=None,
        )
    return row


def grade(row: dict) -> str:
    """HIT/MISS for one year, on the CUMULATIVE seam error through that year.

    The predictor is cumulative, not per-year, because the mechanism is
    path-dependent: a unit the screens let go in 2022 against a too-low bar is
    gone in 2025 too, and a backstop MW not built is not built. So the position
    error observable in year Y is driven by ``Σ (seam − measured)`` over every
    BINDING year up to and including Y, not by year Y's own delta. (Year Y's own
    delta still sets year Y's bar; the cumulative sum simply dominates it once
    more than one year has run, and grading on the single year would score
    PJM 2025 — whose fleet is 13.4 GW of 2022 under-procurement downstream — off
    its own +2.5 GW row.)

    Args:
        row: A row from :func:`read_year`, carrying ``cum_seam_delta_mw``.

    Returns:
        ``"HIT"``, ``"MISS"``, ``"n/a"`` (no cumulative error yet, or the
        screens have not bound) or ``"UNOBSERVABLE"`` (pre-D52 ledger with no
        committed seam peak).
    """
    if not row.get("d52_ledger"):
        return "UNOBSERVABLE"
    if not row.get("screen_binds"):
        return "n/a (pre-screen)"
    d = row.get("cum_seam_delta_mw")
    if d is None:
        return "UNOBSERVABLE"
    if abs(d) < 1e-6:
        return "n/a"
    short = row.get("i7") == "FAIL" or row.get("i12") == "BELOW"
    long_ = row.get("i12") == "ABOVE"
    if d < 0:  # seam below measured -> screens under-procured -> expect SHORT
        return "HIT" if short else "MISS"
    return "HIT" if (long_ or not short) else "MISS"


def measured_peaks() -> dict[str, dict[int, float]]:
    """Measured hindcast peaks per ISO/year, from the D76 census.

    The BRIDGE year (2022) carries no ``peak_demand_mw`` in its ledger — it
    evolves but never solves — yet its screens DO bind, so its seam delta is
    needed for the cumulative predictor. The census measured it directly off
    the same ``load_demand`` call the LP's hindcast branch makes.

    Returns:
        ``{iso: {year: measured peak MW}}`` for the ``t1h`` recipe.
    """
    census = json.loads(Path("docs/handoffs/d76/peak_census.json").read_text())
    return {
        b["iso"]: {
            int(y): r["measured_peak_mw"]
            for y, r in b["years"].items()
            if r["measured_peak_mw"] is not None
        }
        for b in census["blocks"]
        if b["recipe"] == "t1h"
    }


def main() -> int:
    out = {}
    meas_all = measured_peaks()
    hdr = (f"{'iso':<6} {'yr':>5} {'seam d MW':>11} {'cum d MW':>10} "
           f"{'firm/thermal':>13} {'requirement':>13} {'I7 slack':>11} "
           f"{'I7':>5} {'I12':>8} {'read':>16}")
    print(hdr)
    print("-" * len(hdr))
    for iso, bundle in BUNDLES.items():
        rows, cum, cum_known = {}, 0.0, True
        meas = meas_all.get(iso, {})
        for year, led in sorted(ledgers(iso, bundle).items()):
            # capx D52 ledger field; the screens bind from the window's SECOND
            # year (prior_results guard at runner.py:2125), bridge year included.
            # A pre-D52 ledger carries NO ``screen_*`` keys at all, which is a
            # different thing from a D52 ledger whose first year records that
            # the screens did not bind. Distinguish them, or an ISO whose seam
            # is simply unobservable reads as one whose screens never ran.
            d52_ledger = "screen_peak_demand_mw" in led
            seam = led.get("screen_peak_demand_mw")
            binds = d52_ledger and led.get("screen_adequacy_requirement_mw") is not None
            if not d52_ledger:
                cum_known = False
            m = meas.get(year)
            year_delta = (
                round(float(seam) - float(m), 3)
                if (seam is not None and m is not None)
                else None
            )
            if binds:
                if year_delta is None:
                    cum_known = False
                else:
                    cum += year_delta
            row = read_year(iso, year, led)
            if row is None:  # bridge year: evolved, never solved — nothing to grade
                continue
            row["screen_binds"] = binds
            row["d52_ledger"] = d52_ledger
            row["seam_delta_mw"] = year_delta
            row["cum_seam_delta_mw"] = round(cum, 3) if cum_known else None
            row["reading"] = grade(row)
            rows[year] = row
            firm = row.get("accredited_firm_mw", row.get("thermal_after_mw"))
            req = row.get("requirement_mw", row.get("retirement_bounded_floor_mw"))
            fmt = lambda v: "—" if v is None else f"{v:,.0f}"  # noqa: E731
            print(f"{iso:<6} {year:>5} {fmt(year_delta):>11} "
                  f"{(fmt(cum) if cum_known else '—'):>10} {firm:>13,.0f} "
                  f"{req:>13,.0f} {row['i7_slack_mw']:>11,.0f} {row['i7']:>5} "
                  f"{str(row['i12']):>8} {row['reading']:>16}")
        out[iso] = {"bundle": bundle, "years": rows}
        print()
    Path("docs/handoffs/d76/i7_i12_reading.json").write_text(
        json.dumps(out, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

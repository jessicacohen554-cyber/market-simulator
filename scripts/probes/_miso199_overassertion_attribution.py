"""miso-199 EXTENSION — where the ST_GAS floor's over-assertion ACTUALLY lives.

ZERO-SOLVE. **The rule below is frozen in this docstring and the file is pushed
+ blob-verified BEFORE any adjudicating quantity is computed.** Nothing here is
weighed against a price residual (rule 1 ``[R-STRUCT]``).

===============================================================================
STATUS: THIS PROBE CANNOT REVIVE THIS SESSION'S REFUSED LEVER
===============================================================================
``_miso199_mustrun_window_basis_phase0.json`` already ran its frozen L-2b line
and **REFUTED the charter's premise**: the keeper's over-assertion partitions
0.110 / 0.568 / 0.197 MISPLACEMENT against 0.890 / 0.432 / 0.803 LEVEL, so the
dominant channel is **LEVEL in 2 of 3 years** and the window family is
**REFUSED**. That verdict is final and is NOT re-opened here — L-2b was declared
before any number and is not renegotiated (the miso-172 discipline: "the
mechanical verdict is not reinterpreted").

**This extension is therefore explicitly NON-ADJUDICATING for miso-199's lever.**
It exists because a refusal that does not say WHERE the quantity actually lives
hands the successor nothing. Its outputs are DIAGNOSTIC and feed the successor's
charter only. No result below can make the window family admissible again.

===============================================================================
BASES
===============================================================================
Identical to the census (B1 ``run_year``'s own chain, B2 raw CAMPD through the
frozen deriver's helpers, B3 the committed keeper sidecars), imported verbatim
from ``_miso198_stgas_oom_conduct_phase0`` and re-pointed at the current keeper
``miso198_oom_B`` (``2026-09-01-miso-198-oomlevel``). The C2 level map is built
by ``_miso198_level_selection``'s OWN frozen machinery, imported, never restated
(rule 23 ``[R-FROZEN-DERIVE]``).

===============================================================================
THE FROZEN RULE
===============================================================================

**X-1 ATTRIBUTION OF ``O_mis``.** The census measured a fleet-level ``O_mis`` of
0.076 / 0.397 / 0.116 TWh and a worst-4-month concentration of 0.807 in the
false-positive floor energy. X-1 attributes ``O_mis`` to (plant, year, month)
cells and reports the ranked list.
  * **L-X1a CONCENTRATED** iff the single largest (plant, year, month) cell
    carries >= **0.40** of the three-year ``O_mis`` total. A concentrated
    ``O_mis`` is an EVENT (an outage the floor asserted through), not a
    property of the window RANKING, because a ranking defect is diffuse across
    the year by construction — the load rank has no calendar structure.
  * **L-X1b** for the top cell, the plant's measured availability from the
    outage extract (``unit_outage_derate_factors``, the same source the floor's
    ``pmax x availability`` clip uses) is reported beside its measured net
    output. If availability is HIGH while the meter reads ~0, the cell is the
    named miso-172 "laid up but reads available at PART-YEAR grain" family and
    the successor is an AVAILABILITY-representation repair, NOT a window one.

**INSTRUMENT DEFECT IN X-2, FOUND AFTER THE FIRST NUMBERS WERE READ, DISCLOSED AND
REPAIRED RATHER THAN ABSORBED** (the miso-198 §3 precedent). The first X-2 run patched
``fleet_pkg.thermal_tranche_p25_measured_level``, which is the accessor
``_miso198_level_selection`` patches — correct against THAT session's keeper
(``miso191_bax_B``, ``st_gas_mustrun_oom_level=False``) but WRONG against this one. The
current keeper arms ``st_gas_mustrun_oom_level``, and the runtime then does
``_p25_measured = {**_p25_measured, **_oom_level}`` (arrays.py:2512), so the
out-of-merit map OVERRIDES the patched one on every ST_GAS key and the swap is a no-op.
**The symptom was unmistakable and is recorded here rather than hidden: the "C2"
partition came back BYTE-IDENTICAL to the incumbent's** (raw 9.932/10.386/10.441, O
0.695/0.698/0.590) instead of C2's own published 13.975/15.010/15.185 raw assertion
(FINDING-miso198 §4). X-2 now patches ``thermal_tranche_oom_level`` — the accessor that
actually wins in this keeper — and **asserts the swap took effect before partitioning**
(the raw assertion must move by > 1 % against the incumbent, else the run aborts rather
than reporting a silent no-op as a result). **The frozen L-X2 line below is UNCHANGED**;
only the instrument that feeds it is repaired.

**X-2 WHY THE MEDIAN OVER-ASSERTS — testing miso-198 §4's OWN explanation.**
FINDING-miso198 §4 refused the C2 (p50-over-out-of-merit) level and explained
the refusal thus: *"A statistic that is non-pinning inside its own sample is
placed, at runtime, in a differently selected set of hours. That mismatch —
window basis, not level — is the binding defect."* That is a falsifiable claim
about C2, and the census tested it only on the INCUMBENT floor. X-2 tests it on
C2 itself: rebuild the runtime floor with ONLY the C2 level map swapped in (the
selection probe's own single-delta harness) and partition C2's over-assertion by
the same MIS / LVL identity.
  * **L-X2 §4's EXPLANATION HOLDS** iff C2's over-assertion is MIS-dominant
    (>= **0.45** in >= **2 of 3** years) — i.e. the median really does over-
    assert by landing in hours the plant was not running. **If C2's
    over-assertion is LVL-dominant, §4's stated mechanism is WRONG**: the median
    over-asserts because it exceeds what the plant makes in hours it IS running,
    which is a property of the LEVEL against its own conditioning sample and has
    nothing to do with the window. Either way the C2 candidate stays refused —
    S-iii refused it on the MAGNITUDE of its over-assertion, which X-2 does not
    change and does not re-score.

===============================================================================
Usage
===============================================================================
    python3 scripts/probes/_miso199_overassertion_attribution.py --satisfiability
    python3 scripts/probes/_miso199_overassertion_attribution.py

Record: ``results/calibration/_miso199_overassertion_attribution.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "src"))
sys.path.insert(0, str(_REPO))

import numpy as np  # noqa: E402

import market_sim.data.fleet as fleet_pkg  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402
from scripts.probes import _miso198_level_selection as sel  # noqa: E402
from scripts.probes import _miso198_stgas_oom_conduct_phase0 as ph0  # noqa: E402
from scripts.probes import _miso199_mustrun_window_basis_phase0 as ph0w  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
GROUP = "ST_GAS"

KEEPER = _REPO / "results" / "calibration" / "miso198_oom_B"
RUN_ID = "2026-09-01-miso-198-oomlevel"
ph0.KEEPER = KEEPER
ph0.RUN_ID = RUN_ID

OUT = _REPO / "results" / "calibration" / "_miso199_overassertion_attribution.json"

# ---- frozen ex-ante lines (the docstring is the authority) ------------------
LX1A_CONCENTRATION = 0.40    # largest (plant, year, month) share of 3-yr O_mis
LX2_DOMINANT_SHARE = 0.45
LX2_MIN_YEARS = 2


def partition(floors, net, online) -> tuple[float, float, dict]:
    """(O_mis, O_lvl, per-(plant,month) O_mis MWh) — the census's own identity."""
    mon = ph0w.month_index()
    o_mis = o_lvl = 0.0
    cells: dict[tuple[int, int], float] = {}
    for code, flr in floors.items():
        meas = net.get(code)
        if meas is None:
            meas = np.zeros(HOURS, dtype=float)
        h_meas = online.get(code)
        if h_meas is None:
            h_meas = np.zeros(HOURS, dtype=bool)
        over = np.where(flr > 0.0, np.maximum(0.0, flr - meas), 0.0)
        o_mis += float(over[~h_meas].sum())
        o_lvl += float(over[h_meas].sum())
        mis = np.where(~h_meas, over, 0.0)
        for m in range(1, 13):
            v = float(mis[mon == m].sum())
            if v > 0:
                cells[(int(code), m)] = v
    return o_mis, o_lvl, cells


def run() -> dict:
    rec: dict = {
        "probe": Path(__file__).name,
        "run_id": RUN_ID,
        "keeper_bundle": str(KEEPER.relative_to(_REPO)),
        "status": (
            "NON-ADJUDICATING DIAGNOSTIC. The window family is already REFUSED "
            "by the census's frozen L-2b line; nothing here re-opens it."
        ),
        "frozen_lines": {
            "LX1A_CONCENTRATION": LX1A_CONCENTRATION,
            "LX2_DOMINANT_SHARE": LX2_DOMINANT_SHARE,
            "LX2_MIN_YEARS": LX2_MIN_YEARS,
        },
        "x1": {},
        "x2": {},
    }

    # ---- shared per-year measured/fleet state ------------------------------
    per_year: dict[int, dict] = {}
    for year in YEARS:
        print(f"  [{year}] building B1 fleet + B2 measured …")
        fleet, fa, _ = ph0.build_run_year_fleet(year)
        net, online = ph0.measured_year(year)
        per_year[year] = {
            "floors": ph0.plant_floor_series(fleet, fa),
            "net": net,
            "online": online,
        }

    # -------------------------------------------------------------------- X-1
    all_cells: dict[tuple[int, int, int], float] = {}
    o_mis_by_year: dict[int, float] = {}
    for year in YEARS:
        d = per_year[year]
        o_mis, _o_lvl, cells = partition(d["floors"], d["net"], d["online"])
        o_mis_by_year[year] = o_mis
        for (code, m), v in cells.items():
            all_cells[(code, year, m)] = v
    total_mis = sum(o_mis_by_year.values())
    ranked = sorted(all_cells.items(), key=lambda kv: -kv[1])
    rec["x1"] = {
        "O_mis_by_year_twh": {y: round(v / 1e6, 4) for y, v in o_mis_by_year.items()},
        "O_mis_total_twh": round(total_mis / 1e6, 4),
        "top_cells": [
            {
                "plant_code": c, "year": y, "month": m,
                "O_mis_gwh": round(v / 1e3, 1),
                "share_of_3y_O_mis": round(v / total_mis, 4) if total_mis > 0 else None,
            }
            for (c, y, m), v in ranked[:12]
        ],
    }
    top_share = (ranked[0][1] / total_mis) if (ranked and total_mis > 0) else 0.0
    rec["x1"]["LX1a_top_cell_share"] = round(top_share, 4)
    rec["x1"]["LX1a_concentrated"] = bool(top_share >= LX1A_CONCENTRATION)
    rec["x1"]["LX1a_verdict"] = (
        "CONCENTRATED — the misplacement is an EVENT in one (plant, year, month) "
        "cell, not a property of the window RANKING (a ranking defect is diffuse "
        "by construction: the system-load rank carries no calendar structure)."
        if top_share >= LX1A_CONCENTRATION
        else "DIFFUSE — no single cell carries the misplacement."
    )

    # ---- L-X1b: availability vs meter in the top cell ----------------------
    if ranked:
        (tc, ty, tm) = ranked[0][0]
        mon = ph0w.month_index()
        sel_m = mon == tm
        d = per_year[ty]
        cap, primary = dtt._fleet_nameplate_and_group(ISO)
        grp = primary.get(int(tc))
        npl = float(cap.get((int(tc), grp), 0.0)) if grp else 0.0
        derate = unit_outage_derate_factors(ty, iso=ISO)
        mult = np.asarray(derate.get((int(tc), grp), np.ones(HOURS)), dtype=float)
        meas = d["net"].get(tc, np.zeros(HOURS))
        flr = d["floors"].get(tc, np.zeros(HOURS))
        onl = d["online"].get(tc, np.zeros(HOURS, dtype=bool))
        rec["x1"]["LX1b_top_cell"] = {
            "plant_code": tc, "year": ty, "month": tm,
            "plant_group": grp,
            "nameplate_mw": round(npl, 1),
            "mean_outage_availability": round(float(mult[sel_m].mean()), 4),
            "mean_measured_net_mw": round(float(meas[sel_m].mean()), 1),
            "measured_online_hours_in_month": int(onl[sel_m].sum()),
            "hours_in_month": int(sel_m.sum()),
            "mean_floor_mw": round(float(flr[sel_m].mean()), 1),
            "O_mis_gwh": round(ranked[0][1] / 1e3, 1),
        }
        b = rec["x1"]["LX1b_top_cell"]
        rec["x1"]["LX1b_verdict"] = (
            "AVAILABILITY-REPRESENTATION DEFECT — the outage extract reads the "
            "plant AVAILABLE while its own meter reads ~0, so the pmax x "
            "availability clip never relaxes the floor. This is the named "
            "miso-172 'laid up but reads available' family at PART-YEAR grain. "
            "The successor is an AVAILABILITY repair, NOT a window one."
            if b["mean_outage_availability"] >= 0.50
            and b["measured_online_hours_in_month"] <= 0.25 * b["hours_in_month"]
            else "NOT the availability family on this cell's evidence."
        )

    # -------------------------------------------------------------------- X-2
    print("  building the C2 (p50-over-out-of-merit) level map …")
    allon, oomon = sel.measured_samples()
    cands = sel.candidate_levels(allon, oomon)
    c2 = cands["C2"]
    # THE REPAIRED SLOT (see the docstring's instrument-defect note): this
    # keeper arms st_gas_mustrun_oom_level, and arrays.py:2512 merges the
    # out-of-merit map OVER the measured-level map, so the accessor that must
    # be patched is thermal_tranche_oom_level — patching the p25_measured one
    # is a silent no-op here.
    orig = fleet_pkg.thermal_tranche_oom_level
    patched = {(int(c), GROUP): float(v) for c, v in c2.items()}

    def _patched(iso: str):  # noqa: ANN202 - runtime accessor shim
        base = dict(orig(iso))
        base.update(patched)
        return base

    fleet_pkg.thermal_tranche_oom_level = _patched
    try:
        by_year: dict[int, dict] = {}
        for year in YEARS:
            print(f"  [{year}] rebuilding the floor under C2 …")
            fleet, fa, _ = ph0.build_run_year_fleet(year)
            floors = ph0.plant_floor_series(fleet, fa)
            d = per_year[year]
            o_mis, o_lvl, _ = partition(floors, d["net"], d["online"])
            raw = sum(float(v.sum()) for v in floors.values())
            O = o_mis + o_lvl
            by_year[year] = {
                "raw_assertion_twh": round(raw / 1e6, 4),
                "O_overassertion_twh": round(O / 1e6, 4),
                "over_share": round(O / raw, 4) if raw > 0 else None,
                "O_mis_twh": round(o_mis / 1e6, 4),
                "O_lvl_twh": round(o_lvl / 1e6, 4),
                "shares": {
                    "MIS": round(o_mis / O, 4) if O > 0 else None,
                    "LVL": round(o_lvl / O, 4) if O > 0 else None,
                },
            }
    finally:
        fleet_pkg.thermal_tranche_oom_level = orig

    # LIVENESS ASSERTION (the repair's own regression test): a swap that did
    # not take effect must ABORT, never be reported as a partition. The
    # incumbent raw assertions are the census's own published figures.
    incumbent_raw = {2023: 9.9319, 2024: 10.3857, 2025: 10.4408}
    moved = {
        y: abs(by_year[y]["raw_assertion_twh"] - incumbent_raw[y]) / incumbent_raw[y]
        for y in YEARS
    }
    if not all(v > 0.01 for v in moved.values()):
        raise SystemExit(
            "X-2 ABORT: the C2 level swap did not take effect (raw assertion "
            f"moved {moved} against the incumbent). Reporting this partition "
            "would restate the incumbent's numbers as C2's — the exact defect "
            "the docstring's instrument note records."
        )

    dom = {"MIS": 0, "LVL": 0}
    for year in YEARS:
        sh = by_year[year]["shares"]
        for ch in dom:
            if sh[ch] is not None and sh[ch] >= LX2_DOMINANT_SHARE:
                dom[ch] += 1
    winners = [c for c, n in dom.items() if n >= LX2_MIN_YEARS]
    channel = winners[0] if len(winners) == 1 else None
    rec["x2"] = {
        "candidate": "C2 (p50 over out-of-merit online hours) — the level "
                     "FINDING-miso198 §4 refused",
        "swap_liveness_rel_move_vs_incumbent": {y: round(v, 4) for y, v in moved.items()},
        "swap_slot": "thermal_tranche_oom_level (REPAIRED — see the docstring's "
                     "instrument-defect note; the p25_measured slot is a silent "
                     "no-op against a keeper arming st_gas_mustrun_oom_level)",
        "by_year": by_year,
        "dominant_channel": channel,
        "years_over_line": dom,
        "LX2_section4_explanation_holds": bool(channel == "MIS"),
        "LX2_verdict": (
            "§4's EXPLANATION HOLDS — C2's over-assertion is MISPLACEMENT."
            if channel == "MIS"
            else (
                "§4's STATED MECHANISM IS WRONG. C2's over-assertion is a LEVEL "
                "effect: the median exceeds what the plant makes in hours it IS "
                "running. It is a property of the level against its own "
                "conditioning sample and has nothing to do with the window. C2 "
                "STAYS REFUSED — S-iii refused it on the MAGNITUDE of its "
                "over-assertion, which this measurement does not change."
                if channel == "LVL"
                else "DISPERSED — neither channel dominates C2's over-assertion."
            )
        ),
    }
    return rec


def satisfiability() -> None:
    """Verify the machinery — NO adjudicating quantity computed."""
    print("SATISFIABILITY (no adjudicating quantity computed)")
    census = _REPO / "results" / "calibration" / (
        "_miso199_mustrun_window_basis_phase0.json"
    )
    assert census.exists(), "premise: the census this extension subordinates to has run"
    c = json.loads(census.read_text())
    print(f"  census L-2b premise_holds = {c['n2']['L2b_premise_holds']}")
    assert c["n2"]["L2b_premise_holds"] is False, (
        "premise: this extension only exists on a REFUTED census"
    )
    orig = fleet_pkg.thermal_tranche_p25_measured_level
    base = orig(ISO)
    keys = [k for k in base if k[1] == GROUP]
    print(f"  runtime accessor resolves {len(keys)} ST_GAS level key(s)")
    assert keys, "premise: the level accessor is reachable"
    mon = ph0w.month_index()
    assert mon.shape == (HOURS,) and mon[0] == 1 and mon[-1] == 12
    print(f"  month index OK ({int((mon == 2).sum())} February hours)")
    print("SATISFIABLE — the attribution and the C2 swap are both reachable.")


def main() -> None:
    ap = argparse.ArgumentParser(description="miso-199 over-assertion attribution")
    ap.add_argument("--satisfiability", action="store_true")
    args = ap.parse_args()
    if args.satisfiability:
        satisfiability()
        return
    rec = run()
    OUT.write_text(json.dumps(rec, indent=1, default=str))
    print(f"\nwrote {OUT.relative_to(_REPO)}")
    print("\n== X-1 attribution of O_mis (top cells) ==")
    for c in rec["x1"]["top_cells"][:8]:
        print(
            f"  plant {c['plant_code']:>6}  {c['year']}-{c['month']:02d}  "
            f"{c['O_mis_gwh']:8.1f} GWh  share {c['share_of_3y_O_mis']}"
        )
    print(f"  L-X1a top-cell share {rec['x1']['LX1a_top_cell_share']} -> "
          f"{rec['x1']['LX1a_verdict']}")
    if "LX1b_top_cell" in rec["x1"]:
        print(f"  L-X1b {json.dumps(rec['x1']['LX1b_top_cell'])}")
        print(f"  L-X1b {rec['x1']['LX1b_verdict']}")
    print("\n== X-2 C2's own over-assertion partition ==")
    for y in YEARS:
        b = rec["x2"]["by_year"][y]
        print(
            f"  {y}: raw {b['raw_assertion_twh']:7.3f}  O {b['O_overassertion_twh']:6.3f}"
            f" ({b['over_share']:.3f})   MIS {b['O_mis_twh']:6.3f} ({b['shares']['MIS']:.3f})"
            f"   LVL {b['O_lvl_twh']:6.3f} ({b['shares']['LVL']:.3f})"
        )
    print(f"  L-X2 {rec['x2']['LX2_verdict']}")


if __name__ == "__main__":
    main()

"""nyiso-191 PHASE 0 (NO LP) — what a class-widened ``cc_capacity_reconcile`` derive would admit.

Replicates :mod:`scripts.data.derive_cc_capacity_reconcile`'s population rule
EXACTLY — the same demonstrated-peak authority (CAMPD p99.9 net), the same
``_CAP_MARGIN``, ``_MIN_DELTA``, ``_PURE_PLAY_CC_SHARE``, ``_CT_ONLY_RATIO`` and
``_CAP_FEASIBLE_CF`` constants imported from it, the same un-guarded model-capacity
basis and the same summer-derate rescale — with ONE difference: the screened class
set is a parameter instead of the hard-coded ``"CC_REGULAR"``.

Run BEFORE the derive is edited and BEFORE any solve, so the pre-registration can
state which plants the widened rule reaches and which its own guards decline. No
constant is added, moved or retuned; every threshold is the frozen one (rule 23).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_cc_capacity_reconcile import (  # noqa: E402
    _CAP_FEASIBLE_CF,
    _CAP_MARGIN,
    _CC_NET_OF_GROSS,
    _CT_ONLY_RATIO,
    _MIN_DELTA,
    _PURE_PLAY_CC_SHARE,
    _campd_p999_and_annual,
    _ct_only_codes,
)

ISO = "NYISO"
YEARS = [2023, 2024, 2025]
SUMMER_DERATE_ISOS = ("PJM", "NYISO", "NEISO", "CAISO")
# The two class sets under comparison: what ships today, and the widening.
CURRENT_CLASSES = ("CC_REGULAR",)
WIDENED_CLASSES = ("CC_REGULAR", "CC_CHP")


def model_capacity(iso: str, year: int, classes: tuple[str, ...]) -> dict:
    """The derive's ``_model_cc_capacity``, with the class set parameterised."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import cc_summer_derate_ratio, load_fleet_from_csv

    gens = load_fleet_from_csv(
        iso, get_iso_config(iso), year=year, apply_cc_summer_guard=False
    )
    plant_cap: dict[int, float] = {}
    cc_cap: dict[int, float] = {}
    names: dict[int, str] = {}
    groups: dict[int, str] = {}
    for g in gens:
        pc = int(g.plant_code)
        if pc <= 0:
            continue
        plant_cap[pc] = plant_cap.get(pc, 0.0) + float(g.pmax_mw)
        if g.plant_group in classes:
            cc_cap[pc] = cc_cap.get(pc, 0.0) + float(g.pmax_mw)
            names[pc] = g.name
            groups[pc] = g.plant_group
    out: dict[int, dict] = {}
    for pc, cap in cc_cap.items():
        share = cap / plant_cap[pc]
        rescaled = cap
        ratio = None
        if iso.upper() in SUMMER_DERATE_ISOS:
            ratio = cc_summer_derate_ratio(pc)
            if ratio is not None and ratio > 0.0:
                rescaled = cap / ratio
        out[pc] = {
            "name": names[pc],
            "group": groups[pc],
            "cap_mw": rescaled,
            "pure_play_share": share,
            "summer_derate_ratio": ratio,
            "pure_play_ok": share >= _PURE_PLAY_CC_SHARE,
        }
    return out


def screen(plants: dict, p999: pd.Series, annual, ct_only: set[int]) -> list[dict]:
    """The derive's --mode both row decision, verdict recorded for every plant."""
    rows = []
    for code, info in sorted(plants.items()):
        cur = float(info["cap_mw"])
        peak = float(p999.get(code, np.nan))
        rec = {
            "plant_code": code,
            "plant_name": info["name"],
            "plant_group": info["group"],
            "current_mw": round(cur, 1),
            "campd_p999_mw": (round(peak, 1) if np.isfinite(peak) else None),
            "pure_play_share": round(info["pure_play_share"], 3),
        }
        if not info["pure_play_ok"]:
            rec["verdict"] = "SKIP: not pure-play"
            rows.append(rec)
            continue
        if not np.isfinite(peak) or peak <= 0.0 or cur <= 0.0:
            rec["verdict"] = "SKIP: no CAMPD peak"
            rows.append(rec)
            continue
        if code in ct_only:
            rec["verdict"] = "SKIP: CT-only CEMS reporter (frozen guard)"
            rows.append(rec)
            continue
        if cur > _CAP_MARGIN * peak:
            implied = max(
                (float(annual.get((code, y), 0.0)) / (peak * 8760.0) for y in YEARS),
                default=0.0,
            )
            rec["implied_cf_at_peak"] = round(implied, 3)
            if implied > _CAP_FEASIBLE_CF:
                rec["verdict"] = "SKIP: CF-infeasible cap (frozen guard)"
            else:
                rec["verdict"] = "CAP"
                rec["reconciled_mw"] = round(peak, 1)
                rec["delta_pct"] = round(100 * (peak - cur) / cur, 1)
        elif cur < peak * (1.0 - _MIN_DELTA):
            if peak > _CAP_MARGIN * cur:
                rec["verdict"] = "SKIP: peak >margin above model (artifact)"
            else:
                rec["verdict"] = "RAISE"
                rec["reconciled_mw"] = round(peak, 1)
                rec["delta_pct"] = round(100 * (peak - cur) / cur, 1)
        else:
            rec["verdict"] = "no row (within margin)"
        rows.append(rec)
    return rows


def main() -> int:
    cur_plants = model_capacity(ISO, max(YEARS), CURRENT_CLASSES)
    wide_plants = model_capacity(ISO, max(YEARS), WIDENED_CLASSES)
    p999, campd_annual = _campd_p999_and_annual(ISO, set(wide_plants), YEARS)

    from market_sim.data.eia923 import load_monthly_generation

    gen = load_monthly_generation()
    gen = gen[gen["year"].isin(YEARS)]
    annual = gen.groupby(["plant_id", "year"])["netgen_annual_mwh"].sum()
    ct_only = _ct_only_codes(campd_annual, gen.groupby("plant_id")["netgen_annual_mwh"].sum())

    cur_rows = screen(cur_plants, p999, annual, ct_only)
    wide_rows = screen(wide_plants, p999, annual, ct_only)
    cur_codes = {r["plant_code"] for r in cur_rows if r["verdict"] in ("CAP", "RAISE")}
    wide_codes = {r["plant_code"] for r in wide_rows if r["verdict"] in ("CAP", "RAISE")}

    rec = {
        "session": "nyiso-191",
        "phase": "0 — NO LP, population rule only",
        "iso": ISO,
        "years": YEARS,
        "constants_frozen": {
            "_CAP_MARGIN": _CAP_MARGIN,
            "_MIN_DELTA": _MIN_DELTA,
            "_PURE_PLAY_CC_SHARE": _PURE_PLAY_CC_SHARE,
            "_CT_ONLY_RATIO": _CT_ONLY_RATIO,
            "_CAP_FEASIBLE_CF": _CAP_FEASIBLE_CF,
            "_CC_NET_OF_GROSS": _CC_NET_OF_GROSS,
        },
        "current_classes": list(CURRENT_CLASSES),
        "widened_classes": list(WIDENED_CLASSES),
        "n_rows_current": len(cur_codes),
        "n_rows_widened": len(wide_codes),
        "new_rows": sorted(wide_codes - cur_codes),
        "lost_rows": sorted(cur_codes - wide_codes),
        "ct_only_declined": sorted(ct_only & set(wide_plants)),
        "current_screen": cur_rows,
        "widened_screen": wide_rows,
    }
    out = REPO / "results/calibration/_nyiso191_ccchp_scope_phase0.json"
    out.write_text(json.dumps(rec, indent=2, default=str))

    print(f"rows today (CC_REGULAR only): {len(cur_codes)}   widened: {len(wide_codes)}")
    print(f"NEW rows: {rec['new_rows']}    LOST rows: {rec['lost_rows']}")
    print()
    print(f"{'code':8}{'name':34}{'grp':11}{'cur':>8}{'p999':>8}{'verdict':>44}")
    for r in wide_rows:
        if r["plant_group"] != "CC_CHP":
            continue
        print(
            f"{r['plant_code']:<8}{r['plant_name'][:33]:34}{r['plant_group']:11}"
            f"{r['current_mw']:8.1f}"
            f"{(r['campd_p999_mw'] if r['campd_p999_mw'] is not None else float('nan')):8.1f}"
            f"{r['verdict']:>44}"
            + (f"  -> {r.get('reconciled_mw')} MW ({r.get('delta_pct')}%)" if "reconciled_mw" in r else "")
        )
    print(f"\nwrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

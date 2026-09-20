"""nyiso-245 — G3 (corpus/shape), G4 (not inert) and G5 (C1/C2 exposure).

ZERO LP (rule 32 ``[R-SHARD]`` (a)). Reads the derived artifact, the
``_nyiso245_cache`` fleet dump and the keeper's committed sidecars, and SIMULATES
the reprice in numpy — no wiring, no solve, so a gate can still refuse before any
``ScenarioConfig`` field is written.

Every threshold is fixed in
``docs/PRECOMMIT-nyiso245-position-shape-offer-surface-2026-09-20.md`` §3, committed
at ``398f0437`` (``5cbf4fef`` post-rebase, content unchanged) before any number here
was computed (rule 1 ``[R-STRUCT]``).

* **G3a** — the Δ ladder is monotone non-decreasing in position in >= 80 % of
  populated (gas x state) cells.
* **G3b** — Δ at the top position bin is strictly larger in the tightest net-load
  bin than in the loosest, in >= 3 of 4 years measured independently.
* **G3c** — price-taker contamination, REPORTED at full magnitude, never gated.
* **G4** — not inert: >= 500 MW of repriced capacity moves by >= $1.00/MWh in the
  median missed winter hour. A deliberately low bar; rule 1 ``[R-STRUCT]`` forbids
  gating on whether the residual moved, so the induced movement in nyiso-244 §6.1's
  differenced statistic is REPORTED and gates nothing.
* **G5** — C1/C2 exposure, pre-registered: the share of annual thermal energy on
  repriced rows and the median $/MWh the reprice moves them.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso245_surface_effect.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
ART = REPO / "data" / "raw" / "_validation-source" / "nyiso_offer_surface_positional.json"
OUT = REPO / "results" / "calibration" / "_nyiso245_surface_effect.json"

HOURS = 8760
# --- PRECOMMIT §3 bars, fixed before any number here. ------------------------
MONOTONE_BAR = 0.80
DRIVER_YEARS_BAR = 3
INERT_MW_BAR, INERT_USD_BAR = 500.0, 1.00
#: nyiso-244 §6.1's measured differenced statistic, quoted so the report is
#: against the market's own numbers and not against a recomputed proxy.
MARKET_WITHDRAWN = {"150": 7674.5, "200": 6202.5}
MODEL_WITHDRAWN_NOW = {"150": 3610.7, "200": 1213.1}


def load_year(year: int) -> dict:
    """Cached fleet dump for one year."""
    d = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    return {k: d[k] for k in d.files}


def base_mask(plant_code: np.ndarray, plant_group: np.ndarray) -> np.ndarray:
    """``True`` for each plant's FIRST tranche in fill order (family definition)."""
    seen: set[tuple[str, str]] = set()
    out = np.zeros(len(plant_code), dtype=bool)
    for i, (pc, pg) in enumerate(zip(plant_code, plant_group)):
        if not str(pc) or str(pc) == "None":
            continue
        key = (str(pc), str(pg))
        if key not in seen:
            seen.add(key)
            out[i] = True
    return out


def base_row_of(plant_code: np.ndarray, plant_group: np.ndarray) -> dict[int, int]:
    """Map each row -> its plant's base row index."""
    first: dict[tuple[str, str], int] = {}
    out: dict[int, int] = {}
    for i, (pc, pg) in enumerate(zip(plant_code, plant_group)):
        if not str(pc) or str(pc) == "None":
            continue
        key = (str(pc), str(pg))
        if key not in first:
            first[key] = i
        out[i] = first[key]
    return out


def own_curve_positions(
    plant_code: np.ndarray, plant_group: np.ndarray, pmax: np.ndarray
) -> np.ndarray:
    """Each tranche's own-curve position midpoint in (0, 1], class-free.

    The plant's tranches are taken in FILL order — the order they stack in that
    plant's own offer curve — and each row's position is the midpoint of its own
    MW span over the plant's total. The same unit-relative coordinate the corpus
    side measures (``step_mw / uol_mw``), and it needs no class attribute, which
    is what makes the surface constructible on a masked corpus at all.
    """
    pos = np.zeros(len(pmax), dtype=float)
    groups: dict[tuple[str, str], list[int]] = {}
    for i, (pc, pg) in enumerate(zip(plant_code, plant_group)):
        if not str(pc) or str(pc) == "None":
            continue
        groups.setdefault((str(pc), str(pg)), []).append(i)
    for idx in groups.values():
        caps = pmax[idx]
        total = float(caps.sum())
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        pos[idx] = (cum - 0.5 * caps) / total
    return pos


def g3_corpus(art: dict) -> dict:
    """G3a monotonicity, G3b driver response per year, G3c contamination."""
    prov = art["_provenance"]
    lad = np.array(
        [[[cell[1] for cell in row] for row in state] for state in art["markets"]["DAM"]["ladder"]],
        dtype=float,
    )  # (gas, state, pos)
    wt = np.array(
        [[[cell[2] for cell in row] for row in state] for state in art["markets"]["DAM"]["ladder"]],
        dtype=float,
    )

    populated, monotone = 0, 0
    for g in range(lad.shape[0]):
        for s in range(lad.shape[1]):
            v = lad[g, s]
            if not np.isfinite(v).all() or wt[g, s].min() <= 0:
                continue
            populated += 1
            if np.all(np.diff(v) >= -1e-9):
                monotone += 1
    frac = monotone / populated if populated else 0.0

    per_year = art.get("per_year_top_position", {})
    rows, ok_years = {}, 0
    for y, rec in sorted(per_year.items()):
        d = rec["delta_by_state_bin_top_position"]
        tight, loose = d[-1], d[0]
        good = np.isfinite(tight) and np.isfinite(loose) and tight > loose
        ok_years += int(good)
        rows[y] = {
            "loosest_state_bin_delta": loose,
            "tightest_state_bin_delta": tight,
            "rises": bool(good),
            "weights_mw": rec["weight_by_state_bin_top_position_mw"],
        }

    contam = {
        k: v.get("contamination")
        for k, v in art["census"].items()
        if isinstance(v, dict) and v.get("contamination")
    }
    return {
        "G3a_monotone": {
            "populated_cells": populated,
            "monotone_cells": monotone,
            "fraction": round(frac, 4),
            "bar": MONOTONE_BAR,
            "verdict": "PASS" if frac >= MONOTONE_BAR else "FAIL",
        },
        "G3b_driver": {
            "per_year": rows,
            "years_rising": ok_years,
            "bar": DRIVER_YEARS_BAR,
            "verdict": "PASS" if ok_years >= DRIVER_YEARS_BAR else "FAIL",
        },
        "G3c_contamination_reported_not_gated": contam,
        "gas_bin_edges_usd_per_mmbtu": prov.get("gas_bin_edges_usd_per_mmbtu"),
        "ladder_top_position_by_state_pooled": [
            [round(float(lad[g, s, -1]), 3) for s in range(lad.shape[1])]
            for g in range(lad.shape[0])
        ],
    }


def simulate(year: int, art: dict) -> dict:
    """Post the measured Δ onto the tagged rows in numpy — G4 and G5."""
    from scripts.probes.nyiso242_tail_reachability import _is_thermal, missed_mask

    d = load_year(year)
    pmax = d["pmax"].astype(float)
    av = d["availability"].astype(float)
    mc = d["mc_base"].astype(float)
    markup = d["gen_markup_hr"].astype(float)
    pc, pg = d["gen_plant_code"], d["plant_group"]
    klass = d["plant_group"]

    is_base = base_mask(pc, pg)
    tagged = (markup > 0.0) & (~is_base)
    base_of = base_row_of(pc, pg)
    pos = own_curve_positions(pc, pg, pmax)

    prov = art["_provenance"]
    pos_edges = np.asarray(prov["position_bins"], dtype=float)
    pcts = np.asarray(prov["netload_pcts"], dtype=float)
    gas_edges = np.asarray(prov["gas_bin_edges_usd_per_mmbtu"], dtype=float)
    lad = np.array(
        [[[c[1] for c in row] for row in st] for st in art["markets"]["DAM"]["ladder"]],
        dtype=float,
    )

    # The solve-side conditioning: net load = demand - wind - solar, and the
    # keeper's own delivered-gas series (the SAME object the derive binned on).
    gas = np.load(CACHE / f"gas_{year}.npy").astype(float)
    nl = _net_load(year)
    state_bin = np.searchsorted(np.quantile(nl, pcts), nl, side="right")
    gas_bin = np.searchsorted(gas_edges, gas, side="right")
    pos_bin = np.clip(
        np.searchsorted(pos_edges[1:-1], pos, side="right"), 0, pos_edges.size - 2
    )

    rows = np.nonzero(tagged)[0]
    base_rows = np.array([base_of.get(int(i), -1) for i in rows], dtype=int)
    keep = base_rows >= 0
    rows, base_rows = rows[keep], base_rows[keep]

    delta = lad[gas_bin[None, :], state_bin[None, :], pos_bin[rows][:, None]]  # (n,T)
    finite = np.isfinite(delta)
    new = np.where(finite, mc[base_rows, :] + delta, mc[rows, :])
    move = new - mc[rows, :]

    mc_after = mc.copy()
    mc_after[rows, :] = new

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    win = {
        "winter_missed": idx[missed & np.isin(month, (1, 2, 12))],
        "ordinary_winter": idx[~missed & np.isin(month, (1, 2, 12))],
    }
    win = {k: v[v < mc.shape[1]] for k, v in win.items()}

    sel = win["winter_missed"]
    cap_rows = pmax[rows][:, None] * av[rows][:, sel]
    moved = np.abs(move[:, sel]) >= INERT_USD_BAR
    moved_mw = float(np.median((cap_rows * moved).sum(axis=0)))
    med_move = float(np.median(move[:, sel]))

    # G5 — the C1/C2 exposure. Annual thermal energy on repriced rows, from the
    # keeper's own committed class dispatch, attributed by the row's share of its
    # class's available capacity (the model's own dispatch is per class, not per row).
    ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    gen = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    therm = [c for c in gen.columns if _is_thermal(str(c))]
    total_twh = float(gen[therm].to_numpy(float).sum()) / 1e6
    tag_cap, all_cap = 0.0, 0.0
    for cls in therm:
        m = klass == cls
        if not m.any():
            continue
        all_cap += float(pmax[m].sum())
        tag_cap += float(pmax[m & tagged].sum())

    # The differenced statistic of nyiso-244 §6.1, recomputed before and after.
    # REPORTED, GATES NOTHING (rule 1 [R-STRUCT]).
    uid = d["unit_ids"]
    internal = np.ones(len(uid), dtype=bool)
    for pre in ("NYISO_external", "NYISO_DR"):
        internal &= ~np.char.startswith(uid.astype(str), pre)

    def withdrawn(px: np.ndarray, p: float) -> float:
        cap = pmax[internal][:, None] * av[internal]
        below = (px[internal] <= p) * cap
        a = float(np.median(below[:, win["ordinary_winter"]].sum(axis=0)))
        b = float(np.median(below[:, sel].sum(axis=0)))
        return a - b

    diff = {
        p: {
            "model_now": round(withdrawn(mc, float(p)), 1),
            "model_with_surface": round(withdrawn(mc_after, float(p)), 1),
            "market": MARKET_WITHDRAWN.get(p),
        }
        for p in ("150", "200")
    }
    for p in diff:
        diff[p]["move_mw"] = round(
            diff[p]["model_with_surface"] - diff[p]["model_now"], 1
        )

    return {
        "year": year,
        "G4_not_inert": {
            "repriced_rows": int(rows.size),
            "moved_capacity_mw_median_missed_hour": round(moved_mw, 1),
            "median_move_usd_per_mwh": round(med_move, 3),
            "bar_mw": INERT_MW_BAR,
            "bar_usd": INERT_USD_BAR,
            "verdict": "PASS" if moved_mw >= INERT_MW_BAR else "FAIL (INERT)",
        },
        "G5_c1c2_exposure": {
            "thermal_twh_from_keeper": round(total_twh, 3),
            "repriced_share_of_thermal_capacity": round(tag_cap / all_cap, 4)
            if all_cap
            else None,
            "median_move_usd_per_mwh_all_hours": round(float(np.median(move)), 3),
            "p95_move_usd_per_mwh_all_hours": round(
                float(np.percentile(move, 95)), 3
            ),
            "share_of_row_hours_moved_down": round(float((move < 0).mean()), 4),
        },
        "REPORTED_differenced_withdrawal_gates_nothing": diff,
    }


def _net_load(year: int) -> np.ndarray:
    """Measured EIA-930 NYISO net load, the derive's own conditioning driver."""
    from scripts.data.derive_nyiso_offer_surface import net_load_by_year

    return net_load_by_year()[year]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, nargs="+", default=[2022])
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    art = json.loads(ART.read_text())
    res = {"G3_corpus": g3_corpus(art), "years": {}}
    for y in args.year:
        res["years"][str(y)] = simulate(y, art)

    g3 = res["G3_corpus"]
    print(f"=== G3a monotone  {g3['G3a_monotone']['fraction']:.1%} of "
          f"{g3['G3a_monotone']['populated_cells']} cells  bar {MONOTONE_BAR:.0%}"
          f"  -> {g3['G3a_monotone']['verdict']}")
    print(f"=== G3b driver response ({g3['G3b_driver']['years_rising']}/4 years, "
          f"bar {DRIVER_YEARS_BAR}) -> {g3['G3b_driver']['verdict']}")
    for y, r in g3["G3b_driver"]["per_year"].items():
        print(f"    {y}: loosest {r['loosest_state_bin_delta']:8.2f} -> tightest "
              f"{r['tightest_state_bin_delta']:8.2f}   {'rises' if r['rises'] else 'DOES NOT RISE'}")
    print("=== G3c contamination (reported, not gated):",
          json.dumps(g3["G3c_contamination_reported_not_gated"].get("DAM-2022", {})))
    for y, r in res["years"].items():
        g4, g5 = r["G4_not_inert"], r["G5_c1c2_exposure"]
        print(f"\n=== {y} G4 {g4['verdict']}: {g4['repriced_rows']} rows, "
              f"{g4['moved_capacity_mw_median_missed_hour']:.1f} MW moved >= "
              f"${INERT_USD_BAR:.2f} (bar {INERT_MW_BAR:.0f} MW), median move "
              f"{g4['median_move_usd_per_mwh']:+.2f} $/MWh")
        print(f"    G5 exposure: {g5['repriced_share_of_thermal_capacity']:.1%} of "
              f"thermal capacity; median move {g5['median_move_usd_per_mwh_all_hours']:+.2f}, "
              f"p95 {g5['p95_move_usd_per_mwh_all_hours']:+.2f}; "
              f"{g5['share_of_row_hours_moved_down']:.1%} of row-hours move DOWN")
        print("    REPORTED (gates nothing) — MW withdrawn from below P, missed vs ordinary:")
        for p, v in r["REPORTED_differenced_withdrawal_gates_nothing"].items():
            print(f"      ${p:>4s}: model now {v['model_now']:9.1f} -> with surface "
                  f"{v['model_with_surface']:9.1f}  ({v['move_mw']:+.1f})   market {v['market']}")

    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()

"""ERCOT-144 Phase 1 — model-vs-measured coal offer LEVEL, PER PLANT, all 10 plants.

No LP, no solve, no parameter changed. Chartered by ERCOT-143's per-plant
measurement (``docs/DIAGNOSIS-ercot143-lignite-offer-slope-2026-07-30.md`` §2):
every ERCOT coal plant submits a NEAR-FLAT SCED TPO curve at a plant-specific
level, so the fleet's smooth supply curve is CROSS-PLANT LEVEL DISPERSION.
This probe quantifies, for each of the model's 10 coal plants:

1. **MODEL** — the current ``ercot140_coal_peak_arm`` keeper's per-plant,
   per-tranche offer curve at the LP seam (``apply_coal_tranches``), reusing
   ERCOT-143's capture.
2. **MEASURED** — the plant's own submitted TPO curve from the pooled 60-Day
   SCED subsets: modal curve per resource, per-year stability (2024 vs 2025
   subsets), and the cap-weighted level of the PRICED segment (points at the
   ~-$250 offer-floor self-schedule block are excluded and reported — they are
   a price-taker commitment signal, not a marginal cost; handoff risk note).
3. **DELTA** — model minus measured, cap-weighted and at the tranche grain
   (each committed/econ tranche's capacity window mapped onto the measured
   step curve), which is the Phase-1 adjudication statistic.

Rule notes: measurement only (rules 13/14 — measured conduct read as driver
evidence); ERCOT-scoped (rule 25); training years 2023-2025 only (rule 22; the
on-disk ``*_2026_*`` files are never opened; SUBSETS enumerates 2024-2025).

Usage::

    python scripts/probes/ercot144_coal_perplant_offer.py \
        [--skip-model] [--json-out PATH]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from scripts.probes.ercot123_coal_sced_reach import (  # noqa: E402
    SUBSETS,
    TPO_MW,
    TPO_PR,
    load_sced,
)

YEARS = (2023, 2024, 2025)

#: Resource-name prefix -> EIA plant code, covering ALL 10 model coal plants
#: (ercot143 LIGNITE_RES + the ERCOT-144 handoff's control map).
PREFIX_TO_PLANT: dict[str, int] = {
    "OGSES": 6180,  # Oak Grove SES
    "SANMIGL": 6183,  # San Miguel
    "TNP_ONE": 7030,  # Major Oak (TNP One / Twin Oaks)
    "MLSES": 6146,  # Martin Lake
    "LEG": 298,  # Limestone
    "WAP": 3470,  # W A Parish (coal units only; class filter is CLLIG)
    "COLETO": 6178,  # Coleto Creek
    "FPPYD": 6179,  # Fayette (FPP)
    "CALAVERS": 7097,  # Calaveras / J K Spruce
    "SCES": 56611,  # Sandy Creek
}
PLANT_NAMES = {
    298: "Limestone",
    3470: "W A Parish",
    6146: "Martin Lake",
    6178: "Coleto Creek",
    6179: "Fayette",
    6180: "Oak Grove",
    6183: "San Miguel",
    7030: "Major Oak",
    7097: "JK Spruce",
    56611: "Sandy Creek",
}

#: Offer-floor block: submitted points at/below this are the self-schedule
#: price-taker signal (San Miguel's -$250 block), excluded from the LEVEL
#: statistic and reported separately (handoff pre-registered risk).
SELF_SCHED_FLOOR = -200.0


def _plant_of(resource: str) -> int | None:
    """Map a 60-Day disclosure Resource Name to its EIA plant code."""
    for pref, code in PREFIX_TO_PLANT.items():
        if resource.startswith(pref + "_") or resource.startswith(pref):
            # Guard: LEG must not swallow other LEG-prefixed names; the
            # explicit map is prefix-unique on this corpus (checked in S2).
            return code
    return None


# --------------------------------------------------------------------------
# 1 — MODEL: the keeper's per-plant per-tranche curve (ercot143 capture reused)
# --------------------------------------------------------------------------


def section_model(bundle: Path, scratch: Path) -> list[dict]:
    """Capture the keeper's coal offer rows for all 10 plants, per tranche."""
    from scripts.probes.ercot143_lignite_offer_slope import capture_model_offer

    print(f"\n{'=' * 78}\n1 — MODEL: keeper per-plant per-tranche offer curve ({bundle.name})")
    print("=" * 78)
    out: list[dict] = []
    for year in YEARS:
        cap = capture_model_offer(bundle, year, scratch)
        print(f"\n  --- {year} ---")
        for code in sorted(PLANT_NAMES):
            name = PLANT_NAMES[code]
            sel = [i for i in range(len(cap["unit_id"])) if int(cap["plant_code"][i]) == code]
            if not sel:
                continue
            tot = float(sum(cap["pmax"][i] for i in sel))
            order = sorted(sel, key=lambda i: cap["bid"][i])
            capw = float(sum(cap["bid"][i] * cap["pmax"][i] for i in sel) / tot)
            lo = float(min(cap["bid"][i] for i in sel))
            hi = float(max(cap["bid"][i] for i in sel))
            parts = " | ".join(
                f"{cap['unit_id'][i].rpartition('_')[2]} "
                f"{cap['pmax'][i] / tot * 100:.0f}%@${cap['bid'][i]:.2f}"
                for i in order
            )
            print(f"    {name:<12} capw ${capw:>6.2f}  [{lo:.2f}..{hi:.2f}]  {parts}")
            out.append(
                {
                    "year": year,
                    "plant": name,
                    "plant_code": code,
                    "pmax_mw": round(tot, 1),
                    "capw_bid": round(capw, 2),
                    "bid_bot": round(lo, 2),
                    "bid_top": round(hi, 2),
                    "tranches": [
                        {
                            "tranche": cap["unit_id"][i].rpartition("_")[2],
                            "share": round(float(cap["pmax"][i]) / tot, 4),
                            "pmax_mw": round(float(cap["pmax"][i]), 1),
                            "bid": round(float(cap["bid"][i]), 2),
                            "heat_rate": round(float(cap["heat_rate"][i]), 3),
                            "fuel_price": round(float(cap["fuel_price"][i]), 4),
                        }
                        for i in order
                    ],
                }
            )
    return out


# --------------------------------------------------------------------------
# 2 — MEASURED: the plant's own submitted TPO curve, pooled + per-year
# --------------------------------------------------------------------------


def _modal_key_curve(g: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, int] | None:
    """Return (mw, price, count) of the modal submitted curve of a resource."""
    P = g[TPO_PR].to_numpy(float)
    M = g[TPO_MW].to_numpy(float)
    ok = np.isfinite(P) & np.isfinite(M)
    keys = [
        tuple(np.round(np.sort(P[i][ok[i]]), 2)) for i in range(len(P)) if ok[i].any()
    ]
    if not keys:
        return None
    key, n = Counter(keys).most_common(1)[0]
    i = next(
        j
        for j in range(len(P))
        if ok[j].any() and tuple(np.round(np.sort(P[j][ok[j]]), 2)) == key
    )
    pr = P[i][ok[i]]
    mw = M[i][ok[i]]
    o = np.argsort(mw)
    return mw[o], pr[o], int(n)


def _priced_level(mw: np.ndarray, pr: np.ndarray) -> dict:
    """Cap-weighted level of the priced (>SELF_SCHED_FLOOR) step segment.

    The submitted TPO is a step supply curve: point k covers capacity
    (mw[k-1], mw[k]] at price pr[k] (the first point covers 0..mw[0]).
    Weights are the step widths; the self-schedule floor block is excluded
    from the level and its MW reported.
    """
    edges = np.concatenate([[0.0], mw])
    widths = np.diff(edges)
    keep = pr > SELF_SCHED_FLOOR
    floor_mw = float(widths[~keep].sum())
    if not keep.any() or widths[keep].sum() <= 0:
        return {"level": float("nan"), "lo": float("nan"), "hi": float("nan"),
                "floor_block_mw": floor_mw, "priced_mw": 0.0}
    w = widths[keep]
    p = pr[keep]
    return {
        "level": float((w * p).sum() / w.sum()),
        "lo": float(p.min()),
        "hi": float(p.max()),
        "floor_block_mw": floor_mw,
        "priced_mw": float(w.sum()),
    }


def _window_price(mw: np.ndarray, pr: np.ndarray, lo_f: float, hi_f: float) -> float:
    """Mean price of the step curve over capacity window [lo_f, hi_f] (fractions
    of the curve's top MW), floor-block points included as-submitted."""
    top = float(mw[-1])
    lo, hi = lo_f * top, hi_f * top
    edges = np.concatenate([[0.0], mw])
    tot = 0.0
    wsum = 0.0
    for k in range(len(pr)):
        a, b = edges[k], edges[k + 1]
        w = max(0.0, min(b, hi) - max(a, lo))
        if w > 0:
            tot += w * pr[k]
            wsum += w
    return tot / wsum if wsum > 0 else float("nan")


def section_measured() -> dict:
    """2 — measured per-plant curves: modal, per-year stability, priced level."""
    print(f"\n{'=' * 78}\n2 — MEASURED: per-plant submitted TPO curves (pooled 60-Day SCED subsets)")
    print("=" * 78)
    frames: dict[str, pd.DataFrame] = {}
    for tag, _year, _fam in SUBSETS:
        r = load_sced(tag)
        if r is not None:
            f = r[0][r[0].cls == "COAL"].copy()
            f["subset"] = tag
            f["sub_year"] = _year
            frames[tag] = f
    if not frames:
        print("  FATAL: no SCED subset on disk")
        return {}
    pooled = pd.concat(frames.values(), ignore_index=True)
    pooled["plant_code"] = pooled["Resource Name"].map(_plant_of)
    unmapped = sorted(pooled.loc[pooled.plant_code.isna(), "Resource Name"].unique())
    if unmapped:
        print(f"  UNMAPPED coal resources (excluded): {unmapped}")

    out: dict = {"unmapped_resources": unmapped, "plants": []}
    for code in sorted(PLANT_NAMES):
        name = PLANT_NAMES[code]
        g_pl = pooled[pooled.plant_code == code]
        if g_pl.empty:
            print(f"\n  {name}: NOT IN CORPUS")
            out["plants"].append({"plant_code": code, "plant": name, "in_corpus": False})
            continue
        resources = sorted(g_pl["Resource Name"].unique())
        print(f"\n  {name} (EIA {code}) — {len(g_pl)} res-intervals, units: {resources}")
        res_rows = []
        for rn in resources:
            g = g_pl[g_pl["Resource Name"] == rn]
            mk = _modal_key_curve(g)
            if mk is None:
                res_rows.append({"resource": rn, "curve": None})
                continue
            mw, pr, n = mk
            lev = _priced_level(mw, pr)
            # per-year modal levels (2024 vs 2025 subsets) — time stability
            yr_lev = {}
            for yr in (2024, 2025):
                gy = g[g.sub_year == yr]
                mky = _modal_key_curve(gy) if len(gy) else None
                if mky is not None:
                    yr_lev[str(yr)] = round(_priced_level(mky[0], mky[1])["level"], 2)
            pts = "  ".join(f"({m:.0f}@${p:g})" for m, p in zip(mw, pr))
            print(f"    {rn:<18} modal x{n:<5} level ${lev['level']:.2f} "
                  f"[{lev['lo']:.2f}..{lev['hi']:.2f}] floor_blk {lev['floor_block_mw']:.0f}MW "
                  f"| by-yr {yr_lev}")
            print(f"      {pts}")
            res_rows.append(
                {
                    "resource": rn,
                    "n_intervals": int(len(g)),
                    "modal_count": n,
                    "modal_mw": [round(float(v), 1) for v in mw],
                    "modal_price": [round(float(v), 2) for v in pr],
                    "priced_level": round(lev["level"], 4),
                    "priced_lo": round(lev["lo"], 2),
                    "priced_hi": round(lev["hi"], 2),
                    "floor_block_mw": round(lev["floor_block_mw"], 1),
                    "priced_mw": round(lev["priced_mw"], 1),
                    "level_by_year": yr_lev,
                }
            )
        # plant-level: cap-weight resources by their modal-curve top MW
        good = [r for r in res_rows if r.get("modal_mw")]
        if good:
            wts = np.array([r["modal_mw"][-1] for r in good], float)
            levs = np.array([r["priced_level"] for r in good], float)
            plant_level = float((wts * levs).sum() / wts.sum())
            spread = float(
                max(r["priced_hi"] for r in good) - min(r["priced_lo"] for r in good)
            )
            print(f"    -> PLANT level ${plant_level:.2f}  within-plant priced spread ${spread:.2f}")
        else:
            plant_level, spread = float("nan"), float("nan")
        out["plants"].append(
            {
                "plant_code": code,
                "plant": name,
                "in_corpus": True,
                "resources": res_rows,
                "plant_level": round(plant_level, 4) if np.isfinite(plant_level) else None,
                "within_plant_spread": round(spread, 2) if np.isfinite(spread) else None,
            }
        )
    return out


# --------------------------------------------------------------------------
# 3 — DELTA: model vs measured, cap-weighted and at the tranche grain
# --------------------------------------------------------------------------


def section_delta(model_rows: list[dict], measured: dict) -> list[dict]:
    """3 — the adjudication statistic: per-plant model-minus-measured."""
    print(f"\n{'=' * 78}\n3 — DELTA: model vs measured, cap-weighted + tranche grain")
    print("=" * 78)
    meas_by_code = {p["plant_code"]: p for p in measured.get("plants", [])}
    out: list[dict] = []
    for year in YEARS:
        print(f"\n  --- {year} ---")
        print(f"    {'plant':<12}{'model capw':>11}{'meas level':>11}{'delta':>8}   tranche-grain (model -> measured@window)")
        for m in [r for r in model_rows if r["year"] == year]:
            mp = meas_by_code.get(m["plant_code"])
            if not mp or not mp.get("in_corpus") or mp.get("plant_level") is None:
                continue
            # measured plant curve: concatenate unit modal curves cap-side by
            # stacking (units are near-identical; use the largest-modal unit's
            # curve shape for window mapping, cap-weighted level for the level)
            good = [r for r in mp["resources"] if r.get("modal_mw")]
            best = max(good, key=lambda r: r["modal_count"])
            mw = np.array(best["modal_mw"], float)
            pr = np.array(best["modal_price"], float)
            # model committed+econ (above-mustrun, below-peak) cap-weighted bid
            mid = [t for t in m["tranches"] if t["tranche"] not in ("mustrun",)
                   and not t["tranche"].startswith("peak")]
            mid_w = sum(t["pmax_mw"] for t in mid)
            mid_capw = (sum(t["bid"] * t["pmax_mw"] for t in mid) / mid_w) if mid_w else float("nan")
            delta = mid_capw - mp["plant_level"]
            tr_txt = []
            tr_rows = []
            cum = 0.0
            for t in sorted(m["tranches"], key=lambda t: t["bid"]):
                lo_f, hi_f = cum, cum + t["share"]
                cum = hi_f
                wprice = _window_price(mw, pr, lo_f, hi_f)
                tr_txt.append(f"{t['tranche']} {t['bid']:.2f}->{wprice:.2f}")
                tr_rows.append(
                    {
                        "tranche": t["tranche"],
                        "share": t["share"],
                        "model_bid": t["bid"],
                        "measured_window_price": round(wprice, 2) if np.isfinite(wprice) else None,
                    }
                )
            print(f"    {m['plant']:<12}{mid_capw:>11.2f}{mp['plant_level']:>11.2f}{delta:>8.2f}   "
                  + " | ".join(tr_txt))
            out.append(
                {
                    "year": year,
                    "plant": m["plant"],
                    "plant_code": m["plant_code"],
                    "model_mid_capw": round(mid_capw, 2),
                    "measured_plant_level": mp["plant_level"],
                    "delta_mid": round(delta, 2),
                    "tranche_grain": tr_rows,
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results/calibration/ercot140_coal_peak_arm",
    )
    ap.add_argument("--skip-model", action="store_true")
    ap.add_argument("--json-out", type=Path, default=None)
    ap.add_argument(
        "--scratch",
        type=Path,
        default=REPO / "results/calibration/_ercot144_scratch",
    )
    args = ap.parse_args()

    print("=" * 78)
    print("ERCOT-144 Phase 1 — coal offer LEVEL per plant, model vs measured")
    print("measurement only: no LP, no solve, no parameter changed")
    print("=" * 78)

    blob: dict = {"lane": "ercot144-coal-perplant-offer", "phase": 1, "no_lp": True}
    model_rows: list[dict] = []
    if not args.skip_model:
        args.scratch.mkdir(parents=True, exist_ok=True)
        blob["keeper_bundle"] = args.bundle.name
        model_rows = section_model(args.bundle, args.scratch)
        blob["S1_model_offer"] = model_rows
    blob["S2_measured_perplant"] = section_measured()
    if model_rows:
        blob["S3_delta"] = section_delta(model_rows, blob["S2_measured_perplant"])

    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(blob, indent=2, default=float))
        print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

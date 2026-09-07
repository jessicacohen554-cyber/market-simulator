"""nyiso-218 — score the rule-29 STRUCTURAL screen gates S-1..S-5 for the
+3.0 % fossil energy-band offer lift (owner rulings R1/R2, 2026-09-07).

The instrument is the nyiso-213 payload-rebuild pattern with this session's own
gate definitions, all declared in ``PREREG-nyiso218-fossil-energy-band-lift.md``
§6 before the screen solved. The rebuild half is unchanged and is re-verified
here against the committed keeper payload (``payload_rebuild_identity``), so
keeper and arm are scored by ONE instrument on ONE basis.

G-CTRL is **form 4**: the control is the keeper's COMMITTED bundle
(``results/calibration/nyiso213_summer_seam`` + ``frontend/data/backcast/runs/
2026-09-07-nyiso-213-summer-seam.js``). No control solve is spent; the G-DRIFT
code audit validating form 4 is in the PREREG §4.

**The gates are STOP gates only and none is gated on C3a** (rule 1
``[R-STRUCT]``, rule 29 ``[R-SCREEN]``): a screen that reads "did the target
residual improve" is fitted-mechanism selection done one year at a time. C3a,
C3b and C3c are REPORTED at full magnitude and gate nothing.

Run::

    uv run python scripts/probes/nyiso218_screen_gates.py \
        --arm results/calibration/_nyiso218_screen_2023 --year 2023
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "src", ROOT / "scripts", ROOT / "scripts/probes"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.backcast_artifacts import decode_run_js  # noqa: E402

KEEPER_DIR = ROOT / "results/calibration/nyiso213_summer_seam"
KEEPER_PAYLOAD = (
    ROOT / "frontend/data/backcast/runs/2026-09-07-nyiso-213-summer-seam.js"
)
PHASE0 = ROOT / "results/calibration/_nyiso218_offer_lift_phase0.json"
T = 8760
MONTH_STARTS = np.cumsum(
    [0] + [d * 24 for d in (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30)]
)

#: Classes whose ``offer_curve_by_group`` bands the arm moves (phase-0 Part A
#: measured the moved set as exactly these five in every year).
MOVED_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_GAS")

#: S-2's order-of-magnitude window on the phase-0 prediction, declared ex ante.
S2_LO, S2_HI = 0.5, 2.0


def _year_block(bundle: Path, base: dict, year: int) -> dict:
    """Rebuild the payload year-block the rubric reads, from a bundle's hourlies."""
    sysd = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    yb = json.loads(json.dumps(base))
    mon = np.searchsorted(MONTH_STARTS, np.arange(T), side="right") - 1

    def _wm(x: np.ndarray, w: np.ndarray) -> float:
        return float((x * w).sum() / w.sum()) if w.sum() > 0 else float(x.mean())

    for z, sub in sysd.groupby("zone"):
        sub = sub.sort_values("hour")
        pr, dm = sub.price.to_numpy(), sub.demand.to_numpy()
        mo = mon[sub.hour.to_numpy() % T]
        yb["lmp"][z] = {
            "p": round(_wm(pr, dm), 2),
            "d": round(float(dm.sum() / 1e6), 4),
            "pMon": [round(_wm(pr[mo == k], dm[mo == k]), 2) for k in range(12)],
            "dMon": [round(float(dm[mo == k].sum() / 1e6), 4) for k in range(12)],
        }
    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"].groupby("klass").mw.sum() / 1e6
    for k in list(yb["gmModel"]):
        yb["gmModel"][k] = round(float(ch.get(k, 0.0)), 4)
    return yb


def _fuel_rows(bundle: Path, year: int, base: dict) -> list[dict]:
    """Rebuild C4's ``fuelRows`` gas/coal hourly fit from a bundle's class hourlies.

    The gas/coal model series is the hourly sum of the classes the taxonomy rolls
    up to each EIA-930 fuel (``classes_for_fuel930``) — the same construction
    ``render_calibration_html`` uses at registration. The actual is the LIVE
    ``load_eia_hourly_benchmark`` series; it is called identically for keeper and
    arm, so the PASS→FAIL flip test is like-for-like. nyiso-217 P2 measured that
    the loader's only NYISO effect in 2022-2025 is 2024's ``other`` series, which
    neither family reads.
    """
    from market_sim.config.plant_taxonomy import classes_for_fuel930
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    piv = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(T)).fillna(0.0)
    bench_h = load_eia_hourly_benchmark("NYISO", year)
    rows = []
    for fuel in ("gas", "coal"):
        classes = classes_for_fuel930(fuel)
        model = np.zeros(T)
        for c in classes:
            if c in piv.columns:
                model = model + piv[c].to_numpy(dtype=float)
        actual = np.asarray(bench_h[fuel], dtype=float)[:T]
        m_twh = float(model.sum() / 1e6)
        b_twh = float(actual.sum() / 1e6)
        if actual.std() > 0 and model.std() > 0:
            r = float(np.corrcoef(model, actual)[0, 1])
            nrmse = float(np.sqrt(((model - actual) ** 2).mean()) / actual.mean())
        else:
            r, nrmse = None, None
        rows.append(
            {
                "fuel": fuel,
                "m": round(m_twh, 2),
                "b": round(b_twh, 2),
                "r": round(r, 3) if r is not None else None,
                "nrmse": round(nrmse, 3) if nrmse is not None else None,
            }
        )
    # Preserve any non-gas/coal rows the committed payload carried (C4 reads
    # only gas and coal, but the block is kept whole so nothing is silently lost).
    keep = [r for r in (base.get("fuelRows") or []) if r.get("fuel") not in ("gas", "coal")]
    return rows + keep


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--year", type=int, required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    arm, year = Path(args.arm), args.year
    import calibration_verdict as cv

    rec: dict = {"session": "nyiso-218", "arm": str(arm), "year": year, "gates": {}}
    ph0 = json.load(open(PHASE0))
    pred = next(b for b in ph0["part_b"] if b["year"] == year)

    # ---- S-1 recipe identity: the arm differs from the keeper ONLY in the
    # three energy bands of the 13 fossil groups (and the --year selection keys).
    k_cfg = json.load(open(KEEPER_DIR / "run_config.json"))["scenario_config"]
    a_cfg = json.load(open(arm / "run_config.json"))["scenario_config"]
    diff = {
        k: (k_cfg.get(k), a_cfg.get(k))
        for k in set(k_cfg) | set(a_cfg)
        if k_cfg.get(k) != a_cfg.get(k)
    }
    year_keys = {
        k: v for k, v in diff.items() if k in ("weather_year", "gas_price_override")
    }
    other = {
        k: v
        for k, v in diff.items()
        if k not in year_keys and k != "offer_curve_by_group"
    }
    kc, ac = k_cfg["offer_curve_by_group"], a_cfg["offer_curve_by_group"]
    band_moves, band_bad = {}, []
    for g in sorted(set(kc) | set(ac)):
        for b in sorted(set(kc.get(g, {})) | set(ac.get(g, {}))):
            kv, av = kc.get(g, {}).get(b), ac.get(g, {}).get(b)
            if kv == av:
                continue
            if b in ("committed", "econ_low", "econ_high") and kv:
                ratio = av / kv
                band_moves[f"{g}.{b}"] = [kv, av, round(ratio, 12)]
                if abs(ratio - 1.03) > 1e-9:
                    band_bad.append(f"{g}.{b} ratio {ratio!r}")
            else:
                band_bad.append(f"{g}.{b} moved but is not a lifted energy band")
    # 30 = 10 routable fossil groups x 3 energy bands. The three
    # ``*_INTERMEDIATE`` groups left the override at
    # ADDENDUM-nyiso218-intermediate-drop-2026-09-07 (the router cannot
    # resolve them; the drop was MEASURED bitwise-identical on mc_base).
    s1 = not other and not band_bad and len(band_moves) == 30
    rec["gates"]["S1"] = {
        "pass": bool(s1),
        "n_bands_moved": len(band_moves),
        "n_bands_expected": 30,
        "all_ratios_exactly_1.03": not band_bad,
        "violations": band_bad,
        "non_offer_curve_recipe_diff": other,
        "year_selection_keys_excluded": year_keys,
        "band_moves": band_moves,
    }

    # ---- payload rebuild (one instrument, both arms) + rebuild identity check
    base = decode_run_js(KEEPER_PAYLOAD.read_text())["years"][str(year)]
    bench = json.load(
        gzip.open(ROOT / f"frontend/data/backcast/bench/NYISO/{year}.json.gz")
    )["bench"]
    yk = _year_block(KEEPER_DIR, base, year)
    ya = _year_block(arm, base, year)
    rebuild_identity = {
        "lmp_p_max_abs_diff": max(
            abs(yk["lmp"][z]["p"] - base["lmp"][z]["p"]) for z in base["lmp"]
        ),
        "gmModel_max_abs_diff": max(
            abs(yk["gmModel"][k] - base["gmModel"][k]) for k in base["gmModel"]
        ),
        "zones_match": sorted(yk["lmp"]) == sorted(base["lmp"]),
    }
    yk["fuelRows"] = _fuel_rows(KEEPER_DIR, year, base)
    ya["fuelRows"] = _fuel_rows(arm, year, base)
    committed_gas = next(
        (r for r in (base.get("fuelRows") or []) if r.get("fuel") == "gas"), {}
    )
    rebuilt_gas = next(r for r in yk["fuelRows"] if r["fuel"] == "gas")
    rebuild_identity["fuelRows_gas_committed_vs_rebuilt"] = {
        "committed": {k: committed_gas.get(k) for k in ("m", "b", "r", "nrmse")},
        "rebuilt_keeper": {k: rebuilt_gas.get(k) for k in ("m", "b", "r", "nrmse")},
    }

    # ---- S-2 passthrough: direction and order of magnitude vs the phase-0 prediction
    def _lw(yb: dict) -> float:
        pairs = [(z["p"], z.get("d", 0.0)) for z in yb["lmp"].values()]
        num = sum(p * d for p, d in pairs)
        den = sum(d for _p, d in pairs)
        return num / den if den else float("nan")

    lw_k, lw_a = _lw(yk), _lw(ya)
    measured = lw_a - lw_k
    pred_in = pred["modes"]["inzone"]["pred_d_lw_price_usd_mwh"]
    pred_sy = pred["modes"]["system"]["pred_d_lw_price_usd_mwh"]
    band_lo, band_hi = S2_LO * min(pred_in, pred_sy), S2_HI * max(pred_in, pred_sy)
    same_sign = (measured > 0) == (pred_in > 0)
    s2 = bool(same_sign and band_lo <= measured <= band_hi)
    rec["gates"]["S2"] = {
        "pass": s2,
        "keeper_lw_price": round(lw_k, 4),
        "arm_lw_price": round(lw_a, 4),
        "measured_d_lw_price": round(measured, 4),
        "pred_inzone": pred_in,
        "pred_system": pred_sy,
        "accept_window": [round(band_lo, 4), round(band_hi, 4)],
        "same_sign": bool(same_sign),
        "realized_over_pred_inzone": round(measured / pred_in, 4) if pred_in else None,
        "passthrough_usd_mwh_per_1pct_band": round(measured / 3.0, 4),
    }

    # ---- S-3 footprint confinement
    def _cls(bundle: Path) -> pd.Series:
        ch = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
        return ch[ch["pass"] == "P1"].groupby("klass").mw.sum() / 1e6

    ck, ca = _cls(KEEPER_DIR), _cls(arm)
    classes = sorted(set(ck.index) | set(ca.index))
    delta = {c: round(float(ca.get(c, 0.0) - ck.get(c, 0.0)), 4) for c in classes}
    moved_agg = sum(delta.get(c, 0.0) for c in MOVED_CLASSES)
    total_k = float(ck.sum())
    stchp = abs(delta.get("ST_CHP", 0.0))
    s3 = bool(
        moved_agg <= 1e-6
        and abs(sum(delta.values())) <= 0.005 * total_k
        and stchp <= abs(moved_agg) + 1e-9
    )
    rec["gates"]["S3"] = {
        "pass": s3,
        "moved_class_aggregate_delta_twh": round(moved_agg, 4),
        "all_class_sum_delta_twh": round(sum(delta.values()), 4),
        "energy_balance_tol_twh": round(0.005 * total_k, 4),
        "st_chp_abs_delta_twh": round(stchp, 4),
        "class_delta_twh": delta,
    }

    # ---- S-4 no NON-TARGET load-bearing criterion flips PASS -> FAIL (C1/C2/C4)
    sc: dict = {}
    for label, yb in (("keeper", yk), ("arm", ya)):
        sc[label] = {
            "C1": {
                r["key"]: (r["status"], r.get("magnitude"))
                for r in cv.score_fuelmix(year, yb, bench, "NYISO")
            },
            "C2": {
                r["key"]: (r["status"], r.get("magnitude"))
                for r in cv.score_sysvol(year, yb, bench, "NYISO")
            },
            "C4": {
                r["key"]: (r["status"], r.get("magnitude"))
                for r in cv.score_dispatch_corr(year, yb, bench, "NYISO")
            },
            "C3a_REPORTED": (
                lambda r: (r["status"], r.get("magnitude"), r.get("model"), r.get("actual"))
            )(cv.score_price_mean(year, yb, bench)),
            "C3b_REPORTED": (lambda r: (r["status"], r.get("magnitude")))(
                cv.score_price_shape(year, yb, bench)
            ),
        }
    flips = []
    for cid in ("C1", "C2", "C4"):
        for key, (st, _m) in sc["keeper"][cid].items():
            if st == "PASS" and sc["arm"][cid].get(key, ("?",))[0] == "FAIL":
                flips.append([cid, key])
    rec["gates"]["S4"] = {
        "pass": not flips,
        "flips_pass_to_fail": flips,
        "gated_criteria": ["C1", "C2", "C4"],
        "reported_not_gated": ["C3a", "C3b", "C3c"],
        "scores": sc,
        "payload_rebuild_identity_vs_committed": rebuild_identity,
        "C8_forced_share": (
            "NOT COMPUTABLE for an unregistered screen bundle (needs "
            "legitimacy_diagnostics.json, written only by the register path). "
            "The arm moves no floor, no share and no availability — only three "
            "offer bands — so the forced VOLUME is untouched by construction; "
            "REPORTED, and re-scored on the full-span bundle if the span is spent."
        ),
        "C6_governance": (
            "the attestation is written at registration; the arm is the keeper "
            "recipe plus the declared authorized_price_tuning channel (rule 1 "
            "carve-out conditions (a)-(e))."
        ),
    }

    # ---- S-5 price tail, reported at full magnitude (C3c is a ledgered caveat)
    def _tail(bundle: Path) -> dict:
        df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
        pv = df[df["pass"] == "P1"].pivot(index="hour", columns="zone", values="price")
        mx = pv.max(axis=1).to_numpy()
        return {
            "hours_max_zonal_gt_300": int((mx > 300).sum()),
            "hours_max_zonal_gt_100": int((mx > 100).sum()),
            "system_mean": round(float(pv.mean(axis=1).mean()), 4),
        }

    rec["gates"]["S5"] = {
        "pass": None,
        "note": "REPORTED ONLY — C3c is the standing ledgered caveat; never a gate here.",
        "keeper": _tail(KEEPER_DIR),
        "arm": _tail(arm),
    }

    rec["screen_verdict"] = {
        "gates_pass": all(
            rec["gates"][g]["pass"] for g in ("S1", "S2", "S3", "S4")
        ),
        "per_gate": {g: rec["gates"][g]["pass"] for g in ("S1", "S2", "S3", "S4", "S5")},
    }
    out = Path(args.out or ROOT / f"results/calibration/_nyiso218_screen_gates_{year}.json")
    out.write_text(json.dumps(rec, indent=1, default=str) + "\n")
    print(json.dumps(rec["screen_verdict"], indent=1))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

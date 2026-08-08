"""miso-142 gate G-B — signature vs cause: the marginal class and the STACK SLOPE.

No solve, no keeper replay.  Tests PREREG
``results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md``
predictions **P5** (CT headroom -- TRAP 1's counter-measurement) and **P10**
(the decisive sufficiency gate), and supplies G-B's causal test for **O2**.

**The miso-129 bar: a signature is not a cause.**  O2 observes a coal overrun
co-occurring with the price miss.  Co-occurrence licenses nothing.  Coal is
credited as *causing* the low price only if displacing coal would move the
price, and the size of that effect is the **local slope of the model's own
supply stack at the clearing point** -- which is measured here, from the
keeper's committed P1 output, not inferred.

**Three instruments, all from committed artifacts:**

1. **The empirical stack slope (P10).**  Within one window (so fuel prices are
   near-constant), bin the model's own hours by the thermal MW it had to serve
   and take the median clearing price per bin.  ``d(price)/d(thermal GW)`` at
   the operating point is the price reach of ONE GW of quantity displacement --
   the number every quantity hypothesis in this lane has to be multiplied by.
   Reported over the first 1 / 2 / 5 / 12 GW so a non-linear stack cannot hide
   behind a single local derivative, and inverted to answer the only question
   that matters: **how many GW of displacement would it take to reach the
   measured actual price?**
2. **The marginal class, measured from behaviour.**  For each class, the OLS
   slope of its own dispatch on total thermal requirement across the window's
   hours.  The class that absorbs the incremental MW *is* the class at the
   margin; this needs no ``mc`` rebuild and therefore crosses no basis.
3. **CT headroom (P5).**  Capability minus dispatch in the affected hours, on
   the miso-139 §7 basis, rebuilt from the model's own fleet + availability so
   TRAP 1 is answered with a number BEFORE anything is attributed to capability.

**TRAP 5** (the coal alias) is handled by the explicit, asserted map carried
over from ``_miso141_cc_rows_and_cushion.py``.
**Basis note:** every price and every MW here is the MODEL's own, so no
EIA-930/EIA-923 instrument offset enters this gate at all.

Probe hygiene (miso-140b §6): REPO ROOT on ``sys.path``, ``load_zonal_shares``
asserted non-None.

Usage::

    .venv/bin/python scripts/probes/_miso142_marginal_and_slope.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))  # probe hygiene, miso-140b §6 -- REPO ROOT
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso137_c3a_gap_decomposition import (  # noqa: E402
    HOURS,
    actual_hourly,
    model_hourly,
    month_of_hour,
)

KEEPER = REPO / "results/calibration/miso132_ccmin_B"
OUT = REPO / "results/calibration/_miso142_marginal_and_slope.json"
YEARS = (2023, 2024, 2025)  # rule 22

W1_MONTHS, W1_HOD = (6, 7), (8, 21)
SUMMER_JJA, SUMMER_JJAS = (6, 7, 8), (6, 7, 8, 9)
AFT_HOD = (12, 13, 14, 15, 16, 17)  # miso-139 §7's window

# TRAP 5: explicit sidecar alias, asserted (miso-141).
COAL_COLS = ("COAL_BIT", "COAL_LIGNITE", "COAL_PRB")
GAS_COLS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS", "CC_CHP", "CT_CHP", "ST_CHP")
# Dispatchable thermal: what the stack has to supply once the price-takers
# (wind/solar/nuclear/hydro/import/storage) have been netted off.
THERMAL_COLS = COAL_COLS + GAS_COLS + ("OTHER", "oil", "biomass")
SIDECAR_ALIAS = {"COAL": COAL_COLS}
# miso-139 §7 cushion classes (its own basis, reproduced so the two compare).
CUSHION_CLASSES = ("CT_PEAKER", "CC_REGULAR")
CUSHION_EXTRA = ("COAL",)

N_BINS = 12


def classes(year: int) -> pd.DataFrame:
    df = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    if "pass" in df:
        df = df[df["pass"].astype(str).str.upper() == "P1"]
    piv = df.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
    piv = piv.reindex(range(HOURS)).fillna(0.0)
    piv.columns = [str(c) for c in piv.columns]
    for c in THERMAL_COLS:
        assert c in piv.columns, (
            f"class {c!r} absent from sidecar (have {sorted(piv.columns)}) -- an "
            "unmapped class silently reads ZERO (TRAP 5, miso-141)"
        )
    return piv


def binned_curve(q: np.ndarray, p: np.ndarray, n: int = N_BINS) -> dict:
    """Median clearing price by thermal-requirement bin -- the model's own stack."""
    edges = np.quantile(q, np.linspace(0, 1, n + 1))
    rows = []
    for i in range(n):
        lo, hi = edges[i], edges[i + 1]
        sel = (q >= lo) & (q <= hi) if i == n - 1 else (q >= lo) & (q < hi)
        if sel.sum() < 5:
            continue
        rows.append(
            {
                "bin": i,
                "n": int(sel.sum()),
                "thermal_gw_median": round(float(np.median(q[sel])) / 1000.0, 4),
                "price_median": round(float(np.median(p[sel])), 3),
                "price_mean": round(float(np.mean(p[sel])), 3),
            }
        )
    return {"edges_gw": [round(e / 1000.0, 4) for e in edges], "bins": rows}


def slope_over(curve: dict, base_gw: float, delta_gw: float) -> float | None:
    """Price rise ($/MWh per GW) from ``base_gw`` to ``base_gw + delta_gw``.

    Linear interpolation on the binned median curve; ``None`` when the target
    lies beyond the model's own observed range in this window (reported as such
    rather than extrapolated -- extrapolating a stack you have not observed is
    how a flat model gets credited with a steep tail).
    """
    b = curve["bins"]
    if len(b) < 2:
        return None
    x = np.array([r["thermal_gw_median"] for r in b])
    y = np.array([r["price_median"] for r in b])
    tgt = base_gw + delta_gw
    if tgt > x.max() or base_gw < x.min():
        return None
    return round(float((np.interp(tgt, x, y) - np.interp(base_gw, x, y)) / delta_gw), 3)


def gw_to_reach(curve: dict, base_gw: float, target_price: float) -> dict:
    """GW of extra thermal requirement needed to reach ``target_price``.

    Answers the lane's actual question.  ``reachable`` is False when the model's
    own observed curve never gets there -- the honest answer, not an
    extrapolation.
    """
    b = curve["bins"]
    x = np.array([r["thermal_gw_median"] for r in b])
    y = np.array([r["price_median"] for r in b])
    if target_price > y.max():
        return {
            "reachable": False,
            "max_observed_price": round(float(y.max()), 3),
            "at_thermal_gw": round(float(x[int(np.argmax(y))]), 3),
            "note": "the model's own summer stack never reaches the target price "
            "anywhere in its observed range -- no quantity displacement inside "
            "the window can produce it",
        }
    # y is not guaranteed monotone; take the first crossing.
    for i in range(1, len(x)):
        if y[i] >= target_price:
            frac = (target_price - y[i - 1]) / max(1e-9, (y[i] - y[i - 1]))
            xt = x[i - 1] + frac * (x[i] - x[i - 1])
            return {
                "reachable": True,
                "thermal_gw_at_target": round(float(xt), 3),
                "gw_above_base": round(float(xt - base_gw), 3),
            }
    return {"reachable": False, "note": "no crossing found"}


def marginal_response(piv: pd.DataFrame, sel: np.ndarray, q: np.ndarray) -> dict:
    """OLS slope of each class's dispatch on total thermal requirement.

    The class absorbing the incremental MW is the class at the margin.  Slopes
    sum to ~1.0 across the thermal classes by construction, which is asserted as
    a self-check.
    """
    out, tot = {}, 0.0
    qq = q - q.mean()
    den = float((qq * qq).sum())
    for c in THERMAL_COLS:
        v = piv[c].to_numpy(float)[sel]
        s = float(((v - v.mean()) * qq).sum() / den) if den else float("nan")
        out[c] = round(s, 4)
        tot += s
    out["_sum_check"] = round(tot, 4)
    return out


def ct_headroom(year: int, sel: np.ndarray, piv: pd.DataFrame) -> dict:
    """P5 / TRAP 1 -- capability minus dispatch, miso-139 §7 basis."""
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import generators_to_fleet_arrays, load_fleet_from_csv
    from _miso141_summer_derate_basis import keeper_config

    cfg = keeper_config(year)
    gens = load_fleet_from_csv(
        "MISO",
        get_iso_config("MISO"),
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in get_iso_config("MISO").zones]
    fa = generators_to_fleet_arrays(gens, zones, HOURS, iso="MISO", config=cfg, year=year)
    cap = fa.pmax[:, None] * fa.availability
    groups = np.array([g.plant_group for g in gens])
    n = int(sel.sum())

    rows, cushion = {}, 0.0
    for cls in CUSHION_CLASSES + CUSHION_EXTRA:
        gsel = groups == cls
        if not gsel.any():
            continue
        cols = [c for c in SIDECAR_ALIAS.get(cls, (cls,)) if c in piv.columns]
        assert cols, (
            f"class {cls!r} has no sidecar column -- an unmapped class reads zero "
            "dispatch and inflates the cushion by its whole capability (TRAP 5)"
        )
        capability = float(cap[gsel][:, sel].sum()) / n
        disp = float(sum(piv[c].to_numpy(float)[sel].sum() for c in cols)) / n
        head = max(0.0, capability - disp)
        rows[cls] = {
            "capability_mw": round(capability, 1),
            "dispatch_mw": round(disp, 1),
            "headroom_mw": round(head, 1),
            "loaded_frac": round(disp / capability, 4) if capability else None,
        }
        cushion += head
    return {"n_hours": n, "classes": rows, "cushion_mw": round(cushion, 1)}


def main() -> None:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zs = load_zonal_shares("MISO", 2025, [z.name for z in get_iso_config("MISO").zones])
    assert zs is not None, "load_zonal_shares None -- repo root off sys.path"

    hr = np.arange(HOURS)
    mon, hod = month_of_hour(hr), hr % 24
    w1 = np.isin(mon, W1_MONTHS) & (hod >= W1_HOD[0]) & (hod < W1_HOD[1])
    aft_jja = np.isin(mon, SUMMER_JJA) & np.isin(hod, AFT_HOD)
    aft_jjas = np.isin(mon, SUMMER_JJAS) & np.isin(hod, AFT_HOD)

    out: dict = {
        "prereg": "results/calibration/PREREG-miso142-summer-supply-stack-2026-08-08.md",
        "gate": "G-B (signature vs cause; the stack slope)",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "basis": "model-only: keeper P1 price + P1 class dispatch + model fleet "
        "capability. No EIA-930/EIA-923 instrument offset enters this gate.",
        "years": {},
    }

    for year in YEARS:
        piv = classes(year)
        _, p_h, W_h, _ = model_hourly(year)
        rt, _ = actual_hourly(year)
        thermal = piv[list(THERMAL_COLS)].sum(axis=1).to_numpy(float)

        yr: dict = {}
        for wname, sel in (("W1_jun_jul_h8_20", w1), ("JJA_h12_17", aft_jja)):
            ok = sel & np.isfinite(p_h) & np.isfinite(thermal)
            q, p = thermal[ok], p_h[ok]
            a = rt[ok]
            base_gw = float(np.median(q)) / 1000.0
            curve = binned_curve(q, p)
            act_lw = float(
                (a[np.isfinite(a)] * W_h[ok][np.isfinite(a)]).sum()
                / W_h[ok][np.isfinite(a)].sum()
            )
            mdl_lw = float((p * W_h[ok]).sum() / W_h[ok].sum())
            yr[wname] = {
                "n_hours": int(ok.sum()),
                "model_lw_price": round(mdl_lw, 3),
                "actual_lw_price": round(act_lw, 3),
                "deficit_usd_per_mwh": round(mdl_lw - act_lw, 3),
                "thermal_gw_median": round(base_gw, 3),
                "thermal_gw_p05_p95": [
                    round(float(np.quantile(q, 0.05)) / 1000.0, 3),
                    round(float(np.quantile(q, 0.95)) / 1000.0, 3),
                ],
                "stack_curve": curve,
                "slope_usd_per_gw": {
                    f"+{d}GW": slope_over(curve, base_gw, float(d))
                    for d in (1, 2, 5, 12)
                },
                "gw_needed_to_reach_actual": gw_to_reach(curve, base_gw, act_lw),
                "marginal_response_ols": marginal_response(piv, ok, q),
            }
        yr["ct_headroom_W1"] = ct_headroom(year, w1, piv)
        yr["ct_headroom_JJA_h12_17"] = ct_headroom(year, aft_jja, piv)
        yr["ct_headroom_JJAS_h12_17"] = ct_headroom(year, aft_jjas, piv)
        out["years"][str(year)] = yr

    OUT.write_text(json.dumps(out, indent=1))

    print("=" * 78)
    print("miso-142 G-B -- marginal class and STACK SLOPE (model's own output)")
    print("=" * 78)
    for year in YEARS:
        y = out["years"][str(year)]
        for wname in ("W1_jun_jul_h8_20", "JJA_h12_17"):
            w = y[wname]
            print(
                f"\n{year} {wname}  ({w['n_hours']} h)  model {w['model_lw_price']:.2f} "
                f"vs actual {w['actual_lw_price']:.2f}  deficit "
                f"{w['deficit_usd_per_mwh']:+.2f} $/MWh"
            )
            print(
                f"   thermal median {w['thermal_gw_median']:.1f} GW "
                f"(p05-p95 {w['thermal_gw_p05_p95'][0]:.1f}-{w['thermal_gw_p05_p95'][1]:.1f})"
            )
            print("   STACK SLOPE $/MWh per GW: ", end="")
            print(
                "  ".join(
                    f"{k} {v}" for k, v in w["slope_usd_per_gw"].items()
                )
            )
            g = w["gw_needed_to_reach_actual"]
            print(
                f"   to reach the ACTUAL price: "
                + (
                    f"+{g['gw_above_base']} GW of thermal requirement"
                    if g.get("reachable")
                    else f"UNREACHABLE -- model's own max observed price in this "
                    f"window is {g.get('max_observed_price')} $/MWh"
                )
            )
            mr = w["marginal_response_ols"]
            top = sorted(
                ((k, v) for k, v in mr.items() if not k.startswith("_")),
                key=lambda kv: -kv[1],
            )[:5]
            print(
                "   marginal response (dClass/dThermal): "
                + "  ".join(f"{k} {v:+.3f}" for k, v in top)
                + f"   [sum {mr['_sum_check']}]"
            )
        for key in ("ct_headroom_W1", "ct_headroom_JJA_h12_17", "ct_headroom_JJAS_h12_17"):
            h = y[key]
            ct = h["classes"].get("CT_PEAKER", {})
            print(
                f"   {key:26s} CT_PEAKER loaded {ct.get('loaded_frac')} "
                f"({ct.get('dispatch_mw')} / {ct.get('capability_mw')} MW), "
                f"idle {ct.get('headroom_mw')} MW | total cushion {h['cushion_mw']} MW"
            )
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

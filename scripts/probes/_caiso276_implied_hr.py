"""caiso-276 phase 0 part 4: is 2022's residual ONE object (a marginal
heat-rate bias levered by gas price) or TWO (an adder plus a December
excess)? And WHAT carries the too-high marginal heat rate? ZERO LP.

caiso-270 §4 measured a system-wide implied-marginal-heat-rate bias — the
model above the market in 40 of 48 ISO-months, mean +1.01, median +0.84 — and
ranked Dec-2022's +1.73 twelfth of forty-eight, i.e. an ORDINARY month for the
bias whose dollar error is large only because gas that month was 3.7x the
year's mean. caiso-273 §6.3 nevertheless carried "2022 is two objects" as a
standing disclosure. This probe settles which reading 2022's own numbers
support, and then measures the offer-stack state in the hours that carry the
residual.

THE TWO TESTS
-------------
H-1  ONE-OBJECT TEST. Per calendar month, the implied marginal heat rate
     (load-weighted price / the model's own delivered gas price) for model and
     actual. If ``HR_model - HR_actual`` is roughly CONSTANT across months —
     December included — then one bias times a varying gas price explains the
     whole year and 2022 is ONE object. If December's HR bias is an outlier,
     it is a second object and needs its own mechanism.

H-2  BOUND CENSUS. In the hours carrying the residual, is the model's marginal
     resource inefficient because the efficient capacity is EXHAUSTED (every
     cheap CC tranche at its upper bound) or because it is NOT COMMITTED /
     NOT AVAILABLE (idle capacity sitting at zero below a cheaper offer than
     the clearing price)? Those two diagnoses have opposite successors:
     exhaustion is a fleet/availability object, non-commitment is the RA
     must-offer reach the caiso-276 charter was pointed at. The census reads
     the keeper's OWN assembled ``mc_base`` and ``pmax x availability``, so
     the offer prices are the prices the LP solved on.

Neither test reads whether a lever moves C3a (rule 1 ``[R-STRUCT]``); both
describe the solved state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso275_B_gascoupling_2022"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
BENCH = REPO / "frontend/data/backcast/bench/CAISO/2022.json.gz"
OUT = REPO / "results/calibration/_caiso276_implied_hr.json"
YEAR = 2022
T = 8760
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
_MD = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum((0,) + tuple(d * 24 for d in _MD))[:12]
#: Offer-price match tolerance, $/MWh — caiso-272's value, unchanged, never swept.
TOL = 0.25


def lw(v, w) -> float:
    return float((np.asarray(v, float) * np.asarray(w, float)).sum() / np.sum(w))


def main() -> None:
    import gzip

    out: dict = {"session": "caiso-276", "year": YEAR, "phase": "0d"}
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    zones = [z for z in CA_ZONES if z in pr.columns]
    P = pr[zones].to_numpy(float).T
    D = dm[zones].to_numpy(float).T
    lam = (P * D).sum(axis=0) / D.sum(axis=0)
    w = D.sum(axis=0)
    # The MONTHLY committed actual is the basis here (the scorer's own
    # ``rt_lw_mon``), not the hourly series: H-1 is a per-month statistic and
    # using the bench keeps it on the gated basis (part 2's reconciliation).
    rt_lw_mon = json.load(gzip.open(BENCH))["bench"]["avgLMP"]["rt_lw_mon"]

    print("rebuilding the keeper's own 2022 offer surface (fleet_only)...")
    state, meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=(), required_sequences=()
    )
    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], float)  # (gen, hour) offer price
    fuel_row = np.asarray(state["fuel_prices"], float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    out["git_sha_keeper"] = meta.get("git_sha")
    midx = np.clip(np.searchsorted(_CUM, np.arange(T), side="right") - 1, 0, 11)

    # ---- the model's OWN delivered gas price, load-weighted per month ----
    # Use the gas-fired rows' own fuel price row (the assembled series the LP
    # priced on), capacity-weighted so it is the fleet's delivered gas, not a
    # hub quote.
    gasmask = np.isin(fuel, ["natural_gas", "gas", "NG"]) | np.char.startswith(
        klass.astype(str), "C"
    )
    gasmask = gasmask & (fuel_row.max(axis=1) > 0) if fuel_row.ndim == 2 else gasmask
    if fuel_row.ndim == 2:
        cw = cap[gasmask].sum(axis=0)
        gas_h = np.where(
            cw > 0,
            (fuel_row[gasmask] * cap[gasmask]).sum(axis=0) / np.maximum(cw, 1e-9),
            np.nan,
        )
    else:
        gas_h = np.full(T, np.nan)
    out["gas_series_available"] = bool(np.isfinite(gas_h).any())

    rows = []
    for m in range(12):
        sel = midx == m
        ww = w[sel]
        g = lw(gas_h[sel], ww) if np.isfinite(gas_h[sel]).all() else float("nan")
        pm = lw(lam[sel], ww)
        am = rt_lw_mon[m]
        rows.append(
            {
                "month": m + 1,
                "gas_usd_mmbtu": round(g, 3),
                "model_price": round(pm, 2),
                "actual_price": am,
                "hr_model": round(pm / g, 3) if g and g == g else None,
                "hr_actual": round(am / g, 3) if g and g == g else None,
                "hr_bias": round(pm / g - am / g, 3) if g and g == g else None,
                "gap_usd": round(pm - am, 2),
            }
        )
    out["H1_monthly_implied_hr"] = rows
    print("\n=== H-1  implied marginal heat rate by month, 2022 ===")
    print("  mon     gas   model  actual   HR_mod  HR_act  HR_BIAS     gap$")
    for r in rows:
        print(
            f"  {r['month']:>3d} {r['gas_usd_mmbtu']:>7.2f} {r['model_price']:>7.2f}"
            f" {r['actual_price']:>7.2f} {r['hr_model']:>8.3f} {r['hr_actual']:>7.3f}"
            f" {r['hr_bias']:>+8.3f} {r['gap_usd']:>+8.2f}"
        )
    bias = np.array([r["hr_bias"] for r in rows if r["hr_bias"] is not None])
    if bias.size:
        stats = {
            "mean": round(float(bias.mean()), 3),
            "sd": round(float(bias.std(ddof=1)), 3),
            "cv": round(float(bias.std(ddof=1) / abs(bias.mean())), 3),
            "december": rows[11]["hr_bias"],
            "december_rank_of_12": int(1 + (bias > rows[11]["hr_bias"]).sum()),
            "ex_dec_mean": round(float(bias[:11].mean()), 3),
            "ex_dec_sd": round(float(bias[:11].std(ddof=1)), 3),
        }
        out["H1_stats"] = stats
        print(
            f"\n  HR bias: mean {stats['mean']:+.3f}  sd {stats['sd']:.3f}"
            f"  CV {stats['cv']:.3f}"
        )
        print(
            f"  December {stats['december']:+.3f} ranks"
            f" {stats['december_rank_of_12']} of 12"
            f" (ex-Dec mean {stats['ex_dec_mean']:+.3f},"
            f" sd {stats['ex_dec_sd']:.3f})"
        )
        # ONE-OBJECT verdict, stated as a measurement not an assertion
        z = (
            ((rows[11]["hr_bias"] - stats["ex_dec_mean"]) / stats["ex_dec_sd"])
            if stats["ex_dec_sd"]
            else float("nan")
        )
        out["H1_december_z_vs_exdec"] = round(float(z), 2)
        print(f"  December's HR bias is {z:+.2f} sd from the ex-December mean")

    # ---- H-2  BOUND CENSUS in the residual-carrying hours ----
    # Residual-carrying hours are defined WITHOUT reference to the price gap:
    # the ex-December shoulder window the part-2 decomposition located, i.e.
    # hod 6-9 and 19-22. Reported for the belly core (hod 10-16) beside it so
    # the comparison is visible.
    hod = np.arange(T) % 24
    windows = {
        "shoulder_hod_6_9_19_22": np.isin(hod, [6, 7, 8, 9, 19, 20, 21, 22])
        & (midx != 11),
        "belly_core_hod_10_16": np.isin(hod, range(10, 17)) & (midx != 11),
        "december_all": midx == 11,
    }
    gasrows = np.isin(klass, ["CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"])
    disp_path = BUNDLE / f"dispatch/{YEAR}_P1.parquet"
    dd = pd.read_parquet(disp_path, columns=["unit_id", "klass", "hour", "mw"])
    dmat = (
        dd.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(index=list(fa.unit_ids), columns=range(T))
        .fillna(0.0)
        .to_numpy(float)
    )
    out["dispatch_rows_matched"] = int(
        np.isfinite(dmat).all() and dmat.shape[0] == len(fleet)
    )

    cens = {}
    for name, mask in windows.items():
        hrs = np.where(mask)[0]
        c = cap[:, hrs]
        d = dmat[:, hrs]
        l = lam[hrs]
        # a gas tranche is IDLE-AND-IN-THE-MONEY if it is dispatching ~0 while
        # its own offer sits BELOW the clearing price: capacity the market
        # could have used at that price and the model did not.
        inmoney = (mc[:, hrs] < l[None, :] - TOL) & (c > 1.0)
        idle = d <= 0.01 * np.maximum(c, 1e-9)
        atbound = d >= 0.99 * np.maximum(c, 1e-9)
        gi = gasrows[:, None]
        cens[name] = {
            "hours": int(hrs.size),
            "mean_price": round(lw(l, w[hrs]), 2),
            "gas_cap_mw": round(float((c * gi).sum(axis=0).mean()), 0),
            "gas_disp_mw": round(float((d * gi).sum(axis=0).mean()), 0),
            "gas_idle_inmoney_mw": round(
                float((c * gi * inmoney * idle).sum(axis=0).mean()), 1
            ),
            "gas_atbound_mw": round(float((c * gi * atbound).sum(axis=0).mean()), 0),
            "gas_headroom_above_disp_mw": round(
                float(((c - d) * gi).sum(axis=0).mean()), 0
            ),
            "frac_cap_atbound": round(
                float((c * gi * atbound).sum() / max((c * gi).sum(), 1e-9)), 4
            ),
        }
    out["H2_bound_census"] = cens
    print("\n=== H-2  gas offer-stack state in each window (model P1, 2022) ===")
    hdr = (
        "window",
        "hours",
        "price",
        "gasCap",
        "gasDisp",
        "IDLE&IN-MONEY",
        "atBound",
        "headroom",
        "fracBound",
    )
    print("  {:<24s}{:>6s}{:>8s}{:>8s}{:>9s}{:>15s}{:>9s}{:>10s}{:>10s}".format(*hdr))
    for name, r in cens.items():
        print(
            f"  {name:<24s}{r['hours']:>6d}{r['mean_price']:>8.2f}"
            f"{r['gas_cap_mw']:>8.0f}{r['gas_disp_mw']:>9.0f}"
            f"{r['gas_idle_inmoney_mw']:>15.1f}{r['gas_atbound_mw']:>9.0f}"
            f"{r['gas_headroom_above_disp_mw']:>10.0f}"
            f"{r['frac_cap_atbound']:>10.4f}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

"""soco-75 zero-LP probe: average vs INCREMENTAL coal heat rate, SOCO econ tranches.

Measures, per SOCO coal unit-year 2019-2025, the incremental heat rate
d(heatInput)/d(grossLoad) above minimum load from the unit's own CAMPD hourly
CEMS, using the FROZEN construction of the registered carrier's derive
(``scripts/data/derive_campd_marginal_hr.derive_unit_bands``: steady-state hours,
LSL/HSL = p3/p97, normalized-quadratic I/O fit, econ_low at x=0.5, econ_high at
x=0.9), and compares it with the per-plant-year AVERAGE heat rate the SOCO
econ tranches are actually priced at (``campd_coal_heat_rates_SOCO.csv``
``heat_rate_gross``: sum(heatInput)/sum(grossLoad)). A linear OLS slope over the
econ range (x in [0.2, 1.0]) is reported alongside as a construction-robustness
check. Ratios are basis-free (both are gross), so the parasitic factor cancels.

Zero fitted parameters, SOCO-own data only. Reporting only; writes nothing.

    .venv/bin/python scripts/probes/_soco75_incremental_hr.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from derive_campd_marginal_hr import (  # noqa: E402
    HSL_PCT,
    LSL_PCT,
    UNIT_LEVEL_DIR,
    derive_unit_bands,
)

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402

PLANTS = {
    703: "Bowen", 6257: "Scherer", 6073: "Daniel", 26: "Gaston",
    3: "Barry", 641: "Crist", 6052: "Wansley", 6002: "Miller",
}
STATES = ("AL", "GA", "FL", "MS")
YEARS = tuple(range(2019, 2026))
# derive_unit_bands NaNs a multiple outside (0, 5); a 10 MMBtu/MWh divisor keeps
# coal (~9-11) inside that window without changing the fit.
BASE = 10.0
COAL_TOKENS = ("coal", "bituminous", "lignite", "anthracite", "petroleum coke")


def load() -> pd.DataFrame:
    """Steady-state coal unit-hours of the eight SOCO coal plants, 2019-2025."""
    frames = []
    cols = ["facilityId", "unitId", "grossLoad", "heatInput", "opTime",
            "primaryFuelInfo"]
    for st in STATES:
        for y in YEARS:
            p = UNIT_LEVEL_DIR / f"{st}_{y}.parquet"
            if not p.exists():
                continue
            d = pd.read_parquet(p, columns=cols)
            d["facilityId"] = d["facilityId"].astype(int)
            d = d[d["facilityId"].isin(PLANTS)]
            d["year"] = y
            frames.append(d)
    c = pd.concat(frames, ignore_index=True)
    fuel = c["primaryFuelInfo"].astype(str).str.lower()
    c = c[fuel.apply(lambda s: any(t in s for t in COAL_TOKENS))]
    # the carrier's own steady-state filter and the coal HR artifact's band
    op = (c["grossLoad"] > 0) & (c["heatInput"] > 0) & (c["opTime"] >= 0.99)
    c = c[op].copy()
    c["hr"] = c["heatInput"] / c["grossLoad"]
    return c[(c["hr"] >= 8.0) & (c["hr"] <= 25.0)]


def linear_econ_slope(u: pd.DataFrame) -> float:
    """OLS slope of heatInput on grossLoad over the econ range x in [0.2, 1]."""
    gl = u["grossLoad"].to_numpy(float)
    hi = u["heatInput"].to_numpy(float)
    lsl, hsl = np.percentile(gl, LSL_PCT), np.percentile(gl, HSL_PCT)
    x = (gl - lsl) / (hsl - lsl)
    m = (x >= 0.2) & (x <= 1.0)
    if m.sum() < 100:
        return float("nan")
    return float(np.polyfit(gl[m], hi[m], 1)[0])


def plant_year_ratios() -> pd.DataFrame:
    """Plant-year gen-weighted incremental/average ratios (quadratic lo/hi, linear)."""
    return _tables(verbose=False)


def _tables(verbose: bool) -> pd.DataFrame:
    """Build the unit-year and plant-year tables; print them when ``verbose``."""
    c = load()
    art = pd.read_csv(PROCESSED_DIR / "campd_coal_heat_rates_SOCO.csv")
    art = art[art["year"] > 0].set_index(["plant_code", "year"])
    rows = []
    for (f, uid, y), u in c.groupby(["facilityId", "unitId", "year"]):
        r = derive_unit_bands(u, BASE)  # x BASE below -> MMBtu/MWh gross
        if r is None:
            continue
        rows.append({
            "plant": PLANTS[f], "code": f, "unit": uid, "year": y,
            "hours": len(u), "hsl": r["cap"],
            "gross_mwh": u["grossLoad"].sum(),
            "avg_unit": u["heatInput"].sum() / u["grossLoad"].sum(),
            "marg_lo": r["marg_econ_low"] * BASE, "marg_hi": r["marg_econ_high"] * BASE,
            "marg_comm": r["marg_committed"] * BASE, "lin": linear_econ_slope(u),
        })
    pu = pd.DataFrame(rows)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_rows", 400)
    if verbose:
        print("=== unit-year (gross MMBtu/MWh) ===")
        print(pu.round(3).to_string(index=False))

    def agg(g: pd.DataFrame) -> pd.Series:
        w = g["gross_mwh"]
        out = {}
        for k in ("avg_unit", "marg_lo", "marg_hi", "lin"):
            m = g[k].notna()
            out[k] = np.average(g.loc[m, k], weights=w[m]) if m.any() else np.nan
        out["n_units"] = len(g)
        out["twh"] = w.sum() / 1e6
        return pd.Series(out)

    py = pu.groupby(["plant", "code", "year"]).apply(agg).reset_index()
    py["art_avg"] = [
        art["heat_rate_gross"].get((c_, y_), np.nan)
        for c_, y_ in zip(py["code"], py["year"])
    ]
    for k in ("marg_lo", "marg_hi", "lin"):
        py[f"{k}/avg"] = py[k] / py["art_avg"]
    if verbose:
        print("\n=== plant-year, gen-weighted (ratio to the artifact avg HR the econ"
              " tranche is priced at) ===")
        print(py.round(3).to_string(index=False))
        print("\n=== stability: per-plant ratio across years (mean / sd / min / max) ===")
        for k in ("marg_lo/avg", "marg_hi/avg", "lin/avg"):
            s = py.groupby("plant")[k].agg(["mean", "std", "min", "max", "count"])
            print(f"-- {k}\n{s.round(3).to_string()}")
    return py


def main() -> None:
    """Print unit-year and plant-year incremental/average HR tables."""
    _tables(verbose=True)


def main_greedy(years: list[int], basis: str, scope: str = "all") -> None:
    """Greedy of econ tranches re-priced at the measured INCREMENTAL heat rate.

    Arm: every above-min-load coal tranche (``_econlo``, ``_econhi``, and the
    ``_committed`` slab of a plant that carries a measured ``_mustrun`` floor, where
    ``_committed`` sits ABOVE minimum load) has its fuel component (mc - vom)
    scaled by the plant's incremental/average ratio (econ_low ratio, econ_high for
    ``_econhi``). A cycler's ``_committed`` slab IS its minimum-load block and keeps
    the average rate (it carries the no-load heat). ``basis``: ``year`` = same-year
    ratio, ``pooled`` = the plant's 2019-2025 mean (the forward construction).
    Reported baseline-differenced through soco-73's identical greedy instrument.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import _soco73_phase0 as p73

    py = plant_year_ratios()
    pooled = py.groupby("code")[["marg_lo/avg", "marg_hi/avg"]].mean()
    for y in years:
        fl = p73.rebuild(y, None)
        g0 = p73.greedy(y, fl)
        ids = fl["unit_ids"]
        mc = fl["mc"].copy()
        vom = fl["stash"]["vom"]
        plants = {int(fl["plant"][i]) for i, x in enumerate(ids) if x.startswith("COAL")}
        has_mr = {pc: any(x.endswith("_mustrun") and int(fl["plant"][i]) == pc
                          for i, x in enumerate(ids)) for pc in plants}
        moved = []
        for i, x in enumerate(ids):
            if not x.startswith("COAL"):
                continue
            pc = int(fl["plant"][i])
            if scope == "mustrun" and not has_mr[pc]:
                continue
            hi = x.endswith("_econhi")
            if not (x.endswith("_econlo") or hi
                    or (x.endswith("_committed") and has_mr[pc])):
                continue
            col = "marg_hi/avg" if hi else "marg_lo/avg"
            if basis == "pooled":
                if pc not in pooled.index:
                    continue
                r = float(pooled.loc[pc, col])
            else:
                m = py[(py.code == pc) & (py.year == y)]
                if m.empty or not np.isfinite(m[col].iloc[0]):
                    continue
                r = float(m[col].iloc[0])
            before = float(np.median(mc[i])) if mc.ndim == 2 else float(mc[i])
            mc[i] = vom[i] + (mc[i] - vom[i]) * r
            after = float(np.median(mc[i])) if mc.ndim == 2 else float(mc[i])
            moved.append((x.split("_", 3)[-1], round(r, 3), round(before, 2), round(after, 2)))
        arm = dict(fl, mc=mc)
        g = p73.greedy(y, arm)
        keys = set(g["delta"]) | set(g0["delta"])
        d = {k: g["delta"].get(k, 0.0) - g0["delta"].get(k, 0.0) for k in keys}
        pd_ = {p: g["plant_delta"].get(p, 0.0) - g0["plant_delta"].get(p, 0.0)
               for p in set(g["plant_delta"]) | set(g0["plant_delta"])}
        print(f"\n===== {y} [{basis}/{scope}]  tranches re-priced (tranche, ratio, $before, $after):")
        for t in moved:
            print("   ", t)
        print("  plant delta TWh " + " ".join(f"{p}:{v:+.3f}" for p, v in sorted(pd_.items())))
        print("  class delta TWh: " + "  ".join(
            f"{k} {v:+.3f}" for k, v in sorted(d.items()) if abs(v) > 1e-4))
        if y <= 2024:
            r0, n0, r1, n1 = p73.c4_coal(y, g["coal_delta_t"] - g0["coal_delta_t"])
            print(f"  C4 coal: keeper r={r0:.3f} nrmse={n0:.3f} -> arm~ r={r1:.3f} nrmse={n1:.3f}")
            print(p73.c1_rows(y, d).round(3).to_string(index=False))


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("mode", choices=["measure", "greedy"], nargs="?", default="measure")
    ap.add_argument("--basis", choices=["year", "pooled"], default="year")
    ap.add_argument("--scope", choices=["all", "mustrun"], default="all")
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    a = ap.parse_args()
    if a.mode == "measure":
        main()
    else:
        main_greedy(a.years, a.basis, a.scope)

"""SPP-51b session-B ADDENDUM instrument (ZERO LP): recompute every hour-matched number
in ``FINDING-spp-51b-2026-09-09-session-b.md`` on the CORRECTED SPP price clock.

SPP-51c (``PRECOMMIT-spp-51c-ADDENDUM-2026-09-09`` §A, routed SPP-51c R-1) established that
``data/raw/_validation-source/actual_lmp_hourly_SPP.parquet`` is indexed on UTC while the model's
frame is Central PREVAILING time -- 6 h in CST months, 5 h in CDT.  Session B's finding merged
separately and every model-vs-measured comparison in it is hour-matched, so all of them are
recomputed here beside the published (misaligned) values.

The MODEL side is not affected: prices are recovered as ``committed_actual + lmpDeltaHr`` and the
payload delta was written against the same misaligned actual, so the misalignment cancels and the
recovery returns the true model price either way.

This does NOT land the clock repair -- that is SPP-51c R-1, a scoring-basis change needing its own
pre-registration.  It reads ``data/raw`` and writes nothing.  The alignment is gated first by
reproducing SPP-51c's own ``rt_lw`` on both clocks.

usage:  uv run python docs/handoffs/spp51b/clock_recheck.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from prices import BANDS, model_price, system_demand  # noqa: E402

ACT = Path("data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
OUT = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "e7ea1db8-8d13-5aa9-9561-fc9c88bbd737/scratchpad/spp51b"
)
RUN = "2026-09-08-spp-50-rebaseline"
GAS = pd.read_csv(
    "data/raw/gas-prices/eia_delivered_gas_electric_power_by_state_monthly_2018-2026.csv"
)


def raw_actual(year):
    d = pd.read_parquet(ACT)
    return d[d.year == year].sort_values("hour")["rt"].to_numpy(float)


def offsets(year):
    """UTC -> Central PREVAILING: 6 h in CST months, 5 h in CDT (SPP-51c ADDENDUM §A)."""
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    dst = {
        2023: ("2023-03-12", "2023-11-05"),
        2024: ("2024-03-10", "2024-11-03"),
        2025: ("2025-03-09", "2025-11-02"),
    }[year]
    cdt = (idx >= pd.Timestamp(dst[0])) & (idx < pd.Timestamp(dst[1]))
    return np.where(cdt, 5, 6)


def corrected_actual(year):
    a = raw_actual(year)
    off = offsets(year)
    n = len(a)
    src = np.arange(n) + off[:n]
    out = np.full(n, np.nan)
    ok = src < n
    out[ok] = a[src[ok]]
    return out


def alignment_gate() -> None:
    """Reproduce SPP-51c ADDENDUM §A's ``rt_lw`` on both clocks before recomputing anything."""
    print("=" * 78)
    print(
        "0. ALIGNMENT GATE — rt_lw against SPP-51c ADDENDUM §A (must match before anything else)"
    )
    print("=" * 78)
    mis = {2023: 24.438, 2024: 24.531, 2025: 27.957}
    cor = {2023: 25.178, 2024: 25.497, 2025: 28.649}
    for y in (2023, 2024, 2025):
        lo = system_demand(y)
        a, c = raw_actual(y), corrected_actual(y)
        n = min(len(lo), len(a))
        m1 = np.isfinite(a[:n]) & np.isfinite(lo[:n])
        m2 = np.isfinite(c[:n]) & np.isfinite(lo[:n])
        print(
            f"  {y}: misaligned theirs {mis[y]:.3f} mine "
            f"{np.average(a[:n][m1], weights=lo[:n][m1]):.3f}   |   corrected theirs "
            f"{cor[y]:.3f} mine {np.average(c[:n][m2], weights=lo[:n][m2]):.3f}"
        )


alignment_gate()

print("=" * 78)
print("1. LOAD-BAND DECOMPOSITION — misaligned (as published) vs CORRECTED clock")
print("=" * 78)
for y in (2023, 2024, 2025):
    m = model_price(RUN, y)
    l = system_demand(y)
    n = min(len(m), len(l))
    rows = []
    for lbl, a in (("mis", raw_actual(y)), ("cor", corrected_actual(y))):
        aa = a[:n]
        ok = np.isfinite(m[:n]) & np.isfinite(aa) & np.isfinite(l[:n])
        pct = np.full(n, np.nan)
        pct[ok] = pd.Series(l[:n][ok]).rank(pct=True).to_numpy() * 100
        r = {}
        for lo, hi in BANDS:
            s = ok & (pct >= lo) & ((pct < hi) if hi < 100 else True)
            mm = np.average(m[:n][s], weights=l[:n][s])
            ac = np.average(aa[s], weights=l[:n][s])
            r[f"{lo}-{hi}"] = round(100 * (mm / ac - 1), 1)
        r["LW"] = round(
            100
            * (
                np.average(m[:n][ok], weights=l[:n][ok])
                / np.average(aa[ok], weights=l[:n][ok])
                - 1
            ),
            2,
        )
        rows.append(pd.Series(r, name=lbl))
    print(f"\n{y}  (err %, model vs actual)")
    print(pd.DataFrame(rows).to_string())

print("\n" + "=" * 78)
print("2. STEEPENING RATIO  MHR(>=95pct)/MHR(25-75pct)")
print("=" * 78)
for y in (2023, 2024, 2025):
    m = model_price(RUN, y)
    l = system_demand(y)
    n = min(len(m), len(l))
    out = {}
    for lbl, a in (
        ("measured mis", raw_actual(y)),
        ("measured cor", corrected_actual(y)),
    ):
        aa = a[:n]
        ok = np.isfinite(m[:n]) & np.isfinite(aa) & np.isfinite(l[:n])
        pct = np.full(n, np.nan)
        pct[ok] = pd.Series(l[:n][ok]).rank(pct=True).to_numpy() * 100
        mid = ok & (pct >= 25) & (pct < 75)
        top = ok & (pct >= 95)
        out[lbl] = round(
            np.average(aa[top], weights=l[:n][top])
            / np.average(aa[mid], weights=l[:n][mid]),
            4,
        )
        out["model"] = round(
            np.average(m[:n][top], weights=l[:n][top])
            / np.average(m[:n][mid], weights=l[:n][mid]),
            4,
        )
    print(f"  {y}: {out}")

print("\n" + "=" * 78)
print("3. MID-LOAD: base-cost MERIT ORDER vs actual vs the LP dual")
print("=" * 78)
KH = Path("results/calibration/spp43_screened_B/hourly")
for y in (2023, 2024, 2025):
    a = np.load(OUT / f"head_arrays_{y}.npz")
    mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
    dem = a["demand"]
    T = mc.shape[1]
    mg = a["min_gen"]
    availmw = pmax[:, None] * (av if av.ndim == 2 else av[None, :])
    head = np.maximum(availmw - (mg if mg.shape == availmw.shape else 0), 0)
    forced = mg.sum(axis=0) if mg.shape == availmw.shape else np.zeros(T)
    d = pd.read_parquet(KH / f"class_hourly_{y}.parquet")
    d = d[d["pass"] == "P1"]
    res = (
        d[d["klass"].astype(str).str.startswith(("CC", "CT", "ST", "COAL", "OTHER"))]
        .groupby("hour")["mw"]
        .sum()
        .sort_index()
        .to_numpy()[:T]
    )
    m = model_price(RUN, y)[:T]
    l = system_demand(y)[:T]
    for lbl, act in (("mis", raw_actual(y)[:T]), ("cor", corrected_actual(y)[:T])):
        ok = np.isfinite(m) & np.isfinite(act) & np.isfinite(l)
        pct = np.full(T, np.nan)
        pct[ok] = pd.Series(l[ok]).rank(pct=True).to_numpy() * 100
        mid = np.where(ok & (pct >= 25) & (pct < 75))[0]
        cl = np.empty(len(mid))
        for i, h in enumerate(mid):
            o = np.argsort(mc[:, h])
            cum = np.cumsum(head[o, h])
            j = int(np.searchsorted(cum, max(res[h] - forced[h], 0.0)))
            cl[i] = mc[o[min(j, len(o) - 1)], h]
        merit = float(np.nanmean(cl))
        lp = float(np.average(m[mid], weights=l[mid]))
        ac = float(np.average(act[mid], weights=l[mid]))
        if lbl == "mis":
            print(
                f"\n  {y}  merit ${merit:.2f}  LP ${lp:.2f}  wedge ${lp - merit:+.2f}"
            )
        print(
            f"      actual({lbl}) ${ac:.2f}   merit-vs-actual {100 * (merit / ac - 1):+.1f} %   "
            f"LP-vs-actual {100 * (lp / ac - 1):+.1f} %   gap ${lp - ac:.2f}"
        )

print("\n" + "=" * 78)
print("4. FUEL: one-lever arithmetic + R-5 Permian ceiling, corrected clock")
print("=" * 78)
PERM = {58835, 56326, 55065, 3482, 6193}
for y in (2023, 2024, 2025):
    a = np.load(OUT / f"head_arrays_{y}.npz")
    rows = pd.read_csv(OUT / f"head_rows_{y}.csv")
    mc, av, pmax = a["mc_base"], a["availability"], a["pmax"]
    hr, fuel, vom = a["heat_rate"], a["fuel_prices"], a["vom"]
    dem = a["demand"]
    T = mc.shape[1]
    availmw = pmax[:, None] * (av if av.ndim == 2 else av[None, :])
    m = model_price(RUN, y)[:T]
    l = system_demand(y)[:T]
    act = corrected_actual(y)[:T]
    gref = (
        float(
            GAS[(GAS.state.isin(["KS", "OK"])) & (GAS.year == y)].price_usd_mcf.mean()
        )
        / 1.036
    )
    ok = np.isfinite(m) & np.isfinite(act) & np.isfinite(l)
    pct = np.full(T, np.nan)
    pct[ok] = pd.Series(l[ok]).rank(pct=True).to_numpy() * 100
    isperm = np.isin(rows.plant_code.to_numpy(), list(PERM))
    grp = rows.plant_group.fillna("").astype(str).to_numpy()
    isgas = np.array([g.startswith(("CC", "CT", "ST_GAS")) for g in grp])
    for lbl, sel in (("MID", ok & (pct >= 25) & (pct < 75)), ("TOP", ok & (pct >= 95))):
        idx = np.where(sel)[0]
        near = np.abs(mc[:, idx] - m[idx][None, :]) <= 0.25
        w = near * availmw[:, idx]
        tot = w.sum()
        rw = w.sum(axis=1)
        mp = float(np.average(m[idx], weights=l[idx]))
        ac = float(np.average(act[idx], weights=l[idx]))
        hrw = float(np.average(hr, weights=rw))
        fw = float((w * fuel[:, idx]).sum() / tot)
        vw = float(np.average(vom, weights=rw))
        fg = float((w[isgas] * fuel[isgas][:, idx]).sum() / max(w[isgas].sum(), 1e-9))
        lev = (ac - vw) / max(hrw * fw, 1e-9)
        line = f"  {y} {lbl}: model ${mp:.2f} actual ${ac:.2f} ({100 * (mp / ac - 1):+.1f}%)  fuel-only lever x{lev:.4f}"
        line += (
            f"   gas rows ${fg:.3f} vs ref ${gref:.3f} ({100 * (fg / gref - 1):+.1f}%)"
        )
        if lbl == "MID":
            line += f"\n        R-5 Permian ceiling ${float(rw[isperm].sum() / tot) * hrw * fw:.2f} of a ${mp - ac:.2f} gap"
        print(line)

print("\n" + "=" * 78)
print("5. FLAT MULTIPLIER that zeroes C3a — corrected clock")
print("=" * 78)
for y in (2023, 2024, 2025):
    m = model_price(RUN, y)
    l = system_demand(y)
    a = corrected_actual(y)
    n = min(len(m), len(l), len(a))
    m, l, a = m[:n], l[:n], a[:n]
    ok = np.isfinite(m) & np.isfinite(a) & np.isfinite(l)
    k = np.average(a[ok], weights=l[ok]) / np.average(m[ok], weights=l[ok])
    pct = np.full(n, np.nan)
    pct[ok] = pd.Series(l[ok]).rank(pct=True).to_numpy() * 100
    r = {}
    for lo, hi in BANDS:
        s = ok & (pct >= lo) & ((pct < hi) if hi < 100 else True)
        mm = np.average(m[s], weights=l[s])
        ac = np.average(a[s], weights=l[s])
        r[f"{lo}-{hi}"] = f"{100 * (mm / ac - 1):+.1f}->{100 * (mm * k / ac - 1):+.1f}"
    print(f"  {y} (x{k:.4f}): " + "  ".join(f"{kk} {vv}" for kk, vv in r.items()))

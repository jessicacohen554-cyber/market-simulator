"""neiso-74 screen: is NEISO pumped-storage under-cycling a STORAGE-side defect?

The neiso-72 keeper leaves the post-split ``NG: PS`` column as the fleet's first
measured pumped-storage series: **1.932 TWh discharged in 2025** against the
keeper's endogenous **0.497 TWh** (~4x). The handoff names a storage-side lever
(dispatch adder / AS value / duration / RTE). Before any of that is admissible
we have to separate two candidate root causes, because rule 1 ``[R-STRUCT]``
forbids patching the second with a storage-side parameter:

  (H1) STORAGE-SIDE.  The model's storage physics or objective is wrong (energy
       capacity, RTE, an unmodelled non-arbitrage duty), so even facing the REAL
       price shape it would refuse to cycle.
  (H2) PRICE-SHAPE.   The model's storage physics is right and the model's own
       diurnal price spread is too narrow to clear the RTE hurdle. Then the
       defect is upstream (offer stack / merit order) and a storage-side knob
       would be a fitted patch on someone else's residual.

The decisive test is a **counterfactual price-taker arbitrage** on MEASURED
NEISO prices with the model's OWN storage physics (1,865.0 MW,
``PUMPED_STORAGE_DURATION_HOURS`` x power, ``PUMPED_STORAGE_RTE``, cyclic SOC).
It is the same LP the model solves, with the price vector swapped from model
duals to measured DA/RT LMPs, so any throughput difference is attributable to
the price shape alone.

  * If measured-price arbitrage also lands near 0.5 TWh -> H1: the real fleet
    cycles for reasons the arbitrage objective does not contain (reserves,
    regulation, self-schedule), and a storage-side identification is the lever.
  * If measured-price arbitrage lands near 1.9 TWh -> H2: the physics is fine
    and the model's price shape is the defect; the storage lever is refused.

Also reports, all measured and no-LP:
  * the ``NG: PS`` sign convention and coverage (gross discharge vs net),
  * the measured duty cycle (hours online, MW when online, diurnal shape) vs
    the keeper's bang-bang 636 h at full 1,865 MW,
  * the model-vs-measured diurnal price spread, so H2 can be sized directly.

Read-only over 2023-2025 (rule 20 ``[R-HOLDOUT]``: no year outside the training
window is touched). No LP solve, no bundle written.

Run:  uv run python scripts/probes/_neiso74_ps_cycling_screen.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))
if str(REPO / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO / "scripts"))

from market_sim.config.constants import (  # noqa: E402
    PUMPED_STORAGE_DURATION_HOURS,
    PUMPED_STORAGE_RTE,
)

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/neiso72_hy_window_B"
ISNE_930 = REPO / "data/raw/eia-930-hourly/ISNE hourly.parquet"
NEISO_PS_MW = 1865.0  # model/storage.py::load_eia860_pumped_storage, EIA-860 PS


def hdr(text: str) -> None:
    print(f"\n{'=' * 78}\n{text}\n{'=' * 78}")


# ---------------------------------------------------------------- measured 930
def ps_hourly(year: int) -> pd.Series | None:
    """Raw (un-interpolated) ``NG: PS`` hourly series for ISNE, local-year."""
    df = pd.read_parquet(ISNE_930)
    local = df["Local date"]
    df = df[(local.dt.year == year) & ~((local.dt.month == 2) & (local.dt.day == 29))]
    if df.empty or "NG: PS" not in df.columns:
        return None
    df = df.sort_values("UTC time")
    # "Local date" is date-only; the local clock hour lives in the 1-24 "Hour"
    # column (EIA's hour-ending convention), so hour-of-day must come from it.
    return pd.Series(
        pd.to_numeric(df["NG: PS"], errors="coerce").to_numpy(dtype=float),
        index=pd.Index(
            (pd.to_numeric(df["Hour"], errors="coerce").to_numpy(dtype=float) - 1) % 24,
            name="hour_ending_local",
        ),
        name="ps",
    )


def describe_measured(year: int) -> dict | None:
    s = ps_hourly(year)
    if s is None:
        return None
    cov = float(s.notna().mean())
    v = s.dropna()
    if v.empty:
        return {"year": year, "coverage": cov, "n": 0}
    pos = v[v > 1.0]
    neg = v[v < -1.0]
    out = {
        "year": year,
        "coverage": cov,
        "n": int(v.size),
        "twh_pos": float(pos.sum()) / 1e6,
        "twh_neg": float(neg.sum()) / 1e6,
        "h_pos": int(pos.size),
        "h_neg": int(neg.size),
        "max": float(v.max()),
        "min": float(v.min()),
        "mw_when_on_mean": float(pos.mean()) if pos.size else 0.0,
        "mw_when_on_p50": float(pos.median()) if pos.size else 0.0,
        "mw_when_on_p95": float(pos.quantile(0.95)) if pos.size else 0.0,
    }
    return out


# ------------------------------------------------------- measured NEISO prices
def measured_prices(year: int, kind: str) -> np.ndarray | None:
    """Dense 8760 hub price vector (chronological), or ``None``."""
    from data.derive_actual_lmp import neiso_zone_hourly  # type: ignore

    fr = neiso_zone_hourly(year, kind)
    if fr is None or "hub" not in fr.columns:
        return None
    ser = fr["hub"].dropna()
    if ser.empty:
        return None
    # Drop Feb 29 to match the model's 8760 calendar, then pad/trim.
    idx = ser.index
    keep = ~((idx.month == 2) & (idx.day == 29))
    arr = ser[keep].to_numpy(dtype=float)
    if arr.size < 8760:
        arr = np.concatenate([arr, np.full(8760 - arr.size, float(np.nanmean(arr)))])
    return arr[:8760]


# ------------------------------------------------- price-taker arbitrage (LP)
def arbitrage_throughput(
    price: np.ndarray,
    power_mw: float = NEISO_PS_MW,
    duration_h: float = PUMPED_STORAGE_DURATION_HOURS,
    rte: float = PUMPED_STORAGE_RTE,
    eps: float = 0.001,
) -> dict:
    """Perfect-foresight price-taker arbitrage, the model's own storage physics.

    Same formulation as ``model/storage.py``: charge/discharge bounded by
    ``power_mw``, SOC in ``[0, power_mw * duration_h]``, one-way efficiency
    ``sqrt(rte)`` on both legs, cyclic boundary, and the rule-9 ``[R-EPSILON]``
    0.001 $/MWh tiebreaker on charge+discharge. Solved directly on a CSC matrix
    through HiGHS (rule: no Pyomo/PuLP/scipy.optimize).

    Returns discharge/charge throughput (TWh) and the hours each leg is active.
    """
    import highspy
    from scipy import sparse

    T = int(price.size)
    e_cap = power_mw * duration_h
    eta = float(np.sqrt(rte))
    # Columns: Chg[0:T] | Dis[T:2T] | SOC[2T:3T]
    n = 3 * T
    # maximize price*Dis - price*Chg  ->  minimize price*Chg - price*Dis (+eps)
    cost = np.concatenate([price + eps, -price + eps, np.zeros(T)])
    lower = np.zeros(n)
    upper = np.concatenate(
        [np.full(T, power_mw), np.full(T, power_mw), np.full(T, e_cap)]
    )
    # SOC[t] - SOC[t-1] - eta*Chg[t] + Dis[t]/eta = 0   (cyclic at t=0)
    rows, cols, vals = [], [], []
    for t in range(T):  # constraint assembly only, not LP-inner-loop hot path
        prev = (t - 1) % T
        rows += [t, t, t, t]
        cols += [2 * T + t, 2 * T + prev, t, T + t]
        vals += [1.0, -1.0, -eta, 1.0 / eta]
    A = sparse.csc_matrix((vals, (rows, cols)), shape=(T, n))

    Ar = A.tocsr()  # HiGHS addRows wants row-wise starts/indices
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.addVars(n, lower, upper)
    h.changeColsCost(n, np.arange(n, dtype=np.int32), cost)
    h.addRows(
        T,
        np.zeros(T),
        np.zeros(T),
        Ar.nnz,
        Ar.indptr[:-1].astype(np.int32),
        Ar.indices.astype(np.int32),
        Ar.data.astype(float),
    )
    h.run()
    sol = np.asarray(h.getSolution().col_value, dtype=float)
    chg, dis = sol[:T], sol[T : 2 * T]
    return {
        "twh_dis": float(dis.sum()) / 1e6,
        "twh_chg": float(chg.sum()) / 1e6,
        "h_dis": int((dis > 1.0).sum()),
        "h_chg": int((chg > 1.0).sum()),
        "revenue_musd": float((price * dis - price * chg).sum()) / 1e6,
    }


# ------------------------------------------------------------- model dispatch
def model_ps(year: int) -> dict | None:
    p = KEEPER / "hourly" / f"storage_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    d = df[(df["pass"] == "P1") & (df["tech"] == "pumped_storage")]
    if d.empty:
        return None
    return {
        "twh_dis": float(d["discharge_mw"].sum()) / 1e6,
        "twh_chg": float(d["charge_mw"].sum()) / 1e6,
        "h_dis": int((d["discharge_mw"] > 1.0).sum()),
        "h_chg": int((d["charge_mw"] > 1.0).sum()),
    }


def model_price(year: int) -> np.ndarray | None:
    p = KEEPER / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return None
    df = pd.read_parquet(p)
    d = df[df["pass"] == "P1"]
    if d.empty:
        return None
    # Load-weighted system price (the LP's own energy-balance duals).
    g = d.groupby("hour").apply(
        lambda x: float(np.average(x["price"], weights=np.maximum(x["demand"], 1e-6))),
        include_groups=False,
    )
    return g.sort_index().to_numpy(dtype=float)


def spread_stats(price: np.ndarray, label: str) -> dict:
    """Daily max/min spread stats — the arbitrage hurdle is 1/RTE = 1.25x."""
    d = price[: 365 * 24].reshape(365, 24)
    lo, hi = d.min(axis=1), d.max(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(lo > 0.01, hi / lo, np.inf)
    return {
        "label": label,
        "mean": float(price.mean()),
        "daily_spread_$": float((hi - lo).mean()),
        "daily_ratio_p50": float(np.nanmedian(ratio[np.isfinite(ratio)])),
        "days_ratio_gt_hurdle": int((ratio > 1.0 / PUMPED_STORAGE_RTE).sum()),
    }


def main() -> int:
    hdr("neiso-74 PS cycling screen — measured NG:PS vs keeper vs price-taker LP")
    print(
        f"model physics: {NEISO_PS_MW:.1f} MW, duration {PUMPED_STORAGE_DURATION_HOURS:.1f} h "
        f"({NEISO_PS_MW * PUMPED_STORAGE_DURATION_HOURS / 1e3:.2f} GWh), RTE {PUMPED_STORAGE_RTE:.2f} "
        f"(one-way {np.sqrt(PUMPED_STORAGE_RTE):.4f}); arbitrage hurdle = "
        f"{1.0 / PUMPED_STORAGE_RTE:.3f}x"
    )

    hdr("1. measured EIA-930 NG:PS (sign convention + coverage + duty cycle)")
    meas: dict[int, dict] = {}
    for y in YEARS:
        m = describe_measured(y)
        if m is None or m.get("n", 0) == 0:
            print(f"  {y}: no NG:PS rows")
            continue
        meas[y] = m
        print(
            f"  {y}: coverage {m['coverage']:.3f}  +{m['twh_pos']:.3f} TWh in "
            f"{m['h_pos']} h  /  {m['twh_neg']:.3f} TWh in {m['h_neg']} h   "
            f"range [{m['min']:.0f}, {m['max']:.0f}] MW"
        )
        print(
            f"        MW when discharging: mean {m['mw_when_on_mean']:.0f}  "
            f"p50 {m['mw_when_on_p50']:.0f}  p95 {m['mw_when_on_p95']:.0f}  "
            f"(nameplate {NEISO_PS_MW:.0f})"
        )

    hdr("2. keeper (neiso72_hy_window_B) endogenous PS dispatch")
    mod: dict[int, dict] = {}
    for y in YEARS:
        m = model_ps(y)
        if m is None:
            continue
        mod[y] = m
        print(
            f"  {y}: discharge {m['twh_dis']:.4f} TWh in {m['h_dis']} h   "
            f"charge {m['twh_chg']:.4f} TWh in {m['h_chg']} h"
        )

    hdr("3. price-taker arbitrage on MEASURED prices (the H1/H2 discriminator)")
    for y in YEARS:
        for kind in ("da", "rt"):
            px = measured_prices(y, kind)
            if px is None:
                print(f"  {y} {kind}: no measured price")
                continue
            r = arbitrage_throughput(px)
            print(
                f"  {y} {kind.upper()}: {r['twh_dis']:.4f} TWh discharged in "
                f"{r['h_dis']} h (charge {r['twh_chg']:.4f} TWh / {r['h_chg']} h), "
                f"gross margin ${r['revenue_musd']:.1f}M"
            )

    hdr("4. price-taker arbitrage on MODEL prices (control for the same LP)")
    for y in YEARS:
        px = model_price(y)
        if px is None:
            continue
        r = arbitrage_throughput(px)
        print(
            f"  {y} MODEL: {r['twh_dis']:.4f} TWh discharged in {r['h_dis']} h "
            f"(keeper LP: {mod.get(y, {}).get('twh_dis', float('nan')):.4f} TWh / "
            f"{mod.get(y, {}).get('h_dis', -1)} h)"
        )

    hdr("5. diurnal price spread — model vs measured")
    for y in YEARS:
        rows = []
        px = model_price(y)
        if px is not None:
            rows.append(spread_stats(px, "model P1"))
        for kind in ("da", "rt"):
            m = measured_prices(y, kind)
            if m is not None:
                rows.append(spread_stats(m, f"measured {kind.upper()}"))
        for r in rows:
            print(
                f"  {y} {r['label']:<14} mean ${r['mean']:7.2f}  daily spread "
                f"${r['daily_spread_$']:7.2f}  ratio p50 {r['daily_ratio_p50']:.2f}  "
                f"days>hurdle {r['days_ratio_gt_hurdle']}/365"
            )

    hdr("6. measured diurnal duty shape (2025, the wholly-split year)")
    s = ps_hourly(2025)
    if s is not None:
        v = s.dropna()
        hod = np.asarray(v.index, dtype=int)
        by_hod = v.groupby(hod).mean()
        onfrac = (v > 1.0).groupby(hod).mean()
        print("  hour-of-day mean NG:PS MW (positive = discharge; local clock):")
        for lo in (0, 12):
            print(
                "   "
                + "  ".join(
                    f"{h:02d}:{float(by_hod.loc[h]):5.0f}" for h in range(lo, lo + 12)
                )
            )
        print("  hour-of-day fraction of hours online (>1 MW):")
        for lo in (0, 12):
            print(
                "   "
                + "  ".join(
                    f"{h:02d}:{float(onfrac.loc[h]):5.2f}" for h in range(lo, lo + 12)
                )
            )

    hdr("7. price-shape decomposition — where the model's spread is lost")
    for y in YEARS:
        px_m = model_price(y)
        px_a = measured_prices(y, "da")
        if px_m is None or px_a is None:
            continue
        dm = px_m[: 365 * 24].reshape(365, 24)
        da = px_a[: 365 * 24].reshape(365, 24)
        print(
            f"  {y}: level  model ${px_m.mean():6.2f}  vs DA ${px_a.mean():6.2f}  "
            f"({100 * (px_m.mean() / px_a.mean() - 1):+.1f}%)"
        )
        print(
            f"        daily MAX   model ${dm.max(axis=1).mean():7.2f}  vs DA "
            f"${da.max(axis=1).mean():7.2f}  ({100 * (dm.max(axis=1).mean() / da.max(axis=1).mean() - 1):+.1f}%)"
        )
        print(
            f"        daily MIN   model ${dm.min(axis=1).mean():7.2f}  vs DA "
            f"${da.min(axis=1).mean():7.2f}  ({100 * (dm.min(axis=1).mean() / da.min(axis=1).mean() - 1):+.1f}%)"
        )
        hod_m = dm.mean(axis=0)
        hod_a = da.mean(axis=0)
        print(
            f"        hour-of-day range  model ${hod_m.max() - hod_m.min():6.2f}  "
            f"vs DA ${hod_a.max() - hod_a.min():6.2f}   "
            f"(peak DA h{int(hod_a.argmax())} / model h{int(hod_m.argmax())}; "
            f"trough DA h{int(hod_a.argmin())} / model h{int(hod_m.argmin())})"
        )

    hdr("8. who absorbs the model's diurnal swing (2025 P1) — the flat-margin read")
    cp = KEEPER / "hourly" / "class_hourly_2025.parquet"
    sp = KEEPER / "hourly" / "system_2025.parquet"
    if cp.exists() and sp.exists():
        cd = pd.read_parquet(cp)
        cd = cd[cd["pass"] == "P1"].pivot(index="hour", columns="klass", values="mw")
        cd = cd.fillna(0.0)
        hod = cd.groupby(cd.index % 24).mean()
        sd = pd.read_parquet(sp)
        sd = sd[sd["pass"] == "P1"].groupby("hour")["demand"].sum().sort_index()
        dem = sd.groupby(sd.index % 24).mean()
        trough, peak = int(dem.idxmin()), int(dem.idxmax())
        print(
            f"  demand hour-of-day: trough h{trough} {dem[trough]:,.0f} MW -> peak "
            f"h{peak} {dem[peak]:,.0f} MW  (swing {dem[peak] - dem[trough]:,.0f} MW)"
        )
        for k in ("CC_REGULAR", "CT_PEAKER", "oil", "ST_GAS", "hydro"):
            if k not in hod.columns:
                continue
            lo, hi = float(hod.loc[trough, k]), float(hod.loc[peak, k])
            print(
                f"    {k:<11} h{trough} {lo:8,.0f} MW -> h{peak} {hi:8,.0f} MW  "
                f"(+{hi - lo:7,.0f} MW, {100 * (hi - lo) / max(dem[peak] - dem[trough], 1):5.1f}% "
                f"of the swing; online at the trough: {'YES' if lo > 1.0 else 'no'})"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

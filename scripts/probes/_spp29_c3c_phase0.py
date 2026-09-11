"""SPP-29 phase 0 — is SPP's absent C3c price tail reachable by any hourly mechanism?

ZERO LP. Every number in ``docs/handoffs/FINDING-spp-29-c3c-price-tail-2026-09-11.md``
is produced by this script from committed artifacts only:

- the keeper bundle ``results/calibration/spp27_span`` (``hourly/system_<year>.parquet``
  for the LP's realized max zonal dual, ``meta.json`` for the fleet reconstruction),
- ``data/raw/_validation-source/actual_lmp_hourly_{zonal_,}SPP.parquet`` (the RT/DA
  hub series the C3c benchmark ``frontend/data/backcast/tail/actual_tail.json`` is
  derived from),
- ``data/raw/SWPP_{region,fueltype}.parquet`` (EIA-930 metered demand / wind / solar),
- ``data/raw/spp-binding-constraints/RTBM-BC-YEARLY-<year>.csv.zip`` (SPP's published
  5-minute binding-constraint + shadow-price archive).

THE SCREENING STACK. ``_price()`` is a merit-order screen, not an LP: it sorts the
reconstructed fleet by hourly marginal cost, cumulates ``pmax x availability`` and
reads off the marginal unit against a net-load series. It ignores the network, the
commitment floors, the hydro budget and storage. It is VALIDATED against the keeper
LP in ``validate()`` — spearman 0.981 / 0.984 / 0.951 and an EXACT match on the
scored ``hours > $200`` count (0 / 5 / 0) — and it is deliberately LOOSE in the tail
(it omits storage discharge, so it prices tighter than the LP), which makes its
counterfactual an upper bound on what a perfect-quantity hourly LP could reach.

Rule 12 note: ``reconstruct_bundle_fleet`` is order-dependent across years within a
process for SPP (RESULT-spp27-span §9). This script builds ONE YEAR PER PROCESS via
``--year``; never loop years in one interpreter.

Usage:
    uv run python scripts/probes/_spp29_c3c_phase0.py --year 2025 --cache /tmp
    uv run python scripts/probes/_spp29_c3c_phase0.py --report --cache /tmp
    uv run python scripts/probes/_spp29_c3c_phase0.py --congestion --year 2024
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "spp27_span"
VSRC = REPO / "data" / "raw" / "_validation-source"
YEARS = (2023, 2024, 2025)

#: EIA-930 is published interval-ending UTC. Converting to a fixed UTC-6 and
#: shifting one hour back maximizes the correlation against the model's own
#: demand array (0.98369 in 2025, against 0.97547 unshifted) — measured, not
#: assumed. See ``align_930()``.
_TZ, _SHIFT = "Etc/GMT+6", -1


def _series_930(kind: str, code: str) -> pd.Series:
    f = REPO / "data" / "raw" / f"SWPP_{kind}.parquet"
    d = pd.read_parquet(f)
    col = "type" if kind == "region" else "fueltype"
    s = d[d[col] == code].set_index("period")["value_mwh"].sort_index()
    return s.tz_convert(_TZ)


def align_930(s: pd.Series, year: int) -> np.ndarray:
    """EIA-930 series -> the model's 8760 hour-of-year index."""
    v = s[s.index.year == year].values[:8760].astype(float)
    return np.roll(np.nan_to_num(v), _SHIFT)


def metered_net_load(year: int) -> np.ndarray:
    """SPP's own metered net load: 930 demand - wind - solar."""
    return (
        align_930(_series_930("region", "D"), year)
        - align_930(_series_930("fueltype", "WND"), year)
        - align_930(_series_930("fueltype", "SUN"), year)
    )


def actual_prices(year: int) -> tuple[pd.Series, pd.Series, pd.DataFrame]:
    """(hub-average RT, hub-average DA, per-hub RT) on the model's hour index.

    The hub average is the C3c benchmark basis: ``actual_lmp_hourly_SPP.rt`` and
    the two-hub mean of ``actual_lmp_hourly_zonal_SPP`` agree to 6.1e-05 $/MWh.
    """
    z = pd.read_parquet(VSRC / "actual_lmp_hourly_zonal_SPP.parquet")
    s = pd.read_parquet(VSRC / "actual_lmp_hourly_SPP.parquet")
    hubs = z[z.year == year].pivot_table(index="hour", columns="zone", values="rt")
    idx = range(8760)
    return (
        hubs.mean(axis=1).reindex(idx),
        s[s.year == year].set_index("hour").da.reindex(idx),
        hubs.reindex(idx),
    )


def build_year(year: int, cache: Path) -> dict:
    """Reconstruct the keeper's fleet for ONE year (no LP) and cache the arrays."""
    import sys

    sys.path.insert(0, str(REPO))
    sys.path.insert(0, str(REPO / "src"))
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    st, _ = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
    fa = st["fleet_arrays"]
    pmax = np.asarray(fa.pmax, dtype=float)
    out = {
        "mc": np.asarray(st["mc_base"]),
        "avail": pmax[:, None] * np.asarray(fa.availability, dtype=float),
        "pmax": pmax,
        "D": np.asarray(st["demand"], dtype=float).sum(axis=0),
        "W": (
            np.asarray(st["wind_cap"], dtype=float)[:, None]
            * np.asarray(st["wind_cf"], dtype=float)
        ).sum(axis=0),
        "S": (
            np.asarray(st["solar_cap"], dtype=float)[:, None]
            * np.asarray(st["solar_cf"], dtype=float)
        ).sum(axis=0),
    }
    np.save(cache / f"spp{year}.npy", out, allow_pickle=True)
    return out


def _price(mc: np.ndarray, avail: np.ndarray, net: np.ndarray) -> np.ndarray:
    """Merit-order screening price: the marginal unit's MC against ``net``.

    ``inf`` marks an hour whose net load exceeds the whole available stack —
    an infeasibility the LP would price at ``ISOConfig.voll``.
    """
    out = np.empty(8760)
    for t in range(8760):
        m, c = mc[:, t], avail[:, t]
        o = np.argsort(m)
        cs, ms = np.cumsum(c[o]), m[o]
        i = np.searchsorted(cs, net[t])
        out[t] = ms[i] if i < len(ms) else np.inf
    return out


def lp_max_zonal(year: int) -> np.ndarray:
    """The keeper LP's max zonal dual per hour — the quantity C3c scores."""
    s = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.pivot_table(index="hour", columns="zone", values="price").max(axis=1).values
    )


def congestion(year: int) -> None:
    """Does SPP's published congestion select the C3c tail hours? (It does not.)"""
    zf = (
        REPO
        / "data"
        / "raw"
        / "spp-binding-constraints"
        / f"RTBM-BC-YEARLY-{year}.csv.zip"
    )
    d = pd.read_csv(zf, usecols=["Interval", "Shadow Price", "Monitored Facility"])
    d["Interval"] = pd.to_datetime(d["Interval"], format="%m/%d/%Y %H:%M:%S")
    d["sp"] = pd.to_numeric(d["Shadow Price"], errors="coerce").fillna(0)
    b = d[d.sp.abs() > 0].copy()
    # SPP stamps RTBM intervals interval-ENDING, so 00:05 belongs to hour 0.
    b["hoy"] = (
        (b.Interval - pd.Timestamp(f"{year}-01-01 00:05:00")) // pd.Timedelta("1h")
    ).astype(int)
    g = (
        b.groupby("hoy")
        .agg(
            n_binding=("sp", "size"),
            n_fac=("Monitored Facility", "nunique"),
            rent=("sp", lambda s: s.abs().sum()),
            maxsp=("sp", lambda s: s.abs().max()),
        )
        .reindex(range(8760))
        .fillna(0)
    )
    rt, _, _ = actual_prices(year)
    tail = rt[rt > 200].index.values
    print(f"--- {year} RTBM congestion vs the {len(tail)} C3c tail hours ---")
    print(f"  hours with >=1 binding constraint: {int((g.n_binding > 0).sum())}/8760")
    for col in ("n_binding", "n_fac", "rent", "maxsp"):
        pctl = (g[col].values[None, :] < g[col].loc[tail].values[:, None]).mean(
            axis=1
        ) * 100
        top = set(g[col].nlargest(len(tail)).index)
        print(
            f"  {col:10s} tail-percentile median {np.median(pctl):5.1f} | "
            f"top-{len(tail)} overlap {len(top & set(tail.tolist())):2d}/{len(tail)} | "
            f"spearman vs RT price {g[col].corr(rt, method='spearman'):+.3f}"
        )


def report(cache: Path) -> None:
    """The FINDING's tables, every year, from the cached reconstructions."""
    tailjson = json.loads(
        (
            REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
        ).read_text()
    )["isos"]["SPP"]
    for year in YEARS:
        d = np.load(cache / f"spp{year}.npy", allow_pickle=True).item()
        mc, avail, pmax = d["mc"], d["avail"], d["pmax"]
        net_model = d["D"] - d["W"] - d["S"]
        net_met = metered_net_load(year)
        rt, da, hubs = actual_prices(year)
        tail = rt[rt > 200].index.values
        lp = lp_max_zonal(year)
        p_model, p_met = (
            _price(mc, avail, net_model),
            _price(mc, avail, net_met),
        )
        fin = np.isfinite(p_met)
        hub_cols = list(hubs.columns)
        headroom, need = [], []
        for t in tail:
            o = np.argsort(mc[:, t])
            cs, ms = np.cumsum(avail[:, t][o]), mc[:, t][o]
            headroom.append(cs[-1] - net_model[t])
            i200 = np.searchsorted(ms, 200.0)
            need.append((cs[i200 - 1] if i200 else 0.0) - net_model[t])
        n_met = int((p_met > 200).sum())
        ratio = n_met / len(tail)
        print(f"===== {year} =====")
        print(
            f"  A1 actual RT tail (hub avg > $200)      {len(tail)}"
            f"   [committed benchmark {tailjson[str(year)]['rt_gt']}]"
        )
        print(
            f"  A2 BOTH hubs > $200 within the tail     "
            f"{int(((hubs[hub_cols[0]] > 200) & (hubs[hub_cols[1]] > 200)).reindex(tail).sum())}"
            f"   median min-hub ${hubs.min(axis=1).reindex(tail).median():.2f}"
        )
        print(
            f"  A4 SPP's OWN hourly DA market > $200    {int((da > 200).sum())}"
            f"   DA annual max ${da.max():.2f}"
        )
        print(
            f"  A5 tail hours whose DA cleared < $100   "
            f"{int((da.reindex(tail) < 100).sum())}/{len(tail)}"
        )
        print(
            f"  A6 median RT-DA wedge in tail           "
            f"${(rt - da).reindex(tail).median():+.2f}"
            f"   (all hours ${(rt - da).median():+.2f})"
        )
        print(
            f"  B1 keeper LP hours > $200               {int((lp > 200).sum())}"
            f"   LP max ${lp.max():.4f}"
        )
        print(
            f"  B2 fleet MW with MC > $200 / max MC     "
            f"{pmax[mc.max(axis=1) > 200].sum():.1f} of {pmax.sum():.0f} MW"
            f" / ${mc.max():.2f}"
        )
        print(f"  B3 model headroom in tail hours         {np.median(headroom):.0f} MW")
        print(
            f"  B4 MW to remove to reach $200           {np.median(need):.0f} MW"
            f" = {np.median(np.asarray(need) / net_model[tail]) * 100:.1f}% of net load"
        )
        print(
            f"  C1 model - metered NET LOAD in tail     "
            f"{np.mean(net_model[tail] - net_met[tail]) / 1e3:+.2f} GW"
            f"   (all hours {np.mean(net_model - net_met) / 1e3:+.2f} GW)"
        )
        print(
            f"  D1 screen on MODEL net load > $200      {int((p_model > 200).sum())}"
            f"   (LP {int((lp > 200).sum())})"
            f"   spearman {pd.Series(p_model[fin]).corr(pd.Series(lp[fin]), method='spearman'):.3f}"
        )
        print(
            f"  D2 screen on METERED net load > $200    {n_met}"
            f"   (infeasible {int((~fin).sum())})   max ${np.max(p_met[fin]):.2f}"
        )
        print(
            f"  D3 C3c band on perfect quantities       {n_met}/{len(tail)}"
            f" = {ratio:.4f}x -> {'PASS' if 0.5 <= ratio <= 2.0 else 'FAIL'}"
        )
        print(
            f"  D4 implied markup over MC in tail       "
            f"${np.median(rt.values[tail] - np.where(fin[tail], p_met[tail], 2000)):.2f}"
            f"   ({np.median(rt.values[tail] / np.maximum(np.where(fin[tail], p_met[tail], 2000), 1)):.1f}x)"
        )
        print()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, choices=YEARS)
    ap.add_argument("--cache", type=Path, default=Path("/tmp"))
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--congestion", action="store_true")
    a = ap.parse_args()
    if a.congestion:
        congestion(a.year or 2024)
    elif a.report:
        report(a.cache)
    elif a.year:
        build_year(a.year, a.cache)
        print(f"cached {a.cache}/spp{a.year}.npy")
    else:
        ap.error("pass --year (build, one per process), --report, or --congestion")


if __name__ == "__main__":
    main()

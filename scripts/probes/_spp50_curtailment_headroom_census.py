"""SPP-50 (ZERO LP): Object A re-measured, and what it actually decomposes into.

The lane was chartered on "Object A" -- the coal<->CC elasticity SPP-47 filed as
SPP's largest C1 residual (``r = +0.885`` against gas price, slope
``+4.081 TWh`` per ``$/MMBtu``) -- with phase 0 required to re-fit it on the
benchmark SPP-49 corrected. It re-fits, and then it stops being the object:

1. **The elasticity survives in SIGN and collapses as a COEFFICIENT.** On the
   committed corrected bench the SPP-47 window reads ``r = +0.911`` but slope
   ``+2.209`` -- HALF what it read on the uncorrected actual -- while the keeper
   years alone read ``+9.942`` and all seven years ``+1.660``. A coefficient
   that moves 4.5x between windows describes the residual; it does not explain
   it.
2. **The coal<->CC pair does not close.** The antisymmetry is real
   (``r = -0.967`` over seven years) but the pair SUM is ``-3.365 TWh`` on
   average and negative in 6 of 7 years, so something underneath it is short.
3. **That something is exact.** Mean wind excess ``+10.1444 TWh`` against mean
   fossil miss ``-9.9895 TWh`` over the seven registered SPP years -- they
   cancel to ``+0.155 TWh``, 1.5 % of either.
4. **And the wind excess is not a defect in the wind INPUT.** It reconciles to
   the codebase's own published constant: ``_spp_wind_reference_curtailment_rate``
   = 0.0965013 gives a gross-up of x1.106808, and the model's
   delivered/actual wind ratio is 1.1068 in 2019 and 1.1015-1.1065 elsewhere.
   The bound is the measured UNCURTAILED POTENTIAL and it is correct
   (rules 13/14).
5. **The defect is that nothing spends it.** ``renewables.py`` states the
   construction's own precondition -- "The LP then curtails endogenously" -- and
   the LP curtails **0.00-0.48 %** of the potential against the 9.65 % it grossed
   up (MISO: **0.00 % in all six registered years**, to five decimals). This
   REPRODUCES SPP-51b/51c/58's 2023-2025 measurement at a different keeper and
   EXTENDS it to the 2019-2022 rung, where 2019 curtails nothing at all.

The dispatch consequence is legible at the other end: the model drives SPP's
whole PRB coal fleet to exactly 0.0 MW for 149-293 h/yr in six of seven years,
at a mean price of -$22.5..-$25.4 with wind at 84-88 % of its annual max, while
SPP's real PRB fleet never falls below 8.1-17.5 % of its own annual max in any
year.

NO MECHANISM IS TESTED HERE and no matrix cell letter moves (rule 28(b)). Every
number is read from committed artifacts: the registered run payloads, the
committed bench parts, the bundles' committed `hourly/` sidecars, CAMPD, and
EIA-930.

TWO PROBE-SIDE ARTIFACTS, recorded because both were plausible and both were
silently wrong -- the SPP-45/47 discipline applied to this lane's own work:

* **Leap years.** The model's calendar is a flat 8760 h; EIA-930's 2020 and 2024
  carry 8784. Compared index-for-index the hourly wind ``r`` reads 0.4262 /
  0.5046; dropping Feb 29 from the actual restores 0.9325 / 0.9350. The model
  was never misaligned -- the first pass of this probe was.
* **A corrupt EIA-930 hour in 2023.** The raw SWPP ``WND`` series carries one
  3,589,445 MWh hour against a ~35 GW fleet, which alone drove a naive 2023
  ``r`` of 0.1172. The bench builder already screens it: raw annual 106.639 TWh
  minus that hour is 103.050, which is the committed bench ``wind`` value
  103.0490. This probe adopts the benchmark's own screen rather than inventing
  one.

Traps honoured: SPP unit ids in both shapes where unit ids are read (SPP-45
trap (a)); CAMPD is STATE-scoped, so plants are attributed to SPP by EIA-860 BA
code through ``build_zone_lookup`` FIRST and CAMPD is read only for that set
(trap (d)); no path-swapped measured input is compared in-process, so the
``lru_cache`` hazard of trap (b) is never reached.

Run: ``PYTHONPATH=src python3 scripts/probes/_spp50_curtailment_headroom_census.py [leg]``
     leg in {elasticity, floor, headroom, census, all}; default all.
"""

from __future__ import annotations

import base64
import glob
import gzip
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.coal import coal_supply_by_iso  # noqa: E402
from market_sim.data.renewables import (  # noqa: E402
    _miso_wind_reference_curtailment_rate,
    _spp_wind_reference_curtailment_rate,
)
from market_sim.data.zone_assignment import build_zone_lookup  # noqa: E402

CAMPD = REPO / "data/raw/campd-unit-level"
BENCH = REPO / "frontend/data/backcast/bench/{iso}/{y}.json.gz"
RUNS = REPO / "frontend/data/backcast/runs/{rid}.js"
REGISTRY = REPO / "frontend/data/backcast/registry"

# SPP's two registered runs and the bundle each year's committed sidecars live in.
SPP_RUN = {
    y: "2026-09-19-spp-49-benchmark-membership" for y in (2019, 2020, 2021, 2022)
}
SPP_RUN.update(
    {y: "2026-09-16-spp-42-commitment-feasibility" for y in (2023, 2024, 2025)}
)
SPP_BUNDLE = {
    y: REPO / "results/calibration/spp49_benchmembership_span"
    for y in (2019, 2020, 2021, 2022)
}
SPP_BUNDLE.update(
    {y: REPO / "results/calibration/spp42_span_a" for y in (2023, 2024, 2025)}
)
SPP_YEARS = sorted(SPP_RUN)

FOSSIL = (
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_BIT",
    "COAL_WC",
    "COAL",
    "CC_REGULAR",
    "CC_CHP",
    "ST_GAS",
    "CT_PEAKER",
    "CT_CHP",
    "ST_CHP",
    "OTHER_FOSSIL",
    "oil",
)
# An EIA-930 hour above this is a reporting error, not weather: SPP's registered
# wind nameplate peaks at 35,934 MW (MMU ASOM 2025 p. 50).
_EIA930_IMPLAUSIBLE_MWH = 60_000.0

_payload_cache: dict[str, dict] = {}
_wnd_cache: dict[str, pd.DataFrame] = {}


# --------------------------------------------------------------------------- #
# committed-artifact readers
# --------------------------------------------------------------------------- #
def payload(run_id: str) -> dict:
    """The registered run's dashboard payload (carries the SCORED `gmModel`)."""
    if run_id not in _payload_cache:
        src = Path(str(RUNS).format(rid=run_id)).read_text()
        m = re.search(r'runGz\["([^"]+)"\]="([^"]+)"', src)
        _payload_cache[run_id] = json.loads(
            gzip.decompress(base64.b64decode(m.group(2)))
        )
    return _payload_cache[run_id]


def bench_class_full(iso: str, year: int) -> dict | None:
    """The committed bench part's ``classFull`` — the SCORED actual for C1."""
    path = Path(str(BENCH).format(iso=iso, y=year))
    if not path.exists():
        return None
    return json.loads(gzip.decompress(path.read_bytes()))["bench"]["classFull"]


def class_hourly(year: int, klass: str) -> np.ndarray:
    df = pd.read_parquet(SPP_BUNDLE[year] / f"hourly/class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    return (
        np.zeros(8760) if df.empty else df.sort_values("hour")["mw"].to_numpy()[:8760]
    )


def band_hourly(year: int, klass: str, band: str) -> np.ndarray:
    df = pd.read_parquet(SPP_BUNDLE[year] / f"hourly/class_band_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass) & (df["band"] == band)]
    return (
        np.zeros(8760) if df.empty else df.sort_values("hour")["mw"].to_numpy()[:8760]
    )


def system_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """(load-weighted zonal price, total demand) per hour."""
    d = pd.read_parquet(SPP_BUNDLE[year] / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    price = d.groupby("hour").apply(
        lambda g: float(np.average(g["price"], weights=np.maximum(g["demand"], 1e-9))),
        include_groups=False,
    )
    return price.sort_index().to_numpy()[:8760], d.groupby("hour")[
        "demand"
    ].sum().sort_index().to_numpy()[:8760]


def eia930_wind(year: int) -> tuple[np.ndarray, int]:
    """EIA-930 SWPP hourly WND on the model's 8760 calendar, screened as the bench screens it."""
    if "d" not in _wnd_cache:
        d = pd.read_parquet(REPO / "data/raw/SWPP_fueltype.parquet")
        d = d[d["fueltype"] == "WND"].copy()
        d["local"] = d["period"].dt.tz_convert("America/Chicago").dt.tz_localize(None)
        _wnd_cache["d"] = d
    d = _wnd_cache["d"]
    d = d[(d["local"] >= f"{year}-01-01") & (d["local"] < f"{year + 1}-01-01")]
    s = d.groupby("local")["value_mwh"].sum().sort_index()
    s = s.reindex(pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h"))
    bad = s > _EIA930_IMPLAUSIBLE_MWH
    s = s.mask(bad).interpolate().fillna(0.0)
    s = s[~((s.index.month == 2) & (s.index.day == 29))]  # the model's calendar is 8760
    return s.to_numpy()[:8760], int(bad.sum())


def spp_prb_plant_codes() -> set[int]:
    """SPP's PRB/sub-bituminous coal plants: BA-attributed FIRST, then coal-class filtered."""
    supply = coal_supply_by_iso("SPP")
    return {int(p) for p in build_zone_lookup("SPP")} & {
        int(p) for p, c in supply.items() if str(c).upper() in ("PRB", "SUB")
    }


def campd_fleet_hourly(codes: set[int], year: int) -> np.ndarray | None:
    """Hourly gross load for an ALREADY-ATTRIBUTED plant set (trap (d))."""
    parts = []
    for path in sorted(glob.glob(str(CAMPD / f"*_{year}.parquet"))):
        df = pd.read_parquet(path, columns=["facilityId", "date", "hour", "grossLoad"])
        df = df[df["facilityId"].astype("int64").isin(codes)]
        if not df.empty:
            parts.append(df)
    if not parts:
        return None
    df = pd.concat(parts, ignore_index=True)
    ts = pd.to_datetime(df["date"]) + pd.to_timedelta(df["hour"].astype(int), unit="h")
    s = df.assign(ts=ts).groupby("ts")["grossLoad"].sum().sort_index()
    s = s.reindex(
        pd.date_range(f"{year}-01-01", f"{year}-12-31 23:00", freq="h")
    ).fillna(0.0)
    s = s[~((s.index.month == 2) & (s.index.day == 29))]
    return s.to_numpy()[:8760]


def scored_miss(year: int, klass: str) -> tuple[float, float]:
    """(model TWh, actual TWh) on the SCORED basis: payload `gmModel` vs bench `classFull`."""
    gm = payload(SPP_RUN[year])["years"][str(year)]["gmModel"]
    cf = bench_class_full("SPP", year) or {}
    return float(gm.get(klass, 0.0)), float(cf.get(klass, 0.0))


# --------------------------------------------------------------------------- #
# leg: elasticity
# --------------------------------------------------------------------------- #
def leg_elasticity() -> None:
    from market_sim.data.eia923 import load_monthly_fuel_costs

    costs = load_monthly_fuel_costs()
    plants = frozenset(build_zone_lookup("SPP"))

    def vw(year: int, group: str) -> float:
        sub = costs[
            (costs["year"] == year)
            & (costs["fuel_group"] == group)
            & costs["plant_id"].isin(plants)
        ]
        q = float(sub["quantity"].sum())
        return (
            float((sub["price_per_mmbtu"] * sub["quantity"]).sum() / q)
            if q > 0
            else float("nan")
        )

    gas = {y: vw(y, "Natural Gas") for y in SPP_YEARS}
    coal = {y: vw(y, "Coal") for y in SPP_YEARS}
    m_coal, m_cc = {}, {}
    for y in SPP_YEARS:
        mm, aa = scored_miss(y, "COAL_PRB")
        m_coal[y] = mm - aa
        mm, aa = scored_miss(y, "CC_REGULAR")
        m_cc[y] = mm - aa

    print("## A — the elasticity, re-fit on the CORRECTED committed bench")
    print(
        f"{'year':6s}{'gas vw$':>9s}{'coal vw$':>10s}{'spread':>8s}{'COAL_PRB miss':>15s}"
        f"{'CC_REG miss':>13s}{'pair sum':>10s}"
    )
    for y in SPP_YEARS:
        print(
            f"{y:<6d}{gas[y]:9.3f}{coal[y]:10.3f}{gas[y] - coal[y]:8.3f}"
            f"{m_coal[y]:+15.4f}{m_cc[y]:+13.4f}{m_coal[y] + m_cc[y]:+10.4f}"
        )

    def ols(xs, ys):
        x, y = np.asarray(xs, float), np.asarray(ys, float)
        ok = np.isfinite(x) & np.isfinite(y)
        x, y = x[ok], y[ok]
        slope, icept = np.polyfit(x, y, 1)
        return float(slope), float(icept), float(np.corrcoef(x, y)[0, 1]), len(x)

    print("\n   OLS: COAL_PRB C1 miss (TWh) ~ SPP delivered gas price ($/MMBtu)")
    for tag, ys in [
        ("2019-2022 (SPP-47's window, corrected bench)", [2019, 2020, 2021, 2022]),
        ("2023-2025 (keeper years)", [2023, 2024, 2025]),
        ("ALL SEVEN registered years", SPP_YEARS),
    ]:
        s, b0, r, n = ols([gas[y] for y in ys], [m_coal[y] for y in ys])
        print(
            f"     {tag:44s} n={n}  r={r:+.3f}  slope={s:+.3f} TWh/$  zero-cross=${-b0 / s:.2f}"
        )
    print(
        "   (SPP-47 read r=+0.885, slope=+4.081 on the UNCORRECTED actual. The sign holds;"
    )
    print("    the coefficient does not — it moves 4.5x between windows.)")

    print(
        "\n   antisymmetry: corr(COAL_PRB miss, CC_REGULAR miss), and whether the pair CLOSES"
    )
    for tag, ys in [
        ("2019-2022", [2019, 2020, 2021, 2022]),
        ("2023-2025", [2023, 2024, 2025]),
        ("ALL SEVEN", SPP_YEARS),
    ]:
        a = np.array([m_coal[y] for y in ys])
        c = np.array([m_cc[y] for y in ys])
        print(
            f"     {tag:12s} r={float(np.corrcoef(a, c)[0, 1]):+.3f}"
            f"   mean pair sum={float(np.mean(a + c)):+.4f} TWh"
        )


# --------------------------------------------------------------------------- #
# leg: floor
# --------------------------------------------------------------------------- #
def leg_floor() -> None:
    codes = spp_prb_plant_codes()
    print(f"## B — the coal FLOOR. SPP PRB plant set: {len(codes)} plants\n")
    print(
        "   Scale-free basis (hourly MW / that side's OWN annual max), so the CAMPD-gross vs"
    )
    print("   EIA-923-net wedge cannot be doing the work.")
    print(
        f"{'year':6s}{'act min':>9s}{'act p1':>9s}{'act p5':>9s}{'mod min':>9s}{'mod p1':>9s}"
        f"{'mod p5':>9s}{'h mod=0':>9s}{'h<act p1':>10s}{'TWh below':>11s}{'C1 miss':>10s}"
    )
    for y in SPP_YEARS:
        raw = campd_fleet_hourly(codes, y)
        if raw is None:
            continue
        mod = class_hourly(y, "COAL_PRB")
        n = min(len(raw), len(mod))
        raw, mod = raw[:n], mod[:n]
        mm, aa = scored_miss(y, "COAL_PRB")
        act = raw * (aa * 1e6 / raw.sum())
        fa = np.percentile(act, [0, 1, 5]) / act.max()
        fm = np.percentile(mod, [0, 1, 5]) / mod.max()
        floor = (
            fa[1] * mod.max()
        )  # the real fleet's own p1 fraction, on the MODEL's own max
        below = mod < floor
        print(
            f"{y:<6d}{fa[0]:9.3f}{fa[1]:9.3f}{fa[2]:9.3f}{fm[0]:9.3f}{fm[1]:9.3f}{fm[2]:9.3f}"
            f"{int((mod < 1e-6).sum()):9d}{int(below.sum()):10d}"
            f"{float((floor - mod[below]).sum() / 1e6):11.4f}{mm - aa:+10.4f}"
        )

    print(
        "\n   WHAT THE ZERO-COAL HOURS ARE — they are not scattered, they are one market state:"
    )
    print(
        f"{'year':6s}{'h coal=0':>9s}{'h mustrun=0':>13s}{'mean price':>12s}{'mean netload':>14s}"
        f"{'wind / its max':>16s}"
    )
    for y in SPP_YEARS:
        coal = class_hourly(y, "COAL_PRB")
        mr = band_hourly(y, "COAL_PRB", "mustrun")
        wind, solar = class_hourly(y, "wind"), class_hourly(y, "solar")
        price, dem = system_hourly(y)
        z = coal < 1e-6
        if not z.any():
            print(
                f"{y:<6d}{0:9d}{int((mr < 1e-6).sum()):13d}{'—':>12s}{'—':>14s}{'—':>16s}"
            )
            continue
        nl = dem - wind - solar
        print(
            f"{y:<6d}{int(z.sum()):9d}{int((mr < 1e-6).sum()):13d}{price[z].mean():12.2f}"
            f"{nl[z].mean():14.0f}{wind[z].mean() / wind.max():16.3f}"
        )

    print(
        "\n   WHICH BAND CARRIES THE SWING (model TWh, 2020 -> 2022) — mustrun is FLAT, so this"
    )
    print("   is a merit-order question, not a commitment one:")
    for b in ("mustrun", "committed", "econlo", "econhi", "peak"):
        d = (
            band_hourly(2022, "COAL_PRB", b).sum()
            - band_hourly(2020, "COAL_PRB", b).sum()
        ) / 1e6
        print(f"     COAL_PRB {b:10s} {d:+8.4f} TWh")


# --------------------------------------------------------------------------- #
# leg: headroom
# --------------------------------------------------------------------------- #
def leg_headroom() -> None:
    rate, ryear = _spp_wind_reference_curtailment_rate()
    gross = 1.0 / (1.0 - rate)
    print("## C — the wind gross-up, and whether the LP spends it")
    print(
        f"   _spp_wind_reference_curtailment_rate = {rate:.7f} (through {ryear})"
        f"  ->  gross-up x{gross:.6f}"
    )
    print(
        "   renewables.py states the construction's own precondition: \"The LP then curtails"
    )
    print('   endogenously." This measures whether it does.\n')
    print(
        f"{'year':6s}{'wind model':>12s}{'wind actual':>12s}{'ratio':>9s}{'intended curt':>15s}"
        f"{'LP curt':>10s}{'spent':>8s}{'fossil miss':>13s}{'cancel':>9s}"
    )
    for y in SPP_YEARS:
        wm, wa = scored_miss(y, "wind")
        gm = payload(SPP_RUN[y])["years"][str(y)]["gmModel"]
        cf = bench_class_full("SPP", y) or {}
        foss = sum(float(gm.get(c, 0.0)) - float(cf.get(c, 0.0)) for c in FOSSIL)
        obs = wm / wa
        lp = 100.0 * (1.0 - obs / gross)
        print(
            f"{y:<6d}{wm:12.4f}{wa:12.4f}{obs:9.4f}{100 * rate:14.2f}%{lp:9.2f}%"
            f"{100 * lp / (100 * rate):7.1f}%{foss:+13.4f}{wm - wa + foss:+9.4f}"
        )

    ex = np.array(
        [scored_miss(y, "wind")[0] - scored_miss(y, "wind")[1] for y in SPP_YEARS]
    )
    fo = []
    for y in SPP_YEARS:
        gm = payload(SPP_RUN[y])["years"][str(y)]["gmModel"]
        cf = bench_class_full("SPP", y) or {}
        fo.append(sum(float(gm.get(c, 0.0)) - float(cf.get(c, 0.0)) for c in FOSSIL))
    print(
        f"\n   mean wind excess {ex.mean():+.4f} TWh · mean fossil miss {np.mean(fo):+.4f} TWh"
        f" · they cancel to {ex.mean() + np.mean(fo):+.4f} TWh"
        f" ({abs(100 * (ex.mean() + np.mean(fo)) / ex.mean()):.1f} % of either)"
    )

    print(
        "\n   CURTAILMENT-SHAPED OR FLAT? A pure scale defect gives a flat per-decile ratio."
    )
    print(
        f"{'year':6s}{'screened h':>11s}{'hourly r':>10s}{'d1-d5 ratio':>13s}"
        f"{'d8-d10 ratio':>14s}{'rise':>8s}{'d8-d10 share of excess':>24s}"
    )
    for y in SPP_YEARS:
        act, nbad = eia930_wind(y)
        mod = class_hourly(y, "wind")
        n = min(len(act), len(mod))
        act, mod = act[:n], mod[:n]
        dec = np.array_split(np.argsort(act), 10)
        ratios = np.array([mod[i].mean() / max(act[i].mean(), 1e-9) for i in dec])
        share = np.array([(mod[i] - act[i]).sum() for i in dec])
        print(
            f"{y:<6d}{nbad:11d}{float(np.corrcoef(mod, act)[0, 1]):10.4f}{ratios[:5].mean():13.3f}"
            f"{ratios[7:].mean():14.3f}{ratios[7:].mean() - ratios[:5].mean():+8.3f}"
            f"{100 * share[7:].sum() / share.sum():23.1f}%"
        )


# --------------------------------------------------------------------------- #
# leg: census
# --------------------------------------------------------------------------- #
def leg_census() -> None:
    print(
        "## D — cross-ISO census (rule 25: a census informs where to look; NO verdict transfers)"
    )
    runs: dict[str, list] = {}
    for f in sorted(glob.glob(str(REGISTRY / "*.json"))):
        d = json.loads(Path(f).read_text())
        if d.get("iso"):
            runs.setdefault(d["iso"], []).append(
                (os.path.basename(f)[:-5], d.get("years") or [])
            )
    print(
        f"{'ISO':7s}{'n yrs':>6s}{'wind ratio mean':>17s}{'sd':>9s}{'min':>9s}{'max':>9s}"
        f"{'mean excess':>13s}{'mean fossil':>13s}{'cancel':>9s}"
    )
    for iso in sorted(runs):
        rr, ee, ff = [], [], []
        for rid, yrs in runs[iso]:
            if not Path(str(RUNS).format(rid=rid)).exists():
                continue
            d = payload(rid)
            for y in yrs:
                cf = bench_class_full(iso, y)
                gm = (d["years"].get(str(y)) or {}).get("gmModel") or {}
                if not cf or float(cf.get("wind", 0.0)) < 1.0:
                    continue
                wm, wa = float(gm.get("wind", 0.0)), float(cf["wind"])
                rr.append(wm / wa)
                ee.append(wm - wa)
                ff.append(
                    sum(float(gm.get(c, 0.0)) - float(cf.get(c, 0.0)) for c in FOSSIL)
                )
        if not rr:
            continue
        r = np.array(rr)
        print(
            f"{iso:7s}{len(r):6d}{r.mean():17.4f}{r.std(ddof=1) if len(r) > 1 else 0.0:9.4f}"
            f"{r.min():9.4f}{r.max():9.4f}{np.mean(ee):+13.3f}{np.mean(ff):+13.3f}"
            f"{np.mean(ee) + np.mean(ff):+9.3f}"
        )
    srate, _ = _spp_wind_reference_curtailment_rate()
    mrate, _ = _miso_wind_reference_curtailment_rate()
    print(
        f"\n   SPP gross-up  x{1 / (1 - srate):.6f} (rate {srate:.6f})  vs observed mean ratio above"
    )
    print(
        f"   MISO gross-up x{1 / (1 - mrate):.6f} (rate {mrate:.6f})  — MISO's observed ratio is"
    )
    print(
        "   1.05147 in ALL SIX registered years with sd 0.0000: the LP curtails NOTHING there."
    )
    print("   MISO's number is reported, not acted on — it is MISO's lane's (rule 25).")


LEGS = {
    "elasticity": leg_elasticity,
    "floor": leg_floor,
    "headroom": leg_headroom,
    "census": leg_census,
}


def main() -> None:
    leg = sys.argv[1] if len(sys.argv) > 1 else "all"
    for name, fn in LEGS.items():
        if leg in ("all", name):
            fn()
            print()


if __name__ == "__main__":
    main()

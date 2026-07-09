"""ERCOT ercot51 coal over-commitment / online-capability-wedge diagnostic.

Reproduces + extends the per-plant coal CF comparison from the coal-availability
thread (model dispatch CF vs CAMPD actual CF, all years). NO SOLVE — reads a
solved baseline bundle's ``dispatch/<year>_P1.parquet`` (keeper config) against
the CAMPD actuals (built via run_calibration_full._campd_hourly_frame, the same
net-MW frame the bundle persists as its shared CAMPD input).

Establishes, per coal plant and per supply class (PRB / lignite):
  * mean CF, hrs>0.8, annual energy (TWh) — model vs actual, and the gaps
  * tight-hour (net-load >= p95) coal online — model vs actual over-commitment
  * 2023 missed-tail-hour wedge: hours where the model's load-weighted dual is
    < $200 but actual RT SCED > $200 — how much coal the model holds online
    there vs CEMS (the freed headroom a coal cycling fix would expose).

Usage: python scripts/probes/_ercot51_coal_cf_diag.py results/calibration/<baseline_bundle>
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import (  # noqa: E402
    _campd_hourly_frame,
    _parasitic_factor_map,
)

from market_sim.data.coal import coal_supply_class  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
BINCSV = REPO / "data" / "raw" / "reference" / "custom-bin-assignments.csv"
ACTUAL_LMP = (
    REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
)
YEARS = (2023, 2024, 2025)
THR = 200.0


def coal_nameplate() -> dict[int, float]:
    """{plant_code: nameplate_MW} for the 10 ERCOT coal plants."""
    df = pd.read_csv(BINCSV)
    c = df[df["Plant_Group"] == "COAL"]
    return {int(r.Plant_Code): float(r.Nameplate_MW) for r in c.itertuples(index=False)}


def load_actual_coal(year: int, names: dict[int, float]) -> pd.DataFrame:
    """CAMPD actual net-MW hourly for the coal plants -> (plant_code, hour, mw).

    Uses the SAME parasitic factor map the solve persists as its shared CAMPD
    input, so model and actual are compared on identical net-MW definitions.
    """
    factors = _parasitic_factor_map()
    frame = _campd_hourly_frame(year, "ERCOT", factors, 8760)
    if frame is None:
        raise SystemExit(f"no CAMPD frame for {year}")
    frame = frame[frame["plant_id"].isin(names)].copy()
    frame = frame.rename(columns={"plant_id": "plant_code", "net_mw": "mw"})
    return frame[["plant_code", "hour", "mw"]]


def load_model_coal(bundle: Path, year: int) -> pd.DataFrame:
    """Model P1 dispatch aggregated to (plant_code, hour, mw) for coal fuel."""
    d = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    if "pass" in d.columns:
        d = d[d["pass"] == "P1"]
    coal = d[d["fuel"].astype(str).str.lower() == "coal"]
    agg = coal.groupby(["plant_code", "hour"], observed=True)["mw"].sum().reset_index()
    return agg


def model_price(bundle: Path, year: int) -> tuple[np.ndarray, np.ndarray | None, str]:
    """Model hourly price + optional demand.

    Prefers ``system.parquet`` (load-weighted energy-balance dual + zonal
    demand). Falls back to the dispatch frame's per-generator ``lmp`` reduced
    to max-across-zones (the C3c energy-only tail metric) when the full run has
    not yet written ``system.parquet``; demand is then ``None``.
    """
    syspath = bundle / "system.parquet"
    if syspath.exists():
        sysdf = pd.read_parquet(syspath)
        if "pass" in sysdf.columns:
            sysdf = sysdf[sysdf["pass"] == "P1"]
        sy = sysdf[sysdf["year"] == year]
        num = np.zeros(8760)
        dem_h = np.zeros(8760)
        for _z, zg in sy.groupby("zone", observed=True):
            h = zg["hour"].to_numpy(int)
            num[h] += zg["price"].to_numpy(float) * zg["demand"].to_numpy(float)
            dem_h[h] += zg["demand"].to_numpy(float)
        price_h = np.divide(num, dem_h, out=np.full(8760, np.nan), where=dem_h > 0)
        return price_h, dem_h, "dual"
    # dispatch-lmp fallback: max zonal lmp per hour
    d = pd.read_parquet(bundle / "dispatch" / f"{year}_P1.parquet")
    if "pass" in d.columns:
        d = d[d["pass"] == "P1"]
    zl = d.groupby(["zone", "hour"], observed=True)["lmp"].first().reset_index()
    price_h = np.full(8760, -np.inf)
    for _z, zg in zl.groupby("zone", observed=True):
        h = zg["hour"].to_numpy(int)
        price_h[h] = np.maximum(price_h[h], zg["lmp"].to_numpy(float))
    price_h[price_h == -np.inf] = np.nan
    return price_h, None, "lmp"


def cf_stats(mw: np.ndarray, cap: float) -> tuple[float, int, float]:
    """(mean CF, hrs with CF>0.8, annual TWh) for an 8760 MW series."""
    cf = np.clip(mw / cap, 0, None)
    return float(cf.mean()), int((cf > 0.8).sum()), float(mw.sum() / 1e6)


def pivot_hourly(df: pd.DataFrame, names: dict[int, float]) -> dict[int, np.ndarray]:
    """{plant_code: 8760 MW array} padded to 8760 hours."""
    out = {}
    for pc, g in df.groupby("plant_code", observed=True):
        arr = np.zeros(8760)
        h = g["hour"].to_numpy(int)
        m = h < 8760
        arr[h[m]] = g["mw"].to_numpy(float)[m]
        out[int(pc)] = arr
    return out


def klass_of(pc: int) -> str:
    sc = coal_supply_class(pc)
    return "lignite" if sc == "lignite" else "prb"


def run(bundle: Path) -> None:
    names = coal_nameplate()
    lmp = pd.read_parquet(ACTUAL_LMP)
    print(f"\n===== ERCOT coal over-commitment diagnostic :: {bundle.name} =====")
    for year in YEARS:
        dpath = bundle / "dispatch" / f"{year}_P1.parquet"
        if not dpath.exists():
            print(f"\n[{year}] no dispatch parquet yet — skipping")
            continue
        model = pivot_hourly(load_model_coal(bundle, year), names)
        actual = pivot_hourly(load_actual_coal(year, names), names)

        print(f"\n----- {year} : per-plant CF (model vs actual) -----")
        print(
            f"{'plant':>6} {'name/class':<14} {'cap':>7} "
            f"{'mCF':>5}{'aCF':>5} {'m>.8':>6}{'a>.8':>6} {'gap>.8':>7} "
            f"{'mTWh':>6}{'aTWh':>6}"
        )
        rows = []
        for pc in sorted(
            names,
            key=lambda p: (
                -(
                    cf_stats(model.get(p, np.zeros(8760)), names[p])[1]
                    - cf_stats(actual.get(p, np.zeros(8760)), names[p])[1]
                )
            ),
        ):
            cap = names[pc]
            mcf, m80, mtwh = cf_stats(model.get(pc, np.zeros(8760)), cap)
            acf, a80, atwh = cf_stats(actual.get(pc, np.zeros(8760)), cap)
            rows.append(
                (pc, klass_of(pc), cap, mcf, acf, m80, a80, m80 - a80, mtwh, atwh)
            )
            print(
                f"{pc:>6} {klass_of(pc):<14} {cap:>7.0f} "
                f"{mcf:>5.2f}{acf:>5.2f} {m80:>6d}{a80:>6d} {m80 - a80:>+7d} "
                f"{mtwh:>6.2f}{atwh:>6.2f}"
            )

        # class aggregates
        print(f"\n----- {year} : class aggregates -----")
        for kl in ("prb", "lignite"):
            pcs = [pc for pc in names if klass_of(pc) == kl]
            cap = sum(names[pc] for pc in pcs)
            msum = np.sum([model.get(pc, np.zeros(8760)) for pc in pcs], axis=0)
            asum = np.sum([actual.get(pc, np.zeros(8760)) for pc in pcs], axis=0)
            mcf, m80, mtwh = cf_stats(msum, cap)
            acf, a80, atwh = cf_stats(asum, cap)
            print(
                f"  {kl:<8} cap {cap / 1e3:5.1f} GW | model CF {mcf:.2f} hrs>0.8 {m80:5d} "
                f"{mtwh:5.1f}TWh | actual CF {acf:.2f} hrs>0.8 {a80:5d} {atwh:5.1f}TWh"
            )

        # tight-hour (net-load p95) over-commitment: use actual coal-fleet total
        # as a proxy for tightness ordering is unavailable without system.parquet;
        # instead rank hours by ACTUAL coal fleet output (tight hours = fleet ran
        # hardest) AND by model dual if system.parquet present.
        coal_model_tot = np.sum([model.get(pc, np.zeros(8760)) for pc in names], axis=0)
        coal_actual_tot = np.sum(
            [actual.get(pc, np.zeros(8760)) for pc in names], axis=0
        )
        # Model price series + optional demand. Prefer system.parquet
        # (load-weighted dual + demand); fall back to the dispatch frame's
        # per-gen ``lmp`` (max-across-zones, the C3c energy-only tail metric)
        # when the full run hasn't written system.parquet yet.
        price_h, dem_h, price_src = model_price(bundle, year)

        aly = lmp[lmp["year"] == year]
        rt = np.full(8760, np.nan)
        rh = aly["hour"].to_numpy(int)
        rt[rh[rh < 8760]] = aly["rt"].to_numpy(float)[rh < 8760]

        # tightness selector: demand p95 if available, else actual-RT p95
        if dem_h is not None:
            tight_key, loose_key = dem_h, dem_h
            tlabel = "demand"
        else:
            tight_key = np.nan_to_num(rt, nan=-np.inf)
            loose_key = np.nan_to_num(rt, nan=np.inf)
            tlabel = "actualRT"
        tight = tight_key >= np.nanpercentile(tight_key[np.isfinite(tight_key)], 95)
        loose = loose_key <= np.nanpercentile(loose_key[np.isfinite(loose_key)], 25)
        print(
            f"\n----- {year} : tight/loose hours (by {tlabel}, price_src={price_src}) -----"
        )
        print(
            f"  tight (>=p95, n={int(tight.sum())}): coal online "
            f"model {coal_model_tot[tight].mean():6.0f} vs actual {coal_actual_tot[tight].mean():6.0f} MW "
            f"(delta {coal_model_tot[tight].mean() - coal_actual_tot[tight].mean():+.0f})"
        )
        print(
            f"  loose (<=p25, n={int(loose.sum())}): coal online "
            f"model {coal_model_tot[loose].mean():6.0f} vs actual {coal_actual_tot[loose].mean():6.0f} MW "
            f"(delta {coal_model_tot[loose].mean() - coal_actual_tot[loose].mean():+.0f})"
        )

        # missed-tail-hour wedge (acute target): model price < THR but actual RT > THR.
        missed = np.nan_to_num(price_h, nan=-np.inf) < THR
        missed &= np.nan_to_num(rt, nan=-np.inf) > THR
        nmiss = int(missed.sum())
        print(
            f"\n----- {year} : missed tail hours (model {price_src}<${THR:.0f} & actual RT>${THR:.0f}) -----"
        )
        print(f"  n_missed = {nmiss}")
        if nmiss:
            print(
                f"  in missed hrs: coal online model {coal_model_tot[missed].mean():6.0f} "
                f"vs actual {coal_actual_tot[missed].mean():6.0f} MW "
                f"(model over-commit {coal_model_tot[missed].mean() - coal_actual_tot[missed].mean():+.0f} MW "
                f"= headroom a coal cycling fix frees)"
            )
            print(
                f"  model price in missed hrs: mean ${np.nanmean(price_h[missed]):.1f} "
                f"(actual RT mean ${np.nanmean(rt[missed]):.1f})"
            )


if __name__ == "__main__":
    for b in sys.argv[1:]:
        run(Path(b))

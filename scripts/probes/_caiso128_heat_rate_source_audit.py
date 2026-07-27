"""caiso-128 derive: where the model's offer heat rate comes from, and how far
it sits from the plant's own measured CEMS rate — per class, per ISO.

TASK 1 of the caiso-128 CT offer-accuracy lane. Measurement-only (NO solve,
nothing armed). The owner lead nominated the ``HEAT_RATE_BINS`` fuel x vintage
fallback as the suspect; this instrument tests that lead and reports the actual
provenance split.

The chain under test (read off the code, then measured here):

* ``data/raw/eia-860/eia860_generators.parquet`` carries a ``heat_rate`` column;
  the EIA-860 Generator_Y sheets themselves carry **no heat rate at all**.
* ``scripts/data/process_eia860._join_egrid_heat_rate`` fills that column from
  **eGRID PLNT23 ``PLHTRT``** — a plant-level, annual, all-fuel average
  (PLHTIAN / PLNGENAN), mapped onto every generator at the plant.
* ``fleet/eia860._rows_to_generators`` prefers that value and falls back to
  ``HEAT_RATE_BINS[fuel_type][efficiency_bin]`` only when it is missing.
* ``fleet/eia860._egrid_boundary_hr_repairs`` reconciles bad eGRID rates, but is
  scoped to ``Natural Gas Fired Combined Cycle`` — no simple-cycle plant is ever
  repaired.

Three quantities are compared per plant-year, all from primary sources:

``egrid23`` / ``egrid24``
    ``PLHTRT`` from the 2023 and 2024 eGRID vintages (Btu/kWh -> MMBtu/MWh).
    ``egrid23`` is what the model actually offers on, in every modeled year.
``hr_all``
    CAMPD annual heat input / gross load over all generating hours — the
    CEMS-basis analogue of eGRID's annual average (startup + part-load fuel in
    the numerator, so it is NOT an energy-offer rate).
``hr_load``
    CAMPD heat input / gross load restricted to full-clock hours
    (``opTime >= 0.99``) above half the plant's observed peak — the
    **loading-conditional** rate an energy offer should carry. Startup fuel
    belongs in the startup cost, not in the energy offer, so this is the basis
    the offer curve wants.

Also reported: the gross->net boundary ratio implied by CEMS annual gross load
against eGRID's own ``PLNGENAN`` net generation, because the model's ``pmax`` is
net summer capability while CEMS ``grossLoad`` is gross — the one real basis
mismatch between the incumbent and the candidate input.

Usage:
    PYTHONPATH=.:src .venv/bin/python \\
        scripts/probes/_caiso128_heat_rate_source_audit.py --year 2024
    ... --iso CAISO ERCOT PJM MISO NYISO NEISO      # cross-ISO scope check
    ... --iso CAISO --plants                        # per-plant CT detail
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CAMPD_UNIT = REPO / "data" / "raw" / "campd-unit-level"
CAMPD_FAC = REPO / "data" / "raw" / "campd-facility-level"
EGRID_DIR = REPO / "data" / "raw" / "fleet-egrid"
# Loading-conditional basis: full-clock hours only (a partial hour carries the
# start's fuel against a fraction of the energy) above half the observed peak.
OPTIME_MIN = 0.99
LOAD_FRAC_MIN = 0.5
CEMS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_CHP", "CT_PEAKER", "ST_GAS", "COAL")


def egrid_plant_rates(vintage: int) -> pd.DataFrame:
    """Return ``ORISPL, hr, net_mwh`` from an eGRID vintage's plant sheet.

    ``hr`` is ``PLHTRT`` converted Btu/kWh -> MMBtu/MWh and filtered to the same
    3,000-30,000 Btu/kWh plausibility window ``process_eia860`` applies, so the
    2023 column reproduces exactly what the model fleet carries.
    """
    name = {
        2022: "egrid2022_data.xlsx",
        2023: "egrid2023_data_rev2.xlsx",
        2024: "egrid2024_data.xlsx",
    }[vintage]
    path = EGRID_DIR / name
    if not path.exists():
        return pd.DataFrame(columns=["plant_code", "hr", "net_mwh"])
    sheet = f"PLNT{str(vintage)[2:]}"
    frame = pd.read_excel(path, sheet_name=sheet, skiprows=1)
    key = next(c for c in frame.columns if str(c).upper().startswith("ORISPL"))
    hrc = next(c for c in frame.columns if "HTRT" in str(c).upper())
    genc = next((c for c in frame.columns if "NGENAN" in str(c).upper()), None)
    hr = pd.to_numeric(frame[hrc], errors="coerce")
    out = pd.DataFrame(
        {
            "plant_code": pd.to_numeric(frame[key], errors="coerce"),
            "hr": hr.where((hr >= 3_000) & (hr <= 30_000)) / 1e3,
            "net_mwh": (
                pd.to_numeric(frame[genc], errors="coerce")
                if genc
                else np.nan
            ),
        }
    )
    return out.dropna(subset=["plant_code"]).drop_duplicates("plant_code")


def cems_plant_rates(states: set[str], year: int) -> pd.DataFrame:
    """Return per-plant measured heat rates for ``year`` over ``states``.

    Prefers the unit-level CAMPD extract (it carries ``opTime``, so a partial
    operating hour can be excluded from the loading-conditional basis) and falls
    back to the facility-level extract where a state's unit file is absent.
    Units are summed to plant-hour first, so the rate is a plant rate.
    """
    frames = []
    for st in sorted(states):
        unit = CAMPD_UNIT / f"{st}_{year}.parquet"
        fac = CAMPD_FAC / f"{st}_{year}.parquet"
        if unit.exists():
            f = pd.read_parquet(
                unit, columns=["facilityId", "date", "hour", "opTime", "grossLoad",
                               "heatInput"]
            )
        elif fac.exists():
            f = pd.read_parquet(
                fac, columns=["facilityId", "date", "hour", "grossLoad", "heatInput"]
            )
            f["opTime"] = 1.0  # facility extract carries no opTime
        else:
            continue
        frames.append(f)
    if not frames:
        return pd.DataFrame(columns=["plant_code", "hr_all", "hr_load", "cems_mwh"])

    raw = pd.concat(frames, ignore_index=True)
    raw["plant_code"] = pd.to_numeric(raw["facilityId"], errors="coerce")
    raw = raw.dropna(subset=["plant_code"])
    raw = raw[raw["grossLoad"] > 0.0]
    # The loading-conditional filter is a UNIT property: a unit's peak and its
    # full-clock flag are its own. Filtering on the plant sum would admit a
    # starting unit whenever a sibling carried the plant above half its peak.
    has_unit = "unitId" in raw.columns
    ukey = ["plant_code", "unitId"] if has_unit else ["plant_code"]
    raw["u_peak"] = raw.groupby(ukey, observed=True)["grossLoad"].transform("max")
    keep = (raw["grossLoad"] > LOAD_FRAC_MIN * raw["u_peak"]) & (
        raw["opTime"] >= OPTIME_MIN
    )

    ph = raw.groupby("plant_code", observed=True).agg(
        cems_mwh=("grossLoad", "sum"),
        heat_all=("heatInput", "sum"),
        cems_hrs=("date", "count"),
    )
    hi = (
        raw[keep]
        .groupby("plant_code", observed=True)
        .agg(
            load_mwh=("grossLoad", "sum"),
            load_heat=("heatInput", "sum"),
            load_hrs=("date", "count"),
        )
    )
    pk = (
        raw.groupby(["plant_code", "date", "hour"], observed=True)["grossLoad"]
        .sum()
        .groupby("plant_code", observed=True)
        .max()
        .rename("cems_pk")
    )
    out = ph.join(hi, how="left").join(pk, how="left").reset_index()
    out["hr_all"] = out["heat_all"] / out["cems_mwh"].replace(0, np.nan)
    out["hr_load"] = out["load_heat"] / out["load_mwh"].replace(0, np.nan)
    out["plant_code"] = out["plant_code"].astype(int)
    return out.drop(columns=["heat_all", "load_heat", "load_mwh"])


def iso_fleet(iso: str) -> pd.DataFrame:
    """Return ``plant_code, plant_group, fuel_type, pmax, heat_rate, on_bin``.

    Built through the model's own loader, so ``heat_rate`` is exactly the value
    the offer curve is assembled from. ``on_bin`` marks a unit whose rate is one
    of the ``HEAT_RATE_BINS`` centers — i.e. the eGRID join missed it and the
    fuel x vintage fallback fired.
    """
    from market_sim.config.constants import HEAT_RATE_BINS
    from market_sim.data.fleet import load_fleet_from_csv

    bins = {ft: set(np.round(list(v.values()), 6)) for ft, v in HEAT_RATE_BINS.items()}
    rows = []
    for g in load_fleet_from_csv(iso):
        rows.append(
            {
                "plant_code": int(g.plant_code),
                "plant_group": g.plant_group or "",
                "fuel_type": g.fuel_type,
                "pmax": float(g.pmax_mw),
                "heat_rate": float(g.heat_rate),
                "state": getattr(g, "state", "") or "",
                "on_bin": round(float(g.heat_rate), 6)
                in bins.get(g.fuel_type, set()),
            }
        )
    return pd.DataFrame(rows)


def plant_table(iso: str, year: int) -> pd.DataFrame:
    """Join one ISO's fleet to its eGRID vintages and measured CEMS rates."""
    fleet = iso_fleet(iso)
    states = {s for s in fleet["state"].unique() if s}
    cems = cems_plant_rates(states, year)
    e23 = egrid_plant_rates(2023).rename(columns={"hr": "egrid23", "net_mwh": "net23"})
    e24 = egrid_plant_rates(2024).rename(columns={"hr": "egrid24", "net_mwh": "net24"})

    # Fleet -> plant grain: capacity-weighted rate, dominant group, bin share.
    fleet = fleet[fleet["plant_group"].isin(CEMS_CLASSES)]
    agg = (
        fleet.assign(w=lambda d: d["pmax"] * d["heat_rate"],
                     wb=lambda d: d["pmax"] * d["on_bin"])
        .groupby(["plant_code", "plant_group"], observed=True)
        .agg(pmax=("pmax", "sum"), w=("w", "sum"), wb=("wb", "sum"))
        .reset_index()
    )
    agg["model_hr"] = agg["w"] / agg["pmax"].replace(0, np.nan)
    agg["bin_share"] = agg["wb"] / agg["pmax"].replace(0, np.nan)
    out = (
        agg.drop(columns=["w", "wb"])
        .merge(cems, on="plant_code", how="left")
        .merge(e23[["plant_code", "egrid23", "net23"]], on="plant_code", how="left")
        .merge(e24[["plant_code", "egrid24", "net24"]], on="plant_code", how="left")
    )
    out["iso"] = iso
    return out


def _wavg(v: pd.Series, w: pd.Series) -> float:
    """Return the ``w``-weighted mean of ``v`` over rows where both are finite."""
    ok = v.notna() & w.notna() & (w > 0)
    return float(np.average(v[ok], weights=w[ok])) if ok.any() else np.nan


def report_class(tab: pd.DataFrame, year: int) -> None:
    """Print the per-ISO x class provenance and heat-rate error summary."""
    print(
        f"\n=== {year} offer heat rate vs measured, by ISO x class "
        f"(cap-weighted) ===\n"
        f"{'iso':<7} {'class':<11} {'GW':>6} {'%MW bin':>8} | {'model':>6} "
        f"{'eG24':>6} {'hrAll':>6} {'hrLoad':>6} | {'vs hrLoad':>9} "
        f"{'vs hrAll':>8} {'n':>4}"
    )
    for (iso, klass), sub in tab.groupby(["iso", "plant_group"], observed=True):
        cov = sub[sub["hr_load"].notna() & sub["model_hr"].notna()]
        if cov.empty:
            continue
        w = cov["pmax"]
        m = _wavg(cov["model_hr"], w)
        hl = _wavg(cov["hr_load"], w)
        ha = _wavg(cov["hr_all"], w)
        print(
            f"{iso:<7} {klass:<11} {sub['pmax'].sum() / 1e3:>6.1f} "
            f"{100 * _wavg(sub['bin_share'], sub['pmax']):>7.0f}% | "
            f"{m:>6.2f} {_wavg(cov['egrid24'], w):>6.2f} {ha:>6.2f} {hl:>6.2f} | "
            f"{100 * (m / hl - 1):>8.0f}% {100 * (m / ha - 1):>7.0f}% {len(cov):>4}"
        )
    print(
        "\n  model  = the offer heat rate the LP actually uses (eGRID PLNT23 "
        "PLHTRT,\n           or the HEAT_RATE_BINS fuel x vintage center where "
        "that join missed).\n"
        "  %MW bin = share of the class's capacity on the bin fallback (the "
        "owner lead).\n"
        "  hrAll  = CEMS annual heat input / gross load (all generating hours).\n"
        "  hrLoad = CEMS loading-conditional (full-clock hours above half the "
        "observed peak)."
    )


def report_boundary(tab: pd.DataFrame) -> None:
    """Print the CEMS-gross vs eGRID-net boundary ratio, by class.

    The model dispatches NET MW (``pmax`` is net summer capability) while CEMS
    reports GROSS load, so a gross-basis measured rate understates fuel per net
    MWh by the auxiliary-load fraction. This sizes that one real basis mismatch.
    """
    print("\n=== gross->net boundary: CEMS gross MWh / eGRID net MWh (2023) ===")
    print(f"{'class':<12} {'n':>4} {'p25':>6} {'p50':>6} {'p75':>6} {'cap-wtd':>8}")
    for klass, sub in tab.groupby("plant_group", observed=True):
        ok = sub[
            sub["cems_mwh"].notna() & sub["net23"].notna() & (sub["net23"] > 1e4)
        ].copy()
        if len(ok) < 3:
            continue
        r = ok["cems_mwh"] / ok["net23"]
        r = r[(r > 0.8) & (r < 1.5)]  # drop boundary-mismatched pairs
        if r.empty:
            continue
        q = np.percentile(r, [25, 50, 75])
        print(
            f"{klass:<12} {len(r):>4} {q[0]:>6.3f} {q[1]:>6.3f} {q[2]:>6.3f} "
            f"{_wavg(r, ok.loc[r.index, 'pmax']):>8.3f}"
        )


def report_plants(tab: pd.DataFrame, klass: str, top: int) -> None:
    """Print the per-plant detail for one class, largest measured energy first."""
    sub = tab[tab["plant_group"] == klass].sort_values(
        "cems_mwh", ascending=False
    )
    print(f"\n=== per-plant {klass} (top {top} by CEMS energy) ===")
    print(
        f"{'plant':>6} {'MW':>6} {'bin':>4} | {'model':>6} {'eG23':>6} "
        f"{'eG24':>6} {'hrAll':>6} {'hrLoad':>6} | {'err%':>5} {'GWh':>7} "
        f"{'hrs':>5} {'ldhrs':>6}"
    )
    for _, r in sub.head(top).iterrows():
        err = (
            100 * (r.model_hr / r.hr_load - 1) if pd.notna(r.hr_load) else np.nan
        )
        print(
            f"{int(r.plant_code):>6} {r.pmax:>6.0f} "
            f"{'Y' if r.bin_share > 0.5 else '':>4} | {r.model_hr:>6.2f} "
            f"{r.egrid23:>6.2f} {r.egrid24:>6.2f} {r.hr_all:>6.2f} "
            f"{r.hr_load:>6.2f} | {err:>5.0f} {r.cems_mwh / 1e3:>7.1f} "
            f"{int(r.cems_hrs) if pd.notna(r.cems_hrs) else 0:>5} "
            f"{int(r.load_hrs) if pd.notna(r.load_hrs) else 0:>6}"
        )


def report_cf_tilt(tab: pd.DataFrame, klass: str) -> None:
    """Print the eGRID error against capacity factor, in CF quartiles.

    The decisive question for the lane: eGRID ``PLHTRT`` is an ANNUAL ALL-FUEL
    average, so it carries the plant's startup and part-load fuel spread over
    its net generation. A low-CF peaker starts far more often per MWh delivered,
    so the inflation should RISE as CF falls. If it does, the incumbent input is
    not merely a level error — it systematically over-prices exactly the
    low-duty plants that never clear, which is a merit-order defect.
    """
    sub = tab[
        (tab["plant_group"] == klass)
        & tab["hr_load"].notna()
        & tab["model_hr"].notna()
        & (tab["pmax"] > 0)
    ].copy()
    if len(sub) < 8:
        return
    sub["cf"] = sub["cems_mwh"] / (sub["pmax"] * 8760.0)
    sub["err"] = 100.0 * (sub["model_hr"] / sub["hr_load"] - 1.0)
    sub["q"] = pd.qcut(sub["cf"], 4, labels=["Q1 low", "Q2", "Q3", "Q4 high"])
    print(f"\n=== {klass}: eGRID inflation vs capacity factor ===")
    print(f"{'CF quartile':<10} {'n':>3} {'CF':>7} {'model':>6} {'hrLoad':>7} {'err%':>6}")
    for q, g in sub.groupby("q", observed=True):
        print(
            f"{str(q):<10} {len(g):>3} {g['cf'].mean():>7.3f} "
            f"{_wavg(g['model_hr'], g['pmax']):>6.2f} "
            f"{_wavg(g['hr_load'], g['pmax']):>7.2f} "
            f"{_wavg(g['err'], g['pmax']):>6.0f}"
        )
    ok = sub["cf"].notna() & sub["err"].notna()
    print(
        f"  rank corr(CF, err) = "
        f"{sub.loc[ok, 'cf'].corr(sub.loc[ok, 'err'], method='spearman'):+.3f}  "
        f"(negative = low-CF plants are the most over-priced)"
    )


def report_coverage_stability(iso: str, years: list[int]) -> None:
    """Print CEMS coverage of the fleet and the measured rate's cross-year stability.

    The two build gates for a measured-heat-rate swap: how much of each class's
    capacity the replacement input actually covers (the rest keeps the incumbent
    chain), and whether a plant's loading-conditional rate is a stable physical
    property year to year — a rate that jumps between years is a noisy estimate,
    not a measurement, and could not carry a forward story (rule 13).
    """
    tabs = {y: plant_table(iso, y) for y in years}
    base = tabs[years[0]]
    print(f"\n=== {iso} CEMS coverage of the fleet, {years[0]} ===")
    print(f"{'class':<12} {'plants':>7} {'covered':>8} {'GW':>7} {'GW cov':>7} {'%MW':>6}")
    for klass, sub in base.groupby("plant_group", observed=True):
        cov = sub[sub["hr_load"].notna()]
        print(
            f"{klass:<12} {len(sub):>7} {len(cov):>8} {sub['pmax'].sum() / 1e3:>7.2f} "
            f"{cov['pmax'].sum() / 1e3:>7.2f} "
            f"{100 * cov['pmax'].sum() / max(sub['pmax'].sum(), 1e-9):>5.0f}%"
        )

    print(f"\n=== {iso} cross-year stability of hr_load ({years[0]}-{years[-1]}) ===")
    print(f"{'class':<12} {'n':>4} {'r':>6} {'medCV':>7} {'p90CV':>7}")
    merged = None
    for y in years:
        col = tabs[y][["plant_code", "plant_group", "pmax", "hr_load"]].rename(
            columns={"hr_load": f"hr{y}"}
        )
        merged = col if merged is None else merged.merge(
            col.drop(columns=["plant_group", "pmax"]), on="plant_code", how="outer"
        )
    hcols = [f"hr{y}" for y in years]
    merged = merged.dropna(subset=hcols)
    for klass, sub in merged.groupby("plant_group", observed=True):
        if len(sub) < 3:
            continue
        vals = sub[hcols].to_numpy(dtype=float)
        cv = vals.std(axis=1, ddof=0) / np.maximum(vals.mean(axis=1), 1e-9)
        r = float(np.corrcoef(vals[:, 0], vals[:, -1])[0, 1]) if len(sub) > 2 else np.nan
        print(
            f"{klass:<12} {len(sub):>4} {r:>6.3f} {np.median(cv):>7.3f} "
            f"{np.percentile(cv, 90):>7.3f}"
        )
    print(
        "  r = corr(first year, last year) across plants; CV = per-plant "
        "coefficient of\n  variation across the years (a physical rate should "
        "read r ~ 1 and CV ~ 0)."
    )


def main() -> None:
    """Run the provenance + measured-rate audit for the requested ISOs."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", nargs="+", default=["CAISO"])
    ap.add_argument("--year", type=int, default=2024)
    ap.add_argument("--klass", default="CT_PEAKER")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--plants", action="store_true", help="per-plant detail")
    ap.add_argument("--out", default="", help="optional parquet dump of the table")
    ap.add_argument(
        "--stability", nargs="*", type=int, default=None,
        help="years for the coverage + cross-year stability report",
    )
    args = ap.parse_args()

    tab = pd.concat(
        [plant_table(iso, args.year) for iso in args.iso], ignore_index=True
    )
    report_class(tab, args.year)
    report_boundary(tab)
    for iso in args.iso:
        report_cf_tilt(tab[tab["iso"] == iso], args.klass)
    if args.stability:
        for iso in args.iso:
            report_coverage_stability(iso, list(args.stability))
    if args.plants:
        for iso in args.iso:
            report_plants(tab[tab["iso"] == iso], args.klass, args.top)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        tab.to_parquet(args.out, index=False)
        print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()

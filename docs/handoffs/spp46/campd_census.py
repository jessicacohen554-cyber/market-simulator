"""SPP-46 phase 0.1 (zero-LP): the per-class COMMITTED-STATE census of SPP's gas
fleet from its own CAMPD conduct, against keeper-3's committed dispatch.

Units are classified by CAMPD's own ``unitType`` / ``primaryFuelInfo``
(Combined cycle -> CC; Combustion turbine -> CT; a boiler burning natural gas
-> ST_GAS), restricted to the facilities keeper-3's fleet carries in the
matching merchant class (CC_REGULAR / CT_PEAKER / ST_GAS; the CHP plants are
excluded through the fleet's own class labels). A mixed plant (e.g. 1217 Earl F
Wisdom: one boiler + one CT) is therefore split by unit, not tabled once.

Per class x year:
* measured class gross generation (TWh) beside keeper-3's P1 dispatch and the
  bench actual (EIA-923 classFull), so CAMPD coverage is stated;
* the ONLINE state per unit (grossLoad >= max(_ONLINE_MW, 0.05 x HSL_unit),
  HSL = p99.5 of the unit's pooled load — the SPP-44 derive's own threshold),
  cap-weighted online fraction and loading-when-on;
* the committed-state floor F(t) = sum over online PLANTS of the plant-basis
  LSL (SPP-44's construction; LSL = p5 of the plant's online-hour load) and
  the FOOTPRINT sum_t max(0, F - D) against keeper-3's class dispatch D(t),
  decomposed into hours where D > 0 (the only hours a P0-anchored online-hours
  leg can touch, since a run the model never starts has no online hours) and
  hours where D = 0 (unreachable by any P0-anchored leg);
* the duty membership: per plant online fraction and p25 run length, and the
  share of F carried by the near-baseload cohort (online_frac >= 0.75);
* for CT: the OVER-run footprint sum_t max(0, D - G_measured) and its split by
  system-load percentile (from keeper-3's own demand).

Writes census_<year>.csv (per plant), census_summary.csv, and
class_series_<year>.parquet (hourly ON capacity, measured gen, F, D per class)
for the phase-0.2 revealed-conduct construction.

Usage: uv run python docs/handoffs/spp46/campd_census.py
"""
import gzip, json, sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
from derive_campd_gas_commitment_params import _ONLINE_FRAC, UNIT_LEVEL_DIR  # noqa: E402
from market_sim.data.campd import _ONLINE_MW, states_for_iso  # noqa: E402
from market_sim.model.commitment import find_runs  # noqa: E402

OUT = REPO / "docs/handoffs/spp46"
BUNDLE = REPO / "results/calibration/spp43_screened_B"
YEARS = (2023, 2024, 2025)
CLASSES = {"CC_REGULAR": "cc", "CT_PEAKER": "ct", "ST_GAS": "st"}
DUTY_ONLINE_FRAC = 0.75


def campd_class(unit_type: str, fuel: str) -> str | None:
    ut = (unit_type or "").lower(); fu = (fuel or "").lower()
    if "combined cycle" in ut:
        return "cc"
    if "combustion turbine" in ut:
        return "ct"
    if "boiler" in ut or "fired" in ut or "fluidized" in ut or "stoker" in ut or "cell burner" in ut:
        if "natural gas" in fu or fu.strip() in ("gas", "pipeline natural gas") or ("gas" in fu and "coal" not in fu):
            return "st"
    return None


def load_units(year: int, codes: set[int]) -> pd.DataFrame:
    frames = []
    for state in states_for_iso("SPP"):
        p = UNIT_LEVEL_DIR / f"{state}_{year}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p, columns=["facilityId", "unitId", "date", "hour", "grossLoad", "unitType", "primaryFuelInfo"])
        df["facilityId"] = pd.to_numeric(df["facilityId"], errors="coerce")
        df = df[df["facilityId"].isin(codes)]
        if not df.empty:
            frames.append(df)
    df = pd.concat(frames)
    df["klass"] = [campd_class(u, f) for u, f in zip(df.unitType, df.primaryFuelInfo)]
    df = df[df.klass.notna()].copy()
    df["ts"] = pd.to_datetime(df["date"].astype(str)) + pd.to_timedelta(df["hour"], unit="h")
    return df


def hourly_matrix(df: pd.DataFrame, year: int) -> pd.DataFrame:
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    piv = df.pivot_table(index="ts", columns=["facilityId", "unitId"], values="grossLoad", aggfunc="sum")
    return piv.reindex(idx).fillna(0.0)


def main() -> None:
    fleet_rows = {y: pd.read_csv(OUT / f"rows_{y}.csv") for y in YEARS}
    summary, series_rows = [], []
    for year in YEARS:
        fr = fleet_rows[year]
        ch = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        sysp = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
        sysp = sysp[sysp["pass"] == "P1"]
        load = sysp.groupby("hour")["demand"].sum().sort_index().to_numpy()
        load_pct = pd.Series(load).rank(pct=True).to_numpy()
        bench = json.load(gzip.open(REPO / f"frontend/data/backcast/bench/SPP/{year}.json.gz"))["bench"]["classFull"]
        codes_by_class = {k: set(int(c) for c in fr[fr.plant_group == k].plant_code if c > 0) for k in CLASSES}
        all_codes = set().union(*codes_by_class.values())
        units = load_units(year, all_codes)
        mat = hourly_matrix(units, year)
        unit_klass = units.groupby(["facilityId", "unitId"])["klass"].first()
        series = {}
        for grp, tag in CLASSES.items():
            cols = [c for c in mat.columns if unit_klass.get(c) == tag and int(c[0]) in codes_by_class[grp]]
            if not cols:
                continue
            sub = mat[cols]
            fleet_mw = fr[fr.plant_group == grp].groupby("plant_code")["pmax"].sum()
            covered_mw = float(fleet_mw.reindex(sorted(set(int(c[0]) for c in cols))).fillna(0).sum())
            # unit HSL / online state
            hsl_u = sub.quantile(0.995)
            on_u = sub.ge(np.maximum(_ONLINE_MW, _ONLINE_FRAC * hsl_u), axis=1)
            on_cap = (on_u * hsl_u).sum(axis=1).to_numpy()
            gen = sub.sum(axis=1).to_numpy()
            D = ch[ch.klass == grp].sort_values("hour")["mw"].to_numpy(dtype=float)
            assert D.size == 8760
            # plant basis for F (SPP-44 construction)
            plant = sub.T.groupby(level=0).sum().T
            hsl_p = plant.quantile(0.995)
            on_p = plant.ge(np.maximum(_ONLINE_MW, _ONLINE_FRAC * hsl_p), axis=1)
            lsl_p = pd.Series({c: float(np.percentile(plant[c][on_p[c]], 5)) if on_p[c].any() else 0.0 for c in plant.columns})
            F = (on_p * lsl_p).sum(axis=1).to_numpy()
            excess = np.maximum(0.0, F - D)
            over = np.maximum(0.0, D - gen)
            fp_pos = float(excess[D > 0].sum()) / 1e3
            fp_zero = float(excess[D <= 0].sum()) / 1e3
            # duty membership per plant
            prow = []
            F_duty = np.zeros(8760)
            for c in plant.columns:
                on = on_p[c].to_numpy()
                runs = find_runs(on)
                rl = [e - s for s, e in runs]
                of = float(on.mean())
                prow.append(dict(year=year, klass=grp, plant_code=int(c), hsl_mw=float(hsl_p[c]), lsl_mw=float(lsl_p[c]),
                                 lsl_frac=float(lsl_p[c] / hsl_p[c]) if hsl_p[c] > 0 else np.nan, online_frac=of,
                                 n_runs=len(runs), run_p25=float(np.percentile(rl, 25)) if rl else 0.0,
                                 run_p50=float(np.percentile(rl, 50)) if rl else 0.0,
                                 gen_gwh=float(plant[c].sum()) / 1e3, fleet_mw=float(fleet_mw.get(int(c), 0.0)),
                                 duty=of >= DUTY_ONLINE_FRAC))
                if of >= DUTY_ONLINE_FRAC:
                    F_duty += on * float(lsl_p[c])
            pdf = pd.DataFrame(prow)
            pdf.to_csv(OUT / f"census_{year}_{tag}.csv", index=False)
            excess_duty = np.maximum(0.0, F_duty - D)
            on_frac_cw = float((on_cap.sum()) / (hsl_u.sum() * 8760))
            summary.append(dict(
                year=year, klass=grp, campd_plants=int(plant.shape[1]), campd_units=len(cols),
                fleet_plants=len(codes_by_class[grp]), fleet_mw=float(fleet_mw.sum()), covered_mw=covered_mw,
                hsl_sum_mw=float(hsl_u.sum()),
                campd_gen_twh=float(gen.sum()) / 1e6, keeper_twh=float(D.sum()) / 1e6, bench_twh=float(bench.get(grp, np.nan)),
                online_frac_capwtd=on_frac_cw,
                loading_when_on=float(gen[on_cap > 0].sum() / on_cap[on_cap > 0].sum()),
                F_mean_mw=float(F.mean()), D_mean_mw=float(D.mean()), hours_D_zero=int((D <= 0).sum()),
                footprint_gwh=float(excess.sum()) / 1e3, footprint_in_D_pos_gwh=fp_pos, footprint_in_D_zero_gwh=fp_zero,
                hours_F_gt_D=int((F > D).sum()),
                duty_plants=int(pdf.duty.sum()), duty_mw=float(pdf[pdf.duty].hsl_mw.sum()),
                F_duty_mean_mw=float(F_duty.mean()), footprint_duty_gwh=float(excess_duty.sum()) / 1e3,
                overrun_gwh=float(over.sum()) / 1e3,
                overrun_top10_load_gwh=float(over[load_pct >= 0.9].sum()) / 1e3,
                overrun_mid_load_gwh=float(over[(load_pct >= 0.25) & (load_pct < 0.75)].sum()) / 1e3,
                overrun_low_load_gwh=float(over[load_pct < 0.25].sum()) / 1e3,
                underrun_gwh=float(np.maximum(0.0, gen - D).sum()) / 1e3,
            ))
            series[grp] = dict(on_cap=on_cap, gen=gen, F=F, D=D)
        sdf = pd.DataFrame({f"{g}_{k}": v for g, d in series.items() for k, v in d.items()})
        sdf["load"] = load
        sdf.to_parquet(OUT / f"class_series_{year}.parquet", index=False)
    s = pd.DataFrame(summary)
    s.to_csv(OUT / "census_summary.csv", index=False)
    pd.set_option("display.width", 300); pd.set_option("display.max_columns", 50)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

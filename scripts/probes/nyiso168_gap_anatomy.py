"""nyiso-168 phase-0: WHERE the 0.70 price-response gain deficit lives.

nyiso-167 established that NYISO's keeper reproduces ~0.70 of the market's
price response as one year-invariant affine law, and handed the GAIN forward
as the object.  A law is a description, not a mechanism.  This probe locates
the deficit and kills the candidate mechanisms that can be killed by
measurement rather than by argument.

SIX MEASUREMENTS, all on committed artifacts (NO LP; rule 22 — every year read
is 2023, 2024 or 2025):

A. GAP BY LOAD PERCENTILE BAND.  The load-weighted model system price minus
   the actual DA hub price, in load-sorted bands, with each band's share of
   the annual mean gap.  Separates a tail object (C3c) from a slope object.
B. DECILE LADDER + IMPLIED MARGINAL HEAT RATE.  Model and actual price per
   $/MMBtu of Transco Z6 NY, by load decile — the price-implied marginal heat
   rate, model vs market.
C. PEAK-HOUR SUPPLY MIX vs EIA-930.  The model's top-decile dispatch by fuel
   bucket against the measured NYIS hourly fuel mix, at the ISO's own load
   ordering.  Tests whether the flat top is a mix/availability object.
D. STORAGE ARBITRAGE.  Net storage discharge by load decile — how much of the
   ladder's flattening the model's own storage buys.
E. MEASURED FOSSIL-FLEET INCREMENTAL HEAT RATE (CAMPD NY unit-level hourly
   grossLoad + heatInput, pooled).  ``d(heatInput)/d(grossLoad)`` by output
   level, from first differences.  This is the market's OWN physical marginal
   heat rate — the benchmark for how much of the market's price steepness is
   physics rather than markup or congestion.
F. ZONAL SPLIT.  The load-weighted deficit decomposed into a zonal-gradient
   component and a level component that survives in the least-congested zone.

Reproduction: ``python scripts/probes/nyiso168_gap_anatomy.py``
Record: ``results/calibration/_nyiso168_gap_anatomy.json``
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/nyiso159_lossarm_B"
YEARS = (2023, 2024, 2025)
OUT = "results/calibration/_nyiso168_gap_anatomy.json"

GAS_CSV = "data/raw/gas-prices/transco_z6_ny_daily.csv"
ACTUAL_HOURLY = "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
ACTUAL_ZONAL = "data/raw/_validation-source/actual_lmp.json"
E930 = "data/raw/eia-930-hourly/NYIS hourly.parquet"

#: EIA-930 fuel column -> bucket, and model class -> the same bucket.
E930_BUCKET = {
    "NG: NG": "gas",
    "NG: NUC": "nuclear",
    "NG: OIL": "oil",
    "NG: WAT": "hydro",
    "NG: WND": "wind",
    "NG: SUN": "solar",
    "NG: OTH": "other",
    "NG: COL": "coal",
}
CLASS_BUCKET = {
    "CC_CHP": "gas",
    "CC_REGULAR": "gas",
    "CT_CHP": "gas",
    "CT_PEAKER": "gas",
    "ST_GAS": "gas",
    "ST_CHP": "gas",
    "nuclear": "nuclear",
    "hydro": "hydro",
    "wind": "wind",
    "solar": "solar",
    "oil": "oil",
    "biomass": "other",
    "OTHER": "other",
}
#: Load-percentile band edges for measurement A.
BANDS = ((0, 50), (50, 80), (80, 90), (90, 95), (95, 99), (99, 99.9), (99.9, 100))


def hourly_gas(year: int) -> np.ndarray:
    """Daily Transco Z6 NY spot broadcast to the year's 8760 standard hours."""
    gas = pd.read_csv(GAS_CSV, parse_dates=["date"]).set_index("date")
    ser = gas["transco_z6_ny_usd_mmbtu"].astype(float)
    days = pd.date_range(f"{year}-01-01", f"{year}-12-31", freq="D")
    ser = ser.reindex(days).ffill().bfill()
    idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
    return ser.reindex(idx.normalize()).to_numpy()


def keeper_system(
    year: int,
) -> tuple[np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame]:
    """Return ``(load, load-weighted model price, zonal price, zonal demand)``."""
    s = pd.read_parquet(f"{BUNDLE}/hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot_table(index="hour", columns="zone", values="price")
    d = s.pivot_table(index="hour", columns="zone", values="demand")
    load = d.sum(axis=1).to_numpy()
    return load, (p * d).sum(axis=1).to_numpy() / load, p, d


def measure_a(load, model, da) -> tuple[list[dict], float]:
    """Gap by load-percentile band, with each band's annual-mean contribution."""
    order = np.argsort(load)
    rows, total = [], 0.0
    for lo, hi in BANDS:
        idx = order[int(8760 * lo / 100) : int(8760 * hi / 100)]
        gap = float(model[idx].mean() - np.nanmean(da[idx]))
        contrib = gap * len(idx) / 8760.0
        total += contrib
        rows.append(
            dict(
                pct_lo=lo,
                pct_hi=hi,
                n=len(idx),
                load_mw=float(load[idx].mean()),
                model=float(model[idx].mean()),
                actual_da=float(np.nanmean(da[idx])),
                gap=gap,
                annual_contribution=contrib,
            )
        )
    return rows, total


def measure_b(load, model, da, gas) -> list[dict]:
    """Decile ladder and the price-implied marginal heat rate, model vs market."""
    order = np.argsort(load)
    dec = np.zeros(8760, int)
    dec[order] = np.minimum(np.arange(8760) * 10 // 8760, 9)
    rows = []
    for k in range(10):
        m = dec == k
        rows.append(
            dict(
                decile=k,
                load_mw=float(load[m].mean()),
                model=float(model[m].mean()),
                actual_da=float(np.nanmean(da[m])),
                gas=float(gas[m].mean()),
                implied_hr_model=float(np.nanmean(model[m] / gas[m])),
                implied_hr_da=float(np.nanmean(da[m] / gas[m])),
            )
        )
    return rows


def measure_e(year: int) -> dict:
    """Measured NY fossil-fleet incremental heat rate from CAMPD first differences."""
    cols = ["date", "hour", "grossLoad", "heatInput"]
    d = pd.read_parquet(f"data/raw/campd-unit-level/NY_{year}.parquet", columns=cols)
    d[["grossLoad", "heatInput"]] = d[["grossLoad", "heatInput"]].fillna(0.0)
    fleet = d.groupby(["date", "hour"])[["grossLoad", "heatInput"]].sum()
    fleet = fleet.sort_index().reset_index()
    G = fleet["grossLoad"].to_numpy(float)
    H = fleet["heatInput"].to_numpy(float)
    ok = G > 500.0
    G, H = G[ok], H[ok]
    dG, dH = np.diff(G), np.diff(H)
    mid = 0.5 * (G[1:] + G[:-1])
    sel = np.abs(dG) > 200.0  # real moves only, not noise
    edges = np.quantile(mid[sel], np.linspace(0, 1, 6))
    quints = []
    for i in range(5):
        m = sel & (mid >= edges[i]) & (mid <= edges[i + 1])
        if m.sum() < 30:
            continue
        slope = float(np.sum(dG[m] * dH[m]) / np.sum(dG[m] * dG[m]))
        quints.append(
            dict(output_mw=float(mid[m].mean()), n=int(m.sum()), incremental_hr=slope)
        )
    return dict(pooled_average_hr=float(H.sum() / G.sum()), quintiles=quints)


def measure_f(year: int, p: pd.DataFrame, d: pd.DataFrame) -> dict:
    """Zonal split of the load-weighted deficit: gradient vs surviving level."""
    actual = json.load(open(ACTUAL_ZONAL))["NYISO"][str(year)]["zones"]
    zones = [z for z in p.columns if z != "NYISO_external"]
    share = (d[zones].sum() / d[zones].sum().sum()).to_dict()
    ref = "Upstate_West"
    out, weighted, grad_weighted = {}, 0.0, 0.0

    def _da(zone: str):
        v = actual.get(zone, {}).get("da")
        return (
            float(np.mean(v))
            if isinstance(v, list)
            else (None if v is None else float(v))
        )

    ref_model, ref_da = float(p[ref].mean()), _da(ref)
    for z in zones:
        mz, az = float(p[z].mean()), _da(z)
        if az is None:
            continue
        w = float(share[z])
        weighted += w * (mz - az)
        if z != ref and ref_da is not None:
            grad_weighted += w * ((mz - ref_model) - (az - ref_da))
        out[z] = dict(
            load_share=w,
            model=mz,
            actual_da=az,
            delta=mz - az,
            gradient_model=mz - ref_model,
            gradient_actual=None if ref_da is None else az - ref_da,
        )
    return dict(
        zones=out,
        load_weighted_deficit=weighted,
        gradient_component=grad_weighted,
        level_component=weighted - grad_weighted,
        reference_zone=ref,
    )


#: The four NEISO gates nyiso-167 §4 recorded as an ASSOCIATION with NEISO's
#: gain of 0.986, and handed forward as an open NYISO-lane question.
NEISO_GATES = (
    "neiso_winter_fuel_inventory",
    "neiso_winter_fuel_mustrun",
    "neiso_gas_coldsnap_derate",
    "scarcity_price_overlay",
    "temp_dependent_derate",
)
NEISO_BUNDLES = (
    "neiso86_2022_corrected",
    "neiso97_dstrepair_A",
    "neiso99_basis_A",
    "neiso99_joint_B",
)


def neiso_arm_census() -> dict:
    """Is there a committed NEISO run with those gates OFF, to attribute against?

    nyiso-167 §4 measured an ASSOCIATION between NEISO's gain of 0.986 and the
    four supply-side gates it arms that NYISO does not, and said explicitly
    that it had measured an association and not a mechanism.  Turning that
    into a mechanism requires a NEISO arm WITHOUT them.  This census reads the
    ``run_config.json`` of every committed NEISO bundle and reports the flag
    state; it adjudicates nothing and fills no matrix cell (rule 25
    ``[R-ISO-SCOPE]``, rule 28(d)) — it establishes only whether the
    attribution nyiso-167 asked a successor to make is available on the
    committed record at all.
    """
    import os
    import re as _re

    out: dict = {}
    for bundle in NEISO_BUNDLES:
        path = f"results/calibration/{bundle}/run_config.json"
        if not os.path.exists(path):
            out[bundle] = {"present": False}
            continue
        text = open(path).read()
        flags = {}
        for flag in NEISO_GATES:
            m = _re.search(rf'"{flag}"\s*:\s*([a-zA-Z]+|null)', text)
            flags[flag] = m.group(1) if m else "ABSENT"
        out[bundle] = {"present": True, "flags": flags}
    all_on = [
        b
        for b, v in out.items()
        if v.get("present") and all(x == "true" for x in v["flags"].values())
    ]
    out["_summary"] = {
        "bundles_checked": len(
            [v for v in out.values() if isinstance(v, dict) and v.get("present")]
        ),
        "bundles_with_all_five_armed": len(all_on),
        "an_arm_without_them_exists": len(all_on)
        < len([v for v in out.values() if isinstance(v, dict) and v.get("present")]),
    }
    return out


def main() -> None:
    act = pd.read_parquet(ACTUAL_HOURLY)
    raw930 = pd.read_parquet(E930)
    raw930["year"] = raw930["Local date"].astype("datetime64[ns]").dt.year

    record: dict = {
        "probe": "nyiso168_gap_anatomy",
        "bundle": BUNDLE,
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "years": list(YEARS),
        "note": (
            "Zero solve. Locates the nyiso-167 price-response-gain deficit and "
            "kills the mechanism candidates that measurement can kill. Gap is "
            "stated on the DA basis (the like-for-like comparable for a "
            "perfect-foresight LP; RT adds the scarcity tail it cannot form)."
        ),
        "by_year": {},
        "G_neiso_arm_census": neiso_arm_census(),
    }
    cen = record["G_neiso_arm_census"]["_summary"]
    print(
        f"NEISO arm census: {cen['bundles_with_all_five_armed']} of "
        f"{cen['bundles_checked']} committed NEISO bundles arm ALL FIVE gates; "
        f"an arm without them exists = {cen['an_arm_without_them_exists']}\n"
    )

    for year in YEARS:
        load, model, p, d = keeper_system(year)
        a = act[act["year"] == year].sort_values("hour")
        da = a["da"].to_numpy(float)
        gas = hourly_gas(year)

        bands, total = measure_a(load, model, da)
        row: dict = {
            "A_gap_by_load_band": bands,
            "A_total_annual_gap": total,
            "B_decile_ladder": measure_b(load, model, da, gas),
            "E_measured_incremental_hr": measure_e(year),
            "F_zonal_split": measure_f(year, p, d),
        }

        # C: peak-decile mix vs EIA-930, each side on its OWN load ordering.
        order = np.argsort(load)
        dec = np.zeros(8760, int)
        dec[order] = np.minimum(np.arange(8760) * 10 // 8760, 9)
        ch = pd.read_parquet(f"{BUNDLE}/hourly/class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        piv = ch.pivot_table(index="hour", columns="klass", values="mw")
        piv = piv.reindex(range(8760)).fillna(0.0)
        g930 = raw930[raw930["year"] == year].sort_values("UTC time").iloc[:8760]
        aload = g930["Demand"].to_numpy(float)
        adec = np.zeros(len(aload), int)
        adec[np.argsort(aload)] = np.minimum(
            np.arange(len(aload)) * 10 // len(aload), 9
        )
        mix = {}
        for bucket in ("gas", "nuclear", "hydro", "wind", "solar", "oil", "other"):
            mcols = [c for c in piv.columns if CLASS_BUCKET.get(c) == bucket]
            mmw = piv[mcols].to_numpy().sum(axis=1) if mcols else np.zeros(8760)
            acols = [k for k, v in E930_BUCKET.items() if v == bucket]
            amw = (
                g930[acols].to_numpy(float).sum(axis=1)
                if acols
                else np.zeros(len(aload))
            )
            mix[bucket] = dict(
                model_d9=float(mmw[dec == 9].mean()),
                actual_d9=float(np.nanmean(amw[adec == 9])),
                model_d0=float(mmw[dec == 0].mean()),
                actual_d0=float(np.nanmean(amw[adec == 0])),
            )
        row["C_peak_mix_vs_e930"] = mix

        # D: net storage discharge by decile.
        st = pd.read_parquet(f"{BUNDLE}/hourly/storage_{year}.parquet")
        st = st[st["pass"] == "P1"]
        net = (
            (
                st.groupby("hour")["discharge_mw"].sum()
                - st.groupby("hour")["charge_mw"].sum()
            )
            .reindex(range(8760))
            .fillna(0.0)
        )
        row["D_storage_net_discharge_by_decile"] = [
            float(net.to_numpy()[dec == k].mean()) for k in range(10)
        ]

        record["by_year"][str(year)] = row

        print(f"=== {year}   annual DA-basis gap ${total:+.2f}/MWh")
        for b in bands:
            print(
                f"  load pct {b['pct_lo']:5.1f}-{b['pct_hi']:5.1f}  n {b['n']:5d}"
                f"  model {b['model']:7.2f}  DA {b['actual_da']:7.2f}"
                f"  gap {b['gap']:+8.2f}  contrib {b['annual_contribution']:+6.2f}"
            )
        e = row["E_measured_incremental_hr"]
        print(
            "  CAMPD measured incremental HR by output quintile: "
            + ", ".join(
                f"{q['output_mw']:.0f}MW->{q['incremental_hr']:.2f}"
                for q in e["quintiles"]
            )
        )
        f = row["F_zonal_split"]
        print(
            f"  zonal split: load-weighted deficit ${f['load_weighted_deficit']:+.2f}"
            f" = gradient ${f['gradient_component']:+.2f}"
            f" + level ${f['level_component']:+.2f}"
        )
        print()

    with open(OUT, "w") as fh:
        json.dump(record, fh, indent=1)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

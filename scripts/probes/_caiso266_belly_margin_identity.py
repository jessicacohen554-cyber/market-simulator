"""caiso-266 — the shoulder-month object, located and sized on the belly axis.

Reproduces every number in
``results/calibration/FINDING-caiso266-belly-margin-identity-2026-09-08.md``
from committed artifacts alone. **ZERO LP** — no matrix is built, no solver is
called, no fleet is rebuilt.

Inputs, all committed:

* the keeper bundle's ``hourly/`` sidecars — ``system_<y>.parquet``,
  ``class_hourly_<y>.parquet``, ``class_band_hourly_<y>.parquet``,
  ``storage_<y>.parquet`` (``results/calibration/caiso260_demand_vintage/``);
* the committed actual-LMP reference
  ``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet``;
* the committed bench parts ``frontend/data/backcast/bench/CAISO/<y>.json.gz``
  (the 85-plant CAMPD gas panel the run is scored against);
* the EIA-930 ``CISO hourly`` extract ``data/raw/eia-930-hourly/CISO hourly.parquet``;
* the committed measured offer surface
  ``data/raw/_validation-source/caiso_offer_curve_measured.json`` and the
  keeper's ``run_config.json``.

Sections mirror the FINDING: M0 (additive-vs-proportional), M1 (price-bin
decomposition), M3 (model-regime split), M4/M13 (composition and the EIA-930
basis trap), M8 (storage on the caiso-256 battery-only basis), M10 (the CEMS
panel commitment state), M11 (offer-band sign) and M12 (sizing).

Usage: ``python3 scripts/probes/_caiso266_belly_margin_identity.py``
"""

from __future__ import annotations

import base64
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results/calibration/caiso260_demand_vintage/hourly"
ACTUAL = ROOT / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
E930 = ROOT / "data/raw/eia-930-hourly/CISO hourly.parquet"
MEASURED = ROOT / "data/raw/_validation-source/caiso_offer_curve_measured.json"
RUNCFG = ROOT / "results/calibration/caiso260_demand_vintage/run_config.json"
OUT = ROOT / "results/calibration/_caiso266_belly_margin_identity.json"
M1_TABLE = ROOT / "results/calibration/_caiso265_m1.json"

YEARS = (2023, 2024, 2025)
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")
# Cumulative hours before the 1st of each month, non-leap calendar — the
# repo's own hour-of-year anchor (data/eia930/frames._MONTH_START_HOUR).
MONTH_START = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
# The gap population: hours the model prices off a positive (gas-marginal)
# dual AND the market cleared under $20/MWh. Both legs are fixed here, not
# tuned: $20 is the top of the actual-price bin ladder in M1.
BELLY_ACTUAL_MAX = 20.0


def _eia930_hourly() -> pd.DataFrame:
    """EIA-930 CISO wide extract keyed to the non-leap hour-of-year index.

    Local-clock duplicates (the autumn DST repeat) are averaged and 29 Feb is
    dropped, so the frame aligns 1:1 with the model's 8,760-hour calendar.
    """
    e = pd.read_parquet(E930)
    ld = pd.to_datetime(e["Local date"])
    e = e.assign(
        _month=ld.dt.month,
        _day=ld.dt.day,
        _year=ld.dt.year,
        _hoy=[
            (MONTH_START[m - 1] + d - 1) * 24 + h
            for m, d, h in zip(ld.dt.month, ld.dt.day, e["Hour"].astype(int) - 1)
        ],
    )
    return e[~((e._month == 2) & (e._day == 29))]


def _decode_campd(b64: str, annual_twh: float | None, npl: float) -> np.ndarray:
    """Decode a bench plant's CF%-encoded CAMPD series to hourly MW.

    Byte-identical to ``legitimacy_diagnostics._decode_cf_bytes``; duplicated
    rather than imported so the probe runs without the solve stack.
    """
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    total = raw.sum()
    if annual_twh is not None and total > 0.0:
        return raw * (annual_twh * 1e6 / total)
    return raw / 100.0 * npl


def _bench_gas_panel(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (nameplate, hourly MW, class) for the bench's CAMPD gas panel."""
    path = ROOT / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"
    with gzip.open(path) as fh:
        plants = json.load(fh)["bench"]["plants"]
    npl, mw, grp = [], [], []
    for p in plants.values():
        if p.get("nodata") or not p.get("campd") or p["group"] not in GAS_CLASSES:
            continue
        cap = float(p.get("npl") or 0.0)
        npl.append(cap)
        mw.append(_decode_campd(p["campd"], p.get("c_ann"), cap))
        grp.append(p["group"])
    return np.array(npl), np.vstack(mw), np.array(grp)


def _year_frame(year: int, e930: pd.DataFrame) -> pd.DataFrame:
    """One 8,760-row frame carrying the model, the actual and the meters.

    ``pm`` is the scorer's own C3a model basis — the zone-demand-weighted mean
    over the run's zones — and reproduces the keeper's printed model side to
    the cent. ``w`` is the common weight vector both sides are decomposed on,
    so the bin/month contributions sum exactly to the printed gap.
    """
    sysf = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    price = sysf.pivot_table(index="hour", columns="zone", values="price")
    dem = sysf.pivot_table(index="hour", columns="zone", values="demand")
    dump = sysf.pivot_table(index="hour", columns="zone", values="dump").sum(axis=1)
    total_d = dem.sum(axis=1)
    ca_zones = [z for z in price.columns if not z.startswith("WECC")]

    actual = pd.read_parquet(ACTUAL)
    pa = actual[actual.year == year].set_index("hour")["rt"].reindex(range(8760))

    cls = pd.read_parquet(BUNDLE / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    cw = (
        cls.pivot_table(index="hour", columns="klass", values="mw")
        .reindex(range(8760))
        .fillna(0.0)
    )
    bands = pd.read_parquet(BUNDLE / f"class_band_hourly_{year}.parquet")
    bw = (
        bands.pivot_table(index="hour", columns=["klass", "band"], values="mw")
        .reindex(range(8760))
        .fillna(0.0)
    )
    store = pd.read_parquet(BUNDLE / f"storage_{year}.parquet")
    store = store[store["pass"] == "P1"]
    li = store[store.tech == "li_ion"].set_index("hour")
    ps = store[store.tech == "pumped_storage"].set_index("hour")

    df = pd.DataFrame(index=pd.RangeIndex(8760))
    df["month"] = [
        next(m for m in range(12, 0, -1) if h // 24 >= MONTH_START[m - 1])
        for h in df.index
    ]
    df["hod"] = df.index % 24
    df["pm"] = ((price * dem).sum(axis=1) / total_d).values
    df["pa"] = pa.values
    df["demand"] = total_d.values
    df["w"] = df.demand / df.demand.sum()
    df["contrib"] = (df.pm - df.pa) * df.w
    df["min_ca"] = price[ca_zones].min(axis=1).values
    df["dump"] = dump.values
    df["dsw"] = price["WECC_DSW"].values
    df["pnw"] = price["WECC_PNW"].values
    df["la_basin"] = price["LA_BASIN"].values
    df["np15"] = price["NP15"].values
    for k in ("solar", "wind", "hydro", "nuclear", "import", "biomass", "OTHER"):
        df["m_" + k] = cw[k].values if k in cw else 0.0
    df["m_gas"] = cw[[g for g in GAS_CLASSES if g in cw]].sum(axis=1).values
    committed = sum(
        bw[(k, "committed")].values
        for k in GAS_CLASSES
        if (k, "committed") in bw.columns
    )
    df["m_gas_committed"] = committed
    df["m_gas_econ"] = df.m_gas - df.m_gas_committed
    for k in GAS_CLASSES:
        df["m_" + k] = cw[k].values if k in cw else 0.0
    df["li_charge"] = li["charge_mw"].reindex(df.index).fillna(0.0).values
    df["li_discharge"] = li["discharge_mw"].reindex(df.index).fillna(0.0).values
    df["ps_charge"] = ps["charge_mw"].reindex(df.index).fillna(0.0).values

    ey = e930[e930._year == year].groupby("_hoy").mean(numeric_only=True)
    for col, name in (
        ("NG: SUN", "a_solar"),
        ("NG: WND", "a_wind"),
        ("NG: WAT", "a_hydro"),
        ("NG: NUC", "a_nuclear"),
        ("NG: NG", "a_gas_ba"),
        ("NG: OTH", "a_battery_net"),
        ("Total interchange", "a_interchange"),
        ("Demand", "a_demand_ba"),
    ):
        df[name] = ey[col].reindex(df.index).values
    df["a_import"] = -df.a_interchange
    df["a_battery_charge"] = (-df.a_battery_net).clip(lower=0.0)

    # Model price regime. F = every zone at or below the renewable/dump floor
    # (the model is spilling); M = some CA zone floored, others not;
    # G = every CA zone priced off a positive dual, i.e. thermal-marginal.
    df["regime"] = np.where(
        df.pm <= 0.5, "F", np.where(df.min_ca <= 0.5, "M", "G")
    )
    df["gap_set"] = (df.regime == "G") & (df.pa < BELLY_ACTUAL_MAX)
    return df


def m0_additive_vs_proportional() -> dict:
    """M0 — is the seasonal ordering a denominator artifact? (No.)"""
    rows = [r for r in json.load(open(M1_TABLE))["months"] if r["year"] >= 2023]
    delta = np.array([r["model"] - r["actual_load_weighted"] for r in rows])
    pct = np.array([r["err_load_weighted"] * 100.0 for r in rows])
    act = np.array([r["actual_load_weighted"] for r in rows])
    return {
        "n_months": len(rows),
        "corr_absolute_delta_vs_actual_price": round(
            float(np.corrcoef(delta, act)[0, 1]), 3
        ),
        "corr_pct_error_vs_actual_price": round(
            float(np.corrcoef(pct, act)[0, 1]), 3
        ),
        "mean_absolute_delta_usd_per_mwh": round(float(delta.mean()), 3),
        "min_absolute_delta": round(float(delta.min()), 3),
        "max_absolute_delta": round(float(delta.max()), 3),
    }


def m1_price_bins(df: pd.DataFrame) -> dict:
    """M1 — the annual gap decomposed on the ACTUAL price axis."""
    edges = [-1e9, 0, 10, 20, 30, 45, 60, 100, 1e9]
    labels = ["<0", "0-10", "10-20", "20-30", "30-45", "45-60", "60-100", ">100"]
    binned = pd.cut(df.pa, bins=edges, labels=labels)
    out = {}
    for lab, grp in df.groupby(binned, observed=False):
        out[str(lab)] = {
            "hours": int(len(grp)),
            "weight": round(float(grp.w.sum()), 4),
            "contrib": round(float(grp.contrib.sum()), 4),
            "mean_actual": round(float(grp.pa.mean()), 2),
            "mean_model": round(float(grp.pm.mean()), 2),
        }
    sub20 = df[df.pa < BELLY_ACTUAL_MAX]
    return {
        "total_gap": round(float(df.contrib.sum()), 4),
        "bins": out,
        "sub_20_contrib": round(float(sub20.contrib.sum()), 4),
        "sub_20_share_of_gap": round(
            float(sub20.contrib.sum() / df.contrib.sum()), 3
        ),
        "model_min_price": round(float(df.pm.min()), 2),
        "actual_min_price": round(float(df.pa.min()), 2),
        "hours_in_0_to_15_model": int(((df.pm >= 0) & (df.pm < 15)).sum()),
        "hours_in_0_to_15_actual": int(((df.pa >= 0) & (df.pa < 15)).sum()),
    }


def m3_regime_split(df: pd.DataFrame) -> dict:
    """M3 — the gap split by the MODEL's own price regime (the floor kill)."""
    out = {}
    for reg, grp in df.groupby("regime"):
        out[reg] = {
            "hours": int(len(grp)),
            "contrib": round(float(grp.contrib.sum()), 4),
            "mean_model": round(float(grp.pm.mean()), 2),
            "mean_actual": round(float(grp.pa.mean()), 2),
        }
    return out


def m4_composition(df: pd.DataFrame) -> dict:
    """M4/M10/M13 — what the gap-carrying hours are made of."""
    g = df[df.gap_set]
    return {
        "hours": int(len(g)),
        "contrib": round(float(g.contrib.sum()), 4),
        "model_price": round(float(g.pm.mean()), 2),
        "actual_price": round(float(g.pa.mean()), 2),
        "model_dump_mw": round(float(g.dump.mean()), 3),
        "solar": {
            "model": round(float(g.m_solar.mean()), 0),
            "metered_ba": round(float(g.a_solar.mean()), 0),
        },
        "import": {
            "model": round(float(g.m_import.mean()), 0),
            "metered_net_ba": round(float(g.a_import.mean()), 0),
        },
        "gas_vs_BA_NG_TRAP": {
            "model": round(float(g.m_gas.mean()), 0),
            "eia930_BA_NG": round(float(g.a_gas_ba.mean()), 0),
            "note": (
                "EIA-930 NG:NG is the WHOLE CISO balancing authority's gas, "
                "which is NOT the model's 85-plant CAMPD panel. Comparing them "
                "reads as a 3.6-5.5 GW model deficit that does not exist. Use "
                "the bench CEMS panel (m10) instead."
            ),
        },
        "battery_charge_caiso256_basis": {
            "model_li_ion": round(float(g.li_charge.mean()), 0),
            "metered_NG_OTH": round(float(g.a_battery_charge.mean()), 0),
            "model_pumped_storage": round(float(g.ps_charge.mean()), 0),
        },
        "congestion": {
            "la_basin_minus_dsw": round(float((g.la_basin - g.dsw).mean()), 2),
            "np15_minus_pnw": round(float((g.np15 - g.pnw).mean()), 2),
            "dsw_price": round(float(g.dsw.mean()), 2),
        },
        "hod_contrib": {
            int(h): round(float(v), 4)
            for h, v in g.groupby("hod").contrib.sum().items()
        },
        "month_contrib": {
            int(m): round(float(v), 4)
            for m, v in g.groupby("month").contrib.sum().items()
        },
    }


def m10_commitment_state(df: pd.DataFrame, year: int) -> dict:
    """M10 — reality's belly COMMITMENT state on the bench's own CEMS panel."""
    npl, mw, grp = _bench_gas_panel(year)
    sel = df.gap_set.values
    online = mw > np.maximum(0.005 * npl[:, None], 0.5)
    online_cap = (online * npl[:, None]).sum(axis=0)
    gen = mw.sum(axis=0)
    per_class = {}
    for k in sorted(set(grp)):
        m = grp == k
        per_class[k] = {
            "nameplate": round(float(npl[m].sum()), 0),
            "measured_online_cap": round(
                float((online[m] * npl[m, None]).sum(axis=0)[sel].mean()), 0
            ),
            "measured_gen": round(float(mw[m].sum(axis=0)[sel].mean()), 0),
            "model_gen": round(float(df.loc[sel, "m_" + k].mean()), 0),
        }
    return {
        "panel_plants": int(len(npl)),
        "panel_nameplate_mw": round(float(npl.sum()), 0),
        "measured_online_cap_mw": round(float(online_cap[sel].mean()), 0),
        "measured_gen_mw": round(float(gen[sel].mean()), 0),
        "measured_loading_when_online": round(
            float(gen[sel].sum() / online_cap[sel].sum()), 3
        ),
        "model_gas_mw": round(float(df.loc[sel, "m_gas"].mean()), 0),
        "measured_minus_model_gen_mw": round(
            float(gen[sel].mean() - df.loc[sel, "m_gas"].mean()), 0
        ),
        "model_gas_at_binding_floors_mw": round(
            float(df.loc[sel, "m_gas_committed"].mean()), 0
        ),
        "per_class": per_class,
    }


def m11_offer_band_sign() -> dict:
    """M11 — measured CC bands vs the keeper's armed values (pre-registered)."""
    meas = json.load(open(MEASURED))
    armed = json.load(open(RUNCFG))["scenario_config"]["offer_curve_by_group"]
    per_year = meas["_provenance"]["per_year_band_mults"]["CC_REGULAR"]
    rows = {}
    for band in ("committed", "econ_low", "econ_high", "peak"):
        a = armed["CC_REGULAR"][band]
        pooled = meas["CC_REGULAR"]["bands"].get(band) or meas["CC_REGULAR"][
            "unarmed"
        ].get(band)
        yrs = {y: per_year[band][y] for y in ("2023", "2024", "2025")}
        rows[band] = {
            "armed": a,
            "measured_pooled": pooled,
            "pooled_below_armed": bool(pooled < a),
            "per_year": yrs,
            "per_year_below_armed": sum(1 for v in yrs.values() if v < a),
        }
    n_pooled_below = sum(1 for r in rows.values() if r["pooled_below_armed"])
    return {
        "bands": rows,
        "pooled_bands_below_armed": n_pooled_below,
        "verdict": "LIVE" if n_pooled_below >= 3 else "CLOSED",
        "note": (
            "The pooled 3-year value is the only admissible one: rule 1 "
            "[R-STRUCT] condition (b) requires ONE config across every scored "
            "year, so a per-year multiplier cannot be selected."
        ),
    }


def m12_sizing(df: pd.DataFrame, year: int) -> dict:
    """M12 — the kill-before-solve arithmetic, plus the CA carbon-floor leg."""
    meas = json.load(open(MEASURED))
    prov = meas["_provenance"]
    carbon = prov["carbon_basis"]["usd_per_t"][str(year)]
    factor = prov["carbon_basis"]["co2_factor_t_per_mmbtu"]
    hr_cc = meas["CC_REGULAR"]["base_hr"]
    hr_ct = meas["CT_PEAKER"]["base_hr"]
    vom_cc = prov["vom_usd_per_mwh"]["CC_REGULAR"]
    vom_ct = prov["vom_usd_per_mwh"]["CT_PEAKER"]
    floor_cc = factor * hr_cc * carbon + vom_cc
    floor_ct = factor * hr_ct * carbon + vom_ct
    g = df[df.gap_set]
    gas = float(g.m_gas.mean())
    econ = float(g.m_gas_econ.mean())
    return {
        "model_lambda": round(float(g.pm.mean()), 2),
        "actual": round(float(g.pa.mean()), 2),
        "required_move": round(float(g.pa.mean() - g.pm.mean()), 2),
        "carbon_usd_per_t": carbon,
        "cc_zero_fuel_floor_usd_per_mwh": round(float(floor_cc), 2),
        "ct_zero_fuel_floor_usd_per_mwh": round(float(floor_ct), 2),
        "share_gap_hours_below_cc_zero_fuel_floor": round(
            float((g.pa < floor_cc).mean()), 3
        ),
        # Sensitivity on the emission factor: the committed surface uses
        # 0.057 t/MMBtu; EPA's pipeline-gas factor is 0.05306. The conclusion
        # does not turn on which is used, so both are reported.
        "cc_zero_fuel_floor_epa_factor": round(
            float(0.05306 * hr_cc * carbon + vom_cc), 2
        ),
        "share_below_cc_floor_epa_factor": round(
            float((g.pa < 0.05306 * hr_cc * carbon + vom_cc).mean()), 3
        ),
        "share_gap_hours_below_zero": round(float((g.pa < 0).mean()), 3),
        "model_gas_mw": round(gas, 0),
        "model_gas_at_binding_floors_mw": round(float(g.m_gas_committed.mean()), 0),
        "model_gas_economic_mw": round(econ, 0),
        "required_over_economic_ratio": round(gas / max(econ, 1e-9), 2),
        "prereg_kill_bar": 2.0,
        "prereg_kill_bar_fires": bool(gas / max(econ, 1e-9) > 2.0),
    }


def m13_export_outlet(df: pd.DataFrame) -> dict:
    """M13 — the model's import column is one-directional; CAISO is not."""
    g = df[df.gap_set]
    return {
        "model_annual_import_twh": round(float(df.m_import.sum() / 1e6), 2),
        "metered_annual_net_import_twh": round(float(df.a_import.sum() / 1e6), 2),
        "gap_hours_model_import_mw": round(float(g.m_import.mean()), 0),
        "gap_hours_metered_net_import_mw": round(float(g.a_import.mean()), 0),
        "metered_net_export_hours": int((df.a_import < 0).sum()),
        "metered_net_export_hours_in_gap_set": int((g.a_import < 0).sum()),
        "model_net_export_hours": int((df.m_import < 0).sum()),
    }


def main() -> None:
    e930 = _eia930_hourly()
    result = {
        "note": (
            "caiso-266 reproduction artifact. ZERO LP. Keeper "
            "2026-09-06-caiso-260-b1-demand (bundle caiso260_demand_vintage), "
            "unchanged. Model basis = the scorer's own zone-demand-weighted "
            "C3a model side; the decomposition weight vector is the model's "
            "own hourly demand, applied to BOTH sides, so contributions sum "
            "to the printed gap. Rule 22: 2023-2025 only."
        ),
        "m0_additive_vs_proportional": m0_additive_vs_proportional(),
        "m11_offer_band_sign": m11_offer_band_sign(),
        "years": {},
    }
    for year in YEARS:
        df = _year_frame(year, e930)
        result["years"][str(year)] = {
            "m1_price_bins": m1_price_bins(df),
            "m3_regime_split": m3_regime_split(df),
            "m4_composition": m4_composition(df),
            "m10_commitment_state": m10_commitment_state(df, year),
            "m12_sizing": m12_sizing(df, year),
            "m13_export_outlet": m13_export_outlet(df),
        }
    OUT.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT.relative_to(ROOT)}")
    for year in YEARS:
        y = result["years"][str(year)]
        print(
            f"{year}: gap {y['m1_price_bins']['total_gap']:+.3f} $/MWh | "
            f"G-regime n={y['m4_composition']['hours']} carries "
            f"{y['m3_regime_split']['G']['contrib']:+.3f} | "
            f"F-regime carries {y['m3_regime_split']['F']['contrib']:+.3f} | "
            f"actual below the CC zero-fuel floor in "
            f"{y['m12_sizing']['share_gap_hours_below_cc_zero_fuel_floor']:.1%}"
        )


if __name__ == "__main__":
    main()

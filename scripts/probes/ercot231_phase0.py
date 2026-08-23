#!/usr/bin/env python3
"""ercot-231 Phase-0: the non-AS tightness surface measured at the keeper miss set.

Implements PRECOMMIT-ercot231-nonas-tightness-2026-08-23 §5.4 (all factors) —
computed AFTER the precommit was pushed and blob-verified (blob ``526401e``).
Every series is consumed through the model's own loaders (or the frozen
ercot221_gates constructions) so the measurements ride the exact conventions
the solve rides:

* miss set — the keeper's committed ``system_2023.parquet`` demand-weighted
  P1 price vs the hub RT actual (``_member`` / ``_actual``, frozen);
* demand / interchange — ``market_sim.data.eia930.demand._load_ercot_hourly``
  (the ERCOT backcast demand basis, screened);
* by-fuel actuals — the same ``_ercot_hourly_frame`` rows (row i == model
  hour i, per the frame docstring);
* renewables potential — the built NP6 HSL parquet (the model's CF source).

Output: ``results/calibration/ercot231_phase0.json``. Read-only: no LP, no
solve, no model input is written. N2a's reachable-surface checks are HTTP
list reads with outcomes recorded verbatim (the ercot-228 attempt-log form).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
# Repo root too: zonal_shares' raw fallback imports scripts.data.curate_zonal_shares,
# exactly as the production solve (launched from the repo root) resolves it.
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ercot221_gates import _actual, _member  # noqa: E402  (frozen)

KEEPER = REPO / "results/calibration/ercot223_release_arm"
YEAR = 2023
DC_TIE_CAPABILITY_MW = 1256.0  # DC-E 600 + DC-N 220 + Railroad 300 + Eagle Pass 36 + Laredo VFT 100


def _pct(x: np.ndarray, qs=(10, 50, 90)) -> dict:
    x = np.asarray(x, dtype=float)
    out = {f"p{q}": round(float(np.percentile(x, q)), 1) for q in qs}
    out["min"] = round(float(x.min()), 1)
    out["max"] = round(float(x.max()), 1)
    out["mean"] = round(float(x.mean()), 1)
    return out


def _class_mw(df: pd.DataFrame, klass: str) -> np.ndarray:
    g = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    return (
        g.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0).to_numpy(float)
    )


def main() -> None:
    out: dict = {"probe": "ercot231_phase0", "year": YEAR}

    # ---- miss set (frozen constructions) -------------------------------
    m = _member(KEEPER, YEAR)
    a = _actual(YEAR)
    price = np.nan_to_num(m["price"])
    tail = np.nan_to_num(a) > 200.0
    miss = tail & (price <= 200.0)
    caught = tail & (price > 200.0)
    out["miss_set"] = {
        "tail_hours": int(tail.sum()),
        "caught": int(caught.sum()),
        "missed": int(miss.sum()),
        "phantom": int(((~tail) & (price > 200.0) & np.isfinite(a)).sum()),
    }

    # ---- model-loader demand + interchange -----------------------------
    from market_sim.data.eia930.demand import _load_ercot_hourly
    from market_sim.data.eia930.frames import _ercot_hourly_frame

    demand, ix = _load_ercot_hourly(YEAR)
    frame = _ercot_hourly_frame(YEAR)
    netgen = frame["Net generation"].to_numpy(float)

    # ---- N1: interchange at the miss set -------------------------------
    ident = demand + ix - netgen  # EIA balance identity on the loader series
    n1 = {
        "sign_convention": "positive = net export (EIA-930)",
        "interchange_at_miss": _pct(ix[miss]),
        "interchange_at_caught": _pct(ix[caught]),
        "interchange_annual": _pct(ix),
        "import_hours_at_miss": int((ix[miss] < 0).sum()),
        "export_hours_at_miss": int((ix[miss] > 0).sum()),
        "import_p50_share_of_capability": round(
            float(-np.percentile(ix[miss], 50)) / DC_TIE_CAPABILITY_MW, 3
        ),
        "max_import_share_of_capability": round(
            float(-ix[miss].min()) / DC_TIE_CAPABILITY_MW, 3
        ),
        "netting_identity_abs_mw": {
            "at_miss_max": round(float(np.abs(ident[miss]).max()), 2),
            "annual_p50": round(float(np.median(np.abs(ident))), 2),
            "annual_max": round(float(np.abs(ident).max()), 2),
        },
    }
    # By-neighbor split (N1a attribution driver), from the fetched EIA-930
    # BA-to-BA product (keyless bulk route; diba MW positive = ERCO exports).
    nb_path = REPO / "data/raw/eia-930-interchange/ERCO interchange hourly.parquet"
    if nb_path.exists():
        nb = pd.read_parquet(nb_path)
        # File order per diba is chronological (the fetcher writes UTC-ordered
        # rows); the hour-ending window slice [Jan-1 01:00 .. Jan-1 00:00 of
        # year+1] therefore maps position -> model hour. Verified against the
        # wide extract's Total interchange: p50 |CEN+SWPP - total| = 0.0 MW,
        # max 1.0 MW (rounding). 6 extract-gap hours per diba interpolated.
        lo = pd.Timestamp(f"{YEAR}-01-01 01:00:00")
        hi = pd.Timestamp(f"{YEAR + 1}-01-01 00:00:00")
        by = {}
        total_nb = None
        for diba, g in nb.groupby("diba", observed=True):
            g = g[(g["local_time"] >= lo) & (g["local_time"] <= hi)]
            if len(g) != 8760:
                continue
            series = (
                pd.Series(g["mw"].to_numpy(float))
                .interpolate()
                .bfill()
                .ffill()
                .to_numpy()
            )
            by[str(diba)] = series
            total_nb = series if total_nb is None else total_nb + series
        if by and total_nb is not None:
            n1["by_neighbor_at_miss"] = {
                d: _pct(s[miss]) for d, s in by.items()
            }
            n1["by_neighbor_sum_vs_total_abs"] = {
                "p50": round(float(np.median(np.abs(total_nb - ix))), 1),
                "max": round(float(np.max(np.abs(total_nb - ix))), 1),
            }
    out["n1_interchange"] = n1

    # ---- N3: renewables wedge at the miss set --------------------------
    cls = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{YEAR}.parquet")
    model_wind = _class_mw(cls, "wind")
    model_solar = _class_mw(cls, "solar")
    act_wind = frame["NG: WND"].interpolate().bfill().ffill().to_numpy(float)
    act_solar = frame["NG: SUN"].interpolate().bfill().ffill().to_numpy(float)
    hsl = pd.read_parquet(REPO / "data/raw/ercot-hsl/ercot_2023_hsl_hourly.parquet")
    hsl = hsl.sort_values("hour").reset_index(drop=True)
    wind_hsl = hsl["wind_hsl_mw"].to_numpy(float)
    solar_hsl = hsl["solar_hsl_mw"].to_numpy(float)
    wind_gen_np6 = hsl["wind_gen_mw"].to_numpy(float)
    solar_gen_np6 = hsl["solar_gen_mw"].to_numpy(float)
    wedge = (model_wind + model_solar) - (act_wind + act_solar)
    meas_curt = np.maximum(0.0, (wind_hsl - wind_gen_np6)) + np.maximum(
        0.0, (solar_hsl - solar_gen_np6)
    )
    out["n3_renewables"] = {
        "model_minus_actual_at_miss": _pct(wedge[miss]),
        "wind_wedge_at_miss_p50": round(
            float(np.median((model_wind - act_wind)[miss])), 1
        ),
        "solar_wedge_at_miss_p50": round(
            float(np.median((model_solar - act_solar)[miss])), 1
        ),
        "measured_curtailment_at_miss": _pct(meas_curt[miss]),
        "model_redelivery_vs_measured_curtailment_corr": round(
            float(np.corrcoef(wedge[miss], meas_curt[miss])[0, 1]), 3
        )
        if miss.sum() > 2
        else None,
        "np6_vs_eia930_gen_basis_p50": {
            "wind": round(float(np.median((wind_gen_np6 - act_wind)[miss])), 1),
            "solar": round(float(np.median((solar_gen_np6 - act_solar)[miss])), 1),
        },
    }
    # Zonal decomposition of MEASURED curtailment at the miss set (which NP6
    # regions carried the curtailed MW reality shed and the model redelivers).
    zon = pd.read_parquet(
        REPO / "data/raw/ercot-hsl/ercot_2023_hsl_zonal_hourly.parquet"
    )
    zon["curt"] = np.maximum(0.0, zon["hsl_mw"] - zon["gen_mw"])
    miss_hours = set(np.where(miss)[0].tolist())
    zm = zon[zon["hour"].isin(miss_hours)]
    by_region = (
        zm.groupby("region", observed=True)["curt"].mean().sort_values(ascending=False)
    )
    total = float(by_region.sum())
    out["n3_renewables"]["measured_curtailment_by_region_mean_mw_at_miss"] = {
        r: round(float(v), 1) for r, v in by_region.items() if v > 1.0
    }
    out["n3_renewables"]["west_family_share_of_curtailment"] = round(
        float(
            by_region.reindex(
                ["west", "farwest", "northwest", "panhandle", "centerwest"],
                fill_value=0.0,
            ).sum()
        )
        / total,
        3,
    ) if total > 0 else None
    # GTC coverage listing (N3-K leg 2): measured 2023 constraint names vs the
    # armed ERCOT_GTC_LINK_MAP; the unmapped names are adjudicated in the
    # map's own comment (intra-zone pockets unrepresentable in the 7-zone
    # reduction; N_TO_H deliberately absent as one of several parallel paths).
    try:
        from market_sim.data.gtc import load_gtc_hourly
        from market_sim.config.constants import ERCOT_GTC_LINK_MAP

        gtc_frame = load_gtc_hourly("ERCOT", YEAR)
        if gtc_frame is not None:
            present = sorted(gtc_frame["gtc"].unique())
            out["n3_renewables"]["gtc_coverage_2023"] = {
                "measured_constraints": present,
                "mapped": sorted(ERCOT_GTC_LINK_MAP),
                "unmapped": sorted(set(present) - set(ERCOT_GTC_LINK_MAP)),
            }
    except Exception as exc:  # clean partition absent
        out["n3_renewables"]["gtc_coverage_2023"] = {"error": str(exc)}

    # ---- N4: demand-side integrity -------------------------------------
    raw = pd.read_parquet(REPO / "data/raw/eia-930-hourly/ERCO hourly.parquet")
    local = raw["Local date"]
    raw = raw[
        (local.dt.year == YEAR)
        & ~((local.dt.month == 2) & (local.dt.day == 29))
    ].sort_values("UTC time")
    raw = raw.reset_index(drop=True)
    raw_demand = raw["Demand"].to_numpy(float)
    p0a_nan_at_miss = int(np.isnan(raw_demand[miss]).sum())
    p0a_nan_annual = int(np.isnan(raw_demand).sum())
    # screen/interpolation effect: loader demand differs from raw where repaired
    repaired = (~np.isclose(demand, raw_demand, atol=0.5)) | np.isnan(raw_demand)
    p0a_repaired_at_miss = int(repaired[miss].sum())

    # native-load system total on the parser's own hoy mapping (levels)
    xl = pd.read_excel(
        REPO / "data/raw/zone-specific-demand" / f"ERCOT_Native_Load_{YEAR}.xlsx"
    )
    he = xl["Hour Ending"].astype(str).str.split(" ", n=1, expand=True)
    date = pd.to_datetime(he[0], format="mixed", dayfirst=False)
    hod = he[1].str.slice(0, 2).astype(int) - 1
    month = date.dt.month.to_numpy()
    day = date.dt.day.to_numpy()
    keep = ~((month == 2) & (day == 29))
    # Month-start HOURS (days x 24). The native file is on PREVAILING time
    # (2023: March has 743 rows, November 721), so the naive hoy mapping is
    # 1 h off across the DST summer vs the fixed-offset model clock — the
    # +/-2 lag scan below absorbs that and reports the best-aligned lag.
    mstart = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24
    hoy = mstart[month[keep] - 1] + (day[keep] - 1) * 24 + hod.to_numpy()[keep]
    wz_cols = [
        c
        for c in ("COAST", "EAST", "NORTH", "NCENT", "SCENT", "SOUTH", "FWEST", "WEST")
        if c in xl.columns
    ]
    native_total = np.full(8760, np.nan)
    sums = xl.loc[keep, wz_cols].sum(axis=1).to_numpy(float)
    for h, v in zip(hoy, sums):
        if 0 <= h < 8760:
            native_total[h] = v if np.isnan(native_total[h]) else native_total[h]
    lag_stats = {}
    for lag in (-2, -1, 0, 1, 2):
        shifted = np.roll(native_total, lag)
        w = shifted - demand
        ok = miss & np.isfinite(w)
        lag_stats[str(lag)] = {
            "wedge_at_miss_p50": round(float(np.median(w[ok])), 1),
            "wedge_at_miss_p90abs": round(
                float(np.percentile(np.abs(w[ok]), 90)), 1
            ),
            "annual_mean_abs": round(float(np.nanmean(np.abs(w))), 1),
        }
    best_lag = min(
        lag_stats, key=lambda k: lag_stats[k]["annual_mean_abs"]
    )
    # Sign-consistency leg of N4-K at the best-aligned lag: the share of
    # miss-set hours whose wedge carries the median's sign.
    shifted = np.roll(native_total, int(best_lag))
    w_best = shifted - demand
    okb = miss & np.isfinite(w_best)
    med_sign = np.sign(np.median(w_best[okb]))
    sign_share = float((np.sign(w_best[okb]) == med_sign).mean())
    # The file's own ERCOT system-total column as a parse cross-check.
    ercot_col = np.full(8760, np.nan)
    if "ERCOT" in xl.columns:
        tot_col = xl.loc[keep, "ERCOT"].to_numpy(float)
        for h, v in zip(hoy, tot_col):
            if 0 <= h < 8760 and np.isnan(ercot_col[h]):
                ercot_col[h] = v
        col_vs_sum = float(np.nanmax(np.abs(ercot_col - native_total)))
    else:
        col_vs_sum = None

    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.eia930.zonal_shares import load_zonal_shares

    zone_names = get_iso_config("ERCOT").zone_names
    shares = load_zonal_shares("ERCOT", YEAR, zone_names)
    zonal = {"measured_shares_active": shares is not None}
    if shares is not None:
        zonal["miss_vs_annual_share_delta"] = {
            z: round(float(shares[i, miss].mean() - shares[i].mean()), 4)
            for i, z in enumerate(zone_names)
        }
    out["n4_demand"] = {
        "p0a_raw_nan_at_miss": p0a_nan_at_miss,
        "p0a_raw_nan_annual": p0a_nan_annual,
        "p0a_repaired_hours_at_miss": p0a_repaired_at_miss,
        "p0b_native_vs_eia930": {
            "by_lag_hours": lag_stats,
            "best_lag": int(best_lag),
            "native_rows_mapped": int(np.isfinite(native_total).sum()),
            "sign_consistency_share_at_best_lag": round(sign_share, 3),
            "median_sign": int(med_sign),
            "ercot_total_col_vs_wz_sum_max_abs": col_vs_sum,
        },
        "p0c_zonal": zonal,
    }

    # ---- N5: small/uncarried classes at the miss set -------------------
    sto = pd.read_parquet(KEEPER / "hourly" / f"storage_{YEAR}.parquet")
    sto = sto[sto["pass"] == "P1"] if "pass" in sto.columns else sto
    bat_net = (
        (sto.groupby("hour")["discharge_mw"].sum() - sto.groupby("hour")["charge_mw"].sum())
        .reindex(range(8760))
        .fillna(0.0)
        .to_numpy(float)
    )
    pairs = {
        "hydro": (_class_mw(cls, "hydro"), frame["NG: WAT"].to_numpy(float)),
        "other_biomass_oil": (
            _class_mw(cls, "OTHER") + _class_mw(cls, "biomass") + _class_mw(cls, "oil"),
            (frame["NG: OTH"].fillna(0.0) + frame["NG: UES"].fillna(0.0)).to_numpy(
                float
            ),
        ),
        "battery_net": (bat_net, frame["NG: BAT"].to_numpy(float)),
    }
    n5 = {}
    for name, (mod, act) in pairs.items():
        act = np.nan_to_num(act)
        n5[name] = {
            "model_at_miss_p50": round(float(np.median(mod[miss])), 1),
            "actual_at_miss_p50": round(float(np.median(act[miss])), 1),
            "uncarried_at_miss": _pct(np.maximum(0.0, act - mod)[miss]),
        }
    # context: the big-fuel closure at the miss set (model - actual)
    gas_model = sum(
        _class_mw(cls, k) for k in ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
    )
    coal_model = _class_mw(cls, "COAL_LIGNITE") + _class_mw(cls, "COAL_PRB")
    nuc_model = _class_mw(cls, "nuclear")
    n5["closure_context_model_minus_actual_p50"] = {
        "gas": round(float(np.median((gas_model - frame["NG: NG"].to_numpy(float))[miss])), 1),
        "coal": round(float(np.median((coal_model - frame["NG: COL"].to_numpy(float))[miss])), 1),
        "nuclear": round(float(np.median((nuc_model - frame["NG: NUC"].to_numpy(float))[miss])), 1),
    }
    out["n5_small_classes"] = n5

    # ---- N2: coverage documentation + N2a reachable-surface checks -----
    out["n2_coverage"] = {
        "instrument_table": {
            "CC_REGULAR/COAL/CT_PEAKER/ST_GAS": "60-Day DAM HSL water-fill (ercot_thermal_dam_availability family, class-hour mean PINNED to measured; + _plant site pins; + gas/coal event caps)",
            "CC_CHP/CT_CHP/ST_CHP": "CAMPD outage windows (DAM-excluded by design, scenarios.py; item-20 record: CC_CHP slope -1.41%/degC NEGATIVE)",
            "nuclear": "ercot_nuclear_unit_availability (measured unit availability)",
            "non-CAMPD plants": "ercot_noncampd_plant_availability (armed)",
            "coal seasonal": "coal_nameplate_summer_derate (armed)",
            "partial outages": "ercot_partial_outage_shaped_derate (item 24, armed)",
            "storage": "NO measured outage channel (bounded by G-BAT +/-25% and the n5 battery_net wedge)",
            "wind/solar": "NP6 HSL basis (N3)",
            "hydro/biomass/oil/OTHER": "carried as classes; no outage channel (bounded by n5)",
        },
    }
    attempts = []
    for target, url in [
        (
            "public doc list, Hourly Resource Outage Capacity (NP3-233, reportTypeId 13103) — SYSTEM-grain aggregate",
            "https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=13103",
        ),
        (
            "public doc list, Unplanned Resource Outages Report (NP1-346-ER, reportTypeId 22912) — per-unit, 60-day lag",
            "https://www.ercot.com/misapp/servlets/IceDocListJsonWS?reportTypeId=22912",
        ),
    ]:
        try:
            r = subprocess.run(
                ["curl", "-s", "-m", "30", "-w", "\\n%{http_code}", url],
                capture_output=True,
                text=True,
                timeout=40,
            )
            body, _, code = r.stdout.rpartition("\n")
            outcome = f"HTTP {code}"
            try:
                docs = json.loads(body)["ListDocsByRptTypeRes"]["DocumentList"]
                dates = [
                    d["Document"]["PublishDate"][:10]
                    for d in docs
                    if "Document" in d
                ]
                outcome += (
                    f", {len(dates)} documents, PublishDate range "
                    f"{min(dates)} .. {max(dates)}"
                    if dates
                    else ", 0 documents"
                )
            except Exception:
                outcome += f", body head: {body[:160]!r}"
        except Exception as exc:  # network wall / timeout
            outcome = f"request failed: {exc}"
        attempts.append({"target": target, "url": url, "outcome": outcome})
    out["n2_coverage"]["n2a_attempt_log"] = attempts

    dest = REPO / "results/calibration/ercot231_phase0.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()

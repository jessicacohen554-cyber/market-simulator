"""nyiso-208 — supplementary legs of the NYISO ramp-slope census (M4/M5/M6).

Zero LP. Reads `data/raw` only. The headline slopes (M1/M2/M3) come from running
the SHIPPED derive scripts directly; this probe covers the legs those scripts do
not print, pre-registered in
``results/calibration/PREREG-nyiso208-ramp-slope-census.md`` §4:

* **M4** — Capital_Hudson hot-limb slope with ``avail = nameplate`` (outage derate
  OFF), one change only. If it equals the shipped value the outage extract does
  not reach CH's plants, which KILLS this session's own P2 (guard-stale)
  hypothesis.
* **M5** — span search over {2023}, {2024}, {2025}, {2023,2024}, {2024,2025} on the
  shipped basis. **Pre-limited**: five comparisons against a +/-0.0010 window, so a
  hit is SUGGESTIVE ONLY and never identification (PREREG §4 M5, binding).
* **M6** — (a) share of CH hot days whose measured evening when-available CF is at
  or above the applied floor fraction ``frac(tmax)``; (b) CH hot-day median
  when-available CF inside the h14-21 window vs the complementary hours
  (the nyiso-203 §3 block-CF treatment, never applied to this zone).

Plus the PREREG's declared context (Pearson r, hot/mild median CF, hot-day count,
forced-energy sizing) and — LABELLED POST-HOC — the CF distribution stats that
bear on why CH's Pearson r is near zero.

The shipped derive-script functions are imported BY FILE PATH and called, never
re-implemented, so the statistics recomputed here are the scripts' own.

Run:  PYTHONPATH=. uv run python scripts/probes/_nyiso208_ramp_slope_census.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DIR, REPO_ROOT

ZONE = "Capital_Hudson"
YEARS = (2023, 2024, 2025)

# The frozen CH_ST_ev ramp family, reliability_floor_coeffs_NYISO.csv rows 46-47.
KNOT_T = (25.0, 38.0)
KNOT_F = (0.0, 0.3200)
FROZEN_SLOPE = 0.0246  # the prose slope; 0.0246 * 13 = 0.3198 -> 0.320
TOL = 0.0010  # PREREG §5 P1 window


def _load_shipped():
    """Import the shipped ST derive script by file path (never re-implemented)."""
    path = REPO_ROOT / "scripts" / "data" / "derive_nyiso_st_reliability_floor.py"
    spec = importlib.util.spec_from_file_location("_nyiso_st_derive", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def zone_hourly(mod, zone: str, years: tuple[int, ...]) -> pd.DataFrame:
    """Hourly fleet gross MW + available MW for a zone's ST_GAS fleet, pooled."""
    plant_npl, nameplate = mod.zone_steam_plant_codes(zone)
    codes = set(plant_npl)
    frames = []
    for yr in years:
        path = RAW_DIR / "campd-unit-level" / f"NY_{yr}.parquet"
        if not path.exists():
            continue
        c = pd.read_parquet(path)
        c = c[c["facilityId"].astype(int).isin(codes)].copy()
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        gross_h = c.groupby("ts")["grossLoad"].sum()
        avail_h = mod.zone_available_capacity(plant_npl, gross_h.index)
        g = pd.DataFrame({"gross": gross_h, "avail": avail_h})
        g["nameplate"] = nameplate
        g["date"] = g.index.normalize()
        g["hour"] = g.index.hour
        frames.append(g)
    return pd.concat(frames), nameplate


def tmax_series(zone: str) -> pd.Series:
    """The archived per-zone daily TMAX the shipped script's --no-fetch path reads."""
    arch = pd.read_csv(
        RAW_DIR / "nyiso-weather" / "nyiso_zone_tmax_daily.csv", parse_dates=["date"]
    )
    za = arch[arch["zone"] == zone]
    return za.set_index("date")["tmax_c"]


def daily_evening_cf(
    g: pd.DataFrame, tmax: pd.Series, denom: str, years: tuple[int, ...]
) -> pd.DataFrame:
    """Daily evening (HB14-21) fleet CF on a chosen denominator, joined to TMAX.

    ``denom='avail'`` is the shipped basis (nameplate net of unit outages);
    ``denom='nameplate'`` is the M4 derate-off variant, one change only.
    """
    sub = g[g.index.year.isin(years)]
    ev = sub[sub["hour"].isin(range(14, 22))]
    day = ev.groupby("date").agg(gross=("gross", "sum"), d=(denom, "sum"))
    cf = (day["gross"] / day["d"]).where(day["d"] > 0)
    out = pd.DataFrame({"cf": cf})
    out["tmax"] = out.index.map(tmax)
    return out.dropna()


def hot_slope(df: pd.DataFrame) -> tuple[float, int]:
    """The SHIPPED hot-limb construction: OLS of daily CF on (tmax - 25), hot days."""
    hot = df[df["tmax"] >= 25.0]
    if len(hot) < 2:
        return 0.0, len(hot)
    return float(np.polyfit(hot["tmax"] - 25.0, hot["cf"], 1)[0]), len(hot)


def applied_frac(tmax: np.ndarray) -> np.ndarray:
    """The model's own composition: np.interp over the family's knots (core.py)."""
    return np.interp(tmax, KNOT_T, KNOT_F)


def main() -> None:
    mod = _load_shipped()
    tmax = tmax_series(ZONE)
    g, nameplate = zone_hourly(mod, ZONE, YEARS)
    shipped = daily_evening_cf(g, tmax, "avail", YEARS)
    out: dict = {
        "session": "nyiso-208",
        "object": "CH_ST_ev ramp family (reliability_floor_coeffs_NYISO.csv rows 46-47)",
        "zone": ZONE,
        "nameplate_mw": round(nameplate, 1),
        "frozen_slope_per_c": FROZEN_SLOPE,
        "frozen_cap_knot": KNOT_F[1],
        "prereg": "results/calibration/PREREG-nyiso208-ramp-slope-census.md",
    }

    # --- M4: derate ON (shipped) vs derate OFF (nameplate), one change only ----
    s_avail, n_hot = hot_slope(shipped)
    nameplate_basis = daily_evening_cf(g, tmax, "nameplate", YEARS)
    s_npl, _ = hot_slope(nameplate_basis)
    outage_hours = int((g["avail"] < g["nameplate"] - 1e-6).sum())
    out["M4_availability_sensitivity"] = {
        "slope_shipped_avail_basis": round(s_avail, 6),
        "slope_nameplate_basis": round(s_npl, 6),
        "identical_to_4dp": round(s_avail, 4) == round(s_npl, 4),
        "hours_with_any_outage_derate": outage_hours,
        "hours_total": int(len(g)),
        "outage_derate_share_of_hours": round(outage_hours / max(len(g), 1), 4),
        "n_hot_days": n_hot,
        "note": (
            "If the extract does not reach CH's plants, no extract-drift story "
            "can explain a CH gap -- this KILLS the session's own P2 hypothesis."
        ),
    }

    # --- M5: span search (PRE-LIMITED; a hit is SUGGESTIVE ONLY, never ID) -----
    spans = [(2023,), (2024,), (2025,), (2023, 2024), (2024, 2025), YEARS]
    m5 = {}
    for sp in spans:
        df = daily_evening_cf(g, tmax, "avail", sp)
        s, n = hot_slope(df)
        m5["_".join(str(y) for y in sp)] = {
            "slope": round(s, 6),
            "n_hot_days": n,
            "within_tol_of_frozen": bool(abs(s - FROZEN_SLOPE) <= TOL),
        }
    out["M5_span_search"] = {
        "spans": m5,
        "any_span_reproduces": any(v["within_tol_of_frozen"] for v in m5.values()),
        "binding_caveat": (
            "PREREG §4 M5: five extra comparisons against a +/-0.0010 window. A hit "
            "is SUGGESTIVE ONLY and is never reported as identification."
        ),
    }

    # --- M6(a): conduct -- is the floor above what the driver evidence supports? -
    hot = shipped[shipped["tmax"] >= 25.0].copy()
    hot["frac_frozen"] = applied_frac(hot["tmax"].to_numpy())
    hot["frac_measured_slope"] = np.clip(
        s_avail * (hot["tmax"] - 25.0), 0.0, KNOT_F[1]
    )
    out["M6a_conduct"] = {
        "n_hot_days": int(len(hot)),
        "share_hot_days_cf_ge_frozen_floor": round(
            float((hot["cf"] >= hot["frac_frozen"]).mean()), 4
        ),
        "share_hot_days_cf_ge_measured_slope_floor": round(
            float((hot["cf"] >= hot["frac_measured_slope"]).mean()), 4
        ),
        "median_hot_tmax_c": round(float(hot["tmax"].median()), 2),
        "max_hot_tmax_c": round(float(hot["tmax"].max()), 2),
        "frozen_frac_at_median_hot_tmax": round(
            float(applied_frac(np.array([hot["tmax"].median()]))[0]), 4
        ),
        "frozen_frac_at_max_hot_tmax": round(
            float(applied_frac(np.array([hot["tmax"].max()]))[0]), 4
        ),
        "median_hot_day_cf": round(float(hot["cf"].median()), 4),
        "P5_pass_gt_50pct": bool((hot["cf"] >= hot["frac_frozen"]).mean() > 0.50),
    }

    # --- M6(b): window -- does h14-21 select the zone's higher-output block? ----
    g_hot = g[g["date"].map(tmax).ge(25.0).fillna(False)].copy()
    g_hot["cf_h"] = (g_hot["gross"] / g_hot["avail"]).where(g_hot["avail"] > 0)
    inside = g_hot[g_hot["hour"].isin(range(14, 22))]["cf_h"].dropna()
    outside = g_hot[~g_hot["hour"].isin(range(14, 22))]["cf_h"].dropna()
    med_in, med_out = float(inside.median()), float(outside.median())
    ratio = med_in / med_out if med_out > 0 else float("inf")
    block = {}
    for lo in range(0, 24, 4):
        blk = g_hot[g_hot["hour"].isin(range(lo, lo + 4))]["cf_h"].dropna()
        block[f"h{lo:02d}-{lo + 3:02d}"] = round(float(blk.median()), 4)
    out["M6b_window"] = {
        "median_cf_inside_h14_21": round(med_in, 4),
        "median_cf_outside_h14_21": round(med_out, 4),
        "ratio_inside_over_outside": (
            round(ratio, 3) if np.isfinite(ratio) else "inf (outside median = 0)"
        ),
        "hot_day_block_median_cf": block,
        "P6_pass_ratio_ge_1p5": bool(ratio >= 1.5),
    }

    # --- declared context: sizing under the frozen vs the measured slope --------
    ev = g[g["hour"].isin(range(14, 22))].copy()
    ev["tmax"] = ev["date"].map(tmax)
    ev = ev.dropna(subset=["tmax"])
    fr_frozen = applied_frac(ev["tmax"].to_numpy())
    fr_meas = np.clip(s_avail * (ev["tmax"].to_numpy() - 25.0), 0.0, KNOT_F[1])
    floor_frozen = fr_frozen * ev["avail"].to_numpy()
    floor_meas = fr_meas * ev["avail"].to_numpy()
    meas_mw = ev["gross"].to_numpy()
    out["sizing_twh_2023_2025"] = {
        "floor_energy_demanded_frozen": round(floor_frozen.sum() / 1e6, 5),
        "floor_energy_demanded_measured_slope": round(floor_meas.sum() / 1e6, 5),
        "excess_over_metered_frozen": round(
            np.maximum(0.0, floor_frozen - meas_mw).sum() / 1e6, 5
        ),
        "excess_over_metered_measured_slope": round(
            np.maximum(0.0, floor_meas - meas_mw).sum() / 1e6, 5
        ),
        "metered_evening_energy": round(meas_mw.sum() / 1e6, 5),
        "note": (
            "Floor energy demanded = sum(frac x avail) over h14-21; excess over "
            "metered = sum(max(0, floor - metered)). NOT an LP result: the model's "
            "added energy also depends on what the LP would have dispatched anyway."
        ),
    }

    # --- POST-HOC DIAGNOSTIC (labelled): why is CH's Pearson r near zero? -------
    allday = shipped
    out["POSTHOC_cf_distribution"] = {
        "LABEL": "POST-HOC DIAGNOSTIC -- not pre-registered; explains the r, claims nothing",
        "pearson_r_cf_tmax_all_days": round(float(allday["cf"].corr(allday["tmax"])), 4),
        "spearman_r_cf_tmax_all_days": round(
            float(allday["cf"].corr(allday["tmax"], method="spearman")), 4
        ),
        "cf_max": round(float(allday["cf"].max()), 4),
        "cf_p99": round(float(allday["cf"].quantile(0.99)), 4),
        "share_days_cf_gt_1": round(float((allday["cf"] > 1.0).mean()), 4),
        "share_days_cf_eq_0": round(float((allday["cf"] <= 1e-9).mean()), 4),
        "share_hot_days_cf_eq_0": round(float((hot["cf"] <= 1e-9).mean()), 4),
        "n_days_total": int(len(allday)),
    }

    out["verdict_inputs"] = {
        "M1_slope_shipped": round(s_avail, 6),
        "P1_reproduces_within_0.0010": bool(abs(s_avail - FROZEN_SLOPE) <= TOL),
        "P2_guard_stale_below_0.0200": bool(s_avail < 0.0200),
        "ratio_measured_over_frozen": round(s_avail / FROZEN_SLOPE, 3),
    }

    dest = Path(REPO_ROOT) / "results" / "calibration" / "_nyiso208_ramp_slope_census.json"
    dest.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()

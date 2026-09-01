"""caiso-232 — ZERO-SOLVE decomposition of the C3a overrun on two axes the
prior C3a lane never measured: **solar availability** and **hour-of-day within
month**, on keeper ``2026-09-01-caiso-231-b1-ungrounded``.
NO LP, NO SOLVE, NOTHING ARMED — committed bytes only.

Why this probe exists: the owner's 2026-09-01 handoff names two symptoms —
"overprice in mornings while solar is available" and "Decembers" — and asks
whether price formation adjusts correctly around solar. The standing C3a
record does not answer that on its own axes. FINDING-caiso202 §B bucketed the
residual by **actual price**; FINDING-caiso227 §A bucketed it by **month
block** (Sep–Dec). Neither bucketed by solar availability, and neither split
the residual into a **level** part (month mean) and a **shape** part
(within-month hour-of-day deviation) — which is the split that separates the
owner's two symptoms into two different defects.

Sections:

* **A** — level/shape split. The month × hour-of-day residual map, then the
  same map with each (year, month) mean removed, isolating diurnal SHAPE from
  monthly LEVEL.
* **B** — the solar-response test. Residual vs measured solar-potential share
  of load, and the within-month shape error ordered by the **measured solar
  ramp rate** (Δ solar HSL, MW/h) in the morning (h6–11) and evening (h16–21)
  windows. Also the diurnal amplitude ratio (model daily price range ÷ actual).
* **C** — the phase control. Cross-correlation of model vs measured solar and
  of model λ vs actual RT at lags −3…+3 h, to rule out a time-alignment
  artifact as the cause of a morning-vs-evening residual dipole.
* **D** — the spill mechanism test. Does the LP's zero-MC solar actually set
  λ when it spills? Model λ binned by spill fraction; and model annual spill
  against CAISO's **published curtailment split by reason** (Local vs System,
  ``data/raw/caiso-curtailment``), the measurement that identifies which half
  of real curtailment a zonal network can and cannot reproduce.
* **E** — the December object. December's residual by hour-of-day (is it flat
  = level, or peaked = shape), the model's monthly import volume and measured
  WECC hub prices (MALIN / PALOVRDE), and the pooled 36-month correlation of
  the monthly residual with import volume and with the hub premium.

Every input is committed: the keeper's ``hourly/`` sidecars, the actual-LMP
reference (``rt`` + ``da``), the measured CAISO HSL potential/delivered
series, the EIA-930 CISO hourly fuel mix, the measured WECC intertie hub
parquet, and CAISO's published production-and-curtailments workbooks.

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso232_solar_ramp_december_decomp.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

BUNDLE = Path("results/calibration/caiso231_b1_ungrounded/hourly")
OUT = Path("results/calibration/_caiso232_solar_ramp_december_decomp.json")
YEARS = (2023, 2024, 2025)

# The five in-CA model zones. WECC_PNW / WECC_DSW are import nodes and are
# excluded from the CA load-weighted lambda (the C3a construction).
CA_ZONES = ["NP15", "ZP26", "LA_BASIN", "SDGE", "SP15_rest"]

# Morning / evening windows used for the ramp-ordered shape test.
MORNING = (6, 11)
EVENING = (16, 21)


def _load_panel() -> pd.DataFrame:
    """Assemble the hourly panel: model λ, actuals, measured solar, model classes.

    Returns one row per (year, hour) with the CA load-weighted model λ, the
    RT/DA actuals, the measured solar potential (HSL) and delivered series,
    and the model's per-class dispatch.
    """
    act = pd.read_parquet("data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet")
    frames = []
    for yr in YEARS:
        sysd = pd.read_parquet(BUNDLE / f"system_{yr}.parquet")
        sysd = sysd[sysd["zone"].isin(CA_ZONES)]
        lam = (
            sysd.groupby("hour")
            .apply(
                lambda d: pd.Series(
                    {
                        "model_lmp": np.average(d["price"], weights=d["demand"]),
                        "load": d["demand"].sum(),
                    }
                ),
                include_groups=False,
            )
            .reset_index()
        )
        cls = pd.read_parquet(BUNDLE / f"class_hourly_{yr}.parquet")
        piv = cls.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum")
        hsl = pd.read_parquet(f"data/raw/caiso-hsl/caiso_{yr}_hsl_hourly.parquet")

        df = (
            lam.merge(act[act["year"] == yr][["hour", "rt", "da"]], on="hour")
            .merge(hsl, on="hour")
            .join(piv, on="hour")
        )
        df["year"] = yr
        ts = pd.Timestamp(f"{yr}-01-01") + pd.to_timedelta(df["hour"], unit="h")
        df["month"], df["hod"] = ts.dt.month, ts.dt.hour
        df["gap_rt"] = df["model_lmp"] - df["rt"]
        df["gap_da"] = df["model_lmp"] - df["da"]
        df["solar_pot_share"] = df["solar_hsl_mw"].clip(lower=0) / df["load"]
        df["solar_ramp"] = df["solar_hsl_mw"].diff().fillna(0.0)
        df["spill"] = df["solar_hsl_mw"].clip(lower=0) - df["solar"]
        frames.append(df)

    panel = pd.concat(frames, ignore_index=True)
    # LEVEL = the (year, month) mean residual; SHAPE = the deviation from it.
    for basis in ("rt", "da"):
        panel[f"gap_{basis}_shape"] = panel[f"gap_{basis}"] - panel.groupby(
            ["year", "month"]
        )[f"gap_{basis}"].transform("mean")
    return panel


def _load_curtailment() -> pd.DataFrame:
    """CAISO published 5-min curtailment, summed to (year, month, hod) by Reason.

    MW-per-5-min are converted to MWh by /12 (the workbook's own convention,
    matching scripts/build_caiso_hsl.py).
    """
    frames = []
    for yr in YEARS:
        c = pd.read_excel(
            f"data/raw/caiso-curtailment/productionandcurtailmentsdata_{yr}.xlsx",
            sheet_name="Curtailments",
        )
        c.columns = [str(x).strip() for x in c.columns]
        c["Date"] = pd.to_datetime(c["Date"])
        c["hod"] = c["Hour"].astype(int) - 1  # workbook is hour-ending 1..24
        c["month"] = c["Date"].dt.month
        g = (
            c.groupby(["month", "hod", "Reason"])["Solar Curtailment"]
            .sum()
            .div(12)
            .unstack("Reason")
            .fillna(0.0)
            .reset_index()
        )
        g["year"] = yr
        frames.append(g)
    return pd.concat(frames, ignore_index=True)


def _lagged_corr(a: np.ndarray, b: np.ndarray, lags=(-3, -2, -1, 0, 1, 2, 3)) -> dict:
    """corr(a shifted by `lag`, b); positive lag = `a` later than `b`."""
    out = {}
    for lag in lags:
        if lag == 0:
            x, y = a, b
        elif lag > 0:
            x, y = a[lag:], b[:-lag]
        else:
            x, y = a[:lag], b[-lag:]
        ok = np.isfinite(x) & np.isfinite(y)
        out[str(lag)] = round(float(np.corrcoef(x[ok], y[ok])[0, 1]), 4) if ok.sum() > 2 else None
    return out


def main() -> None:
    panel = _load_panel()
    curt = _load_curtailment()
    res: dict = {
        "keeper": "2026-09-01-caiso-231-b1-ungrounded",
        "bundle": str(BUNDLE.parent),
        "note": "ZERO-SOLVE. Committed bytes only. No mechanism armed, nothing registered.",
    }

    # ---- A: level / shape ------------------------------------------------
    res["A_level_by_month"] = {
        str(y): panel[panel.year == y].groupby("month")[["gap_rt", "gap_da"]].mean().round(3).to_dict()
        for y in YEARS
    }
    res["A_shape_by_hod"] = {
        str(y): panel[panel.year == y].groupby("hod")[["gap_rt_shape", "gap_da_shape"]].mean().round(3).to_dict()
        for y in YEARS
    }
    res["A_raw_gap_by_hod"] = {
        str(y): panel[panel.year == y].groupby("hod")[["model_lmp", "rt", "da", "gap_rt"]].mean().round(3).to_dict()
        for y in YEARS
    }

    # ---- B: solar response ----------------------------------------------
    sbins = [-0.01, 0.001, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 2.0]
    res["B_by_solar_share"] = {}
    for y in YEARS:
        s = panel[panel.year == y].copy()
        s["b"] = pd.cut(s["solar_pot_share"], sbins)
        t = s.groupby("b", observed=True).agg(
            hours=("gap_rt", "size"), model=("model_lmp", "mean"),
            rt=("rt", "mean"), da=("da", "mean"),
            gap_rt=("gap_rt", "mean"), gap_da=("gap_da", "mean"))
        res["B_by_solar_share"][str(y)] = {str(k): v for k, v in t.round(3).to_dict("index").items()}

    res["B_shape_by_ramp"] = {}
    for label, (lo, hi) in (("morning_h6_11", MORNING), ("evening_h16_21", EVENING)):
        w = panel[panel.hod.between(lo, hi)].copy()
        w["b"] = pd.qcut(w["solar_ramp"], 6, duplicates="drop")
        t = w.groupby("b", observed=True).agg(
            hours=("gap_rt_shape", "size"), ramp_mw_per_h=("solar_ramp", "mean"),
            shape_err=("gap_rt_shape", "mean"), model=("model_lmp", "mean"), rt=("rt", "mean"))
        res["B_shape_by_ramp"][label] = {str(k): v for k, v in t.round(3).to_dict("index").items()}

    amp = {}
    for y in YEARS:
        s = panel[panel.year == y].copy()
        s["day"] = s["hour"] // 24
        g = s.groupby("day").agg(m=("model_lmp", lambda x: x.max() - x.min()),
                                 a=("rt", lambda x: x.max() - x.min()))
        amp[str(y)] = {"model_daily_range": round(float(g.m.mean()), 2),
                       "actual_daily_range": round(float(g.a.mean()), 2),
                       "ratio": round(float(g.m.mean() / g.a.mean()), 4)}
    res["B_diurnal_amplitude"] = amp

    # ---- C: phase control ------------------------------------------------
    res["C_phase"] = {}
    for y in YEARS:
        s = panel[panel.year == y].sort_values("hour")
        res["C_phase"][str(y)] = {
            "model_solar_vs_measured_solar": _lagged_corr(
                s["solar"].to_numpy(float), s["solar_gen_mw"].to_numpy(float), (-2, -1, 0, 1, 2)),
            "model_lambda_vs_actual_rt": _lagged_corr(
                s["model_lmp"].to_numpy(float), s["rt"].to_numpy(float)),
        }

    # ---- D: spill mechanism + curtailment reason split -------------------
    res["D_lambda_by_spill"] = {}
    for y in YEARS:
        s = panel[(panel.year == y) & (panel.solar_hsl_mw > 2000)].copy()
        s["b"] = pd.cut(s["spill"] / s["solar_hsl_mw"].clip(lower=1),
                        [-1, 0.001, 0.02, 0.05, 0.10, 0.20, 1.0])
        t = s.groupby("b", observed=True).agg(
            hours=("model_lmp", "size"), spill_mw=("spill", "mean"),
            model=("model_lmp", "mean"), rt=("rt", "mean"), da=("da", "mean"))
        res["D_lambda_by_spill"][str(y)] = {str(k): v for k, v in t.round(3).to_dict("index").items()}

    reason = {}
    for y in YEARS:
        c = curt[curt.year == y]
        s = panel[panel.year == y]
        loc, sysm = float(c["Local"].sum()), float(c["System"].sum())
        reason[str(y)] = {
            "measured_local_twh": round(loc / 1e6, 4),
            "measured_system_twh": round(sysm / 1e6, 4),
            "local_share_of_total": round(loc / (loc + sysm), 4),
            "model_spill_twh": round(float(s["spill"].clip(lower=0).sum()) / 1e6, 4),
            "model_spill_minus_measured_system_twh": round(
                (float(s["spill"].clip(lower=0).sum()) - sysm) / 1e6, 4),
            "morning_share_of_local_h6_11": round(
                float(c[c.hod.between(*MORNING)]["Local"].sum() / max(loc, 1.0)), 4),
        }
    res["D_curtailment_reason"] = reason
    res["D_curtailment_by_hod"] = {
        str(y): curt[curt.year == y].groupby("hod")[["Local", "System"]].sum().round(1).to_dict()
        for y in YEARS
    }

    # shape error vs measured local curtailment, over month x hod cells
    cells = panel.groupby(["year", "month", "hod"])["gap_rt_shape"].mean().reset_index()
    j = cells.merge(curt, on=["year", "month", "hod"], how="left").dropna(subset=["Local"])
    res["D_shape_vs_local_corr"] = {
        str(y): {
            "corr_shape_local": round(float(np.corrcoef(
                j[j.year == y].gap_rt_shape, j[j.year == y].Local)[0, 1]), 3),
            "corr_shape_system": round(float(np.corrcoef(
                j[j.year == y].gap_rt_shape, j[j.year == y].System)[0, 1]), 3),
            "n_cells": int((j.year == y).sum()),
        }
        for y in YEARS
    }

    # ---- E: the December object ------------------------------------------
    hubs = pd.read_parquet("data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet")
    hp = hubs.pivot_table(index=["year", "hour"], columns="hub", values="price").reset_index()
    mh = panel.merge(hp, on=["year", "hour"], how="left")

    res["E_december_by_hod"] = {
        str(y): mh[(mh.year == y) & (mh.month == 12)]
        .groupby("hod")[["model_lmp", "rt", "da", "gap_rt", "solar", "import", "CC_REGULAR", "hydro"]]
        .mean().round(2).to_dict()
        for y in YEARS
    }
    res["E_monthly_imports_and_hubs"] = {
        str(y): mh[mh.year == y].groupby("month").agg(
            model=("model_lmp", "mean"), rt=("rt", "mean"), da=("da", "mean"),
            gap_rt=("gap_rt", "mean"), imports_mw=("import", "mean"),
            malin=("MALIN", "mean"), palovrde=("PALOVRDE", "mean")).round(2).to_dict()
        for y in YEARS
    }
    g = mh.groupby(["year", "month"]).agg(
        gap=("gap_rt", "mean"), imp=("import", "mean"),
        malin=("MALIN", "mean"), rt=("rt", "mean")).dropna()
    res["E_pooled_corr_36_months"] = {
        "corr_gap_imports": round(float(np.corrcoef(g.gap, g.imp)[0, 1]), 3),
        "corr_gap_malin_premium_vs_rt": round(float(np.corrcoef(g.gap, g.malin - g.rt)[0, 1]), 3),
        "n_months": int(len(g)),
    }
    res["E_december_flatness"] = {
        str(y): {
            "gap_min_hod": round(float(mh[(mh.year == y) & (mh.month == 12)]
                                       .groupby("hod").gap_rt.mean().min()), 2),
            "gap_max_hod": round(float(mh[(mh.year == y) & (mh.month == 12)]
                                       .groupby("hod").gap_rt.mean().max()), 2),
        }
        for y in YEARS
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(f"wrote {OUT}")
    print(json.dumps(res["B_diurnal_amplitude"], indent=1))
    print(json.dumps(res["D_curtailment_reason"], indent=1))
    print(json.dumps(res["E_pooled_corr_36_months"], indent=1))


if __name__ == "__main__":
    main()

"""miso-167 — MISO 2025 summer-scarcity anatomy (READ-ONLY, no LP solved).

Answers the owner's re-charter ("2025 MISO needs to be calibrated in summer
scarcity") by measuring WHERE the keeper 2026-08-16-miso-160-wefor-shape misses
and WHICH of the candidate causes survives. Everything here is a MEASUREMENT of
committed artifacts against measured actuals; nothing is fed back into a solve
(rule 13 [R-MEASURED]).

Sources, all committed:
  model P1 zonal price/demand/slack  results/calibration/miso160_wefor_B/hourly/system_<y>.parquet
  model P1 reserve family duals      .../reserve_family_<y>.parquet
  model P1 class dispatch            .../class_hourly_<y>.parquet
  measured RT/DA hourly LMP          data/raw/_validation-source/actual_lmp_hourly_MISO.parquet
  measured demand + interchange      data/raw/MISO_region.parquet          (EIA-930)
  measured RT ASM MCP by product     data/raw/MISO-AS/asm_rtmcp_zonal_<y>.parquet
  measured RT cleared reserve MW     data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet

Stages:
  1 tail      — model vs actual across the scarcity tail, and the model's reserve
                posture inside the actual scarcity hours
  2 inputs    — is it LOAD or TRADE? model demand/net-imports vs EIA-930
  3 slope     — summer price-vs-demand decile curve; how flat the model's stack is
  4 reserves  — model reserve requirement/dual vs MISO's OWN cleared MW and ASM MCP
  5 foreseen  — splits the scarcity miss into DA-foreseen (reachable by a
                deterministic LP) vs RT-only (a perfect-foresight model-class limit)

Hour key throughout: the model's chronological non-leap 8760 CST calendar, the
same key ``scripts/data/derive_miso_hub_lmp.py`` writes the validation series on,
so model and actual are hour-for-hour comparable with no re-alignment.

Run:  .venv/bin/python scripts/probes/_miso167_summer_scarcity_instrument.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = ROOT / "results" / "calibration" / "miso160_wefor_B" / "hourly"
ACTUAL = ROOT / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_MISO.parquet"
ASDIR = ROOT / "data" / "raw" / "MISO-AS"
YEARS = (2023, 2024, 2025)

# Fixed non-leap calendar: hour-of-year at which each month begins.
MONTH_START = [0, 744, 1416, 2160, 2880, 3624, 4344, 5088, 5832, 6552, 7296, 8016, 8760]
SUMMER = (MONTH_START[5], MONTH_START[9])  # Jun 1 .. Sep 30 inclusive
HE = [f"he{i:02d}" for i in range(1, 25)]

# A scarcity hour is one MISO's RT market itself priced above this.
SCARCE_RT = 200.0
# "Day-ahead foreseen": MISO's own DA market — itself a deterministic
# co-optimized LP with foresight — also priced the hour up. Above this line a
# deterministic model is *capable* of reaching the hour; below it the RT spike is
# an operational event that perfect-foresight hourly dispatch cannot contain.
FORESEEN_DA = 150.0


# --------------------------------------------------------------------------
# loaders
# --------------------------------------------------------------------------
def month_of(hour: np.ndarray) -> np.ndarray:
    """Return the 1-12 month index for each hour-of-year on the fixed calendar."""
    return np.searchsorted(np.array(MONTH_START[1:]), hour, side="right") + 1


def model_system(year: int) -> pd.DataFrame:
    """Load-weighted P1 system price, total demand, slack and dump, per hour."""
    d = pd.read_parquet(BUNDLE / f"system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    d["pw"] = d["price"] * d["demand"]
    g = d.groupby("hour").agg(
        pw=("pw", "sum"),
        demand=("demand", "sum"),
        slack=("slack", "sum"),
        dump=("dump", "sum"),
        pmax=("price", "max"),
    )
    g["price"] = g["pw"] / g["demand"]
    return g.drop(columns="pw").reset_index()


def model_reserve(year: int) -> pd.DataFrame:
    """Per-hour reserve totals summed across families (dual reported as max)."""
    d = pd.read_parquet(BUNDLE / f"reserve_family_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return (
        d.groupby("hour")
        .agg(
            req_mw=("requirement_mw", "sum"),
            held_mw=("held_mw", "sum"),
            shortfall_mw=("shortfall_mw", "sum"),
            dual_max=("dual", "max"),
        )
        .reset_index()
    )


def actual(year: int) -> pd.DataFrame:
    a = pd.read_parquet(ACTUAL)
    return a[a["year"] == year][["hour", "rt", "da"]].reset_index(drop=True)


def e930_hourly(year: int) -> pd.DataFrame:
    """EIA-930 MISO demand (D) and total interchange (TI) on the CST hour key.

    The 930 extract is UTC-stamped; the model's calendar is fixed Central
    STANDARD time (UTC-6) with Feb 29 dropped.
    """
    d = pd.read_parquet(ROOT / "data" / "raw" / "MISO_region.parquet")
    d = d[d["type"].isin(["D", "TI", "NG"])].copy()
    d["cst"] = d["period"] - pd.Timedelta(hours=6)
    d = d[d["cst"].dt.year == year]
    d = d[~((d["cst"].dt.month == 2) & (d["cst"].dt.day == 29))]
    w = d.pivot_table(index="cst", columns="type", values="value_mwh", aggfunc="first").sort_index()
    w["hour"] = np.arange(len(w))
    return w.reset_index()[["hour", "D", "TI", "NG"]]


def _est_he_to_cst_hour(frame: pd.DataFrame, year: int, k: pd.Series) -> pd.Series:
    """Map an hour-ending-k EST stamp to the model's CST hour-of-year.

    MISO market reports are hour-ending 1-24 Eastern STANDARD time year-round
    (UTC-5); hour-ending k is hour-beginning k-1 EST, which is hour k-2 CST.
    """
    ts = frame["date"] + pd.to_timedelta(k - 2, unit="h")
    return ts


def asm_mcp(year: int) -> pd.DataFrame:
    """MISO-Wide RT ancillary MCP by product on the model's CST hour key."""
    d = pd.read_parquet(ASDIR / f"asm_rtmcp_zonal_{year}.parquet")
    d = d[d["zone"] == "Miso-Wide"].copy()
    d["date"] = pd.to_datetime(d["date"])
    long = d.melt(id_vars=["date", "product"], value_vars=HE, var_name="he", value_name="mcp")
    long["k"] = long["he"].str[2:].astype(int)
    long["ts"] = _est_he_to_cst_hour(long, year, long["k"])
    long = long[(long["ts"].dt.year == year)]
    long = long[~((long["ts"].dt.month == 2) & (long["ts"].dt.day == 29))]
    base = pd.Timestamp(f"{year}-01-01")
    long["hour"] = ((long["ts"] - base).dt.total_seconds() // 3600).astype(int)
    long = long[(long["hour"] >= 0) & (long["hour"] < 8760)]
    w = long.pivot_table(index="hour", columns="product", values="mcp", aggfunc="first")
    return w.reset_index()


def asm_cleared(year: int) -> pd.DataFrame:
    """MISO RT cleared reserve MW (all regions, by product) on the CST hour key."""
    d = pd.read_parquet(ASDIR / f"asm_rt_cleared_mw_{year}.parquet")
    d["date"] = pd.to_datetime(d["date"])
    d["ts"] = _est_he_to_cst_hour(d, year, d["hour_end_est"])
    d = d[(d["ts"].dt.year == year)]
    d = d[~((d["ts"].dt.month == 2) & (d["ts"].dt.day == 29))]
    base = pd.Timestamp(f"{year}-01-01")
    d["hour"] = ((d["ts"] - base).dt.total_seconds() // 3600).astype(int)
    d = d[(d["hour"] >= 0) & (d["hour"] < 8760)]
    tot = d.groupby("hour")["cleared_mw"].sum().rename("miso_cleared_mw").reset_index()
    byp = d.pivot_table(index="hour", columns="product", values="cleared_mw", aggfunc="sum").reset_index()
    return tot.merge(byp, on="hour")


def assemble(year: int) -> pd.DataFrame:
    """One frame per hour joining every model and measured series."""
    df = (
        model_system(year)
        .merge(model_reserve(year), on="hour")
        .merge(actual(year), on="hour")
        .merge(e930_hourly(year), on="hour", how="left")
        .merge(asm_mcp(year), on="hour", how="left")
        .merge(asm_cleared(year), on="hour", how="left")
    )
    cls = pd.read_parquet(BUNDLE / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    imp = cls[cls["klass"] == "import"].groupby("hour")["mw"].sum().rename("model_import")
    df = df.merge(imp, on="hour", how="left")
    df["model_import"] = df["model_import"].fillna(0.0)
    df["mon"] = month_of(df["hour"].to_numpy())
    df["gap"] = df["rt"] - df["price"]
    prods = [c for c in ("GENREGMCP", "GENSPINMCP", "GENSUPPMCP") if c in df.columns]
    df["asm_sum"] = df[prods].sum(axis=1) if prods else np.nan
    return df


def summer(df: pd.DataFrame) -> pd.DataFrame:
    return df[(df["hour"] >= SUMMER[0]) & (df["hour"] < SUMMER[1])]


# --------------------------------------------------------------------------
# stages
# --------------------------------------------------------------------------
def stage1_tail(df: pd.DataFrame) -> dict:
    """Model vs actual across the tail, and the model's posture inside it."""
    su = summer(df)
    out: dict = {
        "annual": {
            "model_lw": float((df["price"] * df["demand"]).sum() / df["demand"].sum()),
            "actual_rt_mean": float(df["rt"].mean()),
        },
        "summer": {
            "model_mean": float(su["price"].mean()),
            "actual_rt_mean": float(su["rt"].mean()),
            "mean_err": float((su["price"] - su["rt"]).mean()),
            "lw_gap": float((su["gap"] * su["demand"]).sum() / su["demand"].sum()),
        },
        "tail": {},
    }
    for thr in (100, 200, 500, 1000):
        hit = df[df["rt"] > thr]
        out["tail"][f"rt_gt_{thr}"] = {
            "actual_hours": int(len(hit)),
            "actual_hours_summer": int((su["rt"] > thr).sum()),
            "model_hours_same_thr": int((df["price"] > thr).sum()),
            "model_in_hit_median": float(hit["price"].median()) if len(hit) else None,
            "model_in_hit_max": float(hit["price"].max()) if len(hit) else None,
            "res_dual_gt0_hours": int((hit["dual_max"] > 0).sum()),
            "res_shortfall_hours": int((hit["shortfall_mw"] > 0).sum()),
            "slack_hours": int((hit["slack"] > 0).sum()),
        }
    return out


def stage2_inputs(df: pd.DataFrame) -> dict:
    """Is the miss a LOAD error or a TRADE error? Against EIA-930."""
    def blk(sub: pd.DataFrame) -> dict:
        sub = sub.dropna(subset=["D"])
        return {
            "n": int(len(sub)),
            "model_demand_gw": float(sub["demand"].mean() / 1000),
            "e930_demand_gw": float(sub["D"].mean() / 1000),
            "demand_err_pct": float(((sub["demand"] - sub["D"]) / sub["D"]).mean() * 100),
            # EIA-930 TI is POSITIVE when EXPORTING; model import is positive when
            # importing, so the comparable measure of model error is model + TI.
            "e930_net_import_gw": float(-sub["TI"].mean() / 1000),
            "model_net_import_gw": float(sub["model_import"].mean() / 1000),
            "import_err_gw": float((sub["model_import"] + sub["TI"]).mean() / 1000),
        }

    su = summer(df)
    return {
        "annual": blk(df),
        "summer": blk(su),
        "summer_scarce": blk(su[su["rt"] > SCARCE_RT]),
    }


def stage3_slope(df: pd.DataFrame) -> dict:
    """Summer price-vs-demand decile curve: how flat is the model's stack?"""
    s = summer(df).copy()
    s["bin"] = pd.qcut(s["demand"] / 1000, 10, labels=False, duplicates="drop")
    rows = []
    for b, sub in s.groupby("bin"):
        rows.append({
            "decile": int(b), "n": int(len(sub)),
            "load_gw": float(sub["demand"].mean() / 1000),
            "model": float(sub["price"].mean()),
            "actual": float(sub["rt"].mean()),
            "err": float((sub["price"] - sub["rt"]).mean()),
            "model_p95": float(sub["price"].quantile(0.95)),
            "actual_p95": float(sub["rt"].quantile(0.95)),
        })
    lo = next(r for r in rows if r["decile"] == 5)
    hi = max(rows, key=lambda r: r["decile"])
    dl = hi["load_gw"] - lo["load_gw"]
    m_slope = (hi["model"] - lo["model"]) / dl
    a_slope = (hi["actual"] - lo["actual"]) / dl
    return {
        "deciles": rows,
        "model_slope_usd_per_gw": float(m_slope),
        "actual_slope_usd_per_gw": float(a_slope),
        "flatness_ratio": float(a_slope / m_slope),
    }


def stage4_reserves(df: pd.DataFrame) -> dict:
    """Model reserve posture vs MISO's OWN cleared MW and ancillary MCP."""
    su = summer(df)
    sc = su[su["rt"] > SCARCE_RT]
    prods = [c for c in ("GENREGMCP", "GENSPINMCP", "GENSUPPMCP") if c in df.columns]
    cl = [c for c in ("reg", "spin", "supp", "str") if c in df.columns]

    def blk(sub: pd.DataFrame) -> dict:
        return {
            "n": int(len(sub)),
            "model_req_gw": float(sub["req_mw"].mean() / 1000),
            "model_held_gw": float(sub["held_mw"].mean() / 1000),
            "model_dual_mean": float(sub["dual_max"].mean()),
            "model_dual_max": float(sub["dual_max"].max()),
            "miso_cleared_gw": float(sub["miso_cleared_mw"].mean() / 1000),
            "miso_cleared_by_product_gw": {p: float(sub[p].mean() / 1000) for p in cl},
            "miso_asm_mcp_sum": float(sub["asm_sum"].mean()),
            "miso_asm_by_product": {p: float(sub[p].mean()) for p in prods},
        }

    out = {"summer": blk(su), "summer_scarce": blk(sc)}
    gap = float((sc["rt"] - sc["price"]).mean())
    out["asm_share_of_energy_gap_pct"] = float(100 * sc["asm_sum"].mean() / gap) if gap else None
    out["energy_gap_in_scarce_hours"] = gap
    return out


def stage5_foreseen(df: pd.DataFrame) -> dict:
    """Split the scarcity miss into DA-foreseen (reachable) vs RT-only."""
    su = summer(df)
    sc = su[su["rt"] > SCARCE_RT].copy()
    sc["foreseen"] = sc["da"] > FORESEEN_DA
    total = float((su["gap"] * su["demand"]).sum())
    out: dict = {"summer_hours": int(len(su)), "n_scarce": int(len(sc)),
                 "summer_lw_gap": float(total / su["demand"].sum())}
    for lbl, sub in (("DA_foreseen", sc[sc["foreseen"]]), ("RT_only", sc[~sc["foreseen"]])):
        if not len(sub):
            out[lbl] = {"n": 0}
            continue
        out[lbl] = {
            "n": int(len(sub)),
            "mean_load_gw": float(sub["demand"].mean() / 1000),
            "mean_da": float(sub["da"].mean()),
            "mean_rt": float(sub["rt"].mean()),
            "mean_model": float(sub["price"].mean()),
            "mean_gap": float(sub["gap"].mean()),
            "share_of_summer_gap_pct": float(100 * (sub["gap"] * sub["demand"]).sum() / total),
        }
    return out


# --------------------------------------------------------------------------
def main() -> int:
    out: dict = {"basis": {
        "session": "miso-167",
        "keeper": "2026-08-16-miso-160-wefor-shape",
        "bundle": "results/calibration/miso160_wefor_B",
        "hour_key": "model chronological non-leap 8760 CST calendar",
        "summer": f"Jun-Sep, hours {SUMMER[0]}..{SUMMER[1] - 1}",
        "scarce_rt_threshold": SCARCE_RT,
        "foreseen_da_threshold": FORESEEN_DA,
    }}
    for year in YEARS:
        df = assemble(year)
        out[str(year)] = {
            "tail": stage1_tail(df),
            "inputs": stage2_inputs(df),
            "slope": stage3_slope(df),
            "reserves": stage4_reserves(df),
            "foreseen": stage5_foreseen(df),
        }

    dest = ROOT / "results" / "calibration" / "_miso167_summer_scarcity_instrument.json"
    dest.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {dest.relative_to(ROOT)}\n")

    for year in YEARS:
        y = out[str(year)]
        t, i, s, r, f = y["tail"], y["inputs"], y["slope"], y["reserves"], y["foreseen"]
        print(f"================ {year} ================")
        print(f" summer: model {t['summer']['model_mean']:.2f} vs actual RT {t['summer']['actual_rt_mean']:.2f}"
              f"  (load-wtd gap {t['summer']['lw_gap']:+.2f} $/MWh)")
        print(f" stack slope: model {s['model_slope_usd_per_gw']:.2f} vs actual {s['actual_slope_usd_per_gw']:.2f} $/GW"
              f"  -> {s['flatness_ratio']:.2f}x TOO FLAT")
        print(f" inputs @scarcity: load err {i['summer_scarce']['demand_err_pct']:+.2f}%,"
              f" net-import err {i['summer_scarce']['import_err_gw']:+.2f} GW")
        print(f" reserves @scarcity: model req {r['summer_scarce']['model_req_gw']:.2f} GW vs MISO cleared"
              f" {r['summer_scarce']['miso_cleared_gw']:.2f} GW | model dual {r['summer_scarce']['model_dual_mean']:.2f}"
              f" vs MISO ASM MCP {r['summer_scarce']['miso_asm_mcp_sum']:.2f}"
              f" = {r['asm_share_of_energy_gap_pct']:.1f}% of the ${r['energy_gap_in_scarce_hours']:.2f} energy gap")
        for lbl in ("DA_foreseen", "RT_only"):
            b = f[lbl]
            if not b.get("n"):
                continue
            print(f"   {lbl:11s} n={b['n']:3d} load {b['mean_load_gw']:6.2f} GW | DA {b['mean_da']:7.2f}"
                  f" RT {b['mean_rt']:8.2f} model {b['mean_model']:7.2f} | {b['share_of_summer_gap_pct']:5.1f}% of summer gap")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())

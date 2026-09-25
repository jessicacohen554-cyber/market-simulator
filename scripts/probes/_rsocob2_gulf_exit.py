"""R-SOCO-B2 probe: when did the former Gulf Power plants and load leave SOCO's EIA-930 BA?

Zero LP. Reproduces every number in
``docs/handoffs/r-soco/FINDING-r-soco-b2-boundary-2026-09-25.md`` and writes them to
``docs/handoffs/r-soco/rsocob2_boundary/probe.json``.

Four instruments, each the publisher's own record:

1. **Load side, FERC-714 vs EIA-930.** PUDL ``out_ferc714__hourly_planning_area_demand``
   (the committed route of ``scripts/data/slice_soco_ferc714_pudl.py``) for the five
   SOCO-footprint respondents (Alabama 2, Georgia 183, Mississippi 184, Oglethorpe 107,
   MEAG 210), Gulf Power 185 and FPL 63. ``r_soco = SOCO 930 demand - sum(five)``.
2. **Generation side, hourly CEMS.** CAMPD gross load of the SOCO-coded plants split into
   ``core`` / ``gulf`` / ``aec``; least squares of EIA-930 SOCO fossil net generation on
   the three per period.
3. **Annual reconciliation.** EIA-930 SOCO coal+gas vs the benchmark frame
   (``run_calibration_full._eia923_frame``), with and without the Gulf plants' EIA-923
   generation for their in-BA share of the year.
4. **Rule-outs.** Recodes (current EIA-860 recode set intersected with the SOCO
   universe), CHP share, EIA-930 raw vs Adjusted.

Usage (PUDL parquets are fetched into ``--work`` if absent, ~255 MB)::

    PYTHONPATH=src:scripts uv run python scripts/probes/_rsocob2_gulf_exit.py --work <dir>
"""

from __future__ import annotations

import argparse
import glob
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for _p in (str(ROOT / "src"), str(ROOT / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

PUDL = "https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly"
GULF = [641, 643, 7715, 57502, 55242]
AEC = [53, 55, 56, 533, 6192, 7063, 56522, 64469]
SOCO_RESP = [2, 183, 184, 107, 210]
#: The measured exit instant (hour-beginning UTC) — the first hour Gulf 185 stops
#: filing, the first hour of the FPL 930 step (section 2 of the FINDING).
EXIT_UTC = pd.Timestamp("2022-07-13 11:00")
OUT = ROOT / "docs/handoffs/r-soco/rsocob2_boundary/probe.json"


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.replace(",", ""), errors="coerce")


def load_930() -> pd.DataFrame:
    """EIA-930 BALANCE rows for SOCO / FPL / AEC, numeric, hour-beginning UTC."""
    keep = [
        "Balancing Authority",
        "UTC Time at End of Hour",
        "Local Time at End of Hour",
        "Demand (MW)",
        "Net Generation (MW) from Coal",
        "Net Generation (MW) from Natural Gas",
        "Net Generation (MW) from All Petroleum Products",
        "Net Generation (MW) from Coal (Adjusted)",
        "Net Generation (MW) from Natural Gas (Adjusted)",
    ]
    fs = sorted(glob.glob(str(ROOT / "data/raw/eia-930/EIA930_BALANCE_20*.parquet")))
    d = pd.concat(pd.read_parquet(f, columns=keep) for f in fs)
    d = d[d["Balancing Authority"].isin(["SOCO", "FPL", "AEC"])].copy()
    for c in keep[3:]:
        d[c] = _num(d[c])
    fmt = "%m/%d/%Y %I:%M:%S %p"
    d["u"] = pd.to_datetime(d["UTC Time at End of Hour"], format=fmt) - pd.Timedelta(
        hours=1
    )
    d["t"] = pd.to_datetime(d["Local Time at End of Hour"], format=fmt)
    return d


def load_714(work: Path) -> pd.DataFrame:
    """PUDL FERC-714 hourly demand for the SOCO respondents, Gulf 185 and FPL 63."""
    f = work / "f714.parquet"
    if not f.exists():
        subprocess.run(
            ["curl", "-sS", "-o", str(f), f"{PUDL}/out_ferc714__hourly_planning_area_demand.parquet"],
            check=True,
        )
    ids = SOCO_RESP + [1, 185, 63]
    df = pd.read_parquet(
        f,
        columns=["datetime_utc", "respondent_id_ferc714", "demand_reported_mwh"],
        filters=[("respondent_id_ferc714", "in", ids)],
    )
    return df.pivot_table(
        index="datetime_utc", columns="respondent_id_ferc714", values="demand_reported_mwh"
    )


def load_cems(soco_by_year: dict[int, set[int]]) -> pd.DataFrame:
    """Hourly CAMPD gross load, UTC, grouped core / gulf / aec."""
    rows = []
    for y, soco in soco_by_year.items():
        core = soco - set(GULF) - set(AEC)
        want = core | set(GULF) | set(AEC)
        for st in ("AL", "GA", "MS", "FL"):
            c = pd.read_parquet(
                ROOT / f"data/raw/campd-unit-level/{st}_{y}.parquet",
                columns=["stateCode", "facilityId", "date", "hour", "grossLoad"],
            )
            c["facilityId"] = pd.to_numeric(c["facilityId"], errors="coerce")
            c = c[c["facilityId"].isin(want)]
            # CAMPD hours are local STANDARD time: GA Eastern, AL/MS/FL-panhandle Central.
            off = np.where(c["stateCode"] == "GA", 5, 6)
            c["utc"] = (
                pd.to_datetime(c["date"])
                + pd.to_timedelta(c["hour"], unit="h")
                + pd.to_timedelta(off, unit="h")
            )
            c["grp"] = np.where(
                c["facilityId"].isin(GULF),
                "gulf",
                np.where(c["facilityId"].isin(AEC), "aec", "core"),
            )
            rows.append(c[["utc", "grp", "grossLoad"]])
    c = pd.concat(rows)
    return c.pivot_table(index="utc", columns="grp", values="grossLoad", aggfunc="sum").fillna(0.0)


def main() -> None:
    """Run the four instruments and write the probe JSON."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--work", type=Path, required=True)
    a = ap.parse_args()
    a.work.mkdir(parents=True, exist_ok=True)

    import run_calibration_full as rcf
    from market_sim.data.ba_membership import current_ba_recoded_plants
    from market_sim.data.eia923 import load_monthly_generation
    from market_sim.data.zone_assignment import build_zone_lookup

    out: dict = {"exit_utc_hour_beginning": str(EXIT_UTC)}
    g = load_monthly_generation()
    d = load_930()
    F = load_714(a.work)

    # 1. load side
    E = d.pivot_table(index="u", columns="Balancing Authority", values="Demand (MW)")
    J = E[["SOCO", "FPL"]].join(F, how="inner")
    J["ops"] = J[SOCO_RESP].sum(axis=1, min_count=len(SOCO_RESP))
    J["r_soco"] = J["SOCO"] - J["ops"]
    M = J.resample("MS").mean()
    out["load_monthly_MW"] = {
        str(k.date()): {
            "r_soco": round(float(v["r_soco"]), 0),
            "gulf_185": None if pd.isna(v[185]) else round(float(v[185]), 0),
            "fpl930_minus_714": round(float(v["FPL"] - v[63]), 0),
        }
        for k, v in M.loc["2019":"2023"].iterrows()
    }
    Dd = J.resample("D").mean()
    out["load_daily_r_soco_MW"] = {
        str(k.date()): round(float(v), 0)
        for k, v in Dd.loc["2022-07-06":"2022-07-20", "r_soco"].items()
    }
    out["gulf_185_last_hour_utc"] = str(F[185].dropna().index.max())
    h = J.loc["2022-07-12":"2022-07-14"].copy()
    h["dS"] = h["r_soco"] - h["r_soco"].shift(24)
    h["dF"] = h["FPL"] - h["FPL"].shift(24)
    out["hourly_step_2022_07_13"] = {
        str(k): {"d_r_soco_vs_prior_day": round(float(r.dS), 0), "d_fpl930_vs_prior_day": round(float(r.dF), 0)}
        for k, r in h.loc["2022-07-13 06:00":"2022-07-13 14:00"].iterrows()
    }

    # 2. generation side
    soco_by_year = {
        y: set(g[(g.year == y) & (g.ba_code == "SOCO")].plant_id) for y in range(2019, 2026)
    }
    C = load_cems(soco_by_year)
    x = d[d["Balancing Authority"] == "SOCO"].set_index("u")
    fos = x[
        [
            "Net Generation (MW) from Coal",
            "Net Generation (MW) from Natural Gas",
            "Net Generation (MW) from All Petroleum Products",
        ]
    ].sum(axis=1, min_count=2)
    Z = C.join(fos.rename("f930"), how="inner").dropna()
    periods = {
        "2019": Z.loc["2019"],
        "2020": Z.loc["2020"],
        "2021 Jan-Aug": Z.loc["2021-01":"2021-08"],
        "2021 Sep-Dec": Z.loc["2021-09":"2021-12"],
        "2022 to exit": Z[(Z.index >= "2022") & (Z.index < EXIT_UTC)],
        "2022 after exit": Z[(Z.index >= EXIT_UTC) & (Z.index < "2023")],
        "2023": Z.loc["2023"],
        "2024": Z.loc["2024"],
        "2025": Z.loc["2025"],
    }
    fits = {}
    for name, z in periods.items():
        A = np.c_[z[["core", "gulf", "aec"]].to_numpy(), np.ones(len(z))]
        b, *_ = np.linalg.lstsq(A, z["f930"].to_numpy(), rcond=None)
        r = z["f930"].to_numpy() - A @ b
        fits[name] = {
            "hours": int(len(z)),
            "b_core": round(float(b[0]), 3),
            "b_gulf": round(float(b[1]), 3),
            "b_aec": round(float(b[2]), 3),
            "const_MW": round(float(b[3]), 0),
            "R2": round(float(1 - r.var() / z["f930"].var()), 4),
        }
    out["cems_fit"] = fits
    gz = Z.loc["2022", "gulf"]
    pre = float(gz[gz.index < EXIT_UTC].sum() / gz.sum())
    out["gulf_2022_cems_share_before_exit"] = round(pre, 4)

    # 3. annual reconciliation
    gen = rcf.load_monthly_generation()
    xs = d[d["Balancing Authority"] == "SOCO"]
    recon = {}
    for y in range(2019, 2025):
        xy = xs[xs.t.dt.year == y]
        coal = float(xy["Net Generation (MW) from Coal"].sum()) / 1e6
        gas = float(xy["Net Generation (MW) from Natural Gas"].sum()) / 1e6
        b = rcf._eia923_frame(y, gen, "SOCO")
        fb = b[b["klass"].str.match("^(CC_|CT_|ST_|COAL)")]
        tot = float(fb["annual_mwh"].sum()) / 1e6
        bgas = float(fb[~fb["klass"].str.startswith("COAL")]["annual_mwh"].sum()) / 1e6
        gulf = float(g[(g.year == y) & g.plant_id.isin(GULF)].netgen_annual_mwh.sum()) / 1e6
        share = 1.0 if y <= 2021 else pre if y == 2022 else 0.0
        gin = gulf * share
        recon[str(y)] = {
            "930_coal_gas_TWh": round(coal + gas, 3),
            "930_gas_TWh": round(gas, 3),
            "bench_fossil_TWh": round(tot, 3),
            "bench_gas_TWh": round(bgas, 3),
            "gulf_923_TWh": round(gulf, 3),
            "gulf_in_BA_TWh": round(gin, 3),
            "ratio_as_bench": round((coal + gas) / tot, 4),
            "ratio_with_gulf_in_BA": round((coal + gas) / (tot + gin), 4),
            "930_gas_minus_923_gas_as_bench": round(gas - bgas, 3),
            "930_gas_minus_923_gas_with_gulf": round(gas - bgas - gin, 3),
        }
    out["annual_reconciliation"] = recon

    # 4. rule-outs
    universe = set(build_zone_lookup("SOCO")) | set().union(*soco_by_year.values())
    out["recoded_in_soco_universe"] = sorted(current_ba_recoded_plants("SOCO") & universe)
    chp = g[(g.year.between(2019, 2024)) & (g.ba_code == "SOCO") & g.fuel_type.isin(["NG", "BIT", "SUB"])]
    out["soco_chp_Y_TWh"] = {
        str(k): round(float(v) / 1e6, 2)
        for k, v in chp[chp.chp.astype(str).str.upper().str.startswith("Y")].groupby("year").netgen_annual_mwh.sum().items()
    }
    adj = {}
    for y in range(2019, 2025):
        xy = xs[xs.t.dt.year == y]
        adj[str(y)] = round(
            float(
                xy["Net Generation (MW) from Coal (Adjusted)"].sum()
                + xy["Net Generation (MW) from Natural Gas (Adjusted)"].sum()
                - xy["Net Generation (MW) from Coal"].sum()
                - xy["Net Generation (MW) from Natural Gas"].sum()
            )
            / 1e6,
            3,
        )
    out["930_adjusted_minus_raw_fossil_TWh"] = adj

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("cems_fit", "annual_reconciliation", "gulf_185_last_hour_utc", "gulf_2022_cems_share_before_exit")}, indent=1))


if __name__ == "__main__":
    main()

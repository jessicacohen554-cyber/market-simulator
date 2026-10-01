"""SPP-96 phase 0 (zero LP): is SPP reserve co-optimisation (queue item SPP-56, M2) non-inert?

PRECOMMIT: docs/records/spp/PRECOMMIT-spp-96-reserve-coopt-2026-09-28.md (tests T1/T2, rule §4).

T1 — market side: hourly RTBM reserve MCPs (zone-mean of the 5-minute posts) against the
     actual RT LMP benchmark the scorer reads.
T2 — model side: the keeper's reserve-eligible headroom (sum pmax x availability over
     ``_reserve_eligible`` minus the P1 dispatch of the eligible classes), rebuilt per year with
     ``run_year(fleet_only=True)`` (no LP, the SPP-55 construction), against SPP's MEASURED
     cleared up-reserve MW (regup + spin + supp + rampup + uncup where posted).

Usage: uv run python scripts/probes/_spp96_reserve_coopt_phase0.py
Writes docs/records/spp/spp96/phase0.json and docs/records/spp/spp96/headroom_<year>.parquet.
"""

import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
from scripts.replay_keeper import derived_run_year_inputs, run_year_kwargs  # noqa: E402
from scripts.run_calibration import run_year  # noqa: E402
from market_sim.model.reserves.spec import _reserve_eligible  # noqa: E402

BUNDLE = REPO / "results/calibration/spp94_arm_span"
OUT = REPO / "docs/records/spp/spp96"
YEARS = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
# class_hourly classes whose members are RESERVE_FUEL_TYPES — the set _reserve_eligible
# admits (same list as docs/records/spp/spp55/headroom.py).
ELIGIBLE_CLASSES = (
    "CC_CHP", "CC_REGULAR", "COAL_LIGNITE", "COAL_PRB", "CT_CHP",
    "CT_PEAKER", "ST_GAS", "ST_CHP", "nuclear", "oil",
)
UP_PRODUCTS = ("regup", "spin", "supp", "rampup", "uncup")
BIND_BAR_HOURS = 88  # PRECOMMIT §4 (a): 1 % of hours
SHARE_BAR = 0.05  # PRECOMMIT §4 (b)


def hourly_mcp(year: int) -> pd.DataFrame:
    """Zone-mean, hour-mean RTBM MCPs on the model clock (CST hour-beginning, no Feb 29)."""
    z = zipfile.ZipFile(REPO / f"data/raw/spp-or-mcp/RTBM_MCP_{year}.csv.zip")
    d = pd.read_csv(z.open(z.namelist()[0]))
    # 2022's file is upper-case with a different date format; normalise both.
    d.columns = [c.strip().upper() for c in d.columns]
    d = d.rename(columns={"REGUPSERVICE": "RegUPService", "REGDNSERVICE": "RegDNService", "SPIN": "Spin", "SUPP": "Supp"})
    t = pd.to_datetime(d["GMTINTERVALEND"], format="mixed")
    t = t - pd.Timedelta(minutes=5) - pd.Timedelta(hours=6)
    keep = (t.dt.year == year) & ~((t.dt.month == 2) & (t.dt.day == 29))
    d, t = d[keep], t[keep]
    doy = t.dt.dayofyear.values
    if pd.Timestamp(year=year, month=12, day=31).dayofyear == 366:
        doy = np.where(doy > 60, doy - 1, doy)
    d = d.assign(hour=(doy - 1) * 24 + t.dt.hour.values)
    cols = ["RegUPService", "RegDNService", "Spin", "Supp"]
    return d.groupby("hour")[cols].mean().reindex(range(8760))


def main() -> None:
    """Run T1 and T2 for every keeper year and write the phase-0 record."""
    OUT.mkdir(parents=True, exist_ok=True)
    meta = json.loads((BUNDLE / "meta.json").read_text())
    kw = run_year_kwargs(meta)
    lmp = pd.read_parquet(REPO / "data/raw/_validation-source/actual_lmp_hourly_SPP.parquet")
    orc = pd.read_parquet(REPO / "data/raw/_validation-source/spp_rtbm_or_cleared_hourly.parquet")
    rows = []
    for year in YEARS:
        # --- T1
        mcp = hourly_mcp(year)
        rt = lmp[lmp.year == year].set_index("hour")["rt"].reindex(range(8760))
        # --- T2
        kw_y = dict(kw)
        kw_y.update(derived_run_year_inputs(BUNDLE, year))
        r = run_year(year, "SPP", 8760, float(meta["gas_prices"][str(year)]), {}, fleet_only=True, **kw_y)
        fa = r["fleet_arrays"]
        elig = _reserve_eligible(fa)
        cap_t = (fa.pmax[:, None] * fa.availability)[elig].sum(axis=0)
        ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
        ch = ch[ch["pass"] == "P1"]
        piv = ch.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum", observed=True)
        piv = piv.reindex(range(8760)).fillna(0.0)
        disp_t = piv[[c for c in ELIGIBLE_CLASSES if c in piv.columns]].sum(axis=1).values
        head = cap_t - disp_t
        o = orc[orc.year == year].set_index("hour").reindex(range(8760))
        req = o[list(UP_PRODUCTS)].fillna(0.0).sum(axis=1).values
        has_req = o["regup"].notna().values
        short = (head < req) & has_req
        pd.DataFrame(
            {"hour": range(8760), "cap_elig": cap_t, "disp_elig": disp_t, "headroom": head, "req_cleared_up": req}
        ).to_parquet(OUT / f"headroom_{year}.parquet")
        rows.append(
            {
                "year": year,
                "t1_rt_lmp_mean": round(float(rt.mean()), 3),
                "t1_mcp_mean": {c: round(float(mcp[c].mean()), 3) for c in mcp.columns},
                "t1_spin_share_of_lmp": round(float(mcp["Spin"].mean() / rt.mean()), 4),
                "t1_regup_share_of_lmp": round(float(mcp["RegUPService"].mean() / rt.mean()), 4),
                "t2_req_median_mw": round(float(np.median(req[has_req]))),
                "t2_req_max_mw": round(float(req[has_req].max())),
                "t2_headroom_min_mw": round(float(head.min())),
                "t2_headroom_p1_mw": round(float(np.percentile(head, 1))),
                "t2_headroom_median_mw": round(float(np.median(head))),
                "t2_headroom_over_req_median": round(float(np.median(head[has_req] / req[has_req])), 2),
                "t2_bind_hours": int(short.sum()),
                "t2_bind_hour_list": [int(i) for i in np.flatnonzero(short)],
                "t2_max_shortfall_mw": round(float((req - head)[has_req].max()), 1),
                "req_hours_covered": int(has_req.sum()),
            }
        )
        print(json.dumps({k: v for k, v in rows[-1].items() if k != "t2_bind_hour_list"}), flush=True)
    fail_years = (2019, 2020, 2021, 2022)
    earns = any(
        r["t2_bind_hours"] >= BIND_BAR_HOURS and r["t1_spin_share_of_lmp"] >= SHARE_BAR
        for r in rows
        if r["year"] in fail_years
    )
    rec = {"bundle": BUNDLE.name, "years": rows, "earns_solve": earns,
           "verdict": "NON-INERT: design charter to owner" if earns else "INERT: no solve"}
    (OUT / "phase0.json").write_text(json.dumps(rec, indent=1))
    print("VERDICT:", rec["verdict"])


if __name__ == "__main__":
    main()

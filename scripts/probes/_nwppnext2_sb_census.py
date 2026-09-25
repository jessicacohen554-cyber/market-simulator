"""NWPP-NEXT-2 probe: EIA-860 standby (SB) / out-of-service (OS, OA) census (zero LP).

Question: how much capacity and how much benchmarked EIA-923 generation sits on
generators the fleet drops through its ``status == "OP"`` filter
(``market_sim/data/fleet/eia860.py``), per year 2019-2025, for NWPP and briefly
for every other region.

Membership mirrors the two seams the run reads:
* fleet   -- EIA-860 ``balancing_authority_code`` in ``ba_codes(iso)``;
* bench   -- ``run_calibration_full._iso_plant_ids(iso, year)`` over the
             national EIA-923 frame (``_eia923_frame``).
Vintage per year Y is ``vintage_<Y>/`` (``eia860_vintage_tracks_solve_year``);
2025 reads the top-level 2025 Early Release snapshot.

Read-only. Output: CSVs + a printed summary under the scratch dir given by
``--out`` (default ``/tmp``).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_calibration_full as rcf  # noqa: E402
from market_sim.data.fleet.models import ba_codes  # noqa: E402
from market_sim.data.eia923 import load_monthly_generation  # noqa: E402

YEARS = range(2019, 2026)
ISOS = ("NWPP", "ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SPP", "SOCO")
COAL = {"BIT", "SUB", "LIG", "RC", "WC", "SC", "SGC"}
GAS = {"NG", "OG", "BFG", "PG", "SGP"}
OIL = {"DFO", "RFO", "JF", "KER", "WO", "PC"}
MATERIAL_MWH = 10_000.0  # 10 GWh/yr: reporting threshold only, never a model input


def vintage_path(year: int) -> Path:
    """Return the EIA-860 generator parquet the fleet reads for ``year``."""
    base = ROOT / "data/raw/eia-860"
    p = base / f"vintage_{year}" / "eia860_generators.parquet"
    return p if p.exists() else base / "eia860_generators.parquet"


def model_class(pm: str, es: str) -> str:
    """Coarse model class from EIA-860 prime mover + energy source."""
    pm, es = str(pm).strip().upper(), str(es).strip().upper()
    if es in COAL:
        return "coal"
    if pm in {"CT", "CA", "CS"}:
        return "CC"
    if pm in {"GT", "IC"}:
        return "CT_PEAKER" if es in GAS else ("CT_oil" if es in OIL else "other")
    if pm == "ST" and es in GAS:
        return "ST_GAS"
    return "other"


def campd_gross(year: int, states: set[str]) -> pd.Series:
    """CAMPD annual gross load (MWh) per facilityId over ``states``."""
    out = []
    for st in sorted(states):
        f = ROOT / f"data/raw/campd-unit-level/{st}_{year}.parquet"
        if f.exists():
            d = pd.read_parquet(f, columns=["facilityId", "grossLoad"])
            d["facilityId"] = pd.to_numeric(d["facilityId"], errors="coerce").astype(
                "Int64"
            )
            out.append(d.groupby("facilityId")["grossLoad"].sum())
    if not out:
        return pd.Series(dtype=float)
    return pd.concat(out).groupby(level=0).sum()


def census(iso: str, gen923: pd.DataFrame, with_campd: bool) -> pd.DataFrame:
    """Per (year, plant) rows for every non-OP (SB/OS/OA) generator in ``iso``."""
    codes = set(ba_codes(iso))
    rows = []
    for y in YEARS:
        v = pd.read_parquet(vintage_path(y))
        v = v[v["balancing_authority_code"].astype(str).str.strip().isin(codes)].copy()
        v["status"] = v["status"].astype(str).str.strip().str.upper()
        v["mw"] = pd.to_numeric(v["nameplate_capacity_mw"], errors="coerce")
        v["cls"] = [
            model_class(p, e) for p, e in zip(v["prime_mover"], v["energy_source"])
        ]
        op_plants = set(v.loc[v["status"] == "OP", "plant_id"].astype(int))
        bench_members = rcf._iso_plant_ids(iso, y)
        e = rcf._eia923_frame(y, gen923, iso)
        e923 = e.groupby("plant_id")["annual_mwh"].sum()
        eklass = e.groupby("plant_id").apply(
            lambda d: "/".join(
                f"{k}:{m / 1e3:.0f}"
                for k, m in zip(d["klass"], d["annual_mwh"])
                if abs(m) > 500
            )
        )
        raw = gen923[gen923["year"] == y].groupby("plant_id")["netgen_annual_mwh"].sum()
        nonop = v[v["status"].isin(["SB", "OS", "OA"])]
        cg = campd_gross(y, set(nonop["state"].astype(str))) if with_campd else None
        for (pid, st), g in nonop.groupby([nonop["plant_id"].astype(int), "status"]):
            rows.append(
                dict(
                    iso=iso,
                    year=y,
                    plant_id=pid,
                    plant=str(g["plant_name"].iloc[0]),
                    ba=str(g["balancing_authority_code"].iloc[0]),
                    status=st,
                    n_gen=len(g),
                    mw=float(g["mw"].sum()),
                    cls="/".join(sorted(set(g["cls"]))),
                    pm="/".join(sorted(set(g["prime_mover"].astype(str)))),
                    partial_op=pid in op_plants,
                    plant_op_mw=float(
                        v.loc[
                            (v["plant_id"].astype(int) == pid) & (v["status"] == "OP"),
                            "mw",
                        ].sum()
                    ),
                    in_bench=pid in bench_members,
                    e923_mwh=float(e923.get(pid, 0.0)),
                    e923_klass_gwh=str(eklass.get(pid, "")),
                    e923_raw_mwh=float(raw.get(pid, 0.0)),
                    campd_gross_mwh=(
                        float(cg.get(pid, np.nan)) if cg is not None else np.nan
                    ),
                )
            )
    return pd.DataFrame(rows)


def main() -> None:
    """Run the census and write CSVs + printed tables."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="/tmp")
    args = ap.parse_args()
    out = Path(args.out)
    gen = load_monthly_generation()
    frames = []
    for iso in ISOS:
        df = census(iso, gen, with_campd=(iso == "NWPP"))
        frames.append(df)
        print(iso, len(df), flush=True)
    allf = pd.concat(frames, ignore_index=True)
    allf.to_csv(out / "sb_census_all.csv", index=False)
    pd.set_option(
        "display.width", 250, "display.max_rows", 400, "display.max_columns", 40
    )
    n = allf[allf.iso == "NWPP"]
    print(n.sort_values(["status", "plant_id", "year"]).to_string())
    only = allf[~allf.partial_op]
    only = only.assign(mat=only.e923_mwh >= MATERIAL_MWH)
    piv = only[only.status == "SB"].pivot_table(
        index=["iso", "cls"],
        columns="year",
        values=["mw", "e923_mwh"],
        aggfunc="sum",
        fill_value=0,
    )
    print(piv.round(0).to_string())
    mat = only[(only.status == "SB") & only.mat].pivot_table(
        index="iso",
        columns="year",
        values=["mw", "e923_mwh"],
        aggfunc="sum",
        fill_value=0,
    )
    print(mat.round(0).to_string())
    print(
        "in_bench share of SB-only e923:",
        only[only.status == "SB"]
        .groupby("iso")
        .apply(lambda d: d.loc[d.in_bench, "e923_mwh"].sum() / max(d.e923_mwh.sum(), 1))
        .round(3)
        .to_dict(),
    )


if __name__ == "__main__":
    main()

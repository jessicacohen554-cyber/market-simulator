#!/usr/bin/env python3
"""NYISO-NEXT-7 phase 0 (ZERO LP): does the single external star node leak import?

Measures, from committed artifacts only:

1. The MEASURED neighbour composition of each NYISO border link: NYISO's own
   P-32 ``SCH -`` rows attributed to model zones (``SEAM_ROW_ZONE`` plus the
   PAR split of ``SCH - PJ - NY``), reported per neighbour (HQ / IESO / PJM / NE).
2. The MODEL side: the keeper's aggregate ``import`` class (the only import
   quantity the committed sidecars carry) against the NEXT-3 control, set
   against the NEXT-6 Long Island cut (``_nyisonext6_g1_footprint.json``). The
   share of the cut that did NOT leave total import is the volume re-routed
   through the other border links of the one external node.
3. Link congestion status per zone from the committed prices: a link is at a
   bound in an hour iff its zone's price differs from ``NYISO_external``'s.
4. The identification test for a per-neighbour ladder: the frozen
   ``derive_nyiso_import_tranches`` formula is a monotone Q-Q coupling of flow
   against the NY DA price. It is admissible per neighbour only if each
   neighbour's own flow co-moves with that price. Spearman rank correlation of
   hourly per-neighbour net import against the NY DA zonal-mean LBMP, beside
   the aggregate the ladder is actually derived on.
5. Side-check: ``SCH - HQ_IMPORT_EXPORT`` is an accounting duplicate of
   ``SCH - HQ - NY`` (``nyiso_par_attribution.ACCOUNTING_DUPLICATE``) but is
   listed in the ladder derivation's ``EXTERNAL_SEAMS["HQ"]``. Measure what it
   adds to the derivation's net import.

Usage:
    python scripts/probes/nyisonext7_star_node_phase0.py --ctrl-dir <dir>

``--ctrl-dir`` holds the NEXT-3 control's ``class_hourly_<y>.parquet`` and
``system_<y>.parquet``, extracted from git (``8227c1f3^``).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.data.nyiso_par_attribution import (  # noqa: E402
    ACCOUNTING_DUPLICATE,
    PJM_AC_ROW,
    SEAM_ROW_ZONE,
    attributed_envelope_by_zone,
    attributed_zone_net,
)
from market_sim.data.nyiso_seam_envelope import (  # noqa: E402
    NYISO_SEAM_TIE_LANDING,
    posted_import_limit_hourly,
)

YEARS = (2021, 2022, 2023, 2024, 2025)
CALIB = REPO / "results" / "calibration"
FLOW_DIR = REPO / "data" / "raw" / "NYISO" / "interface-flows"
DA = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_NYISO.parquet"

NEIGHBOUR_OF_ROW = {
    "SCH - OH - NY": "IESO",
    "SCH - HQ - NY": "HQ",
    "SCH - HQ_CEDARS": "HQ",
    "SCH - NE - NY": "NE",
    "SCH - NPX_CSC": "NE",
    "SCH - NPX_1385": "NE",
    "SCH - PJM_HTP": "PJM",
    "SCH - PJM_VFT": "PJM",
    "SCH - PJM_NEPTUNE": "PJM",
    PJM_AC_ROW: "PJM",
}


def _flows(year: int) -> pd.DataFrame:
    df = pd.read_csv(FLOW_DIR / f"NYISO_interface_flows_hourly_{year}.csv.gz")
    return df[df["interface"].astype(str).str.startswith("SCH -")].copy()


def _hoy_series(df: pd.DataFrame, rows: list[str]) -> np.ndarray:
    sub = df[df["interface"].isin(rows)].copy()
    t = pd.to_datetime(sub["interval_start_local"])
    sub["hoy"] = (t.dt.dayofyear - 1) * 24 + t.dt.hour
    piv = sub.pivot_table(
        index="hoy", columns="interface", values="flow_mw", aggfunc="mean"
    )
    return piv.sum(axis=1).reindex(range(8760)).to_numpy(dtype=float)


def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = ~np.isnan(a) & ~np.isnan(b)
    return float(pd.Series(a[m]).rank().corr(pd.Series(b[m]).rank()))


def measured_block(year: int) -> dict:
    """Per-link neighbour composition and the per-neighbour identification test."""
    df = _flows(year)
    out: dict = {}

    # (1) link x neighbour, mean MW (PJM AC split by the PAR shares).
    att = attributed_zone_net(df, year)
    link_total = att.groupby("zone")["flow_mw"].mean()
    comp: dict[str, dict[str, float]] = {}
    single = df[df["interface"].isin(SEAM_ROW_ZONE)].copy()
    single["zone"] = single["interface"].map(SEAM_ROW_ZONE)
    single["nb"] = single["interface"].map(NEIGHBOUR_OF_ROW)
    t = pd.to_datetime(single["interval_start_local"]).dt.floor("h")
    single["h"] = t
    n_hours = att["local_hour"].nunique()
    per = single.groupby(["zone", "nb"])["flow_mw"].sum() / n_hours
    for (z, nb), v in per.items():
        comp.setdefault(z, {})[nb] = round(float(v), 1)
    for z in link_total.index:
        pjm_ac = float(link_total[z]) - sum(comp.get(z, {}).values())
        comp.setdefault(z, {})
        comp[z]["PJM_AC(PAR)"] = round(pjm_ac, 1)
        comp[z]["total"] = round(float(link_total[z]), 1)
    out["link_composition_mean_mw"] = comp

    # (4) per-neighbour co-movement with the NY DA price.
    lmp = pd.read_parquet(DA)
    da = (
        lmp[lmp["year"] == year]
        .set_index("hour")["da"]
        .reindex(range(8760))
        .to_numpy(float)
    )
    groups = {
        "HQ": ["SCH - HQ - NY", "SCH - HQ_CEDARS"],
        "IESO": ["SCH - OH - NY"],
        "PJM_AC": [PJM_AC_ROW],
        "PJM_DC": ["SCH - PJM_HTP", "SCH - PJM_VFT", "SCH - PJM_NEPTUNE"],
        "NE_AC": ["SCH - NE - NY"],
        "NE_DC": ["SCH - NPX_CSC", "SCH - NPX_1385"],
    }
    series = {k: _hoy_series(df, v) for k, v in groups.items()}
    agg = sum(series.values())
    out["spearman_vs_ny_da"] = {
        k: round(_spearman(v, da), 3) for k, v in series.items()
    }
    out["spearman_vs_ny_da"]["AGGREGATE"] = round(_spearman(agg, da), 3)
    out["mean_mw"] = {k: round(float(np.nanmean(v)), 1) for k, v in series.items()}
    out["mean_mw"]["AGGREGATE"] = round(float(np.nanmean(agg)), 1)

    # (5) accounting duplicate inside the ladder derivation's HQ list.
    dup = _hoy_series(df, [ACCOUNTING_DUPLICATE])
    out["hq_dup_mean_mw"] = round(float(np.nanmean(dup)), 1)
    out["hq_dup_share_of_derivation_net"] = round(
        float(np.nanmean(dup) / (np.nanmean(agg) + np.nanmean(dup))), 3
    )
    return out


def model_block(year: int, ctrl_dir: Path, cut: dict) -> dict:
    """Aggregate import re-route share and link congestion status."""
    arm_root = (
        CALIB / ("nyisonext6_2021" if year == 2021 else "nyisonext6_span") / "hourly"
    )
    ca = pd.read_parquet(arm_root / f"class_hourly_{year}.parquet")
    cc = pd.read_parquet(ctrl_dir / f"class_hourly_{year}.parquet")
    imp_a = ca[ca["klass"] == "import"]["mw"].to_numpy(float)
    imp_c = cc[cc["klass"] == "import"]["mw"].to_numpy(float)
    d_twh = (imp_a.sum() - imp_c.sum()) / 1e6
    cut_twh = float(cut[str(year)]["cut_twh"])
    rerouted = cut_twh + d_twh  # import fell by -d_twh; the rest moved links

    sa = pd.read_parquet(arm_root / f"system_{year}.parquet")
    sc = pd.read_parquet(ctrl_dir / f"system_{year}.parquet")
    pa = sa.pivot(index="hour", columns="zone", values="price")
    pc = sc.pivot(index="hour", columns="zone", values="price")
    ext_a = pa["NYISO_external"]
    congested = {
        z: round(float(((pa[z] - ext_a).abs() > 0.01).mean()), 3)
        for z in ("Upstate_West", "Capital_Hudson", "NYC", "Long_Island")
    }
    dem = sa.pivot(index="hour", columns="zone", values="demand")
    d_uw = pa["Upstate_West"] - pc["Upstate_West"]
    return {
        "import_twh_ctrl": round(imp_c.sum() / 1e6, 3),
        "import_twh_arm": round(imp_a.sum() / 1e6, 3),
        "import_delta_twh": round(d_twh, 4),
        "li_cut_twh": cut_twh,
        "rerouted_twh": round(rerouted, 4),
        "rerouted_share": round(rerouted / cut_twh, 3) if cut_twh else None,
        "link_at_bound_share_arm": congested,
        "uw_price_delta_lw": round(
            float((d_uw * dem["Upstate_West"]).sum() / dem["Upstate_West"].sum()), 3
        ),
        "uw_hours_price_fell": int((d_uw < -0.01).sum()),
        "ext_price_delta_mean": round(float((ext_a - pc["NYISO_external"]).mean()), 3),
    }


def _model_hour_series(att: pd.DataFrame, zone: str) -> np.ndarray:
    """Measured attributed net for one zone on the model's non-leap clock."""
    sub = att[att["zone"] == zone]
    t = sub["local_hour"]
    keep = ~((t.dt.month == 2) & (t.dt.day == 29))
    sub, t = sub[keep], t[keep]
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    idx = pd.MultiIndex.from_arrays([t.dt.month, t.dt.day, t.dt.hour])
    ser = pd.Series(sub["flow_mw"].to_numpy(float), index=idx)
    ser = ser.groupby(level=[0, 1, 2]).mean()
    clock = pd.MultiIndex.from_arrays([cal.month, cal.day, cal.hour])
    return ser.reindex(clock).to_numpy(float)


def reconstruct_block(year: int) -> dict:
    """Rebuild every at-bound border-link flow from prices + the keeper's caps.

    A border link with its zone price above ``NYISO_external``'s is at its import
    cap, below it at its export cap; equal means interior (unknown). Caps are the
    keeper's own: the PAR-attributed p90 envelope, Long Island's import side
    clipped at the posted tie limits (NEXT-6).
    """
    df = _flows(year)
    caps = attributed_envelope_by_zone(df, year, 8760, 90.0)
    li_post = posted_import_limit_hourly(
        df, NYISO_SEAM_TIE_LANDING["Long_Island"], 8760
    )
    imp, exp = caps["Long_Island"]
    caps["Long_Island"] = (np.minimum(imp, li_post), exp)
    root = CALIB / ("nyisonext6_2021" if year == 2021 else "nyisonext6_span") / "hourly"
    sa = pd.read_parquet(root / f"system_{year}.parquet")
    pa = sa.pivot(index="hour", columns="zone", values="price").sort_index()
    ext = pa["NYISO_external"].to_numpy(float)
    att = attributed_zone_net(df, year)
    ca = pd.read_parquet(root / f"class_hourly_{year}.parquet")
    total = ca[ca["klass"] == "import"].sort_values("hour")["mw"].to_numpy(float)
    out: dict = {}
    flows = {}
    for z in ("Upstate_West", "Capital_Hudson", "NYC", "Long_Island"):
        pz = pa[z].to_numpy(float)
        ic, ec = caps[z]
        f = np.full(8760, np.nan)
        f[pz > ext + 0.01] = ic[pz > ext + 0.01]
        f[pz < ext - 0.01] = -ec[pz < ext - 0.01]
        flows[z] = f
        meas = _model_hour_series(att, z)
        m = ~np.isnan(f) & ~np.isnan(meas)
        out[z] = {
            "at_bound_share": round(float((~np.isnan(f)).mean()), 3),
            "model_mw_at_bound": round(float(f[m].mean()), 1),
            "measured_mw_same_hours": round(float(meas[m].mean()), 1),
            "excess_twh": round(float((f[m] - meas[m]).sum() / 1e6), 3),
        }
    ds = flows["Capital_Hudson"] + flows["NYC"] + flows["Long_Island"]
    m = ~np.isnan(ds)
    uw_meas = _model_hour_series(att, "Upstate_West")
    mm = m & ~np.isnan(uw_meas)
    # Upper bound on the model's Upstate_West import: node supply minus the
    # three at-bound links (export sinks, <= 600 MW, would only lower it).
    uw_ub = total - ds
    out["upstate_west_implied_ub"] = {
        "hours_all_three_at_bound": int(m.sum()),
        "model_ub_mw": round(float(uw_ub[mm].mean()), 1),
        "measured_mw": round(float(uw_meas[mm].mean()), 1),
        "excess_ub_twh": round(float((uw_ub[mm] - uw_meas[mm]).sum() / 1e6), 3),
    }
    return out


def main() -> None:
    """Run the phase-0 measurement and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ctrl-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=CALIB / "_nyisonext7_phase0.json")
    args = ap.parse_args()
    cut = json.loads((CALIB / "_nyisonext6_g1_footprint.json").read_text())
    rec = {
        str(y): {
            "measured": measured_block(y),
            "model": model_block(y, args.ctrl_dir, cut),
            "reconstruct": reconstruct_block(y),
        }
        for y in YEARS
    }
    args.out.write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec, indent=1))


if __name__ == "__main__":
    main()

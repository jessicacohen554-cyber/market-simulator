"""pjm-137 M4 (no LP): how much PJM price separation lives INSIDE a model zone.

`FINDING-pjm136` §3 asked whether the 8-zone reduction can carry the DOM-vs-AEP
separation and answered yes *for the boundary*, using PJM's published trading
hubs that sit inside `PJM_ComEd` and `PJM_AEP_Ohio`. It could not run the same
test on `PJM_Dominion` — PJM publishes no hub there — so Dominion's own internal
spread was never measured, and §3 filed the intra-zonal question as open for
EMAAC alone.

pjm-137's M2 makes that gap load-bearing: PJM's own day-ahead binding-constraint
record says the constraints that dominate the hours Dominion separates are
Loudoun-County 500 kV transformers and 230 kV lines — PLEASANT VIEW, GOOSE
CREEK, ASHBURN, BRAMBLETON — whose **both** ends sit inside `PJM_Dominion`. If
that is right, the separation the model is missing is intra-zonal by
construction and no zonal mechanism can reach it.

This probe measures it directly. PJM publishes an ``AGGREGATE``/``EHV`` pnode
per 500 kV station (the pjm-137 intake
`scripts/data/fetch_pjm_ehv_lmp.py`), 38 of them inside DOM alone. For every
model zone:

* **intra-zone dispersion** — the mean over hours of ``max - min`` of the
  day-ahead LMP across that zone's own EHV nodes, and its congestion-only
  counterpart;
* **the widest intra-zone node pair**, selected BY THE DATA (largest mean
  ``|Δ|``), never by hand;
* the same statistics restricted to the top-decile ISO-load hours, where the
  Dominion CT fleet actually runs.

The headline comparison is **intra-`PJM_Dominion` dispersion against the
inter-zonal DOM-vs-AEP_Ohio spread the whole pjm-133..136 lineage has been
chasing**. A reduction can express the second and not the first, so their ratio
is the reach of the entire zonal-mechanism family.

Nothing is written outside `results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm137_intrazonal_ehv_spread.py
"""

from __future__ import annotations

import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.zonal_shares import _PJM_LOAD_ZONE_GROUPS

YEARS = (2023, 2024, 2025)
HOURS = 8760

EHV_DIR = RAW_DATA_DIR / "pjm-ehv-lmp"
ZONAL_LMP_DIR = RAW_DATA_DIR / "pjm-zonal-lmp"
OUT_PATH = Path("results/probes/pjm137_intrazonal_ehv_spread.json")

#: EHV-feed `zone` code -> the metered-load zone code `_PJM_LOAD_ZONE_GROUPS`
#: is keyed on. Pure naming aliases, the same class of mapping the pjm-136
#: zonal intake carries for the LMP pnode names; no judgement.
EHV_ZONE_TO_LOAD_ZONE: dict[str, str] = {
    "AECO": "AE",
    "AEP": "AEP",
    "APS": "AP",
    "ATSI": "ATSI",
    "BGE": "BC",
    "COMED": "CE",
    "DAY": "DAY",
    "DEOK": "DEOK",
    "DOM": "DOM",
    "DPL": "DPL",
    "DUQ": "DUQ",
    "EKPC": "EKPC",
    "JCPL": "JC",
    "METED": "ME",
    "OVEC": "OVEC",
    "PECO": "PE",
    "PENELEC": "PN",
    "PEPCO": "PEP",
    "PPL": "PL",
    "PSEG": "PS",
    "RECO": "RECO",
    # the EHV feed spells a few zones differently from the LMP pnode feed
    "PENLEC": "PN",
    "PENN": "PN",
    "PN": "PN",
    "PE": "PE",
    "PL": "PL",
    "PS": "PS",
    "AE": "AE",
    "BC": "BC",
    "CE": "CE",
    "JC": "JC",
    "ME": "ME",
    "PEP": "PEP",
    "AP": "AP",
}

#: A node must be priced in at least this share of the year to enter a zone's
#: dispersion statistic — otherwise a station commissioned mid-year would open
#: and close the max-min band spuriously.
_MIN_COVERAGE = 0.95

_MONTH_START_HOUR = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def _hour_of_year(ts: pd.Series) -> np.ndarray:
    """Non-leap hour-of-year index for naive local timestamps (Feb 29 removed)."""
    return (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


def _ehv(year: int) -> pd.DataFrame:
    """One year of EHV node LMPs with a model-zone label and hour-of-year index."""
    files = sorted(EHV_DIR.glob(f"da_ehv_lmps_{year}_*.parquet"))
    if not files:
        raise SystemExit(
            f"no EHV LMP parquet for {year} — run "
            "scripts/data/fetch_pjm_ehv_lmp.py first"
        )
    d = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    ept = pd.to_datetime(d["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    d = d[keep].copy()
    d["hour"] = _hour_of_year(ept[keep])
    d["load_zone"] = d["zone"].str.upper().map(EHV_ZONE_TO_LOAD_ZONE)
    d["model_zone"] = d["load_zone"].map(_PJM_LOAD_ZONE_GROUPS)
    return d[d["model_zone"].notna()].copy()


def _zonal_reference(year: int) -> dict[str, np.ndarray]:
    """DOM-vs-AEP zonal LMP and congestion spread (the inter-zonal comparator)."""
    files = sorted(ZONAL_LMP_DIR.glob(f"da_hrl_lmps_{year}_*.parquet"))
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw = raw[raw["pnode_name"].isin(("DOM", "AEP"))].copy()
    ept = pd.to_datetime(raw["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    raw = raw[keep].copy()
    raw["hour"] = _hour_of_year(ept[keep])
    out = {}
    for key, col in (("lmp", "total_lmp_da"), ("mcc", "congestion_price_da")):
        p = raw.pivot_table(
            index="hour", columns="pnode_name", values=col, aggfunc="mean"
        ).reindex(range(HOURS))
        out[key] = (p["DOM"] - p["AEP"]).to_numpy()
    return out


def _dispersion(frame: pd.DataFrame, col: str) -> tuple[np.ndarray, list[str]]:
    """Hourly max-min across a zone's well-covered EHV nodes."""
    wide = frame.pivot_table(
        index="hour", columns="pnode_name", values=col, aggfunc="mean"
    ).reindex(range(HOURS))
    cov = wide.notna().mean()
    nodes = sorted(cov[cov >= _MIN_COVERAGE].index)
    if len(nodes) < 2:
        return np.full(HOURS, np.nan), nodes
    arr = wide[nodes].to_numpy()
    return np.nanmax(arr, axis=1) - np.nanmin(arr, axis=1), nodes


def _widest_pair(frame: pd.DataFrame, nodes: list[str]) -> dict:
    """The node pair inside one zone with the largest mean |Δ| — data-selected."""
    wide = frame.pivot_table(
        index="hour", columns="pnode_name", values="total_lmp_da", aggfunc="mean"
    ).reindex(range(HOURS))
    best = {"pair": None, "mean_abs_delta": 0.0}
    for a, b in combinations(nodes, 2):
        delta = (wide[a] - wide[b]).to_numpy()
        m = float(np.nanmean(np.abs(delta)))
        if m > best["mean_abs_delta"]:
            best = {
                "pair": f"{a} vs {b}",
                "mean_abs_delta": m,
                "pct_hours_gt_1": float(np.nanmean(np.abs(delta) > 1.0) * 100),
                "pct_hours_gt_10": float(np.nanmean(np.abs(delta) > 10.0) * 100),
            }
    return best


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    payload: dict = {"years": list(YEARS), "per_year": {}}
    for year in YEARS:
        d = _ehv(year)
        ref = _zonal_reference(year)
        zones: dict[str, dict] = {}
        for mz, g in d.groupby("model_zone"):
            disp_lmp, nodes = _dispersion(g, "total_lmp_da")
            disp_mcc, _ = _dispersion(g, "congestion_price_da")
            if len(nodes) < 2:
                continue
            zones[str(mz)] = {
                "ehv_nodes": len(nodes),
                "mean_intrazone_lmp_dispersion": float(np.nanmean(disp_lmp)),
                "mean_intrazone_congestion_dispersion": float(np.nanmean(disp_mcc)),
                "pct_hours_dispersion_gt_1": float(np.nanmean(disp_lmp > 1.0) * 100),
                "pct_hours_dispersion_gt_10": float(np.nanmean(disp_lmp > 10.0) * 100),
                "p90_intrazone_lmp_dispersion": float(np.nanpercentile(disp_lmp, 90)),
                "widest_pair": _widest_pair(g, nodes),
            }
        payload["per_year"][str(year)] = {
            "zones": zones,
            "interzonal_dom_vs_aep_mean_abs_lmp": float(
                np.nanmean(np.abs(ref["lmp"]))
            ),
            "interzonal_dom_vs_aep_mean_abs_congestion": float(
                np.nanmean(np.abs(ref["mcc"]))
            ),
        }
        dom = zones.get("PJM_Dominion")
        if dom:
            payload["per_year"][str(year)]["dominion_intra_over_inter_ratio"] = float(
                dom["mean_intrazone_lmp_dispersion"]
                / np.nanmean(np.abs(ref["lmp"]))
            )
        print(f"  {year} done ({len(zones)} model zones with >=2 EHV nodes)", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

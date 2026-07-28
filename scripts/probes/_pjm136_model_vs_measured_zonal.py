"""pjm-136 M1a/M2b (no LP): the model's zonal dual structure against PJM's own
zonal prices, on all EIGHT model zones.

The hub-based companion (`_pjm136_zonal_dual_structure.py`) established the
decomposition on the twelve published trading hubs. This probe runs the same
questions on PJM's `type = ZONE` pnodes, which crosswalk 1:1 onto every model
zone via the canonical `eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS` — including
`PJM_West_APS`, `PJM_Central_PA` and `PJM_SWMAAC`, the three zones no hub covers
and two of which are Dominion's other import paths.

Three measurements, no solve:

* **M1a — where the MODEL separates.** The LP is lossless with `flow_cost = 0`,
  so two zones joined by an uncongested path clear at the identical dual: model
  price separation *is* the statement "the path between them binds" (the
  `_pjm134_c2_dominion_interface.py` identity). Read off the keeper's committed
  `hourly/system_<year>.parquet` P1 duals, this says exactly which internal
  links carry congestion in the model and how often — the dual-space half of
  M1, which needs no `flows.parquet`.
* **M1b — where PJM separates.** The same statistic on the measured zonal LMPs,
  and its congestion/loss split. The gap between M1a and M1b is the defect.
* **M2b — the derive preview.** The MISO-form marginal delivery-factor
  deviation `dev_z = sum(MLC_z) / sum(MEC)` per model zone, load-weighted across
  the PJM zones each model zone rolls up, plus the $ separation it implies at
  the measured MEC — i.e. what a PJM analogue of the shipped
  `miso_zonal_loss_surface` would actually price, before any LP is built.

Measured source: `data/raw/pjm-zonal-lmp/da_hrl_lmps_<year>_<month>.parquet`
(the pjm-136 intake, `scripts/data/fetch_pjm_zonal_lmp_components.py`), weighted
by the committed metered zonal load
(`data/raw/zone-specific-demand/PJM<year>_hrl_load_metered.csv`) — the same
local-clock file `eia930.zonal_shares.load_zonal_shares` uses, so model hour and
measured hour share one clock. Model source: the committed keeper bundle's
`hourly/` sidecars. Nothing is written outside `results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm136_model_vs_measured_zonal.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR
from market_sim.data.eia930.zonal_shares import _PJM_LOAD_ZONE_GROUPS

YEARS = (2023, 2024, 2025)
HOURS = 8760

KEEPER_DIR = Path("results/calibration/pjm135_netpos_keeper_C")
ZONAL_LMP_DIR = RAW_DATA_DIR / "pjm-zonal-lmp"
OUT_PATH = Path("results/probes/pjm136_model_vs_measured_zonal.json")

#: PJM LMP `type = ZONE` pnode name -> the metered-load zone code the canonical
#: `_PJM_LOAD_ZONE_GROUPS` crosswalk is keyed on. Pure naming aliases (the LMP
#: feed spells zones out, the metered-load feed abbreviates); no judgement.
LMP_PNODE_TO_LOAD_ZONE: dict[str, str] = {
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
}

#: Aggregate pnodes that are not transmission zones (system / regional rollups).
NON_ZONE_PNODES = ("PJM-RTO", "MID-ATL/APS")

MODEL_ZONES = (
    "PJM_ComEd",
    "PJM_AEP_Ohio",
    "PJM_ATSI",
    "PJM_West_APS",
    "PJM_Central_PA",
    "PJM_Dominion",
    "PJM_EMAAC",
    "PJM_SWMAAC",
)

#: The model's internal PJM links (iso_configs._pjm_config), the only boundaries
#: on which a dual difference is a statement about a transmission constraint.
MODEL_LINKS = (
    ("PJM_ComEd", "PJM_AEP_Ohio"),
    ("PJM_AEP_Ohio", "PJM_ATSI"),
    ("PJM_AEP_Ohio", "PJM_Dominion"),
    ("PJM_AEP_Ohio", "PJM_West_APS"),
    ("PJM_ATSI", "PJM_Central_PA"),
    ("PJM_West_APS", "PJM_Central_PA"),
    ("PJM_West_APS", "PJM_SWMAAC"),
    ("PJM_West_APS", "PJM_Dominion"),
    ("PJM_Central_PA", "PJM_EMAAC"),
    ("PJM_SWMAAC", "PJM_EMAAC"),
    ("PJM_SWMAAC", "PJM_Dominion"),
)

#: Below this a dual difference is HiGHS noise, not congestion.
EPS = 1e-6
#: The materiality threshold the pjm-134/135 lineage quotes.
MATERIAL = 1.0

_MONTH_START_HOUR = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def _hour_of_year(ts: pd.Series) -> np.ndarray:
    """Non-leap hour-of-year index for naive local timestamps (Feb 29 removed)."""
    return (
        _MONTH_START_HOUR[ts.dt.month.to_numpy() - 1]
        + (ts.dt.day.to_numpy() - 1) * 24
        + ts.dt.hour.to_numpy()
    )


def _model_duals(year: int) -> pd.DataFrame:
    """Keeper P1 hourly zonal duals, hour-of-year index x model zone."""
    frame = pd.read_parquet(KEEPER_DIR / "hourly" / f"system_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot(index="hour", columns="zone", values="price")


def _metered_load(year: int) -> pd.DataFrame:
    """Metered PJM zonal load (MW), hour-of-year index x load-zone code."""
    path = RAW_DATA_DIR / "zone-specific-demand" / f"PJM{year}_hrl_load_metered.csv"
    frame = pd.read_csv(path, usecols=["datetime_beginning_ept", "zone", "mw"])
    ept = pd.to_datetime(frame["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    frame = frame[keep].copy()
    frame["hour"] = _hour_of_year(ept[keep])
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    return frame.pivot_table(index="hour", columns="zone", values="mw", aggfunc="mean")


def _measured_components(year: int) -> dict[str, pd.DataFrame]:
    """Load-weighted measured DA components per MODEL zone, hour-of-year index.

    Returns one frame per component (``lmp``/``mcc``/``mlc``/``mec``), each
    hour-of-year x model zone. A model zone that rolls up several PJM
    transmission zones is aggregated by that hour's metered load in each — the
    definition of a zonal price, and the same weighting
    ``eia930.zonal_shares`` uses to build the model's own zonal demand.
    """
    files = sorted(ZONAL_LMP_DIR.glob(f"da_hrl_lmps_{year}_*.parquet"))
    if not files:
        raise SystemExit(
            f"no measured zonal LMP parquet for {year} — run "
            "scripts/data/fetch_pjm_zonal_lmp_components.py first"
        )
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw = raw[~raw["pnode_name"].isin(NON_ZONE_PNODES)].copy()

    ept = pd.to_datetime(raw["datetime_beginning_ept"], format="mixed")
    keep = (ept.dt.year == year) & ~((ept.dt.month == 2) & (ept.dt.day == 29))
    raw = raw[keep].copy()
    raw["hour"] = _hour_of_year(ept[keep])
    raw["load_zone"] = raw["pnode_name"].map(LMP_PNODE_TO_LOAD_ZONE)
    missing = sorted(set(raw.loc[raw["load_zone"].isna(), "pnode_name"]))
    if missing:
        raise SystemExit(f"unmapped PJM LMP zone pnodes: {missing}")
    raw["model_zone"] = raw["load_zone"].map(_PJM_LOAD_ZONE_GROUPS)
    unmapped = sorted(set(raw.loc[raw["model_zone"].isna(), "load_zone"]))
    if unmapped:
        raise SystemExit(f"load zones absent from _PJM_LOAD_ZONE_GROUPS: {unmapped}")

    load = _metered_load(year)
    weights = load.stack().rename("mw").reset_index()
    weights.columns = ["hour", "load_zone", "mw"]
    raw = raw.merge(weights, on=["hour", "load_zone"], how="left")
    # A zone with no metered row that hour falls back to an equal weight rather
    # than dropping out of its model zone's average.
    raw["mw"] = raw["mw"].fillna(raw["mw"].median())

    out: dict[str, pd.DataFrame] = {}
    for key, col in (
        ("lmp", "total_lmp_da"),
        ("mcc", "congestion_price_da"),
        ("mlc", "marginal_loss_price_da"),
        ("mec", "system_energy_price_da"),
    ):
        raw["_wv"] = raw[col] * raw["mw"]
        num = raw.pivot_table(
            index="hour", columns="model_zone", values="_wv", aggfunc="sum"
        )
        den = raw.pivot_table(
            index="hour", columns="model_zone", values="mw", aggfunc="sum"
        )
        out[key] = (num / den).reindex(range(HOURS))
    raw.drop(columns="_wv", inplace=True)
    return out


def _sep_stats(diff: np.ndarray) -> dict[str, float]:
    """Separation statistics for one signed hourly price-difference series."""
    good = diff[~np.isnan(diff)]
    n = good.size
    return {
        "n_hours": int(n),
        "share_separated": round(float((np.abs(good) > EPS).sum() / n), 4),
        "share_material": round(float((np.abs(good) > MATERIAL).sum() / n), 4),
        "share_a_dearer": round(float((good > EPS).sum() / n), 4),
        "mean_spread": round(float(good.mean()), 4),
        "mean_abs_spread": round(float(np.abs(good).mean()), 4),
        "p90_abs_spread": round(float(np.percentile(np.abs(good), 90)), 4),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--bundle", default=str(KEEPER_DIR))
    args = ap.parse_args(argv)
    bundle = Path(args.bundle)

    payload: dict[str, object] = {
        "probe": "pjm136_model_vs_measured_zonal",
        "session": "pjm-136",
        "no_lp": True,
        "model_bundle": str(bundle),
        "measured_source": str(ZONAL_LMP_DIR / "da_hrl_lmps_<year>_<month>.parquet"),
        "years": {},
    }

    print("=" * 84)
    print("pjm-136 M1a/M2b — model duals vs PJM's own zonal DA prices (8 model zones)")
    print("=" * 84)

    for year in YEARS:
        model = _model_duals(year)
        meas = _measured_components(year)
        block: dict[str, object] = {}

        # ---- M1a/M1b: link-by-link separation, model vs measured ------------
        links: list[dict[str, object]] = []
        for a, b in MODEL_LINKS:
            m_diff = (model[a] - model[b]).to_numpy()
            x_diff = (meas["lmp"][a] - meas["lmp"][b]).to_numpy()
            c_diff = (meas["mcc"][a] - meas["mcc"][b]).to_numpy()
            l_diff = (meas["mlc"][a] - meas["mlc"][b]).to_numpy()
            links.append(
                {
                    "zone_a": a,
                    "zone_b": b,
                    "model": _sep_stats(m_diff),
                    "measured_total": _sep_stats(x_diff),
                    "measured_congestion": _sep_stats(c_diff),
                    "measured_loss": _sep_stats(l_diff),
                }
            )
        block["links"] = links

        # ---- copper-plate census: how many distinct duals per hour ----------
        duals = model[list(MODEL_ZONES)].to_numpy()
        spread = np.nanmax(duals, axis=1) - np.nanmin(duals, axis=1)
        block["copper_plate"] = {
            "share_hours_all_eight_identical": round(
                float((spread <= EPS).sum() / spread.size), 4
            ),
            "share_hours_spread_over_1": round(
                float((spread > MATERIAL).sum() / spread.size), 4
            ),
            "mean_max_spread": round(float(np.nanmean(spread)), 4),
        }
        meas_lmp = meas["lmp"][list(MODEL_ZONES)].to_numpy()
        # The measured frame is on the EPT clock, which has no 02:00 on the
        # spring-forward day and two 01:00s on the fall-back day; those 1-2
        # hours per year land as all-NaN rows and are excluded, never imputed.
        covered = ~np.isnan(meas_lmp).all(axis=1)
        block["copper_plate"]["measured_hours_missing"] = int((~covered).sum())
        meas_spread = np.nanmax(meas_lmp[covered], axis=1) - np.nanmin(
            meas_lmp[covered], axis=1
        )
        block["copper_plate"]["measured_mean_max_spread"] = round(
            float(np.nanmean(meas_spread)), 4
        )
        block["copper_plate"]["measured_share_hours_all_identical"] = round(
            float((meas_spread <= EPS).sum() / meas_spread.size), 4
        )

        # ---- M2b: delivery-factor deviation per model zone ------------------
        mec = meas["mec"].mean(axis=1)  # identical across zones by construction
        dev: dict[str, dict[str, float]] = {}
        denom = float(mec.sum())
        for zone in MODEL_ZONES:
            mlc = meas["mlc"][zone]
            dev[zone] = {
                "dev_annual": round(float(mlc.sum()) / denom, 6),
                "mean_mlc": round(float(mlc.mean()), 4),
            }
        # Load-weighted fleet reference: the PJM-wide marginal loss the zonal
        # deviations are measured against (an LP has no slack bus, so what a
        # hurdle prices is each zone's deviation FROM the system).
        ref = float(np.mean([v["dev_annual"] for v in dev.values()]))
        for zone in MODEL_ZONES:
            dev[zone]["dev_vs_fleet_mean"] = round(dev[zone]["dev_annual"] - ref, 6)
        block["delivery_factor"] = {
            "mean_mec": round(float(mec.mean()), 4),
            "fleet_mean_dev": round(ref, 6),
            "zones": dev,
        }

        payload["years"][str(year)] = block

        # ------------------------------------------------------------ report
        cp = block["copper_plate"]
        print(f"\n### {year}")
        print(
            f"  copper-plate: model all-8-zones-identical in "
            f"{100 * cp['share_hours_all_eight_identical']:.1f}% of hours "
            f"(mean max spread ${cp['mean_max_spread']:.2f}); measured identical in "
            f"{100 * cp['measured_share_hours_all_identical']:.1f}% "
            f"(mean max spread ${cp['measured_mean_max_spread']:.2f})"
        )
        print(
            f"\n  {'model link':34s} {'MODEL sep':>10s} {'>$1':>7s} | "
            f"{'MEAS sep':>9s} {'>$1':>7s} {'meanΔ':>8s} {'cong':>8s} {'loss':>8s}"
        )
        for row in links:
            name = (
                f"{row['zone_a'].replace('PJM_', '')}→"
                f"{row['zone_b'].replace('PJM_', '')}"
            )
            print(
                f"  {name:34s} {100 * row['model']['share_separated']:9.1f}% "
                f"{100 * row['model']['share_material']:6.1f}% | "
                f"{100 * row['measured_total']['share_separated']:8.1f}% "
                f"{100 * row['measured_total']['share_material']:6.1f}% "
                f"{row['measured_total']['mean_spread']:8.3f} "
                f"{row['measured_congestion']['mean_spread']:8.3f} "
                f"{row['measured_loss']['mean_spread']:8.3f}"
            )
        print(
            f"\n  delivery-factor deviation (mean MEC "
            f"${block['delivery_factor']['mean_mec']:.2f}/MWh):"
        )
        for zone in MODEL_ZONES:
            row = dev[zone]
            print(
                f"    {zone:18s} dev {row['dev_annual']:+.5f}  "
                f"vs fleet {row['dev_vs_fleet_mean']:+.5f}  "
                f"mean MLC {row['mean_mlc']:+.3f} $/MWh"
            )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"\nwrote {OUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

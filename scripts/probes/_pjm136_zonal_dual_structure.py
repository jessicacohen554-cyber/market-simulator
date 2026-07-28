"""pjm-136 M2/M3 (no LP): what produces PJM's zonal price separation, and can an
8-zone reduction carry it?

The pjm-136 charter's premise, measured by pjm-135 and carried here: the model's
PJM is a **copper-plate** -- all eight zones plus the external star node clear at
one dual in 95.5/97.3/96.2 % of hours, while PJM's own published day-ahead prices
separate DOM from AEP-DAYTON by >$1 in ~50-63 %. Until something makes Dominion's
dual differ from its neighbours', no allocation lever can move the CT/CC
inversion (FINDING-pjm135 §7 closes the per-border lever by measurement).

The LP is **lossless with flow_cost = 0 on every PJM link**, so two zones joined
by an uncongested path clear at the identical dual *by construction*. PJM's real
price separation has two additive parts and only one of them needs a binding
limit:

    LMP_i = MEC + MCC_i + MLC_i        (PJM Manual 11 / OATT Att. K)
    LMP_i - LMP_j = (MCC_i - MCC_j) + (MLC_i - MLC_j)

`MCC` (congestion) requires a constraint to bind; `MLC` (marginal loss) does
not -- it is a pure network-physics gradient present in every hour. MISO already
ships exactly this as `ScenarioConfig.miso_zonal_loss_surface`
(`scripts/data/derive_miso_loss_surface.py`, miso-76 M3).

Two measurements, both from already-committed raw data, no solve:

* **M2 -- the loss/hurdle question.** Decompose the measured DOM-vs-neighbour
  day-ahead separation into its congestion and loss parts, per year: how much of
  the mean gap, and of the >$1 hours, is carried by each. Then compute the
  MISO-form marginal delivery-factor deviation `dev_z,m = sum(MLC_z) / sum(MEC)`
  per zone-month, i.e. exactly what a PJM analogue of the shipped MISO surface
  would consume, and the $ separation it implies.
* **M3 -- topology adequacy.** PJM publishes several hubs inside single model
  zones (ComEd holds CHICAGO / CHICAGO GEN / N ILLINOIS; EMAAC holds EASTERN /
  NEW JERSEY; AEP_Ohio holds AEP GEN / AEP-DAYTON). Comparing the *intra-zone*
  hub-pair spread against the *inter-zone* DOM-vs-AEP spread answers whether the
  8-zone reduction can express the congestion at all, or whether the separation
  lives inside a zone where no zonal mechanism can reach it.

M1 (which internal link would have to bind) needs `flows.parquet`, which is
gitignored and therefore absent from committed bundles; it runs in
`_pjm136_link_utilisation.py` against this session's control arm.

Source: `data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv` -- PJM Data Miner 2
`da_hrl_lmps` / `rt_hrl_lmps` hub rows, all four published component columns.
Nothing is written outside `results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm136_zonal_dual_structure.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import RAW_DATA_DIR

YEARS = (2023, 2024, 2025)

OUT_PATH = Path("results/probes/pjm136_zonal_dual_structure.json")

#: Hub -> model zone. Only hubs whose zone membership is unambiguous are mapped;
#: WESTERN HUB (the PJM-wide western trading hub, a weighted basket spanning
#: several zones), WEST INT HUB (a boundary/interface hub) and OHIO HUB (spans
#: AEP/DAY/DEOK/ATSI) are deliberately left OUT of the zone map and used only
#: where a basket is the right object. The mapped entries follow the crosswalk
#: already committed in `_pjm_c3c_summer_tail_decomp.py` and
#: `_pjm134_c2_dominion_interface.py`.
HUB_TO_ZONE: dict[str, str] = {
    "DOMINION HUB": "PJM_Dominion",
    "AEP-DAYTON HUB": "PJM_AEP_Ohio",
    "AEP GEN HUB": "PJM_AEP_Ohio",
    "ATSI GEN HUB": "PJM_ATSI",
    "CHICAGO HUB": "PJM_ComEd",
    "CHICAGO GEN HUB": "PJM_ComEd",
    "N ILLINOIS HUB": "PJM_ComEd",
    "EASTERN HUB": "PJM_EMAAC",
    "NEW JERSEY HUB": "PJM_EMAAC",
}

#: Hub pairs inside ONE model zone -- the 8-zone reduction represents each of
#: these as a single price by construction, so any spread here is congestion the
#: reduction cannot express at any zonal granularity.
INTRA_ZONE_PAIRS = (
    ("PJM_ComEd", "CHICAGO HUB", "N ILLINOIS HUB"),
    ("PJM_ComEd", "CHICAGO HUB", "CHICAGO GEN HUB"),
    ("PJM_ComEd", "N ILLINOIS HUB", "CHICAGO GEN HUB"),
    ("PJM_EMAAC", "EASTERN HUB", "NEW JERSEY HUB"),
    ("PJM_AEP_Ohio", "AEP-DAYTON HUB", "AEP GEN HUB"),
)

#: Hub pairs ACROSS model zones -- the separation a zonal mechanism could carry.
#: The first entry is the pjm-136 target pair.
INTER_ZONE_PAIRS = (
    ("DOMINION HUB", "AEP-DAYTON HUB"),
    ("DOMINION HUB", "AEP GEN HUB"),
    ("DOMINION HUB", "ATSI GEN HUB"),
    ("DOMINION HUB", "CHICAGO HUB"),
    ("DOMINION HUB", "EASTERN HUB"),
    ("AEP-DAYTON HUB", "CHICAGO HUB"),
    ("AEP-DAYTON HUB", "ATSI GEN HUB"),
    ("EASTERN HUB", "CHICAGO HUB"),
)

#: A separation below this is publication rounding on a 6-decimal feed, not a
#: price difference.
EPS = 1e-6

#: The materiality threshold the pjm-134/pjm-135 lineage already quotes for
#: "PJM's own DA congestion separates DOM from AEP-DAYTON by >$1".
MATERIAL = 1.0


def _load_year(year: int) -> pd.DataFrame:
    """Load PJM's published hourly hub LMP components for ``year``.

    Returns a frame indexed by (hub, EPT hour) carrying both market runs' four
    published columns. Rows are filtered to the calendar year in EPT, which is
    the settlement calendar the hourly model index also runs on.
    """
    path = RAW_DATA_DIR / "lmp-data" / f"PJM_{year}_rt_da_monthly_lmps.csv"
    frame = pd.read_csv(path)
    frame["ept"] = pd.to_datetime(frame["datetime_beginning_ept"])
    frame = frame[frame["ept"].dt.year == year].copy()
    return frame


def _pivot(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Hub-columned hourly matrix for one published component column."""
    return frame.pivot_table(
        index="ept", columns="pnode_name", values=column, aggfunc="mean"
    ).sort_index()


def _identity_check(frame: pd.DataFrame, run: str) -> dict[str, float]:
    """Verify LMP = MEC + MCC + MLC on the published rows (guards the algebra)."""
    resid = (
        frame[f"total_lmp_{run}"]
        - frame[f"system_energy_price_{run}"]
        - frame[f"congestion_price_{run}"]
        - frame[f"marginal_loss_price_{run}"]
    )
    return {
        "max_abs_residual": round(float(resid.abs().max()), 9),
        "mean_abs_residual": round(float(resid.abs().mean()), 9),
        "n_rows": int(resid.size),
    }


def _pair_decomposition(
    lmp: pd.DataFrame, mcc: pd.DataFrame, mlc: pd.DataFrame, near: str, far: str
) -> dict[str, object]:
    """Decompose the ``near`` minus ``far`` hourly spread into MCC and MLC parts.

    ``near`` is the zone under test (Dominion for the pjm-136 target pair); a
    positive spread means ``near`` is the dearer node, i.e. import-constrained
    and/or loss-penalised relative to ``far``.
    """
    d_lmp = (lmp[near] - lmp[far]).to_numpy()
    d_mcc = (mcc[near] - mcc[far]).to_numpy()
    d_mlc = (mlc[near] - mlc[far]).to_numpy()
    n = d_lmp.size

    material = np.abs(d_lmp) > MATERIAL
    n_mat = int(material.sum())
    # Of the material-spread hours, how many would survive with congestion
    # alone, and how many with losses alone? These overlap; the point is which
    # component can carry the gap on its own.
    mcc_alone = int((np.abs(d_mcc) > MATERIAL).sum())
    mlc_alone = int((np.abs(d_mlc) > MATERIAL).sum())

    # Mean-share attribution: the two components sum to the spread exactly, so
    # their means partition the mean spread.
    mean_lmp = float(d_lmp.mean())
    mean_mcc = float(d_mcc.mean())
    mean_mlc = float(d_mlc.mean())

    return {
        "near": near,
        "far": far,
        "n_hours": int(n),
        "mean_spread": round(mean_lmp, 4),
        "mean_congestion_part": round(mean_mcc, 4),
        "mean_loss_part": round(mean_mlc, 4),
        "loss_share_of_mean": (
            round(mean_mlc / mean_lmp, 4) if abs(mean_lmp) > 1e-9 else None
        ),
        "congestion_share_of_mean": (
            round(mean_mcc / mean_lmp, 4) if abs(mean_lmp) > 1e-9 else None
        ),
        "mean_abs_spread": round(float(np.abs(d_lmp).mean()), 4),
        "mean_abs_congestion": round(float(np.abs(d_mcc).mean()), 4),
        "mean_abs_loss": round(float(np.abs(d_mlc).mean()), 4),
        "share_hours_separated": round(float((np.abs(d_lmp) > EPS).sum() / n), 4),
        "share_hours_material": round(n_mat / n, 4),
        "share_hours_near_dearer": round(float((d_lmp > EPS).sum() / n), 4),
        "share_hours_material_congestion": round(mcc_alone / n, 4),
        "share_hours_material_loss": round(mlc_alone / n, 4),
        "loss_sign_persistence": round(
            float((d_mlc > EPS).sum() / n), 4
        ),  # share of hours the loss part alone makes `near` dearer
        "corr_spread_congestion": round(float(np.corrcoef(d_lmp, d_mcc)[0, 1]), 4),
        "corr_spread_loss": round(float(np.corrcoef(d_lmp, d_mlc)[0, 1]), 4),
        "p10_spread": round(float(np.percentile(d_lmp, 10)), 4),
        "p90_spread": round(float(np.percentile(d_lmp, 90)), 4),
    }


def _delivery_factor_surface(
    frame: pd.DataFrame, run: str
) -> dict[str, dict[str, float]]:
    """MISO-form marginal delivery-factor deviation per zone, annual and monthly.

    ``dev_z = sum(MLC_z,t) / sum(MEC_t)`` -- the MEC-weighted estimator
    `derive_miso_loss_surface.py` uses, chosen so the surface reproduces the
    measured total MLC exactly when re-multiplied by the measured MEC series.
    A negative deviation means the zone is *downstream*: delivering a marginal
    MW there costs more than one MW at the reference, so its LMP carries a
    positive loss component.
    """
    sub = frame[frame["pnode_name"].isin(HUB_TO_ZONE)].copy()
    sub["zone"] = sub["pnode_name"].map(HUB_TO_ZONE)
    sub["month"] = sub["ept"].dt.month

    mec = sub.groupby("ept")[f"system_energy_price_{run}"].mean()
    out: dict[str, dict[str, float]] = {}
    for zone, block in sub.groupby("zone"):
        # Average the zone's hubs first, so a multi-hub zone is one series.
        hourly = block.groupby("ept")[f"marginal_loss_price_{run}"].mean()
        aligned_mec = mec.reindex(hourly.index)
        denom = float(aligned_mec.sum())
        out[zone] = {
            "dev_annual": round(float(hourly.sum()) / denom, 6) if denom else None,
            "mean_mlc": round(float(hourly.mean()), 4),
            "n_hubs": int(block["pnode_name"].nunique()),
        }
    # Express each zone against the fleet-mean reference, which is what a
    # zonal LP hurdle would actually price (the LP has no slack bus).
    devs = {z: v["dev_annual"] for z, v in out.items() if v["dev_annual"] is not None}
    ref = float(np.mean(list(devs.values())))
    for zone, value in devs.items():
        out[zone]["dev_vs_fleet_mean"] = round(value - ref, 6)
    return out


def main() -> None:
    payload: dict[str, object] = {
        "probe": "pjm136_zonal_dual_structure",
        "session": "pjm-136",
        "no_lp": True,
        "source": "data/raw/lmp-data/PJM_<year>_rt_da_monthly_lmps.csv",
        "note": (
            "M2 loss-vs-congestion decomposition and M3 topology adequacy for "
            "the PJM zonal dual structure. Day-ahead is the primary basis (the "
            "DA market is the hourly full-network optimization the LP mirrors); "
            "real-time is reported alongside, never derived from."
        ),
        "years": {},
    }

    for year in YEARS:
        frame = _load_year(year)
        year_block: dict[str, object] = {
            "identity_check_da": _identity_check(frame, "da"),
            "identity_check_rt": _identity_check(frame, "rt"),
        }

        for run in ("da", "rt"):
            lmp = _pivot(frame, f"total_lmp_{run}")
            mcc = _pivot(frame, f"congestion_price_{run}")
            mlc = _pivot(frame, f"marginal_loss_price_{run}")

            inter = [
                _pair_decomposition(lmp, mcc, mlc, near, far)
                for near, far in INTER_ZONE_PAIRS
            ]
            intra = []
            for zone, hub_a, hub_b in INTRA_ZONE_PAIRS:
                block = _pair_decomposition(lmp, mcc, mlc, hub_a, hub_b)
                block["model_zone"] = zone
                intra.append(block)

            year_block[run] = {
                "inter_zone_pairs": inter,
                "intra_zone_pairs": intra,
                "delivery_factor_surface": _delivery_factor_surface(frame, run),
            }

        payload["years"][str(year)] = year_block

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, indent=2))

    # ---------------------------------------------------------------- report
    print("=" * 78)
    print("pjm-136 M2/M3 — PJM zonal dual structure (published DA components)")
    print("=" * 78)

    for year in YEARS:
        block = payload["years"][str(year)]
        idc = block["identity_check_da"]
        print(
            f"\n### {year}   LMP = MEC+MCC+MLC identity: max|resid| "
            f"{idc['max_abs_residual']:.2e} over {idc['n_rows']:,} rows"
        )
        da = block["da"]

        print("\n  M2 — inter-zone separation, decomposed (DA):")
        print(
            f"    {'pair':38s} {'mean Δ':>8s} {'cong':>8s} {'loss':>8s} "
            f"{'loss%':>7s} {'>$1 h':>7s} {'lossΔ>$1':>9s}"
        )
        for row in da["inter_zone_pairs"]:
            pair = f"{row['near'].replace(' HUB','')}-{row['far'].replace(' HUB','')}"
            ls = row["loss_share_of_mean"]
            print(
                f"    {pair:38s} {row['mean_spread']:8.3f} "
                f"{row['mean_congestion_part']:8.3f} {row['mean_loss_part']:8.3f} "
                f"{(100 * ls if ls is not None else float('nan')):7.1f} "
                f"{100 * row['share_hours_material']:6.1f}% "
                f"{100 * row['share_hours_material_loss']:8.1f}%"
            )

        print("\n  M3 — intra-zone hub spread (the reduction CANNOT express these):")
        print(
            f"    {'zone / pair':38s} {'mean|Δ|':>8s} {'|cong|':>8s} {'|loss|':>8s} "
            f"{'>$1 h':>7s}"
        )
        for row in da["intra_zone_pairs"]:
            pair = (
                f"{row['model_zone'].replace('PJM_','')}: "
                f"{row['near'].replace(' HUB','')}-{row['far'].replace(' HUB','')}"
            )
            print(
                f"    {pair:38s} {row['mean_abs_spread']:8.3f} "
                f"{row['mean_abs_congestion']:8.3f} {row['mean_abs_loss']:8.3f} "
                f"{100 * row['share_hours_material']:6.1f}%"
            )

        print("\n  M2 — marginal delivery-factor deviation (MISO-form, DA):")
        surface = da["delivery_factor_surface"]
        for zone in sorted(surface):
            row = surface[zone]
            print(
                f"    {zone:20s} dev {row['dev_annual']:+.5f}  "
                f"vs fleet mean {row.get('dev_vs_fleet_mean', float('nan')):+.5f}  "
                f"mean MLC {row['mean_mlc']:+.3f} $/MWh  ({row['n_hubs']} hub(s))"
            )

    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()

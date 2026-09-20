"""pjm-h12 card D-2 PHASE 0 — the zero-LP test a seam successor must pass first.

Rule 29 ``[R-SCREEN]`` clause (0) survives as PRACTICE: a question answerable
without an LP is answered without one. This probe answers card D-2's open
structural claim — *does a rank-preserving re-anchoring of the PJM seam ladder
improve the HOURLY fit* — entirely offline, from committed artifacts. The
previous arm (`seam_neighbour_hourly_ladder`, matrix cell ``O``) was ruled not
promotable because exactly that claim was contradicted by its solve. Six shards
are not spent again until the claim survives here.

WHAT IT DOES. The seam ladder's clearing law is a step function of price
(``scripts/data/derive_pjm_seam_ladders.offline_score``)::

    sim = sum_k step * 1[price > import_k] - sum_k step * 1[price < export_k]

The ladder's rungs are **quantiles of the MEASURED DA price** (``qq_import`` =
``quantile(da, 1 - exceed)``, ``qq_export`` = ``quantile(da, depth)``), but the
LP clears them against the **MODEL's** price. That Q-Q mismatch is the defect.
This probe drives the identical law with three price series and scores each
against the same measured flows:

  P9    measured DA           -- the derivation's own sanity check (should
                                 reproduce measured volume; pjm-174 read -0.046 TWh)
  ASIS  the model's own price -- what the LP does today
  ARM   the model's price, RANK-PRESERVINGLY re-anchored: each hour is mapped to
        the measured-DA price at the model price's OWN within-year quantile.
        Hourly ORDERING is untouched by construction, so the arm cannot
        manufacture hourly correlation -- it can only remove the level/spread
        mismatch. That is what makes the hourly reading admissible evidence.

Model prices come from the PJM keeper's committed ``hourly/system_<year>.parquet``
sidecars (rule 15 ``[R-DASHBOARD]`` commits them precisely so a diagnostic need
not replay a solve), load-weighted across zones to one system series per hour.

NOT A MECHANISM. Nothing here is wired into a solve and nothing is registered.
The ARM series is a DIAGNOSTIC reconstruction; the admissible forward-mode
mechanism it motivates is a *quantile-indexed* ladder (store each rung's
quantile and evaluate it against the model's own distribution), which carries no
measured price level and so regenerates for a forecast year -- see
``docs/ADDENDUM-pjm-h12-the-seam-is-a-variance-compression-2026-09-20.md``.

Usage::

    uv run python scripts/probes/pjm_h12_seam_qq_phase0.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

from derive_pjm_seam_ladders import (  # noqa: E402
    ACTUAL_LMP_PARQUET,
    load_joined,
    offline_score,
)

from market_sim.config.interchange_config import (  # noqa: E402
    PJM_SEAM_LADDER_BY_YEAR,
)

#: The PJM keeper pair whose committed sidecars carry the model price. The
#: touchpoint holds 2020-2022 and is folded to the keeper under rule 30
#: ``[R-TOUCHPOINT-FOLD]`` (a), so together they span every year PJM carries.
_BUNDLE_FOR_YEAR = {
    2020: "pjm_h11_touchpoint_span",
    2021: "pjm_h11_touchpoint_span",
    2022: "pjm_h11_touchpoint_span",
    2023: "pjm_h11_keeper_span",
    2024: "pjm_h11_keeper_span",
    2025: "pjm_h11_keeper_span",
}

YEARS = tuple(sorted(_BUNDLE_FOR_YEAR))


def model_system_price(year: int) -> pd.Series:
    """Load-weighted system hourly P1 price from the keeper's committed sidecar.

    The LP's zonal duals are collapsed to one system series the same way the
    seam clears against PJM as a whole. ``PJM_external`` is the import node, not
    a load zone, so it is excluded.
    """
    path = (
        REPO
        / "results"
        / "calibration"
        / _BUNDLE_FOR_YEAR[year]
        / "hourly"
        / f"system_{year}.parquet"
    )
    df = pd.read_parquet(path)
    df = df[(df["pass"] == "P1") & (df["zone"] != "PJM_external")]
    w = np.maximum(df["demand"].to_numpy(dtype=float), 1e-9)
    df = df.assign(_num=df["price"].to_numpy(dtype=float) * w, _den=w)
    g = df.groupby("hour")[["_num", "_den"]].sum()
    return (g["_num"] / g["_den"]).rename("model")


def rank_preserving_reanchor(model: np.ndarray, measured_da: np.ndarray) -> np.ndarray:
    """Map each model hour onto the measured-DA price at its OWN quantile.

    A strictly monotone transform of ``model``: the hourly ordering is preserved
    exactly, so Spearman rank correlation against any series is unchanged. Only
    the marginal distribution moves. Ties are resolved by average rank, which
    keeps the map single-valued.
    """
    n = model.size
    # average-rank -> quantile in (0, 1), then read the measured marginal there.
    order = pd.Series(model).rank(method="average").to_numpy(dtype=float)
    q = (order - 0.5) / n
    return np.quantile(np.sort(measured_da), q)


def main() -> int:
    if not ACTUAL_LMP_PARQUET.exists():
        sys.exit(f"missing measured LMP: {ACTUAL_LMP_PARQUET}")

    joined = load_joined(YEARS)
    seams = sorted(PJM_SEAM_LADDER_BY_YEAR[YEARS[0]])

    rows: list[dict] = []
    for year in YEARS:
        g = joined.loc[year].copy()
        ladders = PJM_SEAM_LADDER_BY_YEAR[year]

        model = model_system_price(year).reindex(g.index)
        g = g.assign(model=model.to_numpy(dtype=float))
        g = g.dropna(subset=["da", "model"] + seams)
        if g.empty:
            print(f"{year}: no overlapping hours, skipped")
            continue

        da = g["da"].to_numpy(dtype=float)
        mod = g["model"].to_numpy(dtype=float)
        arm = rank_preserving_reanchor(mod, da)

        for tag, price in (("P9", da), ("ASIS", mod), ("ARM", arm)):
            scored = offline_score(g.assign(da=price), ladders)
            for seam, s in scored.items():
                rows.append({"year": year, "driver": tag, "seam": seam, **s})

    out = pd.DataFrame(rows)
    if out.empty:
        sys.exit("no rows scored")

    agg = (
        out.groupby(["year", "driver"])
        .agg(
            sim_twh=("sim_twh", "sum"),
            act_twh=("act_twh", "sum"),
            hourly_corr=("hourly_corr", "mean"),
            dur_rmse=("dur_rmse", "mean"),
        )
        .reset_index()
    )
    agg["vol_err_twh"] = agg["sim_twh"] - agg["act_twh"]

    print()
    print("PJM seam ladder, offline clearing under three price drivers")
    print("  P9   = measured DA (the derivation's own check)")
    print("  ASIS = the model's own price (what the LP does today)")
    print(
        "  ARM  = model price, RANK-PRESERVINGLY re-anchored to the measured marginal"
    )
    print()
    hdr = f"{'year':6} {'driver':7} {'sim TWh':>9} {'act TWh':>9} {'vol err':>9} {'hourly r':>9} {'dur RMSE':>9}"
    print(hdr)
    print("-" * len(hdr))
    for year in YEARS:
        sub = agg[agg["year"] == year]
        if sub.empty:
            continue
        for tag in ("P9", "ASIS", "ARM"):
            r = sub[sub["driver"] == tag]
            if r.empty:
                continue
            r = r.iloc[0]
            print(
                f"{year:6} {tag:7} {r['sim_twh']:9.3f} {r['act_twh']:9.3f} "
                f"{r['vol_err_twh']:+9.3f} {r['hourly_corr']:9.4f} {r['dur_rmse']:9.1f}"
            )
        print()

    print("SPAN TOTALS (sum over years; hourly r and duration RMSE averaged)")
    print(f"{'driver':7} {'vol err TWh':>12} {'hourly r':>10} {'dur RMSE':>10}")
    for tag in ("P9", "ASIS", "ARM"):
        s = agg[agg["driver"] == tag]
        print(
            f"{tag:7} {s['vol_err_twh'].sum():12.3f} "
            f"{s['hourly_corr'].mean():10.4f} {s['dur_rmse'].mean():10.1f}"
        )

    print()
    print("PER-SEAM hourly r, ASIS -> ARM (the claim the last arm failed)")
    piv = out.pivot_table(
        index="seam", columns="driver", values="hourly_corr", aggfunc="mean"
    )
    print(f"{'seam':12} {'P9':>8} {'ASIS':>8} {'ARM':>8} {'delta':>8}")
    for seam in piv.index:
        r = piv.loc[seam]
        print(
            f"{seam:12} {r.get('P9', float('nan')):8.4f} {r.get('ASIS', float('nan')):8.4f} "
            f"{r.get('ARM', float('nan')):8.4f} {r.get('ARM', 0) - r.get('ASIS', 0):+8.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

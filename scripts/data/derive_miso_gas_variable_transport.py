"""Derive each MISO gas plant's VARIABLE transport over its zone's traded hub.

Rule 23 ``[R-FROZEN-DERIVE]``: a measured-behaviour parameter table.  It
re-derives ONLY when its source data updates (a new EIA-923 vintage or a new
hub-series year) — never because a residual moved.  Re-derivation commits cite
the data change.

WHAT THIS MEASURES, and why it is the right object
--------------------------------------------------
The owner ruled (2026-09-06, on miso-212 §8 / miso-224 §5) that a MISO gas
dispatch offer is priced at **marginal commodity plus variable transport** — not
at the bare traded hub (the miso-224 screen arm, killed on G-3/G-4) and not at
the EIA-923 AVERAGE delivered print (the incumbent keeper's overlay).  The
ruling is conditioned: the variable-transport component must be MEASURED, with
zero fitted scalars, or the arm does not run.

A plant's EIA-923 monthly print is its AVERAGE delivered cost — the commodity it
bought plus every charge it paid, divided by that month's takes.  Split it the
way the tariff itself is split:

    print[p,m] - hub[p,m]  =  v[p]  +  F[p] / burn[p,m]

* ``v[p]`` is the VOLUME-INVARIANT wedge over the traded hub: the pipeline usage
  (commodity) charge, fuel retention, and any delivery-point basis the plant pays
  on the *next* MMBtu.  That is the ruling's "variable transport".
* ``F[p]`` is the month's FIXED charge in dollars — reservation/demand charges
  and contracted transport, which do not change with the next MMBtu and which a
  dispatch offer must not carry.

The estimator is weighted least squares of the wedge on ``1/burn`` over the
plant's own admissible months, pooled across 2023-2025, with **weight = burn**.
The weighting is not a convenience: a month's print is itself the volume-weighted
mean price of that month's deliveries, so its sampling variance scales as
``1/burn`` and ``burn`` is the efficient WLS weight.  It also makes the pooled
fallback rungs mean what they say — the cost of a POOLED MMBtu rather than the
cost of an average plant-month, which a fleet of peakers burning almost nothing
would otherwise dominate (unweighted, the MISO-wide rung reads $1.97/MMBtu
against a capacity-weighted fleet of $0.89).  The unweighted OLS value is emitted
alongside every row as ``v_ols_usd_mmbtu`` so the choice is auditable and was
made once, before any arm was solved, and never swept.  ONE value per plant for every scored year
(rule 1 ``[R-STRUCT]`` condition (b): one config across every scored year; a
per-year value would be per-year fitting).  Nothing here is swept against any
gate, and no value is chosen: the number is whatever the receipts say.

IDENTIFICATION EVIDENCE (miso-225 phase 0, all committed):

* The within-plant burn spread is large — median max/min = 38.7x — so the
  intercept and slope ARE separately identified; the low per-plant R2
  (0.07-0.37 by class) is noise in a self-reported monthly print, not a lack of
  spread.
* An independent, REGRESSION-FREE estimator confirms it: the plant's own
  top-burn-quartile burn-weighted wedge, which amortizes 79 % of the fitted
  fixed leg away (cap-weighted $1.114 -> $0.231/MMBtu), lands at ``v`` plus
  exactly its own measured residual fixed leg (CC_REGULAR: top-quartile $0.386 =
  ``v`` $0.213 + residual $0.173).  The two estimators agree at r = 0.975 across
  the fleet.  The regression is primary because it removes the fixed leg by
  construction; the top-quartile is the cross-check and is emitted alongside.
* The print is measurably an AVERAGE, not a marginal cost: month-over-month, the
  slope of d(wedge) on d(hub) is **-0.69 fleet-wide and -0.76 for CC_REGULAR**
  (a perfectly lagged average implies -1; a hub-tracking marginal cost implies
  0), and the wedge LEVEL is uncorrelated with the hub level (r = -0.02).

FORWARD ANALOGUE (rule 13 ``[R-MEASURED]``'s admissibility test).  ``v[p]`` is a
contractual/physical attribute of the plant's delivery path.  A forecast year
re-identifies it from the then-current EIA-923 vintage by this same frozen
formula and applies it to the forward hub, so the quantity regenerates from
forward drivers and responds to changed conditions through the hub.

FALLBACK LADDER, declared here and not tuned: **own -> (zone, class) -> class ->
MISO-wide**.  A plant carries its own ``v`` only with at least ``MIN_MONTHS``
admissible plant-months AND a burn spread of at least ``MIN_BURN_SPREAD``.  The
CLASS rung sits above the MISO-wide one because a receipt-less combined cycle
resembles other combined cycles far more than it resembles the peaker fleet that
dominates the ISO-wide pool by plant count (MISO-wide $1.97 against a
capacity-weighted fleet $0.89).  Only 70 % of MISO gas nameplate has any
EIA-923 gas receipt at all, so the ladder is load-bearing — it mirrors the print
path's own ISO-restricted nearby/state pooling
(:func:`~market_sim.data.fuel.plant_prices.apply_plant_monthly_fuel_prices`).

NO CLIPPING.  A negative ``v`` is kept as measured (12 plants / 8.3 GW): the
MidCon zones are priced off the Chicago series by the documented rule-14
reconciliation in :func:`~market_sim.data.fuel.basis.miso.apply_miso_gas_marginal_commodity`,
and a MidCon plant really does buy under the Chicago index.  Clipping at zero
would be a choice; reporting is a measurement.

Usage::

    PYTHONPATH=src python3 scripts/data/derive_miso_gas_variable_transport.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.fuel.basis.miso import _miso_zone_hub_kind
from market_sim.data.fuel.hubs import (
    _flow_date_staircase,
    _henry_hub_daily_dated,
    _miso_citygate_daily_dated,
    _trade_date_staircase,
)

ROOT = Path(__file__).resolve().parents[2]
BINS = ROOT / "data/raw/_processed-legacy/bin_assignments_MISO.csv"
F923 = ROOT / "data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet"
OUT = ROOT / "data/raw/reference/miso_gas_variable_transport.csv"

#: Rule 22 ``[R-HOLDOUT]`` — the training tier.  ONE pooled value per plant over
#: all three years (rule 1 condition (b)); never a per-year value.
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: A plant carries its OWN ``v`` only with this many admissible plant-months and
#: this much burn spread.  Declared before any arm was solved; never swept.
MIN_MONTHS = 12
MIN_BURN_SPREAD = 2.0

#: The gas classes of ``bin_assignments_MISO.csv``.  COAL is out of scope: this
#: table prices gas rows only.
GAS_GROUPS = ("CC_", "CT_", "ST_GAS", "ST_CHP")


def _hub_month_means(years: tuple[int, ...]) -> dict[tuple[str, int, int], float]:
    """Return ``{(hub_kind, year, month): mean daily hub $/MMBtu}``.

    Built from the SAME daily staircases
    :func:`~market_sim.data.fuel.basis.miso.apply_miso_gas_marginal_commodity`
    prices the arm's gas rows from — Chicago on its gas FLOW day, Henry Hub on
    its trade day — so ``v`` is measured against the very series it will be
    added to, not against a proxy for it.
    """
    out: dict[tuple[str, int, int], float] = {}
    chi_all = _miso_citygate_daily_dated(None)
    hh_all = _henry_hub_daily_dated(None)
    for year in years:
        chi = _flow_date_staircase(chi_all.get(year, {}), year)
        hh = _trade_date_staircase(hh_all.get(year, {}), year)
        for kind, arr in (("chicago", chi), ("henry", hh)):
            if arr is None:
                continue
            vals = np.asarray(arr, dtype=float)
            freq = "D" if len(vals) <= 366 else "h"
            idx = pd.date_range(f"{year}-01-01", periods=len(vals), freq=freq)
            series = pd.Series(vals, index=idx)
            for month, grp in series.groupby(series.index.month):
                out[(kind, year, int(month))] = float(grp.mean())
    return out


def _fit(
    wedge: np.ndarray, burn: np.ndarray, *, weighted: bool = True
) -> tuple[float, float, float]:
    """Fit ``wedge = v + F * (1/burn)``; return ``(v, F_usd_month, weighted r2)``.

    ``weighted`` selects the burn-weighted WLS (the estimator this table ships,
    efficient because a month's print has variance ~ ``1/burn``) over plain OLS
    (emitted alongside for audit).
    """
    x = 1.0 / burn
    design = np.column_stack([np.ones_like(x), x])
    w = np.sqrt(burn) if weighted else np.ones_like(burn)
    coef, *_ = np.linalg.lstsq(design * w[:, None], wedge * w, rcond=None)
    resid = (wedge - design @ coef) * w
    mean = float((wedge * w**2).sum() / (w**2).sum())
    ss_res = float((resid**2).sum())
    ss_tot = float((((wedge - mean) * w) ** 2).sum())
    return (
        float(coef[0]),
        float(coef[1]),
        (1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")),
    )


def _top_quartile(wedge: np.ndarray, burn: np.ndarray) -> float:
    """Regression-free cross-check: burn-weighted wedge in the top burn quartile."""
    cut = float(np.quantile(burn, 0.75))
    sel = burn >= cut
    return float((wedge[sel] * burn[sel]).sum() / burn[sel].sum())


def build_panel(years: tuple[int, ...] = YEARS) -> pd.DataFrame:
    """Return the admissible (plant, year, month) wedge panel for MISO gas."""
    bins = pd.read_csv(BINS)
    gas = bins[bins["Plant_Group"].astype(str).str.startswith(GAS_GROUPS)].copy()
    zone_kind = _miso_zone_hub_kind(years[0])
    gas["hub_kind"] = gas["Zone"].map(zone_kind).fillna("chicago")

    f923 = pd.read_parquet(F923)
    f923 = f923[
        (f923["fuel_group"] == "Natural Gas")
        & (f923["year"].isin(years))
        & (f923["quantity"] > 0)
        & (f923["price_per_mmbtu"] > 0)
    ]
    hub = _hub_month_means(years)

    rows: list[dict[str, object]] = []
    for plant in gas.itertuples():
        for rec in f923[f923["plant_id"] == int(plant.Plant_Code)].itertuples():
            level = hub.get((plant.hub_kind, int(rec.year), int(rec.month)))
            if level is None:
                continue
            rows.append(
                {
                    "plant_id": int(plant.Plant_Code),
                    "plant_name": str(plant.Plant_Name),
                    "group": str(plant.Plant_Group),
                    "zone": str(plant.Zone),
                    "hub_kind": str(plant.hub_kind),
                    "nameplate_mw": float(plant.Nameplate_MW),
                    "year": int(rec.year),
                    "month": int(rec.month),
                    "burn_mmbtu": float(rec.quantity),
                    "hub_usd_mmbtu": level,
                    "wedge_usd_mmbtu": float(rec.price_per_mmbtu) - level,
                }
            )
    return pd.DataFrame(rows)


def derive(years: tuple[int, ...] = YEARS) -> pd.DataFrame:
    """Return the per-plant variable-transport table, fallback ladder applied."""
    panel = build_panel(years)
    if panel.empty:
        raise ValueError(
            "MISO gas wedge panel is empty — check the F923 and hub inputs"
        )

    # Pooled rungs first, so a plant that misses its own bars can take one.
    pooled_zone_group: dict[tuple[str, str], float] = {}
    for key, grp in panel.groupby(["zone", "group"]):
        if len(grp) >= MIN_MONTHS:
            pooled_zone_group[key] = _fit(
                grp["wedge_usd_mmbtu"].to_numpy(float),
                grp["burn_mmbtu"].to_numpy(float),
            )[0]
    pooled_group: dict[str, float] = {}
    for key, grp in panel.groupby("group"):
        if len(grp) >= MIN_MONTHS:
            pooled_group[str(key)] = _fit(
                grp["wedge_usd_mmbtu"].to_numpy(float),
                grp["burn_mmbtu"].to_numpy(float),
            )[0]
    pooled_iso = _fit(
        panel["wedge_usd_mmbtu"].to_numpy(float), panel["burn_mmbtu"].to_numpy(float)
    )[0]

    out: list[dict[str, object]] = []
    for plant_id, grp in panel.groupby("plant_id"):
        burn = grp["burn_mmbtu"].to_numpy(float)
        wedge = grp["wedge_usd_mmbtu"].to_numpy(float)
        spread = float(burn.max() / burn.min()) if burn.min() > 0 else float("inf")
        own = len(grp) >= MIN_MONTHS and spread >= MIN_BURN_SPREAD
        v_fit, fixed, r2 = _fit(wedge, burn)
        v_ols = _fit(wedge, burn, weighted=False)[0]
        key = (grp["zone"].iloc[0], grp["group"].iloc[0])
        if own:
            v, source = v_fit, "own"
        elif key in pooled_zone_group:
            v, source = pooled_zone_group[key], "zone_group_pool"
        elif key[1] in pooled_group:
            v, source = pooled_group[key[1]], "group_pool"
        else:
            v, source = pooled_iso, "miso_pool"
        out.append(
            {
                "plant_id": int(plant_id),
                "plant_name": grp["plant_name"].iloc[0],
                "group": key[1],
                "zone": key[0],
                "nameplate_mw": float(grp["nameplate_mw"].iloc[0]),
                "n_months": int(len(grp)),
                "burn_spread": round(spread, 3),
                "v_usd_mmbtu": round(v, 6),
                "v_source": source,
                "fixed_usd_month": round(fixed, 3),
                "r2": round(r2, 4),
                "v_ols_usd_mmbtu": round(v_ols, 6),
                "v_topquartile_usd_mmbtu": round(_top_quartile(wedge, burn), 6),
                "wedge_burn_weighted": round(
                    float((wedge * burn).sum() / burn.sum()), 6
                ),
            }
        )
    frame = pd.DataFrame(out).sort_values("plant_id").reset_index(drop=True)
    frame.attrs["pooled_zone_group"] = {
        f"{k[0]}|{k[1]}": v for k, v in pooled_zone_group.items()
    }
    frame.attrs["pooled_group"] = dict(pooled_group)
    frame.attrs["pooled_iso"] = pooled_iso
    return frame


def main() -> None:
    """Write the derived table and print the fallback rungs a consumer needs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    frame = derive()
    header = [
        "# MISO gas VARIABLE transport over the zone's traded hub ($/MMBtu).",
        "# Derived by scripts/data/derive_miso_gas_variable_transport.py "
        f"from EIA-923 receipts x the daily hub staircases, {YEARS[0]}-{YEARS[-1]} pooled.",
        "# Rule 23 [R-FROZEN-DERIVE]: re-derive ONLY on a source-data update; cite it.",
        "# Consumers resolve a plant absent from this table down the declared ladder"
        " own -> zone_group -> group -> miso, whose rungs are in the sibling .pool.csv.",
        f"# Pooled fallback rungs: MISO-wide v = {frame.attrs['pooled_iso']:.6f} $/MMBtu; "
        "per (zone|group) rungs in the sibling .pool.csv.",
    ]
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w") as handle:
        handle.write("\n".join(header) + "\n")
        frame.to_csv(handle, index=False)
    pool = pd.DataFrame(
        [
            {"rung": "zone_group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_zone_group"].items())
        ]
        + [
            {"rung": "group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_group"].items())
        ]
        + [
            {
                "rung": "miso",
                "key": "__MISO__",
                "v_usd_mmbtu": round(frame.attrs["pooled_iso"], 6),
            }
        ]
    )
    pool.to_csv(args.out.with_suffix(".pool.csv"), index=False)

    mw = frame["nameplate_mw"].to_numpy(float)
    v = frame["v_usd_mmbtu"].to_numpy(float)
    print(f"plants {len(frame)}  MW {mw.sum():,.0f}")
    print(f"  v cap-weighted   {float((v * mw).sum() / mw.sum()):+.4f} $/MMBtu")
    print(f"  v p10/p50/p90    {np.percentile(v, [10, 50, 90]).round(4)}")
    print(f"  sources          {frame['v_source'].value_counts().to_dict()}")
    print(f"  MISO-wide pool   {frame.attrs['pooled_iso']:+.4f}")
    print(f"wrote {args.out}\nwrote {args.out.with_suffix('.pool.csv')}")


if __name__ == "__main__":
    main()

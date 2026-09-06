"""miso-225 phase 0 (A) — identify the MISO gas fleet's VARIABLE transport, per plant.

The owner ruled (2026-09-06, this session's opening ruling on miso-212 §8 /
miso-224 §5) that a MISO gas dispatch offer is priced at **marginal commodity
plus variable transport** — NOT at the bare traded hub the miso-224 arm
screened, and NOT at the EIA-923 average delivered print the keeper carries.
The ruling is conditioned: the variable-transport component must be MEASURED
and sourced before the arm is armed, with zero fitted scalars, or the arm does
not run.

THE IDENTIFICATION (rule 13 ``[R-MEASURED]``, rule 23 ``[R-FROZEN-DERIVE]``).
A plant's EIA-923 monthly delivered print is its AVERAGE delivered cost: the
commodity it bought, plus the pipeline/LDC charges it paid, amortized over that
month's takes.  Split the charges the way the tariff does:

    print[p,m] - hub[p,m]  =  v[p]  +  F[p] / burn[p,m]

``v[p]`` is the VOLUME-INVARIANT wedge over the traded hub — the usage
(commodity) charge, fuel retention and any delivery-point basis the plant pays
on the *next* MMBtu.  That is exactly the "variable transport" of the ruling.
``F[p]`` is the month's FIXED charge in dollars — reservation/demand charges and
contracted transport, which do not vary with the next MMBtu and which the ruling
says a dispatch offer must drop.  The estimator is OLS of the wedge on ``1/burn``
over the plant's own months; it is written down here BEFORE any arm exists and is
never swept — the number it returns is whatever the receipts say.

Forward analogue (rule 13's admissibility test): ``v[p]`` is a contractual /
physical attribute of the plant's delivery path, re-identified for a forecast
year from the then-current EIA-923 vintage exactly as it is here, and applied to
the forward hub.  It responds to changed conditions through the hub, which is
the point.

Zero-LP.  Reads only committed inputs.  Writes ``_miso225_transport_id.json``.

Usage:  PYTHONPATH=src python3 scripts/probes/_miso225_transport_identification_phase0.py
"""

from __future__ import annotations

import json
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
OUT = ROOT / "results/calibration/_miso225_transport_id.json"

YEARS = (2023, 2024, 2025)  # rule 22 [R-HOLDOUT]: training tier only.
# A plant-month is admissible for the regression only with a real, positive
# print and a real burn; the identification needs SPREAD in burn to separate the
# intercept from the slope, so a plant qualifies for its OWN v only with enough
# months and enough spread.  Both bars are declared here, before any result.
MIN_MONTHS = 12
MIN_BURN_SPREAD = 2.0  # max(burn) / min(burn)

GAS_GROUPS = ("CC_", "CT_", "ST_GAS", "ST_CHP", "CC_CHP")


def _hub_month_means() -> dict[tuple[str, int, int], float]:
    """Return ``{(kind, year, month): mean daily hub $/MMBtu}`` for both hubs.

    The daily staircases are the SAME objects
    :func:`~market_sim.data.fuel.basis.miso.apply_miso_gas_marginal_commodity`
    prices the arm's gas rows from — Chicago on its gas FLOW day, Henry on its
    trade day — so the wedge is measured against the very series the arm would
    use, not a monthly proxy for it.
    """
    out: dict[tuple[str, int, int], float] = {}
    chi_all = _miso_citygate_daily_dated(None)
    hh_all = _henry_hub_daily_dated(None)
    for year in YEARS:
        chi = _flow_date_staircase(chi_all.get(year, {}), year)
        hh = _trade_date_staircase(hh_all.get(year, {}), year)
        for kind, arr in (("chicago", chi), ("henry", hh)):
            if arr is None:
                continue
            vals = np.asarray(arr, dtype=float)
            # The MISO staircases are DAILY (365/366); the hourly form is the
            # fuel array's, not the hub series'.  Detect rather than assume.
            freq = "D" if len(vals) <= 366 else "h"
            idx = pd.date_range(f"{year}-01-01", periods=len(vals), freq=freq)
            s = pd.Series(vals, index=idx)
            for month, grp in s.groupby(s.index.month):
                out[(kind, year, int(month))] = float(grp.mean())
    return out


def _fit(wedge: np.ndarray, burn: np.ndarray) -> tuple[float, float, float]:
    """OLS ``wedge = v + F * (1/burn)``; return ``(v, F, r2)``."""
    x = 1.0 / burn
    A = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(A, wedge, rcond=None)
    pred = A @ coef
    ss_res = float(((wedge - pred) ** 2).sum())
    ss_tot = float(((wedge - wedge.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return float(coef[0]), float(coef[1]), r2


def main() -> None:
    bins = pd.read_csv(BINS)
    gas = bins[bins["Plant_Group"].astype(str).str.startswith(GAS_GROUPS)].copy()
    zone_kind = _miso_zone_hub_kind(YEARS[0])
    gas["hub_kind"] = gas["Zone"].map(zone_kind).fillna("chicago")

    f923 = pd.read_parquet(F923)
    f923 = f923[
        (f923["fuel_group"] == "Natural Gas")
        & (f923["year"].isin(YEARS))
        & (f923["quantity"] > 0)
        & (f923["price_per_mmbtu"] > 0)
    ]

    hub = _hub_month_means()
    rows = []
    for r in gas.itertuples():
        sub = f923[f923["plant_id"] == int(r.Plant_Code)]
        for m in sub.itertuples():
            h = hub.get((r.hub_kind, int(m.year), int(m.month)))
            if h is None:
                continue
            rows.append(
                {
                    "plant_id": int(r.Plant_Code),
                    "plant_name": str(r.Plant_Name),
                    "group": str(r.Plant_Group),
                    "zone": str(r.Zone),
                    "hub_kind": r.hub_kind,
                    "mw": float(r.Nameplate_MW),
                    "year": int(m.year),
                    "month": int(m.month),
                    "print": float(m.price_per_mmbtu),
                    "burn": float(m.quantity),
                    "hub": h,
                    "wedge": float(m.price_per_mmbtu) - h,
                }
            )
    panel = pd.DataFrame(rows)

    per_plant = []
    for pid, grp in panel.groupby("plant_id"):
        burn = grp["burn"].to_numpy(float)
        wedge = grp["wedge"].to_numpy(float)
        spread = float(burn.max() / burn.min()) if burn.min() > 0 else float("inf")
        rec = {
            "plant_id": int(pid),
            "plant_name": grp["plant_name"].iloc[0],
            "group": grp["group"].iloc[0],
            "zone": grp["zone"].iloc[0],
            "mw": float(grp["mw"].iloc[0]),
            "n_months": int(len(grp)),
            "burn_spread": spread,
            "mean_wedge": float(wedge.mean()),
            "identified": bool(len(grp) >= MIN_MONTHS and spread >= MIN_BURN_SPREAD),
        }
        if rec["identified"]:
            v, F, r2 = _fit(wedge, burn)
            rec.update(v_usd_mmbtu=v, fixed_usd_month=F, r2=r2)
        per_plant.append(rec)
    pp = pd.DataFrame(per_plant)

    ident = pp[pp["identified"]].copy()
    w = ident["mw"].to_numpy(float)
    v = ident["v_usd_mmbtu"].to_numpy(float)

    def q(a, p):
        return float(np.percentile(a, p)) if len(a) else float("nan")

    # Pooled fallbacks, same estimator, for plants that cannot carry their own v.
    pooled = {}
    for key, grp in panel.groupby(["zone", "group"]):
        if len(grp) >= MIN_MONTHS:
            vv, FF, rr = _fit(grp["wedge"].to_numpy(float), grp["burn"].to_numpy(float))
            pooled[f"{key[0]}|{key[1]}"] = {"v": vv, "fixed": FF, "r2": rr, "n": int(len(grp))}
    v_all, F_all, r2_all = _fit(panel["wedge"].to_numpy(float), panel["burn"].to_numpy(float))

    out = {
        "generated_by": "scripts/probes/_miso225_transport_identification_phase0.py",
        "years": list(YEARS),
        "bars": {"min_months": MIN_MONTHS, "min_burn_spread": MIN_BURN_SPREAD},
        "panel": {
            "n_plant_months": int(len(panel)),
            "n_plants": int(panel["plant_id"].nunique()),
            "mean_wedge_usd_mmbtu": float(panel["wedge"].mean()),
            "burn_weighted_mean_wedge": float(
                (panel["wedge"] * panel["burn"]).sum() / panel["burn"].sum()
            ),
        },
        "identified": {
            "n_plants": int(len(ident)),
            "mw": float(w.sum()),
            "mw_share_of_gas_fleet": float(w.sum() / pp["mw"].sum()),
            "v_cap_weighted": float((v * w).sum() / w.sum()) if len(v) else float("nan"),
            "v_p10": q(v, 10),
            "v_p50": q(v, 50),
            "v_p90": q(v, 90),
            "v_share_negative": float((v < 0).mean()) if len(v) else float("nan"),
            "median_r2": float(np.nanmedian(ident["r2"].to_numpy(float))),
            "fixed_usd_month_p50": q(ident["fixed_usd_month"].to_numpy(float), 50),
        },
        "pooled_zone_group": pooled,
        "pooled_miso_wide": {"v": v_all, "fixed": F_all, "r2": r2_all, "n": int(len(panel))},
        "per_plant": pp.sort_values("mw", ascending=False).to_dict("records"),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=float))
    print(json.dumps({k: out[k] for k in ("panel", "identified", "pooled_miso_wide")}, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

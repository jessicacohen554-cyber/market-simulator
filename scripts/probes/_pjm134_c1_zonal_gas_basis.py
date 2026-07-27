"""pjm-134 C1 (no LP): does the model's PJM zonal gas-basis ranking invert the measured one?

ASK-pjm134 §4 candidate C1. The pjm-121/129/133 keeper lineage runs
``pjm_zonal_gas_basis``, whose committed table
(``data/raw/pjm_zonal_gas_hub.csv``) prices each PJM zone's gas off its
**primary state's** EIA delivered-to-electric-power series (N3045<ST>3M) minus
Henry Hub, then re-centres on a gas-capacity-weighted mean of zero
(:func:`market_sim.data.fuel.basis.meanzero._apply_meanzero_zonal_gas_basis`).

If Dominion's delivered gas sits above AEP_Ohio's and ComEd's in the model by
more than it does in the measurement, Dominion's CT/CC sit behind theirs in
merit order in every hour -- which is the observed allocation inversion.

The comparator is EIA-923 Schedule 2 **plant-level** delivered natural-gas
receipts (``eia923_monthly_fuel_costs.parquet``), volume-weighted over the
plants the model itself places in each zone (``build_zone_lookup("PJM")``).
That is the same measured quantity on the model's own boundary rather than on
the state boundary -- rule 14's misalignment question asked directly.

No LP is solved and nothing is written outside ``results/probes/``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.data.eia923 import EIA923_MONTHLY_COSTS_PATH
from market_sim.data.fuel.basis.meanzero import PJM_ZONAL_GAS_HUB_PATH
from market_sim.data.zone_assignment import build_zone_lookup
from market_sim.config.paths import RAW_DATA_DIR


YEARS = (2023, 2024, 2025)

# The three zones ASK-pjm134 §2 measures the inversion across. Dominion is the
# under-running zone; AEP_Ohio and ComEd carry the offsetting over-run.
FOCUS = ("PJM_Dominion", "PJM_AEP_Ohio", "PJM_ComEd")

# Representative PJM peaker heat rate (MMBtu/MWh) used only to translate a
# $/MMBtu fuel spread into the $/MWh merit-order offset it produces. Not a
# model input -- a unit conversion for the report. EIA-860/923 PJM GT fleet
# average full-load heat rate is ~10.5 MMBtu/MWh.
CT_HEAT_RATE_MMBTU_PER_MWH = 10.5

# Same, for a PJM combined cycle.
CC_HEAT_RATE_MMBTU_PER_MWH = 7.0

OUT_PATH = Path("results/probes/pjm134_c1_zonal_gas_basis.json")


def _model_basis() -> pd.DataFrame:
    """Return the committed model per-zone basis vs Henry Hub ($/MMBtu)."""
    frame = pd.read_csv(PJM_ZONAL_GAS_HUB_PATH)
    frame = frame[frame["year"].isin(YEARS)]
    return frame[["zone", "year", "basis_vs_hh_usd_mmbtu", "hub"]].reset_index(
        drop=True
    )


def _henry_hub() -> pd.DataFrame:
    """Return monthly Henry Hub spot ($/MMBtu) for the scored years."""
    hh = pd.read_csv(RAW_DATA_DIR / "gas-prices" / "henry_hub_monthly.csv")
    hh = hh[hh["year"].isin(YEARS)]
    return hh.rename(columns={"price_usd_mmbtu": "hh"})[["year", "month", "hh"]]


def _measured_zone_gas() -> pd.DataFrame:
    """Volume-weighted F923 delivered gas price per (PJM zone, year, month).

    Restricted to plants the model's own ``build_zone_lookup`` places in a PJM
    zone, so the aggregation boundary is the model's zone, not the state.
    """
    costs = pd.read_parquet(EIA923_MONTHLY_COSTS_PATH)
    costs = costs[
        (costs["fuel_group"] == "Natural Gas") & (costs["year"].isin(YEARS))
    ].copy()
    lookup = build_zone_lookup("PJM")
    costs["zone"] = costs["plant_id"].map(lookup)
    costs = costs[costs["zone"].notna()]
    costs = costs[(costs["quantity"] > 0) & (costs["price_per_mmbtu"] > 0)]

    def _vw(group: pd.DataFrame) -> pd.Series:
        q = group["quantity"].to_numpy(dtype=float)
        p = group["price_per_mmbtu"].to_numpy(dtype=float)
        return pd.Series(
            {
                "price": float((p * q).sum() / q.sum()),
                "mmbtu": float(q.sum()),
                "n_plants": int(group["plant_id"].nunique()),
            }
        )

    monthly = (
        costs.groupby(["zone", "year", "month"], as_index=False)
        .apply(_vw, include_groups=False)
        .reset_index(drop=True)
    )
    return monthly


def _annualise(monthly: pd.DataFrame, hh: pd.DataFrame) -> pd.DataFrame:
    """Volume-weight the monthly measured prices into a zone-year basis vs HH."""
    merged = monthly.merge(hh, on=["year", "month"], how="left")
    merged["basis_m"] = merged["price"] - merged["hh"]
    rows = []
    for (zone, year), grp in merged.groupby(["zone", "year"]):
        w = grp["mmbtu"].to_numpy(dtype=float)
        rows.append(
            {
                "zone": zone,
                "year": int(year),
                "measured_price": float((grp["price"] * w).sum() / w.sum()),
                "measured_basis": float((grp["basis_m"] * w).sum() / w.sum()),
                "mmbtu": float(w.sum()),
                "months_covered": int(grp["month"].nunique()),
                "n_plants_max": int(grp["n_plants"].max()),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    """Run the C1 measurement and write the machine-readable verdict."""
    model = _model_basis()
    hh = _henry_hub()
    monthly = _measured_zone_gas()
    measured = _annualise(monthly, hh)

    merged = model.merge(measured, on=["zone", "year"], how="outer")
    merged = merged.sort_values(["year", "zone"]).reset_index(drop=True)

    print("=" * 100)
    print("C1 -- PJM zonal gas basis vs Henry Hub ($/MMBtu): model table vs F923")
    print("     measured = EIA-923 Sch.2 plant receipts, volume-weighted over the")
    print("     plants build_zone_lookup('PJM') places in each zone")
    print("=" * 100)
    for year in YEARS:
        sub = merged[merged["year"] == year]
        print(f"\n--- {year} ---")
        print(
            f"{'zone':<16}{'model':>9}{'measured':>10}{'model-meas':>12}"
            f"{'mmbtu(M)':>11}{'plants':>8}{'mo':>4}"
        )
        for r in sub.itertuples():
            mb = r.basis_vs_hh_usd_mmbtu
            xb = r.measured_basis
            diff = mb - xb if pd.notna(xb) else float("nan")
            mm = r.mmbtu / 1e6 if pd.notna(r.mmbtu) else float("nan")
            npl = int(r.n_plants_max) if pd.notna(r.n_plants_max) else 0
            nmo = int(r.months_covered) if pd.notna(r.months_covered) else 0
            xb = xb if pd.notna(xb) else float("nan")
            print(
                f"{r.zone:<16}{mb:>9.3f}{xb:>10.3f}{diff:>12.3f}"
                f"{mm:>11.1f}{npl:>8}{nmo:>4}"
            )

    # --- the ranking test -------------------------------------------------
    print("\n" + "=" * 100)
    print("C1 RANKING TEST -- Dominion vs the two over-running western zones")
    print("  positive = Dominion gas is DEARER (its units sit further back in merit)")
    print("=" * 100)
    verdict: dict[str, object] = {"years": {}}
    fires = []
    for year in YEARS:
        sub = merged[merged["year"] == year].set_index("zone")
        row: dict[str, object] = {}
        print(f"\n--- {year} ---")
        for other in ("PJM_AEP_Ohio", "PJM_ComEd"):
            m_spread = float(
                sub.loc["PJM_Dominion", "basis_vs_hh_usd_mmbtu"]
                - sub.loc[other, "basis_vs_hh_usd_mmbtu"]
            )
            x_spread = float(
                sub.loc["PJM_Dominion", "measured_basis"]
                - sub.loc[other, "measured_basis"]
            )
            over = m_spread - x_spread
            row[f"vs_{other}"] = {
                "model_spread_usd_mmbtu": round(m_spread, 4),
                "measured_spread_usd_mmbtu": round(x_spread, 4),
                "model_overstatement_usd_mmbtu": round(over, 4),
                "ct_usd_mwh": round(over * CT_HEAT_RATE_MMBTU_PER_MWH, 3),
                "cc_usd_mwh": round(over * CC_HEAT_RATE_MMBTU_PER_MWH, 3),
                "sign_inverted": bool(np.sign(m_spread) != np.sign(x_spread)),
            }
            print(
                f"  Dominion - {other:<14} model {m_spread:+.3f}  measured "
                f"{x_spread:+.3f}  model overstates by {over:+.3f} $/MMBtu"
                f"  = {over * CT_HEAT_RATE_MMBTU_PER_MWH:+.2f} $/MWh on a CT,"
                f" {over * CC_HEAT_RATE_MMBTU_PER_MWH:+.2f} on a CC"
            )
            fires.append(over)
        verdict["years"][str(year)] = row

    # --- ordinal rank of every zone, model vs measured ---------------------
    print("\n" + "=" * 100)
    print("C1 FULL-ZONE ORDINAL RANK (1 = cheapest gas)")
    print("=" * 100)
    rank_rows = {}
    for year in YEARS:
        sub = merged[merged["year"] == year].dropna(subset=["measured_basis"])
        mr = sub["basis_vs_hh_usd_mmbtu"].rank().astype(int)
        xr = sub["measured_basis"].rank().astype(int)
        tau = float(pd.Series(mr.to_numpy()).corr(pd.Series(xr.to_numpy()), method="kendall"))
        print(f"\n--- {year} --- Kendall tau(model rank, measured rank) = {tau:+.3f}")
        print(f"{'zone':<16}{'model rk':>10}{'meas rk':>9}{'delta':>7}")
        for zone, a, b in zip(sub["zone"], mr, xr):
            flag = "  <<<" if zone in FOCUS else ""
            print(f"{zone:<16}{a:>10}{b:>9}{a - b:>7}{flag}")
        rank_rows[str(year)] = {
            "kendall_tau": round(tau, 4),
            "model_rank": {z: int(a) for z, a in zip(sub["zone"], mr)},
            "measured_rank": {z: int(b) for z, b in zip(sub["zone"], xr)},
        }
    verdict["rank"] = rank_rows

    worst = max(abs(f) for f in fires)
    verdict["summary"] = {
        "max_abs_overstatement_usd_mmbtu": round(worst, 4),
        "max_ct_usd_mwh": round(worst * CT_HEAT_RATE_MMBTU_PER_MWH, 3),
        "n_sign_inversions": int(
            sum(
                1
                for y in verdict["years"].values()
                for v in y.values()
                if v["sign_inverted"]
            )
        ),
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(verdict, indent=1))
    print(f"\nwrote {OUT_PATH}")


if __name__ == "__main__":
    main()

"""FFR-7C: re-derive FFR-6A's exit decode on the CORRECTED retirement target.

Committed-artifact measurement only — this probe never solves, never touches a
model path, and writes nothing outside its own JSON.

FFR-6A (``docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md`` §3.3)
bounded ERCOT's true margin-driven exits at ~0 GW from a four-row decode of the
THEN-KNOWN 1.534 GW thermal target.  FFR-7A's corrected target
(``docs/handoffs/ffr-7a-scoring-target-hygiene-2026-08-06.md``) is *larger* —
2.294 GW — and contains +1.7 GW of physical exits that decode never saw.  This
probe re-runs the decode over every corrected-target ERCOT in-window thermal
exit >= 100 MW, on the same measured-price pro-forma, with per-unit heat rates.

Construction (pre-registered in
``docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md`` §1)::

    M_u(y) = sum_t max(0, p_t - mc_t) * (1 - outage) / 1000     [$/kW-yr]
    mc_t   = HR * fuel_t + VOM

``price_taker_net_revenue`` and ``SOM_OUTAGE_RATE`` are imported from the
standing SOM replica (``scripts/probes/fom_scarcity_revenue_audit.py``, itself
validated 0.89-0.97 against published Potomac-SOM net revenue) rather than
re-implemented — this extends that machinery, it does not fork it.

Usage::

    uv run python scripts/probes/ffr7c_exit_decode.py \\
        --out docs/handoffs/ffr-7c/exit-decode-2026-08-06.json
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
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from fom_scarcity_revenue_audit import (  # noqa: E402
    SOM_ASSUMPTIONS,
    SOM_OUTAGE_RATE,
    price_taker_net_revenue,
)

WINDOW = (2021, 2022, 2023, 2024, 2025)

# FFR-6A's replica levels for the two non-SOM classes, recovered exactly from
# its committed artifact (docs/handoffs/ffr-6a/measured-price-replica-
# 2026-08-06.txt) by inversion: the published coal column is reproduced to
# +-0.01 $/kW-yr in EVERY window year by a FLAT marginal cost of $23.18/MWh
# (the SOM-cited 2024 existing-coal mc, 2024 SOM pp.119-120), and the nuclear
# column by a flat $10.00/MWh. Held here as the reproduction gate for this
# session's arithmetic.
FFR6A_COAL_PROXY_MC: float = 23.18
FFR6A_NUCLEAR_PROXY_MC: float = 10.00
FFR6A_GAS_ST_PROXY = SOM_ASSUMPTIONS["gas_ct"]  # HR 10.5 / VOM 4.0, as FFR-6A used

# FFR-6A's published replica table — the gate this probe must reproduce.
FFR6A_REPLICA = {
    2021: {"gas_ct": 945.1, "gas_cc": 972.4, "coal": 1013.3, "nuclear": 1094.5},
    2022: {"gas_ct": 129.7, "gas_cc": 176.4, "coal": 321.7, "nuclear": 415.3},
    2023: {"gas_ct": 216.4, "gas_cc": 240.0, "coal": 234.1, "nuclear": 306.5},
    2024: {"gas_ct": 65.6, "gas_cc": 86.7, "coal": 75.4, "nuclear": 139.8},
    2025: {"gas_ct": 47.0, "gas_cc": 76.4, "coal": 97.2, "nuclear": 181.6},
}

# Shipped going-forward bars: fixed_om_<f> * retirement_fom_multiplier_<f>
# (ScenarioConfig defaults, unchanged in the FFR-5D arms' run_config).
BARS = {"coal": 45.0 * 1.3, "gas_cc": 30.0, "gas_ct": 21.0, "gas_st": 35.0, "oil": 25.0}

# Shipped execution lags (ScenarioConfig.retirement_execution_lag_*): the
# pipeline rule's decision (LOSS) year is exit_year - lag.
EXEC_LAG = {"coal": 3, "gas_ct": 2, "gas_cc": 1, "gas_st": 1, "oil": 1, "nuclear": 3}

THERMAL_FUELS = frozenset(
    {"coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear", "biomass"}
)
MIN_MW = 100.0

# CAMPD parasitic-load fractions by model plant group (data.campd
# DEFAULT_PARASITIC_LOAD_PCT) — net heat rate = gross / (1 - parasitic).
PARASITIC = {"COAL": 0.07, "ST_GAS": 0.05, "CC_CHP": 0.025, "CT_PEAKER": 0.01}

# Per-unit dossier: the physical class (independent of the target's taxonomy),
# its CAMPD key, its model bin, and the fuel basis to price it on.
UNITS = {
    "56611_S01": {
        "name": "Sandy Creek 1",
        "plant": 56611,
        "campd_unit": "S01",
        "physical_class": "coal",
        "bin": "SC_COAL3 (plant 56611, 936.0 MW, HR 9.50)",
        "parasitic_group": "COAL",
        "fuel": "prb",
        "bin_hr": 9.50,
    },
    "3612_2": {
        "name": "V H Braunig 2",
        "plant": 3612,
        "campd_unit": "2",
        "physical_class": "gas_st",
        "bin": "SC_STGAS3 (plant 3612, 1138.0 MW, HR 8.49)",
        "parasitic_group": "ST_GAS",
        "fuel": "gas",
        "bin_hr": 8.49,
    },
    "3612_1": {
        "name": "V H Braunig 1",
        "plant": 3612,
        "campd_unit": "1",
        "physical_class": "gas_st",
        "bin": "SC_STGAS3 (plant 3612, 1138.0 MW, HR 8.49)",
        "parasitic_group": "ST_GAS",
        "fuel": "gas",
        "bin_hr": 8.49,
    },
    "52120_G-66": {
        "name": "Freeport Energy G-66",
        "plant": 52120,
        "campd_unit": None,  # not a CAMPD reporter (industrial CHP)
        "physical_class": "gas_cc",
        "bin": "H_CHP2 (plant 52120, 419.3 MW, HR 5.86, class CC_CHP)",
        "parasitic_group": "CC_CHP",
        "fuel": "gas",
        "bin_hr": 5.86,
    },
    "3548_2": {
        "name": "Decker Creek 2",
        "plant": 3548,
        "campd_unit": "2",
        "physical_class": "gas_st",
        "bin": "ABSENT (3548 carries only CT8, CT_PEAKER 206.0 MW)",
        "parasitic_group": "ST_GAS",
        "fuel": "gas",
        "bin_hr": None,  # the bin sheet's 13.44 is the CT_PEAKER block, not unit 2
    },
}

# constants.VOM, by physical class.
VOM = {"coal": 4.5, "gas_cc": 2.0, "gas_ct": 3.5, "gas_st": 4.0, "oil": 4.5}

# EIA natural-gas heat content, data.fuel.basis.ercot._MCF_TO_MMBTU.
MCF_TO_MMBTU = 1.036
# South_Central zonal gas basis vs Henry Hub, data/raw/ercot_zonal_gas_hub.csv
# (all five units sit in the model's South_Central zone).
SOUTH_CENTRAL_BASIS = {
    2021: 6.30,
    2022: 0.36,
    2023: 0.56,
    2024: 0.45,
    2025: -0.12,
}


# --------------------------------------------------------------------------- #
# Measured series
# --------------------------------------------------------------------------- #
def rt_prices(year: int) -> np.ndarray:
    """Measured ERCOT hourly RT hub price ($/MWh) for one year, (8760,)."""
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    rt = lmp.loc[lmp["year"] == year].sort_values("hour")["rt"].to_numpy()
    assert rt.size == 8760, f"{year}: {rt.size} hours"
    return rt


def henry_hub_hourly(year: int) -> np.ndarray:
    """Daily Henry Hub ($/MMBtu) broadcast to (8760,) — FFR-6A's gas basis."""
    hh = pd.read_csv(REPO / "data/raw/gas-prices/henry_hub_daily.csv")
    hh["date"] = pd.to_datetime(hh["date"])
    days = pd.date_range(f"{year}-01-01", periods=366, freq="D")
    s = hh.set_index("date")["price_usd_mmbtu"].reindex(days).ffill().bfill()
    return s.to_numpy()[np.arange(8760) // 24]


def ercot_delivered_gas_hourly(year: int) -> np.ndarray:
    """Measured TX electric-power delivered gas + South_Central basis, (8760,).

    EIA series N3045TX3 ($/Mcf monthly, the *power-plant* delivered level, not
    city gate) converted at 1.036 MMBtu/Mcf, plus the zone's own annual basis
    from ``ercot_zonal_gas_hub.csv``. The repo's own ERCOT delivered-gas anchor
    (``data.fuel.basis.ercot``); used here only as a sensitivity column.
    """
    ep = pd.read_csv(REPO / "data/raw/ercot_electric_power_gas_price.csv")
    yr = ep[ep["year"] == year].set_index("month")["price_usd_mcf"]
    monthly = np.array(
        [float(yr.get(m, np.nan)) / MCF_TO_MMBTU for m in range(1, 13)], dtype=float
    )
    if np.isnan(monthly).all():
        return np.full(8760, np.nan)
    monthly[np.isnan(monthly)] = np.nanmean(monthly)
    hours_per_month = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    hours_per_month[-1] += 8760 - hours_per_month.sum()
    return np.repeat(monthly, hours_per_month)


def prb_hourly(year: int) -> np.ndarray:
    """Measured delivered PRB coal ($/MMBtu) broadcast to (8760,).

    ``data.fuel.coal._prb_monthly_actuals`` — the quantity-weighted EIA-923
    receipts of the ERCOT PRB-by-rail reporters (Fayette, J K Spruce). This is
    exactly the series the model prices non-reporting PRB plants on, and Sandy
    Creek (plant 56611, ``COAL_PLANT_SUPPLY[56611] == "prb"``) files no
    receipts of its own.
    """
    from market_sim.data.fuel.coal import _prb_monthly_actuals

    monthly = _prb_monthly_actuals().get(year)
    if monthly is None:
        return np.full(8760, np.nan)
    hours_per_month = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]) * 24
    hours_per_month[-1] += 8760 - hours_per_month.sum()
    return np.repeat(np.asarray(monthly, dtype=float), hours_per_month)


def campd_unit_year(plant: int, unit: str, year: int) -> dict | None:
    """Return measured ``{gross_hr, gross_mwh, op_hours}`` for one unit-year."""
    path = REPO / f"data/raw/campd-unit-level/TX_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(
        path, columns=["facilityId", "unitId", "grossLoad", "heatInput", "opTime"]
    )
    sub = df[
        (df["facilityId"].astype("int64") == plant)
        & (df["unitId"].astype(str) == str(unit))
    ]
    if sub.empty:
        return None
    gl = float(np.nansum(sub["grossLoad"]))
    hi = float(np.nansum(sub["heatInput"]))
    if gl <= 0.0:
        return None
    return {
        "gross_hr": hi / gl,
        "gross_mwh": gl,
        "op_hours": float(np.nansum(sub["opTime"])),
    }


# --------------------------------------------------------------------------- #
# The decode
# --------------------------------------------------------------------------- #
def reproduction_gate() -> dict:
    """Reproduce FFR-6A's published replica table; abort the run on a miss."""
    rows = {}
    for year in WINDOW:
        rt, hh = rt_prices(year), henry_hub_hourly(year)
        got = {
            "gas_ct": price_taker_net_revenue(rt, hh, 10.5, 4.0),
            "gas_cc": price_taker_net_revenue(rt, hh, 7.0, 4.0),
            "coal": price_taker_net_revenue(
                rt, np.zeros(8760), 0.0, FFR6A_COAL_PROXY_MC
            ),
            "nuclear": price_taker_net_revenue(
                rt, np.zeros(8760), 0.0, FFR6A_NUCLEAR_PROXY_MC
            ),
        }
        want = FFR6A_REPLICA[year]
        rows[year] = {
            k: {"ffr7c": round(v, 1), "ffr6a": want[k], "delta": round(v - want[k], 2)}
            for k, v in got.items()
        }
        for k, v in got.items():
            if abs(v - want[k]) > 0.06:
                raise SystemExit(
                    f"REPRODUCTION GATE FAILED {year} {k}: {v:.2f} vs {want[k]}"
                )
    return rows


def target_units() -> pd.DataFrame:
    """The pre-registered unit list, straight off the committed target CSV."""
    df = pd.read_csv(
        REPO / "data/raw/_validation-source/capacity_actuals_ercot.csv", comment="#"
    )
    df["mw"] = df["mw"].astype(float)
    df["year"] = df["year"].astype(int)
    sel = df[
        (df["kind"] == "retirement")
        & df["fuel"].isin(THERMAL_FUELS)
        & (df["mw"] >= MIN_MW)
        & df["year"].between(min(WINDOW), max(WINDOW))
    ]
    return sel.sort_values("mw", ascending=False).reset_index(drop=True)


def unit_margins(unit_id: str, dossier: dict) -> dict:
    """Per-year measured-price margins for one unit, all variants."""
    out: dict[int, dict] = {}
    for year in WINDOW:
        rt = rt_prices(year)
        cls = dossier["physical_class"]
        vom = VOM[cls]
        campd = (
            campd_unit_year(dossier["plant"], dossier["campd_unit"], year)
            if dossier["campd_unit"]
            else None
        )
        row: dict = {"campd": campd}

        if dossier["fuel"] == "gas":
            fuel_primary = henry_hub_hourly(year)
            fuel_sens = ercot_delivered_gas_hourly(year) + SOUTH_CENTRAL_BASIS[year]
        else:
            fuel_primary = prb_hourly(year)
            from market_sim.config.constants import PRB_PRICE_BY_YEAR

            lvl = PRB_PRICE_BY_YEAR.get(year)
            fuel_sens = (
                np.full(8760, float(lvl)) if lvl is not None else np.full(8760, np.nan)
            )

        # (i) FFR-6A class proxy
        if cls == "coal":
            row["class_proxy"] = price_taker_net_revenue(
                rt, np.zeros(8760), 0.0, FFR6A_COAL_PROXY_MC
            )
        elif cls == "gas_cc":
            row["class_proxy"] = price_taker_net_revenue(rt, fuel_primary, 7.0, 4.0)
        else:  # gas_st / gas_ct both use FFR-6A's HR 10.5 proxy
            row["class_proxy"] = price_taker_net_revenue(rt, fuel_primary, 10.5, 4.0)

        # (iii) the MODEL's own carried heat rate for the unit's bin
        # (custom-bin-assignments.csv ``Plant_Avg_HR_MMBtu_MWh``) — what the
        # shipped screen would price this capacity at, at measured prices.
        if dossier.get("bin_hr"):
            row["bin_hr"] = float(dossier["bin_hr"])
            row["model_bin_hr"] = price_taker_net_revenue(
                rt, fuel_primary, float(dossier["bin_hr"]), vom
            )

        # (ii) unit-measured heat rate, gross and net-adjusted
        if campd:
            gross_hr = campd["gross_hr"]
            net_hr = gross_hr / (1.0 - PARASITIC[dossier["parasitic_group"]])
            row["hr_gross"] = gross_hr
            row["hr_net"] = net_hr
            row["unit_gross"] = price_taker_net_revenue(rt, fuel_primary, gross_hr, vom)
            row["unit_net"] = price_taker_net_revenue(rt, fuel_primary, net_hr, vom)
            if not np.isnan(fuel_sens).all():
                row["unit_net_fuel_sens"] = price_taker_net_revenue(
                    rt, fuel_sens, net_hr, vom
                )
        out[year] = {
            k: (round(v, 2) if isinstance(v, float) else v) for k, v in row.items()
        }
    return out


def main(argv: list[str] | None = None) -> int:
    """Run the reproduction gate, then decode every pre-registered unit."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default=None, help="JSON output path.")
    args = p.parse_args(argv)

    gate = reproduction_gate()
    print("REPRODUCTION GATE: PASS (FFR-6A replica reproduced in all 5 window years)")

    sel = target_units()
    print(f"\nPre-registered unit list: {len(sel)} units / {sel['mw'].sum():.1f} MW\n")

    payload: dict = {
        "reproduction_gate": {str(y): v for y, v in gate.items()},
        "bars": BARS,
        "exec_lag": EXEC_LAG,
        "outage_rate": SOM_OUTAGE_RATE,
        "units": {},
    }

    for _, r in sel.iterrows():
        uid = str(r["unit_id"])
        dossier = UNITS[uid]
        exit_year = int(r["year"])
        target_fuel = str(r["fuel"])
        phys = dossier["physical_class"]
        margins = unit_margins(uid, dossier)

        bar_target = BARS[target_fuel]
        bar_phys = BARS[phys]
        lag_target = EXEC_LAG[target_fuel]
        lag_phys = EXEC_LAG[phys]

        def adj(y: int) -> float | None:
            """The adjudicating margin: unit-measured net HR, else class proxy."""
            row = margins.get(y, {})
            return row.get("unit_net", row.get("class_proxy"))

        prim_year = exit_year - 1
        prim = adj(prim_year)
        verdict_t = None if prim is None else bool(prim < bar_target)
        verdict_p = None if prim is None else bool(prim < bar_phys)

        payload["units"][uid] = {
            "name": dossier["name"],
            "plant": dossier["plant"],
            "mw": float(r["mw"]),
            "exit_year": exit_year,
            "target_fuel": target_fuel,
            "physical_class": phys,
            "model_bin": dossier["bin"],
            "bar_target_taxonomy": bar_target,
            "bar_physical_class": bar_phys,
            "primary_year": prim_year,
            "primary_margin": prim,
            "primary_margin_basis": (
                "unit_net"
                if margins.get(prim_year, {}).get("unit_net")
                else "class_proxy"
            ),
            "economically_consistent_target_bar": verdict_t,
            "economically_consistent_physical_bar": verdict_p,
            "bar_invariant": verdict_t == verdict_p,
            "loss_year_target_lag": exit_year - lag_target,
            "loss_year_physical_lag": exit_year - lag_phys,
            "loss_year_margin_target_lag": adj(exit_year - lag_target),
            "loss_year_margin_physical_lag": adj(exit_year - lag_phys),
            "margins_by_year": {str(y): v for y, v in margins.items()},
        }

        m = payload["units"][uid]
        print(
            f"{uid:12s} {dossier['name']:22s} {r['mw']:7.1f} MW  exit {exit_year}  "
            f"{target_fuel}/{phys}"
        )
        print(
            f"             margin({prim_year}) = "
            f"{prim if prim is None else round(prim, 1)} $/kW-yr  vs bar "
            f"{bar_target} (target) / {bar_phys} (physical)  -> "
            f"{'MARGIN-CONSISTENT EXIT' if verdict_t else 'clears (NOT margin-driven)'}"
            f"{'' if m['bar_invariant'] else '  [SEAM-DEPENDENT]'}"
        )

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(payload, indent=1))
        print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

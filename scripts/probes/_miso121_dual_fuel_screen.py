#!/usr/bin/env python
"""miso-121 Phase 0 — ``dual_fuel_switching`` measured identification screen (no LP).

Runs the four legs pre-registered in
``results/calibration/PREREG-miso121-dual-fuel-switching-2026-08-03.md`` §4 and
evaluates the inertness routes / LIVE bars fixed in its §5, on MISO's own data
and the keeper's own reconstruction. **No LP solve anywhere in this file.**

Legs
----
A  CAPABILITY      EIA-860 Multifuel switch-capable ``(plant_code, plant_group)``
                   pairs intersected with the keeper's own MISO fleet.
B  SWITCH PRICE    Measured MISO-month EIA-923 (F923) Schedule 5 Petroleum
                   receipt cost; measured months vs national-constant fallback.
C  BINDING         The keeper's own resolved ``(n_gen, T)`` gas price array
                   (pre-``min``) against the delivered oil series — exactly
                   ``dual_fuel_switch_mask``'s comparison. ``max Δ_fuel ≤ 0``
                   makes the mechanism's ``min()`` the identity map.
D  OBSERVABILITY   Do MISO's own in-window winters show the switch in CAMPD?
                   Tested TWO ways: the reported fuel label, and the physical
                   CO2-per-MMBtu signature (pipeline gas ~53 vs distillate
                   ~73 kg/MMBtu) which is the stronger of the two.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only. Elliott (Dec 2022) is out of scope and
is never read. Rule 23 ``[R-FROZEN-DERIVE]``: nothing here is fitted or swept —
every quantity is read from measured registries.

Usage::

    uv run python scripts/probes/_miso121_dual_fuel_screen.py \
        --json results/calibration/_miso121_dual_fuel_screen.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from market_sim.config.constants import OIL_PRICE_PER_MMBTU  # noqa: E402
from market_sim.data.fleet.eia860 import dual_fuel_plant_groups  # noqa: E402
from market_sim.data.fuel._shared import _GAS_FUEL_IDX  # noqa: E402
from market_sim.data.fuel.dual_fuel import dual_fuel_oil_price_series  # noqa: E402
from market_sim.data.fuel.plant_prices import iso_monthly_oil_prices  # noqa: E402
from market_sim.data.fuel.resolve import resolve_fuel_prices  # noqa: E402
from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "miso117_ctheatrate_B"
CAMPD_UNIT_DIR = REPO / "data" / "raw" / "campd-unit-level"

#: PREREG §5 bands. Fixed before any measurement; never edited after.
BAR_CAPABLE_MW = 500.0
BAR_CAPABLE_SHARE = 0.01
BAR_MEASURED_MONTH_FRAC = 0.50
BAR_BINDING_GENHOURS = 100
BAR_BYTE_IDENTITY = 1e-9
BAR_MARGINAL_P50_DOFFER = 0.10

#: Winter months inside the rule-22 window. December is the *same* calendar
#: year's December (2023/2024/2025) — Dec-2022 (Elliott) is never read.
WINTER_MONTHS = (1, 2, 12)

#: Physical CO2 intensity separating pipeline gas from distillate/residual oil
#: (EPA 40 CFR 98 Table C-1: pipeline natural gas 53.06, distillate no. 2
#: 73.96, residual no. 6 75.10 kg CO2/MMBtu). The midpoint threshold below is a
#: FUEL-IDENTIFICATION cut from published emission factors, not a fitted value.
CO2_KG_PER_MMBTU_GAS = 53.06
CO2_KG_PER_MMBTU_DISTILLATE = 73.96
#: The distillate/residual identification BAND. Bounded ABOVE as well as below,
#: because coal (bituminous 93.28 / subbituminous 97.17 kg/MMBtu) sits above
#: oil, not below it — an open-ended ">= threshold" test books coal as oil.
CO2_RATE_OIL_BAND_LO = 70.0
CO2_RATE_OIL_BAND_HI = 80.0
SHORT_TON_KG = 907.18474

#: CAMPD ``primaryFuelInfo`` labels. The mechanism acts on gas-primary units
#: only; the diesel-labelled units are an internal control on the band.
_GAS_LABELS = ("Pipeline Natural Gas", "Natural Gas")
_OIL_LABELS = ("Diesel Oil", "Residual Oil")


def leg_a_capability(fleet, capable: frozenset) -> dict:
    """Leg A — capable tranche census on the keeper's own fleet."""
    groups = fleet.plant_group
    is_gas = np.isin(fleet.fuel_type_idx, _GAS_FUEL_IDX)
    gas_rows = np.nonzero(is_gas)[0]
    capable_rows = [
        int(g)
        for g in gas_rows
        if (int(fleet.plant_code[g]), str(groups[g])) in capable
    ]
    pmax = np.asarray(fleet.pmax, dtype=float)
    capable_mw = float(pmax[capable_rows].sum()) if capable_rows else 0.0
    gas_mw = float(pmax[gas_rows].sum())
    roster: dict[int, dict] = {}
    for g in capable_rows:
        code = int(fleet.plant_code[g])
        row = roster.setdefault(code, {"mw": 0.0, "groups": set(), "tranches": 0})
        row["mw"] += float(pmax[g])
        row["groups"].add(str(groups[g]))
        row["tranches"] += 1
    return {
        "capable_rows": capable_rows,
        "n_capable_tranches": len(capable_rows),
        "n_capable_plants": len(roster),
        "capable_mw": capable_mw,
        "gas_mw": gas_mw,
        "capable_share_of_gas": (capable_mw / gas_mw) if gas_mw > 0 else 0.0,
        "roster": {
            str(k): {
                "mw": round(v["mw"], 1),
                "groups": sorted(v["groups"]),
                "tranches": v["tranches"],
            }
            for k, v in sorted(roster.items(), key=lambda kv: -kv[1]["mw"])
        },
    }


def leg_b_switch_price(config, year: int) -> dict:
    """Leg B — measured MISO F923 Petroleum receipts vs the national fallback."""
    monthly = iso_monthly_oil_prices(config, year)
    if monthly is None:
        return {
            "series_present": False,
            "n_measured_months": 0,
            "n_months": 12,
            "monthly_usd_mmbtu": None,
            "fallback_usd_mmbtu": OIL_PRICE_PER_MMBTU,
        }
    arr = np.asarray(monthly, dtype=float)
    measured = ~np.isnan(arr)
    return {
        "series_present": True,
        "n_measured_months": int(measured.sum()),
        "n_months": int(arr.size),
        "monthly_usd_mmbtu": [None if np.isnan(v) else round(float(v), 4) for v in arr],
        "measured_mean_usd_mmbtu": (
            round(float(np.nanmean(arr)), 4) if measured.any() else None
        ),
        "measured_min_usd_mmbtu": (
            round(float(np.nanmin(arr)), 4) if measured.any() else None
        ),
        "fallback_usd_mmbtu": OIL_PRICE_PER_MMBTU,
    }


def leg_c_binding(state, config, year: int, capable_rows: list[int]) -> dict:
    """Leg C — the arithmetic binding test on the keeper's own price array.

    Resolves the keeper's delivered fuel-price array at HEAD. The keeper runs
    ``dual_fuel_switching=False``, so the array returned is exactly the
    **pre-``min``** gas price the mechanism would cap.
    """
    fleet = state["fleet_arrays"]
    prices = resolve_fuel_prices(config, fleet, year)
    oil_hourly = dual_fuel_oil_price_series(config, year)
    if not capable_rows:
        return {
            "max_delta_fuel": None,
            "n_binding_genhours": 0,
            "note": "no capable row in fleet",
        }
    gas = prices[np.asarray(capable_rows, dtype=int), :]
    delta = gas - oil_hourly[None, :]
    binding = delta > 0.0
    heat = np.asarray(fleet.heat_rate, dtype=float)[np.asarray(capable_rows)]
    out: dict = {
        "max_delta_fuel": float(delta.max()),
        "max_gas_price": float(gas.max()),
        "capable_gas_mean": float(gas.mean()),
        "oil_min": float(oil_hourly.min()),
        "oil_mean": float(oil_hourly.mean()),
        "n_binding_genhours": int(binding.sum()),
        "n_capable_genhours": int(delta.size),
        "headroom_to_parity_min": float((-delta).min()),
    }
    if binding.any():
        doffer = (delta * heat[:, None])[binding]
        out["binding_doffer_max"] = float(doffer.max())
        out["binding_doffer_p50"] = float(np.percentile(doffer, 50))
        out["binding_doffer_p95"] = float(np.percentile(doffer, 95))
    return out


def _miso_plant_codes() -> frozenset[int]:
    """MISO plant codes from the model's own zone lookup."""
    from market_sim.data.zone_assignment import build_zone_lookup

    return frozenset(int(p) for p in build_zone_lookup(ISO))


def leg_d_observability(capable_plants: set[int], years=YEARS) -> dict:
    """Leg D — is a fuel switch observable in MISO's own CAMPD feed?

    Two independent tests, the second strictly stronger than the pre-registered
    minimum:

    * **D1 label** — does the hourly ``primaryFuelInfo`` field ever vary within
      a unit-year? (In CAMPD it is a static unit attribute, so a switch cannot
      be read off the label.)
    * **D2 CO2 signature** — does a capable unit's measured
      ``co2Mass / heatInput`` ever cross the published gas/distillate
      identification threshold in an in-window winter hour with real heat input?
      This is the physical observable a fuel switch must produce.
    """
    if not capable_plants:
        return {"tested": False, "note": "no capable plant to test"}
    out: dict = {"tested": True, "by_year": {}}
    cols = [
        "facilityId",
        "unitId",
        "date",
        "hour",
        "grossLoad",
        "co2Mass",
        "heatInput",
        "primaryFuelInfo",
    ]
    # CAMPD stores ``facilityId`` as a STRING in these extracts, so the filter
    # values must be strings too — an int-valued filter raises ArrowTypeError
    # and would silently read zero rows.
    want = {str(int(p)) for p in capable_plants}
    for year in years:
        frames = []
        for path in sorted(CAMPD_UNIT_DIR.glob(f"*_{year}.parquet")):
            df = pd.read_parquet(path, columns=cols)
            df = df[df["facilityId"].astype(str).isin(want)]
            if not df.empty:
                frames.append(df)
        if not frames:
            out["by_year"][str(year)] = {"n_unit_hours": 0, "note": "no CAMPD rows"}
            continue
        df = pd.concat(frames, ignore_index=True)
        df["month"] = pd.to_datetime(df["date"]).dt.month
        # D1 — does the reported label ever vary within a unit-year?
        label_var = df.groupby(["facilityId", "unitId"])["primaryFuelInfo"].nunique()
        # D2 — CO2 intensity on in-window winter hours with real heat input.
        #
        # POPULATION GUARD: the roster keys are PLANTS, and a MISO dual-fuel
        # plant routinely also hosts COAL units. Coal's CO2 intensity (EPA
        # 40 CFR 98 Table C-1: bituminous 93.28, subbituminous 97.17 kg/MMBtu)
        # sits ABOVE the distillate band, so a plant-grain census books coal
        # unit-hours as an "oil signature" and over-counts by ~13x. The
        # mechanism acts ONLY on gas-primary units, so D2 is scored on the
        # GAS-LABELLED units alone, and the separately-labelled "Diesel Oil"
        # units are carried as an internal control on where the band sits.
        win = df[df["month"].isin(WINTER_MONTHS)].copy()
        win = win[win["heatInput"].astype(float) > 0.0]
        rate = (
            win["co2Mass"].astype(float) * SHORT_TON_KG / win["heatInput"].astype(float)
        )
        win = win.assign(co2_kg_per_mmbtu=rate)
        gas_win = win[win["primaryFuelInfo"].isin(_GAS_LABELS)]
        oil_ctl = win[win["primaryFuelInfo"].isin(_OIL_LABELS)]
        in_band = gas_win[
            (gas_win["co2_kg_per_mmbtu"] >= CO2_RATE_OIL_BAND_LO)
            & (gas_win["co2_kg_per_mmbtu"] <= CO2_RATE_OIL_BAND_HI)
        ]
        coal_like = gas_win[gas_win["co2_kg_per_mmbtu"] > CO2_RATE_OIL_BAND_HI]
        out["by_year"][str(year)] = {
            "n_unit_hours": int(len(df)),
            "n_units": int(df.groupby(["facilityId", "unitId"]).ngroups),
            "n_plants_found": int(df["facilityId"].nunique()),
            "label_units_with_varying_fuel": int((label_var > 1).sum()),
            "label_values": sorted(df["primaryFuelInfo"].dropna().unique().tolist()),
            "gas_winter_unit_hours_burning": int(len(gas_win)),
            "gas_winter_co2_rate_p50": (
                round(float(gas_win["co2_kg_per_mmbtu"].median()), 3)
                if len(gas_win)
                else None
            ),
            "gas_winter_co2_rate_p99": (
                round(float(gas_win["co2_kg_per_mmbtu"].quantile(0.99)), 3)
                if len(gas_win)
                else None
            ),
            # THE leg-D statistic: gas-labelled unit-hours whose measured CO2
            # intensity sits in the distillate/residual band.
            "oil_signature_unit_hours": int(len(in_band)),
            "oil_signature_share_of_gas": (
                round(float(len(in_band) / len(gas_win)), 6) if len(gas_win) else None
            ),
            "n_units_with_oil_signature": (
                int(in_band.groupby(["facilityId", "unitId"]).ngroups)
                if len(in_band)
                else 0
            ),
            "above_band_coal_like_unit_hours": int(len(coal_like)),
            # Internal control: units CAMPD itself labels Diesel Oil should sit
            # inside the same band, which is what makes the band a fuel ID.
            "diesel_labelled_unit_hours": int(len(oil_ctl)),
            "diesel_labelled_co2_rate_p50": (
                round(float(oil_ctl["co2_kg_per_mmbtu"].median()), 3)
                if len(oil_ctl)
                else None
            ),
        }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", type=Path, default=None)
    args = ap.parse_args()

    print("=" * 78)
    print("miso-121 PHASE 0 — dual_fuel_switching measured identification (no LP)")
    print("=" * 78)

    capable = dual_fuel_plant_groups()
    print(f"\nEIA-860 Multifuel capable (plant, group) pairs, ALL ISOs: {len(capable)}")

    miso_plants = _miso_plant_codes()
    capable_miso_plants = {p for (p, _g) in capable if p in miso_plants}
    print(
        f"MISO plant codes in the zone lookup: {len(miso_plants)}; "
        f"of those, EIA-860 switch-capable: {len(capable_miso_plants)}"
    )

    results: dict = {
        "iso": ISO,
        "years": list(YEARS),
        "keeper_bundle": str(KEEPER.relative_to(REPO)),
        "n_capable_pairs_all_iso": len(capable),
        "n_capable_miso_plants_eia860": len(capable_miso_plants),
        "bands": {
            "BAR_CAPABLE_MW": BAR_CAPABLE_MW,
            "BAR_CAPABLE_SHARE": BAR_CAPABLE_SHARE,
            "BAR_MEASURED_MONTH_FRAC": BAR_MEASURED_MONTH_FRAC,
            "BAR_BINDING_GENHOURS": BAR_BINDING_GENHOURS,
            "BAR_BYTE_IDENTITY": BAR_BYTE_IDENTITY,
            "BAR_MARGINAL_P50_DOFFER": BAR_MARGINAL_P50_DOFFER,
        },
        "by_year": {},
    }

    fleet_capable_plants: set[int] = set()
    for year in YEARS:
        print(f"\n{'-' * 78}\n{year}\n{'-' * 78}")
        state, _meta = reconstruct_bundle_fleet(KEEPER, year, verbose=True)
        fleet = state["fleet_arrays"]
        config = state["config"]
        if getattr(config, "dual_fuel_switching", False):
            raise SystemExit(
                "FATAL: reconstructed keeper config already arms "
                "dual_fuel_switching — leg C would not be the pre-min array"
            )

        a = leg_a_capability(fleet, capable)
        fleet_capable_plants |= {int(p) for p in a["roster"]}
        print(
            f"  LEG A capability: {a['n_capable_tranches']} tranches / "
            f"{a['n_capable_plants']} plants / {a['capable_mw']:.1f} MW "
            f"({100 * a['capable_share_of_gas']:.2f} % of {a['gas_mw']:.0f} MW gas)"
        )
        for code, row in list(a["roster"].items())[:12]:
            print(f"      {code:>6s}  {row['mw']:>8.1f} MW  {','.join(row['groups'])}")

        b = leg_b_switch_price(config, year)
        print(
            f"  LEG B switch price: measured months "
            f"{b['n_measured_months']}/{b['n_months']}  "
            f"mean {b.get('measured_mean_usd_mmbtu')} $/MMBtu  "
            f"(fallback constant {b['fallback_usd_mmbtu']})"
        )

        c = leg_c_binding(state, config, year, a["capable_rows"])
        print(
            f"  LEG C binding: max Δ_fuel = {c['max_delta_fuel']} $/MMBtu  "
            f"binding gen-hours = {c['n_binding_genhours']} / "
            f"{c.get('n_capable_genhours')}"
        )
        print(
            f"      capable gas: mean {c.get('capable_gas_mean'):.4f} "
            f"max {c.get('max_gas_price'):.4f} $/MMBtu  |  "
            f"oil: min {c.get('oil_min'):.4f} mean {c.get('oil_mean'):.4f}"
        )
        a.pop("capable_rows", None)
        results["by_year"][str(year)] = {"leg_a": a, "leg_b": b, "leg_c": c}

    print(f"\n{'-' * 78}\nLEG D — CAMPD observability\n{'-' * 78}")
    d = leg_d_observability(fleet_capable_plants)
    results["leg_d"] = d
    for year, row in d.get("by_year", {}).items():
        print(f"  {year}: {json.dumps(row)}")

    # ---- Route evaluation, PREREG §5, applied verbatim -------------------
    print(f"\n{'=' * 78}\nROUTE EVALUATION (PREREG §5)\n{'=' * 78}")
    per_year = results["by_year"]
    min_mw = min(y["leg_a"]["capable_mw"] for y in per_year.values())
    min_share = min(y["leg_a"]["capable_share_of_gas"] for y in per_year.values())
    tot_measured = sum(y["leg_b"]["n_measured_months"] for y in per_year.values())
    tot_months = sum(y["leg_b"]["n_months"] for y in per_year.values())
    max_delta = max(
        (y["leg_c"]["max_delta_fuel"] or -np.inf) for y in per_year.values()
    )
    max_binding = max(y["leg_c"]["n_binding_genhours"] for y in per_year.values())
    # INTEGRITY GUARD: route I-D adjudicates "MISO's data does not observe the
    # switch". It must never fire because the CAMPD query itself found nothing —
    # a non-empty capable roster with zero matched unit-hours is a PROBE BUG.
    total_unit_hours = sum(
        int(r.get("n_unit_hours") or 0) for r in d.get("by_year", {}).values()
    )
    if fleet_capable_plants and total_unit_hours == 0:
        raise SystemExit(
            "FATAL: leg D matched 0 CAMPD unit-hours against a capable roster "
            f"of {len(fleet_capable_plants)} plants — the query is broken, and "
            "route I-D must not be adjudicated on it."
        )
    oil_sig = sum(
        int(r.get("oil_signature_unit_hours") or 0)
        for r in d.get("by_year", {}).values()
    )
    label_var = sum(
        int(r.get("label_units_with_varying_fuel") or 0)
        for r in d.get("by_year", {}).values()
    )

    routes = {
        "I_A_capability_absent": bool(
            min_mw < BAR_CAPABLE_MW or min_share < BAR_CAPABLE_SHARE
        ),
        "I_B_switch_price_unidentified": bool(
            (tot_measured / tot_months) < BAR_MEASURED_MONTH_FRAC
        ),
        "I_C_byte_identity": bool(max_delta <= BAR_BYTE_IDENTITY),
        "I_D_unobservable_windows": bool(oil_sig == 0 and label_var == 0),
    }
    results["screen"] = {
        "min_capable_mw": min_mw,
        "min_capable_share_of_gas": min_share,
        "measured_month_frac": tot_measured / tot_months,
        "max_delta_fuel_all_years": None if max_delta == -np.inf else float(max_delta),
        "max_binding_genhours_any_year": max_binding,
        "leg_d_oil_signature_unit_hours": oil_sig,
        "leg_d_label_units_with_varying_fuel": label_var,
        "routes": routes,
    }
    for name, fired in routes.items():
        print(f"  {name:34s} {'FIRES' if fired else 'does not fire'}")

    live = not any(routes.values())
    results["screen"]["verdict"] = "LIVE" if live else "INERT"
    print(
        f"\nPHASE-0 VERDICT: {'LIVE — Phase 1 A/B authorized' if live else 'INERT — cell U -> I, ZERO solves'}"
    )

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(results, indent=2, default=str))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

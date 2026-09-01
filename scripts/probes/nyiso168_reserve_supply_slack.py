"""nyiso-168 phase-0: is NYISO's reserve supply ramp-limited, or free?

THE OBJECT (nyiso-167): the keeper reproduces ~0.70 of NYISO's measured price
response.  This session's phase-0 located the deficit and this probe tests the
one mechanism that survived it.

WHAT IS MEASURED, on committed artifacts plus a fleet reconstruction (NO LP):

1. NYISO's OWN measured ancillary clearing prices (``data/clean/
   ancillary-services/NYISO/{DAM,RTM}``) against the designated keeper's own
   committed reserve-family duals, by load band.  A nested cascade is MAXed,
   never summed (the xiso-cascade rule); distinct products are then summed.
2. Each family's requirement, held MW and slack on the keeper's own
   ``reserve_family_<year>.parquet`` sidecar.
3. The RAMP10-CAPPED SUPPLY CEILING against those requirements.  A
   per-generator ramp bound is ``R_g <= min(headroom_g, ramp10_g)``, so the
   class's supply is bounded above by ``sum_g ramp10_frac_g * pmax_g`` -- the
   capacity basis, before availability or dispatch subtract anything.  Class
   fractions are ``fleet.withholding.RAMP10_FRAC_BY_FUEL`` (NREL/TP-5500-55588
   App. H class ramp rates, EIA generator ramp ranges); hydro is reported both
   in and out, because ``_nyiso_design`` unions it in at FULL headroom on the
   declared ``CAISO_HYDRO_RAMP10_FRAC = 1.0`` basis and ``fleet.RAMP10_FRAC_*``
   carries no hydro entry at all (the nyiso-144 coverage gap).

THE PRE-REGISTERED READING, fixed before the ceiling was computed.
``_nyiso_design`` returns a ReserveDesign with ``supply_cap=None``,
``headroom_eligible=None`` and no ``pergen_*`` -- verified in code, and NYISO
is the only ISO of the three with the machinery that sets neither (``_ercot_
design``, ``_ercot_multiproduct_design`` and ``_pjm_design`` all set
``supply_cap``; PJM additionally runs the full per-generator layout).  Every
eligible unit's FULL headroom therefore backs reserve at zero cost, which is
why the keeper's family duals are zero in 99.6 % of hours.  KILL: if the
ramp10-capped CEILING still clears every NYCA family's requirement by a wide
margin on the capacity basis alone, a per-generator ramp bound is PROVABLY
LP-INERT for NYISO and NO SOLVE IS SPENT on it.

The ceiling is an upper bound in the direction that matters: availability and
dispatch can only reduce the supply below it, but they reduce the UNCAPPED
supply by the same amounts, so a ceiling that clears the requirement several
times over bounds the CAP'S OWN BITE at zero.

Zero solve.  Rule 22: every year read is 2023, 2024 or 2025.
"""

from __future__ import annotations

import glob
import json

import numpy as np
import pandas as pd

BUNDLE = "results/calibration/nyiso159_lossarm_B"
YEARS = (2023, 2024, 2025)
OUT = "results/calibration/_nyiso168_reserve_supply_slack.json"

#: NYISO ancillary price columns; the three reserve products form ONE nested
#: cascade and are combined with max(), never sum (xiso-cascade rule).
CASCADE = [
    "spin_price_usd_per_mw",
    "nonspin_price_usd_per_mw",
    "supp_30min_price_usd_per_mw",
]
REG = "reg_up_price_usd_per_mw"

#: 10-minute ramp capability as a fraction of capacity, by model fuel type —
#: ``market_sim.data.fleet.withholding.RAMP10_FRAC_BY_FUEL`` (NREL/TP-5500-55588
#: App. H class ramp rates + EIA generator ramp ranges). Mirrored here so the
#: probe stays runnable without the model package; hydro deliberately absent —
#: ``fleet.RAMP10_FRAC_*`` carries no hydro entry (the nyiso-144 coverage gap).
RAMP10_FRAC: dict[str, float] = {
    "gas_cc": 0.40,
    "gas_ct": 1.00,
    "gas_st": 0.20,
    "oil": 1.00,
    "coal": 0.15,
    "nuclear": 0.0,
}
#: ``reserves.spec.RESERVE_FUEL_TYPES`` / ``QUICK_START_FUEL_TYPES`` — the two
#: NYISO reserve eligibility classes ``_nyiso_design`` stacks.
RESERVE_FUELS = frozenset({"gas_cc", "gas_ct", "gas_st", "coal", "nuclear", "oil"})
QUICK_FUELS = frozenset({"gas_ct", "oil"})
#: Published NYCA-wide requirements (``reserves.spec.NYISO_RCPF_PRODUCTS``).
NYCA_REQUIREMENT_MW: dict[str, tuple[float, str]] = {
    "nyca_30min_total": (2620.0, "class0"),
    "nyca_10min_total": (1310.0, "class1"),
    "nyca_10min_spin": (655.0, "class1"),
}


def _model_fuel_type(fuel: str, prime_mover: str, technology: str) -> str:
    """Map a clean-fleet row onto the model's fuel-type vocabulary."""
    if fuel != "gas":
        return fuel
    if "Combined Cycle" in technology:
        return "gas_cc"
    if "Steam" in technology or prime_mover == "ST":
        return "gas_st"
    return "gas_ct"


def ramp10_ceiling(year: int) -> dict:
    """Return the ramp10-capped reserve supply CEILING per eligibility class.

    ``sum_g ramp10_frac_g * pmax_g`` over each class's eligible fuel types —
    the capacity-basis upper bound on what a per-generator ramp bound could
    leave available, before availability or dispatch subtract anything. Hydro
    is reported separately: ``_nyiso_design`` unions it into BOTH classes at
    full headroom and ``RAMP10_FRAC`` has no entry for it, so a ramp bound
    built on that table would drop it entirely — the ceiling is therefore
    quoted both with hydro at its armed 1.0 basis and without it.
    """
    d = pd.read_parquet(f"data/clean/fleet/fleet_{year}.parquet")
    d = d[d["iso"].astype(str) == "NYISO"].copy()
    cap = d["summer_capacity_mw"].fillna(d["nameplate_capacity_mw"]).astype(float)
    ft = [
        _model_fuel_type(str(f), str(p), str(t))
        for f, p, t in zip(d["fuel"], d["prime_mover"], d["technology"])
    ]
    by_fuel = pd.Series(cap.to_numpy(), index=ft).groupby(level=0).sum()
    hydro = float(by_fuel.get("hydro", 0.0))
    out = {
        "capacity_mw_by_fuel": {k: float(v) for k, v in by_fuel.items()},
        "hydro_uncapped_mw": hydro,
    }
    for name, fuels in (("class0", RESERVE_FUELS), ("class1", QUICK_FUELS)):
        thermal = sum(float(by_fuel.get(f, 0.0)) for f in fuels)
        ramp = sum(float(by_fuel.get(f, 0.0)) * RAMP10_FRAC.get(f, 0.0) for f in fuels)
        out[name] = {
            "thermal_capacity_mw": thermal,
            "ramp10_ceiling_mw": ramp,
            "ramp10_ceiling_with_hydro_mw": ramp + hydro,
        }
    out["families"] = {
        fam: {
            "requirement_mw": req,
            "ceiling_with_hydro_mw": out[cls]["ramp10_ceiling_with_hydro_mw"],
            "cover_with_hydro_x": out[cls]["ramp10_ceiling_with_hydro_mw"] / req,
            "ceiling_thermal_only_mw": out[cls]["ramp10_ceiling_mw"],
            "cover_thermal_only_x": out[cls]["ramp10_ceiling_mw"] / req,
        }
        for fam, (req, cls) in NYCA_REQUIREMENT_MW.items()
    }
    return out


def load_bands(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(system load MW, load-band index)`` for the keeper's own hours.

    Bands are 0 = load percentile 0-50, 1 = 50-90, 2 = 90-100 — the split the
    phase-0 gap decomposition is stated on.
    """
    s = pd.read_parquet(f"{BUNDLE}/hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    load = s.pivot_table(index="hour", columns="zone", values="demand").sum(axis=1)
    load = load.reindex(range(8760)).to_numpy()
    order = np.argsort(load)
    band = np.zeros(8760, dtype=int)
    band[order[int(8760 * 0.50) : int(8760 * 0.90)]] = 1
    band[order[int(8760 * 0.90) :]] = 2
    return load, band


def measured_as_prices(year: int, market: str) -> dict[str, np.ndarray]:
    """Return the hourly zone-max NYISO cascade and regulation price series."""
    files = glob.glob(f"data/clean/ancillary-services/NYISO/{market}/*{year}*.parquet")
    if not files:
        return {}
    a = pd.read_parquet(files[0])
    hr = (
        pd.to_datetime(a["interval_start_local"]) - pd.Timestamp(f"{year}-01-01")
    ).dt.total_seconds() // 3600
    a = a.assign(hr=hr.astype(int))
    a = a[(a.hr >= 0) & (a.hr < 8760)]
    piv = a.groupby("hr")[CASCADE + [REG]].max().reindex(range(8760))
    return {
        "cascade": piv[CASCADE].max(axis=1).to_numpy(float),
        "regulation": piv[REG].to_numpy(float),
    }


def model_duals(year: int) -> tuple[np.ndarray, pd.DataFrame]:
    """Return ``(summed family dual, per-family frame)`` from the keeper."""
    rf = pd.read_parquet(f"{BUNDLE}/hourly/reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"]
    tot = rf.groupby("hour")["dual"].sum().reindex(range(8760)).fillna(0.0).to_numpy()
    return tot, rf


def main() -> None:
    record: dict = {
        "probe": "nyiso168_reserve_supply_slack",
        "bundle": BUNDLE,
        "years": list(YEARS),
        "note": (
            "Zero solve. Measures NYISO's own cleared AS prices against the "
            "designated keeper's committed reserve-family duals, and the "
            "keeper's reserve supply under the as-armed uncapped-headroom "
            "basis. A nested cascade is MAXed, never summed."
        ),
        "by_year": {},
    }
    for year in YEARS:
        load, band = load_bands(year)
        tot, rf = model_duals(year)
        row: dict = {"bands": ["p0-50", "p50-90", "p90-100"]}
        for market in ("DAM", "RTM"):
            m = measured_as_prices(year, market)
            if not m:
                continue
            row[market] = {
                k: {
                    "mean": float(np.nanmean(v)),
                    "share_gt0_pct": float(np.nanmean(v > 1e-3) * 100.0),
                    "by_band_mean": [float(np.nanmean(v[band == b])) for b in range(3)],
                }
                for k, v in m.items()
            }
        row["model_family_dual_sum"] = {
            "mean": float(tot.mean()),
            "share_gt0_pct": float(np.mean(tot > 1e-3) * 100.0),
            "by_band_mean": [float(tot[band == b].mean()) for b in range(3)],
        }
        row["model_by_family"] = {
            str(fam): {
                "requirement_mw_mean": float(g["requirement_mw"].mean()),
                "held_mw_mean": float(g["held_mw"].mean()),
                "dual_mean": float(g["dual"].mean()),
                "share_gt0_pct": float(np.mean(g["dual"].to_numpy() > 1e-3) * 100.0),
                "slack_mw_mean": float((g["held_mw"] - g["requirement_mw"]).mean()),
            }
            for fam, g in rf.groupby("family")
        }
        row["ramp10_ceiling"] = ramp10_ceiling(year)
        record["by_year"][str(year)] = row
        print(f"=== {year}")
        for market in ("DAM", "RTM"):
            if market in row:
                c = row[market]["cascade"]
                print(
                    f"  {market} measured cascade  mean ${c['mean']:6.2f} "
                    f" >0 in {c['share_gt0_pct']:5.1f}% h "
                    f" bands {[round(x, 2) for x in c['by_band_mean']]}"
                )
        d = row["model_family_dual_sum"]
        print(
            f"  MODEL summed duals     mean ${d['mean']:6.3f} "
            f" >0 in {d['share_gt0_pct']:5.1f}% h "
            f" bands {[round(x, 3) for x in d['by_band_mean']]}"
        )
        for fam, c in row["ramp10_ceiling"]["families"].items():
            print(
                f"    ramp10 ceiling {fam:18s} req {c['requirement_mw']:6,.0f}"
                f"  ceiling {c['ceiling_with_hydro_mw']:8,.0f} ({c['cover_with_hydro_x']:5.2f}x)"
                f"  thermal-only {c['ceiling_thermal_only_mw']:8,.0f}"
                f" ({c['cover_thermal_only_x']:5.2f}x)"
            )

    with open(OUT, "w") as fh:
        json.dump(record, fh, indent=1)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

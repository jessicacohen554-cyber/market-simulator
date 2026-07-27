"""pjm-133 pre-solve sizing — how large can the nameplate-aware delta be on PJM?

Sizes the ``hydro_budget_nameplate_aware`` delta BEFORE arm B is solved, so the
pre-registration carries a physical bound rather than a hope. This is the PJM
analogue of ``_caiso130_nameplate_precheck.py``, **mirrored not copied**: PJM's
keeper (``pjm121_ccbelt``) runs ``hydro_ror_split`` and ``hydro_min_flow_floor``
BOTH OFF, so there is no flat RoR class and the entire re-allocation lands on
shapeable plants; and PJM's measured comparator is confounded in a way CAISO's
is not (section B), which is why the PRIMARY is registered on the C1 volume
criterion rather than on a measured hour-of-day window.

Five sections, **no LP is built or solved anywhere**:

A. **Keeper baseline** from the keeper bundle's own committed
   ``hourly/class_hourly_<year>.parquet`` sidecars (never a replay): hydro by
   hour-of-day window against measured EIA-930 ``NG: WAT``, the annual model
   volume against the C1 benchmark, and the model CO2 against the eGRID bench.
B. **Provenance of the level target the flag serves** — PJM files no
   ``NG: PS`` column, so its ``NG: WAT`` is pumped-storage-inclusive while the
   model's budget-hydro fleet is prime-mover ``HY`` only and its 5.0 GW of
   ``PS`` is built separately as storage. Measured, not asserted, so the
   prereg can disclose exactly what the pin is worth.
C. **The delta's energy budget** from the same no-LP ``build_hydro_fleet`` diff
   the caiso-130 blast-radius probe uses: MWh re-allocated, clipped
   plant-months, month-total drift, plant-set identity, and the recipients'
   post-flag implied capacity factor (the pre-solve read on whether the freed
   water lands on plants with room to SHAPE it or on plants already near
   baseload — the caiso-130 §3 failure mode, measurable before the solve).
D. **No-feedback ceilings** on what the delta can move: the C1 hydro volume
   closure (deterministic — the budget total is preserved, so the ceiling is
   exactly the re-allocated energy) and the C3a demand-weighted price movement
   under three allocations of the freed energy (flat / keeper-hydro-shape /
   peak-concentrated), from the keeper's own lambda-vs-thermal-dispatch slope.
E. **The CO2 side**, from the same displacement estimate.

Usage:
    PYTHONPATH=.:src:scripts/probes .venv/bin/python \
        scripts/probes/_pjm133_nameplate_precheck.py
"""

from __future__ import annotations

import gzip
import json
import logging
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(_p))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.hydro import build_hydro_fleet, hours_per_month  # noqa: E402

YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results" / "calibration" / "pjm121_ccbelt"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "PJM"

# Hour-of-day windows, identical to the caiso-125/130 definitions so the two
# sessions' window numbers are directly comparable.
WINDOWS: dict[str, range] = {
    "overnight": range(0, 7),
    "belly": range(9, 16),
    "evening": range(17, 22),
    "late": range(22, 24),
}
# Model dispatch classes whose output is thermal, i.e. the quantity whose
# marginal unit sets the LP's energy-balance dual. Used only to build the
# empirical lambda-vs-thermal slope in section D.
THERMAL_CLASSES = (
    "CC_CHP",
    "CC_REGULAR",
    "COAL_BIT",
    "COAL_PRB",
    "COAL_WC",
    "CT_CHP",
    "CT_PEAKER",
    "ST_CHP",
    "ST_GAS",
    "oil",
)
# The PJM_external seam zone is a modelling node, not a load pocket; C3a is a
# PJM-internal demand-weighted mean, so it is excluded from the lambda weight.
SEAM_ZONE = "PJM_external"
# Quantile bins used for the empirical dlambda/dThermal slope. 50 bins over
# 8760 hours leaves ~175 hours per bin — enough to average out the LP's
# hour-to-hour commitment noise without smearing the scarcity tail.
N_SLOPE_BINS = 50
# Share of hours (by lambda rank) the peak-concentrated allocation is spread
# over in the section-D worst case.
PEAK_HOUR_SHARE = 0.10

# PJM keeper hydro settings, read from its committed bundle (never guessed).
KEEPER_HYDRO = dict(backfill_year=2024, eia930_monthly=True, ror_split=False, min_flow_floor=False)


def class_pivot(year: int) -> pd.DataFrame:
    """Return the keeper's P1 class dispatch as an (hour x class) pivot (MW)."""
    frame = pd.read_parquet(KEEPER / "hourly" / f"class_hourly_{year}.parquet")
    frame = frame[frame["pass"] == "P1"]
    return frame.pivot_table(
        index="hour", columns="klass", values="mw", observed=True
    ).sort_index()


def system_frame(year: int) -> pd.DataFrame:
    """Return the keeper's P1 system frame (zone, hour, price, demand, ...)."""
    frame = pd.read_parquet(KEEPER / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def pjm_lambda_and_demand(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (demand-weighted hourly lambda, hourly PJM-internal demand)."""
    sysf = system_frame(year)
    internal = sysf[sysf["zone"] != SEAM_ZONE]
    num = (internal["price"] * internal["demand"]).groupby(internal["hour"]).sum()
    den = internal["demand"].groupby(internal["hour"]).sum()
    return (num / den).sort_index().to_numpy(float), den.sort_index().to_numpy(float)


def bench(year: int) -> dict:
    """Return the committed C1/C5a benchmark payload for a PJM year."""
    with gzip.open(BENCH / f"{year}.json.gz") as handle:
        return json.load(handle)["bench"]


def section_a() -> dict:
    """A. Keeper baseline: hydro windows, C1 hydro volume, CO2."""
    from market_sim.data.eia930.envelopes import _hydro_wat_month_hod

    print("=== A. keeper baseline (from pjm121_ccbelt's own hourly/ sidecars) ===")
    out: dict[int, dict] = {}
    for year in YEARS:
        piv = class_pivot(year)
        model = piv["hydro"].to_numpy(float)
        meas = _hydro_wat_month_hod("PJM", year)["mw"].to_numpy(float)[: len(model)]
        hod = np.arange(len(model)) % 24
        row = {
            f"gap_{name}": float(np.nanmean(model[np.isin(hod, list(win))] - meas[np.isin(hod, list(win))]))
            for name, win in WINDOWS.items()
        }
        bch = bench(year)
        row["model_twh"] = float(model.sum() / 1e6)
        row["bench_twh"] = float(bch["classFull"]["hydro"])
        row["vol_gap_twh"] = row["model_twh"] - row["bench_twh"]
        row["co2_bench_mt"] = float(bch["co2"]["egrid"])
        row["annual_model_mw"] = float(np.nanmean(model))
        row["annual_meas_mw"] = float(np.nanmean(meas))
        out[year] = row
        print(
            f"  {year}: overnight {row['gap_overnight']:+7.1f} | belly {row['gap_belly']:+7.1f} "
            f"| evening {row['gap_evening']:+8.1f} | late {row['gap_late']:+7.1f} MW"
        )
        print(
            f"        C1 hydro volume: model {row['model_twh']:6.3f} vs bench "
            f"{row['bench_twh']:6.3f} TWh  =>  gap {row['vol_gap_twh']:+6.3f} TWh"
        )
    return out


def section_b() -> dict:
    """B. What the pinned level target actually contains (PJM-specific)."""
    from market_sim.config.paths import EIA_860_DIR
    from market_sim.data.eia930.envelopes import measured_monthly_hydro
    from market_sim.data.hydro import EIA_860_PARQUET_NAME

    print("\n=== B. provenance of the LEVEL TARGET the flag serves ===")
    e860 = pd.read_parquet(Path(EIA_860_DIR) / EIA_860_PARQUET_NAME)
    pjm = e860[e860["balancing_authority_code"] == "PJM"]
    by_pm = pjm.groupby("prime_mover")["nameplate_capacity_mw"].sum()
    hy_mw = float(by_pm.get("HY", 0.0))
    ps_mw = float(by_pm.get("PS", 0.0))
    print(
        f"  EIA-860 PJM nameplate: HY (budget-hydro fleet) {hy_mw:,.0f} MW | "
        f"PS (built separately as STORAGE) {ps_mw:,.0f} MW"
    )
    zone_names = get_iso_config("PJM").zone_names
    out: dict[int, dict] = {}
    for year in YEARS:
        target = measured_monthly_hydro("PJM", year)
        _u, unpinned = build_hydro_fleet(
            "PJM",
            year,
            zone_names=zone_names,
            backfill_year=KEEPER_HYDRO["backfill_year"],
            eia930_monthly=False,
            forecast_budget=False,
        )
        row = {
            "wat_target_twh": float(target.sum() / 1e6),
            "eia923_hy_twh": float(unpinned.sum() / 1e6),
            "hy_nameplate_mw": hy_mw,
            "ps_nameplate_mw": ps_mw,
        }
        row["pin_uplift_twh"] = row["wat_target_twh"] - row["eia923_hy_twh"]
        row["implied_fleet_cf"] = row["wat_target_twh"] * 1e6 / (hy_mw * 8760.0)
        out[year] = row
        print(
            f"  {year}: EIA-930 NG:WAT target {row['wat_target_twh']:6.2f} TWh vs "
            f"EIA-923 prime-mover-HY budget {row['eia923_hy_twh']:5.2f} TWh "
            f"=> pin uplift {row['pin_uplift_twh']:+5.2f} TWh "
            f"(implied HY-fleet CF {row['implied_fleet_cf']:.1%})"
        )
    print(
        "  PJM files NO `NG: PS` column (ISNE does), so its `NG: WAT` carries\n"
        "  pumped-storage generation the model books in its STORAGE fleet. The\n"
        "  pin is therefore PS-inflated. DISCLOSED, NOT FIXED HERE (single delta)."
    )
    return out


def section_c() -> dict:
    """C. The delta's energy budget, plant-set identity and recipient CF."""
    print("\n=== C. delta energy budget (no LP: build_hydro_fleet off vs on) ===")
    zone_names = get_iso_config("PJM").zone_names
    hpm = hours_per_month().astype(float)
    out: dict[int, dict] = {}
    for year in YEARS:
        common = dict(
            zone_names=zone_names,
            backfill_year=KEEPER_HYDRO["backfill_year"],
            eia930_monthly=KEEPER_HYDRO["eia930_monthly"],
            forecast_budget=False,
            ror_split=KEEPER_HYDRO["ror_split"],
            min_flow_floor=KEEPER_HYDRO["min_flow_floor"],
        )
        units_a, mon_a = build_hydro_fleet("PJM", year, nameplate_aware_target=False, **common)
        units_b, mon_b = build_hydro_fleet("PJM", year, nameplate_aware_target=True, **common)
        cap = np.array([u.pmax_mw for u in units_a], dtype=float)[:, None] * hpm[None, :]
        over_a = np.maximum(0.0, mon_a - cap)
        over_b = np.maximum(0.0, mon_b - cap)
        delta = mon_b - mon_a
        gain = np.maximum(delta, 0.0)  # energy ARRIVING at a plant-month
        recv = gain > 1e-9
        row = {
            "n_plants_a": len(units_a),
            "n_plants_b": len(units_b),
            "budget_twh": float(mon_a.sum() / 1e6),
            "moved_mwh": float(gain.sum()),
            "moved_pct_of_budget": 100.0 * float(gain.sum()) / float(mon_a.sum()),
            "clipped_plant_months": int((over_a > 1e-9).sum()),
            "undeliverable_mwh_off": float(over_a.sum()),
            "undeliverable_mwh_on": float(over_b.sum()),
            "recipient_plant_months": int(recv.sum()),
            "month_total_max_drift_mwh": float(np.abs(delta.sum(axis=0)).max()),
            "delivered_mw_equiv": float(gain.sum() / 8760.0),
            # Energy-weighted implied CF of the RECIPIENT plant-months after the
            # re-allocation: low CF => the water lands where the LP still has
            # room to shape it; high CF => it lands on near-baseload plants and
            # can only be spread flat (the caiso-130 section-3 failure mode).
            "recipient_cf_after": float(
                (mon_b[recv] / cap[recv] * mon_b[recv]).sum() / max(mon_b[recv].sum(), 1.0)
            ),
            "donor_cf_before": float(
                (mon_a[over_a > 1e-9] / cap[over_a > 1e-9] * mon_a[over_a > 1e-9]).sum()
                / max(mon_a[over_a > 1e-9].sum(), 1.0)
            ),
        }
        assert row["n_plants_a"] == row["n_plants_b"], "flag changed the plant SET"
        out[year] = row
        print(
            f"  {year}: moved {row['moved_mwh']/1e3:7.1f} GWh "
            f"({row['moved_pct_of_budget']:.2f} % of a {row['budget_twh']:.2f} TWh budget, "
            f"= {row['delivered_mw_equiv']:+5.1f} MW annual mean)"
        )
        print(
            f"        clipped plant-months {row['clipped_plant_months']:3d} -> recipients "
            f"{row['recipient_plant_months']:3d} | undeliverable "
            f"{row['undeliverable_mwh_off']/1e3:7.1f} -> {row['undeliverable_mwh_on']:.1f} GWh"
            f" | month drift {row['month_total_max_drift_mwh']:.2e} MWh"
        )
        print(
            f"        donor CF before {row['donor_cf_before']:.1%} (>100 % is the defect) "
            f"| recipient CF after {row['recipient_cf_after']:.1%} "
            f"(headroom to SHAPE = 1 - this)"
        )
    return out


def _lambda_slope(year: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (hourly lambda, hourly demand, hourly dlambda/dThermal in $/MWh per MW).

    The slope is empirical and keeper-internal: hours are binned by their own
    total thermal dispatch, and the finite difference of the bin-mean lambda
    against the bin-mean thermal MW gives the local steepness of the LP's own
    supply stack. It is a NO-FEEDBACK proxy — it holds commitment, the water
    value and every other LP response fixed — which is exactly what a pre-solve
    ceiling is for.
    """
    piv = class_pivot(year)
    lam, dem = pjm_lambda_and_demand(year)
    thermal = piv[[c for c in THERMAL_CLASSES if c in piv.columns]].sum(axis=1).to_numpy(float)
    order = np.argsort(thermal)
    bins = np.array_split(order, N_SLOPE_BINS)
    bin_t = np.array([thermal[b].mean() for b in bins])
    bin_l = np.array([lam[b].mean() for b in bins])
    # Central differences on the bin means; edges use the one-sided difference.
    slope_bin = np.gradient(bin_l, bin_t)
    slope_bin = np.clip(slope_bin, 0.0, None)  # a falling stack is binning noise
    slope = np.empty_like(thermal)
    for b, s in zip(bins, slope_bin):
        slope[b] = s
    return lam, dem, slope


def section_d(sizing: dict) -> dict:
    """D. No-feedback ceilings: C1 volume closure and the C3a price movement."""
    print("\n=== D. no-feedback ceilings — what this delta CAN and CANNOT reach ===")
    out: dict[int, dict] = {}
    for year in YEARS:
        lam, dem, slope = _lambda_slope(year)
        piv = class_pivot(year)
        hydro = piv["hydro"].to_numpy(float)
        moved = sizing[year]["moved_mwh"]

        def dc3a(alloc: np.ndarray) -> float:
            """Demand-weighted lambda movement for an hourly MWh allocation."""
            return float(-(dem * alloc * slope).sum() / dem.sum())

        flat = np.full(len(lam), moved / len(lam))
        shape = hydro / hydro.sum() * moved
        # Peak-concentrated: the whole re-allocation spread over the top
        # PEAK_HOUR_SHARE of hours by lambda — the worst case for C3a.
        n_peak = int(len(lam) * PEAK_HOUR_SHARE)
        peak = np.zeros(len(lam))
        peak[np.argsort(lam)[-n_peak:]] = moved / n_peak
        row = {
            "moved_gwh": moved / 1e3,
            "c1_volume_ceiling_twh": moved / 1e6,
            "c3a_flat": dc3a(flat),
            "c3a_shape": dc3a(shape),
            "c3a_peak": dc3a(peak),
            "mean_lambda": float(np.average(lam, weights=dem)),
        }
        out[year] = row
        print(
            f"  {year}: C1 hydro volume ceiling {row['c1_volume_ceiling_twh']:+6.3f} TWh "
            f"(exact — the month total is preserved, so the gap can close by this and no more)"
        )
        print(
            f"        C3a demand-weighted lambda movement: flat {row['c3a_flat']:+6.3f} | "
            f"hydro-shape {row['c3a_shape']:+6.3f} | peak-concentrated {row['c3a_peak']:+6.3f} $/MWh "
            f"(on a {row['mean_lambda']:.2f} $/MWh mean)"
        )
    return out


def section_e(sizing: dict, ceilings: dict, baseline: dict) -> dict:
    """E. The CO2 side of the same displacement."""
    print("\n=== E. CO2 side of the displacement (no-feedback) ===")
    out: dict[int, dict] = {}
    for year in YEARS:
        bch = bench(year)
        intens = bch["co2"]["intensity"]
        # Marginal displaced intensity: the LP displaces its own marginal
        # thermal unit. Bracket it with the CC (lightest plausible marginal)
        # and the bituminous-coal (heaviest plausible marginal) intensities
        # from the SAME measured benchmark, rather than picking one.
        lo, hi = float(intens["CC_REGULAR"]), float(intens["COAL_BIT"])
        moved_twh = sizing[year]["moved_mwh"] / 1e6
        row = {
            "co2_model_delta_mt_lo": -moved_twh * lo,
            "co2_model_delta_mt_hi": -moved_twh * hi,
            "co2_bench_mt": baseline[year]["co2_bench_mt"],
        }
        out[year] = row
        print(
            f"  {year}: model CO2 moves {row['co2_model_delta_mt_hi']:+6.3f} to "
            f"{row['co2_model_delta_mt_lo']:+6.3f} Mt (coal-marginal .. CC-marginal) "
            f"against a {row['co2_bench_mt']:.1f} Mt measured level"
        )
    return out


def main() -> None:
    logging.basicConfig(level=logging.ERROR)
    baseline = section_a()
    provenance = section_b()
    sizing = section_c()
    ceilings = section_d(sizing)
    co2 = section_e(sizing, ceilings, baseline)

    print("\n=== SUMMARY: predicted C1 hydro volume closure ===")
    for year in YEARS:
        gap = baseline[year]["vol_gap_twh"]
        ceil = ceilings[year]["c1_volume_ceiling_twh"]
        print(
            f"  {year}: gap {gap:+6.3f} TWh, full delivery moves it to "
            f"{gap + ceil:+6.3f} TWh — the clip explains "
            f"{100.0 * ceil / abs(gap):.1f} % of the deficit"
        )

    out = REPO / "results" / "probes" / "pjm133_precheck.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {
                "baseline": baseline,
                "provenance": provenance,
                "sizing": sizing,
                "ceilings": ceilings,
                "co2": co2,
            },
            indent=1,
            default=float,
        )
        + "\n"
    )
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""nyiso-171 phase 0 — identify NYISO's CC_CHP steam-host floor from measured conduct.

ZERO SOLVE. Every series is a committed artifact or a raw measured record.

The object (handed forward by nyiso-169b, untouched by nyiso-170): the keeper's
CC_CHP is wrong in BOTH directions at the bottom of its own duration curve —
model p05 869/892/817 MW vs measured 531/732/648, yet at p01 the model collapses
to near zero in 96 hours of 2025 where the measured fleet is never off. The brief
frames this as a steam-host-following resource the model treats as freely
dispatchable.

Phase 0 answers three questions BEFORE any parameter is touched:

  (a) which plants drive the near-zero model hours, and is the measured CC_CHP
      fleet floor a PER-PLANT property or a portfolio artifact?
  (b) are the p05 over-run and the p01 under-run the same plants?
  (c) what already floors CC_CHP today — a full rule 19 [R-ONE-MECH] D-2
      attribution, so a correction REPLACES rather than stacks.

Pre-registered gates (see PREREG-nyiso171-chp-floor-identification.md, committed
with this file BEFORE it was run):

  A1  rule 19 attribution complete and unambiguous
  A2  the model's structural floor, per plant, as the code builds it
  A3  THE STOP CONDITION — measured floor per-plant (PASS) vs portfolio
      artifact (FAIL -> say so and stop)
  A4  meter-coverage validity guard (the nyiso-170 section 3 lesson)
  A5  can a floor even bind — outage vs economics in the collapse hours
  A6  sizing, and the honest direction on the p05 over-run and class volume

Rule 13 [R-MEASURED]: CAMPD enters ONLY as conduct identification. Nothing is
pinned to observed generation and no statistic is tuned to a residual.
Rule 22 [R-HOLDOUT]: 2023/2024/2025 only.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.data.derive_actual_lmp import _std_hour_index  # noqa: E402

KEEPER = ROOT / "results/calibration/nyiso159_lossarm_B"
BENCH = ROOT / "frontend/data/backcast/bench/NYISO"
TRANCHES = RAW_DATA_DIR / "_processed-legacy/thermal_tranches_NYISO.csv"
OUT = ROOT / "results/calibration/_nyiso171_chp_floor_identification.json"
YEARS = (2023, 2024, 2025)
STD_TZ = "Etc/GMT+5"  # fixed standard-time clock, as nyiso169b/170 (no DST gap)

# Gate thresholds, fixed before the measurement.
A3_MIN_COVERAGE = 0.50  # per-plant mins must carry >= half the fleet floor
A4_SILENT_TWH = 1e-6  # a meter reporting below this is silent, not zero


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_cc_chp_by_plant(year: int, chpset: set[int]) -> pd.DataFrame:
    """Measured hourly MW per CC_CHP plant on the model's 8760 clock.

    Same class construction as nyiso169b/nyiso170 (CAMPD ``unitType`` crossed
    with the EIA-860 CHP flag) so the series are directly comparable.
    """
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitType", "date", "hour", "grossLoad"],
    )
    fid = d["facilityId"].astype(int)
    ut = d["unitType"].fillna("")
    d = d[ut.str.contains("Combined cycle") & fid.isin(chpset)]
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    idx = _std_hour_index(pd.DatetimeIndex(ts).tz_localize(STD_TZ), year, STD_TZ)
    frame = pd.DataFrame(
        {
            "hour": idx,
            "plant": d["facilityId"].astype(int).to_numpy(),
            "mw": d["grossLoad"].fillna(0.0).to_numpy(),
        }
    )
    wide = frame.pivot_table(
        index="hour", columns="plant", values="mw", aggfunc="sum", fill_value=0.0
    )
    return wide.reindex(range(8760)).fillna(0.0)


def model_cc_chp(year: int) -> pd.Series:
    """The keeper's own P1 hourly CC_CHP MW (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c["klass"] == "CC_CHP")]
    return c.set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)


def bench_cc_chp(year: int) -> float:
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return float(json.load(fh)["bench"]["classFull"]["CC_CHP"])


# ---------------------------------------------------------------- A1
def gate_a1() -> dict:
    """Rule 19 [R-ONE-MECH]: every mechanism forcing CC_CHP in the keeper."""
    diag = json.load(open(KEEPER / "legitimacy_diagnostics.json"))
    rows = [r for r in diag["diagnostics"]["D2"]["rows"] if r["class"] == "CC_CHP"]
    mechs = sorted({r["mechanism"] for r in rows})
    return {
        "mechanisms": mechs,
        "by_year": {
            str(r["year"]): {
                "mechanism": r["mechanism"],
                "forced_twh": r["forced_twh"],
                "class_total_twh": r["class_total_twh"],
                "share_of_class": r["share_of_class"],
            }
            for r in rows
        },
        "d2_exempt_classes": diag["gates"].get("d2_exempt_classes"),
        "single_mechanism": len(mechs) == 1,
        "verdict": "PASS — one mechanism, a correction REPLACES its level source"
        if len(mechs) == 1
        else "FAIL — more than one mechanism forces CC_CHP; reconcile before adding",
    }


# ---------------------------------------------------------------- A2
def gate_a2() -> dict:
    """The model's structural CC_CHP floor, per plant, as assembly.py builds it.

    ``chp_pmin_cf`` (the artifact's CAMPD p2 never-below statistic) times
    ``(1 - mustrun_pct/100)`` times nameplate — the grid-delivered steam floor
    that becomes ``chp_grid_pmin_mw`` and is tagged MECH_CHP_STEAM.
    """
    df = pd.read_csv(TRANCHES)
    cc = df[df.plant_group == "CC_CHP"].copy()
    cc["mustrun_pct"] = cc["mustrun_pct"].fillna(0.0)
    cc["floor_mw"] = (
        cc["chp_pmin_cf"].fillna(0.0)
        * (1.0 - cc["mustrun_pct"] / 100.0)
        / 100.0
        * cc["nameplate_mw"]
    )
    zero = cc[cc["floor_mw"] <= 0.0]
    return {
        "n_plants": int(len(cc)),
        "fleet_nameplate_mw": round(float(cc["nameplate_mw"].sum()), 1),
        "fleet_structural_floor_mw": round(float(cc["floor_mw"].sum()), 1),
        "n_plants_zero_floor": int(len(zero)),
        "nameplate_share_zero_floor": round(
            float(zero["nameplate_mw"].sum() / cc["nameplate_mw"].sum()), 4
        ),
        "campd_visible_all_zero": bool(
            (cc.loc[cc.status == "ok", "floor_mw"] <= 0.0).all()
        ),
        "plants": [
            {
                "plant": int(r.plant_code),
                "name": str(r.name),
                "status": str(r.status),
                "nameplate_mw": round(float(r.nameplate_mw), 1),
                "chp_pmin_cf": float(r.chp_pmin_cf),
                "median_cf": (None if pd.isna(r.median_cf) else float(r.median_cf)),
                "floor_mw": round(float(r.floor_mw), 1),
            }
            for r in cc.sort_values("nameplate_mw", ascending=False).itertuples(
                index=False
            )
        ],
    }


# ---------------------------------------------------------------- A3 / A4
def gate_a3_a4(year: int, chpset: set[int]) -> dict:
    """THE STOP CONDITION — is the measured CC_CHP floor per-plant or portfolio?

    A fleet series can look "never off" for two completely different reasons:

      PER-PLANT PHYSICS — each cogen individually never drops below its own
      steam-host level. The floor is then a physical/contractual property of a
      machine, admissible under rule 13 and representable as ``min_gen``.

      PORTFOLIO ARTIFACT — every plant cycles to zero on its own, but they are
      never all off at once, so only the SUM has a floor. There is then no
      per-plant physics to represent, and a per-plant ``min_gen`` would force a
      machine to run in hours its own meter says it was off — a rule 17
      [R-FLOOR-WINDOW] violation by construction.

    The discriminator is exact: ``sum_p min_t(gen_p,t)`` vs ``min_t(sum_p gen_p,t)``.
    Under per-plant physics the two are close; under a portfolio artifact the
    first collapses to ~0 while the second does not.

    A4 rides along: a plant whose CAMPD meter is SILENT (identically zero all
    year) contributes a spurious zero to the per-plant minimum. The nyiso-170
    section 3 CEMS-coverage lesson and the chp_layup census guard both say a
    silent meter is no evidence — such plants are reported and excluded from
    the discriminator rather than convicted by it.
    """
    wide = campd_cc_chp_by_plant(year, chpset)
    fleet = wide.sum(axis=1)

    # A4 — meter validity, per plant.
    twh = wide.sum(axis=0) / 1e6
    silent = [int(p) for p in wide.columns if float(twh[p]) <= A4_SILENT_TWH]
    live = [p for p in wide.columns if p not in set(silent)]

    def q(s: pd.Series, p: float) -> float:
        return float(np.percentile(s.to_numpy(), p))

    per_plant = []
    for p in wide.columns:
        s = wide[p]
        on = s > 0.0
        per_plant.append(
            {
                "plant": int(p),
                "twh": round(float(twh[p]), 4),
                "silent_meter": bool(float(twh[p]) <= A4_SILENT_TWH),
                "on_share": round(float(on.mean()), 4),
                "p01_mw": round(q(s, 1), 1),
                "p05_mw": round(q(s, 5), 1),
                "min_mw": round(float(s.min()), 1),
                # loading conditional on being online — the WP-3 lens
                "p05_on_mw": (round(float(np.percentile(s[on], 5)), 1) if on.any() else None),
                "median_on_mw": (round(float(s[on].median()), 1) if on.any() else None),
            }
        )

    fleet_p01 = q(fleet, 1)
    fleet_min = float(fleet.min())
    # The discriminator, over meter-live plants only (A4).
    sum_plant_min = float(sum(float(wide[p].min()) for p in live))
    sum_plant_p01 = float(sum(q(wide[p], 1) for p in live))
    coverage_min = (sum_plant_min / fleet_min) if fleet_min > 0 else 0.0
    coverage_p01 = (sum_plant_p01 / fleet_p01) if fleet_p01 > 0 else 0.0

    # How many plants are individually never off?
    never_off = [int(p) for p in live if float(wide[p].min()) > 0.0]

    return {
        "n_plants_campd": int(wide.shape[1]),
        "n_silent_meters": len(silent),
        "silent_plants": silent,
        "fleet_min_mw": round(fleet_min, 1),
        "fleet_p01_mw": round(fleet_p01, 1),
        "fleet_p05_mw": round(q(fleet, 5), 1),
        "sum_plant_min_mw": round(sum_plant_min, 1),
        "sum_plant_p01_mw": round(sum_plant_p01, 1),
        "coverage_min": round(coverage_min, 4),
        "coverage_p01": round(coverage_p01, 4),
        "n_plants_never_off": len(never_off),
        "plants_never_off": never_off,
        "per_plant": sorted(per_plant, key=lambda r: -r["twh"]),
        "verdict": (
            "PER-PLANT PHYSICS"
            if coverage_p01 >= A3_MIN_COVERAGE
            else "PORTFOLIO ARTIFACT"
        ),
    }


# ---------------------------------------------------------------- A5
def gate_a5(year: int) -> dict:
    """Can a floor even bind — are the model's collapse hours outage or economics?

    ``min_gen`` is clipped to ``pmax x availability``, so a floor placed on a
    fleet that is genuinely on outage in the collapse hours is INERT. Without a
    per-plant model replay the discriminator available on committed artifacts is
    the TEMPORAL SHAPE of the collapse: a real outage is CONTIGUOUS (a plant is
    out for days or weeks), while an economic shutdown is SCATTERED across the
    cheap hours of many days.
    """
    m = model_cc_chp(year)
    thr = float(np.percentile(m.to_numpy(), 1))
    low = m <= max(thr, 1.0)
    idx = np.flatnonzero(low.to_numpy())
    if idx.size == 0:
        return {"n_low_hours": 0}
    # Contiguity: how many maximal runs do the low hours form, and how long?
    breaks = np.flatnonzero(np.diff(idx) > 1)
    runs = np.split(idx, breaks + 1)
    lens = np.array([len(r) for r in runs])
    hod = pd.Series(idx % 24).value_counts().sort_index()
    return {
        "n_low_hours": int(idx.size),
        "p01_mw": round(thr, 1),
        "model_min_mw": round(float(m.min()), 1),
        "model_p05_mw": round(float(np.percentile(m.to_numpy(), 5)), 1),
        "n_runs": int(len(runs)),
        "longest_run_h": int(lens.max()),
        "median_run_h": float(np.median(lens)),
        "share_in_runs_ge_24h": round(float(lens[lens >= 24].sum() / lens.sum()), 4),
        "n_distinct_days": int(len({int(i) // 24 for i in idx})),
        "hour_of_day_top5": {int(k): int(v) for k, v in hod.nlargest(5).items()},
        "verdict": (
            "OUTAGE-LIKE (contiguous)"
            if float(lens[lens >= 24].sum() / lens.sum()) >= 0.5
            else "ECONOMIC (scattered) — a floor would bind"
        ),
    }


# ---------------------------------------------------------------- A5b
def gate_a5b(year: int) -> dict:
    """A5's pre-registered contiguity test is a WEAK instrument — this is the strong one.

    A5 discriminates outage from economics by the temporal SHAPE of the collapse
    hours, which split 2023/2024 ("scattered") from 2025 ("contiguous"). Shape is
    only a proxy. The direct discriminator is available on the same committed
    artifacts and is reported alongside, not instead of, the pre-registered one:

      * an ECONOMIC shutdown happens in CHEAP hours — the class is out of merit,
        so price sits BELOW the annual mean and the rest of the gas fleet runs;
      * an AVAILABILITY event happens regardless of price, and derates the whole
        gas fleet together, so price sits ABOVE the annual mean while total gas
        output collapses with it.

    ``min_gen`` is clipped to ``pmax x availability``, so a steam floor is
    INERT by construction in any hour whose collapse is an availability event.
    """
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    sysh = s.groupby("hour").agg(price=("price", "mean"), demand=("demand", "sum"))

    m = c[c["klass"] == "CC_CHP"].set_index("hour")["mw"].reindex(range(8760)).fillna(0.0)
    thr = float(np.percentile(m.to_numpy(), 1))
    idx = np.flatnonzero((m <= max(thr, 1.0)).to_numpy())

    gas_classes = ["CC_CHP", "CC_REGULAR", "CT_PEAKER", "ST_GAS", "ST_CHP", "CT_CHP"]
    gas = (
        c[c["klass"].isin(gas_classes)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(8760))
        .fillna(0.0)
    )
    blk_price = float(sysh.loc[idx, "price"].mean())
    yr_price = float(sysh["price"].mean())
    blk_gas = float(gas.iloc[idx].mean())
    yr_gas = float(gas.mean())
    by_class = {
        k: round(
            float(
                c[c["klass"] == k]
                .set_index("hour")["mw"]
                .reindex(range(8760))
                .fillna(0.0)
                .iloc[idx]
                .mean()
            ),
            1,
        )
        for k in gas_classes
    }
    price_ratio = blk_price / yr_price if yr_price else float("nan")
    gas_ratio = blk_gas / yr_gas if yr_gas else float("nan")
    return {
        "n_low_hours": int(idx.size),
        "block_mean_price": round(blk_price, 2),
        "year_mean_price": round(yr_price, 2),
        "price_ratio": round(price_ratio, 3),
        "block_total_gas_mw": round(blk_gas, 1),
        "year_total_gas_mw": round(yr_gas, 1),
        "gas_ratio": round(gas_ratio, 4),
        "block_mean_by_gas_class_mw": by_class,
        "months": {
            int(k): int(v)
            for k, v in pd.Series(idx % 8760 // 730 + 1).value_counts().sort_index().items()
        },
        "verdict": (
            "AVAILABILITY EVENT — a steam floor is INERT here (min_gen <= pmax x availability)"
            if (price_ratio > 1.0 and gas_ratio < 0.5)
            else "ECONOMIC — a floor would bind"
        ),
    }


# ---------------------------------------------------------------- A6
def gate_a6(year: int, chpset: set[int], a3: dict) -> dict:
    """Sizing, and the honest direction on the p05 over-run and class volume.

    The candidate floor is the measured PER-PLANT never-below level summed over
    meter-live plants (``sum_plant_p01_mw`` from A3) — not a fitted value. The
    energy it would force is bounded BELOW at the fleet grain by
    ``sum_t max(0, F - model_t)``; a genuine per-plant floor binds at least this
    much and generally more (a plant can sit under its own floor while the fleet
    total is above F).
    """
    m = model_cc_chp(year)
    F = a3["sum_plant_p01_mw"]
    deficit = np.maximum(0.0, F - m.to_numpy())
    forced_mwh = float(deficit.sum())
    model_twh = float(m.sum() / 1e6)
    bench = bench_cc_chp(year)
    return {
        "candidate_floor_mw": round(F, 1),
        "n_hours_binding_fleet_grain": int((deficit > 0).sum()),
        "forced_mwh_lower_bound": round(forced_mwh, 1),
        "forced_twh_lower_bound": round(forced_mwh / 1e6, 5),
        "model_twh": round(model_twh, 4),
        "bench_twh": round(bench, 4),
        "current_volume_error_twh": round(model_twh - bench, 4),
        "volume_error_after_floor_twh": round(
            model_twh + forced_mwh / 1e6 - bench, 4
        ),
        "forced_share_of_class": round(forced_mwh / (model_twh * 1e6), 6),
        "note": (
            "The floor can only RAISE output, so it repairs the p01 under-run and "
            "moves the p05/p25 over-run and the class volume error further in the "
            "wrong direction. Both magnitudes are reported so the trade is explicit."
        ),
    }


# ---------------------------------------------------------------- A7
def gate_a7(year: int, chpset: set[int]) -> dict:
    """Can ANY floor mechanism help — what is the SIGN of the CC_CHP gap?

    Every floor (steam-host, lay-up, commitment bridge, class min-gen) is a
    lower bound: it can only RAISE output. So a floor can only help in hours
    where the model runs BELOW the market. This gate measures the sign of the
    model-minus-measured gap hour by hour, on the level-anchored basis
    nyiso-170 established (one factor, ``benchmark_TWh / CAMPD_TWh``, which
    preserves the annual level error exactly and compares shape only).

    Reported both over all hours and with the A5b availability hours removed,
    because a floor is inert in those by construction.
    """
    wide = campd_cc_chp_by_plant(year, chpset)
    meas = wide.sum(axis=1)
    twh = float(meas.sum() / 1e6)
    anchor_f = (bench_cc_chp(year) / twh) if twh > 0 else float("nan")
    meas_a = meas * anchor_f
    m = model_cc_chp(year)

    thr = float(np.percentile(m.to_numpy(), 1))
    low = (m <= max(thr, 1.0)).to_numpy()

    gap = (m - meas_a).to_numpy()
    keep = ~low
    return {
        "campd_twh": round(twh, 4),
        "bench_twh": round(bench_cc_chp(year), 4),
        "anchor": round(float(anchor_f), 4),
        "share_hours_model_above_all": round(float((gap > 0).mean()), 4),
        "share_hours_model_above_ex_availability": round(
            float((gap[keep] > 0).mean()), 4
        ),
        "mean_gap_mw_all": round(float(gap.mean()), 1),
        "mean_gap_mw_ex_availability": round(float(gap[keep].mean()), 1),
        "verdict": (
            "MODEL OVER-RUNS in the large majority of hours — no floor mechanism "
            "can address this object, because a floor only raises output"
            if float((gap[keep] > 0).mean()) > 0.5
            else "model under-runs in a majority of hours — a floor is directionally right"
        ),
    }


def main() -> int:
    chpset = chp_plants()
    out: dict = {
        "probe": "nyiso171_chp_floor_identification",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "bundle": KEEPER.name,
        "solves": 0,
        "years": list(YEARS),
        "gates": {
            "A3_min_coverage": A3_MIN_COVERAGE,
            "A4_silent_twh": A4_SILENT_TWH,
        },
        "A1_rule19_attribution": gate_a1(),
        "A2_model_structural_floor": gate_a2(),
        "A3_A4_measured_floor": {},
        "A5_collapse_hours": {},
        "A5b_outage_vs_economics": {},
        "A6_sizing": {},
        "A7_gap_sign": {},
    }

    print("\n=== A1  rule 19 [R-ONE-MECH] — what already floors CC_CHP ===")
    a1 = out["A1_rule19_attribution"]
    print(f"  mechanisms: {a1['mechanisms']}")
    for y, r in a1["by_year"].items():
        print(
            f"  {y}  {r['mechanism']:12s} forced {r['forced_twh']:.4f} TWh "
            f"of {r['class_total_twh']:.3f} = {r['share_of_class']*100:.2f}% of class"
        )
    print(f"  {a1['verdict']}")

    print("\n=== A2  the model's structural floor, per plant ===")
    a2 = out["A2_model_structural_floor"]
    print(
        f"  CC_CHP nameplate {a2['fleet_nameplate_mw']:,.0f} MW over "
        f"{a2['n_plants']} plants; fleet structural floor "
        f"{a2['fleet_structural_floor_mw']:,.1f} MW"
    )
    print(
        f"  plants with a ZERO floor: {a2['n_plants_zero_floor']}/{a2['n_plants']} "
        f"= {a2['nameplate_share_zero_floor']*100:.1f}% of nameplate"
    )
    print(f"  every CAMPD-visible plant zero-floored: {a2['campd_visible_all_zero']}")
    for p in a2["plants"][:8]:
        print(
            f"    {p['plant']:6d} {p['name'][:34]:34s} {p['status']:10s} "
            f"cap {p['nameplate_mw']:7.1f}  pmin_cf {p['chp_pmin_cf']:5.1f}  "
            f"median_cf {str(p['median_cf']):>6s}  floor {p['floor_mw']:7.1f}"
        )

    for y in YEARS:
        a3 = gate_a3_a4(y, chpset)
        out["A3_A4_measured_floor"][str(y)] = a3
        out["A5_collapse_hours"][str(y)] = gate_a5(y)
        out["A5b_outage_vs_economics"][str(y)] = gate_a5b(y)
        out["A6_sizing"][str(y)] = gate_a6(y, chpset, a3)
        out["A7_gap_sign"][str(y)] = gate_a7(y, chpset)

    print("\n=== A3/A4  THE STOP CONDITION — per-plant physics or portfolio artifact? ===")
    for y in YEARS:
        a3 = out["A3_A4_measured_floor"][str(y)]
        print(
            f"  {y}  fleet min {a3['fleet_min_mw']:7.1f}  p01 {a3['fleet_p01_mw']:7.1f} "
            f"| sum of plant mins {a3['sum_plant_min_mw']:6.1f}  "
            f"sum of plant p01s {a3['sum_plant_p01_mw']:6.1f}"
        )
        print(
            f"        coverage(min) {a3['coverage_min']:.3f}  coverage(p01) "
            f"{a3['coverage_p01']:.3f}  plants never off "
            f"{a3['n_plants_never_off']}/{a3['n_plants_campd']}  "
            f"silent meters {a3['n_silent_meters']}  -> {a3['verdict']}"
        )

    print("\n=== A5  are the model's collapse hours outage or economics? ===")
    for y in YEARS:
        a5 = out["A5_collapse_hours"][str(y)]
        print(
            f"  {y}  low hours {a5['n_low_hours']:4d} in {a5['n_runs']:3d} runs "
            f"(longest {a5['longest_run_h']:3d} h, median {a5['median_run_h']:.0f} h, "
            f"{a5['share_in_runs_ge_24h']*100:.0f}% in runs >= 24 h) over "
            f"{a5['n_distinct_days']} days  -> {a5['verdict']}"
        )

    print("\n=== A5b  the STRONG discriminator: price and total gas in those hours ===")
    for y in YEARS:
        b = out["A5b_outage_vs_economics"][str(y)]
        print(
            f"  {y}  price ${b['block_mean_price']:7.2f} vs yr ${b['year_mean_price']:6.2f} "
            f"({b['price_ratio']:.2f}x)   TOTAL GAS {b['block_total_gas_mw']:7.1f} vs yr "
            f"{b['year_total_gas_mw']:7.1f} MW ({b['gas_ratio']:.3f}x)"
        )
        print(f"        by class: {b['block_mean_by_gas_class_mw']}")
        print(f"        -> {b['verdict']}")

    print("\n=== A6  sizing, and the honest direction ===")
    for y in YEARS:
        a6 = out["A6_sizing"][str(y)]
        print(
            f"  {y}  floor {a6['candidate_floor_mw']:6.1f} MW binds "
            f"{a6['n_hours_binding_fleet_grain']:4d} h  forces >= "
            f"{a6['forced_twh_lower_bound']:.5f} TWh "
            f"({a6['forced_share_of_class']*100:.3f}% of class)"
        )
        print(
            f"        class volume error {a6['current_volume_error_twh']:+.4f} -> "
            f"{a6['volume_error_after_floor_twh']:+.4f} TWh"
        )

    print("\n=== A7  can ANY floor help — the SIGN of the gap ===")
    for y in YEARS:
        g = out["A7_gap_sign"][str(y)]
        print(
            f"  {y}  anchor {g['anchor']:.3f}  model above measured in "
            f"{g['share_hours_model_above_all']*100:5.1f}% of all hours, "
            f"{g['share_hours_model_above_ex_availability']*100:5.1f}% excluding "
            f"availability hours   mean gap {g['mean_gap_mw_ex_availability']:+7.1f} MW"
        )
        print(f"        -> {g['verdict']}")

    OUT.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

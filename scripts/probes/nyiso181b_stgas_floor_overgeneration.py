"""nyiso-181 (``stgas-floor`` lane) — adjudicate the 2023 ``ST_GAS`` OVER-generation object.

Runs every gate fixed in ``results/calibration/PREREG-nyiso181-stgas-floor-overgeneration.md``
before this file existed: the three instrument checks (I1 bundle identity, I2 class closure,
I3 the reduced-cost identity that licenses ``mc > price`` as "out of the money"), the
forced/marginal/economic partition of ``ST_GAS`` dispatch on the LP's OWN installed offer, the
H1 per-hour driver test (forced energy landing in hours the plant's own CAMPD meter reads
zero), the H2 unforced-excess test, and the P3 between-year falsifier.

ZERO SOLVE for the adjudication itself: dispatch, offer and reduced cost come from the
committed ``unit_hourly_stgas_<year>.parquet`` slice, prices from the keeper's own
``system_<year>.parquet``, and the floor matrices from
``legitimacy_diagnostics.load_or_rebuild_floors`` — the D-2/D-4 gate's own basis, imported
rather than re-implemented, so every measured number here is the one the committed gates score
on (the ``ct_only`` skip and the span-union vintage guard included).

Usage::

    python3 scripts/probes/nyiso181b_stgas_floor_overgeneration.py \
        --unit-bundle <dir with hourly/unit_hourly_stgas_*.parquet> \
        --keeper-bundle results/calibration/nyiso177_vintage_B1p \
        --out results/calibration/_nyiso181b_stgas_floor_overgeneration.json
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

from scripts.legitimacy_diagnostics import (  # noqa: E402
    at_floor_mask,
    bench_plant_view,
    ct_only_span_union,
    load_bench,
    load_or_rebuild_floors,
)
from src.market_sim.data.floor_mechanisms import (  # noqa: E402
    MECH_NAMES,
    MECH_RELIABILITY_FLOOR,
)

YEARS = (2023, 2024, 2025)
HOURS = 8760
MONEY_EPS = 0.01  # $/MWh — the PREREG §2 partition band
# PREREG §0.2: bench classFull actuals and the dual-fuel oil re-attribution the
# keeper's class_hourly under-counts (nyiso-180 §5). Both are READ, never fitted.
ACTUAL_ST_GAS_TWH = {2023: 8.1406, 2024: 9.9132, 2025: 13.7121}


def _zone_price(bundle: Path, year: int) -> dict[str, np.ndarray]:
    """``{zone: (8760,) $/MWh}`` from a bundle's own P1 system sidecar."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    out: dict[str, np.ndarray] = {}
    for z, g in df.groupby("zone", observed=True):
        arr = np.zeros(HOURS)
        arr[g["hour"].to_numpy(int)] = g["price"].to_numpy(float)
        out[str(z)] = arr
    return out


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return df[df["pass"] == "P1"]


def i1_bundle_identity(unit_bundle: Path, keeper: Path) -> dict:
    """I1 — the unit bundle must BE the keeper, cell for cell (PREREG §2)."""
    rows = []
    for y in YEARS:
        a = (
            _class_hourly(unit_bundle, y)
            .set_index(["klass", "hour"])["mw"]
            .sort_index()
        )
        b = _class_hourly(keeper, y).set_index(["klass", "hour"])["mw"].sort_index()
        joined = a.align(b, join="outer")
        cls_diff = int((joined[0].fillna(-1) != joined[1].fillna(-1)).sum())
        cls_max = float(np.nanmax(np.abs(joined[0] - joined[1]))) if len(a) else 0.0
        pa, pb = _zone_price(unit_bundle, y), _zone_price(keeper, y)
        zones = sorted(set(pa) | set(pb))
        pr_diff = sum(
            int((pa.get(z, np.zeros(HOURS)) != pb.get(z, np.zeros(HOURS))).sum())
            for z in zones
        )
        pr_max = max(
            float(
                np.max(np.abs(pa.get(z, np.zeros(HOURS)) - pb.get(z, np.zeros(HOURS))))
            )
            for z in zones
        )
        rows.append(
            {
                "year": y,
                "class_cells": int(len(joined[0])),
                "class_cells_differing": cls_diff,
                "class_max_abs_delta": round(cls_max, 9),
                "price_cells": len(zones) * HOURS,
                "price_cells_differing": pr_diff,
                "price_max_abs_delta": round(pr_max, 9),
            }
        )
    ok = all(
        r["class_cells_differing"] == 0 and r["price_cells_differing"] == 0
        for r in rows
    )
    return {
        "bar": "0 differing class-hour cells and 0 differing zonal prices",
        "rows": rows,
        "verdict": "PASS" if ok else "FAIL",
    }


def load_units(unit_bundle: Path, year: int) -> pd.DataFrame:
    """The P1 ``ST_GAS`` unit-hours of the slice.

    The committed slice is cut on FUEL (``gas_st``), so it carries the
    ``ST_CHP`` plant group as well; ``plant_group`` is the pre-re-attribution
    class key (nyiso-180 ``klass_base``), so filtering it here is what makes
    I2's closure against ``class_hourly``'s ``ST_GAS`` exact.
    """
    df = pd.read_parquet(unit_bundle / "hourly" / f"unit_hourly_stgas_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["plant_group"].astype(str) == "ST_GAS")]
    return df.copy()


def i2_class_closure(unit_bundle: Path, keeper: Path) -> dict:
    """I2 — the slice must reproduce the keeper's class + its oil re-attribution."""
    rows = []
    for y in YEARS:
        u = load_units(unit_bundle, y)
        slice_twh = float(u["mw"].sum()) / 1e6
        ch = _class_hourly(keeper, y)
        st = float(ch.loc[ch["klass"] == "ST_GAS", "mw"].sum()) / 1e6
        # The class_hourly ST_GAS undercount is the oil-switched energy of THIS
        # class; bound it by the whole pooled oil class (nyiso-180 §5's own
        # strict upper bound), and report the slice as the reference.
        oil = float(ch.loc[ch["klass"] == "oil", "mw"].sum()) / 1e6
        rows.append(
            {
                "year": y,
                "unit_slice_twh": round(slice_twh, 6),
                "class_hourly_ST_GAS_twh": round(st, 6),
                "class_hourly_oil_twh": round(oil, 6),
                "undercount_twh": round(slice_twh - st, 6),
                "within_oil_bound": bool(-1e-6 <= (slice_twh - st) <= oil + 1e-6),
                "closes": bool(abs(slice_twh - st) <= oil + 1e-6),
            }
        )
    ok = all(r["within_oil_bound"] for r in rows)
    return {
        "bar": "slice = class_hourly ST_GAS + a non-negative share of the pooled oil class",
        "rows": rows,
        "verdict": "PASS" if ok else "FAIL",
    }


def attach_price(u: pd.DataFrame, prices: dict[str, np.ndarray]) -> pd.DataFrame:
    zone = u["zone"].astype(str).to_numpy()
    hour = u["hour"].to_numpy(int)
    p = np.zeros(len(u))
    for z, arr in prices.items():
        m = zone == z
        if m.any():
            p[m] = arr[hour[m]]
    u = u.copy()
    u["price"] = p
    u["omega"] = u["red_cost"].to_numpy(float) - (u["mc"].to_numpy(float) - p)
    return u


def i3_identity(frames: dict[int, pd.DataFrame]) -> dict:
    """I3 — Omega ~ 0, which licenses reading ``mc > price`` as out-of-the-money."""
    rows = []
    for y, u in frames.items():
        om = np.abs(u["omega"].to_numpy(float))
        rows.append(
            {
                "year": y,
                "unit_hours": int(len(u)),
                "omega_p50": round(float(np.percentile(om, 50)), 9),
                "omega_p95": round(float(np.percentile(om, 95)), 9),
                "omega_max": round(float(om.max()), 6),
            }
        )
    ok = all(r["omega_p95"] <= MONEY_EPS for r in rows)
    return {
        "bar": "p95 |omega| <= $0.01/MWh",
        "rows": rows,
        "verdict": "PASS" if ok else "FAIL",
    }


def floors_for(unit_bundle: Path, year: int) -> pd.DataFrame:
    """Unit-grain ``(unit_id, hour) -> min_gen, mechanism`` on the D-2 gate's basis."""
    arrays, ra_missing = load_or_rebuild_floors(unit_bundle, "NYISO", year)
    uids = np.asarray(arrays["unit_ids"], dtype=str)
    mg = np.asarray(arrays["min_gen"], dtype=float)
    mech = np.asarray(arrays["mechanism"], dtype=np.int64)
    n, t = mg.shape
    df = pd.DataFrame(
        {
            "unit_id": np.repeat(uids, t),
            "hour": np.tile(np.arange(t), n),
            "min_gen": mg.reshape(-1),
            "mech": mech.reshape(-1),
        }
    )
    df.attrs["ra_floor_missing"] = ra_missing
    return df


def partition(u: pd.DataFrame) -> pd.DataFrame:
    """PREREG §2: assign every dispatched unit-hour to exactly one of A / B / C."""
    d = u["mc"].to_numpy(float) - u["price"].to_numpy(float)
    band = np.where(
        d > MONEY_EPS,
        "A_out_of_money",
        np.where(d < -MONEY_EPS, "C_in_money", "B_marginal"),
    )
    u = u.copy()
    u["band"] = band
    return u


def measured_view(year: int, ct_union: set[str]) -> dict[str, np.ndarray]:
    """Per-plant measured CAMPD MW on D-4's own basis, ``ct_only`` plants dropped."""
    view = bench_plant_view(load_bench(REPO, "NYISO", year))
    return {
        code: np.asarray(b["mw"], float)[:HOURS]
        for code, b in view.items()
        if not (b.get("ct_only") or code in ct_union)
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--unit-bundle", required=True, type=Path)
    ap.add_argument("--keeper-bundle", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args(argv)

    report: dict = {
        "probe": "nyiso181b_stgas_floor_overgeneration",
        "prereg": "results/calibration/PREREG-nyiso181-stgas-floor-overgeneration.md",
        "unit_bundle": str(a.unit_bundle),
        "keeper_bundle": str(a.keeper_bundle),
    }

    report["I1_bundle_identity"] = i1_bundle_identity(a.unit_bundle, a.keeper_bundle)
    report["I2_class_closure"] = i2_class_closure(a.unit_bundle, a.keeper_bundle)

    frames: dict[int, pd.DataFrame] = {}
    for y in YEARS:
        frames[y] = attach_price(
            load_units(a.unit_bundle, y), _zone_price(a.keeper_bundle, y)
        )
    report["I3_reduced_cost_identity"] = i3_identity(frames)

    ct_union = ct_only_span_union(REPO, "NYISO", list(YEARS))
    report["ct_only_union"] = sorted(ct_union)

    years_out: dict[str, dict] = {}
    for y in YEARS:
        u = partition(frames[y])
        fl = floors_for(a.unit_bundle, y)
        u = u.merge(fl, on=["unit_id", "hour"], how="left")
        u["min_gen"] = u["min_gen"].fillna(0.0)
        u["mech"] = u["mech"].fillna(0).astype(int)
        # at-floor on the D-2 gate's own tolerance, evaluated per unit-hour
        mw = u["mw"].to_numpy(float)[None, :]
        mg = u["min_gen"].to_numpy(float)[None, :]
        u["at_floor"] = at_floor_mask(mw, mg)[0]

        tot = float(u["mw"].sum()) / 1e6
        by_band = (
            (u.groupby("band", observed=True)["mw"].sum() / 1e6).round(6).to_dict()
        )
        forced = u[u["at_floor"]]
        by_mech = {
            MECH_NAMES.get(int(m), str(int(m))): round(float(g["mw"].sum()) / 1e6, 6)
            for m, g in forced.groupby("mech", observed=True)
            if int(m) != 0
        }
        # A split by mechanism: out-of-the-money energy that IS at a floor, and
        # the residue that is out of the money at no floor at all.
        a_mask = u["band"] == "A_out_of_money"
        a_at_floor = float(u.loc[a_mask & u["at_floor"], "mw"].sum()) / 1e6
        a_by_mech = {
            MECH_NAMES.get(int(m), str(int(m))): round(float(g["mw"].sum()) / 1e6, 6)
            for m, g in u[a_mask & u["at_floor"]].groupby("mech", observed=True)
            if int(m) != 0
        }

        # ---- H1: forced energy in hours the plant's own meter reads zero ----
        meas = measured_view(y, ct_union)
        rf = u[u["at_floor"] & (u["mech"] == MECH_RELIABILITY_FLOOR)]
        z_rows = []
        z_total = 0.0
        rf_scored = 0.0
        for code, g in rf.groupby("plant_code", observed=True):
            key = str(int(code))
            series = meas.get(key)
            floored = float(g["mw"].sum()) / 1e6
            if series is None:
                z_rows.append(
                    {
                        "plant": key,
                        "floored_twh": round(floored, 6),
                        "status": "unmetered_or_ct_only",
                    }
                )
                continue
            rf_scored += floored
            m0 = series[g["hour"].to_numpy(int)] <= 0.0
            zt = float(g["mw"].to_numpy(float)[m0].sum()) / 1e6
            z_total += zt
            z_rows.append(
                {
                    "plant": key,
                    "floored_twh": round(floored, 6),
                    "binding_hours": int(len(g)),
                    "meter_zero_hours": int(m0.sum()),
                    "meter_zero_share_hours": round(float(m0.mean()), 4),
                    "Z_twh": round(zt, 6),
                    "Z_share_of_plant": round(zt / floored, 4) if floored > 0 else None,
                    "status": "scored",
                }
            )
        rf_total = float(rf["mw"].sum()) / 1e6
        z_rows.sort(key=lambda r: -(r.get("Z_twh") or 0.0))
        top2 = sum((r.get("Z_twh") or 0.0) for r in z_rows[:2])

        model = tot
        actual = ACTUAL_ST_GAS_TWH[y]
        a_twh = by_band.get("A_out_of_money", 0.0)
        years_out[str(y)] = {
            "model_class_twh": round(model, 6),
            "actual_class_twh": actual,
            "miss_twh": round(model - actual, 6),
            "partition_twh": by_band,
            "forced_at_floor_twh": round(float(forced["mw"].sum()) / 1e6, 6),
            "forced_by_mechanism_twh": by_mech,
            "A_at_floor_twh": round(a_at_floor, 6),
            "A_at_floor_by_mechanism_twh": a_by_mech,
            "A_not_at_any_floor_twh": round(a_twh - a_at_floor, 6),
            "reliability_floor_forced_twh": round(rf_total, 6),
            "reliability_floor_scored_twh": round(rf_scored, 6),
            "H1_Z_twh": round(z_total, 6),
            "H1_Z_share_of_mechanism": round(z_total / rf_total, 4)
            if rf_total > 0
            else None,
            "H1_Z_share_of_miss": round(z_total / (model - actual), 4)
            if (model - actual) > 0
            else None,
            "H1_top2_share_of_Z": round(top2 / z_total, 4) if z_total > 0 else None,
            "H1_plants": z_rows,
            "H2_unforced_excess_twh": round((model - a_twh) - actual, 6),
            "H2_BC_share": round(
                (by_band.get("B_marginal", 0.0) + by_band.get("C_in_money", 0.0))
                / model,
                4,
            )
            if model > 0
            else None,
        }
    report["years"] = years_out

    # ---- P3: the between-year falsifier ----
    d_a = years_out["2023"]["partition_twh"].get("A_out_of_money", 0.0) - years_out[
        "2024"
    ]["partition_twh"].get("A_out_of_money", 0.0)
    d_miss = years_out["2023"]["miss_twh"] - years_out["2024"]["miss_twh"]
    report["P3_between_year"] = {
        "delta_A_2023_minus_2024_twh": round(d_a, 6),
        "delta_miss_2023_minus_2024_twh": round(d_miss, 6),
        "share_explained": round(d_a / d_miss, 4) if d_miss else None,
        "bar": "< 0.25 predicted (the forced term must NOT carry the swing)",
    }

    y23 = years_out["2023"]
    report["predictions"] = {
        "P1a_rule17_violation": {
            "bar": ">= 0.05 of the reliability_floor's forced ST_GAS energy",
            "measured": y23["H1_Z_share_of_mechanism"],
        },
        "P1b_material_carrier": {
            "bar": ">= 0.97 TWh (25% of the +3.879 TWh miss)",
            "measured": y23["H1_Z_twh"],
        },
        "P1c_membership_signature": {
            "bar": ">= 0.60 of Z in the top-2 plants",
            "measured": y23["H1_top2_share_of_Z"],
        },
        "P2a_unforced_excess": {
            "bar": ">= 0.97 TWh",
            "measured": y23["H2_unforced_excess_twh"],
        },
        "P2b_between_year_BC": {
            "bar": ">= 5pp above 2024's B+C share",
            "measured": round(
                (y23["H2_BC_share"] or 0) - (years_out["2024"]["H2_BC_share"] or 0), 4
            ),
        },
    }

    # ------------------------------------------------------------------ #
    # POST-HOC (added after the gates above were computed; moves no bar and
    # changes no pre-registered number). Both pre-registered hypotheses are
    # CLASS-AGGREGATE tests, and the class aggregate turns out to be a
    # CANCELLATION, so the aggregate cannot see what the plant grain does.
    # ------------------------------------------------------------------ #
    posthoc: dict = {
        "note": "POST-HOC. Computed after the pre-registered gates; no gate, bar "
        "or prediction above is affected. Measured = CAMPD gross from the "
        "bench's own ST_GAS class slices (D-4's basis); the class-level "
        "actual in `years` stays the scorer's grid-delivered classFull.",
        "plants": {},
        "grain": {},
        "availability_ratio": {},
    }
    for y in YEARS:
        u = partition(frames[y])
        fl = floors_for(a.unit_bundle, y)
        u = u.merge(fl, on=["unit_id", "hour"], how="left")
        u["min_gen"] = u["min_gen"].fillna(0.0)
        u["mech"] = u["mech"].fillna(0).astype(int)
        u["at_floor"] = at_floor_mask(
            u["mw"].to_numpy(float)[None, :], u["min_gen"].to_numpy(float)[None, :]
        )[0]
        bench = load_bench(REPO, "NYISO", y)
        meas = {
            str(k).split(":")[0]: np.asarray(v["mw"], float)[:HOURS]
            for k, v in bench.items()
            if v.get("group") == "ST_GAS"
        }
        rows = []
        for code, g in u.groupby("plant_code", observed=True):
            key = str(int(code))
            hourly_cap = g.groupby("hour", observed=True)["cap_mw"].sum()
            cap_max = float(hourly_cap.max())
            cap_mean = float(hourly_cap.mean())
            forced = (
                float(
                    g.loc[
                        g["at_floor"] & (g["mech"] == MECH_RELIABILITY_FLOOR), "mw"
                    ].sum()
                )
                / 1e6
            )
            A = float(g.loc[g["band"] == "A_out_of_money", "mw"].sum()) / 1e6
            BC = float(g.loc[g["band"] != "A_out_of_money", "mw"].sum()) / 1e6
            ms = meas.get(key)
            me = float(ms.sum()) / 1e6 if ms is not None else None
            rows.append(
                {
                    "plant": key,
                    "model_twh": round(A + BC, 6),
                    "measured_campd_gross_twh": None if me is None else round(me, 6),
                    "delta_twh": None if me is None else round(A + BC - me, 6),
                    "A_out_of_money_twh": round(A, 6),
                    "BC_unforced_twh": round(BC, 6),
                    "unforced_excess_twh": None if me is None else round(BC - me, 6),
                    "reliability_floor_forced_twh": round(forced, 6),
                    "cap_max_mw": round(cap_max, 1),
                    "model_availability": round(cap_mean / cap_max, 4)
                    if cap_max
                    else None,
                    "measured_cf_of_max": None
                    if (me is None or not cap_max)
                    else round(me * 1e6 / HOURS / cap_max, 4),
                }
            )
        rows.sort(
            key=lambda r: -(abs(r["delta_twh"]) if r["delta_twh"] is not None else 0)
        )
        posthoc["plants"][str(y)] = rows
        posthoc["availability_ratio"][str(y)] = {
            r["plant"]: round(
                r["model_availability"] / max(r["measured_cf_of_max"], 1e-9), 2
            )
            for r in rows
            if r["model_availability"] and r["measured_cf_of_max"] is not None
        }

        # --- grain reconciliation: unit grain vs D-2's plant-sum convention ---
        pv = u.pivot_table(
            index="plant_code",
            columns="hour",
            values=["mw", "min_gen"],
            aggfunc="sum",
            observed=True,
        )
        D, G = pv["mw"].to_numpy(float), pv["min_gen"].to_numpy(float)
        binding = (
            u.sort_values(["plant_code", "hour", "min_gen"])
            .groupby(["plant_code", "hour"], observed=True)
            .tail(1)
        )
        M = (
            binding.pivot_table(
                index="plant_code",
                columns="hour",
                values="mech",
                aggfunc="max",
                observed=True,
            )
            .reindex(pv["mw"].index)
            .to_numpy()
        )
        afp = at_floor_mask(D, G)
        plant_rf = float(D[afp & (M == MECH_RELIABILITY_FLOOR)].sum()) / 1e6
        unit_rf = (
            float(
                u.loc[u["at_floor"] & (u["mech"] == MECH_RELIABILITY_FLOOR), "mw"].sum()
            )
            / 1e6
        )
        cls = float(u["mw"].sum()) / 1e6
        posthoc["grain"][str(y)] = {
            "unit_grain_reliability_floor_twh": round(unit_rf, 6),
            "plant_grain_reliability_floor_twh": round(plant_rf, 6),
            "under_count_twh": round(unit_rf - plant_rf, 6),
            "under_count_share": round((unit_rf - plant_rf) / unit_rf, 4)
            if unit_rf
            else None,
            "unit_grain_class_dispatch_twh": round(cls, 6),
            "unit_grain_forced_share_lower_bound": round(unit_rf / cls, 4)
            if cls
            else None,
            "note": "the unit-grain forced share is a LOWER bound: the rebuilt "
            "floors come from run_year(fleet_only=True) and so exclude the "
            "P1-seam nyiso_gas_commitment_bridge, which the committed D-2 "
            "carries at 0.1135 / 0.1622 / 0.1664 TWh.",
        }
    report["posthoc"] = posthoc

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(report, indent=1))
    print(json.dumps(report["predictions"], indent=1))
    print(json.dumps(report["P3_between_year"], indent=1))
    for y in YEARS:
        r = years_out[str(y)]
        print(
            f"\n{y}: model {r['model_class_twh']:.3f} actual {r['actual_class_twh']:.3f} "
            f"miss {r['miss_twh']:+.3f} | A {r['partition_twh'].get('A_out_of_money', 0):.3f} "
            f"B {r['partition_twh'].get('B_marginal', 0):.3f} "
            f"C {r['partition_twh'].get('C_in_money', 0):.3f} | "
            f"floor {r['reliability_floor_forced_twh']:.3f} Z {r['H1_Z_twh']:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""nyiso-174 phase 0 — WHICH SIDE of the East River (2493) class crosswalk is
wrong, how many other NYISO plants carry the same defect, and what a repair
would actually move.

ZERO SOLVE. No parameter is touched, no band is swept, nothing is registered.
This is an adjudication off committed artifacts + the primary record
(EIA-860 generator prime movers, EIA-923 Page-1 net generation by prime mover,
CAMPD unit-level hourly), in the nyiso-168/169/170/171/172/173 discipline.

The object. East River is ``ST_CHP`` in
``data/raw/_processed-legacy/thermal_tranches_NYISO.csv`` but lands in
``CC_CHP`` under the shared CAMPD ``unitType`` construction that nyiso-169b /
170 / 171 / 172 / 173 all use for their MEASURED series, carrying
2.13-2.19 TWh/yr into the measured CC_CHP comparison series. One of the two
classifications is wrong; the brief forbids picking the flattering one.

Four measurements, in the brief's own order:

* **M1 WHICH SIDE IS WRONG.** East River's prime-mover composition from the
  PRIMARY record: EIA-860 ``Prime Mover`` / ``Technology`` per generator,
  EIA-923 Page-1 net generation by prime mover, and the CAMPD unit roster with
  each unit's MEASURED heat rate and steam export. Reported against both
  candidate classifications and against the model's own loaded fleet.

* **M2 HOW MANY OTHER PLANTS.** The crosswalk run BOTH WAYS over the whole
  NYISO fleet: every CAMPD NY unit-year whose ``unitType``-assigned class is
  not one the model's EIA-860 fleet carries for that plant, with its measured
  TWh. A one-plant repair and a systematic crosswalk defect are different
  tasks; this decides which.

* **M3 WHAT THE REPAIR MOVES.** The basis of each downstream number is
  established rather than assumed: nyiso-169b measurement A (the C1 class
  volume errors) is recomputed to show which construction it rests on, and the
  nyiso-170 section 3 CEMS-identifiability anchor table is recomputed on the
  corrected construction. A conclusion that flips is the finding.

* **M4 RULE 19 [R-ONE-MECH] ENUMERATION.** Every mechanism whose eligibility
  for plant 2493 is keyed on ``plant_group``, read off the engine, so any
  reclassification REPLACES rather than stacks.

Rule 13 [R-MEASURED]: every input here is a reproducible measured record used
for CLASSIFICATION identification only; nothing is pinned to an outcome and no
statistic is tuned to a residual. Rule 14 [R-ACCURATE]: the primary record
decides, not the backcast. Rule 22 [R-HOLDOUT]: 2023-2025 only.

Run: ``PYTHONPATH=.:src python scripts/probes/nyiso174_class_crosswalk_audit.py``
Writes: ``results/calibration/_nyiso174_class_crosswalk_audit.json``
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)

YEARS = (2023, 2024, 2025)
BENCH = REPO / "frontend/data/backcast/bench/NYISO"
KEEPER = REPO / "results/calibration/nyiso159_lossarm_B"
OUT = REPO / "results/calibration/_nyiso174_class_crosswalk_audit.json"

#: The plant under adjudication — Con Edison East River, Manhattan.
EAST_RIVER = 2493

#: The gas classes the CEMS-identifiability anchor table (nyiso-170 section 3)
#: covers.
ANCHOR_CLASSES = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")


# ----------------------------------------------------------------- loaders --


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination."""
    flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
    return {int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"}


def campd_unit_class(
    unit_type: object, facility_id: int, chpset: set[int]
) -> str | None:
    """The class the SHARED CAMPD ``unitType`` construction assigns to a unit.

    Thin wrapper over :func:`scripts.lib.campd_measured_classes
    .campd_unittype_class` — the one construction, so this probe's "old basis"
    and the helper can never drift. Reproduces nyiso-172's ``class_mask`` in
    per-row form (verified against nyiso-171's committed A3 numbers in M5).
    """
    return campd_unittype_class(unit_type, facility_id in chpset)


def model_groups_by_plant(year: int) -> dict[int, dict[str, float]]:
    """``{plant_code: {plant_group: capacity MW}}`` from the model's own fleet.

    This is the PRIMARY-RECORD side: ``load_fleet_from_csv`` builds each NYISO
    unit from an EIA-860 generator row and classes it through the canonical
    :func:`market_sim.config.plant_taxonomy.classify_plant` — the same
    classifier the EIA-923 class benchmark (``classFull``) uses, so the model
    and the thing it is scored against are on one basis by construction.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    out: dict[int, dict[str, float]] = {}
    for g in load_fleet_from_csv("NYISO", get_iso_config("NYISO"), year=year):
        code = int(g.plant_code)
        if code <= 0 or not g.plant_group:
            continue
        out.setdefault(code, {})
        out[code][g.plant_group] = out[code].get(g.plant_group, 0.0) + float(g.pmax_mw)
    return out


def campd_units(year: int) -> pd.DataFrame:
    """CAMPD NY unit-year roster: gross TWh, fuel MMBtu, steam export, op-hours.

    ``grossLoad`` is filled to zero explicitly — CAMPD reports NULL for a
    non-operating unit-hour, and a NULL-propagating aggregation silently
    returns NaN (the nyiso-173 trap (d)).
    """
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=[
            "facilityId",
            "facilityName",
            "unitId",
            "unitType",
            "grossLoad",
            "steamLoad",
            "heatInput",
            "opTime",
        ],
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d["steamLoad"] = d["steamLoad"].fillna(0.0)
    d["heatInput"] = d["heatInput"].fillna(0.0)
    d["opTime"] = d["opTime"].fillna(0.0)
    d["facilityId"] = d["facilityId"].astype(int)
    g = d.groupby(
        ["facilityId", "facilityName", "unitId", "unitType"], as_index=False
    ).agg(
        gross_twh=("grossLoad", lambda s: float(s.sum()) / 1e6),
        mmbtu=("heatInput", "sum"),
        steam_klb=("steamLoad", "sum"),
        op_hours=("opTime", "sum"),
        peak_mw=("grossLoad", "max"),
    )
    g["year"] = year
    return g


def bench_classes(year: int) -> dict[str, float]:
    """Committed grid-delivered class volumes (``classFull``), TWh."""
    with gzip.open(BENCH / f"{year}.json.gz") as fh:
        return json.load(fh)["bench"]["classFull"]


def model_class_twh(year: int) -> dict[str, float]:
    """The keeper's own P1 class volumes, TWh (rule 15: read, don't replay)."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    s = c[c["pass"] == "P1"].groupby("klass")["mw"].sum() / 1e6
    return {str(k): float(v) for k, v in s.items()}


# ------------------------------------------------------------ measurements --


def m1_east_river() -> dict:
    """M1 — East River's prime-mover composition from the primary record."""
    gen = pd.read_parquet(RAW_DATA_DIR / "eia-860/eia860_generator_operable.parquet")
    e = gen[gen["Plant Code"] == EAST_RIVER]
    eia860 = [
        {
            "generator_id": str(r["Generator ID"]).strip(),
            "technology": str(r["Technology"]),
            "prime_mover": str(r["Prime Mover"]).strip().upper(),
            "nameplate_mw": float(r["Nameplate Capacity (MW)"]),
            "summer_mw": float(r["Summer Capacity (MW)"]),
            "winter_mw": float(r["Winter Capacity (MW)"]),
            "min_load_mw": float(r["Minimum Load (MW)"]),
            "operating_year": int(r["Operating Year"]),
            "chp_flag": str(r["Associated with Combined Heat and Power System"]),
        }
        for _, r in e.iterrows()
    ]

    g923 = pd.read_parquet(
        RAW_DATA_DIR / "_processed-legacy/eia923_monthly_generation.parquet"
    )
    er923 = g923[(g923["plant_id"] == EAST_RIVER) & (g923["year"].isin(YEARS))]
    eia923 = {
        str(y): {
            str(pm): round(float(v) / 1e6, 4)
            for pm, v in sub.groupby("prime_mover")["netgen_annual_mwh"].sum().items()
        }
        for y, sub in er923.groupby("year")
    }

    campd = {}
    for y in YEARS:
        u = campd_units(y)
        e_u = u[u["facilityId"] == EAST_RIVER]
        campd[str(y)] = [
            {
                "unit_id": str(r["unitId"]),
                "unit_type": str(r["unitType"]),
                "gross_twh": round(float(r["gross_twh"]), 4),
                "peak_mw": float(r["peak_mw"]),
                "op_hours": round(float(r["op_hours"]), 1),
                "steam_klb": round(float(r["steam_klb"]), 0),
                "measured_hr": (
                    round(float(r["mmbtu"]) / (float(r["gross_twh"]) * 1e6), 3)
                    if float(r["gross_twh"]) > 0
                    else None
                ),
            }
            for _, r in e_u.iterrows()
        ]

    mg = model_groups_by_plant(2025)
    return {
        "eia860_generators": eia860,
        "eia860_prime_movers": sorted({g["prime_mover"] for g in eia860}),
        "eia860_has_combined_cycle_prime_mover": any(
            g["prime_mover"] in {"CA", "CT", "CS"} for g in eia860
        ),
        "eia860_summer_mw_by_prime_mover": {
            pm: round(sum(g["summer_mw"] for g in eia860 if g["prime_mover"] == pm), 1)
            for pm in sorted({g["prime_mover"] for g in eia860})
        },
        "eia923_netgen_twh_by_prime_mover": eia923,
        "campd_units": campd,
        "model_fleet_groups_mw": {
            k: round(v, 1) for k, v in mg.get(EAST_RIVER, {}).items()
        },
        "campd_unittype_construction_class": "CC_CHP",
    }


def m2_fleet_crosswalk() -> dict:
    """M2 — the crosswalk run both ways over the whole NYISO fleet."""
    chpset = chp_plants()
    rows = []
    for y in YEARS:
        mg = model_groups_by_plant(y)
        u = campd_units(y)
        u["campd_class"] = [
            campd_unit_class(t, f, chpset)
            for t, f in zip(u["unitType"], u["facilityId"])
        ]
        u["model_classes"] = u["facilityId"].map(
            lambda c: ",".join(sorted(mg.get(int(c), {}))) or "ABSENT-FROM-MODEL"
        )
        u["agrees"] = [
            (r["campd_class"] in mg.get(int(r["facilityId"]), {}))
            for _, r in u.iterrows()
        ]
        rows.append(u)
    allu = pd.concat(rows, ignore_index=True)
    dis = allu[~allu["agrees"]]

    by_plant = (
        dis.groupby(["facilityId", "facilityName", "campd_class", "model_classes"])[
            "gross_twh"
        ]
        .sum()
        .reset_index()
        .sort_values("gross_twh", ascending=False)
    )
    present = by_plant[by_plant["model_classes"] != "ABSENT-FROM-MODEL"]
    absent = by_plant[by_plant["model_classes"] == "ABSENT-FROM-MODEL"]
    er_twh = float(present[present["facilityId"] == EAST_RIVER]["gross_twh"].sum())
    present_twh = float(present["gross_twh"].sum())

    return {
        "unit_years_total": int(len(allu)),
        "unit_years_disagreeing": int(len(dis)),
        "campd_twh_by_year": {
            str(y): round(float(allu[allu["year"] == y]["gross_twh"].sum()), 4)
            for y in YEARS
        },
        "disagreeing_twh_by_year": {
            str(y): round(float(dis[dis["year"] == y]["gross_twh"].sum()), 4)
            for y in YEARS
        },
        "misclassed_3yr_twh": round(present_twh, 4),
        "absent_from_model_3yr_twh": round(float(absent["gross_twh"].sum()), 4),
        "east_river_3yr_twh": round(er_twh, 4),
        "east_river_share_of_misclassed": (
            round(er_twh / present_twh, 4) if present_twh else None
        ),
        "misclassed_plants": [
            {
                "plant_code": int(r["facilityId"]),
                "name": str(r["facilityName"]).strip(),
                "campd_unittype_class": str(r["campd_class"]),
                "model_classes": str(r["model_classes"]),
                "twh_3yr": round(float(r["gross_twh"]), 6),
            }
            for _, r in present.iterrows()
        ],
        "absent_from_model_top": [
            {
                "plant_code": int(r["facilityId"]),
                "name": str(r["facilityName"]).strip(),
                "campd_unittype_class": str(r["campd_class"]),
                "twh_3yr": round(float(r["gross_twh"]), 6),
            }
            for _, r in absent.head(10).iterrows()
        ],
    }


def m3_what_moves() -> dict:
    """M3 — the basis of each downstream number, and the corrected anchors."""
    chpset = chp_plants()
    out: dict = {"c1_class_errors": {}, "anchor_table": {}}

    # --- (i) the C1 class volume errors (nyiso-169b measurement A) -----------
    # Model P1 vs the COMMITTED benchmark `classFull`. `classFull` is built by
    # `run_calibration_full._benchmark_eia923_frame` -> `_eia923_frame` ->
    # `_classify_f923` -> `plant_taxonomy.classify_plant`, i.e. on the EIA-923
    # PRIME-MOVER basis, the same side as the model fleet — NOT on the CAMPD
    # `unitType` construction. Recomputed here so the claim is measured.
    for y in YEARS:
        b, m = bench_classes(y), model_class_twh(y)
        out["c1_class_errors"][str(y)] = {
            k: {
                "model_twh": round(m.get(k, 0.0), 4),
                "actual_twh": round(b.get(k, 0.0), 4),
                "delta_pct": (
                    round((m.get(k, 0.0) - b[k]) / b[k] * 100, 2)
                    if b.get(k, 0.0)
                    else None
                ),
            }
            for k in ANCHOR_CLASSES
        }

    # --- (ii) the nyiso-170 section 3 CEMS-identifiability anchors -----------
    # anchor = benchmark grid-delivered TWh / CEMS gross TWh, per class, on the
    # OLD (CAMPD unitType) construction and on the CORRECTED one. The corrected
    # construction assigns each CAMPD unit to the class its own plant's EIA-860
    # prime-mover roster carries, matching the unit's prime-mover FAMILY
    # (turbine-fired vs boiler-fired) — no per-plant judgement, and it collapses
    # to the old construction wherever the two agree.
    for y in YEARS:
        mg = model_groups_by_plant(y)
        u = campd_units(y)
        u["old"] = [
            campd_unit_class(t, f, chpset)
            for t, f in zip(u["unitType"], u["facilityId"])
        ]
        u["new"] = [
            _corrected_class(str(r["old"]), mg.get(int(r["facilityId"]), {}))
            for _, r in u.iterrows()
        ]
        b = bench_classes(y)
        row = {}
        for k in ANCHOR_CLASSES:
            old_twh = float(u[u["old"] == k]["gross_twh"].sum())
            new_twh = float(u[u["new"] == k]["gross_twh"].sum())
            bench = float(b.get(k, 0.0))
            row[k] = {
                "cems_units_old": int((u["old"] == k).sum()),
                "cems_units_new": int((u["new"] == k).sum()),
                "cems_gross_twh_old": round(old_twh, 4),
                "cems_gross_twh_new": round(new_twh, 4),
                "bench_twh": round(bench, 4),
                "anchor_old": round(bench / old_twh, 3) if old_twh > 0 else None,
                "anchor_new": round(bench / new_twh, 3) if new_twh > 0 else None,
            }
        out["anchor_table"][str(y)] = row
    return out


def _corrected_class(old: str, plant_groups: dict[str, float]) -> str | None:
    """Reassign one CAMPD unit to the class its own plant's model fleet carries.

    Thin wrapper over :func:`scripts.lib.campd_measured_classes
    .corrected_unit_class`, where the repair and its rationale live.
    """
    return corrected_unit_class(
        None if old in (None, "None", "") else old, plant_groups
    )


def _hourly_by_class(year: int, chpset: set[int]) -> dict[str, dict[str, "pd.Series"]]:
    """Measured hourly MW per class on BOTH constructions, on the 8760 clock."""
    from scripts.data.derive_actual_lmp import _std_hour_index

    mg = model_groups_by_plant(year)
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitId", "unitType", "date", "hour", "grossLoad"],
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)  # nyiso-173 trap (d)
    fid = d["facilityId"].astype(int)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    # STD_TZ: the FIXED standard-time clock (nyiso-173 trap (c) — America/
    # New_York raises a DST nonexistent-time error on 2023-03-12 02:00).
    h = _std_hour_index(
        pd.DatetimeIndex(ts).tz_localize("Etc/GMT+5"), year, "Etc/GMT+5"
    )
    old = pd.Series(
        [campd_unit_class(t, f, chpset) for t, f in zip(d["unitType"], fid)],
        index=d.index,
    )
    new = pd.Series(
        [_corrected_class(str(o), mg.get(int(f), {})) for o, f in zip(old, fid)],
        index=d.index,
    )
    out: dict[str, dict[str, pd.Series]] = {"old": {}, "new": {}}
    for tag, lab in ((old, "old"), (new, "new")):
        for k in ANCHOR_CLASSES:
            sel = (tag == k).to_numpy()
            s = pd.Series(d.loc[sel, "grossLoad"].to_numpy())
            out[lab][k] = (
                s.groupby(h[sel]).sum().reindex(range(8760)).fillna(0.0).astype(float)
            )
    return out


def _plant_minima(year: int, chpset: set[int], klass: str, basis: str) -> dict:
    """Per-plant hourly minimum MW for one class, on either construction.

    ``basis="old"`` reproduces the shared CAMPD ``unitType`` construction (and
    with it nyiso-171's committed A3 numbers, which is the reproduction check);
    ``basis="new"`` uses the corrected per-plant prime-mover assignment.
    """
    from scripts.data.derive_actual_lmp import _std_hour_index

    mg = model_groups_by_plant(year)
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=["facilityId", "unitType", "date", "hour", "grossLoad"],
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    fid = d["facilityId"].astype(int)
    ts = pd.to_datetime(d["date"]) + pd.to_timedelta(d["hour"], unit="h")
    h = _std_hour_index(
        pd.DatetimeIndex(ts).tz_localize("Etc/GMT+5"), year, "Etc/GMT+5"
    )
    old = [str(campd_unit_class(t, f, chpset)) for t, f in zip(d["unitType"], fid)]
    cls = (
        old
        if basis == "old"
        else [_corrected_class(o, mg.get(int(f), {})) for o, f in zip(old, fid)]
    )
    sel = pd.Series(cls, index=d.index).eq(klass).to_numpy()
    sub = pd.DataFrame(
        {
            "fid": fid.to_numpy()[sel],
            "h": h[sel],
            "mw": d["grossLoad"].to_numpy()[sel],
        }
    )
    per = sub.groupby(["fid", "h"])["mw"].sum().unstack("fid").reindex(range(8760))
    per = per.fillna(0.0)
    mins = per.min()
    return {
        "n_plants": int(per.shape[1]),
        "n_plants_reaching_zero": int((mins <= 1.0).sum()),
        "sum_of_plant_minima_mw": round(float(mins.clip(lower=0).sum()), 1),
        "fleet_minimum_mw": round(float(per.sum(axis=1).min()), 1),
        "plants_never_off": [int(c) for c in mins.index[mins > 1.0]],
    }


def m5_downstream_restatement() -> dict:
    """M5 — the probe-side objects restated on the corrected construction.

    Two committed results rest directly on the measured CC / CC_CHP series:
    nyiso-172 section 3.4's one-sided CC availability bound (which nyiso-173
    downgraded to portfolio-only) and nyiso-171's CC_CHP "hard floor". Both are
    recomputed here on both constructions so the change is measured, not
    inferred — and the ``old`` leg doubles as the reproduction check against
    those sessions' committed numbers.
    """
    chpset = chp_plants()
    out: dict = {}
    months = pd.date_range("2023-01-01", periods=8760, freq="h").month.to_numpy()
    for y in YEARS:
        H = _hourly_by_class(y, chpset)
        mc = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        mc = mc[mc["pass"] == "P1"]
        model_cc = (
            mc[mc["klass"].isin(["CC_CHP", "CC_REGULAR"])]
            .groupby("hour")["mw"]
            .sum()
            .reindex(range(8760))
            .fillna(0.0)
            .to_numpy()
        )
        row = {}
        for lab in ("old", "new"):
            meas_cc = (H[lab]["CC_CHP"] + H[lab]["CC_REGULAR"]).to_numpy()
            # The nyiso-172 section 3.4 bound: the measured fleet's within-month
            # maximum is a strict lower bound on that fleet's availability.
            bound = pd.Series(meas_cc).groupby(months).transform("max").to_numpy()
            viol = model_cc > bound
            chp = H[lab]["CC_CHP"].to_numpy()
            row[lab] = {
                "violation_hours": int(viol.sum()),
                "violation_share_pct": round(float(viol.mean()) * 100, 2),
                "mean_gap_mw": (
                    round(float((model_cc - bound)[viol].mean()), 1)
                    if viol.any()
                    else None
                ),
                "measured_cc_twh": round(float(meas_cc.sum()) / 1e6, 4),
                "measured_cc_chp_twh": round(float(chp.sum()) / 1e6, 4),
                "measured_cc_chp_min_mw": round(float(chp.min()), 1),
                "measured_cc_chp_hours_at_zero": int((chp <= 1.0).sum()),
            }
        # nyiso-171's A3 stop condition, re-run on the corrected CC_CHP
        # membership: is the residual class floor built ENTIRELY from plants
        # that each reach zero? East River was its one counter-example.
        row["cc_chp_plant_minima_old"] = _plant_minima(y, chpset, "CC_CHP", "old")
        row["cc_chp_plant_minima_new"] = _plant_minima(y, chpset, "CC_CHP", "new")
        out[str(y)] = row
    return out


def m4_mechanism_enumeration() -> dict:
    """M4 — every mechanism keyed on ``plant_group`` that reaches plant 2493."""
    from market_sim.data import outages

    mg = model_groups_by_plant(2025).get(EAST_RIVER, {})
    tranches = pd.read_csv(
        RAW_DATA_DIR / "_processed-legacy/thermal_tranches_NYISO.csv"
    )
    er_tr = tranches[tranches["plant_code"] == EAST_RIVER]
    bins = pd.read_csv(RAW_DATA_DIR / "_processed-legacy/bin_assignments_NYISO.csv")
    er_bin = bins[bins["Plant_Code"] == EAST_RIVER]

    # The outage router's own decision for each of the plant's CAMPD classes.
    routing = {
        c: (
            None
            if outages._generic_unit_outage_target(EAST_RIVER, "x", c) is None
            else list(outages._generic_unit_outage_target(EAST_RIVER, "x", c))
        )
        for c in ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
    }
    return {
        "model_fleet_groups_mw": {k: round(v, 1) for k, v in mg.items()},
        "tranches_rows": er_tr.to_dict(orient="records"),
        "bin_assignment_rows": er_bin.to_dict(orient="records"),
        "outage_router_targets": routing,
        "fleet_group_override_now": {
            str(k): v for k, v in outages._FLEET_GROUP_OVERRIDE.items()
        },
    }


def main() -> None:
    res = {
        "probe": "nyiso174_class_crosswalk_audit",
        "solves": 0,
        "years": list(YEARS),
        "M1_which_side_is_wrong": m1_east_river(),
        "M2_fleet_crosswalk": m2_fleet_crosswalk(),
        "M3_what_the_repair_moves": m3_what_moves(),
        "M4_mechanism_enumeration": m4_mechanism_enumeration(),
        "M5_downstream_restatement": m5_downstream_restatement(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=1, sort_keys=True))

    m1, m2 = res["M1_which_side_is_wrong"], res["M2_fleet_crosswalk"]
    print("=== M1 East River (2493) — the primary record ===")
    print(
        "  EIA-860 prime movers:",
        m1["eia860_prime_movers"],
        "| combined-cycle prime-mover code present:",
        m1["eia860_has_combined_cycle_prime_mover"],
    )
    print("  EIA-860 summer MW by prime mover:", m1["eia860_summer_mw_by_prime_mover"])
    print("  EIA-923 net TWh by prime mover:", m1["eia923_netgen_twh_by_prime_mover"])
    print("  model fleet groups (MW):", m1["model_fleet_groups_mw"])
    print("  CAMPD 2025 units:")
    for u in m1["campd_units"]["2025"]:
        print(
            f"    {u['unit_id']:>4} {u['unit_type'][:30]:<30} "
            f"gross {u['gross_twh']:>6.3f} TWh  peak {u['peak_mw']:>5.0f} MW  "
            f"HR {u['measured_hr']}  steam {u['steam_klb']:>10.0f} klb"
        )
    print("\n=== M2 the whole-fleet crosswalk ===")
    print(
        f"  {m2['unit_years_disagreeing']} of {m2['unit_years_total']} unit-years "
        f"disagree; {m2['misclassed_3yr_twh']} TWh misclassed + "
        f"{m2['absent_from_model_3yr_twh']} TWh absent from the model"
    )
    print(
        f"  East River is {m2['east_river_3yr_twh']} TWh = "
        f"{m2['east_river_share_of_misclassed']:.1%} of the misclassed volume"
    )
    for p in m2["misclassed_plants"][:6]:
        print(
            f"    {p['plant_code']:>6} {p['name'][:30]:<30} "
            f"{p['campd_unittype_class']:>10} -> {p['model_classes']:<20} "
            f"{p['twh_3yr']:>8.4f} TWh"
        )
    print("\n=== M3 anchors, 2025 (bench / CEMS gross) ===")
    a = res["M3_what_the_repair_moves"]["anchor_table"]["2025"]
    print(f"  {'class':<12} {'old':>8} {'new':>8}   {'units old/new':>14}")
    for k in ANCHOR_CLASSES:
        print(
            f"  {k:<12} {str(a[k]['anchor_old']):>8} {str(a[k]['anchor_new']):>8}"
            f"   {a[k]['cems_units_old']:>6}/{a[k]['cems_units_new']:<7}"
        )
    print("\n=== M5 downstream restatement (old -> corrected) ===")
    m5 = res["M5_downstream_restatement"]
    print(
        f"  {'year':<6} {'CC bound violation h':>22} {'meas CC_CHP TWh':>18} {'CC_CHP min MW':>15}"
    )
    for y in YEARS:
        o, n = m5[str(y)]["old"], m5[str(y)]["new"]
        print(
            f"  {y:<6} {o['violation_hours']:>9} -> {n['violation_hours']:<9}"
            f" {o['measured_cc_chp_twh']:>8.3f} -> {n['measured_cc_chp_twh']:<7.3f}"
            f" {o['measured_cc_chp_min_mw']:>6.0f} -> {n['measured_cc_chp_min_mw']:<6.0f}"
        )
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()

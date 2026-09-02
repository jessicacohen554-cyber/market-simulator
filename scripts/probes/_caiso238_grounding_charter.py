"""caiso-238 — Q2 materiality measurement for the grounding charter.

Measures, from the keeper bundle's OWN COMMITTED ARTIFACTS ONLY (no LP, no
solver, no replay), the live-and-material content of the four class-(c)
residual DOF rows caiso-236 §10 left untouched:

  1. ``offer_curve_by_group`` — the fitted remainder after caiso-231, split by
     whether the group carries any CAISO dispatch at all.
  2. ``offer_curve_committed_below_floor[CAISO]`` (``ST_GAS`` = 0.81) — the
     armed multiplier against the class's OWN CAISO-measured physical min-load
     basis (``phys_committed``), and the class's dispatch share.
  3. ``offer_curve_smoothing_{n,exp}`` — the tranche count the smoother
     actually renders and whether ``exp = 1.0`` is an identity.
  4. ``battery_dispatch_adder`` — the storage discharge share it prices.

Every number is read from ``run_config.json``, the ``hourly/`` sidecars, and
the committed offer-curve registries. Rule 1 ``[R-STRUCT]``: C3a is never this
probe's object and nothing here is argued from the price residual.

Usage::

    uv run python scripts/probes/_caiso238_grounding_charter.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

BUNDLE = Path("results/calibration/caiso231_b1_ungrounded")
MEASURED = Path("data/raw/_validation-source/caiso_offer_curve_measured.json")
OUT = Path("results/calibration/_caiso238_grounding_charter.json")
YEARS = (2023, 2024, 2025)

#: The three price bands caiso-231 re-grounded on the measured buckets, for the
#: five CAISO gas groups it covers (FINDING-caiso231 §2).
MEASURED_BANDS = ("econ_low", "econ_high", "peak")
MEASURED_GROUPS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS")

#: Bucket each CAISO gas group draws its measured bands from
#: (``derive_caiso_offer_surface.py``'s own disclosed contamination note).
BUCKET_OF = {
    "CC_REGULAR": "CC_REGULAR",
    "CC_CHP": "CC_REGULAR",
    "CT_PEAKER": "CT_PEAKER",
    "CT_CHP": "CT_PEAKER",
    "ST_GAS": "CT_PEAKER",
}


def _class_energy() -> dict:
    """Return per-class P1 energy (TWh) and share of the CAISO gas fleet."""
    out: dict = {"per_year": {}}
    for year in YEARS:
        df = pd.read_parquet(BUNDLE / "hourly" / f"class_hourly_{year}.parquet")
        p1 = df[df["pass"] == "P1"] if "P1" in set(df["pass"]) else df
        twh = p1.groupby("klass")["mw"].sum() / 1e6
        total = float(twh.sum())
        gas_classes = [k for k in twh.index if str(k).startswith(("CC_", "CT_", "ST_"))]
        gas_total = float(twh.loc[gas_classes].sum())
        out["per_year"][year] = {
            "passes_present": sorted(set(df["pass"].astype(str))),
            "total_twh": round(total, 4),
            "gas_total_twh": round(gas_total, 4),
            "by_class_twh": {str(k): round(float(v), 5) for k, v in twh.items()},
            "gas_share_by_class": {
                str(k): round(float(twh[k]) / gas_total, 6) if gas_total else 0.0
                for k in gas_classes
            },
        }
    return out


def _offer_surface_census(armed: dict, energy: dict) -> dict:
    """Classify every armed scalar in ``offer_curve_by_group`` by provenance."""
    measured = json.loads(MEASURED.read_text())
    # Which classes carry dispatch in ANY year?
    dispatching: set[str] = set()
    gas_share_max: dict[str, float] = {}
    for year in YEARS:
        for k, v in energy["per_year"][year]["by_class_twh"].items():
            if v > 0:
                dispatching.add(k)
        for k, s in energy["per_year"][year]["gas_share_by_class"].items():
            gas_share_max[k] = max(gas_share_max.get(k, 0.0), s)

    rows = []
    n_scalars = 0
    for group, bands in armed.items():
        live = group in dispatching
        for band, value in bands.items():
            if band == "peak_ladder":
                # rendered rungs: (share, mult) pairs
                n_here = sum(len(r) for r in value)
                provenance = "derived-from-peak"
            elif isinstance(value, (int, float)):
                n_here = 1
                if group in MEASURED_GROUPS and band in MEASURED_BANDS:
                    bucket = measured[BUCKET_OF[group]]["bands"]
                    provenance = (
                        "measured"
                        if abs(float(value) - float(bucket[band])) < 1e-9
                        else "fitted"
                    )
                elif band.startswith("phys_"):
                    provenance = "measured-physical"
                elif band in ("econ_low_share", "pct_peaking"):
                    provenance = "fitted-geometry"
                else:
                    provenance = "fitted"
            else:
                n_here = 1
                provenance = "fitted"
            n_scalars += n_here
            rows.append(
                {
                    "group": group,
                    "band": band,
                    "value": value,
                    "n_scalars": n_here,
                    "provenance": provenance,
                    "group_dispatches": live,
                    "group_gas_share_max": round(gas_share_max.get(group, 0.0), 6),
                }
            )

    def _tot(pred) -> int:
        return sum(r["n_scalars"] for r in rows if pred(r))

    return {
        "n_scalars_total": n_scalars,
        "ledger_n_scalars": 112,
        "by_provenance": {
            p: _tot(lambda r, p=p: r["provenance"] == p)
            for p in sorted({r["provenance"] for r in rows})
        },
        "on_dispatching_groups": _tot(lambda r: r["group_dispatches"]),
        "on_absent_groups": _tot(lambda r: not r["group_dispatches"]),
        "fitted_and_live": _tot(
            lambda r: r["group_dispatches"] and r["provenance"].startswith("fitted")
        ),
        "fitted_and_live_noncommitted_material": [
            {k: r[k] for k in ("group", "band", "value", "group_gas_share_max")}
            for r in rows
            if r["group_dispatches"]
            and r["provenance"].startswith("fitted")
            and not r["band"].startswith("committed")
            and r["group_gas_share_max"] >= 0.01
        ],
        "absent_groups": sorted(
            {r["group"] for r in rows if not r["group_dispatches"]}
        ),
        "rows": rows,
    }


def _st_gas_object(armed: dict, energy: dict) -> dict:
    """Object 2: the 0.81 committed band against its own measured basis."""
    st = armed["ST_GAS"]
    measured = json.loads(MEASURED.read_text())
    phys = float(st["phys_committed"])
    mult = float(st["committed"])
    return {
        "armed_committed_mult": mult,
        "audit_physical_floor": 0.85,
        "below_audit_floor": mult < 0.85,
        "caiso_measured_physical_basis": phys,
        "basis_source": (
            "data/raw/reference/caiso_campd_marginal_hr_summary.csv "
            "avg_committed_p50 (CAISO's OWN CAMPD min-load block burn), carried "
            "on the band dict as phys_committed"
        ),
        "ratio_armed_to_measured": round(mult / phys, 4),
        "measured_ct_bucket_committed_bid_mult": measured["CT_PEAKER"]["unarmed"][
            "committed"
        ],
        "gas_offer_margin_markup": max(0.0, mult - phys),
        "markup_clips_to_zero": mult < phys,
        "st_gas_gas_share_by_year": {
            y: energy["per_year"][y]["gas_share_by_class"].get("ST_GAS", 0.0)
            for y in YEARS
        },
        "st_gas_twh_by_year": {
            y: energy["per_year"][y]["by_class_twh"].get("ST_GAS", 0.0) for y in YEARS
        },
    }


def _storage_object(energy: dict) -> dict:
    """Object 4: the discharge share ``battery_dispatch_adder`` prices.

    Split by ``tech`` — the adder prices the LI-ION leg only; pumped storage
    carries its own per-ISO ``pumped_storage_dispatch_adder`` (``null`` here).
    """
    out: dict = {}
    for year in YEARS:
        df = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
        total = energy["per_year"][year]["total_twh"]
        by_tech = df.groupby("tech")[["charge_mw", "discharge_mw"]].sum() / 1e6
        out[year] = {
            "passes_present": sorted(set(df["pass"].astype(str))),
            "discharge_twh_by_tech": {
                str(k): round(float(v), 5) for k, v in by_tech.discharge_mw.items()
            },
            "li_ion_share_of_total_generation": round(
                float(by_tech.discharge_mw.get("li_ion", 0.0)) / total, 5
            ),
            "all_storage_share_of_total_generation": round(
                float(by_tech.discharge_mw.sum()) / total, 5
            ),
        }
    return out


def _fleet_geometry_census() -> dict:
    """The in-repo measured counterparts for the tranche-geometry scalars.

    Reads ``bin_assignments_CAISO.csv`` (the fleet basis the offer multipliers
    scale) and the two per-plant peaking maps that SUPERSEDE the offer curve's
    class-wide ``pct_peaking`` when ``cc_peaking_per_plant`` / ``cc_duct_peaking``
    are armed (``fleet/assembly.py`` lines 551-582).
    """
    from market_sim.data.fleet.campd_bins import (  # noqa: PLC0415
        cc_duct_peaking_pct,
        thermal_tranche_peaking,
    )

    b = pd.read_csv("data/raw/_processed-legacy/bin_assignments_CAISO.csv")
    duct = cc_duct_peaking_pct()
    tt = thermal_tranche_peaking("CAISO", False)
    out: dict = {}
    for grp, sub in b.groupby("Plant_Group"):
        w = sub.Nameplate_MW.to_numpy(float)
        row = {
            "n_plants": int(len(sub)),
            "nameplate_mw": round(float(w.sum()), 1),
            "pct_peaking_capwt": round(float((sub.Pct_Peaking * w).sum() / w.sum()), 3),
            "pct_peaking_distinct": sorted(float(x) for x in sub.Pct_Peaking.unique()),
            "peaking_sources": sorted({str(x) for x in sub.Peaking_Source}),
            "pct_committed_capwt": round(
                float((sub.Pct_Committed * w).sum() / w.sum()), 3
            ),
            "committed_sources": sorted({str(x) for x in sub.Committed_Source}),
            "base_hr_capwt": round(
                float((sub.Plant_Avg_HR_MMBtu_MWh * w).sum() / w.sum()), 3
            ),
        }
        if grp in ("CC_REGULAR", "CC_CHP"):
            codes = sub.Plant_Code.astype(int)
            in_duct = codes.isin(duct.keys())
            in_tt = pd.Series([(c, grp) in tt for c in codes], index=in_duct.index)
            fall = (~in_duct) & (~in_tt)
            row["n_in_duct_map"] = int(in_duct.sum())
            row["n_in_tranche_map"] = int(in_tt.sum())
            row["n_fall_through_to_classwide"] = int(fall.sum())
            row["mw_share_fall_through"] = round(
                float(sub.Nameplate_MW[fall].sum() / w.sum()), 4
            )
        if grp == "ST_GAS":
            row["plants"] = sub[
                ["Plant_Code", "Plant_Name", "Zone", "Nameplate_MW"]
            ].to_dict("records")
        out[str(grp)] = row
    return out


def main() -> None:
    rc = json.loads((BUNDLE / "run_config.json").read_text())
    sc = rc["scenario_config"]
    armed = sc["offer_curve_by_group"]

    energy = _class_energy()
    result = {
        "_provenance": {
            "session": "caiso-238",
            "keeper": "2026-09-01-caiso-231-b1-ungrounded",
            "bundle": str(BUNDLE),
            "precommit": (
                "results/calibration/PRECOMMIT-caiso238-grounding-charter-2026-09-02.md"
            ),
            "note": (
                "Committed artifacts only — no LP, no solver, no replay. C3a is "
                "never this probe's object (rule 1 [R-STRUCT])."
            ),
        },
        "gates": {
            k: sc.get(k)
            for k in (
                "use_campd_bins",
                "plant_level_fleet",
                "caiso_offer_surface_measured",
                "caiso_offer_surface_measured_ungrounded",
                "caiso_offer_surface_conditional",
                "gas_offer_net_revenue_margin",
                "gas_offer_margin_anchor",
                "cc_committed_offer_margin",
                "offer_curve_smoothing_n",
                "offer_curve_smoothing_exp",
                "offer_curve_smoothing_mid",
                "battery_dispatch_adder",
                "storage_as_commitment",
                "caiso_storage_as_reservation",
                "storage_degradation",
                "storage_capacity_value",
            )
        },
        "class_energy": energy,
        "object1_offer_curve_by_group": _offer_surface_census(armed, energy),
        "object2_st_gas_committed": _st_gas_object(armed, energy),
        "object3_offer_curve_smoothing": {
            "n": sc.get("offer_curve_smoothing_n"),
            "exp": sc.get("offer_curve_smoothing_exp"),
            "mid": sc.get("offer_curve_smoothing_mid"),
            "identity_when": (
                "n <= 0 recovers the flat two-block econ curve; exp = 1.0 is a "
                "STRAIGHT (linear) ramp across n slices, NOT an identity "
                "(scenarios.py offer_curve_smoothing_n docstring; "
                "fleet/assembly.py _econ_curve_steps)"
            ),
            "exp_is_identity": False,
            "econ_tranches_rendered_per_plant": sc.get("offer_curve_smoothing_n"),
        },
        "fleet_geometry_census": _fleet_geometry_census(),
        "object4_battery_dispatch_adder": {
            "value": sc.get("battery_dispatch_adder"),
            "storage": _storage_object(energy),
        },
    }
    OUT.write_text(json.dumps(result, indent=1))
    print(f"wrote {OUT}")

    c = result["object1_offer_curve_by_group"]
    print("\n-- object 1 --")
    print("  scalars total/ledger:", c["n_scalars_total"], "/", c["ledger_n_scalars"])
    print("  by provenance:", c["by_provenance"])
    print("  on dispatching groups:", c["on_dispatching_groups"])
    print("  on absent groups:", c["on_absent_groups"], c["absent_groups"])
    print("  fitted AND live:", c["fitted_and_live"])
    print("  FALSIFIER rows:", json.dumps(c["fitted_and_live_noncommitted_material"]))
    print("\n-- object 2 --")
    print(json.dumps(result["object2_st_gas_committed"], indent=1))
    print("\n-- object 4 --")
    print(json.dumps(result["object4_battery_dispatch_adder"], indent=1))


if __name__ == "__main__":
    main()

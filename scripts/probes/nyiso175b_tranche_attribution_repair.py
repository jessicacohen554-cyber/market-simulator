"""nyiso-175b PHASE 0 — size the fleet-wide tranche-attribution defect.

Tests the four PRE-SOLVE gates of
``results/calibration/PREREG-nyiso175b-tranche-attribution-repair.md``, which was
committed before this file was run.

THE OBJECT. Two artifacts assign a per-plant aggregate to one of a mixed plant's
classes by a PROXY instead of by the units' own meters — the same defect family
as neiso-99's rule 14 ``[R-ACCURATE]`` exception:

* ``derive_thermal_tranches._fleet_nameplate_and_group`` attributes a plant's
  **facility-summed** CAMPD net to the group holding the most **nameplate**
  (nyiso-175 §4.4: wrong at three NYISO plants, 15.233 TWh over 2023-2025);
* ``derive_campd_unit_outages._resolve_unit_group`` short-circuits on the
  plant's ``fac_group`` — last-writer-wins over the fleet iteration — before it
  consults the unit's own type (nyiso-174 §6 item 1).

Both are repaired by the SAME corrected per-unit construction, which already
exists and is tested: :func:`scripts.lib.campd_measured_classes.corrected_unit_class`
keeps a unit's prime-mover FAMILY and lets the unit's own plant's model roster
pick the class inside it. Zero DOF; a crosswalk repair, not a re-derivation
against a residual (rule 23 ``[R-FROZEN-DERIVE]``).

REPRODUCTION TRAPS honoured (nyiso-174/175 corpus):
  (c) ``STD_TZ`` — the probe corpus works on the FIXED standard-time clock;
      ``America/New_York`` raises on 2023-03-12 02:00.
  (d) CAMPD writes ``grossLoad`` NULL for a non-operating unit-hour (52 % of NY
      CC unit-hours in 2025). Filled to zero EXPLICITLY before any accumulation.
  (f) the class is ``corrected_unit_class``, never the bare ``unitType`` string.
  Plus one of this file's own: ``facilityId`` is a STRING dtype in the NY
  unit-level parquets and must be cast before any integer comparison.

Nothing here touches a parameter, and nothing here runs an LP.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402
from market_sim.data.chp import _chp_by_plant  # noqa: E402
from market_sim.data.fleet import load_fleet_from_csv  # noqa: E402
from scripts.data.derive_campd_unit_outages import (  # noqa: E402
    _is_multi_gas_facility,
    _resolve_unit_group,
)
from scripts.lib.campd_measured_classes import (  # noqa: E402
    campd_unittype_class,
    corrected_unit_class,
)

YEARS = (2023, 2024, 2025)
ISO = "NYISO"
OUT = REPO / "results/calibration/_nyiso175b_tranche_attribution_repair.json"

EAST_RIVER, RAVENSWOOD, CARLSON = 2493, 2500, 2682
NAMED = {EAST_RIVER: "East River", RAVENSWOOD: "Ravenswood", CARLSON: "S A Carlson"}

#: The groups ``derive_thermal_tranches`` emits tranche rows for. Mirrors that
#: module's ``_THERMAL_GROUPS`` — imported rather than retyped where possible.
try:  # pragma: no cover - import shape differs by checkout
    from scripts.data.derive_thermal_tranches import _THERMAL_GROUPS  # noqa: E402
except Exception:  # pragma: no cover
    _THERMAL_GROUPS = frozenset(
        {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "COAL"}
    )

#: K1's bar: TWh of NYISO CAMPD energy the repair must re-seat over 2023-2025.
K1_BAR_TWH = 4.0


_CACHE: dict = {}


def chp_plants() -> set[int]:
    """EIA-860 CHP plant codes — the model's own CHP determination.

    Same call the nyiso-175 probe used, so the CHP flag behind every class
    verdict here is identical to the one behind that session's numbers.
    """
    if "chp" not in _CACHE:
        flags = _chp_by_plant(RAW_DATA_DIR / "eia-860", 2025)
        _CACHE["chp"] = {
            int(k) for k, v in flags.items() if str(v).strip().upper() == "Y"
        }
    return _CACHE["chp"]


def _round(x, n=4):
    try:
        return round(float(x), n)
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------- loaders --


def fleet_groups() -> tuple[dict[int, dict[str, float]], dict[int, str]]:
    """``({code: {group: MW}}, {code: primary_group})`` — the nameplate rule.

    Reproduces ``derive_thermal_tranches._fleet_nameplate_and_group`` for a
    non-ERCOT ISO exactly, so the "current" side of every comparison here is
    the deriver's own behaviour and not a paraphrase of it.
    """
    if "fleet" in _CACHE:
        return _CACHE["fleet"]
    cap: dict[int, dict[str, float]] = {}
    for gen in load_fleet_from_csv(ISO, get_iso_config(ISO)):
        code = int(gen.plant_code)
        if code <= 0 or not gen.plant_group:
            continue
        cap.setdefault(code, {})
        cap[code][gen.plant_group] = cap[code].get(gen.plant_group, 0.0) + float(
            gen.pmax_mw
        )
    primary = {
        code: max(groups.items(), key=lambda kv: kv[1])[0]
        for code, groups in cap.items()
        if groups
    }
    _CACHE["fleet"] = (cap, primary)
    return cap, primary


def campd_units(year: int) -> pd.DataFrame:
    """NY unit-level CAMPD for one year, with each unit's CORRECTED class.

    ``grossLoad`` NULL is a non-operating unit-hour and is filled to zero before
    any aggregation (trap (d)); ``facilityId`` is a string dtype and is cast.
    """
    if ("campd", year) in _CACHE:
        return _CACHE[("campd", year)]
    d = pd.read_parquet(
        RAW_DATA_DIR / f"campd-unit-level/NY_{year}.parquet",
        columns=[
            "facilityId",
            "unitId",
            "unitType",
            "primaryFuelInfo",
            "grossLoad",
        ],
    )
    d["grossLoad"] = d["grossLoad"].fillna(0.0)
    d["facilityId"] = d["facilityId"].astype(int)
    chpset = chp_plants()
    cap, _ = fleet_groups()
    pairs = d[["facilityId", "unitType"]].drop_duplicates()
    kmap: dict[tuple[int, str], str | None] = {}
    for fid, ut in zip(pairs["facilityId"], pairs["unitType"]):
        raw = campd_unittype_class(ut, int(fid) in chpset)
        kmap[(int(fid), str(ut))] = corrected_unit_class(raw, cap.get(int(fid)))
    d["klass"] = [
        kmap[(int(f), str(u))] for f, u in zip(d["facilityId"], d["unitType"])
    ]
    _CACHE[("campd", year)] = d
    return d


def reseat_group(
    code: int,
    klass: str,
    cap: dict[int, dict[str, float]],
    primary: dict[int, str],
) -> str | None:
    """The tranche row a unit's energy belongs on, under the REPAIR.

    The rule: a unit's energy goes to the model bin that CONTAINS the unit —
    its corrected prime-mover class — and where the plant carries no such bin
    the attribution is left exactly as it is today (the plant's primary group).

    **The fallback clause is an AMENDMENT forced by pre-registered gate K2**,
    and it amends the CONSTRUCTION, never the threshold. As first written this
    function had no fallback, and K2 caught three ST_GAS-only plants — 2490,
    8906 and 2516 Northport — whose CAMPD combustion turbines correct to
    ``CT_PEAKER``, a bin those plants do not carry, so 0.0051 TWh over three
    years would have been silently dropped out of the ``ST_GAS`` denominator.
    That is a reclassification, not a crosswalk repair: the repair's warrant is
    "attribute a unit's energy to the bin that contains it", and where there is
    no such bin the repair has nothing to say. Confining it to the case it is
    justified for is what makes it a strict crosswalk repair — and what makes
    K2 pass honestly instead of by redefinition.
    """
    if klass and klass in cap.get(code, {}):
        return klass
    return primary.get(code)


# -------------------------------------------------------------- the gates --


def k1_reseated_energy() -> dict:
    """K1 — how much measured energy the repair moves onto a different row.

    Today every unit's energy at a plant is attributed to ``primary[code]``.
    Under the repair each unit's energy goes to its OWN corrected class, so the
    re-seated energy is that of the units whose corrected class is not the
    plant's primary group.
    """
    cap, primary = fleet_groups()
    per_year, per_plant = {}, {}
    total_moved = 0.0
    for year in YEARS:
        d = campd_units(year)
        d = d[d["klass"].notna()]
        g = d.groupby(["facilityId", "klass"], observed=True)["grossLoad"].sum()
        moved_y = 0.0
        for (code, klass), mwh in g.items():
            code = int(code)
            prim = primary.get(code)
            if prim is None or prim not in _THERMAL_GROUPS:
                continue
            seat = reseat_group(code, str(klass), cap, primary)
            if seat == prim:
                continue
            twh = float(mwh) / 1e6
            moved_y += twh
            key = str(code)
            per_plant.setdefault(
                key,
                {
                    "name": NAMED.get(code, ""),
                    "primary_group": prim,
                    "primary_nameplate_mw": _round(cap[code].get(prim, 0.0), 1),
                    "model_groups": {k: _round(v, 1) for k, v in cap[code].items()},
                    "reseated_twh_by_year": {},
                    "reseated_to": {},
                },
            )
            per_plant[key]["reseated_twh_by_year"].setdefault(str(year), 0.0)
            per_plant[key]["reseated_twh_by_year"][str(year)] = _round(
                per_plant[key]["reseated_twh_by_year"][str(year)] + twh
            )
            per_plant[key]["reseated_to"][str(seat)] = _round(
                per_plant[key]["reseated_to"].get(str(seat), 0.0) + twh
            )
        per_year[str(year)] = _round(moved_y)
        total_moved += moved_y
    for v in per_plant.values():
        v["reseated_twh_total"] = _round(sum(v["reseated_twh_by_year"].values()))
    ranked = sorted(
        per_plant.items(), key=lambda kv: -(kv[1]["reseated_twh_total"] or 0.0)
    )
    top = dict(ranked[:12])
    return {
        "gate": "K1",
        "bar_twh": K1_BAR_TWH,
        "reseated_twh_by_year": per_year,
        "reseated_twh_total": _round(total_moved),
        "n_plants_affected": len(per_plant),
        "top_plants": top,
        "east_river_share_of_moved": _round(
            (per_plant.get(str(EAST_RIVER), {}).get("reseated_twh_total") or 0.0)
            / total_moved
            if total_moved
            else 0.0
        ),
        "verdict": "PASS" if total_moved >= K1_BAR_TWH else "FAIL",
    }


def k2_single_group_noop() -> dict:
    """K2 — the repair must be a NO-OP at every single-thermal-group plant."""
    cap, primary = fleet_groups()
    single = {
        code
        for code, groups in cap.items()
        if len([g for g in groups if g in _THERMAL_GROUPS]) == 1
    }
    offenders: dict[str, dict] = {}
    checked = 0
    for year in YEARS:
        d = campd_units(year)
        d = d[d["klass"].notna()]
        d = d[d["facilityId"].isin(single)]
        g = d.groupby(["facilityId", "klass"], observed=True)["grossLoad"].sum()
        for (code, klass), mwh in g.items():
            code = int(code)
            checked += 1
            prim = primary.get(code)
            if prim is None or prim not in _THERMAL_GROUPS:
                continue
            seat = reseat_group(code, str(klass), cap, primary)
            if seat != prim and float(mwh) > 0.0:
                o = offenders.setdefault(
                    str(code),
                    {
                        "name": NAMED.get(code, ""),
                        "primary_group": prim,
                        "model_groups": {
                            k: _round(v, 1) for k, v in cap[code].items()
                        },
                        "moved_twh": 0.0,
                        "to": {},
                    },
                )
                o["moved_twh"] = _round(o["moved_twh"] + float(mwh) / 1e6)
                o["to"][str(seat)] = _round(
                    o["to"].get(str(seat), 0.0) + float(mwh) / 1e6
                )
    return {
        "gate": "K2",
        "n_single_thermal_group_plants": len(single),
        "n_plant_class_rows_checked": checked,
        "n_offenders": len(offenders),
        "offenders": offenders,
        "verdict": "PASS" if not offenders else "FAIL",
        "construction_amended_by_this_gate": True,
        "amendment": (
            "As FIRST constructed this gate FAILED on three ST_GAS-only plants "
            "(2490, 8906, 2516 Northport), 0.0051 TWh over three years: their "
            "CAMPD combustion turbines correct to CT_PEAKER, a bin those "
            "plants do not carry, so the energy would have been dropped out of "
            "the ST_GAS denominator. The CONSTRUCTION was amended, never the "
            "threshold — reseat_group now leaves a unit on the plant's primary "
            "group where the plant carries no bin in the unit's family — and "
            "the gate was re-run. See reseat_group's docstring."
        ),
        "note": (
            "An offender is a plant where the repair genuinely relocates "
            "energy away from the single bin the model carries."
        ),
    }


def k3_existing_gate_does_not_cover() -> dict:
    """K3 — rule 19: does ``mixed_gas_routing`` already reach East River?

    Measured, not read: ``_resolve_unit_group`` is CALLED with the plant's real
    fleet groups and each unit's real CAMPD ``unitType`` / ``primaryFuelInfo``,
    with the gate both OFF and ON.
    """
    cap, primary = fleet_groups()
    d = campd_units(2023)
    rows = []
    for code in (EAST_RIVER, RAVENSWOOD, CARLSON):
        fac_groups = set(cap.get(code, {}))
        fac_group = primary.get(code)
        units = (
            d[d["facilityId"] == code][["unitId", "unitType", "primaryFuelInfo"]]
            .drop_duplicates()
            .sort_values("unitId")
        )
        for _, u in units.iterrows():
            off = _resolve_unit_group(
                False,
                str(u["unitType"]),
                fac_groups,
                fac_group,
                str(u["primaryFuelInfo"] or ""),
                mixed_gas_routing=False,
            )
            on = _resolve_unit_group(
                False,
                str(u["unitType"]),
                fac_groups,
                fac_group,
                str(u["primaryFuelInfo"] or ""),
                mixed_gas_routing=True,
            )
            corrected = corrected_unit_class(
                campd_unittype_class(u["unitType"], code in chp_plants()),
                cap.get(code),
            )
            rows.append(
                {
                    "plant": code,
                    "name": NAMED.get(code, ""),
                    "unit": str(u["unitId"]),
                    "unitType": str(u["unitType"]),
                    "fuel": str(u["primaryFuelInfo"] or ""),
                    "model_groups": sorted(fac_groups),
                    "is_multi_gas_facility": bool(_is_multi_gas_facility(fac_groups)),
                    "resolved_gate_OFF": off,
                    "resolved_gate_ON": on,
                    "corrected_crosswalk": corrected,
                    "gate_ON_fixes_it": bool(on == corrected),
                }
            )
    er = [r for r in rows if r["plant"] == EAST_RIVER]
    er_turbine = [r for r in er if r["corrected_crosswalk"] == "CT_CHP"]
    covered = bool(er_turbine) and all(r["gate_ON_fixes_it"] for r in er_turbine)
    return {
        "gate": "K3",
        "question": "does the EXISTING mixed_gas_routing gate already cover East River?",
        "units": rows,
        "east_river_turbine_units_fixed_by_existing_gate": covered,
        "verdict": "PASS" if not covered else "FAIL",
        "note": (
            "PASS means the existing gate does NOT cover it, so new routing "
            "logic is warranted under rule 19 [R-ONE-MECH]. FAIL would mean "
            "arming the existing gate instead of writing anything new."
        ),
    }


def k4_missing_rows_appear() -> dict:
    """K4 — the turbine bins that carry the energy must gain a tranche row."""
    cap, primary = fleet_groups()
    want = {EAST_RIVER: "CT_CHP", RAVENSWOOD: "CC_REGULAR", CARLSON: "CT_PEAKER"}
    committed = REPO / "data/raw/_processed-legacy/thermal_tranches_NYISO.csv"
    have: set[tuple[int, str]] = set()
    csv_note = None
    if committed.exists():
        t = pd.read_csv(committed)
        have = {
            (int(r["plant_code"]), str(r["plant_group"])) for _, r in t.iterrows()
        }
    else:  # pragma: no cover
        csv_note = f"committed tranche CSV not found at {committed}"
    out = {}
    for code, group in want.items():
        out[str(code)] = {
            "name": NAMED[code],
            "carrier_group": group,
            "carrier_in_model_fleet": group in cap.get(code, {}),
            "carrier_nameplate_mw": _round(cap.get(code, {}).get(group, 0.0), 1),
            "primary_group_today": primary.get(code),
            "row_exists_in_committed_csv": (code, group) in have,
            "primary_row_exists_in_committed_csv": (
                (code, primary.get(code, "")) in have
            ),
        }
    missing = [
        v
        for v in out.values()
        if v["carrier_in_model_fleet"] and not v["row_exists_in_committed_csv"]
    ]
    return {
        "gate": "K4",
        "committed_csv": str(committed.relative_to(REPO)),
        "csv_note": csv_note,
        "plants": out,
        "n_carrier_rows_missing_today": len(missing),
        "verdict": "PASS" if missing else "FAIL",
        "note": (
            "PASS means the carrier bin genuinely has no tranche row today, "
            "which is the defect the repair closes."
        ),
    }


def context_named_plants() -> dict:
    """The three named plants' measured class split, for the finding's table."""
    cap, primary = fleet_groups()
    out = {}
    for code in (EAST_RIVER, RAVENSWOOD, CARLSON):
        rec = {
            "name": NAMED[code],
            "model_groups_mw": {k: _round(v, 1) for k, v in cap.get(code, {}).items()},
            "primary_group_by_nameplate": primary.get(code),
            "measured_twh_by_class": {},
        }
        for year in YEARS:
            d = campd_units(year)
            d = d[(d["facilityId"] == code) & d["klass"].notna()]
            g = d.groupby("klass", observed=True)["grossLoad"].sum() / 1e6
            rec["measured_twh_by_class"][str(year)] = {
                str(k): _round(v) for k, v in g.items()
            }
        out[str(code)] = rec
    return out


def main() -> None:
    k1 = k1_reseated_energy()
    k2 = k2_single_group_noop()
    k3 = k3_existing_gate_does_not_cover()
    k4 = k4_missing_rows_appear()
    gates = {"K1": k1["verdict"], "K2": k2["verdict"], "K3": k3["verdict"],
             "K4": k4["verdict"]}
    res = {
        "session": "nyiso-175b",
        "keeper": "2026-08-30-nyiso-159-loss-surface",
        "prereg": (
            "results/calibration/PREREG-nyiso175b-tranche-attribution-repair.md"
        ),
        "years": list(YEARS),
        "gate_verdicts": gates,
        "all_presolve_gates_pass": all(v == "PASS" for v in gates.values()),
        "K1_reseated_energy": k1,
        "K2_single_group_noop": k2,
        "K3_existing_gate": k3,
        "K4_missing_rows": k4,
        "context_named_plants": context_named_plants(),
    }
    OUT.write_text(json.dumps(res, indent=1, sort_keys=False) + "\n")
    print(f"wrote {OUT}")
    for k, v in gates.items():
        print(f"  {k}: {v}")
    print(f"  all pre-solve gates pass: {res['all_presolve_gates_pass']}")


if __name__ == "__main__":
    main()

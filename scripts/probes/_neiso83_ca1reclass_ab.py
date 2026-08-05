"""neiso-83 A/B scorer — ``cc_steam_part_reclass`` at NEISO (6081 Stony Brook ``CA1``).

Scores the PRE-REGISTERED properties of
``results/calibration/PREREG-neiso83-stonybrook-ca1-2026-08-05.md`` from the two
solved bundles plus committed artifacts. **No solve, and no gate that is not in
the prereg.**

Construction properties (prereg §5), every one of which must hold or the run is
INVALID rather than "inert":

* **P1 flag fidelity** — arm A records ``cc_steam_part_reclass: false``, arm B
  ``true``, and the arms' scenario blocks differ in exactly that one key.
* **P2 fleet grain** — exactly one unit differs between the arms' fleets, total
  ``pmax`` conserved, ``6081_CA1.heat_rate`` identical in both.
* **P3 ISO scope** (rule 25) — the other five ISOs' fleets byte-identical under
  the armed flag, re-measured here rather than inherited from Phase 0.
* **P4 firing at the ENERGY grain** (the miso-126 wiring gap) — the ``oil``
  class annual energy must move by > 0.001 TWh in at least one year. A
  byte-identical arm means the flag never reached the LP, which is INVALID; a
  loader-level check cannot substitute for this one.
* **P5 conservation** — the FULL identity over ``class_hourly`` + ``storage`` +
  ``system``, per-hour relative, never ``class_hourly`` alone.
* **P6 system integrity** — total generation within ±0.05 %, slack and dump not
  rising.

Then the stop-and-escalate triggers N1-N4 (prereg §7) and the V1-V4 verdict
ladder (§8), whose V3 branch promotes a correct-and-inert outcome on rules 1 /
13 / 14 — the size of the residual move is REPORTED, never required.

Also computed and reported, none of them a gate: per-class TWh vs the committed
bench, mean λ, the >$300 tail count, and the capacity-leg / denominator-leg
decomposition of the arm's effect on plant 6081.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_neiso83_ca1reclass_ab.py \
        --json-out results/calibration/_neiso83_ca1reclass_ab.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/neiso83_control_A"
ARM_B = REPO / "results/calibration/neiso83_ca1reclass_B"
KEEPER = REPO / "results/calibration/neiso81_chpheatrate_B"
BENCH = REPO / "frontend/data/backcast/bench/NEISO"
OUT_PATH = REPO / "results/calibration/_neiso83_ca1reclass_ab.json"

FLAG = "cc_steam_part_reclass"
PLANT = 6081
UNIT = "6081_CA1"

# ---- thresholds, every one fixed in the prereg before either arm solved ----
#: §5 P2 — capacity-conservation tolerance, MW.
P2_CAPACITY_TOL_MW = 0.05
#: §5 P4 — the energy-grain firing bar, TWh. Below this the flag never reached
#: the LP and the run is INVALID (not inert).
P4_FIRING_MIN_TWH = 0.001
#: §5 P5 — per-hour RELATIVE balance tolerance. The sidecar ``mw`` column is
#: float32 (epsilon 1.2e-7), so an absolute GWh bar would score dtype rather
#: than conservation.
P5_BALANCE_REL_TOL = 1e-6
#: §5 P6 / §7 N4 — accepted total-generation drift.
P6_TOTAL_GEN_TOL = 0.0005
#: §7 N1 — the incumbent determination this promotion must not fall below
#: (rule 22 D-5(b)).
INCUMBENT_DETERMINATION = "CALIBRATED-WITH-CAVEATS"
#: Determination ordering, best -> worst.
_DET_RANK = {"CALIBRATED": 0, "CALIBRATED-WITH-CAVEATS": 1, "NOT-YET": 2}
#: §6 hard physical ceilings on plant 6081's own contribution, TWh — the block's
#: measured effective available capacity × 8,760 h. Reported as a bound on the
#: 6081 leg, never as a gate on the class delta (which also carries displacement).
S_CEILING_TWH = {"2023": 0.0, "2024": 1.370, "2025": 1.176}


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def _p1(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    return _p1(pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet"))


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).to_dict()


def _system(bundle: Path, year: int) -> pd.DataFrame:
    return _p1(pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet"))


def _pairwise(a: Path, b: Path, year: int) -> dict:
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
            if float(v) > 1e-9
        },
    }


def _lambda(bundle: Path, year: int) -> float:
    """NEISO load-weighted mean λ, the HQ import node excluded."""
    frame = _system(bundle, year)
    native = frame[frame["zone"].astype(str) != "HQ_import"]
    return float((native["price"] * native["demand"]).sum() / native["demand"].sum())


def _tail_hours(bundle: Path, year: int, thresh: float = 300.0) -> int:
    frame = _system(bundle, year)
    native = frame[frame["zone"].astype(str) != "HQ_import"]
    lam = (native["price"] * native["demand"]).groupby(native["hour"]).sum() / (
        native.groupby("hour")["demand"].sum()
    )
    return int((lam > thresh).sum())


def _scenario_block(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text()).get(
        "scenario_config", {}
    ) or {}


def _scorecard(bundle: Path) -> dict | None:
    path = bundle / "metrics.json"
    if not path.exists():
        return None
    m = json.loads(path.read_text())
    return {
        "determination": m.get("determination"),
        "criteria": {
            k: (v.get("status") if isinstance(v, dict) else v)
            for k, v in (m.get("criteria") or {}).items()
        },
        "free_class_score": m.get("free_class_score"),
        "grade_summary": m.get("grade_summary"),
        "caveats": m.get("caveats"),
    }


def _bench_classfull(year: int) -> dict[str, float]:
    b = json.loads(gzip.open(BENCH / f"{year}.json.gz").read())["bench"]
    return {k: float(v) for k, v in (b.get("classFull") or {}).items()}


# --------------------------------------------------------------------------- #
# P1 - P6 — the construction properties
# --------------------------------------------------------------------------- #
def p1_flag_fidelity() -> dict:
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "property": "P1 flag fidelity + single delta",
        "differing_keys": diff,
        "n_differing": len(diff),
        "arm_A_flag": a.get(FLAG),
        "arm_B_flag": b.get(FLAG),
        "passed": list(diff) == [FLAG]
        and a.get(FLAG) is False
        and b.get(FLAG) is True,
        "falsifier": "differing keys != [the flag] ⇒ INVALID, no verdict written",
    }


def p2_fleet_grain() -> dict:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    cfg = _scenario_block(ARM_B)
    kw = {
        "measured_ct_heat_rates": bool(cfg.get("measured_ct_heat_rates", False)),
        "measured_chp_heat_rates": bool(cfg.get("measured_chp_heat_rates", False)),
        "cc_steam_part_capacity": bool(cfg.get("cc_steam_part_capacity", False)),
    }
    iso_config = get_iso_config("NEISO")
    off = {g.unit_id: g.model_dump() for g in load_fleet_from_csv("NEISO", iso_config, **kw)}
    on = {
        g.unit_id: g.model_dump()
        for g in load_fleet_from_csv(
            "NEISO", iso_config, cc_steam_part_reclass=True, **kw
        )
    }
    moved = sorted(u for u in set(off) & set(on) if off[u] != on[u])
    cap_off = sum(float(v["pmax_mw"]) for v in off.values())
    cap_on = sum(float(v["pmax_mw"]) for v in on.values())
    hr_same = (
        UNIT in off
        and UNIT in on
        and abs(float(off[UNIT]["heat_rate"]) - float(on[UNIT]["heat_rate"])) < 1e-9
    )
    return {
        "property": "P2 fleet grain",
        "units_added": sorted(set(on) - set(off)),
        "units_removed": sorted(set(off) - set(on)),
        "units_changed": moved,
        "changed_fields": {
            u: {k: [off[u][k], on[u][k]] for k in off[u] if off[u][k] != on[u][k]}
            for u in moved
        },
        "total_pmax_mw": {"off": round(cap_off, 3), "armed": round(cap_on, 3)},
        "capacity_conserved": abs(cap_on - cap_off) <= P2_CAPACITY_TOL_MW,
        "ca1_heat_rate_unchanged": bool(hr_same),
        "passed": bool(
            moved == [UNIT]
            and not (set(on) ^ set(off))
            and abs(cap_on - cap_off) <= P2_CAPACITY_TOL_MW
            and hr_same
        ),
        "falsifier": "more than one unit moved, or capacity not conserved ⇒ INVALID",
    }


def p3_iso_scope() -> dict:
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet import load_fleet_from_csv

    rows = {}
    ok = True
    for iso in ("ERCOT", "CAISO", "PJM", "MISO", "NYISO"):
        cfg = get_iso_config(iso)
        off = {g.unit_id: g.model_dump() for g in load_fleet_from_csv(iso, cfg)}
        on = {
            g.unit_id: g.model_dump()
            for g in load_fleet_from_csv(iso, cfg, cc_steam_part_reclass=True)
        }
        identical = off == on
        rows[iso] = {"n": len(off), "byte_identical": bool(identical)}
        ok = ok and identical
    return {
        "property": "P3 ISO scope (rule 25 [R-ISO-SCOPE])",
        "per_iso": rows,
        "passed": bool(ok),
        "falsifier": "any other ISO's fleet moving ⇒ the gate leaks ⇒ INVALID",
        "note": (
            "Measured by RUNNING the armed loader per ISO, not by reading the "
            "registry. MISO 1004 Edwardsport — the one other member of the "
            "re-class population, and a real 555 MW IGCC machine — must stay COAL."
        ),
    }


def p4_firing_at_energy_grain() -> dict:
    """The miso-126 wiring gap: a loader check is NOT proof the flag fired."""
    per_year, fired = {}, False
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        deltas = {
            k: round(b.get(k, 0.0) - a.get(k, 0.0), 6) for k in sorted(set(a) | set(b))
        }
        oil_delta = deltas.get("oil", 0.0)
        pw = _pairwise(ARM_A, ARM_B, year)
        per_year[str(year)] = {
            "energy_delta_twh": {k: v for k, v in deltas.items() if abs(v) > 1e-6},
            "oil_energy_delta_twh": oil_delta,
            "cc_regular_energy_delta_twh": deltas.get("CC_REGULAR", 0.0),
            "max_abs_class_hour_mw": pw["max_abs_diff_mw"],
            "max_by_class_mw": pw["max_by_class_mw"],
        }
        if abs(oil_delta) > P4_FIRING_MIN_TWH:
            fired = True
    return {
        "property": "P4 firing at the ENERGY grain (miso-126 wiring gap)",
        "threshold_twh": P4_FIRING_MIN_TWH,
        "per_year": per_year,
        "passed": fired,
        "falsifier": (
            "|Δ oil energy| <= threshold in every year ⇒ the flag was recorded "
            "but never reached the LP ⇒ INVALID. This is NOT 'the mechanism is "
            "inert' — that reading is what miso-126 lost a solve to."
        ),
    }


def p5_conservation() -> dict:
    """The FULL balance identity across three sidecars."""

    def hourly(bundle: Path, year: int) -> dict[str, pd.Series]:
        c = _p1(pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet"))
        q = _p1(pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet"))
        spath = bundle / "hourly" / f"storage_{year}.parquet"
        zero = pd.Series(0.0, index=sorted(q["hour"].unique()), dtype="float64")
        if spath.exists():
            s = _p1(pd.read_parquet(spath))
            dis = s.groupby("hour")["discharge_mw"].sum().astype("float64")
            chg = s.groupby("hour")["charge_mw"].sum().astype("float64")
        else:
            dis = chg = zero
        return {
            "class": c.groupby("hour")["mw"].sum().astype("float64"),
            "discharge": dis,
            "charge": chg,
            "slack": (
                q.groupby("hour")["slack"].sum().astype("float64")
                if "slack" in q
                else zero
            ),
            "dump": (
                q.groupby("hour")["dump"].sum().astype("float64") if "dump" in q else zero
            ),
            "demand": q.groupby("hour")["demand"].sum().astype("float64"),
        }

    per_year, ok = {}, True
    for year in YEARS:
        a, b = hourly(ARM_A, year), hourly(ARM_B, year)
        d = {k: b[k].reindex(a[k].index).fillna(0.0) - a[k] for k in a}
        residual = (
            d["class"] + d["discharge"] - d["charge"] + d["slack"] - d["dump"] - d["demand"]
        )
        rel = (residual.abs() / b["demand"]).max()
        per_year[str(year)] = {
            **{f"{k}_delta_gwh": round(float(v.sum()) / 1e3, 6) for k, v in d.items()},
            "max_abs_hourly_residual_mw": round(float(residual.abs().max()), 8),
            "max_relative_hourly_residual": float(f"{float(rel):.3e}"),
        }
        if float(rel) > P5_BALANCE_REL_TOL:
            ok = False
    return {
        "property": "P5 conservation, full identity",
        "identity": "d_class + d_discharge - d_charge + d_slack - d_dump - d_demand == 0",
        "basis": "PER-HOUR RELATIVE: max_h |residual_h| / demand_h",
        "tolerance_relative": P5_BALANCE_REL_TOL,
        "per_year": per_year,
        "passed": ok,
    }


def p6_system_integrity() -> dict:
    per_year, ok = {}, True
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        ta, tb = sum(a.values()), sum(b.values())
        sa, sb = _system(ARM_A, year), _system(ARM_B, year)
        slack_a = float(sa["slack"].sum()) if "slack" in sa else 0.0
        slack_b = float(sb["slack"].sum()) if "slack" in sb else 0.0
        dump_a = float(sa["dump"].sum()) if "dump" in sa else 0.0
        dump_b = float(sb["dump"].sum()) if "dump" in sb else 0.0
        frac = (tb - ta) / ta if ta else 0.0
        per_year[str(year)] = {
            "total_gen_twh": {"A": round(ta, 5), "B": round(tb, 5)},
            "total_gen_frac_delta": round(frac, 8),
            "slack_mwh": {"A": round(slack_a, 3), "B": round(slack_b, 3)},
            "dump_mwh": {"A": round(dump_a, 3), "B": round(dump_b, 3)},
        }
        if (
            abs(frac) > P6_TOTAL_GEN_TOL
            or slack_b > slack_a + 1e-6
            or dump_b > dump_a + 1e-6
        ):
            ok = False
    return {
        "property": "P6 system integrity",
        "tolerance_total_gen": P6_TOTAL_GEN_TOL,
        "per_year": per_year,
        "passed": ok,
    }


def control_integrity() -> dict:
    """REPORTED, not a prereg gate: is arm A a faithful same-HEAD control?

    The scorecard basis is what makes the A/B like-for-like; a byte miss versus
    the committed keeper is same-HEAD code drift — the very reason a control is
    solved rather than differencing against the committed bundle (miso-124).
    """
    byte = {str(y): _pairwise(KEEPER, ARM_A, y) for y in YEARS}
    keeper_sc, a_sc = _scorecard(KEEPER), _scorecard(ARM_A)
    scorecard_ok = (
        a_sc is not None
        and keeper_sc is not None
        and a_sc["determination"] == keeper_sc["determination"]
        and a_sc["criteria"] == keeper_sc["criteria"]
    )
    return {
        "reported_not_a_gate": True,
        "scorecard_matches_committed_keeper": bool(scorecard_ok),
        "keeper_determination": (keeper_sc or {}).get("determination"),
        "control_determination": (a_sc or {}).get("determination"),
        "byte_basis_vs_committed_keeper": byte,
        "byte_basis_identical": all(
            v["max_abs_diff_mw"] <= 1e-6 for v in byte.values()
        ),
    }


# --------------------------------------------------------------------------- #
# §6 directional expectations (reported) and §7 stop triggers (scored)
# --------------------------------------------------------------------------- #
def directional() -> dict:
    rows = {}
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        d_oil = b.get("oil", 0.0) - a.get("oil", 0.0)
        d_cc = b.get("CC_REGULAR", 0.0) - a.get("CC_REGULAR", 0.0)
        rows[str(year)] = {
            "oil_twh": {"A": round(a.get("oil", 0.0), 5), "B": round(b.get("oil", 0.0), 5)},
            "CC_REGULAR_twh": {
                "A": round(a.get("CC_REGULAR", 0.0), 5),
                "B": round(b.get("CC_REGULAR", 0.0), 5),
            },
            "oil_delta_twh": round(d_oil, 6),
            "CC_REGULAR_delta_twh": round(d_cc, 6),
            "S1_oil_falls": bool(d_oil < 0.0),
            "S2_cc_rises": bool(d_cc > 0.0),
            "ceiling_on_6081_leg_twh": S_CEILING_TWH.get(str(year)),
            "cc_delta_within_ceiling": (
                abs(d_cc) <= S_CEILING_TWH.get(str(year), float("inf")) + 1e-9
            ),
        }
    return {
        "reported_not_a_gate": True,
        "per_year": rows,
        "note": (
            "Rule 1 [R-STRUCT]: nothing here can reject the arm. The ceiling "
            "bounds plant 6081's OWN contribution; a class delta may exceed it "
            "legitimately through displacement of other plants."
        ),
    }


def stop_triggers(props: dict) -> dict:
    a_sc, b_sc = _scorecard(ARM_A), _scorecard(ARM_B)
    n1_flips = []
    if a_sc and b_sc:
        for crit, a_status in a_sc["criteria"].items():
            if a_status == "PASS" and b_sc["criteria"].get(crit) == "FAIL":
                n1_flips.append({"criterion": crit, "A": a_status, "B": b_sc["criteria"].get(crit)})
    b_det = (b_sc or {}).get("determination")
    n1 = bool(
        b_det and _DET_RANK.get(b_det, 9) > _DET_RANK.get(INCUMBENT_DETERMINATION, 9)
    )
    n2 = bool(n1_flips)
    a_tail = (a_sc or {}).get("criteria", {}).get("price_tail")
    b_tail = (b_sc or {}).get("criteria", {}).get("price_tail")
    n_cav_a = len((a_sc or {}).get("caveats") or [])
    n_cav_b = len((b_sc or {}).get("caveats") or [])
    n3 = bool((a_tail == "CAVEAT" and b_tail == "FAIL") or n_cav_b > n_cav_a)
    n4 = not props["p6"]["passed"]
    return {
        "N1_determination_worse": {
            "fired": n1,
            "incumbent": INCUMBENT_DETERMINATION,
            "arm_A": (a_sc or {}).get("determination"),
            "arm_B": b_det,
        },
        "N2_criterion_pass_to_fail": {"fired": n2, "flips": n1_flips},
        "N3_c3c_degraded_or_new_caveat": {
            "fired": n3,
            "price_tail": {"A": a_tail, "B": b_tail},
            "n_caveats": {"A": n_cav_a, "B": n_cav_b},
        },
        "N4_system_integrity": {"fired": n4, "detail": props["p6"]["per_year"]},
        "any_fired": bool(n1 or n2 or n3 or n4),
    }


def reported_context() -> dict:
    """Everything measured but gating nothing."""
    lam, tails, c1 = {}, {}, {}
    for year in YEARS:
        la, lb = _lambda(ARM_A, year), _lambda(ARM_B, year)
        lam[str(year)] = {
            "A": round(la, 4),
            "B": round(lb, 4),
            "delta_usd": round(lb - la, 4),
            "frac_of_level": round((lb - la) / la if la else 0.0, 6),
        }
        tails[str(year)] = {
            "A": _tail_hours(ARM_A, year),
            "B": _tail_hours(ARM_B, year),
        }
        cf = _bench_classfull(year)
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        c1[str(year)] = {
            k: {
                "actual": round(cf[k], 4),
                "A": round(a.get(k, 0.0), 4),
                "B": round(b.get(k, 0.0), 4),
                "abs_err_A": round(abs(a.get(k, 0.0) - cf[k]), 4),
                "abs_err_B": round(abs(b.get(k, 0.0) - cf[k]), 4),
                "abs_err_delta": round(
                    abs(b.get(k, 0.0) - cf[k]) - abs(a.get(k, 0.0) - cf[k]), 4
                ),
            }
            for k in sorted(cf)
        }
    summed = {
        y: round(sum(r["abs_err_delta"] for r in rows.values()), 4)
        for y, rows in c1.items()
    }
    return {
        "lambda_load_weighted": lam,
        "tail_hours_over_300": tails,
        "c1_per_class_vs_bench": c1,
        "c1_summed_abs_err_delta_twh": summed,
    }


def outage_decomposition() -> dict:
    """The capacity leg vs the denominator leg at plant 6081 (reported)."""
    from market_sim.data.outages import _iso_plant_capacity, unit_outage_derate_factors

    d_off = _iso_plant_capacity("NEISO").get((PLANT, "CC_REGULAR"))
    d_on = _iso_plant_capacity("NEISO", True).get((PLANT, "CC_REGULAR"))
    rows = {}
    for year in YEARS:
        off = unit_outage_derate_factors(year, 8760, "", iso="NEISO")[
            (PLANT, "CC_REGULAR")
        ]
        on = unit_outage_derate_factors(
            year, 8760, "", iso="NEISO", cc_steam_part_reclass=True
        )[(PLANT, "CC_REGULAR")]
        eff_off = float(off.mean()) * d_off
        eff_cap = float(off.mean()) * d_on
        eff_on = float(on.mean()) * d_on
        rows[str(year)] = {
            "mean_avail": {"off": round(float(off.mean()), 4), "armed": round(float(on.mean()), 4)},
            "effective_avail_mw": {
                "off": round(eff_off, 1),
                "capacity_leg_only": round(eff_cap, 1),
                "armed": round(eff_on, 1),
            },
            "capacity_leg_mw": round(eff_cap - eff_off, 1),
            "denominator_leg_mw": round(eff_on - eff_cap, 1),
        }
    return {
        "reported_not_a_gate": True,
        "denominator_mw": {"off": round(float(d_off), 1), "armed": round(float(d_on), 1)},
        "per_year": rows,
        "root_cause_named_not_fixed": (
            "campd-unit-outages-NEISO.csv carries plant 6081's DIESEL peakers "
            "(CAMPD units 004/005 = EIA-860 generators 1 and 2) with "
            "plant_group=CC_REGULAR, because `oil` carries no plant_group and "
            "the overlay cannot represent an oil unit's outage. In 2024 and 2025 "
            "those two units are the ONLY source of 6081 outage rows while the "
            "CC block's own units 001/002/003 have none — so a fully-available "
            "CC block is derated to 29.5 % / 19.4 %. Pre-existing, ISO-agnostic, "
            "needs a fleet-taxonomy change with six-ISO blast radius. NAMED as an "
            "open root-cause issue (rule 21), NOT fixed here (rules 19, 25)."
        ),
    }


def verdict(props: dict, triggers: dict) -> dict:
    construction = {k: props[k]["passed"] for k in ("p1", "p2", "p3", "p4", "p5", "p6")}
    if not props["p4"]["passed"]:
        return {
            "branch": "V1",
            "outcome": "INVALID — the flag never reached the LP",
            "cell": None,
            "construction": construction,
        }
    if not all(construction.values()):
        return {
            "branch": "V2",
            "outcome": "INVALID — a construction property failed",
            "cell": None,
            "construction": construction,
        }
    if not triggers["any_fired"]:
        return {
            "branch": "V3",
            "outcome": (
                "K — PROMOTE on rules 1 [R-STRUCT] / 13 [R-MEASURED] / 14 "
                "[R-ACCURATE]: a zero-DOF correctness fix. The size of the "
                "residual move is reported, never required."
            ),
            "cell": "K",
            "construction": construction,
        }
    return {
        "branch": "V4",
        "outcome": (
            "STOP-AND-ESCALATE to the owner; keeper UNCHANGED. Cell stays O "
            "with the escalation recorded (the nyiso-120 precedent)."
        ),
        "cell": "O",
        "construction": construction,
        "fired": {k: v for k, v in triggers.items() if isinstance(v, dict) and v.get("fired")},
    }


def main() -> int:
    """Score the pre-registered ladder and write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=str(OUT_PATH))
    args = ap.parse_args()

    props = {
        "p1": p1_flag_fidelity(),
        "p2": p2_fleet_grain(),
        "p3": p3_iso_scope(),
        "p4": p4_firing_at_energy_grain(),
        "p5": p5_conservation(),
        "p6": p6_system_integrity(),
    }
    triggers = stop_triggers(props)
    rec = {
        "session": "neiso-83",
        "iso": "NEISO",
        "flag": FLAG,
        "arm_A": str(ARM_A.relative_to(REPO)),
        "arm_B": str(ARM_B.relative_to(REPO)),
        "prereg": "results/calibration/PREREG-neiso83-stonybrook-ca1-2026-08-05.md",
        "construction_properties": props,
        "control_integrity": control_integrity(),
        "directional_expectations": directional(),
        "stop_triggers": triggers,
        "reported_context": reported_context(),
        "outage_decomposition": outage_decomposition(),
        "verdict": verdict(props, triggers),
    }

    print("=" * 78)
    print("neiso-83 A/B — cc_steam_part_reclass")
    print("=" * 78)
    for key in ("p1", "p2", "p3", "p4", "p5", "p6"):
        p = props[key]
        print(f"  {key.upper()} {p['property']:<52} {'PASS' if p['passed'] else 'FAIL'}")
    print()
    for name, t in triggers.items():
        if isinstance(t, dict) and "fired" in t:
            print(f"  {name:<36} fired = {t['fired']}")
    print()
    for y in YEARS:
        r = rec["directional_expectations"]["per_year"][str(y)]
        print(
            f"  {y}: oil {r['oil_twh']['A']:.4f} -> {r['oil_twh']['B']:.4f} "
            f"({r['oil_delta_twh']:+.4f})   CC_REGULAR "
            f"{r['CC_REGULAR_twh']['A']:.4f} -> {r['CC_REGULAR_twh']['B']:.4f} "
            f"({r['CC_REGULAR_delta_twh']:+.4f})"
        )
    print()
    print(f"  VERDICT {rec['verdict']['branch']}: {rec['verdict']['outcome']}")

    Path(args.json_out).write_text(json.dumps(rec, indent=1, sort_keys=True) + "\n")
    print(f"\nwrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

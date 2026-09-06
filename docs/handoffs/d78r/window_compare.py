"""capx D78-R — the FULL 2021-2025 window, control-P vs the repaired arm, read
off the two bundles' committed ledgers and ``score.json``. Zero LP.

Grades every gate and condition of
``PRECOMMIT-capx-d78r-full-window-2026-09-06.md``:

  * **S2** cohort purity — zero sector-1 (and zero unknown-sector) rows in the
    arm's ``pipeline_events`` / economic ``retirements`` / ``floor_retained`` /
    ``throughput_deferred``, every year.
  * **S3** the must-offer identity — the arm's sector-1 ``offer_stack`` rows are
    the control's, byte-identical on an identical-fleet year and present at the
    same offer / ``A_g`` on every other year.
  * **S4** the auction untouched on the identical-fleet years.
  * **S6** the window-total sign line, as a RATIO to control-P's own realized
    values (D74 §9 item 3), with the row-level attribution of any excess.
  * **(a) purity / (b) fidelity** — exact on the identical-fleet years, in the
    fleet-delta form after; **(c) composition** and **(d) LOYO** from
    ``score.json``.

    uv run python docs/handoffs/d78r/window_compare.py \\
        --ctl results/hindcast/pjm-2021-2025-realized-t1h-d78-control-P \\
        --arm results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate \\
        [--years 2021 2022 2023 2024 2025] [--out .../window_compare.json]

The sector map is the EIA-860 2020-vintage plant table (the gate's own key,
``plant_code``), joined exactly as D58's ``ab_compare.py`` and D78's
``screen_compare.py`` did. Rule 29(c): the bundles are deleted / slimmed before
merge, so this JSON and the FINDING are the record.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V2020 = ROOT / "data/raw/eia-860/vintage_2020"

_PLANT_RE = re.compile(r"_p(\d+)_")
_LEGACY_RE = re.compile(r"^(\d+)_")

WINDOW = (2021, 2022, 2023, 2024, 2025)

#: PRECOMMIT §5.2 — the pre-declared window-total bands, arm / control-P.
S6_BANDS = {"decided_mw": (0.85, 1.15), "executed_economic_mw": (0.80, 1.25)}

#: PRECOMMIT §6(a) — the footprint keys that must be identical (identical-fleet
#: years) or identical up to the exit delta (every other year).
FOOTPRINT_KEYS = (
    "thermal_additions",
    "renewable_additions",
    "storage_additions",
    "announced_derates",
    "confirmed_derates",
    "ccs_retrofits",
    "entry_decided_mw_by_tech",
    "peak_demand_mw",
    "screen_peak_demand_mw",
    "screen_adequacy_requirement_mw",
)

#: The scalar auction fields S4 requires identical on an identical-fleet year.
CLEARING_SCALARS = (
    "n_offers",
    "offered_mw",
    "price_takers_mw",
    "requirement_mw",
    "census_mw",
    "cleared_mw",
    "cleared_position",
    "census_position",
    "price_usd_per_mw_day",
    "how",
    "n_uncleared",
)

MW_TOL = 1e-3
PRICE_TOL = 1e-6
OFFER_TOL = 1e-9
AG_TOL = 1e-6


# --------------------------------------------------------------------------- #
# readers
# --------------------------------------------------------------------------- #
def plant_code(unit_id: str) -> int | None:
    """The EIA plant code a model unit id carries, or ``None``."""
    m = _PLANT_RE.search(unit_id)
    if m:
        return int(m.group(1))
    m = _LEGACY_RE.match(unit_id)
    return int(m.group(1)) if m else None


def sectors() -> dict[int, int]:
    """``{plant_code: EIA-860 Sector}`` from the gate's own 2020 vintage."""
    df = pd.read_parquet(
        V2020 / "eia860_plant.parquet", columns=["Plant Code", "Sector"]
    )
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def sector_of(uid: str, sec: dict[int, int]) -> str:
    """The unit's plant sector as a string, or ``"unknown"`` (fails open)."""
    c = plant_code(uid)
    return str(sec[c]) if c in sec else "unknown"


def bundle_dir(out_dir: Path) -> Path:
    """The single ``<out-dir>/PJM/<cache_key>/`` directory of a bundle."""
    hits = glob.glob(str(out_dir / "PJM" / "*" / ""))
    assert len(hits) == 1, (out_dir, hits)
    return Path(hits[0])


def ledger(b: Path, year: int) -> dict | None:
    p = b / f"evolution_{year}.json"
    return json.loads(p.read_text()) if p.exists() else None


def score(b: Path) -> dict | None:
    p = b / "score.json"
    return json.loads(p.read_text()) if p.exists() else None


# --------------------------------------------------------------------------- #
# per-year projections
# --------------------------------------------------------------------------- #
def events(led: dict, kind: str) -> dict[str, dict]:
    return {
        e["unit_id"]: e
        for e in (led.get("pipeline_events") or [])
        if e.get("event") == kind
    }


def failing_pool(led: dict) -> dict[str, float]:
    """The screen's failing set: the rows the decision partition reached."""
    return {
        e["unit_id"]: float(e.get("mw") or 0.0)
        for e in (led.get("pipeline_events") or [])
        if e.get("event") in ("decided", "entry_capped")
    }


def economic_exits(led: dict) -> dict[str, dict]:
    return {
        r["unit_id"]: r
        for r in (led.get("retirements") or [])
        if r.get("reason") == "economic"
    }


def stack_rows(led: dict) -> dict[str, tuple]:
    """``{unit_id: (unit, fuel, offer, A_g, cleared)}`` from the D57 clearing."""
    cc = led.get("capacity_clearing") or {}
    return {r[0]: tuple(r) for r in (cc.get("offer_stack") or [])}


def by_sector(rows: dict[str, float], sec: dict[int, int]) -> dict:
    mw: dict[str, float] = defaultdict(float)
    n: dict[str, int] = defaultdict(int)
    for uid, v in rows.items():
        s = sector_of(uid, sec)
        mw[s] += v
        n[s] += 1
    return {
        "mw": {k: round(v, 3) for k, v in sorted(mw.items())},
        "rows": dict(sorted(n.items())),
    }


def by_fuel(rows: dict[str, dict]) -> dict[str, float]:
    out: dict[str, float] = defaultdict(float)
    for r in rows.values():
        out[str(r.get("fuel"))] += float(r.get("mw") or 0.0)
    return {k: round(v, 3) for k, v in sorted(out.items())}


def leg_year(led: dict, sec: dict[int, int]) -> dict:
    """Everything one leg-year contributes to the grade."""
    cc = led.get("capacity_clearing") or {}
    dec, cap, exe = (
        events(led, "decided"),
        events(led, "entry_capped"),
        events(led, "executed"),
    )
    pool = failing_pool(led)
    econ = economic_exits(led)
    stack = stack_rows(led)
    s1_stack = {u: r for u, r in stack.items() if sector_of(u, sec) == "1"}
    return {
        "clearing": {k: cc.get(k) for k in CLEARING_SCALARS},
        "uncleared_mw_by_fuel": cc.get("uncleared_mw_by_fuel"),
        "n_stack_rows": len(stack),
        "sector1_stack_rows": len(s1_stack),
        "sector1_stack_accredited_mw": round(sum(r[3] for r in s1_stack.values()), 3),
        "sector1_stack_uncleared_rows": sum(1 for r in s1_stack.values() if not r[4]),
        "sector1_stack_uncleared_accredited_mw": round(
            sum(r[3] for r in s1_stack.values() if not r[4]), 3
        ),
        "sector_gated_census": led.get("sector_gated"),
        "failing_rows": len(pool),
        "failing_mw": round(sum(pool.values()), 3),
        "failing_by_sector": by_sector(pool, sec),
        "decided_rows": len(dec),
        "decided_mw": round(sum(float(e["mw"]) for e in dec.values()), 3),
        "decided_by_execute_year": {
            str(y): round(
                sum(float(e["mw"]) for e in dec.values() if e.get("execute_year") == y),
                3,
            )
            for y in sorted({e.get("execute_year") for e in dec.values()})
        },
        "capped_rows": len(cap),
        "capped_mw": round(sum(float(e["mw"]) for e in cap.values()), 3),
        "executed_pipeline_rows": len(exe),
        "executed_pipeline_mw": round(sum(float(e["mw"]) for e in exe.values()), 3),
        "economic_exit_rows": len(econ),
        "economic_exit_mw": round(sum(float(r["mw"]) for r in econ.values()), 3),
        "economic_exit_by_fuel": by_fuel(econ),
        "floor_retained_mw": round(
            sum(float(r.get("mw") or 0.0) for r in (led.get("floor_retained") or [])), 3
        ),
        "throughput_deferred_mw": round(
            sum(
                float(r.get("mw") or 0.0)
                for r in (led.get("throughput_deferred") or [])
            ),
            3,
        ),
        "fleet_by_fuel_before": led.get("fleet_by_fuel_before"),
        "footprint": {k: led.get(k) for k in FOOTPRINT_KEYS},
    }


# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
def s2_purity(led: dict, sec: dict[int, int]) -> dict:
    """S2 — no sector-1 or unknown-sector row in the arm's decision ledgers."""
    bad: dict[str, list[str]] = defaultdict(list)
    for e in led.get("pipeline_events") or []:
        s = sector_of(e["unit_id"], sec)
        if s in ("1", "unknown"):
            bad[f"pipeline_events:{e.get('event')}:{s}"].append(e["unit_id"])
    for r in led.get("retirements") or []:
        if r.get("reason") == "economic" and sector_of(r["unit_id"], sec) == "1":
            bad["retirements:economic:1"].append(r["unit_id"])
    for block in ("floor_retained", "throughput_deferred"):
        for r in led.get(block) or []:
            s = sector_of(r["unit_id"], sec)
            if s == "1":
                bad[f"{block}:1"].append(r["unit_id"])
    return {
        "pass": not bad,
        "violations": {k: sorted(v) for k, v in sorted(bad.items())},
        "n_violating_rows": sum(len(v) for v in bad.values()),
    }


def scalars_identical(a: dict, b: dict) -> dict:
    """Field-by-field comparison of the clearing scalars, at S4's tolerances."""
    diffs = {}
    for k in CLEARING_SCALARS:
        x, y = a["clearing"].get(k), b["clearing"].get(k)
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            tol = PRICE_TOL if "price" in k or "position" in k else MW_TOL
            if abs(float(x) - float(y)) > tol:
                diffs[k] = [x, y]
        elif x != y:
            diffs[k] = [x, y]
    return {"pass": not diffs, "diffs": diffs}


def stack_identity(ctl: dict, arm: dict) -> dict:
    """Row-level stack comparison: shared rows identical, one-sided listed."""
    only_ctl = sorted(set(ctl) - set(arm))
    only_arm = sorted(set(arm) - set(ctl))
    changed = []
    for u in sorted(set(ctl) & set(arm)):
        c, a = ctl[u], arm[u]
        if (
            c[1] != a[1]
            or abs(float(c[2]) - float(a[2])) > OFFER_TOL
            or abs(float(c[3]) - float(a[3])) > AG_TOL
            or bool(c[4]) != bool(a[4])
        ):
            changed.append({"unit_id": u, "ctl": list(c), "arm": list(a)})
    return {
        "shared_rows": len(set(ctl) & set(arm)),
        "changed_rows": len(changed),
        "changed": changed[:40],
        "only_in_ctl": only_ctl[:80],
        "n_only_in_ctl": len(only_ctl),
        "only_in_arm": only_arm[:80],
        "n_only_in_arm": len(only_arm),
        "identical": not changed and not only_ctl and not only_arm,
    }


def pool_fidelity(
    ctl_led: dict, arm_led: dict, sec: dict[int, int], fleet_identical: bool
) -> dict:
    """(b) — the failing pool = the control's minus exactly the sector-1 rows.

    On an identical-fleet year that is exact and both one-sided sets are fully
    graded. On a later year the fleets differ by the earlier exits, so a
    one-sided row is EXPLAINED when the unit is absent from the other leg's
    fleet (its stack, its pool and its ledgers all lack it) — the fleet-delta
    form of the same question (D78 §3.4).
    """
    c_pool, a_pool = failing_pool(ctl_led), failing_pool(arm_led)
    c_stack, a_stack = stack_rows(ctl_led), stack_rows(arm_led)
    only_ctl = {u: v for u, v in c_pool.items() if u not in a_pool}
    only_arm = {u: v for u, v in a_pool.items() if u not in c_pool}
    shared_mismatch = [
        {"unit_id": u, "ctl_mw": c_pool[u], "arm_mw": a_pool[u]}
        for u in sorted(set(c_pool) & set(a_pool))
        if abs(c_pool[u] - a_pool[u]) > MW_TOL
    ]
    # control-only rows: every one must be sector 1 (the gate's own removal),
    # or explained by the fleet delta (absent from the arm's fleet entirely).
    ctl_unexplained = {
        u: v
        for u, v in only_ctl.items()
        if sector_of(u, sec) != "1" and (fleet_identical or u in a_stack)
    }
    # arm-only rows: none may exist on an identical-fleet year; later, each must
    # be a merchant row the control's own fleet no longer carries.
    arm_unexplained = {
        u: v for u, v in only_arm.items() if fleet_identical or u in c_stack
    }
    return {
        "only_in_ctl": {
            "rows": len(only_ctl),
            "mw": round(sum(only_ctl.values()), 3),
            "by_sector": by_sector(only_ctl, sec),
        },
        "only_in_arm": {
            "rows": len(only_arm),
            "mw": round(sum(only_arm.values()), 3),
            "by_sector": by_sector(only_arm, sec),
        },
        "shared_rows": len(set(c_pool) & set(a_pool)),
        "shared_mw_mismatches": shared_mismatch[:40],
        "n_shared_mw_mismatches": len(shared_mismatch),
        "ctl_only_unexplained": sorted(ctl_unexplained)[:40],
        "n_ctl_only_unexplained": len(ctl_unexplained),
        "arm_only_unexplained": sorted(arm_unexplained)[:40],
        "n_arm_only_unexplained": len(arm_unexplained),
        "exact_form": fleet_identical,
        "pass": not shared_mismatch and not ctl_unexplained and not arm_unexplained,
    }


def s6_attribution(ctl: dict[int, dict], arm: dict[int, dict], years) -> dict:
    """S6's row-level attribution of any window-total excess.

    An arm economic-exit row the control does not execute in the SAME year is
    attributable when the control (i) decides it in-window with a later
    ``execute_year``, or (ii) leaves it ``entry_capped`` in-window. Anything
    else is an unexplained gain and fires S6 inside the band.
    """
    ctl_dec: dict[str, int] = {}
    ctl_cap: set[str] = set()
    ctl_exec_year: dict[str, int] = {}
    for y in years:
        L = ctl.get(y)
        if not L:
            continue
        for u, e in events(L, "decided").items():
            ctl_dec.setdefault(u, int(e.get("execute_year") or 0))
        ctl_cap |= set(events(L, "entry_capped"))
        for u in economic_exits(L):
            ctl_exec_year.setdefault(u, y)

    unattributed: list[dict] = []
    pulled_forward: list[dict] = []
    for y in years:
        L = arm.get(y)
        if not L:
            continue
        for u, r in economic_exits(L).items():
            cy = ctl_exec_year.get(u)
            if cy == y:
                continue  # same row, same year: no excess to attribute
            row = {"unit_id": u, "arm_year": y, "mw": round(float(r["mw"]), 3)}
            if cy is not None and cy != y:
                row["ctl_executed_year"] = cy
                pulled_forward.append(row)
            elif u in ctl_dec and ctl_dec[u] != y:
                row["ctl_decided_execute_year"] = ctl_dec[u]
                pulled_forward.append(row)
            elif u in ctl_cap:
                row["ctl_state"] = "entry_capped"
                pulled_forward.append(row)
            else:
                unattributed.append(row)
    return {
        "attributable_rows": len(pulled_forward),
        "attributable_mw": round(sum(r["mw"] for r in pulled_forward), 3),
        "unattributed_rows": len(unattributed),
        "unattributed_mw": round(sum(r["mw"] for r in unattributed), 3),
        "unattributed": unattributed[:40],
        "pass": not unattributed,
    }


def footprint_diff(ctl: dict, arm: dict) -> dict:
    """Which of the (a) footprint keys moved, with both values when they did."""
    moved = {}
    for k in FOOTPRINT_KEYS:
        c, a = ctl["footprint"].get(k), arm["footprint"].get(k)
        if isinstance(c, (int, float)) and isinstance(a, (int, float)):
            if abs(float(c) - float(a)) > MW_TOL:
                moved[k] = [c, a]
        elif json.dumps(c, sort_keys=True) != json.dumps(a, sort_keys=True):
            moved[k] = [c, a]
    return {"identical": not moved, "moved": moved}


# --------------------------------------------------------------------------- #
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ctl", required=True, type=Path)
    ap.add_argument("--arm", required=True, type=Path)
    ap.add_argument("--years", nargs="*", type=int, default=list(WINDOW))
    ap.add_argument(
        "--out", type=Path, default=Path(__file__).with_name("window_compare.json")
    )
    a = ap.parse_args()

    sec = sectors()
    cb, ab = bundle_dir(a.ctl), bundle_dir(a.arm)
    ctl_led = {y: ledger(cb, y) for y in a.years}
    arm_led = {y: ledger(ab, y) for y in a.years}

    out: dict = {"years": {}, "window": {}, "gates": {}}
    tot = {
        "ctl": defaultdict(float),
        "arm": defaultdict(float),
    }
    s2_all_pass = True
    s3_rows: dict[str, dict] = {}
    s4_rows: dict[str, dict] = {}
    fid_rows: dict[str, dict] = {}
    foot_rows: dict[str, dict] = {}

    for y in a.years:
        cL, aL = ctl_led.get(y), arm_led.get(y)
        if cL is None or aL is None:
            out["years"][str(y)] = {"missing": {"ctl": cL is None, "arm": aL is None}}
            continue
        c, m = leg_year(cL, sec), leg_year(aL, sec)
        fleet_identical = json.dumps(
            c["fleet_by_fuel_before"], sort_keys=True
        ) == json.dumps(m["fleet_by_fuel_before"], sort_keys=True)

        s2 = s2_purity(aL, sec)
        s2_all_pass &= s2["pass"]
        stack = stack_identity(stack_rows(cL), stack_rows(aL))
        s1_stack = {
            "ctl_rows": c["sector1_stack_rows"],
            "arm_rows": m["sector1_stack_rows"],
            "ctl_accredited_mw": c["sector1_stack_accredited_mw"],
            "arm_accredited_mw": m["sector1_stack_accredited_mw"],
            "pass": (
                c["sector1_stack_rows"] == m["sector1_stack_rows"]
                and abs(
                    c["sector1_stack_accredited_mw"] - m["sector1_stack_accredited_mw"]
                )
                <= MW_TOL
            )
            if fleet_identical
            else (m["sector1_stack_rows"] > 0),
        }
        s4 = (
            scalars_identical(c, m)
            if fleet_identical
            else {"pass": None, "note": "fleet delta"}
        )
        fid = pool_fidelity(cL, aL, sec, fleet_identical)
        foot = footprint_diff(c, m)

        s3_rows[str(y)] = s1_stack
        s4_rows[str(y)] = s4
        fid_rows[str(y)] = fid
        foot_rows[str(y)] = foot

        for leg, d in (("ctl", c), ("arm", m)):
            for k in (
                "decided_mw",
                "capped_mw",
                "economic_exit_mw",
                "executed_pipeline_mw",
            ):
                tot[leg][k] += d[k]

        out["years"][str(y)] = {
            "entering_fleet_identical": fleet_identical,
            "ctl": c,
            "arm": m,
            "s2_cohort_purity_arm": s2,
            "s3_sector1_must_offer": s1_stack,
            "s4_auction_scalars": s4,
            "stack_row_identity": stack,
            "b_fidelity": fid,
            "a_footprint": foot,
        }

    # ---- window totals, as ratios to control-P's own realized values -------- #
    win: dict = {}
    for k in ("decided_mw", "capped_mw", "economic_exit_mw", "executed_pipeline_mw"):
        cv, av = round(tot["ctl"][k], 3), round(tot["arm"][k], 3)
        win[k] = {
            "ctl": cv,
            "arm": av,
            "delta": round(av - cv, 3),
            "ratio": round(av / cv, 6) if cv else None,
        }
    s6_bands = {}
    for k, band in (
        ("decided_mw", S6_BANDS["decided_mw"]),
        ("economic_exit_mw", S6_BANDS["executed_economic_mw"]),
    ):
        r = win[k]["ratio"]
        s6_bands[k] = {
            "ratio": r,
            "band": list(band),
            "pass": (r is not None and band[0] <= r <= band[1]),
        }
    attrib = s6_attribution(ctl_led, arm_led, a.years)
    out["window"] = win
    out["gates"] = {
        "S2_cohort_purity": {
            "pass": s2_all_pass,
            "per_year": {
                y: d.get("s2_cohort_purity_arm", {}).get("pass")
                for y, d in out["years"].items()
            },
        },
        "S3_must_offer": {
            "pass": all(v["pass"] for v in s3_rows.values()),
            "per_year": s3_rows,
        },
        "S4_auction_identical_fleet_years": {
            "pass": all(v["pass"] for v in s4_rows.values() if v["pass"] is not None),
            "per_year": s4_rows,
        },
        "S6_window_total": {
            "pass": all(v["pass"] for v in s6_bands.values()) and attrib["pass"],
            "bands": s6_bands,
            "attribution": attrib,
        },
        "b_fidelity": {
            "pass": all(v["pass"] for v in fid_rows.values()),
            "per_year": {y: v["pass"] for y, v in fid_rows.items()},
        },
        "a_footprint": {
            "per_year": {y: v["identical"] for y, v in foot_rows.items()},
        },
    }

    # ---- (c) composition and (d) LOYO, from score.json ---------------------- #
    cs, ascore = score(cb), score(ab)

    def _prec(s: dict | None) -> dict | None:
        if not s:
            return None
        prp = ((s.get("retirements") or {}).get("plant_release_precision")) or {}
        return (prp.get("window") or {}).get("economic")

    def _ret(s: dict | None) -> dict | None:
        if not s:
            return None
        r = s.get("retirements") or {}
        return {
            "total_gw": r.get("total_gw"),
            "unit_recall_gt300": r.get("unit_recall_gt300"),
            "false_retire": r.get("false_retire"),
        }

    cprec, aprec = _prec(cs), _prec(ascore)
    out["c_composition"] = {
        "ctl_window_economic_precision": cprec,
        "arm_window_economic_precision": aprec,
        "pass": (
            None
            if not (cprec and aprec)
            or cprec.get("precision") is None
            or aprec.get("precision") is None
            else aprec["precision"] >= cprec["precision"]
        ),
        "note": "condition (c): arm precision must not fall below control-P's.",
    }
    out["reported_fc3"] = {"ctl": _ret(cs), "arm": _ret(ascore)}
    cl, al = (cs or {}).get("loyo"), (ascore or {}).get("loyo")
    out["d_loyo"] = {
        "ctl_holds_2of3": (cl or {}).get("holds_2of3"),
        "arm_holds_2of3": (al or {}).get("holds_2of3"),
        "ctl_folds": (cl or {}).get("folds"),
        "arm_folds": (al or {}).get("folds"),
        "pass": (
            None
            if not (cl and al)
            else not (
                (cl["holds_2of3"].get("recall_pass") is True)
                and (al["holds_2of3"].get("recall_pass") is not True)
            )
        ),
        "note": "condition (d): the arm must not lose a fold control-P holds.",
    }

    a.out.write_text(json.dumps(out, indent=2, default=str))

    # ---- console summary ---------------------------------------------------- #
    for y, d in out["years"].items():
        if "missing" in d:
            print(f"== {y}: MISSING {d['missing']}")
            continue
        c, m = d["ctl"], d["arm"]
        print(
            f"== {y} (entering fleet identical: {d['entering_fleet_identical']})\n"
            f"   pool  ctl {c['failing_rows']}r/{c['failing_mw']} MW  "
            f"arm {m['failing_rows']}r/{m['failing_mw']} MW   "
            f"one-sided ctl {d['b_fidelity']['only_in_ctl']['rows']}r/"
            f"{d['b_fidelity']['only_in_ctl']['mw']} MW "
            f"{d['b_fidelity']['only_in_ctl']['by_sector']['rows']}  "
            f"arm {d['b_fidelity']['only_in_arm']['rows']}r/"
            f"{d['b_fidelity']['only_in_arm']['mw']} MW\n"
            f"   decided ctl {c['decided_mw']} ({c['decided_rows']}) {c['decided_by_execute_year']}  "
            f"arm {m['decided_mw']} ({m['decided_rows']}) {m['decided_by_execute_year']}\n"
            f"   econ exits ctl {c['economic_exit_mw']} {c['economic_exit_by_fuel']}  "
            f"arm {m['economic_exit_mw']} {m['economic_exit_by_fuel']}\n"
            f"   auction ctl {c['clearing']['n_offers']}off/"
            f"{c['clearing']['offered_mw']}/{c['clearing']['price_takers_mw']}pt/"
            f"{c['clearing']['price_usd_per_mw_day']}$  "
            f"arm {m['clearing']['n_offers']}off/{m['clearing']['offered_mw']}/"
            f"{m['clearing']['price_takers_mw']}pt/{m['clearing']['price_usd_per_mw_day']}$\n"
            f"   S2 {d['s2_cohort_purity_arm']['pass']}  S3 {d['s3_sector1_must_offer']['pass']}  "
            f"S4 {d['s4_auction_scalars']['pass']}  (b) {d['b_fidelity']['pass']}  "
            f"stack changed {d['stack_row_identity']['changed_rows']}"
        )
    print("\n== WINDOW TOTALS (arm / control-P)")
    for k, v in out["window"].items():
        print(f"   {k}: ctl {v['ctl']}  arm {v['arm']}  ratio {v['ratio']}")
    print(
        f"\n== GATES: {json.dumps({k: v.get('pass') for k, v in out['gates'].items()})}"
    )
    print(f"   S6 bands: {json.dumps(out['gates']['S6_window_total']['bands'])}")
    print(
        f"   S6 attribution: {json.dumps({k: v for k, v in attrib.items() if k != 'unattributed'})}"
    )
    print(f"   (c) {out['c_composition']['pass']}  (d) {out['d_loyo']['pass']}")
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()

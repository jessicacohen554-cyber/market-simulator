"""capx D52 A/B instrument (ZERO solves): the arm's committed ledgers beside the
control's, on the published NYCA basis.

    uv run python docs/handoffs/d52/ab-compare-2026-09-04.py <control run_dir> <arm run_dir> [<probe run_dir>]

Per scored year: the ledger requirement (LP-peak basis) and the NEW seam fields
(``screen_peak_demand_mw`` / ``screen_adequacy_requirement_mw`` /
``screen_entering_firm_mw`` / ``screen_reserve_position`` — written by every
solve since capx D52), the published Table D.2 requirement and SOM position,
the position gap in points, HEAD's vintage curve at the seam position, the
admission-cap exit budget, and the exits / entries / pipeline events. For a
control that predates D52 (no seam fields) the seam requirement is
reconstructed from HEAD's composite on the growth-scaled peak and the entering
firm from ``fleet_by_fuel_before`` at class EFORd (the PREDECL §1 method),
labelled ``reconstructed``. Then: the score.json FC-3 rows side by side, the
rule-22 LOYO sign test on |position − published| (folds over 2023–2025), and the
D45 P9 (a)/(b)/(c) grade for a probe leg. Rows + stdout are committed beside
this file. Nothing here feeds a solve.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.capacity_market import (  # noqa: E402
    ADEQUACY_EXTERNAL_TIE_FIRM_MW,
    PLANNING_RESERVE_MARGIN_BY_ISO,
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO,
    evaluate_demand_curve,
    resolve_demand_curve_vintage,
)
from market_sim.config.constants import EFORD  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    thermal_accreditation_fraction,
)

PUB = {
    int(r["capability_year"][:4]): r
    for r in json.loads(
        (Path(__file__).parent.parent / "d45" / "published-positions-2026-09-03.json").read_text()
    )["nyiso"]
}
HEAD_FACTOR = (1.0 + PLANNING_RESERVE_MARGIN_BY_ISO["NYISO"]) * (
    PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["NYISO"]
)
SCORED = (2023, 2024, 2025)
TARGET_TOTAL_GW = 1.711  # capacity_actuals_nyiso (2026-09-02 rebuild), retire.total_gw
FALSE_RETIRE_BAND = 0.15


def curve_price(year: int, pos: float | None) -> float | None:
    if pos is None:
        return None
    v = resolve_demand_curve_vintage("NYISO", year)
    if not v.demand_curve:
        return None
    return evaluate_demand_curve(v.demand_curve, pos) * v.net_cone_curve_per_kw_yr


def load_run(run_dir: Path) -> tuple[dict, Path, dict[int, dict], dict]:
    meta = json.loads((run_dir / "meta.json").read_text())
    bundle = REPO / meta["bundle"]
    leds = {int(p.stem.split("_")[1]): json.loads(p.read_text()) for p in bundle.glob("evolution_*.json")}
    score = json.loads((bundle / "score.json").read_text()) if (bundle / "score.json").exists() else {}
    return meta, bundle, leds, score


def reconstructed_entering_firm(led: dict, prev: dict | None) -> float:
    """PREDECL §1 method: fleet_by_fuel_before at class EFORd + prior-year pools + hydro/storage/tie."""
    pools = prev or led
    cred = led.get("renewable_credit_applied") or {}
    thermal = sum(
        mw * thermal_accreditation_fraction(f, EFORD.get(f, 0.05), "NYISO")
        for f, mw in (led.get("fleet_by_fuel_before") or {}).items()
    )
    wind = float(pools.get("wind_cap_mw") or 0.0) * float(cred.get("wind", 0.0))
    solar = float(pools.get("solar_cap_mw") or 0.0) * float(cred.get("solar", 0.0))
    return (
        thermal
        + wind
        + solar
        + float(led.get("firm_clean_accredited_mw") or 0.0)
        + float(pools.get("storage_firm_mw") or 0.0)
        + ADEQUACY_EXTERNAL_TIE_FIRM_MW["NYISO"]
    )


def year_rows(run_dir: Path, seam_peaks: dict[int, float] | None = None) -> dict:
    """Per-year rows; ``seam_peaks`` (year -> MW) lets a pre-D52 control borrow the
    arm's recorded seam peak — the seam peak is the growth-scaled weather-year
    load and does not depend on the requirement gates, so it is identical across
    the A/B; the control's seam requirement is then HEAD's composite on it."""
    meta, bundle, leds, score = load_run(run_dir)
    rows, prev_solved = {}, None
    for y in sorted(leds):
        led = leds[y]
        r = dict(year=y, bridge=bool(led.get("bridge")))
        if led.get("bridge"):
            r["exits"] = _exits(led)
            r["seam"] = {k: led.get(k) for k in ("screen_peak_demand_mw", "screen_adequacy_requirement_mw", "screen_entering_firm_mw", "screen_reserve_position")}
            rows[y] = r
            continue
        peak, rm = led.get("peak_demand_mw"), led.get("reserve_margin")
        r.update(
            ledger_peak_mw=peak,
            ledger_requirement_mw=led.get("adequacy_requirement_mw"),
            firm_after_mw=(peak * (1.0 + rm)) if (peak and rm is not None) else None,
            ledger_position=led.get("capacity_reserve_position"),
        )
        seam_req = led.get("screen_adequacy_requirement_mw")
        seam_firm = led.get("screen_entering_firm_mw")
        seam_pos = led.get("screen_reserve_position")
        seam_peak = led.get("screen_peak_demand_mw")
        source = "ledger (D52 seam fields)"
        if seam_req is None and prev_solved is not None:
            # Pre-D52 control: reconstruct (PREDECL §1). The seam peak is not
            # recorded; back the requirement out only when a ledger position
            # exists, else fall back to the composite on the LP peak (flagged).
            seam_firm = reconstructed_entering_firm(led, prev_solved)
            if led.get("capacity_reserve_position"):
                seam_req = seam_firm / led["capacity_reserve_position"]
                seam_peak = seam_req / HEAD_FACTOR
                source = "reconstructed (firm from fleet_by_fuel_before; requirement backed out of the ledger position)"
            elif seam_peaks and seam_peaks.get(y):
                seam_peak = float(seam_peaks[y])
                seam_req = seam_peak * HEAD_FACTOR
                source = "reconstructed (firm from fleet_by_fuel_before; seam peak borrowed from the arm's ledger; requirement = HEAD composite on it)"
            else:
                seam_req = None
                source = "reconstructed firm only (curve-OFF control: no ledger position, seam requirement unknown)"
            seam_pos = (seam_firm / seam_req) if seam_req else None
        r.update(
            seam_source=source,
            seam_peak_mw=seam_peak,
            seam_requirement_mw=seam_req,
            seam_entering_firm_mw=seam_firm,
            seam_position=seam_pos,
        )
        pub = PUB.get(y)
        if pub:
            r.update(
                published_peak_mw=pub["nysrc_peak_mw"],
                published_requirement_mw=pub["ucap_requirement_mw"],
                published_position=pub["pos_published"],
                real_spot_kw_yr=pub["spot_kw_yr"],
                curve_at_published=curve_price(y, pub["pos_published"]),
                requirement_gap_vs_published_mw=(seam_req - pub["ucap_requirement_mw"]) if seam_req else None,
                position_gap_pts=((seam_pos - pub["pos_published"]) * 100.0) if seam_pos else None,
                curve_at_seam_position=curve_price(y, seam_pos),
                exit_budget_mw=(seam_firm - seam_req) if (seam_firm and seam_req) else None,
            )
        r["exits"] = _exits(led)
        r["entry_decided_mw_by_tech"] = led.get("entry_decided_mw_by_tech")
        r["thermal_additions_mw"] = sum(float(a.get("mw") or 0.0) for a in (led.get("thermal_additions") or []) if isinstance(a, dict))
        ev = [e for e in (led.get("pipeline_events") or []) if isinstance(e, dict)]
        by = {}
        for e in ev:
            k = f"{e.get('event')}:{e.get('fuel')}"
            by[k] = by.get(k, 0.0) + float(e.get("mw") or 0.0)
        r["pipeline_events_mw"] = by
        r["backstop_mw"] = led.get("reserve_backstop_mw") or led.get("backstop_build_mw")
        rows[y] = r
        prev_solved = led
    return dict(run=run_dir.name, cache_key=meta.get("cache_key"), git=meta.get("git"), years=rows, score=_fc3(score))


def _exits(led: dict) -> dict:
    out = {}
    for e in led.get("retirements") or []:
        if isinstance(e, dict):
            k = f"{e.get('fuel')}:{e.get('reason') or e.get('channel') or '?'}"
            out[k] = out.get(k, 0.0) + float(e.get("mw") or 0.0)
    return out


def _fc3(score: dict) -> dict:
    """The FC-3 rows a T1-H is graded on, pulled tolerant of the scorer's shape."""
    keep = {}

    def walk(prefix: str, obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                walk(f"{prefix}.{k}" if prefix else str(k), v)
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            if any(t in prefix for t in ("retire", "false_retire", "recall", "add.", "additions", "loyo", "band", "status", "backstop")):
                keep[prefix] = obj

    walk("", score)
    return keep


def loyo_sign_test(control: dict, arm: dict) -> list[dict]:
    """Rule 22 on a zero-parameter mechanism: per-year |position − published| OFF vs ON."""
    folds = []
    err = {}
    for y in SCORED:
        c, a = control["years"].get(y, {}), arm["years"].get(y, {})
        if c.get("position_gap_pts") is None or a.get("position_gap_pts") is None:
            continue
        err[y] = (abs(c["position_gap_pts"]), abs(a["position_gap_pts"]))
    for held in err:
        train = [y for y in err if y != held]
        train_arms = all(err[y][1] < err[y][0] for y in train)
        held_improves = err[held][1] < err[held][0]
        folds.append(
            dict(
                held_out=held,
                train_years=train,
                train_arms=train_arms,
                held_out_err_off_pts=err[held][0],
                held_out_err_on_pts=err[held][1],
                fold="PASS" if (not train_arms or held_improves) else "FAIL",
                note="held-out improves" if held_improves else "held-out degrades",
            )
        )
    return folds


def p9_grade(leg: dict) -> dict:
    """D45 P9 (a)/(b)/(c) verbatim on a probe leg."""
    s = leg["score"]
    total = s.get("retirements.total_gw.model")
    false_r = s.get("retirements.false_retire.frac_of_model")
    gaps = {y: leg["years"][y].get("position_gap_pts") for y in SCORED if y in leg["years"]}
    return dict(
        a_total_within_10pct=(abs(total / TARGET_TOTAL_GW - 1.0) <= 0.10) if isinstance(total, (int, float)) else None,
        a_total_gw=total,
        a_target_gw=TARGET_TOTAL_GW,
        b_false_retire_in_band=(false_r <= FALSE_RETIRE_BAND) if isinstance(false_r, (int, float)) else None,
        b_false_retire=false_r,
        c_positions_within_3pts=all(g is not None and abs(g) <= 3.0 for g in gaps.values()) if gaps else None,
        c_gaps_pts=gaps,
    )


def reopen_condition(arm: dict) -> dict:
    gaps = {y: arm["years"][y].get("position_gap_pts") for y in SCORED if y in arm["years"]}
    met = all(g is not None and abs(g) <= 3.0 for g in gaps.values()) and len(gaps) == len(SCORED)
    return dict(condition="repaired L2 seam positions within ±3 pts of published in EVERY scored year", gaps_pts=gaps, met=met,
                failing_years={y: g for y, g in gaps.items() if g is None or abs(g) > 3.0})


if __name__ == "__main__":
    arm = year_rows(Path(sys.argv[2]))
    arm_seam_peaks = {y: r.get("seam_peak_mw") for y, r in arm["years"].items() if r.get("seam_peak_mw")}
    control = year_rows(Path(sys.argv[1]), seam_peaks=arm_seam_peaks)
    probe = year_rows(Path(sys.argv[3])) if len(sys.argv) > 3 else None
    out = dict(
        head_factor=HEAD_FACTOR,
        control=control,
        arm=arm,
        probe=probe,
        loyo=loyo_sign_test(control, arm),
        reopen=reopen_condition(arm),
        p9_probe=p9_grade(probe) if probe else None,
        fc3_diff={k: (control["score"].get(k), arm["score"].get(k)) for k in sorted(set(control["score"]) | set(arm["score"])) if control["score"].get(k) != arm["score"].get(k)},
    )
    Path(__file__).with_suffix(".json").write_text(json.dumps(out, indent=1, default=float))
    for name, leg in (("control", control), ("arm", arm), ("probe", probe)):
        if not leg:
            continue
        print(f"== {name}: {leg['run']} key {leg['cache_key']}")
        for y, r in leg["years"].items():
            if r.get("bridge"):
                print(f"  {y} bridge seam={r.get('seam')} exits={r['exits']}")
                continue

            def f(v, d=0):
                return "-" if v is None else f"{v:,.{d}f}"

            print(
                f"  {y} peak ledger/seam/pub {f(r.get('ledger_peak_mw'))}/{f(r.get('seam_peak_mw'))}/{f(r.get('published_peak_mw'))}"
                f" | req ledger/seam/pub {f(r.get('ledger_requirement_mw'))}/{f(r.get('seam_requirement_mw'))}/{f(r.get('published_requirement_mw'))}"
                f" | firm enter {f(r.get('seam_entering_firm_mw'))} after {f(r.get('firm_after_mw'))}"
                f" | pos seam {f(r.get('seam_position'),4)} ledger {f(r.get('ledger_position'),4)} pub {f(r.get('published_position'),3)} gap {f(r.get('position_gap_pts'),1)} pts"
                f" | curve@seam ${f(r.get('curve_at_seam_position'),2)} @pub ${f(r.get('curve_at_published'),2)} real ${f(r.get('real_spot_kw_yr'),2)}"
                f" | budget {f(r.get('exit_budget_mw'))} | exits {r['exits']} | entry {r.get('entry_decided_mw_by_tech')} | events {r.get('pipeline_events_mw')} | {r.get('seam_source')}"
            )
    print("== LOYO sign test (arm vs control)")
    for fl in out["loyo"]:
        print("  ", fl)
    print("== §6 re-open condition:", out["reopen"])
    if probe:
        print("== P9 grade (probe):", out["p9_probe"])
    print("== FC-3 rows that differ (control, arm):")
    for k, v in out["fc3_diff"].items():
        print("  ", k, v)
    if not out["fc3_diff"]:
        print("   none — byte-identical FC-3")

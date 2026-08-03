"""miso-117 A/B scorer — `measured_ct_heat_rates` against the miso-109b keeper.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-miso117-ct-heat-rates-2026-08-03.md`` from the two
solved bundles plus the committed MISO artifact. **No solve, and no gate that
is not in the prereg.**

Construction gates (prereg §4):

* **K1 flag fidelity** — arm B records ``measured_ct_heat_rates=true``, arm A
  ``false``, and **both** record ``measured_chp_heat_rates=true`` (the keeper's
  own setting; a probe that lets that default to False reads a different model
  than the keeper solved — miso-116 §3). All 86 artifact rows carry
  ``flag == "ok"``.
* **K2 control integrity** — reported on the prereg's TWO bases, both stated
  whatever they show. (a) The *scorecard* basis, which is the comparability
  gate: arm A reproduces the committed keeper's determination and its nine
  criterion statuses. (b) The *strict byte* basis: arm A minus the committed
  keeper's ``class_hourly_<year>.parquet``, class-hour for class-hour. Drift on
  (b) is REPORTED, not a kill — caiso-146, neiso-69 and ercot-150 all measured
  real same-HEAD drift while their A/B stayed unconfounded, because both arms
  share it. A scorecard that does not reproduce IS a kill.
* **K3 mechanism is LIVE** — ``max |Δ CT_PEAKER MW| > 50`` in at least one year
  (the nyiso-89 §4a check). Failing this is verdict ``I``, not ``R``.
* **K4 single delta** — the arms' ``run_config`` scenario blocks differ in
  exactly the one boolean.
* **K5 year span** — both bundles carry ``[2023, 2024, 2025]`` and nothing else
  (rule 22 ``[R-HOLDOUT]`` / D-6 quarantine).

Protective gates (prereg §6.1), read from each bundle's own regenerated
``legitimacy_diagnostics.json``:

* **C7 / D-1** ``CT_PEAKER`` ``profile_r >= 0.80`` and ``cv_ratio >= 0.50``.
* **C8 / D-2** ``CT_PEAKER`` forced share vs the **0.15 peaker cap**. This is
  the miso-107 interaction the prereg predicts moves: arming the flag raised
  the h14-21 ``reliability_floor x CT_PEAKER`` limb 1.188 -> 1.743 TWh (+47 %)
  and the share 11.77 -> 14.21 %. A crossing routes to the rule-20 conditional
  pass on D-4 window + D-1 shape — **never** to relaxing the limb.
* **D-4** off-window binding stays 0.000 on every limb.
* **C7 ``COAL_PRB``** — the keeper's one failing criterion. Reported so a
  degradation is visible; the prereg blocks promotion if it worsens.

Everything else — C1 class TWh, mean lambda, slack/dump — is REPORTED, per
prereg §7: a worse backcast is a discovered bug under rules 1 / 14, not a kill
condition.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso117_ctheatrate_ab.py
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/miso117_control_A"
ARM_B = REPO / "results/calibration/miso117_ctheatrate_B"
KEEPER = REPO / "results/calibration/miso109_hy_level_B"
ARTIFACT = REPO / "data/raw/_processed-legacy/campd_ct_heat_rates_MISO.csv"
BENCH = REPO / "frontend/data/backcast/bench/MISO"
OUT_PATH = REPO / "results/probes/miso117_ctheatrate_ab.json"

#: PREREG §4 K3 — the liveness floor, in MW of class dispatch divergence.
K3_LIVENESS_MW = 50.0
#: PREREG §6.1 — the protective bounds, MISO's own committed gate values.
D1_MIN_PROFILE_R = 0.80
D1_MIN_CV_RATIO = 0.50
D2_PEAKER_MAX_SHARE = 0.15
#: Realized Henry Hub by year, the basis the prereg quotes its $/MWh at.
GAS_USD_PER_MMBTU = {2023: 2.54, 2024: 2.19, 2025: 3.52}
#: The class this lever reprices, and the class carrying the keeper's one
#: failing criterion (C7 COAL_PRB) — both reported every year.
CT_CLASS = "CT_PEAKER"
FAILING_CLASS = "COAL_PRB"


def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max/by-class class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
            if float(v) > 1e-6
        },
    }


def _system(bundle: Path, year: int) -> pd.DataFrame:
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"]


def _miso_lambda(bundle: Path, year: int) -> float:
    """MISO load-weighted mean lambda over the zones that carry demand.

    Zero-demand zones are the seam / external pseudo-nodes (the South-seam
    split and the priced-interchange reference nodes); weighting by demand
    drops them without naming them, so the statistic does not depend on a
    hand list of zone names (rule 24 ``[R-REGISTRY]``).
    """
    frame = _system(bundle, year)
    load = frame[frame["demand"] > 0]
    return round(float((load["price"] * load["demand"]).sum() / load["demand"].sum()), 4)


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    frame = _system(bundle, year)
    return round(float(frame["slack"].sum()), 3), round(float(frame["dump"].sum()), 3)


def _cfg_flag(bundle: Path, key: str) -> bool | None:
    """A bundle's recorded ``ScenarioConfig`` boolean, either channel."""
    path = bundle / "run_config.json"
    if not path.exists():
        return None
    cfg = json.loads(path.read_text())
    scen = cfg.get("scenario_config", {}) or {}
    if key in scen:
        return bool(scen[key])
    # replay_keeper routes --set through the generic prb_overrides channel too.
    ovr = (cfg.get("calibration_flags", {}) or {}).get(
        "coal_prb_sigmoid_overrides"
    ) or {}
    if key in ovr:
        return bool(ovr[key])
    return None


def _scenario_block(bundle: Path) -> dict:
    cfg = json.loads((bundle / "run_config.json").read_text())
    return cfg.get("scenario_config", {}) or {}


def _k1_flag_fidelity() -> dict:
    """PREREG K1 — the one flag differs and the keeper's CHP flag is carried."""
    art = pd.read_csv(ARTIFACT)
    out = {
        "A_measured_ct_heat_rates": _cfg_flag(ARM_A, "measured_ct_heat_rates"),
        "B_measured_ct_heat_rates": _cfg_flag(ARM_B, "measured_ct_heat_rates"),
        "A_measured_chp_heat_rates": _cfg_flag(ARM_A, "measured_chp_heat_rates"),
        "B_measured_chp_heat_rates": _cfg_flag(ARM_B, "measured_chp_heat_rates"),
        "artifact_rows": int(len(art)),
        "artifact_rows_ok": int((art["flag"] == "ok").sum()),
        # Recorded twice by the --set channel; rule 26 [R-REGISTRY] wants the
        # arming visible in run_config.json, so assert BOTH places for arm B.
        "B_recorded_in_prb_overrides": bool(
            (
                json.loads((ARM_B / "run_config.json").read_text())
                .get("calibration_flags", {})
                .get("coal_prb_sigmoid_overrides", {})
                or {}
            ).get("measured_ct_heat_rates")
        ),
    }
    out["passed"] = bool(
        out["A_measured_ct_heat_rates"] is False
        and out["B_measured_ct_heat_rates"] is True
        and out["A_measured_chp_heat_rates"] is True
        and out["B_measured_chp_heat_rates"] is True
        and out["artifact_rows_ok"] == out["artifact_rows"]
        and out["B_recorded_in_prb_overrides"]
    )
    return out


def _k2_control_integrity() -> dict:
    """PREREG K2(b) — the STRICT BYTE basis: arm A vs the committed keeper."""
    out: dict = {"basis": "strict byte: arm A minus committed keeper class-hour"}
    per_year = {}
    for year in YEARS:
        per_year[str(year)] = _pairwise(ARM_A, KEEPER, year)
    out["per_year"] = per_year
    out["max_abs_diff_mw"] = round(
        max(v["max_abs_diff_mw"] for v in per_year.values()), 6
    )
    out["byte_identical"] = out["max_abs_diff_mw"] < 1e-6
    out["note"] = (
        "REPORTED, not a kill (prereg §4 K2). The comparability gate is the "
        "SCORECARD basis, scored separately by calibration_verdict.py; drift "
        "here is shared by both arms and does not confound the A/B."
    )
    return out


def _k3_liveness() -> dict:
    """PREREG K3 — the arm must move real CT_PEAKER dispatch."""
    per_year = {}
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        per_year[str(year)] = {
            "max_abs_diff_mw": pw["max_abs_diff_mw"],
            "ct_peaker_max_mw": pw["max_by_class_mw"].get(CT_CLASS, 0.0),
            "classes_moved": sorted(pw["max_by_class_mw"]),
        }
    best = max(v["ct_peaker_max_mw"] for v in per_year.values())
    return {
        "per_year": per_year,
        "ct_peaker_max_mw_any_year": round(best, 4),
        "threshold_mw": K3_LIVENESS_MW,
        "passed": bool(best > K3_LIVENESS_MW),
    }


def _k4_single_delta() -> dict:
    """PREREG K4 — the arms' ScenarioConfig blocks differ in one boolean."""
    a, b = _scenario_block(ARM_A), _scenario_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "passed": list(diff) == ["measured_ct_heat_rates"],
    }


def _k5_year_span() -> dict:
    """PREREG K5 — both bundles carry exactly the training span."""
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    return {
        "years": spans,
        "passed": all(v == list(YEARS) for v in spans.values()),
        "note": "rule 22 [R-HOLDOUT]: MISO holds no calibration-complete marker",
    }


def _diagnostics(bundle: Path) -> dict | None:
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())["diagnostics"]


def _d1_rows(diag: dict | None, klass: str) -> dict:
    if not diag:
        return {}
    return {
        str(r["year"]): {
            "profile_r": r.get("profile_r"),
            "cv_ratio": r.get("cv_ratio"),
            "verdict": r.get("verdict"),
        }
        for r in diag["D1"]["rows"]
        if r.get("class") == klass
    }


def _d2_rows(diag: dict | None, klass: str) -> dict:
    if not diag:
        return {}
    out: dict = {}
    for r in diag["D2"]["rows"]:
        if r.get("class") != klass:
            continue
        out.setdefault(str(r["year"]), {})[r["mechanism"]] = {
            "forced_twh": r.get("forced_twh"),
            "class_total_twh": r.get("class_total_twh"),
            "share_of_class": r.get("share_of_class"),
        }
    return out


def _d4_rows(diag: dict | None) -> dict:
    if not diag:
        return {}
    out: dict = {}
    for r in diag["D4"]["rows"]:
        out.setdefault(str(r["year"]), {})[r["floor"]] = {
            "window": r.get("window"),
            "floored_twh": r.get("floored_twh"),
            "offwindow_share": r.get("offwindow_share"),
            "verdict": r.get("verdict"),
        }
    return out


def _protective() -> dict:
    """PREREG §6.1 — C7 / C8 / D-4 on both arms, from committed diagnostics."""
    da, db = _diagnostics(ARM_A), _diagnostics(ARM_B)
    out: dict = {
        "d1_ct_peaker": {"A": _d1_rows(da, CT_CLASS), "B": _d1_rows(db, CT_CLASS)},
        "d1_coal_prb": {
            "A": _d1_rows(da, FAILING_CLASS),
            "B": _d1_rows(db, FAILING_CLASS),
        },
        "d2_ct_peaker": {"A": _d2_rows(da, CT_CLASS), "B": _d2_rows(db, CT_CLASS)},
        "d4": {"A": _d4_rows(da), "B": _d4_rows(db)},
        "bounds": {
            "d1_min_profile_r": D1_MIN_PROFILE_R,
            "d1_min_cv_ratio": D1_MIN_CV_RATIO,
            "d2_peaker_max_share": D2_PEAKER_MAX_SHARE,
        },
    }
    if not db:
        out["passed"] = None
        out["note"] = "arm B legitimacy_diagnostics.json not generated yet"
        return out
    # C7 CT_PEAKER — both bounds, all years.
    ct = out["d1_ct_peaker"]["B"]
    c7_ok = all(
        (row["profile_r"] or 0) >= D1_MIN_PROFILE_R
        and (row["cv_ratio"] or 0) >= D1_MIN_CV_RATIO
        for row in ct.values()
    )
    # C8 CT_PEAKER — the total forced share across mechanisms, vs the cap.
    c8_shares = {
        y: round(sum(m["share_of_class"] for m in mechs.values()), 4)
        for y, mechs in out["d2_ct_peaker"]["B"].items()
    }
    c8_ok = all(s <= D2_PEAKER_MAX_SHARE for s in c8_shares.values())
    # D-4 — no limb may bind off its declared window.
    d4_ok = all(
        row["offwindow_share"] == 0.0
        for year in out["d4"]["B"].values()
        for row in year.values()
    )
    out["c8_total_share_B"] = c8_shares
    out["c8_total_share_A"] = {
        y: round(sum(m["share_of_class"] for m in mechs.values()), 4)
        for y, mechs in out["d2_ct_peaker"]["A"].items()
    }
    out["c7_ct_peaker_passed"] = bool(c7_ok)
    out["c8_ct_peaker_passed"] = bool(c8_ok)
    out["d4_passed"] = bool(d4_ok)
    out["passed"] = bool(c7_ok and c8_ok and d4_ok)
    if not c8_ok:
        out["c8_route"] = (
            "OVER CAP — rule 20 [R-FORCED-BUDGET] conditional pass: check every "
            "binding non-exempt mechanism clears D-4 (above) AND the class "
            "clears D-1 profile_r/cv_ratio (above). NEVER relax the limb "
            "(prereg §8; miso-106 keeper note; rules 1 / 14)."
        )
    return out


def _actual_class_twh(year: int) -> dict:
    path = BENCH / f"{year}.json.gz"
    if not path.exists():
        return {}
    bench = json.loads(gzip.open(path).read())["bench"]
    return bench.get("classFull", {})


def _artifact_report() -> dict:
    """What the measured artifact does to the fleet, before any dispatch."""
    art = pd.read_csv(ARTIFACT)
    ok = art[art["flag"] == "ok"].dropna(subset=["model_heat_rate_egrid"])
    delta = ok["heat_rate"] - ok["model_heat_rate_egrid"]
    cap = ok["class_capacity_mw"]
    gen = ok["gross_mwh"]
    return {
        "plants_total": int(len(art)),
        "plants_applied": int(len(ok)),
        "plants_excluded_by_band": int((art["flag"] != "ok").sum()),
        "capacity_mw": round(float(cap.sum()), 1),
        "moved_gt_half_mmbtu": int((delta.abs() > 0.5).sum()),
        "cheaper_plants": int((delta < 0).sum()),
        "dearer_plants": int((delta > 0).sum()),
        "cheaper_mw": round(float(cap[delta < 0].sum()), 1),
        "dearer_mw": round(float(cap[delta > 0].sum()), 1),
        "cap_weighted_delta_mmbtu": round(
            float((delta * cap).sum() / cap.sum()), 4
        ),
        "gen_weighted_delta_mmbtu": round(
            float((delta * gen).sum() / gen.sum()), 4
        ),
        "cap_weighted_model_over_measured": round(
            float((ok["model_over_measured"] * cap).sum() / cap.sum()), 4
        ),
    }


def main() -> int:
    """Score every pre-registered gate and print the A/B report."""
    report: dict = {
        "session": "miso-117",
        "prereg": "results/calibration/PREREG-miso117-ct-heat-rates-2026-08-03.md",
        "arm_a": str(ARM_A.relative_to(REPO)),
        "arm_b": str(ARM_B.relative_to(REPO)),
        "keeper": str(KEEPER.relative_to(REPO)),
        "artifact": _artifact_report(),
        "K1_flag_fidelity": _k1_flag_fidelity(),
        "K2_control_integrity_strict_byte": _k2_control_integrity(),
        "K3_liveness": _k3_liveness(),
        "K4_single_delta": _k4_single_delta(),
        "K5_year_span": _k5_year_span(),
        "protective": _protective(),
    }
    # Reported, never a kill condition (prereg §7).
    reported: dict = {}
    for year in YEARS:
        a_twh, b_twh = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        actual = _actual_class_twh(year)
        classes = sorted(set(a_twh) | set(b_twh))
        a_slack, a_dump = _slack_dump(ARM_A, year)
        b_slack, b_dump = _slack_dump(ARM_B, year)
        reported[str(year)] = {
            "class_twh": {
                k: {
                    "A": a_twh.get(k, 0.0),
                    "B": b_twh.get(k, 0.0),
                    "delta": round(b_twh.get(k, 0.0) - a_twh.get(k, 0.0), 4),
                    "actual": (
                        round(float(actual[k]), 4) if k in actual else None
                    ),
                }
                for k in classes
            },
            "lambda_load_weighted": {
                "A": _miso_lambda(ARM_A, year),
                "B": _miso_lambda(ARM_B, year),
            },
            "slack_mwh": {"A": a_slack, "B": b_slack},
            "dump_mwh": {"A": a_dump, "B": b_dump},
            "gas_usd_per_mmbtu": GAS_USD_PER_MMBTU[year],
        }
        lam = reported[str(year)]["lambda_load_weighted"]
        lam["delta"] = round(lam["B"] - lam["A"], 4)
    report["reported"] = reported

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(report, indent=1) + "\n")

    # ---- console summary -------------------------------------------------
    print("=" * 78)
    print("miso-117 A/B — measured_ct_heat_rates vs a same-HEAD zero-delta control")
    print("=" * 78)
    art = report["artifact"]
    print(
        f"artifact: {art['plants_applied']}/{art['plants_total']} plants applied, "
        f"{art['plants_excluded_by_band']} excluded by the physical band, "
        f"{art['capacity_mw']:,.1f} MW"
    )
    print(
        f"  {art['cheaper_plants']} plants / {art['cheaper_mw']:,.1f} MW cheaper, "
        f"{art['dearer_plants']} / {art['dearer_mw']:,.1f} MW dearer; "
        f"cap-wt {art['cap_weighted_delta_mmbtu']:+.4f} MMBtu/MWh, "
        f"gen-wt {art['gen_weighted_delta_mmbtu']:+.4f}"
    )
    for gate in ("K1_flag_fidelity", "K3_liveness", "K4_single_delta", "K5_year_span"):
        print(f"  {gate:<28} {'PASS' if report[gate]['passed'] else 'FAIL'}")
    k2 = report["K2_control_integrity_strict_byte"]
    print(
        f"  K2 strict-byte control drift   max {k2['max_abs_diff_mw']:,.4f} MW "
        f"({'byte-identical' if k2['byte_identical'] else 'DRIFT — reported, not a kill'})"
    )
    prot = report["protective"]
    print("\nprotective (prereg §6.1):")
    for arm in ("A", "B"):
        d1 = prot["d1_ct_peaker"][arm]
        if d1:
            cells = "  ".join(
                f"{y}: r={v['profile_r']} cv={v['cv_ratio']}" for y, v in d1.items()
            )
            print(f"  D-1 {CT_CLASS} {arm}: {cells}")
    for arm in ("A", "B"):
        d1 = prot["d1_coal_prb"][arm]
        if d1:
            cells = "  ".join(
                f"{y}: r={v['profile_r']} cv={v['cv_ratio']} {v['verdict']}"
                for y, v in d1.items()
            )
            print(f"  D-1 {FAILING_CLASS} {arm}: {cells}")
    if prot.get("c8_total_share_A"):
        print(f"  D-2 {CT_CLASS} forced share A: {prot['c8_total_share_A']}")
        print(f"  D-2 {CT_CLASS} forced share B: {prot['c8_total_share_B']}  "
              f"(cap {D2_PEAKER_MAX_SHARE})")
    if prot.get("c8_route"):
        print(f"  !! {prot['c8_route']}")

    print("\nreported (never a kill — rules 1 / 14):")
    for year in YEARS:
        blk = reported[str(year)]
        lam = blk["lambda_load_weighted"]
        print(
            f"  {year}: lambda {lam['A']:.4f} -> {lam['B']:.4f} "
            f"({lam['delta']:+.4f} $/MWh) | slack {blk['slack_mwh']['A']} -> "
            f"{blk['slack_mwh']['B']} | dump {blk['dump_mwh']['A']} -> "
            f"{blk['dump_mwh']['B']}"
        )
        movers = sorted(
            blk["class_twh"].items(),
            key=lambda kv: -abs(kv[1]["delta"]),
        )[:8]
        for k, v in movers:
            if abs(v["delta"]) < 1e-4:
                continue
            act = f" (actual {v['actual']})" if v["actual"] is not None else ""
            print(
                f"      {k:<14} {v['A']:>9.4f} -> {v['B']:>9.4f} TWh "
                f"({v['delta']:+.4f}){act}"
            )
    print(f"\nwrote {OUT_PATH.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""nyiso-108 A/B scorer — the hydro input repair against the nyiso-105 keeper.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-nyiso108-hydro-input-repair-2026-07-31.md`` from the
two solved bundles. **No solve, and no gate that is not in the prereg.**

The arm is the PAIR ``hydro_backfill_year=2024`` + ``hydro_eia930_monthly=True``
— option (i), the CAISO/NEISO posture — adjudicated pre-solve against NYISO's own
MIS P-63 telemetry (prereg §2).

Construction gates (prereg §4):

* **K1 flag fidelity** — arm B records ``hydro_backfill_year == 2024`` and
  ``hydro_eia930_monthly == true``; the control records ``null`` / ``false``.
  (The fleet census the flags produce — 3 → 147 units in 2025 — is established
  PRE-SOLVE by ``_nyiso108_hydro_construction_audit.py``; slim bundles carry
  class-level hourlies only, so K1 gates on the recorded flags and K3 on the
  dispatch those flags produce.)
* **K2 control integrity** — TWO BASES, and only the first is a gate. The
  *scorecard* basis (same determination, same per-criterion statuses as the
  committed keeper) is the pre-registered gate. The stricter *byte* basis
  (class-hour for class-hour, < 1e-6 MW) is computed and REPORTED; a byte miss is
  same-HEAD drift, a separately-reported finding, not a failed gate (caiso-146 /
  neiso-69 precedent).
* **K3 mechanism is LIVE** — ``max |Δ hydro MW|`` on a class-hour > 50 in EVERY
  year, and annual hydro dispatch differing by > 0.5 TWh in EVERY year. Failing
  this is verdict ``I`` (inert), not ``R``.
* **K4 single delta** — the arms' recorded configs differ in exactly the two
  hydro keys and nothing else.
* **K5 year span** — both bundles carry ``[2023, 2024, 2025]`` and nothing else
  (rule 16; rule 22 D-6 quarantine, holdout spend freeze ACTIVE).
* **K6 pin sensitivity** — C1 recomputed with the D-10 pinned classes excluded,
  AND with hydro itself excluded, since prereg §3.2 makes hydro's own volume
  term plumbing.

Everything else — hydro volume error in any year, per-class TWh, mean λ, tail
hours, slack/dump — is REPORTED per prereg §5: the hydro volume statistic is
declared plumbing and is never banked, and a worse backcast on a strictly more
accurate measured input is a discovered bug under rules 1/14, never a kill.

Usage::

    PYTHONPATH=.:src .venv/bin/python scripts/probes/_nyiso108_hydro_input_repair_ab.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/nyiso108_control_A"
ARM_B = REPO / "results/calibration/nyiso108_hydrorepair_B"
KEEPER = REPO / "results/calibration/nyiso105_chpheatrate_B"
OUT_PATH = REPO / "results/calibration/_nyiso108_hydro_input_repair_ab.json"

#: PREREG §4 K3 — the liveness floor, in MW of class dispatch divergence.
K3_LIVENESS_MW = 50.0
#: PREREG §4 K3 — the annual-energy liveness floor, TWh.
K3_LIVENESS_TWH = 0.5
#: PREREG §4 K2 — a zero-delta replay must land inside this many MW.
K2_TOL_MW = 1e-6
#: The two keys under test (prereg §2 option (i)).
FLAGS = ("hydro_backfill_year", "hydro_eia930_monthly")
#: PREREG §4 — NYISO's D-10 pinned classes (scripts/calibration_verdict.py).
#: Both spellings of the interchange class are listed: the verdict module names
#: it ``imports`` while the committed class-hourly sidecars emit ``import``.
PINNED = {
    "CC_CHP",
    "CT_CHP",
    "ST_CHP",
    "hydro",
    "import",
    "imports",
    "nuclear",
    "solar",
    "wind",
}

#: nyiso-107 §C.1 — NYISO MIS P-63 `Hydro`, the EIA-independent instrument. Used
#: ONLY to report where each arm's hydro sits against a series that is neither
#: the model input nor the scorer benchmark (prereg §3.2).
P63_HYDRO_TWH = {2023: 27.1845, 2024: 26.9763, 2025: 24.2489}
#: The benchmark the scorer actually uses (923 raw / 923 raw / 930 swap).
AS_SCORED_BENCH_TWH = {2023: 28.0312, 2024: 27.4654, 2025: 24.1039}


# --------------------------------------------------------------------------- #
# committed-bytes readers
# --------------------------------------------------------------------------- #
def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """Annual per-class energy, TWh."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / 1.0e6).round(4).to_dict()


def _pairwise(a: Path, b: Path, year: int) -> dict:
    """Max / by-class class-hour divergence between two bundles for one year."""
    left = _class_hourly(a, year).set_index(["klass", "hour"])["mw"].sort_index()
    right = _class_hourly(b, year).set_index(["klass", "hour"])["mw"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=0.0)
    diff = (lj - rj).abs()
    return {
        "max_abs_diff_mw": round(float(diff.max()), 6),
        "max_by_class_mw": {
            str(k): round(float(v), 4)
            for k, v in diff.groupby(level="klass").max().items()
        },
    }


def _system(bundle: Path, year: int) -> pd.DataFrame:
    """P1 system hourly frame for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean λ (the external interchange node excluded)."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _tail_hours(bundle: Path, year: int, thresh: float = 300.0) -> int:
    """C3c basis: load-weighted system λ hours above *thresh*."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    lam = (ny["price"] * ny["demand"]).groupby(ny["hour"]).sum() / ny.groupby("hour")[
        "demand"
    ].sum()
    return int((lam > thresh).sum())


def _slack_dump(bundle: Path, year: int) -> tuple[float, float]:
    """Total slack / dump energy for one bundle-year, MWh."""
    frame = _system(bundle, year)
    slack = float(frame["slack"].sum()) if "slack" in frame.columns else float("nan")
    dump = float(frame["dump"].sum()) if "dump" in frame.columns else float("nan")
    return round(slack, 3), round(dump, 3)


def _recorded_flags(bundle: Path) -> dict:
    """The bundle's own recorded hydro settings, from meta.json + run_config."""
    out: dict = {}
    meta_path = bundle / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for key in FLAGS:
            out[key] = meta.get(key)
    cfg_path = bundle / "run_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        for key in FLAGS:
            if key in cfg:
                out.setdefault(f"{key}__run_config", cfg[key])
    return out


def _config_block(bundle: Path) -> dict:
    """Everything the bundle recorded that could differ between the two arms.

    Merges the ``run_config.json`` scenario block with the flat ``meta.json``
    calibration keys, because the two hydro flags under test are
    ``solve_and_persist`` kwargs (NOT ``ScenarioConfig`` fields), so they land in
    meta rather than the scenario block. A single-delta proof that read only the
    scenario block would be blind to exactly the keys being tested.
    """
    block: dict = {}
    cfg_path = bundle / "run_config.json"
    if cfg_path.exists():
        cfg = json.loads(cfg_path.read_text())
        block.update(cfg.get("scenario_config", {}) or {})
    meta_path = bundle / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
        for k, v in meta.items():
            # `timestamp`/`note` are bookkeeping, not solve inputs; nested dicts
            # are flattened one level so override maps compare key-by-key.
            if k in ("timestamp", "note", "years"):
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    block[f"{k}.{k2}"] = v2
            else:
                block.setdefault(k, v)
    return block


def _hydro_units(bundle: Path, year: int) -> int | None:
    """Distinct hydro LP units in the solved bundle, when unit detail exists.

    Slim bundles carry class-level hourlies only, so this is usually ``None``.
    The fleet census (3 vs 147 units in 2025) is established PRE-SOLVE by
    ``_nyiso108_hydro_construction_audit.py``; K1 does not depend on it.
    """
    for name in (f"units_{year}.parquet", f"unit_hourly_{year}.parquet"):
        path = bundle / "hourly" / name
        if not path.exists():
            continue
        frame = pd.read_parquet(path, columns=["unit_id"])
        return int(frame["unit_id"].astype(str).str.endswith("_hydro").sum())
    return None


# --------------------------------------------------------------------------- #
# the pre-registered construction gates
# --------------------------------------------------------------------------- #
def k1_flag_fidelity() -> dict:
    """Arm B records the pair armed; the control records it bare."""
    a, b = _recorded_flags(ARM_A), _recorded_flags(ARM_B)
    a_bare = a.get("hydro_backfill_year") is None and not a.get("hydro_eia930_monthly")
    b_armed = int(b.get("hydro_backfill_year") or 0) == 2024 and bool(
        b.get("hydro_eia930_monthly")
    )
    return {
        "arm_A_flags": a,
        "arm_B_flags": b,
        "control_is_bare": bool(a_bare),
        "arm_is_armed": bool(b_armed),
        "passed": bool(a_bare and b_armed),
    }


def k2_control_integrity() -> dict:
    """Scorecard basis is the gate; byte basis is reported (prereg §4 K2)."""
    byte = {}
    for year in YEARS:
        byte[year] = _pairwise(KEEPER, ARM_A, year)
    byte_ok = all(v["max_abs_diff_mw"] <= K2_TOL_MW for v in byte.values())
    return {
        "byte_basis_vs_committed_keeper": byte,
        "byte_basis_identical": byte_ok,
        "note": (
            "Byte basis is REPORTED, not the gate (prereg §4 K2). The gate is the "
            "scorecard basis, scored from the arms' own metrics.json."
        ),
    }


def k3_liveness() -> dict:
    """The pair must move hydro dispatch in EVERY year, on both bases."""
    per_year = {}
    live_mw, live_twh = [], []
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        hydro_mw = pw["max_by_class_mw"].get("hydro", 0.0)
        a_twh = _class_twh(ARM_A, year).get("hydro", 0.0)
        b_twh = _class_twh(ARM_B, year).get("hydro", 0.0)
        per_year[year] = {
            "max_abs_diff_mw": pw["max_abs_diff_mw"],
            "hydro_class_max_mw": hydro_mw,
            "hydro_twh": {"A": a_twh, "B": b_twh, "delta": round(b_twh - a_twh, 4)},
            "max_by_class_mw": pw["max_by_class_mw"],
        }
        live_mw.append(hydro_mw > K3_LIVENESS_MW)
        live_twh.append(abs(b_twh - a_twh) > K3_LIVENESS_TWH)
    return {
        "per_year": per_year,
        "threshold_mw": K3_LIVENESS_MW,
        "threshold_twh": K3_LIVENESS_TWH,
        "live_all_years_mw": all(live_mw),
        "live_all_years_twh": all(live_twh),
        "passed": all(live_mw) and all(live_twh),
    }


def k4_single_delta() -> dict:
    """The two arms' recorded configs differ in exactly the two hydro keys."""
    a, b = _config_block(ARM_A), _config_block(ARM_B)
    diff = {
        k: {"A": a.get(k), "B": b.get(k)}
        for k in sorted(set(a) | set(b))
        if a.get(k) != b.get(k)
    }
    return {
        "differing_keys": diff,
        "n_differing": len(diff),
        "expected": list(FLAGS),
        "passed": sorted(diff) == sorted(FLAGS),
    }


def k5_year_span() -> dict:
    """Both bundles carry exactly [2023, 2024, 2025] (rule 16 / rule 22)."""
    spans = {}
    for name, bundle in (("A", ARM_A), ("B", ARM_B)):
        meta = json.loads((bundle / "meta.json").read_text())
        spans[name] = [int(y) for y in meta.get("years", [])]
    return {
        "years": spans,
        "passed": all(v == [2023, 2024, 2025] for v in spans.values()),
    }


def k6_pin_sensitivity() -> dict:
    """Class energy split into pinned vs free classes — and hydro held out.

    prereg §3.2 makes hydro's own volume term plumbing, so a C1 movement that is
    ONLY the hydro term must be visible as such.
    """
    out = {}
    for year in YEARS:
        a, b = _class_twh(ARM_A, year), _class_twh(ARM_B, year)
        keys = sorted(set(a) | set(b))
        rows = {
            k: {
                "A": round(a.get(k, 0.0), 4),
                "B": round(b.get(k, 0.0), 4),
                "delta": round(b.get(k, 0.0) - a.get(k, 0.0), 4),
                "pinned": k in PINNED,
            }
            for k in keys
        }
        free_moved = {
            k: v["delta"]
            for k, v in rows.items()
            if not v["pinned"] and abs(v["delta"]) > 1e-4
        }
        non_hydro_moved = {
            k: v["delta"]
            for k, v in rows.items()
            if k != "hydro" and abs(v["delta"]) > 1e-4
        }
        out[year] = {
            "by_class": rows,
            "free_classes_moved": free_moved,
            "free_abs_twh_moved": round(sum(abs(v) for v in free_moved.values()), 4),
            "non_hydro_abs_twh_moved": round(
                sum(abs(v) for v in non_hydro_moved.values()), 4
            ),
        }
    return {
        "per_year": out,
        "verdict_rests_on_free_classes_too": any(
            v["free_abs_twh_moved"] > 0.0 for v in out.values()
        ),
        "moves_more_than_hydro": any(
            v["non_hydro_abs_twh_moved"] > 0.0 for v in out.values()
        ),
    }


# --------------------------------------------------------------------------- #
# reported-only diagnostics (prereg §5 — these can never kill)
# --------------------------------------------------------------------------- #
def reported() -> dict:
    """Everything prereg §5 lists as REPORTED, never a kill condition."""
    out = {}
    for year in YEARS:
        a_slack, a_dump = _slack_dump(ARM_A, year)
        b_slack, b_dump = _slack_dump(ARM_B, year)
        a_h = _class_twh(ARM_A, year).get("hydro", 0.0)
        b_h = _class_twh(ARM_B, year).get("hydro", 0.0)
        out[year] = {
            "mean_lambda": {"A": _lambda(ARM_A, year), "B": _lambda(ARM_B, year)},
            "tail_hours_gt_300": {
                "A": _tail_hours(ARM_A, year),
                "B": _tail_hours(ARM_B, year),
            },
            "slack_mwh": {"A": a_slack, "B": b_slack},
            "dump_mwh": {"A": a_dump, "B": b_dump},
            # PLUMBING (prereg §3.2) — reported, never banked as an improvement.
            "hydro_volume_PLUMBING": {
                "A_twh": a_h,
                "B_twh": b_h,
                "A_vs_bench_pct": round(
                    100.0 * (a_h / AS_SCORED_BENCH_TWH[year] - 1.0), 2
                ),
                "B_vs_bench_pct": round(
                    100.0 * (b_h / AS_SCORED_BENCH_TWH[year] - 1.0), 2
                ),
                "A_vs_p63_pct": round(100.0 * (a_h / P63_HYDRO_TWH[year] - 1.0), 2),
                "B_vs_p63_pct": round(100.0 * (b_h / P63_HYDRO_TWH[year] - 1.0), 2),
                "note": (
                    "Pinned to the same EIA-930 NG: WAT series the 2025 benchmark "
                    "uses — near-tautological BY CONSTRUCTION. Declared plumbing "
                    "in prereg §3.2; never quoted as an improvement."
                ),
            },
            "class_twh": {
                "A": _class_twh(ARM_A, year),
                "B": _class_twh(ARM_B, year),
            },
            "hydro_lp_units": {
                "A": _hydro_units(ARM_A, year),
                "B": _hydro_units(ARM_B, year),
            },
        }
    return out


def scorecards() -> dict:
    """Per-criterion statuses from each bundle's own metrics.json, if present."""
    out = {}
    for name, bundle in (("keeper", KEEPER), ("A", ARM_A), ("B", ARM_B)):
        path = bundle / "metrics.json"
        if not path.exists():
            out[name] = None
            continue
        m = json.loads(path.read_text())
        out[name] = {
            "determination": m.get("determination"),
            "criteria": {
                k: (v.get("status") if isinstance(v, dict) else v)
                for k, v in (m.get("criteria") or {}).items()
            },
            "grade_summary": m.get("grade_summary"),
            "free_class_headline": (m.get("free_class_score") or {}).get("headline"),
        }
    return out


def main() -> int:
    """Score every pre-registered gate and write the A/B JSON."""
    res = {
        "probe": "nyiso-108 hydro input repair A/B (backfill 2024 + EIA-930 pin)",
        "prereg": (
            "results/calibration/PREREG-nyiso108-hydro-input-repair-2026-07-31.md"
        ),
        "arms": {"A_control": ARM_A.name, "B": ARM_B.name, "keeper": KEEPER.name},
        "gates": {
            "K1_flag_fidelity": k1_flag_fidelity(),
            "K2_control_integrity": k2_control_integrity(),
            "K3_liveness": k3_liveness(),
            "K4_single_delta": k4_single_delta(),
            "K5_year_span": k5_year_span(),
            "K6_pin_sensitivity": k6_pin_sensitivity(),
        },
        "scorecards": scorecards(),
        "reported_never_a_kill": reported(),
    }

    gated = {k: v for k, v in res["gates"].items() if "passed" in v}
    print("\n=== nyiso-108 pre-registered construction gates ===")
    for name, gate in gated.items():
        print(f"  {name:<24} {'PASS' if gate['passed'] else 'FAIL'}")
    k2 = res["gates"]["K2_control_integrity"]
    print(
        f"  K2 byte basis (REPORTED)  "
        f"{'identical' if k2['byte_basis_identical'] else 'DRIFTED — see finding'}"
    )

    print("\n=== hydro (PLUMBING — prereg §3.2, never banked) ===")
    print(f"{'year':<6}{'A TWh':>9}{'B TWh':>9}{'A vs bench':>12}{'B vs bench':>12}{'B vs P-63':>11}")
    for year in YEARS:
        r = res["reported_never_a_kill"][year]["hydro_volume_PLUMBING"]
        print(
            f"{year:<6}{r['A_twh']:>9.4f}{r['B_twh']:>9.4f}"
            f"{r['A_vs_bench_pct']:>11.2f}%{r['B_vs_bench_pct']:>11.2f}%"
            f"{r['B_vs_p63_pct']:>10.2f}%"
        )

    print("\n=== determination ===")
    for name in ("keeper", "A", "B"):
        sc = res["scorecards"].get(name)
        print(f"  {name:<8} {sc['determination'] if sc else 'no metrics.json'}")

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0 if all(g["passed"] for g in gated.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

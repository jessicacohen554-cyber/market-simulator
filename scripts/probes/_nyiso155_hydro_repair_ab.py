"""nyiso-155 A/B scorer — the hydro truncation repair RE-ARM against the nyiso-152 keeper.

Scores the PRE-REGISTERED gates of
``results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md``
from the two solved bundles. **No solve here, and no gate that is not in the
prereg.** Template: ``_nyiso108_hydro_input_repair_ab.py`` (the first arm of
the same pair, 2026-07-31), extended with the prereg's G5 SHAPE leg — the only
place the prereg allows a real hydro result to live, because the 930 level pin
makes the hydro VOLUME statistic near-tautological BY CONSTRUCTION (prereg §4).

Gates (prereg §3):

* **G1 IDENT** (STOP) — control vs the committed keeper bundle
  ``nyiso152_armSE``: per-year class-hour dispatch and system price compare at
  exactly 0.0. Failure branch is pre-committed: measurement completes, both
  runs register, NO promotion is self-adjudicated (nyiso-128 K6 class).
* **G2 SINGLE-DELTA** (STOP) — the arms' recorded configs (meta flattened over
  the scenario block, because the two hydro keys are ``solve_and_persist``
  kwargs, not ``ScenarioConfig`` fields) differ in exactly the two hydro keys.
* **G3 INPUT EFFECT** (report) — hydro annual dispatch per arm vs the
  nyiso-107 §E expectations.
* **G4 HYDRO VOLUME** (report) — labelled TAUTOLOGICAL BY CONSTRUCTION at
  every mention; never banked, in either direction.
* **G5 SHAPE** (report) — hydro hourly r, hour-of-day profile r and swing vs
  gap-masked EIA-930 ``NG: WAT``; monthly seasonal shape r vs NYISO MIS P-63
  ``Hydro`` (the EIA-independent instrument). Direction-blind, full magnitude.
* **G6/G7** — determination + per-criterion statuses from each bundle's own
  ``metrics.json`` (the authoritative read is ``calibration_verdict.py``).
* **G8 LEGITIMACY** (STOP) — no NEW failing D-row on the arm vs the control,
  from each bundle's ``legitimacy_diagnostics.json``.

Usage::

    python scripts/probes/_nyiso155_hydro_repair_ab.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    sys.path.insert(0, str(_p))

YEARS = (2023, 2024, 2025)

ARM_A = REPO / "results/calibration/nyiso155_hydro_control"
ARM_B = REPO / "results/calibration/nyiso155_hydro_repair"
KEEPER = REPO / "results/calibration/nyiso152_armSE"
FUELMIX = REPO / "data/raw/NYISO/fuel-mix"
OUT_PATH = REPO / "results/calibration/_nyiso155_hydro_repair_ab.json"
_TWH = 1e6

#: The two keys under test (prereg §2) — solve_and_persist kwargs.
FLAGS = ("hydro_backfill_year", "hydro_eia930_monthly")
#: PREREG §3 G1 — the IDENT bar (exactly 0.0; float read-back tolerance only).
G1_TOL = 0.0
#: nyiso-107 §C.1 — NYISO MIS P-63 `Hydro` annual TWh (level reference only).
P63_HYDRO_TWH = {2023: 27.1845, 2024: 26.9763, 2025: 24.2489}
#: The scorer's as-scored benchmark (923 raw / 923 raw / 930 swap).
AS_SCORED_BENCH_TWH = {2023: 28.0312, 2024: 27.4654, 2025: 24.1039}
#: nyiso-107 §E — expected budget motion of the pair (report reference).
EXPECTED_DELTA_TWH = {2023: -1.5668, 2024: -1.1287, 2025: +3.0143}


# --------------------------------------------------------------------------- #
# committed-bytes readers (nyiso-108 template)
# --------------------------------------------------------------------------- #
def _class_hourly(bundle: Path, year: int) -> pd.DataFrame:
    """P1 class-hour dispatch for one bundle-year."""
    frame = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return frame[frame["pass"] == "P1"] if "pass" in frame.columns else frame


def _class_twh(bundle: Path, year: int) -> dict[str, float]:
    """Annual per-class energy, TWh."""
    frame = _class_hourly(bundle, year)
    return (frame.groupby("klass")["mw"].sum() / _TWH).round(4).to_dict()


def _hydro_hourly(bundle: Path, year: int) -> np.ndarray:
    """The bundle's hourly hydro dispatch vector (MW, hour-indexed)."""
    frame = _class_hourly(bundle, year)
    h = (
        frame[frame["klass"] == "hydro"]
        .set_index("hour")["mw"]
        .sort_index()
        .reindex(range(8760), fill_value=0.0)
    )
    return h.to_numpy(dtype=float)


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


def _system_price_diff(a: Path, b: Path, year: int) -> float:
    """Max abs zonal price divergence between two bundles for one year."""
    left = _system(a, year).set_index(["zone", "hour"])["price"].sort_index()
    right = _system(b, year).set_index(["zone", "hour"])["price"].sort_index()
    lj, rj = left.align(right, join="outer", fill_value=np.nan)
    return round(float((lj - rj).abs().max()), 6)


def _lambda(bundle: Path, year: int) -> float:
    """NYISO demand-weighted mean λ (the external interchange node excluded)."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    return round(float((ny["price"] * ny["demand"]).sum() / ny["demand"].sum()), 4)


def _tail_hours(bundle: Path, year: int, thresh: float = 300.0) -> int:
    """Load-weighted system λ hours above *thresh* (report only; the
    authoritative C3c basis is calibration_verdict.py — nyiso-108 recorded
    that this reduction does not reproduce the scorer's committed counts)."""
    frame = _system(bundle, year)
    ny = frame[~frame["zone"].astype(str).str.startswith("NYISO_external")]
    lam = (ny["price"] * ny["demand"]).groupby(ny["hour"]).sum() / ny.groupby(
        "hour"
    )["demand"].sum()
    return int((lam > thresh).sum())


def _config_block(bundle: Path) -> dict:
    """Everything the bundle recorded that could differ between the two arms.

    Merges the ``run_config.json`` scenario block with the flat ``meta.json``
    calibration keys, because the two hydro flags under test are
    ``solve_and_persist`` kwargs (NOT ``ScenarioConfig`` fields) — the exact
    structural blindness that let the pair fall out of the keeper lineage
    silently (prereg §0). A single-delta proof reading only the scenario block
    would be blind to the keys being tested.
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
            if k in ("timestamp", "note", "years", "shared_inputs", "git_sha", "basis_sha"):
                continue
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    block[f"{k}.{k2}"] = v2
            else:
                block.setdefault(k, v)
    return block


def _measured_hydro(year: int) -> np.ndarray | None:
    """Gap-masked EIA-930 ``NG: WAT`` hourly vector — the scorer's own series."""
    from market_sim.data.eia930.actuals import load_eia_hourly_benchmark

    bench = load_eia_hourly_benchmark("NYISO", year)
    if not bench or "hydro" not in bench:
        return None
    arr = np.asarray(bench["hydro"], dtype=float)
    return arr[:8760] if arr.size >= 8760 else None


def _p63_monthly(year: int) -> np.ndarray:
    """NYISO MIS P-63 ``Hydro`` monthly TWh vector (12 entries)."""
    fm = pd.read_csv(FUELMIX / f"NYISO_fuelmix_hourly_{year}.csv.gz")
    hyd = fm[fm["fuel_category"] == "Hydro"].copy()
    ts = pd.to_datetime(hyd["interval_start_local"])
    hyd["month"] = ts.dt.month
    out = hyd.groupby("month")["gen_mw"].sum().reindex(range(1, 13), fill_value=0.0)
    return out.to_numpy(dtype=float) / _TWH


def _r(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson r over the common finite mask."""
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 3 or a[mask].std() == 0 or b[mask].std() == 0:
        return float("nan")
    return round(float(np.corrcoef(a[mask], b[mask])[0, 1]), 4)


def _hod_profile(arr: np.ndarray) -> np.ndarray:
    """Hour-of-day mean profile (24 entries) over finite hours."""
    v = arr[: 8760 // 24 * 24].reshape(-1, 24)
    return np.nanmean(v, axis=0)


# --------------------------------------------------------------------------- #
# the pre-registered gates
# --------------------------------------------------------------------------- #
def g1_ident() -> dict:
    """Control vs the committed keeper: dispatch AND price at exactly 0.0."""
    per_year = {}
    ok = True
    for year in YEARS:
        pw = _pairwise(KEEPER, ARM_A, year)
        dp = _system_price_diff(KEEPER, ARM_A, year)
        per_year[year] = {
            "max_abs_dispatch_mw": pw["max_abs_diff_mw"],
            "max_abs_price": dp,
        }
        ok = ok and pw["max_abs_diff_mw"] <= G1_TOL and dp <= G1_TOL
    return {"per_year": per_year, "bar": G1_TOL, "passed": bool(ok)}


def g2_single_delta() -> dict:
    """The arms' recorded configs differ in exactly the two hydro keys."""
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


def g3_input_effect() -> dict:
    """Hydro dispatch per arm vs the nyiso-107 §E expectations (report)."""
    out = {}
    for year in YEARS:
        a = _class_twh(ARM_A, year).get("hydro", 0.0)
        b = _class_twh(ARM_B, year).get("hydro", 0.0)
        out[year] = {
            "A_twh": a,
            "B_twh": b,
            "delta_twh": round(b - a, 4),
            "expected_budget_delta_twh": EXPECTED_DELTA_TWH[year],
        }
    return {"per_year": out, "note": "report-class; deviations explained, never tuned"}


def g4_volume() -> dict:
    """Hydro volume — TAUTOLOGICAL BY CONSTRUCTION under the 930 pin.

    The budget and the benchmark become the same series, so the arm's number
    is plumbing (prereg §4). Reported at full magnitude, banked NEVER.
    """
    out = {}
    for year in YEARS:
        a = _class_twh(ARM_A, year).get("hydro", 0.0)
        b = _class_twh(ARM_B, year).get("hydro", 0.0)
        out[year] = {
            "A_twh": a,
            "B_twh": b,
            "A_vs_bench_pct": round(100.0 * (a / AS_SCORED_BENCH_TWH[year] - 1.0), 2),
            "B_vs_bench_pct_TAUTOLOGICAL": round(
                100.0 * (b / AS_SCORED_BENCH_TWH[year] - 1.0), 2
            ),
            "A_vs_p63_pct": round(100.0 * (a / P63_HYDRO_TWH[year] - 1.0), 2),
            "B_vs_p63_pct": round(100.0 * (b / P63_HYDRO_TWH[year] - 1.0), 2),
        }
    return {
        "per_year": out,
        "note": (
            "TAUTOLOGICAL BY CONSTRUCTION under the 930 level pin — budget and "
            "benchmark are the same series. Declared plumbing (prereg §4); no "
            "skill claim is made from it and no promotion argument may lean on "
            "it, in any direction."
        ),
    }


def g5_shape() -> dict:
    """Hydro dispatch SHAPE — the only place a real result can live (prereg §4)."""
    out = {}
    for year in YEARS:
        measured = _measured_hydro(year)
        a, b = _hydro_hourly(ARM_A, year), _hydro_hourly(ARM_B, year)
        row: dict = {}
        if measured is not None:
            row["hourly_r"] = {"A": _r(a, measured), "B": _r(b, measured)}
            day = 8760 // 24 * 24
            row["daily_r"] = {
                "A": _r(
                    a[:day].reshape(-1, 24).mean(axis=1),
                    np.nanmean(measured[:day].reshape(-1, 24), axis=1),
                ),
                "B": _r(
                    b[:day].reshape(-1, 24).mean(axis=1),
                    np.nanmean(measured[:day].reshape(-1, 24), axis=1),
                ),
            }
            hp_m = _hod_profile(measured)
            hp_a, hp_b = _hod_profile(a), _hod_profile(b)
            row["hod_profile_r"] = {"A": _r(hp_a, hp_m), "B": _r(hp_b, hp_m)}
            row["hod_swing_mw"] = {
                "measured": round(float(np.nanmax(hp_m) - np.nanmin(hp_m)), 1),
                "A": round(float(hp_a.max() - hp_a.min()), 1),
                "B": round(float(hp_b.max() - hp_b.min()), 1),
            }
        # Monthly seasonal shape against P-63 (EIA-independent instrument).
        p63 = _p63_monthly(year)
        am = a[: 8760].copy()
        bm = b[: 8760].copy()
        idx = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        a_m = pd.Series(am, index=idx).groupby(idx.month).sum().to_numpy() / _TWH
        b_m = pd.Series(bm, index=idx).groupby(idx.month).sum().to_numpy() / _TWH
        row["monthly_shape_r_vs_p63"] = {"A": _r(a_m, p63), "B": _r(b_m, p63)}
        row["annual_peak_month"] = {
            "p63": int(np.argmax(p63) + 1),
            "A": int(np.argmax(a_m) + 1),
            "B": int(np.argmax(b_m) + 1),
        }
        out[year] = row
    return {"per_year": out, "note": "direction-blind, full magnitude (prereg G5)"}


def g6_g7_scorecards() -> dict:
    """Determination + per-criterion statuses from each bundle's metrics.json."""
    out = {}
    for name, bundle in (("keeper", KEEPER), ("A_control", ARM_A), ("B_repair", ARM_B)):
        path = bundle / "metrics.json"
        if not path.exists():
            out[name] = None
            continue
        m = json.loads(path.read_text())
        out[name] = {
            "determination": m.get("determination"),
            "reasons": m.get("reasons"),
            "criteria": {
                k: (v.get("status") if isinstance(v, dict) else v)
                for k, v in (m.get("criteria") or {}).items()
            },
            "caveats": m.get("caveats"),
            "free_class_headline": (m.get("free_class_score") or {}).get("headline"),
        }
    return out


def _failing_d_rows(bundle: Path) -> set[str]:
    """Identifiers of failing rows in a bundle's legitimacy_diagnostics.json."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return set()
    doc = json.loads(path.read_text())
    failing: set[str] = set()

    def _walk(obj, trail=""):
        if isinstance(obj, dict):
            status = obj.get("status") or obj.get("verdict") or obj.get("result")
            if isinstance(status, str) and status.upper() == "FAIL":
                failing.add(trail or "root")
            for k, v in obj.items():
                _walk(v, f"{trail}/{k}" if trail else str(k))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                _walk(v, f"{trail}[{i}]")

    _walk(doc)
    return failing


def g8_legitimacy() -> dict:
    """No NEW failing D-row on the arm vs the control (STOP)."""
    a, b = _failing_d_rows(ARM_A), _failing_d_rows(ARM_B)
    new = sorted(b - a)
    return {
        "control_failing": sorted(a),
        "arm_failing": sorted(b),
        "new_failing_on_arm": new,
        "passed": not new,
    }


def reported() -> dict:
    """Side-effect statistics at full magnitude (rule 14 — never patched)."""
    out = {}
    for year in YEARS:
        pw = _pairwise(ARM_A, ARM_B, year)
        out[year] = {
            "mean_lambda": {"A": _lambda(ARM_A, year), "B": _lambda(ARM_B, year)},
            "tail_hours_gt_300_probe_basis": {
                "A": _tail_hours(ARM_A, year),
                "B": _tail_hours(ARM_B, year),
            },
            "class_twh": {"A": _class_twh(ARM_A, year), "B": _class_twh(ARM_B, year)},
            "max_by_class_delta_mw": pw["max_by_class_mw"],
        }
    return out


def main() -> int:
    """Score every pre-registered gate and write the A/B JSON."""
    res = {
        "probe": "nyiso-155 hydro truncation repair RE-ARM A/B",
        "prereg": (
            "results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md"
        ),
        "arms": {"A_control": ARM_A.name, "B_repair": ARM_B.name, "keeper": KEEPER.name},
        "gates": {
            "G1_ident": g1_ident(),
            "G2_single_delta": g2_single_delta(),
            "G8_legitimacy": g8_legitimacy(),
        },
        "report": {
            "G3_input_effect": g3_input_effect(),
            "G4_volume_TAUTOLOGICAL_BY_CONSTRUCTION": g4_volume(),
            "G5_shape": g5_shape(),
            "G6_G7_scorecards": g6_g7_scorecards(),
            "side_effects_full_magnitude": reported(),
        },
    }

    print("\n=== nyiso-155 pre-registered STOP gates ===")
    for name, gate in res["gates"].items():
        print(f"  {name:<18} {'PASS' if gate['passed'] else 'FAIL'}")

    print("\n=== hydro volume (TAUTOLOGICAL BY CONSTRUCTION — never banked) ===")
    g4 = res["report"]["G4_volume_TAUTOLOGICAL_BY_CONSTRUCTION"]["per_year"]
    for year in YEARS:
        r = g4[year]
        print(
            f"  {year}: A {r['A_twh']:.4f} TWh ({r['A_vs_bench_pct']:+.2f}%)  "
            f"B {r['B_twh']:.4f} TWh ({r['B_vs_bench_pct_TAUTOLOGICAL']:+.2f}% "
            f"tautological)"
        )

    print("\n=== hydro SHAPE (the load-bearing leg) ===")
    for year in YEARS:
        row = res["report"]["G5_shape"]["per_year"][year]
        hr = row.get("hourly_r", {})
        mr = row["monthly_shape_r_vs_p63"]
        print(
            f"  {year}: hourly_r A {hr.get('A')} -> B {hr.get('B')}; "
            f"monthly_r(P63) A {mr['A']} -> B {mr['B']}"
        )

    print("\n=== determination ===")
    for name, sc in res["report"]["G6_G7_scorecards"].items():
        print(f"  {name:<10} {sc['determination'] if sc else 'no metrics.json'}")

    OUT_PATH.write_text(json.dumps(res, indent=1, default=str))
    print(f"\nwrote {OUT_PATH}")
    return 0 if all(g["passed"] for g in res["gates"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())

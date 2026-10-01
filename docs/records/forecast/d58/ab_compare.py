"""capx D58 A/B differencing — arm vs same-HEAD control, read off two bundles.

Grades the PREDECL §3 predictions and the §4 screen gates S1-S5 from the two
bundles' committed ledgers and (where present) their ``score.json``. Zero LP.

    uv run python docs/handoffs/d58/ab_compare.py <control-dir> <arm-dir> [out.json]
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
V2020 = ROOT / "data/raw/eia-860/vintage_2020"
ACTUALS = ROOT / "data/raw/_validation-source/capacity_actuals_pjm.csv"

_PLANT_RE = re.compile(r"_p(\d+)_")
_LEGACY_RE = re.compile(r"^(\d+)_")

# Rows that must be identical between the arms if the gate is a pure
# candidate-set partition (PREDECL §3 P4 / screen gate S5).
#
# REPAIRED 2026-09-06, capx D58: this tuple originally omitted
# ``capacity_clearing``, so S5 read PASS on the D58 screen while the gate was
# in fact moving 34.2 GW out of the capacity auction's sell-offer stack and
# depressing PJM's clearing price 9.67 % — the second seam the gate was
# supposed to be tested for. The omission is recorded as a miss against the
# pre-declaration's own instrumentation (FINDING §5); the key is added here so
# the check tests what S5 claims to test. `capacity_clearing` is the FIRST key
# any future sector-gate leg on a clearing-armed ISO should read.
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
    "capacity_clearing",
)


def plant_code(unit_id: str) -> int | None:
    m = _PLANT_RE.search(unit_id)
    if m:
        return int(m.group(1))
    m = _LEGACY_RE.match(unit_id)
    return int(m.group(1)) if m else None


def sectors() -> dict[int, int]:
    df = pd.read_parquet(V2020 / "eia860_plant.parquet", columns=["Plant Code", "Sector"])
    df = df.dropna(subset=["Plant Code", "Sector"])
    return {int(c): int(s) for c, s in zip(df["Plant Code"], df["Sector"])}


def real_exit_plants() -> dict[int, float]:
    df = pd.read_csv(ACTUALS, comment="#")
    df = df[(df["kind"] == "retirement") & (df["year"].between(2021, 2025))]
    out: dict[int, float] = defaultdict(float)
    for _, r in df.iterrows():
        out[int(r["plant_id"])] += float(r["mw"])
    return dict(out)


def cache_dir(bundle: Path) -> Path:
    iso = next(d for d in (bundle / "PJM",) if d.exists())
    return next(p for p in iso.iterdir() if p.is_dir())


def screen_rows(led: dict) -> tuple[list, list]:
    ev = led.get("pipeline_events") or []
    fail = [e for e in ev if e.get("event") in ("decided", "entry_capped")]
    return ev, fail


def year_block(bundle: Path, year: int) -> dict | None:
    p = cache_dir(bundle) / f"evolution_{year}.json"
    return json.loads(p.read_text()) if p.exists() else None


def summarize(bundle: Path, sec: dict[int, int], real: dict[int, float]) -> dict:
    out: dict[str, dict] = {}
    for year in (2021, 2022, 2023, 2024, 2025):
        led = year_block(bundle, year)
        if led is None:
            continue
        ev, fail = screen_rows(led)
        by_sector: dict[str, float] = defaultdict(float)
        adm_by_sector: dict[str, float] = defaultdict(float)
        adm_by_plant: dict[int | None, float] = defaultdict(float)
        for e in fail:
            code = plant_code(e["unit_id"])
            key = str(sec[code]) if code in sec else "unknown"
            mw = float(e.get("mw") or 0.0)
            by_sector[key] += mw
            if e.get("event") == "decided":
                adm_by_sector[key] += mw
                adm_by_plant[code] += mw
        adm = sum(adm_by_plant.values())
        hit = sum(v for k, v in adm_by_plant.items() if k in real)
        out[str(year)] = {
            "failing_rows": len(fail),
            "failing_mw": round(sum(by_sector.values()), 3),
            "failing_mw_by_sector": {k: round(v, 3) for k, v in sorted(by_sector.items())},
            "sector1_failing_mw": round(by_sector.get("1", 0.0), 3),
            "sector1_rows": sum(
                1
                for e in fail
                if (c := plant_code(e["unit_id"])) is not None and sec.get(c) == 1
            ),
            "unknown_sector_rows": sum(
                1 for e in fail if plant_code(e["unit_id"]) not in sec
            ),
            "admitted_mw": round(adm, 3),
            "admitted_mw_by_sector": {
                k: round(v, 3) for k, v in sorted(adm_by_sector.items())
            },
            "admitted_plant_grain_precision": round(hit / adm, 5) if adm else None,
            "capped_mw": round(
                sum(float(e.get("mw") or 0.0) for e in ev if e.get("event") == "entry_capped"),
                3,
            ),
            "event_counts": {
                k: sum(1 for e in ev if e.get("event") == k)
                for k in ("decided", "entry_capped", "executed", "re_confirmed", "reversed")
            },
            "sector_gated": led.get("sector_gated"),
            "capacity_clearing": {
                k: v
                for k, v in (led.get("capacity_clearing") or {}).items()
                if not isinstance(v, (list, dict))
            },
            "retirements_rows": len(led.get("retirements") or []),
            "retirements_mw": round(
                sum(float(r.get("mw") or 0.0) for r in (led.get("retirements") or [])), 3
            ),
            "retirements_economic_mw": round(
                sum(
                    float(r.get("mw") or 0.0)
                    for r in (led.get("retirements") or [])
                    if r.get("reason") != "announced"
                ),
                3,
            ),
            "retirements": led.get("retirements"),
            "capacity_reserve_position": led.get("capacity_reserve_position"),
            "adequacy_requirement_mw": led.get("adequacy_requirement_mw"),
            "footprint": {k: led.get(k) for k in FOOTPRINT_KEYS},
        }
    return out


def score_rows(bundle: Path) -> dict:
    p = cache_dir(bundle) / "score.json"
    if not p.exists():
        return {}
    s = json.loads(p.read_text())
    r = s.get("retirements", {})
    prp = r.get("plant_release_precision", {})
    return {
        "retire_total_gw": r.get("total_gw", {}).get("model"),
        "retire_total_err": r.get("total_gw", {}).get("err_frac"),
        "retire_total_band": r.get("total_gw", {}).get("band"),
        "per_fuel": {
            k: v.get("model_gw") for k, v in (r.get("per_fuel") or {}).items()
        },
        "unit_recall": r.get("unit_recall_gt300", {}).get("matched"),
        "unit_recall_frac": r.get("unit_recall_gt300", {}).get("recall"),
        "plant_matched": r.get("unit_recall_gt300", {}).get("plant_matched"),
        "false_retire_gw": r.get("false_retire", {}).get("false_gw"),
        "false_retire_frac": r.get("false_retire", {}).get("frac_of_model"),
        "precision_window_economic": prp.get("window", {}).get("economic", {}).get("precision"),
        "precision_window_all": prp.get("window", {}).get("all", {}).get("precision"),
        "precision_per_year_economic": {
            y: d.get("economic", {}).get("precision")
            for y, d in (prp.get("per_year") or {}).items()
        },
        "loyo": {
            y: d.get("recall") for y, d in ((s.get("loyo") or {}).get("folds") or {}).items()
        },
        "loyo_holds_2of3": (s.get("loyo") or {}).get("holds_2of3", {}).get("recall_pass"),
        "additions": (s.get("additions") or s.get("add") or {}),
    }


def gates(ctl: dict, arm: dict) -> dict:
    """The PREDECL §4 screen gates S1-S5, evaluated."""
    res = {}
    s1_rows = sum(v["sector1_rows"] for v in arm.values())
    s1_unk = sum(v["unknown_sector_rows"] for v in arm.values())
    res["S1_zero_sector1_and_unknown_rows"] = {
        "sector1_rows": s1_rows,
        "unknown_rows": s1_unk,
        "pass": s1_rows == 0 and s1_unk == 0,
    }
    for year, lo, hi in ((2022, 0.05, 0.30), (2023, 0.05, 0.30)):
        y = str(year)
        if y not in ctl or y not in arm:
            continue
        c, a = ctl[y]["failing_mw"], arm[y]["failing_mw"]
        fall = (c - a) / c if c else None
        res[f"S{2 if year == 2022 else 3}_{year}_failing_fall"] = {
            "control_mw": c,
            "arm_mw": a,
            "fall_frac": round(fall, 5) if fall is not None else None,
            "pass": fall is not None and lo <= fall <= hi,
        }
    if "2023" in ctl and "2023" in arm:
        d = ctl["2023"]["admitted_mw"] - arm["2023"]["admitted_mw"]
        res["S3b_2023_admitted_drop_400_850"] = {
            "drop_mw": round(d, 3),
            "arm_capped_mw": arm["2023"]["capped_mw"],
            "pass": 400 <= d <= 850 and arm["2023"]["capped_mw"] == 0,
        }
    if "2022" in arm:
        res["S4_2022_admitted_ge_10500"] = {
            "arm_admitted_mw": arm["2022"]["admitted_mw"],
            "control_admitted_mw": ctl.get("2022", {}).get("admitted_mw"),
            "pass": arm["2022"]["admitted_mw"] >= 10500,
        }
    diffs = {}
    for y in sorted(set(ctl) & set(arm)):
        for k in FOOTPRINT_KEYS:
            if ctl[y]["footprint"].get(k) != arm[y]["footprint"].get(k):
                diffs.setdefault(y, []).append(k)
    res["S5_footprint_identical"] = {"differing": diffs, "pass": not diffs}
    res["ALL_PASS"] = all(v.get("pass") for v in res.values() if isinstance(v, dict))
    return res


def main() -> None:
    ctl_dir, arm_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path(__file__).with_name(
        "ab_compare.json"
    )
    sec, real = sectors(), real_exit_plants()
    ctl, arm = summarize(ctl_dir, sec, real), summarize(arm_dir, sec, real)
    payload = {
        "control_dir": str(ctl_dir),
        "arm_dir": str(arm_dir),
        "control": ctl,
        "arm": arm,
        "control_score": score_rows(ctl_dir),
        "arm_score": score_rows(arm_dir),
        "screen_gates": gates(ctl, arm),
    }
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    print(json.dumps(payload["screen_gates"], indent=2, default=str))
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()

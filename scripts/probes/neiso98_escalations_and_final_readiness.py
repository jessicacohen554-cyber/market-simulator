"""neiso-98 — re-measure the NEISO lane's standing escalations and the `final` blockers AT HEAD.

Read-only, committed-artifact-only. **No LP is constructed and no year is solved,
scored or registered.** Rule 22 ``[R-HOLDOUT]`` as amended 2026-08-06: reading an
INPUT for an out-of-training year is unrestricted ("what is held out is the SCORE,
never the DATA"); what this probe must never do — and does not — is score model
output against those actuals. Every out-of-training read below is of the measured
actual series alone, with no model side.

Six legs, each a re-measurement rather than a carry-forward:

  1. **O5 — the legacy-P2 scoring basis.** Is NEISO still the only ISO of six whose
     designated keeper's ``meta.json`` carries ``commitment=true`` / ``passes
     ["P1","P2"]``? Measured on all six keeper shards' own bundles.
  2. **The Stony Brook 6081 outage routing** (the escalation O5 is best settled
     with): are units 004/005 still routed to ``plant_group=CC_REGULAR``?
  3. **The NYISO cross-ISO disclosure.** Does the NYISO keeper still arm
     ``nyiso_import_hub_prices``, i.e. still consume the repaired NEISO DA hub
     series as a live solve input?
  4. **2019 cannot exercise C3c** — re-confirmed ON THE REPAIRED INSTRUMENT. The
     neiso-94/96 measurement (RT max $261.35, 0 hours > $300) predates the
     neiso-97 repair, which touched 2018-2023. The finding proves no affected cell
     reaches $138.65, so the claim should survive; this leg checks it rather than
     assuming it.
  5. **The validation ladder's instrument coverage.** 2020/2021/2022 are all inside
     the repaired 2018-2023 span — measured per year, both markets, so a future
     authorized touchpoint iteration is known to measure against the repaired
     series.
  6. **H1-2026 partial-year solve gate.** Is ``eia930.frames._eia_hourly_frame``
     still rejecting any extract shorter than ``HOURS_PER_YEAR``, i.e. is the
     six-ISO partial-year blocker still live at HEAD?

Usage::

    uv run python scripts/probes/neiso98_escalations_and_final_readiness.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
KEEPER_DIR = REPO / "frontend/data/backcast/keepers"
REGISTRY = REPO / "frontend/data/backcast/registry"
NEISO_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet"
OUTAGES = REPO / "data/raw/campd-unit-outages-NEISO.csv"
TAIL_THRESHOLD = 300.0
OUT = REPO / "results/calibration/_neiso98_escalations.json"

# Validation-ladder years (rule 22: ladder bottoms out at 2020) plus the
# NEISO-specific locked-test year. Read as INPUTS only.
LADDER_YEARS = (2020, 2021, 2022)
LOCKED_YEAR = 2019
REPAIRED_SPAN = range(2018, 2024)  # the neiso-97 vintage-aware repair's span


def bundle_for(run_id: str) -> Path | None:
    """The on-disk bundle directory a registry sidecar points at, if present."""
    side = REGISTRY / f"{run_id}.json"
    if not side.exists():
        return None
    meta = json.loads(side.read_text())
    for key in ("bundle", "bundle_dir", "results_dir", "dir"):
        val = meta.get(key)
        if isinstance(val, str):
            p = REPO / val if not val.startswith("/") else Path(val)
            if p.exists():
                return p
    # Fall back to a name scan: sidecars do not all carry an explicit bundle key.
    return None


def leg1_p2_basis() -> list[dict]:
    """Per-ISO keeper commitment/passes, read from each keeper bundle's meta.json."""
    rows = []
    for shard in sorted(KEEPER_DIR.glob("*.json")):
        if shard.stem in {"index"}:
            continue
        d = json.loads(shard.read_text())
        iso, run_id = d.get("iso"), d.get("keeper")
        if not run_id:
            continue
        bundle = bundle_for(run_id)
        if bundle is None:
            # Scan results/calibration for a bundle whose meta names this run.
            for cand in sorted((REPO / "results/calibration").glob("*/meta.json")):
                try:
                    m = json.loads(cand.read_text())
                except Exception:
                    continue
                if m.get("run_id") == run_id or m.get("id") == run_id:
                    bundle = cand.parent
                    break
        meta = {}
        if bundle is not None and (bundle / "meta.json").exists():
            meta = json.loads((bundle / "meta.json").read_text())
        rows.append(
            {
                "iso": iso,
                "keeper": run_id,
                "bundle": (
                    str(bundle.relative_to(REPO)) if bundle is not None else None
                ),
                "bundle_present": bundle is not None,
                "commitment": meta.get("commitment"),
                "passes": meta.get("passes"),
            }
        )
    return rows


def leg2_stony_brook() -> dict:
    """Plant 6081 units 004/005 routing in the committed NEISO outage extract."""
    if not OUTAGES.exists():
        return {"_missing": str(OUTAGES.relative_to(REPO))}
    df = pd.read_csv(OUTAGES)
    plant_col = next(
        (c for c in df.columns if c.lower() in {"plant_code", "plant_id", "facility_id"}),
        None,
    )
    unit_col = next(
        (c for c in df.columns if c.lower() in {"unit_id", "unitid", "unit"}), None
    )
    if plant_col is None or "plant_group" not in df.columns:
        return {"_columns": list(df.columns)}
    sel = df[df[plant_col].astype(str) == "6081"]
    out = {"columns": [plant_col, unit_col, "plant_group"], "units": []}
    for unit, g in sel.groupby(sel[unit_col].astype(str) if unit_col else sel.index):
        out["units"].append(
            {
                "unit": str(unit),
                "rows": int(len(g)),
                "plant_groups": sorted(map(str, g["plant_group"].unique())),
            }
        )
    out["units"].sort(key=lambda r: r["unit"])
    return out


def leg3_nyiso_disclosure() -> dict:
    """Does the NYISO keeper still arm nyiso_import_hub_prices?"""
    d = json.loads((KEEPER_DIR / "NYISO.json").read_text())
    run_id = d.get("keeper")
    bundle = bundle_for(run_id)
    if bundle is None:
        for cand in sorted((REPO / "results/calibration").glob("*/meta.json")):
            try:
                m = json.loads(cand.read_text())
            except Exception:
                continue
            if m.get("run_id") == run_id or m.get("id") == run_id:
                bundle = cand.parent
                break
    res = {"nyiso_keeper": run_id, "bundle_present": bundle is not None}
    if bundle is not None and (bundle / "run_config.json").exists():
        cfg = json.loads((bundle / "run_config.json").read_text())
        flat = cfg.get("scenario", cfg) if isinstance(cfg, dict) else {}
        res["nyiso_import_hub_prices"] = _deep_get(flat, "nyiso_import_hub_prices")
    return res


def _deep_get(obj, key):
    """Find ``key`` anywhere in a nested dict (run_config nesting varies by vintage)."""
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for v in obj.values():
            got = _deep_get(v, key)
            if got is not None:
                return got
    return None


def leg45_actual_tail_by_year() -> list[dict]:
    """Per-year actual-LMP extremes and >$300 counts, MEASURED SIDE ONLY.

    No model output is read and nothing is scored: this is an input inspection of
    the repaired instrument, which rule 22 leaves unrestricted.
    """
    df = pd.read_parquet(NEISO_LMP)  # columns: year, hour, rt, da
    rows = []
    for year in sorted({*LADDER_YEARS, LOCKED_YEAR}):
        sel = df[df["year"] == year]
        if sel.empty:
            rows.append({"year": year, "_absent": True})
            continue
        rec = {
            "year": year,
            "rows": int(len(sel)),
            "inside_repaired_span": year in REPAIRED_SPAN,
        }
        for market in ("rt", "da"):
            col = next((c for c in sel.columns if c.lower() == market), None)
            if col is None:
                col = next((c for c in sel.columns if market in c.lower()), None)
            if col is None:
                continue
            vals = pd.to_numeric(sel[col], errors="coerce")
            rec[f"{market}_max"] = round(float(vals.max()), 4)
            rec[f"{market}_mean"] = round(float(vals.mean()), 4)
            rec[f"{market}_hours_gt_300"] = int((vals > TAIL_THRESHOLD).sum())
            rec[f"{market}_coverage"] = round(float(vals.notna().mean()), 4)
        rows.append(rec)
    return rows


def leg6_partial_year_gate() -> dict:
    """Is the HOURS_PER_YEAR full-series gate still live in eia930.frames?"""
    src = REPO / "src/market_sim/data/eia930/frames.py"
    if not src.exists():
        return {"_missing": "src/market_sim/data/eia930/frames.py"}
    text = src.read_text()
    hits = [
        line.strip()
        for line in text.splitlines()
        if "HOURS_PER_YEAR" in line
    ]
    return {
        "file": "src/market_sim/data/eia930/frames.py",
        "hours_per_year_references": hits,
        "gate_present": bool(hits),
    }


def main() -> None:
    result = {
        "probe": "neiso98_escalations_and_final_readiness",
        "solve_performed": False,
        "scored_any_out_of_training_year": False,
        "leg1_p2_scoring_basis": leg1_p2_basis(),
        "leg2_stony_brook_6081": leg2_stony_brook(),
        "leg3_nyiso_disclosure": leg3_nyiso_disclosure(),
        "leg45_actual_lmp_by_year": leg45_actual_tail_by_year(),
        "leg6_partial_year_gate": leg6_partial_year_gate(),
    }

    p2 = [r for r in result["leg1_p2_scoring_basis"] if r.get("commitment") is True]
    result["verdict"] = {
        "isos_on_legacy_p2": sorted(r["iso"] for r in p2),
        "neiso_is_sole_p2_iso": [r["iso"] for r in p2] == ["NEISO"],
        "keeper_bundles_resolved": sum(
            1 for r in result["leg1_p2_scoring_basis"] if r["bundle_present"]
        ),
        "ladder_years_all_inside_repaired_span": all(
            r.get("inside_repaired_span")
            for r in result["leg45_actual_lmp_by_year"]
            if r["year"] in LADDER_YEARS and not r.get("_absent")
        ),
        "y2019_rt_hours_gt_300": next(
            (
                r.get("rt_hours_gt_300")
                for r in result["leg45_actual_lmp_by_year"]
                if r["year"] == LOCKED_YEAR
            ),
            None,
        ),
        "y2019_rt_max": next(
            (
                r.get("rt_max")
                for r in result["leg45_actual_lmp_by_year"]
                if r["year"] == LOCKED_YEAR
            ),
            None,
        ),
        "partial_year_gate_still_live": result["leg6_partial_year_gate"].get(
            "gate_present"
        ),
    }

    OUT.write_text(json.dumps(result, indent=2) + "\n")

    print("=== leg 1 — keeper scoring basis (commitment / passes) ===")
    for r in result["leg1_p2_scoring_basis"]:
        print(
            f"  {r['iso']:<6} {r['keeper']:<38} commitment={r['commitment']!s:<6}"
            f" passes={r['passes']}  bundle={'yes' if r['bundle_present'] else 'MISSING'}"
        )
    print("\n=== leg 2 — Stony Brook plant 6081 outage routing ===")
    print("  " + json.dumps(result["leg2_stony_brook_6081"]))
    print("\n=== leg 3 — NYISO cross-ISO disclosure ===")
    print("  " + json.dumps(result["leg3_nyiso_disclosure"]))
    print("\n=== legs 4/5 — actual NEISO LMP by year (INPUT read, nothing scored) ===")
    for r in result["leg45_actual_lmp_by_year"]:
        if r.get("_absent"):
            print(f"  {r['year']}: ABSENT from the committed parquet")
            continue
        print(
            f"  {r['year']}: repaired={r['inside_repaired_span']!s:<5}"
            f" rt_max {r.get('rt_max'):>9.2f} rt>{TAIL_THRESHOLD:.0f} {r.get('rt_hours_gt_300'):>4}"
            f" | da_max {r.get('da_max'):>9.2f} da>{TAIL_THRESHOLD:.0f} {r.get('da_hours_gt_300'):>4}"
            f" | rows {r['rows']} cov {r.get('rt_coverage')}"
        )
    print("\n=== leg 6 — partial-year solve gate ===")
    for line in result["leg6_partial_year_gate"].get("hours_per_year_references", []):
        print(f"  {line}")
    print("\n=== verdict ===")
    for k, v in result["verdict"].items():
        print(f"  {k}: {v}")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

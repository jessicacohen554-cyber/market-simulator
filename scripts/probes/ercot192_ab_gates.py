"""ERCOT-192 A/B gate scorer — the precommit §5 table, read-only, no LP.

Scores the pre-registered A/B gates on the two committed bundles and writes one
artifact. Nothing here re-scores the rubric: ``metrics.json`` is read as each
solve wrote it.

Gates (``docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md``
§5):

* **G-BIT** (KILL) — 2024 and 2025 must be **bit-identical** between control and
  arm. The year table carries 2023 only, so any 2024/25 motion means the
  implementation leaked outside its year. Scored on the sha256 of every
  ``hourly/*_<year>.parquet`` sidecar plus the per-year price/objective
  aggregates.
* **G-SHED** (KILL) — no NEW shed year vs the control (the ercot-48/49
  manufactured-shortage falsifier).
* **G-OWNER** (report + escalate) — C3a-2024 stays PASS, C3b-2024 under 0.20,
  C3a-2025 within its −9.1 % bound.
* **G-DET** (report) — determination and fail set, as measured.
* **C3a / C3b / C3c per year** — reported at FULL MAGNITUDE and, per §0, never
  targeted: this lane is not C3a-2023 spend (card Q, ruling Q-B, final).

**G-COAL148 is NOT scored here** — it has its own committed scorer,
``scripts/probes/ercot185_coal148.py``, run against the same pair.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot192_ab_gates.py \
        --base results/calibration/ercot192_ctl_A \
        --arm  results/calibration/ercot192_arm_B
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pandas as pd  # noqa: E402

YEARS = (2023, 2024, 2025)
BIT_YEARS = (2024, 2025)
DEFAULT_OUT = REPO / "results/calibration/ercot192_ab_gates.json"


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _sidecar_shas(bundle: Path, year: int) -> dict[str, str]:
    """sha256 of every hourly sidecar for one year."""
    out: dict[str, str] = {}
    hourly = bundle / "hourly"
    if not hourly.is_dir():
        return out
    for p in sorted(hourly.glob(f"*_{year}.parquet")):
        out[p.name] = _sha(p)
    return out


def _system_aggregates(bundle: Path, year: int) -> dict:
    """Per-year P1 price/demand aggregates — a second, independent G-BIT face."""
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return {}
    df = pd.read_parquet(p)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    lw = num / den
    return {
        "load_weighted_price_mean": round(float(lw.mean()), 8),
        "hours_gt_200": int((lw > 200.0).sum()),
        "price_sum": round(float(df["price"].sum()), 6),
        "demand_sum": round(float(df["demand"].sum()), 6),
    }


def _criteria_rows(bundle: Path) -> dict:
    """The scored criteria block, as the solve wrote it."""
    p = bundle / "metrics.json"
    if not p.exists():
        raise SystemExit(f"{bundle}: no metrics.json — the solve did not score")
    return json.loads(p.read_text())


def _shed_hours(bundle: Path, year: int) -> dict:
    """P1 shed (slack) total and hour count for one year."""
    p = bundle / "hourly" / f"system_{year}.parquet"
    if not p.exists():
        return {}
    df = pd.read_parquet(p)
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    return {
        "slack_MWh": round(float(df["slack"].sum()), 6),
        "shed_hours": int((df.groupby("hour")["slack"].sum() > 0).sum()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--arm", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    out: dict = {
        "probe": "ercot192_ab_gates",
        "precommit": (
            "docs/PRECOMMIT-ercot192-coal-limbs-2023-reapplication-2026-08-12.md"
        ),
        "base": str(args.base),
        "arm": str(args.arm),
    }

    # ---- G-BIT (KILL) ---------------------------------------------------
    bit: dict = {"years": {}, "verdict": "PASS"}
    for year in BIT_YEARS:
        b_sha, a_sha = _sidecar_shas(args.base, year), _sidecar_shas(args.arm, year)
        b_agg, a_agg = (
            _system_aggregates(args.base, year),
            _system_aggregates(args.arm, year),
        )
        same_files = sorted(b_sha) == sorted(a_sha)
        mismatched = sorted(k for k in b_sha if b_sha.get(k) != a_sha.get(k))
        agg_same = b_agg == a_agg
        ok = bool(same_files and not mismatched and agg_same and b_sha)
        bit["years"][str(year)] = {
            "n_sidecars": len(b_sha),
            "same_file_set": same_files,
            "mismatched_sidecars": mismatched,
            "aggregates_identical": agg_same,
            "base_aggregates": b_agg,
            "arm_aggregates": a_agg,
            "verdict": "PASS" if ok else "FAIL",
        }
        if not ok:
            bit["verdict"] = "FAIL"
    out["G_BIT"] = bit

    # ---- the reported per-year numbers (NEVER targeted, precommit §0) ----
    mb, ma = _criteria_rows(args.base), _criteria_rows(args.arm)
    out["G_DET"] = {
        "base": {
            "determination": mb.get("determination"),
            "reasons": mb.get("reasons"),
            "caveats": mb.get("caveats"),
        },
        "arm": {
            "determination": ma.get("determination"),
            "reasons": ma.get("reasons"),
            "caveats": ma.get("caveats"),
        },
        "determination_changed": mb.get("determination") != ma.get("determination"),
    }
    reported: dict = {"criteria_status": {}, "load_weighted_price_by_year": {}}
    for crit in sorted(set(mb.get("criteria", {})) | set(ma.get("criteria", {}))):
        reported["criteria_status"][crit] = {
            "base": (mb.get("criteria", {}).get(crit) or {}).get("status"),
            "arm": (ma.get("criteria", {}).get(crit) or {}).get("status"),
            "label": (mb.get("criteria", {}).get(crit) or {}).get("label"),
        }
    # metrics.json carries only per-criterion status; the per-year C3a/C3b cells
    # come from scripts/calibration_verdict.py AFTER registration (it scores off
    # the run payload + bench). The bundle-basis load-weighted mean below is the
    # model side of C3a and is reported here so the A/B delta is visible without
    # a registration round-trip.
    for year in YEARS:
        reported["load_weighted_price_by_year"][str(year)] = {
            "base": _system_aggregates(args.base, year),
            "arm": _system_aggregates(args.arm, year),
        }
    out["reported"] = reported
    out["grade_summary"] = {
        "base": mb.get("grade_summary"),
        "arm": ma.get("grade_summary"),
    }
    out["reporting_note"] = (
        "Per precommit §0 and card Q ruling Q-B (final, ercot-191): this lane is "
        "NOT C3a-2023 spend. Every price movement here is reported at full "
        "magnitude, was never targeted, is not a gate and is not the promotion "
        "basis. No C3a-2023 improvement is claimed."
    )

    # ---- G-SHED (KILL) --------------------------------------------------
    shed: dict = {"years": {}, "verdict": "PASS"}
    for year in YEARS:
        b, a = _shed_hours(args.base, year), _shed_hours(args.arm, year)
        new_shed = bool(
            b and a and b.get("shed_hours", 0) == 0 and a.get("shed_hours", 0) > 0
        )
        shed["years"][str(year)] = {"base": b, "arm": a, "new_shed_year": new_shed}
        if new_shed:
            shed["verdict"] = "FAIL"
    out["G_SHED"] = shed

    args.out.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()

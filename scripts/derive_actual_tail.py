"""Derive the committed actual scarcity-tail part for the C3c verdict criterion.

Writes ``frontend/data/backcast/tail/actual_tail.json`` — per (ISO, year) counts
of actual hours above the ISO's scarcity threshold (rubric §5) in BOTH markets:

- ``da_gt``: hours the **day-ahead** hourly market cleared above the threshold —
  the *DA-expressible tail*, the rubric-v2 C3c benchmark. The DA market is an
  hourly, commitment-aware market: the same temporal resolution as this model's
  hourly LP, so its tail count is the scarcity an hourly model is *in scope* to
  reproduce (docs/multi-iso/miso-scarcity-tail-diagnosis.md §1: MISO 2023's
  entire 30-hour RT tail is single-hour 5-minute-market transients; the DA tail
  that year is 1 hour).
- ``rt_gt``: hours the real-time market averaged above the threshold — reported
  alongside as the out-of-representation companion (RT includes sub-hourly ramp
  scarcity, forecast misses and re-dispatch transients an hourly deterministic
  LP cannot see). Note the direction is not uniform: ERCOT's DA tail is LARGER
  than its RT tail (2023: 311 vs 181 h — DA prices scarcity expectations), so
  the DA basis is not a leniency device.

Source: ``data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet``
(single hub series, columns ``year, hour, rt, da`` — the same files
``render_calibration_html._actual_lmp_hourly`` reads). Coverage fractions are
recorded so a partially-covered series (e.g. CAISO 2023 DA, whose Jan–Feb aged
out of OASIS retention) is visibly a LOWER BOUND on the count.

Holdout guard (CLAUDE.md rule 22): only 2023–2025 are read or written. The
script refuses to emit any other year even if present in the source files.

Usage:
    uv run python scripts/derive_actual_tail.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
SRC_DIR = REPO / "data" / "raw" / "_validation-source"
OUT = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"

# Per-ISO scarcity-tail threshold ($/MWh) — MUST mirror rubric §5 /
# calibration_verdict.TAIL_THRESHOLD (winter city-gate scarcity sets
# NYISO/NEISO higher).
TAIL_THRESHOLD = {
    "ERCOT": 200.0,
    "PJM": 200.0,
    "MISO": 200.0,
    "CAISO": 200.0,
    "NYISO": 300.0,
    "NEISO": 300.0,
}

# Rule-22 holdout quarantine: 2022 and H1-2026 are untouchable until an ISO's
# calibration-complete marker exists; this deriver never emits any year outside
# the calibration window regardless of what the source files carry.
ALLOWED_YEARS = (2023, 2024, 2025)


def derive() -> dict:
    """Compute the per-(ISO, year) DA/RT tail counts from the hub series."""
    isos: dict[str, dict] = {}
    for iso, thr in sorted(TAIL_THRESHOLD.items()):
        p = SRC_DIR / f"actual_lmp_hourly_{iso}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        for year, d in df.groupby(df["year"].astype(int)):
            if int(year) not in ALLOWED_YEARS:
                continue  # holdout guard — never derive outside 2023-2025
            rt = d["rt"].to_numpy(float)
            da = (
                d["da"].to_numpy(float)
                if "da" in d.columns
                else np.full(len(d), np.nan)
            )
            isos.setdefault(iso, {})[str(int(year))] = {
                "threshold": thr,
                "da_gt": int(np.nansum(da > thr)),
                "rt_gt": int(np.nansum(rt > thr)),
                "da_coverage": round(float(np.mean(~np.isnan(da))), 3),
                "rt_coverage": round(float(np.mean(~np.isnan(rt))), 3),
                "hours": int(len(d)),
            }
    return {
        "note": (
            "Actual scarcity-tail hour counts per ISO-year at the rubric §5 "
            "threshold. da_gt (day-ahead) is the DA-expressible tail the C3c "
            "criterion gates on (same hourly resolution as the model LP); "
            "rt_gt (real-time) is the reported out-of-representation companion "
            "(includes sub-hourly transients). Counts over covered hours only — "
            "a coverage < 1.0 makes the count a lower bound. Source: "
            "data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet (hub "
            "series). Regenerate with scripts/derive_actual_tail.py when a "
            "source series updates (rule 23: re-derivation commits cite the "
            "data change). Years restricted to 2023-2025 (rule-22 holdout "
            "quarantine)."
        ),
        "thresholds": TAIL_THRESHOLD,
        "isos": isos,
    }


def main() -> None:
    out = derive()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for iso, years in sorted(out["isos"].items()):
        row = ", ".join(
            f"{y}: DA {r['da_gt']}h / RT {r['rt_gt']}h"
            for y, r in sorted(years.items())
        )
        print(f"{iso:6s} (> ${out['thresholds'][iso]:.0f}) {row}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

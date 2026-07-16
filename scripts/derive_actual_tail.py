"""Derive the committed actual scarcity-tail part for the C3c verdict criterion.

Writes ``frontend/data/backcast/tail/actual_tail.json`` — per (ISO, year) counts
of actual hours above the ISO's scarcity threshold (rubric §5) in BOTH markets:

- ``rt_gt``: hours the **real-time** market's hourly hub average cleared above
  the threshold — the actual RT scarcity tail, the C3c benchmark for EVERY ISO
  (rubric v2.7 owner amendment 2026-07-16: the tail criterion judges the
  scarcity the market actually realized).
- ``da_gt``: hours the day-ahead hourly market cleared above the threshold —
  reported alongside as the non-gated diagnostic companion. The DA count
  prices scarcity *expectations*: its wedge over RT is the day-ahead
  weather/load forecast-risk premium a realized-weather (perfect-foresight)
  backcast is out of representation to price. The direction is not uniform:
  ERCOT's DA tail is LARGER than its RT tail (2023: 311 vs 181 h) while
  MISO's is far smaller (2023: 1 vs 30 h).

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
# calibration-complete marker exists; this deriver never emits a holdout year
# for an ISO without its marker in calibration-complete.json. In-sample years
# are always allowed; a marker'd ISO additionally emits the holdout years its
# one-shot validation scores (the marker is the authorization — CLAUDE.md
# rule 22; first use: NEISO 2022, declared 2026-07-07).
ALLOWED_YEARS = (2023, 2024, 2025)
HOLDOUT_YEARS = (2022, 2026)
_MARKER_PATH = (
    Path(__file__).resolve().parent.parent
    / "frontend"
    / "data"
    / "backcast"
    / "calibration-complete.json"
)


def _marker_isos() -> set[str]:
    """ISOs with a calibration-complete marker (holdout years unlocked)."""
    try:
        data = json.loads(_MARKER_PATH.read_text())
    except (OSError, ValueError):
        return set()
    return {str(k).upper() for k in (data.get("complete") or {})}


def derive() -> dict:
    """Compute the per-(ISO, year) DA/RT tail counts from the hub series."""
    isos: dict[str, dict] = {}
    marker_isos = _marker_isos()
    for iso, thr in sorted(TAIL_THRESHOLD.items()):
        p = SRC_DIR / f"actual_lmp_hourly_{iso}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        for year, d in df.groupby(df["year"].astype(int)):
            year_ok = int(year) in ALLOWED_YEARS or (
                int(year) in HOLDOUT_YEARS and iso.upper() in marker_isos
            )
            if not year_ok:
                continue  # holdout guard — marker-gated (rule 22)
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
            "threshold. rt_gt (real-time hourly hub average) is the actual RT "
            "scarcity tail the C3c criterion gates on for every ISO (rubric "
            "v2.7, owner amendment 2026-07-16); da_gt (day-ahead) is the "
            "reported non-gated diagnostic companion (prices scarcity "
            "expectations — embeds the DA forecast-risk premium). Counts over "
            "covered hours only — a coverage < 1.0 makes the count a lower "
            "bound. Source: "
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

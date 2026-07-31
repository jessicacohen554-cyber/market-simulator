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
    uv run python scripts/data/derive_actual_tail.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import CALIBRATION_DIR  # noqa: E402
from scripts.lib import holdout_policy  # noqa: E402

SRC_DIR = CALIBRATION_DIR
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

# Rule-22 holdout quarantine, TIER-AWARE (owner decision 2026-07-31). An
# out-of-training year is emitted only when the ISO carries the marker for
# THAT YEAR'S TIER: ``complete`` authorizes the validation ladder
# (2018/2020/2021/2022), ``final`` authorizes the locked test (2019, H1-2026).
# The tier map is :mod:`scripts.lib.holdout_policy` — the same module the
# other three gates read (run_calibration_full.enforce_holdout_year_gate,
# legitimacy_diagnostics.run_d6_quarantine, audit_keepers) — so a new ladder
# rung is one edit there, not a second constant here, and an unenumerated year
# fails closed to the locked tier.
#
# Previously this deriver read the ``complete`` block alone, so an ISO holding
# only the validation marker (PJM/NYISO today) would have had its H1-2026
# locked-tier row emitted off a declaration that does not authorize it.
ALLOWED_YEARS = tuple(sorted(holdout_policy.CALIBRATION_YEARS))

# Out-of-training years this deriver will CONSIDER at all. Deliberately NOT
# the full ``holdout_policy.VALIDATION_YEARS`` ladder: rule 22 makes the
# backward rungs (2018/2020/2021) staged owner decisions taken one at a time,
# and no ISO has been granted one — PJM's own marker reads "validation ONLY
# (2022)". Widening this tuple is that separate owner decision; the tier gate
# below then still requires the right marker block for whatever is added.
CONSIDERED_HOLDOUT_YEARS: tuple[int, ...] = (2022, 2026)

_MARKER_PATH = (
    Path(__file__).resolve().parent.parent.parent / holdout_policy.MARKER_FILE
)


def _marker_doc() -> dict:
    """Parsed ``calibration-complete.json``; ``{}`` when absent/unreadable.

    An empty document authorizes nothing out-of-training — fail closed.
    """
    try:
        return json.loads(_MARKER_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _year_emittable(iso: str, year: int, marker_doc: dict) -> bool:
    """Whether ``iso``'s ``year`` may be emitted under the rule-22 tier gates.

    Two conditions, both required for an out-of-training year: it is one this
    deriver considers at all (:data:`CONSIDERED_HOLDOUT_YEARS`), and the ISO
    holds the marker block for that year's tier.
    """
    tier = holdout_policy.tier_for_year(year)
    if tier == holdout_policy.TIER_TRAIN:
        return True
    if int(year) not in CONSIDERED_HOLDOUT_YEARS:
        return False
    return holdout_policy.authorized(marker_doc, iso.upper(), tier)


def derive() -> dict:
    """Compute the per-(ISO, year) DA/RT tail counts from the hub series."""
    isos: dict[str, dict] = {}
    marker_doc = _marker_doc()
    for iso, thr in sorted(TAIL_THRESHOLD.items()):
        p = SRC_DIR / f"actual_lmp_hourly_{iso}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        for year, d in df.groupby(df["year"].astype(int)):
            if not _year_emittable(iso, int(year), marker_doc):
                continue  # holdout guard — per-tier marker (rule 22)
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
            "series). Regenerate with scripts/data/derive_actual_tail.py when a "
            "source series updates (rule 23: re-derivation commits cite the "
            "data change). Years restricted by the rule-22 TIER gates "
            "(scripts/lib/holdout_policy): 2023-2025 always; a validation-"
            "ladder year (2018/2020/2021/2022) only for an ISO in the marker "
            "file's `complete` block; a locked-test year (2019, H1-2026) only "
            "for an ISO in `final`."
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

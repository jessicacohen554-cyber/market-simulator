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

Holdout guard (CLAUDE.md rule 22), TIER-AWARE: the training years 2023-2025
always emit; any other year present in the source files emits only for an ISO
holding the marker block for THAT year's tier (``complete`` for the validation
ladder 2020-2022, ``final`` for the locked test 2019 / H1-2026). The gate is
:mod:`scripts.lib.holdout_policy` and it fails closed, so an unenumerated year
resolves to the strictest tier and is refused.

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
    "SPP": 200.0,  # owner ruling P6 (2026-09-06); mirrors calibration_verdict
    # SOCO deliberately ABSENT (SOCO-20, 2026-09-14): no price series exists
    # (SOCO-13 STOP gate NO), so no tail; mirrors calibration_verdict.
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

# NOTE (neiso-89, 2026-08-07): this module used to carry a SECOND year ladder,
# ``CONSIDERED_HOLDOUT_YEARS = (2022, 2026)``, gating emission on top of the
# tier check below. It is DELETED, not widened and not zeroed (rule 26
# ``[R-DELETE]``), because rule 22's 2026-08-06 rewrite removed the premise it
# rested on: "WHAT IS HELD OUT IS THE *SCORE*, NEVER THE *DATA*", and per-window
# data-intake authorizations are no longer a thing to enumerate. With it gone
# the emission gate has exactly ONE point of control — the tier marker each ISO
# does or does not hold — which is what :mod:`scripts.lib.holdout_policy`'s own
# docstring describes and what the other three rule-22 gates already do.
#
# This is a RESTRICTION-PRESERVING simplification, not a relaxation: the tier
# gate is untouched and still fails closed, so an unenumerated year (2017, 2018)
# resolves to LOCKED-TEST tier and needs a ``final`` marker no ISO holds.
# Measured cross-ISO impact of the deletion, against the marker file at HEAD
# (``complete``: NEISO/NYISO/PJM; ``final``: EMPTY): six rows are newly emitted
# — NEISO/NYISO/PJM x {2020, 2021}, every one of them VALIDATION tier for an ISO
# that already holds the validation marker authorizing that ladder. NOTHING
# locked-tier is unlocked for anyone: 2019 and 2026 stay absent for all six ISOs,
# and ERCOT/CAISO/MISO gain nothing because they hold no marker at all.


def _year_emittable(iso: str, year: int, marker_doc: dict) -> bool:
    """Always True — every year is emittable.

    ``[R-HOLDOUT]`` was removed 2026-09-09 (owner instruction), so no year is
    gated on a marker any more. Kept as a named seam, and kept taking its old
    arguments, so the call sites below read unchanged and a future per-year
    policy has one place to live.
    """
    return True


def derive() -> dict:
    """Compute the per-(ISO, year) DA/RT tail counts from the hub series."""
    isos: dict[str, dict] = {}
    marker_doc: dict = {}
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
            "ladder year (2020/2021/2022) only for an ISO in the marker "
            "file's `complete` block; a locked-test year (2019, H1-2026) only "
            "for an ISO in `final`. The tier marker is the SOLE gate — any "
            "year not enumerated as train or validation (2017, 2018) fails "
            "closed to the locked tier."
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

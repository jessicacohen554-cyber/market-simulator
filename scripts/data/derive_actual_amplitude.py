"""Derive the committed actual diurnal-amplitude part for the REPORTED-ONLY
hour-of-day price-amplitude measurement.

Writes ``frontend/data/backcast/amplitude/actual_amplitude.json`` — per
(ISO, year) the measured **hour-of-day mean price profile** in both markets:

- ``rt_hod``: the 24-value hour-of-day mean of the real-time hourly hub price.
  This is the primary basis, because it is what the rubric already gates the
  price LEVEL on (``calibration_verdict.score_price_mean``: RT is the honest
  benchmark for a perfect-foresight dispatch LP, DA only a fallback).
- ``da_hod``: the same profile in the day-ahead market, the reported companion.

**Why a 24-value profile is all the scorer needs.** Every committed run payload
already carries ``lmpDeltaHr`` — the hourly ``model − actual RT`` delta, written
by ``render_calibration_html`` as int16 with ``-32768`` reserved as the
NOT-A-NUMBER sentinel. Because the hour-of-day mean is linear,

    hod(model) = hod(actual) + hod(delta)

so the scorer reconstructs the model's own profile from this part plus the
payload it already reads. **Nothing here needs an LP solve, a bundle
regeneration or a re-registration** — every already-registered run scores in
place, which is the same property that made the C3c standing rule scorer-only.

**Day mask.** A day carrying any missing hour is DROPPED from the profile and
counted, never interpolated (the ``_xiso1_diurnal_amplitude_audit`` convention),
so a partially-covered series (CAISO 2023 DA, whose Jan–Feb aged out of OASIS
retention) reports on its covered days and says how many. The scorer applies the
same rule to the delta by dropping days that carry the sentinel; the two masks
coincide because the model side is never missing, so a sentinel hour is exactly
an hour with no committed actual.

Source: ``data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet`` (hub
series, columns ``year, hour, rt, da``) — the same files
``derive_actual_tail.py`` reads for the C3c part.

Holdout guard (CLAUDE.md rule 22 ``[R-HOLDOUT]``), TIER-AWARE and identical to
``derive_actual_tail``: the training years 2023–2025 always emit; any other year
present in the source emits only for an ISO holding the marker block for THAT
year's tier (``complete`` for the validation ladder 2020–2022, ``final`` for the
locked test 2019 / H1-2026). The gate is :mod:`scripts.lib.holdout_policy` and
it FAILS CLOSED, so an unenumerated year resolves to the strictest tier and is
refused. Deriving the part is data preparation, not a spend — rule 22's
2026-08-06 clarification ("what is held out is the SCORE, never the DATA") — but
the tier gate is kept anyway so this part can never be the thing that makes an
unauthorized year scorable.

Usage:
    uv run python scripts/data/derive_actual_amplitude.py
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

SRC_DIR = CALIBRATION_DIR
OUT = REPO / "frontend" / "data" / "backcast" / "amplitude" / "actual_amplitude.json"

# SOCO is deliberately ABSENT (SOCO-20, 2026-09-14): the amplitude reference is
# a PRICE artifact and SOCO has no price series (SOCO-13 STOP gate NO; the
# rubric v3.8 no-price class scores C1/C2/C4/C6/C8 only) — the third of the
# three TAIL_THRESHOLD-family skips gate G6 names, documented, not forgotten.
ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NYISO", "PJM", "SPP")
DAYS, HOURS_PER_DAY = 365, 24


def _year_emittable(iso: str, year: int, marker_doc: dict) -> bool:
    """Always True — every year is emittable.

    ``[R-HOLDOUT]`` was removed 2026-09-09 (owner instruction), so no year is
    gated on a marker any more. Kept as a named seam, and kept taking its old
    arguments, so the call sites below read unchanged and a future per-year
    policy has one place to live.
    """
    return True


def hour_of_day(series: np.ndarray) -> tuple[list[float] | None, int]:
    """Hour-of-day mean profile over COMPLETE days, and the day count.

    Days carrying any missing hour are dropped, never interpolated. Returns
    ``(None, 0)`` when no complete day survives, so a fully-absent series is
    recorded as absent rather than as a profile of NaN.
    """
    if series.size < DAYS * HOURS_PER_DAY:
        series = np.concatenate(
            [series, np.full(DAYS * HOURS_PER_DAY - series.size, np.nan)]
        )
    grid = series[: DAYS * HOURS_PER_DAY].reshape(DAYS, HOURS_PER_DAY)
    ok = ~np.isnan(grid).any(axis=1)
    if not ok.any():
        return None, 0
    return [round(float(v), 4) for v in grid[ok].mean(axis=0)], int(ok.sum())


def derive() -> dict:
    """Compute the per-(ISO, year) measured hour-of-day profiles."""
    isos: dict[str, dict] = {}
    marker_doc: dict = {}
    for iso in ISOS:
        path = SRC_DIR / f"actual_lmp_hourly_{iso}.parquet"
        if not path.exists():
            continue
        df = pd.read_parquet(path)
        for year, day in df.groupby(df["year"].astype(int)):
            if not _year_emittable(iso, int(year), marker_doc):
                continue  # holdout guard — per-tier marker (rule 22)
            day = day.sort_values("hour")
            row: dict = {}
            for kind in ("rt", "da"):
                if kind not in day.columns:
                    continue
                arr = pd.to_numeric(day[kind], errors="coerce").to_numpy(float)
                hod, ndays = hour_of_day(arr)
                if hod is None:
                    continue
                row[f"{kind}_hod"] = hod
                row[f"{kind}_days"] = ndays
                row[f"{kind}_range"] = round(float(max(hod) - min(hod)), 4)
                row[f"{kind}_peak_hour"] = int(np.argmax(hod))
                row[f"{kind}_trough_hour"] = int(np.argmin(hod))
            if row:
                row["hours"] = int(len(day))
                isos.setdefault(iso, {})[str(int(year))] = row
    return {
        "note": (
            "Measured hour-of-day mean price profiles per ISO-year, the actual "
            "side of the REPORTED-ONLY diurnal price-amplitude measurement "
            "(rubric v3.5, owner decision 2026-08-25 — option B of "
            "docs/DECISION-CARD-xiso-diurnal-amplitude-rubric-2026-08.md). "
            "rt_hod is the primary basis (the same RT benchmark C3a gates the "
            "price level on); da_hod is the reported companion. Profiles are "
            "means over COMPLETE days only — a day with any missing hour is "
            "dropped and *_days records how many survived, so a partially "
            "covered series is visibly a partial-coverage profile rather than "
            "a silently interpolated one. The scorer reconstructs the model's "
            "own profile as hod(model) = hod(actual) + hod(lmpDeltaHr) from the "
            "run payload it already reads, so the measurement needs NO LP "
            "solve, NO bundle regeneration and NO re-registration: every "
            "already-registered run scores in place. This part is REPORTED-ONLY "
            "input: it contributes no criterion status and no caveat budget, "
            "and cannot change any determination. Source: "
            "data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet (hub "
            "series). Regenerate with scripts/data/derive_actual_amplitude.py "
            "when a source series updates (rule 23: re-derivation commits cite "
            "the data change). Years restricted by the rule-22 TIER gates "
            "(scripts/lib/holdout_policy): 2023-2025 always; a validation-"
            "ladder year (2020/2021/2022) only for an ISO in the marker file's "
            "`complete` block; a locked-test year (2019, H1-2026) only for an "
            "ISO in `final`. The gate fails closed."
        ),
        "isos": isos,
    }


def main() -> None:
    out = derive()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    for iso, years in sorted(out["isos"].items()):
        row = ", ".join(
            f"{y}: RT ${r.get('rt_range', float('nan')):.2f} ({r.get('rt_days', 0)}d)"
            for y, r in sorted(years.items())
        )
        print(f"{iso:6s} hod range  {row}")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

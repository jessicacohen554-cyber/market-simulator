"""caiso-228 gate D0 — coverage of the measured RT scarcity tail by qualifying
SoCalGas low-OFO gas days.

PRE-REGISTERED, EVIDENCE-ONLY (PRECOMMIT-caiso227-ofo-arm-2026-08-31.md §4 D0).
The trigger definition is FROZEN by that precommit's §2 and may NOT be revised
in response to anything measured here: a qualifying gas day is any SoCalGas
``side == "low"`` row in the ``gas-ofo-events`` clean partition — every stage,
waived days included, no tolerance cut.

Reads committed bytes only (no solve):

- ``data/clean/gas-ofo-events/CAISO/gas-ofo-events.parquet`` (curated from the
  immutable raw ENVOY snapshots) — the qualifying gas days.
- ``data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet`` — the measured
  hourly hub RT price whose >$200 hours ARE the C3c benchmark tail
  (``scripts/data/derive_actual_tail.py``; rubric §5, CAISO threshold $200).

Gas-day offset (PRECOMMIT §4 D4, schema ``gas_day`` description): a SoCalGas
gas day runs 07:00-07:00 **Pacific**, so gas day D covers operating hours
[D 07:00, D+1 07:00) local. A midnight-to-midnight mapping is a bug; both are
computed here so the offset's effect is visible rather than asserted.

Model/actual clock: row k of the hourly frame is the k-th physical hour of the
BA-local (prevailing Pacific) calendar year with Feb 29 dropped — the
``eia_loader._eia_hourly_frame`` semantics mirrored in
:func:`market_sim.data.storage_as_awards._model_frame_utc_index`.

Usage:
    uv run python scripts/probes/caiso228_ofo_d0_coverage.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

YEARS = (2023, 2024, 2025)
TAIL_THRESHOLD = 200.0  # rubric §5, CAISO — mirrors calibration_verdict.TAIL_THRESHOLD
PACIFIC = ZoneInfo("America/Los_Angeles")
GAS_DAY_START_HOUR = 7  # SoCalGas gas day 07:00-07:00 Pacific (schema gas_day)


def local_stamps(year: int, hours: int) -> pd.DatetimeIndex:
    """Local (Pacific) wall-clock stamp of each row of the model hourly frame."""
    start = pd.Timestamp(year=year, month=1, day=1, tz=PACIFIC)
    end = pd.Timestamp(year=year + 1, month=1, day=1, tz=PACIFIC)
    rng = pd.date_range(start, end, freq="h", inclusive="left")
    rng = rng[~((rng.month == 2) & (rng.day == 29))]
    return rng[:hours]


def main() -> None:
    ofo = pd.read_parquet(
        REPO / "data/clean/gas-ofo-events/CAISO/gas-ofo-events.parquet"
    )
    low = ofo[ofo["side"] == "low"]
    lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    )

    out: dict[str, object] = {
        "trigger": "SoCalGas low OFO, any stage, waived INCLUDED (PRECOMMIT §2, frozen)",
        "tail_threshold_usd_mwh": TAIL_THRESHOLD,
        "years": {},
    }
    for year in YEARS:
        s = lmp[lmp["year"] == year].sort_values("hour").reset_index(drop=True)
        stamps = local_stamps(year, len(s))
        tail = s["rt"] > TAIL_THRESHOLD

        days = set(
            low.loc[low["gas_day"].dt.year.isin({year, year - 1}), "gas_day"].dt.date
        )
        # gas day D covers [D 07:00, D+1 07:00) local -> the gas day OWNING an
        # operating hour is that hour's date shifted back by 7 h.
        owning_gas_day = (stamps - pd.Timedelta(hours=GAS_DAY_START_HOUR)).date
        on_gas_day = pd.Series([d in days for d in owning_gas_day])
        # the naive (wrong) mapping, computed only to show the offset matters
        on_cal_day = pd.Series([d in days for d in stamps.date])

        n_tail = int(tail.sum())
        # per-day breakdown, so the coverage number is auditable rather than
        # asserted: which measured tail days are qualifying gas days and which
        # are not.
        per_day = pd.DataFrame({"gas_day": owning_gas_day, "tail": tail.to_numpy()})
        counts = per_day[per_day["tail"]].groupby("gas_day").size()
        tail_days = {
            str(day): {"tail_hours": int(n), "qualifying": day in days}
            for day, n in counts.items()
        }
        out["years"][str(year)] = {
            "low_ofo_days_in_year": int(low["gas_day"].dt.year.eq(year).sum()),
            "tail_hours_actual_rt": n_tail,
            "tail_hours_on_qualifying_gas_day": int((tail & on_gas_day).sum()),
            "tail_hours_on_qualifying_calendar_day": int((tail & on_cal_day).sum()),
            "coverage_frac": round(float((tail & on_gas_day).sum()) / n_tail, 4)
            if n_tail
            else None,
            "c3c_hours_required": None,  # filled below from the rubric band
            "all_hours_on_qualifying_gas_day": int(on_gas_day.sum()),
            "trigger_duty_frac": round(float(on_gas_day.sum()) / len(s), 4),
            "tail_days": tail_days,
        }

    # C3c requirement: model count must land in [0.5x, 2x] of the RT actual,
    # or within TAIL_SMALL_COUNT=10 hours when the actual is under 10 h.
    for year, need in (("2023", 24), ("2024", 18), ("2025", 0)):
        out["years"][year]["c3c_hours_required"] = need

    print(json.dumps(out, indent=2))
    dest = REPO / "results/calibration/_caiso228_d0_coverage.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main()

"""miso-222 phase 0 — HOW BIG IS THE DECLARED EMERGENCY RANGE, and can it close the gap?

Zero-solve, zero-LP. Sizes the object of the ELMP / emergency-supply owner ask
(miso-219 sections 5 and 9) directly from MISO's own published conduct corpus.

**THE PREMISE CORRECTION THIS PROBE EXISTS TO MAKE.** miso-219 filed the ELMP
re-basing to owner court on the ground that *"the emergency-range MW is neither
already-measured nor already-registered in this repo"*. The second half stands —
there is no ``ScenarioConfig`` field and no matrix row. **The first half is wrong.**
MISO publishes ``Economic Max`` and ``Emergency Max`` per masked unit per operating
hour in the Market Reports conduct corpus; this repo already fetches it
(``scripts/data/fetch_miso_energy_offers.py``), already curates it
(``scripts/data/curate_miso_energy_offers.py``) and already carries it in the data
contract as ``energy-offers`` with the fields ``emergency_max_mw`` /
``emergency_min_mw`` / ``emergency_flag``. The corpus landed at miso-145
(2026-08-09), BEFORE miso-219 filed. So the ask is not "may we go acquire a new
measurement" — it is "may we use one we already have, given its limits".

**The declared emergency range** is ``max(0, Emergency Max - Economic Max)`` summed
over units flagged available, at the object's own hours. That is the MW a
participant will produce only under an emergency instruction, which MISO prices at
the ELMP Event Step floors — the block the model's ``maxgen_emergency_tier_pricing``
should be keyed to instead of load slack (which is 0.000 MWh in all 45 object hours,
so the armed and correctly-clocked tier contributes exactly $0).

**Read against miso-222's removal sizing** (``_miso222_removal_sizing.json``), this
answers the question the owner actually has to rule on: is the emergency range of a
magnitude that could move C3c at all?

**LIMITS, declared here and not discovered later.** Unit identity is masked and the
corpus publishes **no fuel or technology attribute**; the offer-side class bridge was
built and REFUTED at miso-138, so no class crosswalk may be asserted from it.
Locational information is ``Region`` in {North, Central, South}, a MISO market region
and **not** a model zone. Any mechanism built on this input is therefore
fleet-aggregate or region-aggregate — never per-unit and never per-model-zone.

**Rule 13 [R-MEASURED].** Only OFFER columns are read. The award columns (RT
``Cleared MW1``-``Cleared MW12``, ``Target MW Reduction``) are dispatch OUTCOMES —
the answer class — and are dropped before anything else touches the frame, the same
discipline ``curate_miso_energy_offers.OUTCOME_COLS`` enforces.

**Clock.** The reports are published on fixed EST (UTC-5) year round, stamped
interval-BEGINNING (``Mkthour Begin (EST)``). The model runs on ``Etc/GMT+6`` (fixed
CST), also interval-beginning, so ``CST hour = EST hour - 1`` with no DST handling on
either side. An object hour printed ``HEk`` is model hour-of-day ``k - 1``.

Rule 22 [R-HOLDOUT] — 2023/2024/2025 only. Nothing is minted; no mechanism is armed.

Usage::

    python3 scripts/probes/_miso222_emergency_range_phase0.py
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

from _miso221_peak_shape_phase0 import _r, _stamp, object_hours  # noqa: E402

OUT = REPO / "results/calibration/_miso222_emergency_range.json"
RT_DIR = REPO / "data/raw/miso-energy-offers/rt"
YEARS = (2023, 2024, 2025)

#: Dispatch OUTCOMES — dropped before any other column is touched (rule 13).
OUTCOME_COLS: tuple[str, ...] = ("MW", "Target MW Reduction") + tuple(
    f"Cleared MW{i}" for i in range(1, 13)
)
#: EST (published) minus CST (model clock).
EST_MINUS_CST_H = 1


def _read_day(path: Path) -> pd.DataFrame:
    """Read one operating day's offer file, outcomes dropped first (rule 13)."""
    with zipfile.ZipFile(path) as z:
        name = z.namelist()[0]
        raw = pd.read_csv(io.BytesIO(z.read(name)), low_memory=False)
    raw = raw.drop(columns=[c for c in OUTCOME_COLS if c in raw.columns])
    leaked = [c for c in OUTCOME_COLS if c in raw.columns]
    assert not leaked, f"rule 13: outcome columns survived the drop: {leaked}"
    ts = pd.to_datetime(raw["Mkthour Begin (EST)"])
    out = pd.DataFrame(
        {
            "month": ts.dt.month.to_numpy(),
            "day": ts.dt.day.to_numpy(),
            "cst_h": (ts.dt.hour - EST_MINUS_CST_H).to_numpy(),
            "unit": raw["Unit Code"].to_numpy(),
            "region": raw["Region"].astype(str).to_numpy(),
            "available": raw["Unit Available Flag"]
            .astype(str)
            .str.upper()
            .isin(["1", "Y", "TRUE", "T"])
            .to_numpy(),
            "eco_max": pd.to_numeric(raw["Economic Max"], errors="coerce").to_numpy(),
            "emer_max": pd.to_numeric(raw["Emergency Max"], errors="coerce").to_numpy(),
        }
    )
    return out


def _object_keys(year: int) -> dict[tuple[int, int, int], str]:
    """``{(month, day, cst_hour): stamp}`` for the year's 15 object hours."""
    keys = {}
    for h in object_hours(year):
        s = _stamp(h)  # 'MM-DD HEkk' on the model's own clock
        mm, rest = s.split("-", 1)
        dd, he = rest.split(" HE")
        keys[(int(mm), int(dd), int(he) - 1)] = s
    return keys


def analyse_year(year: int) -> dict:
    """Declared emergency range at the year's object hours, and its context."""
    files = sorted(RT_DIR.glob(f"{year}*_rt_co.zip"))
    if not files:
        return {"year": year, "error": "no RT offer files fetched for this year"}
    frames = [_read_day(f) for f in files]
    d = pd.concat(frames, ignore_index=True)
    d["range"] = np.clip(d["emer_max"] - d["eco_max"], 0.0, None)
    av = d[d["available"]]

    keys = _object_keys(year)
    rows = []
    for (mm, dd, ch), stamp in sorted(keys.items()):
        sel = av[(av["month"] == mm) & (av["day"] == dd) & (av["cst_h"] == ch)]
        if sel.empty:
            rows.append({"stamp": stamp, "covered": False})
            continue
        rows.append(
            {
                "stamp": stamp,
                "covered": True,
                "units": int(sel["unit"].nunique()),
                "eco_max_gw": _r(float(sel["eco_max"].sum()) / 1000, 3),
                "emer_max_gw": _r(float(sel["emer_max"].sum()) / 1000, 3),
                "emergency_range_mw": _r(float(sel["range"].sum()), 0),
                "units_offering_range": int((sel["range"] > 0.5).sum()),
                "by_region_mw": {
                    str(k): _r(float(v), 0)
                    for k, v in sel.groupby("region")["range"].sum().items()
                },
            }
        )
    covered = [r for r in rows if r.get("covered")]
    per_hour = av.groupby(["month", "day", "cst_h"])["range"].sum()
    return {
        "year": year,
        "files_read": len(files),
        "months_covered": sorted(set(int(m) for m in d["month"].unique())),
        "masked_units": int(d["unit"].nunique()),
        "object_hours": rows,
        "object_hours_covered": len(covered),
        "emergency_range_mw_at_object_hours": {
            "mean": _r(float(np.mean([r["emergency_range_mw"] for r in covered])), 0)
            if covered
            else None,
            "min": _r(float(np.min([r["emergency_range_mw"] for r in covered])), 0)
            if covered
            else None,
            "max": _r(float(np.max([r["emergency_range_mw"] for r in covered])), 0)
            if covered
            else None,
        },
        "emergency_range_mw_all_jun_jul_hours": {
            "mean": _r(float(per_hour.mean()), 0),
            "p95": _r(float(per_hour.quantile(0.95)), 0),
            "max": _r(float(per_hour.max()), 0),
        },
    }


def main() -> int:
    """Measure every year and write the record."""
    rec = {
        "probe": "miso-222 phase 0 - the declared emergency range, from MISO's own conduct corpus",
        "source": "data/raw/miso-energy-offers/rt (MISO Market Reports *_rt_co, ~90-day lag)",
        "solved": False,
        "premise_correction": (
            "miso-219 section 9 filed the ELMP re-basing on the ground that the "
            "emergency-range MW is 'neither already-measured nor already-registered'. "
            "The registered half stands; the MEASURED half is wrong - MISO publishes "
            "Economic Max and Emergency Max per masked unit-hour, this repo fetches and "
            "curates them, and the data contract carries them as energy-offers."
            "emergency_max_mw / emergency_min_mw / emergency_flag (landed miso-145, "
            "2026-08-09, before miso-219 filed)."
        ),
        "limits": [
            "unit identity is MASKED; no fuel or technology attribute is published, and "
            "the offer-side class bridge was REFUTED at miso-138 - no class crosswalk",
            "location is Region in {North, Central, South}, a MISO market region, NOT a "
            "model zone",
            "so any mechanism built on this input is fleet- or region-aggregate, never "
            "per-unit and never per-model-zone",
            "coverage is Jun-Jul here (the object's months); the landed corpus is JJA",
        ],
        "rule_13": (
            "only OFFER columns are read; the award columns (Cleared MW1-12, Target MW "
            "Reduction) are dispatch OUTCOMES and are dropped before anything else "
            "touches the frame"
        ),
        "clock": "published fixed EST interval-beginning; model is fixed CST; CST = EST - 1 h",
        "by_year": {},
    }
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        print(f"  {y} done", flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=2))
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

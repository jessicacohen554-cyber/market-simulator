"""R-CAISO-10 Object 1 (ZERO LP): why the RA bridge does not hold midday CC_REGULAR.

R-CAISO-9 split the keeper's 2025 midday (h9-16) CC_REGULAR deficit per plant into
"CEMS on, model off" (-947 MW), "both on, loaded lower" (-668 MW) and "model over"
(+793 MW). This probe classifies the CEMS-on / model-off plant-hours by what the
model did with that plant on the SAME DAY, which is what the RA must-offer bridge
(``model.commitment.caiso_ra_mustoffer_min_gen``) keys on: it floors only a gap
between a run BEFORE and a run AFTER the idle hours.

Buckets (plant-hour, midday, CEMS on > 0.5 MW, model plant output <= 0.5 MW):

* ``UNAVAIL``   model available capacity for the plant is 0 in that hour (outage)
* ``OFF_DAY``   the model runs the plant in NO hour of that day
* ``EVE_ONLY``  runs in h17-23 but not h0-8 (no "before" run -> no bridge)
* ``MORN_ONLY`` runs in h0-8 but not h17-23 (no "after" run -> no bridge)
* ``BOTH``      runs before AND after, and the gap is still unfloored

Also reports, for the same MW, whether CEMS shows the plant on through the whole
day (all 24 h) -- a continuously-committed plant, the conduct the bridge exists to
represent -- and the RA floor (mechanism 7) held midday on CC_REGULAR per year.

Inputs: the keeper's benchmark CEMS (``calibration_verdict.load_artifacts``) and the
per-year legs of the keeper, extracted locally from their shard commits with
``git archive`` (gitignored; provenance SHAs in RESULT-r-caiso-9 §Retrievability).
The model side is P1 (P0 is not persisted), so ``BOTH``/``EVE_ONLY`` describe the
P1 pattern, which the bridge's own P0 pattern approximates.

Writes ``results/calibration/_rcaiso10/object1_census.json``.

Usage::

    PYTHONPATH=.:src:scripts python3 scripts/probes/_rcaiso10_object1_census.py
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts", "scripts/probes"]
import calibration_verdict as cv  # noqa: E402

KEEPER = "2026-09-28-caiso-r9-sd-floor"
LEG = "results/calibration/rcaiso9_A_{y}"
OUT = Path("results/calibration/_rcaiso10/object1_census.json")
T = 8760
HOD = np.arange(T) % 24
DAY = np.arange(T) // 24
MID = (HOD >= 9) & (HOD <= 16)
ON = 0.5  # MW, same threshold as the R-CAISO-9 split
MECH_RA_MUSTOFFER = 7  # data.floor_mechanisms.MECH_RA_MUSTOFFER


def _cf(b64: str, cap: float) -> np.ndarray:
    return np.frombuffer(base64.b64decode(b64)[:T], np.uint8) * cap / 100.0


def census(year: int, art: dict) -> dict:
    """Classify one year's midday CEMS-on / model-off CC_REGULAR MW."""
    yb = art["bench"][year]
    leg = Path(LEG.format(y=year))
    u = pd.read_parquet(
        leg / f"hourly/unit_hourly_{year}.parquet",
        columns=["plant_code", "plant_group", "hour", "mw", "cap_mw"],
        filters=[("plant_group", "==", "CC_REGULAR")],
    )
    g = u.groupby(["plant_code", "hour"])[["mw", "cap_mw"]].sum()
    fl = np.load(leg / f"floors/{year}_P1.npz")
    ra = (fl["mechanism"] == MECH_RA_MUSTOFFER) & (
        fl["plant_group"][:, None] == "CC_REGULAR"
    )
    ra_mid_mw = float(np.where(ra, fl["min_gen"], 0).sum(axis=0)[MID].mean())

    buckets = dict.fromkeys(
        ("UNAVAIL", "OFF_DAY", "EVE_ONLY", "MORN_ONLY", "BOTH"), 0.0
    )
    cems_allday = 0.0
    total_act_mid = 0.0
    n_plants = 0
    for code, bp in yb["plants"].items():
        if bp.get("group") != "CC_REGULAR" or bp.get("nodata") or not bp.get("campd"):
            continue
        cap = float(bp.get("npl") or 0.0)
        if cap <= 0:
            continue
        a = _cf(bp["campd"], cap)
        total_act_mid += float(a[MID].sum())
        try:
            pg = g.loc[int(str(code).split(":")[0])]
        except KeyError:
            continue  # plant not in the model's CC_REGULAR set
        n_plants += 1
        m = pg["mw"].reindex(range(T)).fillna(0).to_numpy()
        c = pg["cap_mw"].reindex(range(T)).fillna(0).to_numpy()
        on_m = (m > ON).reshape(-1, 24)
        on_a = (a > ON).reshape(-1, 24)
        morn = on_m[:, :9].any(1)
        eve = on_m[:, 17:].any(1)
        anyd = on_m.any(1)
        allday_a = on_a.all(1)
        sel = MID & (a > ON) & (m <= ON)
        for h in np.flatnonzero(sel):
            d = DAY[h]
            if c[h] <= ON:
                k = "UNAVAIL"
            elif not anyd[d]:
                k = "OFF_DAY"
            elif morn[d] and eve[d]:
                k = "BOTH"
            elif eve[d]:
                k = "EVE_ONLY"
            else:
                k = "MORN_ONLY"
            buckets[k] += a[h]
            if allday_a[d]:
                cems_allday += a[h]
    nmid = MID.sum()
    total = sum(buckets.values())
    return {
        "plants": n_plants,
        "cems_cc_regular_mid_mw": round(total_act_mid / nmid),
        "cems_on_model_off_mid_mw": round(total / nmid),
        "by_model_day_pattern_mw": {k: round(v / nmid) for k, v in buckets.items()},
        "share": {k: round(v / total, 3) for k, v in buckets.items()} if total else {},
        "of_which_cems_on_all_24h_mw": round(cems_allday / nmid),
        "ra_floor_cc_regular_mid_mw": round(ra_mid_mw),
    }


def main() -> None:
    """Run the census for every keeper span year and write the JSON."""
    art = cv.load_artifacts(KEEPER)
    out = {"keeper": KEEPER, "threshold_mw": ON, "years": {}}
    for y in (2022, 2023, 2024, 2025):
        out["years"][str(y)] = census(y, art)
        print(y, json.dumps(out["years"][str(y)]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    main()

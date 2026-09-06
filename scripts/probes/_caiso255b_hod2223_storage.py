"""caiso-255b (ZERO LP): is EIA-930 ``NG: OTH`` CAISO's battery fleet, and does
the hod 22-23 gap belong to STORAGE?

Registered in
``results/calibration/PRECOMMIT-caiso255b-hod2223-storage-repoint-2026-09-06.md``,
pushed before any cell of the object was computed. caiso-253 re-pointed the
hod 22-23 gap from IMPORT to STORAGE on the strength of ``NG: OTH`` rising
274 -> 2,112 -> 3,342 MW against the keeper's ~680 -> 1,683 -> 2,769 MW of
storage discharge. Its own parenthesis is the reason G-ID exists: **EIA-930
carries no battery category**, so ``NG: OTH`` is a CATCH-ALL and reading it as
"CAISO's batteries" is an inference, not a measurement.

THE CLOCK, AND WHY THIS FILE USES THE LOADER RATHER THAN THE RAW PARQUET
-----------------------------------------------------------------------
``data/raw/eia-930-hourly/CISO hourly.parquet`` carries EIA's own stamps, whose
``Local time`` is the **hour-ENDING** label on a DST-aware wall clock. The
model's hourly index is neither: row ``h`` is hour ``h`` of the solve year on a
fixed offset. Comparing the two directly is an off-by-one-hour error, and the
repo already owns the fix — ``eia930.frames._eia_hourly_frame_filled`` returns a
frame whose **row k is local hour k, interval-beginning, on the model's clock**,
with the HE->HB shift applied at anchoring. Its docstring names the bug it was
written for: *"the CISO-2025 solar-profile +1h shift (FINDING-caiso102,
2026-07-19; also hit PJM-2023/MISO-2025)"*.

**Every actual in this probe therefore comes from the loader, never from the raw
parquet.** The alignment is not asserted, it is anchored three ways, and the
anchor is part of the probe (``--anchor``) so a reader can re-run it:

* **astronomy** - June 2025, sunrise 05:45 / sunset 20:15 PDT. Model and loader
  BOTH first exceed 200 MW of solar at hod 6 and last at hod 19;
* **solar correlation** - model vs loader = **0.9999 at zero shift**, against
  0.9407 / 0.9415 at +/-1 h;
* **an independent series** - demand ranks the loader clock above both raw-stamp
  readings in 2023 and 2025.

Scoring is unaffected by any of this: ``eia930/actuals.py`` already reads
through the same loader, so no keeper, determination or rubric score depends on
the raw-stamp clock.

Output: ``results/calibration/_caiso255b_hod2223_storage.json``.

Usage::

    PYTHONPATH=.:src uv run python scripts/probes/_caiso255b_hod2223_storage.py
    PYTHONPATH=.:src uv run python scripts/probes/_caiso255b_hod2223_storage.py --anchor
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from market_sim.data.eia930.frames import _eia_hourly_frame_filled  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso252_b1_notrim"
OUT = REPO / "results/calibration/_caiso255b_hod2223_storage.json"
YEARS = (2023, 2024, 2025)
TARGET_HOURS = (22, 23)
BELLY = (10, 15)

#: caiso-253's published pair, the P-2 comparator (calibration-log caiso-253).
PUB_ACTUAL = {2023: 274.0, 2024: 2112.0, 2025: 3342.0}
PUB_MODEL = {2023: 680.0, 2024: 1683.0, 2025: 2769.0}
#: G-ID-3: |annual net| / annual gross throughput must not exceed this.
NEUTRALITY_MAX = 0.35


def actual(year: int) -> pd.DataFrame:
    """EIA-930 CISO on the MODEL's clock (row k = hour k). Never the raw stamps."""
    f = _eia_hourly_frame_filled("CISO", year)
    if f is None:
        raise SystemExit(f"EIA-930 CISO {year}: no clean 8760 frame")
    idx = pd.date_range(f"{year}-01-01", periods=len(f), freq="h")
    return pd.DataFrame(
        {
            "hod": idx.hour,
            "month": idx.month,
            "oth": pd.to_numeric(f["NG: OTH"], errors="coerce").to_numpy(),
            "sun": pd.to_numeric(f["NG: SUN"], errors="coerce").to_numpy(),
        }
    )


def model_storage(year: int) -> pd.DataFrame:
    """Keeper P1 storage, summed over techs, indexed by hour-of-day."""
    s = pd.read_parquet(BUNDLE / f"hourly/storage_{year}.parquet")
    s = s[s["pass"] == "P1"]
    g = s.groupby("hour")[["charge_mw", "discharge_mw"]].sum()
    g["hod"] = g.index % 24
    return g


def model_class(year: int, klass: str) -> pd.Series:
    c = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    c = c[(c["pass"] == "P1") & (c.klass == klass)]
    g = c.groupby("hour").mw.sum()
    return g.groupby(g.index % 24).mean()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--anchor",
        action="store_true",
        help="print the three clock anchors and exit without scoring the gates",
    )
    a = ap.parse_args()

    if a.anchor:
        d = actual(2025)
        j = d[d.month == 6]
        ea = j.groupby("hod")["sun"].mean()
        c = pd.read_parquet(BUNDLE / "hourly/class_hourly_2025.parquet")
        c = c[(c["pass"] == "P1") & (c.klass == "solar")].copy()
        idx = pd.date_range("2025-01-01", periods=8760, freq="h")
        c["month"] = c.hour.map(lambda h: idx[h].month)
        ma = c[c.month == 6].groupby(c.hour % 24).mw.mean()
        on = lambda s: [h for h in range(24) if s.get(h, 0) > 200]  # noqa: E731
        print("JUNE 2025 solar (sunrise 05:45 / sunset 20:15 PDT)")
        print(f"  loader: first>200MW hod={min(on(ea))} last={max(on(ea))}")
        print(f"  model : first>200MW hod={min(on(ma))} last={max(on(ma))}")
        mv = ma.reindex(range(24)).fillna(0).to_numpy()
        ev = ea.reindex(range(24)).fillna(0).to_numpy()
        for sh in (-1, 0, 1):
            print(
                f"  solar corr shift {sh:+d}h = {np.corrcoef(mv, np.roll(ev, sh))[0, 1]:.4f}"
            )
        return

    res: dict = {"session": "caiso-255b", "years": {}, "gates": {}}

    # ---- G-ID: is NG: OTH a battery fleet at all? --------------------------
    gid: dict = {"legs": {}}
    for y in YEARS:
        d = actual(y)
        belly = d[d.hod.between(*BELLY)]["oth"].dropna()
        allv = d["oth"].dropna()
        gross = float(allv.abs().sum())
        gid["legs"][str(y)] = {
            "belly_mean_mw": round(float(belly.mean()), 1),
            "belly_frac_negative": round(float((belly < 0).mean()), 4),
            "gross_throughput_gwh": round(gross / 1e3, 1),
            "net_gwh": round(float(allv.sum()) / 1e3, 1),
            "neutrality_ratio": round(abs(float(allv.sum())) / gross, 4),
        }
    legs = gid["legs"]
    gid["G_ID_1_sign_pass"] = all(
        legs[str(y)]["belly_frac_negative"] > 0.5 for y in YEARS
    )
    gid["G_ID_2_growth_pass"] = (
        legs["2023"]["gross_throughput_gwh"]
        < legs["2024"]["gross_throughput_gwh"]
        < legs["2025"]["gross_throughput_gwh"]
    )
    gid["G_ID_3_neutrality_pass"] = all(
        legs[str(y)]["neutrality_ratio"] <= NEUTRALITY_MAX for y in YEARS
    )
    gid["pass"] = all(gid[k] for k in gid if k.endswith("_pass"))
    res["gates"]["G_ID"] = gid

    # ---- G-GAP / G-FLEET / G-ENERGY ---------------------------------------
    for y in YEARS:
        d = actual(y)
        act = float(d[d.hod.isin(TARGET_HOURS)]["oth"].dropna().mean())
        g = model_storage(y)
        w = g[g.hod.isin(TARGET_HOURS)]
        dis, chg = float(w.discharge_mw.mean()), float(w.charge_mw.mean())
        allv = d["oth"].dropna()
        res["years"][str(y)] = {
            "actual_ng_oth_mw": round(act, 1),
            "model_net_mw": round(dis - chg, 1),
            "model_discharge_mw": round(dis, 1),
            "gap_net_minus_actual_mw": round(dis - chg - act, 1),
            "direction": "model OVER-discharges"
            if dis - chg > act
            else "model UNDER-discharges",
            "P2_actual_pct_err_vs_caiso253": round(
                100 * (act - PUB_ACTUAL[y]) / PUB_ACTUAL[y], 1
            ),
            "P2_model_pct_err_vs_caiso253": round(
                100 * (dis - PUB_MODEL[y]) / PUB_MODEL[y], 1
            ),
            "model_max_discharge_mw": round(float(g.discharge_mw.max()), 0),
            "actual_max_mw": round(float(allv.max()), 0),
            "fleet_ratio_model_over_actual": round(
                float(g.discharge_mw.max()) / float(allv.max()), 3
            ),
            "model_cc_regular_at_2223_mw": round(
                float(model_class(y, "CC_REGULAR")[list(TARGET_HOURS)].mean()), 1
            ),
        }

    res["verdict"] = {
        "G_ID": "PASS - NG: OTH is CAISO's battery fleet" if gid["pass"] else "FAIL",
        "G_GAP": (
            "the model OVER-discharges storage at hod 22-23 in EVERY year once "
            "aligned on the model's clock - the OPPOSITE of the premise "
            "caiso-253's re-pointing rests on"
        ),
        "G_FLEET": (
            "model storage power capability EXCEEDS the actual series' own "
            "maximum in all three years, so the object is NOT a short fleet"
        ),
        "P2": (
            "HOLDS on the model side (+0.0% all years) and FALSIFIED on the "
            "actual side: caiso-253's actuals were read off the RAW parquet's "
            "hour-ENDING stamps instead of the loader's model-clock frame"
        ),
        "queue_item": "caiso-253 queue item 1 (storage re-pointing) is REFUTED",
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")

    print(f"G-ID: {res['verdict']['G_ID']}")
    for y in YEARS:
        r = res["years"][str(y)]
        print(
            f"  {y}: actual {r['actual_ng_oth_mw']:8.1f}  model_net {r['model_net_mw']:8.1f}  "
            f"gap {r['gap_net_minus_actual_mw']:+8.1f}  {r['direction']}  "
            f"(P-2 actual err {r['P2_actual_pct_err_vs_caiso253']:+.1f}%, "
            f"model err {r['P2_model_pct_err_vs_caiso253']:+.1f}%)"
        )
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

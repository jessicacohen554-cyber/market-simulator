"""miso-156 Phase 1 — the ``ramp_envelopes`` PRE-CHECK for MISO, on measured data.

**NOT PRE-REGISTERED as a statistic** (PREREG section 10) — it is the
identification step branch **B-IDENT** authorizes: *"Phase 1 proceeds to the
identity queue (``measured_ramp_capability`` / ``ramp_envelopes``) ... or names
it and stops if no admissible identification exists in-session."* Every number
here is labelled NOT PRE-REGISTERED where it is reported, with its
counter-measurement and its full magnitude.

WHY THIS QUESTION. miso-156 Phase 0 put MISO's C3a miss on the marginal-unit
IDENTITY channel (D1 = +11.97 $/MWh, 169 % of the 2025 annual gap) and showed the
CLASS is already right at the peak — ``CT_PEAKER`` is the model's marginal class
in 74.1 % of top-200 zone-hours against 69.0 % implied by the market — while the
model's implied heat rate at those hours is **11.93** against the market's
**28.83**. The model's stack does not climb in the tightest hours. A ramp
envelope is the one queued mechanism that makes a deterministic LP climb without
touching an offer level: constraining hour-to-hour movement forces costlier units
to be held ahead of the peak.

THE PJM PRECEDENT AND ITS TRANSFER BOUND (rule 25 ``[R-ISO-SCOPE]``). PJM armed
``ramp_limits=True`` at pjm-140 on a rule-14 physics identification — *the model
out-ramps the real PJM fleet 1.4-1.7x at the p99 1-h move* — NOT on fit. That
verdict transfers nothing: MISO enters as ``U`` and must be identified from
MISO's own data. This probe runs the MISO equivalent of PJM's pre-check.

THE MEASUREMENT. Model 1-h fleet ramp = the hour-to-hour change in total thermal
dispatch from the keeper's own committed ``hourly/class_hourly_<year>.parquet``
(P1). Measured 1-h fleet ramp = the same quantity from EIA-930's MISO
fuel-type series (``data/raw/MISO_fueltype.parquet``), restricted to the same
thermal fuels. Reported as the ratio of |1-h move| at p50/p90/p99 and at the
annual max, plus the Jun+Jul window where the C3a miss lives.

KILL RULE, fixed before the numbers are read: if MISO's model does **NOT**
out-ramp the measured fleet at the p99 1-h move in at least 2 of 3 years, the
lever is **INERT for MISO** and this session says so — a ramp envelope that binds
nothing cannot move a marginal unit, and arming it would be a mechanism chosen
for its name rather than its physics.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds neither marker.

Usage::

    PYTHONPATH=$PWD:$PWD/src .venv/bin/python \\
        scripts/probes/_miso156_ramp_precheck.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (str(REPO), str(REPO / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BUNDLE = REPO / "results/calibration/miso148_basis_B"
OUT = REPO / "results/calibration/_miso156_ramp_precheck.json"
YEARS = (2023, 2024, 2025)

# The model reporting classes that are dispatchable thermal, i.e. the fleet a
# ramp envelope would bind. VRE, hydro and storage are excluded on BOTH sides.
THERMAL = (
    "CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP",
    "COAL_PRB", "COAL_BIT", "COAL_LIGNITE", "COAL_SUB", "COAL_WASTE", "OIL",
)
# EIA-930 fuel-type labels for the same physical fleet. NUCLEAR is excluded on
# both sides (baseload, never ramp-bound); the model carries it separately.
E930_THERMAL = ("NG", "COL", "OTH")  # MISO's EIA-930 has no OIL row; oil sits inside OTH

KILL_P99_MIN_RATIO = 1.0     # model must EXCEED measured at p99 to be admissible
KILL_YEARS = 2               # ... in at least 2 of 3 years


def model_thermal_mw(year: int) -> np.ndarray:
    """Return the (8760,) model P1 thermal dispatch, from committed artifacts."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[(ch["pass"] == "P1") & (ch["klass"].isin(THERMAL))]
    out = ch.groupby("hour")["mw"].sum().reindex(range(8760), fill_value=0.0)
    return out.to_numpy(float)


def measured_thermal_mw(year: int) -> tuple[np.ndarray, dict]:
    """Return the (8760,) measured MISO thermal generation, EIA-930 fuel type.

    Counter-measurement (reported, not assumed): the fuel labels actually present
    and the share of hours with a complete record are returned alongside, so a
    silently-short series cannot masquerade as a flat fleet.
    """
    d = pd.read_parquet(REPO / "data/raw/MISO_fueltype.parquet")
    cols = {c.lower(): c for c in d.columns}
    tcol = cols.get("period") or cols.get("timestamp") or list(d.columns)[0]
    fcol = cols.get("fueltype") or cols.get("fuel") or list(d.columns)[1]
    vcol = cols.get("value") or cols.get("mw") or list(d.columns)[-1]
    d = d[[tcol, fcol, vcol]].copy()
    d.columns = ["ts", "fuel", "mw"]
    d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce")
    labels = sorted(str(x) for x in d["fuel"].dropna().unique())
    d = d[d["fuel"].astype(str).isin(E930_THERMAL)]
    # Fixed Central standard time, the model's own clock (derive_miso_hub_lmp).
    loc = d["ts"].dt.tz_convert("Etc/GMT+6").dt.tz_localize(None)
    d = d.assign(y=loc.dt.year, mo=loc.dt.month, day=loc.dt.day, hh=loc.dt.hour)
    d = d[(d["y"] == year) & ~((d["mo"] == 2) & (d["day"] == 29))]
    dim = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    start = np.concatenate(([0], np.cumsum(dim) * 24))[:12]
    hour = start[d["mo"].to_numpy() - 1] + (d["day"].to_numpy() - 1) * 24 + d["hh"].to_numpy()
    s = pd.Series(d["mw"].to_numpy(float)).groupby(hour).sum()
    out = s.reindex(range(8760)).to_numpy(float)
    diag = {
        "e930_labels_present": labels,
        "e930_labels_used": [x for x in E930_THERMAL if x in labels],
        "hours_with_record": int(np.isfinite(out).sum()),
        "annual_twh": float(np.nansum(out) / 1e6),
    }
    return out, diag


def ramp_stats(mw: np.ndarray, mask: np.ndarray | None = None) -> dict:
    """|1-h move| quantiles, on hours where both endpoints are present."""
    d = np.abs(np.diff(mw))
    good = np.isfinite(d)
    if mask is not None:
        good &= mask[1:]
    v = d[good]
    if v.size == 0:
        return {"n": 0}
    return {
        "n": int(v.size),
        "p50": float(np.percentile(v, 50)),
        "p90": float(np.percentile(v, 90)),
        "p99": float(np.percentile(v, 99)),
        "max": float(v.max()),
    }


def main() -> dict:
    out = {
        "prereg": "PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md",
        "label": "NOT PRE-REGISTERED — the B-IDENT identification step",
        "kill_rule": (
            "model p99 1-h move must EXCEED measured in >=2 of 3 years, else "
            "ramp_envelopes is INERT for MISO"
        ),
        "years": {},
    }
    jj = np.zeros(8760, dtype=bool)
    dim = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    start = np.concatenate(([0], np.cumsum(dim) * 24))[:12]
    jj[start[5]: start[7]] = True

    exceed = 0
    for year in YEARS:
        m = model_thermal_mw(year)
        a, diag = measured_thermal_mw(year)
        both = np.isfinite(m) & np.isfinite(a)
        rm, ra = ramp_stats(np.where(both, m, np.nan)), ramp_stats(np.where(both, a, np.nan))
        rmj = ramp_stats(np.where(both, m, np.nan), jj)
        raj = ramp_stats(np.where(both, a, np.nan), jj)
        ratio = {k: (rm[k] / ra[k] if ra.get(k) else None) for k in ("p50", "p90", "p99", "max")}
        ratio_jj = {k: (rmj[k] / raj[k] if raj.get(k) else None) for k in ("p50", "p90", "p99", "max")}
        if (ratio["p99"] or 0) > KILL_P99_MIN_RATIO:
            exceed += 1
        out["years"][str(year)] = {
            "e930": diag,
            "model_annual_twh": float(np.nansum(m) / 1e6),
            "model_ramp": rm, "measured_ramp": ra, "ratio": ratio,
            "model_ramp_junjul": rmj, "measured_ramp_junjul": raj,
            "ratio_junjul": ratio_jj,
        }
        print(f"[{year}] 1-h |move| MW   model p50/p90/p99/max "
              f"{rm['p50']:.0f}/{rm['p90']:.0f}/{rm['p99']:.0f}/{rm['max']:.0f}   "
              f"measured {ra['p50']:.0f}/{ra['p90']:.0f}/{ra['p99']:.0f}/{ra['max']:.0f}   "
              f"ratio {ratio['p50']:.2f}/{ratio['p90']:.2f}/{ratio['p99']:.2f}/{ratio['max']:.2f}"
              f"   JunJul p99 ratio {ratio_jj['p99']:.2f}", flush=True)
    out["years_model_exceeds_at_p99"] = exceed
    out["verdict"] = (
        "ADMISSIBLE — the model out-ramps the measured fleet at p99"
        if exceed >= KILL_YEARS
        else "INERT FOR MISO — the model does NOT out-ramp the measured fleet at p99"
    )
    print(out["verdict"], f"({exceed} of 3 years)")
    OUT.write_text(json.dumps(out, indent=1))
    print(f"wrote {OUT}")
    return out


if __name__ == "__main__":
    main()

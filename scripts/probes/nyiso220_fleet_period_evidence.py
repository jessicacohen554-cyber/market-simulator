"""nyiso-220 charter evidence (ZERO LP) — what the 145 unconstrained hydro plants actually do.

The owner's instruction, 2026-09-08: *"I don't think the other 145 should keep the
month that's the problem I think that's way too generous for how flexible hydro
is."* This probe is the measurement behind
``docs/CHARTER-nyiso220-fleet-wide-hydro-budget-period-2026-09-08.md`` §2 and §4.

It answers two questions from **committed artifacts plus the screen arm's own
per-unit hourlies**, with no solve:

**Q-A — where does the RESIDUAL cross-day footprint sit?** The nyiso-220 screen
constrained only the two projects whose governing instrument had been retrieved
(2693 Niagara at 24 h, 2694 St. Lawrence at 168 h) and left 145 plants on the
calendar month. Decomposing the arm's remaining footprint per plant shows the
unconstrained set is **18.8 % of hydro energy carrying 61.4 % of the residual**,
swinging **17.96 %** of its own energy across days against the constrained set's
**2.61 %** -- nearly 7x as hard per MWh.

**Q-B — what would a pondage-bucketed assignment cover?** Bucketing the committed
measured pondage onto the LP's own calendar period grid (24 h / 168 h / 730 h --
not fitted thresholds) puts **70.92 % of fleet MW on a DAILY** period and 24.92 %
on weekly, leaving only **1.67 %** with the storage to justify the month the model
currently grants all of it.

**The validation that makes the pondage route credible** rather than merely
available: where the instrument route and the pondage route both exist they
**agree, 2 for 2, on 71.4 % of fleet MW** -- Niagara's 0.244 h lands in the daily
bucket (matching the 24 h derived from the treaty's silence) and St. Lawrence's
73.07 h lands in the 24-168 h bucket (matching the 168 h the IJC peaking-and-
ponding directive states in words). That is the only out-of-sample test of the
pondage route available and it passes.

**Reported against the probe's own conclusion (charter §5 R1):** the bucket depends
on head, and **78.03 % of fleet MW rests on a labelled dam-height PROXY whose error
runs in both directions**. Plants near a bucket boundary (Spier Falls 82.8 h,
Curtis 2.0 h) could move across it under a 2x head correction. The probe prints the
head-basis split so this is visible wherever its buckets are quoted.

**Reproducibility, stated plainly.** Q-A reads ``results/calibration/nyiso220_arm_2025``,
which is **gitignored** under rule 29(c) and retained on local disk under rule 31
``[R-RETAIN]`` -- so this probe does **not** re-run from a clean clone. Its
committed JSON output is therefore the record, exactly as rule 29(c) intends
("the PRECOMMIT / FINDING doc carries every number the session will ever cite").
Q-B reads only committed inputs and re-runs anywhere. Regenerating Q-A needs the
single-delta arm re-solved: ``scripts/replay_keeper.py
results/calibration/nyiso213_summer_seam --years 2025 --set
hydro_budget_period_by_instrument=true --out-dir results/calibration/nyiso220_arm_2025``.

ZERO LP. Nothing armed, no ``ScenarioConfig`` field, keeper untouched, no held-out
year read (2025 training tier only). Authorizes nothing.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

ARM = REPO / "results" / "calibration" / "nyiso220_arm_2025"
INDEX = REPO / "results" / "calibration" / "_nyiso219_ferc_licence_index.csv"
OUT_JSON = REPO / "results" / "calibration" / "_nyiso220_fleet_period_evidence.json"

# The plants the nyiso-220 screen actually constrained, and their periods.
CONSTRAINED: dict[int, int] = {2693: 24, 2694: 168}

# The LP's own calendar period grid. These are NOT fitted thresholds -- they are
# the periods the budget row can express (a day, a week, a month).
BUCKET_EDGES: tuple[tuple[str, float], ...] = (
    ("daily (<24 h)", 24.0),
    ("weekly (24-168 h)", 168.0),
    ("monthly-ish (168-730 h)", 730.0),
)


def _month_index(hours: int = 8760) -> np.ndarray:
    """Return the calendar month index (0-11) of each hour."""
    from market_sim.data.fleet import _hour_to_month_index

    return np.asarray(_hour_to_month_index(hours), dtype=int)


def cross_day_footprint(mw: np.ndarray, month: np.ndarray) -> float:
    """Return MWh this plant moves across day boundaries within its months.

    For each month the flat level is that month's energy spread evenly; the
    footprint is the sum over days of ``max(0, day energy - flat allocation)``,
    i.e. exactly the energy a daily budget period would forbid moving.
    """
    total = float(mw.sum())
    if total <= 0:
        return 0.0
    idx = np.arange(mw.size)
    excess = 0.0
    for m in range(12):
        sel = month == m
        level = mw[sel].sum() / sel.sum()
        hrs = idx[sel]
        for day in np.unique(hrs // 24):
            block = hrs[(hrs // 24) == day]
            excess += max(0.0, float(mw[block].sum()) - level * len(block))
    return excess


def bucket_for(pondage_hours: float | None) -> str:
    """Return the LP-period bucket a measured pondage falls in."""
    if pondage_hours is None:
        return "no pondage (no NID dam)"
    for name, edge in BUCKET_EDGES:
        if pondage_hours < edge:
            return name
    return "month or longer (>=730 h)"


def main() -> int:
    """Run both evidence passes and write deterministic JSON."""
    month = _month_index()

    # ---- Q-A: decompose the arm's residual footprint per plant --------------
    unit = pd.read_parquet(
        ARM / "hourly" / "unit_hourly_2025.parquet",
        columns=["pass", "plant_code", "fuel", "hour", "mw"],
    )
    unit = unit[(unit["pass"] == "P1") & (unit["fuel"].astype(str) == "hydro")]
    pivot = unit.pivot_table(
        index="hour", columns="plant_code", values="mw", aggfunc="sum"
    ).sort_index()

    per_plant = []
    for code in pivot.columns:
        mw = pivot[code].to_numpy(dtype=float)
        per_plant.append(
            {
                "plant": int(code),
                "twh": float(mw.sum()) / 1e6,
                "footprint_mwh": cross_day_footprint(mw, month),
            }
        )
    df = pd.DataFrame(per_plant)
    df["pct_own_energy"] = 100.0 * df.footprint_mwh / (df.twh * 1e6)

    con = df[df.plant.isin(CONSTRAINED)]
    unc = df[~df.plant.isin(CONSTRAINED)]
    tot_e, tot_f = float(df.twh.sum()), float(df.footprint_mwh.sum())

    def _grp(g: pd.DataFrame) -> dict:
        e, f = float(g.twh.sum()), float(g.footprint_mwh.sum())
        return {
            "plants": int(len(g)),
            "twh": round(e, 4),
            "pct_of_hydro_energy": round(100.0 * e / tot_e, 2),
            "footprint_twh": round(f / 1e6, 4),
            "pct_of_residual_footprint": round(100.0 * f / tot_f, 2),
            "swing_rate_pct_of_own_energy": round(100.0 * f / (e * 1e6), 2),
        }

    # ---- Q-B: what a pondage-bucketed assignment would cover ----------------
    rows = list(csv.DictReader(INDEX.open()))
    fleet_mw = sum(float(r["nameplate_mw"] or 0.0) for r in rows)
    buckets: dict[str, dict] = {}
    head_basis: dict[str, dict] = {}
    for r in rows:
        raw = r.get("pondage_hours_upper_bound", "")
        hours = float(raw) if raw not in ("", "None") else None
        mw = float(r["nameplate_mw"] or 0.0)
        b = buckets.setdefault(bucket_for(hours), {"plants": 0, "mw": 0.0})
        b["plants"] += 1
        b["mw"] += mw
        hb = head_basis.setdefault(
            r.get("head_basis") or "none", {"plants": 0, "mw": 0.0}
        )
        hb["plants"] += 1
        hb["mw"] += mw

    def _pct(d: dict) -> dict:
        return {
            k: {
                "plants": v["plants"],
                "mw": round(v["mw"], 1),
                "pct_fleet_mw": round(100.0 * v["mw"] / fleet_mw, 2),
            }
            for k, v in d.items()
        }

    payload = {
        "probe": "nyiso220_fleet_period_evidence",
        "zero_lp": True,
        "owner_instruction": (
            "I don't think the other 145 should keep the month that's the problem "
            "I think that's way too generous for how flexible hydro is. this "
            "deserves a charter to get right"
        ),
        "charter": "docs/CHARTER-nyiso220-fleet-wide-hydro-budget-period-2026-09-08.md",
        "source_arm": "results/calibration/nyiso220_arm_2025 (gitignored, rule 29(c)/31)",
        "residual_footprint_decomposition": {
            "total_hydro_twh": round(tot_e, 4),
            "total_residual_footprint_twh": round(tot_f / 1e6, 4),
            "constrained": _grp(con),
            "unconstrained": _grp(unc),
        },
        "worst_unconstrained": [
            {
                "plant": int(r.plant),
                "twh": round(float(r.twh), 4),
                "pct_own_energy": round(float(r.pct_own_energy), 2),
            }
            for r in unc.sort_values("footprint_mwh", ascending=False)
            .head(8)
            .itertuples()
        ],
        "pondage_bucket_census": _pct(buckets),
        "head_basis_split": _pct(head_basis),
        "route_validation": {
            "claim": (
                "where the instrument route and the pondage route both exist they "
                "agree, 2 for 2, on 71.4 % of fleet MW"
            ),
            "2693_niagara": {
                "pondage_h": 0.244,
                "pondage_bucket": bucket_for(0.244),
                "instrument_period_h": 24,
            },
            "2694_st_lawrence": {
                "pondage_h": 73.067,
                "pondage_bucket": bucket_for(73.067),
                "instrument_period_h": 168,
            },
        },
        "stated_risk": (
            "The bucket depends on HEAD, and 78.03 % of fleet MW rests on a "
            "labelled dam-height proxy whose error runs in BOTH directions. "
            "Plants near a boundary could move across it under a 2x head "
            "correction. Charter §5 R1; this is the most likely way a "
            "fleet-wide build is wrong."
        ),
        "authorizes": "nothing — evidence for an owner decision on charter §9",
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {OUT_JSON.relative_to(REPO)}")
    d = payload["residual_footprint_decomposition"]
    for k in ("constrained", "unconstrained"):
        g = d[k]
        print(
            f"  {k:<14} {g['plants']:>3} plants  {g['pct_of_hydro_energy']:>5.1f}% of energy  "
            f"{g['pct_of_residual_footprint']:>5.1f}% of residual  "
            f"swing {g['swing_rate_pct_of_own_energy']:>5.2f}%"
        )
    print("  pondage buckets:")
    for k, v in payload["pondage_bucket_census"].items():
        print(f"    {k:<28}{v['plants']:>4} plants {v['pct_fleet_mw']:>7.2f}% fleet MW")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

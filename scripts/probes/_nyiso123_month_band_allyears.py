"""nyiso-123 — the month x actual-price-band decomposition, for ALL THREE training years.

nyiso-122 established that NYISO's 2025 C3a FAILURE is two seasonally separable
objects: a **Jan+Feb $100-300-band** miss and a **Jun+Jul >$300 tail** miss, with
every other month netting positive.  It measured that split for **2025 only**.
The committed record (``_nyiso122_c3a_2025_decomp.json``) carries per-year bands
aggregated over the **whole year**, so the seasonal structure that carries the
argument exists for no year but 2025, and only in that finding's prose.

Rule 22 requires a leave-one-year-out grounding *before* any structural mechanism
is promoted.  This probe supplies its first leg: the same month x band table for
**2023 and 2024**, so the claim "2025 is the same defect with the compensating
error removed" can be checked rather than asserted.

It deliberately does **not** impose 2025's Jan+Feb / Jun+Jul grouping on the other
years.  Every month is reported, and the seasonal grouping is applied afterwards
as one view among several, so a year whose gap sits in different months shows that
rather than being folded into 2025's shape.

Reads only COMMITTED artifacts -- the keeper bundle's ``hourly/system_<year>.parquet``
sidecars (rule 15) and the committed hourly actual
``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``.  No LP, no derive,
no solve.  Every measured price is a validation target (rule 13 ``[R-MEASURED]``);
nothing here enters a solve.

Rule 22: TRAINING YEARS ONLY.  The committed actual parquet also carries 2018-2022
and H1-2026, every one of which is out-of-training for NYISO, and the holdout spend
freeze is ACTIVE regardless.  ``YEARS`` is a hard filter and ``_actual()`` raises.

Outputs ``results/calibration/_nyiso123_month_band_allyears.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Training years only -- rule 22 [R-HOLDOUT].
YEARS: tuple[int, ...] = (2023, 2024, 2025)
HOURS = 8760

REPO = Path(__file__).resolve().parents[2]
KEEPER_BUNDLE = REPO / "results/calibration/nyiso120_c119_scopegate"
ACTUAL_HOURLY = REPO / "data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet"
OUT = REPO / "results/calibration/_nyiso123_month_band_allyears.json"

# The model's fixed non-leap 8760-hour clock, keyed to 2023 and shared by EVERY
# model year (scripts/data/build_ercot_as_withholding.py::_CALENDAR, build_caiso_hsl,
# pipeline/ttc.py).  A leap year's Feb 29 is dropped, so hour h maps to the same
# (month, day, hour) in every year.  nyiso-122's probes built the map with a
# per-year ``date_range(f"{year}-01-01", ...)``, which is identical for the
# non-leap 2023 and 2025 but shifts 2024 by one day from Mar 1 onward; this probe
# uses the canonical clock for all three years and reports the difference.
_CALENDAR = pd.date_range("2023-01-01", periods=HOURS, freq="h")
MONTH_OF_HOUR = _CALENDAR.month.to_numpy()

# Coarse bands on the ACTUAL RT price.  Same edges nyiso-122 used, so the 2025
# row of this table must reproduce that finding's section 1 exactly: the $300 cap is the
# ISO's own C3c scarcity threshold (rubric section 5, NYISO/NEISO = $300) and $100 is
# the rung above which nyiso-110's compression object dominates.
COARSE_EDGES = (-np.inf, 100.0, 300.0, np.inf)
COARSE_LABELS = ("<=100", "100-300", ">300")
TAIL_THRESHOLD = 300.0

# The seasonal grouping nyiso-122 derived FROM 2025.  Applied here as a VIEW over
# the per-month rows, never as the unit of measurement, so a year whose gap sits
# elsewhere is visible rather than absorbed.
SEASONS: tuple[tuple[str, tuple[int, ...]], ...] = (
    ("Jan+Feb", (1, 2)),
    ("Jun+Jul", (6, 7)),
)


def _model_hourly(year: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(price, demand)`` demand-weighted system hourly series for ``year``.

    Identical construction to ``_nyiso122_c3a_2025_decomp._model_hourly`` -- the
    model system price in hour t is the zonal dual weighted by that zone-hour's
    demand, which is the basis C3a scores on.
    """
    df = pd.read_parquet(KEEPER_BUNDLE / f"hourly/system_{year}.parquet")
    if df["pass"].nunique() > 1:  # P1 is the scored pass (spec section 1.6)
        df = df[df["pass"] == df["pass"].max()]
    p = df.pivot_table(index="hour", columns="zone", values="price").reindex(range(HOURS))
    d = df.pivot_table(index="hour", columns="zone", values="demand").reindex(range(HOURS))
    w = d.to_numpy(float)
    price = np.nansum(p.to_numpy(float) * w, axis=1) / np.nansum(w, axis=1)
    return price, np.nansum(w, axis=1)


def _actual(year: int) -> np.ndarray:
    """Committed hourly actual RT LMP for ``year``, NaN-padded to 8760 hours."""
    if year not in YEARS:  # rule 22 -- fail closed, never widen the window
        raise SystemExit(f"REFUSED: {year} is out-of-training for NYISO (rule 22)")
    df = pd.read_parquet(ACTUAL_HOURLY)
    df = df[df["year"] == year]
    out = np.full(HOURS, np.nan)
    hr = df["hour"].to_numpy(int)
    keep = hr < HOURS
    out[hr[keep]] = df["rt"].to_numpy(float)[keep]
    return out


def _coarse_band(actual: np.ndarray) -> np.ndarray:
    """Index into ``COARSE_LABELS`` for each hour's ACTUAL price."""
    return np.digitize(actual, COARSE_EDGES[1:-1], right=False)


def decompose(year: int) -> dict:
    """Month x actual-price-band contribution to ``year``'s annual C3a gap."""
    model, dem = _model_hourly(year)
    act = _actual(year)
    ok = np.isfinite(model) & np.isfinite(act) & np.isfinite(dem) & (dem > 0)
    m, a, w = model[ok], act[ok], dem[ok]
    mo, band = MONTH_OF_HOUR[ok], _coarse_band(act)[ok]
    wn = w / w.sum()  # annual load weights -- every contribution below is on the
    #                   SAME denominator, so month and band rows sum to the annual gap

    mean_m, mean_a = float(np.sum(wn * m)), float(np.sum(wn * a))
    contrib = wn * (m - a)

    months = []
    for k in range(1, 13):
        km = mo == k
        if not km.any():
            continue
        by_band = {}
        for bi, lab in enumerate(COARSE_LABELS):
            kb = km & (band == bi)
            by_band[lab] = round(float(contrib[kb].sum()), 3) if kb.any() else 0.0
        months.append(
            {
                "month": k,
                "hours": int(km.sum()),
                "load_share_pct": round(100 * float(wn[km].sum()), 3),
                "model_mean": round(float(np.average(m[km], weights=w[km])), 2),
                "actual_mean": round(float(np.average(a[km], weights=w[km])), 2),
                "gap_contrib": round(float(contrib[km].sum()), 3),
                "by_band": by_band,
                "tail_hours": int((a[km] > TAIL_THRESHOLD).sum()),
            }
        )

    # ---- the seasonal VIEW, assembled from the per-month rows ---------------
    seasons, claimed = [], set()
    for name, mset in SEASONS:
        km = np.isin(mo, mset)
        claimed |= set(mset)
        seasons.append(
            {
                "season": name,
                "months": list(mset),
                "gap_contrib": round(float(contrib[km].sum()), 3),
                "by_band": {
                    lab: round(float(contrib[km & (band == bi)].sum()), 3)
                    for bi, lab in enumerate(COARSE_LABELS)
                },
                "tail_hours": int((a[km] > TAIL_THRESHOLD).sum()),
            }
        )
    krest = ~np.isin(mo, sorted(claimed))
    seasons.append(
        {
            "season": "all other months",
            "months": [k for k in range(1, 13) if k not in claimed],
            "gap_contrib": round(float(contrib[krest].sum()), 3),
            "by_band": {
                lab: round(float(contrib[krest & (band == bi)].sum()), 3)
                for bi, lab in enumerate(COARSE_LABELS)
            },
            "tail_hours": int((a[krest] > TAIL_THRESHOLD).sum()),
        }
    )

    # ---- REGIME vs DEFECT ---------------------------------------------------
    # A band's contribution to the annual gap is (load share) x (conditional
    # miss).  Those two factors answer different questions and must not be
    # conflated: the conditional miss is what the MODEL gets wrong per hour, the
    # load share is how often the MARKET puts it in that situation.  A
    # contribution that grows because the share grew is the SAME defect in a
    # changed regime; one that grows because the conditional miss grew is a
    # defect that got worse.  Contributions are also normalized by the year's
    # actual mean, because C3a scores a PERCENTAGE and the three years sit at
    # very different price levels (32.05 / 38.14 / 66.37).
    regime = []
    for bi, lab in enumerate(COARSE_LABELS):
        kb = band == bi
        if not kb.any():
            continue
        regime.append(
            {
                "band": lab,
                "hours": int(kb.sum()),
                "load_share_pct": round(100 * float(wn[kb].sum()), 3),
                "cond_model_mean": round(float(np.average(m[kb], weights=w[kb])), 2),
                "cond_actual_mean": round(float(np.average(a[kb], weights=w[kb])), 2),
                # per-hour miss WITHIN the band -- the model-side quantity
                "cond_miss": round(
                    float(np.average(m[kb] - a[kb], weights=w[kb])), 2
                ),
                "gap_contrib": round(float(contrib[kb].sum()), 3),
                # the same contribution on C3a's own percentage basis
                "gap_contrib_pct": round(100 * float(contrib[kb].sum()) / mean_a, 3),
            }
        )

    # ---- where the gap ACTUALLY concentrates, derived not assumed ----------
    # The two months carrying the largest negative contribution in THIS year,
    # so a year whose miss is not seasonal in 2025's shape says so itself.
    order = sorted(months, key=lambda r: r["gap_contrib"])
    return {
        "year": year,
        "model_mean_lw": round(mean_m, 2),
        "actual_mean_lw": round(mean_a, 2),
        "gap": round(mean_m - mean_a, 3),
        "err_pct": round(100 * (mean_m - mean_a) / mean_a, 2),
        "hours_scored": int(ok.sum()),
        "months": months,
        "seasons": seasons,
        "regime": regime,
        "worst_two_months": [
            {"month": r["month"], "gap_contrib": r["gap_contrib"]} for r in order[:2]
        ],
        "best_two_months": [
            {"month": r["month"], "gap_contrib": r["gap_contrib"]} for r in order[-2:]
        ],
        "band_totals": {
            lab: round(float(contrib[band == bi].sum()), 3)
            for bi, lab in enumerate(COARSE_LABELS)
        },
    }


def main() -> None:
    res = {
        "probe": "nyiso-123 -- month x actual-price-band C3a decomposition, all three training years (no LP)",
        "keeper": "2026-08-04-nyiso-120-c119-scope",
        "bundle": str(KEEPER_BUNDLE.relative_to(REPO)),
        "years": list(YEARS),
        "years_note": "rule 22 [R-HOLDOUT]: training years only; 2018-2022 and 2026 present in the committed actual parquet are NEVER read",
        "clock_note": (
            "hour->month uses the repo's canonical fixed NON-LEAP 8760 clock keyed to 2023 "
            "(build_ercot_as_withholding._CALENDAR). nyiso-122 used a per-year date_range, "
            "identical for 2023/2025 and one day offset for leap-2024 from Mar 1 onward."
        ),
        "results": [decompose(y) for y in YEARS],
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")

    for r in res["results"]:
        print(
            f"\n=== {r['year']}  model {r['model_mean_lw']:.2f}  actual "
            f"{r['actual_mean_lw']:.2f}  gap {r['gap']:+.2f} ({r['err_pct']:+.2f}%)"
        )
        print(f"  {'mo':>3}{'load%':>8}{'model':>9}{'actual':>9}{'<=100':>9}{'100-300':>9}{'>300':>8}{'TOTAL':>9}{'tailh':>7}")
        for b in r["months"]:
            print(
                f"  {b['month']:3d}{b['load_share_pct']:8.2f}{b['model_mean']:9.2f}"
                f"{b['actual_mean']:9.2f}{b['by_band']['<=100']:+9.3f}"
                f"{b['by_band']['100-300']:+9.3f}{b['by_band']['>300']:+8.3f}"
                f"{b['gap_contrib']:+9.3f}{b['tail_hours']:7d}"
            )
        print("  " + "-" * 71)
        for s in r["seasons"]:
            print(
                f"  {s['season']:<18}{s['by_band']['<=100']:+9.3f}{s['by_band']['100-300']:+9.3f}"
                f"{s['by_band']['>300']:+8.3f}{s['gap_contrib']:+9.3f}{s['tail_hours']:7d}"
            )
        print(
            f"  worst months {[(x['month'], x['gap_contrib']) for x in r['worst_two_months']]}"
            f" | best {[(x['month'], x['gap_contrib']) for x in r['best_two_months']]}"
        )
        print(f"  {'band':>8}{'hours':>7}{'load%':>8}{'cond mod':>10}{'cond act':>10}"
              f"{'cond miss':>11}{'contrib$':>10}{'contrib%':>10}")
        for g in r["regime"]:
            print(
                f"  {g['band']:>8}{g['hours']:7d}{g['load_share_pct']:8.2f}"
                f"{g['cond_model_mean']:10.2f}{g['cond_actual_mean']:10.2f}"
                f"{g['cond_miss']:+11.2f}{g['gap_contrib']:+10.3f}{g['gap_contrib_pct']:+10.2f}"
            )

    # ---- the cross-year comparison the leave-one-year-out grounding needs ---
    print("\n=== YEAR-OVER-YEAR, on C3a's own percentage basis (pp of actual mean)")
    print(f"  {'band':>8}" + "".join(f"{y:>10}" for y in YEARS)
          + f"{'23->24':>10}{'24->25':>10}")
    byyear = {r["year"]: {g["band"]: g for g in r["regime"]} for r in res["results"]}
    for lab in COARSE_LABELS:
        v = [byyear[y].get(lab, {}).get("gap_contrib_pct", 0.0) for y in YEARS]
        print(f"  {lab:>8}" + "".join(f"{x:+10.2f}" for x in v)
              + f"{v[1] - v[0]:+10.2f}{v[2] - v[1]:+10.2f}")
    tot = [r["err_pct"] for r in res["results"]]
    print(f"  {'TOTAL':>8}" + "".join(f"{x:+10.2f}" for x in tot)
          + f"{tot[1] - tot[0]:+10.2f}{tot[2] - tot[1]:+10.2f}")
    print(f"\n  {'band':>8}  conditional per-hour miss $/MWh, and load share %")
    for lab in COARSE_LABELS:
        cm = [byyear[y].get(lab, {}).get("cond_miss", 0.0) for y in YEARS]
        ls = [byyear[y].get(lab, {}).get("load_share_pct", 0.0) for y in YEARS]
        print(f"  {lab:>8}  miss " + " ".join(f"{x:+9.2f}" for x in cm)
              + "   share " + " ".join(f"{x:7.2f}" for x in ls))

    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

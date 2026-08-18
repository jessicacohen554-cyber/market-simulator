"""neiso-100 — measure how stale the standing NEISO 2022 touchpoint is against the keeper.

Read-only, committed-artifact-only. **No LP is constructed and no year is solved,
scored or registered.** In particular this probe deliberately does **not** invoke
``calibration_verdict`` on the 2022 bundle: ``holdout-freeze.json`` is ACTIVE and
its ``scope.frozen_operations`` names ``score``, which a scorer-side re-read is.

Why it exists. neiso-98 §3.3 concluded that a 2022 re-iteration was not worth
requesting, on three legs; neiso-99 §6 asserted that conclusion forward. Leg 3 of
it — *"the model side has not moved either"* — was true of neiso-97 (a dispatch
no-op) and is **false** of neiso-99, which is the first NEISO keeper change since
neiso-93 that moves the dispatch AND the scored pass. This measures what actually
separates the touchpoint from the keeper, so the standing claim rests on a number
rather than on a recollection.

Two legs:

  1. **Recipe/input divergence at hash grain.** ``meta.json``'s content-addressed
     ``shared_inputs`` plus the ``commitment`` / ``passes`` scoring basis, compared
     across the touchpoint, the superseded keeper and the designated keeper. The
     three-way form matters: it separates staleness that was ALREADY present at
     neiso-98 (and went unreported there) from staleness neiso-99 introduced.

  2. **2022's exposure to the liquid-fuel-CT routing guard, measured on 2022
     itself.** The obvious objection to bounding the routing leg's 2022 effect
     from the tuned years is that 2022's exposure could be larger. This diffs the
     pre-guard extract against HEAD on a ``(facility_id, unit_id, outage_start,
     outage_end)`` key and counts removed windows that OVERLAP each calendar year
     — overlap, not start-year, because a window opened in December is charged to
     the following year too. It also splits guard removals (the four plants
     neiso-99 names) from whole-file re-derive churn, so the churn can be shown to
     touch neither the training window nor the touchpoint.

Rule 22 ``[R-HOLDOUT]``: every out-of-training read here is of a measured INPUT
with no model side. Nothing is scored.

Usage::

    uv run python scripts/probes/neiso100_touchpoint_staleness.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]

#: The designated keeper, the keeper it superseded, and the standing 2022
#: validation touchpoint.
KEEPER = ("2026-08-17-neiso-99-joint-p1", REPO / "results/calibration/neiso99_joint_B")
PRIOR = ("2026-08-17-neiso-97-dstrepair", REPO / "results/calibration/neiso97_dstrepair_A")
TOUCHPOINT = ("2026-08-06-neiso-2022-corrected-basis", REPO / "results/calibration/neiso86_2022_corrected")

OUTAGES = REPO / "data/raw/campd-unit-outages-NEISO.csv"
#: The commit that landed the liquid-fuel-CT routing guard; its parent is the
#: pre-guard extract.
GUARD_COMMIT = "ef9e911"
#: The four plants neiso-99 names as the guard's population.
GUARD_PLANTS = (568, 1588, 1595, 6081)
#: Window key: a row is "the same window" iff all four agree.
WINDOW_KEY = ["facility_id", "unit_id", "outage_start", "outage_end"]
YEARS = range(2018, 2027)

OUT = REPO / "results/calibration/_neiso100_touchpoint_staleness.json"


def basis(bundle: Path) -> dict:
    """Read one bundle's scoring basis and content-addressed input set."""
    meta = json.loads((bundle / "meta.json").read_text())
    return {
        "commitment": meta.get("commitment"),
        "passes": meta.get("passes"),
        "shared_inputs": {k: Path(v).name for k, v in (meta.get("shared_inputs") or {}).items()},
    }


def leg1_divergence() -> dict:
    """Compare touchpoint / prior keeper / keeper at hash grain."""
    tp, pr, kp = (basis(b) for _, b in (TOUCHPOINT, PRIOR, KEEPER))
    axes = []
    for key in sorted(set(tp["shared_inputs"]) | set(kp["shared_inputs"])):
        t, p, k = (d["shared_inputs"].get(key) for d in (tp, pr, kp))
        axes.append(
            {
                "axis": key,
                "touchpoint": t,
                "prior_keeper": p,
                "keeper": k,
                "differs_vs_keeper": t != k,
                # Staleness already present at neiso-98, i.e. not introduced by
                # the neiso-99 promotion.
                "stale_before_neiso99": t != p,
            }
        )
    axes.append(
        {
            "axis": "scoring_basis",
            "touchpoint": f"commitment={tp['commitment']} passes={tp['passes']}",
            "prior_keeper": f"commitment={pr['commitment']} passes={pr['passes']}",
            "keeper": f"commitment={kp['commitment']} passes={kp['passes']}",
            "differs_vs_keeper": (tp["commitment"], tp["passes"]) != (kp["commitment"], kp["passes"]),
            "stale_before_neiso99": (tp["commitment"], tp["passes"]) != (pr["commitment"], pr["passes"]),
        }
    )
    return {
        "axes": axes,
        "n_differing_vs_keeper": sum(a["differs_vs_keeper"] for a in axes),
        "n_stale_before_neiso99": sum(a["stale_before_neiso99"] for a in axes),
    }


def _pre_guard_extract() -> pd.DataFrame:
    """The outage extract as it stood immediately before the routing guard."""
    blob = subprocess.run(
        ["git", "show", f"{GUARD_COMMIT}^:{OUTAGES.relative_to(REPO)}"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    from io import BytesIO

    return pd.read_csv(BytesIO(blob))


def _overlap_counts(df: pd.DataFrame) -> list[dict]:
    """Windows overlapping each calendar year, with their MW-window sum.

    Overlap rather than start-year: a window opened in December is charged to
    the following year as well, which is the grain a solve actually sees.
    """
    start = pd.to_datetime(df["outage_start"])
    end = pd.to_datetime(df["outage_end"])
    rows = []
    for year in YEARS:
        hit = (start <= pd.Timestamp(f"{year}-12-31 23:00")) & (end >= pd.Timestamp(f"{year}-01-01"))
        rows.append(
            {
                "year": year,
                "windows": int(hit.sum()),
                "mw_window_sum": round(float(df.loc[hit, "unit_capacity_mw"].sum()), 1),
            }
        )
    return rows


def leg2_routing_exposure() -> dict:
    """Split the pre/post extract diff into guard removals vs re-derive churn."""
    pre, post = _pre_guard_extract(), pd.read_csv(OUTAGES)
    for frame in (pre, post):
        frame["_k"] = frame[WINDOW_KEY].astype(str).agg("|".join, axis=1)
    removed = pre[~pre["_k"].isin(set(post["_k"]))].copy()

    is_guard = removed["facility_id"].isin(GUARD_PLANTS)
    guard, churn = removed[is_guard], removed[~is_guard]
    return {
        "pre_rows": int(len(pre)),
        "post_rows": int(len(post)),
        "removed_rows": int(len(removed)),
        "guard_rows": int(len(guard)),
        "churn_rows": int(len(churn)),
        "guard_rows_by_unit": [
            {"facility_id": int(f), "unit_id": str(u), "rows": int(n)}
            for (f, u), n in guard.groupby(["facility_id", "unit_id"]).size().items()
        ],
        "guard_overlap_by_year": _overlap_counts(guard),
        "churn_overlap_by_year": _overlap_counts(churn),
    }


def main() -> None:
    """Measure both legs and write the record."""
    leg1, leg2 = leg1_divergence(), leg2_routing_exposure()

    guard_by_year = {r["year"]: r for r in leg2["guard_overlap_by_year"]}
    churn_train = sum(
        r["windows"] for r in leg2["churn_overlap_by_year"] if 2021 <= r["year"] <= 2025
    )
    exposure_2022 = guard_by_year[2022]["windows"]
    tuned_min = min(guard_by_year[y]["windows"] for y in (2023, 2024, 2025))

    record = {
        "probe": "neiso100_touchpoint_staleness",
        "keeper": KEEPER[0],
        "prior_keeper": PRIOR[0],
        "touchpoint": TOUCHPOINT[0],
        "no_lp": True,
        "nothing_scored": True,
        "leg1_recipe_divergence": leg1,
        "leg2_routing_exposure": leg2,
        "verdict": {
            "touchpoint_axes_differing_from_keeper": leg1["n_differing_vs_keeper"],
            "axes_already_stale_before_neiso99": leg1["n_stale_before_neiso99"],
            "y2022_guard_windows": exposure_2022,
            "min_tuned_year_guard_windows": tuned_min,
            # The load-bearing claim: 2022's exposure to the routing guard is
            # strictly smaller than any tuned year's, so the routing leg's 2022
            # effect is bounded below its measured 2023-2025 band.
            "y2022_exposure_below_every_tuned_year": exposure_2022 < tuned_min,
            # The churn must touch neither the training window nor the touchpoint.
            "churn_windows_in_2021_2025": int(churn_train),
        },
    }

    print("=" * 74)
    print("neiso-100 — 2022 touchpoint staleness vs the designated keeper")
    print("=" * 74)
    print(f"\ntouchpoint {TOUCHPOINT[0]}  vs keeper {KEEPER[0]}\n")
    print(f"{'axis':<24} {'touchpoint':<34} {'keeper':<34} differs")
    for axis in leg1["axes"]:
        print(
            f"  {axis['axis']:<22} {str(axis['touchpoint']):<34} "
            f"{str(axis['keeper']):<34} {'YES' if axis['differs_vs_keeper'] else '-'}"
        )
    print(
        f"\n  differing axes: {leg1['n_differing_vs_keeper']}"
        f"  (already stale before neiso-99: {leg1['n_stale_before_neiso99']})"
    )

    print(f"\nrouting-guard removals: {leg2['guard_rows']} rows; re-derive churn: {leg2['churn_rows']} rows")
    print(f"\n  {'year':<6} {'guard windows':>14} {'MW-window sum':>15} {'churn windows':>15}")
    churn_by_year = {r["year"]: r for r in leg2["churn_overlap_by_year"]}
    for year in YEARS:
        g, c = guard_by_year[year], churn_by_year[year]
        print(f"  {year:<6} {g['windows']:>14} {g['mw_window_sum']:>15.1f} {c['windows']:>15}")

    print("\nverdict:")
    for key, value in record["verdict"].items():
        print(f"  {key:<44} {value}")

    OUT.write_text(json.dumps(record, indent=2) + "\n")
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    sys.exit(main())

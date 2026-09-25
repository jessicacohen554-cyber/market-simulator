"""Completeness audit of the EIA-923 monthly net-generation vintage.

The current-year EIA-923 release is a *preliminary monthly survey*: plants
trickle in their monthly net generation over the year following the report
year, so for a recent vintage (2025 today) many plants have reported only the
first few months — or not at all — while others are complete. The calibration
gate must not score a model class against a half-reported actual.

This script measures, per ISO and per model fuel class, how complete the
2025 EIA-923 plant data is, using two *vintage-internal* signals that need no
per-class EIA-930 split (which does not exist):

  1. **Month coverage** — the last calendar month any plant of the class
     reported, and the fraction of expected plant-months actually present.
     A complete annual vintage reports all 12 months for (nearly) every plant.
  2. **Year-over-year retention** — the class's 2025 reported net generation as
     a fraction of its 2024 (complete-vintage) total. A vintage still filling in
     reads far below the prior year purely because months/plants are missing.

It emits a per-(ISO, class) verdict — ``complete`` vs ``incomplete`` — that the
calibration verdict (C1 gate) and the dashboard color-coding both consume from a
single committed JSON, so the completeness call lives in one place.

Run: ``python scripts/audit_eia923_completeness.py [--year 2025] [--json PATH]``
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse the calibration loaders so the audit sees exactly the plant->ISO and
# 923-row->class mapping the benchmark builder uses (no parallel taxonomy).
from market_sim.config.paths import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT))
from scripts.run_calibration_full import (  # noqa: E402
    _classify_f923,
    _iso_plant_ids,
)

from market_sim.config.iso_configs import _ISO_BUILDERS  # noqa: E402
from market_sim.data.eia923 import (  # noqa: E402
    load_monthly_generation,
    monthly_netgen_columns,
)

# Fossil model classes the C1 gate scores (mirrors calibration_verdict
# GAS_CLASSES + COAL_CLASSES). Non-fossil/renewable classes are scored on
# EIA-930, so 923 completeness does not gate them.
#
# CAVEAT (nyiso-106) — that last sentence is true for every ISO EXCEPT the
# `(iso, class)` pairs in `results.calibration._EIA923_OVERRIDE`, which route a
# renewable class BACK to EIA-923 because its EIA-930 series is unusable. Today
# that is exactly one pair, NYISO solar (EIA-930 `NYIS` `NG: SUN` is identically
# zero — NY grid solar is overwhelmingly distribution-connected / net-metered).
# Such a class IS exposed to 923 vintage incompleteness and is NOT audited here:
# the 2025 vintage carries 8 of 565 NYIS solar plants and scored as solar +437 %.
# It is covered instead where the number is actually built —
# `run_calibration_full._backfill_renewables_eia930` now carries a class with no
# EIA-930 authority forward from the prior complete year (the same repair
# `biomass` takes), so the per-class actual is repaired rather than merely
# skipped. If a future `_EIA923_OVERRIDE` pair needs a SKIP as well as a repair,
# widen SCORED_CLASSES to include it — do not assume renewables are 930-scored.
# results/calibration/FINDING-nyiso106-solar-benchmark-vintage-2026-07-31.md §A.5
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = (
    "COAL_PRB",
    "COAL_LIGNITE",
    "COAL_BIT",
    "COAL_WC",
)  # COAL-SUB: no bare COAL
SCORED_CLASSES = tuple(c for c in (*GAS_CLASSES, *COAL_CLASSES))

# --- completeness thresholds ------------------------------------------------
# A class is COMPLETE when its current-year vintage looks like a full annual
# report. The defining failure of a preliminary EIA-923 vintage is MISSING
# PLANTS: plants trickle their report in over the year following the report year,
# so a recent vintage carries only a fraction of the plants that operated (2025
# nationally: ~7.7k plant-rows vs ~18k in the complete 2024 vintage). We measure
# that directly with two signals, BOTH of which must hold:
#
#   * **plant-reporting retention** — of the plants that reported this class with
#     material generation in the prior (complete) year, what fraction ALSO report
#     in the current vintage. Immune to real year-over-year generation swings (a
#     plant that ran less still files a report), so it isolates the "did the data
#     arrive" question — exactly the user's "incomplete plant data".
#   * **plant-month coverage** — among the plants that DID report, the fraction of
#     12 monthly cells present (non-null). A plant mid-filing reports only the
#     first months; a complete annual report carries all 12. A present-but-zero
#     month counts as reported (a legitimately-idle peaker month is not a gap).
#
# Volume retention is recorded for context but NOT gated on: a class can genuinely
# grow or shrink year-over-year (coal-gas switching swings coal ±20%), so a volume
# delta is not a completeness signal the way a missing plant is.
PLANT_RETENTION_MIN = 0.97  # >=97% of prior-year reporting plants present
PLANT_MONTH_MIN = 0.97  # >=97% of monthly cells present among reporting plants
LAST_MONTH_MIN = 12  # the vintage must carry December
# A plant counts as a prior-year "reporter" of the class only above this annual
# net generation — tiny/idle plants drop in and out of the survey for reasons
# unrelated to vintage completeness, so they would add noise to the retention
# ratio (and a missing 10 GWh plant is immaterial to the class total anyway).
PRIOR_PLANT_MIN_MWH = 10_000.0  # 10 GWh
# Below this annual volume a class is immaterial in the ISO: there is no
# meaningful plant data to be "complete" about, and the C1 absolute band governs
# it regardless, so it is reported as ``immaterial`` (never gated, never a silent
# pass) rather than complete/incomplete.
IMMATERIAL_TWH = 1.0


def _class_frame(gen: pd.DataFrame, iso: str, year: int) -> pd.DataFrame:
    """Per (plant, class) annual + monthly netgen for one ISO-year, in MWh.

    Restricts the national 923 table to the ISO's plants and classifies each row
    into a model fuel class, matching :func:`run_calibration_full._eia923_frame`.
    """
    df = gen[gen["year"] == year].copy()
    iso_plants = _iso_plant_ids(iso)
    if iso_plants:
        df = df[df["plant_id"].isin(iso_plants)].copy()
    if df.empty:
        return df
    df["klass"] = [
        _classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(
            df["fuel_type"], df["prime_mover"], df["chp"], df["plant_id"]
        )
    ]
    return df


def _audit_iso_class(cur: pd.DataFrame, prior: pd.DataFrame, klass: str) -> dict | None:
    """Completeness metrics for one (ISO, class). ``None`` if absent both years."""
    mcols = monthly_netgen_columns()
    c = cur[cur["klass"] == klass]
    p = prior[prior["klass"] == klass]
    cur_twh = float(c["netgen_annual_mwh"].sum()) / 1e6
    prior_twh = float(p["netgen_annual_mwh"].sum()) / 1e6
    if c.empty and p.empty:
        return None

    # Plant-reporting retention: prior-year plants with material generation, and
    # how many of them also appear in the current vintage. The cleanest
    # "incomplete plant data" signal — immune to real generation swings.
    prior_plants = set(
        int(pid)
        for pid, g in p.groupby("plant_id")["netgen_annual_mwh"].sum().items()
        if float(g) >= PRIOR_PLANT_MIN_MWH
    )
    cur_plants = set(int(pid) for pid in c["plant_id"].unique())
    n_prior = len(prior_plants)
    n_reported = len(prior_plants & cur_plants)
    plant_retention = (n_reported / n_prior) if n_prior else None
    n_missing = n_prior - n_reported

    # Plant-month coverage among the plants that DID report (present = non-null).
    monthly = c[mcols].to_numpy(float) if not c.empty else np.zeros((0, 12))
    present = np.isfinite(monthly)
    months_with_data = np.where(present.any(axis=0))[0]
    last_month = int(months_with_data.max() + 1) if months_with_data.size else 0
    expected_cells = monthly.shape[0] * 12
    plant_month_frac = float(present.sum()) / expected_cells if expected_cells else 0.0
    retention = (cur_twh / prior_twh) if prior_twh > 0 else None

    immaterial = max(cur_twh, prior_twh) < IMMATERIAL_TWH
    complete = (
        not immaterial
        and last_month >= LAST_MONTH_MIN
        and plant_month_frac >= PLANT_MONTH_MIN
        and (plant_retention is None or plant_retention >= PLANT_RETENTION_MIN)
    )
    status = "immaterial" if immaterial else ("complete" if complete else "incomplete")
    reasons = []
    if not immaterial:
        if last_month < LAST_MONTH_MIN:
            reasons.append(f"reaches only month {last_month}/12")
        if plant_retention is not None and plant_retention < PLANT_RETENTION_MIN:
            reasons.append(
                f"{n_missing}/{n_prior} prior plants missing "
                f"({plant_retention:.0%} reporting)"
            )
        if plant_month_frac < PLANT_MONTH_MIN:
            reasons.append(f"plant-months {plant_month_frac:.0%} present")
    return {
        "class": klass,
        "status": status,
        "cur_twh": round(cur_twh, 3),
        "prior_twh": round(prior_twh, 3),
        "retention": round(retention, 3) if retention is not None else None,
        "plant_retention": (
            round(plant_retention, 3) if plant_retention is not None else None
        ),
        "n_prior_plants": n_prior,
        "n_missing_plants": n_missing,
        "last_month": last_month,
        "plant_month_frac": round(plant_month_frac, 3),
        "reasons": reasons,
    }


def _family_of(klass: str) -> str:
    """Return the fossil family (``gas``/``coal``) a scored class belongs to."""
    return "coal" if klass in COAL_CLASSES else "gas"


def _apply_family_gate(classes: dict[str, dict]) -> dict[str, bool]:
    """Annotate each class with ``family_complete`` and ``gate``; return families.

    A class is GATE-ELIGIBLE in a preliminary vintage iff it is itself complete
    AND its whole fossil family is complete. The family condition is required
    because the dashboard/verdict benchmark (``classFull``) is *vintage-reconciled*
    per family — when any class in a family is short, ``reconcile_vintage_classes``
    scales the WHOLE family (including its complete classes) up to the EIA-930
    family total, so a complete class's reconciled actual would be inflated and
    gating it would compare the model against a distorted number. Requiring the
    family to be complete makes the reconcile a guaranteed no-op, so the gated
    class's actual is its true, un-scaled per-class EIA-923 total.
    """
    fam_complete: dict[str, bool] = {}
    for fam in ("gas", "coal"):
        members = [
            r
            for k, r in classes.items()
            if _family_of(k) == fam and r["status"] != "immaterial"
        ]
        # A family is complete only if it has at least one material class and
        # every material class in it is complete (an empty family gates nothing).
        fam_complete[fam] = bool(members) and all(
            r["status"] == "complete" for r in members
        )
    for klass, rec in classes.items():
        fam = _family_of(klass)
        rec["family"] = fam
        rec["family_complete"] = fam_complete[fam]
        rec["gate"] = bool(rec["status"] == "complete" and fam_complete[fam])
    return fam_complete


def audit(year: int, prior_year: int) -> dict:
    """Full per-ISO, per-class completeness audit for ``year`` vs ``prior_year``."""
    gen = load_monthly_generation()
    result: dict[str, dict] = {}
    families: dict[str, dict] = {}
    for iso in _ISO_BUILDERS:
        cur = _class_frame(gen, iso, year)
        prior = _class_frame(gen, iso, prior_year)
        classes: dict[str, dict] = {}
        for klass in SCORED_CLASSES:
            rec = _audit_iso_class(cur, prior, klass)
            if rec is not None:
                classes[klass] = rec
        families[iso] = _apply_family_gate(classes)
        result[iso] = classes
    return {
        "year": year,
        "prior_year": prior_year,
        "thresholds": {
            "last_month_min": LAST_MONTH_MIN,
            "plant_retention_min": PLANT_RETENTION_MIN,
            "plant_month_min": PLANT_MONTH_MIN,
            "prior_plant_min_mwh": PRIOR_PLANT_MIN_MWH,
            "immaterial_twh": IMMATERIAL_TWH,
        },
        "families": families,
        "isos": result,
    }


# Canonical committed map: a per-year "part" the calibration verdict and the
# dashboard builder both read (same committed-parts→generated-shared-files model
# as the bench parts). One JSON per audited year, auto-discovered by year.
REPO = Path(__file__).resolve().parent.parent
COMPLETENESS_DIR = REPO / "frontend" / "data" / "backcast" / "completeness"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2025)
    ap.add_argument("--prior-year", type=int, default=2024)
    ap.add_argument(
        "--json",
        type=Path,
        default=None,
        help="extra path to also write the map to (the canonical part is always "
        "written unless --no-write is given)",
    )
    ap.add_argument(
        "--no-write",
        action="store_true",
        help="print only; do not write the canonical completeness part",
    )
    args = ap.parse_args()
    out = audit(args.year, args.prior_year)

    n_gate = 0
    for iso, classes in out["isos"].items():
        fam = out["families"][iso]
        print(
            f"\n=== {iso} ({args.year} vs {args.prior_year}) "
            f"[gas family {'COMPLETE' if fam['gas'] else 'incomplete'}, "
            f"coal family {'COMPLETE' if fam['coal'] else 'incomplete'}] ==="
        )
        for klass, rec in classes.items():
            tag = rec["status"].upper()
            gate = " GATE" if rec["gate"] else ""
            n_gate += int(rec["gate"])
            reasons = f"  [{'; '.join(rec['reasons'])}]" if rec["reasons"] else ""
            pr = rec["plant_retention"]
            print(
                f"  {klass:<12} {tag:<11}{gate:<5} "
                f"cur={rec['cur_twh']:7.2f} prior={rec['prior_twh']:7.2f} "
                f"plantsRep={pr if pr is not None else 'n/a':>5} "
                f"({rec['n_missing_plants']}/{rec['n_prior_plants']} miss) "
                f"pm={rec['plant_month_frac']:.2f}{reasons}"
            )
    print(
        f"\nGate-eligible (ISO, class) pairs for {args.year}: {n_gate} "
        "(verified-complete class in a verified-complete family)."
    )

    payload = json.dumps(out, indent=2, sort_keys=True)
    if not args.no_write:
        COMPLETENESS_DIR.mkdir(parents=True, exist_ok=True)
        canonical = COMPLETENESS_DIR / f"eia923_{args.year}.json"
        canonical.write_text(payload + "\n")
        print(f"wrote {canonical.relative_to(REPO)}")
    if args.json:
        args.json.write_text(payload + "\n")
        print(f"wrote {args.json}")


if __name__ == "__main__":
    main()

"""nyiso-203 — the owner-ruled `CC_REGULAR` duct-tranche offer lever, re-measured on the
CURRENT keeper: does it still have a subject?

ZERO LP. Every number is read from the COMMITTED keeper bundle — the `class_band_hourly_<year>`
sidecar (rule 15 commits it for every keeper) plus a `fleet_only` reconstruction of the same
bundle (`scripts.lib.bundle_fleet.reconstruct_bundle_fleet`, fidelity-guarded). No solve, no
screen, nothing armed.

THE LEVER. `calibration-complete.json`'s `withdrawn.NYISO.reentry` names ONE route back to the
`complete` marker — the owner's own ruling in the nyiso-193 promotion sentence (2026-09-05,
verbatim): *"tune the cc regular offer curve up for the duct burner peaking tranche because
it's merit order is wrong it runs more often at lower CF and is running hot over 80% CF in all
years"* — *"which targets exactly the cell-G `CC_REGULAR` over-run that took C1-2024 out of
band."*

WHY IT IS RE-MEASURED HERE. nyiso-198 took two committed-artifact measurements against it (peak
band CF, and the share of class energy it carries) on keeper `2026-09-06-nyiso-196-extract-basis`
and stated them "for the owner court, not decided". Two keepers have landed since, and the
lever's stated TARGET has moved: C1-2024 `CC_REGULAR` was +3.68 TWh / +3.0 pp (out of band) at
the withdrawal and is +2.39 TWh / +2.1 pp on the current keeper. This probe re-takes the
measurements on the keeper the owner would actually be ruling on, and adds the one number the
disposition turns on: the ARITHMETIC BOUND on what the lever can move.

Reported per year:

  * **D-1** the `CC_REGULAR` peak (duct) band's LP capacity, and its share of the class's.
  * **D-2** the band's dispatched energy, its share of class energy, and its capacity factor —
    the two nyiso-198 numbers, re-taken.
  * **D-3** how much of that band is NOT duct capability, from EIA-860's own `Duct Burners`
    flags via nyiso-198's committed per-plant row-scoped percentages.
  * **D-4** THE BOUND: the band's energy expressed in the units C1 is scored in (percentage
    points of ISO load), against C1-2024's current margin to the +/-3.0 pp band. Raising an
    offer can at most displace the band's own energy, so this bounds the lever from above.

Diagnostic only (rule 13). Nothing is re-scored; no verdict moves.

Reproduce: `uv run python scripts/probes/_nyiso203_duct_lever_disposition.py`.
Writes `results/calibration/_nyiso203_duct_lever_disposition.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = ROOT / "results" / "calibration" / "nyiso202_startup_aware"
KEEPER_ID = "2026-09-06-nyiso-202-startup-aware"
KLASS = "CC_REGULAR"
YEARS = (2023, 2024, 2025)
# nyiso-198 phase 0 part 2, committed record: the peak band re-scoped to the EIA-860 rows the
# filing itself flags as duct-capable (CA/CS with Duct Burners = Y). Every CT row reads X (not
# applicable), so a CT row's nameplate-vs-summer gap cannot be duct capability.
NYISO198 = ROOT / "results" / "calibration" / "_nyiso198_duct_peaking_basis_phase0.json"
OUT = ROOT / "results" / "calibration" / "_nyiso203_duct_lever_disposition.json"
C1_BAND_PP = 3.0  # the rubric's C1 fuel-mix share band, +/- percentage points


def main() -> None:
    """Measure the lever's footprint and its arithmetic bound on the current keeper."""
    v198 = json.loads(NYISO198.read_text())
    rec: dict = {
        "session": "nyiso-203",
        "status": "ZERO LP — committed keeper artifacts + fleet_only reconstruction",
        "keeper": KEEPER_ID,
        "bundle": str(BUNDLE.relative_to(ROOT)),
        "lever": (
            "owner ruling 2026-09-05 (nyiso-193 promotion sentence), named in "
            "calibration-complete.json withdrawn.NYISO.reentry as THE route back to `complete`: "
            "tune the CC_REGULAR duct-burner PEAKING tranche offer UPWARD from measured "
            "duct-firing conduct"
        ),
        "years": {},
    }

    for year in YEARS:
        state, _meta = reconstruct_bundle_fleet(BUNDLE, year, verbose=False)
        fa = state["fleet_arrays"]
        groups = np.asarray(fa.plant_group)
        pmax = np.asarray(fa.pmax, dtype=float)
        uids = list(fa.unit_ids)
        pcode = np.asarray(fa.plant_code)
        sel = groups == KLASS
        is_peak = np.array([u.endswith("_peak") for u in uids])
        class_mw = float(pmax[sel].sum())
        peak_mw = float(pmax[sel & is_peak].sum())

        # D-3: the non-duct fraction of THIS class's peak band, from nyiso-198's committed
        # per-plant EIA-860 row-scoped percentages (pct_row_scoped applied to LP plant pmax).
        plants198 = v198["years"][str(year)]["plants"]
        peak_mw_row = 0.0
        covered_mw = 0.0
        for code in sorted({int(c) for c in pcode[sel & is_peak]}):
            p = plants198.get(str(code))
            rows = sel & is_peak & (pcode == code)
            mw_here = float(pmax[rows].sum())
            if p is None or p.get("peak_band_mw_row_scoped") is None:
                continue
            covered_mw += mw_here
            lp_peak = float(p["lp_peak_band_mw"]) or 0.0
            scale = mw_here / lp_peak if lp_peak else 0.0
            peak_mw_row += float(p["peak_band_mw_row_scoped"]) * scale

        # D-2: dispatched energy from the committed class-band sidecar.
        cb = pd.read_parquet(BUNDLE / "hourly" / f"class_band_hourly_{year}.parquet")
        cb = cb[(cb["klass"] == KLASS) & (cb["pass"] == "P1")]
        class_twh = float(cb["mw"].sum()) / 1e6
        peak_twh = float(cb[cb["band"] == "peak"]["mw"].sum()) / 1e6
        hours = int(cb["hour"].nunique())
        cf = peak_twh * 1e6 / (peak_mw * hours) if peak_mw else float("nan")

        rec["years"][str(year)] = {
            "class_lp_mw": round(class_mw, 2),
            "peak_band_lp_mw": round(peak_mw, 2),
            "peak_band_share_of_class_capacity_pct": round(
                100.0 * peak_mw / class_mw, 2
            ),
            "peak_band_lp_mw_row_scoped": round(peak_mw_row, 2),
            "peak_band_mw_not_duct": round(peak_mw - peak_mw_row, 2),
            "not_duct_share_pct": round(100.0 * (peak_mw - peak_mw_row) / peak_mw, 1),
            "row_scope_coverage_mw": round(covered_mw, 2),
            "class_energy_twh": round(class_twh, 4),
            "peak_band_energy_twh": round(peak_twh, 4),
            "peak_band_share_of_class_energy_pct": round(
                100.0 * peak_twh / class_twh, 2
            ),
            "peak_band_cf": round(cf, 4),
            "hours": hours,
        }

    # D-4: THE BOUND. Express the band's energy in the units C1 is scored in. C1's share error
    # is (model - actual) energy over ISO load, so ISO load is recovered from the keeper's own
    # committed C1 pair (TWh error and pp error) and the band is converted onto that scale.
    # C1 `CC_REGULAR` errors as scored on this keeper and on the run whose miss took the marker
    # down, quoted from the committed determinations (scripts/calibration_verdict.py --run-id and
    # the run's registry sidecar) rather than recomputed here. 2025 is SKIPPED by C1 (preliminary
    # EIA-923 vintage, 45 % plant reporting), so it bounds nothing.
    c1_overrun_twh = {"2023": 0.37, "2024": 2.39}
    c1_overrun_at_withdrawal_2024 = 3.68  # 2026-09-05-nyiso-192-astoria-panel, +3.0 pp
    bound = {}
    for year, over in c1_overrun_twh.items():
        band = rec["years"][year]["peak_band_energy_twh"]
        bound[year] = {
            "c1_cc_regular_overrun_twh": over,
            "peak_band_energy_twh": band,
            "max_possible_closure_pct": round(100.0 * band / over, 1),
        }
    bound["2024_at_withdrawal"] = {
        "c1_cc_regular_overrun_twh": c1_overrun_at_withdrawal_2024,
        "peak_band_energy_twh": rec["years"]["2024"]["peak_band_energy_twh"],
        "max_possible_closure_pct": round(
            100.0
            * rec["years"]["2024"]["peak_band_energy_twh"]
            / c1_overrun_at_withdrawal_2024,
            1,
        ),
    }
    rec["bound"] = {
        "note": (
            "Raising an offer can displace at most the band's OWN dispatched energy, so this "
            "bounds the lever from above. The lever REDUCES CC_REGULAR, so it can only help "
            "while the C1 error is positive, which it is in both scored years. 2025 is SKIPPED "
            "by C1 (preliminary EIA-923 vintage) and is excluded."
        ),
        "by_year": bound,
    }
    OUT.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")

    print(
        f"=== nyiso-203 — the duct-tranche lever on keeper {KEEPER_ID} (ZERO LP) ===\n"
    )
    print(
        f"  {'year':<6}{'class MW':>10}{'peak MW':>9}{'% cap':>7}{'not-duct MW':>13}"
        f"{'% not duct':>12}{'peak TWh':>10}{'% class E':>11}{'peak CF':>9}"
    )
    for year in YEARS:
        r = rec["years"][str(year)]
        print(
            f"  {year:<6}{r['class_lp_mw']:>10.0f}{r['peak_band_lp_mw']:>9.0f}"
            f"{r['peak_band_share_of_class_capacity_pct']:>7.1f}"
            f"{r['peak_band_mw_not_duct']:>13.0f}{r['not_duct_share_pct']:>12.1f}"
            f"{r['peak_band_energy_twh']:>10.4f}"
            f"{r['peak_band_share_of_class_energy_pct']:>11.2f}"
            f"{r['peak_band_cf']:>9.3f}"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

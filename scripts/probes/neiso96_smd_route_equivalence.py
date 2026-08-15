"""Prove the ISO-NE daily-report LMP route equals the SMD-workbook route.

neiso-96, 2026-08-15.  ``scripts/data/derive_actual_lmp.py`` has always
sourced NEISO from the hand-downloaded SMD hourly workbooks
(``data/raw/lmp-data/NEISO/<year>_smd_hourly.xlsx``).  Those are CAPTCHA-gated
at the ISO Express *Zonal Information* form, so H1-2026 could not be obtained
that way.  ``scripts/data/fetch_neiso_smd_zonal_lmp.py`` reaches the same nine
SMD pricing locations through ISO-NE's ungated static historical-report tree
instead.

Carrying 2026 on the second route is only legitimate if the two routes are ONE
input rather than two -- otherwise the parquet would silently become a
year-gated splice, which CLAUDE.md rule 22 as amended 2026-08-06 forbids
("apply a measured input consistently across all years").  This probe measures
that, rather than asserting it.

Method.  For each sampled operating day of a COMMITTED year, compare the
daily-report reduction against the committed workbook, hour for hour and
location for location, at the point BEFORE densification -- i.e. against
``derive_actual_lmp.neiso_zone_hourly``'s own output, the exact frame the
committed parquet is built from.  Comparing pre-densification is deliberate: it
tests the source reduction itself, and it lets a leap day (dropped by the 8760
calendar) be sampled like any other.

Sampled days are chosen to cover the cases a splice would break on: both DST
transitions, a leap day, the winter scarcity events that produce the tail hours
C3c scores, and an ordinary summer day.

Output: ``results/calibration/_neiso96_smd_route_equivalence.json``.

NO YEAR IS SOLVED, SCORED OR REGISTERED.  This reads committed inputs and a
published actuals source only.

Usage:
    uv run python scripts/probes/neiso96_smd_route_equivalence.py \
        --sample-dir <dir with NEISO_smd_zonal_lmp_<year>.csv>
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data import derive_actual_lmp as dal  # noqa: E402
from scripts.data.fetch_neiso_smd_zonal_lmp import SMD_LOCATIONS  # noqa: E402

OUT = REPO / "results" / "calibration" / "_neiso96_smd_route_equivalence.json"

#: Float64 equality tolerance, in $/MWh. Neither route is bit-exact against the
#: other in float64, and the cause is storage rather than a price disagreement:
#: openpyxl returns the doubles Excel stored (16.580000000000002), while the CSV
#: publishes the decimal ISO-NE settled on. Same published cents, different last
#: bit. Measured worst 4.5e-13 on a ~$2,000 Elliott hour (~2e-16 relative, one
#: ULP). The decisive test is ``identical_at_parquet_precision`` -- the parquet
#: stores float32, where the two routes agree exactly -- not this tolerance.
FLOAT_NOISE = 1e-9

#: Operating days sampled from the committed years, and why each is in.
SAMPLE_DAYS: dict[str, str] = {
    "2019-01-21": "MLK-day winter cold snap; 2019 is the locked-test year",
    "2020-03-08": "spring-forward: 23 published hours",
    "2021-11-07": "fall-back: 25 published hours, '02X' repeated hour",
    "2022-02-04": "ordinary winter day",
    "2022-12-24": "Winter Storm Elliott -- inside 2022's 117-hour RT tail",
    "2023-07-04": "ordinary summer day, in-sample",
    "2024-02-29": "leap day -- exists pre-densification, dropped by the 8760 calendar",
    "2025-01-22": "January 2025 cold snap, in-sample",
    "2025-06-24": "June 2025 heat event, in-sample",
    # The DST days of BOTH workbook vintages. ISO-NE changed the SMD workbook
    # shape: 2018-2023 publish a flat 24 rows on every day (DST-naive), while
    # 2024-2025 publish the true 23 / 25. Sampling both vintages is what
    # separates "the daily-report route disagrees" from "the OLD WORKBOOK
    # disagrees with the market" -- see the assessment's route-equivalence
    # section.
    "2025-03-09": "spring-forward, 23-row workbook vintage",
    "2025-11-02": "fall-back, 25-row workbook vintage",
    "2024-03-10": "spring-forward, 23-row workbook vintage",
    "2024-11-03": "fall-back, 25-row workbook vintage",
    "2023-11-05": "fall-back, FLAT-24 workbook vintage (in-sample year)",
    "2019-11-03": "fall-back, FLAT-24 workbook vintage (locked-test year)",
}

#: SMD sheet -> the model zone it folds into, inverted from the producer's map
#: so a per-sheet comparison can be reported by zone as well.
SHEET_TO_ZONE = {
    sheet: zone for zone, sheets in dal.NEISO_ZONE_MAP.items() for sheet in sheets
}


def workbook_rows_per_date(year: int) -> dict[str, int]:
    """Count the SMD workbook's RAW published hub rows per calendar date.

    The raw count -- not the count of derived instants -- is what separates the
    two workbook vintages. On a spring-forward day the flat-24 vintage publishes
    24 rows for a 23-hour day; the producer's positional clock spills the 24th
    into the next local date, so counting derived instants finds 23 and the
    defect hides. Counting what the file actually published exposes it.
    """
    import openpyxl

    path = dal.LMP_DIR / "NEISO" / f"{year}_smd_hourly.xlsx"
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    rows = wb[dal.NEISO_HUB_SHEET].iter_rows(values_only=True)
    next(rows, None)  # header
    counts: dict[str, int] = defaultdict(int)
    for r in rows:
        if r is None or r[0] is None or r[1] is None:
            continue
        if not str(r[1]).strip()[:2].isdigit():
            continue
        counts[f"{pd.Timestamp(r[0]).normalize():%Y-%m-%d}"] += 1
    wb.close()
    return dict(counts)


def load_sample(sample_dir: Path) -> dict[int, list[dict]]:
    """Load the fetched daily-report reductions, grouped by year."""
    by_year: dict[int, list[dict]] = defaultdict(list)
    for path in sorted(Path(sample_dir).glob("NEISO_smd_zonal_lmp_*.csv")):
        with path.open(newline="") as f:
            for r in csv.DictReader(f):
                by_year[int(r["date"][:4])].append(r)
    return dict(by_year)


def route_frame(rows: list[dict]) -> dict[str, pd.DataFrame]:
    """Rebuild per-SMD-sheet hourly series from daily-report rows.

    Applies the SAME positional clock as
    ``derive_actual_lmp._neiso_sheet_series``: within an operating day the k-th
    published row begins exactly k real hours after that day's (never
    ambiguous) local midnight. ``seq`` carries k directly.
    """
    out: dict[str, dict[str, dict]] = {"da": defaultdict(dict), "rt": defaultdict(dict)}
    for r in rows:
        day_start = (
            pd.Timestamp(r["date"]).tz_localize(dal._EASTERN_TZ).tz_convert("UTC")
        )
        ts = day_start + pd.Timedelta(hours=int(r["seq"]))
        sheet = SMD_LOCATIONS[r["location_id"]]
        out["da"][sheet][ts] = float(r["da_lmp"])
        out["rt"][sheet][ts] = float(r["rt_lmp"])
    return {
        kind: pd.DataFrame({sheet: pd.Series(v) for sheet, v in sheets.items()})
        for kind, sheets in out.items()
    }


def compare(sample_dir: Path) -> dict:
    """Compare both routes on every sampled day; return the machine record."""
    by_year = load_sample(sample_dir)
    days: list[dict] = []
    worst = 0.0
    worst_hub = 0.0
    total_cells = 0
    f32_bad = 0
    for year in sorted(by_year):
        rows = by_year[year]
        route = route_frame(rows)
        book = {k: dal.neiso_zone_hourly(year, k) for k in ("da", "rt")}
        if book["da"] is None or book["rt"] is None:
            days.append({"year": year, "status": "NO WORKBOOK -- skipped"})
            continue
        raw_counts = workbook_rows_per_date(year)
        # The workbook path folds SMD sheets into model zones; rebuild the same
        # fold from the daily-report side so the comparison is like for like.
        for day in sorted({r["date"] for r in rows}):
            rec: dict = {"day": day, "why": SAMPLE_DAYS.get(day, ""), "cells": {}}
            # Classify the day by SHAPE before comparing values. ISO-NE changed
            # the SMD workbook: 2018-2023 publish a flat 24 rows on every
            # calendar day, DST or not, while 2024-2025 (and the daily reports
            # in every year) publish the true 23 on spring-forward and 25 on
            # fall-back. When the two sources disagree on how many hours the day
            # HAD, they cannot agree hour-for-hour and the mismatch is a
            # property of the workbook vintage, not of the route -- so the
            # equivalence verdict is taken over shape-agreeing days and the
            # rest are reported separately as the workbook-shape defect.
            book_hours = raw_counts.get(day, 0)
            report_hours = len({r["seq"] for r in rows if r["date"] == day})
            rec["book_hours"] = book_hours
            rec["report_hours"] = report_hours
            rec["shape_agrees"] = bool(book_hours == report_hours)
            for kind in ("da", "rt"):
                r_sheets = route[kind]
                folded = {
                    z: r_sheets[[s for s in sheets if s in r_sheets.columns]].mean(
                        axis=1
                    )
                    for z, sheets in dal.NEISO_ZONE_MAP.items()
                }
                folded["hub"] = r_sheets[dal.NEISO_HUB_SHEET]
                cmp_frame = pd.DataFrame(folded)
                b = book[kind]
                idx = cmp_frame.index.intersection(b.index)
                idx = idx[idx.tz_convert(dal._EASTERN_TZ).strftime("%Y-%m-%d") == day]
                cols = [c for c in cmp_frame.columns if c in b.columns]
                a_vals = cmp_frame.loc[idx, cols]
                b_vals = b.loc[idx, cols]
                diff = (a_vals - b_vals).abs()
                n = int(diff.size)
                mx = float(diff.to_numpy().max()) if n else 0.0
                # The hub is tracked on its own because it is the ONLY column
                # the committed parquet and the C3c tail criterion read.
                #
                # Neither route is bit-exact against the other in float64, and
                # the reason is the WORKBOOK's storage rather than a price
                # disagreement: openpyxl hands back the doubles Excel stored
                # (16.580000000000002, 8.040000000000001), while the CSV
                # publishes the decimal ISO-NE settled on and it parses to the
                # nearest double. Same published cents, different last bit. The
                # residual is <= 1.2e-13 $/MWh, and the parquet stores float32,
                # so ``f32_mismatch`` -- equality at the precision that actually
                # ships -- is the decisive test, not the float64 delta.
                hub_mx = (
                    float(diff["hub"].max()) if "hub" in diff.columns and n else 0.0
                )
                f32_mismatch = (
                    int(
                        (
                            a_vals.to_numpy("float32") != b_vals.to_numpy("float32")
                        ).sum()
                    )
                    if n
                    else 0
                )
                if rec["shape_agrees"]:
                    worst = max(worst, mx)
                    worst_hub = max(worst_hub, hub_mx)
                    total_cells += n
                    f32_bad += f32_mismatch
                rec["cells"][kind] = {
                    "hours": int(len(idx)),
                    "columns": cols,
                    "compared": n,
                    "max_abs_diff": mx,
                    "max_abs_diff_hub": hub_mx,
                    "float32_mismatches": f32_mismatch,
                }
            days.append(rec)
    shape_mismatch = [d for d in days if d.get("shape_agrees") is False]
    return {
        "note": (
            "Equivalence of the ISO-NE daily historical-report LMP route "
            "(scripts/data/fetch_neiso_smd_zonal_lmp.py) against the committed "
            "SMD workbook route (derive_actual_lmp.neiso_zone_hourly), compared "
            "pre-densification on sampled operating days of the committed "
            "years. The verdict is taken over days where the two sources agree "
            "on how many hours the day HAD; 0.0 there means the two routes are "
            "ONE input, so carrying H1-2026 on the daily-report route does not "
            "year-gate the input (rule 22 as amended 2026-08-06). Days listed "
            "under shape_mismatch are the SMD workbook's DST defect, not a "
            "route difference: the 2018-2023 workbook vintage publishes a flat "
            "24 rows on every day, so on a 23-hour or 25-hour operating day it "
            "cannot align with the market's own published hours. No year "
            "solved, scored or registered."
        ),
        "sample_rationale": SAMPLE_DAYS,
        "days": days,
        "totals": {
            "cells_compared_shape_agreeing": total_cells,
            "worst_abs_diff_shape_agreeing": worst,
            "worst_abs_diff_hub_shape_agreeing": worst_hub,
            "float32_mismatches_shape_agreeing": f32_bad,
            "identical_at_parquet_precision": bool(f32_bad == 0),
            "float_noise_tolerance": FLOAT_NOISE,
            "routes_equivalent": bool(worst <= FLOAT_NOISE),
            "shape_mismatch_days": [d["day"] for d in shape_mismatch],
            "shape_mismatch_detail": [
                {
                    "day": d["day"],
                    "workbook_hours": d["book_hours"],
                    "market_hours": d["report_hours"],
                }
                for d in shape_mismatch
            ],
        },
    }


def main(argv: list[str] | None = None) -> int:
    """Run the comparison and write the machine record."""
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample-dir", type=Path, required=True)
    args = p.parse_args(argv)
    rec = compare(args.sample_dir)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    for d in rec["days"]:
        if "cells" not in d:
            print(f"{d.get('year')}: {d.get('status')}")
            continue
        bits = " ".join(
            f"{k}: {c['hours']}h x{len(c['columns'])} maxdiff {c['max_abs_diff']}"
            for k, c in d["cells"].items()
        )
        flag = "" if d["shape_agrees"] else "  <- WORKBOOK SHAPE DEFECT"
        print(
            f"{d['day']}  wb {d['book_hours']}h / market {d['report_hours']}h  "
            f"{bits}{flag}"
        )
    t = rec["totals"]
    print(
        f"\nshape-agreeing days: {t['cells_compared_shape_agreeing']} cells, "
        f"worst float64 |diff| = {t['worst_abs_diff_shape_agreeing']:.3e} "
        f"(hub {t['worst_abs_diff_hub_shape_agreeing']:.3e}); "
        f"float32 mismatches {t['float32_mismatches_shape_agreeing']} -> "
        f"identical at parquet precision: {t['identical_at_parquet_precision']}"
    )
    if t["shape_mismatch_days"]:
        print(
            "workbook-shape defect (flat-24 vintage on a DST day): "
            + ", ".join(
                f"{d['day']} wb {d['workbook_hours']}h vs market {d['market_hours']}h"
                for d in t["shape_mismatch_detail"]
            )
        )
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0 if t["routes_equivalent"] else 1


if __name__ == "__main__":
    sys.exit(main())

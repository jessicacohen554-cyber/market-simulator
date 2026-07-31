"""NYISO out-of-training LMP bench: RE-DERIVE 2018-2022 + H1-2026 on the FIXED clock.

Owner-authorized 2026-07-31 NYISO out-of-training DATA READINESS (rule 22
Option-2 channel-1 intake; session-logged in
``frontend/data/backcast/calibration-complete.json`` ``intake_log``). **No LP is
constructed, solved, or scored** — this only re-derives a committed bench
artifact from its raw sources.

Why this exists (the debt this pays off)
----------------------------------------
The NYISO 2018-2022 and H1-2026 blocks of
``actual_lmp_hourly_NYISO.parquet`` / ``actual_lmp.json`` were built by the
2026-07-12 and 2026-07-13 intake landers, i.e. **before** the 2026-07-15
all-ISO scoring-clock fix. When the in-sample 2023-2025 rows were rebuilt
chronologically that day, the out-of-training blocks were deliberately
preserved byte-frozen — so they still carry the OLD *prevailing-clock*
indexing, in which every hourly comparison over the ~5,600 DST hours of a year
is paired one real hour off (the artifact diagnosed in
``docs/DIAGNOSIS-ercot-lmp-clock-artifact-and-summer-residuals-2026-07.md``
§1). The register carries this as a standing caveat: *"Before any authorized
validation-year scoring, these blocks must be re-derived with the fixed
``derive_actual_lmp.py``."* This script is that re-derivation.

Unlike the two landers it supersedes (``holdout_intake_nyiso_2022_lmp.py``,
``holdout_intake_nyiso_2018_2021_h1_2026_lmp.py``), which only APPENDED years
not already present, this one **replaces** the named years in place. The
direction of the guard is therefore inverted: the out-of-training rows are
*expected* to change, and the IN-SAMPLE 2023-2025 rows (plus every other ISO's
block) are what must come through byte-identical.

Sources: the same ``mis.nyiso.com`` monthly zips the committed years use — DA
``damlbmp/<YYYYMM>01damlbmp_zone_csv.zip`` staged into the builder's outer
container ``lmp-data/NYISO/NYISO_zonal_hourly.zip``, RT
``realtime/<YYYYMM>01realtime_zone_csv.zip`` flat beside it. Same builder
(``derive_actual_lmp.build``), same recipe, one changed input: the clock.

2026 is H1 only (Jan-Jun) — ``mis.nyiso.com`` publishes no H2-2026 — so its
coverage gate is restricted to that window and Jul-Dec stay NaN, exactly the
convention the committed 2026 block already uses.

Usage::

    python scripts/archive/reclock_nyiso_holdout_lmp_2026_07.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
sys.path.insert(0, str(REPO / "src"))

from derive_actual_lmp import OUT, build  # noqa: E402
from market_sim.config import paths  # noqa: E402

HOURLY = paths.CALIBRATION_DIR / "actual_lmp_hourly_NYISO.parquet"
FULL_YEARS = (2018, 2019, 2020, 2021, 2022)
PARTIAL_YEAR = 2026
PARTIAL_YEAR_MONTHS = 6  # H1 only
TARGET_YEARS = FULL_YEARS + (PARTIAL_YEAR,)
# The in-sample training window — the rows this script must NOT touch.
IN_SAMPLE = (2023, 2024, 2025)

_MONTH_OF_HOUR = pd.Series(
    pd.date_range("2001-01-01", periods=8760, freq="h")
).dt.month.to_numpy()


def _coverage(block: pd.DataFrame, kind: str, months: int | None) -> float:
    """Fraction of non-NaN hours in ``kind``, restricted to Jan..``months``."""
    arr = block[kind].to_numpy(float)
    if months is not None:
        arr = arr[_MONTH_OF_HOUR <= months]
    return float(np.mean(~np.isnan(arr)))


def _clock_delta(old: pd.DataFrame, new: pd.DataFrame, year: int) -> str:
    """One-line description of how far the re-clocked block moved."""
    o = old[old["year"] == year].sort_values("hour").reset_index(drop=True)
    n = new[new["year"] == year].sort_values("hour").reset_index(drop=True)
    parts = []
    for kind in ("da", "rt"):
        a, b = o[kind].to_numpy(float), n[kind].to_numpy(float)
        both = ~np.isnan(a) & ~np.isnan(b)
        moved = int((a[both] != b[both]).sum())
        mae = float(np.abs(a[both] - b[both]).mean()) if both.any() else float("nan")
        parts.append(
            f"{kind}: {moved:,}/{int(both.sum()):,} hours moved, "
            f"mean |Δ| ${mae:.2f}, annual ${np.nanmean(a):.2f}->${np.nanmean(b):.2f}"
        )
    return f"  {year} " + " | ".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="build + report, no write")
    args = ap.parse_args()

    committed_hourly = pd.read_parquet(HOURLY)
    committed_json = json.loads(OUT.read_text())
    missing = [y for y in TARGET_YEARS if y not in set(committed_hourly["year"])]
    if missing:
        print(f"NOTE: {missing} absent from the committed parquet — landing fresh")

    table, hourly = build(list(TARGET_YEARS), isos=["NYISO"])
    fresh = hourly["NYISO"]

    blocks, recs = [], {}
    for year in TARGET_YEARS:
        rec = table.get("NYISO", {}).get(str(year))
        if rec is None:
            return _fail(f"builder produced no NYISO {year} record — sources unstaged?")
        block = fresh[fresh["year"] == year]
        months = PARTIAL_YEAR_MONTHS if year == PARTIAL_YEAR else None
        gate = 0.95 if year == PARTIAL_YEAR else 0.99
        for kind in ("da", "rt"):
            cov = _coverage(block, kind, months)
            if cov < gate:
                return _fail(
                    f"{year} {kind} coverage {cov:.3f} < {gate} "
                    f"(window months<={months or 12}) — incomplete sources"
                )
        blocks.append(block)
        recs[year] = rec

    print("\nclock re-derivation deltas (old prevailing -> new chronological):")
    for year in TARGET_YEARS:
        if year in set(committed_hourly["year"]):
            print(_clock_delta(committed_hourly, fresh, year))

    # ── parquet: replace the target years, in-sample rows byte-frozen ───────
    key = ["year", "hour"]
    keep = committed_hourly[~committed_hourly["year"].isin(TARGET_YEARS)]
    merged = (
        pd.concat([keep, *blocks], ignore_index=True)
        .sort_values(key)
        .reset_index(drop=True)
    )
    before_in = (
        committed_hourly[committed_hourly["year"].isin(IN_SAMPLE)]
        .set_index(key)
        .sort_index()
    )
    after_in = merged.set_index(key).sort_index().loc[before_in.index]
    if not before_in.equals(after_in):
        return _fail("in-sample 2023-2025 rows would change — refusing to write")
    got_years = sorted(set(merged["year"]))
    if len(merged) != 8760 * len(got_years):
        return _fail(f"non-dense merge: {len(merged)} rows over {got_years}")
    if args.dry_run:
        print("\n--dry-run: guards passed, nothing written")
        return 0

    merged.to_parquet(HOURLY, index=False)
    reread = pd.read_parquet(HOURLY)
    assert reread.set_index(key).sort_index().loc[before_in.index].equals(before_in), (
        "post-write verification failed"
    )
    print(f"\nwrote {HOURLY} ({len(merged):,} rows, years {got_years})")

    # ── JSON: replace the target NYISO years; everything else frozen ────────
    def _snap(tbl: dict, skip_nyiso: set[str]) -> dict:
        out = {
            iso: json.dumps(v, sort_keys=True)
            for iso, v in tbl.items()
            if iso != "NYISO"
        }
        out.update(
            {
                f"NYISO/{y}": json.dumps(v, sort_keys=True)
                for y, v in tbl["NYISO"].items()
                if y not in skip_nyiso
            }
        )
        return out

    skip = {str(y) for y in TARGET_YEARS}
    before = _snap(committed_json, skip)
    nyiso = dict(committed_json["NYISO"])
    for year, rec in recs.items():
        nyiso[str(year)] = rec
    committed_json["NYISO"] = {y: nyiso[y] for y in sorted(nyiso, key=int)}
    if _snap(committed_json, skip) != before:
        return _fail("a frozen JSON block changed — refusing to write")
    OUT.write_text(json.dumps(committed_json, indent=2) + "\n")
    print(f"wrote {OUT} (NYISO years {list(committed_json['NYISO'])})")
    return 0


def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

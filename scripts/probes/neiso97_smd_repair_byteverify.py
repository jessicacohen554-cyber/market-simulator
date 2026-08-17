"""Byte-verify the neiso-97 SMD DST-naive repair per the PJM finding's 2a protocol.

Audit row O8 (``docs/audit/third-party-audit-2026-08.md`` section 8), executed
under the owner-signed neiso-97 charter. Compares the REPAIRED
``actual_lmp_hourly_NEISO.parquet`` against a pristine copy of the committed
pre-repair blob, cell for cell, and proves five things:

1. **Row grid / dtypes / column order unchanged**; the 2024, 2025 and 2026 year
   blocks (true-shape workbook vintage / report route) are BYTE-IDENTICAL.
2. **Every changed cell sits inside the measured mechanism window** — the DST
   days of 2018-2023 plus the spring spill slot; zero changes anywhere else
   (every true-shape day still reproduces from the workbook byte-for-byte).
3. **Value preservation**: every displaced cell in the repaired blob equals the
   PRISTINE value at the defective offset the flat-24 clock had put it at —
   spring position p (1..22) holds pristine position p+1; fall position p
   (3..24) holds pristine position p-1; position 0 of both days is unchanged.
4. **The cells a re-placement cannot recover carry the market's published
   values**: the fall-back repeated hour's two instances equal the daily
   historical-report truth (committed ``smd-zonal-lmp`` CSVs) at the float32
   precision the parquet stores, replacing the vintage's collapsed mean.
5. **NaN accounting**: exactly one NaN per market-year (the fall-back lost
   hour) is FILLED with the measured value in 2018-2023; zero NaNs are
   introduced anywhere; 2024+ NaN patterns are untouched.

Output: ``results/calibration/_neiso97_smd_repair_byteverify.json``; exits
non-zero on any failed check. NO YEAR IS SOLVED, SCORED OR REGISTERED.

Usage:
    uv run python scripts/probes/neiso97_smd_repair_byteverify.py \
        --pristine <copy of the pre-repair parquet>
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from scripts.data import derive_actual_lmp as dal  # noqa: E402

OUT = REPO / "results" / "calibration" / "_neiso97_smd_repair_byteverify.json"

OLD_VINTAGE = (2018, 2019, 2020, 2021, 2022, 2023)
NEW_YEARS = (2024, 2025, 2026)


def load_year(path: Path, year: int) -> dict[str, np.ndarray]:
    """One year's dense hub da/rt arrays (float32 as stored)."""
    df = pd.read_parquet(path)
    df = df[df["year"] == year].sort_values("hour")
    return {"da": df["da"].to_numpy(), "rt": df["rt"].to_numpy(), "n": len(df)}


def dst_days(year: int) -> tuple[str, str]:
    """(spring-forward, fall-back) dates for ``year`` from the tz database."""
    days = pd.date_range(f"{year}-01-01", f"{year+1}-01-01", freq="D")
    starts = days.tz_localize(dal._EASTERN_TZ)
    hours = ((starts[1:] - starts[:-1]) / pd.Timedelta(hours=1)).astype(int)
    spring = [f"{d:%Y-%m-%d}" for d, h in zip(days[:-1], hours) if h == 23]
    fall = [f"{d:%Y-%m-%d}" for d, h in zip(days[:-1], hours) if h == 25]
    return spring[0], fall[0]


def slot(year: int, date: str, pos: int) -> int:
    """Std-clock 8760 slot of ``date``'s ``pos``-th real hour."""
    inst = pd.Timestamp(date).tz_localize(dal._EASTERN_TZ).tz_convert(
        "UTC"
    ) + pd.Timedelta(hours=pos)
    return int(
        dal._std_hour_index(pd.DatetimeIndex([inst]), year, dal._STD_TZ["NEISO"])[0]
    )


def truth_pair(year: int, fall: str) -> dict[str, tuple[float, float]]:
    """The fall-back repeated hour's two published hub instances (da & rt)."""
    path = dal.NEISO_REPORT_DIR / f"NEISO_smd_zonal_lmp_{year}.csv"
    rows = {}
    with path.open(newline="") as f:
        for r in csv.DictReader(f):
            if r["date"] == fall and r["location_id"] == "4000":
                rows[int(r["seq"])] = (float(r["da_lmp"]), float(r["rt_lmp"]))
    return {
        "da": (rows[1][0], rows[2][0]),
        "rt": (rows[1][1], rows[2][1]),
    }


def eq32(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Elementwise float32 equality with NaN == NaN."""
    a32, b32 = a.astype(np.float32), b.astype(np.float32)
    return (a32 == b32) | (np.isnan(a32) & np.isnan(b32))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pristine", type=Path, required=True)
    args = p.parse_args()
    repaired_path = dal.HOURLY_OUT / "actual_lmp_hourly_NEISO.parquet"

    res: dict = {"checks": {}, "per_year": {}}
    ok = True

    def check(name: str, passed: bool, detail=None):
        nonlocal ok
        res["checks"][name] = {"pass": bool(passed), "detail": detail}
        if not passed:
            ok = False

    pf = pd.read_parquet(args.pristine)
    rf = pd.read_parquet(repaired_path)
    check(
        "grid_and_dtypes",
        list(pf.columns) == list(rf.columns)
        and len(pf) == len(rf)
        and all(pf[c].dtype == rf[c].dtype for c in pf.columns)
        and (pf["year"].to_numpy() == rf["year"].to_numpy()).all()
        and (pf["hour"].to_numpy() == rf["hour"].to_numpy()).all(),
        {"rows": len(rf), "cols": list(map(str, rf.columns))},
    )

    for year in NEW_YEARS:
        a, b = load_year(args.pristine, year), load_year(repaired_path, year)
        ident = bool(eq32(a["da"], b["da"]).all() and eq32(a["rt"], b["rt"]).all())
        check(f"{year}_byte_identical", ident)

    for year in OLD_VINTAGE:
        a, b = load_year(args.pristine, year), load_year(repaired_path, year)
        spring, fall = dst_days(year)
        sp0 = slot(year, spring, 0)
        spill = slot(year, spring, 22) + 1
        fb0 = slot(year, fall, 0)
        pair = truth_pair(year, fall)
        expected = (
            {slot(year, spring, q) for q in range(1, 23)}
            | {spill}
            | {slot(year, fall, q) for q in range(1, 25)}
        )
        yr: dict = {}
        for kind in ("da", "rt"):
            pa, ra = a[kind], b[kind]
            changed = set(np.flatnonzero(~eq32(pa, ra)).tolist())
            outside = sorted(changed - expected)
            # 3. value preservation at the corrected offsets. Spring position
            # 22's defective offset is the SPILL slot, where the pristine blob
            # stored the spilled value already AVERAGED with the next day's
            # true first hour (``_densify_std`` folds duplicate instants), so
            # positions 1..21 check the direct offset and position 22 + the
            # spill slot check the collision decomposition instead:
            # pristine[spill] == mean(repaired[pos 22], repaired[spill]).
            bad_offsets = []
            for q in range(1, 22):  # spring positions 1..21 <- pristine p+1
                s_new, s_old = slot(year, spring, q), slot(year, spring, q) + 1
                if not eq32(ra[[s_new]], pa[[s_old]])[0]:
                    bad_offsets.append(("spring", q))
            s22 = slot(year, spring, 22)
            recon = (float(ra[s22]) + float(ra[spill])) / 2.0
            if abs(float(pa[spill]) - recon) > 0.005 + 1e-9:
                bad_offsets.append(("spring_collision_decomposition", recon))
            for q in range(3, 25):  # fall positions 3..24 <- pristine p-1
                s_new, s_old = slot(year, fall, q), slot(year, fall, q) - 1
                if not eq32(ra[[s_new]], pa[[s_old]])[0]:
                    bad_offsets.append(("fall", q))
            anchors_ok = bool(
                eq32(ra[[sp0]], pa[[sp0]])[0] and eq32(ra[[fb0]], pa[[fb0]])[0]
            )
            # 4. the unrecoverable pair == published truth (float32)
            s1, s2 = slot(year, fall, 1), slot(year, fall, 2)
            pair_ok = bool(
                np.float32(ra[s1]) == np.float32(pair[kind][0])
                and np.float32(ra[s2]) == np.float32(pair[kind][1])
            )
            # 5. NaN accounting
            nan_p, nan_r = np.isnan(pa), np.isnan(ra)
            filled = sorted(np.flatnonzero(nan_p & ~nan_r).tolist())
            introduced = sorted(np.flatnonzero(~nan_p & nan_r).tolist())
            lost_slot = slot(year, fall, 24)
            yr[kind] = {
                "cells_changed": len(changed),
                "changed_outside_mechanism": outside,
                "offset_preservation_failures": bad_offsets,
                "anchors_unchanged": anchors_ok,
                "pair_matches_published_truth": pair_ok,
                "pair_published": pair[kind],
                "pristine_pair_mean": round(float(pa[s1]), 2),
                "nan_filled": filled,
                "nan_introduced": introduced,
            }
            check(
                f"{year}_{kind}",
                not outside
                and not bad_offsets
                and anchors_ok
                and pair_ok
                and filled == [lost_slot]
                and not introduced,
                yr[kind],
            )
        res["per_year"][year] = yr

    res["verdict"] = "PASS" if ok else "FAIL"
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n")
    print(json.dumps({k: v["pass"] for k, v in res["checks"].items()}, indent=1))
    print("VERDICT:", res["verdict"])
    print(f"wrote {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Extend NEISO holdout-year data readiness from 2022-only to 2018-2021 (+ the
2026 zone-temp split already on disk), generalizing
``scripts/archive/land_neiso_2022_readiness.py``'s MERGE-not-replace pattern.

CLAUDE.md rule 22 (Option 2); owner authorization 2026-07-13, logged in
``frontend/data/backcast/calibration-complete.json`` intake_log: *"This data
can literally be collected for all years - we're not running anything on it.
Fetch it all at once for 2018-2022 and first half 2026 if available."*

Data-readiness only - **no LP is constructed, solved, or scored** (the G-19
one-shot execution HOLD stays in force). Every write asserts the pre-existing
2023-2025 (and, for outages/zone_temp/lw_temp, the just-landed 2022) rows
byte-frozen before writing - MERGE, never replace.

Artifacts landed per holdout year in ``YEARS`` (default 2018-2021):

  * ``zone_temp``  neiso_zone_temp_daily.csv        - append committed NOAA h1/h2 splits.
  * ``lw_temp``    neiso_load_weighted_temp_daily.csv - re-derive via the frozen
                   load-weighting recipe (``derive_neiso_temp_reliability_floor``).
  * ``calref``     calibration_reference.json isos.NEISO.<year> splice +
                   NEISO_<year>_renewable_capacity.csv.
  * ``outages``    campd-unit-outages-NEISO.csv - append ONLY <year>-start windows
                   from the HEAD-vintage detector (same DEGRADED vintage-asymmetry
                   caveat as the 2022 windows - not resolved here).

``actual_lmp`` / ``actual_tail`` are handled separately (``--lmp-years``) since
they need an ISO-NE SMD hourly workbook on disk under ``data/raw/lmp-data/NEISO/``;
2020-2021 have one (copied from the pre-existing root-level file), 2018-2019 do
not (register MISSING, no fabrication per rule 14).

Run:
    uv run python scripts/archive/land_neiso_holdout_multiyear.py                # all years, all artifacts
    uv run python scripts/archive/land_neiso_holdout_multiyear.py --dry-run
    uv run python scripts/archive/land_neiso_holdout_multiyear.py --only outages --years 2019 2020
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

sys.path.insert(0, str(REPO / "scripts" / "data"))
RAW = REPO / "data" / "raw"
NEISO_WEATHER = RAW / "neiso-weather"
VALIDATION = RAW / "_validation-source"
LMP_DIR = RAW / "lmp-data"

YEARS = (2018, 2019, 2020, 2021)
LMP_YEARS = (2020, 2021)  # 2018-2019: no ISO-NE SMD hourly workbook on disk


def _append_frozen_csv(path: Path, new_block: str, *, dry_run: bool) -> str:
    old = path.read_text()
    if not old.endswith("\n"):
        old += "\n"
    new = old + new_block
    assert new.startswith(old), "in-sample prefix would change - refusing to write"
    if not dry_run:
        path.write_text(new)
    added = new_block.count("\n")
    return f"{path.relative_to(REPO)}: +{added} rows"


def land_zone_temp(year: int, dry_run: bool) -> str:
    path = NEISO_WEATHER / "neiso_zone_temp_daily.csv"
    existing = pd.read_csv(path)
    if (existing["date"].astype(str).str[:4] == str(year)).any():
        return f"{path.relative_to(REPO)}: {year} already present - skipped"
    parts = [
        pd.read_csv(NEISO_WEATHER / f"neiso_zone_temp_daily_{year}h1.csv"),
        pd.read_csv(NEISO_WEATHER / f"neiso_zone_temp_daily_{year}h2.csv"),
    ]
    block = pd.concat(parts, ignore_index=True)
    assert list(block.columns) == list(existing.columns), "schema mismatch vs committed"
    assert (block["date"].astype(str).str[:4] == str(year)).all()
    block = block.sort_values(["zone", "date"]).reset_index(drop=True)
    text = block.to_csv(index=False, header=False)
    return _append_frozen_csv(path, text, dry_run=dry_run)


def land_lw_temp(year: int, dry_run: bool) -> str:
    path = NEISO_WEATHER / "neiso_load_weighted_temp_daily.csv"
    existing = pd.read_csv(path)
    if (existing["date"].astype(str).str[:4] == str(year)).any():
        return f"{path.relative_to(REPO)}: {year} already present - skipped"
    import derive_neiso_temp_reliability_floor as dn

    wx = dn.fetch_neiso_temp(f"{year}-01-01", f"{year}-12-31")
    out = wx.reset_index()
    out.columns = ["date", "tmax_c", "tmin_c"]
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out = out.sort_values("date")
    assert (out["date"].str[:4] == str(year)).all()
    assert list(existing.columns) == ["date", "tmax_c", "tmin_c"]
    text = out.to_csv(index=False, header=False)
    return _append_frozen_csv(path, text, dry_run=dry_run)


def land_calref(year: int, dry_run: bool) -> str:
    calref = VALIDATION / "calibration_reference.json"
    renew = VALIDATION / f"NEISO_{year}_renewable_capacity.csv"
    committed = json.loads(calref.read_text())
    have_year = str(year) in committed["isos"]["NEISO"]
    have_csv = renew.exists()
    if have_year and have_csv:
        return f"{calref.relative_to(REPO)}: NEISO {year} + renewable CSV already present - skipped"

    import build_calibration_reference as bcr

    with tempfile.TemporaryDirectory(dir=str(REPO)) as td:
        bcr.OUTPUT_DIR = Path(td)
        bcr.build_reference()
        rebuilt = json.loads((Path(td) / "calibration_reference.json").read_text())
        block = rebuilt["isos"]["NEISO"].get(str(year))
        if block is None:
            return f"{calref.relative_to(REPO)}: NEISO {year} not producible by build_calibration_reference - skipped (MISSING)"
        tmp_csv = Path(td) / f"NEISO_{year}_renewable_capacity.csv"
        csv_bytes = tmp_csv.read_bytes() if tmp_csv.exists() else None

    msgs = []
    if not have_csv and csv_bytes is not None:
        if not dry_run:
            renew.write_bytes(csv_bytes)
        rows = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert (rows["iso"] == "NEISO").all() and (rows["year"] == year).all()
        verb = "would write" if dry_run else "wrote"
        msgs.append(f"{renew.relative_to(REPO)}: {verb} {len(rows)} rows (new file)")
    else:
        msgs.append(
            f"{renew.relative_to(REPO)}: already present or unavailable - skipped"
        )

    if not have_year:
        original = calref.read_text()
        data = json.loads(original)
        data["isos"]["NEISO"][str(year)] = block

        def _dump(obj: dict) -> str:
            return json.dumps(obj, indent=2, sort_keys=True) + "\n"

        proof = json.loads(_dump(data))
        proof["isos"]["NEISO"].pop(str(year))
        assert _dump(proof) == original, "calref splice would perturb frozen content"
        if not dry_run:
            calref.write_text(_dump(data))
        msgs.append(
            f"{calref.relative_to(REPO)}: spliced isos.NEISO.{year} (all else frozen)"
        )
    else:
        msgs.append(
            f"{calref.relative_to(REPO)}: NEISO {year} already present - skipped"
        )
    return "; ".join(msgs)


def _derive_outages(dco, years: list[int]) -> pd.DataFrame:
    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "outages.csv"
        argv = [
            "derive_campd_unit_outages.py",
            "--iso",
            "NEISO",
            "--years",
            *[str(y) for y in years],
            "--out",
            str(out),
        ]
        old_argv = sys.argv
        try:
            sys.argv = argv
            dco.main()
        finally:
            sys.argv = old_argv
        return pd.read_csv(out)


def land_outages(year: int, dry_run: bool) -> str:
    path = RAW / "campd-unit-outages-NEISO.csv"
    committed = pd.read_csv(path)
    n_committed = len(committed)
    if (committed["outage_start"].astype(str).str[:4] == str(year)).any():
        return f"{path.relative_to(REPO)}: {year} windows already present - skipped"

    import derive_campd_unit_outages as dco

    fresh = _derive_outages(dco, [year, 2023, 2024, 2025])
    block = fresh[fresh["outage_start"].astype(str).str[:4] == str(year)].copy()
    assert list(block.columns) == list(committed.columns), "outage schema mismatch"
    text = block.to_csv(index=False, header=False)
    status = _append_frozen_csv(path, text, dry_run=dry_run)
    return (
        f"{status} [committed {n_committed} frozen; +{len(block)} {year}-start windows]"
    )


def land_actual_lmp(year: int, dry_run: bool) -> str:
    path = VALIDATION / "actual_lmp.json"
    committed = json.loads(path.read_text())
    if str(year) in committed["NEISO"]:
        return f"{path.relative_to(REPO)}: NEISO {year} already present - skipped"
    smd = LMP_DIR / "NEISO" / f"{year}_smd_hourly.xlsx"
    if not smd.exists():
        return f"NEISO {year}: no ISO-NE SMD hourly workbook on disk - skipped (MISSING, register)"

    import derive_actual_lmp as dal

    with tempfile.TemporaryDirectory() as td:
        dal.OUT = Path(td) / "actual_lmp.json"
        dal.HOURLY_OUT = Path(td)
        table, hourly = dal.build([year], isos=["NEISO"])
        block_hourly = hourly["NEISO"]
        dal.OUT.write_text(json.dumps({"NEISO": table["NEISO"]}, indent=2) + "\n")
        dal.lw_retrofit([year], isos=["NEISO"])
        block = json.loads(dal.OUT.read_text())["NEISO"][str(year)]

    # Merge the hourly parquet (byte-frozen prefix check against every other year).
    hourly_path = VALIDATION / "actual_lmp_hourly_NEISO.parquet"
    committed_hourly = pd.read_parquet(hourly_path)
    if not dry_run:
        if year not in committed_hourly["year"].unique():
            merged_hourly = pd.concat(
                [block_hourly, committed_hourly], ignore_index=True
            )
            check = merged_hourly[merged_hourly["year"] != year].reset_index(drop=True)
            old_sorted = committed_hourly.reset_index(drop=True)
            assert check.equals(old_sorted), "in-sample hourly rows perturbed"
            merged_hourly.to_parquet(hourly_path, index=False)

    original = path.read_text()
    data = json.loads(original)
    data["NEISO"] = {str(year): block, **data["NEISO"]}

    def _dump(obj: dict) -> str:
        return json.dumps(obj, indent=2) + "\n"

    proof = json.loads(_dump(data))
    proof["NEISO"].pop(str(year))
    assert _dump(proof) == original, "actual_lmp splice would perturb frozen content"
    if not dry_run:
        path.write_text(_dump(data))
    return f"{path.relative_to(REPO)}: spliced NEISO {year} (DA {block['da']} / RT {block['rt']}); hourly parquet merged"


def land_actual_tail(year: int, dry_run: bool) -> str:
    path = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
    committed = json.loads(path.read_text())
    if str(year) in committed["isos"].get("NEISO", {}):
        return f"{path.relative_to(REPO)}: NEISO {year} already present - skipped"
    hourly_path = VALIDATION / "actual_lmp_hourly_NEISO.parquet"
    h = pd.read_parquet(hourly_path)
    if not (h["year"] == year).any():
        return f"NEISO {year}: no hourly LMP rows (actual_lmp not yet landed) - skipped"

    import derive_actual_tail as dat

    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / "actual_lmp_hourly_NEISO.parquet"
        h.to_parquet(staged, index=False)
        saved = dat.SRC_DIR
        try:
            dat.SRC_DIR = Path(td)
            full = dat.derive()
        finally:
            dat.SRC_DIR = saved
    block = full["isos"]["NEISO"][str(year)]

    original = path.read_text()
    data = json.loads(original)
    data["isos"]["NEISO"] = {str(year): block, **data["isos"]["NEISO"]}

    def _dump(obj: dict) -> str:
        return json.dumps(obj, indent=1) + "\n"

    proof = json.loads(_dump(data))
    proof["isos"]["NEISO"].pop(str(year))
    assert _dump(proof) == original, "actual_tail splice would perturb frozen content"
    if not dry_run:
        path.write_text(_dump(data))
    return f"{path.relative_to(REPO)}: spliced NEISO {year} (DA {block.get('da_gt')}h / RT {block.get('rt_gt')}h)"


ALL = ("zone_temp", "lw_temp", "calref", "outages", "actual_lmp", "actual_tail")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="+", choices=ALL, default=list(ALL))
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    handlers = {
        "zone_temp": land_zone_temp,
        "lw_temp": land_lw_temp,
        "calref": land_calref,
        "outages": land_outages,
        "actual_lmp": land_actual_lmp,
        "actual_tail": land_actual_tail,
    }
    print(f"NEISO holdout multi-year driver ({'DRY-RUN' if args.dry_run else 'WRITE'})")
    for year in sorted(args.years):
        for name in args.only:
            print(f"[{name} {year}] {handlers[name](year, args.dry_run)}")


if __name__ == "__main__":
    main()

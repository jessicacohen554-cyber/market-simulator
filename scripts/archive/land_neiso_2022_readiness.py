#!/usr/bin/env python3
"""Land the NEISO 2022 validation-holdout DATA-READINESS text/data artifacts.

One-shot, idempotent, MERGE-not-replace driver for the NEISO 2022 residual
intake (CLAUDE.md rule 22; owner authorization 2026-07-12, logged in
``frontend/data/backcast/calibration-complete.json``). It regenerates each 2022
input from its committed producer and MERGES it into the committed artifact,
**asserting every pre-existing 2023-2025 in-sample row byte-frozen before the
write** - never a replace, never a re-derivation of the in-sample rows.

This is a data-readiness step, **NOT a solve**: no LP is constructed, solved or
scored (rule 22's solve/score quarantine - the G-19 one-shot execution HOLD -
is untouched). Everything here is loader-level intake under the pushed NEISO
calibration-complete marker.

Artifacts landed (each ``--only <name>`` selectable; default = all):

  * ``zone_temp``    data/raw/neiso-weather/neiso_zone_temp_daily.csv
                     - append the committed 2022h1/h2 per-zone NOAA splits.
  * ``lw_temp``      data/raw/neiso-weather/neiso_load_weighted_temp_daily.csv
                     - 2022 load-weighted daily series, re-fetched from the six
                     NOAA GHCN stations with the frozen derive_neiso weighting.
  * ``calref``       data/raw/_validation-source/calibration_reference.json
                     (splice isos.NEISO.2022) + NEISO_2022_renewable_capacity.csv
                     - from build_calibration_reference (EIA-860/923/930/eGRID).
  * ``outages``      data/raw/campd-unit-outages-NEISO.csv
                     - append ONLY the 2022-start windows from the HEAD-vintage
                     derive_campd_unit_outages (the committed 968 stay frozen;
                     the detector-vintage asymmetry is a register DEGRADED row,
                     NOT resolved here).
  * ``actual_lmp``   data/raw/_validation-source/actual_lmp.json
                     - splice NEISO 2022 (DA 85.56 / RT 84.92) built from the
                     relocated 2022 SMD workbook + load-weighting.
  * ``actual_tail``  frontend/data/backcast/tail/actual_tail.json
                     - splice NEISO 2022 (DA 27h / RT 117h) from the hourly
                     parquet.

``actual_lmp``/``actual_tail`` need the 2022 SMD workbook resolvable under
``data/raw/lmp-data/NEISO/`` and (for the tail) the 2022 hourly parquet; the
binary lander workflow relocates/builds those first, then runs this driver.
Both are also self-sufficient locally (they build what they need under a temp
dir), so the driver doubles as the no-LP local verification harness.

Run:
    uv run python scripts/archive/land_neiso_2022_readiness.py                 # all
    uv run python scripts/archive/land_neiso_2022_readiness.py --only calref outages
    uv run python scripts/archive/land_neiso_2022_readiness.py --dry-run       # verify only
"""

from __future__ import annotations

import argparse
import json
import shutil
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
HOLDOUT_YEAR = 2022
IN_SAMPLE_YEARS = (2023, 2024, 2025)


# --------------------------------------------------------------------------- #
# Generic freeze helpers
# --------------------------------------------------------------------------- #
def _read_bytes(path: Path) -> bytes:
    return path.read_bytes()


def _append_frozen_csv(path: Path, new_block: str, *, dry_run: bool) -> str:
    """Append ``new_block`` to ``path`` with the existing bytes an exact prefix.

    The pre-existing file content becomes a byte-identical prefix of the result,
    so every in-sample row is provably frozen. ``new_block`` is the already
    formatted text of the appended rows (no header), each line newline-terminated.
    Returns a one-line status string.
    """
    old = path.read_text()
    if not old.endswith("\n"):
        old += "\n"
    new = old + new_block
    assert new.startswith(old), "in-sample prefix would change - refusing to write"
    if not dry_run:
        path.write_text(new)
    added = new_block.count("\n")
    return f"{path.relative_to(REPO)}: +{added} rows (in-sample bytes frozen as prefix)"


def _splice_json_year(
    path: Path,
    iso: str,
    year: str,
    block: dict,
    *,
    isos_container: bool,
    indent: int,
    dry_run: bool,
) -> str:
    """Splice a single ``iso``/``year`` block into a committed JSON, freezing all
    other content byte-identically.

    ``isos_container`` True -> the ISO map lives under a top-level ``"isos"`` key
    (calibration_reference.json, actual_tail.json); False -> the ISO map is the
    top-level object (actual_lmp.json). The freeze proof: dropping the newly
    added year and re-serialising reproduces the original file byte-for-byte.
    """
    original = path.read_text()
    data = json.loads(original)
    container = data["isos"] if isos_container else data
    if iso not in container:
        raise KeyError(f"{iso} absent from {path}")
    if year in container[iso]:
        return f"{path.relative_to(REPO)}: {iso} {year} already present - skipped"
    # Insert the holdout year first, preserving in-sample year order after it.
    container[iso] = {year: block, **container[iso]}

    def _dump(obj: dict) -> str:
        return json.dumps(obj, indent=indent, sort_keys=False) + "\n"

    # Freeze proof: remove the spliced year, re-serialise, compare to original.
    proof = json.loads(_dump(data))
    (proof["isos"] if isos_container else proof)[iso].pop(year)
    assert _dump(proof) == original, (
        f"splice would perturb frozen content in {path} - refusing to write"
    )
    if not dry_run:
        path.write_text(_dump(data))
    return f"{path.relative_to(REPO)}: spliced {iso} {year} (all other content frozen)"


# --------------------------------------------------------------------------- #
# zone_temp
# --------------------------------------------------------------------------- #
def land_zone_temp(dry_run: bool) -> str:
    """Append the committed 2022 per-zone NOAA splits to the consolidated file."""
    path = NEISO_WEATHER / "neiso_zone_temp_daily.csv"
    existing = pd.read_csv(path)
    if (existing["date"].astype(str).str[:4] == str(HOLDOUT_YEAR)).any():
        return f"{path.relative_to(REPO)}: 2022 already present - skipped"
    parts = [
        pd.read_csv(NEISO_WEATHER / f"neiso_zone_temp_daily_{HOLDOUT_YEAR}h1.csv"),
        pd.read_csv(NEISO_WEATHER / f"neiso_zone_temp_daily_{HOLDOUT_YEAR}h2.csv"),
    ]
    block = pd.concat(parts, ignore_index=True)
    assert list(block.columns) == list(existing.columns), "schema mismatch vs committed"
    assert (block["date"].astype(str).str[:4] == str(HOLDOUT_YEAR)).all()
    # Match the committed zone-then-date ordering for the appended block.
    block = block.sort_values(["zone", "date"]).reset_index(drop=True)
    text = block.to_csv(index=False, header=False)
    return _append_frozen_csv(path, text, dry_run=dry_run)


# --------------------------------------------------------------------------- #
# lw_temp
# --------------------------------------------------------------------------- #
def land_lw_temp(dry_run: bool) -> str:
    """Re-fetch the six NOAA stations for 2022 with the frozen derive_neiso
    load-weighting and append the daily series (in-sample bytes frozen)."""
    path = NEISO_WEATHER / "neiso_load_weighted_temp_daily.csv"
    existing = pd.read_csv(path)
    if (existing["date"].astype(str).str[:4] == str(HOLDOUT_YEAR)).any():
        return f"{path.relative_to(REPO)}: 2022 already present - skipped"
    import derive_neiso_temp_reliability_floor as dn  # frozen weighting recipe

    wx = dn.fetch_neiso_temp(f"{HOLDOUT_YEAR}-01-01", f"{HOLDOUT_YEAR}-12-31")
    out = wx.reset_index()
    out.columns = ["date", "tmax_c", "tmin_c"]
    out["date"] = pd.to_datetime(out["date"]).dt.strftime("%Y-%m-%d")
    out = out.sort_values("date")
    assert (out["date"].str[:4] == str(HOLDOUT_YEAR)).all()
    assert list(existing.columns) == ["date", "tmax_c", "tmin_c"]
    text = out.to_csv(index=False, header=False)
    return _append_frozen_csv(path, text, dry_run=dry_run)


# --------------------------------------------------------------------------- #
# calref (+ renewable capacity)
# --------------------------------------------------------------------------- #
def land_calref(dry_run: bool) -> str:
    """Splice isos.NEISO.2022 into calibration_reference.json and emit
    NEISO_2022_renewable_capacity.csv, from build_calibration_reference."""
    calref = VALIDATION / "calibration_reference.json"
    renew = VALIDATION / f"NEISO_{HOLDOUT_YEAR}_renewable_capacity.csv"
    committed = json.loads(calref.read_text())
    have_year = "2022" in committed["isos"]["NEISO"]
    have_csv = renew.exists()
    if have_year and have_csv:
        return f"{calref.relative_to(REPO)}: NEISO 2022 + renewable CSV already present - skipped"

    import build_calibration_reference as bcr

    # Temp dir UNDER the repo so build_reference's relative_to(REPO) logging works.
    with tempfile.TemporaryDirectory(dir=str(REPO)) as td:
        bcr.OUTPUT_DIR = Path(td)  # redirect ALL writes off the committed tree
        bcr.build_reference()
        rebuilt = json.loads((Path(td) / "calibration_reference.json").read_text())
        block = rebuilt["isos"]["NEISO"]["2022"]
        tmp_csv = Path(td) / f"NEISO_{HOLDOUT_YEAR}_renewable_capacity.csv"
        csv_bytes = tmp_csv.read_bytes()

    msgs = []
    if not have_csv:
        if not dry_run:
            renew.write_bytes(csv_bytes)
        rows = pd.read_csv(pd.io.common.BytesIO(csv_bytes))
        assert (rows["iso"] == "NEISO").all() and (rows["year"] == HOLDOUT_YEAR).all()
        verb = "would write" if dry_run else "wrote"
        msgs.append(f"{renew.relative_to(REPO)}: {verb} {len(rows)} rows (new file)")
    else:
        msgs.append(f"{renew.relative_to(REPO)}: already present - skipped")

    if not have_year:
        # calibration_reference.json is dumped indent=2, sort_keys=True, +"\n".
        original = calref.read_text()
        data = json.loads(original)
        data["isos"]["NEISO"]["2022"] = block

        def _dump(obj: dict) -> str:
            return json.dumps(obj, indent=2, sort_keys=True) + "\n"

        proof = json.loads(_dump(data))
        proof["isos"]["NEISO"].pop("2022")
        assert _dump(proof) == original, "calref splice would perturb frozen content"
        if not dry_run:
            calref.write_text(_dump(data))
        msgs.append(
            f"{calref.relative_to(REPO)}: spliced isos.NEISO.2022 (all else frozen)"
        )
    else:
        msgs.append(f"{calref.relative_to(REPO)}: NEISO 2022 already present - skipped")
    return "; ".join(msgs)


# --------------------------------------------------------------------------- #
# outages
# --------------------------------------------------------------------------- #
def land_outages(dry_run: bool) -> str:
    """Append ONLY the 2022-start outage windows (HEAD detector vintage) to the
    committed 968; the 968 stay byte-frozen (the vintage asymmetry is a register
    DEGRADED row, not resolved here)."""
    path = RAW / "campd-unit-outages-NEISO.csv"
    committed = pd.read_csv(path)
    n_committed = len(committed)
    if (committed["outage_start"].astype(str).str[:4] == str(HOLDOUT_YEAR)).any():
        return f"{path.relative_to(REPO)}: 2022 windows already present - skipped"

    import derive_campd_unit_outages as dco

    fresh = _derive_outages(dco, [HOLDOUT_YEAR, 2023, 2024, 2025])
    block = fresh[fresh["outage_start"].astype(str).str[:4] == str(HOLDOUT_YEAR)].copy()
    assert list(block.columns) == list(committed.columns), "outage schema mismatch"
    # Keep the committed 968 byte-frozen (prefix); append the 2022 windows.
    text = block.to_csv(index=False, header=False)
    status = _append_frozen_csv(path, text, dry_run=dry_run)
    return (
        f"{status} [committed {n_committed} frozen; +{len(block)} 2022-start windows]"
    )


def _derive_outages(dco, years: list[int]) -> pd.DataFrame:
    """Run the committed NEISO outage detector for ``years`` into a DataFrame,
    without writing to the committed CSV (redirect its output to a temp path)."""
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


# --------------------------------------------------------------------------- #
# actual_lmp
# --------------------------------------------------------------------------- #
def land_actual_lmp(dry_run: bool) -> str:
    """Splice NEISO 2022 (DA 85.56 / RT 84.92) into actual_lmp.json, built from
    the relocated 2022 SMD workbook + the frozen load-weighting."""
    path = VALIDATION / "actual_lmp.json"
    committed = json.loads(path.read_text())
    if "2022" in committed["NEISO"]:
        return f"{path.relative_to(REPO)}: NEISO 2022 already present - skipped"
    _ensure_smd_2022()
    import derive_actual_lmp as dal

    with tempfile.TemporaryDirectory() as td:
        dal.OUT = Path(td) / "actual_lmp.json"
        dal.HOURLY_OUT = Path(td)
        table, hourly = dal.build([HOLDOUT_YEAR], isos=["NEISO"])
        hourly["NEISO"].to_parquet(
            dal.HOURLY_OUT / "actual_lmp_hourly_NEISO.parquet", index=False
        )
        dal.OUT.write_text(json.dumps({"NEISO": table["NEISO"]}, indent=2) + "\n")
        dal.lw_retrofit([HOLDOUT_YEAR], isos=["NEISO"])
        block = json.loads(dal.OUT.read_text())["NEISO"]["2022"]

    assert round(block["da"], 2) == 85.56, f"DA {block['da']} != 85.56"
    assert round(block["rt"], 2) == 84.92, f"RT {block['rt']} != 84.92"
    for k in ("da_mon", "rt_mon", "zones", "src", "rt_lw", "da_lw"):
        assert k in block, f"NEISO 2022 block missing {k}"
    return _splice_json_year(
        path, "NEISO", "2022", block, isos_container=False, indent=2, dry_run=dry_run
    )


# --------------------------------------------------------------------------- #
# actual_tail
# --------------------------------------------------------------------------- #
def land_actual_tail(hourly_parquet: Path, dry_run: bool) -> str:
    """Splice NEISO 2022 (DA 27h / RT 117h) into actual_tail.json from the 2022
    hourly parquet."""
    path = REPO / "frontend" / "data" / "backcast" / "tail" / "actual_tail.json"
    committed = json.loads(path.read_text())
    if "2022" in committed["isos"].get("NEISO", {}):
        return f"{path.relative_to(REPO)}: NEISO 2022 already present - skipped"
    block = _neiso_2022_tail_block(hourly_parquet)
    assert block["da_gt"] == 27, f"DA tail {block['da_gt']} != 27"
    assert block["rt_gt"] == 117, f"RT tail {block['rt_gt']} != 117"
    return _splice_json_year(
        path, "NEISO", "2022", block, isos_container=True, indent=1, dry_run=dry_run
    )


def _neiso_2022_tail_block(hourly_parquet: Path) -> dict:
    """Return the NEISO 2022 actual_tail block by running the committed producer.

    Stages the 2022 hourly series under the producer's expected filename in a
    temp dir, points ``derive_actual_tail.SRC_DIR`` at it, and returns the
    marker-gated ``isos.NEISO.2022`` block the producer emits - so the spliced
    block is byte-for-byte what a full producer run would write.
    """
    import derive_actual_tail as dat

    h = pd.read_parquet(hourly_parquet)
    if not (h["year"] == HOLDOUT_YEAR).any():
        raise RuntimeError(f"no NEISO {HOLDOUT_YEAR} rows in {hourly_parquet}")
    with tempfile.TemporaryDirectory() as td:
        staged = Path(td) / "actual_lmp_hourly_NEISO.parquet"
        h.to_parquet(staged, index=False)
        saved = dat.SRC_DIR
        try:
            dat.SRC_DIR = Path(td)
            full = dat.derive()
        finally:
            dat.SRC_DIR = saved
    return full["isos"]["NEISO"][str(HOLDOUT_YEAR)]


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def _ensure_smd_2022() -> None:
    """Ensure the 2022 SMD workbook is resolvable under lmp-data/NEISO/ (the
    binary lander does the tracked git mv; this covers the local run)."""
    dst = RAW / "lmp-data" / "NEISO" / "2022_smd_hourly.xlsx"
    src = RAW / "lmp-data" / "2022_smd_hourly.xlsx"
    if not dst.exists():
        if not src.exists():
            raise FileNotFoundError("2022 SMD workbook not found at root or NEISO/")
        shutil.copy2(src, dst)


ALL = ("zone_temp", "lw_temp", "calref", "outages", "actual_lmp", "actual_tail")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--only", nargs="+", choices=ALL, default=list(ALL))
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="Verify + assert freeze but write nothing.",
    )
    ap.add_argument(
        "--hourly-parquet",
        type=Path,
        default=VALIDATION / "actual_lmp_hourly_NEISO.parquet",
        help="Hourly parquet feeding actual_tail (default: committed path; the "
        "binary lander rebuilds it with the 2022 block before this driver runs).",
    )
    args = ap.parse_args()

    handlers = {
        "zone_temp": lambda: land_zone_temp(args.dry_run),
        "lw_temp": lambda: land_lw_temp(args.dry_run),
        "calref": lambda: land_calref(args.dry_run),
        "outages": lambda: land_outages(args.dry_run),
        "actual_lmp": lambda: land_actual_lmp(args.dry_run),
        "actual_tail": lambda: land_actual_tail(args.hourly_parquet, args.dry_run),
    }
    print(
        f"NEISO 2022 data-readiness driver ({'DRY-RUN' if args.dry_run else 'WRITE'})"
    )
    for name in args.only:
        print(f"[{name}] {handlers[name]()}")


if __name__ == "__main__":
    main()

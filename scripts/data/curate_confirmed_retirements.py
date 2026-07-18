"""Curate the ``confirmed-retirements`` clean datatype.

Reconciles each ISO's binding-instrument retirement registry (PJM deactivation
acceptances, MISO Attachment Y approvals, NYISO deactivation notices, ISO-NE
cleared de-list bids, CAISO SWRCB/CPUC orders, ERCOT NSO acceptances, plus
cross-ISO consent decrees and statutes) onto the single tidy schema in
``data/dictionary/schema/confirmed-retirements.schema.yaml`` and writes each ISO
partition through the frozen :func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/confirmed_retirements/<iso>.py`` (each
registers an :class:`~scripts.lib.confirmed_retirements.IsoSpec`); this script is
a thin dispatcher over the registry, so adding an ISO never touches it. Every
row is validated against the EIA-860 fleet spine (the plant/generator must
exist, and any stated ``capacity_mw`` must be within 5 % of the EIA-860
nameplate) so a typo or a stale identity fails loudly rather than silently
force-retiring the wrong unit. ``exit_year`` is a *column* (the registry spans
several years), so each ISO writes one partition
``data/clean/confirmed-retirements/<ISO>/…parquet`` (``year=None``). Reads only
``data/raw``; idempotent. Run
``python scripts/data/curate_confirmed_retirements.py [--isos PJM ERCOT ...]``.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

import pandas as pd

from scripts.lib import clean_io
from scripts.lib import confirmed_retirements as cr
from scripts.lib.clean_io import paths

# First calendar year the forward channel scores: an exit before it belongs to
# the backcast vintage snapshot / within-window retiree build, never the
# forecast injector (mirrors process_eia860.RETIREMENT_WINDOW_START).
RETIREMENT_WINDOW_START: int = 2023

# Fractional nameplate tolerance for the EIA-860 spine MW cross-check.
_MW_TOLERANCE: float = 0.05

# Default EIA-860 fleet-spine parquet (the canonical loader extract).
_DEFAULT_SPINE = paths.RAW_DATA_DIR / "eia-860" / "eia860_generators.parquet"


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def _load_spine(spine_path: Path) -> dict[tuple[int, str], float]:
    """Return ``{(plant_id, generator_id): nameplate_mw}`` from the EIA-860 spine.

    The nameplate is the MW cross-check reference. Returns an empty map when the
    spine parquet is absent (spine validation then only checks ``exit_year``).
    """
    if not spine_path.is_file():
        return {}
    df = pd.read_parquet(
        spine_path, columns=["plant_id", "generator_id", "nameplate_capacity_mw"]
    )
    spine: dict[tuple[int, str], float] = {}
    for row in df.itertuples(index=False):
        try:
            pid = int(row.plant_id)
        except (TypeError, ValueError):
            continue
        gid = str(row.generator_id).strip()
        mw = row.nameplate_capacity_mw
        spine[(pid, gid)] = float(mw) if pd.notna(mw) else float("nan")
    return spine


def _validate_against_spine(
    iso: str, df: pd.DataFrame, spine: dict[tuple[int, str], float]
) -> None:
    """Raise if any registry row is not grounded in the EIA-860 fleet spine.

    Checks, per row: ``exit_year >= RETIREMENT_WINDOW_START``; the
    ``(plant_id, generator_id)`` identity exists in the spine; and the stated
    ``capacity_mw`` (when present) is within :data:`_MW_TOLERANCE` of the
    EIA-860 nameplate. Spine identity/MW checks are skipped only when the spine
    parquet is entirely absent (logged by the caller), never per-row.
    """
    problems: list[str] = []
    for row in df.itertuples(index=False):
        key = (int(row.plant_id), str(row.generator_id).strip())
        label = f"{iso} {key[0]}_{key[1]} ({row.instrument_id})"
        # The window check applies to LIVE rows only: a live pre-window exit
        # belongs to the backcast vintage snapshot, never the forecast
        # injector. A ``superseded`` row is an audit-trail / reversal record —
        # its exit never happened (the counter-instrument cancelled it), so
        # its original date is historical by construction (e.g. the
        # Byron/Dresden 2021 dates IL CEJA reversed).
        superseded = bool(row.superseded) if pd.notna(row.superseded) else False
        if not superseded and (
            pd.isna(row.exit_year) or int(row.exit_year) < RETIREMENT_WINDOW_START
        ):
            problems.append(
                f"{label}: exit_year {row.exit_year} < window start "
                f"{RETIREMENT_WINDOW_START} (belongs to the backcast snapshot)"
            )
        if not spine:
            continue
        if key not in spine:
            problems.append(f"{label}: (plant_id, generator_id) not in EIA-860 spine")
            continue
        nameplate = spine[key]
        stated = row.capacity_mw
        if pd.notna(stated) and pd.notna(nameplate) and nameplate > 0:
            rel_err = abs(float(stated) - nameplate) / nameplate
            if rel_err > _MW_TOLERANCE:
                problems.append(
                    f"{label}: capacity_mw {stated} off {rel_err:.0%} from EIA-860 "
                    f"nameplate {nameplate} (> {_MW_TOLERANCE:.0%})"
                )
    if problems:
        raise ValueError(
            f"confirmed-retirements spine validation failed for {iso}:\n  - "
            + "\n  - ".join(problems)
        )


def curate(
    raw_root: Path | None = None,
    isos: Iterable[str] | None = None,
    spine_path: Path | None = None,
) -> list[Path]:
    """Curate and write every requested ISO's confirmed-retirements partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it at
        a fixture directory.
    isos:
        Subset of ISOs to curate (default: every registered ISO). An ISO whose
        raw CSV has not landed yet (DATA NEEDED) yields an empty frame and is
        skipped.
    spine_path:
        EIA-860 fleet-spine parquet for the identity/MW cross-check (defaults to
        the committed ``eia860_generators.parquet``); tests point it at a fixture
        or omit it (empty spine → only the ``exit_year`` window is enforced).

    Returns the list of paths written. Reads only ``data/raw``; safe to re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    spine_path = Path(spine_path) if spine_path is not None else _DEFAULT_SPINE
    registry = cr.load_registry()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)

    spine = _load_spine(spine_path)
    if not spine:
        print(f"[warn] EIA-860 spine {_rel(spine_path)} absent; MW/identity check off")

    written: list[Path] = []
    for iso in wanted:
        df = cr.parse_iso(iso, raw_root)
        if df.empty:
            print(f"[skip] {iso}: no rows in {_rel(cr.raw_csv_for(iso, raw_root))}")
            continue
        _validate_against_spine(iso, df, spine)
        source = _rel(cr.raw_csv_for(iso, raw_root))
        path = clean_io.write_clean(df, cr.DATATYPE, iso=iso, year=None, source=source)
        clean_io.validate_clean(path)
        written.append(path)
        live = int((~df["superseded"].astype(bool)).sum())
        print(f"wrote {path}  ({len(df)} rows, {live} live)")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--isos",
        nargs="*",
        default=None,
        help="subset of ISOs to curate (default: every registered ISO)",
    )
    args = parser.parse_args(argv)
    written = curate(isos=args.isos)
    print(f"\n{len(written)} partition(s) written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

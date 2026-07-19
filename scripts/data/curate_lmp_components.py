"""Curate the ``lmp-components`` clean datatype.

Parses each ISO's staged per-node LMP component record (MISO: the D6 hub
staging of the daily ex-post reports; see the raw README) onto the tidy
schema in ``data/dictionary/schema/lmp-components.schema.yaml`` and writes
each (ISO, market, year) partition through the frozen
:func:`scripts.lib.clean_io.write_clean` seam.

Per-ISO parsing lives in ``scripts/lib/lmp_components/<iso>.py`` (each
registers an :class:`~scripts.lib.lmp_components.IsoSpec`); this script is
a thin dispatcher over the registry, so adding an ISO never touches it.
Reads only ``data/raw``; idempotent. Run
``python scripts/data/curate_lmp_components.py [--isos MISO]
[--years 2023 2024 2025]``.

Quarantine (CLAUDE.md rule 22): the default year set is the calibration
train window. Curating a staged out-of-train year (e.g. the authorized
2022 validation-holdout staging) requires ``--allow-out-of-train`` and
session-logged owner authorization.

Integrity: within one (market, interval) the implied system marginal
energy component (LMP - MCC - MLC) is common to every node up to the
report's 2-decimal rounding; the curation recomputes the cross-node
spread per interval and warns loudly past the tolerance (a corrupted
staging row, never a market feature).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Iterable

from scripts.lib import clean_io
from scripts.lib import lmp_components as lc
from scripts.lib.clean_io import paths

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("curate_lmp_components")

# Market-date years curated by default — the calibration train window
# (CLAUDE.md rule 22).
DEFAULT_YEARS: tuple[int, ...] = (2023, 2024, 2025)


def _rel(path: Path) -> str:
    """Path relative to the repo root for compact provenance (else absolute)."""
    try:
        return str(path.relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path)


def curate(
    raw_root: Path | None = None,
    isos: Iterable[str] | None = None,
    years: Iterable[int] | None = None,
    allow_out_of_train: bool = False,
) -> list[Path]:
    """Curate and write every requested (ISO, market, year) partition.

    Parameters
    ----------
    raw_root:
        Root of the raw tree (defaults to ``paths.RAW_DIR``); tests point it
        at a fixture directory.
    isos:
        Subset of ISOs (default: every registered ISO).
    years:
        Market-date years (default: :data:`DEFAULT_YEARS`). Years outside
        the train window are refused unless ``allow_out_of_train`` — rule 22.
    allow_out_of_train:
        Explicit opt-in for out-of-train years (owner-authorized intake
        validation only; see the raw README's quarantine section).

    Returns the list of paths written. A (market, year) with no staging
    yields an empty frame and is skipped. Reads only ``data/raw``; safe to
    re-run.
    """
    raw_root = Path(raw_root) if raw_root is not None else paths.RAW_DIR
    registry = lc.load_specs()
    wanted = [s.upper() for s in isos] if isos else sorted(registry)
    years = list(years) if years is not None else list(DEFAULT_YEARS)

    out_of_train = sorted(set(years) - set(DEFAULT_YEARS))
    if out_of_train and not allow_out_of_train:
        raise SystemExit(
            f"years {out_of_train} are outside the train window "
            f"{DEFAULT_YEARS} — pass --allow-out-of-train only with "
            "session-logged owner authorization (CLAUDE.md rule 22)"
        )

    written: list[Path] = []
    for iso in wanted:
        spec = registry[iso]
        # RAW_DIR-relative raw_subdir (shared staging — lib docstring).
        raw_dir = raw_root / spec.raw_subdir
        for year in years:
            for market in lc.MARKETS:
                df = spec.parse(raw_dir, market, year)
                if df.empty:
                    continue
                spread = lc.mec_identity_spread(df)
                bad = spread[spread > lc.MEC_IDENTITY_TOLERANCE_USD_MWH]
                if not bad.empty:
                    log.warning(
                        "%s %s %d: MEC identity spread > $%.2f in %d/%d "
                        "intervals (max $%.2f at %s) — inspect the staging",
                        iso,
                        market,
                        year,
                        lc.MEC_IDENTITY_TOLERANCE_USD_MWH,
                        len(bad),
                        len(spread),
                        float(bad.max()),
                        bad.idxmax(),
                    )
                path = clean_io.write_clean(
                    df,
                    lc.DATATYPE,
                    iso=iso,
                    year=year,
                    market=market,
                    source=_rel(raw_dir),
                )
                clean_io.validate_clean(path)
                written.append(path)
                print(f"{iso} {market} {year}: {len(df)} rows -> {_rel(path)}")
    return written


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--isos", nargs="+", default=None, help="subset of ISOs")
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help=f"market-date years (default {DEFAULT_YEARS})",
    )
    ap.add_argument(
        "--raw-root", type=Path, default=None, help="override the raw tree root"
    )
    ap.add_argument(
        "--allow-out-of-train",
        action="store_true",
        help="permit out-of-train years (owner-authorized intake only, rule 22)",
    )
    args = ap.parse_args()
    written = curate(
        raw_root=args.raw_root,
        isos=args.isos,
        years=args.years,
        allow_out_of_train=args.allow_out_of_train,
    )
    if not written:
        raise SystemExit("nothing curated — no staged raw files found")


if __name__ == "__main__":
    main()

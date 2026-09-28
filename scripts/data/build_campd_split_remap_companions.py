"""Build the ``-splitremap-`` companions of an ISO's CAMPD-derived artifacts (miso-280).

WHY. ``market_sim.data.campd.CAMPD_UNIT_PLANT_REMAP`` re-keys a CEMS unit
filed under a legacy facility to the EIA plant it belongs to. miso-280 added
West Riverside Energy Center's CTs (EIA 64020, generators CTG3 / CTG4), which
CEMS files under the legacy Riverside facility 55641 as ``CT-03`` / ``CT-04``
(CAMPD CT-03 + CT-04 gross tracks EIA-923 64020 net within 2 % every year
2020-2025; ``docs/FINDING-miso280-phase0-riverside-vlr-southgas-2026-09-28.md``
section 1). No live solve path reads raw CAMPD, so the entry reaches a solve only
through the DERIVED artifacts -- and every one the MISO keeper reads was derived
before the entry existed. This builder writes their re-derived companions,
read under ``ScenarioConfig.campd_split_remap_companions``.

CONSTRUCTION -- A PLANT-SCOPED SPLICE, NEVER A WHOLESALE HEAD RE-DERIVE. Each
companion is the INCUMBENT artifact's exact bytes with the lines of the
remap-touched plants (both sides of every remap entry) replaced by the SAME
deriver's lines for those plants, run at HEAD with the extended remap. Every
other line is byte-identical. The derivers have drifted since some incumbents
were written (the CC derive gained the EIA-923 identity column; the std and
maxgen outage derives regenerate other plants differently, and the 2018 CAMPD
extracts behind the std extract's 2018 rows are no longer on disk), so a
wholesale HEAD re-derive would import unrelated drift into a keeper input --
the thing rule 23 ``[R-FROZEN-DERIVE]`` forbids. The lane verified, per family,
that the HEAD deriver with the new entries stripped reproduces the incumbent's
lines for the remap plants (the control), so the splice carries the remap delta
and nothing else. Outage rows are spliced only inside ``--years`` (the std
extract's 2018 rows are kept verbatim: West Riverside did not exist in 2018).

FAMILIES (``--family``; default all four):

* ``std``      -- ``unit_outage_csv_for_iso(iso, mixed_gas_routing=True)``
  (MISO: ``campd-unit-outages-unitroute-MISO.csv``), deriver
  ``derive_campd_unit_outages.py --mixed-gas-routing``;
* ``shortgas`` -- ``campd-unit-outages-shortgas-<ISO>.csv``, deriver
  ``--short-windows --short-window-groups gas --merit-order-guard``;
* ``maxgen``   -- ``unit_outage_maxgen_csv_for_iso(iso, True)``, deriver
  ``derive_campd_maxgen_outages.py --mixed-gas-routing --split-remap`` (its
  disjointness guard reads the ``std`` companion, so ``std`` is built first);
* ``cc``       -- ``campd_cc_heat_rates_<ISO>.csv``, deriver
  ``derive_campd_cc_heat_rates.py`` (the fresh rows are projected onto the
  incumbent's columns; a fresh row the incumbent construction could not have
  written -- flag ``eia923_identity`` -- aborts).

The four tranche-family companions are written by
``derive_thermal_tranches.py --split-remap`` AFTER this (they read the ``std``
companion as their outage-derated denominator).

``--fresh-dir`` reuses deriver outputs already written there
(``fresh-<family>.csv``) instead of re-running the derivers. Zero free
parameters. Never an overwrite of an incumbent.
"""

from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    unit_outage_csv_for_iso,
    unit_outage_maxgen_csv_for_iso,
    unit_outage_short_gas_csv_for_iso,
)

FAMILIES: tuple[str, ...] = ("std", "shortgas", "maxgen", "cc")

#: Per family: (plant column, the column whose leading 4 characters give the
#: row's year for the ``--years`` scope or None to splice every year, the
#: columns that ANCHOR a fresh line to the incumbent position it replaces).
_KEYS: dict[str, tuple[str, str | None, tuple[str, ...]]] = {
    "std": ("facility_id", "outage_start", ("facility_id", "unit_id")),
    "shortgas": ("facility_id", "outage_start", ("facility_id", "unit_id")),
    "maxgen": ("facility_id", "window_start", ("facility_id", "window_start")),
    "cc": ("plant_code", None, ("plant_code", "year")),
}

#: CC rows whose flag this incumbent construction could not have written.
_CC_FORBIDDEN_FLAGS: frozenset[str] = frozenset({"eia923_identity"})


def remap_plants() -> set[int]:
    """Both sides of every ``CAMPD_UNIT_PLANT_REMAP`` entry (legacy and EIA plant)."""
    return {int(f) for f, _ in campd.CAMPD_UNIT_PLANT_REMAP} | {
        int(v) for v in campd.CAMPD_UNIT_PLANT_REMAP.values()
    }


def incumbent_path(family: str, iso: str) -> Path:
    """The incumbent artifact of ``family`` (the MISO keeper's selection)."""
    if family == "std":
        return unit_outage_csv_for_iso(iso, mixed_gas_routing=True)
    if family == "shortgas":
        return unit_outage_short_gas_csv_for_iso(iso)
    if family == "maxgen":
        return unit_outage_maxgen_csv_for_iso(iso, mixed_gas_routing=True)
    if family == "cc":
        return PROCESSED_DIR / f"campd_cc_heat_rates_{iso.upper()}.csv"
    raise ValueError(f"unknown family {family!r}")


def companion_path(incumbent: Path) -> Path:
    """``X-<ISO>.csv`` / ``X_<ISO>.csv`` -> ``X-splitremap-<ISO>.csv`` (constructed, not checked)."""
    stem = incumbent.stem
    cut = max(stem.rfind("-"), stem.rfind("_"))
    return incumbent.with_name(
        f"{stem[:cut]}-{campd.SPLIT_REMAP_TAG}-{stem[cut + 1 :]}{incumbent.suffix}"
    )


def derive_command(family: str, iso: str, years: list[int], out: Path) -> list[str]:
    """The deriver invocation whose output supplies ``family``'s fresh lines."""
    py = [sys.executable]
    ys = [str(y) for y in years]
    if family == "std":
        return py + [
            str(REPO / "scripts/data/derive_campd_unit_outages.py"),
            "--iso", iso, "--years", *ys, "--mixed-gas-routing", "--out", str(out),
        ]  # fmt: skip
    if family == "shortgas":
        return py + [
            str(REPO / "scripts/data/derive_campd_unit_outages.py"),
            "--iso", iso, "--years", *ys, "--short-windows",
            "--short-window-groups", "gas", "--merit-order-guard", "--out", str(out),
        ]  # fmt: skip
    if family == "maxgen":
        return py + [
            str(REPO / "scripts/data/derive_campd_maxgen_outages.py"),
            "--iso", iso, "--mixed-gas-routing", "--split-remap", "--out", str(out),
        ]  # fmt: skip
    if family == "cc":
        return py + [
            str(REPO / "scripts/data/derive_campd_cc_heat_rates.py"),
            "--iso", iso, "--years", *ys, "--out", str(out),
        ]  # fmt: skip
    raise ValueError(f"unknown family {family!r}")


def _parse(text: str) -> tuple[list[str], list[str], list[list[str]]]:
    """Return (header, raw data lines, parsed data rows) of a CSV's text."""
    lines = [ln if ln.endswith("\n") else ln + "\n" for ln in text.splitlines()]
    header = next(csv.reader([lines[0]]))
    body = [ln for ln in lines[1:] if ln.strip()]
    rows = [next(csv.reader([ln])) for ln in body]
    return header, body, rows


def _format_row(header: list[str], values: dict[str, str]) -> str:
    """One CSV line in ``header``'s column order (pandas' minimal quoting)."""
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow([values.get(c, "") for c in header])
    return buf.getvalue()


def splice(
    incumbent_text: str,
    fresh_text: str,
    plants: set[int],
    plant_col: str,
    year_col: str | None,
    years: set[int] | None,
    anchor_cols: tuple[str, ...] = (),
) -> tuple[str, dict[str, int]]:
    """Replace ``plants``' in-scope lines of the incumbent with the fresh ones.

    A line is IN SCOPE when its plant is in ``plants`` and (``year_col`` is
    None or the year its ``year_col`` value starts with is in ``years``). The
    incumbent's in-scope lines are removed; the fresh file's in-scope lines,
    projected onto the incumbent's header (values copied as text, so their
    formatting is the deriver's own), are inserted, in the fresh file's order,
    at the position of the first removed line with the same ``anchor_cols``
    values; else, where the incumbent is sorted by plant code, at the plant's
    sorted position; else at the first removed line sharing the anchor with
    the plant column dropped (the sibling plant's row for the same year or
    event window); else at the end. Every other line is byte-identical and
    keeps its order, so splicing a fresh file whose in-scope lines equal the
    incumbent's reproduces the incumbent byte-for-byte (the lane's control).
    """
    header, inc_lines, inc_rows = _parse(incumbent_text)
    fhead, _f_lines, f_rows = _parse(fresh_text)
    pi, fpi = header.index(plant_col), fhead.index(plant_col)
    sec_cols = tuple(c for c in anchor_cols if c != plant_col)

    def in_scope(row: list[str], p_idx: int, hdr: list[str]) -> bool:
        try:
            code = int(float(row[p_idx]))
        except ValueError:
            return False
        if code not in plants:
            return False
        if year_col is None or years is None:
            return True
        return int(str(row[hdr.index(year_col)])[:4]) in years

    def key(row: list[str], hdr: list[str], cols: tuple[str, ...]) -> tuple:
        return tuple(row[hdr.index(c)] for c in cols)

    kept: list[str] = []
    kept_codes: list[int | None] = []
    anchor_pos: dict[tuple, int] = {}
    sec_pos: dict[tuple, int] = {}
    removed = 0
    for line, row in zip(inc_lines, inc_rows):
        if in_scope(row, pi, header):
            anchor_pos.setdefault(key(row, header, anchor_cols), len(kept))
            sec_pos.setdefault(key(row, header, sec_cols), len(kept))
            removed += 1
            continue
        kept.append(line)
        try:
            kept_codes.append(int(float(row[pi])))
        except ValueError:
            kept_codes.append(None)
    monotone = all(
        a is not None and b is not None and a <= b
        for a, b in zip(kept_codes, kept_codes[1:])
    )
    placed: dict[int, list[str]] = {}
    added = 0
    for row in f_rows:
        if not in_scope(row, fpi, fhead):
            continue
        code = int(float(row[fpi]))
        k = key(row, fhead, anchor_cols)
        if k in anchor_pos:
            pos = anchor_pos[k]
        elif monotone:
            pos = next((i for i, c in enumerate(kept_codes) if c > code), len(kept))
        elif key(row, fhead, sec_cols) in sec_pos:
            pos = sec_pos[key(row, fhead, sec_cols)]
        else:
            pos = len(kept)
        placed.setdefault(pos, []).append(_format_row(header, dict(zip(fhead, row))))
        added += 1
    out: list[str] = []
    for i, line in enumerate(kept):
        out.extend(placed.get(i, []))
        out.append(line)
    out.extend(placed.get(len(kept), []))
    return (
        ",".join(_quote(h) for h in header) + "\n" + "".join(out),
        {"removed": removed, "added": added},
    )


def _quote(field: str) -> str:
    """Header cell with pandas' minimal quoting."""
    buf = io.StringIO()
    csv.writer(buf, lineterminator="").writerow([field])
    return buf.getvalue()


def build_family(
    family: str, iso: str, years: list[int], fresh_dir: Path, rerun: bool
) -> dict[str, object]:
    """Derive (or reuse) ``family``'s fresh output and write its companion."""
    inc = incumbent_path(family, iso)
    fresh = fresh_dir / f"fresh-{family}.csv"
    if rerun or not fresh.exists():
        fresh_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(derive_command(family, iso, years, fresh), check=True)
    plant_col, year_col, anchor_cols = _KEYS[family]
    inc_text = inc.read_text()
    header = _parse(inc_text)[0]
    head_line = inc_text.splitlines()[0] + "\n"
    if ",".join(_quote(h) for h in header) + "\n" != head_line:
        raise SystemExit(f"{inc.name}: header does not round-trip; refusing to splice")
    fresh_text = fresh.read_text()
    if family == "cc":
        fhead, _, frows = _parse(fresh_text)
        fi, gi = fhead.index("plant_code"), fhead.index("flag")
        bad = [
            r
            for r in frows
            if int(float(r[fi])) in remap_plants() and r[gi] in _CC_FORBIDDEN_FLAGS
        ]
        if bad:
            raise SystemExit(
                f"cc: {len(bad)} remap-plant row(s) carry a flag the incumbent "
                "construction cannot write; refusing to splice"
            )
    text, counts = splice(
        inc_text,
        fresh_text,
        remap_plants(),
        plant_col,
        year_col,
        set(years) if year_col else None,
        anchor_cols,
    )
    dst = companion_path(inc)
    if dst.resolve() == inc.resolve():
        raise SystemExit(f"companion path collides with incumbent ({inc})")
    dst.write_text(text)
    return {"incumbent": inc.name, "companion": dst.name, **counts}


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026],
        help="Derive years; outage lines outside them are kept verbatim. The "
        "shortgas and cc incumbents span 2019-2025 and take --cc-years.",
    )
    ap.add_argument(
        "--cc-years",
        nargs="+",
        type=int,
        default=[2019, 2020, 2021, 2022, 2023, 2024, 2025],
        help="Years for the shortgas and cc derivers (their incumbents' span).",
    )
    ap.add_argument("--family", nargs="+", choices=FAMILIES, default=list(FAMILIES))
    ap.add_argument("--fresh-dir", required=True, type=Path)
    ap.add_argument("--rerun", action="store_true")
    args = ap.parse_args()
    iso = args.iso.upper()
    order = [f for f in FAMILIES if f in args.family]
    for family in order:
        years = args.years if family in ("std", "maxgen") else args.cc_years
        res = build_family(family, iso, years, args.fresh_dir, args.rerun)
        print(f"{family}: {res}")


if __name__ == "__main__":
    main()

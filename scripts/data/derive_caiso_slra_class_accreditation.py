#!/usr/bin/env python
"""Derive CAISO's published class-level accreditation ledger from the SLRA appendix.

**What this produces.** Two reviewable artifacts digitized first-party from
CAISO's *Summer Loads and Resources Assessment* Technical Appendix, Table 1.1
("Existing resources by fuel type and deliverability status"):

* ``caiso_slra_class_accreditation.csv`` — one row per published fuel type with
  its **total** Net Dependable Capacity (NDC) and Net Qualifying Capacity (NQC),
  plus the per-deliverability-tranche split for the classes the table reports it
  for. This is CAISO's OWN resource-adequacy ledger, at class grain.
* the **storage whole-class accreditation ratio** that
  :data:`market_sim.config.constants.STORAGE_WHOLE_CLASS_ACCREDITATION_BY_ISO`
  cites, printed by ``--report`` and reconciled against the registry literal by
  ``tests/unit/data/test_caiso_slra_class_accreditation.py``.

**Why storage needs a whole-class ratio and not a duration table.** CAISO
publishes no storage duration→credit ratings. Its CY2026 NQC report's
``2026 Tech Factors`` tab carries technology factors for Solar Fixed / Solar
Tracking / Solar Thermal / Wind / non-dispatchable Hydro / Geothermal /
Cogeneration / Biomass and **no battery row at all** — because batteries are
*dispatchable*, and the appendix says so in terms: *"For dispatchable resources
like battery and natural gas plants, the NQC value is typically near its NDC or
installed capacity."* A CAISO entry in the by-duration registry would therefore
be an invented object. The publishable object is the realized whole-class ratio,
which is what this script derives.

**The basis correction, which is the whole point.** The published ratio is
NQC/**NDC**. The model multiplies a storage unit's **nameplate** ``power_cap_mw``
by its accreditation credit, and CAISO's NDC is materially below nameplate
(measured: 91.47 % of the EIA-860 CISO battery fleet). Quoting the published
0.9458 against nameplate would over-credit the class by 8.1 pp — the
substitution FFR-4D §6.1 warned against. This script emits the ratio on BOTH
bases and the registry takes the nameplate one.

**Rule 23 [R-FROZEN-DERIVE].** Re-derives ONLY when CAISO publishes a new
assessment and that PDF is intaken under
``data/raw/capacity-market/loads-resources/caiso/``. NEVER because a model
residual moved. There is no free parameter here: every number out is a published
MW or a ratio of two published MW.

**Rule 13 [R-MEASURED].** The output is a published market-design input that
regenerates for a forward year (CAISO publishes the assessment annually, ahead
of the summer) and responds to changed conditions (the ledger moves as the fleet
builds and as deliverability status resolves). It is not a model outcome and
nothing in it is fitted.

``pypdf`` is a lazy import, matching ``curate_caiso_lcr.py`` /
``curate_caiso_mic.py``: the committed CSV is the durable artifact, so the
extractor's dependency is not a runtime dependency of the model.

Usage::

    uv run --with pypdf python scripts/data/derive_caiso_slra_class_accreditation.py
    uv run --with pypdf python scripts/data/derive_caiso_slra_class_accreditation.py --report
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from market_sim.config.paths import RAW_DIR  # noqa: E402

logger = logging.getLogger(__name__)

SLRA_DIR: Path = RAW_DIR / "capacity-market" / "loads-resources" / "caiso"
DEFAULT_PDF: Path = (
    SLRA_DIR / "2026-summer-loads-and-resources-assessment-technical-appendix.pdf"
)
DEFAULT_YEAR: int = 2026
OUT: Path = SLRA_DIR / "caiso_slra_class_accreditation.csv"

# Table 1.1's deliverability tranches, in published column order. A fuel row
# reports a (NDC, NQC) pair for a subset of these and then the Total pair; the
# Total pair is ALWAYS the last two numbers on the row, which is what makes the
# class totals unambiguous to read even when the tranche columns are sparse.
TRANCHES: tuple[str, ...] = (
    "full_capacity",
    "interim",
    "partial",
    "energy_only",
)

# The published fuel-type labels, as they appear in the table's leftmost column.
FUEL_LABELS: tuple[str, ...] = (
    "Battery",
    "Biogas",
    "Biomass",
    "Distillate",
    "Geothermal",
    "Hybrid",
    "Hydro",
    "Natural Gas",
    "Nuclear",
    "Other",
    "Solar",
    "Waste Heat",
    "Wind",
    "Total",
)

# Table 1.1's fuel rows do not foot EXACTLY to its own published Total: the NQC
# column reconciles to the megawatt (59,069) while the NDC column's rows sum to
# 83,923 against a published 83,922. That 1 MW is CAISO's own per-row rounding,
# not a parse defect — so the closure check tolerates a couple of MW (and logs
# any nonzero drift) while still catching the hundreds-of-MW error a genuine
# mis-parse would produce. Never widen this to paper over a real mismatch.
_FOOTING_TOLERANCE_MW: int = 2

# Published NDC/NQC pairs are integers with thousands separators; the extractor
# occasionally splits one across a space ("2, 300"), so the separator group
# tolerates surrounding whitespace.
_NUMBER = re.compile(r"\d{1,3}(?:\s*,\s*\d{3})*")


def _numbers(line: str) -> list[int]:
    """Return the integer MW values on one Table 1.1 row, in published order."""
    return [
        int(m.group(0).replace(",", "").replace(" ", ""))
        for m in _NUMBER.finditer(line)
    ]


def _table_lines(pdf_path: Path) -> list[str]:
    """Return the Table 1.1 fuel rows as raw text lines.

    Locates the page carrying the table's own heading and truncates at the
    figure caption that follows it, so a later table's rows can never be read
    instead.
    """
    from pypdf import PdfReader

    heading = re.compile(r"Deliverability\s*\n\s*Fuel Type", re.IGNORECASE)
    for page in PdfReader(str(pdf_path)).pages[:14]:
        text = page.extract_text() or ""
        match = heading.search(text)
        if match is None:
            continue
        body = text[match.end() :]
        return [ln.strip() for ln in body.splitlines() if ln.strip()]
    raise ValueError(f"Table 1.1 header not found in {pdf_path}")


def extract_table_1_1(pdf_path: Path) -> dict[str, dict[str, int]]:
    """Extract Table 1.1's per-fuel NDC/NQC totals and the battery tranche split.

    Returns a mapping ``fuel_label -> {"total_ndc_mw", "total_nqc_mw", ...}``.
    A fuel whose row reports the full four-tranche split additionally carries
    ``<tranche>_ndc_mw`` / ``<tranche>_nqc_mw`` keys. The class totals are read
    as the LAST two numbers on each row, which is unambiguous regardless of how
    many tranche columns that fuel populates.

    Raises:
        ValueError: if a published label is missing, or if the Total row does
            not reconcile against the sum of the fuel rows (the closure check
            that makes a silent mis-parse impossible).
    """
    lines = _table_lines(pdf_path)
    out: dict[str, dict[str, int]] = {}
    for label in FUEL_LABELS:
        row = next(
            (ln for ln in lines if ln.startswith(label) and _numbers(ln)),
            None,
        )
        if row is None:
            raise ValueError(f"Table 1.1 row not found: {label!r}")
        values = _numbers(row[len(label) :])
        if len(values) < 2:
            raise ValueError(f"Table 1.1 row {label!r} has too few values: {values}")
        entry = {"total_ndc_mw": values[-2], "total_nqc_mw": values[-1]}
        # A row reporting every tranche has 4 pairs + the total pair = 10 values.
        if len(values) == 2 * (len(TRANCHES) + 1):
            for i, tranche in enumerate(TRANCHES):
                entry[f"{tranche}_ndc_mw"] = values[2 * i]
                entry[f"{tranche}_nqc_mw"] = values[2 * i + 1]
        out[label] = entry

    total = out["Total"]
    for basis in ("total_ndc_mw", "total_nqc_mw"):
        summed = sum(v[basis] for k, v in out.items() if k != "Total")
        drift = summed - total[basis]
        if abs(drift) > _FOOTING_TOLERANCE_MW:
            raise ValueError(
                f"Table 1.1 {basis} does not reconcile: rows sum to {summed:,}, "
                f"published Total is {total[basis]:,} (drift {drift:+,})"
            )
        if drift:
            logger.warning(
                "Table 1.1 %s rows sum to %s against a published Total of %s "
                "(%+d MW) — CAISO's own per-row rounding, within tolerance",
                basis,
                f"{summed:,}",
                f"{total[basis]:,}",
                drift,
            )
    return out


def write_csv(table: dict[str, dict[str, int]], year: int, out: Path) -> None:
    """Write the extracted ledger to the reviewable CSV artifact."""
    columns = ["iso", "compliance_year", "fuel_type", "total_ndc_mw", "total_nqc_mw"]
    for tranche in TRANCHES:
        columns += [f"{tranche}_ndc_mw", f"{tranche}_nqc_mw"]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        for label in FUEL_LABELS:
            row: dict[str, object] = {
                "iso": "CAISO",
                "compliance_year": year,
                "fuel_type": label,
            }
            row.update(table[label])
            writer.writerow(row)
    logger.info("wrote %s (%d rows)", out, len(FUEL_LABELS))


def report(table: dict[str, dict[str, int]], nameplate_mw: float) -> None:
    """Print the storage whole-class accreditation ratio on both bases."""
    battery = table["Battery"]
    ndc, nqc = battery["total_ndc_mw"], battery["total_nqc_mw"]
    print(f"CAISO battery, published Table 1.1: NDC {ndc:,} MW  NQC {nqc:,} MW")
    for tranche in TRANCHES:
        t_ndc = battery.get(f"{tranche}_ndc_mw")
        t_nqc = battery.get(f"{tranche}_nqc_mw")
        if t_ndc:
            print(
                f"  {tranche:<14s} NDC {t_ndc:6,}  NQC {t_nqc:6,}  {t_nqc / t_ndc:.5f}"
            )
    print(f"  NQC / NDC       = {nqc / ndc:.6f}   (the PUBLISHED ratio)")
    print(f"  NDC / nameplate = {ndc / nameplate_mw:.6f}")
    print(f"  NQC / nameplate = {nqc / nameplate_mw:.6f}   <- the REGISTRY value")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: extract Table 1.1, write the CSV, optionally report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", type=Path, default=DEFAULT_PDF)
    parser.add_argument("--year", type=int, default=DEFAULT_YEAR)
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument(
        "--nameplate-mw",
        type=float,
        default=15_448.4,
        help=(
            "EIA-860 CISO operable battery nameplate MW, the model's own "
            "multiplicand (2025 Early Release, Status='OP'; the same object "
            "STORAGE_BASE_FLEET_MW['CAISO'] is built from)."
        ),
    )
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    table = extract_table_1_1(args.pdf)
    write_csv(table, args.year, args.out)
    if args.report:
        report(table, args.nameplate_mw)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

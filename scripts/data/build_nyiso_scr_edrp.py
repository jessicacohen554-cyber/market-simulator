"""Build the NYISO SCR/EDRP demand-response enrollment CSV from the Gold Book.

Encodes the per-zone Special Case Resources (SCR) and Emergency Demand Response
Program (EDRP) registered capability transcribed from each year's **NYISO Gold
Book (Load & Capacity Data Report)** projection-of-enrollment table, and
re-emits ``data/raw/nyiso-demand-response/nyiso_scr_edrp_enrollment.csv``
deterministically (byte-identical). The immutable source is the committed Gold
Book PDF (``data/raw/NYISO/{year}-Gold-Book-Public.pdf``); the per-(zone,
program, season) MW below are transcribed from its cited table/page (see
``_SOURCES``). The CSV is a measured PUBLISHED input (CLAUDE.md rule 13/23): it
regenerates for a forward year from the next Gold Book and responds to changed
enrollment — re-derive ONLY when a new Gold Book is published, NEVER against a
price/volume residual.

The transcription is held here (not parsed live from the PDF) so the enrollment
input is diff-reviewable and its provenance is explicit: each ``_ENROLLMENT``
row cites, via ``_SOURCES``, the exact Gold Book document, table and page it was
read from. To add a year: read the new Gold Book's SCR/EDRP projection table,
append its ``_SOURCES`` citation and its A-K ``_ENROLLMENT`` rows, and re-run.

Consumed by ``src/market_sim/data/nyiso_demand_response.py``, which aggregates
the eleven A-K load zones onto the five NYISO model zones and builds the DR
pseudo-generator supply blocks used when ``ScenarioConfig.nyiso_scr_edrp`` is
on.

Usage:
    python scripts/data/build_nyiso_scr_edrp.py            # write the CSV
    python scripts/data/build_nyiso_scr_edrp.py --check     # verify byte-identity
"""

from __future__ import annotations

import argparse
import csv
import io
import sys

from market_sim.config.paths import RAW_DIR

# NYISO load zones, in the Gold Book's own A-K row order.
_ZONES: tuple[str, ...] = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K")

# Gold Book source per capability year: (source_doc, source_table, source_page).
# The immutable PDFs live at data/raw/NYISO/{doc}.
_SOURCES: dict[int, tuple[str, str, int]] = {
    2023: ("2023-Gold-Book-Public.pdf", "I-17", 67),
    2024: ("2024-Gold-Book-Public.pdf", "I-18", 71),
    2025: ("2025-Gold-Book-Public.pdf", "I-17", 69),
}

# Registered DR capability (MW) transcribed from the cited Gold Book table, per
# capability year and zone, as (SCR summer, SCR winter, EDRP summer, EDRP
# winter). SCR is the large ICAP program (~1.23-1.49 GW NYCA summer,
# concentrated in Zone J / NYC); EDRP is the small voluntary program (<= ~13 MW
# NYCA). Both are dispatched only in NYISO-declared reliability events.
_ENROLLMENT: dict[int, dict[str, tuple[float, float, float, float]]] = {
    2023: {
        "A": (209.6, 147.5, 0.0, 0.0),
        "B": (29.7, 18.3, 0.0, 0.0),
        "C": (90.1, 63.0, 0.0, 0.0),
        "D": (217.8, 207.4, 0.0, 0.1),
        "E": (33.1, 17.9, 0.3, 0.0),
        "F": (114.2, 56.0, 0.0, 0.0),
        "G": (36.1, 24.7, 0.0, 0.0),
        "H": (10.9, 8.8, 0.0, 0.0),
        "I": (32.2, 18.0, 0.3, 0.1),
        "J": (418.6, 223.3, 7.8, 0.3),
        "K": (33.7, 16.6, 0.0, 0.0),
    },
    2024: {
        "A": (230.6, 261.1, 0.0, 0.1),
        "B": (29.5, 22.4, 0.0, 0.0),
        "C": (79.7, 60.1, 0.0, 0.0),
        "D": (225.1, 234.8, 0.2, 0.0),
        "E": (30.3, 39.1, 0.0, 0.0),
        "F": (123.8, 73.5, 0.0, 0.0),
        "G": (40.2, 22.0, 0.0, 0.0),
        "H": (11.6, 8.2, 0.2, 0.2),
        "I": (32.7, 21.3, 1.2, 0.0),
        "J": (442.2, 242.6, 11.8, 0.0),
        "K": (35.3, 19.7, 0.0, 0.0),
    },
    2025: {
        "A": (411.7, 288.8, 0.1, 0.0),
        "B": (27.9, 25.0, 0.0, 0.0),
        "C": (82.6, 65.4, 0.0, 0.0),
        "D": (226.9, 218.2, 0.2, 0.1),
        "E": (34.2, 34.3, 0.2, 0.0),
        "F": (103.5, 51.9, 0.0, 0.0),
        "G": (40.7, 21.9, 0.0, 0.0),
        "H": (11.3, 7.5, 0.0, 0.3),
        "I": (38.6, 21.5, 0.0, 0.3),
        "J": (478.7, 278.5, 0.7, 0.4),
        "K": (30.6, 13.1, 0.0, 0.0),
    },
}

_HEADER = [
    "gold_book_year",
    "nyiso_zone",
    "program",
    "season",
    "enrolled_mw",
    "source_doc",
    "source_table",
    "source_page",
]


def _output_path():
    return RAW_DIR / "nyiso-demand-response" / "nyiso_scr_edrp_enrollment.csv"


def render_csv() -> str:
    """Return the enrollment CSV text (header + one row per year/zone/prog/season).

    Row order matches the committed artifact: year ascending, then zone A-K,
    then program (SCR before EDRP), then season (summer before winter). MW are
    written to one decimal place (the Gold Book's own precision).
    """
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(_HEADER)
    for year in sorted(_ENROLLMENT):
        doc, table, page = _SOURCES[year]
        for zone in _ZONES:
            scr_s, scr_w, edrp_s, edrp_w = _ENROLLMENT[year][zone]
            for program, (summer, winter) in (
                ("SCR", (scr_s, scr_w)),
                ("EDRP", (edrp_s, edrp_w)),
            ):
                for season, mw in (("summer", summer), ("winter", winter)):
                    w.writerow(
                        [year, zone, program, season, f"{mw:.1f}", doc, table, page]
                    )
    return buf.getvalue()


def main() -> None:
    """Write (or, with ``--check``, verify) the enrollment CSV."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--check",
        action="store_true",
        help="Verify the on-disk CSV is byte-identical to the encoded "
        "transcription (exit 1 on drift) instead of writing it.",
    )
    args = ap.parse_args()

    text = render_csv()
    path = _output_path()
    if args.check:
        current = path.read_text() if path.exists() else ""
        if current == text:
            print(f"OK: {path} matches the encoded transcription")
        else:
            print(
                f"DRIFT: {path} differs from the encoded transcription", file=sys.stderr
            )
            raise SystemExit(1)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    n_rows = text.count("\n") - 1
    print(f"wrote {n_rows} rows -> {path}")


if __name__ == "__main__":
    main()

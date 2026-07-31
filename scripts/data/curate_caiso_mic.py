#!/usr/bin/env python3
"""Transcribe CAISO's published Maximum Import Capability (MIC) filings.

Reads the annual "California ISO Maximum RA Import Capability for Year <Y>"
PDF (one page, one row per branch group / merchant scheduling limit) and emits
the ``branch_group`` / ``import_limit`` rows of the capacity-deliverability
registry ``data/raw/capacity-deliverability/caiso/caiso.csv`` — the measured
seam-import half of ``capacity_deliverability_limits`` (the CAISO keeper's
MIC -> ``WECC_import`` mapping; CLAUDE.md "Locational deliverability").

Transcription convention (reverse-engineered from the committed 2023-2025 rows
and asserted against them by ``--verify``, so a back-year transcription is
provably the same recipe rather than a fresh judgement call):

* the value taken is the **"Maximum Import Capability MW"** column — NOT
  ``Net Import``, which is the pre-ETC/TOR figure and goes negative;
* a branch group whose MIC is **0** is omitted (it carries no allocatable
  import capability that year) — this is why e.g. Silver Peak appears only in
  the 2024 delivery year;
* the OASIS branch-group code (``<NAME>_ITC`` / ``_ISL``) is mapped to the
  registry's published-report display name via :data:`BG_DISPLAY_NAME`;
* rows are ``season=annual``, ``area_type=branch_group``,
  ``metric=import_limit``, ``source_page=1``.

The PDFs are fetched from ``www.caiso.com`` at the stable per-year URL
patterns in :data:`MIC_URL_PATTERNS`; nothing is committed but the CSV rows
(the filings themselves stay at their public URLs, cited per row).

Usage:
    python scripts/data/curate_caiso_mic.py --verify 2023 2024 2025
    python scripts/data/curate_caiso_mic.py --years 2018 2019 2020 2021 2022 --merge
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

OUT_PATH = RAW_DATA_DIR / "capacity-deliverability" / "caiso" / "caiso.csv"

FIELDNAMES = [
    "iso",
    "delivery_year",
    "season",
    "area",
    "area_type",
    "metric",
    "value_mw",
    "value_pu",
    "source_doc",
    "source_page",
]

# CAISO renamed the file twice; try each pattern in order. The URL that
# actually served the year is what lands in the row's ``source_doc``, so the
# citation always points at the document the number came from.
MIC_URL_PATTERNS: tuple[str, ...] = (
    "https://www.caiso.com/documents/"
    "isomaximumresourceadequacyimportcapabilityforyear{year}.pdf",
    "https://www.caiso.com/documents/"
    "iso-maximum-resource-adequacy-import-capability-for-year-{year}.pdf",
)

# OASIS branch-group code -> the display name the committed registry rows use
# (CAISO's own report names for the same intertie).
BG_DISPLAY_NAME: dict[str, str] = {
    "IPPDCADLN": "IPP-DC",
    "MCCLMKTPC": "McCullough-Marketplace",
    "MEADMKTPC": "Mead-Marketplace",
    "MEADTMEAD": "Mead-T-Mead",
    "MKTPCADLN": "Marketplace-Adelanto",
    "MONAIPPDC": "Mona-IPP-DC",
    "WSTWGMEAD": "Westwing-Mead",
    "GONDIPPDC": "Gonder-IPP-DC",
    "BLYTHE": "Blythe",
    "CASCADE": "Cascade",
    "CFE": "CFE",
    "ELDORADO": "Eldorado",
    "IID-SCE": "IID-SCE",
    "IID-SDGE": "IID-SDGE",
    "LAUGHLIN": "Laughlin",
    "MCCULLGH": "McCullough",
    "MEAD": "Mead",
    "MERCHANT": "Merchant",
    "NORTHGILA500": "North Gila 500",
    "NOB": "NOB",
    "PALOVRDE": "Palo Verde",
    "PARKER": "Parker",
    "RNCHLAKE": "Rancho Seco/Lake",
    "SILVERPK": "Silver Peak",
    "SUMMIT": "Summit",
    "SYLMAR-AC": "Sylmar-AC",
    "VICTVL": "Victorville",
    "RDM230": "Round Mountain 230",
    "CTW230": "Cottonwood 230",
    "LLNL": "LLNL",
    "MALIN500": "Malin 500",
    "COTPISO": "COTP",
    "TRACY230": "Tracy 230",
    "TRACY500": "Tracy 500",
    "TRCYTEA": "Tracy-TEA",
    "NEWMELONP": "New Melones",
    "WESTLYLBNS": "Westley-Los Banos",
    "WESTLYFINK": "Westley-Fink",
    "WESTLYTSLA": "Westley-Tesla",
    "STANDIFORD": "Standiford",
    "OAKDALE": "Oakdale",
    "MARBLE": "Marble",
    "AMARGO": "Amargosa",
    "NWEST230": "Northwest 230",
    "MERCURY": "Mercury",
    "HA500": "HA500",
    "SUMMIT120": "Summit",
}

# ``<CODE>_ITC|_ISL <scheduling points…> Import <net> <sched> <unused> <MIC> <OTC>``
# The scheduling-point field is free text (may hold spaces and ``&``), so the
# row is anchored on the code, the literal Import direction, and the five
# trailing integers. Column separators are NOT reliably spaces: the 2024
# filing's PDF renders several rows with the code glued to the scheduling
# point (``NEWMELONP_ITCNML230``) and the scheduling point glued to the
# direction (``RANCHOSECOImport``), so neither boundary may require
# whitespace.
_ROW = re.compile(
    r"^(?P<code>[A-Z0-9\-]+)_(?:ITC|ISL|BG).*?Import"
    r"\s+(?P<net>-?\d+)\s+(?P<sched>-?\d+)\s+(?P<unused>-?\d+)"
    r"\s+(?P<mic>-?\d+)\s+(?P<otc>-?\d+)\s*$"
)


def fetch_mic_pdf(year: int, cache_dir: Path) -> tuple[Path, str]:
    """Download the year's MIC filing, returning ``(local_path, source_url)``.

    Tries each pattern in :data:`MIC_URL_PATTERNS` and keeps the first that
    returns a plausible PDF, so the returned URL is the one that served it.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"caiso_mic_{year}.pdf"
    for pattern in MIC_URL_PATTERNS:
        url = pattern.format(year=year)
        try:
            with urllib.request.urlopen(url, timeout=90) as resp:
                payload = resp.read()
        except Exception:  # noqa: BLE001 — try the next naming pattern
            continue
        if payload[:4] == b"%PDF" and len(payload) > 5_000:
            path.write_bytes(payload)
            return path, url
    raise FileNotFoundError(f"no MIC filing found for {year} (tried every pattern)")


def parse_mic(pdf_path: Path) -> dict[str, int]:
    """Return ``{display_name: maximum_import_capability_mw}`` for one filing.

    Zero-MIC branch groups are dropped here (the committed convention); an
    unmapped OASIS code raises rather than silently inventing a display name.
    """
    from pypdf import PdfReader

    text = "\n".join(page.extract_text() for page in PdfReader(pdf_path).pages)
    out: dict[str, int] = {}
    for line in text.splitlines():
        m = _ROW.match(line.strip())
        if not m:
            continue
        code = m.group("code")
        mic = int(m.group("mic"))
        if mic == 0:
            continue
        if code not in BG_DISPLAY_NAME:
            raise KeyError(
                f"{pdf_path.name}: unmapped branch-group code {code!r} — add it "
                "to BG_DISPLAY_NAME with CAISO's own report name"
            )
        out[BG_DISPLAY_NAME[code]] = mic
    if not out:
        raise ValueError(f"{pdf_path.name}: parsed no MIC rows")
    return out


def rows_for_year(year: int, cache_dir: Path) -> list[dict]:
    """Return the registry rows for one delivery year's MIC filing."""
    pdf_path, url = fetch_mic_pdf(year, cache_dir)
    return [
        {
            "iso": "CAISO",
            "delivery_year": year,
            "season": "annual",
            "area": area,
            "area_type": "branch_group",
            "metric": "import_limit",
            "value_mw": mic,
            "value_pu": "",
            "source_doc": url,
            "source_page": 1,
        }
        for area, mic in parse_mic(pdf_path).items()
    ]


def verify(years: list[int], cache_dir: Path) -> int:
    """Assert the parser reproduces the committed rows for ``years``.

    Returns a process exit code: 0 when every year matches value-for-value.
    """
    import pandas as pd

    committed = pd.read_csv(OUT_PATH)
    committed = committed[
        (committed["area_type"] == "branch_group")
        & (committed["metric"] == "import_limit")
    ]
    bad = 0
    for year in years:
        want = dict(
            zip(
                committed[committed["delivery_year"] == year]["area"],
                committed[committed["delivery_year"] == year]["value_mw"].astype(int),
                strict=True,
            )
        )
        got = parse_mic(fetch_mic_pdf(year, cache_dir)[0])
        if got == want:
            print(f"  {year}: MATCH ({len(got)} branch groups)")
            continue
        bad += 1
        print(f"  {year}: MISMATCH ({len(got)} parsed vs {len(want)} committed)")
        for area in sorted(set(want) | set(got)):
            if want.get(area) != got.get(area):
                print(
                    f"    {area:24s} committed={want.get(area)} parsed={got.get(area)}"
                )
    return 1 if bad else 0


def main() -> None:
    """Verify against committed years, or transcribe new delivery years."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--verify",
        nargs="+",
        type=int,
        default=None,
        help="assert the parser reproduces these already-committed delivery "
        "years exactly, then exit (the lineage proof for a back-year run)",
    )
    ap.add_argument("--years", nargs="+", type=int, default=None)
    ap.add_argument(
        "--merge",
        action="store_true",
        help="merge into the committed registry, keeping every existing row "
        "byte-identical (a delivery year already present is left alone)",
    )
    ap.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("/tmp/caiso-mic-pdfs"),
        help="where the fetched filings are cached (not committed)",
    )
    args = ap.parse_args()

    if args.verify:
        print("verifying parser against committed rows:")
        sys.exit(verify(args.verify, args.cache_dir))
    if not args.years:
        ap.error("pass --years or --verify")

    new_rows: list[dict] = []
    for year in sorted(args.years):
        year_rows = rows_for_year(year, args.cache_dir)
        print(f"  {year}: {len(year_rows)} branch groups")
        new_rows.extend(year_rows)

    if not args.merge:
        w = csv.DictWriter(sys.stdout, fieldnames=FIELDNAMES)
        w.writeheader()
        w.writerows(new_rows)
        return

    existing = list(csv.DictReader(OUT_PATH.open()))
    have = {
        (r["delivery_year"], r["area"], r["area_type"], r["metric"]) for r in existing
    }
    added = [
        r
        for r in new_rows
        if (str(r["delivery_year"]), r["area"], r["area_type"], r["metric"]) not in have
    ]
    # Byte-APPEND, never rewrite: the committed file carries mixed line endings
    # (its first 139 rows CRLF, its last 15 LF, from successive hand-appends),
    # so re-emitting the existing rows through csv.writer would normalise them
    # and churn every committed line. The existing bytes are left untouched and
    # only the new rows are written.
    blob = OUT_PATH.read_bytes()
    buf = io.StringIO()
    csv.DictWriter(buf, fieldnames=FIELDNAMES).writerows(added)
    with OUT_PATH.open("ab") as fh:
        if blob and not blob.endswith((b"\n", b"\r")):
            fh.write(b"\r\n")
        fh.write(buf.getvalue().encode())
    print(
        f"merged: kept {len(existing)} committed rows byte-frozen, added {len(added)}"
    )


if __name__ == "__main__":
    main()

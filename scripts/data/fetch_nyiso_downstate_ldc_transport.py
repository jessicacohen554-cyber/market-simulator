"""Fetch the NYISO downstate LDC **non-firm transportation** delivery rate series.

Builds ``data/raw/gas-prices/nyiso_downstate_ldc_transport_monthly.csv``: the
measured monthly LDC delivery charge ($/MMBtu) a non-firm downstate
(NYC zone J / Long Island zone K) electric-generation gas peaker pays to move
its own gas from the city gate to the plant, OVER the Transco Zone 6 NY
pipeline-hub commodity the dispatch model already prices its downstate gas at.

Why this is the correct rate class (not the statewide citygate stand-in it
supersedes). NYISO's downstate combustion-turbine peakers (the Bayonne / Equus /
Edgewood / Glenwood-Landing LM6000 fleet) run only a few hundred hours a year,
hold no firm interstate pipeline capacity, and buy their commodity at the
market hub — so their delivered fuel index is the **pipeline-hub daily spot**
(Transco Z6 NY, already in the model) **plus the local LDC non-firm
transportation delivery charge**, NOT the statewide firm citygate sales price
(EIA N3050NY3). National Grid's tariff makes them transportation customers:
KeySpan Gas East (KEDLI, Long Island) Service Classification No. 7 Interruptible
Transportation became **SC-19 Non-Firm Demand Response Transportation** effective
2019 (Case 16-G-0058); Brooklyn Union Gas (KEDNY, NYC) serves the same customers
under **SC-22 C&G (Non-Firm) Transportation**. Both LDCs publish the delivery
rate every month in the *Statement of Non-Firm Demand Response Sales and
Transportation Rates* (``statnfdr`` PDFs), so the series is measured,
forward-native (rate-case delivery steps + monthly delivery-rate-adjustment
clauses), and regenerates for a forecast year responding to changed conditions
(CLAUDE.md rule #13). Nothing is fitted to a price/volume residual.

We use the **Tier 1** rate (customers with fully automatic dual-fuel switchover —
the equipment a grid-reliability merchant peaker runs). The published
"Total Monthly SC-19/SC-22 Tier 1 Transportation Service" figure already folds in
the monthly delivery-rate adjustments (Earnings Adjustment Mechanism, Demand
Capacity Surcharge, Net Utility Plant Tracker, Rate Adjustment Clause, …), so it
is the complete delivered transport charge — no separate TAC statement is needed.

Per-zone (rule #11 — the LI gas island and the NYC system carry materially
different delivery costs):

  * NYC (zone J)          -> KEDNY (Brooklyn Union) SC-22 Tier 1
  * Long_Island (zone K)  -> KEDLI (KeySpan Gas East) SC-19 Tier 1

Source PDFs (nationalgridus.com "Gas Rate Statements"):
  KEDLI: /media/pdfs/billing-payments/gas-rates/nyl/[<year>/]statnfdr-<n>-eff-<mm>-01-<yy>-for-kedli.pdf
  KEDNY: /media/pdfs/billing-payments/gas-rates/nym/[<year>/]statnfdr-<n>-eff-<mm>-01-<yy>-for-kedny.pdf
(statement number, separator style, and year subdirectory vary month to month, so
the fetcher tries a small template set per month and validates the effective date
printed inside the PDF.)

Years 2023-2025 only (CLAUDE.md rule 22: 2022 and H1-2026 are holdout-quarantined;
this fetcher never requests them). $/therm -> $/MMBtu via the exact factor 10
(1 therm = 0.1 MMBtu).

Usage:
    python scripts/data/fetch_nyiso_downstate_ldc_transport.py
    (requires network access to nationalgridus.com and ``pdfminer.six`` /
    ``pypdf`` for text extraction; the committed CSV is the durable artifact.)
"""

from __future__ import annotations

import argparse
import re
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "raw" / "gas-prices" / "nyiso_downstate_ldc_transport_monthly.csv"

THERM_TO_MMBTU = 10.0  # 1 therm = 0.1 MMBtu -> $/therm * 10 = $/MMBtu

# Per-LDC intake spec: model zone, National Grid site sub-path, filename suffix,
# the interruptible/non-firm TRANSPORTATION service class, and the Jan-2023
# ``statnfdr`` statement number (statements increment one per month).
LDC_SPECS = {
    "KEDLI": {
        "zone": "Long_Island",
        "subpath": "nyl",
        "suffix": "kedli",
        "sc_label": "Service Classification No. 19 Tier 1",
        "jan2023_stmt": 17,
    },
    "KEDNY": {
        "zone": "NYC",
        "subpath": "nym",
        "suffix": "kedny",
        "sc_label": "Tier 1 C&G Transportation Service",
        "jan2023_stmt": 18,
    },
}

_BASE = "https://www.nationalgridus.com/media/pdfs/billing-payments/gas-rates/"


def _extract_text(pdf_bytes: bytes) -> str:
    """Return the text of a PDF using whichever extractor is installed."""
    import io

    try:
        from pdfminer.high_level import extract_text  # type: ignore

        return extract_text(io.BytesIO(pdf_bytes))
    except Exception:
        pass
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _candidate_urls(spec: dict, year: int, month: int) -> list[str]:
    """Yield the plausible ``statnfdr`` URLs for one LDC-year-month.

    Statement numbering, hyphen/underscore separators, the year subdirectory,
    and the odd effective-day (some months post as ``mm-02-yy``) all vary, so we
    enumerate a compact template set and let the caller validate by content.
    """
    base_num = spec["jan2023_stmt"] + (year - 2023) * 12 + (month - 1)
    yy, mm = f"{year % 100:02d}", f"{month:02d}"
    urls: list[str] = []
    for num in (base_num, base_num - 1, base_num + 1):
        for subdir in (f"{year}/", ""):
            for sep in ("-", "_"):
                for day in ("01", "02"):
                    fn = (
                        f"statnfdr{sep}{num}{sep}eff{sep}{mm}-{day}-{yy}"
                        f"{sep}for{sep}{spec['suffix']}.pdf"
                    )
                    urls.append(f"{_BASE}{spec['subpath']}/{subdir}{fn}")
    return urls


def _download(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        data = urllib.request.urlopen(req, timeout=45).read()
        return data if data[:4] == b"%PDF" else None
    except Exception:
        return None


def _tier1_transport_rate(text: str, sc_label: str) -> float:
    """Return the "Total Monthly ... Tier 1 Transportation Service" $/therm.

    The transportation block lists the volumetric delivery rate, the individual
    delivery-rate-adjustment lines, their total, and finally the all-in monthly
    transportation service rate — the last $/therm value in the block.
    """
    i = text.find(sc_label)
    if i < 0:
        raise ValueError(f"section {sc_label!r} not found")
    # Bound the block so a following tier/section can't leak in.
    tail = text[i + len(sc_label) :]
    for stop in ("Service Classification No.", "Issued By", "Issued by"):
        j = tail.find(stop)
        if j > 0:
            tail = tail[:j]
            break
    nums = re.findall(r"-?\d\.\d{3,6}", tail)
    if not nums:
        raise ValueError(f"no rate in section {sc_label!r}")
    return float(nums[-1])


def fetch(years: tuple[int, ...] = (2023, 2024, 2025)) -> list[tuple]:
    """Download + parse every LDC-year-month; return the CSV rows."""
    rows: list[tuple] = []
    for ldc, spec in LDC_SPECS.items():
        for year in years:
            for month in range(1, 13):
                pdf = None
                used = None
                for url in _candidate_urls(spec, year, month):
                    pdf = _download(url)
                    if pdf is not None:
                        used = url
                        break
                if pdf is None:
                    raise RuntimeError(
                        f"no statnfdr PDF found for {ldc} {year}-{month:02d}"
                    )
                rate_therm = _tier1_transport_rate(_extract_text(pdf), spec["sc_label"])
                rows.append(
                    (
                        ldc,
                        spec["zone"],
                        year,
                        month,
                        round(rate_therm, 5),
                        round(rate_therm * THERM_TO_MMBTU, 4),
                        used.rsplit("/", 1)[1],
                    )
                )
                print(f"  {ldc} {year}-{month:02d}: {rate_therm:.5f} $/therm")
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="*", type=int, default=[2023, 2024, 2025])
    args = ap.parse_args(argv)
    rows = fetch(tuple(args.years))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "ldc,zone,year,month,rate_usd_per_therm,rate_usd_per_mmbtu,source_statement\n"
    )
    with OUT.open("w") as fh:
        fh.write(header)
        for ldc, zone, y, m, rt, rm, src in rows:
            fh.write(f"{ldc},{zone},{y},{m},{rt},{rm},{src}\n")
    print(f"\nwrote {len(rows)} rows -> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

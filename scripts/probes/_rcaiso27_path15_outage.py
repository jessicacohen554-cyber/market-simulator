"""R-CAISO-27 probe: does a public outage record cover the Path-15 / Gates-Midway elements? Zero LP.

Reads CAISO OASIS ``TRNS_OUTAGE`` (the public transmission-outage report, field
``CURTAILED_OTC_MW``) for sample months 2022-25, fetched live, nothing committed, and reports:

- every distinct ``TI_ID`` (the interface the curtailment is booked against), and
- the rows whose equipment / notes text names a Path-15 element (Gates, Midway, Arco, Los Banos).

The question is coverage: if no ``TI_ID`` is an internal path, the report is intertie-scoped and an
internal element appears only as the CAUSE of an intertie curtailment, which is not an availability
series for that element.

Usage: ``python3 scripts/probes/_rcaiso27_path15_outage.py``.
Record: ``docs/handoffs/r-caiso-27/FINDING-r-caiso-27-path15-outage-data-2026-10-01.md``.
"""

from __future__ import annotations

import io
import time
import urllib.request
import zipfile

import pandas as pd

OASIS = (
    "https://oasis.caiso.com/oasisapi/SingleZip?queryname=TRNS_OUTAGE"
    "&startdatetime={a}T07:00-0000&enddatetime={b}T07:00-0000&version=1&resultformat=6"
)
MONTHS = [("20220601", "20220630"), ("20231101", "20231130"), ("20240601", "20240630")]
PATH15 = r"gates|midway|arco|los ?banos"


def fetch(a: str, b: str) -> pd.DataFrame:
    """Return one OASIS ``TRNS_OUTAGE`` window as a DataFrame (empty on an OASIS error)."""
    raw = urllib.request.urlopen(OASIS.format(a=a, b=b), timeout=180).read()
    z = zipfile.ZipFile(io.BytesIO(raw))
    csv = [n for n in z.namelist() if n.endswith(".csv")]
    return pd.read_csv(z.open(csv[0])) if csv else pd.DataFrame()


def main() -> None:
    """Print TI_ID coverage and the Path-15-element rows for each sample month."""
    ids: set[str] = set()
    for a, b in MONTHS:
        d = fetch(a, b)
        if d.empty:
            print(f"{a}: OASIS returned no CSV")
            continue
        ids |= set(d.TI_ID.unique())
        text = d.EQUIPMENT_OUTAGE.astype(str) + " " + d.OUTAGE_NOTES.astype(str)
        hit = d[text.str.contains(PATH15, case=False, regex=True)]
        print(f"{a}: rows {len(d)}, Path-15-element rows {len(hit)}")
        if len(hit):
            print(
                hit.groupby("TI_ID").CURTAILED_OTC_MW.agg(["count", "max"]).to_string()
            )
        time.sleep(8)  # OASIS rate limit
    print(f"distinct TI_IDs ({len(ids)}):", " ".join(sorted(ids)))


if __name__ == "__main__":
    main()

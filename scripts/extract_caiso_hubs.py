"""Extract the CAISO trading hubs from full-grid OASIS GRP zips into the raw
window-CSV format that :mod:`scripts.postprocess_oasis_downloads` folds into the
hourly aggregates.

The CAISO Historical OASIS bulk archive (``s3://caiso-oasis-s3-prod-groupzips``)
serves *full-grid* GRP exports: DAM ``PRC_LMP`` (one file/day, all nodes) and
RTM 5-minute ``PRC_INTVL_LMP`` (one file/hour, all nodes), each zip holding one
inner CSV per price component (LMP/MCE/MCC/MCL[/MGHG]). This keeps only the
three trading hubs (TH_NP15/SP15/ZP26_GEN-APND) and concatenates them into one
raw CSV per market so the frozen postprocess seam sees exactly the columns it
expects (INTERVALSTARTTIME_GMT, NODE, LMP_TYPE, MW/VALUE).

HASP and RTPD (Fifteen Minute) zips are ignored two ways: the file glob matches
only ``*_DAM_LMP_GRP_*`` / ``*_RTM_LMP_GRP_*``, and the inner-CSV filter only
reads ``PRC_LMP_DAM_`` / ``PRC_INTVL_LMP_RTM_`` members — so a stray zip yields
no rows rather than wrong-market prices.

The DAM GRP export omits the MGHG component file; every existing DAM/RTM hub row
has GHG = 0.0 (TH_ APNodes carry no GHG adder), so MGHG=0.0 twins are synthesized
from the DAM LMP rows to match the aggregate schema.

Usage::

    python scripts/extract_caiso_hubs.py --zip-dir <dir_of_zips> --out-dir <dir>

Writes ``{dam,rtm}_hubs_<mindate>_<maxdate>.csv`` into ``--out-dir`` (only for
markets that produced rows). Those names match postprocess's raw-window glob, so
a subsequent ``python scripts/postprocess_oasis_downloads.py`` picks them up.
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

HUBS = ("TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND")


def _hub_rows(zip_path: Path, inner_token: str) -> tuple[str | None, list[str]]:
    """Return ``(header, hub_rows)`` from a zip's inner CSVs matching a token.

    ``header`` is the shared column line from the first matching member;
    ``hub_rows`` are the raw data lines whose text contains a trading-hub name.
    """
    header: str | None = None
    rows: list[str] = []
    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            if inner_token not in name or not name.endswith(".csv"):
                continue
            with zf.open(name) as fh:
                text = io.TextIOWrapper(fh, encoding="utf-8")
                head = text.readline().rstrip("\n")
                header = header or head
                rows.extend(
                    ln.rstrip("\n") for ln in text if any(h in ln for h in HUBS)
                )
    return header, rows


def _date_tag(rows: list[str], header: str) -> str:
    """Return ``<mindate>_<maxdate>`` (YYYYMMDD) from the OPR_DT column."""
    idx = header.split(",").index("OPR_DT")
    dates = sorted({r.split(",")[idx].replace("-", "") for r in rows})
    return f"{dates[0]}_{dates[-1]}"


def build_market(zips: list[Path], inner_token: str, synth_mghg: bool):
    """Collect hub rows across ``zips``; return ``(header, all_rows)``."""
    header: str | None = None
    body: list[str] = []
    mghg: list[str] = []
    for z in sorted(zips):
        head, rows = _hub_rows(z, inner_token)
        if head is None:
            continue
        header = header or head
        body.extend(rows)
        if synth_mghg:
            cols = header.split(",")
            i_type, i_val = cols.index("LMP_TYPE"), cols.index("MW")
            _, lmp_rows = _hub_rows(z, inner_token + "LMP")
            for ln in lmp_rows:
                f = ln.split(",")
                f[i_type], f[i_val] = "MGHG", "0"
                mghg.append(",".join(f))
    return header, body + mghg


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--zip-dir", type=Path, required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    plans = (
        # (market, filename glob, inner-CSV token, synthesize MGHG twins?)
        ("dam", "*_DAM_LMP_GRP_*.zip", "PRC_LMP_DAM_", True),
        ("rtm", "*_RTM_LMP_GRP_*.zip", "PRC_INTVL_LMP_RTM_", False),
    )
    for mkt, glob, token, synth in plans:
        zips = list(args.zip_dir.glob(glob))
        if not zips:
            print(f"{mkt}: no zips matching {glob}")
            continue
        header, rows = build_market(zips, token, synth)
        if not header or not rows:
            print(f"{mkt}: {len(zips)} zip(s) but no hub rows found")
            continue
        tag = _date_tag(rows, header)
        out = args.out_dir / f"{mkt}_hubs_{tag}.csv"
        out.write_text("\n".join([header] + rows) + "\n")
        print(f"{mkt}: {len(zips)} zip(s) -> {out.name} ({len(rows)} hub rows)")


if __name__ == "__main__":
    main()

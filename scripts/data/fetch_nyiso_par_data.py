"""Fetch and curate NYISO's NY-NJ PAR postings: P-33 ``outSched`` + P-34 ``ParFlows``.

Both halves of the eastern-seam attribution identified at nyiso-126 and amended
at nyiso-127 (``results/calibration/PREREG-nyiso127-addendum-eastern-seam-availability-source-2026-08-05.md``).

Why two postings
----------------
NYISO's *"NY-NJ PAR Interchange Percentages, Operational Base Flow (OBF), and
other MW Offsets"* posting directs a published percentage of the PJM-AC
interchange over eight named PARs, and reverts an out-of-service PAR's share to
the free-flowing western AC ties. Applying that rule needs three things, and one
posting alone supplies none of them completely:

* the **eight percentages** — the posting itself, cited constants, no intake;
* the **PAR in-service state** — **P-33 ``outSched``** (``Scheduled Outages``),
  which publishes ``Scheduled Out``/``Scheduled In`` per facility PTID;
* the **PAR ↔ PTID identity** — also **P-33 ``outSched``**, whose
  ``Equipment Name`` matches the posting's PAR names exactly. ``ParFlows``
  carries a bare numeric ``Point ID`` and no name at all, which is why it cannot
  be the identifying source (nyiso-127 addendum §1).

**P-34 ``ParFlows``** (5-minute measured flow per PAR PTID) is intaken as the
**independent corroboration**: a PAR that ``outSched`` says is out must measure
exactly zero flow. Measured 2023-01, that holds to the interval (addendum §3).

Source URLs (no authentication; all 72 monthly archives 2023-2025 verified
HTTP 200)::

    http://mis.nyiso.com/public/csv/outSched/<yyyymm01>outSched_csv.zip
    http://mis.nyiso.com/public/csv/ParFlows/<yyyymm01>ParFlows_csv.zip

Outputs (``data/raw/NYISO/par-data/``)
--------------------------------------
* ``NYISO_par_outages.csv`` — one row per (PAR, outage window): the deduplicated
  ``Scheduled Out``/``Scheduled In`` spans for the eight named PARs, with their
  posting name, interface and published share. Small and human-auditable.
* ``NYISO_par_flows_hourly_<year>.csv.gz`` — hourly mean measured flow for the
  eight named PARs. Curated to the eight the posting names (of 63 PTIDs in the
  raw series) because those are the only ones the attribution reads; the full
  P-34 series remains the cited source.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only — the training window. Intake of an
out-of-training window would need its own session-logged owner authorization.
This intake runs under the owner authorization of 2026-08-05 ("Authorise intake
+ execute").
"""

from __future__ import annotations

import argparse
import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

from market_sim.config.paths import RAW_DIR
from market_sim.data.nyiso_par_attribution import PAR_REGISTRY

OUT_DIR = RAW_DIR / "NYISO" / "par-data"
MIS = "http://mis.nyiso.com/public/csv"
YEARS = (2023, 2024, 2025)

# PAR_REGISTRY (the eight published PAR -> PTID identities, their interface and
# share) lives in market_sim.data.nyiso_par_attribution — the LP reads it too,
# so there is exactly one copy (rule 24 [R-REGISTRY]).


def _fetch_month(report: str, year: int, month: int, cache: Path) -> Path:
    """Download one monthly MIS archive, skipping an already-present file."""
    name = f"{year}{month:02d}01{report}_csv.zip"
    dest = cache / name
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f"{MIS}/{report}/{name}"
    resp = requests.get(url, timeout=300)
    resp.raise_for_status()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(resp.content)
    return dest


def _read_archive(path: Path) -> pd.DataFrame:
    """Concatenate every daily CSV member of one monthly zip."""
    zf = zipfile.ZipFile(path)
    return pd.concat(
        [pd.read_csv(io.BytesIO(zf.read(n))) for n in zf.namelist()],
        ignore_index=True,
    )


def build_par_outages(cache: Path) -> pd.DataFrame:
    """Deduplicated outage windows for the eight named PARs.

    ``outSched`` re-posts every open outage on every daily snapshot, and a
    long-term outage's ``Scheduled In`` is rolled forward as it is extended, so
    the raw feed carries one row per (snapshot, outage). Deduplicating on
    (PTID, out, in) leaves one row per distinct published window; the union of
    those windows is the PAR's out-of-service state.

    Args:
        cache: Directory holding the fetched ``outSched`` monthly zips.

    Returns:
        One row per (PAR, window), with the posting name, interface and share.
    """
    frames = [
        _read_archive(_fetch_month("outSched", y, m, cache))
        for y in YEARS
        for m in range(1, 13)
    ]
    raw = pd.concat(frames, ignore_index=True)
    sel = raw[raw["PTID"].isin(PAR_REGISTRY)].copy()
    sel["outage_start"] = pd.to_datetime(
        sel["Scheduled Out Date/Time"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    sel["outage_end"] = pd.to_datetime(
        sel["Scheduled In Date/Time"], format="%m/%d/%Y %H:%M:%S", errors="coerce"
    )
    sel = sel.dropna(subset=["outage_start", "outage_end"])
    out = sel.drop_duplicates(subset=["PTID", "outage_start", "outage_end"])[
        ["PTID", "Equipment Name", "outage_start", "outage_end"]
    ].copy()
    out.columns = ["ptid", "equipment_name", "outage_start", "outage_end"]
    out["par"] = out["ptid"].map(lambda p: PAR_REGISTRY[p][0])
    out["interface"] = out["ptid"].map(lambda p: PAR_REGISTRY[p][2])
    out["published_share"] = out["ptid"].map(lambda p: PAR_REGISTRY[p][3])
    return out.sort_values(["interface", "ptid", "outage_start"]).reset_index(drop=True)


def build_par_flows(year: int, cache: Path) -> pd.DataFrame:
    """Hourly mean measured flow for the eight named PARs in ``year``.

    Args:
        year: Training year to curate.
        cache: Directory holding the fetched ``ParFlows`` monthly zips.

    Returns:
        Columns ``interval_start_local, ptid, par, interface, flow_mw``. Keyed by
        LOCAL wall-clock, never positionally; the DST fall-back hour's duplicate
        label is averaged so the key stays unique.
    """
    frames = [
        _read_archive(_fetch_month("ParFlows", year, m, cache)) for m in range(1, 13)
    ]
    raw = pd.concat(frames, ignore_index=True)
    sel = raw[raw["Point ID"].isin(PAR_REGISTRY)].copy()
    ts = pd.to_datetime(sel["Timestamp"], format="%m/%d/%Y %H:%M:%S")
    sel["interval_start_local"] = ts.dt.floor("h")
    hourly = (
        sel.groupby(["interval_start_local", "Point ID"])["Flow (MWH)"]
        .mean()
        .reset_index()
    )
    hourly.columns = ["interval_start_local", "ptid", "flow_mw"]
    hourly["par"] = hourly["ptid"].map(lambda p: PAR_REGISTRY[p][0])
    hourly["interface"] = hourly["ptid"].map(lambda p: PAR_REGISTRY[p][2])
    return hourly.sort_values(["interval_start_local", "ptid"]).reset_index(drop=True)


def main() -> None:
    """Fetch both postings and write the curated per-PAR artifacts."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--cache",
        type=Path,
        required=True,
        help="Directory for the raw monthly MIS zips (not committed).",
    )
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    outages = build_par_outages(args.cache)
    dest = OUT_DIR / "NYISO_par_outages.csv"
    outages.to_csv(dest, index=False)
    print(f"wrote {dest}  ({len(outages)} windows, {outages['ptid'].nunique()} PARs)")

    for year in YEARS:
        flows = build_par_flows(year, args.cache)
        dest = OUT_DIR / f"NYISO_par_flows_hourly_{year}.csv.gz"
        flows.to_csv(dest, index=False, compression="gzip")
        print(f"wrote {dest}  ({len(flows):,} rows)")


if __name__ == "__main__":
    main()

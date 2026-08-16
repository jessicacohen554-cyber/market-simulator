"""Reduce hand-downloaded CAISO OASIS *GRP* (all-node) zips to hub window CSVs.

The OASIS "single zip" bulk downloads (``PRC_LMP`` DAM / ``PRC_INTVL_LMP``
RTM ``*_LMP_GRP_*_csv.zip``, one component file per LMP_TYPE, every node in
the system, ~15k nodes) are far bulkier than the per-hub window CSVs
``scripts/data/fetch_caiso_oasis.py`` produces — but they are the only route to
history that has aged out of the OASIS API's ~39-month retention (the
2023-01-01..2023-03-09 hole in ``CAISO_dam_hourly_2023.csv``; probed
2026-06-22, see ``scripts/data/derive_actual_lmp.py`` CAISO_MIN_HOURS note).

This script extracts ONLY the handful of nodes the aggregates carry — see
:data:`NODES`: the three trading hubs (``fetch_caiso_oasis.HUBS``, the same
TH_NP15/TH_SP15/TH_ZP26 system-price basis ``derive_actual_lmp.py``
load-weights), the WECC intertie nodes, and since caiso-165 the four
``DLAP_*-APND`` load aggregation points — and writes
them as compact per-day window CSVs (``{market}_grp_{Ymd}_{Ymd}.csv``,
columns ``INTERVALSTARTTIME_GMT, NODE, LMP_TYPE, MW``) into the same
directory. Those windows are then folded into the committed hourly
aggregates by the EXISTING pipeline — run
``scripts/data/postprocess_oasis_downloads.py`` afterwards; its ``dam_*``/
``rtm_*`` globs match the window names, its (timestamp, node) de-dup makes
the fold idempotent, and ``--stage-dir`` moves the processed windows out.

Markets: ``dam`` (PRC_LMP) is folded by default. ``rtm`` (PRC_INTVL_LMP
5-minute) requires ``--markets rtm`` explicitly — fold it only when the raw
zips cover enough of a month to stand for it: the C3a/C3b scorer unmasks a
month the moment its monthly mean exists, so a month fabricated from a few
storm-day hours would enter the GATED benchmark as if it covered the whole
month (the 2023-01 RTM zips on hand span ~34 scattered hours of Jan 1-4 —
left unfolded for exactly that reason). HASP zips (hour-ahead, a different
market run from either aggregate) are never folded.

Duplicate download copies (`` 2.zip`` suffixes) are skipped by name.

Usage:
    python scripts/data/fold_caiso_oasis_grp_zips.py                 # extract DAM windows
    python scripts/data/fold_caiso_oasis_grp_zips.py --markets dam rtm
    python scripts/data/postprocess_oasis_downloads.py --stage-dir /tmp/oasis-raw
"""

from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))  # repo root: canonical scripts.data.* sibling imports on direct run
sys.path.insert(0, str(REPO / "src"))

from scripts.data.fetch_caiso_intertie_lmp import INTERTIE_NODES  # noqa: E402
from scripts.data.fetch_caiso_oasis import DLAPS, HUBS  # noqa: E402  (single source for both sets)
from market_sim.config import paths  # noqa: E402

LMP_DIR = paths.RAW_DATA_DIR / "lmp-data" / "CAISO"

# Hub nodes + the WECC intertie nodes (MALIN/CAPTJACK/PALOVRDE) + the four
# DLAP load aggregation points — the bulk zips are the only route to history
# that has aged out of the API's retention, and since caiso-165 that history
# includes the DLAP component record (see the NODES note in
# scripts/data/extract_caiso_hubs.py).
#
# Widening this set does NOT retroactively widen already-extracted windows:
# ``fold`` skips a window whose CSV exists, so a window written before the
# DLAPs were added stays hub-only. Pass ``--refold`` to rewrite it.
NODES = HUBS + DLAPS + tuple(n for ns in INTERTIE_NODES.values() for n in ns)

# GRP zip name: {Ymd}_{Ymd}_{DAM|RTM|HASP}_LMP_GRP_{group}_{...}_csv.zip
_GRP_NAME = re.compile(
    r"^(?P<start>\d{8})_(?P<end>\d{8})_(?P<market>DAM|RTM|HASP)_LMP_GRP_.*_csv\.zip$"
)
# Duplicate-download suffix ("... 2.zip") left by a browser re-download.
_DUP_NAME = re.compile(r" \d+\.zip$")

# Columns kept from the raw component CSVs — the schema
# postprocess_oasis_downloads._lmp_frames pivots on.
_KEEP = ["INTERVALSTARTTIME_GMT", "NODE", "LMP_TYPE", "MW"]


def _window_frames(zip_path: Path) -> pd.DataFrame | None:
    """Kept-node rows from every component CSV inside one GRP zip.

    Each member file carries one LMP_TYPE (LMP/MCE/MCC/MCL/MGHG) for every
    node; the concatenated hub subset pivots back to the wide component
    columns downstream. Returns ``None`` when the zip holds no CSV members.
    """
    frames: list[pd.DataFrame] = []
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if not member.lower().endswith(".csv"):
                continue
            with zf.open(member) as fh:
                df = pd.read_csv(fh, usecols=_KEEP)
            frames.append(df[df["NODE"].isin(NODES)])
    if not frames:
        return None
    return pd.concat(frames, ignore_index=True)


def fold(markets: tuple[str, ...], refold: bool = False) -> list[Path]:
    """Extract node window CSVs for ``markets`` from every GRP zip in place.

    Zips whose window CSV already exists are skipped (re-runs only fill
    gaps), so the extraction is idempotent and resumable. Pass ``refold`` to
    rewrite them instead — needed after :data:`NODES` widens, since an
    existing window was written against the older, narrower node set and
    would otherwise silently stay narrow. Returns the window paths written.
    """
    written: list[Path] = []
    # One window per (market, day): group-numbered zips (RTM hour groups)
    # append into the same day window.
    by_window: dict[Path, list[Path]] = {}
    for zip_path in sorted(LMP_DIR.glob("*_csv*.zip")):
        if _DUP_NAME.search(zip_path.name):
            print(f"skip duplicate copy: {zip_path.name}")
            continue
        m = _GRP_NAME.match(zip_path.name)
        if not m or m["market"].lower() not in markets:
            continue
        out = LMP_DIR / f"{m['market'].lower()}_grp_{m['start']}_{m['end']}.csv"
        by_window.setdefault(out, []).append(zip_path)
    for out, zips in sorted(by_window.items()):
        if out.exists() and not refold:
            print(f"skip existing window: {out.name}")
            continue
        parts = [f for z in zips if (f := _window_frames(z)) is not None]
        if not parts:
            continue
        frame = pd.concat(parts, ignore_index=True).drop_duplicates()
        frame.to_csv(out, index=False)
        written.append(out)
        print(
            f"wrote {out.name} ({len(frame)} rows, "
            f"{frame['NODE'].nunique()} nodes, from {len(zips)} zip(s))"
        )
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--markets",
        nargs="+",
        choices=("dam", "rtm"),
        default=["dam"],
        help="GRP markets to extract (HASP is never folded; rtm only when its "
        "raw coverage can honestly stand for the months it unmasks)",
    )
    parser.add_argument(
        "--refold",
        action="store_true",
        help="rewrite windows that already exist; use after the kept-node set "
        "widens, since an existing window was extracted against the older set",
    )
    args = parser.parse_args()
    written = fold(tuple(args.markets), refold=args.refold)
    if written:
        print(
            f"{len(written)} window(s) written — now run "
            "scripts/data/postprocess_oasis_downloads.py --stage-dir <dir> to fold "
            "them into the hourly aggregates"
        )
    else:
        print("nothing to extract — no unprocessed GRP zips found")


if __name__ == "__main__":
    main()

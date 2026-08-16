"""Re-stage the NYISO public zonal LBMP monthly archives (DA + 5-minute RT).

The durable record of NYISO actual prices is the committed
``data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet``; its *sources*
— the monthly ``mis.nyiso.com`` zips — are deliberately gitignored as
regenerable (``.gitignore`` §"Transient outer container", and the per-ISO row
of ``data/raw/lmp-data/README.md``). A fresh clone therefore has no DA source
at all and only a partial RT set, so ``derive_actual_lmp.py`` cannot rebuild
the parquet on full coverage. This script restores that coverage.

It replaces the bare ``for m in 01..12; curl -O ...`` loop the README recorded
as the DA "regeneration" recipe, and it is the fetch half of the NYISO RTD
interval-convention repair (session nyiso-139, owner decision D3 option (b),
"re-stage the NYISO RT archive, repair first").

Two products, both public and uncredentialed:

* **DA** ``csv/damlbmp/<YYYYMM>01damlbmp_zone_csv.zip`` — hourly day-ahead
  zonal LBMP. ``derive_actual_lmp._nyiso_wide`` reads these from a single
  outer container, ``lmp-data/NYISO/NYISO_zonal_hourly.zip``, which this
  script assembles (each monthly zip stored as one nested entry, the basename
  layout that reader's ``startswith(year)`` / ``"damlbmp_zone" in base`` filter
  expects).
* **RT** ``csv/realtime/<YYYYMM>01realtime_zone_csv.zip`` — 5-minute
  preliminary ex-post zonal LBMP, read flat from the same directory.

Idempotent by design: an existing file that opens as a valid zip is left
untouched, so the 21 RT months already committed to the pack (including the
twelve 2022 rule-22 intake months) keep their exact committed bytes and are
never re-downloaded. Only genuinely missing or corrupt months are fetched.

**Data prep only.** This downloads and stages inputs; it solves nothing,
scores nothing and reads no model output. Under rule 22 as amended 2026-08-06
("what is held out is the SCORE, never the DATA"), staging source data for
every year is unrestricted — the holdout spend is *looking at the answer*, and
this script never does.

Usage::

    python scripts/data/fetch_nyiso_zonal_lmp.py                  # 2018-01..2026-06, both
    python scripts/data/fetch_nyiso_zonal_lmp.py --kind rt
    python scripts/data/fetch_nyiso_zonal_lmp.py --start 202301 --end 202512
    python scripts/data/fetch_nyiso_zonal_lmp.py --check          # report coverage, fetch nothing
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

#: Where both products stage, and where ``derive_actual_lmp`` reads them from.
NYISO_LMP_DIR = RAW_DATA_DIR / "lmp-data" / "NYISO"

#: The outer container the DA reader consumes (gitignored, assembled here).
DA_CONTAINER = NYISO_LMP_DIR / "NYISO_zonal_hourly.zip"

#: Public MIS archive roots, per ``data/raw/lmp-data/README.md``.
BASE_URL = "http://mis.nyiso.com/public/csv"

#: ``kind`` -> (URL path segment, filename stem).
_PRODUCTS = {
    "da": ("damlbmp", "damlbmp_zone_csv"),
    "rt": ("realtime", "realtime_zone_csv"),
}

#: The committed parquet's span. 2026 is H1 only — the block was built that
#: way and this script preserves the span so a re-derivation changes the
#: clock convention alone, never which hours exist.
DEFAULT_START = 201801
DEFAULT_END = 202606


def months(start: int, end: int) -> list[int]:
    """Inclusive ``YYYYMM`` list from ``start`` to ``end``.

    Both bounds are integers in ``YYYYMM`` form (e.g. ``201801``). Raises
    ``ValueError`` on a malformed bound or a reversed range.
    """
    for bound in (start, end):
        if bound % 100 < 1 or bound % 100 > 12:
            raise ValueError(f"not a YYYYMM month: {bound}")
    if end < start:
        raise ValueError(f"range is reversed: {start} > {end}")
    out: list[int] = []
    y, m = divmod(start, 100)
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return out


def filename(month: int, kind: str) -> str:
    """Local/remote basename for one ``YYYYMM`` month of ``kind`` (``da``/``rt``)."""
    _, stem = _PRODUCTS[kind]
    return f"{month}01{stem}.zip"


def is_valid_zip(path: Path) -> bool:
    """True when ``path`` opens as a zip holding at least one CSV member.

    Used both to skip already-staged months and to reject a truncated
    download, so a re-run repairs a partial fetch rather than trusting it.
    """
    if not path.exists() or path.stat().st_size == 0:
        return False
    try:
        with zipfile.ZipFile(path) as z:
            return any(n.lower().endswith(".csv") for n in z.namelist())
    except (zipfile.BadZipFile, OSError):
        return False


def fetch_month(month: int, kind: str, *, force: bool = False) -> str:
    """Download one month of one product into :data:`NYISO_LMP_DIR`.

    Returns a short status word: ``"skip"`` when a valid file is already
    staged (the committed-bytes case), ``"get"`` on a successful download, or
    ``"FAIL: ..."`` when the month could not be staged. Downloads land in a
    temp file and are validated as a zip before replacing the target, so an
    interrupted run never leaves a corrupt archive in place.
    """
    dest = NYISO_LMP_DIR / filename(month, kind)
    if not force and is_valid_zip(dest):
        return "skip"
    segment, _ = _PRODUCTS[kind]
    url = f"{BASE_URL}/{segment}/{filename(month, kind)}"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkstemp(dir=dest.parent, suffix=".part")[1])
    try:
        with urllib.request.urlopen(url, timeout=180) as resp, tmp.open("wb") as fh:
            shutil.copyfileobj(resp, fh)
        if not is_valid_zip(tmp):
            return f"FAIL: {url} did not return a readable zip"
        tmp.replace(dest)
        return "get"
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        return f"FAIL: {url}: {exc}"
    finally:
        tmp.unlink(missing_ok=True)


def build_da_container(month_list: list[int]) -> int:
    """Assemble :data:`DA_CONTAINER` from the staged monthly DA zips.

    Each monthly zip is stored (not re-compressed — it is already deflated)
    as a flat entry whose basename is what ``_nyiso_wide``'s DA branch filters
    on. Returns the number of months written. Rebuilt from scratch each call
    so a re-run cannot accumulate stale months.
    """
    staged = [m for m in month_list if is_valid_zip(NYISO_LMP_DIR / filename(m, "da"))]
    tmp = Path(tempfile.mkstemp(dir=NYISO_LMP_DIR, suffix=".part")[1])
    try:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as outer:
            for m in staged:
                name = filename(m, "da")
                outer.write(NYISO_LMP_DIR / name, arcname=name)
        tmp.replace(DA_CONTAINER)
    finally:
        tmp.unlink(missing_ok=True)
    return len(staged)


def coverage(month_list: list[int], kind: str) -> tuple[list[int], list[int]]:
    """Split ``month_list`` into (staged, missing) for one product."""
    staged = [m for m in month_list if is_valid_zip(NYISO_LMP_DIR / filename(m, kind))]
    return staged, [m for m in month_list if m not in set(staged)]


def main() -> int:
    """CLI entry point. Returns a process exit code."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--start", type=int, default=DEFAULT_START, help="YYYYMM (default 201801)"
    )
    ap.add_argument(
        "--end", type=int, default=DEFAULT_END, help="YYYYMM (default 202606)"
    )
    ap.add_argument("--kind", choices=["da", "rt", "both"], default="both")
    ap.add_argument(
        "--jobs", type=int, default=6, help="concurrent downloads (default 6)"
    )
    ap.add_argument("--force", action="store_true", help="re-download even if staged")
    ap.add_argument(
        "--check", action="store_true", help="report coverage only, fetch nothing"
    )
    args = ap.parse_args()

    month_list = months(args.start, args.end)
    kinds = ["da", "rt"] if args.kind == "both" else [args.kind]
    print(
        f"NYISO zonal LBMP staging: {len(month_list)} months {args.start}..{args.end}"
    )

    if args.check:
        for kind in kinds:
            staged, missing = coverage(month_list, kind)
            print(f"  {kind}: {len(staged)} staged, {len(missing)} missing")
            if missing:
                print(
                    f"       missing: {missing[:12]}{' ...' if len(missing) > 12 else ''}"
                )
        print(f"  DA container: {'present' if DA_CONTAINER.exists() else 'ABSENT'}")
        return 0

    failures: list[str] = []
    for kind in kinds:
        with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
            results = list(
                pool.map(
                    lambda m, k=kind: fetch_month(m, k, force=args.force), month_list
                )
            )
        got = sum(r == "get" for r in results)
        skipped = sum(r == "skip" for r in results)
        bad = [r for r in results if r.startswith("FAIL")]
        failures += bad
        print(
            f"  {kind}: {got} downloaded, {skipped} already staged, {len(bad)} failed"
        )
        for f in bad[:10]:
            print(f"    {f}")

    if "da" in kinds:
        n = build_da_container(month_list)
        size_mb = DA_CONTAINER.stat().st_size / 1e6
        print(f"  DA container: {n} months -> {DA_CONTAINER.name} ({size_mb:.1f} MB)")

    if failures:
        print(f"INCOMPLETE: {len(failures)} month(s) failed — coverage is partial")
        return 1
    print("OK: staging complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

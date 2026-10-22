"""Fetch SPP's RTBM effective-limit daily files (``RTBM-EFFLIMIT-YYYYMMDD.csv``).

SPP publishes the effective limits of its Real-Time Balancing Market
constraints as a product of its own, ``fsName=effective-limits`` on the
anonymous portal route (``scripts/data/fetch_spp_alt_portal.py`` documents the
route). It is NOT the ``rtbm-binding-constraints`` product: that archive gained
limit columns only on 2026-03-17 (``FINDING-spp-53`` §3.1), while this one
carries ``Source Limit`` / ``Realtime Effective Limit`` / ``Initial Effective
Limit`` from **2022-04-14** onward. Lane UC-SPP-CORRIDOR (2026-10-22) found it
in the portal menu (``/api/menu/``, slug ``effective-limits``) after lanes
SPP-12/13/14/53 had searched only the binding-constraint product.

Each daily file holds every ACTIVATED / BINDING / BREACHED constraint-interval
(~1-3 MB, ~10k rows). The day files are written byte-for-byte, unmodified, to
``data/raw/spp-effective-limits/by_day/<year>/`` (gitignored: ~2.6 GB for
2022-2025) and every file's sha256 and byte length is appended to the committed
``SHA256SUMS.txt`` so a later session can verify a re-pull. ``--reduce``
writes the committed form, ``rtbm_efflimit_bound_<year>.csv.gz`` (BINDING /
BREACHED lines verbatim), which ``scripts/data/curate_flowgate_limits_at_bind.py``
curates.

Rule 13 ``[R-MEASURED]``: SPP's own published operating limits; nothing here is
derived or fitted.

Usage:
    python scripts/data/fetch_spp_effective_limits.py --years 2022 2023 2024 2025
    python scripts/data/fetch_spp_effective_limits.py --years 2022 2023 2024 2025 --reduce
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "data"))
import fetch_spp_alt_portal as portal  # noqa: E402
from market_sim.config import paths  # noqa: E402

FS_NAME = "effective-limits"
RAW_DIR = paths.SPP_EFFECTIVE_LIMITS_DIR
# The constraint states the committed extraction keeps (SPP posts ACTIVATED /
# BINDING / BREACHED; ACTIVATED rows are ~90 % of each file and carry no bind).
BOUND_STATES = ("BINDING", "BREACHED")
# The portal occasionally leaves a connection open without answering; the
# shared helper's 900 s ceiling then stalls the whole pull. Per-call ceiling (s)
# and retry count for this product; a stalled call is simply retried.
CALL_TIMEOUT_S = 120
CALL_RETRIES = 6


def _curl(
    url: str, byte_range: str | None = None, retries: int = CALL_RETRIES
) -> bytes:
    """``fetch_spp_alt_portal._curl`` with this product's shorter per-call ceiling."""
    cmd = ["curl", "-sS", "-m", str(CALL_TIMEOUT_S), "--fail"]
    if byte_range is not None:
        cmd += ["-r", byte_range]
    cmd.append(url)
    last = b""
    for _ in range(retries):
        p = subprocess.run(cmd, capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout
        last = p.stderr
    raise RuntimeError(f"curl failed {url}: {last[:200]!r}")


portal._curl = _curl
listing, download = portal.listing, portal.download


def list_day_files(year: int) -> list[tuple[str, str, int]]:
    """``[(portal path, file name, byte size), ...]`` for one year's day files."""
    out = []
    for month in listing(FS_NAME, f"/{year}"):
        if month.get("type") != "folder":
            continue
        folder = f"/{year}/{month['name']}/By_Day"
        for item in listing(FS_NAME, folder):
            name = item["name"]
            if name.startswith("RTBM-EFFLIMIT-") and name.endswith(".csv"):
                out.append((f"{folder}/{name}", name, int(item["size"])))
    return sorted(out, key=lambda r: r[1])


def fetch_one(path: str, dest: Path, size: int) -> tuple[str, str, int]:
    """Download one day file unless an identical-size copy exists; return its digest."""
    if not (dest.exists() and dest.stat().st_size == size):
        body = download(FS_NAME, path)
        if len(body) != size:
            raise RuntimeError(f"{path}: got {len(body)} bytes, listing says {size}")
        dest.write_bytes(body)
    digest = hashlib.sha256(dest.read_bytes()).hexdigest()
    return dest.name, digest, size


def reduce_year(year: int) -> Path:
    """Write ``rtbm_efflimit_bound_<year>.csv.gz``: the BINDING/BREACHED lines, verbatim.

    One header (the first day file's), then every day file's data lines whose
    ``State`` field is BINDING or BREACHED, byte-for-byte and in file order.
    This committed form is what ``curate_flowgate_limits_at_bind.py`` reads.
    """
    files = sorted((RAW_DIR / "by_day" / str(year)).glob("RTBM-EFFLIMIT-*.csv"))
    if not files:
        raise SystemExit(f"no day files for {year}; fetch first")
    out = RAW_DIR / f"rtbm_efflimit_bound_{year}.csv.gz"
    header = None
    kept = 0
    # mtime=0 keeps the gzip byte-stable across re-runs.
    with open(out, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        for f in files:
            lines = f.read_bytes().splitlines(keepends=True)
            if not lines:
                continue
            if header is None:
                header = lines[0]
                gz.write(header)
                state_idx = next(csv.reader([header.decode()])).index("State")
            for line in lines[1:]:
                row = next(csv.reader([line.decode()]), [])
                if len(row) > state_idx and row[state_idx] in BOUND_STATES:
                    gz.write(line if line.endswith(b"\n") else line + b"\n")
                    kept += 1
    print(
        f"{year}: {len(files)} day files -> {kept} bound rows -> {out.name}", flush=True
    )
    return out


def main(argv: list[str] | None = None) -> int:
    """Pull every day file for the requested years and refresh the manifest."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", type=int, nargs="+", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument(
        "--reduce",
        action="store_true",
        help="only rebuild the committed bound-row extractions",
    )
    args = ap.parse_args(argv)
    if args.reduce:
        for year in args.years:
            reduce_year(year)
        return 0

    rows: dict[str, tuple[str, int]] = {}
    manifest = RAW_DIR / "SHA256SUMS.txt"
    if manifest.exists():
        for line in manifest.read_text().splitlines():
            digest, size, name = line.split()
            rows[name] = (digest, int(size))
    failed = []
    for year in args.years:
        out_dir = RAW_DIR / "by_day" / str(year)
        out_dir.mkdir(parents=True, exist_ok=True)
        files = list_day_files(year)
        print(f"{year}: {len(files)} day files", flush=True)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(fetch_one, p, out_dir / n, s): n for p, n, s in files}
            for fut in as_completed(futs):
                try:
                    name, digest, size = fut.result()
                    rows[name] = (digest, size)
                except Exception as exc:  # noqa: BLE001 - reported, never swallowed
                    failed.append(futs[fut])
                    print(f"FAIL {futs[fut]}: {exc}", flush=True)
    manifest.write_text("".join(f"{d} {s} {n}\n" for n, (d, s) in sorted(rows.items())))
    print(f"manifest: {len(rows)} files; failed: {failed}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())

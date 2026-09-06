"""Fetch SPP public market products over the ANONYMOUS portal HTTPS route.

Why this script exists
----------------------
Lanes SPP-12 and SPP-13 concluded that SPP's public products were unreachable
from this repo: SPP-12 measured ``portal.spp.org`` download calls returning HTTP
404 and read the 200-with-``[]`` listings as authorization, and SPP-13 then
established that SPP's *documented* programmatic route — anonymous FTP at
``ftp://pubftp.spp.org`` — is blocked by the session egress (port 21 is not
relayed). Row 5-9 of the SPP data manifest were left as an owner-side manual pull.

Lane SPP-14 re-probed the portal while sweeping alternative sources and found
that **both portal calls are anonymous-public and work today over plain HTTPS**.
The two corrections to the earlier reading, each measured 2026-09-06:

  * **download** — ``GET /file-browser-api/download/<fsName>?path=<file path>``
    returns the real CSV (HTTP 200, ``text/csv``) with **no token and no
    cookie**. The earlier 404s were path-shaped: the endpoint serves *files*,
    and a folder path (or a file path that does not exist for that product's
    archive layout) 404s exactly as a wrong path should.
  * **listing** — ``GET /file-browser-api/?fsName=<fs>&path=<p>&type=folder``
    returns the real JSON directory array when ``path`` is ``%2F`` (the root) or
    a real folder. The literal ``[]`` SPP-12 recorded reproduces only for
    ``path=`` (empty), which is the SPA's own first call.

The open-source ``gridstatus`` package's SPP client is the corroborating
witness: it reads these same URLs with a bare ``pandas.read_csv(url)`` and
carries no credential at all (``gridstatus/spp.py``, v0.36.0).

The server honours ``Range``, so an archived year that SPP has rolled into a
single ``/<year>/<year>.zip`` is read by range-fetching only the members needed
— the same zip64 central-directory technique
``scripts/data/build_spp_lmp_reference.py`` already implements for row 5, which
now runs unmodified against this route.

Scope
-----
Manifest rows 6 (hourly load by area), 7 (generation mix), 8 (binding
constraints) and 9 (operating-reserve MCPs). Row 5 (per-hub LMP) is served by
``build_spp_lmp_reference.py`` and is deliberately NOT duplicated here.

Every product is SPP's own published file, fetched byte-for-byte and written
unmodified — rule 13 ``[R-MEASURED]``: a measured market input, never an
outcome pinned to a residual, and nothing here is derived.

Usage:
    python scripts/data/fetch_spp_alt_portal.py --product hourly-load --years 2023 2024 2025
    python scripts/data/fetch_spp_alt_portal.py --product genmix --years 2023
    python scripts/data/fetch_spp_alt_portal.py --list rtbm-mcp --path /2025
"""

from __future__ import annotations

import argparse
import json
import struct
import subprocess
import sys
import urllib.parse
import zlib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402  (resolves the data root)

BASE = "https://portal.spp.org/file-browser-api/"
DOWNLOAD = BASE + "download/"

# fsName -> (destination directory name under data/raw, archive path template).
# The templates are SPP's own published layout, read from the live listings on
# 2026-09-06 and cross-checked against the file grammar the "SPP Markets Public
# Data Guide and Samples v35" states (tracked in data/raw/spp-planning/).
PRODUCTS = {
    "hourly-load": ("spp-hourly-load", "hourly-load"),
    "genmix": ("spp-genmix", "generation-mix-historical"),
    "rtbm-bc": ("spp-binding-constraints", "rtbm-binding-constraints"),
    "da-bc": ("spp-binding-constraints", "da-binding-constraints"),
    "da-mcp": ("spp-or-mcp", "da-mcp"),
    "rtbm-mcp": ("spp-or-mcp", "rtbm-mcp"),
}


def _curl(url: str, byte_range: str | None = None, retries: int = 4) -> bytes:
    """GET ``url`` (optionally a byte range) via curl, retrying on transient error."""
    cmd = ["curl", "-sS", "-m", "900", "--fail"]
    if byte_range is not None:
        cmd += ["-r", byte_range]
    cmd.append(url)
    last = b""
    for _ in range(retries):
        p = subprocess.run(cmd, capture_output=True)
        if p.returncode == 0 and p.stdout:
            return p.stdout
        last = p.stderr
    raise RuntimeError(f"curl failed ({byte_range}) {url}: {last[:200]!r}")


def listing(fs_name: str, path: str = "/") -> list[dict]:
    """Directory listing for ``path`` under ``fs_name``.

    ``path`` must be a real folder; the root is ``"/"`` (sent as ``%2F``). An
    EMPTY ``path`` returns ``[]`` from SPP even when the folder exists — that is
    the artifact lane SPP-12 read as an authorization wall.
    """
    url = (
        BASE
        + "?fsName="
        + urllib.parse.quote(fs_name, safe="")
        + "&path="
        + urllib.parse.quote(path, safe="")
        + "&type=folder"
    )
    return json.loads(_curl(url))


def download(fs_name: str, path: str, byte_range: str | None = None) -> bytes:
    """Fetch one published file (or a byte range of it) from the portal."""
    url = DOWNLOAD + fs_name + "?path=" + urllib.parse.quote(path, safe="")
    return _curl(url, byte_range)


def remote_size(fs_name: str, path: str) -> int:
    """Byte length of a remote file, from its parent folder's listing."""
    parent = path.rsplit("/", 1)[0] or "/"
    name = path.rsplit("/", 1)[-1]
    for item in listing(fs_name, parent):
        if item.get("name") == name:
            return int(item["size"])
    raise RuntimeError(f"{path} not found in listing of {parent}")


def central_directory(fs_name: str, path: str, size: int) -> list[tuple]:
    """``[(name, comp_size, local_header_offset, method), ...]`` for a remote zip.

    Reads the (zip64) central directory over range requests, so the archive body
    is never downloaded. Same construction as ``build_spp_lmp_reference.py``.
    """
    tail_n = min(size, 1 << 20)
    tail = download(fs_name, path, f"{size - tail_n}-{size - 1}")
    j = tail.rfind(b"PK\x06\x07")  # zip64 end-of-central-directory locator
    if j >= 0:
        z64_off = struct.unpack("<Q", tail[j + 8 : j + 16])[0]
        z = download(fs_name, path, f"{z64_off}-{z64_off + 55}")
        cd_size = struct.unpack("<Q", z[40:48])[0]
        cd_off = struct.unpack("<Q", z[48:56])[0]
    else:
        i = tail.rfind(b"PK\x05\x06")
        eocd = tail[i : i + 22]
        cd_size = struct.unpack("<I", eocd[12:16])[0]
        cd_off = struct.unpack("<I", eocd[16:20])[0]
    cd = download(fs_name, path, f"{cd_off}-{cd_off + cd_size - 1}")
    out: list[tuple] = []
    p = 0
    while p < len(cd) - 46 and cd[p : p + 4] == b"PK\x01\x02":
        method = struct.unpack("<H", cd[p + 10 : p + 12])[0]
        comp = struct.unpack("<I", cd[p + 20 : p + 24])[0]
        uncomp = struct.unpack("<I", cd[p + 24 : p + 28])[0]
        nlen = struct.unpack("<H", cd[p + 28 : p + 30])[0]
        elen = struct.unpack("<H", cd[p + 30 : p + 32])[0]
        clen = struct.unpack("<H", cd[p + 32 : p + 34])[0]
        lho = struct.unpack("<I", cd[p + 42 : p + 46])[0]
        name = cd[p + 46 : p + 46 + nlen].decode("latin1")
        extra = cd[p + 46 + nlen : p + 46 + nlen + elen]
        if 0xFFFFFFFF in (comp, uncomp, lho):  # zip64 extra overrides placeholders
            q = 0
            while q < len(extra) - 4:
                tag = struct.unpack("<H", extra[q : q + 2])[0]
                sz = struct.unpack("<H", extra[q + 2 : q + 4])[0]
                if tag == 0x0001:
                    vals = extra[q + 4 : q + 4 + sz]
                    k = 0
                    if uncomp == 0xFFFFFFFF:
                        k += 8
                    if comp == 0xFFFFFFFF:
                        comp = struct.unpack("<Q", vals[k : k + 8])[0]
                        k += 8
                    if lho == 0xFFFFFFFF:
                        lho = struct.unpack("<Q", vals[k : k + 8])[0]
                    break
                q += 4 + sz
        out.append((name, comp, lho, method))
        p += 46 + nlen + elen + clen
    return out


def read_member(fs_name: str, path: str, comp: int, lho: int, method: int) -> bytes:
    """Range-fetch and inflate one zip member from its central-directory record."""
    hdr = download(fs_name, path, f"{lho}-{lho + 29}")
    nlen = struct.unpack("<H", hdr[26:28])[0]
    elen = struct.unpack("<H", hdr[28:30])[0]
    start = lho + 30 + nlen + elen
    raw = download(fs_name, path, f"{start}-{start + comp - 1}")
    return raw if method == 0 else zlib.decompress(raw, -15)


def _year_targets(fs_name: str, year: int) -> list[str]:
    """Published paths that hold ``year`` for ``fs_name``, newest layout first.

    SPP rolls a year into ``/<year>/<year>.zip`` roughly two years on (guide
    p. 8: "Public Data files will be zipped (.zip) after 2 years"), so which of
    these exists depends on the year, not on the product.
    """
    if fs_name == "generation-mix-historical":
        return [f"/GenMix_{year}.csv", f"/SPP/GenMix_{year}_SPP.csv"]
    return [f"/{year}/{year}.zip"]


def fetch_year(product: str, year: int, out_dir: Path) -> Path | None:
    """Download ``year`` of ``product`` into ``out_dir``, unmodified.

    Returns the written path, or ``None`` when SPP publishes no such file (the
    year is served by a different layout — list it with ``--list``).
    """
    _, fs_name = PRODUCTS[product]
    for path in _year_targets(fs_name, year):
        try:
            blob = download(fs_name, path)
        except RuntimeError:
            continue
        # Several products publish their archive as a bare ``<year>.zip``, so the
        # destination name carries the product's fsName to keep them distinct in
        # one directory (``spp-or-mcp/`` holds both DA and RTBM MCP archives).
        leaf = path.rsplit("/", 1)[-1]
        dest = out_dir / (leaf if not leaf[0].isdigit() else f"{fs_name}-{leaf}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(blob)
        print(f"  wrote {dest} ({len(blob):,} bytes) from {fs_name}{path}", flush=True)
        return dest
    print(f"  {product} {year}: no published file at {_year_targets(fs_name, year)}")
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--product", choices=sorted(PRODUCTS))
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--list", metavar="FSNAME", help="print a portal listing and exit")
    ap.add_argument("--path", default="/", help="folder for --list (default root)")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    if args.list:
        for item in listing(args.list, args.path):
            print(f"  {item['type']:6} {str(item.get('size')):>12}  {item['name']}")
        return

    if not args.product:
        ap.error("--product is required unless --list is given")
    dest_name, _ = PRODUCTS[args.product]
    out_dir = args.out_dir or (paths.RAW_DIR / dest_name)
    for year in args.years:
        fetch_year(args.product, year, out_dir)


if __name__ == "__main__":
    main()

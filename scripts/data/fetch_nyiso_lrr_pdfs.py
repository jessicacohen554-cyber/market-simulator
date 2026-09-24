"""Fetch the dated NYISO Locational Reserve Requirements PDFs (+ 2020 SOM).

Downloads the primary-source documents behind the ``nyiso-reserve-requirements``
transcription (see ``data/raw/NYISO-AS/requirements/README.md``) and the 2020
State-of-the-Market report behind the 2018 rows of
``nyiso-som-hub-fuel-annual``:

* ``lrr_nyiso_v1.1_20160817.pdf`` / ``lrr_nyiso_v1.2_20190624.pdf`` — the
  pre-2020 versions from nyiso.com's own document-version history
  (``?version=1.1`` / ``?version=1.2`` of the same Liferay document; a
  version number is immutable, md5-verified). Intaken 2026-09-24 for the
  2019-2021 backcast years. The history also serves v1.3 (byte-identical to
  ``lrr_wayback_20201029.pdf``), v1.4 (= ``lrr_wayback_20211204.pdf``) and
  v2.0/v2.1 (= ``lrr_retrieved_20260710.pdf``), which corroborates the
  transcription's version chain.
* ``lrr_wayback_20201029.pdf`` / ``lrr_wayback_20211204.pdf`` — immutable
  Wayback Machine snapshots (md5-verified; a mismatch is an error).
* ``lrr_retrieved_20260710.pdf`` — the live nyiso.com posting as retrieved
  2026-07-10 (md5-checked with a WARNING only: the live URL is a living
  document, and a changed hash means NYISO has posted a NEWER version — add a
  new dated file + transcription rows rather than overwriting history).
* ``NYISO-2020-SOM-Report-final-5-18-2021.pdf`` — nyiso.com document library
  (md5-verified).

The PDFs are binary raw sources committed via the intake workflow
(``.github/workflows/fetch-nyiso-reserve-interface-intake.yml``) because the
remote-session proxy only permits text pushes.

Run: ``python scripts/data/fetch_nyiso_lrr_pdfs.py``
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from market_sim.config.paths import NYISO_AS_DIR, NYISO_DIR  # noqa: E402

LRR_DIR = NYISO_AS_DIR / "requirements" / "locational-reserve-requirements"
NYISO_DIR = NYISO_DIR

_WAYBACK = "https://web.archive.org/web"
_NYISO_DOC = "https://www.nyiso.com/documents"

# (destination, URL, md5, strict) — md5s recorded at the 2026-07-10 intake.
DOCS: tuple[tuple[Path, str, str, bool], ...] = (
    (
        LRR_DIR / "lrr_nyiso_v1.1_20160817.pdf",
        f"{_NYISO_DOC}/20142/3694424/Locational-Reserves-Requirements.pdf?version=1.1",
        "6af6bb9ba632702e9c6b939d637b8c00",
        True,
    ),
    (
        LRR_DIR / "lrr_nyiso_v1.2_20190624.pdf",
        f"{_NYISO_DOC}/20142/3694424/Locational-Reserves-Requirements.pdf?version=1.2",
        "53485df78303b94cae4285fe44e112f2",
        True,
    ),
    (
        LRR_DIR / "lrr_wayback_20201029.pdf",
        f"{_WAYBACK}/20201029110250if_/https://www.nyiso.com/documents/20142/"
        "3694424/nyiso_locational_reserve_reqmts.pdf/"
        "ab6e7fb9-0d5b-a565-bf3e-a3af59004672",
        "5d57fe6d02351b3153573543a4ae2634",
        True,
    ),
    (
        LRR_DIR / "lrr_wayback_20211204.pdf",
        f"{_WAYBACK}/20211204105606if_/https://www.nyiso.com/documents/20142/"
        "3694424/Locational-Reserves-Requirements.pdf/"
        "ab6e7fb9-0d5b-a565-bf3e-a3af59004672",
        "0436d93d634bb215738ba6c12d1fd2d9",
        True,
    ),
    (
        LRR_DIR / "lrr_retrieved_20260710.pdf",
        f"{_NYISO_DOC}/20142/3694424/Locational-Reserves-Requirements.pdf",
        "7c1d0e2a290e6b268d81855f07af2814",
        False,  # living URL — warn, don't fail (see module docstring)
    ),
    (
        NYISO_DIR / "NYISO-2020-SOM-Report-final-5-18-2021.pdf",
        f"{_NYISO_DOC}/20142/2223763/NYISO-2020-SOM-Report-final-5-18-2021.pdf/"
        "c540fdc7-c45b-f93b-f165-12530be925c7",
        "df4e9c1c65fdf07c20315011e9e481ed",
        True,
    ),
)


def fetch(force: bool = False) -> int:
    """Download every document; verify md5s. Returns a process exit code."""
    rc = 0
    for dest, url, md5, strict in DOCS:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file() and not force:
            print(f"exists   {dest.relative_to(REPO_ROOT)}")
        else:
            req = urllib.request.Request(
                url, headers={"User-Agent": "market-sim-intake"}
            )
            with urllib.request.urlopen(req, timeout=180) as resp:
                dest.write_bytes(resp.read())
            print(f"fetched  {dest.relative_to(REPO_ROOT)}")
        got = hashlib.md5(dest.read_bytes()).hexdigest()
        if got == md5:
            continue
        if strict:
            print(
                f"ERROR: md5 mismatch for {dest.name}: {got} != {md5}", file=sys.stderr
            )
            rc = 1
        else:
            print(
                f"WARNING: {dest.name} md5 {got} != recorded {md5} — the live "
                "posting has changed; intake it as a NEW dated version, do not "
                "overwrite the transcription history",
                file=sys.stderr,
            )
    return rc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--force", action="store_true", help="re-download even if present"
    )
    args = parser.parse_args(argv)
    return fetch(force=args.force)


if __name__ == "__main__":
    raise SystemExit(main())

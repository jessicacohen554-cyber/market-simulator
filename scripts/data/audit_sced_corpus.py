#!/usr/bin/env python3
"""Audit the ERCOT NP3-965 SCED Gen Resource corpus, and write its restore manifest.

The acceptance instrument for a re-fetch RESTORE of the untracked window of
``data/raw/ercot/SCED/`` (publication months 2024-04 .. 2026-03, deliveries
2024-02-01 .. 2025-12-31), built by ercot-248 (2026-08-31) after measuring that
the corpus's ``SHA256SUMS.txt`` **cannot** serve that role: parquet bytes are
writer-version specific, so a re-fetch reproduces the corpus's CONTENT but not
its bytes (tracked shards were written by ``parquet-cpp-arrow 24.0.0``; a
25.0.1 writer gives a different sha256 for a byte-equivalent projection).
``SHA256SUMS.txt`` remains the identity record of the ORIGINAL bytes and is not
touched here.

Row count, column count and delivery day ARE writer-independent, so they are
what a restore is judged against — that is the manifest this script writes
(``RESTORE-ROWCOUNTS.txt``), and ``--check`` re-verifies a corpus against it.

The five structural checks (``--audit``, the default), each one a real footgun
the corpus has hit before:

1. **Duplicate delivery days.** A part is written per delivery day; a second
   part covering a day silently DOUBLE-WEIGHTS it in every consumer that
   streams the corpus (``derive_ercot_sced_offer_wall._load_year`` concatenates
   every selected shard). This is what re-fetching from the 2024-03-24
   retention floor rather than 2024-04-01 causes — pubs 2024-03-24..31 are
   already on disk as the tracked ``2024-03.part0009-0016``.
2. **Coverage gaps**, reported as contiguous runs and never inferred. The one
   expected gap is deliveries **2024-01-10..23** (publications 2024-03-10..23),
   which aged out of the free MIS list before any fetch reached them; the
   credentialed data.ercot.com archive is owner-declined
   (``docs/handoffs/ercot-as-coopt-plan-2026-07.md`` §WS-E).
3. **Locked-test leakage** (CLAUDE.md rule 22): no delivery day may exceed
   ``--max-delivery-date`` (default 2025-12-31). H1-2026 is the locked-test
   tier and the holdout freeze is scoped to it; the fetchers refuse those days
   and this re-checks the result rather than trusting the refusal.
4. **RTC+B quarantine placement**, decided by CONTENT and never by filename.
   ERCOT's Real-Time Co-optimization go-live changed the member format at
   publications 2026-02-03 onward (deliveries 2025-12-05..31): ``HASL`` — a
   required read column of every corpus consumer — is REMOVED. Those parts live
   in ``rtcb-format-2026/``, invisible to the consumers' non-recursive globs and
   readable only through ``scripts/lib/sced_rtcb_adapter``. A part missing
   ``HASL`` at the top level CRASHES the derives; a pre-RTC+B part inside the
   quarantine is silently dropped from them. Both directions are checked.
5. **Multi-day parts.** Early-2023 shards pack 2 delivery days per part by
   design; every part fetched since is one day. A restored part carrying more
   than one day means a supplemental bundle member was written unfiltered.

Usage::

    python scripts/data/audit_sced_corpus.py                 # audit only
    python scripts/data/audit_sced_corpus.py --check         # audit + verify
                                                             #   RESTORE-ROWCOUNTS.txt
    python scripts/data/audit_sced_corpus.py --write-manifest # (re)write it

This is a read-only instrument over ``data/raw/`` except for
``--write-manifest``, which writes the tracked manifest beside the payloads;
it never moves, edits or deletes a payload (the repo data contract: the raw
source root is immutable).
"""

from __future__ import annotations

import argparse
import collections
import sys
from datetime import date, timedelta
from pathlib import Path

import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import ERCOT_MIS_DIR  # noqa: E402

#: The corpus root and its RTC+B format-break quarantine.
CORPUS_DIR = ERCOT_MIS_DIR / "SCED"
RTCB_DIRNAME = "rtcb-format-2026"

#: The publication-month shard glob, matching the consumers' own
#: (``derive_ercot_sced_offer_wall._sced_source_files``) — NON-recursive, so the
#: quarantine is scanned only when asked for explicitly.
SHARD_GLOB = "[0-9][0-9][0-9][0-9]-[0-1][0-9].part*.parquet"

#: The restore window: publication months whose payloads are gitignored at tip
#: (BLOAT-B-5 item A2, owner-signed 2026-08-15). Inclusive, ``YYYY-MM``.
RESTORE_PUB_LO, RESTORE_PUB_HI = "2024-04", "2026-03"

#: Delivery-day span the corpus is expected to cover end to end.
COVERAGE_LO, COVERAGE_HI = date(2022, 12, 31), date(2025, 12, 31)

#: The one accepted coverage gap — permanently unreachable on the free MIS
#: path (publications 2024-03-10..23 aged out before any fetch reached them).
KNOWN_GAP = (date(2024, 1, 10), date(2024, 1, 23))

#: Column whose absence identifies an RTC+B-format part (see check 4).
RTCB_MARKER_COL = "HASL"

MANIFEST_NAME = "RESTORE-ROWCOUNTS.txt"


def _iso(stamp: str) -> str:
    """``MM/DD/YYYY`` (the NP3-965 publication format) -> ``YYYY-MM-DD``."""
    month, day, year = stamp.split("/")
    return f"{year}-{month}-{day}"


def scan_part(path: Path) -> dict:
    """Read one shard's identity: delivery day(s), rows, columns, HASL presence.

    The delivery day is read from the file's own ``SCED Time Stamp`` values,
    never from the filename — the filename carries the PUBLICATION month, which
    leads the delivery by ~60 days.
    """
    pf = pq.ParquetFile(path)
    stamps = pq.read_table(path, columns=["SCED Time Stamp"]).column(0).to_pylist()
    days = sorted({_iso(s[:10]) for s in stamps if s})
    return {
        "file": path.name,
        "days": days,
        "rows": pf.metadata.num_rows,
        "cols": pf.metadata.num_columns,
        "has_hasl": RTCB_MARKER_COL in set(pf.schema_arrow.names),
        "bytes": path.stat().st_size,
    }


def scan_corpus(corpus_dir: Path) -> tuple[list[dict], list[dict]]:
    """Scan the top level and the RTC+B quarantine. Returns ``(top, rtcb)``."""
    top = [scan_part(p) for p in sorted(corpus_dir.glob(SHARD_GLOB))]
    quarantine = corpus_dir / RTCB_DIRNAME
    rtcb = (
        [scan_part(p) for p in sorted(quarantine.glob(SHARD_GLOB))]
        if quarantine.is_dir()
        else []
    )
    return top, rtcb


def _contiguous_runs(days: list[str]) -> list[tuple[str, str]]:
    """Collapse a sorted ISO-day list into ``(start, end)`` contiguous runs."""
    if not days:
        return []
    runs, start, prev = [], days[0], days[0]
    for day in days[1:]:
        if date.fromisoformat(day) - date.fromisoformat(prev) == timedelta(days=1):
            prev = day
            continue
        runs.append((start, prev))
        start = prev = day
    runs.append((start, prev))
    return runs


def audit(top: list[dict], rtcb: list[dict], max_delivery: date) -> list[str]:
    """Run the five structural checks. Returns the list of failure lines."""
    failures: list[str] = []
    every = top + rtcb
    print(f"top-level parts: {len(top)}   rtcb-quarantine parts: {len(rtcb)}")

    # 1. duplicate delivery days
    seen: collections.Counter[str] = collections.Counter()
    for part in every:
        seen.update(part["days"])
    dupes = sorted(d for d, n in seen.items() if n > 1)
    print(f"distinct delivery days: {len(seen)};  duplicates: {len(dupes)}")
    if dupes:
        failures.append(f"DUPLICATE delivery days ({len(dupes)}): {dupes[:20]}")

    # 2. coverage gaps
    span = {
        (COVERAGE_LO + timedelta(days=i)).isoformat()
        for i in range((COVERAGE_HI - COVERAGE_LO).days + 1)
    }
    missing = sorted(span - set(seen))
    runs = _contiguous_runs(missing)
    print(f"missing delivery days in {COVERAGE_LO}..{COVERAGE_HI}: {len(missing)}")
    known = (KNOWN_GAP[0].isoformat(), KNOWN_GAP[1].isoformat())
    for lo, hi in runs:
        n = (date.fromisoformat(hi) - date.fromisoformat(lo)).days + 1
        tag = "  (KNOWN — free-path retention)" if (lo, hi) == known else ""
        print(f"   MISSING {lo} .. {hi}  ({n} day{'s' if n > 1 else ''}){tag}")
    unexpected = [r for r in runs if r != known]
    if unexpected:
        failures.append(f"UNEXPECTED coverage gap(s): {unexpected}")

    # 3. locked-test leakage (rule 22)
    leaked = sorted(d for d in seen if date.fromisoformat(d) > max_delivery)
    print(f"deliveries beyond {max_delivery} (rule 22): {len(leaked)}")
    if leaked:
        failures.append(f"RULE-22 LEAK — deliveries past {max_delivery}: {leaked[:10]}")

    # 4. RTC+B quarantine placement, by content
    stray = [p["file"] for p in top if not p["has_hasl"]]
    misfiled = [p["file"] for p in rtcb if p["has_hasl"]]
    print(
        f"top-level parts missing {RTCB_MARKER_COL} (must be quarantined): "
        f"{len(stray)};  quarantined parts that have it: {len(misfiled)}"
    )
    if stray:
        failures.append(
            f"RTC+B parts at the top level (crash every consumer): {stray[:30]}"
        )
    if misfiled:
        failures.append(f"pre-RTC+B parts wrongly quarantined: {misfiled[:30]}")

    # 5. multi-day parts outside the early-2023 two-days-per-part months
    multi = [
        (p["file"], p["days"])
        for p in every
        if len(p["days"]) != 1 and p["file"][:7] >= RESTORE_PUB_LO
    ]
    legacy_multi = sum(1 for p in every if len(p["days"]) != 1) - len(multi)
    print(
        f"parts carrying != 1 delivery day: {len(multi)} in the restore window "
        f"(+{legacy_multi} in the early-2023 2-days-per-part months, by design)"
    )
    if multi:
        failures.append(f"restored parts with != 1 delivery day: {multi[:10]}")

    total = sum(p["bytes"] for p in every)
    cols = collections.Counter(p["cols"] for p in every)
    print(f"corpus bytes on disk: {total / 2**20:,.1f} MiB over {len(every)} parts")
    print(f"column-count census: {dict(sorted(cols.items()))}")
    return failures


def manifest_rows(top: list[dict], rtcb: list[dict]) -> list[tuple[str, str, int, int]]:
    """The restore-window rows of the manifest, sorted by path."""
    rows = []
    for prefix, parts in (("", top), (f"{RTCB_DIRNAME}/", rtcb)):
        for part in parts:
            if not (RESTORE_PUB_LO <= part["file"][:7] <= RESTORE_PUB_HI):
                continue
            rows.append(
                (
                    prefix + part["file"],
                    ",".join(part["days"]),
                    part["rows"],
                    part["cols"],
                )
            )
    return sorted(rows)


def read_manifest(path: Path) -> list[tuple[str, str, int, int]]:
    """Parse a ``RESTORE-ROWCOUNTS.txt`` into comparable rows."""
    rows = []
    for line in path.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        name, days, nrows, ncols = line.split("\t")
        rows.append((name, days, int(nrows), int(ncols)))
    return sorted(rows)


def check_manifest(observed: list, path: Path) -> list[str]:
    """Compare a scanned corpus against the committed manifest."""
    if not path.exists():
        return [f"no manifest at {path} to check against"]
    expected = read_manifest(path)
    exp_by, obs_by = (
        dict((r[0], r) for r in expected),
        dict((r[0], r) for r in observed),
    )
    failures = []
    for name in sorted(set(exp_by) - set(obs_by)):
        failures.append(f"MISSING part {name} (manifest expects it)")
    for name in sorted(set(obs_by) - set(exp_by)):
        failures.append(f"EXTRA part {name} (not in manifest)")
    for name in sorted(set(exp_by) & set(obs_by)):
        if exp_by[name] != obs_by[name]:
            failures.append(
                f"MISMATCH {name}: manifest {exp_by[name][1:]} "
                f"!= on disk {obs_by[name][1:]}"
            )
    print(
        f"manifest check: {len(expected)} expected / {len(observed)} observed "
        f"parts; {len(failures)} discrepanc{'y' if len(failures) == 1 else 'ies'}"
    )
    return failures


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus-dir", default=str(CORPUS_DIR))
    ap.add_argument(
        "--max-delivery-date",
        default="2025-12-31",
        help="no delivery day may exceed this (CLAUDE.md rule 22 leak check)",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help=f"also verify the corpus against the committed {MANIFEST_NAME}",
    )
    ap.add_argument(
        "--write-manifest",
        action="store_true",
        help=f"(re)write {MANIFEST_NAME} from the scanned corpus",
    )
    args = ap.parse_args()

    corpus = Path(args.corpus_dir)
    max_delivery = date.fromisoformat(args.max_delivery_date)
    top, rtcb = scan_corpus(corpus)
    failures = audit(top, rtcb, max_delivery)

    rows = manifest_rows(top, rtcb)
    manifest_path = corpus / MANIFEST_NAME
    if args.check:
        failures += check_manifest(rows, manifest_path)
    if args.write_manifest:
        header = (
            manifest_path.read_text().split("# columns:")[0]
            if (manifest_path.exists())
            else ""
        )
        if not header:
            raise SystemExit(
                f"{manifest_path} has no header to preserve — write the "
                "provenance header by hand before regenerating the rows"
            )
        body = "# columns: part<TAB>delivery_day(s)<TAB>rows<TAB>cols\n"
        body += "".join(f"{a}\t{b}\t{c}\t{d}\n" for a, b, c, d in rows)
        manifest_path.write_text(header + body)
        print(f"wrote {manifest_path} ({len(rows)} parts)")

    if failures:
        print(f"\nFAILED — {len(failures)} problem(s):")
        for line in failures:
            print(f"  {line}")
        raise SystemExit(1)
    print("\nOK — every structural check passed.")


if __name__ == "__main__":
    main()

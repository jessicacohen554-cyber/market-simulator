#!/usr/bin/env python3
"""Copy a re-derived price reference into committed bench parts, surgically.

When ``data/raw/_validation-source/actual_lmp.json`` changes for an ISO (a new
labelled benchmark, a zone-resolved ``*_lw`` basis), the per-(ISO, year) bench
part ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` still carries the old
``bench.avgLMP``. Regenerating the whole part re-reads every other benchmark
input and can move numbers that have nothing to do with price (the miso-266 /
nyiso-148 hazard). This tool instead replaces ``bench.avgLMP`` ONLY — the
miso-292 method used by miso-294 and NYISO-NEXT-22:

* the replacement is exactly what the builder would emit
  (``render_calibration_html._actual_avg_lmp``: the same keys, the same order);
* a part that had no ``avgLMP`` gains it at the builder's key position
  (after ``ctOnly``, before ``storage``);
* the original bytes are asserted to round-trip under the writer's settings
  (``json.dumps``, gzip level 9, ``mtime`` 0) before anything is written, and the
  decoded part minus ``bench.avgLMP`` is asserted equal to the original;
* ``meta`` (``builderFingerprint`` included) is never touched.

Usage::

    python scripts/data/patch_bench_avglmp.py --iso PJM --years 2019 ... 2025
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (str(REPO), str(REPO / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import render_calibration_html as rch  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402

#: The builder's ``bench`` key order (``render_calibration_html``); ``avgLMP``
#: sits after ``ctOnly``.
_AFTER = "ctOnly"


def _encode(obj: dict) -> bytes:
    """The bench-part writer's exact byte encoding (``write_bench_part``)."""
    return gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)


def patch_part(path: Path, avg: dict | None) -> bool:
    """Replace ``bench.avgLMP`` in one part with ``avg``; return True if changed."""
    raw = path.read_bytes()
    part = json.loads(gzip.decompress(raw))
    if _encode(part) != raw:
        raise SystemExit(f"{path}: original bytes do not round-trip — refusing")
    bench = part["bench"]
    if bench.get("avgLMP") == avg:
        return False
    new_bench: dict = {}
    for k, v in bench.items():
        if k == "avgLMP":
            if avg is not None:
                new_bench[k] = avg  # keep the key's existing position
            continue
        new_bench[k] = v
        if k == _AFTER and avg is not None and "avgLMP" not in bench:
            new_bench["avgLMP"] = avg  # the builder's position for a new key
    if avg is not None and "avgLMP" not in new_bench:
        new_bench["avgLMP"] = avg
    before = {k: v for k, v in bench.items() if k != "avgLMP"}
    after = {k: v for k, v in new_bench.items() if k != "avgLMP"}
    if before != after:
        raise SystemExit(f"{path}: a non-avgLMP key would move — refusing")
    part["bench"] = new_bench
    path.write_bytes(_encode(part))
    return True


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--iso", required=True)
    ap.add_argument("--years", nargs="+", type=int, required=True)
    a = ap.parse_args()
    for y in a.years:
        path = ba.BENCH / a.iso / f"{y}.json.gz"
        if not path.exists():
            print(f"  {a.iso} {y}: no bench part — skipped")
            continue
        changed = patch_part(path, rch._actual_avg_lmp(a.iso, y))
        print(f"  {a.iso} {y}: {'patched' if changed else 'unchanged'}")


if __name__ == "__main__":
    main()

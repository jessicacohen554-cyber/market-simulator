"""Retrofit committed bench parts with the v2.4 load-weighted price fields.

The rubric v2.4 C3a/C3b basis fix (see ``RUBRIC_VERSION`` in
``scripts/calibration_verdict.py`` and
``docs/rubric-v24-price-basis-memo-2026-07.md``) adds like-for-like
load-weighted actual price fields (``rt_lw``/``da_lw`` + monthly vectors) to
the derived reference ``data/raw/_validation-source/actual_lmp.json``
(``derive_actual_lmp.py --lw-retrofit``). The committed per-(ISO, year) bench
parts (``frontend/data/backcast/bench/<ISO>/<year>.json.gz``) embed a copy of
those fields in their ``bench.avgLMP`` block — but most registered bundles'
parquets are not present on any one checkout, so the parts cannot simply be
re-rendered. This script therefore retrofits the committed parts SURGICALLY
(the ``retrofit_co2_payloads.py`` precedent): decode each part, inject the lw
fields from the derived reference in the same key order
``render_calibration_html._actual_avg_lmp`` emits (legacy fields first, lw
fields appended), re-encode with the writer's exact deterministic settings
(``json.dumps`` default separators, gzip ``compresslevel=9, mtime=0``). Parts
whose ISO-year has no lw fields, or that carry no ``avgLMP`` block, are left
byte-identical.

Usage:
    python scripts/retrofit_lw_price_bench.py [--dry-run]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
from market_sim.config import paths  # noqa: E402

BENCH_DIR = REPO / "frontend" / "data" / "backcast" / "bench"
REF = paths.CALIBRATION_DIR / "actual_lmp.json"

# Serialization order of the avgLMP block — MUST match
# render_calibration_html._actual_avg_lmp so a future full re-render of an
# unchanged part is byte-identical to the retrofit output.
_KEY_ORDER = (
    "da",
    "rt",
    "da_mon",
    "rt_mon",
    "da_lw",
    "rt_lw",
    "da_lw_mon",
    "rt_lw_mon",
)


def retrofit(dry_run: bool = False) -> int:
    """Inject lw fields into every coverable bench part; return change count."""
    ref = json.loads(REF.read_text())
    changed = 0
    for part_path in sorted(BENCH_DIR.glob("*/*.json.gz")):
        iso = part_path.parent.name
        year = part_path.stem.split(".")[0]
        rec = (ref.get(iso) or {}).get(year) or {}
        lw = {k: rec[k] for k in _KEY_ORDER[4:] if k in rec}
        if not lw:
            continue
        raw = gzip.decompress(part_path.read_bytes())
        part = json.loads(raw)
        avg = (part.get("bench") or {}).get("avgLMP")
        if avg is None:
            continue
        rebuilt = {k: avg[k] for k in _KEY_ORDER[:4] if k in avg}
        # preserve any non-price keys a future writer may add, then append lw
        rebuilt.update({k: v for k, v in avg.items() if k not in _KEY_ORDER})
        rebuilt.update(lw)
        if rebuilt == avg:
            continue
        part["bench"]["avgLMP"] = rebuilt
        out = gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0)
        if not dry_run:
            part_path.write_bytes(out)
        changed += 1
        print(f"  {iso}/{year}: +{sorted(lw)}")
    print(f"{'DRY-RUN — ' if dry_run else ''}{changed} bench part(s) retrofitted")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    retrofit(dry_run=args.dry_run)


if __name__ == "__main__":
    main()

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

``--full-avglmp`` refreshes the ENTIRE ``avgLMP`` block (legacy + lw fields)
from the derived reference instead of only appending the lw fields — the
surgical equivalent of a full re-render's ``bench[year]["avgLMP"]``
replacement (``render_calibration_html.build_payload``). Use it when the
LEGACY actual fields themselves change, i.e. when new raw price history
lands for an already-benchmarked ISO-year (the 2026-07 CAISO Jan-2023 OASIS
GRP backfill). Scope it with ``--isos``/``--years`` so untouched ISO-years
stay byte-identical.

Usage:
    python scripts/retrofit_lw_price_bench.py [--dry-run]
    python scripts/retrofit_lw_price_bench.py --full-avglmp --isos CAISO --years 2023
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


def retrofit(
    dry_run: bool = False,
    full_avglmp: bool = False,
    isos: list[str] | None = None,
    years: list[int] | None = None,
) -> int:
    """Inject lw fields (or, with ``full_avglmp``, the whole refreshed
    ``avgLMP`` block) into every coverable bench part; return change count."""
    ref = json.loads(REF.read_text())
    changed = 0
    for part_path in sorted(BENCH_DIR.glob("*/*.json.gz")):
        iso = part_path.parent.name
        year = part_path.stem.split(".")[0]
        if isos is not None and iso not in isos:
            continue
        if years is not None and int(year) not in years:
            continue
        rec = (ref.get(iso) or {}).get(year) or {}
        new_fields = {
            k: rec[k]
            for k in (_KEY_ORDER if full_avglmp else _KEY_ORDER[4:])
            if k in rec
        }
        if not new_fields:
            continue
        raw = gzip.decompress(part_path.read_bytes())
        part = json.loads(raw)
        avg = (part.get("bench") or {}).get("avgLMP")
        if avg is None:
            continue
        if full_avglmp:
            # Rebuild the whole block in writer key order from the reference;
            # legacy keys the reference lacks (e.g. rt for a DA-only year)
            # carry over so a partial reference never deletes a benchmark.
            rebuilt = {
                k: new_fields.get(k, avg.get(k))
                for k in _KEY_ORDER
                if k in new_fields or k in avg
            }
            rebuilt.update({k: v for k, v in avg.items() if k not in _KEY_ORDER})
        else:
            rebuilt = {k: avg[k] for k in _KEY_ORDER[:4] if k in avg}
            # preserve any non-price keys a future writer may add, then append lw
            rebuilt.update({k: v for k, v in avg.items() if k not in _KEY_ORDER})
            rebuilt.update(new_fields)
        if rebuilt == avg:
            continue
        part["bench"]["avgLMP"] = rebuilt
        out = gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0)
        if not dry_run:
            part_path.write_bytes(out)
        changed += 1
        print(
            f"  {iso}/{year}: {'avgLMP refreshed' if full_avglmp else '+' + str(sorted(new_fields))}"
        )
    print(f"{'DRY-RUN — ' if dry_run else ''}{changed} bench part(s) retrofitted")
    return changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--full-avglmp",
        action="store_true",
        help="refresh the entire avgLMP block (legacy + lw) from the derived "
        "reference, not just the lw fields",
    )
    ap.add_argument("--isos", nargs="+", default=None, help="restrict to these ISOs")
    ap.add_argument(
        "--years", nargs="+", type=int, default=None, help="restrict to these years"
    )
    args = ap.parse_args()
    retrofit(
        dry_run=args.dry_run,
        full_avglmp=args.full_avglmp,
        isos=args.isos,
        years=args.years,
    )


if __name__ == "__main__":
    main()

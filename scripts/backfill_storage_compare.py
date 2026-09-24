"""Add the report-only ``storageCmp`` block to already-registered run payloads.

Zero-LP backfill for the Run Explorer storage panel. For each ``--run-id`` it
reads the registry sidecar's bundle, builds one ``storageCmp`` block per year
from the bundle's COMMITTED ``hourly/storage_<year>.parquet`` sidecar and the
measured actuals (``scripts/lib/storage_compare.py``), inserts it into the
existing ``frontend/data/backcast/runs/<id>.js`` payload, and re-encodes it
with the frozen codec (``scripts/lib/backcast_artifacts.encode_run_js``).

Nothing else in the payload is touched — no scored field, no class series, no
price — so every criterion and determination re-scores byte-identically. The scalar
stats it prints are the record the RESULT doc carries.

Future registrations get the block from ``render_calibration_html.build_payload``
directly; this script exists for runs registered before the field.

Usage::

    python scripts/backfill_storage_compare.py --run-id <id> [<id> ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from scripts.lib.backcast_artifacts import (  # noqa: E402
    RUNS,
    bundle_dir_for,
    decode_run_js,
    encode_run_js,
    load_sidecar,
)
from scripts.lib.storage_compare import build_storage_compare, summary_row  # noqa: E402


def backfill(run_id: str) -> dict[int, dict]:
    """Insert ``storageCmp`` into one run's payload; return the per-year stats."""
    rec = load_sidecar(run_id)
    iso = str(rec["iso"])
    bdir = bundle_dir_for(rec)
    if bdir is None or not bdir.is_dir():
        raise SystemExit(f"{run_id}: bundle {rec.get('bundle')!r} not on disk")
    js = RUNS / f"{run_id}.js"
    model = decode_run_js(js.read_text())
    stats: dict[int, dict] = {}
    for ykey, ydata in model["years"].items():
        block = build_storage_compare(bdir, iso, int(ykey))
        if block is None:
            ydata.pop("storageCmp", None)
            continue
        ydata["storageCmp"] = block
        stats[int(ykey)] = summary_row(block)
    js.write_text(encode_run_js(run_id, model))
    return stats


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--run-id", nargs="+", required=True)
    args = ap.parse_args(argv)
    for rid in args.run_id:
        stats = backfill(rid)
        for y, s in sorted(stats.items()):
            print(
                f"{rid} {y}: r_net={s['rNet']} r_diur={s['rDiur']} r_soc={s['rSoc']} "
                f"lag={s['bestLag']} dis {s['mDisTwh']}/{s['aDisTwh']} "
                f"chg {s['mChgTwh']}/{s['aChgTwh']} TWh (model/actual)"
            )
        if not stats:
            print(f"{rid}: no comparable year (no actuals for this ISO-span)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

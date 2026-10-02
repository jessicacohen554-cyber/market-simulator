"""R-CAISO-34 (link 16) — add the storage panel's ``socBounds`` block to a committed payload.

ZERO LP, display only. A full re-render (``scripts/render_backcast.py``) needs
the bundle's gitignored ``system.parquet``, which a committed keeper bundle
does not carry, so this decodes the registered ``runs/<id>.js`` payload, adds
``storageCmp.socBounds`` per year from the SAME library function every future
render calls (``scripts/lib/storage_compare.py::build_soc_bounds``, reading the
bundle's committed ``hourly/storage_<year>.parquet`` and the committed
``data/raw/caiso-rtm-eoh-soc/`` extract), and re-encodes with the frozen codec.
Every other byte of the payload is unchanged (checked: decode -> encode of the
untouched payload reproduces the file exactly before anything is added).

Usage::

    python3 scripts/probes/_rcaiso34_inject_soc_bounds.py RUN_ID BUNDLE_DIR [ISO]
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from scripts.lib import backcast_artifacts as ba  # noqa: E402
from scripts.lib import storage_compare as sc  # noqa: E402


def main() -> int:
    """Inject ``socBounds`` into every year of the run payload that has a storageCmp."""
    run_id, bundle = sys.argv[1], Path(sys.argv[2])
    iso = sys.argv[3] if len(sys.argv) > 3 else "CAISO"
    path = ba.RUNS / f"{run_id}.js"
    text = path.read_text()
    model = ba.decode_run_js(text)
    if ba.encode_run_js(run_id, model) != text.rstrip("\n"):
        raise SystemExit(f"{path}: codec round-trip is not byte-stable; refusing")
    years = model["years"] if isinstance(model.get("years"), dict) else model
    added = []
    for yr, blk in years.items():
        if not isinstance(blk, dict) or "storageCmp" not in blk:
            continue
        m = sc.load_model(bundle, iso, int(yr))
        sb = sc.build_soc_bounds(m, iso, int(yr)) if m is not None else None
        if sb is not None:
            blk["storageCmp"]["socBounds"] = sb
            added.append(int(yr))
    path.write_text(
        ba.encode_run_js(run_id, model) + ("\n" if text.endswith("\n") else "")
    )
    print(f"{path}: socBounds added for {sorted(added)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

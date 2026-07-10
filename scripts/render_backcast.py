"""Render backcast run DATA files for the codebase-site dashboard pages.

Unlike the standalone embedded report, this writes the gzip+base64 data files
that the codebase-site backcast pages (``docs/codebase-site/backcast-runs.html``
and ``calibration-status.html``, via ``js/bc-data.js``) consume, so a new run
is picked up automatically once its data file + manifest entry are written:

  * ``frontend/data/backcast/manifest.js`` — ``window.BC.meta`` (groups, zones,
    years, group labels) and ``window.BC.manifest`` (one entry per run: id,
    label, date, shorthand, definition, years).
  * ``frontend/data/backcast/benchmark.js`` — ``window.BC.benchGz`` (the shared
    CAMPD per-plant + EIA-930 fuel benchmark, gzip+base64).
  * ``frontend/data/backcast/runs/<id>.js`` — ``window.BC.runGz['<id>']`` (one
    run's model payload, gzip+base64), loaded lazily on selection.
  * ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — the per-(ISO, year)
    benchmark *part* (benchmark payload + that ISO's display meta). Parts are
    the COMMITTED source for the shared benchmark: each run rewrites only the
    parts for its own ISO/years ("newest bundle covering the year wins", the
    same rule ``build_payload`` applies), and ``scripts/build_manifest.py``
    assembles ``benchmark.js``/``manifest.js`` from parts + registry sidecars
    at deploy time. ``manifest.js`` and ``benchmark.js`` themselves are
    GENERATED files, refreshed only by the deploy workflow — never hand-commit
    them, so concurrent runs can never conflict on them.

The pages load the manifest + benchmark, then lazy-load the selected runs via
injected <script> tags and inflate them with DecompressionStream.

All gzip output uses ``mtime=0`` so re-rendering unchanged data is byte-stable
(identical bytes -> no spurious git churn, and concurrent same-ISO runs that
produce the same benchmark merge cleanly).

Run id = ``<YYYY-MM-DD>-<shorthand>``; the shorthand and 1-3 sentence
definition are auto-derived from the bundle's run_config note (editable in the
registry sidecar afterward). Clicking a run id anywhere shows its definition.

Usage:
    python scripts/render_backcast.py [ID=]BUNDLE ...
    # each BUNDLE is one run/config (may hold several years)
"""

from __future__ import annotations

import argparse
import base64
import gzip
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch", str(REPO / "scripts" / "render_calibration_html.py")
)
rch = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rch)

DATA_DIR = REPO / "frontend" / "data" / "backcast"
RUNS_DIR = DATA_DIR / "runs"
BENCH_DIR = DATA_DIR / "bench"


def _gzb64(obj) -> str:
    """Return gzip+base64 of a JSON-serializable object (byte-deterministic)."""
    return base64.b64encode(
        gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)
    ).decode()


def _slug(text: str) -> str:
    """Return a short kebab shorthand from free text (<= 4 words).

    D-3 exception: a trailing "ablation" survives the word cap, so a
    zero-forcing twin's id is always its keeper's slug + "-ablation"
    (the run_calibration_full --zero-forcing-ablation convention). Without
    this, a keeper label already filling the 4-word cap slugs its twin to
    the SAME id and the twin registration overwrites the keeper (pjm-97
    "pjm 97 measured-interfaces ablation", 2026-07-10). Existing registry
    ids are unaffected: every prior twin slug fit within 4 words.
    """
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    stop = {
        "the",
        "a",
        "an",
        "of",
        "to",
        "with",
        "and",
        "for",
        "re",
        "solve",
        "run",
        "calibration",
        "task",
        "ercot",
    }
    kept = [w for w in words if w not in stop]
    if kept and kept[-1] == "ablation":
        keep = kept[:-1][:4] + ["ablation"]
    else:
        keep = kept[:4]
    return "-".join(keep) or "run"


def _run_meta(bundle: Path, fallback_id: str) -> dict:
    """Derive id / date / shorthand / definition for a bundle."""
    meta = json.loads((bundle / "meta.json").read_text())
    note = ""
    rc = bundle / "run_config.json"
    if rc.exists():
        note = json.loads(rc.read_text()).get("model_changes_note", "") or ""
    ts = meta.get("timestamp", "")
    date = ts[:10] if ts else datetime.now().strftime("%Y-%m-%d")
    shorthand = fallback_id or _slug(note or bundle.name)
    definition = note.strip() or f"Calibration run from bundle {bundle.name}."
    return {
        "id": f"{date}-{shorthand}",
        "label": shorthand.replace("-", " "),
        "date": date,
        "shorthand": shorthand,
        "definition": definition,
        "years": meta["years"],
    }


def manifest_entry(label: str, bundle: Path) -> dict:
    """Return the complete dashboard manifest entry for one bundle.

    This is the record a registry sidecar stores in full, so the deploy-time
    assembler (``scripts/build_manifest.py``) can build ``manifest.js`` from
    sidecars alone — without bundle access, pandas, or the model package.
    """
    rm = _run_meta(bundle, _slug(label))
    rm["iso"] = json.loads((bundle / "meta.json").read_text()).get("iso", "ERCOT")
    rm["file"] = f"frontend/data/backcast/runs/{rm['id']}.js"
    return rm


def _write_bench_part(iso: str, year: int, meta: dict, bench_year: dict) -> Path:
    """Write the per-(ISO, year) benchmark part file (deterministic gzip).

    The part carries the year's benchmark payload plus the ISO display meta
    contributed by this render (groups/labels/zones); the assembler unions the
    metas and merges the year payloads across parts. Rewriting a part with
    identical content produces identical bytes, so unchanged parts never show
    up as a git diff.
    """
    part_dir = BENCH_DIR / iso
    part_dir.mkdir(parents=True, exist_ok=True)
    part = {"meta": {**meta, "years": [int(year)]}, "bench": bench_year}
    path = part_dir / f"{year}.json.gz"
    path.write_bytes(gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0))
    return path


def generate(
    runs: list[tuple[str, Path]],
    years: set[int] | None = None,
) -> None:
    """Write the deployable data files for the given runs.

    Writes the split files under ``frontend/data/backcast/`` (per-run
    ``runs/<id>.js`` + bench parts, plus a local-preview ``manifest.js`` /
    ``benchmark.js``). View them through the codebase-site pages
    (``docs/codebase-site/backcast-runs.html``), whose data loader falls back
    to ``frontend/data/backcast/`` when the deploy-built copy is absent.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    # Group runs by ISO (from each bundle's meta.json) so the dashboard's ISO
    # toggle can switch between ERCOT, PJM, ... each with its own benchmark,
    # zones and run set. The per-plant payload shape is identical across ISOs.
    by_iso: dict[str, list[tuple[str, Path]]] = {}
    for rid_hint, bundle in runs:
        iso = json.loads((bundle / "meta.json").read_text()).get("iso", "ERCOT")
        by_iso.setdefault(iso, []).append((rid_hint, bundle))

    meta_by_iso: dict[str, dict] = {}
    bench_by_iso: dict[str, str] = {}  # iso -> gzip+base64 benchmark
    manifest = []
    for iso, iso_runs in by_iso.items():
        D = rch.build_payload(iso_runs, years=years)
        meta_by_iso[iso] = {
            "groups": D["groups"],
            "groupLabel": D["groupLabel"],
            "zones": D["zones"],
            "years": D["years"],
        }
        bench_by_iso[iso] = _gzb64(D["bench"])
        for year, bench_year in D["bench"].items():
            _write_bench_part(iso, int(year), meta_by_iso[iso], bench_year)
        for i, (rid_hint, bundle) in enumerate(iso_runs):
            rm = _run_meta(bundle, _slug(rid_hint))
            if years is not None:
                rm["years"] = [y for y in rm["years"] if int(y) in years]
            rm["iso"] = iso
            rid = rm["id"]
            model = D["model"][i]
            model["label"] = rm["label"]
            js = (
                "window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};"
                f"window.BC.runGz[{json.dumps(rid)}]=" + json.dumps(_gzb64(model)) + ";"
            )
            (RUNS_DIR / f"{rid}.js").write_text(js)
            rm["file"] = f"frontend/data/backcast/runs/{rid}.js"
            manifest.append(rm)

    bench_js = (
        "window.BC=window.BC||{};window.BC.benchGz=" + json.dumps(bench_by_iso) + ";"
    )
    (DATA_DIR / "benchmark.js").write_text(bench_js)

    manifest_js = (
        "window.BC=window.BC||{};window.BC.meta="
        + json.dumps(meta_by_iso)
        + ";window.BC.manifest="
        + json.dumps(manifest)
        + ";"
    )
    (DATA_DIR / "manifest.js").write_text(manifest_js)

    sz = sum(f.stat().st_size for f in DATA_DIR.rglob("*.js")) / 1e6
    print(
        f"wrote {len(manifest)} run data files under {DATA_DIR} "
        f"({sz:.1f} MB data, ids: {[m['id'] for m in manifest]})"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+", help="[LABEL=]BUNDLE_DIR per run")
    ap.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=None,
        help="Restrict to these calendar years (e.g. 2023 2024); "
        "default = all years in each bundle.",
    )
    args = ap.parse_args()
    runs = []
    for spec in args.bundles:
        if "=" in spec:
            lab, _, d = spec.partition("=")
        else:
            d = spec
            lab = Path(spec).name
        runs.append((lab, Path(d)))
    generate(runs, years=set(args.years) if args.years else None)


if __name__ == "__main__":
    main()

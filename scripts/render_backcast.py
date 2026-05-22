"""Generate the deployable, JSON-driven backcast comparison dashboard.

Unlike the standalone embedded report, this writes a static shell
(``backcast-results.html``) plus separate gzip+base64 data files so the page
can be deployed on GitHub Pages and a new run is picked up automatically once
its data file + manifest entry are written:

  * ``frontend/data/backcast/manifest.js`` — ``window.BC.meta`` (groups, zones,
    years, group labels) and ``window.BC.manifest`` (one entry per run: id,
    label, date, shorthand, definition, years).
  * ``frontend/data/backcast/benchmark.js`` — ``window.BC.benchGz`` (the shared
    CAMPD per-plant + EIA-930 fuel benchmark, gzip+base64).
  * ``frontend/data/backcast/runs/<id>.js`` — ``window.BC.runGz['<id>']`` (one
    run's model payload, gzip+base64), loaded lazily on selection.

The shell loads the manifest + benchmark, then lazy-loads the selected runs via
injected <script> tags and inflates them with DecompressionStream — which works
both over http (Pages) and from a local file (no fetch/CORS trap).

Run id = ``<YYYY-MM-DD>-<shorthand>``; the shorthand and 1-3 sentence
definition are auto-derived from the bundle's run_config note (editable in
manifest.js afterward). Clicking a run id anywhere shows its definition.

Usage:
    python scripts/render_backcast.py [ID=]BUNDLE ... [--out backcast-results.html]
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
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location(
    "rch", str(REPO / "scripts" / "render_calibration_html.py"))
rch = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(rch)

DATA_DIR = REPO / "frontend" / "data" / "backcast"
RUNS_DIR = DATA_DIR / "runs"


def _gzb64(obj) -> str:
    """Return gzip+base64 of a JSON-serializable object."""
    return base64.b64encode(
        gzip.compress(json.dumps(obj).encode(), compresslevel=9)).decode()


def _slug(text: str) -> str:
    """Return a short kebab shorthand from free text (<= 4 words)."""
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    stop = {"the", "a", "an", "of", "to", "with", "and", "for", "re", "solve",
            "run", "calibration", "task", "ercot"}
    keep = [w for w in words if w not in stop][:4]
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
        "date": date, "shorthand": shorthand,
        "definition": definition, "years": meta["years"],
    }


def generate(runs: list[tuple[str, Path]], out: Path,
             standalone: Path | None = None) -> None:
    """Write the data files + the static shell for the given runs.

    Always writes the deployable split files (data under
    ``frontend/data/backcast/``) and the Pages shell at ``out``. When
    ``standalone`` is given, also writes a single self-contained HTML there
    with the manifest / benchmark / every run inlined (no separate files,
    no fetch) — suitable for sending or opening anywhere.
    """
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    # Reuse the payload builder, then split into shared benchmark + per-run.
    D = rch.build_payload(runs)
    meta_block = {
        "groups": D["groups"], "groupLabel": D["groupLabel"],
        "zones": D["zones"], "years": D["years"],
    }
    bench_js = ("window.BC=window.BC||{};window.BC.benchGz="
                + json.dumps(_gzb64(D["bench"])) + ";")
    (DATA_DIR / "benchmark.js").write_text(bench_js)

    manifest, run_js = [], []
    for i, (rid_hint, bundle) in enumerate(runs):
        rm = _run_meta(bundle, _slug(rid_hint))  # rid_hint is the CLI label
        rid = rm["id"]
        model = D["model"][i]
        model["label"] = rm["label"]
        js = ("window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};"
              f"window.BC.runGz[{json.dumps(rid)}]=" + json.dumps(_gzb64(model))
              + ";")
        (RUNS_DIR / f"{rid}.js").write_text(js)
        run_js.append(js)
        rm["file"] = f"frontend/data/backcast/runs/{rid}.js"
        manifest.append(rm)

    manifest_js = ("window.BC=window.BC||{};window.BC.meta="
                   + json.dumps(meta_block) + ";window.BC.manifest="
                   + json.dumps(manifest) + ";")
    (DATA_DIR / "manifest.js").write_text(manifest_js)

    gen = datetime.now().strftime("%Y-%m-%d %H:%M")
    link_css = '<link rel=stylesheet href="frontend/css/style.css">'
    # Deployable shell: load data via <script src> (Pages auto-pickup); the
    # repo stylesheet is linked (it sits at frontend/css/style.css).
    src_tags = ('<script src="frontend/data/backcast/manifest.js"></script>'
                '<script src="frontend/data/backcast/benchmark.js"></script>')
    out.write_text(SHELL.replace("__SITECSS__", link_css)
                   .replace("__DATASCRIPTS__", src_tags)
                   .replace("__GEN__", gen))
    sz = sum(f.stat().st_size for f in DATA_DIR.rglob("*.js")) / 1e6
    print(f"wrote {out} + {len(manifest)} run data files "
          f"({sz:.1f} MB data, ids: {[m['id'] for m in manifest]})")

    if standalone is not None:
        # Self-contained: inline the repo stylesheet (so the design tokens
        # resolve with no external file) and the data.
        css_path = REPO / "frontend" / "css" / "style.css"
        site_css = ("<style>" + css_path.read_text() + "</style>"
                    if css_path.exists() else link_css)
        inline = "".join(f"<script>{s}</script>"
                         for s in [manifest_js, bench_js, *run_js])
        standalone.write_text(SHELL.replace("__SITECSS__", site_css)
                              .replace("__DATASCRIPTS__", inline)
                              .replace("__GEN__", gen))
        print(f"wrote standalone {standalone} "
              f"({standalone.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles", nargs="+", help="[LABEL=]BUNDLE_DIR per run")
    ap.add_argument("--out", default=str(REPO / "backcast-results.html"))
    ap.add_argument("--standalone", default=None,
                    help="Also write a single self-contained HTML (data "
                         "inlined) at this path, for sending/offline viewing.")
    args = ap.parse_args()
    runs = []
    for spec in args.bundles:
        if "=" in spec:
            lab, _, d = spec.partition("=")
        else:
            d = spec; lab = Path(spec).name
        runs.append((lab, Path(d)))
    generate(runs, Path(args.out),
             Path(args.standalone) if args.standalone else None)


# The static shell HTML/JS is defined in the companion module to keep this file
# focused on data generation; imported lazily so `--help` stays fast.
from scripts._backcast_shell import SHELL  # noqa: E402

if __name__ == "__main__":
    main()

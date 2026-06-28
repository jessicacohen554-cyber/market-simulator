"""Assemble the backcast dashboard's shared files from committed parts.

The dashboard's shared files — ``frontend/data/backcast/manifest.js``,
``benchmark.js`` and the ``backcast-results.html`` shell — are GENERATED from the
committed parts by this script. They ARE committed (so a raw-branch GitHub Pages
build serves the dashboard too), but only the Pages deploy workflow refreshes them
on main — it is their single writer. Every calibration run commits only files in
its own namespace:

  * ``frontend/data/backcast/registry/<id>.json`` — the run's complete manifest
    entry (id, label, date, shorthand, definition, years, iso, file, bundle).
  * ``frontend/data/backcast/runs/<id>.js``       — the run's payload.
  * ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — per-(ISO, year)
    benchmark part: ``{"meta": {...}, "bench": {...}}`` (newest run covering
    the year supplies it).

This script is the pure, stdlib-only reducer over those parts: it unions the
per-part ISO metas, merges the year payloads into one gzip+base64 benchmark
per ISO, lists every registered run whose payload file exists, and writes the
three shared files. Because it needs no bundles, pandas or the model package,
the Pages deploy runs it in seconds on a sparse checkout — and locally it
rebuilds the preview after any run is added/removed:

    python scripts/build_manifest.py                 # refresh repo-root preview
    python scripts/build_manifest.py --site-dir _site  # deploy staging

Output is byte-deterministic (gzip mtime=0) apart from the page's generated-at
stamp.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

DATA = REPO / "frontend" / "data" / "backcast"
REGISTRY_DIR = DATA / "registry"
RUNS_DIR = DATA / "runs"
BENCH_DIR = DATA / "bench"
COMPLETENESS_DIR = DATA / "completeness"

# Manifest-entry fields the shell consumes (everything but the bundle path).
ENTRY_FIELDS = (
    "id",
    "label",
    "date",
    "shorthand",
    "definition",
    "years",
    "iso",
    "file",
)


def _gzb64(obj) -> str:
    """gzip+base64 a JSON-serializable object, byte-deterministically."""
    return base64.b64encode(
        gzip.compress(json.dumps(obj).encode(), compresslevel=9, mtime=0)
    ).decode()


def _load_entries() -> list[dict]:
    """Return manifest entries from the registry sidecars, sorted by id.

    Sidecars written before the entry fields were added (the skinny
    ``{id, label, bundle, iso}`` format) are upgraded from the bundle's
    meta/run_config when the bundle is present in this checkout; otherwise the
    run is skipped with a warning (re-register it with dashboard_add_run).
    Entries whose ``runs/<id>.js`` payload is missing are skipped too — a
    half-synced checkout still yields a dashboard of the runs it can serve.
    """
    entries: list[dict] = []
    for path in sorted(REGISTRY_DIR.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"  skip {path.name}: invalid JSON ({exc})", file=sys.stderr)
            continue
        if not all(k in rec for k in ENTRY_FIELDS):
            rec = _upgrade_skinny(rec, path)
            if rec is None:
                continue
        if not (RUNS_DIR / f"{rec['id']}.js").exists():
            print(f"  skip {path.name}: runs/{rec['id']}.js missing", file=sys.stderr)
            continue
        entries.append({k: rec[k] for k in ENTRY_FIELDS})
    entries.sort(key=lambda e: (e["id"], e["label"]))
    return entries


def _upgrade_skinny(rec: dict, path: Path) -> dict | None:
    """Best-effort completion of an old-format sidecar from its bundle."""
    bundle = REPO / rec.get("bundle", "")
    meta_file = bundle / "meta.json"
    if not meta_file.exists():
        print(
            f"  skip {path.name}: old sidecar format and bundle "
            f"{rec.get('bundle')} not in this checkout — re-register with "
            "scripts/dashboard_add_run.py",
            file=sys.stderr,
        )
        return None
    # Mirrors render_backcast._run_meta for the fields the shell displays.
    meta = json.loads(meta_file.read_text())
    note = ""
    rc = bundle / "run_config.json"
    if rc.exists():
        note = json.loads(rc.read_text()).get("model_changes_note", "") or ""
    rid = rec["id"]
    shorthand = rid[11:] if len(rid) > 11 else rid  # strip YYYY-MM-DD- prefix
    return {
        "id": rid,
        "label": shorthand.replace("-", " "),
        "date": rid[:10],
        "shorthand": shorthand,
        "definition": note.strip() or f"Calibration run {rec.get('label')}.",
        "years": meta.get("years", []),
        "iso": rec.get("iso", meta.get("iso", "ERCOT")),
        "file": f"frontend/data/backcast/runs/{rid}.js",
    }


def _assemble_benchmark() -> tuple[dict, dict]:
    """Merge the bench parts into per-ISO meta + benchmark payloads.

    Returns ``(meta_by_iso, bench_by_iso)`` where the meta is the union of
    every part's contribution: years are all part years, zones the sorted
    union, and groups keep the NEWEST part's canonical ordering with any
    older-only classes appended (so a taxonomy rename doesn't reorder the
    class heatmap under the latest runs).
    """
    meta_by_iso: dict[str, dict] = {}
    bench_by_iso: dict[str, dict] = {}
    for iso_dir in sorted(p for p in BENCH_DIR.glob("*") if p.is_dir()):
        iso = iso_dir.name
        parts = []
        for f in sorted(iso_dir.glob("*.json.gz"), reverse=True):
            try:
                parts.append(
                    (
                        int(f.stem.split(".")[0]),
                        json.loads(gzip.decompress(f.read_bytes())),
                    )
                )
            except (ValueError, OSError, json.JSONDecodeError) as exc:
                print(f"  skip bench part {iso}/{f.name}: {exc}", file=sys.stderr)
        if not parts:
            continue
        groups: list[str] = []
        group_label: dict[str, str] = {}
        zones: set[str] = set()
        years: set[int] = set()
        bench: dict[str, dict] = {}
        for year, part in parts:  # newest year first
            m = part["meta"]
            groups += [g for g in m["groups"] if g not in groups]
            for g, lab in m["groupLabel"].items():
                group_label.setdefault(g, lab)
            zones.update(m["zones"])
            years.add(year)
            bench[str(year)] = part["bench"]
        meta_by_iso[iso] = {
            "groups": groups,
            "groupLabel": group_label,
            "zones": sorted(zones),
            "years": sorted(years),
        }
        bench_by_iso[iso] = {str(y): bench[str(y)] for y in sorted(years)}
    return meta_by_iso, bench_by_iso


def _assemble_completeness() -> dict:
    """Slim ``{year: {iso: {class: {status, gate}}}}`` from the committed parts.

    Reduces ``completeness/eia923_<year>.json`` (scripts/audit_eia923_completeness)
    to just the per-(year, ISO, class) status + gate the dashboard needs to
    color-code the generation-mix table for a preliminary-EIA-923 vintage. Returns
    an empty map when no completeness parts are committed (the table then renders
    with no completeness flags, exactly as before).
    """
    out: dict[str, dict] = {}
    if not COMPLETENESS_DIR.exists():
        return out
    for part in sorted(COMPLETENESS_DIR.glob("eia923_*.json")):
        obj = json.loads(part.read_text())
        year = str(obj["year"])
        isos = {
            iso: {
                klass: {"status": rec["status"], "gate": bool(rec.get("gate"))}
                for klass, rec in classes.items()
            }
            for iso, classes in obj.get("isos", {}).items()
        }
        out[year] = isos
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--site-dir",
        default=str(REPO),
        help="Root to write into (repo root for the local "
        "preview, the Pages staging dir for deploys).",
    )
    args = ap.parse_args()
    site = Path(args.site_dir)

    entries = _load_entries()
    if not entries:
        sys.exit(
            "registry is empty (no usable runs); refusing to write an empty dashboard."
        )
    meta_by_iso, bench_by_iso = _assemble_benchmark()
    for iso in sorted({e["iso"] for e in entries} - set(meta_by_iso)):
        print(
            f"  WARNING: runs registered for {iso} but no bench parts under "
            f"{BENCH_DIR}/{iso}/ — its runs will not be selectable",
            file=sys.stderr,
        )
    completeness = _assemble_completeness()

    from scripts.probes._backcast_shell import SHELL

    # Pre-serialize what each data file will carry so the version hash covers the
    # exact bytes the browser sees, not just the inputs that produced them.
    meta_js = json.dumps(meta_by_iso, sort_keys=True)
    manifest_js = json.dumps(entries, sort_keys=True)
    bench_gz = {i: _gzb64(b) for i, b in bench_by_iso.items()}
    bench_js = json.dumps(bench_gz, sort_keys=True)
    completeness_js = json.dumps(completeness, sort_keys=True)

    # Content-hash version stamp. Embedded in BOTH the shell HTML (SHELL_VER)
    # and manifest.js (DATA_VER); if they don't match, the shell self-heals
    # via a one-shot reload (see manifest.js prelude below). Hashing the
    # actual emitted content + the shell template means the hash is stable
    # across deploys when nothing changed — so a no-op deploy produces a
    # byte-identical HTML and stops the steady drip of [skip ci] commits.
    h = hashlib.sha1()
    h.update(SHELL.encode())
    h.update(b"|")
    h.update(meta_js.encode())
    h.update(b"|")
    h.update(manifest_js.encode())
    h.update(b"|")
    h.update(bench_js.encode())
    h.update(b"|")
    h.update(completeness_js.encode())
    ver = h.hexdigest()[:16]

    out_data = site / "frontend" / "data" / "backcast"
    out_data.mkdir(parents=True, exist_ok=True)
    # Self-healing prelude — runs BEFORE benchmark.js / completeness.js (script
    # order in the shell) so a stale cached shell paired with a fresh manifest
    # triggers a single hard reload of the HTML before any downstream code can
    # crash on a shape-changed window.BC.benchGz / .meta. SHELL_VER is set
    # inline at the top of the shell HTML; if it is undefined (very old shell
    # that predates this fix) or simply different from this manifest's
    # DATA_VER, we replace the URL with a fresh cache-busting query so the
    # network returns the current HTML. sessionStorage guards against an
    # infinite loop if the upstream HTML is itself wedged stale.
    prelude = (
        f'window.BC=window.BC||{{}};window.BC.DATA_VER="{ver}";'
        "(function(){if(window.BC.SHELL_VER===window.BC.DATA_VER)return;"
        'try{var k="bc_shell_reload_"+window.BC.DATA_VER;'
        "if(sessionStorage.getItem(k))return;"
        'sessionStorage.setItem(k,"1");'
        "var u=location.pathname+'?_='+Date.now()+location.hash;"
        "location.replace(u);"
        "}catch(e){}})();"
    )
    (out_data / "manifest.js").write_text(
        prelude
        + "window.BC.meta="
        + meta_js
        + ";window.BC.manifest="
        + manifest_js
        + ";"
    )
    (out_data / "benchmark.js").write_text(
        "window.BC=window.BC||{};window.BC.benchGz=" + bench_js + ";"
    )
    # EIA-923 completeness map (window.BC.completeness): per-(year, ISO, class)
    # status the mix table uses to color-code incomplete-plant-data classes in a
    # preliminary vintage. Generated from the committed completeness parts.
    (out_data / "completeness.js").write_text(
        "window.BC=window.BC||{};window.BC.completeness=" + completeness_js + ";"
    )

    # Cache-busting query strings now use the content hash, so they only change
    # when content actually changes — the deploy step that writes back into the
    # repo only commits on real updates (the per-deploy timestamp was forcing a
    # no-op commit every deploy). Each tag carries an onerror that records the
    # failure into window.BC._loadErr so boot() can report which files failed.
    _onerr = 'onerror="window.BC._loadErr.push(this.src)"'
    # User-visible "as of" stamp — the newest registered run's date is what
    # actually changed; that keeps the HTML byte-identical across deploys when
    # no new run landed, while still telling the reader how fresh the data is.
    as_of = max(
        (e.get("date") or "" for e in entries), default=""
    ) or datetime.now().strftime("%Y-%m-%d")
    shell = (
        SHELL.replace(
            "__SITECSS__", '<link rel=stylesheet href="frontend/css/style.css">'
        )
        .replace(
            "__DATASCRIPTS__",
            f'<script src="frontend/data/backcast/manifest.js?v={ver}" {_onerr}>'
            "</script>"
            f'<script src="frontend/data/backcast/benchmark.js?v={ver}" {_onerr}>'
            "</script>"
            f'<script src="frontend/data/backcast/completeness.js?v={ver}" {_onerr}>'
            "</script>"
            f'<script src="frontend/data/backcast/status.js?v={ver}" {_onerr}>'
            "</script>",
        )
        .replace("__SHELL_VER__", ver)
        .replace("__GEN__", as_of)
    )
    (site / "backcast-results.html").write_text(shell)
    print(
        f"assembled dashboard at {site}: {len(entries)} runs, ISOs "
        f"{sorted(meta_by_iso)} (years per ISO: "
        f"{ {i: m['years'] for i, m in meta_by_iso.items()} })"
    )


if __name__ == "__main__":
    main()

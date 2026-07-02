"""Assemble the backcast dashboard DATA files from committed parts.

Reduces the committed per-run registry sidecars + bench/completeness parts to
the shared data files the codebase-site backcast pages consume
(``docs/codebase-site/calibration-status.html`` and ``backcast-runs.html``,
via ``js/bc-data.js``):

  * ``frontend/data/backcast/manifest.js``     — ``window.BC.meta`` + ``window.BC.manifest``
  * ``frontend/data/backcast/benchmark.js``    — ``window.BC.benchGz`` (per-ISO gzip+base64)
  * ``frontend/data/backcast/completeness.js`` — ``window.BC.completeness``

The old root dashboard shell (``backcast-results.html``) is retired — the file
at repo root is now a static redirect stub to the codebase-site pages and is
never regenerated. Run ``scripts/build_codebase_site_backcast.py`` AFTER this
script to copy the data subset into ``docs/codebase-site/data/backcast/``.

Per-run files committed by calibration sessions (never by this script):

  * ``frontend/data/backcast/registry/<id>.json`` — manifest sidecar.
  * ``frontend/data/backcast/runs/<id>.js``       — run payload.
  * ``frontend/data/backcast/bench/<ISO>/<year>.json.gz`` — benchmark part.

Usage::

    python scripts/build_manifest.py                 # refresh repo-root preview
    python scripts/build_manifest.py --site-dir _site  # deploy staging

Output is byte-deterministic (gzip mtime=0).
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
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

    meta_js = json.dumps(meta_by_iso, sort_keys=True)
    manifest_js = json.dumps(entries, sort_keys=True)
    bench_gz = {i: _gzb64(b) for i, b in bench_by_iso.items()}
    bench_js = json.dumps(bench_gz, sort_keys=True)
    completeness_js = json.dumps(completeness, sort_keys=True)

    out_data = site / "frontend" / "data" / "backcast"
    out_data.mkdir(parents=True, exist_ok=True)
    (out_data / "manifest.js").write_text(
        "window.BC=window.BC||{};window.BC.meta="
        + meta_js
        + ";window.BC.manifest="
        + manifest_js
        + ";"
    )
    (out_data / "benchmark.js").write_text(
        "window.BC=window.BC||{};window.BC.benchGz=" + bench_js + ";"
    )
    (out_data / "completeness.js").write_text(
        "window.BC=window.BC||{};window.BC.completeness=" + completeness_js + ";"
    )
    print(
        f"assembled backcast data at {out_data}: {len(entries)} runs, ISOs "
        f"{sorted(meta_by_iso)} (years per ISO: "
        f"{ {i: m['years'] for i, m in meta_by_iso.items()} })"
    )


if __name__ == "__main__":
    main()

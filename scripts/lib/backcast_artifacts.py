"""Single home for the backcast dashboard artifact IO (stdlib-only).

The calibration-run dashboard chain — the registry sidecar, the gzip+base64 run
payload (``runs/<id>.js``), the per-(ISO, year) bench part
(``bench/<ISO>/<year>.json.gz``) and the assembled ``manifest.js`` — is a frozen
wire contract (``docs/backcast-artifact-contract.md``; CLAUDE.md rules 15/20).
Three consumers reconstruct a run *from these bytes alone* (the scorer
``calibration_verdict``; the Pages deploy; replay/goldens), and byte-determinism
lets concurrent registrations merge without conflict (contract §8). This module
is the single implementation of that byte layout, so a codec can never drift
between the ~8 scripts that read/write it (the audit found two different regexes
for one wrapper).

STDLIB-ONLY by construction: the Pages deploy runs these codecs on a bare
``python3`` (no numpy/pandas/model package), and the scorer is deliberately
numpy-free.

Frozen parameters (do NOT change — they re-grade every registered keeper,
contract §9):

  * ``gzb64``: ``compresslevel=9``, ``mtime=0``, default ``json.dumps``
    separators (``sort_keys=False``). ``mtime=0`` makes unchanged input encode
    to identical bytes (no git churn, conflict-free concurrent registration).
  * ``runs/<id>.js`` wrapper: ``window.BC.runGz["<id>"]="<gzb64>"`` — the value
    is the DOUBLE-encoded ``json.dumps(gzb64(model))`` (a JSON string literal
    whose contents are the base64); the read side matches ``= "<b64>"`` by regex.
  * bench parts: raw gzip bytes (``compresslevel=9``, ``mtime=0``), frozen field
    order; ``benchmark.js`` re-wraps them in base64 per ISO.
  * ``manifest.js``: ``window.BC.meta=<json>;window.BC.manifest=<json>;``.

The ``sort_keys=True`` gzb64 variant is the SEPARATE forecast-bands codec
(``export_forecast_bands`` / ``window.FB.bandsGz``) — not a backcast wire format,
exposed here only so both live in one place.
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path

# scripts/lib/backcast_artifacts.py -> <repo>/scripts/lib -> <repo>
REPO = Path(__file__).resolve().parent.parent.parent

# Frozen dashboard-artifact locations (contract §1; CLAUDE.md rule 15).
DATA = REPO / "frontend" / "data" / "backcast"
REGISTRY = DATA / "registry"
RUNS = DATA / "runs"
BENCH = DATA / "bench"


# --------------------------------------------------------------------------- #
# gzb64 codec (WIRE FORMAT — contract §4.1)
# --------------------------------------------------------------------------- #
def gzb64(obj, *, sort_keys: bool = False) -> str:
    """Return gzip+base64 of a JSON-serializable object (byte-deterministic).

    The frozen backcast codec uses default ``json.dumps`` separators and NO key
    sorting (``sort_keys=False``); ``compresslevel=9`` + ``mtime=0`` make
    unchanged input encode to identical bytes. ``sort_keys=True`` is the
    forecast-bands codec (``export_forecast_bands``), whose payload is written
    with sorted keys — same gzip parameters, different JSON ordering.
    """
    return base64.b64encode(
        gzip.compress(
            json.dumps(obj, sort_keys=sort_keys).encode(), compresslevel=9, mtime=0
        )
    ).decode()


def ungzb64(text: str):
    """Inverse of :func:`gzb64`: base64-decode, gunzip, then JSON-parse."""
    return json.loads(gzip.decompress(base64.b64decode(text)))


# --------------------------------------------------------------------------- #
# runs/<id>.js payload (WIRE FORMAT — contract §3.2)
# --------------------------------------------------------------------------- #
# Read side of the payload wrapper: the gzb64 value is the sole quoted base64
# literal in the file. Frozen (contract §9) — ``calibration_verdict`` and the
# browser (``bc-data.js``) both parse the file with this shape.
_RUN_JS_PAYLOAD_RE = re.compile(r'=\s*"([A-Za-z0-9+/=]+)"')


def encode_run_js(run_id: str, model: dict) -> str:
    """Return the one-line ``runs/<id>.js`` assignment for a run model payload.

    The value is DOUBLE-encoded: ``gzb64(model)`` (a base64 string) wrapped
    again in ``json.dumps`` so it is a JSON string literal in the JS source.
    """
    return (
        "window.BC=window.BC||{};window.BC.runGz=window.BC.runGz||{};"
        f"window.BC.runGz[{json.dumps(run_id)}]=" + json.dumps(gzb64(model)) + ";"
    )


def decode_run_js(text: str) -> dict:
    """Decode a ``runs/<id>.js`` payload (``window.BC.runGz[..]="<b64>"``)."""
    m = _RUN_JS_PAYLOAD_RE.search(text)
    if not m:
        raise ValueError("no gzip+base64 payload found in run js")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


# --------------------------------------------------------------------------- #
# bench parts (WIRE FORMAT — contract §3.3)
# --------------------------------------------------------------------------- #
def write_bench_part(
    bench_dir: Path, iso: str, year: int, meta: dict, bench_year: dict
) -> Path:
    """Write the per-(ISO, year) benchmark part ``<bench_dir>/<iso>/<year>.json.gz``.

    Raw gzip bytes (``compresslevel=9``, ``mtime=0``) — NOT base64-wrapped (the
    deploy re-wraps parts into ``benchmark.js`` per ISO). The part is
    ``{"meta": {**meta, "years": [int(year)]}, "bench": bench_year}``; rewriting
    identical content yields identical bytes (conflict-free re-render).
    """
    part_dir = Path(bench_dir) / iso
    part_dir.mkdir(parents=True, exist_ok=True)
    part = {"meta": {**meta, "years": [int(year)]}, "bench": bench_year}
    path = part_dir / f"{year}.json.gz"
    path.write_bytes(gzip.compress(json.dumps(part).encode(), compresslevel=9, mtime=0))
    return path


def load_bench_part(path: Path) -> dict:
    """Return the ``{"meta": ..., "bench": ...}`` dict from a bench part file."""
    return json.loads(gzip.decompress(Path(path).read_bytes()))


# --------------------------------------------------------------------------- #
# manifest.js writer / parser PAIR (WIRE FORMAT — contract §3.4)
# --------------------------------------------------------------------------- #
def render_manifest_js(meta_by_iso: dict, manifest, *, sort_keys: bool = True) -> str:
    """Return the ``manifest.js`` source (``window.BC.meta`` + ``window.BC.manifest``).

    The deploy assembler and the codebase-site copy serialize with
    ``sort_keys=True`` (byte-stable, conflict-free); the ``render_backcast``
    local preview passes ``sort_keys=False`` to reproduce its historical bytes
    (that preview file is never gated — the deploy rebuilds it).
    """
    return (
        "window.BC=window.BC||{};window.BC.meta="
        + json.dumps(meta_by_iso, sort_keys=sort_keys)
        + ";window.BC.manifest="
        + json.dumps(manifest, sort_keys=sort_keys)
        + ";"
    )


def write_manifest_js(
    path: Path, meta_by_iso: dict, manifest, *, sort_keys: bool = True
) -> None:
    """Write :func:`render_manifest_js` to ``path``."""
    Path(path).write_text(
        render_manifest_js(meta_by_iso, manifest, sort_keys=sort_keys)
    )


def parse_manifest_js(path: Path) -> tuple[dict, list]:
    """Extract ``(meta, manifest)`` from a ``manifest.js`` file (parser of the pair).

    Anchors ``json.JSONDecoder.raw_decode`` at each assignment's opening bracket
    rather than a non-greedy ``\\{.*?\\};`` / ``\\[.*?\\];`` regex. A run's
    ``definition``/``market_story`` string may legitimately contain ``];`` or
    ``};`` (e.g. the C3c ``[7,9]`` band notation), which a non-greedy match
    truncates at — breaking the whole deploy. ``raw_decode`` consumes exactly one
    well-formed JSON value and ignores the trailing ``;`` and everything after,
    so any string content is safe. Raises ``ValueError`` when a marker or its
    value is missing.
    """
    text = Path(path).read_text()
    dec = json.JSONDecoder()

    def _decode_after(marker: str):
        i = text.find(marker)
        if i < 0:
            raise ValueError(f"Cannot parse manifest from {path}: missing {marker!r}")
        j = i + len(marker)
        while j < len(text) and text[j] not in "{[":
            j += 1
        if j >= len(text):
            raise ValueError(
                f"Cannot parse manifest from {path}: no value after {marker!r}"
            )
        obj, _ = dec.raw_decode(text, j)
        return obj

    return _decode_after("window.BC.meta="), _decode_after("window.BC.manifest=")


# --------------------------------------------------------------------------- #
# registry sidecars
# --------------------------------------------------------------------------- #
def sidecar_path(run_id: str, registry_dir: Path | None = None) -> Path:
    """Path to the ``registry/<run_id>.json`` sidecar."""
    return (registry_dir or REGISTRY) / f"{run_id}.json"


def load_sidecar(run_id: str, registry_dir: Path | None = None) -> dict:
    """Return the parsed registry sidecar for ``run_id``."""
    return json.loads(sidecar_path(run_id, registry_dir).read_text())


def iter_sidecars(registry_dir: Path | None = None) -> Iterator[tuple[Path, dict]]:
    """Yield ``(path, record)`` for every registry sidecar, sorted by path.

    Sidecars that fail to parse are skipped with a stderr note — the assemblers'
    "a half-synced checkout still yields a usable dashboard" behavior.
    """
    registry_dir = registry_dir or REGISTRY
    for path in sorted(registry_dir.glob("*.json")):
        try:
            rec = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            print(f"  skip {path.name}: invalid JSON ({exc})", file=sys.stderr)
            continue
        yield path, rec


def write_sidecar(entry: dict, registry_dir: Path | None = None) -> Path:
    """Write ``entry`` (which must carry ``id``) as its registry sidecar.

    ``indent=2`` + a trailing newline — the committed sidecar format.
    """
    registry_dir = registry_dir or REGISTRY
    registry_dir.mkdir(parents=True, exist_ok=True)
    path = registry_dir / f"{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2) + "\n")
    return path


def resolve_run_id(
    arg: str, registry_dir: Path | None = None, repo: Path | None = None
) -> str:
    """Return the run id for a CLI arg that is either a run id or a bundle dir.

    A run id resolves when its sidecar exists. Otherwise ``arg`` is treated as a
    bundle path and matched against each sidecar's stored ``bundle`` field.
    """
    registry_dir = registry_dir or REGISTRY
    repo = repo or REPO
    if (registry_dir / f"{arg}.json").exists():
        return arg
    p = Path(arg)
    cand = {arg, p.name, str(p)}
    try:
        cand.add(str(p.resolve().relative_to(repo)))
    except ValueError:
        pass
    for side in sorted(registry_dir.glob("*.json")):
        rec = json.loads(side.read_text())
        if rec.get("bundle") in cand or Path(rec.get("bundle", "")).name == p.name:
            return rec["id"]
    raise SystemExit(
        f"could not resolve a registered run from {arg!r} "
        f"(no registry sidecar and no bundle match)."
    )


def bundle_dir_for(
    rec: dict, repo: Path | None = None, calib_root: Path | None = None
) -> Path | None:
    """Resolve a sidecar's ``bundle`` field to a path under ``results/calibration``.

    Returns ``None`` when the field is absent or — as a hard safety guard for
    retention deletes — resolves outside the calibration root, so retention can
    never delete an arbitrary path.
    """
    repo = repo or REPO
    calib_root = calib_root or (repo / "results" / "calibration")
    raw = rec.get("bundle")
    if not raw:
        return None
    p = Path(raw)
    p = p if p.is_absolute() else repo / p
    try:
        p.resolve().relative_to(calib_root.resolve())
    except ValueError:
        return None
    return p

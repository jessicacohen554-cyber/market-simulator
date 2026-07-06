"""Desktop launcher: stdlib-only local HTTP server + self-contained HTML launch
page for the LCE portfolio tool (ADR 0016).

Started by ``launcher/run_lce.sh`` / ``launcher/run_lce.bat`` (or directly via
``python -m lce_portfolio.launcher``), this module binds a
:class:`http.server.ThreadingHTTPServer` to ``127.0.0.1`` on an ephemeral port
(unless ``--port`` is given), opens the default browser on a self-contained
HTML page (inline CSS/JS, no CDN, no external fetch — same design system as
the ADR 0014 report), and executes queued runs **sequentially** through the
existing :mod:`lce_portfolio.cli` entry point — no forked solve logic.

The exposed launch-page parameters are exactly ADR 0016 §3: ``iso``, ``mode``,
premium deltas / matching targets, ``lcoe_sensitivity``, load file path, LMP
file path, ``run-id``, and open-report-when-done. Everything else (resource
caps, gas price, additionality, ...) stays at :class:`PortfolioConfig`
defaults / config-file-only.

Saved configurations and last-used values persist as JSON under a state
directory (default ``launcher/``, gitignored). A single background worker
thread drains a queue of runs one at a time, so LP solves never overlap
regardless of how many browser tabs or queued batches are open.
"""

from __future__ import annotations

import argparse
import contextlib
import html
import io
import json
import math
import re
import sys
import threading
import time
import traceback
import urllib.parse
import webbrowser
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from queue import Queue

from lce_portfolio import __version__, cli
from lce_portfolio.config import (
    LMP_KIND_ANNUAL_AVERAGE_FLAT,
    LMP_KIND_HOURLY,
    PortfolioConfig,
)

# --- Paths --------------------------------------------------------------

#: scope2-lce-portfolio/ (this file is src/lce_portfolio/launcher.py).
PKG_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_DIR = PKG_ROOT / "launcher"
DEFAULT_RESULTS_DIR = PKG_ROOT / "results"
DEFAULT_INPUTS_DIR = PKG_ROOT / "data" / "inputs"
DEFAULT_REFERENCE_LOAD = PKG_ROOT / "data" / "reference" / "reference_load_100mw.csv"
#: HP-02 real-LMP bundle (optional — degrades gracefully if absent, HP-03 §C).
DEFAULT_BUNDLED_LMP_DIR = PKG_ROOT / "data" / "bundled" / "lmp"
#: Fillable input-template examples (HP-03 §C Templates help block).
DEFAULT_TEMPLATES_DIR = PKG_ROOT / "data" / "templates"

SAVED_CONFIGS_FILENAME = "saved_configs.json"
LAST_USED_FILENAME = "last_used.json"
#: Append-only run history (HP-03 §B): machine-local state like the two
#: files above, gitignored.
RUN_LOG_FILENAME = "run_log.jsonl"

# --- Server defaults (ADR 0016 §2: loopback only) -----------------------

DEFAULT_HOST = "127.0.0.1"
EPHEMERAL_PORT = 0  # ask the OS for a free port when --port is not given

#: Upper bound on accepted request bodies. A real launch-page submit is a few
#: KB even with a long queue; anything near this size is malformed or hostile,
#: and an unchecked Content-Length must never hang the handler or absorb
#: unbounded memory (review finding LN-2).
MAX_REQUEST_BYTES = 1_048_576

# --- Exposed parameter domains (ADR 0016 §3) -----------------------------

#: The six ISOs the tool's data tables cover, plus the data-free demo/test ISO.
KNOWN_ISOS = ("ERCOT", "CAISO", "PJM", "MISO", "NYISO", "NEISO", "SAMPLE")
KNOWN_MODES = ("premium_cap", "matching_target")
KNOWN_SENSITIVITIES = ("low", "mid", "high")

_DEFAULT_CONFIG = PortfolioConfig()
DEFAULT_ISO = "ERCOT"  # first real ISO; SAMPLE stays available for the demo/tests
DEFAULT_MODE = _DEFAULT_CONFIG.mode
DEFAULT_PREMIUM_DELTAS = _DEFAULT_CONFIG.premium_deltas
DEFAULT_MATCHING_TARGETS = _DEFAULT_CONFIG.matching_targets
DEFAULT_LCOE_SENSITIVITY = _DEFAULT_CONFIG.lcoe_sensitivity
DEFAULT_OPEN_REPORT_WHEN_DONE = True

#: run_id / config-name path components: one segment, alnum-first (mirrors
#: cli._RUN_ID_RE — anything looser risks composing an escaping results path).
_SAFE_NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*")
_REPORT_PATH_RE = re.compile(
    r"^/reports/([A-Za-z0-9][A-Za-z0-9._-]*)/(report\.html|report\.json)$"
)


def _fmt_list(values: tuple[float, ...]) -> str:
    """Render a numeric tuple as the comma-separated string the form uses."""
    return ", ".join(_fmt_num(v) for v in values)


def _fmt_num(v: float) -> str:
    """Render ``v`` without a trailing ``.0`` for whole numbers."""
    return str(int(v)) if float(v).is_integer() else str(v)


def parse_float_list(raw, field_name: str) -> tuple[float, ...]:
    """Parse a comma-separated string or list/tuple of numbers into floats.

    Raises :class:`ValueError` with a message naming ``field_name`` on any
    non-numeric entry — never lets a ``TypeError`` escape as a raw traceback.
    Empty lists and non-finite values (``nan``/``inf``) are rejected too
    (review finding LN-4): ``nan`` passes ``PortfolioConfig``'s ``d <= 0``
    range check (all nan comparisons are False) and would reach the LP as a
    nan premium budget, and an empty setpoint list makes the whole run fail
    with a misleading "no setpoint solved" message.
    """
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
    elif isinstance(raw, (list, tuple)):
        parts = list(raw)
    else:
        raise ValueError(f"{field_name} must be a comma-separated string or list")
    if not parts:
        raise ValueError(f"{field_name} must contain at least one value")
    try:
        values = tuple(float(p) for p in parts)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be numeric, got {raw!r}") from exc
    if not all(math.isfinite(v) for v in values):
        raise ValueError(f"{field_name} must be finite numbers, got {raw!r}")
    return values


def resolve_default_lmp(inputs_dir: Path) -> dict:
    """Return the launch page's default LMP file info (ADR 0016 §3).

    Mirrors ``examples/run_real_sweep.py``'s ``resolve_lmp_path`` precedence
    (newest real ``bau_lmp_*.csv`` over newest ``*_dummy.csv``) but never
    invokes the market-sim exporter subprocess itself — the launcher only
    reports what already exists on disk, so it can never trigger a market-sim
    solve (stakeholder hard hold). Returns
    ``{"path": str|None, "is_synthetic": bool, "source": str}``.
    """
    candidates = sorted(inputs_dir.glob("bau_lmp_*.csv")) if inputs_dir.exists() else []
    real = [p for p in candidates if not p.stem.endswith("_dummy")]
    if real:
        newest = max(real, key=lambda p: p.stat().st_mtime)
        return {"path": str(newest), "is_synthetic": False, "source": "real"}
    dummy = [p for p in candidates if p.stem.endswith("_dummy")]
    if dummy:
        newest = max(dummy, key=lambda p: p.stat().st_mtime)
        return {"path": str(newest), "is_synthetic": True, "source": "dummy_existing"}
    return {"path": None, "is_synthetic": True, "source": "none"}


def ensure_reference_load(path: Path = DEFAULT_REFERENCE_LOAD) -> Path:
    """Return the bundled reference load, generating it if missing (ADR 0016 §3).

    ``data/reference/`` is gitignored (PLAN.md §6), so a fresh checkout
    regenerates it from ``scripts/make_reference_load.py`` on first use —
    pure numpy/pandas, no ``market_sim`` involvement, no solve.
    """
    if path.exists():
        return path
    scripts_dir = str(PKG_ROOT / "scripts")
    added = scripts_dir not in sys.path
    if added:
        sys.path.insert(0, scripts_dir)
    try:
        from make_reference_load import build_reference_load
    finally:
        if added:
            sys.path.remove(scripts_dir)
    df = build_reference_load()
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.3f")
    return path


# --- Input-candidate discovery (HP-03 §C) ---------------------------------

#: Column sets used only to *hint* a dropdown/help-block schema label — a
#: lightweight peek, never the authoritative validator (that's intake.py,
#: which still runs at solve time regardless of what this guesses).
_LOAD_COLUMNS = {"hour", "iso", "load_mwh"}
_LMP_HOURLY_COLUMNS = {"hour", "iso", "lmp"}
_LMP_ANNUAL_AVERAGE_COLUMNS = {"iso", "annual_avg_lmp"}

#: Static captions for the three committed example templates (not a copy of
#: their data — data/templates/README.md documents the full contract).
_TEMPLATE_LABELS = {
    "load_8760_by_facility_template.csv": "8760 load by ISO and facility",
    "lmp_8760_template.csv": "Full hourly BAU LMP (preferred)",
    "lmp_annual_average_template.csv": "Annual-average LMP comparison (HP-01)",
}


def _peek_header_columns(path: Path) -> list[str] | None:
    """Best-effort column-name peek for one candidate file.

    Reads only the CSV header line or the Parquet footer schema (pyarrow)
    — never the full file — so a huge or slow-to-read candidate can't stall
    the dropdown/help endpoints. Never raises: any failure (missing file,
    permission error, corrupt header, unreadable Parquet footer) returns
    ``None``, so a bad candidate just shows an "unknown" hint instead of a
    500 — this is a UI convenience, not the real intake validator.
    """
    try:
        if path.suffix == ".parquet":
            import pyarrow.parquet as pq

            return list(pq.ParquetFile(path).schema.names)
        with path.open("r", encoding="utf-8", errors="replace") as f:
            header = f.readline()
        return [c.strip() for c in header.split(",") if c.strip()]
    except Exception:  # noqa: BLE001 - a UI hint must never crash the endpoint
        return None


def classify_input_file(path: Path) -> str:
    """Best-effort schema classification for one candidate file.

    Returns ``"load"``, :data:`LMP_KIND_HOURLY`,
    :data:`LMP_KIND_ANNUAL_AVERAGE_FLAT`, or ``"unknown"`` — mirrors the
    column-set detection rule in ``intake.py`` (HP-01) but only peeks the
    header (:func:`_peek_header_columns`), so the same vocabulary
    ``run_metadata.json``'s ``lmp_kind`` uses also labels a dropdown entry
    before any file is ever read in full.
    """
    cols = _peek_header_columns(path)
    if cols is None:
        return "unknown"
    cols_set = set(cols)
    if _LMP_HOURLY_COLUMNS <= cols_set:
        return LMP_KIND_HOURLY
    if _LMP_ANNUAL_AVERAGE_COLUMNS <= cols_set and "hour" not in cols_set:
        return LMP_KIND_ANNUAL_AVERAGE_FLAT
    if _LOAD_COLUMNS <= cols_set:
        return "load"
    return "unknown"


def list_input_candidates(
    *,
    inputs_dir: Path,
    bundled_lmp_dir: Path,
    templates_dir: Path,
    reference_load: Path,
) -> dict:
    """Server-side candidate-file list for the load/LMP dropdowns (HP-03 §C).

    Lists ONLY the whitelisted directories below plus the single bundled
    reference-load path — never arbitrary filesystem browsing (free-text
    path entry is a separate, unrestricted form field, unaffected by this).
    Each directory is optional: ``bundled_lmp_dir`` may not exist yet (HP-02
    not landed, or a fresh checkout before the pull-out data is fetched) and
    silently contributes nothing rather than raising.
    """

    def _dir_candidates(dir_path: Path, source: str) -> list[dict]:
        if not dir_path.is_dir():
            return []
        out = []
        for p in sorted(dir_path.iterdir()):
            if not p.is_file() or p.suffix not in (".csv", ".parquet"):
                continue
            out.append(
                {
                    "path": str(p),
                    "label": p.name,
                    "source": source,
                    "kind": classify_input_file(p),
                }
            )
        return out

    candidates = (
        _dir_candidates(inputs_dir, "inputs")
        + _dir_candidates(bundled_lmp_dir, "bundled_lmp")
        + _dir_candidates(templates_dir, "templates")
    )
    if reference_load.is_file():
        candidates.append(
            {
                "path": str(reference_load),
                "label": f"{reference_load.name} (bundled reference load)",
                "source": "reference",
                "kind": "load",
            }
        )
    return {"candidates": candidates}


def list_template_help(templates_dir: Path) -> list[dict]:
    """One-line schema summaries for the launch page's Templates help block.

    Reads each template's column header live off disk (:func:`_peek_header_columns`)
    rather than embedding a copy of the example rows in this module — the
    summary always reflects whatever ``data/templates/`` actually contains.
    """
    if not templates_dir.is_dir():
        return []
    out = []
    for p in sorted(templates_dir.iterdir()):
        if not p.is_file() or p.suffix != ".csv":
            continue
        cols = _peek_header_columns(p)
        out.append(
            {
                "path": str(p),
                "label": _TEMPLATE_LABELS.get(p.name, p.name),
                "columns": ", ".join(cols) if cols else "(unreadable)",
            }
        )
    return out


# --- Past-runs browser (HP-03 §A) -----------------------------------------

#: Every finished run writes one ``<iso>_run_metadata.json`` per ISO
#: (outputs.py); an ``--all-isos`` batch writes several into the same
#: run_id directory.
_RUN_METADATA_GLOB = "*_run_metadata.json"


def _scan_run_dir(run_dir: Path) -> dict:
    """One past-runs-browser row for ``run_dir`` — never raises.

    A missing/corrupt/incomplete metadata file (a hand-edited file, a
    truncated write, a directory this launcher never created) shows up as a
    flagged row (``"ok": False``) instead of a traceback — the browser must
    survive any ``results/`` directory, not just ones it wrote itself.
    """
    run_id = run_dir.name
    try:
        mtime = run_dir.stat().st_mtime
    except OSError:
        mtime = 0.0
    report_path = run_dir / "report.html"
    report_url = f"/reports/{run_id}/report.html" if report_path.is_file() else None

    meta_files = sorted(run_dir.glob(_RUN_METADATA_GLOB))
    if not meta_files:
        return {
            "run_id": run_id,
            "ok": False,
            "flag": "no run metadata found",
            "mtime": mtime,
            "report_url": report_url,
        }

    isos: list[str] = []
    modes: set[str] = set()
    lmp_kinds: set[str] = set()
    statuses: list[str] = []
    setpoints: set = set()
    for mf in meta_files:
        try:
            meta = json.loads(mf.read_text())
        except (OSError, json.JSONDecodeError):
            return {
                "run_id": run_id,
                "ok": False,
                "flag": f"unreadable metadata ({mf.name})",
                "mtime": mtime,
                "report_url": report_url,
            }
        if not isinstance(meta, dict) or "iso" not in meta or "solves" not in meta:
            return {
                "run_id": run_id,
                "ok": False,
                "flag": f"incomplete metadata ({mf.name})",
                "mtime": mtime,
                "report_url": report_url,
            }
        isos.append(str(meta.get("iso")))
        modes.add(str(meta.get("mode", "?")))
        # lmp_kind predates HP-01 in the two pre-existing committed bundles —
        # absent, not malformed; label it rather than flagging the row.
        lmp_kinds.add(str(meta.get("lmp_kind", "unknown")))
        for s in meta.get("solves") or []:
            if isinstance(s, dict):
                statuses.append(str(s.get("status", "?")))
                if "setpoint" in s:
                    setpoints.add(s["setpoint"])

    return {
        "run_id": run_id,
        "ok": True,
        "isos": isos,
        "mode": " / ".join(sorted(modes)),
        "lmp_kind": " / ".join(sorted(lmp_kinds)),
        "setpoints": sorted(setpoints),
        "n_optimal": sum(1 for s in statuses if s == "Optimal"),
        "n_solves": len(statuses),
        "mtime": mtime,
        "report_url": report_url,
    }


def list_past_runs(results_dir: Path) -> list[dict]:
    """Every ``results/<run_id>/`` row for the past-runs browser, newest
    first (by directory mtime). ``<run_id>.tmp`` staging directories (a
    run's scratch sibling before the atomic-ish publish swap, ``cli.py``)
    are in-flight or crashed, not a finished run, and are skipped."""
    if not results_dir.is_dir():
        return []
    rows = [
        _scan_run_dir(d)
        for d in results_dir.iterdir()
        if d.is_dir() and not d.name.endswith(".tmp")
    ]
    rows.sort(key=lambda r: r["mtime"], reverse=True)
    return rows


# --- Persistent run log (HP-03 §B) ----------------------------------------


class RunLog:
    """Thread-safe append-only run history (``launcher/run_log.jsonl``).

    Machine-local state like ``saved_configs.json``/``last_used.json``
    (gitignored) — one JSON line per *finished* run (queue execution itself
    stays sequential and unchanged; this only records history alongside
    it).
    """

    def __init__(self, state_dir: Path):
        self.path = state_dir / RUN_LOG_FILENAME
        self.lock = threading.Lock()

    def append(self, entry: dict) -> None:
        line = json.dumps(entry, sort_keys=True)
        with self.lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def tail(self, n: int) -> list[dict]:
        """Return up to the last ``n`` well-formed entries, oldest first.

        A corrupt line (partial write, hand-edited file) is skipped rather
        than raising — the run log is a UI convenience, never a crash
        surface.
        """
        with self.lock:
            if not self.path.exists():
                return []
            try:
                text = self.path.read_text(encoding="utf-8")
            except OSError:
                return []
        entries = []
        for line in text.splitlines()[-n:] if n > 0 else []:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries


# --- Saved-config / last-used persistence --------------------------------


class ConfigStore:
    """Thread-safe JSON persistence for saved configs + last-used values.

    Both files live under ``state_dir`` (default ``launcher/``, gitignored):
    ``saved_configs.json`` is a ``{name: params}`` map the side panel lists;
    ``last_used.json`` holds the single most-recently-submitted run's params,
    used to pre-fill the form on the next page load.
    """

    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.lock = threading.Lock()
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _read(self, filename: str) -> dict:
        path = self.state_dir / filename
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _write(self, filename: str, data: dict) -> None:
        path = self.state_dir / filename
        path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def saved_configs(self) -> dict:
        with self.lock:
            return self._read(SAVED_CONFIGS_FILENAME)

    def save_config(self, name: str, params: dict) -> None:
        if not _SAFE_NAME_RE.fullmatch(name):
            raise ValueError(
                f"invalid config name {name!r}: use letters, digits, '.', '_' "
                "or '-', starting with a letter or digit"
            )
        with self.lock:
            configs = self._read(SAVED_CONFIGS_FILENAME)
            configs[name] = params
            self._write(SAVED_CONFIGS_FILENAME, configs)

    def delete_config(self, name: str) -> None:
        with self.lock:
            configs = self._read(SAVED_CONFIGS_FILENAME)
            configs.pop(name, None)
            self._write(SAVED_CONFIGS_FILENAME, configs)

    def last_used(self) -> dict:
        with self.lock:
            return self._read(LAST_USED_FILENAME)

    def record_last_used(self, params: dict) -> None:
        with self.lock:
            self._write(LAST_USED_FILENAME, params)


# --- Run validation -------------------------------------------------------


def validate_run_payload(payload: dict) -> tuple[dict | None, str | None]:
    """Validate one queued run's raw JSON payload into safe run kwargs.

    Returns ``(kwargs, None)`` on success or ``(None, message)`` with a
    friendly, single-line error message (bad iso/mode, missing file, unsafe
    run id, ...) — this is the pre-flight check the ``/api/run`` endpoint
    runs before ever touching a background thread, so validation errors never
    look like a crashed run. Re-uses :class:`PortfolioConfig`'s own
    ``__post_init__`` validation for range/type rules rather than duplicating
    them, and :func:`lce_portfolio.cli.validate_run_id` for run-id safety.
    """
    if not isinstance(payload, dict):
        # A string/number/list entry in the "runs" array reached here before
        # this guard as a raw AttributeError traceback (review finding LN-1).
        return None, "each queued run must be a JSON object"
    try:
        iso = str(payload.get("iso", "")).strip()
        if iso not in KNOWN_ISOS:
            raise ValueError(
                f"unknown iso {iso!r}; must be one of {', '.join(KNOWN_ISOS)}"
            )
        mode = str(payload.get("mode", DEFAULT_MODE)).strip()
        if mode not in KNOWN_MODES:
            raise ValueError(f"unknown mode {mode!r}; must be one of {KNOWN_MODES}")
        lcoe_sensitivity = str(
            payload.get("lcoe_sensitivity", DEFAULT_LCOE_SENSITIVITY)
        ).strip()

        # Only the setpoint list the chosen mode actually sweeps is parsed
        # from the request; the other stays at the library default so an
        # empty/stale field in the inactive half of the form never fails
        # PortfolioConfig's non-empty/range validation.
        if mode == "premium_cap":
            premium_deltas = parse_float_list(
                payload.get("premium_deltas", DEFAULT_PREMIUM_DELTAS),
                "premium_deltas",
            )
            matching_targets = DEFAULT_MATCHING_TARGETS
        else:
            matching_targets = parse_float_list(
                payload.get("matching_targets", DEFAULT_MATCHING_TARGETS),
                "matching_targets",
            )
            premium_deltas = DEFAULT_PREMIUM_DELTAS

        load_file = str(payload.get("load_file", "")).strip()
        lmp_file = str(payload.get("lmp_file", "")).strip()
        if not load_file:
            raise ValueError("load file path is required")
        if not lmp_file:
            raise ValueError("LMP file path is required")
        if not Path(load_file).exists():
            raise ValueError(f"load file not found: {load_file}")
        if not Path(lmp_file).exists():
            raise ValueError(f"LMP file not found: {lmp_file}")

        run_id_raw = str(payload.get("run_id") or "").strip()
        run_id_auto = not run_id_raw
        run_id = (
            cli.compose_run_id([iso], mode)
            if run_id_auto
            else cli.validate_run_id(run_id_raw)
        )

        open_report_when_done = bool(
            payload.get("open_report_when_done", DEFAULT_OPEN_REPORT_WHEN_DONE)
        )

        # Reuse PortfolioConfig.__post_init__ for the range/type rules
        # (mode/lcoe_sensitivity/premium_deltas/matching_targets) rather than
        # re-implementing them here.
        PortfolioConfig(
            iso=iso,
            mode=mode,
            premium_deltas=premium_deltas,
            matching_targets=matching_targets,
            lcoe_sensitivity=lcoe_sensitivity,
            load_file=load_file,
            lmp_file=lmp_file,
        )
    except ValueError as exc:
        return None, str(exc)

    return (
        {
            "iso": iso,
            "mode": mode,
            "premium_deltas": premium_deltas,
            "matching_targets": matching_targets,
            "lcoe_sensitivity": lcoe_sensitivity,
            "load_file": load_file,
            "lmp_file": lmp_file,
            "run_id": run_id,
            "run_id_auto": run_id_auto,
            "open_report_when_done": open_report_when_done,
        },
        None,
    )


def dedupe_run_ids(validated: list[dict]) -> str | None:
    """Give every run in one submitted batch a distinct results directory.

    ``compose_run_id`` stamps to whole seconds, so two blank-run-id runs of
    the same ISO/mode queued in one submit collide — and ``results/<run-id>/``
    is overwritten on re-use, so the later run silently destroyed the earlier
    one's results mid-batch (review finding LN-3). Auto-composed duplicates
    get a ``-2``/``-3`` suffix; explicitly-typed duplicates are a user mistake
    and return a friendly error message instead. Mutates ``validated`` in
    place; returns ``None`` when all ids are (made) unique.
    """
    seen: set[str] = set()
    for kwargs in validated:
        run_id = kwargs["run_id"]
        if run_id in seen:
            if not kwargs["run_id_auto"]:
                return (
                    f"duplicate run id {run_id!r}: give each queued run a "
                    "distinct run id (or leave the field blank)"
                )
            n = 2
            while f"{run_id}-{n}" in seen:
                n += 1
            run_id = f"{run_id}-{n}"
            kwargs["run_id"] = run_id
        seen.add(run_id)
    return None


def build_argv(run_kwargs: dict) -> list[str]:
    """Compose the ``lce_portfolio.cli.main`` argv for one validated run.

    Always passes ``--results`` (persists into the results store the
    launcher serves reports from) — reuses the existing CLI path end to end,
    never forks the solve logic (ADR 0016 §2).
    """
    argv = [
        "--iso",
        run_kwargs["iso"],
        "--load",
        run_kwargs["load_file"],
        "--lmp",
        run_kwargs["lmp_file"],
        "--sensitivity",
        run_kwargs["lcoe_sensitivity"],
        "--results",
        "--run-id",
        run_kwargs["run_id"],
    ]
    if run_kwargs["mode"] == "matching_target":
        argv += ["--targets", *(str(t) for t in run_kwargs["matching_targets"])]
    else:
        argv += ["--deltas", *(str(d) for d in run_kwargs["premium_deltas"])]
    return argv


# --- Run queue / execution ------------------------------------------------


@dataclass
class RunStatus:
    """Live status of one queued run, as reported by ``GET /api/status``."""

    run_id: str
    iso: str
    mode: str
    state: str = "queued"  # queued -> running -> done | error
    message: str = ""
    report_url: str | None = None

    def to_json(self) -> dict:
        return {
            "run_id": self.run_id,
            "iso": self.iso,
            "mode": self.mode,
            "state": self.state,
            "message": self.message,
            "report_url": self.report_url,
        }


class LauncherState:
    """Shared server state: config store, run queue, one worker thread.

    A single daemon worker thread drains ``jobs`` sequentially — regardless
    of how many HTTP requests submit batches — so LP solves never overlap
    (ADR 0016 §2: "one LP solve at a time").
    """

    def __init__(
        self,
        *,
        state_dir: Path,
        results_dir: Path,
        open_browser: bool,
        inputs_dir: Path = DEFAULT_INPUTS_DIR,
        bundled_lmp_dir: Path = DEFAULT_BUNDLED_LMP_DIR,
        templates_dir: Path = DEFAULT_TEMPLATES_DIR,
        reference_load: Path = DEFAULT_REFERENCE_LOAD,
    ):
        self.config_store = ConfigStore(state_dir)
        self.run_log = RunLog(state_dir)
        self.results_dir = results_dir
        self.inputs_dir = inputs_dir
        self.bundled_lmp_dir = bundled_lmp_dir
        self.templates_dir = templates_dir
        self.reference_load = reference_load
        self.open_browser = open_browser
        self.lock = threading.Lock()
        self.batches: dict[str, list[RunStatus]] = {}
        self._batch_counter = 0
        self.jobs: Queue[tuple[str, int, dict]] = Queue()
        self.worker = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker.start()

    def enqueue_batch(self, runs: list[dict]) -> str:
        with self.lock:
            self._batch_counter += 1
            batch_id = f"batch{self._batch_counter}"
            self.batches[batch_id] = [
                RunStatus(run_id=r["run_id"], iso=r["iso"], mode=r["mode"])
                for r in runs
            ]
        for idx, run_kwargs in enumerate(runs):
            self.jobs.put((batch_id, idx, run_kwargs))
        return batch_id

    def batch_status(self, batch_id: str) -> list[dict] | None:
        with self.lock:
            statuses = self.batches.get(batch_id)
            if statuses is None:
                return None
            return [s.to_json() for s in statuses]

    def _worker_loop(self) -> None:
        while True:
            batch_id, idx, run_kwargs = self.jobs.get()
            try:
                self._execute(batch_id, idx, run_kwargs)
            finally:
                self.jobs.task_done()

    def _set_state(self, batch_id: str, idx: int, **changes) -> None:
        with self.lock:
            status = self.batches[batch_id][idx]
            for key, value in changes.items():
                setattr(status, key, value)

    def _execute(self, batch_id: str, idx: int, run_kwargs: dict) -> None:
        """Run one queued config through the existing CLI, in-process.

        HiGHS logging is already silenced (``lp.py``'s ``output_flag``), and
        the CLI's own ``print``s are captured rather than reaching this
        server's console mid-solve; a validation error from ``cli.main``
        surfaces as its own ``error: ...`` message (never a traceback — the
        CLI already guarantees that). Any *unexpected* exception is caught
        here too (error discipline, ADR 0016 §5): the traceback is printed to
        the real server console for debugging, but the browser only ever
        sees a short friendly message.
        """
        self._set_state(batch_id, idx, state="running")
        started = time.monotonic()
        argv = build_argv(run_kwargs)
        stdout_buf, stderr_buf = io.StringIO(), io.StringIO()
        try:
            with (
                contextlib.redirect_stdout(stdout_buf),
                contextlib.redirect_stderr(stderr_buf),
            ):
                rc = cli.main(argv)
        # SystemExit included (review finding LN-9): it is not an Exception,
        # and an uncaught one (e.g. argparse's parser.error) would kill the
        # single worker thread silently, leaving every later queued run stuck
        # at "queued" until the server is restarted.
        except (Exception, SystemExit):  # noqa: BLE001 - never propagate raw
            traceback.print_exc()
            message = "internal error running the solve — see server console"
            self._set_state(batch_id, idx, state="error", message=message)
            self._append_run_log(run_kwargs, "error", message, started)
            return

        if rc == 0:
            run_id = run_kwargs["run_id"]
            report = self.results_dir / run_id / "report.html"
            report_url = f"/reports/{run_id}/report.html" if report.exists() else None
            self._set_state(batch_id, idx, state="done", report_url=report_url)
            self._append_run_log(run_kwargs, "done", "", started)
            if (
                self.open_browser
                and run_kwargs.get("open_report_when_done", True)
                and report.exists()
            ):
                webbrowser.open(report.resolve().as_uri())
        else:
            message = stderr_buf.getvalue().strip() or "run failed (no message)"
            self._set_state(batch_id, idx, state="error", message=message)
            self._append_run_log(run_kwargs, "error", message, started)

    def _append_run_log(
        self, run_kwargs: dict, state: str, message: str, started: float
    ) -> None:
        """Append one finished run's outcome to ``launcher/run_log.jsonl``
        (HP-03 §B) — queue behavior itself is unaffected, this only records
        history alongside it."""
        self.run_log.append(
            {
                "run_id": run_kwargs["run_id"],
                "iso": run_kwargs["iso"],
                "mode": run_kwargs["mode"],
                "lcoe_sensitivity": run_kwargs.get("lcoe_sensitivity"),
                "status": state,
                "wall_time_seconds": round(time.monotonic() - started, 3),
                "error": message or None,
                "finished_at": time.time(),
            }
        )


# --- HTML launch page ------------------------------------------------------

# Palette mirrors the ADR 0014 report renderer (report.py) so the launch page
# and the report it opens read as one system.
_INK = "#0b0b0b"
_INK_2 = "#52514e"
_MUTED = "#898781"
_SURFACE = "#fcfcfb"
_GRID = "#e1e0d9"
_ACCENT = "#2a78d6"
_CRITICAL = "#d03b3b"
_OK = "#1baf7a"


def _safe_json_for_script(obj) -> str:
    """JSON-encode ``obj`` for embedding in a ``<script>`` tag safely.

    Escapes ``</`` so a string value (e.g. a saved-config name) can never
    prematurely close the surrounding script element.
    """
    return json.dumps(obj).replace("</", "<\\/")


def render_index(context: dict) -> str:
    """Render the self-contained HTML launch page (ADR 0016 §2).

    Inline CSS/JS only, no CDN, no external fetch. ``context`` carries the
    known parameter domains, computed defaults, saved configs, and last-used
    values; the page's JS reads it from an embedded JSON blob to pre-fill the
    form, render the saved-config list, and drive the run queue / status
    polling against ``/api/run`` and ``/api/status``.
    """
    ctx_json = _safe_json_for_script(context)
    title = html.escape(f"LCE Portfolio Launcher v{__version__}")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {{
    --ink: {_INK}; --ink2: {_INK_2}; --muted: {_MUTED};
    --surface: {_SURFACE}; --grid: {_GRID}; --accent: {_ACCENT};
    --critical: {_CRITICAL}; --ok: {_OK};
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; font: 14px/1.5 -apple-system, "Segoe UI", Helvetica, Arial, sans-serif;
    color: var(--ink); background: var(--surface);
  }}
  header {{ padding: 20px 28px 12px; border-bottom: 1px solid var(--grid); }}
  header h1 {{ margin: 0 0 4px; font-size: 20px; }}
  header p {{ margin: 0; color: var(--ink2); }}
  main {{ display: flex; gap: 24px; padding: 24px 28px; align-items: flex-start; }}
  .panel {{
    background: #fff; border: 1px solid var(--grid); border-radius: 8px;
    padding: 18px 20px;
  }}
  #form-panel {{ flex: 2 1 520px; }}
  #side-panel {{ flex: 1 1 320px; }}
  h2 {{ font-size: 15px; margin: 0 0 12px; }}
  label {{ display: block; margin: 12px 0 4px; font-weight: 600; color: var(--ink2); }}
  input[type=text], input[type=number], select {{
    width: 100%; padding: 6px 8px; border: 1px solid var(--grid); border-radius: 4px;
    font: inherit; color: var(--ink);
  }}
  .row {{ display: flex; gap: 12px; }}
  .row > div {{ flex: 1; }}
  .hint {{ color: var(--muted); font-size: 12px; margin-top: 2px; }}
  .synthetic-flag {{
    display: inline-block; margin-top: 4px; padding: 2px 6px; border-radius: 4px;
    background: #fff3e0; color: #9a5b00; font-size: 11px; font-weight: 600;
  }}
  .flatprice-flag {{
    display: inline-block; margin-top: 4px; padding: 2px 6px; border-radius: 4px;
    background: #e7f0fb; color: #1a4d8f; font-size: 11px; font-weight: 600;
  }}
  select.file-select {{ margin-bottom: 6px; }}
  .full-width-panel {{ margin: 0 28px 24px; }}
  .panel-toolbar {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
  .panel-toolbar h2 {{ margin: 0; }}
  .flag-row {{ color: var(--critical); font-weight: 600; }}
  #templates-list {{ list-style: none; margin: 8px 0; padding: 0; }}
  #templates-list li {{ margin-bottom: 10px; }}
  #templates-list code {{ font-size: 12px; color: var(--ink2); }}
  button {{
    font: inherit; padding: 7px 14px; border-radius: 5px; border: 1px solid var(--grid);
    background: #fff; cursor: pointer;
  }}
  button.primary {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  button.danger {{ color: var(--critical); }}
  #queue-list, #saved-list {{ list-style: none; margin: 8px 0; padding: 0; }}
  #queue-list li, #saved-list li {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 6px 8px; border: 1px solid var(--grid); border-radius: 4px; margin-bottom: 6px;
    font-size: 13px;
  }}
  #status-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }}
  #status-table th, #status-table td {{
    text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--grid);
  }}
  .state-done {{ color: var(--ok); font-weight: 600; }}
  .state-error {{ color: var(--critical); font-weight: 600; }}
  .state-running {{ color: var(--accent); font-weight: 600; }}
  #error-banner {{
    display: none; background: #fdeaea; color: var(--critical); border: 1px solid var(--critical);
    border-radius: 6px; padding: 10px 14px; margin-bottom: 14px; white-space: pre-wrap;
  }}
  .checkbox-row {{ display: flex; align-items: center; gap: 8px; margin-top: 14px; }}
  .checkbox-row input {{ width: auto; }}
  fieldset {{ border: 1px solid var(--grid); border-radius: 6px; margin-top: 14px; padding: 10px 14px; }}
  legend {{ padding: 0 6px; color: var(--ink2); font-weight: 600; font-size: 13px; }}
</style>
</head>
<body>
<header>
  <h1>Scope 2 Hourly LCE Portfolio &mdash; Launcher</h1>
  <p>Configure a run, queue several, submit &mdash; runs solve one at a time and open their report when done.</p>
</header>
<main>
  <section class="panel" id="form-panel">
    <h2>Run configuration</h2>
    <div id="error-banner"></div>

    <label for="f-iso">ISO</label>
    <select id="f-iso"></select>

    <label for="f-mode">Mode</label>
    <select id="f-mode">
      <option value="premium_cap">Premium cap (maximize matching)</option>
      <option value="matching_target">Matching target (minimize premium)</option>
    </select>

    <div id="premium-deltas-field">
      <label for="f-premium-deltas">Premium deltas ($/MWh, comma-separated)</label>
      <input type="text" id="f-premium-deltas">
    </div>
    <div id="matching-targets-field">
      <label for="f-matching-targets">Matching targets (0&ndash;1, comma-separated)</label>
      <input type="text" id="f-matching-targets">
    </div>

    <label for="f-sensitivity">LCOE sensitivity</label>
    <select id="f-sensitivity">
      <option value="low">Low</option>
      <option value="mid">Mid</option>
      <option value="high">High</option>
    </select>

    <label for="f-load">Load file path</label>
    <select id="f-load-select" class="file-select">
      <option value="">&mdash; pick a bundled/available file &mdash;</option>
    </select>
    <input type="text" id="f-load">
    <div class="hint">Default: bundled reference load (100 MW stylized facility). Pick from the dropdown or type any path.</div>

    <label for="f-lmp">LMP file path</label>
    <select id="f-lmp-select" class="file-select">
      <option value="">&mdash; pick a bundled/available file &mdash;</option>
    </select>
    <input type="text" id="f-lmp">
    <div class="hint" id="lmp-hint"></div>
    <div class="hint" id="lmp-flatprice-hint"></div>

    <label for="f-run-id">Run ID</label>
    <input type="text" id="f-run-id" placeholder="(auto-generated if left blank)">

    <div class="checkbox-row">
      <input type="checkbox" id="f-open-report" checked>
      <label for="f-open-report" style="margin:0;">Open report when done</label>
    </div>

    <div style="margin-top:16px; display:flex; gap:10px;">
      <button class="primary" id="btn-add-queue">Add to queue</button>
      <button id="btn-submit-queue">Submit queue</button>
    </div>

    <fieldset>
      <legend>Queued runs</legend>
      <ul id="queue-list"></ul>
    </fieldset>

    <fieldset>
      <legend>Status</legend>
      <table id="status-table">
        <thead><tr><th>Run ID</th><th>ISO</th><th>State</th><th>Detail</th></tr></thead>
        <tbody id="status-body"></tbody>
      </table>
    </fieldset>
  </section>

  <section class="panel" id="side-panel">
    <h2>Saved configurations</h2>
    <ul id="saved-list"></ul>
    <label for="f-save-name">Save current form as&hellip;</label>
    <input type="text" id="f-save-name" placeholder="my_config">
    <button id="btn-save-config" style="margin-top:8px;">Save</button>
  </section>
</main>

<section class="panel full-width-panel" id="templates-panel">
  <h2>Templates</h2>
  <p class="hint">Fillable input-template schemas (<code>data/templates/</code>) &mdash; read live off disk, never copied here.</p>
  <ul id="templates-list"></ul>
</section>

<section class="panel full-width-panel" id="runs-panel">
  <div class="panel-toolbar">
    <h2>Past runs</h2>
    <button id="btn-refresh-runs">Refresh</button>
  </div>
  <table id="runs-table">
    <thead>
      <tr>
        <th>Run ID</th><th>ISO(s)</th><th>Mode</th><th>Setpoints</th>
        <th>LMP kind</th><th>Timestamp</th><th>Status</th><th>Report</th>
      </tr>
    </thead>
    <tbody id="runs-body"></tbody>
  </table>
</section>

<section class="panel full-width-panel" id="runlog-panel">
  <div class="panel-toolbar">
    <h2>Run log</h2>
    <button id="btn-refresh-runlog">Refresh</button>
  </div>
  <table id="runlog-table">
    <thead>
      <tr>
        <th>Run ID</th><th>ISO</th><th>Mode</th><th>Status</th>
        <th>Wall time (s)</th><th>Finished</th><th>Error</th>
      </tr>
    </thead>
    <tbody id="runlog-body"></tbody>
  </table>
</section>

<footer><p>Docs: <a href="../docs/site/index.html">how it works</a></p></footer>
<script>
const CTX = {ctx_json};

function $(id) {{ return document.getElementById(id); }}

function showError(msg) {{
  const el = $('error-banner');
  if (!msg) {{ el.style.display = 'none'; el.textContent = ''; return; }}
  el.style.display = 'block';
  el.textContent = msg;
}}

function currentForm() {{
  return {{
    iso: $('f-iso').value,
    mode: $('f-mode').value,
    premium_deltas: $('f-premium-deltas').value,
    matching_targets: $('f-matching-targets').value,
    lcoe_sensitivity: $('f-sensitivity').value,
    load_file: $('f-load').value,
    lmp_file: $('f-lmp').value,
    run_id: $('f-run-id').value,
    open_report_when_done: $('f-open-report').checked,
    lmp_kind_hint: selectedLmpKind,
  }};
}}

function applyForm(cfg) {{
  if (!cfg) return;
  if (cfg.iso) $('f-iso').value = cfg.iso;
  if (cfg.mode) $('f-mode').value = cfg.mode;
  if (cfg.premium_deltas !== undefined) $('f-premium-deltas').value =
    Array.isArray(cfg.premium_deltas) ? cfg.premium_deltas.join(', ') : cfg.premium_deltas;
  if (cfg.matching_targets !== undefined) $('f-matching-targets').value =
    Array.isArray(cfg.matching_targets) ? cfg.matching_targets.join(', ') : cfg.matching_targets;
  if (cfg.lcoe_sensitivity) $('f-sensitivity').value = cfg.lcoe_sensitivity;
  if (cfg.load_file) $('f-load').value = cfg.load_file;
  if (cfg.lmp_file !== undefined) $('f-lmp').value = cfg.lmp_file;
  if (cfg.run_id !== undefined) $('f-run-id').value = cfg.run_id;
  if (cfg.open_report_when_done !== undefined) $('f-open-report').checked = !!cfg.open_report_when_done;
  selectedLmpKind = cfg.lmp_kind_hint !== undefined ? cfg.lmp_kind_hint : selectedLmpKind;
  setFlatPriceBadge(selectedLmpKind === 'annual_average_flat');
  updateModeVisibility();
}}

function updateModeVisibility() {{
  const isPremium = $('f-mode').value === 'premium_cap';
  $('premium-deltas-field').style.display = isPremium ? 'block' : 'none';
  $('matching-targets-field').style.display = isPremium ? 'none' : 'block';
}}

let queue = [];
let selectedLmpKind = CTX.defaults.lmp_kind || null;
let inputCandidates = [];

function setFlatPriceBadge(isFlat) {{
  const el = $('lmp-flatprice-hint');
  el.innerHTML = isFlat
    ? '<span class="flatprice-flag">FLAT-PRICE</span> annual-average LMP — hourly price shape excluded from the frontier.'
    : '';
}}

function populateFileSelect(selectEl, candidates) {{
  Array.from(selectEl.querySelectorAll('option')).slice(1).forEach((o) => o.remove());
  candidates.forEach((c) => {{
    const opt = document.createElement('option');
    opt.value = c.path;
    let label = c.label + ' (' + c.source + ')';
    if (c.kind === 'annual_average_flat') label += ' [FLAT-PRICE]';
    opt.textContent = label;
    opt.dataset.kind = c.kind;
    selectEl.appendChild(opt);
  }});
}}

async function loadInputCandidates() {{
  let data;
  try {{
    const resp = await fetch('/api/input-files');
    data = await resp.json();
  }} catch (err) {{
    return;
  }}
  inputCandidates = data.candidates || [];
  populateFileSelect($('f-load-select'), inputCandidates);
  populateFileSelect($('f-lmp-select'), inputCandidates);
}}

async function loadTemplatesHelp() {{
  let data;
  try {{
    const resp = await fetch('/api/templates-help');
    data = await resp.json();
  }} catch (err) {{
    return;
  }}
  const ul = $('templates-list');
  ul.innerHTML = '';
  (data.templates || []).forEach((t) => {{
    const li = document.createElement('li');
    const strong = document.createElement('strong');
    strong.textContent = t.label;
    const code = document.createElement('code');
    code.textContent = ' ' + t.path;
    const cols = document.createElement('div');
    cols.className = 'hint';
    cols.textContent = 'columns: ' + t.columns;
    li.appendChild(strong);
    li.appendChild(document.createElement('br'));
    li.appendChild(code);
    li.appendChild(cols);
    ul.appendChild(li);
  }});
}}

function fmtTimestamp(epochSeconds) {{
  if (!epochSeconds) return '';
  return new Date(epochSeconds * 1000).toLocaleString();
}}

async function loadPastRuns() {{
  let data;
  try {{
    const resp = await fetch('/api/runs');
    data = await resp.json();
  }} catch (err) {{
    return;
  }}
  const body = $('runs-body');
  body.innerHTML = '';
  (data.runs || []).forEach((r) => {{
    const tr = document.createElement('tr');
    if (!r.ok) {{
      const td = document.createElement('td');
      td.colSpan = 8;
      td.className = 'flag-row';
      td.textContent = 'run_id=' + r.run_id + ': ' + r.flag;
      tr.appendChild(td);
      body.appendChild(tr);
      return;
    }}
    const cells = [
      r.run_id,
      (r.isos || []).join(', '),
      r.mode,
      (r.setpoints || []).join(', '),
      r.lmp_kind,
      fmtTimestamp(r.mtime),
      r.n_optimal + '/' + r.n_solves + ' optimal',
    ];
    cells.forEach((text) => {{
      const td = document.createElement('td');
      td.textContent = text;
      tr.appendChild(td);
    }});
    const tdReport = document.createElement('td');
    if (r.report_url) {{
      const a = document.createElement('a');
      a.href = r.report_url;
      a.target = '_blank';
      a.textContent = 'report';
      tdReport.appendChild(a);
    }}
    tr.appendChild(tdReport);
    body.appendChild(tr);
  }});
}}

async function loadRunLog() {{
  let data;
  try {{
    const resp = await fetch('/api/run-log?n=20');
    data = await resp.json();
  }} catch (err) {{
    return;
  }}
  const body = $('runlog-body');
  body.innerHTML = '';
  (data.entries || []).slice().reverse().forEach((e) => {{
    const tr = document.createElement('tr');
    const cells = [
      e.run_id, e.iso, e.mode, e.status,
      e.wall_time_seconds != null ? String(e.wall_time_seconds) : '',
      fmtTimestamp(e.finished_at),
      e.error || '',
    ];
    cells.forEach((text) => {{
      const td = document.createElement('td');
      td.textContent = text;
      tr.appendChild(td);
    }});
    body.appendChild(tr);
  }});
}}

function renderQueue() {{
  const ul = $('queue-list');
  ul.innerHTML = '';
  queue.forEach((run, i) => {{
    const li = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = `${{run.iso}} / ${{run.mode}} / run_id=${{run.run_id || '(auto)'}}${{run.lmp_kind_hint === 'annual_average_flat' ? ' [FLAT-PRICE]' : ''}}`;
    const btn = document.createElement('button');
    btn.textContent = 'Remove';
    btn.className = 'danger';
    btn.onclick = () => {{ queue.splice(i, 1); renderQueue(); }};
    li.appendChild(label);
    li.appendChild(btn);
    ul.appendChild(li);
  }});
}}

function renderSaved(savedConfigs) {{
  const ul = $('saved-list');
  ul.innerHTML = '';
  Object.keys(savedConfigs).sort().forEach((name) => {{
    const li = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = name;
    const btn = document.createElement('button');
    btn.textContent = 'Load';
    btn.onclick = () => applyForm(savedConfigs[name]);
    li.appendChild(label);
    li.appendChild(btn);
    ul.appendChild(li);
  }});
}}

let statuses = {{}};
let pollTimer = null;

function renderStatus() {{
  const body = $('status-body');
  body.innerHTML = '';
  // Built via textContent, never innerHTML: the error detail echoes solver
  // stderr, which can carry text from user-supplied input files.
  Object.values(statuses).flat().forEach((s) => {{
    const tr = document.createElement('tr');
    const cells = [s.run_id, s.iso];
    cells.forEach((text) => {{
      const td = document.createElement('td');
      td.textContent = text;
      tr.appendChild(td);
    }});
    const tdState = document.createElement('td');
    tdState.className = 'state-' + s.state;
    tdState.textContent = s.state;
    tr.appendChild(tdState);
    const tdDetail = document.createElement('td');
    if (s.state === 'done' && s.report_url) {{
      const a = document.createElement('a');
      a.href = s.report_url;
      a.target = '_blank';
      a.textContent = 'report';
      tdDetail.appendChild(a);
    }} else {{
      tdDetail.textContent = s.state === 'done' ? 'done' : (s.message || '');
    }}
    tr.appendChild(tdDetail);
    body.appendChild(tr);
  }});
}}

async function pollBatch(batchId) {{
  let data;
  try {{
    const resp = await fetch(`/api/status?batch=${{encodeURIComponent(batchId)}}`);
    if (!resp.ok) return;
    data = await resp.json();
  }} catch (err) {{
    if (pollTimer) {{ clearInterval(pollTimer); pollTimer = null; }}
    showError('lost contact with the launcher server — is it still running?');
    return;
  }}
  statuses[batchId] = data.runs;
  renderStatus();
  const pending = data.runs.some((r) => r.state === 'queued' || r.state === 'running');
  if (!pending && pollTimer) {{ clearInterval(pollTimer); pollTimer = null; }}
}}

$('f-mode').addEventListener('change', updateModeVisibility);

$('f-load-select').addEventListener('change', () => {{
  const path = $('f-load-select').value;
  if (path) $('f-load').value = path;
}});

$('f-lmp-select').addEventListener('change', () => {{
  const sel = $('f-lmp-select');
  const opt = sel.selectedOptions[0];
  const path = sel.value;
  if (path) $('f-lmp').value = path;
  selectedLmpKind = (opt && path) ? opt.dataset.kind : null;
  setFlatPriceBadge(selectedLmpKind === 'annual_average_flat');
}});

$('btn-refresh-runs').addEventListener('click', loadPastRuns);
$('btn-refresh-runlog').addEventListener('click', loadRunLog);

$('btn-add-queue').addEventListener('click', () => {{
  showError(null);
  queue.push(currentForm());
  renderQueue();
}});

$('btn-submit-queue').addEventListener('click', async () => {{
  showError(null);
  if (queue.length === 0) {{ queue.push(currentForm()); }}
  let resp, data;
  try {{
    resp = await fetch('/api/run', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{runs: queue}}),
    }});
    data = await resp.json();
  }} catch (err) {{
    showError('could not reach the launcher server — is it still running?');
    return;
  }}
  if (!resp.ok) {{
    showError(data.error || 'submission failed');
    return;
  }}
  queue = [];
  renderQueue();
  statuses[data.batch_id] = data.runs;
  renderStatus();
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(() => pollBatch(data.batch_id), 1000);
}});

$('btn-save-config').addEventListener('click', async () => {{
  showError(null);
  const name = $('f-save-name').value.trim();
  if (!name) {{ showError('enter a name to save this configuration'); return; }}
  let resp, data;
  try {{
    resp = await fetch('/api/save-config', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{name, params: currentForm()}}),
    }});
    data = await resp.json();
  }} catch (err) {{
    showError('could not reach the launcher server — is it still running?');
    return;
  }}
  if (!resp.ok) {{ showError(data.error || 'save failed'); return; }}
  renderSaved(data.saved_configs);
}});

// --- init ---
CTX.known_isos.forEach((iso) => {{
  const opt = document.createElement('option');
  opt.value = iso; opt.textContent = iso;
  $('f-iso').appendChild(opt);
}});
applyForm(CTX.defaults);
renderSaved(CTX.saved_configs);
if (CTX.defaults.lmp_is_synthetic) {{
  $('lmp-hint').innerHTML = 'Default resolved to a <span class="synthetic-flag">SYNTHETIC</span> stub LMP &mdash; not a priced result.';
}} else if (!CTX.defaults.lmp_file) {{
  $('lmp-hint').textContent = 'No LMP file found on disk; enter a path before submitting.';
}} else {{
  $('lmp-hint').textContent = 'Default: newest LMP export found under data/inputs/.';
}}
setFlatPriceBadge(selectedLmpKind === 'annual_average_flat');
loadInputCandidates();
loadTemplatesHelp();
loadPastRuns();
loadRunLog();
</script>
</body>
</html>
"""


# --- HTTP handler ------------------------------------------------------


def _make_handler(state: LauncherState, page_context: dict):
    """Build a request-handler class bound to this server's ``state``."""

    # ``contextlib.redirect_stderr`` in ``LauncherState._execute`` swaps
    # ``sys.stderr`` process-wide while a solve runs, so a handler thread
    # logging a request mid-solve wrote into the run's captured stderr —
    # access-log lines ended up glued onto the run's error message (review
    # finding LN-11). Grab the real console handle once, before any run can
    # redirect it.
    console_stderr = sys.stderr

    class LauncherHandler(BaseHTTPRequestHandler):
        server_version = f"lce-portfolio-launcher/{__version__}"

        def _send_bytes(self, body: bytes, content_type: str, status: int) -> None:
            try:
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # Client went away mid-response (tab closed, poll aborted):
                # one console line, not a threading traceback dump (review
                # finding LN-8; ADR 0016 §5 console discipline).
                console_stderr.write(
                    f"{self.address_string()} - - client disconnected mid-response\n"
                )

        def _send_json(self, obj: dict, status: int = 200) -> None:
            self._send_bytes(
                json.dumps(obj).encode("utf-8"),
                "application/json; charset=utf-8",
                status,
            )

        def _send_html(self, body_text: str, status: int = 200) -> None:
            self._send_bytes(
                body_text.encode("utf-8"), "text/html; charset=utf-8", status
            )

        def _read_json(self) -> dict:
            """Read the request body as a JSON object, or raise ValueError.

            Every malformed shape gets a friendly message instead of a raw
            traceback or a hung handler (review findings LN-1/LN-2): a
            non-integer Content-Length raised ValueError uncaught, a negative
            one blocked in ``rfile.read(-1)`` until the client gave up, an
            oversized one was absorbed into memory unbounded, and a JSON body
            whose top level was not an object crashed with AttributeError.
            """
            raw_length = self.headers.get("Content-Length", "0")
            try:
                length = int(raw_length)
            except ValueError:
                raise ValueError(f"invalid Content-Length {raw_length!r}") from None
            if length < 0:
                raise ValueError(f"invalid Content-Length {raw_length!r}")
            if length > MAX_REQUEST_BYTES:
                raise ValueError(
                    f"request body too large ({length} bytes; max {MAX_REQUEST_BYTES})"
                )
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                raise ValueError("malformed JSON body") from None
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def do_GET(self):  # noqa: N802 - stdlib naming
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/":
                ctx = dict(page_context)
                ctx["saved_configs"] = state.config_store.saved_configs()
                # Pre-fill from the most recent submit, re-read on every page
                # load (review finding LN-7: it was merged once at server
                # start, so a reload never showed the last-used values) — but
                # never the run id: a stale pre-filled id would silently
                # overwrite that run's results on resubmit, while a blank
                # field auto-composes a fresh one.
                defaults = dict(page_context["defaults"])
                last_used = state.config_store.last_used()
                last_used.pop("run_id", None)
                defaults.update(last_used)
                # Keep the SYNTHETIC provenance flag consistent with whatever
                # LMP path is actually pre-filled (same stem heuristic as
                # resolve_default_lmp; the flag must stay visible on stubs).
                if defaults.get("lmp_file"):
                    defaults["lmp_is_synthetic"] = str(
                        Path(defaults["lmp_file"]).stem
                    ).endswith("_dummy")
                    defaults["lmp_kind"] = classify_input_file(
                        Path(defaults["lmp_file"])
                    )
                ctx["defaults"] = defaults
                self._send_html(render_index(ctx))
            elif parsed.path == "/api/status":
                qs = urllib.parse.parse_qs(parsed.query)
                batch_id = (qs.get("batch") or [""])[0]
                runs = state.batch_status(batch_id)
                if runs is None:
                    self._send_json({"error": f"unknown batch {batch_id!r}"}, 404)
                else:
                    self._send_json({"batch_id": batch_id, "runs": runs})
            elif parsed.path == "/api/configs":
                self._send_json({"saved_configs": state.config_store.saved_configs()})
            elif parsed.path == "/api/runs":
                # HP-03 §A: every results/<run_id>/ row, newest first. Pure
                # directory scan — no user-supplied path ever reaches this,
                # so there is no traversal surface here (unlike /reports/).
                self._send_json({"runs": list_past_runs(state.results_dir)})
            elif parsed.path == "/api/run-log":
                # HP-03 §B: tail of launcher/run_log.jsonl; ?n= clamped to a
                # sane range and never allowed to raise on a bad value.
                qs = urllib.parse.parse_qs(parsed.query)
                raw_n = (qs.get("n") or ["20"])[0]
                try:
                    n = max(1, min(200, int(raw_n)))
                except ValueError:
                    n = 20
                self._send_json({"entries": state.run_log.tail(n)})
            elif parsed.path == "/api/input-files":
                # HP-03 §C: only the whitelisted directories below — no
                # query-driven path, so no arbitrary filesystem browsing.
                self._send_json(
                    list_input_candidates(
                        inputs_dir=state.inputs_dir,
                        bundled_lmp_dir=state.bundled_lmp_dir,
                        templates_dir=state.templates_dir,
                        reference_load=state.reference_load,
                    )
                )
            elif parsed.path == "/api/templates-help":
                self._send_json({"templates": list_template_help(state.templates_dir)})
            elif parsed.path.startswith("/reports/"):
                self._serve_report(parsed.path)
            else:
                self.send_error(404)

        def do_POST(self):  # noqa: N802 - stdlib naming
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path == "/api/run":
                self._handle_run()
            elif parsed.path == "/api/save-config":
                self._handle_save_config()
            else:
                self.send_error(404)

        def _handle_run(self):
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            raw_runs = payload.get("runs")
            if not isinstance(raw_runs, list) or not raw_runs:
                self._send_json({"error": "'runs' must be a non-empty list"}, 400)
                return

            validated = []
            for i, run_payload in enumerate(raw_runs):
                kwargs, error = validate_run_payload(run_payload)
                if error is not None:
                    self._send_json({"error": f"run {i + 1}: {error}"}, 400)
                    return
                validated.append(kwargs)

            error = dedupe_run_ids(validated)
            if error is not None:
                self._send_json({"error": error}, 400)
                return
            # run_id_auto is validation-internal — keep it out of the queue,
            # the status payload, and the persisted last-used values.
            for kwargs in validated:
                kwargs.pop("run_id_auto", None)

            batch_id = state.enqueue_batch(validated)
            state.config_store.record_last_used(validated[-1])
            self._send_json(
                {
                    "batch_id": batch_id,
                    "runs": state.batch_status(batch_id),
                }
            )

        def _handle_save_config(self):
            try:
                payload = self._read_json()
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            name = str(payload.get("name", "")).strip()
            params = payload.get("params")
            if not isinstance(params, dict):
                self._send_json({"error": "'params' must be an object"}, 400)
                return
            try:
                state.config_store.save_config(name, params)
            except ValueError as exc:
                self._send_json({"error": str(exc)}, 400)
                return
            self._send_json({"saved_configs": state.config_store.saved_configs()})

        def _serve_report(self, path: str):
            match = _REPORT_PATH_RE.match(path)
            if not match:
                self.send_error(404)
                return
            run_id, filename = match.groups()
            file_path = state.results_dir / run_id / filename
            if not file_path.is_file():
                self.send_error(404)
                return
            content_type = (
                "text/html; charset=utf-8"
                if filename.endswith(".html")
                else "application/json; charset=utf-8"
            )
            self._send_bytes(file_path.read_bytes(), content_type, 200)

        def log_message(self, format, *args):  # noqa: A002 - stdlib signature
            # Mirror to the real console (ADR 0016 §5's error-discipline
            # "mirrored to console") via the pre-redirect handle — writing to
            # sys.stderr here lands inside a running solve's captured stderr
            # and pollutes its error message (finding LN-11).
            console_stderr.write(
                "%s - - [%s] %s\n"
                % (self.address_string(), self.log_date_time_string(), format % args)
            )

    return LauncherHandler


# --- Page context / server bootstrap --------------------------------------


def build_page_context(*, inputs_dir: Path, reference_load: Path) -> dict:
    """Assemble the launch page's default/known-value context (ADR 0016 §3)."""
    lmp_info = resolve_default_lmp(inputs_dir)
    lmp_kind = classify_input_file(Path(lmp_info["path"])) if lmp_info["path"] else None
    return {
        "known_isos": list(KNOWN_ISOS),
        "known_modes": list(KNOWN_MODES),
        "known_sensitivities": list(KNOWN_SENSITIVITIES),
        "defaults": {
            "iso": DEFAULT_ISO,
            "mode": DEFAULT_MODE,
            "premium_deltas": _fmt_list(DEFAULT_PREMIUM_DELTAS),
            "matching_targets": _fmt_list(DEFAULT_MATCHING_TARGETS),
            "lcoe_sensitivity": DEFAULT_LCOE_SENSITIVITY,
            "load_file": str(reference_load),
            "lmp_file": lmp_info["path"] or "",
            "lmp_is_synthetic": lmp_info["is_synthetic"],
            "lmp_kind": lmp_kind,
            "run_id": "",
            "open_report_when_done": DEFAULT_OPEN_REPORT_WHEN_DONE,
        },
    }


def run_server(
    *,
    host: str = DEFAULT_HOST,
    port: int = EPHEMERAL_PORT,
    state_dir: Path = DEFAULT_STATE_DIR,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    inputs_dir: Path = DEFAULT_INPUTS_DIR,
    bundled_lmp_dir: Path = DEFAULT_BUNDLED_LMP_DIR,
    templates_dir: Path = DEFAULT_TEMPLATES_DIR,
    reference_load: Path = DEFAULT_REFERENCE_LOAD,
    open_browser: bool = True,
) -> ThreadingHTTPServer:
    """Build and start the launcher's HTTP server (does not block).

    Reassigns :data:`lce_portfolio.cli.RESULTS_ROOT` to ``results_dir`` so
    every queued run's ``--results`` output lands under it — the CLI reads
    that module attribute at call time, so this is the one integration point
    needed to make the results directory configurable without forking
    ``cli.py``. Returns the started server; call ``.serve_forever()`` (or
    manage its lifecycle) to keep it running, and ``.shutdown()``/
    ``.server_close()`` to stop it.
    """
    cli.RESULTS_ROOT = results_dir
    ensure_reference_load(reference_load)
    state_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    state = LauncherState(
        state_dir=state_dir,
        results_dir=results_dir,
        open_browser=open_browser,
        inputs_dir=inputs_dir,
        bundled_lmp_dir=bundled_lmp_dir,
        templates_dir=templates_dir,
        reference_load=reference_load,
    )
    # last-used values are merged per page load in do_GET (finding LN-7),
    # not baked in here at startup.
    context = build_page_context(inputs_dir=inputs_dir, reference_load=reference_load)

    handler_cls = _make_handler(state, context)
    server = ThreadingHTTPServer((host, port), handler_cls)
    return server


def main(argv: list[str] | None = None) -> int:
    """CLI entry point: start the server, optionally open the browser, serve.

    ``--no-open`` (ADR 0016 §5) suppresses both the initial launch-page open
    and every per-run report auto-open — tests and CI never spawn a browser.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    # No --host flag on purpose (review finding LN-5): ADR 0016 defers any
    # remote/network use of the launch page — "loopback binding is deliberate
    # and stays" — and the un-authenticated server must never be reachable
    # from another machine.
    parser.add_argument("--port", type=int, default=EPHEMERAL_PORT)
    parser.add_argument("--no-open", action="store_true", help="never open a browser")
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=DEFAULT_STATE_DIR,
        help="directory for saved_configs.json / last_used.json",
    )
    parser.add_argument(
        "--results",
        type=Path,
        default=DEFAULT_RESULTS_DIR,
        help="results-store root each run's --results writes under",
    )
    parser.add_argument(
        "--inputs-dir",
        type=Path,
        default=DEFAULT_INPUTS_DIR,
        help="directory searched for the default LMP export",
    )
    parser.add_argument(
        "--bundled-lmp-dir",
        type=Path,
        default=DEFAULT_BUNDLED_LMP_DIR,
        help="HP-02 bundled real-LMP directory for the input-file dropdown "
        "(optional; degrades gracefully if absent)",
    )
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=DEFAULT_TEMPLATES_DIR,
        help="directory of input templates for the dropdown and Templates help block",
    )
    args = parser.parse_args(argv)

    server = run_server(
        host=DEFAULT_HOST,
        port=args.port,
        state_dir=args.state_dir,
        results_dir=args.results,
        inputs_dir=args.inputs_dir,
        bundled_lmp_dir=args.bundled_lmp_dir,
        templates_dir=args.templates_dir,
        open_browser=not args.no_open,
    )
    url = f"http://{server.server_address[0]}:{server.server_address[1]}/"
    print(f"LCE Portfolio launcher serving at {url} (Ctrl+C to stop)")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Per-ISO solve profiles and the incremental manifest for ``regenerate_clean``.

``data/clean`` is gitignored, so every fresh solve container rebuilds it — and a
bare ``scripts/regenerate_clean.py`` rebuilds EVERY datatype for EVERY ISO
(measured 39-95 min; ``curate_emissions`` alone ~25 min at ~9 GiB RSS), although
the backcast solve reads only a small subset of it. This module holds the two
things that cut that bill, in ONE place:

1. :data:`SOLVE_SOURCES` — the datatype -> (curate script, consumer, ISOs)
   registry. An entry is listed iff a loader on the solve path reads it from
   ``data/clean`` with NO ``MARKET_SIM_USE_CLEAN`` gate and NO raw fallback, so
   an absent partition silently no-ops the mechanism (the caiso-157 /
   miso-263 class :mod:`market_sim.data.input_completeness` guards). Datatypes
   the solve reads only under ``MARKET_SIM_USE_CLEAN`` (emissions, egrid,
   fleet, fuel-prices, outages, lmp, ...) or with a raw fallback
   (nyiso-downstate-gas, nyiso-renewable-curtailment) are deliberately absent.
   ``lane="forecast"`` marks capacity-evolution inputs a ``mode="backcast"``
   run never enters; they join a profile only with ``include_forecast``.

2. The incremental manifest — ``data/clean/<datatype>/.manifest.json``. Its
   ``key`` is the sha256 of a JSON object holding:

   * ``code``   — git blob sha (``git hash-object`` semantics, computed from the
     working-tree bytes) of the curate script, of ``scripts/lib/clean_io.py``,
     and of every ``scripts.lib`` module it imports (transitively);
   * ``schema`` — blob sha of ``data/dictionary/schema/<datatype>.schema.yaml``;
   * ``raw``    — per declared raw input path: the ``HEAD`` tree/blob sha from
     ``git rev-parse HEAD:<path>`` (free in a blobless clone), plus the size and
     mtime of every untracked, ignored or modified file under it from
     ``git status --porcelain --ignored``; a path git does not know at all falls
     back to a size+mtime walk.

   The forwarded scope (``--isos`` / ``--years``) is stored beside the key, not
   in it: a datatype is skipped iff the key is unchanged, the stored scope
   covers the requested one (``None`` = everything) and the datatype dir still
   holds a parquet. ``market_sim`` imports of a curate script are NOT in the
   key; a change there needs ``--force``.

Extending: a new clean-only loader on the solve path appends one
:class:`CleanSource` here (``tests/curation/test_clean_profiles.py`` then checks
its script, schema and flags exist). Runbook + timings:
``docs/clean-data-profiles.md``.
"""

from __future__ import annotations

import ast
import hashlib
import importlib
import json
import os
import subprocess
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT: Path = Path(__file__).resolve().parents[2]
SCRIPTS_DIR: Path = REPO_ROOT / "scripts"
SCHEMA_DIR: Path = REPO_ROOT / "data" / "dictionary" / "schema"
MANIFEST_NAME: str = ".manifest.json"
MANIFEST_VERSION: int = 1

#: Every model ISO registered in ``config/iso_configs.py``.
MODEL_ISOS: tuple[str, ...] = (
    "ERCOT",
    "CAISO",
    "PJM",
    "MISO",
    "NYISO",
    "NEISO",
    "SPP",
    "NWPP",
    "SOCO",
)

#: Partition names a model ISO may be filed under in a curate registry, tried
#: in order. ISO-NE's capacity-deliverability and winter-fuel-inventory
#: registries key on ``ISONE`` (the loaders map NEISO -> ISONE on read).
ISO_PARTITION_ALIASES: dict[str, tuple[str, ...]] = {"NEISO": ("NEISO", "ISONE")}


@dataclass(frozen=True)
class CleanSource:
    """One clean datatype a solve path reads with no raw fallback.

    Attributes:
        datatype: ``data/clean/<datatype>``, the schema stem and the
            ``regenerate_clean.DATATYPES`` entry (dashes -> the script name).
        consumer: The loader that reads it (for the reader, not the code).
        lane: ``"backcast"`` (the calibration solve) or ``"forecast"``
            (capacity evolution only; a backcast never enters it).
        partitions: The partition ISOs the curate script can build. ``None``
            = not ISO-partitioned (national tables; run once, no ISO arg);
            ``"any"`` = derived from data, every ISO accepted; a tuple = a
            static list; ``"module:attr"`` = resolved at run time from the
            curate script's own registry (a callable's keys, or an iterable),
            so a new ISO intake needs no edit here.
        iso_flag: The curate script's ISO-subset flag, if it has one.
        years_flag: The curate script's year-subset flag, if it has one.
        only_for: Model ISOs whose solve reads it (``None`` = any ISO).
        reads_partition_of: Model ISO -> the partition its loader reads when
            that is another ISO's (NYISO's Roseton seam price is NEISO's).
        also_reads: Model ISO -> further partitions its loader reads IN
            ADDITION to its own (NWPP's seam headroom reads CAISO's MALIN
            limits beside its own BPA partition).
        raw_inputs: Repo-relative raw paths it reads, for the manifest key.
            The default (all of ``data/raw``) is the conservative choice; a
            narrower list is declared only where the script reads only it.
    """

    datatype: str
    consumer: str
    lane: str = "backcast"
    partitions: str | tuple[str, ...] | None = "any"
    iso_flag: str | None = "--isos"
    years_flag: str | None = None
    only_for: tuple[str, ...] | None = None
    reads_partition_of: dict[str, str] = field(default_factory=dict)
    also_reads: dict[str, tuple[str, ...]] = field(default_factory=dict)
    raw_inputs: tuple[str, ...] = ("data/raw",)

    @property
    def script(self) -> Path:
        """The curate script that builds this datatype."""
        return SCRIPTS_DIR / "data" / f"curate_{self.datatype.replace('-', '_')}.py"


#: The solve-path registry. One entry per clean-only datatype; the comment on
#: each names the reader so a reviewer can re-verify it.
SOLVE_SOURCES: tuple[CleanSource, ...] = (
    # data/capacity_deliverability.py::load_* — CAISO MIC import cap (Part A);
    # guarded by input_completeness (capacity_deliverability_limits).
    CleanSource(
        "capacity-deliverability",
        "market_sim.data.capacity_deliverability",
        partitions="scripts.lib.capacity_deliverability:load_registry",
        raw_inputs=("data/raw/capacity-deliverability",),
    ),
    # data/hydro_modes.py — the hydro_ror_split classifier; input_completeness.
    CleanSource(
        "hydro-plant-modes",
        "market_sim.data.hydro_modes",
        partitions="scripts.data.curate_hydro_plant_modes:DEFAULT_ISOS",
        iso_flag="--iso",
    ),
    # data/coal_stocks.py + coal_receipts.py -> coal_fuel_inventory budget;
    # national per-year tables, input_completeness (miso-263). The solve year
    # is NEVER forwarded: year Y reads stocks <= Y-1 and receipts over the
    # n_rate_years before Y (coal_fuel_inventory.py), so a --years subset
    # would silently starve the budget. Both scripts take --years; we don't.
    CleanSource(
        "coal-stocks",
        "market_sim.data.coal_stocks",
        partitions=None,
        iso_flag=None,
        raw_inputs=("data/raw/coal-stocks",),
    ),
    CleanSource(
        "coal-receipts",
        "market_sim.data.coal_receipts",
        partitions=None,
        iso_flag=None,
        raw_inputs=("data/raw/coal-receipts",),
    ),
    # data/transfer_interface_limits.py — PJM interface limits and the NWPP
    # seam headroom (run_calibration). NWPP reads its own BPA partition plus
    # CAISO's MALIN/CASCADE limits (nwpp_seam_limits_hourly).
    CleanSource(
        "transfer-interface-limits",
        "market_sim.data.transfer_interface_limits",
        partitions="scripts.lib.transfer_interface_limits:load_specs",
        also_reads={"NWPP": ("CAISO",)},
        raw_inputs=(
            "data/raw/iso-specific-transmission",
            "data/raw/caiso-trns-usage",
            "data/raw/nwpp-intertie-otc",
        ),
    ),
    # data/ramp_capability.py — measured ramp caps (fleet/arrays, withholding).
    CleanSource(
        "ramp-capability",
        "market_sim.data.ramp_capability",
        partitions="scripts.lib.ramp_capability:load_registry",
    ),
    # model/uc/params.py — the MILP UC stage's cluster physics (read only when
    # unit_commitment_milp is armed; no raw fallback, it fails loudly).
    CleanSource(
        "uc-params",
        "market_sim.model.uc.params",
        partitions="scripts.lib.uc_params:load_registry",
        raw_inputs=("data/raw/campd-unit-level",),
    ),
    # data/gtc.py — ERCOT generic transmission constraints (run_calibration).
    # The curate CLI takes no ISO flag; the product is ERCOT-only.
    CleanSource(
        "gtc-limits",
        "market_sim.data.gtc",
        partitions=("ERCOT",),
        iso_flag=None,
        raw_inputs=("data/raw/iso-specific-transmission",),
    ),
    # data/reserve_requirements.py — reads iso="NEISO" only.
    CleanSource(
        "reserve-requirements",
        "market_sim.data.reserve_requirements",
        partitions="scripts.lib.reserve_requirements:load_registry",
        years_flag="--years",
        only_for=("NEISO",),
    ),
    # data/storage_as_awards.py -> model/storage.py (run_calibration).
    CleanSource(
        "storage-as-awards",
        "market_sim.data.storage_as_awards",
        partitions="scripts.lib.storage_as_awards:load_registry",
        raw_inputs=("data/raw/storage-as-awards",),
    ),
    # data/maxgen_events.py -> model/lp (run_calibration).
    CleanSource(
        "maxgen-events",
        "market_sim.data.maxgen_events",
        partitions="scripts.lib.maxgen_events:load_registry",
    ),
    # data/winter_fuel_inventory.py (run_calibration, coal_fuel_inventory).
    CleanSource(
        "winter-fuel-inventory",
        "market_sim.data.winter_fuel_inventory",
        partitions="scripts.lib.winter_fuel_inventory:load_registry",
    ),
    # data/chp.py — CHP behind-the-meter share (fleet assembly, offer curves).
    CleanSource(
        "chp-btm-share",
        "market_sim.data.chp",
        raw_inputs=(
            "data/raw/_processed-legacy/plant_emission_rates_v2.parquet",
            "data/raw/_processed-legacy/eia923_monthly_generation.parquet",
        ),
    ),
    # data/nyiso_seam_envelope.py, nyiso_par_attribution.py, interchange/nyiso.
    CleanSource(
        "nyiso-interface-flows",
        "market_sim.data.nyiso_seam_envelope",
        partitions=("NYISO",),
        iso_flag=None,
        years_flag="--years",
        only_for=("NYISO",),
        raw_inputs=("data/raw/NYISO/interface-flows",),
    ),
    # model/interchange/nyiso.py — Roseton DA price read from NEISO's partition.
    CleanSource(
        "seam-neighbour-price",
        "market_sim.model.interchange.nyiso",
        only_for=("NYISO",),
        reads_partition_of={"NYISO": "NEISO"},
        raw_inputs=("data/raw/seam-neighbour-price",),
    ),
    # --- forecast lane: capacity evolution, never entered by mode="backcast" ---
    # data/confirmed_retirements.py — step-0 confirmed exits.
    CleanSource(
        "confirmed-retirements",
        "market_sim.data.confirmed_retirements",
        lane="forecast",
        partitions="scripts.lib.confirmed_retirements:load_registry",
    ),
    # data/transmission_expansion.py (runner).
    CleanSource(
        "transmission-expansion",
        "market_sim.data.transmission_expansion",
        lane="forecast",
        partitions="scripts.lib.transmission_expansion:load_registry",
    ),
    # data/avoidable_cost_rate.py — PJM net-ACR offers (retirement screen).
    CleanSource(
        "capacity-market-avoidable-cost-rate",
        "market_sim.data.avoidable_cost_rate",
        lane="forecast",
        partitions="scripts.lib.capacity_market_avoidable_cost_rate:load_registry",
        raw_inputs=("data/raw/capacity-market/avoidable-cost-rate",),
    ),
)

SOURCES_BY_DATATYPE: dict[str, CleanSource] = {s.datatype: s for s in SOLVE_SOURCES}


@dataclass(frozen=True)
class PlannedRun:
    """One curate invocation: the datatype, its forwarded args and its scope."""

    datatype: str
    args: tuple[str, ...]
    isos: tuple[str, ...] | None
    years: tuple[int, ...] | None


def resolve_partitions(source: CleanSource) -> tuple[str, ...] | None:
    """Return the partition ISOs ``source``'s curate script can build.

    ``None`` means "not restricted" (national tables, or ``"any"``).
    """
    spec = source.partitions
    if spec is None or spec == "any":
        return None
    if isinstance(spec, tuple):
        return spec
    module_name, attr = spec.split(":")
    obj = getattr(importlib.import_module(module_name), attr)
    if callable(obj):
        obj = obj()
    return tuple(sorted(str(k).upper() for k in obj))


def _partition_for(source: CleanSource, iso: str) -> str | None:
    """The partition name ``source`` should build for model ISO ``iso``."""
    iso = iso.upper()
    if source.only_for is not None and iso not in source.only_for:
        return None
    if iso in source.reads_partition_of:
        return source.reads_partition_of[iso]
    available = resolve_partitions(source)
    candidates = ISO_PARTITION_ALIASES.get(iso, (iso,))
    if available is None:
        return candidates[0]
    return next((c for c in candidates if c in available), None)


def plan_profile(
    isos: Sequence[str],
    years: Sequence[int] | None = None,
    *,
    include_forecast: bool = False,
) -> list[PlannedRun]:
    """Plan the curate runs a solve of ``isos`` needs.

    ``isos`` of ``["all"]`` plans every entry with no ISO subset (a full build
    of each needed datatype). Otherwise each entry is planned once, with the
    union of the partitions the requested ISOs read, forwarded through the
    script's ISO flag; an entry no requested ISO reads is dropped. ``years``
    is forwarded wherever the script takes a year flag.
    """
    want_all = [i.lower() for i in isos] == ["all"]
    yrs = tuple(sorted({int(y) for y in years})) if years else None
    plan: list[PlannedRun] = []
    for source in SOLVE_SOURCES:
        if source.lane == "forecast" and not include_forecast:
            continue
        if want_all:
            parts: tuple[str, ...] | None = None
        else:
            found = {_partition_for(source, iso) for iso in isos} - {None}
            for iso in isos:
                found |= set(source.also_reads.get(iso.upper(), ()))
            if not found:
                continue
            parts = tuple(sorted(found))
        args: list[str] = []
        if parts is not None and source.partitions is not None and source.iso_flag:
            args += [source.iso_flag, *parts]
        scope_isos = (
            parts if (source.iso_flag and source.partitions is not None) else None
        )
        scope_years = None
        if yrs and source.years_flag:
            args += [source.years_flag, *map(str, yrs)]
            scope_years = yrs
        plan.append(PlannedRun(source.datatype, tuple(args), scope_isos, scope_years))
    return plan


# ---------------------------------------------------------------------------
# Manifest key
# ---------------------------------------------------------------------------
def _git(*args: str) -> str | None:
    """Run a read-only git command; ``None`` on failure. Never lazy-fetches."""
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1")
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout


def blob_sha(path: Path) -> str | None:
    """Git blob sha of ``path``'s working-tree bytes (``git hash-object``)."""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def _lib_module_files(name: str) -> list[Path]:
    """Files backing ``scripts.lib.<name>`` (a module, or a package's .py files)."""
    base = SCRIPTS_DIR / "lib" / name
    if base.is_dir():
        return sorted(base.rglob("*.py"))
    mod = base.with_suffix(".py")
    return [mod] if mod.is_file() else []


def _scripts_lib_imports(path: Path) -> set[str]:
    """Top-level ``scripts.lib.<name>`` modules ``path`` imports."""
    try:
        tree = ast.parse(path.read_text())
    except (OSError, SyntaxError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            parts = node.module.split(".")
            if parts[:2] == ["scripts", "lib"]:
                if len(parts) > 2:
                    found.add(parts[2])
                else:
                    found.update(a.name for a in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[:2] == ["scripts", "lib"] and len(parts) > 2:
                    found.add(parts[2])
    return found


def code_files(script: Path) -> list[Path]:
    """The curate script plus every ``scripts.lib`` file it reaches, transitively."""
    files: list[Path] = [script, SCRIPTS_DIR / "lib" / "clean_io.py"]
    seen: set[str] = set()
    queue = sorted(_scripts_lib_imports(script))
    while queue:
        name = queue.pop()
        if name in seen:
            continue
        seen.add(name)
        for f in _lib_module_files(name):
            files.append(f)
            queue.extend(sorted(_scripts_lib_imports(f) - seen))
    return sorted(set(files))


def _stat_token(path: Path) -> str:
    """``size:mtime_ns`` of ``path``, or ``missing``."""
    try:
        st = path.stat()
    except OSError:
        return "missing"
    return f"{st.st_size}:{st.st_mtime_ns}"


def raw_fingerprint(rel: str) -> dict[str, object]:
    """Fingerprint one repo-relative raw input (see the module docstring)."""
    head = _git("rev-parse", "-q", "--verify", f"HEAD:{rel}")
    if head is None:
        root = REPO_ROOT / rel
        files = (
            [root]
            if root.is_file()
            else sorted(p for p in root.rglob("*") if p.is_file())
        )
        return {
            "head": None,
            "stat": {
                p.relative_to(REPO_ROOT).as_posix(): _stat_token(p) for p in files
            },
        }
    status = (
        _git("status", "--porcelain", "--ignored", "--untracked-files=all", "--", rel)
        or ""
    )
    dirty: dict[str, str] = {}
    for line in status.splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        dirty[name] = _stat_token(REPO_ROOT / name)
    return {"head": head.strip(), "dirty": dict(sorted(dirty.items()))}


def manifest_components(datatype: str) -> dict[str, object]:
    """The inputs that make up ``datatype``'s manifest key."""
    source = SOURCES_BY_DATATYPE.get(datatype)
    script = (
        source.script
        if source
        else SCRIPTS_DIR / "data" / f"curate_{datatype.replace('-', '_')}.py"
    )
    raw_inputs = source.raw_inputs if source else ("data/raw",)
    return {
        "version": MANIFEST_VERSION,
        "code": {
            f.relative_to(REPO_ROOT).as_posix(): blob_sha(f) for f in code_files(script)
        },
        "schema": blob_sha(SCHEMA_DIR / f"{datatype}.schema.yaml"),
        "raw": {rel: raw_fingerprint(rel) for rel in raw_inputs},
    }


def manifest_key(components: dict[str, object]) -> str:
    """sha256 over the canonical JSON of ``components``."""
    blob = json.dumps(components, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(blob).hexdigest()


# ---------------------------------------------------------------------------
# Manifest read / write / skip
# ---------------------------------------------------------------------------
def _clean_dir() -> Path:
    """``paths.CLEAN_DIR``, looked up lazily so test redirects apply."""
    from market_sim.config import paths

    return Path(paths.CLEAN_DIR)


def manifest_path(datatype: str) -> Path:
    """``data/clean/<datatype>/.manifest.json``."""
    return _clean_dir() / datatype / MANIFEST_NAME


def read_manifest(datatype: str) -> dict | None:
    """The stored manifest, or ``None`` when absent or unreadable."""
    try:
        return json.loads(manifest_path(datatype).read_text())
    except (OSError, ValueError):
        return None


def _covers(stored: Iterable | None, requested: Iterable | None) -> bool:
    """Whether a stored scope (``None`` = everything) covers a requested one."""
    if stored is None:
        return True
    if requested is None:
        return False
    return set(requested) <= set(stored)


def has_output(datatype: str) -> bool:
    """Whether ``data/clean/<datatype>`` holds at least one parquet."""
    root = _clean_dir() / datatype
    return root.is_dir() and any(root.rglob("*.parquet"))


def should_skip(run: PlannedRun, key: str) -> bool:
    """True iff ``run`` is already satisfied by an up-to-date build."""
    stored = read_manifest(run.datatype)
    if not stored or stored.get("key") != key or not has_output(run.datatype):
        return False
    scope = stored.get("scope", {})
    return _covers(scope.get("isos"), run.isos) and _covers(
        scope.get("years"), run.years
    )


def _union(a: Iterable | None, b: Iterable | None) -> list | None:
    """Scope union where ``None`` is everything."""
    if a is None or b is None:
        return None
    return sorted(set(a) | set(b))


def write_manifest(
    run: PlannedRun, key: str, components: dict[str, object]
) -> Path | None:
    """Record a successful build. No-op when the script wrote no datatype dir.

    If the key is unchanged the stored scope is widened by this run's;
    otherwise this run's scope replaces it.
    """
    root = _clean_dir() / run.datatype
    if not root.is_dir():
        return None
    isos = list(run.isos) if run.isos is not None else None
    years = list(run.years) if run.years is not None else None
    prior = read_manifest(run.datatype)
    if prior and prior.get("key") == key:
        scope = prior.get("scope", {})
        isos = _union(scope.get("isos"), isos)
        years = _union(scope.get("years"), years)
    path = root / MANIFEST_NAME
    path.write_text(
        json.dumps(
            {
                "datatype": run.datatype,
                "key": key,
                "scope": {"isos": isos, "years": years},
                "components": components,
            },
            indent=1,
            sort_keys=True,
        )
        + "\n"
    )
    return path

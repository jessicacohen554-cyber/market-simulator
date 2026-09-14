"""The SOLVE-SURFACE fingerprint — what the cache key sees beyond ``ScenarioConfig``.

``ScenarioConfig.cache_key()`` hashes the config and nothing else, so a change
to a *registry table* — a demand-growth rate, an adequacy operand, a
capacity-demand curve, a fuel trajectory — changes what a solve produces while
leaving every key unmoved, and the pre-change ``results/<ISO>/<key>/`` bundle is
silently re-used. That is the SCN-LOAD incident (`DEMAND_GROWTH_RATES` /
`DATACENTER_ADDITIONS_MW` / `ELECTRIFICATION_LAYERS` re-derived, every T1-F peak
moved, zero keys moved), and it is the surface this module closes.

**What it is** (owner ruling Q54, capx D79 phase 1; full design, measurements
and blast radius: `docs/handoffs/DESIGN-capx-d79-2026-09-06.md`). A per-name,
per-ISO-projected VALUE fingerprint of the seven registry modules in
:data:`SURFACE_MODULES`, each name dropped at its FROZEN registration-time hash
in :mod:`market_sim.config.solve_surface_declared` — the capx D24-R option
(b′-1) construction transplanted from ``ScenarioConfig`` fields to
``constants.py`` tables — plus a mechanical, SCOPED epoch ledger
(:data:`SOLVE_EPOCHS`) for the code-level changes a value hash cannot see.

Two refinements make it affordable, both measured over 2026-08-07 → 2026-09-06
(design §4.1): **ISO projection** drops the firing rate from 16 changes for the
unprojected whole to 2-7 per ISO with zero spurious fires; and **dropping at the
frozen registration hash** means a name enters the key ONLY when its live hash
differs from its declaration, so adding a table moves no key and a revert
restores the pre-change key because it is the same model. **Landing moves zero
keys** — merge gate `docs/handoffs/capxd79-solve-surface-no-op-record.json`.

**Rule 24 [R-REGISTRY]: DERIVED, never settable** — no env var, no CLI flag, no
``ScenarioConfig`` field; a knob here would be an off-registry tuning channel
and a solve could not then be reproduced from its recorded config. Rule 26
[R-DELETE]: :data:`~.solve_surface_declared.DECLARED` and :data:`SOLVE_EPOCHS`
are APPEND-ONLY (a retired name keeps its last hash, exactly as
``_CACHE_KEY_RETIRED_FIELDS`` does for a deleted field), enforced by
``scripts/check_cache_key_registration.py`` checks 5-7. Scope boundary (design
§2.3): the four standalone config registry modules plus the three pure-value
ones; ``iso_configs.py`` (reads the reliability-floor CSVs at import),
``model/reserves/spec.py`` and ``model/interchange/spec.py`` (import
``data.fleet``) are OUT of phase 1, routed to a later card.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from functools import lru_cache
from importlib import util
from pathlib import Path

#: The registry modules whose module-level values the key sees (design §2.3).
#: All seven import nothing but each other and stdlib, and none reads a file at
#: import, which is what makes the fingerprint reproducible from source alone.
SURFACE_MODULES: tuple[str, ...] = (
    "market_sim.config.constants",
    "market_sim.config.capacity_market",
    "market_sim.config.fuel_trajectories",
    "market_sim.config.ercot_envelopes",
    "market_sim.config.plant_taxonomy",
    "market_sim.config.entry_config",
    "market_sim.pipeline.offer_curve_base.generic",
)

#: The seven registered ISOs, mirroring ``iso_configs.SUPPORTED_ISOS``. Repeated
#: here rather than imported because ``iso_configs`` reads
#: ``data/raw/reference/reliability_floor_coeffs_<ISO>.csv`` at import time and
#: this module must stay stdlib-only; ``tests/unit/config/test_solve_surface.py``
#: pins the two tuples equal, so an ISO cannot land in only one place. SPP was
#: appended 2026-09-06 (lane SPP-20) in the same commit as its ``_ISO_BUILDERS``
#: entry; appended LAST, and no surface name carries an ``SPP`` token, so the
#: six earlier ISOs' projections are unchanged by construction. SOCO — the
#: Southern Company balancing authority, the eighth registered region and the
#: first that is not an ISO — was appended 2026-09-14 (lane SOCO-20) the same
#: way: last, in the ``_ISO_BUILDERS`` commit, with no surface name carrying a
#: ``SOCO`` token, so the seven earlier projections are again unchanged.
SURFACE_ISOS: tuple[str, ...] = (
    "ERCOT",
    "CAISO",
    "MISO",
    "PJM",
    "NYISO",
    "NEISO",
    "SPP",
    # NWPP registered 2026-09-14 by lane NWPP-20, in the SAME commit as
    # ``iso_configs._ISO_BUILDERS["NWPP"]`` and ``DEMAND_LOADERS["NWPP"]``
    # (plan §2.3 / gate G1: the pinned-tuple test and the import-time assert
    # both refuse a half-flipped pin). Appended LAST so the seven earlier
    # regions' rows and keys are untouched (gate G8).
    "NWPP",
    "SOCO",
)

#: A module-level *surface name*: SCREAMING_CASE, no leading underscore. Private
#: composition pieces (``_PJM_VRR_CURVE``…) are covered transitively through the
#: public tables they are composed into, so hashing them again would double-count.
_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")


@dataclass(frozen=True)
class SolveEpoch:
    """One SCOPED code-level invalidation, declared in code rather than prose.

    The cache-epoch ledger in ``results/cache.py`` states each entry's scope in
    English ("forecast recipes whose horizon reaches 2028"); a ``SolveEpoch``
    states the same thing mechanically, so :func:`applicable_epochs` puts its
    ``id`` into exactly the keys the prose names and no others. A single GLOBAL
    epoch token stays unavailable — it would re-key every backcast keeper for a
    forecast-only change, the objection the ledger raises against a
    ``CACHE_EPOCH`` constant.

    Attributes:
        id: The ledger's dated id, e.g. ``"2026-09-06b"``. Never reused.
        cause: One line naming what changed; the ledger entry is the full record.
        modes: ``ScenarioConfig.mode`` values this reaches; empty = every mode.
        isos: ISOs this reaches; empty = every ISO.
        reaches_year: Applies only to a run whose horizon reaches this year.
            A config with no ``end_year`` is treated as reaching it (fail-safe:
            an unknown horizon is invalidated rather than silently served).
    """

    id: str
    cause: str
    modes: tuple[str, ...] = ()
    isos: tuple[str, ...] = ()
    reaches_year: int | None = None


#: APPEND-ONLY (rule 26 [R-DELETE]): an epoch id is never edited or removed once
#: declared, because it is part of the key of every bundle solved under it.
#:
#: EMPTY AT LANDING, by owner ruling Q54 row 4. D77's ledger entry 2026-09-06b
#: (the CCS-retrofit emission-rate seam) stays prose: back-filling it as an epoch
#: would re-key forecast bundles that the D65-B-R batch is re-solving anyway.
SOLVE_EPOCHS: tuple[SolveEpoch, ...] = ()


class Unhashable(TypeError):
    """A surface value has no canonical image (a class, function or module)."""


def canonical(value: object) -> object:
    """Return a JSON-serialisable, TYPE-FAITHFUL, order-independent image.

    Order-independent so re-ordering a dict literal or a ``frozenset`` moves
    nothing; type-faithful so a tuple is not a list, ``1`` is not ``1.0`` and an
    ``Enum`` member is not its bare value — each of those changes the solve.
    Floats go through ``repr`` (exact round-trip, no formatting drift).

    Args:
        value: Any module-level registry value.

    Returns:
        A structure of lists, strings, bools and ``None`` only.

    Raises:
        Unhashable: ``value`` is a class, function or module, which has no
            value-level image (the code surface is out of scope — design §3).
    """
    if value is None:
        return ["none", None]
    if isinstance(value, Enum):  # before int: an IntEnum is also an int
        return ["enum", type(value).__name__, canonical(value.value)]
    if isinstance(value, bool):  # before int: a bool is also an int
        return ["bool", value]
    if isinstance(value, int):
        return ["int", str(value)]  # str, so JSON cannot widen it to a float
    if isinstance(value, float):
        return ["float", repr(value)]
    if isinstance(value, str):
        return ["str", value]
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, Path):
        return ["path", str(value)]
    if is_dataclass(value) and not isinstance(value, type):
        return [
            "dataclass",
            type(value).__name__,
            [[f.name, canonical(getattr(value, f.name))] for f in fields(value)],
        ]
    if isinstance(value, dict):
        return [
            "dict",
            _sorted([[canonical(k), canonical(v)] for k, v in value.items()]),
        ]
    if isinstance(value, frozenset):
        return ["frozenset", _sorted([canonical(v) for v in value])]
    if isinstance(value, set):
        return ["set", _sorted([canonical(v) for v in value])]
    if isinstance(value, tuple):
        return ["tuple", [canonical(v) for v in value]]
    if isinstance(value, list):
        return ["list", [canonical(v) for v in value]]
    raise Unhashable(f"{type(value).__name__} has no canonical image")


def _compact(value: object) -> str:
    """Render a canonical image as its compact, key-sorted JSON text."""
    return json.dumps(value, separators=(",", ":"))


def _sorted(items: list) -> list:
    """Sort canonical images by their JSON text — a total order on any types.

    Registry keys mix ``str`` and ``tuple``, so Python's own ordering is
    unavailable; the text of each image depends on nothing but the values.
    """
    return sorted(items, key=_compact)


def row_hash(value: object) -> str:
    """Return the 16-hex fingerprint of one surface value."""
    return hashlib.sha256(_compact(canonical(value)).encode()).hexdigest()[:16]


def _iso_tokens(name: str) -> frozenset[str]:
    """The ISOs a name is scoped to by its own ``_``-delimited tokens.

    Token equality, never a substring match, so no ISO name can be found inside
    another word (``ERCOT_GTC_LINK_MAP`` → ERCOT; ``CORRELATED_OUTAGE_CURVE`` →
    none, i.e. shared).
    """
    tokens = set(name.split("_"))
    return frozenset(iso for iso in SURFACE_ISOS if iso in tokens)


def _load(name: str):
    """Return a surface module, WITHOUT initializing a heavy parent package.

    ``market_sim.pipeline.offer_curve_base.generic`` is a pure-value leaf, but
    ``market_sim.pipeline.__init__`` imports the whole solve stack — and
    ``cache_key()`` reaches this module, so a plain ``import_module`` would drag
    that stack (and a cycle back through ``scenarios``) into every key. An
    already-imported module is reused as-is; otherwise the file is executed in
    isolation, which is equivalent because every surface module's values are
    deterministic module-level literals.
    """
    module = sys.modules.get(name)
    if module is not None:
        return module
    rel = name.split("market_sim.", 1)[1].replace(".", "/") + ".py"
    path = Path(__file__).resolve().parents[1] / rel
    spec = util.spec_from_file_location(f"_solve_surface__{name}", path)
    module = util.module_from_spec(spec)
    # Registered BEFORE exec: ``@dataclass`` resolves its own ``cls.__module__``
    # through ``sys.modules`` and raises on a module that is not there yet.
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(spec.name, None)
        raise
    return module


@lru_cache(maxsize=1)
def surface_fingerprint() -> dict[str, object]:
    """Return ``{name: hash}``, or ``{name: {iso: hash}}`` for a by-ISO table.

    The whole surface, unprojected, in :data:`SURFACE_MODULES` order; the first
    module to define a name owns it (they import each other, so a name re-exported
    downstream is the same object). A value with no canonical image is recorded as
    ``"skip:<type>"`` so that this view and the AST view CI check 5 takes stay in
    exact agreement about which names exist.
    """
    out: dict[str, object] = {}
    for module_name in SURFACE_MODULES:
        module = _load(module_name)
        for name, value in vars(module).items():
            if not _NAME_RE.match(name) or name in out:
                continue
            try:
                if (
                    isinstance(value, dict)
                    and value
                    and set(value) <= set(SURFACE_ISOS)
                ):
                    out[name] = {iso: row_hash(v) for iso, v in value.items()}
                else:
                    out[name] = row_hash(value)
            except Unhashable as exc:
                out[name] = f"skip:{exc.args[0].split()[0]}"
    return out


@lru_cache(maxsize=len(SURFACE_ISOS) + 4)
def surface_rows(iso: str | None) -> dict[str, str]:
    """Return the surface rows an ``iso``'s solve is sensitive to.

    The projection rule (design §4.1), in order: a dict whose top-level keys are
    all ISO names contributes ONE row, its own ISO's, and only to that ISO; a
    name carrying ISO tokens contributes only to those ISOs; everything else is
    shared and contributes to every ISO.

    Args:
        iso: An ISO identifier, or ``None`` / an unregistered value (which then
            sees the shared rows only).

    Returns:
        ``{name: 16-hex hash}``, sorted by name.
    """
    rows: dict[str, str] = {}
    for name, value in surface_fingerprint().items():
        if isinstance(value, dict):
            if iso in value:
                rows[name] = value[iso]
            continue
        tokens = _iso_tokens(name)
        if not tokens or iso in tokens:
            rows[name] = value
    return dict(sorted(rows.items()))


@lru_cache(maxsize=len(SURFACE_ISOS) + 4)
def moved_rows(iso: str | None) -> dict[str, str]:
    """Return the rows whose live hash differs from their FROZEN declaration.

    This — and only this — is what ``cache_key`` carries, which is what makes
    landing a zero-key-move event. Two absences are deliberately NOT moves:

    * a live row with NO declaration cannot be compared against anything, so it
      stays out of the key; CI check 5 is what forces the declaration to exist,
      in the PR that adds the table (so an addition never re-keys anything);
    * a declared row that has LEFT the surface keeps every historical key stable,
      exactly as ``_CACHE_KEY_RETIRED_FIELDS`` does for a deleted field.

    Args:
        iso: The ISO whose projection to compare.

    Returns:
        ``{name: live hash}`` for the moved rows, sorted by name; empty when the
        surface is at its declarations.
    """
    from market_sim.config.solve_surface_declared import DECLARED

    moved = {}
    for name, live in surface_rows(iso).items():
        declared = DECLARED.get(name)
        if isinstance(declared, dict):
            declared = declared.get(iso)
        if declared is not None and declared != live:
            moved[name] = live
    return dict(sorted(moved.items()))


def applicable_epochs(config) -> list[str]:
    """Return the ids of the :data:`SOLVE_EPOCHS` whose scope covers ``config``.

    Args:
        config: A ``ScenarioConfig`` (duck-typed: ``mode``, ``iso``, ``end_year``).

    Returns:
        Epoch ids in declaration order — empty for every config while
        :data:`SOLVE_EPOCHS` is empty.
    """
    out = []
    for epoch in SOLVE_EPOCHS:
        if epoch.modes and getattr(config, "mode", None) not in epoch.modes:
            continue
        if epoch.isos and getattr(config, "iso", None) not in epoch.isos:
            continue
        end_year = getattr(config, "end_year", None)
        if (
            epoch.reaches_year is not None
            and end_year is not None
            and end_year < epoch.reaches_year
        ):
            continue
        out.append(epoch.id)
    return out


@lru_cache(maxsize=1)
def _git_sha() -> str:
    """The short HEAD sha, or ``""`` when git cannot answer (never raises)."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=Path(__file__).resolve().parents[3],
            capture_output=True,
            text=True,
            timeout=15,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def surface_stamp(iso: str | None, config) -> dict:
    """Return the ``solve_surface`` block a bundle records beside its cache key.

    Written to ``solve_surface.json`` in every cache bundle and to the
    ``run_config.json`` / ``meta.json`` / board sidecars, so ``key = f(config,
    moved rows, epochs)`` is reproducible from the artifact alone — the property
    every re-key event so far has eroded.

    Args:
        iso: The ISO the run solves.
        config: The run's ``ScenarioConfig``.

    Returns:
        ``{schema, iso, fingerprint, rows, moved, epochs, git_sha}``, where
        ``fingerprint`` hashes the ISO's WHOLE projected row set, so two runs on
        two surfaces are distinguishable even where neither row has moved off
        its declaration.
    """
    rows = surface_rows(iso)
    digest = hashlib.sha256(_compact(dict(sorted(rows.items()))).encode()).hexdigest()[
        :16
    ]
    return {
        "schema": 1,
        "iso": iso,
        "fingerprint": digest,
        "rows": len(rows),
        "moved": moved_rows(iso),
        "epochs": applicable_epochs(config),
        "git_sha": _git_sha(),
    }


def reset_caches() -> None:
    """Drop every memoized view — for tests that mutate a registry in place."""
    surface_fingerprint.cache_clear()
    surface_rows.cache_clear()
    moved_rows.cache_clear()

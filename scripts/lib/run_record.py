"""Solved-config-sourced run records (FFR-3R — the record-provenance class).

A run record — ``meta.json``, ``run_config.json``, a registration sidecar, an
attestation — is an artifact that *describes what a run did*. Four separate
lanes each independently found the same defect in one: a record field sourced
from the CLI ``args`` namespace (or from a mirrored literal) rather than from
the :class:`~market_sim.config.scenarios.ScenarioConfig` object the solve
actually ran on, so the record said something the run did not do.

===========  ============================================================
FFR-1D       a meta entry sourced from a flag that armed nothing
FFR-3D       ``entry_lookahead_reprice`` / ``correlated_forced_outage``:
             once the flags became tri-state, ``bool(None)`` stamped
             ``false`` on every leg that ran the shipped ``True``
FFR-2E       ``capacity_market_clearing``: a flag-sourced value
             mis-classified every shipped-posture leg as curve-OFF,
             because ``forecast_verdict._curve_on`` reads that key
FFR-3L       ``retirement_rule``: missed by the FFR-3D sweep, so every
             shipped-default leg recorded ``null`` for the rule it solved
===========  ============================================================

Each was patched key-by-key with its own explanatory comment, which is what
made the meta dict a patchwork whose correctness is per-key and maintained by
prose. This module replaces that with a declared, checked contract.

**The scoping distinction.** ``args`` → ``ScenarioConfig`` is what a CLI is
*for* and is not the target: config CONSTRUCTION legitimately reads argparse.
The defect is exclusively in the RECORD. Everything here operates on the
record side of the solve.

Usage — declare the record's config-describing block once as a spec, build the
block from it, and assert the finished record against it::

    SPEC = RecordSpec({
        "retirement_rule": FromConfig(),
        "capacity_market_clearing": Derived(
            lambda cfg, ctx: bool(resolve_capacity_market_clearing(cfg, ctx["iso"])),
            "the RESOLVED per-ISO gate, not the scalar field",
        ),
        "capacity_market_clearing_forced": FromArgs(
            "records WHICH CLI ARM was selected, not a config property",
        ),
    })

    meta = {..., **SPEC.build(config, ctx, args_values), ...}
    SPEC.assert_sourced(meta, config, ctx)

The property this guarantees: **a key naming a ``ScenarioConfig`` field cannot
enter the record from ``args`` (or from any other source) without someone
deliberately declaring it** — an undeclared config-named key is a violation, a
``FromConfig``/``Derived`` key is checked against the solved object, and a
``FromArgs`` key must carry a written reason. Instance five fails loudly at the
moment it is written rather than years later in a scored verdict.

Rule 24 (``[R-REGISTRY]``) in prose: "every tunable ... appears in the run's
``run_config.json``". This is that rule made executable for the record side.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

__all__ = [
    "FromConfig",
    "Derived",
    "FromArgs",
    "RecordSpec",
    "as_attr_view",
    "config_field_names",
    "normalize",
    "write_run_config",
]


# --------------------------------------------------------------------------- #
# Source declarations
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class FromConfig:
    """Record this key straight off the solved config.

    Attributes:
        field: The ``ScenarioConfig`` attribute to read. ``None`` (the default)
            means the record key IS the field name — the common case, and the
            one that makes a config-named key correct by construction.
        cast: Optional coercion applied to the config value before recording
            (in practice ``bool``, so a tri-state ``None`` is never stamped
            into a boolean record slot as a *guess* — the config has already
            resolved it by then).
        why: Optional note, only needed when ``field`` differs from the key.
    """

    field: str | None = None
    cast: Callable[[Any], Any] | None = None
    why: str = ""


@dataclass(frozen=True)
class Derived:
    """Record a value COMPUTED from the solved config (never from ``args``).

    For keys whose recorded value is a resolution of the config rather than one
    of its fields — e.g. the per-ISO capacity-clearing gate, which is resolved
    from ``capacity_market_clearing_by_iso`` and the ISO, and is deliberately
    NOT equal to the scalar ``capacity_market_clearing`` field of the same name.

    Attributes:
        fn: ``(config, ctx) -> value``. Must be pure and must read only the
            solved config and the context dict — never an argparse namespace.
        why: Required. Why this key is a resolution rather than a plain field.
    """

    fn: Callable[[Any, Mapping[str, Any]], Any]
    why: str


@dataclass(frozen=True)
class FromArgs:
    """Record this key from the CLI request — the deliberate opt-in.

    Legitimate only when the key records something that is genuinely NOT a
    property of the solved config: which harness arm the operator selected,
    a governance state read at launch, a run label. A ``FromArgs`` key whose
    value the config also carries is the defect this module exists to stop, so
    every entry must state, in one line, why the config cannot answer it.

    Attributes:
        why: Required, non-empty. The one-line reason.
    """

    why: str

    def __post_init__(self) -> None:
        if not str(self.why).strip():
            raise ValueError(
                "FromArgs requires a written reason — an args-sourced record "
                "key is the FFR-3R defect class unless it records something "
                "the solved config genuinely cannot answer"
            )


Source = FromConfig | Derived | FromArgs


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def config_field_names() -> frozenset[str]:
    """Return every ``ScenarioConfig`` field name.

    The set a record key is tested against: a key that names a config field is
    a claim about the solved config, whatever the writer meant by it.
    """
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    return frozenset(f.name for f in dataclasses.fields(ScenarioConfig))


class _AttrView:
    """Expose a persisted config mapping with attribute access.

    A solved config reaches this module in two shapes: the live
    ``ScenarioConfig`` object (inside a runner) and its persisted dump — the
    ``scenario_config`` block of a ``run_config.json``, or a ``config.yaml``
    (inside a registrar or a scoring/audit pass over a committed bundle). Both
    are the same claim about the same solve, so both must be checkable by the
    same spec. Wrapping the mapping also lets duck-typed resolvers such as
    ``resolve_capacity_market_clearing`` run unchanged over a dump.
    """

    def __init__(self, data: Mapping[str, Any]):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        try:
            return self._data[name]
        except KeyError as exc:  # pragma: no cover - message clarity only
            raise AttributeError(f"persisted config carries no field {name!r}") from exc

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"_AttrView({len(self._data)} fields)"


def as_attr_view(config: Any) -> Any:
    """Return ``config`` unchanged, or an attribute view over a mapping."""
    return _AttrView(config) if isinstance(config, Mapping) else config


def normalize(value: Any) -> Any:
    """Round-trip ``value`` through JSON so on-disk and in-memory compare equal.

    A record read back from disk has lost Python's tuples, sets and frozen
    dataclasses; comparing it to a live config value without this reports
    spurious divergence (``("a", "b") != ["a", "b"]``).
    """
    return json.loads(json.dumps(value, default=str, sort_keys=True))


# --------------------------------------------------------------------------- #
# The spec
# --------------------------------------------------------------------------- #
class RecordSpec:
    """A declared, checked contract for one record's config-describing block.

    Args:
        sources: Ordered mapping of record key → :class:`FromConfig` /
            :class:`Derived` / :class:`FromArgs`. Order is the order
            :meth:`build` emits, so the on-disk record stays readable.
        name: Human label used in error messages (e.g. ``"hindcast meta.json"``).
    """

    def __init__(self, sources: Mapping[str, Source], name: str = "run record"):
        self.sources: dict[str, Source] = dict(sources)
        self.name = name

    def merged(self, other: "RecordSpec | None") -> "RecordSpec":
        """Return this spec extended by ``other``'s declarations.

        A caller that merges extra keys into someone else's record (the
        ``extra_summary`` / ``extra_meta`` seams) declares them with a spec of
        its own rather than being exempted wholesale. Composition, not a bypass:
        the extra keys are checked against the same solved config, so the
        opt-in stays deliberate and stays verified.

        Args:
            other: The extending spec, or ``None`` (returns ``self``).

        Raises:
            ValueError: The two specs declare the same key differently.
        """
        if other is None:
            return self
        clash = {
            k
            for k in set(self.sources) & set(other.sources)
            if self.sources[k] != other.sources[k]
        }
        if clash:
            raise ValueError(
                f"{self.name} and {other.name} declare {sorted(clash)} "
                f"differently — one record key has one source"
            )
        return RecordSpec(
            {**self.sources, **other.sources}, name=f"{self.name} + {other.name}"
        )

    # -- construction ------------------------------------------------------ #
    def build(
        self,
        config,
        ctx: Mapping[str, Any] | None = None,
        args_values: Mapping[str, Any] | None = None,
    ) -> dict:
        """Build the config-describing block from the SOLVED config.

        This is the half that makes the defect structurally impossible: every
        ``FromConfig``/``Derived`` value is read off ``config``, so no call site
        gets the chance to reach for ``args``. ``FromArgs`` keys are supplied by
        the caller through ``args_values`` — the deliberate, declared opt-in.

        Args:
            config: The ``ScenarioConfig`` the solve actually ran on.
            ctx: Extra pure context a ``Derived`` resolver may need (``iso``).
            args_values: Values for the ``FromArgs`` keys. Every declared
                ``FromArgs`` key must be present.

        Returns:
            The block, in spec order.

        Raises:
            KeyError: A declared ``FromArgs`` key was not supplied.
            AttributeError: A ``FromConfig`` key names no config attribute.
        """
        ctx = dict(ctx or {})
        args_values = dict(args_values or {})
        config = as_attr_view(config)
        block: dict[str, Any] = {}
        for key, src in self.sources.items():
            if isinstance(src, FromConfig):
                value = getattr(config, src.field or key)
                block[key] = src.cast(value) if src.cast else value
            elif isinstance(src, Derived):
                block[key] = src.fn(config, ctx)
            else:  # FromArgs
                if key not in args_values:
                    raise KeyError(
                        f"{self.name}: {key!r} is declared FromArgs but no "
                        f"value was supplied to build()"
                    )
                block[key] = args_values[key]
        return block

    # -- verification ------------------------------------------------------ #
    def check(
        self, record: Mapping[str, Any], config, ctx: Mapping[str, Any] | None = None
    ) -> list[str]:
        """Return every way ``record`` diverges from the solved ``config``.

        Three classes of violation, all of them instance-five detectors:

        1. **Divergence** — a ``FromConfig``/``Derived`` key whose recorded
           value is not what the solved config says. This is the FFR-1D /
           FFR-3D / FFR-2E / FFR-3L defect itself.
        2. **Undeclared config-named key** — a record key that names a
           ``ScenarioConfig`` field but is in no spec. A new field recorded
           from ``args`` lands here, which is the point: it cannot be recorded
           without someone deliberately opting it in.
        3. **Unreasoned exemption** — a ``FromArgs`` key with no written
           reason. (Constructed-away by ``FromArgs.__post_init__``; re-checked
           here so a hand-built spec cannot skip it.)

        Args:
            record: The finished record (in-memory dict or parsed JSON).
            config: The ``ScenarioConfig`` the solve ran on.
            ctx: Same context passed to :meth:`build`.

        Returns:
            A list of human-readable violations; empty when the record is
            faithful.
        """
        ctx = dict(ctx or {})
        config = as_attr_view(config)
        violations: list[str] = []
        for key, src in self.sources.items():
            if key not in record:
                continue  # a spec key the caller chose not to emit is not a lie
            if isinstance(src, FromArgs):
                if not str(src.why).strip():
                    violations.append(
                        f"{key}: declared FromArgs with no written reason"
                    )
                continue
            if isinstance(src, FromConfig):
                raw = getattr(config, src.field or key)
                expected = src.cast(raw) if src.cast else raw
                origin = f"config.{src.field or key}"
            else:
                expected = src.fn(config, ctx)
                origin = f"derived({src.why})"
            if normalize(record[key]) != normalize(expected):
                violations.append(
                    f"{key}: record says {record[key]!r} but {origin} is "
                    f"{expected!r} — the run record diverges from the solved "
                    f"config (rule 24)"
                )
        undeclared = (config_field_names() & set(record)) - set(self.sources)
        for key in sorted(undeclared):
            violations.append(
                f"{key}: names a ScenarioConfig field but is undeclared in "
                f"{self.name}'s spec — declare it FromConfig/Derived (checked "
                f"against the solve) or FromArgs (with a written reason)"
            )
        return violations

    def assert_sourced(
        self, record: Mapping[str, Any], config, ctx: Mapping[str, Any] | None = None
    ) -> None:
        """Raise :class:`SystemExit` if ``record`` diverges from ``config``.

        Called immediately before a record is written, so a divergent record is
        never produced in the first place. ``SystemExit`` rather than a bespoke
        exception because every call site is a CLI entry point, and a run whose
        record would lie should stop with a readable message.
        """
        violations = self.check(record, config, ctx)
        if violations:
            raise SystemExit(
                f"{self.name}: run record diverges from the solved "
                f"ScenarioConfig (FFR-3R / rule 24):\n  - " + "\n  - ".join(violations)
            )


# --------------------------------------------------------------------------- #
# The FC-7 provenance artifact writer
# --------------------------------------------------------------------------- #
def write_run_config(out_dir: Path, run_dir: "Path | None", **extra) -> "Path | None":
    """Write ``<out_dir>/run_config.json`` from the RUN'S OWN resolved config.

    **Why this exists (FFR-3A blocker 7).** ``forecast_verdict.score_fc7`` row 1
    requires a ``run_config`` artifact with a full ``ScenarioConfig`` flag
    surface, and the full-horizon runner wrote only the cache's ``config.yaml``
    — so **no bundle it produced could pass FC-7 provenance**: the row read
    "run_config.json absent" and FAILed by construction, on every T1-F leg, for
    reasons having nothing to do with the run. FF-2D worked around it with a
    scoring-time helper (``scripts/_ff2d_emit_run_config.py``); that keeps the
    producer broken and puts artifact authorship next to the score.

    **One writer, every runner (FFR-3K).** Moved here VERBATIM from
    ``scripts/run_full_horizon.py`` (where FFR-3D ``34c2f25`` introduced it and
    ``ea7cd5d`` fixed its call-site binding) so the capacity-hindcast harness —
    whose T1-H / T1-X / T1-FF bundles carried the exact same defect — emits the
    same artifact through the same implementation, not a second one.

    **Provenance, which is the whole point.** The payload's ``scenario_config``
    is the cache directory's own ``config.yaml``, read VERBATIM — the dump
    ``results.cache.save_result`` wrote from the config the solve actually ran.
    That is deliberately NOT the object handed to the runner:
    ``runner.run_scenario_iso`` re-binds the ISO, applies
    ``resolve_policy_bundle`` and may apply per-ISO overrides, so the pre-solve
    object is a REQUEST and the on-disk dump is the RESOLUTION. Recording the
    request would be exactly the rule-24 divergence FC-7 is meant to detect. No
    value is reconstructed, normalized, or defaulted here.

    Returns ``None`` — writing nothing — when there is no resolved dump to read
    (a zero-year run, a solve that raised before its first save). A run that
    produced no years has no provenance to record, and FC-7 FAILing on it is the
    truthful verdict; fabricating a config from the request would manufacture a
    pass. Rubric §4 forbids authoring an artifact to move a score, and this
    lands BEFORE the next scoring battery precisely so the instrument is fixed
    rather than the number.

    Args:
        out_dir: Directory to write ``run_config.json`` into (beside the
            summary/meta, where ``forecast_verdict --run-config`` expects it).
        run_dir: The solve's cache directory, or ``None`` if it never resolved.
        **extra: Additional top-level keys recorded verbatim (``iso``,
            ``cache_key``, ``solved_years`` …).

    Returns:
        The path written, or ``None``.
    """
    if run_dir is None:
        return None
    cfg_yaml = Path(run_dir) / "config.yaml"
    if not cfg_yaml.exists():
        return None
    import yaml

    # Lazy: keeps this module importable without src/ on sys.path (the
    # config_field_names precedent); both callers already have it there.
    from market_sim.pipeline.persist import environment_block, git_state

    resolved = yaml.safe_load(cfg_yaml.read_text())
    if not isinstance(resolved, dict) or not resolved:
        return None
    payload = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git": git_state(),
        # Names the file this was taken from, so a reader can re-verify the
        # provenance claim above rather than trust it.
        "scenario_config_source": str(cfg_yaml),
        "scenario_config": resolved,
        # Recorded here, from the positional argument, so a caller never has to
        # pass it again through **extra — doing so collides with this
        # function's own parameter name and raises TypeError at bind time.
        "run_dir": str(run_dir),
        "environment": environment_block(),
        **extra,
    }
    path = Path(out_dir) / "run_config.json"
    path.write_text(json.dumps(payload, indent=2, default=str) + "\n")
    return path

"""Parameter-sweep / named-case-matrix expansion for :class:`ScenarioConfig`.

Extracted verbatim from ``config.scenarios`` (refactor-consolidation plan
2026-07 §5 item 9 — code motion only). ``config.scenarios`` re-exports
:class:`SweepDefinition`, so the historical
``from market_sim.config.scenarios import SweepDefinition`` spelling keeps
working (pinned by ``tests/test_scenarios_facade.py``). ``ScenarioConfig`` is
imported lazily inside the expansion methods: ``config.scenarios`` imports
this module at module level for the re-export, so a module-level back-import
would be an import-time cycle (tests/test_persisted_identity.py AST guard).
``SweepDefinition`` is not pickle-borne — only ``ScenarioConfig``'s module
path is frozen (plan §1) — so defining it here is safe.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from market_sim.config.scenarios import ScenarioConfig


@dataclass
class SweepDefinition:
    """A parameter sweep, or a named-case matrix, expanding into ``ScenarioConfig``\\ s.

    Two mutually-exclusive expansion modes, gated on which mapping is
    non-empty:

    - ``sweep``: the original cartesian mode — a ``{field: [values]}`` mapping
      expands to every combination (``len(values_1) x len(values_2) x ...``
      configs).
    - ``cases``: the PB-1 named-case mode (probability-bounds-plan-2026-07.md
      §1.3) — a ``{case_name: {field: value}}`` mapping expands to exactly one
      config per named case, e.g. the 13-case AEO/IPM-style scenario matrix in
      ``configs/scenario_matrix.yaml``. Unlike ``sweep``, case identity
      (the name) is preserved via :meth:`case_configs` so downstream output
      (the scenario-matrix trajectory table) can label each member.

    Both modes expand *onto* an optional ``base_config`` (every existing
    field of the base is carried through unchanged except the named
    overrides), defaulting to ``ScenarioConfig()`` when none is given —
    reusing this one engine for both the sweep CLI (no base) and the matrix
    CLI (explicit ``--config`` base), per PP-1.1's instruction not to write a
    second sweep engine.
    """

    sweep: dict[str, list] = field(default_factory=dict)
    cases: dict[str, dict] = field(default_factory=dict)
    mode: str = "factorial"

    def __post_init__(self) -> None:
        """Reject a definition that sets both expansion modes at once."""
        if self.sweep and self.cases:
            raise ValueError(
                "SweepDefinition.sweep and SweepDefinition.cases are "
                "mutually exclusive -- a sweep/matrix file must use one "
                "expansion mode, not both"
            )

    def generate(
        self, base_config: ScenarioConfig | None = None
    ) -> list[ScenarioConfig]:
        """Expand into a list of configs (cartesian ``sweep``, or ``cases`` in order).

        Args:
            base_config: Config every expanded member overrides onto.
                Defaults to ``ScenarioConfig()``.
        """
        from market_sim.config.scenarios import ScenarioConfig

        base = base_config if base_config is not None else ScenarioConfig()
        if self.cases:
            return list(self.case_configs(base).values())
        if not self.sweep:
            return [base]
        names = list(self.sweep.keys())
        value_lists = [self.sweep[name] for name in names]
        configs = []
        for combo in itertools.product(*value_lists):
            overrides = dict(zip(names, combo))
            configs.append(base.with_overrides(**overrides))
        return configs

    def case_configs(
        self, base_config: ScenarioConfig | None = None
    ) -> dict[str, ScenarioConfig]:
        """Expand ``cases`` into ``{case_name: config}``, preserving YAML order.

        Args:
            base_config: Config every named case overrides onto. Defaults to
                ``ScenarioConfig()``.

        Raises:
            ValueError: If ``cases`` is empty (this definition is a ``sweep``,
                not a named-case matrix).
        """
        from market_sim.config.scenarios import ScenarioConfig

        if not self.cases:
            raise ValueError(
                "case_configs requires a non-empty 'cases' mapping; this "
                "SweepDefinition has none (it may be a cartesian 'sweep')"
            )
        base = base_config if base_config is not None else ScenarioConfig()
        return {
            name: base.with_overrides(**overrides)
            for name, overrides in self.cases.items()
        }

    @classmethod
    def from_yaml(cls, path) -> "SweepDefinition":
        """Load a sweep or named-case matrix definition from a YAML file."""
        data = yaml.safe_load(Path(path).read_text()) or {}
        return cls(
            sweep=data.get("sweep", {}),
            cases=data.get("cases", {}),
            mode=data.get("mode", "factorial"),
        )

"""Typed cross-year forecast state (``PriorYearResults``).

Replaces the untyped ``prior_results`` dict that ``runner.py``'s year loop
builds at the end of each year and threads into the next year's capacity
evolution (audit AR-2). One field per current dict key; the producer is
``runner.py`` (the ``prior_results = {...}`` assembly) and the consumers are
``runner.py``'s next-iteration reads and ``capacity.evolve_fleet`` /
``apply_storage_new_entry``.

``evolve_fleet`` already reads through a ``_prior_attr`` helper that accepts a
dict *or* an object (``getattr`` fallback), so a typed instance drops in with no
change to its internals. For the remaining dict-style readers in ``runner.py``
(``prior_results["prices"]``, ``prior_results.get("rps_shadow_price")``, …) this
class provides :meth:`get` and :meth:`__getitem__` shims with exact
``dict``-matching semantics. No value change — this stage retypes the container.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np

    from market_sim.data.fleet import FleetArrays
    from market_sim.model.dispatch import DispatchResult


@dataclass
class PriorYearResults:
    """Prior-year solve outcome threaded across the forecast year loop.

    Fields mirror the keys of the ``prior_results`` dict assembled in
    ``runner.py`` one-to-one (types taken from the actual producers). The
    ``.get`` / ``__getitem__`` shims let every existing dict-style reader keep
    working unchanged during the migration.
    """

    fleet_arrays: "FleetArrays"
    dispatch_result: "DispatchResult"
    prices: "np.ndarray"
    peak_demand: float
    planned_additions: list
    mc_cost: "np.ndarray"
    rps_shadow_price: float
    retrofit_log: list[dict]
    storage_power_mw: float
    # Endogenous AS-revenue rates DERIVED from this year's co-opt reserve duals
    # (0.0 / None when the co-opt did not price reserve this year). Consumed by
    # next year's storage-entry and retirement/new-entry screens.
    storage_as_revenue_per_mw_yr: float
    thermal_as_revenue_per_mw_yr: dict | None
    wind_cap_mw: float
    solar_cap_mw: float
    storage_firm_mw: float
    # Price signal the capacity screens (retirement / new entry / storage
    # entry) consume in place of raw ``prices`` — the EWMA-blended and/or
    # lookahead-repriced series (capacity-economics plan 2026-07 §2.2-§2.3).
    # At the defaults (alpha=1.0, lookahead off) the runner passes the same
    # ``econ_prices`` array object, so behaviour is byte-identical. ``None``
    # (e.g. older tests building bare dicts) falls back to ``prices``.
    price_signal: "np.ndarray | None" = None
    # Reserve-price signal for the capacity screens (capacity-economics plan
    # 2026-07 §5 step 2): the hourly $/MWh a reserve-eligible unit can earn
    # holding reserve instead of selling energy. Two eligibility tiers,
    # mirroring the co-opt's headroom cascade / ERCOT's RTORPA-vs-RTOFFPA
    # split: ``reserve_price_signal`` is the synchronized (all-products) tier;
    # ``reserve_price_signal_slow`` is the offline quick-start (Non-Spin)
    # tier. Populated by the runner from the co-opt's own reserve duals
    # (under ercot_thermal_as_endogenous) or the post-solve ORDC scarcity
    # adder; ``None`` (screen_reserve_value_enabled off / neither mechanism
    # active) keeps the screens on the legacy annual AS credits.
    reserve_price_signal: "np.ndarray | None" = None
    reserve_price_signal_slow: "np.ndarray | None" = None
    # Zonal hourly renewable CF profiles ((n_zones, T), rows ordered as
    # ``zone_names``) so the VRE new-entry screen values a candidate's actual
    # capture shape against its build zone's prices instead of a flat mean
    # (capacity-economics plan §6 CX-6c — shape-aware entry revenue). ``None``
    # falls back to the scalar base-CF screen.
    zone_names: "list[str] | None" = None
    wind_cf: "np.ndarray | None" = None
    solar_cf: "np.ndarray | None" = None

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-style read with ``dict.get`` semantics.

        Returns the field value for ``key``, or ``default`` when ``key`` is not
        one of the defined fields.
        """
        if key in self._field_names():
            return getattr(self, key)
        return default

    def __getitem__(self, key: str) -> Any:
        """Dict-style item access; raises ``KeyError`` for unknown keys."""
        if key in self._field_names():
            return getattr(self, key)
        raise KeyError(key)

    def __contains__(self, key: str) -> bool:
        """Support ``key in prior_results`` for dict-style membership tests."""
        return key in self._field_names()

    @classmethod
    def _field_names(cls) -> frozenset[str]:
        """The set of defined field names (cached per class)."""
        cached = cls.__dict__.get("_FIELD_NAMES")
        if cached is None:
            cached = frozenset(f.name for f in fields(cls))
            cls._FIELD_NAMES = cached  # type: ignore[attr-defined]
        return cached

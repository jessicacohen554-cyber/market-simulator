"""The ONE reader of the shipped capacity-price posture (owner decision C.4(a) B1).

**The failure this prevents.** ``ScenarioConfig.capacity_market_clearing_by_iso``
is the shipped per-ISO capacity-clearing posture — the field the production
forecast actually runs. Before this module three surfaces answered "what posture
does production ship?" independently:

* ``run_capacity_hindcast.production_capacity_clearing_default`` — read the live
  dataclass default (FFR-2E, audit FR-14; the correct pattern);
* ``ff_readiness_battery.GOLDEN_CMC_BY_ISO`` — a hand-maintained parallel dict;
* ``run_full_horizon.reference_config(golden_posture=True)`` — imported that dict.

The two answers had already diverged on **NYISO**: the shipped field deliberately
omits it ("curve-eligible but its train-tier determination is NOT-YET … excluded
pending re-calibration" ⇒ gate OFF), while ``GOLDEN_CMC_BY_ISO`` carried
``NYISO: True``. So every ``--golden-posture`` T1-F leg solved NYISO curve-ON
against a production path that runs it curve-OFF — audit FR-14 in a second
costume, and the same class of divergence FFR-2E measured for the hindcast lane.

The owner signed **SINGLE SOURCE OF TRUTH** on 2026-08-03
(``docs/handoffs/ffr-owner-sitting-2026-08-02.md`` Addendum D.1): "Every runner
reads the shipped ``ScenarioConfig`` capacity-price posture field directly; the
parallel ``GOLDEN_CMC_BY_ISO`` constant stops being a second answer. NYISO must
resolve curve-OFF, matching production." ``GOLDEN_CMC_BY_ISO`` was deleted
outright rather than corrected in place (rule 26 ``[R-DELETE]``: a second answer
that still parses is a re-armable second answer).

Rule 24 ``[R-REGISTRY]``: the posture lives in ``ScenarioConfig`` and nowhere
else. This module reads it; it never defines it.
"""

from __future__ import annotations

from dataclasses import MISSING

from market_sim.config.capacity_market import resolve_capacity_market_clearing
from market_sim.config.scenarios import ScenarioConfig

__all__ = [
    "shipped_capacity_clearing_by_iso",
    "shipped_capacity_clearing",
]


def shipped_capacity_clearing_by_iso() -> dict[str, bool] | None:
    """Return the SHIPPED ``capacity_market_clearing_by_iso`` default.

    Read off the ``ScenarioConfig`` dataclass field rather than copied, so an
    owner flip of the production posture is followed by every runner with no
    edit — a hardcoded mirror is a second, silently-diverging tuning channel
    (rule 24).

    Returns a fresh ``dict`` (never the shared default object, so one caller's
    mutation cannot leak into the next config built in the same process), or
    ``None`` when the field carries a plain default rather than a
    ``default_factory``.
    """
    spec = getattr(ScenarioConfig, "__dataclass_fields__", {}).get(
        "capacity_market_clearing_by_iso"
    )
    factory = getattr(spec, "default_factory", None) if spec is not None else None
    if factory is None or factory is MISSING:
        return None
    return dict(factory())


def shipped_capacity_clearing(iso: str) -> bool:
    """Whether production ships ``iso`` curve-ON, through the one resolver seam.

    Resolves the shipped per-ISO mapping the same way a solve does
    (``capacity_market.resolve_capacity_market_clearing``), so an ISO absent
    from the mapping falls through to the scalar exactly as it would in the
    model — NYISO and ERCOT resolve ``False`` here for that reason, not by a
    special case.

    Args:
        iso: Model ISO name.

    Returns:
        The resolved clearing gate production ships for ``iso``.
    """
    cfg = ScenarioConfig(iso=iso.upper(), mode="forecast")
    return bool(resolve_capacity_market_clearing(cfg, iso.upper()))

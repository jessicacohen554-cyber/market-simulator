"""Fail-fast guard: an ARMED mechanism whose derived CLEAN partition is absent.

``data/clean`` is derived-and-disposable (gitignored), so it does not travel
with the repo — every environment regenerates the partitions its recipe needs
from ``data/raw`` via the ``scripts/data/curate_*.py`` scripts. Several gated
mechanisms consume such a partition, and their loaders were written to *degrade
gracefully*: an absent partition logs a warning and the mechanism silently
becomes a no-op. That is the right behaviour for a loader and the wrong
behaviour for a solve, because the resulting run advertises a mechanism in its
``run_config``/``meta`` that never actually ran.

**caiso-157 is the incident this module exists to prevent.** The CAISO
``hydro-plant-modes`` and ``capacity-deliverability`` partitions went missing
between two sessions and the degradation went unnoticed across five keeper
promotions (caiso-146/147/148/151/153). The deliverability half was the
expensive one: with Part A a no-op the CAISO import node falls back to the
hard-coded ``WECC_import_simultaneous`` cap of 7,500 MW — a
*residual-identified* scalar that the keeper's own DOF ledger records as
"``Not in the keeper binding path``" and that ``iso_configs`` carries expressly
"so this fallback cannot silently re-become the binding import limit". It was
binding in 5-10 % of every keeper year. Rules 20 ``[R-DOF]`` and 24
``[R-REGISTRY]``: a retired fitted value that can silently re-arm itself is an
off-registry tuning channel, whatever the intent.

The guard carries **no ScenarioConfig field, no threshold and no tunable** — it
is a pure consistency assertion between what a config claims and what is on
disk — and it is ISO-generic. It fires only when a flag is armed *and* the
partition the flag requires is absent *and* the ISO is one for which that
partition is expected; a flag left at its default never reaches it, so the
whole default-off surface is untouched.

Scope is deliberately narrow: the two mechanisms caiso-157 proves. Widening it
to other armed-flag/partition pairs is filed, not absorbed — each addition owes
a check that "partition absent" is genuinely distinguishable from a legitimate
ISO-level no-op (as it is for both entries here).
"""

from __future__ import annotations

import logging
from typing import Callable

logger = logging.getLogger(__name__)


class DegradedInputError(RuntimeError):
    """An armed mechanism's derived CLEAN partition is missing from disk.

    Raised before the LP is solved so the run fails loudly instead of
    producing a bundle whose ``meta`` advertises a mechanism that never ran.
    """


def _capacity_deliverability_absent(iso: str) -> bool:
    """Return whether the ISO's ``capacity-deliverability`` partition is missing.

    ``False`` for an ISO that publishes no locational RA construct at all
    (ERCOT), because there the empty read is the correct, permanent answer
    rather than a missing-file condition.
    """
    from market_sim.data import capacity_deliverability as capdel

    return capdel.partition_expected(iso) and capdel.partition_available(iso) is False


def _hydro_plant_modes_absent(iso: str) -> bool:
    """Return whether the ISO's ``hydro-plant-modes`` partition is missing.

    There is no ISO for which arming the RoR split without a classifier is
    correct: the mechanism *is* the classifier, so an absent partition is
    always the degraded state.
    """
    from market_sim.data.hydro_modes import load_hydro_shapeable

    return load_hydro_shapeable(iso) is None


#: ``config`` flag -> (clean datatype, curate script, absence probe). The probe
#: takes the model ISO name and returns True when the partition the armed flag
#: requires is missing from ``data/clean``.
_PARTITION_REQUIREMENTS: dict[str, tuple[str, str, Callable[[str], bool]]] = {
    "capacity_deliverability_limits": (
        "capacity-deliverability",
        "scripts/data/curate_capacity_deliverability.py",
        _capacity_deliverability_absent,
    ),
    "hydro_ror_split": (
        "hydro-plant-modes",
        "scripts/data/curate_hydro_plant_modes.py",
        _hydro_plant_modes_absent,
    ),
}


def check_clean_partitions(config, iso: str) -> None:
    """Raise when an armed mechanism's required CLEAN partition is absent.

    Args:
        config: The resolved ``ScenarioConfig`` for the run.
        iso: Model ISO name (e.g. ``"CAISO"``, ``"NEISO"``).

    Raises:
        DegradedInputError: One or more armed mechanisms have no data. The
            message names every offender and the curate script that rebuilds
            it, so the fix is a copy-pasteable command rather than a hunt.
    """
    missing: list[tuple[str, str, str]] = []
    for flag, (datatype, script, absent) in _PARTITION_REQUIREMENTS.items():
        if not bool(getattr(config, flag, False)):
            continue
        try:
            degraded = absent(iso)
        except Exception:  # a probe must never be the reason a solve dies
            logger.warning(
                "input-completeness probe for %s failed; not treating as degraded",
                flag,
                exc_info=True,
            )
            continue
        if degraded:
            missing.append((flag, datatype, script))

    if not missing:
        return

    lines = [
        f"{iso}: {len(missing)} armed mechanism(s) have no derived CLEAN data, "
        "so they would silently no-op and the run would advertise a mechanism "
        "that never ran:",
    ]
    lines += [
        f"  - {flag} needs data/clean/{datatype}/{iso.upper()} — rebuild with "
        f"`PYTHONPATH=. python {script}`"
        for flag, datatype, script in missing
    ]
    lines.append(
        "data/clean is derived and gitignored, so a fresh container starts "
        "empty; regenerate the partitions this recipe consumes before solving "
        "(`python scripts/regenerate_clean.py` rebuilds the whole tree). "
        "(caiso-157: an absent partition re-armed a retired fitted import "
        "scalar across five keeper promotions — rules 20/24.)"
    )
    raise DegradedInputError("\n".join(lines))

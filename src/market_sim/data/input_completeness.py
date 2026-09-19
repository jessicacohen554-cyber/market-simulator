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

Each addition owes a check that "partition absent" is genuinely
distinguishable from a legitimate ISO-level no-op (as it is for every entry
here).

**caiso-190 widened the guard in three ways**, after caiso-188 measured the
same defect class recurring on the designated CAISO keeper
(``FINDING-caiso188-import-tranche-dof-2026-08-09.md`` §4-§7):

1. **Both solve paths call it.** caiso-157 wrote the guard but its only call
   site was ``pipeline/year.py::run_year_solve``, a function with no
   production caller — so it had never once run in a solve while its unit
   tests kept it green in CI. caiso-188 wired the backcast lane
   (``scripts/run_calibration.py``); caiso-190 wires the forecast orchestrator
   (``src/market_sim/runner.py``), which had the same silent-degradation
   surface and no guard call.
2. **Per-requirement severity.** A mechanism with **no defined fallback**
   (``hydro_ror_split`` — the classifier *is* the mechanism) fails fast in
   every mode. A mechanism with a **declared fallback**
   (``capacity_deliverability_limits`` falls back to the baked
   ``WECC_import_simultaneous`` scalar) fails fast in **strict** mode and
   otherwise warns loudly — and either way the resolved outcome is persisted
   by :mod:`market_sim.data.resolved_inputs`, so "which cap did this bundle
   solve against?" is answerable from committed artifacts alone.
3. **Strict is the DEFAULT**, so the calibration lane keeps caiso-188's
   fail-fast behaviour unchanged and a caller must opt *out* deliberately. The
   forecast orchestrator is the one caller that does: a forecast run that
   degrades to a declared fallback is loud but not fatal, because it is not
   the lane a keeper is promoted from.

The guard still carries **no ScenarioConfig field, no threshold and no
tunable** — ``strict`` is a call-site property of the lane, not a knob a
scenario can set — so it remains a pure consistency assertion between what a
config claims and what is on disk.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

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


def _campd_unit_outages_absent(iso: str) -> bool:
    """Return whether the ISO's CAMPD unit-outage extract is missing.

    Unlike the two clean partitions this extract is COMMITTED under
    ``data/raw``, so its absence is an environment condition (a sparse
    checkout that excluded ``data/raw``) rather than the caiso-157 "no solve
    builds it" class. The degradation is identical, though:
    ``_load_unit_outage_events`` returns ``None``, ``unit_outage_derate_
    factors`` returns ``{}``, and the historic overlay the config asked for
    silently becomes no overlay at all.
    """
    from market_sim.data.outages import unit_outage_csv_for_iso

    return not unit_outage_csv_for_iso(iso).exists()


def _coal_fuel_inventory_absent(iso: str) -> bool:
    """Return whether the coal fuel-inventory budget's CLEAN partitions are missing.

    The mechanism needs BOTH halves — ``coal-stocks`` for the opening stock and
    ``coal-receipts`` for the prior-years delivery rate — and
    :func:`market_sim.data.coal_fuel_inventory.build_coal_fuel_budget` returns
    ``None`` if either resolves empty, which appends ZERO rows and leaves the
    LP identical to an unarmed run. Either half missing is therefore the
    degraded state.

    There is no ISO for which arming this without the partitions is correct:
    ``scripts/run_calibration.py`` already refuses the flag outside MISO (rule
    25 ``[R-ISO-SCOPE]``) and outside backcast mode, so an empty read here is
    never a legitimate ISO-level no-op the way ERCOT's absent locational RA
    construct is. The ``iso`` argument is accepted for the registry's uniform
    signature and deliberately unused — these are national EIA-923 partitions.
    """
    from market_sim.data.coal_receipts import load_coal_receipts
    from market_sim.data.coal_stocks import load_coal_stocks

    return load_coal_stocks().empty or load_coal_receipts().empty


def _historic_outages_armed(config) -> bool:
    """Return whether the run asked for the measured CAMPD outage overlay.

    ``outage_source`` is a STRING axis rather than a bool flag, so this
    requirement cannot key off ``getattr(config, flag)`` truthiness the way the
    other two do — hence the per-requirement ``armed`` callable.
    """
    return str(getattr(config, "outage_source", "") or "").lower() == "historic"


@dataclass(frozen=True)
class PartitionRequirement:
    """One armed-mechanism / required-data pair, and what absence means.

    Attributes:
        flag: The ``ScenarioConfig`` field that arms the mechanism. Also the
            name used in the failure message, so it is copy-pasteable into a
            config.
        datatype: The on-disk datatype the mechanism resolves through.
        location: Human-readable path template naming where it should be.
        build_command: The copy-pasteable command that materialises it.
        armed: ``config -> bool``. Defaults to the truthiness of ``flag``.
        absent: ``iso -> bool``. True when the data the armed mechanism needs
            is missing. Must distinguish "absent" from a legitimate ISO-level
            no-op (e.g. energy-only ERCOT publishes no locational RA
            construct, so an empty read there is the permanent right answer).
        fallback: What the LP silently falls back to when the data is absent,
            or ``None`` when the mechanism has **no defined fallback**. This
            is the severity switch: ``None`` fails fast in every mode, a
            declared fallback fails fast only in strict mode.
    """

    flag: str
    datatype: str
    location: str
    build_command: str
    absent: Callable[[str], bool]
    fallback: str | None = None
    armed: Callable[[Any], bool] | None = None

    def is_armed(self, config) -> bool:
        """Return whether ``config`` arms this mechanism."""
        if self.armed is not None:
            return bool(self.armed(config))
        return bool(getattr(config, self.flag, False))


#: The flag -> required-data registry. ADDITIVE by design: a new mechanism that
#: resolves through disposable data appends one entry here and inherits the
#: whole guard, on both solve paths, with no call-site change.
_PARTITION_REQUIREMENTS: tuple[PartitionRequirement, ...] = (
    PartitionRequirement(
        flag="capacity_deliverability_limits",
        datatype="capacity-deliverability",
        location="data/clean/capacity-deliverability/<ISO>",
        build_command="PYTHONPATH=. python scripts/data/curate_capacity_deliverability.py",
        absent=_capacity_deliverability_absent,
        # The baked WECC_import_simultaneous scalar (7,500 MW for CAISO) — a
        # RESIDUAL-IDENTIFIED fitted value that governs whenever Part A does
        # not resolve. Declared, so a non-strict lane warns; strict refuses,
        # because a keeper that solved on it while advertising the published
        # MIC is precisely the caiso-188 defect.
        fallback="the baked simultaneous-import cap (a fitted scalar)",
    ),
    PartitionRequirement(
        flag="hydro_ror_split",
        datatype="hydro-plant-modes",
        location="data/clean/hydro-plant-modes/<ISO>",
        build_command="PYTHONPATH=. python scripts/data/curate_hydro_plant_modes.py",
        absent=_hydro_plant_modes_absent,
        # NO fallback: the classifier IS the mechanism, so an absent partition
        # leaves the LP simply unchanged. Fails fast in every mode.
        fallback=None,
    ),
    PartitionRequirement(
        flag="outage_source",
        datatype="campd-unit-outages",
        location="data/raw/campd-unit-outages-<ISO>.csv",
        build_command=(
            "PYTHONPATH=. python scripts/data/derive_campd_unit_outages.py --iso <ISO>"
        ),
        absent=_campd_unit_outages_absent,
        armed=_historic_outages_armed,
        # Declared: an absent extract degrades to the statistical availability
        # the model uses when no measured overlay is supplied.
        fallback="statistical availability (no measured outage overlay)",
    ),
    PartitionRequirement(
        flag="coal_fuel_inventory",
        datatype="coal-stocks + coal-receipts",
        location="data/clean/coal-stocks/ and data/clean/coal-receipts/",
        build_command=(
            "PYTHONPATH=. python scripts/data/curate_coal_stocks.py && "
            "PYTHONPATH=. python scripts/data/curate_coal_receipts.py"
        ),
        absent=_coal_fuel_inventory_absent,
        # NO fallback, the hydro_ror_split severity class: an absent partition
        # makes build_coal_fuel_budget return None, which appends ZERO budget
        # rows and leaves coal with floors and no ceiling at all — the exact
        # state the mechanism was built to remove. Fatal in every mode.
        #
        # miso-263 is the incident this entry exists to prevent, and it is
        # caiso-157 again one mechanism over. The MISO keeper
        # 2026-09-19-miso-262-cold-year was composed from six per-year shard
        # bundles solved in fresh containers that had hydrated data/raw but
        # never run the two curate scripts above. Each leg recorded
        # `coal_fuel_inventory: true` in its run_config, logged the loader's
        # own "NOT APPLIED" warning, and solved with no coal budget. The
        # resulting dispatch VIOLATES the cap its own config declares in 7/12
        # months of 2022 (+33.17 TWh of coal above the most any feasible
        # dispatch could deliver under the row), 4/12 of 2021 and 3/12 of
        # 2025 — the three years, and only those three, that the superseded
        # warm keeper had bound in. That +34.7 TWh of freed coal was read as
        # a better optimum and promoted (docs/RESULT-miso263-*).
        fallback=None,
    ),
)


def check_clean_partitions(config, iso: str, *, strict: bool = True) -> None:
    """Refuse (or warn about) an armed mechanism whose required data is absent.

    Called before the LP is built on **both** solve paths — the backcast
    orchestrator (``scripts/run_calibration.py::run_year``, wired at
    caiso-188) and the forecast orchestrator
    (``market_sim.runner.run_scenario_iso``, wired at caiso-190).

    Args:
        config: The resolved ``ScenarioConfig`` for the run.
        iso: Model ISO name (e.g. ``"CAISO"``, ``"NEISO"``).
        strict: When ``True`` (the default, and what the calibration lane
            uses), a missing partition is fatal even where a fallback is
            declared — no keeper may solve on the wrong cap. When ``False``,
            only mechanisms with **no** defined fallback are fatal; a declared
            fallback warns loudly instead, and the outcome it produced is
            recorded by :mod:`market_sim.data.resolved_inputs`.

    Raises:
        DegradedInputError: One or more armed mechanisms have no data, at a
            severity this mode treats as fatal. The message names every
            offender and the command that rebuilds it, so the fix is
            copy-pasteable rather than a hunt.
    """
    fatal: list[PartitionRequirement] = []
    degraded_with_fallback: list[PartitionRequirement] = []
    unverifiable: list[tuple[PartitionRequirement, Exception]] = []
    for req in _PARTITION_REQUIREMENTS:
        if not req.is_armed(config):
            continue
        try:
            degraded = req.absent(iso)
        except Exception as exc:
            # caiso-190: a probe that RAISES is not evidence of health. A
            # partition present but unreadable (wrong schema, truncated
            # parquet, missing datatype metadata) degrades the mechanism
            # exactly as absence does — the loader returns nothing and the LP
            # is unchanged. Treating that as "fine" was itself an instance of
            # the silent-no-op class: it is how
            # test_input_completeness.py::test_present_partitions_pass came to
            # pass while BOTH its fixtures raised SchemaError, so the
            # partition-present leg of the guard was never actually exercised.
            # Fail CLOSED in strict mode (the same discipline rule 22 applies
            # to an unrecognised holdout year); stay loud but non-fatal on a
            # lane no keeper is promoted from.
            unverifiable.append((req, exc))
            continue
        if not degraded:
            continue
        if req.fallback is None or strict:
            fatal.append(req)
        else:
            degraded_with_fallback.append(req)

    for req, exc in unverifiable:
        logger.warning(
            "%s: %s is ARMED but its %s probe FAILED (%r) — the mechanism's "
            "data could not be verified, and an unreadable partition no-ops "
            "the mechanism exactly as an absent one does. Rebuild with `%s`.",
            iso,
            req.flag,
            req.datatype,
            exc,
            req.build_command.replace("<ISO>", iso.upper()),
            exc_info=not strict,
        )

    for req in degraded_with_fallback:
        logger.warning(
            "%s: %s is ARMED but %s is absent (%s) — the solve will fall back "
            "to %s and the mechanism will NOT run. Rebuild with `%s`. The "
            "resolved outcome is recorded in run_config.json's resolved_inputs "
            "block (caiso-190); a calibration run would refuse this outright.",
            iso,
            req.flag,
            req.datatype,
            req.location.replace("<ISO>", iso.upper()),
            req.fallback,
            req.build_command.replace("<ISO>", iso.upper()),
        )

    if not fatal and not (strict and unverifiable):
        return

    lines = [
        f"{iso}: {len(fatal) + len(unverifiable) * bool(strict)} armed "
        "mechanism(s) have no usable input data, so they would silently no-op "
        "and the run would advertise a mechanism that never ran:",
    ]
    if strict:
        for req, exc in unverifiable:
            lines.append(
                f"  - {req.flag} needs "
                f"{req.location.replace('<ISO>', iso.upper())}, which is "
                f"present but UNREADABLE ({exc!r}) — rebuild with "
                f"`{req.build_command.replace('<ISO>', iso.upper())}`"
            )
    for req in fatal:
        detail = (
            f"falls back to {req.fallback}"
            if req.fallback is not None
            else "has NO fallback — the mechanism simply would not run"
        )
        lines.append(
            f"  - {req.flag} needs {req.location.replace('<ISO>', iso.upper())} "
            f"({detail}) — rebuild with "
            f"`{req.build_command.replace('<ISO>', iso.upper())}`"
        )
    if strict and any(req.fallback is not None for req in fatal):
        lines.append(
            "STRICT mode (the calibration lane): a DECLARED fallback is fatal "
            "here too, because a keeper that solved on the fallback while its "
            "run_config advertised the published input is the caiso-188 "
            "defect. Pass strict=False only on a lane no keeper is promoted "
            "from."
        )
    lines.append(
        "data/clean is derived and gitignored, so a fresh container starts "
        "empty; regenerate the partitions this recipe consumes before solving "
        "(`python scripts/regenerate_clean.py` rebuilds the whole tree). "
        "(caiso-157: an absent partition re-armed a retired fitted import "
        "scalar across five keeper promotions — rules 20/24. caiso-188: it "
        "recurred on the designated keeper because the guard was never wired "
        "to a solve path.)"
    )
    raise DegradedInputError("\n".join(lines))

"""Shared transmission/TTC assembly for the per-year solve (both orchestrators).

Orchestrator-unification lane (refactor-consolidation plan §5): the base
transmission arrays every per-year LP consumes — the incidence matrix, the
link TTC array, and the aggregate interface groups — were assembled with the
same three calls in both ``runner.py`` (forecast) and
``scripts/run_calibration.py::run_year`` (backcast). :func:`build_transmission_base`
is that assembly, hoisted once.

The **measured backcast TTC overlays** stay backcast-only (CLAUDE.md rule 13 /
plan §3.1): the year-varying NYISO interface table, the monthly Central-East
envelope, and the CLI link-TTC overrides are *applied by the backcast
front-end on top of the base arrays* via the helpers below (moved verbatim
from ``run_calibration.py``; the script keeps same-name ``_``-prefixed
aliases). The forecast orchestrator never calls them, so no measured overlay
is reachable from a forecast run — the divergence is a call-site decision at
the front-end, exactly like every other rule-13 overlay after unification.
"""

from __future__ import annotations

import logging

import numpy as np

from market_sim.config.constants import (
    NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_MONTH,
    NYISO_INTERFACE_TTC_BY_YEAR,
)
from market_sim.model.transmission import (
    build_incidence_matrix,
    build_interface_groups,
    get_ttc_array,
)

logger = logging.getLogger(__name__)

__all__ = [
    "TTC_LINK_ZONES",
    "build_transmission_base",
    "apply_ttc_overrides",
    "apply_iso_year_ttc",
    "apply_iso_monthly_ttc",
    "apply_nwpp_path76_link",
]

# Zone-pair identifying each transfer link whose TTC the calibration CLI can
# override. Both legs of the West Texas Export interface and the Panhandle GTC
# are exposed for tuning — these are ERCOT's primary wind-export constraints.
TTC_LINK_ZONES: dict[str, frozenset[str]] = {
    "ttc_wn": frozenset({"West", "North"}),
    "ttc_wsc": frozenset({"West", "South_Central"}),
    "ttc_pn": frozenset({"Panhandle", "North"}),
}


def build_transmission_base(iso_config, zone_names):
    """Return ``(incidence, ttc, interface_groups)`` for a finalized topology.

    The shared base assembly both orchestrators run once the ISO topology is
    final (i.e. after ``apply_interchange_topology`` has extended the import
    node / split per-hub corridors):

    * ``incidence`` — the ``(n_zones, n_links)`` incidence matrix.
    * ``ttc`` — the static ``(n_links,)`` transfer-capability array.
    * ``interface_groups`` — aggregate interface limits (e.g. CAISO's
      simultaneous WECC import cap) resolved to flow-column groups; empty for
      ISOs without an ``interface_limits`` entry, so the LP is identical there.

    Mode-specific adjustments (measured backcast TTC overlays, the forecast's
    forward-ATC corridor cap, per-year CAISO import caps) are applied by each
    front-end on top of these base arrays.

    Args:
        iso_config: The finalized ISO topology (links + interface limits).
        zone_names: Solve zone list, aligned with the topology.

    Returns:
        ``(incidence, ttc, interface_groups)``.
    """
    incidence = build_incidence_matrix(iso_config.links, zone_names)
    ttc = get_ttc_array(iso_config.links)
    interface_groups = build_interface_groups(
        iso_config.links, iso_config.interface_limits
    )
    return incidence, ttc, interface_groups


def apply_ttc_overrides(
    iso_config, ttc: np.ndarray, overrides: dict[str, float | None]
) -> np.ndarray:
    """Return ``ttc`` with the requested link capabilities overridden.

    Backcast-only CLI tuning channel (the ERCOT wind-export links).

    Args:
        iso_config: The ISO topology, used to map links to zone pairs.
        ttc: The base ``(n_links,)`` transfer-capability array.
        overrides: ``{"ttc_wn": MW | None, "ttc_wsc": MW | None,
            "ttc_pn": MW | None}``.

    Returns:
        A copy of ``ttc`` with each non-``None`` override applied.
    """
    ttc = ttc.copy()
    for key, value in overrides.items():
        if value is None:
            continue
        target = TTC_LINK_ZONES[key]
        for i, link in enumerate(iso_config.links):
            if frozenset({link.from_zone, link.to_zone}) == target:
                logger.info(
                    "override %s link TTC: %.0f -> %.0f MW",
                    "-".join(sorted(target)),
                    ttc[i],
                    value,
                )
                ttc[i] = value
    return ttc


def _refuse_missing_year(table: str, year: int, tabulated) -> None:
    """Refuse a NYISO **historical** year with no measured Central-East entry.

    Both appliers below used to ``return`` unchanged when their table had no
    row for ``year``. That is a SILENT no-op, and its consequence is not
    neutral: with no override the link keeps the ``iso_configs`` STATIC value,
    which carries the **post-upgrade** 2,850 MW Central-East limit (the NY
    Transco AC Transmission project, in service Dec 2023). Any pre-upgrade year
    therefore solved with transmission that did not exist yet — for 2022,
    2,850 MW against a measured annual mean of 1,825 MW (+56 %), and against a
    measured 725 MW in Nov-2022 (3.9x). Central-East is the ISO's main
    upstate->downstate congestion path, so the error relieves precisely the
    congestion that forms downstate scarcity prices, i.e. it lands on the open
    C3c caveat and makes any such run uninterpretable.

    The refusal is scoped to years **at or before the last tabulated year**,
    which is exactly the set where a measured envelope should exist and its
    absence is a gap. A year *beyond* the table is the forward edge and stays a
    silent no-op: there the static value is not a stale fallback but the
    correct one — it IS this series' measured post-upgrade annual mean, and the
    forecast level channel is the transmission-expansion registry on top of it
    (see the ``NYISO_INTERFACE_TTC_BY_YEAR`` comment). That keeps forecast runs
    and forward-edge probes working while closing the historical trap; these
    helpers are backcast-only by construction anyway (module docstring).

    Args:
        table: Name of the constants table missing the year (for the message).
        year: The year with no entry.
        tabulated: The table's available years; the refusal window is
            ``year <= max(tabulated)``. A no-op when the table is empty.

    Raises:
        ValueError: When ``year`` falls at or before the last tabulated year.
    """
    years = [int(y) for y in tabulated]
    if not years or year > max(years):
        return
    raise ValueError(
        f"NYISO backcast year {year} has no {table} entry. The measured "
        "Central-East envelope must be derived before this year can be solved: "
        "run scripts/data/derive_nyiso_central_east_ttc.py (it prints the MIS "
        "re-fetch command) and add the year to market_sim.config.constants. "
        "This refusal is deliberate — the previous silent fallback used the "
        "STATIC post-upgrade 2,850 MW limit, which is wrong for every "
        "pre-Dec-2023 year (nyiso-134 defect D-2)."
    )


def apply_iso_year_ttc(iso_config, iso: str, year: int):
    """Return ``iso_config`` with year-varying interface TTCs applied.

    Some interfaces change capacity across the backcast years as transmission
    is built (e.g. NYISO's Central-East jumps with the NY Transco AC
    Transmission project, in service December 2023). The static topology in
    ``iso_configs`` carries one value; this rewrites the matching links to the
    year-accurate limit (``constants.NYISO_INTERFACE_TTC_BY_YEAR``) so 2023
    runs on the pre-upgrade limit and 2024+ on the upgraded one. A no-op for
    ISOs/years with no entry. Backcast-only overlay (plan §3.1): the forecast
    topology carries the upgraded static value (audit gap B4).
    """
    if iso != "NYISO":
        return iso_config
    overrides = NYISO_INTERFACE_TTC_BY_YEAR.get(year)
    if not overrides:
        _refuse_missing_year(
            "NYISO_INTERFACE_TTC_BY_YEAR", year, NYISO_INTERFACE_TTC_BY_YEAR
        )
        return iso_config
    links = []
    for link in iso_config.links:
        new_ttc = overrides.get((link.from_zone, link.to_zone))
        if new_ttc is not None and new_ttc != link.ttc_mw:
            logger.info(
                "NYISO %d interface TTC: %s->%s %.0f -> %.0f MW "
                "(AC Transmission year-varying limit)",
                year,
                link.from_zone,
                link.to_zone,
                link.ttc_mw,
                new_ttc,
            )
            links.append(link.model_copy(update={"ttc_mw": new_ttc}))
        else:
            links.append(link)
    return iso_config.model_copy(update={"links": links})


def apply_nwpp_path76_link(iso_config, iso: str, config=None):
    """Return ``iso_config`` with WECC Path 76 appended when the flag is armed.

    ``ScenarioConfig.nwpp_path76_alturas_link`` (NWPP-NEXT-6, GATED default
    off): appends :func:`market_sim.config.iso_configs.nwpp_path76_alturas_links`
    (NWPP-NW <-> NWPP-SNV, 300 / 300 MW, WECC 2024 Path Rating Catalog p. 69)
    to the static NWPP topology. Called at BOTH solve entry points
    (``run_calibration.run_year`` and ``runner.run_scenario_iso``) before the
    import node joins, so the link reaches incidence, interface groups and the
    TTC array alike — the caiso-162 lesson that a topology edit wired into one
    path only is silently ignored by the other. Returns the SAME object for
    any other ISO or when the flag is off, so the default path is
    byte-identical.
    """
    if iso != "NWPP" or not getattr(config, "nwpp_path76_alturas_link", False):
        return iso_config
    from market_sim.config.iso_configs import nwpp_path76_alturas_links

    added = nwpp_path76_alturas_links()
    for link in added:
        logger.info(
            "NWPP Path 76 (Alturas): %s<->%s %.0f MW appended",
            link.from_zone,
            link.to_zone,
            link.ttc_mw,
        )
    return iso_config.model_copy(update={"links": list(iso_config.links) + added})


def apply_iso_monthly_ttc(
    ttc, iso_config, iso: str, year: int, hours: int, config=None
):
    """Expand the scalar TTC array to a per-hour ``(hours, n_links)`` matrix
    when the ISO has a measured monthly interface envelope for ``year``.

    NYISO's Central-East day-ahead TTC is not flat across a year: it steps up
    when the AC Transmission upgrade energizes (Dec 2023) and moves month to
    month with that year's approved transmission outages.
    ``constants.NYISO_INTERFACE_TTC_BY_MONTH`` carries the measured 12-month
    mean per interface; this maps each hour of the backcast year to its
    calendar month (leap-safe) and rewrites the matching link's limit hour by
    hour, so the dispatch binds on the measured within-year envelope rather
    than one annual value. Returns ``ttc`` unchanged (1-D) for ISOs/years with
    no monthly table — byte-identical to the prior scalar path.

    **Backcast-only, and deliberately so** (rule 13 [R-MEASURED]; nyiso-104,
    D-5 row ``nyiso_central_east_measured_ttc``). The within-year shape is
    *not* a seasonal rating — on the unchanged post-upgrade topology the
    level-normalized monthly shape correlates across 2024/2025 at only
    r=+0.21 — so it carries no forward analogue, and applying it to a forecast
    year would import one historical year's outage schedule. The forward
    channel for the *level* is the transmission-expansion registry.
    """
    if iso != "NYISO":
        return ttc
    # nyiso-224, rule 19 [R-ONE-MECH]: the cutset envelope REPLACES the
    # CENT EAST table on this one seam; the two never stack. Rule 14
    # [R-ACCURATE] misalignment exception — the single Upstate_West ->
    # Capital_Hudson link is the A-E -> F+ cutset (TOTAL EAST), and CENT EAST
    # is a nested sub-cutset of it. See the constants header.
    cutset = bool(getattr(config, "nyiso_total_east_cutset_ttc", False))
    table_name = (
        "NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH"
        if cutset
        else "NYISO_INTERFACE_TTC_BY_MONTH"
    )
    table = (
        NYISO_CUTSET_TTC_ENVELOPE_BY_MONTH if cutset else NYISO_INTERFACE_TTC_BY_MONTH
    )
    monthly = table.get(year)
    if not monthly:
        _refuse_missing_year(table_name, year, table)
        return ttc
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    days_per_month = [31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    month_of_hour = np.repeat(np.arange(1, 13), [d * 24 for d in days_per_month])[
        :hours
    ]
    ttc_t = np.broadcast_to(ttc, (hours, len(ttc))).copy()
    for i, link in enumerate(iso_config.links):
        profile = monthly.get((link.from_zone, link.to_zone))
        if profile is None:
            continue
        prof = np.asarray(profile, dtype=float)
        ttc_t[:, i] = prof[month_of_hour - 1]
        logger.info(
            "NYISO %d %s->%s monthly TTC envelope: %.0f-%.0f MW (%s)",
            year,
            link.from_zone,
            link.to_zone,
            prof.min(),
            prof.max(),
            (
                "measured TOTAL EAST cutset p90 transfer"
                if cutset
                else "measured Central-East DAM postings"
            ),
        )
    return ttc_t

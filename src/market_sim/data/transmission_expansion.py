"""Read the curated ``transmission-expansion`` registry into forward TTC deltas.

The model's *consumption seam* for each ISO's committed transmission-expansion
registry, curated by the intake pipeline
(``scripts/lib/transmission_expansion`` → ``data/clean/transmission-expansion``).

:func:`load_transmission_expansions` returns the live (non-superseded) rows
whose ``in_service_year`` postdates the ISO's base-static vintage
(:data:`TRANSMISSION_BASE_STATIC_VINTAGE`, this module) — the
only rows that can be *additive* to the static topology — as plain pydantic
objects carrying just what the channel needs. The runner consumes them per
solve year through :func:`apply_transmission_expansion`, which returns a copy
of the :class:`~market_sim.config.iso_configs.ISOConfig` with each affected
link's ``ttc_mw`` (and each affected :class:`InterfaceLimit`'s caps) raised by
the cumulative delta of every applied row in service by that year — and
returns the *same object* untouched when nothing applies, so the off-gate and
no-row paths are byte-identical by construction.

Only ``target_kind`` ``link`` and ``interface`` rows are applied.
``import_tranche`` rows (external supply-side lines — CHPE into NYC, WECC-side
merchant HVDC) and ``intra_zonal`` rows (work entirely inside one model zone)
are loaded and logged as recorded-not-applied: the import fleet is built once
before the year loop and has no per-year seam yet (a named V1 exclusion —
``docs/transmission-expansion-methodology-2026-07.md`` §6), and an intra-zonal
project has no modeled limit to change at this topology's grain.

Fail-loud contract (the W2-E / G12 convention, cloned from
``data.confirmed_retirements``): when the caller passes ``required=True`` — the
runner does so whenever ``transmission_expansion_enabled`` is on in forecast
mode — an unimportable ``scripts.lib.clean_io`` seam or a never-curated
checkout (the datatype root absent from ``data/clean``) RAISES with the
regeneration command instead of silently running the frozen-topology forecast
the flag was set to avoid. A curated root with no partition for the requested
ISO still degrades quietly — a legitimately zero-row registry, not a setup
failure. Remediation:
``PYTHONPATH=. python scripts/data/curate_transmission_expansion.py``.
Forecast-forward only: backcast-year transmission stays with the measured
overlays (``NYISO_INTERFACE_TTC_BY_YEAR``, measured GTC/interface series).
"""

from __future__ import annotations

import logging

import pandas as pd
from pydantic import BaseModel

from market_sim.config.iso_configs import InterfaceLimit, ISOConfig, TransferLink

logger = logging.getLogger(__name__)

DATATYPE = "transmission-expansion"

# Base-static vintage year of each ISO's transmission topology: the year whose
# measured/published limits the static iso_configs TTCs and InterfaceLimit
# caps embed. The loader admits a registry row only when its in_service_year
# is STRICTLY AFTER this vintage — a project already embedded in the base
# statics (e.g. NYISO's AC Transmission Segment A/B inside the measured
# 2024-25 Central-East mean) must never be double-counted as a delta
# (rule 14; the per-row delta convention is documented in
# data/raw/transmission-expansion/README.md). Lives beside its sole consumer,
# like model/transmission.CAISO_PATH_DIRECTIONAL_RATINGS — a documented
# property of the static sources cited in config/iso_configs.py, never a
# tunable (rule 24). Vintages trace those static sources:
#   ERCOT 2024 — measured 2023-24 NP6-86 GTC limits (WESTEX/PNHNDL/NE_LOB)
#     + 2022 Constraints & Needs interior estimates.
#   CAISO 2023 — WECC Path Rating Catalog ratings + LCT 2023 pocket caps.
#   MISO  2025 — PY2025-26 LOLE CIL/CEL groups + JOA RDT limits.
#   PJM   2024 — 2024 transfer-limits/flows postings.
#   NYISO 2025 — measured 2024-25 DAM Central-East mean (post-Segment-A/B).
#   NEISO 2023 — RSP interface limits + ICR tie-benefit cap (pre-NECEC).
TRANSMISSION_BASE_STATIC_VINTAGE: dict[str, int] = {
    "ERCOT": 2024,
    "CAISO": 2023,
    "MISO": 2025,
    "PJM": 2024,
    "NYISO": 2025,
    "NEISO": 2023,
}

# The target kinds the forward channel can express at this topology's grain.
# import_tranche / intra_zonal rows are recorded-not-applied (module docstring).
_APPLY_KINDS = frozenset({"link", "interface"})

# W2-E / G12 fail-loud remediation, quoted verbatim in every required-mode
# raise below (the confirmed-retirements convention: data/clean is derived and
# gitignored, so a fresh checkout has no registry until regenerated).
_REMEDIATION = (
    "run `PYTHONPATH=. python scripts/data/curate_transmission_expansion.py` "
    "from the repo root to regenerate data/clean/transmission-expansion, then "
    "delete any results/<ISO>/<key>/ caches solved before it existed "
    "(cache_key hashes config only, never data-file state)"
)


def _registry_curated() -> bool:
    """Whether the clean transmission-expansion datatype root exists at all.

    Distinguishes the two FileNotFoundError shapes behind ``required=True``:
    an absent datatype ROOT means the checkout was never curated (must raise —
    the run would silently forecast on a frozen topology), while a present
    root with no partition for THIS ISO means curation ran and the ISO
    legitimately has zero qualifying rows (warn-only degrade).
    """
    try:
        from market_sim.config import paths

        return (paths.CLEAN_DIR / DATATYPE).is_dir()
    except Exception:
        return False


class TransmissionExpansion(BaseModel):
    """One committed project row targeting one model element.

    Attributes
    ----------
    row_id / project_id / project_name:
        Registry identity (``row_id`` unique per (project, element)).
    status_tier:
        ``energized`` | ``under_construction`` | ``approved_funded`` (closed
        vocabulary; membership IS the admission bar — roadmap rows never enter
        the registry).
    target_kind:
        ``link`` | ``interface`` | ``import_tranche`` | ``intra_zonal``.
    from_zone / to_zone:
        Model zone pair for ``link`` rows (the listed orientation is the
        delta's direction context); receiving zone in ``to_zone`` for
        ``import_tranche``; containing zone in ``from_zone`` for
        ``intra_zonal``.
    interface_name:
        The :class:`InterfaceLimit` name for ``interface`` rows.
    in_service_year:
        First calendar year the delta is in service (applied to every solve
        year >= it, cumulatively across rows).
    delta_mw / delta_mw_reverse:
        Capability increase in MW (forward-listed direction / optional
        asymmetric reverse for interface rows).
    mapping_confidence:
        ``exact`` | ``reconciled`` | ``ambiguous`` (diagnostic; all applied).
    """

    row_id: str
    project_id: str
    project_name: str
    status_tier: str
    target_kind: str
    from_zone: str | None = None
    to_zone: str | None = None
    interface_name: str | None = None
    in_service_year: int
    delta_mw: float
    delta_mw_reverse: float | None = None
    mapping_confidence: str


def load_transmission_expansions(
    iso: str, required: bool = False
) -> list[TransmissionExpansion]:
    """Return the ISO's live, post-base-vintage transmission-expansion rows.

    Reads the clean ``transmission-expansion`` partition, drops ``superseded``
    rows, and drops rows whose ``in_service_year`` does not postdate the ISO's
    base-static vintage (those are embedded in the static topology already —
    logged, never applied). Returns ``[]`` (with a log line) when the
    partition is absent, so the caller degrades to the frozen static topology.

    Args:
        iso: Model ISO name (e.g. ``"NEISO"``). The registry is partitioned by
            this exact label.
        required: Fail-loud switch (W2-E / G12 convention). When True — the
            runner passes it whenever ``transmission_expansion_enabled`` is on
            in forecast mode — an unimportable ``scripts.lib.clean_io`` seam
            or a never-curated checkout raises :class:`RuntimeError` with the
            regeneration command instead of silently running the
            frozen-topology forecast. A curated root missing only this ISO's
            partition still degrades (zero-row registry). Default False.

    Returns:
        Rows sorted by ``(in_service_year, row_id)`` — every live
        post-vintage row of every ``target_kind`` (the apply filter is
        :func:`apply_transmission_expansion`'s, so recorded-not-applied kinds
        stay visible to logging/reporting).
    """
    try:
        from scripts.lib.clean_io import read_clean
    except ModuleNotFoundError as exc:
        if required:
            raise RuntimeError(
                f"transmission-expansion: scripts.lib.clean_io is unimportable "
                f"(repo root not on sys.path? — invoke with PYTHONPATH=. from "
                f"the repo root) while transmission_expansion_enabled is on in "
                f"forecast mode. Refusing to silently run the frozen-topology "
                f"forecast for {iso}; {_REMEDIATION}."
            ) from exc
        logger.warning(
            "transmission-expansion: scripts.lib.clean_io unavailable; no "
            "forward TTC deltas for %s.",
            iso,
        )
        return []
    try:
        df = read_clean(DATATYPE, iso=iso.upper())
    except FileNotFoundError as exc:
        if required and not _registry_curated():
            raise RuntimeError(
                f"transmission-expansion: clean partition for {iso} is absent "
                f"while transmission_expansion_enabled is on in forecast mode. "
                f"data/clean is derived and gitignored, so a fresh checkout "
                f"has no registry; refusing to silently run the "
                f"frozen-topology forecast; {_REMEDIATION}."
            ) from exc
        logger.warning(
            "transmission-expansion: clean partition for %s absent; forward "
            "TTC channel is a no-op this run (run "
            "scripts/data/curate_transmission_expansion.py to regenerate).",
            iso,
        )
        return []

    if df.empty:
        return []
    live = df[~df["superseded"].astype(bool)].copy()
    if live.empty:
        return []

    vintage = TRANSMISSION_BASE_STATIC_VINTAGE[iso.upper()]
    live["in_service_year"] = pd.to_numeric(live["in_service_year"], errors="coerce")
    live = live.dropna(subset=["in_service_year"])
    embedded = live[live["in_service_year"] <= vintage]
    if not embedded.empty:
        logger.info(
            "transmission-expansion: %d %s row(s) at/before the %d base-static "
            "vintage are embedded in the static topology and not applied: %s",
            len(embedded),
            iso,
            vintage,
            sorted(embedded["row_id"]),
        )
    live = live[live["in_service_year"] > vintage]

    rows: list[TransmissionExpansion] = []
    for row in live.itertuples(index=False):
        rows.append(
            TransmissionExpansion(
                row_id=str(row.row_id),
                project_id=str(row.project_id),
                project_name=str(row.project_name),
                status_tier=str(row.status_tier),
                target_kind=str(row.target_kind),
                from_zone=(str(row.from_zone) if pd.notna(row.from_zone) else None),
                to_zone=(str(row.to_zone) if pd.notna(row.to_zone) else None),
                interface_name=(
                    str(row.interface_name) if pd.notna(row.interface_name) else None
                ),
                in_service_year=int(row.in_service_year),
                delta_mw=float(row.delta_mw),
                delta_mw_reverse=(
                    float(row.delta_mw_reverse)
                    if pd.notna(row.delta_mw_reverse)
                    else None
                ),
                mapping_confidence=str(row.mapping_confidence),
            )
        )
    rows.sort(key=lambda r: (r.in_service_year, r.row_id))
    n_apply = sum(1 for r in rows if r.target_kind in _APPLY_KINDS)
    recorded = [r.row_id for r in rows if r.target_kind not in _APPLY_KINDS]
    logger.info(
        "transmission-expansion: loaded %d live post-%d row(s) for %s "
        "(%d applicable; %d recorded-not-applied%s)",
        len(rows),
        vintage,
        iso,
        n_apply,
        len(recorded),
        f": {recorded}" if recorded else "",
    )
    return rows


def cumulative_deltas(
    expansions: list[TransmissionExpansion], year: int
) -> tuple[dict[tuple[str, str], float], dict[str, tuple[float, float]]]:
    """Cumulative in-service deltas by model element as of ``year``.

    Sums ``delta_mw`` over every applicable (``link``/``interface``) row with
    ``in_service_year <= year``. Returns ``(link_deltas, interface_deltas)``:
    ``link_deltas`` keyed by the row's listed ``(from_zone, to_zone)``
    orientation; ``interface_deltas`` keyed by ``interface_name`` with a
    ``(cap_delta, reverse_cap_delta)`` pair (reverse accumulates
    ``delta_mw_reverse`` where present, else mirrors ``delta_mw`` — a
    symmetric uplift raises both directions of a bidirectional cap).
    """
    link_deltas: dict[tuple[str, str], float] = {}
    interface_deltas: dict[str, tuple[float, float]] = {}
    for row in expansions:
        if row.in_service_year > year or row.target_kind not in _APPLY_KINDS:
            continue
        if row.target_kind == "link":
            key = (str(row.from_zone), str(row.to_zone))
            link_deltas[key] = link_deltas.get(key, 0.0) + row.delta_mw
        else:
            name = str(row.interface_name)
            fwd, rev = interface_deltas.get(name, (0.0, 0.0))
            rev_delta = (
                row.delta_mw_reverse
                if row.delta_mw_reverse is not None
                else row.delta_mw
            )
            interface_deltas[name] = (fwd + row.delta_mw, rev + rev_delta)
    return link_deltas, interface_deltas


def apply_transmission_expansion(
    iso_config: ISOConfig,
    iso: str,
    year: int,
    expansions: list[TransmissionExpansion],
) -> ISOConfig:
    """Return ``iso_config`` with ``year``'s cumulative expansion deltas applied.

    The forward-channel analogue of
    :func:`market_sim.model.transmission.apply_caiso_local_import_limits`
    (the per-year topology-copy template): each ``link`` delta is added to the
    matching :class:`TransferLink`'s ``ttc_mw`` — matched on the row's exact
    listed orientation first (so a one-way pair's export and import links are
    targeted independently), else on the reversed orientation (a bidirectional
    link's symmetric TTC takes the delta from either listing) — and each
    ``interface`` delta is added to the named :class:`InterfaceLimit`'s
    ``cap_mw`` (and ``reverse_cap_mw`` where one is declared). A delta whose
    zone pair or interface name resolves to nothing in the *active* topology
    logs a WARNING with its row keys and is skipped (the registry is validated
    against the default topology at curation; a run-time variant config — a
    re-cut zone, an alternate import node — is a config-dependent surface,
    never a crash).

    Returns the SAME object (``is``-identical) when no delta applies — the
    byte-identity guarantee for the off-gate, pre-COD, and zero-row paths —
    and a validated ``model_copy`` otherwise.

    Args:
        iso_config: The ISO topology to uplift (never mutated).
        iso: Model ISO name (log context only).
        year: Solve year; rows with ``in_service_year <= year`` apply.
        expansions: Rows from :func:`load_transmission_expansions`.
    """
    link_deltas, interface_deltas = cumulative_deltas(expansions, year)
    if not link_deltas and not interface_deltas:
        return iso_config

    changed = False
    new_links: list[TransferLink] = list(iso_config.links)
    for (a, b), delta in sorted(link_deltas.items()):
        if delta == 0.0:
            continue
        exact = [
            i for i, ln in enumerate(new_links) if (ln.from_zone, ln.to_zone) == (a, b)
        ]
        matches = exact or [
            i for i, ln in enumerate(new_links) if (ln.from_zone, ln.to_zone) == (b, a)
        ]
        if not matches:
            logger.warning(
                "transmission-expansion: %s link delta (%s, %s) +%.0f MW in %d "
                "matches no TransferLink in the active topology; skipped",
                iso,
                a,
                b,
                delta,
                year,
            )
            continue
        if len(matches) > 1:
            # A zone pair carries at most one link per orientation in every
            # registered topology; seeing two means the topology changed under
            # the registry — apply to the first and flag for re-mapping.
            logger.warning(
                "transmission-expansion: %s link delta (%s, %s) matches %d "
                "links; applying to the first (re-map the registry row)",
                iso,
                a,
                b,
                len(matches),
            )
        i = matches[0]
        link = new_links[i]
        new_links[i] = link.model_copy(update={"ttc_mw": link.ttc_mw + delta})
        changed = True

    new_limits: list[InterfaceLimit] = list(iso_config.interface_limits)
    limits_changed = False
    for name, (fwd, rev) in sorted(interface_deltas.items()):
        if fwd == 0.0 and rev == 0.0:
            continue
        idx = [i for i, lim in enumerate(new_limits) if lim.name == name]
        if not idx:
            logger.warning(
                "transmission-expansion: %s interface delta %r +%.0f MW in %d "
                "matches no InterfaceLimit in the active topology; skipped",
                iso,
                name,
                fwd,
                year,
            )
            continue
        i = idx[0]
        lim = new_limits[i]
        update: dict[str, float] = {"cap_mw": lim.cap_mw + fwd}
        if lim.reverse_cap_mw is not None:
            update["reverse_cap_mw"] = lim.reverse_cap_mw + rev
        new_limits[i] = lim.model_copy(update=update)
        limits_changed = True
        changed = True

    if not changed:
        return iso_config
    update_fields: dict[str, object] = {"links": new_links}
    if limits_changed:
        update_fields["interface_limits"] = new_limits
    extended = iso_config.model_copy(update=update_fields)
    extended.validate_topology()
    return extended

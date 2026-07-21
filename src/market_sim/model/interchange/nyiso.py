"""NYISO interchange: hub prices, TSL caps, self-supply, firm imports, recon.

Everything NYISO-specific that lived in ``model/transmission.py``: the
measured neighbor-LMP import-hub repricer, the published Zone-K / Zone-J
locality (LCR/TSL) import caps, the downstate local self-supply floor, the
HQ/Ontario firm-import floors, and the priced-node monthly net-interchange
reconciliation band. Per-ISO tuned limits transplant byte-for-byte
(CLAUDE.md rules 23/25). Moved INTACT from ``model/transmission.py``
(session 3F, refactor-consolidation plan §5 item 6); ``transmission``
remains the full-surface facade.
"""

import logging

import numpy as np

from market_sim.config.constants import NYISO_LOCAL_SELFSUPPLY_FRAC
from market_sim.data.floor_mechanisms import (
    MECH_FIRM_IMPORT,
    MECH_NYISO_SELFSUPPLY,
    ensure_mechanism,
)
from market_sim.model.interchange.spec import (
    IMPORT_ZONE,
    NYISO_FIRM_IMPORT_FLOOR_FRAC,
    NYISO_IMPORT_RECON_BAND_FRAC,
)

_logger = logging.getLogger(__name__)


# NYISO priced-node tranche → the modeled neighbor whose measured hourly system
# LMP prices it (nyiso_import_hub_prices). HQ_hydro and IESO_Ontario are absent
# on purpose: neither carries an organized-market LMP series in-repo (HQ is a
# firm-contract flow, firm-floored by inject_nyiso_firm_imports; IESO's HOEP is
# not uploaded), so they keep their static contract-ladder values.
_NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR: dict[str, str] = {
    "PJM_west": "PJM",
    "ISONE_tie": "NEISO",
}
# The residual deep non-firm block spans the remaining tie depth across the
# eastern interfaces; its marginal MW cannot be cheaper than every real
# adjacent market, so it prices at the hourly max of the measured neighbors.
_NYISO_HUB_SCARCITY_TRANCHE: str = "import_scarcity"
_NYISO_HUB_EXPORT_TRANCHE: str = "export_surplus"
# Inter-control-area wheeling hurdle ($/MWh) on the NYISO seam — the same $1
# dead-band the PJM↔NYISO NeighborInterface spec carries (INTERFACE_NEIGHBORS
# ["PJM"]["NYISO"].hurdle), applied symmetrically: import at neighbor + hurdle,
# export at neighbor − hurdle, so a same-hour round trip is strictly
# cost-positive (arbitrage-free).
NYISO_IMPORT_HUB_HURDLE: float = 1.0


def inject_nyiso_import_hub_prices(
    fleet_arrays,
    mc: np.ndarray,
    iso: str,
    year: int,
) -> bool:
    """Reprice NYISO's non-firm import tranches at measured neighbor hourly LMPs.

    The NYISO analogue of :func:`inject_caiso_import_hub_prices` (measured WECC
    intertie LMP) and :func:`inject_miso_pjm_lmp_import_prices` (measured PJM
    border DA LMP): the priced import node's ``PJM_west`` / ``ISONE_tie`` rows
    take the **measured hourly Day-Ahead system LMP** of the neighbor they proxy
    (:func:`market_sim.data.neighbor_price.neighbor_lmp_hourly`, ``rt``
    fallback) plus the wheeling hurdle; the residual ``import_scarcity`` block
    takes the hourly **max** of the two priced neighbors + hurdle (the deep
    non-firm MW beyond the direct-tie blocks cannot undercut every real
    adjacent market); the ``export_surplus`` sink takes the hourly **min** of
    the two − hurdle. The min (not max) on the destination-blind single sink is
    deliberate: pricing it at the dearer neighbor would open a phantom
    wheel-through arbitrage against the cheap static Canadian import tranches
    (buy IESO at its $22-37 contract constant, "sell" at the NE winter price
    inside the external node) that permanently occupies the sink's 600 MW and
    blocks genuine export hours; the min is the wash-free lower envelope of the
    neighbors' willingness-to-pay. ``HQ_hydro`` / ``IESO_Ontario`` keep their
    static firm-contract ladder values (no organized-market series; the HQ
    block is firm-floored anyway).

    Why: the static ``IMPORT_TRANCHES_BY_YEAR`` ladder is a per-year constant
    fit, blind to neighbor fundamentals — it caps the modeled seam price at its
    top constant exactly when the real seam repriced with the neighbors (the
    Dec-2024 New-England-complex month, the Jun-2025 heat wave), and its cheap
    constants soften off-peak prices the real seam never saw. The measured
    neighbor LMP is the real delivered opportunity cost of the imported energy
    (rule #12: regenerates for a forward year from the modeled neighbor /
    reference-price formula, responds to changed conditions), read blind to
    NYISO's own flow (rule #11). The monthly EIA-930 reconciliation band, HQ
    firm floor and simultaneous-import limit are untouched.

    Returns ``True`` when at least one row was repriced, ``False`` (byte-
    identical static ladder) for non-NYISO ISOs, a missing import node, or
    missing measured neighbor series (e.g. forecast years).
    """
    from market_sim.data.neighbor_price import neighbor_lmp_hourly

    if iso.upper() != "NYISO":
        return False
    zone = IMPORT_ZONE.get(iso)
    if zone is None:
        return False
    hours = int(mc.shape[1])
    series: dict[str, np.ndarray] = {}
    for neighbor in sorted(set(_NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR.values())):
        lmp = neighbor_lmp_hourly(neighbor, year, "da")
        if lmp is None:
            lmp = neighbor_lmp_hourly(neighbor, year, "rt")
        if lmp is None or lmp.shape[0] < hours:
            continue
        series[neighbor] = np.asarray(lmp[:hours], dtype=float)
    if not series:
        return False
    # Hourly max (deep-import ceiling) / min (wash-free export willingness-to-
    # pay) over the priced neighbors.
    deep_import = np.maximum.reduce(list(series.values()))
    export_wtp = np.minimum.reduce(list(series.values()))
    applied = False
    for row, uid in enumerate(fleet_arrays.unit_ids):
        if not uid.startswith(f"{zone}_"):
            continue
        tranche = uid[len(zone) + 1 :]
        neighbor = _NYISO_HUB_IMPORT_TRANCHE_NEIGHBOR.get(tranche)
        if neighbor is not None and neighbor in series:
            mc[row, :] = series[neighbor] + NYISO_IMPORT_HUB_HURDLE
            applied = True
        elif tranche == _NYISO_HUB_SCARCITY_TRANCHE:
            mc[row, :] = deep_import + NYISO_IMPORT_HUB_HURDLE
            applied = True
        elif tranche == _NYISO_HUB_EXPORT_TRANCHE:
            mc[row, :] = export_wtp - NYISO_IMPORT_HUB_HURDLE
            applied = True
    return applied


# Afternoon-evening peak window (local HB14-21, inclusive) the Long Island local
# self-supply floor is restricted to — the SAME downstate summer design-cooling
# window the CT/ST temperature reliability ramps use (start_hour=14/end_hour=21 in
# reliability_floor_coeffs_NYISO.csv). Rule-17/rule-18 narrowing (floor-rederive
# 2026-07-05): the LI locational-reliability / cable-import constraint the floor
# proxies physically binds only at the afternoon-evening AC peak — the condition
# the LCR locality requirements are defined at (NYISO Locality Bulk-Power
# Transmission Capability reports, design cooling day) — and is inactive
# overnight, where measured LI net import runs well below its cable ceiling
# (docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md Finding 4: LI inflow
# max 2,480 MW vs ~2,850 MW ceiling, 0 h > 90%) and measured LI CT_PEAKER CF is
# ~0.06 flat. Applied all-hours the floor force-committed in-pocket LM6000 baseload
# overnight (D-2: nyiso_local_selfsupply forced 1.84/2.87/1.86 TWh of CT_PEAKER,
# 43/65/42% of the class; C7 off-peak diurnal FAIL). This is a HOURS narrowing of
# an existing floor, NOT a re-level of its (residual-identified, issue #1345) 0.45
# fraction — the level stays untouched; only the overnight hours it had no driver
# for are removed.
NYISO_SELFSUPPLY_FLOOR_HOURS: tuple[int, ...] = tuple(range(14, 22))  # HB14-21


# Dispatchable thermal fuels eligible to carry a local self-supply floor — the
# in-zone gas / oil / coal fleet, excluding non-dispatchable / energy-limited /
# must-run resources (wind, solar, hydro, nuclear, geothermal, biomass) and the
# import pseudo-generators, which cannot stand in for local reliability units.
def _dispatchable_thermal_codes() -> list[int]:
    from market_sim.data.fleet import FUEL_TYPE_MAP

    names = (
        "gas_cc",
        "gas_ct",
        "gas_st",
        "oil",
        "coal",
        "gas_cc_ccs",
        "hydrogen_ct",
        "hydrogen_ccgt",
    )
    return [FUEL_TYPE_MAP[n] for n in names if n in FUEL_TYPE_MAP]


def apply_nyiso_li_tsl_import_cap(
    ttc: np.ndarray,
    iso_config,
    iso: str,
    year: int,
    hours: int,
) -> np.ndarray:
    """Cap the NYC->Long_Island link at the published Zone-K locality import
    limit during the peak window (issue #1345, ``config.nyiso_li_lcr_tsl``).

    The published NYISO Locality Bulk-Power Transmission Capability import
    limit for Long Island (``data/raw/capacity-deliverability/nyiso/nyiso.csv``:
    325 / 275 / 275 MW for the 2023/24-2025/26 capability years) is the
    transmission-security boundary the Zone-K LCR is derived against — the AC
    import LI may count on at the summer design-cooling peak, with the
    UDR-backed external cables (the priced-import-node links, ~1.2 GW) counted
    separately. Mapping it to hourly dispatch terms (the rule-14
    reconciliation, documented in the ``nyiso_li_lcr_tsl`` ScenarioConfig
    comment): the limit is applied ONLY inside the design-condition window
    (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, HB14-21 — the same window and driver
    document the PR-#1442-narrowed self-supply floor used), where it replaces
    the link's physical 1,650 MW rating; every other hour keeps the physical
    rating (measured LI off-peak imports run well below the cable ceiling and
    the security constraint's driver is inactive). Applied all-hours the
    peak-condition boundary would force ~16 TWh/yr of LI energy vs the
    ~8.5 TWh physically real — the boundary mismatch issue #1345 documents.

    In-window LI supply beyond (external ties + the security-limited AC
    import) then clears from the in-zone fleet ECONOMICALLY — this function is
    the replacement for the Long_Island 0.45 self-supply ``min_gen`` floor
    (``inject_nyiso_local_selfsupply``; the caller must exclude Long_Island
    there when this cap is active — one mechanism per phenomenon, rule 19),
    so the LI reliability energy stops being floor-forced (rule-20 D-2
    budget) and becomes merit-order dispatch behind a published limit.

    The cap is symmetric on the AC link in-window (the LP's bidirectional
    bound); measured LI peak-window exports toward NYC are ~0 MW, a
    documented, immaterial misalignment accepted over one-way link plumbing.

    Args:
        ttc: ``(n_links,)`` static or ``(hours, n_links)`` per-hour transfer
            capabilities (MW).
        iso_config: ISO topology (``links`` searched for NYC->Long_Island).
        iso: ISO identifier; every ISO but ``"NYISO"`` returns ``ttc``
            unchanged.
        year: Backcast/solve calendar year (resolves the capability-year row).
        hours: LP horizon length T.

    Returns:
        ``(hours, n_links)`` per-hour TTC matrix with the in-window LI cap
        applied (a copy), or ``ttc`` unchanged for non-NYISO.

    Raises:
        ValueError: NYISO without a published Long Island import limit for the
            resolved capability year, or no NYC->Long_Island link — the
            mechanism must never silently no-op when explicitly enabled.
    """
    if iso != "NYISO":
        return ttc

    from market_sim.data.capacity_deliverability import (
        import_limit_by_area,
        resolve_delivery_year,
    )

    delivery_year = resolve_delivery_year(iso, int(year))
    limits = import_limit_by_area(iso, delivery_year)
    tsl = limits.get("Long Island")
    if tsl is None:
        raise ValueError(
            f"nyiso_li_lcr_tsl=True but no published Long Island import limit "
            f"for delivery year {delivery_year} in the capacity-deliverability "
            f"table (data/raw/capacity-deliverability/nyiso/nyiso.csv); "
            f"available areas: {sorted(limits)}"
        )

    li_idx = [
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("NYC", "Long_Island")
    ]
    if not li_idx:
        raise ValueError(
            "nyiso_li_lcr_tsl=True but the NYISO topology has no "
            "NYC->Long_Island link to cap."
        )

    ttc_arr = np.asarray(ttc, dtype=float)
    if ttc_arr.ndim == 1:
        ttc_t = np.broadcast_to(ttc_arr, (int(hours), ttc_arr.shape[0])).copy()
    else:
        ttc_t = ttc_arr.copy()
    hod = np.arange(int(hours)) % 24
    in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
    for i in li_idx:
        ttc_t[in_window, i] = np.minimum(ttc_t[in_window, i], float(tsl))
    return ttc_t


def apply_nyiso_nyc_tsl_import_cap(
    ttc: np.ndarray,
    iso_config,
    iso: str,
    year: int,
    hours: int,
) -> np.ndarray:
    """Cap the Lower_Hudson->NYC link at the published NYC (Zone-J) locality
    import limit during the peak window (nyiso-61, ``config.nyiso_nyc_lcr_tsl``).

    The Zone-J analog of :func:`apply_nyiso_li_tsl_import_cap`. The published
    NYISO NYC-locality Bulk-Power Transmission Capability import limit
    (``data/raw/capacity-deliverability/nyiso/nyiso.csv``: 2,875 MW for every
    capability year 2023/24-2025/26) is the transmission-security boundary the
    NYC LCR is derived against — the AC import NYC may count on at the summer
    design-cooling peak. It REPLACES the Lower_Hudson->NYC (Dunwoodie-South)
    link's 3,900 MW energy-TTC estimate (iso_configs.py Gold-Book seed) inside
    the design-condition window (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, HB14-21 —
    the same window and driver document the LI cap uses); every other hour keeps
    the physical 3,900 MW rating (measured off-peak NYC imports run below the
    interface ceiling and the security constraint's driver is inactive).

    RULE-14 boundary (clean, parallel to the LI cap): the 2,875 MW is the
    AC-import transmission-security limit; the controllable HVDC ties into
    Zone J (Neptune / HTP / Linden-VFT) are counted SEPARATELY as the priced
    import-node link (``interchange_config.IMPORT_NODE_LINKS["NYISO"]``
    ``("NYC", 1000.0)``), which stays at its physical rating — so this caps
    ONLY the Dunwoodie-South AC link, not total NYC import. In-window NYC supply
    beyond (external HVDC ties + the security-limited AC import) then clears
    from the in-city fleet ECONOMICALLY, letting the dear Zone-J gas set price
    at the summer peak (the identified 2024/2025 deep-tail lever). This is a
    transmission limit, not a ``min_gen`` floor — it forces no energy (the D-2
    budget is unchanged).

    The cap is symmetric on the AC link in-window (the LP's bidirectional
    bound); measured NYC peak-window exports toward Lower_Hudson are ~0 MW, a
    documented, immaterial misalignment accepted over one-way link plumbing.

    Args:
        ttc: ``(n_links,)`` static or ``(hours, n_links)`` per-hour transfer
            capabilities (MW).
        iso_config: ISO topology (``links`` searched for Lower_Hudson->NYC).
        iso: ISO identifier; every ISO but ``"NYISO"`` returns ``ttc``
            unchanged.
        year: Backcast/solve calendar year (resolves the capability-year row).
        hours: LP horizon length T.

    Returns:
        ``(hours, n_links)`` per-hour TTC matrix with the in-window NYC cap
        applied (a copy), or ``ttc`` unchanged for non-NYISO.

    Raises:
        ValueError: NYISO without a published NYC import limit for the resolved
            capability year, or no Lower_Hudson->NYC link — the mechanism must
            never silently no-op when explicitly enabled.
    """
    if iso != "NYISO":
        return ttc

    from market_sim.data.capacity_deliverability import (
        import_limit_by_area,
        resolve_delivery_year,
    )

    delivery_year = resolve_delivery_year(iso, int(year))
    limits = import_limit_by_area(iso, delivery_year)
    tsl = limits.get("NYC")
    if tsl is None:
        raise ValueError(
            f"nyiso_nyc_lcr_tsl=True but no published NYC import limit "
            f"for delivery year {delivery_year} in the capacity-deliverability "
            f"table (data/raw/capacity-deliverability/nyiso/nyiso.csv); "
            f"available areas: {sorted(limits)}"
        )

    nyc_idx = [
        i
        for i, ln in enumerate(iso_config.links)
        if (ln.from_zone, ln.to_zone) == ("Lower_Hudson", "NYC")
    ]
    if not nyc_idx:
        raise ValueError(
            "nyiso_nyc_lcr_tsl=True but the NYISO topology has no "
            "Lower_Hudson->NYC link to cap."
        )

    ttc_arr = np.asarray(ttc, dtype=float)
    if ttc_arr.ndim == 1:
        ttc_t = np.broadcast_to(ttc_arr, (int(hours), ttc_arr.shape[0])).copy()
    else:
        ttc_t = ttc_arr.copy()
    hod = np.arange(int(hours)) % 24
    in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
    for i in nyc_idx:
        ttc_t[in_window, i] = np.minimum(ttc_t[in_window, i], float(tsl))
    return ttc_t


def inject_nyiso_local_selfsupply(
    fleet_arrays,
    iso: str,
    demand: np.ndarray,
    zone_names: list[str],
    exclude_zones: frozenset[str] = frozenset(),
) -> bool:
    """Floor a NYISO downstate load pocket's in-zone thermal self-supply.

    Models NYISO's locational-minimum-installed-capacity (LMIC) /
    local-reliability rules for the cable-islanded Long Island pocket (zone K):
    a fraction of the zone's own load must be met by IN-ZONE dispatchable
    thermal generation rather than imported across the limited NYC->LI cables.
    The economic LP, lacking the rule, floods cheap NYC gas into LI and
    under-runs the LI fleet (model 3.7 vs EIA-923 8.52 TWh, 2023;
    docs/nyiso-dispatch-validation-2026-06.md).

    For each pocket zone in
    :data:`~market_sim.config.constants.NYISO_LOCAL_SELFSUPPLY_FRAC`, the hourly
    in-zone target is ``frac × demand[zone, t]`` **restricted to the
    afternoon-evening peak window** (:data:`NYISO_SELFSUPPLY_FLOOR_HOURS`, local
    HB14-21) and zero outside it, distributed over the zone's dispatchable
    thermal generators in **marginal-cost merit order** (gas-capable tranches
    first by heat rate, the dear oil-fired peakers last) and each capped at its
    available capacity — the same hour-varying ``FleetArrays.min_gen`` lower
    bound the CHP / CT reliability floors use, and composed with any floor
    already present via ``maximum``. The target is clipped to the zone fleet's
    available capacity each hour so a feasible LP solution always exists (the
    floor can never manufacture unmet load).

    The **window narrowing** (rule-17/18, floor-rederive 2026-07-05): the LI
    locational-reliability / cable-import constraint the floor proxies binds only
    at the summer design-cooling peak (the condition the LCR locality
    requirements are defined at), not overnight — applied all-hours the floor
    force-committed in-pocket LM6000 peaker baseload where measured LI CT_PEAKER
    CF is ~0.06 flat and LI imports run well below their cable ceiling (the D-2
    off-window forcing / C7 diurnal FAIL). The 0.45 fraction itself
    (residual-identified, issue #1345) is **unchanged** — this narrows only the
    hours it binds, never its level.

    The floor is **forward-reproducible** (it scales with load and responds to
    changed conditions) and grounded in NYISO market design — it is NOT a pin to
    measured LI generation (CLAUDE.md rule #12).

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when ``iso`` is not NYISO, no pocket
    fraction is configured, or no eligible in-zone thermal capacity exists.

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ``"NYISO"`` applies a floor.
        demand: Zonal demand of shape ``(n_zones, T)`` in MW.
        zone_names: Zone names ordered to match ``demand``'s rows.
        exclude_zones: Pocket zones whose floor entry is skipped because a
            replacement mechanism owns them this run (rule 19 — one mechanism
            per phenomenon): the ``nyiso_li_lcr_tsl`` Zone-K LCR/TSL import
            cap (issue #1345, :func:`apply_nyiso_li_tsl_import_cap`) excludes
            ``Long_Island`` so the published-limit cap and the 0.45 energy
            floor are never stacked. Empty (the default) is byte-identical.

    Returns:
        ``True`` if any pocket floor was applied, else ``False``.
    """
    if iso != "NYISO" or not NYISO_LOCAL_SELFSUPPLY_FRAC:
        return False

    from market_sim.data.fleet import FUEL_TYPE_MAP

    thermal_codes = _dispatchable_thermal_codes()
    is_thermal = np.isin(fleet_arrays.fuel_type_idx, thermal_codes)
    zone_to_idx = {z: i for i, z in enumerate(zone_names)}
    demand = np.asarray(demand, dtype=float)
    hours = int(fleet_arrays.availability.shape[1])

    applied = False
    for zone, frac in NYISO_LOCAL_SELFSUPPLY_FRAC.items():
        if zone in exclude_zones:
            continue
        if frac <= 0.0 or zone not in zone_to_idx:
            continue
        z_idx = zone_to_idx[zone]
        in_zone = (fleet_arrays.zone_idx == z_idx) & is_thermal
        rows = np.flatnonzero(in_zone & (fleet_arrays.pmax > 0.0))
        if rows.size == 0:
            continue

        target = frac * demand[z_idx, :hours]
        # Restrict the floor to the afternoon-evening peak window
        # (NYISO_SELFSUPPLY_FLOOR_HOURS): the LI local-reliability / cable-import
        # constraint the floor proxies binds only at the summer design-cooling
        # peak, not overnight (rule-17/18 narrowing — see the constant's note).
        hod = np.arange(hours) % 24
        in_window = np.isin(hod, np.asarray(NYISO_SELFSUPPLY_FLOOR_HOURS))
        target = np.where(in_window, target, 0.0)
        avail_cap = (
            fleet_arrays.pmax[rows, np.newaxis] * fleet_arrays.availability[rows, :]
        )
        # Never demand more than the in-zone fleet can supply that hour.
        np.minimum(target, avail_cap.sum(axis=0), out=target)

        if fleet_arrays.min_gen is None:
            fleet_arrays.min_gen = np.broadcast_to(
                fleet_arrays.pmin[:, np.newaxis],
                (fleet_arrays.pmin.size, hours),
            ).copy()

        # Fill the floor in marginal-cost merit order, not by raw heat rate: the
        # LI reliability minimum is met by the in-zone fleet that would actually
        # run — efficient gas first, the dear oil-fired peakers LAST. Distillate
        # costs ~5x gas per MMBtu, so a raw heat-rate sort put oil CTs (heat rate
        # ~9.8) AHEAD of gas CTs (~10-11) and forced ~1.5 TWh/yr of non-physical
        # flat, year-round LI oil into the floor. Tiering oil last means it enters
        # the floor only when in-zone gas capacity is exhausted (deep-winter peak);
        # genuine winter dual-fuel oil still runs economically on top of the floor
        # via the delivered-oil-priced switch (it is not suppressed, only no longer
        # force-committed for a summer reliability minimum). Fuel-cost ordering is
        # forward-reproducible (gas stays cheaper than oil in every forward year),
        # not a fit to measured oil volume (CLAUDE.md rule #12).
        oil_code = FUEL_TYPE_MAP.get("oil")
        is_oil = (fleet_arrays.fuel_type_idx[rows] == oil_code).astype(int)
        order = rows[np.lexsort((fleet_arrays.heat_rate[rows], is_oil))]
        remaining = target.copy()
        mech = ensure_mechanism(fleet_arrays)
        for r in order:
            cap = fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            take = np.minimum(remaining, cap)
            raised = fleet_arrays.min_gen[r, :] < take
            np.maximum(fleet_arrays.min_gen[r, :], take, out=fleet_arrays.min_gen[r, :])
            mech[r, raised] = MECH_NYISO_SELFSUPPLY
            remaining = remaining - take
        applied = True
    return applied


def inject_nyiso_firm_imports(fleet_arrays, iso: str, year: int) -> bool:
    """Floor NYISO's firm (must-flow) import baseload at the priced node.

    Hydro-Québec (Châteauguay/Cedars) and Ontario (IESO) sell NY firm,
    long-term scheduled hydro/nuclear baseload that flows regardless of NY's
    hourly price. The priced node prices them as economic tranches (clearing
    only when NYISO's price exceeds the tranche cost), which backs them off in
    cheap-overnight hours / low-price years even though the real schedule keeps
    flowing. For each tranche in
    :data:`~market_sim.config.interchange_config.NYISO_FIRM_IMPORT_FLOOR_FRAC`, this sets
    a constant hourly ``min_gen`` floor of ``frac × tranche capacity`` on the
    matching import row (capped at the row's available capacity), so the firm
    baseload flows every hour. The configured fractions keep the total firm
    floor below the measured lightest-import hour, so it can never force a
    phantom over-import.

    Modifies ``fleet_arrays`` in place. Returns ``True`` when a floor was
    applied, ``False`` (byte-identical) when ``iso`` is not NYISO, no fraction
    is configured, or no matching import row is present (e.g. the served-wedge
    path without a priced node).

    Args:
        fleet_arrays: Vectorized fleet (modified in place).
        iso: ISO identifier; only ``"NYISO"`` applies a floor.
        year: Backcast year (unused today; carried for parity with the other
            priced-node injectors and future per-year firm schedules).

    Returns:
        ``True`` if any firm-import floor was applied, else ``False``.
    """
    if iso != "NYISO" or not NYISO_FIRM_IMPORT_FLOOR_FRAC:
        return False

    hours = int(fleet_arrays.availability.shape[1])
    unit_ids = list(fleet_arrays.unit_ids)
    applied = False
    for name, frac in NYISO_FIRM_IMPORT_FLOOR_FRAC.items():
        if frac <= 0.0:
            continue
        rows = [i for i, uid in enumerate(unit_ids) if uid.endswith(f"_{name}")]
        for r in rows:
            if fleet_arrays.pmax[r] <= 0.0:
                continue
            floor = frac * fleet_arrays.pmax[r] * fleet_arrays.availability[r, :]
            if fleet_arrays.min_gen is None:
                fleet_arrays.min_gen = np.broadcast_to(
                    fleet_arrays.pmin[:, np.newaxis],
                    (fleet_arrays.pmin.size, hours),
                ).copy()
            raised = fleet_arrays.min_gen[r, :] < floor
            np.maximum(
                fleet_arrays.min_gen[r, :], floor, out=fleet_arrays.min_gen[r, :]
            )
            ensure_mechanism(fleet_arrays)[r, raised] = MECH_FIRM_IMPORT
            applied = True
    return applied


def build_import_node_reconciliation(
    fleet_arrays,
    iso: str,
    year: int,
    band_frac: float = NYISO_IMPORT_RECON_BAND_FRAC,
    *,
    mode: str = "backcast",
    forward_net_import_twh: dict[int, float] | float | None = None,
    system_demand: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    """Build the priced-node monthly net-interchange band, mode-aware.

    Returns the inputs for a per-month band constraint
    (:func:`market_sim.model.dispatch._build_import_node_rows`) that holds the
    NYISO priced import node's monthly NET interchange within an envelope while
    leaving the priced tranches free to set the marginal price *within* each
    month. The band **target** depends on the run mode — and that is the whole
    forecast-vs-backcast distinction (CLAUDE.md rule #10, methodology spec §1.7):

    * ``mode == "backcast"`` — target the **measured** EIA-930 net-interchange
      schedule (:func:`market_sim.data.eia_loader.nyiso_net_interchange`), the
      *realization*. The economic priced node clears a near-flat ~18.5-21.6 TWh
      because its tranche offers are near-static and do not track the metered
      schedule's year-over-year decline (23.45 -> 20.35 -> 19.09 TWh), so it
      under-imports in 2023 and over-imports in 2024/25; banding it to the
      metered level REPLACES that economic estimate with the authoritative
      measurement (rule #11). This is standard production-cost boundary-flow
      calibration (Aurora/PLEXOS/GridView/PROMOD pin the tie-line net flow
      against an unmodeled neighbor; ReEDS fixes net trade with non-modeled
      regions): the neighbor is not co-optimized, so its flow cannot be
      economically derived and is calibrated to actuals in a backcast. The
      target is the measured schedule itself, NOT a residual-minimizing volume
      (rule #12); ``band_frac`` only sets the price / feasibility headroom.

    * ``mode == "forecast"`` — there is no measured schedule, so the target is
      the **neighbor's forecast net position** supplied via
      ``forward_net_import_twh`` (the PJM / Hydro-Québec / Ontario / ISO-NE
      forward export outlook as an annual NYISO net import, shaped to monthly by
      the forecast load via
      :func:`market_sim.data.eia_loader.nyiso_forward_net_import_monthly`). This
      keeps the dispatch being validated the same as the dispatch being forecast
      (rule #10). When no forecast is supplied the band **relaxes** (returns
      ``None``): the priced seam clears endogenously, never pinned to a measured
      monthly total. The forward band is forward-reproducible — it regenerates
      for any year from forward drivers and responds to changed conditions.

    Net sign: the node columns are import tranches (``P >= 0``, inject) plus
    export sinks (``P <= 0``, withdraw), so ``sum P`` is the node's *net import*
    in MW — the negative of the measured export-positive
    :func:`~market_sim.data.eia_loader.nyiso_net_interchange`. Both the backcast
    target (``-sum export``) and the forecast target (the supplied net import)
    are therefore in net-import (positive) MWh, on the same monthly basis.

    Args:
        fleet_arrays: Vectorized fleet (read-only here; the constraint lives in
            the LP, not in ``min_gen``).
        iso: ISO identifier; only ``"NYISO"`` builds a band.
        year: Year keying the measured (backcast) or forecast trajectory.
        band_frac: Monthly band half-width as a fraction of the monthly net
            import. ``0.0`` makes it a hard monthly equality.
        mode: ``"backcast"`` (target the measured schedule, default — preserves
            the existing calibration behaviour byte-for-byte) or ``"forecast"``
            (target the supplied neighbor forecast, else relax).
        forward_net_import_twh: Forecast-only. NYISO annual net import (TWh,
            import-positive) as a ``dict[year -> TWh]`` or bare ``float``; the
            forward band source. Ignored in backcast.
        system_demand: Forecast-only. Hourly system demand used to shape the
            annual forecast to monthly targets (imports track load). Ignored in
            backcast.

    Returns:
        Tuple ``(node_gen_idx, monthly_lo, monthly_hi)`` — the import-node
        thermal-block row indices and the per-month MWh net-import bounds — or
        ``None`` (no constraint) when ``iso`` is not NYISO, no priced import node
        is present (the served-wedge path), or no target is available for the
        mode (backcast year with no measured schedule / forecast with no
        supplied neighbor position).
    """
    if iso != "NYISO":
        return None

    from market_sim.data.eia_loader import (
        nyiso_forward_net_import_monthly,
        nyiso_net_interchange,
    )
    from market_sim.data.fleet import FUEL_TYPE_MAP, _hour_to_month_index

    hours = int(fleet_arrays.availability.shape[1])
    import_code = FUEL_TYPE_MAP["import"]
    # Import tranches (pmax > 0, inject) AND export sinks (pmin < 0, withdraw):
    # their signed P-sum is the node's net import, matching the net-interchange
    # basis. A node with neither is the served-wedge path (no priced node) —
    # nothing to reconcile.
    is_node = fleet_arrays.fuel_type_idx == import_code
    node_idx = np.flatnonzero(
        is_node & ((fleet_arrays.pmax > 0.0) | (fleet_arrays.pmin < 0.0))
    )
    if node_idx.size == 0:
        return None

    if mode == "forecast":
        # Forward band source: the neighbor's forecast net position. None when no
        # forecast is supplied -> band relaxes to the bare priced-seam economics.
        monthly_target = nyiso_forward_net_import_monthly(
            year, forward_net_import_twh, system_demand
        )
        if monthly_target is None:
            return None
    else:
        # Backcast: the measured EIA-930 realization (unchanged behaviour).
        export_pos = nyiso_net_interchange(year)  # export-positive MW, (8760,)
        if export_pos is None:
            return None
        export_pos = np.asarray(export_pos, dtype=float).reshape(-1)[:hours]
        if export_pos.size < hours:
            return None
        # Net import (MW) = -export-positive interchange; aggregate to monthly
        # MWh on the same hour->month map the LP constraint uses (no per-hour
        # Python loop).
        net_import = -export_pos
        month_index = _hour_to_month_index(hours)
        n_months = int(month_index.max()) + 1
        monthly_target = np.zeros(n_months, dtype=float)
        np.add.at(monthly_target, month_index, net_import)

    half = abs(band_frac) * np.abs(monthly_target)
    monthly_lo = monthly_target - half
    monthly_hi = monthly_target + half
    return node_idx, monthly_lo, monthly_hi


def apply_nyiso_firm_import_injections(
    fleet_arrays,
    mc,
    config,
    iso: str,
    year: int,
    *,
    carbon_price: float = 0.0,
    gas_scenario: str = "mid",
    forward_skill: str | None = None,
) -> None:
    """Registry step: the HQ/Ontario firm-import must-flow floors.

    Verbatim step 3 (NYISO half) of the historical
    ``apply_interchange_injections`` monolith — contract structure, not a
    measured-outcome pin; gated on ``config.nyiso_firm_imports``.
    """
    if getattr(config, "nyiso_firm_imports", False):
        if inject_nyiso_firm_imports(fleet_arrays, iso, year):
            _logger.info(
                "%s %d: firm import baseload floored (HQ/Ontario must-flow)",
                iso,
                year,
            )

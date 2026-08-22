"""Reserve co-optimization row builders for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7): the zone-aggregate (:func:`_build_reserve_rows`) and per-generator
(:func:`_build_reserve_rows_pergen`) reserve constructions plus the
post-solve :func:`storage_reserve_mw` attribution helper. Pure code motion —
every def is byte-identical to its pre-split ``dispatch.py`` source.
"""

import numpy as np
import scipy.sparse as sp

from market_sim.data.fleet import FleetArrays
from market_sim.model.lp.layout import (
    VariableLayout,
    _build_zone_storage_map,
    _vstack_csr_free,
)


def _build_reserve_rows(
    layout: VariableLayout,
    fleet: FleetArrays,
    reserve_requirement: np.ndarray,
    reserve_eligible: np.ndarray,
    storage_zone_idx: np.ndarray | None = None,
    storage_power_cap: np.ndarray | float | None = None,
    balance_zone_mask: np.ndarray | None = None,
    balance_ordc_counts: np.ndarray | None = None,
    balance_reserve_class: np.ndarray | None = None,
    online_gated: np.ndarray | None = None,
    online_rho: float = 1.0,
    headroom_eligible: np.ndarray | None = None,
    headroom_products: np.ndarray | None = None,
    headroom_extra_cap: np.ndarray | None = None,
    headroom_storage: np.ndarray | None = None,
    reserve_supply_cap: np.ndarray | None = None,
    online_capacity_cap: np.ndarray | None = None,
    storage_duration_h: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Build the energy+reserve co-optimization constraint rows (zone-aggregate).

    Reserve is tracked per *zone* and per reserve *class* (``n_reserve ==
    n_reserve_classes * n_zones``), not per unit: a reserve variable
    ``R[c,z,t]`` and one shared-headroom row per class-zone-hour. This keeps the
    LP tractable at per-plant fleet scale (a per-unit headroom row for every
    generator-hour is tens of millions of rows; per-zone is a few per hour)
    while giving the same economics — the zonal headroom dual is what lifts that
    zone's energy LMP. Two families, both vectorized (no hour loop):

    * **Shared headroom** -- for each reserve class ``c``, zone ``z`` and hour
      ``t``: ``sum_{class-c eligible g in z} P[g,t] + R[c,z,t] <=
      sum_{class-c eligible g in z} cap[g,t]``. The zone's class-eligible
      capacity is split between energy and upward reserve, so committing energy
      consumes reserve headroom and vice-versa.
    * **Reserve balance** -- one row per *reserve family* ``f`` and hour ``t``,
      drawing on family ``f``'s reserve class ``c_f``:
      ``sum_{z in family f} R[c_f,z,t] + sum_{k in family f} ORDC_k[t]
      >= requirement[f,t]``. The ORDC shortfall steps let the requirement go
      unmet at the published penalty price, so the binding family's balance-row
      dual is that family's reserve clearing price.

    A *family* is one (region, reserve-product) balance constraint. ERCOT and
    PJM run a single system-wide family on a single class (every zone, every
    ORDC step), which is the default when ``balance_zone_mask`` is ``None`` and
    reproduces the legacy single-row LP byte-identically. NYISO runs nested
    *locational* families (NYCA ⊃ East ⊃ SENY ⊃ NYC) across two reserve classes:
    30-minute products draw on the full dispatchable fleet (class 0), while
    10-minute products draw only on the quick-start subset (class 1) — a
    10-minute requirement cannot be met by slow combined-cycle headroom. The
    shared per-zone ``R[c,z]`` variables feed every family of the same class
    that contains the zone, so a downstate reserve shortage stacks the
    East/SENY/NYC family penalties into the downstate zonal LMP even when the
    system is long on reserves. Because the classes are *nested* (quick-start
    units are also dispatchable), a quick-start unit's headroom feeds both its
    class-1 row (10-minute supply) and the class-0 row (30-minute supply), which
    is the correct reserve cascade: a 10-minute MW also counts toward the larger
    30-minute requirement. ``balance_zone_mask[f]`` selects family ``f``'s
    member zones, ``balance_reserve_class[f]`` its eligibility class, and
    ``balance_ordc_counts[f]`` its slice of the family-major ORDC block.

    Args:
        layout: Variable layout (``n_reserve == n_reserve_classes * n_zones``).
        fleet: Fleet arrays supplying ``pmax``, ``(n_gen, T)`` availability and
            per-generator ``zone_idx``.
        reserve_requirement: ``(T,)`` (single system-wide family) or
            ``(n_families, T)`` hourly reserve requirement in MW.
        reserve_eligible: ``(n_gen,)`` boolean (single class) or
            ``(n_classes, n_gen)`` boolean — the reserve-eligible generators of
            each class. ``layout.n_reserve_classes`` must equal the class count.
        storage_zone_idx: ``(n_storage,)`` zone of each storage unit. When given
            (with ``storage_power_cap``), storage backs upward reserve too —
            batteries respond in seconds, so they back every reserve class
            (including the 10-minute quick-start class); excluding them
            understates reserve supply and overstates scarcity.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` MW power cap;
            a unit's upward reserve room is ``cap - discharge + charge``.
        balance_zone_mask: ``(n_families, n_zones)`` boolean — member zones of
            each reserve family. ``None`` builds a single system-wide family
            spanning every zone (the legacy ERCOT/PJM behaviour).
        balance_ordc_counts: ``(n_families,)`` number of ORDC shortfall steps
            owned by each family; they partition the family-major ORDC block
            and must sum to ``layout.n_ordc_steps``. ``None`` assigns every step
            to the single system-wide family.
        balance_reserve_class: ``(n_families,)`` int — the reserve class index
            each family draws on. ``None`` (or all-zero) puts every family on
            class 0 (the single-class default). A ``-1`` entry marks an
            ALL-CLASS family: its balance row sums the reserve of **every**
            class over its member zones (``sum_c sum_{z in f} R[c,z]``) — the
            ERCOT lumped ORDC total-reserve curve (RTORPA), which prices the
            aggregate reserve level that every AS product's held MW counts
            toward, layered on top of the per-product families.
        online_gated: ``(n_classes,)`` boolean — classes whose headroom is
            online-gated (synchronised/spinning reserve). For a gated class the
            shared-headroom row is ``R[c,z] - online_rho * sum_g P[g] <= 0``
            instead of ``sum_g P[g] + R[c,z] <= sum_g cap[g]``, so idle (P=0)
            capacity contributes no reserve and only online generation backs it.
            ``None`` (default) leaves every class idle-allowed (legacy). Applies
            to the legacy per-class headroom; ignored under an additive
            ``headroom_products`` spec.
        online_rho: the online-headroom multiplier for gated classes — how much
            spinning reserve an online unit backs per MW of output (~ the fleet
            ``(pmax-pmin)/pmin`` at min load). Default 1.0.
        headroom_eligible: ``(n_headroom_rows, n_gen)`` boolean — the eligible
            generators of each *additive* headroom row. When supplied (with
            ``headroom_products``) it REPLACES the per-class headroom rows with
            caller-specified rows, so several reserve products can share one
            headroom pool ADDITIVELY (ERCOT's RegUp/RRS/ECRS/NonSpin each hold
            *separate* capacity, ~7-8 GW total, unlike NYISO's nested products
            where one MW counts for both tiers). ``None`` keeps the legacy
            per-class headroom (one row per class, byte-identical).
        headroom_products: ``(n_headroom_rows, n_reserve_classes)`` boolean —
            which products' (classes') per-zone reserve ``R[p,z]`` enter each
            headroom row's sum. Row ``h`` reads
            ``sum_{g in headroom_eligible[h] ∩ z} P[g] + sum_{p in
            headroom_products[h]} R[p,z] <= cap(headroom_eligible[h], z) +
            headroom_extra_cap[h,z]``. Nesting a "fast" row (RegUp+RRS+ECRS on
            the online-responsive set) inside an "all" row (every product on the
            online + offline-quick set) gives the additive quality cascade: a
            slow Non-Spin MW can come from offline quick-start, while the fast
            products are bounded by the smaller online-responsive headroom.
        headroom_extra_cap: ``(n_headroom_rows, n_zones, T)`` or
            ``(n_headroom_rows, n_zones)`` MW — extra non-generator headroom
            added to each additive row's RHS (e.g. offline quick-start capacity
            that backs Non-Spin without an energy term). ``None`` adds nothing.
        headroom_storage: ``(n_headroom_rows,)`` boolean — which additive rows
            pooled storage backs (ercot-226 ``ercot_as_held_location``: the
            two tier rows keep storage room, a class-carve row's RHS must stay
            the class's own thermal capability). ``None`` = every row
            (byte-identical legacy behaviour). Ignored under the duration gate
            (storage then has its own RS columns instead of pooling).
        reserve_supply_cap: ``(n_headroom_rows, T)`` MW — a **system-wide** upper
            bound on the cleared reserve of each additive headroom row's products,
            ``sum_z sum_{p in headroom_products[h]} R[p,z] <= reserve_supply_cap[h,t]``.
            One row per headroom tier per hour, inserted **before** the balance
            rows so the balance dual indexing is unchanged. Re-scopes the reserve
            *supply* to a measured online-responsive capability (ERCOT RTOLCAP/
            RTOFFCAP) instead of the full-fleet headroom in the headroom RHS, so
            modeled reserve tightens into the band the ORDC demand curve prices.
            ``None`` (and the legacy per-class spec) adds no cap rows.
        storage_duration_h: ``(n_reserve_classes,)`` per-product sustained-delivery
            duration in hours (ERCOT ``ERCOT_AS_PRODUCT_DURATION_H``: RegUp/RRS 1 h,
            ECRS 2 h, Non-Spin 4 h). When supplied (and storage is present), the
            ERCOT endogenous-storage DURATION GATE is active: storage is REMOVED
            from the thermal shared-headroom rows and given its own explicit
            per-zone reserve columns ``RS[c,z]`` (``layout._storage_reserve_off``),
            with three additions — (a) a per-zone storage power-competition row
            ``sum_c RS[c,z] + sum_{s in z}(Dis[s]-Chg[s]) <= sum_{s in z} cap[s]``
            (the same power split that was implicit in the shared headroom, now
            explicit); (b) a per-zone LP-linear duration gate
            ``sum_c dur_c*RS[c,z] - sum_{s in z} SOC[s] <= 0`` linking cleared
            storage AS to state of charge, so a 1-h battery cannot sell 4-h
            Non-Spin on its full power; and (c) the ``RS[c,z]`` reserve joins the
            balance rows (and the supply-cap rows, so cleared storage AS still
            counts under RTOLCAP) alongside the thermal ``R[c,z]``. Both new row
            families are per-zone-hour and fully vectorized (``sp.kron`` over
            hours, no hour loop). The gate uses the zone-aggregate SOC
            (``sum_{s in z} SOC[s]``), a small relaxation when a zone mixes battery
            durations. ``None`` (default) keeps storage pooled in the shared
            headroom (byte-identical to the pre-gate co-opt).

    Returns:
        ``(block, row_lower, row_upper)``: the stacked headroom + balance rows
        and their bounds. Headroom rows are ``<=`` (lower ``-inf``); balance
        rows are ``>=`` (upper ``+inf``). Headroom rows are class-major then
        zone within each hour (row ``t*(n_classes*n_zones) + c*n_zones + z``);
        balance rows are family-major within each hour (row ``t*n_families+f``).
    """
    T = layout.T
    n_zones = layout.n_zones
    n_storage = layout.n_storage
    cap = fleet.pmax[:, np.newaxis] * fleet.availability  # (n_gen, T)
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)

    # Per-class eligibility: accept a flat (n_gen,) mask (single class) or a
    # (n_classes, n_gen) stack. n_classes here must match layout.n_reserve //
    # n_zones (= layout.n_reserve_classes).
    elig2d = np.atleast_2d(
        np.asarray(reserve_eligible, dtype=bool)
    )  # (n_classes, n_gen)
    n_classes = elig2d.shape[0]

    use_storage = (
        n_storage > 0 and storage_zone_idx is not None and storage_power_cap is not None
    )
    # Duration gate (ERCOT endogenous storage AS): when per-product durations are
    # supplied and storage is present, storage is pulled OUT of the thermal
    # shared-headroom rows and given its own RS[c,z] columns + power/duration
    # rows (built after the headroom/supply-cap blocks below). ``gate`` guards
    # the two behaviours: (1) skip the storage terms in the thermal headroom
    # (else storage power is double-counted), (2) emit the RS row families.
    gate = use_storage and storage_duration_h is not None
    if gate:
        dur = np.asarray(storage_duration_h, dtype=float).reshape(n_classes)
    if use_storage:
        s_zone = np.asarray(storage_zone_idx, dtype=int)
        s_idx = np.arange(n_storage)
        spc = np.asarray(storage_power_cap, dtype=float)
        zone_storage = _build_zone_storage_map(s_zone, n_zones, n_storage)

    # --- Shared-headroom per-hour block, (n_hr*n_zones, vph). Each headroom row
    # h, zone z (row h*n_zones + z) reads
    #   sum_{g in E_h ∩ z} P[g] + sum_{p in Prod_h} R[p,z] <= cap(E_h, z) + extra
    # where E_h is the row's eligible generator set, Prod_h the set of products
    # (reserve classes) whose per-zone reserve it bounds, and the RHS the
    # eligible thermal + storage + extra capacity. The DEFAULT (legacy) spec is
    # one row per reserve class c bounding only its own R[c,z] against its
    # class-c eligible capacity — byte-identical to the previous per-class loop.
    # The ADDITIVE spec (``headroom_products`` supplied) lets several products
    # share one headroom row, so ERCOT's RegUp/RRS/ECRS/NonSpin compete for the
    # same capacity instead of each independently reusing it. Storage (when
    # supplied) backs every headroom row — batteries respond in seconds, so a
    # unit's upward room (cap - Dis + Chg) enters every row's R sum, its discharge
    # column with +1 and charge with -1 and its power cap added to the RHS.
    if headroom_products is None:
        # Legacy per-class spec: row c eligible = class-c gens, bounds R[c].
        hr_elig = elig2d  # (n_classes, n_gen)
        hr_prod = np.eye(n_classes, dtype=bool)  # (n_classes, n_classes)
        extra = None
    else:
        hr_elig = np.atleast_2d(np.asarray(headroom_eligible, dtype=bool))
        hr_prod = np.atleast_2d(np.asarray(headroom_products, dtype=bool))
        extra = (
            None
            if headroom_extra_cap is None
            else np.asarray(headroom_extra_cap, float)
        )
    n_hr = hr_prod.shape[0]
    rows: list[np.ndarray] = []
    cols: list[np.ndarray] = []
    vals: list[np.ndarray] = []
    z_all = np.arange(n_zones)
    zone_cap = np.zeros((n_hr * n_zones, T))  # RHS, headroom-row-major
    gated = (
        np.zeros(n_classes, dtype=bool)
        if online_gated is None
        else np.asarray(online_gated, dtype=bool).reshape(n_classes)
    )
    for h in range(n_hr):
        base = h * n_zones
        e_idx = np.flatnonzero(hr_elig[h])
        if headroom_products is None and gated[h]:
            # ONLINE-GATED (synchronised/spinning) class, legacy per-class path:
            # reserve can come only from ONLINE capacity, not idle headroom. Row
            # reads ``R[c,z] - rho * sum_{elig g in z} P[g] <= 0`` -> a unit at
            # P=0 contributes nothing (an offline peaker is NOT spinning
            # reserve), and an online unit backs ``rho``x its output (rho = the
            # fleet online-headroom ratio, ~ (pmax-pmin)/pmin near min load). The
            # RHS is 0 (no idle-capacity credit) and storage is excluded (its
            # room is not synchronised thermal spin). LP-linear proxy for
            # commitment-gated spinning reserve (path A); the exact gate needs an
            # online binary (path B / model.commitment). The ERCOT multi-product
            # additive spec uses the P2 commitment screen instead (its fa_p2
            # availability zeroes idle slow-start capacity out of the RHS), so
            # gating does not apply there.
            rows.append(base + zone_idx[e_idx])
            cols.append(e_idx)
            vals.append(np.full(e_idx.size, -float(online_rho)))  # -rho * P[g]
            rows.append(base + z_all)
            cols.append(layout._reserve_off + base + z_all)
            vals.append(np.ones(n_zones))  # +R[c,z]
            # zone_cap stays 0 for this class (no idle/storage credit).
            continue
        # eligible thermal P columns -> this headroom row (zone-summed)
        rows.append(base + zone_idx[e_idx])
        cols.append(e_idx)
        vals.append(np.ones(e_idx.size))
        # reserve columns R[p, z] for every product p bounded by this row
        for p in np.flatnonzero(hr_prod[h]):
            rows.append(base + z_all)
            cols.append(layout._reserve_off + int(p) * n_zones + z_all)
            vals.append(np.ones(n_zones))
        # eligible-generator -> zone incidence for this row's RHS capacity
        zone_gen_elig = sp.csr_matrix(
            (np.ones(e_idx.size), (zone_idx[e_idx], e_idx)),
            shape=(n_zones, layout.n_gen),
        )
        zc = zone_gen_elig @ cap  # (n_zones, T)
        if (
            use_storage
            and not gate
            and (headroom_storage is None or bool(headroom_storage[h]))
        ):
            # Pooled storage in the thermal headroom (pre-duration-gate co-opt).
            # Under the duration gate storage has its own RS columns and power
            # row instead, so it must NOT also add its room here (double count).
            # A row opted out via ``headroom_storage`` (ercot-226 class-carve
            # rows) keeps its thermal-only RHS and no storage columns.
            rows.append(base + s_zone)
            cols.append(layout._dis_off + s_idx)
            vals.append(np.ones(n_storage))  # +Dis
            rows.append(base + s_zone)
            cols.append(layout._chg_off + s_idx)
            vals.append(-np.ones(n_storage))  # -Chg
            if spc.ndim == 2:
                zc = zc + (zone_storage @ spc)  # (n_zones, T)
            else:
                zc = zc + (zone_storage @ spc)[:, None]
        if extra is not None:
            zc = zc + (extra[h] if extra[h].ndim == 2 else extra[h][:, None])
        zone_cap[base : base + n_zones, :] = zc
    headroom_per_hour = sp.coo_matrix(
        (np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))),
        shape=(n_hr * n_zones, layout.vars_per_hour),
    ).tocsr()
    headroom = sp.kron(sp.eye(T, format="csr"), headroom_per_hour, format="csr")
    # RHS: headroom-row-zone-summed eligible capacity per hour, hour-major
    # (row t*(n_hr*n_zones) + h*n_zones + z).
    hr_upper = zone_cap.T.ravel()
    hr_lower = np.full(n_hr * n_zones * T, -np.inf)

    # --- Reserve-balance per-hour block, (n_families, vph): for family f a +1
    # on its member zones' reserve columns (in family f's reserve class c_f) and
    # a +1 on its slice of the ORDC block. Row f reads
    # sum_{z in f} R[c_f,z] + sum_{k in f} ORDC_k >= req[f]. Single-family
    # default (mask None) is one row over every zone/step on class 0 — the
    # legacy ERCOT/PJM LP, byte-identical.
    if balance_zone_mask is None:
        zmask = np.ones((1, n_zones), dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(1, T)
        ordc_counts = np.array([layout.n_ordc_steps], dtype=int)
    else:
        zmask = np.asarray(balance_zone_mask, dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(zmask.shape[0], T)
        ordc_counts = np.asarray(balance_ordc_counts, dtype=int)
    n_fam = zmask.shape[0]
    if balance_reserve_class is None:
        fam_class = np.zeros(n_fam, dtype=int)
    else:
        fam_class = np.asarray(balance_reserve_class, dtype=int).reshape(n_fam)
    brows: list[np.ndarray] = []
    bcols: list[np.ndarray] = []
    bvals: list[np.ndarray] = []
    # reserve columns, family-by-family (vectorized within each family): each
    # family draws on R[c_f, z] for its member zones z, so its reserve columns
    # are offset into its class block (c_f * n_zones). fam_class[f] == -1 is
    # the ALL-CLASS family (ERCOT lumped ORDC total-reserve): it draws on every
    # class's R over its member zones, so each product's held reserve counts
    # toward the total-reserve requirement exactly once.
    for f in range(n_fam):
        zsel = np.flatnonzero(zmask[f])
        fam_classes = (
            range(n_classes) if int(fam_class[f]) < 0 else (int(fam_class[f]),)
        )
        for c in fam_classes:
            brows.append(np.full(zsel.size, f))
            bcols.append(layout._reserve_off + int(c) * n_zones + zsel)
            bvals.append(np.ones(zsel.size))
            if gate:
                # Storage's duration-gated reserve RS[c,z] backs the same family
                # as the thermal R[c,z] of its class (the all-class total family,
                # fam_class -1, sums every class's RS too — cleared storage AS
                # counts toward the lumped total exactly once).
                brows.append(np.full(zsel.size, f))
                bcols.append(layout._storage_reserve_off + int(c) * n_zones + zsel)
                bvals.append(np.ones(zsel.size))
    # ORDC columns: family-major block, family f owns the next ordc_counts[f]
    off = 0
    for f in range(n_fam):
        k = int(ordc_counts[f])
        if k:
            idx = np.arange(off, off + k)
            brows.append(np.full(k, f))
            bcols.append(layout._ordc_off + idx)
            bvals.append(np.ones(k))
            off += k
    bal_per_hour = sp.coo_matrix(
        (np.concatenate(bvals), (np.concatenate(brows), np.concatenate(bcols))),
        shape=(n_fam, layout.vars_per_hour),
    ).tocsr()
    balance = sp.kron(sp.eye(T, format="csr"), bal_per_hour, format="csr")
    # Hour-major RHS (row t*n_fam + f): req2d is (n_fam, T) -> transpose -> ravel.
    bal_lower = req2d.T.ravel()
    bal_upper = np.full(n_fam * T, np.inf)

    # --- Optional reserve-supply cap block, (n_hr, vph). One system-wide row per
    # headroom row h capping that row's cleared reserve:
    #   sum_z sum_{p in Prod_h} R[p,z] <= reserve_supply_cap[h,t].
    # Inserted BETWEEN the headroom and balance blocks so the reserve-balance
    # rows stay the final n_fam*T (the dual indexing in DispatchModel relies on
    # this). Re-scopes reserve SUPPLY to a measured online-responsive capability
    # (ERCOT RTOLCAP) vs the over-counted full-fleet headroom in zone_cap. Works
    # for BOTH the additive multi-product spec (one cap row per headroom tier) and
    # the legacy per-class spec (``hr_prod`` is then the class identity, so one
    # cap row per reserve class). Absent (``reserve_supply_cap is None``) the LP
    # is byte-identical (no cap block).
    blocks = [headroom]
    lowers = [hr_lower]
    uppers = [hr_upper]
    if reserve_supply_cap is not None:
        cap = np.asarray(reserve_supply_cap, dtype=float).reshape(n_hr, T)
        crows: list[np.ndarray] = []
        ccols: list[np.ndarray] = []
        cvals: list[np.ndarray] = []
        for h in range(n_hr):
            for p in np.flatnonzero(hr_prod[h]):
                crows.append(np.full(n_zones, h))
                ccols.append(layout._reserve_off + int(p) * n_zones + z_all)
                cvals.append(np.ones(n_zones))
                if gate:
                    # Duration-gated storage AS counts under the same supply cap
                    # (RTOLCAP includes online batteries), so its RS[p,z] joins
                    # each tier's cap row exactly as the thermal R[p,z] does.
                    crows.append(np.full(n_zones, h))
                    ccols.append(layout._storage_reserve_off + int(p) * n_zones + z_all)
                    cvals.append(np.ones(n_zones))
        cap_per_hour = sp.coo_matrix(
            (np.concatenate(cvals), (np.concatenate(crows), np.concatenate(ccols))),
            shape=(n_hr, layout.vars_per_hour),
        ).tocsr()
        cap_block = sp.kron(sp.eye(T, format="csr"), cap_per_hour, format="csr")
        # Hour-major RHS (row t*n_hr + h): cap is (n_hr, T) -> transpose -> ravel.
        blocks.append(cap_block)
        lowers.append(np.full(n_hr * T, -np.inf))
        uppers.append(cap.T.ravel())

    # --- Optional ON-LINE-CAPACITY ENVELOPE block, (n_hr, vph). The G-22
    # commitment-thinness cap: one system-wide row per headroom row h bounding
    # that row's ENERGY + RESERVE by the committed on-line capacity —
    #   sum_z sum_{g in E_h ∩ z} P[g] + sum_z sum_{p in Prod_h} R[p,z]
    #       (+ sum_z sum_p RS[p,z] if the storage duration gate is on)
    #       <= online_capacity_cap[h,t].
    # Identical placement/shape to the reserve-supply cap above (inserted BEFORE
    # the balance rows so the balance dual indexing is unchanged) — but the added
    # P terms make it condition-responsive: the LP can serve/reserve no more
    # thermal than the real system had on-line, so on a tight (high-energy) hour
    # reserve is forced into shortage and the ORDC/co-opt channel prices the hour
    # up with NO offer-height change. Non-envelope tiers carry the uncapped
    # sentinel RHS (scarcity.ercot_online_capacity_envelope_mw), so their row is
    # always slack. Absent (``online_capacity_cap is None``) the LP is unchanged.
    if online_capacity_cap is not None:
        oc = np.asarray(online_capacity_cap, dtype=float).reshape(n_hr, T)
        erows: list[np.ndarray] = []
        ecols: list[np.ndarray] = []
        evals: list[np.ndarray] = []
        for h in range(n_hr):
            # eligible thermal energy P[g] for this tier's generators (zone-summed
            # into the single system-wide row h — one row per tier per hour).
            e_idx = np.flatnonzero(hr_elig[h])
            erows.append(np.full(e_idx.size, h))
            ecols.append(e_idx)
            evals.append(np.ones(e_idx.size))
            for p in np.flatnonzero(hr_prod[h]):
                erows.append(np.full(n_zones, h))
                ecols.append(layout._reserve_off + int(p) * n_zones + z_all)
                evals.append(np.ones(n_zones))
                if gate:
                    erows.append(np.full(n_zones, h))
                    ecols.append(layout._storage_reserve_off + int(p) * n_zones + z_all)
                    evals.append(np.ones(n_zones))
        env_per_hour = sp.coo_matrix(
            (np.concatenate(evals), (np.concatenate(erows), np.concatenate(ecols))),
            shape=(n_hr, layout.vars_per_hour),
        ).tocsr()
        env_block = sp.kron(sp.eye(T, format="csr"), env_per_hour, format="csr")
        blocks.append(env_block)
        lowers.append(np.full(n_hr * T, -np.inf))
        uppers.append(oc.T.ravel())

    # --- Storage duration-gate blocks (ERCOT endogenous storage AS). Two
    # per-zone-hour row families, inserted BEFORE the balance rows so the balance
    # dual stays the final n_fam*T. Both fully vectorized (sp.kron over hours).
    #  1. Power competition (n_zones per hour): the storage power split, now
    #     explicit since storage left the thermal headroom —
    #       sum_c RS[c,z] + sum_{s in z}(Dis[s] - Chg[s]) <= sum_{s in z} cap[s].
    #  2. Duration gate (n_zones per hour): the ESR State-of-Charge rule —
    #       sum_c dur_c * RS[c,z] - sum_{s in z} SOC[s] <= 0,
    #     so the stored energy (zone-aggregate SOC) must cover each product's
    #     award for its full deployment duration. Gating on the same-hour SOC[t]
    #     column is exact for held (undeployed) reserve — the power row keeps that
    #     MW from also discharging, so the SOC is not drawn down.
    if gate:
        # Power-competition per-hour matrix, (n_zones, vph).
        pw_rows: list[np.ndarray] = []
        pw_cols: list[np.ndarray] = []
        pw_vals: list[np.ndarray] = []
        for c in range(n_classes):
            pw_rows.append(z_all)
            pw_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            pw_vals.append(np.ones(n_zones))  # +RS[c,z]
        pw_rows.append(s_zone)
        pw_cols.append(layout._dis_off + s_idx)
        pw_vals.append(np.ones(n_storage))  # +Dis
        pw_rows.append(s_zone)
        pw_cols.append(layout._chg_off + s_idx)
        pw_vals.append(-np.ones(n_storage))  # -Chg
        pw_per_hour = sp.coo_matrix(
            (
                np.concatenate(pw_vals),
                (np.concatenate(pw_rows), np.concatenate(pw_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        pw_block = sp.kron(sp.eye(T, format="csr"), pw_per_hour, format="csr")
        # RHS: zone-summed storage power cap, (n_zones, T) hour-major.
        if spc.ndim == 2:
            zcap = zone_storage @ spc  # (n_zones, T)
        else:
            zcap = np.broadcast_to((zone_storage @ spc)[:, None], (n_zones, T))
        blocks.append(pw_block)
        lowers.append(np.full(n_zones * T, -np.inf))
        uppers.append(np.ascontiguousarray(zcap).T.ravel())

        # Duration-gate per-hour matrix, (n_zones, vph).
        du_rows: list[np.ndarray] = []
        du_cols: list[np.ndarray] = []
        du_vals: list[np.ndarray] = []
        for c in range(n_classes):
            du_rows.append(z_all)
            du_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            du_vals.append(np.full(n_zones, float(dur[c])))  # +dur_c * RS[c,z]
        du_rows.append(s_zone)
        du_cols.append(layout._soc_off + s_idx)
        du_vals.append(-np.ones(n_storage))  # -SOC[s]
        du_per_hour = sp.coo_matrix(
            (
                np.concatenate(du_vals),
                (np.concatenate(du_rows), np.concatenate(du_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        du_block = sp.kron(sp.eye(T, format="csr"), du_per_hour, format="csr")
        blocks.append(du_block)
        lowers.append(np.full(n_zones * T, -np.inf))
        uppers.append(np.zeros(n_zones * T))

    blocks.append(balance)
    lowers.append(bal_lower)
    uppers.append(bal_upper)
    # Free-concat (see _vstack_csr_free): drop the two large sub-block names so
    # the list is their sole owner and the shared-headroom block (T * n_gen nnz,
    # the largest here) is released before the stacked result is allocated.
    # Byte-identical to sp.vstack(blocks).
    del headroom, balance
    block = _vstack_csr_free(blocks, layout.total_columns)
    row_lower = np.concatenate(lowers)
    row_upper = np.concatenate(uppers)
    return block, row_lower, row_upper


def _build_reserve_rows_pergen(
    layout: VariableLayout,
    fleet: FleetArrays,
    reserve_requirement: np.ndarray,
    pergen_gen_idx: np.ndarray,
    pergen_col: np.ndarray | None = None,
    balance_zone_mask: np.ndarray | None = None,
    balance_ordc_counts: np.ndarray | None = None,
    posture_pools: np.ndarray | None = None,
    posture_mlf: np.ndarray | None = None,
    pergen_ramp10: np.ndarray | None = None,
    storage_zone_idx: np.ndarray | None = None,
    storage_power_cap: np.ndarray | None = None,
    storage_duration_h: np.ndarray | None = None,
    pergen_col_pool: np.ndarray | None = None,
    balance_col_mask: np.ndarray | None = None,
    online_gated_cols: np.ndarray | None = None,
    online_rho: float = 1.0,
    pool_ramp10_shared: np.ndarray | None = None,
) -> tuple[sp.csr_matrix, np.ndarray, np.ndarray]:
    """Build the PER-GENERATOR energy+reserve co-optimization rows.

    The per-unit alternative to :func:`_build_reserve_rows`: one reserve
    variable ``R[r,t]`` per reserve-providing *asset* instead of one per
    zone-class, so reserve competes with energy **on the same marginal unit**
    — the structure that prices the sub-shortage opportunity-cost reserve
    band (docs/multi-iso/pjm-reserve-ordc.md Phase 2). An asset is one
    generator by default (``pergen_col`` omitted: R column ``j`` pairs with
    ``pergen_gen_idx[j]``), or a group of generators sharing an R column
    (``pergen_col[j]`` maps member ``j`` to its column) — the tranche-binned
    fleets aggregate per (plant, class): a plant's tranches dispatch
    bang-bang, so headroom and the 10-minute ramp are plant properties
    (the ``pjm_online_reserve`` doctrine), and the aggregation cuts the
    per-gen LP's row/column count ~4x on a 15 GB box without changing the
    physics (``sum ramp10[tranches] == RAMP10_FRAC[class] x plant pmax``).
    Two families of rows, both vectorized (no hour loop):

    * **Joint headroom** — for each R column ``r`` and hour ``t``:
      ``sum_{members j of r} P[g_j,t] + R[r,t] <= sum_j cap[g_j,t]``
      (``cap = pmax x availability``; one P term for the default 1:1
      mapping). A MW held as reserve cannot also be dispatched as energy, so
      on a fully-loaded marginal asset the row's dual is the forgone energy
      margin — the opportunity cost that lifts the reserve clearing price
      above $0 without any shortfall. The 10-minute deliverability cap
      ``R[r] <= ramp10[r]`` is a *variable bound*
      (:func:`build_variable_bounds`), not a row.
    * **Reserve balance** — one row per reserve family ``f`` and hour ``t``:
      ``sum_{r: zone[r] in family f} R[r,t] + sum_{k in f} ORDC_k[t] >=
      requirement[f,t]``. Families follow the zone-mask convention of
      :func:`_build_reserve_rows` (PJM: the RTO Reserve Zone over every model
      zone, plus the nested Mid-Atlantic/Dominion Reserve Subzone — a MAD
      reserve MW counts toward both, Manual 11 sec 4.2). The binding family's
      dual is that family's reserve clearing price; the joint-headroom rows
      transfer it into the member zones' energy LMPs.

    Storage backs reserve via the SAME duration-gated per-zone ``RS[c,z]``
    columns as the zone-aggregate path (issue #1492, CAISO
    ``caiso_reserve_coopt``): when the layout allocated storage-reserve columns
    (``reserve_storage`` + ``storage_duration_h`` + storage present) and the
    three ``storage_*`` args are supplied, each family's balance row gains the
    ``RS[0,z]`` columns of its member zones, and the two zone-hour row families
    of the zone path are appended between the posture and balance blocks: power
    competition ``Σ_c RS[c,z] + Σ_{s∈z}(Dis−Chg) ≤ Σ_{s∈z} cap[s]`` and the SOC
    duration gate ``Σ_c dur_c·RS[c,z] − Σ_{s∈z} SOC[s] ≤ 0``. The pergen layout
    carries exactly one reserve class, so ``RS[0,z]`` backs every family over
    its member zones — the same co-drawn convention as the thermal R pool
    (CAISO spin/non-spin share the marginal MW, §27.1.2.4).

    Args:
        layout: Variable layout with ``n_reserve == n_r`` (R-column count) and
            ``n_reserve_classes == 1``.
        fleet: Fleet arrays supplying ``pmax``, ``(n_gen, T)`` availability and
            per-generator ``zone_idx``.
        reserve_requirement: ``(T,)`` (single family) or ``(n_families, T)``
            hourly requirement in MW.
        pergen_gen_idx: ``(n_members,)`` int — the fleet index of every member
            generator backing an R column.
        pergen_col: ``(n_members,)`` int — the R column of each member
            (``0..n_r-1``; every column must have at least one member and all
            of a column's members must share a zone). ``None`` is the 1:1
            identity (``n_members == n_r``).
        balance_zone_mask: ``(n_families, n_zones)`` boolean member-zone mask;
            ``None`` builds a single system-wide family.
        balance_ordc_counts: ``(n_families,)`` ORDC steps owned by each family
            (family-major partition of the ORDC block); ``None`` assigns every
            step to the single family.
        posture_pools: ``(q,)`` R-pool indices carrying an online-capacity
            variable U (the commitment-posture lever, design note §A). For a
            postured pool the joint-headroom row is re-anchored to online
            capacity — ``Σ P + R − U ≤ 0`` (same nnz + one U coefficient;
            the member-capacity RHS moves to U's upper bound) — and three
            posture families are appended between the joint and balance
            blocks: min-load coupling ``Σ P − mlf·U ≥ 0`` (pools with
            ``mlf > 0``), startup counting ``U[t] − U[t−1] − SU[t] ≤ 0``
            (cyclic, like the SOC boundary), and the online ramp gate
            ``R − ρ(t)·U ≤ 0`` with ``ρ = pool ramp10 / pool capacity``
            (offline capacity contributes no 10-minute ramp).
        posture_mlf: ``(q,)`` min-stable-when-online fraction per postured
            pool (CEMS-measured, reserve_config._posture_pool_params).
        pergen_ramp10: the ``(n_r,)`` or ``(n_r, T)`` deliverable-ramp caps
            (required with ``posture_pools`` for the ramp-gate ρ).
        pergen_col_pool: ``(n_r,)`` int — the joint-headroom POOL of each R
            column (PJM ``pjm_reserve_pergen_sync`` product split: a pool's
            synchronized and non-synchronized product columns share ONE joint
            P+R row and its member-capacity RHS, so a reserve award of either
            product consumes the same iron). When given, ``pergen_col`` maps
            members to POOLS (``0..n_pools-1``) rather than to R columns.
            ``None`` is the identity (columns ≡ pools) — byte-identical to
            the pre-split layout. Mutually exclusive with ``posture_pools``
            (the posture U re-anchor indexes pools 1:1 with R columns).
        balance_col_mask: ``(n_families, n_r)`` bool — each family's complete
            R-column selection (zone ∧ product), replacing the zone-only
            selection derived from ``balance_zone_mask``. ``None`` keeps the
            zone-derived selection (byte-identical).
        online_gated_cols: ``(n_r,)`` bool — R columns whose award must be
            backed by ON-LINE output (MISO ``miso_reserve_online_gated``,
            PREREG-miso167 §2: Regulating + Spinning require a synchronised
            resource, BPM-002). Each gated column ``r`` gains one coupling
            row per hour, ``R[r,t] − online_rho · Σ_{members j of pool(r)}
            P[g_j,t] ≤ 0`` — the ISO-agnostic online-gated row form of the
            zone-aggregate spec, at pool grain: idle capacity backs none of
            the gated product, so only generation that is actually running
            carries it. ``None`` (every flag-off path) adds no rows —
            byte-identical.
        online_rho: The measured online-headroom multiplier for the gated
            coupling rows (``data.online_reserve_rho`` /
            ``spec._identified_online_rho`` — MW of 10-minute deliverable
            headroom one MW of on-line output carries).
        pool_ramp10_shared: ``(n_pools, T)`` — the pool's availability-scaled
            10-minute deliverable ramp, enforced as one row per pool-hour
            over the SUM of the pool's product columns
            (``Σ_{r: pool(r)=p} R[r,t] ≤ pool_ramp10[p,t]``). Passed by the
            product-split layouts where the per-COLUMN
            ``reserve_pergen_ramp10`` bound alone would let the products
            stack to a multiple of the pool's physical ramp (MISO's Reg+Spin
            and Supplemental share the same iron's 10-minute capability).
            ``None`` adds no rows — byte-identical.

    Returns:
        ``(block, row_lower, row_upper)``: joint-headroom rows (``<=``,
        hour-major then R-column order), then the posture families when
        postured (min-load ``>=``, startup ``<=``, ramp gate ``<=``), then the
        storage duration-gate families when storage-gated (power competition
        ``<=``, SOC duration ``<=``), then balance rows (``>=``, hour-major
        then family order — the final ``n_families * T`` rows, the position
        the ``DispatchModel`` dual extraction relies on).
    """
    T = layout.T
    n_zones = layout.n_zones
    gidx = np.asarray(pergen_gen_idx, dtype=int)
    col = (
        np.arange(gidx.size)
        if pergen_col is None
        else np.asarray(pergen_col, dtype=int)
    )
    if col.shape != gidx.shape:
        raise ValueError(
            f"pergen_col shape {col.shape} != pergen_gen_idx shape {gidx.shape}"
        )
    n_r = layout.n_reserve
    # Product split (pergen_col_pool): pergen_col maps members to POOLS and
    # col_pool maps each of the n_r R columns to its pool; identity when the
    # split is absent (pools ≡ columns, the pre-split layout, byte-identical).
    if pergen_col_pool is not None:
        if posture_pools is not None:
            raise ValueError(
                "pergen_col_pool (the product-split pergen layout) is not "
                "composable with posture_pools — the posture U re-anchor "
                "indexes pools 1:1 with R columns"
            )
        col_pool = np.asarray(pergen_col_pool, dtype=int)
        if col_pool.shape != (n_r,):
            raise ValueError(f"pergen_col_pool shape {col_pool.shape} != ({n_r},)")
        n_pools = int(col_pool.max()) + 1 if col_pool.size else 0
        if np.unique(col_pool).size != n_pools:
            raise ValueError("pergen_col_pool must cover every pool 0..n_pools-1")
        if (
            col.size == 0
            or int(col.max()) + 1 != n_pools
            or (np.unique(col).size != n_pools)
        ):
            raise ValueError(
                "with pergen_col_pool, pergen_col must cover every pool "
                f"0..n_pools-1 (n_pools={n_pools}, "
                f"pools covered={np.unique(col).size})"
            )
    else:
        col_pool = np.arange(n_r, dtype=int)
        n_pools = n_r
        if col.size == 0 or int(col.max()) + 1 != n_r or np.unique(col).size != n_r:
            raise ValueError(
                "pergen_col must cover every R column 0..n_reserve-1 "
                f"(n_reserve={n_r}, columns covered={np.unique(col).size})"
            )
    zone_idx = np.asarray(fleet.zone_idx, dtype=int)
    # Duration-gated storage reserve (issue #1492): active iff the layout
    # allocated RS columns (it already encoded reserve_storage + durations +
    # storage-present) AND the storage args reached this builder. The layout's
    # class count sizes the RS block; the pergen layout guarantees one class.
    gate = (
        layout.n_storage_reserve > 0
        and storage_zone_idx is not None
        and storage_power_cap is not None
        and storage_duration_h is not None
    )
    if gate:
        n_classes = layout.n_reserve_classes
        dur = np.asarray(storage_duration_h, dtype=float).reshape(n_classes)
        s_zone = np.asarray(storage_zone_idx, dtype=int)
        n_storage = s_zone.shape[0]
        s_idx = np.arange(n_storage)
        spc = np.asarray(storage_power_cap, dtype=float)
        zone_storage = _build_zone_storage_map(s_zone, n_zones, n_storage)
        z_all = np.arange(n_zones)
    # Member -> R-column incidence, for the summed-capacity RHS and the
    # per-column zone below.
    member_map = sp.csr_matrix(
        (np.ones(gidx.size), (col, np.arange(gidx.size))),
        shape=(n_pools, gidx.size),
    )
    # All of a pool's members must share a zone (a plant is in one zone) —
    # the balance families select R columns by zone. Column zone = its pool's
    # zone (identity map without the product split).
    pool_zone = np.zeros(n_pools, dtype=int)
    pool_zone[col] = zone_idx[gidx]
    if np.any(member_map @ (zone_idx[gidx] != pool_zone[col]).astype(float) > 0):
        raise ValueError("pergen_col groups generators from different zones")
    r_zone = pool_zone[col_pool]

    # --- Joint-headroom per-hour block, (n_pools, vph): pool row p reads
    # sum_{members j} P[g_j] + sum_{columns r of p} R[r] <= sum_j cap[g_j]
    # (one R term per pool without the product split). A POSTURED pool's row
    # is re-anchored to its online capacity instead — sum P + R − U <= 0 —
    # so reserve can only come from capacity the LP keeps online; the member
    # capacity sum moves to U's upper bound (build_variable_bounds).
    q = 0 if posture_pools is None else int(np.asarray(posture_pools).size)
    jrows = [col, col_pool]
    jcols = [layout._p_off + gidx, layout._reserve_off + np.arange(n_r)]
    jvals = [np.ones(gidx.size), np.ones(n_r)]
    # Summed member capacity per pool, (n_pools, T). Compute pmax*availability
    # ONLY on the reserve members instead of materializing the full (n_gen, T)
    # fleet ``cap`` and fancy-indexing it: byte-identical operands (member i is
    # ``pmax[gidx[i]] * availability[gidx[i]]`` either way), but the dense
    # intermediate is (n_members, T) rather than (n_gen, T) held alongside its
    # (n_members, T) index copy, and it is released before the large ``joint``
    # kron allocates — driver (a) of the reserve-column-construction peak (G-40).
    cap_members = fleet.pmax[gidx][:, np.newaxis] * fleet.availability[gidx]
    pool_cap = member_map @ cap_members  # (n_pools, T) member caps summed per pool
    del cap_members
    joint_rhs = pool_cap  # only copied below when a postured pool mutates it
    if q:
        ppools = np.asarray(posture_pools, dtype=int)
        jrows.append(ppools)
        jcols.append(layout._posture_u_off + np.arange(q))
        jvals.append(-np.ones(q))
        # Zero the postured pools' capacity RHS on a copy — pool_cap must stay
        # intact for the ramp-gate ρ (uses pool_cap[ppools]) below.
        joint_rhs = pool_cap.copy()
        joint_rhs[ppools, :] = 0.0
    joint_per_hour = sp.coo_matrix(
        (
            np.concatenate(jvals),
            (np.concatenate(jrows), np.concatenate(jcols)),
        ),
        shape=(n_pools, layout.vars_per_hour),
    ).tocsr()
    joint = sp.kron(sp.eye(T, format="csr"), joint_per_hour, format="csr")
    # RHS hour-major (row t*n_pools + p): member caps summed per pool,
    # (n_pools, T); 0 for postured pools (the capacity bound lives on U).
    joint_upper = joint_rhs.T.ravel()
    joint_lower = np.full(n_pools * T, -np.inf)

    # --- Commitment-posture families (between joint and balance so the
    # balance rows stay the final n_families*T — the dual-extraction anchor).
    posture_blocks: list[sp.csr_matrix] = []
    posture_lower: list[np.ndarray] = []
    posture_upper: list[np.ndarray] = []
    if q:
        mlf = np.asarray(posture_mlf, dtype=float)
        # (a) Min-load coupling, pools with measured mlf > 0:
        #     sum_{members} P − mlf·U >= 0 (being online costs min-load
        #     energy; binds only capacity the LP itself holds online).
        m_sel = np.flatnonzero(mlf > 0.0)
        if m_sel.size:
            sel_pool = ppools[m_sel]  # R-pool index per min-load row
            # Members of the selected pools: map each member's pool to its
            # min-load row (or -1 when the member's pool carries no row).
            pool_to_row = np.full(n_r, -1, dtype=int)
            pool_to_row[sel_pool] = np.arange(m_sel.size)
            mem_row = pool_to_row[col]
            mem_ok = mem_row >= 0
            ml_per_hour = sp.coo_matrix(
                (
                    np.concatenate([np.ones(int(mem_ok.sum())), -mlf[m_sel]]),
                    (
                        np.concatenate([mem_row[mem_ok], np.arange(m_sel.size)]),
                        np.concatenate(
                            [
                                layout._p_off + gidx[mem_ok],
                                layout._posture_u_off + m_sel,
                            ]
                        ),
                    ),
                ),
                shape=(m_sel.size, layout.vars_per_hour),
            ).tocsr()
            posture_blocks.append(
                sp.kron(sp.eye(T, format="csr"), ml_per_hour, format="csr")
            )
            posture_lower.append(np.zeros(m_sel.size * T))
            posture_upper.append(np.full(m_sel.size * T, np.inf))

        # (b) Startup counting, cyclic: U[p,t] − U[p,t−1] − SU[p,t] <= 0.
        #     Same wrap convention as the storage SOC boundary: hour 0 links
        #     to hour T−1, so a year-crossing posture carries no free start.
        d0 = sp.coo_matrix(
            (
                np.concatenate([np.ones(q), -np.ones(q)]),
                (
                    np.concatenate([np.arange(q), np.arange(q)]),
                    np.concatenate(
                        [
                            layout._posture_u_off + np.arange(q),
                            layout._posture_su_off + np.arange(q),
                        ]
                    ),
                ),
            ),
            shape=(q, layout.vars_per_hour),
        ).tocsr()
        d_prev = sp.coo_matrix(
            (
                -np.ones(q),
                (np.arange(q), layout._posture_u_off + np.arange(q)),
            ),
            shape=(q, layout.vars_per_hour),
        ).tocsr()
        shift_prev = sp.csr_matrix(
            (np.ones(T), (np.arange(T), (np.arange(T) - 1) % T)),
            shape=(T, T),
        )
        posture_blocks.append(
            sp.kron(sp.eye(T, format="csr"), d0, format="csr")
            + sp.kron(shift_prev, d_prev, format="csr")
        )
        posture_lower.append(np.full(q * T, -np.inf))
        posture_upper.append(np.zeros(q * T))

        # (c) Online ramp gate: R[p,t] − ρ[p,t]·U[p,t] <= 0 with
        #     ρ = pool deliverable ramp10 / pool capacity (both availability-
        #     scaled, so ρ is the pool's class ramp fraction) — offline
        #     capacity contributes no 10-minute ramp, the design's scarcity
        #     payoff. Hour-varying coefficients, so built directly (no kron).
        if pergen_ramp10 is None:
            raise ValueError("posture_pools requires pergen_ramp10 for the ramp gate")
        r10 = np.asarray(pergen_ramp10, dtype=float)
        if r10.ndim == 1:
            r10 = np.broadcast_to(r10[:, np.newaxis], (n_r, T))
        with np.errstate(invalid="ignore", divide="ignore"):
            rho = np.where(pool_cap[ppools] > 0, r10[ppools] / pool_cap[ppools], 0.0)
        vph = layout.vars_per_hour
        t_idx = np.repeat(np.arange(T), q)  # hour of each row, hour-major
        j_idx = np.tile(np.arange(q), T)  # posture index of each row
        rg_rows = np.arange(q * T)
        rg = sp.csr_matrix(
            (
                np.concatenate([np.ones(q * T), -rho[j_idx, t_idx]]),
                (
                    np.concatenate([rg_rows, rg_rows]),
                    np.concatenate(
                        [
                            t_idx * vph + layout._reserve_off + ppools[j_idx],
                            t_idx * vph + layout._posture_u_off + j_idx,
                        ]
                    ),
                ),
            ),
            shape=(q * T, layout.total_columns),
        )
        posture_blocks.append(rg)
        posture_lower.append(np.full(q * T, -np.inf))
        posture_upper.append(np.zeros(q * T))

    # --- Reserve-balance per-hour block, (n_families, vph): family f sums the
    # R columns of its member zones' generators plus its ORDC-step slice.
    if balance_zone_mask is None:
        zmask = np.ones((1, n_zones), dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(1, T)
        ordc_counts = np.array([layout.n_ordc_steps], dtype=int)
    else:
        zmask = np.asarray(balance_zone_mask, dtype=bool)
        req2d = np.asarray(reserve_requirement, dtype=float).reshape(zmask.shape[0], T)
        ordc_counts = np.asarray(balance_ordc_counts, dtype=int)
    n_fam = zmask.shape[0]
    # Per-family R-column selection: the product split supplies each family's
    # complete (zone ∧ product) mask; otherwise columns are selected by zone.
    cmask = None
    if balance_col_mask is not None:
        cmask = np.asarray(balance_col_mask, dtype=bool)
        if cmask.shape != (n_fam, n_r):
            raise ValueError(
                f"balance_col_mask shape {cmask.shape} != ({n_fam}, {n_r})"
            )
    brows: list[np.ndarray] = []
    bcols: list[np.ndarray] = []
    bvals: list[np.ndarray] = []
    for f in range(n_fam):
        sel = np.flatnonzero(cmask[f] if cmask is not None else zmask[f][r_zone])
        brows.append(np.full(sel.size, f))
        bcols.append(layout._reserve_off + sel)
        bvals.append(np.ones(sel.size))
        if gate:
            # Storage's duration-gated RS[c,z] backs every family over its
            # member zones (single pergen reserve class — the co-drawn
            # spin/non-spin convention of the thermal pool above).
            zsel = np.flatnonzero(zmask[f])
            for c in range(n_classes):
                brows.append(np.full(zsel.size, f))
                bcols.append(layout._storage_reserve_off + c * n_zones + zsel)
                bvals.append(np.ones(zsel.size))
    off = 0
    for f in range(n_fam):
        k = int(ordc_counts[f])
        if k:
            idx = np.arange(off, off + k)
            brows.append(np.full(k, f))
            bcols.append(layout._ordc_off + idx)
            bvals.append(np.ones(k))
            off += k
    bal_per_hour = sp.coo_matrix(
        (np.concatenate(bvals), (np.concatenate(brows), np.concatenate(bcols))),
        shape=(n_fam, layout.vars_per_hour),
    ).tocsr()
    balance = sp.kron(sp.eye(T, format="csr"), bal_per_hour, format="csr")
    bal_lower = req2d.T.ravel()
    bal_upper = np.full(n_fam * T, np.inf)

    # --- Storage duration-gate blocks (issue #1492 pergen storage AS): the two
    # zone-hour row families of the zone-aggregate path, verbatim, inserted
    # BEFORE the balance rows so the balance dual stays the final n_fam*T.
    #  1. Power competition: sum_c RS[c,z] + sum_{s in z}(Dis - Chg)
    #     <= sum_{s in z} cap[s] — a MW held as reserve cannot also discharge.
    #  2. Duration gate: sum_c dur_c * RS[c,z] - sum_{s in z} SOC[s] <= 0 —
    #     the stored energy must cover the award for its sustain duration
    #     (CAISO ASSOC: 30-min spin/non-spin sustain).
    gate_blocks: list[sp.csr_matrix] = []
    gate_lower: list[np.ndarray] = []
    gate_upper: list[np.ndarray] = []
    if gate:
        pw_rows: list[np.ndarray] = []
        pw_cols: list[np.ndarray] = []
        pw_vals: list[np.ndarray] = []
        for c in range(n_classes):
            pw_rows.append(z_all)
            pw_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            pw_vals.append(np.ones(n_zones))  # +RS[c,z]
        pw_rows.append(s_zone)
        pw_cols.append(layout._dis_off + s_idx)
        pw_vals.append(np.ones(n_storage))  # +Dis
        pw_rows.append(s_zone)
        pw_cols.append(layout._chg_off + s_idx)
        pw_vals.append(-np.ones(n_storage))  # -Chg
        pw_per_hour = sp.coo_matrix(
            (
                np.concatenate(pw_vals),
                (np.concatenate(pw_rows), np.concatenate(pw_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        gate_blocks.append(sp.kron(sp.eye(T, format="csr"), pw_per_hour, format="csr"))
        # RHS: zone-summed storage power cap, (n_zones, T) hour-major.
        if spc.ndim == 2:
            zcap = zone_storage @ spc  # (n_zones, T)
        else:
            zcap = np.broadcast_to((zone_storage @ spc)[:, None], (n_zones, T))
        gate_lower.append(np.full(n_zones * T, -np.inf))
        gate_upper.append(np.ascontiguousarray(zcap).T.ravel())

        du_rows: list[np.ndarray] = []
        du_cols: list[np.ndarray] = []
        du_vals: list[np.ndarray] = []
        for c in range(n_classes):
            du_rows.append(z_all)
            du_cols.append(layout._storage_reserve_off + c * n_zones + z_all)
            du_vals.append(np.full(n_zones, float(dur[c])))  # +dur_c * RS[c,z]
        du_rows.append(s_zone)
        du_cols.append(layout._soc_off + s_idx)
        du_vals.append(-np.ones(n_storage))  # -SOC[s]
        du_per_hour = sp.coo_matrix(
            (
                np.concatenate(du_vals),
                (np.concatenate(du_rows), np.concatenate(du_cols)),
            ),
            shape=(n_zones, layout.vars_per_hour),
        ).tocsr()
        gate_blocks.append(sp.kron(sp.eye(T, format="csr"), du_per_hour, format="csr"))
        gate_lower.append(np.full(n_zones * T, -np.inf))
        gate_upper.append(np.zeros(n_zones * T))

    # --- Online-gated coupling + shared product-ramp blocks (MISO
    # miso_reserve_online_gated; both None on every flag-off path — zero rows,
    # byte-identical). Inserted BEFORE the balance rows so the balance dual
    # stays the final n_fam*T (the dual-extraction anchor).
    gated_blocks: list[sp.csr_matrix] = []
    gated_lower: list[np.ndarray] = []
    gated_upper: list[np.ndarray] = []
    if online_gated_cols is not None:
        gcols = np.flatnonzero(np.asarray(online_gated_cols, dtype=bool))
        if gcols.size:
            # Per-hour block (n_gated, vph): +1 on the gated R column, and
            # −rho on every member P column of its pool. Coefficients are
            # hour-constant, so one kron replicates the pattern (rule 2
            # [R-VECTOR] — no hour loop; the loop below is over the O(n_r)
            # gated columns, like the balance builder's family loop).
            g_rows = [np.arange(gcols.size)]
            g_cols = [layout._reserve_off + gcols]
            g_vals = [np.ones(gcols.size)]
            for k, r in enumerate(gcols):
                # members map to POOLS (``col``); gated column r draws on the
                # members of its own pool (identity when pools ≡ columns).
                m_sel = np.flatnonzero(col == col_pool[r])
                g_rows.append(np.full(m_sel.size, k))
                g_cols.append(layout._p_off + gidx[m_sel])
                g_vals.append(np.full(m_sel.size, -float(online_rho)))
            og_per_hour = sp.coo_matrix(
                (
                    np.concatenate(g_vals),
                    (np.concatenate(g_rows), np.concatenate(g_cols)),
                ),
                shape=(gcols.size, layout.vars_per_hour),
            ).tocsr()
            gated_blocks.append(
                sp.kron(sp.eye(T, format="csr"), og_per_hour, format="csr")
            )
            gated_lower.append(np.full(gcols.size * T, -np.inf))
            gated_upper.append(np.zeros(gcols.size * T))
    if pool_ramp10_shared is not None:
        pr = np.asarray(pool_ramp10_shared, dtype=float)
        if pr.shape != (n_pools, T):
            raise ValueError(f"pool_ramp10_shared shape {pr.shape} != ({n_pools}, {T})")
        sr_per_hour = sp.coo_matrix(
            (
                np.ones(n_r),
                (col_pool, layout._reserve_off + np.arange(n_r)),
            ),
            shape=(n_pools, layout.vars_per_hour),
        ).tocsr()
        gated_blocks.append(sp.kron(sp.eye(T, format="csr"), sr_per_hour, format="csr"))
        gated_lower.append(np.full(n_pools * T, -np.inf))
        gated_upper.append(np.ascontiguousarray(pr).T.ravel())

    # Free-concat the reserve sub-blocks (joint headroom is by far the largest —
    # T * n_members nnz). Drop the block names first so the list owns them and
    # _vstack_csr_free can release joint before allocating the stacked result,
    # instead of scipy.vstack holding joint + result simultaneously. Byte-
    # identical; this is the reserve-column-construction peak the OOM log names.
    _res_sub: list[sp.csr_matrix | None] = [
        joint,
        *posture_blocks,
        *gate_blocks,
        *gated_blocks,
        balance,
    ]
    del joint, balance, posture_blocks, gate_blocks, gated_blocks
    block = _vstack_csr_free(_res_sub, layout.total_columns)
    row_lower = np.concatenate(
        [joint_lower, *posture_lower, *gate_lower, *gated_lower, bal_lower]
    )
    row_upper = np.concatenate(
        [joint_upper, *posture_upper, *gate_upper, *gated_upper, bal_upper]
    )
    return block, row_lower, row_upper


def storage_reserve_mw(
    reserve_dispatch: np.ndarray,
    storage_charge: np.ndarray,
    storage_discharge: np.ndarray,
    storage_power_cap: np.ndarray,
    storage_zone_idx: np.ndarray,
    n_reserve_classes: int,
) -> np.ndarray:
    """Attribute the co-opt's cleared zone reserve to storage, ``(n_zones, T)`` MW.

    The endogenous storage energy-vs-AS split (``ercot_storage_as_endogenous``)
    runs storage and thermal on **one shared per-zone reserve pool** in the
    co-optimization headroom rows (``_build_reserve_rows`` ``use_storage`` block):
    a unit's upward-reserve room ``cap − discharge + charge`` competes with its
    own arbitrage on the same power cap, so the LP's energy-vs-AS *choice* is
    exact, but the cleared reserve variable ``R[c,z]`` is a single pooled value
    backed by thermal **and** storage room and is not split between them by the
    LP. This attributes storage's share of that pool for VALIDATION ONLY — the
    measured-vs-modeled battery AS-vs-energy split — never feeding back into the
    LP.

    The attribution is **storage-first by opportunity cost**: a battery's
    marginal cost of holding upward reserve is near zero (just the forgone energy
    arbitrage), and ERCOT batteries are the dominant, fastest fast-AS provider,
    so in a reserve-priced hour the LP fills the requirement from storage room
    before dearer thermal headroom. Storage AS in zone ``z`` hour ``t`` is then
    ``min(storage upward room, total cleared zone reserve)`` — exact when storage
    is the marginal fast-AS provider, an upper bound otherwise. Fully vectorized
    (no hour loop): the per-zone reserve is the sum across reserve classes (each
    AS product is a class in the multi-product co-opt), and storage room is
    scatter-summed to zones.

    Args:
        reserve_dispatch: ``(n_reserve_classes * n_zones, T)`` cleared reserve,
            class-major (``DispatchResult.reserve_dispatch``).
        storage_charge: ``(n_storage, T)`` cleared charge MW.
        storage_discharge: ``(n_storage, T)`` cleared discharge MW.
        storage_power_cap: ``(n_storage,)`` or ``(n_storage, T)`` power cap MW.
        storage_zone_idx: ``(n_storage,)`` zone index of each storage unit.
        n_reserve_classes: Number of reserve classes (AS products) folded into
            the per-zone reserve pool.

    Returns:
        ``(n_zones, T)`` MW of cleared reserve attributed to storage. Sum over
        zones (and divide hours) for the system AS-vs-energy split.
    """
    rd = np.asarray(reserve_dispatch, dtype=float)
    n_cz, T = rd.shape
    n_zones = n_cz // int(n_reserve_classes)
    # Per-zone total cleared reserve = sum across the reserve classes (products).
    zone_reserve = rd.reshape(int(n_reserve_classes), n_zones, T).sum(axis=0)
    # Storage upward-reserve room: cap − discharge + charge (the max additional
    # discharge swing a unit could offer up as reserve), floored at 0.
    cap = np.asarray(storage_power_cap, dtype=float)
    if cap.ndim == 1:
        cap = cap[:, None]
    room = np.clip(
        cap
        - np.asarray(storage_discharge, dtype=float)
        + np.asarray(storage_charge, dtype=float),
        0.0,
        None,
    )  # (n_storage, T)
    s_zone = np.asarray(storage_zone_idx, dtype=int)
    zone_room = np.zeros((n_zones, T), dtype=float)
    np.add.at(zone_room, s_zone, room)  # scatter-sum storage room into its zone
    return np.minimum(zone_room, zone_reserve)

"""Decision-variable bounds for the dispatch LP.

Package split of ``model/dispatch.py`` (refactor-consolidation plan §5 item
7). Pure code motion — :func:`build_variable_bounds` is byte-identical to
its pre-split ``dispatch.py`` source.
"""

import numpy as np

from market_sim.data.fleet import FleetArrays
from market_sim.model.lp.layout import VariableLayout


def build_variable_bounds(
    layout: VariableLayout,
    fleet: FleetArrays,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    storage_power_cap: np.ndarray | None = None,
    storage_energy_cap: np.ndarray | None = None,
    ttc: np.ndarray | None = None,
    ordc_step_widths: np.ndarray | None = None,
    link_bidirectional: np.ndarray | None = None,
    reserve_pergen_ramp10: np.ndarray | None = None,
    ttc_import: np.ndarray | None = None,
    posture_ucap: np.ndarray | None = None,
    wind_curtail_share: np.ndarray | None = None,
    solar_curtail_share: np.ndarray | None = None,
    storage_soc_min: np.ndarray | None = None,
    storage_discharge_min: np.ndarray | None = None,
    storage_charge_cap: np.ndarray | None = None,
    storage_discharge_cap: np.ndarray | None = None,
    dis_tranche_arm_idx: np.ndarray | None = None,
    dis_tranche_width: np.ndarray | None = None,
    hydro_cascade_pond_cap: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Assemble the LP column (decision-variable) bound vectors.

    Bounds, by variable block:

    * Thermal generation: ``pmin <= P <= pmax * availability``.
    * Wind: ``0 <= W <= wind_cf * wind_cap``.
    * Solar: ``0 <= S <= solar_cf * solar_cap``.
    * Storage: ``0 <= Chg, Dis <= power_cap``; ``0 <= SOC <= energy_cap``.
    * Transmission: ``-ttc <= Flow <= ttc`` (bidirectional links); a
      one-way link (``link_bidirectional[ln]`` False) is bounded
      ``0 <= Flow <= ttc`` so it can carry power only in its from->to
      direction (used to give an interface an asymmetric rating by pairing
      two opposite one-way links with different TTCs).
    * Load slack: ``0 <= Slack <= inf``.
    * Overgeneration dump: ``0 <= Dump <= inf``.

    Args:
        layout: Variable layout describing the column structure.
        fleet: Vectorized fleet arrays; supplies ``pmin``, ``pmax`` and the
            ``(n_gen, T)`` availability profile.
        wind_cf: Wind capacity factor of shape ``(n_zones, T)``.
        wind_cap: Installed wind capacity per zone, shape ``(n_zones,)``.
        solar_cf: Solar capacity factor of shape ``(n_zones, T)``.
        solar_cap: Installed solar capacity per zone, shape ``(n_zones,)``.
        storage_power_cap: Charge/discharge power cap, shape ``(n_storage,)``
            or hour-varying ``(n_storage, T)`` (COD intra-year ramp).
        storage_energy_cap: SOC energy cap, shape ``(n_storage,)`` or
            ``(n_storage, T)``.
        ttc: Total transfer capability per link, shape ``(n_links,)``
            (static) or ``(T, n_links)`` (per-hour seasonal limit).
        ttc_import: Optional reverse-direction (to->from) capability, same
            accepted shapes as ``ttc``. When given, the flow lower bound is
            ``-ttc_import`` instead of ``-ttc`` — used when an export-side
            stability limit (an ERCOT GTC) caps the forward direction while
            the import direction keeps its thermal rating. ``None`` keeps
            the symmetric ``-ttc`` bound (byte-identical prior behaviour).

    Returns:
        Tuple ``(col_lower, col_upper)`` of length ``layout.total_columns``.
    """
    T = layout.T  # T: number of hours
    vph = layout.vars_per_hour

    col_lower = np.zeros((T, vph), dtype=float)
    col_upper = np.zeros((T, vph), dtype=float)

    # Thermal generation: pmin <= P <= pmax * availability. A per-hour
    # min_gen (e.g. the seasonal ST_GAS reliability floor) overrides the
    # scalar pmin lower bound when present.
    if getattr(fleet, "min_gen", None) is not None:
        col_lower[:, layout._p_off : layout._w_off] = fleet.min_gen.T
    else:
        col_lower[:, layout._p_off : layout._w_off] = fleet.pmin[np.newaxis, :]
    col_upper[:, layout._p_off : layout._w_off] = (
        fleet.pmax[:, np.newaxis] * fleet.availability
    ).T

    # Wind: 0 <= W <= wind_cf * wind_cap * curtail_share. The optional
    # (n_zones, T) curtail_share in (0,1] is the ERCOT West Texas Export corridor
    # congestion ceiling (market_sim.data.curtailment_share); 1.0 / None elsewhere
    # leaves the uncurtailed potential bound unchanged.
    wind_upper = np.asarray(wind_cap, dtype=float)[:, np.newaxis] * np.asarray(
        wind_cf, dtype=float
    )
    if wind_curtail_share is not None:
        wind_upper = wind_upper * np.asarray(wind_curtail_share, dtype=float)
    col_upper[:, layout._w_off : layout._s_off] = wind_upper.T

    # Solar: 0 <= S <= solar_cf * solar_cap * curtail_share.
    solar_upper = np.asarray(solar_cap, dtype=float)[:, np.newaxis] * np.asarray(
        solar_cf, dtype=float
    )
    if solar_curtail_share is not None:
        solar_upper = solar_upper * np.asarray(solar_curtail_share, dtype=float)
    col_upper[:, layout._s_off : layout._chg_off] = solar_upper.T

    # Storage: 0 <= Chg, Dis <= power_cap; 0 <= SOC <= energy_cap. Caps are
    # static ``(n_storage,)`` arrays, or hour-varying ``(n_storage, T)`` —
    # the EIA-860 COD intra-year ramp (storage.storage_cap_profiles) feeds
    # the latter so capacity commissioned mid-year is offline before COD.
    if layout.n_storage:
        power_cap = np.asarray(storage_power_cap, dtype=float)
        power_cap = power_cap.T if power_cap.ndim == 2 else power_cap[np.newaxis, :]
        energy_cap = np.asarray(storage_energy_cap, dtype=float)
        energy_cap = energy_cap.T if energy_cap.ndim == 2 else energy_cap[np.newaxis, :]
        col_upper[:, layout._chg_off : layout._dis_off] = power_cap
        col_upper[:, layout._dis_off : layout._soc_off] = power_cap
        col_upper[:, layout._soc_off : layout._flow_off] = energy_cap
        if storage_charge_cap is not None:
            # Measured diurnal charge capability (CAISO battery shape anchor,
            # caiso_storage_shape_anchor): the fleet-wide measured p95
            # hour-of-day charge rate — tighter than the nameplate power cap
            # in the midday belly. Clipped at the power cap so the bound can
            # only tighten, never loosen.
            ccap = np.asarray(storage_charge_cap, dtype=float)
            ccap = ccap.T if ccap.ndim == 2 else ccap[np.newaxis, :]
            col_upper[:, layout._chg_off : layout._dis_off] = np.minimum(
                ccap, power_cap
            )
        if storage_discharge_cap is not None:
            # Discharge-side leg of the same measured envelope.
            dcap = np.asarray(storage_discharge_cap, dtype=float)
            dcap = dcap.T if dcap.ndim == 2 else dcap[np.newaxis, :]
            col_upper[:, layout._dis_off : layout._soc_off] = np.minimum(
                dcap, power_cap
            )
        if storage_discharge_min is not None:
            # Measured-award AS→energy deployment floor (ERCOT
            # ercot_storage_as_deployment): the released reserve draw-down that
            # the real fleet discharges at the net-load ramp. Clipped at the
            # (possibly hour-varying) discharge power cap so the bound pair stays
            # feasible by construction — the caller adds the deployed MW back to
            # ``storage_power_cap`` (rule 19: released from the AS reservation),
            # so cap ≥ floor holds.
            dmin = np.asarray(storage_discharge_min, dtype=float)
            dmin = dmin.T if dmin.ndim == 2 else dmin[np.newaxis, :]
            col_lower[:, layout._dis_off : layout._soc_off] = np.minimum(
                dmin, col_upper[:, layout._dis_off : layout._soc_off]
            )
        if storage_soc_min is not None:
            # Measured AS sustain floor (CAISO battery reservation): the SOC
            # may not be arbitraged below the tariff sustain energy of the
            # hour's awards. Clipped at the (possibly hour-varying) energy cap
            # so the bound pair stays feasible by construction.
            soc_min = np.asarray(storage_soc_min, dtype=float)
            soc_min = soc_min.T if soc_min.ndim == 2 else soc_min[np.newaxis, :]
            col_lower[:, layout._soc_off : layout._flow_off] = np.minimum(
                soc_min, energy_cap
            )

    # Transmission flow: -ttc <= Flow <= ttc (bidirectional). A 1-D ``ttc``
    # (n_links,) broadcasts across all hours (the static-limit path); a 2-D
    # ``ttc`` (T, n_links) sets a per-hour limit per link, letting an interface
    # follow a seasonal envelope (NYISO Central-East monthly TTC).
    if layout.n_links:
        ttc_arr = np.asarray(ttc, dtype=float)
        if ttc_arr.ndim == 1:
            ttc_arr = ttc_arr[np.newaxis, :]
        if ttc_import is not None:
            # Asymmetric interface: the import (to->from) direction keeps its
            # own rating rather than mirroring the export cap (ERCOT measured
            # GTC overlay — a stability limit on exports only).
            imp_arr = np.asarray(ttc_import, dtype=float)
            if imp_arr.ndim == 1:
                imp_arr = imp_arr[np.newaxis, :]
            lower_arr = -imp_arr
        else:
            lower_arr = -ttc_arr
        if link_bidirectional is not None:
            # One-way links carry power only from->to: floor their flow at 0
            # (so a pair of opposite one-way links gives an asymmetric rating).
            oneway = ~np.asarray(link_bidirectional, dtype=bool)
            if oneway.any():
                lower_arr = np.where(oneway[np.newaxis, :], 0.0, lower_arr)
        col_lower[:, layout._flow_off : layout._slack_off] = lower_arr
        col_upper[:, layout._flow_off : layout._slack_off] = ttc_arr

    # Load slack: 0 <= Slack <= inf.
    col_upper[:, layout._slack_off : layout._dump_off] = np.inf

    # Overgeneration dump: 0 <= Dump <= inf. Bounded to the dump block so the
    # co-opt reserve/ORDC blocks (when present) keep their own bounds below;
    # with no co-opt columns _reserve_off == vph, recovering "to the end".
    col_upper[:, layout._dump_off : layout._reserve_off] = np.inf

    # Energy+reserve co-optimization bounds (co-opt only).
    # Zone-aggregate spec: per-zone reserve R_z[z,t]: 0 <= R_z <= inf; the
    # per-zone shared-headroom constraint (build_constraints: sum_{eligible g
    # in z} P + R_z <= zone cap) is what bounds it, transferring the reserve
    # price into that zone's LMP. Per-gen spec (``reserve_pergen_ramp10``
    # given): 0 <= R[j] <= ramp10[g_j] — the unit's 10-minute deliverable ramp
    # (FleetArrays.ramp10) caps what it can hold as upward reserve; the joint
    # P+R row (_build_reserve_rows_pergen) enforces availability/headroom.
    # A static ``(n_r,)`` cap applies every hour (PJM); an hourly ``(n_r, T)``
    # cap carries availability-scaled deliverable ramp (MISO: an on-outage
    # unit contributes no 10-minute ramp, so the pool's cap thins with the
    # outage overlay).
    if layout.n_reserve > 0:
        if reserve_pergen_ramp10 is not None:
            ramp10 = np.asarray(reserve_pergen_ramp10, dtype=float)
            if ramp10.shape == (layout.n_reserve,):
                col_upper[:, layout._reserve_off : layout._ordc_off] = ramp10[
                    np.newaxis, :
                ]
            elif ramp10.shape == (layout.n_reserve, layout.T):
                col_upper[:, layout._reserve_off : layout._ordc_off] = ramp10.T
            else:
                raise ValueError(
                    f"reserve_pergen_ramp10 shape {ramp10.shape} != "
                    f"({layout.n_reserve},) or ({layout.n_reserve}, {layout.T})"
                )
        else:
            col_upper[:, layout._reserve_off : layout._ordc_off] = np.inf

    # Storage-reserve columns RS[c,z,t] (duration gate): 0 <= RS <= inf; the
    # storage power-competition row and the SOC duration-gate row (both in
    # _build_reserve_rows) are what bound them. col_upper defaults to 0 (fixed),
    # so this MUST set them free when the gate is active.
    if layout.n_storage_reserve > 0:
        sr0 = layout._storage_reserve_off
        col_upper[:, sr0 : sr0 + layout.n_storage_reserve] = np.inf

    # ORDC shortfall steps S_k[t]: 0 <= S_k <= step width (MW). Each step's
    # width is the MW span the published demand curve prices at that penalty.
    # Widths are static ``(n_ordc_steps,)`` on every published-curve design, or
    # HOURLY ``(n_ordc_steps, T)`` where the demand curve translates with an
    # hour-varying requirement (NYISO nyiso_ordc_measured_step_span: the curve
    # keeps its published shape but spans the measured as-enforced requirement
    # of the hour, so the widths — the only part of the curve that carries the
    # level, the RCPF penalties being requirement-independent — vary by hour).
    if layout.n_ordc_steps > 0:
        if ordc_step_widths is None:
            raise ValueError(
                "build_variable_bounds: n_ordc_steps > 0 requires ordc_step_widths"
            )
        widths = np.asarray(ordc_step_widths, dtype=float)
        if widths.shape == (layout.n_ordc_steps,):
            wid_hourly = widths[np.newaxis, :]
        elif widths.shape == (layout.n_ordc_steps, layout.T):
            wid_hourly = widths.T
        else:
            raise ValueError(
                f"ordc_step_widths shape {widths.shape} != "
                f"({layout.n_ordc_steps},) or ({layout.n_ordc_steps}, {layout.T})"
            )
        col_upper[:, layout._ordc_off : layout._ordc_off + layout.n_ordc_steps] = (
            wid_hourly
        )

    # Commitment-posture columns: 0 ≤ U[p,t] ≤ pool available capacity (the
    # hour-varying Σ pmax·availability over the pool's members — an on-outage
    # MW cannot be online, so a forced outage forces U down and the restart
    # after it pays a real startup, the correct physics); 0 ≤ SU[p,t] ≤ inf
    # (the startup rows bound it from below; its cost bounds it from above).
    if layout.n_posture > 0:
        ucap = np.asarray(posture_ucap, dtype=float)
        if ucap.shape != (layout.n_posture, layout.T):
            raise ValueError(
                f"posture_ucap shape {ucap.shape} != ({layout.n_posture}, {layout.T})"
            )
        u0 = layout._posture_u_off
        col_upper[:, u0 : u0 + layout.n_posture] = ucap.T
        su0 = layout._posture_su_off
        col_upper[:, su0 : su0 + layout.n_posture] = np.inf

    # RPS ACP escape column: 0 ≤ ACP ≤ inf (its objective cost, the ACP rate,
    # bounds it from above; the RPS row draws on it only when physical RECs are
    # short). Without this the zero-init upper bound would pin it at 0 and the
    # escape would not exist.
    if layout.n_rec_acp:
        a0 = layout._rec_acp_off
        col_upper[:, a0 : a0 + layout.n_rec_acp] = np.inf

    # Storage discharge tranche columns DisT[a,k,t] (ERCOT
    # ercot_storage_rt_offer_surface): 0 ≤ DisT[a,k,t] ≤ width_frac[k] ×
    # power_cap[s_a, t]. Each tranche's width fraction of the hour's power cap
    # enforces the ladder's rung MW; the decomposition row
    # (_build_dis_tranche_rows) ties Σ_k DisT to the base discharge, whose own
    # [dmin, power_cap] bound (untouched above) carries the shared cap and the
    # AS→energy deployment floor. Σ_k width_frac ≤ 1, so the tranche sum can
    # never exceed the base column's own cap — the tranches SHARE it.
    if layout.n_dis_tranche and dis_tranche_arm_idx is not None:
        arm = np.asarray(dis_tranche_arm_idx, dtype=int)
        wf = np.asarray(dis_tranche_width, dtype=float)  # (K,)
        k = wf.size
        # power_cap is (T, n_storage) or (1, n_storage); select the armed
        # battery columns and broadcast a static cap across all hours.
        pc_arm = power_cap[:, arm]  # (T or 1, n_arm)
        if pc_arm.shape[0] == 1:
            pc_arm = np.broadcast_to(pc_arm, (T, arm.size))
        # (T, n_arm, K) -> armed-major/tranche-minor (T, n_arm*K), matching
        # the layout stride _dis_tranche_off + a*K + k.
        tr_upper = wf[None, None, :] * pc_arm[:, :, None]
        dt0 = layout._dis_tranche_off
        col_upper[:, dt0 : dt0 + layout.n_dis_tranche] = tr_upper.reshape(
            T, arm.size * k
        )

    # Hydraulic-cascade columns (NWPP-36): spill 0 ≤ S[c,t] ≤ inf (the water
    # balance row bounds it from above — it is the slack between arriving
    # water and what the budget-capped turbines take); pond volume
    # 0 ≤ V[c,t] ≤ B_c, the plant's MEASURED operated pondage band in kcfs·h
    # (NID surface area × the CROHMS forebay range; hydro_cascade.py).
    if layout.n_cascade:
        n_c = layout.n_cascade // 2
        s0 = layout._cas_s_off
        col_upper[:, s0 : s0 + n_c] = np.inf
        v0 = layout._cas_v_off
        cap = np.asarray(hydro_cascade_pond_cap, dtype=float)
        if cap.shape != (n_c,):
            raise ValueError(f"hydro_cascade_pond_cap shape {cap.shape} != ({n_c},)")
        col_upper[:, v0 : v0 + n_c] = cap[np.newaxis, :]

    # Clip the lower bound to never exceed the upper bound. A committed
    # thermal generator carries a positive Pmin, but the commitment screen
    # (and hour-varying availability) can drive its upper bound to zero in
    # decommitted hours. Without this clip pmin > 0 = upper would make the
    # LP infeasible; the clip forces such a generator off (0 <= P <= 0).
    col_lower = np.minimum(col_lower, col_upper)

    return col_lower.ravel(), col_upper.ravel()

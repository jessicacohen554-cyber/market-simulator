"""Shared base ``dispatch_kwargs`` assembly + reserve co-opt wrapper (Stage 2).

Both orchestrators — ``runner.py`` (forecast) and ``scripts/run_calibration.py``
(backcast) — assembled the LP's base ``dispatch_kwargs`` dict and the
energy+reserve co-optimization update inline, near-verbatim duplicates
(orchestrator-unification plan §3.4). Stage 2 hoists both blocks here:

- :func:`build_base_dispatch_kwargs` — the base dict from a
  :class:`~market_sim.pipeline.spec.DispatchSpec`, plus the (identical in both
  orchestrators) priced-import-node monthly reconciliation band.
- :func:`apply_reserve_coopt` — the thin wrapper over
  ``reserve_config.get_reserve_design`` / ``build_reserve_dispatch_kwargs``
  that both orchestrators now call. The per-ISO reserve *designs* stay in
  ``config/reserve_config.py`` (the module both paths already shared); this
  wrapper owns only the gate, the driver threading, the merge, and the logging.

Byte-identity notes (the Stage-2 acceptance contract, plan §7.2):

- The emitted key set is exactly each orchestrator's pre-refactor key set —
  ``DispatchSpec`` fields left at ``UNSET`` are omitted, reserve keys are merged
  through :meth:`~market_sim.pipeline.spec.ReserveSpec.merge_into`, which
  preserves ``build_reserve_dispatch_kwargs``'s conditional key set.
- The backcast's hand-built PJM zone-aggregate block collapses onto
  ``reserve_config._pjm_design``: verified value-identical — the requirement
  (``req + outer_offset``), penalties, and widths (only the last width depends
  on the requirement scalar, and ``_pjm_design`` overwrites it to ``max(req)``,
  the same value the inline block sized it to), the eligibility mask, the
  deliverable supply cap, and the online gate all reproduce the inline arrays.
- The backcast's post-design ``ercot_rtolcap_supply_cap_mw`` overwrite is
  retired: after the Stage-2 A5 fold, ``_ercot_design`` (single-product) and
  ``_ercot_multiproduct_design`` both set ``supply_cap`` inside the design, and
  in backcast mode the function returns the measured RTOLCAP parquet regardless
  of the threaded forward drivers — the identical array the overwrite produced.
- ``sim_year`` is now threaded from both orchestrators. In backcast the solve
  year equals ``config.weather_year`` (the weather-year pin), and every
  ``sim_year`` consumer falls back to ``config.weather_year`` when ``None`` —
  so threading it is value-identical for the backcast and keeps the forecast's
  evolving-year semantics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

import numpy as np

from market_sim.pipeline.spec import DispatchSpec, ReserveSpec

if TYPE_CHECKING:
    from market_sim.config.reserve_config import ReserveDesign
    from market_sim.data.fleet import FleetArrays

logger = logging.getLogger(__name__)


def build_base_dispatch_kwargs(
    spec: DispatchSpec,
    *,
    import_node_recon: Optional[tuple] = None,
) -> dict:
    """Build the base ``dispatch_kwargs`` dict for the per-year LP.

    ``spec`` carries the final assembled values (see :class:`DispatchSpec`);
    this returns them key-for-key, then applies the priced import-node monthly
    net-interchange band when one was built (NYISO reconciliation — measured
    EIA-930 schedule in backcast, the neighbor's forecast net position in
    forecast). The band is part of the LP feasible region (same for P0/P1), so
    it warm-starts cleanly; no keys (identical LP) unless ``import_node_recon``
    is provided.

    Args:
        spec: The typed base-kwargs bundle.
        import_node_recon: Optional ``(node_gen_idx, monthly_lo, monthly_hi)``
            from ``transmission.build_import_node_reconciliation``.

    Returns:
        The ``dispatch_kwargs`` dict, ready for the gated per-orchestrator
        updates (ramp envelopes, local-capacity rows, mass caps) and
        :func:`apply_reserve_coopt`.
    """
    dispatch_kwargs = spec.to_dispatch_kwargs()
    if import_node_recon is not None:
        node_idx, recon_lo, recon_hi = import_node_recon
        dispatch_kwargs.update(
            import_node_gen_idx=node_idx,
            import_node_monthly_lo=recon_lo,
            import_node_monthly_hi=recon_hi,
        )
    return dispatch_kwargs


def apply_reserve_coopt(
    dispatch_kwargs: dict,
    config,
    fleet_arrays: "FleetArrays",
    hours: int,
    zone_names: list[str],
    *,
    system_load: Optional[np.ndarray] = None,
    wind_gen: Optional[np.ndarray] = None,
    solar_gen: Optional[np.ndarray] = None,
    sim_year: Optional[int] = None,
) -> Optional["ReserveDesign"]:
    """Merge the energy+reserve co-optimization kwargs into ``dispatch_kwargs``.

    The single reserve seam both orchestrators call (Stage 2). Gated on
    ``config.energy_reserve_coopt``. CAISO additionally requires the
    ``config.caiso_reserve_coopt`` flag (default off, issue #1492 / L-10): its
    ``reserve_config._caiso_design`` was previously a hard ``iso == "CAISO"``
    short-circuit here; the flag lifts that short-circuit so the default CAISO
    path stays byte-identical while a probe can enable the co-optimization.

    The ISO's reserve demand curve enters the LP as reserve balance rows so the
    reserve clearing price lifts the energy LMP endogenously. All per-ISO
    physics live in ``config/reserve_config.py`` (already shared by both
    orchestrators); this wrapper threads the forward drivers, merges the
    design's kwargs (preserving the conditional key set via
    :meth:`ReserveSpec.merge_into`), and logs the design.

    Args:
        dispatch_kwargs: The dict to update in place.
        config: ScenarioConfig (``config.iso`` selects the design).
        fleet_arrays: The vectorized fleet.
        hours: LP horizon (``config.hours``).
        zone_names: Zone names in ``zone_idx`` order.
        system_load: Optional system hourly load ``(T,)`` — forward-requirement
            / forward-supply-cap driver (ERCOT designs; ignored elsewhere).
        wind_gen: Optional system hourly wind potential ``(T,)`` (same role).
        solar_gen: Optional system hourly solar potential ``(T,)`` (same role).
        sim_year: The simulation year (forecast threads the evolving year;
            backcast the solve year, which equals ``config.weather_year``).

    Returns:
        The ``ReserveDesign`` merged in, or ``None`` when gated off.
    """
    iso = str(config.iso)
    if not getattr(config, "energy_reserve_coopt", False):
        return None
    # CAISO's reserve design (reserve_config._caiso_design) is gated behind its
    # own default-off flag (issue #1492): without it, keep the historical
    # short-circuit so the default CAISO path is byte-identical.
    if iso == "CAISO" and not getattr(config, "caiso_reserve_coopt", False):
        return None

    from market_sim.config.reserve_config import (
        build_reserve_dispatch_kwargs,
        get_reserve_design,
    )

    design = get_reserve_design(
        config,
        fleet_arrays,
        hours,
        zone_names,
        system_load=system_load,
        wind_gen=wind_gen,
        solar_gen=solar_gen,
        sim_year=sim_year,
    )
    coopt_kw = build_reserve_dispatch_kwargs(design)
    ReserveSpec.from_reserve_kwargs(coopt_kw).merge_into(dispatch_kwargs)
    _log_reserve_coopt(iso, config, fleet_arrays, design, coopt_kw)
    return design


def _log_reserve_coopt(
    iso: str,
    config,
    fleet_arrays: "FleetArrays",
    design: "ReserveDesign",
    coopt_kw: dict,
) -> None:
    """Log the merged reserve design (consolidates both orchestrators' lines)."""
    pen = coopt_kw.get("ordc_penalties", np.zeros(0))
    req = np.atleast_2d(coopt_kw.get("reserve_requirement", np.zeros((1, 1))))
    elig2d = np.atleast_2d(coopt_kw.get("reserve_eligible", np.zeros((1, 1))))
    if iso == "ERCOT" and getattr(config, "ercot_multiproduct_as_coopt", False):
        from market_sim.config.reserve_config import ERCOT_AS_PRODUCTS

        n_prod = len(ERCOT_AS_PRODUCTS)
        logger.info(
            "energy+reserve co-opt (ERCOT MULTI-PRODUCT): %d AS products %s, "
            "per-product req means %s MW, %d steps total, %d headroom tiers",
            n_prod,
            [p[0] for p in ERCOT_AS_PRODUCTS],
            [int(req[p].mean()) for p in range(min(n_prod, req.shape[0]))],
            len(pen),
            int(coopt_kw["reserve_headroom_products"].shape[0]),
        )
    elif iso == "ERCOT":
        logger.info(
            "energy+reserve co-opt (ERCOT): VOLL-anchored ORDC demand, "
            "req top %.0f MW, %d steps ($%.0f-$%.0f), %d reserve-eligible units",
            float(req[0, 0]),
            len(pen),
            float(pen.min()) if len(pen) else 0.0,
            float(pen.max()) if len(pen) else 0.0,
            int(elig2d[0].sum()),
        )
    elif iso in ("NYISO", "NEISO"):
        mask = coopt_kw.get("reserve_balance_zone_mask")
        rclass = np.asarray(coopt_kw.get("reserve_balance_class", np.zeros(0)))
        logger.info(
            "energy+reserve co-opt (%s): %d %s reserve families "
            "(%d 10-min/quick-start), %d ORDC steps ($%.0f-$%.0f), "
            "%d full-fleet / %d quick-start reserve-eligible units",
            iso,
            mask.shape[0] if mask is not None else 1,
            "locational" if iso == "NYISO" else "system",
            int((rclass == 1).sum()),
            len(pen),
            float(pen.min()) if len(pen) else 0.0,
            float(pen.max()) if len(pen) else 0.0,
            int(elig2d[0].sum()),
            int(elig2d[1].sum()) if elig2d.shape[0] > 1 else 0,
        )
        if iso == "NYISO" and design.online_gated is not None:
            logger.info(
                "  NYISO synchronised reserve ON: online-gated spinning class "
                "(rho=%.2f), %d gated reserve family/ies",
                float(design.online_rho),
                int((rclass == 2).sum()),
            )
    elif iso == "MISO":
        _measured = bool(getattr(config, "miso_measured_reserve_requirements", False))
        logger.info(
            "energy+reserve co-opt (MISO): RBDC market-wide requirement "
            "%.0f MW at h0 (%s), %d ORDC steps ($%.0f-$%.0f), "
            "%d reserve-eligible units",
            float(req[0, 0]),
            (
                "measured hourly cleared reg+spin+supp"
                if _measured
                else "MSSC + regulating, flat"
            ),
            len(pen),
            float(pen.min()) if len(pen) else 0.0,
            float(pen.max()) if len(pen) else 0.0,
            int(elig2d[0].sum()),
        )
        for fam in design.families[1:]:
            logger.info(
                "  MISO zonal reserve family %s: requirement %.0f MW at h0 "
                "(%s), published zonal curve steps %s",
                fam.name,
                float(fam.requirement[0]),
                (
                    (
                        "measured hourly Midwest reservation"
                        if "midwest" in fam.name
                        else "measured hourly South reservation"
                    )
                    if _measured
                    else "within-zone MSSC, flat"
                ),
                [
                    f"{w:.0f}MW@${p:.0f}"
                    for w, p in zip(fam.ordc_step_widths, fam.ordc_penalties)
                ],
            )
        if design.pergen_gen_idx is not None:
            _r10 = np.atleast_2d(design.pergen_ramp10)
            logger.info(
                "  MISO PER-ASSET reserve columns (miso_reserve_pergen): "
                "%d members pooled into %d (zone, fuel-class) R columns, "
                "availability-scaled 10-min deliverable ramp cap "
                "mean %.0f / min %.0f MW",
                int(design.pergen_gen_idx.size),
                _r10.shape[0],
                float(_r10.sum(axis=0).mean()),
                float(_r10.sum(axis=0).min()),
            )
        if design.posture_pools is not None and design.posture_pools.size:
            logger.info(
                "  MISO COMMITMENT POSTURE (miso_commitment_posture): "
                "%d of %d pools postured (fast-start exempt by physics), "
                "mlf %.2f-%.2f (cap-wt CEMS committed_pct), "
                "startup $%.0f-$%.0f/MW (NREL class tables)",
                int(design.posture_pools.size),
                int(np.atleast_2d(design.pergen_ramp10).shape[0]),
                float(design.posture_mlf.min()),
                float(design.posture_mlf.max()),
                float(design.posture_startup.min()),
                float(design.posture_startup.max()),
            )
    elif iso == "PJM":
        logger.info(
            "energy+reserve co-opt (PJM): req mean %.0f MW, %d ORDC steps, "
            "%d reserve-eligible units",
            float(req.mean()),
            len(pen),
            int(elig2d[0].sum()),
        )
        if design.pergen_gen_idx is not None:
            _r10 = np.atleast_2d(design.pergen_ramp10)
            logger.info(
                "PJM PER-GEN reserve co-opt ON: %d R columns / %d member units "
                "(eligible, ramp10>0; deliverable ramp mean %.1f GW), "
                "%d balance families (%s), req means %s MW%s",
                _r10.shape[0],
                int(design.pergen_gen_idx.size),
                float(_r10.sum(axis=0).mean()) / 1e3,
                len(design.families),
                ", ".join(f.name for f in design.families),
                [int(f.requirement.mean()) for f in design.families],
                (
                    " — SYNC product split ON (pjm_reserve_pergen_sync: "
                    "online-scoped sync caps recomputed at the P0->P1 seam)"
                    if design.pergen_col_pool is not None
                    else ""
                ),
            )
        if design.posture_pools is not None and design.posture_pools.size:
            logger.info(
                "  PJM COMMITMENT POSTURE (pjm_commitment_posture): "
                "%d of %d pools postured (fast-start exempt by physics), "
                "mlf %.2f-%.2f (cap-wt CEMS committed_pct), "
                "startup $%.0f-$%.0f/MW (NREL class tables)",
                int(design.posture_pools.size),
                int(np.atleast_2d(design.pergen_ramp10).shape[0]),
                float(design.posture_mlf.min()),
                float(design.posture_mlf.max()),
                float(design.posture_startup.min()),
                float(design.posture_startup.max()),
            )
        if design.online_gated is not None:
            logger.info("PJM reserve online-gating ON: ρ=%.2f", design.online_rho)
    elif iso == "CAISO":
        logger.info(
            "energy+reserve co-opt (CAISO, caiso_reserve_coopt): %d families "
            "(%s), req means %s MW, %d ORDC steps ($%.0f-$%.0f, §27.1.2.3.5 "
            "scarcity curves), %d reserve-eligible units",
            len(design.families),
            ", ".join(f.name for f in design.families),
            [int(f.requirement.mean()) for f in design.families],
            len(pen),
            float(pen.min()) if len(pen) else 0.0,
            float(pen.max()) if len(pen) else 0.0,
            int(elig2d[0].sum()),
        )
        if design.pergen_gen_idx is not None:
            _r10 = np.atleast_2d(design.pergen_ramp10)
            logger.info(
                "  CAISO PER-ASSET reserve columns: %d members pooled into %d "
                "(zone, fuel-class) R columns, availability-scaled 10-min "
                "deliverable ramp cap Σ %.1f GW",
                int(design.pergen_gen_idx.size),
                _r10.shape[0],
                float(_r10.sum(axis=0).mean()) / 1e3,
            )
    # Supply cap (ERCOT RTOLCAP / PJM deliverable ramp), any ISO whose design
    # set one — supersedes the per-orchestrator supply-cap log lines.
    if design.supply_cap is not None and design.pergen_gen_idx is None:
        cap = np.atleast_2d(design.supply_cap)
        logger.info(
            "%s reserve-supply cap ON: %d headroom row(s), mean cap MW %s",
            iso,
            cap.shape[0],
            [int(cap[r].mean()) for r in range(cap.shape[0])],
        )


def apply_ercot_commitment_posture(
    dispatch_kwargs: dict,
    config,
    fleet_arrays: "FleetArrays",
) -> bool:
    """Merge the ERCOT standalone energy-only commitment-posture kwargs.

    Gated on ``config.ercot_commitment_posture`` (ERCOT-only). Unlike the
    MISO/CAISO/PJM posture — which rides the pergen RESERVE pool and enters via
    :func:`apply_reserve_coopt` — the ERCOT posture is reserve-decoupled (ERCOT
    has no pergen substrate), so its ``posture_gen_idx``/``posture_col``/
    ``posture_mlf``/``posture_startup`` are threaded as their own dispatch
    kwargs (design note §A; ``docs/handoffs/ercot-commitment-thinness-2026-07.md``).
    Returns True when the posture was merged (a no-op otherwise, byte-identical).
    """
    if str(getattr(config, "iso", "")) != "ERCOT":
        return False
    if not getattr(config, "ercot_commitment_posture", False):
        return False
    from market_sim.config.reserve_config import ercot_commitment_posture_spec

    spec = ercot_commitment_posture_spec(config, fleet_arrays)
    if spec is None:
        logger.info(
            "ERCOT COMMITMENT POSTURE (ercot_commitment_posture): ON but no "
            "postured pools (all merchant-gas pools fast-start-exempt) — no-op"
        )
        return False
    gen_idx, col, mlf, startup = spec
    dispatch_kwargs.update(
        posture_gen_idx=gen_idx,
        posture_col=col,
        posture_mlf=mlf,
        posture_startup=startup,
    )
    q = int(mlf.size)
    logger.info(
        "ERCOT COMMITMENT POSTURE (ercot_commitment_posture): %d postured "
        "(zone, gas-class) pool(s) over %d merchant-gas members (fast-start CT "
        "exempt by physics, rule 18), mlf %.3f-%.3f (measured LSL/HSL p50), "
        "startup $%.0f-$%.0f/MW (NREL class tables) — energy-only, reserve "
        "design untouched (rule 19)",
        q,
        int(gen_idx.size),
        float(mlf.min()),
        float(mlf.max()),
        float(startup.min()),
        float(startup.max()),
    )
    return True


__all__ = [
    "build_base_dispatch_kwargs",
    "apply_reserve_coopt",
    "apply_ercot_commitment_posture",
]

"""Measured offer-surface markups/markdowns (conditional, midcurve, cleared-share, fast-start, lowcurve).

Split out of ``data/fleet.py`` (11,199 ln) into the ``data/fleet`` package
(refactor-consolidation plan §5 item 8, 2026-07-23) as pure code motion:
every moved body is byte-identical; only this header and the census'd
``_pkg_ns()`` call-site routings are new. The package ``__init__`` re-exports
the full pre-split surface; patch semantics are preserved via
:func:`market_sim.data.fleet.models._pkg_ns`.
"""

from __future__ import annotations

from typing import NamedTuple

import json
import logging
import numpy as np
import pandas as pd

from functools import lru_cache
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.offer_curves import CONDITIONAL_SURFACE_GROUPS
from pathlib import Path
from market_sim.data.fleet.models import FleetArrays, Generator

# Pre-split logger name: records keep the historical module path.
logger = logging.getLogger("market_sim.data.fleet")


@lru_cache(maxsize=1)
def _load_ct_offer_surface() -> tuple[tuple[float, float, float], ...]:
    """Load the frozen measured CT/peaker offer-surface regimes.

    Reads ``data/raw/_validation-source/ercot_ct_offer_surface.json`` (produced by
    ``scripts/data/derive_ct_offer_surface.py`` from the 60-Day DAM disclosure) and
    returns its regimes as ``(q_lo, q_hi, offer_level)`` triples. Cached — the
    surface is frozen against residuals (rule 20); a re-derive is a data-update
    commit, not a solve-time knob.
    """
    from market_sim.config import paths

    path = paths.CALIBRATION_DIR / "ercot_ct_offer_surface.json"
    payload = json.loads(path.read_text())
    return tuple(
        (float(lo), float(hi), float(level)) for lo, hi, level in payload["regimes"]
    )


def apply_ercot_ct_offer_surface(
    mc_base: np.ndarray,
    generators: list[Generator],
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> bool:
    """Raise ERCOT CT/peaker econ+peak offers to the measured self-withholding level.

    The G-22 condition-responsive offer surface (filed structural conclusion #1
    of ``docs/FINDING-ercot-priceshape-2026-07.md`` §6; design note
    ``docs/handoffs/ercot-g22-offer-surface-2026-07.md``). In the missed tail
    hours the P1 LP offers every online CT/peaker economic+peak tranche at its
    flat marginal cost ``heat_rate x gas + VOM`` (~$50-150/MWh) — the "phantom
    sub-$200 spare" that caps the energy dual below the scarcity level the real
    market cleared. The real fleet's peakers had already offered themselves to
    the ERCOT cap band (~$1,500/MWh) by those hours: the 60-Day DAM disclosure
    shows the CT/peaker offer at 90% of HSL is cap-band, not heat-rate x gas
    (``scripts/data/derive_ct_offer_surface.py``).

    This posts the **measured** self-withholding offer level on the CT/peaker
    ``econ*``/``peak*`` tranches (the phantom-spare bands; the ``mustrun``/
    ``sync``/``committed`` min-gen scaffolding is untouched), keyed on a
    **net-load percentile** driver. The low regime is inert (level 0), so the LP
    applies ``max(mc, 0) = mc`` and every sub-hinge hour is byte-identical; only
    above the measured hinge — the net-load percentile at which even the peaker
    fleet's lower quartile has crossed to cap-band — is the offer raised. Unlike
    the REJECTED ercot33 static wall this is condition-responsive (inert in the
    ~90% of hours below the hinge, so no broad elevation) and touches only the
    CT/peaker class (no CC/ST peak-band repricing, the channel that moved measured
    volumes through the P0->P1 startup-amortization coupling). Both the trigger
    (net-load) and the level (measured offer) are forward-derivable and respond to
    changed conditions, so the mechanism is admissible in backcast and forecast
    (CLAUDE.md #10/#13); every parameter is measured and frozen (rules 20/26).

    Vectorised (no hour loop, rule 2). Modifies ``mc_base`` in place. Returns
    ``True`` when the surface was applied, ``False`` (byte-identical) when the
    flag is off, the ISO is not ERCOT, or the fleet has no CT/peaker econ/peak
    tranches.

    Args:
        mc_base: The P1 bid-cost matrix ``(n_gen, T)``, mutated in place.
        generators: The dispatch fleet, aligned row-for-row with ``mc_base``.
        net_load_mw: System net-load per hour (``load - wind - solar``), shape
            ``(T,)`` — the same LP-served convention the drag floors use.
        config: Scenario config supplying the enable flag and ISO.
    """
    if not getattr(config, "ercot_ct_offer_surface", False):
        return False
    if config.iso != "ERCOT":
        return False
    # The phantom-spare bands: CT_PEAKER economic (``econ``/``econc00``..) and
    # peak (``peak``/``peak2``..) tranches. The min-gen scaffolding
    # (``mustrun``/``sync``/``committed``) is commitment structure, never repriced.
    rows = [
        g
        for g, gen in enumerate(generators)
        if gen.plant_group == "CT_PEAKER"
        and (
            gen.unit_id.rpartition("_")[2].startswith("econ")
            or gen.unit_id.rpartition("_")[2].startswith("peak")
        )
    ]
    if not rows:
        return False

    regimes = _load_ct_offer_surface()
    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    # Per-hour measured offer level from the net-load-percentile regimes. A
    # percentile hinge maps to a net-load quantile threshold on this year's own
    # net-load distribution (forward-native: the same construction regenerates
    # from a forecast load+VRE net-load), so the surface tracks the year's
    # scarcity structure rather than an absolute MW line.
    level_series = np.zeros(hours)
    for q_lo, q_hi, level in regimes:
        if level <= 0.0:
            continue
        lo_mw = np.quantile(net_load, q_lo)
        if q_hi >= 1.0:
            mask = net_load >= lo_mw
        else:
            mask = (net_load >= lo_mw) & (net_load < np.quantile(net_load, q_hi))
        level_series[mask] = level

    row_idx = np.asarray(rows)
    mc_base[row_idx, :] = np.maximum(mc_base[row_idx, :], level_series[np.newaxis, :])
    hinge = min((lo for lo, _hi, lv in regimes if lv > 0.0), default=1.0)
    logger.info(
        "ERCOT CT/peaker offer surface applied: %d econ/peak tranche rows raised "
        "to the measured self-withholding level above the %.0fth net-load "
        "percentile (%d/%d hours)",
        len(rows),
        hinge * 100.0,
        int((level_series > 0.0).sum()),
        hours,
    )
    return True


@lru_cache(maxsize=4)
def _load_condbinned_surface(path: str) -> dict:
    """Load and cache the measured condition-binned offer surface JSON.

    Frozen against residuals (rule 20); a re-derive is a data-update commit
    (scripts/data/derive_dam_offer_hrmults.py --condition-binned), not a solve-time knob.
    """
    return json.loads(Path(path).read_text())


class _CondSurfaceSpec(NamedTuple):
    """Per-ISO wiring of the shared conditional-surface kernel.

    One row per ISO in :data:`_CONDITIONAL_SURFACE_SPECS`; every field is that
    ISO's own frozen wiring transplanted byte-for-byte from its pre-collapse
    wrapper (rules 23/25 — per-ISO values stay per-ISO, no generic merge):
    the enable flag / path / percentile-edges / min-bin / price-cap-fraction
    ScenarioConfig field names, the default surface JSON filename under
    ``CALIBRATION_DIR``, the priced class tuple, and the exact error wording
    of the edges-mismatch guard.
    """

    flag: str
    path_field: str
    default_filename: str
    pcts_field: str
    min_bin_field: str
    cap_frac_field: str
    groups: tuple[str, ...]
    err_name: str
    rederive_hint: str


#: Per-ISO conditional-surface wiring (see :class:`_CondSurfaceSpec`).
_CONDITIONAL_SURFACE_SPECS: dict[str, _CondSurfaceSpec] = {
    "ERCOT": _CondSurfaceSpec(
        flag="ercot_offer_surface_conditional",
        path_field="ercot_offer_surface_binned_path",
        default_filename="offer_curve_dam_hrmults_condbinned.json",
        pcts_field="ercot_offer_surface_netload_pcts",
        min_bin_field="ercot_offer_surface_min_bin",
        cap_frac_field="ercot_offer_surface_price_cap_frac",
        groups=CONDITIONAL_SURFACE_GROUPS,
        err_name="ercot_offer_surface",
        rederive_hint=(
            "re-derive with matching --condition-binned edges, or fix the config"
        ),
    ),
    "NEISO": _CondSurfaceSpec(
        flag="neiso_offer_surface_conditional",
        path_field="neiso_offer_surface_binned_path",
        default_filename="neiso_offer_surface_condbinned.json",
        pcts_field="neiso_offer_surface_netload_pcts",
        min_bin_field="neiso_offer_surface_min_bin",
        cap_frac_field="neiso_offer_surface_price_cap_frac",
        groups=("CT_PEAKER",),
        err_name="neiso_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_neiso_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
    "PJM": _CondSurfaceSpec(
        flag="pjm_offer_surface_conditional",
        path_field="pjm_offer_surface_binned_path",
        default_filename="pjm_offer_surface_condbinned.json",
        pcts_field="pjm_offer_surface_netload_pcts",
        min_bin_field="pjm_offer_surface_min_bin",
        cap_frac_field="pjm_offer_surface_price_cap_frac",
        groups=("CC_REGULAR", "CT_PEAKER"),
        err_name="pjm_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_pjm_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
    "CAISO": _CondSurfaceSpec(
        flag="caiso_offer_surface_conditional",
        path_field="caiso_offer_surface_binned_path",
        default_filename="caiso_offer_surface_condbinned.json",
        pcts_field="caiso_offer_surface_netload_pcts",
        min_bin_field="caiso_offer_surface_min_bin",
        cap_frac_field="caiso_offer_surface_price_cap_frac",
        groups=("CC_REGULAR", "CT_PEAKER"),
        err_name="caiso_offer_surface",
        rederive_hint=(
            "re-derive scripts/data/derive_caiso_offer_surface.py with matching "
            "--edges, or fix the config"
        ),
    ),
}


def build_offer_surface_conditional_markup(
    iso: str,
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build ``iso``'s conditional offer-surface markup from its spec-registry row.

    The single body behind the four per-ISO
    ``build_<iso>_offer_surface_conditional_markup`` aliases (fleet-package
    split sub-task (b)): gate on the spec's enable flag and the config ISO,
    resolve the frozen surface JSON (explicit path field, else the spec's
    default under ``CALIBRATION_DIR``), enforce the config-vs-derive
    percentile-edge agreement, and hand the spec's class tuple / min-bin /
    price-cap wiring to :func:`_conditional_surface_markup`. Behavior is the
    pre-collapse wrappers' byte-for-byte; see each alias's docstring for the
    ISO-specific provenance and mechanism history.
    """
    spec = _CONDITIONAL_SURFACE_SPECS[iso]
    if not getattr(config, spec.flag, False):
        return None
    if config.iso != iso:
        return None
    path = getattr(config, spec.path_field, None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / spec.default_filename
        if not default.exists():
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))

    edges = tuple(float(x) for x in getattr(config, spec.pcts_field))
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            f"{spec.err_name}: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            f"({spec.rederive_hint})."
        )
    return _conditional_surface_markup(
        fleet_arrays,
        generators,
        fuel_prices,
        net_load_mw,
        config,
        surface=surface,
        edges=edges,
        groups=spec.groups,
        min_bin=int(getattr(config, spec.min_bin_field, 0) or 0),
        price_cap=float(getattr(config, spec.cap_frac_field, 0.95))
        * float(getattr(config, "voll", 5000.0)),
        label=iso,
    )


def build_ercot_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the P1-only condition-responsive gas peak-band offer markup ``(n_gen, T)``.

    The ERCOT G-22 §8 / ercot37-filed HETEROGENEITY-PRESERVING offer surface
    (ScenarioConfig.ercot_offer_surface_conditional). Returns an additive markup on
    the P1 bid MC that reprices ONLY the gas peak-band rungs (CC/CT/ST — split
    equal-capacity at the resolved peak height by the backcast-config no-op) and ONLY
    in anticipated-tight hours, so that the top of the offer stack prices like the
    measured QSE scarcity wall exactly there. Contrast the two rejected predecessors:

      * the flat ``ercot_ct_offer_surface`` posted one p50 level on EVERY CT
        econ/peak row above a hinge → collapsed offer heterogeneity, removed ~3.2 GW
        of spare in one step, overshot (calibration-log 2026-07-06);
      * the STATIC ``peak_ladder`` wall posted the measured ladder in ALL 8760 hours
        → perturbed P0 run lengths and swapped ~8 TWh CT<->ST through the startup-
        amortization coupling (docs/FINDING-ercot-priceshape-2026-07.md §6).

    This mechanism fixes both: it is applied to the P1 clearing objective ONLY (P0 is
    byte-identical → no CT<->ST coupling), the loose bins never lower an offer (ratio
    clamped >= 1 → loose hours byte-identical), and within a tight hour the lower
    rungs stay at the resolved peak while only the upper rungs (p70/p90) reach the
    cap band (heterogeneity preserved). Both the trigger (net-load percentile,
    forward-native) and the level (measured QSE offer quantiles) are rule-13
    admissible; parameters are measured (rule 21) and frozen (rule 20).

    For each priced gas class, the peak-rung row ``g`` (rung index ``r``) in hour
    ``t`` (net-load bin ``b``) is repriced from its baked height (the resolved
    ``peak`` multiplier the fleet built the rung at) to the measured bin/rung
    multiplier::

        ratio       = max(1.0, binned_ladder[cls][b][r] / resolved_peak[cls])
        energy      = heat_rate[g] * fuel_prices[g, t]          # the row's fuel MC
        ratio_cap   = min(ratio, price_cap / energy)            # keep offer < VOLL
        markup[g,t] = energy * (ratio_cap - 1.0)                # additive, >= 0

    Vectorised over hours (rule 2). Returns ``None`` (P1 unchanged) when the flag is
    off, the ISO is not ERCOT, the surface path is unset/empty, or the fleet carries
    no priced gas peak rungs.

    Args:
        fleet_arrays: The vectorized fleet (``heat_rate`` supplies each rung's base).
        generators: The dispatch fleet, aligned row-for-row with ``fleet_arrays``.
        fuel_prices: The ``(n_gen, T)`` delivered fuel price (same array assemble_mc
            used), so the repriced offer scales with the hour's fuel like every other
            band.
        net_load_mw: System net-load per hour (``load - wind - solar``), shape
            ``(T,)`` — the same LP-served convention the drag floors / CT surface use.
        config: Scenario config supplying the enable flag, ISO, surface path, bin
            edges and price cap.
    """
    return build_offer_surface_conditional_markup(
        "ERCOT", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_neiso_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the NEISO P1-only fast-start offer-surface markup ``(n_gen, T)``.

    The ISO-NE analogue of :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.neiso_offer_surface_conditional`` — winter scarcity
    charter Limb B): the measured fast-start offer distribution from ISO-NE's
    public DA Energy Market historical offer data
    (``scripts/data/derive_neiso_offer_surface.py``), condition-binned by
    within-year net-load percentile, posted onto the CT_PEAKER peak-band rungs
    in the P1 clearing objective only. Same mechanics, clamps and rule-13/20/21
    discipline as the ERCOT surface (the shared
    :func:`_conditional_surface_markup` core); NEISO-only, its own frozen
    surface JSON, no cross-ISO fallback (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "NEISO", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_pjm_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the PJM P1-only energy-offer-surface markup ``(n_gen, T)``.

    The PJM analogue of :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.pjm_offer_surface_conditional`` — G-22 lever A): the
    measured top-of-curve offer distribution from PJM's public DataMiner2
    ``energy_market_offers`` feed (``scripts/data/derive_pjm_offer_surface.py``),
    condition-binned by within-year net-load percentile, posted onto the
    CC_REGULAR + CT_PEAKER peak-band rungs in the P1 clearing objective only
    — the two classes whose idle supply is offered above the model price but
    below the actual DA price at the missed summer peaks
    (docs/handoffs/pjm-summer-peak-price-formation-g22-2026-07.md §1-2).
    Same mechanics, clamps and rule-13/20/21 discipline as the ERCOT/NEISO
    surfaces (the shared :func:`_conditional_surface_markup` core); PJM-only,
    its own frozen surface JSON, no cross-ISO fallback (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "PJM", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def build_caiso_offer_surface_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
) -> "np.ndarray | None":
    """Build the CAISO P1-only measured-offer-surface markup ``(n_gen, T)``.

    The CAISO analogue of :func:`build_pjm_offer_surface_conditional_markup`
    (``ScenarioConfig.caiso_offer_surface_conditional`` — the C1
    CC-over/CT-under lane's measured route, WP-A 2026-07-16): the measured
    top-of-curve bid distribution from CAISO's OASIS Public Bid Data
    (``scripts/data/derive_caiso_offer_surface.py``), condition-binned by
    within-year net-load percentile, posted onto the CC_REGULAR + CT_PEAKER
    peak-band rungs in the P1 clearing objective only. The derive nets the
    CARB allowance cost out of the measured tops at the resolved-peak heat
    rate, so the fuel-only repricing here round-trips the measured bid.
    Same mechanics, clamps and rule-13/23 discipline as the ERCOT/NEISO/PJM
    surfaces (the shared :func:`_conditional_surface_markup` core);
    CAISO-only, its own frozen surface JSON, no cross-ISO fallback
    (rule 25).
    """
    return build_offer_surface_conditional_markup(
        "CAISO", fleet_arrays, generators, fuel_prices, net_load_mw, config
    )


def _conditional_surface_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    *,
    surface: dict,
    edges: tuple[float, ...],
    groups: tuple[str, ...],
    min_bin: int,
    price_cap: float,
    label: str,
) -> "np.ndarray | None":
    """Shared condition-binned peak-rung repricing core (ERCOT/NEISO wrappers).

    Behavior is exactly the pre-refactor ERCOT body: peak-rung rows of the
    ``groups`` classes are repriced from their resolved peak height to the
    measured ``binned_ladder`` multiplier of the hour's net-load bin, clamped
    never to lower an offer (ratio >= 1) and never to reach ``price_cap``.
    """
    n_bins = len(edges) + 1

    # Peak-rung rows per priced gas class, tagged with their rung index (peak -> 0,
    # peakN -> N-1). The resolved peak height each rung was built at comes straight
    # from the class offer curve so the ratio recovers the measured multiplier.
    curves = getattr(config, "offer_curve_by_group", None) or {}
    class_rows: dict[str, list[tuple[int, int]]] = {}
    resolved_peak: dict[str, float] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or getattr(gen, "efficiency_bin", None)
        if cls not in groups or cls not in surface:
            continue
        sfx = gen.unit_id.rpartition("_")[2]
        if sfx == "peak":
            rung = 0
        elif sfx.startswith("peak") and sfx[4:].isdigit():
            rung = int(sfx[4:]) - 1
        else:
            continue
        class_rows.setdefault(cls, []).append((g, rung))
        resolved_peak.setdefault(cls, float(curves.get(cls, {}).get("peak", 0.0)))
    if not class_rows:
        return None

    hours = int(fuel_prices.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    # Per-hour tightness bin on the year's OWN net-load percentiles (forward-native:
    # the identical construction the derive used, so bin b at solve time is the same
    # scarcity state as bin b in the measurement).
    thresholds = np.quantile(net_load, edges) if len(edges) else np.array([])
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,), 0..n_bins-1
    # Optional floor: engage the wall only at/above min_bin (protect mild hours
    # from any residual peak-rung repricing). Below it the ratio is forced to 1
    # (byte-identical). 0 → the full measured distribution applies in every bin.
    heat_rate = fleet_arrays.heat_rate
    markup = np.zeros((len(generators), hours), dtype=float)
    n_priced = 0
    for cls, rows in class_rows.items():
        pk = resolved_peak.get(cls, 0.0)
        ladders = surface[cls].get("binned_ladder") or []
        if pk <= 0.0 or len(ladders) != n_bins:
            continue
        # ratio[bin, rung] = measured multiplier / resolved peak, clamped >= 1 so a
        # loose bin never lowers the offer below the keeper's peak height.
        n_rungs = max((r for _, r in rows), default=0) + 1
        ratio = np.ones((n_bins, n_rungs), dtype=float)
        for b in range(n_bins):
            if b < min_bin:
                continue  # mild bin: leave ratio at 1.0 (no repricing)
            lad = ladders[b] or []
            for r in range(n_rungs):
                if r < len(lad):
                    ratio[b, r] = max(1.0, float(lad[r][1]) / pk)
        for g, rung in rows:
            energy = heat_rate[g] * fuel_prices[g, :hours]  # (T,) fuel MC of the rung
            row_ratio = ratio[hour_bin, min(rung, n_rungs - 1)]  # (T,)
            # Cap the repriced offer below VOLL so the peak band never ties the load-
            # shed slack (which would let the LP dump load instead of clearing it).
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio_cap = np.where(energy > 0.0, price_cap / energy, row_ratio)
            eff = np.minimum(row_ratio, np.maximum(1.0, ratio_cap))
            markup[g, :] = energy * (eff - 1.0)
            n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "%s conditional offer surface: repriced %d gas peak-rung rows across "
        "%d net-load bins (tightest bin binds %d/%d hours); P1-only, loose hours "
        "byte-identical",
        label,
        n_priced,
        n_bins,
        tight,
        hours,
    )
    return markup


#: Model class -> measured physics segment of the PJM mid-curve surface
#: (scripts/data/derive_pjm_offer_midcurve.py). CHP classes are deliberately
#: absent (steam-host economics, small idle footprint).
_PJM_MIDCURVE_SEGMENT_OF = {
    "CC_REGULAR": "CC_LIKE",
    "CT_PEAKER": "CT_FAST",
    "COAL": "LONG_RUN",
    "COAL_BIT": "LONG_RUN",
    "COAL_PRB": "LONG_RUN",
    "ST_GAS": "LONG_RUN",
}


def build_pjm_offer_midcurve_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the PJM P1-only MID-CURVE offer-floor markup ``(n_gen, T)``.

    G-22 lever A' (``ScenarioConfig.pjm_offer_midcurve_conditional``): the
    pjm-99 probe proved the measured TOP-of-curve surface is inert in PJM —
    the dual is capped by the ~21 GW idle mid-curve (COAL / CT_PEAKER /
    ST_GAS / CC econ bands) offered at $28-45 where the measured fleet
    prices the same curve region $35-83+, and the depth sweep showed +10 GW
    of procurement depth buys only +$2-4/MWh on that too-cheap body. This
    mechanism floors each targeted econ-tranche row's P1 bid at the
    MEASURED capacity-share-matched offer level of its physics segment
    (``scripts/data/derive_pjm_offer_midcurve.py``):

        target[g, t] = mult(segment, year, bin(t), share_g) x gas_day(t)
        markup[g, t] = max(0, min(target, 0.95 x VOLL) - mc_base[g, t])

    * ``share_g`` is the row's WITHIN-PLANT cumulative-capacity midpoint
      (scale-free — immune to the model-fleet vs measured-segment capacity
      mismatch), read off the model's own tranche structure ordered by
      base cost.
    * Targeted rows: the econ tranches (``econ*`` suffixes) of the mapped
      classes, plus the LONG_RUN classes' ``peak`` tranche (CC/CT peak
      rungs stay owned by the pjm-99 top-of-curve surface — one mechanism
      per row, rule 19). Committed / must-run / sync tranches are never
      touched (their pricing is owned by the coal take-or-pay/passthrough
      sigmoids and the commitment scaffolding).
    * P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and the startup
      amortization coupling are unperturbed — the pjm-99 finding's explicit
      caution for econ-band repricing (the rejected ERCOT flat-CT
      precedent).
    * The floor only ever RAISES a bid to the measured level (max(0, .)),
      mirroring the top-of-curve surface's ratio >= 1 clamp, and is capped
      below VOLL so no tranche ties the load-shed slack.

    Measured OFFER prices are the input; clearing prices stay
    validation-only (rule 13); the surface JSON is frozen against
    residuals (rule 20). PJM-only, no cross-ISO fallback (rule 25).
    """
    if not getattr(config, "pjm_offer_midcurve_conditional", False):
        return None
    if config.iso != "PJM":
        return None
    path = getattr(config, "pjm_offer_midcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "pjm_offer_midcurve_condbinned.json")
    surface = json.loads(Path(path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    shares = np.asarray(prov.get("shares", ()), dtype=float)
    if not edges or shares.size == 0:
        raise ValueError(
            "pjm_offer_midcurve: surface JSON carries no edges/shares — "
            "re-derive scripts/data/derive_pjm_offer_midcurve.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + PJM basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["PJM"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Optional measured-segment scope (ScenarioConfig.pjm_offer_midcurve_segments):
    # None floors every mapped segment (pjm-101/102, byte-identical); a tuple
    # restricts the floor to those segments so another mechanism can own the
    # rest of the stack (rule 19 — e.g. ("LONG_RUN",) leaves the CT_FAST rows
    # to the fast-start startup amortization).
    seg_scope = getattr(config, "pjm_offer_midcurve_segments", None)
    scoped = (
        set(_PJM_MIDCURVE_SEGMENT_OF.values())
        if seg_scope is None
        else {str(s) for s in seg_scope}
    )

    # Per-segment (n_bins, n_shares) mult tables for this delivery year
    # (pooled fallback for an unmapped year, e.g. a forward year).
    tables: dict[str, np.ndarray] = {}
    for seg in set(_PJM_MIDCURVE_SEGMENT_OF.values()) & scoped:
        entry = surface.get(seg)
        if not entry:
            continue
        ladders = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        if not ladders or len(ladders) != n_bins:
            continue
        tables[seg] = np.array(
            [[float(pt[1]) for pt in lad] for lad in ladders], dtype=float
        )  # (n_bins, n_shares)

    # Target rows + within-plant shares. A plant key is the unit_id prefix
    # (everything before the tranche suffix); the share base is EVERY
    # tranche of the plant ordered by its annual-mean base cost, so the
    # model's own rising tranche curve defines each row's curve position.
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in _PJM_MIDCURVE_SEGMENT_OF:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = 0.95 * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            seg = _PJM_MIDCURVE_SEGMENT_OF[row_cls[g]]
            is_target = sfx.startswith("econ") or (sfx == "peak" and seg == "LONG_RUN")
            if not is_target or seg not in tables:
                continue
            # mult per bin at this row's share (linear interp on the grid).
            table = tables[seg]  # (n_bins, n_shares)
            mult_b = np.array(
                [
                    np.interp(s_g, shares, table[b])
                    if np.isfinite(table[b]).all()
                    else np.nan
                    for b in range(n_bins)
                ]
            )
            target = mult_b[hour_bin] * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, np.nan_to_num(target, nan=0.0) - mc_base[g, :])
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "PJM mid-curve offer surface: floored %d econ/long-run tranche rows "
        "at the measured capacity-share offer level (%d net-load bins, "
        "tightest bin %d/%d hours, year table %s); P1-only",
        n_priced,
        n_bins,
        tight,
        hours,
        str(year)
        if any(str(year) in (surface.get(s, {}).get("years", {})) for s in tables)
        else "pooled",
    )
    return markup


#: Model plant_group -> measured class key of the ERCOT mid-curve surface
#: (scripts/data/derive_ercot_offer_midcurve.py). CC_CHP shares the CC measured
#: offers (CHP is a plant attribute, not a DAM Resource Type). ST_GAS is
#: absent — the drag-floor structure owns it (rule 19).
_ERCOT_MIDCURVE_CLASS_OF = {
    "CC_REGULAR": "CC",
    "CC_CHP": "CC",
    "CT_PEAKER": "CT_PEAKER",
}


def build_ercot_offer_midcurve_conditional_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the ERCOT P1-only MID-CURVE offer-floor markup ``(n_gen, T)``.

    G-22 lever A' (``ScenarioConfig.ercot_offer_surface_midcurve_conditional``),
    the ERCOT analogue of ``build_pjm_offer_midcurve_conditional_markup``. The
    existing ``ercot_offer_surface_conditional`` reprices only the gas PEAK rungs
    (top ~263 h/yr); this floors each targeted gas ``econ*`` tranche's P1 bid at
    the MEASURED capacity-share-matched day-ahead offer level of its class
    (``scripts/data/derive_ercot_offer_midcurve.py`` — the 60-Day DAM disclosure
    body, 18-22x at within-unit shares 0.95-0.99):

        target[g, t] = mult(class, year, bin(t), share_g) x gas_day(t)
        markup[g, t] = max(0, min(target, 0.95 x VOLL) - mc_base[g, t])

    * ``share_g`` is the row's WITHIN-PLANT cumulative-capacity midpoint
      (scale-free — immune to the model-fleet vs measured-fleet capacity
      mismatch), read off the model's own CAMPD tranche structure ordered by
      base cost, exactly as the PJM mid-curve does.
    * Targeted rows: the gas econ tranches (``econ*`` suffixes) of the mapped
      classes (CC_REGULAR/CC_CHP -> CC, CT_PEAKER). The gas PEAK rungs stay
      owned by ``ercot_offer_surface_conditional`` (one mechanism per row, rule
      19); ST_GAS is excluded (the drag-floor owns it). The floor only ever
      RAISES a bid to the measured level (max(0, .)) and is capped below VOLL.
    * P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and the startup
      amortization coupling are byte-identical.

    Measured OFFER prices are the input; clearing prices stay validation-only
    (rule 13); the surface JSON is frozen against residuals (rule 23).
    ERCOT-only, no cross-ISO fallback (rule 25).
    """
    if not getattr(config, "ercot_offer_surface_midcurve_conditional", False):
        return None
    if config.iso != "ERCOT":
        return None
    path = getattr(config, "ercot_offer_surface_midcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "ercot_offer_midcurve_condbinned.json")
    surface = json.loads(Path(path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    shares = np.asarray(prov.get("shares", ()), dtype=float)
    if not edges or shares.size == 0:
        raise ValueError(
            "ercot_offer_midcurve: surface JSON carries no edges/shares — "
            "re-derive scripts/data/derive_ercot_offer_midcurve.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + ERCOT basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Per-class (n_bins, n_shares) mult tables for this delivery year (pooled
    # fallback for an unmapped/forward year).
    tables: dict[str, np.ndarray] = {}
    for cls_key in set(_ERCOT_MIDCURVE_CLASS_OF.values()):
        entry = surface.get(cls_key)
        if not entry:
            continue
        ladders = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        if not ladders or len(ladders) != n_bins:
            continue
        tables[cls_key] = np.array(
            [[float(pt[1]) for pt in lad] for lad in ladders], dtype=float
        )  # (n_bins, n_shares)

    # Target rows + within-plant shares. A plant key is the unit_id prefix
    # (everything before the tranche suffix); the share base is EVERY tranche
    # of the plant ordered by its annual-mean base cost, so the model's own
    # rising CAMPD tranche curve defines each row's curve position.
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in _ERCOT_MIDCURVE_CLASS_OF:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = 0.95 * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            if not sfx.startswith("econ"):
                continue
            cls_key = _ERCOT_MIDCURVE_CLASS_OF[row_cls[g]]
            if cls_key not in tables:
                continue
            table = tables[cls_key]  # (n_bins, n_shares)
            mult_b = np.array(
                [
                    np.interp(s_g, shares, table[b])
                    if np.isfinite(table[b]).all()
                    else np.nan
                    for b in range(n_bins)
                ]
            )
            target = mult_b[hour_bin] * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, np.nan_to_num(target, nan=0.0) - mc_base[g, :])
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        logger.info(
            "ERCOT mid-curve offer surface: no econ row floored (measured "
            "offers <= model econ bids at every share/bin) — byte-identical"
        )
        return None
    tight = int((hour_bin >= n_bins - 1).sum())
    logger.info(
        "ERCOT mid-curve offer surface: floored %d gas econ tranche rows at "
        "the measured capacity-share offer level (%d net-load bins, tightest "
        "bin %d/%d hours, year table %s); P1-only",
        n_priced,
        n_bins,
        tight,
        hours,
        str(year)
        if any(str(year) in (surface.get(c, {}).get("years", {})) for c in tables)
        else "pooled",
    )
    return markup


#: Model plant_group -> measured class key of the ERCOT DAM cleared-share
#: boundary artifact (scripts/data/derive_ercot_dam_cleared_share.py). Deliberately
#: NARROWER than the mid-curve map: CC_CHP is excluded (steam-host cogens
#: self-schedule — the ERCOT-70/71 decomposition measures the model's CC_CHP
#: within +12 MW of actual on the target windows, so there is no composition
#: error to price there), ST_GAS is owned by the drag structure (rule 19).
_ERCOT_CLEARED_SHARE_CLASS_OF = {
    "CC_REGULAR": "CC",
    "CT_PEAKER": "CT",
}

# ERCOT-77 steam extension (ercot_offer_surface_cleared_share_steam): the
# legacy gas-steam class joins the wall's scope, priced from the artifact's
# "ST" block (GSREH/GSNONR/GSSUP — the ERCOT-73 leg-c participation cliff).
_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF = {"ST_GAS": "ST"}


def build_ercot_offer_surface_cleared_share_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "np.ndarray | None":
    """Build the ERCOT P1-only DAM CLEARED-SHARE boundary markup ``(n_gen, T)``.

    The ERCOT-72 covered-CC / CT composition mechanism
    (``ScenarioConfig.ercot_offer_surface_cleared_share``). ERCOT has no DAM
    must-offer; the 60-Day disclosure measures that on moderate days only
    ~0.49-0.64 of CC live capability (CT: 0.03-0.47) clears the DAM for energy
    — the remainder is not in the day-ahead supply at any price, while the
    model's econ tranches span ~92% of every plant at the econ multipliers.
    This floors each merchant gas ``econ*`` tranche row whose WITHIN-PLANT
    cumulative-capacity midpoint ``share_g`` exceeds the hour's net-load bin's
    MEASURED cleared share at the bin's MEASURED above-boundary offer wall::

        rel          = (share_g - boundary(bin)) / (1 - boundary(bin))
        target[g, t] = interp(rel, ladder_q, ladder_mult(bin)) x gas_day(t)
        markup[g, t] = max(0, min(target, cap_frac x VOLL) - mc_base[g, t])

    * ``boundary`` (cleared share of live capability) and the wall ladder
      (MW-weighted quantiles of offered-but-uncleared curve-segment prices as
      effective-HR multipliers) are both measured per net-load-percentile bin
      (condition-responsive: measured CC boundary 0.33 loose -> 0.64 tight),
      never day-pinned; zero fitted scalars (rules 13/14/26).
    * Targeted rows: ``econ*`` tranches of CC_REGULAR / CT_PEAKER only. The
      PEAK rungs stay owned by ``ercot_offer_surface_conditional``, the
      committed/mustrun blocks by the bridge/floor structure, ST_GAS by the
      drag, CC_CHP is measured composition-clean (rule 19). Mutually exclusive
      with ``ercot_offer_surface_midcurve_conditional`` (same econ rows — one
      owner per row): arming both is a hard error.
    * The floor only ever RAISES a bid (``max(0, .)``) and is capped below
      VOLL; rows at/below the boundary and bins with no measured data are
      byte-identical. P1-only (the ``mc_bid_adjust`` seam): P0 run lengths and
      the startup-amortization coupling are untouched.
    * ``ercot_offer_surface_cleared_share_state`` (ERCOT-73, default off)
      multiplies each walled row-hour's markup by the MEASURED
      commitment-loading state weight ``w_c(t)`` (the unloaded fraction of
      the class's above-DA-position online capability —
      ``scripts/data/derive_ercot_commitment_loading_state.py``, frozen rule 23):
      the floored bid becomes ``base + w x (wall - base)``. Moderate regimes
      (w ~ 1) keep the full wall; regimes where reality RUC/self-commits the
      un-offered capacity online near cost stand it down (w -> 0). Backcast
      years read the year's own measured hourly series (the CAMPD
      outage-overlay pattern); years absent from the artifact fall back to
      its pooled climatology (net-load-percentile bin x 4-hour block,
      forward-native). Zero fitted scalars.
    * ``ercot_offer_surface_cleared_share_rt`` (ERCOT-86, default off)
      re-prices the SAME above-boundary CC/CT rows at the MEASURED SCED
      spare-offer ladder (``scripts/data/derive_ercot_sced_offer_wall.py`` —
      the RT/SCED data-basis correction of the wall's measured-cheap DAM
      ladder, ERCOT-84 Finding 1). ``_rt_mode`` selects composition
      ``"replace"`` (A: RT-measured bins swap ladder source) or ``"tier"``
      (B: floor at max(state-weighted DAM, RT)). YEAR-SCOPED (rule 13): no
      pooled fallback — years absent from the RT artifact keep the DAM basis
      byte-identical. The RT leg is never state-weighted (the SCED spare is
      measured on the online fleet — the commitment state is already
      conditioned into the surface). ST_GAS stays DAM-basis (rule 19).
    * ``ercot_faststart_pool_offer`` (ERCOT-88) is a SEPARATE builder
      (:func:`build_ercot_faststart_pool_markup`) that REPLACES every
      surface's markup — this wall's included — on the fast-start rows above
      the measured offline-pool boundary (the caller composes by mask, one
      owner per row-hour; see that builder's docstring).
    * ``ercot_shoulder_online_span`` (ERCOT-89, default off) re-anchors the
      wall/RT ladder's rel geometry on the measured CONDITIONAL online span
      (mean telemetered ON share of non-OUT capability per net-load bin x
      season x 4h block): rel = (share - boundary) / (span - boundary),
      clipped to the ladder top above the span — the SCED spare ladder is
      measured on the ONLINE fleet, and the span stops it being stretched
      over capability that is telemetered OFF at the same conditions
      (charter §8.1's measured 8-10x phantom-headroom wedge). Requires the
      RT leg and the fast-start pool leg armed (the above-span increment is
      PRICED by the pool at the caller, never capped — charter §3(ii)).
      Year-scoped (rule 13): absent years keep this geometry byte-identical.
    """
    state_flag = getattr(config, "ercot_offer_surface_cleared_share_state", False)
    steam_flag = getattr(config, "ercot_offer_surface_cleared_share_steam", False)
    rt_flag = getattr(config, "ercot_offer_surface_cleared_share_rt", False)
    if not getattr(config, "ercot_offer_surface_cleared_share", False):
        if state_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_state scopes the "
                "cleared-share wall — arm ercot_offer_surface_cleared_share "
                "too (the state weight has nothing to scope on its own)."
            )
        if steam_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_steam extends the "
                "cleared-share wall — arm ercot_offer_surface_cleared_share "
                "too (the steam scope has no wall to extend on its own)."
            )
        if rt_flag and config.iso == "ERCOT":
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt re-prices the "
                "cleared-share wall's ladder — arm "
                "ercot_offer_surface_cleared_share too (the RT basis has no "
                "wall to re-price on its own)."
            )
        if (
            getattr(config, "ercot_shoulder_online_span", False)
            and config.iso == "ERCOT"
        ):
            raise ValueError(
                "ercot_shoulder_online_span re-anchors the cleared-share "
                "wall's ladder geometry — arm ercot_offer_surface_cleared_"
                "share too (the span has no wall geometry to re-anchor on "
                "its own)."
            )
        return None
    if config.iso != "ERCOT":
        return None
    rt_mode = str(
        getattr(config, "ercot_offer_surface_cleared_share_rt_mode", "replace")
    )
    if rt_flag and rt_mode not in ("replace", "tier"):
        raise ValueError(
            "ercot_offer_surface_cleared_share_rt_mode must be 'replace' "
            f"(composition A) or 'tier' (composition B), got {rt_mode!r}"
        )
    # Effective class scope: the base merchant CC/CT map, plus the ST_GAS ->
    # "ST" extension when the ERCOT-77 steam flag is armed.
    class_of = dict(_ERCOT_CLEARED_SHARE_CLASS_OF)
    if steam_flag:
        class_of.update(_ERCOT_CLEARED_SHARE_STEAM_CLASS_OF)
    if getattr(config, "ercot_offer_surface_midcurve_conditional", False):
        raise ValueError(
            "ercot_offer_surface_cleared_share and "
            "ercot_offer_surface_midcurve_conditional both price the gas econ "
            "rows — one mechanism per row (rule 19); arm exactly one."
        )
    path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not path:
        from market_sim.config import paths as _paths

        path = str(_paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json")
    surface = json.loads(Path(path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if not edges or ladder_q.size == 0:
        raise ValueError(
            "ercot_offer_surface_cleared_share: surface JSON carries no "
            "edges/quantiles — re-derive scripts/data/derive_ercot_dam_cleared_share.py"
        )
    n_bins = len(edges) + 1

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # ERCOT-73 commitment-loading state weight per class-hour (1.0 = full
    # wall). Year table = the measured backcast overlay; climatology = the
    # forward/holdout fallback on the SAME bin edges (asserted) x hour block.
    state_w: dict[str, np.ndarray] = {}
    if state_flag:
        spath = getattr(config, "ercot_offer_surface_cleared_share_state_path", None)
        if not spath:
            from market_sim.config import paths as _paths

            spath = str(_paths.CALIBRATION_DIR / "ercot_commitment_loading_state.json")
        state = json.loads(Path(spath).read_text())
        sprov = state.get("_provenance", {})
        sedges = tuple(float(x) for x in sprov.get("netload_pct_edges", ()))
        if sedges != edges:
            raise ValueError(
                "ercot_offer_surface_cleared_share_state: state artifact bin "
                f"edges {sedges} != wall edges {edges} — re-derive "
                "scripts/data/derive_ercot_commitment_loading_state.py"
            )
        block_h = int(sprov.get("hour_block_hours", 4))
        hod_block = (np.arange(hours) % 24) // block_h  # (T,)
        for cls_key in set(class_of.values()):
            entry = state.get(cls_key)
            if not entry:
                continue
            yr_tbl = entry.get("years", {}).get(str(year))
            if yr_tbl is not None and len(yr_tbl) >= hours:
                state_w[cls_key] = np.clip(
                    np.asarray(yr_tbl[:hours], dtype=float), 0.0, 1.0
                )
            else:
                clim = np.asarray(
                    state.get("climatology", {}).get(cls_key, ()), dtype=float
                )
                if clim.ndim != 2 or clim.shape[0] != n_bins:
                    continue
                w = clim[hour_bin, np.minimum(hod_block, clim.shape[1] - 1)]
                state_w[cls_key] = np.clip(np.nan_to_num(w, nan=1.0), 0.0, 1.0)

    # Delivered-gas day series on the model clock (the derive's own price
    # normalizer: HH daily + ERCOT basis, forward-filled).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Per-class boundary (n_bins,) + wall table (n_bins, n_q) for this delivery
    # year (pooled fallback for an unmapped/forward year).
    boundaries: dict[str, np.ndarray] = {}
    walls: dict[str, np.ndarray] = {}
    for cls_key in set(class_of.values()):
        entry = surface.get(cls_key)
        if not entry:
            continue
        tbl = entry.get("years", {}).get(str(year)) or entry.get("pooled")
        if not tbl:
            continue
        share = np.asarray(tbl.get("cleared_share", ()), dtype=float)
        lad = tbl.get("ladder", ())
        if share.size != n_bins or len(lad) != n_bins:
            continue
        boundaries[cls_key] = share
        walls[cls_key] = np.array(
            [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
        )  # (n_bins, n_q)

    # ERCOT-86 RT/SCED-basis ladder (data-basis correction of the wall's
    # price surface — same boundary, same rows, same bin geometry, the
    # measured SCED online-spare offer ladder instead of the measured-cheap
    # DAM offered-but-uncleared ladder). YEAR-SCOPED by design (rule 13): only
    # a year present in the RT artifact gets an RT ladder — no pooled
    # fallback, so a 2024/2025-derived surface can never reach 2023's
    # conservative-ops regime; absent years keep the DAM basis byte-identical.
    rt_walls: dict[str, np.ndarray] = {}
    if rt_flag:
        rt_path = getattr(config, "ercot_offer_surface_cleared_share_rt_path", None)
        if not rt_path:
            from market_sim.config import paths as _paths

            rt_path = str(
                _paths.CALIBRATION_DIR / "ercot_sced_offer_wall_condbinned.json"
            )
        rt_surface = json.loads(Path(rt_path).read_text())
        rt_prov = rt_surface.get("_provenance", {})
        rt_edges = tuple(float(x) for x in rt_prov.get("netload_pct_edges", ()))
        rt_q = np.asarray(rt_prov.get("ladder_quantiles", ()), dtype=float)
        if rt_edges != edges or not np.array_equal(rt_q, ladder_q):
            raise ValueError(
                "ercot_offer_surface_cleared_share_rt: RT artifact bin "
                f"geometry (edges {rt_edges}, quantiles {rt_q.tolist()}) != "
                f"DAM wall geometry (edges {edges}, quantiles "
                f"{ladder_q.tolist()}) — re-derive "
                "scripts/data/derive_ercot_sced_offer_wall.py"
            )
        for cls_key in set(class_of.values()):
            entry = rt_surface.get(cls_key)
            if not entry:
                continue
            tbl = entry.get("years", {}).get(str(year))  # year-scoped: no pooled
            if not tbl:
                continue
            lad = tbl.get("ladder", ())
            if len(lad) != n_bins:
                continue
            rt_walls[cls_key] = np.array(
                [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
            )  # (n_bins, n_q)
        if not rt_walls:
            logger.info(
                "ERCOT cleared-share RT basis: year %s absent from the RT "
                "artifact — DAM basis retained byte-identical (year-scoped, "
                "rule 13)",
                year,
            )

    # ERCOT-89 shoulder online-span anchor (ercot_shoulder_online_span): the
    # measured CONDITIONAL online span (mean telemetered ON share of non-OUT
    # capability per net-load bin x season x 4h block,
    # scripts/data/derive_ercot_shoulder_online_span.py) re-anchors this
    # wall's ladder GEOMETRY — rel maps the walled rows onto the ladder over
    # [boundary, span] instead of [boundary, 1.0] — because the SCED spare
    # ladder is measured on the ONLINE fleet, and stretching it over
    # capability that is telemetered OFF at the same conditions is the
    # measured 8-10x phantom-headroom wedge (charter §8.1,
    # docs/handoffs/ercot-shoulder-online-envelope-2026-07.md). Rows above
    # the span clamp at the ladder top HERE; the fast-start subset of them is
    # REPLACED by the pool leg's start-inclusive ladder at the caller
    # (REPLACE-BY-MASK — hence the required ercot_faststart_pool_offer arm),
    # so the above-span increment is PRICED, never capped (charter §3(ii)
    # no-cap line: the rejected ercot41/43 envelope family is not re-opened).
    # YEAR-SCOPED (rule 13): an absent year keeps span_h empty and the
    # full-span geometry byte-identical.
    span_flag = getattr(config, "ercot_shoulder_online_span", False)
    span_h: dict[str, np.ndarray] = {}
    if span_flag:
        if not rt_flag:
            raise ValueError(
                "ercot_shoulder_online_span re-anchors the RT/SCED wall "
                "ladder's geometry — arm ercot_offer_surface_cleared_share_rt "
                "too (there is no measured online-spare ladder to re-anchor "
                "without it)."
            )
        if not getattr(config, "ercot_faststart_pool_offer", False):
            raise ValueError(
                "ercot_shoulder_online_span prices the above-span increment "
                "on the fast-start pool's start-inclusive ladder (charter "
                "§3(ii): re-price the offline increment, never cap/clamp-"
                "only) — arm ercot_faststart_pool_offer too."
            )
        span_tables, _season_idx, _block_idx = _load_ercot_online_span_tables(
            config, year, edges, hours
        )
        for _k, _tbl in span_tables.items():
            span_h[_k] = _tbl[hour_bin, _season_idx, _block_idx]  # (T,)

    # Target rows + within-plant share midpoints: every tranche of the plant
    # ordered by its annual-mean base cost — the model's own rising CAMPD
    # tranche curve defines each row's curve position (the mid-curve
    # construction, scale-free against fleet-capacity mismatches).
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in class_of:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls

    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    n_priced = 0
    n_rt_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            sfx = gen.unit_id.rpartition("_")[2]
            # Row-family scope (rule 19, recorded in the steam flag's config
            # comment): CC/CT wall econ* rows only (committed stays owned by
            # the bridge/floor structure); the ERCOT-77 steam extension prices
            # BOTH the committed and econ* ST_GAS tranches — the flat
            # committed offer level is exactly the measured leg-c defect, and
            # the drag keeps only the min-gen QUANTITY scaffolding (floors
            # compose independently of bids). Peak rungs are never touched
            # (ercot_offer_surface_conditional's rows).
            if row_cls[g] == "ST_GAS":
                if not (sfx.startswith("econ") or sfx == "committed"):
                    continue
            elif not sfx.startswith("econ"):
                continue
            cls_key = class_of[row_cls[g]]
            if cls_key not in boundaries:
                continue
            bnd = boundaries[cls_key]  # (n_bins,)
            wall = walls[cls_key]  # (n_bins, n_q)
            rtw = rt_walls.get(cls_key)
            sp = span_h.get(cls_key) if span_flag else None
            if sp is None:
                # Per-bin target multiplier: 0 (no floor) at/below the
                # boundary or where the bin carries no measured boundary/wall.
                mult_b = np.zeros(n_bins)
                for b in range(n_bins):
                    if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                        continue
                    if not np.isfinite(wall[b]).all():
                        continue
                    rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                    mult_b[b] = float(np.interp(rel, ladder_q, wall[b]))
                # ERCOT-86 RT ladder for the SAME above-boundary rows (same
                # boundary test, the SCED spare-offer quantile ladder as the
                # price source). rt_has marks bins the RT artifact measures —
                # only those bins ever leave the DAM basis.
                rt_mult_b = np.zeros(n_bins)
                rt_has = np.zeros(n_bins, dtype=bool)
                if rtw is not None:
                    for b in range(n_bins):
                        if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                            continue
                        if not np.isfinite(rtw[b]).all():
                            continue
                        rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                        rt_mult_b[b] = float(np.interp(rel, ladder_q, rtw[b]))
                        rt_has[b] = True
                mult_h = mult_b[hour_bin]  # (T,); 0 where no floor
                rt_mult_h = rt_mult_b[hour_bin]
                rt_has_h = rt_has[hour_bin]
            else:
                # ERCOT-89 span-anchored geometry: rel is TIME-varying — the
                # ladder is stretched over [boundary, span(cell)] instead of
                # [boundary, 1.0]. Rows above the measured span (or above a
                # zero-width span) take the ladder top; the fast-start subset
                # of those row-hours is replaced by the pool leg at the
                # caller (one owner per row-hour, rule 19).
                bnd_t = bnd[hour_bin]  # (T,)
                span_eff = np.maximum(sp, bnd_t)  # span never below DA share
                above = (s_g > bnd_t) & np.isfinite(bnd_t) & (bnd_t < 1.0)
                width = span_eff - bnd_t
                rel_t = np.full(hours, np.nan)
                in_span = above & (width > 0.0) & (s_g <= span_eff)
                rel_t[in_span] = (s_g - bnd_t[in_span]) / width[in_span]
                rel_t[above & ~in_span] = 1.0
                mult_h = np.zeros(hours)
                rt_mult_h = np.zeros(hours)
                rt_has_h = np.zeros(hours, dtype=bool)
                for b in range(n_bins):
                    sel = (hour_bin == b) & np.isfinite(rel_t)
                    if not sel.any():
                        continue
                    if np.isfinite(wall[b]).all():
                        mult_h[sel] = np.interp(rel_t[sel], ladder_q, wall[b])
                    if rtw is not None and np.isfinite(rtw[b]).all():
                        rt_mult_h[sel] = np.interp(rel_t[sel], ladder_q, rtw[b])
                        rt_has_h[sel] = True
            if not mult_h.any() and not rt_has_h.any():
                continue
            target = mult_h * gas_day  # (T,); 0 where no floor
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            if state_flag:
                # ERCOT-73: floored bid = base + w x (wall - base) — the
                # measured commitment-loading regime scales the markup.
                w = state_w.get(cls_key)
                if w is None:
                    if not rt_has_h.any():
                        continue  # no measured state for the class: no wall
                    row = np.zeros_like(row)  # DAM leg dead; RT leg may floor
                else:
                    row = row * w
            if rt_has_h.any():
                # RT leg is NEVER state-weighted: the SCED spare ladder is
                # measured on the ONLINE fleet (Base Point -> HASL is the
                # un-loaded remainder per interval), so the commitment state
                # the w-weight corrects for is already conditioned into the
                # surface — weighting it again would double-count.
                rt_target = rt_mult_h * gas_day  # (T,)
                rt_target = np.minimum(rt_target, voll_cap)
                rt_row = np.maximum(0.0, rt_target - mc_base[g, :])
                rt_row = np.where(rt_has_h, rt_row, 0.0)
                if rt_mode == "replace":
                    # Composition A: one wall, one ladder source per bin —
                    # RT-measured bins take the RT floor (even where it is
                    # BELOW the DAM ladder: the DAM basis is refuted there,
                    # not composed with); unmeasured bins keep the DAM basis.
                    row = np.where(rt_has_h, rt_row, row)
                else:
                    # Composition B: the state-weighted DAM wall stands
                    # everywhere; the RT tier rides above its reach.
                    row = np.maximum(row, rt_row)
                if rt_row.any():
                    n_rt_priced += 1
            if row.any():
                markup[g, :] = row
                n_priced += 1

    if n_priced == 0 or not np.any(markup > 0.0):
        logger.info(
            "ERCOT cleared-share offer boundary: no econ row floored (every "
            "row at/below the measured cleared share, or measured walls <= "
            "model econ bids) — byte-identical"
        )
        return None
    logger.info(
        "ERCOT cleared-share offer boundary: floored %d gas econ tranche rows "
        "above the measured DAM cleared share (%d net-load bins, year table "
        "%s)%s; P1-only",
        n_priced,
        n_bins,
        str(year)
        if any(
            str(year) in surface.get(c, {}).get("years", {})
            for c in set(class_of.values())
        )
        else "pooled",
        (
            "; commitment-loading state weight ON (measured "
            + (
                "year series"
                if any(str(year) in state.get(c, {}).get("years", {}) for c in state_w)
                else "climatology fallback"
            )
            + ")"
        )
        if state_flag
        else "",
    )
    if rt_flag and rt_walls:
        logger.info(
            "ERCOT cleared-share RT basis (ERCOT-86): %s composition — %d "
            "rows carry the measured SCED spare-offer ladder (year table %s, "
            "classes %s; RT leg un-state-weighted by construction)",
            rt_mode,
            n_rt_priced,
            year,
            sorted(rt_walls),
        )
    return markup


def _load_ercot_online_span_tables(
    config: ScenarioConfig,
    year: int,
    wall_edges: tuple[float, ...],
    hours: int,
) -> "tuple[dict[str, np.ndarray], np.ndarray, np.ndarray]":
    """Resolve the ERCOT-89 conditional online-span artifact for ``year``.

    Returns ``(tables, season_idx, block_idx)`` where ``tables`` maps the
    measured class key (``"CC"``/``"CT"``) to its resolved
    ``(n_bins, n_seasons, n_blocks)`` conditional ON-share table
    (``scripts/data/derive_ercot_shoulder_online_span.py``), and
    ``season_idx`` / ``block_idx`` are the ``(hours,)`` calendar coordinates
    on the model's fixed-CST non-leap clock. Cells the corpus never covers
    (null in the artifact) resolve to **1.0** — full-span geometry, i.e. the
    mechanism is inert for those hours (no measured conditional, no
    correction). A year absent from the artifact returns ``({}, ...)`` — the
    caller stays byte-identical (YEAR-SCOPED, rule 13: no pooled fallback;
    a 2024/2025-derived table never reaches 2023's conservative-ops regime).
    """
    span_path = getattr(config, "ercot_shoulder_online_span_path", None)
    if not span_path:
        from market_sim.config import paths as _paths

        span_path = str(
            _paths.CALIBRATION_DIR / "ercot_shoulder_online_span_condbinned.json"
        )
    surface = json.loads(Path(span_path).read_text())
    prov = surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    season_of_month = [int(x) for x in prov.get("season_of_month", ())]
    block_h = int(prov.get("hour_block_hours", 0))
    if edges != tuple(wall_edges):
        raise ValueError(
            "ercot_shoulder_online_span: span artifact bin edges "
            f"{edges} != cleared-share wall edges {tuple(wall_edges)} — "
            "re-derive scripts/data/derive_ercot_shoulder_online_span.py"
        )
    if len(season_of_month) != 12 or block_h <= 0:
        raise ValueError(
            "ercot_shoulder_online_span: span artifact carries no "
            "season_of_month/hour_block_hours — re-derive "
            "scripts/data/derive_ercot_shoulder_online_span.py"
        )
    # Calendar coordinates on the model's fixed-CST non-leap 8760 clock (the
    # derive's own hoy convention): month via cumulative month-start hours,
    # 4h block via hour-of-day.
    month_start_h = (
        np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24
    )  # (12,) Jan..Dec starts
    hoy = np.arange(hours)
    month_idx = np.searchsorted(month_start_h[1:], hoy % 8760, side="right")  # 0..11
    season_idx = np.asarray(season_of_month, dtype=int)[month_idx]  # (hours,)
    block_idx = (hoy % 24) // block_h  # (hours,)

    tables: dict[str, np.ndarray] = {}
    for cls_key in ("CC", "CT"):
        tbl = surface.get(cls_key, {}).get("years", {}).get(str(year))
        if not tbl:
            continue
        span = np.array(
            [
                [[np.nan if v is None else float(v) for v in row] for row in mat]
                for mat in tbl.get("span", ())
            ],
            dtype=float,
        )
        if span.ndim != 3 or span.shape[0] != len(edges) + 1:
            continue
        # Uncovered cells -> 1.0: full-span geometry, mechanism inert there.
        tables[cls_key] = np.nan_to_num(span, nan=1.0)
    if not tables:
        logger.info(
            "ERCOT shoulder online span (ERCOT-89): year %s absent from the "
            "span artifact — full-span wall geometry retained byte-identical "
            "(year-scoped, rule 13)",
            year,
        )
    return tables, season_idx, block_idx


def build_ercot_faststart_pool_markup(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    mc_base: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    year: int,
) -> "tuple[np.ndarray, np.ndarray] | None":
    """Build the ERCOT-88 offline fast-start pool ``(markup, own_mask)``.

    The §6.2 mechanism of
    ``docs/handoffs/ercot-residual-midband-formation-lane-2026-07.md`` (§9,
    ``ScenarioConfig.ercot_faststart_pool_offer``). The ERCOT-87 measurement
    adjudicated that the actual $150-500 moderate-tightness band prices on the
    OFFLINE startable CT pool (telemetered OFFQS/OFFNS — ~5x the online
    spare's in-band offer mass; 12-18 CT starts per covered band hour), not on
    any online-spare or unmitigated-CC surface. This builder offers that
    capability to the LP at its measured price::

        boundary(bin) = 1 - pool_frac(bin)          # measured pool share
        rel           = (share_g - boundary) / (1 - boundary)
        target[g, t]  = interp(rel, ladder_q, pool_ladder(bin)) x gas_day(t)
        markup[g, t]  = max(0, min(target, cap_frac x VOLL) - mc_base[g, t])

    on the merchant CT rows (the cleared-share wall's measured "CT" class
    scope) whose WITHIN-PLANT cumulative-capacity midpoint lies above the
    hour-bin's measured pool boundary — the top-of-curve capacity that in
    reality is telemetered offline-startable.

    * **Eligibility is unit physics** (rule 12 / charter §9.2):
      ``min_down_hours <= constants.FASTSTART_POOL_MIN_DOWN_HOURS`` — the
      SCED-startable-intra-hour inequality. CC rows fail by physics (4-8 h),
      ST_GAS by its 8-12 h min-down; no class tuple gates eligibility.
    * **Replace composition, by mask** (rule 19 / charter §9.1): the returned
      ``own_mask`` (n_gen, T) marks the row-hours the pool owns; the caller
      REPLACES every other offer surface's markup there (conditional peak
      surface, cleared-share wall, RT leg alike) — that capability is
      offline, so an online-basis price is refuted for it by status. One
      owner per row-hour, enforced at the composition site. In a measured
      row-hour whose pool target sits below the model's base cost the markup
      is 0 and the row bids cost (the pool is OFFERED, never forced).
    * **An offer-availability, never a floor**: no ``min_gen`` is touched —
      forced-energy (D-2) and off-window-binding (D-4) exposure is vacuous by
      construction, so the rule-17 hazard (a CT floor binding overnight at
      CF ~ 0) is structurally impossible.
    * **Above-LSL basis**: the ladder is derived from the pool's above-LSL
      startable increment only (``derive_ercot_faststart_pool.py``) — the
      negative below-LSL min-gen curve bottoms never enter, and the markup
      only ever RAISES a bid.
    * **Year-scoped** (rule 13): no pooled fallback — a year absent from the
      artifact returns None (every surface byte-identical; 2024/2025 only,
      the RT wall's own 2023 input-blocked bar). Zero fitted scalars; the
      artifact is frozen against residuals (rule 23).
    * **ERCOT-89 span boundary** (``ercot_shoulder_online_span``, default
      off): the boundary generalizes from ``1 - pool_frac(bin)`` to the
      measured conditional online span (charter §6 shape (a) — the FULL
      offline increment of merchant CT priced at the pool's start-inclusive
      ladder, clamped below by the bin's DA cleared share). Span years
      absent from the span artifact keep the static boundary byte-identical.
    * P1-only via the shared ``mc_bid_adjust`` seam: P0 run lengths and the
      startup-amortization coupling are untouched.

    Requires the cleared-share wall armed (the recipe context the §9.1
    rule-19 enumeration was performed against); arming the pool leg without
    it is a hard error.
    """
    if not getattr(config, "ercot_faststart_pool_offer", False):
        return None
    if config.iso != "ERCOT":
        return None
    if not getattr(config, "ercot_offer_surface_cleared_share", False):
        raise ValueError(
            "ercot_faststart_pool_offer composes against the cleared-share "
            "wall's row pricing (charter §9.1 enumeration) — arm "
            "ercot_offer_surface_cleared_share too."
        )
    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS

    pool_path = getattr(config, "ercot_faststart_pool_offer_path", None)
    if not pool_path:
        from market_sim.config import paths as _paths

        pool_path = str(_paths.CALIBRATION_DIR / "ercot_faststart_pool_condbinned.json")
    pool_surface = json.loads(Path(pool_path).read_text())
    prov = pool_surface.get("_provenance", {})
    edges = tuple(float(x) for x in prov.get("netload_pct_edges", ()))
    ladder_q = np.asarray(prov.get("ladder_quantiles", ()), dtype=float)
    if not edges or ladder_q.size == 0:
        raise ValueError(
            "ercot_faststart_pool_offer: pool artifact carries no "
            "edges/quantiles — re-derive scripts/data/derive_ercot_faststart_pool.py"
        )
    # Same bin geometry as the wall artifacts by construction (the derive
    # imports the shared NETLOAD_PCT_EDGES/LADDER_QUANTILES); assert against
    # the wall artifact when the wall is armed so a drifted re-derive is loud.
    wall_path = getattr(config, "ercot_offer_surface_cleared_share_path", None)
    if not wall_path:
        from market_sim.config import paths as _paths

        wall_path = str(
            _paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json"
        )
    wall_prov = json.loads(Path(wall_path).read_text()).get("_provenance", {})
    wall_edges = tuple(float(x) for x in wall_prov.get("netload_pct_edges", ()))
    if wall_edges and wall_edges != edges:
        raise ValueError(
            "ercot_faststart_pool_offer: pool artifact bin edges "
            f"{edges} != cleared-share wall edges {wall_edges} — re-derive "
            "scripts/data/derive_ercot_faststart_pool.py"
        )
    n_bins = len(edges) + 1

    tbl = pool_surface.get("CT", {}).get("years", {}).get(str(year))
    if not tbl:  # year-scoped: no pooled fallback (rule 13)
        logger.info(
            "ERCOT fast-start pool (ERCOT-88): year %s absent from the pool "
            "artifact — every surface byte-identical (year-scoped, rule 13)",
            year,
        )
        return None
    frac = np.asarray(tbl.get("pool_frac", ()), dtype=float)
    lad = tbl.get("ladder", ())
    if frac.size != n_bins or len(lad) != n_bins:
        return None
    pool_bnd = 1.0 - np.clip(frac, 0.0, 1.0)  # (n_bins,)
    pool_wall = np.array(
        [[float(pt[1]) for pt in lad_b] for lad_b in lad], dtype=float
    )  # (n_bins, n_q)

    hours = int(mc_base.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    # ERCOT-89 shoulder online-span boundary (ercot_shoulder_online_span):
    # when armed, the pool boundary generalizes from the measured OFFQS/OFFNS
    # pool share (1 - pool_frac per bin) to the measured CONDITIONAL online
    # span (charter §6 shape (a): the FULL offline increment of merchant CT
    # is priced at the pool's start-inclusive ladder, not just its
    # quick-start slice). The span is clamped below by the bin's measured
    # DA cleared share (DA-cleared capability is committed, so the online
    # span can never sit below it — the wall leg uses the same clamp).
    # YEAR-SCOPED (rule 13): a year absent from the span artifact keeps the
    # ERCOT-88 static boundary byte-identical.
    span_ct: "np.ndarray | None" = None
    if getattr(config, "ercot_shoulder_online_span", False):
        span_tables, _season_idx, _block_idx = _load_ercot_online_span_tables(
            config, year, edges, hours
        )
        span_tbl = span_tables.get("CT")
        if span_tbl is not None:
            wall_surface = json.loads(Path(wall_path).read_text())
            wall_ct = wall_surface.get("CT", {})
            wall_tbl = wall_ct.get("years", {}).get(str(year)) or wall_ct.get("pooled")
            bnd_ct = (
                np.asarray(wall_tbl.get("cleared_share", ()), dtype=float)
                if wall_tbl
                else np.full(n_bins, np.nan)
            )
            if bnd_ct.size != n_bins:
                bnd_ct = np.full(n_bins, np.nan)
            span_raw = span_tbl[hour_bin, _season_idx, _block_idx]  # (T,)
            bnd_t = np.where(np.isfinite(bnd_ct[hour_bin]), bnd_ct[hour_bin], 0.0)
            span_ct = np.maximum(span_raw, bnd_t)

    # Delivered-gas day series (the wall's own price normalizer).
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    gas_day = daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)  # (T,)

    # Row universe: the wall's measured merchant-CT class scope (the pool
    # ladder's own measured class); ELIGIBILITY within it is unit physics.
    ct_groups = {
        grp for grp, key in _ERCOT_CLEARED_SHARE_CLASS_OF.items() if key == "CT"
    }
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(generators):
        if (getattr(gen, "plant_group", None) or "") not in ct_groups:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)

    pmax = fleet_arrays.pmax
    voll_cap = float(
        getattr(config, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(config, "voll", 5000.0))
    markup = np.zeros_like(mc_base)
    own_mask = np.zeros_like(mc_base, dtype=bool)
    n_priced = 0
    mean_mc = mc_base.mean(axis=1)
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total  # within-plant share midpoints
        for g, s_g in zip(order, mids):
            gen = generators[g]
            # Rule-12 physics gate: SCED-startable intra-hour. Committed and
            # must-run blocks stay with their own floor structure (rule 19) —
            # only the bid tranches (econ*/peak*) join the pool universe.
            if (
                float(getattr(gen, "min_down_hours", 0) or 0)
                > FASTSTART_POOL_MIN_DOWN_HOURS
            ):
                continue
            sfx = gen.unit_id.rpartition("_")[2]
            if not (sfx.startswith("econ") or sfx.startswith("peak")):
                continue
            if span_ct is None:
                # ERCOT-88 static boundary: the measured OFFQS/OFFNS pool
                # share per net-load bin.
                mult_b = np.zeros(n_bins)
                has_b = np.zeros(n_bins, dtype=bool)
                for b in range(n_bins):
                    pb = pool_bnd[b]
                    if not np.isfinite(pb) or pb >= 1.0 or s_g <= pb:
                        continue
                    if not np.isfinite(pool_wall[b]).all():
                        continue
                    rel = (s_g - pb) / (1.0 - pb)
                    mult_b[b] = float(np.interp(rel, ladder_q, pool_wall[b]))
                    has_b[b] = True
                if not has_b.any():
                    continue
                mult_h = mult_b[hour_bin]  # (T,)
                mask = has_b[hour_bin]  # (T,)
            else:
                # ERCOT-89 span boundary: the row-hours ABOVE the measured
                # conditional online span take the pool's start-inclusive
                # ladder (rel over (span, 1]); hours whose span reaches 1.0
                # (fully-online cells, or cells the corpus never covers)
                # are never pool-owned.
                own_t = (s_g > span_ct) & (span_ct < 1.0)
                rel_t = np.zeros(hours)
                rel_t[own_t] = (s_g - span_ct[own_t]) / (1.0 - span_ct[own_t])
                mult_h = np.zeros(hours)
                mask = np.zeros(hours, dtype=bool)
                for b in range(n_bins):
                    sel = (hour_bin == b) & own_t
                    if not sel.any():
                        continue
                    if not np.isfinite(pool_wall[b]).all():
                        continue
                    mult_h[sel] = np.interp(rel_t[sel], ladder_q, pool_wall[b])
                    mask[sel] = True
                if not mask.any():
                    continue
            target = mult_h * gas_day  # (T,)
            target = np.minimum(target, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            markup[g, :] = np.where(mask, row, 0.0)
            own_mask[g, :] = mask
            n_priced += 1

    if not own_mask.any():
        logger.info(
            "ERCOT fast-start pool (ERCOT-88): no fast-start row above the "
            "measured pool boundary — byte-identical"
        )
        return None
    logger.info(
        "ERCOT fast-start pool (ERCOT-88%s): %d fast-start rows carry the "
        "offline-pool above-LSL SCED2 ladder (year table %s; physics gate "
        "min_down <= %.0f h; replace-by-mask composition, never "
        "state-weighted)",
        ("; ERCOT-89 conditional online-span boundary" if span_ct is not None else ""),
        n_priced,
        year,
        FASTSTART_POOL_MIN_DOWN_HOURS,
    )
    return markup, own_mask


# Model tranche suffixes carrying the gas fleet's committed (LSL) block and the
# economic ramp — the rows the low-curve markdown reprices. ``econc``-prefixed
# suffixes are the N-slice smoothed econ ramp (``_econ_curve_steps``); ``econ``/
# ``econlo``/``econhi`` are the unsmoothed variants. Peak rungs are the TOP
# surface's rows and are never touched here (disjoint by construction, rule 19).
_LOWCURVE_ECON_SUFFIXES: tuple[str, ...] = ("econ", "econlo", "econhi")


def _lowcurve_row_family(unit_id: str) -> str | None:
    """Return ``"committed"`` / ``"econ"`` for a low-curve-eligible row, else None."""
    sfx = str(unit_id).rpartition("_")[2]
    if sfx == "committed":
        return "committed"
    if sfx in _LOWCURVE_ECON_SUFFIXES:
        return "econ"
    if sfx.startswith("econc") and sfx[5:].isdigit():
        return "econ"
    return None


def build_ercot_offer_surface_lowcurve_markdown(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    p0_dispatch: "np.ndarray | None" = None,
) -> "np.ndarray | None":
    """Build the P1-only conditional low-curve gas offer markdown ``(n_gen, T)``.

    The trough-price-formation MIRROR of
    :func:`build_ercot_offer_surface_conditional_markup`
    (``ScenarioConfig.ercot_offer_surface_lowcurve``): where the adopted top leg
    restores the measured offer distribution's UPPER tail in anticipated-tight
    net-load bins (clamped never to lower an offer), this leg restores its LOWER
    tail — the committed fleet's cheap segments the all-hours p50 band collapse
    deleted (clamped never to RAISE one). Measured bands from the same 60-Day
    DAM disclosure corpus, committed/online resources only
    (``scripts/data/derive_dam_offer_hrmults.py --low-curve-binned``):

    * ``binned_committed_p50`` — the Min-Gen-Cost (LSL block) multiplier per
      net-load bin. Committed units bid their LSL far below SRMC
      (cycling-avoidance / stay-on bidding), and MORE so in tight bins (CC p50
      0.585 loose -> 0.133 tight vs the model's resolved ~1.0). Applied to each
      plant's ``_committed`` tranche as a class-level ratio
      ``min(1, measured / resolved_committed)`` — plant heterogeneity rides on
      each plant's own heat rate, exactly the top leg's resolved-peak
      construction.
    * ``binned_low_body`` — the lower-body incremental-curve multiplier per
      curve-position band (rel < 0.22 / 0.44 / 0.67) per bin, matched to each
      plant's own rising econ ramp position-for-position (a cross-fleet RANK
      mapping conflated plant cheapness with curve position, eroding the
      mild-day evening margin and shuffling dispatch from coal — the v1 probe
      finding). With the keeper's delta-adjusted econ ramp already at/below the
      measured band medians, the <= 1 clamp leaves the econ rungs largely
      byte-identical — kept for completeness and forward honesty, not effect.

    ``p0_dispatch`` (the P0 base-cost solution, ``(n_gen, T)``) gates the
    markdown to plant-hours the model's OWN commitment discovery runs the plant
    (plant dispatch > 1 MW): the measured discounts are committed-unit bidding,
    and the model analogue of "committed" is its own P0 solve — the
    forward-regenerating construction the CAISO RA bridge and the PJM path-B
    reserve scoping already use. Without the gate, offline plants' discounted
    blocks undercut coal/ST in P1 and steal dispatch reality's committed-state
    bidding cannot (the v1 probe's -1.7 TWh coal shuffle). ``None`` applies the
    markdown ungated (unit tests / diagnostics).

    P1-only via the shared ``mc_bid_adjust`` seam: P0 run lengths, the
    startup-amortization coupling and every floor are byte-identical. Gas
    classes only (coal untouched — take-or-pay/passthrough governs its low
    bids, rule 19; peak rungs are the top leg's — disjoint). Zero fitted
    scalars: the trigger (net-load percentile) and every level (measured QSE
    quantiles) are rule-13-admissible, derived from source data only (rule 21)
    and frozen against residuals (rule 20).

    Returns ``None`` (P1 unchanged) when the flag is off, the ISO is not ERCOT,
    the surface JSON is absent, or no eligible rows exist.
    """
    if not getattr(config, "ercot_offer_surface_lowcurve", False):
        return None
    if config.iso != "ERCOT":
        return None
    path = getattr(config, "ercot_offer_surface_lowcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / "offer_curve_dam_lowcurve_condbinned.json"
        if not default.exists():
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))

    edges = tuple(float(x) for x in config.ercot_offer_surface_netload_pcts)
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            "ercot_offer_surface_lowcurve: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            "(re-derive with matching --low-curve-binned edges, or fix the config)."
        )
    n_bins = len(edges) + 1
    rel_bands = tuple(
        float(x)
        for x in surface.get("_provenance", {}).get(
            "rel_bands", (0.0, 0.22, 0.44, 0.67)
        )
    )

    heat_rate = np.asarray(fleet_arrays.heat_rate, dtype=float)
    hours = int(fuel_prices.shape[1])
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges) if len(edges) else np.array([])
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    curves = getattr(config, "offer_curve_by_group", None) or {}

    # Plant grouping: rows keyed by the unit_id prefix up to the tranche suffix,
    # families tagged committed/econ. All of a plant's rows (any suffix) feed
    # the P0 online mask.
    plant_committed: dict[str, int] = {}
    plant_econ: dict[str, list[int]] = {}
    plant_rows: dict[str, list[int]] = {}
    plant_cls: dict[str, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None)
        if cls not in surface or not isinstance(surface.get(cls), dict):
            continue
        key = str(gen.unit_id).rpartition("_")[0]
        plant_rows.setdefault(key, []).append(g)
        plant_cls[key] = cls
        fam = _lowcurve_row_family(gen.unit_id)
        if fam == "committed":
            plant_committed[key] = g
        elif fam == "econ":
            plant_econ.setdefault(key, []).append(g)
    if not plant_committed:
        return None

    markdown = np.zeros((len(generators), hours), dtype=float)
    n_repriced = 0
    for key, crow in plant_committed.items():
        cls = plant_cls[key]
        entry = surface[cls]
        committed_p50 = entry.get("binned_committed_p50") or []
        low_body = entry.get("binned_low_body") or []
        resolved_c = float((curves.get(cls) or {}).get("committed", 0.0) or 0.0)
        if resolved_c <= 0.0 or len(committed_p50) != n_bins:
            continue

        # P0 online gate: the plant runs this hour in the model's own base-cost
        # commitment discovery. None -> ungated (all hours eligible).
        if p0_dispatch is not None:
            rows = np.asarray(plant_rows[key], dtype=int)
            online = p0_dispatch[rows, :hours].sum(axis=0) > 1.0  # (T,)
        else:
            online = np.ones(hours, dtype=bool)

        # committed (LSL) tranche: class-level ratio per bin on the resolved band.
        ratio_c = np.ones(n_bins, dtype=float)
        for b in range(n_bins):
            v = committed_p50[b]
            if v is not None and np.isfinite(v):
                ratio_c[b] = min(1.0, float(v) / resolved_c)
        row_ratio = np.where(online, ratio_c[hour_bin], 1.0)  # (T,)
        if np.any(row_ratio < 1.0):
            energy = heat_rate[crow] * fuel_prices[crow, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[crow, :] = adj
                n_repriced += 1

        # econ ramp rungs: within-plant curve position -> measured rel-band
        # median (largely clamped to no-op on the keeper's delta-adjusted ramp).
        erows = plant_econ.get(key)
        if not erows or len(low_body) != n_bins:
            continue
        plant_hr = heat_rate[crow] / resolved_c  # the plant's base heat rate
        order = sorted(erows, key=lambda g: heat_rate[g])
        n_e = len(order)
        for i, g in enumerate(order):
            rel = (i + 0.5) / n_e * rel_bands[-1]  # position within [0, 0.67]
            k = int(np.searchsorted(np.asarray(rel_bands[1:]), rel, side="right"))
            if k >= len(rel_bands) - 1:
                continue
            rung_mult = heat_rate[g] / plant_hr
            if rung_mult <= 0.0:
                continue
            ratio_e = np.ones(n_bins, dtype=float)
            moved = False
            for b in range(n_bins):
                bands = low_body[b] or []
                v = bands[k] if k < len(bands) else None
                if v is not None and np.isfinite(v) and float(v) < rung_mult:
                    ratio_e[b] = float(v) / rung_mult
                    moved = True
            if not moved:
                continue
            row_ratio = np.where(online, ratio_e[hour_bin], 1.0)
            energy = heat_rate[g] * fuel_prices[g, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[g, :] = adj
                n_repriced += 1

    if n_repriced == 0 or not np.any(markdown < 0.0):
        return None
    loose = int((hour_bin == 0).sum())
    logger.info(
        "ERCOT conditional low-curve surface: marked down %d gas committed/econ "
        "rows across %d net-load bins (loosest bin %d/%d hours); P1-only, "
        "ratio clamped <= 1, %s",
        n_repriced,
        n_bins,
        loose,
        hours,
        "P0-online-gated" if p0_dispatch is not None else "ungated",
    )
    return markdown


def build_ercot_offer_surface_lowcurve_floorscoped_markdown(
    fleet_arrays: "FleetArrays",
    generators: list[Generator],
    fuel_prices: np.ndarray,
    net_load_mw: np.ndarray,
    config: ScenarioConfig,
    bridge_floor_mask: "np.ndarray | None",
) -> "np.ndarray | None":
    """Build the FLOOR-SCOPED committed-LSL P1 markdown ``(n_gen, T)`` (ERCOT-64).

    The enumerated price-side lever from the ERCOT-63 adjudication
    (``ScenarioConfig.ercot_offer_surface_lowcurve_floorscoped``;
    docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md §7): the measured
    committed-CC LSL (Min-Gen-Cost) bid — the SAME frozen ERCOT-62 quantile
    artifact the v2 markdown reads (``binned_committed_p50`` per net-load bin,
    ``offer_curve_dam_lowcurve_condbinned.json``) — applied to each gas plant's
    ``_committed`` tranche ONLY in the hours the ERCOT gas commitment bridge
    floors that plant (``bridge_floor_mask``), where the tranche genuinely
    plays its LSL role. The tranche-wide v2
    (:func:`build_ercot_offer_surface_lowcurve_markdown`) was probe-refuted
    even in composition with the bridge because it repriced the tranche's
    ABOVE-floor mid-merit capacity at the LSL bid in every online hour
    (spread compression, CT/CC overshoot — diagnosis §5/§7); this variant
    keeps every non-floored hour byte-identical.

    Scope deltas vs the v2 (deliberate, both remove refuted surface):

    * **Committed tranche only** — no econ low-body leg. The econ rungs were
      "largely clamp-inert, kept for completeness" in the v2; in bridged gap
      hours they are not playing an LSL role (the plant is held AT min-load
      by the floor), so there is nothing measured to reprice them to.
    * **Hour gate = the bridge's own floor mask, never P0-online.** P0-online
      is FALSE in bridged gap hours by construction — the floor exists
      because the base-cost P0 cycled the plant off — so the v2 gate zeroes
      the markdown exactly where this variant must act (the ERCOT-64 charter
      wiring trap #1). The mask is computed ONCE by the bridge and shared
      (``pipeline.commitment.build_ercot_gas_bridge_p1_preps``), never
      re-detected here.

    Rule-19 bookkeeping: a BID change on already-floored hours — no new
    floor, no D-2 id; composes with the bridge (the committed STATE) and is
    disjoint from the top-leg surface (peak rungs). Zero fitted scalars:
    trigger = the bridge floor mask + within-year net-load bin (both the
    model's own / forward-native), levels = the frozen measured QSE
    quantiles (rules 13/20/21). P1-only via the shared ``mc_bid_adjust``
    seam — P0 run lengths, the startup coupling and every floor
    byte-identical; the repriced energy part is floored at $1/MWh and the
    ratio clamped <= 1 (a markdown can only lower).

    PROBE VERDICT (ERCOT-64, 2026-07-13): provably INERT on the keeper — the
    bridge floor clips at the committed tranche's own capacity for every
    bridged plant, so the tranche is exactly pinned (``min_gen == pmax ×
    availability``) in this markdown's entire window and its bid coefficient
    cannot move the LP solution or duals (2023 probe byte-identical to the
    keeper). Recorded as the closure of the LSL price-side enumeration; see
    the ScenarioConfig field docstring and diagnosis §8.

    Args:
        bridge_floor_mask: ``(n_gen, T)`` boolean — the gen-hours the ERCOT
            gas commitment bridge floored (``bridge_floor > 0``). A plant is
            "in its LSL role" in hour ``t`` when ANY of its rows is floored.
            ``None`` / all-False returns ``None`` (no bridged hours — the
            markdown has no window).

    Returns ``None`` (P1 unchanged) when the flag is off, the ISO is not
    ERCOT, the surface JSON is absent, the mask is empty, or no committed row
    moves.
    """
    if not getattr(config, "ercot_offer_surface_lowcurve_floorscoped", False):
        return None
    if config.iso != "ERCOT":
        return None
    if bridge_floor_mask is None or not np.any(bridge_floor_mask):
        return None
    # Same frozen artifact + path field as the v2 (one measured source,
    # rule 23); the default resolves to the ERCOT-62 derive output.
    path = getattr(config, "ercot_offer_surface_lowcurve_path", None)
    if not path:
        from market_sim.config import paths as _paths

        default = _paths.CALIBRATION_DIR / "offer_curve_dam_lowcurve_condbinned.json"
        if not default.exists():
            return None
        path = str(default)
    surface = _load_condbinned_surface(str(path))

    edges = tuple(float(x) for x in config.ercot_offer_surface_netload_pcts)
    json_edges = tuple(
        float(x) for x in surface.get("_provenance", {}).get("netload_pct_edges", ())
    )
    if json_edges and json_edges != edges:
        raise ValueError(
            "ercot_offer_surface_lowcurve_floorscoped: config netload_pcts "
            f"{edges} disagree with the derived surface's edges {json_edges} "
            "(re-derive with matching --low-curve-binned edges, or fix the config)."
        )
    n_bins = len(edges) + 1

    heat_rate = np.asarray(fleet_arrays.heat_rate, dtype=float)
    hours = int(fuel_prices.shape[1])
    mask = np.asarray(bridge_floor_mask, dtype=bool)[:, :hours]
    net_load = np.asarray(net_load_mw, dtype=float)[:hours]
    thresholds = np.quantile(net_load, edges) if len(edges) else np.array([])
    hour_bin = np.searchsorted(thresholds, net_load, side="right")  # (T,)

    curves = getattr(config, "offer_curve_by_group", None) or {}

    # Plant grouping: identical prefix keying to the v2 builder — all of a
    # plant's rows (any tranche suffix) feed its floored-hours mask.
    plant_committed: dict[str, int] = {}
    plant_rows: dict[str, list[int]] = {}
    plant_cls: dict[str, str] = {}
    for g, gen in enumerate(generators):
        cls = getattr(gen, "plant_group", None)
        if cls not in surface or not isinstance(surface.get(cls), dict):
            continue
        key = str(gen.unit_id).rpartition("_")[0]
        plant_rows.setdefault(key, []).append(g)
        plant_cls[key] = cls
        if _lowcurve_row_family(gen.unit_id) == "committed":
            plant_committed[key] = g
    if not plant_committed:
        return None

    markdown = np.zeros((len(generators), hours), dtype=float)
    n_repriced = 0
    floored_plant_hours = 0
    for key, crow in plant_committed.items():
        cls = plant_cls[key]
        committed_p50 = surface[cls].get("binned_committed_p50") or []
        resolved_c = float((curves.get(cls) or {}).get("committed", 0.0) or 0.0)
        if resolved_c <= 0.0 or len(committed_p50) != n_bins:
            continue

        # THE scope: hours the bridge floors this plant (any of its rows).
        rows = np.asarray(plant_rows[key], dtype=int)
        floored = mask[rows, :].any(axis=0)  # (T,)
        if not np.any(floored):
            continue
        floored_plant_hours += int(floored.sum())

        # committed (LSL) tranche: class-level ratio per bin on the resolved
        # band — the v2 construction, gated to the floored hours.
        ratio_c = np.ones(n_bins, dtype=float)
        for b in range(n_bins):
            v = committed_p50[b]
            if v is not None and np.isfinite(v):
                ratio_c[b] = min(1.0, float(v) / resolved_c)
        row_ratio = np.where(floored, ratio_c[hour_bin], 1.0)  # (T,)
        if np.any(row_ratio < 1.0):
            energy = heat_rate[crow] * fuel_prices[crow, :hours]
            adj = energy * (row_ratio - 1.0)
            adj = np.maximum(adj, np.minimum(0.0, 1.0 - energy))
            if np.any(adj < 0.0):
                markdown[crow, :] = adj
                n_repriced += 1

    if n_repriced == 0 or not np.any(markdown < 0.0):
        return None
    logger.info(
        "ERCOT floor-scoped LSL markdown: %d gas committed tranches marked "
        "down over %d bridge-floored plant-hours (%d net-load bins); P1-only, "
        "committed rows only, ratio clamped <= 1",
        n_repriced,
        floored_plant_hours,
        n_bins,
    )
    return markdown

"""Voluntary clean-energy demand — the annual volumetric attribute row (SCN-WS3b).

THE scenario axis owner ruling **S1** (2026-09-06, card D-3) admitted: a
declared, forecast-only, publicly-anchored, DEFAULT-OFF what-if over the
ffr-5b null, the same admissibility class as ``carbon_price_path`` and
``datacenter_load_path`` (the design memo, ``docs/handoffs/voluntary-clean-
demand-design-memo-2026-09-05.md`` §1). The reference case, every backcast
keeper, every hindcast and every crossover carry NO voluntary demand: the
config seam coerces the whole ``voluntary_*`` block to its defaults in any
non-forward run (``ScenarioConfig.__post_init__``, rule 13 [R-MEASURED]) and
:func:`validate_voluntary_config` is the defense in depth.

**Representation (memo §2.1, Option A).** ONE annual inequality per ISO-year,
built as ONE MORE REGION of the clean-tier row family
(``policy.clean_tiers`` / ``model.lp.rows`` — the second consumer of the seam
SCN-WS2a relaxed for exactly this, after its federal CES target row)::

    Σ_t Σ_z (W[z,t] + S[z,t]) + Σ_t Σ_{g ∈ eligible} P[g,t] + Σ_t ESC[t]  ≥  V(ISO, y)

with an ALL-ZONE eligibility mask (any zone's certificate serves any buyer
in the ISO — the voluntary market's annual REC-matching convention and the
same free-intra-ISO-trade premise the ISO-wide RPS row carries), the volume
``V`` expressed through the builder's own obligation-fraction algebra
(:func:`voluntary_obligation_frac`), a name-tuple qualifying spec (the
eligible set — indicator coefficients), and the escape column priced at the
buyer's WILLINGNESS-TO-PAY CEILING ``w`` rather than a statutory ACP. The
row's dual is the voluntary REC / PPA attribute price: ``0`` when slack,
``(0, w]`` when binding, exactly ``w`` when the escape fires (the buyer stops
buying at its ceiling and the shortfall ``V − Σ eligible`` is the
un-procured volume). It reaches entry and retirement through the EXISTING
``clean_attribute_price_by_fuel → max(EAC, RPS dual, clean dual)`` screen
seam (``clean_tiers.clean_credit_by_fuel`` credits every eligible fuel at
``dual × 1.0`` over the all-zone mask) — no new consumer, one certificate
sold once (rule 19 [R-ONE-MECH]).

**Volume (memo §3.1), DC-linked and read from the run's own demand**::

    V(ISO, y) = s_base(path, y) · w_ISO · E_nonDC(ISO, y)  +  f_commit(path, y) · E_DC(ISO, y)

``E_DC`` is the energy of the data-centre block the model already builds
(:func:`market_sim.data.datacenter.datacenter_block_energy_mwh`) and
``E_nonDC = E_total − E_DC`` is the served energy that is not the block,
both taken from the ``(n_zones, T)`` demand the LP is handed — AFTER the load
layers fold in — so a high-DC case raises the voluntary volume without a
second knob and the growth×DC relocation discipline is never double-counted
(memo §3.4). Every level is a cited ``constants.VOLUNTARY_*`` entry; this
module holds no literal, no per-ISO dict and no fallback (rule 24
[R-REGISTRY]). The two cells owner ruling S3 did NOT reach (``f_commit`` mid,
the WTP-ceiling level) are labelled ILLUSTRATIVE at their constants.

**What is deliberately NOT here.** No additionality mask in dispatch (the
W/S columns are zone aggregates with no vintage, and annual REC matching has
none either — memo §2.1; a new-builds-only crediting rule would be an
entry-screen rule, owner box D-3c). No netting logic against a federal CES
target row (owner box D-6 is OPEN: the campaign reports both nettings at the
report layer; in dispatch the two rows are independent constraints, the
FFR-6B §6.4 doctrine). No hourly (24/7) matching (D-3b: deferred to the
isolated ``scope2-lce-portfolio`` tool).

**Eligible set.** ``constants.VOLUNTARY_ELIGIBLE_FUELS_DEFAULT`` (wind, solar,
offshore wind, geothermal — the voluntary RENEWABLE market's set) is the
memo's RECOMMENDATION under the OPEN owner box D-3c, never a ruled default;
``voluntary_eligible_fuels`` is the labelled override for a "carbon-free" arm
(nuclear / CCS). Names resolve against ``FUEL_TYPE_MAP`` at build time and an
unknown name is a hard error (the row builder's own discipline).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from market_sim.config.constants import (
    VOLUNTARY_BASELINE_ISO_WEIGHT,
    VOLUNTARY_BASELINE_SHARE,
    VOLUNTARY_COMMITTED_DC_FRACTION,
    VOLUNTARY_ELIGIBLE_FUELS_DEFAULT,
    VOLUNTARY_WTP_CEILING_USD_PER_MWH,
)
from market_sim.config.scenarios import ScenarioConfig
from market_sim.data.datacenter import datacenter_block_energy_mwh
from market_sim.data.fleet import FUEL_TYPE_MAP
from market_sim.policy.clean_tiers import CleanRegionArrays, append_clean_region

logger = logging.getLogger(__name__)

#: The region label the voluntary row carries in ``CleanRegionArrays.labels``
#: (the runner's dual log keys on it; the federal row's sibling constant is
#: ``policy.federal_ces.FEDERAL_CES_REGION_LABEL``).
VOLUNTARY_REGION_LABEL = "VOLUNTARY"

#: The path vocabulary (the ``datacenter_load_path`` grammar). ``"off"`` = no
#: row, byte-identical.
VOLUNTARY_PATH_OFF: str = "off"
VOLUNTARY_PATHS: tuple[str, ...] = ("off", "low", "mid", "high")

#: The two zone-column fuels every clean-family row credits at 1.0 by
#: construction (``model.lp.rows._RPS_ROW_BASE_FUELS``): an eligible set must
#: name both, or the row would silently credit what the config excluded.
_ZONE_COLUMN_FUELS: tuple[str, str] = ("wind", "solar")


@dataclass(frozen=True)
class VoluntaryVolume:
    """The resolved voluntary volume for one ISO-year, with its components.

    Everything the row's RHS was built from, so what the LP was handed and
    what the config says cannot disagree (memo §5.3). All energies in MWh
    over the demand array's horizon.

    Attributes:
        path: The ``voluntary_clean_demand_path`` label the levels came from.
        baseline_share: ``s_base(path, y)`` — the voluntary share of non-DC load.
        iso_weight: ``w_ISO`` — the per-ISO re-weighting of the national share
            (1.0 wherever the EIA-861 basis is still ``needs-intake``).
        committed_fraction: ``f_commit(path, y)`` — the committed share of the
            DC block's energy.
        energy_total_mwh: ``E_total`` — the demand array's energy.
        energy_dc_mwh: ``E_DC`` — the DC block's energy.
        energy_non_dc_mwh: ``E_nonDC = max(0, E_total − E_DC)``.
        volume_mwh: ``V`` — the row's RHS.
    """

    path: str
    baseline_share: float
    iso_weight: float
    committed_fraction: float
    energy_total_mwh: float
    energy_dc_mwh: float
    energy_non_dc_mwh: float
    volume_mwh: float


def _interp_edge_held(knots: dict[int, float], year: int) -> float:
    """Linear between ``{year: value}`` knots, edge-held outside them.

    The ``DATACENTER_ADDITIONS_MW`` grammar every ``VOLUNTARY_*`` table uses
    (a single knot = held flat). Keys may arrive as strings from YAML.
    """
    if not knots:
        raise ValueError("voluntary level table is empty — nothing to interpolate")
    years = np.array(sorted(int(k) for k in knots), dtype=float)
    values = np.array([float(knots[k]) for k in sorted(knots, key=int)], dtype=float)
    return float(np.interp(float(year), years, values))


def voluntary_row_active(config: ScenarioConfig) -> bool:
    """Return True when the voluntary row is built for this config.

    The single gate: a non-``"off"`` path in a FORWARD run. The config seam
    already coerces the path off in ``mode="backcast"`` and in a hindcast,
    so the mode legs here are defense in depth (the ``_rps_region_grain_
    active`` style — enforced at consumption, never assumed), not a second
    mechanism.
    """
    return (
        config.mode == "forecast"
        and not config.hindcast
        and config.voluntary_clean_demand_path != VOLUNTARY_PATH_OFF
    )


def validate_voluntary_config(config: ScenarioConfig) -> None:
    """Raise if a non-off voluntary path reaches a scored backcast / hindcast.

    The standalone defense in depth the memo §5.1 asks for (the
    ``data.datacenter.validate_datacenter_config`` construction): the
    constructor coerces, this guards a post-construction mutation or bypass.

    Raises:
        ValueError: A non-off path in ``mode="backcast"`` or with ``hindcast``.
    """
    if config.voluntary_clean_demand_path == VOLUNTARY_PATH_OFF:
        return
    if config.mode == "backcast" or config.hindcast:
        raise ValueError(
            "voluntary_clean_demand_path is a forecast-only scenario axis "
            f"(rule 13): got {config.voluntary_clean_demand_path!r} in "
            f"mode={config.mode!r}, hindcast={config.hindcast!r}. A scored "
            "backcast / hindcast never carries voluntary demand (the ffr-5b "
            "null is preserved there)."
        )


def eligible_fuels(config: ScenarioConfig) -> tuple[str, ...]:
    """Return the voluntary row's qualifying fuel-name tuple, validated.

    ``voluntary_eligible_fuels`` when set (the labelled "carbon-free" override,
    owner box D-3c), else :data:`constants.VOLUNTARY_ELIGIBLE_FUELS_DEFAULT`
    (the memo §4.1 recommendation). Every name must be a ``FUEL_TYPE_MAP``
    fleet fuel type (the row builder hard-errors on an unknown name; this
    makes the error name the config field), and the tuple must carry both
    zone-column fuels (``__post_init__`` already refuses a list without them;
    re-checked here because the default tuple is data too).

    Raises:
        ValueError: An unknown fuel name, or wind / solar missing.
    """
    override = config.voluntary_eligible_fuels
    fuels = (
        tuple(str(f) for f in override)
        if override is not None
        else tuple(VOLUNTARY_ELIGIBLE_FUELS_DEFAULT)
    )
    unknown = sorted(f for f in fuels if f not in FUEL_TYPE_MAP)
    if unknown:
        raise ValueError(
            f"voluntary_eligible_fuels entries must be fleet fuel types "
            f"({sorted(FUEL_TYPE_MAP)}); got {unknown}"
        )
    for base in _ZONE_COLUMN_FUELS:
        if base not in fuels:
            raise ValueError(
                f"the voluntary eligible set must include {base!r}: the clean "
                "family's wind/solar zone columns always credit at 1.0, so an "
                "ineligible listing would be silently overridden."
            )
    return fuels


def wtp_ceiling(config: ScenarioConfig) -> float:
    """Return the buyer's willingness-to-pay ceiling in real $/MWh.

    ``voluntary_wtp_ceiling_usd_per_mwh`` when set (a labelled sensitivity),
    else :data:`constants.VOLUNTARY_WTP_CEILING_USD_PER_MWH` at the config's
    path. Only meaningful while the row is active (``__post_init__`` refuses
    an explicit ceiling with the path off — a dangling price with no row).
    """
    override = config.voluntary_wtp_ceiling_usd_per_mwh
    if override is not None:
        return float(override)
    return float(VOLUNTARY_WTP_CEILING_USD_PER_MWH[config.voluntary_clean_demand_path])


def baseline_share(config: ScenarioConfig, year: int) -> float:
    """Return ``s_base(path, y)`` — the voluntary share of non-DC load."""
    return _interp_edge_held(
        VOLUNTARY_BASELINE_SHARE[config.voluntary_clean_demand_path], year
    )


def committed_dc_fraction(config: ScenarioConfig, year: int) -> float:
    """Return ``f_commit(path, y)`` — the committed share of the DC block."""
    return _interp_edge_held(
        VOLUNTARY_COMMITTED_DC_FRACTION[config.voluntary_clean_demand_path], year
    )


def iso_baseline_weight(iso: str) -> float:
    """Return ``w_ISO`` — 1.0 wherever the EIA-861 basis is still needs-intake.

    :data:`constants.VOLUNTARY_BASELINE_ISO_WEIGHT` carries ``None`` for every
    ISO at this commit (the memo §3.2 commercial-sales basis is a public
    intake no SCN lane may write); ``None`` resolves to the national share
    applied to the ISO's own load — an allocation by total load share — the
    disclosed stand-in, never a silent zero. An ISO absent from the table is
    treated the same way (rule 25: nothing crosses an ISO boundary because
    nothing is fitted).
    """
    weight = VOLUNTARY_BASELINE_ISO_WEIGHT.get(iso.upper())
    return 1.0 if weight is None else float(weight)


def resolve_voluntary_volume(
    config: ScenarioConfig,
    iso: str,
    year: int,
    zone_names: list[str],
    zone_demand: np.ndarray,
) -> VoluntaryVolume:
    """Resolve ``V(ISO, y)`` from the run's own demand (memo §3.1).

    Args:
        config: Scenario config supplying the ``voluntary_*`` and DC levers.
        iso: ISO identifier (case-insensitive).
        year: Simulation year.
        zone_names: Model zone names in LP zone-index order.
        zone_demand: The ``(n_zones, T)`` demand the LP is handed for this
            year — AFTER ``add_load_layers`` — so ``E_DC`` and ``E_nonDC``
            partition exactly the energy the row's RHS is a fraction of.

    Returns:
        The resolved volume and its components.
    """
    demand = np.asarray(zone_demand, dtype=float)
    if demand.ndim != 2 or demand.shape[0] != len(zone_names):
        raise ValueError(
            "resolve_voluntary_volume: zone_demand must be (n_zones, T) aligned "
            f"with zone_names (got shape {demand.shape} for {len(zone_names)} zones)"
        )
    energy_total = float(demand.sum())
    energy_dc = datacenter_block_energy_mwh(
        config, iso.upper(), year, list(zone_names), demand.shape[1]
    )
    # The block is inside E_total in both DC regimes (relocated, or added on
    # top); the clamp only guards a synthetic demand smaller than the block.
    energy_non_dc = max(0.0, energy_total - energy_dc)
    share = baseline_share(config, year)
    weight = iso_baseline_weight(iso)
    frac_commit = committed_dc_fraction(config, year)
    volume = share * weight * energy_non_dc + frac_commit * energy_dc
    return VoluntaryVolume(
        path=config.voluntary_clean_demand_path,
        baseline_share=share,
        iso_weight=weight,
        committed_fraction=frac_commit,
        energy_total_mwh=energy_total,
        energy_dc_mwh=energy_dc,
        energy_non_dc_mwh=energy_non_dc,
        volume_mwh=float(volume),
    )


def voluntary_obligation_frac(volume_mwh: float, zone_demand: np.ndarray) -> np.ndarray:
    """Return the ``(n_zones,)`` obligation fraction expressing a VOLUME.

    The K-row builder computes ``rhs = obligation_frac @ zone_annual_demand``
    (``model.lp.rows._build_rps_region_rows``), so a volume ``V`` is expressed
    WITHOUT touching the builder as the uniform share ``V / E_total`` of every
    zone's annual demand: ``Σ_z (V / E_total) · D_z = V`` identically. The
    memo §3.1 writes the general ``frac[z] = V·ω_z / D_z`` with within-ISO
    weights ``ω_z``; under the row's ALL-ZONE mask the zone split of the RHS
    has no LP content (one ISO-wide constraint, one RHS sum), so the
    load-share weighting ``ω_z = D_z / E_total`` — the memo's own default
    for the baseline half — is used for both halves. A zone with zero demand
    (ERCOT ``Panhandle``, ``load_share`` 0.0) contributes 0 either way.

    Args:
        volume_mwh: ``V`` in MWh.
        zone_demand: The same ``(n_zones, T)`` demand the LP is handed.

    Returns:
        ``(n_zones,)`` float fractions; all zeros when the demand has no energy.
    """
    demand = np.asarray(zone_demand, dtype=float)
    energy_total = float(demand.sum())
    n_zones = demand.shape[0]
    if energy_total <= 0.0:
        return np.zeros(n_zones, dtype=float)
    return np.full(n_zones, float(volume_mwh) / energy_total, dtype=float)


def voluntary_region_spec(
    volume_mwh: float,
    zone_demand: np.ndarray,
    ceiling_usd_per_mwh: float,
    fuels: tuple[str, ...],
) -> dict:
    """Return the ``append_clean_region`` keyword arguments for a volume.

    The pure row-shape half of the construction, separated from the level
    resolution so the trivial-first LP tests can hand the family an explicit
    ``V`` and check the row's dual and escape semantics against the
    arithmetic (memo §5.2): all-zone mask, uniform obligation fraction,
    the WTP ceiling as the escape price, the eligible set as a name tuple.
    """
    demand = np.asarray(zone_demand, dtype=float)
    return dict(
        label=VOLUNTARY_REGION_LABEL,
        eligible_zone_mask=np.ones(demand.shape[0], dtype=bool),
        obligation_frac=voluntary_obligation_frac(volume_mwh, demand),
        acp_price=float(ceiling_usd_per_mwh),
        qualifying=tuple(fuels),
        fuel_credit=None,
    )


def append_voluntary_region(
    config: ScenarioConfig,
    iso: str,
    year: int,
    zone_names: list[str],
    arrays: CleanRegionArrays | None,
    zone_demand: np.ndarray | None,
) -> CleanRegionArrays | None:
    """Append the voluntary row to the clean-tier family for one ISO-year.

    The ONE composition point the family offers (SCN-WS2a §6 contract):
    the voluntary region is appended LAST, after MISO's state rows and the
    federal CES target row, so region order — the only thing that fixes
    dual order — is state → federal → voluntary. Returned UNCHANGED (the
    same object) whenever the row is off, so every existing family is
    byte-identical by construction; it is NOT suppressed by
    ``federal_ces_replaces_state_rps`` (the voluntary buyer is not a state
    row and exists under any federal policy — memo §5.1).

    Args:
        config: Scenario config supplying the ``voluntary_*`` fields.
        iso: ISO identifier.
        year: Simulation year.
        zone_names: Model zone names in LP zone-index order.
        arrays: The family so far (state and/or federal regions), or ``None``.
        zone_demand: The ``(n_zones, T)`` demand the LP is handed. Required
            when the row is active (the volume is a fraction of it); ignored
            otherwise.

    Returns:
        The family with the voluntary region appended, ``arrays`` itself when
        the row is off, or ``None`` when nothing exists.

    Raises:
        ValueError: The row is active but no demand was supplied.
    """
    if not voluntary_row_active(config):
        return arrays
    if zone_demand is None:
        raise ValueError(
            "append_voluntary_region: the voluntary row is active "
            f"(voluntary_clean_demand_path={config.voluntary_clean_demand_path!r}) "
            "but no zone_demand was supplied — the volume is a share of the "
            "demand the LP is handed and cannot be sized without it."
        )
    volume = resolve_voluntary_volume(config, iso, year, zone_names, zone_demand)
    ceiling = wtp_ceiling(config)
    fuels = eligible_fuels(config)
    logger.info(
        "%s %d: voluntary clean-demand row (%s): V=%.1f MWh = s_base %.4f x "
        "w_ISO %.3f x E_nonDC %.1f + f_commit %.3f x E_DC %.1f; WTP ceiling "
        "$%.2f/MWh; eligible %s",
        iso.upper(),
        year,
        volume.path,
        volume.volume_mwh,
        volume.baseline_share,
        volume.iso_weight,
        volume.energy_non_dc_mwh,
        volume.committed_fraction,
        volume.energy_dc_mwh,
        ceiling,
        fuels,
    )
    return append_clean_region(
        arrays,
        **voluntary_region_spec(volume.volume_mwh, zone_demand, ceiling, fuels),
    )


def build_voluntary_region(
    config: ScenarioConfig,
    iso: str,
    year: int,
    zone_names: list[str],
    zone_demand: np.ndarray | None,
) -> CleanRegionArrays | None:
    """Return the voluntary row standing alone (K=1), or ``None`` when off.

    :func:`append_voluntary_region` with no prior family — the posture of
    every ISO with neither a state clean tier nor a federal target row
    (ERCOT, the memo §6 probe ISO: the voluntary row is the ONLY attribute
    driver there).
    """
    return append_voluntary_region(config, iso, year, zone_names, None, zone_demand)

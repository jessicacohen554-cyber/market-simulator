"""Forward-admissible ERCOT West Texas Export corridor VRE curtailment-share driver.

The ERCOT 8-zone reduction collapses the West/Panhandle wind corridor's
chronically-binding **nodal** transmission (dozens of internal 138/345 kV lines
in the Permian / CREZ, below zonal resolution) into one wide West->North pipe
that almost never binds, so the LP dispatches West/Panhandle wind and solar well
above what ERCOT's real grid delivered (the C2 / [3e] under-curtailment gap;
docs/handoffs/ercot-vre-curtailment-topology-scope-2026-07.md, WP-B).

This module supplies the reduced-form stand-in for that missing sub-zonal
structure: a curtailment ceiling on the West and Panhandle zones' wind (and
solar) dispatch,

    ceiling_frac(t) = 1 - depth * congestion_share(net_load_decile(t),
                                                   hour_of_day(t), season(t))

applied as a multiplier on the CF upper bound. Two pieces, derived separately:

* ``congestion_share`` — the **SHAPE**: the measured fraction of SCED executions
  with the West Texas Export corridor congested, binned by within-year net-load
  percentile decile x hour-of-day x season. Read from the derived reference table
  (scripts/data/derive_ercot_wtx_curtailment_share.py -> data/raw/reference/
  ercot_wtx_curtailment_share.csv), itself built ONLY from measured NP6-86 SCED
  congestion incidence (data/clean/ercot-wtx-congestion) geo-attributed via the
  ERCOT SP/bus mapping — never the reported curtailment volume or a price
  residual. A function of the model's OWN net-load, so it regenerates forward
  (more West VRE -> deeper net-load troughs -> higher congestion share) and
  reproduces the measured binding-frequency distribution leave-one-year-out
  (rule #23 / the anti-residual gate).
* ``depth`` — the **LEVEL**: a single per-tech coefficient converting congestion
  incidence into curtailed fraction, ``ScenarioConfig.ercot_wtx_curtail_depth_
  wind`` / ``_solar``. Empirically a stable structural constant of the West Texas
  network (~0.097 for wind across 2023-2025, LOYO-validated); centred on the
  measured curtailment MW quantity like the RTOLCAP-forward ``deliv`` coefficient
  (docs/handoffs/ercot-as-coopt-plan-2026-07.md). ``depth = 0`` is the
  zero-forcing ablation (driver inert).

Consumed by the orchestrator (gated on
``ScenarioConfig.ercot_wtx_curtailment_driver``) which computes the model's own
net-load and passes the per-(zone, hour) multipliers to the LP renewable bounds.
Returns neutral (1.0) multipliers for every zone that is not West/Panhandle and
whenever the reference table or clean congestion series is absent, so a missing
input degrades to the static behaviour rather than failing the solve.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Net-load percentile bins — matches the RTOLCAP-forward decile axis granularity
# (scarcity._ercot_rtolcap_fwd_decile) so the two derived drivers share a driver
# axis convention.
NET_LOAD_N_DECILE = 10

# The model zones behind the West Texas Export interface — the corridor whose
# wind/solar the nodal congestion curtails (zone_assignment._ercot_zone).
WEST_CORRIDOR_ZONES = ("West", "Panhandle")

# Reference-table datatype and columns (data/raw/reference).
SHARE_TABLE_NAME = "ercot_wtx_curtailment_share.csv"
_SHARE_KEY = ["net_load_decile", "hour_of_day", "season"]

# --- unpooled diurnal-family products (ercot-165) ---------------------------
# The pooled table above is a UNION over every corridor element, so it saturates
# (2025 mean 0.64) and inherits the shape of whichever family carries the most
# binding weight — measured 0.70-0.77 overnight. Its hod shape is therefore
# ANTI-correlated with the mid-afternoon curtailment mode it exists to close
# (2025 gap-shape corr -0.67, worsening as solar grows; FINDING-ercot164 §3).
# The family table splits that union on the same (decile x hod x season) axis:
#   D       daytime / solar-flood elements (+ WESTEX, which its own measured
#           lift 1.074-1.216 puts in D every year)
#   N       the overnight / wind-export tail
#   PNHNDL  the Panhandle export GTC, held OUT of the split because its owner is
#           a mechanism choice, not a family.
FAMILY_SHARE_TABLE_NAME = "ercot_wtx_curtailment_share_family.csv"
FAMILY_LABELS = ("D", "N", "PNHNDL")
# Which zone carries which share once unpooled. West always takes the D+N sum
# (additive corridor pressure, NOT the saturating OR); the Panhandle zone's
# owner is the pre-registered A/B (FINDING-ercot164 §6.2):
#   "tie"    the endogenous Panhandle->North tie at measured PNHNDL limits is
#            the SOLE Panhandle mechanism — no driver ceiling there (rule 19).
#   "share"  a Panhandle-scoped ceiling shaped by the measured PNHNDL
#            enforcement incidence owns the SUB-LIMIT pressure; the tie keeps
#            only the network limit, so the two bind in different hours.
PANHANDLE_OWNERS = ("tie", "share")

# --- SPP (SPP-58) -----------------------------------------------------------
# SPP's own instance of the same structure, on SPP's own measured data. Rule 25
# [R-ISO-SCOPE]: NOTHING is transferred from ERCOT -- not the table, not the
# depth, not the corridor attribution. SPP's 2-zone reduction (SPP-North /
# SPP-South, one 3,400 MW link) collapses the SPS / Texas-Panhandle and western
# Kansas / Oklahoma export pockets that actually curtail its wind, so the LP
# takes essentially the whole grossed-up bound: measured on the keeper
# 2026-09-09-spp-52a-fossil-offer's committed hourly sidecars, re-curtailment is
# 0.26 / 0.22 / 0.17 % in 2023 / 2024 / 2025 against the 9.65 % reference rate
# the gross-up itself applies -- a 40-60x miss on the construction's own stated
# precondition ("real headroom, endogenously re-curtailed").
#
# The share table is derived by scripts/data/derive_spp_curtailment_share.py
# from SPP's published RTBM binding-constraint archive
# (data/raw/spp-binding-constraints), binned on the SAME (net-load decile x
# hour-of-day x season) axis as ERCOT's so both consumers bin identically. It
# carries the MEAN COUNT of simultaneously binding constraints, rescaled onto
# (0, 1] -- not a fraction of congested intervals, which saturates in SPP
# (91.0 % of 2024's 5-minute intervals carry at least one binding constraint)
# and would encode no shape at all.
SPP_SHARE_TABLE_NAME = "spp_curtailment_share.csv"

# Both SPP model zones carry the ceiling. Unlike ERCOT -- where the corridor is
# two named zones out of eight -- SPP's reduction has no corridor zone to
# attribute to: the derived incidence is footprint-wide, so scoping it to one
# zone would be an attribution the data does not support.
SPP_CEILING_ZONES = ("SPP-North", "SPP-South")


def net_load_decile(net_load: np.ndarray) -> np.ndarray:
    """Within-year net-load percentile bin (0..NET_LOAD_N_DECILE-1) per hour.

    Ranks the year's net-load into equal-count bins. A forecast year ranks its
    OWN net-load, so the mapping regenerates and a changed VRE build shifts which
    hours fall in which bin (rule #10). Vectorized; no per-hour Python loop.
    """
    nl = np.asarray(net_load, dtype=float)
    n = len(nl)
    order = np.argsort(np.argsort(nl))  # ascending rank per hour
    return np.minimum(
        (order * NET_LOAD_N_DECILE) // max(n, 1), NET_LOAD_N_DECILE - 1
    ).astype("int64")


def hour_axes(n_hours: int) -> tuple[np.ndarray, np.ndarray]:
    """Return ``(hour_of_day, season)`` arrays for the non-leap model clock.

    ``season`` is 0=DJF (winter), 1=MAM (spring), 2=JJA (summer), 3=SON (fall) —
    ``(month % 12) // 3`` on the fixed 2023 non-leap calendar template.
    """
    cal = pd.date_range("2023-01-01", periods=8760, freq="h")
    hod = cal.hour.to_numpy()[:n_hours]
    season = ((cal.month.to_numpy() % 12) // 3)[:n_hours]
    return hod.astype("int64"), season.astype("int64")


def load_share_table(reference_dir) -> pd.DataFrame | None:
    """Load the derived congestion-share table, or ``None`` when absent.

    ``reference_dir`` is ``paths.RAW_DIR / "reference"``. Returns a frame keyed by
    ``(net_load_decile, hour_of_day, season)`` carrying ``congestion_share`` in
    [0,1]; ``None`` (with a log line) when the derived CSV has not been generated.
    """
    from pathlib import Path

    path = Path(reference_dir) / SHARE_TABLE_NAME
    if not path.is_file():
        logger.info(
            "ercot-wtx-curtailment: no share table at %s "
            "(run scripts/data/derive_ercot_wtx_curtailment_share.py) — driver inert",
            path,
        )
        return None
    return pd.read_csv(path)


def _share_lookup(table: pd.DataFrame, net_load: np.ndarray) -> np.ndarray:
    """Map each hour to its congestion share via (decile, hour-of-day, season)."""
    n = len(net_load)
    dec = net_load_decile(net_load)
    hod, season = hour_axes(n)
    key = pd.DataFrame({"net_load_decile": dec, "hour_of_day": hod, "season": season})
    merged = key.merge(table, on=_SHARE_KEY, how="left")
    share = merged["congestion_share"].to_numpy(dtype=float)
    # An unseen (decile, hour, season) cell (sparse in a short derive) falls back
    # to 0 congestion — never a fabricated value.
    return np.nan_to_num(share, nan=0.0)


def forecast_wtx_curtail_multipliers(
    config,
    iso: str,
    year: int,
    demand: np.ndarray,
    wind_cf: np.ndarray,
    wind_cap: np.ndarray,
    solar_cf: np.ndarray,
    solar_cap: np.ndarray,
    zone_names: list[str],
) -> tuple[np.ndarray, np.ndarray] | None:
    """Forecast-mode gate for the WP-B corridor ceiling, or ``None`` when off.

    The forecast leg of the driver (runner.py's per-year dispatch assembly;
    the backcast leg lives in ``scripts/run_calibration.py``, guarded there on
    a measured-HSL year instead). Fires only for ERCOT with
    ``ScenarioConfig.ercot_wtx_curtailment_driver`` enabled in forecast mode;
    the renewable bound is then the *uncurtailed* potential basis
    (``load_renewable_profiles`` grosses the delivered EIA-930 profile up by
    the reference curtailment rate under the same gate), so the ceiling never
    double-counts a curtailment already embedded in the bound.

    ``net_load`` is computed from the FORECAST state — the year's scaled
    demand minus the year's evolved wind/solar *potential* (same LP-served
    convention as the backcast gate) — so the decile mapping regenerates each
    forecast year: a bigger West VRE build deepens the net-load troughs and
    re-composes which (hour, season) cells carry the high-congestion deciles
    (rule #10, forward admissibility). Two documented ASSUMPTIONS bound what
    that regeneration captures (handoff §8, owner-accepted framing): the
    within-year percentile axis normalizes away the absolute year-over-year
    congestion rise (depth at deep penetration is conservative), and the
    share/depth encode the 2023–25 West-corridor network topology (future
    Permian/CREZ transmission builds would ease it; the driver does not
    auto-relax).

    Parameters mirror the runner's per-year state; ``demand`` is the
    ``(n_zones, T)`` year demand and the CF/cap pairs the evolved fleet's
    potential basis. Returns ``(wind_mult, solar_mult)`` each ``(n_zones, T)``
    or ``None`` (gate closed / share table absent) — the caller then leaves
    the static bound untouched.
    """
    if iso != "ERCOT" or not getattr(config, "ercot_wtx_curtailment_driver", False):
        return None
    if getattr(config, "mode", "forecast") != "forecast":
        return None
    from market_sim.config import paths as _paths

    net_load = (
        np.asarray(demand, dtype=float).sum(axis=0)
        - (np.asarray(wind_cap, dtype=float)[:, None] * wind_cf).sum(axis=0)
        - (np.asarray(solar_cap, dtype=float)[:, None] * solar_cf).sum(axis=0)
    )
    depth_wind = float(getattr(config, "ercot_wtx_curtail_depth_wind", 0.0))
    depth_solar = float(getattr(config, "ercot_wtx_curtail_depth_solar", 0.0))
    # ercot-165: the UNPOOLED diurnal-family variant. Forward-admissible on the
    # same terms as the pooled share — the family tables live on the model's own
    # net-load decile x hod x season axis and family membership re-derives
    # whenever a new NP6-86 year lands (rule 13 / rule 23).
    if bool(getattr(config, "ercot_wtx_curtail_unpooled", False)):
        mult = wtx_family_curtail_multipliers(
            net_load,
            list(zone_names),
            depth_wind=depth_wind,
            depth_solar=depth_solar,
            panhandle_owner=str(getattr(config, "ercot_wtx_panhandle_owner", "tie")),
            reference_dir=_paths.RAW_DIR / "reference",
        )
    else:
        mult = wtx_curtail_multipliers(
            net_load,
            list(zone_names),
            depth_wind=depth_wind,
            depth_solar=depth_solar,
            reference_dir=_paths.RAW_DIR / "reference",
        )
    if mult is not None:
        logger.info(
            "ercot_wtx_curtailment_driver: %d forecast West/Panhandle VRE "
            "ceiling active (depth wind=%.4f solar=%.4f)",
            year,
            depth_wind,
            depth_solar,
        )
    return mult


def load_family_share_table(reference_dir) -> pd.DataFrame | None:
    """Load the derived per-family congestion-share table, or ``None`` when absent.

    ``reference_dir`` is ``paths.RAW_DIR / "reference"``. Returns a long-format
    frame keyed by ``(family, net_load_decile, hour_of_day, season)`` carrying
    ``congestion_share`` in [0,1]; ``None`` (with a log line) when the derived
    CSV has not been generated, so the caller degrades to the static bound
    rather than failing the solve.
    """
    from pathlib import Path

    path = Path(reference_dir) / FAMILY_SHARE_TABLE_NAME
    if not path.is_file():
        logger.info(
            "ercot-wtx-curtailment: no family share table at %s (run "
            "scripts/data/derive_ercot_wtx_curtailment_share.py --family) — "
            "unpooled driver inert",
            path,
        )
        return None
    return pd.read_csv(path)


def family_share_lookup(
    table: pd.DataFrame, net_load: np.ndarray
) -> dict[str, np.ndarray]:
    """Map each hour to every family's congestion share.

    Returns ``{family: (T,) share}`` for each label in :data:`FAMILY_LABELS`; a
    family absent from the table (or an unseen (decile, hour, season) cell,
    sparse in a short derive) falls back to 0 congestion — never a fabricated
    value, the same convention as the pooled lookup.
    """
    n = len(net_load)
    dec = net_load_decile(net_load)
    hod, season = hour_axes(n)
    key = pd.DataFrame({"net_load_decile": dec, "hour_of_day": hod, "season": season})
    out: dict[str, np.ndarray] = {}
    for fam in FAMILY_LABELS:
        sub = table[table["family"] == fam]
        if sub.empty:
            out[fam] = np.zeros(n, dtype=float)
            continue
        merged = key.merge(
            sub[_SHARE_KEY + ["congestion_share"]], on=_SHARE_KEY, how="left"
        )
        out[fam] = np.nan_to_num(
            merged["congestion_share"].to_numpy(dtype=float), nan=0.0
        )
    return out


def corridor_zone_shares(
    family_share: dict[str, np.ndarray], panhandle_owner: str
) -> dict[str, np.ndarray]:
    """Per-corridor-zone congestion share from the unpooled family shares.

    THE single binning authority for the unpooled driver: both the solve-time
    consumer and the derive script's depth identification call this, so the
    level coefficient is centred on exactly the pressure the LP applies.

    The West zone takes ``D + N`` — the ADDITIVE corridor pressure, not the
    saturating OR the pooled table takes. Saturation is precisely what made the
    pooled union inherit the overnight family's shape (its mean reaches 0.64 in
    2025, so a daytime element binding adds nothing to the union); summing the
    two family unions keeps each family's own measured incidence visible.

    ``panhandle_owner`` selects the pre-registered A/B arm — see
    :data:`PANHANDLE_OWNERS`. Raises ``ValueError`` on an unknown owner rather
    than silently defaulting (rule 24: no off-registry fallback literals).
    """
    if panhandle_owner not in PANHANDLE_OWNERS:
        raise ValueError(
            f"unknown panhandle_owner {panhandle_owner!r}; "
            f"expected one of {PANHANDLE_OWNERS}"
        )
    n = len(next(iter(family_share.values())))
    west = np.asarray(family_share["D"], dtype=float) + np.asarray(
        family_share["N"], dtype=float
    )
    panhandle = (
        np.asarray(family_share["PNHNDL"], dtype=float)
        if panhandle_owner == "share"
        else np.zeros(n, dtype=float)
    )
    return {"West": np.clip(west, 0.0, 1.0), "Panhandle": np.clip(panhandle, 0.0, 1.0)}


def wtx_family_curtail_multipliers(
    net_load: np.ndarray,
    zone_names: list[str],
    *,
    depth_wind: float,
    depth_solar: float,
    panhandle_owner: str,
    reference_dir,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Unpooled per-(zone, hour) curtailment ceiling multipliers (ercot-165).

    The unpooled analogue of :func:`wtx_curtail_multipliers`: instead of
    broadcasting ONE pooled share identically to West and Panhandle, each
    corridor zone gets the share :func:`corridor_zone_shares` assigns it, so the
    Panhandle interface has exactly one owner (rule 19 [R-ONE-MECH]) and the
    West zone's pressure no longer carries the mis-broadcast PNHNDL component.

    Parameters
    ----------
    net_load:
        The model's own system net-load ``(T,)`` (demand - wind_pot - solar_pot).
    zone_names:
        Ordered model zone names; only West/Panhandle rows get a ceiling.
    depth_wind, depth_solar:
        The per-tech level coefficients (ScenarioConfig) — still exactly TWO
        free scalars, re-identified against the unpooled shares. ``0`` -> inert.
    panhandle_owner:
        ``"tie"`` or ``"share"`` (:data:`PANHANDLE_OWNERS`).
    reference_dir:
        ``paths.RAW_DIR / "reference"``.

    Returns
    -------
    ``(wind_mult, solar_mult)`` each ``(n_zones, T)`` in (0,1], or ``None`` when
    the family table is absent (caller keeps the static uncurtailed bound).
    """
    table = load_family_share_table(reference_dir)
    if table is None:
        return None
    nl = np.asarray(net_load, dtype=float)
    T = len(nl)
    n_zones = len(zone_names)
    zone_share = corridor_zone_shares(family_share_lookup(table, nl), panhandle_owner)

    wind_mult = np.ones((n_zones, T), dtype=float)
    solar_mult = np.ones((n_zones, T), dtype=float)
    for i, z in enumerate(zone_names):
        share = zone_share.get(z)
        if share is None:
            continue
        wind_mult[i, :] = np.clip(1.0 - float(depth_wind) * share, 0.0, 1.0)
        solar_mult[i, :] = np.clip(1.0 - float(depth_solar) * share, 0.0, 1.0)
    return wind_mult, solar_mult


def wtx_curtail_multipliers(
    net_load: np.ndarray,
    zone_names: list[str],
    *,
    depth_wind: float,
    depth_solar: float,
    reference_dir,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Per-(zone, hour) curtailment ceiling multipliers for wind and solar.

    Parameters
    ----------
    net_load:
        The model's own system net-load ``(T,)`` (demand - wind_pot - solar_pot).
    zone_names:
        Ordered model zone names; the West/Panhandle rows get the ceiling, all
        others stay 1.0.
    depth_wind, depth_solar:
        The per-tech level coefficients (ScenarioConfig). ``0`` -> inert.
    reference_dir:
        ``paths.RAW_DIR / "reference"`` (where the derived share table lives).

    Returns
    -------
    (wind_mult, solar_mult) each ``(n_zones, T)`` in (0,1], or ``None`` when the
    share table is absent (caller keeps the static uncurtailed bound).
    """
    table = load_share_table(reference_dir)
    if table is None:
        return None
    nl = np.asarray(net_load, dtype=float)
    T = len(nl)
    n_zones = len(zone_names)
    share = _share_lookup(table, nl)  # (T,)

    wind_mult = np.ones((n_zones, T), dtype=float)
    solar_mult = np.ones((n_zones, T), dtype=float)
    corridor = [i for i, z in enumerate(zone_names) if z in WEST_CORRIDOR_ZONES]
    if not corridor:
        return wind_mult, solar_mult
    wind_row = np.clip(1.0 - float(depth_wind) * share, 0.0, 1.0)
    solar_row = np.clip(1.0 - float(depth_solar) * share, 0.0, 1.0)
    for i in corridor:
        wind_mult[i, :] = wind_row
        solar_mult[i, :] = solar_row
    return wind_mult, solar_mult


def load_spp_share_table(reference_dir) -> pd.DataFrame | None:
    """Load SPP's derived congestion-share table, or ``None`` when absent.

    ``reference_dir`` is ``paths.RAW_DIR / "reference"``. Returns a frame keyed
    by ``(net_load_decile, hour_of_day, season)`` carrying ``congestion_share``
    in ``(0, 1]``; ``None`` (with a log line) when
    ``scripts/data/derive_spp_curtailment_share.py`` has not been run, so a
    missing input degrades to the static bound rather than failing the solve.
    """
    from pathlib import Path

    path = Path(reference_dir) / SPP_SHARE_TABLE_NAME
    if not path.is_file():
        logger.info(
            "spp-curtailment: no share table at %s "
            "(run scripts/data/derive_spp_curtailment_share.py) — ceiling inert",
            path,
        )
        return None
    return pd.read_csv(path)


def spp_curtail_multipliers(
    net_load: np.ndarray,
    zone_names: list[str],
    *,
    depth_wind: float,
    reference_dir,
) -> tuple[np.ndarray, np.ndarray] | None:
    """Per-(zone, hour) wind curtailment-ceiling multipliers for SPP (SPP-58).

    ``ceiling_frac(t) = 1 - depth_wind * congestion_share(t)``, with
    ``congestion_share`` read off SPP's own derived binding-incidence table on
    the model's OWN net-load decile x hour-of-day x season axis — so the
    mapping regenerates for a forward year (more wind -> deeper net-load
    troughs -> the high-incidence deciles re-compose) and responds to changed
    conditions, which is what rule 13 ``[R-MEASURED]``'s forward test asks.

    SOLAR IS NOT CEILINGED. SPP's solar bound is ``delivered_pinned``
    (``renewable_bound_provenance``) — it carries no gross-up headroom — so a
    solar ceiling would curtail energy the market actually delivered rather
    than headroom the model invented. The published curtailment series the
    depth is centred on is wind-only for 2023/2024 in any case (the 2025
    edition's total-VER basis puts solar at 0.73 % of curtailments). The solar
    multiplier is returned as an explicit ``1.0`` array rather than ``None`` so
    the caller's two-array contract is unchanged.

    Parameters
    ----------
    net_load:
        The model's own system net load ``(T,)`` (demand - wind potential -
        solar potential), summed over zones.
    zone_names:
        Ordered model zone names. Both SPP zones take the ceiling
        (:data:`SPP_CEILING_ZONES`); anything else stays 1.0.
    depth_wind:
        The level coefficient (``ScenarioConfig.spp_curtail_depth_wind``),
        centred on SPP's published measured curtailment MW. ``0`` -> inert.
    reference_dir:
        ``paths.RAW_DIR / "reference"`` (where the derived table lives).

    Returns
    -------
    ``(wind_mult, solar_mult)`` each ``(n_zones, T)`` in ``(0, 1]``, or ``None``
    when the share table is absent (the caller then keeps the static bound).
    """
    table = load_spp_share_table(reference_dir)
    if table is None:
        return None
    nl = np.asarray(net_load, dtype=float)
    n_hours = len(nl)
    n_zones = len(zone_names)
    share = _share_lookup(table, nl)  # (T,)

    wind_mult = np.ones((n_zones, n_hours), dtype=float)
    solar_mult = np.ones((n_zones, n_hours), dtype=float)
    ceiling_rows = [i for i, z in enumerate(zone_names) if z in SPP_CEILING_ZONES]
    if not ceiling_rows:
        return wind_mult, solar_mult
    wind_row = np.clip(1.0 - float(depth_wind) * share, 0.0, 1.0)
    for i in ceiling_rows:
        wind_mult[i, :] = wind_row
    return wind_mult, solar_mult

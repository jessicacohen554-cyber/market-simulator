"""PJM Day-Ahead virtual-bid layer (G-22 lever B — DA procurement depth).

The real PJM Day-Ahead market clears more volume at peaks than the physical
load the model serves: submitted DECrement bids (virtual demand) net of
INCrement offers (virtual supply) deepen the DA procurement by ~7-11 GW at
the top summer-load hours (measured July-2024; the ~9-10 GW gap of
docs/FINDING-pjm-offer-surface-noop-2026-07.md). Because the backcast is
scored against DA clearing prices, the DA demand side is real market
structure the LP must carry (CLAUDE.md rule 1) — without it the energy
dual is read ~9-10 GW too shallow into the offer stack at the peaks.

Mechanism (``ScenarioConfig.pjm_da_virtual_bids``, PJM-gated, default off)
--------------------------------------------------------------------------
The measured HOURLY submitted INC/DEC bid curves (PJM DataMiner2
``hrl_da_incs_decs``, ``data/raw/pjm-da-virtuals/``,
``scripts/fetch_pjm_da_virtuals.py``) enter the LP as a **single per-hour
NET virtual-demand curve** — the financial net of submitted demand and
supply:

    net_demand(λ) = Σ_{DEC bids ≥ λ} MW − Σ_{INC offers ≤ λ} MW

represented ENTIRELY as export-sink-form DEC withdrawal blocks (``pmax = 0``,
dispatch in ``[-MW(t), 0]`` via an hourly ``min_gen`` lower bound). A block
priced at ``b`` withdraws power — adds DA demand — whenever the zonal dual is
below ``b`` (withdrawing at a positive price lowers the LP objective), so the
aggregate cleared withdrawal reproduces the net-demand curve with **endogenous
clearing**: the dual finds where the model's own stack crosses
``load + net_demand(λ)``.

Why NET, and why DEC-form only (the pjm-101 → pjm-102 fix,
docs/FINDING-pjm-da-depth-midcurve-2026-07.md §5). An INC is a *financial*
position; it deepens the DA price stack but never produces physical MWh. The
earlier separate-INC-supply construction injected the INC MW as physical
zero-cost generation (fuel-type ``import``), which displaced real peaker
dispatch in the energy balance (C1 CT_PEAKER −12/−13 TWh). Netting INC into
the demand curve keeps the identical depth-on-price effect — the net at peaks
is +7-11 GW, almost all DEC — while injecting no supply into the physical mix.

Construction. Per hour, each submitted price point ``p`` contributes a
combined block of ``dec_p + inc_p`` MW at price ``p``: crossing ``λ`` upward
through ``p`` removes ``dec_p`` of demand AND adds ``inc_p`` of supply, so net
demand drops by exactly ``dec_p + inc_p`` there. Keeping the lowest-priced
``Σ dec`` MW of these combined blocks (a partial block at the crossing)
reproduces the net-demand curve over its ``net ≥ 0`` range; the higher-priced
remainder is the INC-dominated net-negative (off-peak) tail, **clamped to
zero** — conservative, no supply injected. The kept mass is compressed to
``N_RUNGS`` equal-MW DEC rungs, each priced at the MW-weighted quantile of its
cumulative-share midpoint. Rung MW is spread across the ISO's load zones by
each hour's zonal demand share (virtual bids clear at pnodes across the whole
footprint).

Admissibility (CLAUDE.md rule 13)
---------------------------------
The curves are SUBMITTED ex-ante participant inputs — the demand-side
mirror of generator energy offers, the same measured-input class as
delivered fuel prices and CAMPD outage windows (same-year measured inputs
admissible in backcast). Cleared virtual volume and the clearing price are
both LP OUTPUTS: the dual finds where the model's own stack crosses
``load + net_demand(λ)``. Nothing is pinned to a measured outcome, and
clearing prices stay validation-only.

Forecast substitute: the frozen condition-binned surface
``data/raw/_validation-source/pjm_da_virtual_surface_condbinned.json``
(``scripts/derive_pjm_da_virtual_surface.py`` — net-load-percentile bins,
load-fraction MW, implied-heat-rate prices; all forward-native axes that
regenerate hourly curves from a forecast year's own load/VRE/gas drivers).
The forecast-path wiring is not built yet — this flag lives in the
backcast calibration path only, like the other measured overlays.
"""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config import paths
from market_sim.data.fleet import Generator

logger = logging.getLogger(__name__)

#: plant_group carried by the virtual pseudo-units. Not a physical class:
#: no bench class matches it (class metrics ignore the units) and the units
#: are reserve-ineligible (fuel_type "import" is outside RESERVE_FUEL_TYPES).
#: Every rung is a DEC-form NET-demand withdrawal block (no supply side).
VIRTUAL_DEC_GROUP = "VIRTUAL_DEC"

#: Equal-MW rungs the hourly net-demand curve is compressed to. Resolution /
#: LP-columns trade-off only (rung prices/MW are the measured curve's own
#: weighted quantiles, not tunable values).
N_RUNGS = 8

#: DEC bids are capped at this fraction of VOLL so a virtual bid can never
#: outbid load shedding (PJM's $2,000/MWh hard cap sits far below VOLL, so
#: this guard is a structural no-op on the measured data).
DEC_VOLL_CAP_FRAC = 0.95


def _raw_dir() -> Path:
    return paths.PJM_DA_VIRTUALS_DIR


def _hour_index_map(iso: str, year: int, hours: int) -> pd.DataFrame:
    """(day, hour-ending) -> model-clock hour index, from the EIA-930 frame.

    The model's 8760 clock is the EIA-930 local frame's row order; joining
    on (local day, hour-ending) mirrors the derive-side convention
    (``derive_pjm_offer_surface._netload_pct``). DST fall-back repeats a
    (day, he) pair — the join keeps the first model hour, and the repeated
    EPT hour's bids average into it upstream.
    """
    from market_sim.data.eia_loader import _eia_hourly_frame_filled

    df = _eia_hourly_frame_filled(iso, year)
    if df is None:
        raise FileNotFoundError(f"EIA-930 {iso} {year}: no clean 8760 frame")
    local = pd.DatetimeIndex(df["Local time"])[:hours]
    out = pd.DataFrame(
        {"day": local.normalize(), "he": local.hour + 1, "t": np.arange(len(local))}
    )
    return out.drop_duplicates(["day", "he"], keep="first")


def _hourly_net_rungs(
    bids: pd.DataFrame, hours: int, n_rungs: int
) -> tuple[np.ndarray, np.ndarray]:
    """Compress each hour's NET virtual-demand curve to equal-MW DEC rungs.

    ``net_demand(λ) = Σ_{DEC bids ≥ λ} MW − Σ_{INC offers ≤ λ} MW`` — the
    financial net of the submitted virtual demand and supply. Each price
    point ``p`` contributes a combined block of ``dec_p + inc_p`` MW at
    price ``p`` (crossing ``λ`` upward through ``p`` drops net demand by both
    the demand that stops buying and the supply that starts selling). The
    lowest-priced ``Σ dec`` MW of these blocks is the ``net ≥ 0`` region; the
    higher-priced remainder is the INC-dominated net-negative tail, clamped to
    zero (no supply injected). Returns ``(mw, price)`` of shape
    ``(n_rungs, hours)``: the kept mass split into ``n_rungs`` equal-MW
    DEC-form withdrawal rungs, each priced at the MW-weighted quantile of its
    cumulative-share midpoint. Hours with no net demand stay zero.
    """
    mw = np.zeros((n_rungs, hours))
    price = np.zeros((n_rungs, hours))
    qs = (np.arange(n_rungs) + 0.5) / n_rungs  # cumulative-MW midpoints
    sub = bids[(bids["inc"] > 0.0) | (bids["dec"] > 0.0)]
    for t, g in sub.groupby("t", sort=False):
        p = g["price"].to_numpy(dtype=float)
        dec = g["dec"].to_numpy(dtype=float)
        block = dec + g["inc"].to_numpy(dtype=float)  # net-demand drop at price p
        total_dec = dec.sum()
        if total_dec < 1.0:
            continue  # no virtual demand this hour: nothing withdraws
        order = np.argsort(p)  # ascending price (lowest willingness first)
        p, block = p[order], block[order]
        # Keep the lowest-priced total_dec MW of combined blocks (net >= 0);
        # the higher-priced remainder is the INC-dominated net-negative tail.
        # kept[j] is this price point's mass inside the [0, total_dec] window,
        # partial at the crossing.
        prior = np.cumsum(block) - block  # combined MW strictly below price p
        keep = np.clip(total_dec - prior, 0.0, block)
        keep_total = keep.sum()  # == total_dec (Σ block >= total_dec always)
        if keep_total < 1.0:
            continue
        pos = keep > 0.0  # drop zero-mass points for interp stability
        # MW-weighted cumulative-share midpoints of the kept demand curve.
        ck = (np.cumsum(keep) - 0.5 * keep)[pos]
        price[:, t] = np.interp(qs * keep_total, ck, p[pos])
        mw[:, t] = keep_total / n_rungs
    return mw, price


def _load_bids_frame(iso: str, year: int, hours: int) -> pd.DataFrame | None:
    """Measured submitted INC/DEC bids for one backcast year, on the model clock.

    Reads the year's monthly ``hrl_da_incs_decs`` parquets and returns a long
    frame ``t, price, inc, dec`` (one row per model hour × submitted price
    point), or ``None`` when the raw corpus is absent (the caller degrades to
    a hard error under the flag — a silent no-op would fake the mechanism).
    """
    files = sorted(_raw_dir().glob(f"hrl_da_incs_decs_{year:04d}_*.parquet"))
    if not files:
        return None
    missing = sorted(
        {f"{m:02d}" for m in range(1, 13)} - {p.stem.rpartition("_")[2] for p in files}
    )
    if missing:
        raise FileNotFoundError(
            f"pjm_da_virtual_bids: {year} raw virtual-bid month(s) {missing} "
            "missing — run scripts/fetch_pjm_da_virtuals.py"
        )
    hmap = _hour_index_map(iso, year, hours)
    parts = []
    for p in files:
        df = pd.read_parquet(
            p, columns=["bid_datetime_beginning_ept", "price_point", "inc_mw", "dec_mw"]
        )
        ts = pd.to_datetime(
            df["bid_datetime_beginning_ept"], format="%m/%d/%Y %I:%M:%S %p", cache=True
        )
        parts.append(
            pd.DataFrame(
                {
                    "day": ts.dt.normalize().to_numpy(),
                    "he": (ts.dt.hour + 1).astype("int16").to_numpy(),
                    "price": df["price_point"].to_numpy(dtype="float64"),
                    "inc": df["inc_mw"].to_numpy(dtype="float64"),
                    "dec": df["dec_mw"].to_numpy(dtype="float64"),
                }
            )
        )
    bids = pd.concat(parts, ignore_index=True)
    # DST fall-back: both EPT occurrences of the repeated (day, he) land on
    # the same model hour — average them so the hour carries one curve.
    bids = bids.groupby(["day", "he", "price"], as_index=False).agg(
        inc=("inc", "mean"), dec=("dec", "mean")
    )
    return bids.merge(hmap, on=["day", "he"], how="inner")


def load_hourly_net_virtual_curve(
    iso: str, year: int, hours: int, n_rungs: int = N_RUNGS
) -> tuple[np.ndarray, np.ndarray] | None:
    """Measured hourly NET virtual-demand DEC-rung ladder for one backcast year.

    Returns ``(mw, price)`` with ``(n_rungs, hours)`` arrays on the model
    clock — the equal-MW DEC-form withdrawal rungs of the per-hour
    ``Σ DEC≥λ − Σ INC≤λ`` net-demand curve (positive part) — or ``None`` when
    the raw corpus is absent.
    """
    bids = _load_bids_frame(iso, year, hours)
    if bids is None:
        return None
    return _hourly_net_rungs(bids, hours, n_rungs)


def build_pjm_da_virtual_units(
    config,
    iso: str,
    year: int,
    demand: np.ndarray,
    zone_names: list[str],
) -> tuple[list[Generator], dict[str, np.ndarray], dict[str, np.ndarray]]:
    """Build the PJM net-virtual-demand pseudo-units, MW profiles and price rows.

    Args:
        config: ScenarioConfig; gates on ``pjm_da_virtual_bids``.
        iso: ISO id; the mechanism is PJM-only.
        year: backcast year whose measured hourly curves are read.
        demand: ``(n_zones, T)`` zonal demand MW (physical, pre-virtual).
        zone_names: zone order matching ``demand`` rows.

    Returns:
        ``(units, profiles, price_rows)``: DEC-form withdrawal pseudo-generators
        to append to the fleet (all ``pmax = 0``; the hourly net-demand curve —
        no supply side), a ``unit_id -> (T,) MW`` bound-profile map (DEC lower
        bounds via ``min_gen``; apply with :func:`apply_virtual_profiles`), and
        a ``unit_id -> (T,)`` $/MWh bid-price map for the units' ``fuel_prices``
        rows (``heat_rate`` is 1.0; apply with :func:`apply_virtual_bid_prices`).
    """
    if iso != "PJM" or not getattr(config, "pjm_da_virtual_bids", False):
        return [], {}, {}

    load = np.asarray(demand, dtype=float)  # (n_zones, T)
    T = load.shape[1]
    curve = load_hourly_net_virtual_curve(iso, year, T)
    if curve is None:
        raise FileNotFoundError(
            "pjm_da_virtual_bids is on but data/raw/pjm-da-virtuals/ has no "
            f"hrl_da_incs_decs_{year}_* parquets — run "
            "scripts/fetch_pjm_da_virtuals.py (the mechanism never silently "
            "no-ops)"
        )

    sys_load = load.sum(axis=0)
    zone_share = load / np.maximum(sys_load[None, :], 1.0)  # (n_zones, T)
    voll_cap = DEC_VOLL_CAP_FRAC * float(getattr(config, "voll", 5000.0))

    units: list[Generator] = []
    profiles: dict[str, np.ndarray] = {}
    price_rows: dict[str, np.ndarray] = {}
    mw, price = curve  # (N_RUNGS, T)
    # A DEC bid can never outbid load shedding (no-op on measured data: PJM's
    # $2,000 hard cap << 0.95 x VOLL).
    price = np.minimum(price, voll_cap)
    for r in range(mw.shape[0]):
        mw_zt = mw[r][None, :] * zone_share  # (n_zones, T)
        for zi, zone in enumerate(zone_names):
            mw_z = mw_zt[zi]
            peak = float(mw_z.max())
            if peak < 0.5:  # sub-MW everywhere: skip the column
                continue
            uid = f"{zone}_vNET_R{r:02d}"
            units.append(
                Generator(
                    unit_id=uid,
                    name=f"PJM DA net-virtual-demand rung {r} ({zone})",
                    zone=zone,
                    fuel_type="import",  # reserve-ineligible, zero-emission
                    pmax_mw=0.0,  # DEC-form withdrawal: dispatch in [-MW(t), 0]
                    pmin_mw=-peak,
                    heat_rate=1.0,  # mc rides the fuel_prices row ($/MWh)
                    vom=0.0,
                    eford=0.0,
                    plant_group=VIRTUAL_DEC_GROUP,
                    bin_label=f"NET_R{r:02d}",
                )
            )
            profiles[uid] = mw_z
            price_rows[uid] = price[r]
    logger.info(
        "PJM %d DA net-virtual-demand layer: %d DEC-form pseudo-units "
        "(%d rungs, measured hourly curves; net = Σ DEC≥λ − Σ INC≤λ, "
        "net-negative tail clamped to zero — no supply injected)",
        year,
        len(units),
        N_RUNGS,
    )
    return units, profiles, price_rows


def apply_virtual_profiles(fleet_arrays, profiles: dict[str, np.ndarray]) -> int:
    """Post-fleet-arrays hourly MW bounds for the virtual pseudo-units.

    The net-demand rungs are DEC-form: hourly lower bound rides ``min_gen``
    (seeded from pmin for every generator if absent — the export-sink-safe
    convention of the fleet floor appliers), set to ``-MW(t)``; their ``pmax``
    is 0 so the dispatch range is ``[-MW(t), 0]``. DEC rows carry no mechanism
    id: a negative lower bound is withdrawal capacity, not a commitment floor
    (D-2 attribution only tracks ``min_gen > 0``). An INC upper-bound branch
    (``availability``) is retained for any positive-``pmax`` profile, but the
    net-demand mechanism emits none.

    Returns the number of unit rows bound.
    """
    if not profiles:
        return 0
    uids = np.asarray(fleet_arrays.unit_ids, dtype=object)
    hours = int(fleet_arrays.availability.shape[1])
    n = 0
    # min_gen is only needed for DEC rows (pmax == 0): don't materialize the
    # (n_gen, T) matrix for a positive-pmax-only profile set.
    need_min_gen = any(
        str(uid) in profiles and fleet_arrays.pmax[g] <= 0.0
        for g, uid in enumerate(uids)
    )
    if need_min_gen and fleet_arrays.min_gen is None:
        fleet_arrays.min_gen = np.broadcast_to(
            fleet_arrays.pmin[:, np.newaxis], (fleet_arrays.pmin.size, hours)
        ).copy()
    for g, uid in enumerate(uids):
        mw = profiles.get(str(uid))
        if mw is None:
            continue
        mw = np.asarray(mw, dtype=float)[:hours]
        if fleet_arrays.pmax[g] > 0.0:  # positive-pmax: upper bound via availability
            fleet_arrays.availability[g, :] = mw / fleet_arrays.pmax[g]
        else:  # DEC net-demand: hourly lower bound
            fleet_arrays.min_gen[g, :] = -mw
        n += 1
    return n


def apply_virtual_bid_prices(
    fuel_prices: np.ndarray, fleet_arrays, price_rows: dict[str, np.ndarray]
) -> int:
    """Write the virtual units' hourly bid prices into ``fuel_prices``.

    Each virtual unit carries ``heat_rate = 1.0`` and ``vom = 0``, so its
    marginal cost is exactly its ``fuel_prices`` row ($/MWh). Must run
    AFTER every other fuel-price applier (the gas-basis overlays key off
    gas fuel types and never touch these rows, but the ordering keeps the
    invariant obvious). Returns the number of rows written.
    """
    if not price_rows:
        return 0
    uids = np.asarray(fleet_arrays.unit_ids, dtype=object)
    hours = fuel_prices.shape[1]
    n = 0
    for g, uid in enumerate(uids):
        row = price_rows.get(str(uid))
        if row is None:
            continue
        fuel_prices[g, :] = np.asarray(row, dtype=float)[:hours]
        n += 1
    return n

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
NET virtual curve** — the financial net of submitted demand and supply:

    net(λ) = Σ_{DEC bids ≥ λ} MW − Σ_{INC offers ≤ λ} MW

``net(λ)`` is monotone non-increasing in ``λ`` with a crossing price ``λ0``:
below ``λ0`` the market holds net virtual DEMAND, above it net virtual
SUPPLY. The layer renders the WHOLE measured curve — **symmetric net form**
(pjm-105; docs/FINDING-pjm-midmerit-level-2026-07.md §6 item 1):

* the ``net > 0`` region → DEC-form withdrawal rungs (``pmax = 0``, dispatch
  in ``[-MW(t), 0]`` via an hourly ``min_gen`` lower bound): a block priced
  at ``b`` withdraws — adds DA demand — whenever the zonal dual is below
  ``b``;
* the ``net < 0`` region → INC-form net-SUPPLY rungs (hourly ``pmax``
  profile via ``availability``, offer price via the unit's ``fuel_prices``
  row): a block offered at ``o`` produces whenever the dual is above ``o``.
  Rung capacities are the increments of ``|net(λ)|`` above ``λ0`` and rung
  prices the measured MW-weighted quantiles — the exact mirror of the DEC
  compression (``N_RUNGS`` per side; resolution only, never tunable).

Clearing is endogenous on BOTH sides: the LP dual finds where the model's
own stack crosses ``load + net(λ)``. Because every DEC rung is priced at or
below ``λ0`` and every INC rung at or above it, at most one side of the
curve is active at any dual — the two sides can never clear against each
other.

Why this is NOT the condemned pjm-101 gross-INC construction
(docs/FINDING-pjm-da-depth-midcurve-2026-07.md §5-6). pjm-101 injected the
GROSS submitted INC curves as physical zero-cost supply — ~56 TWh/yr of
fuel-type-``import`` generation that displaced real peaker dispatch (C1
CT_PEAKER −12/−13 TWh) and suppressed mean prices toward actual through a
mechanism that isn't real (rule 1). The symmetric form's supply side is
bounded by the measured NET position — the annual net of the whole curve
cleared at actual DA prices is ≈ 0 (−0.6/−0.9/+1.3 TWh 2023/24/25, vs the
one-sided clamp's +10.3/+14.8/+17.2 TWh of phantom demand) — it enters at
the measured submitted offer prices (never zero-cost), and it displaces
off-peak generation exactly where the real DA market scheduled less
physical generation than RT load. The predecessor CLAMPED net form (the
net-negative tail zeroed, pjm-102) was owner-adjudicated diagnostic
scaffolding only (2026-07-13): even a perfectly-priced stack had to
over-generate by the clamp's one-sided 10-17 TWh/yr against the RT-physical
C1/C2 benchmarks, and three probes (net-only → pjm-103 → pjm-104) proved
the phantom just re-routes to whichever class is left cheapest.

Admissibility (CLAUDE.md rule 13)
---------------------------------
The curves are SUBMITTED ex-ante participant inputs — the demand-side
mirror of generator energy offers, the same measured-input class as
delivered fuel prices and CAMPD outage windows (same-year measured inputs
admissible in backcast). Cleared virtual volume and the clearing price are
both LP OUTPUTS on both sides of the curve: the dual finds where the
model's own stack crosses ``load + net(λ)``. Nothing is pinned to a
measured outcome, and clearing prices stay validation-only.

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

#: plant_group carried by the DEC-form (net-demand) virtual pseudo-units.
#: Not a physical class: no bench class matches it (class metrics and the
#: C1 ``_gen_totals`` reconcile ignore the units by construction) and the
#: units are reserve-ineligible (fuel_type "import" is outside
#: RESERVE_FUEL_TYPES).
VIRTUAL_DEC_GROUP = "VIRTUAL_DEC"

#: plant_group carried by the INC-form (net-supply) virtual pseudo-units —
#: the ``net < 0`` region of the same measured curve. Same non-physical
#: treatment as VIRTUAL_DEC: no bench class, reserve-ineligible,
#: zero-emission.
VIRTUAL_INC_GROUP = "VIRTUAL_INC"

#: Equal-MW rungs each side of the hourly net curve is compressed to.
#: Resolution / LP-columns trade-off only (rung prices/MW are the measured
#: curve's own weighted quantiles, not tunable values).
N_RUNGS = 8

#: DEC bids are capped at this fraction of VOLL so a virtual bid can never
#: outbid load shedding (PJM's $2,000/MWh hard cap sits far below VOLL, so
#: this guard is a structural no-op on the measured data).
DEC_VOLL_CAP_FRAC = 0.95

#: Strict margin added to the INC-side offer floor (mirrors the storage
#: tiebreaker ε; $/MWh). See ``_inc_offer_floor``.
INC_FLOOR_EPSILON = 0.001


def _raw_dir() -> Path:
    return paths.PJM_DA_VIRTUALS_DIR


def _inc_offer_floor(config, year: int) -> float:
    """Dump-safe lower bound for INC net-supply offer prices ($/MWh).

    The dispatch LP prices overgeneration dump at
    ``dump_cost = −min(0, wind_mc, solar_mc, −storage_eac) + ε`` (see
    ``model.dispatch`` — dump must exceed any production credit so credited
    energy is never generated just to be dumped). The same invariant must
    hold for the INC rungs: an offer below ``−dump_cost`` would make
    generate-and-dump profitable in every hour, pinning the dual at
    ``−dump_cost`` — a gamed LP, not the measured curve. Flooring the INC
    offers at that same credit bound (+ε) keeps the guard sound; it is also
    representation-exact, not a distortion: the LP's dual can never fall
    below ``−dump_cost``, so a floored offer clears identically to the raw
    submitted price in every price state the model can represent. The
    credit bound here is the pre-``negative_renewable_offers`` chain — that
    flag only makes ``wind_mc``/``solar_mc`` MORE negative (a larger
    ``dump_cost``), so this floor stays conservative. On the measured
    2023-2025 corpus the floor is a structural no-op (minimum rendered INC
    rung price ≈ −$1.3/MWh vs a ≈ −$27 floor at the wind-PTC credit) — the
    same status as the DEC-side VOLL cap.
    """
    from market_sim.policy.eac import compute_eac_dispatch_credits
    from market_sim.policy.ira import compute_dispatch_credits

    wind_mc, solar_mc = compute_dispatch_credits(config, year)
    wind_eac, solar_eac, storage_eac = compute_eac_dispatch_credits(config)
    min_credit = min(0.0, wind_mc - wind_eac, solar_mc - solar_eac, -float(storage_eac))
    return min_credit + INC_FLOOR_EPSILON


def _hourly_net_rungs(
    bids: pd.DataFrame, hours: int, n_rungs: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compress each hour's symmetric NET virtual curve to equal-MW rungs.

    ``net(λ) = Σ_{DEC bids ≥ λ} MW − Σ_{INC offers ≤ λ} MW`` — the financial
    net of the submitted virtual demand and supply. Each price point ``p``
    contributes a combined block of ``dec_p + inc_p`` MW at price ``p``
    (crossing ``λ`` upward through ``p`` drops net demand by both the demand
    that stops buying and the supply that starts selling). Sorted by price,
    the lowest-priced ``Σ dec`` MW of these blocks is the ``net ≥ 0``
    region (net demand); the higher-priced remainder — exactly ``Σ inc`` MW
    — is the ``net < 0`` region, whose cumulative mass above the crossing
    price ``λ0`` IS ``|net(λ)|`` (net supply).

    Both regions are rendered: returns ``(dec_mw, dec_price, inc_mw,
    inc_price)``, each of shape ``(n_rungs, hours)`` — the demand region
    split into ``n_rungs`` equal-MW DEC-form withdrawal rungs and the supply
    region into ``n_rungs`` equal-MW INC-form net-supply rungs, each rung
    priced at the MW-weighted quantile of its region's cumulative-share
    midpoint (the same compression on both sides). Every DEC rung price is
    ≤ ``λ0`` ≤ every INC rung price, so the two sides can never clear
    simultaneously at one dual. Hours with no submitted mass on a side stay
    zero on that side; sides with < 1 MW of total mass are dropped.
    """
    dec_mw = np.zeros((n_rungs, hours))
    dec_price = np.zeros((n_rungs, hours))
    inc_mw = np.zeros((n_rungs, hours))
    inc_price = np.zeros((n_rungs, hours))
    qs = (np.arange(n_rungs) + 0.5) / n_rungs  # cumulative-MW midpoints
    sub = bids[((bids["inc"] > 0.0) | (bids["dec"] > 0.0)) & (bids["t"] < hours)]
    for t, g in sub.groupby("t", sort=False):
        p = g["price"].to_numpy(dtype=float)
        dec = g["dec"].to_numpy(dtype=float)
        block = dec + g["inc"].to_numpy(dtype=float)  # net drop at price p
        total_dec = dec.sum()
        order = np.argsort(p)  # ascending price (lowest willingness first)
        p, block = p[order], block[order]
        # Split the combined ladder at the net crossing: the lowest-priced
        # total_dec MW is the net-demand region (keep[j], partial at the
        # crossing); the remainder — Σ block − Σ dec == Σ inc MW — is the
        # net-supply region.
        prior = np.cumsum(block) - block  # combined MW strictly below price p
        keep = np.clip(total_dec - prior, 0.0, block)
        rem = block - keep
        for side_mw, side_price, mass in (
            (dec_mw, dec_price, keep),
            (inc_mw, inc_price, rem),
        ):
            m_total = mass.sum()
            if m_total < 1.0:
                continue  # sub-MW side: nothing to render
            pos = mass > 0.0  # drop zero-mass points for interp stability
            # MW-weighted cumulative-share midpoints of the side's curve.
            ck = (np.cumsum(mass) - 0.5 * mass)[pos]
            side_price[:, t] = np.interp(qs * m_total, ck, p[pos])
            side_mw[:, t] = m_total / n_rungs
    return dec_mw, dec_price, inc_mw, inc_price


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


def load_hourly_net_virtual_curve(
    iso: str, year: int, hours: int, n_rungs: int = N_RUNGS
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray] | None:
    """Measured hourly symmetric net-virtual rung ladders for one backcast year.

    Returns ``(dec_mw, dec_price, inc_mw, inc_price)`` with ``(n_rungs,
    hours)`` arrays on the model clock — the equal-MW DEC-form withdrawal
    rungs of the per-hour ``Σ DEC≥λ − Σ INC≤λ`` net curve's positive region
    and the equal-MW INC-form net-supply rungs of its negative region — or
    ``None`` when the raw corpus is absent.
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
    """Build the PJM symmetric net-virtual pseudo-units, MW profiles, price rows.

    Args:
        config: ScenarioConfig; gates on ``pjm_da_virtual_bids``.
        iso: ISO id; the mechanism is PJM-only.
        year: backcast year whose measured hourly curves are read.
        demand: ``(n_zones, T)`` zonal demand MW (physical, pre-virtual).
        zone_names: zone order matching ``demand`` rows.

    Returns:
        ``(units, profiles, price_rows)``: the net curve's pseudo-generators
        to append to the fleet — DEC-form withdrawal rungs (``pmax = 0``;
        the ``net > 0`` region) plus INC-form net-supply rungs (positive
        ``pmax``; the ``net < 0`` region) — a ``unit_id -> (T,) MW``
        bound-profile map (DEC lower bounds via ``min_gen``, INC upper
        bounds via ``availability``; apply with
        :func:`apply_virtual_profiles`), and a ``unit_id -> (T,)`` $/MWh
        bid/offer-price map for the units' ``fuel_prices`` rows
        (``heat_rate`` is 1.0; apply with :func:`apply_virtual_bid_prices`).
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
    inc_floor = _inc_offer_floor(config, year)

    units: list[Generator] = []
    profiles: dict[str, np.ndarray] = {}
    price_rows: dict[str, np.ndarray] = {}
    dec_mw, dec_price, inc_mw, inc_price = curve  # each (N_RUNGS, T)
    # A DEC bid can never outbid load shedding (no-op on measured data: PJM's
    # $2,000 hard cap << 0.95 x VOLL); an INC offer can never underbid the
    # dump outlet (see _inc_offer_floor — representation-exact clipping).
    dec_price = np.minimum(dec_price, voll_cap)
    inc_price = np.maximum(inc_price, inc_floor)
    sides = (
        ("vNET", VIRTUAL_DEC_GROUP, "NET", dec_mw, dec_price),
        ("vINC", VIRTUAL_INC_GROUP, "INC", inc_mw, inc_price),
    )
    for tag, group, label, mw, price in sides:
        for r in range(mw.shape[0]):
            mw_zt = mw[r][None, :] * zone_share  # (n_zones, T)
            for zi, zone in enumerate(zone_names):
                mw_z = mw_zt[zi]
                peak = float(mw_z.max())
                if peak < 0.5:  # sub-MW everywhere: skip the column
                    continue
                uid = f"{zone}_{tag}_R{r:02d}"
                is_dec = group == VIRTUAL_DEC_GROUP
                units.append(
                    Generator(
                        unit_id=uid,
                        name=(
                            f"PJM DA net-virtual-{'demand' if is_dec else 'supply'} "
                            f"rung {r} ({zone})"
                        ),
                        zone=zone,
                        fuel_type="import",  # reserve-ineligible, zero-emission
                        # DEC-form withdrawal: pmax 0, dispatch in [-MW(t), 0].
                        # INC-form net supply: dispatch in [0, MW(t)].
                        pmax_mw=0.0 if is_dec else peak,
                        pmin_mw=-peak if is_dec else 0.0,
                        heat_rate=1.0,  # mc rides the fuel_prices row ($/MWh)
                        vom=0.0,
                        eford=0.0,
                        plant_group=group,
                        bin_label=f"{label}_R{r:02d}",
                    )
                )
                profiles[uid] = mw_z
                price_rows[uid] = price[r]
    n_dec = sum(1 for u in units if u.plant_group == VIRTUAL_DEC_GROUP)
    logger.info(
        "PJM %d DA symmetric net-virtual layer: %d DEC-form + %d INC-form "
        "pseudo-units (%d rungs/side, measured hourly curves; "
        "net = Σ DEC≥λ − Σ INC≤λ, both regions rendered — annual cleared "
        "net ≈ 0 at actual DA prices)",
        year,
        n_dec,
        len(units) - n_dec,
        N_RUNGS,
    )
    return units, profiles, price_rows


def apply_virtual_profiles(fleet_arrays, profiles: dict[str, np.ndarray]) -> int:
    """Post-fleet-arrays hourly MW bounds for the virtual pseudo-units.

    DEC-form rungs (``pmax == 0``): hourly lower bound rides ``min_gen``
    (seeded from pmin for every generator if absent — the export-sink-safe
    convention of the fleet floor appliers), set to ``-MW(t)``; their ``pmax``
    is 0 so the dispatch range is ``[-MW(t), 0]``. DEC rows carry no mechanism
    id: a negative lower bound is withdrawal capacity, not a commitment floor
    (D-2 attribution only tracks ``min_gen > 0``). INC-form net-supply rungs
    (positive ``pmax``): hourly upper bound rides ``availability``
    (``MW(t) / pmax``), the standard renewable/import convention — dispatch
    in ``[0, MW(t)]``, no floor of any kind.

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
        if fleet_arrays.pmax[g] > 0.0:  # INC net-supply: upper bound
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

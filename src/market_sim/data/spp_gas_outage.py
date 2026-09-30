"""SPP's published hourly natural-gas outage and the gas-family CROW-residual carrier (SPP-105).

Armed by ``ScenarioConfig.spp_gas_crow_residual_outage`` (default off, SPP-only, backcast with
``outage_source="historic"`` only). Record: ``docs/handoffs/DESIGN-spp-105-gas-family-outage-2026-09-30.md``
(carrier B), owner card "Build carrier a and b" (2026-09-30).

The carrier REPLACES the statistical WEFOR / POF on every gas row (rule 19 [R-ONE-MECH]). Those terms are
zeroed in ``data.fleet.arrays._availability_matrix`` and their would-be annual outage rate is kept as the
allocation key. After the measured CAMPD event overlays have run, SPP's measured residual
``R(t) = max(0, SPP_gas(t) - E(t))`` is removed from the gas rows. ``E`` is the event MW those overlays
took, on the rated basis SPP reports. The allocation is pro rata to each row's key and capped at the row's
available MW. It has zero free parameters (rule 21 [R-DOF]).

Declared at the gate: in every hour where SPP's total exceeds the CAMPD events, the model's gas outage equals
the published total (DESIGN s4-s5). A forecast year has no published series, so the statistical stack
stands there (rule 13 [R-MEASURED]).
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np
import pandas as pd

from market_sim.config.paths import SPP_GEN_OUTAGE_CSV

GAS_COLUMN = "Natural Gas MW"
# Nearest-hour alignment tolerance onto the model clock (SPP-84's convention,
# scripts/probes/_spp84_published_outage_rebasis.py::spp_outage_on_model_clock).
ALIGN_TOLERANCE_H = 3
# Leading / trailing dark runs at least this long are COD / retirement, not outage (SPP-84's
# ``--edge-days 30``, reproduced by SPP-104 and SPP-105's phase 0).
EDGE_RUN_H = 30 * 24
# Water-filling passes for the capped proportional split (a pass only re-splits what the previous
# one could not place; the unplaced remainder after the last pass is reported, never forced).
FILL_PASSES = 8


@lru_cache(maxsize=1)
def _published() -> pd.Series:
    """The committed portal series: ``Natural Gas MW`` indexed by naive ``Market Hour``."""
    if not SPP_GEN_OUTAGE_CSV.exists():
        raise FileNotFoundError(
            f"{SPP_GEN_OUTAGE_CSV} missing: run scripts/data/fetch_spp_capacity_gen_outage.py "
            "(spp_gas_crow_residual_outage needs SPP's published gas outage)"
        )
    d = pd.read_csv(SPP_GEN_OUTAGE_CSV, usecols=["Market Hour", GAS_COLUMN])
    t = pd.to_datetime(d["Market Hour"], format="%m/%d/%Y %H:%M:%S")
    s = pd.Series(d[GAS_COLUMN].to_numpy(dtype=float), index=t).sort_index()
    return s[~s.index.duplicated(keep="last")]


def spp_published_gas_outage_mw(year: int, hours: int) -> np.ndarray:
    """SPP's published natural-gas outage MW on the model's ``hours`` slots (NaN where unpublished).

    Model slot ``h`` is fixed CST, starting 1 January 00:00, with 29 February dropped (the SPP model
    clock, ``scripts/probes/_spp72_demand_tightness.model_clock_index``). A slot takes the nearest
    published market hour within ``ALIGN_TOLERANCE_H`` hours.
    """
    idx = pd.date_range(f"{year}-01-01", periods=hours + 24, freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))][:hours]
    s = _published()
    s = s[
        (s.index >= idx[0] - pd.Timedelta(days=1))
        & (s.index <= idx[-1] + pd.Timedelta(days=1))
    ]
    if s.empty:
        raise ValueError(f"no published SPP gas outage for {year}")
    return s.reindex(
        idx, method="nearest", tolerance=pd.Timedelta(hours=ALIGN_TOLERANCE_H)
    ).to_numpy(dtype=float)


def edge_live(post: np.ndarray, min_run: int = EDGE_RUN_H) -> np.ndarray:
    """False on each row's leading / trailing all-zero runs of >= ``min_run`` hours.

    SPP-84's COD / retirement rule: a unit dark from 1 January, or to 31 December, for a month or more
    is not yet built or already gone. It is not "on outage", and SPP's outage report does not carry it.
    """
    n, t = post.shape
    live = np.ones((n, t), dtype=bool)
    on = post > 0.0
    any_on = on.any(1)
    first = np.where(any_on, on.argmax(1), t)
    last = np.where(any_on, t - 1 - on[:, ::-1].argmax(1), -1)
    hrs = np.arange(t)[None, :]
    lead = (first >= min_run)[:, None] & (hrs < first[:, None])
    trail = ((t - 1 - last) >= min_run)[:, None] & (hrs > last[:, None])
    live &= ~(lead | trail)
    live[~any_on] = False
    return live


def allocate_crow_residual(
    pmax: np.ndarray,
    pre: np.ndarray,
    post: np.ndarray,
    rate: np.ndarray,
    published: np.ndarray,
    online: np.ndarray | None = None,
) -> tuple[np.ndarray, dict]:
    """Remove SPP's measured gas residual from the gas rows; return new availability and diagnostics.

    ``pmax`` (n,), ``pre`` / ``post`` (n, T) availability fractions before / after the measured event
    overlays, ``rate`` (n,) the annual statistical outage rate the row would have carried (the key),
    ``published`` (T,) SPP's gas outage MW (NaN = unpublished, no carrier that hour), ``online`` (n, T)
    an optional 0/1 in-service mask (the COD ramp's months).

    A row-hour counts only while the row is LIVE: in service (``online``) and outside a leading /
    trailing dark run of >= 30 days (:func:`edge_live`). The event MW is ``pmax x (1 - post / pre)`` on
    live row-hours: the share of the row the overlays removed, at rated capacity. That is SPP's basis,
    which reports outaged capacity, not derated headroom. The residual is split each hour over the live
    rows, pro rata to ``pmax x rate``, and capped at each row's available MW.
    """
    pm = np.asarray(pmax, dtype=float)
    live = edge_live(post)
    if online is not None:
        live &= np.asarray(online) > 0.0
    with np.errstate(divide="ignore", invalid="ignore"):
        frac_out = np.where(live & (pre > 0.0), 1.0 - post / pre, 0.0)
    events = (pm[:, None] * np.clip(frac_out, 0.0, 1.0)).sum(0)
    resid = np.where(np.isfinite(published), np.maximum(0.0, published - events), 0.0)
    cap = np.where(live, pm[:, None] * post, 0.0)
    key = (pm * np.asarray(rate, dtype=float))[:, None]
    take = np.zeros_like(post)
    # Proportional split with caps (water-filling): each pass re-splits what is
    # still unplaced over the rows that still have headroom. A handful of
    # vectorized passes, not an hour loop (rule 2 [R-VECTOR]).
    for _ in range(FILL_PASSES):
        left = resid - take.sum(0)
        room = cap - take
        w = np.where(room > 1e-9, key, 0.0)
        tot = w.sum(0)
        if not ((left > 1e-6) & (tot > 0.0)).any():
            break
        with np.errstate(divide="ignore", invalid="ignore"):
            share = np.where(tot > 0.0, w / tot, 0.0)
        take += np.minimum(share * np.maximum(left, 0.0)[None, :], room)
    with np.errstate(divide="ignore", invalid="ignore"):
        new = np.where(pm[:, None] > 0.0, post - take / pm[:, None], post)
    diag = {
        "binding_hour_share": float((resid > 0.0).mean()),
        "event_gw_mean": float(events.mean() / 1e3),
        "residual_gw_mean": float(resid.mean() / 1e3),
        "placed_gw_mean": float(take.sum(0).mean() / 1e3),
        "unplaced_gw_mean": float((resid - take.sum(0)).mean() / 1e3),
        "published_coverage": float(np.isfinite(published).mean()),
    }
    return new, diag

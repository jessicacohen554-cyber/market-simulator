"""ercot-184 D5: the build-free reach measurement for the (c2) cliff-resolving refinement.

Pre-registered in ``docs/MEMO-ercot184-cliff-resolution-costing-2026-08-09.md``
§2 (G-SHED PRIMARY + G-REACH + P-1..P-4), pushed BEFORE this probe was written.

COSTING ONLY. No ``ScenarioConfig`` field, no derive, no LP solve, no registered
run, no matrix cell. The keeper ``2026-08-09-run181-position-tail`` is untouched.
Every year touched is 2023 (rule 22).

THE QUESTION (decision card §10 D5): can a resolution change MOVE THE LP'S
CLEARING POSITION up the curve, or does it only price the top of the curve more
accurately?

METHOD — the invariant-quantity repricing (IQR). Re-slicing a plant's economic
ramp preserves its total MW, so in any hour the quantity the thermal stack must
serve is unchanged. The measurement therefore holds the CLEARED QUANTITY fixed
and asks what the refined stack prices AT that quantity:

  1. Reconstruct the keeper's 2023 fleet with no LP (``reconstruct_bundle_fleet``).
  2. Reproduce the priced row geometry (within-plant cumulative midpoints ->
     ``rel`` -> position-tail-completed ladder -> composed markup) and assert it
     equals the builders' own ``_compose`` output BYTE-IDENTICALLY (V-1). The
     gate-off compose sha is checked against the ercot-178 record first (V-0).
  3. Anchor ``Q_h`` = the coarse stack's MW at or below the model's own stored
     price, per hour (system grain; ERCOT prices are zone-identical in 84.2 % of
     2023 hours, disclosed in the memo).
  4. Re-slice every plant's econ ramp under candidate schemes that preserve
     total curve MW, reprice each new slice through the SAME measured ladders at
     its OWN new position, and read the refined stack's price at ``Q_h``.
  5. Adjudicate G-SHED-A/B (clamp displacement + headroom) and G-REACH.

Output: results/calibration/ercot184_cliff_resolution.json.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

CONTROL = REPO / "results/calibration/ercot181_control_A"
KEEPER = REPO / "results/calibration/ercot181_positiontail_B"
VS = REPO / "data/raw/_validation-source"
OUT = REPO / "results/calibration/ercot184_cliff_resolution.json"
YEAR = 2023

#: ercot-178 seam proof SP2 gate-off compose sha, re-verified by ercot-180/181.
CONTROL_COMPOSE_SHA_2023 = (
    "25a4ba697e5902616dff9528c124a6f600d73d3530044087536f38ac7a579567"
)

#: The frozen ladder position grid both priced members read (``np.interp``).
LADDER_Q = np.array([0.1, 0.3, 0.5, 0.7, 0.9])

#: ``offer_curve_smoothing_mid`` the ERCOT keeper solves on (meta.json).
KEEPER_MID = 0.35

#: The keeper's econ slice count (``offer_curve_smoothing_n``).
N_COARSE = 6

#: C3a-2023 needs the annual load-weighted mean to rise by this much
#: (ercot-177 §7: $43.45 -> >= $57.89).
BAR_USD_PER_MWH = 14.44

#: The G-REACH build bar fixed ex ante in the memo's §2.2.
G_REACH_BAR = 5.00


def _sp178():
    """Load the ercot-178 seam-proof module (the canonical ``_compose`` mirror)."""
    spec = importlib.util.spec_from_file_location(
        "sp178", REPO / "scripts/probes/ercot178_contpct_seamproof.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ramp_shape(t: np.ndarray, mid: float = KEEPER_MID) -> np.ndarray:
    """Return ``f(t)``, the econ ramp's position->rise shape function.

    Mirrors :func:`market_sim.data.offer_curves._econ_curve_steps`'s ``mid``
    branch: the two-segment piecewise-linear ramp ``f(0)=0, f(0.5)=mid,
    f(1)=1``.

    Args:
        t: Positions along the econ ramp in ``[0, 1]``.
        mid: The fraction of the lo->pk rise reached at the capacity midpoint.

    Returns:
        The rise fraction at each position.
    """
    t = np.asarray(t, dtype=float)
    return np.where(t <= 0.5, 2.0 * mid * t, mid + (1.0 - mid) * (2.0 * t - 1.0))


def gas_day_series(year: int, hours: int) -> np.ndarray:
    """Return the wall/pool builders' own delivered-gas day series (mirrored)."""
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D")
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    return daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)


# ---------------------------------------------------------------------------
# Geometry: within-plant positions -> rel -> ladder -> markup
# ---------------------------------------------------------------------------


def _load_ladders(year: int) -> dict:
    """Load the keeper's armed wall / pool ladders, position-tail completed."""
    from market_sim.data.fleet.offer_surfaces import _positiontail_xy

    dam = json.loads((VS / "ercot_dam_cleared_share_condbinned.json").read_text())
    rt = json.loads((VS / "ercot_sced_offer_wall_positiontail.json").read_text())
    pool = json.loads((VS / "ercot_faststart_pool_positiontail.json").read_text())
    edges = tuple(float(x) for x in dam["_provenance"]["netload_pct_edges"])
    n_bins = len(edges) + 1

    out: dict = {
        "edges": edges,
        "n_bins": n_bins,
        "boundary": {},
        "dam_wall": {},
        "rt_xy": {},
    }
    for cls_key in ("CC", "CT"):
        tbl = dam.get(cls_key, {}).get("years", {}).get(str(year)) or dam.get(
            cls_key, {}
        ).get("pooled")
        if tbl:
            share = np.asarray(tbl.get("cleared_share", ()), dtype=float)
            if share.size == n_bins and len(tbl.get("ladder", ())) == n_bins:
                out["boundary"][cls_key] = share
                out["dam_wall"][cls_key] = np.array(
                    [[float(pt[1]) for pt in b] for b in tbl["ladder"]], dtype=float
                )
        rtbl = rt.get(cls_key, {}).get("years", {}).get(str(year))
        if rtbl and len(rtbl.get("ladder", ())) == n_bins:
            lad = np.array(
                [[float(pt[1]) for pt in b] for b in rtbl["ladder"]], dtype=float
            )
            tails = rtbl.get("tail") or [[] for _ in range(n_bins)]
            out["rt_xy"][cls_key] = [
                _positiontail_xy(LADDER_Q, lad[b], tails[b]) for b in range(n_bins)
            ]

    ptbl = pool.get("CT", {}).get("years", {}).get(str(year))
    out["pool_xy"] = None
    if ptbl and len(ptbl.get("ladder", ())) == n_bins:
        frac = np.asarray(ptbl.get("pool_frac", ()), dtype=float)
        lad = np.array(
            [[float(pt[1]) for pt in b] for b in ptbl["ladder"]], dtype=float
        )
        tails = ptbl.get("tail") or [[] for _ in range(n_bins)]
        out["pool_boundary"] = 1.0 - np.clip(frac, 0.0, 1.0)
        out["pool_xy"] = [
            _positiontail_xy(LADDER_Q, lad[b], tails[b]) for b in range(n_bins)
        ]
    return out


def position_mult_table(
    share: np.ndarray,
    cls: np.ndarray,
    min_down: np.ndarray,
    lad: dict,
    wall_scope: np.ndarray,
    pool_scope: np.ndarray,
    faststart_max_min_down: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return the ``(n_rows, n_bins)`` ladder multiplier, live mask and rel map.

    Mirrors the builders exactly (the ercot-181 ``_year_geometry`` mirror, with
    the ladders position-tail completed): the cleared-share wall floors CC/CT
    ``econ*`` rows above the measured DAM cleared-share boundary, with the
    RT/SCED leg REPLACING the DAM leg in every bin that carries one; the
    fast-start pool then REPLACES (never stacks on) the wall on merchant CT rows
    above the pool boundary. Each reads its own ladder at
    ``rel = (share - boundary) / (1 - boundary)``.

    Args:
        share: Within-plant cumulative-capacity midpoint per row.
        cls: ``"CC"`` / ``"CT"`` ladder class per row (``""`` = not priced).
        min_down: Per-row minimum-down hours (the pool's physics gate).
        lad: The ladder tables from :func:`_load_ladders`.
        wall_scope: Per-row mask — the wall's ``econ*`` scope.
        pool_scope: Per-row mask — the pool's ``econ*``/``peak*`` scope.
        faststart_max_min_down: The pool's ``min_down <=`` physics gate.

    Returns:
        ``(mult, live, rel)`` each ``(n_rows, n_bins)``; ``rel`` is NaN where the
        row reads no ladder in that bin.
    """
    n_rows = share.shape[0]
    n_bins = lad["n_bins"]
    mult = np.zeros((n_rows, n_bins))
    live = np.zeros((n_rows, n_bins), dtype=bool)
    rel_map = np.full((n_rows, n_bins), np.nan)
    pool_xy = lad.get("pool_xy")
    pool_bnd = lad.get("pool_boundary")
    for i in range(n_rows):
        c = cls[i]
        s_g = share[i]
        if not np.isfinite(s_g):
            continue
        rt_xy = lad["rt_xy"].get(c)
        dam_w = lad["dam_wall"].get(c)
        bnd = lad["boundary"].get(c)
        if wall_scope[i] and bnd is not None:
            for b in range(n_bins):
                if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                    continue
                rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                if dam_w is not None and np.isfinite(dam_w[b]).all():
                    mult[i, b] = float(np.interp(rel, LADDER_Q, dam_w[b]))
                    live[i, b] = True
                    rel_map[i, b] = rel
                if rt_xy is not None and np.isfinite(rt_xy[b][1]).all():
                    xs, ys = rt_xy[b]
                    mult[i, b] = float(np.interp(rel, xs, ys))  # RT replaces DAM
                    live[i, b] = True
                    rel_map[i, b] = rel
        if (
            pool_xy is not None
            and c == "CT"
            and pool_scope[i]
            and min_down[i] <= faststart_max_min_down
        ):
            for b in range(n_bins):
                pb = pool_bnd[b]
                if not np.isfinite(pb) or pb >= 1.0 or s_g <= pb:
                    continue
                if not np.isfinite(pool_xy[b][1]).all():
                    continue
                xs, ys = pool_xy[b]
                mult[i, b] = float(np.interp((s_g - pb) / (1.0 - pb), xs, ys))
                live[i, b] = True
                rel_map[i, b] = (s_g - pb) / (1.0 - pb)
    return mult, live, rel_map


def markup_from_table(
    mult: np.ndarray,
    live: np.ndarray,
    mc: np.ndarray,
    hour_bin: np.ndarray,
    gas_day: np.ndarray,
    voll_cap: float,
) -> np.ndarray:
    """Evaluate the composed markup on an hour slice from the multiplier table.

    ``max(0, min(mult * gas, price_cap) - mc)`` where the row is live in the
    hour's net-load bin, else 0 — the builders' own composition.
    """
    m_h = mult[:, hour_bin]
    live_h = live[:, hour_bin]
    target = np.minimum(m_h * gas_day[None, :], voll_cap)
    return np.where(live_h, np.maximum(0.0, target - mc), 0.0)


# ---------------------------------------------------------------------------
# Re-slicing schemes (every one preserves total curve MW)
# ---------------------------------------------------------------------------


def scheme_uniform(m: int) -> np.ndarray:
    """Uniform breakpoints — the current form generalized to ``m`` slices."""
    return np.linspace(0.0, 1.0, m + 1)


def scheme_top_refined(n_base: int = N_COARSE, k: int = 6) -> np.ndarray:
    """(c2) as chartered: keep the ramp's body, split its TOP slice ``k`` ways."""
    body = np.linspace(0.0, 1.0 - 1.0 / n_base, n_base)
    top = np.linspace(1.0 - 1.0 / n_base, 1.0, k + 1)
    return np.concatenate([body, top[1:]])


def scheme_geometric_top(m: int = 24, ratio: float = 0.82) -> np.ndarray:
    """Aggressively top-weighted breakpoints — widths shrink geometrically.

    The finest expression of "refine the top of each curve" at a fixed slice
    budget: at ``m = 24, ratio = 0.82`` the last slice is ~0.19 % of the ramp,
    the same order as reality's ``q_act`` 0.9976 formation point.
    """
    w = ratio ** np.arange(m, dtype=float)
    w = w / w.sum()
    return np.concatenate([[0.0], np.cumsum(w)])


SCHEMES: dict[str, np.ndarray] = {
    # The identity control: must return delta == 0 exactly (asserted).
    "R0_uniform_6_control": scheme_uniform(6),
    # (c2) as chartered, modest: body untouched, top 1/6 split 6 ways.
    "R1_top_refined_6x6": scheme_top_refined(6, 6),
    # Refinement EVERYWHERE — the control for "is it the top that matters?"
    "R2_uniform_60": scheme_uniform(60),
    # (c2) at reality's own scale: top slice ~0.19 % of the ramp.
    "R3_geometric_top_24": scheme_geometric_top(24, 0.82),
    # (c2) at the near-continuous limit of the TOP: top 1/6 split 60 ways.
    "R4_top_refined_6x60": scheme_top_refined(6, 60),
}


def interp_weights(t_new: np.ndarray, mid: float = KEEPER_MID) -> np.ndarray:
    """Return the ``(m, N_COARSE)`` matrix mapping coarse slice mc -> fine mc.

    The offer curve is affine in the ramp shape ``f(t)`` between its registered
    ``econ_low`` and ``econ_high`` anchors, so a re-sliced row's cost is the
    linear interpolation of the observed slices in ``f`` — exact at every
    observed slice, and exact wherever the underlying curve is affine in ``f``
    (verified per plant; the residual is disclosed in the memo).
    """
    f_k = ramp_shape((np.arange(N_COARSE) + 0.5) / N_COARSE, mid)
    f_n = ramp_shape(t_new, mid)
    W = np.zeros((t_new.size, N_COARSE))
    for j, f in enumerate(f_n):
        # Snap to a coarse node when the new slice's midpoint IS a coarse
        # midpoint. Without this the ulp gap between 0.5*(x[k] + x[k+1]) and
        # (k + 0.5)/n makes the identity re-slicing perturb every cost at 1e-16,
        # which a step lookup then amplifies — the R0 control would not be inert
        # and no scheme's delta would be trustworthy.
        near = int(np.argmin(np.abs(f_k - f)))
        if abs(f_k[near] - f) <= 1e-12 * max(1.0, abs(f_k[near])):
            W[j, near] = 1.0
            continue
        k = int(np.clip(np.searchsorted(f_k, f) - 1, 0, N_COARSE - 2))
        w = (f - f_k[k]) / (f_k[k + 1] - f_k[k])
        W[j, k] = 1.0 - w
        W[j, k + 1] = w
    return W


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", default=str(OUT))
    ap.add_argument("--chunk", type=int, default=1460)
    args = ap.parse_args()

    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    sp = _sp178()
    rec: dict = {"year": YEAR, "keeper_bundle": KEEPER.name}

    # ---- V-0: the gate-off compose sha reproduces the ercot-178 record ------
    state_c, _ = reconstruct_bundle_fleet(
        CONTROL, YEAR, required_flags=sp.ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    assert state_c["config"].ercot_offer_surface_position_tail is False
    sha_c = sp._sha(sp._compose(state_c, state_c["config"], YEAR)[0])
    rec["V0_control_compose_sha"] = sha_c
    rec["V0_matches_ercot178_record"] = sha_c == CONTROL_COMPOSE_SHA_2023
    if not rec["V0_matches_ercot178_record"]:
        raise SystemExit("STOP-THE-LINE: gate-off compose sha moved at this HEAD")
    del state_c

    # ---- keeper state + the builders' own composed markup ------------------
    state, _meta = reconstruct_bundle_fleet(
        KEEPER, YEAR, required_flags=sp.ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    cfg = state["config"]
    assert cfg.ercot_offer_surface_position_tail is True
    composed, _own, parts = sp._compose(state, cfg, YEAR)
    rec["keeper_compose_sha"] = sp._sha(composed)

    fleet, fa, mc_base = state["fleet"], state["fleet_arrays"], state["mc_base"]
    n_gen, T = mc_base.shape
    net_load = sp._net_load(state)[:T]
    gas_day = gas_day_series(YEAR, T)
    voll_cap = float(getattr(cfg, "ercot_offer_surface_price_cap_frac", 0.95)) * float(
        getattr(cfg, "voll", 5000.0)
    )
    lad = _load_ladders(YEAR)
    hour_bin = np.searchsorted(np.quantile(net_load, lad["edges"]), net_load, "right")

    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS

    fs_md = float(FASTSTART_POOL_MIN_DOWN_HOURS)
    sfx = np.array([g.unit_id.rpartition("_")[2] for g in fleet])
    pfx = np.array([g.unit_id.rpartition("_")[0] for g in fleet])
    grp = np.array([getattr(g, "plant_group", "") or "" for g in fleet])
    mdn = np.array([float(getattr(g, "min_down_hours", 0) or 0) for g in fleet])
    cls_of = {"CC_REGULAR": "CC", "CT_PEAKER": "CT"}
    lcls = np.array([cls_of.get(g, "") for g in grp])
    is_econ = np.char.startswith(sfx.astype(str), "econ")
    is_econc = np.char.startswith(sfx.astype(str), "econc")
    is_peak = np.char.startswith(sfx.astype(str), "peak")
    mean_mc = mc_base.mean(axis=1)

    def plant_shares(prefix_arr, cap_arr, mmc_arr):
        """Within-plant cumulative-capacity midpoints (the builders' own map)."""
        out = np.full(prefix_arr.shape[0], np.nan)
        for p in np.unique(prefix_arr):
            rows = np.flatnonzero(prefix_arr == p)
            order = rows[np.argsort(mmc_arr[rows], kind="stable")]
            caps = cap_arr[order]
            tot = caps.sum()
            if tot <= 0.0:
                continue
            out[order] = (np.cumsum(caps) - 0.5 * caps) / tot
        return out

    share = plant_shares(pfx, fa.pmax, mean_mc)

    # ---- V-1: reproduce the priced row geometry BYTE-IDENTICALLY -----------
    mult0, live0, rel0 = position_mult_table(
        share, lcls, mdn, lad, is_econ, is_econ | is_peak, fs_md
    )
    repro = markup_from_table(mult0, live0, mc_base, hour_bin, gas_day, voll_cap)
    wall = parts["wall"] if parts["wall"] is not None else np.zeros_like(mc_base)
    pool = parts["pool"] if parts["pool"] is not None else np.zeros_like(mc_base)
    own = (
        parts["own_mask"]
        if parts["own_mask"] is not None
        else np.zeros_like(mc_base, dtype=bool)
    )
    truth = np.where(own, pool, wall)
    rec["V1_geometry_byte_identical"] = bool(np.array_equal(repro, truth))
    rec["V1_geometry_max_abs_err"] = float(np.abs(repro - truth).max())
    rec["V1_priced_rows"] = int((np.abs(truth) > 0).any(axis=1).sum())
    print(
        f"V-1 geometry byte-identical={rec['V1_geometry_byte_identical']} "
        f"max|err|={rec['V1_geometry_max_abs_err']:.3e} rows={rec['V1_priced_rows']}"
    )
    if not rec["V1_geometry_byte_identical"]:
        raise SystemExit("STOP-THE-LINE: geometry mirror is not the builders' own")

    # The conditional (peak-rung) member is NOT position-indexed: it is carried
    # through every scheme unchanged (precommit ercot-181 §2's last bullet).
    cond = parts["cond"] if parts["cond"] is not None else np.zeros_like(mc_base)
    cond_only = np.where(np.abs(truth) > 0, 0.0, cond)

    # ---- the model's own price and the object hours ------------------------
    sysd = pd.read_parquet(KEEPER / "hourly" / f"system_{YEAR}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    piv = sysd.pivot(index="hour", columns="zone", values="price")
    dem = sysd.pivot(index="hour", columns="zone", values="demand")
    carry = [c for c in dem.columns if dem[c].to_numpy().sum() > 0]
    load = dem[carry].to_numpy().sum(axis=1)
    price = (piv[carry].to_numpy() * dem[carry].to_numpy()).sum(axis=1) / load
    zspread = piv[carry].to_numpy().max(axis=1) - piv[carry].to_numpy().min(axis=1)
    rec["zone_price_identical_frac"] = float((zspread < 1e-9).mean())
    rec["model_lw_price_2023"] = float((price * load).sum() / load.sum())

    act = pd.read_parquet(VS / "actual_lmp_hourly_ERCOT.parquet")
    act = act[act["year"] == YEAR].sort_values("hour")
    actual = act.set_index("hour")["rt"].reindex(range(T)).to_numpy(dtype=float)
    rec["actual_lw_price_2023"] = float(
        np.nansum(actual * load) / load[np.isfinite(actual)].sum()
    )
    gap = (actual - price) * load
    aug_sep = np.zeros(T, dtype=bool)
    hrs = pd.date_range(f"{YEAR}-01-01", periods=T, freq="h")
    aug_sep[(hrs.month == 8) | (hrs.month == 9)] = True
    obj_rank = np.argsort(-np.where(aug_sep & np.isfinite(gap), gap, -np.inf))
    object_hours = np.sort(obj_rank[:100])
    rec["object_hours_n"] = int(object_hours.size)
    rec["object_hours_gap_share_of_annual"] = float(
        np.nansum(gap[object_hours]) / np.nansum(gap[gap > 0])
    )

    # ---- coarse stack ------------------------------------------------------
    # The anchor Q_h is taken from the coarse stack's OWN sorted cumulative
    # capacity at the last in-the-money row, so the coarse read is exact by
    # construction and both stacks are read by the identical rule. Comparing
    # p_fine against the LP's stored dual instead would fold the merit-order
    # read's own residual into every scheme's delta.
    TOL_MW = 1e-6

    def _sorted_stack(bid, cap):
        """Sort by bid with zero-capacity rows pushed out of the merit order.

        A row with no available capacity in the hour cannot be marginal, and
        leaving it in makes the cumulative-capacity curve FLAT across it — so
        "the first index whose cum reaches Q" lands on an earlier, cheaper row
        and the read acquires a one-sided negative bias. Bidding those rows at
        +inf sorts them past every live row and makes ``cum`` strictly
        increasing wherever it is read.
        """
        eff = np.where(cap > TOL_MW, bid, np.inf)
        order = np.argsort(eff, axis=0, kind="stable")
        b_s = np.take_along_axis(eff, order, axis=0)
        c_s = np.take_along_axis(cap, order, axis=0)
        return b_s, np.cumsum(c_s, axis=0)

    def price_at_Q(bid, cap, Qv):
        """The stack's marginal bid at cumulative quantity ``Qv``."""
        b_s, cum = _sorted_stack(bid, cap)
        idx = np.clip((cum < Qv[None, :] - TOL_MW).sum(axis=0), 0, bid.shape[0] - 1)
        return b_s[idx, np.arange(bid.shape[1])]

    cap0 = fa.pmax[:, None] * fa.availability
    bid0 = mc_base + truth + cond_only
    Q = np.zeros(T)
    p_coarse = np.zeros(T)
    for a in range(0, T, args.chunk):
        b = min(a + args.chunk, T)
        b_s, cum = _sorted_stack(bid0[:, a:b], cap0[:, a:b])
        n_in = np.clip((b_s <= price[None, a:b]).sum(axis=0) - 1, 0, b_s.shape[0] - 1)
        cols = np.arange(b - a)
        Q[a:b] = cum[n_in, cols]
        p_coarse[a:b] = b_s[n_in, cols]
    rec["Q_anchor_mean_mw"] = float(Q.mean())
    rec["Q_anchor_object_mean_mw"] = float(Q[object_hours].mean())

    # Instrument fidelity: how much of the LP's stored dual a pure merit-order
    # read of the same fleet reproduces. Disclosed, not corrected for.
    p_self = np.zeros(T)
    for a in range(0, T, args.chunk):
        b = min(a + args.chunk, T)
        p_self[a:b] = price_at_Q(bid0[:, a:b], cap0[:, a:b], Q[a:b])
    rec["self_read_reproduces_anchor"] = bool(np.array_equal(p_self, p_coarse))
    rec["merit_read_vs_LP_dual_max_abs"] = float(np.abs(p_coarse - price).max())
    rec["merit_read_vs_LP_dual_lw"] = float((p_coarse * load).sum() / load.sum())
    rec["merit_read_vs_LP_dual_object_mean"] = float(
        (p_coarse - price)[object_hours].mean()
    )

    # ---- P-1: where does the marginal row sit? -----------------------------
    marg = []
    for h in object_hours:
        inm = bid0[:, h] <= price[h]
        if not inm.any():
            continue
        i = int(np.flatnonzero(inm)[np.argmax(bid0[inm, h])])
        rr = rel0[i, hour_bin[h]]
        marg.append(
            {
                "hour": int(h),
                "price": float(price[h]),
                "actual": float(actual[h]),
                "unit": fleet[i].unit_id,
                "group": str(grp[i]),
                "suffix": str(sfx[i]),
                "bid": float(bid0[i, h]),
                "share": float(share[i]),
                "rel": None if not np.isfinite(rr) else float(rr),
                "econ_slice_k": int(sfx[i][-2:]) if is_econc[i] else None,
            }
        )
    rec["P1_marginal_rows"] = marg
    ks = [m["econ_slice_k"] for m in marg if m["econ_slice_k"] is not None]
    rels = [m["rel"] for m in marg if m["rel"] is not None]
    rec["P1_summary"] = {
        "n_object_hours": len(marg),
        "marginal_is_econc": len(ks),
        "econ_slice_k_hist": {int(k): int(ks.count(k)) for k in sorted(set(ks))},
        "rel_p50": float(np.median(rels)) if rels else None,
        "rel_min": float(np.min(rels)) if rels else None,
        "rel_max": float(np.max(rels)) if rels else None,
        "family_hist": {
            f: int(sum(1 for m in marg if m["suffix"].startswith(f)))
            for f in ("econc", "econ", "committed", "peak", "mustrun")
        },
    }
    print("P-1 marginal-row summary:", json.dumps(rec["P1_summary"], indent=1))

    # ---- the re-slicing experiment ----------------------------------------
    keep = ~is_econc
    plant_ids = sorted(set(pfx[is_econc].tolist()))
    coarse_idx = {}
    for p in plant_ids:
        r = np.flatnonzero(is_econc & (pfx == p))
        coarse_idx[p] = r[np.argsort([int(sfx[i][-2:]) for i in r])]

    rec["schemes"] = {}
    for name, xb in SCHEMES.items():
        m = xb.size - 1
        t_new = 0.5 * (xb[:-1] + xb[1:])
        w_new = np.diff(xb)
        W = interp_weights(t_new)

        n_new = keep.sum() + m * len(plant_ids)
        f_pfx = np.concatenate([pfx[keep], np.repeat(plant_ids, m)])
        f_cls = np.concatenate(
            [lcls[keep], np.repeat(lcls[[coarse_idx[p][0] for p in plant_ids]], m)]
        )
        f_mdn = np.concatenate(
            [mdn[keep], np.repeat(mdn[[coarse_idx[p][0] for p in plant_ids]], m)]
        )
        f_wall = np.concatenate([is_econ[keep], np.ones(m * len(plant_ids), bool)])
        f_pool = np.concatenate(
            [(is_econ | is_peak)[keep], np.ones(m * len(plant_ids), bool)]
        )
        f_cap = np.concatenate(
            [
                fa.pmax[keep],
                np.concatenate(
                    [fa.pmax[coarse_idx[p]].sum() * w_new for p in plant_ids]
                ),
            ]
        )
        f_av = np.concatenate(
            [
                fa.availability[keep],
                np.repeat(
                    fa.availability[[coarse_idx[p][0] for p in plant_ids]], m, axis=0
                ),
            ]
        )
        f_mc = np.empty((n_new, T))
        f_mc[: keep.sum()] = mc_base[keep]
        pos = keep.sum()
        for p in plant_ids:
            f_mc[pos : pos + m] = W @ mc_base[coarse_idx[p]]
            pos += m
        f_cond = np.concatenate([cond_only[keep], np.zeros((m * len(plant_ids), T))])

        f_share = plant_shares(f_pfx, f_cap, f_mc.mean(axis=1))
        f_mult, f_live, f_rel = position_mult_table(
            f_share, f_cls, f_mdn, lad, f_wall, f_pool, fs_md
        )

        # M-2: how far up the LADDER position axis does re-slicing the RAMP
        # reach? The two axes are distinct — a row's rel is set by its
        # within-plant cumulative share, not by its position along the ramp.
        econ_new = np.zeros(n_new, dtype=bool)
        econ_new[keep.sum() :] = True
        r_new = f_rel[econ_new]
        rec.setdefault("M2_ladder_reach", {})[name] = {
            "max_within_plant_share": float(np.nanmax(f_share[econ_new])),
            "max_ladder_rel": float(np.nanmax(np.nan_to_num(r_new, nan=-1))),
            "econ_rows_with_rel_above_0.9": int(
                (np.nan_to_num(r_new, nan=-1) > 0.9).sum()
            ),
            "ladder_mult_at_max_rel_x_gas": float(
                f_mult[econ_new][
                    np.unravel_index(
                        np.nanargmax(np.nan_to_num(r_new, nan=-1)), r_new.shape
                    )
                ]
            ),
        }

        p_fine = np.zeros(T)
        below_clamp0 = np.zeros(T)
        below_clamp1 = np.zeros(T)
        for a in range(0, T, args.chunk):
            b = min(a + args.chunk, T)
            mk = markup_from_table(
                f_mult, f_live, f_mc[:, a:b], hour_bin[a:b], gas_day[a:b], voll_cap
            )
            fbid = f_mc[:, a:b] + mk + f_cond[:, a:b]
            fcap = f_cap[:, None] * f_av[:, a:b]
            p_fine[a:b] = price_at_Q(fbid, fcap, Q[a:b])
            below_clamp0[a:b] = (cap0[:, a:b] * (bid0[:, a:b] < voll_cap)).sum(axis=0)
            below_clamp1[a:b] = (fcap * (fbid < voll_cap)).sum(axis=0)
            del mk, fbid, fcap
        # M-3 — THE LOAD-BEARING MEASUREMENT: after refinement, where does the
        # marginal row actually SIT in the object hours? Refinement demonstrably
        # puts rows at the cliff (M-2); this asks whether the LP clears there.
        oh = object_hours
        _b0, _c0 = _sorted_stack(bid0[:, oh], cap0[:, oh])
        _o0 = np.argsort(
            np.where(cap0[:, oh] > TOL_MW, bid0[:, oh], np.inf), axis=0, kind="stable"
        )
        _cols = np.arange(oh.size)
        _n = np.clip((_b0 <= price[None, oh]).sum(axis=0) - 1, 0, _b0.shape[0] - 1)
        _m0 = _o0[_n, _cols]
        mk_o = markup_from_table(
            f_mult, f_live, f_mc[:, oh], hour_bin[oh], gas_day[oh], voll_cap
        )
        fb_o = f_mc[:, oh] + mk_o + f_cond[:, oh]
        fc_o = f_cap[:, None] * f_av[:, oh]
        _o1 = np.argsort(np.where(fc_o > TOL_MW, fb_o, np.inf), axis=0, kind="stable")
        _b1 = np.take_along_axis(np.where(fc_o > TOL_MW, fb_o, np.inf), _o1, axis=0)
        _c1 = np.cumsum(np.take_along_axis(fc_o, _o1, axis=0), axis=0)
        _i1 = np.clip((_c1 < Q[oh][None, :] - TOL_MW).sum(axis=0), 0, n_new - 1)
        _m1 = _o1[_i1, _cols]
        rel_c = np.array([rel0[_m0[j], hour_bin[oh[j]]] for j in range(oh.size)])
        rel_f = np.array([f_rel[_m1[j], hour_bin[oh[j]]] for j in range(oh.size)])
        rec.setdefault("M3_marginal_position", {})[name] = {
            "coarse_rel_p50": float(np.nanmedian(rel_c)),
            "coarse_rel_max": float(np.nanmax(rel_c)),
            "refined_rel_p50": float(np.nanmedian(rel_f)),
            "refined_rel_max": float(np.nanmax(rel_f)),
            "refined_marginal_rows_rel_above_0.9": int(
                (np.nan_to_num(rel_f, nan=-1) > 0.9).sum()
            ),
            "refined_marginal_is_a_new_econ_slice": int((_m1 >= keep.sum()).sum()),
            "object_price_p50_coarse": float(np.median(p_coarse[oh])),
            "object_price_p50_refined": float(np.median(p_fine[oh])),
            "object_actual_p50": float(np.nanmedian(actual[oh])),
        }
        del mk_o, fb_o, fc_o, _o1, _b1, _c1

        # Both stacks read by the IDENTICAL rule at the IDENTICAL quantity.
        d = p_fine - p_coarse
        # G-SHED-A: MW the refinement pushes from below the 0.95 x VOLL clamp
        # to at/above it.  G-SHED-B: an hour is SHED-EXPOSED when that
        # displacement eats the hour's own sub-clamp headroom, i.e. the refined
        # stack can no longer serve Q_h below the clamp when the coarse one
        # could — the ercot-48/49 manufactured-shortage channel.
        clamp_disp = below_clamp0 - below_clamp1
        exposed = (below_clamp1 < Q) & (below_clamp0 >= Q)
        lw_fine = float((p_fine * load).sum() / load.sum())
        lw_coarse = float((p_coarse * load).sum() / load.sum())
        p_net = np.where(exposed, p_coarse, p_fine)
        rec["schemes"][name] = {
            "n_slices_per_plant": int(m),
            "top_slice_frac_of_ramp": float(w_new[-1]),
            "bottom_slice_frac_of_ramp": float(w_new[0]),
            "fleet_rows": int(n_new),
            "row_growth_vs_keeper": round(n_new / n_gen, 3),
            "delta_lw_usd_per_mwh": lw_fine - lw_coarse,
            "delta_lw_net_of_shed_exposed": float((p_net * load).sum() / load.sum())
            - lw_coarse,
            "delta_max_usd": float(d.max()),
            "delta_min_usd": float(d.min()),
            "hours_moved": int((np.abs(d) > 1e-9).sum()),
            "hours_moved_up": int((d > 1e-9).sum()),
            "hours_moved_down": int((d < -1e-9).sum()),
            "object_hours_delta_mean": float(d[object_hours].mean()),
            "object_hours_delta_max": float(d[object_hours].max()),
            "object_hours_delta_min": float(d[object_hours].min()),
            "G_SHED_A_clamp_displacement_mw_p50": float(np.median(clamp_disp)),
            "G_SHED_A_clamp_displacement_mw_max": float(clamp_disp.max()),
            "G_SHED_A_object_hours_displacement_mw_p50": float(
                np.median(clamp_disp[object_hours])
            ),
            "G_SHED_B_exposed_hours": int(exposed.sum()),
            "G_SHED_B_exposed_object_hours": int(exposed[object_hours].sum()),
            "G_SHED_B_exposed_share_of_delta": (
                float(((p_fine - p_coarse) * exposed * load).sum() / load.sum())
                / (lw_fine - lw_coarse)
                if abs(lw_fine - lw_coarse) > 1e-9
                else 0.0
            ),
            "G_REACH_bar": G_REACH_BAR,
            "G_REACH_verdict": (
                "PASS"
                if (float((p_net * load).sum() / load.sum()) - lw_coarse) >= G_REACH_BAR
                else "FAIL"
            ),
            "share_of_C3a_bar": (lw_fine - lw_coarse) / BAR_USD_PER_MWH,
        }
        s = rec["schemes"][name]
        if name == "R0_uniform_6_control" and abs(s["delta_lw_usd_per_mwh"]) > 1e-9:
            raise SystemExit(
                "STOP-THE-LINE: the identity re-slicing is not inert "
                f"(delta {s['delta_lw_usd_per_mwh']:.6g}) — the re-slicing "
                "pipeline does not reproduce the keeper's own stack"
            )
        print(
            f"{name:24s} m={m:3d} rows={n_new:6d} top={w_new[-1]:.5f} "
            f"dLW={s['delta_lw_usd_per_mwh']:+.4f} net={s['delta_lw_net_of_shed_exposed']:+.4f} "
            f"({100 * s['share_of_C3a_bar']:+.1f}% of bar) shedH={s['G_SHED_B_exposed_hours']} "
            f"objMean={s['object_hours_delta_mean']:+.3f} {s['G_REACH_verdict']}"
        )
        del f_mc, f_cond, f_av

    rec["BAR_usd_per_mwh"] = BAR_USD_PER_MWH
    Path(args.json).write_text(json.dumps(rec, indent=1, default=str))
    print(f"\nwrote {args.json}")


if __name__ == "__main__":
    main()

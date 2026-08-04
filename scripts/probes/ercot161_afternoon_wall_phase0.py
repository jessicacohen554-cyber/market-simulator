"""ERCOT-161 Phase 0 — why the armed RT SCED offer wall misses the ~100-hour tail.

The FINDING-ercot-2023-summer-underrun-2026-08-04 §6 successor, Phase 0 (NO LP,
no solve, no mechanism armed). The 2023 −30 % load-weighted underrun is ~100
hours (98.3 % of the annual gap); at those hours ERCOT's OWN energy stack
(SCED system lambda) cleared $1,470 mean while the model cleared $441 — and the
keeper already arms the measured RT SCED offer wall
(``ercot_offer_surface_cleared_share`` + ``_rt``, ``_rt_mode=replace``) over the
full-year delivery-2023 corpus. This probe answers the finding's four candidate
explanations, all on committed artifacts + the ERCOT-157 corpus:

1. **Bin resolution** — which net-load bin do the top-100 gap hours occupy
   (both the apply-time model geometry and the derive-time EIA-930 geometry),
   and do that bin's measured rungs carry the $500–3,000 conduct or does
   pooling wash it out?
2. **Row coverage** — is the model's *marginal* row at those hours inside the
   wall's masked row set (merchant CC/CT ``econ*``), or is the margin set by a
   tranche the wall never touches (committed block, peak rung, COAL, ST_GAS,
   fast-start pool row)?
3. **Class coverage** — the marginal CLASS at those hours (CT branch =
   licensing-blocked per ercot-160 item 8(b); this probe only identifies, never
   proxies).
4. **Ceiling/rungs** — the ladder's top quantile is p90: what multiplier does
   each walled row actually reach after the ``rel`` interpolation (the
   rel-clamp census), and does ANY model row price inside $500–3,000 at the gap
   hours?

Part C conditions the corpus's own online-spare ladder ON THE GAP HOURS
(the exact ``_spare_segments`` construction of
``scripts/data/derive_ercot_sced_offer_wall.py``, re-used, not re-implemented)
and contrasts it against the pooled bin ladder the wall applies — the direct
measurement of the wash-out hypothesis, including the SCED-optimality check
that at a cleared lambda of $1,470 the spare curve's own p10 must sit near
lambda (every cheaper segment would have been dispatched).

Consumes: the ercot158 keeper bundle (``meta.json`` reconstruction via
``reconstruct_bundle_fleet`` — fleet/offer arrays only, no LP), its committed
hourly sidecars, ``actual_lmp_hourly_ERCOT.parquet``,
``ercot_2023_ordc_reserves_hourly.parquet`` (NP6-905-CD), the three condbinned
offer artifacts, and the delivery-2023 SCED corpus under
``data/raw/ercot/SCED/``.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot161_afternoon_wall_phase0.py \
        [--skip-corpus] [--top-n 100] [--out results/calibration/_ercot161_wall_phase0.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

BUNDLE = REPO / "results/calibration/ercot158_poolarm_B"
HOURLY = BUNDLE / "hourly"
DEFAULT_OUT = REPO / "results/calibration/_ercot161_wall_phase0.json"
YEAR = 2023

#: ERCOT keeper gates that must survive reconstruction (the miso-116
#: measurement-trap guard, ERCOT-tuned). The RT + pool flags ride the
#: ``coal_prb_sigmoid_overrides`` channel, so they are asserted directly on the
#: reconstructed config below rather than via meta top-level keys.
ERCOT_REQUIRED_FLAGS = (
    "ercot_offer_surface_conditional",
    "ercot_offer_surface_cleared_share",
    "ercot_gas_commitment_bridge",
    "energy_reserve_coopt",
    "ercot_multiproduct_as_coopt",
)

#: Sidecar class labels summed into the thermal dispatch point the
#: merit-crossing method targets (present-set intersected at runtime).
SIDECAR_THERMAL_CLASSES = (
    "COAL_LIGNITE",
    "COAL_PRB",
    "CC_REGULAR",
    "CC_CHP",
    "CT_PEAKER",
    "CT_CHP",
    "ST_GAS",
    "ST_CHP",
    "OTHER",
    "OTHER_FOSSIL",
)

#: Generator ``plant_group`` values forming the model-side thermal stack.
GEN_THERMAL_GROUPS = frozenset(
    {
        "COAL",
        "COAL_LIGNITE",
        "COAL_PRB",
        "CC_REGULAR",
        "CC_CHP",
        "CT_PEAKER",
        "CT_CHP",
        "ST_GAS",
        "ST_CHP",
        "OTHER_FOSSIL",
    }
)

#: Price bands ($/MWh) for the gap-hour stack census (Q4).
PRICE_BANDS = (0.0, 120.0, 300.0, 500.0, 1000.0, 2000.0, 3000.0, float("inf"))

#: Extended quantiles reported for the gap-hour-conditioned corpus ladder —
#: the committed artifact stops at p90 (LADDER_QUANTILES); the tail above it is
#: exactly what Q4 interrogates.
EXT_QUANTILES = (0.1, 0.3, 0.5, 0.7, 0.9, 0.95, 0.99)


def _system_series() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """(model_lw_price, system_load, actual_rt, lambda/rtorpa frame) for 2023."""
    sys_df = pd.read_parquet(HOURLY / f"system_{YEAR}.parquet")
    sys_df = sys_df[sys_df["pass"] == "P1"]
    g = sys_df.groupby("hour")
    lw = g.apply(
        lambda d: (d["price"] * d["demand"]).sum() / d["demand"].sum(),
        include_groups=False,
    )
    load = g["demand"].sum()
    model = lw.reindex(range(8760)).to_numpy(float)
    system_load = load.reindex(range(8760)).to_numpy(float)
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    actual = (
        act[act["year"] == YEAR]
        .set_index("hour")["rt"]
        .reindex(range(8760))
        .to_numpy(float)
    )
    ordc = pd.read_parquet(
        REPO / f"data/raw/ercot/ercot_{YEAR}_ordc_reserves_hourly.parquet"
    ).set_index("hour")
    return model, system_load, actual, ordc


def _hour_set(
    model: np.ndarray,
    load: np.ndarray,
    actual: np.ndarray,
    ordc: pd.DataFrame,
    top_n: int,
) -> tuple[np.ndarray, dict]:
    """Top-``top_n`` gap hours by load-weighted contribution + verification."""
    contrib = (actual - model) * load
    top = np.sort(np.argsort(contrib)[::-1][:top_n])
    months = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h").month.to_numpy()
    hod = np.arange(8760) % 24
    lam = ordc["system_lambda"].reindex(top).to_numpy(float)
    stats = {
        "definition": (
            "top-N hours of (actual_rt - model_loadweighted_price) x system_load; "
            "the FINDING-ercot-2023-summer-underrun-2026-08-04 construction"
        ),
        "top_n": int(top_n),
        "lw_model": round(float((model * load).sum() / load.sum()), 2),
        "lw_actual": round(float((actual * load).sum() / load.sum()), 2),
        "gap_share_pct": round(float(contrib[top].sum() / contrib.sum() * 100), 1),
        "actual_mean": round(float(actual[top].mean()), 2),
        "model_mean": round(float(model[top].mean()), 2),
        "lambda_mean": round(float(np.nanmean(lam)), 2),
        "rtorpa_mean": round(
            float(np.nanmean(ordc["rtorpa"].reindex(top).to_numpy(float))), 2
        ),
        "n_aug_sep": int(np.isin(months[top], [8, 9]).sum()),
        "n_actual_gt_1000": int((actual[top] > 1000).sum()),
        "month_counts": {
            int(m): int(c) for m, c in zip(*np.unique(months[top], return_counts=True))
        },
        "hod_counts": {
            int(h): int(c) for h, c in zip(*np.unique(hod[top], return_counts=True))
        },
        "hours": [int(h) for h in top],
    }
    return top, stats


def _reconstruct() -> dict:
    """Rebuild the keeper's 2023 fleet/offer state (no LP), fidelity-guarded."""
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    state, meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    config = state["config"]
    # The RT leg + fast-start pool ride the prb_overrides channel (ERCOT-65
    # mechanics) — assert them on the reconstructed config itself, because a
    # reconstruction that dropped them would measure the ercot150b wall, not
    # the ercot158 keeper (the miso-116 trap).
    for field, want in (
        ("ercot_offer_surface_cleared_share_rt", True),
        ("ercot_faststart_pool_offer", True),
        ("ercot_offer_surface_cleared_share_state", False),
        ("ercot_offer_surface_cleared_share_steam", False),
        ("ercot_shoulder_online_span", False),
    ):
        got = bool(getattr(config, field, False))
        if got != want:
            raise SystemExit(
                f"reconstruction fidelity: {field}={got} but the keeper "
                f"records {want} — the measured surface would not be the keeper's"
            )
    rt_mode = str(getattr(config, "ercot_offer_surface_cleared_share_rt_mode", ""))
    if rt_mode != "replace":
        raise SystemExit(f"rt_mode={rt_mode!r} != the keeper's 'replace'")
    return state


def _compose_markups(state: dict) -> dict:
    """Rebuild the P1 offer-surface markups exactly as run_calibration composes them."""
    from market_sim.data.fleet import (
        build_ercot_faststart_pool_markup,
        build_ercot_offer_surface_cleared_share_markup,
        build_ercot_offer_surface_conditional_markup,
    )

    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    config = state["config"]
    mc_base = state["mc_base"]
    demand = state["demand"]
    net_load = (
        demand.sum(axis=0)
        - (state["solar_cap"][:, None] * state["solar_cf"]).sum(axis=0)
        - (state["wind_cap"][:, None] * state["wind_cf"]).sum(axis=0)
    )
    cond = build_ercot_offer_surface_conditional_markup(
        fa, fleet, state["fuel_prices"], net_load, config
    )
    cs = build_ercot_offer_surface_cleared_share_markup(
        fa, fleet, mc_base, net_load, config, YEAR
    )
    fsp = build_ercot_faststart_pool_markup(fa, fleet, mc_base, net_load, config, YEAR)
    adjust = np.zeros_like(mc_base)
    if cond is not None:
        adjust = adjust + cond
    if cs is not None:
        adjust = adjust + cs
    fsp_markup = fsp_mask = None
    if fsp is not None:
        fsp_markup, fsp_mask = fsp
        adjust = np.where(fsp_mask, fsp_markup, adjust)
    return {
        "net_load": net_load,
        "cond": cond,
        "cs": cs,
        "fsp_markup": fsp_markup,
        "fsp_mask": fsp_mask,
        "mc_bid": mc_base + adjust,
    }


def _wall_geometry(config, net_load: np.ndarray) -> dict:
    """Apply-time bin assignment + artifact ladders/boundaries (2023 block)."""
    from market_sim.config import paths as _paths

    wall = json.loads(
        (_paths.CALIBRATION_DIR / "ercot_dam_cleared_share_condbinned.json").read_text()
    )
    rt = json.loads(
        (_paths.CALIBRATION_DIR / "ercot_sced_offer_wall_condbinned.json").read_text()
    )
    pool = json.loads(
        (_paths.CALIBRATION_DIR / "ercot_faststart_pool_condbinned.json").read_text()
    )
    edges = tuple(float(x) for x in wall["_provenance"]["netload_pct_edges"])
    ladder_q = np.asarray(wall["_provenance"]["ladder_quantiles"], dtype=float)
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")
    out = {
        "edges": edges,
        "ladder_q": ladder_q,
        "hour_bin": hour_bin,
        "boundary": {},
        "rt_ladder": {},
        "dam_ladder": {},
        "pool_frac": np.asarray(
            pool["CT"]["years"][str(YEAR)]["pool_frac"], dtype=float
        ),
        "pool_ladder": np.array(
            [
                [float(pt[1]) for pt in lad_b]
                for lad_b in pool["CT"]["years"][str(YEAR)]["ladder"]
            ]
        ),
    }
    for cls in ("CC", "CT"):
        tbl = wall[cls]["years"][str(YEAR)]
        out["boundary"][cls] = np.asarray(tbl["cleared_share"], dtype=float)
        out["dam_ladder"][cls] = np.array(
            [[float(pt[1]) for pt in lad_b] for lad_b in tbl["ladder"]]
        )
        out["rt_ladder"][cls] = np.array(
            [
                [float(pt[1]) for pt in lad_b]
                for lad_b in rt[cls]["years"][str(YEAR)]["ladder"]
            ]
        )
    return out


def _gas_day(year: int) -> np.ndarray:
    """Delivered-gas day series on the model clock (the builders' own)."""
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(
        s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D"
    )
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=8760, freq="h").normalize()
    return daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)


def _row_universe(state: dict, marks: dict) -> pd.DataFrame:
    """Per-generator frame: class, tranche suffix, plant prefix, share midpoint."""
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    mc_base = state["mc_base"]
    mean_mc = mc_base.mean(axis=1)
    rows = []
    prefixes: dict[str, list[int]] = {}
    for g, gen in enumerate(fleet):
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
    mids = np.full(len(fleet), np.nan)
    for pref, idx in prefixes.items():
        arr = np.asarray(idx, dtype=int)
        order = arr[np.argsort(mean_mc[arr], kind="stable")]
        caps = fa.pmax[order]
        total = caps.sum()
        if total <= 0:
            continue
        cum = np.cumsum(caps)
        mids[order] = (cum - 0.5 * caps) / total
    for g, gen in enumerate(fleet):
        rows.append(
            {
                "g": g,
                "unit_id": gen.unit_id,
                "prefix": gen.unit_id.rpartition("_")[0],
                "suffix": gen.unit_id.rpartition("_")[2],
                "group": getattr(gen, "plant_group", None) or "",
                "min_down_hours": float(getattr(gen, "min_down_hours", 0) or 0),
                "pmax": float(fa.pmax[g]),
                "share_mid": float(mids[g]),
            }
        )
    return pd.DataFrame(rows)


def _owner_matrix(marks: dict) -> np.ndarray:
    """(n_gen, T) int8 owner: 0 base, 1 conditional, 2 wall(RT/DAM), 3 pool."""
    mc_bid = marks["mc_bid"]
    owner = np.zeros(mc_bid.shape, dtype=np.int8)
    if marks["cond"] is not None:
        owner[marks["cond"] > 0] = 1
    if marks["cs"] is not None:
        owner[marks["cs"] > 0] = 2  # wall floors overwrite cond flags on econ rows
    if marks["fsp_mask"] is not None:
        owner[marks["fsp_mask"]] = 3
    return owner


OWNER_NAMES = {0: "base_cost", 1: "conditional_peak", 2: "cleared_share_rt_wall", 3: "faststart_pool"}


def _marginal_rows(
    state: dict,
    marks: dict,
    universe: pd.DataFrame,
    owner: np.ndarray,
    top: np.ndarray,
    model_price: np.ndarray,
) -> dict:
    """Q2/Q3 — identify the marginal row at each gap hour, two methods."""
    fa = state["fleet_arrays"]
    mc_bid = marks["mc_bid"]
    avail = fa.pmax[:, None] * fa.availability  # (n_gen, T)
    groups = universe["group"].to_numpy()
    thermal_rows = np.asarray(
        [g in GEN_THERMAL_GROUPS for g in groups], dtype=bool
    )
    ch = pd.read_parquet(HOURLY / f"class_hourly_{YEAR}.parquet")
    ch = ch[ch["pass"] == "P1"]
    present = [k for k in SIDECAR_THERMAL_CLASSES if k in set(ch["klass"])]
    th = (
        ch[ch["klass"].isin(present)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(8760))
        .to_numpy(float)
    )
    # class utilisation at the gap hours (verifies the FINDING §3 statistics)
    util = {}
    cls_avail = defaultdict(lambda: np.zeros(8760))
    for g in range(len(groups)):
        if thermal_rows[g]:
            cls_avail[groups[g]] += avail[g, :]
    cls_disp = {
        k: ch[ch["klass"] == k].groupby("hour")["mw"].sum().reindex(range(8760)).to_numpy(float)
        for k in present
    }
    merit = []
    bracket = []
    for t in top:
        rows = np.where(thermal_rows & (avail[:, t] > 1e-6))[0]
        order = rows[np.argsort(mc_bid[rows, t], kind="stable")]
        cum = np.cumsum(avail[order, t])
        target = th[t]
        k = int(np.searchsorted(cum, target))
        k = min(k, len(order) - 1)
        g_m = int(order[k])
        merit.append(
            {
                "hour": int(t),
                "g": g_m,
                "bid": float(mc_bid[g_m, t]),
                "class": groups[g_m],
                "suffix": universe["suffix"].iloc[g_m],
                "owner": OWNER_NAMES[int(owner[g_m, t])],
                "model_price": float(model_price[t]),
                "thermal_target_mw": float(target),
            }
        )
        # price-bracket: nearest bid to the model's own load-weighted price
        d = np.abs(mc_bid[rows, t] - model_price[t])
        g_b = int(rows[int(np.argmin(d))])
        bracket.append(
            {
                "hour": int(t),
                "g": g_b,
                "bid": float(mc_bid[g_b, t]),
                "abs_dev": float(d.min()),
                "class": groups[g_b],
                "suffix": universe["suffix"].iloc[g_b],
                "owner": OWNER_NAMES[int(owner[g_b, t])],
            }
        )
    mf = pd.DataFrame(merit)
    bf = pd.DataFrame(bracket)

    def _attrib(df: pd.DataFrame) -> dict:
        return {
            "by_class": df["class"].value_counts().to_dict(),
            "by_owner": df["owner"].value_counts().to_dict(),
            "by_class_owner": {
                f"{c}|{o}": int(n)
                for (c, o), n in df.groupby(["class", "owner"]).size().items()
            },
            "median_bid": round(float(df["bid"].median()), 2),
            "mean_bid": round(float(df["bid"].mean()), 2),
        }

    for k in present:
        av = cls_avail.get(k)
        if av is None or np.nansum(av[top]) <= 0:
            # sidecar classes with no direct generator-group twin (e.g. the
            # COAL split) are reported under the generator-group census below
            continue
        util[k] = round(float(np.nansum(cls_disp[k][top]) / np.nansum(av[top])), 4)
    # generator-group-grain utilisation (matches FINDING §3's COAL/CT/CC stats)
    util_groups = {}
    for grp in sorted(set(groups[thermal_rows])):
        rows_g = np.where(groups == grp)[0]
        a = avail[rows_g][:, top].sum()
        if a <= 0:
            continue
        sidecar_keys = {
            "COAL": ["COAL_LIGNITE", "COAL_PRB"],
        }.get(grp, [grp])
        d = sum(np.nansum(cls_disp[k][top]) for k in sidecar_keys if k in cls_disp)
        util_groups[grp] = round(float(d / a), 4)
    return {
        "merit_crossing": _attrib(mf),
        "price_bracket": _attrib(bf),
        "bracket_median_abs_dev": round(float(bf["abs_dev"].median()), 3),
        "merit_bid_vs_price_median_dev": round(
            float((mf["bid"] - mf["model_price"]).abs().median()), 2
        ),
        "class_utilisation_at_gap_hours": util_groups,
        "sidecar_class_utilisation": util,
        "per_hour_merit": merit,
        "per_hour_bracket": bracket,
    }


def _stack_census(
    state: dict,
    marks: dict,
    universe: pd.DataFrame,
    owner: np.ndarray,
    top: np.ndarray,
) -> dict:
    """Q4 — available-MW-by-price-band census of the gap-hour bid stack."""
    fa = state["fleet_arrays"]
    mc_bid = marks["mc_bid"]
    avail = fa.pmax[:, None] * fa.availability
    groups = universe["group"].to_numpy()
    thermal_rows = np.asarray([g in GEN_THERMAL_GROUPS for g in groups], dtype=bool)
    bands = {}
    for lo, hi in zip(PRICE_BANDS[:-1], PRICE_BANDS[1:]):
        key = f"{int(lo)}-{'inf' if np.isinf(hi) else int(hi)}"
        sel_mw = np.zeros(4)
        tot = 0.0
        for t in top:
            in_band = thermal_rows & (mc_bid[:, t] >= lo) & (mc_bid[:, t] < hi)
            mw = avail[:, t] * in_band
            tot += mw.sum()
            for o in range(4):
                sel_mw[o] += mw[owner[:, t] == o].sum()
        bands[key] = {
            "mean_mw": round(float(tot / len(top)), 1),
            "by_owner_mean_mw": {
                OWNER_NAMES[o]: round(float(sel_mw[o] / len(top)), 1) for o in range(4)
            },
        }
    max_bid = {}
    for grp in sorted(set(groups[thermal_rows])):
        rows_g = np.where((groups == grp) & thermal_rows)[0]
        max_bid[grp] = round(float(mc_bid[rows_g][:, top].max()), 2)
    return {"bands": bands, "max_bid_by_group": max_bid}


def _rel_clamp_census(
    universe: pd.DataFrame, geom: dict, gas_mean: float
) -> dict:
    """Q4 mechanics — what multiplier can each walled row actually reach in bin 6.

    The wall interpolates ``rel = (share_mid - boundary) / (1 - boundary)`` onto
    the p10..p90 quantile ladder; ``np.interp`` clamps above p90. This census
    reports, per class, the MW-weighted distribution of walled-row ``rel`` and
    the maximum wall price any row reaches — the direct test of whether the
    ladder's top rung is even reachable, separate from what the rung's value is.
    """
    from market_sim.data.fleet.offer_surfaces import _ERCOT_CLEARED_SHARE_CLASS_OF

    ladder_q = geom["ladder_q"]
    out = {}
    B = 6  # the top net-load bin (>= p97), where the gap hours live
    for grp, cls in _ERCOT_CLEARED_SHARE_CLASS_OF.items():
        bnd = float(geom["boundary"][cls][B])
        rtw = geom["rt_ladder"][cls][B]
        econ = universe[
            (universe["group"] == grp)
            & universe["suffix"].str.startswith("econ")
        ].copy()
        if econ.empty:
            continue
        above = econ[econ["share_mid"] > bnd].copy()
        above["rel"] = (above["share_mid"] - bnd) / (1.0 - bnd)
        above["mult"] = np.interp(above["rel"], ladder_q, rtw)
        above["target_usd"] = above["mult"] * gas_mean
        seg_edges = [0.0, 0.1, 0.3, 0.5, 0.7, 0.9, 1.01]
        seg_mw = []
        for lo, hi in zip(seg_edges[:-1], seg_edges[1:]):
            m = above[(above["rel"] >= lo) & (above["rel"] < hi)]["pmax"].sum()
            seg_mw.append(round(float(m), 1))
        out[grp] = {
            "boundary_bin6": bnd,
            "rt_ladder_bin6_mult": [round(float(x), 2) for x in rtw],
            "rt_ladder_bin6_usd_at_gap_gas": [
                round(float(x * gas_mean), 1) for x in rtw
            ],
            "n_econ_rows": int(len(econ)),
            "n_above_boundary": int(len(above)),
            "mw_above_boundary": round(float(above["pmax"].sum()), 1),
            "mw_by_rel_segment": dict(
                zip(
                    ["0-0.1", "0.1-0.3", "0.3-0.5", "0.5-0.7", "0.7-0.9", "0.9-1.0"],
                    seg_mw,
                )
            ),
            "max_rel": round(float(above["rel"].max()), 4),
            "max_mult_reached": round(float(above["mult"].max()), 2),
            "max_target_usd": round(float(above["target_usd"].max()), 1),
            "mw_reaching_p90_rung": round(
                float(above[above["rel"] >= 0.9]["pmax"].sum()), 1
            ),
            "mw_weighted_mean_mult": round(
                float((above["mult"] * above["pmax"]).sum() / above["pmax"].sum()), 2
            )
            if len(above)
            else None,
        }
    return out


def _corpus_conditioned_ladder(
    top: np.ndarray, bin6_hours: np.ndarray, ordc: pd.DataFrame
) -> dict:
    """Part C — the corpus's own spare-offer ladder AT the gap hours.

    Reuses the derive's loaders/segment construction verbatim
    (``derive_ercot_sced_offer_wall``): ON-status merchant gas, Base Point ->
    HASL SCED2 segments, effective-HR multiplier = price / delivered-gas day.
    Conditions the MW-weighted quantiles on (a) the top-100 gap hours and
    (b) the remaining bin-6 hours, and reports the pooled artifact rungs for
    contrast — the wash-out measurement.
    """
    from derive_ercot_dam_cleared_share import _gas_day_series, _netload_pct
    from derive_ercot_sced_offer_wall import (
        CLASS_OF_RESTYPE,
        NETLOAD_PCT_EDGES,
        _READ_COLS,
        _chunk_segments,
        _coerce_sced_numeric,
        _delivery_year_rows,
        _sced_source_files,
        _weighted_quantiles,
    )

    gas_day = _gas_day_series()
    pct = _netload_pct(YEAR)
    edges = np.asarray(NETLOAD_PCT_EDGES)
    hour_bin = np.searchsorted(edges, pct, side="right")
    top_set = set(int(h) for h in top)
    bin6_set = set(int(h) for h in bin6_hours)
    keep_hours = top_set | bin6_set

    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR

    def _seg_hoy(seg: pd.DataFrame) -> pd.DataFrame:
        # _chunk_segments returns cls/bin/mult/mw/ts/day (hoy is internal);
        # recompute hour-of-year from the retained ``ts`` stamp, the derive's
        # own CPT -> fixed-CST -> non-leap-clock construction.
        ts = pd.to_datetime(seg["ts"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert("Etc/GMT+6")
        mo = cst.dt.month.to_numpy()
        dy = cst.dt.day.to_numpy()
        hh = cst.dt.hour.to_numpy()
        ok = ~((mo == 2) & (dy == 29))
        seg = seg.loc[np.asarray(ok)].copy()
        seg["hoy"] = _MONTH_START_HOUR[mo[ok] - 1] + (dy[ok] - 1) * 24 + hh[ok]
        return seg

    files = _sced_source_files(YEAR)
    acc: list[pd.DataFrame] = []
    n_files = 0
    for path in files:
        df = pd.read_parquet(path, columns=_READ_COLS)
        df = _delivery_year_rows(df, YEAR)
        df = df[df["Resource Type"].isin(CLASS_OF_RESTYPE)]
        stat = df["Telemetered Resource Status"].astype(str).str.strip()
        df = _coerce_sced_numeric(df[stat.str.startswith("ON")].copy())
        seg = _chunk_segments(df, gas_day, hour_bin)
        del df
        n_files += 1
        if seg.empty:
            continue
        # Filter to the target hours PER SHARD so the accumulator never holds
        # the full year of segments (the derive's own streaming discipline).
        seg = _seg_hoy(seg)
        seg = seg[seg["hoy"].isin(keep_hours)]
        if not seg.empty:
            acc.append(seg)
    seg = (
        pd.concat(acc, ignore_index=True)
        if acc
        else pd.DataFrame(columns=["cls", "bin", "mult", "mw", "ts", "day", "hoy"])
    )

    lam = ordc["system_lambda"].reindex(range(8760)).to_numpy(float)
    gd = _gas_day(YEAR)

    def _ladder(sub: pd.DataFrame) -> dict:
        out = {}
        for cls, grp in sub.groupby("cls"):
            qs = _weighted_quantiles(
                grp["mult"].to_numpy(float), grp["mw"].to_numpy(float), EXT_QUANTILES
            )
            n_iv = grp["ts"].nunique()
            out[cls] = {
                "quantiles": {
                    f"p{int(q*100)}": round(float(v), 2)
                    for q, v in zip(EXT_QUANTILES, qs)
                },
                "max_mult": round(float(grp["mult"].max()), 2),
                "n_intervals": int(n_iv),
                "n_hours": int(grp["hoy"].nunique()),
                "mean_spare_gw": round(
                    float(grp.groupby("ts")["mw"].sum().mean() / 1e3), 3
                ),
            }
        return out

    gap_seg = seg[seg["hoy"].isin(top_set)]
    rest_seg = seg[seg["hoy"].isin(bin6_set - top_set)]

    # per-hour SCED-optimality check: spare p10 vs lambda/gas at the gap hours
    per_hour = []
    for hoy, grp in gap_seg.groupby("hoy"):
        qs = _weighted_quantiles(
            grp["mult"].to_numpy(float), grp["mw"].to_numpy(float), (0.1, 0.5)
        )
        per_hour.append(
            {
                "hoy": int(hoy),
                "spare_p10_mult": round(float(qs[0]), 2),
                "spare_p50_mult": round(float(qs[1]), 2),
                "lambda_over_gas": round(float(lam[hoy] / gd[hoy]), 2)
                if np.isfinite(lam[hoy])
                else None,
                "spare_gw": round(float(grp.groupby("ts")["mw"].sum().mean() / 1e3), 3),
            }
        )
    ph = pd.DataFrame(per_hour)
    corr = None
    if len(ph) > 3 and ph["lambda_over_gas"].notna().sum() > 3:
        corr = round(
            float(ph[["spare_p10_mult", "lambda_over_gas"]].dropna().corr().iloc[0, 1]),
            3,
        )
    return {
        "n_files_read": n_files,
        "gap_hours_ladder": _ladder(gap_seg),
        "bin6_rest_ladder": _ladder(rest_seg),
        "per_hour_gap": per_hour,
        "spare_p10_vs_lambda_corr": corr,
        "gap_hours_covered": int(gap_seg["hoy"].nunique()),
        "bin6_rest_hours_covered": int(rest_seg["hoy"].nunique()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--top-n", type=int, default=100)
    ap.add_argument(
        "--skip-corpus",
        action="store_true",
        help="skip Part C (the SCED corpus scan) for fast iteration",
    )
    args = ap.parse_args()

    model, load, actual, ordc = _system_series()
    top, hour_stats = _hour_set(model, load, actual, ordc, args.top_n)
    print(
        f"[A] top-{args.top_n}: gap share {hour_stats['gap_share_pct']}%, "
        f"actual mean ${hour_stats['actual_mean']}, model ${hour_stats['model_mean']}, "
        f"lambda ${hour_stats['lambda_mean']}, Aug/Sep {hour_stats['n_aug_sep']}"
    )

    state = _reconstruct()
    marks = _compose_markups(state)
    geom = _wall_geometry(state["config"], marks["net_load"])
    universe = _row_universe(state, marks)
    owner = _owner_matrix(marks)
    gd = _gas_day(YEAR)
    gas_mean = float(gd[top].mean())

    # Q1 — bin membership, both geometries
    hb = geom["hour_bin"]
    from derive_ercot_dam_cleared_share import _netload_pct

    eia_bin = np.searchsorted(
        np.asarray(geom["edges"]), _netload_pct(YEAR), side="right"
    )
    q1 = {
        "apply_time_model_bins": {
            int(b): int(c) for b, c in zip(*np.unique(hb[top], return_counts=True))
        },
        "derive_time_eia930_bins": {
            int(b): int(c) for b, c in zip(*np.unique(eia_bin[top], return_counts=True))
        },
        "bin_agreement_pct": round(float((hb[top] == eia_bin[top]).mean() * 100), 1),
        "n_bin6_hours_year_model": int((hb == 6).sum()),
        "n_bin6_hours_year_eia930": int((eia_bin == 6).sum()),
        "top100_share_of_bin6_model": round(
            float((hb[top] == 6).sum() / max((hb == 6).sum(), 1)), 3
        ),
        "gas_day_mean_at_gap_hours": round(gas_mean, 3),
        "rt_ladder_bin6_usd": {
            cls: [round(float(m * gas_mean), 1) for m in geom["rt_ladder"][cls][6]]
            for cls in ("CC", "CT")
        },
        "rt_ladder_bin5_usd": {
            cls: [round(float(m * gas_mean), 1) for m in geom["rt_ladder"][cls][5]]
            for cls in ("CC", "CT")
        },
    }
    print(f"[Q1] model-geometry bins of top100: {q1['apply_time_model_bins']}; "
          f"EIA930 bins: {q1['derive_time_eia930_bins']}; agree {q1['bin_agreement_pct']}%")

    q23 = _marginal_rows(state, marks, universe, owner, top, model)
    print(f"[Q2] merit-crossing owner counts: {q23['merit_crossing']['by_owner']}")
    print(f"[Q3] merit-crossing class counts: {q23['merit_crossing']['by_class']}")
    print(f"[Q3] class utilisation at gap hours: {q23['class_utilisation_at_gap_hours']}")

    q4 = {
        "stack_census": _stack_census(state, marks, universe, owner, top),
        "rel_clamp": _rel_clamp_census(universe, geom, gas_mean),
        "pool_bin6": {
            "pool_frac": float(geom["pool_frac"][6]),
            "boundary": round(float(1.0 - geom["pool_frac"][6]), 4),
            "ladder_usd_at_gap_gas": [
                round(float(m * gas_mean), 1) for m in geom["pool_ladder"][6]
            ],
        },
    }
    band_summary = {
        k: v["mean_mw"] for k, v in q4["stack_census"]["bands"].items()
    }
    print(f"[Q4] bands (mean MW at gap hours): {band_summary}")
    for grp, r in q4["rel_clamp"].items():
        print(
            f"[Q4] {grp}: {r['mw_above_boundary']} MW above bnd {r['boundary_bin6']}, "
            f"max rel {r['max_rel']}, max wall target ${r['max_target_usd']}, "
            f"MW at p90 rung: {r['mw_reaching_p90_rung']}"
        )

    part_c = None
    if not args.skip_corpus:
        bin6_hours = np.where(hb == 6)[0]
        part_c = _corpus_conditioned_ladder(top, bin6_hours, ordc)
        print(
            f"[C] gap-hour CC ladder: {part_c['gap_hours_ladder'].get('CC', {}).get('quantiles')}"
        )
        print(
            f"[C] gap-hour CT ladder: {part_c['gap_hours_ladder'].get('CT', {}).get('quantiles')}"
        )
        print(f"[C] spare-p10 vs lambda/gas corr: {part_c['spare_p10_vs_lambda_corr']}")

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot161_afternoon_wall_phase0.py",
            "session": "ercot-161 Phase 0 (no LP, no solve)",
            "bundle": str(BUNDLE.relative_to(REPO)),
            "keeper": "2026-08-03-ercot158-pool-arm",
            "year": YEAR,
            "finding": "results/calibration/FINDING-ercot-2023-summer-underrun-2026-08-04.md",
        },
        "hour_set": hour_stats,
        "q1_bin_resolution": q1,
        "q2_q3_marginal_rows": {
            k: v
            for k, v in q23.items()
            if k not in ("per_hour_merit", "per_hour_bracket")
        },
        "q2_per_hour_merit": q23["per_hour_merit"],
        "q4_ceiling_rungs": q4,
        "part_c_corpus": part_c,
    }
    args.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()

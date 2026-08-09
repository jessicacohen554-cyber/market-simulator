"""ercot-181 §5 M-0/M-1: the build-free geometric reach of the position-tail form.

Pre-registered in PRECOMMIT-ercot181-quantity-position-2026-08-09.md §5 and run
FIRST (before the §1 corpus instrument): from the keeper control bundle state
and the FROZEN artifacts only — no corpus read, no new artifact, no
ScenarioConfig field, no LP.

QUESTION: can form α (the p90→p100 position-tail completion of the wall and
pool ladders, read at each row's own ``rel``) change ANY row-hour whose control
P1 bid sits at/below the control price? ``np.interp`` end-clamps at the p90
grid point, so the ONLY row-hours form α can change are those with rel > 0.9;
every such row-hour's tail is CONSERVATIVELY assumed nonempty (corpus-free —
an empty measured tail could only shrink the changed set, so inertness proven
here holds a fortiori).

M-1 (fixed ex ante): form α is PROVABLY INERT iff for EVERY candidate row-hour
in EVERY year, ``mc_base + composed_markup`` (the control P1 bid EXCLUDING
startup amortization — a LOWER bound on the true bid, the conservative side
for an inertness claim) exceeds the control bundle's stored zonal price for
the row's zone by more than $1 (the degeneracy margin; a row within $1 counts
LIVE). Raising the cost of an LP variable at bound with strictly positive
reduced cost keeps the identical primal solution and duals. The stored sidecar
``price`` is used as-is (it carries any scored adders — a HIGHER comparator
than the LP energy dual, again the conservative side: it can only push
row-hours toward LIVE).

VALIDATION (stop-the-line on failure): the probe recomputes both members' row
geometry (within-plant midpoints, per-bin boundaries, rel) and reproduces the
gate-off composed wall and pool markups BYTE-IDENTICALLY from
(rel, ladder, gas, caps) against the ``_compose`` mirror — proving the rel map
used to enumerate candidates is the builders' own.

Output: results/calibration/ercot181_positiontail_reach.json.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "scripts" / "data"))

BUNDLE = REPO / "results/calibration/ercot176_control_A"
OUT = REPO / "results/calibration/ercot181_positiontail_reach.json"
YEARS = (2023, 2024, 2025)
LADDER_Q = np.array([0.1, 0.3, 0.5, 0.7, 0.9])
MARGIN_USD = 1.0  # pre-registered degeneracy margin (precommit §5 M-1)
VS = REPO / "data/raw/_validation-source"


def _sp178():
    spec = importlib.util.spec_from_file_location(
        "sp178", REPO / "scripts/probes/ercot178_contpct_seamproof.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gas_day(year: int, hours: int) -> np.ndarray:
    """The wall/pool builders' own delivered-gas day series (mirrored)."""
    from market_sim.config.constants import GAS_BASIS_DIFFERENTIAL
    from market_sim.data.fuel import HENRY_HUB_DAILY_PATH

    hh = pd.read_csv(HENRY_HUB_DAILY_PATH, parse_dates=["date"])
    s = hh.set_index("date")["price_usd_mmbtu"].sort_index()
    full = pd.date_range(
        s.index.min(), s.index.max() + pd.Timedelta(days=14), freq="D"
    )
    daily = s.reindex(full).ffill() + float(GAS_BASIS_DIFFERENTIAL["ERCOT"])
    hour_days = pd.date_range(f"{year}-01-01", periods=hours, freq="h").normalize()
    return daily.reindex(hour_days).ffill().bfill().to_numpy(dtype=float)


def _year_geometry(state: dict, year: int) -> dict:
    """Recompute wall + pool row geometry and reproduce their markups."""
    from market_sim.config.constants import FASTSTART_POOL_MIN_DOWN_HOURS

    sp = _sp178()
    cfg = state["config"]
    fleet = state["fleet"]
    fa = state["fleet_arrays"]
    mc_base = state["mc_base"]
    hours = int(mc_base.shape[1])
    net_load = sp._net_load(state)[:hours]
    gas_day = _gas_day(year, hours)
    pmax = fa.pmax
    mean_mc = mc_base.mean(axis=1)
    voll_cap = float(
        getattr(cfg, "ercot_offer_surface_price_cap_frac", 0.95)
    ) * float(getattr(cfg, "voll", 5000.0))

    dam = json.loads((VS / "ercot_dam_cleared_share_condbinned.json").read_text())
    rt = json.loads((VS / "ercot_sced_offer_wall_condbinned.json").read_text())
    pool = json.loads((VS / "ercot_faststart_pool_condbinned.json").read_text())
    edges = tuple(
        float(x) for x in dam["_provenance"]["netload_pct_edges"]
    )
    n_bins = len(edges) + 1
    thresholds = np.quantile(net_load, edges)
    hour_bin = np.searchsorted(thresholds, net_load, side="right")

    class_of = {"CC_REGULAR": "CC", "CT_PEAKER": "CT"}
    boundaries: dict[str, np.ndarray] = {}
    walls: dict[str, np.ndarray] = {}
    rt_walls: dict[str, np.ndarray] = {}
    for cls_key in set(class_of.values()):
        tbl = dam.get(cls_key, {}).get("years", {}).get(str(year)) or dam.get(
            cls_key, {}
        ).get("pooled")
        if tbl:
            share = np.asarray(tbl.get("cleared_share", ()), dtype=float)
            lad = tbl.get("ladder", ())
            if share.size == n_bins and len(lad) == n_bins:
                boundaries[cls_key] = share
                walls[cls_key] = np.array(
                    [[float(pt[1]) for pt in b] for b in lad], dtype=float
                )
        rtbl = rt.get(cls_key, {}).get("years", {}).get(str(year))
        if rtbl:
            lad = rtbl.get("ladder", ())
            if len(lad) == n_bins:
                rt_walls[cls_key] = np.array(
                    [[float(pt[1]) for pt in b] for b in lad], dtype=float
                )

    # ---- wall reproduction + rel map (state/steam/span all off in keeper) ----
    wall_markup = np.zeros_like(mc_base)
    # rel per (row, bin); NaN = the wall does not floor this row in that bin
    wall_rel = np.full((len(fleet), n_bins), np.nan)
    wall_rt_has = np.zeros((len(fleet), n_bins), dtype=bool)
    prefixes: dict[str, list[int]] = {}
    row_cls: dict[int, str] = {}
    for g, gen in enumerate(fleet):
        cls = getattr(gen, "plant_group", None) or ""
        if cls not in class_of:
            continue
        prefixes.setdefault(gen.unit_id.rpartition("_")[0], []).append(g)
        row_cls[g] = cls
    for rows in prefixes.values():
        rows_arr = np.asarray(rows, dtype=int)
        order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
        caps = pmax[order]
        total = caps.sum()
        if total <= 0.0:
            continue
        cum = np.cumsum(caps)
        mids = (cum - 0.5 * caps) / total
        for g, s_g in zip(order, mids):
            sfx = fleet[g].unit_id.rpartition("_")[2]
            if not sfx.startswith("econ"):
                continue
            cls_key = class_of[row_cls[g]]
            if cls_key not in boundaries:
                continue
            bnd = boundaries[cls_key]
            wall = walls[cls_key]
            rtw = rt_walls.get(cls_key)
            mult_b = np.zeros(n_bins)
            rt_mult_b = np.zeros(n_bins)
            rt_has = np.zeros(n_bins, dtype=bool)
            for b in range(n_bins):
                if not np.isfinite(bnd[b]) or bnd[b] >= 1.0 or s_g <= bnd[b]:
                    continue
                rel = (s_g - bnd[b]) / (1.0 - bnd[b])
                if np.isfinite(wall[b]).all():
                    mult_b[b] = float(np.interp(rel, LADDER_Q, wall[b]))
                    wall_rel[g, b] = rel
                if rtw is not None and np.isfinite(rtw[b]).all():
                    rt_mult_b[b] = float(np.interp(rel, LADDER_Q, rtw[b]))
                    rt_has[b] = True
                    wall_rel[g, b] = rel
            if not mult_b.any() and not rt_has.any():
                continue
            wall_rt_has[g] = rt_has
            mult_h = mult_b[hour_bin]
            target = np.minimum(mult_h * gas_day, voll_cap)
            row = np.maximum(0.0, target - mc_base[g, :])
            if rt_has.any():
                rt_target = np.minimum(rt_mult_b[hour_bin] * gas_day, voll_cap)
                rt_row = np.maximum(0.0, rt_target - mc_base[g, :])
                rt_row = np.where(rt_has[hour_bin], rt_row, 0.0)
                row = np.where(rt_has[hour_bin], rt_row, row)  # mode "replace"
            if row.any():
                wall_markup[g, :] = row

    # ---- pool reproduction + rel map (span off in keeper) ----
    pool_tbl = pool.get("CT", {}).get("years", {}).get(str(year))
    pool_markup = np.zeros_like(mc_base)
    pool_mask = np.zeros_like(mc_base, dtype=bool)
    pool_rel = np.full((len(fleet), n_bins), np.nan)
    if pool_tbl:
        frac = np.asarray(pool_tbl.get("pool_frac", ()), dtype=float)
        lad = pool_tbl.get("ladder", ())
        if frac.size == n_bins and len(lad) == n_bins:
            pool_bnd = 1.0 - np.clip(frac, 0.0, 1.0)
            pool_wall = np.array(
                [[float(pt[1]) for pt in b] for b in lad], dtype=float
            )
            for rows in prefixes.values():
                rows_arr = np.asarray(rows, dtype=int)
                if row_cls.get(int(rows_arr[0])) != "CT_PEAKER":
                    continue
                order = rows_arr[np.argsort(mean_mc[rows_arr], kind="stable")]
                caps = pmax[order]
                total = caps.sum()
                if total <= 0.0:
                    continue
                cum = np.cumsum(caps)
                mids = (cum - 0.5 * caps) / total
                for g, s_g in zip(order, mids):
                    gen = fleet[g]
                    if (
                        float(getattr(gen, "min_down_hours", 0) or 0)
                        > FASTSTART_POOL_MIN_DOWN_HOURS
                    ):
                        continue
                    sfx = gen.unit_id.rpartition("_")[2]
                    if not (sfx.startswith("econ") or sfx.startswith("peak")):
                        continue
                    mult_b = np.zeros(n_bins)
                    has_b = np.zeros(n_bins, dtype=bool)
                    for b in range(n_bins):
                        pb = pool_bnd[b]
                        if not np.isfinite(pb) or pb >= 1.0 or s_g <= pb:
                            continue
                        if not np.isfinite(pool_wall[b]).all():
                            continue
                        rel = (s_g - pb) / (1.0 - pb)
                        mult_b[b] = float(np.interp(rel, LADDER_Q, pool_wall[b]))
                        has_b[b] = True
                        pool_rel[g, b] = rel
                    if not has_b.any():
                        continue
                    mult_h = mult_b[hour_bin]
                    mask = has_b[hour_bin]
                    target = np.minimum(mult_h * gas_day, voll_cap)
                    row = np.maximum(0.0, target - mc_base[g, :])
                    pool_markup[g, :] = np.where(mask, row, 0.0)
                    pool_mask[g, :] = mask

    return {
        "hour_bin": hour_bin,
        "wall_markup": wall_markup,
        "wall_rel": wall_rel,
        "pool_markup": pool_markup,
        "pool_mask": pool_mask,
        "pool_rel": pool_rel,
        "n_bins": n_bins,
    }


def _zone_price(year: int, hours: int, zones: list[str]) -> dict[str, np.ndarray]:
    sysd = pd.read_parquet(BUNDLE / "hourly" / f"system_{year}.parquet")
    sysd = sysd[sysd["pass"] == "P1"]
    out: dict[str, np.ndarray] = {}
    for z in zones:
        s = (
            sysd[sysd["zone"] == z]
            .set_index("hour")["price"]
            .reindex(range(hours))
        )
        out[z] = s.to_numpy(dtype=float)
    return out


# Control-path integrity reference: the ercot-178 seam proof's recorded
# gate-off compose shas (ercot178_contpct_seamproof.json, SP2), re-verified
# by ercot-180 at its HEAD. A mismatch at THIS HEAD is stop-the-line.
CONTROL_COMPOSE_SHA = {
    2023: "25a4ba697e5902616dff9528c124a6f600d73d3530044087536f38ac7a579567",
    2024: "4dfdad090e2ef7f77333c2029b2007029c43ad00084f40c924de5a2ed7d87a76",
    2025: "c9caf9dedb193ae5ef6fb8b0287ef6f48d57fac2257d5ebdf9e20710e9e44656",
}


def run_year(year: int) -> dict:
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    sp = _sp178()
    state, _meta = reconstruct_bundle_fleet(
        BUNDLE, year, required_flags=sp.ERCOT_REQUIRED_FLAGS, required_sequences=()
    )
    composed, own_mask, parts = sp._compose(state, state["config"], year)
    geo = _year_geometry(state, year)

    rec: dict = {"year": year}
    rec["control_composed_sha"] = sp._sha(composed)
    rec["control_sha_matches_ercot178"] = (
        rec["control_composed_sha"] == CONTROL_COMPOSE_SHA.get(year)
    )
    # ---- validation: byte-identical member reproduction (stop-the-line) ----
    wall_ok = (
        parts["wall"] is None and not geo["wall_markup"].any()
    ) or np.array_equal(parts["wall"], geo["wall_markup"])
    pool_ok = (
        parts["pool"] is None and not geo["pool_markup"].any()
    ) or (
        np.array_equal(parts["pool"], geo["pool_markup"])
        and np.array_equal(own_mask, geo["pool_mask"])
    )
    rec["wall_reproduced_byte_identical"] = bool(wall_ok)
    rec["pool_reproduced_byte_identical"] = bool(pool_ok)
    if not (wall_ok and pool_ok):
        rec["VERDICT"] = "STOP-THE-LINE: geometry reproduction mismatch"
        return rec

    fleet = state["fleet"]
    mc_base = state["mc_base"]
    hours = int(mc_base.shape[1])
    hour_bin = geo["hour_bin"]
    bid_off = mc_base + (composed if composed is not None else 0.0)
    own = own_mask if own_mask is not None else np.zeros_like(mc_base, dtype=bool)

    # ---- candidate changed row-hours (rel > 0.9; tails assumed nonempty) ----
    wall_hi = np.take_along_axis(
        geo["wall_rel"], hour_bin[None, :].repeat(len(fleet), 0), axis=1
    )
    pool_hi = np.take_along_axis(
        geo["pool_rel"], hour_bin[None, :].repeat(len(fleet), 0), axis=1
    )
    cand = (np.nan_to_num(wall_hi, nan=-1.0) > 0.9) & ~own
    cand |= (np.nan_to_num(pool_hi, nan=-1.0) > 0.9) & own

    zones = sorted({getattr(g, "zone", "") for g in fleet if getattr(g, "zone", "")})
    zprice = _zone_price(year, hours, zones)
    price_row = np.zeros_like(mc_base)
    for g, gen in enumerate(fleet):
        z = getattr(gen, "zone", "")
        price_row[g, :] = zprice.get(z, np.full(hours, np.nan))
    # a row with no zone price match is compared to the max zonal price
    # (conservative toward LIVE)
    maxp = np.nanmax(np.stack(list(zprice.values())), axis=0)
    bad = ~np.isfinite(price_row)
    price_row[bad] = np.broadcast_to(maxp, price_row.shape)[bad]

    margins = bid_off - (price_row + MARGIN_USD)
    live = cand & (margins <= 0.0)
    n_cand = int(cand.sum())
    n_live = int(live.sum())
    rec.update(
        {
            "n_candidate_row_hours": n_cand,
            "n_live_row_hours": n_live,
            "candidate_rows": int((cand.any(axis=1)).sum()),
            "candidate_hours": int((cand.any(axis=0)).sum()),
            "min_margin_usd": float(margins[cand].min()) if n_cand else None,
            "p05_margin_usd": float(np.percentile(margins[cand], 5))
            if n_cand
            else None,
        }
    )
    if n_live:
        gi, ti = np.where(live)
        top = np.argsort(margins[live])[:20]
        rec["live_examples"] = [
            {
                "unit": fleet[int(gi[k])].unit_id,
                "hour": int(ti[k]),
                "bid": float(bid_off[gi[k], ti[k]]),
                "price": float(price_row[gi[k], ti[k]]),
                "bin": int(hour_bin[ti[k]]),
            }
            for k in top
        ]
        rec["live_hours"] = sorted({int(t) for t in ti})[:100]
    # overlap of candidate hours with the frozen top bin (the object)
    top_bin = int(geo["n_bins"]) - 1
    rec["candidate_hours_in_top_bin"] = int(
        (cand.any(axis=0) & (hour_bin == top_bin)).sum()
    )
    rec["VERDICT"] = "LIVE" if n_live else "PROVABLY-INERT"
    return rec


def main() -> int:
    recs = [run_year(y) for y in YEARS]
    stop = any("STOP" in r.get("VERDICT", "") for r in recs)
    inert = all(r.get("VERDICT") == "PROVABLY-INERT" for r in recs)
    record = {
        "probe": "ercot181_positiontail_reach",
        "precommit": "docs/PRECOMMIT-ercot181-quantity-position-2026-08-09.md §5",
        "bundle": str(BUNDLE.relative_to(REPO)),
        "margin_usd": MARGIN_USD,
        "conservative_assumptions": [
            "every rel>0.9 row-hour counted as changeable (measured tails "
            "assumed nonempty — corpus-free; an empty tail only shrinks the "
            "changed set, so inertness proven here holds a fortiori)",
            "control bid excludes P1 startup amortization (lower bound on "
            "the true bid — a lower bound above price proves the true bid "
            "above price)",
            "sidecar stored price used as comparator (>= the LP energy "
            "dual), and rows without a zone price match compare against the "
            "max zonal price",
        ],
        "per_year": recs,
        "M1_VERDICT": (
            "STOP-THE-LINE"
            if stop
            else ("PROVABLY-INERT (Route A)" if inert else "LIVE (Route B)")
        ),
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(json.dumps({k: v for k, v in record.items() if k != "per_year"}, indent=1))
    for r in recs:
        print(
            {
                k: r.get(k)
                for k in (
                    "year",
                    "VERDICT",
                    "n_candidate_row_hours",
                    "n_live_row_hours",
                    "candidate_hours_in_top_bin",
                    "min_margin_usd",
                )
            }
        )
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

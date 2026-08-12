"""miso-153 Phase 0 — WHY does MISO keep cheap capacity available at its summer
peak? NO LP solve; the fleet is assembled through the production chain at HEAD
under the keeper's OWN ``run_config.json`` and interrogated against the keeper's
OWN committed ``hourly/`` sidecars.

Pre-registration (pushed at ``857a434`` BEFORE this probe ran):
``results/calibration/PREREG-miso153-summer-peak-phase0-2026-08-12.md``.

The object (PREREG §1): the model's Jun+Jul p99/max sit BELOW its own
rest-of-year p99/max — it forms no summer peak — while its demand shape is
correct. Something keeps cheap capacity available at the top of the load.

Statistics, in the pre-registered order:

  D-1  SUMMER CUSHION: at the top-200 model-demand hours, available
       ``Σ pmax × availability`` vs the keeper's committed dispatch, per class.
       Idle headroom in GW and as a share of available.
  D-2  AVAILABILITY SEASONALITY: cap-weighted mean availability by class by
       month; Jun+Jul minus annual, in pp. ITS "WIN" IS A STOP (branch P-D) —
       MISO's outage extract is un-re-tuned (X_cc = 0.240) and re-tuning it
       needs a cross-ISO charter this lane cannot self-authorize.
  D-3  MARGINAL IDENTITY: at the top-200 hours, the price-setting band (the
       dearest available mc at or below the zonal price), plus the mc census of
       idle capacity in the $0-20/MWh band just above the clearing price.
  D-4  RESERVE BINDING: per family, Jun+Jul hours with dual > $0.01 and with
       shortfall > 0, against the rest-of-year contrast.
  IMP  IMPORTS AT PEAK (confirmatory): model ``import``-class MW at the top-200
       hours vs its annual mean and vs assembled import capability.

Gating is T-6 only (PREREG §5): the keeper's own committed dispatch must be
<= the reconstructed available MW. T-6b (price-taking reconstruction vs
``class_hourly``) is an ADDITION beyond the PREREG, carried over from
miso-152's own pre-registered bar; it is labelled as such wherever reported.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 only; MISO holds no marker.

Usage::

    PYTHONPATH=$PWD .venv/bin/python scripts/probes/_miso153_summer_cushion.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

# T-1: the miso-134 module is HARD-WIRED to miso132_ccmin_B. This session's
# keeper is miso-148, so the bundle is REPOINTED before any helper runs —
# inheriting miso-132's config would silently screen the wrong keeper.
# Asserted, never assumed.
BUNDLE = REPO / "results/calibration/miso148_basis_B"
if not (BUNDLE / "run_config.json").is_file():
    raise SystemExit(f"T-1 FAIL: keeper bundle missing: {BUNDLE}")
_m134.BUNDLE = BUNDLE

from _miso134_ct_night_order_screen import (  # noqa: E402
    build_year,
    keeper_config,
    keeper_prices,
)

OUT = REPO / "results/calibration/_miso153_summer_cushion.json"
YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years touched anywhere below

# T-5: the six CARRY zones. MISO_external / MISO_external_South are IMPORT
# NODES and are excluded from every price/demand aggregate; they appear only in
# the import statistic.
CARRY_ZONES = (
    "MISO-East",
    "MISO-Illinois",
    "MISO-Indiana",
    "MISO-Plains",
    "MISO-South",
    "MISO-West",
)
IMPORT_NODES = ("MISO_external", "MISO_external_South")

TOPN = 200  # PREREG §2: the peak window, fixed before measurement

# PREREG §3 D-1 scope: the dispatchable thermal set. COAL is POOLED (see T-9).
GAS_CLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
COAL_CLASSES = ("COAL_BIT", "COAL_PRB", "COAL_LIGNITE", "COAL_WC", "COAL")
COAL_POOL = "COAL_FAMILY"

MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])
JUNJUL = (MO == 6) | (MO == 7)

T6_CELL_TOL = 0.01     # PREREG: violations <= 1 % of (class x hour) cells
T6_MAG_TOL = 0.02      # PREREG: max violation <= 2 % of assembled class cap
T6B_TOL = 0.10         # ADDITION (miso-152's own bar): +-10 % of class energy
T7_OIL_TOL = 0.005     # PREREG: oil > 0.5 % of thermal dispatch => pool
IDLE_BAND = 20.0       # D-3: the $/MWh band just above the clearing price


def _band_of(unit_id: str) -> str:
    """Return the tranche band suffix of a per-plant unit id, or ``""``.

    Raises nothing and defaults nothing on a REQUIRED field (T-2); the raw
    suffix inventory is dumped separately by :func:`suffix_inventory` so a
    collapse cannot hide behind a tidy label (T-3).
    """
    m = re.search(r"_p(\d+)_([a-z0-9_]+)$", unit_id)
    return m.group(2) if m else ""


def _band_family(suffix: str) -> str:
    """Collapse a raw suffix to its band family (mustrun/committed/econ/peak)."""
    for key in ("mustrun", "committed", "econ", "peak"):
        if suffix.startswith(key):
            return key
    return suffix or "?"


def class_label(g) -> str:
    """Return the ``class_hourly`` klass for one assembled generator.

    Mirrors ``run_calibration_full._dispatch_frame``: non-ERCOT fleets class by
    ``plant_group``. COAL is POOLED here rather than split by
    ``coal_supply_class`` (T-9): the split exists only to name the coal rank,
    and pooling both sides is exactly equivalent for D-1's totals while
    removing a fragile mapping. The fleet's own ``coal_supply`` inventory is
    reported separately.

    Fields are read DIRECTLY — a silent ``getattr`` default on the offer path
    IS the bug (T-2).
    """
    group = str(g.plant_group or "")
    return COAL_POOL if group == "COAL" else group


def keeper_class_hourly(year: int) -> pd.DataFrame:
    """Return the keeper's committed P1 (klass x hour) dispatch MW frame."""
    ch = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    ch = ch[ch["pass"] == "P1"]
    wide = ch.pivot_table(index="klass", columns="hour", values="mw",
                          observed=True, aggfunc="sum").fillna(0.0)
    full = pd.DataFrame(0.0, index=wide.index, columns=np.arange(8760))
    full.loc[:, wide.columns] = wide
    return full


def pool_coal_rows(ch: pd.DataFrame) -> pd.DataFrame:
    """Pool the coal supply classes of a class_hourly frame into COAL_FAMILY."""
    present = [c for c in COAL_CLASSES if c in ch.index]
    if not present:
        return ch
    pooled = ch.loc[present].sum(axis=0)
    out = ch.drop(index=present)
    out.loc[COAL_POOL] = pooled
    return out


def suffix_inventory(fleet, arrays, labels) -> dict:
    """T-3: the FULL raw band-suffix inventory, per class, before aggregation.

    Dumped so a collapse to one-tranche-per-band (which keeps only the DEAREST
    econ sub-tranche and yields a spurious exact 0.0) cannot pass unnoticed.
    """
    rows = []
    for i, g in enumerate(fleet):
        rows.append({"klass": labels[i], "suffix": _band_of(str(g.unit_id)),
                     "pmax": float(arrays.pmax[i])})
    df = pd.DataFrame(rows)
    inv = (df.groupby(["klass", "suffix"], observed=True)
             .agg(n=("pmax", "size"), cap_mw=("pmax", "sum"))
             .reset_index())
    return {
        "n_distinct_suffixes": int(df["suffix"].nunique()),
        "distinct_suffixes": sorted(df["suffix"].unique().tolist()),
        "by_class": {
            k: sub[["suffix", "n", "cap_mw"]].to_dict("records")
            for k, sub in inv.groupby("klass", observed=True)
        },
    }


def run_year(year: int) -> dict:
    """Compute every Phase-0 statistic for one year."""
    cfg = keeper_config()
    price_df, demand = keeper_prices(year)

    # T-5: carry zones only for the price/demand aggregates.
    carry = [z for z in CARRY_ZONES if z in price_df.columns]
    if len(carry) != 6:
        raise SystemExit(f"T-5 FAIL: expected 6 carry zones, got {carry}")

    fleet, arrays, mc = _assemble(cfg, year)
    labels = np.array([class_label(g) for g in fleet], dtype=object)
    zones = np.array([str(g.zone) for g in fleet], dtype=object)

    avail = np.asarray(arrays.availability, dtype=np.float64)
    if avail.ndim == 1:
        avail = np.broadcast_to(avail[:, None], (len(fleet), 8760))
    pmax = np.asarray(arrays.pmax, dtype=np.float64)
    avail_mw = pmax[:, None] * avail            # (n_gen, T) — the LP's own bound

    # PREREG §2: the peak window is the top-200 hours of model ISO demand.
    top = np.argsort(demand)[::-1][:TOPN]
    top = np.sort(top)

    ch = pool_coal_rows(keeper_class_hourly(year))
    fleet_classes = sorted(set(labels.tolist()))

    # ---- T-8: which class_hourly classes have NO assembled fleet capacity? --
    excluded = [c for c in ch.index if c not in fleet_classes]
    tot_disp_top = float(ch.loc[:, top].to_numpy().sum())
    excl_share = float(ch.loc[excluded, top].to_numpy().sum() / tot_disp_top) \
        if excluded else 0.0

    thermal = [c for c in fleet_classes if c in GAS_CLASSES or c == COAL_POOL]

    # ---- D-1 SUMMER CUSHION ------------------------------------------------
    d1 = {}
    for k in thermal:
        sel = labels == k
        av = avail_mw[sel][:, top].sum(axis=0)          # (200,)
        dp = ch.loc[k, top].to_numpy() if k in ch.index else np.zeros(TOPN)
        d1[k] = {
            "assembled_cap_mw": float(pmax[sel].sum()),
            "avail_mw_mean": float(av.mean()),
            "disp_mw_mean": float(dp.mean()),
            "idle_mw_mean": float((av - dp).mean()),
            "idle_share": float((av - dp).sum() / av.sum()) if av.sum() else None,
        }
    av_tot = sum(avail_mw[labels == k][:, top].sum(axis=0) for k in thermal)
    dp_tot = sum(ch.loc[k, top].to_numpy() for k in thermal if k in ch.index)
    d1_total = {
        "avail_gw_mean": float(av_tot.mean() / 1000.0),
        "disp_gw_mean": float(dp_tot.mean() / 1000.0),
        "idle_gw_mean": float((av_tot - dp_tot).mean() / 1000.0),
        "idle_gw_p10": float(np.percentile(av_tot - dp_tot, 10) / 1000.0),
        "idle_gw_p90": float(np.percentile(av_tot - dp_tot, 90) / 1000.0),
        "idle_share": float((av_tot - dp_tot).sum() / av_tot.sum()),
    }

    # ---- T-6 (GATING) feasibility: dispatch <= available --------------------
    cells = viol = 0
    worst = 0.0
    worst_k = ""
    per_class_t6 = {}
    for k in thermal:
        av = avail_mw[labels == k][:, top].sum(axis=0)
        dp = ch.loc[k, top].to_numpy() if k in ch.index else np.zeros(TOPN)
        over = dp - av
        cap = float(pmax[labels == k].sum())
        nv = int((over > 1e-6).sum())
        mx = float(over.max() / cap) if cap else 0.0
        per_class_t6[k] = {"violations": nv, "max_viol_share_of_cap": mx}
        cells += TOPN
        viol += nv
        if mx > worst:
            worst, worst_k = mx, k
    t6 = {
        "cells": cells, "violations": viol,
        "violation_share": viol / cells if cells else 0.0,
        "max_viol_share_of_cap": worst, "worst_class": worst_k,
        "bar_cell": T6_CELL_TOL, "bar_mag": T6_MAG_TOL,
        "per_class": per_class_t6,
    }
    t6["PASS"] = bool(t6["violation_share"] <= T6_CELL_TOL
                      and worst <= T6_MAG_TOL)

    # ---- T-7 dual-fuel re-attribution --------------------------------------
    oil_top = float(ch.loc["oil", top].sum()) if "oil" in ch.index else 0.0
    therm_top = float(sum(ch.loc[k, top].sum() for k in thermal if k in ch.index))
    t7 = {"oil_mwh_top": oil_top, "thermal_mwh_top": therm_top,
          "oil_share_of_thermal": oil_top / therm_top if therm_top else 0.0,
          "bar": T7_OIL_TOL}
    t7["pooling_required"] = bool(t7["oil_share_of_thermal"] > T7_OIL_TOL)

    # ---- D-2 AVAILABILITY SEASONALITY --------------------------------------
    d2 = {}
    for k in thermal:
        sel = labels == k
        cap = pmax[sel]
        if not cap.sum():
            continue
        a = avail[sel]                                   # (n_k, T)
        capw = (a * cap[:, None]).sum(axis=0) / cap.sum()  # (T,) cap-weighted
        ann = float(capw.mean())
        jj = float(capw[JUNJUL].mean())
        d2[k] = {
            "annual": ann, "junjul": jj, "junjul_minus_annual_pp": (jj - ann) * 100,
            "monthly": {int(m): float(capw[MO == m].mean()) for m in range(1, 13)},
        }

    # ---- D-3 MARGINAL IDENTITY ---------------------------------------------
    d3 = _marginal_identity(mc, avail_mw, labels, zones, fleet, price_df,
                            carry, top)

    # ---- T-6b (ADDITION, not pre-registered): reconstruction vs class_hourly
    t6b = {}
    for k in thermal:
        sel = labels == k
        rec = d3["_recon_mw"].get(k)
        dp = ch.loc[k, top].to_numpy() if k in ch.index else np.zeros(TOPN)
        if rec is None or dp.sum() == 0:
            continue
        t6b[k] = {"recon_mwh": float(rec.sum()), "keeper_mwh": float(dp.sum()),
                  "rel_err": float((rec.sum() - dp.sum()) / dp.sum())}
        t6b[k]["within_bar"] = bool(abs(t6b[k]["rel_err"]) <= T6B_TOL)
    d3.pop("_recon_mw")

    # ---- IMPORTS AT PEAK ----------------------------------------------------
    imp_series = ch.loc["import"].to_numpy() if "import" in ch.index \
        else np.zeros(8760)
    imp_sel = np.isin(zones, IMPORT_NODES)
    imp = {
        "annual_mean_mw": float(imp_series.mean()),
        "top200_mean_mw": float(imp_series[top].mean()),
        "top200_max_mw": float(imp_series[top].max()),
        "junjul_mean_mw": float(imp_series[JUNJUL].mean()),
        "assembled_import_node_cap_mw": float(pmax[imp_sel].sum()),
        "assembled_import_avail_mw_top200":
            float(avail_mw[imp_sel][:, top].sum(axis=0).mean())
            if imp_sel.any() else 0.0,
    }
    imp["peak_over_annual"] = (imp["top200_mean_mw"] / imp["annual_mean_mw"]
                               if imp["annual_mean_mw"] else None)
    if imp["assembled_import_avail_mw_top200"]:
        imp["headroom_share_at_peak"] = float(
            1.0 - imp["top200_mean_mw"] / imp["assembled_import_avail_mw_top200"])

    return {
        "n_gen": int(len(fleet)),
        "carry_zones": carry,
        "top200_demand_gw_mean": float(demand[top].mean() / 1000.0),
        "top200_price_mean": float(price_df[carry].to_numpy()[top].mean()),
        "annual_price_mean": float(price_df[carry].to_numpy().mean()),
        "excluded_classes": excluded,
        "excluded_dispatch_share_at_peak": excl_share,
        "suffix_inventory": suffix_inventory(fleet, arrays, labels),
        "D1_by_class": d1, "D1_total": d1_total,
        "D2": d2, "D3": d3, "IMPORTS": imp,
        "T6": t6, "T6b_NOT_PREREGISTERED": t6b, "T7": t7,
    }


def _assemble(cfg, year: int):
    """Run the production chain and return (fleet, arrays, mc_base).

    **T-6 REPAIR (instrument defect found BY the pre-registered T-6 gate, not
    pre-registered itself).** ``_apply_outage_overlays`` keys the unit-level
    CAMPD outage derate on ``config.weather_year``, NOT on the solve year
    (``data/fleet/arrays.py:1091-1092``), while the production backcast pipeline
    pins ``weather_year = year`` per solve year
    (``pipeline/backcast_config.py:1235``). miso-134's ``build_year`` passes one
    config for every year, so the keeper's ``weather_year = 2023`` silently
    applied **2023's outage windows to 2024 and 2025** — the identical-across-
    years D-2 profiles and the 2024/2025 T-6 failures are that defect.
    Reproducing the pipeline's own pin is the repair; both the pre-repair and
    post-repair T-6 magnitudes are reported.
    """
    import dataclasses

    cfg_y = dataclasses.replace(cfg, weather_year=year)
    _raw, fleet, arrays, _fp, mc_base, _zn = build_year(cfg_y, year)
    return fleet, arrays, mc_base


def _marginal_identity(mc, avail_mw, labels, zones, fleet, price_df, carry, top):
    """D-3: the price-setting band at the top-200 hours, per carry zone.

    For each (zone, hour) the price-setting band is the DEAREST available
    tranche whose effective marginal cost is at or below the zonal price. Also
    censuses IDLE capacity in the ``$0-IDLE_BAND`` window just above the price
    — what the price would have had to reach to bring it in.
    """
    suffix = np.array([_band_family(_band_of(str(g.unit_id))) for g in fleet],
                      dtype=object)
    setter: dict[str, float] = {}
    idle_band_mw: dict[str, float] = {}
    recon: dict[str, np.ndarray] = {}
    n_obs = 0
    price_gap = []

    for z in carry:
        zsel = zones == z
        if not zsel.any():
            continue
        mc_z = mc[zsel][:, top]                 # (n_z, 200)
        av_z = avail_mw[zsel][:, top]
        lab_z = labels[zsel]
        suf_z = suffix[zsel]
        p_z = price_df[z].to_numpy()[top][None, :]   # (1, 200)

        in_merit = (mc_z <= p_z + 1e-6) & (av_z > 1e-6)
        # reconstruction (price-taking) for T-6b
        rec_z = np.where(in_merit, av_z, 0.0)
        for k in np.unique(lab_z):
            add = rec_z[lab_z == k].sum(axis=0)
            recon[k] = recon.get(k, np.zeros(len(top))) + add

        # the price-setting band: dearest in-merit mc per hour
        masked = np.where(in_merit, mc_z, -np.inf)
        idx = masked.argmax(axis=0)                       # (200,)
        has = np.isfinite(masked[idx, np.arange(len(top))])
        for h in range(len(top)):
            if not has[h]:
                continue
            key = f"{lab_z[idx[h]]}|{suf_z[idx[h]]}"
            setter[key] = setter.get(key, 0.0) + 1.0
            n_obs += 1
            price_gap.append(float(p_z[0, h] - mc_z[idx[h], h]))

        # idle capacity just above the clearing price
        band = (mc_z > p_z + 1e-6) & (mc_z <= p_z + IDLE_BAND) & (av_z > 1e-6)
        for k in np.unique(lab_z):
            m = band[lab_z == k]
            idle_band_mw[k] = idle_band_mw.get(k, 0.0) + float(
                np.where(m, av_z[lab_z == k], 0.0).sum() / len(top))

    census = {k: v / n_obs for k, v in
              sorted(setter.items(), key=lambda kv: -kv[1])} if n_obs else {}
    return {
        "n_zone_hour_obs": n_obs,
        "setter_census_share": census,
        "setter_class_share": _collapse_class(census),
        "mean_price_minus_setter_mc": float(np.mean(price_gap))
        if price_gap else None,
        "idle_mw_within_20_above_price_by_class": dict(
            sorted(idle_band_mw.items(), key=lambda kv: -kv[1])),
        "idle_gw_within_20_above_price_total":
            sum(idle_band_mw.values()) / 1000.0,
        "_recon_mw": recon,
    }


def _collapse_class(census: dict) -> dict:
    out: dict[str, float] = {}
    for key, share in census.items():
        k = key.split("|")[0]
        out[k] = out.get(k, 0.0) + share
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def read_reserves(year: int) -> dict:
    """D-4: per-family Jun+Jul binding, with the rest-of-year contrast."""
    rf = pd.read_parquet(BUNDLE / f"hourly/reserve_family_{year}.parquet")
    rf = rf[rf["pass"] == "P1"]
    out = {}
    for fam, g in rf.groupby("family", observed=True):
        g = g.sort_values("hour")
        dual = g["dual"].to_numpy()
        short = g["shortfall_mw"].to_numpy()
        hrs = g["hour"].to_numpy()
        jj = np.isin(hrs, np.where(JUNJUL)[0])
        rest = ~jj

        def blk(m):
            return {
                "hours": int(m.sum()),
                "bind_hours": int((np.abs(dual[m]) > 0.01).sum()),
                "bind_share": float((np.abs(dual[m]) > 0.01).mean()),
                "short_hours": int((short[m] > 1e-6).sum()),
                "dual_mean": float(np.abs(dual[m]).mean()),
                "dual_max": float(np.abs(dual[m]).max()),
                "short_max_mw": float(short[m].max()),
                "req_mean_mw": float(g["requirement_mw"].to_numpy()[m].mean()),
                "held_mean_mw": float(g["held_mw"].to_numpy()[m].mean()),
            }
        out[str(fam)] = {"junjul": blk(jj), "rest": blk(rest)}
    return out


def main() -> None:
    cfg_raw = json.loads((BUNDLE / "run_config.json").read_text())["scenario_config"]
    cfg = keeper_config()
    import dataclasses
    names = {f.name for f in dataclasses.fields(cfg)}
    matched = sorted(set(cfg_raw) & names)
    dropped = sorted(set(cfg_raw) - names)
    print(f"[T-1] bundle = {BUNDLE.name}")
    print(f"[T-1] run_config keys matched={len(matched)} dropped={len(dropped)}")
    if dropped:
        print(f"[T-1] dropped keys: {dropped}")

    result = {"bundle": BUNDLE.name, "t1_matched": len(matched),
              "t1_dropped": dropped, "years": {}}
    for y in YEARS:
        print(f"\n===== {y} =====", flush=True)
        r = run_year(y)
        r["D4_reserves"] = read_reserves(y)
        result["years"][str(y)] = r
        print(f"  n_gen={r['n_gen']}  top200 demand "
              f"{r['top200_demand_gw_mean']:.1f} GW  "
              f"price ${r['top200_price_mean']:.2f} "
              f"(annual ${r['annual_price_mean']:.2f})")
        t = r["D1_total"]
        print(f"  D-1 idle {t['idle_gw_mean']:.1f} GW "
              f"({t['idle_share']*100:.1f}% of {t['avail_gw_mean']:.1f} GW avail)")
        print(f"  T-6 {'PASS' if r['T6']['PASS'] else 'FAIL'}  "
              f"viol_share={r['T6']['violation_share']*100:.2f}%  "
              f"max_mag={r['T6']['max_viol_share_of_cap']*100:.2f}% "
              f"({r['T6']['worst_class']})")

    OUT.write_text(json.dumps(result, indent=2, default=float))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

"""pjm-138 M2 (no LP): what SHAPE does the system-energy-price half of the
Dominion CT-hour deficit have?

`FINDING-pjm137` §3 measured the CT-hour price deficit at
**$17.72 / $26.69 / $54.61 /MWh** and attributed 51 / 46 / 51 % of it to
measured congestion its §2/§4 proved is intra-Dominion and unreachable by any
zonal mechanism. §6 lead 2 handed the OTHER half forward: after netting the
measured congestion component out, **$8.63 / $14.37 / $26.88 /MWh** remains,
which a zonal model *could* produce — measured DOM **MEC** runs at a CT-hour p50
of $35.94 / $41.35 / $58.86 against the model's whole Dominion dual at
$32.07 / $32.28 / $42.72.

**PJM's `system_energy_price_da` is RTO-UNIFORM** (verified here: zero spread
across all 23 zonal pnodes in every hour), so that residual is not a Dominion
quantity at all — it is PJM's single system marginal energy price, and the
question is ISO-wide marginal-unit formation. This probe measures its SHAPE,
which is the discriminator the successor charter turns on:

* **diffuse across the whole year** → an offer-stack LEVEL problem (the model's
  merit order is systematically too cheap), or
* **concentrated in the tightest net-load deciles / summer afternoons** → a
  scarcity / reserve / available-supply problem, which is where the G-20b guard
  false-negative lead (~2.8–5.0 GW returned to PJM's tightest quartile,
  `FINDING-guard-falseneg-audit-2026-07-27` §3) would live.

Four measurements, no solve:

* **D1 — the identity decomposition.** The total Dominion price deficit splits
  EXACTLY into a system-energy part and a basis part:

      measured_DOM_LMP − model_DOM_dual
        = (measured_MEC − model_load_weighted_dual)      … system energy
        + (measured_DOM_basis − model_DOM_basis)          … congestion + loss

  where each side's basis is its own zonal price minus its own system/
  load-weighted price. This is an identity, not an attribution choice, and it
  separates the half a zonal model can reach from the half pjm-137 closed.
* **D2 — the shape.** The system-energy gap bucketed by hour-of-day, season,
  and model net-load decile, reported both as a mean $/MWh and as each
  bucket's SHARE of the year's total gap-MWh, so concentration is visible
  rather than inferred from means.
* **D3 — the same, CT-energy-weighted.** Every statistic re-weighted by the
  real Dominion CT fleet's measured CAMPD output (the pjm-137 M3 roster and
  filter, `unitType == 'Combustion turbine'` over the committed benchmark's own
  plant keys), so the shape is read in the hours the chartered defect lives in.
* **D4 — the tail instruments.** Measured-vs-model tail-hour counts on the DA
  basis, the model's own reserve price by decile, and the model's idle-headroom
  proxy — the statistics that decide whether the tail deciles are short of
  price because the stack is cheap or because too much capacity is available.

Committed inputs only, plus the pjm-136 zonal LMP-component intake: the keeper
`hourly/` sidecars (class + system), the CAMPD unit-level record, the committed
benchmark payload, and `data/raw/pjm-zonal-lmp/`. Nothing is written outside
`results/probes/`.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm138_mec_gap_shape.py
    PYTHONPATH=. .venv/bin/python scripts/probes/_pjm138_mec_gap_shape.py \
        --bundle results/calibration/pjm137_ctheatrate_B
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

YEARS = (2023, 2024, 2025)
HOURS = 8760
EXTERNAL_ZONE = "PJM_external"
DOM = "PJM_Dominion"

#: Measured-price bands shared with the pjm-138 M1 marginal-ownership readout so
#: the two tables line up row-for-row.
PRICE_BANDS = ((0.0, 40.0), (40.0, 150.0), (150.0, 1e9))
PRICE_BAND_LABS = ("0-40", "40-150", ">150")

#: Model classes netted out of demand to form the model's own net load. These
#: are the LP's renewable decision variables (rule 3 `[R-RENEW-VAR]`) — they are
#: NOT netted from demand in the LP, so netting them here is a diagnostic
#: construction, matching how the ISO's own net-load statistic is defined.
RENEWABLE_CLASSES = ("wind", "solar")

SEASONS = {"DJF": (12, 1, 2), "MAM": (3, 4, 5), "JJA": (6, 7, 8), "SON": (9, 10, 11)}

OUT_PATH = Path("results/probes/pjm138_mec_gap_shape.json")


def _load_p137():
    """Import the pjm-137 probe as a module so its CAMPD-side roster loader is
    reused verbatim (same benchmark plant keys, same `unitType` filter)."""
    path = REPO / "scripts" / "probes" / "_pjm137_dominion_ct_congestion.py"
    spec = importlib.util.spec_from_file_location("_p137", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


# --------------------------------------------------------------------------
# measured zonal LMP components — keyed in EASTERN STANDARD TIME
# --------------------------------------------------------------------------
# WHY THIS IS NOT `_pjm137_dominion_ct_congestion._measured_components`.
#
# That loader indexes hour-of-year off `datetime_beginning_ept`, PJM's Eastern
# PREVAILING time — which advances one hour relative to standard time from the
# March transition to the November one. The model's 8760 index and the CAMPD
# unit-level record are BOTH Eastern STANDARD time year-round (EPA CAMD
# publishes local standard time; the LP's hour 0 is Jan 1 00:00 EST), so from
# March to November the measured series sits ONE HOUR AHEAD of everything it is
# being compared against. Measured here on 2025:
#
#   corr(measured MEC, model system price)   EST months   DST months
#     EPT key, as pjm-137 indexed it            0.7807      0.7964
#     UTC-5 key (this loader)                   0.7867      0.8731
#
# — the two keys are statistically indistinguishable in the standard-time months
# and separate cleanly in the DST months, which is the signature of exactly this
# offset and of nothing else. Annual and bucket MEANS are shift-invariant (the
# 2025 mean gap is 6.62 under either key, to the cent), so pjm-137's headline
# LEVELS survive; the HOUR-OF-DAY attribution does not, and this probe's whole
# question is shape. Keying on `datetime_beginning_utc` also disposes of the
# DST fall-back collision, where two 01:00 intervals carry one EPT label.
_EST_OFFSET = pd.Timedelta(hours=5)

#: Cumulative hour-of-year at the start of each non-leap month.
_MONTH_START_HOUR = np.cumsum([0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30]) * 24


def _est_hour_of_year(utc: pd.Series, year: int) -> tuple[pd.Series, np.ndarray]:
    """Hour-of-year in Eastern Standard Time for a UTC timestamp column."""
    est = pd.to_datetime(utc, format="mixed") - _EST_OFFSET
    keep = (est.dt.year == year) & ~((est.dt.month == 2) & (est.dt.day == 29))
    e = est[keep]
    hoy = (
        _MONTH_START_HOUR[e.dt.month.to_numpy() - 1]
        + (e.dt.day.to_numpy() - 1) * 24
        + e.dt.hour.to_numpy()
    )
    return keep, hoy


def _measured_reserve_est(year: int) -> dict[str, np.ndarray]:
    """PJM's OWN day-ahead reserve clearing prices, EST hour-of-year index.

    `data/raw/PJM-AS/da_reserve_market_results_<year>.parquet` is PJM's
    published DA reserve market result — one row per (locale, service, hour)
    with the as-enforced requirement, the cleared MW and the market clearing
    price. It is the direct measured counterpart to the model's own reserve
    dual (`system_<year>.parquet::reserve_price`), which is what makes the
    comparison in D5 a measurement rather than an inference.
    """
    path = REPO / "data/raw/PJM-AS" / f"da_reserve_market_results_{year}.parquet"
    frame = pd.read_parquet(
        path,
        columns=["datetime_beginning_utc", "locale", "service", "mcp", "as_req_mw",
                 "total_mw"],
    )
    frame = frame[frame["locale"] == "PJM RTO Reserve Zone"].copy()
    keep, hoy = _est_hour_of_year(frame["datetime_beginning_utc"], year)
    frame = frame[keep].copy()
    frame["hour"] = hoy
    out: dict[str, np.ndarray] = {}
    for svc, tag in (
        ("Synchronized Reserve", "syn"),
        ("Primary Reserve", "pri"),
        ("Thirty Minutes Reserve", "t30"),
    ):
        sub = frame[frame["service"] == svc]
        for col, key in (("mcp", f"{tag}_mcp"), ("as_req_mw", f"{tag}_req"),
                         ("total_mw", f"{tag}_cleared")):
            out[key] = (
                sub.groupby("hour")[col]
                .mean()
                .reindex(range(HOURS))
                .to_numpy(float)
            )
    return out


def _metered_load_est(year: int) -> pd.DataFrame:
    """Metered PJM zonal load (MW), EST hour-of-year index x load-zone code."""
    path = (
        REPO / "data/raw/zone-specific-demand" / f"PJM{year}_hrl_load_metered.csv"
    )
    frame = pd.read_csv(
        path, usecols=["datetime_beginning_utc", "zone", "mw"]
    )
    keep, hoy = _est_hour_of_year(frame["datetime_beginning_utc"], year)
    frame = frame[keep].copy()
    frame["hour"] = hoy
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    return frame.pivot_table(index="hour", columns="zone", values="mw", aggfunc="mean")


def _measured_components_est(year: int, p137) -> dict[str, pd.DataFrame]:
    """Load-weighted measured DA components per MODEL zone, EST hour index."""
    files = sorted(
        (REPO / "data/raw/pjm-zonal-lmp").glob(f"da_hrl_lmps_{year}_*.parquet")
    )
    if not files:
        raise SystemExit(
            f"no measured zonal LMP parquet for {year} — run "
            "scripts/data/fetch_pjm_zonal_lmp_components.py first"
        )
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw = raw[~raw["pnode_name"].isin(p137.NON_ZONE_PNODES)].copy()

    keep, hoy = _est_hour_of_year(raw["datetime_beginning_utc"], year)
    raw = raw[keep].copy()
    raw["hour"] = hoy
    raw["load_zone"] = raw["pnode_name"].map(p137.LMP_PNODE_TO_LOAD_ZONE)
    raw["model_zone"] = raw["load_zone"].map(p137._PJM_LOAD_ZONE_GROUPS)
    raw = raw[raw["model_zone"].notna()].copy()

    weights = _metered_load_est(year).stack().rename("mw").reset_index()
    weights.columns = ["hour", "load_zone", "mw"]
    raw = raw.merge(weights, on=["hour", "load_zone"], how="left")
    raw["mw"] = raw["mw"].fillna(raw["mw"].median())

    out: dict[str, pd.DataFrame] = {}
    for key, col in (
        ("lmp", "total_lmp_da"),
        ("mcc", "congestion_price_da"),
        ("mlc", "marginal_loss_price_da"),
        ("mec", "system_energy_price_da"),
    ):
        raw["_wv"] = raw[col] * raw["mw"]
        num = raw.pivot_table(
            index="hour", columns="model_zone", values="_wv", aggfunc="sum"
        )
        den = raw.pivot_table(
            index="hour", columns="model_zone", values="mw", aggfunc="sum"
        )
        out[key] = (num / den).reindex(range(HOURS))
    return out


# --------------------------------------------------------------------------
# model side — committed keeper sidecars only
# --------------------------------------------------------------------------
def _model_year(bundle: Path, year: int) -> dict:
    """Model P1 hourly system price, Dominion dual, load and net load."""
    sysf = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    sysf = sysf[sysf["pass"] == "P1"]
    internal = sysf[sysf["zone"] != EXTERNAL_ZONE]

    price = internal.pivot(index="hour", columns="zone", values="price")
    dem = internal.pivot(index="hour", columns="zone", values="demand")
    load = dem.sum(axis=1).to_numpy(float)
    lw = (price * dem).sum(axis=1).to_numpy(float) / load

    res = internal.pivot(index="hour", columns="zone", values="reserve_price")
    # Reserve price is a system product; every internal zone carries the same
    # value, so the load-weighted mean is that value (guarded by a max()).
    reserve = res.max(axis=1).to_numpy(float)

    cls = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    cls = cls[cls["pass"] == "P1"]
    ren = (
        cls[cls["klass"].isin(RENEWABLE_CLASSES)]
        .groupby("hour")["mw"]
        .sum()
        .reindex(range(HOURS))
        .fillna(0.0)
        .to_numpy(float)
    )
    return {
        "dom": price[DOM].to_numpy(float),
        "lw": lw,
        "load": load,
        "netload": load - ren,
        "reserve": reserve,
        "renewable": ren,
    }


def _hour_month(year: int) -> np.ndarray:
    """Calendar month for each of the 8760 non-leap hour-of-year slots."""
    idx = pd.date_range(f"{year}-01-01", periods=HOURS + 48, freq="h")
    idx = idx[~((idx.month == 2) & (idx.day == 29))][:HOURS]
    return idx.month.to_numpy()


# --------------------------------------------------------------------------
# bucketing helpers
# --------------------------------------------------------------------------
def _bucket_stats(
    gap: np.ndarray, weight: np.ndarray, groups: np.ndarray, labels
) -> dict:
    """Per-bucket mean gap, weight share and ADDITIVE contribution.

    ``contrib_to_weighted_mean`` is ``Σ gap·w / Σ w_all`` — the buckets' values
    sum EXACTLY to the overall weighted-mean gap, so a level problem shows as a
    flat contribution profile tracking the weight share while a tail problem
    shows as a few buckets carrying the whole number. A share-of-total statistic
    is deliberately NOT used: the net annual gap passes through zero (2023 is
    +$0.45/MWh load-weighted), which makes any ratio to it meaningless.
    ``abs_share_pct`` gives the sign-blind concentration alongside it.
    """
    g = np.where(np.isfinite(gap), gap, 0.0)
    w_all = np.where(np.isfinite(gap), weight, 0.0)
    abs_tot = float((np.abs(g) * w_all).sum())
    out: dict[str, dict] = {}
    for lab in labels:
        m = groups == lab
        w = w_all[m]
        if w.sum() <= 0:
            continue
        out[str(lab)] = {
            "hours": int(m.sum()),
            "mean_gap": float((g[m] * w).sum() / w.sum()),
            "weight_share_pct": float(w.sum() / w_all.sum() * 100),
            "contrib_to_weighted_mean": float((g[m] * w).sum() / w_all.sum()),
            "abs_share_pct": (
                float((np.abs(g[m]) * w).sum() / abs_tot * 100) if abs_tot else 0.0
            ),
        }
    return out


def _deciles(x: np.ndarray) -> np.ndarray:
    """Within-year decile label 1..10 by ascending x."""
    order = np.argsort(np.argsort(x))
    return (order * 10 // len(x) + 1).astype(int)


# --------------------------------------------------------------------------
# the measurement
# --------------------------------------------------------------------------
def measure(bundle: Path) -> dict:
    p137 = _load_p137()
    per_year: dict[str, dict] = {}

    for year in YEARS:
        comp = _measured_components_est(year, p137)
        comp_ept = p137._measured_components(year)  # pjm-137's key, for §A1
        mdl = _model_year(bundle, year)
        ct, ct_meta = p137._dominion_ct_hourly(year)

        mec = comp["mec"][DOM].to_numpy(float)  # RTO-uniform system energy price
        lmp = comp["lmp"][DOM].to_numpy(float)
        mcc = comp["mcc"][DOM].to_numpy(float)
        mlc = comp["mlc"][DOM].to_numpy(float)

        month = _hour_month(year)
        hod = np.arange(HOURS) % 24
        season = np.array(
            [next(s for s, ms in SEASONS.items() if m in ms) for m in month],
            dtype=object,
        )

        ok = np.isfinite(mec) & np.isfinite(lmp) & np.isfinite(mdl["dom"])

        # ---- D1 the identity decomposition -------------------------------
        meas_basis = lmp - mec  # == mcc + mlc by PJM's own construction
        model_basis = mdl["dom"] - mdl["lw"]
        sys_gap = mec - mdl["lw"]
        basis_gap = meas_basis - model_basis
        total_gap = lmp - mdl["dom"]

        wload = np.where(ok, mdl["load"], 0.0)
        wct = np.where(ok, ct, 0.0)

        def _wm(x: np.ndarray, w: np.ndarray) -> float:
            return float(np.sum(np.where(ok, x, 0.0) * w) / w.sum())

        d1 = {
            "identity_residual_max_abs": float(
                np.nanmax(np.abs(total_gap[ok] - sys_gap[ok] - basis_gap[ok]))
            ),
            "measured_basis_vs_mcc_plus_mlc_max_abs": float(
                np.nanmax(np.abs(meas_basis[ok] - (mcc[ok] + mlc[ok])))
            ),
            "load_weighted": {
                "measured_dom_lmp": _wm(lmp, wload),
                "model_dom_dual": _wm(mdl["dom"], wload),
                "total_gap": _wm(total_gap, wload),
                "system_energy_gap": _wm(sys_gap, wload),
                "basis_gap": _wm(basis_gap, wload),
                "measured_mec": _wm(mec, wload),
                "model_system_lw": _wm(mdl["lw"], wload),
            },
            "ct_energy_weighted": {
                "measured_dom_lmp": _wm(lmp, wct),
                "model_dom_dual": _wm(mdl["dom"], wct),
                "total_gap": _wm(total_gap, wct),
                "system_energy_gap": _wm(sys_gap, wct),
                "basis_gap": _wm(basis_gap, wct),
                "measured_mec": _wm(mec, wct),
                "model_system_lw": _wm(mdl["lw"], wct),
                "measured_dom_mcc": _wm(mcc, wct),
                "measured_dom_mlc": _wm(mlc, wct),
                "model_dom_basis": _wm(model_basis, wct),
            },
        }

        # ---- D2 the shape, load-weighted ---------------------------------
        dec = _deciles(mdl["netload"])
        d2 = {
            "by_hour_of_day": _bucket_stats(sys_gap, wload, hod, range(24)),
            "by_season": _bucket_stats(sys_gap, wload, season, list(SEASONS)),
            "by_netload_decile": _bucket_stats(sys_gap, wload, dec, range(1, 11)),
            "by_measured_price_band": _bucket_stats(
                sys_gap,
                wload,
                np.array(
                    [
                        PRICE_BAND_LABS[
                            int(np.searchsorted([40.0, 150.0], v, side="right"))
                        ]
                        if np.isfinite(v)
                        else "nan"
                        for v in lmp
                    ],
                    dtype=object,
                ),
                list(PRICE_BAND_LABS),
            ),
        }

        # ---- D3 the same, CT-energy-weighted -----------------------------
        d3 = {
            "by_hour_of_day": _bucket_stats(sys_gap, wct, hod, range(24)),
            "by_season": _bucket_stats(sys_gap, wct, season, list(SEASONS)),
            "by_netload_decile": _bucket_stats(sys_gap, wct, dec, range(1, 11)),
            "ct_share_of_energy_by_decile": {
                str(d): float(wct[dec == d].sum() / wct.sum() * 100)
                for d in range(1, 11)
            },
        }

        # ---- D4 tail instruments -----------------------------------------
        def _cnt(x: np.ndarray, thr: float) -> int:
            return int(np.sum(np.isfinite(x) & (x > thr)))

        top = dec >= 9
        d4 = {
            "hours_measured_mec_gt": {
                str(t): _cnt(mec, t) for t in (75, 100, 150, 250)
            },
            "hours_model_lw_gt": {
                str(t): _cnt(mdl["lw"], t) for t in (75, 100, 150, 250)
            },
            "hours_measured_dom_lmp_gt": {
                str(t): _cnt(lmp, t) for t in (75, 100, 150, 250)
            },
            "hours_model_dom_gt": {
                str(t): _cnt(mdl["dom"], t) for t in (75, 100, 150, 250)
            },
            "model_reserve_price_by_decile": {
                str(d): float(mdl["reserve"][dec == d].mean()) for d in range(1, 11)
            },
            "model_netload_gw_by_decile": {
                str(d): float(mdl["netload"][dec == d].mean() / 1e3)
                for d in range(1, 11)
            },
            "top2_decile_contrib_to_annual_lw_gap": float(
                np.sum(sys_gap[top & ok] * wload[top & ok]) / wload[ok].sum()
            ),
            "annual_lw_gap": float(
                np.sum(sys_gap[ok] * wload[ok]) / wload[ok].sum()
            ),
            "top2_decile_abs_share_pct": float(
                np.sum(np.abs(sys_gap[top & ok]) * wload[top & ok])
                / np.sum(np.abs(sys_gap[ok]) * wload[ok])
                * 100
            ),
            "top2_decile_weight_share_pct": float(
                wload[top & ok].sum() / wload[ok].sum() * 100
            ),
            "gap_quantiles_load_weighted": {
                f"p{int(q * 100)}": float(
                    np.interp(
                        q,
                        np.cumsum(wload[ok][np.argsort(sys_gap[ok])])
                        / wload[ok].sum(),
                        np.sort(sys_gap[ok]),
                    )
                )
                for q in (0.05, 0.25, 0.5, 0.75, 0.95)
            },
            "pct_hours_sys_gap_positive": float(
                np.sum(wload[ok] * (sys_gap[ok] > 0)) / wload[ok].sum() * 100
            ),
        }

        # ---- D5 how much of the system-energy gap is RESERVE ---------------
        # In a co-optimized market the marginal unit that also carries reserve
        # must be indifferent between the two, so its energy price contains the
        # reserve clearing price as an additive opportunity cost. Attributing
        # the WHOLE measured reserve MCP to the gap is therefore the most
        # generous possible attribution to the reserve lane, and the residual
        # it leaves is a LOWER bound on what an energy-stack mechanism would
        # still have to explain. Reported as a bound, never as a decomposition.
        res = _measured_reserve_est(year)
        syn, pri = res["syn_mcp"], res["pri_mcp"]
        okr = ok & np.isfinite(syn)

        def _w(x, w, mask):
            return float(np.sum(x[mask] * w[mask]) / w[mask].sum())

        d5 = {
            "measured_reserve_mcp_gt0_pct_of_hours": {
                "syn": float(np.mean(syn[np.isfinite(syn)] > 0) * 100),
                "pri": float(np.mean(pri[np.isfinite(pri)] > 0) * 100),
            },
            "measured_cover_ratio_p50": {
                k: float(
                    np.nanmedian(res[f"{k}_cleared"] / res[f"{k}_req"])
                )
                for k in ("syn", "pri", "t30")
            },
            "corr_measured_syn_mcp_vs_system_gap": float(
                np.corrcoef(syn[okr], sys_gap[okr])[0, 1]
            ),
            "model_reserve_dual_hours_gt0": int(np.sum(mdl["reserve"] > 0.0)),
            "model_reserve_dual_mean": float(np.mean(mdl["reserve"])),
            "ct_energy_weighted": {
                "system_energy_gap": _w(sys_gap, wct, okr),
                "measured_syn_mcp": _w(syn, wct, okr),
                "model_reserve_dual": _w(mdl["reserve"], wct, okr),
                "residual_after_full_reserve_credit": _w(
                    sys_gap - syn + mdl["reserve"], wct, okr
                ),
            },
            "load_weighted": {
                "system_energy_gap": _w(sys_gap, wload, okr),
                "measured_syn_mcp": _w(syn, wload, okr),
                "model_reserve_dual": _w(mdl["reserve"], wload, okr),
                "residual_after_full_reserve_credit": _w(
                    sys_gap - syn + mdl["reserve"], wload, okr
                ),
            },
            "top_decile_load_weighted": {
                "system_energy_gap": _w(sys_gap, wload, okr & (dec == 10)),
                "measured_syn_mcp": _w(syn, wload, okr & (dec == 10)),
                "model_reserve_dual": _w(mdl["reserve"], wload, okr & (dec == 10)),
                "residual_after_full_reserve_credit": _w(
                    sys_gap - syn + mdl["reserve"], wload, okr & (dec == 10)
                ),
            },
            "syn_mcp_share_of_annual_in_top_decile_pct": float(
                np.nansum(syn[dec == 10]) / np.nansum(syn) * 100
            ),
        }

        # ---- A1 the alignment correction to pjm-137 M3 --------------------
        # pjm-137's M3 headline re-computed under BOTH keys, so the size of the
        # EPT/EST offset is reported rather than asserted. Shape statistics move;
        # levels barely do.
        a1: dict[str, dict] = {}
        for key, cc in (("est_utc_key", comp), ("ept_key_pjm137", comp_ept)):
            l_, c_, m_ = (
                cc["lmp"][DOM].to_numpy(float),
                cc["mcc"][DOM].to_numpy(float),
                cc["mec"][DOM].to_numpy(float),
            )
            k = np.isfinite(l_) & np.isfinite(mdl["dom"])
            wk = np.where(k, ct, 0.0)
            a1[key] = {
                "ct_wtd_measured_dom_lmp": float((l_[k] * wk[k]).sum() / wk.sum()),
                "ct_wtd_model_dom_dual": float(
                    (mdl["dom"][k] * wk[k]).sum() / wk.sum()
                ),
                "ct_wtd_total_deficit": float(
                    ((l_[k] - mdl["dom"][k]) * wk[k]).sum() / wk.sum()
                ),
                "ct_wtd_measured_mcc": float((c_[k] * wk[k]).sum() / wk.sum()),
                "ct_wtd_measured_mec": float((m_[k] * wk[k]).sum() / wk.sum()),
                "corr_measured_mec_vs_model_lw": float(
                    np.corrcoef(m_[k], mdl["lw"][k])[0, 1]
                ),
                "peak_gap_hour_of_day": int(
                    np.argmax(
                        [
                            np.nanmean((m_ - mdl["lw"])[np.arange(HOURS) % 24 == h])
                            for h in range(24)
                        ]
                    )
                ),
            }

        per_year[str(year)] = {
            "fleet": ct_meta,
            "A1_alignment_correction": a1,
            "D1_identity": d1,
            "D2_shape_load_weighted": d2,
            "D3_shape_ct_weighted": d3,
            "D4_tail": d4,
            "D5_reserve_attribution": d5,
        }

    return per_year


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=Path("results/calibration/pjm137_ctheatrate_B"),
        help="calibration bundle whose hourly/ sidecars supply the model duals",
    )
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    args = ap.parse_args(argv)

    print(f"pjm-138 M2 — MEC gap shape on {args.bundle} …", flush=True)
    payload = {
        "bundle": str(args.bundle),
        "years": list(YEARS),
        "M2_mec_gap_shape": measure(args.bundle),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=1))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""miso-131 — the infinite-granularity bound on the coal econ ladder (NO LP).

Adjudicates PREREG-miso131-granularity-infinite-bound-2026-08-05.md (pushed
BEFORE this probe ran). For each keeper-payload COAL_PRB plant the econ band's
hourly dispatch response to the keeper's OWN solved zonal price is
reconstructed twice:

* ``response_6``  — the current 6-step ladder (assembled tranches, quantized);
* ``response_inf`` — the n->inf continuous limit: the piecewise-linear ramp
  through the same assembled (cum-capacity, $) points, same endpoints, same
  capacity, zero new parameters.

The counterfactual class series is ``payload + (response_inf - response_6)``
clipped to [0, plant's own solved annual max] (availability proxy), scored
against the bench actual exactly as D-1 scores (annual hour-of-day mean
profile, off-peak h0-h14 CV ratio). Price-taking is the declared bound
direction: equilibrium feedback can only shrink the gain.

P0b validity gate: the n=6 response model must reproduce the keeper's own
diurnal engine (hod-profile corr >= 0.90 vs the payload class sum, econ+peak
steps; the payload scoring frame must reproduce the official D-1 cv_ratio
within +-0.10). P1 kill: n->inf 2025 cv_ratio < 0.50. P1-secondary kill:
n->inf drops 2023 or 2024 below 0.50.

Years 2023-2025 ONLY (rule 22 [R-HOLDOUT]; MISO holds no marker).

Usage::

    uv run python scripts/probes/_miso131_granularity_infinite_bound.py
"""

from __future__ import annotations

import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

from probes import _miso128_c7_diurnal_organization as M128  # noqa: E402

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    build_base_fleet,
    build_dispatch_fleet,
    fleet_to_bins,
    load_fleet_from_csv,
)
from market_sim.data.fuel.plant_prices import _load_monthly_cache  # noqa: E402
from scripts.lib import backcast_artifacts as ba  # noqa: E402

BUNDLE = REPO / "results/calibration/miso127_onlinepmin_B"
PAYLOAD = REPO / "frontend/data/backcast/runs/2026-08-04-miso-127-onlinepmin.js"
OUT = REPO / "results/calibration/_miso131_granularity_infinite_bound.json"
YEARS = (2023, 2024, 2025)
KEEPER_D1_CV_RATIO = {2023: 0.514, 2024: 0.529, 2025: 0.347}
MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])
OFFPEAK_LAST = 14  # D1_OFFPEAK_LAST_HOUR

# Pre-registered bars (PREREG section 2).
P0B_MIN_PROFILE_R = 0.90
P0B_CV_ABS_TOL = 0.10
P1_KILL_BELOW = 0.50


def _decode_cf(b64: str, annual_twh, npl: float) -> np.ndarray:
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def _bench_plants(year: int) -> dict:
    if year not in YEARS:
        raise ValueError(f"holdout year {year} must not be read")
    with gzip.open(REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz") as f:
        return json.load(f)["bench"]["plants"]


def _zone_prices(year: int) -> dict[str, np.ndarray]:
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    out = {}
    for z, g in df.groupby("zone"):
        out[str(z)] = g.sort_values("hour")["price"].values[:8760]
    return out


def _model_class(year: int) -> np.ndarray:
    df = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == "COAL_PRB")]
    return df.sort_values("hour")["mw"].values[:8760]


def _profile(series: np.ndarray) -> np.ndarray:
    return series.reshape(-1, 24).mean(axis=0)


def _offpeak_cv(prof24: np.ndarray) -> float:
    off = prof24[: OFFPEAK_LAST + 1]
    m = float(off.mean())
    return float(off.std() / m) if m > 1e-9 else 0.0


def _cv_ratio(model_series: np.ndarray, actual_series: np.ndarray) -> float:
    return _offpeak_cv(_profile(model_series)) / _offpeak_cv(_profile(actual_series))


def _assemble_coal_tranches(year: int, cfg) -> tuple[dict, dict]:
    """Per PRB plant: sorted fuel-priced tranches (econ + peak) and zone."""
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    raw = load_fleet_from_csv(
        "MISO", iso_config, year=year,
        measured_ct_heat_rates=cfg.measured_ct_heat_rates,
        measured_chp_heat_rates=cfg.measured_chp_heat_rates,
        cc_steam_part_capacity=cfg.cc_steam_part_capacity)
    bins = fleet_to_bins(raw, "MISO", cfg)
    base = build_base_fleet(bins, "MISO", iso_config, zone_names, cfg, [], [],
                            year, None, vintage_year=year, legacy_n_bins=0)
    fleet, fuel_fracs, _, _ = build_dispatch_fleet(
        base, bins, [], "MISO", year, zone_names, cfg)
    zone_of = bins.set_index("Plant_Code")["ERCOT_Zone"].to_dict()
    plants: dict[int, dict] = {}
    for i, g in enumerate(fleet):
        if str(getattr(g, "fuel_type", "")) != "coal":
            continue
        if str(getattr(g, "coal_supply", "")) != "prb":
            continue
        uid = str(g.unit_id)
        m = re.search(r"_p(\d+)_([a-z0-9]+)$", uid)
        if not m:
            continue
        code, sfx = int(m.group(1)), m.group(2)
        is_econ = sfx.startswith("econc")
        if not (is_econ or sfx == "peak"):
            continue  # mustrun/committed bid ~VOM: constant-on, no hod signal
        p = plants.setdefault(code, {"zone": zone_of.get(code), "tranches": []})
        p["tranches"].append({
            "sfx": sfx, "is_econ": is_econ,
            "pmax": float(g.pmax_mw),
            "hr": float(g.heat_rate),
            "ff": float(fuel_fracs[i]),
            "vom": float(getattr(g, "vom_cost", getattr(g, "vom", 0.0)) or 0.0),
        })
    for p in plants.values():
        p["tranches"].sort(key=lambda t: t["hr"])
    return plants, zone_of


def _monthly_coal_price(costs: pd.DataFrame, year: int,
                        prb_codes: set[int]) -> tuple[dict, np.ndarray]:
    """(plant, month) F923 price with PRB volume-weighted month-mean fallback."""
    sub = costs[(costs.year == year) & (costs.fuel_group == "Coal")]
    per = {(int(r.plant_id), int(r.month)): float(r.price_per_mmbtu)
           for r in sub.itertuples()}
    fb = np.full(13, np.nan)
    prb = sub[sub.plant_id.isin(prb_codes)]
    for m in range(1, 13):
        s = prb[prb.month == m]
        if len(s) and s.quantity.sum() > 0:
            fb[m] = float(np.average(s.price_per_mmbtu, weights=s.quantity))
    year_mean = float(np.nanmean(fb[1:]))
    fb = np.where(np.isfinite(fb), fb, year_mean)
    return per, fb


def _responses(plant: dict, price: np.ndarray, coal_price_h: np.ndarray
               ) -> tuple[np.ndarray, np.ndarray]:
    """(response_6, response_inf) hourly MW for one plant.

    Step offers move with the plant's monthly coal price; the inf-ramp is the
    piecewise-linear interpolation through the step (cum-cap-midpoint, $)
    points, clamped to [0, band cap] — the n->inf limit of the same
    construction, zero new parameters. The single peak tranche stays a step in
    BOTH legs (the object is the ECON band's granularity).
    """
    econ = [t for t in plant["tranches"] if t["is_econ"]]
    peak = [t for t in plant["tranches"] if not t["is_econ"]]
    r6 = np.zeros(8760)
    rinf = np.zeros(8760)
    if econ:
        caps = np.array([t["pmax"] for t in econ])
        hrs = np.array([t["hr"] for t in econ])
        ffs = np.array([t["ff"] for t in econ])
        voms = np.array([t["vom"] for t in econ])
        # (n_steps, T) step offers
        offers = hrs[:, None] * ffs[:, None] * coal_price_h[None, :] + voms[:, None]
        r6 += (caps[:, None] * (offers < price[None, :])).sum(axis=0)
        # inf-ramp: linear in cumulative capacity through step midpoints
        cum = np.cumsum(caps)
        mids = cum - caps / 2.0
        total = float(cum[-1])
        # vectorized per-hour interpolation: for each hour, dispatched cap =
        # interp of price on the (offer_k(t), mids_k) curve, extended to the
        # band edges (0 below the first step's offer at its half-step reach,
        # total above the last). np.interp needs 1-D per hour; build via
        # searchsorted on the monthly-constant offer ladder instead: offers
        # vary only by month, so loop months (12), not hours (rule 2 spirit).
        for m in range(1, 13):
            hsel = MO == m
            off_m = offers[:, hsel][:, 0]  # monthly-constant per step
            p_m = price[hsel]
            r = np.interp(p_m, off_m, mids, left=0.0, right=total)
            rinf[hsel] = r
    if peak:
        for t in peak:
            offer = t["hr"] * t["ff"] * coal_price_h + t["vom"]
            on = (price > offer) * t["pmax"]
            r6 += on
            rinf += on
    return r6, rinf


def main() -> None:
    cfg = M128._keeper_config()
    costs = _load_monthly_cache(None)
    run = ba.decode_run_js(PAYLOAD.read_text())
    record: dict = {"session": "miso-131",
                    "prereg": "PREREG-miso131-granularity-infinite-bound-2026-08-05.md",
                    "years": {}}
    verdicts = []
    for year in YEARS:
        plants_assembled, _ = _assemble_coal_tranches(year, cfg)
        prb_codes = set(plants_assembled)
        per_price, fb = _monthly_coal_price(costs, year, prb_codes)
        zprices = _zone_prices(year)
        bench = _bench_plants(year)
        pl = run["years"][str(year)]["plants"]

        actual = np.zeros(8760)
        for pid, b in bench.items():
            if b.get("nodata") or not b.get("campd") or b["group"] != "COAL_PRB":
                continue
            actual += _decode_cf(b["campd"], b.get("c_ann"),
                                 float(b.get("npl") or 0.0))[:8760]

        payload_sum = np.zeros(8760)
        r6_sum = np.zeros(8760)
        cf_sum = np.zeros(8760)   # counterfactual: payload + (rinf - r6), clipped
        clip_hours = 0
        frozen_cap = 0.0
        total_cap = 0.0
        n_used = 0
        for pid, b in bench.items():
            if b.get("group") != "COAL_PRB":
                continue
            code = int(re.match(r"(\d+)", pid).group(1))
            p = pl.get(pid)
            asm = plants_assembled.get(code)
            if p is None or not p.get("m") or asm is None:
                continue
            zone = asm["zone"]
            if zone not in zprices:
                continue
            npl = float(b.get("npl") or 0.0)
            m_series = _decode_cf(p["m"], p.get("m_ann"), npl)[:8760]
            coal_h = np.array([per_price.get((code, m), fb[m]) for m in MO])
            r6, rinf = _responses(asm, zprices[zone], coal_h)
            delta = rinf - r6
            cf = np.clip(m_series + delta, 0.0, float(m_series.max()))
            clip_hours += int((np.abs(cf - (m_series + delta)) > 1e-9).sum())
            payload_sum += m_series
            r6_sum += r6
            cf_sum += cf
            n_used += 1
            band_cap = sum(t["pmax"] for t in asm["tranches"])
            total_cap += band_cap
            if rinf.max() - rinf.min() < 1e-6:
                frozen_cap += band_cap

        # ---- P0b validity gate ----
        prof_r = float(np.corrcoef(_profile(r6_sum), _profile(payload_sum))[0, 1])
        cv_frame = _cv_ratio(payload_sum, actual)
        p0b_pass = (prof_r >= P0B_MIN_PROFILE_R and
                    abs(cv_frame - KEEPER_D1_CV_RATIO[year]) <= P0B_CV_ABS_TOL)

        # ---- P1 statistic ----
        cv_cf = _cv_ratio(cf_sum, actual)
        record["years"][str(year)] = {
            "plants_used": n_used,
            "p0b_profile_r_response6_vs_payload": round(prof_r, 3),
            "p0b_payload_frame_cv_ratio": round(cv_frame, 3),
            "p0b_keeper_d1_cv_ratio": KEEPER_D1_CV_RATIO[year],
            "p0b_pass": bool(p0b_pass),
            "counterfactual_inf_cv_ratio": round(cv_cf, 3),
            "payload_cv_ratio": round(cv_frame, 3),
            "delta_cv_ratio": round(cv_cf - cv_frame, 3),
            "frozen_share_of_band_cap": round(frozen_cap / total_cap, 3)
            if total_cap else None,
            "clip_hours": clip_hours,
        }
        verdicts.append((year, p0b_pass, cv_cf))
        print(f"{year}: P0b profile_r {prof_r:.3f} | payload-frame cv_ratio "
              f"{cv_frame:.3f} (keeper {KEEPER_D1_CV_RATIO[year]}) -> "
              f"{'PASS' if p0b_pass else 'VOID'} | n->inf cv_ratio {cv_cf:.3f} "
              f"(payload {cv_frame:.3f}) | frozen band share "
              f"{frozen_cap / total_cap if total_cap else float('nan'):.3f}")

    # ---- adjudication (pre-registered) ----
    if not all(v[1] for v in verdicts):
        record["verdict"] = "P0b VOID — construction cannot adjudicate; no verdict"
    else:
        cv25 = dict((y, cv) for y, _, cv in verdicts)[2025]
        harm = [y for y, _, cv in verdicts if y in (2023, 2024) and cv < P1_KILL_BELOW]
        if cv25 < P1_KILL_BELOW:
            record["verdict"] = (
                f"P1 KILL — n->inf 2025 cv_ratio {cv25:.3f} < 0.50: infinite "
                "granularity cannot reach the gate under price-taking; the lane dies")
        elif harm:
            record["verdict"] = (
                f"P1-secondary KILL — n->inf drops {harm} below 0.50: "
                "granularity refuted as harmful")
        else:
            record["verdict"] = (
                f"P1 SURVIVES — n->inf 2025 cv_ratio {cv25:.3f} >= 0.50; the "
                "expected-kill prior is REFUTED; proceed to P2 identification")
    print("\nVERDICT:", record["verdict"])
    OUT.write_text(json.dumps(record, indent=1))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()

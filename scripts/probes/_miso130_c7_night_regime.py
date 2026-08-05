"""miso-130 — the C7 COAL_PRB summer-night readout: the July price wave, the
month-grain coal amplitude deficit, the (empty) CC bridge pool, and the
night-clearing-vs-coal-band regime overlay. NO LP; committed artifacts only.

Four measurements, all descriptive (no mechanism is armed or adjudicated —
no pre-registered kill set was committed before these numbers were read, so
NOTHING here carries a verdict; cells stay as they are and any future lever
screen must pre-register its own bars):

  A. Model vs actual RT hub-mean price, monthly + July hour-of-day, per year.
     Model = keeper P1 demand-weighted zonal price (miso127_onlinepmin_B
     sidecars); actual = data/raw/lmp-data/MISO hub RT LMP rows (2023-2025
     ONLY — rule 22 [R-HOLDOUT]: MISO holds no marker, 2022/2026 files are
     not read), Feb 29 dropped (non-leap model clock).
  B. COAL_PRB month x hour: overnight (h0-5) model-minus-actual MW and the
     off-peak diurnal amplitude, model vs the CAMPD bench, per month/year.
  C. The gas-commitment-bridge pool census (pjm-142's screen statistic,
     measured here WITHOUT a prereg => descriptive only): model CC_REGULAR
     plants running by day (>20% npl) and near-off overnight (<5% npl) in
     July, from the keeper's own payload.
  D. The July merit overlay: every coal/gas tranche's July $ offer (fleet
     assembled at HEAD under the keeper config; per-plant F923 July coal
     prices; ISO measured July gas; the apply_gas_offer_margin form
     mc += markup_hr x (anchor - fuel)) against the keeper's own solved July
     night prices — the share of the COAL_PRB econ ladder priced BELOW the
     model's July night floor, per year (the freeze statistic).

Usage::

    uv run python scripts/probes/_miso130_c7_night_regime.py
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
from market_sim.data.fuel.plant_prices import (  # noqa: E402
    _load_monthly_cache,
    iso_monthly_gas_prices,
)
from scripts.lib import backcast_artifacts as ba  # noqa: E402

BUNDLE = REPO / "results/calibration/miso127_onlinepmin_B"
PAYLOAD = REPO / "frontend/data/backcast/runs/2026-08-04-miso-127-onlinepmin.js"
OUT = REPO / "results/calibration/_miso130_c7_night_regime.json"
YEARS = (2023, 2024, 2025)  # rule 22: the ONLY years read anywhere below
MONTH_LEN = {1: 31, 2: 28, 3: 31, 4: 30, 5: 31, 6: 30,
             7: 31, 8: 31, 9: 30, 10: 31, 11: 30, 12: 31}
MO = np.concatenate([np.full(MONTH_LEN[m] * 24, m) for m in range(1, 13)])
HOD = np.arange(8760) % 24
JULY = MO == 7
NIGHT = HOD < 6
DAY = (HOD >= 10) & (HOD < 19)
OFFPEAK_LAST = 14  # legitimacy_diagnostics.D1_OFFPEAK_LAST_HOUR


def _decode_cf(b64: str, annual_twh, npl: float) -> np.ndarray:
    raw = np.frombuffer(base64.b64decode(b64), dtype=np.uint8).astype(float)
    tot = raw.sum()
    if annual_twh is not None and tot > 0.0:
        return raw * (annual_twh * 1e6 / tot)
    return raw / 100.0 * npl


def _bench_plants(year: int) -> dict:
    with gzip.open(REPO / f"frontend/data/backcast/bench/MISO/{year}.json.gz") as f:
        return json.load(f)["bench"]["plants"]


def _bench_class(plants: dict, klass: str) -> np.ndarray:
    out = np.zeros(8760)
    for p in plants.values():
        if p.get("nodata") or not p.get("campd") or p["group"] != klass:
            continue
        out += _decode_cf(p["campd"], p.get("c_ann"), float(p.get("npl") or 0.0))[:8760]
    return out


def _model_class(year: int, klass: str) -> np.ndarray:
    df = pd.read_parquet(BUNDLE / f"hourly/class_hourly_{year}.parquet")
    df = df[(df["pass"] == "P1") & (df["klass"] == klass)]
    return df.sort_values("hour")["mw"].values[:8760]


def _model_price_demand(year: int) -> tuple[np.ndarray, np.ndarray]:
    df = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    g = df.groupby("hour")
    price = g.apply(lambda x: np.average(x["price"], weights=x["demand"]),
                    include_groups=False).values[:8760]
    return price, g["demand"].sum().values[:8760]


def _actual_rt(year: int) -> np.ndarray:
    if year not in YEARS:  # rule 22 guard — never a holdout year
        raise ValueError(f"holdout year {year} must not be read")
    df = pd.read_csv(REPO / f"data/raw/lmp-data/MISO/miso_hub_lmp_{year}_rt.csv.gz")
    df = df[(df["value"] == "LMP") & (df["date"] != f"{year}-02-29")]
    he = [f"he{i:02d}" for i in range(1, 25)]
    arr = df.groupby("date")[he].mean().sort_index().values.reshape(-1)
    assert arr.size == 8760, (year, arr.size)
    return arr


def part_a_price() -> dict:
    out = {}
    for year in YEARS:
        mp, dem = _model_price_demand(year)
        ap = _actual_rt(year)
        monthly = []
        for m in range(1, 13):
            s = MO == m
            monthly.append({
                "month": m,
                "model_lw": round(float(np.average(mp[s], weights=dem[s])), 2),
                "actual_lw": round(float(np.average(ap[s], weights=dem[s])), 2),
                "actual_lw_cens200": round(
                    float(np.average(np.minimum(ap[s], 200.0), weights=dem[s])), 2),
            })
        jn, jd = JULY & NIGHT, JULY & DAY
        out[str(year)] = {
            "monthly": monthly,
            "july": {
                "model_night_mean": round(float(mp[jn].mean()), 2),
                "actual_night_mean": round(float(ap[jn].mean()), 2),
                "model_night_p10": round(float(np.percentile(mp[jn], 10)), 2),
                "model_night_p50": round(float(np.percentile(mp[jn], 50)), 2),
                "actual_night_p50": round(float(np.percentile(ap[jn], 50)), 2),
                "model_day_mean": round(float(mp[jd].mean()), 2),
                "actual_day_mean": round(float(ap[jd].mean()), 2),
                "model_wave": round(float(
                    mp[JULY].reshape(-1, 24).mean(0).max()
                    - mp[JULY].reshape(-1, 24).mean(0).min()), 1),
                "actual_wave": round(float(
                    ap[JULY].reshape(-1, 24).mean(0).max()
                    - ap[JULY].reshape(-1, 24).mean(0).min()), 1),
            },
        }
    return out


def part_b_coal() -> dict:
    out = {}
    for year in YEARS:
        plants = _bench_plants(year)
        am = _bench_class(plants, "COAL_PRB")
        mm = _model_class(year, "COAL_PRB")
        rows = []
        for m in range(1, 13):
            s = MO == m
            pm = mm[s].reshape(-1, 24).mean(0)
            pa = am[s].reshape(-1, 24).mean(0)
            off = slice(0, OFFPEAK_LAST + 1)
            rows.append({
                "month": m,
                "night_model_minus_actual_mw": round(float((pm[:6] - pa[:6]).mean())),
                "day_model_minus_actual_mw": round(float((pm[10:19] - pa[10:19]).mean())),
                "amp_model_mw": round(float(pm[off].max() - pm[off].min())),
                "amp_actual_mw": round(float(pa[off].max() - pa[off].min())),
            })
        out[str(year)] = rows
    return out


def part_c_pool() -> dict:
    run = ba.decode_run_js(PAYLOAD.read_text())
    out = {}
    for year in YEARS:
        plants = _bench_plants(year)
        pl = run["years"][str(year)]["plants"]
        n_br, cap_br, n_all, cap_all = 0, 0.0, 0, 0.0
        for pid, p in pl.items():
            b = plants.get(pid)
            if b is None or b.get("group") != "CC_REGULAR" or not p.get("m"):
                continue
            npl = float(b.get("npl") or 0.0)
            m = _decode_cf(p["m"], p.get("m_ann"), npl)[:8760]
            jm, jh = m[JULY], HOD[JULY]
            day_on = jm[(jh >= 10) & (jh < 19)].mean()
            night_on = jm[jh < 6].mean()
            n_all += 1
            cap_all += npl
            if day_on > 0.2 * npl and night_on < 0.05 * npl:
                n_br += 1
                cap_br += npl
        out[str(year)] = {"cc_plants": n_all, "cc_npl_mw": round(cap_all),
                          "bridgeable_plants": n_br,
                          "bridgeable_npl_mw": round(cap_br)}
    return out


def part_d_overlay() -> dict:
    cfg = M128._keeper_config()
    iso_config = get_iso_config("MISO")
    zone_names = [z.name for z in iso_config.zones]
    costs = _load_monthly_cache(None)
    anchor = float(cfg.gas_offer_margin_anchor)
    out = {}
    for year in YEARS:
        gj = float(iso_monthly_gas_prices(cfg, year)[6])
        ccosts = costs[(costs.year == year) & (costs.month == 7)
                       & (costs.fuel_group == "Coal")]
        ccosts = ccosts.set_index("plant_id")["price_per_mmbtu"]
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

        prb_econ = []  # (pmax, offer) of COAL_PRB econ tranches
        cc_committed = []
        for i, g in enumerate(fleet):
            fuel = str(getattr(g, "fuel_type", ""))
            uid = str(g.unit_id)
            m = re.search(r"_p(\d+)_([a-z0-9]+)$", uid)
            if not m:
                continue
            code, sfx = int(m.group(1)), m.group(2)
            hr = float(g.heat_rate)
            ff = float(fuel_fracs[i])
            vom = float(getattr(g, "vom_cost", getattr(g, "vom", 0.0)) or 0.0)
            mk = float(getattr(g, "offer_markup_hr", 0.0) or 0.0)
            if fuel == "coal" and str(getattr(g, "coal_supply", "")) == "prb" \
                    and sfx.startswith("econc"):
                cp = float(ccosts.get(code, np.nan))
                if not np.isfinite(cp):
                    continue  # plants without a July F923 row are excluded
                prb_econ.append((float(g.pmax_mw), hr * ff * cp + vom))
            elif fuel == "gas_cc" and sfx == "committed" and uid.startswith("CC_REGULAR"):
                cc_committed.append(
                    (float(g.pmax_mw), hr * gj + vom + mk * (anchor - gj)))

        mp, _ = _model_price_demand(year)
        night = mp[JULY & NIGHT]
        p10, p50 = np.percentile(night, 10), np.percentile(night, 50)
        e = pd.DataFrame(prb_econ, columns=["pmax", "offer"])
        c = pd.DataFrame(cc_committed, columns=["pmax", "offer"])
        out[str(year)] = {
            "july_gas_per_mmbtu": round(gj, 3),
            "model_night_p10": round(float(p10), 2),
            "model_night_p50": round(float(p50), 2),
            "prb_econ_cap_mw": round(float(e.pmax.sum())),
            "prb_econ_offer_p5": round(float(e.offer.quantile(0.05)), 2),
            "prb_econ_offer_p95": round(float(e.offer.quantile(0.95)), 2),
            # THE FREEZE STATISTIC: PRB econ capacity whose July offer is
            # below the model's own July night floor (p10) — priced out of
            # the diurnal wave entirely, so it cannot cycle.
            "prb_econ_share_below_night_p10": round(
                float(e.loc[e.offer < p10, "pmax"].sum() / e.pmax.sum()), 3),
            "prb_econ_share_below_night_p50": round(
                float(e.loc[e.offer < p50, "pmax"].sum() / e.pmax.sum()), 3),
            "cc_committed_cap_mw": round(float(c.pmax.sum())),
            "cc_committed_offer_p10": round(float(c.offer.quantile(0.10)), 2),
            "cc_committed_offer_p90": round(float(c.offer.quantile(0.90)), 2),
            "cc_committed_cap_above_night_p50_minus1": round(
                float(c.loc[c.offer > p50 - 1.0, "pmax"].sum())),
        }
    return out


def main() -> None:
    record = {
        "session": "miso-130",
        "keeper": "2026-08-04-miso-127-onlinepmin",
        "note": ("descriptive measurements only — no prereg, no verdict, no "
                 "mechanism armed; see FINDING-miso130-c7-night-regime-2026-08-05.md"),
        "A_price": part_a_price(),
        "B_coal_prb": part_b_coal(),
        "C_cc_bridge_pool": part_c_pool(),
        "D_overlay": part_d_overlay(),
    }
    OUT.write_text(json.dumps(record, indent=1))
    print(f"wrote {OUT}")
    for year in YEARS:
        a = record["A_price"][str(year)]["july"]
        d = record["D_overlay"][str(year)]
        b = record["B_coal_prb"][str(year)][6]
        print(f"{year}: July night model {a['model_night_mean']} vs actual "
              f"{a['actual_night_mean']}; wave {a['model_wave']} vs {a['actual_wave']}; "
              f"coal night surplus {b['night_model_minus_actual_mw']} MW; "
              f"PRB econ frozen share (below night p10) "
              f"{d['prb_econ_share_below_night_p10']}")


if __name__ == "__main__":
    main()

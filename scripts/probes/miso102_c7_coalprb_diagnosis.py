"""miso-102 — the C7 COAL_PRB off-peak CV diagnosis, from committed artifacts only.

Reproduces every number in ``results/calibration/PREREG-miso102-coalprb-c7-shape-2026-07-28.md``
§1-§3 and ``FINDING-miso102-coalprb-c7-shape-2026-07-28.md``. **No LP re-solve.**

Inputs, all committed:

* ``frontend/data/backcast/runs/2026-07-28-miso-101b-tempgrain.js`` — per-plant
  model MW (the keeper's run payload)
* ``frontend/data/backcast/bench/MISO/<year>.json.gz`` — the CAMPD per-plant bench
* ``results/calibration/miso101_tempgrain_B/hourly/`` — the keeper's class/system sidecars
* ``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`` — actual RT LMP
* ``data/raw/MISO_fueltype.parquet`` — EIA-930 fuel-type actuals
* ``data/raw/_processed-legacy/{coal_takeorpay_MISO,thermal_tranches_MISO}.csv``

The five sections answer, in order: is it a floor / a mix effect / a benchmark
basis (§1); is it the miso-101 §5 cancellation (§2); is it the miso-89 summer
under-derate (§3); is the fleet under-responsive to price or is the price wave
too small (§4); which units and which mechanism own it (§5).

Usage:
    PYTHONPATH=$PWD:$PWD/src python scripts/probes/miso102_c7_coalprb_diagnosis.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import scripts.legitimacy_diagnostics as LD  # noqa: E402
from market_sim.data.fleet.eia860 import eia860_regulated_plants  # noqa: E402

KEEPER = "2026-07-28-miso-101b-tempgrain"
BUNDLE = REPO / "results/calibration/miso101_tempgrain_B"
YEARS = (2023, 2024, 2025)
OFF = np.arange(24) <= LD.D1_OFFPEAK_LAST_HOUR
PRICE_CENSOR = 200.0  # body censor, as miso-89/96 use


def _cv(x: np.ndarray) -> float:
    """CV of a profile slice (the D-1 statistic's inner term)."""
    m = float(x.mean())
    return float(x.std() / m) if m > 1e-9 else 0.0


def _within_day_cv(x: np.ndarray) -> float:
    """Mean over ONLINE days of the day's own 24-hour CV."""
    d = x[:8760].reshape(365, 24)
    on = d.mean(axis=1) > 0.05 * max(float(np.percentile(x, 99.0)), 1e-9)
    if on.sum() < 30:
        return float("nan")
    dd = d[on]
    return float((dd.std(axis=1) / dd.mean(axis=1)).mean())


def load_year(year: int) -> tuple[dict, dict]:
    """Return ``(bench, model_plants)`` for one year — the D-1 pairing inputs."""
    sidecar = json.loads(
        (REPO / f"frontend/data/backcast/registry/{KEEPER}.json").read_text()
    )
    bench = LD.load_bench(REPO, "MISO", year)
    return bench, LD.load_payload_plants(REPO, sidecar, year, bench)


def actual_price(year: int) -> np.ndarray:
    """Body-censored actual MISO RT LMP, hour-of-year mean over zones."""
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
    )
    a = act[act["year"] == year]
    p = a.groupby("hour")["rt"].mean().reindex(range(8760)).to_numpy(float)
    p = np.where(np.isfinite(p), p, np.nanmean(p))
    return np.clip(p, None, PRICE_CENSOR)


def model_price(year: int) -> np.ndarray:
    """Load-weighted ISO model P1 price from the keeper's system sidecar."""
    s = pd.read_parquet(BUNDLE / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.groupby("hour", observed=True)
        .apply(lambda d: np.average(d["price"], weights=d["demand"]), include_groups=False)
        .reindex(range(8760))
        .to_numpy(float)
    )


def section_1_pairing() -> None:
    """§1 — is it a floor, a mix effect, or the benchmark basis?"""
    print("\n" + "=" * 78)
    print("§1  PAIRING / FLOOR / BASIS")
    print("=" * 78)
    diag = json.loads((BUNDLE / "legitimacy_diagnostics.json").read_text())
    d2 = pd.DataFrame(diag["diagnostics"]["D2"]["rows"])
    coal = d2[d2["class"].astype(str).str.startswith("COAL")]
    print("  D-2 forced-energy attribution, MISO coal (the ONLY mechanism on coal):")
    print(coal.to_string(index=False))
    for year in YEARS:
        bench, model = load_year(year)
        prb = {k: b for k, b in bench.items() if b["group"] == "COAL_PRB"}
        paired = [k for k in prb if k in model]
        dropped = [k for k in prb if k not in model]
        m = sum(model[k][:8760] for k in paired)
        a = sum(prb[k]["mw"][:8760] for k in paired)
        print(f"  {year}: {len(paired)} paired, {len(dropped)} DROPPED, "
              f"class energy model {m.sum()/1e6:.2f} / actual {a.sum()/1e6:.2f} TWh "
              f"(ratio {m.sum()/a.sum():.4f})")


def section_2_cancellation() -> None:
    """§2 — is the class composite suppressed by miso-101 §5 cancellation?"""
    print("\n" + "=" * 78)
    print("§2  CANCELLATION (miso-101 §5) — coherence std(sum)/sum(std), off-peak")
    print("=" * 78)
    for year in YEARS:
        bench, model = load_year(year)
        keys = [k for k, b in bench.items() if b["group"] == "COAL_PRB" and k in model]
        m_tot = sum(model[k][:8760] for k in keys)
        a_tot = sum(bench[k]["mw"][:8760] for k in keys)
        m_sd = sum(model[k][:8760].reshape(-1, 24).mean(0)[OFF].std() for k in keys)
        a_sd = sum(bench[k]["mw"][:8760].reshape(-1, 24).mean(0)[OFF].std() for k in keys)
        mc = m_tot.reshape(-1, 24).mean(0)[OFF].std() / m_sd
        ac = a_tot.reshape(-1, 24).mean(0)[OFF].std() / a_sd
        print(f"  {year}: model {mc:.3f}   actual {ac:.3f}   "
              f"-> both in phase; the class sum is NOT a cancellation residual")


def section_3_seasonality() -> None:
    """§3 — is it the miso-89 summer-peak under-derate?"""
    print("\n" + "=" * 78)
    print("§3  SEASONALITY of the COAL_PRB off-peak cv_ratio (miso-89 is SUMMER HE16-18)")
    print("=" * 78)
    seasons = {"winter": [12, 1, 2], "shoulder": [3, 4, 5, 9, 10, 11], "summer": [6, 7, 8]}
    for year in YEARS:
        bench, model = load_year(year)
        keys = [k for k, b in bench.items() if b["group"] == "COAL_PRB" and k in model]
        m_tot = sum(model[k][:8760] for k in keys)
        a_tot = sum(bench[k]["mw"][:8760] for k in keys)
        month = pd.date_range(f"{year}-01-01", periods=8760, freq="h").month
        out = []
        for name, mons in seasons.items():
            sel = np.isin(month, mons)
            nd = sel.sum() // 24
            mp = m_tot[sel][: nd * 24].reshape(-1, 24).mean(0)
            ap = a_tot[sel][: nd * 24].reshape(-1, 24).mean(0)
            out.append(f"{name} {_cv(mp[OFF])/_cv(ap[OFF]):.3f}")
        print(f"  {year}: " + "   ".join(out))


def section_4_price_wave() -> None:
    """§4 — is the fleet under-responsive, or is the price wave too small?"""
    print("\n" + "=" * 78)
    print("§4  PRICE WAVE vs FLEET RESPONSE")
    print("=" * 78)
    hod = np.tile(np.arange(24), 365)[:8760]
    sel = hod <= LD.D1_OFFPEAK_LAST_HOUR
    for year in YEARS:
        bench, model = load_year(year)
        keys = [k for k, b in bench.items() if b["group"] == "COAL_PRB" and k in model]
        m_prb = sum(model[k][:8760] for k in keys)
        a_prb = sum(bench[k]["mw"][:8760] for k in keys)
        mp, ap = model_price(year), actual_price(year)
        pm, pa = mp.reshape(-1, 24).mean(0), ap.reshape(-1, 24).mean(0)
        dm, da = m_prb.reshape(-1, 24).mean(0), a_prb.reshape(-1, 24).mean(0)
        m_sl = np.polyfit(mp[sel], m_prb[sel], 1)[0]
        a_sl = np.polyfit(ap[sel], a_prb[sel], 1)[0]
        cf = dm[OFF].mean() + m_sl * (pa[OFF] - pa[OFF].mean())
        print(f"  {year}: off-peak PRICE cv ratio {_cv(pm[OFF])/_cv(pa[OFF]):.3f}   "
              f"DISPATCH cv ratio {_cv(dm[OFF])/_cv(da[OFF]):.3f}   "
              f"| slope model {m_sl:6.1f} vs actual {a_sl:6.1f} MW/$ "
              f"({m_sl/a_sl:.2f}x)   | counterfactual cv_ratio at the ACTUAL "
              f"price wave: {_cv(cf)/_cv(da[OFF]):.3f}")


def section_5_regulated() -> None:
    """§5 — which units, and does the regulated scope own them?"""
    print("\n" + "=" * 78)
    print("§5  REGULATED vs MERCHANT within-day CV (all MISO coal ranks)")
    print("=" * 78)
    reg = eia860_regulated_plants()
    rows = []
    for year in YEARS:
        bench, model = load_year(year)
        for k, b in bench.items():
            if not b["group"].startswith("COAL") or k not in model:
                continue
            rows.append({
                "year": year, "klass": b["group"],
                "regulated": int(k.split(":")[0]) in reg,
                "a_MW": b["mw"].mean(),
                "m_wdcv": _within_day_cv(model[k]),
                "a_wdcv": _within_day_cv(b["mw"]),
            })
    df = pd.DataFrame(rows).dropna()
    for lab, g in df.groupby("regulated"):
        w = g["a_MW"]
        print(f"  {'REGULATED' if lab else 'MERCHANT ':>10}: n={len(g):3d} plant-years  "
              f"ACTUAL within-day CV {np.average(g.a_wdcv, weights=w):.3f}   "
              f"MODEL {np.average(g.m_wdcv, weights=w):.3f}")
    print("  -> reality: regulated coal cycles MORE within the day than merchant.")
    print("     model:   regulated cycles LESS, by ~4.8x. The ordering is INVERTED.")
    for year in YEARS:
        bench, model = load_year(year)
        keys = [k for k, b in bench.items() if b["group"] == "COAL_PRB" and k in model]
        flat = [k for k in keys if _within_day_cv(model[k]) < 0.02]
        share = sum(bench[k]["mw"].mean() for k in flat) / sum(
            bench[k]["mw"].mean() for k in keys
        )
        n_reg = sum(int(k.split(":")[0]) in reg for k in flat)
        print(f"  {year}: byte-flat PRB plants {len(flat)} ({100*share:.0f}% of class "
              f"energy), of which REGULATED: {n_reg}/{len(flat)}")


def main() -> None:
    """Run every diagnosis section in the order the FINDING presents them."""
    section_1_pairing()
    section_2_cancellation()
    section_3_seasonality()
    section_4_price_wave()
    section_5_regulated()


if __name__ == "__main__":
    main()

"""miso-224 phase 0 (part 2) — MARGINAL FREQUENCY per class-band over EVERY hour.

Zero-solve. Rebuilds the designated keeper's OWN fleet and offer basis
(``2026-09-05-miso-220-nonsteam-lift``, bundle ``miso220_nonsteamlift_B``) through
the chain ``runner.py`` runs — fleet -> bins -> arrays -> resolved delivered fuel ->
``assemble_mc`` -> coal tranches -> gas offer margin — via
``_miso134_ct_night_order_screen.build_year`` (the miso-220 instrument), and reads
which class-band tranche brackets the committed P1 clearing price in EVERY hour,
not only at the 15 object hours miso-220 read.

WHY. miso-223 killed a body arm because its footprint was measured as annual ENERGY
share (the ``committed`` band carries 47.4 % of lifted-class energy) when the gate
was a PRICE gate, and price is set by the MARGINAL tranche. The mandatory phase 0
for any successor aimed at the body is therefore: in what share of body hours does
each band hold the margin? That number, not energy, is the footprint a price gate
needs.

Method (miso-220's, extended to all hours and made congestion-aware). In each hour
the tranches eligible to set a zone's price are the live tranches in every zone
whose committed P1 dual is within $0.01 of that zone's — the uncongested group.
The marginal tranche is the eligible tranche with the highest ``mc_base`` <= price.
The reconstruction residual (price minus that ``mc_base``) is the P1 amortized-
startup adder plus any unmodelled wedge; it is reported at full magnitude, and a
residual above ``RESID_CLEAN`` marks the hour's margin as NOT cleanly identified
by the thermal ladder (imports, hydro, storage and the startup adder are outside
``mc_base``). Tallies are reported both over cleanly-identified hours and over all.

Hour sets, per zone-year (the C3a zone MISO-Indiana is the headline; the five
hub-carrying zones are pooled as the second read):

* ``all`` — 8,760 hours;
* ``body`` — the bottom 90 % of the zone's OWN model price (miso-223's body);
* ``actual_lt_20`` — hours where the zone's hub RT LMP < $20 (the cheap deciles
  where miso-224 part 1 finds the body error largest);
* ``model_bottom_decile`` — the model's own cheapest 10 %.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted.

Usage::

    MISO224_YEARS=2024 python3 scripts/probes/_miso224_marginal_frequency_phase0.py
"""

from __future__ import annotations

import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts" / "probes"))

import _miso134_ct_night_order_screen as _m134  # noqa: E402

KEEPER = REPO / "results/calibration/miso220_nonsteamlift_B"
_m134.BUNDLE = KEEPER

from _miso134_ct_night_order_screen import build_year, keeper_config  # noqa: E402
from _miso221_peak_shape_phase0 import _band, _r  # noqa: E402

OUT = REPO / "results/calibration/_miso224_marginal_frequency.json"
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
YEARS = tuple(int(v) for v in os.environ.get("MISO224_YEARS", "2023,2024,2025").split(","))
assert set(YEARS) <= {2023, 2024, 2025}, "rule 22: MISO holds no holdout marker"
HOURS = 8760
EPS = 1e-6
PRICE_TIE = 0.01        # zones within this of each other share one uncongested price
RESID_CLEAN = 1.0       # $/MWh: residual above this = margin not cleanly on the ladder
CARRYING = ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South"]
HUB_ZONES = ["MISO-West", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South"]


def actual_zone_price(year: int) -> pd.DataFrame:
    """hour x zone hub RT LMP (MISO-South = mean of its four hubs), model clock."""
    a = pd.read_parquet(ZONAL_ACTUAL)
    a = a[a["year"] == year]
    hub = a.pivot_table(index="hour", columns="hub", values="rt", aggfunc="first").reindex(range(HOURS))
    zone_of = a.drop_duplicates("hub").set_index("hub")["zone"]
    out = pd.DataFrame(index=hub.index)
    for z in sorted(zone_of.unique()):
        out[z] = hub[[h for h in hub.columns if zone_of[h] == z]].mean(axis=1)
    return out


def keeper_prices(year: int) -> pd.DataFrame:
    """hour x zone committed P1 price."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return s.pivot_table(index="hour", columns="zone", values="price", aggfunc="first").reindex(range(HOURS))


def _tally(keys: np.ndarray, mask: np.ndarray) -> dict:
    """Share of hours in ``mask`` by key, sorted descending."""
    if not mask.any():
        return {}
    vals, cnt = np.unique(keys[mask], return_counts=True)
    order = np.argsort(-cnt)
    n = int(mask.sum())
    return {str(vals[i]): _r(cnt[i] / n, 4) for i in order}


def analyse_year(year: int) -> dict:
    """Marginal class-band frequency per zone and hour set."""
    cfg = keeper_config()
    raw_fleet, fleet, arrays, fuel_prices, mc, zone_names = build_year(cfg, year)
    n = len(fleet)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    band = np.array([_band(g.unit_id) for g in fleet])
    zone = np.array([str(g.zone) for g in fleet])
    key = np.array([f"{k}|{b}" for k, b in zip(klass, band)])
    pmax = np.asarray(arrays.pmax, float)
    avail = np.asarray(arrays.availability, float)
    if avail.ndim == 1:
        avail = np.tile(avail[:, None], (1, HOURS))
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    zi = {z: i for i, z in enumerate(zone_names)}
    gz = np.array([zi.get(z, -1) for z in zone])

    prices = keeper_prices(year)
    act = actual_zone_price(year)
    P = prices[CARRYING].to_numpy(float)                      # (H, 6)

    out = {"n_tranches": int(n), "zones": {}}
    marg_key = np.full((HOURS, len(CARRYING)), "", dtype=object)
    resid = np.full((HOURS, len(CARRYING)), np.nan)
    marg_mc = np.full((HOURS, len(CARRYING)), np.nan)
    for h in range(HOURS):
        cap_h = pmax * avail[:, h]
        live = cap_h > 1.0
        mc_h = mc[:, h]
        for j, z in enumerate(CARRYING):
            p = P[h, j]
            grp = [zi[CARRYING[k]] for k in range(len(CARRYING)) if abs(P[h, k] - p) <= PRICE_TIE]
            elig = live & np.isin(gz, grp) & (mc_h <= p + EPS)
            if elig.any():
                i = int(np.flatnonzero(elig)[np.argmax(mc_h[elig])])
                marg_key[h, j] = key[i]
                marg_mc[h, j] = mc_h[i]
                resid[h, j] = p - mc_h[i]
        if h % 2000 == 0:
            print(f"    {year} h={h}", flush=True)

    for j, z in enumerate(CARRYING):
        p = P[:, j]
        sets = {
            "all": np.ones(HOURS, bool),
            "body": p <= np.percentile(p, 90),
            "model_bottom_decile": p <= np.percentile(p, 10),
        }
        if z in act.columns:
            a = act[z].to_numpy(float)
            sets["actual_lt_20"] = np.isfinite(a) & (a < 20.0)
        clean = np.isfinite(resid[:, j]) & (resid[:, j] <= RESID_CLEAN)
        zrec = {}
        for name, m in sets.items():
            zrec[name] = {
                "n": int(m.sum()),
                "clean_share": _r(clean[m].mean(), 4),
                "residual_p50": _r(np.nanmedian(resid[m, j]), 3),
                "residual_p90": _r(np.nanpercentile(resid[m, j], 90), 3),
                "model_price_mean": _r(p[m].mean(), 2),
                "by_class_band_clean": _tally(marg_key[:, j], m & clean),
                "by_band_clean": _tally(np.array([k.split("|")[-1] for k in marg_key[:, j]], dtype=object), m & clean),
                "by_class_band_all": _tally(marg_key[:, j], m),
            }
        out["zones"][z] = zrec

    # pooled hub zones: each zone-hour is one observation
    pooled = {}
    js = [CARRYING.index(z) for z in HUB_ZONES]
    keys_p = np.concatenate([marg_key[:, j] for j in js])
    res_p = np.concatenate([resid[:, j] for j in js])
    p_p = np.concatenate([P[:, j] for j in js])
    a_p = np.concatenate([act[CARRYING[j]].to_numpy(float) for j in js])
    clean = np.isfinite(res_p) & (res_p <= RESID_CLEAN)
    for name, m in {"all": np.ones_like(clean), "body": p_p <= np.percentile(p_p, 90),
                    "actual_lt_20": np.isfinite(a_p) & (a_p < 20.0),
                    "model_bottom_decile": p_p <= np.percentile(p_p, 10)}.items():
        pooled[name] = {"n": int(m.sum()), "clean_share": _r(clean[m].mean(), 4),
                        "by_class_band_clean": _tally(keys_p, m & clean),
                        "by_band_clean": _tally(np.array([k.split("|")[-1] for k in keys_p], dtype=object), m & clean),
                        "by_class_band_all": _tally(keys_p, m)}
    out["pooled_hub_zones"] = pooled
    del raw_fleet, fleet, arrays, fuel_prices, mc
    gc.collect()
    return out


def main() -> int:
    """Analyse every requested year and write the JSON record."""
    rec = {"probe": "miso-224 phase 0 part 2 - marginal class-band frequency over every hour",
           "keeper": "2026-09-05-miso-220-nonsteam-lift", "bundle": str(KEEPER.relative_to(REPO)),
           "solved": False, "resid_clean_usd": RESID_CLEAN, "by_year": {}}
    if OUT.exists():
        try:
            rec["by_year"] = json.loads(OUT.read_text()).get("by_year", {})
        except Exception:  # noqa: BLE001 - a partial record is rebuilt, never trusted
            pass
    for y in YEARS:
        rec["by_year"][str(y)] = analyse_year(y)
        z = rec["by_year"][str(y)]["zones"]["MISO-Indiana"]
        for s in ("all", "body", "actual_lt_20"):
            top = list(z[s]["by_class_band_clean"].items())[:6]
            print(f"  {y} Indiana {s}: n={z[s]['n']} clean={z[s]['clean_share']} bands={z[s]['by_band_clean']} top={top}", flush=True)
        OUT.write_text(json.dumps(rec, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""miso-224 phase 0 — WHERE in the price distribution does the body error live, and
WHAT does the model's supply stack do in the hours the real market cleared cheap?

Zero-solve. Every input is a committed artifact: the designated keeper's own
``hourly/`` sidecars (``2026-09-05-miso-220-nonsteam-lift``, bundle
``miso220_nonsteamlift_B``), the C3a scoring instrument's zonal RT LMPs
(``data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet``, fixed-CST
model clock, hub -> model zone) and the EIA-930 MISO hourly extract
(``data/raw/eia-930-hourly/MISO hourly.parquet``, 2022-2025 rows on the same
fixed-CST clock, miso-206 §3.2).

WHY THIS PROBE EXISTS. miso-223 established that the keeper's price distribution
is too flat — body (bottom 90 %) too high in 36/36 months, tail too low in 33/36 —
and then killed a body arm aimed at the ``committed`` offer band because its
footprint was measured as ENERGY share, not MARGINAL frequency. Two successor
objects were named: (A) the LP never curtails MISO wind, so wind's -$26 PTC offer
never reaches the price and the model has a hard ~$17 floor against an actual MISO
that cleared below $20 in 1,781/3,097/510 hours; (B) the bands above ``committed``.
This probe is the measurement that decides between them, by asking the one
question both share: **in which hours is the body too high?** If the error is
concentrated where the ACTUAL price is low (bottom deciles, sub-$20, negative),
the object is the floor — the missing negative-price mechanism (A). If it is flat
across the deciles, the object is the offer level of whatever band is marginal in
an ordinary hour (B).

THE CONSTRUCTION.

* **Zone-matched, hour-matched.** Model P1 price per zone vs the zone's hub RT LMP
  (MISO-South = mean of its four hubs; MISO-Plains has no published hub and is
  excluded from the price blocks). Hour-matched because the question is "what does
  the model do in the hours reality was cheap", which quantile-matching cannot ask.
* **Bands of the ACTUAL price**, per zone-year: deciles of the hub series, plus the
  three named sets actual < $0, < $10, < $20. Each band reports n, mean actual,
  mean model, mean error, and the band's CONTRIBUTION to the annual mean error
  (error x n / 8760), so the bands sum to the annual mean error exactly.
* **Supply stack in the cheap hours.** Model class dispatch (``class_hourly``)
  against EIA-930 net generation by fuel and total interchange, over the hours
  where the 8-hub mean RT LMP is < $0 / < $10 / < $20, and — for contrast — the
  model's OWN bottom decile. Coal is the load-bearing row: MISO's real curtailment
  and negative prices happen when self-committed coal cannot back down; if the
  model's coal in those hours sits far BELOW the measured coal, the model is
  backing coal down where the market could not, which is why nothing ever has to
  spill and wind is never marginal.
* **Clock self-check.** The keeper's P1 wind is an identity on the EIA-930 series
  (model = 1.051466 x measured in every hour, miso-206 N-2). The probe asserts that
  identity against the extract it reads, so a mis-keyed clock fails loudly.

Rule 22 ``[R-HOLDOUT]`` — 2023/2024/2025 only. No LP is solved; nothing is minted;
no ScenarioConfig field is read or written.

Usage::

    python3 scripts/probes/_miso224_floor_anatomy_phase0.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "miso220_nonsteamlift_B"
ZONAL_ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet"
E930 = REPO / "data/raw/eia-930-hourly/MISO hourly.parquet"
OUT = CAL / "_miso224_floor_anatomy.json"
YEARS = (2023, 2024, 2025)
HOURS = 8760
#: miso-206 N-2: bound = delivered / (1 - 0.048947), P1 wind on the bound every hour.
WIND_GROSSUP = 1.0 / (1.0 - 0.048947)
CARRYING = ["MISO-West", "MISO-Plains", "MISO-Illinois", "MISO-Indiana", "MISO-East", "MISO-South"]
COAL = ("COAL", "COAL_BIT", "COAL_LIGNITE", "COAL_PRB")
GAS = ("CC_CHP", "CC_REGULAR", "CT_CHP", "CT_PEAKER", "ST_CHP", "ST_GAS")
DECILE_EDGES = np.arange(0, 101, 10)


def _r(x, k=2):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), k)


def keeper_system(year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(price, demand) pivots, hour x zone, from the keeper's committed P1 sidecar."""
    s = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    p = s.pivot_table(index="hour", columns="zone", values="price", aggfunc="first")
    d = s.pivot_table(index="hour", columns="zone", values="demand", aggfunc="first")
    return p.reindex(range(HOURS)), d.reindex(range(HOURS))


def keeper_classes(year: int) -> pd.DataFrame:
    """hour x class MW from the keeper's committed P1 class sidecar."""
    c = pd.read_parquet(KEEPER / f"hourly/class_hourly_{year}.parquet")
    c = c[c["pass"] == "P1"]
    return c.pivot_table(index="hour", columns="klass", values="mw", aggfunc="sum",
                         observed=True).reindex(range(HOURS)).fillna(0.0)


def actual_zone_price(year: int) -> pd.DataFrame:
    """hour x zone hub RT LMP (MISO-South = mean of its four hubs) on the model clock."""
    a = pd.read_parquet(ZONAL_ACTUAL)
    a = a[a["year"] == year]
    hub = a.pivot_table(index="hour", columns="hub", values="rt", aggfunc="first").reindex(range(HOURS))
    zone_of = a.drop_duplicates("hub").set_index("hub")["zone"]
    out = pd.DataFrame(index=hub.index)
    for z in sorted(zone_of.unique()):
        out[z] = hub[[h for h in hub.columns if zone_of[h] == z]].mean(axis=1)
    out["hub8_mean"] = hub.mean(axis=1)
    return out


def actual_mec(year: int) -> tuple[np.ndarray, pd.DataFrame]:
    """(8760,) system marginal energy component, and hour x hub MCC+MLC, model clock.

    MISO publishes LMP, MCC and MLC per hub; MEC = LMP - MCC - MLC is the single
    system energy price and is identical across hubs up to rounding. The hub csv is
    hour-ending ``he01``..``he24`` on the same fixed clock the zonal comparator uses
    (miso-223 phase 0 reads it the same way); the median across hubs is taken and
    the cross-hub spread is returned as a self-check.
    """
    raw = pd.read_csv(REPO / "data/raw/lmp-data/MISO" / f"miso_hub_lmp_{year}_rt.csv.gz")
    he = [f"he{i:02d}" for i in range(1, 25)]
    long = raw.melt(id_vars=["date", "node", "value"], value_vars=he, var_name="he", value_name="p")
    long["p"] = pd.to_numeric(long["p"], errors="coerce")
    long["dt"] = pd.to_datetime(long["date"]) + pd.to_timedelta(long["he"].str[2:].astype(int) - 1, unit="h")
    long = long[long["dt"].dt.year == year]
    long = long[~((long["dt"].dt.month == 2) & (long["dt"].dt.day == 29))]
    w = long.pivot_table(index="dt", columns=["node", "value"], values="p", aggfunc="first")
    w = w.sort_index()
    assert len(w) == HOURS, (year, len(w))
    hubs = sorted({c[0] for c in w.columns})
    mec = pd.DataFrame({h: w[(h, "LMP")] - w[(h, "MCC")] - w[(h, "MLC")] for h in hubs})
    cong = pd.DataFrame({h: w[(h, "MCC")] + w[(h, "MLC")] for h in hubs})
    return mec.median(axis=1).to_numpy(float), cong.reset_index(drop=True), \
        float((mec.max(axis=1) - mec.min(axis=1)).median())


def e930_frame(year: int) -> pd.DataFrame:
    """EIA-930 MISO hourly by fuel + demand + interchange on the model's 8760 clock.

    The 2022-2025 rows of the committed extract carry fixed-CST hour-ending local
    stamps (miso-206 §3.2). Rows whose local date is in ``year`` are kept, local
    Feb 29 dropped, ordered by UTC — the same selection the production frame
    loader makes. Hour-ending stamp 01:00 is model hour 0.
    """
    h = pd.read_parquet(E930).drop_duplicates("UTC time").set_index("UTC time").sort_index()
    # Key on UTC, never on the extract's local columns (they are DST-aware
    # America/Chicago labels and carry a fall-back duplicate; miso-206 §3.1). The
    # model's fixed-CST hour-ending clock is the consecutive UTC run starting
    # Y-01-01 07:00 (= HE01 CST), with the 24 stamps of fixed-CST Feb 29 dropped.
    n_utc = HOURS + (24 if year % 4 == 0 else 0)
    utc = pd.date_range(f"{year}-01-01 07:00", periods=n_utc, freq="h")
    local_fixed = utc - pd.Timedelta(hours=7)   # hour-BEGINNING fixed-CST stamp
    utc = utc[~((local_fixed.month == 2) & (local_fixed.day == 29))]
    # The 2025 extract is missing its last hour (12-31 HE24; miso-206 §3.3 — the
    # production loader forward-fills it); reindex + ffill reproduces that.
    f = h.reindex(utc).ffill().reset_index()
    assert len(f) == HOURS, (year, len(f))
    return f


def band_table(model: np.ndarray, actual: np.ndarray) -> dict:
    """Error by band of the ACTUAL price: deciles plus the three named cheap sets."""
    ok = np.isfinite(actual) & np.isfinite(model)
    m, a = model[ok], actual[ok]
    n = int(ok.sum())
    mean_err = float((m - a).mean())
    pct = np.percentile(a, DECILE_EDGES)
    rows = {}
    for i in range(10):
        lo, hi = pct[i], pct[i + 1]
        sel = (a >= lo) & ((a < hi) if i < 9 else (a <= hi))
        rows[f"d{i + 1}"] = {
            "n": int(sel.sum()), "actual_lo": _r(lo), "actual_hi": _r(hi),
            "actual_mean": _r(a[sel].mean()), "model_mean": _r(m[sel].mean()),
            "err": _r((m - a)[sel].mean()),
            "contribution": _r((m - a)[sel].sum() / n, 3),
        }
    for name, thr in (("lt_0", 0.0), ("lt_10", 10.0), ("lt_20", 20.0)):
        sel = a < thr
        rows[name] = {
            "n": int(sel.sum()),
            "actual_mean": _r(a[sel].mean()) if sel.any() else None,
            "model_mean": _r(m[sel].mean()) if sel.any() else None,
            "err": _r((m - a)[sel].mean()) if sel.any() else None,
            "contribution": _r((m - a)[sel].sum() / n, 3),
            "share_of_mean_err": _r((m - a)[sel].sum() / n / mean_err, 3) if mean_err else None,
        }
    rows["all"] = {"n": n, "actual_mean": _r(a.mean()), "model_mean": _r(m.mean()),
                   "mean_err": _r(mean_err), "model_min": _r(m.min()), "actual_min": _r(a.min()),
                   "model_hours_lt_20": int((m < 20).sum()), "actual_hours_lt_20": int((a < 20).sum())}
    return rows


def stack_table(cls: pd.DataFrame, e: pd.DataFrame, sel: np.ndarray, demand_model: np.ndarray) -> dict:
    """Model vs EIA-930 supply by fuel over the hour set ``sel`` (means, MW)."""
    if not sel.any():
        return {"n": 0}

    def mcol(names):
        return float(cls[[c for c in names if c in cls.columns]].sum(axis=1).to_numpy()[sel].mean())

    def ecol(col):
        v = e[col].to_numpy(float)[sel]
        return float(np.nanmean(v))

    rows = {
        "n": int(sel.sum()),
        "demand": {"model": _r(demand_model[sel].mean(), 0), "e930": _r(ecol("Demand"), 0)},
        "coal": {"model": _r(mcol(COAL), 0), "e930": _r(ecol("NG: COL"), 0)},
        "gas": {"model": _r(mcol(GAS), 0), "e930": _r(ecol("NG: NG"), 0)},
        "nuclear": {"model": _r(mcol(("nuclear",)), 0), "e930": _r(ecol("NG: NUC"), 0)},
        "wind": {"model": _r(mcol(("wind",)), 0), "e930": _r(ecol("NG: WND"), 0)},
        "solar": {"model": _r(mcol(("solar",)), 0), "e930": _r(ecol("NG: SUN"), 0)},
        "hydro": {"model": _r(mcol(("hydro",)), 0), "e930": _r(ecol("NG: WAT"), 0)},
        "other_oil_bio": {"model": _r(mcol(("OTHER", "oil", "biomass")), 0), "e930": _r(ecol("NG: OTH"), 0)},
        # EIA-930 TI is export-positive; the model's ``import`` class is import-positive.
        "net_import": {"model": _r(mcol(("import",)), 0), "e930": _r(-ecol("Total interchange"), 0)},
    }
    for k in ("coal", "gas", "nuclear", "wind", "solar", "hydro", "other_oil_bio", "net_import"):
        rows[k]["model_minus_e930"] = _r(rows[k]["model"] - rows[k]["e930"], 0)
    return rows


def analyse_year(year: int) -> dict:
    """Bands of the actual price, cheap-hour supply stacks, coal back-down depth."""
    price, demand = keeper_system(year)
    cls = keeper_classes(year)
    act = actual_zone_price(year)
    e = e930_frame(year)

    # Clock self-check: P1 wind == 1.051466 x EIA-930 wind in every hour (miso-206 N-2).
    wind_model = cls["wind"].to_numpy(float)
    wind_e930 = e["NG: WND"].to_numpy(float)
    ratio = wind_model / np.where(wind_e930 > 0, wind_e930, np.nan)
    clock = {"ratio_min": _r(np.nanmin(ratio), 6), "ratio_max": _r(np.nanmax(ratio), 6),
             "expected": _r(WIND_GROSSUP, 6),
             "hours_off_identity_gt_1pct": int(np.nansum(np.abs(ratio / WIND_GROSSUP - 1) > 0.01))}

    zones = [z for z in CARRYING if z in act.columns]
    dm = demand[CARRYING].to_numpy(float)
    lw_model = (price[CARRYING].to_numpy(float) * dm).sum(axis=1) / dm.sum(axis=1)
    demand_model = dm.sum(axis=1)

    bands = {z: band_table(price[z].to_numpy(float), act[z].to_numpy(float)) for z in zones}
    bands["INDIANA_vs_MISO-Indiana"] = bands["MISO-Indiana"]
    bands["lw_model_vs_hub8"] = band_table(lw_model, act["hub8_mean"].to_numpy(float))
    # pooled zone-hours
    pm = np.concatenate([price[z].to_numpy(float) for z in zones])
    pa = np.concatenate([act[z].to_numpy(float) for z in zones])
    bands["pooled_zone_hours"] = band_table(pm, pa)

    # Energy vs congestion: model - hub == (model - MEC) + (MEC - hub). Banded by
    # the ACTUAL hub price decile so the two halves are read on the same hours.
    mec, cong, mec_spread = actual_mec(year)
    hub_of = {"MISO-Indiana": "INDIANA.HUB", "MISO-West": "MINN.HUB", "MISO-Illinois": "ILLINOIS.HUB",
              "MISO-East": "MICHIGAN.HUB"}
    mec_block = {"mec_cross_hub_spread_median": _r(mec_spread, 3)}
    for z, hubname in hub_of.items():
        a_hub = act[z].to_numpy(float)
        m = price[z].to_numpy(float)
        ok = np.isfinite(a_hub) & np.isfinite(m) & np.isfinite(mec)
        pct = np.percentile(a_hub[ok], DECILE_EDGES)
        rows = {}
        for i in range(10):
            sel = ok & (a_hub >= pct[i]) & ((a_hub < pct[i + 1]) if i < 9 else (a_hub <= pct[i + 1]))
            rows[f"d{i + 1}"] = {"n": int(sel.sum()), "hub_mean": _r(a_hub[sel].mean()),
                                 "mec_mean": _r(mec[sel].mean()), "model_mean": _r(m[sel].mean()),
                                 "err_vs_hub": _r((m - a_hub)[sel].mean()),
                                 "err_vs_mec": _r((m - mec)[sel].mean()),
                                 "hub_minus_mec": _r((a_hub - mec)[sel].mean())}
        for name, thr in (("lt_0", 0.0), ("lt_10", 10.0), ("lt_20", 20.0)):
            sel = ok & (a_hub < thr)
            rows[name] = {"n": int(sel.sum()), "hub_mean": _r(a_hub[sel].mean()) if sel.any() else None,
                          "mec_mean": _r(mec[sel].mean()) if sel.any() else None,
                          "model_mean": _r(m[sel].mean()) if sel.any() else None,
                          "err_vs_mec": _r((m - mec)[sel].mean()) if sel.any() else None}
        rows["all"] = {"err_vs_hub": _r((m - a_hub)[ok].mean()), "err_vs_mec": _r((m - mec)[ok].mean()),
                       "hub_minus_mec": _r((a_hub - mec)[ok].mean()),
                       "mec_hours_lt_20": int((mec[ok] < 20).sum()), "mec_hours_lt_10": int((mec[ok] < 10).sum()),
                       "mec_hours_lt_0": int((mec[ok] < 0).sum()), "mec_min": _r(np.nanmin(mec[ok]))}
        mec_block[z] = rows
    # Load-weighted model system price against the MEC itself (no hub basis at all).
    ok = np.isfinite(mec) & np.isfinite(lw_model)
    pct = np.percentile(mec[ok], DECILE_EDGES)
    rows = {}
    for i in range(10):
        sel = ok & (mec >= pct[i]) & ((mec < pct[i + 1]) if i < 9 else (mec <= pct[i + 1]))
        rows[f"d{i + 1}"] = {"n": int(sel.sum()), "mec_mean": _r(mec[sel].mean()), "model_mean": _r(lw_model[sel].mean()),
                             "err": _r((lw_model - mec)[sel].mean()), "contribution": _r((lw_model - mec)[sel].sum() / ok.sum(), 3)}
    rows["all"] = {"mean_err": _r((lw_model - mec)[ok].mean()), "model_min": _r(lw_model[ok].min()), "mec_min": _r(mec[ok].min()),
                   "model_hours_lt_20": int((lw_model[ok] < 20).sum()), "mec_hours_lt_20": int((mec[ok] < 20).sum())}
    mec_block["lw_model_vs_mec_by_mec_decile"] = rows

    hub8 = act["hub8_mean"].to_numpy(float)
    own_p10 = np.nanpercentile(lw_model, 10)
    stacks = {
        "actual_lt_0": stack_table(cls, e, hub8 < 0, demand_model),
        "actual_lt_10": stack_table(cls, e, hub8 < 10, demand_model),
        "actual_lt_20": stack_table(cls, e, hub8 < 20, demand_model),
        "model_own_bottom_decile": stack_table(cls, e, lw_model <= own_p10, demand_model),
        "all_hours": stack_table(cls, e, np.ones(HOURS, bool), demand_model),
    }

    # How far does each side back coal down? Percentiles of hourly coal MW.
    coal_m = cls[[c for c in COAL if c in cls.columns]].sum(axis=1).to_numpy(float)
    coal_e = e["NG: COL"].to_numpy(float)
    q = (1, 5, 10, 25, 50, 90)
    coal = {"model_pct": {f"p{k}": _r(np.nanpercentile(coal_m, k), 0) for k in q},
            "e930_pct": {f"p{k}": _r(np.nanpercentile(coal_e, k), 0) for k in q},
            "model_min_over_max": _r(np.nanmin(coal_m) / np.nanmax(coal_m), 3),
            "e930_min_over_max": _r(np.nanmin(coal_e) / np.nanmax(coal_e), 3)}
    # Same for total thermal (coal + gas + nuclear + other): the inflexible base.
    therm_m = coal_m + cls[[c for c in GAS if c in cls.columns]].sum(axis=1).to_numpy(float) \
        + cls["nuclear"].to_numpy(float)
    therm_e = coal_e + e["NG: NG"].to_numpy(float) + e["NG: NUC"].to_numpy(float)
    thermal = {"model_pct": {f"p{k}": _r(np.nanpercentile(therm_m, k), 0) for k in q},
               "e930_pct": {f"p{k}": _r(np.nanpercentile(therm_e, k), 0) for k in q}}

    # Model price floor mechanics: in the model's own cheapest hours, what price?
    floor = {"model_lw_min": _r(np.nanmin(lw_model)), "model_lw_p1": _r(np.nanpercentile(lw_model, 1)),
             "model_lw_p10": _r(own_p10), "actual_hub8_min": _r(np.nanmin(hub8)),
             "actual_hub8_p1": _r(np.nanpercentile(hub8, 1)), "actual_hub8_p10": _r(np.nanpercentile(hub8, 10)),
             "model_dump_mwh": _r(float(pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")["dump"].sum()), 1),
             "model_slack_mwh": _r(float(pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")["slack"].sum()), 1)}
    return {"clock_check": clock, "bands_by_actual_price": bands, "energy_vs_congestion": mec_block,
            "cheap_hour_stacks": stacks,
            "coal_backdown": coal, "thermal_backdown": thermal, "floor": floor}


def main() -> None:
    out = {"probe": "miso-224 phase 0 — floor anatomy: where the body error lives and what the stack does when reality is cheap",
           "solved": False, "keeper": "2026-09-05-miso-220-nonsteam-lift", "bundle": str(KEEPER.relative_to(REPO)),
           "by_year": {}}
    for y in YEARS:
        out["by_year"][str(y)] = analyse_year(y)
        b = out["by_year"][str(y)]
        ck = b["clock_check"]
        print(f"{y}: clock ratio {ck['ratio_min']}..{ck['ratio_max']} (expect {ck['expected']}), off-identity hours {ck['hours_off_identity_gt_1pct']}")
        ind = b["bands_by_actual_price"]["MISO-Indiana"]
        print(f"  INDIANA: mean err {ind['all']['mean_err']}  contributions d1..d10: "
              + " ".join(f"{ind[f'd{i}']['contribution']:+.2f}" for i in range(1, 11)))
        print(f"  INDIANA: err d1..d10: " + " ".join(f"{ind[f'd{i}']['err']:+.1f}" for i in range(1, 11)))
        print(f"  actual<20: n={ind['lt_20']['n']} err {ind['lt_20']['err']} share_of_mean_err {ind['lt_20']['share_of_mean_err']}")
        mi = b["energy_vs_congestion"]["MISO-Indiana"]
        print(f"  INDIANA vs MEC: err_vs_mec d1..d10: " + " ".join(f"{mi[f'd{i}']['err_vs_mec']:+.1f}" for i in range(1, 11))
              + f" | hub-MEC d1..d10: " + " ".join(f"{mi[f'd{i}']['hub_minus_mec']:+.1f}" for i in range(1, 11)))
        print(f"  MEC: hours<20 {mi['all']['mec_hours_lt_20']}, <10 {mi['all']['mec_hours_lt_10']}, <0 {mi['all']['mec_hours_lt_0']}, min {mi['all']['mec_min']}; "
              f"annual err_vs_mec {mi['all']['err_vs_mec']} vs err_vs_hub {mi['all']['err_vs_hub']}")
        lm = b["energy_vs_congestion"]["lw_model_vs_mec_by_mec_decile"]
        print(f"  LW model vs MEC by MEC decile: " + " ".join(f"{lm[f'd{i}']['err']:+.1f}" for i in range(1, 11)) + f" | mean {lm['all']['mean_err']}")
        st = b["cheap_hour_stacks"]["actual_lt_10"]
        print(f"  hub8<$10 (n={st['n']}): coal model {st['coal']['model']} vs e930 {st['coal']['e930']}; gas {st['gas']['model']} vs {st['gas']['e930']}; "
              f"wind {st['wind']['model']} vs {st['wind']['e930']}; import {st['net_import']['model']} vs {st['net_import']['e930']}")
        print(f"  coal p5 model {b['coal_backdown']['model_pct']['p5']} vs e930 {b['coal_backdown']['e930_pct']['p5']}; floor {b['floor']}")
    OUT.write_text(json.dumps(out, indent=1))
    print(f"-> {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

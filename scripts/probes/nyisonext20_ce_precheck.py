"""NYISO-NEXT-20 (ZERO LP): the NEXT-19 card's section-4 pre-check of a CENTRAL EAST flowgate.

Tests whether one zonal shift-factor row,

    CE(t) = k_F * (r * TE(t) + (1 - r) * W_F(t))  <=  posted CE limit(t)

(``docs/records/nyiso/DESIGN-nyiso-next19-ce-flowgate-2026-10-01.md`` section 3, with
``W_GK = TE - W_F``), could carry CENTRAL EAST in the 5-zone model. Gates
P-1 / P-2 / P-3 were fixed in that card before this probe was written. The
method choices below were fixed before the probe ran (NYISO-NEXT-20,
2026-10-01). None was changed after the results were seen.

Inputs (committed or regenerable raw data only):

* RT 5-min zonal congestion components, ``data/raw/lmp-data/NYISO``
  (P-24B, 2021-2025, intake by ``scripts/data/fetch_nyiso_zonal_lmp.py``).
  Stamps are interval-ENDING (README convention). Congestion is taken
  relative to MHK VL (zone E), and the sign is flipped so that a positive
  value raises the zone's LBMP.
* Hourly CE flow, CE posted limit and TOTAL EAST flow, plus the ``SCH - NE -
  NY`` AC schedule (positive = into NY), ``data/raw/NYISO/interface-flows``.
* F (CAPITL) hourly load, ``data/raw/zone-specific-demand/NYISO``.
* F-sited generation: CAMPD hourly ``grossLoad`` for every facility whose
  EIA-860 county is a zone-F county (``zone_assignment``'s
  NYISO_CAPITAL_HUDSON_COUNTIES minus the NEXT-17 Hudson-Valley set), plus,
  for every F plant with no CAMPD hours, its EIA-923 annual net generation
  spread flat over the year's hours. EIA-923 is available through 2025.

Fixed method choices:

1. ``W_F = F load - F generation - NE-NY AC schedule``. The whole NE AC
   schedule lands in F, as in the fg_split topology (spec.py
   ``NYISO_NE_AC_LANDING``).
2. Active (binding) hour: hourly mean F-E congestion > $5/MWh, the NEXT-19
   probe screen. Active 5-min interval: the same screen on the interval.
3. ``r`` per interval = mean of the five G-K zone congestion values / F
   congestion, on active intervals. Network vintages: V1 = before
   2023-12-01 (pre AC Transmission); V2 = from 2023-12-01. The vintage
   value is the median of ``r`` over all active intervals in the vintage.
4. ``k_F`` per vintage = least-squares fit through the origin of measured CE
   flow on ``X = r*TE + (1-r)*W_F``, over that vintage's active hours.
5. P-1: share of a year's hours with LHS > 1.05 x posted limit, LHS =
   k_F * X. Pass at <= 10 %.
6. P-2: mean F-E congestion over the year's top-decile hours of LHS / limit,
   divided by the mean over all hours. Pass at >= 2.0.
7. P-3: monthly median ``r`` within +/-0.10 of the vintage value. A month
   with fewer than 12 active intervals (one hour) is UNIDENTIFIED and does
   not count as within. Pass at >= 10 of 12 months.
8. Robustness bound for the unmeasured hourly F pumped storage (Blenheim-
   Gilboa, 1,160 MW, only its annual net is measured): P-1 is re-scored
   with Gilboa generating at full output in every hour (W_F lower by
   1,160 MW). If P-1 still fails, the failure does not come from that gap.

Usage::

    python3 scripts/probes/nyisonext20_ce_precheck.py \
        --out results/phase0/nyiso/_nyisonext20_ce_precheck.json
"""

from __future__ import annotations

import argparse
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
RAW = REPO / "data/raw"
YEARS = [2021, 2022, 2023, 2024, 2025]
GK = ["HUD VL", "MILLWD", "DUNWOD", "N.Y.C.", "LONGIL"]
F_COUNTIES = {"Albany", "Columbia", "Greene", "Rensselaer", "Saratoga",
              "Schenectady", "Schoharie", "Warren", "Washington"}  # zone_assignment F set
ACTIVE_USD = 5.0          # F-E congestion screen, $/MWh (NEXT-19 probe, card section 1)
V2_START = pd.Timestamp("2023-12-01")  # NY Transco AC Transmission energized, card section 5.2
GILBOA_MW = 1160.0        # Blenheim-Gilboa pumped-storage rating, NYISO Gold Book
GATES = {"P1_max_share": 0.10, "P1_tol": 0.05, "P2_min_lift": 2.0,
         "P3_band": 0.10, "P3_min_months": 10, "P3_min_intervals": 12}
TZ = "America/New_York"
CONG = "Marginal Cost Congestion ($/MWHr)"


def _local(ts: pd.Series) -> pd.Series:
    """Localize naive prevailing-time stamps; DST-ambiguous stamps become NaT."""
    return ts.dt.tz_localize(TZ, ambiguous="NaT", nonexistent="NaT")


def rt_congestion() -> pd.DataFrame:
    """5-min congestion relative to E, sign flipped (positive raises LBMP); index = interval end."""
    frames = []
    for y in YEARS:
        for f in sorted((RAW / "lmp-data/NYISO").glob(f"{y}??01realtime_zone_csv.zip")):
            z = zipfile.ZipFile(f)
            frames += [pd.read_csv(z.open(n), usecols=["Time Stamp", "Name", CONG]) for n in z.namelist()]
    d = pd.concat(frames)
    d["t"] = pd.to_datetime(d["Time Stamp"], format="%m/%d/%Y %H:%M:%S")
    c = d.pivot_table(index="t", columns="Name", values=CONG)
    return -c.sub(c["MHK VL"], axis=0)


def hourly_congestion(c5: pd.DataFrame) -> pd.DataFrame:
    """Hour-beginning UTC mean of the 5-min congestion (interval-ending -> beginning)."""
    h = c5.copy()
    h.index = (h.index - pd.Timedelta(minutes=5)).floor("h")
    h = h.groupby(level=0).mean()
    idx = _local(pd.Series(h.index, index=h.index))
    h = h[idx.notna().to_numpy()]
    h.index = idx.dropna().dt.tz_convert("UTC").to_numpy()
    return h


def flows(year: int) -> pd.DataFrame:
    """CE flow / limit, TE flow and the NE-NY AC schedule, hourly, UTC index."""
    f = pd.read_csv(RAW / f"NYISO/interface-flows/NYISO_interface_flows_hourly_{year}.csv.gz")
    f["t"] = pd.to_datetime(f.interval_start_utc, utc=True)
    p = f.pivot_table(index="t", columns="interface", values="flow_mw")
    lim = f[f.interface == "CENTRAL EAST - VC"].drop_duplicates("t").set_index("t").positive_limit_mw
    return pd.DataFrame({"ce": p["CENTRAL EAST - VC"], "te": p["TOTAL EAST"],
                         "ne_ny": p["SCH - NE - NY"], "lim": lim})


def f_load(year: int) -> pd.Series:
    """F (CAPITL) integrated hourly load, UTC index."""
    d = pd.read_csv(RAW / f"zone-specific-demand/NYISO/NYISO_load_actuals_{year}.csv")
    d = d[d.Name == "CAPITL"].copy()
    d["t"] = _local(pd.to_datetime(d["Time Stamp"]))
    d = d.dropna(subset=["t"]).drop_duplicates("t")
    return d.set_index(d.t.dt.tz_convert("UTC"))["Load"]


def f_generation(year: int, f_plants: set[int]) -> tuple[pd.Series, dict]:
    """F-sited generation: CAMPD hourly gross MW + EIA-923 flat MW for non-CAMPD F plants."""
    c = pd.read_parquet(RAW / f"campd-unit-level/NY_{year}.parquet",
                        columns=["facilityId", "date", "hour", "grossLoad"])
    c["facilityId"] = pd.to_numeric(c.facilityId, errors="coerce")  # CAMPD stores ORIS as str
    c = c[c.facilityId.isin(f_plants)]
    # CAMPD hours are local STANDARD time (UTC-5 all year).
    c["t"] = (pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], "h")
              + pd.Timedelta(hours=5)).dt.tz_localize("UTC")
    hourly = c.groupby("t").grossLoad.sum(min_count=1).fillna(0.0)
    campd_ids = set(c.loc[c.grossLoad.fillna(0) > 0, "facilityId"].unique())
    e = pd.read_csv(RAW / "eia-923-generation-fuel/eia923_generation_fuel_2019_2025.csv")
    e = e[(e.year == year) & e.plant_id.isin(f_plants - campd_ids)]
    flat_mw = float(e.net_generation_mwh.sum()) / 8760.0
    gilboa = float(e.loc[e.plant_id == 2691, "net_generation_mwh"].sum())
    return hourly + flat_mw, {"campd_facilities": len(campd_ids), "campd_mean_mw": round(float(hourly.mean()), 1),
                              "noncampd_flat_mw": round(flat_mw, 1), "gilboa_net_mwh": gilboa}


def main(argv: list[str] | None = None) -> int:
    """Run the pre-check and write the JSON record."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=REPO / "results/phase0/nyiso/_nyisonext20_ce_precheck.json")
    a = ap.parse_args(argv)

    p = pd.read_parquet(RAW / "eia-860/eia860_plant.parquet")
    f_plants = set(p.loc[(p.State == "NY") & p.County.isin(F_COUNTIES), "Plant Code"].astype(int))

    c5 = rt_congestion()
    act5 = c5["CAPITL"] > ACTIVE_USD
    r5 = (c5.loc[act5, GK].mean(axis=1) / c5.loc[act5, "CAPITL"])
    v2_5 = r5.index >= V2_START
    r_vint = {"V1": float(r5[~v2_5].median()), "V2": float(r5[v2_5].median())}
    n_vint = {"V1": int((~v2_5).sum()), "V2": int(v2_5.sum())}
    ch = hourly_congestion(c5)

    rows, gen_meta = [], {}
    for y in YEARS:
        g, gen_meta[y] = f_generation(y, f_plants)
        d = flows(y).join(f_load(y).rename("lf"), how="inner").join(g.rename("gf"), how="left")
        d["gf"] = d.gf.fillna(gen_meta[y]["noncampd_flat_mw"])
        d = d.join(ch["CAPITL"].rename("fe"), how="left")
        d["year"] = y
        rows.append(d)
    d = pd.concat(rows).dropna(subset=["ce", "te", "ne_ny", "lim", "lf"])
    d["wf"] = d.lf - d.gf - d.ne_ny
    loc = d.index.tz_convert(TZ).tz_localize(None)
    d["vint"] = np.where(loc >= V2_START, "V2", "V1")
    d["r"] = d.vint.map(r_vint)
    d["x"] = d.r * d.te + (1 - d.r) * d.wf

    k_f, fit = {}, {}
    for v in ("V1", "V2"):
        m = (d.vint == v) & (d.fe > ACTIVE_USD)
        x, y_ = d.x[m].to_numpy(), d.ce[m].to_numpy()
        k = float(x @ y_ / (x @ x))
        k_f[v] = k
        res = y_ - k * x
        fit[v] = {"active_hours": int(m.sum()), "k_F": round(k, 4),
                  "r2_uncentered": round(1 - float(res @ res) / float(y_ @ y_), 4),
                  "resid_sd_mw": round(float(res.std()), 1)}
    d["lhs"] = d.vint.map(k_f) * d.x
    d["lhs_gilboa"] = d.vint.map(k_f) * (d.x - (1 - d.r) * GILBOA_MW)
    d["load_ratio"] = d.lhs / d.lim
    # DF-route analog (CE = alpha * TE, alpha fit the same way): the comparison the card cites.
    alpha = {v: float((d.te[(d.vint == v) & (d.fe > ACTIVE_USD)] @ d.ce[(d.vint == v) & (d.fe > ACTIVE_USD)])
                      / (d.te[(d.vint == v) & (d.fe > ACTIVE_USD)] ** 2).sum()) for v in ("V1", "V2")}
    d["lhs_df"] = d.vint.map(alpha) * d.te

    tol = 1 + GATES["P1_tol"]
    per_year = {}
    for y in YEARS:
        s = d[d.year == y]
        p1 = float((s.lhs > tol * s.lim).mean())
        p1g = float((s.lhs_gilboa > tol * s.lim).mean())
        p1_df = float((s.lhs_df > tol * s.lim).mean())
        p1_meas = float((s.ce > tol * s.lim).mean())
        top = s.load_ratio >= s.load_ratio.quantile(0.9)
        fe_all = float(s.fe.mean())
        lift = float(s.fe[top].mean()) / fe_all if fe_all > 0 else float("nan")
        r_y = r5[r5.index.year == y]
        months = {}
        for mo in range(1, 13):
            rm = r_y[r_y.index.month == mo]
            vref = r_vint["V2" if pd.Timestamp(y, mo, 1) >= V2_START else "V1"]
            med = float(rm.median()) if len(rm) else float("nan")
            ok = len(rm) >= GATES["P3_min_intervals"] and abs(med - vref) <= GATES["P3_band"]
            months[mo] = {"n": int(len(rm)), "median_r": round(med, 3) if len(rm) else None, "within": bool(ok)}
        n_ok = sum(v["within"] for v in months.values())
        per_year[y] = {
            "hours": int(len(s)), "active_hours": int((s.fe > ACTIVE_USD).sum()),
            "mean_FE_congestion": round(fe_all, 2),
            "P1_share": round(p1, 4), "P1_pass": p1 <= GATES["P1_max_share"],
            "P1_share_gilboa_full_bound": round(p1g, 4),
            "P1_share_DF_alpha_TE": round(p1_df, 4), "P1_share_measured_CE": round(p1_meas, 4),
            "P2_lift": round(lift, 3), "P2_pass": bool(lift >= GATES["P2_min_lift"]),
            "P3_months_within": n_ok, "P3_pass": n_ok >= GATES["P3_min_months"], "P3_months": months,
            "mean_wf_mw": round(float(s.wf.mean()), 1), "sd_wf_mw": round(float(s.wf.std()), 1),
            "f_generation": gen_meta[y],
        }

    rec = {"gates": GATES, "active_rule": f"F-E congestion > ${ACTIVE_USD}/MWh",
           "r_vintage": {k: round(v, 4) for k, v in r_vint.items()}, "r_vintage_intervals": n_vint,
           "k_F_fit": fit, "alpha_DF_analog": {k: round(v, 4) for k, v in alpha.items()},
           "f_plants_eia860": len(f_plants), "per_year": per_year}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rec, indent=1, default=float))
    summ = {y: {k: v for k, v in r.items() if k not in ("P3_months", "f_generation")} for y, r in per_year.items()}
    print(json.dumps({"r_vintage": rec["r_vintage"], "n": n_vint, "k_F_fit": fit,
                      "alpha": rec["alpha_DF_analog"], "per_year": summ}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

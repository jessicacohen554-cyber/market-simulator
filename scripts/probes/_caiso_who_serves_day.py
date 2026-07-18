"""WHO-SERVES-THE-DAY decomposition (CAISO-95 C5a root-cause lane, no new LP).

The caiso-94 promotion added C5a to the fail set (model CO2 vs eGRID
-13.3/-11.2/-16.5 % 2023/24/25) because the EF-0 daytime clean import displaces
in-state CC gas: the model UNDER-produces gas vs the metered CAISO fleet
(CC_REGULAR -2.96/-1.41/-4.40 TWh after the daytime import; CT_PEAKER/CT_CHP/
ST_GAS chronically under). This script answers the lane's question (a) — is the
gap UNDER-COMMITMENT (fewer CC/CT plant-hours online than the metered fleet) or
UNDER-DISPATCH (units online but out-competed to lower MW) — from a solved
same-machine bundle (``_caiso95_repro_A.py``) against measured CEMS/EIA-930,
by class x hour-of-day x month. NO LP; derive-first (caiso-86b/88/93/94
discipline). Mirrors `_caiso_who_serves_night.py` (hod 6-21 instead of 0-5).

Decomposition identity, per gas class x year x window:
    E = OH x L        (energy = online-cap-hours x conditional loading)
    dE = dOH x L_cems  +  OH_model x dL     (commitment part + dispatch part)
where online = output > 5 % of plant capacity (the run detector's
``run_threshold_frac``), capacity = max(model-year max MW, CEMS-year max
grossLoad) per plant (a same-basis proxy; fleet pmax is not persisted in the
bundle), OH = sum over plants of capacity x online-hours, L = E / OH.

MODEL side: dispatch/{y}_P1.parquet (klass, plant_code, hour, mw).
MEASURED side: CAMPD facility CEMS CA_{y}.parquet (grossLoad, co2Mass) via the
plant_code->klass map + LA-Basin repowering ORISPL crosswalk; EIA-930 CISO for
the non-CEMS context rows (imports/hydro/solar/wind/demand).

CO2 attribution (C5a bridge): per class, the CEMS-implied intensity
(co2Mass/grossLoad, t/MWh) x the model-vs-CEMS energy gap = the tons of the
C5a miss explained by DISPATCH energy alone (rate-side residual reported as
the remainder vs the bench eGRID actual).

Month convention: model hours use the repo's non-leap 8760 calendar
(``MONTH_OF_HOUR``, the derive-script convention); CEMS months come from the
measured date column (2024's leap day lands in measured Feb — disclosed,
immaterial at month grain).

Usage: python scripts/probes/_caiso_who_serves_day.py <bundle_dir>
"""

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
EIA930 = REPO / "data" / "raw" / "eia-930-hourly" / "CISO hourly.parquet"
CAMPD = REPO / "data" / "raw" / "campd-facility-level"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "CAISO"
YEARS = (2023, 2024, 2025)
DAY = list(range(6, 22))  # hod 6-21, the caiso-94 daytime window
ONLINE_FRAC = 0.05  # run detector threshold (caiso_ra_mustoffer_min_gen)
GAS_KLASSES = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP")
# LA-Basin repowering: CEMS facilityId -> EIA plant_code (fleet/klass key).
LA_BASIN = {"315": 62115, "335": 62116, "330": 57901}
_DAYS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
MONTH_OF_HOUR = np.repeat(np.arange(1, 13), [d * 24 for d in _DAYS])  # len 8760


def load_model(bundle: Path):
    """Per-year model plant-hour gas matrix + klass map + class hod profiles."""
    out = {}
    klass_map = {}
    for y in YEARS:
        d = pd.read_parquet(
            bundle / "dispatch" / f"{y}_P1.parquet",
            columns=["klass", "plant_code", "hour", "mw"],
        )
        for pc, k in (
            d[["plant_code", "klass"]].drop_duplicates().itertuples(index=False)
        ):
            klass_map[int(pc)] = k
        d = d[d.klass.isin(GAS_KLASSES)].copy()
        # collapse tranches -> plant-hour
        ph = d.groupby(["plant_code", "hour"], observed=True).mw.sum().reset_index()
        ph["hod"] = ph.hour.to_numpy() % 24
        ph["month"] = MONTH_OF_HOUR[ph.hour.to_numpy()]
        ph["klass"] = ph.plant_code.map(klass_map)
        out[y] = ph
    return out, klass_map


def load_cems(klass_map: dict):
    """Per-year measured plant-hour matrix (grossLoad MW, co2Mass t) by klass."""
    out = {}
    for y in YEARS:
        d = pd.read_parquet(
            CAMPD / f"CA_{y}.parquet",
            columns=["facilityId", "date", "hour", "grossLoad", "co2Mass"],
        )
        fid = d.facilityId.astype(str)
        pc = fid.map(LA_BASIN)
        pc = pd.to_numeric(pc.fillna(pd.to_numeric(fid, errors="coerce")))
        d = d.assign(plant_code=pc)
        d["klass"] = d.plant_code.map(klass_map)
        d["month"] = pd.to_datetime(d.date).dt.month
        d = d.rename(columns={"hour": "hod"})
        d.grossLoad = d.grossLoad.fillna(0.0)
        out[y] = d
    return out


def plant_caps(model_ph: pd.DataFrame, cems: pd.DataFrame) -> pd.Series:
    """Per-plant capacity proxy: max(model max MW, CEMS max grossLoad)."""
    mmax = model_ph.groupby("plant_code").mw.max()
    cmax = cems.groupby("plant_code").grossLoad.max()
    return (
        mmax.to_frame("m").join(cmax.to_frame("c"), how="outer").fillna(0.0).max(axis=1)
    )


def window_stats(df, valcol, caps, hods, months=None):
    """(E TWh, OH TW·h online-cap-hours, L loading, on-share) over a window."""
    sub = df[df.hod.isin(hods)]
    if months is not None:
        sub = sub[sub.month.isin(months)]
    cap = sub.plant_code.map(caps)
    on = sub[valcol].to_numpy() > ONLINE_FRAC * cap.to_numpy()
    e = float(sub[valcol].sum() / 1e6)
    oh = float((cap.to_numpy() * on).sum() / 1e6)
    load = e / oh if oh > 0 else float("nan")
    return e, oh, load


def decompose(m, c):
    """Commitment/dispatch split: dE = dOH x L_c + OH_m x dL."""
    e_m, oh_m, l_m = m
    e_c, oh_c, l_c = c
    de = e_m - e_c
    commit = (oh_m - oh_c) * (l_c if np.isfinite(l_c) else 0.0)
    dispatch = oh_m * ((l_m - l_c) if np.isfinite(l_m) and np.isfinite(l_c) else 0.0)
    return de, commit, dispatch


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    bundle = Path(sys.argv[1])
    model, klass_map = load_model(bundle)
    cems = load_cems(klass_map)

    for y in YEARS:
        mm, cc = model[y], cems[y]
        caps = plant_caps(mm, cc)
        print(f"\n===================== {y} =====================")
        print(
            f"{'class':<12}{'win':<7}{'E_mod':>8}{'E_cems':>8}{'dE':>7}"
            f"{'OH_mod':>8}{'OH_cems':>8}{'L_mod':>7}{'L_cems':>7}"
            f"{'d_commit':>9}{'d_disp':>8}"
        )
        for k in GAS_KLASSES:
            mk = mm[mm.klass == k]
            ck = cc[cc.klass == k]
            if mk.empty and ck.empty:
                continue
            for lbl, hods in (
                ("day", DAY),
                ("night", [h for h in range(24) if h not in DAY]),
            ):
                ms = window_stats(mk, "mw", caps, hods)
                cs = window_stats(ck, "grossLoad", caps, hods)
                de, dcom, ddis = decompose(ms, cs)
                print(
                    f"{k:<12}{lbl:<7}{ms[0]:>8.2f}{cs[0]:>8.2f}{de:>7.2f}"
                    f"{ms[1]:>8.2f}{cs[1]:>8.2f}{ms[2]:>7.2f}{cs[2]:>7.2f}"
                    f"{dcom:>9.2f}{ddis:>8.2f}"
                )

        # hod profile (avg MW + online cap) for the big four
        print("\n-- hod profile: avg MW model|cems  (online-cap GW model|cems) --")
        for k in ("CC_REGULAR", "CT_PEAKER", "CT_CHP", "ST_GAS"):
            mk = mm[mm.klass == k]
            ck = cc[cc.klass == k]
            if mk.empty and ck.empty:
                continue
            days_in_year = 365
            rowm, rowc, ocm, occ = [], [], [], []
            capm = mk.plant_code.map(caps).to_numpy()
            capc = ck.plant_code.map(caps).to_numpy()
            onm = mk.mw.to_numpy() > ONLINE_FRAC * capm
            onc = ck.grossLoad.to_numpy() > ONLINE_FRAC * capc
            for h in range(24):
                im = (mk.hod == h).to_numpy()
                ic = (ck.hod == h).to_numpy()
                rowm.append(mk.mw.to_numpy()[im].sum() / days_in_year)
                rowc.append(ck.grossLoad.to_numpy()[ic].sum() / days_in_year)
                ocm.append((capm[im] * onm[im]).sum() / days_in_year / 1e3)
                occ.append((capc[ic] * onc[ic]).sum() / days_in_year / 1e3)
            print(f"  {k}:")
            print(
                "    MW  m:",
                " ".join(f"{v:5.0f}" for v in rowm),
                "\n        c:",
                " ".join(f"{v:5.0f}" for v in rowc),
            )
            print(
                "    GWon m:",
                " ".join(f"{v:5.1f}" for v in ocm),
                "\n         c:",
                " ".join(f"{v:5.1f}" for v in occ),
            )

        # CC loading-when-on distribution (day window): min-load vs full-load
        print("\n-- day-window loading-when-on distribution (share of on cap-hours) --")
        for k in ("CC_REGULAR", "CT_PEAKER", "CT_CHP"):
            for side, df, val in (("model", mm, "mw"), ("cems", cc, "grossLoad")):
                dk = df[(df.klass == k) & (df.hod.isin(DAY))]
                if dk.empty:
                    continue
                cap = dk.plant_code.map(caps).to_numpy()
                lv = dk[val].to_numpy() / np.where(cap > 0, cap, np.nan)
                on = lv > ONLINE_FRAC
                w = cap[on]
                lvon = lv[on]
                if w.sum() <= 0:
                    continue
                bins = [
                    ("<40%", (lvon < 0.40)),
                    ("40-70%", (lvon >= 0.40) & (lvon < 0.70)),
                    (">=70%", (lvon >= 0.70)),
                ]
                shares = {lbl: float((w * m).sum() / w.sum()) for lbl, m in bins}
                print(
                    f"  {k:<12}{side:<6}", {a: round(b, 2) for a, b in shares.items()}
                )

        # month x window CC_REGULAR + CT_PEAKER energy gap
        print("\n-- month dE (model-cems TWh), day window --")
        for k in ("CC_REGULAR", "CT_PEAKER", "CT_CHP"):
            mk = mm[mm.klass == k]
            ck = cc[cc.klass == k]
            row = []
            for mo in range(1, 13):
                ms = window_stats(mk, "mw", caps, DAY, [mo])
                cs = window_stats(ck, "grossLoad", caps, DAY, [mo])
                row.append(ms[0] - cs[0])
            print(f"  {k:<12}", " ".join(f"{v:+5.2f}" for v in row))

        # CO2 bridge: CEMS intensity x energy gap vs bench eGRID
        print("\n-- C5a CO2 bridge (Mt): energy-gap x CEMS intensity --")
        try:
            bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["co2"]
        except Exception:
            bench = None
        tot_expl = 0.0
        for k in GAS_KLASSES:
            mk = mm[mm.klass == k]
            ck = cc[cc.klass == k]
            e_c = ck.grossLoad.sum() / 1e6
            co2_c = ck.co2Mass.sum() / 1e6
            rate = co2_c / e_c if e_c > 0 else 0.0
            e_m = mk.mw.sum() / 1e6
            expl = (e_m - e_c) * rate
            tot_expl += expl
            print(
                f"  {k:<12} E_mod {e_m:6.2f}  E_cems {e_c:6.2f} TWh  "
                f"rate {rate:5.3f} t/MWh  dCO2 {expl:+6.2f} Mt"
            )
        print(f"  TOTAL energy-explained dCO2 = {tot_expl:+.2f} Mt")
        if bench:
            print(
                f"  bench eGRID = {bench.get('egrid')} Mt "
                f"(intensities {bench.get('intensity')})"
            )
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""R-ERCOT-11 probe: why the ERCOT EIA-923 ``classFull`` benchmark exceeds EIA-930 (zero LP).

Owner ruling (2026-09-28): "Diagnose only". Report-only; nothing here changes the scorer,
the benchmark builder or any committed artifact.

What it reads (never solves, never writes into the repo):

* the keeper bundle's benchmark recipe, rebuilt in memory through
  ``run_calibration_full.build_benchmark_frames`` (the single builder the solve path and
  ``--rebuild-benchmark`` share; ~50 s) -> the per-(plant, class) EIA-923 frame with the
  CAMPD backfill / missing-month fill / dual-fuel re-attribution applied, plus the CAMPD
  net frame;
* the committed bench parts ``frontend/data/backcast/bench/ERCOT/<year>.json.gz``
  (``classFull``, ``e930``, ``co2.btmClass``) — the probe first re-derives ``classFull``
  from the rebuilt frame minus ``co2.btmClass`` and asserts it reproduces the committed
  value, so every number below is on the scorer's own basis;
* raw EIA-923 Page 1 (``market_sim.data.eia923.load_monthly_generation``: per-row
  ``ba_code`` and ``chp``) and EIA-860 plant (sector, BA, county);
* raw EIA-930 ``data/raw/eia-930-hourly/ERCO hourly.parquet`` summed over the LOCAL
  calendar year (all hours, leap day included);
* ERCOT 60-Day DAM Gen Resource Data (``data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_*`` and
  ``data/raw/ercot/DAM/``, two columns only) as the per-month membership record;
* the keeper run payload (``calibration_verdict.load_artifacts``) for the model's
  per-plant ``m_ann`` and class ``gmModel``, and ``calibration_verdict.score_fuelmix``
  (C1) for the shadow re-scores.

Decomposition, per year, in TWh. The ``B_*`` bridge terms sum EXACTLY to the quoted gap
``g_dict`` = Σ classFull − Σ bench ``e930`` fuels (asserted):

* ``B_hydro_not_in_e930_dict`` — classFull carries hydro, the bench's 930 dict does not;
* ``B_foot`` — out-of-footprint MWh: for each fossil plant whose EIA-923 row carries
  ``ba_code`` != ERCO, or whose frame carries months raw EIA-923 does not (whole-plant CAMPD
  add / missing-month fill), the frame's monthly MWh in months ERCOT's own 60-Day DAM
  Gen Resource files cover but do NOT list the plant's resource (crosswalk
  ``data/raw/reference/ercot-dam-plant-crosswalk.csv``, accepted rows or name-match score
  >= 0.9). A BA-label mismatch whose resource IS listed every covered month (Jack Fusco /
  BVE_CC1) is recorded as ``ba_label_only`` and is NOT booked as an excess;
* ``B_dc_multiclass`` — double counts: frame plant total − max(raw EIA-923 total, CAMPD net)
  at a plant with raw EIA-923 generation, where the CAMPD backfill raised a class row the
  plant's other-class EIA-923 rows already carry (Decker Creek's CT-only CEMS flag);
* ``B_month_fill_above_cems`` — the same excess where every raised row is one EIA-923
  reported with a withheld (NaN) month, i.e. the missing-month fill (not a double count);
* ``B_gross_net`` — CAMPD-net-estimated MWh at plants with no EIA-923 row (non-footprint)
  times (1 − median EIA-923 / CAMPD-net ratio of co-reporting plants);
* ``B_resid_gas_other`` / ``B_resid_coal`` / ``B_nuclear`` / ``B_wind_solar`` — the family
  remainders vs the bench dict (gas and OTHER/biomass/oil are pooled because ERCOT's 930
  books OTHER-class generation inside NG); ``B_resid_gas_other`` is the combined CHP/BTM
  share error (a) plus anything unexplained (f).

Diagnostics (not bridge terms): ``hour_conv_dict_minus_raw`` (the bench 930 is 8760 hours
with gaps interpolated vs raw local-year sums), ``other_host_diag`` (OTHER-class slices of
chp=Y plants, which the BTM subtraction never reaches, at the plant's own ``chp_btm_pct``),
``btm_subtracted`` (the subtrahend already in classFull), and the C1 shadow re-scores
X
``m_ann`` from ``gmModel`` because the ERCOT fleet dispatches them too).

Run: ``uv run python scripts/probes/_r_ercot11_bench_vs_930.py [--frames-dir DIR]
[--out FILE.json]``. ``--frames-dir`` caches/reuses the rebuilt frames
(``ercot_eia923.parquet`` / ``ercot_campd.parquet``); ``--out`` writes the JSON (default:
stdout only). Finding: ``docs/handoffs/FINDING-r-ercot-11-benchmark-vs-930-2026-09-28.md``.
"""

from __future__ import annotations

import argparse
import copy
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import calibration_verdict as cv  # noqa: E402

RUN_ID = "2026-09-27-r-10-parish-fuelscope"
BUNDLE = REPO / "results/calibration/r_ercot10_parish_span"
BENCH = REPO / "frontend/data/backcast/bench/ERCOT"
E930_HOURLY = REPO / "data/raw/eia-930-hourly/ERCO hourly.parquet"
EIA860_PLANT = REPO / "data/raw/eia-860/eia860_plant.parquet"
DAM_CROSSWALK = REPO / "data/raw/reference/ercot-dam-plant-crosswalk.csv"
DAM_GLOBS = (
    "data/raw/ercot-AS/60d_DAM_Gen_Resource_Data_20*.parquet",
    "data/raw/ercot/DAM/60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_20*.parquet",
)
# A crosswalk row is used as membership evidence when it is accepted, or a strong name
# match (FRONT_EC_CC1 -> Frontera scores 0.919 but is unaccepted only because the
# low-score PSA_CC1 row also names 55098).
DAM_MATCH_MIN_SCORE = 0.9
YEARS = tuple(range(2019, 2026))
# EIA-923 2025 is the preliminary monthly-survey vintage (the builder's own logs:
# 27 plants CAMPD-added); whole-plant CAMPD adds are a footprint signal only in
# complete vintages.
COMPLETE_VINTAGES = tuple(range(2019, 2025))
GAS = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS", "ST_CHP", "OTHER_FOSSIL")
COAL = ("COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC")
OTHERFAM = ("OTHER", "biomass", "oil")
CHP_GROUPS = ("CC_CHP", "CT_CHP", "ST_CHP")
C1_SHOW = ("CC_REGULAR", "CC_CHP", "CT_PEAKER", "ST_GAS", "ST_CHP", "COAL_PRB", "COAL_LIGNITE")
E930_COLS = {
    "gas": "NG: NG",
    "coal": "NG: COL",
    "nuclear": "NG: NUC",
    "hydro": "NG: WAT",
    "solar": "NG: SUN",
    "wind": "NG: WND",
    "other": "NG: OTH",
    "battery": "NG: BAT",
    "ues": "NG: UES",
}


def rebuild_frames(frames_dir: Path | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rebuilt EIA-923 benchmark frame and CAMPD net frame for the keeper bundle."""
    if frames_dir is not None:
        e, c = frames_dir / "ercot_eia923.parquet", frames_dir / "ercot_campd.parquet"
        if e.exists() and c.exists():
            return pd.read_parquet(e), pd.read_parquet(c)
    import run_calibration_full as rcf

    _iso, fr = rcf.build_benchmark_frames(BUNDLE)
    if frames_dir is not None:
        frames_dir.mkdir(parents=True, exist_ok=True)
        fr["eia923"].to_parquet(frames_dir / "ercot_eia923.parquet")
        fr["campd"].to_parquet(frames_dir / "ercot_campd.parquet")
    return fr["eia923"], fr["campd"]


def raw_923() -> pd.DataFrame:
    """Raw EIA-923 Page-1 rows 2019-2025, classified with the builder's own classifier."""
    import run_calibration_full as rcf
    from market_sim.data.eia923 import load_monthly_generation

    g = load_monthly_generation()
    g = g[g["year"].between(min(YEARS), max(YEARS))].copy()
    g["klass"] = [
        rcf._classify_f923(f, pm, str(c).upper().startswith("Y"), pid)
        for f, pm, c, pid in zip(g["fuel_type"], g["prime_mover"], g["chp"], g["plant_id"])
    ]
    g["is_chp"] = g["chp"].astype(str).str.upper().str.startswith("Y")
    return g


def raw_930() -> pd.DataFrame:
    """Raw EIA-930 ERCO annual TWh by fuel, local calendar year (all hours)."""
    d = pd.read_parquet(E930_HOURLY)
    d["y"] = pd.to_datetime(d["Local date"]).dt.year
    d = d[d["y"].isin(YEARS)]
    cols = list(E930_COLS.values()) + ["Net generation", "Total interchange", "CEN", "CFE", "SWPP"]
    t = d.groupby("y")[cols].sum() / 1e6
    return t.rename(columns={v: k for k, v in E930_COLS.items()})


def dam_presence(sites: set[str]) -> tuple[set[tuple[int, int]], dict[str, set[tuple[int, int]]]]:
    """ERCOT 60-Day DAM coverage: ({(year, month) any file covers}, {site: {(year, month) listed}}).

    A site is listed in a month when any resource ``<site>_*`` appears on any delivery
    date of that month — ERCOT's own settlement record of which plants are ERCOT
    Generation Resources (the membership evidence R-ERCOT-8 used for Fusco).
    """
    cover: set[tuple[int, int]] = set()
    seen: dict[str, set[tuple[int, int]]] = {s: set() for s in sites}
    for pat in DAM_GLOBS:
        for f in sorted(REPO.glob(pat)):
            d = pd.read_parquet(f, columns=["Delivery Date", "Resource Name"])
            dt = pd.to_datetime(d["Delivery Date"], errors="coerce")
            ym = list(zip(dt.dt.year, dt.dt.month))
            cover.update((int(a), int(b)) for a, b in set(ym) if a == a)
            rn = d["Resource Name"].astype(str)
            for site in sites:
                hit = rn.str.startswith(site + "_") | (rn == site)
                if hit.any():
                    seen[site].update((int(a), int(b)) for a, b in set(zip(dt[hit].dt.year, dt[hit].dt.month)))
    return cover, seen


def chp_share(code: int, grp: str) -> float:
    """The plant's own BTM host share (fraction), exactly as the bench subtrahend sizes it."""
    from market_sim.data.chp import chp_btm_pct

    g = grp if grp in CHP_GROUPS else "CC_CHP"
    return chp_btm_pct(int(code), g, iso="ERCOT") / 100.0


def main() -> None:
    """Run the decomposition and C1 shadow re-scores; print (and optionally write) JSON."""
    from render_calibration_html import apply_other_fossil_scoring

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--frames-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    frame, campd = rebuild_frames(args.frames_dir)
    g923 = raw_923()
    e930 = raw_930()
    p860 = pd.read_parquet(EIA860_PLANT).set_index("Plant Code")
    names = p860["Plant Name"].to_dict()
    sector = p860["Sector Name"].to_dict()
    ba860 = p860["Balancing Authority Code"].to_dict()
    art = cv.load_artifacts(RUN_ID)
    pay = art["payload"]["years"]
    xw = pd.read_csv(DAM_CROSSWALK)
    xw = xw[(xw["accepted"] == 1) | (xw["match_score"].fillna(0) >= DAM_MATCH_MIN_SCORE)]
    sites_by_plant: dict[int, list[str]] = {}
    for pc, site in zip(xw["plant_code"], xw["site"]):
        if pc == pc:
            sites_by_plant.setdefault(int(pc), []).append(str(site))
    dam_cover, dam_seen = dam_presence({s for v in sites_by_plant.values() for s in v})

    from market_sim.data.fleet import load_campd_bins
    from market_sim.config.scenarios import ScenarioConfig

    out: dict = {"run_id": RUN_ID, "years": {}, "c1": {}}
    plant_rows: list[dict] = []
    for y in YEARS:
        part = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]
        cf = part["classFull"]
        btm_cls = part.get("co2", {}).get("btmClass", {}) or {}
        fy = apply_other_fossil_scoring(frame[frame["year"] == y], y, plant_col="plant_id")
        ccls = fy.groupby("klass")["annual_mwh"].sum() / 1e6
        # --- reproduce classFull (fossil/other classes; wind/solar are the 930 total) ---
        for k, v in cf.items():
            if k in ("wind", "solar"):
                continue
            rec = float(ccls.get(k, 0.0)) - float(btm_cls.get(k, 0.0))
            assert abs(rec - float(v)) < 2e-4, (y, k, rec, v)
        # --- raw rows for the year, restricted to the plants the frame carries ---
        gy = g923[g923["year"] == y]
        in_frame = set(fy["plant_id"].astype(int))
        gyi = gy[gy["plant_id"].isin(in_frame)]
        raw_plant = gyi.groupby("plant_id")["netgen_annual_mwh"].sum() / 1e6
        raw_pc = gyi.groupby(["plant_id", "klass"])["netgen_annual_mwh"].sum() / 1e6
        fr_plant = fy.groupby("plant_id")["annual_mwh"].sum() / 1e6
        fr_pc = fy.groupby(["plant_id", "klass"])["annual_mwh"].sum() / 1e6
        cy = campd[campd["year"] == y]
        campd_net = cy.groupby("plant_id")["net_mw"].sum() / 1e6
        ba_rows = gyi.groupby("plant_id")["ba_code"].agg(lambda s: ",".join(sorted(set(map(str, s)))))
        bins = load_campd_bins(ScenarioConfig().campd_bins_path, year=y)
        bin_grp = dict(zip(bins["Plant_Code"].astype(int), bins["Plant_Group"]))

        comp_cls: dict[str, dict[str, float]] = {}

        def book(kind: str, klass: str, twh: float) -> None:
            comp_cls.setdefault(kind, {})
            comp_cls[kind][klass] = comp_cls[kind].get(klass, 0.0) + twh

        # (c-footprint) candidates: EIA-923 BA != ERCO, or months the frame carries that raw
        # EIA-923 does not (whole-plant CAMPD add / missing-month fill). Membership is
        # then tested per month against ERCOT's own DAM registration: a covered month in
        # which the plant's DAM resource is absent is out of the ERCOT footprint.
        # Wind/solar classFull is the EIA-930 series itself and plant 0 carries the
        # builder's 930 repair rows, so neither can hold a footprint excess.
        from market_sim.data.eia923 import monthly_netgen_columns

        _mc = monthly_netgen_columns()
        mcols = [f"m{i:02d}" for i in range(1, 13)]
        scored = fy[(fy["plant_id"] > 0) & fy["klass"].isin(GAS + COAL + OTHERFAM + ("hydro",))]
        fr_mon = scored.groupby("plant_id")[mcols].sum() / 1e6
        raw_mon = gyi.groupby("plant_id")[_mc].sum(min_count=1) / 1e6
        for pid, row in fr_mon.iterrows():
            pid = int(pid)
            bas = ba_rows.get(pid)
            rm = raw_mon.loc[pid].to_numpy() if pid in raw_mon.index else [float("nan")] * 12
            gap_months = [i for i in range(12) if row.iloc[i] > 0.0005 and not (rm[i] == rm[i])]
            ba_flag = bas is not None and "ERCO" not in bas.split(",")
            if not ba_flag and not gap_months:
                continue
            sites = sites_by_plant.get(pid, [])
            listed = set().union(*(dam_seen.get(si, set()) for si in sites)) if sites else set()
            out_m = [i for i in range(12) if (y, i + 1) in dam_cover and sites and (y, i + 1) not in listed]
            out_twh = float(sum(row.iloc[i] for i in out_m))
            model = (round(float(pay[str(y)]["plants"].get(str(pid), {}).get("m_ann", 0.0)), 4)
                     if str(y) in pay else None)
            if sites and out_twh > 0.005:
                share = out_twh / float(row.sum())
                _mm = (pay[str(y)]["plants"].get(str(pid), {}).get("m_mon") or [0.0] * 12) if str(y) in pay else [0.0] * 12
                model = round(sum(float(_mm[i]) for i in out_m) / 1e3, 4)  # m_mon is GWh
                for (p2, k), v in fr_pc.items():
                    if int(p2) == pid and k not in ("wind", "solar"):
                        book("foot", k, float(v) * share)
                plant_rows.append(dict(
                    year=y, plant=pid, name=names.get(pid, ""), kind="foot", klass="/".join(
                        k for (p2, k) in fr_pc.index if int(p2) == pid and k not in ("wind", "solar")),
                    twh=round(out_twh, 4), model_twh=model,
                    why=(f"ERCOT DAM resource {'/'.join(sites)} absent in months "
                         f"{[i + 1 for i in out_m]}; EIA-923 {'ba ' + bas if bas else 'no row'}"
                         f" (EIA-860 BA {ba860.get(pid)}); frame carries CAMPD net there")))
            elif ba_flag and sites and not out_m:
                plant_rows.append(dict(
                    year=y, plant=pid, name=names.get(pid, ""), kind="ba_label_only",
                    klass="/".join(k for (p2, k) in fr_pc.index if int(p2) == pid),
                    twh=round(float(row.sum()), 4), model_twh=model,
                    why=(f"EIA-923/860 BA {bas} but ERCOT DAM resource {'/'.join(sites)} listed in "
                         f"every covered month: an ERCOT resource, NOT an excess")))
            elif not sites and (ba_flag or (not gap_months == [] and bas is None and y in COMPLETE_VINTAGES)):
                plant_rows.append(dict(
                    year=y, plant=pid, name=names.get(pid, ""), kind="foot_untested",
                    klass="/".join(k for (p2, k) in fr_pc.index if int(p2) == pid),
                    twh=round(float(row.sum()), 4), model_twh=model,
                    why=f"no DAM crosswalk site; EIA-923 ba {bas}"))
        foot_ids = {r["plant"] for r in plant_rows if r["year"] == y and r["kind"] == "foot"}
        # (plant, class) rows EIA-923 reports with a withheld month (NaN) and positive
        # annual: the builder's missing-month fill tops these up from CAMPD.
        _nm = gyi[gyi[_mc].isna().any(axis=1) & (gyi["netgen_annual_mwh"] > 0)]
        nan_month = set(zip(_nm["plant_id"].astype(int), _nm["klass"]))
        # (c-double count) frame total above max(raw 923, CAMPD net) at a 923-reporting plant
        for pid, tot in fr_plant.items():
            pid = int(pid)
            if pid in foot_ids or pid == 0:
                continue
            r = float(raw_plant.get(pid, 0.0))
            if r <= 0.0:
                continue
            ceiling = max(r, float(campd_net.get(pid, 0.0)))
            excess = float(tot) - ceiling
            if excess <= 0.005:
                continue
            # attribute to the class rows the backfill raised above raw 923
            raised = {
                k: float(fr_pc.get((pid, k), 0.0)) - float(raw_pc.get((pid, k), 0.0))
                for (p2, k) in fr_pc.index if int(p2) == pid
            }
            raised = {k: v for k, v in raised.items() if v > 0}
            rs = sum(raised.values()) or 1.0
            kind = "month_fill" if all((pid, k) in nan_month for k in raised) else "dc"
            for k, v in raised.items():
                book(kind, k, excess * v / rs)
            plant_rows.append(
                dict(year=y, plant=pid, name=names.get(pid, ""), kind=kind,
                     klass="/".join(sorted(raised)), twh=round(excess, 4),
                     why=f"frame {tot:.3f} vs raw EIA-923 {r:.3f} / CAMPD net {float(campd_net.get(pid, 0.0)):.3f}",
                     model_twh=None)
            )
        # (d) CAMPD-net-estimated MWh where 923 reported none for that class (non-foot)
        both = pd.concat([raw_plant.rename("r"), campd_net.rename("c")], axis=1).dropna()
        both = both[(both["r"] > 0.05) & (both["c"] > 0.05)]
        ratio = float((both["r"] / both["c"]).median()) if len(both) else 1.0
        est = 0.0
        for (pid, k), v in fr_pc.items():
            pid = int(pid)
            if pid in foot_ids or pid == 0 or k not in GAS + COAL:
                continue
            add = float(v) - float(raw_pc.get((pid, k), 0.0))
            if add > 0 and float(raw_plant.get(pid, 0.0)) <= 0.0:
                est += add
                book("gross_net", k, add * (1.0 - ratio))
        # (a/b) OTHER-class slices of chp=Y plants: never reached by the BTM subtraction
        oth = gyi[(gyi["klass"] == "OTHER") & gyi["is_chp"]]
        oth_pl = oth.groupby("plant_id")["netgen_annual_mwh"].sum() / 1e6
        other_host = 0.0
        for pid, v in oth_pl.items():
            sh = chp_share(int(pid), str(bin_grp.get(int(pid), "CC_CHP")))
            other_host += float(v) * sh
            if float(v) * sh > 0.005:
                plant_rows.append(
                    dict(year=y, plant=int(pid), name=names.get(int(pid), ""), kind="other_host",
                         klass="OTHER", twh=round(float(v) * sh, 4),
                         why=f"OTHER (OG/PUR/WH) {float(v):.3f} TWh at chp=Y plant, counted gross; "
                             f"plant's own BTM share {sh:.0%} ({sector.get(int(pid), '?')})",
                         model_twh=None)
                )
        book("other_host", "OTHER", other_host)
        # --- family comparison. Against the bench's OWN e930 dict (the quoted gap's
        # basis) and, as a diagnostic, against raw local-year EIA-930. ---
        def fam(keys):
            return sum(float(cf.get(k, 0.0)) for k in keys)

        r930 = e930.loc[y]
        e930d = part["e930"]
        dict_keys = [k for k in ("gas", "coal", "nuclear", "wind", "solar", "other", "oil") if k in e930d]
        g_dict = sum(float(v) for v in cf.values()) - sum(float(e930d[k]) for k in dict_keys)
        fam_keys = {"gas_other": GAS + OTHERFAM, "coal": COAL, "nuclear": ("nuclear",),
                    "wind": ("wind",), "solar": ("solar",)}
        dict_of = {"gas_other": ("gas", "other", "oil"), "coal": ("coal",), "nuclear": ("nuclear",),
                   "wind": ("wind",), "solar": ("solar",)}
        raw_of = {"gas_other": ("gas", "other"), "coal": ("coal",), "nuclear": ("nuclear",),
                  "wind": ("wind",), "solar": ("solar",)}
        fam_dict = {f: fam(ks) - sum(float(e930d.get(k, 0.0)) for k in dict_of[f]) for f, ks in fam_keys.items()}
        hour_conv = {f: sum(float(e930d.get(k, 0.0)) for k in dict_of[f]) - sum(float(r930[k]) for k in raw_of[f])
                     for f in fam_keys}
        hydro_cf = fam(("hydro",))
        c = {kind: sum(d.values()) for kind, d in comp_cls.items()}
        c_in = lambda kind, keys: sum(v for k, v in comp_cls.get(kind, {}).items() if k in keys)  # noqa: E731
        known_go = sum(c_in(kd, GAS + OTHERFAM) for kd in ("foot", "dc", "month_fill", "gross_net"))
        known_coal = sum(c_in(kd, COAL) for kd in ("foot", "dc", "month_fill", "gross_net"))
        foot_hydro = c_in("foot", ("hydro",))
        out["years"][y] = {
            "classFull_sum": round(sum(float(v) for v in cf.values()), 3),
            "e930_dict_sum": round(sum(float(e930d[k]) for k in dict_keys), 3),
            "g_dict": round(g_dict, 3),
            # bridge terms: sum exactly to g_dict
            "B_hydro_not_in_e930_dict": round(hydro_cf - foot_hydro, 3),
            "B_foot": round(c.get("foot", 0.0), 3),
            "B_dc_multiclass": round(c.get("dc", 0.0), 3),
            "B_month_fill_above_cems": round(c.get("month_fill", 0.0), 3),
            "B_gross_net": round(c.get("gross_net", 0.0), 3),
            "B_resid_gas_other": round(fam_dict["gas_other"] - known_go, 3),
            "B_resid_coal": round(fam_dict["coal"] - known_coal, 3),
            "B_nuclear": round(fam_dict["nuclear"], 3),
            "B_wind_solar": round(fam_dict["wind"] + fam_dict["solar"], 3),
            # diagnostics
            "fam_vs_dict": {k: round(v, 3) for k, v in fam_dict.items()},
            "fam_split_gas_vs_dict": round(fam(GAS) - float(e930d["gas"]), 3),
            "fam_split_other_vs_dict": round(fam(OTHERFAM) - float(e930d.get("other", 0.0)), 3),
            "hour_conv_dict_minus_raw": {k: round(v, 3) for k, v in hour_conv.items()},
            "hydro_cf": round(hydro_cf, 3),
            "raw930_wat": round(float(r930["hydro"]), 3),
            "raw930_net_generation": round(float(r930["Net generation"]), 3),
            "raw930_battery_net": round(float(r930["battery"]) + float(r930["ues"]), 3),
            "gross_net_campd_only_twh": round(est, 3),
            "ratio_923_over_campdnet": round(ratio, 4),
            "other_host_diag": round(other_host, 3),
            "chp_923_full": round(float(sum(ccls.get(k, 0.0) for k in CHP_GROUPS)), 3),
            "chp_btm_subtracted": round(float(sum(float(btm_cls.get(k, 0.0)) for k in CHP_GROUPS)), 3),
            "resid_gas_other_after_other_host": round(fam_dict["gas_other"] - known_go - other_host, 3),
            "implied_extra_chp_host_share_pp": round(
                100.0 * (fam_dict["gas_other"] - known_go - other_host)
                / max(float(sum(ccls.get(k, 0.0) for k in CHP_GROUPS)), 1e-9), 2),
            "by_class": {kind: {k: round(v, 3) for k, v in d.items() if abs(v) >= 0.0005}
                         for kind, d in comp_cls.items() if kind != "other_host"},
            "btm_subtracted": {k: round(float(v), 3) for k, v in btm_cls.items()},
            "interchange": {k: round(float(r930[k]), 3) for k in ("Total interchange", "CEN", "CFE", "SWPP")},
            "nonpositive_plant_rows": {str(k): round(float(v), 3) for (p, k), v in fr_pc.items() if int(p) <= 0},
        }
        _b = out["years"][y]
        _bs = sum(v for k, v in _b.items() if k.startswith("B_"))
        assert abs(_bs - g_dict) < 5e-3, (y, _bs, g_dict)
        # --- C1 shadow re-scores (report-only) ---
        ypay = pay.get(str(y))
        if ypay is None:
            continue
        foot_by_cls = comp_cls.get("foot", {})
        dc_by_cls = {k: comp_cls.get("dc", {}).get(k, 0.0) for k in comp_cls.get("dc", {})}
        foot_model = {}
        for r in plant_rows:
            if r["year"] == y and r["kind"] == "foot" and r["model_twh"]:
                k = r["klass"].split("/")[0]
                foot_model[k] = foot_model.get(k, 0.0) + r["model_twh"]

        def shadow(bench_minus: dict, model_minus: dict | None = None, gas_to_930: bool = False):
            b = copy.deepcopy(part)
            p = copy.deepcopy(ypay)
            for k, v in bench_minus.items():
                if k in b["classFull"]:
                    b["classFull"][k] = float(b["classFull"][k]) - v
            for k, v in (model_minus or {}).items():
                if k in p["gmModel"]:
                    p["gmModel"][k] = float(p["gmModel"][k]) - v
            if gas_to_930:
                gs = sum(float(b["classFull"].get(k, 0.0)) for k in GAS)
                sc = float(r930["gas"]) / gs
                for k in GAS:
                    if k in b["classFull"]:
                        b["classFull"][k] = float(b["classFull"][k]) * sc
            recs = cv.score_fuelmix(y, p, b, "ERCOT")
            return {r["key"]: {"status": r["status"], "d": round(r["model"] - r["actual"], 2),
                               "actual": r["actual"], "share_pp": r["share_pp"]}
                    for r in recs if r["key"] in C1_SHOW}

        both_minus = {k: foot_by_cls.get(k, 0.0) + dc_by_cls.get(k, 0.0)
                      for k in set(foot_by_cls) | set(dc_by_cls)}
        out["c1"][y] = {
            "O0_committed": shadow({}),
            "O1_foot_bench_only": shadow(foot_by_cls),
            "O1b_foot_bench_and_model": shadow(foot_by_cls, foot_model),
            "O2_dc_bench_only": shadow(dc_by_cls),
            "O3_foot+dc_bench_and_model": shadow(both_minus, foot_model),
            "O4_gas_family_scaled_to_930_NG": shadow({}, None, True),
        }
    # --- top plants across 2019-2025 ---
    pr = pd.DataFrame(plant_rows)
    excess_kinds = ("foot", "dc", "month_fill", "other_host")
    top = (pr[pr["kind"].isin(excess_kinds)].groupby(["plant", "name", "kind", "klass"], as_index=False)
             .agg(twh=("twh", "sum"), years=("year", lambda s: f"{min(s)}-{max(s)}" if len(s) > 1 else str(min(s))),
                  y2022=("twh", lambda s: 0.0), why=("why", "first")))
    y22 = pr[pr["year"] == 2022].groupby(["plant", "kind"])["twh"].sum()
    top["y2022"] = [float(y22.get((p, k), 0.0)) for p, k in zip(top["plant"], top["kind"])]
    top = top.sort_values("twh", ascending=False).head(20)
    out["top20"] = top.round(4).to_dict(orient="records")
    out["plant_rows"] = pr.round(4).to_dict(orient="records")
    txt = json.dumps(out, indent=1, default=str)
    if args.out:
        args.out.write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()

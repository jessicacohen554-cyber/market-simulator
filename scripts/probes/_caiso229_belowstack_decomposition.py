"""caiso-229 Phase 0 — the C3a residual DECOMPOSED across the CC price floor.

NO LP, NO SOLVE. Every input is committed: the caiso-220 keeper's ``hourly/``
sidecars, the committed actual-LMP reference, the committed measured
offer-surface artifact, the CA-composite citygate series, and the caiso-105/121/
131 ``run_year(fleet_only=True)`` offer reconstruction imported UNCHANGED from
``_caiso202_marginal_rung.py`` (only bundle + cache re-pointed, the caiso-227
reuse pattern).

The charter question (owner handoff, caiso-229): the caiso-227 §G below-stack
wedge — reality's DA clears BELOW the model's cheapest available CC offer in
42.3 % of Sep-Dec-2025 load-weighted hours, the model in 23.2 % — is it

  (A) an OFFER object: the marginal CC rung's level / fuel coupling is
      structurally wrong, so the floor itself sits too high; or
  (B) a SUPPLY-STATE object: the floor is right and the model simply cannot
      push its margin under it as often as reality does?

The identity that separates them, per hour and load-weighted:

    lambda - DA  ==  (lambda - cc_min)  +  (cc_min - DA)
                     \_ above-floor _/    \_ floor-level _/

* term 1 is what an offer lever CANNOT reach (the model already prices above
  its own cheapest CC offer there — a higher rung or a scarcity adder sets it);
* term 2 is the offer lever's ENTIRE domain, and §B measures how deep it is.

Sections
  §A  residual decomposition, per year x scope, split by below-stack status
  §B  the depth of reality's below-stack clearing (the offer lever's reach test)
  §C  the model's OWN CC-floor fuel coupling vs CAISO's measured DAM bid slope
  §D  the sub-floor supply DEFICIENCY in MW (the supply-state object's size)
  §E  the caiso-131 §3 envelope arithmetic

Usage:
    PYTHONPATH=.:src python3 scripts/probes/_caiso229_belowstack_decomposition.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = (2023, 2024, 2025)
HOURS = 8760
BUNDLE = REPO / "results/calibration/caiso220_c1_crosswalk"
ACTUAL_LMP = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
MEASURED_OFFER = REPO / "data/raw/_validation-source/caiso_offer_curve_measured.json"
CITYGATE = REPO / "data/raw/gas-prices/caiso_citygate_daily.csv"
OUT = REPO / "results/calibration/_caiso229_belowstack_decomposition.json"

_spec = importlib.util.spec_from_file_location(
    "_caiso202_marginal_rung", REPO / "scripts/probes/_caiso202_marginal_rung.py"
)
M202 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(M202)
M202.BUNDLE = BUNDLE
M202.CACHE = Path(
    "/tmp/claude-0/-home-user-market-simulator/"
    "14432cce-0a4f-5b9b-95ce-34788c28f568/scratchpad/caiso229"
)

SEPDEC = (9, 10, 11, 12)
SPRING = (3, 4, 5)
BELLY = (10, 11, 12, 13, 14, 15)
SCOPES = {
    "annual": None,
    "sepdec": SEPDEC,
    "spring": SPRING,
}

# The ARMED CAISO CC_REGULAR bands on the keeper: `committed` from the fitted
# _CAISO_OFFER_CURVE (Lever A, backcast_config.py), econ_low/econ_high/peak
# from the MEASURED artifact merged by caiso_offer_surface_measured. The
# measured `committed` band is deliberately NOT armed (backcast_config.py
# comment: "the Lever-A inversion lesson"), so it is quoted from the
# artifact's own `unarmed` block.
ARMED_BANDS = {"committed": 1.00, "econ_low": 1.066, "econ_high": 1.072}
MEASURED_COMMITTED = 1.03

RESULT: dict = {}


def month_of_hour(year: int) -> np.ndarray:
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS + 24), "h")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.month.to_numpy()


def day_of_hour(year: int) -> np.ndarray:
    stamps = pd.Timestamp(f"{year}-01-01") + pd.to_timedelta(np.arange(HOURS + 24), "h")
    stamps = stamps[~((stamps.month == 2) & (stamps.day == 29))][:HOURS]
    return stamps.normalize().to_numpy()


def actuals(year: int) -> pd.DataFrame:
    a = pd.read_parquet(ACTUAL_LMP)
    return a[a["year"] == year].set_index("hour").reindex(range(HOURS))


def frame(year: int) -> dict:
    """The per-hour common frame: model lambda, DA/RT actuals, weights, cc_min."""
    sc = M202.sidecars(year)
    lam = M202.ca_lambda(sc)
    a = actuals(year)
    w = M202.rubric_weights(year)
    rec = M202.fleet_recon(year)
    mc, cap, klass = rec["mc"], rec["cap"], rec["klass"]
    if mc.ndim == 1:
        mc = np.tile(mc[:, None], (1, HOURS))
    cc = klass == "gas_cc"
    if not cc.any():
        cc = np.char.startswith(klass.astype(str), "gas:cc")
    mcc, ccap = mc[cc], cap[cc]
    avail = ccap > 1.0
    cc_min = np.where(
        avail.any(axis=0), np.min(np.where(avail, mcc, np.inf), axis=0), np.nan
    )
    ca_zones = [z for z in sc["demand"].columns if not str(z).startswith("WECC")]
    return {
        "lam": lam,
        "da": a["da"].to_numpy(),
        "rt": a["rt"].to_numpy(),
        "w": w,
        "cc_min": cc_min,
        "mo": month_of_hour(year),
        "hod": np.arange(HOURS) % 24,
        "demand": sc["demand"][ca_zones].sum(axis=1).to_numpy(),
        "mc": mc,
        "cap": cap,
        "klass": klass,
    }


def _mask(f: dict, months, ok) -> np.ndarray:
    m = ok & ~np.isnan(f["cc_min"])
    if months is not None:
        m = m & np.isin(f["mo"], months)
    return m


def section_a() -> dict:
    """lambda - DA == (lambda - cc_min) + (cc_min - DA), load-weighted."""
    print("=" * 78)
    print("§A — the C3a residual decomposed across the model's own CC price floor")
    print("=" * 78)
    print("    lambda - DA  ==  (lambda - cc_min)  +  (cc_min - DA)")
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        ok = ~np.isnan(f["da"])
        rows = {}
        print(
            f"\n[{year}]  {'scope':<8}{'lam-DA':>9}{'lam-ccmin':>11}"
            f"{'ccmin-DA':>10}{'DA<ccmin%':>11}{'ccmin lw':>10}"
        )
        for name, months in SCOPES.items():
            m = _mask(f, months, ok)
            w = f["w"][m]
            ws = w.sum()
            gap = float(np.average(f["lam"][m] - f["da"][m], weights=w))
            above = float(np.average(f["lam"][m] - f["cc_min"][m], weights=w))
            floor = float(np.average(f["cc_min"][m] - f["da"][m], weights=w))
            below = f["da"] < f["cc_min"] - 0.01
            share = float(f["w"][m & below].sum() / ws)
            ccl = float(np.average(f["cc_min"][m], weights=w))
            print(
                f"        {name:<8}{gap:>+9.2f}{above:>+11.2f}{floor:>+10.2f}"
                f"{share * 100:>10.1f}%{ccl:>10.2f}"
            )
            rows[name] = {
                "gap_lam_minus_da": round(gap, 3),
                "above_floor_lam_minus_ccmin": round(above, 3),
                "floor_level_ccmin_minus_da": round(floor, 3),
                "da_below_ccmin_share_pct": round(share * 100, 2),
                "cc_min_lw": round(ccl, 2),
            }
        out[year] = rows
    return out


def section_b() -> dict:
    """How DEEP below the CC floor reality clears — the offer lever's reach test."""
    print("\n" + "=" * 78)
    print("§B — depth of reality's below-floor clearing (hours with DA < cc_min)")
    print("=" * 78)
    out = {}
    with open(MEASURED_OFFER) as fh:
        meas = json.load(fh)
    per_year = meas["_provenance"]["per_year_band_mults"]["CC_REGULAR"]
    # integrity: the ARMED_BANDS constants must match the artifact the keeper
    # merges, or the sign arithmetic below is measuring the wrong thing.
    for _b in ("econ_low", "econ_high"):
        assert np.isclose(meas["CC_REGULAR"]["bands"][_b], ARMED_BANDS[_b]), _b
    assert np.isclose(meas["CC_REGULAR"]["unarmed"]["committed"], MEASURED_COMMITTED)
    for year in YEARS:
        f = FRAMES[year]
        ok = ~np.isnan(f["da"])
        rows = {}
        print(
            f"\n[{year}]  {'scope':<8}{'n_h':>7}{'lw share':>10}{'mean depth':>12}"
            f"{'p50':>8}{'p90':>8}{'wtd $/MWh':>11}"
        )
        for name, months in SCOPES.items():
            m = _mask(f, months, ok) & (f["da"] < f["cc_min"] - 0.01)
            allm = _mask(f, months, ok)
            d = f["cc_min"][m] - f["da"][m]
            w = f["w"][m]
            wshare = float(w.sum() / f["w"][allm].sum())
            mean = float(np.average(d, weights=w))
            p50 = float(np.percentile(d, 50))
            p90 = float(np.percentile(d, 90))
            # contribution of these hours to the annual load-weighted floor term
            wtd = float((w * d).sum() / f["w"][allm].sum())
            print(
                f"        {name:<8}{m.sum():>7d}{wshare * 100:>9.1f}%{mean:>12.2f}"
                f"{p50:>8.2f}{p90:>8.2f}{wtd:>11.2f}"
            )
            rows[name] = {
                "n_hours": int(m.sum()),
                "lw_share_pct": round(wshare * 100, 2),
                "mean_depth": round(mean, 2),
                "p50_depth": round(p50, 2),
                "p90_depth": round(p90, 2),
                "wtd_contrib_usd_mwh": round(wtd, 3),
            }
        # THE OFFER LEVER'S ARITHMETIC CEILING, band by band. The only
        # rule-13/14-admissible level move is toward CAISO's OWN measured DAM
        # bid multiplier. `committed` is the band that SETS cc_min (the
        # cheapest CC tranche is the most efficient plant's committed block);
        # it is armed at the fitted Lever-A 1.00 and its MEASURED value sits
        # in the artifact UNARMED. econ_low/econ_high are armed measured
        # (pooled); the per-year measured values are the artifact's own.
        rows["measured_level_repair"] = {}
        for band, armed in (
            ("committed", ARMED_BANDS["committed"]),
            ("econ_low", ARMED_BANDS["econ_low"]),
            ("econ_high", ARMED_BANDS["econ_high"]),
        ):
            if band == "committed":
                my = float(MEASURED_COMMITTED)  # pooled; no per-year entry
            else:
                my = float(per_year[band][str(year)])
            rel = (my - armed) / armed
            rows["measured_level_repair"][band] = {
                "armed_mult": armed,
                "measured_mult": my,
                "rel_move_pct": round(rel * 100, 2),
            }
            print(
                f"        measured-faithful repair [{band:<9}]: armed {armed:.3f}"
                f" -> measured {my:.3f} ({rel * 100:+.1f} % on the offer)"
            )
        rows["measured_level_repair"]["note"] = (
            "SIGN of a measured-faithful level repair, per band. Positive = the "
            "measured value is ABOVE the armed one, i.e. the repair raises the "
            "floor -- the wrong direction for the C3a-2024/2025 overrun."
        )
        out[year] = rows
    return out


def section_c() -> dict:
    """The model's own CC-floor fuel coupling, in MMBtu/MWh, vs measured bids."""
    print("\n" + "=" * 78)
    print("§C — model CC-floor fuel coupling vs CAISO's measured DAM bid slope")
    print("=" * 78)
    cg = pd.read_csv(CITYGATE, parse_dates=["date"]).set_index("date")[
        "ca_composite_usd_mmbtu"
    ]
    with open(MEASURED_OFFER) as fh:
        meas = json.load(fh)
    base_hr = float(meas["CC_REGULAR"]["base_hr"])
    out = {"base_hr_cc": base_hr, "years": {}}
    print(
        f"\n  {'year':<6}{'slope MMBtu/MWh':>17}{'intercept $/MWh':>17}"
        f"{'r':>7}{'n_days':>8}"
    )
    for year in YEARS:
        f = FRAMES[year]
        day = day_of_hour(year)
        df = pd.DataFrame({"day": day, "cc_min": f["cc_min"]}).dropna()
        daily = df.groupby("day")["cc_min"].median()
        gas = cg.reindex(daily.index).ffill()
        m = gas.notna().to_numpy() & np.isfinite(daily.to_numpy())
        x, y = gas.to_numpy()[m], daily.to_numpy()[m]
        # Theil-Sen, the caiso-153 estimator (the citygate tail makes OLS
        # inadmissible; same reasoning, same estimator, applied to the MODEL).
        from scipy.stats import theilslopes

        slope, icept, _, _ = theilslopes(y, x)
        r = float(np.corrcoef(x, y)[0, 1])
        print(f"  {year:<6}{slope:>17.2f}{icept:>17.2f}{r:>7.2f}{m.sum():>8d}")
        out["years"][year] = {
            "slope_mmbtu_per_mwh": round(float(slope), 3),
            "intercept_usd_mwh": round(float(icept), 2),
            "r": round(r, 3),
            "n_days": int(m.sum()),
            "slope_over_base_hr": round(float(slope) / base_hr, 3),
        }
    return out


def section_d() -> dict:
    """The sub-floor supply DEFICIENCY: MW of extra below-cc_min supply the
    model would need before its margin can leave the CC stack."""
    print("\n" + "=" * 78)
    print("§D — sub-floor supply deficiency (MW) in the hours reality clears below")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        ok = ~np.isnan(f["da"])
        st = pd.read_parquet(BUNDLE / "hourly" / f"storage_{year}.parquet")
        st = st[st["pass"] == "P1"]
        dis = (
            st.pivot_table(index="hour", columns="tech", values="discharge_mw")
            .reindex(range(HOURS))
            .sum(axis=1)
            .to_numpy()
        )
        mc, cap = f["mc"], f["cap"]
        cheap = np.zeros(HOURS)
        ccm = f["cc_min"]
        for h in range(HOURS):
            if not np.isfinite(ccm[h]):
                continue
            sel = mc[:, h] < ccm[h] - 0.01
            cheap[h] = float(cap[sel, h].sum())
        deficiency = f["demand"] - cheap - dis
        rows = {}
        # the discordant hours: reality clears below the floor, the model does not
        disc = ok & (f["da"] < ccm - 0.01) & (f["lam"] >= ccm - 0.01)
        print(
            f"\n[{year}]  {'scope':<8}{'n_disc':>8}{'defic mean':>12}{'p50':>9}"
            f"{'p90':>9}{'model<floor%':>14}"
        )
        for name, months in SCOPES.items():
            m = _mask(f, months, ok)
            dm = m & disc
            w = f["w"][dm]
            if dm.sum() == 0:
                continue
            mean = float(np.average(deficiency[dm], weights=w))
            p50 = float(np.percentile(deficiency[dm], 50))
            p90 = float(np.percentile(deficiency[dm], 90))
            below_model = float(
                f["w"][m & (f["lam"] < ccm - 0.01)].sum() / f["w"][m].sum()
            )
            print(
                f"        {name:<8}{dm.sum():>8d}{mean:>12.0f}{p50:>9.0f}"
                f"{p90:>9.0f}{below_model * 100:>13.1f}%"
            )
            rows[name] = {
                "n_discordant_hours": int(dm.sum()),
                "deficiency_mean_mw": round(mean, 1),
                "deficiency_p50_mw": round(p50, 1),
                "deficiency_p90_mw": round(p90, 1),
                "model_below_floor_pct": round(below_model * 100, 2),
            }
        # belly cells for comparability with caiso-227 §C
        for name, months in (("sepdec_belly", SEPDEC), ("spring_belly", SPRING)):
            m = _mask(f, months, ok) & np.isin(f["hod"], BELLY) & disc
            if m.sum() == 0:
                continue
            w = f["w"][m]
            rows[name] = {
                "n_discordant_hours": int(m.sum()),
                "deficiency_mean_mw": round(
                    float(np.average(deficiency[m], weights=w)), 1
                ),
                "deficiency_p50_mw": round(float(np.percentile(deficiency[m], 50)), 1),
            }
            print(
                f"        {name:<14}{m.sum():>2d} h  mean "
                f"{rows[name]['deficiency_mean_mw']:.0f} MW  p50 "
                f"{rows[name]['deficiency_p50_mw']:.0f} MW"
            )
        out[year] = rows
    return out


def section_e() -> dict:
    """The caiso-131 §3 envelope: what each object would have to deliver."""
    print("\n" + "=" * 78)
    print("§E — required C3a move per year vs the two objects' domains")
    print("=" * 78)

    out = {}
    print(
        f"\n  {'year':<6}{'model lw':>10}{'RT lw':>9}{'C3a %':>8}{'req move':>10}"
        f"{'floor term':>12}{'above term':>12}"
    )
    for year in YEARS:
        f = FRAMES[year]
        okr = ~np.isnan(f["rt"])
        m = _mask(f, None, okr)
        w = f["w"][m]
        mod = float(np.average(f["lam"][m], weights=w))
        act = float(np.average(f["rt"][m], weights=w))
        pct = (mod - act) / act * 100.0
        # move required to reach the +10 % band edge
        req = min(0.0, act * 1.10 - mod)
        floor_term = float(np.average(f["cc_min"][m] - f["rt"][m], weights=w))
        above_term = float(np.average(f["lam"][m] - f["cc_min"][m], weights=w))
        print(
            f"  {year:<6}{mod:>10.2f}{act:>9.2f}{pct:>+7.1f}%{req:>10.2f}"
            f"{floor_term:>+12.2f}{above_term:>+12.2f}"
        )
        out[year] = {
            "model_lw": round(mod, 2),
            "rt_lw": round(act, 2),
            "c3a_pct": round(pct, 2),
            "required_move_usd_mwh": round(req, 2),
            "floor_term_ccmin_minus_rt": round(floor_term, 2),
            "above_floor_term": round(above_term, 2),
        }
    return out




# The two firm/contracted CAISO import tranches (spec.CAISO_FIRM_IMPORT_TRANCHES,
# held at their static contract-cost proxies by the armed caiso_perhub_firm_base).
# On this keeper ``caiso_firm_import_selfschedule=True`` floors BOTH at their
# full shaped capability, so their $/MWh is inframarginal bookkeeping that
# "can no longer gate the flow (never sets the margin at pmin = pmax)"
# (scenarios.py). Firm rows are identified by their static price identity —
# the price IS the spec constant under caiso_perhub_firm_base — and the match
# is asserted against the spec capacity so it cannot silently drift.
def _firm_rows(f: dict) -> np.ndarray:
    from market_sim.model.interchange.spec import IMPORT_TRANCHES

    firm_prices = {
        p for n, _c, p in IMPORT_TRANCHES["CAISO"] if n in ("PNW_hydro_base", "DSW_solar_PV")
    }
    imp = f["klass"] == "import"
    flat = np.isclose(f["mc"].max(axis=1), f["mc"].min(axis=1))
    hit = np.zeros(len(f["klass"]), dtype=bool)
    for pr in firm_prices:
        hit |= imp & flat & np.isclose(f["mc"][:, 0], pr)
    return hit


def section_f() -> dict:
    """The import-limb census in the discordant hours, plus the firm-block
    correction to §D (self-scheduled MW are must-take supply whatever their
    offer price), plus the hour-of-day profile of the discordant hours."""
    print("\n" + "=" * 78)
    print("§F — the import limb vs the CC floor, and the firm-block correction")
    print("=" * 78)
    out = {}
    for year in YEARS:
        f = FRAMES[year]
        ok = ~np.isnan(f["da"])
        imp = f["klass"] == "import"
        firm = _firm_rows(f)
        mc, cap, ccm = f["mc"], f["cap"], f["cc_min"]
        rows = {"firm_rows_matched": int(firm.sum())}
        print(
            f"\n[{year}]  {'scope':<8}{'n_disc':>8}{'imp<floor':>11}"
            f"{'imp>=floor':>12}{'firm>=floor':>13}{'defic corr':>12}"
        )
        for name, months in SCOPES.items():
            m = _mask(f, months, ok) & (f["da"] < ccm - 0.01) & (f["lam"] >= ccm - 0.01)
            hs = np.flatnonzero(m)
            if hs.size == 0:
                continue
            wt = f["w"][hs]
            below = np.zeros(hs.size)
            above = np.zeros(hs.size)
            fabove = np.zeros(hs.size)
            for i, h in enumerate(hs):
                c, pr = cap[:, h], mc[:, h]
                sel = imp & (c > 1.0)
                below[i] = c[sel & (pr < ccm[h])].sum()
                above[i] = c[sel & (pr >= ccm[h])].sum()
                fabove[i] = c[firm & (c > 1.0) & (pr >= ccm[h])].sum()
            b = float(np.average(below, weights=wt))
            a = float(np.average(above, weights=wt))
            fa = float(np.average(fabove, weights=wt))
            rows[name] = {
                "n_discordant_hours": int(hs.size),
                "import_cap_below_floor_mw": round(b, 0),
                "import_cap_above_floor_mw": round(a, 0),
                "firm_cap_above_floor_mw": round(fa, 0),
                "deficiency_correction_mw": round(fa, 0),
            }
            print(
                f"        {name:<8}{hs.size:>8d}{b:>11.0f}{a:>12.0f}"
                f"{fa:>13.0f}{-fa:>12.0f}"
            )
        # hour-of-day profile of the discordant hours (Sep-Dec)
        m = _mask(f, SEPDEC, ok) & (f["da"] < ccm - 0.01) & (f["lam"] >= ccm - 0.01)
        prof = {int(h): int(((f["hod"] == h) & m).sum()) for h in range(24)}
        rows["sepdec_hod_profile"] = prof
        belly = sum(v for h, v in prof.items() if h in BELLY)
        evening = sum(v for h, v in prof.items() if 17 <= h <= 21)
        rows["sepdec_hod_split"] = {
            "belly_10_15": belly,
            "evening_17_21": evening,
            "total": int(m.sum()),
        }
        print(
            f"        Sep-Dec discordant hours: belly(10-15) {belly}, "
            f"evening(17-21) {evening}, total {int(m.sum())}"
        )
        out[year] = rows
    return out




# caiso-131 §4's committed minimum-headroom hour per year — QUOTED, never
# re-derived (caiso-228 §6 DO-NOT-REDO item 3 forbids re-measuring the §4
# headroom surface). LOLP is monotone DECREASING in the reserve measure, so
# the year's MINIMUM headroom yields the year's MAXIMUM overlay adder: a
# rigorous upper bound on what the armed overlay can contribute to C3a.
CAISO131_MIN_HEADROOM_MW = {2023: 12173.0, 2024: 12689.0, 2025: 13137.0}


def section_g() -> dict:
    """Upper bound on the ARMED caiso_scarcity_pricing overlay's C3a
    contribution. The keeper's run_config carries caiso_scarcity_pricing=True
    (the post-solve LOLP adder, runner.py) alongside scarcity_price_overlay
    =False -- the charter-flagged discrepancy. This bounds it arithmetically."""
    from scipy.stats import norm

    from market_sim.results.scarcity import (
        CAISO_SCARCITY_MCL_MW as MCL,
        CAISO_SCARCITY_SHIFT_SIGMA as SH,
        CAISO_SCARCITY_SIGMA_MW as SG,
        CAISO_SCARCITY_VOLL as VOLL,
    )

    print("\n" + "=" * 78)
    print("§G — upper bound on the ARMED CAISO scarcity overlay's C3a contribution")
    print("=" * 78)
    out = {
        "params": {"voll": VOLL, "mcl_mw": MCL, "sigma_mw": SG, "shift_sigma": SH},
        "years": {},
    }
    print(f"\n  overlay params: VOLL {VOLL:.0f}, MCL {MCL:.0f} MW, sigma {SG:.0f} MW")
    print(f"  {'year':<6}{'min headroom MW':>17}{'max LOLP':>12}{'max adder $/MWh':>18}")
    for year in YEARS:
        f = FRAMES[year]
        ok = ~np.isnan(f["da"])
        m = _mask(f, None, ok)
        lam_min = float(f["lam"][m].min())
        r = CAISO131_MIN_HEADROOM_MW[year]
        lolp = float(norm.cdf((MCL + SH * SG - r) / SG))
        adder = lolp * max(VOLL - lam_min, 0.0)
        print(f"  {year:<6}{r:>17.0f}{lolp:>12.2e}{adder:>18.4f}")
        out["years"][year] = {
            "min_headroom_mw_caiso131_s4": r,
            "max_lolp": lolp,
            "max_adder_usd_mwh": round(adder, 4),
            "lambda_min_used": round(lam_min, 2),
        }
    print(
        "\n  The year's MINIMUM headroom gives the year's MAXIMUM adder, so the\n"
        "  overlay's contribution to the annual load-weighted mean is bounded\n"
        "  ABOVE by these numbers -- arithmetically inert on C3a and on C3c."
    )
    return out



FRAMES: dict = {}


def main() -> None:
    for year in YEARS:
        FRAMES[year] = frame(year)
    RESULT["A_decomposition"] = section_a()
    RESULT["B_depth"] = section_b()
    RESULT["C_coupling"] = section_c()
    RESULT["D_deficiency"] = section_d()
    RESULT["E_envelope"] = section_e()
    RESULT["F_import_limb"] = section_f()
    RESULT["G_overlay_bound"] = section_g()
    OUT.write_text(json.dumps(RESULT, indent=1, sort_keys=True, default=str) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()

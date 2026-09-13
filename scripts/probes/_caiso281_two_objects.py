"""caiso-281: are the 2022 price miss and the 2025 gas-burn miss ONE object or TWO?
ZERO LP. Two ``run_year(fleet_only=True)`` rebuilds, everything else committed artifacts.

WHY THIS EXISTS
---------------
caiso-280 closed and INVERTED the import-quantity route to CAISO's 2022 C3a miss
(the model imports +1,773.3 MW MORE than CAISO actually did on the hours carrying
it), leaving "internal marginal-cost formation" as the object. The caiso-281
handoff named one live direction and one trap: the only channel *measured* to move
C3a is the owner-blocked flat x0.92 fossil multiplier, and rule 1 ``[R-STRUCT]``
(c) forbids selecting a value by sweeping. The admissible alternative it named was
a COMMON ROOT between C4-2025's gas-burn error and C3a-2022's price error in "CC
dispatch-order formation" -- a structural repair where a level tune is refused.

This probe runs that phase 0, plus the two legs it forced.

THE GATES (each fixed in a pushed doc BEFORE its number existed)
----------------------------------------------------------------
* **A1/A2/B** -- ``PRECOMMIT-caiso281-is-the-marginal-hr-bias-a-measured-input-
  defect-2026-09-13.md``. Is the +1.024 MMBtu/MWh marginal-heat-rate bias
  (caiso-276 §3) a rule-14 ``[R-ACCURATE]`` input defect? Model tranche heat rates
  against the SAME plants' CAMPD-measured heat rates, restricted to high-load
  hours (``grossLoad >= 0.80 x that unit's own p95``) so part-load and start-up
  operation cannot masquerade as a rating error. Scored by SPEARMAN, which is
  invariant to the gross-vs-net basis difference a level comparison is not.
* **C** -- same charter. The handoff's own kill condition: per-plant mean dispatch
  error, 2022 against 2025, at LP-row grain.
* **D** -- ``ADDENDUM-caiso281-the-diurnal-coincidence-leg-2026-09-13.md``. Does
  the price error sit where the gas error sits, across the 288 (month x hour-of-day)
  buckets? The addendum PREDICTED ``r > 0`` before measuring; both years came back
  negative, and the prediction is recorded as failed rather than rewritten.
* **E** -- ``ADDENDUM-caiso281-gate-E-the-DA-basis-leg-2026-09-13.md``. The offer
  ladder carrying the bias is measured from ``PUB_DAM_GRP`` -- CAISO's DAY-AHEAD
  bids -- while C3a gates on ``rt_lw``. Does caiso-277's CAISO-specific bias survive
  on the ladder's own basis? Reuses ``_caiso277_crossiso_hr`` unchanged, swapping
  only ``rt_lw_mon`` -> ``da_lw_mon``.

THE LOAD-BEARING CODE FACT, established before any measurement
--------------------------------------------------------------
``calibration_verdict._cems_gas_hourly_fit`` SUMS OVER PLANTS before calling
``_pearson_nrmse``. C4's gas fit is therefore a FLEET-TOTAL series, and pure
within-fleet reallocation is invisible to it by construction -- so a "dispatch-order"
repair reaches C4 only through the component that survives aggregation. This probe
reports that component (``rho_agg``) rather than assuming it.

WHAT IT DOES NOT DO
-------------------
No LP, no shard, no arm, no ``ScenarioConfig`` field, nothing registered, no keeper
changed, no mechanism cell moved (rule 28 duty (b) is keyed to testing a mechanism,
and none is tested here). Rule 25 ``[R-ISO-SCOPE]``: CAISO only.

Result: ``docs/RESULT-caiso281-two-objects-not-one-and-the-bias-is-a-basis-artifact-2026-09-13.md``
"""

from __future__ import annotations

import base64
import gzip
import importlib.util
import inspect
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

KEEPER = "2026-09-12-caiso-275-gascoupling"
#: (year -> (bundle dir, run payload)). CAISO's folded 2022 rung lives in its own
#: bundle, so the span keeper cannot serve both years (caiso-277's _BUNDLE_2022).
CFG = {
    2022: ("results/calibration/caiso275_B_gascoupling_2022", f"{KEEPER}-2022.js"),
    2025: ("results/calibration/caiso275_B_gascoupling_span", f"{KEEPER}.js"),
}
GAS_CLASSES = {"CC_REGULAR", "CC_CHP", "CT_PEAKER", "CT_CHP", "ST_GAS"}
T = 8760


def plant_series(year: int, payload_name: str) -> dict:
    """Per-plant (model, actual) hourly MW for the CEMS-covered gas fleet.

    Both sides decode the committed uint8 CF-percent-of-nameplate base64 series --
    payload ``plants[].m`` and bench ``plants[].campd`` -- exactly as
    ``calibration_verdict._cems_gas_hourly_fit`` does, so the reconstruction is the
    same object C4 scores rather than a parallel one.
    """
    from scripts.lib.backcast_artifacts import decode_run_js

    text = (REPO / "frontend/data/backcast/runs" / payload_name).read_text()
    years = decode_run_js(text)["years"]
    pay = years[str(year)] if str(year) in years else years[year]
    bench_p = REPO / f"frontend/data/backcast/bench/CAISO/{year}.json.gz"
    bench = json.loads(gzip.decompress(bench_p.read_bytes()))["bench"]
    out = {}
    for code, b in bench["plants"].items():
        if b.get("group") not in GAS_CLASSES or b.get("nodata"):
            continue
        cap = float(b.get("npl") or 0.0)
        camp, p = b.get("campd"), pay["plants"].get(str(code))
        if cap <= 0.0 or not camp or not p or not p.get("m"):
            continue
        scale = cap / 100.0
        act = np.frombuffer(base64.b64decode(camp)[:T], dtype=np.uint8).astype(float)
        mod = np.frombuffer(base64.b64decode(p["m"])[:T], dtype=np.uint8).astype(float)
        if act.size < T or mod.size < T:
            continue
        out[str(code)] = {
            "group": b.get("group"),
            "npl": cap,
            "act": act * scale,
            "mod": mod * scale,
        }
    return out


def rebuild_fleet(year: int, bundle: Path) -> dict:
    """``run_year(fleet_only=True)`` on the bundle's own ``meta.json`` flags.

    The rule-29 ``[R-SCREEN]`` phase-0 path (``legitimacy_diagnostics`` §2484
    recipe): fleet assembly only, no P0/P1, hence no LP and no shard (rule 32
    ``[R-SHARD]`` (a) keeps it in the parent).
    """
    from scripts.legitimacy_diagnostics import REBUILD_META_RENAMES
    from scripts.run_calibration import run_year

    meta = json.loads((bundle / "meta.json").read_text())
    params = inspect.signature(run_year).parameters
    skip = {
        "year",
        "iso",
        "hours",
        "gas_price",
        "ttc_overrides",
        "fleet_only",
        "xyear_cache",
        "must_run_mw",
    }
    kwargs = {
        REBUILD_META_RENAMES.get(k, k): v
        for k, v in meta.items()
        if REBUILD_META_RENAMES.get(k, k) in params
        and REBUILD_META_RENAMES.get(k, k) not in skip
    }
    gp = meta.get("gas_prices", {})
    state = run_year(
        year,
        "CAISO",
        int(meta.get("hours", 8760)),
        float(gp.get(str(year), gp.get(year, 0.0))),
        {},
        fleet_only=True,
        **kwargs,
    )
    fa = state["fleet_arrays"]
    return {
        "heat_rate": np.asarray(fa.heat_rate, float),
        "pmax": np.asarray(fa.pmax, float),
        "plant_code": np.asarray(fa.plant_code, np.int64),
        "plant_group": np.asarray(
            fa.plant_group if fa.plant_group is not None else [""] * len(fa.unit_ids),
            dtype=str,
        ),
    }


def campd_plant_hr(year: int) -> pd.DataFrame:
    """Plant heat rate from CAMPD unit-hours, HIGH-LOAD hours only.

    ``grossLoad >= 0.80 x that unit's own p95 grossLoad`` (charter §3, fixed before
    the measurement): unrestricted measured heat rate is part-load- and
    start-dominated, a confound that biases TOWARD finding a rating defect.
    ``hr_meas_all`` is the unrestricted rate, reported for contrast.
    """
    cols = ["facilityId", "unitId", "opTime", "grossLoad", "heatInput"]
    d = pd.read_parquet(
        REPO / f"data/raw/campd-unit-level/CA_{year}.parquet", columns=cols
    )
    d = d[(d.opTime > 0) & (d.grossLoad > 0) & (d.heatInput > 0)].copy()
    d["fac"] = d.facilityId.astype(str)
    p95 = d.groupby(["fac", "unitId"]).grossLoad.transform(lambda s: s.quantile(0.95))
    hi = d[d.grossLoad >= 0.80 * p95]
    g = hi.groupby("fac").agg(
        hi_hours=("grossLoad", "size"), HI=("heatInput", "sum"), GL=("grossLoad", "sum")
    )
    g["hr_meas"] = g.HI / g.GL
    a = d.groupby("fac").agg(
        all_hours=("grossLoad", "size"),
        HI=("heatInput", "sum"),
        GL=("grossLoad", "sum"),
    )
    g["hr_meas_all"] = a.HI / a.GL
    g["all_hours"] = a.all_hours
    return g.reset_index()[["fac", "hr_meas", "hr_meas_all", "hi_hours", "all_hours"]]


def gate_a_b(year: int, bundle: Path) -> pd.DataFrame:
    """Gates A1/A2/B — model tranche heat rates against CAMPD-measured plant rates."""
    fa = rebuild_fleet(year, bundle)
    hr, pmax, code, grp = (
        fa["heat_rate"],
        fa["pmax"],
        fa["plant_code"],
        fa["plant_group"],
    )
    rows = []
    for c in np.unique(code):
        if c <= 0:
            continue
        sel = code == c
        if pmax[sel].sum() <= 0:
            continue
        groups = sorted(set(grp[sel]) - {""})
        rows.append(
            {
                "fac": str(int(c)),
                "group": groups[0] if groups else "",
                "pmax": float(pmax[sel].sum()),
                "hr_off_w": float(np.average(hr[sel], weights=pmax[sel])),
                "hr_off_min": float(hr[sel].min()),
                "n_tranche": int(sel.sum()),
            }
        )
    j = pd.DataFrame(rows).merge(campd_plant_hr(year), on="fac", how="inner")
    return j[(j.hi_hours >= 500) & (j.hr_meas > 0)].copy()


def gate_e() -> pd.DataFrame:
    """Gate E — CAISO dHR on the RT basis against the DA basis.

    Reuses ``_caiso277_crossiso_hr``'s construction verbatim (same shared
    ``iso_monthly_gas_prices`` denominator on BOTH sides, same C3a-scorer zonal
    demand weighting) and swaps ONLY the actual series.
    """
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.plant_prices import iso_monthly_gas_prices

    spec = importlib.util.spec_from_file_location(
        "_p277", REPO / "scripts/probes/_caiso277_crossiso_hr.py"
    )
    p277 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(p277)
    rows = []
    for j in p277.discover():
        if j["iso"] != "CAISO":
            continue
        year = j["year"]
        avg = json.load(gzip.open(p277.BENCH / "CAISO" / f"{year}.json.gz"))["bench"][
            "avgLMP"
        ]
        cfg = ScenarioConfig(
            iso="CAISO", weather_year=year, mode="backcast", hindcast=True
        )
        gas = iso_monthly_gas_prices(cfg, year)
        pm, wm, _, _ = p277.model_monthly(j["bundle"], year)
        for m in range(12):
            g = float(gas[m]) if gas is not None and np.isfinite(gas[m]) else None
            rt = (avg.get("rt_lw_mon") or [None] * 12)[m]
            da = (avg.get("da_lw_mon") or [None] * 12)[m]
            if not g or pm[m] != pm[m]:
                continue
            rows.append(
                {
                    "year": year,
                    "month": m + 1,
                    "gas": g,
                    "model": float(pm[m]),
                    "rt": rt,
                    "da": da,
                    "w": wm[m],
                    "dhr_rt": (float(pm[m]) - rt) / g if rt else np.nan,
                    "dhr_da": (float(pm[m]) - da) / g if da else np.nan,
                }
            )
    return pd.DataFrame(rows)


def _t(x: pd.Series) -> tuple[float, float, float, int]:
    x = x.dropna()
    r = stats.ttest_1samp(x, 0)
    return float(x.mean()), float(r.statistic), float(r.pvalue), len(x)


def main() -> None:
    """Run gates A/B/C/D/E and print each against its pre-registered threshold."""
    from scipy.stats import pearsonr, spearmanr

    series = {y: plant_series(y, pay) for y, (_, pay) in CFG.items()}

    print("=== GATE C — per-plant mean dispatch error, 2022 vs 2025 (LP-row grain) ===")
    common = sorted(set(series[2022]) & set(series[2025]))
    e = {
        y: np.array(
            [(series[y][c]["mod"] - series[y][c]["act"]).mean() for c in common]
        )
        for y in (2022, 2025)
    }
    r, pr = pearsonr(e[2022], e[2025])
    rho, ps = spearmanr(e[2022], e[2025])
    print(
        f"  n={len(common)}  Pearson r={r:+.4f} (p={pr:.3g})  Spearman={rho:+.4f} (p={ps:.3g})"
    )
    print(
        f"  KILL if |r|<0.20 AND |rho|<0.20  ->  {'KILL' if abs(r) < 0.20 and abs(rho) < 0.20 else 'PASS/INDET'}"
    )

    print("\n=== AGGREGATION SURVIVAL + level/shape split (ungated, charter §2) ===")
    agg = {}
    for y, s in series.items():
        E = sum(s[c]["mod"] - s[c]["act"] for c in s)
        A = sum(np.abs(s[c]["mod"] - s[c]["act"]) for c in s)
        act = sum(s[c]["act"] for c in s)
        mse = E.mean() ** 2 + E.var()
        agg[y] = E
        print(
            f"  {y}: rho_agg={np.abs(E).sum() / A.sum():.4f}  bias={E.mean():+8.1f} MW "
            f"({100 * E.mean() / act.mean():+.2f}% of actual {act.mean():.1f})  sd={E.std():.1f}  "
            f"bias^2 share of MSE={E.mean() ** 2 / mse:.4f}  shape share={E.var() / mse:.4f}"
        )

    print("\n=== GATES A1/A2/B — model tranche HR vs CAMPD measured HR ===")
    for year, (bundle, _) in CFG.items():
        j = gate_a_b(year, REPO / bundle)
        print(f"  -- {year}: {len(j)} plants matched (>=500 high-load h)")
        for cls in ("CC_REGULAR", "CT_PEAKER", "CC_CHP", "CT_CHP", "ST_GAS"):
            sub = j[j.group == cls]
            if len(sub) < 4:
                print(f"     {cls:11s} n={len(sub)} (too few to rank)")
                continue
            sp = spearmanr(sub.hr_off_w, sub.hr_meas).statistic
            spm = spearmanr(sub.hr_off_min, sub.hr_meas).statistic
            w = sub.pmax
            print(
                f"     {cls:11s} n={len(sub):3d} cap={w.sum():8.0f}MW  "
                f"Spearman(offer_w)={sp:+.3f} (offer_min)={spm:+.3f}  "
                f"HR offer_w={np.average(sub.hr_off_w, weights=w):6.3f} "
                f"offer_min={np.average(sub.hr_off_min, weights=w):6.3f} "
                f"meas={np.average(sub.hr_meas, weights=w):6.3f}  "
                f"D_w={np.average(sub.hr_off_w - sub.hr_meas, weights=w):+.3f} "
                f"D_min={np.average(sub.hr_off_min - sub.hr_meas, weights=w):+.3f}"
            )
        print(
            "     A1 gate (CC_REGULAR): OPEN<=0.40 / KILL>=0.70 -> see Spearman(offer_w)"
        )

    print("\n=== GATE D — diurnal coincidence, 288 (month x hod) buckets ===")
    act_lmp = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
    )
    hod = np.arange(T) % 24
    mon = pd.date_range("2022-01-01", periods=T, freq="h").month.to_numpy()
    key = (mon - 1) * 24 + hod
    for year, (bundle, _) in CFG.items():
        s = pd.read_parquet(REPO / bundle / f"hourly/system_{year}.parquet")
        s = s[s["pass"] == "P1"]
        lam = (
            s.groupby("hour")
            .apply(
                lambda x: np.average(x.price, weights=x.demand), include_groups=False
            )
            .sort_index()
            .to_numpy(float)
        )
        a = act_lmp[act_lmp.year == year].sort_values("hour")
        rt = a.rt.to_numpy(float)
        pi = np.where(np.isnan(rt), a.da.to_numpy(float), rt)
        dpi, E = lam - pi, agg[year]
        bE = np.array([E[key == k].mean() for k in range(288)])
        bD = np.array([dpi[key == k].mean() for k in range(288)])
        hE = np.array([E[hod == h].mean() for h in range(24)])
        hD = np.array([dpi[hod == h].mean() for h in range(24)])
        print(
            f"  {year}: 288-bucket r={pearsonr(bE, bD)[0]:+.4f}  "
            f"24-hod r={pearsonr(hE, hD)[0]:+.4f}  model_lw={np.average(lam, weights=s.groupby('hour').demand.sum().sort_index()):.3f}"
        )
        print("     dGas/hod " + " ".join(f"{hE[h]:+6.0f}" for h in range(0, 24, 3)))
        print("     dPrc/hod " + " ".join(f"{hD[h]:+6.1f}" for h in range(0, 24, 3)))
    print("  COINCIDENT if r>=+0.35 both years; KILL if |r|<0.20 in either")

    print("\n=== GATE E — CAISO dHR, RT basis vs DA basis ===")
    d = gate_e()
    cw = d[d.year.isin([2023, 2024, 2025])]
    for lab, col in (("RT (G-REPRO vs caiso-277 +0.534)", "dhr_rt"), ("DA", "dhr_da")):
        m, t, p, n = _t(cw[col])
        print(
            f"  2023-25 {lab:34s} n={n}  mean={m:+.4f}  t={t:+.3f}  p={p:.4g}  "
            f">0: {100 * (cw[col].dropna() > 0).mean():.1f}%"
        )
    for lab, col in (("RT", "dhr_rt"), ("DA", "dhr_da")):
        m, t, p, n = _t(d[d.year == 2022][col])
        print(
            f"  2022 (reported, NOT gated) {lab:20s} n={n}  mean={m:+.4f}  t={t:+.3f}  p={p:.4g}"
        )
    print("\n  per-year means:")
    print(d.groupby("year")[["dhr_rt", "dhr_da"]].mean().round(4).to_string())
    print(
        "\n  EXPLAINS if |mean_DA|<=0.15 AND |t|<2.0; KILL if mean_DA>=+0.35 AND |t|>=2.0"
    )


if __name__ == "__main__":
    main()

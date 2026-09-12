"""caiso-277: is the marginal-offer level bias ONE cross-ISO object or SEVEN
per-ISO ones? ZERO LP, ZERO fleet rebuilds.

WHY THIS EXISTS, AND A CORRECTION IT HAS TO CARRY
-------------------------------------------------
caiso-276 refused the C3a-2022 arm and re-identified the residual as a
marginal-offer level bias PROPORTIONAL TO THE GAS PRICE (~+1.0 MMBtu/MWh of
implied marginal heat rate). In doing so it cited caiso-270 §4 as establishing
the bias "in 40 of 48 **ISO-months**", and the caiso-277 charter repeated that
as a *program-level* fact.

**That reading is WRONG and this probe exists partly to fix it.** caiso-270 §4
measured "all 48 months of 2022-2025" for **CAISO ONLY** — 4 years x 12 months
of one ISO, not 48 months spread across ISOs. So whether the bias is cross-ISO
has **never been measured**, and the premise of the charter was unestablished.
That makes the measurement more valuable, not less: it is genuinely open.

THE INSTRUMENT, AND WHY IT COSTS SECONDS RATHER THAN HOURS
----------------------------------------------------------
caiso-270 and caiso-276 both took the delivered-gas denominator from the
keeper's re-assembled fleet (``reconstruct_bundle_fleet``), which is minutes of
compute per ISO-year and would be hours across 23 ISO-years. It is also not the
only admissible series. The bias is

    dHR(iso, month) = (price_model - price_actual) / gas

so what the denominator must be is ONE gas series per ISO-month applied to BOTH
sides (caiso-270 §4's own discipline: "both sides at the same delivered-gas
series"). This probe uses the MEASURED one —
``data.fuel.plant_prices.iso_monthly_gas_prices``, the EIA-923 Schedule-5
volume-weighted delivered gas cost across the ISO's own plants — which is
rule-14 ``[R-ACCURATE]`` preferable to a model-internal array, has 12/12 month
coverage for every ISO-year in the record, and reads in seconds. No fleet
rebuild, hence no shard, hence no LP: rule 32 ``[R-SHARD]`` (a) keeps all of it
in the parent.

WHAT IT READS — committed artifacts only
----------------------------------------
* each registered keeper's ``hourly/system_<year>.parquet`` (P1 zonal price +
  demand), located from ``frontend/data/backcast/keepers/<ISO>.json`` ->
  ``registry/<id>.json`` -> ``bundle``;
* the committed ``frontend/data/backcast/bench/<ISO>/<year>.json.gz``
  ``avgLMP.rt_lw`` / ``rt_lw_mon`` — the basis
  ``calibration_verdict.score_price_mean`` actually gates on;
* ``iso_monthly_gas_prices`` for the shared denominator.

WHAT IT DOES NOT DO
-------------------
It selects no lever and proposes no mechanism (rule 1 ``[R-STRUCT]``). It
reports a cross-ISO measurement and a decision card; any mechanism is a later
session's PRECOMMIT. Rule 25 ``[R-ISO-SCOPE]``: nothing measured in one ISO is
transferred to another.
"""

from __future__ import annotations

import gzip
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

KEEPERS = REPO / "frontend/data/backcast/keepers"
REGISTRY = REPO / "frontend/data/backcast/registry"
BENCH = REPO / "frontend/data/backcast/bench"
OUT = REPO / "results/calibration/_caiso277_crossiso_hr.json"
T = 8760
#: Non-leap month-start hour edges — the same ``_CUM`` construction
#: ``render_calibration_html`` uses for ``pMon``, so the monthly split here is
#: the scorer's own calendar.
_MD = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum((0,) + tuple(d * 24 for d in _MD))[:12]
#: CAISO's folded 2022 rung lives in its own bundle dir, so the span keeper
#: does not carry it. Added so CAISO contributes the same 2022 row the
#: caiso-276 measurement was built on (its exact reproduction is the G-REPRO
#: below). Keyed by ISO -> {year: bundle dir}.
EXTRA_RUNGS = {"CAISO": {2022: "results/calibration/caiso275_B_gascoupling_2022"}}


def lw(v, w) -> float:
    v = np.asarray(v, float)
    w = np.asarray(w, float)
    m = np.isfinite(v) & np.isfinite(w) & (w > 0)
    return float((v[m] * w[m]).sum() / w[m].sum()) if m.any() else float("nan")


def discover() -> list[dict]:
    """Every (ISO, year, bundle) whose keeper commits a ``system_<year>`` sidecar."""
    rows = []
    for f in sorted(KEEPERS.glob("*.json")):
        d = json.loads(f.read_text())
        iso, kid = d.get("iso"), d.get("keeper")
        if not (iso and kid):
            continue
        side = REGISTRY / f"{kid}.json"
        if not side.exists():
            print(f"  !! {iso}: no registry sidecar for {kid}")
            continue
        s = json.loads(side.read_text())
        bundle = REPO / str(s.get("bundle"))
        for y in s.get("years") or []:
            p = bundle / f"hourly/system_{y}.parquet"
            if p.exists():
                rows.append(
                    {
                        "iso": iso,
                        "year": int(y),
                        "bundle": bundle,
                        "keeper": kid,
                        "rung": "span",
                    }
                )
        for y, bd in (EXTRA_RUNGS.get(iso) or {}).items():
            p = REPO / bd / f"hourly/system_{y}.parquet"
            if p.exists():
                rows.append(
                    {
                        "iso": iso,
                        "year": int(y),
                        "bundle": REPO / bd,
                        "keeper": kid,
                        "rung": "folded",
                    }
                )
    return sorted(rows, key=lambda r: (r["iso"], r["year"]))


def model_monthly(
    bundle: Path, year: int
) -> tuple[np.ndarray, np.ndarray, float, float]:
    """Monthly and annual load-weighted model price, plus the monthly weights.

    Weighting is the C3a scorer's own: every zone's price weighted by that
    zone's demand, so zero-demand nodes (import buses) carry zero weight and
    drop out exactly as they do in ``score_price_mean``.
    """
    df = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    df = df[df["pass"] == "P1"]
    pr = df.pivot_table(index="hour", columns="zone", values="price", aggfunc="mean")
    dm = df.pivot_table(index="hour", columns="zone", values="demand", aggfunc="sum")
    keep = [z for z in dm.columns if float(dm[z].sum()) > 0]
    P = pr[keep].to_numpy(float).T
    D = dm[keep].to_numpy(float).T
    hours = pr.index.to_numpy()
    lam = (P * D).sum(axis=0) / np.maximum(D.sum(axis=0), 1e-9)
    w = D.sum(axis=0)
    midx = np.clip(np.searchsorted(_CUM, hours, side="right") - 1, 0, 11)
    pm = np.full(12, np.nan)
    wm = np.zeros(12)
    for m in range(12):
        sel = midx == m
        if sel.any():
            pm[m] = lw(lam[sel], w[sel])
            wm[m] = float(w[sel].sum())
    return pm, wm, lw(lam, w), float(w.sum())


def main() -> None:
    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.data.fuel.plant_prices import iso_monthly_gas_prices

    out: dict = {
        "session": "caiso-277",
        "instrument": "cross-ISO implied marginal HR",
        "gas_basis": "iso_monthly_gas_prices (EIA-923 Sch-5 volume-weighted, "
        "same series on BOTH sides)",
        "rows": [],
    }
    print("=== discovering registered keepers with committed hourlies ===")
    jobs = discover()
    print(f"  {len(jobs)} ISO-years across {len({j['iso'] for j in jobs})} ISOs\n")

    gas_cache: dict[tuple[str, int], np.ndarray | None] = {}
    for j in jobs:
        iso, year = j["iso"], j["year"]
        bench_p = BENCH / iso / f"{year}.json.gz"
        if not bench_p.exists():
            print(f"  !! {iso} {year}: no committed bench part — skipped")
            continue
        avg = json.load(gzip.open(bench_p))["bench"]["avgLMP"]
        a_ann, a_mon = avg.get("rt_lw"), avg.get("rt_lw_mon")
        if a_ann is None or not a_mon:
            print(f"  !! {iso} {year}: bench carries no rt_lw — skipped")
            continue
        key = (iso, year)
        if key not in gas_cache:
            try:
                cfg = ScenarioConfig(
                    iso=iso, weather_year=year, mode="backcast", hindcast=True
                )
                gas_cache[key] = iso_monthly_gas_prices(cfg, year)
            except Exception as exc:  # pragma: no cover - data availability
                print(f"  !! {iso} {year}: gas read failed {exc!r}")
                gas_cache[key] = None
        gas = gas_cache[key]
        pm, wm, p_ann, w_ann = model_monthly(j["bundle"], year)
        for m in range(12):
            g = float(gas[m]) if gas is not None and np.isfinite(gas[m]) else None
            a = a_mon[m] if m < len(a_mon) else None
            if pm[m] != pm[m] or a in (None, 0) or not g:
                continue
            out["rows"].append(
                {
                    "iso": iso,
                    "year": year,
                    "month": m + 1,
                    "rung": j["rung"],
                    "gas": round(g, 3),
                    "model": round(float(pm[m]), 2),
                    "actual": round(float(a), 2),
                    "gap": round(float(pm[m]) - float(a), 3),
                    "hr_model": round(float(pm[m]) / g, 3),
                    "hr_actual": round(float(a) / g, 3),
                    "dhr": round((float(pm[m]) - float(a)) / g, 3),
                    "load_share": round(float(wm[m] / w_ann), 4),
                }
            )
        out.setdefault("annual", []).append(
            {
                "iso": iso,
                "year": year,
                "rung": j["rung"],
                "model_lw": round(p_ann, 3),
                "actual_rt_lw": a_ann,
                "gap": round(p_ann - float(a_ann), 3),
                "gap_pct": round(100 * (p_ann / float(a_ann) - 1), 3),
                "c3a_pass_10pct": bool(abs(p_ann / float(a_ann) - 1) <= 0.10),
            }
        )

    # ---- G-REPRO: CAISO 2022 must return caiso-276's published numbers ----
    c22 = [r for r in out["annual"] if r["iso"] == "CAISO" and r["year"] == 2022]
    out["G_REPRO"] = {
        "caiso_2022_model_lw": c22[0]["model_lw"] if c22 else None,
        "expected_model_lw": 94.069,
        "caiso_2022_actual": c22[0]["actual_rt_lw"] if c22 else None,
        "expected_actual": 84.49,
        "verdict": (
            "PASS"
            if c22 and abs(c22[0]["model_lw"] - 94.069) < 0.01
            else "FAIL / ABSENT"
        ),
    }
    print("=== G-REPRO (the instrument must reproduce caiso-276 on CAISO 2022) ===")
    for k, v in out["G_REPRO"].items():
        print(f"  {k:>24s}  {v}")

    print("\n=== ANNUAL: C3a position of every registered keeper-year ===")
    print("  ISO     year  rung    model_lw  actual  gap$    gap%   C3a<=10%")
    for r in out["annual"]:
        print(
            f"  {r['iso']:<7} {r['year']:>4}  {r['rung']:<7}"
            f" {r['model_lw']:>8.2f} {r['actual_rt_lw']:>7.2f}"
            f" {r['gap']:>+7.2f} {r['gap_pct']:>+7.2f}"
            f"   {'PASS' if r['c3a_pass_10pct'] else 'FAIL'}"
        )

    # ---- per-ISO: sign, magnitude, and ADDITIVE vs MULTIPLICATIVE form ----
    df = pd.DataFrame(out["rows"])
    print(
        f"\n=== PER-ISO dHR (implied marginal heat-rate bias), "
        f"n={len(df)} ISO-months ==="
    )
    print(
        "  ISO      n  pos  pos%  dHR mean    sd    se      t | significance"
        "                 | more-stable form"
    )
    per = []
    for iso, g in df.groupby("iso"):
        d = g["dhr"].to_numpy(float)
        gp = g["gap"].to_numpy(float)
        cv_d = (
            float(np.std(d, ddof=1) / abs(np.mean(d))) if len(d) > 1 else float("nan")
        )
        cv_g = (
            float(np.std(gp, ddof=1) / abs(np.mean(gp)))
            if len(gp) > 1
            else float("nan")
        )
        # The CV-ratio "form" test is only INFORMATIVE where the mean is far
        # from zero: CV = sd/|mean| explodes as mean -> 0, so an ISO whose dHR
        # mean is ~0 gets a huge CV on both sides and the comparison is noise.
        # Gate it on the t-statistic below rather than reporting it blind.
        se = float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
        t = float(np.mean(d) / se) if se else float("nan")
        form = (
            "MULTIPLICATIVE-on-gas"
            if cv_d < cv_g
            else "ADDITIVE ($/MWh)"
            if cv_g < cv_d
            else "tie"
        )
        if abs(t) < 2.0:
            form = "UNDETERMINED (dHR mean indistinguishable from 0)"
        rec = {
            "iso": iso,
            "n_months": int(len(d)),
            "dhr_positive": int((d > 0).sum()),
            "dhr_positive_pct": round(100 * float((d > 0).mean()), 1),
            "dhr_mean": round(float(np.mean(d)), 3),
            "dhr_sd": round(float(np.std(d, ddof=1)), 3),
            "dhr_se": round(se, 3),
            "dhr_t_vs_zero": round(t, 2),
            "dhr_signif": (
                "POSITIVE"
                if t >= 2.0
                else "NEGATIVE"
                if t <= -2.0
                else "not distinguishable from 0"
            ),
            "dhr_cv": round(cv_d, 3),
            "gap_mean": round(float(np.mean(gp)), 3),
            "gap_sd": round(float(np.std(gp, ddof=1)), 3),
            "gap_cv": round(cv_g, 3),
            "more_stable_form": form,
            "gas_mean": round(float(g["gas"].mean()), 3),
        }
        per.append(rec)
        print(
            f"  {iso:<7}{rec['n_months']:>3}{rec['dhr_positive']:>5}"
            f"{rec['dhr_positive_pct']:>6.1f}"
            f"{rec['dhr_mean']:>+9.3f}{rec['dhr_sd']:>6.3f}"
            f"{rec['dhr_se']:>6.3f}{rec['dhr_t_vs_zero']:>+7.2f}"
            f" | {rec['dhr_signif']:<28s}| {form}"
        )
    out["per_iso"] = per

    # ---- the one-object test, stated as a measurement ----
    d_all = df["dhr"].to_numpy(float)
    means = np.array([p["dhr_mean"] for p in per])
    one = {
        "pooled_n": int(len(d_all)),
        "pooled_positive": int((d_all > 0).sum()),
        "pooled_positive_pct": round(100 * float((d_all > 0).mean()), 1),
        "pooled_mean": round(float(np.mean(d_all)), 3),
        "per_iso_mean_min": round(float(means.min()), 3),
        "per_iso_mean_max": round(float(means.max()), 3),
        "per_iso_mean_spread": round(float(means.max() - means.min()), 3),
        "per_iso_mean_sd": round(float(np.std(means, ddof=1)), 3),
        "isos_positive_mean": int((means > 0).sum()),
        "isos_total": int(len(means)),
        "n_isos_multiplicative": sum(
            1 for p in per if p["more_stable_form"].startswith("MULT")
        ),
    }
    out["one_object_test"] = one
    print("\n=== ONE-OBJECT TEST (measurement, not assertion) ===")
    for k, v in one.items():
        print(f"  {k:>26s}  {v}")

    # ---- ROBUSTNESS: the COMMON WINDOW, 2023-2025 ----
    # The spans are unequal (CAISO 48 months incl. its 2022 folded rung, ERCOT
    # 60 incl. 2021-22, the rest 36). CAISO's 2022 is the extreme year in the
    # whole record, so the pooled comparison could be an artifact of WHICH
    # years each ISO contributes. Re-run the per-ISO test on the window every
    # ISO shares. If CAISO's positivity survives here it is a property of
    # CAISO, not of 2022; if it vanishes, the finding is a CAISO-2022
    # statement and must be said that way.
    cw = df[(df["year"] >= 2023) & (df["year"] <= 2025)]
    print(
        "\n=== ROBUSTNESS — COMMON WINDOW 2023-2025 only "
        f"(n={len(cw)} ISO-months, 36 per ISO) ==="
    )
    print("  ISO      n  pos  pos%  dHR mean    sd    se      t | significance")
    cwrows = []
    for iso, g in cw.groupby("iso"):
        d = g["dhr"].to_numpy(float)
        se = float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else float("nan")
        t = float(np.mean(d) / se) if se else float("nan")
        sig = (
            "POSITIVE"
            if t >= 2.0
            else "NEGATIVE"
            if t <= -2.0
            else "not distinguishable from 0"
        )
        cwrows.append(
            {
                "iso": iso,
                "n_months": int(len(d)),
                "dhr_positive_pct": round(100 * float((d > 0).mean()), 1),
                "dhr_mean": round(float(np.mean(d)), 3),
                "dhr_sd": round(float(np.std(d, ddof=1)), 3),
                "dhr_se": round(se, 3),
                "dhr_t_vs_zero": round(t, 2),
                "dhr_signif": sig,
            }
        )
        r = cwrows[-1]
        print(
            f"  {iso:<7}{r['n_months']:>3}{int(round(r['dhr_positive_pct'] * r['n_months'] / 100)):>5}"
            f"{r['dhr_positive_pct']:>6.1f}{r['dhr_mean']:>+9.3f}{r['dhr_sd']:>6.3f}"
            f"{r['dhr_se']:>6.3f}{r['dhr_t_vs_zero']:>+7.2f} | {sig}"
        )
    out["common_window_2023_2025"] = cwrows
    cm = {r["iso"]: r for r in cwrows}
    out["caiso_survives_common_window"] = bool(
        cm.get("CAISO", {}).get("dhr_t_vs_zero", 0) >= 2.0
    )
    print(
        f"\n  CAISO positivity survives the common window: "
        f"{out['caiso_survives_common_window']}"
    )
    print(
        "  ISOs significantly POSITIVE on 2023-2025: "
        + (", ".join(r["iso"] for r in cwrows if r["dhr_t_vs_zero"] >= 2.0) or "none")
    )
    print(
        "  ISOs significantly NEGATIVE on 2023-2025: "
        + (", ".join(r["iso"] for r in cwrows if r["dhr_t_vs_zero"] <= -2.0) or "none")
    )

    # ---- gas-level bins, pooled: does dHR grow with gas? ----
    bins = [(0, 3), (3, 5), (5, 8), (8, 12), (12, 20), (20, 70)]
    print("\n=== POOLED dHR by delivered-gas level (caiso-270 §4's own bins) ===")
    print("  gas $/MMBtu      n  HR model  HR actual     dHR   gap$")
    brows = []
    for lo, hi in bins:
        s = df[(df["gas"] > lo) & (df["gas"] <= hi)]
        if s.empty:
            continue
        brows.append(
            {
                "bin": f"({lo}, {hi}]",
                "n": int(len(s)),
                "hr_model": round(float(s["hr_model"].mean()), 2),
                "hr_actual": round(float(s["hr_actual"].mean()), 2),
                "dhr": round(float(s["dhr"].mean()), 3),
                "gap": round(float(s["gap"].mean()), 2),
            }
        )
        print(
            f"  {brows[-1]['bin']:<13}{brows[-1]['n']:>5}"
            f"{brows[-1]['hr_model']:>10.2f}{brows[-1]['hr_actual']:>11.2f}"
            f"{brows[-1]['dhr']:>+8.3f}{brows[-1]['gap']:>+7.2f}"
        )
    out["gas_bins"] = brows

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

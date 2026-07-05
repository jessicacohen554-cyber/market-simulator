#!/usr/bin/env python
"""Score a capacity hindcast against actuals (W2-P5, plan §1.4).

Consumes a bundle produced by ``scripts/run_capacity_hindcast.py`` (evolution
ledgers + dispatch parquets under ``results/hindcast/<run>/<iso>/<key>/``) and
the scoring target ``data/raw/_validation-source/capacity_actuals_<iso>.csv``
(built by ``scripts/build_capacity_actuals.py``). Emits:

* ``<bundle>/score.json`` — every metric, its band, and pass/fail;
* ``docs/hindcast-reports/<iso>-<start>-<end>-<variant>-<date>.md`` — the report,
  including the CO2 decomposition table and the two skill baselines.

Metrics and bands adapt ``forecast-validation-plan.md`` Phase 2c to the 5-year
window (plan §1.4). Scored years are 2023-2025 (2021 seeds, 2022 is the bridge —
never scored, rule 22). A missed band is a **root-cause investigation** (rules
1/11/14), never a band widening, and NOTHING here tunes a parameter.

Usage::

    python scripts/score_capacity_hindcast.py --bundle results/hindcast/ercot-...-realized
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.model.dispatch import DispatchResult  # noqa: E402
from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

SCORED_YEARS = (2023, 2024, 2025)  # 2021 seeds; 2022 bridged (rule 22).
CO2_HEADLINE_YEAR = 2025
LARGE_UNIT_MW = 300.0
SHORT_TON_TO_METRIC = 0.90718474  # CAMPD co2Mass is short tons.

# ISO → CAMPD state files used to derive the actual CO2 reference. ERCOT ≈ the
# Texas grid; the CAMPD TX total slightly overcounts (El Paso / SPP-side TX
# plants are outside ERCOT) — flagged in the report, never used to tune.
ISO_CAMPD_STATES = {
    "ERCOT": ["TX"],
    "PJM": ["PA", "NJ", "MD", "OH", "VA", "WV", "DE", "KY", "IN", "IL", "NC", "DC"],
}

THERMAL_FUELS = frozenset(
    {"coal", "gas_cc", "gas_ct", "gas_st", "oil", "nuclear", "biomass"}
)
ADDITION_TECHS = ("wind", "solar", "gas_cc", "gas_ct", "storage")

# Per plan §1.4 band table.
BANDS = {
    "thermal_gw_retired_total_frac": 0.10,
    "thermal_gw_retired_perfuel_frac": 0.20,
    "retire_recall_min": 0.70,
    "false_retire_frac_max": 0.15,
    "retire_timing_years_max": 1.5,
    "add_gw_frac_default": 0.15,  # wind/solar/gas
    "add_gw_frac_storage": 0.25,
    "techmix_share_pp_max": 0.05,
    "co2_2025_frac": 0.10,
}


# --------------------------------------------------------------------------- #
# Actuals + model aggregation
# --------------------------------------------------------------------------- #
def load_actuals(iso: str) -> pd.DataFrame:
    """Load the committed capacity-actuals CSV for an ISO."""
    path = Path("data/raw/_validation-source") / f"capacity_actuals_{iso.lower()}.csv"
    if not path.exists():
        raise SystemExit(
            f"actuals not found: {path} — run scripts/build_capacity_actuals.py --iso {iso}"
        )
    return pd.read_csv(path, comment="#")


def model_retirements(ledgers: dict) -> pd.DataFrame:
    """All modelled retirements across the window (from the ledgers)."""
    rows = []
    for year, led in ledgers.items():
        for r in led.get("retirements", []):
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["mw"]),
                    "year": year,
                }
            )
    return pd.DataFrame(rows, columns=["unit_id", "fuel", "mw", "year"])


def model_additions(ledgers: dict) -> pd.DataFrame:
    """All modelled additions (thermal + renewable + storage)."""
    rows = []
    for year, led in ledgers.items():
        for a in led.get("thermal_additions", []):
            rows.append({"fuel": a["fuel"], "mw": float(a["mw"]), "year": year})
        for a in led.get("renewable_additions", []):
            rows.append({"fuel": a["tech"], "mw": float(a["mw"]), "year": year})
        for a in led.get("storage_additions", []):
            rows.append({"fuel": "storage", "mw": float(a["mw"]), "year": year})
    return pd.DataFrame(rows, columns=["fuel", "mw", "year"])


def _gw_by_fuel(df: pd.DataFrame, kind: str | None = None) -> dict[str, float]:
    if df.empty:
        return {}
    sub = df if kind is None else df[df["kind"] == kind]
    return (sub.groupby("fuel")["mw"].sum() / 1000.0).round(3).to_dict()


# --------------------------------------------------------------------------- #
# Metrics
# --------------------------------------------------------------------------- #
def _band(err_frac: float, tol: float) -> str:
    return "PASS" if abs(err_frac) <= tol else "FAIL"


def score_retirements(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """Retirement GW (total + per-fuel), unit recall, false-retire, timing."""
    act = actuals[actuals["kind"] == "retirement"]
    act_thermal = act[act["fuel"].isin(THERMAL_FUELS)]
    mod_thermal = model[model["fuel"].isin(THERMAL_FUELS)]

    act_gw = act_thermal["mw"].sum() / 1000.0
    mod_gw = mod_thermal["mw"].sum() / 1000.0
    total_err = (mod_gw - act_gw) / act_gw if act_gw else float("nan")

    # Per fuel.
    perfuel = {}
    fuels = set(act_thermal["fuel"]) | set(mod_thermal["fuel"])
    for f in sorted(fuels):
        a = act_thermal[act_thermal["fuel"] == f]["mw"].sum() / 1000.0
        m = mod_thermal[mod_thermal["fuel"] == f]["mw"].sum() / 1000.0
        e = (m - a) / a if a else float("nan")
        perfuel[f] = {
            "actual_gw": round(a, 3),
            "model_gw": round(m, 3),
            "err_frac": None if np.isnan(e) else round(e, 3),
        }

    # Unit-level recall on >300 MW actual retirements, greedy fuel+size match.
    big = act_thermal[act_thermal["mw"] >= LARGE_UNIT_MW]
    model_pool = mod_thermal.copy()
    matched = 0
    for _, a in big.iterrows():
        cand = model_pool[
            (model_pool["fuel"] == a["fuel"])
            & (model_pool["mw"] >= 0.5 * a["mw"])
            & (model_pool["mw"] <= 1.5 * a["mw"])
        ]
        if not cand.empty:
            matched += 1
            model_pool = model_pool.drop(cand.index[0])
    recall = matched / len(big) if len(big) else float("nan")

    # False-retire: model thermal GW with no actual counterpart, greedy.
    act_pool = act_thermal.copy()
    false_gw = 0.0
    for _, m in mod_thermal.iterrows():
        cand = act_pool[
            (act_pool["fuel"] == m["fuel"])
            & (act_pool["mw"] >= 0.5 * m["mw"])
            & (act_pool["mw"] <= 1.5 * m["mw"])
        ]
        if cand.empty:
            false_gw += m["mw"] / 1000.0
        else:
            act_pool = act_pool.drop(cand.index[0])
    false_frac = false_gw / mod_gw if mod_gw else 0.0

    return {
        "total_gw": {
            "actual": round(act_gw, 3),
            "model": round(mod_gw, 3),
            "err_frac": None if np.isnan(total_err) else round(total_err, 3),
            "band": _band(total_err, BANDS["thermal_gw_retired_total_frac"])
            if not np.isnan(total_err)
            else "SKIP",
        },
        "per_fuel": perfuel,
        "unit_recall_gt300": {
            "n_big_actual": int(len(big)),
            "matched": matched,
            "recall": None if np.isnan(recall) else round(recall, 3),
            "band": ("PASS" if recall >= BANDS["retire_recall_min"] else "FAIL")
            if not np.isnan(recall)
            else "SKIP",
        },
        "false_retire": {
            "false_gw": round(false_gw, 3),
            "frac_of_model": round(false_frac, 3),
            "band": "PASS" if false_frac <= BANDS["false_retire_frac_max"] else "FAIL",
        },
    }


def score_additions(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """Cumulative additions by tech + tech-mix shares."""
    act = actuals[actuals["kind"] == "addition"]
    by_tech = {}
    for tech in ADDITION_TECHS:
        a = act[act["fuel"] == tech]["mw"].sum() / 1000.0
        m = model[model["fuel"] == tech]["mw"].sum() / 1000.0
        e = (m - a) / a if a else float("nan")
        tol = (
            BANDS["add_gw_frac_storage"]
            if tech == "storage"
            else BANDS["add_gw_frac_default"]
        )
        by_tech[tech] = {
            "actual_gw": round(a, 3),
            "model_gw": round(m, 3),
            "err_frac": None if np.isnan(e) else round(e, 3),
            "band": _band(e, tol) if not np.isnan(e) else "SKIP",
        }
    # Tech-mix shares (of total additions).
    act_tot = act["mw"].sum() / 1000.0
    mod_tot = model["mw"].sum() / 1000.0
    shares = {}
    for tech in ADDITION_TECHS:
        a_share = (
            (act[act["fuel"] == tech]["mw"].sum() / 1000.0 / act_tot)
            if act_tot
            else 0.0
        )
        m_share = (
            (model[model["fuel"] == tech]["mw"].sum() / 1000.0 / mod_tot)
            if mod_tot
            else 0.0
        )
        dpp = m_share - a_share
        shares[tech] = {
            "actual_share": round(a_share, 3),
            "model_share": round(m_share, 3),
            "delta_pp": round(dpp, 3),
            "band": "PASS" if abs(dpp) <= BANDS["techmix_share_pp_max"] else "FAIL",
        }
    return {
        "by_tech": by_tech,
        "shares": shares,
        "actual_total_gw": round(act_tot, 3),
        "model_total_gw": round(mod_tot, 3),
    }


def model_co2_by_year(bundle: Path) -> dict[int, float]:
    """Total modelled CO2 (metric tonnes) per scored year, from the parquets."""
    out = {}
    for year in SCORED_YEARS:
        p = bundle / f"year_{year}.parquet"
        if not p.exists():
            continue
        res = DispatchResult.from_parquet(p)
        if res.emissions is not None:
            out[year] = float(np.asarray(res.emissions).sum())
    return out


def actual_co2_by_year(iso: str) -> dict[int, float]:
    """Derive actual CO2 (metric tonnes) from CAMPD unit-level, scored years only.

    Sums ``co2Mass`` (short tons → metric) over the ISO's CAMPD state files.
    ERCOT ≈ TX (slight overcount, flagged). NEVER reads 2022/2026 (rule 22).
    """
    states = ISO_CAMPD_STATES.get(iso, [])
    out: dict[int, float] = {}
    base = Path("data/raw/campd-unit-level")
    for year in SCORED_YEARS:
        total_short = 0.0
        found = False
        for st in states:
            p = base / f"{st}_{year}.parquet"
            if not p.exists():
                continue
            found = True
            df = pd.read_parquet(p, columns=["co2Mass"])
            total_short += float(pd.to_numeric(df["co2Mass"], errors="coerce").sum())
        if found:
            out[year] = total_short * SHORT_TON_TO_METRIC
    return out


# --------------------------------------------------------------------------- #
# Baselines
# --------------------------------------------------------------------------- #
def baseline_announced(iso: str) -> dict:
    """Announced-only baseline: the 2020-vintage planned schedule, verbatim."""
    vdir = Path("data/raw/eia-860/vintage_2020")
    out = {"retire_gw": 0.0, "add_gw": 0.0, "note": "2020-vintage planned schedule"}
    op = vdir / "eia860_generator_operable.parquet"
    if op.exists():
        df = pd.read_parquet(op)
        yr = pd.to_numeric(df.get("Planned Retirement Year"), errors="coerce")
        mw = pd.to_numeric(df.get("Nameplate Capacity (MW)"), errors="coerce")
        mask = yr.isin(list(range(2021, 2026)))
        out["retire_gw"] = round(float(mw[mask].sum()) / 1000.0, 3)
    prop = vdir / "eia860_generator_proposed.parquet"
    if prop.exists():
        df = pd.read_parquet(prop)
        mw = pd.to_numeric(df.get("Nameplate Capacity (MW)"), errors="coerce")
        out["add_gw"] = round(float(mw.sum()) / 1000.0, 3)
    return out


# --------------------------------------------------------------------------- #
# Report
# --------------------------------------------------------------------------- #
def _fmt_band(x: str) -> str:
    return {"PASS": "✅ PASS", "FAIL": "❌ FAIL", "SKIP": "—"}.get(x, x)


def write_report(
    iso, variant, meta, ret, add, co2, baselines, report_path: Path
) -> None:
    """Render the markdown hindcast report."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    L = []
    L.append(f"# Capacity hindcast — {iso} 2021→2025 ({variant} fuel)")
    L.append("")
    L.append(
        f"_Generated {stamp} · W2-P5 · plan §1.4 · bundle `{meta.get('bundle', '')}`_"
    )
    L.append("")
    L.append(
        "Forecast machinery run from the **EIA-860 2020 vintage**, evolved 2021→2025. "
        "2021 seeds the price signal (not scored); **2022 is the quarantine bridge — "
        "evolved, never solved (rule 22)**; 2023-2025 scored. A missed band is a "
        "root-cause investigation (rules 1/11/14), never widened, and nothing here is tuned."
    )
    L.append("")
    # Retirements
    L.append("## Retirements (thermal, cumulative 2021→2025)")
    tg = ret["total_gw"]
    L.append("")
    L.append("| metric | actual | model | err | band |")
    L.append("|---|--:|--:|--:|:--|")
    tg_err = "" if tg["err_frac"] is None else format(tg["err_frac"], "+.0%")
    L.append(
        f"| thermal GW retired | {tg['actual']} | {tg['model']} | "
        f"{tg_err} | {_fmt_band(tg['band'])} |"
    )
    rr = ret["unit_recall_gt300"]
    L.append(
        f"| unit recall >300MW | {rr['n_big_actual']} units | {rr['matched']} matched | "
        f"{('' if rr['recall'] is None else format(rr['recall'], '.0%'))} | {_fmt_band(rr['band'])} |"
    )
    fr = ret["false_retire"]
    L.append(
        f"| false-retire (GW) | — | {fr['false_gw']} | {format(fr['frac_of_model'], '.0%')} of model | {_fmt_band(fr['band'])} |"
    )
    L.append("")
    L.append("Per-fuel retired GW:")
    L.append("")
    L.append("| fuel | actual | model | err |")
    L.append("|---|--:|--:|--:|")
    for f, d in ret["per_fuel"].items():
        e = "" if d["err_frac"] is None else format(d["err_frac"], "+.0%")
        L.append(f"| {f} | {d['actual_gw']} | {d['model_gw']} | {e} |")
    L.append("")
    # Additions
    L.append("## Additions (cumulative 2021→2025)")
    L.append("")
    L.append("| tech | actual GW | model GW | err | band | Δ-share (pp) |")
    L.append("|---|--:|--:|--:|:--|--:|")
    for tech in ADDITION_TECHS:
        d = add["by_tech"][tech]
        s = add["shares"][tech]
        e = "" if d["err_frac"] is None else format(d["err_frac"], "+.0%")
        L.append(
            f"| {tech} | {d['actual_gw']} | {d['model_gw']} | {e} | {_fmt_band(d['band'])} "
            f"| {format(s['delta_pp'] * 100, '+.1f')} |"
        )
    L.append("")
    # CO2
    L.append("## System CO2 (headline: 2025, ±10%)")
    L.append("")
    L.append("| year | model Mt | actual Mt | err | band |")
    L.append("|---|--:|--:|--:|:--|")
    for year in SCORED_YEARS:
        m = co2["model"].get(str(year)) or co2["model"].get(year)
        a = co2["actual"].get(str(year)) or co2["actual"].get(year)
        if m is None:
            continue
        mt_m = m / 1e6
        if a:
            err = (m - a) / a
            band = "PASS" if abs(err) <= BANDS["co2_2025_frac"] else "FAIL"
            band = band if year == CO2_HEADLINE_YEAR else "report-only"
            L.append(
                f"| {year} | {mt_m:.1f} | {a / 1e6:.1f} | {err:+.0%} | "
                f"{_fmt_band(band) if year == CO2_HEADLINE_YEAR else '(report-only)'} |"
            )
        else:
            L.append(f"| {year} | {mt_m:.1f} | (n/a) | — | — |")
    L.append("")
    L.append(
        "> CO2 decomposition (plan §1.4): hindcast CO2 error ≈ **dispatch error** "
        "(the keeper/D-7 gap on the *true* fleet) + **fleet error** (the new "
        "capacity-path information). Supply the keeper CO2 gap to attribute the "
        "split; absent it, the table reports the *total* hindcast error only. "
        "Actual CO2 is CAMPD unit-level (short→metric tons); ERCOT≈TX slightly "
        "overcounts (El Paso/SPP-side TX plants)."
    )
    L.append("")
    # Baselines
    L.append("## Skill baselines (must beat on retirement recall + addition mix)")
    L.append("")
    L.append("| baseline | retire GW | add GW | note |")
    L.append("|---|--:|--:|---|")
    L.append("| (a) frozen fleet | 0.0 | 0.0 | no evolution after 2020 |")
    b = baselines["announced"]
    L.append(f"| (b) announced-only | {b['retire_gw']} | {b['add_gw']} | {b['note']} |")
    L.append(
        "| (c) AEO2021 regional | — | — | report-only context (not computed here) |"
    )
    L.append("")
    if meta.get("leakage_violations"):
        L.append("## ⚠️ Leakage-guard violations")
        for v in meta["leakage_violations"]:
            L.append(f"- {v}")
        L.append("")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(L))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path, required=True, help="run_capacity_hindcast out-dir."
    )
    parser.add_argument(
        "--report-dir", type=Path, default=Path("docs/hindcast-reports")
    )
    args = parser.parse_args(argv)

    meta = json.loads((args.bundle / "meta.json").read_text())
    iso, variant = meta["iso"], meta["variant"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():  # bundle moved: re-derive under --bundle
        cache_dir = args.bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret, madd = model_retirements(ledgers), model_additions(ledgers)

    ret = score_retirements(mret, actuals)
    add = score_additions(madd, actuals)
    co2 = {
        "model": {str(k): v for k, v in model_co2_by_year(cache_dir).items()},
        "actual": {str(k): v for k, v in actual_co2_by_year(iso).items()},
    }
    baselines = {"announced": baseline_announced(iso)}

    score = {
        "iso": iso,
        "variant": variant,
        "scored_years": list(SCORED_YEARS),
        "retirements": ret,
        "additions": add,
        "co2": co2,
        "baselines": baselines,
        "bands": BANDS,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (cache_dir / "score.json").write_text(json.dumps(score, indent=2))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report_path = args.report_dir / f"{iso.lower()}-2021-2025-{variant}-{stamp}.md"
    write_report(iso, variant, meta, ret, add, co2, baselines, report_path)

    print(
        f"[score] {iso} {variant}: thermal-retire band {ret['total_gw']['band']}, "
        f"recall band {ret['unit_recall_gt300']['band']}"
    )
    print(f"[score] score.json: {cache_dir / 'score.json'}")
    print(f"[score] report:     {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

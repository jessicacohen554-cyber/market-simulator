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
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_SRC = Path(__file__).resolve().parent.parent / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from market_sim.data.fleet import BA_CODE_TO_ISO  # noqa: E402
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

# ISOs whose footprint crosses many states and overlaps another ISO get a
# *facility-exact* CO2 reference instead of a state sum: CAMPD unit-level rows
# filtered to the ORISPL/plant codes EIA-860 maps to that ISO's balancing
# authority, summed over the states the ISO spans. A plain state sum would be
# badly boundary-misaligned here (rule 11) — MISO shares IN/IL/KY/MI with PJM,
# so a TX..WI state sum would double-count PJM and overstate MISO CO2 by a large
# margin; NYISO ≈ NY but carries a few NJ/PJM-border plants. The crosswalk keeps
# the reference on the model's own BA boundary. ERCOT/PJM stay on the state-sum
# path above (unchanged, already registered).
ISO_CAMPD_FACILITY = frozenset({"MISO", "NYISO"})

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


def model_plant_code(unit_id: str) -> str | None:
    """Best-effort EIA plant code from a *model* retirement ``unit_id``.

    The economic screen retires generators at whatever grain the fleet carries
    when the screen runs, so ``unit_id`` takes several forms:

    * CAMPD per-plant tranche — ``COAL_South_p6183_committed`` → ``"6183"`` (the
      ``p<plant>`` token the binning layer stamps on every tranche);
    * raw EIA unit — ``3490_GEN1`` → ``"3490"`` (leading plant code);
    * legacy zone aggregate — ``coal_COAL_South_Central`` → ``None`` (plant
      identity was collapsed away pre-G-28; only fuel survives).

    Returns the plant code as a string, or ``None`` when identity is lost.
    """
    s = str(unit_id)
    m = re.search(r"_p(\d+)(?:_|$)", s)  # CAMPD tranche form
    if m:
        return m.group(1)
    m = re.match(r"(\d+)(?:_|$)", s)  # raw plant_generator form
    if m:
        return m.group(1)
    return None


def score_retirements(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """Retirement GW (total + per-fuel), grain-corrected recall + false-retire.

    **Grain fix (G-31).** The economic screen retires *plant-binned tranches*
    (MW derates), never raw EIA units: one plant's coal exits as several tranche
    rows (must-run / committed / peak / econ), and pre-G-28 runs even collapse
    survivors into multi-GW zone aggregates. The old 1:1 ``fuel+size`` match
    (a model row within [0.5×, 1.5×] of one actual unit) therefore mis-scored
    every lumpy or split derate — a 4 GW zone-coal row can never sit inside
    [0.5×, 1.5×] of a 486 MW actual unit, so the whole derate scored as
    *false-retire* (the 94% artifact) while the real unit scored as *un-recalled*
    — even when the model retired exactly the right fuel in the right amount.

    The corrected grain scores capacity the way the screen can actually produce
    it — by fuel MW, plant identity not required (per the G-31 spec):

    * **recall** — a real retired unit (≥ ``LARGE_UNIT_MW``) is *recalled* when
      the model derated at least its MW of the **same fuel** (its plant-binned
      tranche is derated by its MW). Greedy, largest actual unit first, each
      claim consuming the model's per-fuel derate pool so two real units aren't
      both credited to the same MW.
    * **false-retire** — genuine over-retirement only: model-derated MW of a
      fuel in **excess** of what that fuel actually retired, summed over fuels.
      Grain-independent (a tranche split or a zone lump nets out); it flags the
      model retiring *more* coal than reality, never the model retiring the
      *right* coal in an unfamiliar shape. (When this stays high after the fix
      it is a real over-retirement — e.g. the G-30 scarcity-free screen exiting
      the whole coal fleet — a screen root-cause, not a scoring artifact.)

    ``plant_recall_frac`` is reported (not banded) as a stricter diagnostic: the
    share of large actual units whose exact plant the model also retired.
    """
    act = actuals[actuals["kind"] == "retirement"]
    act_thermal = act[act["fuel"].isin(THERMAL_FUELS)]
    mod_thermal = model[model["fuel"].isin(THERMAL_FUELS)]

    act_gw = act_thermal["mw"].sum() / 1000.0
    mod_gw = mod_thermal["mw"].sum() / 1000.0
    total_err = (mod_gw - act_gw) / act_gw if act_gw else float("nan")

    # Per-fuel retired MW (grain-independent — a tranche split sums back).
    perfuel = {}
    fuels = set(act_thermal["fuel"]) | set(mod_thermal["fuel"])
    model_fuel_mw = mod_thermal.groupby("fuel")["mw"].sum().to_dict()
    actual_fuel_mw = act_thermal.groupby("fuel")["mw"].sum().to_dict()
    for f in sorted(fuels):
        a = actual_fuel_mw.get(f, 0.0) / 1000.0
        m = model_fuel_mw.get(f, 0.0) / 1000.0
        e = (m - a) / a if a else float("nan")
        perfuel[f] = {
            "actual_gw": round(a, 3),
            "model_gw": round(m, 3),
            "err_frac": None if np.isnan(e) else round(e, 3),
        }

    # --- Grain-corrected recall (G-31): per-fuel MW coverage --------------- #
    # A real retired unit is recalled when the model derated >= its MW of the
    # same fuel. Greedy largest-first so each unit claims distinct model MW.
    big = act_thermal[act_thermal["mw"] >= LARGE_UNIT_MW].sort_values(
        "mw", ascending=False
    )
    fuel_pool = {f: float(mw) for f, mw in model_fuel_mw.items()}
    matched = 0
    for _, a in big.iterrows():
        f, m = a["fuel"], float(a["mw"])
        if fuel_pool.get(f, 0.0) + 1e-6 >= m:
            matched += 1
            fuel_pool[f] = fuel_pool.get(f, 0.0) - m
    recall = matched / len(big) if len(big) else float("nan")

    # Stricter plant-exact diagnostic (reported, not banded): how many large
    # actual units the model also retired at the *same plant* of the same fuel.
    mod_plant_fuel = set()
    for _, r in mod_thermal.iterrows():
        pc = (
            model_plant_code(r["unit_id"]) if "unit_id" in mod_thermal.columns else None
        )
        if pc is not None:
            mod_plant_fuel.add((pc, r["fuel"]))
    plant_matched = 0
    if "plant_id" in big.columns:
        for _, a in big.iterrows():
            if (str(int(a["plant_id"])), a["fuel"]) in mod_plant_fuel:
                plant_matched += 1
    plant_recall = plant_matched / len(big) if len(big) else float("nan")

    # --- Grain-corrected false-retire (G-31): per-fuel excess -------------- #
    false_gw = 0.0
    for f in set(model_fuel_mw) | set(actual_fuel_mw):
        false_gw += (
            max(0.0, model_fuel_mw.get(f, 0.0) - actual_fuel_mw.get(f, 0.0)) / 1000.0
        )
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
            "grain": "fuel-mw-coverage",  # G-31: not exact unit identity
            "plant_recall_frac": None
            if np.isnan(plant_recall)
            else round(plant_recall, 3),
            "plant_matched": plant_matched,
            "band": ("PASS" if recall >= BANDS["retire_recall_min"] else "FAIL")
            if not np.isnan(recall)
            else "SKIP",
        },
        "false_retire": {
            "false_gw": round(false_gw, 3),
            "frac_of_model": round(false_frac, 3),
            "grain": "per-fuel-excess",  # G-31: genuine over-retire, not artifact
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
    """Total modelled CO2 (metric tonnes) per scored year.

    The LP result does not carry an ``emissions`` array in the forecast path,
    so CO2 is reconstructed from the persisted dispatch × the fleet context's
    per-generator emission rate (tCO2/MWh) — the same quantity the emissions
    module computes, but self-contained here.
    """
    from market_sim.results.outputs import from_parquet, read_fleet_context

    out = {}
    for year in SCORED_YEARS:
        p = bundle / f"year_{year}.parquet"
        if not p.exists():
            continue
        res = from_parquet(DispatchResult, p)
        if res.emissions is not None:
            out[year] = float(np.asarray(res.emissions).sum())
            continue
        try:
            ctx = read_fleet_context(p)
        except ValueError:
            continue
        rate = np.asarray(ctx.emission_rate, dtype=float)  # tCO2/MWh per gen
        gen_mwh = np.asarray(res.dispatch, dtype=float).sum(axis=1)
        out[year] = float((gen_mwh * rate).sum())
    return out


def _iso_plant_codes_and_states(iso: str) -> tuple[set[int], list[str]]:
    """ORISPL/plant codes and the states EIA-860 maps to ``iso``'s BA.

    Mirrors ``build_capacity_actuals._plant_ba``: the plant sheet's ``Balancing
    Authority Code`` is the ISO boundary, and CAMPD ``facilityId`` is the same
    ORISPL code as EIA ``Plant Code``. Returns the plant-code set (for the CAMPD
    facility filter) and the distinct states those plants sit in (to bound which
    CAMPD state files are read).
    """
    plant = pd.read_parquet(Path("data/raw/eia-860/eia860_plant.parquet"))
    plant = plant[pd.to_numeric(plant["Plant Code"], errors="coerce").notna()].copy()
    plant["Plant Code"] = plant["Plant Code"].astype(float).astype(int)
    bas = {ba for ba, i in BA_CODE_TO_ISO.items() if i == iso}
    sub = plant[plant["Balancing Authority Code"].isin(bas)]
    codes = set(int(c) for c in sub["Plant Code"].tolist())
    states = sorted({str(s).strip() for s in sub["State"].dropna() if str(s).strip()})
    return codes, states


def _actual_co2_facility(iso: str) -> dict[int, float]:
    """Facility-exact actual CO2 (metric tonnes), scored years only (rule 11).

    Filters CAMPD unit-level ``co2Mass`` (short → metric) to the plants EIA-860
    maps to ``iso``'s balancing authority, summed over the states the ISO spans.
    Used for footprint-crossing ISOs (``ISO_CAMPD_FACILITY``) where a state sum
    would double-count a neighbouring ISO. NEVER reads 2022/2026 (rule 22).
    """
    codes, states = _iso_plant_codes_and_states(iso)
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
            df = pd.read_parquet(p, columns=["facilityId", "co2Mass"])
            fid = pd.to_numeric(df["facilityId"], errors="coerce")
            mask = fid.isin(codes)
            total_short += float(
                pd.to_numeric(df.loc[mask, "co2Mass"], errors="coerce").sum()
            )
        if found:
            out[year] = total_short * SHORT_TON_TO_METRIC
    return out


def actual_co2_by_year(iso: str) -> dict[int, float]:
    """Derive actual CO2 (metric tonnes) from CAMPD unit-level, scored years only.

    Footprint-crossing ISOs (``ISO_CAMPD_FACILITY``: MISO, NYISO) use a
    facility-exact BA crosswalk. Single-state-dominant ISOs (ERCOT, PJM) sum
    ``co2Mass`` (short tons → metric) over their CAMPD state files; ERCOT ≈ TX
    (slight overcount, flagged). NEVER reads 2022/2026 (rule 22).
    """
    if iso in ISO_CAMPD_FACILITY:
        return _actual_co2_facility(iso)
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
    pr = (
        ""
        if rr.get("plant_recall_frac") is None
        else format(rr["plant_recall_frac"], ".0%")
    )
    L.append(
        "> **Grain (G-31):** recall and false-retire are scored at **per-fuel MW "
        "coverage**, not exact unit identity — a real retired unit is *recalled* "
        "when the model derated ≥ its MW of the same fuel (its plant-binned tranche "
        "is derated by its MW), and *false-retire* is the model's per-fuel MW in "
        "**excess** of what that fuel actually retired. This retires the 94% "
        "false-retire artifact the old 1:1 `fuel+size` match produced against lumpy "
        f"tranche/zone derates. Stricter plant-exact recall (same plant, reported "
        f"only): **{pr or '—'}** ({rr.get('plant_matched', 0)}/{rr['n_big_actual']}). "
        "A false-retire that stays high after the grain fix is a genuine "
        "over-retirement (screen root-cause, e.g. G-30), not a scoring artifact."
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
    # Name the report after the bundle's run id (the out-dir name), so probe
    # arms of one ISO/variant scored the same day (e.g. the CR-3.1
    # -p2c-elcc / -p2c-base before/after pair) never overwrite each other;
    # falls back to the legacy iso-window-variant stem for bare dirs.
    run_id = args.bundle.name or f"{iso.lower()}-2021-2025-{variant}"
    report_path = args.report_dir / f"{run_id}-{stamp}.md"
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

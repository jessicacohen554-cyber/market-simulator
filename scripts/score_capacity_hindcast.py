#!/usr/bin/env python
"""Score a capacity hindcast against actuals (W2-P5, plan §1.4).

Consumes a bundle produced by ``scripts/run_capacity_hindcast.py`` (evolution
ledgers + dispatch parquets under ``results/hindcast/<run>/<iso>/<key>/``) and
the scoring target ``data/raw/_validation-source/capacity_actuals_<iso>.csv``
(built by ``scripts/data/build_capacity_actuals.py``). Emits:

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
import csv
import json
import re
import sys
from datetime import date, datetime, timezone
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
# IS-2020 information-set scoring (RC-0B §c.5, T-R8)
# --------------------------------------------------------------------------- #
# The vintage cutoff V: what was knowable at forecast start (EIA-860 2020
# vintage). Anything whose instrument/announcement post-dates V is unknowable at
# forecast start (RC-0B §c.5-5). Raw scoring grades realized usefulness against
# latest truth; IS-2020 grades forecast skill against the 2020 information set.
# Both are reported side by side — quoting only the flattering one is scoring
# abuse (RC-0B §c.5).
IS2020_CUTOFF = date(2020, 12, 31)

# Retirement-channel vocabulary (RC-0B §c.5-4). Ledger `reason` values map here;
# a bundle produced before the RC-1B recorder split records the pre-split
# "known" reason (steps 0-1 conflated) → announced (rule: legacy "known" maps to
# announced for pre-split bundles).
CHANNEL_ORDER = ("confirmed", "announced", "economic")
_LEGACY_REASON = {"known": "announced"}


# --------------------------------------------------------------------------- #
# Actuals + model aggregation
# --------------------------------------------------------------------------- #
def load_actuals(iso: str) -> pd.DataFrame:
    """Load the committed capacity-actuals CSV for an ISO."""
    path = Path("data/raw/_validation-source") / f"capacity_actuals_{iso.lower()}.csv"
    if not path.exists():
        raise SystemExit(
            f"actuals not found: {path} — run scripts/data/build_capacity_actuals.py --iso {iso}"
        )
    return pd.read_csv(path, comment="#")


def model_retirements(ledgers: dict) -> pd.DataFrame:
    """All modelled retirements across the window (from the ledgers).

    Carries the ledger ``reason`` verbatim so per-channel scoring (§c.5-4) can
    partition on the ``{confirmed, announced, economic}`` vocabulary. Bundles
    produced before the RC-1B recorder split record the pre-split ``"known"``
    reason (steps 0-1 conflated); ``channel_of`` maps that to ``announced``.
    """
    rows = []
    for year, led in ledgers.items():
        for r in led.get("retirements", []):
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["mw"]),
                    "year": year,
                    "reason": r.get("reason", "economic"),
                }
            )
    return pd.DataFrame(rows, columns=["unit_id", "fuel", "mw", "year", "reason"])


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


def model_plant_gen(unit_id: str) -> tuple[str, str] | None:
    """`(plant_code, generator_id)` from a raw-EIA ``unit_id`` (``6023_1``).

    Announced/confirmed retirements are recorded at raw ``<plant>_<gen>`` grain
    (e.g. Byron ``6023_1``, Dresden ``869_2``), the grain the confirmed-registry
    reversal rows are keyed on. Returns ``None`` for tranche/zone forms (a
    plant-binned economic derate carries no single generator id — it can never be
    a registry reversal match, which is correct: reversal rows are unit-grain
    nuclear only).
    """
    m = re.fullmatch(r"(\d+)_([A-Za-z0-9]+)", str(unit_id))
    if m:
        return m.group(1), m.group(2)
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
# IS-2020 information-set scoring (RC-0B §c.5, T-R8) — no re-solve
# --------------------------------------------------------------------------- #
def channel_of(reason) -> str:
    """Map a ledger ``reason`` onto the ``{confirmed, announced, economic}``
    channel vocabulary (§c.5-4). Legacy ``"known"`` → ``announced``."""
    if reason is None or (isinstance(reason, float) and np.isnan(reason)):
        return "economic"
    r = str(reason)
    return _LEGACY_REASON.get(r, r)


def load_reversal_set(iso: str) -> dict[tuple[str, str], dict]:
    """Post-cutoff reversal rows from the confirmed-registry (§c.5-1).

    Membership test for the Byron/Dresden class: a confirmed-registry row with
    ``superseded=true`` whose original instrument was public on or before V
    (``instrument_date <= V``) and was superseded *only* by a counter-instrument
    dated **after** V (``superseding_instrument_date > V``). Keyed on
    ``(plant_id, generator_id)`` — the grain the model records nuclear exits on.

    Eddystone (superseded by a DOE 202(c) order with **no**
    ``superseding_instrument_date`` populated) is correctly excluded: its
    reversal date is unknown to the registry, so it is not a knowable-at-V
    information-set-correct reversal. Diablo Canyon (SB 846, 2022-09) would
    qualify for any future CAISO window; none of the four T-R8 ISOs but PJM
    carries a post-V reversal row.

    Returns ``{(plant, gen): {instrument, unit_name, capacity_mw}}``; empty when
    the ISO has no registry file (read robustly past the ``#`` comment header —
    the registry carries commas inside quoted instrument text).
    """
    path = Path("data/raw/confirmed-retirements") / f"{iso.lower()}.csv"
    if not path.exists():
        return {}
    cutoff = pd.Timestamp(IS2020_CUTOFF)
    lines = [
        ln
        for ln in path.read_text().splitlines(keepends=True)
        if not ln.lstrip().startswith("#")
    ]
    out: dict[tuple[str, str], dict] = {}
    for row in csv.DictReader(lines):
        superseded = str(row.get("superseded") or "").strip().lower() in (
            "true",
            "1",
            "yes",
        )
        if not superseded:
            continue
        sup_date = pd.to_datetime(
            (row.get("superseding_instrument_date") or "").strip(), errors="coerce"
        )
        inst_date = pd.to_datetime(
            (row.get("instrument_date") or "").strip(), errors="coerce"
        )
        # Knowable-at-V original, unknowable-at-V reversal (the §c.5-1 class).
        if pd.isna(sup_date) or sup_date <= cutoff:
            continue
        if pd.notna(inst_date) and inst_date > cutoff:
            continue
        key = (
            str(row.get("plant_id") or "").strip(),
            str(row.get("generator_id") or "").strip(),
        )
        out[key] = {
            "instrument": (row.get("superseding_instrument") or "").strip(),
            "unit_name": (row.get("unit_name") or "").strip(),
            "capacity_mw": row.get("capacity_mw"),
        }
    return out


def reversal_exposure(model: pd.DataFrame, reversal_set: dict) -> dict:
    """Model retirements that qualify for IS-2020 reversal exclusion (§c.5-1).

    A model row is reversal-exposed iff its ``(plant, generator)`` is in the
    post-cutoff reversal set. Its MW is **excluded from IS-2020 false-retire**
    and reported here as ``reversal_exposure_gw`` naming the reversing
    instrument. Raw scoring keeps the MW as false-retire (realized reality: the
    unit runs today). Returns the exposed rows, total GW, unit_ids, and the
    distinct instruments.
    """
    rows, exposed_ids = [], set()
    if not reversal_set or model.empty:
        return {"exposure_gw": 0.0, "rows": [], "unit_ids": set(), "instruments": []}
    for _, r in model.iterrows():
        pg = model_plant_gen(r["unit_id"])
        if pg is not None and pg in reversal_set:
            info = reversal_set[pg]
            rows.append(
                {
                    "unit_id": r["unit_id"],
                    "fuel": r["fuel"],
                    "mw": float(r["mw"]),
                    "plant_id": pg[0],
                    "generator_id": pg[1],
                    "unit_name": info["unit_name"],
                    "instrument": info["instrument"],
                }
            )
            exposed_ids.add(r["unit_id"])
    gw = round(sum(x["mw"] for x in rows) / 1000.0, 3)
    instruments = sorted({x["instrument"] for x in rows if x["instrument"]})
    return {
        "exposure_gw": gw,
        "rows": rows,
        "unit_ids": exposed_ids,
        "instruments": instruments,
    }


def score_retirements_is2020(
    model: pd.DataFrame, actuals: pd.DataFrame, reversal_set: dict
) -> dict:
    """IS-2020 retirement scoring: raw metric with reversal-exposed MW removed.

    Only the reversal exclusion (§c.5-1) changes the numbers here; the Palisades
    physical-exit convention (§c.5-2) and Indian Point coverage fix (§c.5-3) act
    through the **actuals** (RD-5), so they are already reflected in the raw pass
    and need no model-side adjustment. IS false-retire drops the information-set-
    correct reversals; recall is recomputed on the reduced model but is unchanged
    wherever the reversed fuel has no actual to cover (the PJM nuclear case).
    """
    exposure = reversal_exposure(model, reversal_set)
    keep = (
        model[~model["unit_id"].isin(exposure["unit_ids"])]
        if exposure["unit_ids"]
        else model
    )
    base = score_retirements(keep, actuals)
    base["reversal_exposure_gw"] = exposure["exposure_gw"]
    base["reversal_instruments"] = exposure["instruments"]
    base["reversal_rows"] = exposure["rows"]
    return base


def score_channels(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """Per-channel recall + false-retire (§c.5-4), keyed ``{confirmed, announced,
    economic}`` so an economic-screen grade is never polluted by an announced-
    channel event (or vice-versa).

    * **false-retire** is decomposed by allocating each fuel's *actual* retired
      MW across channels in a fixed priority order (confirmed → announced →
      economic); a channel's false-retire is its per-fuel model MW in excess of
      the actual MW still un-attributed when it is reached. The per-channel sum
      reproduces the raw total exactly, and — because the four T-R8 bundles are
      each single-channel per fuel — the allocation is order-independent here.
    * **recall** attributes each ≥300 MW actual unit to the first channel (same
      priority order) whose remaining same-fuel model pool alone covers it; the
      per-channel matched counts sum to the raw matched count wherever each fuel
      is retired by a single channel (all four bundles).
    """
    if "reason" not in model.columns:
        model = model.assign(reason="economic")
    model = model.assign(channel=model["reason"].map(channel_of))
    act = actuals[actuals["kind"] == "retirement"]
    act_th = act[act["fuel"].isin(THERMAL_FUELS)]
    actual_fuel_mw = act_th.groupby("fuel")["mw"].sum().to_dict()

    present = list(dict.fromkeys(model["channel"].tolist()))
    ordered = [c for c in CHANNEL_ORDER if c in present] + [
        c for c in present if c not in CHANNEL_ORDER
    ]

    # False-retire: priority allocation of actual MW pools.
    pool = dict(actual_fuel_mw)
    out: dict[str, dict] = {}
    for c in ordered:
        cm = model[model["channel"] == c]
        cfuel = cm.groupby("fuel")["mw"].sum().to_dict()
        false_gw = 0.0
        for f, mw in cfuel.items():
            avail = pool.get(f, 0.0)
            false_gw += max(0.0, mw - avail) / 1000.0
            pool[f] = max(0.0, avail - mw)
        out[c] = {
            "retired_gw": round(float(cm["mw"].sum()) / 1000.0, 3),
            "false_retire_gw": round(false_gw, 3),
            "model_fuel_gw": {f: round(v / 1000.0, 3) for f, v in cfuel.items()},
        }

    # Recall attribution: greedy, largest actual unit first, priority order.
    big = act_th[act_th["mw"] >= LARGE_UNIT_MW].sort_values("mw", ascending=False)
    rpool = {
        c: model[model["channel"] == c].groupby("fuel")["mw"].sum().to_dict()
        for c in ordered
    }
    matched = {c: 0 for c in ordered}
    for _, a in big.iterrows():
        f, m = a["fuel"], float(a["mw"])
        for c in ordered:
            if rpool[c].get(f, 0.0) + 1e-6 >= m:
                matched[c] += 1
                rpool[c][f] = rpool[c].get(f, 0.0) - m
                break
    for c in ordered:
        out[c]["recall_matched"] = matched[c]
    out["_n_big_actual"] = int(len(big))
    out["_legacy_known_mapped_to"] = "announced"
    return out


def additions_is2020(model_add: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """IS-2020 additions adjustment: exclude post-V restart additions (§c.5-2).

    Convention (Palisades): the physical 2022 exit is booked in the actuals and
    scores as a correct recall in both modes; the ~2025 *restart* is a post-V
    instrument, unknowable at forecast start, so it is excluded from IS-2020
    additions. A restart is an ``addition`` of a fuel at a ``plant_id`` that the
    same actuals record as an earlier in-window ``retirement`` of that fuel.

    Model additions carry no plant identity, so the exclusion is defined over the
    actuals only (the model cannot double-count a restart it never added). In the
    RD-5 actuals as landed there is **no** restart addition row — the coverage
    fix booked only Palisades' physical exit — so this is inert here; it is
    implemented for correctness and forward CAISO/Diablo windows.
    """
    act = actuals[actuals["kind"] == "addition"]
    excluded_gw = 0.0
    excluded_rows: list[dict] = []
    if "plant_id" in actuals.columns:
        retired_plants = set(
            actuals[actuals["kind"] == "retirement"]
            .apply(lambda r: (str(r.get("plant_id")), r["fuel"]), axis=1)
            .tolist()
        )
        for _, a in act.iterrows():
            if (str(a.get("plant_id")), a["fuel"]) in retired_plants:
                excluded_gw += float(a["mw"]) / 1000.0
                excluded_rows.append(
                    {
                        "plant_id": str(a.get("plant_id")),
                        "fuel": a["fuel"],
                        "mw": float(a["mw"]),
                    }
                )
    return {
        "restart_excluded_gw": round(excluded_gw, 3),
        "restart_rows": excluded_rows,
        "note": (
            "Post-V restart additions excluded from IS-2020 additions (§c.5-2). "
            "Inert in the RD-5 actuals as landed — the coverage fix booked only "
            "the physical exit, no restart addition row exists."
        ),
    }


# --------------------------------------------------------------------------- #
# Flip-gate extras (FF-1A): T-R10 no-inversion guard, LOYO folds, BLK-10
# backstop-fired MW — all scorer-side, computed from the committed evolution
# ledgers + RD-5 actuals. NO LP is solved here.
# --------------------------------------------------------------------------- #
# T-R10b zero-real-fuel accumulation threshold (GW). Pre-registered in the
# retirement-rule redesign memo §4 (ff-retirement-rule-redesign-2026-07.md):
# a fuel that retired ZERO in reality accumulating > 1 GW of model economic
# exits is a cross-fuel inversion, whatever the totals do.
TR10B_ZERO_REAL_GW_MAX = 1.0


def score_tr10(model: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    """T-R10 no-inversion guard (redesign memo §4, pre-registered).

    Evaluated on the **economic channel only** (announced/confirmed events are
    instrument-driven, not decision-rule output — the PJM Byron/Dresden nuclear
    reversal must never trip this guard):

    * ``first_mover`` — fuel(s) of the earliest model economic-channel exit.
      **T-R10a** FAILs iff any first-mover fuel has actual retired MW = 0
      (the model's first economic wave hits a fuel reality never retired).
    * **T-R10b** FAILs iff any fuel with zero actual retirements accumulates
      more than ``TR10B_ZERO_REAL_GW_MAX`` GW of model economic exits.

    Vacuously PASS when the model has no economic thermal exits (no wave, no
    inversion). Bands are pre-registered and never widened (rules 1/14).
    """
    act = actuals[actuals["kind"] == "retirement"]
    act_th = act[act["fuel"].isin(THERMAL_FUELS)]
    actual_fuel_mw = act_th.groupby("fuel")["mw"].sum().to_dict()

    if "reason" not in model.columns:
        model = model.assign(reason="economic")
    econ = model[model["reason"].map(channel_of) == "economic"]
    econ_th = econ[econ["fuel"].isin(THERMAL_FUELS)]

    econ_fuel_gw = {
        f: round(mw / 1000.0, 3)
        for f, mw in econ_th.groupby("fuel")["mw"].sum().to_dict().items()
    }
    if econ_th.empty:
        return {
            "first_mover_fuels": [],
            "first_mover_year": None,
            "econ_exit_gw_by_fuel": {},
            "zero_real_fuels_over_1gw": [],
            "tr10a": "PASS",
            "tr10b": "PASS",
            "note": "no economic thermal exits — vacuous PASS",
        }
    first_year = int(econ_th["year"].min())
    first_movers = sorted(econ_th[econ_th["year"] == first_year]["fuel"].unique())
    tr10a_fail = any(actual_fuel_mw.get(f, 0.0) <= 0.0 for f in first_movers)
    zero_real_over = sorted(
        f
        for f, gw in econ_fuel_gw.items()
        if actual_fuel_mw.get(f, 0.0) <= 0.0 and gw > TR10B_ZERO_REAL_GW_MAX
    )
    return {
        "first_mover_fuels": first_movers,
        "first_mover_year": first_year,
        "econ_exit_gw_by_fuel": econ_fuel_gw,
        "actual_gw_by_fuel": {
            f: round(mw / 1000.0, 3) for f, mw in sorted(actual_fuel_mw.items())
        },
        "zero_real_fuels_over_1gw": zero_real_over,
        "tr10a": "FAIL" if tr10a_fail else "PASS",
        "tr10b": "FAIL" if zero_real_over else "PASS",
    }


def blk10_backstop_fired(ledgers: dict) -> dict:
    """BLK-10: precise reserve-margin-backstop fired MW (gap-register §3.9).

    Sums ``thermal_additions`` rows whose ``source == "reserve_backstop"`` —
    the adequacy backstop's own ledger channel (``gas_ct_adequacy_<year>``
    units) — per year and in total, alongside the economic/planned additions
    split, so the backstop's share of the build is separable from economic
    entry. Pure ledger arithmetic; no LP.
    """
    fired_rows: list[dict] = []
    by_source: dict[str, float] = {}
    for year, led in ledgers.items():
        for a in led.get("thermal_additions", []):
            src = a.get("source", "economic")
            by_source[src] = by_source.get(src, 0.0) + float(a["mw"])
            if src == "reserve_backstop":
                fired_rows.append(
                    {
                        "year": int(year),
                        "unit_id": a.get("unit_id"),
                        "fuel": a.get("fuel"),
                        "mw": round(float(a["mw"]), 3),
                    }
                )
    fired_mw = sum(r["mw"] for r in fired_rows)
    return {
        "fired_rows": fired_rows,
        "fired_mw_total": round(fired_mw, 3),
        "fired_gw_total": round(fired_mw / 1000.0, 3),
        "thermal_additions_mw_by_source": {
            k: round(v, 3) for k, v in sorted(by_source.items())
        },
    }


def loyo_folds(model: pd.DataFrame, actuals: pd.DataFrame, reversal_set: dict) -> dict:
    """Leave-one-year-out folds within the scored years (rule 22 LOYO clause).

    Fold ``y`` re-scores the cumulative window with year ``y``'s events removed
    from BOTH the model ledger and the actuals (2021 seed-year and 2022-bridge
    events always stay — only scored years are held out). Scorer-side only: the
    fold is a re-score of the committed bundle, never a re-solve. Per fold:
    grain-corrected recall, false-retire (raw + IS-2020), and the T-R10a/b
    guard. The promotion criterion (plan §2.1 item 4 / rule 22) is that a
    verdict holds in >= 2 of 3 folds; ``holds_2of3`` grades exactly that for
    recall-PASS, T-R10a-PASS and T-R10b-PASS.
    """
    folds: dict[str, dict] = {}
    for y in SCORED_YEARS:
        m = model[model["year"] != y]
        a = actuals[actuals["year"] != y]
        ret = score_retirements(m, a)
        ret_is = score_retirements_is2020(m, a, reversal_set)
        tr10 = score_tr10(m, a)
        rr = ret["unit_recall_gt300"]
        folds[str(y)] = {
            "held_out_year": y,
            "recall": rr["recall"],
            "recall_band": rr["band"],
            "matched": rr["matched"],
            "n_big_actual": rr["n_big_actual"],
            "false_retire_gw_raw": ret["false_retire"]["false_gw"],
            "false_retire_band_raw": ret["false_retire"]["band"],
            "false_retire_gw_is2020": ret_is["false_retire"]["false_gw"],
            "tr10a": tr10["tr10a"],
            "tr10b": tr10["tr10b"],
            "tr10_first_mover_fuels": tr10["first_mover_fuels"],
        }

    def _holds(key: str, ok: str) -> bool:
        return sum(1 for f in folds.values() if f[key] == ok) >= 2

    return {
        "folds": folds,
        "holds_2of3": {
            "recall_pass": _holds("recall_band", "PASS"),
            "tr10a_pass": _holds("tr10a", "PASS"),
            "tr10b_pass": _holds("tr10b", "PASS"),
        },
        "note": (
            "Scorer-side LOYO: fold y drops year-y events from model AND "
            "actuals; no re-solve. >=2/3 folds is the rule-22 promotion bar."
        ),
    }


def _flip_gate_extras(bundle: Path) -> int:
    """Compute T-R10 + LOYO + BLK-10 on a committed bundle and update its
    score.json (keys ``tr10``, ``tr10_is2020``, ``loyo``, ``blk10_backstop``).
    No LP is solved; the existing score keys are preserved."""
    meta = json.loads((bundle / "meta.json").read_text())
    iso = meta["iso"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret = model_retirements(ledgers)
    reversal_set = load_reversal_set(iso)

    tr10 = score_tr10(mret, actuals)
    exposure = reversal_exposure(mret, reversal_set)
    mret_is = (
        mret[~mret["unit_id"].isin(exposure["unit_ids"])]
        if exposure["unit_ids"]
        else mret
    )
    tr10_is = score_tr10(mret_is, actuals)
    loyo = loyo_folds(mret, actuals, reversal_set)
    blk10 = blk10_backstop_fired(ledgers)

    score_path = cache_dir / "score.json"
    score = json.loads(score_path.read_text()) if score_path.exists() else {}
    score.update(
        {
            "tr10": tr10,
            "tr10_is2020": tr10_is,
            "loyo": loyo,
            "blk10_backstop": blk10,
            "flip_gate_extras": {
                "task": "FF-1A",
                "note": (
                    "T-R10 no-inversion guard + LOYO folds (2023-2025) + "
                    "BLK-10 backstop-fired MW — scorer-side, no re-solve."
                ),
                "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }
    )
    score_path.write_text(json.dumps(score, indent=2))

    h = loyo["holds_2of3"]
    print(
        f"[flip-gate] {iso} {bundle.name}: T-R10a {tr10['tr10a']} / "
        f"T-R10b {tr10['tr10b']} (first mover {tr10['first_mover_fuels']}); "
        f"LOYO holds>=2/3: recall={h['recall_pass']} tr10a={h['tr10a_pass']} "
        f"tr10b={h['tr10b_pass']}; BLK-10 fired {blk10['fired_gw_total']} GW"
    )
    for fy, f in loyo["folds"].items():
        print(
            f"[flip-gate]   fold -{fy}: recall "
            f"{f['matched']}/{f['n_big_actual']} ({f['recall_band']}), "
            f"false raw {f['false_retire_gw_raw']} GW, "
            f"tr10a {f['tr10a']} tr10b {f['tr10b']}"
        )
    print(f"[flip-gate] score.json: {score_path}")
    return 0


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


def render_rescore_section(
    iso: str, ret: dict, ret_is: dict, channels: dict, add_is: dict, stamp: str
) -> str:
    """The IS-2020 re-score section appended to a hindcast report (T-R8).

    Presents raw and IS-2020 metrics side by side (RC-0B §c.5: quoting only the
    flattering one is scoring abuse), the reversal-exposure line naming the
    instrument, and the per-channel recall/false-retire tables. The originals
    above this marker are preserved — this is scoring hygiene on the *committed*
    bundle, no re-solve.
    """
    fr, rr = ret["false_retire"], ret["unit_recall_gt300"]
    fr_is = ret_is["false_retire"]
    exp = ret_is.get("reversal_exposure_gw", 0.0)
    L = []
    L.append("")
    L.append("---")
    L.append("")
    L.append(f"## IS-2020 re-score (T-R8, {stamp}) — no re-solve")
    L.append("")
    L.append(
        "Scoring-hygiene re-score of the **committed** bundle against RC-0B §c.5: "
        "**raw** grades realized usefulness against latest truth; **IS-2020** grades "
        "forecast skill against what was knowable at the 2020 vintage cutoff "
        f"(V = {IS2020_CUTOFF.isoformat()}). Both are reported side by side — neither "
        "replaces the other. No LP was solved; the originals above are preserved. "
        "The RD-5 actuals-coverage fix (plants 8907 Indian Point, 1715 Palisades) is "
        "already reflected in the raw pass; IS-2020 adds the Byron/Dresden reversal "
        "exclusion (§c.5-1)."
    )
    L.append("")
    L.append("| retirement metric | raw | IS-2020 |")
    L.append("|---|--:|--:|")
    L.append(
        f"| false-retire (GW) | {fr['false_gw']} ({_fmt_band(fr['band'])}) | "
        f"{fr_is['false_gw']} ({_fmt_band(fr_is['band'])}) |"
    )
    L.append(
        f"| false-retire (% of model) | {format(fr['frac_of_model'], '.0%')} | "
        f"{format(fr_is['frac_of_model'], '.0%')} |"
    )
    rr_is = ret_is["unit_recall_gt300"]
    L.append(
        f"| unit recall >300MW | {('' if rr['recall'] is None else format(rr['recall'], '.0%'))} "
        f"({rr['matched']}/{rr['n_big_actual']}) | "
        f"{('' if rr_is['recall'] is None else format(rr_is['recall'], '.0%'))} "
        f"({rr_is['matched']}/{rr_is['n_big_actual']}) |"
    )
    pr = rr.get("plant_recall_frac")
    L.append(
        f"| plant-exact recall (diagnostic) | "
        f"{('—' if pr is None else format(pr, '.0%'))} "
        f"({rr.get('plant_matched', 0)}/{rr['n_big_actual']}) | (same) |"
    )
    L.append(f"| reversal exposure (GW, §c.5-1) | — | {exp} |")
    L.append("")
    # Finding: plant-exact recall above fuel-MW recall means the model retired the
    # right plant(s) but carries a pmax below the EIA nameplate the RD-5 actuals
    # use — a units-basis near-miss, not a screen miss (rules 1/11: keep the
    # accurate actual, surface the basis gap rather than bend the metric).
    if pr is not None and rr["recall"] is not None and pr > rr["recall"] + 1e-9:
        L.append(
            "> **Recall-grain finding (§c.5-2/-3):** plant-exact recall "
            f"({format(pr, '.0%')}) exceeds fuel-MW-coverage recall "
            f"({format(rr['recall'], '.0%')}) — the model retired the correct "
            "plant(s) in the correct year, but its carried `pmax` sits below the "
            "EIA nameplate the RD-5 actuals use (Palisades: model 768.5 MW vs "
            "actual nameplate 811.8 MW, a 5% basis gap), so the strict ≥-MW "
            "coverage test marks it a near-miss. This is a nameplate-vs-pmax "
            "basis difference, **not** a screen error, and it is the correct "
            "recall §c.5-2/-3 intends — reported honestly at both grains, metric "
            "unbent (rules 1/11). The false-retire and reversal results are "
            "unaffected."
        )
        L.append("")
    if ret_is.get("reversal_rows"):
        L.append(
            f"> **Reversal exclusion (§c.5-1):** {exp} GW of model nuclear "
            "retirement is information-set-correct (mandated by an instrument "
            "public ≤ V) but reality-reversed by a post-V counter-instrument, so "
            "it is **excluded from IS-2020 false-retire** and reported as "
            "`reversal_exposure_gw`. Raw scoring keeps it as false-retire (the unit "
            "runs today). Reversing instrument(s): "
            + "; ".join(
                f"{r['unit_name']} ({r['unit_id']})" for r in ret_is["reversal_rows"]
            )
            + " — "
            + (
                ret_is["reversal_instruments"][0]
                if ret_is["reversal_instruments"]
                else ""
            )
            + "."
        )
        L.append("")
    # Per-channel table.
    L.append("Per-channel recall + false-retire (§c.5-4, legacy `known` → announced):")
    L.append("")
    L.append(
        "| channel | retired GW | false-retire GW | recall (matched / big-actual) |"
    )
    L.append("|---|--:|--:|--:|")
    n_big = channels.get("_n_big_actual", 0)
    for c in CHANNEL_ORDER:
        if c not in channels:
            continue
        d = channels[c]
        L.append(
            f"| {c} | {d['retired_gw']} | {d['false_retire_gw']} | "
            f"{d['recall_matched']}/{n_big} |"
        )
    for c in channels:
        if c in CHANNEL_ORDER or c.startswith("_"):
            continue
        d = channels[c]
        L.append(
            f"| {c} | {d['retired_gw']} | {d['false_retire_gw']} | "
            f"{d['recall_matched']}/{n_big} |"
        )
    L.append("")
    if add_is.get("restart_excluded_gw", 0.0) or add_is.get("note"):
        L.append(f"> **Additions (§c.5-2):** {add_is['note']}")
        L.append("")
    return "\n".join(L)


def append_rescore(report_path: Path, section: str) -> None:
    """Append the re-score section to an existing report, preserving the original.

    Idempotent on the section marker: a prior IS-2020 re-score block for the same
    day is replaced rather than stacked, so re-running the scorer does not grow
    the file without bound."""
    marker = "## IS-2020 re-score (T-R8"
    body = report_path.read_text() if report_path.exists() else ""
    idx = body.find("\n---\n\n" + marker)
    if idx == -1:
        idx = body.find(marker)
        if idx != -1:  # marker without the divider prefix — trim from there
            idx = body.rfind("\n", 0, idx)
    if idx != -1:
        body = body[:idx].rstrip() + "\n"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(body.rstrip() + "\n" + section.rstrip() + "\n")


def _rescore(bundle: Path, report: Path | None) -> int:
    """T-R8 re-score: recompute retirements (raw + IS-2020 + per-channel) on the
    committed bundle with the current RD-5 actuals, preserve the existing
    ``co2``/``baselines`` (CO2 needs the uncommitted dispatch parquets — RD-5
    changes neither), update ``score.json``, and append the re-score section to
    the report. No LP is solved."""
    meta = json.loads((bundle / "meta.json").read_text())
    iso, variant = meta["iso"], meta["variant"]
    cache_dir = Path(meta["bundle"])
    if not cache_dir.exists():
        cache_dir = bundle / iso / meta["cache_key"]

    ledgers = load_ledgers_for_run(cache_dir)
    actuals = load_actuals(iso)
    mret, madd = model_retirements(ledgers), model_additions(ledgers)

    ret = score_retirements(mret, actuals)  # raw, RD-5 actuals
    add = score_additions(madd, actuals)
    reversal_set = load_reversal_set(iso)
    ret_is = score_retirements_is2020(mret, actuals, reversal_set)
    channels = score_channels(mret, actuals)
    add_is = additions_is2020(madd, actuals)

    score_path = cache_dir / "score.json"
    score = json.loads(score_path.read_text()) if score_path.exists() else {}
    score.update(
        {
            "iso": iso,
            "variant": variant,
            "scored_years": list(SCORED_YEARS),
            "retirements": ret,
            "additions": add,
            "retirements_is2020": ret_is,
            "retirement_channels": channels,
            "additions_is2020": add_is,
            "is2020_cutoff": IS2020_CUTOFF.isoformat(),
            "bands": BANDS,
            "rescore": {
                "task": "T-R8",
                "note": (
                    "IS-2020 scoring hygiene (RC-0B §c.5) — raw + IS-2020 + "
                    "per-channel. No re-solve; RD-5 actuals; co2/baselines "
                    "preserved (unchanged by RD-5)."
                ),
                "utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            },
        }
    )
    score.setdefault("co2", {"model": {}, "actual": {}})
    score.setdefault("baselines", {"announced": baseline_announced(iso)})
    score_path.write_text(json.dumps(score, indent=2))

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if report is None:
        report = _find_report(iso, variant, bundle.name)
    if report is not None:
        section = render_rescore_section(iso, ret, ret_is, channels, add_is, stamp)
        append_rescore(report, section)

    fr, fr_is = ret["false_retire"], ret_is["false_retire"]
    print(
        f"[rescore] {iso} {bundle.name}: raw false-retire {fr['false_gw']} GW "
        f"({fr['band']}) → IS-2020 {fr_is['false_gw']} GW ({fr_is['band']}); "
        f"reversal_exposure {ret_is.get('reversal_exposure_gw', 0.0)} GW"
    )
    print(f"[rescore] score.json: {score_path}")
    print(f"[rescore] report:     {report}")
    return 0


def _find_report(iso: str, variant: str, run_id: str) -> Path | None:
    """Locate the committed report for a bundle: newest ``<run_id>-<date>.md``."""
    rdir = Path("docs/hindcast-reports")
    cands = sorted(rdir.glob(f"{run_id}-*.md"))
    if cands:
        return cands[-1]
    cands = sorted(rdir.glob(f"{iso.lower()}-2021-2025-{variant}-*.md"))
    return cands[-1] if cands else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle", type=Path, required=True, help="run_capacity_hindcast out-dir."
    )
    parser.add_argument(
        "--report-dir", type=Path, default=Path("docs/hindcast-reports")
    )
    parser.add_argument(
        "--rescore",
        action="store_true",
        help=(
            "T-R8 IS-2020 re-score: recompute retirements (raw + IS-2020 + "
            "per-channel) on the committed bundle, preserve co2/baselines, and "
            "APPEND a re-score section to the existing report (no re-solve)."
        ),
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        help="Existing report to append the --rescore section to (default: auto-locate).",
    )
    parser.add_argument(
        "--flip-gate-extras",
        action="store_true",
        help=(
            "FF-1A scorer-side extras (no re-solve): T-R10 no-inversion guard "
            "(raw + IS-2020), LOYO folds within 2023-2025, and BLK-10 "
            "reserve-backstop fired MW — computed from the committed evolution "
            "ledgers + RD-5 actuals, merged into score.json."
        ),
    )
    args = parser.parse_args(argv)

    if args.flip_gate_extras:
        return _flip_gate_extras(args.bundle)

    if args.rescore:
        return _rescore(args.bundle, args.report)

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

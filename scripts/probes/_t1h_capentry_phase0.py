#!/usr/bin/env python3
"""T1-H capacity-entry Phase-0 probe — ZERO-SOLVE records + measurement.

Charter: ``docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md`` (owner ruling
2026-08-30, decision card 2). Parent defect register:
``docs/FINDING-entry-screen-t1h-2026-08.md`` (D-1 … D-9). Finding produced
from this probe: ``docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md``.

**No LP solve, no hindcast re-run, no mechanism/default/constant change.**
Every number is read from a committed artifact or is arithmetic replayed on
committed inputs. The four sections mirror the charter's Phase-0 steps:

0. ``dedup`` — verify capx D11-R's ``entry_margin_exhaustion`` claims D-1
   (bang-bang entry VOLUME), and state precisely which defects its rule does
   and does not touch; run the charter's stop rule against HEAD for D-2/D-3.
1. ``d2`` — storage-technology census: every storage tech built in any T1-H
   decision year vs the measured deployment record for that technology class
   (EIA-860 2025 Early Release energy-storage schedule, committed).
2. ``d3`` — re-execute the committed storage-entry ranking arithmetic
   (``model/storage.py`` bang-bang block) on the committed entering-2023
   margins, then re-rank on margin-per-unit-capital-cost and report the
   counterfactual build mix.
3. ``legb`` — decompose the wind capture-ratio repair into a LEVEL leg (the
   dual-based signal object) and a ZONAL leg (per-zone dual rows), on
   committed artifacts only; report what is and is not computable zero-solve.

Usage::

    python3 scripts/probes/_t1h_capentry_phase0.py            # all sections
    python3 scripts/probes/_t1h_capentry_phase0.py --section d3
    python3 scripts/probes/_t1h_capentry_phase0.py --out /tmp/phase0.json

Data profile: ``ercot`` is needed only for the EIA-860 rows in ``d2``
(``data/raw/eia-860/eia860_energy_storage_*.parquet`` +
``eia860_generator_operable.parquet``); every other section runs on a ``code``
profile. Missing inputs are reported as such, never estimated.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Committed artifact paths (every number in the finding traces to one of these)
# ---------------------------------------------------------------------------
PHASE0_ERCOT = REPO / "results/calibration/entry_screen_t1h_phase0_ercot.json"
L1_DUAL_ERCOT = REPO / "results/calibration/entry_signal_l1_dual_replay_ercot.json"
DISARM_LEDGER = REPO / "results/calibration/entry_signal_disarm_ledger_ercot.json"
D11R_AB = REPO / "results/calibration/entry_volume_rule_ab_ercot.json"

BUNDLES = {
    "t1h-refresh (registered)": "results/hindcast/ercot-2021-2025-realized-t1h-refresh/ERCOT/28cef3500ec1fd9e",
    "t1h-control": "results/hindcast/ercot-2021-2025-realized-t1h-control/ERCOT/28cef3500ec1fd9e",
    "t1h-disarm": "results/hindcast/ercot-2021-2025-realized-t1h-disarm/ERCOT/2eab21467a4214c7",
    "t1h-d11r-control": "results/hindcast/ercot-2021-2025-realized-t1h-d11r-control/ERCOT/28cef3500ec1fd9e",
    "t1h-d11r-exhaustion": "results/hindcast/ercot-2021-2025-realized-t1h-d11r-exhaustion/ERCOT/cc7bbe1170db65c2",
    "caiso-2021-2025-realized": "results/hindcast/caiso-2021-2025-realized/CAISO/408f9199a82f5814",
}

# Keeper backcast bundle whose committed zonal hourly duals the L-1 replay used
# as its dual stand-in (the T1-H runs commit no hourly prices of their own).
KEEPER_HOURLY = REPO / "results/calibration/ercot223_release_arm/hourly"

STORAGE_PY = REPO / "src/market_sim/model/storage.py"
NEW_ENTRY_PY = REPO / "src/market_sim/model/capacity_evolution/new_entry.py"
SCENARIOS_PY = REPO / "src/market_sim/config/scenarios.py"
CAPMKT_PY = REPO / "src/market_sim/config/capacity_market.py"

# capex_per_kw / fom_per_kw_yr as shipped in
# config/capacity_market.py::STORAGE_TECHS (read live below; these are the
# expected values, asserted so a constants drift is loud rather than silent).
EXPECTED_CAPEX_PER_KW = {
    "li_ion_4hr": 1810.3,
    "li_ion_8hr": 3154.3,
    "iron_air": 2000.0,
    "li_ion_12hr": 4498.4,
    "flow_battery": 4700.0,
    "compressed_air": 2700.0,
}

# EIA-860 storage-technology code → the STORAGE_TECHS entries it covers.
# Codes are EIA-860 Schedule 3 "Storage Technology" values.
EIA_TECH_CLASS = {
    "LIB": "lithium-ion (li_ion_4hr / li_ion_8hr / li_ion_12hr)",
    "FLB": "flow battery (flow_battery)",
    "MAB": "metal-air (iron_air)",
    "NIB": "nickel-based",
    "NAB": "sodium-based",
    "PBB": "lead-acid",
    "ECC": "electro-chemical capacitor",
    "OTH": "other",
}


def _load(path: Path) -> Any:
    with path.open() as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Section 0 — dedup + stop rule
# ---------------------------------------------------------------------------
def section_dedup() -> dict[str, Any]:
    """Verify D11-R's claim on D-1 and run the charter's stop rule on D-2/D-3.

    Returns a dict of measured booleans/citations, never a judgement.
    """
    out: dict[str, Any] = {}

    scen = SCENARIOS_PY.read_text()
    out["entry_margin_exhaustion_registered"] = (
        "entry_margin_exhaustion: bool = False" in scen
    )
    out["entry_margin_exhaustion_default"] = "False (GATED default-OFF)"

    # The two D11-R arms are registered bundles on disk.
    for name in ("t1h-d11r-control", "t1h-d11r-exhaustion"):
        out[f"bundle::{name}"] = (REPO / BUNDLES[name] / "score.json").exists()

    st = STORAGE_PY.read_text()
    ne = NEW_ENTRY_PY.read_text()

    # D-1 (bang-bang volume): claimed by D11-R. Both allocators keep a
    # bang-bang path that is REPLACED (not stacked) when the flag is armed.
    out["d1_bangbang_storage_path_present"] = bool(
        re.search(r"build_mw = min\(remaining, per_tech_cap\)", st)
    )
    out["d1_walk_storage_path_present"] = "if entry_reprice is not None:" in st
    out["d1_walk_thermal_path_present"] = "entry_reprice" in ne

    # D-2 (no storage availability-year gate) — STOP RULE.
    out["d2_storage_availability_gate_present"] = bool(
        re.search(r"_STORAGE_AVAILABLE_YEAR|available_year", st)
    )
    out["d2_bangbang_iterates_all_techs"] = bool(
        re.search(r"for tech_name, tech in STORAGE_TECHS\.items\(\):", st)
    )
    out["d2_walk_iterates_all_techs"] = st.count(
        "for tech_name, tech in STORAGE_TECHS.items():"
    )
    out["d2_thermal_gate_present"] = "_EMERGING_AVAILABLE_YEAR" in ne

    # D-3 (absolute $/MW-yr ranking) — STOP RULE.
    out["d3_absolute_margin_sort_present"] = bool(
        re.search(r"margins\.sort\(key=lambda m: m\[0\], reverse=True\)", st)
    )
    out["d3_walk_absolute_margin_pick_present"] = bool(
        re.search(r"if m > best_margin:", st)
    )
    out["d3_share_cap_uncited"] = "Source: modeling assumption" in CAPMKT_PY.read_text()

    out["verdict"] = {
        "D-1": "CLAIMED by capx D11-R (entry_margin_exhaustion, both allocators)",
        "D-2": (
            "NOT touched by D11-R — no availability-year gate at HEAD on either "
            "the bang-bang path or the D11-R walk; the walk INHERITS the defect"
        ),
        "D-3": (
            "NOT closed by D11-R — both the bang-bang sort and the walk's "
            "per-tranche pick rank on ABSOLUTE $/MW-yr; D11-R re-evaluates the "
            "ranking more often, it does not change the ranking OBJECT"
        ),
    }
    return out


# ---------------------------------------------------------------------------
# Section 1 — D-2 census
# ---------------------------------------------------------------------------
def _model_storage_census() -> dict[str, dict[str, dict[str, float]]]:
    """Per-arm, per-decision-year storage build (MW) from committed artifacts."""
    census: dict[str, dict[str, dict[str, float]]] = {}
    dis = _load(DISARM_LEDGER)["ledger"]
    census["t1h-control / t1h-refresh (registered)"] = {
        y: v["storage_decided_mw_by_tech"] for y, v in dis["control"].items()
    }
    census["t1h-disarm (entry_lookahead_reprice=False)"] = {
        y: v["storage_decided_mw_by_tech"] for y, v in dis["disarm"].items()
    }
    ab = _load(D11R_AB)["steps"]
    census["t1h-d11r-exhaustion (entry_margin_exhaustion=True)"] = {
        y: v["storage_decided_mw_by_tech"] for y, v in ab["arm"].items()
    }
    census["caiso-2021-2025-realized"] = {
        "all years": {"(none — model_gw 0.0 vs actual 15.147)": 0.0}
    }
    return census


def _eia860_storage_evidence() -> dict[str, Any]:
    """Measured deployment record per storage-technology class (EIA-860 2025 ER).

    Returns first US operating year, national operable MW, ERCOT operable MW,
    and the ERCOT 2023-2025 vintage duration distribution. This is the
    *measured* object against which the model's built technologies are compared;
    it is diagnostic evidence for the census, NOT a model input (rule 13
    ``[R-MEASURED]`` is not engaged — nothing here feeds a solve).
    """
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover - probe convenience
        return {"unavailable": "pandas not importable"}

    base = REPO / "data/raw/eia-860"
    op = base / "eia860_energy_storage_operable.parquet"
    prop = base / "eia860_energy_storage_proposed.parquet"
    plant = base / "eia860_plant.parquet"
    gen = base / "eia860_generator_operable.parquet"
    missing = [str(p.relative_to(REPO)) for p in (op, prop, plant, gen) if not p.exists()]
    if missing:
        return {"unavailable": f"not hydrated: {missing} (data profile 'ercot')"}

    d = pd.read_parquet(op)
    p = pd.read_parquet(plant)[["Plant Code", "Balancing Authority Code"]]
    d["mw"] = pd.to_numeric(d["Nameplate Capacity (MW)"], errors="coerce")
    d["mwh"] = pd.to_numeric(d["Nameplate Energy Capacity (MWh)"], errors="coerce")
    nat = (
        d.groupby("Storage Technology 1")
        .agg(first_operating_year=("Operating Year", "min"), national_mw=("mw", "sum"),
             n_units=("mw", "size"))
        .sort_values("national_mw", ascending=False)
    )

    m = d.merge(p, on="Plant Code", how="left")
    erco = m[m["Balancing Authority Code"] == "ERCO"].copy()
    erco_by_tech = erco.groupby("Storage Technology 1")["mw"].sum()

    vint = erco[erco["Operating Year"].between(2023, 2025)].copy()
    vint["dur"] = vint["mwh"] / vint["mw"]
    bins = [0, 1.5, 2.5, 4.5, 8.5, 1e6]
    dur_hist = vint.groupby(
        pd.cut(vint["dur"], bins), observed=False
    )["mw"].sum().round(1)

    q = pd.read_parquet(prop).merge(p, on="Plant Code", how="left")
    q = q[q["Balancing Authority Code"] == "ERCO"]
    q["mw"] = pd.to_numeric(q["Nameplate Capacity (MW)"], errors="coerce")
    erco_proposed = q.groupby("Storage Technology 1")["mw"].sum()

    g = pd.read_parquet(gen)
    caes = g[g["Prime Mover"] == "CE"][
        ["Plant Name", "State", "Nameplate Capacity (MW)", "Operating Year"]
    ]

    return {
        "source": (
            "data/raw/eia-860/eia860_energy_storage_{operable,proposed}.parquet "
            "+ eia860_plant.parquet (BA code ERCO) + eia860_generator_operable.parquet "
            "(Prime Mover 'CE' = CAES); EIA-860 2025 Early Release"
        ),
        "national_operable_by_tech": {
            k: {
                "class": EIA_TECH_CLASS.get(k, k),
                "first_operating_year": None
                if np.isnan(v["first_operating_year"])
                else int(v["first_operating_year"]),
                "national_mw": round(float(v["national_mw"]), 1),
                "n_units": int(v["n_units"]),
            }
            for k, v in nat.to_dict("index").items()
        },
        "ercot_operable_by_tech_mw": {
            k: round(float(v), 1) for k, v in erco_by_tech.items()
        },
        "ercot_proposed_by_tech_mw": {
            k: round(float(v), 1) for k, v in erco_proposed.items()
        },
        "ercot_2023_2025_vintage": {
            "mw": round(float(vint["mw"].sum()), 1),
            "mwh": round(float(vint["mwh"].sum()), 1),
            "cap_weighted_duration_hr": round(
                float(vint["mwh"].sum() / vint["mw"].sum()), 2
            ),
            "max_duration_hr": round(float(vint["dur"].max()), 2),
            "mw_at_duration_ge_8p5h": round(
                float(vint.loc[vint["dur"] >= 8.5, "mw"].sum()), 1
            ),
            "duration_histogram_mw": {str(k): float(v) for k, v in dur_hist.items()},
        },
        "us_caes_operable": caes.to_dict("records"),
    }


def _model_duration_mix(census: dict[str, dict[str, dict[str, float]]]) -> dict[str, Any]:
    """Capacity-weighted duration (h) of each arm's whole storage build.

    The single number that makes the anachronism commensurable with the
    measured record: STORAGE_TECHS' own ``duration_hr`` weighted by the MW the
    screen decided, against EIA-860's measured ERCOT 2023-2025 vintage.
    """
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.capacity_market import STORAGE_TECHS  # noqa: PLC0415

    out: dict[str, Any] = {}
    for arm, years in census.items():
        mw = 0.0
        mwh = 0.0
        by_tech: dict[str, float] = {}
        for builds in years.values():
            for tech, m in builds.items():
                if tech not in STORAGE_TECHS:
                    continue
                mw += m
                mwh += m * float(STORAGE_TECHS[tech]["duration_hr"])
                by_tech[tech] = by_tech.get(tech, 0.0) + m
        out[arm] = {
            "total_mw": round(mw, 1),
            "total_mwh": round(mwh, 1),
            "cap_weighted_duration_hr": None if mw <= 0 else round(mwh / mw, 2),
            "by_tech_mw": {k: round(v, 1) for k, v in by_tech.items()},
        }
    return out


def section_d2() -> dict[str, Any]:
    census = _model_storage_census()
    return {
        "model_builds": census,
        "model_duration_mix": _model_duration_mix(census),
        "measured_deployment": _eia860_storage_evidence(),
        "repo_availability_year_citations": {
            "storage": (
                "NONE. No _STORAGE_AVAILABLE_YEAR mapping, no ScenarioConfig "
                "*_available_year field and no parameter-citations.md row gives a "
                "commercial-availability year for ANY storage technology. This "
                "probe does NOT invent one (charter: 'where no citation exists, "
                "say so')."
            ),
            "thermal (for contrast)": (
                "h2_available_year=2035, ccs_available_year=2030, "
                "egs_available_year=2030, offshore_wind_available_year=2030, "
                "smr_available_year=None — scenarios.py:2463-2472, consumed by "
                "new_entry._EMERGING_AVAILABLE_YEAR (new_entry.py:184, :258-263)"
            ),
        },
        "repo_internal_inconsistency": (
            "capacity_market.py:552 STORAGE_TECH_POWER_SHARE = {li_ion_4hr 0.70, "
            "li_ion_8hr 0.25, iron_air 0.05} — the model's OWN fleet-composition "
            "constant assigns flow_battery, compressed_air and li_ion_12hr a 0 % "
            "share, while the entry screen builds flow_battery at 2,000 MW."
        ),
    }


# ---------------------------------------------------------------------------
# Section 2 — D-3 replay
# ---------------------------------------------------------------------------
def _capex_table() -> dict[str, float]:
    """capex_per_kw as shipped, read live from capacity_market.STORAGE_TECHS."""
    import sys

    sys.path.insert(0, str(REPO / "src"))
    from market_sim.config.capacity_market import STORAGE_TECHS  # noqa: PLC0415

    tbl = {k: float(v["capex_per_kw"]) for k, v in STORAGE_TECHS.items()}
    drift = {k: (tbl[k], EXPECTED_CAPEX_PER_KW[k]) for k in tbl
             if abs(tbl[k] - EXPECTED_CAPEX_PER_KW.get(k, -1)) > 1e-9}
    if drift:
        raise SystemExit(f"STORAGE_TECHS capex drift vs the finding's basis: {drift}")
    return tbl


def _allocate(ranked: list[str], budget: float, per_tech_cap: float
              ) -> list[dict[str, float | str]]:
    """The committed bang-bang allocator (storage.py, the ``margins`` block).

    ``for seq, (_, tech_name) in enumerate(margins): build_mw = min(remaining,
    per_tech_cap)`` — a fixed VOLUME share to each clearing tech in rank order
    until the budget is gone. Reproduced verbatim so the counterfactual differs
    from the shipped result in the RANKING ONLY.
    """
    out: list[dict[str, float | str]] = []
    remaining = budget
    for tech in ranked:
        if remaining <= 0.0:
            break
        build = min(remaining, per_tech_cap)
        remaining -= build
        out.append({"tech": tech, "build_mw": round(build, 1)})
    return out


def section_d3() -> dict[str, Any]:
    art = _load(PHASE0_ERCOT)
    capex = _capex_table()
    res: dict[str, Any] = {
        "source_margins": str(PHASE0_ERCOT.relative_to(REPO)),
        "allocator": "model/storage.py — margins.sort(reverse=True) + min(remaining, per_tech_cap)",
        "capex_source": "config/capacity_market.py::STORAGE_TECHS[*]['capex_per_kw']",
        "capex_per_kw": capex,
        "years": {},
    }

    for year, blk in art["decision_years"].items():
        ss = blk["storage_screen"]
        budget = float(ss["budget_mw"])
        cap = float(ss["per_tech_cap_mw"])
        margins = {t["tech"]: float(t["margin_per_mw_yr"]) for t in ss["techs"]}
        cost = {t["tech"]: float(t["annual_cost_per_mw_yr"]) for t in ss["techs"]}
        clearing = [t for t, m in margins.items() if m > 0.0]

        shipped_rank = sorted(clearing, key=lambda t: margins[t], reverse=True)
        shipped_alloc = _allocate(shipped_rank, budget, cap)

        # --- the counterfactual metric: margin per unit CAPITAL cost ---------
        # $/MW-yr of margin per $/kW of installed capital. Scale-free in the
        # units (any positive rescale of capex leaves the ORDER unchanged), so
        # it is the developer's ranking object with no free parameter.
        per_capex = {t: margins[t] / capex[t] for t in clearing}
        cf_rank = sorted(clearing, key=lambda t: per_capex[t], reverse=True)
        cf_alloc = _allocate(cf_rank, budget, cap)

        # --- sensitivity: margin per ANNUALIZED cost (profitability index) ---
        per_annual = {t: margins[t] / cost[t] for t in clearing}
        pi_rank = sorted(clearing, key=lambda t: per_annual[t], reverse=True)
        pi_alloc = _allocate(pi_rank, budget, cap)

        # --- joint D-2 + D-3: pool restricted to lithium-ion ------------------
        # Two pools, because the answer depends on which one a D-2 gate admits:
        #   "all li-ion"  = {4hr, 8hr, 12hr} — every li_ion_* entry in STORAGE_TECHS
        #   "deployed li-ion" = {4hr, 8hr}   — the durations STORAGE_TECH_POWER_SHARE
        #        actually carries, and the pool the parent finding's §2 L-3
        #        arithmetic used (this probe reproduces its result on that pool).
        li_all = [t for t in clearing if "li_ion" in t]
        li_dep = [t for t in clearing if t in ("li_ion_4hr", "li_ion_8hr")]
        li_abs = _allocate(sorted(li_all, key=lambda t: margins[t], reverse=True), budget, cap)
        li_cf = _allocate(sorted(li_all, key=lambda t: per_capex[t], reverse=True), budget, cap)
        li_dep_abs = _allocate(
            sorted(li_dep, key=lambda t: margins[t], reverse=True), budget, cap
        )
        li_dep_cf = _allocate(
            sorted(li_dep, key=lambda t: per_capex[t], reverse=True), budget, cap
        )

        res["years"][year] = {
            "budget_mw": budget,
            "per_tech_cap_mw": cap,
            "n_clearing": len(clearing),
            "margin_per_mw_yr": margins,
            "margin_per_dollar_kw": {t: round(v, 2) for t, v in per_capex.items()},
            "margin_per_annual_cost": {t: round(v, 3) for t, v in per_annual.items()},
            "shipped_rank_absolute": shipped_rank,
            "shipped_allocation": shipped_alloc,
            "shipped_matches_committed_ledger": shipped_alloc == [
                {"tech": r["tech"], "build_mw": float(r["build_mw"])}
                for r in ss["allocator_result"]
            ],
            "counterfactual_rank_per_capex": cf_rank,
            "counterfactual_allocation_per_capex": cf_alloc,
            "sensitivity_rank_per_annual_cost": pi_rank,
            "sensitivity_allocation_per_annual_cost": pi_alloc,
            "d2_li_ion_all_durations_absolute": li_abs,
            "d2_plus_d3_li_ion_all_durations_per_capex": li_cf,
            "d2_li_ion_deployed_durations_absolute": li_dep_abs,
            "d2_plus_d3_li_ion_deployed_durations_per_capex": li_dep_cf,
        }
    return res


# ---------------------------------------------------------------------------
# Section 3 — Leg B wind measurement
# ---------------------------------------------------------------------------
def section_legb() -> dict[str, Any]:
    l1 = _load(L1_DUAL_ERCOT)
    res: dict[str, Any] = {
        "a_dual_signal_object": {},
        "b_zonal_variant": {},
        "computability": {},
    }

    # --- (a) the dual-based signal object, measured END-TO-END ---------------
    # The disarm run IS the dual-based signal object, solved. Its additions are
    # committed; its own screen signal is NOT (a disarmed run emits no
    # screen_signal_diag npz — the C-1 caveat, verified below).
    dumps = {
        name: len(list((REPO / path).glob("screen_signal_diag_*.npz")))
        for name, path in BUNDLES.items()
    }
    res["a_dual_signal_object"]["screen_signal_diag_npz_count"] = dumps
    res["a_dual_signal_object"]["c1_caveat_verified"] = dumps["t1h-disarm"] == 0

    for name in ("t1h-refresh (registered)", "t1h-disarm", "t1h-d11r-exhaustion"):
        sc = REPO / BUNDLES[name] / "score.json"
        if not sc.exists():
            continue
        by = _load(sc)["additions"]["by_tech"]
        res["a_dual_signal_object"].setdefault("wind_additions_gw", {})[name] = {
            "actual_gw": by["wind"]["actual_gw"],
            "model_gw": by["wind"]["model_gw"],
            "err_frac": by["wind"]["err_frac"],
            "band": by["wind"]["band"],
        }
    w = res["a_dual_signal_object"]["wind_additions_gw"]
    base = w["t1h-refresh (registered)"]
    gap0 = base["actual_gw"] - base["model_gw"]
    for name, row in w.items():
        row["gap_gw"] = round(base["actual_gw"] - row["model_gw"], 3)
        row["gap_closed_frac_vs_registered"] = round(
            (row["model_gw"] - base["model_gw"]) / gap0, 4
        )

    # --- (b) the zonal variant: LEVEL vs ZONAL decomposition -----------------
    # The L-1 replay records, per step, the wind capture ratio under three
    # constructions: the shipped zone-flat signal, the dual arm's SYSTEM row
    # (load-flat average of the zonal duals) and the dual arm's BUILD-ZONE row.
    # shipped -> system  = the LEVEL leg (signal construction)
    # system  -> zone_row= the ZONAL leg (locational resolution)
    for step, blk in l1["steps"].items():
        arms = blk["arms"]
        shipped = arms["shipped_signal"]["vre"]["wind"]
        dual_key = next(
            (k for k in ("dual_prior_solve", "dual_same_year")
             if k in arms and "vre" in arms[k]),
            None,
        )
        if dual_key is None:
            res["b_zonal_variant"][step] = {
                "blocked": arms.get("dual_prior_solve", {}).get("blocked", "no dual arm")
            }
            continue
        dual = arms[dual_key]["vre"]["wind"]
        shipped_r = float(shipped["capture_ratio_system"])
        sys_r = float(dual["capture_ratio_system"])
        zone_r = float(dual["capture_ratio_zone_row"])
        total = zone_r - shipped_r
        res["b_zonal_variant"][step] = {
            "dual_arm": dual_key,
            "diagnostic_only": dual_key == "dual_same_year",
            "build_zone": dual["build_zone"],
            "capture_ratio_shipped": shipped_r,
            "capture_ratio_dual_system": sys_r,
            "capture_ratio_dual_zone_row": zone_r,
            "level_leg": round(sys_r - shipped_r, 4),
            "zonal_leg": round(zone_r - sys_r, 4),
            "zonal_share_of_repair": None if abs(total) < 1e-9
            else round((zone_r - sys_r) / total, 4),
            "wind_margin_per_mwh_shipped": shipped["margin_per_mwh"],
            "wind_margin_per_mwh_dual_zone_row": dual["margin_per_mwh"],
            "wind_clears_on_merit_at_zone_row": dual["sign"] == "+",
            "shipped_zone_flat_verified": (
                abs(float(shipped["capture_ratio_system"])
                    - float(shipped["capture_ratio_zone_row"])) < 1e-9
            ),
        }

    # --- (b') per-zone capture, re-measured independently --------------------
    # Reproduces the L-1 zone rows from first principles on committed inputs:
    # the keeper's committed zonal hourly duals x the T1-H dump's own hourly
    # wind potential. Reported for EVERY zone, because WHICH zone the screen
    # resolves to is itself a modelling choice (RENEWABLE_ZONE_ALLOCATION
    # sends all ERCOT wind to "West").
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover
        res["b_zonal_variant"]["per_zone"] = {"unavailable": "pandas not importable"}
        return res

    per_zone: dict[str, Any] = {}
    for dump_name, dual_year in (
        ("screen_signal_diag_2023_for_2024.npz", 2023),
        ("screen_signal_diag_2024_for_2025.npz", 2024),
    ):
        dump = REPO / BUNDLES["t1h-refresh (registered)"] / dump_name
        hourly = KEEPER_HOURLY / f"system_{dual_year}.parquet"
        if not (dump.exists() and hourly.exists()):
            per_zone[dump_name] = {"unavailable": "dump or keeper hourly missing"}
            continue
        z = np.load(dump, allow_pickle=True)
        wind = np.asarray(z["wind_potential_mw"], dtype=float)
        solar = np.asarray(z["solar_potential_mw"], dtype=float)
        df = pd.read_parquet(hourly)
        rows: dict[str, Any] = {}
        for zone in sorted(df["zone"].unique()):
            p = df[df["zone"] == zone].sort_values("hour")["price"].to_numpy(float)
            if p.size != wind.size:
                rows[zone] = {"unavailable": f"hour count {p.size} != {wind.size}"}
                continue
            rows[zone] = {
                "zone_mean_price": round(float(p.mean()), 3),
                "wind_capture_price": round(float((p * wind).sum() / wind.sum()), 3),
                "wind_capture_ratio_vs_own_zone_mean": round(
                    float((p * wind).sum() / wind.sum() / p.mean()), 4
                ),
                "solar_capture_ratio_vs_own_zone_mean": round(
                    float((p * solar).sum() / solar.sum() / p.mean()), 4
                ),
            }
        sysp = df.groupby("hour")["price"].mean().to_numpy(float)
        rows["_system_unweighted_mean"] = {
            "zone_mean_price": round(float(sysp.mean()), 3),
            "wind_capture_price": round(float((sysp * wind).sum() / wind.sum()), 3),
            "wind_capture_ratio_vs_own_zone_mean": round(
                float((sysp * wind).sum() / wind.sum() / sysp.mean()), 4
            ),
        }
        per_zone[f"{dump_name} x keeper duals {dual_year}"] = rows
    res["b_zonal_variant"]["per_zone"] = per_zone
    res["b_zonal_variant"]["build_zone_note"] = (
        "data/renewables.py:219 RENEWABLE_ZONE_ALLOCATION['ERCOT'] sends BOTH "
        "wind and solar to 'West'; Panhandle — the most wind-rich zone — is "
        "never a build zone, so its capture ratio never reaches the screen."
    )

    res["computability"] = {
        "(a) end-to-end entry-volume effect of the dual signal": "MEASURED (disarm bundle, committed score.json)",
        "(a) the disarm run's own screen signal": (
            "NOT COMPUTABLE zero-solve — a disarmed run emits 0 screen_signal_diag "
            "npz (verified above); the C-1 recorded caveat holds"
        ),
        "(b) zonal capture-ratio effect": (
            "MEASURED, on a STAND-IN — the keeper backcast's committed zonal duals, "
            "not the T1-H run's own; the L-1 finding §1.1 already declared this bound "
            "and the disarm sized it as material for gas, immaterial for storage"
        ),
        "(b) zonal entry-VOLUME effect (GW of wind)": (
            "NOT COMPUTABLE zero-solve — the screen's build volume is set jointly by "
            "the shared queue budget, the solar/wind competition and (armed) the "
            "exhaustion walk; no committed artifact carries a zonally-resolved entry "
            "decision. Recorded as a measured limitation, NOT estimated."
        ),
    }
    return res


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--section",
        choices=["dedup", "d2", "d3", "legb", "all"],
        default="all",
    )
    ap.add_argument("--out", type=Path, help="optional JSON output path")
    args = ap.parse_args()

    runners = {
        "dedup": section_dedup,
        "d2": section_d2,
        "d3": section_d3,
        "legb": section_legb,
    }
    want = list(runners) if args.section == "all" else [args.section]
    report = {name: runners[name]() for name in want}
    report["_provenance"] = {
        "probe": "scripts/probes/_t1h_capentry_phase0.py",
        "charter": "docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md",
        "finding": "docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md",
        "solves_run": 0,
    }

    text = json.dumps(report, indent=1, default=str)
    print(text)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)


if __name__ == "__main__":
    main()

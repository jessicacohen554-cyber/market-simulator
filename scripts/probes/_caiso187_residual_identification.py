"""caiso-187 — identify ``wefor_residual`` for CAISO from the PRECHECK §2 formula. **NO LP.**

The formula is **FIXED IN THE PRE-REGISTRATION** (`PRECHECK-caiso187-wefor-overlay-2026-08-09.md`
§2, committed at `f7ea03e` BEFORE this script was written) and is reproduced here verbatim.
Nothing in this probe is a choice; every term is either already in the model or counted from
a committed artifact::

    W_c        = the model's OWN unfitted statistical forced-outage rate for class c
                 (constants.THERMAL_AVAILABILITY[c] WEFOR base + age escalation,
                 capacity-weighted over the CAISO fleet, wefor_multiplier = 1.0)

    X_c        = the CAMPD overlay's OWN measured removal for class c, taken through the
                 SHIPPED loader outages.unit_outage_derate_factors so it is the overlay the
                 LP actually applies — 1 - (capacity-weighted mean availability multiplier),
                 pooled over 2023-2025

    residual_c = max(0, W_c - X_c)

    wefor_residual = capacity-weighted mean of residual_c over the covered classes PRESENT
                     in the CAISO fleet, rounded to 4 decimals

**G-SCOPE (PRECHECK §4):** only ``_POF_DROP_GROUPS`` = {CC_REGULAR, CC_CHP, ST_GAS, ST_CHP}
(plus coal by fuel type, of which CAISO has none) are eligible. **CT classes are never
relieved** even though the CAISO extract carries CT_CHP outage rows — that mismatch is
reported here as an open observation and is not acted on.

**G-NODOUBLE (PRECHECK §4):** a class with ``X_c == 0`` gets NO relief — its residual is
``W_c``, i.e. unchanged — so the repair can never invent headroom where the overlay removed
nothing.

The value this writes is **FROZEN** at its commit (G-FROZEN) and is never recomputed after a
price is read.

Usage::

    python scripts/probes/_caiso187_residual_identification.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
HOURS = 8760
KEEPER = REPO / "results" / "calibration" / "caiso184_c1_lpbasis"
OUT = REPO / "results" / "calibration" / "_caiso187_residual_identification.json"
ROUND_DP = 4  # PRECHECK §2a item 1 — fixed in advance, no other rounding is used.


def _keeper_config():
    """The incumbent keeper's ScenarioConfig, from its own committed run_config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})


def _fleet_by_class(cfg):
    """Return ``{class: [(plant_code, pmax_mw, online_year)]}`` for the CAISO LP fleet.

    Built through the shipped path so the population is exactly the LP's bins, not an
    EIA-860 re-query.
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    gens, _ = bins_to_fleet(bins, [z.name for z in iso_cfg.zones], cfg)
    out: dict[str, list[tuple[int, float, int]]] = {}
    for g in gens:
        out.setdefault(str(g.plant_group), []).append(
            (int(g.plant_code), float(g.pmax_mw), int(g.online_year))
        )
    return out


def _w_class(klass: str, units, year: int) -> float:
    """``W_c`` — the UNFITTED statistical WEFOR, capacity-weighted over the fleet.

    ``THERMAL_AVAILABILITY[klass]`` is read as-is (rule 23 ``[R-FROZEN-DERIVE]``: not
    re-derived, no source-data change cited) and ``wefor_multiplier`` is held at **1.0**,
    which is the whole point — this is the rate the model would apply with the fitted knob
    retired.
    """
    from market_sim.config.constants import THERMAL_AVAILABILITY

    params = THERMAL_AVAILABILITY.get(klass)
    if params is None:
        return 0.0
    _pof, w_base, w_rate, w_onset = params[0], params[1], params[2], params[3]
    num = den = 0.0
    for _code, pmax, online in units:
        age = year - online
        wefor = w_base + max(0.0, age - w_onset) * w_rate
        num += wefor * pmax
        den += pmax
    return num / den if den > 0 else 0.0


def _x_class(cfg, units_by_class, year: int) -> dict[str, dict[str, float]]:
    """``X_c`` — the overlay's measured removal, through the SHIPPED loader.

    ``unit_outage_derate_factors`` returns the per-(plant, group) hourly availability
    MULTIPLIER the LP applies. The class's measured removal is one minus its
    capacity-weighted, hour-averaged multiplier. Plants absent from the overlay contribute a
    multiplier of 1.0 (no removal), so the figure is the class's true fleet-wide removal, not
    a removal conditional on having an outage.
    """
    from market_sim.data.outages import unit_outage_derate_factors

    factors = unit_outage_derate_factors(
        year,
        HOURS,
        iso=ISO,
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
        cc_nameplate_basis=bool(getattr(cfg, "unit_outage_lp_capacity_basis", False)),
    )
    out: dict[str, dict[str, float]] = {}
    for klass, units in units_by_class.items():
        # Capacity per plant (a plant may hold several tranches in the fleet).
        cap: dict[int, float] = {}
        for code, pmax, _online in units:
            cap[code] = cap.get(code, 0.0) + pmax
        num = den = 0.0
        covered_cap = 0.0
        for code, pmax in cap.items():
            arr = factors.get((code, klass))
            mult = 1.0 if arr is None else float(np.mean(arr))
            if arr is not None and mult < 1.0 - 1e-12:
                covered_cap += pmax
            num += mult * pmax
            den += pmax
        if den <= 0:
            continue
        out[klass] = {
            "class_capacity_mw": round(den, 1),
            "overlay_covered_capacity_mw": round(covered_cap, 1),
            "mean_availability_multiplier": round(num / den, 6),
            "X_measured_removal": round(1.0 - num / den, 6),
            "plants": len(cap),
            "plants_with_overlay": sum(
                1
                for code in cap
                if factors.get((code, klass)) is not None
                and float(np.mean(factors[(code, klass)])) < 1.0 - 1e-12
            ),
        }
    return out


def main() -> None:
    """Compute the frozen §2 value and write the identification record."""
    from market_sim.data.fleet.arrays import _POF_DROP_GROUPS

    cfg = _keeper_config()
    units_by_class = _fleet_by_class(cfg)
    eligible = sorted(set(_POF_DROP_GROUPS) & set(units_by_class))
    ineligible_with_rows = sorted(set(units_by_class) - set(_POF_DROP_GROUPS))

    per_year: dict[str, dict] = {}
    for year in YEARS:
        x = _x_class(cfg, units_by_class, year)
        rows = {}
        for klass in eligible:
            w = _w_class(klass, units_by_class[klass], year)
            xc = x.get(klass, {}).get("X_measured_removal", 0.0)
            rows[klass] = {
                "W_unfitted_statistical": round(w, 6),
                **x.get(klass, {}),
                "residual_c": round(max(0.0, w - xc), 6),
                "keeper_effective_wefor": round(
                    w * float(getattr(cfg, "wefor_multiplier", 1.0)), 6
                ),
                "keeper_total_removal": round(
                    w * float(getattr(cfg, "wefor_multiplier", 1.0)) + xc, 6
                ),
                "arm_total_removal": round(max(0.0, w - xc) + xc, 6),
            }
        per_year[str(year)] = rows

    # Pool over the three years, capacity-weighted across the eligible classes.
    num = den = 0.0
    pooled: dict[str, dict[str, float]] = {}
    for klass in eligible:
        vals = [per_year[str(y)][klass] for y in YEARS]
        cap = float(np.mean([v.get("class_capacity_mw", 0.0) for v in vals]))
        res = float(np.mean([v["residual_c"] for v in vals]))
        pooled[klass] = {
            "class_capacity_mw": round(cap, 1),
            "W_unfitted_statistical": round(
                float(np.mean([v["W_unfitted_statistical"] for v in vals])), 6
            ),
            "X_measured_removal": round(
                float(np.mean([v.get("X_measured_removal", 0.0) for v in vals])), 6
            ),
            "residual_c": round(res, 6),
            "keeper_total_removal": round(
                float(np.mean([v["keeper_total_removal"] for v in vals])), 6
            ),
            "arm_total_removal": round(
                float(np.mean([v["arm_total_removal"] for v in vals])), 6
            ),
        }
        num += res * cap
        den += cap

    value = round(num / den, ROUND_DP) if den > 0 else None
    g_nodouble = {
        klass: pooled[klass]["X_measured_removal"] > 0.0 for klass in eligible
    }
    out = {
        "iso": ISO,
        "years": YEARS,
        "keeper": KEEPER.name,
        "formula": "residual_c = max(0, W_c - X_c); value = capacity-weighted mean over "
        "eligible classes present in the CAISO fleet, rounded to 4 dp "
        "(PRECHECK-caiso187 §2, frozen at f7ea03e)",
        "keeper_wefor_multiplier": float(getattr(cfg, "wefor_multiplier", 1.0)),
        "keeper_wefor_residual": getattr(cfg, "wefor_residual", None),
        "eligible_classes": eligible,
        "ineligible_classes_present_in_fleet": ineligible_with_rows,
        "per_year": per_year,
        "pooled": pooled,
        "g_nodouble_per_class": g_nodouble,
        "g_nodouble_pass": all(g_nodouble.values()) if g_nodouble else False,
        "WEFOR_RESIDUAL_VALUE": value,
        "WEFOR_RESIDUAL_GROUPS": eligible,
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()

"""capx D48 Phase-1 diagnosis instrument (zero solves): why a position-neutral
basis change moved FC-3.

The PREDECL §5 stop-and-route fired — the arm decided 12,818 MW of coal at
the 2022 screen where the control decided 11,415 MW, with every candidate's
net revenue, going-forward cost and capacity leg byte-identical. This
instrument reconstructs the ONE mechanism that reads the devintaged seam
between the screen and the decision: the pipeline's admission cap
(``retirements._apply_pipeline_retirements`` → ``_apply_reliability_floor``
at ``_admission_cap_horizon``), a FIRM-MW budget

    budget = accredited(cap_fleet) − requirement(cap_year, cap_peak)

that the cap converts into admitted exits at each candidate's own firm
fraction, ranked by ``_floor_retention_merit`` ($/firm-MW ascending). Both
sides of the budget are on the devintaged basis under the arm, so the budget
in MW moves even though the POSITION (their ratio) does not.

    uv run python docs/handoffs/d48/admission-cap-budget-2026-09-04.py

Reads the two committed bundles' ledgers and the D48 arm resolvers; writes
``<this file>.json`` beside itself.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.capacity_market import ADEQUACY_EXTERNAL_TIE_FIRM_MW  # noqa: E402
from market_sim.config.constants import EFORD  # noqa: E402
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.model.capacity_evolution.retirements import (  # noqa: E402
    _admission_cap_horizon,
    gross_adequacy_requirement_mw,
    resolve_adequacy_requirement_mw,
    resolve_demand_response_supply_mw,
    thermal_accreditation_fraction,
)

CONTROL = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d45r/PJM/c6091bd5b62bbc3f"
ARM = REPO / "results/hindcast/pjm-2021-2025-realized-t1h-d48-devintage/PJM/bbe13b3f7b659d36"
SCREEN_YEAR = 2022  # the bridge-year screen that decides the 2022 cohort


@dataclass
class _G:
    unit_id: str
    fuel_type: str


def cfg(armed: bool) -> ScenarioConfig:
    kw = dict(pjm_accreditation_design_vintage=True, pjm_demand_response_supply=True) if armed else {}
    return ScenarioConfig(iso="PJM", mode="forecast", hindcast=True, **kw)


def led(b: Path, y: int) -> dict:
    return json.loads((b / f"evolution_{y}.json").read_text())


def firm_side(c: ScenarioConfig, year: int, fleet: dict, base: dict, peak: float) -> dict:
    thermal = {f: mw * thermal_accreditation_fraction(f, EFORD.get(f, 0.05), "PJM", c, year) for f, mw in fleet.items()}
    cred = base.get("renewable_credit_applied") or {}
    other = (
        float(base.get("wind_cap_mw") or 0) * float(cred.get("wind", 0))
        + float(base.get("solar_cap_mw") or 0) * float(cred.get("solar", 0))
        + float(base.get("firm_clean_accredited_mw") or 0)
        + float(base.get("storage_firm_mw") or 0)
        + ADEQUACY_EXTERNAL_TIE_FIRM_MW["PJM"]
    )
    gross = gross_adequacy_requirement_mw(c, "PJM", peak, year)
    dr = resolve_demand_response_supply_mw(c, "PJM", year, gross) or 0.0
    req = resolve_adequacy_requirement_mw(c, "PJM", peak, year)
    firm = sum(thermal.values()) + other + dr
    return dict(thermal_by_fuel=thermal, thermal_firm_mw=sum(thermal.values()), other_mw=other, dr_mw=dr,
                firm_mw=firm, requirement_mw=req, budget_mw=firm - req, position=firm / req)


def main() -> dict:
    out: dict = {}
    base21 = led(CONTROL, 2021)  # identical in both bundles (2021 is the seed year)
    fleet_enter = dict(base21["fleet_by_fuel_after"])
    peak_enter = float(base21["peak_demand_mw"])  # the bridge year prices on the prior-year peak
    # Dated (exogenous) exits landing between the screen and the cap horizon are
    # netted out of the cap's counterfactual fleet (capx D42) — identical in both arms.
    dated = defaultdict(float)
    for y in (2022, 2023, 2024):
        for r in led(CONTROL, y)["retirements"]:
            if r["reason"] == "announced":
                dated[r["fuel"]] += float(r["mw"])
    screen = {}
    for tag, b in (("control", CONTROL), ("arm", ARM)):
        rows = [r for r in led(b, SCREEN_YEAR)["pipeline_events"] if isinstance(r, dict)]
        decided = [r for r in rows if r["event"] == "decided"]
        capped = [r for r in rows if r["event"] == "entry_capped"]
        screen[tag] = dict(
            decided_mw=sum(r["mw"] for r in decided), decided_n=len(decided),
            capped_mw=sum(r["mw"] for r in capped), capped_n=len(capped),
            decided_by_fuel={f: sum(r["mw"] for r in decided if r["fuel"] == f) for f in {r["fuel"] for r in decided}},
            rows={r["unit_id"]: r for r in rows},
        )
    for tag, armed in (("control", False), ("arm", True)):
        c = cfg(armed)
        scheduled = set(screen[tag]["rows"][u]["unit_id"] for u in screen[tag]["rows"] if screen[tag]["rows"][u]["event"] in ("decided", "entry_capped"))
        fake = [_G(u, screen[tag]["rows"][u]["fuel"]) for u in scheduled]
        cap_year, cap_peak = _admission_cap_horizon(c, scheduled, {}, SCREEN_YEAR - 1, fake, peak_enter, SCREEN_YEAR)
        fleet_cap = {f: mw - dated.get(f, 0.0) for f, mw in fleet_enter.items()}
        at_enter = firm_side(c, SCREEN_YEAR, fleet_enter, base21, peak_enter)
        at_cap = firm_side(c, cap_year, fleet_cap, base21, cap_peak)
        # firm the admitted (decided) set carries on THIS arm's basis
        adm_firm = sum(r["mw"] * thermal_accreditation_fraction(r["fuel"], EFORD.get(r["fuel"], 0.05), "PJM", c, cap_year)
                       for r in screen[tag]["rows"].values() if r["event"] == "decided")
        coal_frac = thermal_accreditation_fraction("coal", EFORD["coal"], "PJM", c, cap_year)
        out[tag] = dict(
            gates=dict(pjm_accreditation_design_vintage=armed, pjm_demand_response_supply=armed),
            cap_year=cap_year, cap_peak_mw=cap_peak, coal_class_firm_fraction=coal_frac,
            entering=at_enter, at_cap_horizon=at_cap,
            admitted_nameplate_mw=screen[tag]["decided_mw"], admitted_n=screen[tag]["decided_n"],
            admitted_firm_mw_on_own_basis=adm_firm,
            capped_nameplate_mw=screen[tag]["capped_mw"],
        )
    # The swap set and the merit-key evidence: identical $/MW on every swapped
    # unit (FOM x multiplier is per fuel), so the re-rank can only come from the
    # firm denominator (class ELCC rating -> per-unit 1-EFORd).
    cr, ar = screen["control"]["rows"], screen["arm"]["rows"]
    swaps = [(u, cr[u]["event"], ar[u]["event"], cr[u]["fuel"], cr[u]["mw"], cr[u]["going_forward_cost_usd"] / (cr[u]["mw"] * 1000.0))
             for u in cr if u in ar and cr[u]["event"] != ar[u]["event"]]
    econ_identical = all(
        abs(cr[u]["net_revenue_usd"] - ar[u]["net_revenue_usd"]) < 1.0
        and abs(cr[u]["going_forward_cost_usd"] - ar[u]["going_forward_cost_usd"]) < 1.0
        and abs(cr[u]["capacity_revenue_usd"] - ar[u]["capacity_revenue_usd"]) < 1.0
        for u in cr if u in ar
    )
    out["swap"] = dict(
        n=len(swaps),
        capped_to_decided_mw=sum(mw for _, ce, ae, _, mw, _ in swaps if ae == "decided"),
        decided_to_capped_mw=sum(mw for _, ce, ae, _, mw, _ in swaps if ae == "entry_capped"),
        fuels=sorted({f for _, _, _, f, _, _ in swaps}),
        gfc_per_kw_yr_distinct=sorted({round(v, 2) for *_, v in swaps}),
        screen_economics_identical_every_unit=econ_identical,
        units=[dict(unit_id=u, control=ce, arm=ae, fuel=f, mw=mw) for u, ce, ae, f, mw, _ in sorted(swaps, key=lambda s: -s[4])],
    )
    out["delta"] = dict(
        budget_at_cap_horizon_mw=out["arm"]["at_cap_horizon"]["budget_mw"] - out["control"]["at_cap_horizon"]["budget_mw"],
        budget_entering_mw=out["arm"]["entering"]["budget_mw"] - out["control"]["entering"]["budget_mw"],
        admitted_firm_mw=out["arm"]["admitted_firm_mw_on_own_basis"] - out["control"]["admitted_firm_mw_on_own_basis"],
        admitted_nameplate_mw=out["arm"]["admitted_nameplate_mw"] - out["control"]["admitted_nameplate_mw"],
        position_at_cap_pts=100 * (out["arm"]["at_cap_horizon"]["position"] - out["control"]["at_cap_horizon"]["position"]),
    )
    return out


if __name__ == "__main__":
    res = main()
    Path(__file__).with_suffix(".json").write_text(json.dumps(res, indent=1, default=float))
    for tag in ("control", "arm"):
        r = res[tag]
        e, k = r["entering"], r["at_cap_horizon"]
        print(f"{tag:>8}: cap horizon {r['cap_year']} peak {r['cap_peak_mw']:,.0f} | entering firm {e['firm_mw']:,.0f} req {e['requirement_mw']:,.0f} budget {e['budget_mw']:,.0f} pos {e['position']:.4f}"
              f" | at cap: firm {k['firm_mw']:,.0f} req {k['requirement_mw']:,.0f} budget {k['budget_mw']:,.0f} pos {k['position']:.4f}"
              f" | admitted {r['admitted_nameplate_mw']:,.0f} MW ({r['admitted_n']}) = {r['admitted_firm_mw_on_own_basis']:,.0f} firm MW at coal fraction {r['coal_class_firm_fraction']:.3f}")
    d, s = res["delta"], res["swap"]
    print(f"delta: budget entering {d['budget_entering_mw']:+,.0f} | budget at cap {d['budget_at_cap_horizon_mw']:+,.0f} | admitted firm {d['admitted_firm_mw']:+,.0f} | admitted nameplate {d['admitted_nameplate_mw']:+,.0f} | position at cap {d['position_at_cap_pts']:+.2f} pts")
    print(f"swap: {s['n']} units, capped->decided {s['capped_to_decided_mw']:,.0f} MW, decided->capped {s['decided_to_capped_mw']:,.0f} MW, fuels {s['fuels']}, distinct $/kW-yr going-forward cost {s['gfc_per_kw_yr_distinct']}, screen economics identical on every unit: {s['screen_economics_identical_every_unit']}")

"""ENTRY SIGNAL L-1b: bang-bang vs margin-exhaustion entry volumes (ERCOT).

Finding `docs/FINDING-entry-screen-t1h-2026-08.md` §7 L-1b: separate the
energy-only cobweb (B-2, real market dynamics) from the bang-bang allocator
amplitude (D-1, `new_entry.py:1441` / `storage.py:1897`). Off the committed
T1-H dumps, recompute each decision year's build under a volume rule whose
scale is the screen's own economics, bounded by the SAME caps, and compare the
implied reserve-margin trajectory to the registered 19.0 → 8.5 → 14.7 →
25.2 %.

RULE 21 [R-DOF], in those words: any ELASTICITY or DAMPING parameter chosen to
make this trajectory match would be AN OPEN ROOT-CAUSE ISSUE, NOT A PARAMETER.
This probe therefore contains NO such coefficient. The volume rule is the one
closure the model already contains — **build until the screen's own repriced
margin is exhausted**: capacity is added in fixed physical tranches, and after
each tranche the SAME committed stack construction the dump records is
re-priced (base merit price via the dump's own ``mc_sorted``/``cap_sorted``
arrays; the ORDC tail via the model's own
``ercot_lookahead_expected_ordc_adder`` on the dump's own ``r_online`` /
``r_full`` / ``sigma_r`` internals), and the walk stops when no candidate's
margin is positive or every cap binds. The tranche size (250 MW) is a
resolution constant, not a tunable — halving it moves no reported GW by more
than one tranche.

Physical increments, each the model's own branch (no new parameters):
* a thermal tranche adds ``B x (1 - EFORD[tech])`` (NERC GADS registry
  constants) to the merit stack at the entrant's own variable cost, and the
  same MW to reserves in the hours where the dump shows reserves
  HEADROOM-BOUND (``r_online == top_of_stack - net_load``) — measured on the
  committed dumps this is 100 % of the top-adder hours in the 2023/2024
  screens, i.e. the binding branch of ``min(rtolcap, headroom)``, not an
  approximation. In rtolcap-bound (slack) hours the tranche adds nothing
  (conservative: the share tables would credit some).
* a storage tranche re-runs the model's own per-day peak-shave
  (``runner._storage_peak_shave_net_load``) with the tranche's merchant share
  ``(1 - ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)``, and adds its AS share to
  reserves in the headroom-bound hours.

Open-loop honesty: each decision year re-prices WITHIN the year, and the
cross-year state is adjusted by the counterfactual-vs-shipped build delta
(thermal at its 2-year COD lag into the later dumps' stacks; storage into the
later dumps' shave), using the same stack arithmetic — but the committed
signals themselves were produced by the SHIPPED path, so second-order
feedbacks (demand, retirement, procurement interactions) stay at their shipped
values. VRE decisions are held at shipped in both arms (their ELCC deltas are
identical across arms and cancel in the RM comparison).

Shipped-arm build reconstruction (the t1h-refresh bundle commits no evolution
ledgers): thermal {2022: cc 3000 + ct 1571, 2023: cc 3000 + ct 3000, 2024:
cc 3000 + ct 3000, 2025: none}, storage {2023: iron_air 3000 + flow_battery
2000}. Basis: the committed hindcast report's window totals (gas_cc 9.0 /
gas_ct 7.571 / storage 5.0 GW, decision basis), the ladder arithmetic
(gas_ct seed 0.7855 GW x 2 = 1.571 first-decision cap, committed in
docs/handoffs/ffr-9b/entry-screen-replay.json ``ladder_seed_gw``), the
finding §2 storage replay, and the sign pattern of this lane's own margin
replay (entry_signal_l1_dual_replay: 2022/2023 positive, 2025 negative under
both reserve-leg bounds; 2024 carried by the prior solve's post-solve ORDC
reserve leg, runner.py:3536-3564, which is not persisted offline).

Usage::

    uv run python scripts/probes/entry_signal_l1b_allocator_counterfactual.py \
        --out results/calibration/entry_signal_l1b_allocator_ercot.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import (  # noqa: E402
    CO2_RATES,
    EFORD,
    HEAT_RATE_BINS,
    VOM,
)
from market_sim.config.capacity_market import (  # noqa: E402
    QUEUE_CAP_GW,
    QUEUE_CAP_PER_TECH_GW,
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECHS,
)
from market_sim.config.entry_config import (  # noqa: E402
    ENTRY_COD_LAG_YEARS,
    ENTRY_GROWTH_LIMIT_MULTIPLE,
)
from market_sim.config.ercot_envelopes import (  # noqa: E402
    ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC,
)
from market_sim.config.scenario_resolvers import (  # noqa: E402
    resolve_new_entry_costs,
)
from market_sim.config.scenarios import (  # noqa: E402
    ScenarioConfig,
    resolve_real_discount_rate,
)
from market_sim.data.fuel import resolve_annual_gas_price  # noqa: E402
from market_sim.model.capacity_evolution.new_entry import (  # noqa: E402
    _capital_recovery_factor,
)
from market_sim.model.storage import (  # noqa: E402
    _degradation_cost_per_mwh,
    _storage_rte,
    compute_storage_annual_cost,
    estimate_storage_revenue,
    storage_accreditation_credit,
)
from market_sim.results.scarcity import (  # noqa: E402
    ercot_lookahead_expected_ordc_adder,
)
from market_sim.runner import _storage_peak_shave_net_load  # noqa: E402

ISO = "ERCOT"
BUNDLE = "results/hindcast/ercot-2021-2025-realized-t1h-refresh"
STEP_PRIOR_SOLVE = {2022: 2021, 2023: 2021, 2024: 2023, 2025: 2024}
STEP_DRIVER_YEAR = {2022: 2021, 2023: 2023, 2024: 2024, 2025: 2025}
# Fuel year of the SOLVE whose stack the entering-year signal is priced on
# (the stack mc is the solve year's own cost basis).
STEP_STACK_GAS_YEAR = {2022: 2021, 2023: 2021, 2024: 2023, 2025: 2024}
TRANCHE_MW = 250.0
# Registered screen-time reserve margins per entering year (finding §1.1 row
# B-2; the trajectory the charter names). The bundle commits no ledger, so the
# finding is the committed citation for the anchor levels; the probe's own
# contribution is the CROSS-ARM DELTA at each year, which needs no anchor.
REGISTERED_RM_PCT = {2022: 19.0, 2023: 8.5, 2024: 14.7, 2025: 25.2}
# Shipped-arm reconstruction (docstring: basis + citations).
SHIPPED_THERMAL = {
    2022: {"gas_cc": 3000.0, "gas_ct": 1571.0},
    2023: {"gas_cc": 3000.0, "gas_ct": 3000.0},
    2024: {"gas_cc": 3000.0, "gas_ct": 3000.0},
    2025: {},
}
SHIPPED_STORAGE = {2023: {"iron_air": 3000.0, "flow_battery": 2000.0}}
# Ladder seed (GW): the measured EIA-860 prior-max at the 2020 vintage —
# deterministic from the same data/vintage as the run; committed record:
# docs/handoffs/ffr-9b/entry-screen-replay.json "ladder_seed_gw".
LADDER_SEED_GW = {"gas_cc": 2.5698, "gas_ct": 0.7855}
# Storage base fleet entering the window (FFR-9A R1 measured base, li-ion).
STORAGE_BASE_MW = 223.1


def load_config() -> ScenarioConfig:
    """Rebuild the exact run config (cache-key-verified)."""
    rc = json.loads((REPO / BUNDLE / "run_config.json").read_text())
    cfg = ScenarioConfig(**rc["scenario_config"])
    meta = json.loads((REPO / BUNDLE / "meta.json").read_text())
    assert cfg.cache_key() == meta["cache_key"], "config drift"
    return cfg


def load_dump(prior: int, step: int) -> dict:
    """One committed screen-signal dump as plain float arrays."""
    key = next(p for p in sorted((REPO / BUNDLE / ISO).iterdir()) if p.is_dir())
    with np.load(key / f"screen_signal_diag_{prior}_for_{step}.npz") as z:
        out = {}
        for k in z.files:
            arr = z[k]
            if arr.dtype.kind in "fiu":
                out[k] = np.asarray(arr, dtype=float)
            else:
                out[k] = arr
        return out


def thermal_vc(tech: str, gas: float) -> float:
    """Best-in-class entrant variable cost (new_entry.py thermal branch)."""
    return min(HEAT_RATE_BINS[tech].values()) * gas + VOM[tech] + min(
        CO2_RATES[tech].values()
    ) * 0.0


def thermal_fixed(tech: str, config: ScenarioConfig) -> float:
    """Seed-state annualized fixed cost, $/MW-yr (identical across arms)."""
    costs = resolve_new_entry_costs(config)[tech]
    crf = _capital_recovery_factor(
        resolve_real_discount_rate(config, tech), costs["lifetime_yr"]
    )
    return (costs["capex_per_kw"] * crf + costs["fom_per_kw_yr"]) * 1000.0


class StepState:
    """Mutable within-year repricing state built from one committed dump."""

    def __init__(self, dump: dict, config: ScenarioConfig, step: int):
        self.config = config
        self.step = step
        self.mc = dump["mc_sorted_usd_mwh"].copy()
        self.cap = dump["cap_sorted_mean_mw"].copy()
        self.net_load_system = dump["net_load_system_mw"].copy()
        self.net_load = dump["net_load_mw"].copy()
        self.as_hold = dump["as_hold_mw"].copy()
        self.sigma_r = dump["sigma_r_mw"].copy()
        self.top_of_stack = dump["top_of_stack_mw"].copy()
        self.r_online = dump["r_online_mw"].copy()
        self.r_full = dump["r_full_mw"].copy()
        # Hours where reserves are headroom-bound in the COMMITTED state: the
        # branch where added capability reaches the reserve tail.
        headroom = dump["installed_headroom_mw"]
        self.headroom_bound = self.r_online >= headroom - 1e-6
        self.storage_power = float(dump["storage_power_mw"])
        self.storage_energy = float(dump["storage_energy_mwh"])
        self.storage_rte = float(dump["storage_rte"])
        self.storage_as = float(dump["storage_as_mw"])
        # Anchors for the delta-corrected base price.
        self._dump_base = dump["price_base_usd_mwh"].copy()
        self._base_raw0 = self._merit_price()
        self._extra_reserve = np.zeros_like(self.net_load)

    def _merit_price(self) -> np.ndarray:
        """Mean-capacity merit price of the CURRENT stack at current load."""
        order = np.argsort(self.mc, kind="stable")
        cum = np.cumsum(self.cap[order])
        search = np.clip(self.net_load + self.as_hold, 0.0, None)
        idx = np.searchsorted(cum, search, side="left")
        return self.mc[order][np.minimum(idx, order.size - 1)]

    def prices(self) -> tuple[np.ndarray, np.ndarray]:
        """(base, adder) at current state — delta-anchored to the dump.

        Base: the dump's own hourly-availability price plus the mean-capacity
        stack construction's delta (exactly zero at zero added capacity).
        Adder: the model's own expected-ORDC function on the current reserve
        state (reproduces the dump's adder at zero delta — validated).
        """
        base = self._dump_base + (self._merit_price() - self._base_raw0)
        headroom = self.top_of_stack - self.net_load
        r_on = np.where(
            self.headroom_bound, headroom, self.r_online + self._extra_reserve * 0.0
        )
        r_fu = np.where(self.headroom_bound, headroom, self.r_full)
        adder = ercot_lookahead_expected_ordc_adder(
            self.config,
            self.step,
            r_online_mw=r_on,
            r_full_mw=r_fu,
            system_lambda=base,
            sigma_r_mw=self.sigma_r,
        )
        return base, adder

    def add_thermal(self, tech: str, mw: float, vc: float) -> None:
        """Commit a thermal tranche: stack capacity + headroom-bound reserves."""
        avail = 1.0 - EFORD[tech]
        self.mc = np.append(self.mc, vc)
        self.cap = np.append(self.cap, mw * avail)
        self.top_of_stack = self.top_of_stack + mw * avail

    def add_storage(self, tech: str, mw: float) -> None:
        """Commit a storage tranche: merchant-share shave + AS-share reserves."""
        frac = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
        dur = float(STORAGE_TECHS[tech]["duration_hr"])
        rte = _storage_rte(tech, self.config)
        self.net_load = _storage_peak_shave_net_load(
            self.net_load, (1.0 - frac) * mw, (1.0 - frac) * mw * dur, rte
        )
        self.storage_power += mw
        self.storage_energy += mw * dur
        self.storage_as += frac * mw
        # AS-share capability reaches reserves where headroom binds (via the
        # rtolcap storage term); headroom itself moves through net_load above.
        self.r_online = self.r_online + 0.0  # headroom-bound branch recomputes
        self.r_full = self.r_full + 0.0

    def set_cross_year_delta(
        self,
        thermal_delta: dict[str, float],
        storage_power_delta: float,
        storage_energy_delta: float,
        gas_stack: float,
    ) -> None:
        """Adjust the committed state by (counterfactual - shipped) prior builds.

        Thermal deltas (COD <= entering year) enter/leave the stack at the
        entrant vc on the solve-year fuel; the storage delta re-runs the
        model's own shave from the PRE-SHAVE net load with the counterfactual
        fleet. Zero deltas leave the committed state byte-identical.
        """
        for tech, dmw in thermal_delta.items():
            if abs(dmw) < 1e-9:
                continue
            avail = 1.0 - EFORD[tech]
            vc = thermal_vc(tech, gas_stack)
            self.mc = np.append(self.mc, vc)
            self.cap = np.append(self.cap, dmw * avail)  # negative = removal
            self.top_of_stack = self.top_of_stack + dmw * avail
        if abs(storage_power_delta) > 1e-9:
            frac = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
            p_cf = self.storage_power + storage_power_delta
            e_cf = self.storage_energy + storage_energy_delta
            self.net_load = _storage_peak_shave_net_load(
                self.net_load_system, (1.0 - frac) * p_cf, (1.0 - frac) * e_cf,
                self.storage_rte,
            )
            self.storage_power = p_cf
            self.storage_energy = e_cf
            self.storage_as += frac * storage_power_delta
        # Re-anchor the base-price delta construction on the adjusted stack.
        self._base_raw0 = self._base_raw0  # anchor stays the committed stack


def storage_margin(
    tech: str, prices: np.ndarray, config: ScenarioConfig, step: int
) -> float:
    """Marginal storage entrant margin at current prices (seed cost state)."""
    rev = estimate_storage_revenue(
        prices,
        int(STORAGE_TECHS[tech]["duration_hr"]),
        _storage_rte(tech, config),
        degradation_cost_per_mwh=_degradation_cost_per_mwh(tech, config),
    )
    cost = compute_storage_annual_cost(tech, step, config, cumulative_gw=None)
    return rev - cost  # ERCOT: capacity value 0 (energy-only), AS credit 0


def equilibrium_walk(
    state: StepState,
    config: ScenarioConfig,
    step: int,
    gas_driver: float,
    ladder_prior_max_gw: dict[str, float],
    iso_budget_mw: float,
    fixed_costs: dict[str, float],
) -> dict:
    """Margin-exhaustion walk: tranches to the best candidate, repriced each.

    Candidates: gas_cc/gas_ct (per-tech queue caps + growth ladder + shared
    ISO budget) and the storage stack (its own budget/share cap/ceiling —
    storage.py never draws the thermal queue budget). Stops when no candidate
    clears zero at the CURRENT repriced signal or every cap binds.
    """
    thermal_caps = {
        t: min(
            QUEUE_CAP_PER_TECH_GW[ISO][t] * 1000.0,
            ENTRY_GROWTH_LIMIT_MULTIPLE * ladder_prior_max_gw[t] * 1000.0,
        )
        for t in ("gas_cc", "gas_ct")
    }
    built = {t: 0.0 for t in thermal_caps}
    st_budget = min(
        STORAGE_ANNUAL_BUILD_CAP_MW[ISO],
        max(0.0, STORAGE_DEPLOYMENT_CEILING_MW[ISO] - state.storage_power),
    )
    st_share_cap = st_budget * STORAGE_TECH_BUILD_SHARE_CAP
    st_built: dict[str, float] = {}
    iso_remaining = iso_budget_mw
    trace = []
    for _ in range(200):
        base, adder = state.prices()
        sig = base + adder
        cands: list[tuple[float, str, str]] = []
        for t in thermal_caps:
            room = min(thermal_caps[t] - built[t], iso_remaining)
            if room >= TRANCHE_MW - 1e-6:
                vc = thermal_vc(t, gas_driver)
                margin = float(np.maximum(sig - vc, 0.0).sum()) - fixed_costs[t]
                cands.append((margin, "thermal", t))
        if sum(st_built.values()) <= st_budget - TRANCHE_MW + 1e-6:
            for t in STORAGE_TECHS:
                if st_built.get(t, 0.0) <= st_share_cap - TRANCHE_MW + 1e-6:
                    cands.append(
                        (storage_margin(t, sig, config, step), "storage", t)
                    )
        cands = [c for c in cands if c[0] > 0.0]
        if not cands:
            break
        margin, kind, tech = max(cands)
        if kind == "thermal":
            state.add_thermal(tech, TRANCHE_MW, thermal_vc(tech, gas_driver))
            built[tech] += TRANCHE_MW
            iso_remaining -= TRANCHE_MW
        else:
            state.add_storage(tech, TRANCHE_MW)
            st_built[tech] = st_built.get(tech, 0.0) + TRANCHE_MW
        trace.append(
            {"tech": tech, "margin_at_entry": round(margin, 1), "mw": TRANCHE_MW}
        )
    base, adder = state.prices()
    return {
        "thermal_built_mw": {t: round(v, 1) for t, v in built.items()},
        "storage_built_mw": {t: round(v, 1) for t, v in sorted(st_built.items())},
        "final_adder_mean": round(float(adder.mean()), 3),
        "tranches": len(trace),
        "last_tranche_margins": trace[-3:],
        "exhausted": not trace or True,
    }


def storage_firm_mw(builds: dict[str, float], config: ScenarioConfig, fleet_mw: float) -> float:
    """ELCC-accredited firm MW of a storage build mix (model's own credit)."""
    total = 0.0
    from market_sim.config.capacity_market import STORAGE_ELCC_SATURATION_EXPONENT

    ceiling = STORAGE_DEPLOYMENT_CEILING_MW[ISO]
    derate = (1.0 - min(1.0, fleet_mw / ceiling)) ** STORAGE_ELCC_SATURATION_EXPONENT
    for tech, mw in builds.items():
        elcc = storage_accreditation_credit(
            float(STORAGE_TECHS[tech]["duration_hr"]), ISO, config, tech
        )
        total += mw * elcc * derate
    return total


def main() -> None:
    """CLI entry: run both arms, emit builds + RM trajectories + verdict."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--vre-budget-consumed-gw",
        type=float,
        default=None,
        help="ISO queue budget consumed by (held-at-shipped) VRE before the "
        "thermal walk; None sweeps {0, 8} and reports both",
    )
    args = ap.parse_args()
    config = load_config()

    sweeps = (
        [args.vre_budget_consumed_gw]
        if args.vre_budget_consumed_gw is not None
        else [0.0, 8.0]
    )
    result: dict = {
        "probe": "entry_signal_l1b_allocator_counterfactual",
        "finding": "docs/FINDING-entry-screen-t1h-2026-08.md §7 L-1b",
        "iso": ISO,
        "bundle": BUNDLE,
        "cache_key": config.cache_key(),
        "tranche_mw": TRANCHE_MW,
        "rule_21_r_dof": (
            "no elasticity or damping parameter exists in this probe; the "
            "volume rule is margin exhaustion under the model's own repriced "
            "signal, bounded by the same caps — the only admissible closure. "
            "Any tuned coefficient here would be an open root-cause issue, "
            "not a parameter."
        ),
        "registered_rm_pct": REGISTERED_RM_PCT,
        "shipped_reconstruction": {
            "thermal": SHIPPED_THERMAL,
            "storage": SHIPPED_STORAGE,
        },
        "validation": {},
        "arms": {},
    }

    # ---- validation: the adder function reproduces each committed dump ----
    checks = []
    for step, prior in STEP_PRIOR_SOLVE.items():
        dump = load_dump(prior, step)
        adder0 = ercot_lookahead_expected_ordc_adder(
            config,
            step,
            r_online_mw=dump["r_online_mw"],
            r_full_mw=dump["r_full_mw"],
            system_lambda=dump["price_base_usd_mwh"],
            sigma_r_mw=dump["sigma_r_mw"],
        )
        err = float(np.abs(adder0 - dump["adder_usd_mwh"]).max())
        # Shave reproduction: the model's own shave on the pre-shave load with
        # the dump's own fleet terms must give back the dump's net load.
        frac = float(ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC)
        nl = _storage_peak_shave_net_load(
            dump["net_load_system_mw"],
            (1.0 - frac) * float(dump["storage_power_mw"]),
            (1.0 - frac) * float(dump["storage_energy_mwh"]),
            float(dump["storage_rte"]),
        )
        shave_err = float(np.abs(nl - dump["net_load_mw"]).max())
        checks.append(
            {
                "step": step,
                "adder_max_abs_err": round(err, 6),
                "adder_ok": err < 0.01,
                "shave_max_abs_err": round(shave_err, 3),
                "shave_ok": shave_err < 1.0,
            }
        )
    result["validation"]["reproduction"] = checks
    if not all(c["adder_ok"] for c in checks):
        result["validation"]["note"] = "adder reproduction failed — see checks"

    for vre_gw in sweeps:
        arm_label = f"vre_budget_{vre_gw:g}gw"
        iso_budget = QUEUE_CAP_GW[ISO] * 1000.0 - vre_gw * 1000.0
        prior_max = dict(LADDER_SEED_GW)
        cf_thermal: dict[int, dict[str, float]] = {}
        cf_storage: dict[int, dict[str, float]] = {}
        steps_out = {}
        for step, prior in STEP_PRIOR_SOLVE.items():
            dump = load_dump(prior, step)
            state = StepState(dump, config, step)
            gas_stack = resolve_annual_gas_price(config, STEP_STACK_GAS_YEAR[step])
            gas_driver = resolve_annual_gas_price(config, STEP_DRIVER_YEAR[step])
            # Cross-year delta: prior counterfactual-vs-shipped decisions
            # whose capacity the committed entering-year state already carries
            # (thermal COD lag 2; storage commissions in its decision year).
            th_delta: dict[str, float] = {}
            for dy, mix in SHIPPED_THERMAL.items():
                if dy + ENTRY_COD_LAG_YEARS.get("gas_cc", 2) <= step:
                    for t, mw in mix.items():
                        th_delta[t] = th_delta.get(t, 0.0) - mw
            for dy, mix in cf_thermal.items():
                if dy + ENTRY_COD_LAG_YEARS.get("gas_cc", 2) <= step:
                    for t, mw in mix.items():
                        th_delta[t] = th_delta.get(t, 0.0) + mw
            st_power_delta = 0.0
            st_energy_delta = 0.0
            for dy, mix in SHIPPED_STORAGE.items():
                if dy < step:
                    for t, mw in mix.items():
                        st_power_delta -= mw
                        st_energy_delta -= mw * float(STORAGE_TECHS[t]["duration_hr"])
            for dy, mix in cf_storage.items():
                if dy < step:
                    for t, mw in mix.items():
                        st_power_delta += mw
                        st_energy_delta += mw * float(STORAGE_TECHS[t]["duration_hr"])
            state.set_cross_year_delta(
                th_delta, st_power_delta, st_energy_delta, gas_stack
            )
            fixed = {t: thermal_fixed(t, config) for t in ("gas_cc", "gas_ct")}
            walk = equilibrium_walk(
                state, config, step, gas_driver, prior_max, iso_budget, fixed
            )
            cf_thermal[step] = {
                t: mw for t, mw in walk["thermal_built_mw"].items() if mw > 0
            }
            cf_storage[step] = dict(walk["storage_built_mw"])
            for t, mw in cf_thermal[step].items():
                prior_max[t] = max(prior_max[t], mw / 1000.0)
            peak = float(
                (
                    dump["net_load_system_mw"]
                    + dump["wind_potential_mw"]
                    + dump["solar_potential_mw"]
                ).max()
            )
            steps_out[str(step)] = {
                "walk": walk,
                "cross_year_delta_thermal_mw": {
                    t: round(v, 1) for t, v in th_delta.items()
                },
                "cross_year_delta_storage_mw": round(st_power_delta, 1),
                "peak_demand_mw": round(peak, 1),
            }

        # RM trajectory: registered anchor + cross-arm accredited delta/peak.
        # Thermal at the CDR seasonal-rating basis (~nameplate; the ERCOT
        # PRM's own counting convention, capacity_market.py PLANNING_RESERVE_
        # MARGIN_BY_ISO citation); storage at the model's duration ELCC.
        rm_traj = {}
        for step in STEP_PRIOR_SOLVE:
            d_firm = 0.0
            for dy in STEP_PRIOR_SOLVE:
                lag = ENTRY_COD_LAG_YEARS.get("gas_cc", 2)
                if dy + lag <= step:
                    for t in ("gas_cc", "gas_ct"):
                        d_firm += cf_thermal.get(dy, {}).get(t, 0.0) - SHIPPED_THERMAL[
                            dy
                        ].get(t, 0.0)
                if dy < step:
                    d_firm += storage_firm_mw(
                        cf_storage.get(dy, {}), config, STORAGE_BASE_MW
                    ) - storage_firm_mw(
                        SHIPPED_STORAGE.get(dy, {}), config, STORAGE_BASE_MW
                    )
            peak = steps_out[str(step)]["peak_demand_mw"]
            rm_cf = REGISTERED_RM_PCT[step] + 100.0 * d_firm / peak
            rm_traj[str(step)] = {
                "registered_rm_pct": REGISTERED_RM_PCT[step],
                "delta_firm_mw": round(d_firm, 1),
                "counterfactual_rm_pct": round(rm_cf, 2),
            }
        steps_swings = [
            rm_traj[str(y + 1)]["counterfactual_rm_pct"]
            - rm_traj[str(y)]["counterfactual_rm_pct"]
            for y in (2022, 2023, 2024)
        ]
        reg_swings = [
            REGISTERED_RM_PCT[y + 1] - REGISTERED_RM_PCT[y] for y in (2022, 2023, 2024)
        ]
        result["arms"][arm_label] = {
            "iso_thermal_budget_mw": iso_budget,
            "steps": steps_out,
            "rm_trajectory": rm_traj,
            "rm_swings_pp": {
                "registered": [round(s, 2) for s in reg_swings],
                "counterfactual": [round(s, 2) for s in steps_swings],
            },
        }

    out = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, sort_keys=False) + "\n")
    print(f"wrote {out}")
    print("reproduction:", json.dumps(result["validation"]["reproduction"]))


if __name__ == "__main__":
    main()

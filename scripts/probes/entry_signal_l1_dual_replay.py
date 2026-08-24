"""ENTRY SIGNAL L-1: the entry/storage screens replayed on committed LP duals.

The finding `docs/FINDING-entry-screen-t1h-2026-08.md` §5 names the caveat this
probe measures: under ``entry_lookahead_reprice = False`` every capacity screen
falls back to ``prior_results["prices"]`` — the LP duals — instead of the
zone-flat marginal-cost step function ``runner._lookahead_reprice_signal``
builds (D-8). No committed T1-H hindcast bundle persists its own hourly duals,
so the committed instance of "the model's LP duals for an ERCOT year" is the
backcast keeper's hourly sidecar (``hourly/system_<year>.parquet``, rule 15) —
the ``price`` column, which carries the year's final scored hourly price per
zone (scarcity components included; verified numerically in the probe run
record). This probe replays BOTH screens' value arithmetic per T1-H decision
year twice — once on the committed ``screen_signal_diag`` dump signal (the
shipped arm, which must reproduce the phase-0/ledger record) and once on the
keeper dual array — holding EVERYTHING else (storage fleet state, cost state,
fuel/carbon drivers, caps, config) identical, and reports the delta in

  (i)   each tech's margin SIGN,
  (ii)  the storage tech RANKING (and allocator outcome),
  (iii) the wind/solar CAPTURE RATIOS,

plus the dual array's own shape statistics (daily spread, zonal dispersion)
against the dump signal's.

MEASUREMENT ONLY (finding §7 L-1: "this rung produces evidence only") — no
mechanism is armed, no solve path touched, no LP run. Stated bounds:

* The exact counterfactual is the T1-H run's OWN prior-year duals at its own
  evolved fleet. Those are not committed (only score.json + the signal dumps
  are), so the keeper dual is a same-ISO-same-year stand-in produced by a
  different run (backcast mode, measured overlays, actual fleet). The delta
  therefore measures SIGNAL CONSTRUCTION (MC-step vs LP dual) plus a
  fleet/run-identity residual, and is labelled as such — it cannot be read as
  the exact armed-counterfactual number.
* Decision years 2022/2023 price off the 2021 solve; no 2021 hourly duals are
  committed anywhere, so their exact-map dual arm is DATA-BLOCKED. For the
  entering-2023 screen the probe additionally reports a same-year read (the
  2023 keeper duals), labelled ``dual_same_year``: what the screen would say
  given the realized 2023 market shape — a foresight-caveated diagnostic,
  never the counterfactual.
* Cost state is the entry seed (``cumulative_gw=None``), identical across
  arms, exactly as ``entry_screen_t1h_phase0.py`` ran — the margin DELTA
  between arms is exact even where the level carries seed-vintage capex.

Validation gates built in (the probe refuses to report unvalidated deltas):
* shipped-arm storage margins reproduce the committed phase-0 artifact
  (``results/calibration/entry_screen_t1h_phase0_ercot.json``) and the 2023
  allocator result reproduces the registered ledger (iron_air 3000 +
  flow_battery 2000);
* the thermal energy-margin arithmetic reproduces the committed FFR-9B replay
  (``docs/handoffs/ffr-9b/entry-screen-replay.json``) on that bundle's own
  dump, byte-for-byte at the recorded rounding.

Usage::

    uv run python scripts/probes/entry_signal_l1_dual_replay.py \
        --bundle results/hindcast/ercot-2021-2025-realized-t1h-refresh \
        --duals-bundle results/calibration/ercot223_release_arm \
        --out results/calibration/entry_signal_l1_dual_replay_ercot.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.constants import (  # noqa: E402
    CO2_RATES,
    HEAT_RATE_BINS,
    HOURS_PER_YEAR,
    VOM,
)
from market_sim.config.capacity_market import (  # noqa: E402
    STORAGE_ANNUAL_BUILD_CAP_MW,
    STORAGE_DEPLOYMENT_CEILING_MW,
    STORAGE_TECH_BUILD_SHARE_CAP,
    STORAGE_TECHS,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
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
    compute_lcoe,
    get_renewable_zone,
)
from market_sim.model.storage import (  # noqa: E402
    _degradation_cost_per_mwh,
    _storage_rte,
    compute_storage_annual_cost,
    estimate_capacity_value,
    estimate_storage_revenue,
)
from market_sim.model.ancillary import as_revenue_per_mw_yr  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402
from market_sim.policy.federal_ces import (  # noqa: E402
    effective_eac_price_for_tech,
)

ISO = "ERCOT"
# entering step year -> the prior SOLVED year whose results drove the screen
# (t1h-refresh meta: solved 2021/2023/2024/2025, bridged 2022).
STEP_PRIOR_SOLVE = {2022: 2021, 2023: 2021, 2024: 2023, 2025: 2024}
# entering step year -> the runner's fuel/carbon driver year (bridge steps
# drive off the last solved year; ffr9b_entry_screen_replay.py precedent).
STEP_DRIVER_YEAR = {2022: 2021, 2023: 2023, 2024: 2024, 2025: 2025}
_THERMAL = ("gas_cc", "gas_ct")
_VRE = ("wind", "solar")

# --- CAISO extension (rule 25 [R-ISO-SCOPE]: CAISO derives its own numbers;
# nothing transfers from ERCOT except the probe's ARITHMETIC). ----------------
#
# The step maps are NOT copied from ERCOT: CAISO's registered bundle
# (caiso-2021-2025-realized, key 408f9199a82f5814) ships
# ``capacity_screen_unified_lookahead=False``, so its lookahead is suppressed
# whenever the entering year is a bridge year (runner.py ``lookahead_next_ok``:
# ``unified_screens or next_year not in HINDCAST_BRIDGE_YEARS``). ERCOT's
# refresh ran unified-ON and therefore priced the bridge steps too. CAISO's
# dumps are consequently the NON-BRIDGE entering years only — the maps below
# are asserted against the dumps actually present, never assumed.
CAISO_STEP_PRIOR_SOLVE = {2024: 2023, 2025: 2024}
CAISO_STEP_DRIVER_YEAR = {2024: 2024, 2025: 2025}

ISO_STEPS = {
    "ERCOT": (STEP_PRIOR_SOLVE, STEP_DRIVER_YEAR),
    "CAISO": (CAISO_STEP_PRIOR_SOLVE, CAISO_STEP_DRIVER_YEAR),
}

# Zones the DUAL arm cannot price, excluded from BOTH arms so the cross-arm
# delta stays like-for-like (rule 1: the comparison object is the signal, not
# the zone set).
#
# CAISO only, and it is a real topology difference between the two lanes, not
# a naming mismatch: the forecast lane's ISOConfig carries ONE seam node
# (`WECC_import`), while the backcast keeper caiso200_h1_memberpanel resolves
# the same seam as TWO external hub nodes (`WECC_DSW`, `WECC_PNW`). The five
# in-state zones — NP15, ZP26, LA_BASIN, SDGE, SP15_rest — match exactly, and
# they are the only zones an entry candidate can build in: `get_renewable_zone`
# returns an in-state zone, and a seam node's dual is an external hub price,
# not a CAISO clearing price a new CAISO unit would earn. Aggregating the two
# hub rows into a synthetic `WECC_import` row would invent a price the model
# never formed, so the node is dropped from both arms instead.
ISO_DUAL_ZONE_EXCLUDE = {"CAISO": ("WECC_import",)}


def load_config(bundle: Path) -> ScenarioConfig:
    """Rebuild the run's exact ScenarioConfig from its committed run_config."""
    rc = json.loads((bundle / "run_config.json").read_text())
    cfg = ScenarioConfig(**rc["scenario_config"])
    meta = json.loads((bundle / "meta.json").read_text())
    if cfg.cache_key() != meta["cache_key"]:
        raise SystemExit(
            f"config reconstruction drifted: {cfg.cache_key()} != "
            f"{meta['cache_key']} — refuse to replay on a wrong config"
        )
    return cfg


def load_dump(bundle: Path, prior: int, step: int, iso: str = ISO) -> dict:
    """Load one committed screen-signal dump as plain arrays."""
    key_dirs = [p for p in sorted((bundle / iso).iterdir()) if p.is_dir()]
    if len(key_dirs) != 1:
        raise SystemExit(f"expected one cache key under {bundle / iso}")
    path = key_dirs[0] / f"screen_signal_diag_{prior}_for_{step}.npz"
    with np.load(path, allow_pickle=True) as z:
        return {k: z[k] for k in z.files}


def dual_price_array(
    duals_bundle: Path, year: int, zone_names: list[str]
) -> np.ndarray | None:
    """Return the keeper's (n_zones, T) hourly price for ``year``, or None.

    The ``price`` column of ``hourly/system_<year>.parquet`` (pass P1 — THE
    scored pass) is the final hourly price with the run's scarcity components
    included; the probe records the composition check in its output.
    """
    path = duals_bundle / "hourly" / f"system_{year}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    if "pass" in df.columns:
        df = df[df["pass"] == "P1"]
    mat = df.pivot_table(index="zone", columns="hour", values="price")
    missing = [z for z in zone_names if z not in mat.index]
    if missing:
        raise SystemExit(f"duals for {year} missing zones {missing}")
    return mat.loc[zone_names].to_numpy(dtype=float)


def thermal_margins(
    prices: np.ndarray,
    gas: float,
    carbon: float,
    config: ScenarioConfig,
    r_sig: np.ndarray | None,
) -> dict:
    """Mirror of the new_entry.py thermal branch (values only, no allocator).

    ``energy = sum_t max(mean_z(price) - var_cost, 0)`` with the reserve leg
    as ``max(energy_h, r_h)`` when supplied (new_entry.py:1104-1108); fixed
    cost is the Wright-seed capex annuity + FOM (cumulative_gw=None, both
    arms). Validated against docs/handoffs/ffr-9b/entry-screen-replay.json.
    """
    price_h = np.asarray(prices, dtype=float).mean(axis=0)
    out = {}
    costs_all = resolve_new_entry_costs(config)
    for tech in _THERMAL:
        best_hr = min(HEAT_RATE_BINS[tech].values())
        best_co2 = min(CO2_RATES[tech].values())
        vc = best_hr * gas + VOM[tech] + best_co2 * carbon
        hourly = np.maximum(price_h - vc, 0.0)
        if r_sig is not None:
            n = min(hourly.size, r_sig.size)
            hourly = np.maximum(hourly[:n], np.asarray(r_sig, dtype=float)[:n])
        energy = float(hourly.sum())
        costs = costs_all[tech]
        crf = _capital_recovery_factor(
            resolve_real_discount_rate(config, tech), costs["lifetime_yr"]
        )
        fixed = (costs["capex_per_kw"] * crf + costs["fom_per_kw_yr"]) * 1000.0
        out[tech] = {
            "var_cost_per_mwh": round(vc, 3),
            "energy_margin_per_mw_yr": round(energy, 1),
            "fixed_cost_per_mw_yr": round(fixed, 1),
            "margin_per_mw_yr": round(energy - fixed, 1),
            "sign": "+" if energy - fixed > 0.0 else "-",
        }
    return out


def vre_capture(
    prices: np.ndarray,
    dump: dict,
    config: ScenarioConfig,
    step: int,
    zone_names: list[str],
    iso: str = ISO,
) -> dict:
    """Capture prices/ratios + margin sign for wind/solar on one price array.

    Two bases per tech: the flat system mean (phase-0 read C, comparable to
    the finding §3) and the screen's own construction — the build zone's
    price row against the potential profile (live only on a zonal array;
    identical to the system basis on a zone-flat one). Margin sign uses the
    per-MWh identity margin/(8760*cf_mean) = capture + attribute - LCOE,
    which is invariant to the potential profile's unknown nameplate scale.
    """
    out: dict = {}
    for tech in _VRE:
        pot = np.asarray(dump[f"{tech}_potential_mw"], dtype=float)
        if pot.sum() <= 0:
            continue
        flat_mean = float(prices.mean())
        sys_price = prices.mean(axis=0)
        zone = get_renewable_zone(iso, tech)
        zrow = prices[zone_names.index(zone)]
        cap_sys = float((sys_price * pot).sum() / pot.sum())
        cap_zone = float((zrow * pot).sum() / pot.sum())
        lcoe = compute_lcoe(tech, step, config, cumulative_gw=None)
        attr = effective_eac_price_for_tech(config, tech, step)
        margin_per_mwh = cap_zone + attr - lcoe
        out[tech] = {
            "flat_signal_mean": round(flat_mean, 2),
            "capture_price_system": round(cap_sys, 2),
            "capture_ratio_system": round(cap_sys / flat_mean, 4),
            "build_zone": zone,
            "capture_price_zone_row": round(cap_zone, 2),
            "capture_ratio_zone_row": round(cap_zone / flat_mean, 4),
            "lcoe_per_mwh": round(lcoe, 2),
            "attribute_price_per_mwh": round(attr, 2),
            "margin_per_mwh": round(margin_per_mwh, 2),
            "sign": "+" if margin_per_mwh > 0.0 else "-",
        }
    return out


def storage_screen(
    prices: np.ndarray,
    config: ScenarioConfig,
    step: int,
    existing_mw: float,
    iso: str = ISO,
) -> dict:
    """The real storage value stack + merit allocator on one price array.

    Calls the model's own functions (estimate_storage_revenue — per-window
    best-zone selection live on a zonal array — estimate_capacity_value,
    as_revenue_per_mw_yr, compute_storage_annual_cost at the entry seed);
    allocator loop mirrors storage.py:1892-1901 verbatim.
    """
    rows = {}
    margins: list[tuple[float, str]] = []
    for tech_name, tech in STORAGE_TECHS.items():
        rev = estimate_storage_revenue(
            prices,
            int(tech["duration_hr"]),
            _storage_rte(tech_name, config),
            degradation_cost_per_mwh=_degradation_cost_per_mwh(tech_name, config),
        )
        cap = estimate_capacity_value(
            tech_name, existing_mw, config, iso, None, year=step
        )
        as_rev = as_revenue_per_mw_yr("storage", existing_mw, config)
        cost = compute_storage_annual_cost(tech_name, step, config, cumulative_gw=None)
        margin = rev + cap + as_rev - cost
        rows[tech_name] = {
            "arbitrage_per_mw_yr": round(rev, 1),
            "capacity_value_per_mw_yr": round(cap, 1),
            "as_revenue_per_mw_yr": round(as_rev, 1),
            "annual_cost_per_mw_yr": round(cost, 1),
            "margin_per_mw_yr": round(margin, 1),
            "sign": "+" if margin > 0.0 else "-",
        }
        if margin > 0.0:
            margins.append((margin, tech_name))
    margins.sort(key=lambda m: m[0], reverse=True)
    budget = min(
        STORAGE_ANNUAL_BUILD_CAP_MW[iso],
        max(0.0, STORAGE_DEPLOYMENT_CEILING_MW[iso] - existing_mw),
    )
    per_tech_cap = budget * STORAGE_TECH_BUILD_SHARE_CAP
    remaining = budget
    built = []
    for _, tech_name in margins:
        if remaining <= 0.0:
            break
        mw = min(remaining, per_tech_cap)
        remaining -= mw
        built.append({"tech": tech_name, "build_mw": round(mw, 1)})
    ranking = sorted(rows.items(), key=lambda kv: kv[1]["margin_per_mw_yr"], reverse=True)
    return {
        "techs": rows,
        "ranking_by_margin": [t for t, _ in ranking],
        "profitable": [t for _, t in margins],
        "budget_mw": budget,
        "allocator_result": built,
    }


def shape_stats(prices: np.ndarray, spread_hours: int = 4) -> dict:
    """Daily top/bottom spread + zonal dispersion of one (n_zones, T) array."""
    sys_p = prices.mean(axis=0)
    days = sys_p[: 365 * 24].reshape(365, 24)
    ordered = np.sort(days, axis=1)
    spread = float(
        (ordered[:, -spread_hours:].mean(axis=1) - ordered[:, :spread_hours].mean(axis=1)).mean()
    )
    return {
        "mean": round(float(prices.mean()), 2),
        "daily_top4_bot4_spread_system": round(spread, 2),
        "zonal_mean_range": round(
            float(prices.mean(axis=1).max() - prices.mean(axis=1).min()), 2
        ),
        "hourly_cross_zone_spread_mean": round(
            float((prices.max(axis=0) - prices.min(axis=0)).mean()), 2
        ),
    }


def _validate_thermal_vs_ffr9b() -> dict:
    """Reproduce the committed FFR-9B thermal energy margins (gate)."""
    ref_path = REPO / "docs/handoffs/ffr-9b/entry-screen-replay.json"
    ref = json.loads(ref_path.read_text())
    bundle = REPO / "results/hindcast/ercot-2021-2025-t1ff-armr-ffr9b-regen"
    rc = json.loads((bundle / "run_config.json").read_text())
    # The FFR-9B bundle predates later field deletions (rule 26 [R-DELETE]),
    # so its dump carries keys the current ScenarioConfig no longer accepts.
    # Filter to current fields — the energy-margin gate compares arithmetic
    # that reads none of the dropped keys, and the byte-match below is itself
    # the proof the filtered config is sufficient for it.
    import dataclasses

    valid = {f.name for f in dataclasses.fields(ScenarioConfig)}
    cfg = ScenarioConfig(
        **{k: v for k, v in rc["scenario_config"].items() if k in valid}
    )
    checks = []
    for entry in ref["steps"]:
        step = int(entry["step_year"])
        prior = STEP_PRIOR_SOLVE[step]
        dump = load_dump(bundle, prior, step)
        sig = dump["price_base_usd_mwh"] + dump["adder_usd_mwh"]
        prices = np.tile(sig[None, :], (7, 1))
        gas = float(entry["gas_price_per_mmbtu"])
        carbon = float(entry["carbon_price"])
        mine = thermal_margins(prices, gas, carbon, cfg, None)
        for tech in _THERMAL:
            want = entry["merchant"]["r_none"]["candidates"].get(tech)
            if want is None:
                continue
            got = round(mine[tech]["energy_margin_per_mw_yr"] / 1000.0, 2)
            checks.append(
                {
                    "step": step,
                    "tech": tech,
                    "ffr9b_energy_per_kw_yr": want["energy_rev_per_kw_yr"],
                    "replay_energy_per_kw_yr": got,
                    "match": abs(got - want["energy_rev_per_kw_yr"]) <= 0.05,
                }
            )
    return {"checks": checks, "all_match": all(c["match"] for c in checks)}


def _validate_storage_vs_phase0(shipped_steps: dict) -> dict:
    """Shipped-arm storage margins vs the committed phase-0 artifact (gate).

    Phase-0 ran at existing_storage_mw=0.0; capacity value is 0 in ERCOT
    either way, so only the (deployment-ceiling) budget could differ — the
    margins must agree to rounding.
    """
    ref = json.loads(
        (REPO / "results/calibration/entry_screen_t1h_phase0_ercot.json").read_text()
    )
    checks = []
    for step, body in shipped_steps.items():
        ref_year = ref["decision_years"].get(str(step))
        if ref_year is None:
            continue
        ref_rows = {r["tech"]: r for r in ref_year["storage_screen"]["techs"]}
        for tech, row in body["storage"]["techs"].items():
            want = ref_rows[tech]["margin_per_mw_yr"]
            got = row["margin_per_mw_yr"]
            checks.append(
                {
                    "step": int(step),
                    "tech": tech,
                    "phase0_margin": want,
                    "replay_margin": got,
                    "match": abs(got - want) <= max(1.0, 1e-5 * abs(want)),
                }
            )
    return {"checks": checks, "all_match": all(c["match"] for c in checks)}


def _validate_break_even_vs_phase0(
    config: ScenarioConfig, iso: str, step: int, existing_mw: float = 0.0
) -> dict:
    """Reproduce a committed phase-0 artifact's ``break_even`` rows (gate).

    CAISO's phase-0 artifact carries NO ``decision_years`` — it was produced
    before the L-5 gate existed, so the bundle had no
    ``screen_signal_diag_*.npz`` to replay (defect D-7) and only ``break_even``
    is populated. That block is therefore the ONLY committed overlap available
    as a gate, and it is a real one: its two columns are exactly the
    price-independent legs of this probe's storage stack — the model's own
    :func:`compute_storage_annual_cost` and :func:`estimate_capacity_value`.
    Reproducing them proves the cost/RA-credit half of the CAISO screen is
    being replayed at the run's own config before any dual-arm delta is read.

    ``existing_mw`` defaults to 0.0 because that is the basis phase-0 priced on
    (its ``--existing-storage-mw`` default). The RA credit tapers toward the
    per-ISO deployment ceiling, so passing the run's ACTUAL entering storage
    would compare two different quantities and fail the gate spuriously — the
    gate's job is to check the arithmetic, not the fleet state.
    """
    ref_path = (
        REPO / f"results/calibration/entry_screen_t1h_phase0_{iso.lower()}.json"
    )
    if not ref_path.exists():
        return {"checks": [], "all_match": True, "skipped": f"no {ref_path.name}"}
    ref = json.loads(ref_path.read_text())
    rows = {r["tech"]: r for r in ref["break_even"]["rows"]}
    checks = []
    for tech_name in STORAGE_TECHS:
        want = rows.get(tech_name)
        if want is None:
            continue
        got_cost = compute_storage_annual_cost(
            tech_name, step, config, cumulative_gw=None
        )
        got_cap = estimate_capacity_value(
            tech_name, existing_mw, config, iso, None, year=step
        )
        checks.append(
            {
                "tech": tech_name,
                "phase0_annual_cost": want["annual_cost_per_mw_yr"],
                "replay_annual_cost": round(got_cost, 1),
                "phase0_capacity_value": want["capacity_value_per_mw_yr"],
                "replay_capacity_value": round(got_cap, 1),
                "match": (
                    abs(got_cost - want["annual_cost_per_mw_yr"]) <= 1.0
                    and abs(got_cap - want["capacity_value_per_mw_yr"]) <= 1.0
                ),
            }
        )
    return {
        "checks": checks,
        "all_match": bool(checks) and all(c["match"] for c in checks),
        "break_even_step": step,
        "note": (
            "phase-0 break-even is priced at the probe's own decision step; a "
            "cost/credit vintage mismatch shows up here rather than silently "
            "in the margins"
        ),
    }


def main() -> None:
    """CLI entry point: emit both arms + deltas as one JSON artifact."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default=ISO, choices=sorted(ISO_STEPS))
    ap.add_argument("--bundle", default="results/hindcast/ercot-2021-2025-realized-t1h-refresh")
    ap.add_argument("--duals-bundle", default="results/calibration/ercot223_release_arm")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    iso = args.iso.upper()
    bundle = REPO / args.bundle
    duals_bundle = REPO / args.duals_bundle
    step_prior, step_driver = ISO_STEPS[iso]

    config = load_config(bundle)
    all_zone_names = list(get_iso_config(iso).zone_names)
    excluded = [z for z in ISO_DUAL_ZONE_EXCLUDE.get(iso, ()) if z in all_zone_names]
    zone_names = [z for z in all_zone_names if z not in excluded]

    result: dict = {
        "probe": "entry_signal_l1_dual_replay",
        "finding": "docs/FINDING-entry-screen-t1h-2026-08.md §7 L-1",
        "iso": iso,
        "bundle": str(args.bundle),
        "duals_bundle": str(args.duals_bundle),
        "cache_key": config.cache_key(),
        "zone_names": zone_names,
        "zones_excluded_from_both_arms": excluded,
        "cost_state": "entry seed (cumulative_gw=None), identical across arms",
        "steps": {},
    }

    # The step map is a CLAIM about which entering years this bundle priced.
    # Assert it against the dumps actually on disk, so a posture difference
    # (CAISO's unified-OFF bridge suppression) fails loudly instead of
    # silently reporting fewer steps than the reader expects.
    key_dirs = [p for p in sorted((bundle / iso).iterdir()) if p.is_dir()]
    if len(key_dirs) != 1:
        raise SystemExit(f"expected one cache key under {bundle / iso}")
    on_disk = sorted(
        (int(p.stem.split("_")[3]), int(p.stem.split("_")[5]))
        for p in key_dirs[0].glob("screen_signal_diag_*_for_*.npz")
    )
    claimed = sorted((prior, step) for step, prior in step_prior.items())
    if on_disk != claimed:
        raise SystemExit(
            f"{iso} step map {claimed} != dumps on disk {on_disk} — refuse to "
            "replay a step set the bundle did not produce"
        )

    for step, prior in step_prior.items():
        dump = load_dump(bundle, prior, step, iso)
        sig = dump["price_base_usd_mwh"] + dump["adder_usd_mwh"]
        adder = dump["adder_usd_mwh"]
        shipped = np.tile(sig[None, :], (len(zone_names), 1))
        storage_mw = float(dump["storage_power_mw"])
        gas = resolve_annual_gas_price(config, step_driver[step])
        carbon = resolve_carbon_price(config, step_driver[step])

        arms: dict = {}

        def one_arm(prices: np.ndarray, label: str) -> dict:
            return {
                "shape": shape_stats(prices),
                "thermal_r_none": thermal_margins(prices, gas, carbon, config, None),
                "thermal_r_dump_adder": thermal_margins(
                    prices, gas, carbon, config, adder
                ),
                "vre": vre_capture(prices, dump, config, step, zone_names, iso),
                "storage": storage_screen(prices, config, step, storage_mw, iso),
            }

        arms["shipped_signal"] = one_arm(shipped, "shipped")
        duals = dual_price_array(duals_bundle, prior, zone_names)
        if duals is not None:
            arms["dual_prior_solve"] = one_arm(duals, "dual")
        else:
            arms["dual_prior_solve"] = {
                "blocked": f"no committed hourly LP duals for prior solve {prior} "
                "(keeper sidecars span 2023-2025 only)"
            }
        if duals is None:
            same = dual_price_array(duals_bundle, step, zone_names)
            if same is not None:
                arms["dual_same_year"] = one_arm(same, "dual_same_year")
                arms["dual_same_year"]["caveat"] = (
                    "entering year's own realized model prices — foresight the "
                    "screen cannot have; diagnostic only, never the counterfactual"
                )
        body = {
            "prior_solve": prior,
            "driver_year": step_driver[step],
            "gas_price_per_mmbtu": round(float(gas), 4),
            "carbon_price": float(carbon),
            "storage_power_entering_mw": round(storage_mw, 1),
            "arms": arms,
        }
        # Delta block: sign flips + rank + capture, shipped vs whichever dual
        # arm exists for this step.
        for dual_label in ("dual_prior_solve", "dual_same_year"):
            d = arms.get(dual_label)
            if not d or "blocked" in d:
                continue
            s = arms["shipped_signal"]
            flips = {}
            for group, key in (("thermal_r_none", None), ("vre", None)):
                for tech, row in s[group].items():
                    if d[group].get(tech) and row["sign"] != d[group][tech]["sign"]:
                        flips[tech] = f"{row['sign']} -> {d[group][tech]['sign']}"
            for tech, row in s["storage"]["techs"].items():
                drow = d["storage"]["techs"].get(tech)
                if drow and row["sign"] != drow["sign"]:
                    flips[tech] = f"{row['sign']} -> {drow['sign']}"
            body[f"delta_{dual_label}"] = {
                "margin_sign_flips": flips,
                "storage_ranking_shipped": s["storage"]["ranking_by_margin"],
                "storage_ranking_dual": d["storage"]["ranking_by_margin"],
                "allocator_shipped": s["storage"]["allocator_result"],
                "allocator_dual": d["storage"]["allocator_result"],
                "capture_ratio_zone_row": {
                    t: {
                        "shipped": s["vre"][t]["capture_ratio_zone_row"],
                        "dual": d["vre"][t]["capture_ratio_zone_row"],
                    }
                    for t in s["vre"]
                    if t in d["vre"]
                },
            }
        result["steps"][str(step)] = body

    if iso == "ERCOT":
        # The two ERCOT gates are ERCOT-specific by construction (the FFR-9B
        # replay bundle and the ERCOT phase-0 decision_years), so they stay
        # bound to ERCOT rather than being generalized into vacuous no-ops.
        result["validation"] = {
            "thermal_vs_ffr9b": _validate_thermal_vs_ffr9b(),
            "storage_vs_phase0": _validate_storage_vs_phase0(
                {
                    s: {"storage": b["arms"]["shipped_signal"]["storage"]}
                    for s, b in result["steps"].items()
                }
            ),
        }
    else:
        result["validation"] = {
            "break_even_vs_phase0": _validate_break_even_vs_phase0(
                config, iso, min(step_prior)
            )
        }

    out_path = REPO / args.out if not Path(args.out).is_absolute() else Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1, sort_keys=False) + "\n")
    ok = all(v["all_match"] for v in result["validation"].values())
    print(f"wrote {out_path}  validation_all_match={ok}")
    if not ok:
        raise SystemExit("validation gates FAILED — deltas are not reportable")


if __name__ == "__main__":
    main()

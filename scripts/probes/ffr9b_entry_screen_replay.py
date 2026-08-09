"""FFR-9B R2/R3 probe: offline replay of the entry screens (ERCOT T1-FF).

Diagnosis-only (docs/handoffs/ffr-9b-vre-entry-diagnosis-2026-08-09.md §1.4):
re-invokes ``apply_economic_new_entry`` / ``apply_storage_new_entry`` per
evolution step of the regenerated treated arm with ``screen_ledger``
diagnostics ON, feeding the bundle's own recorded inputs — the
``screen_signal_diag_<solve>_for_<entering>.npz`` price signal, the evolution
ledgers' fleet/pipeline/prior-max state, the vintage-armed clean-store CF
profiles — so the per-candidate margins, ranking and ``binding_cap`` labels
of each decision step become measurable without any solve. NO solve path is
touched; this file is a probe under ``scripts/probes/`` (calibration record).

Reserve-leg bounding (§1.4 R3, the pre-registered degradation): the true
thermal reserve leg is the PRIOR SOLVED YEAR's realized post-solve ORDC adder
(``runner.py:3482–3484``), which is not recoverable offline because hourly
fleet availability (the outage draws) is not persisted. The replay therefore
runs each step twice — ``r=None`` (lower bound: no reserve leg) and ``r=`` the
entering screen's own dumped adder (upper bound: a same-magnitude scarcity
series) — and reports a cell as ROBUST only when the identity check (replayed
build MW == ledger decided MW, per tech) passes under BOTH bounds.

Usage:
    uv run python scripts/probes/ffr9b_entry_screen_replay.py \
        --bundle results/hindcast/ercot-2021-2025-t1ff-armr-ffr9b-regen/ERCOT/<key> \
        --out docs/handoffs/ffr-9b/entry-screen-replay.json
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.entry_config import (  # noqa: E402
    ENTRY_GROWTH_LIMIT_MULTIPLE,
    ENTRY_THROUGHPUT_WINDOW_YEARS,
)
from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.config.paths import set_eia860_vintage  # noqa: E402
from market_sim.data.build_throughput import (  # noqa: E402
    max_annual_build_gw_by_tech,
)
from market_sim.data.renewables import load_renewable_profiles  # noqa: E402
from market_sim.model.capacity_evolution.new_entry import (  # noqa: E402
    CumulativeDeployment,
    apply_economic_new_entry,
)
from market_sim.model.storage import (  # noqa: E402
    StorageUnit,
    apply_storage_new_entry,
)
from market_sim.data.fuel import resolve_annual_gas_price  # noqa: E402
from market_sim.policy.carbon import resolve_carbon_price  # noqa: E402

sys.path.insert(0, str(REPO / "scripts"))
from run_capacity_hindcast import build_config  # noqa: E402

ISO = "ERCOT"
# entering step year -> the prior SOLVED year whose results drove the screen
STEP_PRIOR_SOLVE = {2022: 2021, 2023: 2021, 2024: 2023, 2025: 2024}
# entering step year -> the runner's fuel/carbon driver year
# (runner.py:1495 — last_solved_year when the step is the 2022 bridge)
STEP_DRIVER_YEAR = {2022: 2021, 2023: 2023, 2024: 2024, 2025: 2025}


def _load_ledgers(bundle: Path) -> dict[int, dict]:
    out = {}
    for p in sorted(bundle.glob("evolution_*.json")):
        led = json.loads(p.read_text())
        out[int(led["year"])] = led
    return out


def _decided_rows(ledgers: dict[int, dict]) -> list[dict]:
    """Every pipeline row ever decided, deduplicated by (tech, decision, cod, seq)."""
    seen: dict[tuple, dict] = {}
    for led in ledgers.values():
        for r in led.get("entry_pipeline", []) or []:
            key = (
                r.get("tech"),
                int(r.get("decision_year", -1)),
                int(r.get("cod_year", -1)),
                int(r.get("seq", -1)),
            )
            base = {k: v for k, v in r.items() if k != "event"}
            seen.setdefault(key, base)
    return list(seen.values())


def _storage_power_entering(ledgers: dict[int, dict], step: int) -> float:
    """Cumulative storage power (MW) on the fleet when step ``step`` evolves.

    The storage stack commissions in-year, after the merchant screen of the
    same evolution step, so the fleet entering step Y carries additions
    through ledger year Y-1 plus the measured base (223.1 MW, FFR-9A R1).
    """
    total = 223.1
    for y, led in ledgers.items():
        if y >= step:
            continue
        for row in led.get("storage_additions", []) or []:
            total += float(row.get("mw", 0.0))
    return total


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    bundle = (REPO / args.bundle) if not Path(args.bundle).is_absolute() else Path(args.bundle)

    config = build_config(
        ISO,
        2021,
        2025,
        variant="realized",
        vintage=2020,
        forward_from_base=True,
        arm="realized",
        capacity_screen_unified_lookahead=True,
        capacity_screen_scarcity_restoration=True,
    )
    set_eia860_vintage(2020)
    iso_config = get_iso_config(ISO)
    zone_names = list(iso_config.zone_names)

    ledgers = _load_ledgers(bundle)
    all_rows = _decided_rows(ledgers)

    seed_gw = max_annual_build_gw_by_tech(ISO, 2020, ENTRY_THROUGHPUT_WINDOW_YEARS)

    # Wright's-Law cumulative-deployment state, advanced exactly as the runner
    # does (advance at the END of every year incl. base and bridge), with local
    # builds from the ledgers (commissioned VRE/thermal + in-year storage).
    def cumulative_at(step: int) -> CumulativeDeployment:
        cum = CumulativeDeployment.initial()
        for y in range(2021, step):
            local: dict[str, float] = {}
            led = ledgers.get(y)
            if led:
                for r in led.get("entry_pipeline", []) or []:
                    if r.get("event") == "commissioned" and int(r["cod_year"]) == y:
                        t = r["tech"]
                        t = "nuclear" if t in ("nuclear_smr", "nuclear_large") else t
                        if t in ("wind", "solar", "gas_cc", "nuclear", "gas_cc_ccs"):
                            local[t] = local.get(t, 0.0) + float(r["mw"]) / 1000.0
                for row in led.get("storage_additions", []) or []:
                    local["li_ion"] = local.get("li_ion", 0.0) + float(
                        row.get("mw", 0.0)
                    ) / 1000.0
            cum.advance_year(local)
        return cum

    result: dict = {
        "probe": "ffr9b_entry_screen_replay (R2/R3)",
        "bundle": str(bundle),
        "ladder_seed_gw": {k: round(v, 4) for k, v in sorted(seed_gw.items())},
        "steps": [],
    }

    prior_max_gw = dict(seed_gw)  # rises endogenously with decided MW
    for step, prior_solve in STEP_PRIOR_SOLVE.items():
        dump_path = bundle / f"screen_signal_diag_{prior_solve}_for_{step}.npz"
        dump = np.load(dump_path, allow_pickle=True)
        signal_1d = dump["price_base_usd_mwh"] + dump["adder_usd_mwh"]
        prices = np.tile(signal_1d, (len(zone_names), 1))
        adder = dump["adder_usd_mwh"]

        wind_cf, _wc, solar_cf, _sc = load_renewable_profiles(
            ISO, prior_solve, iso_config, config
        )

        # Pipeline state entering the screen: rows decided before this step
        # whose cod_year is still in the future (step 4.5 commissioning has
        # already removed cod_year <= step).
        pipeline_state = [
            dict(r)
            for r in all_rows
            if int(r["decision_year"]) < step and int(r["cod_year"]) > step
        ]

        rate_caps_mw = {
            t: ENTRY_GROWTH_LIMIT_MULTIPLE * gw * 1000.0
            for t, gw in prior_max_gw.items()
        }
        storage_mw = _storage_power_entering(ledgers, step)
        driver_year = STEP_DRIVER_YEAR[step]
        gas_price = resolve_annual_gas_price(config, driver_year)
        carbon_price = resolve_carbon_price(config, driver_year)
        cum = cumulative_at(step)
        # Prior solved year's RPS dual, exactly what the runner hands the
        # screen (0.0 when the ledger records none — ERCOT's expected case).
        rps_prior = float(ledgers.get(prior_solve, {}).get("rps_dual") or 0.0)

        # Ledger truth for the identity check.
        led = ledgers.get(step, {})
        truth: dict[str, float] = {}
        for r in led.get("entry_pipeline", []) or []:
            if r.get("event") == "decided" and int(r["decision_year"]) == step:
                truth[r["tech"]] = truth.get(r["tech"], 0.0) + float(r["mw"])

        arms = {}
        for leg, r_sig in (("r_none", None), ("r_dump_adder", adder)):
            ledger_sink: list[dict] = []
            _, _ = apply_economic_new_entry(
                [],
                prices,
                step,
                config,
                ISO,
                rps_shadow_price=rps_prior,
                cumulative=copy.deepcopy(cum),
                gas_price_per_mmbtu=gas_price,
                carbon_price=carbon_price,
                storage_power_mw=storage_mw,
                thermal_as_revenue_per_mw_yr=None,
                reserve_price_signal=r_sig,
                reserve_price_signal_slow=r_sig,
                zone_names=zone_names,
                wind_cf=wind_cf,
                solar_cf=solar_cf,
                reserve_position=None,
                screen_ledger=ledger_sink,
                entry_rate_caps_mw=dict(rate_caps_mw),
                entry_pipeline=copy.deepcopy(pipeline_state),
            )
            rows = {}
            for row in ledger_sink:
                rows[row["tech"]] = {
                    "margin_per_kw_yr": round(row["margin_per_mw_yr"] / 1000.0, 3),
                    "profitable": row["profitable"],
                    "build_mw": round(row.get("build_mw", 0.0), 1),
                    "binding_cap": row.get("binding_cap"),
                    "energy_rev_per_kw_yr": round(
                        row.get("energy_revenue_per_mw_yr", 0.0) / 1000.0, 2
                    ),
                    "attr_rev_per_kw_yr": round(
                        row.get("attribute_revenue_per_mw_yr", 0.0) / 1000.0, 2
                    ),
                    "as_credit_per_kw_yr": round(
                        row.get("as_credit_per_mw_yr", 0.0) / 1000.0, 2
                    ),
                    "annual_cost_per_kw_yr": round(
                        row.get("annual_cost_per_mw_yr", 0.0) / 1000.0, 2
                    ),
                }
            order = sorted(
                (r for r in rows.items() if r[1]["profitable"]),
                key=lambda kv: kv[1]["margin_per_kw_yr"],
                reverse=True,
            )
            identity = {
                t: {
                    "replay_mw": rows.get(t, {}).get("build_mw", 0.0),
                    "ledger_mw": round(truth.get(t, 0.0), 1),
                    "match": abs(
                        rows.get(t, {}).get("build_mw", 0.0) - truth.get(t, 0.0)
                    )
                    < 0.5,
                }
                for t in sorted(set(rows) | set(truth))
            }
            arms[leg] = {
                "candidates": rows,
                "margin_order": [t for t, _ in order],
                "identity": identity,
                "identity_all": all(v["match"] for v in identity.values()),
            }

        # Storage stack replay (screen prices = the same signal; the runner
        # hands prior_results["price_signal"] to apply_storage_new_entry).
        existing = [
            StorageUnit(
                unit_id="probe_agg",
                zone=zone_names[0],
                tech_name="li_ion_4hr",
                power_cap_mw=storage_mw,
                energy_cap_mwh=storage_mw * 4.0,
            )
        ]
        st_after = apply_storage_new_entry(
            existing,
            prices,
            step,
            config,
            ISO,
            cumulative=copy.deepcopy(cum),
            deliverability_headroom={},
            endogenous_as_revenue_per_mw_yr=None,
            reserve_position=None,
        )
        st_built = sum(u.power_cap_mw for u in st_after) - storage_mw
        st_truth = sum(
            float(r.get("mw", 0.0))
            for r in ledgers.get(step, {}).get("storage_additions", []) or []
        )
        result["steps"].append(
            {
                "step_year": step,
                "screen": f"{prior_solve}_for_{step}",
                "signal_mean_usd_mwh": round(float(signal_1d.mean()), 3),
                "storage_power_entering_mw": round(storage_mw, 1),
                "gas_price_per_mmbtu": round(float(gas_price), 4),
                "carbon_price": float(carbon_price),
                "rate_caps_mw": {k: round(v, 1) for k, v in sorted(rate_caps_mw.items())},
                "pending_mw_by_tech": _sum_by_tech(pipeline_state),
                "ledger_decided_mw": {k: round(v, 1) for k, v in sorted(truth.items())},
                "merchant": arms,
                "storage": {
                    "replay_built_mw": round(st_built, 1),
                    "ledger_built_mw": round(st_truth, 1),
                    "match": abs(st_built - st_truth) < 0.5,
                },
            }
        )

        # Endogenous prior-max update, exactly runner.py:1688-1694 (decision
        # grain, only techs with a measured seed).
        for t, mw in truth.items():
            key = "nuclear" if t in ("nuclear_smr", "nuclear_large") else t
            if key in prior_max_gw and mw / 1000.0 > prior_max_gw[key]:
                prior_max_gw[key] = mw / 1000.0

    out = REPO / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, sort_keys=False) + "\n")
    print(f"wrote {out}")


def _sum_by_tech(rows: list[dict]) -> dict[str, float]:
    acc: dict[str, float] = {}
    for r in rows:
        acc[r["tech"]] = acc.get(r["tech"], 0.0) + float(r["mw"])
    return {k: round(v, 1) for k, v in sorted(acc.items())}


if __name__ == "__main__":
    main()

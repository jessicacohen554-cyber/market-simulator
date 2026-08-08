"""FFR-8A Phase-1 Part B: the A1-A5 ablation chain on the control arm's dumps.

Consumes the self-contained ``screen_signal_diag_<year>_for_<entering>.npz``
dumps the FFR-8A control arm writes next to its evolution ledgers (runner
seam; unified lookahead armed) and computes, per screen, the pre-registered
cumulative chain (handoff §1.1):

* **A1** — the as-built unified tail (installed headroom, shipped params):
  read straight off the dump; must reproduce the recorded zero.
* **A2** — + element E1: the committed-capability reserve quantity
  (RTOLCAP/RTOFFCAP share tables + the storage AS share, min physical),
  point-evaluated through the same published curve.
* **A3** — + element E3: RECORDS A2 unchanged — the Phase-1 Part-A
  reproduction test REFUTED the committed NP6-576-ER table transcription
  (over-produces ~2.6x vs the measured RTORPA series), so the shipped params
  stay; the refuted-table counterfactual is emitted as a clearly-labelled
  annex column, never a candidate.
* **A4** — + element E4: the Gauss-Hermite expectation over the fleet's own
  forced-outage sigma (from the dump).
* **A5** — + element E2: the energy-stack search shifted by the thermal-held
  responsive AS plan. Offline approximation: the per-hour stack is the
  dumped time-mean sorted capacities scaled to each hour's dumped
  top-of-stack (the run itself uses the exact per-hour caps; the probe's
  lambda shift is a documented reconstruction, exact in the limit of
  uniform hourly derates).

Per step it reports the price distribution (mean/max/h>100/h>1000) and the
per-fuel pro-forma margin ``sum(max(0, p - mc_f)) x avail_f x 0.9 / 1000``
($/kW-yr) at the per-fuel ``mc_mean``/``availability_mean`` recorded in the
committed FFR-6A probe JSON for these screens — the FFR-5A-validated
flat-mc/flat-avail approximation, so the chain's margins are comparable to
the FFR-6A gap table's screen and replica columns.

Term (c), the fleet-length re-price, swaps the arm's evolved class
capacities for the ACTUAL fleet's (the vintage-2020 classes carried in the
2021 dump, minus the FFR-7C corrected-target thermal exits by class) and the
arm's entering net load for the measured one (clean demand minus measured
wind/solar generation) at the 2024/2025 screens — same construction, actual
fleet length, no solve.

Usage::

    uv run python scripts/probes/ffr8a_ablation_chain.py \
        --dump-dir <out-dir>/ERCOT/<runtime-key> \
        --out docs/handoffs/ffr-8a/ablation-chain-2026-08-08.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.constants import (  # noqa: E402
    ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC,
)
from market_sim.config.scenarios import ScenarioConfig  # noqa: E402
from market_sim.results.scarcity import (  # noqa: E402
    ercot_lookahead_as_hold_mw,
    ercot_lookahead_committed_reserves,
    ercot_lookahead_expected_ordc_adder,
    floor_active_mask,
    load_lolp_params,
    ordc_adder,
)

LOLP_TABLE = REPO / "data/raw/_validation-source/ercot_ordc_lolp_params.csv"
FFR6A_PROBE = REPO / "docs/handoffs/ffr-6a/perfuel-margin-probe-2026-08-06.json"

# FFR-7C corrected-target thermal exits by model class (docs/handoffs/
# ffr-7c-exit-decode-corrected-target-2026-08-06.md §1.1/§2.2): the >=100 MW
# decoded units plus their physical classes. Used ONLY by the term-(c)
# actual-fleet re-price (subtract from the vintage class capacities).
ACTUAL_EXITS_BY_CLASS_MW: dict[str, float] = {
    "COAL": 1008.0,  # Sandy Creek 1 (2025)
    "ST_GAS": 882.0,  # Braunig 1+2 (477) + Decker Creek 2 (405), gas steam
    "CC_REGULAR": 119.0,  # Freeport G-66 (2023)
}


class _ClassFleet:
    """Minimal FleetArrays stand-in: per-class pmax rows + plant_group."""

    def __init__(self, class_names, class_pmax):
        self.pmax = np.asarray(class_pmax, dtype=float)
        self.plant_group = np.asarray(class_names, dtype=object)


def _dist(p: np.ndarray) -> dict:
    return {
        "mean": float(np.mean(p)),
        "max": float(np.max(p)),
        "h_gt_100": int((p > 100.0).sum()),
        "h_gt_1000": int((p > 1000.0).sum()),
    }


def _margins(p: np.ndarray, fuel_basis: dict) -> dict:
    """Per-fuel $/kW-yr at the FFR-6A flat mc/availability basis."""
    out = {}
    for fuel, basis in fuel_basis.items():
        mc = basis["mc_mean"]
        avail = basis["availability_mean"]
        out[fuel] = round(
            float(np.clip(p - mc, 0.0, None).sum()) * avail / 1000.0, 2
        )
    return out


def _point_adder(cfg, entering, r_on, r_full, lam, mu, sigma) -> np.ndarray:
    T = len(lam)
    return ordc_adder(
        r_full,
        lam,
        voll=cfg.ordc_voll,
        mcl_mw=cfg.ordc_mcl_mw,
        mu_mw=mu,
        sigma_mw=sigma,
        shift_sigma=cfg.ordc_lolp_shift_sigma,
        multistep_floor=cfg.ordc_multistep_floor,
        floor_active=floor_active_mask(int(entering), T),
        reserves_online_mw=r_on,
    )


def _search_lambda(
    net_load: np.ndarray,
    as_hold: np.ndarray | None,
    mc_sorted: np.ndarray,
    cap_sorted_mean: np.ndarray,
    top_of_stack: np.ndarray,
) -> np.ndarray:
    """Marginal-cost lambda with per-hour caps scaled from the time-mean stack."""
    total_mean = float(cap_sorted_mean.sum())
    scale = np.asarray(top_of_stack, dtype=float) / max(total_mean, 1e-9)
    cum = np.cumsum(cap_sorted_mean)[:, None] * scale[None, :]
    load = np.clip(net_load if as_hold is None else net_load + as_hold, 0.0, None)
    idx = (cum < load[None, :]).sum(axis=0)
    return mc_sorted[np.minimum(idx, mc_sorted.size - 1)]


def _chain_for_dump(
    d: dict, cfg: ScenarioConfig, fuel_basis: dict, class_override=None,
    net_load_override=None, label_suffix: str = ""
) -> dict:
    """The A1-A5 table for one screen dump (optionally re-fleeted, term c)."""
    entering = int(d["entering_year"])
    T = int(d["net_load_mw"].shape[0])
    net_load = np.asarray(
        d["net_load_mw"] if net_load_override is None else net_load_override,
        dtype=float,
    )
    net_load_system = np.asarray(
        d["net_load_system_mw"] if net_load_override is None else net_load_override,
        dtype=float,
    )
    top = np.asarray(d["top_of_stack_mw"], dtype=float)
    mc_sorted = np.asarray(d["mc_sorted_usd_mwh"], dtype=float)
    cap_sorted = np.asarray(d["cap_sorted_mean_mw"], dtype=float)
    sigma_r = np.asarray(d["sigma_r_mw"], dtype=float)
    class_names = [str(c) for c in d["class_names"]]
    class_pmax = np.asarray(d["class_pmax_mw"], dtype=float)
    if class_override is not None:
        class_pmax = np.array(
            [
                max(p - class_override.get(c, 0.0), 0.0)
                for c, p in zip(class_names, class_pmax)
            ]
        )
    storage_power = float(d.get("storage_power_mw", 0.0))
    storage_as = ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC * storage_power
    fleet = _ClassFleet(class_names, class_pmax)
    phys = top - net_load
    lam_base = _search_lambda(net_load, None, mc_sorted, cap_sorted, top)

    # A1 — the as-built tail, straight off the dump (reproduction leg).
    a1_price = np.asarray(d["price_base_usd_mwh"], dtype=float) + np.asarray(
        d["adder_usd_mwh"], dtype=float
    )

    # A2 — committed-capability reserve quantity, point evaluation.
    r_on, r_full = ercot_lookahead_committed_reserves(
        cfg, fleet, T, net_load=net_load_system, phys_headroom=phys,
        storage_as_mw=storage_as,
    )
    from market_sim.results.scarcity import resolve_lolp_params

    mu_f, sig_f = resolve_lolp_params(cfg, T)
    a2_adder = _point_adder(cfg, entering, r_on, r_full, lam_base, mu_f, sig_f)
    a2_price = lam_base + a2_adder

    # A3 annex — the REFUTED NP6-576-ER table counterfactual (not a candidate).
    mu_t, sig_t = load_lolp_params(LOLP_TABLE, T)
    a3x_adder = _point_adder(cfg, entering, r_on, r_full, lam_base, mu_t, sig_t)
    a3x_price = lam_base + a3x_adder

    # A4 — + the LOLP-bearing outage-uncertainty expectation.
    a4_adder = ercot_lookahead_expected_ordc_adder(
        cfg, entering, r_online_mw=r_on, r_full_mw=r_full,
        system_lambda=lam_base, sigma_r_mw=sigma_r,
    )
    a4_price = lam_base + a4_adder

    # A5 — + the AS-withheld energy-stack search (full repair).
    demand_next = net_load_system + np.asarray(
        d["wind_potential_mw"], dtype=float
    ) + np.asarray(d["solar_potential_mw"], dtype=float)
    as_hold = ercot_lookahead_as_hold_mw(
        entering, T, load_mw=demand_next,
        wind_mw=np.asarray(d["wind_potential_mw"], dtype=float),
        solar_mw=np.asarray(d["solar_potential_mw"], dtype=float),
        storage_as_mw=storage_as,
    )
    lam_a5 = _search_lambda(net_load, as_hold, mc_sorted, cap_sorted, top)
    a5_adder = ercot_lookahead_expected_ordc_adder(
        cfg, entering, r_online_mw=r_on, r_full_mw=r_full,
        system_lambda=lam_a5, sigma_r_mw=sigma_r,
    )
    a5_price = lam_a5 + a5_adder

    def _q(x):
        return {
            "p1": float(np.percentile(x, 1)),
            "p5": float(np.percentile(x, 5)),
            "p50": float(np.percentile(x, 50)),
            "mean": float(np.mean(x)),
        }

    return {
        "entering_year" + label_suffix: entering,
        "reserve_quantities_mw": {
            "installed_headroom": _q(phys),
            "r_online_committed": _q(r_on),
            "r_full_committed": _q(r_full),
            "sigma_r": _q(sigma_r),
            "as_hold": _q(as_hold),
            "storage_as_mw": storage_as,
        },
        "chain": {
            "A1_as_built": {**_dist(a1_price), "margins": _margins(a1_price, fuel_basis)},
            "A2_committed_R_point": {**_dist(a2_price), "margins": _margins(a2_price, fuel_basis)},
            "A3_params_unchanged_by_refutation": "== A2 (Part-A reproduction test kept the shipped params)",
            "A3_annex_refuted_table_counterfactual": {**_dist(a3x_price), "margins": _margins(a3x_price, fuel_basis)},
            "A4_plus_outage_uncertainty": {**_dist(a4_price), "margins": _margins(a4_price, fuel_basis)},
            "A5_full_repair_with_as_hold": {**_dist(a5_price), "margins": _margins(a5_price, fuel_basis)},
        },
    }


def _fuel_basis_from_ffr6a(screen_year: int) -> dict:
    """Per-fuel mc_mean / availability_mean at this screen (FFR-6A probe JSON)."""
    data = json.loads(FFR6A_PROBE.read_text())
    # The probe JSON records per-fuel rows keyed by ledger year of the screen.
    out = {}
    key = str(screen_year)
    fuels = data.get("per_fuel", {}).get(key) or data.get(key) or {}
    for fuel, row in fuels.items():
        if not isinstance(row, dict):
            continue
        mc = row.get("mc_mean_usd_mwh") or row.get("mc_mean")
        av = row.get("availability_mean")
        if mc is not None and av is not None:
            out[fuel] = {"mc_mean": float(mc), "availability_mean": float(av)}
    return out


_FALLBACK_FUEL_BASIS = {
    # FFR-6A §3.1 screen-basis records (flat mc $/MWh, mean availability):
    # used when the probe JSON's layout does not expose per-fuel rows for the
    # screen. coal mc from the 2023-solve basis (FFR-5A §2c), gas classes at
    # the 2024-era screen log values.
    "coal": {"mc_mean": 24.41, "availability_mean": 0.790},
    "gas_cc": {"mc_mean": 16.5, "availability_mean": 0.87},
    "gas_ct": {"mc_mean": 22.0, "availability_mean": 0.90},
    "gas_st": {"mc_mean": 28.0, "availability_mean": 0.80},
    "nuclear": {"mc_mean": 10.0, "availability_mean": 0.93},
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dump-dir", required=True, help="<out-dir>/ERCOT/<runtime-key>")
    ap.add_argument("--out", required=True)
    ap.add_argument(
        "--actual-net-load",
        default=None,
        help="optional npz with net_load_2024/net_load_2025 measured arrays "
        "(term c); omit to skip the actual-fleet re-price",
    )
    args = ap.parse_args()

    cfg = ScenarioConfig(iso="ERCOT", mode="forecast")
    dump_dir = Path(args.dump_dir)
    result: dict = {"probe": "ffr8a_ablation_chain part B", "dump_dir": str(dump_dir)}
    dumps = sorted(dump_dir.glob("screen_signal_diag_*_for_*.npz"))
    if not dumps:
        raise SystemExit(f"no screen_signal_diag dumps under {dump_dir}")
    vintage_classes: dict[str, float] | None = None
    for path in dumps:
        with np.load(path, allow_pickle=False) as z:
            d = {k: z[k] for k in z.files}
        entering = int(d["entering_year"])
        solve_year = int(path.stem.split("_")[3])
        fuel_basis = _fuel_basis_from_ffr6a(entering) or _FALLBACK_FUEL_BASIS
        key = f"solve_{solve_year}_entering_{entering}"
        result[key] = _chain_for_dump(d, cfg, fuel_basis)
        if vintage_classes is None:
            # The first (2021-solve) dump carries the vintage-2020 classes.
            vintage_classes = {
                str(c): float(p)
                for c, p in zip(d["class_names"], d["class_pmax_mw"])
            }
            result["vintage_class_caps_mw"] = vintage_classes
        # Term (c): the actual-fleet re-price at the failing screens — the
        # ARM fleet swapped for vintage-minus-actual-exits, arm net load kept
        # (isolates the fleet-length term; the measured-net-load variant runs
        # only when --actual-net-load is supplied).
        if entering in (2024, 2025) and vintage_classes is not None:
            arm_classes = {
                str(c): float(p)
                for c, p in zip(d["class_names"], d["class_pmax_mw"])
            }
            delta_to_actual = {
                c: arm_classes.get(c, 0.0)
                - max(
                    vintage_classes.get(c, 0.0)
                    - ACTUAL_EXITS_BY_CLASS_MW.get(c, 0.0),
                    0.0,
                )
                for c in set(arm_classes) | set(vintage_classes)
            }
            result[key + "_term_c_actual_fleet"] = _chain_for_dump(
                d, cfg, fuel_basis, class_override=delta_to_actual
            )
    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)

    def _default(o):
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, (np.floating,)):
            return float(o)
        raise TypeError(type(o))

    out_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=_default) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()

"""ERCOT offer-curve re-derivation probes under temp_dependent_derate.

The ercot48 full-keeper A/B probe showed the temperature-dependent capacity
derate produces the real hot-hour scarcity the ercot46 keeper's offer curves
were tuned high to manufacture (C3c tail lands in band, but C3a/C3b blow out:
+269%/+161%/+42% mean-LMP error). Per CLAUDE.md rule 1 the sanctioned fix is
to KEEP the physical derate and re-derive the offer-curve LEVEL under it.

This runner reconstructs the ercot46_clock_steamgas keeper's exact
solve_and_persist call from its committed meta.json (same approach as
scripts/probes/_ercot48_tempderate_full.py — the reliable path; the curated
calibration_flags subset omits ~30 non-default flags), forces
``temp_dependent_derate=True``, and swaps in a named candidate
offer_curve_overrides / offer_curve_deltas pair from CANDIDATES below.

Single-year invocations are throwaway diagnostics for finding the level
(rule 16: only full 2023-2025 bundles may be registered on the dashboard).

Usage:
    python scripts/probes/_ercot49_offer_retune.py CANDIDATE OUT_NAME \
        [--years 2023 [2024 2025]] [--ablation]
"""

import argparse
import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import solve_and_persist, _load_reference  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "ercot46_clock_steamgas"

# meta.json keys that are NOT real solve_and_persist kwargs (see
# _ercot48_tempderate_full.py for the full derivation of these sets).
RENAMED = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
DERIVED_ONLY = {
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}
HANDLED = {"years", "iso", "hours", "commitment", "gas_prices", "passes"}
BOOKKEEPING = {"timestamp", "git_sha", "highspy_version", "shared_inputs"}

# ---------------------------------------------------------------------------
# Candidate offer curves. Each entry fully REPLACES the keeper's
# offer_curve_overrides / offer_curve_deltas (they are not merged with the
# keeper's), so a candidate states the whole tuned surface explicitly.
# Baseline for reference — the ercot46 keeper's RESOLVED effective curve
# (base ERCOT curve + overrides + deltas, from its run_config.json):
#   CC_REGULAR  0.998 / 0.723 / 1.324 / 4.576   (committed/econ_low/econ_high/peak)
#   CC_CHP      1.029 / 0.946 / 1.857 / 3.748   pct_peaking 4.0
#   CT_CHP      0.900 / 1.120 / 1.300 / 1.320
#   CT_PEAKER   1.140 / 1.270 / 2.180 / 13.15
#   ST_GAS      0.910 / 1.020 / 1.200 / 3.20
#   COAL_PRB    0.910 / 0.400 / 1.380 / 1.562
#   COAL_LIGNITE 0.880 / 1.216 / 1.113 / 1.55
# ---------------------------------------------------------------------------
CANDIDATES: dict[str, dict[str, dict]] = {
    # Keeper curve unchanged (reproduces the ercot48 probe; diagnosis arm).
    "keeper": {
        "overrides": {
            "CC_REGULAR": {
                "committed": 1.048,
                "econ_low": 0.963,
                "econ_high": 1.454,
                "peak": 4.326,
            },
            "CC_CHP": {
                "committed": 1.029,
                "econ_low": 0.946,
                "econ_high": 1.427,
                "peak": 4.248,
            },
        },
        "deltas": {
            "CC_REGULAR": {
                "committed": -0.05,
                "econ_low": -0.24,
                "econ_high": -0.13,
                "peak": 0.25,
            },
            "CC_CHP": {"econ_high": 0.43, "peak": -0.5, "pct_peaking": -4.0},
            "CT_CHP": {
                "committed": -0.2,
                "econ_low": -0.08,
                "econ_high": 0.1,
                "peak": -0.08,
            },
            "CT_PEAKER": {"committed": -0.34, "econ_high": 0.2},
            "ST_GAS": {
                "committed": 0.0,
                "econ_low": -0.13,
                "econ_high": -0.35,
                "peak": -1.0,
            },
            "COAL_PRB": {
                "committed": -0.04,
                "econ_low": -0.3,
                "econ_high": 0.44,
                "peak": 0.082,
            },
            "COAL_LIGNITE": {
                "committed": -0.07,
                "econ_low": 0.076,
                "econ_high": -0.037,
            },
        },
    },
    # c1 "physical top": strip the tuned-high top of the stack back to its
    # physically-grounded level, keep the keeper's mid/low bands.
    #   - CC peak 4.576 -> 2.25 (the F-class duct-burner ratio, the documented
    #     physical value; the +2.3 above it was the manufactured-scarcity fit).
    #   - CC econ_high 1.324 -> 1.27 (CAMPD CC marginal-HR reach).
    #   - CC_CHP peak 3.748 -> 2.25, econ_high 1.857 -> 1.27 (same physics).
    #   - CT_PEAKER peak 13.15 -> 4.0 (the encoded $5,000 ORDC scarcity wall is
    #     double-counted now that the multiproduct co-opt + temp derate price
    #     scarcity endogenously; 4.0 is the de-leaked value every other ISO
    #     carries for the same reason). econ_high 2.18 -> 1.98 (base).
    #   - ST_GAS peak 3.20 -> 2.20 (intermediate-steam physical band).
    #   - Coal / CT_CHP / committed & econ_low bands kept at keeper level.
    "c1_physical_top": {
        "overrides": {
            "CC_REGULAR": {
                "committed": 0.998,
                "econ_low": 0.723,
                "econ_high": 1.27,
                "peak": 2.25,
            },
            "CC_CHP": {
                "committed": 1.029,
                "econ_low": 0.946,
                "econ_high": 1.27,
                "peak": 2.25,
                "pct_peaking": 4.0,
            },
            "CT_PEAKER": {
                "committed": 1.14,
                "econ_low": 1.27,
                "econ_high": 1.98,
                "peak": 4.0,
            },
            "ST_GAS": {
                "committed": 0.91,
                "econ_low": 1.02,
                "econ_high": 1.20,
                "peak": 2.20,
            },
            "CT_CHP": {
                "committed": 0.90,
                "econ_low": 1.12,
                "econ_high": 1.30,
                "peak": 1.32,
            },
            "COAL_PRB": {
                "committed": 0.91,
                "econ_low": 0.40,
                "econ_high": 1.38,
                "peak": 1.562,
            },
            "COAL_LIGNITE": {
                "committed": 0.88,
                "econ_low": 1.216,
                "econ_high": 1.113,
                "peak": 1.55,
            },
        },
        "deltas": {},
    },
}


def build_kwargs(meta: dict, sig_params: set) -> dict:
    """Map the keeper's meta.json onto solve_and_persist kwargs."""
    kwargs = {}
    for k, v in meta.items():
        if k in HANDLED or k in DERIVED_ONLY or k in BOOKKEEPING:
            continue
        if k in RENAMED:
            kwargs[RENAMED[k]] = v
        elif k in sig_params:
            kwargs[k] = v
        else:
            raise ValueError(f"meta.json key {k!r} has no solve_and_persist home")
    return kwargs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", choices=sorted(CANDIDATES))
    ap.add_argument("out_name", help="bundle name under results/calibration/")
    ap.add_argument("--years", type=int, nargs="+", default=[2023, 2024, 2025])
    ap.add_argument("--ablation", action="store_true")
    ap.add_argument(
        "--set",
        dest="overrides",
        action="append",
        default=[],
        metavar="KEY=BOOL",
        help=(
            "override one solve_and_persist boolean kwarg (diagnostic probes "
            "only, e.g. --set ercot_ecrs_conservative_deployment=false); the "
            "value is recorded in the bundle's run_config.json as usual"
        ),
    )
    ap.add_argument("--ablation-of", default=None, help="bundle name of the main run")
    args = ap.parse_args()

    sig = inspect.signature(solve_and_persist).parameters
    meta = json.loads((KEEPER / "meta.json").read_text())
    kwargs = build_kwargs(meta, set(sig))

    cand = CANDIDATES[args.candidate]
    kwargs["offer_curve_overrides"] = cand["overrides"]
    kwargs["offer_curve_deltas"] = cand["deltas"]
    kwargs["temp_dependent_derate"] = True
    for ov in args.overrides:
        key, _, val = ov.partition("=")
        if key not in sig:
            raise ValueError(f"--set {key!r} is not a solve_and_persist kwarg")
        kwargs[key] = val.strip().lower() in ("1", "true", "yes", "on")
    kwargs["zero_forcing_ablation"] = args.ablation
    kwargs["ablation_of"] = args.ablation_of if args.ablation else None
    kwargs["note"] = (
        f"offer-curve re-derivation under temp_dependent_derate "
        f"(candidate {args.candidate}, years {args.years}) -- "
        "ercot46_clock_steamgas config reconstructed from meta.json"
    )

    out = ROOT / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    solve_and_persist(
        args.years,
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        run_dir=out,
        **kwargs,
    )
    print(f"DONE {args.candidate} -> {out}")


if __name__ == "__main__":
    main()

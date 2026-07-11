"""miso-55: MISO-measured CT offer grounding on the miso-54 keeper recipe.

The pre-documented Lane-1 item from the miso-54 promotion
(``results/calibration/FINDING-miso-august-scarcity-2026-07.md`` §8: "CAMPD-
grounded CT committed hurdle + econ ramp, rule-23 derive"), executed on what
MISO's own fleet actually measures. Replays the CURRENT KEEPER's exhaustive
``miso54_som_restored/meta.json`` through the RENAME + signature-check
machinery (never ``run_config.json:calibration_flags`` — the miso-50..53
islanding trap), with exactly two deliberate changes on top of the HEAD code
state:

1. **MISO-measured CT_PEAKER bands at HEAD** (``_MISO_OFFER_CURVE``, this
   session): ``derive_campd_marginal_hr.py --iso MISO`` (2023-2025, n=249 CT
   units, ``data/raw/reference/miso_campd_marginal_hr_summary.csv``) measures
   the min-load block's average-HR premium at **1.025** [0.94, 1.14] — wired
   as the committed band — and the CT marginal HR flat-to-FALLING with load
   (0.697/0.687/0.691), so the econ bands stay **neutral 1.0**,
   measurement-AFFIRMED (the NEISO finding on a third fleet). The
   handoff-hypothesized large heat-rate hurdle (the old ERCOT 1.55) is
   REFUTED by MISO's own CAMPD shape: heat-rate physics prices only ~+2.5%
   at min load.

2. **Order-825/ELMP fast-start pricing armed**
   (``tranche_startup_amortization=True`` +
   ``tranche_startup_measured_runs=True``): the commitment-cost component of
   the real MISO CT offer (start + no-load recovery) is not a heat-rate
   multiplier — MISO's ELMP literally folds fast-start startup/no-load offer
   costs into the LMP. The existing P1 mechanism amortizes the NREL start
   cost (constants.CT_STARTUP_PARAMS) over the CAMPD-measured median
   start-to-stop run length (rule-23 derive
   ``derive_campd_ct_run_lengths.py --iso MISO`` ->
   ``campd_ct_run_lengths_MISO.csv``: 95 plants, medians 3-17 h, class
   fallback 10 h over 61,322 pooled runs) as the amortization-horizon
   ceiling — the v3 basis that kills the v2 self-disabling circularity
   (nyiso-44 finding). Both inputs are measured/published; no residual enters
   (rules 13/23). NEISO's keeper carries v2 of this lever; NYISO probes
   validated v3.

Expected direction (pre-committed): the ~$2-8/MWh commitment-cost markup on
CT econ tranches returns mid-merit energy from the over-running CT_PEAKER
(+15.3 TWh 2024) to near-cost COAL_BIT (-16.3/-15.4 TWh), lifting C5a CO2
toward eGRID. If COAL_BIT overshoots after grounding, that is a NEW
root-cause investigation, not a knob (rule 11). August 2023/24 must stay
clean (deltas within a few $ of actual).

Also solves the rule-20 zero-forcing ablation twin (``mode=ablation``).

Usage: python scripts/probes/_miso55_ct_faststart.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso54_som_restored"
OUT_NAME = "miso55_ct_faststart"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below. The three ercot_* recorder keys are inert (false/null) in
# the MISO meta and have no kwarg; the signature check below still errors on
# any NEW unmapped key so nothing can drop silently.
SKIP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "timestamp",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
    "highspy_version",
    "shared_inputs",
    "commitment",
    "commitment_screen_coal",
    "ercot_zonal_gas_basis",
    "ercot_west_netload_gas_shape",
    "ercot_west_gas_delivered_floor",
}


def main(mode: str) -> None:
    meta = json.loads((KEEPER / "meta.json").read_text())
    ablate = mode == "ablation"
    out = ROOT / (OUT_NAME + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    sig = inspect.signature(solve_and_persist).parameters
    kwargs = {}
    unmapped = []
    for k, v in meta.items():
        if k in SKIP:
            continue
        mapped = RENAME.get(k, k)
        if mapped in sig:
            kwargs[mapped] = v
        else:
            unmapped.append(k)
    if unmapped:
        raise SystemExit(
            f"meta.json keys not bound to solve_and_persist: {unmapped} — "
            "extend RENAME/SKIP deliberately, never drop silently"
        )
    # Guard the skipped inert keys: if a future meta ever arms one, fail loud.
    for k in ("ercot_zonal_gas_basis", "ercot_west_netload_gas_shape"):
        if meta.get(k):
            raise SystemExit(f"meta.json arms skipped key {k} — replay invalid")
    if meta.get("ercot_west_gas_delivered_floor") is not None:
        raise SystemExit("meta.json arms ercot_west_gas_delivered_floor")

    # The two deliberate changes vs the miso-54 recipe (docstring §1-§2).
    # §1 (CT_PEAKER committed 1.025 / econ affirmed neutral) is code-resolved
    # at HEAD via _MISO_OFFER_CURVE; meta's offer_curve_overrides stays {}.
    kwargs["tranche_startup_amortization"] = True  # Order-825/ELMP fast-start
    kwargs["tranche_startup_measured_runs"] = True  # v3 measured-run ceiling

    solve_and_persist(
        meta["years"],  # all three train years in one bundle (rule 16)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(OUT_NAME if ablate else None),
        note=(
            f"miso-55 MISO-measured CT offer grounding ({mode}) -- miso-54 "
            "meta.json replay (full keeper structure: reserve co-opt + priced "
            "seam + Manitoba firm imports + intermediate splits + "
            "coal_econ_srmc_bound + SOM coal offers) + CT_PEAKER committed "
            "1.025 measured CAMPD part-load premium (econ bands "
            "measurement-affirmed neutral; derive_campd_marginal_hr --iso "
            "MISO) + Order-825/ELMP fast-start startup amortization on CT "
            "econ/peak tranches over CAMPD-measured run lengths "
            "(tranche_startup_amortization + tranche_startup_measured_runs, "
            "campd_ct_run_lengths_MISO.csv), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])

"""miso-54: the SOM coal-offer redesign RE-SOLVED on the full keeper structure.

Fixes the miso-50..53 config regression and retires the refuted temp derate
in one keeper-candidate run:

1. **Structure restored (the regression fix).** miso-50 through miso-53 were
   launched from ``run_config.json``'s ``calibration_flags`` — the curated
   subset that ``_miso_tempderate_ab.py``'s docstring explicitly warns is
   "missing several MISO structural flags", exactly the trap it was written
   to avoid. Every run since miso-49 therefore silently dropped the whole
   miso-46..49 keeper structure: ``energy_reserve_coopt`` +
   ``miso_zonal_reserves`` + ``miso_reserve_pergen`` (reserve co-opt),
   ``reference_price_interface`` + ``miso_seam_measured_ladder`` +
   ``miso_seam_flow_limit`` / ``_export_limit`` + ``miso_firm_imports``
   (Manitoba must-flow) + ``miso_pjm_border_anchor`` + ``miso_zonal_gas_basis``
   (the entire priced seam — miso-53's solve log has ZERO seam/import lines:
   MISO ran as an island), the ``ct/cc/st_gas`` intermediate splits (and with
   st_gas the bundled ``gas_st_startup_cost`` + NERC-GADS
   ``gas_st_wefor_base_override=0.10``), and ``coal_econ_srmc_bound``. This
   driver replays miso-49's **meta.json** (the exhaustive flat kwarg record)
   through the same RENAME + signature-check machinery as
   ``_miso_tempderate_ab.py`` so no flag is silently dropped.

2. **temp_dependent_derate OFF (rule-24 own-fleet refutation).**
   ``_miso_temp_capability_envelope.py`` (this session) shows the MISO CAMPD
   fleet refutes the literature slopes the same way ERCOT's and PJM's did:
   p98 envelope FLAT (CC 0.990-1.008, CT 0.978-1.02, COAL 0.998-1.041 in
   every TMAX bin to 36-40C, all three years, where the curves predict
   0.84-0.96); COAL — which takes the RAW additive cut here, ~55 GW —
   demonstrates >= 1.00x net-summer on 34C+ hours (median 1.04-1.06, 73-79%
   of capacity proven); scarcity-hour slopes CT +0.00/-0.15 vs model -1.26,
   COAL -0.00/+0.14 vs model -0.40, CC -0.33 vs -0.76. Same exit as the
   ERCOT keeper line and the pjm-95 demotion. This also removes the fake
   August scarcity the derate introduced at miso-49 (Aug-25-2024 hours
   priced ~$1.9k vs actual RT < $150) which the islanding then amplified
   at miso-50 (Aug 2023/24 monthly means +$25-28 over actual).

3. **SOM coal redesign KEPT** (miso-53's measured-conduct grounding, the
   premise-refutation is independent of the regression): coal passthrough
   sigmoids OFF, COAL bands SOM-grounded at HEAD (``_MISO_OFFER_CURVE``),
   per-plant CAMPD fuel-free ``_mustrun`` band as the self-commitment
   representation. ``prb_overrides`` kept (carries ``cc_capacity_reconcile``,
   unrelated to the sigmoid).

4. **Measured intake fixes KEPT**: ``hydro_backfill_year=2024`` +
   ``hydro_eia930_monthly=True`` (miso-51/53); ``gas_daily_shape`` is
   code-resolved ON for MISO in ``backcast_config`` at HEAD.

Also solves the rule-20 zero-forcing ablation twin (``mode=ablation``).

Usage: python scripts/probes/_miso54_som_restored.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso49_tempderate"
OUT_NAME = "miso54_som_restored"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below.
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
        print(f"NOTE: meta.json keys not bound to solve_and_persist: {unmapped}")

    # The two deliberate changes vs the miso-49 recipe (docstring §2-§4).
    kwargs["temp_dependent_derate"] = False  # rule-24 own-fleet refuted
    kwargs["coal_prb_passthrough_sigmoid"] = False  # SOM redesign (miso-53)
    kwargs["coal_bit_sigmoid"] = False
    kwargs["coal_prb_passthrough_tiered"] = False
    kwargs["hydro_backfill_year"] = 2024  # measured hydro intake (miso-51/53)
    kwargs["hydro_eia930_monthly"] = True

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
            f"miso-54 SOM coal offers on RESTORED keeper structure ({mode}) -- "
            "miso-49 meta.json replay (fixes the miso-50..53 calibration_flags "
            "regression: reserve co-opt + priced seam + Manitoba firm imports + "
            "intermediate splits + coal_econ_srmc_bound restored), "
            "temp_dependent_derate OFF (rule-24 MISO own-fleet refutation, "
            "_miso_temp_capability_envelope.py), coal sigmoids OFF on the "
            "SOM-grounded MISO COAL bands (miso-53 redesign), measured hydro "
            "backfill + EIA-930 monthly, 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])

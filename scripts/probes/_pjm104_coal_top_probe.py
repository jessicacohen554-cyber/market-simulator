"""pjm-104 probe driver: pjm-103 + the measured LONG_RUN (coal/steam) top-of-curve floor.

The pjm-103 result (this session): the CT fast-start amortization fixes the
CT_PEAKER over-service of the net DA-virtual depth (2023 +8.57 → +1.35 TWh
vs actual; 2024 in-band; C3a strong), but the retreating CTs hand the evening
DEC demand to coal — COAL_BIT moves OUT in 2023 (+10.84) and 2024 (+8.70)
against the ±8.0 band, and the 2025 C2 coal family stays ~+10%.

The measured basis for the coal leg: the extended mid-curve derive
(``scripts/data/derive_pjm_offer_midcurve.py``, shares grid + 0.975/0.995) now
samples the LONG_RUN top-of-curve belt — the "last-5% wall" the decile grid
missed, where the pjm-99/A' findings located the real $35-83+ price
formation and which no prior mechanism measured for coal (the pjm-99 top
surface scopes to gas classes only). The model's coal peak tranche lives at
within-plant shares ~0.85-1.0 priced ~$35; the measured belt prices it
higher — the floor raises exactly those rows to the measured level.

Rule-19 scoping: ``pjm_offer_midcurve_segments=("LONG_RUN",)`` floors ONLY
the coal / gas-steam econ+peak rows. CT_FAST rows stay owned by the
fast-start startup amortization (the pjm-101/102 combo's CT crush came from
double-pricing the CT stack; that cannot recur under this scope). CC_LIKE
rows stay owned by the keeper's calibrated CC curve.

Delta vs pjm-103 (all measured, zero fitted scalars):
  * pjm_offer_midcurve_conditional=True + pjm_offer_midcurve_segments=("LONG_RUN",)

Usage:
    python scripts/probes/_pjm104_coal_top_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm104_coal_top] \
        [--years 2023 2024 2025] [--zero-forcing-ablation]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import replay_keeper as rk  # noqa: E402
import run_calibration_full as rcf  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--bundle",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm98_cc_mustrun",
        help="base keeper bundle whose meta.json supplies the recipe",
    )
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=REPO / "results" / "calibration" / "pjm104_coal_top",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--zero-forcing-ablation",
        action="store_true",
        help="solve the D-3 zero-forcing ablation twin instead (rule 21); "
        "pairs the twin to the probe via ablation_of",
    )
    args = ap.parse_args()

    meta = json.loads((args.bundle / "meta.json").read_text())
    kwargs = rk.build_kwargs(meta)
    kwargs["iso"] = meta["iso"]
    kwargs["years"] = [int(y) for y in (args.years or meta["years"])]
    kwargs["hours"] = int(meta.get("hours", 8760))
    rcf.enforce_holdout_year_gate(kwargs["years"], kwargs["iso"], False)
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = args.out_dir
    kwargs["pjm_da_virtual_bids"] = True
    kwargs["tranche_startup_amortization"] = True
    kwargs["tranche_startup_measured_runs"] = True
    kwargs["tranche_startup_conditional_runs"] = True
    kwargs["pjm_offer_midcurve_conditional"] = True
    kwargs["pjm_offer_midcurve_segments"] = ("LONG_RUN",)
    kwargs["note"] = (
        "PJM 104 probe: pjm-103 (pjm-98 keeper recipe + net DA virtual depth "
        "+ CT fast-start startup amortization v3/v4 on CAMPD-measured run "
        "horizons) + the measured LONG_RUN top-of-curve floor: "
        "pjm_offer_midcurve_conditional scoped to segments=('LONG_RUN',) — "
        "coal/gas-steam econ+peak tranche rows floored at the measured "
        "capacity-share-matched offer level of the extended mid-curve "
        "surface (shares grid + 0.975/0.995, the last-5% wall the decile "
        "grid missed; derive_pjm_offer_midcurve.py re-derived from the "
        "36-month DataMiner2 corpus). CT_FAST rows stay owned by the "
        "startup amortization and CC_LIKE by the keeper curve (rule 19 "
        "scope — the pjm-101/102 CT double-pricing cannot recur). Zero "
        "fitted scalars in the delta (rules 13/20/21: submitted ex-ante "
        "measured offers, frozen against residuals)."
    )
    if args.zero_forcing_ablation:
        kwargs["zero_forcing_ablation"] = True
        kwargs["ablation_of"] = args.out_dir.name
        kwargs["run_dir"] = args.out_dir.with_name(f"{args.out_dir.name}-ablation")

    print(f"solving {kwargs['iso']} {kwargs['years']} -> {kwargs['run_dir']}")
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

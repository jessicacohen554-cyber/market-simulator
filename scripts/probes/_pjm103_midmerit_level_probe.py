"""pjm-103 probe driver: net DA virtual depth + the CT fast-start offer level.

G-22 lever C (mid-merit offer LEVEL). The net-only control
(2026-07-12-pjm-102b-net-only) established that the measured DA depth alone
makes C3a/C3b PASS but over-serves the added depth with coal+peaker
(C1 2023 CT_PEAKER +8.57 / COAL_BIT +9.55 TWh; C2 2025 coal +9.9% vs the
keeper's pre-existing +5.8%). The measured PJM offer corpus
(pjm_offer_midcurve_condbinned.json) locates the only under-priced mid-merit
class: fast-start CT offers are measured at ~18-38x the delivered-gas day
(~$50-100/MWh) vs the model's 12.3-14.9x HR-multiplier band — the missing
component is the fuel-price-INVARIANT start/no-load recovery, priced by the
existing ``tranche_startup_amortization`` mechanism (FERC Order 825 fast-start
pricing analogue; NREL start costs amortized over CAMPD-measured run
horizons), never by inflating the HR band (the pjm-101/102 surface
over-correction this session must not repeat). Coal offers are NOT raised:
the same corpus measures PJM bituminous (LONG_RUN) offers AT/BELOW the
model's current level in every year (see the session finding doc), so a coal
offer raise would be a residual fit contradicting measured data (rule 13/20).

Delta vs the pjm-98 keeper recipe (all measured/cited, zero fitted scalars):
  * pjm_da_virtual_bids=True  — the committed NET DA-virtual-demand form.
  * tranche_startup_amortization=True + tranche_startup_measured_runs=True +
    tranche_startup_conditional_runs=True — CT_PEAKER/CT_CHP econ+peak
    tranches (and CC duct peak) carry the cited NREL start cost amortized
    over the plant's CAMPD-measured median start-to-stop run
    (campd_ct_run_lengths_PJM.csv), with the v4 condition-keyed horizon
    (campd_ct_run_bands_PJM.csv — tight-hour engagements are shorter
    commitment blocks, so their start recovery amortizes over fewer hours;
    scripts/data/derive_campd_ct_run_lengths.py --iso PJM [--condition-bands]).

The 2023 rebuild diagnosis this design answers: the net layer's DEC
over-clearing vs the actual-DA equilibrium (+3.6 TWh) is an EVENING-PEAK
phenomenon (hours 16-20 carry +3.1 TWh; model dual $32-34 vs actual DA
$38-43) — exactly the hours whose real margin is start-amortized fast-start
CT. Overnight the model under-clears (troughs already high). Coal offers are
measured-consistent, so the coal-side C1/C2 residual is characterized, not
tuned away.

Usage:
    python scripts/probes/_pjm103_midmerit_level_probe.py \
        [--bundle results/calibration/pjm98_cc_mustrun] \
        [--out-dir results/calibration/pjm103_ct_faststart_level] \
        [--years 2023 2024 2025] [--no-virtuals] [--zero-forcing-ablation]
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
        default=REPO / "results" / "calibration" / "pjm103_ct_faststart_level",
    )
    ap.add_argument("--years", nargs="*", type=int, default=None)
    ap.add_argument(
        "--no-virtuals",
        action="store_true",
        help="disable the net DA virtual-bid layer (isolate the CT level leg)",
    )
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
    kwargs["tranche_startup_amortization"] = True
    kwargs["tranche_startup_measured_runs"] = True
    kwargs["tranche_startup_conditional_runs"] = True
    note = (
        "PJM 103 probe: pjm-98 keeper recipe (byte-faithful replay off its "
        "meta.json) + the CT fast-start offer LEVEL: "
        "tranche_startup_amortization + tranche_startup_measured_runs on the "
        "simple-cycle CT econ/peak tranches (and CC duct peak) — the cited "
        "NREL start cost amortized over the plant's CAMPD-measured median "
        "start-to-stop run (campd_ct_run_lengths_PJM.csv), the fuel-price-"
        "invariant commitment-cost component of the real CT offer stack "
        "(FERC Order 825 fast-start pricing analogue), plus the v4 "
        "condition-keyed horizon (campd_ct_run_bands_PJM.csv — a tight-hour "
        "engagement is a shorter commitment block). Grounding: the "
        "measured PJM offer corpus prices fast-start CTs at ~18-38x the "
        "delivered-gas day vs the model's 12.3-14.9x band; the gap is start/"
        "no-load recovery, not heat rate (docs/FINDING-pjm-offer-surface-"
        "noop-2026-07.md re-scoped levers; the pjm-101/102 HR-multiplier "
        "surfaces over-correct and stay off). Zero fitted scalars in the "
        "delta (rules 13/20/21)."
    )
    if not args.no_virtuals:
        kwargs["pjm_da_virtual_bids"] = True
        note += (
            " PLUS pjm_da_virtual_bids=True in the committed NET DA-virtual-"
            "demand form (net(λ)=Σ DEC≥λ − Σ INC≤λ, DEC-form withdrawal "
            "blocks, no supply injected) — the G-22 measured DA procurement "
            "depth whose C1 coal/peaker over-service this probe's offer "
            "level is scored against."
        )
    kwargs["note"] = note
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

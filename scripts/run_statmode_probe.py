"""D-7 statistical-mode A/B: byte-faithful keeper replay with overlays off.

Reproduces a committed keeper's exact ``solve_and_persist`` kwargs from its
bundle ``meta.json`` (same mapping as ``replay_keeper.py``), then applies the
identical delta ``run_calibration_full.apply_statistical_mode`` applies to CLI
args: outage_source -> "statistical", the CT AS/RUC-deployment floor and
spatial reliability-deployment floor forced off, the ST WEFOR-residual relief
cleared, and per-plant EIA-923 monthly coal pricing disabled. Every structural
lever (offer curves, coal passthrough sigmoids, cc-duct band, storage cycling)
and the realized annual Henry Hub gas price are left exactly as the keeper set
them, so the only thing that moves is the overlay/answer-injection set (see
docs/model-legitimacy-audit-2026-07.md D-7).

Usage:
    python scripts/run_statmode_probe.py results/calibration/<keeper_bundle> \
        --out-dir results/calibration/<iso>_statmode_2026-07
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import run_calibration_full as rcf  # noqa: E402
from replay_keeper import build_kwargs  # noqa: E402

# The exact delta apply_statistical_mode() applies to CLI args, translated
# into solve_and_persist kwarg space (outage_source is a direct kwarg; the
# rest ride the generic prb_overrides -> ScenarioConfig channel).
_STATMODE_PRB_OVERRIDES = {
    "wefor_residual": None,
    "wefor_residual_groups": None,
    "coal_plant_monthly_pricing": False,
    "ct_deployment_overlay": False,
    "reliability_deployment_overlay": False,
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundle", help="keeper bundle dir, e.g. results/calibration/<name>")
    ap.add_argument(
        "--out-dir", required=True, help="solve into this dir (never the keeper bundle)"
    )
    args = ap.parse_args()

    bundle = Path(args.bundle)
    meta = json.loads((bundle / "meta.json").read_text())

    kwargs = build_kwargs(meta)
    kwargs["years"] = [int(y) for y in meta["years"]]
    kwargs["iso"] = meta["iso"]
    kwargs["hours"] = int(meta.get("hours", 8760))
    kwargs["reference"] = rcf._load_reference()
    kwargs["run_dir"] = Path(args.out_dir)
    kwargs["outage_source"] = "statistical"
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"].update(_STATMODE_PRB_OVERRIDES)
    kwargs["note"] = (
        f"D-7 statistical-mode A/B probe: byte-faithful replay of keeper "
        f"{bundle.name} (meta.json) with every per-hour/per-year "
        f"answer-injection overlay off (outage_source=statistical, "
        f"ct_deployment_overlay=False, reliability_deployment_overlay=False, "
        f"wefor_residual/groups=None, coal_plant_monthly_pricing=False). "
        f"Structural model + realized annual Henry Hub gas price unchanged. "
        f"Probe only — not a keeper, per CLAUDE.md #1/#13."
    )

    print(
        f"statmode-replaying {bundle} ({meta['iso']} {meta['years']}) -> {args.out_dir}"
    )
    run_dir = rcf.solve_and_persist(**kwargs)
    print(f"solved into {run_dir}")


if __name__ == "__main__":
    main()

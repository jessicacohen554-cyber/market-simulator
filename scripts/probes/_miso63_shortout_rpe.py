"""miso-63 candidate: the miso-62 keeper composed with (a) miso-61's RPE
additive violation pricing and (b) the short (< 5-day) baseload-coal
unit-outage channel — the miso-62 handoff's lane 2 composition plus the
July-2025 availability layer (owner directive 2026-07-13).

Both additions are separately evidenced, zero-fitted-parameter mechanisms:

- ``miso_rpe_pricing`` (registered + scored standalone as
  2026-07-12-miso-61-rpe-pricing): the published $200/MWh RPE demand value
  added to both RDT TCDC violation tiers (2024 SOM §II.E/§III.B). Anchors
  held to the cent in miso-61; active ~30 Aug-2024 hours; orthogonal to coal
  offers (handoff: "they don't interact").
- ``unit_outage_short_windows`` (throwaway 2025 probe
  ``_miso_shortout_probe.py``, this session): sub-5-day baseload-coal CEMS
  full stops (campd-unit-outages-short-MISO.csv, 205 windows incl. Cayuga
  531 MW / Belle River 700 MW at the Jul 28-29 2025 event). July-2025
  demand-weighted LMP +0.53 (39.48 -> 40.01 vs DA actual 58.79), annual
  +0.27, coal −1.8 TWh against the 2025 +9.9 over-run — availability truth
  (rule 14), directionally right everywhere, negligible annual energy.
  Diagnosis: docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md.

Twin (rule 20): both additions are pricing/availability INPUTS (not merchant
floors) so they stay ARMED in the zero-forcing twin, like the passthrough
sigmoids and the parent outage overlay.

Usage: python scripts/probes/_miso63_shortout_rpe.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"
OUT_NAME = "miso63_shortout_rpe"

RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
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
        raise SystemExit(f"meta.json keys not bound to solve_and_persist: {unmapped}")
    if not meta.get("miso_rdt_tcdc"):
        raise SystemExit("miso-62 meta missing miso_rdt_tcdc — wrong base?")

    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("coal_bit_committed_takeorpay"):
        raise SystemExit("miso-62 meta missing coal_bit_committed_takeorpay")
    # The two deliberate changes vs the miso-62 keeper (miso-59..62 pattern):
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True

    solve_and_persist(
        meta["years"],  # 2023 2024 2025 — one bundle (rule 16)
        meta["iso"],
        meta["hours"],
        _load_reference(),
        commitment=meta["commitment"],
        screen_coal=meta["commitment_screen_coal"],
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(OUT_NAME if ablate else None),
        note=(
            f"miso-63 composed candidate ({mode}) -- miso-62 keeper meta.json "
            "replay + miso_rpe_pricing (the miso-61 published $200 RPE demand "
            "value on the RDT violation tiers) + unit_outage_short_windows "
            "(< 5-day baseload-coal CEMS windows, the July-2025 availability "
            "layer; docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md). Zero fitted "
            "parameters added; both mechanisms separately evidenced (miso-61 "
            "registered run; _miso_shortout_probe 2025 A/B)."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])

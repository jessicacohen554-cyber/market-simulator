"""miso-65 candidate: the miso-64 keeper recipe re-solved VERBATIM on the
regenerated ``campd-unit-outages-MISO.csv`` (measured-input staleness fix).

No mechanism, no flag, no parameter changes — the ONLY delta vs the promoted
2026-07-13-miso-64-classdonor keeper is the >= 5-day unit-outage extract,
regenerated with the FROZEN deriver (``scripts/derive_campd_unit_outages.py
--iso MISO --years 2023 2024 2025``, all guards/constants untouched) on the
committed CAMPD unit-level parquets. The committed extract predated the
current deriver (PR #1820 vintage, 2026-07-08; the deriver was last touched
2026-07-13) and does not reproduce from its own frozen code + data: re-running
emits sustained full-stop windows the committed file lacks — including seven
>= 5-day July-2025 North coal stops (Ottumwa 7.3 d at span-CF 0.0001, Gibson-3,
Labadie-2, Baldwin-2, Cayuga-1/2, Sioux-1; ~0.84 GW July-mean) that the
full-stop override keeps unconditionally (span CF < 0.02 — the mechanical
signature). Lane 3 (North supply-curve depth): the model's July-2025 North
margin sits on a coal shelf that reality did not have available.

Precedent: the caiso-78 / nyiso-62 / neiso-59 re-gates — a rule-14/15
measured-input correction, keeper recipe re-solved verbatim, LOYO-exempt
(code-level, year-invariant input regeneration; zero fitted parameters).

Twin (rule 20): outage overlays are physical availability INPUTS, so they
stay ARMED in the zero-forcing twin (the miso-63/64 pattern).

Usage: python scripts/probes/_miso65_outage_regen.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso62_bitpricing"  # miso-64 = this meta + three overrides
OUT_NAME = "miso65_outage_regen"

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
    # The miso-64 keeper's three additions vs the miso-62 meta (all stay armed;
    # ZERO further flag changes — the delta is the regenerated outage extract):
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    kwargs["prb_overrides"]["unit_outage_short_windows"] = True
    kwargs["prb_overrides"]["class_aware_fuel_price_fallback"] = True

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
            f"miso-65 candidate ({mode}) -- the miso-64 keeper recipe VERBATIM "
            "(miso-62 meta.json + miso_rpe_pricing + unit_outage_short_windows "
            "+ class_aware_fuel_price_fallback) on the REGENERATED "
            "campd-unit-outages-MISO.csv: the committed >=5-day extract was "
            "stale vs its own frozen deriver (missed sustained full stops "
            "incl. ~0.84 GW July-2025 North coal, span-CF<0.002). Zero flag/"
            "parameter changes; rule-14 measured-input staleness fix "
            "(caiso-78 re-gate precedent). Lane 3."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])

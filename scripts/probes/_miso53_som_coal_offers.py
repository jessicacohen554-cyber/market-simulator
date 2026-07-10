"""MISO miso-53: SOM-grounded coal offer redesign — sigmoid replaced by
near-cost offers (the miso-52 recipe with the coal passthrough sigmoids OFF
for MISO, on the SOM-grounded MISO COAL offer-curve bands at HEAD).

Adjudication (docs/handoffs/miso-coal-offer-som-redesign-2026-07.md; datatype
som-competitive-conduct): the MISO IMM measures offers at reference levels
~= short-run marginal cost — system price-cost mark-up +3.0% (2023) / -2.5%
(2024), output gap "effectively de minimis" (0.1% / 0.06% of load; 2025
quarterlies 22-71 MW/hr) — so the gas-keyed sigmoid's premise (contracted
coal discounts deeply below delivered cost to hold merit) is the wrong
market structure for 2023-2025 MISO. The mechanism is REPLACED for MISO:

- coal_prb/bit_passthrough_sigmoid OFF (+ tiered follower off): every coal
  tranche above must-run bids full measured F923 delivered SRMC
  (coal_plant_monthly_pricing stays on) — the SOM-measured discount depth
  (~none) — instead of the sigmoid's $15-20/MWh deep discount;
- the MISO COAL_* offer-curve bands are SOM-grounded at HEAD
  (_MISO_OFFER_CURVE: sub-1.0 committed/econ_low multipliers -> 1.00, the
  rising >=1.0 shape kept), retiring the ERCOT-fitted 0.77 econ_low leak;
- self-commitment (SOM Table 7: must-run status on 56%/53% of regulated
  coal starts, "running them regardless of the price") stays represented by
  the per-plant fuel-free _mustrun band (coal_mustrun_per_plant +
  thermal_tranches_MISO.csv) — one mechanism per phenomenon (rule 19): the
  SOM indicts the offer discount, not the floor.

Everything else is byte-identical to miso-52 (gas_daily_shape[MISO] +
monthly sigmoid key at HEAD — now moot with the sigmoid off — + hydro
2024-backfill / EIA-930 monthly repin, on the miso-49 keeper flags).

Usage:
    python scripts/probes/_miso53_som_coal_offers.py main
    python scripts/probes/_miso53_som_coal_offers.py ablation   # after main
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso49_tempderate"

_RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
_DROP = {
    "iso",
    "years",
    "hours",
    "git_sha",
    "passes",
    "gas_prices",
    "coal_plant_monthly_pricing",
    "td_loss_factor",
}


def main(mode: str) -> None:
    cf = json.loads((KEEPER / "run_config.json").read_text())["calibration_flags"]
    ablate = mode == "ablation"
    out = ROOT / ("miso53_som_coal_offers" + ("-ablation" if ablate else ""))
    out.mkdir(parents=True, exist_ok=True)

    kwargs = {}
    for k, v in cf.items():
        if k in _DROP:
            continue
        kwargs[_RENAME.get(k, k)] = v

    kwargs["hydro_backfill_year"] = 2024
    kwargs["hydro_eia930_monthly"] = True

    # THE redesign: coal passthrough sigmoids OFF for MISO — committed/econ/
    # peak coal bids full measured delivered SRMC (SOM mark-up ~ 0). The
    # tiered PRB follower rides the sigmoid and goes with it. prb_overrides
    # is kept: it carries cc_capacity_reconcile (unrelated to the sigmoid).
    kwargs["coal_prb_passthrough_sigmoid"] = False
    kwargs["coal_bit_sigmoid"] = False
    kwargs["coal_prb_passthrough_tiered"] = False

    solve_and_persist(
        cf["years"],  # 2023 2024 2025 — one bundle (rule 16)
        cf["iso"],
        cf["hours"],
        _load_reference(),
        run_dir=out,
        zero_forcing_ablation=ablate,
        ablation_of=(out.parent / "miso53_som_coal_offers").name if ablate else None,
        note=(
            f"miso-53 SOM-grounded coal offers ({mode}) — the miso-52 recipe "
            "with the coal passthrough sigmoids OFF (near-cost offers per the "
            "MISO SOM mark-up ~ 0) on the SOM-grounded MISO COAL bands at "
            "HEAD (sub-1.0 -> 1.00), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])

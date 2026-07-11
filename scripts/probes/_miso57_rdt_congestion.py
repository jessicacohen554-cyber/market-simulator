"""miso-57: RDT S->N congestion depth — wheel-bypass fix + published derate/TCDC.

Executes the miso-56 handoff's sanctioned transmission lane (RDT S->N
congestion depth, FINDING §10 pointer 1). Replays the RECOMMENDED CANDIDATE's
``miso56_measured_scarcity/meta.json`` through the RENAME + signature-check
machinery, with exactly two deliberate changes on top of the HEAD code state:

1. **South-seam external-zone split** (``miso_south_seam_split``,
   ``transmission.split_miso_south_external_node``): the shared MISO_external
   bus links to all five border zones, so the LP wheels South energy
   South->external->Midwest through the bus's energy balance without touching
   any priced band — a free 3,000 MW bypass around the RDT contract path.
   The 2025 diagnostic probe measured the bypass at a 1,255 MW summer mean
   (1,563 of 2,208 summer hours; 7.7 TWh/yr) while the RDT S->N link carried
   54 MW mean and saturated 13 h/yr — with Midwest-South separation ~$0
   against the IMM's measured $9.31/MWh (Summer-2025 quarterly). Structural
   topology fix (rule 1): the southern neighbors (SOCO/TVA/AECI) are
   electrically south of the RDT.

2. **RDT default derate + TCDC pricing** (``miso_rdt_tcdc``,
   ``transmission.apply_miso_rdt_tcdc``): the static JOA contract limits
   (3,000 N->S / 2,500 S->N) become the published operating representation —
   the 92% default derate ("MISO derates the RDT limit to 92 percent of the
   contract limit by default", 2024 SOM §III.B) as the free tier, then the
   published two-step TCDC ($40/MWh at the modeled limit, $500/MWh from 102%,
   hard bound at contract) as priced one-way tiers via TransferLink.flow_cost.
   This reproduces the real market's price formation for Midwest-South
   separation (RDT bound >25% of RT intervals in 2024 at ~$3/MWh separation;
   $9.31/MWh Summer 2025). All parameters published (constants.MISO_RDT_*);
   zero fitted scalars.

**Measured adjudication recorded ex-ante (rule 1 — score movement is a
by-product):** the deliberately conservative choice is the 92% DEFAULT derate,
not the 84%-of-contract average utilization the SOM measures when binding —
so binding-hour congestion is expected to UNDER-shoot ($40-class TCDC step-1
pricing vs the real market's deeper operator derates). Expected direction:
2025 summer Midwest-South separation moves from ~$0 toward the IMM's $9.31
(not necessarily all the way), C3a-2025 toward zero; August 2023/24 should
hold (RDT bound only ~25%/lower in 2023-24 at ~$3 separation — the derate +
TCDC also applies there and adds mild separation, watched, not tuned).

Also solves the rule-20 zero-forcing ablation twin (``mode=ablation``) — the
RDT/topology mechanisms are market structure, not merchant floors, so they
stay armed in the twin.

Usage: python scripts/probes/_miso57_rdt_congestion.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso56_measured_scarcity"
OUT_NAME = "miso57_rdt_congestion"

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

    # The two deliberate changes vs the miso-56 recipe (docstring §1-§2).
    kwargs["miso_south_seam_split"] = True  # sever the external-bus RDT bypass
    kwargs["miso_rdt_tcdc"] = True  # published 92% derate + $40/$500 TCDC

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
            f"miso-57 RDT congestion depth ({mode}) -- miso-56 meta.json "
            "replay (full candidate structure: reserve co-opt pergen + zonal "
            "South + priced seam + intermediate splits + SOM coal offers + "
            "CT 1.025 measured committed + Order-825 fast-start v4 + measured "
            "hourly OR requirements) + South-seam external-zone split "
            "(miso_south_seam_split, severs the free 3 GW "
            "South->external->Midwest wheel around the RDT) + published RDT "
            "92% default derate with $40/$500 two-step TCDC priced tiers "
            "(miso_rdt_tcdc, 2024 SOM III.B / MISO-SPP JOA), 2023-2025"
        ),
        **kwargs,
    )
    print(f"DONE {mode} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])

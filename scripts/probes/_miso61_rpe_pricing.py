"""miso-61: RPE additive violation pricing — the 2025 price-side lane's
first sanctioned mechanism (RPE constraint family, miso-60 handoff lane 1).

The input adjudication came first (2026-07-12 session):

- RPE = Reserve Procurement Enhancement. "MISO enforces STR requirements in
  its two subregions by enforcing reserve procurement enhancement (RPE)
  constraints over the Regional Directional Transfer (RDT) constraint. The
  RPE binds when headroom on the RDT plus the available STR in the importing
  subregion is limited" (2024 SOM §II.E p.9). "MISO also models a Reserve
  Procurement Enhancement (RPE) constraint that limits flows between
  subregions after a supply-side contingency and has a single demand value
  of $200 per MWh" (2024 SOM §III.B pp.51-52).
- In the 2023-2025 design the RPE demand value applies ADDITIVELY with the
  RDT TCDC in real violations: "when the transfer constraints are violated,
  it often produces subregion-wide price spreads of $700 because the demand
  curve values for the RDT ($500) and the RPE ($200) apply additively, which
  was unintended"; the IMM complains even SMALL violations (the $40 first
  step) are overpriced "by $200 per MWh" -> $240. The IMM cap-at-$500
  recommendation was NOT implemented in-window (restated IMM Summer-2025
  quarterly: $41M RDT+RPE congestion, +121% YoY). So additive-in-violation
  is the honest historical representation; date-gate a re-anchor if MISO
  adopts the recommendation (rule 23).
- Lane 2 (hourly measured RDT limit intake) re-verified DATA-BLOCKED for
  the limit series (RT Data Broker RDT endpoint deprecated without archive;
  Data Exchange key-gated; da_pbc/rt_pbc carry no limit MW; no new public
  source as of 2026-07). The admissible measured series is the pbc BINDING
  record (da_pbc hourly / rt_pbc 5-min shadow prices, both directions,
  2023-2025, docs.misoenergy.org, no auth) — intaken this session as the
  lane's VALIDATION anchors (never an LP input: binding is an outcome,
  rule 13).

Mechanism (zero new scalars): miso_rpe_pricing=True — adds
constants.MISO_RPE_DEMAND_VALUE ($200, published) to the flow_cost of both
VIOLATION tiers of each one-way RDT link in transmission.apply_miso_rdt_tcdc
(free tier below the derated modeled limit untouched). Window (rule 12): the
constraint's own driver window — engages only on flow above the derated
modeled limit, exactly where the real market's RPE prices violations.
Driver: the published RPE constraint (STR enforcement over the RDT).
Forward story (rule 13): a market-design constant that persists while the
2023-2025 design does; regenerates for a forward year from the published
tariff parameters. Deliberately conservative, documented one-way gap: the
RPE's STR-scarcity channel ("RPE Only" binding with NO RDT violation — IMM
Summer-2025 quarterly p.29) is unrepresented (no STR product in the LP), so
modeled separation UNDER-states the measured $9.31 Summer-2025 spread.

Expected direction (recorded ex-ante; score movement is a by-product):
violation hours reprice $40->$240 / $500->$700, so the LP either redispatches
up to $240 before violating (raising separation-when-binding toward the
measured ~$3 average / the measured DA -40-pegged violation hours) or pays
the real violation price. 2023/24 anchors (S->N mean-flowing ~1.5-1.6 GW,
separation-when-binding $2.5-2.6) must HOLD or move toward measured ($3);
2025 moves only to the extent the model's S->N flow reaches the violation
region — July-2025's -18.8 monthly gap was pre-adjudicated (§10) to ELMP
ex-post/emergency constructs + deeper operator derates + the upstream
mid-merit split, and is NOT expected to close here. Watch: no D-2/D-4
implications (pricing mechanism, no forcing); C3c may gain tail hours in
violation events.

Also solves the rule-20 zero-forcing ablation twin (mode=ablation). The RPE
pricing is market structure, not a floor — like miso_rdt_tcdc and the seam
split it stays ARMED in the twin (only merchant floors disarm via the
MECH_ABLATION_FIELDS registry; st_gas_mustrun_per_plant auto-disarms there).

Usage: python scripts/probes/_miso61_rpe_pricing.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso60_stgas_vlr"
OUT_NAME = "miso61_rpe_pricing"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below (same guard set as the miso-57/59/60 drivers: the
# signature check errors on any NEW unmapped key so nothing can drop
# silently).
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
    for k in ("ercot_zonal_gas_basis", "ercot_west_netload_gas_shape"):
        if meta.get(k):
            raise SystemExit(f"meta.json arms skipped key {k} — replay invalid")
    if meta.get("ercot_west_gas_delivered_floor") is not None:
        raise SystemExit("meta.json arms ercot_west_gas_delivered_floor")

    # The one deliberate change vs the miso-60 keeper recipe (docstring): the
    # RPE additive violation pricing rides the generic prb_overrides ->
    # with_overrides channel (the miso-59/60 pattern), so it is recorded in
    # the new meta's coal_prb_sigmoid_overrides. The miso-60 recipe's own
    # entries (cc_capacity_reconcile, coal_warm_committed,
    # st_gas_mustrun_per_plant) replay unchanged from the meta.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    if not kwargs["prb_overrides"].get("st_gas_mustrun_per_plant"):
        raise SystemExit(
            "miso-60 meta does not carry st_gas_mustrun_per_plant — wrong base bundle?"
        )
    kwargs["prb_overrides"]["miso_rpe_pricing"] = True
    if not meta.get("miso_rdt_tcdc"):
        raise SystemExit(
            "miso-60 meta does not arm miso_rdt_tcdc — the RPE adder has no "
            "tiers to price (replay invalid)"
        )

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
            f"miso-61 RPE additive violation pricing ({mode}) -- miso-60 "
            "meta.json replay (ST_GAS VLR per-plant commitment floor + coal "
            "warm-boiler committed band + RDT congestion structure: "
            "South-seam split + 92% derate/TCDC + reserve co-opt pergen + "
            "zonal South + priced seam + SOM coal offers + CT 1.025 measured "
            "committed + Order-825 fast-start v4 + measured hourly OR "
            "requirements) + miso_rpe_pricing=True (the published Reserve "
            "Procurement Enhancement $200/MWh demand value added to both RDT "
            "violation tiers -- the 2023-2025 market's measured additive "
            "price formation: $240 small-violation / $700 deep-violation "
            "spreads, 2024 SOM SS II.E/III.B, IMM Summer-2025 quarterly $41M "
            "RDT+RPE congestion). The 2025 price-side lane (FINDING SS 11/13 "
            "continuity); zero new scalars."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])

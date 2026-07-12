"""miso-60: ST_GAS local-reliability commitment floor (VLR) — the 2025
Southern-gas starvation / RDT regional-reversal lane's structural mechanism.

Executes the miso-59 handoff's sanctioned lane. The input adjudication came
first (2026-07-12 session): the MISO-South 2025 delivered-gas basis carried a
mismatched-window construction bug (the committed +0.095 subtracted the
full-year Henry Hub mean from a 6-month LA mean; the like-for-like formula
that reproduces every other cell gives +0.343) — fixed in
data/raw/miso_zonal_gas_hub.csv and riding along here. NOTE the fix is
COUNTER-directional (+$0.25/MMBtu makes South dearer, ~+$2.6/MWh at the
class's HR): the buggy basis was flattering South, so basis is NOT the
starvation driver — kept per rule 15 (accurate data stays; the residual's
root cause is structural).

The structural finding (CEMS unit-grain forensics, this session): the model
starves MISO-South ST_GAS (~6 vs 16.4 TWh measured 2025; class chronic
-4.2/-5.1/-9.2) because the Entergy South steam fleet's measured
always/mostly-online self-commitment is invisible to it —

- Nine Mile Point: synchronized 98.2% of ALL hours 2023-2025, plant
  P5-over-all-hours 414 MW (28% of nameplate) — a genuine measured must-run
  floor, the same P5 quantity that grounds the coal mustrun tranche;
- Sabine 85.6% / Lewis Creek 87.8% / Little Gypsy 50.8% online with
  unit-level min-stable floors when on;
- yet thermal_tranches mustrun_pct = 0 for every gas ST (the derive
  class-gates the measured floor to COAL, its comment conceding it zeroes
  the value "even when its high capacity factor would make the all-hours
  floor look high") and no other mechanism holds the boilers online, while
  their committed bands carry the 1.32x part-load HR penalty + startup
  amortization — the LP leaves them dark and serves the South from Plains
  coal/CC over an N->S RDT flow, the exact 2025 direction reversal
  (FINDING §11: reality ran S->N with $9.31 separation).

The mechanism is the EXISTING cc_mustrun_per_plant architecture's ST_GAS leg
(new gate st_gas_mustrun_per_plant, new id MECH_ST_GAS_MUSTRUN_PER_PLANT):
each plant's measured committed tranche (CEMS P5-when-online) is forced on in
its measured top-online_frac system-load window; offers untouched (rule 19,
no second floor); self-targeting by measurement (rule 18 — Gerald Andrus,
online 13.9%, is floored only in its top-load sliver; the CT G-20 rejection
does not transfer because these steamers' evidence is around-the-clock
synchronization, the opposite of the CT overnight-offline signature).
Driver (rule 12): MISO SOM-documented out-of-market VLR/self-commitment in
the South region (Amite South / DSG / WOTAB). Forward story (rule 13):
committed share + online fraction re-derive from multi-year CAMPD exactly
like the CC leg and forecast emission rates. Zero new scalars: one boolean;
both quantities measured per plant (DOF ledger row auto-generates).

Expected direction (recorded ex-ante; score movement is a by-product):
South ST_GAS floors ~976 MW across Nine Mile/Sabine/Lewis Creek/Little
Gypsy (+ smaller Midwest legs, e.g. plant 990 online 97.4%) -> South supply
rises ~7-8 TWh, 2025 RDT direction moves toward S->N-dominant with
separation toward the IMM's $9.31, C3a-2025 toward zero, sysvol-2025 gas
back toward ±5%. Watch, per the lane's success gate: the 2023-24 RDT anchors
(S->N mean-flowing ~1.55 GW / separation-when-binding ~$2.5-2.9) must hold;
August 2023/24 within a few $; D-2 ST_GAS forced share likely ABOVE the 30%
cap -> rubric-v2.2 grounded-above-budget escalation (D4_WINDOWS row shipped
with the mechanism; D-1 shape gates decide) — run legitimacy diagnostics
while parquets are LOCAL.

Also solves the rule-20 zero-forcing ablation twin (mode=ablation) — the
floor is a merchant reliability commitment, so the twin DISARMS it via the
MECH_ABLATION_FIELDS registry (unlike miso-59's coal_warm pricing exemption,
which stays armed there).

Usage: python scripts/probes/_miso60_stgas_vlr.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso59_coal_warm"
OUT_NAME = "miso60_stgas_vlr"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below (same guard set as the miso-57/59 drivers: the signature
# check errors on any NEW unmapped key so nothing can drop silently).
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

    # The one deliberate change vs the miso-59 keeper recipe (docstring): the
    # ST_GAS local-reliability commitment floor rides the generic
    # prb_overrides -> with_overrides channel (the miso-59 coal_warm pattern),
    # so it is recorded in the new meta's coal_prb_sigmoid_overrides. The
    # miso-59 recipe's own entries (cc_capacity_reconcile, coal_warm_committed)
    # replay unchanged from the meta. The corrected South gas basis is a DATA
    # change (miso_zonal_gas_hub.csv) and needs no flag.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    kwargs["prb_overrides"]["st_gas_mustrun_per_plant"] = True

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
            f"miso-60 ST_GAS local-reliability commitment floor ({mode}) -- "
            "miso-59 meta.json replay (coal warm-boiler committed band + RDT "
            "congestion structure: South-seam split + 92% derate/TCDC + "
            "reserve co-opt pergen + zonal South + priced seam + SOM coal "
            "offers + CT 1.025 measured committed + Order-825 fast-start v4 "
            "+ measured hourly OR requirements) + st_gas_mustrun_per_plant="
            "True (each gas steamer's measured committed tranche forced on "
            "in its measured top-online_frac system-load window -- the "
            "Entergy MISO-South VLR/self-commitment trace: Nine Mile "
            "synchronized 98.2% of ALL hours, Sabine 85.6%, Lewis Creek "
            "87.8%) + corrected MISO-South 2025 delivered-gas basis "
            "(+0.095 -> +0.343, mismatched-window construction bug in "
            "miso_zonal_gas_hub.csv; counter-directional, kept per rule 15). "
            "The 2025 Southern-gas starvation / RDT regional-reversal lane "
            "(FINDING §11/§12 continuity)."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])

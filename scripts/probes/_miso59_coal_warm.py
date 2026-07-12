"""miso-59: coal warm-boiler committed band — the fabricated cold-start premium
on self-committed coal removed (the COAL_BIT/CC mid-merit lane's root cause).

Executes the miso-58 handoff's sanctioned mid-merit lane. The scorer-basis
check came first (rules 1/14, G-21b, 2026-07-12 calibration-log entry): on the
measured CEMS basis the 2023/24 coal under-run is REAL and ~2x the handoff's
number (family -34/-42 TWh vs CAMPD; classFull COAL_BIT -18.2/-17.1,
COAL_PRB -9.2/-13.8, mirrored by CT_PEAKER +8.8/+16.0 and CC_REGULAR
+2.9/+9.4), while the "2025 model over-coals" reading was an EIA-930
attribution artifact (CEMS-corrected 2025: coal -2.9%, gas ~-3.3%).

Dispatch forensics on the replayed miso-58 2023 solve (on/off LMP crossing
points — an LP price-taker runs iff LMP >= mc):

- CC_REGULAR committed+econ: ALWAYS ON at any LMP (offers below the $20.6
  LMP floor) — availability-bound at CF 0.71.
- COAL_PRB committed crosses at $34.6 vs ~$26 static measured-fuel SRMC
  (F923 delivered $2.2-2.3/MMBtu); COAL_BIT committed at $43.8 vs ~$29-31.
- The +$8-15/MWh wedge is compute_monthly_markup's $100/MW cold-start
  amortization (BIN_STARTUP_COST_PER_MW, committed band only, raw P0 run
  lengths, no measured ceiling) — while the same plants' fuel-free mustrun
  bands hold their boilers ONLINE 84-98% of hours in the same solve. A hot
  boiler's committed band is an output ramp, not a cold start.

The fix is the EXISTING gated exemption ``coal_warm_committed``
(``compute_monthly_markup``: skip the P1 startup markup on coal bins whose
must-run floor keeps the boiler hot). Grounding (rule 1): the MISO IMM's own
measured conduct (miso-53 SOM adjudication, `som-competitive-conduct`) says
offers sit AT cost (system price-cost markup +3.0%/-2.5%) — a +$8-15
fabricated start premium on 15 GW of committed coal contradicts the measured
market. Self-committed units recover start costs outside the energy offer
(self-commitment forfeits make-whole; the CC-econ analogue in the fast-start
scope note: start costs settle as uplift, not in the LMP). The ERCOT 98a/98b
rejection of this flag was ERCOT-shaped (their 2023 coal was already
calibrated and the exemption overshot; their CT/ST were UNDER-running) — the
refutation does not cross the ISO boundary, and MISO's residual pattern is
its exact mirror (coal under BOTH years, CT/ST over).

Zero new parameters: one existing boolean, physics-gated per plant
(must_run_pct > 0, from the CAMPD-derived thermal-tranche artifact).

Expected direction (recorded ex-ante; score movement is a by-product):
2023/24 coal committed bands re-enter mid-merit at their measured-fuel SRMC
-> COAL_BIT/COAL_PRB C1 rows close toward band, CC_REGULAR/CT_PEAKER
over-runs shrink, C5a CO2 (-8.4%) closes upward. 2025 movement small (at
$3.52 gas coal committed cleared despite the wedge). Watch, per the lane's
success gate: the 2023-24 RDT anchors (S->N flow/binding/separation) must
hold near measured; 2025 RDT direction/separation and C3a-2025; August
2023/24 within a few $; no CT re-forcing above D-2 caps.

Also solves the rule-20 zero-forcing ablation twin (mode=ablation) —
coal_warm_committed is offer pricing, not a merchant floor, so it stays
armed in the twin (RDT/topology precedent).

Usage: python scripts/probes/_miso59_coal_warm.py {main|ablation}
"""

import inspect
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_calibration_full import _load_reference, solve_and_persist  # noqa: E402

ROOT = Path(__file__).resolve().parents[2] / "results" / "calibration"
KEEPER = ROOT / "miso58_rdt_congestion"
OUT_NAME = "miso59_coal_warm"

# meta.json keys that use a different name than the solve_and_persist kwarg.
RENAME = {
    "commitment_screen_coal": "screen_coal",
    "coal_prb_sigmoid_overrides": "prb_overrides",
    "coal_bit_passthrough_sigmoid": "coal_bit_sigmoid",
    "coal_bit_sigmoid_overrides": "bit_overrides",
}
# recorded for provenance only / not a solve_and_persist kwarg / handled
# explicitly below (same guard set as the miso-57 driver: the signature check
# errors on any NEW unmapped key so nothing can drop silently).
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

    # The one deliberate change vs the miso-58 keeper recipe (docstring): the
    # warm-boiler exemption rides the generic prb_overrides -> with_overrides
    # channel (the same path the --coal-warm-committed CLI flag uses), so it
    # is recorded in the new meta's coal_prb_sigmoid_overrides.
    kwargs.setdefault("prb_overrides", {})
    kwargs["prb_overrides"] = dict(kwargs["prb_overrides"] or {})
    kwargs["prb_overrides"]["coal_warm_committed"] = True

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
            f"miso-59 coal warm-boiler committed band ({mode}) -- miso-58 "
            "meta.json replay (RDT congestion structure: South-seam split + "
            "92% derate/TCDC + reserve co-opt pergen + zonal South + priced "
            "seam + SOM coal offers + CT 1.025 measured committed + Order-825 "
            "fast-start v4 + measured hourly OR requirements) + "
            "coal_warm_committed=True: the P1 $100/MW cold-start amortization "
            "is removed from coal committed bands whose fuel-free mustrun "
            "tranche holds the boiler online (measured 84-98% of hours) -- "
            "the fabricated +$8-15/MWh wedge that priced 15 GW of "
            "self-committed coal out of mid-merit against the SOM's measured "
            "at-cost conduct (G-21b/forensics, 2026-07-12 calibration log)."
        ),
        **kwargs,
    )


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("main", "ablation"):
        raise SystemExit(__doc__.splitlines()[-1])
    main(sys.argv[1])

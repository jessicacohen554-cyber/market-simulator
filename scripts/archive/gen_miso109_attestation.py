"""Write ``calibration_attestation.json`` for the miso-109 hydro-LEVEL arm.

``miso109_hy_level_B`` is the ``2026-07-28-miso-101b-tempgrain`` keeper recipe
(rebuilt from its ``meta.json`` by ``replay_keeper``) with ONE data change: the
monthly hydro LEVEL comes from EIA-923 ``HY`` instead of the PS-inclusive
EIA-930 ``NG: WAT`` pin. The governance posture and the accepted-limitation
ledger are that keeper's, inherited unchanged — no exception is added, widened
or re-scoped, and none was needed: every C-series criterion verdict is
identical between the arms.

The delta REMOVES a mechanism rather than adding one, so the DOF ledger can
only improve (rule 21 ``[R-DOF]``): no constant, factor or offset is
introduced, and none is tuned against any residual (rules 13/23). The
``free_parameters`` ledger is refreshed from THIS bundle's ``run_config.json``
by ``scripts/build_dof_ledger.py`` (run separately).

Usage:
    python scripts/gen_miso109_attestation.py
    python scripts/build_dof_ledger.py results/calibration/miso109_hy_level_B --iso MISO
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/miso101_tempgrain_B/calibration_attestation.json"
ARM = REPO / "results/calibration/miso109_hy_level_B/calibration_attestation.json"

ATTESTED_BY = (
    "miso-109 hydro LEVEL correction 2026-07-30/31: the "
    "2026-07-28-miso-101b-tempgrain keeper recipe, rebuilt from its meta.json "
    "by replay_keeper, solved fresh for 2023/2024/2025 as one process per year "
    "into one bundle (rule 16), with ONE change -- the monthly hydro LEVEL is "
    "taken from EIA-923 HY instead of the EIA-930 NG: WAT pin. "
    "WHAT IT REPLACES: the level pin, in place. It is NOT stacked on anything: "
    "the keeper carries hydro_dispatch_envelope=False, hydro_min_flow_floor="
    "False, hydro_ror_split=False and hydro_budget_nameplate_aware=False, so "
    "the monthly level pin was the ONLY mechanism acting on MISO hydro energy "
    "placement (rule 19 [R-ONE-MECH], enumerated before the change). "
    "THE DEFECT, MEASURED ON MISO'S OWN DATA (rule 25 [R-ISO-SCOPE]; audited by "
    "miso-108, re-derived here from raw sources by "
    "scripts/probes/_miso109_hydro_level_audit.py): data/hydro.py builds the "
    "hydro LP units from EIA-923 prime mover HY alone -- pumped storage is a "
    "storage resource, not inflow hydro -- while the keeper pinned those units' "
    "monthly energy to EIA-930 NG: WAT. MISO files NO NG: PS column, so its "
    "NG: WAT is a conventional-hydro PLUS pumped-storage-discharge series. "
    "Three independent signatures. (a) The extract carries COL/NG/NUC/WAT/SUN/"
    "WND/BAT/OTH and no PS column at all. (b) NG: WAT peaks 3,535 / 3,964 MW "
    "(2023/2024) against 2,478.4 MW of conventional HY nameplate -- 580 / 826 "
    "h/yr ABOVE the whole fleet's nameplate, physically impossible for inflow "
    "hydro -- beside a 2,416.8 MW PS fleet (Ludington 1,978.8, Taum Sauk 408, "
    "Degray 30). (c) There are ZERO negative NG: WAT hours in any year "
    "2018-2025, so pumping is not netted and the contamination is one-way gross "
    "discharge; EIA-923 PS net generation is NEGATIVE every year (-0.840 / "
    "-1.033 TWh, the round-trip loss) -- the opposite sign, independently "
    "confirming the reading. Level vs units: 9.979 vs 8.789 TWh (2023, +13.5 %) "
    "and 10.710 vs 9.042 TWh (2024, +18.5 %). The control's own solve log states "
    "it: 'MISO 2023 hydro budget pinned to monthly target total 9979.0 GWh (was "
    "8789.4 GWh)'. "
    "2025 IS DELIBERATELY NOT DIFFERENCED: its EIA-923 filing is an early "
    "release carrying 14 HY plants against 165, so the naive gap (+8.902 TWh, "
    "+918 %) measures SOURCE COVERAGE and overstates the defect ~5x. Every "
    "year-over-year difference in this session is coverage-gated first. "
    "WHY 923 HY DIRECTLY AND NOT A RECONCILED 930 SERIES: the alternative "
    "(keep NG: WAT for monthly shape, rescale to the 923 level) needs a "
    "reconciliation constant, and this session MEASURED whether one is "
    "identifiable. It is not. MISO's conventional share of NG: WAT drifts "
    "0.9937 -> 0.8442 across 2019-2024 (spread 0.15), and the monthly gap "
    "changes sign by month in 4 of the 5 complete-filing years -- the "
    "discrepancy is PS discharge (positive, Jun-Sep, +197 to +356 GWh every "
    "July/August) net of an opposing boundary difference elsewhere, not one "
    "scalable contaminant. A fitted constant would be a free parameter with no "
    "forward story (rules 5/13/21). Taking 923 HY makes the LEVEL and the UNITS "
    "the same series and the same plant population, adds ZERO free parameters, "
    "and is forward-reproducible: 923 HY regenerates every year and responds to "
    "hydrology, the same admissibility class the per-plant budget already uses. "
    "THE SIGN WAS DECLARED BEFORE THE SOLVE, because a correction that helps is "
    "the easiest kind to accept for the wrong reason. Removing 1.2-1.7 TWh of "
    "zero-marginal-cost hydro must raise fossil volume and mean LMP, and the "
    "keeper was under-priced in every year and under-producing 7 of 8 fossil "
    "classes -- so the fix was predicted to move C1/C3a the helpful way, and "
    "predicted SMALL (~0.5 % of a 250 TWh system, nowhere near a -14.3 % price "
    "miss). Both halves are confirmed: hydro -1.075 / -1.454 / -0.722 TWh, "
    "fossil +0.869 / +1.168 / +0.575 TWh, imports +0.207 / +0.279 / +0.144 TWh, "
    "load-weighted LMP +0.072 / +0.089 / +0.050 $/MWh (+0.22 / +0.30 / +0.13 %). "
    "C3a improves in every year (-1.4 -> -1.2 %, -6.7 -> -6.4 %, -14.3 -> "
    "-14.2 %) and 2023's net fossil deficit narrows -14.387 -> -13.563 TWh. "
    "Rule 14 [R-ACCURATE] mandates the accurate input WHICHEVER WAY the residual "
    "moves; the favourable direction is a consequence, not the justification. "
    "CONTROL: 2026-07-30-miso-109a-control-930pin, the same recipe at the same "
    "HEAD with the pin still armed. It reproduces the committed keeper at "
    "0.00000 % on EVERY class in EVERY year despite 21 changed files under "
    "src/market_sim/ since the keeper's registration commit -- a measured noise "
    "floor of exactly zero, so every arm-B movement is attributable to the "
    "single data change. (The drift window was checked with git diff BEFORE the "
    "control was run; bit-equality was never pre-registered -- the miso-106 G3 "
    "lesson.) "
    "SECOND RESULT, NO SOLVE SPENT: on the corrected level "
    "hydro_budget_nameplate_aware is PROVABLY INERT at MISO. It only changes how "
    "a level TARGET is distributed, and there is now no target, so budgets are "
    "byte-identical with it on and off in all three years (L1 = 0.000 GWh). On "
    "the CONTAMINATED level it moved 259 / 454 / 171 GWh -- its entire apparent "
    "MISO signal was the allocator shuffling PS energy off plant-months pushed "
    "above their own nameplate x hours ceiling. Matrix cell U -> I. "
    "2023-2025 only, all three FRESH in one bundle (rule 16), no holdout year "
    "touched, MISO freeze active. Evidence: "
    "results/calibration/FINDING-miso109-hydro-level-923hy-2026-07-30.md; "
    "audit: results/calibration/"
    "FINDING-miso108-hydro-ps-pin-audit-2026-07-30.md; "
    "probe: scripts/probes/_miso109_hydro_level_audit.py; "
    "log: docs/calibration-log/miso.md 2026-07-30 miso-109."
)

DISCLOSURE = (
    "miso-109 disclosures, reported rather than patched. "
    "(a) A MEASURED INPUT WAS LOST ALONG WITH THE CONTAMINATED ONE: dropping the "
    "pin also drops the measured MONTHLY SHAPE of the 2025 water year, which now "
    "comes from the 2024 backfill (146 of 160 plants, 8.108 of 9.077 TWh). This "
    "is accepted, not hidden -- the discarded shape is itself PS-distorted "
    "(summer-inflated by exactly the Jul-Sep signature above). An independent "
    "read on what was lost: the 14 plants filing in BOTH 2024 and 2025 generated "
    "+3.8 % MORE in 2025 (0.9344 -> 0.9697 TWh), i.e. 2025 was slightly WETTER, "
    "while the contaminated NG: WAT said 2025 was 7.8 % DRIER than 2024. The two "
    "disagree in SIGN, which is further evidence the 930 series' year-over-year "
    "movement at MISO is dominated by PS cycling rather than hydrology. "
    "(b) THE FIX HELPS THE RESIDUAL, AND THAT IS NOT WHY IT IS HERE. The "
    "direction and the smallness were both written down before the solve (see "
    "attested_by); rule 14 would have kept the input had it hurt. No gate flips "
    "in either direction: every C-series verdict is identical between the arms, "
    "and the run is NOT-YET on the same three criteria as the outgoing keeper. "
    "(c) ONE CLASS MOVES THE WRONG WAY. COAL_PRB was the single fossil class "
    "already OVER-producing in 2023 (+1.794 TWh vs actual) and it goes further "
    "over (+2.018). Seven of eight classes move toward their actuals; this one "
    "does not, and it is not to be closed by putting hydro back. "
    "(d) C7 COAL_PRB is UNCHANGED and still FAILs in all three years. The level "
    "fix does not touch MISO's diurnal-shape blocker (miso-96/102) and does not "
    "claim to. "
    "(e) THE FORECAST PATH IS NOT FIXED. The forward hydro level is a multi-year "
    "NG: WAT climatology and inherits the same contamination. Replacing it needs "
    "its own derivation and its own forecast-lane gates, so it is OUT of scope "
    "here and now emits a loud warning instead of failing silently. "
    "(f) STANDING HAZARD, recorded not actioned: the hydro dispatch ENVELOPE "
    "(HYDRO_ENVELOPE_PERCENTILE) and MIN-FLOW FLOOR (HYDRO_MIN_FLOW_PERCENTILE) "
    "are also built from hourly NG: WAT and inherit the contamination. Both are "
    "default-off and off in this keeper, so nothing is stacked today -- but "
    "arming either at a listed ISO needs its own source fix first, and EIA-923 "
    "is monthly so it offers no hourly substitute. "
    "(g) PJM IS A LIVE DEFECT AND IS DELIBERATELY NOT FIXED HERE. The same "
    "three-signature screen run across all six ISOs finds PJM far worse "
    "(+52.9 % to +79.6 % vs its 923 HY budget, breaching conventional nameplate "
    "in 1,249-1,612 h/yr). Adding 'PJM' to the registry is one line, but it "
    "moves PJM's keeper and owes PJM's own A/B and re-gate -- its lane, not this "
    "one (rule 25). NEISO is a TIME SPLIT (it files NG: PS from Nov 2024) and "
    "needs a per-window treatment rather than a switch. ERCOT, CAISO and NYISO "
    "are screened clean. "
    "(h) MATERIALITY, PLAINLY: this is a ~0.5 %-of-energy correction that moves "
    "mean LMP by 5-9 cents/MWh. A reader who values only headline fit should "
    "read it as neutral. The case for it is rule 14 [R-ACCURATE] plus rule 1 "
    "[R-STRUCT]: the LEVEL and the UNITS are now the same measured population, "
    "and the model no longer generates 1.1-1.5 TWh/yr of conventional hydro that "
    "MISO's conventional hydro fleet cannot physically produce."
)


def main() -> int:
    """Write the arm's attestation, inheriting the keeper's ledger unchanged."""
    att = json.loads(KEEPER.read_text())
    att["governance"] = dict(att.get("governance", {}), attested_by=ATTESTED_BY)
    att["disclosures"] = dict(att.get("disclosures", {}), note=DISCLOSURE)
    ARM.write_text(json.dumps(att, indent=1) + "\n")
    print(f"wrote {ARM.relative_to(REPO)}")
    print(f"  exceptions inherited unchanged: {len(att.get('exceptions', []))}")
    print(
        "now run: python scripts/build_dof_ledger.py "
        f"{ARM.parent.relative_to(REPO)} --iso MISO"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

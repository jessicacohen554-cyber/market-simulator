"""Emit the SPP-43 calibration attestation for the 2019-2022 unit-outage intake.

SPP-43 arms **no new ``ScenarioConfig`` field and changes no config at all**.
It is a pure DATA INTAKE: SPP's CAMPD unit-outage extracts covered 2023-2025
only, so in the held-out years 2019-2022 the LP's availability was the flat
EFOR baseline and every outage-conditioned mechanism was inert there. The
intake derives those four years with the deriver's own frozen settings and
APPENDS them, leaving the 2023-2025 block byte-identical.

The run this attests is SPP keeper 12's recipe
(``2026-09-16-spp-42-commitment-feasibility``) replayed UNREVISED on 2019-2022
with the extended extract in place — the successor to the stamped touchpoint
``2026-09-13-spp-40-holdout-span``.

**Why this exists rather than ``scripts/gen_touchpoint_attestation.py``.** The
same two reasons SPP-42 recorded, both still live: that shared helper refuses a
multi-tier year span on a ``holdout_policy.tier_for_year`` guard that
``[R-HOLDOUT]``'s removal (2026-09-09) made stale, and ``replay_keeper
--out-dir`` does not propagate ``calibration_attestation.json`` into the
out-dir, so without this the bundle would score C6 ``UNATTESTED`` for a
plumbing reason rather than a governance one. Both are shared infrastructure
and repairing them is not this lane's object (rule 25 ``[R-ISO-SCOPE]``).

**ZERO free parameters are added and none is re-cut** (rules 21 ``[R-DOF]`` /
24 ``[R-REGISTRY]``): no field, threshold, share, multiplier, gate or CLI input
moves, and ``offer_curve_by_group`` is replayed byte-identically.

Usage:
    python scripts/gen_spp43_attestation.py --bundle results/calibration/spp43_holdout_span
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp42_span_a/calibration_attestation.json"
DEFAULT_BUNDLE = REPO / "results/calibration/spp43_holdout_span"

OFFER_SHA = "090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65"

_ATTESTED = (
    "SPP-43 (2026-09-16), the 2019-2022 CAMPD unit-outage intake. SPP keeper "
    "12's recipe (2026-09-16-spp-42-commitment-feasibility) replayed UNREVISED "
    "on the held-out span with NO config change whatsoever — no --set, zero "
    "differing behavioural ScenarioConfig keys, offer_curve_by_group "
    f"byte-identical (SHA-256 {OFFER_SHA}). The ONLY thing that moves is a "
    "MEASURED INPUT that was previously ABSENT for these four years. "
    "THE DEFECT IT REPAIRS, measured at ZERO LP before any arm was solved: "
    "campd-unit-outages-SPP.csv carried 880/905/936 windows in 2023/2024/2025 "
    "and ZERO rows in 2019-2022 (likewise the short companion), so availability "
    "in the held-out years was the flat EFOR baseline and every "
    "outage-conditioned mechanism was inert there — which is why SPP-42's "
    "commitment-feasibility clip measured '0 infeasible plant-hours, 0.0 MWh "
    "released' across all four years, and is the stated root cause of SPP-40's "
    "held-out C8 ST_GAS forced-share breach. "
    "THE SOURCE SURVEY CAME FIRST AND IS WHAT LICENSED THE INTAKE (rule 29 "
    "[R-SCREEN] step 0, scripts/probes/_spp43_source_survey.py): 13 of SPP's "
    "14 CAMPD detection states carry a complete Jan-1-to-Dec-31 unit-level "
    "parquet in EVERY year 2019-2025, and the 14th (CO) is absent in every year "
    "INCLUDING 2023-2025, so the committed block was itself derived on the same "
    "13-state panel and the gap is purely TEMPORAL, never spatial. Fleet CEMS "
    "coverage in 2019-2022 equals or exceeds the in-sample years (112/109/107/"
    "107 model plants against 107/105/106; ST_GAS 19/18/17/17 against 17/17/17; "
    "COAL 26/25/24/24 against 24/23/23), and all four plants carrying SPP-42's "
    "residual D-4 failures (1230 / 1235 / 1271 / 3008) file CEMS in all seven "
    "years. "
    "RULE 23 [R-FROZEN-DERIVE] IS SATISFIED IN ITS OWN TERMS: extending an "
    "extract's YEAR RANGE on unchanged source data is a FIRST derivation for "
    "those years, not a re-derivation against a residual. No detector "
    "threshold, no constant and no setting was touched — the intake invocation "
    "differs from the committed one in --years and nothing else — and the "
    "derived years were never compared against a residual before being kept. "
    "ADDITIVITY IS PROVEN, NOT ASSERTED. The diff of the committed extract "
    "against the extended one is 3,803 additions and ZERO removals (short "
    "companion: 1,069 / 0), the committed block's bytes are unchanged including "
    "line positions (sha256 over the original byte length is equal), no new row "
    "has outage_end >= 2023-01-01, and — the statement that actually matters — "
    "the LP's OWN 2023-2025 availability multiplier arrays are BYTE-IDENTICAL "
    "before and after, all six of them (std/short x 2023/2024/2025, sha256 over "
    "the sorted (plant_code, plant_group) -> float64 arrays). The keeper's "
    "scored years therefore CANNOT move and were deliberately not re-solved. "
    "RULE 13 [R-MEASURED]: the extract is the admissible class the rule names "
    "in its own text — a unit outage window is a PHYSICAL AVAILABILITY EVENT "
    "entering as a formulaic input, not a measured OUTCOME fed back to close a "
    "residual. It pins no unit to its observed generation, adds no offset, "
    "haircut or adder, and rescales nothing so the model's output lands on an "
    "actual. The identical construction regenerates for a forward year from "
    "that year's own EFOR/maintenance envelope. "
    "RULE 14 [R-ACCURATE] IS THE BASIS AND THE RESIDUAL IS NOT: the flat EFOR "
    "baseline is an ESTIMATE standing in for measured availability that exists "
    "on disk, so it is replaced. Whatever this does to the fit is a RESULT, "
    "never the reason — a degraded criterion is a discovered root cause to "
    "route, not grounds to revert the accurate input. "
    "RULE 29 [R-SCREEN]: NO screen gate and NO residual gate, on the precedent "
    "SPP-38's vintage repair set and SPP-42's promotion note records verbatim — "
    "the screen applies to a candidate MECHANISM competing against a correct "
    "one, and a MISSING measured input is not a candidate mechanism. Phase 0 "
    "was nonetheless done in full and is what set the scope (two probes, both "
    "committed). Rule 29(b) form 4 holds: the control is the COMMITTED "
    "2026-09-13-spp-40-holdout-span bundle (results/calibration/spp40_holdout), "
    "differenced, with NO control solve. Its validity is established by a chain "
    "whose weak link was already closed by an actual re-solve — SPP-42 solved "
    "these same four years at its own base and reproduced that bundle "
    "byte-identically, and G-DRIFT from the keeper-12 promotion commit to this "
    "base finds ZERO changed hunks anywhere on the solve path "
    "(src/market_sim, run_calibration{,_full}.py, replay_keeper.py, scripts/lib, "
    "data/raw/_validation-source, data/raw/reference). "
    "REPORTED AT THE GATE, NOT DISCOVERED. (1) A REPRODUCIBILITY DEFECT IN THE "
    "FROZEN BLOCK, found by deriving 2023-2025 at HEAD as a control and "
    "deliberately NOT folded in: HEAD emits 103 rows the committed block does "
    "not carry, all plant 762 (Ponca) units 3-4, ST_GAS, with ZERO removals. "
    "Ponca reaches the deriver only through load_retired_within_window, so the "
    "frozen block predates that scope. Changing it would move the keeper's "
    "SCORED years and is a separate lane's object; the 2019-2022 block IS "
    "derived at HEAD scope and therefore DOES carry Ponca, because rule 14 "
    "forbids degrading an accurate input to match a stale one. The short "
    "extract reproduces BYTE-IDENTICALLY at HEAD (coal-only scope, which Ponca "
    "is not in). (2) The bundle's shared-input hash for `unit_outages` no longer "
    "matches what spp42_span_a recorded, because the FILE changed even though "
    "its 2023-2025 rows did not; the block is provenance only and replay "
    "ignores it by design, so nothing gates on it. (3) THE HELD-OUT C8 NUMBER "
    "MUST BE READ WITH ITS DENOMINATOR: ST_GAS forced_share read 0.3423/0.3014/"
    "0.5041/0.5556 in the SPP-40 control and 0.2497/0.2844/0.4559/0.4995 on "
    "this base BEFORE this intake, and that movement is NOT a model change — "
    "forced_twh was byte-identical and only the benchmark-side denominator "
    "(class_total_twh) moved between bases. Any claim this lane makes about C8 "
    "separates numerator from denominator before making it. "
    "RULE 30 [R-TOUCHPOINT-FOLD] (c): a held-out year REPORTS and can neither "
    "certify nor decertify — SPP's headline determination remains the 2023-2025 "
    "train-tier verdict however these rungs score, and since [R-HOLDOUT]'s "
    "removal no year in this program is a certified out-of-sample number."
)


def build(bundle: Path) -> dict:
    """Return the SPP-43 attestation for the bundle: keeper 12's ledger + this run's governance."""
    att_path = bundle / "calibration_attestation.json"
    att = (
        json.loads(att_path.read_text())
        if att_path.exists()
        else json.loads(KEEPER.read_text())
    )
    fp = att["free_parameters"]
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    gov = att["governance"]

    # Rule 1 [R-STRUCT] (b): `years_held` is an EXACT SET EQUALITY check against
    # THE RUN'S OWN scored years in calibration_verdict._authorized_tuning_finding.
    # Re-cut it off the bundle's dispatch parquets so it cannot drift from what
    # was actually solved (the SPP-40 / SPP-42 construction, same reason).
    apt = gov["authorized_price_tuning"]
    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")
    apt["years_held"] = solved_years
    apt["years_held_basis"] = (
        "SPP-43 (2026-09-16). Re-cut to THIS run's own solved years, read off "
        "dispatch/<year>_P1.parquet. A statement about WHICH YEARS THIS RUN "
        "HOLDS THE CONFIG ACROSS, never a re-tuning: offer_curve_by_group is "
        f"byte-identical to keeper 12's (SHA-256 {OFFER_SHA}), this lane passes "
        "NO --set at all, and no band, class or value moved. Condition (c) is "
        "untouched — the value was set ex ante and was not swept here."
    )

    gov["dof_inherited_from"] = "spp42_span_a (SPP keeper 12)"
    gov["dof_inheritance_basis"] = (
        "SPP-43 changes NO ScenarioConfig field. It extends a MEASURED INPUT's "
        "year coverage and nothing else, so nothing is added to the ledger and "
        "nothing is re-cut. Machine-confirmed rather than asserted: "
        "build_dof_ledger.py --iso SPP at HEAD emits the same entry count as "
        "keeper 12's own ledger on this bundle. The authorized price-tuning "
        "channel is replayed BYTE-IDENTICALLY (offer_curve_by_group SHA-256 "
        f"{OFFER_SHA}); the rule-23-frozen thermal_tranches_SPP.csv is neither "
        "regenerated nor touched, and campd-unit-outages-short-SPP.csv is "
        "EXTENDED into years it did not cover — an additive first derivation "
        "whose committed 2023-2025 block is byte-identical, which is exactly "
        "what rule 23 permits and is proven above rather than claimed."
    )
    gov["attested_by"] = _ATTESTED

    gov.setdefault("measured_input_switches", {})["campd_unit_outages_2019_2022"] = {
        "value": True,
        "where": (
            "data/raw/campd-unit-outages-SPP.csv and "
            "data/raw/campd-unit-outages-short-SPP.csv -> "
            "market_sim.data.outages.unit_outage_derate_factors / "
            "unit_outage_short_derate_factors -> the LP's availability[g, t] "
            "generator bound. No new gate: the keeper already reads both files "
            "(outage_source='historic', unit_outage_short_windows=True); they "
            "simply had no rows in these four years."
        ),
        "identification": "measured-physical-availability-event",
        "source": (
            "EPA CAMPD hourly unit-level gross generation, "
            "data/raw/campd-unit-level/{STATE}_{YEAR}.parquet, 13 states x 4 "
            "years, derived by scripts/data/derive_campd_unit_outages.py at its "
            "FROZEN settings (min_outage_days 5.0 / 1.0, fullstop override "
            "5 d @ CF 0.02, high_load_pctl 0.85, min_inmerit_hours 24 / 6, "
            "merit_order_guard off) — identical to the committed block's "
            "recorded derive_invocation in every field except --years."
        ),
        "warrant": (
            "Rule 14 [R-ACCURATE]: measured availability exists on disk for "
            "these years and the model was using a flat EFOR estimate instead. "
            "The accurate input replaces the estimate, and a worse fit would be "
            "a discovered root cause to route rather than grounds to revert."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED] PASSES: a unit outage window is the rule's own "
            "named example of an admissible physical availability event. It is a "
            "formulaic input, not a measured outcome — nothing is pinned to "
            "observed generation, no offset/haircut/adder is added, and no input "
            "is rescaled so the model's output lands on an actual. The same "
            "quantity is produced for a forward year from that year's own "
            "EFOR/maintenance envelope and responds to changed conditions."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: no second mechanism is introduced. The two "
            "overlays the keeper already reads are disjoint by construction "
            "(>= 5 d standard vs < 5 d short, the latter defensively re-filtered "
            "to COAL), and mustrun_layup_window_mask stays OFF, so the lay-up "
            "double-subtraction SPP-42 measured (1089 of 1089 rows already in "
            "the standard extract) is not reachable."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: SPP's own extract files only. No other ISO's "
            "extract, detector setting or keeper is touched, and no number "
            "crosses an ISO boundary."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: no new tunable. The consuming flags "
            "(outage_source, unit_outage_short_windows) are already in "
            "ScenarioConfig and in this bundle's run_config.json; the artifact's "
            "own provenance is recorded in its .meta.json sidecar, which now "
            "carries BOTH derive invocations and the composition note."
        ),
    }
    return att


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
    args = ap.parse_args()
    att = build(args.bundle)
    out = args.bundle / "calibration_attestation.json"
    out.write_text(json.dumps(att, indent=2) + "\n")
    fp = att["free_parameters"]
    print(
        f"{args.bundle.name}: attestation written — "
        f"years_held={att['governance']['authorized_price_tuning']['years_held']} "
        f"n_entries={fp['n_entries']} n_residual={fp['n_residual']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

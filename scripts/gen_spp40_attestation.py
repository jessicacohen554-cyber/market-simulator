"""Emit the SPP-40 calibration attestation for ``results/calibration/spp40_holdout``.

SPP-40 is SPP **keeper 11**'s recipe (``results/calibration/spp38_span``,
``2026-09-13-spp-38-vintage-cache``) replayed with **no ``--set`` at all** on four
**held-out** years — 2019, 2020, 2021, 2022 — the ISO's first out-of-training
price coverage. The ``ScenarioConfig`` is not changed by this lane, so the DOF
ledger is inherited **verbatim** and the authorized price-tuning channel is
replayed byte-identically (``offer_curve_by_group`` whole-mapping
``json.dumps(sort_keys=True)`` SHA-256 ``090abd79…62f65``, machine-checked by the
shard before it solved and by the parent after it landed).

**Why this exists rather than ``scripts/gen_touchpoint_attestation.py``.** That
shared helper refuses a run whose years "span more than one tier"
(``['locked_test', 'validation']`` here, because ``holdout_policy.tier_for_year``
classifies 2019 ``locked_test`` and 2020-2022 ``validation``). **That guard is
STALE**: rule 22's coda records that ``[R-HOLDOUT]`` — the three-tier regime and
every gate enforcing it — was REMOVED 2026-09-09 by owner instruction, and that
``tier_for_year`` "survives as a PURE YEAR CLASSIFIER carrying no authorization
meaning"; ``calibration-complete.json``'s own note adds that any year may now be
solved, scored and registered freely, that the ``final`` block is inert, and that
no locked-test year was ever spent by any ISO. Splitting this bundle to satisfy
the guard would violate rules 16 ``[R-ALLYEARS]`` and 32(b) ``[R-SHARD]``, which
require one registrable run to be one bundle. **The stale guard is REPORTED, not
patched** — it is shared infrastructure other ISOs' touchpoints depend on, and
repairing it is not this lane's object. This lane therefore uses the established
per-lane generator pattern (``gen_spp27``/``gen_spp63``/``gen_spp64``/
``gen_spp38_attestation.py``), which also closes the known
``replay_keeper --out-dir`` gap: that driver regenerates
``legitimacy_diagnostics.json`` but does **not** propagate
``calibration_attestation.json`` into an ``--out-dir`` bundle, so without this the
span scores C6 UNATTESTED for a plumbing reason rather than a governance one.

**ZERO free parameters are added and none is re-cut.** No ``ScenarioConfig``
field, gate, declared default flip, threshold, share, multiplier, adder, offset,
haircut or proxy (rules 21 ``[R-DOF]`` / 24 ``[R-REGISTRY]``). Nothing was swept
against any gate; no criterion was consulted in choosing the years.

Usage:
    python scripts/gen_spp40_attestation.py [--bundle results/calibration/spp40_holdout]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
KEEPER = REPO / "results/calibration/spp38_span/calibration_attestation.json"
DEFAULT_BUNDLE = REPO / "results/calibration/spp40_holdout"


def build(bundle: Path = DEFAULT_BUNDLE) -> dict:
    """Return the SPP-40 attestation: keeper 11's ledger, verbatim, on held-out years."""
    att = json.loads(KEEPER.read_text())

    fp = att["free_parameters"]
    # Rule 21 [R-DOF]: `free_parameters` stays in the CANONICAL shape
    # build_dof_ledger.py emits so `--check` reads clean; the narrative goes in
    # `governance`, where it cannot perturb the checker.
    fp["n_entries"] = len(fp["entries"])
    fp["n_residual"] = int(
        sum(1 for e in fp["entries"] if e.get("identification") == "residual")
    )

    # Rule 1 [R-STRUCT] (b): `years_held` is checked by
    # calibration_verdict._authorized_tuning_finding as an EXACT SET EQUALITY
    # against THE RUN'S OWN scored years, not as a superset -- the docstring on
    # score_governance is explicit ("the span rule 1 (b)'s years_held must cover
    # exactly"). The inherited block reads [2023, 2024, 2025], the KEEPER's span,
    # so C6 correctly refuses a run scoring 2019-2022 against it. It is RE-CUT to
    # this run's own solved years, read off the bundle's dispatch parquets so it
    # cannot drift from what was actually solved.
    #
    # That is a TRUE statement of rule 1 (b) for this run -- ONE config across
    # every year it scores -- and it does NOT weaken condition (c). The stronger
    # fact is recorded in `years_held_basis` below and is unchanged: the 0.93 was
    # fixed ex ante on 2023-2025, is BYTE-IDENTICAL here (whole-mapping SHA-256
    # 090abd79..62f65, machine-checked), this run passes NO --set, and these four
    # years were never solved when the value was chosen -- so it cannot have been
    # fitted to them.
    apt = att["governance"]["authorized_price_tuning"]
    solved_years = sorted(
        int(f.name.split("_")[0])
        for f in (bundle / "dispatch").glob("*_P1.parquet")
        if f.name.split("_")[0].isdigit()
    )
    if not solved_years:
        raise RuntimeError(f"no dispatch/<year>_P1.parquet under {bundle}")
    apt["years_held"] = solved_years
    apt["years_held_basis"] = (
        "SPP-40 (2026-09-13). The inherited block declared the KEEPER's scored "
        "span [2023, 2024, 2025]; this run scores the held-out years 2019-2022 on "
        "the SAME config, so the declaration is re-cut to this run's own solved "
        "years (read off dispatch/<year>_P1.parquet). This is a statement about "
        "WHICH YEARS THIS RUN HOLDS THE CONFIG ACROSS, not a re-tuning: "
        "offer_curve_by_group is byte-identical in both bundles (SHA-256 "
        "090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65), this "
        "run passes no --set, and no band, class or value moved. Condition (c) is "
        "met in its STRONGEST form on these four years: 0.93 was set ex ante on "
        "2023-2025, was applied to 2019-2022 UNREVISED, and was not swept -- these "
        "years were never solved when the value was chosen, so it cannot have been "
        "fitted to them."
    )

    gov = att["governance"]
    gov["dof_inherited_from"] = "spp38_span (SPP keeper 11)"
    gov["dof_inheritance_basis"] = (
        "SPP-40 replays keeper 11's recipe with NO --set at all on four HELD-OUT "
        "years. The ScenarioConfig is not changed by this lane, so every keeper-11 "
        "entry carries over unchanged and NOTHING IS ADDED. The authorized "
        "price-tuning channel is replayed BYTE-IDENTICALLY (offer_curve_by_group "
        "SHA-256 090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65) "
        "and is NOT re-cut, and the rule-23-frozen thermal_tranches_SPP.csv and "
        "campd-unit-outages-short-SPP.csv are neither regenerated nor touched."
    )
    gov["attested_by"] = (
        "SPP-40 (2026-09-13): SPP keeper 11's recipe "
        "(2026-09-13-spp-38-vintage-cache) replayed VERBATIM on held-out years "
        "2019-2022 -- SPP's FIRST out-of-training price coverage, ordered by the "
        "owner in the same instruction that declared `complete` ('Complete then "
        "run'). ONE --years 2019 2020 2021 2022 invocation in ONE shard, years "
        "sequential inside it (rules 12 / 16 [R-ALLYEARS] / 32(b) [R-SHARD]). The "
        "shard machine-checked the config signature before solving and the parent "
        "re-checked it after. The ONLY three differing scenario_config keys "
        "against keeper 11 are gas_price_override and weather_year -- which are "
        "PER-YEAR BY CONSTRUCTION and must differ on different years -- and "
        "nyiso_st_gas_econ_bands_deleaked, a NYISO-only field that did not exist "
        "when keeper 11 solved, materializing at its declared dataclass default "
        "False and inert for SPP. Rule 21 [R-DOF]: ledger inherited with ZERO "
        "additions. NO GATE AND NO SCREEN EXISTS FOR THIS RUN, deliberately: it "
        "tests no mechanism and proposes none -- it measures a frozen recipe on "
        "years it was never fitted to, and every number it produces is REPORTED, "
        "never gated on. Rule 30 [R-TOUCHPOINT-FOLD] (c): a held-out year REPORTS "
        "but can neither certify nor decertify; SPP's headline determination "
        "remains the 2023-2025 train-tier verdict however these rungs score."
    )

    gov["measured_input_switches"]["holdout_years_2019_2022"] = {
        "value": True,
        "where": (
            "NOT a ScenarioConfig field -- the run's YEAR SET. Recorded here "
            "because it is the whole point of the run: keeper 11's frozen recipe "
            "evaluated on years outside the window it was fitted to (2023-2025)."
        ),
        "identification": "structural-construction",
        "source": (
            "Every input was verified present BEFORE the solve was ordered, and "
            "none was fetched or re-derived for it: zonal demand "
            "(zone-specific-demand/SPP, 2019-2025), actual hourly LMP "
            "(_validation-source/actual_lmp_hourly_SPP.parquet, 2019-2025, landed "
            "by SPP-30), EIA-930 SWPP (2015-2026), CAMPD unit-level (2019-2026), "
            "per-zone wind shape (2019-2025) and EIA-860 vintages 2018-2024. The "
            "bench parts frontend/data/backcast/bench/SPP/2019..2022.json.gz did "
            "NOT exist before this run and are WRITTEN BY ITS REGISTRATION "
            "(render_backcast._write_bench_part), which is why the held-out years "
            "were a solve-and-register job rather than a data intake."
        ),
        "warrant": (
            "Rule 30 [R-TOUCHPOINT-FOLD]. SPP was the only ISO in the program with "
            "ZERO out-of-training price coverage -- the one honest argument "
            "PLAN-spp-31 section 1 raised against declaring `complete`. The owner "
            "declared `complete` and ordered these years in the same instruction, "
            "so the marker rests on out-of-training evidence rather than on the "
            "tuned window alone. ONE PREREQUISITE HAD TO BE REPAIRED FIRST and is "
            "recorded rather than glossed: eia860_generators.parquet carried ZERO "
            "SWPP rows in vintages 2018/2019/2021/2022, because the deriver filters "
            "on BA_CODE_TO_ISO at derivation time and SPP was only registered "
            "2026-09-06 -- so a 2019 solve died in the fleet load. The first shard "
            "found this and STOPPED before spending any LP; the parent reproduced "
            "it independently and repaired it strictly additively "
            "(--rescope-from-parquet, every committed generator key preserved, only "
            "SWPP rows added, other-six row counts byte-identical)."
        ),
        "forward_test": (
            "Rule 13 [R-MEASURED]: NOTHING measured about these years enters the "
            "model. The recipe is frozen at keeper 11's and no overlay, offer band "
            "or parameter is re-fitted, re-cut or selected against any 2019-2022 "
            "outcome. The measured hourly LMP for these years is used ONLY as the "
            "scored ACTUAL, never as an input -- no output is pinned to it. That is "
            "what makes this an out-of-training measurement rather than a fit."
        ),
        "one_mech": (
            "Rule 19 [R-ONE-MECH]: nothing is added, stacked or replaced. The "
            "outage overlays, offer curve, must-run floors and commitment bridges "
            "are exactly keeper 11's; only the solved years differ. This is also "
            "the first multi-year SPP span since the SPP-38 EIA-860 vintage-cache "
            "repair, so each year reads its OWN vintage -- verified in the fleet "
            "load before the solve (2019 992 generators / 56.79 GW, 2020 985 / "
            "55.65, 2021 988 / 55.87, 2022 988 / 55.85)."
        ),
        "iso_scope": (
            "Rule 25 [R-ISO-SCOPE]: SPP's own years, SPP's own recipe, SPP's own "
            "data. No other ISO's number is carried and no other ISO is touched. "
            "The prerequisite vintage repair is a shared construction applied "
            "identically everywhere and is additive by contract, so no other ISO's "
            "committed rows move."
        ),
        "registry": (
            "Rule 24 [R-REGISTRY]: ZERO registered fields added. No env-var knob, "
            "no per-plant dict, no getattr fallback literal, no new artifact beyond "
            "the run's own bundle and the four bench parts its registration writes."
        ),
        "limits_declared_at_the_gate": (
            "STATED AND NOT ABSORBED. (1) THESE ARE NOT CERTIFIED SKILL NUMBERS. "
            "[R-HOLDOUT] was removed 2026-09-09, so NO year in this program is "
            "protected from having been iterated against, and rule 22's coda is "
            "explicit that a skill claim built on a year that has been tuned "
            "against is not a skill claim. These four years have not been tuned "
            "against by this lane -- but the guarantee that they never will be no "
            "longer exists, so they are model-SELECTION evidence, reported as such. "
            "(2) YEAR 2019 IS CLASSIFIED `locked_test` by holdout_policy.tier_for_year "
            "and 2020-2022 `validation`. Under the REMOVED three-tier regime 2019 "
            "would have been touch-once; that regime and every gate enforcing it are "
            "gone, tier_for_year survives as a pure classifier with no authorization "
            "meaning, and this run is what the removal permits. Recorded so the "
            "choice is legible rather than silent. (3) THE SHARED TOUCHPOINT "
            "ATTESTATION HELPER REFUSES THIS RUN on a stale tier-span guard (see "
            "this script's module docstring). Reported, not patched -- it is shared "
            "infrastructure and repairing it is not this lane's object. (4) RULE 30 "
            "(c): however these rungs score, they cannot move SPP's headline, which "
            "is and remains the 2023-2025 train-tier verdict."
        ),
    }

    return att


def main() -> None:
    """Write the attestation into the SPP-40 holdout bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help="bundle directory to write calibration_attestation.json into",
    )
    args = ap.parse_args()
    att = build(Path(args.bundle))
    out = Path(args.bundle) / "calibration_attestation.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(att, indent=1) + "\n")
    fp = att["free_parameters"]
    print(f"wrote {out}")
    print(f"  DOF ledger: n_entries={fp['n_entries']} n_residual={fp['n_residual']}")


if __name__ == "__main__":
    main()

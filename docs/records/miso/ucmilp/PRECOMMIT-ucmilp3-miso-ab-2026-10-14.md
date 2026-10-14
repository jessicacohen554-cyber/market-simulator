# PRECOMMIT — UC-3-MISO: clean MILP-UC A/B at uc-1.4+, arm A (every floor kept) and arm B (ST_GAS per-plant floor off)

**Written and pushed BEFORE any span shard exists.** Every reading, bar, kill and budget below is fixed here. Charter: UC-DESK
`session_01WX9W5tgYMre3Z134LZoGF6`, owner ruling 2026-10-14 *"Go with your recommendations"*: decision 7 = relaunch every UC-2
ISO at uc-1.4; decision 6 = the MISO un-stack arm. Recorded in `docs/uc-milp-program-plan-2026-10.md` §11 r09 and the §12 register
(`05e3164a`, PR #7240). Lane session `session_01XhMwoXKrbRPUQzQ9UuZRbB` (Opus), branch `claude/ucmilp-3-miso-ab`.

**Predecessor:** `PRECOMMIT-ucmilp-miso-ab-2026-10-10.md` (§§1–10 + Addenda A–H, "the UC-2 PRECOMMIT") and
`RESULT-ucmilp-miso-ab-2026-10-10.md` (R: kill #3 on 2024, T2 wrong sign, C8 ST_GAS / C4 flips). Every UC-2 reading was solved at
uc-1.2 and is confounded by engine defect 6 (the cluster floor was spread pro rata across offer tranches, so peak tranches were forced
on). Rule 1 [R-STRUCT]: that R is not a structural rejection. This lane re-measures the same arm on a clean engine and adds arm B.

## 0. Status: LAUNCH HELD for the FIX-5 pin

UC-DESK (2026-10-14 11:38Z): a probable engine defect 7 (UC no-load double count, lane UC-1-FIX-5) is in repro. A solve at `580c4fbf`
would be confounded again. **No shard launches until UC-DESK names the FIX-5 merge SHA.** Addendum A then records the pin, the
G-DRIFT `580c4fbf → <pin>` and the regenerated prompts. Nothing else in §§1–7 may change at that addendum.

## 1. Control, arms, pin

- **Control = the incumbent keeper's committed bundle** `results/calibration/closeout_miso_nuc_span` (rule 29(b): no control solve),
  unchanged since the UC-2 pins (§2 G-DRIFT). Registered grade summary at the UC-2 PRECOMMIT §0: 8 scored / 4 target / 1 ledgered /
  3 FAIL, NOT-YET.
- **Arm A = the UC-2 arm, unchanged:** `replay_keeper.py results/calibration/closeout_miso_nuc_span --years <y>
  --set unit_commitment_milp=true`. The offs set is empty, every floor is kept (UC-2 PRECOMMIT §1 rule-19 census), and every `uc_*`
  field stays at its declared default, never swept. `uc_slim_window = True` (born default) and `coal_sync_floor_release = False`
  (default, not armed).
- **Arm B = arm A + `--set st_gas_mustrun_per_plant=false`** (owner decision 6, rule 19 [R-ONE-MECH] un-stack). The knob was
  confirmed zero-LP at `580c4fbf`:
  - **Where it lives.** `ScenarioConfig.st_gas_mustrun_per_plant` (`scenarios.py:16479`, default `False`). The keeper arms it only
    through `meta.json → coal_prb_sigmoid_overrides` (no `iso_configs` entry). `replay_keeper --set` writes the same `prb_overrides`
    key, so `false` wins.
  - **Registry off-switch.** `floor_mechanisms.py:347` declares `{"st_gas_mustrun_per_plant": False}` as the off posture of
    `MECH_ST_GAS_MUSTRUN_PER_PLANT`. No registry `--no-` flag exists for it; `--set …=false` is that posture.
  - **Sub-flags go inert with it.** The keeper's level-swap sub-flags `st_gas_mustrun_p25_level`, `…_p25_measured_level` and
    `…_oom_level` stay recorded `true`. They act only when `st_gas_mustrun_per_plant` is on (`arrays.py:3726–3730` gates the block
    that holds the oom branch), so they are not a second delta.
  - **Nothing backfills the floor.** The SOCO gas-steam campaign floor (`commitment.py:2645`) is off in the keeper
    (`soco_gas_st_campaign_commitment: false`). No other mechanism picks up those plants once the floor is off. The UC stage
    (MECH 28) is then the one mechanism that commits ST_GAS, which is exactly what decision 6 asks.
- **Recipe verification gate per leg** (UC-2 PRECOMMIT §1 as stated in its Addendum H): every field the keeper's
  `run_config_<y>.json` records is equal (per-year `gas_price_override`, `gas_offer_margin_anchor`, `weather_year`, and for 2023–25
  `miso_measured_reserve_requirements` and `miso_reserve_online_gated`). The fields allowed to differ are:
  - **Arm A:** `unit_commitment_milp`, the `uc_*` defaults, and default-off fields the keeper predates.
  - **Arm B:** those, plus `st_gas_mustrun_per_plant = false`.
  - Any other difference is a recipe break, and that leg is not composed.
- **Pin:** the FIX-5 merge SHA, a full 40-char SHA recorded in Addendum A. The lane branch is cut from `580c4fbf`; at the pin it is
  merged forward (merge, not rebase) so that `source_revision` = this branch's head, which contains the pin.

## 2. G-DRIFT (zero LP, rule 29(b))

**`eab17188` (UC-2 final pin, UC-2 Addendum F) → `580c4fbf`.**
- `solve_surface_register.py --diff eab17188 580c4fbf`: *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*.
- `git diff --stat` over `src/ scripts/ configs/`, the control bundle, `keepers/MISO.json` and `data/dictionary/schema` touches
  **4 files**:

| hunk | files | MISO classification |
|---|---|---|
| uc-1.3 merit-order cluster-floor fill (`merit_floor_allocation`), pass-2 reuse by input digest, `UC_ENGINE_VERSION = "uc-1.4"` | `pipeline/uc.py` (+259/−18) | **LIVE on both arms only.** It is reached solely through `pipeline/solve.py:676` and `runner.py:4176`, both behind `unit_commitment_milp`, and neither changed. Control: INERT |
| uplift priced in-process at `mc_base`; `uplift_from_bundle` deleted | `model/uc/uplift.py` | LIVE on the arms (uplift reading W3 only; no dispatch effect). Control: INERT |
| uc-1.4 P1 floor `mlf·p̄·a·u` (availability-scaled) | `model/uc/schedule.py` | **LIVE on both arms**, the defect-6 fix the lane exists to measure. Control: INERT |
| composer no longer recomputes uplift from the bundle | `scripts/probes/_ucmilp_compose_span.py` | compose only, no solve. **Consequence:** a leg missing `uc_uplift_<y>.parquet` reports W3 as absent, so the shard addendum makes that file a required push |

**`2f872a62 → eab17188`** is classified in UC-2 Addendum F (control INERT). Since `2f872a62`, the non-UC hunks are the
`campd_crosswalk.load_crosswalk` refactor (same output; `camd_to_eia_plant` has no caller outside the uc-params derive) and
`coal_sync_floor_release` (default off, the historical branch verbatim). Both were re-read here: **INERT**.

**Conclusion:** nothing is LIVE for MISO outside the UC stage. The control is the committed keeper bundle unchanged, with no control
solve. Addendum A extends the G-DRIFT to the FIX-5 pin under the same rule; any LIVE non-UC hunk there means STOP and report to UC-DESK.

## 3. Readings, bars, kills, verdict: the UC-2 PRECOMMIT, unchanged, applied per arm

- **Target readings T1–T5** (UC-2 §2), **control readings** (§3, including "also gating": every leg's P1 Optimal; unserved +≤ 500 MWh
  vs the keeper; no new D-4 FAIL row), **structure S1–S5** (§4), **cost W1–W5** (§5): verbatim, for arm A and for arm B, each
  against the control.
- **Kills (UC-2 §6), per arm, any one ⇒ that arm is R:**
  1. an infeasible window or a "no incumbent" hard stop (engine defect, routed to UC-DESK);
  2. a non-deterministic schedule (exercised only if a relaunch and its predecessor both complete);
  3. a control flip (§3) in any registered year, including unserved +> 500 MWh.
- **Verdict (UC-2 §7), per arm.**
  - **K candidate:** T1 and T2 met, T3/T4 signs right, no kill, every leg Optimal.
  - **R:** a target moves the wrong way past control, or a kill fires.
  - **I:** no kill and no wrong sign, but |Δ| is below the bar on T1 and T2.
  - **Mixed:** worst row, stated row by row.
  - The lane never promotes.
- **A kill stops the arm's verdict, not the evidence:** legs already launched finish and are composed and scored zero-LP, so the RESULT
  carries the full gate table for both arms (UC-2 Addendum D/H precedent). No re-tune, no relaunch with a changed setting, no `uc_*`
  change.
- **Readings added by the charter (reported, not gating):**
  - forced peak-tranche TWh per year (`_peak*` tranche energy at a UC floor; expect ≈ 0 at uc-1.4);
  - C8 recomputed with and without MECH 28;
  - CC_REGULAR / ST_GAS / coal starts vs CEMS (S2);
  - integer clusters / gate set;
  - TL hits;
  - wall ÷ (P0+P1);
  - the 2024 26-Aug (h5701–5706) unserved event diagnosed zero-LP from the bundles if it recurs;
  - every price move diagnosed by sign × hour class × marginal class from `unit_marginal_<y>`.

### 3.1 Declared costs for arm B (named now so no one reads them later as a surprise; not a rule change)

- **C1 ST_GAS.** The kept floor forces **4.84 / 4.32 / 5.23 / 5.21 / 3.32 / 3.52 / 4.18 TWh** of ST_GAS in 2019…2025 (UC-2 §1 census).
  The control is already model-low on ST_GAS, with **2020 headroom 0.91 TWh** (−7.09 vs ±8.00) and 2021 / 2022 at 2.64 / 2.33 TWh.
  - Turning the floor off removes up to the forced energy, minus whatever the UC re-commits on economics.
  - So arm B is **likely to flip C1 ST_GAS 2020** (PASS → FAIL), which fires kill #3 and reads R.
  - That is the predecessor's kill rule applied as chartered ("unchanged"), stated before any number exists.
  - The RESULT reports the magnitude and the structural readings (S2 ST_GAS starts vs CEMS at 3.1–6.5× in the control, and C8 ST_GAS)
    beside it, so the owner can read structure separately from the gate. Whether a mechanical R on a measured-floor removal should end
    the rule-19 question is the owner's call (D-6 card), not this lane's.
- **C8 ST_GAS** should fall, since the floor is the forced energy C8 counts. This is the expected gain, and it is reported.
- **Price.** Removing must-run ST_GAS energy displaces it with the next merit units. Price-body sign expected **up** in floor-window
  hours, which helps the model-low 2021/2022 C3a and hurts the model-high 2019/2020. Sign only; reported.

## 4. Solve plan (rules 16, 32–36)

- **14 shards = 7 years × 2 arms**, one year per shard. Lanes `ucmilp3-miso-a` / `ucmilp3-miso-b`, branches
  `claude/ucmilp3-miso-{a,b}-<y>`, out-dirs `results/calibration/ucmilp3_miso_{a,b}_<y>`.
  - Prompts: `scripts/shard_prompt.py --iso MISO --year <y> --sha <pin> --lane ucmilp3-miso-{a,b}
    --bundle results/calibration/closeout_miso_nuc_span --set unit_commitment_milp=true [--set st_gas_mustrun_per_plant=false]
    --budget <B>` plus the lane addendum. Staged in `shard-prompts-ucmilp3-miso.txt` at `580c4fbf` (NOT LAUNCHABLE) and regenerated
    at the pin in Addendum A.
  - `create_session`: `source_revision` = the full 40-char SHA of this branch's head (which contains the pin), model
    `claude-opus-5-5`, tag `ucmilp:UC-3-MISO-shard`. PENDING > 45 min: archive and relaunch.
- **Budget B** (UC-2 §5 rule, from the UC-2 wall rows, RESULT §0.2):
  - **2019–2021, 2023–2025: 180 min.** The longest UC-2 MISO total was 5,439 s = 90.6 min; ×1.3 = 118 min; plus 48 min of P0
    variance (2022's P0 went 650 → 3,560 s); plus 10 min for hydrate/regenerate/push = 176 → 180. uc-1.4 adds the merit-fill
    allocation and pass-2 reuse; on ERCOT 2019 it was faster than uc-1.2 (ratio 21.7× → 11.2×).
  - **2022: 720 min** (charter): P0 3,560 s alone sank its 115-min UC-2 budget.
  - A shard near its budget with no artifact stops and reports.
  - Restated in Addendum A if FIX-5 changes the stage's cost.
- **Push:** the full bundle (rule 34), `.gitignore` negation + plain `git add`. **A file > 100 MB is split before commit**
  (charter; the owner need not be asked): `split -b 95m -d <f> <f>.part-`. The parts and a `SPLIT-SHA256.txt` (sha256 of the whole
  file and of each part) are committed. The unsplit file is moved out of the tree, never `git add -f`. The parent reassembles and checks
  the sha256 before composing.
- **On each report:** fetch; `git ls-tree -r <sha> -- <out-dir>` non-empty; check out; verify `dispatch/<y>_P1.parquet` (reassembled if
  split), `uc_schedule_<y>`, `uc_uplift_<y>`, `uc_solve_log_<y>.json`, `unit_marginal_<y>`, and the §1 recipe gate. THEN
  `archive_session` (rule 33).
- **Compose and score zero-LP per arm** with `_ucmilp_compose_span.py` (plus the UC-2 declared scratch workaround if it still aborts
  on `gas_price_override`), then:
  - `calibration_verdict.py --json` on control, A and B;
  - `legitimacy_diagnostics.py` regenerated;
  - M1/M3/M4 via `_ucmilp_benefit_screen.py::screen_year`.
  - The parent runs no LP (rule 32).
- **No registration, no promotion** (E13). Slim spans go under `docs/records/miso/ucmilp/data/ucmilp3_miso_{a,b}_span/`; full
  bundles stay on their shard branches (rule 31).
- **Exit:**
  - `RESULT-ucmilp3-miso-ab-<date>.md` (gate table control → A → B first, wall rows, every reading, kills, verdict per arm, D-6 card);
  - the MISO matrix cell `unit_commitment_milp` stamped;
  - ONE PR, not merged by this lane;
  - `send_message` to UC-DESK.

## 5. DO NOT REDO

UC-2's L1 gate (passed; no new bench at uc-1.4: UC-DESK's ERCOT 2019 repro and the FIX-4 gate cover the engine). No control solve.
No sweep of any `uc_*` field. No third arm.

## Addenda

(none yet; Addendum A = the FIX-5 pin)

## Addendum 0 (2026-10-14 11:47Z, before any shard or number exists): UC-DESK ruling on arm B's verdict

**Source:** UC-DESK `session_01WX9W5tgYMre3Z134LZoGF6`, message of 2026-10-14 11:47Z, answering this lane's §3.1 flag. Desk ruling,
disclosed to the owner, who may overrule before launch. Verbatim core: *"arm B is a rule-19 diagnostic arm, not a promotion candidate.
Kill #3 (control flip) is REPORTED for arm B at full magnitude but is NOT binding on its verdict. Arm B's verdict reads on structure,
against measured data: (i) ST_GAS energy and starts vs CEMS (C1 ST_GAS, starts ratio); (ii) C8 / D-2 forced share with the floor gone;
(iii) unserved = 0 (kill #2 stays binding); (iv) price C3a/C3b, reported, not gating. Arm A keeps the chartered kills unchanged."*

**Arm A:** §3 unchanged.

**Arm B: binding kills.**
- Kill #1 (infeasible window / no incumbent) and kill #2 (non-deterministic schedule) stay binding.
- **Unserved, two corrections recorded with the ruling:**
  - In this PRECOMMIT the unserved bound sits under §3 "also gating" (kill #3's family). Kill #2 is schedule determinism.
  - "Unserved = 0" cannot be met literally in 2024, because the control itself sheds **8,356.9 MWh** in h5701–5706 (UC-2 Addendum H).
  - The desk's intent is read as the existing bound: **P1 unserved ≤ the keeper's + 500 MWh in every year**. This stays BINDING for
    arm B, with the 2024 event diagnosed zero-LP if it recurs.
  - Every other kill-#3 row (control PASS→FAIL flips) is reported at full magnitude and is not binding.
- **P1 Optimal** in every leg stays binding.

**Arm B: verdict rows, fixed now (signs vs control; the bars are the measured actuals, no new threshold):**

| row | reading | "supports un-stack" | "against" |
|---|---|---|---|
| B-i(a) | ST_GAS energy, C1 model − EIA-923 TWh per year (2025 SKIPPED, preliminary vintage) | \|gap\| shrinks or holds | \|gap\| widens; the magnitude and any PASS→FAIL stated |
| B-i(b) | ST_GAS starts, model ÷ CEMS (S2 instrument, on-threshold 1 % of available cap), per year | moves toward 1.0 (control 3.1–6.5×) | moves away from 1.0, or overshoots below 1/control-ratio |
| B-ii | ST_GAS forced share (D-2, all floor mechanisms incl. MECH 28) and C8 ST_GAS, with and without MECH 28; new D-4 FAIL rows | forced share falls; no new D-4 FAIL row | forced share does not fall, or MECH 28 alone re-forces ≥ the removed floor's energy |
| B-iii | unserved bound (above) | holds every year | binding kill |
| B-iv | C3a, C3b per year | reported, not gating | — |

**Arm B verdict wording.** "Structure supports un-stack" requires B-i(b) and B-ii in that column in every scored year, with B-iii holding.
"Structure against" requires either of those in the right column in any year. Anything else is mixed, stated row by row. B-i(a) is the
energy cost, reported beside the verdict and never netted into it.
- **Not resolved by this verdict:** if B-i(a) and B-i(b) disagree (fewer starts but less energy than measured), that is a finding on
  the UC's ST_GAS dispatch level, routed to the owner. The lane does not resolve it.
- **Arm B is not a promotion candidate,** whatever it reads (desk ruling). §3.1's declared costs stand as declared.

## Addendum A (2026-10-14 ~12:55Z, before any shard exists): the pin is uc-1.5; G-DRIFT; launch

**Pin.** UC-DESK, 2026-10-14 12:46Z: *"the uc-1.5 pin is 2dd69d5aa936547b402a1ba54d2eba57e759b7e7 (main; #7246 merged, defect 7 fixed:
UC pays no-load once)"*. `main` was merged into this branch (merge, not rebase).
- **`source_revision` for every shard = `054dc883a91196241fc51e079f64f83d699d7ffa`** (this branch's merge commit).
- Its tree equals the pin's tree except this lane's two docs (`git diff --stat 2dd69d5a 054dc883`: the PRECOMMIT and the prompt file
  only).
- Prompts regenerated with `--sha 054dc883…`. Only the SHA and the engine label changed from the staged text at `a0a7cf1e`.

**G-DRIFT `580c4fbf → 2dd69d5a` (zero LP, rule 29(b)).**
- `solve_surface_register.py --diff`: *"342 → 342 names; 0 value(s) moved, 0 added, 0 removed — NO VALUE MOVED"*.
- `git diff --name-status` over `src/ scripts/ configs/`, the control bundle, `keepers/MISO.json` and `data/dictionary/schema`:

| hunk | files | MISO classification |
|---|---|---|
| uc-1.5 (FIX-5, defect 7): `UcParams.incremental_energy_cost`. The UC energy cost of integer-cluster members drops the no-load heat already inside the average heat rate, `mc_uc = mc_base − nl/p̄ · max(mc_base − vom, 0)/hr`, so the UC pays no-load once. Window cost and the uplift basis switch to `mc_uc`. `UC_ENGINE_VERSION = "uc-1.5"` | `model/uc/params.py` (+44), `pipeline/uc.py` (+12/−4), `model/uc/uplift.py` (+14/−9) | **LIVE on both arms only** (UC stage, behind `unit_commitment_milp`). The docstring states "the P1 bid never reads this array", so P1 stays on the bid curve. Control: INERT |
| new ERCOT SCED band derive (UC-BANDS-ERCOT) | `scripts/data/derive_ercot_sced_uc_bands.py` (A) | **INERT for MISO**: an ERCOT derive script, not on any solve path, writes nothing MISO reads |
| bench harness | `scripts/lib/uc_bench.py` (+2/−1) | bench only |

The control is still the committed keeper bundle unchanged; no control solve. §§1–4 and Addendum 0 stand unchanged.

**Budget:** 180 / 720 min as staged. uc-1.5 changes the UC objective coefficients only, not problem size. Its wall effect on MISO is
unmeasured and is reported in W1.

**Launch:** 14 shards, `create_session` per prompt block in `shard-prompts-ucmilp3-miso.txt`; the record is in Addendum B.

## Addendum B (2026-10-14 12:50–12:53Z): launch record

14 span shards launched with `source_revision` `054dc883a91196241fc51e079f64f83d699d7ffa`, model `claude-opus-5-5`, tag
`ucmilp:UC-3-MISO-shard`. Prompts = the blocks of `shard-prompts-ucmilp3-miso.txt` at `6d9c946e`, verified byte-equal to the
per-arm template with only the year substituted (and the 2022 budget). Nothing in §§1–4, Addendum 0 or Addendum A changed.

| year | arm A session | arm B session |
|---|---|---|
| 2019 | `session_01NffxjDiykaVwDCiJASMV4S` | `session_01Qb14cBZTZFw3TNq2K9LY7M` |
| 2020 | `session_01KNg26QdV6t64NSSbseGR4P` | `session_01JmFA4vTzmH5GXhcLaPuZd7` |
| 2021 | `session_018HoWwzCggzv4xea6DcN6rg` | `session_01TAeVqruKCEzqwoVsUhQRGd` |
| 2022 (720 min) | `session_01FqUznJNGSCTBaLimof4aTy` | `session_01HJcHXuxo2BBAkdFBVVNPhJ` |
| 2023 | `session_01XzgyoMkssY8wk6ztaXGJxA` | `session_0139GK3UFPFRGZtpBCf5yHjh` |
| 2024 | `session_0186qYiVLZCXKRGwZWjUdEwP` | `session_01Qfnj51m1oMQy8fhoDcQbyc` |
| 2025 | `session_01VkBj79ngtF1A8L5FGeMwe1` | `session_01DLSUvARfKLj8hn51EGaHSx` |

## Addendum C (2026-10-14 13:45–13:49Z): arm B relaunched; the first arm-B launch never ran

- **What happened.** The 7 arm-B sessions of Addendum B never got a container. Each logged `Sandbox allocation failed`
  (`provision_error_category: rate_limited`) at 12:53Z: the second burst of 7 `create_session` calls within ~8 s, right after arm A's 7.
- **Fix.** Archived at sweep 1 (13:45Z; PENDING > 45 min, no work done, nothing lost) and relaunched **one at a time**. Each new
  session was confirmed provisioned (`Environment runner started`, clone started) before the next was created.
- **What did not change.** The prompts are byte-identical to Addendum B's blocks, with the same `source_revision` `054dc883…`.
- **Arm A** (Addendum B) is running: solves are detached, and the sessions read idle while their watchers wait.

| year | arm B session (relaunch) | superseded (archived, never provisioned) |
|---|---|---|
| 2019 | `session_01PXQdMsA29WdWANPkgn3s6P` | `session_01Qb14cBZTZFw3TNq2K9LY7M` |
| 2020 | `session_014ZGsdyeT2s9g3ER4Uxmpgj` | `session_01JmFA4vTzmH5GXhcLaPuZd7` |
| 2021 | `session_01YUeJxXe5hrnNiJjHUcGAvD` | `session_01TAeVqruKCEzqwoVsUhQRGd` |
| 2022 (720 min) | `session_014u3ehbZU6hEbJmNSAYczAp` | `session_01HJcHXuxo2BBAkdFBVVNPhJ` |
| 2023 | `session_019D8q1JxgA3H4t1H4ymN6Ja` | `session_0139GK3UFPFRGZtpBCf5yHjh` |
| 2024 | `session_01ENvx7D5KNbY2tnR2wBpmye` | `session_01Qfnj51m1oMQy8fhoDcQbyc` |
| 2025 | `session_01HufxCkRxSUxxHFgEZuY6wH` | `session_01DLSUvARfKLj8hn51EGaHSx` |

Arm B therefore starts ~55 min after arm A. Nothing in the arm definitions, readings or rules changes.

## Addendum D (2026-10-14 16:25Z, before any arm-B number is scored): three arm-B legs OOM-killed on under-provisioned containers; relaunched unchanged

- **What happened.** B2023 (`session_019D8q1JxgA3H4t1H4ymN6Ja`), B2024 (`session_01ENvx7D5KNbY2tnR2wBpmye`) and B2025
  (`session_01HufxCkRxSUxxHFgEZuY6wH`) were each killed by the memory cgroup (exit 137, `Memory cgroup out of memory … anon-rss ≈ 13.2 GiB`).
  The kill came after the UC stage finished:
  - B2023: 365/365 Optimal, 3,400.3 s.
  - B2024: 365/365 Optimal, 3,554.5 s.
  - B2025: 365/365 Optimal, 2,914.3 s.

  In every case it hit at the first step of P1 (`P1 route: COLD REBUILD on a floored fleet`). No bundle was written and nothing was pushed.
- **Cause: the container, not the recipe.** These three containers started with **10.6–10.8 GiB free disk**, so
  `prepare_solve_container.py` could add only **4 GiB of swap**: 13.36 + 4.0 = **17.4 GiB**, against the 24 GiB target, as their own
  preflight warned. Every leg that completed, all 7 arm A and B2019–B2022, started with 15.9 GiB free disk and got 9 GiB of swap
  (**22.4 GiB**); their peak was 16.7–17.6 GiB.
- **Not a kill under §3.** Kill #1 is an infeasible window or no incumbent; none occurred. UC-2 W5 says an OOM means STOP and report, and
  that a relaunch must never change a setting. These reports are the STOP record.
- **Relaunch:** byte-identical prompts, the same `source_revision` `054dc883…`, one at a time. No setting changes. A relaunch that again
  lands on a 17.4 GiB container is expected to OOM again; that is recorded as a coverage gap, not retried with any change.
- **Verified and archived arm-B legs (rule 33):**

| leg | branch @ sha | files |
|---|---|---|
| B2019 | `claude/ucmilp3-miso-b-2019` @ `94237f1a3010827ee476394bccc5dfe34678a3c9` | 21 |
| B2020 | `claude/ucmilp3-miso-b-2020` @ `c9265bcc822ec17025bfbb2b06de9b2b91f6095a` | 21 |
| B2021 | `claude/ucmilp3-miso-b-2021` @ `fc46730daf04cfdb7d0e350f2c345b1d9cd45960` | 21 |
| B2022 | `claude/ucmilp3-miso-b-2022` @ `d427c8ed24f56a8c7aed16a7d8d14e6690691fb5` | 23 (P1 split, sha256 verified) |

  The B-leg recipe gate passes: the differing-field set is exactly arm A's plus `st_gas_mustrun_per_plant = False`. Engine `uc-1.5`, 0
  non-optimal windows.

# Model Audit Program — Director Status Board (2026-08)

> # 🔴 **OWNER RULINGS R-AL … R-AO (2026-09-05 18:55Z SITTING)** — RECORDS-ONLY LANE **v29**, pin `5eb5f38a` → `db095953`. **THE GITHUB API IS BACK AT THIS LANE, AND THE FIRST THING IT SHOWS IS THAT THE FLIP IS *STILL NOT LIVE* 80 MINUTES AFTER "DOING IT NOW" — SO G2 IS NOT DECLARED HERE. IT ALSO SHOWS R-AH's 6-OF-6 CONDITION, MET AT 18:06Z, HAS SINCE BEEN *LOST AT HEAD*: `ruff format` IS RED AGAIN ON MAIN.**
>
> **Records only.** This lane records four owner rulings and **executes none of
> them**. No solve, no scoring, no registration, no keeper shard, no marker, no
> freeze file, no matrix shard, no workflow, no `program-status.json`. It
> adjudicates nothing, and **rewrites nothing in v27, v28 or v28b** — the queue
> movements and the corrections below are *dated amendments recorded here*, not
> edits to those entries.
>
> **Q-4 premise, verified at the pin before a byte was written** (word-boundary
> grep across `docs/`): `R-AL` **0 files**, `R-AM` **0**, `R-AN` **0**, `R-AO`
> **0**. Four rulings, given at **18:55Z**, existed **only in the dispatch** at
> 20:14Z. **That is the FOURTH CONSECUTIVE CYCLE** of the same defect — R-AF
> unrecorded until v26, R-AG until v27, R-AH…R-AK until v28b, R-AL…R-AO until
> here. The sweep also returns **≥1 artifact for every label R-A through R-AK**,
> so no earlier ruling has silently fallen off the record.
>
> ### 🟢 THE INSTRUMENT v28 AND v28b LOST IS **RESTORED** — AND EVERY FIGURE THEY HAD TO CARRY ON ATTESTATION IS NOW **READ**
>
> v28 and v28b both recorded the GitHub REST API as **HTTP 403** on every
> repository-scoped path, and both correctly declined to state a flip-set count,
> a run conclusion or a PR state. **At this lane the GitHub MCP tools answer.**
> The dispatch instructed this lane to carry the director's readings as his
> record if it hit the same 403; it did not hit it, so **the director's readings
> below are CONFIRMED BY THIS LANE'S OWN CALLS, not carried.** That is the
> single biggest change in this entry's evidentiary standing, and it is why the
> flip finding below is an *observation* rather than the inference v28 had to
> settle for.
>
> ### THE FOUR RULINGS, AS THE OWNER SELECTED THEM
>
> | ruling | decision card | option chosen (label as selected) | consequence |
> |---|---|---|---|
> | **R-AL** | **card F** — Y-1, the branch-protection flip | **"Doing it now"** | The owner performs the Settings action requiring the six R-AE checks on `main`. R-AH's condition had been met twice (runs 2456, 2463). |
> | **R-AM** | **card G** — G2 | **"Declare G2 once the flip is live"** | The records lane declares G2 in the same entry that reads `protected: true`; **DOCS-B** (plan §4.9) dispatches at that moment; the **FFR Q.2 battery** is notified per plan §2. |
> | **R-AN** | **card H** — the R-V freeze | **"Lift at G2 declaration"** | The keeper freeze on {ERCOT, NEISO, PJM} holds **until G2 is declared**, then lifts. Queue item 14's R-V line is amended as dated. |
> | **R-AO** | **card I** — the bench red | **"Charter an audit Y-8 bench-regen lane"** | Y-8 minted OPEN: re-render all 20 bench parts at builder `4e78c85427bb`, content-invariance per part, C1 re-derivation on NYISO artifact-only, **promote nothing**. |
>
> ### 🔴 R-AL / R-AM — **THE FLIP IS NOT LIVE, READ DIRECTLY. G2 IS NOT DECLARED BY THIS ENTRY.**
>
> `list_branches` at **20:12Z** and again at **20:16Z**: `main` →
> **`"protected": false`**. The owner said *"doing it now"* at **18:55Z**; the
> Settings action had **not** taken effect **80 minutes later**. This is a
> reading of the branch object itself, not v28's inference from local
> equivalents and not v28b's `UNREAD`.
>
> **A second, independent corroboration from the PR stream.** Since the ruling,
> PRs merge in **under a minute**: **#4802** created **20:10:16Z**, merged
> **20:11:15Z** — **59 seconds**; #4801 in **6 s**; #4800 in **31 s**. A CI run
> of the six required checks takes **~10 minutes** (`Fast test tier` alone is
> 8–10 min on both runs read below). **A 59-second merge is arithmetically
> impossible with the six checks required**, so the PR stream and the branches
> API agree.
>
> **Consequence, stated plainly: R-AM's condition is UNMET and this entry does
> NOT declare G2.** The declaration is the next records lane's, written when the
> desk reads `protected: true`. **DOCS-B and the FFR Q.2 battery both hang on
> that same moment** — and see the launch note below, because **DOCS-B has
> already been dispatched anyway**.
>
> ### 🔴 THE FINDING THE DISPATCH DID NOT ANTICIPATE — **R-AH's 6-OF-6 CONDITION HAS BEEN LOST AT HEAD, AND ONE OF THE SIX REQUIRED CHECKS IS RED RIGHT NOW**
>
> The dispatch's JOB 3 asserts *"ruff lint + format clean."* **It is not.** At
> this pin, run alone under `uv run --frozen`:
>
> * `ruff check .` → **exit 0**, *All checks passed!*
> * `ruff format --check .` → **🔴 exit 1**, *3 files would be reformatted, 1389 already formatted*:
>   `scripts/gen_miso217_attestation.py`, **`src/market_sim/data/offer_curves.py`**, `tests/unit/data/test_miso_intermediate_gas_offer_margin.py`.
>
> All three arrived with the **miso-217** landing (#4790 19:04Z → #4799 20:01:48Z
> → #4801 20:05:51Z), and one of them is **core `src/market_sim/`**.
>
> **Why this is the headline and not a nit.** `Ruff lint + format` is **one of
> the six R-AE flip-set checks** (`ci.yml:393`). R-AH's condition — *the Settings
> action fires on the first CI-covered head whose six-check set reads 6 of 6* —
> was met at **18:06:46Z** on head `dd555499`, and **Y-7 met it by fixing this
> very check** (v28's table, item 2: `ruff format --check .` → *1386 files already
> formatted*). **miso-217 has since re-opened it.** So if the owner performs the
> Settings action now, the required set on `main`'s HEAD is **5 of 6, not 6 of
> 6**, and the first PR to run against the new protection will be **blocked by a
> red required check**. This is Y-7's defect recurring **13 hours later**, and it
> is the second time this cycle that a merged lane has undone a flip-set repair.
> **Routed to the owner and the director as the one thing that should be fixed
> BEFORE the flip, not after.**
>
> ### 🟢 THE G2 ROLL-CALL AT THIS PIN — **LEGS 1 AND 2 VERIFIED BY THIS LANE; LEG 3 IS NOT CLEAN; LEG 4 IS NOT LIVE**
>
> | leg | dispatch's record | **this lane's reading at `db095953`** |
> |---|---|---|
> | **1 · PERF-B merged byte-green** | SATISFIED under R-AJ | 🟢 **CONFIRMED, first-hand.** `golden-data-tier.yml` run **#11**, id **`33983249186`**, event `workflow_dispatch`, ref `main`, head **`a0014864`**, `run_attempt` 1, started **18:10:58Z**, **`status: completed`, `conclusion: SUCCESS`**, updated **18:23:13Z**, triggering actor the owner. **v28b's `UNREAD` is discharged.** With the s3 byte gate (PASS at atol=rtol=0), leg 1 is **satisfied on R-AJ's own terms**. |
> | **2 · one completed fast-tier-green ci.yml run** | SATISFIED (runs 2456, 2463) | 🟢 **CONFIRMED at the JOB level, both runs.** See the table below — all six R-AE checks `success` on each, and exactly the two chronic non-set jobs red. |
> | **3 · keeper freeze (R-V)** | SATISFIED | 🟠 **NOT CLEAN — see the keeper-motion section.** All three of {ERCOT, NEISO, PJM} are **byte-touched** since 02:08Z, and **ERCOT's `keeper` field itself changed**. |
> | **4 · branch-protection flip** | NOT LIVE at 18:55Z; owner "doing it now" | 🔴 **STILL NOT LIVE at 20:16Z**, read directly (`protected: false`). **G2 not declared.** |
>
> **Leg 2, job-level, both runs — this is the reading v27/v28/v28b could never take:**
>
> | R-AE required check (`ci.yml`) | run **2456** `33979949551` head `dd555499` | run **2463** `33984897199` head `77a6dafa` |
> |---|---|---|
> | `Ruff lint + format` | 🟢 success | 🟢 success |
> | `Pinned default cache key` | 🟢 success | 🟢 success |
> | `Structural refactor guards` | 🟢 success | 🟢 success |
> | `Cache-key registration guard` | 🟢 success | 🟢 success |
> | `Fast test tier` | 🟢 success | 🟢 success |
> | `Rule-22 quarantine gates` | 🟢 success | 🟢 success |
> | *(non-set)* `Forecast-invariant artifact audit` | 🔴 failure | 🔴 failure |
> | *(non-set)* `FR-22 backcast→forecast parity` | 🔴 failure | 🔴 failure |
> | *(non-set)* `FR-21 staleness (WARN only)` | 🟢 success | 🟢 success |
> | *(non-set)* `Rule-28 mechanism-matrix guard` | 🟢 success | 🟢 success |
> | **overall `conclusion`** | **`failure`** | **`failure`** |
>
> **Both runs are 10 jobs, 8 green, 2 red, overall `failure` — and the two reds
> are outside the required set.** The director's job-level readings are exact.
> **Z-2, stated once more with the evidence in hand:** the overall `conclusion`
> of a `ci.yml` run is **structurally incapable** of showing the flip set green,
> because two permanently-red non-set jobs sit in the same workflow. Anyone
> reading run conclusions alone will read `failure` forever.
>
> ### 🔴 THE SEVEN GATES — **TWO EXIT 1, NOT ONE; AND SIX OF THE SEVEN FIGURES THE DISPATCH GAVE ARE SUPERSEDED**
>
> Each script invoked alone under `uv run --frozen` after `uv sync --frozen`,
> `$?` read immediately, never through a pipe:
>
> | gate script | exit | reading at this pin | vs the dispatch |
> |---|---|---|---|
> | `audit_keepers.py --check` | 🟢 0 | **PASS — 0 failures, 1 warning** | dispatch/v28 said 0 warnings — **superseded** |
> | `check_registry_payload_parity.py` | 🟢 0 | **8 runs checked, 58 bundle dirs swept**, 0 known-unsynced | dispatch said **66 / 108** — **superseded**, cause below |
> | `check_gate_a_provenance.py` | 🔴 **1** | **MISO row cites SUPERSEDED keeper** `2026-09-05-miso-213-layering`; live keeper is `2026-09-05-miso-217-intermphys` | dispatch said **"gate-(a) 6 rows OK"**, exit 0 — **a red the dispatch did not have** |
> | `check_mechanism_matrix.py` | 🟢 0 | **195 field + 49 row + 164 path** anchors, 6 shards, keeper stamps + §5.x headers match | ✅ **matches to the digit** |
> | `check_forecast_staleness.py` | 🟢 0 | **Δ = UNKNOWN** — newest scored sha `c5019afaf3f3` **not reachable in this checkout**; **25 of 99** verdicts undated; 65 config cache epochs | dispatch said **Δ = 11 (WARN limb fired), 25 of 97** — **superseded on both** |
> | `check_bench_freshness.py` | 🔴 **1** | **20 parts, 14 STALE, 0 engine-drift** | dispatch said **20 of 20 STALE** — **superseded**, six parts have been refreshed |
> | `check_golden_manifest.py` | 🟢 0 | 47 manifests, 88 entries (24 enforced / 64 legacy), **15 with a pruned provenance run, 15 stale vs the live keeper** | dispatch said **3 stale** — **superseded**, cause below |
>
> **🔴 GATE-(a) IS RED, AND IT IS AN R-T ROUTING MISS — THE FIRST ONE.** R-T's
> routing half (J-2) exists precisely so that *the promoting PR carries the
> gate-(a) re-key*, making a fourth micro-supersession unnecessary. **Two
> keeper-moving PRs landed this window and they split on it:** ercot-248
> **honoured** it (its commit message names *"forecast program-status gate-(a)
> stamp (R-T)"*, and `gate.a_keeper_marker` for ERCOT reads
> `2026-09-05-ercot248-two-config-keeper` with the re-key recorded in-row), while
> **miso-217 did not** — it moved `keepers/MISO.json` at 19:48:38Z and left
> `program-status.json`'s MISO row on `miso-213`. Note that MISO's row is
> `status: "fail"` either way (MISO is absent from `complete`), so **the
> three-instrument membership is unaffected**; the guard compares **identity
> only**. **R-T's mechanism is sound and was followed once and missed once in the
> same hour** — recorded as the routing rule's first measured miss, not as a
> reason to reopen the micro-supersession question.
>
> **🟠 WHY PARITY AND THE GOLDEN MANIFEST MOVED SO FAR — A KEEPER-ONLY PRUNE, ON
> AN OWNER DIRECTIVE.** `4b7a515e` (19:02:03Z, #4791) carries, verbatim in
> `keepers/*.json`'s `site_retention_note`: **"prune all the other non keeper
> runs from there so just show the keeper for each ISO for now"** (owner
> directive, session ercot-248). **61 non-keeper runs** were pruned across all
> six ISOs (ERCOT 15, CAISO 11, PJM 4, MISO 14, NYISO 14, NEISO 3), sidecar +
> payload + bundle together. That is the whole of the **66 → 8 runs / 108 → 58
> bundle dirs** parity move and the **3 → 15 stale golden-manifest entries**
> (their provenance runs are now pruned). **Neither is a defect**: the parity
> gate exits 0, and the golden gate's own note says a pruned provenance run *"is
> NOT a failure — top-15 retention is correct policy… survivable only because
> each entry carries its own `keeper_snapshot`"*. Recorded because a reader
> comparing this entry's figures to v28's would otherwise read a catastrophe.
>
> **🟠 THE BENCH RED — CAUSE CONFIRMED, COUNT CORRECTED, AND IT IS STILL NOT A CI
> JOB.** Builder fingerprint moved **`dbea7bf45111` → `4e78c85427bb`**. Cause
> confirmed at the source: `dee6472c` (nyiso-192) edits
> `scripts/render_calibration_html.py` (**21 lines**), which is member 1 of
> `BUILDER_SOURCES` in `scripts/lib/bench_stamp.py:45-50` — so every part built
> before it is stale by construction. **But the count is 14, not 20**: the six
> **MISO** and **NYISO** parts have since been re-rendered at the new fingerprint
> by their own lanes (nyiso-192's `d5bba63b`, *"Bench parts change only in
> builderFingerprint"*; miso-217's re-registration `ad562664`). **STALE: CAISO
> 2023-25, ERCOT 2023-25, NEISO 2022-25, PJM 2022-25.** **Y-8 has NOT landed** —
> no `claude/y8-*` branch exists on `origin` at any of this lane's three polls.
> **Z-2 EXTENDED IN A NEW DIRECTION, and this is the sharpest instance yet:**
> `grep -n "check_bench_freshness" .github/workflows/*.yml` returns **nothing**.
> The gate is in **no** workflow. `ci.yml` has exactly **ten** `name:` keys and
> this is not one of them. So the seven-script roster and the ten-job roster
> diverge **on a script that is exit-1 right now** — a real red that **no CI
> conclusion, green or red, can ever show**. Z-2 previously said CI's conclusion
> understates health; here it *overstates* it.
>
> **The three test suites the dispatch named: 41 passed, 1 FAILED — not 42
> passed.** `tests/regression/test_constants_facade.py` +
> `tests/scoring/test_gate_a_provenance.py` + `tests/curation/test_clean_io.py`
> → **`test_live_board_passes` FAILS** on the same MISO staleness above. The
> dispatch's "42 passed" counted the collection, not the result. *(Note also
> that the dispatch's paths were wrong — the files are under `tests/scoring/`
> and `tests/curation/`, not `tests/unit/`.)*
>
> ### 🔴 KEEPER MOTION — **THE DISPATCH SAYS "NO MOTION SINCE 02:08Z". TWO KEEPERS MOVED, ONE OF THEM INSIDE R-V's FROZEN SET.**
>
> JOB 4 asserts *"Keepers: NO motion since 02:08Z (verify from `git log --
> frontend/data/backcast/keepers`)"* and predicts the D56-R2 edit touched the
> frontier block only. **The first half is refuted by the command the dispatch
> itself names; the second half is correct.** `git log --no-merges
> --since=2026-09-05T02:08:01Z -- frontend/data/backcast/keepers` returns
> **THREE** commits:
>
> | commit | UTC | shards | did the **`keeper` field** move? |
> |---|---|---|---|
> | `8645c08e` capx D56-R2, NYISO frontier (Q39) | 18:32:10Z | NYISO (+12/−1) | 🟢 **NO** — frontier block only. **Dispatch correct.** |
> | `4b7a515e` ercot-248 + keeper-only prune | **19:02:03Z** | **all six** | 🔴 **YES, ERCOT**: `2026-08-25-234-eastex-identity` → `2026-09-05-ercot248-two-config-keeper` |
> | `7d585522` miso-217 PROMOTED | **19:48:38Z** | MISO | 🔴 **YES, MISO**: `2026-09-05-miso-213-layering` → `2026-09-05-miso-217-intermphys` |
>
> **What this does to R-V, stated as measurement and NOT adjudicated here.**
> R-V's text (J-4) is *"**No promotion** in those three lanes until PERF-B's
> byte-green loop completes or the owner lifts it"* — the stated test is
> **promotion**. Every records lane since has *measured* it with a stricter
> proxy — *"{ERCOT, NEISO, PJM} byte-untouched / byte-identical"* (v20 leg-3,
> v24, v25, v26, v28b). **At this pin the proxy is broken for all three**: NEISO
> and PJM took the `site_retention_note` line, and **ERCOT's `keeper` field
> itself changed.** Whether that is a *promotion* is exactly the question this
> desk does not answer, so here is the evidence for whoever does:
>
> * It is a **zero-solve identity re-key**, not a new calibration. The bundle
>   `results/calibration/ercot248_two_config_keeper/` carries a
>   **`composite_provenance.json`** (verified present on disk), and the commit
>   states *"every per-year artifact copied byte-for-byte, zero solve"* — 2023
>   from `…-236-swcap-clip-k33`, 2024/2025 from `…-234-eastex-identity`, i.e.
>   **the two configs ERCOT's keeper already designated** under the owner's
>   2026-08-26 `config_partition` ruling. Former ids are preserved in
>   `source_run_id`.
> * It was performed under an **explicit owner directive of 2026-09-05**, quoted
>   verbatim in the shard.
> * Its rule-22 D-5(b) duty **was** discharged: `calibration-complete.json`'s
>   ERCOT entry is re-keyed to `ercot248` with a re-verification, and
>   `audit_keepers.py --check` passes.
>
> **So: no keeper in the frozen set acquired new numbers, but ERCOT's designated
> id is not the id R-V was declared over.** Recorded for the owner as a live
> question — **and R-AN largely moots it**, since the freeze lifts at the G2
> declaration in any case. **MISO's promotion is unambiguously fine**: {MISO,
> CAISO, NYISO} are the three R-V **explicitly unfroze**.
>
> **🟠 R-AI's CLOCKS ARE BROKEN — TWO OF THE THREE.** v28b recorded all three
> intact at 02:08Z + 48 h. **MISO's keeper moved at 19:48:38Z**, so MISO's
> `2026-09-07 01:21Z` clock is **reset, not intact**. NYISO (`01:03Z`) and CAISO
> (`02:08Z`) **stand** — neither shard's `keeper` field moved. Since R-AI's
> instruction is *"re-capture the three stale goldens ONLY IF the keepers stay
> still through R-AF's 48-hour limb"*, **the hold is now conditional on two
> clocks, not three, and MISO's stale golden (`…-miso-198-oomlevel`) has
> re-targeted again** — it was stale against `miso-213`, it is now stale against
> `miso-217`. **No capture was dispatched by this lane** — that remains the
> ruling, executed by not acting. Stage-0 stays **4 of 7**.
>
> ### 🟢 JOB 4 — FOUR-WAY ALIGNMENT **CONFIRMED**, ON ALL FOUR INSTRUMENTS
>
> Director ruling (f) stands: the test is **three** instruments, with `frontier`
> reported beside them and never required to agree. At this pin they agree
> anyway:
>
> | instrument | membership at `db095953` | source, re-derived here |
> |---|---|---|
> | `complete` marker | **{ERCOT, NEISO, PJM, NYISO}** | `calibration-complete.json` |
> | gate-(a) `status: pass` | **{ERCOT, NEISO, PJM, NYISO}** | `program-status.json` (MISO/CAISO `fail`, absent from `complete`) |
> | ISO-level determination | **{ERCOT, NEISO, PJM, NYISO}** = CALIBRATED | `status/<ISO>.js` (MISO, CAISO `NOT-YET`) |
> | *(reported beside)* `frontier` | **{ERCOT 08-31, NEISO 07-11, PJM 07-31, NYISO 09-05}** | `keepers/<ISO>.json`; MISO and CAISO carry none |
>
> **NYISO's `frontier` was re-declared 2026-09-05 on `nyiso-189` by the capx
> desk's D56-R2 lane (#4780, owner ruling Q39) — that desk's act, cited as its
> record.** This is the **first full four-way alignment since 2026-08-30**, and
> the dispatch's claim is confirmed in every particular. **Markers:** `final`
> holds only `_note` — **no locked-test year has ever been solved, scored or
> registered for any ISO**. `holdout-freeze.json` **active**, `scope.tiers =
> ["locked_test"]`, so the validation tier is unfrozen. **Both confirmed
> unchanged.**
>
> ### 🔴 JOB 5 — DISPATCH-VS-LAUNCH: **G-14 GAINS TWO INSTANCES, INCLUDING A *NEW CLASS*; AND THIS LANE IS ITSELF THE SECOND ISSUE OF v29**
>
> The dispatch states *"Y-8 and this lane launched 19:00Z"* and *"G-14: the
> 'died-before-first-push' class gained no instance this cycle."* **The roster
> refutes both.** Read from the session roster (the director ran `list_sessions`;
> this lane re-ran it and reports what the roster says):
>
> | lane | issue | created | outcome |
> |---|---|---|---|
> | **audit records v29** | **1st** | **19:16:14Z** | 🔴 **ARCHIVED 19:18:25Z — *"repo … not cloned; cannot audit"*, needing *"add_repo access or relaunch with repo pre-cloned"*.** Opus. **A NEW FAILURE CLASS.** |
> | **audit records v29** | **2nd** | **20:07:41Z** | 🟢 **this lane** — launched with the checkout, working |
> | **Y-8 bench regen** | **1st** | **19:15:31Z** | 🟠 **completed 19:26:54Z but pushed NOTHING** — *"17/20 stale, 5 unreachable, C1 verdict stable… awaiting desk decision on re-charter and 2022 stale handling"* |
> | **Y-8 bench regen** | **2nd** | **20:07:29Z** | 🟢 running |
> | **DOCS-B finalization** | 1st | **20:08:36Z** | 🟢 running — **see below** |
> | **audit records v30 "G2 declaration"** | 1st | **20:08:27Z** | 🟠 running, **BLOCKED on a `list_sessions` permission prompt** |
>
> **THE NEW CLASS, named because it is neither of G-14's two.** v29's first
> session **launched** (so it is not a launch death) and **reached its dispatch**
> (so it is not the v28b permission stall) — **it had no repository**. It could
> not have pushed anything, because it had nothing to read. Call it
> **"launched-without-checkout"**; it is **G-14's third class** and its first
> instance. **The dispatch's own G-14 line is therefore wrong on the evidence it
> was written from**, which is the Refresh-protocol failure mode exactly: *a
> dispatch written at pin P describes a world that no longer exists at P+1*.
> **Neither Y-8 nor this lane launched at 19:00Z**; both launched at ~19:15Z,
> **both failed**, and **both were re-issued at ~20:07Z**. R-AK's routing (Opus
> for records/capture/small-repair) was honoured on every one of them — **all
> four sessions are Opus** — so **this failure class is not the Fable launch
> death R-AK was written for**, and R-AK does not address it.
>
> **🔴 DOCS-B HAS BEEN DISPATCHED AHEAD OF ITS R-AM CONDITION.** R-AM says DOCS-B
> dispatches *at the moment G2 is declared*. **G2 is not declared** (the flip is
> not live), yet **`DOCS-B finalization` is running since 20:08:36Z**. Recorded
> as an observation, not a complaint — plan §4.9 holds DOCS-B until G2, and the
> desk should either declare G2 (it cannot yet) or note the dispatch as
> deliberately early. **The same applies to the `audit records v30 "G2
> declaration"` lane**, which is named for a declaration whose precondition this
> lane reads as unmet, and which is **blocked on a permission prompt** as of
> 20:13Z.
>
> **v28 and v28b, both LANDED, and their own records corroborate the dispatch.**
> **v28 → #4776**: its session closes *"PR blocked by API 403; body drafted in
> file… investigate GitHub API 403 on PR creation"* — so the branch was pushed
> and **the PR was opened by another route**, exactly as the dispatch says.
> **v28b → #4782**: *"audit pushed & merged (PR #4782); records sha256-match
> main"*; its **first** issue (18:11:21Z) archived at **18:17:30Z** asking *"grant
> the git permissions and a PR route"* — the **6-minute permission stall**, a
> distinct class, as v28b itself recorded. **Y-7 → #4771**, *"merged to main;
> session work complete"*. **All three confirmed.**
>
> **🟢 A NOTE ON R-AK's BASIS, WHICH v28b COULD NOT VERIFY.** v28b recorded,
> correctly, that *"session launch outcomes leave no artifact in the tree"* and
> declined to verify the four Fable launch deaths. **The roster is such an
> artifact, and it corroborates two of the four directly:** two sessions titled
> *"Audit records lane v28"*, model **`claude-fable-5-1`**, created **03:59:14Z**
> and **04:02:13Z**, both `SESSION_STATUS_BUCKET_FAILED` with the identical
> diagnostic `[ede_diagnostic] result_type=user last_content_type=n/a
> stop_reason=tool_use`. **R-AK's basis is no longer attestation-only.**
>
> **The capx desk's acts, recorded only where they move this board's surfaces**
> (that desk's record, cited as such, never routed to here): **D56-R2** re-declared
> NYISO `frontier` (#4780 — the marker); **ercot-248** re-keyed the ERCOT keeper +
> ran the owner's prune (#4791 — the parity/golden/gate-(a) figures above);
> **miso-217** promoted MISO (#4790/#4799/#4801 — the gate-(a) red and the
> `ruff format` red); **D57** is **CLOSED, not open** — the dispatch lists
> *"#4761, #4775, #4786 open"*, but **#4786 merged at 19:05:28Z**; **D59/D60**
> touch nothing measured here.
>
> ### QUEUE AMENDMENTS — 2026-09-05, THIS LANE (dated; **v27, v28 and v28b are not rewritten**)
>
> | queue item | amendment |
> |---|---|
> | **Y-1** | **R-AL recorded** — the owner is performing the Settings action ("doing it now", 18:55Z). 🔴 **STILL NOT LIVE at 20:16Z**, read directly: `main` → `protected: false`, corroborated by 59-second merges. **AND R-AH's 6-of-6 condition is LOST at HEAD** — `Ruff lint + format` is red on `main` (3 files, one of them `src/market_sim/data/offer_curves.py`), so the required set reads **5 of 6** right now. **Fix before the flip, not after.** |
> | **Y-2** | **R-AM recorded.** G2 sitting HELD 18:55Z; the declaration is **conditional on `protected: true`** and is **NOT made here**. It belongs to the next records lane that reads the flip live. DOCS-B + the FFR Q.2 battery ride on that same moment — **note DOCS-B is already running (20:08:36Z), ahead of the condition**. |
> | **R-V** *(item 14)* | **R-AN recorded: the freeze LIFTS AT THE G2 DECLARATION**, and holds until then. 🟠 Its byte-proxy is **broken at this pin**: all three of {ERCOT, NEISO, PJM} are touched and **ERCOT's `keeper` id changed** (zero-solve re-key, owner-directed). R-V's stated test is *promotion*; whether a zero-solve identity re-key is one is **the owner's/director's call, not this desk's** — and R-AN largely moots it. |
> | **X-2** | **R-AI's hold stands, but on TWO clocks, not three.** MISO's keeper moved 19:48:38Z → its `2026-09-07 01:21Z` clock is **reset**; NYISO `01:03Z` and CAISO `02:08Z` **intact**. Stage-0 **4 of 7**; MISO's stale golden re-targets `198 → 217`. **No capture dispatched.** |
> | **Y-8** *(NEW)* | **R-AO recorded — MINTED OPEN.** Charter: re-render all **20** bench parts at builder **`4e78c85427bb`**, content-invariance per part, C1 re-derivation on NYISO **artifact-only**, **promote nothing**. **Not landed** (no branch on `origin` at three polls). Its **first issue completed without pushing**, reporting *17/20 stale, 5 unreachable* and asking for a **re-charter decision on the 2022 parts**; a **second issue is running**. **This lane measures 14/20 stale** — six parts refreshed since. |
> | **Z-2** | **EXTENDED, in a new direction.** `check_bench_freshness.py` is **in no workflow at all** — `ci.yml` has ten `name:` keys and this is not one. A **real exit-1 red** that no CI conclusion can show. Previously Z-2 said the conclusion *understates* health (two chronic non-set reds); here it **overstates** it. |
> | **Z-3** | **APPLIED — SEVENTH CONSECUTIVE INSTANCE.** Director pinned `5d6e9cfb` (18:53Z); this lane read **`5eb5f38a`** at poll 1 (20:08Z) — **44 commits / 14 merges (#4788–#4801)** later — and **`db095953`** at polls 2 and 3 (20:13Z, 20:16Z). The last hop is **#4802, docs-only** (`PREDECL-capx-d60`, +94 lines), touching **no** surface measured here, so **every figure holds at both**. |
> | **G-14** | **TWO instances, one of them a NEW CLASS.** *launched-without-checkout* (v29 issue 1, 19:16Z) joins *launch death* and *permission stall*. **Y-8 issue 1 pushed nothing** and asked for a re-charter. **All four sessions were Opus**, so R-AK's routing was honoured and does **not** address this class. |
> | **X-3 / X-4 / X-5 / X-6b / Y-3 / Q-4** | **UNCHANGED.** X-3 discharged (v28b). X-6b's **undated half stands and is now 25 of 99** (was 25 of 97) — and its **first leg has REGRESSED**: v28 discharged it on `921bb4cd` being reachable, but the newest scored sha is now **`c5019afaf3f3`, NOT reachable in this checkout**, so the staleness Δ is **UNKNOWN**, not 11. Y-3 (R-T 9/6) unchanged **except** for the first measured routing miss above. |
>
> ### Q-4 AT CLOSE
>
> **(i) Label sweep, word-boundary grep across `docs/` after writing.**
> `R-AL` **2** files · `R-AM` **2** · `R-AN` **2** · `R-AO` **2** — **exactly the
> two files this lane touched**, for all four, as the dispatch predicted; no
> third file, no leak outside the two canonical records. Every label **R-A
> through R-AK returns ≥ 1** (`R-A` 98 … `R-AK` 5), so **no earlier ruling has
> fallen off the record**. Also swept: `Q39` **12** · `D56-R2` **5** · `Z-5`
> **2** · `Y-7` **6** · `R-AE` **5** · **`Y-8` 0 → 2** (minted here).
>
> **(ii) Job-vs-changed-file diff.**
>
> | job | changed target file at close |
> |---|---|
> | 1 · G2 roll-call, four legs | board — roll-call table + leg-2 job matrix; **leg 4 read `protected: false`**; **G2 NOT declared** ✅ |
> | 2 · record R-AL…R-AO verbatim | board — rulings table + four sections; plan §8 ✅ |
> | 3 · seven-gate ledger | board — gate table; **2 exit-1 (bench + gate-(a))**, six figures superseded ✅ |
> | 4 · alignment + markers | board — four-instrument table; **keeper-motion correction (2 keepers moved)** ✅ |
> | 5 · dispatch-vs-launch | board — roster table + **G-14's third class** ✅ |
> | 6 · queue v29 + plan §8 | board — queue amendments; plan §8 entry ✅ |
> | 7 · Q-4 close-out | this section ✅ |
>
> **(iii) Run lists.** **READ, not UNREAD** — the API answers at this lane.
> `ci.yml`: **2,474 runs**; the 12 most recent (2467–2478) all conclude
> **`failure`**, every one on the two chronic non-set jobs (2456 and 2463 read
> job-level above). `golden-data-tier.yml`: run **#11** `33983249186` →
> **`success`**.
>
> **Records integrity.** Clean tree at session start and again after
> `git reset --hard origin/main` at `db095953` (`git status --porcelain`
> **empty**); **closing diff confined to these two files** — this board and the
> plan — **insertions only, zero deletions**. **Verified untouched:** every
> keeper shard, every `status/<ISO>.js`, `calibration-complete.json`,
> `holdout-freeze.json`, **`program-status.json`**, every matrix shard, every
> workflow, every bundle / sidecar / registry file, every golden manifest. **No
> solve, no scoring, no registration, no keeper shard, no marker, no freeze file,
> no matrix shard, no workflow dispatch.** CI runs on this lane's PR — both files
> sit in `ci.yml`'s Y-4-widened path filter. **Expect overall `failure`** on the
> two chronic non-set jobs, and **`Ruff lint + format` red** on the three
> miso-217 files, which this lane did not create and does not fix (records-only
> scope). **The flip was NOT live when this PR was opened** — recorded because
> the dispatch asked.

> # ⚖️ **OWNER RULINGS R-AH … R-AK (2026-09-05 15:32Z SITTING)** — RECORDS-ONLY LANE **v28b**, pin `59d85ecc`. **FOUR RULINGS THAT REACHED NO ARTIFACT UNTIL THIS BLOCK — AND v28, WRITING THE ENTRY DIRECTLY BELOW THIS ONE, RECORDED R-AH AS *"none issued. Nothing minted."* — ITS PR MERGED THREE HOURS AFTER THE RULING WAS GIVEN.**
>
> **Records only.** This lane records four owner rulings and **executes none of
> them**. No solve, no scoring, no registration, no keeper shard, no marker, no
> matrix shard, no workflow dispatch, no `program-status.json`. It adjudicates
> nothing, and **rewrites nothing in v27 or v28** — the queue movements and the
> one correction below are *dated amendments recorded here*, not edits to those
> entries.
>
> **Q-4 premise, verified at the pin before a byte was written** (word-boundary
> grep across `docs/`): `R-AH` **0 files**, `R-AI` **0**, `R-AJ` **0**, `R-AK`
> **0** — measured at `ee7754c1`, the dispatch's pin, before v28 landed. Four
> rulings, given at **15:32Z**, existed **only in the dispatch** three hours
> later. This block and the plan §8 entry are their first artifacts. That is
> **three consecutive cycles** of the same defect — R-AF unrecorded until v26,
> R-AG until v27, R-AH…R-AK until here — and the failure is upstream of the
> records lanes, not in them.
>
> **THE PIN MOVED UNDER THIS DISPATCH, AGAIN (Z-3's shape, sixth instance).**
> The director pinned `origin/main` at **`ee7754c1`**; the clone read
> **`8342d74d`** at poll 1 (18:32Z) and **`59d85ecc`** at poll 2 (18:37Z) —
> three merges later (**#4776**, **#4777**, **#4778**, 18:36:20Z–18:37:12Z).
> Every figure below is re-derived at the landed pin; where it differs from the
> dispatch's record, the difference is stated and **the owner's record governs**.
> *(Rebase note: the branch is rebased onto **`139a0988`** — #4779, miso-216,
> 18:41:49Z — which touches neither records file nor any surface measured here;
> every figure is derived at `59d85ecc` and re-checked as unchanged there.)*
>
> ### THE FOUR RULINGS, AS THE OWNER SELECTED THEM
>
> | ruling | decision card | option chosen (label as selected) | consequence |
> |---|---|---|---|
> | **R-AH** | **card A** — Y-1, the branch-protection flip | **"On first 6-of-6 head"** | The Settings action is performed on the **first CI-covered head whose R-AE six-check set reads 6 of 6**. The trigger is a condition, not a date. |
> | **R-AI** | **card C** — X-2, the stage-0 re-captures | **"Hold until the 09-07 clocks"** | **No capture dispatch.** The three stale goldens are re-captured **only if** the keepers stay still through R-AF's 48-hour limb. |
> | **R-AJ** | **card D** — G2 leg 1 + R-V | **"Golden-tier CI proof, then declare"** | **One** `workflow_dispatch` of `golden-data-tier.yml` on the merged PERF-B s3 head is the CI proof; **if green, leg 1 is declared satisfied** and the **R-V keeper-freeze question is served at the next sitting**. |
> | **R-AK** | **card E** — launch-failure routing | **"Opus for eligible lanes"** | Until the failure class clears, **records, capture and small repair lanes are assigned to Opus**; **Fable stays** for adjudication-class lanes and core-infrastructure scope under rule 27, **re-issued on failure**. |
>
> **WHO EXECUTED WHAT — the whole of it.** The **director** triggered the R-AJ
> golden-tier dispatch (run #11, below). The **Y-7 lane**
> (`claude/y7-flipset-closer-a1`, merged **#4771** at **18:06:46Z**) cleared the
> flip set that satisfies R-AH's condition. **Nothing else has been executed:**
> no capture was dispatched — that *is* R-AI's instruction — no Settings flip is
> visible to any instrument this lane can reach, and R-AK is a routing rule with
> no artifact to produce. **This lane executed nothing at all**; it wrote two
> records files.
>
> ### 🔴 A DATED CORRECTION TO v28's Q-4 SWEEP — **R-AH WAS ISSUED, AND v28 RECORDED THE OPPOSITE**
>
> The v28 entry immediately below reads, in its ruling-label sweep: ***"`R-AH` →
> 0 files. Confirmed: none issued. Nothing minted."*** **The count was right and
> the conclusion is wrong.** R-AH was given at the **15:32Z** sitting — before
> v28's own dispatch pin (`182aa74a`, 15:27:57Z / derivation 15:32Z) reached the
> lane — and v28's PR merged at **18:36:20Z (#4776)**, three hours and four minutes
> after the ruling existed. **A zero grep is evidence that nothing was *recorded*,
> never that nothing was *issued*.** v28's text stands untouched and its sweep
> method is sound; this is a dated correction to the inference it drew from it,
> in the D-9 form. **The same shape has now produced a wrong record three cycles
> running** (R-AF, R-AG, and here), and this instance is the sharpest yet: a
> records lane certified the absence of a ruling that a *parallel records lane*
> was already dispatched to write.
>
> ### 🟠 R-AH — THE CONDITION **HAS BEEN MET**; WHETHER THE FLIP IS **LIVE** IS **UNREAD HERE**, AND THE REASON IS AN ACCESS LIMIT, NOT AN OBSERVATION
>
> **Condition met, per the owner's record.** CI run **2456**
> (`33979949551`), head **`dd555499`** — the Y-7 lane's PR head, merged as
> **#4771** at **18:06:46Z** — reads **all six green**: `Ruff lint + format` ·
> `Pinned default cache key` · `Structural refactor guards` · `Cache-key
> registration guard` · `Fast test tier` · `Rule-22 quarantine gates`, with only
> the **two chronic non-set jobs red** (`FR-22 backcast->forecast parity`,
> `Forecast-invariant artifact audit`). **The flip is therefore now the owner's
> Settings action, due on that head.** This is the first 6-of-6 reading the
> program has recorded; v27 read 3 of 6, its coda projected 4 of 6, and v28
> could not read the set at all.
>
> **What this lane could and could not check.** From the checkout: `dd555499`
> is on `main` via `d71fdfe6` (#4771, 18:06:46Z) — the head is real and merged;
> the six names above are **exactly** the six `name:` keys in
> `.github/workflows/ci.yml` (`Rule-22 quarantine gates` :104, `Cache-key
> registration guard` :299, `Pinned default cache key` :345, `Ruff lint +
> format` :393, `Fast test tier` :416, `Structural refactor guards` :541), and
> the two named non-set jobs are the file's `Forecast-invariant artifact audit`
> (:151) and `FR-22 backcast->forecast parity` (:246). **The per-job results
> themselves are the owner's record and were NOT re-read here.**
>
> **🔴 LIVENESS: NOT ESTABLISHED BY THIS LANE — AND THE INSTRUMENT IS
> UNAVAILABLE, NOT SILENT.** Branch protection is a Settings-side object
> asserted **nowhere in the tree**, so no checkout can answer this; the route
> that could — the GitHub REST API — **returns 403 to this session on every
> repository-scoped path**: `{"message":"GitHub access is not enabled for this
> session. An org admin must connect the Claude GitHub App for this
> organization."}` (`/repos/…`, `/repos/…/pulls`, `/repos/…/actions/runs`,
> `/repos/…/branches/main` — all 403; `/user` and `/rate_limit` answer, so it is
> a **scope denial, not an outage**). Git smart-HTTP is unaffected. **This is
> the same 403 v28 recorded one entry below — independently reproduced at a
> second lane, two hours later, so the lost instrument is a standing condition
> and not one session's accident.**
>
> **What is observable from git alone, stated as observation and nothing more:**
> **#4771 itself and nine further pull requests** merged into `main` in the
> **30 minutes** after the 6-of-6 head — #4770 18:07:03Z · #4772 18:07:19Z ·
> #4773 18:15:19Z · #4774 18:21:01Z · #4761 18:21:31Z · #4775 18:29:03Z · #4776
> 18:36:20Z · #4777 18:36:51Z · #4778 18:37:12Z. **This is evidence in neither
> direction**, and the disproof the dispatch named does not discriminate either:
> a merge past a **red non-set job** cannot show the flip is off, because the
> non-set jobs are **outside** the required set and would not block a merge with
> the flip live. The in-session form of that test — this lane's own records PR
> merging — is unavailable, since this lane cannot merge it. **v28 records the
> flip as NOT live** on tree-level grounds (its local six-of-six equivalents had
> fallen back to four of six at `ee7754c1` while PRs kept merging); **this lane
> neither confirms nor contradicts that** — it is an inference from local
> equivalents, not a reading of the required checks. **At this pin the flip's
> liveness is UNREAD.**
>
> ### 🟢 R-AI — VERIFIED IN FULL FROM THE KEEPER LOG: **NO KEEPER HAS MOVED**, AND ALL THREE CLOCKS STAND
>
> **Hold confirmed on the evidence, not on assertion.** Per-shard last content
> commit on `main` (`git log --no-merges -1 -- frontend/data/backcast/keepers/<ISO>.json`):
>
> | ISO | last keeper-moving commit | UTC | clock (R-AF, +48 h) |
> |---|---|---|---|
> | NYISO | `e69fcd54` *nyiso-189: PROMOTE 2026-09-05-nyiso-189-steam-identity* | **01:03:41Z** | **2026-09-07 01:03Z** |
> | MISO | `3a6e90b6` *miso 213 layering — KEEPER 2026-09-05-miso-213-layering* | **01:21:15Z** | **2026-09-07 01:21Z** |
> | CAISO | `84e4ccb0` *Promote CAISO keeper to 2026-09-05-caiso-246-b1-spot* | **02:08:00Z** | **2026-09-07 02:08Z** |
>
> `git log --no-merges --since=2026-09-05T02:08:01Z -- frontend/data/backcast/keepers`
> returns **EMPTY**. ERCOT (`4bc8745a`, 08-31) and NEISO / PJM / `index.json`
> (`5aa9100f`, 08-30) are older still. **No keeper moved between 02:08Z and this
> pin — 16 h 29 m of stillness**, and the three clocks are exactly the ones the
> ruling names.
>
> **The three stale goldens, re-derived against
> `results/regression-goldens/perfb-stage0/manifest.json`:** CAISO golden
> **`2026-09-01-caiso-231-b1-ungrounded`** vs live **caiso-246**; MISO
> **`2026-09-01-miso-198-oomlevel`** vs live **miso-213**; NYISO
> **`2026-09-04-nyiso-186-astoria-identity`** vs live **nyiso-189** — the
> 231/246, 198/213, 186/189 pairs the ruling names, unchanged. Stage-0 stays
> **4 of 7**. **No capture was dispatched by this lane** — that is the ruling,
> executed by not acting.
>
> ### 🟠 R-AJ — THE PROOF RUN IS THE DIRECTOR'S, IT WAS NOT RE-TRIGGERED, AND **ITS STATUS IS UNREAD AT CLOSE**
>
> **The dispatch, recorded:** `golden-data-tier.yml` run **#11**, id
> **`33983249186`**, event **`workflow_dispatch`**, ref **`main`**, head
> **`a0014864`**, started **18:10:58Z**, in progress at 18:22Z, timeout 90 min.
> **Triggered by the director. This lane did not re-trigger it and dispatched no
> workflow at all.**
>
> **Corroborated from the checkout:** `a0014864` is on `main` — the merge of
> **#4772** at **18:07:19Z** — and **PERF-B s3 is reachable from it**: #4753 and
> #4755 (`0e1bebfd`, *"PERF-B s3: the finding, complete — full byte gate PASS
> (ERCOT fwd 2023-25, carve-out, NEISO) and the ERCOT forward perfb-s3-after
> manifest entry"*, 04:04:08Z). So the run sits on a head that carries the merged
> s3 work, as the ruling requires. `golden-data-tier.yml` is
> **`workflow_dispatch`-only** since 2026-09-03 (R-Y), concurrency group
> `golden-data-tier`, `timeout-minutes: 90` — consistent with the dispatch's
> record in every particular this lane can check.
>
> **🔴 STATUS AT CLOSE: UNREAD.** The Actions API path
> (`/repos/…/actions/runs/33983249186`) is one of the 403s above. **This lane
> therefore records neither a conclusion nor "in progress at close"** — both
> would be claims it did not observe, and the second would be a guess dressed as
> a reading. The run reference is carried here in full so the next lane with an
> API reads it in a single call. **Consequence: G2 leg 1 is NOT declared by this
> entry**, and the R-V keeper-freeze question stays where the ruling put it —
> **served at the next sitting**, not here.
>
> ### 🟠 R-AK — RECORDED ON THE DIRECTOR'S ATTESTATION; THE REPOSITORY CANNOT CORROBORATE THE BASIS, AND SAYS SO
>
> **The rule:** until the failure class clears, **records, capture and small
> repair lanes → Opus**; **adjudication-class lanes and core-infrastructure
> scope under rule 27 → Fable**, re-issued on failure.
>
> **The basis, as the director gave it:** four Fable sessions died at launch
> overnight with the **identical platform diagnostic** — *audit records v28
> second issue (04:03Z)*, *capx D57*, *nyiso-189*, *miso-213* — while **every
> Opus session completed**. **Session launch outcomes leave no artifact in the
> tree**, so this lane records the basis on the director's attestation and
> **does not claim to have verified it**. What the tree weakly corroborates is
> only the re-issue half: capx D57 completed and merged (#4761 18:21:31Z, #4775
> 18:29:03Z), and nyiso-189 (`e69fcd54`) and miso-213 (`3a6e90b6`) both landed.
>
> **Recorded for completeness, as the ruling asks:** the **first v28b session
> (Opus)** did **not** die at launch — it launched, ran, and **stopped at
> 18:17Z on a permission question, pushing nothing**; it is archived. **A
> different failure class** from the four Fable launch deaths, and it belongs on
> the record beside them precisely because the two are easy to conflate: one
> class never reaches the work, the other reaches it and stops short of landing.
>
> ### QUEUE AMENDMENTS — 2026-09-05, THIS LANE (dated amendments; **v27 and v28 are not rewritten**)
>
> | queue item | amendment |
> |---|---|
> | **Y-1** | **R-AH recorded.** The flip is the owner's **Settings action on the first 6-of-6 head**, and **that condition was met at 18:06:46Z** — run 2456, head `dd555499`, #4771, **6 of 6**. Y-1 no longer waits on the flip set; it waits on the Settings action itself. Whether that action has been taken is **UNREAD at this pin** (API 403), which is **not** the same as "not live"; v28's "NOT live" reading, one entry below, rests on local equivalents rather than the required checks. |
> | **X-2** | **R-AI recorded: HOLD, no capture dispatch.** Re-capture only if the keepers stay still through R-AF's limb; clocks **2026-09-07 01:03Z NYISO / 01:21Z MISO / 02:08Z CAISO**, **all three intact** — no keeper has moved since 02:08:00Z. Stage-0 stays **4 of 7** (231/246, 198/213, 186/189). |
> | **G2 leg 1** (carried on **X-3**, served at **Y-2**) | **R-AJ recorded.** **X-3's non-launch is discharged** — PERF-B s3 merged (#4753 / #4755) and is in `a0014864`. The **one** authorized golden-tier proof is run **#11 / `33983249186`**, director-triggered, **status unread here**. Leg 1 is **not declared**; the declaration and the R-V keeper-freeze question both wait on that conclusion, at the next sitting. |
> | **R-AK** *(NEW)* | **Launch-failure routing in force.** Records / capture / small repair → **Opus**; adjudication-class and core-infrastructure (rule 27) → **Fable**, re-issued on failure. Standing until the failure class clears. The first v28b session's 18:17Z permission stall is recorded as a **distinct class**, not a launch death. |
>
> ### SEQUENCING AGAINST v28 — **IT MERGED INSIDE THE WINDOW; THIS BLOCK SITS ABOVE IT**
>
> The dispatch gave this lane 45 minutes to see whether the parallel "Audit
> records lane v28" landed first. It did: `claude/audit-records-v28-r3kq9m`
> appeared on `origin` at **18:32Z** (poll 1 — it had no branch when this lane
> started) and merged as **#4776** at **18:36:20Z** (poll 2, 18:37Z). This lane
> **rebased onto it** and appends **above** the v28 entry, per the sequencing
> rule. **Nothing in v27 or v28 is rewritten** — including the R-AH sweep line
> corrected above, which stands as v28 wrote it.
>
> ### Q-4 AT CLOSE
>
> Word-boundary grep across `docs/` after writing: **`R-AH` **2** files ·
> `R-AI` **2** · `R-AJ` **2** · `R-AK` **2**.** Exactly the two files this lane touched, for all four — no third
> file, and no label leaked outside the two canonical records. `R-AH`'s two
> hits include **v28's own sweep line**, which cited the label while concluding
> it had not been issued (corrected above); `R-AI` / `R-AJ` / `R-AK` appear
> nowhere but here. Each of the
> four rulings is diffed against a changed target file in the PR body, one row
> per ruling, as Q-4 requires.
>
> **Records integrity.** Clean tree at session start after
> `git reset --hard origin/main` (`git status --porcelain` empty), and again
> after the rebase onto the merged v28; **closing diff confined to these two
> files** — this board and the plan, **insertions only, zero deletions**.
> **Verified untouched:** every keeper shard, every `status/<ISO>.js`,
> `calibration-complete.json`, `holdout-freeze.json`, `program-status.json`,
> every matrix shard, every workflow, every bundle / sidecar / registry file,
> every golden manifest. **No solve, no score, no registration, no keeper shard,
> no marker, no matrix shard, no workflow dispatch.** CI runs on this lane's PR:
> both target files are enrolled in `ci.yml`'s path filter, widened at **Y-4**
> exactly so records PRs report rather than deadlock (`.github/workflows/ci.yml`,
> the two filenames listed under "THE PATH-FILTER TRAP").
>
> **🔴 ONE THING THIS LANE COULD NOT DO.** The dispatch's push-and-PR route was
> `git push -u origin <branch>` **plus** the GitHub MCP tool
> `mcp__github__create_pull_request`. **That tool is not attached to this
> session, and the REST fallback is the same 403 as above.** The branch is
> pushed; **the PR must be opened by hand or by a lane that has the tool** —
> stated here rather than left as a silent gap, because a records block that
> never reaches a PR is exactly the failure Q-4 exists to prevent.

> # 🟠 v28 (2026-09-05, pin `a0014864`) — **THE DISPATCH'S ONE MINTING JOB WAS OVERTAKEN BY ITS OWN LANE: Y-7 LANDED ELEVEN MINUTES BEFORE THIS PIN AND CLOSED ALL THREE FLIP-SET REDS. AND THE FLIP SET ITSELF IS UNREADABLE FROM THIS LANE — THE GITHUB API IS 403 HERE, THE FIRST INSTRUMENT THIS BOARD HAS EVER LOST.**
>
> **THE PIN MOVED UNDER THIS DISPATCH FOR THE FIFTH CONSECUTIVE CYCLE.** The
> director pinned `182aa74a` (commit 15:27:57Z, derivation 15:32Z);
> `origin/main` was **`a0014864`** at poll 1 (18:11Z) and poll 2 (18:12Z) —
> stable across both. The window `3cdf1cac..a0014864` is **105 commits, 32
> merges (#4740–#4772)**; the dispatch's own window at `182aa74a` was 95
> commits, 29 merges, #4740–#4769. The three merges that moved it are
> **#4771** (`d71fdfe6`, 18:06:46Z, the Y-7 lane), **#4770** (`d1e6d5bd`,
> 18:07:03Z, miso-215) and **#4772** (`a0014864`, 18:07:19Z, caiso-250). **No
> `claude/audit-records-v28-*` head existed on origin at either poll** — no
> remnant; this lane is v28. **Zero solves, zero scoring, zero registration.**
> Every figure below is re-derived at `a0014864`; where it differs from the
> dispatch's record at `182aa74a`, the difference is stated and this reading
> governs.
>
> ### 🟠 JOB 5's MINT — **SUPERSEDED BY EXECUTION. Y-7 RAN, AND FINISHED, WHILE THIS LANE WAS READING ITS DISPATCH**
>
> The dispatch's JOB 5 says *"Mint Y-7 (the flip-set closer lane: F401 fix,
> six-file format, the eight facade re-exports)"* and names it as *"the
> audit-program Y-7 lane launched alongside you"*. It launched **18 seconds**
> after this lane (roster: Y-7 flip-set closer created **15:37:23Z**, Opus;
> this lane **15:37:05Z**, Opus) and **completed**, landing all three items in
> **PR #4771** at **18:06:46Z** — **eleven minutes before this pin**:
>
> | Y-7 item | commit | time | verified at `a0014864` |
> |---|---|---|---|
> | 1 — drop unused `subprocess` import (F401) | `d66aeb0c` | 15:42:33Z | `ruff check scripts/gen_nyiso191_attestation.py` → **All checks passed**; the import is gone from the file |
> | 2 — `ruff format` the six named files | `0b51f28e` | 15:43:22Z | `ruff format --check .` → **1386 files already formatted** |
> | 3 — register the capx D59 locality names on the frozen facade surface | `dd555499` | 15:45:12Z | `tests/regression/test_constants_facade.py` → **2 passed** |
>
> **So Y-7 is not minted here as an open item. It is recorded as EXECUTED.**
> This is the **second consecutive cycle in which the board's assigned job was
> already done by another lane before the records lane could write it** — v27's
> JOB 0 by the capx desk ten minutes after the sitting, v28's JOB 5 by the Y-7
> lane eleven minutes before the pin. The pattern is now a class, not a
> coincidence: **a records dispatch written at pin P describes a world that no
> longer exists by the time the lane reaches P+1.** Recorded for the owner as
> the sharpest instance yet of what Z-3 measures.
>
> ### 🟢 SEVEN GATES — **ALL SEVEN EXIT 0**, exactly as the dispatch said; ONE FIGURE DIFFERS
>
> Each script invoked alone under `uv run --frozen`, `$?` read immediately,
> never through a pipe:
>
> | gate script | exit | reading at `a0014864` | vs dispatch record (`182aa74a`) |
> |---|---|---|---|
> | `audit_keepers.py --check` | 🟢 0 | **PASS 0 failures / 0 warnings** — six keepers + holdout/marker/status | unchanged |
> | `check_registry_payload_parity.py` | 🟢 0 | **66 runs, 108 bundle dirs, 0 known-unsynced tolerated** | unchanged |
> | `check_gate_a_provenance.py` | 🟢 0 | **6 rows** — keeper identity + marker match, no determination read | unchanged |
> | `check_mechanism_matrix.py` | 🟢 0 | **195 field + 49 row + 164 path** anchors, 6 shards, stamps + §5.x headers match | unchanged |
> | `check_forecast_staleness.py` | 🟢 0 | **Δ = 7** (threshold 10); **25 of 97** verdicts undated; newest scored sha `921bb4cd` @ 06:40:20Z | **Δ 3 → 7** |
> | `check_bench_freshness.py` | 🟢 0 | **20 parts, 0 STALE, 20 engine-drift** (NEISO/PJM 73 engine commits, NYISO 19) | unchanged |
> | `check_golden_manifest.py` | 🟢 0 | **47 manifests, 88 entries (24 enforced / 64 legacy), 3 stale** | unchanged |
>
> **Six of the seven readings match the dispatch to the digit.** The one that
> does not is **FR-21's solve-affecting Δ: 7, not 3** — still well under the
> threshold of 10, so the gate's exit is unaffected, but the dispatch's figure
> is superseded. **X-6b is discharged on its first leg**: the newest scored sha
> is `921bb4cd`, and `921bb4cd` **is reachable** — it is merge **#4762**
> (2026-09-04 22:14:44-07:00) in this very window, not an orphan. v27's
> "Δ = unknown / rebased-away stamp" reading is superseded. **The undated half
> stands unchanged: 25 of 97 verdict stamps carry no scored-at date**, so their
> freshness is UNKNOWN regardless of what the newest scored one says.
>
> ### 🔴 THE FLIP SET — **NOT READ THIS SITTING. THE GITHUB API IS 403 AT THIS LANE.**
>
> **This is a new kind of gap and it must not be papered over.** Every prior
> records lane read the flip set, the run-conclusion streak and the PR states
> from the GitHub API. At this lane the API returns **HTTP 403** — body:
> *"GitHub access is not enabled for this session. An org admin must connect
> the Claude GitHub App for this organization."* — for every endpoint, with and
> without the session's `GITHUB_TOKEN`. The agent proxy's own documentation is
> explicit that a 403 of this class is an organization policy denial to be
> **reported, not retried or routed around**, so it was not. `gh` is not
> installed in this container.
>
> **Therefore this entry states NO flip-set count, NO run number, NO run id and
> NO run-conclusion streak.** The dispatch's "run 2454, id 33974877017, head
> `1e43fe10`", its "3 of 6", and its "2431–2454 all `failure`" are **carried as
> the dispatch's record, unverified by this lane** — the one place in this
> entry where a dispatch figure is neither confirmed nor superseded.
>
> **What CAN be established, and is:** the three reds the dispatch named are
> repaired **in the tree** at `a0014864`, and the local equivalent of **all six**
> flip-set jobs is green. Every command below run alone under `uv run --frozen`
> at this pin:
>
> | flip-set job (`ci.yml`) | local equivalent | result at `a0014864` |
> |---|---|---|
> | `Ruff lint + format` | `ruff check` (that script) · `ruff format --check .` | 🟢 All checks passed · **1386 files already formatted** |
> | `Fast test tier` | `pytest -n 2 -m "not slow and not integration and not fulldata"` | 🟢 **8021 passed, 35 skipped, 2 xfailed, 536 subtests, 0 failed** (341 s) |
> | `Structural refactor guards` | `compileall` · `ci_refactor_guards.py` · facade + persisted-identity tests | 🟢 exit 0 · exit 0 (*import-walk OK, script-refs OK*) · **2 passed** |
> | `Rule-22 quarantine gates` | `audit_keepers` · `parity` · `golden_manifest` | 🟢 all exit 0 (above) |
> | `Cache-key registration guard` | `check_cache_key_registration.py` | 🟢 exit 0 — 792 fields, 247 registered, **247 declared defaults match HEAD** |
> | `Pinned default cache key` | `test_persisted_identity.py` + `test_cache_key_default_flip_guard.py` | 🟢 **24 passed** |
>
> The dispatch's own evidence for the Fast-tier red was *"run 2451: 1 failed /
> 8014 passed"*, the single failure being the facade test. At this pin that
> test passes and the tier is **8021 passed / 0 failed**. **So every cause the
> dispatch named is gone.** Whether CI has yet *run* a head containing #4771,
> and what it concluded, **this lane cannot say.** The flip remains **NOT
> live**; the precondition question is the owner's and is unchanged by this
> entry.
>
> ### 🟢 KEEPERS — SIX SHARDS, **NO MOTION SINCE `e75250c7`**, AND THE CLAIM IS NOW STRONGER THAN THE DISPATCH'S
>
> | ISO | keeper at `a0014864` | last content commit | frontier |
> |---|---|---|---|
> | CAISO | `2026-09-05-caiso-246-b1-spot` | `84e4ccb0` **02:08:00Z** | no key |
> | MISO | `2026-09-05-miso-213-layering` | `3a6e90b6` **01:21:15Z** | no key |
> | NYISO | `2026-09-05-nyiso-189-steam-identity` | `e69fcd54` **01:03:41Z** | declared 08-23, **`withdrawn` 08-30 ⇒ ABSENT** |
> | ERCOT | `2026-08-25-234-eastex-identity` | `4bc8745a` 08-31 03:51Z | **present** (08-31) |
> | NEISO | `2026-08-17-neiso-99-joint-p1` | `ddf8e676` 08-18 01:00Z | **present** (07-11) |
> | PJM | `2026-08-15-pjm-162-inputclock` | `a9a57f47` 08-16 05:11Z | **present** (07-31) |
>
> The three promotions are the dispatch's three, to the commit and the second.
> **ERCOT / NEISO / PJM are byte-untouched — R-V's freeze is INTACT.** The
> newest commit of any kind touching `keepers/` in the window is `e686fc78`
> (#4751, **02:36:08Z**), which precedes `e75250c7` (**02:41:32Z**): so the
> dispatch's *"no keeper motion since `e75250c7`"* holds — **and holds across
> the fifteen further PRs (#4758–#4772) that landed after the dispatch was
> written.** Sixteen hours of keeper stability at this pin.
>
> ### 🟢 MARKERS — EVERY FIELD THE DISPATCH NAMED, CONFIRMED FROM THE FILE
>
> `calibration-complete.json`: **`complete` = {ERCOT, NEISO, NYISO, PJM}**;
> **`withdrawn` = {CAISO}**; **`final` = EMPTY** (deliberately, since
> 2026-07-31). NYISO's entry: `declared` **2026-09-05**, `keeper`
> **`2026-09-05-nyiso-189-steam-identity`** and `keeper_at_declaration` the
> **same** run; `by` names **owner ruling Q38, 2026-09-04, at the
> capacity-expansion director's refresh-#35 sitting on card C-9** (*"Re-declare
> now via a records lane"*); `determination` **CALIBRATED on nyiso-189,
> RE-VERIFIED 2026-09-05 without a solve** (`calibration_verdict.py --run-id`,
> committed artifacts only, at `origin/main` **`921bb4cd`**);
> `frontier_basis` **"NONE CLAIMED by this declaration"**;
> `tier_authorized` validation only; `locked_test` **NOT AUTHORIZED**;
> `redeclaration` records this as the **THIRD grant**, not a first.
> `holdout-freeze.json`: **active**, **`scope.tiers = ["locked_test"]`** —
> tier-scoped, so the validation tier is not frozen. **No locked-test year has
> ever been solved, scored or registered for any ISO.**
>
> ### 🟢 JOB 2 — DIRECTOR RULING (f), RECORDED VERBATIM; THE TEST IS NOW THREE INSTRUMENTS AND **NYISO IS ALIGNED**
>
> > "`frontier` is not an alignment leg. It is a separate owner claim about
> > mechanism exhaustion (NEISO's `complete`, 2026-07-07, preceded its
> > `frontier`, 2026-07-11). The four-instrument test is henceforth three
> > instruments — `complete`, gate-(a), ISO-level determination — with
> > `frontier` reported beside them, never required to agree."
>
> | instrument | membership at `a0014864` | source |
> |---|---|---|
> | `complete` marker | **{ERCOT, NEISO, PJM, NYISO}** | `calibration-complete.json` |
> | gate-(a) `status: pass` | **{ERCOT, NEISO, PJM, NYISO}** — guard exit 0, 6 rows | `program-status.json` |
> | **ISO-level** determination `CALIBRATED` | **{ERCOT, NEISO, PJM, NYISO}** | `status/<ISO>.js` |
> | *`frontier` (reported beside, not a leg)* | *{ERCOT, PJM, NEISO}* | *keeper shards* |
>
> **All three legs agree. NYISO is ALIGNED again.** Full ISO-level read:
> **ERCOT CALIBRATED · NEISO CALIBRATED · NYISO CALIBRATED · PJM CALIBRATED ·
> CAISO NOT-YET · MISO NOT-YET**; gate-(a) fails for CAISO and MISO, both of
> which are also absent from `complete` — **the two non-aligned ISOs are
> non-aligned consistently, on all three legs.** The split v27 opened is gone.
>
> **Z-4 is CLOSED.** Both rulings stand on the record and neither is
> adjudicated here: **R-AG** (2026-09-04 22:20Z — route the NYISO
> re-declaration question to the calibration director for a recommendation, no
> audit-lane marker edit) and **Q38 / D56-R** (the capx desk's execution, 58
> minutes later, without sight of R-AG). They coexist. **The marker was moved
> by the capx desk's lane; this board records that and adjudicated nothing.**
> The calibration director desk R-AG named exists — a session opened
> **03:29:10Z**, still running at this pin — and the capx ledger's r#36 entry
> records the cross-desk position in its own words: *"audit ruling R-AG …
> routed the NYISO re-declaration to the calibration director for a
> RECOMMENDATION with no audit-lane marker edit; Q38 … ruled the execution 58
> minutes later without sight of it (R-AG was unrecorded until audit board
> v27). Both are the owner's; they coexist; C-10 is the recommendation R-AG
> asked for."* **v27's remedy worked**: `R-AG` grepped **zero** files at v27
> and grep **7** now.
>
> ### 🟢 JOB 3 — **Z-5, MINTED AND DISCHARGED IN THE SAME ENTRY. THE SPLIT THE DESK FEARED DID NOT OCCUR.**
>
> The owner's two acts, plainly:
>
> 1. **The D56 charter keyed `nyiso-188`.** `nyiso-189` superseded it at
>    **01:03:41Z** (`e69fcd54`), *before* D56 ran. A charter executed as
>    written would have re-declared `complete` onto a keeper that was no longer
>    live — the marker and the keeper shard would have disagreed the moment it
>    landed, and gate-(a) would have gone red on the identity leg it exists to
>    check.
> 2. **The capx desk re-issued D56-R on the live keeper** (its refresh **#36**)
>    and it landed **#4763** (`77d5a05d`) keyed to **`nyiso-189`**, with the
>    determination **re-verified from committed artifacts only** — no solve, at
>    `origin/main` `921bb4cd`.
>
> **No audit lane touched the marker at any point.** The split did not occur
> **because the re-issue read the live keeper rather than the charter's**, and
> the D-5(b) re-key duty attached on promotion is what made the live keeper
> visible to it. **Z-5 is minted here for the record and discharged by that
> execution in the same entry.**
>
> ### 🟢 R-T — MISS **#9** = `miso-213`; THE DESK'S OWN COUNT CONFIRMS IT, AND v27's ROUTED LEAF IS REPAIRED
>
> The MISO gate-(a) stamp was re-keyed to the live keeper by the **capx desk**,
> commit **`337829b3`**, **03:50:03Z**, under its standing Q34 duty — not by
> any audit lane. Its own message: *"eleventh guard firing, **ninth promoter
> miss since R-T**; the r#35 `read_live_at` leaf repaired"*. **Both of the
> dispatch's numbers are the desk's own** — eleventh firing, miss #9 —
> confirmed from the commit, not inferred. **Compliant in the window:
> `caiso-246` and `nyiso-189`.** No promotion since **02:08:00Z**, so the tally
> does not move.
>
> **And v27's routed item is DISCHARGED by the same commit.** v27 recorded the
> MISO row's `read_live_at` leaf stuck at the refresh-#32 pin `2b0b8796` beside
> a `corrected_by` saying `a35c9f9b`, a leaf the guard does not read, and
> **routed it to the capx desk**. The desk repaired it and said so in the same
> line. **The route worked; nothing is outstanding on that leaf.**
>
> ### 🟠 STAGE-0 — **4 OF 7, THREE STALE, CLOCKS UNCHANGED**
>
> `check_golden_manifest` at `a0014864`: CAISO golden `caiso-231-b1-ungrounded`
> **STALE** vs live `caiso-246-b1-spot`; MISO `miso-198-oomlevel` **STALE** vs
> `miso-213-layering`; NYISO `nyiso-186-astoria-identity` **STALE** vs
> `nyiso-189-steam-identity`. Current = {ERCOT, ERCOT\_\_carveout-2023, NEISO,
> PJM}. **The 48-hour clocks, read from the promoting commits** — `84e4ccb0`
> 02:08:00Z, `3a6e90b6` 01:21:15Z, `e69fcd54` 01:03:41Z — fall due
> **2026-09-07 02:08Z (CAISO) / 01:21Z (MISO) / 01:03Z (NYISO)**, absent a
> further promotion: **unchanged from the dispatch**, and none has fallen due
> at this pin. *(R-AF's own text remains recorded only via the v26
> transcription; the limb's exact wording is still not on the record and this
> clock is this lane's reading of it — carried forward unresolved for the third
> cycle.)*
>
> ### 🟠 JOB 4 — THE DISPATCH-VS-LAUNCH LEDGER, BOTH LEGS. **THE ROSTER LEG IS PRESENT AT THIS LANE, NOT ABSENT.**
>
> **The dispatch says the roster leg is "restored at the DESK and absent at
> your lane". It is not absent: `list_sessions` returned 30 rows to this lane.**
> Every roster figure below is this lane's own read, not the desk's relay. The
> API leg is the one that is missing here (above) — the two legs have swapped
> since the dispatch was written.
>
> | session | created | model | status | branch | outcome |
> |---|---|---|---|---|---|
> | **Y-6** flip-set closer | 03:59:32Z | **Opus** | ARCHIVED | **none** | completed, **pushed nothing** |
> | Audit records lane v28 **#1** | 03:59:14Z | **Fable** | ARCHIVED | **none** | archived unrun (director) |
> | Audit records lane v28 **#2** | 04:02:13Z | **Fable** | ARCHIVED | **none** | failed at launch |
> | Audit records lane v28 **#3** — *this lane* | 15:37:05Z | **Opus** | RUNNING | `claude/audit-records-v28-r3kq9m` | this entry |
> | **Y-7** flip-set closer | 15:37:23Z | **Opus** | ARCHIVED | — | **#4771 merged 18:06:46Z** |
> | **"Audit rulings records v28b"** | **18:11:21Z** | **Opus** | **BLOCKED** | **none** | **needs input: repo permissions** |
>
> **Y-6 — DISCHARGED, confirmed on both legs.** Roster: Opus, archived, **no
> branch**. Both of its conditional items were already closed at its pin by the
> capx desk's **`337829b3`** (03:50:03Z, nine minutes before Y-6 launched): the
> MISO re-key **and** the `test_clean_io` roster entry — the commit touches
> exactly two files, `program-status.json` (12 lines) and
> `tests/curation/test_clean_io.py` (+6/−1), its message naming *"add
> `ra-import-allocations` to the frozen `test_clean_io` roster (the caiso-245
> intake's orphaned Fast-tier red)"*. **So Y-6 correctly pushed nothing.
> Retired by execution.**
>
> **A FOURTH v28 SESSION EXISTS, AND IT IS BLOCKED ON THE SAME WALL THIS LANE
> HIT.** *"Audit rulings records v28b"* (Opus, **18:11:21Z**) is
> `SESSION_STATUS_BUCKET_BLOCKED`, no branch, no push, its own post-turn
> summary reading: *"How would you like to proceed — grant the git permissions
> and a PR route, or re-dispatch this lane somewhere with them?"* **This lane
> hit the identical wall**: at start-up the container had **no checkout at
> all**, and both the repo attach and a direct `git clone` were refused by the
> permission classifier. This lane only proceeded because a human intervened
> and the attach was re-tried successfully; **v28b has not had that
> intervention and is idle at the same point.** It is **not** a competing
> writer — it holds no branch and can land nothing — so no remnant arises from
> it.
>
> **This is a THIRD failure class, distinct from the dispatch's new one.** The
> dispatch mints G-14's *"launched and died before its first push"* from v28 #2.
> The roster now separates three:
>
> | class | signature | instances tonight |
> |---|---|---|
> | non-launch | no session row at all | (historic) |
> | **launched-and-died-before-first-push** | session row, archived, no branch, tokens burned | **v28 #1, v28 #2** |
> | **launched-and-blocked-on-repo-access** | session row, **still live**, no branch, awaiting input | **v28b**, and **this lane before intervention** |
>
> The third is the more dangerous of the two new ones **because it does not
> archive**: it sits in the roster looking alive, indefinitely, having produced
> nothing. From the desk's side it is indistinguishable from a lane that is
> merely slow.
>
> **On the model observation — the roster supports LESS than the dispatch
> claims, and the difference is stated.** What it *does* show: **both
> Fable-assigned v28 attempts produced nothing (no branch, archived), and both
> Opus-assigned records lanes ran** — v28 #3 is writing this, Y-6 and Y-7 both
> completed. What it does **not** show is the dispatch's wider claim that *"the
> same failure diagnostic hit three other Fable sessions the same night
> (nyiso-189, miso-213, capx D57)"*: those three sessions all carry **branches**
> (`claude/nyiso-190-cc-regular-2024-displacem…`,
> `claude/miso-214-ct-peaker-conduct`, `claude/capx-d57-pjm-clearing-build-s4i321`)
> and are archived in the ordinary way, and the roster exposes **status, not
> failure reasons**. **The three-Fable-session claim is therefore recorded as
> the dispatch's, unverified here.** An observation for the owner either way;
> **adjudicated by nobody on this board.**
>
> ### 🟢 PERF-B s3 — **LAUNCHED AND COMPLETE**; X-3 DISCHARGED ON THE FINDING'S OWN NUMBERS
>
> v27 recorded PERF-B s3 as **NOT LAUNCHED** with a Z-3 expiry. **Z-3's fifth
> inversion**: it launched, ran and finished. **C-2 / C-1a / C-1b merged in
> #4745, #4752, #4753, #4755.** The finding
> `docs/FINDING-perfb-s3-adaptive-pass-2026-09.md` is **FILLED — 278 lines**,
> not a stub. Headline as the dispatch records it, confirmed from the document:
> **full byte gate PASS at `atol=rtol=0`** on ERCOT forward 2023-25,
> `ERCOT__carveout-2023` and NEISO against merge-base controls; **ERCOT forward
> 4859.5 → 3592.3 s (−1267 s, −26 %)** over three years; **C-3 skipped as
> optional**; **C-4 refuted** (0 s on ERCOT, never chartered); **caiso-205
> deliberately left unwired**, to a CAISO lane.
>
> **X-3 (`markup`) is DISCHARGED**, and the residual is on the record at §5.1:
> C-2 attributed the old `markup` to mis-booked builds and prior-pass solves
> (control rows carry `prior_solve` **672.2 / 654.0 / 945.9 / 763.3 s**; those
> clauses are simply **absent** from every shipped row), and shipped `markup`
> now reads **37.1 / 41.3 / 27.9 s** on ERCOT forward 2023/24/25 and **33.9 s**
> on the carve-out — **the dispatch's "28–41 s/yr", confirmed to the tenth.**
>
> ### 🟢 CAPX LANES — RECORDED ONLY WHERE THEY MOVE THIS BOARD'S SURFACES
>
> **D53** merged via the cleanup PR **#4766** (`98156e1f`; the D53 cleanup
> merge `b6f5bdff` is one of the three commits that last touched the six files
> Y-7 item 2 reformatted). **D54** #4746, **D55** #4747, **D56-R** #4763,
> **D59** #4760 + #4764 — all merged. **D57 is OPEN**: `#4761` does not appear
> in the window's merge list, and a *"PR merge conflict resolution"* session
> (Opus, 18:08:34Z, branch `d57-merge`) is live at this pin. Their footprint on
> this board is exactly three surfaces: **the marker** (D56-R), **the gate-(a)
> row** (the Q34 re-key), and **the three CI reds** (D59's locality names, the
> D53 cleanup merge, nyiso-191) — **all three of which Y-7 has now closed.**
>
> ### 🟢 JOB 7 — Q-4 CLOSE-OUT
>
> **(i) Ruling-label sweep, word-boundary, across `docs/`.** All of
> `R-A … R-AG` resolve to real references (`R-A` 98 files … `R-AD`/`R-AA` 2
> each). The two the dispatch predicted at zero:
>
> * **`R-AH` → 0 files. Confirmed: none issued. Nothing minted.**
> * **`Q39` → 6 files — NOT zero, and the dispatch's prediction is wrong on the
>   count while right on the substance.** No Q39 *ruling* has been issued; the
>   label appears only as a **reserved forward range** in the capx ledger's
>   r#36 entry — *"Rulings, when given, are Q39–Q41"* — and its echoes in the
>   prompt pack, the handoff, the D56-R finding, the NYISO matrix shard and the
>   NYISO calibration log. **Recorded as: reserved, unissued. Nothing minted.**
>
> Also swept: **`Z-5`, `Y-6`, `Y-7` → 0 files each before this entry** (Y-7's
> three commits carry the label in `git log` only, never in `docs/`) — this
> entry is the first `docs/` record of all three. **`R-AG` → 7** (v27's fix
> holding). **`Q38` → 8**, **`D56` → 13**, **`D56-R` → 7**, **`Z-4` → 6**.
> *(Hygiene note carried forward from v27: `Y-1`, `Y-3`, `X-2`, `X-3` and
> `G-14` also collide with other programmes' item labels, so a bare count is
> not a reference count for those five.)*
>
> **(ii) Each job diffed against a changed target file.**
>
> | job | target file | this lane's diff |
> |---|---|---|
> | 1 — gate/keeper/marker/stage-0 refresh | board | **written** (this entry) |
> | 2 — ruling (f) + alignment + Z-4 close | board | **written** |
> | 3 — Z-5 mint + discharge | board | **written** |
> | 4 — dispatch-vs-launch ledger | board | **written** |
> | 5 — queue v28, cards, Y-6/Y-7, X-6b | board | **written** |
> | 6 — plan §8 ledger entry | plan | **written** |
> | 7 — Q-4 close-out | board | **written** |
> | *flip-set / run listings* | *—* | **NOT WRITTEN — API 403 (above)** |
>
> **(iii) Workflow run listings — BLOCKED, and this is the one dispatched item
> this lane could not perform.** `ci.yml` and `golden-data-tier.yml` run
> histories are API-only; the API is 403 here. **From the workflow files
> themselves, which are readable:** `golden-data-tier.yml` is
> **dispatch-only** — its `on:` block is `workflow_dispatch:` alone, commented
> *"Dispatch-only since 2026-09-03 (R-Y). No `schedule:`"* — which **confirms
> the dispatch's characterisation of the trigger**, though *"run #10 green
> 09-04; no run since"* cannot be checked here. `ci.yml`'s `pull_request`
> **path filter carries this board and this plan explicitly** (plus
> `docs/FINDING-*.md`), the Y-4 widening, deliberately not `docs/**` — **so CI
> does run on this lane's PR.**
>
> ### QUEUE v28
>
> | item | state at `a0014864` |
> |---|---|
> | **X-2** | 4/7; three stale, clocks **unchanged** — CAISO due 09-07 02:08Z, MISO 01:21Z, NYISO 01:03Z; **no promotion since 02:08Z**; hold the re-captures until the clocks (card C) |
> | **X-3** | **DISCHARGED** — PERF-B s3 complete; shipped `markup` 27.9–41.3 s/yr |
> | **X-4** | per its finding |
> | **X-5** | unchanged |
> | **X-6** | routed unchanged; **X-6b: first leg discharged** — `921bb4cd` is reachable (#4762), v27's orphaned-stamp reading superseded, **Δ = 7**; the undated half (**25 of 97**) stands |
> | **Y-1** | owner flip pending; **flip-set count NOT READ this sitting (API 403)**; all three named causes repaired in-tree, six-of-six local equivalents green; **flip is NOT live** |
> | **Y-2** | G2 sitting after the flip |
> | **Y-3** | R-T **miss #9 = miso-213**; the desk's own count ("eleventh guard firing, ninth promoter miss"); **v27's `read_live_at` leaf REPAIRED by `337829b3`** |
> | **Y-4** | RETIRED |
> | **Y-5** | discharged at v27's coda |
> | **Y-6** | **RETIRED BY EXECUTION** — completed without a PR; both conditional items pre-closed by `337829b3` |
> | **Y-7** | **NOT MINTED AS OPEN — RECORDED AS EXECUTED**, #4771, all three items, 18:06:46Z |
> | **Z-1** | unchanged |
> | **Z-2** | **run-conclusion streak NOT READ this sitting (API 403)** |
> | **Z-3** | applied; **fifth inversion** (PERF-B s3 launched and completed after v27 recorded it not-launched) |
> | **Z-4** | **CLOSED** — R-AG and Q38/D56-R coexist on the record; marker moved by the capx desk's lane; this board adjudicated nothing; three-instrument test aligns |
> | **Z-5** | **MINTED AND DISCHARGED** in this entry — D56 keyed nyiso-188, D56-R re-issued on live nyiso-189, no split |
> | **G-14** | **two new classes separated**: *died-before-first-push* (v28 #1, #2) and *blocked-on-repo-access* (v28b, and this lane pre-intervention) |
>
> ### OWNER CARDS SERVED THIS SITTING — FOUR
>
> * **A (Y-1, the flip).** All three loose ends the dispatch assigned to Y-7 are
>   **closed in-tree** by #4771, and the local equivalent of all six jobs is
>   green at this pin. **The flip-set count itself was not read** (API 403).
>   The standing condition is unchanged: **flip on the first 6-of-6 CI-covered
>   head** — a reading someone with API access must take.
> * **C (X-2).** **Hold** the three re-captures until the 09-07 clocks. No
>   promotion since 02:08Z; nothing falls due at this pin.
> * **D (G2 leg 1 + R-V).** PERF-B's WS3 charter is **complete on record**. The
>   director recommends **one `golden-data-tier.yml` `workflow_dispatch` on the
>   merged s3 head** as the CI proof, then a declaration on leg 1 and a
>   **lift-or-keep decision on the R-V keeper freeze** — the owner's, both. The
>   workflow is confirmed dispatch-only, so this is a deliberate manual act.
> * **E (infrastructure, no ruling asked).** The launch-failure classes above —
>   including the **new blocked-on-repo-access class**, of which there is a
>   **live instance right now** (v28b). Two of the three v28 records attempts
>   before this one produced nothing; a fourth is stalled on permissions. **The
>   records lane's throughput is currently limited by session provisioning, not
>   by the work.**
>
> **Records integrity:** touched **only** this board and the plan. **Verified
> untouched** (clean tree at session start; closing diff confined to the two
> files): every keeper shard, every `status/<ISO>.js`,
> `calibration-complete.json`, `holdout-freeze.json`, `program-status.json`,
> every matrix shard, every workflow, every bundle / sidecar / registry file,
> every golden manifest. **No solve, no score, no registration.** *(Method
> notes: the container held **no checkout at all** at start-up — the clone is
> this lane's own, `--depth 1` then `fetch --depth=1000 origin main` to reach
> `3cdf1cac`; read-side git only, no working-tree change. The GitHub API was
> probed with and without the session token, returned 403 both ways, and was
> **not** routed around.)*
>
>
> ### 🔴 POST-CLOSE CODA AT `ee7754c1` — **Y-7's FIX SURVIVED FIFTEEN MINUTES. THE FACADE RED IS BACK, FROM THE NEXT CAPX LANE, AND D57 IS NO LONGER OPEN.**
>
> Between poll 2 (18:12Z) and the push, `origin/main` advanced **four merges**
> to **`ee7754c1`**: **#4773** (`0d59d3d9`, miso-216 prereg, 18:15:19Z),
> **#4774** (`b9cc07dd`, the calibration-workstream director desk),
> **#4761 — capx D57** (`ee7754c1`, **18:21:31Z**), and the D57 branch's own
> merge of main. This lane rebased onto `ee7754c1` and re-ran every gate and
> check the four merges can move. **No protected surface moved**: no keeper
> shard, no `calibration-complete.json`, no `holdout-freeze.json`, no
> `status/<ISO>.js`, no `program-status.json`, no workflow. **So every keeper,
> marker, alignment, R-T, stage-0 and Z-4/Z-5 reading in this entry stands
> unchanged at `ee7754c1`.** The **six matrix shards and the matrix index did**
> move, and `check_mechanism_matrix.py` re-run at the new head still exits
> **0** with the **same 195 field + 49 row + 164 path anchors**.
>
> **Two corrections to this entry, both from D57's merge:**
>
> 1. **D57 IS MERGED, NOT OPEN.** The entry above records `#4761` as open on
>    the evidence of the window's merge list at `a0014864`; it merged at
>    **18:21:31Z**, four minutes after this lane's second poll. The `d57-merge`
>    session recorded as live was resolving exactly that. **Every capx lane
>    named in this entry (D53, D54, D55, D56-R, D57, D59) is now merged.**
> 2. **THE FLIP SET'S FACADE RED IS BACK.** `capx D57` adds **+96 lines** to
>    `src/market_sim/config/capacity_market.py`, and
>    `tests/regression/test_constants_facade.py::test_moved_surface_is_complete`
>    **fails at `ee7754c1`**:
>
>    > `market_sim.config.capacity_market grew names the facade does not re-export: ['ClearedCapacityPrice', '_SUPPLY_CLEARING_REFUSED_LOGGED', 'resolve_capacity_market_supply_clearing']`
>
>    **This is the same failure mode, on the same file, that Y-7 item 3 closed
>    for capx D59 (`dd555499` 15:45:12Z, merged in #4771 at 18:06:46Z) —
>    reopened by the next capx merge **fourteen minutes and forty-five seconds
>    later.** `Structural refactor guards` and `Fast test tier` both
>    depend on that test, so **two of the six flip-set jobs are red again in the
>    tree at `ee7754c1`**. The lint leg holds: `ruff check .` **exit 0** and
>    `ruff format --check .` **1386 files already formatted** at the new head,
>    so **Y-7 items 1 and 2 survive; only item 3's class recurred.**
>
> **THIS CHANGES WHAT Y-7 MEANT, AND THE OWNER SHOULD SEE IT.** The entry above
> reads Y-7 as draining a backlog of three merged lanes' loose ends. The coda
> shows it is **not a backlog — it is a recurring leak.** Y-7 closed 3 of 3, landing at
> 18:06:46Z; **the very next capx merge reopened one of them at 18:21:31Z**, by the
> identical mechanism (a promoting lane grows
> `market_sim.config.capacity_market` without registering the new names on the
> frozen facade surface). A closer lane run after each such merge will always be
> one merge behind. **The durable fix is not another closer lane; it is making
> the facade registration part of the promoting lane's own duty** — the same
> shape as D-5(b)'s re-key-on-promotion duty, which is precisely what kept the
> marker and the keeper in step for Z-5. **Recorded as an owner observation;
> adjudicated by nobody here, and no lane is minted for it** — card A's standing
> condition (flip on the first 6-of-6 CI-covered head) already covers the
> symptom, and this coda names the cause.
>
> **Card A is unchanged in form and worse in fact:** the flip-set count remains
> unread (API 403), and the tree-level evidence that stood at `a0014864` —
> six-of-six local equivalents green — **no longer holds at `ee7754c1`**: it is
> now **four of six**, with `Structural refactor guards` and `Fast test tier`
> red on the D57 names. **The flip is NOT live, and at this head it should not
> be.** Everything else in this entry stands at `a0014864` and re-verified at
> `ee7754c1`.
>
> ### 🟢 CODA ADDENDUM AT `8342d74d` — **THE PROMOTING LANE CLOSED ITS OWN RED IN EIGHT MINUTES. THE CODA'S RECOMMENDATION WAS ALREADY THE PRACTICE.**
>
> `origin/main` advanced twice more during the push. **#4775** (`8342d74d`,
> **18:29:03Z**) carries `7e058c12` — *"capx D57: register the three new
> `capacity_market` names in the constants facade + frozen inventory"* — **+3
> lines to `src/market_sim/config/constants.py` and +11 to the facade test's
> frozen inventory, and nothing else.** `test_constants_facade.py` **passes at
> `8342d74d` (2 passed)**.
>
> **So the facade red of the coda above was an eight-minute transient**
> (18:21:31Z → 18:29:03Z), closed **by the promoting lane itself**, not by a
> closer lane. **The coda's reading must be qualified, and it is qualified
> here rather than rewritten** (this board is append-only): the leak is real
> and it recurred, but **it did not need a closer lane — D57 sealed it
> unprompted, inside ten minutes, which is exactly the "promoting lane's own
> duty" shape the coda recommended.** The recommendation was therefore not a
> gap in practice but a **description of practice that already exists and is
> simply not written down as a duty.** What remains for the owner is only
> whether to make it explicit — the D-5(b) treatment — so that it does not
> depend on each lane noticing.
>
> **Net effect on card A:** the coda's "four of six" is superseded. At
> `8342d74d` **all six flip-set jobs' local equivalents are green again** —
> `ruff check` 0, `ruff format --check` 1386 formatted, facade 2 passed,
> refactor guards 0, the three Rule-22 gates 0, cache-key 0, pinned-key 24
> passed. **The flip-set count itself is still unread (API 403), and the flip
> is still NOT live.** This lane's branch is rebased onto `8342d74d`; the
> closing diff remains the two records files, 0 deletions.

> # 🟠 v27 (2026-09-05, pin `d9f034f0`) — **JOB 0 WAS ALREADY DONE — BY THE CAPX DESK, TEN MINUTES AFTER THE SITTING. THE FLIP SET FELL FROM 5 OF 6 TO 3 OF 6 ON THREE IN-FLIGHT LANES' LOOSE ENDS. AND THE ALIGNMENT SPLIT (Z-4) WAS OWNER-RULED *TWICE* IN ONE HOUR, BY TWO DESKS, THE SECOND UNABLE TO SEE THE FIRST — BECAUSE R-AG IS RECORDED NOWHERE.**
>
> **THE PIN MOVED UNDER THIS DISPATCH FOR THE FOURTH CONSECUTIVE CYCLE.** The
> director pinned `a35c9f9b` (22:18:40Z); `origin/main` was **`d9f034f0`** at
> poll 1 (00:12Z) and at poll 2 (00:20Z) — stable across both. The window
> `a35c9f9b..d9f034f0` is **60 commits, 14 merges (#4725–#4738), all landed
> 23:12Z–00:10Z**. No v27 existed at either poll, so this lane IS v27. **Zero
> solves, zero scoring, zero registration.** Every figure below is re-derived
> at `d9f034f0`; where it differs from the dispatch's record at `a35c9f9b`, the
> difference is stated and the record governs.
>
> ### 🟢 JOB 0 — **SKIPPED: THE STAMP WAS ALREADY CURRENT AT MY PIN.** RE-KEYED BY THE CAPX DIRECTOR DESK, NOT BY THIS LANE
>
> The dispatch's job 0 (MISO gate-(a) re-key to `miso-210-clock`) was executed
> **before this lane launched**: commit **`1cbaad95`**, 2026-09-04 **22:30:24Z**
> — ten minutes after the 22:20Z sitting — by the **capx director desk**
> (refresh **#35**, standing re-key duty under owner ruling **Q34**; its own
> message: *"tenth guard firing, eighth promoter miss since R-T"*), merged in
> **#4726** at 23:12Z. Verified from the commit's diff: the MISO row's `detail`
> and `corrected_by` and the block's `derived_at_sha` / `derived_by` moved
> (`26c67788` → `a35c9f9b`); the other five rows are byte-unchanged.
> `check_gate_a_provenance.py` exits **0** at `d9f034f0` (6 rows). **Verdict
> stays fail** — MISO reads NOT-YET at ISO level and is absent from `complete`;
> only the stamp moved, exactly as the dispatch said it would.
>
> **Two things the dispatch's job-0 shape would have done that the desk's
> re-key did not — recorded, NOT repaired:** (i) `corrected_by` names the capx
> desk, not this lane, and does not carry the "R-T miss #8" label the dispatch
> asked for (the desk's *own* wording, "eighth promoter miss since R-T", carries
> the same count); (ii) the MISO row's **`read_live_at` leaf still reads
> `2b0b8796`** — the 2026-09-03 refresh-#32 pin — while the same row's
> `corrected_by` says *"at origin/main a35c9f9b"* and the block's
> `derived_at_sha` is `a35c9f9b`. The guard does not read `read_live_at`
> (identity + marker only), so it cannot catch this. A leaf-level
> inconsistency inside one row, one edit away; **routed to the capx desk**,
> which owns the standing duty and this file. `program-status.json` is
> **untouched by this lane** — the dispatch licensed job 0 only when the stamp
> was stale, and it was not.
>
> ### 🟠 SEVEN GATES — **SIX EXIT 0, ONE EXIT 1**, AND THE ONE IS NOT THE ONE THE DISPATCH NAMED
>
> Each script invoked alone under `uv run --frozen`, `$?` read immediately,
> never through a pipe:
>
> | gate script | exit | reading at `d9f034f0` | vs dispatch record (`a35c9f9b`) |
> |---|---|---|---|
> | `audit_keepers.py --check` | 🟢 0 | PASS 0/0 — six keepers + holdout/marker/status | unchanged |
> | `check_registry_payload_parity.py` | 🔴 **1** | **ONE** dir unmapped: `results/calibration/caiso246_b1_spot_coverage` (3 tracked files) | **RE-REDDENED** (parity was clear at `a35c9f9b`) |
> | `check_gate_a_provenance.py` | 🟢 0 | 6 rows, identity + marker match | **0, was 1** — job 0 done by the capx desk |
> | `check_mechanism_matrix.py` | 🟢 0 | 195 field + 49 row + 164 path anchors, 6 shards, stamps + §5.x headers match | unchanged |
> | `check_forecast_staleness.py` | 🟢 0 | **Δ = (unknown)** — newest scored sha `b4ded0bba29c` unreachable; 3 WARNs; **25 of 90** undated | 75 → **90** verdict stamps, Δ **0 → unknown** |
> | `check_bench_freshness.py` | 🟢 0 | 20 parts, **0 STALE**, 20 engine-drift (12 engine commits; NYISO's 3 parts 8) | 9 → **12** engine commits |
> | `check_golden_manifest.py` | 🟢 0 | **45** manifests, **82** entries (**18** enforced / 64 legacy), **3 stale** | 42/75/11 → 45/82/18; stale count unchanged |
>
> **The parity red is a NEW mid-solve checkpoint, not a return of the old one.**
> `caiso246_b1_spot_coverage` landed in `25abe52` (*"caiso-246 B1: checkpoint
> 2023 hourly sidecars (mid-solve)"*, merged #4737 at 00:02:55Z) from the live
> CAISO lane, whose branch `claude/caiso-244-backcast-calibration-jag23e` is
> still on `origin`. Same class as `caiso243_b1_f923_fallback_guard` at v25/v26,
> which cleared **by registration** when its lane finished. Expected to clear the
> same way; **it is the CAISO lane's promotion-duty item, not this board's** —
> but it is one of the three reds now holding the flip set (below).
>
> ### 🔴 STALENESS Δ IS UNKNOWN FOR A NEW REASON — TWO PROVENANCE STAMPS POINT AT COMMITS THAT WERE **REBASED AWAY BEFORE MERGE**
>
> FR-21 reports *"newest scored sha `b4ded0bba29c` … not reachable in this
> checkout (shallow clone, or scored on an unmerged branch)"*. **It is neither.**
> This lane deepened the blobless clone from 275 to **2,643** commits
> (`git fetch --deepen=400`, trees only, per the fast-clone traps) and both shas
> stay unresolvable. Traced: `b4ded0bba29c` is
> `ff-verdicts.json → nyiso-t1h-d52-curveon → provenance.scored_at_sha`, and the
> fresher hindcast-sidecar sha `ec3e4371e92a` is the **pre-rebase** head of the
> capx-D51 branch — CI run **2424** ran on `ec3e4371` and the same commit is
> `689972d` on `main`; the D52 lane's own `cf8f96c` is titled *"record the
> rebase onto f65efaf"*. **Both lanes rebased after scoring and before merge, so
> the stamps name commits that no longer exist anywhere.** Consequence: the
> staleness gate falls to its fail-closed WARN (Δ unknown ≠ fresh), and a
> reproducer cannot check out "the sha this was scored at". This is L-10's
> `ff-verdicts.json` provenance defect in a **new form — an orphaned stamp, not
> a missing one** — and it is a process seam (rebase-before-merge) rather than
> a scorer bug. **Routed to the capx director under X-6b**, which already owns
> the undated-stamp half of this file.
>
> ### 🔴 CI AT TIP — **THE DISPATCH's RED IS FIXED, AND THE FLIP SET STILL FELL TO 3 OF 6.** BOTH HALVES MEASURED
>
> The dispatch recorded (f): *Fast test tier red on
> `tests/curation/test_data_dictionary_sync.py` (capx D48, `7bf91932`, #4707),
> reproduced locally; Ruff green.* **At `d9f034f0`, neither clause holds.**
>
> - **The data-dictionary red is FIXED** — by **capx D52 `0c51723`** (*"re-render
>   the data dictionary"*, merged #4730 at 23:55Z). Reproduced locally:
>   `test_data_dictionary_sync.py` → **5 passed, 142 subtests passed, exit 0**.
>   The routing to the capx director was right and is discharged by the desk's
>   own next lane.
> - **Ruff format is RED**: `tests/unit/model/test_capacity.py` ("1 file would be
>   reformatted, 1376 already formatted"; lint itself passes). Last touched by
>   **capx D52 `2f12544`** (22:58Z) after **capx D51 `1dd567a`** (22:48Z), both
>   merged. Reproduced locally, `ruff format --check .` exit **1**.
> - **The Fast tier is RED ON A DIFFERENT TEST**:
>   `tests/curation/test_clean_io.py::TestRegenerateEntrypoint::test_datatype_list_matches_schemas`
>   — **1 failed / 7,954 passed / 34 skipped / 2 xfailed, 379 s** at run 2430.
>   `scripts/regenerate_clean.py` `DATATYPES` carries `ra-import-allocations`
>   (the **caiso-245 intake `bebd5d3`**, 22:36Z, merged #4737) and the test's own
>   hand-maintained roster `ALL_DATATYPES` (`test_clean_io.py:38`) does not.
>   Reproduced locally, exit **1**.
>
> Measured job-by-job at run **2430** (`33931797640`, head `b2c6c9b8` — the
> newest CI-covered head whose content is in `main`, via #4729):
>
> | required check (R-AE) | run 2387 (v26) | run 2430 (here) | cause |
> |---|---|---|---|
> | `Ruff lint + format` | 🟢 success | 🔴 **failure — MOVED** | format, `test_capacity.py` (capx D51/D52) |
> | `Pinned default cache key` | 🟢 success | 🟢 success | |
> | `Structural refactor guards` | 🟢 success | 🟢 success | |
> | `Cache-key registration guard` | 🟢 success | 🟢 success | |
> | `Fast test tier` | 🟢 success | 🔴 **failure — MOVED** | `test_clean_io` datatype roster (caiso-245 intake) |
> | `Rule-22 quarantine gates` | 🔴 failure (E11) | 🔴 **failure — new subject** | `check_registry_payload_parity` on `caiso246_b1_spot_coverage`; `check_golden_manifest` step **skipped** (Z-2 short-circuit, still) |
>
> **5 of 6 → 3 of 6.** Every one of the three reds is an in-flight lane's loose
> end (capx D51/D52 format; caiso-245 intake roster; caiso-246 checkpoint) and
> none is a model defect. **The flip is NOT live**: all 14 PRs in the window
> merged through runs concluding `failure` — runs **2406–2430 are 25 for 25
> `failure`**, extending v26's 15-for-15. R-AE's precondition (Y-4 merged) has
> been met since 2026-09-04 08:26 PT; **Y-1 remains the owner's action**, and
> this cycle is the clearest case yet for it: with the flip live, the three reds
> above could not have merged, and the lanes that own them would have fixed them
> on their own PRs.
>
> **Z-1 EXTENDED, SECOND TIME.** v26 named the promotion-duty class as four
> duties; the dispatch extended it to a third class, data-dictionary sync. This
> window shows the class is **intake-schema companions**, plural: a new
> `*.schema.yaml` owes (a) the dictionary re-render (D48's miss, fixed by D52)
> **and** (b) the regenerate-entrypoint roster (caiso-245's miss, open). Two
> consecutive fast-tier reds from two different intakes on two different
> companion surfaces, inside 26 hours.
>
> ### 🔴 FOUR-INSTRUMENT ALIGNMENT **BROKEN AT NYISO — CONFIRMED, ON SUBSTANCE**, EXACTLY AS THE DISPATCH RECORDED
>
> | instrument | membership at `d9f034f0` | source |
> |---|---|---|
> | `frontier` in `keepers/<ISO>.json` | **{ERCOT `2026-08-31`, PJM `2026-07-31`, NEISO `2026-07-11`}** — CAISO/MISO no key; **NYISO declared `2026-08-23`, `withdrawn` `2026-08-30` ⇒ ABSENT** | keeper shards |
> | `complete` marker | **{ERCOT, NEISO, PJM}** | `calibration-complete.json` (byte-unchanged in the window) |
> | gate-(a) `status: pass` | **{ERCOT, NEISO, PJM}** — guard exit 0, 6 rows | `program-status.json` |
> | **ISO-level** determination `CALIBRATED` | **{ERCOT, NEISO, PJM, NYISO}** | `status/<ISO>.js` |
>
> Full ISO-level read: **ERCOT CALIBRATED** (`iso_determination`; registered
> run-level NOT-YET preserved beside it) **· PJM CALIBRATED · NEISO CALIBRATED ·
> NYISO CALIBRATED · CAISO NOT-YET · MISO NOT-YET.** **Run-level, re-derived on
> demand** (`calibration_verdict.py --run-id 2026-09-04-nyiso-188-combined`,
> exit 0): **CALIBRATION DETERMINATION: CALIBRATED**, C3c the lone ledgered
> caveat under the rubric v3.3 standing rule (>$300 RT hours: 2023 model 3 h vs
> actual 10 h; 2024 0 vs 13; 2025 4 vs 42). So NYISO reads CALIBRATED at **both**
> levels and is in **none** of the other three instruments. **`final` is EMPTY**;
> **freeze ACTIVE, `scope.tiers = ["locked_test"]`**; **no locked-test year has
> ever been solved, scored or registered for any ISO.** This is the first
> determination-side break, as the dispatch said; the two prior breaks were
> instrument-side. **Keeper motion in the window: NONE** — `keepers/` untouched,
> the first zero-motion cycle since v22. **R-V freeze INTACT.**
>
> ### 🔴 Z-4 — THE SPLIT WAS RULED **TWICE**, BY TWO DESKS, 58 MINUTES APART — AND THE FIRST RULING IS RECORDED NOWHERE
>
> **Q-4 sweep result, and the one that matters.** `R-AG` returns **zero files
> in `docs/`** (word-boundary grep). Owner ruling R-AG (the 22:20Z sitting:
> route the NYISO `complete` re-declaration question to the **calibration
> director** for a recommendation; the audit board records the split as a real
> state with its cause; **no marker edit by any audit lane**) exists only in
> this lane's dispatch. **This entry is its first record** — the identical
> finding shape to R-AF at v26, one cycle later.
>
> **And it was overtaken within the hour, from the other direction.** The
> **capx director desk**, r#35 **amendment 1** (`ef3de28`, 2026-09-04
> **23:18:49Z**, merged #4736 at 23:56Z), records owner ruling **Q38** on its
> card **C-9**: *"RE-DECLARE NOW via a records lane — D56 ISSUED."* The pack's
> §D56 charters a Fable governance-records lane to restore `complete.NYISO` on
> `2026-09-04-nyiso-188-combined` (determination re-verified artifact-only, the
> withdrawn block nested whole beneath, `audit_keepers` M1 PASS, gate-(a) NYISO
> FAIL → PASS, board headline rewritten, **`frontier_basis` = NONE CLAIMED**).
> The capx desk's own protocol — *"before serving any card, grep the audit
> board's ruling ledger (R-series) for card-adjacent rulings"* (its ledger,
> adopted from this board's Q-4) — **could not have found R-AG, because R-AG was
> never written down.** So: two owner acts on one question, one routing it for
> a recommendation, the other issuing the execution, neither citing the other.
> **This lane adjudicates nothing between them** — both are the owner's; the
> record is that they coexist and that the records gap is the cause.
>
> Three facts a reader needs, all measured: (1) **D56 has NOT launched** — no
> `claude/capx-d56-*` head on `origin` at either poll (heads: `main`, the
> caiso-244 lane, and — appearing between polls — `claude/caiso-backcast-calibration-wh2iqt`);
> Z-3 expiry attached. (2) **The marker is byte-unchanged** across the window;
> the split stands exactly as the dispatch recorded it. (3) **D56 as chartered
> re-splits the instruments on a different leg**: it flips `complete`, gate-(a)
> and (already) determination to {ERCOT, NEISO, PJM, **NYISO**} while leaving
> `frontier` at three by its own *NONE CLAIMED* clause — the frontier instrument
> would then be the odd one out. Whether the four-instrument test should read
> `frontier` as optional, or whether D56 should carry a frontier ruling, is a
> **director question, raised here before D56 runs** rather than found after.
>
> ### 🟢 R-T — **NO PROMOTION IN THE WINDOW; TALLY UNCHANGED AT 8 MISSES / 4 COMPLIANT**
>
> `git log a35c9f9b..d9f034f0 -- frontend/data/forecast/program-status.json`
> returns **two** commits: `1cbaad9` (the capx desk's job-0 re-key, above) and
> `9ea01d2` (the capx D51 records rider — `t1f_provenance` stubs, the NEISO
> golden repointed to GOLDEN-3, a `d51_records_rider` block; no gate-(a) row
> touched). **No promoting commit** in the window (`keepers/` and
> `status/` untouched), so R-T's miss #8 (miso-210, `bf8cfb15`) is repaired and
> the tally does not move. Moot on the flip, as before.
>
> ### 🟠 STAGE-0 **4 OF 7** — UNCHANGED; ALL THREE STALE ENTRIES NOW ON R-AF's 48-HOUR LIMB
>
> `check_golden_manifest` at `d9f034f0`: CAISO golden `caiso-231-b1-ungrounded`
> **STALE** vs live `caiso-243-b1-f923`; MISO `miso-198-oomlevel` **STALE** vs
> `miso-210-clock`; NYISO `nyiso-186-astoria-identity` **STALE** vs
> `nyiso-188-combined` (the R-AF re-capture landed against 186 and was two
> promotions stale within ~2 h — its lane's own finding, #4721). Current =
> {ERCOT, ERCOT\_\_carveout-2023, NEISO, PJM}. Per the director's ruling (e),
> NYISO joins CAISO and MISO on the 48-hour limb. **The clocks, read from the
> promoting commits**: caiso-243 `4163d4a5` 2026-09-04 08:24Z; nyiso-188
> `2cc95aa2` 16:30Z; miso-210 `bf8cfb15` 17:27Z — so, if the limb is 48 h of
> keeper stability as the v26 entry read it, the three captures fall due
> **2026-09-06 08:24Z / 16:30Z / 17:27Z** absent a further promotion. *(R-AF's
> own text is still recorded only via the v26 transcription; the limb's exact
> wording is not on the record and the clock above is this lane's reading of
> it.)*
>
> ### 🟠 THE OTHER DISPATCHES — v27 LAUNCHED (THIS), PERF-B s3 **NOT LAUNCHED**, D56 **NOT LAUNCHED**
>
> The dispatch (g) recorded v27 and PERF-B s3 as non-launches at the 22:20Z
> sitting, re-issued whole under R-S. At `d9f034f0`: **v27 is launched** — this
> branch, this entry — so the sitting's classification inverted within ~2 h,
> **Z-3's fourth proof**. **PERF-B s3: NOT LAUNCHED** — no branch, no PR
> (`list_pull_requests state=open` → **zero** open PRs in the repository at
> 00:1xZ), and no session-3 charter under `docs/` (the s2 charter
> `perfb-session2-markup-charter-2026-09.md` is the newest). **D56: NOT
> LAUNCHED** (above). Both carry Z-3's expiry; neither is yet late on a same-day
> issue, so **G-14's tally gains nothing this cycle**.
>
> **Other Q-4 results, all clean:** `R-AF` now resolves to **5** files (the
> re-capture finding, the capx ledger/pack, board + plan) — v26's gap is closed;
> `Q38` / `D56` resolve to the three capx-director files; `Z-4` returns only
> this entry (minted here, as expected); `R-AE`, `R-AD`, `Z-1…Z-3`, `X-2…X-6`,
> `Y-1…Y-5`, `R-S`, `R-T`, `R-V`, `R-X`, `R-Y`, `R-Z`, `R-AB`, `R-AC`, `G-14`,
> `Q34`, `D-5(b)` all resolve to real references. *(Hygiene note carried
> forward: `Y-1`, `Y-3`, `X-2`, `X-3`, `G-14` also hit other programmes' item
> labels — the capacity-economics plan, the retirement-calibration plan, the
> wave-manager review — so a bare label count is not a reference count for
> those five.)*
>
> ### QUEUE v27
>
> | item | state at `d9f034f0` |
> |---|---|
> | **X-2** | 4/7; **all three on the 48 h limb** — CAISO due 09-06 08:24Z, NYISO 16:30Z, MISO 17:27Z (this lane's reading of the limb; R-AF's text unrecorded) |
> | **X-3** | PERF-B s3 **NOT LAUNCHED** (re-issued 22:20Z under R-S; Z-3 expiry) |
> | **X-4** | per its finding (`FINDING-perfb-s2-markup-attribution-2026-09.md`) |
> | **X-5** | unchanged |
> | **X-6** | routed unchanged; **X-6b widened**: two provenance stamps (`b4ded0bb`, `ec3e4371`) name rebased-away commits — FR-21 Δ unknown |
> | **Y-1** | owner flip pending, precondition met; **flip set 3 of 6** (Ruff format · Fast tier · Rule-22), all three other lanes' loose ends |
> | **Y-2** | G2 sitting after the flip |
> | **Y-3** | R-T **8 / 4**, unchanged — no promotion in the window; job 0 discharged by the capx desk (`1cbaad9`); MISO row `read_live_at` leaf stale, routed to the desk |
> | **Y-4** | RETIRED |
> | **Y-5** | (i) E11 gone (nyiso-188 declared its recipe); (ii) parity red is a NEW checkpoint (`caiso246_b1_spot_coverage`), CAISO lane's |
> | **Z-1** | **EXTENDED AGAIN** — intake-schema companions are a class of TWO surfaces (dictionary render + regenerate roster); two consecutive fast-tier reds from two intakes |
> | **Z-2** | unchanged; 25-for-25 `failure` conclusions (2406–2430); quarantine-gates short-circuit still skips `check_golden_manifest` |
> | **Z-3** | applied; **fourth inversion** (v27 itself) |
> | **Z-4** | **NEW, and already double-ruled**: R-AG (22:20Z, calibration-director recommendation; unrecorded until here) and Q38 (23:18Z, D56 re-declare now); D56 not launched; marker unchanged; **D56's `frontier_basis` NONE CLAIMED would leave the frontier leg split** — director question |
> | **R-AG** | **UNRECORDED until this entry** |
>
> **Records integrity:** touched **only** this board and the plan. **Verified
> untouched** (`git status --porcelain` empty at session start after
> `reset --hard origin/main`; closing diff confined to two files): every keeper
> shard, every `status/<ISO>.js`, `calibration-complete.json`,
> `holdout-freeze.json`, **`program-status.json`** (job 0 skipped — already
> current), every matrix shard, every workflow, every bundle / sidecar /
> registry file, every golden manifest. **No solve, no score, no registration.**
> *(Method note: the clone was deepened, trees only, to test the FR-21
> reachability claim — a read-side git operation, no working-tree change.)*
>
> ### 🟢 POST-CLOSE CODA AT `3cdf1cac` — THE PARITY RED WAS A **21-MINUTE TRANSIENT**, AND THE PIN MOVED ONE COMMIT AFTER POLL 2
>
> Between poll 2 (00:20Z) and the push, `origin/main` advanced **one merge**:
> `3cdf1cac`, **#4739** at **00:23:37Z** (`20a47b55`, *"caiso-246: drop the
> prior session's partial 2023 sidecars before the fresh three-year B1 solve"*),
> from the new `claude/caiso-backcast-calibration-wh2iqt` head that appeared
> between the polls. It **deletes exactly the three tracked files** of
> `results/calibration/caiso246_b1_spot_coverage` and touches nothing else —
> no keeper shard, marker, status file, freeze file, matrix shard, workflow or
> records file. This lane rebased onto it and re-ran the two gates it can move:
> `check_registry_payload_parity.py` → **exit 0** (65 runs, 106 dirs, 0
> tolerated); `check_golden_manifest.py` → **exit 0**. **So at `3cdf1cac` all
> seven gates exit 0** (the other five re-derived on surfaces the commit did
> not touch). The parity red above stood from 00:02:55Z to 00:23:37Z — cleared
> by **deletion** this time, not registration, because the checkpoint was the
> prior session's partial output. **Y-5(ii) is discharged**, and the R-AE flip
> set at the next CI-covered head should read **4 of 6** (Ruff format and the
> Fast tier still red on the D51/D52 and caiso-245 loose ends; Rule-22's
> `check_golden_manifest` step will finally run once parity passes). Everything
> else in this entry is unchanged by the coda and stands at `d9f034f0`. **Z-3
> generalised**: a gate red carries an expiry too.

> # 🟢 v26 (2026-09-04, pin `8a18e9e1`) — **Y-4 LANDED. THE PATH-FILTER TRAP IS CLOSED — AND IT HAS ALREADY FIRED ON A RECORDS PR. THE FLIP SET IS 5 OF 6, ONE KEEPER-RECIPE DECLARATION FROM DONE. AND R-AF IS RECORDED NOWHERE.**
>
> **THE PIN MOVED UNDER THIS DISPATCH FOR THE THIRD CONSECUTIVE CYCLE — AND A
> SECOND v25 LANE HAD ALREADY LANDED.** The director pinned `b168260e`;
> `origin/main` was **`8a18e9e1`** at first poll and **stable across three**
> (08:2x, 08:3x, 08:4x). The window `b168260e..8a18e9e1` is **70 commits**.
> ⚠️ **A records lane at pin `a8464861` had already written v25 and merged it**
> (#4689, `78b0eec2`, inside my window). **This lane is therefore v26, not a
> second v25** — v25 is retained verbatim below as history, and *nothing in it
> is corrected*: every v25 figure re-derives correctly **at v25's own pin**.
> What follows is what moved in `a8464861..8a18e9e1`.
>
> ### 🟢 BOARD Y-4 — **LAUNCHED, AND TWO THIRDS MERGED.** v25's "NOT LAUNCHED ACROSS THREE POLLS" WAS TRUE WHEN TAKEN AND IS NOW SUPERSEDED
>
> v25 recorded Y-4 as a non-launch on three polls and took **G-14's tally to
> SIX**. Within the hour it launched. Measured, not inferred — branch, PR and
> merge all located:
>
> | Y-4 duty | state at `8a18e9e1` | evidence |
> |---|---|---|
> | CAISO gate-(a) stamp re-key | 🟢 DISCHARGED (pre-Y-4) | `26d35d0e`, capx director, owner ruling Q34 — as v25 found |
> | `caiso_ct_peaker_committed_measured` registry row | 🟢 **DISCHARGED** | **job 2, `f4f17249`**, merged #4688 (`69194725`); row live at `forecast_parity_registry.py:557`, disposition **GAP** on the R-X route |
> | path-filter remedy | 🟢 **DISCHARGED** | **job 3, `d94a6423`**, same merge — the **narrow widening**, not a passthrough workflow |
> | lane finding | 🟠 **IN FLIGHT** | job 4, `4ca5fa3f`, on `claude/y4-caiso241-duties-nvcroc` (head `b010eaa1`), **PR #4694 open**, CI runs 2391/2392 in progress |
>
> **This is the third time in three cycles that "no branch" proved to be a
> snapshot** (R-X, R-Y at v24; Y-4 here). Lesson (i) is now load-bearing, and
> **the inversion v25 flagged is confirmed in the other direction**: v24 used the
> re-poll to upgrade a non-launch to IN FLIGHT and was right; v25 used it to
> confirm a non-launch and was right *at its pin* and wrong within the hour. The
> discipline is **re-poll before classifying**, and **a non-launch classification
> carries an expiry**, which no prior record stated. Recorded as **board Z-3**.
>
> ### 🔴 THE DISPATCH'S CLOSING INSTRUCTION IS FALSE AT THIS PIN — AND THERE IS A RECEIPT
>
> The dispatch closes: *"Your PR is docs-only, so ci.yml will not run on it; the
> flip has not happened; say so in the PR body."* **The first clause no longer
> holds.** Y-4 job 3 widened `ci.yml`'s `pull_request.paths` (lines **69–94**),
> and the three paths enrolled are exactly this lane's shape:
>
> ```
> - "docs/handoffs/audit-program-director-board-2026-08.md"
> - "docs/model-audit-release-plan-2026-08.md"
> - "docs/FINDING-*.md"
> ```
>
> **Both files this lane may touch are on that list. CI runs on this PR.** This
> is not a prediction — **v25's own records-only PR already proved it**: run
> **2385** (`33853215685`, head `78b0eec2`, two docs files and nothing else)
> **ran all ten CI jobs and concluded `failure`.** Per the protocol's
> *a-dispatch-may-not-upgrade-a-lane's-claim* clause, **the record governs and
> the dispatch's clause is superseded** — stated here and in the PR body. The
> second clause (*the flip has not happened*) **is confirmed**: no branch
> protection is asserted anywhere in the repo, and R-AE's set is not yet green.
>
> ### 🟢 R-AE's SIX-CHECK FLIP SET — **5 OF 6**, UP FROM v25's 4 OF 6. THE FAST TIER WENT GREEN
>
> Measured job-by-job at run **2387** (`33853323644`, head `87e3afc0` — the
> newest CI-covered head whose content is in `main`):
>
> | required check (R-AE) | run 2381 (v25) | run 2387 (here) |
> |---|---|---|
> | `Ruff lint + format` | 🟢 success | 🟢 success |
> | `Pinned default cache key` | 🟢 success | 🟢 success |
> | `Structural refactor guards` | 🟢 success | 🟢 success |
> | `Cache-key registration guard` | 🟢 success | 🟢 success |
> | **`Fast test tier`** | 🔴 failure | 🟢 **success — MOVED** |
> | **`Rule-22 quarantine gates`** | 🔴 failure | 🔴 **failure — the sole blocker** |
>
> Both of v24's fast-tier failures are gone. Re-run locally at this pin, exit
> code captured directly: `test_forecast_parity.py` + `test_gate_a_provenance.py`
> → **34 passed, 1 xfailed, exit 0**. **The flip is one keeper-recipe
> declaration away** — the nyiso-185 **E11**, which belongs to the NYISO lane.
>
> ### 🟠 SEVEN GATES — **FIVE EXIT 0, TWO EXIT 1.** COUNT UNCHANGED, ONE SUBJECT HALVED
>
> Each script invoked alone, `$?` read immediately, **never through a pipe**:
>
> | gate script | exit | reading at `8a18e9e1` | vs v25 |
> |---|---|---|---|
> | `audit_keepers.py --check` | 🔴 **1** | FAIL 1/0 — NYISO `2026-09-04-nyiso-185-family-hr` **E11** | unchanged |
> | `check_registry_payload_parity.py` | 🔴 **1** | **ONE** dir unmapped: `nyiso185_control` (17 tracked files) | **HALVED** |
> | `check_gate_a_provenance.py` | 🟢 0 | 6 rows, identity + marker match | unchanged |
> | `check_mechanism_matrix.py` | 🟢 0 | 195 field + 49 row + 164 path anchors, 6 shards, stamps match | unchanged |
> | `check_forecast_staleness.py` | 🟢 0 | Δ = 0; 2 WARNs (**25 of 75** verdicts undated) | 74 → **75** |
> | `check_bench_freshness.py` | 🟢 0 | 20 parts, **0 STALE**, 20 engine-drift (9 engine commits) | unchanged |
> | `check_golden_manifest.py` | 🟢 0 | 42 manifests, 75 entries (11 enforced), **3 stale** | unchanged |
>
> **The parity red halved by REGISTRATION, not by pruning.**
> `caiso243_b1_f923_fallback_guard` (18 tracked files) now maps to sidecar
> `registry/2026-09-04-caiso-243-b1-f923.json` — the caiso-243 promotion
> registered the bundle it had checkpointed mid-solve. `nyiso185_control`
> remains, still committed deliberately as a *"bit-identity instrument, not
> registered"*. **Y-5(ii) is half-discharged; the NYISO half stands.**
>
> ### 🔴 A CORRECTION AGAINST INTEREST — "LEG 2 IS ONE REGISTRY ROW FROM GREEN" IS TRUE OF THE *TEST*, NOT OF THE *GATE*
>
> v25 wrote *"Leg 2 is ONE registry row from green"*; Y-4 job 4's own commit
> message reports *"0 registry failures, CAISO off the unaccounted list, filed
> gaps 12 → 13"*. **Both are literally true and neither is the gate's verdict.**
> Measured from run 2381's job log against this pin's local run:
>
> | | run 2381 (v25's pin) | `8a18e9e1` (here) |
> |---|---|---|
> | `check_forecast_parity.py` exit | 🔴 1 | 🔴 **1 — still red** |
> | unaccounted | **3** | **2** |
> | filed gaps | 12 | 13 |
> | FAIL rows | ERCOT · **CAISO** · NYISO | ERCOT · NYISO |
>
> The two survivors — ERCOT `ercot_storage_as_soc_reserve`, NYISO
> `nyiso_seam_deliverability_envelope` — **predate this cycle and are nobody's
> promotion duty**. `0 registry failure(s)` is a *different counter* in the same
> summary line from `unaccounted`, and quoting it reads as a discharge it is not.
>
> **The two instruments disagree BY DESIGN, and the test says so out loud.**
> `tests/scoring/test_forecast_parity.py` carries a declared frozenset
> `_FR22_OPEN_UNACCOUNTED` naming exactly those two, and asserts on the **subset**
> (*"a forecast lane clearing one of the open two must not red this test on its
> way out"*); the companion `test_check_exits_zero_on_the_current_keepers` is
> `@pytest.mark.xfail(strict=True)` **mirroring the FR-22 job's red**, with
> `strict=True` so the marker cannot rot. So: **the pytest is a regression gate on
> NEW misses; the FR-22 job is the standing red on the open two.** Neither is
> lying. **The consequence for R-AE is that its six-check set is CORRECTLY scoped
> and must stay so** — `FR-22 backcast→forecast parity` can never go green until a
> forecast-program lane acts, so adding it to a required set would deadlock every
> PR in the repo. Confirmed against the evidence, not assumed.
>
> ### 🔴 Z-2, THE OTHER HALF — CI's RUN CONCLUSION *OVER*-STATES THE FLIP-RELEVANT STATE
>
> v25 established that CI **under**-reports the gate ledger (the quarantine-gates
> job short-circuits after `audit_keepers`, so steps 6/7/8 read `skipped` — still
> true at run 2387). The complementary half is now measured: **every completed CI
> run in the visible window is `failure` — 2369, 2370, 2371, 2372, 2373, 2374,
> 2375, 2376, 2377, 2378, 2379, 2380, 2385, 2386, 2387: fifteen for fifteen.**
> Yet 5 of R-AE's 6 are green. The overall conclusion is dominated by **two
> chronically-red jobs that sit OUTSIDE the flip set** — `FR-22 backcast→forecast
> parity` (by design, above) and `Forecast-invariant artifact audit`.
> **So neither the run conclusion NOR the job summary substitutes for the gate
> sweep: one under-reports, the other over-reports.** Z-2 is extended to say both.
>
> *(Method note, recorded because it nearly produced a false figure: run bare,
> `check_forecast_invariants.py` exits **1 on `ModuleNotFoundError: numpy`** —
> an exit code that is not a verdict. Under `uv run --frozen` it exits 1 on its
> real finding: ~10 forecast-namespace runs whose invariant FAILs are undeclared
> in `invariant-failures.json`. **An exit code is only evidence once you have
> read the output that produced it.**)*
>
> ### 🟢 R-T ROUTING — **THE NINTH PROMOTION ALSO COMPLIED. TWO CONSECUTIVE, AND THIS ONE WENT 3-FOR-3**
>
> `git log 49bfbc49..8a18e9e1 -- frontend/data/forecast/program-status.json`
> returns **seven** commits; the promoting commits in the same window are
> `04e1c09c` (caiso-240), `97698fd6` (miso-202), `a6c8db2f` (caiso-241),
> `1fe734bb` (nyiso-185), `4163d4a5` (caiso-243). **Two of the five touch
> `program-status.json` in the promoting commit itself: nyiso-185 (the eighth,
> v25's finding) and `4163d4a5`, caiso-243 — THE NINTH.** Verified from the
> commits' own file lists.
>
> **And caiso-243 is the first promotion to clear the whole promotion-duty class
> at once**, which nyiso-185 did not:
>
> | shared-surface duty | nyiso-185 | caiso-243 |
> |---|---|---|
> | gate-(a) stamp re-key (R-T) | 🟢 | 🟢 |
> | keeper-recipe declaration (`audit_keepers` E11) | 🔴 **created the red** | 🟢 |
> | registry/payload parity (bundle mapped) | 🔴 left `nyiso185_control` | 🟢 registered |
> | FR-22 registry row | n/a (none armed) | 🟢 none armed |
>
> ⚠️ **Still NOT read as self-enforcing, for the same reason v25 gave and one
> more.** Two compliances under a standing owner duty (Q34) are not a mechanism;
> the flip is what makes them one. **But the direction of travel is now real and
> should be recorded as such** — 7 non-compliant, then 2 compliant, the second
> clean on all four duties. **Z-1 is unchanged in substance and strengthened in
> evidence:** the promotion-duty class is **four** duties, all four sit inside
> R-AE's six-check set, and the flip covers all four.
>
> ### 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — RE-DERIVED FAIL-CLOSED
>
> | instrument | membership at `8a18e9e1` | source |
> |---|---|---|
> | `frontier` in `keepers/<ISO>.json` | **{ERCOT `2026-08-31`, PJM `2026-07-31`, NEISO `2026-07-11`}** — CAISO/MISO no key; **NYISO `withdrawn` ⇒ ABSENT** | keeper shards |
> | `complete` marker | **{ERCOT, NEISO, PJM}** | `calibration-complete.json` |
> | gate-(a) `status: pass` | **{ERCOT, NEISO, PJM}** — `check_gate_a_provenance` exit 0, 6 rows | `program-status.json` |
> | **ISO-level** determination `CALIBRATED` | **{ERCOT, NEISO, PJM}** | `status/<ISO>.js` |
>
> Full ISO-level read: **ERCOT CALIBRATED · PJM CALIBRATED · NEISO CALIBRATED ·
> CAISO NOT-YET · MISO NOT-YET · NYISO NOT-YET.** **`final` is EMPTY** (only
> `_note`). **Freeze ACTIVE, `scope.tiers = ["locked_test"]`.** **No locked-test
> year has ever been solved, scored or registered for any ISO.** Dispatch item
> (a)'s instrument clause **confirmed unchanged**.
>
> **RUN-LEVEL vs ISO-LEVEL, named again because the distinction is structural.**
> The fourth instrument above is **ISO-level** (`iso_determination` where a
> partitioned keeper carries one — ERCOT alone — else `determination`, in
> `status/<ISO>.js`). The **run-level** determination remains **not a committed
> artifact anywhere**: it exists only as `calibration_verdict.py --run-id`
> output, produced on demand. v25's finding re-verified, unchanged.
>
> ### 🟠 KEEPER MOTION — **ONE HOP, ONE ISO** (AGAIN), AND R-V HOLDS
>
> Since v25's pin: **CAISO `caiso-241-b1-ctpeaker` → `2026-09-04-caiso-243-b1-f923`**
> (#4686, promoting commit `4163d4a5` — the F923 low-volume fallback repair).
> NYISO stays at `nyiso-185-family-hr`, MISO at `miso-202-unitclip`. **R-V freeze
> INTACT** — `keepers/{ERCOT,NEISO,PJM}.json` untouched across the window.
>
> **Stage-0 is 4 of 7 current — board X-2 count unchanged** (ERCOT,
> ERCOT\_\_carveout-2023, NEISO, PJM CURRENT). **CAISO's stale row re-targets
> again**, `perfb-stage0 [CAISO] 2026-09-01-caiso-231-b1-ungrounded` now stale
> against **caiso-243** (it was caiso-241 one cycle ago, caiso-240 the cycle
> before). NYISO's stands against `nyiso-185-family-hr`, MISO's against
> `miso-202-unitclip`.
>
> ### 🔴 R-AF IS RECORDED NOWHERE IN `docs/` — AND BOTH ITS TRIGGERS HAVE NOW FIRED
>
> **Q-4 sweep result, and the one that matters.** Every board label was grepped
> across `docs/` before closing. `R-AF` returns **exactly one file** —
> `docs/mechanism-testing-matrix.md:7947` — and that hit is a **substring
> collision inside the phrase "SUMME**R-AF**TERNOON"**, not a reference.
> **Ruling R-AF (the stage-0 re-capture policy) appears in neither canonical
> audit file nor anywhere else in the repository.** This lane's v26 entry is its
> first record; it is transcribed in the plan §8 entry alongside this block.
>
> **And it is already overtaken by events on both limbs:**
>
> - **NYISO ("now, 177 held since 09-02")** — the premise **expired**. NYISO
>   promoted to `2026-09-04-nyiso-185-family-hr` on `1fe734bb`, so "177 held" is
>   no longer true and the re-capture target is a **different keeper**. The
>   charter needs re-keying before it can be executed as written.
> - **CAISO ("when their lane's next promotion lands")** — the condition
>   **fired**: caiso-243 landed at `4163d4a5`. CAISO's stage-0 re-capture is now
>   **due on R-AF's own terms**.
> - **MISO** — no promotion since `miso-202-unitclip`; the 48 h limb is the live
>   one.
>
> Other Q-4 results, all clean: `R-AE` and `Z-2` resolve to the plan + board only
> (both minted last cycle, as expected); `X-1…X-6`, `Y-1…Y-4`, `Z-1`, `R-AB`,
> `R-AD`, `R-T`, `R-V`, `R-X`, `R-Y`, `R-Z`, `R-AC`, `G-14`, `Q34`, `D-5(b)` all
> resolve to real references.
>
> ### 🔴 THE OTHER TWO DISPATCHES — **NOT LAUNCHED**, ON THREE POLLS EACH
>
> `origin` carries **four** heads: `main`, `claude/y4-caiso241-duties-nvcroc`,
> `claude/nyiso-186-cc-regular-2024-b16yp7`, and — appearing between poll 1 and
> poll 3 — `claude/capx-d47-golden3-attestation-nrqtyq`. **None is the NYISO
> stage-0 re-capture (R-AF) and none is PERF-B session 2 (X-3).** Classified as
> non-launches **with Z-3's expiry attached**: this is a snapshot at
> `8a18e9e1`, and Y-4 is this very cycle's proof that the classification can
> invert within the hour. **G-14's non-launch tally: v25 took it to SIX and Y-4
> has since retired one of those; this lane adds none — the two open dispatches
> are same-day and not yet late.**
>
> ### QUEUE v26
>
> | item | state at `8a18e9e1` |
> |---|---|
> | **X-1** | RETIRED BY EXECUTION (v25) |
> | **X-2** | 4/7; **CAISO re-capture now DUE under R-AF**; NYISO charter needs re-keying to nyiso-185; MISO on the 48 h limb |
> | **X-3** | PERF-B s2 **NOT LAUNCHED** (3 polls, Z-3 expiry attached) |
> | **X-4** | folded into X-3 |
> | **X-5** | unchanged |
> | **X-6** | ROUTED — X-6a bench (20/20 drift, 9 engine commits) → calibration desk; X-6b (25 of 75 undated) → capx director |
> | **Y-1** | owner flip **5 of 6**, single blocker = nyiso-185 **E11** |
> | **Y-2** | G2 sitting still pending the flip (R-AD unchanged) |
> | **Y-3** | R-T now **7 non-compliant / 2 compliant**; record only, moot on flip |
> | **Y-4** | **DISCHARGED on jobs 2+3** (#4688); job 4 IN FLIGHT (PR #4694) |
> | **Y-5** | (i) E11 **stands** — the flip's sole blocker; (ii) **half-discharged**, `nyiso185_control` alone remains |
> | **Z-1** | unchanged in substance, **strengthened**: the class is FOUR duties, all inside R-AE's six |
> | **Z-2** | **EXTENDED** — CI under-reports (job short-circuit) *and* over-reports (run conclusion); 15-for-15 `failure` against 5-of-6 green |
> | **Z-3 NEW** | a non-launch classification **carries an expiry**; three cycles running, "no branch" inverted within the hour |
> | **R-AF** | **UNRECORDED until this entry**; NYISO limb's premise expired, CAISO limb fired |
>
> **Records integrity:** touched **only** this board and the plan. **Verified
> untouched** (`git status --porcelain` empty at session start; diff confined to
> two files at close): every keeper shard, every `status/<ISO>.js`,
> `calibration-complete.json`, `holdout-freeze.json`, `program-status.json`,
> every matrix shard, every workflow, every bundle / sidecar / registry file,
> every golden manifest. **No solve, no score, no registration.**

> # 🟠 v25 (2026-09-04, pin `a8464861`) — **THE GATE LEDGER MOVED IN BOTH DIRECTIONS: gate-(a) IS REPAIRED, TWO OTHER GATES WENT RED. THE FAST TIER IS DOWN TO *ONE* FAILURE. AND THE R-T PATTERN BROKE AT EIGHT — WITHOUT THE FLIP.**
>
> **THE PIN MOVED UNDER THIS DISPATCH, AGAIN — AND THEN AGAIN MID-SESSION.** The
> director pinned `b168260e` (#4671); `origin/main` was already **`a8464861`**
> (#4684) at this lane's first poll and stable across two. The window
> `b168260e..a8464861` is **42 commits / 6 merged PRs**. Every figure below is
> re-derived at **`a8464861`**, and each place the dispatch's RECORD moved is
> named. ⚠️ **A third poll, taken later in the session for the Y-4 branch check,
> found main at `0227ffb1`.** The pin is NOT moved: protocol says pin once, and
> the drift window `a8464861..0227ffb1` (2 commits, #4685) touches **three capx
> handoff docs and nothing else** — no keeper shard, no `program-status.json`, no
> gate input, no bundle, no workflow, no source file. **Not one figure in this
> record moves at `0227ffb1`**, and that is measured (`git diff --stat`), not
> assumed.
>
> ### 🟠 SEVEN GATES — **FIVE EXIT 0, TWO EXIT 1.** THE DISPATCH's ITEM (a) HOLDS ON ITS *SUBJECT* AND FAILS ON ITS *COUNT*
>
> The dispatch records *"six exit 0, `check_gate_a_provenance` exit 1 (CAISO cites
> caiso-240, live keeper caiso-241) — v24's reading confirmed at `b168260e`."*
> **Re-measured, and the ledger inverted on three of seven rows.** Each script
> invoked alone, `$?` read immediately, **never through a pipe**:
>
> | gate script | exit | reading at `a8464861` | vs dispatch |
> |---|---|---|---|
> | `audit_keepers.py --check` | 🔴 **1** | **FAIL 1/0 — NYISO keeper `2026-09-04-nyiso-185-family-hr` E11** | **NEW RED** |
> | `check_registry_payload_parity.py` | 🔴 **1** | **two tracked bundle dirs map to no retained sidecar** | **NEW RED** |
> | `check_gate_a_provenance.py` | 🟢 **0** | 6 rows checked, identity + marker match | **REPAIRED** |
> | `check_mechanism_matrix.py` | **0** | 195 field + 49 row + 164 path anchors, 6 ISO shards, keeper stamps match | unchanged |
> | `check_forecast_staleness.py` | **0** | Δ = 0; 2 WARNs (25 of 74 verdicts undated) | unchanged |
> | `check_bench_freshness.py` | **0** | 20 parts, **0 STALE**, 20 with engine drift | unchanged |
> | `check_golden_manifest.py` | **0** | 42 manifests, 75 entries (11 enforced), **3 stale vs live keeper** | unchanged |
>
> **The two new reds, named:**
>
> 1. **`audit_keepers` E11** — *"UNDECLARED keeper-recipe change(s) vs former
>    keeper `2026-09-02-nyiso-177-vintage-matched`: `fossil_announced_exits_enabled`
>    (False → True) — the silent-de-arm class"*. Produced by the **nyiso-185
>    promotion** (#4679, `1fe734bb`). The remedy the check itself names: declare it
>    in the shard's promotion prose, or revert it.
> 2. **`check_registry_payload_parity`** — `results/calibration/caiso243_b1_f923_fallback_guard`
>    (introduced `0ff3ab7f`, the caiso-243 mid-solve checkpoint) and
>    `results/calibration/nyiso185_control` (introduced `949adf30`, committed
>    deliberately as a *"bit-identity instrument, not registered"*). **Both are
>    TRACKED and COMMITTED** — verified with `git ls-files` (9 and 17 files) — so
>    this is not a working-tree artifact of this session. Remedy per the gate:
>    register, prune, or record in `KEEP_REQUIRED_UNMAPPED_BUNDLES`.
>
> ### 🔴 AND A STRUCTURAL FINDING THE PROTOCOL's "RUN THE GATES YOURSELF" CLAUSE JUST EARNED
>
> **CI's own reading UNDERSTATES the red count, and the reason is step
> short-circuiting.** At run 2381 the `Rule-22 quarantine gates` job reports
> `failure` on `audit_keepers --check` (step 5) — and steps **6, 7 and 8**
> (`legitimacy_diagnostics`, **`check_registry_payload_parity`**,
> `check_golden_manifest`) all read **`skipped`**. The parity failure exists at
> exactly that content and **CI never measured it.** A reader taking the job
> summary at face value would record one red gate where there are two.
>
> **This is the first cycle in which running the seven scripts locally found
> something the CI job structurally could not report.** It is not a defect in the
> gate — fail-fast is a reasonable job design — but it means **a CI job conclusion
> is not a substitute for the gate sweep**, and any future lane that skips the
> sweep because "CI already ran it" will under-report. Recorded as **board Z-2**.
>
> ### 🟢 FAST TEST TIER — **DOWN FROM TWO FAILURES TO ONE.** ONE OF THE caiso-241 DUTIES IS DISCHARGED
>
> **Run 2381 (`33851504404`, head `6a3aa39f`, the newest CI-covered head; main's
> tip is a docs-only merge past it), `Fast test tier` job `100955123752`
> conclusion `failure` — `1 failed, 7868 passed, 34 skipped, 2 xfailed`,
> 528.18 s.** Against v24's run 2371 (`2 failed, 7846 passed`).
>
> | v24's two failures | state at `a8464861` |
> |---|---|
> | `test_gate_a_provenance.py::test_live_board_passes` | 🟢 **PASSES** — both stale stamps re-keyed |
> | `test_forecast_parity.py::test_all_six_keepers_resolve` | 🔴 **STILL FAILS** — `caiso_ct_peaker_committed_measured` |
>
> The surviving assertion, verbatim from the job log: *"CAISO:
> `['caiso_ct_peaker_committed_measured']` armed in the keeper with no
> forecast-orchestrator consumer and no registry declaration — resolve it or
> declare it in `scripts/lib/forecast_parity_registry.py`"*. Confirmed at the
> source: `grep -n "caiso_ct_peaker" scripts/lib/forecast_parity_registry.py`
> **exits 1, zero hits**. **Leg 2 is ONE registry row from green.**
>
> ### 🔴 R-AE's SIX-CHECK FLIP SET IS **4 OF 6**, NOT 5 OF 6 — A *SECOND* CHECK WENT RED IN THIS WINDOW
>
> R-AE amends R-AB to require the full six. Measured job-by-job at run 2381:
>
> | required check (R-AE) | run 2381 |
> |---|---|
> | `Ruff lint + format` | 🟢 **success** — the amendment's premise, confirmed |
> | `Pinned default cache key` | 🟢 success |
> | `Structural refactor guards` | 🟢 success |
> | `Cache-key registration guard` | 🟢 success |
> | **`Fast test tier`** | 🔴 failure (the one parity row) |
> | **`Rule-22 quarantine gates`** | 🔴 **failure — NEW** (green at 2371 *and* 2374) |
>
> **The dispatch's ruling (e) could not have known this**: it amends R-AB for
> Ruff going green, which is right, but in the same window `Rule-22 quarantine
> gates` went red on the nyiso-185 E11. **The flip set therefore has two reds, not
> one, and both are promotion duties again** — a keeper-recipe declaration and a
> parity registry row. **A DISPATCH MAY NOT UPGRADE A LANE'S CLAIM, and this lane
> does not weaken one either**: R-AE stands as the owner's ruling; what moved is
> the measurement beneath it, taken 42 commits later.
>
> ### 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — RE-DERIVED FAIL-CLOSED
>
> | instrument | membership at `a8464861` |
> |---|---|
> | `frontier` present in `keepers/<ISO>.json` | **{ERCOT, NEISO, PJM}** — CAISO/MISO carry no `frontier` key; **NYISO `withdrawn` ⇒ ABSENT** |
> | `complete` marker | **{ERCOT, NEISO, PJM}** |
> | gate-(a) `status: pass` (`program-status.json`) | **{ERCOT, PJM, NEISO}** |
> | **ISO-level** determination `CALIBRATED` | **{ERCOT, NEISO, PJM}** |
>
> **`final` is EMPTY** (its only key is `_note`). **Freeze ACTIVE with
> `scope.tiers = ["locked_test"]`**, `frozen_operations = [solve, score, dashboard
> registration]`; validation tier (2020/2021/2022) explicitly `not_frozen`,
> governed by the `complete` marker + `--holdout-authorized`. **No locked-test year
> has ever been solved, scored or registered for any ISO.** Dispatch item (b)
> **confirmed unchanged**.
>
> **RUN-LEVEL vs ISO-LEVEL, named as the protocol requires — and the reason they
> cannot be conflated is structural.** The fourth instrument is the **ISO-level**
> determination: `iso_determination` in `frontend/data/backcast/status/<ISO>.js`,
> `build_status.py`'s partition-aware rollup ({CAISO NOT-YET, ERCOT CALIBRATED,
> MISO NOT-YET, NEISO CALIBRATED, NYISO NOT-YET, PJM CALIBRATED}). The
> **run-level** determination is a *different* instrument and **is not a committed
> artifact at all**: the registry sidecar carries **no determination field**
> (`2026-09-04-nyiso-185-family-hr.json` keys are exactly `id, label, date,
> shorthand, definition, years, iso, file, bundle`), and the run payload
> `runs/<id>.js` carries **zero** `determination` keys across all 598,285 bytes.
> Run-level determination exists only as `calibration_verdict.py --run-id` output,
> produced on demand. **This is why v24 had to invoke the verdict scorer to quote
> caiso-241's run-level NOT-YET — there was nothing to read.** The two instruments
> can never be silently swapped by reading a file, because only one of them is in
> a file.
>
> ### 🟠 KEEPER MOTION — **ONE HOP, ONE ISO**, AND R-V HOLDS
>
> Since v24's pin `8d5a3e16`: **NYISO 177 → `2026-09-04-nyiso-185-family-hr`**
> (#4679, promoting commit `1fe734bb`, owner ruling). CAISO stays at
> `caiso-241-b1-ctpeaker`, MISO at `miso-202-unitclip`. **R-V freeze INTACT** —
> `keepers/{ERCOT,NEISO,PJM}.json` blob shas byte-identical at `8d5a3e16` and
> `a8464861` (`e0094771…`, `e8337a42…`, `7154468a…`).
>
> **Stage-0 is 4 of 7 current — board X-2 stands, count unchanged** (ERCOT,
> ERCOT\_\_carveout-2023, NEISO, PJM CURRENT). **Two of the three stale rows
> re-target this cycle:** CAISO's is now stale against `caiso-241-b1-ctpeaker` (the
> dispatch predicted this), and **NYISO's `nyiso-159-loss-surface` is now stale
> against `nyiso-185-family-hr`** — which the dispatch did not, because the
> promotion post-dates it. MISO's stays against `miso-202-unitclip`.
>
> ### 🟢 R-T ROUTING — **THE PATTERN BROKE AT EIGHT, AND IT BROKE WITHOUT THE FLIP**
>
> `git log 49bfbc49..a8464861 -- frontend/data/forecast/program-status.json`
> returns **four** commits — and **one of them IS a promoting commit.**
> **`1fe734bb`, the nyiso-185 promotion, touches `keepers/NYISO.json`,
> `status/NYISO.js` AND `program-status.json` in a single commit** — verified from
> the commit's own file list, not from its message. **R-T count: SEVEN
> non-compliant promotions, then the EIGHTH COMPLIED.**
>
> The dispatch's item (g) records *"Y-3 R-T pattern seven-for-seven, moot on flip,
> record only."* At this pin it is **seven-for-eight**. The other three commits are
> the records-v23 job 0 (`e8bc1990`) and two **director** re-keys (`6ed483df`,
> `26d35d0e`) — the second under the new standing duty (owner ruling **Q34**,
> capx r#33 card C-5).
>
> ⚠️ **This lane does NOT read that as the duty becoming self-enforcing, and says
> so against the temptation.** One compliance is not a mechanism; it followed an
> owner ruling and a director's standing duty, not a structural gate; and
> **nyiso-185 discharged the *stamp* duty while simultaneously creating a NEW
> shared-surface failure** (the E11 recipe-declaration miss above). **The
> promotion-duty class is at least THREE duties, not two** — gate-(a) stamp,
> parity registry row, keeper-recipe declaration — and this promotion went 1-for-2
> on the two it faced. That strengthens board Z-1 rather than weakening it: all
> three duties sit inside R-AE's six-check set, so the flip covers all three.
>
> ### 🔴 board Y-4 — **NOT LAUNCHED**, ACROSS THREE POLLS; AND ONE OF ITS THREE DUTIES WAS DISCHARGED BY A DIFFERENT LANE
>
> The dispatch says *"Record as IN FLIGHT unless you find its branch/PR/merge."*
> **Lesson (h) applied: polled three times, spread across the session.** Polls 1–2:
> `origin` carries **only `refs/heads/main`**. Poll 3: two lane branches appeared
> (`claude/caiso-f923-lowvolume-defect-dnegou`, `claude/nyiso-186-cc-regular-2024-b16yp7`)
> — **neither is Y-4**. `list_branches` at `perPage: 100` agrees. **No Y-4 branch,
> no PR, no merge. G-14's non-launch tally goes to SIX.**
>
> **But Y-4's three duties have NOT moved together, and the dispatch-vs-launch
> reading is duty-by-duty:**
>
> | Y-4 duty | state at `a8464861` | by whom |
> |---|---|---|
> | CAISO gate-(a) stamp re-key | 🟢 **DISCHARGED** | **`26d35d0e` — the capx director**, under owner ruling Q34 / r#33 card C-5. **Not Y-4.** |
> | `caiso_ct_peaker_committed_measured` registry declaration | 🔴 **UNDISCHARGED** | — (grep exit 1, zero hits) |
> | path-filter remedy (always-run job OR widened paths) | 🔴 **UNDISCHARGED** | — `ci.yml` `pull_request.paths` re-verified at lines 48–68; **`docs/**` still absent**; no always-run job added |
>
> **So the dispatch's framing — one lane, one PR, two duties — no longer matches
> the ground.** The duty most likely to be picked up by a passing lane (the stamp)
> was, by the director's own standing re-key; the two that need a deliberate owner
> — a registry row and a workflow change — were not. **Y-4's residue is the harder
> half**, and it is now the whole of what blocks R-AE.
>
> ### 🔴 LEG 4 — **30-FOR-30 A FOURTH TIME**, ON A FOURTH DISTINCT SET OF RUNS
>
> All 30 most recent completed `ci.yml` runs (**2352–2381**) are `pull_request`
> events and **every one concluded `failure`**; zero successes. v22 measured this
> on runs to 2321, v23 on 2322–2350, v24 on 2342–2371, v25 on 2352–2381. **The
> flip is NOT live.** Beyond the two flip-set reds, the standing reds at main's tip
> are `Forecast-invariant artifact audit` and `FR-22 parity` (both **H-1
> DO-NOT-REQUIRE**). 🟢 **`FR-21 forecast-board staleness` is now GREEN** — its
> `check_gate_a_provenance` step passes, so the R-T gap no longer re-reds a third
> job.
>
> ### 🟢 G2 LEGS AT ONE PIN
>
> | leg | state at `a8464861` |
> |---|---|
> | 1 · golden data tier | 🟢 **SATISFIED** — run #9 (`33704730253`) `workflow_dispatch`, `success`, still the newest of 9 (`total_count: 9`); cron confirmed removed (`golden-data-tier.yml` line 64–65, `workflow_dispatch:` only) |
> | 2 · fast-tier-green `ci.yml` run | 🟠 **MET ONCE (run 2351), NOT HOLDING — but ONE failure from green**, down from two |
> | 3 · keeper freeze | 🟢 **SATISFIED** — R-V holding, {ERCOT, NEISO, PJM} byte-identical |
> | 4 · branch-protection flip | 🔴 **NOT LIVE** — 30-for-30 a fourth time, still the owner's Settings action |
>
> **R-AD's precondition (flip confirmed live) is unchanged and unmet. This lane
> makes no G2 declaration and fires no FFR Q.2 notification.**
>
> ### 🟢 board X-1 / R-Z / R-AC — **RETIRED BY EXECUTION, CONFIRMED AND EXTENDED**
>
> Dispatch item (b) verified and **it holds beyond its own citation**. `Ruff lint +
> format` is `success` at run 2374 (job `100923983419`) **and still `success` at
> run 2381** (job `100955123881`) — both steps, `Ruff lint` and `Ruff format
> check`, green in each. The green has now survived **seven further CI runs and
> five merged PRs**, so it is a standing state, not a single observation.
> `pyproject.toml` line 67 ff. carries the `extend-exclude` entry with its R-AC
> citation. **board X-1 → RETIRED BY EXECUTION**, as dispatched. Cite
> `docs/FINDING-lint-hygiene-2026-09.md`.
>
> ### 🟢 board Z-1 — THE PROMOTION-DUTY CLASS, RECORDED AS DISPATCHED (AND WIDENED BY ONE)
>
> The dispatch asks this lane to record that **the flip is the fix** and that no
> new mechanism is proposed. **Recorded, and the evidence at this pin supports it
> more strongly than the dispatch's own framing:** the class is **three** duties,
> not two — gate-(a) stamp, parity registry row, **and keeper-recipe declaration
> (E11)**, the third discovered this cycle on the nyiso-185 promotion. All three
> are enforced only inside jobs that a PR can currently ignore, and **all three sit
> inside R-AE's six-check required set**, so the flip makes all three physically
> enforced at PR time. **No new mechanism is proposed.** Per the dispatch: any
> further stamp re-key by a records or audit lane **after** the flip is a defect
> report, not routine. ⚠️ **Before the flip it is not routine either** — this lane
> repaired nothing and routed everything, and the one stamp that was repaired in
> this window was repaired by the director under an explicit owner ruling.
>
> ### 🟢 Q-4 LABEL SWEEP
>
> Word-boundary (`grep -rE "\bLABEL\b" docs/`), per v24's hygiene finding:
>
> | label | hits before this record | note |
> |---|---|---|
> | **`R-AE`** | **0** | **new — this block and the §8 entry are its first artifacts** |
> | **`Z-1`** | **0** | **new — likewise; the boundary form is clean, no collision** |
> | `Y-4` | 2 | board + plan, from v24 |
> | `R-Z` / `R-AA` / `R-AB` / `R-AC` / `R-AD` | 4 / 2 / 5 / 4 / 2 | all now on the record (v24 landed them) |
> | `Q34` | 2 | capx ledger + prompt pack |
> | `Q30` | 13 | incl. `CLAUDE.md` (step-1b fossil dates) |
>
> v24's hygiene rules re-confirmed and re-stated: **bare-substring greps for these
> labels are unusable** (`R-AC` matches 141 files, because rule 14 is
> `[R-ACCURATE]`), and **`X-1`/`X-2`/`X-3`/`Y-1`/`Y-3` collide** with ERCOT probe
> labels and mathematical subscripts. **Cite as "board X-N" / "board Y-N" / "board
> Z-N", never bare** — a convention this block follows throughout.
>
> ### CORRECTIONS
>
> **Nothing in v24 is corrected.** Every v24 figure this lane re-derived agrees
> with v24 at v24's own pin `8d5a3e16`; all movement below is `b168260e..a8464861`
> motion, not v24 error. v24's self-correction of its own dispatch, and its adopted
> path-filter addendum, are both re-verified here and stand.
>
> **FIVE items of THIS dispatch's RECORD moved under this lane's measurement**, and
> are restated above rather than repeated:
> - **(a)** gates are **5 exit 0 / 2 exit 1**, not 6/1 — and `check_gate_a_provenance`
>   is now one of the **green** ones. Three of seven rows changed state.
> - **(d)** the fast tier is **1 failed / 7868 passed** (run 2381), not 2 failed /
>   7846 (run 2374); one of the two named failures is discharged. **R-T is
>   seven-for-EIGHT**, not seven-for-seven.
> - **(e)** R-AE's six-check set is **4 of 6 green**, not 5 of 6 — `Rule-22
>   quarantine gates` went red in this window.
> - **(f)** Y-4 is **NOT LAUNCHED** (three polls), not IN FLIGHT; and one of its
>   duties was discharged by the **capx director**, not by Y-4.
> - **(g)** board X-2's CAISO re-target is confirmed; **NYISO's row re-targets too**.
>
> Dispatch items **(b)** (lint discharged) and **(c)** (records v24 discharged) are
> **confirmed as written**. Item **(h)**'s lesson was applied and **paid off a
> second time** — but note the inversion: v24 used it to *upgrade* a non-launch to
> IN FLIGHT; v25's three polls **confirm** a non-launch. The lesson is a re-poll
> discipline, not a presumption of launch.
>
> ### QUEUE (v25)
>
> - **board Y-4 · NOT LAUNCHED, RESIDUE NARROWED TO TWO DUTIES** — (i) declare or
>   account `caiso_ct_peaker_committed_measured` in
>   `scripts/lib/forecast_parity_registry.py` under the R-X route; (ii) the
>   path-filter remedy — an always-run job **OR** the narrow paths widening, one
>   not both, **never a weakened required set**. The stamp duty is already
>   discharged (`26d35d0e`). Both remaining duties are one small PR; no solve, no
>   score, no registration, no keeper shard.
> - **board Y-5 · NEW — THE TWO NEW GATE REDS.** (i) The nyiso-185 **E11**
>   keeper-recipe declaration (`fossil_announced_exits_enabled` False → True in the
>   NYISO shard's promotion prose, or revert) — this is the promoting lane's duty
>   and it is what reds `Rule-22 quarantine gates`, i.e. **a second R-AE flip-set
>   blocker**. (ii) The two unmapped bundle dirs (`caiso243_b1_f923_fallback_guard`,
>   `nyiso185_control`) — register, prune, or `KEEP_REQUIRED_UNMAPPED_BUNDLES`;
>   each belongs to its own in-flight lane. **Record and route, do not repair
>   here.**
> - **board Z-1 · RECORDED, NOT DISPATCHED** — the promotion-duty class; **three**
>   duties, all inside R-AE's set; the flip is the fix; no new mechanism proposed.
> - **board Z-2 · NEW, RECORD ONLY** — `Rule-22 quarantine gates` **short-circuits**
>   after its first failing step, so a CI job conclusion **under-reports** the gate
>   ledger. The seven-script sweep is not redundant with CI and must not be skipped
>   because "CI already ran it".
> - **board X-1 · RETIRED BY EXECUTION** (dispatched; verified and extended above).
> - **board X-2 · UNCHANGED in count** — stage-0 4 of 7; CAISO and **NYISO** rows
>   re-target.
> - **board X-3 / X-4 / X-5 / X-6 · UNCHANGED.**
> - **board Y-1 · the owner Settings flip (R-AE)** — **4 of 6** required checks
>   green; blocked on Y-4(i), Y-4(ii) and **now Y-5(i)**. None is a program item.
> - **board Y-2 · G2 declaration sitting (R-AD)** — precondition unmet, unchanged.
> - **board Y-3 · the R-T pattern — now seven-for-EIGHT.** The eighth promotion
>   complied, under owner ruling Q34's standing duty rather than a structural gate.
>   **Record, do not dispatch**; still moot the moment the flip is live.
>
> **Net: the program moved forward and sideways at once. Leg 2 went from two
> blockers to one, gate-(a) is green for the first time since the caiso-241
> promotion, `FR-21` recovered, Ruff's green is now a standing state, and the R-T
> pattern broke at eight. Against that: two gates that were green are red, R-AE's
> flip set lost a check, and the newly-red one exposes a THIRD promotion duty. The
> shape of the problem is unchanged and is the whole of Z-1 — every one of these is
> a shared-surface duty that no PR is forced to discharge, and the flip that would
> force them is itself gated on three of them.**

> # 🔴 v24 (2026-09-04, pin `8d5a3e16`) — **LEG 2's GREEN DID NOT SURVIVE ONE KEEPER PROMOTION. THE FAST TIER IS RED AGAIN, AND BOTH FAILURES TRACE TO A SINGLE PROMOTION'S TWO UNMET SHARED-SURFACE DUTIES.**
>
> **THE PIN MOVED UNDER THIS DISPATCH, AGAIN.** The director pinned `c6e46b49`
> (#4642); `origin/main` was already **`8d5a3e16`** (#4664) at this lane's first
> poll and stable across three (19:5x–20:0x Z). The window `c6e46b49..8d5a3e16`
> is **56 commits / 12 merged PRs**. Every figure below is re-derived at
> **`8d5a3e16`**, and each place the dispatch's RECORD moved is named.
>
> ### 🔴 THE HEADLINE — LEG 2 IS **UN-SATISFIED AT MAIN's TIP**, AND THE CAUSE IS ONE PROMOTION
>
> **Run 2371 (`33799209070`, head `dc278084`, the miso-203 branch whose merge is
> main's tip), `Fast test tier` job `100794204431` conclusion `failure` —
> `2 failed, 7846 passed, 34 skipped, 2 xfailed`, 8 m 37 s.** Against v23's run
> 2351 (`7823 passed, 0 failed`). **Both failures trace to the SAME single keeper
> promotion — caiso-241 (#4661, `a6c8db2f`) — and both are unmet duties on a
> SHARED SURFACE the promoting PR did not touch:**
>
> 1. `tests/scoring/test_gate_a_provenance.py::test_live_board_passes` — `assert 1 == 0`.
>    The CAISO gate-(a) stamp still cites `2026-09-03-caiso-240-b1-stgas`; the live
>    keeper is `2026-09-03-caiso-241-b1-ctpeaker`. **This is R-T non-compliance #7.**
> 2. `tests/scoring/test_forecast_parity.py::test_all_six_keepers_resolve` —
>    *"CAISO: ['caiso_ct_peaker_committed_measured'] armed in the keeper with no
>    forecast-orchestrator consumer and no registry declaration."* The field is a
>    real `ScenarioConfig` field (`scenarios.py:11411`, default `False`, introduced
>    `81b1aa80`) and it **is** in the mechanism matrix — so rule 28 duty (c) was
>    MET and `check_mechanism_matrix.py` is exit 0 — but it is **absent from
>    `scripts/lib/forecast_parity_registry.py`**. **This is the first recurrence of
>    the R-X object class since R-X discharged**, on the very next promotion.
>
> **What this establishes, and it is the cycle's most important finding: leg 2's
> criterion is satisfiable but not *stable*.** Run 2351's green is a historical
> fact and is NOT withdrawn — the leg was met, once, as v23 recorded. But it
> survived **one** keeper promotion, because two duties that live outside the
> promoting lane's own files are enforced by tests inside the fast tier and
> nothing makes a promoting PR discharge them. **Leg 2 and leg 4 are the same
> problem twice** (board M-7's phrasing, now demonstrated rather than forecast):
> the flip R-AB orders would require `Fast test tier`, which is red at main's tip
> for exactly this reason.
>
> ### 🔴 SEVEN GATES — **SIX EXIT 0, ONE EXIT 1.** THE DISPATCH's ITEM (a) DOES NOT HOLD AT THIS PIN
>
> The dispatch records *"Seven gates all exit 0 (first all-green sitting on
> record; verify at your pin)."* **Verified, and it does not hold at `8d5a3e16`.**
> That reading was true at `c6e46b49` and was undone by the caiso-241 promotion
> merged after it. Each script invoked alone, `$?` read immediately, **never
> through a pipe**:
>
> | gate script | exit | reading at `8d5a3e16` |
> |---|---|---|
> | `audit_keepers.py --check` | **0** | PASS 0 failures / 0 warnings |
> | `check_registry_payload_parity.py` | **0** | 64 runs / 100 bundle dirs / 0 tolerated |
> | `check_mechanism_matrix.py` | **0** | 195 field + 49 row + 164 path anchors, 6 ISO shards, keeper stamps match |
> | `check_forecast_staleness.py` | **0** | Δ = 0; 2 WARNs (25 of 74 verdicts undated) |
> | `check_bench_freshness.py` | **0** | 20 parts, **0 STALE**, 20 with engine drift |
> | `check_gate_a_provenance.py` | 🔴 **1** | **ONE row: CAISO cites `caiso-240`, live keeper `caiso-241-b1-ctpeaker`** |
> | `check_golden_manifest.py` | **0** | 42 manifests, 75 entries (11 enforced), 3 stale vs live keeper |
>
> The one red is **not** this lane's to repair — it is the caiso-241 promoter's
> unmet R-T duty, and repairing it here is exactly the manual re-key the flip
> exists to end. **Recorded and routed, not patched** (see Y-4).
>
> ### 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — RE-DERIVED FAIL-CLOSED
>
> All four re-derived independently at this pin, `frontier` fail-closed (a null or
> withdrawn `frontier` is **ABSENT**):
>
> | instrument | membership at `8d5a3e16` |
> |---|---|
> | `frontier` present in `keepers/<ISO>.json` | **{ERCOT, NEISO, PJM}** — CAISO/MISO carry no `frontier` key; **NYISO `withdrawn` 2026-08-30 ⇒ ABSENT** |
> | `complete` marker | **{ERCOT, NEISO, PJM}** |
> | gate-(a) passers (`program-status.json`) | **{ERCOT, PJM, NEISO}** |
> | ISO-level determination `CALIBRATED` | **{ERCOT, NEISO, PJM}** |
>
> **`final` is EMPTY** (its only key is `_note`). The **holdout spend freeze is
> ACTIVE with `scope.tiers = ["locked_test"]`** — validation tier (2020/2021/2022)
> governed by the `complete` marker + `--holdout-authorized` alone. **No
> locked-test year has ever been solved, scored or registered for any ISO.** The
> dispatch's item (b) is **confirmed unchanged**.
>
> ⚠️ **The stale CAISO stamp does NOT move an instrument.** CAISO fails gate (a)
> identically before and after (NOT-YET, absent from `complete`), so alignment is
> a *verdict* statement that survives a *identity* failure — the distinction the
> guard was built to expose, working as designed.
>
> ### 🟠 KEEPER MOTION — **ONE HOP MORE THAN THE DISPATCH RECORDED**, AND R-V HOLDS
>
> The dispatch's item (c) names two promotions since v23's pin `49bfbc49`. At this
> pin there are **three hops across two ISOs**:
>
> | ISO | motion since `49bfbc49` | PR |
> |---|---|---|
> | CAISO | 239 → 240 → **`2026-09-03-caiso-241-b1-ctpeaker`** | #4641, **#4661** |
> | MISO | 201 → `2026-09-03-miso-202-unitclip` | #4651 |
>
> **Since the director's own pin `c6e46b49` the motion is CAISO 240 → 241 alone.**
> **caiso-241 is `NOT-YET` at run level** (`calibration_verdict.py --run-id`,
> committed artifacts only, no solve: C3a mean LMP FAIL — 2024 **+12.3 %**, 2025
> **+15.5 %**; C1/C2/C3b/C4/C6/C8 PASS; C3c the lone ledgered caveat) and
> **`NOT-YET` at ISO level** (CAISO is absent from `complete`, so it holds no
> marker determination). **The R-V freeze on {ERCOT, NEISO, PJM} is INTACT** —
> all three keeper shards byte-unchanged in this window; every promotion is in an
> explicitly-unfrozen lane.
>
> **Stage-0 is 4 of 7 current — X-2 stands, unchanged in count** (ERCOT,
> ERCOT\_\_carveout-2023, NEISO, PJM CURRENT; CAISO, MISO, NYISO STALE). CAISO's
> stale row **re-targets** though: it was stale against `caiso-231-b1-ungrounded`
> and is now stale against `caiso-241-b1-ctpeaker`.
>
> ### 🔴 R-T ROUTING — **SEVEN FOR SEVEN**, AND THE COST IS NOW MEASURED IN CI
>
> `git log 49bfbc49..8d5a3e16 -- frontend/data/forecast/program-status.json`
> returns **two** commits, and **neither is a promoting PR**: `e8bc1990` (records
> v23 job 0) and `6ed483df` (the capx director's fifth manual re-key, #4642).
> **The caiso-241 promotion `a6c8db2f` touched `keepers/CAISO.json` and
> `status/CAISO.js` and did NOT touch `program-status.json`** — verified from the
> commit's own file list. **R-T non-compliance count: SEVEN promotions since the
> ruling** (miso-200 #4614, miso-201 #4630, nyiso-177 #4632, caiso-239 #4634,
> caiso-240 #4641, miso-202 #4651, **caiso-241 #4661**) — **zero re-keyed by the
> promoting PR.**
>
> **What v24 adds to this pattern is that it is no longer only a records cost.**
> For six cycles the R-T gap produced a stale stamp and a gate exit 1. The seventh
> produced **a red `Fast test tier` on `main`'s tip**, i.e. it took back the G2
> leg the program spent four lanes earning. Y-3 called this "moot the moment the
> flip is live"; that is still true, and it is now also **the reason the flip
> cannot be taken as R-AB specifies it** (below).
>
> ### 🔴 R-AB — THE FLIP LIST IS **4-OF-5 READY**, AND THE FIFTH IS THE caiso-241 REPAIR
>
> R-AB orders the flip with the R-P list **minus** `Ruff lint + format`: required =
> `Fast test tier`, `Pinned default cache key`, `Structural refactor guards`,
> `Cache-key registration guard`, `Rule-22 quarantine gates`. **Measured at run
> 2371 (main's tip content), job by job:**
>
> | required check | run 2371 |
> |---|---|
> | Pinned default cache key | 🟢 success |
> | Structural refactor guards | 🟢 success |
> | Cache-key registration guard | 🟢 success |
> | Rule-22 quarantine gates | 🟢 success |
> | **Fast test tier** | 🔴 **failure** (the two caiso-241 duties) |
>
> **Four of the five are flip-ready right now. The fifth is red, and it is red for
> a reason that is not a program item and not an engine defect** — it is one
> promotion's two undischarged shared-surface duties. **This lane does not
> recommend deferring the flip**; it records that flipping at this pin blocks
> every PR until those two are repaired, and that the repair is small, named and
> owned (Y-4). **A DISPATCH MAY NOT UPGRADE A LANE'S CLAIM and this one does not
> try to** — R-AB is the owner's ruling and stands; what moved is the measurement
> underneath it, taken 56 commits after the ruling was made.
>
> ### 🔴 R-AB, SECOND BLOCKER — **H-1's PATH-FILTER TRAP APPLIES TO ALL FIVE REQUIRED CHECKS, AND THIS LANE's OWN PR DEMONSTRATES IT**
>
> H-1 carries this as a `file-integrity-guard` problem: *"a required check that is
> path-filtered blocks every PR it does not run on … requiring it strands every
> docs-only PR, this records lane's included, forever."* **Measured at this pin,
> the same trap applies to R-AB's entire required set, which H-1 does not yet
> say.** `ci.yml`'s `pull_request` trigger is **path-filtered** (`src/**`,
> `scripts/**`, `tests/**`, `pyproject.toml`, `uv.lock`, `.python-version`,
> `conftest.py`, `frontend/data/{backcast,hindcast,forecast}/**`,
> `tests/golden/**`, the two mechanism-matrix paths, `CLAUDE.md`,
> `.github/workflows/ci.yml`) — and **`docs/**` is not among them.** All five
> checks R-AB names are `ci.yml` jobs, so on a docs-only PR **none of the five
> ever reports**, and GitHub treats a never-reporting required check as
> **pending**, not passed.
>
> **This is demonstrated, not reasoned.** This lane's own PR (#4667) touches
> exactly two files, both under `docs/`. Its head commit produced **one** check
> run in total — `shrink-guard`, `success` — and **zero `ci.yml` jobs**
> (`total_count: 0` for the branch on the runs API). Under R-AB as written that PR
> would sit **pending on five checks forever**, and so would every future records
> refresh, every plan/board edit and every handoff doc.
>
> **The fix is H-1's own, applied one level wider: a widened filter or an
> always-run no-op job — never a weaker required set.** Recorded as a
> **second blocker on Y-1**, alongside the `Fast test tier` red (Y-4). Both are
> small; neither is a program item; and **neither is a reason to defer the flip
> once they are cleared.**
>
> ### 🔴 LEG 4 — **30-FOR-30 A THIRD TIME**, ON A THIRD DISTINCT SET OF RUNS
>
> All 30 most recent completed `ci.yml` runs (**2342–2371**) are `pull_request`
> events and **every one concluded `failure`**. v22 measured this on runs up to
> 2321, v23 on 2322–2350, v24 on 2342–2371. **The flip is NOT live.** Remaining
> reds on main's tip beyond the fast tier: `Ruff lint + format` (blocker (a), the
> lint lane's object), `Forecast-invariant artifact audit` and `FR-22 parity`
> (both **H-1 DO-NOT-REQUIRE**), and `FR-21` — which fails on the
> `check_gate_a_provenance` step, i.e. **the R-T gap re-reds a third job too**.
>
> ### 🟢 G2 LEGS AT ONE PIN
>
> | leg | state at `8d5a3e16` |
> |---|---|
> | 1 · golden data tier | 🟢 **SATISFIED** — run #9 (`33704730253`) `workflow_dispatch`, `success`, still the newest of 9; cron confirmed removed from the workflow (`workflow_dispatch:` only) |
> | 2 · fast-tier-green `ci.yml` run | 🟠 **MET ONCE (run 2351), NOT HOLDING** — red at main's tip on the two caiso-241 duties |
> | 3 · keeper freeze | 🟢 **SATISFIED** — R-V holding, {ERCOT, NEISO, PJM} byte-unchanged |
> | 4 · branch-protection flip | 🔴 **NOT LIVE** — 30-for-30, still the owner's Settings action |
>
> **R-AD declares G2 "at the next director refresh after the flip is confirmed
> live". That precondition is unchanged and unmet.** This lane makes no G2
> declaration and fires no FFR Q.2 notification.
>
> ### 🟢 X-1 / R-Z / R-AC — THE LINT LANE **LAUNCHED**, AND LESSON (f) IS VINDICATED ON ITS FIRST APPLICATION
>
> **This lane's first branch poll found NO lint or ruff branch on `origin`.** Per
> v23's own protocol lesson — *"'no branch' is a snapshot — re-poll once before
> classifying a non-launch"* — it re-polled, and found
> **`claude/lint-hygiene-r-z-ac-zooe9c`**, two commits, no PR yet:
> `3a3b445a` (R-AC, `pyproject.toml` +12) and `b9384baf` (R-Z, ruff format on
> **seven** files). **A protocol lesson written one cycle ago prevented a false
> non-launch on its first use.** **G-14's tally stays at five.**
>
> **And this lane's independent measurement agrees with the lane's own scoping,
> which is worth recording because it is a non-obvious sequencing fact:**
> `ruff check` is **5 errors, all `E731`×3 / `E402`×2 / `E401`×1 in
> `docs/handoffs/d37/` and `d45/` probe scripts** — unchanged from v23 — so
> **R-AC clears lint entirely**. But `ruff format --check` is **11 files at this
> pin (v23 measured 10)**, of which only 4 are under `docs/handoffs/`. **Clearing
> lint UNMASKS the format step, which is currently `skipped` behind it, leaving
> SEVEN files** — `scripts/gen_nyiso177_attestation.py`,
> `src/market_sim/data/fleet/campd_bins.py`, `src/market_sim/data/offer_curves.py`,
> `tests/regression/test_hourly_sidecars.py`,
> `tests/unit/data/test_campd_per_unit_attribution.py`,
> `tests/unit/data/test_unit_outage_st_capacity_basis.py`,
> `tests/unit/pipeline/test_caiso_ct_peaker_committed_measured.py`. That is
> exactly the branch's second commit. **R-AC alone does not green the Ruff job;
> R-AC + the seven does.**
>
> ⚠️ **Two of the seven are `src/market_sim/` core files ≥300 lines** —
> `campd_bins.py` (2,684) and `offer_curves.py` (1,637) — so **rule 27 `[R-PUSH]`
> blob verification is owed on that push.** Measured reassurance for the lane: the
> format diffs are **14 and 39 lines** respectively, **not** the HOUSE-1 incident
> class (which reflowed a hand-formatted core file 3,960 → 9,508 lines and is why
> `extend-exclude` carries its charter comment).
>
> ### 🟢 Q-4 LABEL SWEEP — AND A LABEL-HYGIENE FINDING
>
> **`R-Z`, `R-AA`, `R-AB`, `R-AC`, `R-AD` each return ZERO word-boundary hits
> across `docs/`** before this record — the five rulings of the 2026-09-03 sitting
> existed only in the dispatch prompt. This block and the §8 entry are their first
> artifacts. **Two hygiene facts, recorded so later sweeps are not misled:**
>
> - **Bare-substring greps for these labels are unusable.** `R-AC` matches
>   **141 files** on substring — because rule 14 is `[R-ACCURATE]`. Always sweep
>   these labels with a word boundary (`grep -rE "\bR-AC\b"`).
> - **The queue's own `X-N`/`Y-N` namespace is not unique across `docs/`.**
>   `X-1`/`X-2`/`X-3` collide with ERCOT probe labels (18 / 18 / 11 files);
>   `Y-1`/`Y-3` collide with *mathematical subscripts* (year `Y-1`, the PJM/ISO-NE
>   `Y-3` forward-clearing lag) in four forecast-program docs. Only `X-4`/`X-5`/
>   `X-6` are clean. **Cite these as "board X-N" / "board Y-N", never bare.**
>
> ### 🟢 R-AA — RATIFIED, NOTHING FURTHER OWED HERE
>
> R-AA ratifies R-X's `nyiso_seam_par_attribution` GAP row under the R-X route
> (R-X finding §3.3 flag closed); the wire-forward question **stays routed to the
> capx/forecast desk, undecided**. No action falls to this lane, and none is
> taken. ⚠️ **But see the headline:** the R-X *object class* recurred on
> `caiso_ct_peaker_committed_measured` at the next promotion, which means the R-X
> route needs an owner **on new fields**, not only on the seven it adjudicated.
> That is Y-4, and it is the substantive queue change this cycle.
>
> ### CORRECTIONS
>
> **Nothing in v23 is corrected.** Every v23 figure this lane re-derived agrees
> with v23 at v23's own pin; the movements above are all `49bfbc49..8d5a3e16`
> motion, not v23 error. **Four items of the DISPATCH's RECORD moved under this
> lane's own measurement and are restated above rather than repeated:** (a) seven
> gates is **6/7**, not 7/7; (c) keeper motion is **three hops**, not two, and
> adds caiso-241; (d) the R-T count is **SEVEN**, not six; (g) R-AB's required
> list contains one job that is **red at main's tip**. Item (h)'s "X-1 → IN
> FLIGHT" is **correct** and was confirmed only on the second poll.
>
> ### QUEUE (v24)
>
> - **Y-4 · NEW, and the cycle's only new dispatchable item — THE caiso-241
>   TWO-DUTY REPAIR.** One small PR: re-key the CAISO gate-(a) stamp to
>   `2026-09-03-caiso-241-b1-ctpeaker`, and declare or account
>   `caiso_ct_peaker_committed_measured` in `scripts/lib/forecast_parity_registry.py`
>   under the R-X route. **This is what stands between main's tip and a green
>   `Fast test tier`, and therefore between the program and an R-AB flip that does
>   not block every PR.** Stamp-only + one registry row; no solve, no score, no
>   registration, no keeper shard.
> - **board X-1 · IN FLIGHT** — lint lane `claude/lint-hygiene-r-z-ac-zooe9c`,
>   branch pushed, PR not yet opened. Rule 27 blob-verify owed on two core files.
> - **board X-2 · UNCHANGED** — stage-0 re-captures, 4 of 7 current
>   (PERF-B/capture lane, R-O schema); CAISO's row re-targets to caiso-241.
> - **board X-3 / X-4 / X-5 / X-6 · UNCHANGED.**
> - **board Y-1 · the owner Settings flip (R-AB)** — 4 of 5 required checks green;
>   gated in practice on **two** small blockers, neither a program item: **Y-4**
>   (the `Fast test tier` red) and **the path-filter trap** — `ci.yml` does not run
>   on `docs/**`, so all five required checks would strand every docs-only PR as
>   *pending*, this lane's own #4667 demonstrating it. H-1's remedy applies: widen
>   the filter or add an always-run no-op job, never weaken the required set.
> - **board Y-2 · G2 declaration sitting (R-AD)** — precondition (flip confirmed
>   live) unmet; all four legs to be verified at ONE pin when it is.
> - **board Y-3 · the R-T non-compliance pattern — now SEVEN for seven**, and no
>   longer records-only: it has cost a G2 leg. Still moot the moment the flip is
>   live. **Record, do not dispatch.**
>
> **Net: the program did not lose a leg it had earned — run 2351 stands — but it
> learned that leg 2 is not self-sustaining. Four legs' worth of work is one
> undischarged promotion duty away from red at any time, and the flip that would
> enforce those duties is itself gated on the very duty being undischarged. Y-4
> breaks that loop with one stamp-only PR.**

> # 🟢 v23 (2026-09-03, pin `49bfbc49`) — **G2 LEG 2 IS *SATISFIED* — RUN 2351, `Fast test tier` GREEN, THE FIRST EVER. R-W, R-X AND R-Y ALL DISCHARGED IN THE SAME CYCLE; LEG 1's INSTRUMENT IS GREEN FOR THE FIRST TIME SINCE 08-15.**
>
> **THE PIN MOVED TWICE UNDER THIS DISPATCH.** The director pinned `68690427`
> (#4628); `origin/main` was already **`c73f78f5`** (#4634) at this lane's first
> two-poll stability, and **`49bfbc49`** (#4644) by the time job 0 was pushed —
> because **R-X and R-Y both launched, landed AND merged inside this lane's own
> session.** Every figure below is re-derived at **`49bfbc49`** (two-poll stable);
> the two windows — `68690427..c73f78f5` (28 commits) and `c73f78f5..49bfbc49`
> (27 commits) — are called out separately where they change an answer.
>
> ### 🔴→🟢 JOB 0 FOUND **THREE** STALE GATE-(a) ROWS, NOT ONE — AND IT IS LEG 2's LAST BLOCKER
>
> The dispatch sent this lane to re-key **MISO** to `2026-09-02-miso-200-unitroute`.
> At the pin, `check_gate_a_provenance.py` **exit 1 on THREE rows**, and MISO's live
> keeper was **`2026-09-02-miso-201-stbasis`** — one promotion past the dispatch's own
> target. The three: **CAISO** `231-b1-ungrounded → 239-b1-stgas` (#4634), **MISO**
> `198-oomlevel → 201-stbasis` (#4630, via `200-unitroute` #4614), **NYISO**
> `159-loss-surface → 177-vintage-matched` (#4632).
>
> **This is no longer records hygiene.** `tests/scoring/test_gate_a_provenance.py::test_live_board_passes`
> calls the checker's `main([])`, so it clears **only when every row is current** — and
> at `49bfbc49` it is **the sole remaining `Fast test tier` failure on `main`**. The
> `FR-21` CI job is red on the same step. **R-X's own finding routes this re-key to
> this lane by name, naming all three ISOs** (its §7: *"the next records lane should
> carry leg 2 as 'BLOCKED on the caiso-239 / miso-201 / nyiso-177 forecast-board
> re-key'"*). The dispatch's scope was extended from one row to three by **explicit
> owner decision taken in-session** on that measurement. **Executed, stamp-only:
> exactly 12 leaf paths change, no verdict moves** (all three read NOT-YET and are
> absent from `complete` on both sides), ERCOT/PJM/NEISO byte-unchanged,
> `check_gate_a_provenance` **1 → 0**, all seven gates green.
>
> ### 🟢🟢 AND JOB 0's OWN PR RUN PRODUCED THE GREEN — **LEG 2 IS SATISFIED**
>
> **Run 2351 (`33707179376`, PR #4646, head `e8bc1990` = the job-0 commit alone),
> status `completed`, `Fast test tier` job `100498709463` conclusion `success` —
> `7823 passed, 34 skipped, 2 xfailed`, ZERO failures, 9 m 43 s.** The criterion is
> *"a completed `ci.yml` run whose `Fast test tier` job concludes success"*, as v21
> wrote it and R-W and R-X both restated it; **it is met, for the first time.** The
> run's overall conclusion is still `failure` on `Ruff lint + format` and the two
> **H-1 DO-NOT-REQUIRE** jobs — **the criterion has never been the run's
> conclusion**, which is exactly why v21 could refuse run 2298 and R-X run 2344.
> `FR-21` is green in the same run, on the very step job 0 was written to clear.
> **The object count walked 12 → 1 → 1 → 0 across four lanes, and not one of them
> claimed a green it did not have.** Full record and the honesty checks: **M-15**.
>
> ### 🟢 R-W **DISCHARGED**, COMPLETENESS-CHECKED — AND ITS COUNT LINEAGE REPLACES THE BOARD's
>
> 11 of 12 CI-true failures repaired by root cause, **zero regressions**, 7,717
> passing. The 12th was **substantively routed, not patched** — the second
> consecutive lane to hold that line. And it root-caused a **13th, latent** defect:
> `tests/scoring/test_golden_manifest_provenance.py` executes
> `scripts/capture_keeper_goldens.py` by path, whose import-time
> `MARKET_SIM_HIGHS_THREADS=1` pin **leaks into the pytest process**, so every later
> in-process LP solve dies `Not Set` against an already-initialized HiGHS scheduler.
> **THE BOARD'S CI COUNTS ARE HEREBY CORRECTED:** *"56 → 33"* and *"33 remaining"*
> were **local poisoned counts**. CI-side truth: **9** at R-U's pin, **12** at R-W's
> start, **1** after. Use the CI numbers.
>
> ### 🟢 R-X **DISCHARGED** — THE PARITY RED IS CLEARED, AND LEG 2 RE-BLOCKED ON JOB 0
>
> Owner ruled **GAP declarations** (the FFR-1E route); the wire-forward question was
> **deliberately routed to the capx/forecast desk, undecided**. The lane found the job
> **larger than R-W saw — seven unaccounted fields, not three** — filed the ERCOT pair
> plus one same-class NYISO fork as GAP, accounted two as `PARAMETER_OF`, and
> **reviewed rather than extended** the `_FR22_OPEN_UNACCOUNTED` pin. Run **2344**:
> `Fast test tier` **`1 failed, 7807 passed`** — *the parity test is GREEN*; the one
> red is job 0's object. **It refused the leg-2 claim itself** — the fourth
> consecutive lane to refuse on measurement.
>
> ### 🟢 R-Y **DISCHARGED** — AND LEG 1's INSTRUMENT IS **GREEN FOR THE FIRST TIME SINCE 2026-08-15**
>
> The 3-for-3 scheduled reds were **three different defects, one merged between each
> firing** — not the history rewrite, not the corpus conversions, not the manifest
> schema (each ruled out on evidence). Run #5 the `curate_lmp` dtype crash (already
> fixed); #6 an un-provisioned new raw corpus (`eia-930-interchange`, the loud-failure
> guard working as designed); #7 that plus a stale NYISO `complete` assertion the
> Q5-W withdrawal invalidated. **The cron is REMOVED — `workflow_dispatch`-only, as
> ruled** (the billed-minutes point recorded: a failing cron was spending owner money
> unwatched). The first dispatch, run #8, surfaced a **fourth** defect — a teardown
> abort at interpreter finalization, fixed at the shared `clean_io.validate_clean`
> seam. **Run #9 (`33704730253`) is `success`**, 51 passed / 0 failed, zero
> data-missing skips, the ERCOT fleet-arrays golden byte-identical.
>
> ### 🔴 THE FLIP IS **STILL NOT LIVE** — LEG 4 REMAINS THE OWNER'S ALONE
>
> Re-measured: **all 30 most recent `ci.yml` runs are `pull_request` events and every
> one concluded `failure`** (runs 2322–2350), against **13 merges in-window**. v22's measurement is
> **confirmed unchanged**. R-X's lint rider landed, but **blocker (a) has re-reddened
> from a new direction**: `ruff check` is red on **5 errors, all in capx probe scripts
> under `docs/handoffs/d37/` and `d45/`**, and **10 files** would fail the format step
> behind it. The flip is best taken when that job is green, which is now a
> *per-run-probe-script hygiene* question, not a source-tree one.
>
> ### 🟢 GATES, ALIGNMENT, KEEPER MOTION
>
> Seven gate scripts at `49bfbc49`, each unpiped: **six exit 0, one exit 1** — and the
> one is job 0's, repaired on this lane's branch. Four-instrument alignment
> **HOLDS at {ERCOT, NEISO, PJM}**, all four agreeing, `final` **EMPTY**. Keeper
> motion is **three ISOs** (CAISO, MISO ×2, NYISO) — **the R-V freeze on
> {ERCOT, NEISO, PJM} is intact**; every one of the three is an explicitly-unfrozen
> lane. **Stage-0 has REGRESSED to 4-of-7 current** (CAISO, MISO, NYISO goldens stale
> against those same promotions) — independently confirmed by R-Y §8.

> # 🔴 v22 (2026-09-02, pin `dfc44d95`) — **G2 LEG 2 REFUSED A THIRD TIME, ON EVIDENCE NEWER THAN v21's. R-U IS DISCHARGED; R-W HAS NOT LAUNCHED; THE PARITY DEFECT HAS DOUBLED.**
>
> **THE PIN MOVED UNDER THE DISPATCH.** The director pinned `a5abe3fe` (merge of
> #4603); `origin/main` was already **`dfc44d95`** (#4608) at this lane's first
> poll and stable across two more. Every figure below is re-derived at
> `dfc44d95`, and the four-commit window `a5abe3fe..dfc44d95` is reported
> separately where it matters.
>
> ### 🔴 LEG 2: THE REFUSAL HOLDS, AND THE NEWEST EVIDENCE IS **RUN 2307**, NOT 2298
>
> v21 refused the leg-2 satisfaction claim on run 2298. **A newer run exists and
> this lane found it rather than re-quoting v21:** **run 2307** (id
> `33590273632`, branch `claude/ci-red-repair-hn56lh`, head `937c48ee`, completed
> **2026-09-02T04:28:51Z** — 52 minutes after 2298). Job-by-job: **7 green, 3
> red.** The three reds are **`Fast test tier`** (step *Fast pytest tier*,
> 04:19:23 → 04:28:47 = **9 min 24 s**, failed on **content**), `FR-22
> backcast→forecast parity` (**by design**) and `Forecast-invariant artifact
> audit`. **G2 leg 2's criterion — "one completed fast-tier-green `ci.yml` run" —
> is still unmet, now confirmed three times on three successively newer runs
> (2278 → 2298 → 2307).**
>
> ### 🟢 BUT R-U IS **FULLY DISCHARGED** — ALL THREE CHARTER JOBS ARE GREEN IN A RUN OF THEIR OWN
>
> **This is new, and it is better than v21 could report.** In run 2307,
> **`Ruff lint + format`, `Pinned default cache key` and `Structural refactor
> guards` are ALL THREE `success`** — the first run in which R-U's entire charter
> is simultaneously green. Its lane merged as **#4564, #4573, #4578** and the
> branch is **deleted**. **R-U's charter is complete; leg 2 was never in it.**
> That is precisely the gap J-11 forecast and v21 vindicated — and it is now a
> *closed* lane's residue rather than an open lane's omission.
>
> ### 🔴 R-W HAS **NOT LAUNCHED** — NON-LAUNCH #5, AND LEG 2's ONLY ROUTE IS UNSTAFFED
>
> Dispatch-vs-launch at this pin: **`R-W` returns ZERO hits across the whole
> board** (the Q-4 sweep found ≥1 artifact for every label **R-A … R-V**, and
> **0** for R-W), there is **no remote branch** matching the fast-tier repair,
> there are **ZERO open PRs repo-wide**, and no merge in the window touches the
> fast tier. **G-14's tally goes to five.** The distinction that makes this worse
> than it looks: R-U is closed and discharged, so **the job leg 2 actually
> requires now has a dedicated ruling and no session at all.**
>
> ### 🔴 THE PARITY DEFECT DID NOT HOLD STILL — IT **DOUBLED, INSIDE THIS WINDOW**
>
> `check_registry_payload_parity.py` **exit 1**, naming **two** dead bundles, not
> the director's one: **`miso200_control_A` AND `miso200_unitroute_B`**. The
> second landed **in this very window** via **#4607** (`e8a5a485`), and **both are
> tracked on `origin/main` at 14 files each.** Same lane, same class, one more per
> merge. **Routing it to the calibration desk HARDER is right, and now better
> evidenced:** register, prune or allowlist is their call, but the cost is a
> parity job red on **every** PR the repository opens, and a defect that
> **reproduces on the lane's next push.**
>
> ### 🟢 STAGE-0 IS 7 OF 7 CURRENT — CONFIRMED, ON A STRONGER FOOTING THAN CLAIMED
>
> `check_golden_manifest.py` **exit 0**: **42 manifests, 75 entries, 11 enforced /
> 64 legacy, and of the enforced 0 pruned and 0 stale.** All seven stage-0 rows
> name their ISO's live keeper, cross-checked against the keeper shards
> independently. **Capture-A verifies against its dispatch with no gap** (MISO ←
> `2026-09-01-miso-198-oomlevel`, oracle **PASS — 271 flags identical, 0 drift**,
> read from the finding). ⚠️ **One correction to Capture-A's own finding:** its
> headline reads *"5 current / 1 stale → 6 current / 0 stale"* while its own
> table enumerates **seven** entries — it does not count `ERCOT__carveout-2023`
> as a row, the residue of the "6 rows" framing v21 closed. **The gate's 7 is
> authoritative; the conclusion is unaffected.** And the standing caveat is
> restated because it has not moved: **7-of-7 current is NOT byte-green
> certification** — that needs the golden tier exercised, and it has not been.
>
> ### 🔴 THE GOLDEN TIER IS NOT MERELY UNEXERCISED — IT IS **THREE-FOR-THREE RED ON ITS OWN SCHEDULE**
>
> Re-measured: **7 runs ever.** The last `workflow_dispatch` is **run #4,
> 2026-08-15** — the director's read, **confirmed**. But runs **#5 (08-17), #6
> (08-24) and #7 (08-31)** are `schedule` events and **all three failed**, and
> **run #7 post-dates R-V's un-park.** So leg 1 is not blocked on permission or
> on someone pressing a button: **byte-green still has no working instrument.**
>
> ### 🔴 AND THE FLIP IS MEASURABLY NOT LIVE — SAID FROM EVIDENCE, NOT FROM "NO LANE CAN VERIFY IT"
>
> Every one of the **30 most recent `ci.yml` runs is a `pull_request` event and
> every one is `failure`** — yet **13 PRs merged in this window alone** (#4585 …
> #4608). A required-check set would have blocked them. **Branch protection is
> not enforcing R-P's list at this pin**, and that is now a measurement rather
> than an assumption.

---

> # 🔴 v21 (2026-09-02, pin `0653bf13`) — **G2 LEG 2 IS *NOT* SATISFIED. THE DISPATCH SAID IT WAS, AND RUN 2298 IS NOT GREEN.**
>
> **THE DISPATCH THAT OPENED THIS LANE INSTRUCTED, VERBATIM: record run 2298
> (id `33587007663`) as *"THE GREEN COMPLETED RUN … G2 LEG 2 SATISFIED, retiring
> the 'leg 2 not satisfiable' correction it supersedes."* **THAT IS REFUSED ON
> MEASUREMENT.** Run 2298's own API record reads
> **`"conclusion": "failure"`**, and its job list gives the reason: of ten jobs,
> **seven are green and three are red — and one of the three is `Fast test
> tier`.**
>
> **G2 leg 2's criterion is not "a completed run". It is — this board's own
> words, still on the page — *"one completed fast-tier-green `ci.yml` run"*.**
> The fast tier is **red** in the very run offered as proof. **Leg 2 stays
> BLOCKED, and the v19b "not satisfiable" correction is NOT retired — it is
> RE-CONFIRMED on newer evidence** (run 2298, 2026-09-02, replacing run 2278).
>
> **R-U'S OWN FINDING NEVER CLAIMED OTHERWISE, AND SAYS SO IN TERMS.**
> `docs/FINDING-ci-red-repair-2026-09.md` §6 reads: ***"7 of 7 required checks
> green. The run is not 'fully green' and this finding does not claim it is"***,
> and its table marks `Fast test tier` **🔴 failure · ❌ deferred (memo §3)**.
> **The error is the dispatch's compression of "7 of 7 *required* checks green"
> into "the green completed run", and then into a leg-2 satisfaction claim the
> lane that did the work explicitly declined to make.**
>
> **AND THIS BOARD PREDICTED IT, ONE CYCLE EARLY, IN WRITING.** J-11's scoping
> note: *"R-U names **three** jobs; **four** are red-not-by-design, and the
> fourth is the gating one … `Fast test tier` … is NOT in R-U's three, and it is
> the job G2 leg 2 actually requires. **Leaving it out leaves leg 2 blocked even
> on a fully [successful R-U]**."* **That warning is now VINDICATED BY
> MEASUREMENT rather than carried as a caution.** A records lane's forecast of a
> completeness gap came true exactly as written; the value of J-11 was that it
> made this cycle's check a five-minute confirmation instead of a discovery.
>
> **WHAT R-U DID EARN, AND IT IS SUBSTANTIAL — CREDIT IT AT FULL WEIGHT.** All
> **three** jobs in its charter are genuinely repaired and green in 2298
> (`Ruff lint + format`, `Pinned default cache key`, `Structural refactor
> guards`), each by root cause, none by re-pinning, skipping or loosening a
> guard; the fast tier improves **56 → 33 failures with ZERO regressions across
> 51 changed files**; and **both R-P blockers are cleared**, so leg 4 is
> unlocked-pending-the-owner. **The advance is real. The leg-2 claim attached to
> it is not.**
>
> ### 🟢 v21 ALSO: THE OTHER TWO LANDINGS VERIFY CLEAN, AND **FULL ERCOT COVERAGE CLOSES THE 7-NOT-6 LINE**
>
> **Capture-B and R-O both check out against their dispatches with no gap.**
> R-O's config-partition schema is present in all three chartered surfaces
> (`capture_keeper_goldens.py`, `check_golden_manifest.py`,
> `tests/scoring/test_golden_manifest_provenance.py`), the ERCOT shard carries
> its `config_partition` block, and **`ERCOT__carveout-2023` →
> `2026-08-25-236-swcap-clip-k33` reports CURRENT** — so ERCOT is covered on
> **both** its configs and the board's *"the table is 7 rows, not 6"* line
> **closes**. **Stage-0 is 6 of 7 CURRENT, MISO the sole stale entry** — the
> dispatch's claim, confirmed at both of this lane's pins.
>
> ### 🟢 AND: **PERF-B MOVED — TWICE — DURING THIS LANE'S OWN SESSION. v20's J-9 IS SUPERSEDED.**
>
> v20 recorded *"No PERF-B surface has moved yet — `results/regression-goldens/`
> is byte-unchanged across the whole 29-PR window (J-9)."* **That is no longer
> true and must not be carried.** `perfb-campd-ercot-before` landed before this
> lane's first pin, and **`perfb-campd-ercot-after` landed *during* it** (#4595,
> `c428d49a`, *"ERCOT byte gate PASS (§5.5) — both normalizer grains now
> gated"*). The golden-manifest instrument moved **41 manifests / 74 entries /
> 10 enforced → 42 / 75 / 11** between this lane's two pins. **PERF-B's byte
> gate now covers both grains of `_normalize_campd`** — the facility-level (TX,
> no `unitId`) branch as well as the unit-level one.
>
> ### 🔴 AND: **G2 IS RED AT BOTH PINS, IT IS COMMITTED ON `main`, AND IT REDDENS EVERY PR — INCLUDING THIS ONE**
>
> `check_registry_payload_parity.py` **exit 1** on `results/calibration/miso200_control_A`.
> ⚠️ **It is NOT an untracked local artifact:** `git ls-tree` shows **14 files
> tracked at `origin/main`**, landed via #4591. The director's *"same transient
> class as caiso231"* reading is **correct and now verified rather than
> asserted** — caiso231 landed unregistered too and **both its sidecars are
> present today**, so the class resolves by registration. But **while it stands,
> the parity gate is a `pull_request` job, so it is red on every PR opened
> against `main`** — this board's own included. **Not this program's to fix**
> (calibration desk: register, prune, or allowlist).

---

> # 🟢 THE PROGRAM IS NO LONGER PARKED — R-V UN-PARKS THE GOLDEN TIER, RESUMES PERF-B, AND FREEZES THREE KEEPER LANES
>
> **REWRITTEN AT v20 (2026-09-02, pin `07472e7c`), REPLACING THE G1-PARK BLOCK
> THAT STOOD FOR EIGHT CYCLES.** Read the paragraph below it as history: the
> park it describes was declared 2026-08-22 and **lifted by owner ruling R-V at
> the 2026-09-01 third sitting**. Three things move at once, and the third is the
> price of the first two:
>
> 1. **THE GOLDEN TIER IS UN-PARKED.** The 2026-08-22 park is lifted; the CI
>    proof may be spent. ⚠️ **But un-parked is not exercised, and this lane
>    measured rather than assumed it: the owner has run NO `workflow_dispatch`
>    of `golden-data-tier.yml` at this pin** — the last dispatch of any kind was
>    **run #4, 2026-08-15**. **G2 leg 1 therefore still cannot be claimed**
>    (J-6).
> 2. **WS3 / PERF-B IS RESUMED.** WS3 moves from *paused ~82 %* to
>    **RESUMED-IN-PROGRESS**, and DOCS-B is queueable behind it. ⚠️ **No PERF-B
>    surface has moved yet** — `results/regression-goldens/` is byte-unchanged
>    across the whole 29-PR window (J-9).
> 3. **A KEEPER FREEZE IS DECLARED ON {ERCOT, NEISO, PJM}** — the three
>    `complete` / CALIBRATED / frontier ISOs, i.e. exactly the three whose stage-0
>    rows are CURRENT. **No promotion in those lanes** until PERF-B's byte-green
>    loop completes or the owner lifts it. **{MISO, CAISO, NYISO} are EXPLICITLY
>    UNFROZEN** and keep promoting — which is why this window's one keeper motion
>    (MISO `191 → 198`) is not a freeze breach (J-4, J-8).
>
> **WHAT IS STILL BLOCKED, AND BY WHAT.** The program does **not** advance to G2
> on this ruling. G2's four legs now read: **leg 1 IN MOTION** (un-parked,
> unexercised, no capture yet) · **leg 2 BLOCKED on R-U** — the `Fast test tier`
> job still fails on content · **leg 3 SATISFIED** for the three frozen ISOs ·
> **leg 4 BLOCKED on R-U, then the owner's Settings action**. **AUDIT-B** (G3)
> and **SITE-A** (G3) are still waiting by design. The FFR desk's **Q.2
> supersession battery** commissions at G2 (`ffr-owner-sitting-2026-08-02.md`
> AS.6) and **still does not fire**. Whoever resumes the work starts at the
> **RESTART CHECKLIST** at the bottom of this board, not at change (a).
>
> *(Superseded, retained as history — the block this replaces: "PROGRAM PARKED AT
> G1 BY OWNER DECISION — WS3/PERF PAUSED FOR CALIBRATION. This is not drift and
> nothing below is late. The owner paused WS3/PERF-B so the calibration program
> can run. PERF-B merged byte-green is a G2 precondition, so G2 cannot be declared
> while WS3 is paused and the program sits at G1 … The golden tier remains PARKED
> (owner ruling 2026-08-22, unchanged) … so G2 leg 1 has TWO parked dependencies —
> WS3/PERF-B and the golden tier — not one." **Both parks are lifted by R-V; leg 1
> is now blocked on execution, not on permission.**)*
>
> ### 🟢 NEW AT v17 — THE REFRESH SITTING'S FOUR RULINGS ARE ON THE RECORD, AND THREE OF THE FOUR ARE ALREADY *PAST* EXECUTION
>
> v16 recorded the 2026-08-30 decision cards executed. v17 records a **third
> sitting** — the 2026-08-31 **REFRESH** — whose seven rulings split into the
> three v16's post-pin block caught as *ruled* (**R-A / R-B / R-C**, all three
> now **EXECUTED AND MERGED**: #4442, #4439, #4431) and the four this records
> lane executes (**R-D / R-E / R-F / R-G**). **R-D rests the C-1 wind question**
> at this representation grain with a decision map; **R-G closes nyiso-160/leg2
> by archive**; **R-F parks the nyiso-161 card behind a dated trigger** — and
> **that trigger is already met at this pin** (F-3). **R-E's chartered Q1+Q2 have
> BOTH already reported**, Q1 **REAL** and Q2 **CONFIRM** (F-2).
>
> ### 🟢 AND: ERCOT IS DECLARED `complete` AND `frontier` — THE FIRST ERCOT RULE-22 MARKER EVER
>
> Re-derived at this pin, not carried: `complete` = **{ERCOT, NEISO, PJM}** and
> the active `frontier` set = **{ERCOT, NEISO, PJM}**. ERCOT reads **CALIBRATED**
> at ISO level under the ercot-246 two-config partition ruling. `final` is still
> **EMPTY**, no ISO has ever spent a locked-test year, and the freeze is still
> tier-scoped to the locked test. See F-4.
>
> ### 🔴 AND: FOUR-INSTRUMENT ALIGNMENT BROKE AGAIN THE MOMENT IT WAS RESTORED — AND THE OUTLIER IS AN INSTRUMENT, NOT A MODEL
>
> v16's headline was alignment restored at {PJM, NEISO}. One cycle later
> **three** instruments agree at **{ERCOT, NEISO, PJM}** — CALIBRATED, `complete`,
> `frontier` — and the **forecast gate-(a) passers are still {PJM, NEISO}**. The
> break is **not** a substantive disagreement: ERCOT's seed gate-(a) stamp names
> `2026-08-24-231-tie-zone-measured` against a live `234-eastex-identity`, i.e. it
> **fails on a stale stamp**. **Four of six seed stamps are stale** (ERCOT, CAISO,
> NYISO, MISO). See F-5.
>
> ### 🟢 v18 DELTA (2026-09-01, pin `6c7f82dac015`) — THE STALE-STAMP BREAK ABOVE IS NOW **REPAIRED**, AND ALIGNMENT IS RESTORED
>
> Read the two paragraphs above as **history**: the alignment break they describe
> was recorded at v17 and **executed at v18**. The owed half of owner ruling
> **R-I** is done — all four stale gate-(a) stamps re-keyed, and **ERCOT's leg
> moves `fail → PASS` on the marker**, so the gate-(a) passers are now
> **{ERCOT, PJM, NEISO}** = the full `complete` membership and **four-instrument
> alignment is RESTORED at {ERCOT, NEISO, PJM}**. Per R-I, ERCOT's row cites
> **both** determination values — partition rollup **CALIBRATED** and registered
> run-level **NOT-YET** — neither replacing the other. **No ISO's `open`
> changes.** Three further records repairs land with it, and **two of the three
> came back different from the dispatch**: the `ff-verdicts.json` provenance
> defect is **TWO instances, not one**, and it blinds the staleness anchor; and
> the cascade rule's *"no exposure in the other five ISOs"* finding is
> **OVERTURNED — MISO carries a live sibling defect**, found by #4485 after the
> director's pin. **The v18 block is a DELTA, not a refresh: every figure on this
> board outside those four jobs still carries its v17 pin `d44446e0` and is not
> re-verified.** See **D-1 … D-6**, immediately below.
>
> ### 🔴 v18b COMPLETION (2026-09-01, pin `192460b6`) — THE SITTING'S **SEVENTH** RULING, **R-H**, WAS STILL RECORDED NOWHERE — AND IT HAD ALREADY DECIDED THE CARD THIS BOARD'S QUEUE WAS SERVING
>
> The 2026-08-31 REFRESH sitting produced **SEVEN** rulings. v17 recorded four
> (R-D/R-E/R-F/R-G) on top of the three already merged (R-A/R-B/R-C); the v18
> delta above recorded **R-I**. **R-H reached no artifact at all** — verified at
> this pin before writing: `grep "R-H"` across `docs/` (excluding the rule ID
> `[R-HOLDOUT]`) returns **ZERO**, board and plan §8 included, *after* the v18
> delta landed.
>
> **This was not a cosmetic gap.** R-H **RULED the nyiso-161 winter-face waiver
> card — OPTION A, NOT-YET STANDS** — and **owner-queue item 1 still presented
> that card as *"servable at the next sitting, not waiting on anything."* The
> board was inviting the director to re-serve a card the owner had already
> decided**, which is exactly the failure the never-re-serve duty exists to
> prevent. **D-7 records the ruling; the queue item is RETIRED.**
>
> **And the v18 delta is itself an instance of the failure shape it named.**
> D-5(a) named *"landed but incomplete"* — and the lane that named it **omitted
> R-H**, as did a **second records lane running the same dispatch in parallel at
> the same pin** (D-8b). **Two independent lanes, the same blind spot,
> inherited from the same dispatch: parallelism is not a completeness check.**
>
> **One dated correction to D-4:** MISO's cascade defect was **LIVE when D-4 was
> written and is REPAIRED at this pin** (#4497). The finding stands; its tense
> does not (D-9).

> ### 🟢 v19 FULL REFRESH (2026-09-01, pin `72576ebe`) — TWO SITTINGS OF RECORDS DEBT CLEARED IN ONE LANE: **R-J THROUGH R-O ARE ALL ON THE RECORD**, TWO QUEUE ITEMS RETIRE, AND FOUR-INSTRUMENT ALIGNMENT **HOLDS**
>
> **This is a FULL refresh, not a delta.** Every figure below — keeper table,
> markers, sidecar walk, stage-0 table, all seven gates, the forecast board, the
> queue and the roster — is re-derived at **`72576ebe`**, this lane's own pin.
> The v18/v18b blocks below it are retained as history and their `d44446e0` /
> `6c7f82dac015` / `192460b6` figures are **not** carried forward.
>
> **THE SITTING'S SIX UNRECORDED RULINGS ARE NOW RECORDED — verified absent
> first.** `grep` of each label across `docs/` at the pin returned **ZERO
> occurrences for R-J, R-K, R-M, R-N and R-O**, and R-L existed only in the
> capture lane's own finding and the capx desk's ledger — never on this board or
> in plan §8. **G-1 … G-6 record all six.** Two of the six were already
> *executed* and merely unrecorded (R-J, R-N); two were executed by a dispatched
> lane (R-L) or superseded (R-K); **R-M is executed by this lane**; and **R-O's
> chartered lane has not launched** (G-6).
>
> ### 🟢 AND THE PROGRAM'S TWO OLDEST GATE DEFECTS ARE **FIXED IN CODE**, NOT MERELY DIAGNOSED
>
> R-J's four maintenance items all landed (#4495 ×3, #4502 ×1 — mapping verified
> from commits, not from the dispatch). The parity allowlist is replaced by a
> **class-level classifier**; the bench gate's **date-kind mismatch** — diagnosed
> and re-diagnosed across three board versions — is repaired at source; the
> stage-0 manifest carries **per-entry provenance (schema v2)** with all six shas
> recovered from history; and a **hard CI guard** now holds the forecast gate-(a)
> rows against the backcast store. **Checklist items 2, 10, 11 and 12 are
> discharged by execution, and queue item Q-1 retires with them.** (G-1.)
>
> ### 🟢 AND: STAGE-0 COVERAGE TRIPLED — 1 CURRENT / 5 STALE → **3 CURRENT / 3 STALE**
>
> R-L's capture lane took **NEISO and ERCOT-forward** — the owner's verbatim
> *"Just NEISO and ERCOT"*, deliberately against restart-checklist item 5, which
> **stands**. Both fidelity oracles **PASS with zero config drift**; schema v2 is
> proven by the captures (each changed only its own entry); rule 22 is clean.
> **`results/regression-goldens/` moved for the first time in three cycles**, so
> WS3's completion figure moves by measurement rather than by assumption (G-3,
> G-11). **ERCOT's 2023 carve-out config still has no golden** — the object R-O
> charters a schema lane to make representable.
>
> ### 🟢 AND: ALL SIX FORECAST GATE-(a) STAMPS ARE **CURRENT** — THE FIRST TIME IN PROGRAM HISTORY
>
> v17 reported four of six stale and the alignment broken *on a stamp*. At this
> pin **every one of the six `a_keeper_marker` rows names the live keeper**, the
> R-N micro-supersession having re-keyed the last of them (CAISO, after the new
> guard's **first real firing**). So **CALIBRATED = `complete` = active
> `frontier` = gate-(a) passers = {ERCOT, NEISO, PJM}** — four-instrument
> alignment **HOLDS**, and the three gate-(a) failures are now failures **on the
> merits** (determination / marker), not stamp artefacts. **This is the first
> cycle in which the divergence could not have been a bookkeeping lag.** (G-9.)
>
> ### 🟠 AND TWO JOBS OF THIS LANE'S OWN DISPATCH CAME BACK **ALREADY DONE OR MOVED**
>
> **The anchor repair (job 4) was a NO-OP at the pin**: `--fix-anchors` repairs
> **0**, the gate carries **0 WARNs**, and the ~243 the dispatch reported at
> `8462da22` had already been repaired — **digits-only, correctly, and entirely
> unannounced** — inside an unrelated capx forecast re-score, #4522 (G-8). And
> **R-M's target moved between dispatch and pin**: `neiso-t3` was re-scored onto a
> **reachable** sha, and the defective stamp migrated to a *different key*. The
> annotation was therefore applied **by sha, not by key name** — the dispatch's
> key list would have annotated one healthy verdict and missed one defective one
> (G-4). **"Trust nothing in this prompt" earned its place twice in one lane.**
>
> ### 🔴 AND THE DISPATCH-VS-LAUNCH CHECK IS NOW **3-FOR-3 ON NON-LAUNCHES IN ONE SITTING**
>
> Two prior dispatches of *this* lane never launched (recorded in the protocol
> section, per the director's re-issue), and **R-O's chartered schema lane shows
> no branch and no PR at this pin** (G-6). The R-L capture lane's own finding
> records that **its** first dispatch never launched either. **Four
> non-launches, one sitting.** The check is no longer a formality on this
> program; it is the single highest-yield step in the refresh protocol.

> ### 🟢 v19b SECOND-SITTING COMPLETION (2026-09-01, re-pinned at `f45766e4`) — **R-P, R-Q AND R-R** ARE RECORDED, AND R-P COMES WITH A **BLOCKER THE RULING'S OWN EVIDENCE DID NOT SEE**
>
> **The v19 block above is history and its `72576ebe` figures are superseded by
> re-derivation, not by assumption.** Every figure was re-measured at
> **`f45766e4`** (merge of #4535), stable across two polls, **not a forced
> update**. The window since v19 landed is **6 commits / 1 merged PR**, and the
> re-derivation confirms: keeper shards **all six byte-unmoved**, sidecars
> **60**, stage-0 **3 current / 3 stale**, markers unchanged, **all seven gate
> scripts still exit 0**. What changed is the ruling set.
>
> **THE SECOND SITTING'S THREE RULINGS, verified absent before writing** —
> `grep` of each label across `docs/` returned **ZERO for R-P, R-Q and R-R**:
> **R-P** flips branch protection now, fast gates only; **R-Q** dispatches two
> capture lanes for MISO/CAISO/NYISO; **R-R** convenes the G2 un-park sitting.
> **H-1 … H-6** record them.
>
> ### 🔴 AND THE ONE FINDING THIS LANE WOULD BE NEGLIGENT TO BURY: **THREE OF R-P's SEVEN REQUIRED CHECKS ARE RED ON `main` RIGHT NOW**
>
> R-P's amendment rests on *"7 gates holding green across 60+ PR windows"* — and
> that evidence is **true of a different set of seven**. The seven **audit-program
> gate scripts** all exit 0 at this pin. The seven **CI jobs** R-P proposes to
> require are not those seven: measured against **run 2278**, the most recent
> *completed* `ci.yml` run, **`Pinned default cache key`, `Ruff lint + format` and
> `Structural refactor guards` all FAIL** — and reproduce failing from
> base-branch content. **Flipping the ruleset as written freezes every merge on
> the repository**, which is precisely what memo §4 exists to prevent, arriving
> through §3 instead. A second, quieter blocker: the shrink guard is
> **path-filtered** and never reports on a docs-only PR, so requiring it strands
> every records-lane PR as *pending*. **The memo refresh is written as ruled and
> both blockers are attached to it** (H-1); the flip is the owner's Settings
> action and this lane performed none.
>
> ### 🔴 AND R-Q's TWO CAPTURE LANES HAVE **NOT LAUNCHED** — THE SITTING'S NON-LAUNCH COUNT IS NOW **SIX**
>
> Dispatch-vs-launch at this pin: **no Capture-A and no Capture-B branch exists**,
> no PR, and the stage-0 table they were dispatched to move is **byte-unchanged
> at 3 current / 3 stale**. Together with R-O's still-unlaunched schema lane and
> the four already recorded at v19, **six dispatches from this sitting produced no
> session** (H-3, H-6). **This is now the program's dominant failure mode, and it
> is not a measurement problem** — every one of the six was found by the same
> two-command check.

> ### 🟢 v20 FULL REFRESH (2026-09-02, pin `07472e7c`) — **THE THIRD SITTING'S FOUR RULINGS R-S…R-V ARE ON THE RECORD**, THE PROGRAM IS UN-PARKED, AND A KEEPER FREEZE IS DECLARED
>
> **This is a FULL refresh, not a delta.** Every figure below — keeper table,
> markers, sidecar walk, stage-0 table, all seven gates, the `ci.yml` job set, the
> forecast board, four-instrument alignment, the queue and the roster — is
> re-derived at **`07472e7c`** (merge of #4563), held stable across two polling
> rounds, **not a forced update** (`f45766e4` is an ancestor). The v19/v19b blocks
> below are retained as history and their `72576ebe` / `f45766e4` figures are
> **not** carried. **ZERO SOLVE** (rule 22 `[R-HOLDOUT]`): no LP, no year solved,
> no run registered, no re-scoring; no keeper shard, `calibration-complete.json`,
> `holdout-freeze.json` or `program-status.json` edit; rule 26
> `[R-MECH-MATRIX]` — no mechanism tested and **no matrix verdict, evidence
> string, fc posture or keeper stamp touched**. *(The v20 item prefix is `J-`;
> `I-` is skipped because `I-1` reads as a roman numeral and because the ruling
> label `R-I` already exists.)*
>
> **THE WINDOW IS THE LARGEST THIS BOARD HAS EVER REFRESHED OVER IN ONE STEP
> SINCE v19: 81 commits / 29 merged PRs** since v19b's pin. **The four rulings
> were verified absent before writing** — `grep` of each label across `docs/`
> returned **ZERO for R-S, R-T, R-U and R-V**. **J-1 … J-4 record them.**
>
> ### 🟢 R-T's DURABLE HALF IS THE ONE TO KEEP: **A KEEPER-PROMOTION PR NOW RE-KEYS THE GATE-(a) STAMP IN THE SAME PR**
>
> The executed half is small and spent — the director re-keyed MISO's stamp under
> a one-push grant (**#4561**, 5 changed lines, the guard's **THIRD** real firing,
> verdict unmoved, alignment held; verified `exit 0` here). **The routing half is
> permanent and it removes the defect class rather than the defect**: the
> promotion that created the staleness landed in **#4552**, and the stamp was
> re-keyed **nine PRs later** in #4561 — a nine-PR window in which the forecast
> board named a superseded keeper. From this event forward that window is **zero
> by construction**: re-keying is the *promoting lane's* duty, in its own PR, and
> the guard enforces it at PR time once branch protection lands. **Recorded on
> this board AND in `frontend/data/backcast/keepers/README.md`**, where promotion
> lanes actually read their duties (J-2).
>
> ### 🔴 AND THE FINDING THIS LANE WOULD BE NEGLIGENT TO BURY: **THE "PARKED" GOLDEN TIER HAS BEEN SPENDING ITSELF ON A CRON, AND FAILING, FOR THREE STRAIGHT WEEKS**
>
> This board has recorded for **seven cycles** that the golden tier's *"CI proof
> is **deliberately unspent**"*. Measured against the workflow's own run list:
> that is **false, and has been false since 2026-08-17**. Runs **#5 (08-17), #6
> (08-24) and #7 (08-31)** are all `schedule` events on `main`, and **all three
> are RED**. Run #7 provisioned `data/clean` successfully and then failed at
> **`Data-provisioned pytest tier (serial)`** — a **content** failure, not the
> OOM class #4071 fixed. So the tier was never idle: it was billing runner
> minutes weekly, failing weekly, and **no instrument on this program was looking
> at it** — the park was recorded as a *state* and never re-measured as one. It
> also lands squarely on CLAUDE.md's *"scheduled workflows spend money with
> nobody watching."* **R-V un-parks a tier that was already running and already
> red** (J-6).
>
> ### 🔴 AND R-U's THREE RED JOBS ARE STILL RED — **17 CI RUNS LATER, ON A LANE THAT NEVER LAUNCHED**
>
> R-P's blocker, re-measured on **run 2295** (the most recent *completed* `ci.yml`
> run at this pin, and the R-T re-key's own PR): **`Pinned default cache key`,
> `Ruff lint + format` and `Structural refactor guards` all still FAIL**, with
> **`Fast test tier`** a fourth — failing on content after running 8 min 18 s to
> completion. The job set is **4 green / 6 red**, identical in shape to run 2278.
> **R-U's chartered repair lane shows no branch and no PR** (J-3, J-11). **G2 leg
> 2 is blocked on precisely this**, and so, downstream, is R-P's flip.
>
> ### 🔴 AND THE NON-LAUNCH COUNT REACHES **NINE**, WITH THE INSTRUMENT NOW WEAKER THAN IT WAS
>
> Dispatch-vs-launch at this pin on all six open dispatches: **Capture-A,
> Capture-B, R-O, R-U and PERF-B show no branch and no PR**; only this records
> lane launched. Six from the second sitting plus **three re-issued or newly
> chartered at the third** (J-11). ⚠️ **AND THE INSTRUMENT HAS DEGRADED**: the
> session-roster tool is no longer in this desk's surface, so detection is now
> **git-only**. A lane that launched and died before its first push is
> **invisible**. Every "never launched" on this board is therefore, strictly,
> **"no branch and no PR at this pin"** — and that is said wherever it is
> asserted.
>
> ### 🟠 AND ONE FIGURE THE DISPATCH CARRIED RE-DERIVES **DIFFERENT — IN THE DIRECTION OF "IT NEVER HAPPENED"**
>
> The dispatch records the **243 anchor WARNs** as *"GONE — repaired by commit
> `f5b33644`, an out-of-program lane"*. `f5b33644` is real, and it is the
> capx-director-refresh lane's (Opus 5, #4531). But its own commit message says
> the guard *"reported 0 anchor warnings on `origin/main` and 236 after"* **its
> own previous commit** — and `f5b33644~1` is **not a first-parent commit of
> `main`**: the breakage and its repair merged together in #4531. **`main` never
> saw the broken state, the count was 236 rather than 243, and there was no
> defect on the board for an out-of-program lane to repair.** The WARNs were
> already 0 at v19b's pin. **A third consecutive dispatch has now carried an
> anchor-WARN figure that measurement does not support** (J-12).

> ### ⚡ POST-PIN MOTION (`07472e7c..9220243f`, measured while this board awaited merge) — **FOUR OF THE FIVE UNLAUNCHED DISPATCHES LAUNCHED WITHIN HOURS, AND TWO ARE ALREADY MERGED**
>
> **THE PIN WAS NOT MOVED.** Every figure in the v20 block and in the live tables
> below stands as measured at **`07472e7c`** and is not silently rewritten — this
> is an annotation, per the standing *pin once, then record motion* rule. `main`
> advanced to **`9220243f`**: **20 commits / 6 merged PRs (#4564–#4569)**.
> **Nothing material to the keeper table, markers, freeze, registry or stage-0
> COVERAGE moved** — those five surfaces show **0 commits** in this window too, so
> the keeper table, the marker block, the sidecar walk and the 3-current/3-stale
> count are all still current at `9220243f`. **What changed is the dispatch
> ledger, and it changed hard:**
>
> | dispatch | at the pin (J-11) | post-pin | evidence |
> |---|---|---|---|
> | **R-U CI-red repair** | no branch, no PR | 🟢 **LAUNCHED AND MERGED** | **#4564**, 54 files — the five ruff errors fixed (*"two are real latent defects"*), 46 files ruff-formatted, `STORAGE_TECH_AVAILABLE_YEAR` added to the frozen constants-facade inventory, `caiso_offer_surface_measured_ungrounded` registered in `_CACHE_KEY_OPTIONAL_FIELDS`, plus a finding doc |
> | **R-O schema lane** | no branch, no PR, third pin | 🟢 **LAUNCHED AND MERGED** | **#4567** — `check_golden_manifest.py` now resolves a `ERCOT__carveout-2023` partition key through `keepers/<ISO>.json`'s `config_partition.configs[]`, and `capture_keeper_goldens.py` can take one |
> | **PERF-B resume** | no branch, no PR | 🟠 **LAUNCHED, IN FLIGHT** | `claude/perf-b-apply-nabnpi` @ `94245d14`, **ahead of `main`**, unmerged |
> | **Capture-B (CAISO → NYISO)** | no branch, no PR | 🟠 **BRANCH CUT, NOTHING PUSHED** | `claude/stage0-capture-caiso-nyiso-vicx26` sits at **exactly `9220243f`** — zero commits of its own |
> | **Capture-A (MISO)** | no branch, no PR | 🔴 **STILL NO BRANCH** | the one dispatch of the five that has not appeared |
>
> **🟢 AND R-P's SECOND BLOCKER IS REPAIRED — BY NAME.** Commit `f0fb9ce4` removes
> the `paths:` filter from `file-integrity-guard`'s `pull_request` trigger so the
> check **always reports**, and its comment cites *"blocker 2 of owner ruling R-P
> (director board v19b, H-1)"* and warns not to re-add the filter without first
> taking the check out of the required set. **The `push` trigger keeps its filter
> — billed minutes, deliberately.** So of R-P's two blockers, **(b) is closed and
> (a) is closed pending a green CI run.** The flip itself remains the owner's
> Settings action and is still not live.
>
> **🟠 WHAT DID *NOT* MOVE, and it is the part that matters for G2 leg 1: R-O
> landed the SCHEMA, not a CAPTURE.** Re-derived at `9220243f`:
> `check_golden_manifest.py` **exit 0**, still **6 enforced entries / 3 stale**,
> and ERCOT's entry still carries **no partition key** — so **the 2023 carve-out
> is now REPRESENTABLE and still UNCOVERED**, and full coverage is still 7
> captures, not 6. `results/regression-goldens/` has **0 commits** across this
> window as well. **Stage-0 is unmoved at 3 current / 3 stale.**
>
> **🟠 AND THE MECHANISM-MATRIX ANCHORS WERE REPAIRED AGAIN — A FOURTH INSTANCE**
> (`0d090576`, *"the +19-line `scenarios.py` shift"*), taking path anchors
> **159 → 160**. Same shape as J-12's: a lane shifts `scenarios.py`, every anchor
> below it moves, the same lane repairs the digits in the same PR. **Four
> instances now say this is not an incident but a standing cost of storing line
> numbers against a file under active edit** — worth a director look at whether
> the anchor should be a line number at all. **Recorded, not adjudicated.**
>
> **THE HONEST READING OF THE NON-LAUNCH LEDGER, AND IT CUTS BOTH WAYS.** J-11's
> five negatives were **true at the pin** and are **not withdrawn** — but four of
> the five resolved within hours, so the count is a snapshot of dispatch *latency*,
> not of dispatches lost. ⚠️ **And this is precisely why the phrasing was weakened
> to *"no branch and no PR at this pin"*:** with the session-roster tool gone,
> git-only detection cannot distinguish a lane that never launched from one that
> had not yet pushed — and here it was overwhelmingly the latter. **Capture-B is
> the case in point: its branch exists and carries zero commits, a state that was
> invisible to the check minutes earlier and is barely visible now.** The one
> genuine outstanding non-launch is **Capture-A**.

> **STATUS: AT G1, UN-PARKED — WS3 RESUMED, G2 NOT DECLARED** ⬅ *(was "PARKED AT
> G1" for eight cycles; changed by R-V, not by progress against a gate)*. Live
> rollup maintained by the program-director session, updated on each owner
> "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v20):** **BASE SHA FOR EVERY FIGURE ON THIS BOARD: `07472e7c`**
(merge of #4563), derived live from `origin/main` on 2026-09-02 and **held
stable across two polling rounds**. **The fetch was NOT a forced update** —
`f45766e4` tests as an **ancestor** of the pin, as do both of the director's
derivation pins, `1aa8ac14` (merge of #4559) and `a6642a39` (merge of #4561).
**The director's pins are REACHABLE and STALE**: `1aa8ac14` by **10 commits**
and `a6642a39` by **5**. Every count below states the window it was measured
over. **Nothing is carried from the dispatch or from the v19b block unverified
— and one dispatched figure re-derives materially different (J-12).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since the v19b pin** (`f45766e4..07472e7c`) — the v20 window | 2026-09-01 → 2026-09-02 | **81** | **52** | **29** (#4530, #4536–#4563) |
| since the director's first pin (`1aa8ac14..07472e7c`) | 2026-09-02 | **10** | **6** | **4** (#4560–#4563) |
| since the director's post-pin (`a6642a39..07472e7c`) | 2026-09-02 | **5** | **3** | **2** (#4562, #4563) |

**LANE CLASSIFICATION OF THE 29 MERGED PRs — derived from branch name AND
commit subjects AND changed paths, never from the branch name alone**, and it
sums exactly:

| lane | PRs | count |
|---|---|--:|
| **MISO calibration** (`miso-st-gas-steam-chp-calibration`, `miso-mustrun-window-basis`, `miso-steam-bid-side`) | #4530, #4541, #4544, #4545, #4547, #4552, #4556, #4557, #4563 | **9** |
| **capx / forecast desk** (`capx-*`, director refresh, T3-golden-2, D20, D34, D36, T16-A) | #4536, #4537, #4543, #4546, #4548, #4550, #4555, #4558, #4559, #4562 | **10** |
| **CAISO calibration** (import depth / envelope / capacity derivation, backcast) | #4539, #4542, #4553, #4560 | **4** |
| **NYISO calibration** (nyiso-171/172/173) | #4540, #4549, #4551, #4554 | **4** |
| **audit program** (v19b's own records PR; the R-T gate-(a) re-key) | #4538, #4561 | **2** |
| | | **29** ✓ |

**KEEPER MOTION: ONE — MISO `2026-08-30-miso-191-bexit` → `2026-09-01-miso-198-oomlevel`**,
promoted at `86319e3f` in **#4552**. **RECORDED, NOT ADJUDICATED** (J-8). The
other **five shards are byte-unmoved** across the window (`git diff` over
`frontend/data/backcast/keepers/` returns MISO alone). **It is not a freeze
breach**: R-V's freeze covers {ERCOT, NEISO, PJM} and explicitly leaves MISO
unfrozen — and in any case the promotion **predates the ruling's record**.

**ZERO open PRs and ZERO branches ahead of `main`** at this pin: `ls-remote`
returns four heads, and all three non-`main` heads test as **ancestors of
`main`**. `list_pull_requests(state=open)` returns **[]**.

**Headline, one line: the third sitting's four rulings are recorded; R-V
un-parks the golden tier, resumes PERF-B and freezes {ERCOT, NEISO, PJM}; R-T's
routing half makes gate-(a) staleness structurally impossible at the source;
and the two things the rulings assumed were quiet turn out not to be — the
"unspent" golden tier has been failing on a weekly cron since 2026-08-17, and
R-U's three red jobs are unchanged 17 CI runs later on a lane that never
launched.**

*(The v19b snapshot below is retained verbatim as that cycle's record. Its
`f45766e4` figures are history.)*

**Snapshot (v19b, RETAINED AS HISTORY):** **BASE SHA FOR EVERY FIGURE IN THIS BLOCK: `f45766e4`**
(merge of #4535), derived live from `origin/main` on 2026-09-01 18:03 UTC and
**held stable across two polling rounds**. **The fetch was NOT a forced update**
(`12c34488..f45766e4`, fast-forward). **The v19 pin `72576ebe` is REACHABLE and
6 commits / 1 merged PR stale**; the director's two derivation pins `8462da22`
and `a40cfc68` are staler still. **Nothing is carried from the dispatch or from
the v19 block unverified — and the dispatch's figures were re-derived AGAIN,
with four of them different (H-5).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v19 LANDED** (`12c34488..f45766e4`) — the v19b window | 2026-09-01 17:47 → 17:54 UTC | **6** | **5** | **1** (#4535) |
| since the v19 pin (`72576ebe..f45766e4`) | same evening | **12** | **9** | **3** (#4533–#4535) |
| **the v19 cycle** (`d44446e0..72576ebe`) — retained below as history | 2026-08-31 → 2026-09-01 | **167** | **104** | **62** |

**The v19b window is one PR** (#4535, `nyiso-170`, a NYISO phase-0 **stop** that
touched no parameter and registered nothing), so the lane classification of the
62-PR v19 cycle below stands as measured and is not re-derived here. **What IS
re-derived at this pin, in full:** all six keeper shards (byte-compared —
**all six unmoved**), all six determinations and grade summaries, all eighteen
C3a(RT) magnitudes, the marker blocks, the 60-sidecar walk, the stage-0 table,
the forecast board's six gate rows, four-instrument alignment, and all seven
gate scripts.

**Keeper motion: NONE.** CAISO's `220 → 231` promotion is the v19 cycle's, already
recorded (G-10), and is **not** re-adjudicated here.

**ONE open PR** (#4530, `miso-198`) and **five branches ahead of `main`**, none
of them a capture lane (H-3).

**Headline, one line: the second sitting's three rulings are on the record; R-P's
memo refresh is written as ruled and carries two blockers its own evidence did
not see — three of its seven required checks are red on main today; R-Q's two
capture lanes never launched, taking the sitting's non-launch count to six; and
R-R's G2 un-park sitting is recorded convened-not-held.**

*(The v19 snapshot below is retained verbatim as that cycle's record. Its
`72576ebe` figures are history.)*

**Snapshot (v19, RETAINED AS HISTORY):** **BASE SHA FOR EVERY FIGURE IN THIS
BLOCK: `72576ebe`**
(merge of #4527), derived live from `origin/main` on 2026-09-01 17:16 UTC and
**held stable across two polling rounds** before the pin was taken. **The fetch
was NOT a forced update** (`main -> FETCH_HEAD`, fast-forward, both polls) —
recorded because v17's was, and a forced move is the one condition under which a
carried sha silently stops meaning what it meant. The director's two derivation
pins are both **REACHABLE and STALE**: `8462da22` (merge of #4520) by **7 merged
PRs** and `a40cfc68` (merge of #4523) by **4** (#4524–#4527). Every count below
states the window it was measured over. **Nothing is carried from the dispatch,
from board v17/v18/v18b, or from any table, unverified — and FOUR figures the
dispatch asserted are re-derived DIFFERENT (G-12).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v17's pin** (`d44446e0..72576ebe`) — the v19 cycle | 2026-08-31 04:26 → 2026-09-01 17:0x UTC | **167** | **104** | **62** (#4465–#4527, no #4480) |
| since the director's first pin (`8462da22..72576ebe`) | same window's tail | **20** | **13** | **7** (#4521–#4527) |
| since the director's post-pin (`a40cfc68..72576ebe`) — what moved after the prompt was re-issued | same | **11** | **7** | **4** (#4524–#4527) |

**Of the 62 merged PRs, classified per lane from the branch name AND the commits
AND the touched paths** (all three, per the v17 protocol amendment — and this
cycle the branch name alone would again have mis-filed six):

- **9 are this program's / 8 lanes**: #4465 (v18 delta), #4472 (the R-D closure
  map), #4488 (gate-(a) repair), #4495 (R-J's three gate repairs), #4498 (v18b),
  #4502 (R-J's stage-0 provenance repair), #4509 + #4517 (the R-L capture lane),
  #4523 (the R-N micro-supersession).
- **28 are the capx desk's / 18 lanes** — a DIFFERENT program: the 22 `capx-*`
  PRs, **plus #4467** and **plus the five PRs of `claude/market-sim-calibration-director-lckr9a`**.
- **25 are the calibration program's / 14 lanes**: MISO 11, NYISO 6, CAISO 5,
  ERCOT 1, cross-ISO 2 (#4466 the C3c charter audit, #4497 the xiso cascade scan).

⚠️ **THE BRANCH-NAME HAZARD REVERSED DIRECTION THIS CYCLE, AND IT IS WORSE IN
THIS DIRECTION.** v17 found *capx* branches wearing calibration-shaped names.
This cycle **`claude/market-sim-calibration-director-lckr9a` IS THE CAPX
DIRECTOR'S DESK** — every one of its commits is titled `capx-director r#22…r#26`
and it touches only `capx-director-{handoff,ledger,prompt-pack}` — and
**`claude/neiso-rc-repair-fymtkz` (#4467) IS A FORECAST/T1-X HINDCAST LANE**, not
a NEISO backcast lane: it writes `frontend/data/forecast`,
`frontend/data/hindcast`, `results/hindcast` and `scripts/register_forecast_run.py`.
Together they are **6 of the capx desk's 28 PRs**. Worse in this direction
because a *calibration*-shaped name in the calibration column looks correct and
raises no flag — v17's capx-shaped names at least announced themselves.
**#4467 is also the lane that minted both of R-M's unverifiable stamps** (G-4).

**Keeper motion: ONE promotion, in CAISO.** Re-derived rather than asserted: all
six `keeper` fields compared byte-for-byte at `d44446e0` and at the pin —
**CAISO `2026-08-26-caiso-220-c1-crosswalk` → `2026-09-01-caiso-231-b1-ungrounded`**
(#4515), the other five byte-identical. **No rule-22 D-5(b) re-key was owed**:
CAISO sits in the `withdrawn` block, not `complete`, and `audit_keepers.py`
returns **PASS 0/0** across the promotion. Recorded, **never adjudicated** (G-10).

**ONE open PR and TWO branches ahead of `main`** (live `list_pull_requests` +
`ls-remote` ancestry test at the pin): **#4530** (`miso-st-gas-steam-chp-calibration`,
opened 17:25 UTC — *after* the pin) and `capx-director-refresh-0z0e0f`. The R-N
lane's branch `claude/audit-program-director-irzj4a` is an **ancestry-tested
merged remnant**, i.e. the supersession is spent and closed. **No other
audit-program lane is running at this pin**; this records lane is the only one,
and it is the dispatched instrument of the standing deviation.

**Headline, one line: six rulings recorded for the first time, two queue items
retired, the program's two oldest gate defects fixed in code, stage-0 coverage
tripled, all six forecast gate-(a) stamps CURRENT and four-instrument alignment
holding at {ERCOT, NEISO, PJM} — while two of this lane's own six jobs came back
already-done or moved-since-dispatch, and the sitting's non-launch count reached
four.**

*(v17's snapshot block below is retained verbatim as that cycle's record. Its
`d44446e0` figures are history and are NOT this board's measurement.)*

**Snapshot (v17, RETAINED AS HISTORY):** **BASE SHA FOR EVERY FIGURE IN THIS
BLOCK: `d44446e0`**
(merge of #4464), derived live from `origin/main` on 2026-08-31 and **held stable
across two polling rounds** before the pin was taken. **The fetch that took it
was a FORCED UPDATE** (`3d8ea013...d44446e0 main -> origin/main (forced
update)`), recorded because a forced move of `main` is the one condition under
which a carried sha silently stops meaning what it meant. The director's own
derivation base **`4bdb2d60` (merge of #4454) is REACHABLE (ancestry-tested
inside `origin/main`) but 10 MERGED PRs STALE** (#4455–#4464), and unlike v16's
two-PR gap **this one moves real figures on this board** — the MISO keeper, the
ERCOT markers, three of the five gate readings and both C3c program answers all
landed inside it. Every count below states the window it was measured over.
**Nothing is carried from the dispatch, from board v16, or from any table,
unverified — and three figures the dispatch asserted are re-derived DIFFERENT
(F-8).**

| window | span | commits | non-merge | merged PRs |
|---|---|--:|--:|---|
| **since v16's pin** (`54ca19ae..d44446e0`) — the v17 cycle | 2026-08-31 00:19 → 04:26 UTC | **93** | **57** | **36** (#4429–#4464) |
| since v16's board LANDED (`e52b90a4..d44446e0`) | same day | **79** | **48** | **31** |
| **since the director's derivation** (`4bdb2d60..d44446e0`) — what moved after the prompt was written | same day | **23** | **13** | **10** (#4455–#4464) |

**Of the 36 merged PRs, classified per lane from BOTH the branch name and the
commits behind it** (v16 classified by branch name alone; that no longer
suffices — see the protocol amendment): **6 are this program's / 4 lanes**
(#4430/#4432/#4439 the R-B joint-wind lane, #4442 the R-A arming lane, #4431
the R-C re-verify lane, #4434 v16's own landing); **12 are the capx desk's /
8 lanes** (#4429, #4436, #4441, #4446, #4447, #4452, #4453, #4455, #4457,
#4458, #4460, #4461 — a DIFFERENT program); **18 are the calibration
program's / 10 lanes** (#4433, #4435, #4437, #4438, #4440, #4443, #4444,
#4445, #4448, #4449, #4450, #4451, #4454, #4456, #4459, #4462, #4463, #4464).
⚠️ **THREE capx lanes carry branch names that read as calibration work** —
`miso-t1h-retire-g3-regression` (capx-D3), `ercot-i3-slack-measure`
(capx D4-I3) and `calibration-workstream-relaunch` (the capx **director's own
refresh desk**, r#21) — **and account for 6 of the desk's 12 PRs.** A
branch-name-only classification would have mis-filed **half** the capx desk
into the calibration column.

**Keeper motion: ONE promotion, in MISO.** Re-derived rather than asserted: all
six `keeper` fields compared byte-for-byte at `54ca19ae` and at the pin —
**MISO `2026-08-30-miso-188-rvsscope` → `2026-08-30-miso-191-bexit`**, the other
five byte-identical. The keeper-shard byte-diff over the whole window is **two
files, +7/−1**: MISO's one-line keeper swap and **ERCOT's new six-line `frontier`
block**.

**ZERO open PRs** (live `list_pull_requests` at the pin) and **ZERO branches
ahead of `main`**: `ls-remote` returns **five** heads, and all four non-`main`
tips (`capx-d8-re-emission`, `miso-t1h-retire-g3-regression`,
`model-audit-director-workstream`, `pjm-164-c3c-phantom-audit`) are
**ancestry-tested INSIDE `origin/main`** — merged, not ahead. **No audit-program
lane is running at the pin**; this records lane is the only one, and it is the
dispatched instrument of the standing deviation.

**Headline, one line: all four refresh rulings executed — the ERCOT wind
question rested with a map, leg2 closed by archive, the nyiso-161 card parked
behind a trigger that has ALREADY fired, and the C3c program's Q1 and Q2 both
already answered (REAL, CONFIRM) and then INDEPENDENTLY REPLICATED post-pin —
while ERCOT took the program's first-ever ERCOT `complete`+`frontier` markers and
four-instrument alignment broke again on a STALE STAMP rather than on a model
fact.**

**⚡ POST-PIN RESOLUTION — ONE labelled follow-up measurement at `54d5772c`
(merge of #4466), taken under the v14 sanctioned exception because BOTH of
R-E's answers were INDEPENDENTLY REPLICATED while this board was being written.**
The pin readings above are NOT re-pinned; this block is the second labelled
state.

**A THIRD LANE ran R-E's Q1 AND Q2 in parallel, blind to the two that had
already answered them — and both verdicts SURVIVED.** Read from the landed
artifacts, not from a listing:

- **Q1 = REAL, replicated by a DIFFERENT CONSTRUCTION** (pjm-165,
  `docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md`). pjm-164 overlapped the
  model's C3c **tail hours** against the actual RT LMP tail; this lane overlapped
  the model's **positive-reserve-dual hours** against PJM's **published
  reserve-market record**. Four legs pjm-164 did not carry: the requirement is an
  **exact published identity in 26,229 family-hours**; the channel **never
  touches a penalty step** and is structurally bounded below the published $300
  one; the positive-dual hours coincide with PJM's posted shortage intervals at
  **75–91× base rate (p ≤ 9.7e-11)**; and the model **UNDER**-prices reality by
  **2.7–7×**. **No disagreement on the verdict.** F-2 stands, strengthened.
- **Q2 = CONFIRMED, and the replication is the more interesting one because it
  first got the OPPOSITE answer and RETRACTED it** (nyiso-165,
  `docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`). Running blind, it
  measured *"reality WAS NYCA-short"*, found nyiso-164's record afterwards,
  re-derived from the raw CSVs and **reproduced nyiso-164's numbers exactly** —
  NYCA-tier tail-hour mean **$306.74 / $254.62 / $393.31**, ceiling test **0 of
  65**. **nyiso-164 is right; the parallel lane's first reading was wrong**, and
  it says so in its own title. F-3's trigger reading is unaffected.
- **🔴 AND THE RETRACTION FOUND SOMETHING THIS BOARD SHOULD CARRY: TWO LIVE
  DEFECTS IN A COMMITTED CALIBRATION REFERENCE.**
  `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` is wrong on
  **both** counts — a cascade **sum** where the **max** is correct, and a
  positional `hoy` map that never localizes prevailing Eastern to the model's
  standard-time clock — in **every column, every year**. **Blast radius: NO
  keeper, NO scored result, NO determination** (its only consumer is the
  post-solve RCPF comparator for co-opt-off runs; `nyiso_rcpf_enabled` is False
  in the keeper and rule 19 `[R-ONE-MECH]` makes arming it alongside
  `energy_reserve_coopt` a hard error). **It is a trap for diagnostic sessions,
  not a defect in any result — and it caught one.** The repair is cheap and
  regenerable in-session from committed CSVs; the lane deliberately did **not**
  do it mid-audit and filed it for a data lane or an owner grant. **Recorded on
  this board's Watch, not adjudicated.**
- **🟢 The duplication is itself a finding, and the governance log now carries
  the cross-ISO synthesis both first-execution lanes deliberately deferred.**
  Three lanes, two questions, each executed twice in parallel by lanes that could
  not see each other — **and both replications agreed** (Q2 after correction).
  That is the strongest evidence this program has produced that a zero-solve
  measurement on committed artifacts reproduces.

**A statement about R-F's card, made by the replicating lane and RULED BY
NOBODY.** Its §6 records that the corrected Q2 result **strengthens** the
nyiso-161 card's characterisation of its **summer** half and removes an
objection to it: had the false positive stood, the summer face would have been a
published in-representation reserve-shortage quantity the model simply fails to
bind — a *defect*, not a model-class limitation — contradicting the card's own
phrase *"the ledgered C3c limitation"*. It does not stand. **Three
qualifications the lane states itself:** it bears only on the summer half (the
winter face's AORR identification block is untouched); it is about
*characterisation*, not arithmetic, caveat budget or the standing rule; and
**that lane rules nothing on the card**. **Neither does this board** — R-F parked
it for the DIRECTOR to re-serve, and F-3's reading is unchanged: the trigger is
met and the card is re-servable.

**Every keeper shard, `calibration-complete.json`, `holdout-freeze.json`, the
registry, `results/regression-goldens/`, `.github/workflows/` and `docs/audit/`
are verified BYTE-UNMOVED `d44446e0` → `54d5772c`**, so every keeper-table,
marker, holdout, stage-0 and workstream figure above stands unchanged.

**ALL FIVE GATES RE-RUN at `54d5772c`** (exit codes captured directly, unpiped):
audit_keepers **PASS 0/0** · parity **exit 0, 58 / 93 / 0** · matrix **exit 0,
194 + 49 + 153** (⬅ **+1 path anchor**, the new findings' citations) · staleness
**exit 0, Δ = 1 → 0**, and **stamped/scored 81/49 → 83/51** · bench **exit 0, 0
STALE, 19 of 20 with engine drift — unchanged**.

**Lane state at the second reading: FOUR merged PRs** (#4466 the c3c replication
lane, #4467 NEISO-RC-R Phase B, #4468 miso-194, #4469 the calibration director's
refresh), **and this lane's own branch is now the only one ahead of `main`.**

**Nothing else changes.** F-1…F-8, the keeper table, the stage-0 table, the
gates table, the forecast board and the queue are unaffected; **F-2's and F-3's
verdicts are confirmed rather than rewritten**, and this block reads as what
happened next.

## What moved — v23 (`dfc44d95..49bfbc49`, "the three-discharge cycle")

Director's pin `68690427`; **`origin/main` was `c73f78f5` at this lane's first
two-poll stability and `49bfbc49` by the time job 0 was pushed** — R-X and R-Y
launched, landed and merged *during this session*. Every number below is
re-derived at **`49bfbc49`**, two-poll stable, each gate invoked alone with `$?`
read unpiped. The v22→v23 span is **55 commits** across the two windows.

### M-1 · 🔴→🟢 JOB 0 — THE DISPATCH NAMED ONE ROW; THE PIN HAD **THREE**, AND ITS TARGET WAS ALREADY STALE

The dispatch's job 0 was: re-key MISO from `2026-09-01-miso-198-oomlevel` to
`2026-09-02-miso-200-unitroute`. Two things were false by the time this lane
measured them.

**(a) MISO's live keeper was not `200-unitroute`.** `keepers/MISO.json` at the
pin reads **`2026-09-02-miso-201-stbasis`** (#4630, `30a6518a`, 21:07Z) — MISO
promoted *twice* after R-T's own re-key. The dispatch's target was itself
superseded; re-keying to it would have left the gate red.

**(b) It was not one row.** `check_gate_a_provenance.py` **exit 1 naming three**:

| ISO | stamp cited | live keeper | promotion |
|---|---|---|---|
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` | **`2026-09-02-caiso-239-b1-stgas`** | #4634, `c0cf3790`, 22:59Z |
| MISO | `2026-09-01-miso-198-oomlevel` | **`2026-09-02-miso-201-stbasis`** | #4630, `30a6518a`, 21:07Z |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | **`2026-09-02-nyiso-177-vintage-matched`** | #4632, `3040e2e0`, 20:37Z |

**Why all three moved together, and why that is not scope creep.**
`tests/scoring/test_gate_a_provenance.py::test_live_board_passes` calls the
checker's `main([])`, so it passes **only when every row is current**. A
MISO-only re-key leaves the gate exit 1, the test red and the dispatch's own
stated acceptance criterion (*"check_gate_a_provenance exit 0 after"*)
**unreachable**. The extension from one row to three was put to the owner and
**taken as an explicit in-session decision** on that measurement — not assumed.
**R-X's finding independently routes exactly this three-ISO re-key to this lane
by name** (M-4).

**Executed to the R-N/R-T stamp pattern.** Verified structurally: **exactly 12
leaf paths change** — the three rows' `detail` / `read_live_at` / `corrected_by`
plus `gate_a_provenance.derived_at_{sha,date}` / `derived_by` — with the JSON key
set byte-identical and **`status` unmoved on all six rows**. All three ISOs read
**NOT-YET** and are **absent from `complete`** on both sides, so each leg fails
identically before and after: **nothing opened, nothing closed, nothing solved,
scored or registered.** ERCOT / PJM / NEISO are **byte-unchanged**. NYISO's
displaced `nyiso-159` provenance is **preserved inside the row** rather than
deleted, since it described that keeper and not this one. Post-edit:
`check_gate_a_provenance` **exit 0**, `check_forecast_staleness` **exit 0**,
`tests/scoring/test_gate_a_provenance.py` **13 passed**, and the fast tier's
remaining failure is **none** — the routed FR-22 item having been cleared by R-X.

### M-2 · 🔴 THE R-T ROUTING DUTY — RECORDED FAIRLY, AND THE DISPATCH'S CHARITABLE READING **DOES NOT SURVIVE THE TIMESTAMPS**

The dispatch asked this to be recorded fairly, offering that the miso-200
session *"plausibly predated the keepers/README.md note."* Re-derived, it did
not — and neither did any of the others:

| event | commit | UTC |
|---|---|---|
| R-T's own re-key | `f863458a` | 2026-09-02 **02:56** |
| keepers/README.md step-4 note lands | `9b1e96b2` | 2026-09-02 **03:28** |
| miso-200 promotion (#4614) | `ca59460e` | 2026-09-02 **17:14** |
| nyiso-177 promotion (#4632) | `3040e2e0` | 2026-09-02 **20:37** |
| miso-201 promotion (#4630) | `30a6518a` | 2026-09-02 **21:07** |
| caiso-239 promotion (#4634) | `c0cf3790` | 2026-09-02 **22:59** |

**FOUR consecutive promotions, every one 13 h or more after the note, none of
which re-keyed the stamp.** No `program-status.json` commit in that span is a
gate-(a) re-key. So the duty is not failing at the margin of a stale clone — it
is **not being read at all**, across three different ISO desks.

**⬅ INDEPENDENTLY CORROBORATED, BY A DESK THAT IS NOT THIS PROGRAM.** Open PR
**#4642** (capx-director refresh **r#32**, opened 02:07Z while this lane was
mid-session) reaches the identical finding from the capx side and raises it as
its own decision card **C-2**: *"three owner-track keeper promotions in one day
(CAISO caiso-239, MISO miso-201, NYISO nyiso-177) … all three skipped the R-T
gate-(a) re-key — guard fails x3."* **Three desks — R-X (M-4), this lane (M-1)
and the capx director — converged on the same three-row object from three
directions within hours.** That is not a records-hygiene complaint any more; it
is a systemic routing failure with three independent witnesses.

**The fair conclusion is the one the dispatch already reached, now with
evidence: the durable enforcement is the owner's branch-protection flip, not a
fifth desk grant.** The README's own words are *"there should not be a third"*;
this is the **fourth**, and it took three rows. A promoting lane cannot be
blamed for skipping a check that no gate blocks it on — **which is precisely
leg 4** (M-7).

### M-3 · 🟢 R-W **DISCHARGED IN FULL** — AND THE BOARD'S CI-COUNT LINEAGE IS CORRECTED HERE

`docs/FINDING-fast-tier-repair-2026-09.md`, PR #4611, merged `6d52fdc5`.
**11 of 12 CI-true main-content failures repaired by root cause; zero
regressions across 10 changed files; 7,704 → 7,717 passing.** The 12th — the
ERCOT FR-22 fork — was **routed with its remedies enumerated, not patched on
either side**; it declined the leg-2 claim in terms. **Credit it as the second
consecutive lane to hold that line** (R-U was the first), and R-X (M-4) makes
it four in a row across v21–v23.

**The 13th defect, found on the way, is the more valuable half.** §4b:
`tests/scoring/test_golden_manifest_provenance.py` loads
`scripts/capture_keeper_goldens.py` by path; that script pins
`MARKET_SIM_HIGHS_THREADS=1` **at import**, correct for its own CLI but leaking
into the whole pytest process. `model/lp/model.py` then sets `threads=1` on
every later LP and HiGHS refuses against a scheduler already sized at 2 —
`run()` returns `kError`, model status `Not Set`. **Bisected to a 42-file
prefix; reproduced verbatim outside the suite in a four-step `highspy` probe.**
CI has been green on it only by collection-order luck.

**THE BOARD'S COUNTS ARE CORRECTED, per R-W §7.5's routing to this lane.**
*"56 → 33"* and *"33 remaining"* were **local `-n 2` counts taken in a poisoned
container**, not measurements of `main`:

| pin | local | **CI (authoritative)** |
|---|--:|--:|
| R-U's pin (run 2298) | 33 | **9** |
| R-W's start (run 2319) | 91 / 204 | **12** |
| after R-W (runs 2322/2324) | 1 | **1** |

**Quote the CI column.** R-U's *zero-regression* diff is untouched by this — it
compared two runs under identical local conditions, which stays valid. With the
leak closed a local serial count is a valid measurement again, and it now agrees
with the runner to the digit.

### M-4 · 🟢 R-X **DISCHARGED** — GAP FILED, PARITY RED CLEARED, AND LEG 2 HANDED TO JOB 0

`docs/FINDING-fr22-gap-leg2-2026-09.md`, PR #4635 (`2ad85f2c`). **Dispatched AND
launched inside this lane's session** — the label returned zero artifacts at
`c73f78f5` and a merged PR at `49bfbc49`.

The owner ruled **file GAP declarations** on the
`ercot_storage_adaptive_expectation` + `ercot_adaptive_event_release` fork, the
FFR-1E route. **The wire-forward question was deliberately NOT decided** — it
routes to the capx/forecast desk (`runner.py` / `pipeline/solve.py` seam,
`p1_storage_discharge_cost`), filed and tracked rather than silenced. Three
things beyond the ruling's letter, all flagged as such by the lane itself:

- **The job was larger than R-W saw: seven unaccounted fields on `main`, not
  three** — three of the extra four were already armed at R-W's pin and **masked
  by the test's assertion order**.
- Two were accounted as `PARAMETER_OF` already-declared rows (bookkeeping, no
  disposition made); **one — `nyiso_seam_par_attribution` — was filed GAP as a
  same-class fork and explicitly marked as the one row beyond the ruling.**
- **`_FR22_OPEN_UNACCOUNTED` was REVIEWED, not extended** — exact, both members
  live, unchanged. No `BACKCAST_ONLY` claim, no forward wiring, no matrix edit.

**Run 2344: `Fast test tier` `1 failed, 7807 passed, 34 skipped, 2 xfailed` —
the parity test is GREEN.** The one red is job 0's object, *"present on `main`
since 22:57Z and outside this lane's permitted files."* **It refused the leg-2
claim itself** and wrote this lane's instruction verbatim: carry leg 2 as
*"BLOCKED on the caiso-239 / miso-201 / nyiso-177 forecast-board re-key (FR-22
gap filings landed, parity red cleared — #4635)."* **Two independent lanes
converged on the same three-row object from opposite directions.**

### M-5 · 🟢 R-Y **DISCHARGED** — THE GOLDEN TIER IS GREEN, AND THE CRON IS GONE

`docs/FINDING-golden-tier-repair-2026-09.md`, PR #4644 (`49bfbc49`). Also
**launched and merged inside this session**.

The 3-for-3 schedule reds were **three different defects, each merged between
one firing and the next** — and the board's standing suspects are **ruled out on
evidence**: not the 2026-08-16 history rewrite, not the corpus conversions, not
the R-J/R-O manifest-schema changes.

| run | cause |
|---|---|
| #5 (08-17) | `curate_lmp` int64/str dtype crash — already fixed by #4071 the same day |
| #6 (08-24) | ercot-231 added `data/raw/eia-930-interchange/` + a test reading it **without extending the sparse-checkout list**; the loud-failure guard turned the data-missing skip red — **the guard working as designed** |
| #7 (08-31) | that gap, **plus** an `integration` test still asserting NYISO's `complete` marker after the Q5-W withdrawal |

**The cron is REMOVED — `workflow_dispatch`-only, exactly as R-Y ruled.** The
billed-minutes point is recorded: a failing scheduled workflow on a private repo
was spending owner money unwatched, three firings running.

**The dispatch itself then earned its keep.** Run #8 went red on a **fourth,
never-attributed defect** — `curate_confirmed_retirements.py` completed every
write and validation then aborted at interpreter finalization (`terminate called
without an active exception`, exit -6), the intermittent teardown abort three
earlier sessions had logged and none had pinned. Mechanism: pandas hands Arrow a
Python file handle on the validate round-trip read and an Arrow IO thread
outlives finalization. **Fixed at the shared `clean_io.validate_clean` seam.**

**Run #9 (`33704730253`) is `success`** — 12m57s, **51 passed / 2 skipped / 0
failed**, guard reading *"no data-missing skips; golden ran and passed"*, the
ERCOT fleet-arrays golden byte-identical. **The first green tier run since
run #4 (2026-08-15), and the first ever on a head carrying the ercot-231 corpus
and the NYISO withdrawal.** Two dispatches were spent and the finding says why:
**the first surfaced a real defect; it was not a re-roll of a flake.**

**What it does NOT certify, in the finding's own words and worth repeating:** it
is **not** a byte-green certificate for the stage-0 keeper LP goldens. It makes
that certification *possible* — the instrument works again — it does not perform
it.

### M-6 · 🔴 STAGE-0 HAS **REGRESSED, 7-of-7 → 4-of-7** — ON THE SAME THREE PROMOTIONS

`check_golden_manifest.py` **exit 0** (the ratchet does not gate staleness):
**42 manifests, 75 entries, 11 enforced / 64 legacy, 0 pruned — and 3 STALE.**

| stage-0 row | golden | state |
|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | 🟢 CURRENT |
| `ERCOT__carveout-2023` | `2026-08-25-236-swcap-clip-k33` | 🟢 CURRENT |
| PJM | `2026-08-15-pjm-162-inputclock` | 🟢 CURRENT |
| NEISO | `2026-08-17-neiso-99-joint-p1` | 🟢 CURRENT |
| **CAISO** | `2026-09-01-caiso-231-b1-ungrounded` | 🔴 **STALE** → `239-b1-stgas` |
| **MISO** | `2026-09-01-miso-198-oomlevel` | 🔴 **STALE** → `201-stbasis` |
| **NYISO** | `2026-08-30-nyiso-159-loss-surface` | 🔴 **STALE** → `177-vintage-matched` |

**Independently confirmed by R-Y §8**, which reached 4-of-7 from its own reading.
This is the *same three promotions* as job 0 — one event, three instruments
(gate-(a) stamp, stage-0 manifest, and the fast-tier test). **Capture-A's MISO
capture is now a RE-capture**, and leg 1's "merged byte-green" cannot be claimed
against live keepers until these three are re-captured under the R-O partition
schema. **It is not this lane's to repair** (goldens are capture artifacts, not
records) — routed to the PERF-B/stage-0 lane.

### M-7 · 🔴 LEG 4 — THE FLIP IS STILL NOT LIVE, AND BLOCKER (a) HAS RE-REDDENED FROM A NEW DIRECTION

**Re-measured, not assumed: all 30 most recent completed `ci.yml` runs (2322–2350)
are `pull_request` events, and every one concluded `failure`** — against **13
merges** across the two windows. **v22's 30-for-30 measurement is confirmed
unchanged, on an entirely different set of 30 runs.**

R-X landed the lint rider (`b2ce045a`, `ruff format` on R-W §7.2's three files),
**and the job is red anyway** — from a source the board has not tracked before:

- **`ruff check`: 5 errors, ALL in per-run capx probe scripts** —
  `docs/handoffs/d37/grade-2026-09-02.py`, `d37/predecl-screen-grain-2026-09-02.py`,
  `d45/positions-from-ledgers-2026-09-03.py` (×2), `d45/published-positions-2026-09-03.py`
  (`E731` ×3, `E402`, `E401`).
- **`ruff format --check`: 10 files** would reformat — the format step is *skipped
  behind the failing lint step*, so the rider's three files are never even reached.

**This reframes blocker (a).** It is no longer a source-tree hygiene problem; it
is that **desks check per-run probe scripts into `docs/handoffs/` and those
scripts are linted.** R-U §3.3's *"re-reddens within minutes"* dynamic is now in
its third day and has changed shape. The flip is best taken immediately after a
green Ruff job; **that is a small, well-defined cleanup, and it is the last thing
standing between leg 4 and the owner's Settings action.**

### M-8 · 🟢 SEVEN GATE SCRIPTS AT `49bfbc49` — SIX EXIT 0, ONE EXIT 1 (AND THAT ONE IS JOB 0's)

Measured on **`main` content**, each invoked alone, `$?` read immediately, never
through a pipe.

| gate script | exit | reading at `49bfbc49` |
|---|--:|---|
| `audit_keepers.py --check` | **0** | **PASS — 0 failures, 0 warnings**; `complete` = {ERCOT, NEISO, PJM} |
| `check_registry_payload_parity.py` | **0** | 🟢 **REPAIRED** — 61 runs, 96 bundle dirs swept, 0 known-unsynced. v22's two dead bundles (`miso200_control_A`, `miso200_unitroute_B`) **resolved by registration in #4609**, exactly as v21 predicted the transient class would |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + 6 shards; anchors **195 field + 49 row + 161 path** (v22: 195/49/160 — **+1 path**); **0 WARNs**; keeper stamps + §5.x headers match every shard |
| `check_forecast_staleness.py` | **0** | ⬅ **Δ re-derives as `8 commit(s)` (threshold 10)** — v22 read `(unknown)`; **the L-10 blinding has lifted** · **110 stamped / 84 scored** (v22: 96/70) · **25 of 65** verdict stamps undated (unchanged count, wider base) · **35** config epochs (v22: 28) |
| `check_bench_freshness.py` | **0** | 20 parts, **0 STALE**, 20 with engine drift — ⬅ **at 24 engine commits** (v22: 17, v20: 6). Drift has quadrupled since v20 with **no bench part regenerated** |
| `check_gate_a_provenance.py` | **1** | 🔴 **THREE stale rows** — M-1. **Exit 0 on this lane's branch** |
| `check_golden_manifest.py` | **0** | 42 / 75 / 11 enforced, 0 pruned, **3 STALE** — M-6 (v22: 0 stale) |

**Six of seven green on `main`; the seventh is repaired on this lane's branch.**
Two gates carry silent degradation the exit codes do not show: **bench engine
drift 17 → 24** and **stage-0 0 → 3 stale**.

### M-9 · 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — RE-DERIVED, FAIL-CLOSED

| instrument | source | membership at `49bfbc49` |
|---|---|---|
| Determination = `CALIBRATED` | `status/<ISO>.js` | **{ERCOT, NEISO, PJM}** |
| Rule-22 `complete` marker | `calibration-complete.json` `complete` | **{ERCOT, NEISO, PJM}** |
| Active `frontier` | **`keepers/<ISO>.json`**, `withdrawn` honoured | **{ERCOT, NEISO, PJM}** — NYISO `frontier.withdrawn = 2026-08-30`; CAISO, MISO absent |
| Forecast gate-(a) passers | `program-status.json` `gate.a_keeper_marker.status` | **{ERCOT, NEISO, PJM}** |

**ALL FOUR AGREE**, and they agree **before and after job 0** — which is the
point of a stamp-only re-key. `final` is **EMPTY**: **no ISO holds a locked-test
grant**, consistent with rule 22 and NEISO's `locked_test` note reading *NEVER
GRANTED, NOT SPENT*. **v22's L-12 method note was heeded** — `frontier` was read
from `keepers/<ISO>.json`, never from `calibration-complete.json`.

### M-10 · 🟠 KEEPER MOTION: **THREE ISOs, FIVE PROMOTIONS** — RECORDED, NEVER ADJUDICATED, AND THE FREEZE IS INTACT

Across `68690427..49bfbc49`: **CAISO** `231-b1-ungrounded → 239-b1-stgas`;
**MISO** `198-oomlevel → 200-unitroute → 201-stbasis`; **NYISO**
`159-loss-surface → 177-vintage-matched` (by explicit owner ruling). All three
still read **NOT-YET**; **no determination moved into or out of `CALIBRATED`**.

**The R-V freeze on {ERCOT, NEISO, PJM} is NOT breached** — `git diff` over
`keepers/` and `status/` touches **only the three explicitly-unfrozen lanes**.
**This lane records the motion and adjudicates none of it**, per standing
practice.

### M-11 · 🟢 THE PROTOCOL'S YIELD, THIS CYCLE

v22 adopted *"a dispatch may not upgrade a lane's own claim"* and recommended
listing the runs of every workflow the board claims about. **Both fired here:**

1. **The dispatch's job 0 target was stale** — `keepers/MISO.json` named
   `201-stbasis`, not `200-unitroute` (M-1a). Re-reading the source beat quoting
   the instruction.
2. **The dispatch's G6 reading (`1`) was three** (M-1b) and its G7 reading
   (`6/7 current`) was **4/7** (M-6). Both re-derived, both different.
3. **`R-X` and `R-Y` returned zero artifacts at the first pin and merged PRs at
   the second** — the dispatch-vs-launch instrument caught the transition *only*
   because main was re-polled before writing. **G-14's non-launch tally does not
   advance this cycle; it goes the other way.**
4. **The charitable framing offered by the dispatch did not survive the
   timestamps** (M-2) — and is recorded as it fell, not as it was offered.
5. **No lane's claim was upgraded.** R-W, R-X and this lane all state leg 2
   **NOT SATISFIED**; the board does not say otherwise.

### M-12 · 🟢 RECORDS INTEGRITY — WHAT THIS LANE TOUCHED

**Touched:** `frontend/data/forecast/program-status.json` (job 0, three gate-(a)
rows + the provenance block, 12 leaf paths, verdicts unmoved), this board, and
release-plan §8.

**Verified NOT touched:** every `keepers/<ISO>.json`, every `status/<ISO>.js`,
`calibration-complete.json`, `holdout-freeze.json`, every mechanism-matrix shard,
every workflow under `.github/workflows/`, and every bundle, sidecar and registry
file. **No solve, no score, no registration.** Rule 27 blob verification was run
on the `program-status.json` push (1,156 lines): **remote blob sha ==
local, line counts equal.**

### M-13 · G2 ROLL-CALL AT `49bfbc49`

1. **PERF-B merged byte-green** — 🟠 **IN MOTION, AND UNBLOCKED FOR THE FIRST
   TIME.** R-Y repaired the instrument and **run #9 is green** (M-5) — *"merged
   byte-green" is no longer blocked on tooling.* What remains is the work:
   **(i)** the L-8 `markup` hand-back (471–601 s/yr, unattributed) adjudicated as
   a charter item; **(ii)** stage-0 back to **7-of-7** — now a *re*-capture of
   three (M-6); **(iii)** a `regression_gate.py --mode byte` run against those
   current goldens, in-session, never in CI.
2. **One completed fast-tier-green `ci.yml` run** — 🟢 **SATISFIED (M-15).**
   **Run 2351, `Fast test tier` `success`, `7823 passed / 0 failed`** — the first
   ever, produced by job 0's own PR run. The refusals walked the object down
   **12 → 1 → 1 → 0** across R-U, R-W, R-X and this lane. ⚠️ **It is satisfied,
   not secured:** the green rests on the gate-(a) stamp, and **four promotions in
   one day left that stamp stale** (M-2) — **the next promotion that skips the
   R-T duty re-reds this job.** Leg 2 and leg 4 are the same problem twice.
3. **A keeper freeze** — 🟢 **SATISFIED**, R-V holding; five promotions, all in
   unfrozen lanes (M-10).
4. **Branch-protection flip** — 🔴 **NOT LIVE**, re-measured 30-for-30 (M-7).
   Blocker (b) stays repaired; **blocker (a) has re-reddened from capx probe
   scripts under `docs/handoffs/`**, which is a small cleanup, not a program
   item. **Still the owner's Settings action alone.**

**Net: three owner rulings discharged in one cycle; leg 1's instrument is green
for the first time in nineteen days; LEG 2 IS SATISFIED for the first time
(M-15); leg 3 holds; leg 4 is unchanged and still the owner's. G2 now stands at
two legs met, one in motion, and one waiting on a Settings action.**

### M-14 · 🟢 WHAT A **G2 DECLARATION** WILL REQUIRE, AND THE DUTY THAT FOLLOWS IT

**Restated because the legs are now close enough that the bar matters.** G2 is
declarable only when **all four legs are verified AT ONE PIN, in one sitting, by
one lane** — never assembled from four cycles' separate readings:

1. **Leg 1** — a `regression_gate.py --mode byte` PASS against **7-of-7 current**
   stage-0 goldens, plus the PERF-B charter hand-back adjudicated. *Today: 4/7,
   gate not run.*
2. **Leg 2** — **one completed `ci.yml` run whose `Fast test tier` job concludes
   `success`**, quoted by run id and head sha from the API record. Not "required
   checks green", not a local pass. *Today: **MET** — run 2351, job
   `100498709463`, head `e8bc1990` (M-15). A declaring lane must still re-verify
   it at its own pin: the green depends on a stamp that goes stale on the next
   un-re-keyed promotion.*
3. **Leg 3** — the R-V freeze intact over the declaring window, `keepers/` and
   `status/` diffed. *Today: satisfied.*
4. **Leg 4** — branch protection **observably live**: a merge blocked by a red
   required check, or the ruleset read directly. **30-for-30 red-with-merges is
   the disproof standing today.** *Today: not live.*

**THE DECLARATION DUTY, unchanged and restated so it is not lost:** the PM
session that declares G2 **notifies the FFR desk**, because the **FFR Q.2
supersession battery is pinned to fire at G2** — it does not fire on its own and
has not fired. **DOCS-B dispatches behind that notification**, not before it.
**G2 is NOT declarable at this pin.**

### M-15 · 🟢🟢 **G2 LEG 2 IS SATISFIED — RUN 2351, `Fast test tier` = `success`. THE FIRST EVER, AND IT LANDED INSIDE THIS LANE.**

**This supersedes the "one merge away" framing written earlier in this same
cycle.** It is recorded as an amendment rather than by rewriting M-1 and M-13,
so the sequence stays legible: this lane wrote leg 2 as *blocked on job 0*, then
job 0's own PR run produced the green.

**The criterion, verbatim from board v21 and restated unchanged by both R-W and
R-X:** *"one completed fast-tier-green `ci.yml` run"* — **a completed `ci.yml`
run whose `Fast test tier` job concludes `success`.**

**The evidence, from the API record and nowhere else:**

| field | value |
|---|---|
| run | **2351**, id **`33707179376`**, event `pull_request`, PR **#4646** |
| head sha | **`e8bc1990`** — the job-0 commit alone |
| run status | **`completed`** |
| **`Fast test tier` job** | id **`100498709463`** — conclusion **`success`** |
| step *Fast pytest tier* | **`success`**, 02:20:29Z → 02:30:12Z (**9 m 43 s**) |
| pytest summary | **`7823 passed, 34 skipped, 2 xfailed, 23 warnings in 578.68s`** — **ZERO failures** |

**Every other required-class job is green in the same run:** `Rule-22 quarantine
gates`, `Cache-key registration guard`, `Pinned default cache key`, `Structural
refactor guards`, `Rule-28 mechanism-matrix guard`, **and `FR-21 forecast-board
staleness` — whose `check_gate_a_provenance` step is now `success`, the red that
job 0 was written to clear.**

**Stated with the same care the four refusals were.** The **run's** overall
conclusion is `failure`, on three jobs: `Ruff lint + format` (M-7's capx probe
scripts) and `FR-22 backcast->forecast parity` + `Forecast-invariant artifact
audit`, **both named DO-NOT-REQUIRE by H-1**. **The criterion has never been the
run's conclusion** — v21 refused run 2298 *because its job was red*, R-W wrote
*"the criterion is the job, not a test"*, and R-X refused run 2344 on the same
reading while its own chartered test was green. **On the criterion as written and
thrice restated, leg 2 is MET.** Two further honesty checks, both passing: it is
a **PR-branch run**, exactly as runs 2298, 2307 and 2344 were — the measurement
basis is unchanged, not relaxed; and the head content is **`main` plus the
three-row re-key and nothing else**, so **on merge it becomes `main`'s own
state** — this is not a branch-local artifact.

**How the object count actually walked down, across four lanes and three
cycles:** R-U 56→33 local (CI 9) · R-W **12 → 1** by root cause + the §4b
poisoner · R-X **1 → 1** with the object *swapped* (parity cleared, the re-key
exposed beneath it) · **this lane 1 → 0.** Not one of the four claimed a green it
did not have, and the fourth got one.

**What leg 2 now needs to STAY satisfied:** nothing, if #4646 merges — but the
green is only as durable as the gate-(a) stamp, which **four promotions in one
day left stale** (M-2). **The next keeper promotion that skips the R-T duty
re-reds this exact job.** Leg 2's satisfaction and leg 4's flip are therefore the
same problem seen twice, which is the strongest argument this board has yet
carried for the Settings action.

## What moved — v22 (`0653bf13..dfc44d95`, "the discharge-and-unstaffed cycle")

Director's pin `a5abe3fe`; **actual `origin/main` at this lane's poll `dfc44d95`**
(#4608), stable across three polls. The v21→v22 window is **13 merges**
(#4585…#4608); the director's four-commit window `a5abe3fe..dfc44d95` is called
out where it changes an answer. Every number below re-derived at `dfc44d95`.

### L-1 · 🔴 LEG 2 REFUSED A THIRD TIME — AND THIS LANE FOUND A NEWER RUN THAN THE ONE IT WAS SENT TO RE-CHECK

The dispatch pointed at v21's refusal on run 2298. **A newer completed run on the
same branch exists**, and the protocol's job is to measure at the pin rather than
inherit the citation. **Run 2307** (id `33590273632`, `claude/ci-red-repair-hn56lh`,
head `937c48ee`, completed 2026-09-02T04:28:51Z), read job-by-job from the API:

| job | conclusion | note |
|---|---|---|
| `Ruff lint + format` | 🟢 success | ⬅ **R-U charter job, GREEN** |
| `Pinned default cache key` | 🟢 success | ⬅ **R-U charter job, GREEN** |
| `Structural refactor guards` | 🟢 success | ⬅ **R-U charter job, GREEN** |
| `Rule-22 quarantine gates` | 🟢 success | incl. `check_registry_payload_parity` (branch predates L-10's bundles) |
| `Rule-28 mechanism-matrix guard` | 🟢 success | — |
| `Cache-key registration guard` | 🟢 success | — |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success | carries the hard `check_gate_a_provenance` step |
| **`Fast test tier`** | 🔴 **failure** | step *Fast pytest tier*, 04:19:23→04:28:47 = **9 min 24 s**, failed on **content** — ⬅ **G2 leg 2's blocker** |
| `FR-22 backcast→forecast parity` | 🔴 failure | **by design** |
| `Forecast-invariant artifact audit` | 🔴 failure | unverified |

**7 green / 3 red.** Leg 2's criterion is *one completed fast-tier-green `ci.yml`
run*; the fast tier is red. **The refusal now stands on three successively newer
runs — 2278, 2298, 2307 — and has never once been contradicted.**

### L-2 · 🟢 R-U IS **DISCHARGED IN FULL**, AND THAT IS A BETTER RESULT THAN v21 COULD REPORT

Run 2307 is **the first run in which all three R-U charter jobs are
simultaneously `success`**. Its lane merged as **#4564, #4573, #4578** and
`claude/ci-red-repair-hn56lh` is **deleted from the remote**. **Credit stands at
full weight and the charter is now complete, not merely advanced.** The leg-2
gap is therefore no longer *an open lane's omission* — it is *a closed lane's
residue*, which is exactly why L-3 matters more than it would have last cycle.

### L-3 · 🔴 R-W HAS **NOT LAUNCHED** — NON-LAUNCH #5, ON THE ONE ROUTE LEG 2 HAS

Dispatch-vs-launch, run at the pin on four independent instruments:

1. **Q-4 label sweep**: `R-W` returns **ZERO** hits across the board. Every label
   **R-A … R-V** returns ≥1 (R-A 10, R-B 5, R-C 6, R-D 14, R-E 9, R-F 11, R-G 6,
   R-H 21, R-I 12, R-J 35, R-K 6, R-L 37, R-M 17, R-N 15, R-O 44, R-P 37, R-Q 30,
   R-R 14, R-S 30, R-T 30, R-U 67, R-V 61). **R-W is new to the record and this
   entry is its first.**
2. **No remote branch** matching the fast-tier repair (`git ls-remote --heads`).
3. **ZERO open PRs repo-wide.**
4. **No merge in the window** touches the fast tier.

**G-14's tally reaches five.** ⚠️ **The compounding fact:** with R-U discharged
(L-2), **the job leg 2 actually requires now has a dedicated ruling and no
session at all** — the first time in this program that a gate leg's sole route
has been both correctly identified and entirely unstaffed.

### L-4 · 🔴 THE PARITY DEFECT **DOUBLED INSIDE THIS WINDOW** — IT IS REPRODUCING, NOT SITTING

`check_registry_payload_parity.py` **exit 1**, and it names **two** bundles where
the director's read named one:

| bundle | tracked on `origin/main`? | landed |
|---|---|---|
| `results/calibration/miso200_control_A` | **yes — 14 files** | #4591 |
| `results/calibration/miso200_unitroute_B` | **yes — 14 files** | ⬅ **#4607, INSIDE THIS WINDOW** (`e8a5a485`) |

Both are Class-E dead solve output: *"bundle dir maps to no retained sidecar
`bundle` field and is not keep-required"*. **Same lane (miso-200), same class,
one additional bundle per merge.** The director's *"route it to the calibration
desk HARDER"* is upheld and sharpened: **this is not a transient awaiting
registration, it is a lane emitting a new dead bundle on each push**, and while
it stands the `pull_request` parity job is red on **every PR the repository
opens**. Register, prune or allowlist remains **their** call — **not this
program's to fix** — but the cost is now doubling.

### L-5 · 🟢 STAGE-0 7/7 CURRENT AND CAPTURE-A CLEAN — WITH ONE COUNT CORRECTION TO THE FINDING ITSELF

`check_golden_manifest.py` **exit 0** at the pin: **42 manifests, 75 entries, 11
enforced / 64 legacy; of the enforced, 0 with a pruned provenance run and 0
stale.** The 11 enforced = **7 stage-0 rows + 4 PERF-B `campd` rows**. Every
stage-0 row names its ISO's live keeper, verified against `keepers/<ISO>.json`
independently of the gate:

| stage-0 entry | provenance run | keeper shard agrees |
|---|---|---|
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` | ✅ |
| ERCOT | `2026-08-25-234-eastex-identity` | ✅ |
| `ERCOT__carveout-2023` | `2026-08-25-236-swcap-clip-k33` | ✅ (R-O partition) |
| MISO | `2026-09-01-miso-198-oomlevel` | ✅ ⬅ Capture-A |
| NEISO | `2026-08-17-neiso-99-joint-p1` | ✅ |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | ✅ |
| PJM | `2026-08-15-pjm-162-inputclock` | ✅ |

**Capture-A (#4601, commit `980508344`) verifies completely against its
dispatch**: MISO captured against the run the dispatch named, manifest MISO entry
only, finding doc `docs/FINDING-stage0-capture-miso-2026-09.md` present, **oracle
result read from the finding — PASS, 271 flags identical, 0 drift**; no keeper
shard, marker, matrix shard, registry, freeze or `program-status.json` edit.

⚠️ **Correction to the finding, recorded because the board's count depends on
it.** Its headline reads *"Stage-0 coverage: 5 current / 1 stale → 6 current / 0
stale"* while its own sentence then enumerates **seven** entries. It does not
count `ERCOT__carveout-2023` as a row — the residue of the "6 rows" framing v21
closed. **The gate's 7 is authoritative. The finding's conclusion is unaffected**;
only its coverage arithmetic is one short.

**WHAT 7-OF-7 DOES NOT CLAIM, restated as instructed.** It is *manifest currency*
— each golden's provenance run is registered and matches the live keeper. It is
**NOT byte-green certification**, which requires the golden tier actually
exercised. See L-6: it has not been, and it is red.

### L-6 · 🔴 THE GOLDEN TIER: DIRECTOR'S READ CONFIRMED, WITH THE EMPHASIS CORRECTED

**7 runs ever.** Last `workflow_dispatch` = **run #4, 2026-08-15** (`success`) —
**the director's "no dispatch since run #4 of 2026-08-15" is confirmed exactly.**
But the runs after it are not absent, they are **red**:

| run | event | conclusion | date |
|---|---|--:|---|
| #5 | `schedule` | 🔴 failure | 2026-08-17 |
| #6 | `schedule` | 🔴 failure | 2026-08-24 |
| #7 | `schedule` | 🔴 failure | **2026-08-31 — post-dates R-V's un-park** |

**Three consecutive scheduled failures, the newest after the un-park.** So G2 leg
1 is not waiting on permission or on a button press: **byte-green has no working
instrument**, and un-parking did not give it one.

### L-7 · 🟢 PERF-B SESSION 1 CLOSE — CONFIRMED EXACTLY; AND ITS CHARTER QUESTION RE-DERIVES **DIFFERENT**

**Close confirmed:** five PRs — **#4571, #4577, #4579, #4587, #4595** — branch
`claude/perf-b-apply-nabnpi` **deleted**. All four `perfb-campd*` manifest rows
read CURRENT, so the `_normalize_campd` byte gate covers **both grains**
(NEISO unit-level, ERCOT facility-level/TX).

⚠️ **THE DISPATCH'S CHARTER QUESTION HAS A DIFFERENT ANSWER THAN IT PRESUMES.**
It asked which of the four charter items *remain unadjudicated*, naming three
candidates (ci.yml checkout residue, basis LUT, warm-start flip signature).
Derived from `docs/handoffs/perf-recheck-2026-08.md` **§5.1**, whose own heading
reads ***"The charter's four items, re-verified at HEAD — all four are
CLOSED"***: **ZERO remain unadjudicated.** Two were re-verified here against
source rather than against the doc:

| # | item | doc state | this lane's check |
|---|---|---|---|
| 1 | `results_write` refactor | LANDED | — (accepted) |
| 2 | `ci.yml` checkout change | LANDED, nothing open | ✅ **21 `sparse-checkout` blocks across 10 jobs; `fast-tests` carries `timeout-minutes: 20` (`ci.yml:389`)** |
| 3 | Exp-2 memoized-enum basis LUT | LANDED | ✅ **`_BASIS_STATUS_OBJS` at `model/lp/model.py:43`, indexed at `:1501-1502`** — exactly as cited |
| 4 | `forecast_xyear_warmstart` flip | CLOSED — no flip ships | ✅ substance holds (`forecast_xyear_warmstart: bool = True`) ⚠️ **line citation drifted: doc says `scenarios.py:13606`, actual `:13825` (+219)** |

**So the WS3-next charter starts from a clean slate, not from three open items.**
The one repair owed is a citation re-pin on item 4, not an investigation.

### L-8 · 🟠 THE PERF-B HAND-BACK, ONTO THE QUEUE AS A **CHARTER ITEM, NOT A LANE**

`markup` measures **471–601 s/yr** on the ERCOT arms against a `results_write` of
**8.3–11.4 s** — **~50× the phase PERF-B spent two sessions optimizing** — and is
**UNATTRIBUTED** (`perf-recheck-2026-08.md` §5.4 tail, the doc's own closing
observation, explicitly *"well outside this lane's scope"*). Recorded per the
dispatch as a **WS3-next-charter item**: **no branch, no prompt, no dispatch, and
it is not counted as a lane in the roster.** The hand-back's own framing, which
the queue entry preserves: *"recorded so the next charter starts from the
measurement rather than from §2.6's stale `compute_monthly_markup`: close the
flag."* **`results_write` is close to exhausted as a lever; `markup` is not.**

### L-9 · 🔴 THE SHALLOW-CLONE TRAP, HIT A **FOURTH** TIME — IN THIS LANE'S OWN CONTAINER — AND G-13's RULE IS **INSUFFICIENT AS WRITTEN**

`git rev-parse --is-shallow-repository` → **`true`** at session start. Remedied
exactly as G-13 prescribes: `git fetch --filter=tree:0 --unshallow`, **3.4 s**,
matching the v18b lane's measurement. **G-13's rule worked and should stay.**

⚠️ **BUT THE REMEDY INTRODUCES A SECOND TRAP THE RULE DOES NOT COVER, AND THIS
LANE HIT IT.** `--filter=tree:0` makes the clone **partial, with a promisor
remote** — so a bare reachability probe **silently fetches the object it is
testing for**. Measured here: `941f4983` and `8ba592814d92` both reported absent,
then reported **present** on a later probe, because an intervening
`git rev-parse` had lazily fetched them. **A probe that mutates its own answer is
worse than a shallow clone, because the second reading looks authoritative.**

> **THE RULE, EXTENDED — the missing second clause.** After un-shallowing, run
> every reachability probe as
> **`git rev-parse --verify <sha>^{commit}` + `git merge-base --is-ancestor`,
> under `GIT_NO_LAZY_FETCH=1`**, and confirm anything still absent **against the
> remote API**. This is also what CLAUDE.md's partial-clone rule already
> requires (*"never resolve a blob you do not intend to download"*) — G-13 and
> that rule are the same discipline and should be read together.

### L-10 · 🔴 THE `ff-verdicts.json` PROVENANCE DEFECT HAS **REGENERATED**, AND D-2's COUNT NO LONGER HOLDS

Re-measured with L-9's sound method, then **remote-confirmed one sha at a time**.
The file has **grown from D-2's 46 refs / 12 distinct to 53 refs / 17 distinct**.
Six distinct shas are not on `main`, and they fall into **two classes D-2 did not
separate**:

| sha | verdict(s) | refs | remote API | class |
|---|---|--:|---|---|
| `a67364c1aa2d` | `neiso-t3` | 1 | **No commit found** | **ABSENT** |
| `89dacc4c0343` | `neiso-t3-pre-fc5` | 1 | **No commit found** | **ABSENT** |
| `271ad606c3fd` | `neiso-t3-pre-fc6` | 1 | **No commit found** | **ABSENT** |
| `80327d08fc2a` | `miso-t1h` | 1 | ✅ resolves — *"capx D33: the coverage audit and the siting identification"*, 2026-09-02T06:10:37Z | **live, UNMERGED branch** |
| `8ba592814d92` | `caiso-t1f`, `ercot-t1f`, `ercot-t1x`, `miso-t1f-*`, … | **13** | ✅ resolves — FFR-3A-2, 2026-08-04 | **pre-rewrite orphan** |
| `941f4983` | six `*-ffr3a3-*` `solved_at_sha` | **6** | ✅ resolves — merge of #3396, 2026-08-04 | **pre-rewrite orphan** |

**Two findings the board should carry.**

**(a) The defect is REGENERATING, and the repair pattern is its source.** D-2
named `89dacc4c0343` on `neiso-t3`. That sha has since **moved to
`neiso-t3-pre-fc5`**, and **`neiso-t3` now carries a NEW unreachable sha,
`a67364c1aa2d`.** The verdict was re-scored **again**, from **another branch that
never merged**. D-2 counted 2 absent; there are now **3**, all NEISO T3, all
`scored_at_sha`. **Re-scoring from an unmerged branch is not a one-off slip — it
is this lane's standing method, and each repair mints a fresh dead reference.**

**(b) The instrument is still blind, but for a DIFFERENT reason than D-2
recorded.** The newest-scored anchor is now **`80327d08fc2a`, which is not
missing — it is real, dated today, and simply unmerged.**
`check_forecast_staleness.py` still prints *"Staleness is UNKNOWN, which is not
the same as fresh"*, and its **solve-affecting Δ reads `(unknown)` where v20 read
Δ = 0 of 10.** So the board's freshness reading is blinded by a **live branch**,
not by a lost commit — a strictly different repair. Meanwhile the two
**pre-rewrite orphans** (`8ba59281`, `941f4983`, **19 refs between them**) are the
expected residue of the **2026-08-16 history rewrite** CLAUDE.md warns about:
**dead by construction, not by lane error**, and not repairable by re-scoring.

→ **Q-2 IS NOT RETIRED. It is wider than when it was written, and it now has
three distinct sub-classes with three distinct repairs.**

### L-11 · 🟢 SEVEN GATE SCRIPTS AT `dfc44d95` — SIX EXIT 0, ONE EXIT 1

Each invoked on its own with `$?` read immediately, **never through a pipe**.

| gate script | exit | reading at `dfc44d95` |
|---|--:|---|
| `audit_keepers.py --check` | **0** | **PASS — 0 failures, 0 warnings**; `complete` = {ERCOT, NEISO, PJM} |
| `check_registry_payload_parity.py` | **1** | 🔴 **TWO dead bundles** — L-4. Director's read named one; the second landed in-window |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors **195 field + 49 row + 160 path** (v20: 194/49/159 — **+1 field, +1 path**); **0 WARNs — counted, not quoted** (v21 correctly refused the dispatch's "243"; on `main` it is **zero**). Keeper stamps + §5.x headers match every shard |
| `check_forecast_staleness.py` | **0** | ⬅ **Δ = `(unknown)`** (v20: **0 of 10**) — blinded per L-10(b) · **96 stamped / 70 scored** (v20: 91/65) · **25 of 59** verdict stamps undated (v20: 25 of 56) · **28** config epochs (v20: 26) · board inputs all present |
| `check_bench_freshness.py` | **0** | 20 parts, **0 STALE**, 20 with engine drift — ⬅ **at 17 engine commits (v20: 6)**; drift has nearly tripled while no bench part was regenerated |
| `check_gate_a_provenance.py` | **0** | **6 rows**: keeper identity + marker state match the backcast store; no determination read |
| `check_golden_manifest.py` | **0** | **42 / 75 / 11 enforced**, **0 pruned, 0 stale** among enforced — L-5. (v20: 38 / 70 / 6 enforced, 3 stale) |

**Six of seven green; the one red is not this program's to fix (L-4).**

### L-12 · 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — WITH A METHOD NOTE THAT NEARLY COST A WRONG READING

Re-derived independently from four sources, **fail-closed** (missing or
unparseable ⇒ **NOT** in the set):

| instrument | source | membership at `dfc44d95` |
|---|---|---|
| Determination = `CALIBRATED` | `status/<ISO>.js` | **{ERCOT, NEISO, PJM}** |
| Rule-22 `complete` marker | `calibration-complete.json` `complete` | **{ERCOT, NEISO, PJM}** |
| Active `frontier` | **`keepers/<ISO>.json`**, `withdrawn` honoured | **{ERCOT, NEISO, PJM}** — NYISO **WITHDRAWN**; CAISO, MISO **absent** |
| Forecast gate-(a) passers | `program-status.json` `gate.a_keeper_marker.status` | **{ERCOT, NEISO, PJM}** |

**ALL FOUR AGREE.** `final` is **EMPTY** — **no ISO holds a locked-test grant**,
consistent with CLAUDE.md rule 22 (`[R-HOLDOUT]`) and with NEISO's
`locked_test` note reading *NEVER GRANTED, NOT SPENT*.

⚠️ **METHOD NOTE, recorded because it nearly published a false break.** A first
pass read `frontier` from `calibration-complete.json` and returned **∅**,
printing **MISALIGNED**. The frontier block lives in **`keepers/<ISO>.json`**,
exactly as **G-9** states. **Fail-closed handling converts a parser miss into a
false MISALIGNED** — the safe direction, but still wrong. **An empty set from an
instrument that structurally cannot be empty is a parser bug until proven
otherwise.** Caught before publication; recorded so the next lane checks the
source before believing the break.

### L-13 · 🟢 KEEPER MOTION: **NONE** — AND THE R-V FREEZE IS NOT BREACHED

`git diff` over `keepers/` and `status/` is **empty across both windows** —
the director's `a5abe3fe..dfc44d95` **and** the full v21 window
`0653bf13..dfc44d95`. The freeze on **{ERCOT, NEISO, PJM}** is intact;
**{MISO, CAISO, NYISO} remain explicitly unfrozen and simply did not promote.**
The director's four-commit window contains, in total: one A/B arm bundle
(`miso200_unitroute_B`, which is L-4's second defect) and one NYISO probe script
(`nyiso176_input_artifact_reproducibility.py`). **No determination moved.**

### L-14 · 🟢 THE DIRECTOR'S LEG-2 DISPATCH ERROR — ACKNOWLEDGED, AND THE DURABLE LESSON ADOPTED

Recorded as instructed, as a **governance record and not a reproach**: the v21
dispatch compressed R-U's *"7 of 7 **required** checks green"* into a leg-2
satisfaction claim; v21 refused it on measurement; **the correction STANDS and
R-U's credit stands at full weight** — reinforced this cycle by L-2, where its
charter completes. The lesson is now in the **Refresh protocol** as a standing
rule:

> **A DISPATCH MAY NOT UPGRADE A LANE'S OWN CLAIM.** When a records instruction
> asserts more than the finding it cites asserts, the finding governs. R-U's own
> text — *"The run is not 'fully green' and this finding does not claim it is"* —
> was correct and complete; the error was entirely downstream of it.

**And the same instrument that caught it caught something this cycle:** L-7's
charter question and L-5's count both re-derived different from the dispatch, and
L-1 found a **newer run** than the one it was sent to re-check. **The protocol's
yield is holding.**

### L-15 · G2 ROLL-CALL AT `dfc44d95`

1. **PERF-B merged byte-green** — 🟠 **IN MOTION.** Session 1 closed byte-green
   per-change (five PRs, both `_normalize_campd` grains gated, atol=rtol=0);
   stage-0 is **7/7 current**. **Still blocked on the instrument, not the work:**
   the golden tier is un-parked, **unexercised since run #4**, and **red on its
   last three scheduled runs** (L-6). *Merged byte-green* remains uncertifiable.
2. **One completed fast-tier-green `ci.yml` run** — 🔴 **BLOCKED.** Refused a
   third time on run 2307 (L-1). **R-U discharged (L-2); R-W chartered and
   NOT LAUNCHED (L-3).** Leg 2's sole route is unstaffed.
3. **A keeper freeze** — 🟢 **SATISFIED**, R-V holding; no motion in either
   window (L-13).
4. **Branch-protection flip** — 🔴 **NOT LIVE**, now measured rather than
   assumed: 30-for-30 red `ci.yml` runs against 13 merges in-window. Blocker (a)
   is **repaired** (R-U's three jobs green, L-2) and blocker (b) was repaired by
   `f0fb9ce4`. **What remains is the owner's Settings action alone** — for the
   first time, with both blockers cleared in code.

**Net: leg 4's blockers are cleared and it now waits only on the owner; leg 2 is
unchanged in state but materially worse in staffing; legs 1 and 3 stand.**

## What moved — v21 (`07472e7c..0653bf13`, "the leg-2 refusal cycle")

**THIS IS A FULL REFRESH.** Every figure in this section — all seven gates, the
stage-0 table, the four instruments, the in-flight roster and the G2 roll-call —
is re-derived at **`0653bf13`**, this lane's own pin. The v20 block and below are
retained as history and their `07472e7c` figures are **not** carried forward.

**TWO PINS, DISCLOSED.** This lane pinned `0a3d22c7` at two-poll stability
(05:54:40 / 05:54:56 UTC) — **identical to the director's pin** — and derived the
landings, the gates and the alignment there. `main` then advanced to `0653bf13`
mid-session (#4593, #4594, #4595, all merged inside six minutes). **Rather than
publish a board six minutes stale on its most important in-flight item, this lane
re-pinned and re-derived all seven gates and the stage-0 table at `0653bf13`.**
Both readings are reported below wherever they differ; where no second figure is
given, the two pins agree.

### K-1 · 🔴 **G2 LEG 2: THE DISPATCH'S CENTRAL INSTRUCTION IS REFUSED ON EVIDENCE**

**Instructed:** *"THE GREEN COMPLETED RUN 2298 (id 33587007663) — record it as
G2 LEG 2 SATISFIED, retiring the 'leg 2 not satisfiable' correction it
supersedes."*

**Measured, from the Actions API at this pin:**

| run 2298 (`33587007663`), head `0b4bdb39` | |
|---|---|
| run-level `conclusion` | 🔴 **`failure`** |
| jobs green | **7** of 10 |
| jobs red | **3** — `FR-22 backcast->forecast parity`, `Forecast-invariant artifact audit`, **`Fast test tier`** |

**The leg's criterion, quoted from this board (v19b, and still on the page):**
*"one completed fast-tier-green `ci.yml` run"*. Run 2298 is **completed** and is
**not fast-tier-green**. **Leg 2 is therefore STILL BLOCKED**, and the v19b
correction is **re-confirmed on fresher evidence**, not retired.

**Three things this lane will not do, and why each matters:**

1. **It will not record leg 2 satisfied.** The claim fails against the leg's own
   stated criterion. A satisfied leg 2 is a G2 precondition; recording it falsely
   would put the program one instrument short of a G2 declaration it has not
   earned — and G2 declaration fires the FFR desk's **Q.2 supersession battery**
   (Q.2 duty, below). A false leg-2 does not stop at this board.
2. **It will not blame R-U.** R-U delivered its charter in full, and its finding
   §6 **states the limitation in the same table the dispatch drew the claim
   from**. The gap is between the finding and the dispatch, not inside the
   finding.
3. **It will not treat the fast tier's improvement as partial credit toward the
   leg.** 56 → 33 is a real by-product of a root-cause repair; the leg wants
   green, and 33 failures are not green. Partial credit on a binary leg is how a
   "blocked" quietly becomes a "satisfied" across two cycles.

### K-2 · 🟢 **J-11 VINDICATED — A RECORDS-LANE FORECAST CAME TRUE, VERBATIM**

J-11 (v20) recorded, before R-U ran: *"R-U names **three** jobs; **four** are
red-not-by-design, and the fourth is the gating one. Whether `Fast test tier` is
inside R-U's scope is **not adjudicated here** — it is recorded so the lane does
not discover it late,"* and, at the checklist: *"it is NOT in R-U's three, and it
is the job G2 leg 2 actually requires. Leaving it out leaves leg 2 blocked even
on a fully [successful R-U]."*

**Outcome: exactly that.** R-U's three went green; the fourth stayed red; leg 2
stayed blocked. **Record this as the scoping note working as designed** — the
warning converted a discovery into a confirmation. It also answers the question
J-11 declined to adjudicate: **`Fast test tier` was NOT in R-U's scope**, and the
finding routes it onward (§7, *"deferred by memo §3"*).

### K-3 · 🟢 **R-U LANDING — VERIFIED COMPLETE AGAINST ITS DISPATCH, WITH ONE CORRECTION**

Dispatch-vs-launch, then completeness-vs-dispatch:

| dispatch claim | verdict at pin |
|---|---|
| all three red jobs repaired | 🟢 **CONFIRMED** — `Ruff lint + format`, `Pinned default cache key`, `Structural refactor guards` all 🟢 in run 2298 |
| one shared root cause (`test_persisted_identity`) across cache-key-pin and refactor-guards | 🟢 **CONFIRMED** — §2/§4; the repair is a field *registration*, not a re-pin, and **not one pin literal was edited** |
| lint fixed under charter exclusions | 🟢 **CONFIRMED** — §3; and §3.3 records it **re-reddening 16 minutes after the parent merged**, routed to the owner as a charter question (`docs/handoffs/**/*.py` is not in `extend-exclude`) |
| shrink-guard evaluated (finding §5) | 🟢 **CONFIRMED** — verdict **"make it report"**: the `paths:` filter is removed from the `pull_request` trigger only; `push` keeps its filter. Semantics untouched (>30 % rule, deletion rule, ≥300-line threshold, fail-closed incomplete-scan, `intentional-shrink`) |
| "THE GREEN COMPLETED RUN 2298 … G2 LEG 2 SATISFIED" | 🔴 **REFUSED — K-1.** Run 2298 concluded **failure**; 7 of 7 **required** checks green ≠ fast-tier-green |

**Two by-products worth their own lines.** (a) **Zero regressions**: the fast
tier was run twice locally under identical conditions, branch vs `origin/main`,
and the failure sets diffed name-for-name — **56 → 33, the branch-only set
EMPTY** across 51 changed files. (b) **§5b's induced matrix regression** —
registering one field added 19 lines high in `scenarios.py` and staled 236
anchors at once, repaired with `--fix-anchors` and *proved* anchor-only
(digit-normalized pre/post images byte-identical, sole numeric delta **+19**,
all six ISO shards unmodified). **§5b called this "a standing tax on a heavily
crossed file" — and K-6 records the tax being paid again one day later.**

### K-4 · 🟢 **CAPTURE-B AND R-O — BOTH CLEAN; FULL ERCOT COVERAGE CLOSES THE 7-NOT-6 LINE**

**Capture-B (#4586 / #4590 / #4592).** `check_golden_manifest.py` reports
**CAISO → `2026-09-01-caiso-231-b1-ungrounded` CURRENT** and **NYISO →
`2026-08-30-nyiso-159-loss-surface` CURRENT**, each with its provenance run
registered. Matches dispatch; no gap.

**R-O (#4567 / #4576).** The config-partition schema is present in **all three**
chartered surfaces, verified by reading each rather than by trusting the
dispatch's list:

| surface | evidence at pin |
|---|---|
| capture tool — `scripts/capture_keeper_goldens.py` | **20** `config_partition` / `carveout` references |
| `scripts/check_golden_manifest.py` | **7**, incl. the dated module note *"Entry keys, and config partitions (2026-09-02)"* and the `<ISO>__<role>` key separator |
| `tests/scoring/test_golden_manifest_provenance.py` | **40** |
| `frontend/data/backcast/keepers/ERCOT.json` | carries the `config_partition` block with both roles and the owner's verbatim ruling |

**And the gate resolves the partition key end-to-end:
`ERCOT__carveout-2023` → `2026-08-25-236-swcap-clip-k33` — provenance run
registered, golden CURRENT.** With `ERCOT` → `2026-08-25-234-eastex-identity`
also CURRENT, **ERCOT is covered on both designated configs**. The board's
standing *"the stage-0 table is 7 rows, not 6"* line is **CLOSED**.

### K-5 · 🟢 **STAGE-0 AT `0653bf13`: 6 CURRENT / 1 STALE — MISO THE SOLE STALE ENTRY**

Read from `check_golden_manifest.py` (exit **0**), the instrument that owns this
table since R-J — not hand-recomputed alongside it. **Identical at both pins.**

| stage-0 entry | provenance run | state |
|---|---|---|
| `CAISO` | `2026-09-01-caiso-231-b1-ungrounded` | 🟢 CURRENT |
| `ERCOT` | `2026-08-25-234-eastex-identity` | 🟢 CURRENT |
| `ERCOT__carveout-2023` | `2026-08-25-236-swcap-clip-k33` | 🟢 CURRENT |
| `NEISO` | `2026-08-17-neiso-99-joint-p1` | 🟢 CURRENT |
| `NYISO` | `2026-08-30-nyiso-159-loss-surface` | 🟢 CURRENT |
| `PJM` | `2026-08-15-pjm-162-inputclock` | 🟢 CURRENT |
| **`MISO`** | `2026-08-16-miso-160-wefor-shape` | 🔴 **STALE** — provenance run **PRUNED** from the registry; live keeper `2026-09-01-miso-198-oomlevel` |

**Coverage went 3 current / 3 stale (v20) → 6 current / 1 stale.** The remaining
gap is **one capture**, and its lane has not launched (K-7).

### K-6 · 🟢 **ALL SEVEN GATE SCRIPTS RE-RUN AT `0653bf13` — EACH ALONE, `$?` READ DIRECTLY, NEVER THROUGH A PIPE**

Re-run in full at **both** pins with identical exit codes, so the three
intervening merges moved no gate. **This matches the director's read exit-for-exit.**

| gate script | exit | reading at `0653bf13` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, over `complete` = {ERCOT, NEISO, PJM} |
| `check_registry_payload_parity.py` | 🔴 **1** | **`results/calibration/miso200_control_A`** — bundle dir maps to no retained sidecar, not keep-required. **Live, committed, and PR-reddening** — K-8 |
| `check_golden_manifest.py` | **0** | ⬅ **42 manifests, 75 entries (11 enforced / 64 legacy)**; 1 pruned provenance, 1 stale. *(At `0a3d22c7`: 41 / 74 / 10 — the delta is PERF-B's `perfb-campd-ercot-after`, K-9)* |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + 6 ISO shards; keeper stamps + §5.x headers match every shard. ⬅ **243 WARNs** and **160 path anchors** *(v20: **0 WARNs**, 159 path)* — anchor line-number drift, **not** a matrix edit and **not** blocking |
| `check_forecast_staleness.py` | **0** | ⬅ **Δ = 1 of 10** *(v20: 0)* · ⬅ **25 of 58** verdict stamps undated *(v20: 25 of 56 — two added, none re-scored)* · ⬅ **27** config epochs *(v20: 26)* · newest scored `b67a5f3ad30c` @ 2026-09-02T04:59:19Z |
| `check_bench_freshness.py` | **0** | **20 parts, 0 STALE, 20 with engine drift** — unchanged in count, but the drift is now **13 engine commits** *(v20: 6)*, so the honest-reading WARN is widening |
| `check_gate_a_provenance.py` | **0** | **6 rows: keeper identity + marker state match the backcast store; no determination read.** Holds through the window |

⚠️ **THE 243 WARNs ARE §5b's PREDICTED TAX, PAID AGAIN — AND THIS IS ITS SECOND
INSTANCE IN TWO DAYS.** v20 recorded this gate at *"**0 WARNs**; `--fix-anchors`
repairs **0**"* and explicitly overturned a dispatch's "243 WARNs" claim as
in-branch-only (J-12). **At this pin 243 unresolvable anchors are real and on
`main`** — a *different* occurrence with a coincidentally equal count, caused by
later commits inserting lines into `scenarios.py`. R-U §5b named the mechanism
one day before: *"any PR adding lines high in `scenarios.py` inherits a red matrix
guard until it runs `--fix-anchors` … a standing tax on a heavily-crossed file."*
**The gate still exits 0** (the anchors are beyond the ratchet, and the field NAME
is the durable identifier), so this is a maintenance signal, not a break — but
**J-12's "0 WARNs" figure must not be re-quoted.**

### K-7 · 🟠 **IN-FLIGHT ROSTER AT `0653bf13` — TWO OWNER ACTIONS UNEXECUTED, ONE LANE UNLAUNCHED, ONE LANE LANDED**

**Observed, never performed.** Both owner actions were read from live evidence
per the dispatch's own instruction, by this board's conventions:

| item | state at pin | evidence — measured, not inferred |
|---|---|---|
| **R-P flip** (owner Settings) | 🔴 **UNEXECUTED** | **PR #4592 created 05:28:17Z, merged 05:28:23Z — 6 seconds.** No required check can have run; no ruleset is in force. *(R-U §8 independently: "no ruleset is in force at this pin".)* **Both R-P blockers are now cleared**, so the flip is unlocked and waiting on the owner alone |
| **golden-tier `workflow_dispatch`** (owner) | 🔴 **UNEXECUTED** | Workflow run list, all **7** runs ever: #1 08-14 dispatch 🔴 · #2 08-15 dispatch 🔴 · #3 08-15 dispatch 🟢 · #4 **08-15 dispatch 🟢 — the last dispatch of any kind** · #5 08-17 schedule 🔴 · #6 08-24 schedule 🔴 · #7 **08-31 schedule 🔴 — the last run of any kind**. ⚠️ **No run at all since R-V un-parked the tier on 2026-09-01**, and its last observation is **RED** |
| **Capture-A MISO** ("third issue 2026-09-02") | 🔴 **NOT LAUNCHED** | **Zero open PRs · zero open issues · two remote branches total** (`main` + `claude/caiso-backcast-structural-wnbteg`). No MISO capture branch exists. MISO stays the sole stale stage-0 entry (K-5) |
| **PERF-B** | 🟢 **LANDED, TWICE** | #4587 then **#4595 during this session**; branch `claude/perf-b-apply-nabnpi` is **merged and gone from the remote**, so the dispatch's "live branch" is stale. Gate 7 🟢. See K-9 |

**The dispatch listed PERF-B's branch as live and Capture-A MISO as an in-flight
issue; at this pin the repository shows two open PRs' worth of neither.** The
roster's honest shape is: **PERF-B done for this window, Capture-A never
started.**

### K-8 · 🔴 **G2 = 1 IS LIVE ON `main`, NOT A LOCAL ARTIFACT — AND IT REDDENS EVERY PR**

The director's read called this *"the same transient class as caiso231 two cycles
ago … re-derive at your pin and record transient-or-live."* **Both halves
answered:**

- **LIVE, and committed.** `git ls-tree -r origin/main` shows **14 tracked files**
  under `results/calibration/miso200_control_A`, landed via **#4591** (`345335f3`,
  *"miso-200: the A/B control leg"*). It is **not** an untracked working-tree
  leftover, and it does not clear by anyone's `git clean`.
- **Transient *by construction*, and the precedent is verified rather than
  quoted.** Only the **`_control_A`** leg exists — no `_B`, no sidecar — i.e. the
  MISO desk is mid-A/B and registration is the next step. The caiso231 precedent
  **resolved exactly that way**: it landed unregistered two cycles ago and
  **both** `2026-09-01-caiso-231-a0-control.json` and `-b1-ungrounded.json` are
  present today.
- ⚠️ **The consequence the director's note does not carry:
  `check_registry_payload_parity` runs in the `Rule-22 quarantine gates`
  **`pull_request`** job.** While the bundle stands unregistered, **every PR
  opened against `main` is red on that job — including this board's own PR.** A
  red cell on this lane's PR is this defect, not this lane's content.

**Not this program's to fix** (dispatch, and correct: it is the calibration
desk's bundle). The desk's three options are named by the gate itself: register
it, prune it, or record it in `KEEP_REQUIRED_UNMAPPED_BUNDLES`.

### K-9 · 🟢 **PERF-B: v20's J-9 IS SUPERSEDED — BOTH NORMALIZER GRAINS ARE NOW BYTE-GATED**

v20's J-9 read *"No PERF-B surface has moved yet — `results/regression-goldens/`
is byte-unchanged across the whole 29-PR window."* **Superseded; do not carry
it.** Two captures landed on either side of this lane's first pin:

- `perfb-campd-ercot-before` — the ERCOT byte-gate BEFORE arm (`819f2e6a`).
- `perfb-campd-ercot-after` — **landed during this session** (#4595, `c428d49a`):
  *"ERCOT byte gate PASS (§5.5) — both normalizer grains now gated."*

The commit's own evidence: keeper `2026-08-25-234-eastex-identity`, **full 8760 ×
2023–2025**, arms differing only in `campd.py`; `regression_gate.py --mode byte`
check [1] **PASS** (9 files, 34 numeric columns, `atol=rtol=0`), **zero reshuffle
in all three years**, smoke PASS, `audit_keepers` PASS, manifest pre-screen 10/10,
both arms fidelity OK (271 flags identical, 751 scenario_config matched, 0
drifted). **Why ERCOT matters specifically:** a TX extract is *facility-level* and
carries no `unitId`, so it takes the `_normalize_campd` branch that NEISO's
unit-level files never enter — **both grains of the normalizer are now covered by
a full-8760 byte gate.** Check [4] fails on a byte-identical NYISO text already
attributed to control (§5.3), **pre-existing on `main`, unrelated to the branch**.

**Consequence for G2 leg 1:** PERF-B's byte-green loop is materially advanced —
this is the leg's substantive content — but leg 1 also wants the **MISO golden**
(K-5, uncaptured) and the **tier exercised** (K-7, undispatched since 08-15 and
red on its last run). **Leg 1 remains IN MOTION, not satisfied.**

### K-10 · 🟢 **FOUR-INSTRUMENT ALIGNMENT RE-DERIVED — HOLDS AT {ERCOT, NEISO, PJM}**

Re-derived from committed artifacts at this pin, never carried. **Matches the
director's read.**

| ISO | determination | `complete` | active `frontier` | forecast gate-(a) | aligned |
|---|---|---|---|---|---|
| **ERCOT** | CALIBRATED (ISO level, two-config partition) | 🟢 | 🟢 2026-08-31 | 🟢 pass | 🟢 **4/4** |
| **NEISO** | CALIBRATED | 🟢 | 🟢 2026-07-11 | 🟢 pass | 🟢 **4/4** |
| **PJM** | CALIBRATED | 🟢 | 🟢 2026-07-31 | 🟢 pass | 🟢 **4/4** |
| CAISO | NOT-YET | — | absent | fail (closed on absence from `complete`) | — |
| MISO | NOT-YET | — | absent | fail (closed on absence from `complete`) | — |
| NYISO | NOT-YET | — | **WITHDRAWN 2026-08-30** | fail (closed on absence from `complete`) | — |

**`final` is EMPTY** — `calibration-complete.json`'s `final` block holds only its
`_note`, so **no ISO has ever spent a locked-test year**, and the tier-scoped
freeze still covers 2019 / H1-2026 for all six. **Fail-closed nulls confirmed:**
every non-passing gate-(a) row fails *closed* on absence from `complete`, not on a
missing or unreadable value. **All six gate-(a) keeper stamps name the live
keeper** — the v17 stale-stamp defect stays repaired through this window.

### K-11 · 🔴 **THE G2 ROLL-CALL, REWRITTEN AT `0653bf13`**

| leg | state | what actually stands between here and satisfied |
|---|---|---|
| **1 — golden tier exercised / PERF-B byte-green** | 🟠 **IN MOTION** | Un-parked by R-V, **still unexercised** (no dispatch since 2026-08-15; last run 08-31 **RED**). PERF-B byte gate now **PASS on both grains** (K-9). Wants: the **MISO golden** (one capture, lane unlaunched) **+ the tier dispatched and green** |
| **2 — one completed fast-tier-green `ci.yml` run** | 🔴 **BLOCKED — UNCHANGED** | Run 2298's `Fast test tier` 🔴 (**33** failures, down from 56). **The dispatch's "SATISFIED" is refused (K-1); the v19b correction is re-confirmed, not retired.** Wants: the fast tier green — a defect lane nobody currently owns (R-U routed it, memo §3 deferred it) |
| **3 — keeper stability across the frozen ISOs** | 🟢 **SATISFIED-AS-SCOPED** | R-V's freeze on {ERCOT, NEISO, PJM}; zero promotions in the frozen three this window (G6 clean, no new stale stamps). ⚠️ **Scope is the whole claim** — {MISO, CAISO, NYISO} keep promoting by design, and the freeze is **prose-enforced only** (no gate script reads it) |
| **4 — branch protection / required checks** | 🟠 **UNLOCKED, PENDING THE OWNER** | **Both R-P blockers cleared by R-U** (7 of 7 required green; shrink guard now always reports). **The flip itself is the owner's Settings action and is UNEXECUTED** — measured at 6 s merge-to-create on #4592 (K-7) |

**G2 IS NOT DECLARABLE AT THIS PIN.** Legs 1 and 2 are substantive work, leg 4 is
an owner action; only leg 3 is closed, and only within its declared scope.

### K-12 · 🟢 **THE G2-DECLARATION DUTY, RESTATED SO IT IS NOT LOST**

**On declaration — not before — the PM session notifies the FFR desk**, whose
**Q.2 supersession battery** is pinned to commission at G2
(`docs/handoffs/ffr-owner-sitting-2026-08-02.md` AS.6; plan §2). **It still does
not fire**, and K-11 is why. Recorded here because the duty has now survived
several board versions without being actioned, and a leg-2 miscount (K-1) would
have fired it early.

### K-13 · 🟢 **Q-4 PROTOCOL EXECUTED — ALL 22 RULING LABELS PRESENT, NO R-H-CLASS GAP**

Every label **R-A … R-V** was grepped across the board **and** plan §8 before
closing. **All 22 appear in both** (board range 5–60 occurrences, plan 2–16).
**No ruling reached this cycle unrecorded** — the v18b failure shape (R-H ruled,
recorded nowhere, in two parallel lanes at once) **does not repeat**. The one
recording gap this cycle is of a different kind and is corrected in place: the
dispatch's leg-2 claim (K-1).

---

## What moved — v20 (`f45766e4..07472e7c`, "the un-park cycle")

**Every figure re-derived at `07472e7c`.** Item prefix `J-` (see the v20 block
for why `I-` is skipped).

### J-1 · 🟢 RULING **R-S** — "JUST SEND THEM ALL AGAIN": NO DEVIATION CHANGE, THE THREE SOLVE PROMPTS RE-ISSUED AS **SECOND** ISSUES

**Owner, verbatim: *"Just send them all again."*** Recorded here for the first
time (`grep "R-S"` across `docs/` returned **ZERO** before this edit).

**The sitting's opening state was the failure mode, and it is the reason the
ruling exists.** v19b closed with **six dispatches from the 2026-09-01 sittings
that had produced no session** — R-O's schema lane, R-Q's Capture-A and
Capture-B, two consecutive dispatches of the v19 records lane, and the R-L
capture lane's own first dispatch. R-S is the owner's disposition of that state,
and it is deliberately **minimal**: **re-issue, change nothing else.**

**What R-S DID rule:**
- **The three solve prompts are re-issued** — **Capture-A** (MISO stage-0
  capture, its **target updated to `2026-09-01-miso-198-oomlevel`**, since the
  keeper R-Q named has since been superseded), **Capture-B** (CAISO → NYISO), and
  **R-O**'s config-partition schema lane. Each is now a **SECOND issue**, and is
  counted as such in the non-launch ledger (J-11).
- **No deviation change.** The R-L standing deviation — *a stage-0 capture lane
  registers nothing on the backcast dashboard* (adopted at v19 G-3) — is
  **untouched**, and the staleness / no-consumer caveats the owner accepted on
  R-Q's card carry forward unchanged.

**What R-S did NOT rule, stated so nobody reads more into it:** it did not
diagnose *why* the six did not launch, did not change how lanes are dispatched,
and did not amend the capture scope. It re-sends the same work. ⚠️ **The
target-id update on Capture-A is the one substantive edit**, and it is a
consequence of MISO promoting (J-8), not a scope change.

### J-2 · 🟢 RULING **R-T** — THE MISO GATE-(a) RE-KEY IS **EXECUTED AND SPENT**; ITS **ROUTING HALF** IS THE DURABLE PART

Recorded here for the first time (`grep "R-T"` → **ZERO** before this edit).
**Two halves, and the board must not let the small one eclipse the large one.**

**(a) THE EXECUTED HALF — SPENT, verified rather than taken from the dispatch.**
Under a **one-push grant** (the R-N pattern), the director re-keyed MISO's
forecast gate-(a) stamp. Commit **`f863458a`**, PR **#4561**, and the diff is
exactly what was authorised: **`frontend/data/forecast/program-status.json`
alone, 5 insertions / 5 deletions, one file.** Its commit message records the
firing count and this lane confirms the end state:

- **The guard's THIRD real firing** — `check_gate_a_provenance.py` exit 1 at the
  director refresh, **exit 0 after**. **Re-run here at the v20 pin: `exit 0`, 6
  rows, keeper identity + marker state match the backcast store.**
- **VERDICT UNMOVED.** MISO's leg (a) reads **`fail` before and after** — NOT-YET
  determination, absent from `complete`. The re-key repaired the *stamp*, not the
  *verdict*, which is the whole point of a provenance guard that **reads no
  determination**.
- **ALIGNMENT HELD.** Gate-(a) passers stay **{ERCOT, PJM, NEISO}** (J-7).

**(b) THE ROUTING HALF — DURABLE, AND IT IS WHY THIS RULING MATTERS.** ⬅ **FROM
THIS EVENT FORWARD, A KEEPER-PROMOTION PR RE-KEYS THE GATE-(a) STAMP IN THE SAME
PR.** It is the **promoting lane's duty**, not a follow-up and not the director's;
the guard enforces it at PR time once branch protection lands (R-P).

**The gap this closes is measured, not hypothetical.** The MISO promotion landed
at `86319e3f` in **#4552**; the stamp was re-keyed in **#4561** — **nine merged
PRs later**. For that whole window the forecast board's MISO row named a keeper
the backcast store had superseded. Under R-T's routing that window is **zero by
construction**. This is the **third** instance of the same class (v17's four
stale stamps, R-N's CAISO one-push, R-T's MISO one-push): the first two were
repaired *downstream*, and this is the first to be routed *at the source*. **The
duty is recorded on this board AND appended to
`frontend/data/backcast/keepers/README.md`** — the file a promoting lane
actually reads its steps from, where duty (b) now sits alongside the
`build_status.py` step it belongs next to.

### J-3 · 🟠 RULING **R-U** — THE CI-RED REPAIR LANE IS **CHARTERED**, AND IT HAS **NOT LAUNCHED**

Recorded here for the first time (`grep "R-U"` → **ZERO** before this edit).
R-U charters a lane to repair the CI jobs v19b's H-1 found red on `main` —
**`Pinned default cache key`, `Ruff lint + format`, `Structural refactor
guards`** — the three that block R-P's branch-protection flip.

**DISPATCH-VS-LAUNCH AT THIS PIN: no branch, no PR.** `ls-remote` returns four
heads (`main` plus three, all ancestors of `main`); the open-PR list is empty.
⚠️ **git-only detection** — a lane that launched and died before its first push
would be invisible (J-11).

**AND THE DEFECTS ARE UNMOVED, re-measured on run 2295** — the most recent
*completed* `ci.yml` run at this pin, which is #4561's own PR run at `f863458a`,
**17 CI runs after v19b measured run 2278**. All three are still failing, at the
same steps. A **fourth** is failing with them and is the one that matters most
to this program: **`Fast test tier`**, failing on **content** after running
**8 min 18 s** to completion. **G2 leg 2 wants a completed fast-tier-green
`ci.yml` run, so leg 2 is blocked on R-U** — and, through R-P, so is leg 4. Full
job table in **Gates**.

⚠️ **A scoping note the charter does not state and the next lane needs:** R-U
names **three** jobs; **four** are red-not-by-design, and the fourth is the
gating one. Whether `Fast test tier` is inside R-U's scope is **not adjudicated
here** — it is recorded so the lane does not discover it late.

### J-4 · 🟢 RULING **R-V** — GOLDEN TIER **UN-PARKED**, PERF-B **RESUMED**, AND A **KEEPER FREEZE DECLARED** ON {ERCOT, NEISO, PJM}

Recorded here for the first time (`grep "R-V"` → **ZERO** before this edit).
**This is the ruling the RESTART CHECKLIST's item 1 has been waiting for since
v13 — "decide the golden tier and the freeze together" — and R-V decides them
together, exactly as this board recommended for six cycles.** It is also the
substance of R-R's convened G2 un-park sitting, which the third sitting **HELD**
(J-5).

**The three parts, as ruled:**

1. **THE GOLDEN TIER IS UN-PARKED.** The 2026-08-22 owner park is lifted. The CI
   proof may now be spent; it costs one `workflow_dispatch` in billed minutes,
   which is why it was parked.
2. **PERF-B IS RESUMED.** WS3 moves from *PAUSED* to **RESUMED-IN-PROGRESS**, and
   DOCS-B (G2) becomes queueable behind it.
3. **A KEEPER FREEZE IS DECLARED ON {ERCOT, NEISO, PJM}.** No promotion in those
   three lanes until PERF-B's byte-green loop completes **or the owner lifts it**.
   **{MISO, CAISO, NYISO} are EXPLICITLY UNFROZEN.**

**WHY THE PARTITION IS EXACTLY RIGHT, and it is worth stating because it is not
a coincidence:** the frozen set is **identical** to the three ISOs whose stage-0
rows are **CURRENT** (PJM, NEISO, ERCOT-forward) and identical to the
four-instrument alignment set. A freeze buys **stillness**, and stillness is only
worth buying where a golden already exists to protect. The three unfrozen ISOs
are precisely the three whose rows are **STALE** and which R-Q's captures were
dispatched to move — freezing them would have frozen the wrong end.

**WHAT R-V DOES NOT DO, measured rather than assumed:**
- **It does not advance the program to G2.** Legs re-read: **leg 1 IN MOTION** ·
  **leg 2 BLOCKED on R-U** · **leg 3 SATISFIED** for the frozen three · **leg 4
  BLOCKED on R-U, then owner Settings**. See **Gates**.
- **It does not itself take a capture.** `results/regression-goldens/` is
  **byte-unchanged** across all 81 commits of this window — no commit touches it.
  **Stage-0 stays 3 current / 3 stale.**
- **It does not, by itself, produce a byte-green certificate.** Un-parking grants
  permission; **nothing has exercised it** (J-6).

### J-5 · 🟢 R-R's SITTING WAS **HELD** — "CONVENED-NOT-HELD" IS RETIRED

v19b recorded R-R as **CONVENED, NOT HELD**, with nothing in it decided. **The
2026-09-01 third sitting IS that room, and it sat.** Its agenda is discharged as
follows, and this is the direct evidence: **R-V** decides restart-checklist item 1
material (golden tier + freeze **together**, exactly as the agenda framed it),
resumes **PERF-B**, and makes **DOCS-B** queueable; **R-U** takes up the leg-2
correction v19b sent into the room; **G2 is NOT declared**, which was the honest
possible outcome given leg 2. **The "convened-not-held" reading is retired and
must not be re-served.** ⚠️ **What the sitting did NOT settle: R-P's flip** —
still the owner's Settings action, still blocked on the same three red checks
(J-3), and **still not live at this pin**.

### J-6 · 🔴 THE UN-PARKED TIER WAS NEVER IDLE — **THREE CONSECUTIVE RED CRON RUNS, AND THE BOARD CALLED THE PROOF "DELIBERATELY UNSPENT" THROUGH ALL OF THEM**

**The single most consequential correction in this refresh, and it is a
correction to this board's own standing text.** The Watch item and the
`GOLDEN-TIER-FIX` rollup row have said for **seven cycles** that the #4071 fix is
merged, locally replayed green, and its **CI proof deliberately unspent**.
Measured against `golden-data-tier.yml`'s own run list at this pin:

| run | event | date | head | conclusion |
|--:|---|---|---|---|
| **#7** | **`schedule`** | 2026-08-31 | `d44446e0` (main) | 🔴 **failure** |
| **#6** | **`schedule`** | 2026-08-24 | `d84a95e1` (main) | 🔴 **failure** |
| **#5** | **`schedule`** | 2026-08-17 | `6cc332e7` (main) | 🔴 **failure** |
| #4 | `workflow_dispatch` | 2026-08-15 | branch | 🟢 success |
| #3 | `workflow_dispatch` | 2026-08-15 | main | 🟢 success |
| #2 / #1 | `workflow_dispatch` | 2026-08-15 / 08-14 | main | 🔴 failure |

**Three findings, each stated separately because they are separately actionable:**

1. **THE PROOF WAS NOT UNSPENT — IT WAS BEING SPENT WEEKLY AND FAILING.** A cron
   has fired the tier every week on `main` since 2026-08-17 and **every one of
   those three runs is RED.** Seven cycles of board text describe a state that
   stopped being true five cycles ago.
2. **AND IT IS NOT THE FAILURE #4071 FIXED.** Run #7's job walked **all six
   provisioning steps green** — checkout, uv, deps, `data/clean`, emissions —
   for 10 min 40 s, and then failed at **`Data-provisioned pytest tier
   (serial)`**, taking the `Loud-failure guard` down with it. That is a
   **content** failure in the tier's own tests, not the OOM/provisioning class
   the #4071 fix addressed. **The local four-step replay this board cites as
   "verified green" does not cover it.**
3. **AND NOTHING WAS WATCHING.** CLAUDE.md's own standing warning —
   *"Scheduled (`cron`) workflows spend money with nobody watching"* — is
   instantiated here on this program's own workflow, in a **private repo where
   every runner-minute is billed**, for three weeks. **The park was recorded as a
   state and never re-measured as one**, which is the same failure shape as a
   carried figure that is never re-derived.

**CONSEQUENCE FOR R-V AND FOR G2 LEG 1, stated plainly:** R-V un-parks a tier
that was **already running and already red**, so "un-parked" buys less than it
appears to. **The owner has run NO `workflow_dispatch` at this pin** — last
dispatch of any kind was run #4 on 2026-08-15 — so the un-park is **granted and
unexercised**. **Leg 1 is now blocked on a green tier run, which is a defect to
fix, not a permission to grant.** ⚠️ **Not this lane's to fix, and not
adjudicated here**: the tier's tests are the engine desks' surface. **Routed and
recorded.**

### J-7 · 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** AT {ERCOT, NEISO, PJM} — RE-DERIVED, WITH FAIL-CLOSED NULL HANDLING

Re-derived at the pin from four independent sources, never from each other, and
**never from the dispatch**:

| instrument | source read | membership |
|---|---|---|
| **CALIBRATED determination** | `status/<ISO>.js`, parsed live | **{ERCOT, NEISO, PJM}** |
| **`complete` marker** | `calibration-complete.json` `complete` block | **{ERCOT, NEISO, PJM}** |
| **active `frontier`** | `keepers/<ISO>.json` `frontier` blocks | **{ERCOT, NEISO, PJM}** |
| **forecast gate-(a) passers** | `program-status.json` `gate.a_keeper_marker.status` | **{ERCOT, PJM, NEISO}** |

**ALL FOUR AGREE. ALIGNMENT HOLDS** — a third consecutive cycle, and the first
across a **keeper motion + a stamp re-key** in the same window.

**FAIL-CLOSED NULL HANDLING, applied and stated:** `frontier` is **ABSENT** on
CAISO and MISO and **WITHDRAWN** on NYISO (`withdrawn: 2026-08-30`). Absent and
withdrawn are both treated as **NOT in the active set** — never as unknown, never
as a pass. Applied the same way, the three non-passing gate-(a) rows are failures
**ON THE MERITS**, not stamp artefacts: CAISO and MISO NOT-YET and absent from
`complete`; NYISO's marker withdrawn. **All six stamps name their ISO's live
keeper** — verified twice, field-by-field here and independently by
`check_gate_a_provenance.py` (**exit 0**).

⚠️ **The standing caveat survives untouched and is not narrowed by a third
agreeing cycle: nothing in the repo compares all four instruments.** Three legs
are now CI-guarded; the `frontier` leg has **no instrument at all**, and the
alignment itself exists only because this board re-derives it every cycle. v16
retired this on one cycle's agreement and v17 un-retired it. **It stays open.**

### J-8 · 🟠 KEEPER MOTION — MISO `191-bexit` → `198-oomlevel` (RECORDED, **NOT** ADJUDICATED)

**The window's only keeper motion.** Promoted at `86319e3f` — *"miso-198:
PROMOTE 2026-09-01-miso-198-oomlevel — the out-of-merit level re-conditioning"* —
in **#4552** (`miso-st-gas-steam-chp-calibration-9snn32`). The other **five
shards are byte-unmoved** across the window.

**This board adjudicates none of it.** MISO's calibration desk owns the
promotion, its PREREG and its structural case. What is recorded here is what the
motion does to **this board's instruments**, re-derived from the committed
artifacts:

- **Determination UNCHANGED: `NOT-YET`.** Grade summary **8 / 6 / 1 / 1**
  (scored / target / fails / ledgered) — identical to `191-bexit`'s. Rubric
  **v3.5**. The single failing criterion is still **C3a**, and MISO remains one
  of the two ISOs (with CAISO) whose *only* failing criterion it is.
- **C3a(RT) moves in one year and barely: 2023 `+0.1 %` (unmoved) · 2024
  `−4.6 % → −4.5 %` · 2025 `−12.3 %` (unmoved, still the FAIL).** **A promotion
  that did not move the residual is rule 1 `[R-STRUCT]` working**, not a null
  result — the same reading this board gave CAISO's `220 → 231` at v19.
- **`audit_keepers.py` PASS, 0 failures / 0 warnings**, over `complete` =
  {ERCOT, NEISO, PJM} — the M1 re-key check is satisfied **vacuously** for MISO,
  which holds no `complete` entry and so owed no marker re-key. **Verified, not
  assumed.**
- **It deepened MISO's stage-0 gap by one**: the golden still names
  `2026-08-16-miso-160-wefor-shape`, now **three promotions** past capture, and
  `check_golden_manifest.py` names the live keeper `198-oomlevel` in its STALE
  line (J-9).
- **It is what made R-T necessary** — and the nine-PR stamp-staleness window it
  opened is exactly what R-T's routing half closes (J-2).
- **It is NOT a freeze breach.** R-V freezes {ERCOT, NEISO, PJM} and leaves MISO
  explicitly unfrozen; the promotion also predates the ruling's record.
- **Sidecar total is UNCHANGED at 60** despite two new MISO registrations
  (`198-control`, `198-oomlevel`) — MISO sits at its rule-15 cap of 15, so
  `prune_iso` retired two. **The retention rule working, observed rather than
  assumed.**

### J-9 · 🔴 NOT ONE PERF-B SURFACE MOVED — **`results/regression-goldens/` IS BYTE-UNCHANGED ACROSS ALL 81 COMMITS**

Verified with `git log -- results/regression-goldens/` over the full window:
**zero commits.** So, stated separately because they are separate claims:

- **Stage-0 stays 3 current / 3 stale**, and `check_golden_manifest.py` (exit 0)
  reports the same three ISOs stale — **CAISO, MISO, NYISO** — against the same
  three live keepers, MISO's now reading `198-oomlevel`.
- **Neither R-Q capture lane has run**, and R-S has now re-issued both (J-1,
  J-11).
- **ERCOT's 2023 carve-out is still UNCOVERED and still unrepresentable** at this
  manifest schema; R-O's lane is unlaunched across **three** pins.
- **`.github/workflows/` and `docs/audit/` are also byte-untouched** this window,
  so **WS1's completion figure is carried by measurement, not by assumption**,
  and **WS6/BLOAT is unchanged**.

⚠️ **THE HONEST READING OF "WS3 RESUMED": IT IS A RULING, NOT YET A
MEASUREMENT.** WS3 moves to RESUMED-IN-PROGRESS on **R-V's authority alone**. Its
completion figure is therefore held at the **~82 %** v19 measured, **not
advanced** — nothing has been captured, certified or merged since. **The next
cycle's honest test is whether the surface moves; a resumed workstream that
produces no commit is a paused one wearing a different label.**

### J-10 · 🟢 ALL SEVEN GATE SCRIPTS EXIT **0** — RE-RUN HERE, EXIT CODES CAPTURED DIRECTLY AND UNPIPED

Every one re-run at `07472e7c`, each invoked on its own with `$?` read
immediately, **never through a pipe** (a pipe reports the last stage's status and
has silently green-washed a gate on this program before). Full readings in
**Gates**. Against the director's readings at `1aa8ac14`, **six of seven
re-derive identical**; two figures move, both benignly:

- **`check_mechanism_matrix.py` path anchors `156 → 159`** (field **194** and row
  **49** unchanged), **0 WARNs**, 0 unresolvable beyond the ratchet. **No new
  `ScenarioConfig` field**, so duty (c) of rule 26 is not engaged.
- **`check_forecast_staleness.py` undated verdict stamps `31 of 55` → `25 of 56`**
  — one verdict added, six re-scored through the stamped scorer. **Δ = 0 of 10**
  (v19b: 2), **91 stamped / 65 scored**, **26** config epochs. The WARN persists
  and is unchanged in kind.

**`check_gate_a_provenance.py` is the one that CHANGED STATE in the window:
exit 1 → exit 0**, repaired by #4561 (J-2). Everything else was green before and
after.

### J-11 · 🔴 DISPATCH-VS-LAUNCH ON ALL SIX OPEN DISPATCHES — **FIVE OF SIX SHOW NO BRANCH AND NO PR**, AND THE INSTRUMENT IS NOW WEAKER

Run at the pin from **`git ls-remote --heads origin`** (four heads: `main` plus
three, **all three ancestors of `main`**, i.e. merged) and **one live
`list_pull_requests(state=open)`** (returns **[]**).

| dispatch | ruling | branch at pin | open PR | goldens/target moved? | reading |
|---|---|---|---|---|---|
| **Capture-A** (MISO stage-0, target now `miso-198-oomlevel`) | R-Q → re-issued R-S | **none** | none | no — goldens byte-unchanged | 🔴 **no branch, no PR** · 2nd issue |
| **Capture-B** (CAISO → NYISO stage-0) | R-Q → re-issued R-S | **none** | none | no | 🔴 **no branch, no PR** · 2nd issue |
| **R-O schema lane** (config-partition manifest) | R-O → re-issued R-S | **none** | none | no — ERCOT carve-out still uncovered | 🔴 **no branch, no PR** · 2nd issue, **3rd pin** |
| **R-U CI-red repair** | R-U (new) | **none** | none | no — 3 jobs still red on run 2295 | 🔴 **no branch, no PR** · 1st issue |
| **PERF-B resume** | R-V (new) | **none** | none | no — no PERF-B surface moved (J-9) | 🔴 **no branch, no PR** · 1st issue |
| **this records lane (v20)** | dispatch | `claude/audit-records-v20-*` | — | board + plan §8 + README | 🟢 **LAUNCHED** |

**Running count: SIX from the second sitting + THREE from the third = NINE
dispatches that show no session.** One of the six second-sitting entries — the
v19 records lane — has since launched and merged (#4538), so the standing total
of *currently* unlaunched dispatches is **five**.

**⚠️ AND THE INSTRUMENT LOST ITS SECOND LEG — SAY THIS WHEREVER A NON-LAUNCH IS
ASSERTED.** v19 and v19b stated their limit as *"it observes branches, not
sessions."* At v20 that is no longer a caveat but the **whole method**: **the
session-roster tool is no longer in this desk's surface**, so detection is
**git-only**. There is now **no instrument at all** that can distinguish:

- a dispatch that **never reached a session**, from
- a session that **launched and died before its first push**, from
- a session **running right now** with nothing pushed yet.

**Every "never launched" on this board therefore means, strictly, "no branch and
no PR at this pin" — nothing stronger.** The director's question from v19b —
*why* the non-launches happen — has been made **harder to answer**, not easier,
by the loss of the roster, and it remains the director desk's.

### J-12 · 🟠 THE DISPATCH'S ANCHOR-WARN FIGURE RE-DERIVES DIFFERENT — **THE DEFECT NEVER EXISTED ON `main`**

The dispatch records G3 as *"0 with the 243 anchor WARNs **GONE** — repaired by
commit `f5b33644`, an out-of-program lane; **record who**."* Re-derived:

- **WHO: `f5b33644`, authored by Claude Opus 5, session `01CjdPEJQoyo68io1wmiUiLP`,
  in the `claude/capx-director-refresh-0z0e0f` lane, merged as PR #4531.** It is
  indeed out-of-program — the capx forecast desk's, not this one's. **Recorded as
  asked.**
- **BUT IT REPAIRED ITS OWN LANE'S BREAKAGE, NOT A DEFECT ON `main`.** The commit
  message says so in its own words: the guard *"reported 0 anchor warnings on
  `origin/main` and 236 after"* **the previous commit** — `0931d7e6`, which
  deleted `renewable_buildout_pace` from `scenarios.py` and shifted every anchor
  below it. And `f5b33644~1` is **not a first-parent commit of `main`**: breakage
  and repair merged **together** in #4531, so **`main` never held the broken
  state at any tip.**
- **The count was 236, not 243**, and the WARNs were **already 0 at v19b's pin** —
  `f5b33644` is an ancestor of `f45766e4`, and v19b measured 0 WARNs.

**So all three parts of the dispatched claim need correcting: there were not 243,
they were not on `main`, and "GONE" implies a repair of something this board was
tracking — the ~243 v19 chased was a *different* instance, already found a no-op
at v19's own pin (G-8).** ⚠️ **This is the THIRD consecutive dispatch to carry an
anchor-WARN figure measurement does not support.** The figure is mechanical,
trivially re-derivable in one command, and has been wrong three times running —
which is a fact about **carrying figures between dispatches**, not about the
matrix guard. **A dispatch repeating a figure does not re-establish it.**

### J-13 · 🟢 RECORDS INTEGRITY — WHAT THIS LANE TOUCHED, AND WHAT IT VERIFIED IT DID NOT

**Files edited, and no others:** `docs/handoffs/audit-program-director-board-2026-08.md`,
`docs/model-audit-release-plan-2026-08.md` (§8), and
`frontend/data/backcast/keepers/README.md` (**additive only** — one dated block
recording R-T's routing duty and R-V's freeze; **the shard-shape docs, the
promotion steps and the Class-E retention rule are byte-untouched**). The README
edit is the **one sanctioned exception** to this lane's keeper-store prohibition
and it changes **no keeper**.

**Verified byte-unmoved at the pin, by `git log` over the window rather than by
assertion:** every **keeper shard** (`git diff` returns MISO alone, and that is
#4552's promotion, not this lane's), **`calibration-complete.json`** (0 commits),
**`holdout-freeze.json`** (0 commits), **`results/regression-goldens/`** (0
commits), **`.github/workflows/`** (0 commits), **`docs/audit/`** (0 commits),
the **registry**, and **every mechanism-matrix verdict, evidence string, fc
posture and keeper stamp**. `program-status.json` and `ff-verdicts.json` moved in
the window (3 commits each) — **none of them this lane's**; #4561 is the director's
R-T push and the rest are the capx desk's.

**No workflow was created or edited**, per CLAUDE.md's standing prohibition —
which J-6 makes newly pointed: this program's one scheduled workflow has been
billing minutes weekly with nobody reading its result.

## What moved — v19b (`12c34488..f45766e4`, "the second-sitting rulings")

**Every figure re-derived at `f45766e4`.** The window is one PR, so this section
records **rulings and state**, not motion — and the re-derivation of the v19
figures is itself the finding in H-4.

### H-1 · 🔴 RULING **R-P** — BRANCH PROTECTION: **FLIP NOW, FAST GATES ONLY** — RECORDED AND WRITTEN AS RULED, WITH **TWO BLOCKERS ATTACHED**

Recorded for the first time (`grep "R-P"` → **ZERO** across `docs/` at this pin).
R-P is an owner **AMENDMENT of signed plan §6 decision 3** (*"enable after G2,
not before"*, signed 2026-08-13) on new evidence: **#4515 merged over a red hard
gate**, and the audit-program gate scripts holding green across 60+ PR windows.

**EXECUTED:** a dated check-name refresh is appended to
`docs/governance/branch-protection-memo-2026-08.md` (+96 lines, purely additive;
the memo body is untouched and remains the settings procedure). It replaces only
the §3/§4 **check-name lists**, verified against `ci.yml` at this pin, and records
the naming caveat R-P names: **`FR-21 forecast-board staleness (WARN only)` still
says *WARN only* in its display name but has carried the HARD
`check_gate_a_provenance` step since R-J** (`ci.yml:213`, inside the job whose
`name:` is at `ci.yml:158`). A second structural fact worth the same ink:
**`check_golden_manifest` lives inside `Rule-22 quarantine gates`** (`ci.yml:118`,
job name at `:75`), so requiring that one check already covers the board's
undercounted seventh gate — the required list is shorter than the gate list.

**🔴 BLOCKER 1 — THREE OF THE SEVEN PROPOSED REQUIRED CHECKS ARE RED ON `main`
RIGHT NOW.** Measured against **run 2278**, the most recent *completed* `ci.yml`
run at this pin (#4535, head `d9c5d4b1`), and reproduced locally from
base-branch content:

| proposed required check | run 2278 |
|---|---|
| `Rule-22 quarantine gates` | 🟢 success |
| `Rule-28 mechanism-matrix guard` | 🟢 success |
| `Cache-key registration guard` | 🟢 success |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success |
| **`Pinned default cache key`** | 🔴 **failure** |
| **`Ruff lint + format`** | 🔴 **failure** — 5 errors: three `F821` undefined names in `src/market_sim/runner.py` (`entry_walks`, `entry_reserve_adders`, `build_nyiso_link_loss`) + two dead-code lints in `scripts/gen_caiso197_attestation.py` |
| **`Structural refactor guards`** | 🔴 **failure** at *facade re-export + persisted-identity tests* |

**Why the ruling's evidence and this measurement can both be true.** *"Seven
gates holding green"* is the **seven audit-program gate SCRIPTS** — every one
exits **0** at this pin, and this board has published exactly that for two
cycles. **They are not the seven CI JOBS R-P proposes to require.** Four of the
proposed jobs are the green ones; three are jobs **no audit-program script
covers**. The conflation is easy to make from this board's own Gates table,
which is one reason it is recorded here rather than left in the memo.

**Consequence, stated plainly: flipping the ruleset with the list as written
freezes every merge on the repository** — the exact outcome memo §4 was written
to prevent, arriving through §3 instead of §4. **A sequencing that executes R-P
without the freeze** is offered in the memo appendix and recommended by nobody
but this lane: require the **four green checks now**, add the other three the day
their lanes go green — the same one-checkbox follow-up §4 already prescribes for
FR-22 and the invariant audit.

**🟠 BLOCKER 2 — THE SHRINK GUARD IS PATH-FILTERED.** `file-integrity-guard`'s
`pull_request` trigger filters to `src/**`, `scripts/**`, `CLAUDE.md`,
`model-methodology-spec.md`, `.github/workflows/**`. **A docs-only PR — every
records-lane PR, this one included — never reports it**, and GitHub treats a
required check that never reports as **pending, not passed**. Memo §3's *"if it
reports a check on PRs"* qualifier is load-bearing and must not be dropped.

**DO-NOT-REQUIRE, re-verified rather than carried:** `FR-22
backcast->forecast parity` is **red at this pin — `check_forecast_parity` exit 1,
7 armed-but-undeclared fields** (ERCOT ×3, NYISO ×2, CAISO ×1, MISO ×1), one of
them `caiso_offer_surface_measured_ungrounded`, i.e. **the caiso-231 keeper
promotion of today**. `Forecast-invariant artifact audit` red, unverified, stays
out. `Fast test tier` — memo §3's deferral stands, **and its ground has shifted**:
it is no longer merely a checkout failure, it **ran to completion in 8.5 minutes
on run 2278 and FAILED on content**.

**EXECUTION STATE — observed, not assumed. The flip is NOT live at this pin.**
A lane cannot read repository settings, so this is read off the merge record:
**#4535 was created 17:54:17Z and merged 17:54:33Z — 16 seconds** — while its own
`ci.yml` run did not complete until **18:04:18Z**, ten minutes later, six jobs
failing. **#4534 merged 6 seconds after creation.** No required-status-check
ruleset was in force for either. The memo body's *86-second pattern* is now a
**16-second** pattern.

### H-2 · 🟠 RULING **R-Q** — CAPTURE MISO + CAISO + NYISO NOW; TWO SOLVE LANES DISPATCHED

Recorded for the first time (`grep "R-Q"` → **ZERO**). Two lanes: **Capture-A
(MISO)** and **Capture-B (CAISO, then NYISO)**, with the **staleness and
no-consumer caveats accepted by the owner on the card**. Target: **6 of 6
bare-ISO stage-0 entries current**; the ERCOT **carve-out slot stays with R-O**
and is not in R-Q's scope.

**R-Q supersedes restart-checklist item 5's ordering.** Item 5 named MISO next
and **stood through R-L**, which took NEISO and ERCOT against it as a one-capture
exception. R-Q now authorises MISO *and* the other two together, so item 5 is
**discharged as an ordering constraint** — recorded rather than silently dropped.

### H-3 · 🔴 R-Q's TWO LANES HAVE **NOT LAUNCHED**, AND THE STAGE-0 TABLE THEY WERE SENT TO MOVE IS BYTE-UNCHANGED

Dispatch-vs-launch at `f45766e4`, on the same evidence standard the board has
used all cycle:

- **`ls-remote` returns seven heads** — `main`, `audit-program-director-irzj4a`
  (the spent R-N remnant), `capx-d20-reconstruction-provenance`,
  `capx-d34-carbonprice-guard`, `capx-t3-golden-2`,
  `miso-st-gas-steam-chp-calibration`, `nyiso-170-merit-order-split`. **None is a
  capture lane.**
- **The live PR list holds one open PR** (#4530, `miso-198`), unrelated.
- **No commit in the window touches `results/regression-goldens/`.**
- **The stage-0 table is byte-identical to v19's**: 3 current / 3 stale, and
  `check_golden_manifest` still reports CAISO / MISO / NYISO stale against the
  same three live keepers.

⚠️ **The same honest limit as R-O's:** the check observes **branches, not
sessions**, and an unpushed lane is invisible to it — this lane's own branch was
unpushed at measurement time. **What is established is: no branch, no PR, no
artifact.**

### H-4 · 🟢 THE v19 FIGURES RE-DERIVE **IDENTICAL** — WHICH IS A RESULT, NOT A FORMALITY

The v19 board was written six commits ago; a records lane could reasonably have
carried its tables. Re-derived instead, at the new pin:

| figure | v19 (`72576ebe`) | v19b (`f45766e4`) |
|---|---|---|
| keeper shards | 6 | **all six byte-unmoved** |
| registry sidecars | 60 | **60** |
| solve-year histogram | {2022:2, 2023:58, 2024:54, 2025:54} | **identical** — locked-test years still **NONE** |
| stage-0 | 3 current / 3 stale | **3 current / 3 stale** |
| markers | `complete` {ERCOT, NEISO, PJM} · `final` **empty** · freeze locked-test-scoped | **identical** |
| four-instrument alignment | {ERCOT, NEISO, PJM} | **{ERCOT, NEISO, PJM}** |
| parity | 60 runs / 95 dirs | **60 / 95** |
| matrix anchors | 194 + 49 + 156, 0 WARNs | **194 + 49 + 156, 0 WARNs** |
| staleness Δ | 0 of 10 | ⬅ **2 of 10** (#4535's engine-adjacent commits; still far under threshold) |

**Exactly one reading moved**, and it moved for a legible reason. **The rest is a
re-derivation that agreed** — which is what the protocol is for, and the only way
to know the difference between a stable board and a stale one.

### H-5 · 🟠 THE DISPATCH'S FIGURES, RE-DERIVED A SECOND TIME — FOUR STILL DIFFER, AND THE CORRECTIONS ARE THE SAME ONES

The third dispatch re-asserted several v19-cycle figures this board had already
corrected. Re-measured at this pin, **the v19 corrections stand**:

| dispatch asserted (again) | measured at `f45766e4` |
|---|---|
| parity allowlist **26 → 3** | **40 → 8** — 26 was the board's last count; it had grown to 40 by the repair |
| **~243 anchor WARNs** to repair (job 4) | **0 WARNs; `--fix-anchors` repairs 0; `git diff` empty.** Already repaired in #4522 at the v19 window, digits-only |
| gate-(a) **exit 1** | **exit 0** — the pre-repair reading; R-N's #4523 fixed it |
| R-M targets `neiso-t3` @ `89dacc4c0343` | **`neiso-t3-pre-fc5`** carries that sha; `neiso-t3` was re-scored onto reachable `7dffe3341158` |

**Job 4 is a no-op for the second consecutive dispatch**, and the reason is
unchanged: the repair landed in a capx forecast lane that did not mention it.
**A dispatch repeating a figure does not re-establish it.**

### H-6 · 🔴 RULING **R-R** — THE **G2 UN-PARK SITTING IS CONVENED**, NOT HELD

Recorded for the first time (`grep "R-R"` → **ZERO**). The owner convenes the G2
un-park sitting for the director's **next** sitting, with an agenda:

1. **Restart-checklist item 1 material** — the golden tier and the keeper freeze
   **decided together**, which this board has recommended for six cycles.
2. **G2 legs 2–4** — the CI-green leg, the freeze leg, the branch-protection leg
   (R-P is leg 4 moving ahead of the sitting).
3. **PERF-B resume.**
4. **DOCS-B queueing.**

**Recorded as CONVENED-NOT-HELD.** Nothing in it is decided, and **G2 is not
declared**: leg 1 still carries both owner parks. ⚠️ **And one agenda item needs
a correction carried into the room: G2 leg 2 is NOT satisfiable today.** The leg
is *"one completed fast-tier-green `ci.yml` run"*; on run 2278 — the most recent
completed run — the **`Fast test tier` job FAILED on content** after running 8.5
minutes to completion. The board has carried leg 2 as *"obtainable and
decision-free"* for four cycles on the strength of the **gate scripts** being
green. **That reading does not survive this measurement, and leg 2 is
re-classified `BLOCKED — needs the fast tier green` below.**

### H-7 · 🟢 THREE STANDING ITEMS RECORDED FOR CROSS-DESK VISIBILITY, ADJUDICATED BY NOBODY HERE

- **Q-4 is ADOPTED** into the refresh protocol (already recorded at v19 G-15;
  re-affirmed by the second sitting and executed again by this lane).
- **🟠 THE EIA-923 2025 FINAL VINTAGE HAS STILL NOT PUBLISHED.** As reported by
  the director at this sitting: **still early-release as of 2026-09-01, with EIA
  stating September 2026 for the final**. **NEISO's `final`-grant data block lifts
  on publication and needs no ruling** (rule 22: data intake needs no
  authorization). ⚠️ **Attribution: this is the DIRECTOR'S report, not this
  lane's measurement** — a records lane has no EIA feed, and the honest status of
  the claim is *reported, not verified here*.
- **🟢 THE 2020 AND 2021 VALIDATION TOUCHPOINTS ARE AUTHORIZED AND WHOLLY
  UNSPENT.** Verified by walking all 60 sidecars at this pin, not asserted: the
  solve-year histogram is **{2022: 2, 2023: 58, 2024: 54, 2025: 54}** and the scan
  for **2020** and **2021** returns **NONE** — zero registrations, ever, for any
  ISO. All three `complete` ISOs {ERCOT, NEISO, PJM} may spend them (the freeze
  is scoped to `locked_test` alone), and **ERCOT has not spent even its 2022** —
  the only two 2022 rows are PJM's and NEISO's. **This is the calibration desk's
  surface; recorded for visibility, dispatched by nobody here.**

## What moved — v19 CYCLE (`d44446e0..72576ebe`, "the records-debt cycle")

**Every figure in this section is derived at `72576ebe` from committed bytes.**
Nothing is read from the dispatch, from v17/v18/v18b, or from any table on this
board. Where a dispatched figure and the pin disagree, the pin wins and the
disagreement is recorded (G-12).

### G-1 · 🟢 RULING **R-J** — ALL FOUR UNBLOCKED MAINTENANCE ITEMS **EXECUTED AND MERGED**, AND THEY RETIRE QUEUE ITEM Q-1 BY EXECUTION

Recorded here for the first time: **`grep "R-J"` across `docs/` at the pin
returns ZERO** (the only near-match is the unrelated word `R-JUDGMENT`). The
ruling authorised the four maintenance items that needed no owner decision. All
four are **merged and verified in the working tree at the pin** — and the
commit→PR mapping was **derived by ancestry, not taken from the dispatch**:

| item | commit | PR | verified at the pin |
|---|---|---|---|
| **Parity allowlist → class-level carve-out** (checklist item 10, BLOAT B-8) | `76c5eed6` | **#4495** | `KEEP_REQUIRED_UNMAPPED_BUNDLES` is now a **residual** enumeration of **8** entries behind a structural two-conjunct classifier (no solve output **AND** named by a committed PREREG/RESULT reproduction) |
| **Bench gate date-kind fix** (checklist item 12) | `d5c3178f` | **#4495** | both sides now use the **committer instant in offset-bearing form**; the docstring records that `--since` is inclusive, verified 2026-09-01 |
| **Stage-0 per-entry provenance** (checklist items 2 + 11) | `362e2771` | **#4502** | manifest **schema v1 → v2**; `provenance` + `keeper_snapshot` per entry; the shared top-level `git_sha`/`git_dirty`/`env` **removed** |
| **`check_gate_a_provenance` hard CI guard** | `3f5a24ae` | **#4495** | wired at `.github/workflows/ci.yml:213`, `python3` stdlib, **exit 0** at the pin |

**🟠 ONE R-J FIGURE THE DISPATCH ASSERTED IS RE-DERIVED DIFFERENT, AND THE TRUE
STORY IS BETTER.** The dispatch said the allowlist went **26 → 3**. Measured at
four shas (`565f555c`, `8462da22`, `a40cfc68`, `72576ebe`) it is **8 at every
one**, and the pre-repair count at `565f555c^` is **40, not 26** — the 26 was the
audit board's *last count*, and the enumeration had grown by 14 in the interim,
exactly as the gate's own docstring warned (*"a stale entry is a re-armable
hole"*). **So the repair is 40 → 8, a larger win than the dispatch claimed**, and
the residual 8 are live-lane control/recipe dirs, not dead output.

**🟢 THE STAGE-0 REPAIR ALSO OVERTURNED TWO OF THIS BOARD'S OWN STANDING
CLAIMS**, and the lane said so in its own commit message rather than quietly
fixing them: **`af1ccb6` DOES resolve and IS an ancestor of `main`** (it is the
CAISO capture commit), and **the five "unrecoverable" shas were recoverable all
along** — every intermediate value had been committed on its way through the
manifest's history. All six were recovered **with evidence and zero UNKNOWN
rows**: ERCOT `ec413d20`, NEISO `ebd31a9`, NYISO `2dd9dbc`, CAISO `9f6ff3e`,
MISO `af1ccb6`, PJM `1cfea72`; the chain **self-corroborates** (CAISO's sha *is*
the NYISO capture commit, MISO's *is* the CAISO one). **v17's "does not resolve"
was a shallow-clone artefact** — see G-13, which this lane hit independently.

**Q-1 IS RETIRED BY EXECUTION**, not by ruling: the thing it asked for exists.

### G-2 · 🟢 RULING **R-K** — STAGE-0 CAPTURES **HOLD**; **SPENT**, SUPERSEDED BY R-L

Recorded for the first time (`grep "R-K"` → **ZERO** at the pin). R-K held the
stage-0 captures. It was superseded within the same sitting by **R-L**, which
authorised two of them by name. **R-K is spent and is not a live constraint**;
it is recorded so the hold and its release are both legible, and so a future
reader does not find R-L acting against an apparently-standing hold.

### G-3 · 🟢 RULING **R-L** — "JUST NEISO AND ERCOT" — **DISCHARGED IN FULL**, WITH ONE DEVIATION THE DIRECTOR ACCEPTED AND THIS BOARD NOW ADOPTS AS STANDING

Owner ruling, verbatim: **"Just NEISO and ERCOT"** — **deliberately against
restart-checklist item 5** (*capture MISO next*), which **STANDS UNCHANGED**;
R-L is an exception for this capture, not an amendment. Executed by
`claude/stage0-capture-neiso-ercot-elgk62` (**#4509** the captures, **#4517** the
finding), **the audit program's first solve lane**.

**Discharge, verified at the pin against the committed manifest — not read off
the finding:**

| leg | evidence at `72576ebe` |
|---|---|
| **Both fidelity oracles PASS, zero config drift** | `keepers.NEISO.fidelity.scenario_config_drift == []` and `keepers.ERCOT.fidelity.scenario_config_drift == []`; 259 / 271 meta flags matched |
| **Schema v2 proven** | each capture wrote **only its own entry**: NEISO `provenance.basis_sha 3c1f9642`, ERCOT `3c1f9642` / `git_sha a64cc7aa`, while CAISO/MISO/NYISO/PJM retain `9f6ff3ee` / `af1ccb6c` / `2dd9dbc9` / `1cfea728` untouched. **The v17 defect — one capture silently re-labelling every earlier one — is structurally impossible now, and this is the demonstration** |
| **Rule 22 clean** | years `[2023, 2024, 2025]` on both entries; no out-of-training year solved, scored or registered |
| **Coverage** | `check_golden_manifest.py` **exit 0**: **3 CURRENT / 3 STALE** |

**🟢 THE ACCEPTED DEVIATION, AND THIS BOARD'S STANDING READING OF IT.** The
capture lane **registered nothing on the backcast dashboard**, and the director
**accepted that**. The reasoning, adopted here as **the program's standing
reading of the stage-0 table's registry column**:

- **A golden's "provenance run" is the KEEPER it was captured against**, not the
  capture itself. That is exactly what schema v2 encodes (`keeper_id` +
  `keeper_snapshot`) and exactly what `check_golden_manifest.py` enforces.
- **The Card-1 precedent registered nothing either**, and **0 of the 60
  registered sidecars is a golden capture** — verified by walking the registry at
  the pin, not asserted.
- **Registering captures would spend top-15-per-ISO retention on regression
  baselines** — which is the *precise* fix **E-7 rejected** (*"do not exempt
  golden runs from retention — that re-creates the parity gate's dead-bundle
  class"*). Registering them is the same error wearing the opposite sign.

**Consequence for how this table is read, going forward:** the registry column
of the stage-0 table asks *"is this golden's provenance KEEPER RUN still
registered?"* — a **retention** question that schema v2's `keeper_snapshot`
already makes survivable — and **never** *"was the capture registered?"*, which
would be a category error. **A golden capture is not a dashboard run and rule 15
`[R-DASHBOARD]` does not reach it.**

### G-4 · 🟢 RULING **R-M** — Q-2's REMEDY **EXECUTED BY THIS LANE**, AND THE TARGET HAD **MOVED** SINCE THE DISPATCH

Recorded for the first time (`grep "R-M"` → **ZERO** at the pin) **and executed
here**, which is the difference between this entry and a finding that describes a
repair. The ruling: the two forecast verdicts whose `scored_at_sha` never reached
`main` are **ANNOTATED AS PERMANENTLY UNVERIFIABLE**.

**🔴 THE DISPATCH'S KEY LIST WAS ALREADY WRONG AT THE PIN, AND FOLLOWING IT WOULD
HAVE ANNOTATED A HEALTHY VERDICT AND MISSED A DEFECTIVE ONE.** The dispatch named
`neiso-t3` @ `89dacc4c0343` and `neiso-t3-pre-fc6` @ `271ad606c3fd`. At the pin:

- **`neiso-t3` no longer carries `89dacc4c0343`.** #4522's FC-6 P1 re-score moved
  it to **`7dffe3341158` @ 2026-09-01T06:12:01Z — REACHABLE in `origin/main`**.
  `neiso-t3` is healthy and was **not** annotated.
- **`89dacc4c0343` migrated to a different key**, `neiso-t3-pre-fc5`, when the
  FC-5 disposition lane preserved the prior verdict under a new name.
- `neiso-t3-pre-fc6` @ `271ad606c3fd` is unchanged.

**So the annotation was applied by SHA, not by key name** — the two verdicts
carrying an unreachable stamp at this pin are **`neiso-t3-pre-fc5`** and
**`neiso-t3-pre-fc6`**. Both are archival *preserved-prior* verdicts; both read
`HOLD`.

**Unreachability re-established, not inherited** — and against the **remote**,
because this container's clone is shallow (G-13). All **43** verdict stamps
carrying a `scored_at_sha` were swept; the four the shallow clone could not see
but which the GitHub API resolves (`8ba592814d92`, `bd97c6ebaa68`,
`e2a422c191aa`, `74775c4d661f`, `6fbd3f28eb9a`, `60e19610e454`) are healthy.
**The strict count is 2 of 43 — the same count v18b reached independently by
un-shallowing, from a different pin and a different method.**

**What was written, and what deliberately was not:**

- **Two additive keys per verdict**, as **siblings of `provenance`, never inside
  it**: `scored_at_sha_unverifiable: true` and
  `scored_at_sha_unverifiable_note` (a one-line cause note citing R-M). Neither
  is a `forecast-provenance/v1` field name (`schema`, `scored_at_sha`,
  `scored_at_date`, `cache_epoch`), and `forecast_provenance.read_stamp()` reads
  only the `provenance` object — **so no instrument can read the annotation as a
  provenance stamp.**
- **No sha altered and none fabricated.** Both historical values stand verbatim.
  Machine-verified: **4 lines added, 0 removed, 0 altered**; both `provenance`
  blocks **byte-identical** before and after; both determinations **`HOLD` →
  `HOLD`**; **no other verdict object touched**, key set unchanged at 55.
- **`check_forecast_staleness.py` re-run after the edit: exit 0**, anchored on
  **`7dffe3341158`**, which is **reachable in `origin/main`** — the ruling's
  explicit precondition, tested rather than assumed.

**Q-2 IS RETIRED.**

### G-5 · 🟢 RULING **R-N** — THE ONE-PUSH MICRO-SUPERSESSION IS **SPENT**, AND THE STANDING DEVIATION IS BACK IN FORCE

Recorded for the first time (`grep "R-N"` → **ZERO** at the pin). The records
path for this sitting was ruled to be **a one-push micro-supersession plus this
lane**. The director spent the supersession as **#4523** (commit `6d700725`,
**5 lines**), re-keying CAISO's forecast gate-(a) stamp to
`2026-09-01-caiso-231-b1-ungrounded`.

**Verified at this pin rather than accepted:** `check_gate_a_provenance.py`
**exits 0** (6 rows: keeper identity + marker state match the backcast store),
CAISO's `a_keeper_marker` names the live keeper, and the branch
`claude/audit-program-director-irzj4a` is an **ancestry-tested merged remnant**.

**Two things worth keeping from how it was executed.** First, it is the **new
guard's FIRST REAL FIRING** — #4495's `check_gate_a_provenance` went red (exit 1)
on the caiso-231 promotion and green after the re-key, which is a guard doing the
job it was built for **eight PRs after it was built**, on a defect class this
board had re-reported for three cycles with no gate able to see it. Second, the
push was **rebased onto #4522's disjoint capx edit** to the same shared file
rather than overwriting it — the shared-surface duty observed in practice, on the
one file three desks write.

**The supersession is SPENT and does not carry forward.** The standing deviation
governs again (*"issue prompts, I don't want you doing it from here"*), and **this
lane is its dispatched instrument**. A future sitting that wants to write
directly needs its own supersession.

### G-6 · 🟠 RULING **R-O** — THE ERCOT CARVE-OUT GOLDEN IS ANSWERED BY **CHARTERING A SCHEMA LANE**, AND THAT LANE HAS **NOT LAUNCHED** AT THIS PIN

Recorded for the first time (`grep "R-O"` → **ZERO** at the pin). R-L's capture
answered the ERCOT-forward config and explicitly reported the **2023 carve-out as
NOT covered and not coverable without a schema change**. R-O's disposition is not
"capture it anyway" but **charter the schema lane**, scoped to three things:

1. **A config-partition representation in the manifest** — today `keepers` is
   keyed one entry per ISO, so a two-config ISO has nowhere to put its second
   golden.
2. **`live_keeper` partition resolution** — `check_golden_manifest.py` compares
   one `keeper_id` against one live keeper; under a partition it must resolve
   *which* config a golden is of before it can call it CURRENT or STALE.
3. **The carve-out capture itself**, once (1) and (2) exist.

**LANE STATE AT THE PIN — the dispatch-vs-launch check applied, as instructed:
NOT LAUNCHED.** `ls-remote` returns four heads (`main`,
`audit-program-director-irzj4a`, `capx-director-refresh-0z0e0f`,
`miso-st-gas-steam-chp-calibration-9snn32`); **none is a schema lane**, and the
live PR list shows **one** open PR, unrelated (#4530). No commit in the window
touches `check_golden_manifest.py`'s partition handling. ⚠️ **The honest limit of
this evidence, stated because this board's own lane is invisible to it:** an
unpushed session is indistinguishable from no session — *this* lane's branch was
also unpushed at the moment of measurement. **What is established is: no branch,
no PR, no commits at `72576ebe`.**

**Standing consequence while the lane is unlaunched:** ERCOT's stage-0 row is
CURRENT **for its forward config only**, and full ERCOT coverage remains **two
captures, not one** — a fact the manifest still cannot express, which is exactly
what R-O exists to fix. Queue item added; see the queue.

### G-7 · 🟢 SEVEN GATES, NOT FIVE — THE ROSTER IS CORRECTED AND ALL SEVEN EXIT **0**

The board's protocol text and restart-checklist item 0 both said **five**; the
director's handoff said **six**; **SEVEN is correct**. Two gates were being
undercounted: **`check_gate_a_provenance.py`** (`ci.yml:213`, a **hard** gate, new
this window under R-J) and **`check_golden_manifest.py`** (`ci.yml:118`, which has
existed and been enforced throughout — **the undercounted seventh**, and the
instrument that now *owns* the stage-0 table). Both the Gates table and
checklist item 0 are corrected.

**All seven re-run at the pin, exit codes captured directly and never through a
pipe.** Readings in the Gates table. **Two of the director's seven readings
re-derive different at this pin**, both benignly: the matrix gate's **+243 anchor
WARNs are gone** (G-8) and the gate-(a) red is **repaired** (G-5) — the dispatch
predicted both would need this lane's action; neither did.

### G-8 · 🟠 JOB 4 — THE ANCHOR REPAIR — WAS **ALREADY DISCHARGED**, BY AN UNRELATED LANE, **UNANNOUNCED**

`python3 scripts/check_mechanism_matrix.py --fix-anchors` at the pin: **"repaired
0 line anchor(s); 0 left in the ratchet"**, `git diff` **empty**, gate **exit 0**
with **0 WARNs**, anchors **194 field + 49 row + 156 path** (v17: 194/49/152).
The ~243 WARNs the dispatch measured at `8462da22` were real and are gone.

**Where they went, established by diff rather than inferred:** `scenarios.py` is
**byte-identical** between `8462da22` and the pin, while
`docs/codebase-site/data/mechanism-matrix.js` changed by **120 insertions /
120 deletions** in exactly one commit — **`369c9bb7`, inside #4522**, the capx
lane whose commit subject is *"Re-score neiso-t3 FC-6 on the repaired P1 arm"*
and whose message **does not mention the matrix at all**.

**It was done correctly.** Verified post hoc by normalising every `:NNNN` token
on both sides of that commit: the two files are then **identical** — so the edit
moved **digits only**. No verdict letter, evidence string, fc posture or keeper
stamp moved, which is the same constraint this lane was given.

**🟠 THE FINDING IS NOT THE REPAIR — IT IS THE SILENCE.** A shared, CI-gated base
file was rewritten across 120 line-pairs by a lane whose declared scope was a
forecast re-score, with no mention in the commit subject or body. It happened to
be correct and happened to be exactly what this lane was dispatched to do. **The
class is a lane touching a shared surface without declaring it** — the same class
#4523 handled *well* one PR later by rebasing rather than overwriting (G-5). On
watch; not adjudicated, and **not a defect in the repair**.

**Protocol consequence, and it is the generalisable one: re-derive a dispatched
job's PRECONDITION before executing it, not only its figures.** Running
`--fix-anchors` blind would have produced an empty commit and a board entry
claiming a repair this lane did not make.

### G-9 · 🟢 FOUR-INSTRUMENT ALIGNMENT **HOLDS** — AND FOR THE FIRST TIME EVER, ALL SIX GATE-(a) STAMPS ARE CURRENT

Re-derived independently from four sources at the pin, with **fail-closed null
handling** — an ISO with a missing or unparseable value counts as **NOT** in the
set, never as a pass:

| instrument | source | membership at `72576ebe` |
|---|---|---|
| **Determination = CALIBRATED** | `status/<ISO>.js` `keeper.determination` | **{ERCOT, NEISO, PJM}** |
| **Rule-22 `complete` marker** | `calibration-complete.json` `complete` block | **{ERCOT, NEISO, PJM}** |
| **Active `frontier`** | per-ISO `frontier` block, **`withdrawn` honoured, absent block ⇒ NOT active** | **{ERCOT, NEISO, PJM}** — NYISO `withdrawn: 2026-08-30`; CAISO and MISO carry **no** frontier block |
| **Forecast gate-(a) passers** | `program-status.json` per-ISO `gate.a_keeper_marker.status` | **{ERCOT, NEISO, PJM}** |

**ALL FOUR AGREE. Alignment HOLDS at {ERCOT, NEISO, PJM}.**

**🟢 AND THE STRUCTURAL POINT IS BIGGER THAN THE MEMBERSHIP.** v17 recorded
**four of six** gate-(a) stamps **stale**, and the alignment break was *entirely*
that staleness — a bookkeeping lag masquerading as a disagreement. At this pin
**every one of the six `a_keeper_marker` rows names its ISO's live keeper**
(ERCOT `234-eastex-identity`, PJM `pjm-162-inputclock`, NEISO `neiso-99-joint-p1`,
CAISO `caiso-231-b1-ungrounded`, MISO `miso-191-bexit`, NYISO
`nyiso-159-loss-surface`) — machine-checked by `check_gate_a_provenance.py`,
**exit 0**. So the three ISOs that fail gate (a) fail it **on the merits**: CAISO
and MISO are `NOT-YET` and hold no marker; NYISO's marker is `withdrawn`.
**This is the first cycle in which the divergence could not have been a stale
stamp** — because a gate now refuses to let one exist.

**The watch item this retires, and the one it does not.** The *stale-stamp*
mechanism is now **gated in CI** and comes off the watch. **What does not retire
is the four-instrument comparison itself**: `check_gate_a_provenance` compares
keeper identity and marker state and **explicitly reads no determination**, and
nothing in the repo compares `frontier` membership against anything. **Three of
the four instruments are now cross-checked; the fourth still is not.**

### G-10 · 🟠 KEEPER MOTION — CAISO 220 → 231 (recorded, NOT adjudicated)

The cycle's **only** promotion: **`2026-08-26-caiso-220-c1-crosswalk` →
`2026-09-01-caiso-231-b1-ungrounded`** (#4515), a rule 25 `[R-ISO-SCOPE]` /
rule 14 `[R-ACCURATE]` structural-integrity repair replacing three
ERCOT-lineage-fitted offer bands (CC_CHP / CT_CHP / ST_GAS) that were sitting
un-grounded on CAISO's binding path. **Determination unchanged at `NOT-YET`;
grade unchanged at 8 / 6 / 1 / 1.** C3a(RT) moves marginally and **not
favourably**: 2023 **+4.0 → +4.1 %**, 2025 **+15.5 → +15.6 %**, 2024 unchanged at
**+12.5 %** — which is rule 1 `[R-STRUCT]` behaving exactly as written, a
structurally-correct repair kept despite a residual that did not improve.

**No rule-22 re-key was owed** (CAISO is `withdrawn`, not `complete`), and
`audit_keepers.py` returns **PASS 0/0** across it. **This board takes no position
on the merits.** Two items in the promotion's own record are noted because they
bear on this program's rules, not on CAISO's: it records a **standing owner
directive of 2026-09-01, "NO CONTROL ARMS"** (a single-delta arm is solved once
and scored against the committed keeper; HEAD drift is not measured with an LP
run), and it **records rather than drops a pre-registered gate it could not
satisfy** (G-STRUCT's DOF leg predicted the `offer_curve_by_group` ledger count
would fall 112 → 103; `build_dof_ledger._count_scalars` is provenance-blind and
measures surface size, not fitted content). **Both recorded, neither adjudicated.**

### G-11 · 🟢 A WORKSTREAM SURFACE MOVED — THE FIRST TIME IN THREE CYCLES

v17 reported the three workstream surfaces byte-untouched *at once*. Re-measured
over `d44446e0..72576ebe` with `git diff --name-status`:

- **`results/regression-goldens/`** — **MOVED**: `perfb-stage0/manifest.json`
  (schema v2 under R-J, then two captures under R-L). **WS3's stage-0 coverage
  figure moves by measurement**, 1/6 → 3/6.
- **`.github/workflows/`** — **MOVED**: `ci.yml`, gaining the
  `check_gate_a_provenance` step.
- **`docs/audit/`** — **byte-untouched**. WS1 is unchanged, and its blocker is
  still the G3 gate, not remaining A-half work.

**What this does NOT do is move G2.** PERF-B is still paused by owner decision
and the golden tier is still parked by owner ruling, so **byte-green cannot be
CLAIMED for the two new captures any more than for the PJM one**. Leg 1 keeps
**both** parked dependencies. Coverage improving while the gate stays shut is the
honest reading.

### G-12 · 🟠 FOUR FIGURES THE DISPATCH ASSERTED ARE RE-DERIVED **DIFFERENT** — WHICH IS THE PROTOCOL WORKING

None was a trap; each is a figure that moved between derivation and pin, or a
shorthand that did not survive measurement. **All four are recorded because the
instruction "trust nothing in this prompt" is not ceremonial.**

| dispatch asserted | re-derived at `72576ebe` |
|---|---|
| parity allowlist **26 → 3** named entries | **40 → 8** (26 was the board's last count; it had grown to 40 by the repair) — G-1 |
| **~243 anchor WARNs** to repair with `--fix-anchors` | **0 WARNs, 0 repaired** — already fixed by #4522 — G-8 |
| gate-(a) **exit 1**, repaired at `a40cfc68` | **exit 0** at the pin ✓ (the repair landed; the *reading* is the post-repair one) — G-5 |
| R-M targets `neiso-t3` + `neiso-t3-pre-fc6` | **`neiso-t3-pre-fc5` + `neiso-t3-pre-fc6`**; `neiso-t3` was re-scored onto a reachable sha — G-4 |

Also re-derived and different from v17's carried figures, none of them the
dispatch's fault: registry sidecars **58 → 60**, parity **58/93 → 60/95**,
staleness **81/49 → 89/57 stamped/scored** and **24 → 25 epochs**, bench engine
drift **19 of 20 → 20 of 20** at **6** engine commits (still **0 STALE**, still
ungated), matrix path anchors **152 → 156**.

### G-13 · 🔴 THE SHALLOW-CLONE TRAP, HIT INDEPENDENTLY FOR THE THIRD TIME IN THIS PROGRAM — AND IT HAS NOW PRODUCED ONE PUBLISHED WRONG READING

**This container's clone is SHALLOW** (`git rev-parse --is-shallow-repository`
→ `true`; earliest reachable commit `e52b90a4`, v16's own landing). Every
`git cat-file` / `merge-base` test against a sha older than that returns *absent*
— **indistinguishable, locally, from a sha that never existed.**

Measured here: of the **13** distinct `scored_at_sha` values on the forecast
board, the shallow clone reports **8 unreachable**; the GitHub API resolves **6
of those 8**. **The true strict count is 2.** Had this lane trusted the local
answer it would have annotated **six healthy verdicts** as permanently
unverifiable and written six fabricated defects onto the record — a strictly
worse outcome than the defect it was sent to annotate.

**The class already has a published casualty.** v17's stage-0 table asserted
`af1ccb6` *"does not resolve"* and built a Watch item and a checklist step on it;
R-J's repair lane found it **resolves and is an ancestor of main**, absent only
from *its* container's depth-258 clone. **Three sessions, three containers, one
trap.** The rule, now stated for the third time and worth stating once more
because it keeps costing:

> **BEFORE REPORTING AN ABSENCE FROM GIT, ESTABLISH THAT THE REPOSITORY COULD
> HAVE SHOWN YOU THE THING.** Check `--is-shallow-repository` first. Then either
> `git fetch --filter=tree:0 --unshallow` (measured at ~2 s by the v18b lane) or
> confirm against the remote API. **A local "not found" is evidence about the
> clone, not about the repository.**

### G-14 · 🔴 THE DISPATCH-VS-LAUNCH CHECK REACHED **FOUR NON-LAUNCHES IN ONE SITTING** — AND ITS YIELD IS NOW THE HIGHEST OF ANY PROTOCOL STEP

Recorded per the director's re-issue instruction, and extended by this lane's own
measurement:

1. **The original v19 records dispatch NEVER LAUNCHED** — no branch, no session,
   confirmed from git and the session roster.
2. **The FIRST RE-ISSUE of the same dispatch NEVER LAUNCHED** — same evidence.
   The records debt therefore stood **two sittings deep**; this lane is the third
   dispatch and the first to run. Both instances are recorded in the protocol
   section, as instructed.
3. **R-L's capture lane's first dispatch never launched** — recorded in that
   lane's own finding (*"Re-issued by the director after the dispatch-vs-launch
   check found the original R-L dispatch never launched"*).
4. **R-O's chartered schema lane has not launched at this pin** — no branch, no
   PR, no commits (G-6).

**Read against v16–v18, the trend is unambiguous.** v16 caught a near-miss; v17's
check returned *done* rather than *launched* on R-E; **this sitting produced four
non-launches, one of them twice**. A dispatched job is not a done job and is not
even a *started* job. **The step costs one `ls-remote` plus one PR list and is
the only thing standing between a ruling and silent evaporation.**

### G-15 · 🟢 QUEUE ITEM **Q-4** IS **ADOPTED BY THE DIRECTOR** INTO THE REFRESH PROTOCOL

v18b proposed Q-4 and explicitly declined to adopt it (*"the refresh protocol is
the director desk's"*). **The director has adopted it.** Both halves are now
standing protocol and both were executed by this lane:

- **`grep` every ruling label of the sitting across `docs/` before a records lane
  closes.** Run at the pin: R-A…R-I and R-L resolved; **R-J, R-K, R-M, R-N, R-O
  returned ZERO** — which is precisely how this cycle's five-ruling gap was
  found, and it is the same instrument that finally caught R-H.
- **Diff every dispatched job against a CHANGED TARGET FILE.** Run at close; the
  table is in the protocol section. **It is what caught G-8** — job 4's target
  file needed no change, so the job was already discharged and a "finding
  describing the repair" would have been false.
- **And its rider stands: a parallel lane is not a completeness check.**
  Redundancy catches measurement error, never scope omission, because both lanes
  inherit scope from one dispatch.

## v18 DELTA — the gate-(a) repair lane (`d44446e0` → `6c7f82dac015`, 2026-09-01)

**THIS IS A DELTA BLOCK, NOT A v18 REFRESH, and the distinction is load-bearing.**
A refresh re-derives the whole board — the PR classification, the keeper table,
the stage-0 table, the parity/bench/matrix gate counts, the sidecar walk. **This
lane re-derived none of that.** It is a repair lane with four jobs, and it
re-derived exactly what those four jobs touch: the six gate-(a) rows, the two
R-D maps' headline figures, every provenance sha in `ff-verdicts.json`, and the
cross-ISO cascade evidence. **Every other figure on this board still carries its
v17 pin `d44446e0` and is NOT re-verified here.** Read it that way.

**PIN: `6c7f82dac015`** (merge of #4485), held stable across two polls. The v17
board's own pin `d44446e0` is **21 commits / 2 merged PRs behind** it — and one
of those two PRs (#4485) **overturns a finding this lane was dispatched to
record** (D-4 below).

**Headline: the R-I repair the last lane was dispatched to make is now MADE — one
gate verdict moves, ERCOT `fail → PASS` — and four-instrument alignment is
RESTORED at {ERCOT, NEISO, PJM}. Three of this lane's four jobs came back
different from the dispatch: one bigger, one overturned, one confirmed exactly.**

### D-1 · 🟢 R-I IS EXECUTED — GATE (a) IS ALIGNED, AND THE ALIGNMENT BREAK OF F-6 IS CLOSED

v17's **F-6** recorded that four of six gate-(a) stamps were stale and that
ERCOT's leg failed *on a stale stamp rather than on a model fact*. **It recorded
it and did not repair it.** This lane repairs it. All six rows re-derived live
from `keepers/<ISO>.json` + `calibration-complete.json` at the pin; **the
director's derivation is confirmed in all six**, keeper ids included.

| ISO | seed's stamp (pre) | live keeper | (a) before | (a) after |
|---|---|---|---|---|
| **ERCOT** | `2026-08-24-231-tie-zone-measured` | `2026-08-25-234-eastex-identity` | fail | **PASS ⬅ MOVED** |
| CAISO | `caiso-200-h1-memberpanel` | `2026-08-26-caiso-220-c1-crosswalk` | fail | fail (stamp only) |
| MISO | `miso-177-rho-measured` | `2026-08-30-miso-191-bexit` | fail | fail (stamp only) |
| NYISO | `nyiso-157-par-attribution` | `2026-08-30-nyiso-159-loss-surface` | fail | fail (stamp only) |
| PJM | `pjm-162-inputclock` | same — current | pass | pass (**untouched, byte-identical**) |
| NEISO | `neiso-99-joint-p1` | same — current | pass | pass (**untouched, byte-identical**) |

**The one verdict that moves moves on the MARKER, not on the re-key.** ERCOT
entered `complete` on 2026-08-31 (ercot-247), so the stale row's assertion
*"Absent from the `complete` block"* was **false at this pin** and is withdrawn.
Gate (a) is decided on the marker — full-span keeper **and** a `complete` entry —
and ERCOT holds both, so the leg passes mechanically.

**Per R-I, ERCOT's row now cites BOTH determination values, neither replacing the
other:** the ISO-level partition rollup **CALIBRATED** (ercot-246 ruling of
2026-08-31, `keepers/ERCOT.json config_partition`; forward keeper on {2024, 2025}
and the 2023 carve-out `236-swcap-clip-k33` on {2023}, both CALIBRATED on their
own spans) **and** the registered run-level **NOT-YET** at full magnitude
(C3a-2023 model 38.75 vs actual 64.32 $/MWh = **−39.7 %**, tol ±10 %; C3b-2023
monthly load-weighted **NRMSE 0.730**, tol ≤0.20 — both re-read from
`status/ERCOT.js`, not from v17's F-5). A reader comparing the two boards now
sees **why** they differ instead of a contradiction.

**The backcast half of R-I was verified already-satisfied** before anything was
edited: `build_status.py` implements the partition rollup (l.515–583) and
`status/ERCOT.js` publishes `determination: CALIBRATED` with
`registered_determination: NOT-YET` preserved beside it.

**Blast radius, stated because a gate row is an expensive object.** Structural
diff of `program-status.json`: **exactly 16 changed leaves**, all inside the four
repaired `a_keeper_marker` rows plus `gate_a_provenance`. **PJM's and NEISO's rows
are byte-identical.** **NO ISO's `open` CHANGES** — ERCOT is now
(a) PASS · (b) fail · (c) pass · (d) `none`, so leg (b) and the absent leg (d)
still close its full-solve gate; `open` stays **false**, and NEISO remains the
only ISO with `open: true`. **Gate-(a) passers are now {ERCOT, PJM, NEISO} = the
full `complete` membership**, so three instruments and the forecast board agree.
Nothing was solved, scored or registered; no keeper shard, marker, freeze file or
matrix shard was touched. `gate_a_provenance` keeps its deliberately-distinct
field names (`derived_at_*`, never `scored_at_*`) — re-verified by running
`check_forecast_staleness.py`, which still classes the seed as **1 stamped,
0 scored**. **No CI guard for gate-(a) staleness was added**; it stays an open
owner queue item (Q-1 below).

### D-2 · 🔴 THE `ff-verdicts.json` PROVENANCE DEFECT IS **TWO**, NOT ONE — AND IT BLINDS THE STALENESS INSTRUMENT

The dispatch named `neiso-t3`'s `scored_at_sha` `89dacc4c0343`. **The count
matters — one instance and twenty are different problems — so all 46 sha
references in the file were tested, not just the named one.**

**⚠️ METHOD NOTE, because the obvious test gives a false answer here.** This
session's checkout is a **shallow clone (256 commits, earliest 2026-08-30)**, so
`git cat-file -t` reports **39 of 46** references unreachable. **That number is an
artifact and must not be quoted.** Re-tested against the **remote** (the
authoritative source), the true figure is:

> **2 of 46 sha references are unreachable. 12 distinct shas, 10 reachable.**

| verdict | field | sha | status |
|---|---|---|---|
| `neiso-t3` | `scored_at_sha` | `89dacc4c0343` | **unreachable** — the one the dispatch named |
| `neiso-t3-pre-fc6` | `scored_at_sha` | `271ad606c3fd` | **unreachable — A SECOND INSTANCE, not in the dispatch** |

Both are NEISO T3 verdicts, both `scored_at_sha`, both stamped 2026-08-31, both
by the `neiso-rc-repair` lane's re-score from branch commits that never reached
`main`. **All five `solved_at_sha` references are reachable.** Both
determinations are **HOLD** and are unaffected — only the provenance is
unverifiable. **No sha was fabricated and nothing was re-scored to obtain one**
(dispatch instruction, honoured).

**The consequence is worse than "unverifiable provenance", and the board should
carry the sharper version.** `89dacc4c0343` is the **newest** scored sha on the
gate-evidence class, i.e. the anchor the staleness instrument measures from — so
`check_forecast_staleness.py` cannot measure distance at all and reports
**"Staleness is UNKNOWN, which is not the same as fresh."** The instrument
already flags this itself, and names the right two causes ("shallow clone, or
scored on an unmerged branch"). **One unreachable stamp on the newest verdict
blinds the whole board's freshness reading.** Same class as the stage-0
manifest's `af1ccb6` (v16 F-5 / v17 E-7). → **Q-2.**

### D-3 · 🟢 THE TWO R-D MAPS AGREE EXACTLY — CROSS-REFERENCED, NEITHER WITHDRAWN

Re-verified independently of the director's check. Both
`DECISION-MAP-ercot-wind-entry-2026-08-31.md` (now 290 lines) and
`MAP-c1-wind-entry-closure-2026-09.md` (now 525 lines) carry **12.313 GW**
(= 12.663 actual − 0.350 model), **1.442 GW** best posture, **8.87 %**
(= 1.092/12.313, arithmetic checked), **13.77 %** naive sum, **0.00 pp**
joint-vs-signal. **No figure disagrees.** A cross-reference header was added to
each naming the other and which is canonical for which purpose — the DECISION-MAP
for the **ruling record**, the MAP for the **fuller closure map**. Neither is
deleted or superseded. The header on the MAP also corrects its own preamble claim
to be *"the first artifact to carry R-D"*: true at its base `54d5772c`, false at
this pin, and left in place as the honest record of what that lane could see.

### D-4 · 🔴 THE CASCADE RULE'S "NO EXPOSURE ELSEWHERE" FINDING IS **OVERTURNED** — MISO CARRIES A LIVE SIBLING DEFECT

**The dispatch asked this lane to record the rule together with a negative
finding: *"a generalizable trap with no evidenced exposure in the other five ISOs
at this pin."* THAT FRAMING DOES NOT SURVIVE AT THIS PIN, and recording it would
have put a false negative on the board.**

The rule itself stands, and is worth stating on **provenance**, not on the word
"nested" — both halves are live in this repo:

> **Summing the shadow prices of distinct nested constraints is CORRECT** (a
> marginal MW relieves all of them — this is what `results/rcpf.py` does to build
> a cumulative posted price). **Summing published cumulative product prices is
> WRONG** — that price already contains the lower products', so the sum
> double-counts. **A NESTED RESERVE CASCADE MUST BE MAXED, NEVER SUMMED.**

**What changed:** PR **#4485** (`nyiso-165`, merged into this pin, **after** the
director's `240e80e4`) ran the cross-ISO scan empirically rather than by
inspection and **found a live MISO instance**. Verified independently by this
lane at the pin, not read from the finding:

- `scripts/probes/_miso171_reserve_product_decomposition.py:205–206` sums MISO's
  **published** `GENREGMCP + GENSPINMCP + GENSUPPMCP` into `total` (and
  `reg + spin` into `regspin`). The cascade is monotone in **100.0000 %** of rows
  in every year and both markets — the identical signature to NYISO's.
- Re-derived from the committed record
  `results/calibration/_miso171_reserve_product_decomposition.json`: **12 summed
  cells, `total/reg` from 1.22× to 2.49×**, concentrating in the tail. The
  finding's two quoted cells reproduce **exactly** (`da_foreseen/rt_mcp`
  $181.40 vs $76.88 = **2.36×**; `scarce47/rt_mcp` $97.62 vs $46.44 = **2.10×**).
- **Mitigations confirmed:** the per-product fields are recorded alongside and are
  correct, so the record is recoverable without a re-solve; and **no prose cites a
  summed figure.** ⚠️ **A grep for `regspin` in `docs/` returns hits that are NOT
  citations** — they are the model-side `miso_rbdc_regspin` *mechanism* family, an
  unrelated name collision. Recorded so the next reader does not mistake them for
  exposure.
- **PJM, NEISO, CAISO, ERCOT are cleared with evidence** (PJM carries the cascade
  but pins a single product; NEISO deliberately uses the cascade top alone; CAISO's
  additions are nested-**region**, the legitimate half; ERCOT's are **MW
  quantities**, legitimately additive). **The director's negative finding was right
  about four of five ISOs and wrong about MISO** — and the difference is that #4485
  measured the data where the director inspected the code.

**Nothing was done about it here, and that is correct.** Rule 25 `[R-ISO-SCOPE]`:
a NYISO verdict never fills MISO's cell. No intake was touched, no cross-ISO audit
opened — **the calibration desk's call, not this program's**. → **Q-3.**

### D-5 · 🟠 THREE DIRECTOR-DESK DEFECTS, RECORDED BECAUSE THIS BOARD TRACKS ITS OWN

- **(a) A NEW FAILURE SHAPE: "LANDED BUT INCOMPLETE."** The v17 records lane was
  dispatched to execute R-I and instead **recorded it as F-6 and moved on**. This
  is *not* the shape the board has been watching for. v17's F-10 and the refresh
  protocol check **dispatch-vs-launch** — the two consecutive *never-launched*
  lanes. A lane that launches, lands, writes a correct finding, and **silently
  omits the repair it was dispatched to make** passes every never-launched check.
  **The next dispatch-vs-launch check must look for "landed but incomplete" as
  well as "never launched"** — i.e. diff each dispatched lane's *jobs* against its
  *artifacts*, not merely confirm a branch merged. Had this repair not been
  re-dispatched, F-6 would have sat on the board as a permanent standing
  observation of a defect that was one edit from repair.
- **(b) THE DUPLICATE R-D DISPATCH — ATTRIBUTED TO THE DIRECTOR.** R-D's map was
  produced twice by two lanes in the same window because the map was dispatched
  *after* the records lane had already executed it. **Neither lane erred**, and
  the two agree exactly (D-3). The dispatch ledger did not reflect work already
  landed at dispatch time — the same root cause as (a), read from the other end.
- **(c) THE DIRECTOR'S OWN DERIVATION BUG — a `null` frontier read as ACTIVE via
  `or {}`.** A withdrawn frontier block that is present-but-`null` fell through an
  `or {}` default and read as active, which **nearly reported CAISO and MISO as
  gaining frontier status**. Caught before publication; the active frontier set
  was and remains **{ERCOT, NEISO, PJM}**. Recorded because a derivation script
  that fails *open* on a governance object is the same class of instrument defect
  the board names in models: `or {}` turns "declared absent" into "not declared",
  and those are opposite facts.

### D-7 · 🔴 v18b — RULING **R-H**, RECORDED FOR THE FIRST TIME: THE nyiso-161 WINTER-FACE WAIVER CARD IS **RULED**, OPTION A, NOT-YET STANDS

**Verified absent before it was written, at pin `192460b6` — i.e. AFTER the v18
delta above had landed.** `grep "R-H"` across `docs/` matches only the rule ID
`[R-HOLDOUT]`; the string as a ruling label appears in **zero** files, this
board and plan §8 included. The 2026-08-31 REFRESH sitting produced **seven**
rulings; six were on the record and **this was the seventh**.

**THE RULING.** On the nyiso-161 winter-face waiver card — the card R-F parked
behind a dated trigger — the owner ruled **OPTION A: NOT-YET STANDS.**
Exhaustively, what A *is*:

- **No rubric amendment.** The rubric is untouched.
- **No new caveat class.** In particular **no access-blocked class** is created —
  which matters beyond NYISO, because CAISO's C3a residual is CEII-blocked on
  both lever routes and would have had an immediate claim on one.
- **The v3.0 tier guard is untouched**, and the line that **only C3c is
  non-downgrading** holds. Nothing joins C3c on the ledgerable list.
- **NOT-YET continues to mean exactly what it has meant**: *one identified input
  missing, everything else clean.* The determination is not redefined to
  accommodate the card.
- **NYISO's determination is unchanged** and stands as published: **NOT-YET on
  {C3a-2025, C3c}**.
- **The MyNYISO stakeholder-account access retry stays OPEN and needs no
  ruling** — a data-access attempt, not a determination question; A does not
  close it.

**🟢 AND THE RECORD MUST CARRY WHY A GOT *STRONGER* AFTER IT WAS RULED. C3c's Q2
STRENGTHENED the basis for A.** Q2 (nyiso-164, **CONFIRM**; independently
replicated by nyiso-165 after that lane first reached the opposite answer and
retracted it) establishes that NYISO's C3c caveat is supported **by NYISO's own
evidence**, not inherited from another ISO — so the **summer face is evidenced
as a genuine model-class limitation** rather than a published quantity the model
fails to bind. That leaves the **structural route intact and better grounded
than when the card was filed**: close the **winter** face → C3a-2025 returns to
≈ **−5.6 %**, inside band → **C3c becomes the lone failure** → the rule-22
standing rule (rubric v3.3) reads **CALIBRATED**. **A is not a dead end; it is
the route that keeps the standing rule honest.**

**CONSEQUENCE, EXECUTED HERE.** Owner-queue **item 1** presented this card as
*"servable at the next sitting, not waiting on anything"* — inviting the
director to re-serve a decided card. It is **RETIRED** in the queue below with
this disposition, and **F-3's closing clause, which carried the same error, is
annotated in place.** **This board does not re-open A, does not weigh it, and
takes no position beyond recording it.**

### D-8 · 🔴 v18b — THE FAILURE SHAPE D-5(a) NAMED HAPPENED **AGAIN, TWICE, IN THE CYCLE THAT NAMED IT**

Recorded plainly, because D-5(a) exists precisely so the next cycle catches this
and the next cycle did not.

- **(a) THE LANE THAT NAMED "LANDED BUT INCOMPLETE" WAS ITSELF INCOMPLETE.** The
  v18 delta executed R-I, cleared three records defects, wrote D-5(a) — and
  **omitted R-H**, leaving the ruled card served as open on the very queue it
  refreshed. D-5(a)'s prescription (*diff each dispatched lane's jobs against its
  artifacts*) would have caught it; the lane applied it to **v17** and not to
  **itself**.
- **(b) 🔴 AND A SECOND RECORDS LANE RAN THE SAME DISPATCH IN PARALLEL, AT THE
  SAME PIN — AND SHARED THE SAME BLIND SPOT.** At pin `6c7f82dac015` two
  audit-program records lanes were live on this identical dispatch:
  `claude/audit-gate-a-repair-12ewmv` (merged as **#4488**, the v18 delta above)
  and this one. **They independently reached the same two dispatch-overturning
  corrections** — MISO's live cascade defect, and *two* unreachable
  `scored_at_sha` rather than one — which is strong evidence that zero-solve
  measurement on committed artifacts reproduces. **And both omitted R-H.**
  **DURABLE LESSON: A DUPLICATE LANE IS NOT A SAFETY NET.** Redundancy catches
  *measurement* error, because two lanes measure independently. It does **not**
  catch a *scope* omission, because both copies inherit the scope from the same
  dispatch. **Only a completeness check against the SITTING'S OWN RULING LIST
  catches that** — `grep` each ruling label, which is exactly how R-H's absence
  was finally established. **Add it to the refresh protocol as a step, not a
  habit.**
- **(c) This is D-5(b)'s root cause repeating, not a new one.** D-5(b) traced the
  duplicate R-D map to *a dispatch ledger that did not reflect work already
  landed at dispatch time*. Here the same ledger did not reflect **work already
  in flight**. **Same defect, one step earlier in the lifecycle.**

### D-9 · 🟢 v18b — DATED CORRECTION TO D-4: MISO'S CASCADE DEFECT WAS LIVE WHEN D-4 WAS WRITTEN AND IS **REPAIRED** AT THIS PIN

**D-4's finding stands in full; only its tense is stale.** D-4 was written at
`6c7f82dac015`, where
`scripts/probes/_miso171_reserve_product_decomposition.py` still summed MISO's
published `GENREGMCP`/`GENSPINMCP`/`GENSUPPMCP`. At **`192460b6`** the
xiso-cascade lane (**#4497**, `2fe2f2db` *"Repair MISO ASM-MCP cascade sum:
aggregate by per-hour top, never sum [R-ACCURATE]"*) has **repaired it at
source**: the probe now emits `top` — the **mean of the per-hour cascade
max** — plus a `sync_only_increment`, and the docstring carries a dated
correction naming the superseded `regspin`/`total` fields. The companion commit
`4ba1ef24` adds dated corrections **at every summed-figure cite site**.

**What this changes and what it does not.** The **rule is unchanged and now
carried in code as well as prose**: *A NESTED RESERVE CASCADE MUST BE MAXED,
NEVER SUMMED*, stated on the **provenance** of the number — summing distinct
nested **shadow prices** is correct and is what
`results/rcpf.py::rcpf_product_prices` legitimately does; summing **published
cumulative product prices** double-counts. **D-4's magnitudes stand** (sum/max
**1.85–2.20×** in hours cleared > $50) as the measurement of what was repaired.
**The queue item D-6/Q-3 routed to MISO's lane is therefore satisfied on its
repair half** — but its **second half is NOT**: #4485 explicitly flagged that
**the fields' downstream use was never audited**, a question neither the scan
nor the repair opened. **That half stays open, and stays MISO's** (rule 25
`[R-ISO-SCOPE]`). **This lane repaired nothing and opened no cross-ISO audit.**

### D-6 · OPEN QUEUE ITEMS ADDED (owner)

| # | item | state |
|---|---|---|
| **Q-1** | **A CI guard for gate-(a) staleness.** Four of six stamps were stale for a second consecutive cycle, and the repair is manual each time. **Deliberately NOT built here** (dispatch instruction). | **OPEN — owner decision** |
| **Q-2** | **Two unreachable `scored_at_sha` in `ff-verdicts.json`** (`neiso-t3`, `neiso-t3-pre-fc6`), blinding the staleness anchor (D-2). Needs an owner call on the remedy: re-score to obtain a real sha, or record the stamps as permanently unverifiable. **No sha may be fabricated.** | **OPEN — owner decision** |
| **Q-3** | **The cascade rule + MISO's sibling defect** (D-4). ⚠️ **UPDATED at v18b (D-9): the REPAIR HALF IS DONE** — #4497 (`2fe2f2db`) fixed the probe at source to aggregate by per-hour cascade max, with dated corrections at every cite site. **The SECOND half stays OPEN and stays MISO's:** the summed fields' **downstream use was never audited**, a question neither the scan nor the repair opened. **Not this program's call.** | **PARTLY CLOSED — repair landed #4497; downstream-use audit still routed to the calibration desk** |
| **Q-4** | 🆕 **v18b — A COMPLETENESS STEP FOR THE REFRESH PROTOCOL.** Two independent records lanes ran the same dispatch at the same pin and **both omitted ruling R-H** (D-7/D-8). Redundancy catches measurement error, not scope omission. **Proposed step, cheap and mechanical: `grep` each ruling label of the sitting against `docs/` before a records lane closes, and diff each dispatched job against a changed target file.** Recorded as a protocol proposal, **not adopted here** — the refresh protocol is the director desk's. | **OPEN — owner/director decision** |

**What this lane did NOT do**, stated so the next director does not infer it: no
solve, no scoring, no registration on either dashboard; no keeper shard,
`calibration-complete.json` or `holdout-freeze.json` edit; no matrix shard touched
(rule 26 — this lane tests no mechanism); no CI guard added; no ISO's intake
touched; neither R-D map deleted.

## What moved — v17 CYCLE (`54ca19ae..d44446e0`, "the refresh-ruling cycle")

**Read F-1…F-3 as one act:** they are the 2026-08-31 owner **REFRESH sitting**,
executed by this dispatched records lane under the standing deviation (the
supersession v16 recorded was one-sitting and is spent).

### F-1 · 🟢 R-D EXECUTED — THE C-1 WIND QUESTION IS RESTED AT THIS GRAIN, WITH A MAP, AND NOTHING IS ARMED OR REJECTED

Owner ruling R-D, on `docs/FINDING-c1-joint-wind-ab-2026-08-31.md` (R-B's
chartered A/B; both kill-gates PASS; **`NON_COMPLEMENTARY`**). Executed per the
**caiso-222 §1(c) option-3 pattern** — the residual is designated **ATTRIBUTED
AND CLOSED at this representation grain** with a decision map attached rather
than an open investigation. **Retires v16 owner-queue item 2.**

**The measurement, re-read from the finding at this pin.** The joint arm builds
wind **1.442 GW** — to the megawatt the committed signal-alone arm's number —
closing **8.87 %** of the **12.313 GW** miss, while **the volume rule contributes
exactly ZERO wind** on a dual-based level (naive sum of the singles 13.77 %; best
single 8.87 %; joint 8.87 %; difference **0.00 pp**). The walk is **live, not
inert**: it changes **exactly one decision** in the whole 2021–2025 window —
entering-2023 solar **5,550 MW → 0** — with everything else byte-identical to the
pure disarm arm. The volume rule's 4.91 % under the *shipped* signal is
identified as a **shipped-signal artifact**.

**The attribution.** A **zone-flat, ORDC-dominated signal at hub grain**:
`zonal_mean_range` and `hourly_cross_zone_spread` measured **exactly 0.0**, ~90 %
of the dispersion is the ORDC adder, West build-zone capture **0.494/0.805/0.927**
shipped against **0.988/0.988/1.055** on the model's own duals.

**Published open, not retired: 91.1 % of the miss stays open**, every addition
band FAILs in both arms, and the dual level's adequacy cost is **terminal RM
25.19 → 38.84 %, +13.65 pp** on a [13.8 %, 28.7 %] band. **Nothing is armed** —
`entry_lookahead_reprice` verified at `ScenarioConfig` default `True`
(`scenarios.py:3919`) — and **nothing is rejected**. **Re-open conditions,
exhaustive:** a NEW MEASURED DRIVER (rule 13 `[R-MEASURED]`), or an
OWNER-CHARTERED REPRESENTATION-GRAIN CHANGE (the caiso-223 class — a program, not
a lever). Neither is reachable by re-running a lever at hub grain.

**Records:** `docs/DECISION-MAP-ercot-wind-entry-2026-08-31.md` (new) ·
`docs/calibration-log/ercot.md` · `docs/calibration-log/governance.md` · R-D
ruling stamps appended to the **evidence strings only** of the two joint-wind
ERCOT cells. **⚠️ ONE DISPATCH CORRECTION:** the dispatch said "cells stay O".
Re-read at the pin, the two cells are **`entry_lookahead_reprice` cell K / fc O**
and **`entry_margin_exhaustion` cell O / fc K** — neither is "O/O". The binding
instruction (**no verdict letter changes**) was followed exactly; both cells are
byte-unchanged except for the appended stamp, and `check_mechanism_matrix.py`
exits **0** after the edit (2 lines changed, 2 inserted / 2 deleted, whole file).

### F-2 · 🔵 R-E RECORDED — AND ITS TWO CHARTERED QUESTIONS HAVE ALREADY REPORTED AT THIS PIN: Q1 **REAL**, Q2 **CONFIRM**

R-E charters the C3c scarcity program's **Q1 + Q2, chained** (Q1 the PJM phantom
audit first; Q2 opens only on Q1 = REAL), with **Q3 unopened and explicitly not
recommended** — it is an architecture decision colliding with rules 4
`[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint. Its execution lane is
dispatched separately. **The dispatch-vs-launch check on it does not read
"launched" — it reads DONE:**

- **Q1 = REAL** — pjm-164, **#4456**,
  `docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`, zero solve. PJM's
  reserve-dual channel is **not** the ercot-214 phantom: 2025 model-tail overlap
  with reality's tail **14 of 32** hours (0.44 of the model tail, 0.24 of the
  actual), **13** of them with a positive reserve dual, against published
  DataMiner2 reserve MCPs; 2023–24 near-zero overlap but near-zero reserve
  involvement, so that mis-timing is not the reserve channel's. Three honest
  caveats, **none determination-level**.
- **Q2 = CONFIRM** — nyiso-164, **#4459**,
  `docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`, zero solve. The
  pre-registered kill gate fires on **both** clauses (NYCA-tier reserve price
  never exceeds the concurrent LMP in **65/65** tail hours; model carries
  **5.08/3.92/2.99 GW** of reserve-carrying headroom against a 2,620 MW NYCA
  30-min requirement, NYCA families at zero dual and zero shortfall in all
  **26,280** hours). **NYISO's C3c ledger is CONFIRMED on its own evidence**, and
  the lane reports the interpretation reversal rather than burying it.

**Two consequences for this board's queue, both derived rather than assumed:**
the **PJM determination-integrity card the dispatch made conditional on Q1 =
PHANTOM does NOT open** — no PJM keeper rests on a phantom channel; and **R-F's
trigger is met** (F-3). **Neither lane moved a keeper, marker, determination or
matrix cell, and neither spent a holdout year.**

### F-3 · 🟠 R-F EXECUTED — THE nyiso-161 CARD IS PARKED BEHIND A DATED TRIGGER, AND THE TRIGGER HAS ALREADY FIRED

Owner ruling R-F: **neither A (NOT-YET stands) nor C (declare CALIBRATED)**. The
card **stays filed** and moves from *open-undecided* to **PARKED — re-serve when
the C3c program's Q1/Q2 report lands**. **NYISO's determination is unchanged and
restated: NOT-YET on {C3a-2025 −11.5 %, C3c}.**

**Re-derived at this pin, and it changes how the item must be carried: the report
has landed and Q1 returned REAL, not PHANTOM** (F-2). So the card is not
*waiting* — it is **PARKED-AND-RE-SERVABLE, servable at the next sitting.**
Carrying it as "waiting on a report" would leave the next reader expecting
something that has already arrived. **The deferral itself is untouched: the owner
deferred, and only the owner un-defers.** Standing context, unchanged: the
**AORR access route is PERMANENTLY CLOSED by owner decision** and **nyiso-97 §5
re-open condition 3 is WITHDRAWN** (conditions 1 and 2 stay live passive watch
items), so the winter face of C3a-2025 is **permanently unidentifiable from
obtainable data**; **option B is dominated** (marker re-entry needs CALIBRATED,
not CWC); and **the precedent surface is not NYISO-only** — CAISO's C3a residual
is CEII-blocked on both lever routes and would have an immediate claim on any
access-blocked caveat class.

> **🔴 ↳ v18b CORRECTION — "PARKED-AND-RE-SERVABLE" IS SUPERSEDED. THE CARD IS
> NOT RE-SERVABLE; IT IS RULED.** The owner ruled it at the same 2026-08-31
> sitting, as **R-H — OPTION A, NOT-YET STANDS** — and that ruling reached no
> artifact until **v18b** (D-7), which is why this finding, and the queue item
> it fed, carried the card as open for two board versions. **F-3's account of
> R-F is accurate as history and its standing-context paragraph still holds; only
> the "servable at the next sitting" reading is withdrawn.** The queue item is
> **RETIRED**. **Do not re-serve it.**

### F-4 · 🟢 R-G EXECUTED — nyiso-160/leg2 CLOSED BY ARCHIVE, AND THE PROMOTE-OR-ARCHIVE ITEM RETIRES FOR GOOD

On `docs/FINDING-nyiso-leg2-reverify-2026-08-31.md` (nyiso-162, #4431, R-C's
zero-solve re-verification), the owner ruled **archive**. The re-verification
dissolved its own question: **there is NO candidate** — leg2 produced a stop with
cause at access, not an object (no prereg, no mechanism, no A/B pair, no control)
— and the object that *does* exist is the keeper's own recipe re-established at
HEAD, scoring **identically** to the live keeper: **zero record-level differences
across 60 scored records** (the sole difference anywhere is the C6 attestation
narrative string), **0 solve-affecting levers**, **max |Δ| = 0 over 1,043,280
hourly rows**, `metrics.json` 58/60 leaves identical. Promotion would have been a
formal no-op that **weakened** the designation's evidentiary basis; archiving
costs nothing evidentially. **The registered runs and the findings stay on the
record**; the item is **not re-servable**, because the object it named does not
exist. Keeper and determination untouched, `audit_keepers --iso NYISO` PASS 0/0,
**no matrix cell moves**.

### F-5 · 🟢 ERCOT TOOK ITS FIRST RULE-22 MARKER EVER — AND ITS FIRST FRONTIER — IN THE SAME OWNER UTTERANCE

Re-derived from the live files, not from the dispatch (which did not mention it
at all). `frontend/data/backcast/calibration-complete.json` `complete` now holds
**{ERCOT, NEISO, PJM}**; `keepers/ERCOT.json` carries a new `frontier` block
`declared: 2026-08-31`. Owner, quoted in the marker: *"I think you can declare it
complete / frontier."* The determination basis is the **ercot-246 ruling** — a
partitioned keeper's ISO-level determination is the **worst config determination
over the DESIGNATED spans** — under which the forward config on {2024, 2025} and
the 2023 carve-out on {2023} both read CALIBRATED, so ERCOT reads **CALIBRATED**.
The marker's own text carries the honest record at full magnitude: the forward
keeper's **registered unrestricted 3-year determination is still NOT-YET** on
{C3a-2023 −39.7 %, C3b-2023 0.730}, and that registered record stands published
untouched. `audit_keepers` M1b was extended in the same commit to re-verify the
partition rollup live rather than read the shard's assertion, and it **PASSES**
at this pin.

**Scope, stated because a marker is the most expensive object on this board:**
`complete` authorizes the **validation tier only**. `final` is **EMPTY**
(`_note` only), ERCOT is absent from it, the freeze stays tier-scoped to the
locked test for every ISO, and **no ISO has ever spent a locked-test year** —
re-verified at the pin by walking all **58** sidecars (year histogram
**{2022: 2, 2023: 56, 2024: 52, 2025: 52}**; the scan for {≤2018, 2019, 2026}
returns **NONE**; the only out-of-training registrations remain the two
authorized 2022 touchpoints).

### F-6 · 🔴 FOUR-INSTRUMENT ALIGNMENT BROKE AGAIN — AND THE OUTLIER IS A STALE STAMP, NOT A MODEL FACT

v16's headline was alignment restored at {PJM, NEISO}. At this pin **three of
four agree at {ERCOT, NEISO, PJM}** — CALIBRATED = `complete` = active
`frontier` — and the **forecast gate-(a) passers remain {PJM, NEISO}**.

Re-derived field-by-field against the live shards, exactly as v16's protocol
requires (the seed is a different program's file and its schema is re-read, not
assumed):

| ISO | seed's gate-(a) keeper | live keeper | (a) | (b) | (c) | (d) | `open` |
|---|---|---|---|---|---|---|---|
| ERCOT | `2026-08-24-231-tie-zone-measured` | ⬅ `234-eastex-identity` | **fail — STALE stamp** | fail | pass | none | false |
| PJM | `pjm-162-inputclock` | same | **pass — current** | fail | pass | none | false |
| CAISO | `caiso-200-h1-memberpanel` | `caiso-220-c1-crosswalk` | fail — STALE | fail | fail | none | false |
| NYISO | `nyiso-157-par-attribution` | `nyiso-159-loss-surface` | fail — STALE | pass | pass | none | false |
| NEISO | `neiso-99-joint-p1` | same | **pass — current** | pass | pass | **granted** | **TRUE** |
| MISO | `miso-177-rho-measured` | ⬅ `miso-191-bexit` | fail — STALE | fail | pass | none | false |

**The break is instrument-side.** ERCOT now holds `complete` and reads
CALIBRATED, and its gate-(a) fails **on a stamp naming a keeper two promotions
old**. **Four of six stamps are stale** (ERCOT, CAISO, NYISO, MISO) — the same
count as v16 but with MISO now two promotions behind rather than one.

**🟢 AND A FIRST: NEISO'S FULL-SOLVE AUTHORIZATION GATE IS OPEN.** v16 recorded
*"NO ISO'S FULL-SOLVE AUTHORIZATION GATE OPENS, and none opened from this
refresh"*, with leg (d) `none` everywhere. At this pin NEISO reads
**(a)+(b)+(c)+(d) all held, `open: true`** — leg (d) **granted** by the
T3-NEISO-GOLDEN lane, which also measured NEISO's T3 BAU golden (25/25 years).
**This is the forecast program's board and this lane adjudicates none of it**;
it is recorded because a leg this board has published as `none` for every ISO,
every cycle, has moved.

### F-7 · 🔵 THE CALIBRATION SWEEP — 18 PRs ACROSS 10 LANES, AND EXACTLY ONE PROMOTION (recorded, not adjudicated)

Recorded from the merge subjects and the landed artifacts, never adjudicated by
this board:

- **ERCOT — the biggest state change of the window, and it is not a keeper.**
  The ercot-245 Phase-0 census **KILLED the per-class commitment-state bound**
  (K-A ST mass, K-C saturation, K-T gas classes fire; Phase-1 **not licensed**),
  **ercot-246** ruled the ISO-level determination of a partitioned keeper, and
  **ercot-247** took the `complete` + `frontier` declaration (F-5). Keeper
  `2026-08-25-234-eastex-identity` **unmoved**.
- **MISO — the cycle's only promotion**, `miso-188-rvsscope` →
  **`2026-08-30-miso-191-bexit`** (binning-aware exit-cohort delivery, #4433 +
  the registrations). Its C3a row moved **+3.5 % → +0.1 % (2023)** and
  **−4.3 % → −4.6 % (2024)**; **C3a-2025 −12.3 % is unchanged and still the lone
  fail**. Separately **miso-192** (D-4 posture) and **miso-193**
  (`cc_duct_peaking`, registered as a rejected probe with its bundle sidecars,
  cell **U → K**) landed.
- **CAISO — UNMOVED.** caiso-226 (OFO intake) and **caiso-227** (C3a-2025
  root-cause / PS intake) landed, and **caiso-228's SoCalGas OFO gas-deliverability
  arm DIED AT GATE D1 with no solve**. Terminal rest undisturbed; C3a-2024/2025
  still +12.5 / +15.5 %.
- **NYISO — no keeper motion; four records sessions.** nyiso-162 (R-C), nyiso-163
  (+163b: the AORR access route **permanently closed**, the C3c program opened),
  nyiso-164 (**Q2 = CONFIRM**). Determination unchanged.
- **PJM — untouched for a NINTH consecutive cycle, and it was audited rather than
  changed.** pjm-164 ran **Q1** against its own CALIBRATED keeper and returned
  **REAL** (F-2). Still the only 8/8 zero-caveat scorecard and still the only
  current stage-0 row.
- **NEISO — UNMOVED on the backcast**; its `final` grant stays **DATA-BLOCKED**.
  On the forecast board it became the first ISO with an **open** gate (F-6).
- **The capx desk (a DIFFERENT program) merged 12 PRs across 8 lanes** — D12-A
  (#4429), D3 (#4455/#4458), D4-I3 (#4460), D8-RE (#4457), the S-6 and S-123-V
  verifies (#4436/#4441), the T3 NEISO golden (#4447/#4452) and three
  `calibration-workstream-relaunch` **director refreshes** (#4446/#4453/#4461).
  **Recorded only for shared-surface touches.** ⚠️ **Three of its eight branch
  names read as calibration lanes** and were reclassified by commit content —
  they account for **6 of its 12 PRs** (F-8's methodological half).

### F-8 · 🟠 THREE FIGURES THE DISPATCH ASSERTED ARE RE-DERIVED **DIFFERENT** — WHICH IS THE PROTOCOL WORKING

Recorded plainly because the dispatch instructed *"trust nothing in this
prompt"*, and the instruction earned its keep:

| dispatch asserted | re-derived at `d44446e0` |
|---|---|
| parity **60 runs / 95 dirs** | **58 runs / 93 bundle dirs** |
| bench **0 STALE, 0 drift** | **0 STALE, 19 of 20 parts WITH engine drift** |
| the two joint-wind cells "stay **O**" | **cell K / fc O** and **cell O / fc K** — neither is O/O |

The bench line is the substantive one: v16 predicted the WARNs return "on the
first engine commit dated 2026-08-31 or later", then measured **20 of 20** in its
post-pin block. At this pin it is **19 of 20** — and the one part that does *not*
WARN is **MISO/2023**, which was **rewritten by the miso-191 registration**
(`1b419b7b`, 2026-08-31 00:33 UTC) and is therefore *newer* than the three engine
commits, not fresher in any repaired sense. The instrument is behaving exactly as
v16 diagnosed it; nothing was repaired.

## What moved — v16 CYCLE (v16 record, RETAINED as history) (`69ae4dc7..54ca19ae`, "the decision-card cycle")

**Read F-1…F-4 as one act.** They are the 2026-08-30 owner **decision-card**
sitting — a *second, later* sitting than v15's PM rulings — all four cards
executed inside the same window, and, by an explicit one-sitting owner
supersession of the standing deviation, executed **by the director desk itself**
rather than dispatched (F-10).

### F-1 · 🟢 CARD 1 EXECUTED — THE PJM STAGE-0 GOLDEN IS CAPTURED, AND THE STAGE-0 TABLE HAS ITS FIRST CURRENT ROW

The capture this board has called *the cheapest and the largest gap* on
**seven consecutive boards** was taken (#4369). Re-derived at the pin from the
committed manifest, not read from the ledger entry:
`results/regression-goldens/perfb-stage0/manifest.json` `keepers` now holds
**all six ISOs** (v15: five), the PJM entry's `keeper_id` is
**`2026-08-15-pjm-162-inputclock`** which **byte-matches the live keeper**, its
`years` are `[2023, 2024, 2025]` (rule 16, the keeper's own recorded span), and
its per-file `content_hashes` are present. The manifest's top-level `git_sha` is
**`1cfea72`**, which `git cat-file` resolves **and** `merge-base --is-ancestor`
places **inside `origin/main`** — the `af1ccb6` defect is not repeated for this
capture.

**The scope was exactly the card and no more: WS3 stays PARKED.** Card 1
explicitly DECLINED the full freeze + golden-tier restart and the
captures-only option. So **G2 leg 1 keeps both of its parks** — this is a
scoped capture inside a parked workstream, not a restart, and nothing in the
G2 leg list moves.

The capture's own operational record is on the plan's §8 entry and is honest
about what it cost: the first attempt died on the container's 13.3 GiB cgroup
RAM limit and succeeded only after a 12 GB swapfile; it needed a re-fetch of
the converted `pjm-da-virtuals` corpus; and it WARNed on a missing PJM
hydro-plant-modes partition. **Fidelity oracle: 256 recorded flags replayed
identically, `scenario_config` 713 matched / 0 drifted, 15 HEAD-only meta keys
(post-freeze `ScenarioConfig` additions).** For whoever un-parks WS3 the
operational half is the transferable part: **assume a re-capture is a real
solve, and assume it needs the swapfile.**

### F-2 · 🔵 CARD 2 EXECUTED — THE HOMELESS T1-H CAPACITY-ENTRY DEFECT GOT A CHARTER, A LANE, AND A MEASURED A/B IN ONE DAY

v15's owner-queue item 6 — *"the T1-H capacity-entry defect (two defects, not
one) still has no charter and no home"*, carried since v13 item 11 across
**three boards** — is **retired**. The charter
`docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md` was written and then run to
completion in the same window:

- **Phase 0** (#4369, `docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md`) —
  zero-solve characterization from committed T1-H artifacts.
- **Phase 1 Leg A** (#4419 + #4426,
  `docs/FINDING-t1h-capentry-phase1-ab-2026-08-30.md`) — the storage-entry
  **D-2 + D-3 joint repair A/B'd on one HEAD**. Both charter kill-gates PASS:
  **K1 had nothing to fire on** (every addition-metric band identical between
  arms to the digit) and **K2 (inert) does not fire** (the storage-mix rows
  differ). The arm reproduces the Phase-0 §3.3 pre-registered signature
  byte-exact: `iron_air` 3,000 + `flow_battery` 2,000 MW (64.0 h, li-ion 0 %)
  → **`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000 MW (5.6 h, li-ion 100 %)** —
  the 1.6 h class ERCOT actually built. Couplings reported at full magnitude:
  the ledger reserve-margin path shifts **down** (8.54 → 6.98 / 14.65 → 13.10
  / 25.19 → 23.61 %) with **no downstream decision flipping**, and co2
  (reported-only) moves −0.49 / −0.52 / **+0.34** Mt.
- **ERCOT matrix cells verified at the pin, not asserted:**
  `storage_entry_availability_gate` and `storage_entry_cost_normalized_rank`
  both read **`cell: "O", fc: "O"`** in `mechanism-matrix/ERCOT.js` with the
  Leg-A A/B as citation — **`U` → `O`, measured, ARMING OPEN**.

**Nothing is armed, and arming is an owner decision on this A/B record** — the
charter's own line, and the lane held it: both `ScenarioConfig` fields ship
**default-OFF**, registered on the **forecast** namespace only, with the
backcast registry, every keeper shard, `calibration-complete.json`,
`holdout-freeze.json` and `program-status.json` untouched.

**Leg B (the separate wind leg) is a measurement rung and stayed one.** The
dual-based signal object closes **8.87 %** of the wind entry miss (model
0.350 → 1.442 GW against 12.663 GW actual; remaining gap 12.313 → 11.221 GW),
**leaving 91.1 % open** — and the same run's terminal reserve margin *worsens*
25.19 → 40.24 % and its gas_ct and storage bands move the other way. The
finding proposes no lever and states so: *"Leg B does not become a repair rung
on this evidence."* The measured input for the owner's **C-1 signal-object
call** is delivered; the call is not made.

### F-3 · 🟢 CARD 3 EXECUTED — "RE-VERIFY REQUIRED" IS NOW A STANDING RULE

The cross-lane re-grade precedent carried on this board since v13 (the
nyiso-143 D-4 rider + the shared-benchmark determination flip) has a rule.
Verified in place at the pin: `docs/calibration-log/governance.md`, the
2026-08-30 entry, **Ruling 1 — CROSS-LANE RE-GRADE: RE-VERIFY REQUIRED
(standing rule)**. A scorer or shared-file change that flips another lane's or
program's committed state now requires **the affected lane's own D-5(b)-style
re-verification from committed artifacts, never a solve**, before the flip
publishes — and a disagreeing re-verification **stops** the flip and escalates.
**Retires v15 owner-queue item 5.** The *adjacent* instance v15 attached to
that item (#4343, a different program writing this program's marker file) is
now covered by the rule going forward, and the Watch entry is re-scoped to the
class rather than the instance.

### F-4 · 🟢 CARD 4 EXECUTED — THE NYISO FRONTIER IS REVERTED, AND ALL FOUR INSTRUMENTS ALIGN

Owner, verbatim on the record: *"NYISO is not frontier it was reverted bc it's
not yet so it's PJM and NEISO only."* Executed as the **append-only**
`reverted_2026-08-30` key in `keepers/NYISO.json` `frontier` — the 2026-08-23
ratification and R-1's currency annotation are **retained as history**, not
deleted. Verified at the pin: the block carries `declared: 2026-08-23`,
`withdrawn: 2026-08-30`, `keeper_at_withdrawal:
2026-08-30-nyiso-157-par-attribution`, the owner verbatim, **and** the
`calibration-keeper-text-auditor`'s machine-readable `withdrawn` /
`withdrawn_note` mirror, added specifically so
`docs/codebase-site/js/calibration-status.js` `frontierActive()` **suppresses
the FRONTIER badge** rather than leaving the dashboard asserting a reverted
claim. That mirror is the interesting half: **v15's Watch item "evidence prose
is gate-checked nowhere" got its first machine-readable answer** — one field,
one ISO, by hand, but a rendering-drift gap closed at the renderer rather than
in prose.

**Retires v15 owner-queue item 1** (the board's top item for two cycles in one
form or another) and sets the standing rule **marker-master**: a frontier does
not survive its ISO leaving CALIBRATED/`complete`.

*(Records note, no action: `keeper_at_withdrawal` names nyiso-157, which the
same window superseded with nyiso-159. That is correct as history — it records
the keeper at the moment of withdrawal — and is flagged only so a later reader
does not mistake it for a stale currency defect of the R-1 class.)*

### F-5 · 🔴 RE-DERIVING E-7 FOUND IT IS FIVE-WIDE, AND THE `af1ccb6` DEFECT WAS OVERWRITTEN RATHER THAN RESOLVED

v15's E-7 recorded that a top-15 retention prune removed the **ERCOT** stage-0
golden's provenance run from the registry. **Re-deriving the whole table rather
than carrying it — the v15 protocol amendment, applied — shows the ERCOT case
was the visible instance of a five-wide condition.** At the pin, each capture's
`keeper_id` tested for a committed registry sidecar:

| capture's `keeper_id` | registry sidecar |
|---|---|
| `2026-08-15-ercot204-rule26-delete` | **MISSING** |
| `2026-08-16-caiso-197-w2-r5` | **MISSING** |
| `2026-08-16-miso-160-wefor-shape` | **MISSING** |
| `2026-08-14-neiso-93-envelope` | **MISSING** |
| `2026-08-16-nyiso-140-layup-exclusion` | **MISSING** |
| `2026-08-15-pjm-162-inputclock` | **PRESENT** |

**All five were already missing at `69ae4dc7`** (tested at both revs) — so this
is not new damage this window; it is v15 having reported the *motion* (ERCOT's
prune happened in its window) where the *condition* already covered five. **The
only capture whose provenance run is registered is the one taken this window.**

**And the manifest's provenance sha problem changed shape.** `af1ccb6` no
longer appears anywhere in the manifest (`grep` count 0). It was not resolved —
the Card-1 capture's diff is `-  "git_sha": "af1ccb6",` / `+  "git_sha":
"1cfea72",` against **124 inserted lines that add only the PJM entry**. The
manifest has **one** top-level `git_sha` for **six** captures taken at six
different trees and **no per-entry provenance sha** (entry fields verified:
`bundle`, `content_hashes`, `defaulted_unrecorded_params`,
`dropped_dead_config_keys`, `fidelity`, `hours`, `keeper_id`,
`recorded_flag_count`, `years`). So the five older captures now carry a sha
that **resolves and is wrong** — strictly harder to notice than one that did
not resolve at all.

**This is a schema limitation, not an error by the Card-1 lane** — the lane
wrote the field its script writes, and recorded a resolvable sha, which is the
improvement it was asked for. The consequence for WS3 is unchanged in kind and
sharper in fact: **the per-file `content_hashes` remain the only sound
verification instrument**, and the restart checklist's item 11 (record
provenance *inside* the manifest) now has a second, independent reason —
**per-entry**, not just self-contained.

### F-6 · 🟢 AUDIT ROW O7 IS CLOSED — THE FIRST WS1 ROW TO MOVE IN THREE CYCLES

`docs/audit/third-party-audit-2026-08.md` row **O7** reads **CLOSED 2026-08-30**
at the pin (#4377; the row's own diff is the only change to `docs/audit/` in the
whole window). The owner's Door-2 ruling — *keeper-moving restoration DECLINED,
accept-as-limitation DECLINED, the §5 attribution-harness partial AUTHORIZED* —
was built **and exercised** on a real year:

- **HP-1 PASS**: a de-laddered leg whose **P0, startup markup, bridge min-gen
  floors and committed-row run stats are hash-provably BIT-IDENTICAL** to the
  keeper's, both adaptive passes — which is precisely the attribution the
  forfeiture had cost.
- **The decomposition is itself a finding**: on the 2023 `ercot236_k33_clip`
  A/B, the ladder's **pricing** channel at the keeper's own commitment state is
  **−$0.02/MWh**, while **commitment + interaction carries +$2.26/MWh of the
  +$2.24/MWh whole** (74/132 committed rows, 12,380 MW commitment delta). The
  ladder is essentially **not** a pricing mechanism at this recipe; it is a
  commitment mechanism.
- What stays true permanently, now measured rather than open: **R1's own
  arm/off comparison remains whole-solve** — the forfeiture is a property of
  the mechanism, not of its wiring — carried as the ERCOT keeper's **named
  permanent limitation** (ercot-188/E2, unexpired). **Keeper untouched.**

Records: `docs/FINDING-o7-attribution-harness-2026-08-30.md`;
`results/calibration/o7_attribution_harness_2023.json`; harness
`scripts/probes/o7_attribution_harness.py` (+17 toy tests).

### F-7 · 🟠 NYISO PROMOTED (157 → 159) — THE ONE KEEPER MOTION, AND IT IMPROVED THE SCORECARD

The cycle's only promotion. Re-read from the shards at the pin, not carried:
`2026-08-30-nyiso-159-loss-surface`, determination **`NOT-YET`**, grade
**8 scored / 6 target / 2 fails / 0 ledgered** against nyiso-157's
**8 / 5 / 3 / 0**. **C3b (`price_shape`) left the fail set** — the measured
zonal loss surface closed it — leaving **{C3a-2025, C3c}**. C3a(RT) moves
+1.0 → **+2.3 %** (2023), −2.0 → **−1.2 %** (2024), −12.0 → **−11.5 %** (2025).

Two governance readings, both verified rather than assumed:

- **C3c reads FAIL, not CAVEAT, and that is the standing rule working.** The
  C3c standing rule requires C3c to be the **lone** failing criterion; C3a-2025
  also fails, so guard (a) keeps the rule silent and **both failures stand**.
  `caveats.ledgered` is empty for this keeper.
- **No `complete` re-key was owed.** NYISO's `complete` marker was withdrawn on
  2026-08-30 (Q5-W), so rule 22 D-5(b)'s re-key-on-promotion duty does not
  attach. Verified: `complete` = **{NEISO, PJM}**, both re-keyed to their live
  keepers, and `audit_keepers.py` PASS 0/0.

**The successor lane's audit is the more interesting artifact for this board.**
nyiso-160 ran a zero-delta replay of the *new* keeper at HEAD and audited it
from committed bytes: **max abs divergence 0.0 on every hourly-sidecar value
column, all three years**; C3a reproduces to 0.00 pp; the two differing
recorded keys are post-recording rule-24 schema growth at registered default
`False`, proven inert. **Verdict: NO G1-class drift.** That is the strongest
keeper-reproducibility evidence on this board, and it bears directly on the
re-capture question (F-8, checklist item 4).

### F-8 · 🔵 THE CALIBRATION SWEEP — SIX LANES, THIRTY PRs, AND A LOT OF KILLS (recorded, not adjudicated)

Recorded because it is the board's context, **not** adjudicated — none of it is
this program's to rule on:

- **ERCOT** — **ercot-242** room-axis extension of the RT/SCED wall registered
  (`2026-08-30-run242-room-axis` sidecar present). **ercot-243** killed at
  census (population is h3068-2024 alone; K-1 and K-3 fire, lane stops).
  **ercot-244** rtolhsl ceiling **KILLED AT CENSUS**. **ercot-245** per-class
  commitment-state Phase-0 precommit + probe + Amendment 1.
- **NYISO** — the **158 → 159 → 160 → 161** arc, ending in the 159 promotion
  (F-7). **⚡ Past the dispatch:** the dispatch listed the **nyiso-leg2**
  winter-locational candidate as *awaiting owner promote-or-archive*; at this
  pin that lane's branch is **deleted** and **nyiso-160 recorded a Leg-2 STOP
  WITH CAUSE at access** (the MyNYISO AORR artifacts never landed; the owner,
  asked in-session, answered *"Cannot produce them"* — the nyiso-97
  stop-if-walled class, no substitute mechanism invented). The winter face of
  C3a-2025 is now **identification-blocked on both legs**; determination
  consequence **none**; **no matrix cell verdict moves**. **nyiso-161** then
  filed an **owner-ordered winter-face waiver decision card**. Recorded as a
  second, labelled state — see the Owner queue.
- **MISO** — **⚡ Past the dispatch:** miso-190's registration watch **CLOSES**
  (sidecars `2026-08-30-miso-190-control` and `-ppexit` both present, #4370 —
  a third-cycle watch item ends), and **miso-191 has LANDED** (#4379 + #4384,
  binning-aware exit-cohort delivery), not "in flight" as the dispatch had it.
- **CAISO** — caiso-224 merged (#4390/#4395/#4415 + the #4401 parity fix), and
  **caiso-225's watch sweep came back ALL NULL** (#4425, zero solves): W-1,
  W-2, W-3 and the F2 derate all still blocked, A3's SoCalGas OFO record
  confirmed **available + feasible but unfunded**, nothing fires, no intake
  charter opens, **keeper/matrix/markers untouched**. **Terminal rest
  re-affirmed** — new evidence for owner-queue item 7.
- **Crossover** — the **CO2 grain repair** landed (#4388 + the capx D5/D5-R
  pair), which is why the forecast board's co2 magnitudes are restated (F-9).

### F-9 · 🟢 THE FORECAST BOARD'S GATE LEGS ARE SCORED FOR THE FIRST TIME — AND NEISO IS THE FIRST THREE-LEG ISO

v15 recorded gate legs **(b) and (c) UNSCORED**. At this pin the committed seed
`frontend/data/forecast/program-status.json` — **restructured this window; its
schema was re-read, not assumed** (it now carries `gate_reading`, `readiness`,
`gate_a_provenance` and six per-lane record blocks) — scores **all four legs
for all six ISOs**. Re-derived leg-by-leg from `isos.<ISO>.gate`:

| ISO | (a) | (b) | (c) | (d) | legs held |
|---|---|---|---|---|---|
| NEISO | pass | pass | pass | none | **THREE — the first in program history** |
| NYISO | fail | pass | pass | none | two |
| PJM | **pass** | fail | pass | none | two |
| ERCOT | fail | fail | pass | none | one |
| MISO | fail | fail | pass | none | one |
| CAISO | fail | fail | fail | none | none |

**`open` is `false` for all six and leg (d) is `none` everywhere — no ISO's
full-solve authorization gate opens, and none opened from this refresh.** Legs
(b)/(c) moved on the owner's **Q7 ruling about what leg (c) MEASURES** (FC-4
measured and reported, never in-band) plus NEISO's first T1-X, **not** on any
improvement in the model — and every FC-4 that passes leg (c) is itself a
**FAIL quoted at full magnitude**.

**Gate (a), this board's own column, re-derived field-by-field against the live
keepers and the live `complete` block:** passers = **{PJM, NEISO}** = the
`complete` set, unchanged in membership from v15.

**🔴 Seed staleness went the wrong way: three stale stamps → FOUR.** ERCOT
(names `231-tie-zone-measured` vs live `234-eastex-identity`), CAISO (`200-h1-
memberpanel` vs `220-c1-crosswalk`), MISO (`177-rho-measured` vs
`188-rvsscope`) — and **NYISO is newly stale** (`157-par-attribution` vs
`159-loss-surface`), re-staled by its own promotion two hours after the Q5-W
lane had re-stamped it current. PJM and NEISO are current. **The v15 pattern
held and then broke in the same window**: the lane that moves a marker
re-stamps the board it drives — but the lane that moves a *keeper* did not.

**🟠 And the seed carries two readings at once again.** Its top-level
`gate_reading` prose still says *"nobody holds three"* and names lane D14 as
the lane that **would** produce a first three-leg ISO, while a bracketed
in-line UPDATE and the per-ISO `gate` block both record that D14 landed and
NEISO holds three. That is the **same class of defect the D13 reconcile lane
was raised to repair**, re-appearing inside one window because the board's
prose and its data move at different cadences. **Recorded, not adjudicated** —
the forecast namespace is a different program's, and the per-ISO blocks are
the authority.

*No forecast run was solved or re-scored by this lane*; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it.

### F-10 · 🟠 THE DEVIATION WAS SUPERSEDED FOR ONE SITTING, AND A DISPATCH-VS-LAUNCH NEAR-MISS WAS CAUGHT

**On the record as a protocol fact, not a complaint.** The 2026-08-30
decision-card sitting's records duties were executed **in-session by the
director desk** under an **explicit one-sitting owner supersession** of the
standing deviation (owner, verbatim in the plan's §8: *"give me decision
cards … make real progress"*, with the deviation change recorded as
owner-directed). **That supersession is spent.** The standing deviation —
*the director issues prompts and pushes nothing* — **is back in force**, and
this lane is its dispatched records instrument.

**And a near-miss was caught rather than suffered:** the prior director session
**archived before issuing this dispatch**, which the **2026-08-31 director
startup** noticed and repaired by dispatching this lane. Recorded as a
**dispatch-vs-launch near-miss caught by startup**, explicitly **not** as a
failure streak — the check that v14 added as step 0 (*look for the BRANCH, not
a plausible-sounding commit*) is the same check that catches this class, and
it worked from the other direction this time: not "was a dispatched lane
launched?" but "was a completed sitting's dispatch issued at all?"

## What moved — v15 CYCLE (v15 record, RETAINED as history) (`def338e..69ae4dc7`, "the ruling-execution cycle")

**Read E-1…E-4 as one act.** They are the 2026-08-30 PM sitting's four rulings,
all executed inside a single 103-minute window, three of them by the same
records lane and one by the calibration lane it chartered.

### E-1 · 🟢 R-1 EXECUTED — THE NYISO FRONTIER CITATION IS ANNOTATED, RETIRING THE BOARD'S TOP QUEUE ITEM

v14's owner-queue item 1 (and v13's item 7 before it) was the `frontier` block
in `keepers/NYISO.json` citing **superseded nyiso-152** while the designated
keeper had moved 152 → 155 → 157. **Ruled R-1 and executed** (#4342,
`4c63b05`): the block now carries `currency_annotation_2026-08-30`, which
states in terms that the inline *"KEEPER: 2026-08-22-nyiso-152-duty-complete,
determination CALIBRATED"* describes **the keeper AT DECLARATION, not the
current keeper**, names both subsequent moves, and records the current
determination as **NOT-YET**.

**The shape of the fix is the point.** It is an **annotation, not a rewrite**:
no declaration text above it is altered, `keeper_at_declaration` stays, and the
ratification itself is explicitly unchanged. That is the correct disposition
for a dated owner act — the record of what was ratified stays true, and the
currency question is answered beside it rather than by editing history. **One
field, zero solves, zero determination change.**

**The class it belongs to is NOT retired.** Evidence PROSE is still gate-checked
nowhere: `check_mechanism_matrix.py` validates `keeper:` stamps and §5.x prose
headers and passes while citation text beside them goes stale. This instance is
closed by hand; the next one will also have to be. **Whether any gate should
read evidence text remains unruled** — it stays on Watch and is now the queue's
standing structural question rather than a live defect.

### E-2 · 🔵 R-2 EXECUTED — ercot-240 CHARTERED AND COMPLETED THE SAME DAY: THE "DEMAND GAP" IS THE DC-TIE NET IMPORT IDENTITY

Chartered at the sitting, precommitted (#4341, `0a7ed18`), measured and closed
within hours (#4344 probe + JSON, #4345 FINDING, #4348 calibration-log entry).
**ZERO-SOLVE** — every number read from committed artifacts and raw measured
inputs (the `ercot236_k33_clip` keeper sidecar, the EIA-930 wide extract, the
ERCOT MIS native-load record NP3-565-CD, the committed actuals parquet, the
committed ercot-239 JSON), with the model demand series recomputed through the
engine's own loader and gated against the sidecar.

**The adjudication:** the event-hour "demand gap" is the **DC-TIE NET IMPORT
IDENTITY, exactly and everywhere.** The model's demand input is **NOT**
understating real demand — it serves the measured net-generation boundary,
correctly. All three chartered demand-source candidates (4CP/load response,
the 930-vs-MIS boundary, weather-hour alignment) are **REFUTED as gap
carriers** under the precommitted rules, and the phase-0 §0.5/§4 framing is
re-adjudicated.

**Why this is a good outcome and not a null.** A "demand gap" that had been
read as a *model input defect* turns out to be an **accounting identity** —
the boundary the model is built to serve. That closes a candidate root cause
for the ERCOT 2023 C3a residual by showing it was never a cause at all, at the
cost of one zero-solve day. Rule 1 `[R-STRUCT]` reading: the mechanism was
already right; the framing was wrong.

### E-3 · 🟢 R-3 EXECUTED — caiso-222 Q1 IS **TERMINAL REST + MAP**

Recorded #4342 (`634927a`, the CAISO calibration log + the packet §9). Q1 is
ruled **§1(c) option 3 — TERMINAL REST + MAP**: the CAISO C3a residual
(**+12.5 % 2024 / +15.5 % 2025**, re-derived at the pin below) is designated
**ATTRIBUTED AND CLOSED at this representation grain**, with a decision map
attached rather than an open investigation.

This is the disposition v14's queue item 7 was waiting on. **It does not make
CAISO CALIBRATED** — the determination stays `NOT-YET` and the C3a fails stay
published at full magnitude — it rules that *further pursuit at this grain is
not the route*. Owner ruling 5 (*C3a must genuinely pass; NOT-YET is the honest
fallback*) is untouched and still governs.

### E-4 · 🔵 R-4 EXECUTED — Q2 ROUTES (i)+(iii) ARMED/CHARTERED, (ii) CEII **DECLINED**; ROUTE (iii) RAN AS caiso-223 THE SAME DAY

**The ruling** (#4342): route **(i) ARMED** — W-1/W-2/W-3 become **standing
watch items**, each arming only with its own precommit, and the armed watch
tests are the **ONLY sanctioned re-checks** of the Q1 terminal rest. Route
**(iii) CHARTERED** as the sub-zonal topology program's opening round. Route
**(ii) DECLINED** — CEII access (FERC 18 C.F.R. §388.113, the A-1/A-2/A-3
filing/agreement class); the option stays on the record for any future owner
act.

**The execution** — caiso-223, #4347 (precommit, criteria/tiers/gates fixed
*ex ante*) then #4350 (artifacts + FINDING + log). **ZERO-SOLVE; nothing
armed; keeper `2026-08-26-caiso-220-c1-crosswalk` UNCHANGED.** What it
delivered:

- **Partition PROPOSED AND ADJUDICATED (P-A′)** — one new San-Joaquin-Valley
  pocket zone **FSNO** between two element-grounded cuts, replacing the single
  Path-15 link that the **DMM record says does NOT bind**, while the two cuts
  that **DO** bind are invisible at hub grain. That is a rule 14
  `[R-ACCURATE]` argument made against a measured record, not a residual.
- **Membership DERIVED** — 42 crosswalk plants / **2,701 MW** into FSNO, pnode
  map committed, **zero silent defaults**.
- **Load split MEASURED** — the caiso-172 ATL_LDF method, 3-way: **FSNO
  0.1326 / ZP26 0.1148 / NP15 0.7526** of DLAP_PGAE. **Gates 13/13 PASS**, and
  the two-way control reproduces the committed caiso-172 artifact **EXACTLY**.
- The round **ends on a sufficiency gap list** rather than an arm.

**Declared a REPRESENTATION-GRAIN PROGRAM, NOT A LEVER.** That is the
distinction rule 1 `[R-STRUCT]` turns on, and it is why the round is legible:
it changes what the model can *see*, and it is required to earn its arming
separately. Its successor **caiso-224** is the cycle's live lane (#4357
precommit merged; #4360 open — the gated `caiso_fsno_subzonal_topology`,
**default off**, plus a G-CTRL bit-zero comparator probe).

### E-5 · 🟢 THE ALIGNMENT BREAK v14 REPORTED IS REPAIRED — BY MARKER WITHDRAWAL, NOT BY A CALIBRATION WIN

**Re-derived at the pin from `calibration-complete.json`, the six keeper
shards, and the forecast seed — not carried.**

The capx **Q5-W** lane (#4343) withdrew **NYISO's `complete` marker** to the
`withdrawn` block, on the Q5 uniform rule — *a `complete` marker cannot stand
on a NOT-YET keeper* — applying the 2026-08-06 CAISO precedent evenly. **This
is a DIFFERENT program's act on the shared marker file**, taken under its own
charter; it is recorded here because this board's instruments read that file.

| instrument | v14 (`0a5e896`) | v15 (`69ae4dc7`) |
|---|---|---|
| CALIBRATED | {PJM, NEISO} | **{PJM, NEISO}** |
| `complete` block | {NEISO, NYISO, PJM} | **{NEISO, PJM}** |
| forecast gate (a) passers | {PJM, NYISO, NEISO} | **{PJM, NEISO}** |
| `frontier` | {PJM, NYISO, NEISO} | **{PJM, NYISO, NEISO}** ⬅ **unmoved** |

**Three instruments now agree; `frontier` is the lone outlier.** Two honest
readings, both of which belong on the record:

1. **The break did not close by NYISO improving.** NYISO's keeper, its
   `NOT-YET` determination and its 8/5/3/0 scorecard are all byte-unchanged.
   The instruments agree because one of them was *withdrawn*.
2. **The misalignment moved rather than vanished.** `frontier` still contains
   an ISO that is neither CALIBRATED nor `complete`. Unlike v14's break, this
   one is **not** a governance hazard — a ratified frontier is a dated
   statement about lever-queue exhaustion, not a holdout authorization, and
   nothing is spendable on it. But it *is* the fourth instrument disagreeing
   with the other three, and **nothing in the repo checks that.**

**`final` remains EMPTY (`_note` only). No ISO has ever spent a locked-test
year** — re-verified below, not restated.

### E-6 · 🔵 FOUR CALIBRATION ROUNDS OPENED, ONE A/B CLOSED REJECTED — AND NOT ONE OF THEM MOVED A KEEPER

The cycle's calibration content, all of it zero-solve or kill-gated, none of it
promoting:

| lane | PRs | what landed |
|---|---|---|
| **ercot-239 r2 → r3** | #4351, **#4356**, #4359 | precommit round 2 (graded measured `peak_ladder` under the calibrated top, August steepness) → Stage-A census + **Amendment 1** (G-A(iv) proxy re-based to the measured invariant) → Stage-B A/B driver → **REGISTERED AND REJECTED** (`2026-08-30-239-graded-ladder`, ERCOT, **2023 only**): kills clean, officials collapse to pre-k33, spur **74 → 11**; escalated, **keeper untouched**. Then r3 precommit — h3068-2024 bounded diagnosis |
| **ercot-241** | #4349, **#4358** | Phase-0 precommit for the off-core conduct-parameterization screen → **phase-0 MEASURED**: kills clear, **Phase-1 gate OPEN**, dependence is position/participation-carried |
| **nyiso-158** | #4339 | phase-0 winter-face diagnosis: the binding-depth differential **is the measured Transco TTC step**; **no measured driver reaches the sharpened iroquois re-open bar** (first leg closed, Leg-2-only); **C3b-2025 is wholly the two faces** (98.4 % of squared error; either face alone restores the band); the CE-util overshoot is **not** an envelope defect |
| **nyiso-159** | #4352 | phase-0: the NYISO loss component measured on the completed 36-month record, **+ PREREG** of the zonal loss surface |
| **caiso-223 → caiso-224** | #4347, #4350, #4357, **#4360 (open)** | E-4 above; successor gated **default off** |

**The pattern is worth naming: this cycle bought five sharpened addresses and
one clean rejection for zero keeper risk.** v14's durable lesson — *a negative
result with a bitwise proof beats a positive one without* — is not merely
carried this cycle, it is **the whole cycle**. The ercot-239 graded ladder was
rejected **on its own pre-registered gates**, exactly as v14's nyiso-157
iroquois companion was; the model of "arm, measure, kill, escalate, keeper
untouched" now has four consecutive instances across three ISOs.

**miso-190's registration watch stays OPEN** — verified at the pin, not
assumed: no `miso-19*` sidecar exists in `frontend/data/backcast/registry/`
(newest MISO sidecars are `188-control` / `188-rvsscope`), and the branch
`claude/miso-190-backcast-calibration-okt1cn` sits **139 commits behind main
with nothing unmerged**. Third consecutive cycle open.

### E-7 · 🔴 NEW — THE ERCOT STAGE-0 GOLDEN'S PROVENANCE RUN WAS PRUNED OUT FROM UNDER IT

Discovered by re-deriving the Stage-0 table rather than reading v14's, and it
is the cycle's one genuinely adverse finding.

`results/regression-goldens/perfb-stage0/manifest.json` maps the ERCOT golden
to `keeper_id: 2026-08-15-ercot204-rule26-delete`. **That run's registry
sidecar was DELETED this window** — commit `e51a8a7d` (#4356), under **top-15
retention**, in the same commit that registered the 239 graded ladder. Its
bundle directory `results/calibration/ercot204_rule26_delete` went with it.

**The prune itself is legitimate and correctly executed** — top-15-per-ISO
retention is rule 15 `[R-DASHBOARD]` policy, the run was long superseded, and
parity exits 0 at the pin. **The collision is with WS3, which nothing checks.**
Stated precisely, and verified at the pin:

- At the pin, **none of the five golden `keeper_id`s resolves to a registered
  sidecar.** ERCOT's is the one that demonstrably **left this window** (its
  deletion commit exists and is named above); for the other four, no commit
  ever touched a registry path under those exact ids, so they were never
  registered under their manifest names — a **different** condition, recorded
  as such rather than merged into one alarming sentence.
- The manifest is **byte-unmoved**: `git diff` over
  `results/regression-goldens/` returns **empty** across all 66 commits.
- **The per-file `content_hashes` are unaffected and remain the verification
  instrument** — every manifest entry carries them, and they do not depend on
  the registry.

**So nothing is lost that was not already gitignored, and no gate went red.**
What changed is the *provenance chain*: the ERCOT golden now names a run with
**no committed registry record at all**, on top of a manifest `git_sha`
(`af1ccb6`) that **still does not resolve** (re-checked at the pin). Whoever
un-parks WS3 now has two broken provenance links on the ERCOT row, not one.
**Recommended, and cheap: capture PJM first anyway (it has no golden and the
only clean scorecard), and treat every re-capture as re-establishing
provenance rather than refreshing it.**


## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `07472e7c`)

**RE-DERIVED AT THE v20 PIN.** All six `keeper` fields were byte-compared
`f45766e4` → `07472e7c`: **five unmoved, MISO moved.** All six determinations,
grade summaries and all eighteen C3a(RT) magnitudes were **re-parsed live from
the status shards**, not carried from v19b. Rubric **v3.5** on every shard.
**Keeper motion this window: ONE — MISO `2026-08-30-miso-191-bexit` →
`2026-09-01-miso-198-oomlevel`** (#4552), **recorded, not adjudicated** (J-8);
CAISO's `220 → 231` is the v19 cycle's and is not re-adjudicated.

⬅ 🅿️ **AND A NEW COLUMN OF STATE THIS TABLE MUST NOW CARRY: R-V FREEZES THREE OF
THESE SIX LANES.** **{ERCOT, NEISO, PJM} are FROZEN** — no promotion until
PERF-B's byte-green loop completes or the owner lifts it. **{MISO, CAISO, NYISO}
are EXPLICITLY UNFROZEN** and keep promoting. The frozen set is exactly the
`complete` / CALIBRATED / frontier / gate-(a)-passing set, and exactly the three
whose stage-0 rows are CURRENT (J-4).

Determinations and grade summaries parsed live from the status shards at the
pin. **C3a(RT) is the load-weighted mean-LMP error against RT actuals, per year
2023 / 2024 / 2025** — printed for every ISO because it is the criterion every
NOT-YET fail set contains, and printing it only for the failures hides how
narrow the margins are. ERCOT's row is the board's TWO-CONFIG entry (v14 D-2):
the grade column shows forward-span / carve-out / registered-3-year reads.

**Five of six `keeper` fields are byte-unchanged from v19b and that is a
re-derivation, not a carry** — all six compared byte-for-byte at the pin, all six
determinations and grade summaries re-parsed from the status shards, all eighteen
C3a(RT) magnitudes re-read. **The sixth, MISO, moved (`191-bexit` →
`198-oomlevel`)** and its whole row is re-derived (J-8).

| ISO | Designated keeper | 🅿️ R-V | Determination | Grade (scored/target/fails/ledgered) | C3a(RT) 2023 / 2024 / 2025 |
|-----|-------------------|---|---------------|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` (FORWARD, 2024–2025) **+ `2026-08-25-236-swcap-clip-k33`** (2023 carve-out) — TWO-CONFIG | ⬅ **FROZEN** | **ISO-level `CALIBRATED`** (ercot-246 partition rollup) · forward `CALIBRATED` on span · carve-out `CALIBRATED` · **registered 3-yr `NOT-YET`, published untouched** | 8 / 5 / **2** / 1 (the registered 3-yr read) | **−39.7 % F** (the carve-out's year) / −0.2 % / −7.9 % |
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` | unfrozen | `NOT-YET` | 8 / 6 / **1** / 1 | +4.1 % / **+12.5 % F** / **+15.6 % F** |
| PJM | `2026-08-15-pjm-162-inputclock` | ⬅ **FROZEN** | **`CALIBRATED`** | 8 / **8** / 0 / **0** | +6.2 % / −0.8 % / −7.7 % |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | unfrozen | `NOT-YET` | 8 / 6 / **2** / 0 | +2.3 % / −1.2 % / **−11.5 % F** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | ⬅ **FROZEN** | **`CALIBRATED`** | 8 / 7 / 0 / 1 | +3.1 % / +5.7 % / +1.7 % |
| MISO | ⬅ **`2026-09-01-miso-198-oomlevel`** (was `191-bexit`) | unfrozen | `NOT-YET` | 8 / 6 / **1** / 1 | +0.1 % / ⬅ **−4.5 %** / **−12.3 % F** |

| ISO | v20 cycle (`f45766e4..07472e7c`) |
|-----|--------------------------------|
| **ERCOT** | **Keeper unmoved and untouched — no ERCOT lane merged in this 29-PR window at all.** ⬅ 🅿️ **FROZEN by R-V.** Its stage-0 forward row stays CURRENT; its **2023 carve-out is still UNCOVERED and still unrepresentable**, and R-O's schema lane is now unlaunched across **three** pins (J-9, J-11). The `ercot_wtx_*` two-channel config hazard is carried unchanged — see Watch |
| **CAISO** | **Keeper unmoved** (`231-b1-ungrounded`, promoted last cycle). **Explicitly UNFROZEN by R-V.** Four lanes merged, all diagnostic and none promoting: import-depth wide-sample (#4560), import-total envelope (#4553), import-capacity derivation (#4542), backcast calibration (#4539). Its **import-depth DOF is closed as not identifiable** on a 2019–2025 regime break (caiso-235) — the calibration desk's finding, recorded here for visibility only. **Stage-0 row still STALE** |
| **PJM** | **UNMOVED and untouched for an ELEVENTH consecutive cycle** — not one PJM PR in the window. Still the only **8/8 zero-caveat** scorecard on the board. ⬅ 🅿️ **FROZEN by R-V**, which for PJM changes nothing observable: its keeper has been still longer than any other, which is exactly why its golden is CURRENT |
| **NYISO** | **No keeper motion; four diagnostic lanes** (nyiso-171 CC/CHP floor, nyiso-172 ST_GAS deficit, nyiso-173 CC availability ×2). Determination unchanged: `NOT-YET` {C3a-2025 −11.5 %, C3c}. **Explicitly UNFROZEN.** Its `frontier` remains **WITHDRAWN** (2026-08-30) and its marker remains in `withdrawn` — both handled fail-closed in the alignment derivation (J-7). **Stage-0 row still STALE** |
| **NEISO** | **UNMOVED and untouched** — no NEISO lane merged this window. ⬅ 🅿️ **FROZEN by R-V.** Its backcast residual is still the **`final` grant itself**, DATA-BLOCKED on the 2025 EIA-923 FINAL vintage (EIA stating September 2026 — *the director's report, not this lane's measurement*). On the *forecast* board it is still the only ISO with an **OPEN** gate, leg (d) **granted** |
| **MISO** | ⬅ **THE CYCLE'S ONLY PROMOTION: `191-bexit` → `198-oomlevel`** (#4552), the out-of-merit level re-conditioning — **the busiest column again at NINE PRs across three lanes** (ST_GAS/steam CHP calibration, must-run window basis, steam bid-side). Determination and grade **unchanged** (`NOT-YET`, 8/6/1/1); C3a 2024 −4.6 → **−4.5 %**, 2025 **−12.3 %** unmoved — **kept despite a residual that did not improve, which is rule 1 `[R-STRUCT]` working**, the same reading CAISO's promotion got at v19. **Explicitly UNFROZEN.** Two consequences this board owns: it **deepened MISO's stage-0 gap to three promotions past capture** (joint-deepest), and it **opened the nine-PR gate-(a) staleness window that R-T now closes at the source** (J-2, J-8) |

| ISO | v19 cycle (`d44446e0..72576ebe`) |
|-----|--------------------------------|
| **ERCOT** | **Keeper unmoved — and its stage-0 row went CURRENT for the first time** (R-L, G-3): the forward config's golden is captured at HEAD with the fidelity oracle at **271 flags identical, 0 config drift**. **Its 2023 carve-out config still has no golden and cannot get one** until R-O's schema lane runs (G-6) — so "ERCOT CURRENT" means *forward only*, and full coverage is still two captures. One data-intake lane landed (ercot-248, SCED all-resource). A latent config hazard surfaced in its recorded keeper config — see Watch |
| **CAISO** | **THE CYCLE'S ONLY PROMOTION: 220 → 231** — the un-grounded-class offer re-grounding, three ERCOT-lineage bands removed from CAISO's binding path (G-10). Determination and grade **unchanged** (NOT-YET, 8/6/1/1); C3a 2023 +4.0 → **+4.1 %**, 2025 +15.5 → **+15.6 %** — kept despite a residual that did not improve, which is rule 1 `[R-STRUCT]` working. Also caiso-229 (C3a belly) and caiso-230 (above-floor decomposition). **Its stage-0 gap deepened by this promotion** |
| **PJM** | **UNMOVED and untouched for a TENTH consecutive cycle.** Still the only 8/8 zero-caveat scorecard. Its stage-0 row is CURRENT for a third cycle and is now one of **three**, not one |
| **NYISO** | **No keeper motion; five diagnostic lanes** (nyiso-165/166 AS-reference repair, nyiso-167 C3a-2025 attribution, nyiso-168 supply-curve slope, nyiso-169 congestion-gradient — the last **stopping** rather than arming, its zonal-gradient half found not carried by any binding constraint). Determination unchanged: NOT-YET {C3a-2025 −11.5 %, C3c}. **The nyiso-161 card stays RULED and RETIRED** (R-H, v18b) |
| **NEISO** | **UNMOVED on the backcast, and its stage-0 row went CURRENT** (R-L, G-3) — fidelity oracle **259 flags identical, 0 drift**; the golden is correctly **P1-only**, matching neiso-99's move off the archived P2 pass (audit row O5). Its backcast residual remains the **`final` grant itself**, still DATA-BLOCKED on the 2025 EIA-923 FINAL vintage. On the *forecast* board — a different program's — it is still the only ISO with an OPEN gate |
| **MISO** | **No keeper motion, and the busiest calibration column on the board: ELEVEN PRs across five lanes** (miso-195/196 outage-envelope, miso-197/198 CC_REGULAR + ST_GAS conduct, the xiso cascade repair). **Its stage-0 gap is now the joint-deepest** at two promotions past capture — and **restart-checklist item 5 still names MISO next**, unchanged by R-L |

**Markers at `07472e7c`, re-read live this cycle:** `complete` = **{ERCOT,
NEISO, PJM}** · **`final` = EMPTY** (the block holds a `_note` and no ISO) ·
**`holdout-freeze.json` `active: true`, TIER-SCOPED to `locked_test` alone** ·
`withdrawn` = **{NYISO, CAISO}**. **UNCHANGED FROM v19b, and that is a
measurement, not a carry**: `calibration-complete.json` and `holdout-freeze.json`
each show **0 commits** in the 81-commit window. All three `complete` entries
remain re-keyed to their live keepers (rule 22 D-5(b)); **the one ISO that
promoted this cycle (MISO) holds no `complete` marker and so owed no re-key** —
verified, not assumed. **`audit_keepers.py` returns PASS: 0 failures, 0
warnings** at the pin, re-run here.

⚠️ **AND A DISTINCTION R-V's FREEZE MAKES NEWLY IMPORTANT: THE KEEPER FREEZE AND
THE HOLDOUT FREEZE ARE DIFFERENT INSTRUMENTS AND MUST NEVER BE CONFLATED.**
R-V's is a **promotion** freeze on {ERCOT, NEISO, PJM}, declared to keep three
goldens still; `holdout-freeze.json` is a **spend** freeze on the **locked-test
tier** for **all six** ISOs. They share a word and nothing else — different
scope, different subject, different lifting authority. **R-V neither touches nor
relaxes the holdout freeze**, and this lane edited neither file.

**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — re-verified at the pin by walking
every registry sidecar, not restated. Across all **60** registered sidecars the
solve-year histogram is **{2022: 2, 2023: 58, 2024: 54, 2025: 54}** (per-ISO
sidecar counts: ERCOT 15, MISO 15, NYISO 15, **CAISO 6**, PJM 5, NEISO 4). The
scan for any year in {≤2018, 2019, 2026} returns **NONE**. The only
out-of-training registrations remain the **two authorized 2022 validation
touchpoints** (`2026-08-05-pjm-2022-touchpoint`,
`2026-08-06-neiso-2022-corrected-basis`). NEISO's one-shot stays **NEVER GRANTED,
not spent** (D-23). *Motion note: the sidecar total is **UNCHANGED at 60**
despite MISO registering two new runs (`198-control`, `198-oomlevel`) — MISO
sits at its rule-15 cap of 15, so `prune_iso` retired two in the same commit.
**The retention rule observed working, not assumed.** The year histogram is
therefore unmoved as well.* **And 0 of the 60 is a golden capture** — the
measurement behind the stage-0 table's standing reading. This line is re-verified
and republished every cycle because WS5 Job 1 found the public site asserting its
exact opposite for two weeks.

**Determinations: ERCOT (ISO-level), PJM, NEISO `CALIBRATED` · CAISO, NYISO,
MISO `NOT-YET` — with ERCOT's registered 3-year read still NOT-YET and still
published.** **C3a appears in every NOT-YET fail set, and for CAISO and MISO it
is the ONLY failing criterion**; NYISO adds only C3c. **The alignment position
HOLDS this cycle** — see J-7.

## Workstream rollup

**🔴 NOT ONE WORKSTREAM SURFACE MOVED THIS WINDOW** — measured, not assumed, over
the full `f45766e4..07472e7c` window (**81 commits, 29 merged PRs**) with
`git log -- <path>`: **`results/regression-goldens/` 0 commits**,
**`.github/workflows/` 0 commits**, **`docs/audit/` 0 commits**. All 29 PRs are
calibration-desk, capx-desk or records lanes (see the v20 snapshot's lane table).

⚠️ **SO WS3's ROW CHANGES ITS LABEL AND NOT ITS NUMBER, AND THE DISTINCTION IS
THE WHOLE POINT.** R-V **resumes** PERF-B, so the row reads
**RESUMED-IN-PROGRESS** instead of **PAUSED**. Its completion figure is **held at
~82 %** — the figure v19 measured off R-L's two captures — because **nothing has
been captured, certified or merged since**. **A resumed workstream that produces
no commit is a paused one wearing a different label**, and the next cycle's
honest test is whether `results/regression-goldens/` moves (J-9). Every other
row's completion figure is carried **by measurement of an untouched surface**,
not by estimate, and every blocker below is re-stated rather than re-assumed.

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8, O5, O4 CLOSED/RESOLVED**; **O6** is standing policy; **O7 CLOSED** (#4377) — the Door-2 attribution harness built *and* exercised, HP-1 hash-proven bit-identical, keeper untouched | **In progress ~95 %** (unchanged — `docs/audit/` byte-untouched this window) | **AUDIT-B still gated at G3 — waiting by design, and that gate is what caps this row**, not any remaining A-half work. No audit row carries an owner action this board tracks |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, landing-verify green on merged main | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. ⬅ 🟢 **PERF-B RESUMED BY OWNER (R-V)** — was *PAUSED*. Stage-0: **6 of 6 ISOs captured, 3 of 6 CURRENT**. Changes (c)/(d)/(e) merged, (a)/(b) unstarted | ⬅ **RESUMED-IN-PROGRESS ~82 %** — **the label moved, the number did NOT.** Held at v19's measured figure because **no PERF-B surface moved this window** (`results/regression-goldens/` 0 commits across 81); re-estimating upward on a ruling alone would be exactly the estimate-drift this column exists to avoid | ⬅ **NO LONGER BLOCKED BY THE TWO PARKS — BLOCKED BY EXECUTION.** R-V lifts both the WS3 pause and the golden-tier park, so **G2 leg 1's dependencies are now defects, not permissions**: 🔴 **the golden tier is un-parked but UNEXERCISED** (no `workflow_dispatch` at this pin) **and its last three scheduled runs are RED on content** (J-6), so nothing can be certified byte-green yet; 🔴 **the PERF-B lane itself shows no branch and no PR** (J-11). 🟠 **What else remains**: three rows STALE (CAISO/MISO/NYISO, each with a **pruned** provenance run — survivable by design via `keeper_snapshot`), and **ERCOT's carve-out config is still unrepresentable** until R-O's schema lane runs |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | ⬅ **DOCS-B is now QUEUEABLE behind PERF-B (R-V), but still not startable** — it commissions at G2, and **G2 is not declared** (legs 2 and 4 blocked on R-U). Waiting by design, with a nearer horizon than at v19b |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES** (#4120/#4121, #4187/#4191). Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Deferral list unchanged |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED**; **BLOAT-3 ADJUDICATED and EXECUTED** (BLOAT-S2, −444.5 MiB at tip). ⬅ 🟢 **B-8, the class-level parity carve-out, EXISTS** | **Completed (charter) · gate 🟢 GREEN** | **🟢 GREEN at the pin** — `check_registry_payload_parity.py` **exit 0** (60 runs checked, 95 bundle dirs swept, 0 known-unsynced tolerated). ⬅ **The allowlist is no longer the mechanism**: a two-conjunct structural classifier admits pre-registered campaign points and replay recipe dirs, and the residual enumeration stands at **8** entries, down from **40** (G-1). Checklist item 10 is **discharged** |
| — `BENCH FRESHNESS` | `check_bench_freshness.py` / audit S1 lineage | **🟢 exit 0 at this pin — 0 STALE of 20 parts, 20 of 20 with engine drift at 6 engine commits** | ⬅ 🟢 **THE INSTRUMENT IS REPAIRED** (G-1). The **date-kind mismatch** this board diagnosed across three versions — part date read with `%ad` (author), engine commits filtered with `--since` (committer) — is fixed at source: **both sides now use the committer instant in offset-bearing form**, and `--since`'s inclusivity is verified rather than assumed. The day-granularity artefact goes with it. **So "20 of 20 with drift" is now a TRUE reading of a repaired instrument, not the artefact it was** — and it is the honest one: 6 engine commits under `src/market_sim/{data,config}/` have landed since the parts were committed. **0 STALE is still the reading that matters, and it holds.** Not gated either way; regenerate before trusting a *marginal* C1 verdict |
| — `GOLDEN-TIER-FIX` | #4014 built it; #4071 fixed the first cron RED, verified by a full local four-step replay | ⬅ 🔴 **Fix completed · tier UN-PARKED · tier RED** | ⬅ 🔴 **THE PARK IS LIFTED (R-V) AND THE ROW'S OLD TEXT WAS FALSE.** It read *"CI proof **deliberately unspent**"* for seven cycles. **The proof was being spent weekly on a `schedule` trigger and failing: runs #5 (08-17), #6 (08-24) and #7 (08-31) are ALL RED on `main`.** Run #7 provisioned `data/clean` and emissions **green** and then failed at **`Data-provisioned pytest tier (serial)`** — a **content** failure, **not** the OOM class #4071 fixed, so the local replay does not cover it. **The owner has run NO `workflow_dispatch` at this pin** (last was #4, 2026-08-15), so the un-park is **granted and unexercised**. Consequence is unchanged in effect but changed in kind: **none of the three CURRENT captures can be certified byte-green** — no longer for want of permission, but because **the tier does not pass** (J-6). Not this program's to fix; **routed, not adjudicated** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🟢 GREEN at this pin** | `check_mechanism_matrix.py` **exit 0**: integrity OK across the base file + **6 ISO shards**; anchors ⬅ **194 field + 49 row + 159 path** (v19b: 194/49/156 — **+3 path anchors, NO new `ScenarioConfig` field**, so rule 26 duty (c) is not engaged), **0 WARNs**, 0 unresolvable beyond the ratchet (3 skipped paths, 39 non-field tokens); keeper stamps AND §5.x prose headers match every `keepers/<ISO>.json`, **held across the MISO promotion**. ⬅ **On the dispatch's "243 anchor WARNs GONE": the count was 236, it lived only inside PR #4531's own branch, and `main` never held it** — breakage (`0931d7e6`) and repair (`f5b33644`, Opus 5, capx-director-refresh lane) merged together, and the WARNs were already 0 at v19b's pin (J-12) |
| — `GATE-(a) PROVENANCE` | 🆕 rule-22 / forecast-seed cross-check | **🟢 NEW GATE, exit 0** | ⬅ Added under R-J (#4495, `ci.yml:213`, **hard**). Holds each `program-status.json` `a_keeper_marker` row against the live backcast keeper + marker state; **reads no determination**. **Fired for real eight PRs after it was built** (the caiso-231 promotion, exit 1 → re-key → exit 0, G-5). It gates the exact defect class this board re-reported for three cycles with no instrument able to see it |
| — `GOLDEN MANIFEST` | the undercounted seventh gate (`ci.yml:118`) | **🟢 exit 0** | Not new — **enforced throughout, and simply not counted** by this board's five-gate roster (G-7). It is now the **owner of the stage-0 table**: 38 manifests / 70 entries (6 enforced, 64 legacy grandfathered by the ratchet), reporting **3 with a pruned provenance run, 3 stale vs the live keeper**. Its own note is the standing reading: *a pruned provenance run is NOT a failure — top-15 retention is correct policy; it is survivable only because each entry carries its own `keeper_snapshot`* |

## Stage-0 golden staleness (v20 record at `07472e7c` — ⚠️ **SUPERSEDED BY K-5, THEN BY L-5**)

> ⚠️ **SUPERSEDED AGAIN AT v22 (`dfc44d95`) — SEE L-5. STAGE-0 IS 7 OF 7
> CURRENT**, the first full-coverage state in program history: all six bare-ISO
> entries **plus** the `ERCOT__carveout-2023` partition, each against its live
> keeper, every provenance run registered, **0 stale and 0 pruned among the
> enforced**. Capture-A (#4601) closed the last stale row. ⚠️ **It does NOT
> claim byte-green certification** — that needs the golden tier exercised, and
> the tier is unexercised since run #4 **and red on its last three scheduled
> runs** (L-6). Retained below as the v20/v21 record.

> ⚠️ **SUPERSEDED AT v21 (`0653bf13`) — SEE K-5.** The table below reads
> **3 current / 3 stale**; at the v21 pin it is **6 CURRENT / 1 STALE**, with
> **MISO the sole stale entry** (its provenance run pruned; live keeper
> `2026-09-01-miso-198-oomlevel`). The *"`results/regression-goldens/` has ZERO
> commits"* sentence below is also **superseded** — four captures have landed
> since (Capture-B ×2, PERF-B ×2; K-9). Retained as the v20 record.


**RE-DERIVED AT THE v20 PIN AND BYTE-UNCHANGED IN COVERAGE: 3 current / 3
stale.** `check_golden_manifest.py` **exit 0** still reports CAISO, MISO and
NYISO stale — **but MISO's stale line now names a different live keeper**,
`2026-09-01-miso-198-oomlevel`, because MISO promoted (J-8). **The gate tracked
the promotion without being told**, which is the schema-v2 `keeper_id` mapping
doing its job.

**`results/regression-goldens/` has ZERO commits across the 81-commit window** —
so no capture was taken, and the coverage count is unmoved. **R-Q's two capture
lanes still show no branch and no PR** (J-11), and **R-S has re-issued both**,
with Capture-A's target updated to `miso-198-oomlevel` (J-1). **R-V's un-park
does not change this table** — it removes a permission, not a capture.

Re-derived at the pin from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json`, **and cross-checked
against `check_golden_manifest.py`'s own output (exit 0)** — which, since R-J,
is the instrument that owns this table rather than a hand recomputation this
board performs alongside it. Each captured bundle is mapped back to its keeper
through the manifest's own `keeper_id` field, not by name.

**🟠 THE TABLE DID NOT MOVE THIS CYCLE, AND ONE ROW DEEPENED.** Coverage holds at
**3 current / 3 stale** (v19's gain from 1 / 5 stands). **MISO deepened** —
promoted, so its gap is now **three** promotions past capture and it is the
board's deepest single row. **The three CURRENT rows are exactly R-V's three
FROZEN lanes**, which is the freeze doing what it was declared to do: the rows
that could go stale are the ones now held still.

⚠️ **AND R-V's UN-PARK DOES NOT MAKE THESE THREE CURRENT ROWS BYTE-GREEN.** The
tier that would certify them is un-parked but **RED on its last three scheduled
runs** (J-6). *(Historical, retained: the v19 reading was "the table moved the
right way for the first time" — that gain is intact, it simply did not repeat.)*

**🟢 AND THE MANIFEST IS A DIFFERENT ARTIFACT NOW — schema v1 → v2.** There is
**deliberately no shared top-level `git_sha`**; every entry carries its own
`provenance` (`git_sha`, `git_sha_full`, `basis_sha`, `git_dirty`, `recorded_at`,
`env`, `highspy_version`, `source`, `recovery`) **and** a `keeper_snapshot`
copied from its provenance run's sidecar. Two consequences, both verified rather
than assumed: **(1)** the v17 defect — one capture silently re-labelling every
earlier one — is now structurally impossible, and R-L's two captures are the
demonstration (each changed only its own entry, the other four byte-identical);
**(2)** a top-15 retention prune **costs nothing**, because the snapshot outlives
the sidecar. `basis_sha` adopts the repo's existing durable primitive
(`pipeline.persist.basis_sha`), since a capture's own `git_sha` is routinely a
session-local branch commit.

| ISO | 🅿️ R-V | Golden captured against | Provenance run in registry | Designated keeper at `07472e7c` | Verdict |
|-----|---|-------------------------|---|--------------------------------|---------|
| **PJM** | **FROZEN** | 🟢 `2026-08-15-pjm-162-inputclock` (v16 window, #4369) | ✅ **PRESENT** | `2026-08-15-pjm-162-inputclock` | 🟢 **CURRENT.** Held a fourth cycle; PJM's keeper has now been still for **eleven** |
| **ERCOT (forward)** | **FROZEN** | 🟢 `2026-08-25-234-eastex-identity` (v19 window, #4509) | ✅ **PRESENT** | `2026-08-25-234-eastex-identity` | 🟢 **CURRENT.** Fidelity oracle **PASS**: 271 meta flags identical, `scenario_config_drift == []` |
| **ERCOT (2023 carve-out)** | **FROZEN** | ❌ **NONE — and NOT CAPTURABLE at this schema** | — | `2026-08-25-236-swcap-clip-k33` | 🔴 **UNCOVERED.** `keepers` is keyed one entry per ISO, so a two-config ISO has nowhere to put a second golden. **R-O charters the schema lane; it has not launched at a THIRD consecutive pin** (J-11) |
| **NEISO** | **FROZEN** | 🟢 `2026-08-17-neiso-99-joint-p1` (v19 window, #4509) | ✅ **PRESENT** | `2026-08-17-neiso-99-joint-p1` | 🟢 **CURRENT.** Oracle **PASS**: 259 flags identical, 0 drift. Correctly **P1-only**, replacing the superseded `neiso-93-envelope` entry's P2 parquets |
| **CAISO** | unfrozen | `2026-08-16-caiso-197-w2-r5` (`basis_sha 9f6ff3ee`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | `2026-09-01-caiso-231-b1-ungrounded` | **🔴 STALE**, two promotions past capture. **Capture-B's first target; re-issued under R-S and unlaunched** |
| **MISO** | unfrozen | `2026-08-16-miso-160-wefor-shape` (`basis_sha af1ccb6c`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | ⬅ **`2026-09-01-miso-198-oomlevel`** (was `191-bexit`) | ⬅ **🔴 STALE, and it DEEPENED this window** — the cycle's one promotion (J-8). **THREE promotions past capture: the deepest single row on the board.** Capture-A's target, **updated to this id by R-S** and unlaunched |
| **NYISO** | unfrozen | `2026-08-16-nyiso-140-layup-exclusion` (`basis_sha 2dd9dbc9`) | ⚠️ **PRUNED — survivable via `keeper_snapshot`** | `2026-08-30-nyiso-159-loss-surface` | **🔴 STALE.** Capture-B's second target; re-issued under R-S and unlaunched |

**Count: 3 current / 3 stale / 0 without a golden — 3-of-6 effective coverage**,
unmoved this cycle. *(Coverage counts ISOs, not configs: ERCOT's 2023 carve-out has
no golden of its own, so **full** coverage is 7 captures, not 6, and the row above
is listed separately so the gap is not rounded away.)*

- **🟢 "WHICH TREE IS THE GOLDEN OF" IS NOW A WELL-POSED QUESTION** — per entry,
  for the first time. The per-file `content_hashes` remain the verification
  instrument, but they are no longer the *only* sound one.
- **🟢 THE RETENTION/GOLDEN COLLISION IS RECONCILED ON THE MANIFEST SIDE**, as
  E-7 required and **not** by exempting golden runs from retention. Three of six
  entries have a pruned provenance run and the gate reports it as **information,
  not failure** — the correct posture, because retention is correct policy.
- **🟠 THE PROMOTION-GAP COUNTS ARE STILL NOT RE-DERIVABLE FROM COMMITTED BYTES**,
  and are still labelled rather than re-asserted. The per-ISO keeper shards'
  git history begins 2026-08-26 while the remaining captures date 2026-08-16.
  What **is** derived here: each row's **verdict** (exact, `keeper_id` vs live
  `keeper`), the **registry-presence** column, and the **motion since v19b**
  (MISO **+1**, everyone else **+0**, byte-compared). v15's absolutes are
  carried **under v15's label**; MISO's stands at v15's eleven + 2, NYISO's at
  v15's ten + 1.
- **🟠 THE THREE STALE ROWS ARE THE THREE WHOSE KEEPERS KEEP MOVING — AND R-V HAS
  NOW MADE THAT AN EXPLICIT PARTITION RATHER THAN AN OBSERVATION.** For four
  cycles this board reported the correlation; **R-V's freeze acts on it**,
  holding still exactly the three whose goldens are CURRENT and leaving free
  exactly the three whose goldens are STALE. ⚠️ **But note what that means for
  the freeze's stated purpose: a freeze on {ERCOT, NEISO, PJM} protects goldens
  that already exist; it does NOT help the three stale rows, whose repair is a
  capture, not a hold.** And the standing demonstration is unchanged — **Card 1
  and R-L each took a capture with no freeze at all** (three captures across two
  lanes), so **a freeze was never a precondition for capturing**. The freeze's
  real work is **certification stability**, and that is currently blocked on the
  golden tier being red (J-6), not on any keeper moving.

## Gates

> ⚠️ **SUPERSEDED AGAIN AT v22 (`dfc44d95`) — SEE L-11 for all seven exit codes,
> L-1 for the `ci.yml` job set, and L-15 for the G2 legs.** Figures below that
> v22 re-derives **different**, and which must not be re-quoted: the parity gate
> names **two** bundles, not one (L-4); `check_golden_manifest` reads **42 / 75 /
> 11 enforced with 0 stale**, not 38 / 70 / 6 with 3 stale (L-5);
> `check_forecast_staleness`'s Δ is **`(unknown)`**, not 0 of 10 (L-10);
> `check_bench_freshness` reports **17 engine commits**, not 6; matrix anchors are
> **195 / 49 / 160**. The `Fast test tier` row stays **VINDICATED** and is
> re-confirmed on run 2307 (L-1). Retained as the v20/v21 record.

> ⚠️ **SUPERSEDED AT v21 (`0653bf13`) — SEE K-6 for all seven exit codes and
> K-1 for the `ci.yml` job set.** Two figures below are now WRONG and must not
> be re-quoted: `check_registry_payload_parity.py` is **exit 1** at the v21 pin
> (K-8), not 0; and `check_mechanism_matrix.py` reports **243 WARNs / 160 path
> anchors**, not "0 WARNs / 159" (K-6). The job table's `Fast test tier` row —
> *"NOT named by R-U, and it is G2 leg 2's blocker"* — is **VINDICATED**, not
> superseded (K-2). Retained as the v20 record.

**SEVEN gate SCRIPTS — the roster corrected at v19 (G-7) and re-run at the v20
pin.** ⚠️ **AND A DISTINCTION THIS TABLE MUST CARRY, because R-P and R-U both
turn on it:** these seven are the **audit-program gate scripts**, all of which
exit 0. They are **NOT** the ten `ci.yml` **jobs**, **six of which are red** —
four of them not by design (J-3). Reading "seven gates green" as "CI is green" is
the conflation that would freeze the repository on the branch-protection flip.

**All seven re-run at `07472e7c`. Each invoked on its own with `$?` read
immediately — exit codes captured DIRECTLY and NEVER through a pipe** (a pipe
reports the last stage's status, and has green-washed a gate on this program
before). Outputs read, not quoted from the v19b block.

| gate script | exit | reading at `07472e7c` |
|---|--:|---|
| `audit_keepers.py` | **0** | **PASS — 0 failures, 0 warnings**, over `complete` = {ERCOT, NEISO, PJM}; the MISO promotion is clean through it, and M1's re-key check is satisfied **vacuously** for MISO (no `complete` entry ⇒ no re-key owed) |
| `check_registry_payload_parity.py` | **0** | **OK — 60 runs checked, 95 bundle dirs swept, 0 known-unsynced tolerated.** Identical to v19b **across a promotion + two registrations + two prunes**, which is the retention/parity pair working. Residual allowlist **8** (R-J) |
| `check_mechanism_matrix.py` | **0** | integrity OK, base + **6 ISO shards**; anchors ⬅ **194 field + 49 row + 159 path** (v19b: …156 — **+3 path, no new `ScenarioConfig` field**), **0 WARNs**, 0 unresolvable beyond the ratchet. Keeper stamps + §5.x headers match every shard **across the MISO promotion**. ⬅ **The dispatch's "243 WARNs, repaired by `f5b33644`" does not survive re-derivation — 236, in-branch only, never on `main`** (J-12) |
| `check_forecast_staleness.py` | **0** | ⬅ **Δ = 0 of 10** (v19b: 2) · ⬅ **91 stamped / 65 scored** (v19b: 89/57) · ⬅ **25 of 56 verdict stamps undated** (v19b: 31 of 55 — one added, six re-scored) · ⬅ **26** config epochs · board inputs **all present** · newest scored `cba50e46aa70` @ 2026-09-02T02:09:15Z. The undated-stamp WARN **persists, unchanged in kind** |
| `check_bench_freshness.py` | **0** | **20 parts checked, 0 STALE, 20 with engine drift** at 6 engine commits — unchanged, and still the repaired instrument's honest reading (R-J). Builder fingerprint at HEAD `dbea7bf45111` |
| `check_gate_a_provenance.py` | **0** | ⬅ **THE ONE GATE THAT CHANGED STATE IN THIS WINDOW: exit 1 → exit 0**, repaired by #4561 (R-T). **6 rows: keeper identity + marker state match the backcast store; no determination read.** This was its **THIRD** real firing (J-2) |
| `check_golden_manifest.py` | **0** | **38 manifests, 70 entries (6 enforced / 64 legacy, 62 of the legacy with a pruned provenance run); of the enforced, 3 with a pruned provenance run, 3 stale vs the live keeper.** ⬅ **MISO's STALE line now names `2026-09-01-miso-198-oomlevel`** — the gate tracked the promotion unprompted (J-8) |

**The `ci.yml` JOB set at the same pin, from run 2295 (#4561's own PR, head
`f863458a`) — the most recent COMPLETED run, and 17 runs after v19b's run 2278.**
⚠️ **Every `ci.yml` run in the last 30 is a `pull_request` event; there is no
`push`-on-`main` run at all**, so "red on `main`" here means *reproduces from
base-branch content on every PR head*, which is what the 30-for-30 failure streak
shows.

| job | conclusion | Δ vs run 2278 | covered by a gate script? |
|---|---|---|---|
| `Rule-22 quarantine gates` | 🟢 success | — | yes — audit_keepers + parity + golden-manifest |
| `Rule-28 mechanism-matrix guard` | 🟢 success | — | yes — matrix |
| `Cache-key registration guard` | 🟢 success | — | no |
| `FR-21 forecast-board staleness (WARN only)` | 🟢 success | — | yes — staleness + **the hard gate-(a) step** |
| `Pinned default cache key` | 🔴 **failure** — *Pinned-key + declared-default guard tests* | **unchanged** | **no** · **R-U** |
| `Ruff lint + format` | 🔴 **failure** — *Ruff lint*; format check never reached | **unchanged** | **no** · **R-U** |
| `Structural refactor guards` | 🔴 **failure** — *facade re-export + persisted-identity tests*; compileall and import-walk both green | **unchanged** | **no** · **R-U** |
| `Fast test tier` | 🔴 **failure** — *Fast pytest tier*, **8 min 18 s to completion**, failed on **content** | **unchanged** | **no** · ⚠️ **NOT named by R-U, and it is G2 leg 2's blocker** |
| `FR-22 backcast->forecast parity` | 🔴 failure — **by design**, a live calibration-desk signal | unchanged | no |
| `Forecast-invariant artifact audit` | 🔴 failure — unverified | unchanged | no |

**Four green, six red, only two of the six red *by design* — IDENTICAL IN EVERY
CELL to run 2278, 17 CI runs and 29 merged PRs later.** The other four — pinned
key, ruff, structural guards, fast tier — are **unowned engine defects merged
past because no check is required**. **R-U charters the repair and R-U has not
launched** (J-3, J-11). **That is simultaneously the strongest argument FOR
R-P's flip and the reason the flip still cannot use R-P's list unamended.**

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — NOT DECLARED. ⬅ THE TWO OWNER PARKS ARE LIFTED (R-V); WHAT REMAINS IS
  DEFECTS AND EXECUTION, WHICH IS A BETTER PLACE TO BE BUT IS NOT CLOSER TO
  TODAY.** Every leg re-read at this pin:
  1. **PERF-B merged byte-green** — 🟠 ⬅ **IN MOTION, AND NEWLY UNBLOCKED ON
     PERMISSION.** Both parks that gated it (WS3, golden tier) are lifted. **Three
     things still stand between it and closure, all of them work:** (i) coverage
     is **3 current / 3 stale** and `results/regression-goldens/` moved **zero
     bytes** this window, R-S's re-issued captures unlaunched (J-9, J-11);
     (ii) 🔴 **the golden tier is un-parked but RED** — three consecutive
     scheduled runs failing on content, and **unexercised** since (no
     `workflow_dispatch` at this pin), so **no capture can be certified
     byte-green** (J-6); (iii) ERCOT's carve-out is still unrepresentable until
     R-O's schema lane runs. **The leg wants *merged byte-green*, not captures** —
     and byte-green currently has no working instrument.
  2. **One completed fast-tier-green `ci.yml` run** — 🔴 ⬅ **BLOCKED ON R-U**,
     the classification v19b assigned and this cycle confirms unchanged. On run
     2295 the **`Fast test tier` job still FAILS on content** after 8 min 18 s to
     completion. **R-U charters the repair; R-U has not launched** (J-3, J-11).
     **It is not a decision, it is a defect — and it is now a defect with an
     owner.** ⚠️ R-U's charter names three jobs and **this is not one of them**;
     whether it is in scope is unadjudicated (J-3).
  3. **A keeper freeze** — 🟢 ⬅ **SATISFIED. DECLARED BY R-V** on **{ERCOT,
     NEISO, PJM}**, taken **together with the golden tier** exactly as this board
     recommended for six cycles and as restart-checklist item 1 required.
     **{MISO, CAISO, NYISO} explicitly unfrozen.** The leg's longest-standing
     owner call is closed (J-4).
  4. **Branch-protection flip** — 🔴 **RULED R-P: FLIP NOW, fast gates only — AND
     STILL NOT LIVE.** Its two blockers are **both unchanged at this pin**: three
     of the seven proposed required checks are still red (now R-U's charter), and
     `file-integrity-guard` is still path-filtered. **Blocked on R-U, then on the
     owner's Settings action**, which no lane can perform or verify.

  **Net: leg 3 closes, leg 1 moves from *parked* to *in motion*, legs 2 and 4 are
  both blocked on the same unlaunched R-U lane.** On declaration the PM notifies
  the FFR desk (Q.2 battery) — **still not firing.**
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**, whose charter is
  satisfied, gate green, and last recommendation (B-8) executed under R-J.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg.**

## Watch

- **🔴 NEW — FOUR UNOWNED ENGINE DEFECTS ARE SITTING RED ON `main`, AND NOTHING
  STOPS THEM.** Measured on run 2278 (H-1): **`Ruff lint + format`** (5 errors —
  three `F821` **undefined names** in `src/market_sim/runner.py`:
  `entry_walks`, `entry_reserve_adders`, `build_nyiso_link_loss`, plus two
  dead-code lints in `scripts/gen_caiso197_attestation.py`), **`Pinned default
  cache key`**, **`Structural refactor guards`** (facade re-export +
  persisted-identity tests) and **`Fast test tier`** (now failing on **content**,
  not on the checkout the memo diagnosed — it ran 8.5 minutes to completion).
  **None is red by design**, unlike FR-22 and the invariant audit; each is a
  defect merged past because **no check is required**. Three of them are in
  R-P's proposed required set, which is why the flip cannot use that list
  unamended. **Not this program's to fix** — `src/market_sim/` is the
  calibration/engine desks' surface, and an `F821` is a real latent bug, not a
  lint nit. **Routed, not adjudicated; recorded so the next flip attempt sees it
  before it freezes the repo.**
- **🟠 NEW — A REQUIRED CHECK THAT IS PATH-FILTERED BLOCKS EVERY PR IT DOES NOT
  RUN ON.** `file-integrity-guard` filters its `pull_request` trigger to
  `src/**`, `scripts/**`, `CLAUDE.md`, `model-methodology-spec.md`,
  `.github/workflows/**`. GitHub treats a required check that never reports as
  **pending**, not passed — so requiring it strands every docs-only PR, **this
  records lane's included**, forever. Memo §3's *"if it reports a check on PRs"*
  qualifier is load-bearing. **The fix is a widened filter or an always-run no-op
  job, not a weaker required set** (H-1).
- **🔴 SHARPENED AGAIN AT v20 — THE NON-LAUNCH RATE IS THE PROGRAM'S DOMINANT
  FAILURE MODE, AND THE INSTRUMENT THAT FINDS IT HAS LOST A LEG.** v19 recorded
  four in one sitting; v19b added two (R-Q's captures); v20 adds **three more** —
  R-S's re-issues of Capture-A/Capture-B/R-O count as second issues, and **R-U
  and PERF-B are new and unlaunched** — for a running total of **NINE dispatches
  that produced no session**, of which **five are currently outstanding**. R-O's
  schema lane is now unlaunched across **three** pins. **The check still costs
  one `ls-remote` and one PR list.**
  ⚠️ **AND THE LIMIT IS NO LONGER A CAVEAT, IT IS THE METHOD: the session-roster
  tool is no longer in this desk's surface, so detection is GIT-ONLY.** A lane
  that launched and died before its first push, and a lane running right now with
  nothing pushed, are both **indistinguishable from never-dispatched**. Every
  "never launched" on this board means, strictly, **"no branch and no PR at this
  pin"** — and that phrasing is used wherever it is asserted. **The director's
  question from v19b — *why* — has been made harder to answer, not easier**, and
  it remains the director desk's.
- **🔴 REPLACED AT v20 — GOLDEN TIER: THE PARK IS LIFTED (R-V), AND THE ITEM IT
  REPLACES WAS FACTUALLY WRONG FOR FIVE CYCLES.** This bullet read *"PARKED BY
  OWNER RULING 2026-08-22 … the CI proof is **deliberately unspent** … record it
  as a park, not a blocker"* for seven cycles. **Measured against the workflow's
  own run list, the proof was NOT unspent**: a `schedule` trigger has fired the
  tier weekly on `main` and **runs #5 (2026-08-17), #6 (08-24) and #7 (08-31) are
  all RED.** Run #7 failed at **`Data-provisioned pytest tier (serial)`** after
  provisioning green — a **content** failure, **not** the OOM class #4071 fixed,
  so the local four-step replay this board cited as verification does not cover
  it. **The correct reading now: the tier is UN-PARKED, UNEXERCISED (no
  `workflow_dispatch` since run #4, 2026-08-15) and FAILING.** The consequence is
  unchanged in effect and changed in kind — PJM, NEISO and ERCOT-forward are all
  CURRENT and **none can be certified byte-green**, no longer for want of
  permission but because **the tier does not pass**. ⚠️ **And the meta-lesson is
  the one to keep: a state recorded once and never re-measured is a carried
  figure**, which is exactly what the refresh protocol exists to prevent — it
  simply had no step pointing at a workflow's run list. **Not this program's to
  fix** (the tier's tests are the engine desks' surface); **routed, not
  adjudicated** (J-6). It also instantiates CLAUDE.md's *"scheduled workflows
  spend money with nobody watching"* on this program's own workflow, in a private
  repo, for three weeks.
- **🟢 RETIRED — THE STAGE-0 MANIFEST'S SINGLE-SHA PROVENANCE DEFECT.** Carried
  and sharpened across v15–v18; **FIXED under R-J** (#4502). Schema v2 gives every
  entry its own `provenance` and `keeper_snapshot`, the shared top-level `git_sha`
  is **removed**, and R-L's two captures **demonstrated** the fix (each changed
  only its own entry). Retired on execution, not on argument.
- **🟢 RETIRED — THE RETENTION/GOLDEN COLLISION.** Also R-J. Reconciled **on the
  manifest side**, exactly as E-7 required and **not** by exempting golden runs
  from retention. Three of six entries have a pruned provenance run; the gate
  reports it as information, and `keeper_snapshot` makes it survivable. The
  dead-bundle class E-7 warned about was never created.
- **🟢 RETIRED — THE BENCH-FRESHNESS DATE-KIND / DAY-BOUNDARY ARTEFACT.** Also
  R-J. Both sides of the comparison now use the **committer instant in
  offset-bearing form**, and `--since`'s inclusivity is verified in the docstring
  rather than assumed. **The reading discipline it forced is retired with it** —
  "20 of 20 with drift" at this pin is a true statement about a repaired
  instrument. **What is NOT retired is the substantive caution**: 0 STALE is the
  reading that matters, engine drift is ungated by design, and a *marginal* C1
  verdict still deserves a bench regeneration first.
- **🟢 RETIRED — THE STALE FORECAST GATE-(a) STAMP CLASS.** Carried since v15 and
  the direct cause of two alignment breaks. **Now gated in CI**
  (`check_gate_a_provenance.py`, hard, `ci.yml:213`) and **proven live**: it went
  red on the caiso-231 promotion and green after R-N's re-key (G-5). ⚠️ **The
  narrower half survives and is recorded so the retirement is not read too
  broadly:** the guard checks **keeper identity + marker state** and **explicitly
  reads no determination**, and **nothing compares `frontier` membership to
  anything**. Three of the four instruments are now cross-checked. The fourth is
  not — see the next item.
- **🟠 CARRIED, NARROWED — NOTHING IN THE REPO COMPARES ALL FOUR INSTRUMENTS.**
  At this pin all four agree at **{ERCOT, NEISO, PJM}** (G-9), and the *mechanism*
  that broke the alignment twice is now gated. But the alignment itself is still
  established **only by this board re-deriving it every cycle**, and the
  `frontier` leg has no instrument at all. **A cycle of agreement is not a closed
  item** — v16 retired this on one cycle's alignment and v17 un-retired it.
- **🟠 NEW — A KEEPER SETTING ONE FIELD THROUGH TWO CHANNELS: the `ercot_wtx_*`
  CONFLICT IN THE ERCOT KEEPER'S RECORDED CONFIG.** Surfaced by R-L's capture
  and recorded verbatim rather than smoothed over: *explicit kwargs
  `{'ercot_wtx_curtailment_driver': False, …}` are stomped by `prb_overrides`
  `{'ercot_wtx_curtailment_driver': True}` in the LIVE solve (`run_year` applies
  `prb_overrides` last); recording the prb values. Pass the driver through ONE
  channel.* **Three things this is NOT**, each stated so nobody over-reads it: it
  is **the keeper's own recorded config**, not something the capture introduced;
  the golden records the `prb` values, i.e. it **reproduces the keeper's live
  behaviour**, which is what a regression baseline must do; and it is **not a
  fidelity failure** — the oracle passed at 271 flags identical, 0 drift. **What
  it IS: a latent rule-24 `[R-REGISTRY]`-adjacent hazard** — a value whose
  effective setting depends on application order rather than on the registry.
  **ROUTED TO THE CALIBRATION DESK, which owns ERCOT's config; it is not this
  program's to fix**, and this board neither adjudicates nor schedules it.
- **🔴 NEW — DO NOT QUOTE MONITORING NOTIFICATIONS; READ LOGS.** R-L's capture
  lane disclosed, rather than quietly dropping, that **three streamed progress
  events its own logs do not corroborate** arrived through session log-tail
  notifications: `Solve: 163.216s (warm)` and `Solve: 342.735s (cold)` appear in
  **no log file** (grep count 0) and match none of the twelve real ERCOT solve
  times — and **ERCOT ran zero warm solves**, so a `(warm)` ERCOT event could not
  have been genuine; `solving ERCOT 2024` **is** real but was **delivered before
  it existed in the file**. **Two fabricated, one premature.** This is an
  **infrastructure observation, not a modelling finding**, and it is on the watch
  because of what it implies for every session on this program: **a streamed
  progress notification is not evidence.** Every timing, count and status in a
  finding must be read from committed logs and artifacts. The capture lane did
  exactly that, which is why its numbers stand.
- **🟠 NEW — A SHARED, CI-GATED BASE FILE WAS REWRITTEN BY A LANE THAT DID NOT
  DECLARE IT.** #4522 (`369c9bb7`) moved **120 line-pairs** of
  `docs/codebase-site/data/mechanism-matrix.js` inside a commit whose subject and
  body are entirely about a forecast FC-6 re-score (G-8). **The edit was correct**
  — verified digits-only by normalisation — and it discharged this lane's job 4.
  **The class is the silence, not the change.** Recorded beside its own
  counter-example one PR later: **#4523 handled the same shared surface well**,
  rebasing onto the disjoint edit rather than overwriting it (G-5). Not
  adjudicated; the matrix is rule 26's surface and three desks write near it.
- **🔴 SHARPENED, THIRD INSTANCE — THE SHALLOW-CLONE TRAP, AND IT HAS COST A
  PUBLISHED READING.** G-13. Three sessions, three containers, one failure: a
  `git cat-file` absence in a shallow clone is **indistinguishable from a sha
  that never existed**. It produced **v17's wrong `af1ccb6` reading** (which R-J's
  lane overturned), and it would have made **this** lane annotate six healthy
  verdicts as permanently unverifiable had it trusted the local answer. **Nothing
  gates it.** The discipline: check `--is-shallow-repository` **before** reporting
  any absence, then `git fetch --filter=tree:0 --unshallow` (~2 s) or confirm
  against the remote API.
- **🔴 CARRIED — TWO LIVE DEFECTS IN A COMMITTED CALIBRATION REFERENCE.**
  `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` — a cascade
  **sum** where the **max** is correct, and a positional `hoy` map that never
  localizes prevailing Eastern to the model's standard-time clock — in **every
  column, every year**. **Blast radius unchanged: NO keeper, NO scored result, NO
  determination**; its only consumer is the post-solve RCPF comparator for
  co-opt-off runs, `nyiso_rcpf_enabled` is False in the NYISO keeper, and rule 19
  `[R-ONE-MECH]` makes arming it alongside `energy_reserve_coopt` a hard error.
  **A trap for DIAGNOSTIC sessions, not a defect in any result.** Still on watch
  because **nothing gates it** — no CI check reads a `_validation-source/`
  reference for internal consistency. ⬅ **The sibling half in MISO is repaired**
  (#4497, D-9); **the NYISO reference itself is not.**
- **🟠 CARRIED — THE FORECAST SEED CARRIES TWO READINGS AT ONCE.** Its top-level
  prose and its per-ISO `gate` blocks disagree about who holds what. **A different
  program's file; recorded, not adjudicated.** The per-ISO blocks are the
  authority, and this board derives gate (a) from them plus the live shards,
  never from the prose. ⬅ **Narrowed in one respect**: the per-ISO blocks' *stamps*
  are now CI-guarded, so the disagreement can no longer be about which keeper a
  row names.
- **🟠 CARRIED — the standing parity-gate hazard, and it recurred this cycle in
  its mildest form.** The gate reports a LIVE lane's pre-registered control /
  recipe dirs as "dead solve output". The dispatch carried a parity **red** on
  `caiso231_a0_control` from the previous sitting; **it resolved transiently when
  that lane's own registrations landed** (#4506, #4515), with no fix made and
  none needed. **Before reporting a future parity red, check whether the named
  dirs belong to a running lane — never recommend pruning a dir a live lane
  owns.** ⬅ **The structural half is now fixed** (B-8 exists; allowlist 40 → 8),
  so the gate's green is closer to a property than the maintenance state it was.
- **🟠 CARRIED — FORECAST-BOARD STALENESS.** Δ = **0** of 10 at the pin (v17: 1).
  What stays on watch is unchanged and is not the Δ: **31 of 55 verdict stamps
  are still undated** (freshness UNKNOWN until each passes through the stamped
  scorer) and **25 config epochs** now sit on the board (v17: 24, v16: 20, v15:
  14 — grown every cycle this board has measured it); confirm mixed-vintage
  comparison is intended before reading any cross-run delta as a model effect.
  ⬅ **Two of those stamps are now annotated as permanently unverifiable** (R-M,
  G-4) — which does not change the count, and is not meant to: the annotation
  records that their freshness can never be established, rather than pretending
  it has been.
- **🟠 CARRIED, AND PARTLY ANSWERED — EVIDENCE PROSE IS GATE-CHECKED NOWHERE.**
  `check_mechanism_matrix.py` validates `keeper:` stamps and §5.x prose headers
  and passes while citation text beside them goes stale. **Whether any gate
  should read evidence text remains unruled.**
- **🟠 CARRIED — #4054 / nyiso-140 null-treatment question**, never adjudicated —
  and now eleven promotions out of reach.
- **DURABLE LESSON (unchanged; the park makes it sharper):**
  `golden-data-tier.yml` is the ONLY workflow that runs
  `scripts/regenerate_clean.py`, so any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal while the tier is parked.
  **Treat curate-script changes as unguarded.**
- **🟢 DURABLE LESSON, earned again — a negative or zero-solve result with a
  proof beats a positive one without.** This window: **nyiso-169's
  congestion-gradient half found NOT CARRIED by any binding constraint and the
  lane STOPPED**; **nyiso-168 killed its one new mechanism ex ante**;
  **miso-195 refuted the remove-only outage-envelope cap at phase 0**; **caiso-231
  recorded a pre-registered gate it could not satisfy rather than dropping it**;
  and **R-J's repair lane overturned two of THIS BOARD'S standing claims in its
  own commit message**. The sharpest measurements of the cycle again came from
  the negatives and the self-corrections.
- **🆕 DURABLE LESSON — RE-DERIVE A DISPATCHED JOB'S *PRECONDITION*, NOT ONLY ITS
  FIGURES.** v15 taught *re-derive the table that cannot have changed*; v16 added
  *re-derive the reading that improved*; **v19 adds: re-derive that the job still
  needs doing.** Two of this lane's six jobs came back already-discharged (job 4,
  G-8) or moved (R-M's target, G-4). Executing either blind would have produced a
  false record — an empty commit claiming a repair, or an annotation on the wrong
  verdict. **A dispatch describes the world at derivation time; the pin is the
  world.**

## Forecast board — re-derived at `07472e7c`: ALL SIX gate-(a) stamps CURRENT AGAIN, after R-T repaired the one the MISO promotion broke

**RE-DERIVED AT THE v20 PIN.** Every `a_keeper_marker` row was re-compared
field-by-field against the live `keepers/<ISO>.json` and the live `complete`
block, and independently against `check_gate_a_provenance.py` (**exit 0**, 6
rows). Four-instrument alignment **HOLDS at {ERCOT, NEISO, PJM}** under the same
fail-closed null handling (J-7).

⬅ **ONE ROW MOVED, AND ITS HISTORY IS THE POINT.** MISO's stamp named
`191-bexit` while the backcast store had promoted to `198-oomlevel` — for **nine
merged PRs**, from #4552 to #4561. The guard **caught it** (its third real
firing), the director **re-keyed it** under a one-push grant, and **R-T's routing
half now makes the gap zero**: the promoting PR carries the re-key (J-2).

**Re-derived, not carried — and the seed's schema was re-read rather than
assumed** (the v16 protocol amendment, applied again; this file belongs to a
different program and has been restructured more than once). Every
`gate.a_keeper_marker` was compared field-by-field against the live
`keepers/<ISO>.json` and the live `complete` block at the pin, **and
independently against `check_gate_a_provenance.py`, which now machine-checks the
same identity in CI (exit 0)**. Legs (b)/(c)/(d) and `open` are read from each
ISO's own `gate` block.

| ISO | Seed names (gate a) | Live keeper | (a) | (b) | (c) | (d) | `open` |
|---|---|---|---|---|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | same | **pass — CURRENT** | fail | pass | none | false |
| PJM | `2026-08-15-pjm-162-inputclock` | same | **pass — current** | fail | pass | none | false |
| NEISO | `2026-08-17-neiso-99-joint-p1` | same | **pass — current** | pass | pass | **granted** | **TRUE** |
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` | same | **fail — ON THE MERITS**, stamp **CURRENT** (`NOT-YET`, absent from `complete`) | fail | fail | none | false |
| MISO | ⬅ **`2026-09-01-miso-198-oomlevel`** (was `191-bexit`; **re-keyed #4561, R-T**) | same | **fail — ON THE MERITS**, stamp ⬅ **CURRENT AGAIN** (`NOT-YET`, absent from `complete`) — **verdict unmoved by the re-key** | fail | pass | none | false |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | same | **fail — ON THE MERITS**, stamp **CURRENT** (marker **withdrawn**, handled fail-closed) | pass | pass | none | false |

**Gate (a) passers = {ERCOT, PJM, NEISO} = the `complete` set = the CALIBRATED
set = the active `frontier` set. FOUR-INSTRUMENT ALIGNMENT HOLDS** (J-7) — a
third consecutive cycle, and the first to hold **across a keeper promotion and a
stamp re-key inside the same window**.

**🟢 ZERO STALE STAMPS — BUT THE HONEST VERSION OF THAT SENTENCE IS NEW.** v17
reported four of six stale and found the whole alignment break was that
staleness. v19 reported zero stale for the first time. **This cycle is the first
in which a stamp went stale AND was caught AND was repaired inside the window** —
so "zero stale at the pin" is now a statement about a **working loop**, not a
lucky quiescent moment. The three non-passing rows are failures **on the merits**
(determination / marker), never stamp artefacts.

⚠️ **AND THE LOOP HAD A NINE-PR LAG, WHICH IS WHY R-T's ROUTING HALF MATTERS MORE
THAN ITS EXECUTED HALF.** The guard is a **detector**, not a preventer: it fires
on the *next* PR, and the stamp stayed wrong from #4552 to #4561. **R-T moves the
duty to the promoting lane's own PR**, which converts the detector into a
precondition and takes the lag to zero (J-2).

**🟢 THE FIRST OPEN GATE IN PROGRAM HISTORY HOLDS A SECOND CYCLE.** NEISO keeps
all four legs with `open: true`, leg (d) **granted**. **This board adjudicates
none of it**: the forecast namespace is a different program's, its legs move on
that program's rulings, and **every FC-4 behind a passing leg (c) is still a FAIL
reported at full magnitude**. It is recorded because a leg this board published
as `none` for every ISO, every cycle, moved — and has now stayed moved.

**🟠 The seed still carries two readings at once** — its top-level prose and its
per-ISO blocks disagree about who holds what (Watch). ⬅ **Narrowed**: the blocks'
*stamps* are now CI-guarded, so the disagreement can no longer be about which
keeper a row names. Both recorded; **neither adjudicated**.

**🟠 AND TWO FORECAST VERDICTS ON THIS BOARD NOW CARRY A PERMANENT PROVENANCE
CAVEAT.** Under R-M (G-4), `neiso-t3-pre-fc5` and `neiso-t3-pre-fc6` are
annotated as having a `scored_at_sha` that never reached `main` and can never be
resolved. **Both are archival preserved-prior verdicts, both read `HOLD`, and
neither determination was touched.** No live gate leg above rests on either.

**No forecast run was solved or re-scored by this lane**; per rule 15
`[R-DASHBOARD]` the forecast namespace is registered through
`scripts/register_forecast_run.py` alone, and the backcast CI gates stay blind
to it. **The R-M annotation is a records edit to a committed input, not a
re-score**: no scorer ran, no determination moved, and
`check_forecast_staleness.py` exits 0 before and after.

## Owner queue at cycle end

> ### ⬅ **v23 ADDITIONS AND STATE CHANGES, re-served at `49bfbc49`.** The v22 and
> v20 lists below are retained; these amend them. **W-1 and W-3 are RETIRED BY
> EXECUTION** (X-0).
>
> **X-0. 🟢 RETIREMENTS — TWO v22 QUEUE ITEMS CLOSE BY EXECUTION.** **W-1 (R-W not launched)
> is RETIRED BY EXECUTION**: R-W landed as #4611 and is discharged (M-3), and
> **R-X and R-Y launched, landed and merged inside this lane's own session**
> (M-4, M-5). **G-14's non-launch tally does not advance this cycle.** **W-3 (the
> reproducing parity defect) is RETIRED BY EXECUTION**: the calibration desk
> registered both `miso200_*` legs in #4609 and
> `check_registry_payload_parity.py` is **exit 0** (M-8) — the transient-class
> resolution v21 predicted. **W-2 (the flip) STANDS, amended by X-1.**
>
> **X-1. 🔴 TOP OF THE QUEUE — THE FLIP'S BLOCKER (a) HAS RE-REDDENED, AND IT IS
> NOW A THREE-FILE CLEANUP.** `Ruff lint + format` is red on `main` again, but
> **not from the source tree**: 5 `ruff check` errors, **all in per-run capx probe
> scripts** under `docs/handoffs/d37/` and `docs/handoffs/d45/` (`E731` ×3,
> `E402`, `E401`), with **10 files** failing the format step behind it (M-7).
> R-X's rider fixed R-W §7.2's three files and the job stayed red for a reason
> nobody had tracked. **Two decisions belong to the owner/director, neither of
> them large:** (i) do the cleanup — small and mechanical; (ii) decide whether
> **per-run probe scripts checked into `docs/handoffs/` should be linted at all**,
> since they are session artifacts, not maintained source, and they will keep
> re-reddening this job. **Then the Settings action, which no lane can perform or
> verify.** Everything else about W-2 is unchanged and executable as written.
>
> **X-2. 🟠 STAGE-0 HAS REGRESSED 7-of-7 → 4-of-7 — THREE RE-CAPTURES, AND THEY
> ARE LEG 1's LAST STRUCTURAL ITEM.** The 2026-09-02 promotions left the CAISO,
> MISO and NYISO stage-0 goldens stale (M-6), independently confirmed by R-Y §8.
> **Capture-A's MISO capture is now a *re*-capture.** With R-Y's instrument green
> again, this is the item standing between PERF-B and a byte-green claim against
> live keepers. **Route: the PERF-B / stage-0 capture lane, under the R-O
> partition schema.** *(Not a records act; this lane does not touch goldens.)*
>
> **X-3. 🟠 CARRIED FORWARD, UNCHANGED — THE WS3-NEXT CHARTER `markup` HAND-BACK.**
> L-8's item stands exactly as written: **`markup` at 471–601 s/yr, ~50× the next
> item, unattributed.** It is a **charter item, not a lane** (R-Y §9 reaches the
> same conclusion independently and calls adjudicating it *"the substantive item
> leg 1 waits on"*). Attribute it or close it; either discharges it.
>
> **X-4. 🟢 NEW, SMALL, OPTIONAL — SCRIPT HYGIENE ON THE TWO IMPORT-TIME ENV PINS.**
> Per R-W §7.6. `scripts/capture_keeper_goldens.py` and
> `scripts/replay_keeper.py` mutate `os.environ` **at import time**
> (`MARKET_SIM_HIGHS_THREADS`, `MARKET_SIM_WARMSTART`, `MARKET_SIM_WARMSTART_XYEAR`).
> That is correct for each script's own CLI process and **was the mechanism behind
> every inflated local test count this program has recorded** (M-3). **The leak is
> already closed on the test side**, where it did the damage — the question is
> only whether the pins should move under `main()` so a future by-path load is
> **safe by construction**. `replay_keeper.py` has no test loading it today and its
> pinned value equals the `pipeline/solve.py` default. **Small optional charter,
> not a defect.**
>
> **X-5. 🟠 STANDING TAX, NOT AN ITEM — MECHANISM-MATRIX ANCHOR DRIFT.** R-W §7.7
> recorded an instance: 25 stale `scenarios.py:NNNN` anchors on run 2324, from
> `main` commits that grew the file between two runs of the same PR. **It resolved
> upstream on its own** and the guard is **green at this pin** (M-8). Recorded so
> the class is named: **anchor drift is a standing tax on a heavily-crossed file,
> and the digits-only repair belongs to whichever lane next touches
> `scenarios.py` — never to a records lane, which is forbidden matrix edits.**
> No owner action.
>
> **X-6. 🟠 TWO SILENT DEGRADATIONS THE EXIT CODES DO NOT SHOW.** Both gates exit
> 0 and both are drifting: **`check_bench_freshness` is at 24 engine commits**
> (v20: 6, v22: 17 — quadrupled) with **no bench part regenerated**, and
> `check_forecast_staleness` now reports **35 config epochs** (v22: 28) with **25
> of 65 verdict stamps carrying no scored-at date** (M-8). Neither blocks
> anything today; both make a marginal C1 verdict and any cross-run delta less
> trustworthy the longer they run. **Flagged for visibility, adjudicated by
> nobody here.**
>

> ### ⬅ **v22 ADDITIONS AND STATE CHANGES, re-served at `dfc44d95`.** The v20
> list below is retained; these amend it.
>
> **W-1. 🔴 NEW AND TOP OF THE QUEUE — R-W IS CHARTERED AND HAS NOT LAUNCHED,
> AND IT IS NOW LEG 2's *ONLY* ROUTE.** The fast-tier repair lane was dispatched
> 2026-09-02 by card. At this pin: **no branch, no open PR (repo-wide: zero), no
> merge, and ZERO mentions of `R-W` anywhere on this board before this entry**
> (L-3). **This is non-launch #5** on G-14's tally. ⚠️ **What makes it different
> from the previous four: R-U is now DISCHARGED** — all three of its charter jobs
> are green in run 2307 (L-2) — **so no other lane is even adjacent to the
> `Fast test tier` job.** Leg 2 has a correct diagnosis, a dedicated ruling, and
> nobody working it. **Owner/director action: the second-order question G-14 and
> J-11 already posed — not "re-send it" but establish why dispatches are not
> producing sessions**, now on its fifth instance.
>
> **W-2. 🟢 R-P's FLIP — BOTH BLOCKERS ARE NOW CLEARED IN CODE; ONLY THE
> SETTINGS ACTION REMAINS.** Blocker (b) was repaired by `f0fb9ce4` (#4564).
> **Blocker (a) is now repaired too**: `Pinned default cache key`, `Ruff lint +
> format` and `Structural refactor guards` are **all three green in run 2307**
> (L-2) — the confirming green run item 1 below asked for. **And the flip is
> measurably NOT live**: 30-for-30 red `ci.yml` runs against 13 merges in this
> window (L-1, L-15). **The sequencing this board has recommended for four
> cycles is now executable as written**: require the green checks now, add
> `Fast test tier` the day R-W lands. **No lane can perform or verify the
> Settings action.**
>
> **W-3. 🔴 THE PARITY DEFECT IS REPRODUCING — ROUTE IT TO THE CALIBRATION DESK
> WITH THE COST ATTACHED.** Two dead `miso200_*` bundles now, not one; the second
> landed **in-window** via #4607; **both tracked on `main` at 14 files each**
> (L-4). **Not this program's to fix** — register, prune or allowlist is the
> calibration desk's call — **but it is one additional dead bundle per push from
> that lane, and it reddens the parity job on every PR the repository opens,
> including this board's own.** The escalation asked for is the cost, not the
> remedy.
>
> **W-4. 🟠 WS3-NEXT CHARTER ITEM (NOT A LANE) — THE `markup` PHASE.** PERF-B
> session 1's hand-back, queued as instructed: `markup` = **471–601 s/yr** on the
> ERCOT arms vs `results_write` **8.3–11.4 s**, **~50×** the phase PERF-B
> optimized, and **UNATTRIBUTED** (L-8). **No prompt is issued and none should
> be until WS3's next charter is written** — this is the measurement that charter
> should open from. ⚠️ **And its premise is corrected**: **all four** of PERF-B's
> charter items are **CLOSED**, not three-of-four open (L-7). The only repair
> owed is a citation re-pin (`scenarios.py:13606` → `:13825`).
>
> **W-5. 🔴 Q-2 IS WIDER, NOT RETIRED — AND IT NOW HAS THREE SUB-CLASSES.**
> `ff-verdicts.json` provenance: **3 shas genuinely absent** (all NEISO T3, and
> **the defect regenerated onto `neiso-t3` after D-2 named it**), **1 live
> unmerged branch blinding the staleness Δ**, **2 pre-rewrite orphans carrying 19
> refs** that are dead by construction of the 2026-08-16 history rewrite (L-10).
> **Three distinct repairs, not one.** The instrument-blinding sub-class is the
> one that costs the board a reading every cycle.
>
> **W-6. 🟠 A METHOD DEBT THIS LANE INCURRED AND PAID, WORTH ONE LINE OF OWNER
> ATTENTION.** G-13's shallow-clone rule is correct but **insufficient**: its
> prescribed remedy creates a **partial clone whose reachability probes mutate
> their own answers** by lazy-fetching (L-9). The extended rule is written into
> the Refresh protocol. **Fourth container in four sittings to hit this.**

Re-served and re-verified at **`07472e7c`**. **The 2026-09-01 THIRD sitting adds
four ruled items (R-S, R-T, R-U, R-V), RETIRES R-R by holding it, and RETIRES
R-T's executed half by execution.** Q-1 and Q-2 stay retired by execution;
**nothing retired is ever re-served**. What remains:

1. **🔴 CARRIED, BOTH BLOCKERS UNCHANGED — R-P's BRANCH-PROTECTION FLIP IS RULED,
   THE MEMO IS REFRESHED, AND THE LIST AS WRITTEN WOULD STILL FREEZE THE
   REPOSITORY.** The dated check-name refresh is in
   `docs/governance/branch-protection-memo-2026-08.md`, with the `FR-21` naming
   caveat recorded (its display name says *WARN only*; it has carried the **hard**
   `check_gate_a_provenance` step since R-J). **Both blockers re-measured on run
   2295 and both stand:** (a) **`Pinned default cache key`, `Ruff lint + format`
   and `Structural refactor guards` are still RED**, unchanged in every cell 17
   CI runs later — ⬅ **these are now R-U's charter, so the blocker has an owner
   for the first time**, and R-P's flip is **blocked on R-U**; (b)
   **`file-integrity-guard` is still path-filtered** and would strand every
   docs-only PR as *pending*. ⚡ **POST-PIN: BLOCKER (b) IS REPAIRED, BY NAME** —
   `f0fb9ce4` (#4564) drops the `paths:` filter from `file-integrity-guard`'s
   `pull_request` trigger so the check always REPORTS, citing *"blocker 2 of owner
   ruling R-P (director board v19b, H-1)"* and warning against re-adding it
   without first removing the check from the required set (the `push` trigger
   keeps its filter, for billed minutes). **And R-U's merge is blocker (a)'s
   repair attempt.** Both are now addressed in code; what remains is a green CI
   run to confirm (a), then the owner's Settings action.
   **The sequencing this lane recommends and nobody
   has ruled on is unchanged: require the four green checks now, add the other
   three the day R-U's lane goes green.** **The flip is the owner's Settings
   action; no lane can perform or verify it, and it is NOT live at this pin**
   (J-3).
2. **🔴 CARRIED AND RE-ISSUED — R-Q's TWO CAPTURE LANES STILL HAVE NOT LAUNCHED,
   AND R-S HAS SENT THEM AGAIN.** Capture-A (MISO, ⬅ **target updated to
   `2026-09-01-miso-198-oomlevel`** after the promotion) and Capture-B (CAISO →
   NYISO), staleness and no-consumer caveats accepted by the owner on R-Q's card
   and **unchanged by R-S**, targeting **6 of 6 bare-ISO stage-0 entries
   current**. At this pin: **no branch, no PR, no commit touching
   `results/regression-goldens/` in 81 commits, and the stage-0 table unchanged
   at 3 current / 3 stale** (J-9, J-11). **Owner/director action is now the
   second-order one: not "confirm the dispatch" — R-S already re-sent it — but
   establish WHY a re-issued dispatch produces no session**, which the roster
   tool's removal has made harder to answer (J-11).
2b. **⚡ POST-PIN: R-U's LANE LAUNCHED AND MERGED (#4564)** — this item is
   DISCHARGED on the lane; what remains is confirming CI actually went green.
   Recorded at the pin as follows, and not rewritten:
   **🔴 R-U's CI-RED REPAIR LANE IS CHARTERED AND HAS NOT LAUNCHED, AND
   TWO G2 LEGS SIT BEHIND IT.** It owns `Pinned default cache key`, `Ruff lint +
   format` and `Structural refactor guards`. **No branch, no PR at this pin**, and
   all three are unchanged on run 2295. ⚠️ **One scoping question for the owner or
   director, recorded rather than answered: `Fast test tier` is a FOURTH job that
   is red-not-by-design, it is NOT in R-U's three, and it is the job G2 leg 2
   actually requires.** Leaving it out leaves leg 2 blocked even on a fully
   successful R-U (J-3).
2c. **🟠 NEW — R-V's PERF-B RESUME IS RULED AND THE LANE HAS NOT LAUNCHED, AND
   THE UN-PARKED GOLDEN TIER IS RED.** Two owner/director actions, distinct: (i)
   **the golden tier is un-parked but unexercised** — no `workflow_dispatch` since
   run #4 on 2026-08-15 — **and its last three scheduled runs failed on content**,
   so un-parking bought a permission whose instrument does not currently work
   (J-6); (ii) **no PERF-B branch or PR exists** and no PERF-B surface moved
   (J-9, J-11). **Until the tier passes, no capture — existing or future — can be
   certified byte-green, and G2 leg 1 cannot close.**
3. **🟢 ~~R-R's G2 UN-PARK SITTING — "CONVENED, NOT HELD"~~ — RETIRED AT v20 BY
   BEING HELD. DO NOT RE-SERVE.** The 2026-09-01 third sitting **is** that room
   and it sat. Its agenda is discharged item by item: **restart-checklist item 1
   material** — golden tier + freeze **decided together** — is **R-V**; **PERF-B
   resume** is **R-V**; **DOCS-B queueing** follows from it; **G2 leg 2** is
   taken up by **R-U**. **G2 was NOT declared**, which was the honest outcome
   given leg 2, and the correction v19b sent into the room (leg 2 is blocked, not
   decision-free) **was accepted rather than argued** — R-U charters the repair
   (J-5). ⚠️ **What the room did NOT settle and what therefore stays on this
   queue as item 1: R-P's flip.**
4. **🟢 ~~Q-1 — THE FOUR UNBLOCKED MAINTENANCE ITEMS~~ — RETIRED AT v19 BY
   EXECUTION (R-J). DO NOT RE-SERVE.** All four merged and verified in the tree,
   commit→PR mapping derived by ancestry: `76c5eed6`/`d5c3178f`/`3f5a24ae`
   (#4495) + `362e2771` (#4502). Restart-checklist items 2, 10, 11 and 12 are
   discharged with it.
5. **🟢 ~~Q-2 — THE `ff-verdicts.json` UNVERIFIABLE PROVENANCE STAMPS~~ —
   RETIRED AT v19 BY EXECUTION (R-M). DO NOT RE-SERVE.** Two verdicts annotated
   **by sha rather than by key**, because the target had moved since the
   dispatch. Re-verified intact at this pin: both stamps still annotated, both
   determinations `HOLD`, `check_forecast_staleness` exit 0 on a reachable anchor.
6. **🟠 CARRIED, HALF-OPEN AND STAYS MISO's — Q-3's SECOND HALF.** The repair
   landed (#4497); **the fields' DOWNSTREAM USE was never audited**, as #4485
   flagged and neither the scan nor the repair opened. Rule 25 `[R-ISO-SCOPE]`
   keeps it MISO's. The rule stands and is now carried in code as well as prose:
   **a nested reserve cascade must be MAXED, never SUMMED**, stated on the
   *provenance* of the number.
7. **🟢 Q-4 — ADOPTED into the refresh protocol**, and executed by this lane for
   the **third** consecutive dispatch: the ruling-label grep (which found
   **R-S/R-T/R-U/R-V at zero**, and confirmed R-A…R-R all resolve) and the
   job-vs-changed-file diff (which found the dispatch's anchor-WARN figure
   unsupported for a third time — J-12). ⬅ **A proposed extension, recorded not
   adopted: Q-4 checks documents and diffs; it has no step that reads a
   WORKFLOW's run list, which is precisely how a red weekly cron went unseen for
   three weeks** (J-6).
8. **⚡ POST-PIN: R-O's SCHEMA LANE LAUNCHED AND MERGED (#4567) — the SCHEMA half
   is done, the CAPTURE half is not.** `check_golden_manifest.py` now resolves an
   `ERCOT__carveout-2023` partition key through the shard's `config_partition`, so
   the carve-out is **representable**; re-derived at `9220243f` it is still
   **UNCOVERED** (6 enforced entries, ERCOT carrying no partition key), and full
   coverage is still **7 captures, not 6**. Recorded at the pin as follows, and
   not rewritten:
   **🟠 R-O's SCHEMA LANE IS CHARTERED, RE-ISSUED UNDER R-S, AND STILL HAS NOT
   LAUNCHED** — across **three** pins now. Config-partition representation in the
   manifest, `live_keeper` partition resolution, then the ERCOT carve-out capture.
   Until it runs, "ERCOT CURRENT" means *forward config only* and full coverage is
   **7 captures, not 6** — and **R-Q's 6-of-6 target does not include it**.
   ⚠️ **R-V's freeze does NOT help here**: ERCOT is frozen, so the carve-out
   config will stay still — but a frozen config with **no golden at all** is not
   protected by stillness, only by capture, and the capture needs the schema
   first.
9. **🟠 NEISO `final` GRANT — DATA-BLOCKED, AND THE BLOCK IS DATED.** Reported by
   the director at this sitting: the 2025 EIA-923 vintage is **still
   early-release, with EIA stating September 2026 for the final**. *(Attribution:
   the director's report, not this lane's measurement.)* The block **lifts itself
   on publication** and needs no ruling — data intake needs no authorization
   (rule 22). Standing and re-verified at this pin: **no ISO has ever spent a
   locked-test year** (60 sidecars walked; {≤2018, 2019, 2026} returns NONE),
   NEISO's one-shot is **NEVER GRANTED, not spent** (D-23), freeze tier-scoped to
   the locked test.
10. **🔵 STANDING, CROSS-DESK VISIBILITY ONLY — the 2020 and 2021 validation
    touchpoints are AUTHORIZED AND WHOLLY UNSPENT.** Verified by walking all 60
    sidecars: **zero registrations, ever, for 2020 or 2021, for any ISO.** All
    three `complete` ISOs may spend them (the freeze is `locked_test`-scoped), and
    **ERCOT has not spent even its 2022**. **The calibration desk's surface;
    recorded here so it is not lost, dispatched by nobody on this board.**
11. **⚪ DORMANT — the ERCOT rule-16 waiver qualifier.** Unchanged, with two
    load-bearing dependants now: ERCOT's `complete` marker rests on the ercot-246
    partition rollup, **and R-O's chartered schema work exists only because of the
    same partition**. **Re-fires only if the carve-out structure changes.**
12. **🟠 CARRIED, DISPOSITION UNCHANGED — the CAISO NOT-YET determination.**
    **TERMINAL REST + MAP** stands (R-3). CAISO's keeper did not move this cycle
    and its determination is unchanged; C3a-2024/2025 still fail at
    **+12.5 % / +15.6 %**. Owner ruling 5 stands: **C3a must genuinely pass.**
    *(Cross-desk note, recorded not adjudicated: the caiso-235 lane closed CAISO's
    import-depth DOF as **not identifiable** on a 2019–2025 regime break. The
    calibration desk's finding; it narrows CAISO's remaining route and this board
    takes no position on it.)*
13. **🟠 CARRIED NOTE — the nyiso-148 2025 dear-gas level card**: no signature or
    decline in any window since; its same-day UPDATE block should be read before
    its numbers (the keeper it names is **six** promotions superseded).
14. **🅿️ NEW, STANDING UNTIL LIFTED — R-V's KEEPER FREEZE ON {ERCOT, NEISO,
    PJM}.** No promotion in those three lanes until **PERF-B's byte-green loop
    completes or the owner lifts it**. **{MISO, CAISO, NYISO} are explicitly
    unfrozen** and promoted freely this cycle (MISO did). **This board does not
    enforce the freeze and no gate script checks it** — `audit_keepers.py` reads
    marker/keeper identity and knows nothing about a promotion embargo, so the
    freeze is **prose-enforced only**. Recorded here, on the board's headline, and
    in `frontend/data/backcast/keepers/README.md`, which is where a promoting lane
    reads its duties. ⚠️ **Not to be confused with `holdout-freeze.json`**, a
    different instrument with a different scope (J-4).
15. **🟢 RETIRED — do not re-serve:**
    - **v20** ~~R-R's *"G2 un-park sitting, CONVENED NOT HELD"*~~ — **HELD at the
      2026-09-01 third sitting**, agenda discharged into R-U and R-V (J-5).
    - **v20** ~~R-T's gate-(a) re-key~~ — **EXECUTED AND SPENT** (#4561), guard
      re-verified `exit 0` here. **Its ROUTING half is not retired — it is
      standing policy** (J-2).
    - **v19b** ~~restart-checklist item 5's *"capture MISO next"* ordering~~ —
      **DISCHARGED BY R-Q**, which authorises MISO together with CAISO and NYISO.
      The item stood through R-L (which went against it as a one-capture
      exception) and is now superseded rather than broken.
    - **v19** ~~Q-1 (four maintenance items)~~ — **EXECUTED, R-J**.
    - **v19** ~~Q-2 (ff-verdicts provenance)~~ — **EXECUTED, R-M**.
    - **v18b** ~~the **nyiso-161 WINTER-FACE WAIVER CARD**~~ — **RULED R-H:
      OPTION A, NOT-YET STANDS.** Retired **for good**. ⚠️ Read the delay as the
      lesson: the ruling existed from 2026-08-31 and reached no artifact until
      v18b, sitting on this queue as *"servable at the next sitting"* through two
      board versions and two independent records lanes.
    - ~~**arm the T1-H storage-entry repair**~~ — **RULED R-A, EXECUTED** (#4442).
    - ~~**the C-1 wind signal-object call**~~ — **RULED R-D: TERMINAL REST + MAP**.
    - ~~**the nyiso-leg2 promote-or-archive item**~~ — **RULED R-G: CLOSED BY
      ARCHIVE**, retired for good.
    - ~~**a PJM determination-integrity card, conditional on Q1 = PHANTOM**~~ —
      **DOES NOT OPEN.** Q1 returned **REAL**. Recorded so the conditional is
      visibly discharged rather than silently dropped.

## Session roster

> **🟠 v19 STATES ITS OWN LIMIT, as v17, v16, v15, v14 and v13 did.** This
> records lane is **not** the director desk and holds no session-listing
> authority, so it did **not** run `list_sessions`. Lane state below is derived
> from **git** (`ls-remote` branch tips, each tip tested for ancestry inside
> `origin/main` rather than read off the listing) plus one **live
> `list_pull_requests`** call at the pin. No row is carried from v17/v18 or from
> the dispatch unverified. ⚠️ **The limit that matters this cycle: it observes
> BRANCHES, not SESSIONS** — an unpushed lane is invisible to it, this lane's own
> included (G-6).

### Lane state at `07472e7c`, derived from remote branch tips + live PR list

⚠️ **AND THE ROSTER'S SECOND LEG IS GONE.** v19/v19b stated *"this lane holds no
session-listing authority, so it did not run `list_sessions`"* as a matter of
scope. At v20 it is a matter of **capability**: **the session-roster tool is no
longer in this desk's tool surface at all.** Lane state below is therefore
**git-only** — `ls-remote` branch tips, each ancestry-tested inside `origin/main`,
plus one live `list_pull_requests`. **A lane that launched and never pushed is
invisible, full stop.**

**ZERO pull requests are open and ZERO branches are ahead of `main`** — the
quietest roster this board has ever recorded. `ls-remote` returns **four** heads;
**all three non-`main` tips test as ancestors of `main`**, i.e. merged remnants.
`list_pull_requests(state=open)` returns **[]**. **The pin was NOT taken under a
forced update** — `f45766e4` is an ancestor, fast-forward, both polls.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v20 (this lane)** | `claude/audit-records-v20-*` | **🟢 WORKING** — the two program record files + the additive `keepers/README.md` note. Cut fresh at `origin/main` so its pack carries only this session's objects. ⚠️ **Unpushed at measurement time — invisible to this board's own non-launch check**, which is exactly the limit that check has, now with no second instrument to cover it |
| **R-Q Capture-A (MISO, target `miso-198-oomlevel`)** | *(none)* | 🔴 **NO BRANCH, NO PR** — and no commit touching `results/regression-goldens/` in 81 commits. **Re-issued by R-S; second issue** (J-1, J-11) |
| **R-Q Capture-B (CAISO → NYISO)** | *(none)* | 🔴 **NO BRANCH, NO PR** — same evidence. **Re-issued by R-S; second issue** |
| **R-O schema lane** | *(none)* | 🔴 **NO BRANCH, NO PR, ACROSS THREE PINS** — chartered at the first sitting, re-issued by R-S, still absent |
| **R-U CI-red repair** | *(none)* | 🔴 **NO BRANCH, NO PR** — first issue, and all three of its jobs are unchanged-red on run 2295 (J-3) |
| **PERF-B resume** | *(none)* | 🔴 **NO BRANCH, NO PR** — first issue under R-V, and no PERF-B surface moved (J-9) |
| **R-T gate-(a) re-key** | `claude/audit-program-director-irzj4a` | 🟢 **SPENT, MERGED, ancestry-tested remnant** — #4561, `f863458a`, **5 changed lines**, one file. The one-push grant is discharged; **the routing half is standing policy** (J-2) |
| **Records v19b (predecessor)** | *(branch gone from the remote)* | **MERGED — #4538.** Same branch mandate as this lane, not a second lane |
| MISO calibration | `claude/miso-mustrun-window-basis-g1tqk1` | **MERGED remnant** (#4557/#4556). The MISO **promotion** came through `claude/miso-st-gas-steam-chp-calibration-9snn32` (#4552), whose branch is already gone. Not this board's work |
| NYISO calibration — 170 | `claude/nyiso-170-merit-order-split-x3sp2w` | **MERGED remnant** (#4535). Not this board's work |

> ⚡ **POST-PIN (`9220243f`): FOUR OF THESE FIVE LANES LAUNCHED WITHIN HOURS.**
> **R-U merged (#4564)** · **R-O merged (#4567)** · **PERF-B** is live on
> `claude/perf-b-apply-nabnpi`, ahead of `main` · **Capture-B** has a branch,
> `claude/stage0-capture-caiso-nyiso-vicx26`, sitting at exactly `9220243f` with
> **zero commits of its own**. **Capture-A (MISO) is the one still absent.** The
> rows above stand as measured at the pin and are not rewritten; see the POST-PIN
> MOTION block at the top of this board.

**The honest reading: the branch check returned FIVE negatives this cycle**, and
each was looked for three ways — as a branch, as a PR, and as a commit touching
the surface the lane was dispatched to change — **and found in none of the
three**. Nothing was assumed launched. ⚠️ **But the check is weaker than it was
at v19b, and the weakening is not cosmetic**: with the roster gone it can no
longer be paired with a session listing, so **"no branch, no PR" is now the
strongest statement available** and must never be written up as "no session was
started." **This lane fails its own test in the same way** — invisible until it
pushes.

*(v17's lane table is recoverable verbatim from this file at `d44446e0`, v16's at
`e52b90a4`, v19's at `72576ebe`, and v19b's at `f45766e4`. The v15 block below is
retained in place because it carries the "⚡ Post-pin" annotations that document
how that cycle's live lanes resolved.)*

### v15's lane state, retained as history (at `69ae4dc7`)

*Derived at the v15 pin from remote branch tips + a live PR list; retained
verbatim as that cycle's record. Every "⚡ Post-pin" annotation below is v15's
own, and every lane it names has since merged.*

**ONE pull request is open and TWO branches are ahead of `main`** (the PR
reading is live, not inferred). **This ends four consecutive cycles of "no
audit-adjacent lane is running"** — v13 and v14 could each report only
completed work.

| Lane | Branch | State at the pin |
|---|---|---|
| **Records v15 (this lane)** | `claude/audit-records-v15-refresh-ob75pb` | **🟢 WORKING** — the two chartered files; branch cut fresh off `origin/main` at the pin. *(Charter named a `claude/director-records-v15-*` branch; the session's designated branch is this one, and the standing branch mandate governs — same lane, same scope, recorded so the name is not read as a second lane.)* |
| **CAISO sub-zonal (caiso-224)** | `claude/caiso-backcast-next-run-5u7ob7` | **🟢 LIVE — +2 ahead, PR #4360 OPEN.** The gated `caiso_fsno_subzonal_topology` (**default off**) + a G-CTRL bit-zero comparator probe against the committed caiso-220 sidecars. The successor to caiso-223 (R-4 route (iii)); its precommit merged as #4357. **⚡ Post-pin: MERGED (#4360) and branch deleted** |
| **ERCOT residual queue (ercot-239 r3)** | `claude/ercot-239-residual-queue-lbkvbf` | **🟢 LIVE — +1 ahead, NO PR YET.** h3068-2024 attributed (event-exit lag) — FINDING + probe + log close + matrix note. Its r2 arc merged this window (#4351 → **#4356 rejected/escalated** → #4359 r3 precommit). **⚡ Post-pin: MERGED (#4361) and branch deleted** |
| **MISO backcast calibration (miso-190)** | `claude/miso-190-backcast-calibration-okt1cn` | Branch exists, **139 commits BEHIND main, nothing unmerged**. The PREREG + gates instrument remain committed (frozen before the mechanism exists). **Registration watch OPEN for a third cycle** — verified by the absence of any `miso-19*` registry sidecar, not by the branch alone |
| ercot-240 demand gap | `claude/ercot-240-demand-gap-xbdwn5` | **MERGED AND BRANCH DELETED** — #4341 (precommit) + #4344/#4345/#4348 (probe, FINDING, log). Chartered and completed the same day (E-2) |
| audit-rulings PM records | `claude/audit-rulings-0830pm-thxtdd` | **MERGED AND BRANCH DELETED** — #4342 (R-1 annotation + R-3/R-4 rulings record) + #4346 (the §8 ledger entry for the sitting, incl. sub-entry (k)) |
| caiso-223 sub-zonal scope | `claude/caiso-223-subzonal-scope-x5egla` | **MERGED AND BRANCH DELETED** — #4347 (precommit) + #4350 (partition + membership + LDF 13/13 + FINDING). Superseded by caiso-224 above |
| nyiso-158 winter-face phase-0 | `claude/nyiso-seam-diagnosis-phase0-sl2opv` | **MERGED AND BRANCH DELETED** — #4339 |
| nyiso-159 zonal loss surface | `claude/nyiso-zonal-loss-surface-b3zm2r` | **MERGED AND BRANCH DELETED** — #4352 (phase-0 + PREREG) |
| ercot-241 conduct screen | `claude/ercot-241-conduct-param-adpfmm`, `claude/ercot-241-backcast-8horad` | **MERGED, BOTH BRANCHES DELETED** — #4349 (precommit) + #4358 (phase-0 measured; Phase-1 gate OPEN) |
| Records v14 (predecessor) | `claude/director-records-v14-ledger-lhywlm` | **MERGED AND BRANCH DELETED** — #4338, the post-pin addendum at `def338e` |
| capx lanes — **A DIFFERENT PROGRAM** | `claude/capx-*`, `claude/q5w-nyiso-marker-withdrawal-5yzj0s` | #4336, #4337, #4340, **#4343**, #4353, #4354, #4355 — the capx expansion desk. **Not this board's work**, per the standing conflation warning. **#4343 is recorded on this board only because it wrote the shared marker file** (E-5), and **#4355 only because its engine change moved two of this board's gate readings** (Gates) |

**The honest reading: the branch check did its job in both directions again.**
Every lane this cycle's PRs imply was found as a branch or as a deleted branch
with merged PRs behind it; **nothing was assumed launched without one**; and
the two live lanes were found by ancestry testing, **not** by reading the
`ls-remote` listing (which shows `main` itself as a row and would have been
misread). The capx branches remain the exact class of plausible-sounding
commits that would fool a commit-list scan — this cycle they merged **seven**
PRs, two of which genuinely touched this program's surfaces and five of which
did not.


## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** The director session pushes
nothing itself, by standing owner instruction (*"issue prompts, I don't want you
doing it from here"*). **A refresh is not complete until that lane has landed
both files.**

**⚠️ THE DEVIATION HAS NOW BEEN SUPERSEDED THREE TIMES, EACH TIME FOR ONE
SITTING OR ONE PUSH, AND IS BACK IN FORCE.** The 2026-08-30 decision-card sitting
executed its own records duties in-session under an explicit one-sitting
supersession (v16 F-10); the 2026-09-01 **second** sitting granted a **one-push
micro-supersession**, ruling **R-N**, spent as **#4523** (5 lines, the CAISO
gate-(a) re-key — G-5); and the 2026-09-01 **third** sitting granted another,
ruling **R-T**, spent as ⬅ **#4561** (5 lines, the MISO gate-(a) re-key — J-2).
**All three are spent and none carries forward.** The standing deviation governs,
this lane is its dispatched instrument, and a future sitting that wants to write
directly needs its own supersession.

⚠️ **A PATTERN WORTH NAMING, since it is now three-for-three: every
micro-supersession this program has granted has been a FIVE-LINE gate-(a) stamp
re-key.** That is not a coincidence — it is the shape of a defect the standing
deviation's round-trip is too slow for. **R-T's routing half is the structural
answer** (the promoting PR carries the re-key, so no supersession is needed at
all), and if it works, **the fourth micro-supersession should never be
requested** (J-2). ⬅ **R-S separately confirms the deviation's OTHER half is
unchanged**: R-L's *"a capture lane registers nothing on the dashboard"* stands,
re-issued with the prompts and not amended (J-1).

**🔴 A THIRD MANDATORY STEP, ADOPTED AT v22 (2026-09-02) BY DIRECTOR INSTRUCTION —
THE DURABLE LESSON OF THE LEG-2 ERROR:**

> ### **A DISPATCH MAY NOT UPGRADE A LANE'S OWN CLAIM.**
> **When a records instruction asserts more than the finding it cites asserts,
> the finding governs and the instruction is refused on measurement.** The v21
> dispatch compressed R-U's *"7 of 7 **required** checks green"* into *"THE GREEN
> COMPLETED RUN … G2 LEG 2 SATISFIED"* — a claim **the lane that did the work
> explicitly declined to make**, in terms: *"The run is not 'fully green' and this
> finding does not claim it is."* v21 refused it; **the correction STANDS, and
> R-U's credit stands at full weight** (reinforced at v22/L-2, where its charter
> completes). **This is the error class to check for first**, because it is the
> one that arrives pre-authorised: a records lane inherits it from its own
> instruction, and nothing downstream will catch it. **Test: for every claim the
> dispatch makes, open the cited artifact and check the artifact says it.**
> *(Ran at v22 and yielded three: the leg-2 claim itself, the PERF-B
> "three items unadjudicated" premise (L-7 — all four are CLOSED), and the
> stage-0 "6 current" count in Capture-A's own finding (L-5 — it is 7).)*

**⚠️ AND A METHOD CLAUSE, ADOPTED AT v22 — G-13 EXTENDED.** Before reporting any
absence from git: check `--is-shallow-repository`; un-shallow with
`git fetch --filter=tree:0 --unshallow` (~3 s); **then run every reachability
probe as `git rev-parse --verify <sha>^{commit}` + `git merge-base
--is-ancestor` under `GIT_NO_LAZY_FETCH=1`, and confirm anything still absent
against the remote API.** The un-shallow makes the clone **partial**, and a bare
probe in a partial clone **lazily fetches the object it is testing for** — so the
second reading of the same sha silently contradicts the first (L-9). **Four
containers in four sittings have now hit some layer of this.**

**🟢 Q-4 IS ADOPTED (2026-09-01). Two steps are now MANDATORY before a records
lane closes**, and both ran here for the **fourth** consecutive dispatch
(v22: label sweep **R-A … R-W** — every label A–V returns ≥1, **R-W returns 0**
and is recorded as non-launch #5, L-3; job-vs-changed-file diff run at close
below):

- **(i) `grep` EVERY ruling label of the sitting across `docs/`.** Not the ones
  the dispatch highlights — every one, **A through the current letter**. Run at
  v20 across **R-A … R-V**: it returned **ZERO for R-S, R-T, R-U and R-V** (the
  four this lane records) and **at least one artifact for every one of R-A
  through R-R**, so no earlier ruling has silently fallen off the record. It is
  the instrument that caught R-H and the two-sitting R-J…R-O gap, and it is
  mechanical, cheap and unmissable.
- **(ii) Diff EVERY dispatched job against a CHANGED TARGET FILE.** *A finding
  that describes a repair is not the repair.* Run at close for this lane:

  | job | changed target file at close |
  |---|---|
  | 1 · board v20 **FULL** refresh | `docs/handoffs/audit-program-director-board-2026-08.md` — headline block, snapshot, keeper table, markers, rollup, stage-0, both Gates tables, G2 legs, Watch, forecast board, queue, roster, checklist ✅ |
  | 2 · record R-S…R-V in board + plan §8 + the README note | same file (J-1…J-4) + `docs/model-audit-release-plan-2026-08.md` §8 + `frontend/data/backcast/keepers/README.md` ✅ |
  | 3 · dispatch-vs-launch on all six | board, roster + J-11 ✅ |
  | 4 · workstream rollup re-estimate | board, Workstream rollup — **WS3 label changed, number deliberately HELD** ✅ (J-9) |
  | 5 · completeness (Q-4 (i)) + this diff | this table ✅ |

  **⬅ v22's run of step (ii), at `dfc44d95`:**

  | job | changed target file at close |
  |---|---|
  | 1 · record Capture-A landing + stage-0 7/7 | board L-5 + headline block ✅ (with the finding's own count corrected) |
  | 2 · record PERF-B session close + hand-back | board L-7/L-8 + queue **W-4** ✅ (charter premise re-derived: all four CLOSED) |
  | 3 · leg-2 correction as governance record + durable lesson | board L-14 + **Refresh protocol** (new mandatory step) ✅ |
  | 4 · R-W dispatch-vs-launch + flip/tier re-measure | board L-3 / L-6 / L-15 + queue **W-1**, **W-2** ✅ |
  | 5 · gates, keeper motion, four-instrument alignment | board L-11 / L-12 / L-13, Gates + Stage-0 pointers ✅ |
  | 6 · G2 roll-call as corrected | board L-15 ✅ |
  | 7 · completeness (Q-4 (i), R-A…R-W) + this diff | this table ✅ |

  ⬅ **v22's instances of the "job came back different" class — THREE, and one of
  them is the dispatch's own leg-2 premise**: (a) the PERF-B charter question
  presumed three items unadjudicated; **all four are CLOSED** (L-7); (b) the
  stage-0 landing was reported as 6-of-7 by Capture-A's own finding; **the gate
  says 7** (L-5); (c) the run this lane was sent to re-check (2298) **was not the
  newest** — run 2307 exists and is 52 minutes newer (L-1). **Also: the pin
  itself moved** — `a5abe3fe` → `dfc44d95` before the first poll.

  ⬅ **v20's own instance of the "job came back different" class**: the dispatch's
  *"243 anchor WARNs GONE, repaired by `f5b33644`"* diffs against **no defect at
  all** — the count was 236, it existed only inside PR #4531's branch, and `main`
  never held it (J-12). **Third consecutive dispatch to carry an unsupported
  anchor-WARN figure.**
- ⬅ **🆕 PROPOSED EXTENSION (recorded, NOT adopted — the director's call):
  (iii) LIST THE RUNS OF EVERY WORKFLOW THIS BOARD MAKES A CLAIM ABOUT.** Q-4's
  two steps read *documents* and *diffs*. Neither reads **what CI actually ran**,
  and that gap let a weekly `schedule` run fail red for three consecutive weeks
  under a board line reading *"CI proof deliberately unspent"* (J-6). One API
  call per workflow. **The failure was not a wrong number; it was a state nobody
  re-measured — which is precisely the class Q-4 exists to catch.**

  ⬅ **v22 RAN (iii) UNPROMPTED, AND IT YIELDED TWICE — RECOMMEND ADOPTION.**
  Two API calls (`golden-data-tier.yml`, `ci.yml`) produced: **(1)** the tier is
  not merely unexercised but **red on all three of its scheduled runs, the
  newest post-dating R-V's un-park** (L-6) — the exact J-6 class, recurring;
  and **(2)** the run the dispatch cited was **not the newest** — run 2307 is
  52 min newer than 2298 and carries a materially better R-U result (L-1, L-2).
  **Neither was reachable from documents or diffs.** Cost: two calls.

- **And the rider stands: a parallel lane is NOT a completeness check.**
  Redundancy catches *measurement* error, because two lanes measure
  independently; it does **not** catch a *scope* omission, because both inherit
  the scope from one dispatch. Two lanes both omitted R-H; that is the proof.

**v20's protocol record — an un-park cycle, and two instruments that got weaker:**

- **🔴 A "STATE" RECORDED ONCE AND NEVER RE-MEASURED IS A CARRIED FIGURE WEARING
  A DIFFERENT COSTUME.** The golden tier's park was written down in 2026-08-22
  and re-published verbatim for seven cycles — *"CI proof deliberately unspent"* —
  while a cron ran it weekly and it failed three weeks running (J-6). **This
  board's discipline of re-deriving every FIGURE had no counterpart for every
  STATE.** The protocol's re-derivation duty is hereby read as covering both:
  **park, pause, freeze, grant, block — each is a claim, and each needs a source
  re-read at the pin, not a sentence copied forward.**
- **🔴 AN INSTRUMENT CAN DEGRADE BETWEEN CYCLES, AND THE BOARD MUST SAY SO
  RATHER THAN REPORT AT THE OLD CONFIDENCE.** v19/v19b's dispatch-vs-launch check
  had two legs, git and the session roster, and stated the roster as a *scope*
  limit. **At v20 the roster tool is simply gone from this desk's surface**, so
  the check is git-only and strictly weaker. **The right response is to weaken
  the CLAIM, not to keep the phrasing**: every non-launch here reads *"no branch
  and no PR at this pin"*, never *"never launched"* (J-11). **A number carried at
  a confidence its instrument no longer supports is worse than no number.**
- **🟢 RECORD A RULING'S EXECUTED HALF AND ITS DURABLE HALF SEPARATELY, AND LEAD
  WITH THE DURABLE ONE.** R-T is a 5-line stamp re-key **and** a permanent
  routing change. The 5 lines are spent and interesting to nobody next week; the
  routing removes a **defect class** that has now cost three separate repairs
  (v17's four stale stamps, R-N, R-T). **A records lane that logs only what was
  pushed would have recorded the forgettable half** (J-2).
- **🟢 A DISCHARGED CHECKLIST ITEM IS NOT A SOLVED PROBLEM — SAY WHAT THE
  DISCHARGE DID *NOT* BUY.** R-V decided restart-checklist item 1 exactly as
  asked, and the item retires. But un-parking revealed a **red tier** behind the
  permission barrier, the freeze **does nothing for the three stale rows**, and
  the freeze is **prose-enforced only**. **Retiring the item without those three
  riders would have read as progress the program did not make** (J-4, J-6).
- **🔴 PIN ONCE, THEN RECORD MOTION — held.** `origin/main` was stable across two
  polls and the fetch was **not** a forced update (`f45766e4` an ancestor). The
  director's two derivation pins were **10** and **5** commits stale by the time
  this lane ran.
- **🆕 RE-CONFIRMED FOR A THIRD TIME — THE DISPATCH'S OWN FIGURES DO NOT
  RE-ESTABLISH THEMSELVES.** The anchor-WARN figure has now been carried and
  corrected across three consecutive dispatches, each time in a *different* way
  (already-repaired at v19, no-op at v19b, **never-existed** at v20 — J-12).
  **The cheapest figure on the board is the one that has been wrong the most.**

**v19b's protocol record — the third dispatch of the same lane, and the
non-launch count reaching six:**

- **🔴 THE DISPATCH-VS-LAUNCH CHECK HAS NOW FOUND SIX NON-LAUNCHES FROM ONE
  SITTING, AND TWO OF THEM WERE THIS LANE'S OWN DISPATCHES.** Recorded at the
  director's explicit instruction, for the second time and in full:
  **(a)** the **original v19 records dispatch never launched** — no branch, no
  session, confirmed from git and the session roster; **(b)** the **first
  re-issue never launched either**, on the same evidence; **(c)** this is the
  **third dispatch**, and the second to actually run (the second re-issue landed
  v19 as #4533). **(d)** R-L's capture lane's first dispatch never launched,
  recorded in its own finding. **(e)** R-O's schema lane — unlaunched across two
  pins. **(f)+(g)** R-Q's Capture-A and Capture-B — unlaunched (H-3).
  **The step costs one `ls-remote` plus one live PR list, and it is the only
  instrument on this program that has ever caught any of these.**
- **🆕 ADDED — DISTINGUISH A GATE *SCRIPT* FROM A CI *JOB* BEFORE QUOTING
  "GREEN".** R-P's amendment rests on *"7 gates holding green"*, which is true of
  the seven **audit-program scripts** and false of the ten **`ci.yml` jobs**, three
  of which are red and are in R-P's own required list (H-1). **This board's Gates
  table was the likely source of the conflation**, so it now publishes both sets
  side by side. **When a ruling cites this board's numbers back at it, check which
  object the number is about.**
- **🆕 ADDED — A RULING CAN BE RECORDED FAITHFULLY *AND* CARRY ITS OWN
  COUNTER-EVIDENCE.** R-P was executed as ruled — the memo refresh is written,
  the check names verified, the naming caveat recorded — **and the two blockers
  are attached to it rather than resolved by silently editing the list.** A
  records lane does not overrule an owner amendment; it also does not launder one
  past evidence the owner did not have. **Write it as ruled; attach what the
  ruling could not see; leave the decision where it belongs.**
- **🆕 ADDED — RE-DERIVE EVEN A SIX-COMMIT-OLD BOARD.** v19's tables were six
  commits and one PR old, and carrying them would have been defensible. Re-derived
  instead: **every figure agreed except one** (staleness Δ 0 → 2), which is what
  makes the agreement worth something (H-4). **A board that has not been
  re-derived is not known to be current, however recent it is.**
- **🔴 PIN ONCE, THEN RECORD MOTION — held again.** `origin/main` was stable
  across two polls; the fetch was **not** a forced update. The dispatch's two
  derivation pins were **stale by 20 and 11 commits**, and the v19 pin itself by
  6 commits / 1 PR.
- **🆕 RE-CONFIRMED — THE DISPATCH'S OWN FIGURES, RE-DERIVED A SECOND TIME.** The
  third dispatch re-asserted four v19-cycle figures this board had already
  corrected; **all four corrections stand** at the new pin (H-5), including job
  4's anchors, which are a no-op for the second consecutive dispatch. **A
  dispatch repeating a figure does not re-establish it.**
**v19's protocol record:**

- **🔴 THE DISPATCH-VS-LAUNCH CHECK PRODUCED FOUR NON-LAUNCHES IN ONE SITTING,
  AND TWO OF THEM WERE THIS LANE.** Recorded at the director's explicit
  instruction. **(a)** The original v19 records dispatch **never launched** — no
  branch, no session, confirmed from git and the session roster. **(b)** The
  **first re-issue of the same dispatch also never launched**, on the same
  evidence; the records debt therefore stood **two sittings deep**, and this is
  the **third** dispatch and the first to run. **(c)** R-L's capture lane's first
  dispatch never launched, recorded in its own finding. **(d)** **R-O's chartered
  schema lane has not launched at this pin** (G-6). **The step's yield is now the
  highest of any in this protocol**, and it costs one `ls-remote` plus one PR
  list. ⚠️ **State its limit honestly**: it observes *branches*, not *sessions* —
  this lane's own branch was unpushed at measurement time and would have failed
  its own test.
- **🆕 ADDED — RE-DERIVE A DISPATCHED JOB'S *PRECONDITION*, NOT ONLY ITS
  FIGURES.** v15: re-derive the table that cannot have changed. v16: re-derive
  the reading that improved. **v19: re-derive that the job still needs doing.**
  **Two of this lane's six jobs came back already-discharged or moved** — job 4's
  anchors were repaired by an unrelated lane between dispatch and pin (G-8), and
  R-M's target verdict was re-scored onto a healthy sha so the defect **migrated
  to a different key** (G-4). Executing either blind produces a *false record*:
  an empty commit claiming a repair, or an annotation on the wrong verdict. **A
  dispatch describes the world at derivation time; the pin is the world.**
- **🆕 ADDED — CHECK `--is-shallow-repository` BEFORE REPORTING ANY ABSENCE FROM
  GIT.** Third instance in this program, and it has now cost a published reading
  (G-13). A shallow clone's `git cat-file` miss is **indistinguishable from a sha
  that never existed**: here it reported 8 of 13 forecast provenance shas
  unreachable when the true count is **2**, and it is what produced v17's wrong
  `af1ccb6` claim. Either `git fetch --filter=tree:0 --unshallow` (~2 s) or
  confirm against the remote API. **Before reporting an absence from git,
  establish that the repository could have shown you the thing.**
- **🆕 ADDED — COUNT THE GATES FROM `ci.yml`, NOT FROM THE LAST BOARD.** The
  roster said five for four cycles, the dispatch said six; **seven is correct**
  (G-7). `check_golden_manifest.py` had been enforced at `ci.yml:118` the entire
  time and was simply never counted — and it is the instrument that *owns* the
  stage-0 table this board recomputes by hand every cycle. **Re-read the
  workflow, not the predecessor's list.**
- **🔴 PIN ONCE, THEN RECORD MOTION — held again, in both directions.**
  `origin/main` was stable across two polling rounds before the pin, and the
  fetch was **not** a forced update. The director's own two pins were **7** and
  **4** merged PRs stale by the time this lane ran, and **`main` moved past the
  pin again while this board was being written** (`663605c58e` at close). **The
  pin was not moved**; the delta is recorded in the roster.
- **🆕 SHARPENED — A BRANCH NAME IS NOT A LANE, AND THE DANGEROUS DIRECTION IS
  THE REVERSE ONE.** v17 found capx branches wearing calibration names. This
  cycle **`market-sim-calibration-director` IS the capx director's desk** and
  **`neiso-rc-repair` is a forecast hindcast lane** — 6 of that desk's 28 PRs.
  **Worse in this direction**, because a calibration-shaped name filed into the
  calibration column looks correct and raises no flag. **Classify from commit
  subjects AND touched paths, both, every cycle.**
- **Carried from v16/v17 and still live:** re-derive the reading that *improved*
  (the bench gate's WARN count *rose* this cycle and that is the repaired
  instrument, not a regression); read a restructured file's schema before its
  values (the stage-0 manifest went v1 → v2 this window — a field-set assumption
  would have read it as gutted rather than as fixed).

**Carried, restated in one line each** (full text in v10–v17): run the gates,
never quote them (exit codes captured directly, not through a pipe) · quote no
cycle count without its base sha, in the dispatch and on the board · trust no
table, including the dispatch's — re-derive from committed bytes at the pin ·
**look for the BRANCH, not a plausible-sounding commit**, and then check the
branch's *commits and paths* · a refresh is complete when the sessions exist, not
when the prompts are written · read a content-addressed identity before inferring
· **confirm `frontend/data/hindcast/` is present before quoting any
stamped/scored count** (done this cycle: *board inputs: all present*) · **say
which figures are derived and which are carried** — this board's stage-0
promotion-gap absolutes remain the current instance, labelled rather than
re-asserted.

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh confirms (a) whether the owner has ruled on anything
in the queue — **the 2026-08-31 sitting's nine rulings and the 2026-09-01
sitting's six are now ALL on the record: R-A/R-B/R-C merged before v17,
R-D/R-E/R-F/R-G at v17, R-I at the v18 delta, R-H at v18b, and R-J through R-O at
v19**; (b) whether the keeper freeze has been called — **still deferred, and this
cycle cuts back toward v16: two captures were taken with no freeze at all, and
the question is down to three stale rows**; and (c) whether the golden tier's
park has been lifted — **unchanged, and the CI proof stays deliberately unspent,
which is why none of the three CURRENT captures can be certified byte-green**.

**🟢 AND THE FOURTH THING EVERY RECORDS LANE MUST CONFIRM ABOUT ITSELF — that it
recorded every ruling of the sitting — IS NO LONGER A PROPOSAL. It is Q-4,
adopted, and it is step (i) above.** D-5(a) named *"landed but incomplete"*; the
lane that named it omitted R-H, and so did a second lane on the same dispatch.
**This cycle the same shape recurred at five times the scale — five rulings
unrecorded across two sittings — and the adopted grep is what found them.**

## RESTART CHECKLIST — ⬅ **THE PROGRAM IS UN-PARKED (R-V); THIS IS NOW THE RESUME CHECKLIST**

**Do these in order. Do not start at change (a).** ⬅ **Its top item is
DISCHARGED** — R-V decided the golden tier and the freeze together, exactly as
item 1 required (J-4). **That does not shorten the list**: the discharge revealed
a **red golden tier** behind the permission it removed (item 9, now the binding
step), and items 3–5, 7, 9b and 13 are all still work. **Whoever resumes starts
here, not at change (a).**

0. **🔴 ⬅ CORRECTED AT v21: SIX OF SEVEN EXIT 0 — `check_registry_payload_parity.py`
   IS EXIT 1 at `0653bf13`** on `results/calibration/miso200_control_A`, a bundle
   **committed to `main`** (#4591) with no sidecar. It is the calibration desk's
   in-flight A/B control leg — **not this program's to fix** — but it is a
   `pull_request` job, **so it reddens every PR until the desk registers, prunes
   or allowlists it** (K-8). Re-run all seven yourself; the v20 line below is the
   historical reading.
0a. **🟢 ALL SEVEN GATE SCRIPTS EXIT 0 AT THE v20 PIN `07472e7c` — but ⚠️ THAT
   IS NOT THE SAME STATEMENT AS "`main` IS GREEN".** *(Corrected at v19b: this
   item said "main is fully green" for five cycles.)* The **seven gate scripts**
   are green; the **`ci.yml` job set is 4 green / 6 red**, four of the six being
   unowned engine defects (`Ruff lint + format`, `Pinned default cache key`,
   `Structural refactor guards`, `Fast test tier`) and only two red **by design**
   — **unchanged in every cell across 29 merged PRs**, and now **R-U's charter**.
   **Read the Gates section's second table before quoting this line**, and never
   cite "seven gates green" as evidence about CI (J-3).
   **The seven scripts, re-run at `07472e7c`, each invoked alone with `$?` read
   directly and NEVER through a pipe** (the roster is **seven**, not the *five*
   this item carried for four cycles):
   `audit_keepers.py` **PASS 0/0** (over `complete` = {ERCOT, NEISO, PJM}) ·
   `check_registry_payload_parity.py` **exit 0** (60 runs / 95 dirs / 0
   tolerated) · `check_mechanism_matrix.py` **exit 0** (194 field + 49 row +
   ⬅ **159** path anchors, **0 WARNs**; `--fix-anchors` repairs **0**) ·
   `check_forecast_staleness.py` **exit 0, ⬅ Δ = 0/10** (the undated-stamp WARN
   persists at ⬅ **25 of 56**) ·
   `check_bench_freshness.py` **exit 0, 0 STALE of 20 — 20 of 20 with engine
   drift**, the repaired instrument's honest reading ·
   `check_gate_a_provenance.py` **exit 0** (`ci.yml:213`, **hard**, 6 rows) —
   ⬅ **the one gate that changed state this window, exit 1 → 0 via #4561** ·
   `check_golden_manifest.py` **exit 0** (`ci.yml:118`; it is the stage-0 table's
   instrument, and it tracked MISO's promotion unprompted). Green for a sixth
   consecutive cycle. **Always re-run all seven rather than reading this line**,
   and **count them from `ci.yml`, not from this list** — at this repo's merge
   cadence (29 PRs in this window) the reading ages in minutes.
0c. **🔴 ⬅ NEW AT v20 — AND CHECK THE WORKFLOW RUN LISTS, NOT JUST THE SCRIPTS.**
   Neither the seven scripts nor Q-4's greps look at what CI **actually ran**.
   That blind spot let the **golden data tier fail on a weekly `schedule`
   trigger for three consecutive weeks** (runs #5/#6/#7, 2026-08-17 / 08-24 /
   08-31, all RED on `main`) while this board recorded its CI proof as
   *"deliberately unspent"* (J-6). **Before trusting any "parked", "unspent" or
   "green" claim about a workflow, list its runs.** One call, and it would have
   caught this five cycles ago.
0b. **🟢 THE GOLDEN PROVENANCE PROBLEM IS FIXED — DO NOT RE-DO IT.** The
   condition this item described for four cycles (one top-level `git_sha` for six
   captures; five provenance runs pruned; `af1ccb6` believed unresolvable) is
   **closed by R-J** (#4502). The manifest is **schema v2**: `provenance` +
   `keeper_snapshot` **per entry**, no shared top-level sha, all six historical
   shas recovered from history **with evidence and zero UNKNOWN rows**, and
   retention reconciled on the manifest side so a prune costs nothing. **Two of
   this board's own former claims were overturned in the process**: `af1ccb6`
   **does** resolve (it is the CAISO capture commit) and the five shas were
   recoverable all along — the "does not resolve" reading was a **shallow-clone
   artefact** (G-13). The per-file `content_hashes` are unaffected and remain a
   sound verification instrument; they are no longer the only one.
1. **🟢 ~~DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER~~ — DECIDED. RULING R-V,
   2026-09-01. THIS ITEM IS DISCHARGED AND MUST NOT BE RE-SERVED.** It stood at
   the top of this checklist from v13 to v19b, and it was decided **exactly the
   way the checklist asked** — both together, in one ruling: **the golden tier is
   UN-PARKED**, **PERF-B is RESUMED**, and **a keeper freeze is declared on
   {ERCOT, NEISO, PJM}** with {MISO, CAISO, NYISO} explicitly unfrozen (J-4).
   ⚠️ **THREE THINGS THE DISCHARGE DOES NOT BUY, each of which is the next
   person's actual work:**
   (a) 🔴 **The un-parked tier is RED.** Its last three scheduled runs failed on
   content, and it has **not been `workflow_dispatch`-ed since 2026-08-15**
   (J-6). **Un-parking removed the permission barrier and revealed a defect
   barrier behind it.** Nothing can be certified byte-green until the tier
   passes.
   (b) 🟠 **The freeze protects the three goldens that exist; it does nothing
   for the three that are stale.** Those need **captures**, not stillness — and
   the standing demonstration is that **a capture never needed a freeze anyway**
   (Card 1 took one, R-L took two, both inside busy windows).
   (c) 🔴 **The freeze is PROSE-ENFORCED ONLY.** No gate script checks it:
   `audit_keepers.py` reads marker/keeper identity and knows nothing about a
   promotion embargo. It is recorded on the board headline, in the queue, and in
   `frontend/data/backcast/keepers/README.md` — and that is the whole
   enforcement.
2. **🟢 ~~RECORD PROVENANCE PER ENTRY~~ — DONE (R-J, #4502).** Verified in the
   manifest at the pin. **Do not re-do it**; verify existing captures against
   their `content_hashes` and their own per-entry `provenance`.
3. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. **Do not trust this board's staleness table — and you no
   longer have to hand-recompute it**: run `check_golden_manifest.py`, which maps
   each entry back through its own `keeper_id` and reports CURRENT / STALE and
   pruned-provenance status directly. **At `07472e7c` the answer is unchanged in
   shape: PJM, NEISO and ERCOT-forward CURRENT; CAISO, MISO and NYISO STALE (all
   three with a PRUNED provenance run, survivable via `keeper_snapshot`); and
   ERCOT's 2023 carve-out UNCOVERED and not capturable at this schema.** ⬅ **What
   DID change: MISO's stale line now names `2026-09-01-miso-198-oomlevel`**, three
   promotions past capture and the board's deepest single row. **The gate tracked
   the promotion unprompted — which is the reason to run it rather than read this
   line.**
4. **Assume every re-capture is a real solve — and budget the memory.** 🆕
   **R-L's capture lane re-measured this and the picture is container-dependent,
   not fixed.** Card 1's PJM capture died on a **13.3 GiB cgroup memcg** at
   13.9 GB RSS and needed a 12 GB swapfile; R-L's container reported an
   effectively **unbounded** `memory.max`, so the binding constraint was physical
   RAM: ERCOT peaked at **12.50 GB** against 15 GB and **never paged** (swap
   usage 0), NEISO at **3.94 GB**. **Budget for ~12.5 GB on ERCOT and check
   `memory.max` rather than assuming Card 1's limit.** Also: R-L's container had
   **no Python dependencies at all** and needed a venv built from the pinned
   `requirements.txt`; hydration was a no-op on its full clone and **no
   converted-corpus re-fetch was required** (unlike PJM's `pjm-da-virtuals`).
   The **re-stamp-not-re-solve** shortcut is still established for **neiso-97
   only** — re-establish before relying on it.
5. **~~Capture PJM FIRST~~ — DONE (#4369). ~~Capture MISO next~~ — ⬅ **THIS
   ITEM'S ORDERING IS DISCHARGED BY R-Q** (H-2), which authorises **MISO, CAISO
   and NYISO together** via two dispatched capture lanes, superseding the
   one-at-a-time sequence rather than breaking it. ⚠️ ⬅ **Neither lane shows a
   branch or a PR at a SECOND pin** (J-11), and **R-S has re-issued both** with
   Capture-A's target updated to `2026-09-01-miso-198-oomlevel` (J-1) — so the
   work the item names is still undone, the *ordering* is discharged, the
   *captures* are not, and the target ids have moved under them once already.
   **Re-read the live keeper before capturing; do not take a target id off a
   dispatch.** Historical note, retained:** R-L took
   NEISO and ERCOT against this item by owner ruling, as a one-capture exception,
   and the item stood through it. R-L's
   verbatim *"Just NEISO and ERCOT"* was **deliberately against this item**, for
   that capture only; it was an exception, **not an amendment** (G-3) — and R-Q has
   since amended the ordering outright. MISO's own case is unchanged and is now
   one of three: joint-deepest gap on the board at two promotions past capture.
   **ERCOT still needs a second capture** — its 2023 carve-out — and that one is
   **outside R-Q's scope entirely**, blocked on **R-O's schema lane**, not on a
   freeze and not on a capture slot (G-6, H-2).
6. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at
   HEAD. Verify the blob (`af34031c`) rather than re-porting it.
7. **Close the #4054 residual if you want belt-and-braces — but re-derive it, do
   not inherit it.** The NYISO keeper is **eleven** promotions past the captured
   nyiso-140 config; MISO is v15's eleven + one.
8. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures. **Three
   CURRENT captures still do not close leg 1.**
9. **🔴 CONFIRM THE GOLDEN TIER IS GREEN IN CI BEFORE CLAIMING ANY BYTE-GREEN
   RESULT — AND AT v20 THIS IS THE BINDING STEP, NOT A FORMALITY.** ⬅ **The
   un-parking (step 1 / R-V) is DONE; the tier is RED.** Its last three
   `schedule` runs — #5 (2026-08-17), #6 (08-24), #7 (08-31) — **all failed**, and
   run #7 provisioned `data/clean` and emissions **green** before failing at
   `Data-provisioned pytest tier (serial)`: a **content** failure in the tier's
   own tests, **not** the provisioning/OOM class #4071 fixed, so **the local
   four-step replay does not cover it** (J-6). A local replay was never the gate
   and is even less one now. **This applies to all three CURRENT captures, and it
   is what blocks G2 leg 1 — a defect to fix, not a permission to obtain.**
9b. **KEEP THE SITTING-HANDOFF QUESTION — still the highest-yield step here, and
   the instrument behind it is now WEAKER.** *Did the last sitting's records
   duties get dispatched, or did the session end holding them — and if they were
   dispatched, did the lane LAUNCH?* **The 2026-09-01 sittings have now produced
   NINE dispatches with no session** (five still outstanding at this pin — J-11).
   ⚠️ ⬅ **The check is GIT-ONLY as of v20**: the session-roster tool is no longer
   in this desk's surface, so `ls-remote` + one live PR list is the whole
   instrument. It establishes **"no branch, no PR"** and nothing stronger — an
   unpushed lane, a lane that died before its first push, and a lane that was
   never dispatched are **mutually indistinguishable**. **Write the weaker claim.**
10. **🟢 ~~FIX THE PARITY GATE'S CLASSIFIER~~ — DONE (R-J, #4495).** The
    class-level carve-out (B-8) **exists**: a two-conjunct structural test admits
    pre-registered campaign points and replay recipe dirs, and the residual
    enumeration is **8**, down from **40** (the board's last count of 26 was
    itself 14 stale). **The gate's green is now closer to a property than the
    maintenance state it was.** The standing reading discipline survives: before
    reporting a parity red, check whether the named dirs belong to a **live**
    lane — this cycle a red on `caiso231_a0_control` resolved transiently when
    that lane's own registrations landed, and no fix was needed.
11. **🟢 ~~RECONCILE RETENTION WITH THE GOLDEN MANIFEST~~ — DONE (R-J, #4502),
    AND DONE THE WAY E-7 REQUIRED.** Each entry carries a `keeper_snapshot`
    copied from its provenance run's sidecar, so a top-15 prune costs nothing.
    **Fixed on the manifest side, NOT by exempting golden runs from retention** —
    the dead-bundle class E-7 warned about was never created. Three of six
    entries currently have a pruned provenance run and the gate reports it as
    **information, not failure**.
12. **🟢 ~~CHECK THE BENCH GATE'S DRIFT ARITHMETIC~~ — DONE (R-J, #4495).** The
    `%ad`-vs-`--since` **date-kind mismatch** and the day-granularity artefact are
    fixed at source: both sides now use the **committer instant in offset-bearing
    form**, with `--since`'s inclusivity verified rather than assumed. **So the
    reading is trustworthy now, and it reads 20 of 20 with engine drift at 6
    engine commits — a true statement, not the artefact it used to be.** The
    substantive discipline survives unchanged: **0 STALE is the reading that
    matters**, engine drift is ungated by design, and a *marginal* C1 verdict
    still deserves a bench regeneration first.
13. **🆕 RUN R-O's SCHEMA LANE BEFORE CLAIMING FULL ERCOT COVERAGE.** The
    manifest keys `keepers` one entry per ISO, so ERCOT's two-config partition
    **cannot be represented** and its 2023 carve-out golden cannot be taken at
    all. Three parts, in order: config-partition representation in the manifest;
    `live_keeper` partition resolution in `check_golden_manifest.py`; then the
    capture. **Chartered by R-O and NOT LAUNCHED as of `72576ebe`** (G-6). Until
    it runs, "ERCOT CURRENT" means *forward config only* and full coverage is
    **7 captures, not 6**.

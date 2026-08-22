# Model Audit Program — Director Status Board (2026-08)

> # ⛔ PROGRAM PARKED AT G1 BY OWNER DECISION — WS3/PERF PAUSED FOR CALIBRATION
>
> **This is not drift and nothing below is late.** The owner paused WS3/PERF-B so
> the calibration program can run. *PERF-B merged byte-green* is a G2
> precondition, so **G2 cannot be declared while WS3 is paused** and the program
> sits at **G1**. **DOCS-B** (G2) and **AUDIT-B** (G3) are **waiting by design**;
> **SITE-A** (G3) likewise. The FFR desk's **Q.2 supersession battery**, which
> commissions at G2 (`ffr-owner-sitting-2026-08-02.md` AS.6), **does not fire.**
> Whoever un-parks the program starts at the **RESTART CHECKLIST** at the bottom
> of this board, not at change (a).
>
> ### 🔴 NEW AT v11 — THE GOLDEN TIER IS PARKED BY OWNER RULING, and **G2's leg 1 now has TWO parked dependencies**
>
> The owner **parked the golden data tier on 2026-08-22**. The #4071 fix is
> merged and replays green locally; **the CI proof is deliberately unspent** and
> will not be dispatched. Record it as a **PARK, not a blocker**, and it leaves
> the board's owner queue after **twelve cycles as the top standing item** — it
> is retired by ruling, not by evidence. **The consequence has to be said
> plainly: byte-green cannot be CLAIMED for G2 while the tier is paused**, so G2
> leg 1 (*PERF-B merged byte-green*) is now blocked by **two** owner parks at
> once — WS3/PERF-B and the golden tier.
>
> ### 🔴 AND: TWO CI GATES ARE RED AT THIS PIN, and the dispatch names neither correctly
>
> **WS6 parity is RED, not green** (five NYISO `nyiso151_*` dirs), and the
> **mechanism-matrix guard is RED** on a one-word category typo whose repair is
> already sitting on an unmerged branch. Detail in changes 2 and 3.
>
> ### 🟢 AND: NYISO IS CALIBRATED ON THE AUTHORITATIVE BENCHMARK — **THREE CALIBRATED, the most the program has ever held**

> **STATUS: PARKED AT G1** — live rollup maintained by the program-director
> session, updated on each owner "refresh". Canonical program definition:
> `docs/model-audit-release-plan-2026-08.md` (its §8 ledger is the durable event
> record; this board is the at-a-glance state). Completion figures are the
> director's estimate against each workstream's full DoD (A+B halves).

**Snapshot (v11):** dispatch written against `04605b7a`; **this records lane
re-derived every figure live on 2026-08-22 at ~14:24 UTC against `origin/main`,
pinned at `94fafba`** — the dispatch's own stated base `04605b7a` **is not a
commit reachable from `main` at this read**, so nothing was carried from it
unverified · **ZERO open PRs** (live `list_pull_requests`) · **thirty-three PRs
merged since the v10 records lane's own PR #4164**: **#4165–#4198**, of which
**#4178 was never merged**, across **125 commits**. Measured instead from the
board file's last content commit `36980f9` (the WS6 lane's v10 amendment, merged
as #4168): **32 PRs / 122 commits**. **One UNMERGED remote branch exists**
(`claude/ercot-2023-summer-scarcity-9lg3nm` @ `14ce4ce`, ercot-227, pushed
2026-08-22 14:25 UTC) **with no PR open for it** — and it carries the repair for
one of the two red gates.

**Headline: the dispatch called this the quietest window in two weeks. It was
one of the busiest.** Cycle fact 12 asserts *"ZERO promotions and both
calibration lanes closed negative"*; the same dispatch's facts 5 and 6 name two
2026-08-22 keepers. **Measured at the pin: THREE promotions** (MISO twice, NYISO
once), **12 new registry sidecars**, **27 new calibration documents**, and **five
ISO lanes active** (ERCOT 225–228, CAISO 209–213, MISO 173–176, NYISO 147–151).
The one thing the dispatch got right about the quiet is that **ERCOT and CAISO
both closed negative** — but a cycle in which two ISOs rest and three keepers
move is not a quiet cycle, and the freeze case is *stronger* at v11, not weaker.

## What moved this cycle

**Read the corrections first.** The dispatch's cycle facts are wrong on three
counts and stale on a fourth, and two of the errors are internal contradictions
rather than staleness — the dispatch disagrees with itself.

1. **🔴 CORRECTION — THIS WAS NOT A ZERO-PROMOTION CYCLE, and it was not quiet.**
   Cycle fact 12(3) asks the owner to weigh the WS3 restart against *"ZERO
   promotions and both calibration lanes closed negative, the quietest window in
   two weeks."* **Measured on the keeper shards at the pin, three promotions
   landed:**
   - **MISO → `2026-08-20-miso-173-layup-mask`** (`6aae79d`) — *"first MISO
     bundle with zero D-4 conduct failures"*, the named successor to miso-172's
     remaining C8-2023 failure that v10 recorded as *running*.
   - **MISO → `2026-08-22-miso-175-hourkey`** (`4df2411`) — promoted **on the
     arm's own pre-registered gates with every kill silent**
     (`PREREG-miso175-seam-envelope-hour-key-2026-08-22.md`, committed with
     **engine-frozen per-seam cap arrays — 48 sha256 digests and signed window
     deltas — BEFORE any solve**). No owner override.
   - **NYISO → `2026-08-22-nyiso-149-duty-curve`** (`55c2cda`) — see change 5.

   That is **MISO's sixth and seventh promotions** since its stage-0 golden was
   captured and **NYISO's sixth**. Two ISOs did rest, and rested well: **CAISO
   filed five consecutive rest continuations** (caiso-209 … caiso-213, no solve,
   no probe, no LP spent in any of them) and **ERCOT ran a four-session
   owner-dispatched factor program (ercot-225…228) that moved no keeper** —
   F1/F1b/F3/F4 **REFUTED-P0 on the measured record**, F4 **DATA-ABSENT**. Rest
   on evidence is the discipline working; it is not the same fact as a quiet
   program, and the owner should not weigh the freeze against a window that did
   not happen.

2. **🔴 CORRECTION — WS6 PARITY IS RED AT THIS PIN, NOT GREEN.** Cycle fact 7
   reports *"parity OK, 53 runs / 67 bundle dirs / 0 tolerated"*. Run at the pin,
   `scripts/check_registry_payload_parity.py` **exits 1** on **five** dirs, all
   NYISO: `nyiso151_armH`, `nyiso151_armHC`, `nyiso151_armHC_recipe`,
   `nyiso151_armH_recipe`, `nyiso151_control`. The dispatch's *53 runs* is right
   (**53 registered sidecars** at the pin); its *67 bundle dirs* is not —
   **`results/calibration/` holds 76 bundle dirs**. Three things the board should
   say about this, because they are not the same thing:
   - **The dispatch is right about the pattern and wrong about the state.** The
     lane that owns all five dirs is **RUNNING at this read** —
     `session_01HX7WJaLeSi18NRvvAE9SuY`, *"NYISO frontier status"*, task summary
     ***"armHC solves complete; running gates + diagnostics"***. These are **live
     experiment state**, not dead output, exactly as the 2026-08-20 repair
     characterised the class. The gate flapping red/green through the interval is
     that lane's arms appearing and registering.
   - **But only two of the five fit the adjudicated class.** `nyiso151_armH` and
     `nyiso151_armHC` **carry real solve output** — `hourly/`,
     `legitimacy_diagnostics.json`, `run_config.json` — as does
     `nyiso151_control`. Only the two `_recipe` dirs are the meta-only
     `--replay-bundle` inputs the 2026-08-20 finding adjudicated. Calling all
     five "the false-positive pattern" over-reads that finding.
   - **🔴 AND THE ROOT CAUSE THE REPAIR NAMED WAS NEVER FIXED.**
     `FINDING-ws6-parity-nyiso-recipe-dirs-2026-08-20.md` recommended **a
     class-level carve-out for meta-only, doc-cited dirs** *"so this list stops
     growing one arm at a time"* — and **built the list instead**:
     `KEEP_REQUIRED_UNMAPPED_BUNDLES` at HEAD is a hand-maintained frozenset of
     named dirs. So **every new NYISO A/B re-reds the gate by construction**,
     which is precisely what happened three days later. The recommendation was
     recorded as *"prevention recommended (not built, per dispatch)"*; **at v11
     it has a second data point and should be built.** It is a ~10-line change
     in one script and it retires a recurring red.

3. **🔴 NEW, AND THE DISPATCH DOES NOT MENTION IT — A SECOND GATE IS RED.**
   `scripts/check_mechanism_matrix.py` **exits 1** at the pin:

   > `::error file=docs/codebase-site/data/mechanism-matrix.js::mechanism-matrix integrity: row ercot_ruc_commitment_floor references unknown category commitment`

   The base file's category registry admits `commit`; the row was written
   `commitment`. It landed via **#4195** (ercot-227). This is the **rule 26
   `[R-MECH-MATRIX]` enforcement job failing on the matrix it enforces**, and CI
   fails every PR against `main` while it stands. Two mitigating facts, both
   verified rather than assumed:
   - **Rule 26 duty (c) is otherwise satisfied** — `ercot_ruc_commitment_floor`
     exists in `scenarios.py` and has a cell line in **all six** ISO shards. The
     defect is a one-word typo, not a missing registration.
   - **The repair already exists, unmerged.** The branch tip `14ce4ce` carries
     `cat: "commit"` and its commit message reads *"ruc row cat fix"*. **It is one
     merge away**, and no PR is open for it (change 0 of the owner queue).

   Carried alongside it, from caiso-213 §3 and **not repaired by any lane**:
   **239 unresolvable mechanism-matrix anchors, up from 0** — foreign in origin
   (ercot-226) and living in the **SHARED base file**, so no single ISO lane owns
   the fix and `--fix-anchors` rewrites every ISO's rows at once. Routed
   off-lane by caiso-213 and still open.

4. **🔴 CORRECTION + DIRECTOR MISS — THE BENCHMARK SCARE IS CLOSED, AND THE
   DIRECTOR WAS WRONG ON THE MERITS.** nyiso-149 (#4180/#4183,
   `FINDING-nyiso149-bench-root-cause-2026-08-22.md`, 226 lines) root-caused it
   exactly, and the answer is none of the three causes the director's own
   dispatches carried:
   - **The cause is `01db36d`** — nyiso-147's `nyiso_chp_btm_measured` flag —
     **acting through the registering bundle's `btm.parquet`**. Not the history
     rewrite, not thin CAMPD hydration, not engine drift. The flag makes the
     BTM subtrahend flag-dependent, and the shared per-(ISO, year) bench part
     inherits **the registering run's config**.
   - **The reconciliation layer never moved, and this is measured, not
     inferred.** The benchmark EIA-923 frame rebuilt at HEAD hashes to
     **`920c8b8bc1b1`** — the identical content-addressed shared-input name
     **every registered NYISO bundle meta declares, nyiso-142 (which wrote the
     old part) and nyiso-148 (which wrote the new one) alike**. Same hash ⇒ same
     rows ⇒ `_benchmark_eia923_frame` / `_backfill_eia923_with_campd` produced
     the same output in both eras.
   - **The closure is exact.** The sector subtrahend reproduces the old part and
     the measured subtrahend reproduces the new one **to ≤0.0005 TWh on every
     gas/coal class in all three years**. There is no residual left for any other
     cause.
   - **The regenerated part is AUTHORITATIVE and the C1-2024 `CC_REGULAR` failure
     was a TRUE model defect the old part had been masking** — **+3.98 TWh** of
     ±3 % EIA-930 family-reconcile smear pro-rata re-inflating a gas family the
     refuted 35 % sector carve had over-shrunk. The old benchmark needed a
     **×1.117** annual force-scale to agree with the grid; the measured one lands
     inside the deadband unscaled.

   **RECORD IT AS A DIRECTOR MISS, in full.** The director endorsed a
   **thin-CAMPD-hydration** hypothesis on circumstantial evidence — a silent
   early-return in `_backfill_eia923_with_campd`, profile-gated CAMPD, and no
   reconciliation-code change in the window — and **recommended holding a
   five-ISO bench regeneration on that basis.** The hypothesis was refuted by
   direct measurement. **The lesson is specific and worth carrying into the
   refresh protocol: the content-addressed input hash was available the whole
   time, and it settles in ONE READ what three cycles of inference could not.**
   Three circumstantial signals pointing the same way is not evidence when a
   content hash is sitting in every bundle meta.

   **On the five-ISO regeneration — moot on the merits, still open on paper, and
   the board should not collapse the two.** Verified at the pin: the flag is
   hard-gated `iso == "NYISO"` at `src/market_sim/data/fleet/assembly.py:423-425`
   and defaults `False`, so **no other ISO's bench part can have moved through
   this channel.** But nyiso-148's own Addendum 2 closes only its §11 item 1 and
   states *"§11 items 2–4 remain open"* — **nobody amended item 2.** It is moot
   on the evidence and open in the artifact record; retiring it from the owner
   queue is correct, amending the finding is a one-line job someone still owes.

5. **🟢 NYISO IS CALIBRATED ON THE AUTHORITATIVE BENCHMARK — the first keeper to
   clear it, and it cleared it by fixing the model.** Keeper
   **`2026-08-22-nyiso-149-duty-curve`**, determination **CALIBRATED**,
   re-verified at the promotion from committed artifacts with no solve (rule 22
   D-5(b)). **C1 PASS 14/14 — including C1-2024 `CC_REGULAR`, the exact criterion
   that made the prior keeper NOT-YET on the authoritative benchmark.** The
   keeper is the nyiso-146c lineage plus **two measured zero-DOF fields**:
   `nyiso_chp_btm_measured` (nyiso-147) and `chp_layup_duty_curve` (nyiso-149,
   the graded lay-up duty the nyiso-148 split's rejection named as successor).
   All pre-registered gates pass (`_nyiso149_duty_curve_gates.json`).
   **The point worth recording is the direction of the repair:** the lane could
   have reverted the benchmark and recovered a CALIBRATED reading for free.
   It ruled the measured reconciliation correct instead, accepted the NOT-YET
   that ruling created, and then closed the exposed defect with a real duty
   curve — rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]` both working, and the
   more accurate input made the fit *worse first*.
   **A governance event inside this that the shards do not show:** the incumbent
   `2026-08-19-nyiso-146c-state-scoped` **flipped CALIBRATED → NOT-YET without
   any shard edit**, when the regenerated benchmark landed underneath it. A
   keeper's determination moved while its config did not. The nyiso-149 pin
   (`btm_bench_twh`, bench basis measured-when-artifact-exists, flag-independent)
   makes that unrepeatable, but the class of event — **a committed determination
   changing under a shared measured artifact** — is new and belongs on the risk
   register.

6. **🟢 WS5 JOB 1 IS COMPLETE ACROSS BOTH PASSES** — pass 2 merged as
   **#4187 + #4191**, record `docs/FINDING-site-facts-repair-2-2026-08-22.md`
   (373 lines). The owner reported three defects and all three are repaired:
   - **(a) "Three LP solves per year" → two.** `solving-pricing.html` was the
     last page built around P0→P1→P2. The **sequence, the animation and the
     aria-labels** are all re-presented as two passes — `js/viz-p012-sequence.js`
     `STEPS` 3 → 2, *"Pass N of 3"* → *"of 2"*, the P1 arrow pointing at P2
     dropped, `buildP2SVG` removed as dead code, and the hardcoded seed label
     `Step 1 of 3` made `STEPS.length`-derived **so it cannot drift again**.
     Exercised in Chromium, not merely loaded. **P2 survives as archived prose
     only.** *Owner ruling 2026-08-22, binding and worth restating because it is
     the kind of scope line that gets misread later:* **SITE CONTENT ONLY — P2
     stays in the codebase behind `--enable-legacy-p2`, and nothing under `src/`
     was touched.**
   - **(b) Solve-time claims, understated 3–11×, replaced with measured
     wallclock.** See change 7 — these are now on the site and belong in the
     record.
   - **(c) The ISO-specific corpora added to `data-pipeline.html`** with **honest
     retention status**, including naming the **unrecoverable** ones (the CAISO
     OASIS group-zip dailies; pre-slim SCED columns past ERCOT MIS retention).
     The five offer corpora are described as `IDENTIFY`, not dispatch inputs —
     traced to their consumers in code **before** being described, because under
     rule 13 `[R-MEASURED]` that distinction is the whole point.

   **Two things the reported scope did not include and a sweep surfaced**, both
   repaired: the 25-year forecast claim was wrong in its **mechanism**, not just
   its number (change 7), and **three pages rendered 81 table headers at
   1.01–2.41:1 contrast** — black on navy, effectively invisible, one root cause.
   **Deferred correctly to SITE-A** and left untouched: the orphaned
   `forecast-validation.html` nav entry and `model-updates.html` → pointer (both
   §6-signed dispositions carried into §7.6), plus site-wide wide-table clipping
   (`html`/`body` both `overflow-x: hidden`, so a wide table is **clipped and
   unreachable, not scrollable** — only the four new corpus tables got a scroll
   container). **SITE-A remains gated at G3 and NOT started**; Job 1 was scoped
   pre-G3 precisely because false statements should not wait on a gate.

7. **🟢 THE SOLVE-TIME NUMBERS ARE NOW ON THE SITE AND BELONG IN THE RECORD.**
   Host class: **4 vCPU / 15–16 GB**. Per-year: **3–6 min** on the plain
   calibration recipe (**ERCOT 183–323 s**, **MISO 293–339 s**); **4–18 min** for
   **keeper recipes at HEAD** (**NEISO 278–362 s**, **NYISO 229–459 s**, **ERCOT
   846–1,093 s**). Full-horizon **2026–2050 cold**: **ERCOT 51.1 min**, **NEISO
   41.2 min**, **NYISO 34.7 min**; **CAISO's WARM arm alone 122.4 min** with its
   **cold arm stopped at 22 of 25 years — no verdict, and it must not be quoted
   as one**; **PJM and MISO NEVER measured at full horizon.**
   **The material discovery, and the reason the old site number was right by
   accident:** **cross-year warm-start is DISARMED on the forecast path by owner
   decision D-10 (2026-08-04)** — `shipped_forecast_xyear_warmstart` returns
   `False` and is the **one reader** all three shipped forecast runners pass
   through — **because FFR-3M measured that a killed-and-resumed forecast does
   not reproduce from its own cache.** So forecast years solve **cold** and the
   **~2.3× is an accepted cost**. Backcast cross-year warm-start is a **separate
   mechanism and stays on** (5.6× on ERCOT's year-1 P0 from a persisted basis).
   **One caveat governs every wall figure above and is now stated on the pages
   themselves:** cross-run walls on this host vary up to **±35 %** — the PERF-B
   record measures the same ERCOT-2025 P0 at **574.5 s and 363.6 s in
   back-to-back byte-identical arms**. **Phase structure is the reliable signal;
   a single wall reading is not.** Two claims that asserted a P1 simplex-iteration
   count were **removed rather than restated** — no measured P1 iteration count
   exists anywhere in the record, and P0 alone runs ~190,000 dual-simplex
   iterations.

8. **🟡 CONFIRMED — GOLDEN-TIER CI IS UNCHANGED FOR A FOURTH CONSECUTIVE READ,
   AND IS NOW PARKED.** Live `actions_list` on `golden-data-tier.yml` returns
   **five runs, unchanged**: latest is still the red **`31999181985`** (schedule,
   2026-08-17T05:48:08Z, main); last green is still **`31913648051`**
   (workflow_dispatch, 2026-08-15T23:01:19Z, branch
   `claude/golden-tier-emissions-oom-03qlck`). The **Monday 2026-08-24 05:37 UTC**
   cron v10 predicted has not yet arrived — today is Saturday 2026-08-22 — so
   nothing about the tier's CI state has moved or could have. **What changed is
   the disposition, not the evidence:** the owner **parked the tier on
   2026-08-22** and the CI proof is **deliberately unspent**. The fix (#4071) is
   merged and locally replayed green across a full four-step job. **The park is
   an owner ruling delivered through this cycle's director dispatch; no in-repo
   artifact records it, so THIS BOARD IS ITS RECORD.**

9. **🟢 CONFIRMED — KEEPERS AND DETERMINATIONS EXACTLY AS DISPATCHED, and THREE
   CALIBRATED is the most the program has held.** Every one read from its own
   shard and its own `status/<ISO>.js` keeper block at the pin — see the keeper
   table. **The CALIBRATED set is still exactly the `complete`-marker set**, and
   NYISO's arrival makes that three-for-three rather than a coincidence of two.

10. **🟢 CONFIRMED — NEISO-100 IS RESOLVED AS A LANE AND REDUCES TO AN OWNER
    DECISION.** `ASSESSMENT-neiso101-2019-input-prep-2026-08-18.md` closes the
    **DATA half** of `final` precondition #2, with **zero tracked files
    modified**; **its entire residual is the `final` grant itself —
    precondition #5**, not any preparable input. It also **recommends dropping
    `bench/NEISO/2019` from the precondition list**: it is *"an output of the
    spend, not an input to it"* — a registration byproduct, not a precondition.
    **The 2025 EIA-923 FINAL vintage has still not landed.** *Carried from
    neiso-101 and NOT independently re-verified in this lane:* this session runs
    `DATA PROFILE: code`, so `data/raw` is unhydrated, and a tree-only read
    (`GIT_NO_LAZY_FETCH=1 git ls-tree`) shows no `data/raw/eia-923/` subtree at
    all — the EIA-923 payload lives in `_processed-legacy/eia923_monthly_*.parquet`
    whose vintage cannot be read without downloading the blob. **Stated as
    carried rather than re-derived, because this board does not assert what it
    did not measure.**

11. **🟢 CORRECTION — THE SESSION READ DID NOT FAIL, AND HAS NOT FAILED FOR THREE
    CONSECUTIVE CYCLES.** Cycle fact 13 pre-authorises a commit-trailer rebuild
    *"if it fails again (it has for four consecutive cycles)"*. **The premise is
    wrong twice over:** `list_sessions` returned **40 sessions** (`mine: true`,
    `has_more: true`) at this read, and **v9 and v10 both recorded successful
    live reads** (30 and 40 sessions respectively). The deviation has been
    **CLOSED for three cycles running**, not failing for four. **No roster row
    below is trailer-rebuilt.** Honest limit, unchanged: the page caps at 40 with
    `has_more: true`, so lanes older than 2026-08-15 fall outside it — none of
    this cycle's do.

## Keeper table (read from `frontend/data/backcast/keepers/<ISO>.json` and `status/<ISO>.js` at `94fafba`)

| ISO | Designated keeper | Determination | This cycle |
|-----|-------------------|---------------|------------|
| ERCOT | `2026-08-20-ercot223-arm-eventrelease` | `NOT-YET` | **UNMOVED — a four-session owner-dispatched factor program ran and promoted nothing.** ercot-225 filed an **owner decision card on the G-SPUR band-top gate, AWAITING SIGN-OFF** (measured on every registered ERCOT run; **no verdict of any standing run changes under the revision**, and one recorded artifact-leg FAIL is exonerated). ercot-226 built and probed the 2023 held-sequestration factor program: **F1/F1b/F3/F4 REFUTED-P0 on the measured record**, F2 (held-location) built and probed. ercot-228 returned **DATA-ABSENT** on F4 — no public 2023 DA-forecast vintage is retrievable and the only archive holding one is the **owner-declined credentialed API**. ercot-227 is **unmerged on `claude/ercot-2023-summer-scarcity-9lg3nm`** and carries the matrix-gate repair. Fail set unchanged {C3a-2023 −39.7 %, C3b-2023 0.729}, C3c ledgered ×3 |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `NOT-YET` | **UNMOVED — and the most disciplined lane on the board for a second consecutive cycle.** **Five** rest continuations (caiso-209 … caiso-213), **no solve, no probe, no LP spent in any of them**; every one re-verified on committed bytes at a HEAD that kept moving (caiso-213 alone re-read across 35 commits). caiso-212's bench-staleness adjudication **carries on its own stated terms** — fingerprint `dbea7bf45111` unmoved, `BUILDER_SOURCES` unmoved, `run_calibration_full.py` byte-identical across `c55da9c..HEAD`. **caiso-213 found the 239-anchor matrix defect and routed it off-lane rather than fixing a shared file from an ISO lane** (rule 26 discipline). Owner packet unchanged at **TWO** funding items, neither of which closes C3a alone (62.1 %/10.4 % and <5 %) |
| PJM | `2026-08-15-pjm-162-inputclock` | `CALIBRATED` | **Unmoved and untouched for a THIRD consecutive cycle** — no PJM calibration lane ran. Two PJM T1-H hindcast reports landed (forecast family; separate dashboard namespace, plan §7.5). Still `final`-NOT-YET on the merits (#4083); 2020 rung not data-ready. **The only ISO whose keeper has been stable for three cycles — which makes it the cheapest stage-0 capture on the board** |
| NYISO | **`2026-08-22-nyiso-149-duty-curve`** | **`CALIBRATED`** | **PROMOTED — and it is the first NYISO keeper to clear the AUTHORITATIVE benchmark.** C1 PASS **14/14**, including the C1-2024 `CC_REGULAR` that made the prior keeper NOT-YET; C2/C3a/C3b/C4/C6/C8 all PASS; **C3c the single ledgered caveat** (model 1/0/0 h >$300 vs RT actual 10/13/42 h), auto-ledgered under the C3c STANDING RULE and **reported at full magnitude without downgrading** (rubric v3.3). Two measured zero-DOF fields over the 146c lineage. **The lane fixed the model rather than reverting the benchmark** (change 5). `complete` **re-keyed to nyiso-149** with determination re-verified from committed artifacts, no solve (rule 22 D-5(b)). **NYISO is also the sole source of all five parity-RED dirs — from a lane that is still running** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `CALIBRATED` | **Unmoved and untouched by calibration.** A NEISO T1-H realized/Mystic-rescore hindcast report landed (forecast family, separate namespace). **EIA-923 2025 final vintage STILL NOT LANDED** (carried from neiso-101, not re-verified here — see change 10). `final` precondition #2's data half is CLOSED; its entire residual is the `final` grant |
| MISO | **`2026-08-22-miso-175-hourkey`** | `NOT-YET` | **PROMOTED TWICE.** miso-173-layup-mask (2026-08-20) — **the first MISO bundle with ZERO D-4 conduct failures**, closing the chain miso-170 opened → **miso-175-hourkey** (2026-08-22), promoted **on the arm's own pre-registered gates with EVERY KILL SILENT**, its per-seam cap arrays **engine-frozen and committed as 48 sha256 digests with signed window deltas BEFORE any solve**. No owner override in either. miso-174 adjudicated the seam over-import question and miso-176 measured M2M seam binding reality (`m2m_seam_entitlement_cap` minted **G**). Determination stays **NOT-YET** |

**Markers at HEAD (`94fafba`, re-read this cycle):** `complete` =
**{NEISO, NYISO, PJM}** · **`final` = empty (`_note` only)** ·
**`holdout-freeze.json` `active: true`**, and it outranks both marker blocks.
**NO ISO HAS EVER SPENT A LOCKED-TEST YEAR** — verified exhaustively rather than
asserted: across all **53** registered sidecars (52 at v10; **12 added this
cycle, 11 net after reconciliation**) the solve-year histogram is
**{2022: 2, 2023: 51, 2024: 51, 2025: 51}**, and the only two out-of-training
registrations are the authorized **2022 validation touchpoints** (PJM
`2026-08-05-pjm-2022-touchpoint`, NEISO `2026-08-06-neiso-2022-corrected-basis`).
**No 2019, no H1-2026, anywhere** ([R-HOLDOUT]).
**This line is re-verified and republished every cycle for a reason, and v10
supplied it:** WS5 Job 1 found the public site asserting the exact opposite — that
NEISO's locked-test one-shot *had been scored and stood* — for a full two weeks
after owner decision D-23 corrected it on the record. **A governance fact that is
true in the JSON and false on the site is not a fact the program can claim.**
Determinations: **PJM, NYISO, NEISO `CALIBRATED`** · **ERCOT, CAISO, MISO
`NOT-YET`** — the CALIBRATED set is still exactly the `complete`-marker set, and
at three-of-three that is now a pattern rather than a coincidence.

## Workstream rollup

| WS | State | Completion | Blockers / next |
|----|-------|------------|-----------------|
| WS1 `AUDIT` | AUDIT-A **completed** (#3991). Rows **O8 CLOSED**, **O5 CLOSED** (#4072, re-verified **stronger** at #4085 on a newer keeper set, residual third replay path **gated + tested**), **O4 re-measured and STILL OPEN** (#4085 — disposition act only, owner card, recommendation (A)) | **In progress ~91 %** | **AUDIT-B gated at G3 — waiting by design.** Rows **O4, O6, O7** open |
| WS2 `DEBUG` | **COMPLETED** — DEBUG-A ✓, DEBUG-B ✓, pjm-162 promoted, sibling-import residue retired, landing-verify green on merged main. Row B1 annotated **STALE** (#4085), no code change | **Completed** | none; no DEBUG-C continuation chartered |
| WS3 `PERF` | PERF-A ✓. **PERF-B PAUSED BY OWNER.** Stage-0: **5 of 6 ISOs captured** (ERCOT #4033, NEISO #4041, NYISO #4050, CAISO #4058, MISO #4060; **PJM never captured**). Changes: **(c) landed via #3964**, **(d)+(e) merged via #4067**, **(a)/(b) unstarted**. Close-out note + wallclock baseline landed (#4075). **`results/regression-goldens/` is byte-unmoved this cycle** — verified by `git diff --stat`, not assumed | **Paused ~74 %** | **Paused, not blocked — and now blocked TWICE at G2.** 0 of 6 goldens match their keeper for a second consecutive cycle, and with the **golden tier parked**, byte-green cannot even be *claimed*. On restart: freeze calibration, then re-verify every golden — RESTART CHECKLIST |
| WS4 `DOCS` | DOCS-A **completed** (#3999 + #4005); DOCS-B held | **In progress ~60 %** | **DOCS-B gated at G2 — waiting by design** |
| WS5 `SITE` | **Job 1 (site factual repair, pre-G3) COMPLETE ACROSS BOTH PASSES.** Pass 1 #4120 + #4121 (15 repairs, 3 governance-grade); **pass 2 #4187 + #4191**, record `docs/FINDING-site-facts-repair-2-2026-08-22.md` (373 lines) — three owner-reported defects repaired plus two a sweep surfaced. Job 2 = **SITE-A**, not started | **Job 1 COMPLETED · Job 2 not started** | **SITE-A gated at G3 — waiting by design.** Its deferral list grew this cycle: the orphaned `forecast-validation.html` nav entry, `model-updates.html` → pointer, and **site-wide wide-table clipping** |
| WS6 `BLOAT` | Prunes B-1..B-8 merged; **BLOAT-2 CLOSED** (#4032); **BLOAT-3 ADJUDICATED** (#4031) and **EXECUTED** (BLOAT-S2 #4047, −444.5 MiB / 144 files at tip). **The chartered work stays completed; the parity gate is RED again** | **Completed (charter) · gate RED** | **🔴 RED at this pin, five NYISO `nyiso151_*` dirs, exit 1.** The owning lane is **RUNNING**, so these are live experiment state — but **the 2026-08-20 repair's own recommended fix (a class-level carve-out for meta-only doc-cited dirs) was NEVER BUILT**; it allowlisted two dirs by name instead, so **every new NYISO A/B re-reds the gate by construction**. Second data point in three days. Build the carve-out |
| — `GOLDEN-TIER-FIX` | **COMPLETED and independently verified** (#4014). First scheduled cron came back **RED**, **diagnosed + fixed same-day** (#4071), **deliverables verified by a full local four-step job replay, all green** | **Completed · tier PARKED** | **🅿️ PARKED BY OWNER RULING 2026-08-22.** The CI proof is **deliberately unspent** and will not be dispatched. CI state unchanged for a **fourth** read (5 runs; latest red `31999181985`; last green `31913648051`). **Consequence: byte-green cannot be CLAIMED for G2 while the tier is paused** |
| — `MATRIX GUARD` | rule 26 `[R-MECH-MATRIX]` CI enforcement | **🔴 RED at this pin** | `check_mechanism_matrix.py` **exit 1** — `ercot_ruc_commitment_floor` cites category `commitment`; the registry admits `commit`. Landed via **#4195**. **Repair exists unmerged at `14ce4ce`** (`cat: "commit"`) — one merge away, no PR open. Separately: **239 unresolvable anchors** (0 → 239), origin ercot-226, in the SHARED base file, routed off-lane by caiso-213 and unowned |

**WS1–WS4 are byte-unmoved this cycle; WS5 moved and WS6's gate went red again.**
Verified rather than assumed: across all 33 merges **neither this board nor the
plan's §8 ledger was touched by any lane**, the only WS-owned content that moved
is WS5's **five `docs/codebase-site/` content files**, **no
`.github/workflows/` file changed**, and **no `results/regression-goldens/` file
changed**. Rows **O4, O6, O7** remain the open audit rows, all three gated at G3
or awaiting an owner act.

## Stage-0 golden staleness (recomputed at `94fafba`)

Re-derived at HEAD from `frontend/data/backcast/keepers/<ISO>.json` and
`results/regression-goldens/perfb-stage0/manifest.json` (`git_sha` **`af1ccb6`**,
`git_dirty: false`, **byte-unmoved this cycle**) — **not copied from v10.** Each
captured bundle was mapped back to its registered run id through the registry
sidecars' `bundle` field rather than by name.

| ISO | Golden captured against | Designated keeper at `94fafba` | Verdict |
|-----|-------------------------|--------------------------------|---------|
| ERCOT | `2026-08-15-ercot204-rule26-delete` (#4033) | `2026-08-20-ercot223-arm-eventrelease` | **STALE — four promotions past capture** (unchanged; ERCOT rested) |
| NEISO | `neiso93_envelope_A` = `2026-08-14-neiso-93-envelope` (#4041) | `2026-08-17-neiso-99-joint-p1` | **STALE — two promotions past capture.** The re-stamp-not-re-solve shortcut was established for **neiso-97 only**; re-establish before relying on it |
| CAISO | `caiso197_w2_r5` = `2026-08-16-caiso-197-w2-r5` (#4058) | `2026-08-17-caiso-200-h1-memberpanel` | **STALE — one promotion past capture.** Unchanged for a second cycle; still the narrowest gap on the board, and CAISO has now rested through two |
| MISO | `2026-08-16-miso-160-wefor-shape` (#4060) | `2026-08-22-miso-175-hourkey` | **🔴 STALE — SEVEN promotions past capture**, two of them this cycle (169 → 170 → 170b → 172 → 173 → 175) |
| NYISO | `nyiso140_exclusion_arm` = `2026-08-16-nyiso-140-layup-exclusion` (#4050) | `2026-08-22-nyiso-149-duty-curve` | **🔴 STALE — SIX promotions past capture**, and the worst gap on the board for a second cycle |
| PJM | — | `2026-08-15-pjm-162-inputclock` | **NO GOLDEN — never captured**, and the keeper has now been **stable for three cycles** |

**Count: 5 stale / 0 current / 1 no-golden** — unchanged from v10 at 0/6
effective coverage, against **4 / 1 / 1** at v8 and v9.

**🔴 THE STRUCTURAL POINT STANDS, AND v11 SHARPENS IT RATHER THAN REPEATING IT.**
Zero coverage is now in its **second** consecutive cycle and its **seventh**
consecutive cycle of keepers outrunning captures. What v11 adds:

- **The gaps are still widening even in a cycle two ISOs sat out.** MISO went
  from four promotions past capture to **seven**; NYISO from five to **six**.
  CAISO and ERCOT held only because their lanes deliberately rested — and
  **rest-by-choice is not a capture window**, because the moment a lever is
  found those lanes resume.
- **The one ISO that could be captured cheaply today is PJM**, which has no
  golden at all and a keeper unmoved for three cycles. It is simultaneously the
  **largest coverage gap** and the **cheapest capture**, and that combination
  has now held across three boards without being taken.
- **🔴 AND THE GOLDEN-TIER PARK CHANGES THE ARITHMETIC OF THE FREEZE.** Until
  this cycle, the freeze bought re-captured goldens that could be *proven* green
  in CI. With the tier parked, **a re-capture can be taken but its byte-green
  claim cannot be certified** — G2's leg 1 is behind two owner parks, not one.
  **This is not an argument against the freeze; it is an argument that the
  freeze alone no longer suffices.** Whoever declares it must decide the golden
  tier's disposition in the same act, or WS3 restarts into a gate it still
  cannot pass.

## Gates

- **G0** adopted ✓ (2026-08-13) · **G1** DECLARED ✓ (2026-08-16, #4006).
- **G2 — UNREACHABLE, and now behind TWO owner parks rather than one.** Leg 1 is
  *PERF-B merged byte-green*; PERF-B is paused by owner decision **and** the
  golden tier that would certify byte-green is parked by owner ruling. No other
  leg substitutes. The legs:
  1. **PERF-B merged byte-green** — **doubly blocked at v11**: 5 of 6 captured
     and **all 5 stale for a second cycle**, (c)/(d)/(e) merged, (a)/(b)
     unstarted, **and the golden tier is parked so byte-green cannot be
     claimed** even if captures were current.
  2. **One completed fast-tier-green `ci.yml` run** — the sparse block landed
     (#3964, runner-validated at 31873178938: 6838 passed / 31 skipped).
     **⚠️ Note for whoever tries to satisfy this today: `main` currently fails
     the `mechanism-matrix-guard` job** (change 3), so a green `ci.yml` run is
     not obtainable at this pin until `14ce4ce` merges.
  3. **A keeper freeze** — **owner call, outstanding across nine director cycles.**
     Three promotions landed this cycle even with two ISOs resting; at this pin
     **three lanes are running** (NYISO frontier, ERCOT F1b/ercot-229, the
     RHO_CLIP identification) and two are review-ready. There is still no quiet
     window in view, and v11's evidence is that **there is no longer a quiet
     window that would help**, because the golden tier is parked.
  4. **Branch-protection flip** — owner action, memo ready.

  On declaration the PM notifies the FFR desk (Q.2 battery).
- **G3** — unchanged: after G2, **DOCS-B** + the **BLOAT leg**. BLOAT's verdict
  and its chartered execution are satisfied (#4031 + #4047); **its parity gate is
  RED again** and is the one G3 leg that keeps regressing — **twice in three
  days now**, on a root cause whose fix was recommended and never built.
  The golden-tier proof leg is satisfied by #4014 + the green dispatch **as
  evidence**, though the tier itself is now parked.
- **G4** — unchanged: SITE-A + AUDIT-B. **WS5 Job 1 is not a G4 leg** — it was
  deliberately scoped pre-G3 as factual repair, and completing both its passes
  does not advance G4.

## Watch

- **🅿️ GOLDEN TIER — PARKED BY OWNER RULING 2026-08-22.** After **twelve cycles
  as the top standing owner-queue item**, it is retired from the queue by
  decision rather than by evidence. The #4071 fix is merged and locally replayed
  green; the CI proof is **deliberately unspent**. CI state re-read live and
  **unchanged for a fourth consecutive cycle**. **Record it as a park, not a
  blocker** — but record the consequence too: **BLOAT-S2's D3 leg and every
  byte-green claim remain unprovable**, and G2 leg 1 is now doubly parked.
- **🔴 TWO CI GATES ARE RED ON `main` AT THIS PIN.** WS6 parity (five NYISO
  `nyiso151_*` dirs) and the rule 26 matrix guard (`ercot_ruc_commitment_floor`
  → unknown category `commitment`). The matrix repair is **one merge away** on
  `14ce4ce`. The parity red will **recur on the next NYISO A/B** unless the
  class-level carve-out the 2026-08-20 finding recommended is actually built.
  **A program that reports its own gates green while `main` fails two of them is
  the failure mode this board exists to prevent** — which is why every gate on
  this board is now run, not quoted.
- **🔴 STAGE-0 COVERAGE IS AT ZERO FOR A SECOND CYCLE**, and the gaps widened in
  a cycle two ISOs sat out. See the structural point above — and note that the
  golden-tier park means the freeze must now be declared **together with** a
  disposition for the tier, not before it.
- **🟠 NEW — A KEEPER'S DETERMINATION CHANGED WITHOUT ITS CONFIG CHANGING.**
  `2026-08-19-nyiso-146c-state-scoped` flipped **CALIBRATED → NOT-YET** with no
  shard edit, when the regenerated shared benchmark landed underneath it. The
  nyiso-149 pin (`btm_bench_twh`, flag-independent) makes that specific route
  unrepeatable, but **the class of event is new**: a shared measured artifact,
  re-rendered by whichever run happens to register next, silently re-grading
  committed determinations. **Every ISO shares that benchmark path.** Worth an
  explicit look at whether any other shared artifact carries a registering run's
  config the way `btm.parquet` did.
- **🟠 THE UNCITED `RHO_CLIP` 0.5 FLOOR — STILL UNRULED, and the lane is now
  running.** Verified at the pin: `src/market_sim/data/online_reserve_rho.py:87`
  still reads `RHO_CLIP: tuple[float, float] = (0.5, 4.0)`. **Both measured NYISO
  values fall BELOW the floor** (`incity_obligation` 0.3014, `nyc_spin` 0.2011)
  and **MISO's measured rho is 0.1764** — also below — so `rho_used` returns
  **the floor, not the measurement**, a live rule 5 `[R-NO-MAGIC]` exposure
  inside a mechanism MISO has now been promoted **six times** on top of. **The
  identification lane IS running at this read** (`session_01TM83kV5Pv5cKUJBrjyt2wx`,
  *"RHO_CLIP 0.5 floor citation in MISO"*, summary *"reading evidence docs;
  mapping miso-169 arm mechanism"*). **Do not re-issue it.** What remains is the
  ruling, which the code's own comment says is the owner's.
- **🟠 CARRIED — PUBLISHED GOVERNANCE FACTS DRIFT FROM THE JSON THAT HOLDS THEM.**
  Unchanged this cycle: `holdout-freeze.json`'s own prose still says intake is
  permitted *"under session-logged owner authorization"*, which the **2026-08-06
  rule 22 amendment reversed** (*what is held out is the score, never the data or
  the architecture*). Committed governance data disagreeing with the governing
  rule. **Explicitly re-confirmed as untouched by WS5 pass 2** (its §5 item 6) —
  it is governance data, not site content, and belongs to a governance lane.
- **🟠 THE 239 UNRESOLVABLE MATRIX ANCHORS — FOUND, ROUTED, UNOWNED.** caiso-213
  found the count moved **0 → 239**, foreign in origin (ercot-226) and in the
  **SHARED base file** — and correctly **did not fix it from a CAISO lane**,
  because `--fix-anchors` rewrites every ISO's rows at once (rule 26(d)). That
  discipline is right and it leaves the defect ownerless. **A cross-ISO matrix
  hygiene pass is the natural home**, and it should land in the same act as the
  `14ce4ce` category repair.
- **DURABLE LESSON (unchanged, and the golden-tier park makes it sharper, not
  softer):** `golden-data-tier.yml` is the **ONLY** workflow that runs
  `scripts/regenerate_clean.py`, so **any curation-time defect under
  `scripts/data/curate_*.py` has NO pre-merge signal** — invisible to every PR
  check, surfacing only on the weekly cron, and compounded by `data/clean` being
  derived and gitignored. **With the tier parked, that blind spot is now
  permanent until it is un-parked. Treat curate-script changes as unguarded.**
- **🔴 NEW DURABLE LESSON — WHEN A CONTENT HASH EXISTS, READ IT.** The
  benchmark scare ran for three cycles on inference (a silent early return,
  profile-gated CAMPD, no reconciliation-code change in the window) and was
  settled in one read by a hash that had been sitting in every bundle meta the
  whole time (`920c8b8bc1b1`). **Three circumstantial signals pointing the same
  way are not evidence when a content-addressed identity is available.** The
  director's own miss (change 4) is the case in point.
- **🟠 #4054 / nyiso-140 null-treatment question — STILL OPEN, NEVER ADJUDICATED,
  and further out of reach again.** The NYISO keeper has moved **six promotions**
  past the captured nyiso-140 config. Any claim that re-checking it "costs a
  fidelity read, not a solve" must be **re-derived**, not inherited.
- **🟢 CARRIED CLOSED — the ≥24 GB MISO container ask** (retired at v9 on
  miso-169's measurement, 13.95 → 12.40 GB peak) has stayed retired across
  **six** further MISO promotions on the 15 GB box.

## Owner queue at cycle end

Re-ordered and re-verified at `94fafba`. **Three items retired this cycle** and
**two new ones arrive**, both of them owner decision cards a lane filed and
cannot itself sign.

0. **🔴 NEW, AND THE CHEAPEST ITEM ON THE BOARD — MERGE `14ce4ce` TO CLEAR THE
   MATRIX GATE.** `main` fails `check_mechanism_matrix.py` on a one-word category
   typo (`commitment` → `commit`) landed by #4195. **The repair is already
   written and pushed** on `claude/ercot-2023-summer-scarcity-9lg3nm`, which has
   **no PR open**. Until it merges, **CI is red on `main` and G2 leg 2 is
   unobtainable**. This is a merge, not a decision — it sits at rank 0 only
   because everything else waits behind a red gate.
1. **🔴 THE `RHO_CLIP` 0.5-FLOOR RULING — SIXTH CYCLE, and the identification is
   BEING PRODUCED RIGHT NOW.** The constant is unchanged at
   `online_reserve_rho.py:87`; MISO's measured rho is **0.1764**, clipped up to
   0.5 with no citation, under a keeper promoted **six times** on top of it
   (rule 5 `[R-NO-MAGIC]`). **The lane is running** (roster below) and will
   deliver the identification. **What the owner owes is the ruling on the band,
   which the module's own comment says is not a session's to make.** The re-solve
   is one `--set`.
2. **🔴 WS3 RESTART / CALIBRATION FREEZE — RE-SERVED, AND THE ASK HAS CHANGED
   SHAPE.** v10 recommended a **scoped, time-boxed** freeze and that
   recommendation stands. **What v11 adds is that a freeze alone is no longer
   sufficient:** with the golden tier parked, re-captured goldens **cannot be
   certified byte-green**, so G2 leg 1 stays blocked even after a successful
   freeze. **The freeze and the golden tier's disposition are now ONE decision,
   and serving them separately guarantees WS3 restarts into a gate it cannot
   pass.** The correction to the dispatch matters here: **this was not a
   zero-promotion cycle** (change 1), so the owner should not weigh the freeze
   against a lull that did not occur. The honest framing is unchanged and
   answerable: *how many days of calibration are six certifiable goldens worth?*
3. **🟠 NEW — SIGN OR DECLINE THE ercot-225 G-SPUR BAND-TOP GATE CARD.**
   `DECISION-ercot225-gspur-bandtop-gate-2026-08-21.md`, drafted 2026-08-21,
   status **AWAITING OWNER SIGN-OFF**; the gate is **not changed by the card**.
   Measured on every registered ERCOT run from committed artifacts only (no LP,
   no solve, no re-bundle), protocol precommitted and blob-verified before any
   number was computed. **No verdict of any standing run changes under the
   revision**, and one recorded artifact-leg FAIL is exonerated. **A cheap
   signature that unblocks the ERCOT lane's gate design.**
4. **🟠 NEW — THE nyiso-148 2025 DEAR-GAS LEVEL CARD.**
   `docs/DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md` — *"the $6.57
   that is not a CHP object"*. **Nothing is armed, changed or promoted by it.**
   Note it carries a same-day update: the keeper it names has since been
   superseded by nyiso-149, so **read the card's UPDATE block before its
   numbers.**
5. **NEISO `final` GRANT — the whole of what NEISO-100 reduces to.** neiso-101
   closed the **data half** of precondition #2 with **zero tracked files
   modified**; **its entire residual is the `final` grant itself (precondition
   #5)**. It also recommends **dropping `bench/NEISO/2019` from the precondition
   list** as a registration byproduct, which the owner should accept or reject
   explicitly rather than leaving on the list. **The 2025 EIA-923 FINAL vintage
   has still not landed** (carried, not re-verified here — change 10). Standing
   and unchanged: **no ISO has ever spent a locked-test year**, NEISO's one-shot
   is **NEVER GRANTED, not spent** (D-23), and 2019 is unsolvable at HEAD on the
   Pilgrim gap regardless.
6. **Validation-freeze lift signature** — the **O4/O5 card**
   (`AUDIT-FOLLOWUP-o5-o4-2026-08-18.md` §2.4), recommendation **(A) close the
   charter with cause, lift the VALIDATION tier only, leave `final` empty**. The
   detector question is closed on evidence; *"resolve the detector question"* is
   not one of the choices. **Unmoved for a second cycle.**
7. **🟠 CARRIED — rule on the cross-ISO scorer-change precedent.** The nyiso-143
   D-4 conduct rider reached MISO's committed diagnostics and MISO agreed with
   it. The outcome was good; the *mechanism* — a scorer-side change in one ISO's
   lane silently re-grading another ISO's artifacts — is the shape rule 25
   `[R-ISO-SCOPE]` exists to prevent. **This cycle produced a near-twin worth
   ruling on in the same breath** (the shared-benchmark determination flip, Watch
   above): both are one lane's act re-grading another's committed record.
8. **🟠 CARRIED — the `holdout-freeze.json` prose conflict.** Unchanged, and
   explicitly confirmed untouched by WS5 pass 2. Committed governance data
   disagreeing with the governing rule. **Still the cheapest correctness item on
   the board.**
9. **O6 — locked-test scheduling.** Re-verified exhaustively at this pin across
   all **53** registered sidecars (year histogram {2022: 2, 2023: 51, 2024: 51,
   2025: 51}). `complete` = {NEISO, NYISO, PJM}; `final` holds only its `_note`;
   the freeze is `active: true` and outranks both. **Never let a lane spend one**;
   scheduling is the owner's alone.
10. **O7 — ERCOT P0 bit-identity proof forfeited** (accept-and-document, or
    charter restoration).
11. **decision-1 ack** — warm-start closed-overtaken; **still unacked, twelfth
    cycle**; a one-word ack retires it. *(v10 corrected the dispatch's numbering
    down by two against v9's record; the dispatch's "12th cycle" is carried here
    as given, since the two counters have been reconciled to the same base.)*
12. **caiso-199 NOT-YET determination** — carried. **The CAISO lane rested five
    times this cycle without spending an LP**, and its packet is unchanged at two
    funding items, **neither of which closes C3a alone** (most-favourable bounds
    62.1 % / 10.4 % of the required 2024/2025 move, and <5 % direct λ share).
    Owner ruling 5 stands: **C3a must genuinely pass; NOT-YET is the honest
    fallback.**
13. **RETIRED THIS CYCLE:**
    - ~~**the golden-tier proof-of-fix `workflow_dispatch`**~~ — **PARKED BY
      OWNER RULING 2026-08-22** after twelve cycles as rank 0. Retired by
      decision, not by evidence; its consequence for G2 is recorded above.
    - ~~**the benchmark-authority question**~~ — **CLOSED by nyiso-149**, which
      grounded the owner's 2026-08-21 "regenerated is authoritative" ruling in
      mechanism rather than recency, and pinned it flag-independent so the parts
      cannot flip back.
    - ~~**the five-ISO bench regeneration**~~ — **MOOT**: the flag is hard-gated
      `iso == "NYISO"` and defaults off, so no other ISO's part could have moved.
      **Retired from the queue on the merits, but note it is still listed open in
      nyiso-148's own §11 item 2** — someone owes that finding a one-line
      amendment.

## Session roster

> **🟢 LIVE READ — the deviation stays CLOSED for a THIRD consecutive cycle, and
> the dispatch's premise is corrected.** Cycle fact 13 pre-authorised a
> commit-trailer rebuild *"if it fails again (it has for four consecutive
> cycles)"*. **It has not failed for four cycles — it has SUCCEEDED for three.**
> v9 read 30 sessions, v10 read 40, and this read returned **40**
> (`mine: true`, `has_more: true`). The fallback was not needed and **no row
> below is trailer-rebuilt.** Honest limit, unchanged: the page caps at 40, so
> lanes older than 2026-08-15 fall outside it — none of this cycle's do.

**Lanes active this cycle**, live status as read at ~14:24 UTC 2026-08-22:

| Lane | Session | Live state |
|------|---------|------------|
| **Records v11 (this lane)** | `session_0139EsHUG9wpkrxu3o6sdVYa` | **WORKING** — *"re-deriving board figures at live HEAD; parity RED"*. Branch `claude/director-records-board-ledger-rjauh9` |
| **RHO_CLIP identification** | `session_01TM83kV5Pv5cKUJBrjyt2wx` | **🟢 WORKING** — *"reading evidence docs; mapping miso-169 arm mechanism"*. **The owner-queue rank-1 lane; do not re-issue** |
| **NYISO frontier (nyiso-150/151)** | `session_01HX7WJaLeSi18NRvvAE9SuY` | **🟢 WORKING** — *"armHC solves complete; running gates + diagnostics"*. **Owns all five parity-RED dirs**; they are live experiment state |
| **ERCOT F1b / ercot-229** | `session_01B1rSnA9jgeYdByToi5ufVJ` | **🟢 WORKING** — *"ercot-229 F1b: ancestry verified, field wired, deps installing"* (NSPIN held-depth arm control) |
| **M2M/CMP seam-class intake** | `session_01GbRk4t1DpRB4c7ezEA3qhB` | **REVIEW_READY** — miso-176's intake half |
| **CAISO backcast reverification** | `session_01JT8oJbCULufoFnQzW6tt4K` | **REVIEW_READY** |
| CAISO backcast re-verification (earlier) | `session_01PM6PoVGKSFHGQtP3fgKKiJ` | COMPLETED — the caiso-209…213 rest chain |
| **NYISO benchmark root cause** | `session_014UYhUf2gqptZeGSZFnLvep` | COMPLETED — **nyiso-149, #4180/#4183** |
| CAISO C3a/C3c compression | `session_015iqE2vmnA68XhDjDKP5wgf` | COMPLETED |
| MISO seam-envelope hour-key | `session_0156vX9YySmncMw8gpFrrwv8` | COMPLETED — **miso-175 promotion** |
| NEISO 2019 scoring inputs prep | `session_01XQKk26kNqgzhcT5FCVZgFg` | COMPLETED — **neiso-101** |
| *(WS5 site-facts pass 2, #4187/#4191)* | *not in the 40-row page* | **COMPLETED** — merged; the page's floor is 2026-08-15 and this lane's rows fall outside it |

**Live remote branches** (complete set at this pin, `git ls-remote --heads`):

| Branch | SHA | Read |
|--------|-----|------|
| `main` | `94fafba` | tip (merge of #4198) |
| `claude/ercot-2023-summer-scarcity-9lg3nm` | `14ce4ce` | **🔴 UNMERGED, NO PR OPEN** — ercot-227, pushed 2026-08-22 14:25 UTC. **Carries the matrix-gate category repair** (owner queue rank 0) |
| *(this lane's branch once it pushes)* | — | board v11 + §8 entry |

**ONE genuinely unmerged remote branch, and it matters** — verified by
`git merge-base --is-ancestor`, which returns false for `14ce4ce`. v10 recorded
zero unmerged branches and warned that **a branch-only read now understates the
program**; v11 shows the opposite failure mode is also live — **`list_pull_requests`
returns ZERO open PRs while an unmerged branch holds the fix for a red CI gate.**
**Neither instrument alone sees the program. Read both, every cycle.**

## Refresh protocol

On each owner "refresh", the director: (1) lists sessions + fetches fresh
`origin/main`, re-reads plan §8 and lane handoffs; (2) reports each workstream
as **not started / in progress with % / completed / pending blockers**;
(3) issues prompts for any lane whose gate has cleared, appends the §8 ledger
entry, and updates this board in the same pass.

**v9's lesson held for a third cycle and earned its keep again.** *"A records
lane that transcribes a director read is a liability on a program whose lanes
merge hourly."* At v11 the dispatch was wrong on **four** counts — and, unlike
v10, **two of them are internal contradictions rather than staleness**: the
dispatch asserts zero promotions while naming two 2026-08-22 keepers in its own
facts 5 and 6, and it asserts a four-cycle session-read failure that its own
predecessors recorded as three consecutive successes. **A stale fact is a timing
problem; a self-contradictory fact is a drafting problem, and the fix is
different.** Keep the verify-against-HEAD instruction in every records prompt —
and read the dispatch against itself before reading it against HEAD.

**v11 adds three protocol amendments, on top of v10's two (check the live session
roster before declaring a lane unlaunched; pin the read and say so):**

- **🔴 RUN THE GATES, NEVER QUOTE THEM.** The dispatch reported WS6 parity green
  from a prior read; it is red, and a second gate the dispatch does not mention
  is red too. **Both were found by executing the scripts, in ten seconds each.**
  A board that reports gate state it did not run is asserting exactly the kind of
  unverified claim this program exists to catch. **Every gate on this board is
  now run at the pin.**
- **🔴 READ BOTH INSTRUMENTS: `list_pull_requests` AND `ls-remote`.** Zero open
  PRs is not zero outstanding work. At this pin an unmerged branch holds the fix
  for a red CI gate with no PR open for it — invisible to a PR-only read, and
  invisible to a session-roster-only read. v10 established that branch state
  understates the program; v11 establishes that PR state does too.
- **🔴 WHEN A CONTENT-ADDRESSED IDENTITY EXISTS, READ IT BEFORE INFERRING.** The
  director spent three cycles on a hypothesis that one hash read refuted
  (change 4). **Circumstantial convergence is not evidence when identity is
  available.** This is now a standing check on any "which change moved X?"
  question: **is X content-addressed, and did anyone actually look?**

**Under the standing deviation, step (3)'s two write duties are dispatched to a
records lane rather than pushed by the director.** A refresh is not complete
until that lane has landed both files — and, per the v5→v6 gap, a dispatch that
is never launched leaves the board silently wrong. **Verify the landing before
declaring a cycle done.**

**While the program is parked, the refresh cycle is not the live instrument it
was.** A park-period refresh should confirm only (a) whether the golden tier is
proven green **in CI** after the #4071 fix, (b) whether the owner has ruled on
anything in the owner queue, and (c) whether the keeper freeze has been called —
that last one is the un-park trigger. **At v11, (a) is ANSWERED AND RETIRED — the
tier is parked and the proof will not be spent, so this leg of the park-period
check is closed and should not be re-run**; (b) has moved for the first time in
three cycles (the golden-tier ruling itself, plus two new cards awaiting
signature); and (c) is unchanged, **but the ask has changed shape** — the freeze
and the golden tier's disposition are now one decision.

## RESTART CHECKLIST — for whoever un-parks the program

**Do these in order. Do not start at change (a).**

0. **🔴 NEW — GET `main` GREEN FIRST.** Two CI gates are red at `94fafba`: the
   rule 26 matrix guard (fix pushed and unmerged at `14ce4ce`) and WS6 parity
   (five NYISO `nyiso151_*` dirs from a lane that is still running). **Nothing
   else on this checklist is verifiable while CI is red** — G2 leg 2 explicitly
   requires a completed fast-tier-green `ci.yml` run, and it is unobtainable at
   this pin.
1. **DECIDE THE GOLDEN TIER AND THE FREEZE TOGETHER.** The precondition, not a
   nicety — and at v11 it is **two decisions that must be made as one.** A freeze
   buys re-captured goldens; **a parked golden tier means those captures cannot
   be certified byte-green**, so the freeze alone leaves G2 leg 1 blocked.
   Un-parking the tier costs one `workflow_dispatch` (billed minutes, which is
   why it was parked). **Do not wait for a cheap calibration window; there has
   not been one in nine cycles and this cycle produced three promotions with two
   ISOs deliberately resting.** Consider a **scoped, time-boxed** freeze.
2. **Re-verify every stage-0 golden against the then-current keepers** before
   resuming any change. Do not trust this board's staleness table — re-read
   `frontend/data/backcast/keepers/<ISO>.json` and
   `results/regression-goldens/perfb-stage0/manifest.json` at that HEAD and
   re-derive it, **mapping captured bundles back through the registry sidecars'
   `bundle` field** rather than by name (three of the five captures are against
   bundles whose runs are not the registered id you would guess). **At `94fafba`
   the answer is that ALL FIVE captures are stale and PJM was never taken.**
3. **Assume every re-capture is a real solve.** The gaps are wider than at v10:
   MISO is **seven** promotions past its capture, NYISO **six**, ERCOT four,
   NEISO two, CAISO one. The **re-stamp-not-re-solve** shortcut was established
   for **neiso-97 only** and NEISO has since moved to neiso-99 — **re-establish
   it before relying on it.** Apply the sidecar-comparison test per ISO before
   spending a solve, but **re-derive the config diff first**.
4. **Capture PJM FIRST.** It is the one ISO with no golden at all **and** the one
   whose keeper has not moved in three cycles — simultaneously the largest
   coverage gap and the cheapest capture. That combination has now held across
   three consecutive boards without being taken.
5. **Do NOT re-do change (c).** It landed via #3964 and is byte-identical at HEAD.
   Verify the blob (`af34031c`) rather than re-porting it.
6. **Close the #4054 residual if you want belt-and-braces** — but **re-derive it,
   do not inherit it.** The NYISO keeper has moved **six promotions** past the
   captured nyiso-140 config.
7. **Then, and only then, resume changes (a)–(e)** — and re-read the G2 leg list,
   because *merged byte-green* is what the gate wants, not captures.
8. **Confirm the golden tier is green IN CI before claiming any byte-green
   result** — which now requires un-parking it (step 1). A tier that cannot
   provision `data/clean` cannot prove byte-identity of anything, and a local
   replay is not the gate.
9. **Fix the parity gate's CLASSIFIER, not its symptom.** 5 dead dirs at v11, all
   NYISO, from a **running** lane. The 2026-08-20 repair diagnosed this correctly
   — pre-registered recipes and in-flight controls both legitimately precede any
   sidecar — and then **allowlisted two dirs by name instead of building the
   class-level carve-out it recommended.** That is why the gate re-reddened three
   days later, and why it will re-redden on the next A/B. **Build the carve-out;
   it is a ~10-line change and it retires a recurring red for good.** Explicitly
   **not** a pre-merge check, which would penalise correct pre-registration.

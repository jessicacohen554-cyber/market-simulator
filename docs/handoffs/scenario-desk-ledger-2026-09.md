# Scenario Readiness Desk — Ledger

Standing coordination ledger for the SCN track, implementing
`docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` ("the plan"). Maintained by the
desk session; one refresh = one commit = one small PR. The desk charters lanes and tracks
state — it never solves, never edits `src/market_sim/` or `scripts/`, and never charters
backcast-calibration work or anything on the capacity-expansion director's queue
(`docs/handoffs/capx-director-ledger-2026-08.md`), which it deconflicts with at every refresh.

**CROSS-DESK NOTICE (SPP-21, 2026-09-06, branch `claude/spp-21-matrix-shard-ti2gy3`):** SPP shard exists from this commit — **seven** shards; every rule-28(c) cell line now includes SPP. *(A self-referential sha cannot be written inside its own single commit — G2 requires one — so the lane and branch are the citation; `git log --grep=SPP-21` resolves the sha.)*

**Charter date:** 2026-09-05 · **Last refresh:** 2026-09-07 (refresh #18) ·
**r#18 am.2 — THE POLICY BOARD, GRADED BY REGISTERED ARTIFACT AT `b52e4035`, AND ONE PROMPT PER ISO.** Owner: *"Just create prompts for each iso in one codeblock I am not going to copy paste two things per iso"* + *"NEISO and PJM are running in sessions and a bunch of ERCOT landed"* + *"I didn't launch miso or Caiso."* Graded by sidecar, not by claim — 13 registered policy legs on main: **ERCOT 11 of 11, LEGS COMPLETE** (all-clean, carb-hi/lo/mid, carb-mid+load-hi, ces-p10/p20/p30, ces-p20+vol-hi, ces-t80, vol-hi) and owing only gate scoring, the FINDING, §5.1 and its matrix cells; **NEISO 2** (vol-mid, vol-hi) of 9; **PJM 4 legs SOLVED INTO `results/` BUT ZERO REGISTERED** (CARB-MID+LOAD-HI, CES-P10, CES-T80, VOL-MID) — a real gap against the charter's *register + declare in the SAME commit*, and the first thing PJM's prompt orders; **NYISO 0 policy legs** (its two `results/` entries are the REF and LOAD-HI rematerializations, not cases); **CAISO and MISO NEVER LAUNCHED** (owner-confirmed — the r#18 note that they were "issued" is corrected to *issued-unlaunched*). **The S15 and S16 addenda are FOLDED INTO ONE PROMPT PER ISO** rather than pasted beside a charter: two pastes per lane was the defect the owner named, and a lane that gets a charter plus two addenda has three chances to run the wrong one. Each ISO's prompt now states that ISO's own remaining work, its own shard width from the §5.5 table, and — for ERCOT — that it is the **unmasked control** under S15 (no `STATE_RPS_ACP` row, so step 1 adds no `CES-P60` leg and the null it reports is what the five masked ISOs are compared against).
**r#18 am.1 — RULING S16: THE PER-ISO POLICY LANE IS A COORDINATOR THAT LAUNCHES ITS OWN SHARDS, AND A SHARD IS SIZED TO UNDER ONE HOUR OF LP.** Owner instruction, verbatim: *"I don't want to run all of these in one session per iso though that's way too much compute and we have effectively unlimited ability to run lps in parallel so the per iso session should launch shards itself"* and *"Update those prompts accordingly to launch individual sessions for runs to target <1 hr of lp solve per session."* **This is codification, not invention — three of the four running lanes had already converged on it independently**: ERCOT wrote `SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md` (four groups G1–G4, each its own container, run ids and keys tabulated for the solver), PJM split into S2/S3/S4/S6, NYISO fanned nine legs across four containers. v7 standardises ERCOT's protocol, which is the one that already works, rather than a new scheme. **The sizing is DERIVED, not chosen** — from the Stage A-LOAD synthesis §8's own measured min/solve-year per ISO, at 5 solve-years per leg and a 60-minute LP budget: NEISO 1.09 → 10 legs/shard · ERCOT 1.30 → 9 · NYISO 4.06 → 2 · CAISO 4.33 → 2 · MISO 5.23 → 2 · **PJM 7.90 → 1** (and PJM's within-window profile is super-linear, 6.5/2.3/4.7/14.0/20.9 min across 2026–2030, so one PJM leg is ~48 min of real LP and a second would blow the budget). A shard also pays ~20 min of fixed setup (hydrate + `uv sync` + `regenerate_clean`), which is wall, not LP — so a shard is **filled toward the budget, never split below about half of it** unless the surviving leg count forces it. **The rule-12 reading, stated precisely so no lane over-reads it:** rule 12's *"cap at ~2 simultaneous runs … to stay within memory limits"* is a **per-container memory constraint**, and shards are separate containers with their own 15 GB, so it does not compose across them; what is untouched and still binds is rule 12's **within-invocation** half — one solve at a time inside a shard, years always sequential. That is exactly what ERCOT's protocol already recorded under the owner's own parallel-session instruction (ADDENDUM A(d)). **S14 is not withdrawn but is largely superseded in practice**: its ≤2-concurrent cap governed solves sharing one box, and the campaign no longer runs that way. **Duty split, which is the substance of v7:** the per-ISO session keeps everything that must be decided once and centrally — phase 0, the PRECOMMIT, the keys, the kills, gate scoring, the FINDING, the plan/ledger rows and the matrix cells — and a shard does **only** solve → register → declare, writes no docs, and reports in its final chat message. → **charter v7 and the shard template are §5.5**; the S16 addendum is pasted to the four running lanes and stapled to CAISO's and MISO's v6. The **S15 `CES-P60` leg is folded into the shard plan** as one more leg wherever step 1 shows the mask binding.
**r#18 (HEAD `96a6c4b3`):** **SCN-WS5A-RESOLVE IS COMPLETE — 13/13 — AND THE POLICY HALF IS RUNNING IN ALL FOUR ISSUED ISOs.** RESOLVE's headline: **the campaign's CO2 levels were overstated by up to 57 %, and the repair does not cancel out of the deltas**; every leg gated 5/5, re-registered under its original run id with the pre-fix artifacts deleted, 2026/2027 byte-identical to pre-fix on every fuel (the empirical proof D77 and D65-B are confined to 2028+). CAISO and MISO closed 3/3 each with their own FINDINGs, so **CAISO and MISO policy now meet P1 and are ISSUED on v6**. Policy progress: ERCOT 3/11 (CARB-LO/MID/HI) with ADDENDUM A and a sub-lane solve protocol; PJM 4 legs (CES-T80, CES-P10, VOL-MID, CARB-MID+LOAD-HI), 13 of 13 cases surviving phase 0; NEISO 2/9; NYISO 0 legs but REF and LOAD-HI rematerialized at the pin with G13 PASS and nine legs fanned across four containers. Audit **EXIT 0** (115 sidecars / 1,610 records / 112 declared FAILs).
**THE REFRESH'S FINDING IS STRUCTURAL, TWO LANES FOUND IT INDEPENDENTLY, AND IT REACHES EVERY ISO BUT ONE.** The entry screen folds attribute prices as `attr = max(effective_eac_price_for_tech(...), rps_credit_for_zone(...), _clean_credit_for_tech(...))` with **no fuel gate on the RPS leg** (`new_entry.py` ~:1132–1143, read at HEAD by this desk, not inherited). So wherever a state RPS row sits at its escape price, **a federal CES premium below that price adds exactly nothing to entry revenue**. NEISO measured `rps_dual = 50.0` in 5 of 5 years in REF, VOL-MID and VOL-HI alike, and its `VOL-HI`/`VOL-MID` pair came back **byte-identical in every reported scalar, fuel and capacity column in all five years** — a pure WTP-ceiling ladder with no volume confound (NEISO's `E_DC` is exactly zero) that produced no response of any kind. PJM's phase 0 flagged the same thing independently: *"PJM's $45 RPS ceiling dominates two chartered axes."* **The desk's cross-ISO read, which is the part neither lane could see:** `STATE_RPS_ACP` = MISO 30, NYISO 40, PJM 45, CAISO 50, NEISO 50, **ERCOT absent** — so the campaign's committed CES premium ladder {10, 20, 30} sits under every one of them, the voluntary ceilings {$4.50, $7.00} sit under every one of them, and `CES-T80`'s ACP $50 **ties exactly** on CAISO and NEISO. **The CES premium axis therefore cannot discriminate on entry in five of six ISOs at the committed levels, and ERCOT — the one unmasked ISO — is the one whose REF is adequacy-collapsed.** This is not a defect: it is rule 19 `[R-ONE-MECH]`'s `max()` attribute doctrine working as designed, and it is economically right (attribute revenue is a max, never a sum). The retirement screen's RPS leg **is** fuel-gated to `_RPS_ELIGIBLE_FUELS = {wind, solar}` (`retirements.py` ~:3509–3516, also read here), so a premium paid to `gas_cc_ccs` or nuclear is **not** masked there — which is why the CES legs are not byte-identical, cannot be killed at phase 0, and still solve. → **CARD D-12 RULED — S15: add ONE bracketing leg above the mask.** `CES-P60`, one common level for every ISO, above the footprint's highest published ACP ($50), set from published ACPs and never from a residual, and deliberately **not** per-ISO so it cannot become the per-ISO fitting rule 25 `[R-ISO-SCOPE]` forbids. ~5 legs / ~100 min LP. It converts a null into a measured threshold and, decisively, **falsifies the alternative reading that the CES row simply is not wired** — which is the reading an expert would otherwise be entitled to.
**GOVERNANCE MOVED UNDER US, TWICE, AND NEITHER IS THIS DESK'S ACT.** (1) **`complete` is now {ERCOT, NEISO, PJM, CAISO, NYISO}** — CAISO (`caiso-260-b1-demand`) and NYISO (`nyiso-202-startup-aware`) were re-declared by the owner's own lanes (`1c6d6665`, and caiso-261 the same day). Only **MISO** is now outside it. That widens §2.1b leg (a) for five ISOs and materially changes the Stage-B picture the D-5 card will be re-presented against — **disclosed, not acted on; this desk declares no marker.** (2) **SPP exists as a SEVENTH matrix shard** (capx cross-desk notice, SPP-21), so rule 28(c)'s "a cell line in every shard" is now seven, not six. No SCN charter is affected — every SCN duty is *"your ISO's shard"* — but a successor writing a base-row duty must count seven. **D-5 stays HELD under S13**: RESOLVE has landed, the policy half has run ~9 legs of ~40 and has not. capx r#53 deconflicted (D65-B-R board write, D75-R-ARM armed PJM's VRE devintage, D78-R3 → Q56 ARM): all PJM-heavy `src/` and board work, no SCN file collision, and the compute slot is governed by S14.
*(previous)* **r#17 (HEAD `28fb1882`):** **THE POLICY HALF IS LIVE — SCN-WS5A-POLICY-ERCOT LAUNCHED, PUSHED ITS PRECOMMIT BEFORE ANY LP, KILLED 2 OF 12 CASES AT ZERO COST ON PROVEN IDENTITIES, AND CAUGHT TWO DEFECTS IN THE CHARTER I WROTE.** Its phase 0: `VOL-MID` slack in all five years (eligible 197.3–234.9 TWh vs V = 80.3–198.5, thinnest margin +36.4 TWh) and `CAP-STATE-TIGHT` resolving to **no carbon program at all** (`CAP_AND_TRADE_PROGRAMS.get("ERCOT")` is None and returns before `mass_cap_enabled` is read) — both byte-identical to REF, both killed; the carbon ladder reproduced its declared table to the cent (G1 passed pre-LP) and 2026 is byte-identical in all five carbon-bearing arms. **RESOLVE SPLIT INTO THREE PARALLEL LANES** (`-post-d77`, `-caiso`, `-miso`) and stands at **6 of 13** — PJM REF landed with **all five gates PASS** (G1 1/6/6 units to 1e-9; 2026/27 to the digit on CO2 and price) and, against its own PRECOMMIT, **measured the PJM D67-ARM/D81 confound INERT** (every capacity row identical in all five years; the backstop is rate-capped at −16 % reserve margin, so moving the requirement operand cannot move a clamped build) — a correction in the lane's own favour. 2030 CO2 470.46 → 463.04 Mt, attributed **between** D77 (accounting) and D65-B (the capture VOM adder 8.0 → 2.95 pulling 11.3 TWh of CCS in ahead of dirtier gas) rather than assigned wholesale to the seam repair. CAISO and MISO PRECOMMITs are pushed, 0 legs each. → **PJM policy is UNBLOCKED (P1 met); charter re-cut as v6 and pasted for NEISO, NYISO, PJM.** **CARD D-11 RULED — S14: relax P4 to rule 12's own ~2-concurrent cap**, so ERCOT's **eleven** prepared legs solve alongside RESOLVE instead of behind seven heavy ones. **TWO CORRECTIONS AGAINST THIS DESK, BOTH FROM THE ERCOT LANE:** (1) r#16 recorded RESOLVE as having "re-solved IN PLACE … an accepted deviation from the charter's `-r2` out-dir" — **it did neither**; git shows every leg *renaming* its slim artifacts `scn-campaign-load-2026-09-06/<ISO>/<CASE>/` → `…-r2/<ISO>/<CASE>/`, exactly the charter recipe. The misread was of PRECOMMIT §4.1, which is about the **driver** (`run_ces_leg.py`, because `run_full_horizon.py`'s `--out-dir` redirect is unreachable from a campaign leg) and not about the out-dir, which §4 item 1 declares separately. Left standing, charter P2 would have sent five lanes to a path main does not carry — for CAISO/MISO it would have found the **stale pre-fix bundle**, which is the exact hazard RESOLVE exists to defeat. (2) G7's WTP ceiling `$4.5/MWh` is the **mid** cell; every surviving voluntary leg runs `high`, ceiling **$7.0/MWh** — S9's level is untouched, the charter named the wrong one of two committed cells. Both fixed in v6. *(Note that §4's collision register had the `-r2` tree right all along — it was §0's prose that drifted, which is why a lane reading only the summary line would have been misled.)* **TWO RECORDS ITEMS from the same lane's §9, logged not chartered:** (3) the campaign YAML's ERCOT tail-regime block still narrates a **122 GW** 2030 DC anchor against the pin's **88,603 MW** — prose only, no level depends on it, and SCN-WS5A-LOAD's P-1 already recorded the consequence, but it *reads* as a level; it joins the stale voluntary/cap comment blocks (post-S9/S10/S12) as one cheap words-only cleanup a future FIX lane should sweep together. (4) **`VOL-MID` is inert on ERCOT across the whole T1-F window**, not merely at the 2026 T0 WS-3b measured — so ERCOT can never produce a live mid-voluntary reading, and the thing that would change that is **D-3c's crediting leg** (new-builds-only rather than all-eligible), which is still OPEN. Worth carrying into D-3c's next presentation as evidence the card now has and did not before. Audit **EXIT 0** at HEAD (104 sidecars / 1,456 records / 97 declared FAILs). Marker unchanged: `complete` = {ERCOT, NEISO, PJM}. capx r#51 deconflicted: its whole queue (D78-R3, D75-R-ARM, D76-P3, the D65-B-R batch) is PJM-heavy `src/` and board work — no file collision with any SCN region, and the only contention is the compute slot S14 just re-scoped. **AMENDED SAME SITTING (owner: "ERCOT session closed reissue"):** the r#17 release note is WITHDRAWN unissued and ERCOT is **re-issued as the v6-RESUME charter (§5.3)** — a resumption standing on its committed PRECOMMIT, not the v6 template, which would order a finished phase 0 repeated; stem `claude/scn-ws5a-policy-21mq1y` is BURNED. Grading that PRECOMMIT by content for the resumption turned up **a third correction, and this one is the lane's**: its §2 case table carries **ELEVEN** `SOLVE` rows with eleven distinct keys, while the sentence beneath it and its §7 budget both say *"10 legs / 50 solve-years"* — an off-by-one from counting `CAP-STATE-TIGHT` as killed against a denominator that never contained it. **The table wins: 11 legs, 55 solve-years.** This desk had propagated the "10" into §0, §1, §2 and the plan before catching it; corrected everywhere in this commit, and the resumption charter tells the lane to solve eleven and re-scale its own budget. A lane trusting the sentence over the table would have silently dropped a leg. **Cards still open and dormant: D-1(b), D-1(c)** (the latter now with SCN-CAP's PJM regional-RGGI fallthrough as new evidence, and a PJM policy lane about to phase-0 test it); **D-5 correctly still held under S13** — RESOLVE owes 7 legs and the policy half has run none.
*(previous)* **r#16 (HEAD `00cee150`):** **SCN-WS5A-RESOLVE IS RUNNING — PRECOMMIT + 5 of 13 legs on main, ALL FIVE GATES PASS on every leg.** THE PIN is `bdfb3095`; G-DRIFT 34 commits, four LIVE (D77, D65-B ISO-wide; **D67-ARM and D81 on PJM only — a correction to this desk's r#14 'INERT' note, the ISO's own default arms it**); **the cache blocker is defeated by construction at the pin** — D65-B re-keys every config — so the lane re-solved IN PLACE with `run_ces_leg.py` (a stated, accepted deviation from the charter's `-r2` out-dir). **Ruling S5's paired check is now measured on the campaign REFs**: G1 identity to 1e-9 on 13/36/37 converted NYISO units and on NEISO's; 2026–27 identical to the pre-fix bundles; NYISO 2030 CO2 26.31 → 14.17 Mt (−46 %); the DC-shape axis survives the repair; prediction P-B hits on NYISO. → **the ERCOT, NEISO and NYISO policy lanes are LAUNCHABLE NOW under charter v5** (P1 met for those three; PJM/CAISO/MISO wait for their re-solved REF); rule 12 sequences their solves behind RESOLVE's heavy legs. capx D79 phase 1 landed AFTER the pin (the fingerprint is in `cache_key()`; CLAUDE.md +8) — pinned lanes are unaffected. Audit EXIT 0. No card.
**r#15 (HEAD `e6a0402f`):** quiet again — 13 commits, all capx (r#50 + am.1: D67-ARM armed PJM, D78-R exact, D81, D76 phases 0–1, **D79 → Q54 ADOPT (frozen-hash fingerprint) — the cache-key hazard this desk routed at r#10/r#11 is now a program mechanism**; D65-B-R's batch STILL running, so the per-plant slot is still taken). **SCN-WS5A-RESOLVE undispatched for a SECOND refresh** — under the charter's two-refresh threshold this reads LOST, but the r#5 standing rule (ask before grading lost) and the capx director's own r#50 lesson ("a timing artefact of the owner's batching, not a lost prompt — the third emission was wasted") both say otherwise: **status ASKED, the charter re-emitted verbatim, not relaunched under a new stem** (the stem is unburned because nothing was ever pushed to it). Policy lanes correctly unlaunched. Audit EXIT 0. Marker unchanged. No card.
**r#14 (HEAD `5375be8b`):** quiet on the SCN side — r#13 + am.1 merged (#5165); **SCN-WS5A-RESOLVE not yet dispatched** (one refresh; asked, not graded); the policy lanes correctly unlaunched (P1 absent); the audit stays EXIT 0. The delta is the capx track's (79 commits): **D65-B-R's batch, D78-R's two legs and D81's full window are all SOLVING now** — the queue is saturated, so **rule 12 makes RESOLVE's PJM/CAISO/MISO legs wait for a slot**: one sentence added to its charter (confirm no other per-plant solve before each heavy leg; NEISO/NYISO may start any time). CLAUDE.md gained one line (capx D67-ARM: the PJM published adequacy requirement) — INERT for every SCN leg (a `{iso: bool}` gate no campaign case sets); D75-R and D76 added default-off fields — RESOLVE's G-DRIFT classifies them. NYISO promoted to nyiso-202 (CALIBRATED), marker unchanged, §2.1b NEISO only. No card; nothing new issued.
**r#13 am.1 — RULING S13 (D-5) = HOLD until SCN-WS5A-RESOLVE and the policy half land.** No Stage-B grant; nothing full-horizon is chartered; D-5 is re-presented the refresh both are on main, with the amended cost table and the post-fix NEISO REF. The only lane to launch now is SCN-WS5A-RESOLVE.
**r#13 (HEAD `13ee0c89`):** **STAGE A-LOAD IS COMPLETE AT THE FROZEN PIN — 16/16 legs, the synthesis, the D-5 cost table (313.7 min of LP, 3.92 min per solve-year, ~4.7 h wall) — and RULING S8 WAS NEVER EXECUTED**, because its amendment had no session to land in (the desk's third addendum-to-nobody in a day) and the lane finished at its own freeze, correctly; it scoped the re-solve for the desk (13 of 16 legs) and named the blocker the desk missed: **D77 moves no key, so a naive re-solve hits the pre-fix cache** → **SCN-WS5A-RESOLVE issued** as a standalone lane (new out-dir per ISO redirecting `CACHE_ROOT`, a per-leg cache-hit proof, the S5 identity reproduced on the campaign REFs, same-id re-registration). **SCN-FIX2 and SCN-CAP both LANDED complete**: the carbon form is the committed path ladder (and CARB-HI is LIVE on NYISO/NEISO at full horizon, 2031–2047 — a Stage B fact), the voluntary levels are relabelled committed, `mass_cap_tons_by_year` ships inert and `CAP-STATE-TIGHT` binds on NYISO and CAISO in every year and is slack on NEISO; PJM is NOT byte-identical under the case (partial RGGI fallthrough) — the policy charter is re-cut as **v4** with that fixed and P1 pointing at the RESOLVE PRECOMMIT. capx D80 landed: the audit is **EXIT 0 on main**. **Card D-5 PRESENTED** with the cost table and a HOLD recommendation (gate Stage B on the re-solve and the policy half).
**r#12 am.2 —** owner: "I don't have any forecast sessions going for prompt 3." Correct — the six policy lanes were never launched (gated on P1), so the cap addendum had no target; **WITHDRAWN**, the cap case folded into the ONE combined policy charter (v3, §5) as case 13 under P5 with gates G10–G12. Standing rule from r#12 am.2: **the desk issues addenda only to lanes that are verifiably running; anything for an unlaunched lane goes into its charter.**
**r#12 am.1 — RULING S12 (D-2(c)) = COMMIT THE 80 % SLOPE AND BUILD THE FIELD** → **SCN-CAP issued** (Fable, zero-LP: `mass_cap_tons_by_year` read first in `_power_sector_cap`, the `CAP-STATE-TIGHT` case per WS-1a §4.2, backcast-inert, matrix row + six cells) and a CAP addendum to the three program-ISO policy lanes (case 13, gated on P5, gates G10–G12; killed at phase 0 where the budget is slack in every year). Every §3.5 case is now inside Stage A.
**r#12 (HEAD `ba894c9c`):** **SCN-FIX1 LANDED ITS FIRST TWO ITEMS AND TURNED THE Y-24 AUDIT GREEN FOR SCN** (30 → 8 undeclared, the 8 all capx's; the collate defect found to flip the SIGN of the six-ISO delta on a filling campaign, repaired as a strict no-op on well-formed rows) — but it ran on the r#10 charter, so the carbon-form switch and the S9/S10 relabel (issued on the unmerged #5124) never reached it → **SCN-FIX2 issued**, and the policy lanes' P3 still fails at HEAD; recorded against the desk · **capx D80 cross-checked the same 22 declarations byte-identically** and answered the forensic question (no second namespace writer; a pre-ratchet base rebased forward) · **SCN-WS5A-LOAD at 12/16, MISO complete, and the lane's own D-10 scope correction (13 of 16 legs re-solve) is the reading r#11 already recorded** · capx D79 charters the solve-surface fingerprint this desk routed twice (D77 §4c) — discharged there · the policy lanes are gated on ADDENDUM 2 + P3 and not yet dispatched (expected) · **CAP-STATE-TIGHT is one ruling and one field away → card D-2(c) PRESENTED** · D-5 held.
**r#11 am.2 —** owner instruction: the voluntary addendum is FOLDED INTO the policy-lane template (one paste per ISO); the combined text in §5 is the issued charter, the separate addendum is withdrawn unissued. Gates renumbered G1–G9 (the former G9 footprint clause merged into G3). No ruling, no scope change.
**r#11 am.1 — THREE RULINGS, S9 / S10 / S11, AND THE VOLUNTARY LEGS JOIN STAGE A-POLICY.** S9 (D-2(b)): the WS-3b placeholders ARE the committed levels — `f_commit` mid 0.5, WTP ceiling $4.5/MWh. S10 (D-3c): the renewable-only eligible set stands as built. S11 (D-6): a voluntary MWh counts toward the federal standard; every combined leg reports both nettings. → the four legs (VOL-MID, VOL-HI, CES-P20+VOL-HI, ALL-CLEAN) are added to the six policy lanes by ADDENDUM (phase-0 regime test per year; a slack row is killed, never solved; gates G7–G10), and SCN-FIX1 gains item 4 (the relabel, words only; ALL-CLEAN's carbon form). CAP-STATE-TIGHT alone stays out.
*(previous)* **r#11 (HEAD `d1aa877f`):** **STAGE A-POLICY IS RELEASED UNDER S5** — capx D77 landed its FINDING with the identity gate PASS at model grain (every converted NEISO unit at `measured × 0.10` to 1e-9 in every year; NEISO 2030 CO2 13.37 → 6.95 Mt once dispatch re-orders), which is exactly the paired check S5 named; the six `SCN-WS5A-POLICY-<ISO>` charters are issued for phase 0 + PRECOMMIT with the first solve gated on the campaign's post-D77 pin (WS-5A ADDENDUM 2), the ISO's re-solved REF, and the carbon-form switch · **SCN-WS1b-r2 LANDED complete at 12/12** (PJM: 17.4 TWh of coal displaced by $3.75/t; three program ISOs exactly inert; the price-setting rate exceeds the load-following rate in 3 of 3) · **SCN-WS5A-LOAD at 11/16 falsified its own CCS claim: PJM carries 909.8 MW of `gas_cc_ccs` with no carbon program (§45Q alone), MISO 334.5 MW** — so under S8's own empty-ledger criterion PJM and MISO re-solve too and only ERCOT stands · **capx D65-B landed Acts A + B as one re-key event**, so the post-D77 pin is post-D65-B as well · the carbon FORM is still the desk's delta stand-in one lane after S2's floor landed — a desk-owned blocker → **SCN-FIX1 re-issued with the YAML switch** (no dispatch evidence yet; the audit backlog grew to 30 / 22 SCN) · VOL-*, the two combos and ALL-CLEAN held out of the release on the three open voluntary boxes → **cards D-2(b), D-3c, D-6 PRESENTED**; CAP-STATE-TIGHT out (level unruled) · WS-3c: no ISO meets both halves of its criterion yet · D-5 held · *records note:* r#10 am.1 (ruling S8) reached main only with this refresh — PR #5106 merged before its commit was pushed; the amendment itself was issued to the lane at the time.
*(previous)* **r#10 am.1 — RULING S8 (D-10) = RE-PIN ONCE POST-D77 NOW** → the SCN-WS5A-LOAD amendment is **ISSUED**: finish any mid-solve PJM/MISO leg at `1cc45bb2`, re-pin at or after the D77 merge with a hunk-by-hunk G-DRIFT, re-solve NEISO + NYISO (5 legs), solve CAISO at the new pin, keep ERCOT/PJM/MISO under the audit; the re-solved NEISO REF is S5's model-grain paired check, so **Stage A-POLICY releases the refresh it lands, no card**. SCN-FIX1 stands issued.
*(previous)* **r#10 (HEAD `6887484f`):** **THE CAMPAIGN FALSIFIED RULING S5's PREMISE, AND THE SEAM IT WAS HELD ON IS NOW REPAIRED.** SCN-WS5A-LOAD has three ISOs complete (8 of 16 legs) and measured **8.8 GW of `gas_cc_ccs` in NEISO's REFERENCE case** (6.5 GW in NYISO's) — the retrofit screen is armed by the STATE carbon program, not by the CES, so the load half was never uncontaminated for the three program ISOs' CO2 LEVELS from 2028 (NEISO 2030 overstated by 5.60 Mt = 41.9 %, NYISO by 5.29 Mt = 25.3 %; the deltas mostly cancel). capx D50 had published the asymmetry before S5 was written; recorded against the desk. **capx D77 landed the repair within the hour of ruling S7** (a `ccs_capture_fraction` stamp composed at both restoration sites; zero DOF; **no cache key moves, so every pre-fix bundle reaching 2028 with a retrofit is silently stale at its own key** — NEISO's and NYISO's five campaign legs exactly). Its NEISO screen and FINDING are owed → **card D-10**: re-pin once, re-solve the five contaminated legs plus CAISO, keep ERCOT/PJM/MISO under G-DRIFT · **ERCOT's shipped forecast REF is in deep shortage** (unserved 0.38 → 127.2 TWh by 2030, $4,438/MWh) — G-S4 at campaign scale, routed as priority · **SCN-WS3b LANDED COMPLETE** the day after S6 (three fields, the row, four S5-held YAML cases, 783 lines of tests, six `U` cells) and found the memo's ERCOT 2026 T0 instrument SLACK → SCN-WS3c HELD on a named criterion, not issued · **SCN-WS1b-r2: 5 of 6 pairs** (PJM and MISO 8/8; NEISO/NYISO exact identities; the price-setting rate exceeds the load-following rate 1.13–1.33× in all three live ISOs), closing PR #5101 open · **main is RED on the Y-24 forecast-invariant audit, 18 of 26 undeclared runs SCN's** → **SCN-FIX1 issued** (the declarations + the `collate_scenario_campaign.py` common-set repair, zero LP) · A-POLICY releases on the model-grain paired check with no new card; D-5 still not presentable; §2.1b NEISO only.
*(previous)* **r#9 am.1 — TWO RULINGS, S6 AND S7.** **S6 (D-8) = RELAUNCH NOW, THIRD STEM** → **SCN-WS3b-r3 ISSUED** (`claude/scn-ws3b3-voluntary-demand-q7mv`, Fable, zero-LP build, ready-in-waiting under S5). **S7 (D-9) = YES, NAME THE CCS EMISSION-RATE SEAM REPAIR AS THE CAPX DIRECTOR'S NEXT LANE** — an owner direction on the capx queue, recorded here verbatim and ROUTED to the capx ledger for the director's next sitting; this desk still charters nothing on it. Stage A-POLICY's release now has a named path, not a date.
*(previous)* **r#9 (HEAD `0e20e8cf`):** **BOTH RUNNING LANES ARE CHECKPOINTS, AND THE SEAM THAT HOLDS HALF THE CAMPAIGN HAS NO OWNER.** `SCN-WS5A-LOAD` merged only its pin re-audit — 20 new main commits, three solve-path hunks each classified INERT for a forecast leg with its reason, phase 0 bit-identical, the campaign **FROZEN at `1cc45bb2`** with 0 of 16 legs solved at the commit — so no synthesis, no cost table, and **D-5 is still not presentable**. `SCN-WS1b-r2` scored its first live pair, **ERCOT 2027: ARM NOT KILLED**, 7 of 8 gates PASS and G4 a reported miss (Δp/Δcarbon 0.5157 t/MWh, above the lane's own band); CO2 −0.928 Mt on a near-1:1 coal→gas swap with every zero-carbon class at exactly 0.0000 TWh; the leakage line reads 0.0 **by construction** (ERCOT has no import node), so the headline is an upper bound. Only PJM and MISO remain live at 2027 (the S2 floor makes the three program ISOs inert), so the lane owes two more pairs, not five · **ERCOT's forecast REF is ADEQUACY-COLLAPSED at 2027 in both arms** ($982/MWh, reserve margin −6.5 %, 4.6 TWh of slack over 641 h) — the known G-S4 defect measured a second time on a second lever; the CO2 delta is robust, the price delta is not campaign-grade, and every ERCOT Stage A-LOAD leg differences against this REF from 2027 on · **the lane found a design limit in its own pre-registered gate**: G8 tests a transition and cannot see a REF that is already broken → standing change #2, every paired-probe gate now asserts a REF-side precondition · **THE CCS EMISSION-RATE SEAM IS UNCHARTERED AT CAPX r#45** — named ('routed there, named here') but carried by no D-lane; D65-B is the VOM/fixed-cost arming, D74/D75 are other objects, and no commit has touched the emission-rate path since 2026-09-06. So Stage A-POLICY's release condition has no owner and no ETA; routed again as *unchartered*, and carried to the owner as **card D-9** · **SCN-WS3b-r2: no evidence of dispatch for a THIRD refresh** (no PR ever, no branch, and the session listing this desk can see is scoped to its own account — it cannot see WS-5A or WS-1b either, so absence there proves nothing) → **card D-8**, a third stem written and held on it · records repaired against the desk's own account: ruling S5's `RULED` line was never appended to plan §6 and §1's scoreboard had drifted five lanes behind §0 — both fixed here · capx: D62/D72/D66 landed (every one a negative), D60-R3 at leg 4/5 with a fired STOP, D67 INERT for every SCN leg, Q50/Q51 parked at owner direction, `complete` still {ERCOT, NEISO, PJM}; no HOLD.
*(previous)* **r#8 (HEAD `34f3ce35`):** **STAGE A-LOAD IS RUNNING** — `SCN-WS5A-LOAD` launched with its
PRECOMMIT pushed before the first solve, as **one lane covering all six ISOs** rather than the six
the desk issued; graded acceptable on content and recorded · **THE REFRESH'S FINDING IS A
CONSEQUENCE OF THE DESK'S OWN RULING CHAIN, AND NOBODY PREDICTED IT.** SCN-LOAD's intake —
ruling **S4**, which the owner granted **over** the desk's and SCN-WS4a's recommendation to defer
— landed `d14a7ed0` **after** SCN-WS4b's pin and re-derived the entire load-shape constant family
(**473 insertions / 263 deletions in `constants.py` alone**, covering `DEMAND_GROWTH_RATES`,
`DATACENTER_ADDITIONS_MW` and `ELECTRIFICATION_LAYERS`). **So the pre-declaration chain this
campaign is built on — WS-4b's six readings, and WS-4c's T0 scoring of them — was computed against
constants that have since moved.** Not invalidated: both were correct at their pins. But the
horizon HIT/MISS scoring now runs against a **moved target**, and that is said out loud rather
than absorbed. Measured pre-solve by the campaign lane, at zero LP: **CAISO's ORGANIC arm is no
longer degenerate** (`high` 4,240 MW vs `mid` 1,622 MW at 2030, from the CEC Form 1.1c the intake
read) so the campaign is **16 legs, not 15**; **PJM is now degenerate for a NEW reason** (published
B-9b overtook the retired 30 GW queue estimate); **ERCOT's tail regime is predicted NOT to
reproduce** (the DC high anchor fell 122 → 88.6 GW, −27 %, while the growth rate rose, so WS-4b's
1.019 TAIL ratio should land below 1.0 and relocate); and **G-DRIFT reads LIVE on every ISO, twice
over** — 82 files / +9,529 lines on the solve path *plus* the constant re-derivation — so rule
29(b) form 4 is invalid for all six and the control is the lane's own same-HEAD REF ·
**SCN-WS1b-r2 pre-registered SCN-WS4c's measured marginal rate as a second yardstick** — a lane
picking up another lane's finding across a refresh, which is the coordination actually working ·
**SCN-WS3b-r2: no evidence of dispatch across two refreshes and two asks.** It feeds only the
S5-held half, so it blocks nothing today; not re-issued unless wanted.
*(previous)* **r#7 (HEAD `e80bdd87`):**
**r#7 (HEAD `e80bdd87`):** **STAGE A-LOAD IS UNBLOCKED AND ISSUED — SCN-WS4c LANDED COMPLETE.**
19 arms (15 T0 + 4 T1-F), all solve clean, and SCN-WS4b's six pre-declared readings score
**20 HIT / 3 SPLIT / 3 MISS**. Two results outrank the scores: (1) **the fossil-average heuristic
this campaign's own charter used is systematically biased** — the implied marginal CO2 rate sits
**below** fossil-average wherever coal is inframarginal (ERCOT 0.73×, PJM 0.77×, MISO 0.65×) and
**above** it in every gas-dominated ISO (CAISO 1.05×, NYISO 1.05×, NEISO 1.17×), so the charter's
"CO2 rises ≈ fossil-average × added fossil-served MWh" is high by 23–35 % with coal and low by
5–17 % without — predictable in advance from one fact about the fleet; (2) **G-DRIFT was
vindicated by measurement, and it is evidence about rule 29(b) itself** — NEISO's REF T1-F does
**not** reproduce the committed `ff-t1f-d50` bundle, differing by up to **2.821 Mt (−18.8 % in
2030)**, so differencing against the committed bundle — **rule 29(b)'s stated DEFAULT** — would
have measured NEISO's entire deployment response against a stale reference. Routed ·
**SCN-WS1b-r2's phase 0 KILLED ITS OWN LEG 1 at zero LP cost — and the charter it killed was
MINE.** `CARBON_PRICE_PATHS` anchors every registered RFF path at **$0 in 2026**, so no
`carbon_price_path` value of any kind can produce a signal in a 2026-only solve; the arm is inert
in all six ISOs, not the three I predicted. **The desk RATIFIES the lane's 2027 scope call**
(`--end-year 2027`, still below `ccs_retrofit_available_year` and so still S5-safe) and records
the error against itself: r#6 am.1 retired the `carbon_price_delta` form as "no longer needed"
after ruling S2, when in fact it was **the only form that yields a 2026 signal at all** ·
**capx D72 measured the blast radius of ruling S2 and it is EMPTY** — D23 stands, re-examined and
upheld · SCN-WS3b-r2 still shows no branch — asked again, not graded lost.
*(previous)* **r#6, amendment 1:**
**r#6 am.1 — RULING S5 SPLITS STAGE A IN TWO.** D-7 is ruled: **hold the policy half, run the
load half now.** Stage A is no longer one campaign. **STAGE A-LOAD** — `REF` /
`LOAD-HI` / `LOAD-HI-ORGANIC` across six ISOs, plus the pure-carbon T0 probes **below 2028** —
has **no `gas_cc_ccs` exposure at all** and proceeds as soon as SCN-WS4c lands. **STAGE A-POLICY**
— every CES case, every carbon case at or above `ccs_retrofit_available_year` (2028), `ALL-CLEAN`,
and the `VOL-*` cases when they exist — **HOLDS until the capx CCS emission-rate seam is
repaired**. The ruling buys the campaign's uncontaminated half now and spends no LP twice.
**Routed to the capx director as a priority signal**: their CCS repair now gates half of a
chartered campaign, which it did not before. **The desk issues nothing on this ruling** — A-LOAD's
own precondition (SCN-WS4c) is still in flight, so the sequencing is recorded and the lane is
issued the refresh WS-4c lands.
*(previous)* **r#6 (HEAD `ad45b0e4`):**
**r#6 (HEAD `ad45b0e4`):** **ALL FOUR RULING-RELEASED LANES LANDED IN ONE DAY — and SCN-WS2b
found a defect that SIGN-FLIPS the campaign's headline answer.** Landed: **SCN-WS1c** (ruling S2
executed — the federal price is now a floor under the state program, matrix re-stamped, full-suite
parity accounted, and a second copy of the replace assertion found by parity), **SCN-WS2b** (the
ERCOT + NEISO ladders re-proved at HEAD, the national clearing script, the ERCOT/NEISO cells
re-stamped), **SCN-LEVELS** (S3 executed, `CES-T80` made live, levels measured to be the levels
the lanes actually ran), **SCN-LOAD** (S4 executed — six published ISO load forecasts curated as
the `load-forecast` datatype, with an obtainability-measured scope note pushed first) ·
**THE FINDING THAT MATTERS MORE THAN ANY OF THEM: a CCS emission-rate seam defect that INVERTS
NEISO's headline CO2 answer.** Retrofitted `gas_cc_ccs` units are credited at 0.95 by the CES
while carrying an **uncaptured** `emission_rate` in the dispatch fleet — measured on one unit
across its own retrofit year, `fuel_type` flips ✓, `heat_rate` rises ×1.12 ✓, and `emission_rate`
stays **0.3745 → 0.3745** ✗; three writes in one block of `ccs.py`, two persist, one is
overwritten downstream. As scored, the CES premium **raises** NEISO 2030 CO2 by **+9.99 Mt**; with
the intended 90 % capture applied at fixed dispatch it **cuts** it by **−6.01 Mt**. **This is a
capx-track file and not the desk's to fix — routed** — but it bears directly on the owner's actual
question, so **card D-7 is presented**: does Stage A run before it is repaired? · **SCN-WS4c is IN
FLIGHT** (PRECOMMIT, a zero-LP phase 0, harness and the first T0 slim artifacts) · **SCN-WS1b has
produced nothing for two refreshes and SCN-WS3b has never appeared — status ASKED, neither graded
lost**, per the standing change this desk made at r#5 after getting exactly that call wrong ·
**the CI-red SCN-WS1c routed is already GREEN** — the capx track discharged it; verified, not
assumed.
*(previous)* **r#5, amendment 1:**
**r#5 am.1 — FOUR OWNER RULINGS, RECORDED VERBATIM AS S1–S4, AND EVERY ONE OF THEM UNBLOCKS A
LANE.** **S1 (D-3) = YES**, a voluntary clean-demand scenario axis is admissible as a declared,
forecast-only, publicly-anchored axis — the ffr-5b ruling is held to be about a *fitted driver*,
a different admissibility class. **D-3b is settled with it: in-LP hourly 24/7 stays DEFERRED** to
the isolated portfolio tool (the owner took the recommended option, not the hourly-too variant).
**S2 (D-1) = FLOOR**, `effective = max(RFF path(year), program trajectory(year))` on a program
ISO — with the measured consequence accepted, that the floor makes `policy_bundle="tight"` an
exact no-op on CAISO/NYISO/NEISO rather than an increase. **S3 (D-2) = the plan's §3.5 table as
the committed default**, which converts SCN-WS2a's labelled-illustrative CES target
{2026: current, 2035: 0.80, 2050: 1.00} / ACP $50 into a committed level **with no re-solve**,
because the lane built and probed against exactly it. **S4 (D-4) = FUND THE FULL DATATYPE** —
this OVERRIDES the desk's and the lane's recommendation to defer, and it is the largest scope of
the three options offered. **ISSUED ON THE RULINGS: SCN-WS1c** (the floor repair, i.e. the WS-1a
item 1 the card gate withheld), **SCN-WS3b** (the voluntary build), **SCN-LEVELS** (commit the
§3.5 levels), **SCN-LOAD** (the full six-source load-forecast intake) · **Stage A's critical path
is now: WS-1b + WS-2b + WS-4c landing, and WS-3b → WS-3c landing.** D-3 no longer blocks it; it
schedules it · still OPEN: **D-3c** (the voluntary eligible set — the memo's box 3, which WS-3b
builds against the memo's recommendation and flags), **D-6** (attribute netting), **D-5** (the
Stage-B grant, correctly held until Stage A's cost table exists).
*(previous)* **r#5 (HEAD `3dcf1b22`):** **THE WAVE-2 SET IS ESSENTIALLY IN. SCN-WS4c IS UNBLOCKED AND
ISSUED — the last lane before Stage A.** Landed since r#4: **SCN-WS2a COMPLETE** (the NEISO T0
target-row pair registered, FINDING, and the matrix row + one cell per shard as its last
commit — every item of its charter), **SCN-WS4b** (both named cases, the six per-ISO
pre-declared adequacy readings, the `backstop-built` column + test), **SCN-MX-R-r2** (the CI
diagnosis, the epoch entry, and a correction to this ledger). **SCN-WS1b and SCN-WS2b are IN
FLIGHT with PRECOMMITs pushed before their solves**, exactly as rule 29 requires ·
**TWO CORRECTIONS THE DESK OWES, BOTH AGAINST ITS OWN RECORD.** (1) **r#4 graded SCN-WS4b LOST
and "never launched". That was wrong in fact** — the lane launched between r#4 and r#5 on
`claude/scn-ws4b-load-hi-adequacy-jvv96t` and landed complete. The r#4 call followed the
charter's two-refresh threshold correctly, but the threshold mis-fired, and the honest record
is *launched late*, not *never launched*. (2) **The desk asserted across r#2, r#3 and r#4 that
`check_mechanism_matrix.py`'s duty-(c) half "did not fire" because it exited 0. It DID fire and
it DID fail** — SCN-MX-R-r2 found job `101393800190` printing both `::error … not registered`
lines and exiting 1 on PR #4870, which was **created and merged five seconds apart with seven
red checks**, the guard not being a required status. The desk's three exit-0 readings were the
checker's **validate-only mode**, which returns before the registration leg exists in the
control flow and was never a registration verdict. The real defect is a merge-protection gap
plus a blind spot for any shared, forecast-only or keeper-unarmed field · **Stage-B picture
has widened and is not this desk's to move: THREE ISOs now hold CALIBRATED keepers while absent
from `complete`** — NYISO (my r#4 routing landed → capx card C-19/Q51 + D70, **Q51 ruled HOLD
ONE REFRESH**), MISO (C-17/Q49, **declined**) and CAISO (C-18/Q50, **hold until caiso-253**).
`complete` still reads {ERCOT, NEISO, PJM} · **CLAUDE.md changed under us**: rule 1 now carries
an **authorized offer-curve price-tuning carve-out**, rule 13 its one exception, rule 29 gains
clause **(c) DELETE BEFORE MERGE**, and a **new rule 30 `[R-TOUCHPOINT-FOLD]`** exists — all
four are written into SCN-WS4c's charter.
*(previous)* **r#4 (HEAD `21deb4a7`):** **NOTHING NEW IS UNBLOCKED BY CODE — and the one real unblock this
refresh is GOVERNANCE, is not this desk's to take, and nobody has taken it.** NYISO promoted
`2026-09-06-nyiso-196-extract-basis` — **CALIBRATED, grade 7, zero fails, C3c the lone ledgered
caveat** — and the withdrawal block's own re-entry clause reads *"re-entry is a NEW explicit
owner declaration on a keeper scoring CALIBRATED."* **That condition is now MET and the marker
has NOT been re-declared**: `complete` still reads {ERCOT, NEISO, PJM}, so NYISO's §2.1b leg (a)
is still FAIL and Q45's lapsed premise is still lapsed — **on a technicality that a single owner
declaration clears.** Disclosed and routed to the capx director per charter §0.4; this desk
declares no marker · **SCN-WS4b and SCN-MX-R are LOST** — issued r#2, re-emitted r#3, still no
branch and no PR at r#4, which is the charter's two-refresh threshold → **relaunched verbatim
under `-r2` stems, recorded never-launched against interest, NOT graded as running** ·
**SCN-WS2a's PRECOMMIT and docs legs merged** (#4892) but the probe, the FINDING and the CES
matrix row are still owed — the lane has PRs so it is not lost, it is owed · SCN-WS1b and
SCN-WS2b launched by the owner; no branches yet, which is expected within a refresh · the desk's
own r#3 PR merged (#4888), so the ledger conflict is closed · §2.1b gate unchanged **today**:
**NEISO only** — and NYISO is one declaration away from being the second.
*(previous)* **r#3 (HEAD `ea273339`):** **BOTH r#2 FINDINGS WERE SELF-CORRECTED BY THE LANES THEMSELVES,
BEFORE ANY r#2 PROMPT WAS DISPATCHED** — SCN-WS0 landed items 5 and 6 plus the G-E4 rider
(`e8c7072d`, `79034547`, `47ba0610`) and SCN-WS1a minted the `carbon_price_path` +
`policy_bundle` rows with a cell in every shard (`717de664`) and scored its CAISO T0
(`a147362b`). **THREE OF THE FOUR r#2 CHARTERS ARE THEREFORE WITHDRAWN UNDISPATCHED**:
SCN-WS0-R (its whole scope landed), SCN-WS2a-R (**SCN-WS2a IS LIVE** — two unmerged commits
on its branch, the docs leg and a pushed PRECOMMIT, so dispatching -R would build a twin),
and SCN-MX-R's carbon half. **SCN-MX-R survives NARROWED** to the one thing still unowned:
why `check_mechanism_matrix.py` exited 0 on a PR that added two `ScenarioConfig` fields with
no row · **the desk's r#2 PR conflicted on the ledger and is resolved here by rebuild** —
this refresh is r#2's record plus r#3's, on top of `ea273339`, with SCN-WS0's own §3 edits
taken over the desk's (better sourced) · **WS-0's T0 returns the campaign's first substantive
result and it is a CARBON-LEAKAGE number**: $25/t cuts NEISO's modeled in-ISO CO2 −2.71 Mt
(−16.6 %) while the reported import line rises **+1.85 Mt on a single NYISO rung**, so
**about two thirds of the headline reduction leaves the scored basis** — and at a CT-realistic
0.53 t/MWh instead of the 0.428 disclosure default the net shrinks to ≈ −0.42 Mt. Every
campaign delta must now be read with the import line beside it, per ISO · **ISSUED: SCN-WS1b
and SCN-WS2b (both newly UNBLOCKED by WS-0 item 5), SCN-MX-R (narrowed); SCN-WS4b RE-EMITTED
verbatim** (issued r#2, no branch at r#3 — one refresh, so NOT graded lost; dispatch status
asked) · no card ruled: **D-1, D-2, D-3, D-4, D-6 and the new sub-boxes all still OPEN** ·
§2.1b gate unchanged, **NEISO only**; no Stage-B lane issuable, none issued.
*(previous)* **r#2 (HEAD `db8b6015`):** **ALL FIVE WAVE-1 LANES LAUNCHED AND LANDED WORK — three complete, two
CHECKPOINTS.** WS-1a delivered items 2–4 + the Phase-0 table + the D-1 memo and **STOPPED on its
card gate exactly as chartered** — and its Phase 0 **proves G-C1 with a number**: `policy_bundle
="tight"` is a carbon-price CUT of **$16–$102/t in every one of 25 years** on CAISO/NYISO/NEISO,
and under the recommended FLOOR the RFF mid path **never once exceeds** a program trajectory, so
the floor makes `tight` an exact **no-op** there rather than a fix — a new D-1 sub-question, not a
new answer · WS-4a **complete**: ERCOT was already fully populated (the plan's "only for PJM" line
was stale), MISO populated from the 2026 LTLF regional decomposition validated on the deck's own
published totals, NEISO `{}` re-confirmed, D-4 gap list presentable unedited · WS-3a **complete**
(and **launched twice** — two branches ran the same charter; the second merged as a cross-check
addendum, no divergence) · **WS-0 CHECKPOINT** (items 1–4 + PRECOMMIT landed; the `scenario`
registration kind and the paired T0 owed) · **WS-2a CHECKPOINT** (the row + two fields landed;
postures/probe/matrix/docs owed) · **GRADED AGAINST CLAIM, TWICE: no matrix row or cell exists for
`carbon_price_path`, `policy_bundle`, or `federal_ces_target_by_year`** — WS-1a's own scorecard
edit reads "stamped … minted at WS-1a" and it never committed to `docs/codebase-site/data/` at
all; WS-2a added two solve-affecting `ScenarioConfig` fields with no row, **and CI passed**, so
`check_mechanism_matrix.py`'s duty-(c) half did not catch them (routed, not fixed) · **ISSUED:
SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b** · **cards D-1 and D-3 RE-PRESENTED on new evidence,
D-4 PRESENTED** (its gap list now exists); D-2 and D-6 stand presented, unmoved · no card has been
ruled — **D-1, D-2, D-3, D-6 all still OPEN** · §2.1b gate unchanged: **NEISO only**; no Stage-B
lane issuable, none issued · capx r#41 deconflicted: D62/D65 issued, D60-R2 status ASKED not
graded lost, none holds an SCN file.
*(previous)* **r#1 (HEAD `d01ab8b0`):** the desk opens. Ledger created; plan read whole; capx r#40 read for
deconfliction (**D60-R2 RUNNING**, D61/D64 issued-unlaunched, D58 released-pending-D60, D63
queued — none holds a wave-1 SCN file, but D60-R2 and the owner's backcast lanes append to the
six matrix shards continuously, so the last-commit one-line shard protocol is MANDATORY, not
advisory) · **WAVE 1 ISSUED IN FULL — SCN-WS0, WS-1a, WS-2a, WS-3a, WS-4a** (five disjoint-file
lanes, no owner ruling required to start any of them) · **cards D-1, D-2, D-3, D-6 PRESENTED**;
D-4 held for WS-4a's gap list, D-5 held for Stage A's measured cost table · **§2.1b gate read at
the pin: NEISO ONLY** — NYISO's `complete` was withdrawn again on 2026-09-05 (nyiso-193
executing the owner's nyiso-192 promotion ruling; Q5 uniform rule), so `complete` =
{ERCOT, NEISO, PJM} and Q45's premise has lapsed. No Stage-B lane is issuable at this refresh
and none is issued.

**Transport note (r#1):** this session's harness assigns the branch
`claude/scn-desk-charter-x9v4k4` and forbids pushing elsewhere, so this refresh lands there
rather than on the charter's nominal `claude/scn-desk-ledger`. Successor refreshes should use
`claude/scn-desk-ledger` unless their own harness says otherwise; the ledger file path is
unchanged and is what matters.

---

## 0. Refresh log (newest first)

### r#16 — 2026-09-06, main HEAD `00cee150`

*(This refresh's PR.)* Delta from the r#15 pin `e6a0402f`: **89 commits**. r#15 merged (#5204). `CLAUDE.md`
+8 lines: capx D79's solve-surface fingerprint now enters `cache_key()` (owner ruling Q54) — a re-derived
registry table re-keys the ISOs whose rows moved. It landed **after** RESOLVE's pin, so every pinned SCN lane
is unaffected; any SCN solve at a later HEAD carries the fingerprint in its key.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-RESOLVE** | **RUNNING — PRECOMMIT (#5214) + legs 1–5 of 13 (#5221) on main; every gate PASS on every leg** | THE PIN `bdfb3095e9fa…`; G-DRIFT `1cc45bb2..pin` over 34 solve-path commits — 30 INERT with reasons, four LIVE: D77 and D65-B (ISO-wide by design), **D67-ARM and D81 (PJM only — measured on the resolved PJM legs; the desk's r#14 "INERT for every SCN leg" was wrong, the ISO's own `default_scenario_overrides` arms it)**. Phase 0 measured that **every one of the 16 legs re-keys at the pin** (D65-B's `ccs_retrofit_vom_adder` is not cache-optional), so the STATUS doc's cache blocker is defeated by construction; the lane re-solved **in place** under the original dirs with `run_ces_leg.py` and a per-leg fresh-solve proof (G5), a deviation from the charter's `-r2` out-dir with its reason stated in §4.1 — **accepted**. NEISO 2/2 and NYISO 3/3 landed: G1 identity to 1e-9 (NYISO: 13/36/37 converted units 2028–30), G2/G3 2026–27 identical to the pre-fix bundles for every fuel, G4 14/14 both sides, G5 fresh solves (~1,200 s). **NYISO 2030 CO2 26.31 → 14.17 Mt (−46.2 %)**; LOAD-HI's delta falls 5.34 → 3.12 Mt (prediction P-B HIT: unequal CCS fleets across the arms); **the DC-shape axis survives** (−0.08 → −0.15 Mt at 2030, both ~0.1 Mt on a 14–26 Mt level). Pre-fix artifacts deleted, same run ids, declarations in the same commits, audit EXIT 0. Next: PJM (2), CAISO (3), MISO (3), one at a time behind the capx batch. |
| **SCN-WS5A-POLICY-<ISO> ×6** | **ERCOT, NEISO, NYISO LAUNCHABLE NOW (charter v5); PJM, CAISO, MISO wait for their re-solved REF** | P1 is met where the RESOLVE lane's G1 PASS exists for the ISO (NEISO, NYISO) or where its §2 measures the ISO clean (ERCOT, 0.00 TWh CCS every year). v5 changes: P1 names the pin and the per-ISO condition; P2 points at the in-place dirs; P4 counts RESOLVE's heavy legs; the PJM read list carries D67-ARM + D81. |

**S5's paired check is now measured on the campaign's own reference cases, not only D77's bare screen** —
the condition the desk released A-POLICY on at r#11 is over-satisfied for NEISO and NYISO. The policy
lanes for those two and for ERCOT are pasted this refresh; their first solves queue behind RESOLVE's
per-plant legs under rule 12 (the owner holds the slot), and phase 0 + PRECOMMIT need no slot.

**Corrected against the desk.** r#14 called capx D67-ARM "INERT for every SCN leg (a `{iso: bool}` gate no
campaign case sets)". False for PJM: the gate arrives through `_pjm_config`'s `default_scenario_overrides`,
so every PJM forecast leg at the pin carries the published adequacy requirement, and D81's must-offer
convention with it. The RESOLVE PRECOMMIT pre-declares that PJM's pre-vs-post difference is therefore not
D77's alone. The v5 charter says the same to the PJM policy lane.

**Capx (deconfliction).** No director refresh in the delta. D79 phase 1 landed (the fingerprint); D78-R2
step 0; pjm-167 F1/F2 built default-OFF (owner lane). The capx batch's state is unknown at this pin (no
r#51 yet) — the RESOLVE lane confirms the slot before each heavy leg as chartered. No SCN file held.

**Issued:** the policy charter **v5** for ERCOT, NEISO, NYISO (launch order ERCOT + NEISO, then NYISO). **Held:**
the PJM / CAISO / MISO policy lanes (v5 text, P1 pending their REF); the policy synthesis; Stage B (S13).
**Cards:** none.

---

### r#15 — 2026-09-06, main HEAD `e6a0402f`

*(This refresh's PR.)* Delta from the r#14 pin `5375be8b`: **13 commits**, all the capx track's; r#14
merged (#5196). `CLAUDE.md` unchanged.

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-RESOLVE** | **NOT DISPATCHED — second refresh. ASKED, not LOST; charter re-emitted verbatim** | No branch, no PR, no `…-r2/` dir. The charter's two-refresh threshold is not applied: (a) the r#5 standing rule — absence is evidence only beside an ask, and the r#4 LOST call it came from was wrong; (b) the capx director recorded at r#50 that its own third emission of five undispatched charters "was wasted — a timing artefact of the owner's batching, not a lost prompt". The stem `claude/scn-ws5a-resolve-post-d77-k6ty` is unburned (nothing was ever pushed to it) and stays. The text re-emitted is the r#13 charter plus the r#14 rule-12 sentence, unchanged. |
| **SCN-WS5A-POLICY-<ISO> ×6** | **NOT LAUNCHED — correct** | P1 absent. |
| audit | `forecast-invariant-artifacts` **EXIT 0** at HEAD. | — |

**Capx (deconfliction), r#50 + am.1.** D67-ARM armed PJM's published requirement with every
pre-declaration hit (the CLAUDE.md line r#14 recorded); D78-R proved the sector gate an exact partition
and holds on its own band → D78-R2; D81 returned 2.1 GW to the merchant fleet; D76 phases 0–1 landed;
**D79 earned card C-22/Q54 and the owner ruled ADOPT — a frozen-hash solve-surface fingerprint at zero
key moves.** That is the "same key, different solve" hazard this desk routed at r#10 (D77 §4c) and
r#11, now a program mechanism; once it lands, the RESOLVE lane's cache-hit proof becomes redundant with
the fingerprint, but the charter keeps it (belt and braces at zero cost). CAISO gate (a) re-keyed by the
owner's lane; `complete` still {ERCOT, NEISO, PJM}. **D65-B-R's batch is still running** — the per-plant
slot is still taken; RESOLVE's NEISO/NYISO legs need no slot. No SCN file held. No HOLD.

**Issued:** nothing new (RESOLVE re-emitted). **Cards:** none.

---

### r#14 — 2026-09-06, main HEAD `5375be8b`

*(This refresh's PR.)* Delta from the r#13 pin `13ee0c89`: **79 commits**, none SCN's beyond r#13's own
merge (#5165). `CLAUDE.md` +1 line: capx D67-ARM's `capacity_adequacy_requirement_published_by_iso`
entry in the Capacity Evolution section — a `{iso: bool}` gate no scenario case sets, INERT for every SCN
leg (the WS-5A ADDENDUM verified the same for D67's build). `scenarios.py` +142: capx D75-R (PJM VRE ELCC
vintage axis, default-OFF) and D76 (measured-hindcast screen-peak gate, default-OFF) — both inside the
RESOLVE lane's G-DRIFT window, both expected INERT for a forecast load leg; the lane classifies them.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-RESOLVE** | **NO EVIDENCE OF DISPATCH — one refresh; asked, not graded** | No branch, no PR, no `results/scn-campaign-load-2026-09-06-r2/`. Issued at r#13 in chat. |
| **SCN-WS5A-POLICY-<ISO> ×6** | **NOT LAUNCHED — correct** | P1 (RESOLVE's PRECOMMIT) does not exist. |
| **audit** | `forecast-invariant-artifacts` **EXIT 0** at HEAD, re-run. | — |

**Rule 12 now binds the RESOLVE lane from outside the SCN track.** Capx r#49: D65-B-R's batch (every bare
key, per-plant ISOs included), D78-R's two legs and D81's full window are **all solving at once** — the
director calls the queue saturated. RESOLVE's NEISO and NYISO legs are small and may start any time; its
PJM, CAISO and MISO legs (per-plant, 8.9–9.65 GB) may run only when nothing else per-plant is solving.
One sentence added to the charter (§5): before each of those three legs, confirm with the owner that no
capx per-plant solve is live; never assume the slot. Recorded in §4.

**Capx (deconfliction).** D65-B-R found D65-B's screen ran without `--golden-posture` (a director charter
gap, not SCN's); D81 measures D54 §4.2's bias at zero; NYISO promoted to `nyiso-202` (CALIBRATED) with
gate (a) re-keyed by the owner's lane, Q51 still parked, `complete` still {ERCOT, NEISO, PJM}; D67-ARM /
D76 / D75-R / D79 undispatched on their side. No SCN file held. No HOLD.

**Issued:** nothing new. **Cards:** none (D-5 held under S13; D-1(b)/D-1(c) open and dormant).

---

### r#13 amendment 1 — 2026-09-06: ruling S13 on card D-5

Presented as a clickable decision card in the r#13 sitting; the answer was the recommended option.

**S13 (2026-09-06), verbatim: "Hold until RESOLVE and the policy half land."** No per-campaign §2.1b grant is
recorded; nothing full-horizon is chartered. D-5 is re-presented the refresh SCN-WS5A-RESOLVE (the post-D77
re-solve) and Stage A-POLICY are both on main, with the amended cost table and the post-fix NEISO reference
case, and §2.1b legs (b)/(c) re-read on the post-fix board at that sitting. The desk's queue is therefore
strictly serial from here: RESOLVE → the six policy lanes (v4) → the policy synthesis → D-5.

---

### r#13 — 2026-09-06, main HEAD `13ee0c89`

*(This refresh's PR.)* Delta from the r#12 pin `2485e611`: **45 commits**. r#12 am.2 (#5149) merged.
`CLAUDE.md` unchanged. Capx r#48 in the delta (D78 landed exact; D74 refused its own arm; D65-B's screen
fired two gates the director wrote for the wrong ISO → D65-B-R; D78-R / D81 chartered, D82 reserved).

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-LOAD** | **COMPLETE at the frozen pin — 16 of 16 legs, six FINDINGs, the synthesis and the D-5 cost table; RULING S8 NOT EXECUTED, and correctly so by the lane** | PR #5130 (10 commits, +11,673). CAISO complete: the ORGANIC arm two lanes called degenerate was worth solving (ΔCO2 −0.011 → −0.113 Mt, Δpeak −0.40 → −1.92 GW at identical energy — WS-4b/WS-4c were right at their pin, stale after SCN-LOAD read the CEC Local Reliability Scenario); the import line first moves in 2030 exactly as the lane's P-6 predicted; the backstop ladder binds and I3 appears in 2028; CAISO carries the campaign's largest CCS fleet (45.16 TWh) at 4× the intended rate — 16.2 % of its 2030 level. **Synthesis §0: "this is half a campaign, and the half it left out is not the only contaminated one"** — five of six ISOs carry mis-rated CCS in REF from 2028; deltas mostly survive; ERCOT clean. **§8: the D-5 cost table exists, measured — 313.7 min of LP for 16 legs / 80 solve-years (3.92 min per solve-year; NEISO 1.09, ERCOT 1.30, NYISO 4.06, CAISO 4.33, MISO 5.23, PJM 7.90), ~4.7 h wall on one box; PJM super-linear inside the window (20.9 min for 2030); MISO 9.65 GB peak.** The STATUS doc states why the lane did not re-solve: the campaign was frozen by its own PRECOMMIT and re-pinning mid-campaign puts legs at two bases; it scoped the re-solve for the desk instead (13 of 16 legs) and named a blocker the desk had not: **D77 moves no key, so a naive re-solve HITS the pre-fix cache and returns the numbers it was meant to replace.** Audit declarations landed with every registration. |
| **SCN-FIX2** | **LANDED — COMPLETE** | #5153, `FINDING-scn-fix2-2026-09-06.md`. The five carbon rows on the committed path form (`mid` on ERCOT/PJM/MISO: 0 / 3.75 / 7.50 / 11.25 / 15.00 $/t over 2026–2030; exactly inert on the three program ISOs), the S9/S10 relabel words-only (files line-identical once comments are stripped), 3/3 pins + 18/18 keeper `run_config.json` + 12/12 REF bases byte-identical, exactly the 30 keys of the five re-formed cases move and no bundle exists at any of them. **A measured result nobody predicted, load-bearing for Stage B:** "inert on the program ISOs" is a T1-F fact, not a horizon fact — over 2026–2050 the `high` path crosses ABOVE the state trajectory on NYISO 2031–2047 (peak +$9.05/t) and NEISO 2033–2042 (peak +$3.32/t); CAISO stays inert in all 25 years. A full-horizon `CARB-HI` is live on NYISO and NEISO. Routed: the YAML's voluntary/cap comment blocks are stale after S9/S10/S12; the live forecast default key is `547053bdfccd4264`, not the `e5ecd…` literal the desk's charters carried. |
| **SCN-CAP** | **LANDED — COMPLETE** | #5154, `FINDING-scn-cap-2026-09-06.md`. `mass_cap_tons_by_year` ships `None`, coerced in backcast/hindcast, read FIRST (schedule → scalar → published → inert), linear between knots, edges held; `CAP-STATE-TIGHT` live at the ruled schedule verbatim with the CAISO anchor disclosed; 0 of 143 committed `run_config.json` keys move, 0 of 6 keeper keys, both defaults unchanged; new matrix row `mass_cap_schedule` + six `U` cells. **§3 binding table against the pre-D77 REFs: binds on NYISO in all five years (margins +0.53 … +2.81 Mt) and on CAISO in all five (+0.81 … +5.01), SLACK on NEISO in all five (4.6–5.7 Mt margin) — NEISO's case will be killed at phase 0.** **A charter premise false at HEAD, routed not papered over:** PJM is in `CAP_AND_TRADE_PROGRAMS` (partial RGGI), so under the case PJM falls through to the published regional budget in 2027–2030 and is NOT byte-identical to REF — the desk's policy charter carried the same false sentence and is corrected below. |
| **capx D80** | **LANDED** — the 8 capx ids declared; `forecast-invariant-artifacts` reads **EXIT 0 on main** (102 sidecars, 97 FAILs declared, audit OK, re-run at HEAD). | #5151. The Y-24 backlog is closed on both tracks. |
| **SCN-WS5A-POLICY-<ISO> ×6** | **NOT LAUNCHED — correct; P1 did not exist and now names a different document** | No branch, no PR. Their charter is re-cut as v4 (below) and remains unlaunchable until the re-solve lane's PRECOMMIT names the pin. |

**RULING S8 HAS NO EXECUTOR, and that is the desk's third instance of the same error in one day.**
The S8 amendment (r#10 am.1) was written for "the running lane"; the owner had no such session to
paste it into (the owner said exactly this at r#12 am.2 about a different addendum), and the load
lane finished at its freeze as its own PRECOMMIT required. Result: the 13 contaminated legs stand at
the pre-D77 pin, the policy lanes' precondition P1 points at an "ADDENDUM 2" nobody will write, and the
synthesis's own recommendation for D-5 is to gate Stage B on the re-solve. **→ SCN-WS5A-RESOLVE issued
as a standalone lane**: the S8 recipe as a charter, the 13 legs in rule-12 order, THE PIN named in its
own PRECOMMIT (which becomes P1), the STATUS doc's cache blocker defeated by a new out-dir per ISO that
redirects `cache.CACHE_ROOT` (`run_full_horizon.py` ~:736–750) plus a per-leg cache-hit proof, the S5
paired check reproduced on the campaign REFs, same-id re-registration with old-artifact deletion and
audit declarations in the same commit, and a dated synthesis addendum with the amended cost table.
The r#12 am.2 standing rule applies retroactively: nothing is issued as an amendment again unless the
target session is verifiably running.

**The policy charter is re-cut as v4** (§5): P1 now names the RESOLVE PRECOMMIT + its G1 PASS; P2 the
`…-r2` REF dir (ERCOT's standing leg excepted); P3 and P5 marked MET with their commits; **the PJM cap
clause corrected** (PJM runs the phase-0 binding test on the regional-budget fallthrough, expects slack,
reports it; ERCOT/MISO alone are byte-identical); the CAP §3 binding expectations carried in; key
literals banished in favour of `PINNED_DEFAULT_CACHE_KEY`. Still not launchable until RESOLVE's
PRECOMMIT and G1 land.

**Card D-5 is presentable at last — with a recommendation to hold it.** The charter's condition ("the
measured cost table on the dashboard") is met by synthesis §8. The synthesis's own recommendation, and
the desk's: what should gate Stage B is not cost but the re-solve — a Stage B built on the pre-D77
NEISO REF inherits a 41.9 %-contaminated 2030 level — and the policy half has not run. Presented with
that recommendation; the owner may grant now, conditional on the re-solve.

**Routed.** (a) FIX2's full-horizon crossing (CARB-HI live on NYISO/NEISO 2031–2047) — a Stage B
design fact for whoever charters Stage B; (b) the YAML's stale voluntary/cap comment blocks — folded
into the RESOLVE lane's file list? No: outside its regions; carried as a one-line item for the next
records lane; (c) the desk's own stale key literal — every charter from r#13 reads the pinned constant.

**Capx (deconfliction).** Live capx branches: `capx-d65br-batch` (re-solves every bare key at one HEAD
carrying D77 + D65-B — it writes `frontend/data/hindcast/` sidecars for bare ids and
`invariant-failures.json`; the RESOLVE lane writes campaign ids only; append-only, distinct dirs),
`capx-d78r-full-window`, `capx-d81-must-offer`. Rule 12: the RESOLVE lane's PJM/MISO/CAISO legs and
D65-B-R's per-plant legs cannot co-run — **the RESOLVE charter says it is the only solving lane while
it runs PJM/MISO/CAISO; the owner sequences the two batches.** No file HOLD. `complete` unchanged;
§2.1b gate NEISO only.

**Issued:** **SCN-WS5A-RESOLVE** (Opus, `all`). **Re-cut, not launched:** the policy charter v4.
**Held:** the policy synthesis; Stage B (D-5 presented).
**Cards:** **D-5 PRESENTED** with the measured cost table and a hold recommendation.

---

### r#12 amendment 2 — 2026-09-06: the cap addendum withdrawn and folded into the policy charter (owner)

The owner had no session to paste the cap addendum into — right: the six `SCN-WS5A-POLICY-<ISO>` lanes
have never been launched, because their first solve is gated on WS-5A's ADDENDUM 2 (P1), which does not
exist yet. An addendum to a lane that is not running is a desk error, the second of its kind this day
(r#11 am.2 folded the voluntary addendum for the same reason). The cap case is folded into the combined
policy charter as case 13 (program ISOs only, precondition P5, gates G10–G12); §5 carries the v3 text
and the addendum is withdrawn unissued. **Standing rule: an addendum goes only to a lane verifiably
running; for an unlaunched lane the change goes into the charter, and the desk says when the charter
is launchable** — here, when WS-5A's ADDENDUM 2 is on main.

---

### r#12 amendment 1 — 2026-09-06: ruling S12 on card D-2(c)

Presented as a clickable decision card in the r#12 sitting; the answer was the recommended option.

**S12 (2026-09-06), verbatim: "Commit the 80 % slope and build the field."** The `CAP-STATE-TIGHT`
budget is WS-1a §4.2's schedule — a linear decline to 20 % of the 2025 published per-state budget by
2050 (NYISO 23.16 → 4.6 Mt, NEISO 20.67 → 4.1, CAISO 30.5 → 6.1 on a REF-2026 anchor, disclosed) — and
the schedule field `mass_cap_tons_by_year` is built. **Issued:** **SCN-CAP** (Fable, zero-LP; §5) and
the **CAP addendum** to SCN-WS5A-POLICY-CAISO / -NYISO / -NEISO (§5): a thirteenth case gated on a new
precondition P5 (the field and the case on main), killed at phase 0 where the budget is slack in every
year (WS-1a §4.1 measured the published path slack everywhere but NYISO-2025; the ruled slope is what
makes the row bind), with gates G10 (emissions = budget, dual > 0 where binding; dual 0 where slack),
G11 (one instrument at a time — the row REPLACES the adder on the ISO, no federal price under
`carbon_price_path: zero`) and G12 (carbon-case footprint). ERCOT / PJM / MISO lanes are untouched:
the row is gated off by `CAP_AND_TRADE_PROGRAMS` and the case is byte-identical to REF there.
**With S12 every §3.5 case is inside Stage A.** Unchanged: D-5 held; Stage B not issuable.

---

### r#12 — 2026-09-06, main HEAD `ba894c9c`

*(This refresh rides PR #5124, rebased onto main — r#11 + am.1 + am.2 are still unmerged, so the
policy charters and the FIX1 re-issue reached their lanes through chat, not main.)* Delta from the
r#11 pin `d1aa877f`: **36 commits**. `CLAUDE.md` unchanged. Capx r#47 + am.1 in the delta.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-FIX1** | **LANDED — items 1 and 2 COMPLETE on the r#10 charter; items 3–4 (issued at r#11 / r#11 am.1, unmerged) never reached it → SCN-FIX2** | PRs #5127 / #5129 / #5136, `FINDING-scn-fix1-2026-09-06.md`. All **22** `scn-` runs / 34 (run, ident) pairs declared, each to its FINDING; the 16 stale `registration_ratchet_baseline` lines pruned in the same commit (mandatory, the lane showed, or 22 reds become 16); the audit goes **30 → 8**, the 8 exactly the capx set. **The collate defect is worse than routed and the routed case was the mild one:** on the whole tree the system-scope `LOAD-HI` 2030 delta **changes sign** (naive −243.86 vs common-set +168.78 Mt) because MISO had a REF and no LOAD-HI leg yet — any campaign read while filling in hits it; the repair is a strict no-op where coverage already matched (+20.1555 before and after), 14 pre-existing tests unchanged. Ruff: the charter's named red is already green (`824f9567`); two OTHER files are format-red on main (`scripts/run_calibration.py`, `src/market_sim/data/fuel/basis/miso.py`), neither SCN's — routed onward. |
| **capx D80** *(their records lane on the same file; graded because it wrote into this ledger)* | **LANDED as a cross-check** | #5139, `FINDING-scn-invariant-declarations-2026-09-06.md`: derived the identical 22-run edit independently (byte-identical, 25 min after FIX1 merged) and did not re-land it; answered the `4fab3f0a` forensic question (no second writer of the forecast namespace — the Y-24 ratchet is a working-tree gate, and a lane that registers on a pre-ratchet base then rebases forward lands a sidecar the gate never saw); named the one I7 no FINDING covered (ERCOT t1f LOAD-HI: the energy-only retirement-bounded limb, a 244.4 MW retirement REF does not make). It also ported this desk's r#10 am.1 (S8) block onto main's ledger — the record the PR-merge race had dropped — so the rebase of #5124 skipped it cleanly. |
| **SCN-WS5A-LOAD** | **RUNNING — 12 of 16 legs; MISO complete; PR #5130 open; the S8 amendment ACKNOWLEDGED and its scope corrected by the lane itself** | `0bf1d7f8`: WS-4b's DC shape number lands to 0.3 GW (3.91 vs 3.6 GW); all three MISO arms fail {I3, I7, I12} at REF (declared in the registration commit "this time — the ERCOT/PJM miss is not repeated"); MISO's import line 0.0 by construction (no tranches); `miso-2026-2030-d60-arm` stale at HEAD by +14.7 % energy. `9170899f` routes a correction to D-10: **the re-solve set is 13 of 16 legs, not 6** (NEISO 2, NYISO 3, PJM 2, MISO 2 of 3, CAISO 3; ERCOT's 3 the only clean ones) — **the same conclusion r#11 recorded from the ledgers a refresh earlier**; the two readings agree. `6788b4d5` declares its own five failing arms. CAISO next, then ADDENDUM 2 and the re-solves. |
| **SCN-WS5A-POLICY-<ISO> ×6** | **NOT DISPATCHED — one refresh; expected** | Their first solve is gated on WS-5A's ADDENDUM 2 (P1), which does not exist yet, and on P3 (the carbon form), which SCN-FIX1 did not land. Zero-LP phase 0 could start any time. Not graded. |

**Stage A-POLICY's remaining blocker is the desk's own YAML.** SCN-FIX1 was dispatched on the r#10
text; the r#11 and r#11 am.1 re-issues (the carbon-form switch, the S9/S10 relabel, ALL-CLEAN's
form) sat on an unmerged PR. The policy lanes' precondition **P3** therefore still fails at HEAD:
`CARB-*` reads `carbon_price_delta` {15, 25, 50}. → **SCN-FIX2 issued** (items 3–4 as one tiny
zero-LP lane, its measurement being the resolved-carbon table per case × ISO × year). Recorded
against the desk: a re-issue on an unmerged PR is a re-issue nobody can read; from r#12 a charter
change that gates a live lane is pasted to the owner in the same message, never left to the PR.

**Capx r#47 + am.1 (deconfliction).** D60-R4 refuted the D48 indictment (item closed); D67 earned
its arming card (Q52 → ARM, D67-ARM issued); D58 KILLED on the sector-gate/clearing seam (Q53 →
reading 1, D78 released after D74's screen); D77 recorded as repaired with 45 bundles mis-stated;
D75 STOP fired (preliminary ratings) → D75-R; **D79 chartered: "every forecast row on the board is
stale at an unchanged key" → a solve-surface fingerprint** — this is the cache-key hazard the desk
routed at r#10 (D77 §4c) and again at r#11, now a chartered structural repair, so the desk's
routing is discharged there; **D80 = the Y-24 records lane** (landed, above). D65-B's batch is the
SOLE board writer until it lands. Shared files with SCN: `invariant-failures.json` (append-only,
all lanes) and the sidecar dir (distinct run ids). No HOLD. §2.1b gate NEISO only, `complete`
unchanged.

**The last §3.5 case out of Stage A.** `CAP-STATE-TIGHT` needs (a) a budget slope — WS-1a §4.2
pre-declared a linear decline to **20 % of the 2025 published per-state budget by 2050** (NYISO
23.16 → 4.6 Mt, NEISO 20.67 → 4.1, CAISO 30.5 → 6.1 on a REF-anchored basis, since CARB publishes
no power-sector budget) and labelled the slope an OWNER level — and (b) the schedule field
`mass_cap_tons_by_year`, which WS-1a §4.1(a) said the case NEEDS and which does not exist in
`scenarios.py` at HEAD. So the case is one ruling **and one small build** away. → **card D-2(c)**
presented: rule the slope and charter the field, or drop the case from Stage A.

**Issued:** **SCN-FIX2** (Opus, zero-LP). **Held:** the policy synthesis; SCN-WS3c (withdrawn,
absorbed); Stage B. **Cards:** **D-2(c) PRESENTED.** D-5 still held (synthesis pending CAISO + the
13-leg re-solve). D-10 stands as ruled (S8); the lane's scope correction is the same reading.

---

### r#11 amendment 2 — 2026-09-06: the policy charter and the voluntary addendum combined (owner instruction)

The owner asked for the addendum to be combined with the prompts it attaches to. The six-ISO policy template
now carries the voluntary cases, the per-year regime kill, gates G7–G9 (the former G9 footprint clause merged
into G3, so the numbering is G1–G9), rulings S9/S10/S11 in its rulings block, the WS-3b/memo reads, and the
`voluntary_clean_demand` cell in its last commit. One paste per ISO. The r#11 template and the r#11 am.1
addendum are superseded unissued; §5 carries the combined text. Nothing else moves.

---

### r#11 amendment 1 — 2026-09-06: rulings S9 (D-2(b)), S10 (D-3c), S11 (D-6)

Presented as clickable decision cards in the r#11 sitting; all three answers were the recommended option.

**S9 (2026-09-06), verbatim: "Take the placeholders as committed."** `f_commit` mid = **0.5** and the
WTP ceiling = **$4.5/MWh** (the NREL unbundled-REC price band the memo cites) are the committed voluntary
levels. No number moves — WS-3b shipped exactly these; the label moves (SCN-FIX1 item 4, words only).
**S10 (2026-09-06), verbatim: "Ratify the default as built."** The eligible set is wind / solar /
offshore wind / geothermal; nuclear and CCS only via the labelled `voluntary_eligible_fuels` override;
every eligible unit credited; no additionality mask in dispatch.
**S11 (2026-09-06), verbatim: "Counts toward; report both."** A voluntary MWh counts toward the federal
standard by default; CES-P20+VOL-HI and ALL-CLEAN report both nettings side by side with the CES dual
under each.

**What the rulings release.** VOL-MID, VOL-HI, CES-P20+VOL-HI and ALL-CLEAN join the six policy lanes by
the ADDENDUM in §5 — with WS-3b's zero-LP regime test made a phase-0 kill (a slack row is byte-identical to
REF and is never solved; ERCOT 2026 measured slack) and four added STOP gates from the memo §6 (dual in
(0, WTP] where binding, = WTP at escape; curtailment falls before dispatch moves; footprint confined;
both nettings reported). SCN-FIX1's r#11 am.1 text adds item 4 (the relabel; ALL-CLEAN's carbon form
`carbon_price_delta: 25.0 → carbon_price_path: mid`). **CAP-STATE-TIGHT is now the only §3.5 case out of
Stage A**, on its unruled budget slope (plan §3.5 (i)) — presented at the next sitting if the owner wants
the price-vs-quantity comparison in this campaign.

**Issued on the amendment:** the voluntary ADDENDUM to SCN-WS5A-POLICY-<ISO> ×6; SCN-FIX1 re-issued
(r#11 am.1 text). **Unchanged:** D-5 held; SCN-WS3c held (its probe is now subsumed — the policy lanes'
VOL-* legs carry the memo §6 gate per ISO, so WS-3c is **WITHDRAWN as a separate lane**, its scope
absorbed); Stage B not issuable.

---

### r#11 — 2026-09-06, main HEAD `d1aa877f`

*(This refresh's PR.)* Delta from the r#10 pin `6887484f`: **60 commits**. r#10 + am.1 merged (#5106).
`CLAUDE.md` unchanged. No capx director refresh in the delta.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS1b-r2** | **LANDED — COMPLETE, 12/12 arms** | #5101 + `4fab3f0a` (CAISO pair) + `9b95330f` (six `carbon_price_path` cells, last commit). §0 filled: three ISOs live at +$3.75/t with textbook coal→gas re-ordering (PJM's elasticity the substantive result: 17.4 TWh of coal, 7.7 % of its output, displaced by $3.75/t — the coal/gas-CC spread is $2.44/MWh wide there); three ISOs **exactly inert** (S2 measured, not a null); price campaign-grade on PJM and MISO only; the price-setting rate exceeds the load-following rate 1.13–1.33× in 3 of 3 (the lane's n = 2 magnitude claim retracted by its own n = 3); direction 9/9, magnitude 6/9, all three misses under-predictions; leg 2 held by S5. 24 solve-years, 89.4 min, 12 arms registered. Plan §5.1 / ledger §3 Carbon rows 3 and 7 written by the lane. |
| **SCN-WS5A-LOAD** | **RUNNING — 11 of 16 legs at the frozen pin; PJM complete, MISO REF landed; the S8 amendment not yet visibly acted on (expected — S8 step 1 finishes PJM/MISO at the old pin first)** | PJM (`FINDING-scn-ws5a-load-pjm`): WS-4b's sharpest call lands (I3 absent at `mid`, present under LOAD-HI — two years earlier than they said, SPLIT); **PJM carries 909.8 MW (REF) / 1,512.8 MW (LOAD-HI) of `gas_cc_ccs` from 2029 with NO state carbon program** — §45Q is a bid offset independent of carbon price, so the screen clears without one; the lane KILLS its own "state program arms the screen" claim and corrects both earlier FINDINGs (the STATUS doc's CORRECTION block). PJM's CCS units are the campaign's worst-rated pre-fix (0.6063 t/MWh, ~15× the intended, above unabated CT) and the two arms carry materially different CCS fleets (3.50 vs 11.62 TWh), so the defect does **not** cancel in PJM's delta. **MISO REF carries 334.5 MW of `gas_cc_ccs` too** (read from its committed summary). |
| **capx D77** *(graded because S7 named it)* | **COMPLETE — and its identity gate is ruling S5's paired check** | `3d748d02` (#5118): same-HEAD one-field A/B of `neiso-t1f` 2026–2030, 0 FAIL / 0 WARN both legs. **Gate 1 identity PASS every year** (12 / 23 / 24 converted units at `measured × 0.10` to 1e-9); gate 3 confinement PASS; gate 5 no-collateral PASS to the digit; gate 6 PASS; gate 2 reads FAIL as literally written and is diagnosed as the retrofit SET moving (pre-declared NOT a STOP); gate 4 2030 −2,184.6 MW, reported. 2026–2027 identical to four decimals (pre-2028 inertness measured). **The correction is larger than WS-2b's fixed-dispatch arithmetic** because dispatch moves too: NEISO 2030 CO2 13.37 → 6.95 Mt (−48.0 %), lw price $67.67 → $57.30. §8.1 blast radius names the pre-fix SCN bundles: WS-2b's four ladder legs, WS-4c's two NEISO t1f arms, the campaign's NEISO REF/LOAD-HI. |
| **capx D65-B** *(not ours; it moves the pin every SCN policy leg will stand on)* | **LANDED Acts A + B, ONE RE-KEY EVENT** | `fb93b76e` (#5112): `ccs_retrofit_vom_adder` 8.0 → 2.95 $/MWh (derivation-first, the test committed failing against 8.0), `ccs_retrofit_fixed_cost_co2_scaling` default False → True as a (b′-1) flip; a defect found and repaired before the screen (the flip made the D50 control arm unconstructible). Its screen and batch pending. Any post-D77 pin is also post-D65-B; the campaign re-pin's G-DRIFT classifies it LIVE wherever a retrofit ledger is non-empty. |
| **SCN-FIX1** | **NO EVIDENCE OF DISPATCH — one refresh; asked, not graded** | No branch, no PR, no commit. The audit backlog it declares grew meanwhile: **30 undeclared at HEAD, 22 SCN** (WS-1b-r2's CAISO pair and WS-5A's two PJM legs added). Re-issued with one item added (below). |

**STAGE A-POLICY IS RELEASED UNDER RULING S5 — no new card.** S5's condition was *"the seam is
repaired AND a paired check confirms `emission_rate` follows the retrofit."* The repair is `ae8dd2a0`;
the paired check is D77's gate 1, PASS at model grain on a real NEISO t1f solve in every year. The
condition is met on the record as written, and the desk releases the policy half. **Sequencing is the
whole content of the release:** every policy leg differences against a REF, and the load campaign's
REFs are being re-solved at a post-D77 pin under S8 — so the six `SCN-WS5A-POLICY-<ISO>` charters
(§5) are issued NOW for phase 0 + PRECOMMIT, with a hard STOP on the first solve until WS-5A's
PRECOMMIT ADDENDUM 2 names the pin on main (P1), the ISO's REF at that pin is registered (P2), and the
carbon form is switched (P3). Cases: CARB-LO/MID/HI, CES-P10/P20/P30, CES-T80, CARB-MID+LOAD-HI. **Held
out of the release:** VOL-MID, VOL-HI, CES-P20+VOL-HI, ALL-CLEAN (two voluntary levels and the eligible
set are unruled → cards D-2(b), D-3c, D-6 presented this refresh so they can be added by addendum),
and CAP-STATE-TIGHT (its budget level never ruled, plan §3.5 (i)). On CAISO/NYISO/NEISO the three
CARB-* legs are byte-identical to REF under the S2 floor (WS-1b-r2 measured 0.000000) and are killed
at phase 0, never solved — so the program ISOs run five policy legs, the others eight.

**S8's re-solve set widens under its own criterion, and the ledger says so before the lane does.** S8
kept ERCOT/PJM/MISO "on the strength of an EMPTY retrofit ledger read per leg, never assumed." PJM's
ledger is not empty (909.8 / 1,512.8 MW) and MISO's is not (334.5 MW) — both via §45Q, no program
needed. So the re-solve set is **NEISO 2 + NYISO 3 + PJM 2 + MISO (its LOAD-HI/ORGANIC pending; REF
re-solves) + CAISO 3**; **only ERCOT stands** (retrofit ledger measured NONE). The amendment's rule
already produces this; recorded here so the cost table D-5 will carry is read as ~S8-plus-PJM/MISO,
not as the r#10 estimate. PJM re-solves are ~28 min each, MISO ~60.

**The carbon FORM is still the desk stand-in, and that is now a blocker the desk owns.** The YAML runs
`carbon_price_delta` {15, 25, 50}; S3 committed the RFF `carbon_price_path` ladder, SCN-LEVELS recorded
the delta as an interim "until SCN-WS1c lands S2's floor", WS-1c landed it on 2026-09-06 and nobody
switched the YAML. WS-1b-r2 §7 says the same. → **SCN-FIX1 re-issued with item 3: the four carbon-form
rows.** Consequence the switch makes explicit: on program ISOs the CARB-* legs are exact no-ops (the
ruled S2 outcome), and on ERCOT/PJM/MISO the signal starts in 2027 at $3.75/t (mid) — small, but the
committed level. `ALL-CLEAN` keeps its delta until the voluntary cards are ruled.

**Superseded pre-fix bundles, disposition.** D77 §8.1 lists WS-2b's ladder legs and WS-4c's NEISO t1f
arms as stale at their keys. They are landed probes whose evidence lives in their FINDINGs; **they are
superseded by the policy legs and the campaign's re-solved REF, not re-run as probes** (rule 29(c)
spirit: the doc is the record). WS-2b's §5.4 arithmetic is re-based by the NEISO policy lane's CES-P20
leg, which D77 §4c already said it needs.

**Routed.** (a) **§45Q arms the retrofit screen without a carbon program** — a mechanism fact the capx
track's D50 evidence did not generalize; PJM's pre-fix CCS at 0.6063 t/MWh and the lane's untested
hypothesis (ERCOT's shortage margin makes the *incremental* uplift negative) go to the screen's owner.
(b) The audit backlog is now 30 (22 SCN); SCN-FIX1 declares SCN's, the 8 capx ids are theirs.
(c) WS-3c stays held: PJM's REF passes adequacy (no I3 at `mid`) but its retrofit ledger is not empty;
MISO likewise; ERCOT fails adequacy. **No ISO currently meets both halves of the criterion** — the
desk will revisit when the post-D77/D65-B re-solves land (D65-B's cheaper retrofit may move the
ledgers further, not closer).

**Capx (deconfliction).** No director refresh in the delta; live capx lanes D60-R4 (#5109 landed a
refuted falsifier), D65-B (screen + batch pending — the batch re-solves every bare key at one HEAD and
writes forecast sidecars), D74 (build landed), D63/D73/D75/D76. **The D65-B batch and the SCN policy
lanes both write `frontend/data/hindcast/` sidecars and `invariant-failures.json`** — different run
ids, append-only; the one-key-per-line protocol is in every charter. No HOLD.

**Issued:** **SCN-WS5A-POLICY-<ISO> ×6** (Opus; phase 0 + PRECOMMIT now, solves gated on P1–P4; launch
order ERCOT + NEISO, then NYISO, then PJM / CAISO / MISO alone); **SCN-FIX1 re-issued** (r#11 text,
item 3 added). **Held:** SCN-WS5A-POLICY-SYNTH (issues when the six land), SCN-WS3c, Stage B.
**Cards:** **D-2(b), D-3c, D-6 PRESENTED** (the voluntary legs' three open boxes). D-5 still held.

---

### r#10 amendment 1 — 2026-09-06: ruling S8 on card D-10

Presented as a clickable decision card in the r#10 sitting; the answer was the recommended option.

**S8 (2026-09-06), verbatim: "Re-pin once post-D77 now."** The SCN-WS5A-LOAD amendment written at r#10
(§5) is issued to the running lane as written: (1) finish any mid-solve PJM/MISO leg at `1cc45bb2`,
rebasing between legs never during one; (2) re-pin at or after `fc583339` (the D77 merge) with a
hunk-by-hunk G-DRIFT in a PRECOMMIT ADDENDUM 2 pushed before the first re-solve; (3) re-solve NEISO REF +
LOAD-HI and NYISO REF + LOAD-HI + LOAD-HI-ORGANIC, solve CAISO's three legs at the new pin, and keep
ERCOT/PJM/MISO on the strength of an EMPTY retrofit ledger read per leg, never assumed; (4) the re-solved
NEISO REF reports the per-unit identity `emission_rate_co2 = measured × (1 − 0.90)` and the 2030 CO2
level pre- vs post-fix — **this is ruling S5's model-grain paired check**; (5) re-register under the same
run ids, delete the pre-fix NEISO/NYISO artifacts in the same commit, and declare every registered run's
invariant FAILs in `invariant-failures.json` in the registration commit; (6) the synthesis with a per-ISO
pin + G-DRIFT-verdict table, then card D-5 with the measured cost table including the re-solve.

**What S8 changes for the rest of the queue.** Stage A-POLICY's release condition (S5) is met the refresh
the re-solved NEISO REF lands with the identity holding — **no new card**; the desk then issues the six
`SCN-WS5A-POLICY-<ISO>` lanes, WS-1b-r2's leg 2 (re-expressed on the `carbon_price_path` axis per its
§7), and WS-2b's ladder re-base (D77 §4c). SCN-WS3c's criterion is unchanged (PJM/MISO REF adequacy +
empty retrofit ledger). SCN-FIX1 is unchanged. The r#8 "one base for every leg" doctrine is satisfied per
ISO by G-DRIFT rather than by a byte-identical pin, and the ledger says so.

---

### r#10 — 2026-09-06, main HEAD `6887484f`

*(This refresh's PR.)* Delta from the r#9 pin `0e20e8cf`: **165 commits**, the largest this desk has
graded. r#9's own PR #5049 merged (`f4658482`). **`CLAUDE.md` changed:** rule 30(a) amended a second
time the same day (owner, verbatim: *"Delete the stupid per year determination from the run explorer
… I just want the scores and charts"*) — the Run Explorer's report is scores and charts only, every
prose panel deleted not hidden; rule 22's substance now rests on the Calibration Status page. No SCN
lane touches a touchpoint surface; recorded only.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-LOAD** | **RUNNING — 3 of 6 ISOs COMPLETE (ERCOT 3, NEISO 2, NYISO 3 = 8 of 16 legs), and it FALSIFIED RULING S5's PREMISE** | PRs #5034 … #5103 (nine merges). Every leg a verified descendant of the frozen pin `1cc45bb2`, zero solve-path diff, `git.dirty=False`; registered under campaign `scn-campaign-load-2026-09-06`; per-ISO delta reports + three FINDINGs + a STATUS doc. **ERCOT** (`FINDING-scn-ws5a-load-ercot`): the headline is about REF — at HEAD ERCOT's shipped forecast posture is in **deep shortage**, unserved **0.38 → 127.2 TWh** (14.7 % of 2030 load), lw price **$91 → $4,438/MWh**, `hours_ge_500` 74 → 7,962 of 8,760; P-1 HIT (no tail regime; WS-4b's 1,800 TWh discontinuity does not reproduce); WS-4b's peak/adequacy artefact a clean MISS (the retired 122 GW DC anchor); three of the lane's own six predictions miss, reported. **NEISO**: 14/14 invariants PASS both arms, zero unserved — and **8,832.9 MW / 16.72 TWh of `gas_cc_ccs` in the REFERENCE case by 2030**, every unit mis-rated (0.3719 t/MWh, *above* the unabated 0.3666): the 2030 CO2 level overstated by **≈5.60 Mt = 41.9 %**; the delta mostly cancels (+0.089 of +1.408 Mt, 6.3 %, rides on defective units). **NYISO**: cleanest ISO (14/14, zero unserved, zero backstop); CCS exposure **6,475 MW / 24.42 TWh**, contaminating **≈5.29 Mt = 25.3 %** of the 2030 level; the sharpest diagnostic of S4's re-derivation (the ORGANIC peak within 0.4 GW, the LOAD-HI peak off by 3.3 GW — split exactly along which anchor SCN-LOAD moved); leakage +0.12 → +0.96 Mt = 7–25 % of the in-ISO ΔCO2. Running: PJM, then MISO, then CAISO. A `collate_scenario_campaign.py` defect found in pre-flight and routed (below). |
| **SCN-WS1b-r2** | **CHECKPOINT — 5 of 6 pairs scored; closing PR #5101 OPEN** | PJM 2027 **8/8 PASS**, campaign-grade (CO2 −13.44 Mt, leakage +0.43 Mt = 3.2 %, nearly 2× the lane's band top — a reported miss); MISO 2027 **8/8 PASS**, both bands HIT (CO2 −6.64 Mt; leakage 0.0 as a **model-boundary artifact** — no MISO import tranche exists); NEISO and NYISO solved as **exact-identity** tests (Δ = 0.000000 on every metric — the S2 floor doing what it says) and surfacing a LEVEL result the deltas hide: reported import CO2 is **41.3 % of NYISO's** and **25.3 % of NEISO's** scored in-ISO total. §3.7 n = 3: the price-setting rate exceeds the load-following rate in all three live ISOs (1.15× / 1.13× / 1.33×) — direction holds, the lane's magnitude claim retracted by its own test. Four arms registered. Owes: §0, CAISO (inert by the same floor; not yet confirmed), the six cells; #5101 carries §8/§9 and the plan §5.1 / ledger §3 Carbon rows 3/7 — **this refresh leaves those rows alone**. *Minor, noted:* the two inert pairs spent ~4 solve-years to confirm a pre-computed zero; the identity form is a real measurement (nothing else moved) and it produced the level result, so it is recorded as a spend, not a breach. |
| **SCN-WS3b** | **LANDED — COMPLETE, on its own branch, the day after S6** | `claude/scn-ws3b-voluntary-demand-h59n9b` (PRs #5085, #5090, #5095) — the desk's r#9 stem was, as always, not the realized name. Three fields in one block (`voluntary_clean_demand_path` ships `off`), `policy/voluntary_demand.py` (454 lines), the row on the clean-tier family as its second consumer, the DC-energy helper, `VOLUNTARY_*` anchors with citations, the four YAML cases (**live and S5-held**), 783 lines of tests, the constant-family table (standing change #1 honoured), the base row + six `U` cells as the last commit, `FINDING-scn-ws3b-2026-09-06.md`. **Zero-LP finding for WS-3c:** the memo's ERCOT 2026 T0 instrument is **SLACK** (eligible ~197 TWh vs ~76/115 TWh of voluntary volume) — the arm is inert in 2026 and must be screened where live. Seven items routed (§7). **Its two PRs auto-merged with two red checks — graded, not assumed: both reds are main-wide, not the lane's** (below). |
| **SCN-WS3c** | **HELD on a named criterion (not issued)** | Precondition met (WS-3b on main). Not issued because the instrument it was chartered on is slack, and the obvious replacement — ERCOT T1-F 2026–2030 — fails **standing change #2's REF-side adequacy precondition** (ERCOT REF unserved 127 TWh by 2030). Issues when Stage A-LOAD's PJM and MISO REFs land: the probe ISO is the one whose REF passes the adequacy precondition **and** whose retrofit ledger is empty (zero `gas_cc_ccs`, so S5-safe by measurement), screened on the T1-F window where the row binds. |
| **capx D77** *(not ours; graded because S7 named it)* | **CHECKPOINT — the repair is on main; the screen and FINDING are owed** | `ae8dd2a0` (#5089): phase 0 CONFIRMED WS-2b's candidate (`campd_bins.apply_plant_emission_rates_v2` restores the host's uncaptured CAMPD rate every forecast year; `fuel_class("gas_cc_ccs") == "gas"`; the 0.3745 is plant 55041's measured rate to four decimals); the fix is a `ccs_capture_fraction` stamp composed at both restoration sites (`measured × (1 − fraction)`, one composition point, zero DOF); 10 seam tests + 184 identity tests pass; **no cache key moves — pre-fix bundles at the same key are silently stale** (the D77 §3 hazard). The NEISO t1f screen (§4: identity to 1e-9, confinement, retrofit MW in band, no collateral) is pre-registered and **not on main**; the FINDING it cites does not exist yet and its branch is gone. |

**RULING S5's PREMISE IS FALSE — measured by the campaign it released, and the record already
held the evidence.** S5 reasoned from the *credit* channel (no CES armed ⇒ no `gas_cc_ccs`
exposure). The defect is in *dispatch*, and the retrofit screen is armed by **any** resolved carbon
signal — the state programs (RGGI on NEISO/NYISO, CARB on CAISO) resolve whether or not a case sets
one. capx D50 had published exactly this asymmetry (*"at carbon 0 the repair closes the screen … under
RGGI it does not"*) before S5 was written; the desk did not read it into the ruling. What S5 still
bought is real — no crediting exposure, and every delta is mostly protected — but "the
uncontaminated half" was never true for three ISOs' CO2 **levels** from 2028. Consequence at HEAD:
NEISO's two legs and NYISO's three were solved **pre-D77** and are exactly the bundles D77 §3
declares invalidated at their own key; CAISO is not yet solved; ERCOT/PJM/MISO are clean by
construction (no state program ⇒ empty retrofit ledger; ERCOT measured NONE). → **card D-10**, with
the desk's recommendation to re-pin once and re-solve only the five contaminated legs (plus CAISO
at the new pin), the desk's own r#8 "one base for every leg" doctrine being satisfied per ISO by
G-DRIFT rather than by a byte-identical pin.

**A-POLICY's release condition, re-read against D77.** S5: *"until the seam is repaired AND a paired
check confirms `emission_rate` follows the retrofit."* The repair is on main; the confirmation exists
at **unit grain** (D77's seam tests drive a retrofitted unit through the restoration) and is owed at
**model grain** (D77's NEISO screen, or — under D-10's recommended option — the campaign's own
re-solved NEISO REF, which the amendment turns into that paired check). **The desk releases A-POLICY
under S5, with no new card, the refresh either lands.** Not before: WS-2b's ladder, WS-1b-r2's leg 2
and every CES case would otherwise be solved into the same silent-stale-key hazard.

**TWO MAIN-WIDE CI REDS, graded from the job logs, not the check names.** (1) **Ruff format**:
`scripts/data/derive_caiso_offer_surface.py` — the owner's caiso-254 file, red on main since before
WS-3b's PRs; not SCN's. (2) **`forecast-invariant-artifacts`** (Y-24 ratchet, `bbcd4755`): **26
registered runs carry an invariant FAIL not declared in `frontend/data/hindcast/invariant-failures.json`
at HEAD, and 18 of them are SCN runs** — WS-4c's ten probes (I3/I7), WS-1b-r2's six pairs (I3/I7),
WS-5A-LOAD's three ERCOT legs (I3 + I12). The file's own `how_to_update` says the declaration lands
*in the same commit as the registration*; three SCN lanes registered without it (WS-4c before the
ratchet existed; the two running lanes after). The 8 capx ids are theirs. **→ SCN-FIX1 issued** (the
backlog), and the WS-5A amendment carries the duty forward for every future registration.

**Routed.** (a) **ERCOT's shipped forecast REF is in deep shortage** — 127 TWh unserved by 2030 —
which is G-S4 measured a third time and now at campaign scale; every ERCOT campaign leg is a
difference between arms both shedding at VOLL. capx adequacy queue; priority. (b) **D77 §4c: two bare
NEISO bundles at the SAME cache key disagree by up to 1.52 Mt/yr** (WS-2b BAU at `0c349d2f` vs the
campaign REF at `29b1c757`) — the key does not identify a solve across code changes; audit track,
beside the G-DRIFT pattern (now four data points). (c) `collate_scenario_campaign.py` sums the
system-scope delta over different ISO sets (STATUS doc; 71 % understatement measured) — SCN-WS0's
file → **SCN-FIX1 item 2**, not a route. (d) WS-3b §7 items 1–2 (persist the voluntary volume into the
year summary — WS-0/owner regions; the EIA-861 state × sector intake — `scripts/data/`) and D-2's
re-presentation of `f_commit` mid / the WTP level — held with D-3c and D-6 for one card sitting.
(e) WS-5A's `run_id` collapse (no case component in `iso-start-end-LABEL`) — registration seam,
WS-0's; folded into SCN-FIX1's FINDING as a note, not repaired.

**Capx (deconfliction), r#46 + am.1.** D60-R3 merged with the SCN-LOAD growth hunk unrecorded →
D60-R4 issued fresh (the r#45 D48 indictment withdrawn as majority-misattributed); **D77 chartered on
S7 as a dependency of D65-B's batch** (executed within the hour — the routing worked); D65-B released
for items 1–5, its every-bare-key batch held on D77; D63, D73, D74, D75 (FINDING PR #5100 open), D76
chartered. Q50/Q51 parked; `complete` still {ERCOT, NEISO, PJM}; **§2.1b gate NEISO only**. Files an
SCN lane needs: `invariant-failures.json` is written by the Y-lanes and both running SCN lanes —
one-appended-key-per-line, last commit after rebase, written into SCN-FIX1. No HOLD.

**Issued:** **SCN-FIX1** (Opus, zero-LP: the 18 declarations + the collate repair). **Written and
held on D-10:** the SCN-WS5A-LOAD amendment. **Held:** SCN-WS3c (criterion above), Stage A-POLICY
(releases on the paired check, no card), Stage B (§2.1b NEISO only; D-5 open).
**Cards:** **D-10 PRESENTED.** D-5 still not presentable (synthesis pending three ISOs). D-9 stands
**EXECUTED** by capx D77 (checkpoint).

---

### r#9 amendment 1 — 2026-09-06: rulings S6 (card D-8) and S7 (card D-9)

Presented as clickable decision cards in the r#9 sitting; both answers were the recommended option.

**S6 (2026-09-06), verbatim: "Relaunch now, third stem."** SCN-WS3b is relaunched as **SCN-WS3b-r3**
on `claude/scn-ws3b3-voluntary-demand-q7mv` (Fable, `ercot`), the charter written at r#9 and recorded
whole in §5. It is a zero-LP build; every case it makes expressible stays **S5-held** until the seam is
repaired, and the charter says so in its own §0. The two earlier stems are burned.

**S7 (2026-09-06), verbatim: "Yes, name it the capx director's next lane."** The owner directs that the
CCS emission-rate seam repair — `ccs.py:572`'s capture write not reaching the dispatch fleet, WS-2b
§8 item 1, NEISO 2030 CO2 +9.99 vs −6.01 Mt — be chartered as a **named capx lane, next**, with the
paired check ruling S5 already specifies as its gate: *`emission_rate` follows the retrofit*. **Routed
to the capx director** (their ledger, their next sitting) as an owner direction, not a desk request;
this desk edits none of their files and charters nothing on the seam. The release chain for Stage
A-POLICY is now: capx seam lane lands → a paired check confirms the rate follows the retrofit → the
desk releases A-POLICY under S5 with **no new card**.

**Issued on the amendment:** SCN-WS3b-r3. **Routed:** S7 to the capx director. **Unchanged:** D-5
held (no cost table), D-3c / D-6 / D-1(b) / D-1(c) open, Stage B not issuable.

---

### r#9 — 2026-09-06, main HEAD `0e20e8cf6faeb593f292af2c14d05e26d1192aa1`

*(This refresh's PR.)* Delta from the r#8 pin `34f3ce35`: **26 commits / 34 files**. `CLAUDE.md` is
**not** in the delta — rule 30(a)'s r#8 amendment is still the latest rule change. Harness branch for
this refresh: `claude/scenario-readiness-refresh-9-d0pha6`; the ledger path is unchanged.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-LOAD** | **RUNNING — CHECKPOINT (pin frozen; 0 of 16 legs solved at the last commit)** | PR #5027 (`20f9ce9f`) merged the PRECOMMIT **ADDENDUM only**: 20 new main commits re-audited, the three solve-path hunks (capx D67, nyiso-198 `cc_duct_peaking_row_scoped`, caiso-254) each classified INERT for a forecast leg with its reason (D67 unarmed in every ISO's `default_scenario_overrides`; nyiso-198 default-off and "byte-inert while off"; caiso-254 a backcast-config path), phase 0 re-run **bit-for-bit** at `1cc45bb2` (ERCOT 50,421 / CAISO 2,618 / MISO 7,067 / NYISO 851 / PJM 0 / NEISO 0 MW block deltas — same 16 legs, same P-1…P-6), and the campaign **FROZEN there**: "anything landing after this SHA is post-freeze, never retro-fitted." No results dir, no FINDING, no synthesis, no cost table → **D-5 not presentable**. The realized branch `claude/scn-ws5a-load-campaign-f5znk9` is gone from the remote (merged; the harness deletes merged heads — three remote heads exist in total), which is not a signal. |
| **SCN-WS1b-r2** | **RUNNING — CHECKPOINT, 1 of 3 live ISOs scored** | PR #5017 (`67665190`): ERCOT 2027 pair scored — **ARM NOT KILLED**. G1/G2/G3/G5/G6/G7/G8 PASS; **G4 a REPORTED MISS** (Δp/Δcarbon 0.5157 t/MWh — inside the structural bound [0, 1.08], above the lane's own band [0.9, 1.5] and above WS-4c's 1.68 point; not revised, reported at full magnitude). CO2 −0.9280 Mt (−0.36 %) on a near-1:1 coal→gas substitution (−1.29 / +1.27 TWh); hydro/nuclear/solar/wind move **0.0000 TWh exactly**; the 2026 year of both arms bit-identical (the §1 arithmetic confirmed). Leakage line 0.0000 **by construction** — no import node — so ERCOT's headline is an upper bound and carries no leakage disclosure. FINDING §0, §4 (five ISO rows), §5, §6, §8, §9 still `FILL`. Under the S2 floor only ERCOT/PJM/MISO are live at 2027 (phase-0 census: CAISO/NYISO/NEISO Δ = 0.0000 in every year), so the lane owes **two** more scored pairs, not five. Its leg 2 (the 2026–2030 ladder) stays HELD by S5. |
| **SCN-WS3b-r2** | **NO EVIDENCE OF DISPATCH — THIRD REFRESH → card D-8, not a LOST grade** | Three detectors, none conclusive alone and stated as such: (1) GitHub PR search, all time — no PR has ever carried "voluntary" / "ws3b" beyond WS-3a's two memo PRs (#4857, #4859); (2) no remote branch — weak, merged heads are deleted; (3) the session listing visible to this desk (100 newest, 2026-08-24 → now) has no WS-3b session — **but it has no WS-5A or WS-1b session either**, so the listing is scoped to this desk's own account and cannot see owner-launched lanes. Absence is evidence only beside an ask (charter §0.3); the ask is D-8. A third stem is written (§5) and held on the card. |

**TWO RESULTS FROM WS-1b-r2's ONE SCORED PAIR OUTRANK ITS VERDICT.**
1. **ERCOT's forecast REF is adequacy-collapsed at 2027, in both arms.** Load-weighted price
   **$982.31** (2026: $91.04), reserve margin **−6.5 %**, **4,621.8 GWh** of slack across **641 h**,
   invariant I3 FAIL / I12 WARN / I14 WARN in both arms. This is the known G-S4 defect (plan §5.1
   row 3, first seen on the WS-2b ladder) measured a second time, on a different lane and a
   different lever. The lane's split is the right one and is adopted here: the **CO2 delta and the
   coal→gas re-ordering are merit-order effects and ROBUST** to the collapse (both arms shed the
   same 4.6 TWh); the **price delta and the implied rate are NOT campaign-grade**, because in 641
   scarcity hours a carbon adder moves a VOLL-set price by ≈ $0 while those hours still carry
   load-weight — which also means the true fossil-marginal rate is *higher* than 0.5157 and the
   lane's G4 band was built on the wrong regime, as it says itself. **Consequence for the RUNNING
   campaign:** every ERCOT Stage A-LOAD leg differences against this REF from 2027 on, so ERCOT's
   price-side and adequacy readings are disclosure-only from 2027. Not new to the campaign lane —
   SCN-WS4c's ERCOT T1-F carried the same REF — but stated here so the synthesis reads it in rather
   than discovers it. Routed (capx G-S4 / adequacy; not this desk's to fix).
2. **The paired STOP gate G8 has a design limit the lane found on itself.** "`unserved_mwh` does
   not become non-zero in the arm while zero in REF" tests a *transition* and cannot see a REF
   that is already broken — it passed identically with 4.6 TWh unserved in both arms. The lane
   flagged it and did **not** patch a pre-registered gate, which is correct. → **Standing change
   #2** below.

**THE ROUTED SEAM THAT HOLDS HALF THE CAMPAIGN IS UNOWNED.** At capx r#45 (`c1ffbf8a`) the CCS
emission-rate seam is *named* — "WS-2b found a CCS emission-rate seam that INVERTS NEISO's headline
CO2 answer — routed there, named here" — but **no D-lane carries it**: D65-B is the VOM-adder /
fixed-cost arming (Q47), the proposed D74/D75 are the steam+oil convention and the VRE ELCC vintage,
and `git log --since=2026-09-06` on `ccs.py`, `data/emissions.py`, `data/fleet/`, `runner.py`
returns nothing on the emission-rate path. `ccs.py:572` still writes
`emission_rate_co2 *= (1 − capture)`; WS-2b's evidence (§8 item 1) is that the write is **restored
downstream** — leading candidate the plant-keyed CEMS-rate restoration (`plant_emission_rates_v2`),
which would also explain why the rate ignored the ×1.12 heat-rate rise — and that downstream path is
exactly what no lane has looked at. So **Stage A-POLICY's release condition has no owner and no
ETA.** Routed again — this time as *unchartered*, a different fact from *unrepaired* — and carried
to the owner as **card D-9**, because the capx queue's order is the owner's to direct and this
desk's only to disclose. The desk still proposes no fix and charters none.

**Records repair, against the desk's own record.** Ruling S5 (r#6 am.1) was recorded in §2 and the
D-7 paragraph was written into plan §6, but the `RULED … S5` line the charter requires on the
plan's row was **never appended**, and plan §9's ledger stops at r#5 am.1 — a reader of the plan
alone would not know D-7 is ruled. Both appended this refresh. §1's scoreboard had also drifted:
five landed lanes (WS-1c, LEVELS, LOAD, WS-1b-r2, WS-3b-r2) had no row, and the WS-1b / WS-2b /
WS-2a / MX-R-r2 / WS-4c / WS-3b rows still read r#4–r#5 statuses; reconciled to §0's record.

**G-DRIFT, third data point, in the other direction.** WS-5A-LOAD's addendum audited 20 commits /
3 solve-path hunks and classified every one INERT with a reason, at zero LP — rule 29(b)'s G-DRIFT
working exactly as written. Beside r#7 (NEISO −18.8 % stale) and r#8 (six-ISO LIVE), the pattern
is that the audit is cheap and decisive **in both directions**, and the committed keeper is a valid
control exactly when the audit says so. Still not a rule change; still routed as a pattern.

**Capx (deconfliction), r#45 at `d4113182`.** D62 landed and refused its own arm; D72 measured
ruling S2's blast radius **EMPTY** (D23 upheld); D66 split the PJM residual 78/22
requirement/supply; D60-R3 is at leg 4/5 with a fired I12 STOP; a D67 the director never chartered
landed the PJM published-requirement gate — **INERT for every SCN forecast leg** (unarmed in every
ISO's overrides; WS-5A's addendum verified it). Q50/Q51 (CAISO/NYISO `complete`) **parked at owner
direction** — `complete` still {ERCOT, NEISO, PJM}, `final` empty; **§2.1b gate NEISO only**. No
capx lane holds a file an SCN lane needs; **no HOLD**. Live owner backcast PR #5030 (nyiso-198)
touches `campd_bins.py` only. The matrix guard is RED at r#45 on nyiso-198's field (rule 28c, the
adding lane's) — the rule-28(c) enforcement gap SCN-MX-R-r2 diagnosed is still open as a mechanism.

**STANDING CHANGES, written into every future charter from r#9:**
1. *(from r#8)* A lane whose deliverable is a **pre-declaration** states the constant families it
   depends on, so a later intake's blast radius on it is computable rather than discovered.
2. *(new, from WS-1b-r2 §3.3)* A **paired-probe STOP gate asserts a REF-side precondition**
   (adequacy: `unserved_mwh`, reserve margin, I3) **and** a no-worsening condition — never the
   transition alone. A REF that is already broken must fail the gate's premise, not pass its
   delta.

**Issued:** nothing unconditionally. **SCN-WS3b-r3** written (§5) and **held on card D-8**. Stage
A-POLICY stays HELD (S5; the seam is unrepaired *and* unchartered). **D-5 not presentable** — no
synthesis, no cost table. Stage B not issuable (§2.1b NEISO only; D-5 open).
**Cards:** **D-8** (SCN-WS3b: relaunch now under the third stem, hold, or drop the axis) and **D-9**
(direct the capx director to charter the CCS emission-rate seam repair) **PRESENTED**. D-5 held.

---

### r#8 — 2026-09-06, main HEAD `34f3ce357fbdfd245e54a89e734f2c003829de7c`

*(PR #5016.)* Delta from the r#7 pin `e80bdd87`: **31 commits**.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS5A-LOAD** | **RUNNING — PRECOMMIT pushed before the first solve** | `cf05fbfb`, branch `claude/scn-ws5a-load-campaign-f5znk9`. Pin re-fetched to `821c11c5` with the two intervening commits verified docs-only (zero diff on `src/`, `scripts/`, `configs/`) so the G-DRIFT audit and phase 0 carry unchanged — the right way to handle a moving base. |
| **SCN-WS1b-r2** | Six-ISO carbon paired probe (leg 1, 2027-scoped); leg 2 held by S5 | **IN FLIGHT r#8** | `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz` | **Opus** | Pre-registered **SCN-WS4c's measured implied-marginal rate as a second yardstick** before solving — one lane folding another's finding into its own gate across a refresh. Solves pending on the desk-ratified 2027 scope. |
| **SCN-WS3b-r2** | Voluntary-demand build, released by S1 | **NO EVIDENCE OF DISPATCH r#8** | `claude/scn-ws3b2-voluntary-demand-k8zp` | **Fable** | Two refreshes, two asks, no branch or commit. **Blocks nothing today** — it feeds only the S5-held policy half. Not re-issued unless the owner wants it; a third stem is available. |

**ONE DEVIATION FROM THE DESK'S ISSUANCE, GRADED ACCEPTABLE.** The desk issued Stage A-LOAD as
**six per-ISO lanes** plus a synthesis, on the reasoning that per-ISO disjointness is what keeps
concurrent lanes from colliding. The lane that launched runs **all six ISOs in one invocation**
(its §1.1 states the choice). The desk grades this by content rather than by conformance: the
collision risk the six-lane split existed to manage is **absent when there is one writer**, rule
12's binding constraint (years sequential within an invocation, ≤ 2 concurrent, 1 when a per-plant
ISO runs) is *easier* to honour in a single lane, and the campaign's own synthesis no longer needs
a seventh session. **Accepted as issued.** The desk records that its six-lane form was the more
cautious construction and was not the necessary one.

**THE FINDING OF THIS REFRESH — ruling S4 moved the target the pre-declaration chain scores
against, and the desk's own ruling chain caused it.** The sequence, stated plainly:
1. At r#5 the desk recommended **defer** on card D-4, and SCN-WS4a's own gap list recommended
   defer. The owner ruled **S4 = FUND THE FULL DATATYPE**, over both recommendations.
2. SCN-LOAD executed it. `d14a7ed0` re-derived the load-shape constant family — **473 insertions /
   263 deletions in `constants.py`**, across `DEMAND_GROWTH_RATES`, `DATACENTER_ADDITIONS_MW` and
   `ELECTRIFICATION_LAYERS` — which is exactly what "curate the six published forecasts" means and
   exactly what the ruling asked for.
3. It landed **after** SCN-WS4b's pin `af6269cf`. So **WS-4b's six pre-declared readings, and
   SCN-WS4c's 20 HIT / 3 SPLIT / 3 MISS scoring of them, were both computed on constants that have
   since moved.**

**What this does and does not mean.** It does **not** invalidate either lane: each was correct at
its own pin, each said what pin it stood on, and the pre-declaration discipline is what makes the
movement *visible* instead of silent. What it means is that **the horizon HIT/MISS scoring runs
against a moved target**, and three specific readings are now known to be stale before a single
horizon LP is spent — measured by the campaign lane at zero LP cost:

| ISO | WS-4b / WS-4c said | HEAD says | consequence |
|---|---|---|---|
| **CAISO** | `high := mid`, byte-identical, "should not be solved" | `high` **4,240 MW** vs `mid` **1,622 MW** at 2030 (CEC Form 1.1c, read by the intake) | the ORGANIC arm is **live**; the campaign is **16 legs, not 15** |
| **PJM** | `high := mid` through 2030 | `high := mid` at **every** anchor — published B-9b overtook the retired 30 GW queue estimate | same operational conclusion, **different mechanism**; recorded so the record is right rather than merely unchanged |
| **ERCOT** | tail-regime ratio **1.019 (TAIL)** at 2030 | DC high anchor fell **122 → 88.6 GW (−27 %)** while the growth rate **rose** | ratio predicted **below 1.0 (relocate)** — the lane's own headline test |

**The desk's position, stated against itself.** Neither the desk nor SCN-WS4a anticipated, when
recommending defer, that the intake's *value* would arrive as a **re-derivation that supersedes a
live pre-declaration mid-campaign**. That is an argument the desk did not make and should have:
"defer" was argued on provenance grounds ("the campaign runs on the cited constants today"), and
the real cost of funding was never the work — it was the **ordering**. The owner's ruling has been
vindicated on substance (three constants were wrong or stale, and one of them, CAISO, was
suppressing a leg the campaign needs) and the desk's sequencing was the weak part. **Standing
change: from r#9, any lane whose deliverable is a pre-declaration states the constant families it
depends on, so a later intake's blast radius on it is computable rather than discovered.**

**G-DRIFT reads LIVE on every ISO, twice over** — 82 files / +9,529 lines on the solve path, **and**
the load-constant re-derivation making every committed REF trajectory unreproducible at HEAD. Rule
29(b) form 4 is therefore invalid for all six ISOs and the control is the lane's own same-HEAD REF
leg. This is the second consecutive refresh in which a measured G-DRIFT audit has overturned rule
29(b)'s stated default (SCN-WS4c measured NEISO stale by 2.821 Mt at r#7). **Two measured cases is
still not a rule change** and the desk proposes none — but it is now a pattern worth the audit
track's attention, and it is routed as one.

**Rule changes since r#7.** Rule 30(a) amended again (owner, verbatim: *"the formatting on the html
dashboard for holdout years shouldn't be any different than the 3 training years"*) — a held-out
year renders **as a year, not as a designation**. No SCN lane touches a touchpoint; recorded only.

**Capx.** D60-R3 leg 4/5 re-solved `pjm-t1f` and **a pre-declared STOP FIRED on I12** — reported
rather than absorbed, cause identified as a requirement P23 assumed would not move. D66 reconciled
the PJM supply census against PJM's own BRA record at zero LP. D67 is in flight with a G-DRIFT
that "comes back LIVE" — three lanes now reporting the same thing. **The CCS seam holding
Stage A-POLICY is still unrepaired at this pin.**

**Issued:** nothing — Stage A-LOAD is running and no other precondition moved.
**Cards:** none newly presented. D-5 becomes answerable when the campaign's synthesis lands.

---

### r#7 — 2026-09-06, main HEAD `e80bdd87bad0cb0622678b84736bc0cd7fa148f7`

*(PR #5001.)* Delta from the r#6 am.1 pin `0027a6c9`: **42 commits**.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F, scored against WS-4b's pre-declared readings | **LANDED r#7 — COMPLETE** | `claude/scn-ws4c-load-hi-probes-o85iyi` (PRs #4986/#4990/#4993/#4996/#4997) | **Opus** | 19 arms all clean; **20 HIT / 3 SPLIT / 3 MISS** against WS-4b; phase 0 killed three arms at zero LP; three of its own predictions missed and reported at full magnitude. **Its two headline results — the biased fossil-average heuristic and the measured G-DRIFT vindication — outrank its scorecard** (§0 r#7). **Releases Stage A-LOAD.** |
| **SCN-WS1b-r2** | **IN FLIGHT — re-scoped by its own phase 0** | `a13d298b` the PRECOMMIT addendum (pushed before any solve, original never edited), `9c8f67a6` the 2027 scope call + retargeted instruments, `e5bfe1d4` the FINDING skeleton. **No solve spent yet** — the phase-0 gate refused the arms, which is rule 29 clause (0) working exactly as written. |
| **SCN-WS3b-r2** | **NOT SEEN — asked again** | No branch, no commit. One refresh after the relaunch. Feeds only the S5-held half, so it is not on Stage A-LOAD's path. |
| **SCN-LOAD** | LANDED r#6; branch still open | `claude/scn-load-forecast-intake-t17qxj` remains unmerged-but-landed (its content is on main via PR #4970). No action. |

**THE DESK'S OWN CHARTER WAS WRONG, AND THE LANE CAUGHT IT BEFORE SPENDING AN LP.**
At r#6 amendment 1 this desk re-scoped SCN-WS1b with a change it stated confidently:
> *"the reduced form is RETIRED; run the real thing … D-1 is now ruled S2 = FLOOR, and SCN-WS1c
> has LANDED the repair. So leg 1 runs `--set carbon_price_path=mid`, the charter's original full
> form."*
That was wrong on a fact the desk did not check. `CARBON_PRICE_PATHS`
(`config/fuel_trajectories.py:1132-1137`) anchors **every** registered RFF path at **$0 in 2026** —
2026 is the paths' common origin knot — so **no `carbon_price_path` value of any kind can produce
a signal in a 2026-only solve**. The lane's re-census through the solves' own builder measured
Δ2026 = 0.0000 in **all six** ISOs, for two different reasons: the floor on CAISO / NYISO / NEISO
(as predicted), and the path's own $0 origin knot on ERCOT / PJM / MISO (not predicted at all).
The desk's error was to treat `carbon_price_delta` as a *workaround for an open card* when it was
in fact **the only form that yields a 2026 signal**; ruling S2 changed which form is right for a
horizon leg, and changed nothing about the 2026 leg.
**RATIFIED: the lane's minimal repair, `--end-year 2027`.** It is the smallest change that makes
the arm live (the mid path's 2027 knot is +\$3.75/t on the three non-program ISOs), and it stays
**below `ccs_retrofit_available_year` (2028)**, so it remains inside Stage A-LOAD under ruling S5.
The lane may proceed on it without a further card.

**SCN-WS4c'S TWO RESULTS THAT OUTRANK ITS OWN SCORECARD.**

1. **The fossil-average heuristic is biased, and the bias has a sign you can predict.** The
   implied marginal CO2 rate against the fossil-fleet average:
   | with inframarginal coal | | gas-dominated | |
   |---|---|---|---|
   | ERCOT | 0.73× | CAISO | 1.05× |
   | PJM | 0.77× | NYISO | 1.05× |
   | MISO | 0.65× | NEISO | 1.17× |
   The charter's own expectation — *"CO2 rises ≈ fossil-average rate × added fossil-served MWh"* —
   is therefore **high by 23–35 % where coal is in the stack and low by 5–17 % where it is not**.
   This is not noise and it is not a defect: it is the merit order doing its job, and it means
   **every future LOAD-shaped expectation in this campaign should be written against the implied
   marginal rate, not the fleet average.** Folded into the Stage A-LOAD charter.
2. **G-DRIFT was vindicated by measurement — and that is evidence about rule 29(b), not just
   about this lane.** ERCOT's REF T1-F reproduces the committed `ff-t1f-d50` bundle *exactly*.
   NEISO's does **not**: up to **2.821 Mt, −18.8 % in 2030**, with d50's 50 MW backstop firing
   gone. Rule 29(b) states that *"the incumbent keeper's COMMITTED bundle IS the control"* and
   makes form 4 the **default**; on this ISO that default would have measured the entire
   deployment response against a stale reference, and only the code-level G-DRIFT audit the same
   rule prescribes caught it. **Routed to the capx director and the audit track** as a measured
   case where 29(b)'s default failed and its own escape hatch saved it — the desk takes no view on
   whether the rule should change, and states plainly that one measured case is not a rule change.

**STAGE A-LOAD IS UNBLOCKED. ISSUED THIS REFRESH.** Every precondition verified on main at this
pin: SCN-WS0 (all six items), SCN-WS4a, SCN-WS4b, SCN-WS4c (FINDING landed), SCN-LEVELS, SCN-LOAD.
Ruling S5 is the authorization and **no further card is needed**. Six per-ISO lanes
(`SCN-WS5A-LOAD-<ISO>`) plus `SCN-WS5A-LOAD-SYNTH` after they register. The carbon half of A-LOAD
rides SCN-WS1b-r2's ratified 2027 legs and is **not** a precondition — A-LOAD's three load cases
stand alone, and the synthesis says so if WS-1b-r2 has not landed.

**Capx deconfliction.** **D72 measured the blast radius of this desk's own ruling S2** — the G-C1
carbon-nulling radius is **EMPTY** and D23 is re-examined and **upheld** (`6e5d7b88`, `5a4761dd`).
That is the right outcome to record for a ruling the desk pushed: it changed no committed result.
D60-R3 and D66 have live branches; neither touches an SCN region. The CCS seam that holds
Stage A-POLICY is still unrepaired at this pin.

**Issued:** `SCN-WS5A-LOAD-<ISO>` ×6 + `SCN-WS5A-LOAD-SYNTH`.
**Cards:** none newly presented. **D-5 becomes answerable the moment SYNTH lands** — it will carry
the measured Stage-A-LOAD cost table its charter has always required.

---

### r#6 amendment 1 — 2026-09-06: ruling S5 on card D-7

**S5 (2026-09-06), verbatim in effect: HOLD THE POLICY HALF; RUN THE LOAD HALF NOW.** Stage A
splits along the one line the defect actually draws — whether a case moves `gas_cc_ccs`.

| | cases | CCS exposure | status |
|---|---|---|---|
| **STAGE A-LOAD** | `REF`, `LOAD-HI`, `LOAD-HI-ORGANIC` across six ISOs at T1-F 2026–2030; plus the pure-carbon **T0 2026** probes | **none** — the retrofit screen is inert below `ccs_retrofit_available_year` (2028) by construction, and a 2026-only T0 never reaches it | **RELEASED.** Issued the refresh SCN-WS4c lands (its probes are this half's T0 leg). |
| **STAGE A-POLICY** | every `CES-*` case, every carbon case at or above 2028 (`CARB-*` T1-F legs), `ALL-CLEAN`, and `VOL-*` / `CES-P20+VOL-HI` when they exist | **yes** — these are the cases whose CO2 number may be sign-wrong | **HELD** until the capx CCS emission-rate seam is repaired and a paired check confirms `emission_rate` follows the retrofit. |

**Why this is the cheap answer, stated so a successor does not re-litigate it.** The alternative
the desk offered — run everything now, re-solve the affected cases after the repair — spends the
LP twice on most of the policy half (six ISOs × the CES ladder + the 2028+ carbon legs), and the
alternative of holding *everything* would park the load half behind a defect it has no exposure
to. S5 takes the only split that costs neither.

**What the desk does with it, and what it does not.** Recorded here and in plan §6; **routed to
the capx director as a priority signal** — the CCS repair (D50/D60/D65 lane) now gates half of a
chartered campaign, which it did not before this refresh. The desk **issues nothing on this
ruling today**: Stage A-LOAD's precondition is SCN-WS4c, still in flight. When WS-4c lands, the
six `SCN-WS5A-LOAD-<ISO>` lanes and their synthesis are issuable **without a further card** —
S5 is the authorization for that half.

**One scope note recorded against interest.** The `VOL-*` cases are placed in A-POLICY, not
A-LOAD, even though the voluntary row's default eligible set is renewable-only and does not credit
CCS. The reason is that a voluntary attribute row still *displaces thermal*, and in a 2026–2030
window NEISO's CCS fleet exists from 2028 — so a `VOL-*` leg can move `gas_cc_ccs` indirectly. It
is moot for sequencing today (SCN-WS3b has not started), but the placement is deliberate rather
than inherited.

---

### r#6 — 2026-09-06, main HEAD `ad45b0e454022e55ac76d1e03e0e6c207ae86be2`

*(PR #4970.)* Delta from the r#5 pin `3dcf1b22`: **113 commits**. The four lanes released by
rulings S1–S4 were issued and, for three of the four, launched and landed inside a single day.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS1c** | The floor repair — plan §7 "WS-1a" item 1, released by S2 | **LANDED r#6** | `claude/scn-ws1c-carbon-floor-tmlmjl` (PRs #4956/#4961/#4967) | **Fable** | Ruling S2 executed. PRECOMMIT predicted the repair before the code; a **second copy of the replace assertion** was found by the parity sweep; full suite accounted to baseline (264−20=244); matrix re-stamped. Routed a CI-red it had not caused rather than reaching into another track's file — **now green** (§0 r#6). |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **LANDED r#6 — the session's most consequential lane** | `claude/scn-ws2b-ces-clearing-y40sks` (PRs #4909/#4963-adj) | **Opus** | All six ladder legs solve and register; the clearing script closes the G-S2 bracket for one cell (NEISO 2026, 0.00 pp, and honest about *why*); ERCOT saturates \$20–\$40 on `iso_budget_exhausted`. **Found the CCS emission-rate seam that sign-flips NEISO's headline CO2 (+9.99 → −6.01 Mt)** and routed it rather than fixing another track's file. |
| **SCN-LEVELS** | Commit the §3.5 campaign levels, released by S3 | **LANDED r#6** | `claude/scn-levels-*` | **Fable** | S3 executed: levels committed, `CES-T80` made live, docstrings de-illustrated. Its FINDING **measures** rather than asserts that the committed levels are the levels the lanes ran. |
| **SCN-LOAD** | The full six-source `load-forecast` curated datatype, released by S4 | **LANDED r#6** | `claude/scn-load-forecast-intake-t17qxj` (PR #4970) | **Opus** | S4 executed. Scope note pushed first with **obtainability measured per source**, so the closure is scored against a prediction; the six published forecasts curated as the datatype. |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F, scored against WS-4b's pre-declared readings | **IN FLIGHT r#6** | `claude/scn-ws4c-load-hi-probes-o85iyi` | **Opus** | PRECOMMIT + a **zero-LP phase 0** confirming WS-4b's arithmetic is HEAD's (rule 29 step 0 working) + harness + the first T0 slim artifacts. Owed: the rest of the battery, the two T1-F legs, the HIT/MISS scoring, the FINDING. |
| **SCN-WS1b-r2** | Six-ISO carbon paired probe (leg 1); leg 2 held by S5 | **IN FLIGHT r#7 — re-scoped by its own phase 0** | `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz` | **Opus** | Its phase-0 gate **killed the desk's charter at zero LP**: every RFF path anchors at \$0 in 2026, so no `carbon_price_path` produces a 2026 signal. **Desk RATIFIES `--end-year 2027`** — still below 2028, still S5-safe. Solves pending. |
| **SCN-WS3b-r2** | Voluntary-demand build, released by S1 | **NOT SEEN r#7 — asked again** | `claude/scn-ws3b2-voluntary-demand-k8zp` | **Fable** | One refresh after relaunch. Feeds only the S5-held half, so it is **not** on Stage A-LOAD's path. |

**THE HEADLINE FINDING, AND IT IS NOT A CES FINDING.** SCN-WS2b's re-prove existed to catch
exactly this class of thing, and it did. In NEISO the CES premium's **entire** response is
`gas_cc_ccs` (17.1 → 59.7 TWh at 2030), and **those retrofitted units are credited at 0.95 by the
CES while carrying an UNCAPTURED emission rate in the dispatch fleet.** Measured on a single unit
across its own retrofit year:

| field | before | after | verdict |
|---|---|---|---|
| `fuel_type` | `gas_cc` | `gas_cc_ccs` | ✓ |
| `heat_rate` | 7.5101 | 8.4113 (×1.12, the parasitic penalty) | ✓ |
| `emission_rate` | 0.3745 | **0.3745** | ✗ **unchanged to four decimals** |

Three writes in the same block of `ccs.py`; two persist, one is overwritten downstream. **The
consequence is a sign flip on the campaign's own headline metric:** as scored the premium *raises*
NEISO 2030 CO2 by **+9.99 Mt**; with the intended 90 % capture applied as an accounting
recomputation at fixed dispatch it *cuts* it by **−6.01 Mt**.
**Not this desk's to fix and not SCN-WS2b's** — `ccs.py`, `data/fleet/` and `runner.py` are all
outside that lane's regions and the CCS seam belongs to the capx D50 / D60 / D65 lane. **Routed
to the capx director** with the arithmetic attached (WS-2b FINDING §8). What the desk adds is the
scope statement the routing needs: **every campaign case that moves `gas_cc_ccs` has a CO2 number
that may be sign-wrong until this is repaired** — which is the CES cases, the carbon cases above
`ccs_retrofit_available_year` (2028), and `ALL-CLEAN`. That is most of Stage A's policy half, and
it is why **card D-7 is presented** rather than the desk quietly sequencing around it.

**A SECOND, OPPOSITE LEAKAGE RESULT — the campaign is now measuring something real.** WS-0
measured a $25/t carbon adder exporting two thirds of its NEISO CO2 reduction across the NYISO
seam. WS-2b measures the CES premium doing **the reverse**: `import_co2_mt_reported` **falls**
6.38 → 3.36 Mt at 2030 (−3.02 Mt) as 17.5 TWh of imports are repatriated. Two instruments, two
opposite signs, both measured — the import line WS-0 built is earning its place.

**OTHER SUBSTANTIVE RESULTS WORTH THE OWNER'S ATTENTION.**
- **The ERCOT ladder now SATURATES between \$20 and \$40**, because the binding constraint in
  every premium year is `iso_budget_exhausted`, **not economics**. Direction holds table by table
  against July; levels do not, and every level change is charged to a named flip or reported as
  unattributed — which is what item 1 was for. ERCOT's BAU commissioned VRE collapses
  **14 GW → 0.65 GW** and its CES-40 build falls **37 GW → 24 GW** since July.
- **The G-S2 bracket CLOSES for one cell, and closes for an honest reason.** SCN-WS2a's target-row
  probe landed mid-session, so the uniform-share half existed after all: at NEISO 2026 both
  representations read **0.3447**, gap **0.00 pp** — and they agree **because neither moves
  anything** (the premium is dispatch-inert there; the 0.55 target row escapes at its ACP). The
  cross-ISO spread under a uniform price grows **8.7 pp (2026) → 35.2 pp (2030)**.

**THE ROUTED CI-RED IS ALREADY GREEN — verified, not assumed.** SCN-WS1c routed a rule-28(c)
breach on pristine `main`: `capacity_going_forward_bar_published_by_iso`, a shared field landed
with the capx D60-R3 merge, had no matrix row and no ratchet entry, turning `mechanism-matrix-guard`
red on every open PR. The lane correctly refused to fix another track's cell (rule 28(d)) and
routed it. At this pin the desk re-ran `scripts/check_mechanism_matrix.py` on a clean checkout:
**exit 0, "absent-shared ratchet OK".** The capx track discharged it. Closed, with the lane's
handling recorded as correct: it reported a red gate it had not caused and did not reach into
another lane's file to clear its own PR.

**RULE CHANGES SINCE r#5 — three, and two bind SCN lanes directly.**
- **Rule 21 `[R-DOF]`** gains the R-AY cross-reference: an authorized `offer_curve_by_group`
  multiplier IS a ledgered free parameter, identified by the ruling rather than a measured source,
  and its presence does not by itself make the residual it closes an open root-cause issue.
- **Rule 22 `[R-HOLDOUT]` gains the R-AZ registration-time marker re-check** — the launch gate
  read the marker once, so a multi-hour solve could outlive its authorization;
  `dashboard_add_run.py` now re-asks at registration, **with no bypass flag**. Binds any SCN lane
  registering a run: a refused registration is not a registration.
- **Rule 30 `[R-TOUCHPOINT-FOLD]`** is now written out in full (stamp to the keeper, rebuild the
  status ladder, a held-out year never downgrades the ISO) plus rubric **v3.6** (on an
  out-of-training year C3c's lone-failure condition is dropped). No SCN lane touches a touchpoint.

**WHAT IS UNBLOCKED: nothing new, and the reason is worth stating.** SCN-WS3c still needs
SCN-WS3b, which has not started. Stage A still needs SCN-WS1b, SCN-WS4c and the WS-3b→WS-3c pair.
**The gate on Stage A is no longer a ruling — it is three lanes and one defect.**

**Issued:** nothing. **Cards:** **D-7 PRESENTED** (Stage A vs the CCS seam). D-3c and D-6 remain
open; D-5 remains correctly held.

---

### r#5 — 2026-09-06, main HEAD `3dcf1b220ed2cf2bbb62e38b4af3906510c83a5f`

*(PR #4921.)* Delta from the r#4 pin `21deb4a7`: **79 commits** — the largest since the desk
opened. SCN contributed fourteen; the rest is capx r#42 (+2 amendments), the audit program's
Y-15/Y-16/G-3 lanes, owner-track miso-221 / nyiso-197, and three CLAUDE.md rule changes.

**GRADED BY CONTENT:**

| lane | verdict | evidence |
|---|---|---|
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **LANDED r#5 — COMPLETE** | `claude/scn-ws2a-federal-ces-qm512t` (PRs #4870/#4892/#4902) | **Fable** | Every charter item in: the row on the clean-tier family, the coupling relaxation (WS-3b's precondition), two fields, the postures, the docs legs, the **NEISO T0 probe registered** (`c5f9358a`), the FINDING, and the matrix row + one cell per shard as its **last commit** (`d57cf785`). |
| **SCN-WS4b** | Pre-declared adequacy reading per ISO under LOAD-HI + the LOAD-HI / LOAD-HI-ORGANIC cases + the `backstop-built` column | **LANDED r#5** | `claude/scn-ws4b-load-hi-adequacy-jvv96t` (PR #4916) | **Fable** | **The r#4 LOST call is WITHDRAWN — launched late, not never launched** (§0 r#5 correction 1). Both cases declared, six per-ISO readings pre-declared in `load-hi-adequacy-reading-2026-09-06.md`, the column + its test. No solve by charter. **Unblocks SCN-WS4c.** |
| **SCN-MX-R-r2** | The rule-28 duty-(c) CI diagnosis; the verified-outstanding cache-epoch entry; the CES row conditionally | **LANDED r#5** | `claude/scn-mxr2-matrix-duty-repair-lk9ndd` (PR #4910) | **Fable** | Diagnosed the gap and **corrected the desk's own reading of it** (§0 r#5 correction 2); wrote the epoch entry; **left the CES row to live SCN-WS2a rather than racing it**, exactly as chartered — and WS-2a then landed it. |
| **SCN-WS1c** | The floor repair — plan §7 "WS-1a" **item 1**, released by ruling S2 | **ISSUED r#5 am.1** | `claude/scn-ws1c-carbon-floor-v2rk` | **Fable** | The item SCN-WS1a's card gate correctly withheld. Owns `policy/cap_and_trade.py`, the D34 guard, one `results/cache.py` epoch entry, the carbon tests. Byte-identity for every keeper and every zero-path forecast bundle is a deliverable. |
| **SCN-WS3b** | Voluntary-demand build, released by ruling S1 | **ISSUED r#5 am.1** | `claude/scn-ws3b-voluntary-demand-n5wq` | **Fable** | Builds the WS-3a memo's signed design: the annual volumetric row (D-3b deferred, so **no hourly block**), the DC-linked volume resolver, three fields, constants with citations, matrix row + six cells. **D-3c is still open** — builds the memo's recommended eligible set and flags it. |
| **SCN-LEVELS** | Commit the §3.5 campaign levels, released by ruling S3 | **ISSUED r#5 am.1** | `claude/scn-levels-d2-commit-c3jx` | **Fable** | Records lane, **zero solves and zero numeric change**: relabels SCN-WS2a's illustrative CES target / ACP as committed, writes the levels into the campaign YAML and the plan §3.5 table. Takes `configs/scenario_campaign_matrix.yaml` ownership from SCN-WS4b. |
| **SCN-LOAD** | The full six-source `load-forecast` curated datatype, released by ruling S4 | **ISSUED r#5 am.1** | `claude/scn-load-forecast-intake-w9tf` | **Opus** | **S4 overrode the desk's own recommendation to defer.** Uses the `data-intake` skill. The MISO driver-level 403 host wall is flagged at the gate. Closes G-D4-1..G-D4-4; G-D4-5 (`DEMAND_GROWTH_TRANSITION_YEAR`, no published source) stays a disclosed null. |
| **SCN-WS1b** | Six-ISO carbon paired T0 probe + NEISO/ERCOT delta ladder + the per-ISO leakage line | **IN FLIGHT r#5** | merged through `main` (`ed7fd527`, `acf5ed1f`, `e68e1971`) | **Opus** | PRECOMMIT pushed before any solve (rule 29 honoured); T0 scoring instrument, both leg launchers, registration helper and bundle gitignore in. **Owed: the twelve registrations, the ladder legs, the leakage table, the FINDING.** |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **IN FLIGHT r#5** | `claude/scn-ws2b-ces-clearing-y40sks` (live; PR #4909 merged item 2) | **Opus** | PRECOMMIT pushed before any solve; **item 2 landed — the uniform-price half of the G-S2 bracket**. Owed: item 1's ERCOT+NEISO ladder re-prove, the July table-by-table attribution, the FINDING. |

**CORRECTION 1 — the r#4 LOST call on SCN-WS4b was wrong in fact.** The charter's rule is *no
branch and no PR two refreshes after issuance ⇒ LOST*, and at the r#4 pin that was literally
true. The lane then launched on `claude/scn-ws4b-load-hi-adequacy-jvv96t` — a third name,
neither of the two stems the desk issued — and landed its whole charter. So "never launched"
is **withdrawn**; the record is **launched late**. What this says about the threshold: a
two-refresh window measured in hours is too tight when refreshes are hours apart rather than
days, and branch-name matching is a weak detector because the harness never uses the issued
stem. Standing change for r#6 onward: **before grading a lane LOST, ask dispatch status
first** and treat absence as evidence only alongside it. The relaunch cost nothing here (the
`-r2` charter was never dispatched either), but the grading was wrong and is recorded as such.

**CORRECTION 2 — the desk's CI-gap claim was wrong, and the truth is worse than the claim.**
Across r#2, r#3 and r#4 this ledger asserted that `check_mechanism_matrix.py` "exited 0", so
its duty-(c) half "did not fire", confirmed "across three pins". SCN-MX-R-r2 established
otherwise (`FINDING-scn-mxr-2026-09-06.md` §1.1):
- On PR #4870 the guard **ran and failed** — job `101393800190` prints both
  `::error … new ScenarioConfig field … is not registered` lines and exits 1.
- The PR was **created at 23:28:44Z and merged at 23:28:49Z** — five seconds — so the failure
  was reported to an already-merged PR. The guard is **not a merge-blocking required status**,
  and **seven of its eleven checks were red** (fast tests, refactor guards, quarantine gates,
  forecast parity, invariant audit, shrink-guard, this one).
- The desk's three exit-0 readings were the checker's **validate-only mode** (no `--base`),
  which returns at `if not args.base:` *before* the registration diff leg — it asserts store
  integrity and keeper-stamp parity and **never was a registration verdict**. Reading it as one
  was the desk's error.
- The durable hole it *does* have: **any shared (no ISO stem), forecast-only, or
  keeper-unarmed `ScenarioConfig` field that reaches `main` without its row is invisible to
  every later run** — `gap_ratchet` only walks ISO-stemmed fields and `shared_gap_ratchet` only
  sees fields armed on a backcast keeper, which a forecast-only field refused in backcast mode
  can never be. A `carbon_*`, `storage_*`, `ccs_*` or `entry_*` field would be swallowed the
  same way.
Routed by the lane to the capx/audit track, which owns the CI surface. **Not this desk's to
repair**, and the desk states plainly that its own three-pin "confirmation" was an artifact of
running the checker in the wrong mode.

**WHAT IS NOW UNBLOCKED — one lane, and it is the last one before Stage A.**
- **SCN-WS4c — UNBLOCKED, ISSUED.** Its three preconditions (WS-0, WS-4a, WS-4b) are all on
  main; WS-4b's own FINDING closes with *"This landing is the LAST thing blocking SCN-WS4c."*
- **SCN-WS3b** — still blocked on **card D-3 alone**, open since r#1. Both code preconditions
  have been met since r#3.
- **SCN-WS5A ×6 + SYNTH** — the gate is now: WS-1b and WS-2b landing, WS-4c landing, and
  **either D-3 ruled YES with WS-3b/c landed, or D-3 ruled NO** (in which case the `VOL-*` and
  `CES-P20+VOL-HI` cases drop from the campaign with a ledger note). **D-3 is on the critical
  path to Stage A now**, which it was not at r#1 — worth the owner knowing.
- **Stage B** — unchanged: needs card D-5 **and** an open §2.1b gate at issuance.

**THE STAGE-B PICTURE WIDENED, AND NONE OF IT IS THIS DESK'S TO MOVE.** Three ISOs now hold
CALIBRATED keepers while absent from `complete`, so their gate leg (a) reads FAIL:
| ISO | keeper | card | ruling |
|---|---|---|---|
| **NYISO** | `2026-09-06-nyiso-196-extract-basis` | C-19 / **Q51** — served by capx r#42 am.1 after **this desk's r#4 routing** | **HOLD ONE REFRESH** |
| **MISO** | promoted CALIBRATED (capx r#42) | C-17 / Q49 | **DECLINED** |
| **CAISO** | promoted CALIBRATED (capx r#42) | C-18 / Q50 | **HOLD until caiso-253** |
`complete` still reads {ERCOT, NEISO, PJM}. The desk records the state and the consequence — if
all three were declared, five of six ISOs would clear leg (a) and card D-5 would be a very
different question — and declares nothing.

**RULE CHANGES SINCE r#4, all four written into SCN-WS4c's charter.**
- **Rule 1 `[R-STRUCT]` amendment (owner, 2026-09-05):** the registered `offer_curve_by_group`
  band multipliers are an **authorized price-tuning channel**, under five binding conditions
  (band multipliers only; one config across every scored year; declared ex ante in the PREREG
  and **never swept against the gates**; merit-order movement is intended; declared in the
  attestation's `authorized_price_tuning` block and carried as a DOF free parameter). The first
  half of rule 1 is untouched.
- **Rule 13 `[R-MEASURED]`** carries the same exception, for the offer curve and nothing else.
- **Rule 29 gains clause (c) DELETE BEFORE MERGE** *(owner ruling R-AV)*: a screen bundle, and
  any control bundle a screen earns, **is deleted from `results/calibration/` before its PR
  merges** — the doc carries every number, and an unregistered bundle dir is a parity gate RED,
  not an allowlist candidate. Binds any SCN lane that produces a screen bundle.
- **New rule 30 `[R-TOUCHPOINT-FOLD]`:** a touchpoint publishes AS the keeper, not beside it.
  No current SCN lane touches a touchpoint; recorded so none assumes otherwise.

**Capx deconfliction (r#42 + two amendments).** **D60-R2 is DEAD** after four silent sittings →
**D60-R3 issued** with the D71 drift bisect folded in; **D65 Act A landed** and its own G-DRIFT
was wrong, surfacing material reproducible HEAD drift → D71; Q47 arm coupled after D60-R3 →
D65-B. No capx branch is live at this pin. The matrix tree now has SCN-WS2a's landed row plus
capx D65's — the last-commit one-line protocol held on both, with no conflict.

**Issued:** SCN-WS4c.
**Cards:** none newly ruled on the SCN side. **D-3 has moved onto Stage A's critical path.**

---

### r#4 — 2026-09-06, main HEAD `21deb4a75fd2d2c1d1b2c8ed4070968fe818313c`

*(PR #4894.)* Delta from the r#3 pin `ea273339`: **14 commits** — the desk's own r#3 (#4888,
merged), SCN-WS2a's two branch commits (#4892), wallclock A-2/A-6, and nyiso-196.

**THE ANSWER TO "WHAT ELSE IS UNBLOCKED": nothing, by code.** Checked against every queued
lane's actual precondition, not its label:

| lane | precondition | state at `21deb4a7` |
|---|---|---|
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F, scored against WS-4b's pre-declared readings | **ISSUED r#5** | `claude/scn-ws4c-loadhi-probes-q8vd` | **Opus** | **UNBLOCKED** — WS-0, WS-4a and WS-4b all on main. The last lane before Stage A. |

| **SCN-WS5A** ×6 | the whole wave-2 set | blocked — WS-1b/WS-2b in flight, WS-2a owed, WS-4b/c not started |
| **Stage B** | card D-5 **and** an open §2.1b gate | not issuable; D-5 is held until Stage A's measured cost table exists, which is the correct order |

**THE ONE REAL UNBLOCK IS GOVERNANCE, AND IT IS NOT THIS DESK'S TO TAKE.** On 2026-09-06 the
owner-track lane nyiso-196 promoted `2026-09-06-nyiso-196-extract-basis` and it reads
**CALIBRATED — grade 7, fails 0, C3c the lone ledgered caveat**, on a rule 14 + rule 13 + rule 1
basis with zero free parameters and zero new DOF entries. NYISO's `withdrawn` block states its
own re-entry condition verbatim: *"re-entry is a NEW explicit owner declaration on a keeper
scoring CALIBRATED."* **The condition is satisfied. The declaration has not been made** —
`calibration-complete.json` `complete` still reads {ERCOT, NEISO, PJM} at this pin. Consequences,
stated because they are this desk's to track even though the act is not:
- FF §2.1b leg (a) for NYISO stays **FAIL** while the marker is absent, so no NYISO forecast
  campaign is authorizable, and **Q45's premise stays lapsed** — the capx director recorded at
  r#40 that no re-authorization card is served until a CALIBRATED NYISO keeper returns. **It has
  returned.**
- If and when the owner re-declares, NYISO becomes the **second** ISO whose Stage-B campaign is
  askable, behind NEISO — which changes what card D-5 should ask for when Stage A lands.
- **This desk declares nothing.** Markers, keepers and defaults are the owner's, and the backcast
  records lane is the capx director's queue (charter §0.4: disclose per case, never fix).
  **Routed to the capx director**; surfaced to the owner in this refresh's report. Recorded here
  so that if the marker is *deliberately* being withheld, the reason is asked for rather than
  assumed.

**LOST — two lanes, and the charter's own threshold decides it, not judgement.** SCN-WS4b and
SCN-MX-R were issued at r#2 and re-emitted/narrowed at r#3. At r#4 `git ls-remote origin
'refs/heads/claude/scn-*'` returns **nothing** for either, and no PR exists. That is **two
refreshes after issuance**, which is the charter's LOST threshold. Applying the relaunch protocol
exactly as written: **re-issued verbatim under fresh `-r2` stems, recorded "never launched"
against interest, and NOT re-graded as running.** The r#2/r#3 stems are burned. This is the
second time the desk has had to note the same asymmetry: the five r#1 lanes all launched within
hours, so a lane that shows no branch across two refreshes was almost certainly never dispatched
rather than silently failing.

**RE-GRADED — SCN-WS2a, the one lane still mid-charter.** Its two branch commits merged at #4892:
`73e5351f` (the `05-policy.md` + G-S6 docstring legs, item 6's doc half) and `6e6449ab` (the
NEISO T0 PRECOMMIT, `PRECOMMIT-scn-ws2a-2026-09-05.md`, pushed before the solve as rule 29
requires). **Still owed: the probe result, the postures tests, the FINDING, and the CES matrix
row** — `federal_ces_target_by_year` remains absent from `mechanism-matrix.js` at this pin
(verified: 0 occurrences), so the rule 28 duty-(c) gap SCN-MX-R was chartered to diagnose is now
confirmed across **three** pins. The lane holds merged PRs, so it is **owed, not lost**; the
relaunch protocol does not apply to it and SCN-WS2a-R stays withdrawn.

**Launched by the owner, not yet visible:** SCN-WS1b and SCN-WS2b. No branches at this pin, which
is normal inside one refresh — both were dispatched after r#3. They are graded RUNNING on the
owner's statement, and will be graded by content at r#5.

**Capx deconfliction.** No new capx lane since r#3; D65's branch is still live (`43b3a737`) and
touches no SCN region. The matrix tree has three pending SCN writers (WS-1b, WS-2b, live WS-2a)
plus capx — the last-commit one-line protocol stands unchanged.

**Issued:** SCN-WS4b-r2, SCN-MX-R-r2 (both verbatim relaunches).
**Cards:** none ruled; all open. **One new routing item, not a card:** the NYISO marker
re-declaration, which belongs to the owner and the capx director.

---

### r#3 — 2026-09-06, main HEAD `ea2733395077f15b365273032c8821f86b18b1fb`

*(PR #4891.)* Delta from the r#2 pin
`db8b6015`: **18 commits**, of which nine are SCN and the rest are capx D65 and owner-track
nyiso-196.

**WHY THIS REFRESH EXISTS: the desk's own r#2 PR would not merge.** `git merge-tree
origin/main HEAD` conflicted on `docs/handoffs/scenario-desk-ledger-2026-09.md` — SCN-WS0
edited the ledger's §1 row and §3 rows 6–7 on main while the desk's r#2 commit rewrote the
same sections. **Resolved by rebuild, per the charter's own instruction to recreate the branch
fresh off `origin/main` at every refresh:** this branch is `ea273339` + the r#2 content +
r#3, with **SCN-WS0's §3 edits taken over the desk's** wherever they overlap (the lane's
version is sourced to its own FINDING and is the better record) and the desk's structural
sections preserved. The plan file merged cleanly and its r#2 card-status and §9 blocks are
re-applied on top of main's SCN-WS0 additions. No content from either side was dropped.

**RE-GRADED BY CONTENT — the r#2 verdicts that moved:**

| lane | r#2 verdict | r#3 verdict | what changed |
|---|---|---|---|
| **SCN-WS0** | CHECKPOINT, 4 of 6 | **LANDED — all six items** | `e8c7072d` (5/6, the `scenario` registration kind grouped by campaign with a CO2 delta-vs-reference), `79034547` (6/6, the paired NEISO T0), `47ba0610` (**the G-E4 cap-row rider the desk was about to charter, closed by the lane itself**), `f6abf592` (slim artifacts). `FINDING-scn-ws0-2026-09-05.md` on main. Both arms registered under `scn-ws0-smoke`; 0 FAIL / 0 WARN on all 14 invariants per arm; 2.3 / 2.2 min, 3.31 / 2.94 GB. |
| **SCN-WS1a** | LANDED, **matrix duty NOT discharged** | **LANDED, duty DISCHARGED** | `717de664` mints the `carbon_price_path` and `policy_bundle` base rows plus a cell line in every shard — verified at the pin (2 rows present). `a147362b` scores the CAISO T0 pair against the precommit: every structural gate row passes. The r#2 finding was true at the r#2 pin and the lane repaired it on its own; recorded that way, not as a desk intervention. |
| **SCN-WS2a** | CHECKPOINT, items 1–2 | **CHECKPOINT — and LIVE** | Branch `claude/scn-ws2a-federal-ces-qm512t` carries two commits ahead of main: `73e5351f` (the 05-policy.md + G-S6 docstring legs) and `6e6449ab` (**the NEISO T0 PRECOMMIT, pushed before the solve**, exactly as rule 29 requires). The lane is working its owed items now. |
| **SCN-WS3a / SCN-WS4a** | LANDED | LANDED, unchanged | — |

**THE SUBSTANTIVE RESULT OF THE WEEK — carbon leakage, measured.** SCN-WS0's exercising T0 is
the first case run through the new emissions surface, and it is not a plumbing result. A
$25/tCO2 adder cuts NEISO's modeled in-ISO CO2 by **−2.71 Mt (−16.6 %)** and simultaneously
raises `import_co2_mt_reported` by **+1.85 Mt**, *all of it on one rung* — `NYISO_CT_peak`,
+4.32 TWh, while both firm Hydro-Québec seams barely move. On the scored `emissions_mt` basis
the case reads as a 16.6 % cut; with the disclosure line beside it the modeled net is nearer
**−0.85 Mt (−5.2 %)**. And 0.428 t/MWh is the CARB *unspecified* default for a seam with no
derived EF — at a gas-CT-realistic 0.53, which is what the rung is named for, the net shrinks
again to **≈ −0.42 Mt**. This is G-E3 (plan §2.5) measured on a real case for the first time.
Three consequences the desk carries forward, all now written into the lanes:
1. **Every campaign delta is read with the import line beside it, per ISO — never a generic
   sentence.** Folded into SCN-WS1b's charter as a deliverable, since it is the lane that runs
   all six ISOs.
2. **The NEISO seam EF is now a number with a magnitude attached, not a placeholder.** It
   attaches to card D-4 as a second, sharper instance of the same provenance question.
3. The lane also found and fixed, in the same commit, that **export sinks share the `import`
   fuel type and dispatch negative**, so the import CO2 line was differencing them against
   imports — an unearned offset, now clamped rather than netted. Inert on this T0; fixed
   before it was not.

**WITHDRAWALS — three r#2 charters, none dispatched, none re-issued.** The charter forbids
re-issuing a lane that already landed, and the capx twin-check doctrine forbids building a
twin of a live lane:
- **SCN-WS0-R — WITHDRAWN.** Its entire scope (items 5–6, rider A the G-E4 cap-row export,
  rider A the G-E4 cap-row export) is on main. **Rider B is the one exception and it is
  CHECKED, not assumed: `results/cache.py` has not changed since the r#2 pin**, so the
  cache-epoch entry SCN-WS4a routed — recording that MISO forecast bundles are stale at the
  same key after the DC-share change — is still outstanding. It is one ledger entry, not a
  lane: **re-assigned to SCN-MX-R**, whose scope is widened by exactly this one file, stated
  in its charter and here in §4.
- **SCN-WS2a-R — WITHDRAWN.** SCN-WS2a is live with a pushed PRECOMMIT. Dispatching -R now
  would be the twin the D60-R2 precedent exists to prevent. If SCN-WS2a goes silent for two
  refreshes, the relaunch protocol applies then — not now.
- **SCN-MX-R — NARROWED, not withdrawn.** Its carbon half is done. What survives is real and
  unowned: `federal_ces_target_by_year` and `federal_ces_acp_usd_per_mwh` are still absent
  from the matrix at this pin, **and `check_mechanism_matrix.py` still exits 0** — so the
  duty-(c) enforcement gap is confirmed across two pins, not a one-off. The CES row itself
  belongs to live SCN-WS2a (rule 28(b): the session that tests the mechanism stamps it), so
  MX-R diagnoses the gate and stamps the row **only if** WS-2a lands without it.

**NEWLY UNBLOCKED, ISSUED THIS REFRESH.** WS-0 item 5 was the single blocker on both:
- **SCN-WS1b** — the six-ISO carbon paired probe + the NEISO/ERCOT T1-F ladder. Card D-1 is
  still open, so it runs the **reduced form** its charter names (`--set carbon_price_delta=25`
  rather than `carbon_price_path=mid`), and says so in its PRECOMMIT.
- **SCN-WS2b** — the premium-ladder re-prove at HEAD posture + the national clearing script.
  Independent of SCN-WS2a and SCN-WS2a-R; it consumes committed legs, not the target row.

**SCN-WS4b — RE-EMITTED VERBATIM, not graded lost.** Issued at r#2; no branch and no PR at
r#3. That is **one** refresh, and the charter's LOST threshold is two. Every r#1 lane launched
within hours, so the practical read is that it was never dispatched — the capx relaunch
doctrine for exactly this case is *ask, re-emit verbatim, do not grade lost*, and that is what
this refresh does. If it is absent again at r#4 it is LOST and gets a `-r2` stem.

**Capx deconfliction (D65 landed since r#2).** `4b28c93f` — capx D65 minted its own
mechanism-matrix row and a `U` cell in all six shards, i.e. **the capx track is writing the
matrix tree right now**. The last-commit one-line protocol is load-bearing for every SCN lane
this refresh; SCN-MX-R in particular must rebase immediately before its single stamping
commit. D65's code scope (`capacity_evolution/ccs.py` and the CCS cost anchors) touches no SCN
region. D60-R2 still unreported.

**Issued:** SCN-WS1b, SCN-WS2b, SCN-MX-R (narrowed), SCN-WS4b (re-emitted).
**Cards:** none ruled; all open, unchanged from r#2 except that WS-0's leakage number attaches
to D-4 as a second instance.

---

### r#2 — 2026-09-05, main HEAD `db8b6015a1534873dac50ddda0dce9372d099305`

`db8b6015` = PR #4885. Delta from the r#1 pin `d01ab8b0`: **111 commits**, of which the SCN track
contributed five merged PRs (#4853 desk, #4856/#4860/#4867 WS-1a, #4857/#4859 WS-3a, #4863 WS-4a,
#4869 WS-0, #4870 WS-2a). The rest is owner-track backcast (caiso-252 → CAISO keeper CALIBRATED,
miso-220 → MISO keeper CALIBRATED, nyiso-195/196, NEISO/PJM touchpoints), capx r#41 + D61/D64, and
CI plumbing (Y-13/Y-14).

**Graded BY CONTENT — every wave-1 lane:**

| lane | verdict | what is on main | what is owed |
|---|---|---|---|
| **SCN-WS1a** | **LANDED (complete under its gate)** | Phase-0 trajectory table + machine-readable JSON/py/txt (`docs/handoffs/scn-ws1a/`), items 2+3 (G-C2 `spec.py` corridor adder off the resolver; G-C3 membership-weighted column at `assemble_mc`), item 4 pre-declared, `FINDING-scn-ws1a-2026-09-05.md` incl. the D-1 evidence memo §6 | **item 1 correctly NOT executed** (D-1 open — the gate worked). **Matrix duty NOT discharged** (§below). Its §4.3 routes the cap-row slack/dual export to WS-0 as a G-E4 rider. |
| **SCN-WS3a** | **LANDED** | `voluntary-clean-demand-design-memo-2026-09-05.md`, 8 sections + 5 owner boxes (D-3, new D-3b, new D-3c, the D-6 brief, the D-2 voluntary sub-levels) + Addendum A | nothing. **Launched twice** — `…-s8iukw` and `…-9f1you` both ran the charter; the second merged with an add/add resolution as a cross-check addendum and reports no divergence. Recorded, not a fault of either lane: the desk issued one stem and the harness provisioned two. |
| **SCN-WS4a** | **LANDED** | ERCOT verified already-populated since 2026-07-21 (plan §2.4's "only for PJM" line was **stale**, corrected in-lane); MISO shares from 2026 LTLF slide 21 validated on the deck's own totals (9.6 TWh 2026, 266 TWh 2046, ~58 % Central); NEISO `{}` re-confirmed against the 2026 CELT with the arithmetic written out; `FINDING-scn-ws4a-2026-09-05.md` §4 = the D-4 gap list | nothing in scope. Routes **one cache-epoch entry** (`results/cache.py`, WS-1a's region) it correctly refused to write. |
| **SCN-WS0** | **CHECKPOINT — 4 of 6 items** | (1/6) emissions grain, (2/6) matrix frame + `report_scenario_deltas.py`, (3/6) `collate_scenario_campaign.py`, (4/6) the six-ISO scenario YAML set + `configs/scenario_campaign_matrix.yaml` + the `--set` override, plus `PRECOMMIT-scn-ws0-t0-2026-09-05.md` | **item 5** (the `scenario` kind on `register_forecast_run.py` + the campaign grouping / delta sparkline — verified absent) and **item 6** (the paired NEISO T0 through the new tables, both arms registered under campaign `scn-ws0-smoke`). No `FINDING-scn-ws0`. |
| **SCN-WS2a** | **CHECKPOINT — items 1–2** | one commit: the federal CES target row on the clean-tier family, the `rows.py:1346` coupling relaxation (WS-3b's precondition, delivered), `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh` with `__post_init__` guards and cache-key registration at `None` | **item 3** (the three postures documented + tested), **item 4** (the NEISO 2026 T0 probe — no PRECOMMIT, no registration), **item 6** (matrix), `docs/codebase/05-policy.md` + the `constraints.py` docstring (G-S6), no `FINDING-scn-ws2a`, scorecard row unmoved. |

**THE FINDING OF THIS REFRESH — two undischarged matrix duties, one of them claimed as done.**
Grep at the pin over `docs/codebase-site/data/mechanism-matrix.js` and all six shards:

- `carbon_price_path` — **0 rows, 0 cells** (one incidental prose mention inside an unrelated
  NYISO note). `policy_bundle` — **0 rows, 0 cells**. Yet the ledger §3 row-5 Carbon cell, edited
  by SCN-WS1a itself, reads *"stamped (`carbon_price_path` + `policy_bundle` rows minted at
  WS-1a)"*. `git log --grep=SCN-WS1a -- docs/codebase-site/data/` returns **nothing**: the lane
  never committed to that tree. The claim is corrected in §3 below **against the lane's own
  record**, which is what grading by content is for. Rule 28 duty (b) undischarged.
- `federal_ces_target_by_year` / `federal_ces_acp_usd_per_mwh` — two solve-affecting
  `ScenarioConfig` fields added by SCN-WS2a with **no base row and no cell in any shard**. Rule 28
  duty (c) says that row belongs in the same PR and CI enforces it — **yet
  `scripts/check_mechanism_matrix.py` exits 0 at the pin** (warnings only, all pre-existing anchor
  drift). So the CI half that is supposed to catch a new field without a row **did not fire**.
  That is a gate defect, not an SCN mechanism question, and `scripts/` is not this desk's to edit:
  **routed** to SCN-MX-R to diagnose and report, and to the capx/audit track to fix if the repair
  is in the checker.

**Branch-stem divergence, recorded so §5 reconciles.** Every lane was provisioned by the harness
on its own branch name rather than the stem the desk issued (`scn-ws0-k7m2-8743yi`,
`scn-ws1a-carbon-d1-eupbi5`, `scn-ws2a-federal-ces-qm512t`, `scn-ws3a-voluntary-demand-{s8iukw,
9f1you}`, `scn-ws4a-datacenter-shares-yf7wvi`). WS-4a's FINDING flags it explicitly. No collision
resulted; §5 now records both the issued stem and the realized branch, and future issuance treats
the stem as advisory.

**Graded by content — capx deconfliction (capx r#41, HEAD `5cc1e7ce`):** D61 and D64 **landed**
and each relocated its object (the PJM D57 price ratio is the going-forward bar + census, not the
E&AS operand; the CCS carbon-0 closure rests on an **uncited** `ccs_retrofit_vom_adder` 8.0,
2.7–3.6× every published basis) → **D62 and D65 ISSUED** (D65's branch is live). **D60-R2: nothing
since #4824, status ASKED, not graded lost.** Files: D62/D65 are capacity-evolution and CCS
cost-leg lanes (`capacity_evolution/ccs.py`, `new_entry.py`, `constants.py`'s CCS anchors);
D60-R2 still holds `scripts/forecast_verdict.py` + `frontend/data/forecast/`. **No collision with
any r#2 SCN lane** — but note SCN-WS4b and SCN-MX-R both append to matrix shards, so the
last-commit protocol binds harder than ever (capx parity is RED on two unmapped bundles and the
owner's backcast track promoted two keepers today).

**Wave-2 unblocking, measured against the actual preconditions:**
- **SCN-WS1b** — BLOCKED. Its charter registers twelve arms; the `scenario` registration kind is
  WS-0 item 5 and is not on main.
- **SCN-WS2b** — BLOCKED, same reason (it registers ladder legs).
- **SCN-WS4b** — **UNBLOCKED and ISSUED.** Everything it consumes landed in WS-0 items 2 and 4
  (`report_scenario_deltas.py`, `configs/scenario_campaign_matrix.yaml`) and WS-4a; it registers
  nothing, so item 5 does not gate it. Campaign-YAML ownership **transfers to it** (§4).
- **SCN-WS4c** — BLOCKED on WS-4b.
- **SCN-WS3b** — BLOCKED on card D-3, still open. Its two code preconditions are now MET
  (WS-2a's coupling relaxation, WS-4a's DC module).

**Issued:** SCN-WS0-R, SCN-WS2a-R, SCN-MX-R, SCN-WS4b (§5).
**Cards:** D-1 and D-3 RE-PRESENTED on new evidence; D-4 PRESENTED; D-2, D-6 stand.

---

### r#1 — 2026-09-05, main HEAD `d01ab8b0ea5e3c6e1a68c86f8daad1b4b6d605e9`

`d01ab8b0` = PR #4840 (`claude/miso-219-evening-scarcity-qrliuv`), Sat 2026-09-05 15:25:45
−0700. The plan was surveyed at `4d4dc6ce`; the delta to the pin is owner-track backcast work
(miso-219 and predecessors) plus capx records lanes — **no file in any wave-1 SCN region moved**,
so every plan §2 file:line citation is used as written and each lane re-verifies its own anchors
at its branch point (each prompt says so).

**Read this refresh:** CLAUDE.md; the plan entire (§1 definition of done, §2 per-mechanism
state, §3 workstreams, §3.5 case set, §4 constraints, §5/§5.1 sequencing + scorecard, §6 owner
boxes, §7 prompts, §8 findings); FF plan §2.1b (window cap + four-leg gate), §2.4 (budget
anchors + the `data/clean` prerequisite), §7; capx ledger top block + §1 scoreboard;
`docs/mechanism-testing-matrix.md` §5 and the six shards.

**Graded by content — SCN lanes:** none exist. `git ls-remote origin 'refs/heads/claude/scn-*'`
returns empty; no `FINDING-scn-*` doc on main; plan §5.1 unmoved from v1. This is the first
refresh, so nothing is LOST and no relaunch protocol applies.

**Graded by content — capx deconfliction (from capx r#40, HEAD `4d4dc6ce`):**

| capx lane | status | files it holds | collision with wave 1? |
|---|---|---|---|
| **D60-R2** | RUNNING (PR #4824) | `scripts/forecast_verdict.py` (the `_dof_ledger_row` builder + six new (ISO, field) rows), `frontend/data/forecast/` board + verdict re-scores, the finding | **NO** on `src/`; **SHARD-ADJACENT** — its re-scores can append to matrix shards. Mitigated by the last-commit protocol. |
| **D61** | ISSUED, unlaunched | docs only (PJM E&AS operand Phase 0) | no |
| **D64** | ISSUED r#40, unlaunched | docs only (CCS ΔFOM / capture VOM Phase 0) | no |
| **D58** | RELEASED, dispatch after D60 lands | `frontend/data/forecast/` PJM board t1f row; solves | **NO** on `src/`; WS-0 must not touch `program-status.json`. |
| **D63** | queued-named | MISO/CAISO DOF-row identification | no |
| **T3-NYISO-GOLDEN** | HELD (precondition lapsed) | — | no |

**Conclusion: no HOLD is required for any wave-1 lane.** The capx track's live writers are in
`scripts/forecast_verdict.py` and `frontend/data/forecast/`; wave 1's `src/` regions
(`policy/carbon.py`, `policy/cap_and_trade.py`, `policy/federal_ces.py`, `policy/clean_tiers.py`,
`model/lp/rows.py`, `model/interchange/spec.py`, `results/export.py|outputs.py|emissions.py`,
`src/market_sim/matrix.py`, `data/datacenter.py`, and the four named `runner.py` /
`scenarios.py` / `constants.py` regions) are unheld. The one live shared surface is the six
matrix shards, written by capx re-scores AND by the owner's backcast lanes several times a day
(`3eaf7918` caiso-252, `fe38a699` nyiso-194 both landed on 2026-09-05) — hence the protocol.

**Issued:** SCN-WS0, SCN-WS1a, SCN-WS2a, SCN-WS3a, SCN-WS4a (§5).
**Cards presented:** D-1, D-2, D-3, D-6.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **SCN-WS0** | Emissions grain (by fuel / by zone / import line / unserved) + multi-metric matrix frame + `report_scenario_deltas.py` + `collate_scenario_campaign.py` + the scenario YAML set + `--set` override + `scenario` registration kind; one paired NEISO T0 to exercise it | **LANDED r#3 — all six items** | `claude/scn-ws0-k7m2-8743yi` (merged, PRs #4869/#4877) | **Opus** | Completed itself between refreshes, **including the G-E4 cap-row rider the desk was about to charter**. T0 STOP gate PASS, 0 FAIL/0 WARN × 14 invariants per arm, both arms registered (`scn-ws0-smoke`). `FINDING-scn-ws0-2026-09-05.md`. **Its result is the leakage number** (§0 r#3). Unblocks WS-1b, WS-2b, WS-4b/c, WS-5. **SCN-WS0-R WITHDRAWN undispatched.** |
| **SCN-WS1a** | Federal carbon-price semantics (G-C1, gated on D-1) + the two seam defects (G-C2, G-C3) + the pre-declared `CAP-STATE-TIGHT` case | **LANDED r#3 (complete under its card gate, matrix duty discharged)** | `claude/scn-ws1a-carbon-d1-eupbi5` (merged, PRs #4856/#4860/#4867/#4887) | **Fable** | Items 2–4 + Phase 0 + the D-1 evidence memo; item 1 correctly withheld on the open card. **`717de664` minted the `carbon_price_path` + `policy_bundle` rows and a cell in all six shards** — the r#2 finding was true at its pin and the lane repaired it itself. `a147362b` scored the CAISO T0: every structural gate row passes. Item 1 remains the only thing D-1 blocks. |
| **SCN-WS2a** | The endogenous national CES **target** row (G-S1, G-S3) + the two new fields + the three state/federal postures | **LANDED r#5 — complete** | `claude/scn-ws2a-federal-ces-qm512t` (PRs #4870/#4892 + the probe/FINDING/matrix commits) | **Fable** | NEISO T0 target-row pair registered (escape regime, dual = ACP $50 exactly), `FINDING-scn-ws2a-2026-09-05.md`, `federal_ces_target` row + six cells as its last commit. Level committed by S3 (SCN-LEVELS) with no re-solve. |
| **SCN-WS3a** | Voluntary clean-demand **design memo** (no code, no solve) | **LANDED r#2** | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` (both merged, PRs #4857/#4859) | **Fable** | Memo + 5 owner boxes (D-3, new **D-3b**, new **D-3c**, the D-6 brief, the D-2 voluntary sub-levels) + a cross-check addendum. **Launched twice**; no divergence between the instances. |
| **SCN-WS4a** | DC zone shares for ERCOT + MISO; NEISO `{}` re-check; the D-4 constant-vs-published gap list | **LANDED r#2** | `claude/scn-ws4a-datacenter-shares-yf7wvi` (merged, PR #4863) | **Opus** | ERCOT already populated (plan §2.4 corrected); MISO populated + validated on published totals; NEISO `{}` re-confirmed; D-4 gap list presentable unedited. |
| **SCN-WS1b** | *(the r#3 stem)* | **SUPERSEDED r#6 am.1 by SCN-WS1b-r2** | `claude/scn-ws1b-carbon-sixiso-h6rt` (burned) | **Opus** | Two silent refreshes → relaunched. Its charter carried the desk's `carbon_price_delta` error; the r2 lane's phase 0 caught it. |
| **SCN-WS2b** | Premium-ladder re-prove at HEAD posture + `scripts/ces_national_clearing.py` | **LANDED r#6 — complete; FOUND THE CCS SEAM** | `claude/scn-ws2b-ces-ladder-clearing-p9wf` (merged) | **Opus** | ERCOT + NEISO ladders re-proved at HEAD (six legs registered, G-S5 closed), the clearing script, ERCOT/NEISO cells re-stamped. §8 item 1 is the CCS emission-rate seam (+9.99 vs −6.01 Mt NEISO 2030) that holds Stage A-POLICY under S5 — **UNCHARTERED at capx r#45** (§0 r#9). |
| **SCN-WS0-R** | *(WS-0's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | Its entire scope landed on main between r#2 and r#3, riders included. Recorded so no successor re-issues it. |
| **SCN-WS2a-R** | *(WS-2a's owed half)* | **WITHDRAWN r#3, NEVER DISPATCHED** | — | — | SCN-WS2a is live with a pushed PRECOMMIT; dispatching -R would build the twin the D60-R2 precedent exists to prevent. If WS-2a is silent for two refreshes the relaunch protocol applies then. |
| **SCN-MX-R** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-mxr-matrix-duty-repair-j5tv` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-MX-R-r2** | The rule-28 duty-(c) CI diagnosis; the cache-epoch entry; a conditional CES stamp | **LANDED r#5 — complete** | `claude/scn-mxr2-matrix-duty-repair-t7bq` (merged) | **Fable** | Found the guard fired and FAILED on PR #4870 (merged five seconds after creation with seven red checks — not a required status) and that validate-only mode never checks registration; the desk's three exit-0 readings withdrawn. `FINDING-scn-mxr-2026-09-06.md`. The mechanism gap is still open (matrix guard RED again at capx r#45 on nyiso-198's field). |
| **SCN-WS4b** | *(the r#2/r#3 stem)* | **LOST r#4 — NEVER LAUNCHED** | `claude/scn-ws4b-loadhi-adequacy-b2np` (burned) | — | No branch, no PR, two refreshes after issuance. Relaunch protocol applied; not re-graded as running. |
| **SCN-WS4b-r2** | *(the r#4 relaunch)* | **SUPERSEDED r#5, NEVER DISPATCHED** | `claude/scn-ws4b2-loadhi-adequacy-x3mc` (burned) | — | The original lane landed the charter. The relaunch was never needed; recorded so no successor dispatches it. |
| **SCN-WS4c** | Six T0 LOAD-HI probes + NEISO/ERCOT T1-F | **LANDED r#7 — complete** | `claude/scn-ws4c-loadhi-probes-q8vd` (merged, PRs #4941…#4997) | **Opus** | 19 arms (15 T0 + 4 T1-F), campaign `scn-ws4-probe`; WS-4b's readings score 20 HIT / 3 SPLIT / 3 MISS; the fossil-average heuristic carries a signed error (0.65–0.77× with coal, 1.05–1.17× without); NEISO's committed `ff-t1f-d50` measured stale by 2.821 Mt (G-DRIFT vindicated). `datacenter_load_block` stamped `K` in all six shards. |
| **SCN-WS3b** | *(the r#5 am.1 stem)* | **SUPERSEDED r#6 am.1 by SCN-WS3b-r2** | `claude/scn-ws3b-voluntary-demand-n5wq` (burned) | **Fable** | Released by S1; never dispatched. |
| **SCN-WS3c** | Voluntary-demand probe | **WITHDRAWN r#11 am.1 — scope absorbed by the policy lanes' VOL-* legs** | — | — | The memo §6 gate is carried per ISO by SCN-WS5A-POLICY-<ISO>'s voluntary addendum (G7–G10), with the phase-0 regime kill. A separate ERCOT probe would have run on a slack row over a collapsed REF. |
| **SCN-WS5A-LOAD** | **Stage A-LOAD** — `REF`/`LOAD-HI`/`LOAD-HI-ORGANIC`, T1-F 2026–2030, six ISOs | **LANDED r#13 — COMPLETE at the frozen pin `1cc45bb2` (16/16, six FINDINGs, synthesis, D-5 cost table); 13 legs carry pre-D77 CCS rates → SCN-WS5A-RESOLVE** | `claude/scn-ws5a-load-campaign-f5znk9` (PRs #5010 … #5130, all merged) | **Opus** | Falsified S5's premise (state programs AND §45Q arm the retrofit screen); ERCOT REF in deep shortage; CAISO's ORGANIC arm worth solving; the collate defect; the cache blocker for the re-solve. Cost: 313.7 min LP / 80 solve-years. `FINDING-scn-ws5a-load-synthesis-2026-09-06.md`. |
| **SCN-WS1c** | Ruling S2 executed — the federal carbon price as a FLOOR under the state program (plan §7 WS-1a item 1) | **LANDED r#6 — complete** | `claude/scn-ws1c-carbon-floor-v2rk` realized (PRs #4956/#4961/#4967) | **Fable** | 450/450 cells match the committed `floor` prediction; 0 of 90 run_configs / 0 keys moved; `tight` an exact no-op on the three program ISOs (the ruled outcome). capx D72 later measured its blast radius EMPTY. `FINDING-scn-ws1c-2026-09-06.md`. |
| **SCN-LEVELS** | Ruling S3 executed — the §3.5 levels committed, `CES-T80` made live | **LANDED r#6 — complete** | `claude/scn-levels-d2-commit-c3jx` realized (PR #4950) | **Fable** | Zero numbers moved, 91 keys byte-identical, no solve. Named the three levels S3 did not reach (§2 D-2 row). `FINDING-scn-levels-2026-09-06.md`. |
| **SCN-LOAD** | Ruling S4 executed — six published ISO load forecasts curated as the `load-forecast` datatype | **LANDED r#6 — complete** | `claude/scn-load-forecast-intake-w9tf` realized (PRs #4952/#4970/#4976) | **Opus** | All six sources on disk; the constants re-derived (`d14a7ed0`, +473/−263 in `constants.py`), which moved the target WS-4b/WS-4c pre-declared against (§0 r#8). Six items routed. `FINDING-scn-load-2026-09-06.md`. |
| **SCN-WS1b-r2** | Six-ISO carbon paired probe (leg 1, 2027); leg 2 (the 2026–2030 ladder) | **LANDED r#11 — COMPLETE, 12/12 arms** (leg 2 superseded by the CARB-* policy legs) | `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz` (PRs #4992 … #5101 merged) | **Opus** | Three ISOs live (PJM 8/8, MISO 8/8, ERCOT 7 + 1 band miss; PJM 17.4 TWh coal displaced by $3.75/t), three exactly inert (S2 measured), price campaign-grade on PJM/MISO only, price-setting vs load-following rate 1.13–1.33×, import CO2 41.3 % / 25.3 % of NYISO/NEISO in-ISO. 24 solve-years, 89.4 min. Six cells stamped. Its six registered pairs' invariant FAILs are declared by SCN-FIX1. |
| **SCN-WS3b-r2** | Voluntary-demand build, released by S1 | **SUPERSEDED r#9 am.1 by SCN-WS3b-r3 (S6)** — no evidence of dispatch across r#7–r#9 | `claude/scn-ws3b2-voluntary-demand-k8zp` (never realized) | **Fable** | No PR ever, no branch, not visible in the desk-scoped session list (which also cannot see the lanes that DID run). Blocks nothing today (feeds the S5-held half). SCN-WS3b-r3 issued at r#9 am.1. |
| **SCN-WS3b** *(realized as -r3's charter)* | Voluntary-demand build | **LANDED r#10 — COMPLETE** | `claude/scn-ws3b-voluntary-demand-h59n9b` (PRs #5085/#5090/#5095; the two auto-merged with main-wide reds, graded not the lane's) | **Fable** | Three fields (`off` default), resolver, the row on the clean-tier family, DC-energy helper, `VOLUNTARY_*` anchors, the four S5-held YAML cases, 783 test lines, constant-family table, base row + six `U` cells. `FINDING-scn-ws3b-2026-09-06.md`; ERCOT 2026 T0 instrument SLACK; seven items routed. |
| **SCN-FIX1** | Declare the SCN runs' invariant FAILs; repair `collate_scenario_campaign.py`'s system-scope delta | **LANDED r#12 — items 1–2 COMPLETE (r#10 charter); items 3–4 → SCN-FIX2** | `claude/scn-fix1-records-collate-n3rt-heca49` (PRs #5127/#5129/#5136) | **Opus** | 22 runs / 34 pairs declared, 16 baseline lines pruned, audit 30 → 8 (all capx). Collate delta on the common ISO set (sign flip found on the filling tree). Ruff: two other files red on main, routed. `FINDING-scn-fix1-2026-09-06.md`. |
| **SCN-FIX2** | The carbon form → `carbon_price_path` (S3); the S9/S10 relabel | **LANDED r#13 — COMPLETE** | `claude/scn-fix2-carbon-form-relabel-lurf5k` (#5153) | **Opus** | Resolved-carbon table measured; words-only relabel; 30 keys of the re-formed cases move, none with a bundle. Found CARB-HI LIVE on NYISO/NEISO at full horizon. `FINDING-scn-fix2-2026-09-06.md`. |
| **SCN-CAP** | `mass_cap_tons_by_year` + `CAP-STATE-TIGHT` (S12) + matrix row | **LANDED r#13 — COMPLETE** | `claude/scn-cap-schedule-field-re00nd` (#5154) | **Fable** | Field inert by default, read first; 0 of 143 keys move; binds NYISO + CAISO all years, slack NEISO; PJM falls through to the regional RGGI budget (charter premise false, routed → policy charter v4). `FINDING-scn-cap-2026-09-06.md`. |
| **SCN-WS5A-POLICY-\<ISO\>** ×6 | **Stage A-POLICY** — CARB-LO/MID/HI, CES-P10/P20/P30, CES-T80, CARB-MID+LOAD-HI at T1-F 2026–2030 per ISO, **+ VOL-MID / VOL-HI / CES-P20+VOL-HI / ALL-CLEAN (S9/S10/S11, folded into the template at r#11 am.2)**, **+ CAP-STATE-TIGHT on the three program ISOs by the r#12 am.1 CAP addendum (S12; gated on P5 = SCN-CAP on main)** | **ERCOT RUNNING (PRECOMMIT on main, phase 0 done, 11 legs survive, first solve RELEASED by S14 — RE-ISSUED r#17 (session closed; stem burned)); NEISO / NYISO / PJM ISSUED r#17 under charter v6; CAISO / MISO wait for their re-solved REF (P1)** | ERCOT: `claude/scn-ws5a-policy-21mq1y` (PR #5252, merged); others `claude/scn-ws5a-policy-<iso>-<4ch>` | **Opus** | **Charter v6 in §5 (v5 SUPERSEDED — do not paste it).** ERCOT's phase 0 killed `VOL-MID` (slack all five years) and `CAP-STATE-TIGHT` (no program on ERCOT at all) on identities, reproduced the carbon table to the cent, and routed the two v5 defects v6 fixes. Program ISOs run five legs (CARB-\* killed at phase 0 under the S2 floor), the others eight. Supersedes WS-1b-r2's leg 2 and WS-2b's pre-fix ladder. |
| **SCN-WS5A-RESOLVE** | Ruling S8 as a standalone lane: the 13 contaminated legs re-solved post-D77/D65-B at THE PIN `bdfb3095`; the S5 identity on the campaign REFs; same-id re-registration | **LANDED r#18 — COMPLETE, 13/13, every gate PASS on every leg** | `claude/scn-ws5a-resolve-post-d77-m8m5ft` (PRs #5214, #5221, #5238); `-caiso-0rkx2k` (#5241, PRECOMMIT only); `-miso-0s8zln` (#5244, PRECOMMIT only) | **Opus** | Cache blocker defeated by construction (D65-B re-keys everything); **re-solved into `results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/` per the charter recipe — the r#16 "in place / accepted deviation" note is WITHDRAWN, see §0 r#17.** NYISO 2030 CO2 −46 %; DC-shape axis survives; P-B hit. **PJM: all five gates PASS and the D67-ARM/D81 confound measured INERT** (rate-capped backstop at −16 % margin); 2030 CO2 −7.42 Mt split between D77 and D65-B. Owes PJM 1, CAISO 3, MISO 3, the FINDING, the synthesis addendum + amended cost table. **AMENDED 2026-09-07 by SCN-WS5A-RESOLVE-ERCOT: the lane is 16/16, not 13/13 — ERCOT NOW SITS AT THE PIN TOO.** S8 excluded ERCOT's REF / LOAD-HI / LOAD-HI-ORGANIC as "CCS-clean at `1cc45bb2`" and the parent PRECOMMIT §0.1 item 2 wrote that D77/D65-B "are inert on a fleet that converts nothing". **Both are falsified.** The full resolved-config diff pre-fix → pin is exactly two fields, `ccs_retrofit_vom_adder` 8.0 → 2.95 and `ccs_retrofit_fixed_cost_co2_scaling` False → True, and both are INPUTS TO THE RETROFIT SCREEN — an input is not inert because the screen's pre-change output was zero. Solved: ERCOT REF converts **0 → 5,763.8 MW** by 2030 and 2030 CO2 falls **328.874 → 312.866 Mt (−4.87 %)**; LOAD-HI −16.818, ORGANIC −16.818. G1/G2/G3/G4 PASS on all three; **19.8 min of LP for 15 solve-years (1.32 min/solve-year, confirming the r#18 am.1 shard arithmetic on a fresh container — but `regenerate_clean` cost ~39 min, TWICE the LP)**. **G3 SPLITS AND HALF OF IT CORRECTS THE POLICY FINDING:** at 2028 the pin REF converts NOTHING while every carbon/CES arm converts 2,932–2,996 MW, so **the 2028 conversion is a POLICY RESPONSE**, not the pin's (the A/B at equal load: LOAD-HI 0/2,932/3,000 vs CARB-MID+LOAD-HI 2,996/3,000/3,000; and VOL-HI, which cannot credit CCS, reproduces REF's 0/2,764/3,000 to the tenth of a MW); at 2029–30 REF converts on its own and the contamination reading stands. **The load delta barely moves** (+13.4072 → +12.5978 Mt at 2030, −6.0 %, vs NEISO's −82 % and NYISO's −42 %) because both ERCOT arms convert on the same schedule, and **the DC-shape gap moves by 0.0001 Mt** — the synthesis §1.1 headline is untouched on ERCOT. **TWO ROUTED ITEMS, both cheap and both real:** (1) the eleven committed ERCOT policy legs must be re-differenced against this REF (the policy FINDING's owed ADDENDUM B) — until then no ERCOT policy-vs-REF delta at 2028–30 is quotable from either document; (2) **`unit_id` IS NOT UNIQUE in the ERCOT fleet** (a legacy heat-rate-bin label colliding with new-build capacity), which made this lane's own added G5 identity gate FAIL by grading an unconverted twin — corrected resolution gives max rel dev 0.000e+00 — and **every sibling RESOLVE lane scored its G1 identity keyed on `unit_id`**, where the same defect would produce a false PASS rather than a false FAIL. Evidence: `docs/handoffs/{PRECOMMIT,FINDING}-scn-ws5a-resolve-ercot-2026-09-07.md`. |
| **SCN-WS5A-POLICY-SYNTH** | The Stage-A policy-half synthesis + the six-ISO rollup on the common ISO set | **HELD — issues when the six land** | — | Opus | Needs SCN-FIX1's collate repair on main. |
| **Stage B** | Full-horizon legs | **NOT ISSUABLE** | — | — | Needs card D-5 **and** an OPEN §2.1b gate for the named ISO at issuance. At the r#1 pin only NEISO is open. Re-check at issuance, never at planning. |

---

## 2. Owner cards

| card | question | status | recorded ruling |
|---|---|---|---|
| **D-1** | Federal carbon price on a program ISO: **replace** (today), **floor** (`max`), or **additive**? | **RULED r#5 am.1 — S2** | **S2 (2026-09-06): FLOOR.** `effective = max(RFF path(year), program trajectory(year))` on a program ISO, the path alone elsewhere. `carbon_price` (scalar) keeps its Q26 replace semantics untouched. Ruled with the measured consequence on the record: the RFF mid path never exceeds a program trajectory in any year, so the floor makes `tight` an exact **no-op** on CAISO/NYISO/NEISO rather than an increase. → **SCN-WS1c issued.** |
| **D-1(b)** | *(new, raised by the evidence)* Once the floor is in, `policy_bundle="tight"` is an exact **no-op** on CAISO/NYISO/NEISO — the RFF mid path never exceeds a program trajectory in any year. Should `tight` mean something else on a program ISO? | **PRESENTED r#2** | — |
| **D-1(c)** | *(new)* PJM's partial RGGI footprint under a federal floor — floor against what, when only part of the fleet faces the state program? | **PRESENTED r#2** | — |
| **D-2** | Campaign levels — carbon paths, CES premium ladder, **CES target schedule + ACP**, voluntary levels, load-high pairing. | **RULED r#5 am.1 — S3** | **S3 (2026-09-06): the plan's §3.5 table is the COMMITTED default.** Carbon RFF low/mid/high; CES premium {10, 20, 30}; **CES target {2026: current, 2035: 0.80, 2050: 1.00} with ACP $50**; LOAD-HI = growth high + DC high. No re-solve is owed: SCN-WS2a built and probed against exactly this and labelled it illustrative, so the change is to the label, not the number. The WS-3a memo box 5 voluntary sub-levels ride the same ruling on the plan's defaults. → **SCN-LEVELS issued.** **EXECUTED 2026-09-06 by SCN-LEVELS** (`FINDING-scn-levels-2026-09-06.md`): the committed levels are written into `configs/scenario_campaign_matrix.yaml`, the two CES field docstrings, plan §3.5 + §5.1 and this ledger; **`CES-T80` went LIVE** (its fields landed with WS-2a, its level with S3) at `{2026: 0.55, 2035: 0.80, 2050: 1.00}` / ACP 50.0; **zero numbers moved, zero defaults moved, 91 pre-existing cache keys measured byte-identical, no solve.** **THREE LEVELS S3 DID NOT REACH and that the lane refused to infer — re-present them:** (i) `CAP-STATE-TIGHT`'s declining budget (§3.5 names no number; the slope is still the OWNER level of `FINDING-scn-ws1a-2026-09-05.md` §4.2); (ii) the voluntary `f_commit` **mid** and the WTP-ceiling **level**, which the memo's box 5 itself leaves owner-set even as S3 commits "the box-5 defaults"; (iii) the carbon ladder's **form** — S3 commits the RFF *path* ladder, which cannot go live until SCN-WS1c lands S2's floor, so the campaign still runs the additive `carbon_price_delta` interim whose {15, 25, 50} knots are a desk stand-in and NOT ruled levels. |
| **D-3** | Is a voluntary clean-demand **scenario axis** admissible given ffr-5b's inadmissibility ruling on corporate PPA demand as a *driver*? | **RULED r#5 am.1 — S1** | **S1 (2026-09-06): YES — a declared, forecast-only, publicly-anchored, default-off scenario axis.** The ffr-5b ruling is held to be about a *fitted driver*, a different admissibility class; its null is preserved in REF and every scored lane. → **SCN-WS3b issued**, WS-3c follows it. |
| **D-3b** | *(memo box 2)* Does in-LP hourly (24/7) matching stay deferred to the isolated `scope2-lce-portfolio` tool? | **RULED r#5 am.1 — with S1** | **DEFERRED.** The owner took S1's recommended form rather than the hourly-in-LP variant, so 24/7 stays in the isolated tool, fed the campaign's LMPs. WS-3b builds the annual volumetric row only. |
| **D-3c** | *(memo box 3, NEW)* The eligible set — renewable-only by default (incl. offshore wind), carbon-free (nuclear/CCS) only as a labelled override; credit all eligible units or new builds only? | **PRESENTED r#2 — STILL OPEN after S1/S3** | — · S1 ruled the AXIS admissible and S3 ruled its LEVELS; neither reaches the eligible SET. SCN-WS3b therefore builds against the memo's **recommendation**, which stays labelled a recommendation and is the one place SCN-LEVELS deliberately left the illustrative-class wording standing (`FINDING-scn-levels-2026-09-06.md` §4). |
| **D-4** | Fund the `load-forecast` curated intake? | **RULED r#5 am.1 — S4** | **S4 (2026-09-06): FUND THE FULL DATATYPE.** All six published sources curated through the data-intake skill. **This OVERRIDES the desk's and SCN-WS4a's recommendation to defer**, and is the largest of the three options offered — recorded as the owner's call on a question the desk had answered the other way. → **SCN-LOAD issued**, with the known 403 host wall on MISO's driver-level data flagged at the gate rather than discovered mid-lane. **LANDED 2026-09-06 — the ruling is vindicated on evidence neither recommendation had.** All six sources obtainable and on disk; G-D4-1/-2/-4 CLOSED, G-D4-3 partial (ERCOT verified, PJM's Table B-9b read but the shares deliberately not rewritten — routed), G-D4-5 a disclosed null; the MISO 403 wall re-confirmed BLOCKED. The return was NOT the provenance upgrade the card was argued on: the intake found an era-window error in every rate and a table silently mixing peak- and energy-derived bases, worth up to **+31 % of the 2030 demand scalar**, while NYISO — the one row already properly derived — reproduced to four decimals. `FINDING-scn-load-2026-09-06.md`; six items routed to this desk. |
| **D-7** | Does Stage A run before the CCS emission-rate seam is repaired? | **RULED r#6 am.1 — S5** | **S5 (2026-09-06): HOLD THE POLICY HALF, RUN THE LOAD HALF NOW.** Stage A splits at the `gas_cc_ccs` line: **A-LOAD** (`REF`/`LOAD-HI`/`LOAD-HI-ORGANIC` six-ISO T1-F + the sub-2028 carbon T0 probes) is released and issues when SCN-WS4c lands, needing no further card; **A-POLICY** (every CES case, every 2028+ carbon case, `ALL-CLEAN`, `VOL-*`) holds until the capx CCS seam is repaired and a paired check confirms `emission_rate` follows the retrofit. Routed to the capx director as a priority signal. |
| **D-5** | Per-campaign §2.1b grant for the NEISO scenario campaign (Stage B). | **HELD** — presented only with Stage A's measured cost table on the dashboard. **Re-checked r#9: still not presentable** — SCN-WS5A-LOAD is frozen at its pin with 0 of 16 legs solved at its last commit, so no cost table exists. **r#10: 8 of 16 legs; synthesis pending PJM/MISO/CAISO and the D-10 re-solve.** **PRESENTED r#13** — the cost table exists (synthesis §8: 313.7 min LP / 16 legs / 80 solve-years; NEISO 1.09 min per solve-year, so a 13-case NEISO full-horizon campaign ≈ 13 × 25 × ~1.1–1.5 min ≈ 6–8 h); recommendation **HOLD** until SCN-WS5A-RESOLVE lands (a Stage B on the pre-D77 NEISO REF inherits a 41.9 %-contaminated 2030 level) and the policy half has run; §2.1b legs (a) NEISO in `complete` ✓, (b)/(c) to be re-read on the post-fix board at grant time, (d) is this card. | **RULED r#13 am.1 — S13: HOLD** | **S13 (2026-09-06): "Hold until RESOLVE and the policy half land."** Re-presented when both are on main. |
| **D-6** | Attribute netting between a federal CES row and a voluntary-demand row. Recommendation: **counts toward**, report both. | **PRESENTED r#1 — STILL OPEN after S3** | — · S3 did not reach it. `CES-P20+VOL-HI` therefore reports BOTH nettings and asserts neither; the memo §4.3 is the brief and Addendum A.2 the dissent to weigh beside it. |
| **D-8** | *(desk card, NEW r#9)* **SCN-WS3b — relaunch under a third stem now, hold it until the CCS seam repair lands, or drop the voluntary axis from Stage A?** Two stems (r#5 am.1, r#6 am.1) produced no branch, no PR and no commit across three refreshes. The build is zero-LP and touches nothing the CCS seam touches, so it can be built now and wait; but every case it makes expressible (`VOL-*`, `CES-P20+VOL-HI`, `ALL-CLEAN`) is S5-held, so it buys nothing until the seam is repaired. Recommendation: **relaunch now** — the seam has no owner (D-9), so waiting on it is open-ended, and a ready-in-waiting build costs one Fable session. | **RULED r#9 am.1 — S6** | **S6 (2026-09-06): "Relaunch now, third stem."** → **SCN-WS3b-r3 ISSUED** on `claude/scn-ws3b3-voluntary-demand-q7mv`; the VOL-* cases it builds stay S5-held. |
| **D-9** | *(desk card, NEW r#9)* **Direct the capx director to charter the CCS emission-rate seam repair as a named lane?** At capx r#45 the seam is named but no D-lane carries it (D65-B is the VOM/fixed-cost arming; D74/D75 are other objects; no commit on the emission-rate path since 2026-09-06). It is the sole release condition for Stage A-POLICY (ruling S5) and for SCN-WS1b-r2's leg 2. This desk cannot charter it (§0.4 of the charter — the CCS seam is theirs) and does not propose a fix; it can only disclose that the routing has landed nowhere. Recommendation: **yes, name it as the capx director's next lane** — a one-file-plus-downstream diagnosis with the paired check already specified by S5 ("a paired check confirms `emission_rate` follows the retrofit"). | **RULED r#9 am.1 — S7** | **S7 (2026-09-06): "Yes, name it the capx director's next lane."** Routed to the capx ledger as an owner direction for the director's next sitting; the paired check of S5 is the lane's gate. The desk charters nothing on it. **EXECUTED r#10: capx D77 chartered (r#46 am.1) and landed the repair (`ae8dd2a0`, #5089) within the hour; screen + FINDING owed.** |
| **D-2(b)** | *(re-presentation, NEW r#11; SCN-LEVELS §4 and SCN-WS3b §4 both flagged it)* **The two voluntary levels S3 did not reach:** `f_commit` mid (the committed fraction of DC block energy under voluntary clean commitments; WS-3b ships a **0.5 placeholder** labelled illustrative) and the WTP-ceiling level (the price at which a voluntary buyer forgoes the attribute; WS-3b ships **$4.5/MWh** labelled illustrative). Until ruled, VOL-MID / VOL-HI / CES-P20+VOL-HI / ALL-CLEAN are held out of Stage A-POLICY. Recommendation: **take the memo's box-5 placeholders as the committed levels** (0.5; $4.5/MWh, the NREL unbundled-REC price band the memo cites) so the four legs can be added by addendum. | **RULED r#11 am.1 — S9** | **S9 (2026-09-06): "Take the placeholders as committed."** 0.5 / $4.5/MWh; relabel by SCN-FIX1 item 4. |
| **D-3c** | *(memo box 3, re-presented r#11)* The voluntary **eligible set**: WS-3b built the memo's recommendation — wind, solar, offshore wind, geothermal by default; nuclear/CCS only via the labelled `voluntary_eligible_fuels` override; all eligible units credited, no additionality mask. Recommendation: **ratify the default as built**. | **RULED r#11 am.1 — S10** | **S10 (2026-09-06): "Ratify the default as built."** |
| **D-6** | *(re-presented r#11)* Attribute **netting** between a federal CES row and the voluntary row: WS-3b built no netting logic and named the report-layer hook. Recommendation: **counts toward, report both** (one MWh, one claim). | **RULED r#11 am.1 — S11** | **S11 (2026-09-06): "Counts toward; report both."** CES-P20+VOL-HI and ALL-CLEAN report both nettings (gate G10). |
| **D-2(c)** | *(re-presentation, NEW r#12)* **`CAP-STATE-TIGHT`'s budget slope — the last §3.5 case out of Stage A.** WS-1a §4.2 pre-declared a linear decline to **20 % of the 2025 published per-state budget by 2050** (NYISO 23.16 → 4.6 Mt; NEISO 20.67 → 4.1; CAISO 30.5 → 6.1, REF-anchored because CARB publishes no power-sector budget) and labelled the slope an owner level; the case also needs the schedule field `mass_cap_tons_by_year`, absent at HEAD (WS-1a §4.1(a)) — one small Fable build (a new `ScenarioConfig` field + matrix row + six cells, backcast-inert). Recommendation: **commit the 80 %-decline slope and charter the field**, so the price-vs-quantity comparison the case exists for runs in this campaign; the alternative drops the case with a ledger note. | **RULED r#12 am.1 — S12** | **S12 (2026-09-06): "Commit the 80 % slope and build the field."** → SCN-CAP issued; the CAP addendum to the three program-ISO policy lanes. |
| **D-13** | *(owner instruction, NOT a desk card — recorded here because it changes a live charter)* **The per-ISO policy lane is too much compute for one session, and LP parallelism is effectively unlimited.** | **RULED r#18 am.1 — S16** | **S16 (2026-09-07), owner verbatim:** *"I don't want to run all of these in one session per iso though that's way too much compute and we have effectively unlimited ability to run lps in parallel so the per iso session should launch shards itself"* + *"Update those prompts accordingly to launch individual sessions for runs to target <1 hr of lp solve per session."* The per-ISO lane becomes a **COORDINATOR**: it keeps phase 0, the PRECOMMIT, keys, kills, gate scoring, the FINDING, the plan/ledger rows and the matrix cells, and **launches one shard session per leg-group**, each sized to **< 60 min of LP**. Shard size is DERIVED from the synthesis §8 measured min/solve-year at 5 solve-years per leg: NEISO 10 · ERCOT 9 · NYISO 2 · CAISO 2 · MISO 2 · **PJM 1**. Rule 12's ~2-concurrent cap is a **per-container memory** constraint and does not compose across shards; its **within-invocation** half (one solve at a time, years sequential) is untouched and still binds inside every shard. Codifies what ERCOT's SUBLANE protocol, PJM's S2/S3/S4/S6 split and NYISO's four containers had already converged on. Charter **v7** + the shard template: §5.5. |
| **D-12** | *(desk card, NEW r#18)* **The CES premium ladder cannot discriminate on entry in five of six ISOs at the committed levels.** The entry screen folds `attr = max(EAC, rps_credit_for_zone, clean_credit)` with **no fuel gate on the RPS leg** (`new_entry.py` ~:1132–1143), so where a state RPS sits at its escape a federal CES premium below it adds nothing. `STATE_RPS_ACP` = MISO 30 · NYISO 40 · PJM 45 · CAISO 50 · NEISO 50 · **ERCOT absent**; the committed ladder {10, 20, 30} and the voluntary ceilings {$4.50, $7.00} sit under every one, and `CES-T80`'s ACP $50 ties exactly on CAISO and NEISO. Measured independently by two lanes (NEISO: `rps_dual` 50.0 in 5/5 years and a byte-identical VOL-HI/VOL-MID pair; PJM phase 0: *"PJM's $45 RPS ceiling dominates two chartered axes"*). Not a defect — rule 19's `max()` doctrine, and economically right. The retirement leg **is** fuel-gated (`retirements.py` ~:3509–3516), so the CES legs still differ and still solve. Recommendation: **add one bracketing leg above the mask** — a single common `CES-P60`, above the footprint's highest published ACP, set from published ACPs and not per-ISO. | **RULED r#18 — S15** | **S15 (2026-09-07): "Add one bracketing leg above the mask (Recommended)."** Each lane first measures its own REF RPS dual per year at **zero LP**; where it sits at or above the CES dual, it adds a single **`CES-P60`** leg. $60/MWh is ONE common level for every ISO — above the footprint's highest published ACP ($50), identified from published ACPs and **never** from a residual, and deliberately not per-ISO so it cannot become the per-ISO fitting rule 25 `[R-ISO-SCOPE]` forbids. ~5 legs / ~100 min LP. Its purpose is to convert a null into a measured threshold **and to falsify the alternative reading that the CES row is simply not wired**; a leg that clears the mask and still moves nothing is a reportable finding, not a gate failure. The committed §3.5 levels (ruling S3) are **untouched** — this adds a bracketing leg beside the ladder, it does not re-level it. |
| **D-11** | *(desk card, NEW r#17)* **The solve slot — SCN-WS5A-POLICY-ERCOT is fully prepared and blocked only by the desk's own concurrency clause.** Its phase 0 is done, eleven legs survive, its PRECOMMIT is on main, and it is HELD by charter P4, which allows ONE repo-wide solve while RESOLVE is on PJM/CAISO/MISO. **CLAUDE.md rule 12's own cap is ~2 concurrent per-plant multi-zone runs** — P4 is *stricter than the rule*, written that way because this desk cannot observe how many solves the capx track has live (its §4 queue carries D78-R3, D75-R-ARM and D76-P3, all PJM, plus the D65-B-R batch). RESOLVE still owes 7 heavy legs (PJM 1, CAISO 3, MISO 3; the ERCOT lane measured CAISO and MISO at 4.87 and 9.65 GB peak on a 15 GB box, ERCOT at 4.2 GB). Recommendation: **relax P4 to rule 12's ~2 cap** — ERCOT never shares a fleet with PJM/CAISO/MISO, so the two solves are independent, and the alternative parks eleven prepared legs behind seven heavy ones. | **RULED r#17 — S14** | **S14 (2026-09-06): "Relax P4 to rule 12's ~2 cap (Recommended)."** ERCOT's first solve is RELEASED and may run concurrently with RESOLVE's remaining legs, under two conditions carried into charter v6: **at most 2 SCN-track solves at once**, and **not while the capx track is mid-solve** — the owner sequences that half, since only the owner sees both tracks. The stricter one-solve reading of P4 is retired; rule 12's own text governs. No other precondition moves. |
| **D-10** | *(desk card, NEW r#10)* **The campaign's pin after D77 — re-pin once and re-solve the contaminated legs, finish at the frozen pin and re-solve afterwards, or finish and disclose?** SCN-WS5A-LOAD's NEISO (2) and NYISO (3) legs were solved pre-D77 and are exactly the bundles D77 §3 declares silently stale at their own cache key; CAISO is unsolved; ERCOT/PJM/MISO carry no state carbon program, so their retrofit ledgers are empty and D77 is inert by construction. Recommendation: **re-pin once, post-D77, now** — re-solve NEISO + NYISO (5 legs, ≈35 min), solve CAISO at the new pin, keep ERCOT/PJM/MISO under a hunk-by-hunk G-DRIFT; the re-solved NEISO REF doubles as S5's model-grain paired check. | **RULED r#10 am.1 — S8** | **S8 (2026-09-06): "Re-pin once post-D77 now."** → the SCN-WS5A-LOAD amendment ISSUED as written (§5); A-POLICY releases on the re-solved NEISO REF's identity check, no card. |

Rulings are recorded verbatim and numbered **S1, S2, …** here and appended to the plan's §6 row
as `RULED <date>: …` in the same refresh commit.

---

## 3. Readiness scorecard (the plan's §5.1, kept current here)

State at r#1 = plan v1, unmoved. Each landing lane updates BOTH this table and the plan's §5.1.

| Criterion (plan §1) | Carbon | CES premium | CES target | Voluntary | Load-HI | Emissions |
|---|---|---|---|---|---|---|
| 1 expressible in committed config | yes — **G-C1 CLOSED** (SCN-WS1c 2026-09-06, executing owner ruling **S2**/card D-1): `resolved = max(RFF path, program trajectory)` on a program ISO, the path alone elsewhere. The `tight` cut of $16–$102/t on CAISO/NYISO/NEISO is gone — corrected +$15.98 to +$102.29/t in all 25 yrs, and **no cell anywhere falls**. Gates: 450/450 cells match WS-1a's committed `floor` prediction; footprint exactly 3×25 cells; 0 of 90 committed run_configs on the changed branch and 0 keys moved. **`tight` is now an exact NO-OP on the three program ISOs** — the ruled outcome; **D-1(b)** (what `tight` should mean there) and **D-1(c)** (PJM's partial footprint) stay OPEN. `FINDING-scn-ws1c-2026-09-06.md` | yes | **yes** (SCN-WS2a: `federal_ces_target_by_year` + `federal_ces_acp_usd_per_mwh`; illustrative level, D-2 open) | **yes** (SCN-WS3b 2026-09-06, executing owner ruling **S1**/card D-3): `voluntary_clean_demand_path` off/low/mid/high + `voluntary_wtp_ceiling_usd_per_mwh` + `voluntary_eligible_fuels`, all forecast-only (the whole block coerced to its defaults in backcast/hindcast) and cache-optional at `off`; levels in `constants.VOLUNTARY_*` with citations (the NREL 2021/2022/2023 national voluntary share series 0.06/0.06/0.08; the cited $2–7/MWh public REC range; `f_commit` low 0 / high 1.0). `VOL-MID` / `VOL-HI` / `CES-P20+VOL-HI` / `ALL-CLEAN` are LIVE in `configs/scenario_campaign_matrix.yaml` and **HELD under S5** (Stage A-POLICY). Two cells stay LABELLED ILLUSTRATIVE and are re-presented (`f_commit` mid 0.5, WTP mid $4.5 — unreached by S3); `w_ISO` is `needs-intake` (EIA-861 commercial share, resolves to 1.0); the eligible-set default is the memo's RECOMMENDATION (D-3c OPEN); no netting logic is built (D-6 OPEN). `FINDING-scn-ws3b-2026-09-06.md` | **yes (SCN-WS4b 2026-09-06)** — `LOAD-HI` / `LOAD-HI-ORGANIC` disclosed in the campaign YAML (ERCOT tail regime in 2030 only; ORGANIC byte-identical on PJM/CAISO/NEISO through 2030) + the six-ISO adequacy reading pre-declared (`FINDING-scn-ws4b-2026-09-06.md` §2) + the `backstop_built_mw`/`_mwh` column; siting sourced for ERCOT/PJM/MISO (SCN-WS4a). **Inputs re-derived 2026-09-06 (SCN-LOAD, ruling S4)** — the growth/DC/electrification constants now derive from the curated `load-forecast` datatype; demand at 2030 moves +30.9 % (ERCOT mid) / +17.8 % (PJM mid), and the `LOAD-HI` case comment's ERCOT tail-regime arithmetic is stale (block share 97.3 % → 44.1 %, routed). `FINDING-scn-load-2026-09-06.md` | **yes r#2** — six-ISO REF bases + `scenario_campaign_matrix.yaml` + the `--set` override (WS-0 item 4) |
| 2 reaches dispatch + deployment | yes (G-C2 + G-C3 closed at WS-1a; cap-row dual NOT exported — G-E4 rider now assigned to **SCN-WS0-R**) | yes | **yes** (SCN-WS2a: the row → dispatch; dual → the existing `max()` screen seam; deployment leg not exercised by the 1-yr T0) | **yes** (SCN-WS3b): the row rides the clean-tier family as its second consumer (region order state → federal → voluntary, all-zone mask, RHS = `V / E_total` of every zone's demand, escape at the WTP ceiling) → dispatch; its dual → the existing `clean_attribute_price_by_fuel → max(EAC, RPS dual, clean dual)` screen seam, no new consumer. Trivial-first LP (1 zone / 24 h): binding dual = the clean-minus-dirty gap; ceiling dual = WTP with escape = the shortfall (objective identity); curtailed wind recovered before thermal is displaced. Deployment leg not exercised — a zero-LP build lane | yes | — |
| 3 paired probe right-signed, per ISO | **ALL SIX ISOs measured at 2027 on the S2 floor (SCN-WS1b-r2, 2026-09-06, `FINDING-scn-ws1b-2026-09-06.md`)** — twelve paired T0 arms, REF vs `carbon_price_path=mid`. **Three LIVE** (ERCOT/PJM/MISO, +$3.75/t): right-signed, STOP gate **8/8 PASS on PJM and MISO**, 7 PASS + 1 reported band miss on ERCOT; coal→gas re-ordering visible in all three, with PJM shedding **17.4 TWh of coal (7.7 % of its coal output)** to a $3.75/t price because the coal/gas-CC spread is narrow, not because the price is large. **Three INERT** (CAISO/NYISO/NEISO): Δ = **0.000000** on every metric to six decimals — the ruled S2 outcome measured, not a null. **CAMPAIGN-GRADE ON PRICE: PJM and MISO only.** ERCOT's price level is NOT (641 scarcity hours, reserve margin −6.5 %, 4.6 TWh unserved in BOTH arms — the known G-S4 defect); its CO2 and merit-order results are robust to it, its price is not. **Note the charter's 2026-only leg was structurally unrunnable** — `CARBON_PRICE_PATHS` anchors every RFF path at $0 in 2026, caught at zero LP by phase 0 and re-scoped to 2027 (desk r#7 ratified). **Cross-campaign result:** the price-setting marginal rate exceeds SCN-WS4c's load-following rate in 3/3 ISOs (1.13–1.33×), so the two are not interchangeable; the magnitude is a range, not a constant, and coal share does not order it **ERCOT Stage A-POLICY (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CARB-LO/MID/HI at T1-F 2026–2030 at THE PIN. 2027 (control valid): ΔCO2 −0.393 / −0.928 / −2.335 Mt at $2.00 / $3.75 / $7.50/t, coal→gas-CC ~1:1, every zero-carbon row 0.0000, import 0.0 by construction (upper bound); CARB-MID 2027 reproduces WS-1b to every digit (255.0452 Mt); dose-response SUPER-linear (HI 2.52× MID). Leg-vs-leg at the pin the response SATURATES under scarcity (HI − LO −1.94 → −0.13 Mt, 2027 → 2030). **2028–2030 vs REF is CONTAMINATED**: every arm converts ~3 GW/yr of gas-CC to CCS at the retrofit cap (VOL-HI at carbon $0 included) while the `1cc45bb2` REF converts none — capx D65-B is LIVE on ERCOT; the REF/LOAD-HI re-solve is routed. Price disclosure-only (G2). Gates 12 PASS / 0 kill.** **NEISO (SCN-WS5A-POLICY-NEISO, 2026-09-07): the S2 inertness EXTENDS TO THE WHOLE T1-F WINDOW and is now a phase-0 KILL, not a solved null** — all three `CARB-*` plus `CARB-MID+LOAD-HI` differ from their baseline in exactly one resolved field whose only LP-affecting consumer resolves identically in all five years (RGGI 26.05 → 34.15 $/t dominates every registered path; closest approach `high` at 2030, $30.00 vs $34.15). **20 solve-years never spent.** | **ERCOT + NEISO at HEAD posture (SCN-WS2b)** — direction holds table by table vs the July surface, invariant pattern identical; ERCOT saturates above ~$20/MWh on the queue budget and its price/deployment levels are not campaign-grade (adequacy collapse, G-S4 stands); NEISO right-signed on share/price/imports but its CO2 read-out is governed by the CCS emission-rate seam (`FINDING-scn-ws2b-2026-09-06.md` §5.3, routed) **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CES-P10/P20/P30 at the pin. No dispatch footprint in 2026–2027 (every fuel row 0.0000); the premium acts through the offer (negative-price hours 522 → 599, captured wind −$0.9 / −$1.8) and the ENTRY screen: P20 +2,000 MW wind for solar (2030), P30 +1,500 MW solar / −1,000 MW gas-CC (2029) + 5,000 MW wind (2030). **The ladder does NOT saturate at $20–30** at the pin (clean 0.3992 vs 0.4058, CO2 303.08 vs 299.59 Mt) — WS-2b's `iso_budget_exhausted` saturation was its POC base's. 2028–2030 vs REF contaminated by the D65-B CCS conversion (routed).** **NEISO ladder at the policy pin (SCN-WS5A-POLICY-NEISO, 2026-09-07): large, entirely retrofit-driven, non-saturating, and it REVERSES SIGN on the leakage line** — 2030 in-ISO CO2 6.1058 → 3.0942 / 2.8713 / 2.9392 Mt at $10/$20/$30 (non-monotone at the top rung) against a strictly monotone leakage-inclusive 10.8715 → 5.2251. `vre_mw` identical to REF in every rung: WS-2b's "zero economic entry" now has its mechanism (the $50 RPS escape masks the premium on the entry screen). July's CO2 read-out caveat RETIRED — post-D77. | NEISO only, escape regime (dual = ACP $50 exactly; CO2 +2e-4 reported not smoothed — `FINDING-scn-ws2a-2026-09-05.md` §4.3). **Quotable as a CAMPAIGN-LEVEL result since S3**, having been run at exactly the committed level **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): CES-T80 at the committed level. Escape regime in all five years, dual = ACP $50.0000 exactly (G4 exact); REF's credited share 0.3953 → 0.3172 never reaches 0.55. First deployment reading: the $50 dual swaps +3,500 MW solar for −3,000 MW gas-CC in 2029 and pays +16.8 / +16.4 TWh of unserved (2029/30). **DEFECT FOUND (routed): the row credits DUMPED energy** — curtailment goes to 0.000 the year the row binds with thermal/storage/unserved unchanged and I3 gaining a 2.15–2.41 % dump line; ~4.9 TWh/yr of phantom credit at ERCOT.** **NEISO T1-F, both limbs of the identity in ONE arm (`CES-T80`, 2026-09-07):** ACP 50.0000 exactly where unmet (2026-2028), −0.0 where met (2029), strictly interior 4.2912 (2030). Deployment leg still unexercised — now for a MEASURED reason: the $50 ACP equals NEISO's $50 RPS escape, so `max(50,50)` adds no entry. | **no** **ERCOT (SCN-WS5A-POLICY-ERCOT, 2026-09-07, `FINDING-scn-ws5a-policy-ercot-2026-09-06.md`): VOL-HI / CES-P20+VOL-HI / ALL-CLEAN at the pin (VOL-MID killed at phase 0, slack all five years). Dual 0 / 0 / 7.0 / 7.0 / 7.0 $/MWh exactly (slack while V < eligible, escape at the `high` ceiling from 2028; G7 exact), ALL-CLEAN [50, 7] all years; escape 24.5 / 59.0 / 100.8 TWh. Price and unserved byte-identical to REF in every year; the row moves NO build; under a $20 premium its dual is irrelevant to deployment (build ≡ CES-P20); on top of carbon + DC-high load it adds 0.0000 Mt. Both nettings reported (counts-toward headline). **Same dump-crediting defect as the CES target** (routed): the row's first act is to "recover" REF's whole 4.9 TWh curtailment into the dump column.** **NEISO (SCN-WS5A-POLICY-NEISO, 2026-09-07) — the cleanest form of the instrument any ISO can produce, and it moves nothing.** `E_DC` = 0 makes `VOL-MID`/`VOL-HI` volume-identical to the MWh, i.e. a pure $4.50-vs-$7.00 ceiling ladder; measured byte-identical in every column of every year, the dual alone differing. Row binds 2026-2028, slack 2029-2030; dual = ceiling exactly / −0.0 exactly; 2026 escape 1.5127 TWh exactly. NEISO can carry D-2(b)'s ceiling evidence and its answer is **"the ceiling cannot be discriminated here"**. G8 VACUOUS (REF curtailment 0.0000 by construction). | **yes — all six** (SCN-WS4c 2026-09-06, `FINDING-scn-ws4c-2026-09-06.md`): 15 T0 arms (2026) + 4 T1-F arms (2026–2030), campaign `scn-ws4-probe`. CO2 rises in every ISO on the fossil stack alone (ERCOT +13.687 / PJM +20.084 / MISO +8.992 / CAISO +2.544 / NYISO +1.637 / NEISO +0.812 Mt), price rises in all six, footprint confined to fossil + imports, `by_fuel["import"]` 0.0 everywhere. **The implied marginal rate carries a SIGNED error vs the fossil-fleet average** — below it wherever coal is inframarginal (0.73× / 0.77× / 0.65×), above it where not (1.05× / 1.05× / 1.17×) — so "fossil-average × added MWh" is biased high 23–35 % with coal and low 5–17 % without. SCN-WS4b's readings score 20 HIT / 3 SPLIT / 3 MISS **CAMPAIGN LANDED, then RE-SOLVED (SCN-WS5A-LOAD + SCN-WS5A-RESOLVE, 2026-09-06)** — `scn-campaign-load-2026-09-06`, **16 legs / 80 solve-years, all rc=0**, six ISOs × {REF, LOAD-HI[, LOAD-HI-ORGANIC]} over T1-F 2026–2030 (`FINDING-scn-ws5a-load-synthesis-2026-09-06.md` + six per-ISO FINDINGs). The campaign **FALSIFIED ruling S5's premise** that the load half carries no `gas_cc_ccs`: five of six ISOs carry mis-rated CCS in REF from 2028, which is card **D-10** and owner ruling **S8**. **13 of the 16 legs need a re-solve post-capx-D77; 7 are landed** (NEISO 2, NYISO 3, PJM 2) at THE PIN `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`, CAISO 3 + MISO 3 with sibling lanes (`FINDING-scn-ws5a-resolve-2026-09-06.md`); ERCOT's three are CCS-clean and stand at `1cc45bb2`, so the campaign sits at **two declared pins**. Post-fix, the 2030 REF CO2 level falls **54.3 % (NEISO) / 47.8 % (NYISO) / 1.58 % (PJM)** and the load-response **ΔCO2 falls 82 % / 42 %** — the correction does **not** cancel out of a delta, because it re-screens the retrofit fleet differently in the two arms. Gates 5/5 PASS on every re-solved leg (G1 unit identity `host rate × (1 − capture)`, zero failures). **The §1.1 volume-vs-shape headline survives the repair**; **no delta from a CCS-carrying ISO may be quoted from a pre-fix bundle**. CAISO and MISO re-solves are with sibling lanes. | — |
| 4 backcast byte-identity | yes (WS-1a: no key moves; keeper + forecast key list, FINDING §5) — **re-measured at the S2 floor** (SCN-WS1c): 0 keys moved, default `e5ecd4105ada3e58` stable, **0 of 90** committed `run_config.json` on the changed branch, backcast 2023–25 trajectories identical in all six ISOs; six keeper bundles named, `FINDING-scn-ws1c-2026-09-06.md` §4 | yes | yes (SCN-WS2a: six keeper keys byte-identical, FINDING §5) | yes (SCN-WS3b: **0 of 128** committed `run_config.json` keys moved on the changed branch — 18 backcast, 110 forecast — six keeper keys byte-identical, pinned default `e5ecd4105ada3e58` / backcast `6a2845e50951394e` unchanged; `mode="backcast"` + hindcast coercion to the dataclass defaults asserted by test; `FINDING-scn-ws3b-2026-09-06.md` §3) | yes | — |
| 5 matrix duty | stamped — `carbon_price_path` + `policy_bundle` base rows and a cell in every shard at `717de664` (on main). The r#2 "NOT stamped" reading was true at `db8b6015`; the lane's claim ran one PR ahead of its commit and the lane closed it itself. Verified on disk by SCN-MX-R-r2 (r#4, `FINDING-scn-mxr-2026-09-06.md` §5). | stamped | stamped (`federal_ces_target` row + six cells, SCN-WS2a last commit) | stamped (`voluntary_clean_demand` base row + a `U` cell in all six shards, SCN-WS3b last commit) | stamped | — |
| 6 emissions grain | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | by fuel / by zone | **G-E1..E5 CLOSED** (SCN-WS0, all six items landed 2026-09-05); G-E6 / G-E7 stay OPEN as declared disclosure items |
| 7 registered probes on dashboard | **twelve arms** `{ercot,caiso,pjm,miso,nyiso,neiso}-2026-2027-scn-ws1-probe-{ref,carb}` (kind `scenario`, campaign `scn-ws1-probe`, each CARB paired to its REF) — SCN-WS1b-r2 **+ ERCOT Stage A-POLICY: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{carb-lo,carb-mid,carb-hi,carb-mid-plus-load-hi}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, each paired to `reference_case: REF`; solved at THE PIN `bdfb3095` in four owner-launched sub-lanes) **NEISO: NONE — four carbon cases killed at phase 0 on a proven identity, never solved, correctly never registered.** | **six ladder legs** `{ercot,neiso}-2026-2030-scn-ws2-ladder-{bau,ces-20,ces-40}` (kind `scenario`, campaign `scn-ws2-ladder`) — G-S5 CLOSED, the pruned POC evidence restored at HEAD **+ ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{ces-p10,ces-p20,ces-p30,ces-p20-plus-vol-hi}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN) **+ NEISO `neiso-2026-2030-scn-campaign-policy-2026-09-06-{ces-p10,ces-p20,ces-p30}`.** | NEISO T0 pair `neiso-2026-2026-scn-ws2a-neiso-2026-t0-{ref,target}` (kind `scenario`) **+ ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{ces-t80,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN) **+ NEISO `neiso-2026-2030-scn-campaign-policy-2026-09-06-{ces-t80,all-clean}`.** | — **ERCOT: `ercot-2026-2030-scn-campaign-policy-2026-09-06-{vol-hi,ces-p20-plus-vol-hi,all-clean}`** (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, at THE PIN; VOL-MID killed at phase 0, never solved) **+ NEISO `neiso-2026-2030-scn-campaign-policy-2026-09-06-{vol-mid,vol-hi,ces-p20-vol-hi,all-clean}`** — `vol-mid` is LIVE here, unlike ERCOT. | **19 arms**, campaign `scn-ws4-probe` (kind `scenario`): `{ercot,caiso,pjm,miso,nyiso,neiso}-2026-2026-scn-ws4-probe-t0-{ref,load-hi[,load-hi-organic]}` + `{ercot,neiso}-2026-2030-scn-ws4-probe-t1f-{ref,load-hi}`. The three ORGANIC arms are ERCOT/MISO/NYISO only — CAISO/PJM/NEISO killed at rule-29 phase 0 as byte-for-byte degenerate **plus 16 campaign arms**, campaign `scn-campaign-load-2026-09-06` (kind `scenario`, each case paired to `reference_case: REF`): `{ercot,caiso,miso,nyiso}-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}` + `{pjm,neiso}-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi}` (PJM and NEISO ship a degenerate DC axis). **13 of the 16 were RE-REGISTERED UNDER THE SAME IDS post-capx-D77** by SCN-WS5A-RESOLVE, with each pre-fix bundle's slim artifacts deleted in the same commit (rule 26 `[R-DELETE]`); ERCOT's three keep their `1cc45bb2` bundles. A sidecar's `git.sha` and key provenance therefore say which pin its numbers are from — read it before quoting one. | `scn-ws0-smoke` REF/CARB pair |

**The CES-target column's level became COMMITTED with no evidence change** (SCN-LEVELS,
2026-09-06). D-2 → S3 committed the plan's §3.5 table, and SCN-WS2a had already built and
probed the target row against exactly those values under an "illustrative" label — so **no
cell of this table moved on the evidence**: rows 2, 4, 5 and 7 are untouched, row 1 changes
only its label, and row 3's probe becomes quotable as a campaign result rather than as
machinery. Measured: 91 pre-existing cache keys byte-identical, no `ScenarioConfig` default
moved, no solve. The three levels S3 did **not** reach are named in §2's D-2 row and must be
re-presented, not inferred.

**Open lane assignments against the scorecard:** ~~WS-0 → the Emissions column entire (criterion
6) + criterion 1's harness half~~ — **LANDED 2026-09-05, ALL SIX ITEMS**, G-E1..E5 closed and
criterion 1's harness half with them; G-E6/G-E7 remain open as declared disclosure items
(`docs/handoffs/FINDING-scn-ws0-2026-09-05.md`); WS-1a → Carbon row 1 (the G-C1 defect) and rows 4/5; WS-1b →
Carbon rows 3/7; WS-2a → the CES-target column rows 1/2/4/5 and its probe half of row 3; WS-2b →
CES-premium rows 3/7; WS-3a → nothing (memo); WS-4a → Load-HI row 1 (partial → the siting half)
— **LANDED 2026-09-05**: MISO populated from the 2026 LTLF regional DC decomposition, ERCOT
verified already-populated (the plan §2.4 "only for PJM" line was stale and is corrected), NEISO
`{}` re-confirmed with its arithmetic; the named case remains SCN-WS4b's and is NOT claimed. **WS-4b → Load-HI row 1's case half — LANDED 2026-09-06** (branch `claude/scn-ws4b-load-hi-adequacy-jvv96t`; the §5 stem rows name `-b2np`, the r2 charter `scn-ws4b2-…-x3mc` — reconcile): the case comment completed, the reading pre-declared per ISO against the bare `ff-verdicts.json` keys, the report column with 13 tests; six items routed in its FINDING §5, first among them that the board's `gate_reading` prose is stale for CAISO/MISO. **SCN-WS4c is unblocked.**
The D-4 gap list is `docs/handoffs/FINDING-scn-ws4a-2026-09-05.md` §4, presentable unedited; that
FINDING §6 routes one cache-epoch ledger entry (MISO forecast bundles stale at the same key) that
SCN-WS4a may not write, `results/cache.py` being another lane's region.

---

## 4. Collision register (file → owning lane → wave)

**Wave-1 shared-file protocol** (written verbatim into every wave-1 prompt):

1. `config/scenarios.py` and `runner.py` are touched by WS-1a and WS-2a in the **named disjoint
   regions ONLY**. Any edit outside your region is a **STOP** — route it to SCN-DESK in your
   FINDING; do not widen.
2. The six matrix shards (`docs/codebase-site/data/mechanism-matrix/<ISO>.js`) and
   `docs/codebase-site/data/mechanism-matrix.js`: make the edit your **LAST commit**, after
   `git fetch origin main` + rebase, as **one appended cell line per ISO**, so any conflict is
   one line. This is not advisory — capx D60-R2's re-scores and the owner's backcast lanes
   append to these files several times a day (`3eaf7918`, `fe38a699` both on 2026-09-05).
   Merge order if WS-1a and WS-2a are both ready: **WS-1a first, WS-2a rebases.** CI
   (`scripts/check_mechanism_matrix.py`) enforces that a new `ScenarioConfig` field carries its
   base row + a cell line in every shard **in the same PR** (rule 28 duty c).
3. **`configs/scenario_campaign_matrix.yaml` OWNERSHIP TRANSFERS to SCN-WS4b at r#2** — WS-0's
   YAML work (item 4) landed and its owed items 5–6 do not touch the file. SCN-WS0-R must not
   edit it.
3a. **MATRIX-TREE PROTOCOL, AMENDED r#3.** The r#2 freeze is **lifted** — SCN-WS1a minted its
   own rows and cells, so there is no longer one repair lane holding the tree. The standing
   rule returns to protocol item 2 (**last commit, after rebase, one appended line per ISO**),
   and it binds harder than at r#2: capx D65 stamped its own row and six cells at `4b28c93f`,
   so the capx track is an active concurrent writer. Live SCN-WS2a stamps the CES row itself
   (rule 28(b) — the session that tests the mechanism stamps it); SCN-MX-R stamps it **only
   if** WS-2a lands without it. SCN-WS1b and SCN-WS2b stamp their own cells, last commit.
4. **Nobody touches `frontend/data/forecast/program-status.json`** — it is the capx board,
   written by D60-R2 and D58.

| file / region | owning lane | wave | note |
|---|---|---|---|
| `src/market_sim/results/export.py`, `results/outputs.py`, `results/emissions.py` | SCN-WS0 | 1 | |
| `src/market_sim/matrix.py`, `scripts/collate_full_horizon.py` | SCN-WS0 | 1 | |
| new `scripts/report_scenario_deltas.py`, new `scripts/collate_scenario_campaign.py` | SCN-WS0 | 1 | WS-4b adds the "backstop-built" column to the former **after** WS-0 lands. |
| `scripts/run_full_horizon.py`, `scripts/run_ces_leg.py` | SCN-WS0 | 1 | **the `--set` override ONLY** |
| `scripts/register_forecast_run.py`, the forecast dashboard pages | SCN-WS0 | 1 | NOT `frontend/data/forecast/program-status.json` |
| `configs/scenarios/*`, `configs/scenario_campaign_matrix.yaml` | SCN-WS0 | 1 | sole writer this wave |
| `src/market_sim/policy/carbon.py`, `policy/cap_and_trade.py`, `config/scenario_resolvers.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/interchange/spec.py` — **the one carbon-adder line (~:1931)** | SCN-WS1a | 1 | |
| `runner.py` — **REGION: the `assemble_mc` call site (~:2561-2575)** | SCN-WS1a | 1 | |
| `config/scenarios.py` — **REGION: the D34 guard in `__post_init__` (~:15572)** | SCN-WS1a | 1 | |
| `src/market_sim/results/cache.py` — **one epoch entry** | SCN-WS1a (LANDED) → SCN-WS0-R (WITHDRAWN) → **SCN-MX-R at r#3** | 1–3 | The WS-4a-routed entry (MISO forecast bundles stale at the same key after the DC-share change) did **not** land — verified: the file is unchanged since `db8b6015`. MX-R's scope is widened by this one file only, and it writes a ledger entry, never a key. |
| `tests/unit/policy/test_cap_and_trade.py`, `test_carbon_price_below_base_guard.py` | SCN-WS1a | 1 | |
| `src/market_sim/model/lp/rows.py` | SCN-WS2a | 1 | WS-3b is the next writer (wave 2), **after** WS-2a merges. |
| `src/market_sim/policy/federal_ces.py`, `policy/clean_tiers.py` | SCN-WS2a | 1 | |
| `runner.py` — **REGION: RPS/clean-row arming + dual plumbing (~:1195-1229, :2851-2864, :4484-4521)** | SCN-WS2a | 1 | |
| `config/scenarios.py` — **REGION: the `federal_ces_*` block (~:3084-3157) + its `__post_init__` guard (~:15584)** | SCN-WS2a | 1 | |
| `docs/codebase/05-policy.md`, `policy/constraints.py` docstring (G-S6) | SCN-WS2a | 1 | |
| `docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md` (new) | SCN-WS3a | 1 | memo only |
| `config/constants.py` — **REGION: `DATACENTER_ZONE_SHARE` / `DATACENTER_ADDITIONS_MW` only** | SCN-WS4a | 1 | `VOLUNTARY_*` anchors are WS-3b's separate region, wave 2. |
| `src/market_sim/data/datacenter.py`, `tests/unit/data/test_datacenter.py` | SCN-WS4a | 1 | WS-3b's DC-linked volume helper is the next writer, **after** WS-4a merges. |
| the six matrix shards + `mechanism-matrix.js` | **SCN-MX-R ONLY until it merges**; then ALL, last commit only | 1–3 | see protocol items 2 and 3a |
| `scripts/register_forecast_run.py`, `configs/scenarios/*` | SCN-WS0 (LANDED) → **SCN-WS0-R** | 1–2 | |
| `configs/scenario_campaign_matrix.yaml` | SCN-WS0 (LANDED) → **SCN-WS4b** | 1–2 | transfer recorded at r#2 |
| `scripts/check_mechanism_matrix.py` | **NOBODY on the SCN track** | — | the duty-(c) CI gap is diagnosed and reported by SCN-MX-R and routed to the capx/audit track; `scripts/` is not this desk's to repair |
| `scripts/forecast_verdict.py`, `frontend/data/forecast/program-status.json` | **capx D60-R2 / D58** | — | **no SCN lane may touch these** |
| `src/market_sim/model/capacity_evolution/ccs.py` + the downstream plant emission-rate restoration (`data/emissions.py`, `data/fleet/`, the `runner.py` seam) | **capx track — UNCHARTERED at r#45** | — | The CCS emission-rate seam (WS-2b §8 item 1). No SCN lane may touch it; no capx lane holds it either (§0 r#9, card D-9). Stage A-POLICY and WS-1b-r2 leg 2 wait on it. |
| `policy/voluntary_demand.py` (new), `model/lp/rows.py` (clean-tier family, second consumer), `data/datacenter.py` (one volume helper), `constants.py` **REGION `VOLUNTARY_*`**, `scenarios.py` **REGION the new `voluntary_*` block**, `runner.py` **REGION the voluntary row arming beside WS-2a's**, `configs/scenario_campaign_matrix.yaml` **rows `VOL-MID`/`VOL-HI`/`CES-P20+VOL-HI`/`ALL-CLEAN` only** | **SCN-WS3b** (LANDED r#10) | 2 | Written at r#9; the file list is the memo §5.4's. Ownership of the four YAML rows passes from SCN-WS4b (landed). |
| `frontend/data/hindcast/invariant-failures.json` | **SCN-FIX1** (the `scn-` backlog keys) · SCN-WS5A-LOAD and SCN-WS1b-r2 (each run they register, same commit) · the audit track's Y-lanes · capx (their 8 ids) | 3 | Append-only, one key per line, last commit after rebase. Nobody deletes another lane's key. |
| `scripts/collate_scenario_campaign.py` (system-scope delta only) + new `tests/scoring/test_collate_scenario_campaign_common_set.py` | **SCN-FIX1** | 3 | WS-0's file; WS-5A-LOAD consumes, never modifies. |
| `configs/scenario_campaign_matrix.yaml` — **the four carbon-form rows** (CARB-LO/MID/HI, CARB-MID+LOAD-HI) + their pin in `tests/scoring/test_scenario_campaign_configs.py` | **SCN-FIX1** (r#11 item 3) | 3 | The policy lanes READ the YAML (P3) and never edit it. ALL-CLEAN's form waits on the voluntary cards. |
| `configs/scenario_campaign_matrix.yaml` (the five carbon-form rows), `tests/scoring/test_scenario_campaign_configs.py`, `constants.py` REGION `VOLUNTARY_*` (words), `scenarios.py` the three `voluntary_*` docstrings (words) | **SCN-FIX2** | 3 | FIX1's r#11 items, re-chartered after FIX1 landed on the r#10 text. |
| `scenarios.py` **REGION the `mass_cap_*` block (~:2941) + the two registration lines**, `policy/cap_and_trade.py::_power_sector_cap`, the YAML `CAP-STATE-TIGHT` case, new `tests/unit/policy/test_mass_cap_schedule.py`, `docs/codebase/05-policy.md` (one paragraph), the matrix row + six cells (last commit) | **SCN-CAP** | 3 | Rebases on SCN-FIX2 if it lands first (both touch the YAML, disjoint case blocks). |
| `results/scn-campaign-load-2026-09-06-r2/<ISO>/` (new), the five re-solved ISOs' campaign sidecars (same ids), `results/scn-campaign-load-2026-09-06/<ISO>/` for those five (DELETED on re-registration; ERCOT's stay), `invariant-failures.json` (their keys), the synthesis FINDING (a dated ADDENDUM section only), STATUS, `PRECOMMIT-/FINDING-scn-ws5a-resolve-*.md`, the five `datacenter_load_block` cells | **SCN-WS5A-RESOLVE** | 3 | capx D65-B-R writes bare-id sidecars to the same dir — distinct ids, append-only. |
| *(compute, not a file)* the per-plant solve slot (rule 12) | **capx r#51 queue: D65-B-R batch / D78-R3 / D75-R-ARM / D76-P3, all PJM-heavy** ↔ **SCN-WS5A-RESOLVE**'s PJM / CAISO / MISO legs ↔ **SCN-WS5A-POLICY-\<ISO\>** | 3 | **AMENDED r#17 by ruling S14:** the SCN track may run **2 concurrent solves on different ISOs**, not one — rule 12's own cap. Not while capx is mid-solve; the owner sequences that half, being the only party who sees both tracks. Pair a heavy ISO with a light one (MISO 9.65 GB, CAISO 4.87, ERCOT 4.2 on a 15 GB box). A second-in-slot lane names the lane it runs beside in its PRECOMMIT. |
| `frontend/data/hindcast/<iso>-2026-2030-scn-campaign-policy-2026-09-06-<case>.json`, `results/scn-campaign-policy-2026-09-06/<ISO>/`, `PRECOMMIT-/FINDING-scn-ws5a-policy-<iso>-*.md`, the ISO's three shard cells | **SCN-WS5A-POLICY-<ISO>** | 3 | Per-ISO disjoint. The D65-B batch writes other run ids to the same sidecar dir — append-only. |

---

## 5. Issuance record

Stems are recorded so a relaunch (`…-r2`) can never collide with the original.

| refresh | lane | model (id) | branch stem issued | **branch realized** | data profile | plan §7 body used |
|---|---|---|---|---|---|---|
| r#1 | SCN-WS0 | **Opus** `claude-opus-5` | `claude/scn-ws0-k7m2` | `claude/scn-ws0-k7m2-8743yi` | `neiso` | §7 "WS-0", verbatim |
| r#1 | SCN-WS1a | **Fable** `claude-fable-5-1` | `claude/scn-ws1a-p4qd` | `claude/scn-ws1a-carbon-d1-eupbi5` | `caiso` | §7 "WS-1a", verbatim + the D-1 gate split (item 1 conditional) |
| r#1 | SCN-WS2a | **Fable** `claude-fable-5-1` | `claude/scn-ws2a-t9xb` | `claude/scn-ws2a-federal-ces-qm512t` | `neiso` | §7 "WS-2a", verbatim |
| r#1 | SCN-WS3a | **Fable** `claude-fable-5-1` | `claude/scn-ws3a-r6vn` | `claude/scn-ws3a-voluntary-demand-{s8iukw, 9f1you}` **(twice)** | `code` | §7 "WS-3a", verbatim |
| r#1 | SCN-WS4a | **Opus** `claude-opus-5` | `claude/scn-ws4a-h3zc` | `claude/scn-ws4a-datacenter-shares-yf7wvi` | `all` | §7 "WS-4" **items 2 and 5 only** (items 1/3/4 split to WS-4b/WS-4c, wave 2) |

**r#2 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#2 | SCN-WS0-R | **Opus** `claude-opus-5` | `claude/scn-ws0r-registration-t0-m4qk` | `neiso` | plan §7 "WS-0" **items 5 and 6 only** + the G-E4 cap-row rider (routed from WS-1a §4.3) + the WS-4a cache-epoch entry |
| r#2 | SCN-WS2a-R | **Fable** `claude-fable-5-1` | `claude/scn-ws2ar-ces-postures-probe-w8dr` | `neiso` | plan §7 "WS-2a" **items 3 and 4** + the G-S6 doc legs; matrix withheld to SCN-MX-R |
| r#2 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | not a plan §7 body — a rule-28 repair charter written at r#2 from the refresh's own finding |
| r#2 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | plan §7 "WS-4" **items 1 and 3** (the split recorded at r#1), no solve |

**r#3 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#3 | SCN-WS1b | **Opus** `claude-opus-5` | `claude/scn-ws1b-carbon-sixiso-h6rt` | `all` | plan §7 "WS-1b", verbatim + the reduced-form D-1 gate + WS-0's per-ISO leakage duty |
| r#3 | SCN-WS2b | **Opus** `claude-opus-5` | `claude/scn-ws2b-ces-ladder-clearing-p9wf` | `ercot` then `neiso` | plan §7 "WS-2b", verbatim |
| r#3 | SCN-MX-R | **Fable** `claude-fable-5-1` | `claude/scn-mxr-matrix-duty-repair-j5tv` | `code` | r#2 repair charter, **narrowed at r#3** to the CI-gate diagnosis + a conditional CES stamp |
| r#3 | SCN-WS4b | **Fable** `claude-fable-5-1` | `claude/scn-ws4b-loadhi-adequacy-b2np` | `all` | r#2 charter **re-emitted verbatim** |

**r#4 issuance (relaunches).**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#4 | SCN-WS4b-r2 | **Fable** `claude-fable-5-1` | `claude/scn-ws4b2-loadhi-adequacy-x3mc` | `all` | the r#3 charter **verbatim** |
| r#4 | SCN-MX-R-r2 | **Fable** `claude-fable-5-1` | `claude/scn-mxr2-matrix-duty-repair-t7bq` | `code` | the r#3 narrowed charter **verbatim** |

**r#7 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#7 | SCN-WS5A-LOAD-\<ISO\> ×6 | **Opus** `claude-opus-5` | `claude/scn-ws5a-load-<iso>-<4ch>` | \<iso\> | **S5** + SCN-WS4c landing | plan §7 "WS-5" Stage A, **load half only** |
| r#7 | SCN-WS5A-LOAD-SYNTH | **Opus** `claude-opus-5` | `claude/scn-ws5a-load-synth-<4ch>` | `code` | same | plan §3 WS-5 Stage C outline, load half; presents D-5 |

**r#6 am.1 issuance — two relaunches, one re-scope.** SCN-WS1b-r2
(`claude/scn-ws1b2-carbon-sixiso-r4hm`, Opus) and SCN-WS3b-r2
(`claude/scn-ws3b2-voluntary-demand-k8zp`, Fable). **The WS-1b-r2 charter carried a desk error**
(the retired `carbon_price_delta` form) which its phase 0 caught before any LP was spent; the
2027 repair is ratified at r#7.

**r#5 amendment 1 issuance — the four ruling-released lanes.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#5 am.1 | SCN-WS1c | **Fable** `claude-fable-5-1` | `claude/scn-ws1c-carbon-floor-v2rk` | `neiso` | **S2** | plan §7 "WS-1a" **item 1**, verbatim |
| r#5 am.1 | SCN-WS3b | **Fable** `claude-fable-5-1` | `claude/scn-ws3b-voluntary-demand-n5wq` | `ercot` | **S1** | plan §7 "WS-3b", verbatim + the memo's signed design |
| r#5 am.1 | SCN-LEVELS | **Fable** `claude-fable-5-1` | `claude/scn-levels-d2-commit-c3jx` | `code` | **S3** | not a plan §7 body — a records charter written from the ruling |
| r#5 am.1 | SCN-LOAD | **Opus** `claude-opus-5` | `claude/scn-load-forecast-intake-w9tf` | `all` | **S4** | plan §3 WS-4 **item 4** (the intake), scope set by the ruling |

**r#5 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | body used |
|---|---|---|---|---|---|
| r#5 | SCN-WS4c | **Opus** `claude-opus-5` | `claude/scn-ws4c-loadhi-probes-q8vd` | `all` | plan §7 "WS-4" **item 4**, verbatim + WS-4b's pre-declared readings as the scoring target + the four post-r#4 rule changes |

**r#9 issuance — one lane written at r#9, HELD on card D-8, then ISSUED at r#9 am.1 under ruling S6.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#9 | SCN-WS3b-r3 | **Fable** `claude-fable-5-1` | `claude/scn-ws3b3-voluntary-demand-q7mv` | `ercot` | **S1 + S6** (D-8, r#9 am.1) | plan §7 "WS-3b" **verbatim**, split from its WS-3c half; + the memo's signed design; + the r#9 standing changes (constant-family declaration; no solve) |

The full charter, so a successor can paste it without re-deriving it:

```
You are lane SCN-WS3b-r3. MODEL: Fable claude-fable-5-1 — this is the FIRST WRITER of a new mechanism (a new LP row family consumer, three new ScenarioConfig fields, a resolver) built from a signed design whose eligible set (D-3c) is still an open owner box, so the lane adjudicates as it builds; Sonnet is forbidden on every SCN lane (CLAUDE.md rule 27, desk §5.1). DATA PROFILE: ercot. Branch stem: claude/scn-ws3b3-voluntary-demand-q7mv.
Read CLAUDE.md freshly and in full — since this charter was first written at r#5 am.1 the rules that changed are: rule 1 [R-STRUCT] (the authorized offer-curve band-multiplier carve-out — irrelevant to you, but do not cite the old text), rule 13 [R-MEASURED] (its one exception), rule 21 [R-DOF] (the R-AY cross-reference), rule 22 [R-HOLDOUT] (the R-AZ registration-time marker re-check — you register nothing, but it binds every registration seam you touch), rule 29 [R-SCREEN] clause (c) DELETE BEFORE MERGE, and rule 30 [R-TOUCHPOINT-FOLD] with its 2026-09-06 (a) amendment; docs/forecast-development-plan-2026-07.md (§2.1b — you need no grant, you solve nothing; §2.4 including the data/clean prerequisite; §7; §7.5); the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §1 (definition of done), §2.3, §3 WS-3 (the whole workstream text), §3.5 (VOL-MID / VOL-HI / CES-P20+VOL-HI / ALL-CLEAN — the cases your fields make expressible), §7 WS-3b; the memo docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md IN FULL including Addendum A (§2.1 is the signed representation, §3 the volume construction and anchors, §4.1 the default eligible set, §5 your fields/coercion/cache-key/registry/matrix duties, §5.4 the runner and pipeline touch points, §6 the probe design you hand to SCN-WS3c, §7 the boxes); FINDING-scn-ws2a-2026-09-05.md (the rows.py coupling relaxation you inherit — the second-consumer seam it documents is yours); FINDING-scn-ws4a-2026-09-05.md and FINDING-scn-load-2026-09-06.md (the DC block and the load constants your volume construction consumes — SCN-LOAD RE-DERIVED them on 2026-09-06 under ruling S4, so read the values at HEAD, never from the memo's §3.3 table, and cite the datatype); FINDING-scn-levels-2026-09-06.md §4 (the two voluntary levels S3 did NOT reach); the matrix docs/mechanism-testing-matrix.md §5 + the six shards under docs/codebase-site/data/mechanism-matrix/ (you add a row and six cells); and the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#9 + §2 (S1, S3, S5 bind you; D-3c and D-6 are OPEN) + §4 (your file regions).

PRECONDITIONS (verify with git log on origin/main; STOP and route if any is unmet):
- SCN-WS2a's rows.py coupling relaxation is on main (`089eb401` — clean-tier rows no longer require the RPS region family). It is.
- SCN-WS4a's DC module + SCN-LOAD's re-derived constants are on main (`d14a7ed0`). They are.
- Ruling S1 (D-3 = YES, a declared forecast-only publicly-anchored default-off axis; D-3b DEFERRED — in-LP hourly matching stays in the isolated scope2-lce-portfolio tool; you build the ANNUAL VOLUMETRIC row only). Ruling S3 (the memo's box-5 defaults are the committed levels EXCEPT `f_commit` mid and the WTP-ceiling level, which S3 did not reach — carry those two as LABELLED illustrative and list them for re-presentation; never infer a ruled value).
- No twin: search PRs and origin branches for "voluntary", "ws3b", "scn-ws3b" before your first commit. The r#5 am.1 stem `claude/scn-ws3b-voluntary-demand-n5wq` and the r#6 am.1 stem `claude/scn-ws3b2-voluntary-demand-k8zp` never produced a branch, a PR or a commit across three desk refreshes; if either now shows work, STOP and route to SCN-DESK — do not build the twin.

FILES YOU OWN (your regions; anything else is a STOP):
- new `src/market_sim/policy/voluntary_demand.py` (volume resolver, eligibility, WTP), new `tests/unit/policy/test_voluntary_demand.py`.
- `src/market_sim/model/lp/rows.py` — the clean-tier row family ONLY, as its second consumer (after WS-2a's federal_ces). No edit to any other row family.
- `src/market_sim/data/datacenter.py` — ONE new DC-linked volume helper (the memo §3.1 construction); do not touch the share/anchor code WS-4a and SCN-LOAD wrote.
- `src/market_sim/config/constants.py` — a NEW `VOLUNTARY_*` region only (baseline share, committed fraction by year, WTP ceiling, ISO allocation basis), every value cited to the memo §3.3 / Addendum A.1 public anchors (NREL voluntary green power market tables, CEBA public aggregate, the hyperscalers' published commitments, EIA-861 commercial share). `needs-citation` cells stay labelled, never silently filled.
- `src/market_sim/config/scenarios.py` — a NEW contiguous `voluntary_*` block of ≤3 fields (`voluntary_clean_demand_path: off/low/mid/high`, `voluntary_wtp_ceiling_usd_per_mwh`, `voluntary_eligible_fuels`) + their `__post_init__` forecast-only coercion (the `datacenter_load_path` / `carbon_price_delta` pattern) + registration in `_CACHE_KEY_OPTIONAL_FIELDS` at the inert default. Never any other block.
- `runner.py` — ONLY the row-arming + dual-plumbing lines the memo §5.4 names, adjacent to WS-2a's federal_ces arming; the dual reaches the entry screen through the EXISTING `max(EAC, RPS, clean)` seam (rule 19 [R-ONE-MECH]) — no new seam.
- `configs/scenario_campaign_matrix.yaml` — ADD the four cases the plan §3.5 table lists and the YAML lacks: `VOL-MID`, `VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN` (config only; you solve none of them). Ownership of this file passed from SCN-WS4b (landed) to you for these four rows only.
- `docs/codebase-site/data/mechanism-matrix.js` (one base row `voluntary_clean_demand`) + the six shards (one appended cell line each) — LAST commit after `git fetch origin main` + rebase; capx D60-R3 and the owner's backcast lanes append to these files several times a day.
- the plan §5.1 Voluntary column (rows 1, 2, 4, 5), `docs/handoffs/FINDING-scn-ws3b-<date>.md`, `docs/codebase/05-policy.md` (one section).

FILES YOU MUST NOT TOUCH (with the owner, and which are LIVE now):
- `src/market_sim/model/capacity_evolution/ccs.py`, `data/emissions.py`, the plant emission-rate restoration path — capx track (the routed CCS emission-rate seam; UNCHARTERED at capx r#45, still capx's). The voluntary row must not credit `gas_cc_ccs` by default (memo §4.1 renewable-only) — that is the one place your build meets the seam, and the override `voluntary_eligible_fuels` is the labelled path, not a default.
- `scripts/forecast_verdict.py`, `frontend/data/forecast/program-status.json` — capx D60-R3, LIVE at leg 4/5.
- `src/market_sim/data/fleet/campd_bins.py` — owner's nyiso-198, LIVE (open PR #5030).
- `src/market_sim/data/offer_curves.py`, `assembly.py`, `backcast_config.py` — owner's caiso-254, LIVE.
- `scripts/check_mechanism_matrix.py`, `scripts/*` generally — nobody on the SCN track.
- `config/constants.py` outside the `VOLUNTARY_*` region: `DATACENTER_ZONE_SHARE` / `DATACENTER_ADDITIONS_MW` / `DEMAND_GROWTH_RATES` / `ELECTRIFICATION_LAYERS` are SCN-LOAD's re-derived values — READ them, never edit.
- `policy/federal_ces.py`, `policy/clean_tiers.py`, the `federal_ces_*` block — SCN-WS2a's landed regions; you consume their seam, you do not modify it.
- every `results/`, `frontend/data/hindcast/`, `frontend/data/forecast/` sidecar — you register nothing (no solve).

THE PLAN §7 BODY, VERBATIM (split only: the (WS-3c) half is NOT yours — it is issued separately once you land):
(WS-3b) You are lane SCN-WS3b. DATA PROFILE: ercot. Build exactly the memo's signed design: policy/voluntary_demand.py (volume resolver, eligibility, WTP), the row on the shared row family (after WS-2a's coupling change), fields voluntary_clean_demand_path / voluntary_wtp_ceiling_usd_per_mwh / voluntary_eligible_fuels with forecast-only coercion and cache-optional at off, constants with citations, matrix row + six cells, trivial-first tests (binding: dual = clean-minus-dirty gap; ceiling: dual = WTP, escape = shortfall). Backcast keys byte-identical — list them. FINDING + scorecard.

RULINGS THAT SCOPE YOU: S1 (the axis is admissible as declared/forecast-only/publicly-anchored/DEFAULT-OFF; ffr-5b's null is preserved in REF — `off` must be BYTE-IDENTICAL to today's REF, and you prove it by cache key). S3 (levels: the memo's box-5 defaults, minus the two cells named above). S5 (Stage A-POLICY, which includes every VOL-* case, is HELD on the CCS seam — you build the cases; nobody solves them until the desk releases A-POLICY; your FINDING states this in §0). D-3c OPEN: build the memo §4.1 default (renewable-only, offshore wind included; nuclear/CCS only via the labelled `voluntary_eligible_fuels` override; credit all eligible units, no additionality mask in dispatch) and label it a RECOMMENDATION in the field docstring and the FINDING — never a ruled default. D-6 OPEN: build NO netting logic; the campaign reports both nettings at the report layer, and your FINDING names where that hook lives.

NO SOLVE. This is a build lane: trivial-first LP tests (1 gen / 1 zone / 24 h, then the two named cases) and the full fast tier are your only LP. If you believe a solve is needed to prove something, STOP and route it to SCN-WS3c's PRECOMMIT via the desk. Rule 29's PRECOMMIT therefore does not apply to you; rule 29(c) does — no bundle of yours may exist on main.

CONSTANT-FAMILY DECLARATION (desk standing change, r#9): your volume construction consumes `DATACENTER_ADDITIONS_MW` (the DC block energy per ISO-year) and `DEMAND_GROWTH_RATES` (the non-DC load base), both re-derived by SCN-LOAD on 2026-09-06 from the curated `load-forecast` datatype. State in your FINDING §1, as a table: each constant family you read, the commit it was read at, and the sign of its effect on `voluntary_mwh` — so a later intake's blast radius on the voluntary volume is computable rather than discovered. Your OWN new `VOLUNTARY_*` family gets the same table row for its successors.

DELIVERABLES, in commit order: (1) the resolver + fields + coercion + cache-optional registration, with the trivial-first tests; (2) the row on the shared family + the runner arming + the dual plumbing, with the binding/ceiling tests; (3) the DC-linked volume helper + the `VOLUNTARY_*` constants with citations; (4) the four campaign YAML cases; (5) backcast byte-identity: the six keeper cache keys and every committed forecast key listed and measured unchanged at `off`, `mode="backcast"` coercion asserted by test; (6) `docs/handoffs/FINDING-scn-ws3b-<date>.md` — §0 bottom line (incl. the S5 hold on every VOL-* solve), §1 the constant-family table, §2 what was built vs the memo (every deviation named), §3 the gates and their measured values, §4 the two S3-unreached levels + the D-3c recommendation, for re-presentation, §5 the hook for D-6's dual reporting, §6 what SCN-WS3c inherits (its PRECOMMIT inputs: expected footprint, the four phase-0 regimes of memo Addendum A.3), §7 routed items, §8 files touched (each inside a region above); (7) the plan §5.1 Voluntary column rows 1/2/4/5 + the ledger-facing scorecard line; (8) LAST, after rebase: the matrix base row + one appended cell line per ISO (`U` in every ISO — nothing is tested until WS-3c), evidence = your FINDING path.

Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves (`voluntary_clean_demand_path` ships `off`); no solve of any kind outside the unit tests; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**r#16 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#16 | SCN-WS5A-POLICY-{ERCOT, NEISO, NYISO} — charter **v5**, launchable | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-<iso>-<4ch>` | \<iso\> | S5 + S8 (the pin `bdfb3095`) + S9–S12 | v4 with P1/P2 made concrete (the pin; in-place dirs), P4 counting RESOLVE's heavy legs, the PJM D67-ARM/D81 read |

**r#13 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#13 | SCN-WS5A-RESOLVE | **Opus** `claude-opus-5` | `claude/scn-ws5a-resolve-post-d77-k6ty` | `all` | **S8** (never executed by the load lane) + **S5** (the paired check) | the r#10 am.1 amendment re-cut as a standalone charter + the STATUS doc's cache recipe |
| r#13 | SCN-WS5A-POLICY-\<ISO\> ×6 — charter **v4** (not launched) | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-<iso>-<4ch>` | \<iso\> | S5 + S8 + S9–S12 | v3 with P1 → the RESOLVE PRECOMMIT, P3/P5 MET, the PJM cap clause corrected (SCN-CAP §5.1), key literals removed |

**SCN-WS5A-RESOLVE, whole:**

```
You are lane SCN-WS5A-RESOLVE. MODEL: Opus claude-opus-5 — pre-declared execution: 13 named re-solves at one named pin with the gates written below; nothing here is a judgment call. DATA PROFILE: all. Branch stem: claude/scn-ws5a-resolve-post-d77-k6ty.
Read CLAUDE.md freshly and in full (rules 1, 13, 21, 22, 28, 29, 30 all amended since 2026-09-05; rule 29(b) G-DRIFT and (c) DELETE BEFORE MERGE bind you; rule 12 concurrency binds you hard — you are the only lane that may be solving while you run PJM, MISO or CAISO); docs/forecast-development-plan-2026-07.md §2.1b (T1-F 2026–2030 needs no grant; never a year past 2030), §2.4, §7, §7.5; the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §3 WS-5 and §4; EVERY SCN-WS5A-LOAD document: PRECOMMIT-scn-ws5a-load-2026-09-06.md + its ADDENDUM (the freeze at `1cc45bb2` and why), STATUS-scn-ws5a-load-2026-09-06.md (its "re-solve set is 13 of 16" table and its CACHE blocker paragraph — read that twice), the six per-ISO FINDINGs and FINDING-scn-ws5a-load-synthesis-2026-09-06.md (§0, §5 honest-unfit, §8 the cost table you extend); FINDING-capx-d77-2026-09-06.md (§2 the fix, §3 NO KEY MOVES — the hazard you exist to defeat, §4 the identity gate you reproduce, §8.1 the stale-bundle census); FINDING-capx-d65b-2026-09-06.md (the CCS VOM adder re-key your pin also carries); FINDING-scn-fix2-2026-09-06.md §3 (the live forecast default key is `547053bdfccd4264`, not the older literal some charters carry — read `tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY` rather than any literal); the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#10 am.1 (ruling S8, verbatim), r#11, r#12, r#13 + §2 (S5, S8 bind you) + §4 (your file regions).

WHY YOU EXIST: ruling S8 (2026-09-06, card D-10: "Re-pin once post-D77 now") was issued as an amendment to the running load lane, which never received it and finished the campaign at the frozen pre-D77 pin `1cc45bb2` — correctly, by its own PRECOMMIT — leaving 13 of 16 legs carrying mis-rated `gas_cc_ccs` (NEISO 41.9 % of its 2030 CO2 level, NYISO 25.3 %, CAISO 16.2 %, PJM 0.42 %, MISO small; deltas mostly survive). You execute S8 as a standalone lane. ERCOT's three legs are the only clean ones (retrofit ledger NONE, measured) and are NOT re-solved.

THE PIN: `origin/main` at the moment you write your PRECOMMIT — at or after `fc583339` (D77) and `b1f77621` (D65-B); record the full sha as THE PIN in `docs/handoffs/PRECOMMIT-scn-ws5a-resolve-<date>.md`, which the six policy lanes read as their precondition P1. Never move it after the first solve. G-DRIFT `1cc45bb2..<pin>` hunk by hunk over the rule-29 window plus the forecast entry chain (`run_full_horizon.py`, `run_ces_leg.py`, `check_forecast_invariants.py`, `configs/`), every hunk INERT/LIVE for a `mode="forecast"` load leg with its reason — D77 and D65-B are LIVE by design on every ISO whose retrofit ledger is non-empty (all five you solve); the SCN-FIX2 carbon-form switch is INERT for REF/LOAD-HI/LOAD-HI-ORGANIC (no carbon override); everything else is yours to classify. Pushed BEFORE the first solve.

THE CACHE BLOCKER, and the recipe that defeats it (STATUS doc): D77 moves no cache key, so a re-solve at the same key HITS the pre-fix bundle and returns the numbers it was meant to replace. Therefore: (1) a NEW out-dir per ISO, `results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/`, and `run_full_horizon.py --out-dir` pointing there (it redirects `cache.CACHE_ROOT` to the out-dir — read `scripts/run_full_horizon.py` ~:736–750 and confirm before relying on it); (2) NEVER link or copy a pre-fix bundle into the new root (the WS-4c harness helper that "links arm bundles into the shared cache root" must not be used); (3) prove every re-solved leg is a fresh solve: its `run_config.json` `git_sha` equals the pin, its wall time is a solve's not a cache read's, and its 2028–2030 `gas_cc_ccs` emission rate is `measured host × 0.10`, not ~0.37. A leg whose numbers reproduce the pre-fix bundle to the digit is a CACHE HIT and a STOP — report it, never register it.

THE 13 LEGS, in rule-12 order: NEISO REF + LOAD-HI (≈11 min); NYISO REF + LOAD-HI + LOAD-HI-ORGANIC (≈61 min); then ONE AT A TIME: PJM REF + LOAD-HI (≈80 min), CAISO REF + LOAD-HI + LOAD-HI-ORGANIC (≈65 min), MISO REF + LOAD-HI + LOAD-HI-ORGANIC (≈80 min, peak RSS 9.65 GB — nothing else may solve). [r#14] The capx track is solving concurrently (D65-B-R's every-bare-key batch, D78-R, D81 — capx ledger r#49): before EACH of the PJM / CAISO / MISO legs, confirm with the owner that no capx per-plant solve is live and record the answer in your FINDING; never assume the slot. NEISO and NYISO may start at once. Rebase BETWEEN legs, never DURING one; HEAD GUARD `[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90` around every solve; years sequential.

THE PAIRED CHECK (ruling S5's, at model grain, on YOUR ISOs — D77 proved it on a bare NEISO t1f, you prove it on the campaign REFs): per re-solved REF, per retrofitted unit-year, `emission_rate_co2` = the host's measured CAMPD rate × (1 − 0.90) to rel. tol 1e-9 (D77 §4b gate 1); confinement — no non-converted unit's rate moves vs the pre-fix bundle; every zero-carbon class's generation identical to the pre-fix bundle in 2026–2027 (the pre-2028 inertness measured, not argued); and the 2030 CO2 level pre-fix vs post-fix per ISO beside the contamination each FINDING pre-declared (NEISO ≈5.60 Mt, NYISO ≈5.29, CAISO ≈5.04, PJM/MISO small). STOP gates, structural and STOP-only: (G1) the identity above; (G2) confinement; (G3) 2026–2027 zero-carbon identity; (G4) no non-target load-bearing invariant flips PASS → FAIL vs the pre-fix leg (a flip on I3/I7/I12 caused by re-ordered dispatch is reported with its cause, not a STOP — say which); (G5) the cache-hit test above. Nothing is gated on a residual. Pre-declare per ISO the expected sign and order of magnitude of the 2030 level change and whether the LOAD-HI delta moves (NEISO §2.3 predicted ≈6.3 % of its ΔCO2 rode on defective units; PJM's arms carry different CCS fleets so its delta does not cancel).

REGISTRATION: re-register each re-solved leg under the SAME run id as the pre-fix leg (the sidecar's `git_sha`, key provenance and out-dir change — say so per leg in the FINDING and in the sidecar's provenance block); DELETE the pre-fix NEISO/NYISO/PJM/MISO/CAISO slim artifacts under `results/scn-campaign-load-2026-09-06/<ISO>/` and their old sidecar bodies in the same commit as each re-registration (rule 26: a stale bundle at a valid key is a re-armable wrong answer; ERCOT's stay); declare every invariant FAIL each re-registered run carries in `frontend/data/hindcast/invariant-failures.json` IN THE SAME COMMIT (and DELETE any declared ident the re-solve no longer fails — a stale declaration also fails the audit; run `scripts/check_forecast_invariants.py --sidecar-dir` before every push, it is EXIT 0 on main today and must stay so). Re-run `report_scenario_deltas.py` per ISO and `collate_scenario_campaign.py` (its common-set repair landed, SCN-FIX1) on the repaired set.

DELIVERABLES: (1) PRECOMMIT (the pin, G-DRIFT, the cache recipe, the 13 legs, the gates, the predictions); (2) the legs, one commit per leg (artifacts + sidecar + declaration + old-artifact deletion); (3) `docs/handoffs/FINDING-scn-ws5a-resolve-<date>.md` — §0 bottom line, §1 the pin and G-DRIFT, §2 the paired check per ISO (the identity table, the confinement, the 2026–27 identity), §3 the 2030 level pre vs post per ISO and the LOAD-HI delta pre vs post, §4 gate verdicts, §5 the cache-hit proof per leg, §6 wall / RSS per solve-year — EXTEND the synthesis's §8 cost table with a "re-solve" row set and restate the campaign total, §7 routed, §8 files; (4) a SYNTHESIS ADDENDUM appended to FINDING-scn-ws5a-load-synthesis-2026-09-06.md (a dated section, never a rewrite) carrying the post-fix six-ISO rollup on the common ISO set, the corrected honest-unfit list, and the amended cost table for card D-5; (5) the plan §5.1 Load-HI rows 3 and 7 + the ledger §3 mirror, and the STATUS doc's campaign-state block updated (post-fix, 16/16 at two pins: ERCOT at `1cc45bb2` by G-DRIFT, the rest at THE PIN); (6) LAST, after rebase: the `datacenter_load_block` cell in the five re-solved ISOs' shards re-stamped with the post-fix evidence, one appended line each.
Push by pack size (CLAUDE.md Git & Pushing; a leg's slim artifacts + sidecar go over `git push`, small packs); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves; no solve outside this list and never past 2030; no new case; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**r#12 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#12 | SCN-FIX2 | **Opus** `claude-opus-5` | `claude/scn-fix2-carbon-form-relabel-v8kq` | `code` | **S3, S9, S10** | SCN-FIX1's r#11 / r#11 am.1 items 3–4, re-chartered whole |
| r#12 am.1 | SCN-CAP | **Fable** `claude-fable-5-1` | `claude/scn-cap-schedule-field-p2wd` | `neiso` | **S12** | not a plan §7 body — WS-1a §4.1(a)'s build, chartered from the ruling |
| r#12 am.2 | SCN-WS5A-POLICY-\<ISO\> ×6 — the combined charter, v3 | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-<iso>-<4ch>` | \<iso\> | S5 + S8 + S9/S10/S11 + **S12** | the r#11 template with the voluntary and cap cases folded in; the r#12 am.1 cap addendum WITHDRAWN (it had no session to attach to — the policy lanes were never launched, being gated on P1) |

**SCN-CAP, whole:**

```
You are lane SCN-CAP. MODEL: Fable claude-fable-5-1 — a new solve-affecting ScenarioConfig field on the cap-and-trade row, read before an existing scalar, with a backcast-inertness and a rule-28 matrix duty: structural, so the Fable side of the split. DATA PROFILE: neiso. Branch stem: claude/scn-cap-schedule-field-p2wd.
Read CLAUDE.md freshly and in full (rules 1, 13, 21, 22, 28, 29, 30 all amended since 2026-09-05; rule 28(c) is CI-enforced — a new ScenarioConfig field without its matrix row and six cells FAILS the PR); docs/forecast-development-plan-2026-07.md §7 and §7.5; the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §1 (definition of done, every item), §2.1 (the cap row's current state), §3.5 (`CAP-STATE-TIGHT`); FINDING-scn-ws1a-2026-09-05.md §4 IN FULL — §4.1 is the zero-LP census that proves a declining schedule cannot be expressed at HEAD (`mass_cap_tons` is a scalar, `scenarios.py:2943`; the published RGGI budget after 2025 falls back to the 11-state regional total, "wildly slack"), and §4.2 is the pre-declared case you make expressible; `src/market_sim/policy/cap_and_trade.py::_power_sector_cap` (lines ~389–405: explicit `mass_cap_tons` wins, else the published budget, else inert) — the ONE seam you extend; the matrix row `mass_cap_lp_row` in docs/codebase-site/data/mechanism-matrix.js and the six shards; the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#12 + r#12 am.1 + §2 (S2, S3, S12 bind you) + §4 (your file regions).

RULING S12 (2026-09-06), the level you build to: "Commit the 80 % slope and build the field." The schedule is WS-1a §4.2's, verbatim: a linear decline to 20 % of the 2025 published per-state budget by 2050 — NYISO {2026: 23.16e6, 2030: 20.2e6, 2040: 12.8e6, 2050: 4.6e6}, NEISO {2026: 20.67e6, 2030: 18.0e6, 2040: 11.4e6, 2050: 4.1e6}, CAISO {2026: 30.5e6, 2030: 26.5e6, 2040: 16.5e6, 2050: 6.1e6} (CAISO anchored to the model's own REF-2026 CO2 because CARB publishes no power-sector budget — state that in the case comment, it is the one non-published anchor and it is disclosed, not hidden), metric tonnes, linear between knots. The level is the owner's; you build the field and write the case, you never adjust a number.

FILES YOU OWN: `src/market_sim/config/scenarios.py` — ONE new field `mass_cap_tons_by_year: dict[str, dict[int, float]] | None = None` placed contiguous with the `mass_cap_*` block (~:2941–2943), its docstring citing S12 and WS-1a §4.2, its backcast/hindcast coercion to `None` in `__post_init__` beside `mass_cap_tons`'s handling (the `datacenter_load_path` / `carbon_price_delta` pattern), and its registration in `_CACHE_KEY_OPTIONAL_FIELDS` at `None` (the frozen drop value; every existing key byte-identical — measure it). `src/market_sim/policy/cap_and_trade.py::_power_sector_cap` — read the schedule FIRST (per ISO, interpolate linearly between knots, hold the last knot flat after 2050, return None outside the ISO's keys so the existing scalar/published fallbacks keep their order), one composition point (rule 19). `configs/scenario_campaign_matrix.yaml` — the `CAP-STATE-TIGHT` case exactly as WS-1a §4.2 declares it (`mass_cap_enabled: true`, `mass_cap_program: co2`, `state_carbon_pricing: true`, `carbon_price_path: zero`, the three schedules) — it is a program-ISO case; on ERCOT/PJM/MISO the row is gated off by `CAP_AND_TRADE_PROGRAMS` and the case must be byte-identical to REF there (assert it). `tests/scoring/test_scenario_campaign_configs.py` (the pin), new `tests/unit/policy/test_mass_cap_schedule.py` (trivial-first: 1 gen / 1 zone / 24 h with a binding cap — the row dual is the allowance price and emissions equal the cap to 1e-6; a slack cap — dual 0; interpolation at a non-knot year; the fallback order unchanged when the field is None; backcast coercion). `docs/codebase-site/data/mechanism-matrix.js` — a NEW base row `mass_cap_schedule` (or extend `mass_cap_lp_row`'s def to name the field; choose one and say why) + one appended cell line in EVERY shard, LAST commit after `git fetch origin main` + rebase (rule 28(c); CI fails without it). `docs/codebase/05-policy.md` (one paragraph). `docs/handoffs/FINDING-scn-cap-<date>.md`.
FILES YOU MUST NOT TOUCH (owner, LIVE now): every other line of `scenarios.py` (capx D74 / D65-B / D78 and the owner's backcast lanes write it daily — keep your hunk to the one block + the two registration lines); `policy/carbon.py`, `policy/federal_ces.py`, `policy/voluntary_demand.py`, `model/lp/rows.py` (other lanes' landed regions; the cap row's LP construction is already built — you change what BUDGET it reads, never the row); `frontend/data/hindcast/**`, `results/**`, `scripts/**`; the campaign YAML's other cases (SCN-FIX2 holds the five carbon-form rows — rebase on it if it lands first; if both touch the same YAML the conflict is one case block each).

NO SOLVE beyond the unit tests. The case is solved by the three program-ISO policy lanes (SCN-WS5A-POLICY-CAISO/NYISO/NEISO) under their own PRECOMMIT once your field is on main — their precondition P5. Rule 29's PRECOMMIT does not apply to you; rule 29(c) does (no bundle of yours on main).

DELIVERABLES, in commit order: (1) the field + coercion + cache-optional registration + the backcast-inertness test; (2) `_power_sector_cap` reading the schedule first + the trivial-first LP tests; (3) the YAML case + pin + the byte-identical-on-non-program-ISOs assertion; (4) byte-identity measured: the six keeper backcast keys, the forecast default `e5ecd4105ada3e58`, and every committed forecast `run_config.json` on the changed branch (0 must move); (5) FINDING — §0 bottom line, §1 the field and its fallback order (a table: schedule → scalar → published → inert), §2 the case with the three schedules and the CAISO anchor disclosure, §3 the resolved budget per ISO-year 2026–2030 vs the committed REF CO2 trajectory (so the policy lanes know in advance where the row binds — WS-1a §4.1's table, redone against the post-D77 REFs once WS-5A's re-solves land, otherwise the pre-fix ones with that said), §4 the key measurements, §5 routed, §6 files; (6) `docs/codebase/05-policy.md`; (7) LAST after rebase: the matrix row + six cells (`U` everywhere — nothing is tested until the policy lanes solve it), evidence = your FINDING path.
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back (`scenarios.py`, `cap_and_trade.py`, the YAML qualify); no CI workflows; no default moves (the field ships `None`); no solve outside the unit tests; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**SCN-FIX2, whole:**

```
You are lane SCN-FIX2. MODEL: Opus claude-opus-5 — pre-declared execution of two records edits already specified to the line; nothing here is a judgment call. DATA PROFILE: code. Branch stem: claude/scn-fix2-carbon-form-relabel-v8kq.
Read CLAUDE.md freshly and in full (rules 1, 13, 21, 22, 29, 30 all amended since the SCN charters were written — rule 30 twice on 2026-09-06); the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §3.5 (the case set; note (iii) — the carbon ladder's FORM is the RFF path per ruling S3, and the delta knots {15, 25, 50} were a desk stand-in "until SCN-WS1c lands S2's floor", which it did on 2026-09-06); FINDING-scn-ws1c-2026-09-06.md (the floor); FINDING-scn-ws1b-2026-09-06.md §1–§2 (the path measured: $0 in 2026 everywhere, +$3.75/t at 2027 on ERCOT/PJM/MISO, exactly inert on CAISO/NYISO/NEISO); FINDING-scn-ws3b-2026-09-06.md §4 (the two levels and the eligible-set default it shipped as placeholders / a recommendation); FINDING-scn-levels-2026-09-06.md (the precedent: a label change with zero numbers moved, measured by cache key); the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#11, r#11 am.1, r#12 + §2 (S3, S9, S10, S11 bind you) + §4 (your file regions). SCN-FIX1 landed its items 1–2 (declarations, collate repair) on the r#10 charter before items 3–4 were issued; you are items 3–4, nothing more.

FILES YOU OWN: `configs/scenario_campaign_matrix.yaml` — the four carbon rows + ALL-CLEAN's carbon component ONLY; `tests/scoring/test_scenario_campaign_configs.py` — the pin on those five cases; `src/market_sim/config/constants.py` — the `VOLUNTARY_*` region, WORDS ONLY; `src/market_sim/config/scenarios.py` — the three `voluntary_*` field docstrings, WORDS ONLY; `docs/handoffs/FINDING-scn-fix2-<date>.md`.
FILES YOU MUST NOT TOUCH (owner, LIVE now): every other line of `scenarios.py` and `constants.py` (capx D74/D65-B/D78 and the owner's backcast lanes write them daily); `frontend/data/hindcast/**` (SCN-WS5A-LOAD is re-solving and registering; capx D65-B's batch and D80 write the sidecar dir and `invariant-failures.json`); `results/**`; `scripts/**`; the matrix shards (no mechanism changes here; `carbon_price_path` and `voluntary_clean_demand` already have rows).

DELIVERABLES, in commit order:
(1) The YAML form switch (ruling S3, plan §3.5 (iii)): `CARB-LO: {carbon_price_path: low}`, `CARB-MID: {carbon_price_path: mid}`, `CARB-HI: {carbon_price_path: high}`, `CARB-MID+LOAD-HI: {carbon_price_path: mid, demand_growth_path: high, datacenter_load_path: high}`, and `ALL-CLEAN`'s `carbon_price_delta: 25.0` → `carbon_price_path: mid` (its other four overrides untouched). Rewrite the YAML's interim-form comment block (its lines ~65–117 explain the stand-in) to state the committed form and cite S3 + WS-1c; delete the commented-out path block that becomes live. Update the test pin. Then MEASURE, not argue: the `--set`/case resolver yields for each of the five cases the per-year resolved carbon $/t on all six ISOs (ERCOT/PJM/MISO: 0 / 3.75 / 7.5 / 11.25 / 15 for mid; CAISO/NYISO/NEISO: identical to REF every year) — tabulate in the FINDING; and assert the six keeper backcast cache keys and the forecast default `e5ecd4105ada3e58` are byte-identical (a case override never touches a key; say so with the measurement).
(2) The relabel (rulings S9, S10): in `constants.py`'s `VOLUNTARY_*` region and the three `voluntary_*` docstrings, every "placeholder" / "illustrative" describing `f_commit` mid = 0.5 and the WTP ceiling = $4.5/MWh becomes "committed (owner ruling S9, 2026-09-06)", and the eligible-set default's "recommendation" becomes "committed (owner ruling S10, 2026-09-06)". Words only: no value, default, type or key moves — assert the same keys unchanged and `ruff check` + `ruff format --check` clean on the two files (two OTHER files are format-red on main — `scripts/run_calibration.py`, `src/market_sim/data/fuel/basis/miso.py` — not yours; name them, do not touch them).
(3) FINDING: §0 bottom line, §1 the resolved-carbon table per case × ISO × year, §2 the relabel diff (words only, listed), §3 the key measurements, §4 files touched. No plan §5.1 edit, no shard edit, no solve.
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back (`scenarios.py`, `constants.py`, the YAML, the test file all qualify); no CI workflows; no default moves and no value moves; no solve of any kind; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**r#11 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#11 | SCN-WS5A-POLICY-\<ISO\> ×6 | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-<iso>-<4ch>` | \<iso\> | **S5** (condition met by D77's identity gate) + **S8** (the pin) | plan §7 "WS-5" Stage A, **policy half only**, the VOL-*/combo/cap cases split out on the open cards |
| r#11 | SCN-FIX1 (re-issue) | **Opus** `claude-opus-5` | `claude/scn-fix1-records-collate-n3rt` (unchanged) | `code` | the Y-24 ratchet + the STATUS defect + plan §3.5 (iii) | the r#10 charter + item 3 (the carbon-form switch) |

**The SCN-WS5A-POLICY-<ISO> charter, whole — r#17 v6. SUPERSEDES v5, whose text is DELETED here rather than kept beside it (rule 26 `[R-DELETE]` in spirit: a stale charter that still reads is a re-armable wrong prompt).** v6 fixes the two defects SCN-WS5A-POLICY-ERCOT routed from its own phase 0 (§9 items 1–2 of `PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md`) — **P2's path** (RESOLVE re-solved to `…-r2/<ISO>/<CASE>/`, not in place) and **G7's ceiling literal** ($7.0/MWh on a `high` leg, not the $4.5 mid cell) — and carries **S14**'s P4 relaxation and PJM's newly-met P1. **ERCOT's session is CLOSED (owner, r#17). Its phase 0 is on main and must not be redone, so it is re-issued as the v6-RESUME charter in §5.3 — never this template**, which would order a finished phase 0 repeated. **ONE paste per ISO; substitute the ISO in the four marked places. LAUNCHABLE NOW for NEISO, NYISO, PJM; CAISO / MISO when their re-solved REF is on main (P1):**

```
You are lane SCN-WS5A-POLICY-<ISO>, one of six (ISO ∈ {ERCOT, NEISO, NYISO, PJM, CAISO, MISO}). MODEL: Opus claude-opus-5 — pre-declared execution of a committed case set on a committed pin; every gate is written down below. DATA PROFILE: <iso, lower-case>. Branch stem: claude/scn-ws5a-policy-<iso>-<4 random chars>.
Read CLAUDE.md freshly and in full — the rules that changed since the plan was written: rule 1 [R-STRUCT] carve-out, rule 13 [R-MEASURED] exception, rule 21 [R-DOF] R-AY xref, rule 22 [R-HOLDOUT] R-AZ registration re-check, rule 29 [R-SCREEN] clauses (b) G-DRIFT and (c) DELETE BEFORE MERGE, rule 30 [R-TOUCHPOINT-FOLD] with both 2026-09-06 amendments; docs/forecast-development-plan-2026-07.md (§2.1b — T1-F 2026–2030 is inside the 5-solve-year window, NO grant needed and NEVER a year past 2030; §2.4 incl. the data/clean prerequisite; §7; §7.5 — the forecast namespace only); the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §1, §3 WS-3 (the voluntary row's design and its probe gate, now yours per ISO), §3 WS-5 (Stage A + the Stage C outline), §3.5 (the case set; the CARB-* form is the RFF `carbon_price_path` ladder per ruling S3 — SCN-FIX1 lands that YAML switch), §4 (the caveats every leg carries), §7 WS-5; the memo docs/handoffs/voluntary-clean-demand-design-memo-2026-09-05.md §6 + Addendum A.3 (the voluntary structural gate and the four phase-0 regimes); the FINDINGs you build on: FINDING-scn-ws5a-load-<iso>-2026-09-06.md (your ISO's REF and its caveats — ERCOT's REF is in deep shortage, 127 TWh unserved by 2030, so ERCOT's price side is disclosure-only; NEISO/NYISO/PJM/MISO REFs carry gas_cc_ccs from 2028/2029), PRECOMMIT-scn-ws5a-load-2026-09-06.md + its ADDENDUMs (ADDENDUM 2 names THE PIN), FINDING-scn-ws1b-2026-09-06.md (the carbon axis measured: live from 2027 on ERCOT/PJM/MISO, EXACTLY INERT on CAISO/NYISO/NEISO under the S2 floor — so on a program ISO the three CARB-* legs are byte-identical to REF and are KILLED at phase 0, never solved; and the leakage duty §4), FINDING-scn-ws2a/ws2b (the CES rows; WS-2b's ladder is pre-D77 and superseded by your CES legs), FINDING-scn-ws3b-2026-09-06.md §4–§6 (the voluntary row as built, its committed levels, and the zero-LP regime finding: ERCOT 2026 is SLACK), FINDING-capx-d77-2026-09-06.md (the repaired CCS emission-rate seam and its §8.1 blast radius), FINDING-capx-d65b-2026-09-06.md (the CCS VOM adder re-key your pin carries); PRECOMMIT-scn-ws5a-resolve-2026-09-06.md (§0 THE PIN, §1 the G-DRIFT you inherit — for PJM, capx D67-ARM and D81 are LIVE at the pin on top of D77/D65-B, so PJM's REF carries the published adequacy requirement and the must-offer convention, and your PJM deltas are differences under those; §4 the cache recipe); docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md — THE FIRST POLICY LANE'S PHASE 0, and the template for yours: read its §1 (preconditions as a verdict table), §3.3 (the WTP ceiling), §4 (the zero-LP carbon and cap tables) and §9 (the two charter defects it caught, both already fixed in this v6 text — do not re-route them); the matrix + your ISO's shard (you stamp `federal_ces_target`, `federal_ces` premium, `carbon_price_path` and `voluntary_clean_demand` cells for your ISO, last commit); and the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#17 (+ r#10, r#10 am.1, r#11, r#11 am.1) + §2 (S2, S3, S5 — RELEASED at r#11 —, S8, S9, S10, S11, S12, S14 bind you) + §4 (your file regions).

RULINGS THAT SCOPE YOU: S2 — the federal carbon price is a FLOOR under a state program. S3 — the §3.5 levels are committed (CES premium {10, 20, 30}; CES target {2026: 0.55, 2035: 0.80, 2050: 1.00}, ACP $50; carbon = the RFF path ladder). S5 — Stage A-POLICY is RELEASED (capx D77's identity gate is the paired check). S8 — the campaign's pin is post-D77 and named by WS-5A ADDENDUM 2. S9 — the voluntary levels are `f_commit` mid = 0.5 and the WTP ceiling = $4.5/MWh (WS-3b's shipped values; SCN-FIX1 relabels them committed). S10 — the voluntary eligible set is the renewable-only default as built (wind, solar, offshore wind, geothermal; nuclear/CCS only via the labelled `voluntary_eligible_fuels` override, which no campaign case sets). S11 — a voluntary MWh COUNTS TOWARD the federal standard; every combined leg reports BOTH nettings side by side. S12 — `CAP-STATE-TIGHT`'s budget is WS-1a §4.2's linear decline to 20 % of the 2025 published per-state budget by 2050 (NYISO 23.16 → 4.6 Mt, NEISO 20.67 → 4.1, CAISO 30.5 → 6.1 on a disclosed REF-2026 anchor), carried by the schedule field `mass_cap_tons_by_year` that lane SCN-CAP builds. S14 — charter P4 is relaxed to rule 12's own ~2-concurrent cap (see P4).

PRECONDITIONS (verify with git log on origin/main; STOP and route if unmet):
(P1) MET for NEISO, NYISO and PJM on main, and for ERCOT by G-DRIFT: lane SCN-WS5A-RESOLVE's PRECOMMIT (`docs/handoffs/PRECOMMIT-scn-ws5a-resolve-2026-09-06.md`, #5214) names THE PIN = `bdfb3095e9fa0cd2bec3f4e843f320b42588c72b`; its legs 1–5 (#5221) report gate G1 (the emission-rate identity, 1e-9) PASS on the re-solved NEISO and NYISO REFs, **its leg 6 (`9ef06cf8`, #5238) reports ALL FIVE GATES PASS on the re-solved PJM REF** (G1 1/6/6 converted units to 1e-9; 2026/2027 reproduce the pre-fix bundle to the digit on CO2 and price), and its §2 measures ERCOT clean (0.00 TWh gas_cc_ccs in every year), so ERCOT's standing legs at `1cc45bb2` are the control by G-DRIFT. YOUR PIN IS `bdfb3095…` — never a newer one (capx D79's solve-surface fingerprint entered `cache_key()` AFTER the pin; you solve at the pin, and your keys are pre-fingerprint keys, which the pin records). **PJM only:** capx D67-ARM and D81 are LIVE at the pin through PJM's own `default_scenario_overrides`, and leg 6 measured that confound **INERT on the REF pair** — every capacity row identical in all five years, because PJM's REF sits at a −16 % reserve margin where the rate-capped backstop is clamped whichever requirement operand it tests; read `9ef06cf8`'s body before you attribute any PJM delta, and re-measure rather than inherit that finding on a case that moves the margin. For CAISO / MISO: P1 is met only when the RESOLVE lane's re-solved REF for your ISO is on main with G1 PASS in its leg commit or FINDING; until then do phase 0 and your PRECOMMIT and STOP before any solve.
(P2) **[v6 CORRECTION — v5 named the wrong path and would have sent you to a stale or absent REF.]** RESOLVE did **not** re-solve in place: each leg *renames* its slim artifacts out of the pre-fix tree, so **a re-solved ISO's REF is at `results/scn-campaign-load-2026-09-06-r2/<ISO>/REF/`** (NEISO, NYISO and PJM are there today; CAISO and MISO land there when their legs run). PRECOMMIT §4 item 1 declares that out-dir; §4.1 is about the **driver** (`run_ces_leg.py`, because `run_full_horizon.py`'s `--out-dir` cache redirect is unreachable from a campaign leg) and says nothing about the path — do not read one for the other. **ERCOT alone is at the un-suffixed `results/scn-campaign-load-2026-09-06/ERCOT/REF/`**, because it was never re-solved and never needed to be. The run id and the sidecar (`frontend/data/hindcast/<iso>-2026-2030-scn-campaign-load-2026-09-06-ref.json`) are unchanged either way. Verify the sidecar's `git_sha` = the pin before reusing it; if you find a REF only under the un-suffixed path for a re-solved ISO, that is the **pre-fix bundle RESOLVE exists to replace** — STOP and route. Never re-solve REF.
(P3) MET on main since SCN-FIX2 (`83f391b0`): CARB-LO/MID/HI read `carbon_price_path: low/mid/high` and ALL-CLEAN's carbon component `carbon_price_path: mid`. Verify by reading the YAML at your pin; if it has regressed, STOP and route.
(P5) MET on main since SCN-CAP (`89b0a9f4`, FINDING-scn-cap-2026-09-06.md): the field `mass_cap_tons_by_year` and the case `CAP-STATE-TIGHT` exist. Its §3 binding table (pre-D77 REFs): binds on NYISO and CAISO in all five years, SLACK on NEISO in all five (kill at phase 0 unless your post-D77 REF moves it — the thin margins that could flip are NYISO-2030 and CAISO-2026). PJM: the case is NOT byte-identical to REF there — PJM is in `CAP_AND_TRADE_PROGRAMS` (its partial RGGI footprint), so an ISO absent from the schedule falls through to the published REGIONAL RGGI budget in 2027–2030 (SCN-CAP §5 item 1); the PJM lane runs the phase-0 binding test and expects SLACK (kill), and reports the fallthrough it measured. ERCOT / MISO: no program, byte-identical to REF, not solved.
(P4) **[v6, ruling S14 — the stricter one-solve reading is RETIRED; rule 12's own text governs.]** Rule 12 concurrency: **≤ 2 SCN-track solves at once**, counting SCN-WS5A-RESOLVE's legs and every policy lane, and **not while the capx track is mid-solve** — the owner sequences that half, because only the owner sees both tracks. Two SCN solves may run concurrently **only on different ISOs**; two per-plant multi-zone LPs on the same ISO never. Measured peaks from the ERCOT lane, for sizing: MISO 9.65 GB, CAISO 4.87 GB, ERCOT 4.2 GB on a 15 GB box — so pair a heavy ISO with a light one, never two heavy ones. Desk launch order: ERCOT and NEISO first (both cheap), then NYISO, then PJM, CAISO, MISO. **If you are the second SCN solve, say so in your PRECOMMIT and name the lane you are running beside**; if you cannot establish what else is solving, hold and ask rather than assume the slot is free.

YOUR CASES (every one a one- or two-field override on the committed YAML; nothing else): CARB-LO, CARB-MID, CARB-HI, CES-P10, CES-P20, CES-P30, CES-T80, CARB-MID+LOAD-HI (LOAD-HI is WS-5A's committed leg at the pin — reuse it as the pairing base), VOL-MID, VOL-HI, CES-P20+VOL-HI, ALL-CLEAN, and CAP-STATE-TIGHT on CAISO / NYISO / NEISO / PJM under P5 (ERCOT / MISO: no program, byte-identical to REF, not solved). Never add a case on your own.

PHASE 0 (zero LP, before the PRECOMMIT): for every case, the resolved-input delta vs REF at the pin — the resolved carbon $/t per year (the S2 floor: on CAISO/NYISO/NEISO every CARB-* leg resolves identically to REF in every year and is KILLED here, not solved; on ERCOT/PJM/MISO it is $0 in 2026 and live from 2027), the CES premium / target row presence, the voluntary volume V(year) at `mid` and `high`, and the case's cache key. For the voluntary legs, the memo Addendum A.3 / WS-3b §6 regime test per year — eligible generation at REF vs V(year): regime (i) SLACK (eligible ≥ V in every year) means the row cannot bind and the leg is byte-identical to REF — KILL it and say so with the two numbers per year (WS-3b measured ERCOT 2026 slack: ~197 TWh eligible vs ~76 / ~115 TWh at mid / high); a voluntary leg solves only where the row binds in at least one year, and the regime per year goes in the PRECOMMIT. For CAP-STATE-TIGHT (program ISOs): the resolved budget per year (SCN-CAP's FINDING §3) against your ISO's REF CO2 at the pin — where the budget exceeds REF's CO2 in every year the row is slack, the case is byte-identical to REF and is KILLED; where it binds in at least one year, it solves. A case whose resolved inputs equal REF's in every year is byte-identical and is never solved (rule 29 clause 0). Then G-DRIFT `<WS-5A pin>..HEAD` if HEAD has moved past the pin — you solve at the PIN regardless; the audit is for the record.

PRECOMMIT (pushed before the first solve, `docs/handoffs/PRECOMMIT-scn-ws5a-policy-<iso>-<date>.md`): the pin; the cases that survive phase 0 with their keys; per case the expected sign and order of magnitude on CO2, price, clean share, gas_cc_ccs MW and (voluntary legs) the row's dual and escape MWh, from the WS-1b-r2 (carbon), WS-2a/2b (CES) and WS-3b §6 (voluntary) measured or pre-computed responses, never from the residual; the STOP gate, structural and STOP-only: (G1) the resolved-input premise reproduces at the pin; (G2) a REF-side precondition — your ISO's REF carries the adequacy state WS-5A measured (unserved, reserve margin, I3/I7/I12) and you say which cases are price-side disclosure-only because of it (desk standing change #2: a broken REF fails the premise, never passes the delta); (G3) footprint confinement — a carbon case moves fossil rows and imports only, a CES case moves eligible/ineligible shares and the CES dual, a voluntary case moves eligible-class rows, thermal rows and the escape column only, every zero-carbon class row otherwise identical; (G4) the CES-T80 dual identity (escape regime: dual = ACP exactly where the target is unmet; interior otherwise); (G5) no non-target load-bearing invariant flips PASS → FAIL vs REF; (G6) no unserved energy appears in an arm where REF has none; (G7) **[v6 CORRECTION — v5 named the mid cell as if it bounded every arm.]** where the voluntary row binds, its dual is positive and ≤ **that arm's own** WTP ceiling, read from `VOLUNTARY_WTP_CEILING_USD_PER_MWH[path]`: **$7.0/MWh on every `high` leg (`VOL-HI`, `CES-P20+VOL-HI`, `ALL-CLEAN`) and $4.5/MWh on `VOL-MID` alone**; where it escapes, dual = that ceiling exactly and escape MWh = the shortfall. S9's committed level is untouched — $4.5 is the mid cell, and v5 quoted the wrong one of two committed cells; (G8) curtailment of eligible resources falls before thermal dispatch changes (the first MWh a REC buyer pays for is one that was dumped); (G9) on CES-P20+VOL-HI and ALL-CLEAN, the two nettings are BOTH reported (counts-toward as the headline, additional beside it) with the CES dual under each — never one alone; (G10, CAP-STATE-TIGHT) in every binding year emissions equal the budget to 1e-6 and the row dual `co2_cap_price` is positive, and in a slack year the dual is 0 exactly; (G11, CAP-STATE-TIGHT) `carbon_price_path: zero` resolves to the STATE program adder only (never a federal price) and the row REPLACES the adder where active (`state_carbon_pricing: true`) — one instrument at a time, never both; (G12, CAP-STATE-TIGHT) footprint as a carbon case, and the dual is reported beside the adder path's exogenous price in the same year — the price-vs-quantity comparison the case exists for. Nothing is gated on whether a residual moved. The constant families you consume (carbon paths, CES levels, the `VOLUNTARY_*` anchors, the load constants through LOAD-HI and the DC block) with the commit they were read at — desk standing change #1.

SOLVE: `run_full_horizon.py` / `run_ces_leg.py` per case at the pin, 2026–2030, years sequential, HEAD GUARD `[ "$(git rev-parse HEAD)" = "$H0" ] || exit 90` around every solve, rebase BETWEEN legs never DURING one. Register every leg (kind `scenario`, campaign `scn-campaign-policy-2026-09-06`, one run id per (ISO, case)) and DECLARE every invariant FAIL the registered run carries in `frontend/data/hindcast/invariant-failures.json` IN THE SAME COMMIT (its `how_to_update`; the audit CI job is red today on undeclared SCN runs — you add none). `report_scenario_deltas.py` per case vs REF with `import_co2_mt_reported` beside `emissions_mt` in every table (the WS-0 leakage duty; on NYISO/NEISO the import line is 25–41 % of the in-ISO level, on CAISO the import node pays carbon and books 0.0). Re-run the FC-6 paired battery on your REF/CARB-MID pair where CARB-MID is live. Slim artifacts only (the campaign gitignore block WS-5A committed); no bundle parquet beyond `bundle/`.

DELIVERABLES: (1) PRECOMMIT; (2) legs + registrations + declarations, one commit per case; (3) `docs/handoffs/FINDING-scn-ws5a-policy-<iso>-<date>.md` — §0 bottom line, §1 phase 0 (killed cases named with the identity or the slack regime that killed them), §2 per-case deltas with the import line beside every CO2 number and both nettings on the combined legs, §3 gate verdicts G1–G12, §4 the deployment response (retirements / entry / retrofits vs REF — the campaign's first policy-side deployment reading), §5 your own predictions scored at full magnitude, §6 wall / RSS per solve-year (the D-5 cost table's input), §7 routed, §8 files; (4) the plan §5.1 Carbon / CES-premium / CES-target / Voluntary rows 3 and 7 for your ISO and the ledger §3 mirror; (5) LAST, after rebase: your ISO's cells in its shard — `federal_ces_target`, the CES premium row, `carbon_price_path`, `voluntary_clean_demand`, and on a program ISO the mass-cap row — one appended line each, U → K/R/I with the evidence.
KEY LITERALS: never carry one — read `tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY` (the live forecast default is `547053bdfccd4264` at r#13; the `e5ecd4105ada3e58` some earlier charters cite is pre-D60 and stale).
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves; no solve outside your PRECOMMIT and never past 2030; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

### 5.2 r#17 issuance — three policy lanes under v6, and the ERCOT release note

| refresh | lane | model (id) | branch stem issued | **branch realized** | data profile | released by | body used |
|---|---|---|---|---|---|---|---|
| r#16 | SCN-WS5A-POLICY-ERCOT | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-ercot-<4ch>` | `claude/scn-ws5a-policy-21mq1y` (PR #5252) — **STEM BURNED** | `ercot` | **S5** + **S8** | charter **v5**; both v5 defects self-corrected in the lane's own PRECOMMIT §1/§3.3. Phase 0 complete and merged; **session CLOSED before its first solve** |
| r#17 | SCN-WS5A-POLICY-ERCOT (**RESUME**) | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-ercot-r2-<4ch>` | — | `ercot` | **S14** (the slot) | **v6-RESUME, §5.3** — not the v6 template: a resumption standing on the committed PRECOMMIT, verify-don't-redo, 11 legs |
| r#17 | SCN-WS5A-POLICY-NEISO | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-neiso-<4ch>` | — | `neiso` | **S5** + **S8** | charter **v6** (v5 re-emitted with the two ERCOT-routed fixes + S14) |
| r#17 | SCN-WS5A-POLICY-NYISO | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-nyiso-<4ch>` | — | `nyiso` | **S5** + **S8** | charter **v6** |
| r#17 | SCN-WS5A-POLICY-PJM | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-pjm-<4ch>` | — | `pjm` | **S5** + **S8** + P1 met by RESOLVE leg 6 (`9ef06cf8`) | charter **v6** |

NEISO and NYISO were issued at r#16 and are **one refresh silent, not two** — not graded lost, and
the re-emission is under the SAME stems (unburned; nothing was ever pushed to them). Their v6 text
is not a "verbatim re-emission": standing change #3 says a charter change for an **unlaunched** lane
goes into its charter, which is exactly what v6 is.

### 5.4 r#18 issuance — CAISO + MISO on v6, and the S15 bracketing addendum to all six

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#18 | SCN-WS5A-POLICY-CAISO | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-caiso-<4ch>` | `caiso` | **S5** + **S8** + P1 met by RESOLVE-CAISO (3/3, `c6d7b786`) | charter **v6** + the S15 addendum |
| r#18 | SCN-WS5A-POLICY-MISO | **Opus** `claude-opus-5` | `claude/scn-ws5a-policy-miso-<4ch>` | `miso` | **S5** + **S8** + P1 met by RESOLVE-MISO (3/3, `a1204354`) | charter **v6** + the S15 addendum |
| r#18 | S15 BRACKETING ADDENDUM ×6 | — | pasted into each live lane | — | **S15** | the block below; ERCOT / NEISO / NYISO / PJM are verifiably running (commits this window), so it goes to them as an addendum (standing change #3); CAISO / MISO receive it beside their charter |

**The S15 bracketing addendum, whole. ONE paste per lane; substitute the ISO in the two marked places. ERCOT included — it is the unmasked control and its §1 measurement is what proves the control is a control:**

```
SCN-WS5A-POLICY-<ISO> — ADDENDUM (owner ruling S15, SCN-DESK r#18, 2026-09-07). ONE new leg. Nothing already declared changes.

WHY. Two lanes found the same seam independently. The ENTRY screen folds attribute prices as attr = max(effective_eac_price_for_tech(...), rps_credit_for_zone(...), _clean_credit_for_tech(...)) -- new_entry.py ~:1132-1143 -- and the RPS leg carries NO fuel gate. So wherever a state RPS row sits at its escape price, a federal CES premium BELOW that price adds exactly nothing to entry revenue. STATE_RPS_ACP is MISO 30, NYISO 40, PJM 45, CAISO 50, NEISO 50, and ERCOT is absent from the dict entirely. The campaign's committed CES premium ladder {10, 20, 30} sits under every one of those, the voluntary ceilings {$4.50, $7.00} sit under every one, and CES-T80's ACP $50 TIES EXACTLY on CAISO and NEISO. NEISO measured rps_dual = 50.0 in 5 of 5 years and got a byte-identical VOL-HI/VOL-MID pair; PJM's phase 0 recorded "PJM's $45 RPS ceiling dominates two chartered axes."

This is NOT a defect and nothing here changes the code. It is rule 19 [R-ONE-MECH]'s max() attribute doctrine working as designed, and it is economically correct: attribute revenue is a max, never a sum. The RETIREMENT screen's RPS leg IS fuel-gated to _RPS_ELIGIBLE_FUELS = {wind, solar} (retirements.py ~:3509-3516), so a premium paid to gas_cc_ccs or nuclear is not masked there -- which is exactly why your CES legs are not byte-identical, are not killable at phase 0, and still solve as chartered.

STEP 1 -- ZERO LP, AND IT MAY MAKE STEP 2 UNNECESSARY. From your own committed REF bundle at THE PIN, report rps_dual per year (all five). Then per year state whether the mask binds: it binds where the REF RPS dual is >= the CES dual your CES-P10/P20/P30 legs carry. Report the two numbers per year, not a verdict alone. If the mask does NOT bind in any year on your ISO -- your RPS row is interior rather than at escape, or your ISO has no RPS row at all (ERCOT) -- then say so, add NO leg, and you are done with this addendum: your existing ladder already discriminates and IS the unmasked reading the other ISOs are compared against.

STEP 2 -- ONLY where step 1 shows the mask binding: add ONE leg, CES-P60. Same two fields your CES-P10/P20/P30 legs set (federal_ces_enabled true, the premium), premium = 60.0. Nothing else. $60/MWh is ONE COMMON LEVEL FOR EVERY ISO, chosen because it clears the highest published ACP in the footprint ($50) with margin. It is identified from the published ACPs and NEVER from any residual, and it is deliberately not per-ISO: a level picked to clear your own ISO's ACP would be the per-ISO fitting rule 25 [R-ISO-SCOPE] forbids. Do not re-level it, do not add a second bracketing leg, do not tune it.

GATES for this leg, structural and STOP-only, added to the set you already declared:
(G-B1) the mask is actually cleared -- at $60 the entry fold's attr strictly exceeds REF's attr for at least one eligible tech-zone-year. Compute it from step 1's duals BEFORE solving; if it does not clear, the leg is pointless and you STOP and route rather than solving it.
(G-B2) footprint as a CES case: eligible/ineligible shares and the CES dual move; every zero-carbon class row otherwise as your G3 declares.
(G-B3) no non-target load-bearing invariant flips PASS -> FAIL vs REF.
A leg that clears G-B1 and STILL shows no entry response is a REPORTABLE FINDING, not a gate failure -- report it at full magnitude. That outcome is the whole reason this leg exists: it distinguishes "correctly masked" from "the CES row does not reach entry at all," and only one of those two is a model that works.

WHAT DOES NOT CHANGE. Ruling S3's committed levels are untouched -- this is a bracketing leg BESIDE the ladder, not a re-levelling of it. Every case, kill, key and gate in your PRECOMMIT stands. Your pin is unchanged. Do not re-run phase 0 for the legs you already declared.

RECORD IT: a dated ADDENDUM section on your own PRECOMMIT carrying step 1's per-year duals, the G-B1 arithmetic and the leg's key -- pushed BEFORE you solve it (rule 29 [R-SCREEN]) -- and a subsection in your FINDING reporting the threshold result beside the masked ladder, so a reader sees the null and the bracket together. If your ISO is unmasked and you add no leg, that IS your deliverable for this addendum and it still goes in the FINDING.
```

### 5.5 r#18 am.1 — charter v7: the coordinator/shard split (ruling S16)

**v7 = v6 + this addendum.** It is pasted to the four running lanes as an ADDENDUM and stapled to
CAISO's and MISO's v6 charter. It moves no case, key, kill or gate — only WHO SOLVES. The shard
template inside it is ERCOT's own `SUBLANE-…-solve-protocol` generalised, because that is the one
that already ran. **ONE paste per lane; substitute the ISO in the marked places.**

```
SCN-WS5A-POLICY-<ISO> — ADDENDUM (owner ruling S16, SCN-DESK r#18 am.1, 2026-09-07). YOU ARE NOW A COORDINATOR. You stop solving legs yourself and launch shard sessions that solve them in parallel.

OWNER INSTRUCTION, VERBATIM: "I don't want to run all of these in one session per iso though that's way too much compute and we have effectively unlimited ability to run lps in parallel so the per iso session should launch shards itself" + "Update those prompts accordingly to launch individual sessions for runs to target <1 hr of lp solve per session."

THIS IS CODIFICATION, NOT A NEW SCHEME. Three lanes already converged on it: ERCOT wrote docs/handoffs/SUBLANE-scn-ws5a-policy-ercot-solve-protocol-2026-09-06.md (groups G1-G4, each its own container, keys and run ids tabulated for the solver), PJM split into S2/S3/S4/S6, NYISO fanned nine legs across four containers. READ THE ERCOT SUBLANE PROTOCOL FIRST -- it is the template this addendum standardises, and your shard prompt is that document with your ISO's numbers in it.

WHAT YOU KEEP (nothing here moves to a shard): phase 0, the PRECOMMIT and any ADDENDUM, the case set, the cache keys, the kills, the STOP-gate definitions, gate SCORING, the FINDING, the plan §5.1 rows, the ledger §3 mirror, and your ISO's matrix shard cells. A shard NEVER writes a doc, never scores a gate, never touches the matrix, the plan or the desk ledger.

WHAT A SHARD DOES, AND ONLY THIS: solve its assigned cases at THE PIN -> register each leg -> declare that leg's invariant FAILs in the same commit -> report in its final chat message. It writes ONLY results/scn-campaign-policy-2026-09-06/<ISO>/<CASE>/, its bundle/report subdir, frontend/data/hindcast/<run id>.json, and lines in frontend/data/hindcast/invariant-failures.json.

SHARD SIZE IS DERIVED, NOT CHOSEN. From the Stage A-LOAD synthesis §8's own measured min/solve-year, at 5 solve-years per leg and a 60-minute LP budget:

  ISO    min/solve-yr   min/leg   LEGS PER SHARD
  NEISO      1.09          5.5         10
  ERCOT      1.30          6.5          9
  NYISO      4.06         20.3          2
  CAISO      4.33         21.7          2
  MISO       5.23         26.2          2
  PJM        7.90         39.5          1

Use YOUR ISO's row. PJM is 1 leg per shard and that is not conservatism: PJM's within-window profile is super-linear (6.5 / 2.3 / 4.7 / 14.0 / 20.9 min for 2026-2030, synthesis §8 note 1), so one PJM leg is ~48 min of real LP and a second would blow the budget. A shard also pays ~20 min of FIXED SETUP (hydrate + uv sync + regenerate_clean) which is wall, not LP -- so FILL each shard toward the budget and do not split below about half of it unless your surviving leg count forces it. Divide YOUR OWN surviving set (the cases that passed phase 0, plus the S15 CES-P60 leg wherever step 1 shows the mask binding); do not re-derive the case set and do not inherit another ISO's grouping.

RULE 12, READ PRECISELY -- do not over-read this in either direction. Rule 12's "cap at ~2 simultaneous runs for per-plant multi-zone LPs to stay within memory limits" is a PER-CONTAINER MEMORY constraint. Shards are separate containers with their own ~15 GB, so it does NOT compose across them and you may launch as many shards as you have legs. What is UNTOUCHED and still binds inside every shard: ONE solve at a time, and YEARS ALWAYS SEQUENTIAL within a leg. Never parallelise years. Ruling S14's <=2-concurrent cap governed solves sharing one box and is superseded in practice by sharding, not withdrawn.

HOW TO LAUNCH. Use mcp__Claude_Code_Remote__create_session, one call per shard, with the shard prompt below as `prompt`, model claude-opus-5, and a title naming the ISO and the group (e.g. "SCN-WS5A-POLICY-<ISO> shard G3"). Launch them ALL AT ONCE -- that is the point. Omit environment_id so each inherits yours. IF THAT TOOL IS NOT AVAILABLE TO YOU: do not improvise and do not solve them yourself. Emit every shard prompt as a separate fenced code block in your final chat message, say plainly that you could not launch them, and stop -- the owner will paste them.

THE SHARD PROMPT YOU EMIT. Fill every <angle-bracketed> field from your own committed PRECOMMIT; a shard must never have to look a key up:

  You are a SOLVER SHARD for lane SCN-WS5A-POLICY-<ISO>, group <G>. You are NOT a new lane and you make NO decisions: the phase 0, case set, keys, kills and gates are committed in docs/handoffs/PRECOMMIT-scn-ws5a-policy-<iso>-<date>.md (+ its ADDENDUMs) and belong to the parent lane. MODEL: Opus claude-opus-5. DATA PROFILE: <iso>. Branch: claude/scn-ws5a-policy-<iso>-solve-<G>-<4 random chars>.
  Read CLAUDE.md freshly and in full, and your parent's PRECOMMIT.
  YOUR CASES, in this order, with the key each MUST resolve to at THE PIN:
    <CASE>  key <key>  --label scn-campaign-policy-2026-09-06-<label>  run id <iso>-2026-2030-scn-campaign-policy-2026-09-06-<label>
    <...one line per case in your group...>
  SETUP, at THE PIN, before anything else:
    H0=bdfb3095e9fa0cd2bec3f4e843f320b42588c72b
    git fetch origin main && git checkout --detach $H0
    python3 scripts/hydrate_data.py --profile <iso>
    uv sync
    PYTHONPATH=. uv run python scripts/regenerate_clean.py    # data/clean is derived + gitignored; a fresh container has none
  PRE-SOLVE CHECKS, all must hold or you STOP and report -- never improvise:
    [ "$(git rev-parse HEAD)" = "$H0" ] and git status --porcelain empty;
    results/<ISO>/<key> does NOT already exist for any key in your group (a pre-existing dir is a CACHE HIT and is a STOP, not a shortcut);
    re-resolve each of your keys at the pin and assert it equals the value above -- a moved key means the pin or the resolve chain changed under you: STOP and report.
  SOLVE, one leg at a time, years sequential, HEAD guard around every leg:
    for CASE in <your cases>; do
      [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90
      MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
        uv run python scripts/run_ces_leg.py \
          --config configs/scenarios/<iso>_scenario_base_2026_2030.yaml \
          --matrix configs/scenario_campaign_matrix.yaml \
          --case "$CASE" --campaign scn-campaign-policy-2026-09-06 \
          --out-dir "results/scn-campaign-policy-2026-09-06/<ISO>/$CASE" \
          > "$SCRATCH/$CASE.log" 2>&1 || { echo "SOLVE FAILED $CASE"; exit 91; }
    done
  REGISTER each leg (kind scenario, campaign scn-campaign-policy-2026-09-06, the run id above) and DECLARE every invariant FAIL that leg carries in frontend/data/hindcast/invariant-failures.json IN THE SAME COMMIT (its how_to_update). The audit is EXIT 0 on main -- you add no undeclared run.
  NEVER: solve REF, LOAD-HI, LOAD-HI-ORGANIC, any case outside your group, or any year past 2030. Never edit src/, configs/, scripts/, .github/, the PRECOMMIT, the matrix shards, the plan or the desk ledger. Never create a CI workflow, move a default, add a ScenarioConfig field, or re-run phase 0. Never parallelise years within a leg.
  YOU WRITE ONLY: results/scn-campaign-policy-2026-09-06/<ISO>/<CASE>/, its bundle/report subdir, frontend/data/hindcast/<run id>.json, and lines in invariant-failures.json. No docs -- your report is your final chat message.
  REPORT, as your final message: per case the wall min and per-year marks, peak RSS, the resolved key, the run id, the declared FAIL keys, and headline CO2 / price / clean share vs REF. Do NOT score gates or draw conclusions -- the parent lane does that. If anything failed, say exactly which leg and at which year, and stop.
  Push by pack size (CLAUDE.md Git & Pushing); verify any pushed file >=300 lines by fetch-back.

AFTER THE SHARDS RETURN: you collect their reports, score YOUR gates (G1-G12 plus S15's G-B1..G-B3 if you ran CES-P60), write the FINDING, do the plan §5.1 rows and the ledger §3 mirror, and stamp your ISO's matrix cells LAST after rebase. A shard that reports a failure is YOUR problem to diagnose -- re-launch that one shard, never widen the others.

WHAT DOES NOT CHANGE. Every case, kill, key, gate and prediction in your PRECOMMIT stands. THE PIN is unchanged. Ruling S3's committed levels are untouched. Do not re-run phase 0. If you have already solved some legs in-session, KEEP them -- shard only what is left.
```

### 5.3 SCN-WS5A-POLICY-ERCOT — the v6-RESUME charter (owner: "ERCOT session closed reissue")

The r#17 release note is **WITHDRAWN unissued**: it addressed a live session, and the owner reports
the ERCOT session is **closed**. Standing change #3 therefore routes the change into a charter — but
**not** the v6 template, which would order a finished phase 0 redone. This is a **resumption**
charter: it stands on the lane's own committed PRECOMMIT (`06526c7d`, PR #5252) as prior work,
verifies rather than re-derives, and goes straight to the solve under S14. The old stem
`claude/scn-ws5a-policy-21mq1y` is **BURNED** (pushed and merged), so the resumption takes a new one.

**One defect found grading the PRECOMMIT by content, and it is load-bearing for the resumption.**
Its §2 case table carries **eleven** `**SOLVE**` rows, each with a distinct cache key, but the
sentence beneath it reads *"10 legs to solve, 50 solve-years"* and its §7 budget repeats *"10 legs ×
5 solve-years"*. The table is authoritative — the eleven keys are enumerated and distinct — and the
sentence is an off-by-one (the commit message's "10 legs survive, 2 killed" counts `CAP-STATE-TIGHT`
as killed against a 12-case denominator that never contained it; on the 13-case denominator that
does, 2 killed leaves 11). **The real budget is 11 legs / 55 solve-years.** This desk propagated the
"10" into §0, §1, §2 and the plan before catching it; corrected in the same commit. A resuming lane
that trusts the sentence over the table silently drops a leg.

```
You are lane SCN-WS5A-POLICY-ERCOT, RESUMING. MODEL: Opus claude-opus-5 — pre-declared execution of a case set that is already committed and gated; you are here to SOLVE it, not to re-derive it. DATA PROFILE: ercot. Branch stem: claude/scn-ws5a-policy-ercot-r2-<4 random chars> (the original stem claude/scn-ws5a-policy-21mq1y is BURNED — pushed and merged — never reuse it).

YOU ARE NOT A NEW LANE. A previous session of this lane did the whole zero-LP half and merged it. Read your own prior work FIRST and treat it as yours: docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md (commit 06526c7d, PR #5252). It is your PRECOMMIT, pushed before any LP exactly as rule 29 [R-SCREEN] requires. DO NOT re-run phase 0. DO NOT re-derive the case set, the keys, the volumes or the gates. DO NOT rewrite it; a dated ADDENDUM section is the only edit you may make to it.

WHAT IT ALREADY ESTABLISHED, and what you inherit unchanged:
- THE PIN = bdfb3095e9fa0cd2bec3f4e843f320b42588c72b. You solve at the pin, never a newer HEAD. capx D79's solve-surface fingerprint entered cache_key() AFTER the pin, so your keys are pre-fingerprint keys and the pin records that.
- §2 is your case table: eleven cases to SOLVE, each with its resolved override and its distinct key at the pin (CARB-LO, CARB-MID, CARB-HI, CES-P10, CES-P20, CES-P30, CES-T80, CARB-MID+LOAD-HI, VOL-HI, CES-P20+VOL-HI, ALL-CLEAN). Read the keys from that table; never retype one from memory or from any other document.
- Two cases are KILLED and STAY killed, on identities you proved at zero LP: VOL-MID (§3.2 — the row is slack in all five years, so REF's own optimum is feasible with ESC=0 at the same objective; dual 0, byte-identical) and CAP-STATE-TIGHT (§4.2 — CAP_AND_TRADE_PROGRAMS.get("ERCOT") is None and resolve_carbon_program returns before mass_cap_enabled is consulted, so no LP input differs). Do not solve either. Do not revisit either.
- REF is the control and is NOT re-solved: results/scn-campaign-load-2026-09-06/ERCOT/REF/, key 6e40769352a572ba as solved at 1cc45bb2, sidecar frontend/data/hindcast/ercot-2026-2030-scn-campaign-load-2026-09-06-ref.json. ERCOT is the ONE ISO whose REF is at that un-suffixed path — the other five were re-solved by SCN-WS5A-RESOLVE into results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/. Your §5 G-DRIFT establishes form 4 validity for ERCOT (0.00 TWh gas_cc_ccs in every year of all three legs, so D77/D65-B re-key ERCOT without moving an answer, and D67-ARM/D81 resolve None); that finding stands.
- LOAD-HI is the pairing base for CARB-MID+LOAD-HI and is NOT re-solved — the committed leg at 1cc45bb2, key 31cf71afda5c610d.

FOUR CHANGES SINCE YOUR PRECOMMIT, ALL IN YOUR FAVOUR. Nothing else moves.
(1) PRECONDITION P4 IS RULED AND YOUR FIRST SOLVE IS RELEASED. Owner ruling S14 (2026-09-06, desk card D-11): the charter's "ONE repo-wide solve while MISO/PJM/CAISO is solving" is RETIRED — it was stricter than CLAUDE.md rule 12, which caps concurrency at ~2 per-plant multi-zone runs. The governing rule is now: at most 2 SCN-track solves at once, on DIFFERENT ISOs, and not while the capx track is mid-solve. ERCOT (your measured 4.2 GB) against SCN-WS5A-RESOLVE's CAISO (4.87 GB) or MISO (9.65 GB) legs is inside that cap. Confirm with the owner that the capx track is idle before you start; name in your FINDING which lane you ran beside; if you cannot establish what else is solving, hold and ask rather than assume the slot is free.
(2) YOUR §9 ITEMS 1 AND 2 ARE ACCEPTED AND WERE EXECUTED BY THE DESK. Both were right and both were the desk's errors, recorded as such in ledger §0 r#17. The policy charter is re-cut as v6 with P2 pointing at results/scn-campaign-load-2026-09-06-r2/<ISO>/<CASE>/ and G7 bounded per arm. Your own §3.3 reading is now the charter's: G7's ceiling is $7.0/MWh on every high leg (VOL-HI, CES-P20+VOL-HI, ALL-CLEAN) and $4.5/MWh on VOL-MID alone, which is killed. Ruling S9's committed level is untouched — $4.5 is the mid cell. Score G7 against $7.0 for every leg you solve.
(3) YOUR OWN LEG COUNT IS OFF BY ONE, AND YOUR TABLE IS THE ONE THAT IS RIGHT. §2 says "10 legs to solve, 50 solve-years" and §7's budget says "10 legs × 5 solve-years", but §2's table carries ELEVEN **SOLVE** rows with eleven distinct keys. Solve all ELEVEN. The real budget is 11 legs / 55 solve-years, and your §7 wall-clock estimate should be re-scaled by 11/10 before you quote it. Record the correction in your ADDENDUM; it is a counting slip in the prose, not an error in the table, the keys or the kills.
(4) YOUR §9 ITEMS 3 AND 4 ARE LOGGED AS DESK RECORDS ITEMS AND ARE NOT YOURS. Do not touch the campaign YAML's stale ERCOT tail-regime prose (item 3). Item 4 — VOL-MID inert across the whole T1-F window, with D-3c's new-builds-only crediting leg being what would change that — is carried to card D-3c by the desk; state it in your FINDING §7 as already routed, and do not act on it.

BEFORE THE FIRST SOLVE, a cheap re-verification only — this is a check, not a redo. In one commit push docs/handoffs/PRECOMMIT-scn-ws5a-policy-ercot-2026-09-06.md ADDENDUM A: (a) re-resolve the eleven keys at the pin through the same chain your §2 used (matrix_configs → resolve_policy_bundle → set_caiso_fsno_partition(False) → apply_iso_scenario_defaults → cache_key) and assert each reproduces its committed value — if any key has moved, STOP and route, because the pin or the resolve chain has changed under you; (b) re-assert P3 by reading configs/scenario_campaign_matrix.yaml at the pin (CARB-LO/MID/HI → carbon_price_path low/mid/high; ALL-CLEAN → mid); (c) the leg-count correction from change (3) with the re-scaled budget; (d) the S14 slot statement naming the lane you run beside; (e) a G-DRIFT of pin..HEAD classifying every solve-path hunk INERT-for-ERCOT with its reason, or LIVE — your §5 form-4 argument is the baseline and you extend it, you do not rebuild it. Nothing in ADDENDUM A is gated on a residual and none of it may change a case, a level or a gate.

SOLVE: run_ces_leg.py per case at the pin, 2026–2030, years sequential, one leg at a time. Per-leg command exactly as SCN-WS5A-RESOLVE's PRECOMMIT §4.1 gives it, with the policy campaign's own out-dir:
  MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 uv run python scripts/run_ces_leg.py --config configs/scenarios/ercot_scenario_base_2026_2030.yaml --matrix configs/scenario_campaign_matrix.yaml --case <CASE> --campaign scn-campaign-policy-2026-09-06 --out-dir results/scn-campaign-policy-2026-09-06/ERCOT/<CASE>
HEAD GUARD [ "$(git rev-parse HEAD)" = "$H0" ] || exit 90 around every solve; rebase BETWEEN legs, never DURING one. Register every leg (kind `scenario`, campaign scn-campaign-policy-2026-09-06, one run id per (ISO, case)) and DECLARE every invariant FAIL the registered run carries in frontend/data/hindcast/invariant-failures.json IN THE SAME COMMIT (its how_to_update) — the audit reads EXIT 0 on main today and you add no undeclared run. Slim artifacts only (the campaign gitignore block SCN-WS5A-LOAD committed); no bundle parquet beyond bundle/. report_scenario_deltas.py per case vs REF with import_co2_mt_reported beside emissions_mt in every table (the WS-0 leakage duty; ERCOT has no import node, so that line reads 0.0 BY CONSTRUCTION and every ERCOT CO2 delta is an upper bound — say so beside each number, as WS-1b-r2 did). Re-run the FC-6 paired battery on your REF/CARB-MID pair.

SCORE THE GATES YOUR PRECOMMIT DECLARED, G1–G12, at full magnitude, and note that G2 binds hard here: ERCOT's REF is in deep adequacy shortage (127 TWh unserved by 2030, $4,438/MWh), so every ERCOT price delta is DISCLOSURE-ONLY and no price result of yours is campaign-grade. The CO2 and deployment sides are. Say which is which per case rather than reporting a price number that reads as a finding.

DELIVERABLES: (1) ADDENDUM A, pushed before the first solve; (2) eleven legs + registrations + declarations, one commit per case; (3) docs/handoffs/FINDING-scn-ws5a-policy-ercot-<date>.md — §0 bottom line, §1 the phase 0 you already did (cite your PRECOMMIT, summarise the two kills, do not re-derive), §2 per-case deltas with the leakage line beside every CO2 number and both nettings on CES-P20+VOL-HI and ALL-CLEAN (ruling S11: counts-toward as the headline, additional beside it), §3 gate verdicts G1–G12, §4 the deployment response (retirements / entry / retrofits vs REF — the campaign's first policy-side deployment reading, and ERCOT converts no CCS so the retrofit row is a null you state), §5 your PRECOMMIT's predictions scored at full magnitude including any that missed, §6 wall / RSS per solve-year (the D-5 cost table's input), §7 routed, §8 files; (4) the plan §5.1 Carbon / CES-premium / CES-target / Voluntary rows 3 and 7 for ERCOT and the ledger §3 mirror; (5) LAST, after rebase: the ERCOT shard's cells — federal_ces_target, the CES premium row, carbon_price_path, voluntary_clean_demand — one appended line each, U → K/R/I with the evidence.
KEY LITERALS: your eleven keys come from your own §2 table, read at the pin. For the forecast default, read tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY — never carry a key literal from prose.
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves; no solve outside your PRECOMMIT and never past 2030; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**SCN-FIX1, r#11 am.1 text, whole (supersedes r#10's and r#11's — item 4 added):**

```
You are lane SCN-FIX1 (r#11 am.1 text; supersedes the r#10 and r#11 texts, neither dispatched). MODEL: Opus claude-opus-5 — pre-declared execution: two zero-LP repairs whose shape is fully specified below; nothing here is a judgment call. DATA PROFILE: code. Branch stem: claude/scn-fix1-records-collate-n3rt.
Read CLAUDE.md freshly and in full — the rules that changed since the SCN charters were first written: rule 1 [R-STRUCT] carve-out, rule 13 [R-MEASURED] exception, rule 21 [R-DOF] R-AY xref, rule 22 [R-HOLDOUT] R-AZ registration re-check, rule 29 [R-SCREEN] clause (c), rule 30 [R-TOUCHPOINT-FOLD] and BOTH of its 2026-09-06 amendments (the Run Explorer's report is scores and charts only); docs/forecast-development-plan-2026-07.md §7 and §7.5 (forecast namespace only); the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §1 item 7 and §3 WS-0 (the collation tool is WS-0's deliverable G-E2); docs/handoffs/STATUS-scn-ws5a-load-2026-09-06.md "Routed defect" (the collate defect, measured: LOAD-HI-ORGANIC system-scope 2030 delta reported +5.462 Mt vs +18.830 Mt on the common {ERCOT, NYISO} set — a 71 % understatement equal to NEISO's REF level); frontend/data/hindcast/invariant-failures.json (its `purpose` and `how_to_update` keys — read them before editing); scripts/lib/invariant_ledger.py and scripts/check_forecast_invariants.py (the audit, CI job `forecast-invariant-artifacts`); the FINDINGs you cite: FINDING-scn-ws4c-2026-09-06.md, FINDING-scn-ws1b-2026-09-06.md (§3.3 the ERCOT 2027 adequacy collapse; §3.4/§3.6 PJM and MISO), FINDING-scn-ws5a-load-ercot-2026-09-06.md (§0: ERCOT REF unserved 0.38 → 127.2 TWh, I12 worse in every year); and the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#10 + §4 (your file regions).

PRECONDITIONS (verify; STOP if unmet): `uv run python scripts/check_forecast_invariants.py --sidecar-dir` exits 1 on origin/main with undeclared FAILs whose run ids contain `scn-` (22 at the r#11 pin — the 18 below plus caiso-2026-2027-scn-ws1-probe-{ref,carb} and pjm-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi}; re-run the audit at your pin and declare exactly what it prints for every `scn-` id: caiso-2026-2026-scn-ws4-probe-t0-{ref,load-hi}; ercot-2026-2026-scn-ws4-probe-t0-load-hi-organic; ercot-2026-2027-scn-ws1-probe-{ref,carb}; ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}; ercot-2026-2030-scn-ws4-probe-t1f-{ref,load-hi}; miso-2026-2026-scn-ws4-probe-t0-{ref,load-hi,load-hi-organic}; miso-2026-2027-scn-ws1-probe-{ref,carb}; pjm-2026-2026-scn-ws4-probe-t0-load-hi; pjm-2026-2027-scn-ws1-probe-{ref,carb}). The 8 non-`scn-` ids (d60-arm, golden3-d60, t1h-d45/d45r/d57/d62) are the capx track's — you do NOT declare them; name them in your FINDING as left for capx.

FILES YOU OWN: `configs/scenario_campaign_matrix.yaml` (the four carbon-form rows + ALL-CLEAN's carbon component ONLY), `src/market_sim/config/constants.py` REGION `VOLUNTARY_*` and the three `voluntary_*` docstrings in `config/scenarios.py` (WORDS ONLY, item 4) + `tests/scoring/test_scenario_campaign_configs.py` (their pin), `frontend/data/hindcast/invariant-failures.json` — APPEND keys under `declared_failures` for `scn-` run ids ONLY, one key per run, the ident list exactly as the audit prints it; never edit or delete an existing key. `scripts/collate_scenario_campaign.py` — the system-scope delta only. A new `tests/scoring/test_collate_scenario_campaign_common_set.py`. `docs/handoffs/FINDING-scn-fix1-<date>.md`.
FILES YOU MUST NOT TOUCH (owner, LIVE now): any `frontend/data/hindcast/*.json` sidecar (SCN-WS5A-LOAD and SCN-WS1b-r2 are registering runs RIGHT NOW; capx D60-R4/D63 hold the board files); `results/**`; `scripts/check_forecast_invariants.py` and `scripts/lib/invariant_ledger.py` (the audit track's, Y-24); `scripts/report_scenario_deltas.py` (WS-0's, unaffected); every `src/` file; the matrix shards (nothing here is a mechanism).

DELIVERABLES, in commit order:
(1) `invariant-failures.json`: the `scn-` keys, each with the finding it belongs to named in your FINDING §1 by ident — I3 (unserved/dump) on ERCOT = the forecast REF adequacy collapse (G-S4; FINDING-scn-ws1b §3.3, FINDING-scn-ws5a-load-ercot §0), I3 on MISO = FINDING-scn-ws4c / FINDING-scn-ws1b §3.6 as they report it, I12 (reserve margin) on ERCOT campaign legs = FINDING-scn-ws5a-load-ercot §0 item 4, I7 (reliability floor) on CAISO/MISO/PJM/ERCOT probes = as FINDING-scn-ws4c reports it. Every ident you declare must be one the audit prints for that id at your pin — no more, no fewer; a stale declaration also fails the checker. Re-run the audit: the `scn-` lines must be gone and the count of remaining lines must equal the capx set you named. Commit this FIRST and rebase before it (the file is written by three live lanes; one appended key per line keeps any conflict one line).
(2) `collate_scenario_campaign.py`: the system-scope row for a case computes its delta on `isos(case) ∩ isos(reference_case)`, labels the row with that intersection, and where the intersection is a strict subset of the reference's ISO set the row says so in its own column — a computable-looking number over mismatched systems is never emitted. Trivial-first test: three ISOs in REF, two in the case, hand-computed delta on the common pair; then reproduce the STATUS doc's measured numbers (+18.830 on the common set) from the committed `results/scn-campaign-load-2026-09-06/` artifacts as a regression test. No other behaviour of the tool changes; `report_scenario_deltas.py` is untouched.
(3) [ADDED r#11] `configs/scenario_campaign_matrix.yaml`: switch the three carbon cases and the pairing case to the S3-committed FORM — `CARB-LO/MID/HI: {carbon_price_path: low/mid/high}` and `CARB-MID+LOAD-HI: {carbon_price_path: mid, demand_growth_path: high, datacenter_load_path: high}` — replacing the `carbon_price_delta` {15, 25, 50} desk stand-in (plan §3.5 (iii); SCN-WS1c landed S2's floor on 2026-09-06 so the path is now meaningful; FINDING-scn-ws1b §1/§2 measured it: $0 in 2026 everywhere, live from 2027 on ERCOT/PJM/MISO, exactly inert on the program ISOs). Update `tests/scoring/test_scenario_campaign_configs.py`'s pin for those four cases (the one test file the YAML deliverable forces, as WS-3b recorded). No other case moves; `ALL-CLEAN`'s form is handled in item 4 (the voluntary cards were ruled at r#11 am.1). No solve.
(4) [ADDED r#11 am.1] Rulings S9/S10 relabel: in `src/market_sim/config/constants.py` (the `VOLUNTARY_*` region ONLY) and the three `voluntary_*` field docstrings in `config/scenarios.py`, the words that label `f_commit` mid = 0.5 and the WTP ceiling = $4.5/MWh "placeholder"/"illustrative" become "committed (owner ruling S9, 2026-09-06)" and the eligible-set default's "recommendation" becomes "committed (owner ruling S10, 2026-09-06)". Words only — no value moves, no default moves, no key moves (assert the six keeper keys and `e5ecd4105ada3e58` unchanged). Also `ALL-CLEAN` in the campaign YAML: `carbon_price_delta: 25.0` → `carbon_price_path: mid` (the form switch of item 3 now reaches it, the voluntary cards being ruled), with the test pin. These are the only `src/` lines you touch; the docstring edit is inside WS-3b's landed regions and nobody else's.
(5) FINDING: §0 bottom line, §1 the declaration table (id → idents → finding), §2 the collate repair with the before/after on the committed artifacts, §3 the 8 capx ids left undeclared and the Ruff red (`scripts/data/derive_caiso_offer_surface.py`, the owner's caiso-254 file — report, do not touch), §4 files touched. No plan §5.1 edit (WS-1b-r2's open PR #5101 holds those rows), no shard edit.
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves and no value moves; no solve of any kind; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**r#10 issuance.**

| refresh | lane | model (id) | branch stem issued | data profile | released by | body used |
|---|---|---|---|---|---|---|
| r#10 | SCN-FIX1 | **Opus** `claude-opus-5` | `claude/scn-fix1-records-collate-n3rt` | `code` | the Y-24 ratchet + the STATUS doc's routed defect | not a plan §7 body — a records + repair charter written at r#10 |
| r#10 am.1 | SCN-WS5A-LOAD **amendment** | *(the running lane)* | — | — | **S8** (card D-10, ruled "re-pin once post-D77 now") — ISSUED | an amendment to the WS-5 body, never a widening |

**SCN-FIX1, whole:**

```
You are lane SCN-FIX1. MODEL: Opus claude-opus-5 — pre-declared execution: two zero-LP repairs whose shape is fully specified below; nothing here is a judgment call. DATA PROFILE: code. Branch stem: claude/scn-fix1-records-collate-n3rt.
Read CLAUDE.md freshly and in full — the rules that changed since the SCN charters were first written: rule 1 [R-STRUCT] carve-out, rule 13 [R-MEASURED] exception, rule 21 [R-DOF] R-AY xref, rule 22 [R-HOLDOUT] R-AZ registration re-check, rule 29 [R-SCREEN] clause (c), rule 30 [R-TOUCHPOINT-FOLD] and BOTH of its 2026-09-06 amendments (the Run Explorer's report is scores and charts only); docs/forecast-development-plan-2026-07.md §7 and §7.5 (forecast namespace only); the plan docs/handoffs/forecast-scenario-readiness-plan-2026-09.md §1 item 7 and §3 WS-0 (the collation tool is WS-0's deliverable G-E2); docs/handoffs/STATUS-scn-ws5a-load-2026-09-06.md "Routed defect" (the collate defect, measured: LOAD-HI-ORGANIC system-scope 2030 delta reported +5.462 Mt vs +18.830 Mt on the common {ERCOT, NYISO} set — a 71 % understatement equal to NEISO's REF level); frontend/data/hindcast/invariant-failures.json (its `purpose` and `how_to_update` keys — read them before editing); scripts/lib/invariant_ledger.py and scripts/check_forecast_invariants.py (the audit, CI job `forecast-invariant-artifacts`); the FINDINGs you cite: FINDING-scn-ws4c-2026-09-06.md, FINDING-scn-ws1b-2026-09-06.md (§3.3 the ERCOT 2027 adequacy collapse; §3.4/§3.6 PJM and MISO), FINDING-scn-ws5a-load-ercot-2026-09-06.md (§0: ERCOT REF unserved 0.38 → 127.2 TWh, I12 worse in every year); and the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#10 + §4 (your file regions).

PRECONDITIONS (verify; STOP if unmet): `uv run python scripts/check_forecast_invariants.py --sidecar-dir` exits 1 on origin/main with undeclared FAILs whose run ids contain `scn-` (18 at the r#10 pin: caiso-2026-2026-scn-ws4-probe-t0-{ref,load-hi}; ercot-2026-2026-scn-ws4-probe-t0-load-hi-organic; ercot-2026-2027-scn-ws1-probe-{ref,carb}; ercot-2026-2030-scn-campaign-load-2026-09-06-{ref,load-hi,load-hi-organic}; ercot-2026-2030-scn-ws4-probe-t1f-{ref,load-hi}; miso-2026-2026-scn-ws4-probe-t0-{ref,load-hi,load-hi-organic}; miso-2026-2027-scn-ws1-probe-{ref,carb}; pjm-2026-2026-scn-ws4-probe-t0-load-hi; pjm-2026-2027-scn-ws1-probe-{ref,carb}). The 8 non-`scn-` ids (d60-arm, golden3-d60, t1h-d45/d45r/d57/d62) are the capx track's — you do NOT declare them; name them in your FINDING as left for capx.

FILES YOU OWN: `frontend/data/hindcast/invariant-failures.json` — APPEND keys under `declared_failures` for `scn-` run ids ONLY, one key per run, the ident list exactly as the audit prints it; never edit or delete an existing key. `scripts/collate_scenario_campaign.py` — the system-scope delta only. A new `tests/scoring/test_collate_scenario_campaign_common_set.py`. `docs/handoffs/FINDING-scn-fix1-<date>.md`.
FILES YOU MUST NOT TOUCH (owner, LIVE now): any `frontend/data/hindcast/*.json` sidecar (SCN-WS5A-LOAD and SCN-WS1b-r2 are registering runs RIGHT NOW; capx D60-R4/D63 hold the board files); `results/**`; `scripts/check_forecast_invariants.py` and `scripts/lib/invariant_ledger.py` (the audit track's, Y-24); `scripts/report_scenario_deltas.py` (WS-0's, unaffected); every `src/` file; the matrix shards (nothing here is a mechanism).

DELIVERABLES, in commit order:
(1) `invariant-failures.json`: the `scn-` keys, each with the finding it belongs to named in your FINDING §1 by ident — I3 (unserved/dump) on ERCOT = the forecast REF adequacy collapse (G-S4; FINDING-scn-ws1b §3.3, FINDING-scn-ws5a-load-ercot §0), I3 on MISO = FINDING-scn-ws4c / FINDING-scn-ws1b §3.6 as they report it, I12 (reserve margin) on ERCOT campaign legs = FINDING-scn-ws5a-load-ercot §0 item 4, I7 (reliability floor) on CAISO/MISO/PJM/ERCOT probes = as FINDING-scn-ws4c reports it. Every ident you declare must be one the audit prints for that id at your pin — no more, no fewer; a stale declaration also fails the checker. Re-run the audit: the `scn-` lines must be gone and the count of remaining lines must equal the capx set you named. Commit this FIRST and rebase before it (the file is written by three live lanes; one appended key per line keeps any conflict one line).
(2) `collate_scenario_campaign.py`: the system-scope row for a case computes its delta on `isos(case) ∩ isos(reference_case)`, labels the row with that intersection, and where the intersection is a strict subset of the reference's ISO set the row says so in its own column — a computable-looking number over mismatched systems is never emitted. Trivial-first test: three ISOs in REF, two in the case, hand-computed delta on the common pair; then reproduce the STATUS doc's measured numbers (+18.830 on the common set) from the committed `results/scn-campaign-load-2026-09-06/` artifacts as a regression test. No other behaviour of the tool changes; `report_scenario_deltas.py` is untouched.
(3) FINDING: §0 bottom line, §1 the declaration table (id → idents → finding), §2 the collate repair with the before/after on the committed artifacts, §3 the 8 capx ids left undeclared and the Ruff red (`scripts/data/derive_caiso_offer_surface.py`, the owner's caiso-254 file — report, do not touch), §4 files touched. No plan §5.1 edit (WS-1b-r2's open PR #5101 holds those rows), no shard edit.
Push by pack size (CLAUDE.md Git & Pushing); verify every pushed file ≥300 lines by fetch-back; no CI workflows; no default moves; no solve of any kind; if you must touch a file outside your regions, STOP and route to SCN-DESK in your FINDING.
```

**The SCN-WS5A-LOAD amendment, whole (ISSUED under S8):**

```
AMENDMENT to lane SCN-WS5A-LOAD (paste into the running session; issued by SCN-DESK r#10 am.1 under ruling S8 on card D-10). Read the desk ledger docs/handoffs/scenario-desk-ledger-2026-09.md §0 r#10 + r#10 am.1, PRECOMMIT-capx-d77-2026-09-06.md §2–§4 (the fix, the cache hazard, the screen design), and your own FINDING-scn-ws5a-load-neiso §2 and -nyiso §0 item 4.
WHAT CHANGED: capx D77 (`ae8dd2a0`, PR #5089) repaired the CCS emission-rate seam you measured — `campd_bins.apply_plant_emission_rates*` now composes `measured × (1 − gen.ccs_capture_fraction)`, the stamp `apply_ccs_retrofit` sets. D77 §3 pre-declares: NO cache key moves, so every forecast bundle whose horizon reaches 2028 and whose fleet carries a retrofitted unit is SILENTLY INVALIDATED at its own key — your NEISO REF/LOAD-HI (8,833 / 8,803 MW retrofitted) and NYISO REF/LOAD-HI/LOAD-HI-ORGANIC (6,475 MW) are exactly that set. Your ERCOT legs carry ZERO gas_cc_ccs (measured) and are unaffected; PJM and MISO carry no state carbon program, so the retrofit screen closes at carbon 0 (capx D50) and D77 is inert there — VERIFY that by reading the retrofit ledger of each leg you solve, do not assume it.
THE RULING (S8): re-pin ONCE, post-D77, and re-solve only the contaminated legs. Concretely, in this order:
(1) Finish PJM and MISO at the frozen pin `1cc45bb2` if a leg is mid-solve (rebase BETWEEN legs, never DURING one — capx doctrine §5.0e); confirm each PJM/MISO leg's retrofit ledger is empty and say so per leg.
(2) Re-pin to origin/main at or after `fc583339` (the D77 merge). Run G-DRIFT `1cc45bb2..<new pin>` hunk by hunk over the rule-29 window plus the forecast entry chain and classify every hunk INERT/LIVE for a `mode="forecast"` load leg with its reason, in a PRECOMMIT ADDENDUM 2 pushed BEFORE the first re-solve. D77 is LIVE by design for any ISO with a non-empty retrofit ledger and INERT by construction elsewhere; every other hunk is yours to classify.
(3) Re-solve NEISO REF + LOAD-HI (2 legs, ≈11 min) and NYISO REF + LOAD-HI + LOAD-HI-ORGANIC (3 legs) at the new pin. Solve CAISO's 3 legs at the new pin (they were never solved pre-fix). Do NOT re-solve ERCOT, PJM or MISO — state per ISO why the pre-fix leg stands (empty retrofit ledger = D77 inert by construction, which is the G-DRIFT verdict, not a hope).
(4) The re-solved NEISO REF is also the campaign's PAIRED CHECK for ruling S5's release condition: report, per retrofitted unit-year, `emission_rate_co2` post-fix vs the host's measured rate (the identity is `measured × 0.10` to rel. tol 1e-9 — D77 §4b gate 1) and the NEISO 2030 CO2 level pre-fix (13.37 Mt, of which you measured ≈5.60 Mt contaminated) vs post-fix. Report the LOAD-HI delta pre vs post as well; your §2.3 predicted ≈6.3 % of the 2030 ΔCO2 rode on defective units.
(5) Re-register the re-solved legs under the SAME run ids (the sidecar's git sha changes; say so in the FINDING), delete the pre-fix NEISO/NYISO slim artifacts and sidecars in the same commit (rule 26: a stale bundle at a valid key is a re-armable wrong answer), and declare any invariant FAIL each registered run carries in `frontend/data/hindcast/invariant-failures.json` IN THE SAME COMMIT as the registration (its `how_to_update`; CI job `forecast-invariant-artifacts` is red on 18 SCN runs today — SCN-FIX1 declares the backlog, you declare every run you register from now on).
(6) Then the synthesis exactly as chartered, with one added table: per ISO, the campaign pin the leg stands on and the G-DRIFT verdict that lets it stand. Present card D-5 with the measured cost table, including the re-solve cost.
Everything else in your charter and PRECOMMIT is unchanged. No new case, no default move, no solve outside this list.
```

**Realized-branch reconciliation (r#10):** SCN-WS3b's r#9 am.1 stem `claude/scn-ws3b3-voluntary-demand-q7mv` was realized as `claude/scn-ws3b-voluntary-demand-h59n9b`; the stem is burned.

**Burned stems, never to be reused:** `claude/scn-ws3b3-voluntary-demand-q7mv` (realized under another name), `claude/scn-ws3b-voluntary-demand-n5wq` and
`claude/scn-ws3b2-voluntary-demand-k8zp` (SCN-WS3b / -r2, never realized across three refreshes),
`claude/scn-ws1b-carbon-sixiso-h6rt` (SCN-WS1b, superseded by -r2), `claude/scn-ws4b-loadhi-adequacy-b2np`,
`claude/scn-ws4b2-loadhi-adequacy-x3mc` (superseded — the original lane landed),
`claude/scn-mxr-matrix-duty-repair-j5tv` (LOST at r#4), plus the r#3 withdrawals below.

**Withdrawn at r#3, never dispatched:** SCN-WS0-R (`claude/scn-ws0r-registration-t0-m4qk`) and
SCN-WS2a-R (`claude/scn-ws2ar-ces-postures-probe-w8dr`). Their stems are burned and must not be
reused; a future lane needing that scope takes a new stem.

**Branch stems are ADVISORY, not binding** (r#2): every r#1 lane was provisioned by the harness on
its own branch name. The stem's purpose — stopping a relaunch from colliding with an original — is
served by the realized-branch column above, which every future relaunch must check first.

### 5.1 Model assignment — the standing rule and the r#1 assignments

**The rule, in force for every SCN lane at every refresh.** Rule 27 `[R-PUSH]` second half: any
session whose scope writes core infrastructure — anything under `src/market_sim/`,
`scripts/run_*.py` / `scripts/score_*.py`, `CLAUDE.md`, `model-methodology-spec.md`, or
`.github/workflows/` — is **Opus or Fable, never Sonnet**. The desk charter tightens this to
**no Sonnet on any SCN lane at all**, docs-only lanes included, so rule 27 is never the binding
constraint here — the plan's own label is. Within Opus/Fable the split follows the director's
r#20 doctrine, restated at plan §3: **`[FABLE]` for structural / adjudication work** (a design
whose shape is still being decided, a semantics change, an argument against a standing ruling)
and **`[OPUS]` for pre-declared execution** (a charter whose deliverables and gates are already
written down and whose job is to carry them out exactly).

| lane | label | model id | why this side of the split |
|---|---|---|---|
| SCN-WS0 | `[OPUS]` | `claude-opus-5` | Execution. Six enumerated deliverables, each with its own commit and its own trivial-first test; the paired T0's gate is arithmetic (by-fuel CO2 sums to `emissions_mt`). Nothing here is a judgment call. Writes `src/` + `scripts/` → rule 27 binds. |
| SCN-WS1a | `[FABLE]` | `claude-fable-5-1` | Adjudication. It changes what an existing registered field *resolves to* on three ISOs, argues the D-1 evidence memo the owner rules on, and must prove byte-identity across every keeper key. Writes `src/` → rule 27 binds. |
| SCN-WS2a | `[FABLE]` | `claude-fable-5-1` | Structural. A new LP row family, a coupling relaxation (`rows.py:1346`) that a later lane inherits, two new fields with a mutual-exclusion guard, and three postures to document. Writes `src/` → rule 27 binds. |
| SCN-WS3a | `[FABLE]` | `claude-fable-5-1` | Pure adjudication — the memo argues, line by line, that a declared scenario axis is a different admissibility class from the driver `ffr-5b` ruled out. Docs-only, so rule 27's letter would permit Sonnet; **the charter forbids it**, and this is the least Sonnet-shaped task in the wave. |
| SCN-WS4a | `[OPUS]` | `claude-opus-5` | Execution. Transcribe published siting geography with citations, hold shares to 1.0, re-check one immateriality arithmetic, enumerate a gap list. Rule 14 provenance work with a fixed shape. Writes `config/constants.py` → rule 27 binds. |

**Queued lanes carry their labels forward** (assigned now so a relaunch cannot drift): SCN-WS1b
Opus, SCN-WS2b Opus, SCN-WS4b **Fable** (it is the adequacy *adjudication* — it pre-declares how
each ISO's high case is read, and pre-declaring a reading is the Fable half of plan §3 WS-4),
SCN-WS4c Opus, SCN-WS3b **Fable** (build-from-a-signed-design, but it is the first writer of a
new mechanism), SCN-WS3c Opus, SCN-WS5A-\<ISO\> ×6 + -SYNTH Opus.

**The desk itself.** The charter assigns **Fable** to SCN-DESK; this session is configured
`claude-opus-5` and the serving model may differ again. Recorded against interest — it is a
divergence from the charter, it affects only adjudication tone and not any lane's assignment,
and a successor desk session should be opened on Fable.

**Splits and gates applied to the plan's §7 bodies (never widenings):**
- WS-1a: plan item 1 is conditional on card D-1 reading FLOOR; unsigned → items 2–3 + the
  Phase-0 trajectory table + the D-1 evidence memo, then stop.
- WS-4: the plan's single §7 "WS-4" prompt is split three ways by the charter's wave plan —
  items 2+5 to **WS-4a** (wave 1), items 1+3 to **WS-4b** (wave 2, Fable), item 4 to **WS-4c**
  (wave 2, Opus) — because items 1 and 4 depend on WS-0's campaign YAML and harness, which do
  not exist yet.
- No other lane's body was edited.

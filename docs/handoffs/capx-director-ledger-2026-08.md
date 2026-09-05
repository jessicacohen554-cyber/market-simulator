# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization Program) track.
Maintained by the director session on branch `claude/capx-director-ledger`; one refresh = one
commit when anything changes. The director charters sessions and tracks state — it never runs
solves, never edits `src/market_sim/`, and never charters backcast-calibration work (that track
is the owner's own CAISO/ERCOT/MISO sessions, watched here for deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-09-05 (refresh #40) ·
**r#40 (HEAD `4d4dc6ce`):** **Q46 LANDS — NYISO → `2026-09-05-nyiso-192-astoria-panel` (NOT-YET, grade 6) and `complete` + `frontier` WITHDRAWN under the Q5 uniform rule; gate (a) FAIL; the validation-tier authorization lapses** → **T3-NYISO-GOLDEN HELD on its Amendment-1 precondition; Q45's premise has lapsed** (no re-authorization card until a CALIBRATED NYISO keeper returns) · **nyiso-194 KILLS both one-year screens** of the owner-named duct-burner tranche lever on frozen structural gates (rule 29 working as written; keeper unchanged) · **D60-R2 LAUNCHED AND RUNNING** — twin check clear, all 17 pinned keys re-resolve unmoved across the nyiso-192 merge, **Addendum D pushed before any row** with two blunt negatives pre-declared (MISO's FC-7 will NOT clear — five pre-batch MISO overrides carry no curated row and are outside Q37's limb; CAISO keeps its pre-existing `negative_renewable_offers` caveat) → queued-named **D63 (MISO/CAISO DOF-row identification)** · **rule 15 retention amended to KEEPER-ONLY** (G-1; owner ruling R-AQ card K) · the R-AE flip set CLEARED again (Y-10: five files formatted, two lints; ruff green at the pin), the branch-protection flip routed to the OWNER'S CLICK-PATH (Y-9: the API is proxy-refused and the MCP set has no protection tool; a path-filter gap on `docs/handoffs/FINDING-*.md` flagged) · caiso-252 (zero-LP): the C4 2025 cell is CC_REGULAR's DIURNAL error, the mirror of the import diurnal shape; the CT miss is ONE plant (Panoche) · gates 6/6 · parity 0 · ruff green (§0ak) ·
*(previous)* **Last refresh #39:**
**r#39 (HEAD `cf5425f7`):** **D60 legs 1–2 of 5 LAND** — `miso-t1f` re-solved on `b1a73a087064ffd8` (the ratio, not the gate, moves the board: I12 +4 pts/yr, the 2030 backstop stops buying 6.6 GW of gas_ct, FC-2 row 4 FAIL → CAVEAT; the sector gate moves NOTHING on exits — P18 VACUOUS, honestly graded; CCS a measured null) · `nyiso-t1f` re-solved, **P10 STOP FIRED**: PROMOTE → PROMOTE-WITH-CAVEATS on FC-7 ALONE because the two armed gates enter the DOF ledger unattested — the lane refused to author the rows after reading the result and routed it → **D60 Amendment 2 authorizes the Q37 pre-declared follow-up attestation** · Addenda B (GOLDEN-3 attestation assertions) and C (the `pjm-t1f` leg absorbed, key `09996eca` confirmed) pushed before their solves · **D60 finding's solve-independent §§ landed; caiso/pjm-t1f + GOLDEN-3 pending** · owner track: **CAISO → caiso-251-b1-nomargin — C3a FAIL → PASS in all three years** (the gas offer was carrying NEISO's functional form; C4 supporting FAIL opens; NOT-YET; a WRONG DOF count corrected against interest) · **MISO → miso-217-intermphys** (the `phys_*` coverage gap closed, 58.4 % of gas capacity; NOT-YET C3a-2025 alone) · miso-218 (owner-requested ×1.10 level scale: the premise held, the lane's decisive prediction was wrong, NOT a keeper by pre-commitment — rule 1/13) · **nyiso-192's UNMERGED branch carries an in-lane owner ruling to promote a NOT-YET arm and WITHDRAW NYISO's `complete` + `frontier` (Q5 uniform rule)** → T3-NYISO-GOLDEN Amendment 1 (precondition: the marker) · the OWNER-DIRECTED CLEANUP: `scripts/archive` deleted (292 files), 1,229 record-only probes, 18 non-keeper backcast bundles, 36 forecast sidecars + 109 hindcast dirs — **zero verdict keys lost, every `-pre-*` prior intact**; a run_config.json committed WITH CONFLICT MARKERS by the nyiso-192 registration repaired · **rule 29 clause (b): NO CONTROL SOLVES — the committed keeper is the control; G-DRIFT replaces them** · DOCS-B finalized; 2022 ERCOT/NYISO measured inputs extended (touchpoint prep, nothing spent) · audit v29/v30: R-AL..R-AO; the branch-protection flip STILL NOT LIVE; G2 not declared; the R-V keeper freeze on {ERCOT, NEISO, PJM} still in force · gate-(a) 6/6; parity 0; ruff red ×5 (§0aj) ·
*(previous)* **Last refresh #38:**
**r#38 (HEAD `aa86890e`):** **D57 LANDS AND IS PROMOTED IN-SESSION (Q44)** — the PJM clearing half puts the cleared position within −0.5 / −1.0 / −2.8 pts of the published BRA and the §3.5 identity holds in all eight screens; the price reads 1.5–5.7× published because the CT/ST/oil E&AS operand is ZERO (≥ 3.8 / 18.0 / 8.6 $/kW-yr per unit would land it); the JOINT PJM posture (D48 ×2 + clearing) armed via `_pjm_config` overrides, arm A = the bare `pjm-t1h`, D45-R at `-pre-d57`; composition reads worse (steam over-exits, coal retained) and rule 1 keeps it → **D61 (the E&AS operand, Phase 0) issued** · **D56-R2 LANDED** — NYISO frontier declared; all four instruments read {ERCOT, NEISO, NYISO, PJM} · **D60 = CHECKPOINT, STILL RUNNING (owner-confirmed)** — the flip commit (Q40/Q41/Q42; both pinned default keys advanced by design) and four zero-solve renames landed; the fifth (`pjm-t1f`) REVERSED on a fired STOP because D57's promotion moved PJM's bare t1f key → **§D60 Amendment 1 adds the pjm-t1f leg** (~28 min); the four re-solves + finding owed · **D58 RELEASED** (after D60) · **Q45 (C-14): the NYISO §2.1b campaign AUTHORIZED, dispatch after D60 lands → T3-NYISO-GOLDEN chartered** · owner acts recorded: **rule 29 `[R-SCREEN]`** (one-year screen before the full span; structural STOP gate only), the **site pruned to keepers only** + ERCOT's two configs registered as ONE run (`2026-09-05-ercot248-two-config-keeper`, every surface re-keyed by the lane), audit rulings R-AH…R-AK recorded by v28b · owner track: nyiso-192 (payload CHP add-back instrument repaired; Astoria merit-panel duplicate A/B-armed, unpromoted), miso-215/216/217 (phys_* coverage gap sized; anchor grain NO CHANGE; the arm built blind), caiso-250/251 (the STORAGE cell is caiso-168's object; hydro refuted; the fuel-coupling form pre-registered) · parity red on two in-flight checkpoints; ruff red ×2 (miso-217) (§0ai) ·
*(previous)* **Last refresh #37:**
**r#37 (HEAD `182aa74a`):** THE WHOLE r#36 WAVE LANDS IN TEN HOURS — **D56-R** (NYISO `complete` RE-DECLARED on nyiso-189; validation tier returns, nothing spent; frontier left pending C-10) · **D59** (the locality half built the way NYISO's spot market works — NYC/LI on their own published ICAP curves, §5.15.2 max — and on this record DECIDES NOTHING: the model's NYC census sits +0.7–0.8 GW above the Gold Book, so NYC reads 5–9 pts long and its curve pays BELOW NYCA; P9 one-of-three again; cell I; DO NOT ARM, self-executing) · **D50-R** (PJM 3,584.7 → 909.8 MW with STOP 1 fired-and-diagnosed as deferral; MISO 4,631 → 0 MW capacity-identical; blast radius priced at 1.1 h residual; ARM recommended) · **D53 LANDED AND ARMED FOR MISO BY IN-LANE OWNER INSTRUCTION** (the bare `miso-t1h` re-keyed to the gated leg, D46 preserved at `-pre-d53`; PJM untouched) · **D57 IN FLIGHT** (build + Phase-0 reproduction to 0.000 $/0.000 pt; arms pre-declared, not yet solved) · **FOUR CARDS RULED THIS SITTING: Q39 frontier BOTH · Q40 ARM D51's ratio · Q41 ARM BOTH D52 gates · Q42 ARM the CCS capex default + the 1.1 h re-measure**; Q43 records the D53 in-lane arming · six NEW ruff-format reds (D59 ×3, D53 ×1, nyiso-191 ×2) routed (§0ah.4) · ISSUED: D56-R2 (frontier records), D60 (the arming batch) (§0ah) ·
*(previous)* **Last refresh #36:**
**r#36 (HEAD `e75250c7`):** the r#35 wave LANDS — **D48 Ph.1** (landed BEFORE the r#35 pin; the r#35 desk graded it "running" — recorded against interest), **D51** (ratio 0.8546 → 0.8934, the 2024 double-netting closed to 1.5 pts; arming limb (c) fails by the LETTER, not the substance → card C-11; NEISO leg 7: Q30 has NO NEISO-side counter-example, C-7 closed), **D52** (NYISO positions +9.4/+5.2/+7.3 → −2.6/−1.8/−0.6 pts, LOYO 3/3, FC-3 byte-identical at the default; curve-ON probe P9 1-of-3 → curve stays OFF self-executing; the over-fire relocates to the 2025/26 vintage + the LOCALITY half → card C-12 + D59), **D54** (the PJM clearing-half DESIGN + zero-solve instrument: cleared position within 0.7/1.0/2.6 pts of published, price 1.7–5.5× because the CT/ST/oil E&AS operand is zero → D57 build issued), **D55** (defect real, repair exact, NO observable on the exhausted-floor recipe; zero stale goldens), **D50 = CHECKPOINT** (ERCOT + NEISO arms registered — ERCOT 0 conversions vs 2,741.8 MW; NEISO cap still binds under RGGI; the PJM arm, the blast radius and the FINDING the matrix cells already cite are OWED → D50-R) · **D53 IN FLIGHT** on its branch with all four arming limbs MET and an ARM recommendation (finding §6 carries two unfilled template tokens) · **D56 NEVER LAUNCHED and its target keeper MOVED** (nyiso-188 → `2026-09-05-nyiso-189-steam-identity`, CALIBRATED → CALIBRATED) → D56-R re-issued on nyiso-189; the audit board's Z-4 (R-AG / Q38 double ruling; the frontier leg) → card C-10 · owner track: **CAISO → caiso-246-b1-spot**, **MISO → miso-213-layering** (stamp NOT re-keyed — the ELEVENTH guard firing, re-keyed here under Q34; the r#35 `read_live_at` leaf repaired), **NYISO → nyiso-189** (re-keyed itself) · two orphaned CI reds measured: the caiso-245 roster miss REPAIRED here (one test-roster line, disclosed), the D51/D52 ruff-format red is FIXED ON D53's BRANCH and clears when it merges · ISSUED: D50-R, D56-R, D57, D58 (released-conditional on D53), D59 (§0ag) ·
*(previous)* **Last refresh #35:**
**r#35 (HEAD `a35c9f9b`):** four capx lanes running (D48 Ph.1, D50, D51, D52), none landed yet · **NYISO → `2026-09-04-nyiso-188-combined` — THE FIRST NYISO KEEPER TO READ `CALIBRATED`** (lone ledgered C3c; no marker requested by the lane) → **card C-9: re-declare NYISO `complete`** · MISO → `miso-210-clock` (the max-gen clock repair; NOT-YET C3a-2025 alone) — stamp NOT re-keyed, **standing duty executed (tenth firing)** · caiso-244 locates the CAISO import LEVEL object (the north-corridor firm block, zero LP) · re-derived queue: **three lanes unlocked and ISSUED — D53 (the SECTOR GATE, D32 C5/R3: the screen models a merchant decision 88–92 % of exiting MW never faced), D54 (the PJM clearing-half design, D45 §2.3 item 3, docs-only, code gated on D48), D55 (D32 R2+R4: the float-noise retention-key defect + the release-precision diagnostic)** (§0af) · **AMENDMENT 1: Q38 — NYISO `complete` RE-DECLARED on nyiso-188 via records lane D56 (issued)** ·
*(previous)* **Last refresh #34:**
**r#34 (HEAD `8f5cb32c`):** THE WHOLE r#33 WAVE LANDS — **D45-R CLOSES THE ONCE-ONLY CLEARING-HALF CHARTER** (PJM's $0 is a basis artifact at the market's cleared quantity; NYISO's latent curve-ON flip fires at +189 % and is a REQUIREMENT-BASIS + LOCALITY artifact, not a curve defect — DO NOT ARM, no PJM default moves; the six bare keys current; Stage 2 + Stage 3 CLOSED; PJM t1f measured 28 min, MISO 65 min) · **D49: ERCOT's CCS at carbon 0 is a CONSTRUCTION SEAM (capex flat per kW, credit ∝ host CO2) that also undoes D41 §4.3's zero-clearing at unit grain for PJM/MISO; the MISO exit under-build is NOT the D43 wall — it is the reserve POSITION netted twice (the 0.8546 ratio identified on a fleet still carrying the dated exits)** · D47 restores GOLDEN-3's FC-7 by a pre-declared attestation and finds two `-pre-d46` baselines carry more axes than recorded; D47b corrects the cost fields (D46's 7–10× was span-confounded) · D48 Phase 0 LANDED (fields default-off, BRA DR intake, PREDECL corrects D45 §2.2's 2–4 pts to 7–11 on a consistent basis), **Phase 1 RUNNING (owner-confirmed)** · D45-R's leg 7 (NEISO dates-OFF control) pre-declared but NOT RUN → card C-7 · owner track: NYISO promoted TWICE (nyiso-186 → 187, both re-keyed their stamps), CAISO → caiso-243 (**the F923 defect's root cause — `state` never passed to `Generator` — is EVERY plant-level ISO's**), audit v26 (flip set 5 of 6; path-filter trap closed) · **D50 / D51 / D52 ISSUED** (§0ae) · **AMENDMENT 1: Q36 leg 7 rides D51; Q37 rubric §5 gains the pre-declared follow-up-attestation limb (D51 records rider)** ·
*(previous)* **Last refresh #33:**
**r#33 (HEAD `b168260e`):** **D46 STAGE 1 LANDED IN FULL** (PRs #4661/#4668; 8/8 pre-declared cache keys realized; 13 hits / 6 misses graded) — **the fossil-dates flip RE-ROUTES exits rather than adding them, and the sign is per-ISO** (MISO recall 5/19 → 16/19 FAIL→PASS, the batch's one gate-leg improvement; NEISO recall 4/6 → 3/6 WORSE; ERCOT a data-coverage null that still worsened a board row) · **GOLDEN-3: the corrected D41 constants end NEISO's CCS wave nine years early** (83 → 60 conversions) · **the board's t1f cost estimates were 7–10× too high** (ERCOT 2.0 h → 11.8 min) — Stage 3 re-priced · **D45's owed half STILL absent** (§4–§9 placeholders; branch gone) → card C-4 · **CAISO promoted AGAIN (caiso-241) and skipped step 4 AGAIN — the seventh miss**; the gate-(a) guard is red at HEAD and R-AB's flip is blocked on exactly that stamp → card C-5 · owner track: caiso-242 killed its own arm and found a 2.8 GW / $736 per MWh fuel-cost data defect; miso-204 found the MISO C3a comparator is ONE HUB on a clock an hour off; nyiso-181b/183 locate the C1-2023 ST_GAS miss to ONE PLANT'S heat-rate basis (Ravenswood) · audit v24: fast tier red again, R-Z/R-AC lint executed (§0ad) · **AMENDMENT 1: THREE RULINGS — Q33 D45 is DEAD → D45-R issued, absorbing D46 Stage 2 AND Stage 3 (Q35, the re-measured price); Q34 a STANDING gate-(a) re-key duty for this desk — executed at once on caiso-241 (guard exit 0, R-AB unblocked)** · **AMENDMENT 3 (owner challenge "nothing else unlocked, or lazy?" — LAZY, against interest): FOUR unlocked items the sitting under-served — the NEISO dates-OFF paired control (7 min; decides whether Q30's default HURTS NEISO's own FC-3), the ERCOT CCS-at-carbon-0 diagnosis, the MISO exit-side margin decomposition on D46's own diagnostics dumps, and the PJM accreditation-devintage repair D45 §2.3 already identified with sources → D45-R amended, D47 amended, D48 + D49 ISSUED** ·
*(previous)* **Last refresh #32:**
**r#32 (HEAD `c73f78f5`):** NOTHING CAPX LANDED — **D44 + D45 show no branch, no PR, no commit** (relaunch protocol: dispatch status ASKED, both RE-EMITTED verbatim, not graded lost) · the owner's backcast track promoted **THREE keepers in one day** — CAISO → `2026-09-02-caiso-239-b1-stgas` (NOT-YET C3a alone; the caiso-238 object-2 premise FALSIFIED, repair relocated to the uncited 1.15 class literal), MISO → `2026-09-02-miso-201-stbasis` (NOT-YET C3a-2025 alone; ST-side capacity basis on the LP's own basis), NYISO → `2026-09-02-nyiso-177-vintage-matched` (owner-ruled override; NOT-YET, fail set WIDENED by C1-2023 ST_GAS) · **FOUND AGAINST THE RECORD: all three promotion PRs skipped the R-T gate-(a) re-key — `check_gate_a_provenance.py` FAILS on CAISO/MISO/NYISO** (verdicts unmoved; the at-source routing missed its first three tests) · the re-measure's stale set WIDENS (every CAISO/MISO/NYISO forecast bundle now sits on a superseded keeper) — pricing still deferred to D44's landing · queue otherwise unchanged (§0ac) · **AMENDMENT 1 (mid-sitting, HEAD `2b0b8796`): the owner was right — D44 LANDED (PR #4639, the default flipped, plus two pieces of plumbing that would have made it inert) and D45 is a CHECKPOINT (PJM L1 registered as the bare `pjm-t1h`; NYISO L2/L3 + PJM L4 + finding §4–§9 still owed); CAISO and MISO promoted AGAIN (caiso-240, miso-202) and skipped step 4 AGAIN — C-2's grant spent on those two (guard exit 0); audit v23 landed R-X/R-Y and G2 leg 2; the RE-MEASURE IS PRICED (card C-3)** · **AMENDMENT 2: C-3 RULED Q32 — STAGED (cheap set now, t1f tail later); D46 ISSUED (pack §D46); this desk's r#32 push merged as PR #4642** ·
*(previous)* **Last refresh #31:**
**r#31 (HEAD `68690427`):** ALL THREE r#30 lanes LAND — **D37: the post-wave years SCORE, armed positions within ±3.3 pts of the real FCAs (control +21.1), the P9 flip condition FAILS on its own terms (default stays off)** · **D42: recall 5/19 → 16/19, zero screen displacement → Q30 ARMS THE FOSSIL-DATES DEFAULT** · **D43: decision-inert — the discarded dispersion is dispersion the LP never priced** (CAISO cell I) · miso-200 promotes (NOT-YET C3a alone, smaller) · **Q31 funds both caiso-238 asks** · D44 (Q30 execution) + D45 (the once-only D6+R3 joint charter) issued (§0ab) ·
*(previous)* **Last refresh #30:**
**r#30 (HEAD `a5abe3fe`):** the four-lane wave lands whole AGAIN — D40 (Net ICR lever BUILT, +21.4 → −2.1 pts at the clean entry; **Q28: armed for D37 only**) · D41 (**the zero-carbon CCS wave STOPS at corrected values**) · D39 (**one term: the energy leg's DISPERSION, discarded by the shared zone-flat tail-free re-price**; REC duals exact at ACP; CAISO first) · D32 (floor selection **indistinguishable from random**; the one discriminating driver is filed retirement dates the fossil channel ignores → **Q29: the D42 A/B is chartered**) · a label-collision lane ("D33"-MISO-additions) graded by content · **D37/D42/D43 issued** (§0aa) ·
*(previous)* **Last refresh #29:**
**r#29 (HEAD `0a3d22c7`):** ALL FIVE re-emitted/issued lanes LAND (D31/D33/D30/D35/D38) — D31 swings the MISO exit residual to **−74.3 % UNDER on faithful inputs** (rule 14's expected signature, localized sharper than ever) · D33: the NEISO position is a **requirement-denominator VINTAGE artifact** (published Net ICRs already in-repo → D40) · D30: **DEFECT-CANDIDATE on two CCS fixed-cost legs, not 45Q** (→ D41) · D35: **FC-6 leaves the neiso-t3 FAIL set** (now CAVEAT; failing = FC-1..FC-4) · **UNLOCKED AND ISSUED: D32 · D40 · D41 · D39**; D37 held behind D40's arming; D6+R3 deliberately still queued (§0z) ·
*(previous)* **Last refresh #28:**
**r#28 (HEAD `1aa8ac14`):** D36 answers the storage question — **the ARBITRAGE leg is short in every year by $50–150/kW-yr; the RA leg is second-order and IS the D28/D33 position object** · T16-A lands outcome B — **NEISO's RPS is unreachable at every stack-built VRE volume** (REC dual at the $50 ACP ceiling in all 50 arm-years), battery row CAVEAT-measured · **MISO PROMOTES `2026-09-01-miso-198-oomlevel`** (no criterion status moves — structural improvement without gate movement) · D31/D33/D30 were NEVER DISPATCHED (owner-confirmed; prompts re-emitted) · D35 released, D38 issued (§0y) ·
*(previous)* **Last refresh #27:**
**r#27 (HEAD `a2e80dbf`):** GOLDEN-2 REGISTERED — verdict HOLD, **FC-7 PASSES (first on any golden)**, FC-6 FAIL on the NEW P2 only, storage entry survives arming as a −56.2 % divergence (720 MW iron-air, 2050 only); Q25 SPENT · D34 + D20 LANDED · T1.6 deleted under rule 26 and **Q27 re-points it to `entry_rate_limits`** · D36 issued; T16-A held for golden-close; D35/D37 named-queued (§0x) ·
*(previous)* **Last refresh #26:**
**HEAD at refresh:** `8462da22` — the nine-writer wave lands 7-of-9 with two clean mid-lane checkpoints (§0w.1); **D27 vindicates D17's arithmetic and refutes it as a remedy — coal ate all 14.7 GW** (§0w.1); CAISO promotes caiso-231 (§0w.5); the Q22/R-H duplication recorded AGAINST INTEREST (§0w.2); Q24 funds the MISO PRA/RBDC intake; D26-S/D31/D33 issued (§0w.4) · **Owner cards A/B/C SIGNED 2026-08-25; Q20–Q23 r#25; Q24 r#26** (§3)
**Handoff prompt for a successor director session:** `docs/handoffs/capx-director-handoff-2026-08-30.md` (rewritten whole at r#36; the ledger wins where they diverge)

---

## 0ak. Refresh #40 (2026-09-05, main HEAD `4d4dc6ce`) — the pending NYISO promotion lands and takes the marker with it; D60-R2 launches clean and pre-declares its own two negatives; the owner-named NYISO lever dies on its one-year screens; keeper-only retention becomes rule 15's text

**0. FIRST ACT.** Handoff claim (§0aj = r#39 + am.1/am.2) matched the top entry; this is r#40.
Delta `cf5425f7..4d4dc6ce`: 10 merges (#4817–#4826), 21:12Z → 21:42Z. My r#39 pushes merged
(#4820, #4821); branch deleted, recreated off `4d4dc6ce`. Gates: `audit_keepers` 0 ·
`check_gate_a_provenance` 0 (six rows; the NYISO row re-derived to FAIL by the promoting lane
itself, R-T honoured) · parity 0 · matrix 0 · goldens 0 (15 pruned-provenance, keeper-only by
rule now) · **ruff format AND lint GREEN** (Y-10 cleared the five reds + the F401).

**1. GRADED BY CONTENT — capx lanes:**
- **D60-R2 — LAUNCHED, RUNNING** (PR #4824, `f7aecae3` + `342c7593`): **STATE AT START — the
  twin check is CLEAR** (no `capx-d60r*` branch; the only "D60-R" commits are this desk's own
  issuance records); two owner-track merges landed under it (caiso-252's one-file PRECOMMIT;
  **the nyiso-192 promotion, which merged DURING the commit** — kept verbatim, rebased onto,
  read as a structural JSON diff: NYISO-only, records-only, no verdict / key / bundle) and
  **all 13 bare keys + 4 pinned defaults re-resolve to D60's pins to the digit, measured twice**
  (before and after the rebase): `caiso-t1f` `29f8eb372810195f`, `pjm-t1f` `09996eca71ee80fd`,
  `neiso-t3` `f04fd06348e1623d`. It flagged, not absorbed, exactly what Amendment 1 told it to:
  the withdrawal of `complete.NYISO` is T3-NYISO-GOLDEN's precondition, the director's call.
  **Addendum D pushed before any row and before leg 3**: the mechanism named precisely
  (`_dof_ledger_row` scores the token `unattested` as a MISSING ledger; the builder REPORTS
  identification, never supplies it); six NEW rows keyed (ISO, field) with `requires=
  "iso-registry"` so no row can identify another ISO's value (rule 25 by construction); the
  seventh (`ccs_retrofit_capex_co2_scaling`) is D50's committed row and is now DORMANT — Q42
  made the field a default and the ledger enumerates NON-defaults, exactly the P20 mechanism
  Addendum B pre-declared for GOLDEN-3. **Two blunt negatives pre-declared rather than
  discovered: (i) `miso-t1f`'s FC-7 will NOT clear — FIVE pre-batch MISO registry overrides
  (`entry_vre_capacity_revenue`, `entry_vre_zone_selection`, `miso_rps_compliance_regions`,
  `miso_clean_tier_rows`, `retirement_sector_gate`) carry no curated row and sit outside Q37's
  limb; (ii) CAISO keeps its pre-existing `negative_renewable_offers` caveat.** Both routed
  here, not absorbed ("widening the scope to make a row read PASS is the thing Q37's limb is
  narrow to prevent"). Pending: legs 3–5, the rows, the re-scores, finding §5/§8.
- **T3-NYISO-GOLDEN — HELD on Amendment 1.** `complete.NYISO` is withdrawn at the pin (§0ak.2);
  its start precondition fails; **Q45's premise has lapsed.** No re-authorization card is
  served: the question only exists once a NYISO keeper reads CALIBRATED again and the marker
  is re-declared under the withdrawal's own re-entry clause (the third withdrawal — 07-19,
  08-30, 09-05 — each with the same clause).
- **D58 — held on D60-R2** (both write the PJM board rows). **D61 — issued, unlaunched.**

**2. GRADED — owner track (§2 rows):**
- **Q46 LANDS (PR #4817): NYISO → `2026-09-05-nyiso-192-astoria-panel`** — the nyiso-189 recipe
  on the CAMPD per-unit-merit outage extract re-derived after the Astoria 8906 stack-duplicate
  repair (rule 23: the panel repair is the cited data change; zero ScenarioConfig changes).
  **NOT-YET, grade 6 of 8, fails 2** (C1-2024 CC_REGULAR +3.68 TWh / +3.0 pp; C3c no longer
  lone); C2/C3a/C3b/C4/C6/C8 PASS. The D-5(b) worse-determination stop FIRED, was escalated on
  the card, **and the owner chose it with its cost**: `complete.NYISO` → withdrawn (D56-R's
  entry nested whole), the Q39 frontier → `frontier_withdrawn_2026_09_05`, gate (a) PASS →
  FAIL, keeper display re-keyed (R-T), validation-tier authorization lapses; `final` untouched,
  nothing spent. The bundle/payload the cleanup had pruned before the promotion landed were
  RESTORED (it is the keeper). Owner-named next lever: the CC_REGULAR duct-burner peaking
  tranche offer, measured identification, rule-29 screen — **which nyiso-194 then ran and
  KILLED**: phase 0 measured the tranche (loading distribution, band size, revealed price), two
  one-year 2024 screens pre-registered on frozen structural gates, and BOTH died (cap 8 fails
  S-3; peak 2.50 fails D-2, shape away from CAMPD) — no full span spent, keeper unchanged.
  Rule 29 doing exactly what it was written to do, on the first lever the owner named under it.
- **CAISO — caiso-252** (zero-LP; keeper unchanged at 251): the C4 2025 cell is NOT the object
  the handoff named — CC_REGULAR carries 90 / 87 / 95 % of the gas-fleet MSE as a DIURNAL error
  (over-generates night/evening, under-generates mid-day) that is hour-for-hour the mirror of
  the model's too-flat import diurnal shape; the caiso-251 degradation sits entirely in Aug–Dec
  and splits 56 % CC / 59 % CT; the real CT energy is ONE NP15 plant, Panoche (0.74–1.42 TWh
  actual vs 0.05–0.16 model); 7/10 predictions falsified; the DMM 2025 RA-import misalignment
  recorded at source. The import diurnal shape (caiso-244's LEVEL object's sibling) is now the
  CAISO track's live object.
- **Rule 15 `[R-DASHBOARD]` retention → KEEPER-ONLY** (G-1, #4823; owner ruling R-AQ, card K,
  quoted verbatim from ercot-248): each ISO's dashboard and `results/calibration` carry only the
  designated keeper run(s) plus golden-referenced / allowlisted bundles; every other run pruned
  at the next registration; registration of rejected probes unchanged; git history the record.
  `check_golden_manifest` and `prune_iso_runs` prose aligned; rule-history entry.
- **Audit track — Y-9 / Y-10** (#4822/#4825): the branch-protection flip is now **ROUTE 2, the
  owner's click-path** — the REST API is proxy-refused for this session class (403 before any
  PUT) and the MCP GitHub toolset carries no protection tool; the six required check names
  verified against `ci.yml`. **Flagged, live:** the R-AE path-filter glob `docs/FINDING-*.md`
  does not match `docs/handoffs/FINDING-*.md` (76 findings unenrolled — after the flip such a
  PR triggers no CI and deadlocks on six pending checks). Y-10 re-stamped all 20 bench parts at
  builder `b2f21b9a`, formatted the five reds, repaired two lints — **the R-AE flip set is
  clear at the pin** — and PROPOSED (owner ruling, not executed) narrowing the bench builder
  fingerprint: three fingerprint moves on 09-05, none reached a payload, 53 % of the hashed
  surface is comments. The audit desk's card.

**3. RULINGS / DECISIONS:** **Q46 recorded** (in-lane, nyiso192-Q1: promote the Astoria arm,
withdraw the marker — landed #4817). No new card. Director decisions: T3-NYISO-GOLDEN stays
HELD (Amendment 1 executes itself); **D63 queued-named** — a records lane for the five
pre-batch MISO override rows + CAISO's `negative_renewable_offers` row, each pre-declared from
its landing finding (S-123 / D31 / D33-M / D53 / the CAISO offer lanes) under Q37's limb, issued
when D60-R2 lands (it owns `ff-verdicts.json` this window); D58 releases at the same moment.

**4. THE QUEUE, RE-DERIVED:** D60-R2 running · D58 held on it · T3-NYISO-GOLDEN held on the
marker (no date) · D61 issued, unlaunched · D63 named, issued on D60-R2's landing. Owner track
objects this desk watches: the CAISO import diurnal shape (caiso-252), the NYISO CC_REGULAR
2024 excess after the duct-burner kill (nyiso-194), MISO's evening scarcity tail (miso-219:
unreachable by any registered field). Queued-named unchanged (§0aj.4).

**AMENDMENT 1 (same sitting, owner: "Issue prompts").** Dispatchable without a collision: **D61** (issued
r#38, never launched — re-emitted verbatim) and a NEW zero-solve lane, **D64** (the D50 fourth seam:
CCS ΔFOM / capture VOM per captured tonne, D50 §8 Disclosure 1; Fable; docs only). D63 and D58
stay held on D60-R2 (its files); T3-NYISO stays held on the marker.

## 0aj. Refresh #39 (2026-09-05, main HEAD `cf5425f7`) — D60's first two re-solves land and one fires its P10 STOP on an instrument; CAISO's C3a passes for the first time; the owner-directed cleanup deletes 1,500 files and loses no evidence; a pending NYISO promotion on an open branch would withdraw the marker Q45 rests on

**0. FIRST ACT.** Handoff claim (§0ai = r#38) matched the top entry; this is r#39. Delta
`aa86890e..cf5425f7`: 26 merges (#4794–#4816), 19:23Z → 21:06Z. My r#38 push merged as
**#4798**; branch deleted, recreated off `cf5425f7`. Gates: `audit_keepers` 0 ·
`check_gate_a_provenance` **0** (MISO re-keyed to miso-217 by the CLEANUP lane — the
promotion skipped step 4, the tenth promoter miss; CAISO re-keyed by the caiso-251 lane
itself) · parity **0** (the cleanup emptied the keep-required allowlist; 6 runs / 39 dirs) ·
matrix 0 · goldens 0 (15 stale-with-pruned-provenance, by design) · **ruff format RED ×5**
(`gen_miso217/218_attestation.py`, `offer_curves.py`, `reserve_requirements.py`,
`test_miso_intermediate_gas_offer_margin.py`) + one F401 (`benchmark_corridor.py`, the
cleanup lane's) — the owner's MISO track and the cleanup lane own them; the audit desk's Y-1
flip set is red again on exactly these.

**1. GRADED BY CONTENT — capx lanes:**
- **D60 — RUNNING; legs 1–2 of 5 LANDED** (PRs #4796/#4800/#4802/#4807/#4815;
  `FINDING-capx-d60-2026-09-05.md` §§0–4, 6–7 written, §5 pending):
  - **Leg 1 `miso-t1f`** (49.6 min / 9.68 GB; key `b1a73a087064ffd8` = Addendum A's CORRECTED
    value, matched to the digit): three mechanisms, every moved row attributed from committed
    single-mechanism records — **the sector gate MOVES NOTHING on exits** (87.8–103.1 GW gated
    out of the screen; every retirement row byte-identical; ZERO economic exits in either arm
    → P17 HIT, **P18 VACUOUS, graded as such — the composition claim is untested on this
    horizon, not validated**); **the ratio IS what moves the board** (position 0.903 → 0.943
    in 2027 … 0.945 → 0.987 in 2030; accredited firm +5.2 GW in 2026; I12 ≈ +4 pts/yr; the
    2030 backstop stops buying 6,584.5 MW of gas_ct; FC-2 row 4 33.6 % FAIL → 23.0 % CAVEAT —
    P5 HIT in D51's measured direction); **CCS a measured NULL** (0 vs 4,631.1 MW; P1 HIT).
    FC-1 stays FAIL {I12, I7} — 2029 I7 76 MW short of clearing, the marginal row P3 named.
    HOLD → HOLD; prior at `miso-t1f-pre-d60`.
  - **Leg 2 `nyiso-t1f`** (10.9 min / 3.37 GB; key matched): **P10 STOP FIRED — PROMOTE →
    PROMOTE-WITH-CAVEATS on FC-7 ALONE.** Every model row is unmoved or better (FC-1 14/14
    PASS, FC-2 all PASS, FC-8 PASS); the two armed gates enter the DOF ledger with no curated
    identification row → `unattested` → FC-7 CAVEAT. The identification IS committed (D52
    §8(1): published NYSRC Table D.2 peak; adopted IRM × (1 − derate), vintage-gated, reconciled
    by test), so the rows are writable and would restore PROMOTE with no re-solve — **the lane
    refused to author them after reading the result** (the D46 sequence; Addendum B pre-declared
    against it) and routed the decision here. The arming itself did exactly what D52 said: 2026–
    2030 sits beyond Table D.2, the vintage limb holds last at 1.0823, a +0.24 % requirement
    bump and nothing else (P7/P8 HIT). Disclosed and routed: NYISO's step-0 confirmed-exit
    channel is EMPTY AT SOURCE (`nyiso.csv` a documented zero-row stub) — a data-intake item
    for the owner's NYISO track, not a differentiator here.
  - **Addendum B** (before the GOLDEN-3 re-solve): the T3 attestation's six assertions fixed in
    advance under Q37's limb. **Addendum C** (before the `pjm-t1f` leg): Amendment 1 absorbed;
    key `09996eca71ee80fd` re-verified through the harness path, no difference; P21–P25
    pre-declared with direction (the clearing half should dominate the CCS half on the backstop
    share; the D57 coal-retained / gas-steam-over-exit signature inherited and measured, not
    repaired).
  - **Pending:** `caiso-t1f`, `pjm-t1f`, `neiso-t3` GOLDEN-3, finding §5. **Director decision on
    the routed STOP → Amendment 2** (§0aj.3).
- **D58, T3-NYISO-GOLDEN, D61:** issued, not launched (no branch). **T3's precondition is
  newly at risk** (§0aj.2, nyiso-192) → Amendment 1.

**2. GRADED — owner track (§2 rows):**
- **CAISO → `2026-09-05-caiso-251-b1-nomargin`** (#4814): the CAISO gas offer was carrying
  NEISO's functional form; removing it restores the fuel coupling CAISO's own OASIS record
  measures (the fixed-margin form left CT_PEAKER at 0.53 of its physical fuel sensitivity vs a
  measured 0.9–1.0) — **C3a (load-bearing) FAIL → PASS in all three years; C4 (supporting) PASS
  → FAIL on one cell; NOT-YET, but the outstanding failure drops a tier**; promoted on the basis
  registered before measurement with C3a excluded in both directions; rule-29 G-SCREEN on 2024
  passed first (CT dispatch doubles) — the first keeper promoted under R-SCREEN. **Against
  interest:** a WRONG DOF count ("5 → 5"; the field is a dict) published in four places, caught
  by the keeper-auditor, corrected — the true figure 9 entries / 6 residual UNCHANGED, and the
  "removes a free parameter" claim withdrawn (the anchor was derived, never a ledgered DOF).
  The CAISO stage-0 golden is now two promotions stale.
- **MISO → `2026-09-05-miso-217-intermphys`** (#4799/#4801/#4813): one MISO-gated zero-DOF
  field returns 38,501 MW (58.4 % of assembled gas capacity) to the armed offer-margin
  mechanism; every kill silent; the pre-registered un-instrumented cross-class backfill
  materialised (91 % of CC_REGULAR-2024's headroom, inside the band); NOT-YET C3a-2025 alone.
  **Step 4 skipped** (the cleanup lane re-keyed the stamp). **miso-218** (owner-requested ×1.10
  ratio-preserving offer-level scale): the owner's premise HELD and the lane's decisive
  prediction was WRONG (all three C3a years land inside ±10 %; C3a-2025 −12.3 → −6.3) — and it
  is **NOT a keeper by pre-commitment**: a uniform level scalar chosen to move a price residual
  is exactly the fitted mechanism rules 1 and 13 foreclose; it also breaks a load-bearing C1 cell
  and pushes every C8 class over budget. Registered as a rule-13 probe, then pruned (keeper-only
  retention). The right outcome, reached the right way.
- **NYISO — nyiso-192/193, and an UNMERGED promotion**: nyiso-193 (records) found Q39 already
  ruled and executed, re-labelled the arm question `nyiso192-Q1` (it had collided with Q40),
  filed the NYC steam delivered-gas intake spec and a D-2 unit-grain scorer card. The
  `nyiso192_astoria_panel` arm registered NOT-YET (grade 6, fails 2: C1-2024 CC_REGULAR +3.68
  TWh; C3c no longer lone) — then **the open branch `claude/nyiso-192-frontier-adjudication-
  mo2nrq` (2 commits, unmerged at the pin) carries an IN-LANE OWNER RULING on nyiso192-Q1:
  "Ok promote it … then tune the cc regular offer curve up for the duct burner peaking tranche"**
  — keeper → `2026-09-05-nyiso-192-astoria-panel` (NOT-YET), the D-5(b) worse-determination
  stop fired and the owner chose it WITH ITS COST: `complete.NYISO` → withdrawn (D56-R's entry
  nested), the Q39 frontier → `frontier_withdrawn_2026_09_05`, forecast gate (a) PASS → FAIL,
  validation-tier authorization lapses. **When that merges, Q45's premise (NYISO holds (a)) no
  longer holds** → T3-NYISO-GOLDEN Amendment 1 makes the marker an explicit start precondition
  (STOP and route if withdrawn). The same commit restores six JSON files corrupted by
  rebase-conflict markers, and notes the MISO gate-(a) stamp drift the cleanup lane has since
  repaired on main — expect a rebase conflict there. Recorded as **pending Q46**; numbered when
  it lands.
- **THE OWNER-DIRECTED CLEANUP** (`cleanup-dead-code-stale-data`, #4808/#4816; "delete what is
  not needed, never archive"): `scripts/archive/` deleted entirely (292 files), 1,229 record-only
  probe scripts deleted (the 69 live code imports stay), 21 dead scripts, dead `src/` (metrics.py,
  som_conduct.py, pipeline/result.py + seven functions/six constants); `results/calibration`
  pruned to the six keeper bundles + ercot-248's constituents (18 unmapped solve-output bundles
  deleted, the keep-required allowlist EMPTIED); **forecast side: 36 superseded sidecars + 109
  unregistered `results/hindcast` dirs + the sidecar-less ffr*/arm3arm outputs deleted — every
  bare key, every board-cited run, the crossovers and the T3 goldens kept.** Verified here:
  **ff-verdicts.json lost ZERO keys (99 → 101; every `-pre-d*` prior intact)** — the program's
  A/B evidence is finding-plus-verdict, and both survive. Also repaired: the D57 arm-A
  `run_config.json` that the nyiso-192 registration (#4795) committed WITH EIGHT UNRESOLVED
  CONFLICT BLOCKS (not JSON; `test_cache_config_agreement` erroring) — restored to D57's own
  bytes. Rotation rule in `scripts/README.md` now reads DELETE.
- **Rule 29 `[R-SCREEN]` clause (b) — NO CONTROL SOLVES** (owner, 2026-09-05): the incumbent
  keeper's committed bundle IS the control (G-CTRL form 4 default); HEAD drift is a CODE
  question answered by a zero-LP **G-DRIFT** audit (classify every changed hunk on the backcast
  path INERT-with-reason or LIVE; only a LIVE hunk earns a control solve, and only for the
  screen's years), recorded in the PRECOMMIT before the arm is solved. Backcast-track scope;
  every backcast prompt this desk offers cites both clauses.
- **2022 holdout data completeness** (#4811): ERCOT 60-Day DAM thermal availability 2022, ERCOT
  nuclear CF 2022, `actual_tail.json` ERCOT 2020–2022 under the `complete` marker; NYISO LI
  2022/23 N-1-1 TSL row, NY Harbor ULSD 2022, market-generator solar 2022 — data-only, every
  producer re-proved on 2023–2025 first, NOTHING spent (rule 22: intake needs no marker).
- **DOCS-B finalized** (#4806/#4809/#4810): the spec finalized (WS4, gate G2), the user manual
  swept, CHANGELOG caught up, docs index counts refreshed, `/sync-docs` final pass. **Y-8**
  (#4803): 14 stale bench parts re-rendered at builder `4e78c854`.
- **Audit v29 + v30** (#4804/#4812): **R-AL** (owner performs the branch-protection flip —
  "doing it now"), **R-AM** (declare G2 when the flip is live; DOCS-B dispatches then), **R-AN**
  (the R-V keeper freeze on {ERCOT, NEISO, PJM} lifts AT the G2 declaration), **R-AO** (Y-8
  chartered). **The flip is NOT LIVE** (`protected: false` read five times across two lanes,
  110 min after "doing it now"), so **G2 is NOT declared and the keeper freeze is STILL IN
  FORCE**; ERCOT's keeper field moved under it (ercot-248, zero-solve, owner-directed) —
  unadjudicated by the audit desk. Stage-0 corrected to 2 of 7. Recorded here; not this desk's.

**3. DECISIONS THIS SITTING (director's, inside standing rulings):**
- **D60 Amendment 2 — the P10 STOP is resolved under Q37's limb, not waived.** Q37 (r#34)
  adopted exactly this: *a follow-up lane may author an attestation iff pre-declared before
  authoring, attestation row only, artifact-only re-score.* The identification of every field
  the batch armed is COMMITTED (D52 §8(1), D51 §1.3, D50 §1.2, D57 design §3.7), so the missing
  rows are an instrument gap, not a model gap. D60 pre-declares the rows (field, source, rule-13
  status, citation) in an Addendum D BEFORE writing them, writes them as curated design-decision
  rows, and re-scores every affected bare key artifact-only (`nyiso-t1f` now; `miso-t1f`,
  `pjm-t1f`, GOLDEN-3 as their legs land) — FC-7 the only row that may move; a moved
  determination is reported as the instrument's, never the model's. The `-pre-d60` priors are
  untouched.
- **T3-NYISO-GOLDEN Amendment 1 — the marker is a START precondition.** Q45 was granted on
  NYISO holding gate (a). If `complete.NYISO` is withdrawn at the lane's start (the pending
  nyiso-192 promotion), STOP and route — a §2.1b campaign on an ISO without the marker is not
  authorized by Q45, and re-authorization is a new card, not an assumption.
- **No new owner card.** The nyiso192-Q1 ruling is the owner's, given in-lane; it is recorded
  as pending Q46 and numbered when the branch lands. The R-V freeze / G2 / flip are the audit
  desk's items.

**4. THE QUEUE, RE-DERIVED:** D60 running (legs 3–5 + finding §5 + Amendment 2) · D58 held on
D60 · T3-NYISO-GOLDEN held on D60 AND on the marker (Am.1) · D61 issued, unlaunched · after
D60: D58's arming card, D61 → D62. Queued-named unchanged (§0ai.4) plus: NYISO's empty
confirmed-exit channel at source (data intake, owner's NYISO track); the owner-named CC_REGULAR
duct-burner peaking-tranche offer lever (backcast, owner's track, rule-29 screen); the NYC steam
delivered-gas intake spec (nyiso-193, owner-court).

**AMENDMENT 1 (same sitting, owner: "D60 is no longer running").** Relaunch protocol: unlanded
work restarts FRESH from the committed charter. Verified at `8b236246`: legs 1–2 registered
(`miso-t1f` `b1a73a087064ffd8`, `nyiso-t1f` `19a9690bb12c8459`), `caiso-t1f` / `pjm-t1f` /
`neiso-t3` still on their pre-D60 shas, finding §5 empty, Addendum D unwritten, no D60 branch
on origin. **→ D60-R issued** (pack §D60-R; Opus; caiso/pjm/neiso): the three re-solves,
Amendment 2's rows + re-scores, finding §5/§8 and its close. D58 and T3-NYISO-GOLDEN stay held
on D60-R.

**AMENDMENT 2 (same sitting, owner: "Issue a new prompt for it").** D60-R never launched
(no `capx-d60r*` branch, no commit at `c3addecc`) — audit ruling R-AK's launch-failure class,
re-issued on failure: **D60-R2** (pack §D60-R2), same charter on a fresh stem with a
stops-at-start twin check and push-each-leg discipline.

## 0ai. Refresh #38 (2026-09-05, main HEAD `aa86890e`) — D57 lands and the owner promotes the PJM clearing half in-session; D60 is a live checkpoint whose fifth rename fired a STOP on D57's own promotion; NYISO's frontier is back and its §2.1b campaign is authorized; a new owner rule (R-SCREEN) and a site-wide prune land on the owner's track

**0. FIRST ACT.** Handoff claim (§0ah = r#37) matched the top entry; this is r#38. Delta
`182aa74a..aa86890e`: 27 merges (#4761, #4770–#4793), 18:06Z → 19:12Z 09-05 — the fastest
window yet. My r#37 push merged as **#4774**; branch deleted, recreated off `aa86890e`. Gates:
`audit_keepers` 0 · `check_gate_a_provenance` **0** (the ERCOT row re-keyed by the ercot-248
lane itself to `2026-09-05-ercot248-two-config-keeper`) · matrix 0 · goldens 0 (88 entries, 24
enforced; **15 stale with a PRUNED provenance run** — the site prune, survivable by design via
`keeper_snapshot`) · **parity 1** (two in-flight checkpoints: `caiso251_ctrl`, `nyiso192_astoria_
panel` — their lanes' promotion-duty items, the v25/v26 class) · **ruff format RED ×2**
(`offer_curves.py`, `test_miso_intermediate_gas_offer_margin.py` — miso-217's, branch merged
and deleted; routed to the owner's MISO track, not `src/`-editable here). Y-7 (#4771) had
already formatted the six r#37 reds — my r#37 routing to D57/D60 was pre-empted, correctly.

**1. GRADED BY CONTENT — capx lanes:**
- **D57 — LANDED AND PROMOTED** (PRs #4761/#4775/#4786, `FINDING-capx-d57-2026-09-05.md`):
  built as designed, gated, zero DOF, byte-inert unarmed (bare `pjm-t1h` `c6091bd5b62bbc3f`
  unmoved before the ruling; PJM keeper replay byte-identical); **Phase 0 reproduces the D54
  instrument to 0.000 $/MW-day and 0.000 pt on both bases.** Two arms solved: **cleared position
  within −0.48 / −0.98 / −2.79 pts of the published BRA cleared position** (arm A; the census
  evaluation sat +8.5 / +4.1 / −4.3 away); **the §3.5 identity holds in all eight screens** (the
  failing set IS the uncleared set, to the unit); **price 1.52× / 2.43× / 5.73× published**
  (arm B 1.92 / 2.81 / 6.35), set by a marginal offer in every long year, never inside the ±20 %
  falsifier — **the gas-CT (404 units / 24.2 GW), gas-ST (115 / 8.8 GW) and oil (421 / 3.7 GW)
  fleets carry exactly ZERO E&AS margin in the hindcast prices and offer at their full bars**,
  a 37 GW plateau at $61–103/MW-day above the published $29–50; **≥ 3.8 / 18.0 / 8.6 $/kW-yr
  per CT / ST / oil unit (2022/23) would put those offers AT the published price.** Measured,
  not moved. FC-3 follows the operand: the 2022 cohort shrinks 88.6 GW failing at $0 → the
  19.2 GW uncleared set; **coal RETAINED** (economic coal 11.4 → 0.44 GW — D48's +1.4 GW and
  more) while the zero-E&AS **gas-steam fleet exits in full** (9.5 vs 2.7 GW actual); the entry
  screen, reading $28.7/kW-yr instead of $0, builds +4 GW gas CC in 2023; `retire.total_gw`
  18.70 (control 17.96, actual 15.06), recall 17 → 12/20, `false_retire` 6.69 → 9.49; HOLD both
  arms; 14 HIT / 4 SPLIT / 6 MISS. **§8.1 — OWNER RULING IN-SESSION: PROMOTED (recorded here
  as Q44).** The JOINT flip (`pjm_accreditation_design_vintage` + `pjm_demand_response_supply`
  + `capacity_market_supply_clearing_by_iso["PJM"]`) via `_pjm_config` `default_scenario_
  overrides` — the shared defaults stay off, no b′-1 line, no other ISO's key moves, every
  backcast keeper byte-identical, `--no-…` reaches the D45-R control; arm A's own key
  `f0e050e820c1159a` IS the bare `pjm-t1h` (no re-solve), D45-R preserved at
  `pjm-t1h-pre-d57`, arm B keeps `-headbasis`; PJM shard cells K ×3. **What it leaves:** the PJM
  T1-F bundle (`pjm-t1f`, `321f04e9060787f0`) now carries a SUPERSEDED posture — routed to the
  batched re-measure, i.e. **D60**; and the named successor, **the CT / ST / oil E&AS operand
  (§4) → D61.** Rule 1 and rule 14 both applied by the owner exactly as written: a structurally
  correct mechanism stays in with its worse composition, and the worse fit names the root cause.
- **D56-R2 — LANDED** (PR #4780, `FINDING-capx-d56r2-nyiso-frontier-2026-09-05.md`):
  `keepers/NYISO.json` carries a live `frontier` block again (declared 2026-09-05 on nyiso-189,
  Q39 verbatim, the 2026-08-23 ratification and its 08-30 reversion preserved whole beneath);
  `frontier_basis` rewritten with the prior text as a dated WAS: clause; auditor PASS (S1 asked
  for `build_status.py --iso NYISO`, run, determination unmoved); guard 6/6 with no gate-(a)
  leaf moved; **the four-instrument test reads {ERCOT, NEISO, NYISO, PJM} on all four** at
  `8342d74d`. Spent nothing, solved nothing.
- **D60 — CHECKPOINT, STILL RUNNING (owner-confirmed at this sitting)** (PRs #4781/#4783/
  #4792; PREDECL + Addendum A, no finding yet): **the flip commit landed** — Q40 (MISO ratio via
  `_miso_config`), Q41 (both NYISO gates via `_nyiso_config`, NYISO's first ISO-level
  overrides), Q42 (`ccs_retrofit_capex_co2_scaling` dataclass default True, the second b′-1
  line, frozen drop value `False`); **both pinned default keys advanced BY DESIGN and declared**
  (`ScenarioConfig()` 4c6b03ae → e5ecd410; bare backcast 8211c72b → 6a2845e5; dated cause blocks
  in `test_persisted_identity.py`, a 2026-09-05 cache-epoch ledger entry) — an explicit `False`
  still keeps its pre-flip bundle; every backcast and every horizon ending before 2028
  byte-identical; CLAUDE.md step 2 + spec §5.6 amended; 16-assertion `test_d60_arming_batch.py`;
  `check_cache_key_registration` 248/248. **Four zero-solve renames landed** with byte-identity
  ESTABLISHED before each (`miso-t1h` ← the D53 rider; `nyiso-t1h` ← the D52 arm; `ercot-t1f` /
  `neiso-t1f` ← the D50 arms; priors at `-pre-d60`; no earlier baseline overwritten). **The
  fifth rename (`pjm-t1f` ← the D50 PJM arm) FIRED STOP 1 and was REVERSED before pushing:**
  D57 merged between the pre-declaration and the rebase and armed three PJM gates, so the bare
  `pjm-t1f` recipe now resolves to `09996eca71ee80fd` and the D50 arm is no longer at it —
  `pjm-t1f` keeps its D45-R record, stale on TWO postures, and only a re-solve at that key
  fixes it; correctly NOT run (PJM was D57's) and routed here with the key. Addendum A also
  corrected its own `miso-t1f` post-D60 key (`b1a73a087064ffd8`) and pre-declared a THIRD
  mechanism on the MISO t1f leg (the sector gate rides it). **OWED: the four re-solves
  (`miso-t1f`, `nyiso-t1f`, `caiso-t1f`, `neiso-t3` GOLDEN-3), the finding — and now the
  `pjm-t1f` leg (~28 min), which is free: D57 has landed.** → **§D60 Amendment 1** (the owner's
  relaunch-protocol answer: still running — amend, do not re-issue).
- **D58 — RELEASED** (D53 merged, D57 landed). Dispatch **after D60 lands** — both write the PJM
  shard and the PJM board rows. Its control is the NEW bare `pjm-t1h` (the joint posture).
- **D53 (Q43), D59, D50-R, D56-R:** no change since r#37.

**2. GRADED — owner track (§2 rows):**
- **ERCOT — the two-config keeper registered as ONE run** (`2026-09-05-ercot248-two-config-
  keeper`, `composite_provenance.json`: 2023 from 236-swcap, 2024/25 from 234-eastex, every
  artifact byte-copied, zero solve; re-verified CALIBRATED on the full span and both designated
  spans) with every surface re-keyed in one change (shard + `config_partition` run ids, the
  marker with D-5(b) re-verification, the forecast gate-(a) stamp — R-T honoured — the ERCOT
  matrix stamp); and **the OWNER DIRECTIVE to prune every ISO's dashboard to its keeper alone**
  (`prune_iso_runs.py --force-uncite`: ERCOT 15, CAISO 11, PJM 4, MISO 14, NYISO 14, NEISO 3
  runs off the site; golden-referenced and allowlisted bundles kept on disk; every shard's
  `site_retention_note` updated — run-id citations in shards, the marker and the matrix may now
  point at runs no longer on the site, stated in the notes). **A records act with a program-wide
  consequence: the top-15 retention is superseded by keeper-only for now**, and `prune_iso_runs`
  gained a golden/allowlist retention guard (`4cacbda1`).
- **Rule 29 `[R-SCREEN]` landed in CLAUDE.md (owner rule, 2026-09-05):** screen a new config on
  ONE year (the year the mechanism's own footprint is largest, named in the PRECOMMIT) before
  spending the full span; a STRUCTURAL STOP gate only — may kill, never promote, never gated on
  the target residual; rule 16 untouched (the screen bundle is a throwaway probe). Backcast-
  track scope; this desk's forecast hindcasts are unaffected (their ≤ 25-min legs are their own
  screen), but every backcast prompt this desk ever offers cites it.
- **NYISO — nyiso-192** (keeper unchanged at 189): the dashboard payload's CHP behind-the-meter
  add-back fell through to the 35 % merchant default instead of the measured shares the LP held
  out — the handed-forward CC_CHP object was inflated THREE-FOLD by the instrument, repaired and
  the payload re-rendered; the Astoria merit-panel stack-duplicate defect measured (not
  Astoria-only) and A/B-armed as the session's one arm; bundle `nyiso192_astoria_panel` is the
  parity-red checkpoint. **MISO — miso-215/216/217** (keeper unchanged at 213): the `phys_*`
  coverage gap is real and 58.4 % of assembled gas capacity wide, borrowing valid 9/9, but the
  arm is adverse on the two cohorts that matter → no A/B (miso-215); the gas-offer margin
  anchor's grain: no grain dominates, ≥ 87.8 % of the distortion is the fixed-margin FORM's own
  footprint, **recommendation NO CHANGE** with the CT_PEAKER −$10–20 bias carried on the
  packet's face (miso-216); miso-217 built the `phys_*` arm + scorer blind (its two ruff reds).
  **CAISO — caiso-250/251** (keeper unchanged at 246): the ranked-first STORAGE object is NOT
  new — a storage charge column is the marginal buyer and 44–60 % of the cell lies inside
  caiso-168's adjudicated belly mask; hydro REFUTED (interior 93–96 % of hours); caiso-251
  pre-registers the gas-offer fuel-coupling form (G-COUPLE passes: the armed fixed-margin form
  under-couples CT to half its fuel sensitivity); `caiso251_ctrl` is the other parity-red
  checkpoint; branch `caiso-250-…-7tci3e` open.
- **Audit v28 + v28b** (#4776/#4782): four owner rulings recorded — **R-AH** (Y-1 branch-
  protection flip on the first 6-of-6 head), **R-AI** (hold the three stage-0 re-captures until
  the 09-07 48-hour clocks), **R-AJ** (one `golden-data-tier.yml` dispatch as G2 leg-1 proof,
  then the R-V keeper-freeze question), **R-AK** (Opus for records/capture/small-repair lanes
  until the launch-failure class clears; Fable stays for adjudication and rule-27 scope) — and
  v28b records against interest that v28 wrote "none issued" three hours after R-AH was given.
  Z-4 CLOSED; X-6b's first leg discharged (Δ = 7). **R-AK is card-adjacent to this desk's model
  assignments and is ADOPTED**: the T3-NYISO-GOLDEN and D58 lanes below go to Opus; D61 (an
  operand adjudication) stays Fable.

**3. RULINGS THIS SITTING:**
- **Q44 (recorded — in-lane, D57 §8.1, 2026-09-05): PROMOTE the joint PJM configuration** as
  the forecast default via `_pjm_config` overrides. The R-AG shape, recorded the same sitting.
- **Q45 (C-14, live): AUTHORIZE the NYISO §2.1b full-horizon campaign — dispatch after D60's
  re-solves land**, so one HEAD carries every armed posture before the 25-year golden is cut.
  → **T3-NYISO-GOLDEN** chartered (pack), RELEASED-CONDITIONAL on D60's finding.
- **D60 status (live): STILL RUNNING → §D60 Amendment 1** (the `pjm-t1f` leg added; nothing
  re-issued).
- **Owner acts recorded, not numbered:** rule 29 `[R-SCREEN]`; the keeper-only site prune; the
  ercot-248 consolidation (each cited above).

**4. THE QUEUE, RE-DERIVED:** D60 running (+ Amendment 1) · D58 released, after D60 · T3-NYISO-
GOLDEN issued, after D60 · **D61 issued** (the PJM CT/ST/oil E&AS operand, Phase 0 zero-solve:
what real revenue streams the hindcast price denies those fleets, sized against the PJM SOM
net-revenue tables as validation observables, and whether the D12 scarcity-basis / reserve
co-opt channel — pjm-164 measured PJM's reserve dual REAL — is the operand's home; rule 21: no
coefficient) · queued-named: the D50 fourth seam + seam-3 price object; the ARV-annualization
CR-3 object; D59's NYC census object (the owner's NYISO track — nyiso-192 is already on the
Astoria footprint); D51's position observability; `co2_rate` in `pipeline_events`; the I7/I12
seam re-basing lane; D53's additions mirror + CHP-host screen; the D48 DR-convention probes;
dispersion siblings. **Cards open: none.** Next cards: D58's PJM sector-gate arming (on its
result); D61's operand (on its Phase 0); the audit desk's R-V keeper-freeze question is the
audit desk's.

## 0ah. Refresh #37 (2026-09-05, main HEAD `182aa74a`) — the r#36 wave lands whole inside ten hours; NYISO is `complete` again; the locality half is structurally right and inert on a long NYC census; four cards ruled at once and the arming batch is chartered

**0. FIRST ACT.** Handoff claim (§0ag = r#36) matched the top entry; this is r#37. Delta
`e75250c7..182aa74a`: 50 commits, 15 merges (#4754–#4769), 02:41Z → 15:28Z 09-05. My r#36
push merged as **#4754** and the branch was deleted; recreated off `182aa74a`. Gates at the
pin: `audit_keepers` 0 · parity 0 · `check_gate_a_provenance` **0** (six rows; NYISO now
reads PASS on the marker — D56-R's re-derivation) · matrix 0 · goldens 0 (88 entries, still
3 stale: CAISO/MISO/NYISO vs their 09-05 keepers) · **ruff format RED on six files** (§0ah.4).
Keepers UNCHANGED at r#36's set (CAISO 246 · ERCOT 234 · MISO 213 · NEISO 99 · NYISO 189 ·
PJM 162). **Markers: `complete` = {ERCOT, NEISO, NYISO, PJM}**; `final` empty.

**1. GRADED BY CONTENT — capx lanes:**
- **D56-R — LANDED** (PR #4763, `FINDING-capx-d56r-nyiso-redeclaration-2026-09-05.md`):
  `complete.NYISO` declared 2026-09-05 on `2026-09-05-nyiso-189-steam-identity` (keeper =
  keeper_at_declaration), determination re-verified artifact-only first, the 2026-08-30
  withdrawal nested whole beneath; `audit_keepers` M1a/M1b PASS; `holdout_policy.authorized
  (NYISO, validation)` False → True, locked tier False; board gate (a) FAIL → PASS on the
  literal test; NYISO reads (a) PASS · (b) PASS · (c) PASS · (d) none — **§2.1b candidacy
  re-opens**. Frontier NOT re-asserted (no Q39 in §3 at its pin `921bb4cd`), stated never
  silent. Every provenance leaf re-stamped after its third rebase (the X-6b doctrine, applied).
  Spent NOTHING, solved NOTHING.
- **D59 — LANDED** (PRs #4760/#4764, `FINDING-capx-d59-2026-09-05.md`):
  `locality_capacity_curves` built default-off, zero DOF, NYISO-only — NYC (J) and LI (K) on
  their own published ICAP demand curves at the published LCRs, position on the ICAP Manual
  §2.6 identity, settlement by §5.15.2 max(NYCA, locality); 12 gross-CONE rows intaken;
  retirement / entry / storage seams; 15 tests. **The A/B is BYTE-IDENTICAL on every FC-3
  row**, and the reason is the position, not the price rule: the model's NYC ICAP census
  (9,959 / 9,543 / 9,543 MW) sits **+727 / +824 / +838 MW above the Gold Book Zone-J summer
  capability**, so NYC reads 1.115 / 1.107 / 1.147 vs published 1.026 / 1.057 / 1.078 and the
  2025/26 NYC curve pays $25.7 — BELOW NYCA's $28.65 — so the max returns NYCA and the 2025
  gas_st wave fires as in the control. P9 re-read: (a) NO (+96 %), (b) NO (0.643), (c) YES —
  one of three, **the NYCA curve stays OFF** (self-executing, twice now). Transcription check
  answered: the curve intake is exact; the 2025 SOM Table 9 margin row is a source carry-over
  of 2024. **Recommendations: DO NOT ARM the locality field (structurally right, inert, NYC
  price 0.22–0.43× the market's on a census 5–9 pts long); DO NOT ARM the NYCA curve.** Cell
  **I**. Routed: the NYC census +0.7–0.8 GW (the 2023-24 Peaker-Rule exit set the 2020-vintage
  fleet still carries — the owner's NYISO backcast lane's fleet object); the ARV-at-1.0
  annualization shared by the NYCA and locality curves (a CR-3 object, queued-named). The
  curve question re-opens on those two objects, not before.
- **D50-R — LANDED** (PR #4768, `FINDING-capx-d50-2026-09-04.md` now exists at the cited
  filename): **PJM window 3,584.7 → 909.8 MW (−74.6 %)** — 2028 closes entirely, 2029 gains
  +157.7 MW, which FIRED STOP 1 and is diagnosed from the ledger as deferral (the control's
  2029 pool was depleted by its own 2028 conversions), not addition; the two 2029 converters
  sit at 1.023 / 1.030 of the scaled bar — the seam-3 price-object channel the PREDECL
  under-called, LIVE and named. **MISO (conditional leg, fired): 4,631 → 0 MW, capacity-
  identical — the structural proof that retrofit accounting is inert.** Blast radius measured,
  not estimated: 153 committed forecast configs; 150 re-key; 42 reach ≥ 2028; **31 bundles /
  25 keys can move**; of those **7 BARE keys** (the six t1f + `neiso-t3` GOLDEN-3), 4 already
  measured by the arms (post-flip bare key = arm key under b′-1); residual **CAISO 22.6 +
  NYISO 12 + GOLDEN-3 33.0 = 67.6 min ≈ 1.1 h**. **Recommends ARM** (a construction repair;
  rule 1 decides it independently of the numbers). Disclosed at the gate: the fourth seam
  (ΔFOM / capture VOM reference-host-sized) is UNBUILT; the threshold moves rather than
  vanishes. → **card C-13 → Q42 ARM.**
- **D53 — LANDED, AND ARMED FOR MISO BY IN-LANE OWNER INSTRUCTION** (merged via the cleanup
  PR #4766 and the branch's forced tip `107f8c79`, "arm the retirement-screen sector gate for
  MISO only (owner instruction on the measured A/B; iso_configs override, rule 25)"): the
  owner's standing structural-integrity formula applied once all four §6 limbs read MET.
  Form: `_miso_config` `default_scenario_overrides` `retirement_sector_gate: True`, dataclass
  default unchanged; the bare `miso-t1h` now resolves to `c306ddc6d28c60c2` (the leg already
  solved), a two-key rename with D46 preserved at `miso-t1h-pre-d53` (HOLD → HOLD, every row
  identical); MISO cell **K**; every other ISO's key unmoved (asserted by test); the MISO t1f
  leg NOT re-solved (its next solve resolves the gated screen by construction). The finding's
  two template tokens were filled before merge. **Recorded as Q43** (an owner ruling given in
  a lane, not on a card — the R-AG shape, recorded here the same sitting so it never goes
  unrecorded). The PJM leg (D58) remains the discriminating test.
- **D57 — IN FLIGHT, a graded checkpoint** (branch `claude/capx-d57-pjm-clearing-build-
  gsdypm`, 4 commits): the mechanism BUILT (gated `capacity_market_supply_clearing_by_iso`,
  `adequacy.py` +292, retirements.py +234, tests +439) with **Phase 0 reproducing the D54
  instrument in code to 0.000 $ / 0.000 pt**; the PREDECL addendum pushed before any solve
  (posture at its HEAD: D53 unmerged then, D48 fields OFF; arm keys `f0e050e820c1159a` /
  `ccee17a4c1563727`); the whole sell-offer stack carried on the `capacity_clearing` ledger
  block so the E&AS operand reads off the arm ledgers; spec §5.9 doc-sync. Arms NOT yet
  solved. **Note for its finding: D53 has since merged (MISO-only override; PJM untouched)
  and does not move the bare `pjm-t1h` key — its §0 posture row is stale but its arms are not.**
- **D58 — still RELEASED-CONDITIONAL**: D53 merged ✓; D57 not landed.

**2. GRADED — owner track (§2 rows):** keepers unchanged. **nyiso-190** (zero solves): the
nyiso-189 keeper's unmeasured justifying clause measured and REFUTED (keeper stands on its
measured record). **nyiso-191**: the CC_CHP scope extension of `cc_capacity_reconcile`
TESTED and REJECTED on rule 19 (artifact reverted). **miso-214** (zero solve): 62–70 % of the
CT energy the model misses was produced BELOW the plant's own delivered cost at the market's
own price — unreachable by any price/offer mechanism; K-d fires, no A/B chartered; an
offer-form coverage gap named for miso-215. **caiso-247/248/249**: the C3a residual is NOT a
hub-basis residual (hub-marginal regime 4.0 / 3.6 % of the gap; the ACQUITTAL falsifier
fires); **caiso-248 STOP-THE-LINE against interest** — caiso-247's fleet rebuild carried 184
phantom biomass LP units (`inject_biomass_mustrun` derived from `solve_and_persist` locals,
never in `meta.json`, invisible to `run_year_kwargs`), the BIOMASS headline WITHDRAWN, the
other two results bit-identical and standing; caiso-249: the STORAGE residual bucket (43 / 55
% of the gap) is NOT a loss-surface artifact — no thermal unit is marginal in those hours,
price set by inter-temporal duals; the DOM_GAS/STORAGE split remains unquotable.

**3. RULINGS THIS SITTING (cards served live, AskUserQuestion):**
- **Q39 (C-10): RE-DECLARE `frontier` on nyiso-189 too** — both instruments, as the withdrawal
  removed both. → **D56-R2** (records lane).
- **Q40 (C-11): ARM `adequacy_accounting_ratio_dated_net` for MISO** (the substance of D51's
  §7, over the letter of limb (c)). → **D60**.
- **Q41 (C-12): ARM BOTH NYISO requirement gates** as the forecast default. → **D60**.
- **Q42 (C-13): ARM `ccs_retrofit_capex_co2_scaling` as the default and SCHEDULE the 1.1 h
  residual re-measure** (CAISO t1f, NYISO t1f, GOLDEN-3). → **D60**.
- **Q43 (recorded): the D53 in-lane arming instruction** (§0ah.1).
**The batch, sized:** under b′-1 EVERY forecast bare key re-keys on Q42 (D50 §6.1: the
post-flip bare key IS the explicit-True arm key). Behaviour can move only where the screen is
reached (≥ 2028), so the t1h bare keys (`miso-t1h`, `nyiso-t1h`, and every other ISO's) are
**cache-key formalities** — byte-identical by construction, handled as documented renames
with the prior record preserved, the D53 precedent — while `miso-t1f` (Q40 + Q42, 65 min),
`nyiso-t1f` (Q41 + Q42, ~12 min), `caiso-t1f` (Q42, 22.6 min) and `neiso-t3` GOLDEN-3 (Q42,
33 min) are RE-SOLVED with priors preserved; `ercot/neiso/pjm-t1f` post-flip bare keys = the
D50 arms (rename). ≈ 2.2 h of solve, one Opus lane, sequential (rule 12 inside the session),
ordered flip-first so every re-solve lands on the final posture once.

**4. RECORDS / HYGIENE:** six files fail `ruff format --check` at the pin — three of D59's
(`capacity_market.py`, `new_entry.py`, `runner.py`), D53's `retirements.py` (via the cleanup
merge), nyiso-191's two (`gen_nyiso191_attestation.py`, `test_derive_cc_capacity_reconcile_
scope.py`); every owning branch is merged and deleted. Under rule 27 this desk does not edit
`src/`. Routed: `capacity_market.py` / `retirements.py` / `runner.py` to **D57** (it edits all
three and rebases before every push — format them in its next commit); `new_entry.py` +
the two nyiso-191 files to **D60** as its first, format-only commit. The audit desk's Y-1 flip
set stays red until both land; stated so it is not re-discovered. No re-key duty fired
(guard 6/6; NYISO's PASS is D56-R's own derivation).

**5. THE QUEUE, RE-DERIVED:** D56-R2 + D60 issued; D57 running; D58 held on D57; the NYC
census object (D59) → the owner's NYISO backcast track (the keeper fleet's 2023-24 Peaker-Rule
exit set / DMNC basis) — offered, not chartered here (backcast is the owner's track); the
ARV-annualization CR-3 object, the D50 fourth seam (ΔFOM/VOM per captured tonne) and the D50
seam-3 price object queued-named; **the NYISO t3 campaign card is served when D60 lands**
(NYISO holds (a)+(b)+(c) and its requirement basis will then be the armed one — a golden on
the pre-arm basis would be stale on registration, §0af's own rule). Unchanged: the D48
DR-convention probes, the VRE ELCC limb, D51's position-observability question, the
`co2_rate` ledger field, the I7/I12 seam re-basing lane, D53's additions mirror + CHP-host
screen, dispersion siblings (LOW EV).

## 0ag. Refresh #36 (2026-09-05, main HEAD `e75250c7`) — the whole r#34/r#35 wave lands (D48 Ph.1 · D51 · D52 · D54 · D55; D50 a checkpoint); the PJM clearing-half design measures the E&AS operand as the object; NYISO's position artifact is CLOSED and the over-fire relocates to the locality; D56 never launched and its keeper moved; the eleventh gate-(a) firing is re-keyed under the standing duty

**0. FIRST ACT.** Handoff claim (§0af = r#35 + amendment 1) matched the top entry; this is r#36.
Delta `a35c9f9b..e75250c7`: 105 commits, 28 merges (#4725–#4752), 20:12Z 09-04 → 02:41Z
09-05. My branch is `claude/calibration-workstream-director-twmpyt` (the owner's stem for this
sitting; origin's copy had been deleted — recreated off `e75250c7`). Seven gates at the pin,
each run alone: `audit_keepers` 0 · `check_registry_payload_parity` **0** (v27's red cleared by
registration, as it predicted) · `check_mechanism_matrix` 0 · `check_bench_freshness` 0 (20
parts, 0 STALE, 20 engine-drift) · `check_golden_manifest` 0 (47 manifests / 86 entries, **3
stale: CAISO vs caiso-246, MISO vs miso-213, NYISO vs nyiso-189** — every one a promotion in
this window) · `check_forecast_staleness` 0 (Δ 7 of 10; the orphaned-stamp WARN, below) ·
**`check_gate_a_provenance` 1 → MISO** (the eleventh firing; re-keyed, §0ag.4).

**RECORDED AGAINST INTEREST (r#35): D48 Phase 1 had ALREADY LANDED at the r#35 pin.** PR
#4718 merged 2026-09-04 09:38 PT (`a1e72a99`), an ancestor of `a35c9f9b`; the r#35 desk wrote
"Phase 1 RUNNING (owner-confirmed)" and graded nothing. `git log --grep` on "D48" would have
found it (the grade-by-content doctrine, r#22, unapplied to one lane). Graded here, one
sitting late.

**1. GRADED BY CONTENT — capx lanes:**

- **D48 Phase 1 — LANDED** (PRs #4716/#4718, `FINDING-capx-d48-2026-09-04.md`): the
  accounting lands on the instrument to the MW (requirement 160,904 / 166,810 / 150,605 MW;
  position +0.10/+0.26 pt, curve $0/$0/cap in both arms, additions byte-identical — P2/P3/P5
  HIT) **but FC-3 moved +1.403 GW of economic coal** (`retire.total_gw` 17.958 → 19.361,
  `false_retire` 6.691 → 8.094) with every screen candidate's operands byte-identical — the
  mover is the pipeline **admission cap**, a firm-MW budget that a position-neutral basis change
  does not leave neutral (both sides ×1.25; +5.0 GW at the 2022 fleet) and whose $/firm-MW
  merit key re-ranks 38 coal units on per-unit EFORd. The **DR half** carries almost all of it
  (+5.1 GW vs +0.9). §5 condition (a) FAILS as written → **DO NOT ARM either field alone;
  arm WITH the clearing half** (D45 §2.3 item 3), where the same budget is priced at the
  published curve's $15–21/kW-yr. Suffixed `pjm-t1h-d48-devintage` HOLD. Routed: the clearing
  half (→ D54 design, landed → **D57**), the VRE/storage ELCC two-date limb (+447 MW, named),
  the DR offered-vs-cleared convention (two zero-DOF probes V-only `a0ff4a31` / D-only
  `c79fc92a`, named), the 2028/29+ DR ratio convention.
- **D51 — LANDED** (PR #4729, `FINDING-capx-d51-2026-09-04.md`): the ratio re-identifies
  **0.8546 → 0.8934** (0.878/0.909 per year) with D31's construction reproduced to the decimal
  and ONE term moved (the dated channel measured, not retyped); armed, positions 1.0777 /
  1.0194 / 0.9875 — the 2024 double-netting closed from 5.8 pts short of the market's 1.034 to
  1.5; the PY2024 cliff crossed ($113.6 → $0); the undated cohort back in the floor-capped
  regime (995 candidates / 79.7 GW fail, every one capped). Released: 477.4 MW of coal at the
  2022 bridge at 1.1 % plant-grain precision (D32's random selection at one sixth of the
  pre-declared size, P5 MISS); `retire.total_gw` 9.799 → 10.276 (−40.8 %, FAIL both); the
  BLK-10 backstop's 2.4 GW gas_ct no longer fires (`add.by_tech.gas_ct` FAIL → PASS,
  `add.shares.gas_cc` PASS → FAIL by denominator arithmetic). **Arming limbs (a)(b)(d) MET,
  (c) NOT MET BY THE LETTER** (a share row moved) while its rationale — a second object moving
  the position — is absent; the lane reports both readings and does not override its
  pre-registration → **card C-11**. **Rider (d), NEISO leg 7 (Q36): `neiso-t1h-d45r-datesoff`
  reproduces the D37 control to the decimal (P16 HIT; 13 src commits inert for NEISO) and
  REFUTES P17's counter-example limbs — at the shipped lever the dates flip improves or holds
  every gated retirement row (coal econ 0.791 → 0.534, recall 4/6 → 4/6 with plant-grain UP,
  false-retire 4.410 → 3.182). Q30's default has NO NEISO-side counter-example; D46's recall
  loss belongs to the lever-ARMED pair.** Card C-7 is CLOSED on the merits. Records rider
  (a)–(c),(e) done (Q37 rubric v1.1; `-pre-d46` stubs; NEISO golden → GOLDEN-3). Routed:
  the admission cap's horizon headroom (~0.4 GW accredited where 1.3–4.2 implied — to the
  floor-regime lane), the backstop-after-storage ordering (P6 MISS), the 2023/2025 ledger
  positions not reconstructing from their entering fleets (+3,498 / −7,455 MW raw; a
  position-observability question, queued-named), oil unscreened after 2022 (still open).
- **D52 — LANDED** (PR #4730, `FINDING-capx-d52-2026-09-04.md`): with both gates ON the NYCA
  requirement IS NYSRC Table D.2's UCAP requirement to <1 MW (34,559 / 33,398 / 34,058) and the
  entering position moves **+9.4 / +5.2 / +7.3 pts LONG → −2.6 / −1.8 / −0.6 pts**, inside
  D45 §6's ±3 band every year, LOYO 3/3; the OFF gap was larger than D45 §5.2 read because the
  screens price adequacy on the seam's growth-scaled 2024-weather peak, 2.1–3.6 GW under the
  published bar in EVERY year (a D45 correction, confirmed on the ledger). At the curve-OFF
  default the A/B is **byte-identical on every FC-3 row** — zero cost. **The conditional probe
  RAN: P9 (c) YES / (a) NO / (b) NO → the curve stays OFF (self-executing).** But the object
  moved: the 2023 screen L3 collapsed at $0 now pays $63.34 and fails nothing; the over-fire
  relocates to the 2025 screen at the 2025/26 vintage's $28.65 (market $51.36; **Zone J
  $141**) — 1,801 MW of downstate gas_st, sized by the 2025 admission budget as PREDECL P5 said.
  Two recommendations: **ARM the two requirement gates as NYISO's default (card C-12)**; keep
  the curve OFF and route the **locality half** (D45 §5.2.4 item 3) first, then the 2025/26
  vintage / 2025 SOM transcription check, then re-run the same P9 → **D59**. Routed item 4
  (the LP-basis `peak_demand_mw` / `adequacy_requirement_mw` ledger fields are not what the
  screens consume) — **director's call, taken: the seam fields stay ADDITIVE, nothing is
  renamed; re-basing the I7/I12 verdict rows on the seam is a scorer change that needs its own
  pre-declared records lane under the cross-lane re-grade rule — queued-named, not issued.**
- **D54 — LANDED** (PR #4746, `DESIGN-capx-d54-pjm-clearing-half-2026-09-05.md` +
  PREDECL): the mechanism stated buildable without design choices — per-unit offer = max(0,
  going-forward cost − E&AS net revenue) ÷ accredited MW, capped at the MSOC form; the stack
  (screened thermal at its offer, everything else a $0 price-taker) cleared against the DY's
  VRR curve on D48's basis; cleared units paid, uncleared $0; the screen's failing set IS the
  uncleared set (§3.5 identity); census recovered exactly when every offer is $0 or the market
  is short. **Zero DOF.** The zero-solve instrument on the committed ledgers puts the cleared
  position within **0.7 / 1.0 / 2.6 pts** of the published cleared position and the price at
  **1.7× / 2.4× / 5.5×** published — because the gas-CT / gas-ST / oil fleets carry exactly
  zero E&AS margin in the hindcast prices (D45 §1(i)), ~65 GW of offers sit above the
  published price where the record shows 9–20 GW uncleared. The design is pre-declared as a
  MEASUREMENT of the E&AS operand; a build that lands on the published price without an
  operand change is REFUSED (PREDECL §4). Seam: one generic per-ISO field
  `capacity_market_supply_clearing_by_iso` (PJM-scoped by registry, rule 25; requires the
  curve gate); A/B arms A (D48 ON + clearing ON, the D48 §8 configuration) and B (clearing on
  HEAD's basis); seven STOP conditions. §4.7: D53's gate needs no design change (gated units
  become $0 price-takers). §4.9: NYISO's clearing half is a supply-census question (D52/D59),
  NOT this design. **→ D57 (the build) issued.**
- **D55 — LANDED** (PR #4747, `FINDING-capx-d55-2026-09-05.md`): the key-1 float-noise defect
  real, repaired to the class constant, heterogeneous-pmax test added, `plant_release_precision`
  reported-only row shipped (13.5 % on D31 = the D32 anchor) — and on the recipe every MISO
  T1-H leg runs **the fix changes NOTHING**: `miso-t1h-d55-keyfix` is byte-identical to D46
  (same key `eff2c890746ec966`; 21/21 FC-3 rows; HOLD) because the 2022/2023 floors retain
  every failing unit and an order over a fully-retained set is unobservable. Where a floor did
  release (D31 dates-OFF 3,684 MW; D51 477 MW) the replay shows the fixed key turning the
  release into the CO2 tail (Schahfer, a real exit, in; White Bluff / Independence out; Marion
  first but 2.4 MW). **Stale-golden list EMPTY** — every golden is a backcast capture and a
  backcast has no capacity evolution (corrects the charter's "goldens go stale" premise). Routed:
  the screen-year `co2_rate` not persisted in `pipeline_events` (a ledger-schema addition,
  queued-named); 4 pre-existing `test_ff_readiness_battery.py` failures on main, untouched.
- **D50 — CHECKPOINT, NOT COMPLETE** (PR #4728): the field `ccs_retrofit_capex_co2_scaling`
  built default-off + CHP hosts excluded (seam 2) + the p55470 flag; PREDECL + Addendum A
  (the scaled-ceiling census). **ERCOT arm `ercot-t1f-d50-ccscapex`: ZERO conversions vs the
  control's 2,741.8 MW** (every converting host at 0.82–0.94 of the scaled bar; fleet /
  retirements / builds identical; HOLD → HOLD). **NEISO arm `neiso-t1f-d50-ccscapex`: the
  3 GW/yr cap STILL BINDS under RGGI** (8,961.5 vs 8,942.6 MW; a per-tonne island cannot
  unbind a per-tonne credit); what moves is WHO converts (CC_CHP rows gone, MW-weighted CO2
  rate 0.608 → 0.550 in 2028; PROMOTE → PROMOTE). **OWED: the PJM arm (`pjm-t1f-d50-ccscapex`,
  pre-declared 0 conversions vs 3,584.7 MW, seam 2 load-bearing for 722 MW of CHP rows — no
  key exists), the blast radius (§6), the arming recommendation (§8), and
  `FINDING-capx-d50-2026-09-04.md` itself — which all three ISO shards' matrix cells CITE BY
  NAME and which does not exist on main** (a dangling citation, recorded against the lane).
  → **D50-R** (completion; Opus). Nothing arms.
- **D53 — IN FLIGHT, a graded checkpoint** (branch `claude/capx-d53-sector-gate-redt3y`, 4
  commits, unmerged; design + build + both legs solved): `retirement_sector_gate` default-off;
  on the bare recipe the arm reproduces D46 to the decimal on every retirement row (P1/P3
  HIT) while the screen's failing census drops **1,497 units / 76.75 GW → 410 / 17.46 GW with
  not one sector-1 row** (P2 HIT; 1,298 units / 109.98 GW gated); the rider (gate + D51's
  ratio) fills the same 2022 headroom with **367.3 MW drawn from Warrick (sector 3) and Big
  Cajun 2 (sector 2) at 99.8 % plant-grain precision** where D51 filled it with three utility
  coal plants at 1.1 %; `false_retire` 0.0; recall 14 → 15/19. **All four §6 limbs MET,
  recommendation ARM** — served as a card when it lands on main, not before (grade by
  content). Two template tokens (`MET_ROW`, `§6_PARAGRAPH`) are unfilled in the finding's §6
  table — the lane should fill them before merge. Routed: the PJM leg (→ **D58**), the
  additions-screen mirror and the CHP-host screen (queued-named), the unknown-sector fail-open
  set (records), the `forecast_verdict.py` HOLD exit code stopping `set -e` pipelines
  (harness records item).
- **D56 — NEVER LAUNCHED** (no branch, no commit, marker byte-unchanged: `complete` =
  {ERCOT, NEISO, PJM}), **and its target moved**: NYISO promoted nyiso-188 → nyiso-189 (§0ag.2),
  CALIBRATED → CALIBRATED. The charter's own STOP clause covers this (re-verify on the new
  keeper; re-key per D-5(b)); re-verified here: **`2026-09-05-nyiso-189-steam-identity` reads
  CALIBRATED** (C3c the lone ledgered caveat, 3/0/4 h vs 10/13/42 h > $300). **→ D56-R
  re-issued on nyiso-189** (relaunch protocol: fresh from the committed charter), carrying the
  Z-4 frontier question as card **C-10**.

**2. GRADED — owner track (§2 rows):** **CAISO → `2026-09-05-caiso-246-b1-spot`** (#4751): the
2025 hub-overlay coverage gap was a GATE ARTIFACT; the arm covers Sep–Nov 2025 on the measured
daily spot the keeper already prices gas at, the F923 fallback retired from the training window
(0 reachable months in 36), three of six post-solve predictions falsified at full size;
re-verified NOT-YET on C3a alone (2024 +12.3 / 2025 +11.4 %). **Re-keyed its own gate-(a)
stamp** (the first CAISO promotion since R-T to carry step 4). caiso-245 (zero LP): the
published RA-import allocations do NOT carry the north over-import (LSEs hold 45–48 % north,
the MIC share) — the stop rule fired, the re-split arm not built, the object moves to "RA
import CAPABILITY forced as ENERGY"; its `ra-import-allocations` intake left the frozen
`test_clean_io` roster un-refreshed (repaired here, §0ag.4). **MISO →
`2026-09-05-miso-213-layering`** (#4748): the mean-zero zonal basis was fully redundant on
923-priced cells (the print path prices 100 % of MISO gas capacity-hours), repaired as one
default-off field, single-delta A/B vs the keeper itself, every kill silent, all six object
gates moving South→North; NOT-YET on C3a-2025 alone, −12.38 → −11.75 %. **Stamp NOT re-keyed
→ the ninth promoter miss.** **NYISO → `2026-09-05-nyiso-189-steam-identity`** (#4743): the
owner's Bethlehem form B2 (`egrid_steam_collapse_heat_rates`, 38 CCs) built and A/B-solved;
CALIBRATED → CALIBRATED, no rejection-rule flip, every regression stated; re-keyed its own
stamp (the fifth NYISO promotion in a row to honour step 4). **Audit v27** (#4740): job 0
pre-empted by this desk; flip set 5 → **3 of 6** (ruff format · fast tier · rule-22) — all
three in-flight lanes' loose ends; **Z-4** (R-AG / Q38 double ruling, the frontier leg) and
**X-6b** (orphaned `scored_at_sha` stamps from rebase-before-merge on the D51/D52 branches)
routed to this desk; **R-AG recorded for the first time in the audit board's own v27 entry**
(it is not in this ledger's §3 until now — §0ag.5). PERF-B s3 landed (#4745/#4752; watch only).

**3. THE QUEUE, RE-DERIVED (every routed list at the pin):**
- **D54 → D57 (issued).** D48 landed with "arm WITH the clearing half"; D54's design is
  buildable; the E&AS operand is the pre-declared measurement. Fable, pjm, the largest arming
  consequence in the chain.
- **D50's owed half → D50-R (issued).** PJM arm + blast radius + the finding the cells cite.
  Opus (pre-declared execution).
- **D56 → D56-R (issued).** Same charter on nyiso-189; C-10's answer rides it.
- **D53 item 1 → D58 (issued, released-conditional):** the PJM sector-gate leg on D48's basis,
  dispatch strictly after D53 merges AND after D57 lands (both write the PJM shard).
- **D52 route → D59 (issued):** the NYISO locality half — design-first, because the shipped
  Part-B gate only COLLAPSES payment in a LONG zone; NYISO's object is a SHORT locality paid
  its own curve (Zone J $141 vs NYCA $28.65), so the instance needs the per-locality demand
  curve evaluated at the locality position — NYISO's real spot mechanism (D54 §4.9).
- **Queued-named, not issued:** the D48 DR-convention probe pair (V-only / D-only); the VRE
  ELCC two-date limb; D51's position-observability question (2023/2025 ledgers); the
  `pipeline_events` `co2_rate` ledger field (D55); the I7/I12 seam re-basing records lane
  (D52 item 4); D53's additions-screen mirror + CHP-host screen (after D53 lands); the NYISO
  t3 campaign (after D56-R + C-12 land — a 25-year golden on the pre-arm requirement basis
  would be stale on registration); the 2025/26 NYISO curve-vintage / 2025 SOM transcription
  check (records; folded into D59 as a zero-solve step). Dispersion siblings unchanged, LOW EV.
- Nothing else: D46/D47/D49/D45-R lists fully dispositioned; the C-7 question closed by D51
  §4; cross-ISO `state` defect (caiso-243) is the backcast lanes'.

**4. RECORDS ACTS THIS SITTING (zero solves):**
- **Gate-(a) MISO row re-keyed** `miso-210-clock` → `2026-09-05-miso-213-layering` under Q34
  — the ELEVENTH guard firing, the NINTH promoter miss since R-T (caiso-246 and nyiso-189
  re-keyed their own in the same window). Targeted string edit of exactly six leaves
  (`detail` head + tally sentence, `read_live_at`, `corrected_by`, `derived_at_sha`,
  `derived_at_date`, `derived_by`) — the file is not round-trippable through `json.dumps`;
  `git diff --stat` 6/6 lines; guard exit 0; `test_gate_a_provenance.py` 13 passed. **v27's
  routed leaf repaired**: the MISO `read_live_at` now reads the pin (`e75250c7`) instead of the
  r#32 pin `2b0b8796` the r#35 re-key left behind. CAISO's and NYISO's `read_live_at` /
  `corrected_by` leaves are the promoting lanes' own (their `detail` text is current); left as
  their record.
- **The orphaned Fast-tier red repaired — a boundary call, disclosed.** `test_clean_io.py`'s
  frozen `ALL_DATATYPES` roster lacked `ra-import-allocations` (the caiso-245 intake, whose
  branch is merged and deleted — no lane owns it); one roster line + a dated comment, test 27
  passed, ruff clean. Not lane work and not `src/`; done because the flip set (Y-1) was held
  red by a file nobody would return to. **The ruff-format red (`test_capacity.py`, D51/D52's)
  is NOT touched**: D53's branch carries that file formatted (verified by `ruff format --check`
  on the branch blob), so it clears on D53's merge, and a second writer on it would collide.
- **The X-6b process seam is adopted as desk doctrine** (below, and in every charter from D57
  on): score and register AFTER the final rebase; a rebase after scoring re-stamps
  `scored_at_sha` by an artifact-only re-score before merge — an orphaned stamp names a commit
  that no longer exists anywhere.

**5. CARDS (presented in the closing message; unruled at the entry's writing):**
- **C-10 — the frontier leg of the NYISO re-declaration (Z-4).** R-AG (22:20Z 09-04: route
  the re-declaration to the calibration director for a recommendation; no audit lane edits the
  marker) and Q38 (23:18Z: re-declare now via D56) coexist; neither cites the other; R-AG is
  recorded only in the audit board's v27 entry and, from here, in §3. This desk's
  recommendation, as R-AG asked: **re-declare `complete` AND `frontier` together on
  nyiso-189** — the 2026-08-30 withdrawal removed both, the other three `complete` ISOs hold
  both, and a `complete`-only re-entry leaves the four-instrument test split on the frontier
  leg by construction. Options: (A) both, via D56-R (recommended); (B) `complete` only, and the
  four-instrument test reads `frontier` as optional; (C) decline both. D56-R carries the
  frontier limb CONDITIONALLY on this ruling; absent a ruling it writes `frontier_basis` = NONE
  CLAIMED as chartered.
- **C-11 — arm D51's `adequacy_accounting_ratio_dated_net` for MISO?** Limb (c) fails by the
  letter (a share row moved by denominator arithmetic) while every substantive test holds.
  Recommendation: **ARM** — a rule-23 identity re-derived on the fleet Q30 actually uses, zero
  DOF, rule-14 sign (exits harder in 2024), the D49 double-netting closed. Cost if armed: bare
  `miso-t1h` re-solve (~25 min) with the D46 record preserved at `-pre-d51`, plus the MISO t1f
  leg (~65 min) whose I7 FAIL 2026–2029 D45-R measured on the 0.8546 ledger. Options: ARM /
  HOLD-and-route (the letter) / DECLINE.
- **C-12 — arm D52's two requirement gates as NYISO's forecast default?** Recommendation:
  **ARM BOTH** — published Table D.2 construction, LOYO 3/3, shipped-default cost exactly zero
  (FC-3 byte-identical), golden requirement +0.24 %. Cost if armed: bare `nyiso-t1h` (~12 min)
  + `nyiso-t1f` re-measure, priors preserved. The curve stays OFF regardless (P9 failed,
  self-executing). Options: ARM BOTH / ARM item 1 only / DECLINE.
- **Next cards, not served:** D53 arming (when it lands — all four limbs met on the branch);
  D48+D57 joint arming (after D57's result); D50 arming + blast radius (after D50-R).

## 0af. Refresh #35 (2026-09-04, main HEAD `a35c9f9b`) — nothing capx lands (four lanes running); NYISO's keeper reads CALIBRATED for the first time and re-opens the marker question; the queue re-derived from every routed list yields three more lanes; the tenth gate-(a) firing is re-keyed under the standing duty

**0. FIRST ACT.** Handoff claim (§0ae = r#34 + amendment 1) matched the top entry; this is r#35.
Delta `8f98399b..a35c9f9b`: 12 commits, 5 merges, zero capx (D48 Phase 1, D50, D51, D52 all
owner-confirmed RUNNING — graded in flight; nothing to grade until they push). My r#34 branch
merged (#4723) and deleted; recreated off `a35c9f9b`.

**1. GRADED — owner track:**
- **NYISO → `2026-09-04-nyiso-188-combined` — CALIBRATED** (re-verified here: target grade 7 of
  8, fails 0, C3c the lone ledgered caveat reclassified by the v3.3 standing rule). Three
  objects in one lane: the Astoria routing's remaining artifacts re-derived at zero parameters;
  the registered `cc_capacity_reconcile` flag (per-plant CC_REGULAR LP capacity bounded at the
  CAMPD p99.9 demonstrated peak, −740 MW over 12 plants) moves C1-2024 CC_REGULAR +3.80 → +2.05
  TWh and C3a-2025 −10.3 → −6.9 %, every regression in band and stated (C3a-2023 +4.8 → +7.9 %);
  Bethlehem 2539's heat rate handed to the owner as a two-form decision. **The lane requested
  NO marker and said so explicitly** ("whether a CALIBRATED keeper re-opens the `complete`
  question (withdrawn 2026-08-30) is" the owner's). The withdrawal record's own re-entry
  clause: *a NEW explicit owner declaration once the designated keeper again scores
  CALIBRATED.* The condition is met for the first time. **→ card C-9.** Consequences if
  declared: NYISO's validation-tier (2020–2022) authorization returns (nothing was ever spent
  under the 2026-07-31 marker); forecast gate (a) flips to PASS (NYISO would hold (a) + (b)
  again — `nyiso-t1f` is PROMOTE — the state it briefly had at r#5); D-5(b) re-key duty
  attaches to every future NYISO promotion (four in two days this week). The gate-(a) stamp
  was re-keyed by the lane itself (the fourth NYISO promotion in a row to honor step 4).
- **MISO → `2026-09-04-miso-210-clock`** (#4724): the max-gen emergency-tier registry placed on
  the model's CST clock (EST→CST, the miso-204 clock defect reaching the solve path), single-
  delta A/B, all ten gates pass, blind scorer; re-verified NOT-YET on C3a-2025 alone (−12.4 %).
  **Stamp NOT re-keyed — the eighth promoter miss since R-T; re-keyed here under the standing
  duty (Q34), the guard's TENTH firing, six leaves, exit 0.** Disclosed: `program-status.json`
  is no longer byte-round-trippable through the serializer this desk used at r#32/r#33 (a
  lane re-dumped it with different settings), so this re-key was a targeted string edit of
  exactly the six leaves — verified by the guard and by `git diff --stat` (5 lines).
- **caiso-244** (zero LP): the CAISO import LEVEL object LOCATED — the +8.4/+8.7/+5.3 TWh net
  over-import is entirely the NORTH corridor (PNW +11.3/+10.7/+8.8; DSW UNDER-imported); the
  `PNW_hydro_base` FLOOR alone exceeds the measured PNW net import by +8.3/+7.7/+5.3 TWh; the
  four fitted spot capacities are not where the level sits. Also the on-recipe re-measure of
  caiso-242's ratios (1.08/1.22/1.19, a third of the voided size) and the one sanctioned
  fleet-only recipe reconstruction (`replay_keeper.run_year_kwargs`). Keeper unchanged.
- **Stage-0 NYISO re-capture** landed (R-AF), already one promotion stale at close; **nyiso-188
  CI repair** (parity allowlist for the four bit-identity control bundles).

**2. THE QUEUE, RE-DERIVED (the amendment-3 step, every routed list at the pin):**
- **D32 R3 → D53 (issued).** D32 §4.3/§4.4 is the structural finding this program has been
  circling: **exits are 88–92 % regulated-utility (IRP) decisions while the model applies a
  merchant net-revenue screen to the whole fleet** — "the screen models a decision most of
  these owners do not face", which is why it fails 77–92 % of a fleet 97 % of which stayed,
  and why the reliability floor throttles at a 96 % masking share. D32 named the sector gate
  (C5: EIA-860 `Sector` per unit, published, forward-regenerating, a partition with no weight)
  and routed a design doc (R3); Q30/D44 since armed its companion C3. **Precondition met, no
  machinery exists anywhere** (grep: no sector gate in spec, config or screen). With dates ON,
  D49 measured the undated cohort still failing 73–77 GW at $0 capacity, all `entry_capped` —
  the gate is exactly what decides which of those face the screen at all. Rule 1: the right
  market structure. Fable.
- **D45 §2.3 item 3 → D54 (issued, docs-only).** The PJM clearing half — clear the VRR curve
  against the fleet's net-ACR offer stack (Manual 18 §6 / MSOC) rather than evaluate it at the
  census — is the last structural piece of the D6/D28 chain and D45's own §9 successor. Its
  DESIGN and pre-declaration need nothing from D48; its code and solve inherit D48's basis
  (the PREDECL says so) and are gated on D48 landing. Fable.
- **D32 R2 + R4 → D55 (issued).** The float-noise defect in `_floor_retention_merit` key 1 is
  STILL in the code at `a35c9f9b` (the per-unit quotient, not the class constant), so the
  CO2/heat-rate tie-breaks still fire only within rounding buckets; the release-precision
  scorer diagnostic (R4) never landed either. Correctness, zero DOF, small. Opus.
- **NYISO locality (D45 §5.2.4 item 3)** — QUEUED-NAMED behind D52 (position first). **NYISO
  t3 campaign** — a card only after C-9 and D52 (a 25-year golden on the pre-D52 requirement
  basis would be stale on registration). **Dispersion siblings** — unchanged, low EV.
- Nothing else: D46/D47/D49 routed lists are fully dispositioned (§0ae.3); caiso-243's
  cross-ISO `state` defect is the owner's backcast lanes' (ISO-gated fields, forecast keys
  unmoved).

**3. CARDS:** **C-9** — re-declare NYISO `complete` on `2026-09-04-nyiso-188-combined`
(re-declare now via a records lane / wait for keeper stability / decline).

**AMENDMENT 1 (the C-9 answer, same sitting):**

- **C-9 → Q38: RE-DECLARE NOW via a records lane — D56 ISSUED** (pack §D56; Fable — a marker
  consequence). The declaration is an OWNER act executed by the lane per the withdrawn
  block's own `reentry` clause ("a NEW explicit owner declaration … on a designated keeper
  that scores CALIBRATED") and the CLAUDE.md procedure: a `complete.NYISO` entry with
  `keeper` = `keeper_at_declaration` = `2026-09-04-nyiso-188-combined`, `determination`
  re-verified from committed artifacts (never a solve), `by` citing this ruling verbatim, the
  withdrawn block preserved whole beneath (the file's own nesting convention, as the 2026-07-31
  re-declaration did with the 2026-07-19 withdrawal); `audit_keepers` M1a/M1b PASS; the
  forecast gate-(a) row re-derived (NYISO flips FAIL → PASS on the literal test — NYISO holds
  (a) + (b) again, the lead it held at r#5 and lost at r#12); the board's headline /
  gate_reading / `marker_complete` rewritten with byte-identity asserted everywhere else.
  **What the marker grants:** the validation-tier (2020–2022) touchpoint authorization
  returns under rule 22 (nothing was ever spent under the prior marker); it grants NOTHING
  on the locked tier (`final` stays empty; the freeze covers it). **What it obliges:** every
  future NYISO promotion carries the D-5(b) re-key + determination re-verification duty —
  four promotions in two days this week is exactly the cadence that makes M1 load-bearing.
- **Not in D56, deliberately:** a NYISO t3 campaign. With (a) + (b) passing NYISO becomes a
  §2.1b candidate, but D52 is re-basing its adequacy requirement right now and a 25-year
  golden on the pre-D52 basis would be stale on registration. **That card is served when D52
  lands**, not before.

## 0ae. Refresh #34 (2026-09-04, main HEAD `8f5cb32c`) — the once-only clearing-half charter is CLOSED on record; D49 turns two "walls" into two named construction defects; the re-measure is done except one 7-minute control; three per-ISO repair lanes are ready with sources and zero free parameters

**0. FIRST ACT.** Handoff claim (§0ad = r#33, three amendments) matched the top entry on
`origin/main`; this is r#34. Delta `a8464861..8f5cb32c`: 66 commits, 22 merges; my r#33
branch merged (#4683) and deleted; recreated off `8f5cb32c`. Owner states D48 is still
running — graded IN FLIGHT regardless of what the branch list shows (r#20/21 protocol).

**1. GRADED — capx lanes (four landed, one in flight, one leg owed):**

- **D45-R — LANDED, COMPLETE; the once-only D6+R3 question is RETIRED** (PRs #4690/#4697/#4708;
  D45 finding §4–§9 filled in place, 666 lines; PREDECL `PREDECL-capx-d45r-2026-09-04.md`
  pushed before the first solve; **8/8 pre-declared cache keys realized**; 16 gradable items:
  6 HIT / 9 SPLIT / 1 MISS, plus D45's own untested half 3 HIT / 3 SPLIT). What it established:
  - **PJM (L1 replay, L4 control):** the dates channel RE-ROUTES coal out of the cap-bound
    economic cohort (18.1 → 11.4 GW economic; recall 16/20 → 17/20) — the D46 MISO reading
    reproduced at PJM, and the one clean MISS of the lane's own pre-declaration (P2′ said
    "adds"). L4 at the flat $77.43 anchor fails NOTHING (every exit is the dates channel,
    6.5 GW) while curve-ON retires 11.4 GW more — the pair brackets the clearing half from
    both sides. **Verdict: the $0 is a basis artifact sitting AT the market's cleared quantity
    once the auctions' own UCAP design and the filed dates are honored; the curve stays ON;
    no PJM default moves.** Successor: D48 (basis) then the clearing half (§2.3 item 3).
  - **NYISO (L2 live curve-OFF → bare `nyiso-t1h`; L3 curve-ON probe suffixed):** at the flat
    $110 anchor the retirement screen is INERT (zero economic events; every exit exogenous);
    the total-band FAIL is a TARGET move (the actuals file was rebuilt 1.488 → 1.711 GW on
    2026-09-02). **The D28 latent flip fires at +189 %** (3.5 GW downstate steam retires in
    the 2023 screen at $0, then the fleet goes SHORT and pays $69/$39) **and it is a POSITION
    artifact first, the curve second:** at the PUBLISHED position (1.043) the same curve pays
    $47.57 within 4 % of the real $49.32 spot. The model's SUPPLY is the market's within
    0.6 GW; the REQUIREMENT is 1.9–2.2 GW low in 2021–2024 — **dominantly the PEAK BASIS**
    (the hindcast sets the requirement on its realized weather-year peak, NYSRC on the
    ICAP-market FORECAST peak), plus the single 2025-26 vintage factor (2.1 pts in 2024) —
    and NYISO's locality market (NYC clears at 3–4× NYCA) is represented as one NYCA-wide
    position. **Pre-stated arming conditions: 0 of 3 met → DO NOT ARM; the FF-3D flip stays
    withheld** behind §5.2.4 repairs 1–2 (requirement on the published forecast peak;
    per-capability-year adopted IRM + derate — both zero-DOF, both sourced) then 3 (the
    locality LCRs as NYISO's `capacity_deliverability_limits` instance). → **D52.**
  - **The re-measure closes (Stages 2 + 3):** `pjm-t1h`, `nyiso-t1h`, `neiso-t1h` (shipped
    posture — the Net ICR lever raises the bar ~5 GW; shipped reads 1.21/1.18/1.02 long and
    retires 6.8 GW vs 4.4 armed), `nyiso-t1f` (PROMOTE holds, the board's first NYISO t1f),
    `pjm-t1f` (HOLD; I7 fails four years, backstop share 43.9 % CAVEAT → FAIL as the gas_ct
    ladder absorbs 5.5 GW of dated exits, **CCS clears at carbon 0 on the corrected
    constants where D41 measured none**), `miso-t1f` (HOLD on a different basis — the
    base-year firm opens 11 GW short, backstop builds 16 GW + storage 4 GW/yr, share 33.6 %
    FAIL). **Measured: PJM t1f 28.2 min, MISO 65.2 min** — inside the 2 h STOP, and the
    board's 7.3 h / 10.1 h were 15× / 9× high. Every prior preserved at `-pre-d45r`; three
    dead D45 `VERDICT_MAP` rows re-pointed; the §0ac.7 stale set CLOSED for every key except
    CAISO's. **Leg 8 (conditional CAISO) STOP-and-routed correctly: CAISO's forecast cache keys
    at HEAD EQUAL D46's committed bundles** — the caiso-241/243 promotions changed the backcast
    keeper without changing any forecast default, so **the "keeper-vintage axis" bites only
    when a promotion moves a forecast cache key**; §0ac.7's framing was over-broad and is
    corrected here.
  - **OWED: leg 7, the NEISO dates-OFF paired control** — pre-declared in the D45-R PREDECL
    §4.2 (P16: reproduces d37-control up to HEAD drift; P17: the flip alone at the shipped
    lever reproduces D46's re-routing, i.e. the NEISO regression is the flip's, not the
    lever's) but **never solved, registered or mentioned in the finding**; no
    `neiso-*-datesoff` bundle on main. Seven minutes, and it is the one measurement that
    decides whether Q30's default has a NEISO-side counter-example. → **card C-7.**
- **D49 — LANDED, both halves, zero solves** (PRs #4700/#4706). **Half 1: (c), a construction
  seam.** Every one of ERCOT's 14 converting rows clears at the HOUR CEILING because the
  §45Q credit scales with the host's CO2 flow per MWh (regular-CC hosts at 8.2–11.3
  MMBtu/MWh earn $18–24/MWh against a ~$16.6 bar) **while the capex is the ATB capture-island
  increment for an H-class reference host, charged flat per kW** — the same machine is
  credited for 40–90 % more CO2 than it is charged to capture. Run identically on PJM's and
  MISO's own units, **99 % / 100 % of their 2028 converting MW clear on the corrected
  constants too** (there through the CHP hosts' per-electric-MWh rates) — **D41 §4.3's
  zero-clearing was a class-average artifact and never held at unit grain**, and D46 §4.5's
  "does not extend past PJM/MISO" is bounded the other way. Physical plausibility is
  satisfied by the seam, not a band. Routed as a repair lane with three zero-DOF seams:
  capex ∝ captured CO2 against the ATB reference host; CHP hosts excluded or rated
  electric-only; the p55470 (hr 34.75) curated-sheet row flagged. **Blast radius: re-keys
  every forecast config (the D41 §6.2 precedent) — to be measured before it lands.** → **D50.**
  **Half 2: neither H-WALL nor the D43 wall mirrored.** The MISO undated cohort's margins are
  bimodal and never within reach of the bar: in 2022/2023 76.6/73.0 GW of 98.1 GW FAIL on
  energy-only margins ($0–20 vs bars of $21–58.5, capacity term $0 at position 1.032 on the
  vertical vintage) and **every failing MW is `entry_capped` by the admission floor**; in
  2024/2025 NOTHING fails because the capacity term alone ($111–117, then $448–473/kW-yr at
  0.949 on the RBDC plateau) exceeds every bar. Dispersion mirrored onto exits moves 0.00 GW
  in the exit direction. **The margin-side object is the POSITION, netted twice:** D31's
  0.8546 supply-accounting ratio was identified on a census fleet that still carried the
  2021–2023 real exits the PRA had already dropped; Q30/D44 now removes those same plants
  explicitly (5,961 MW announced + 3,838 derate in the window) and the ratio still applies,
  so the consumed position falls 5.8/6.9 pts SHORT of the market's own and the vertical
  2024 vintage pays a $123/kW-yr cliff to 98 GW. Repair: re-identify the ratio net of the
  dated exits on the same PRA overlap years — rule 23, zero DOF, back-of-envelope ~0.88/0.91
  and the 2024 position back near 1.03; sign: the 2024 term returns to $0, exits HARDER in
  2025. It returns the cohort to the floor regime, where D32's objects decide composition.
  → **D51.** Also recorded: oil is not being screened after 2022 (3.5 GW stays in the fleet,
  549 rows fail only in the bridge); the vertical-vintage step's x = 1.0 location is what the
  screen is sensitive to. **D49 §3, the transferable sentence:** *both screens fail the same
  way — a term that should scale with the unit is held at a class constant, and a price
  object without a body supplies the hours.*
- **D47 + D47b — LANDED** (PRs #4691/#4699): GOLDEN-3 FC-7 FAIL → **PASS** by an attestation
  pre-declared before it existed, exactly one row moved, HOLD unchanged (`neiso-t3-pre-d47`
  preserved). The `-pre-d46` table, MEASURED rather than restated: `neiso-t1f-pre-d46` carries
  a FOURTH axis (the R-A storage-entry arming landed after its prior solved); `miso-t1h-pre-d46`
  was missing from D46's enumeration; `neiso-t1h-pre-d46` is genuinely single-axis but both
  ends sit on a posture the model does not ship (now retired by D45-R L5). **D47b refused this
  desk's "~45–90 min" figure**: D46's 7–10× was span-confounded (the pre-D46 `c_cost` fields
  were 25-year full-horizon numbers, the D46 legs 5-year) — real factor ~1.7×, so it projected
  PJM ~4.2 h / MISO ~5.9 h. **D45-R then MEASURED 28 / 65 min.** Both desks were wrong in
  opposite directions; the board now carries measured 5-year figures for all six ISOs and
  says the 25-year horizon is unmeasured except NEISO. Routed: `ercot/caiso-t1f-pre-d46` have
  no resolved cache key (un-diffable stubs); rubric §5 has no limb for a pre-declared
  follow-up attestation; the board's NEISO `golden` field still describes GOLDEN-2.
- **D48 — PHASE 0 LANDED, PHASE 1 RUNNING** (PRs #4707; owner-confirmed in flight).
  `pjm_accreditation_design_vintage` + `pjm_demand_response_supply` built default-off on one
  seam (`accredited_firm_capacity_mw(config, accreditation_year)` — CR-1 position, floor,
  backstop, ledger and per-unit capacity payment move together or not at all), the BRA DR
  series intaken, byte-inertness proven, PREDECL pushed. **The PREDECL corrects D45 §2.2 and
  this desk's D48 charter:** the "2–4 points past the zero-cross" was a mis-paired ratio
  (net supply over an un-netted requirement, VRE on Manual 21 instead of the ledger's
  credits); on ONE consistent basis the census position sits **7–11 points past** it —
  between the market's committed (1.05) and offered (1.13–1.22) positions, which is exactly
  where a census-of-everything-installed should sit and why the price forms at the cleared
  quantity. So the devintage is expected structurally correct and **near-inert on FC-3**; its
  value is that the clearing-half lane inherits a position it can clear against. P9-style
  flip condition pre-stated; the A/B registers suffixed; the default flip is the owner's.

**2. GRADED — owner track:** **NYISO promoted TWICE** — `nyiso-186-astoria-identity` (the
Astoria split-facility identity; the 2024 CC_REGULAR excess is three plants, no plant-level
hypothesis fires) then **`2026-09-04-nyiso-187-astoria-routing`** (55375 CT3/CT4 → 57664
remap, caiso-196 form; re-verified NOT-YET {C1-2024 CC_REGULAR +3.80 TWh, C3a-2025 −10.3 %,
C3c}) — **both re-keyed their own gate-(a) stamps** (the streak is broken; the guard reads
6/6 at HEAD). nyiso-187's merit-position decomposition: the CT/steam deficit is
**OUT-OF-MARKET commitment** in every class-zone (bucket B 0.57–0.89 — capacity the market
ran would not clear at the price the market itself paid, on the model's offer; no measured
input wrong on its source). **CAISO → `2026-09-04-caiso-243-b1-f923`** (re-verified NOT-YET
C3a alone, 2025 +15.5 → +14.4 %): the F923 low-volume defect repaired at root — **`bins_to_fleet`
never passed `state` to `Generator`, so `FleetArrays.state` was empty on 100 % of the fleet
and the donor-count guard was skipped fleet-wide; THE SAME ON PJM, MISO, NYISO and NEISO**,
whose keepers all run `plant_level_fleet=True` — a cross-ISO data-integrity flag for the
owner's other four lanes (each keeper's F923 fallback tier has been silently disabled). One
solve, no control (owner's choice), gates pass, 2023/2024 bit-identical. **miso-208** (the
market ran the model's peakers, less of its coal, more of its gas — the supply-mix map),
**miso-209** (partial-derate shape inert by construction; the production extract is empty
structurally), **miso-210** and a **NYISO stage-0 re-capture** in flight. **Audit v25/v26:**
Y-4 landed, the path-filter trap CLOSED (and already fired on a records PR), the fast tier
went green, **R-AE's flip set 5 of 6 — one keeper-recipe declaration from done**; R-AF (the
stage-0 re-capture policy) is recorded nowhere in `docs/`. **PERF-B session 2** attributed
the `markup` residual (both orchestrators derive it as a residual of narrower timers) and
delivered the WS3-next charter.

**3. QUEUE STATE, re-derived from every landed finding's routed list (the amendment-3 step):**
- D45-R §2.3/§5.2.4 → **D48 (running)**, **D52 (issued)**; PJM clearing half (§2.3 item 3) and
  NYISO locality (§5.2.4 item 3) → QUEUED-NAMED behind D48/D52 respectively (each inherits a
  position it can clear against only after its devintage lands).
- D49 → **D50 (issued)**, **D51 (issued)**; D49 §5 item 2 (Stage-3 expectation: the cap binds in
  2028, efficient hosts drop) is now a D50 pre-declaration input, not a queue item; item 5
  (oil unscreened post-2022) → a MISO records flag for D51's finding; item 4 (the vertical
  cliff's x = 1.0 sensitivity) → recorded, no lane.
- D47 §6 → items 2 (stub marking) and 4 (golden field) ride D51 as a records rider; item 3
  (rubric §5 second limb) → **card C-8**; item 1 retired by D45-R L5.
- D46 §9 items 1–2 → answered by D45-R leg 7 (owed) and D49 half 1; items 4–7 closed by
  D47/D45-R.
- The model-class wall (D43, C3c, the gain): **shrunk by D49** — the entry under-build's
  dispersion term stands, but the exit under-build and the CCS wave are now construction
  defects with named repairs, not wall. Dispersion siblings stay queued-named, low EV.
- caiso-243's `state` defect → the OWNER's other four backcast lanes (recorded in §2; not a
  capx lane; the forecast fleets inherit whatever the keeper recipe carries).

**4. CARDS:** **C-7** D45-R leg 7 (running / dead → rides D51 as a 7-min rider / drop) ·
**C-8** rubric §5 second limb for pre-declared follow-up attestations (adopt as written /
decline).

**AMENDMENT 1 (the C-7/C-8 answers; post-pin delta `8f5cb32c..1cde85df`):**

- **C-7 → Q36: D45-R is DONE; leg 7 rides D51 as rider (d)** — the NEISO dates-OFF paired
  control, run exactly as D45-R's PREDECL §4.2 declared (key `5925e67c572a910f`, suffixed
  `neiso-t1h-d45r-datesoff`), graded against P16/P17. D51's rider (d) is now UNCONDITIONAL.
- **C-8 → Q37: rubric §5 gains a second limb** — *a follow-up lane may author a forecast
  attestation iff it is PRE-DECLARED before authoring, moves only the attestation row, and
  re-scores artifact-only.* Recorded as a rubric amendment in D51's records rider (e), citing
  D47 as the model case and this ruling as the signature.
- **Post-pin delta, graded:** the NYISO stage-0 golden RE-CAPTURED (re-stamped to keeper 186
  under owner ruling R-AF / board X-2 — the R-AF ruling the audit board found recorded nowhere
  now has an executing lane; NYISO's keeper has since moved to 187, so that golden is one
  promotion stale again); **miso-210** pre-registered (the max-gen clock repair, EST→CST
  placement of two armed keeper mechanisms, single-delta A/B, blind scorer — the miso-204
  clock defect reaching the solve path); **nyiso-188** opened (three objects pre-registered,
  the curate remap seam). Gate-(a) guard 6/6 at `1cde85df`.

## 0ad. Refresh #33 (2026-09-04, main HEAD `b168260e`) — D46 Stage 1 lands whole and its lesson is that the dates flip RE-ROUTES exits with a per-ISO sign; GOLDEN-3 answers D41's RGGI question nine years early; the t1f price list was an order out; D45's owed half is still missing; the seventh gate-(a) miss is now blocking the audit programme's own flip

**0. FIRST ACT.** Handoff claim (§0ac = r#32, two amendments) matched the ledger's top entry
on `origin/main`; this is r#33. The r#32 amendment-2 commit (`4c5fdac1`) merged as PR #4657.
Delta graded: `c6e46b49..b168260e`, 66 commits, 17 merges. My branch was merged and deleted
mid-cycle again; recreated off `b168260e`.

**1. GRADED — capx lanes:**

- **D46 STAGE 1 — LANDED IN FULL** (PRs #4661 `…-oe1h77`, #4668 `…-ofmvb8`; finding
  `docs/handoffs/FINDING-capx-d46-remeasure-2026-09-03.md`, 585 lines; pre-declaration pushed
  `71d3f1a6` BEFORE the first solve, graded at full magnitude: **13 hits, 6 misses, 1 split, 8/8
  cache keys realized exactly**). Every Stage-1 deliverable is on main: four T1-H legs
  (`neiso/miso/caiso/ercot-t1h`, the last two MINTED as pre-declared), three t1f legs
  (`ercot/neiso/caiso-t1f`), GOLDEN-3 on `neiso-t3`, six `-pre-d46` preservations, `VERDICT_MAP`
  at 45 rows / 0 duplicates (two superseded rows RE-POINTED rather than duplicated — the
  charter's "never edit" would have minted a duplicate dict key; the lane was right to deviate
  and said so), four matrix shards stamped with own-ISO evidence and **no verdict letter
  moved**, board refreshed only where a record moved, gate (a) untouched. **Determinations:
  none moved** (HOLD ×7, NEISO t1f PROMOTE held).
  - **The substantive result — the flip RE-ROUTES exits, and the sign is per-ISO, so it does
    not transfer (rule 25 vindicated by measurement).** MISO: identical coal exits move from
    `retire:economic` 3,684 MW to `retire:announced` 2,410 + 1,496 derate — rule 19 working,
    no exit lost — and **`unit_recall_gt300` 5/19 → 16/19, FAIL → PASS**, the batch's one
    gate-leg improvement (`retire.total_gw` 4.469 → 9.799 GW, err −0.743 → −0.436). NEISO
    (the one clean single-axis leg): the flip **loses 791.5 MW of coal economic exits and
    gains 849.4 MW of gas_cc** — recall **4/6 → 3/6**, `false_retire` 0.263 → 0.315, both
    WORSE, at an ISO whose dated set holds essentially no in-window coal. CAISO: exits rise
    into an ISO that barely retired (G3 +6.642 → +9.469, the rule-14 signature). ERCOT: the
    channel retires **exactly nothing in the hindcast** — all three filed rows are dated
    2027–2029, a **data-coverage (window) null, not a screen null** (they DO fire in the
    2026–2030 t1f window) — and it still pushed `unit_recall_gt300` from SKIP to a scored
    **0/1 FAIL** by making a target reachable it then did not retire. **A gate leg can worsen
    on an input that changes nothing** — routed item 5, worth carrying into every future
    reading of a recall row.
  - **The CCS axis (D41) is live where the t1h window could not see it.** Inert in all four
    T1-H legs (verified from ledgers). **ERCOT t1f: 14 conversions / 2,741.8 MW clear at
    carbon = 0** on the corrected constants — D41 §4.3's "no host class clears" was scoped to
    PJM/MISO and **does not extend**. **GOLDEN-3 answers D41 §7's routed RGGI question on the
    full horizon, more sharply than asked:** conversions 83 rows / 14,774.5 MW → 60 / 11,208.9
    MW (−24.1 %), the 2040 at-cap conversion disappears, the wave ends nine years early — while
    the 2028–2030 cap still binds, so **a five-year t1f window is blind to a 25-year answer**.
  - **Forecast gate rows (scope caveat: `ercot/caiso-t1f-pre-d46` are FFR-3A-2 vintage, so
    their deltas span a month of HEAD, not the three axes):** ERCOT t1f **all worse** (I12
    negative two years earlier, 2030 −1.5 → −7.1 %; sustained-VOLL hours 1,137 → 4,039/yr);
    CAISO t1f **better on every moved row** (I12 no longer negative in any year, FC-1 FAIL set
    shrinks to [I12, I7], backstop 65.5 → 52.6 %); NEISO t1f essentially unchanged; GOLDEN-3
    identical to GOLDEN-2 on 7 of 8 categories, P2 now clean. **GOLDEN-3 FC-7 PASS → FAIL on
    one row — no attestation — LEFT STANDING deliberately** (authoring one after reading the
    row is the sequence golden-1 refused); a pre-declared attestation restores it with no
    re-solve → **D47**.
  - **Costs, measured against the board:** T1-H estimates accurate; **the three t1f estimates
    were 7–10× too high** (ERCOT 2.0 h → 11.8 min, NEISO 1.0 h → 8.0 min, CAISO 2.8 h → 22.6
    min at 3–5 GB); the GOLDEN-2-derived anchors were right (campaign 33.0 min, FC-6 battery
    2.37 h). The container also spent ~55 min regenerating `data/clean` first. **Stage 3
    re-priced below.**
  - **The re-dispatch of 2026-09-04 refused to re-execute, correctly** (§11): re-running would
    have overwritten the `-pre-d46` baselines the charter forbids touching; it verified the
    landed state independently (8/8 keys, 6/6 preservations, 232 artifacts, guards exit 0) and
    re-verified the Stage-2 gate CLOSED. One row RE-OPENED by the owner's track after the lane
    closed it: **caiso-241 promoted after D46's CAISO legs solved** — `caiso-t1h` / `caiso-t1f`
    are stale again on the keeper-vintage axis, per the §0ac amendment-2 standing clause.
  - **Errors the lane recorded against itself, carried here:** the four ERCOT misses share one
    avoidable cause (a HIGH-confidence prediction made without one committed-artifact query
    that would have shown no in-window dates); GOLDEN-3's FC-4 was first mis-scored SKIPPED on
    a bad path and corrected before registration.
- **D45 — STILL A CHECKPOINT; the owed half has NOT landed.** `FINDING-capx-d45-*` §4, §5, §6,
  §7, §8 and §9 are literal `[filled …]` placeholders on `b168260e`; no `nyiso-*-d45` or
  `pjm-*-d45-fixed` bundle exists; the lane's branch is deleted. Two sittings without motion.
  **Relaunch protocol: not graded lost — card C-4.** Its close-out (§9) is what gates D46
  Stage 2, so Stage 2 is gated on a session whose status nobody has confirmed.

**2. GRADED — owner/backcast track (eight findings, one promotion, seven zero-solve):**

- **CAISO → `2026-09-03-caiso-241-b1-ctpeaker`** (PR #4663): the CT_PEAKER `committed` band
  ruled OUTSIDE caiso-238's Lever-A refusal on five limbs, grounded at its own physical
  counterpart (1.350 → 0.991, zero free parameters), solved against a REAL control under the
  owner's two in-session rulings (solve funded; the caiso-231 no-control-arms directive
  AMENDED for arms live in every year); every pre-registered gate passed; **the object it was
  meant to explain SURVIVES** (7 % of the volume miss closed); a volume-ceiling breach and a
  falsified P-7 disclosed (the latter a general DOF-instrument defect four sessions have hit).
  Re-verified here: NOT-YET C3a alone (+12.3 / +15.5 %); `audit_keepers` PASS. **Step 4
  skipped AGAIN — the SEVENTH consecutive R-T miss;** guard red at HEAD on one row.
- **caiso-242** (zero solves, owner-funded solve NOT spent): the pre-registered falsifier
  fired first and the arm was withdrawn — CT_PEAKER availability never binds (priced out in
  81–91 % of hours); the diagnosis is a **gas-basis identity error** (multipliers derived on
  the citygate spot, evaluated on the delivered series — every CAISO gas class's economic
  band offered 10–49 % above the bid it encodes); **and a live data defect worth 2.8 GW:
  2,816 MW of CAISO gas priced at $96.16/MMBtu (a $736/MWh marginal cost) for all 720 hours
  of November 2025**, from one EIA-923 row on 2 % of normal volume, reaching the LP because
  `state` is empty on 100 % of CAISO's gas rows and silently disables the donor-count guard.
  A rule-14 data repair with zero DOF — the CAISO lane's next object.
- **miso-203 / 204 / 205** (zero solves each): the summer-peak anchor is admissible and
  REFUSED anyway; the C3a-2025 tail is an **ENERGY** object (15/15 hours energy-largest), not
  congestion; **and the C3a comparator is a SINGLE HUB (INDIANA.HUB) — and the two committed
  probe records are on a clock one hour off the model's (25 h after Feb 28 of a leap year)**,
  diagnosed by lag scan at r = 1.000000 at k = −1. The annual mean is unaffected to three
  decimals (so no keeper determination moves and miso-204 explicitly says it is not a licence
  to re-score); every hour-matched statistic in miso-202/203's records is affected. miso-205
  re-did the driver story on the repaired clock: **solar is +34 % ABOVE normal in the object's
  hours, the renewable anomaly is WIND, the dominant driver is plain LOAD** — miso-203's
  mechanism REFUTED. Three instrument defects NAMED, none chartered; the single-hub
  comparator is an **owner item** (a scoring-reference question, not a calibration lever).
- **nyiso-181 / 181b / 182 / 183** (zero non-control solves): the "un-dispatched
  in-the-money ST_GAS" object (3.8–9.1 TWh/yr) was an artifact of the offer reconstruction —
  on the LP's own installed offer it is 0.06–0.07 TWh/yr; the C1-2023 ST_GAS over-generation
  is **ONE PLANT — Ravenswood, +5.472 TWh above its own meter, ECONOMIC not forced**, hidden
  by a class-aggregate cancellation that also hides ~1 TWh/yr of D-2 forced energy at native
  unit grain; the availability hypothesis REFUTED on its own gate; **the carrier is the OFFER,
  in ONE TERM: Ravenswood's heat-rate basis 9.50 vs a measured 10.71 MMBtu/MWh** ($8–13/MWh
  too cheap), while eight peers cluster at 1.60–1.75× measured. The NYISO lever queue was
  rewritten around it. Keeper unchanged at nyiso-177.
- **Audit v24** (PRs #4667/#4671): **leg 2's green did not survive one promotion** — the fast
  tier is red again on the caiso-241 stamp; **R-AB (the branch-protection flip) is 4-of-5
  ready and the fifth is exactly that re-key**, so the seventh promoter miss now blocks the
  programme's own durable fix; R-AB's second blocker is the path-filter trap (all five
  required checks are `ci.yml` jobs that never run on docs-only PRs). **R-Z + R-AC executed**
  (lint hygiene lane: `docs/handoffs` probe scripts excluded from ruff, seven files formatted,
  `ruff check` and `ruff format --check` both exit 0). Seven gates: six exit 0, one exit 1 (the
  stamp).

**3. STAGE 3 RE-PRICED (routed item 3).** If PJM's 7.3 h and MISO's 10.1 h carry the measured
t1f factor (7–10×), Stage 3 is **~45–90 min per ISO**, not 17 h — the order that made it
owner-scheduled has evaporated. Stage 3's MISO leg is also the one D41 touches most. →
**card C-6**: fold Stage 3 into the Stage-2 dispatch.

**4. THE STAGE-2 GATE PROBLEM, stated plainly.** Stage 2 (PJM/NYISO t1h + NYISO t1f) waits
on D45's §9 close-out, and D45's owed half — NYISO L2 (live, curve-OFF, diagnostics-on) + L3
(curve-ON probe) + PJM L4 (fixed-anchor control) + §4–§9 — is the SAME solve as Stage 2's
NYISO leg plus a PJM control. Whatever C-4 returns, the efficient shape is one lane: **D45-R**
runs the owed legs at HEAD (post-D44 posture, which supersedes D45's pre-D44 L1 anyway),
registers L2 as the bare `nyiso-t1h` (= Stage 2's NYISO leg), re-solves PJM L1 at HEAD as the
bare `pjm-t1h` (the D45 L1 preserved at `pjm-t1h-pre-d46`), fills §4–§9 and writes the §9
close-out. Stage 2's remaining leg (NYISO t1f, ~8–15 min measured-factor) and Stage 3 (PJM +
MISO t1f) ride the same lane if C-6 says so. Chartered as **D45-R** after the cards.

**5. RECORDS / DIRECTOR-TIER DECISIONS taken this sitting (no card needed):**
- **D47 issued — GOLDEN-3 attestation, records-only** (Opus; zero solves): a properly
  pre-declared `forecast_attestation.json` for the committed GOLDEN-3 bundle restores its
  FC-7 with no re-solve; the pre-declaration sequence (declare, then author, then re-score) is
  the whole point. Also folds the two D46-routed records items: the `-pre-d46` like-for-like
  caveat table, and the `neiso-t1h` posture disclosure (the bare key carries D37's Q28-armed
  Net ICR lever, which the shipped default leaves OFF — preserved deliberately by D46 so the
  refresh stayed single-axis; **director ruling: a bare key should carry the SHIPPED posture**,
  so the default-posture NEISO t1h re-solve (~7 min) is added to the D45-R batch, and D37's
  armed leg keeps its suffixed key).
- Routed items 1 (NEISO re-routing decomposition — needs a paired control) and 2 (ERCOT CCS at
  carbon = 0) are **QUEUED-NAMED at LOW EV**: both are measured facts with no gate consequence
  and no owner question; they re-open only with a lane that needs them.
- The miso-204 single-hub comparator is **NOT this desk's** — it is a backcast scoring-reference
  question for the owner's MISO lane; recorded in §2 so no capx lane ever "fixes" it.

**6. CARDS PRESENTED (answers appended as amendments):** **C-4** D45 owed-half status (running
/ dead → D45-R / close partial) · **C-5** the seventh gate-(a) miss — standing re-key duty for
this desk at every refresh, or hold for R-AB's flip (which the stamp itself blocks) · **C-6**
Stage 3 folded into the D45-R batch at the re-measured price, or kept owner-scheduled.

**AMENDMENT 1 (the C-4/C-5/C-6 answers, same sitting; pin `26c67788`):**

- **C-4 → Q33: D45 is DEAD; D45-R ISSUED** (pack §D45-R; Fable; branch
  `claude/capx-d45r-pjm-nyiso-close`). It absorbs D46 Stage 2 whole: the owed NYISO L2
  (live, curve-OFF, diagnostics-on) IS Stage 2's bare `nyiso-t1h`; PJM L1 is replayed at HEAD
  (post-D44) as the bare `pjm-t1h`; NYISO L3 (curve-ON probe) and PJM L4 (fixed-anchor control)
  run suffixed; §4–§9 are filled and the §9 close-out is written — the once-only mechanism-class
  question retires there or nowhere. The NEISO default-posture leg (§0ad.5) rides along.
- **C-6 → Q35: STAGE 3 FOLDED INTO D45-R** at the re-measured price (PJM + MISO t1f, solo and
  sequential, pre-declared with a 2 h STOP each). With it the whole §0ac.7 stale set closes in
  one dispatch, CAISO's re-opened row excepted (that one is the CAISO lane's — a promotion is
  imminent there again given caiso-242's data defect, so re-solving it now would be wasted).
- **C-5 → Q34: A STANDING RE-KEY DUTY FOR THIS DESK.** Whenever `check_gate_a_provenance.py`
  fails at a refresh pin, the director re-keys the stale row(s) to the R-N/R-T leaf pattern,
  verdict-neutral, in its own commit, and records each event in §2 as a promoter miss — no
  card, no one-push grant. **Executed immediately:** CAISO `caiso-240 → caiso-241`, the guard's
  ninth firing, six leaves, exit 0 after; R-AB's fifth blocker cleared (the audit desk owns the
  flip itself). The duty is a stopgap: it ends when R-AB's flip makes the guard a required check.
- **Standing consequence:** the "seventh consecutive promoter miss" count stays on the record;
  the duty does not absolve the promoting lanes of step 4, it stops the miss from blocking
  anyone else.

**AMENDMENT 2 (post-push delta, `b168260e..26c67788`, graded before close):**

- **NYISO → `2026-09-04-nyiso-185-family-hr` BY OWNER RULING** (PR #4679). The arm is the
  keeper recipe plus exactly one field, `egrid_family_heat_rates=True` — the zero-DOF grounding
  of the Ravenswood heat-rate basis nyiso-183 located (its heat-side factor 1.029 lands inside
  the peers' [1.0006, 1.0707]); the same-HEAD control reproduces the keeper **bit-identically
  (0 of 52,560 hourly zonal prices differ, every year)**, which also proves the D44 default flip
  is LP-inert for this backcast. Re-verified here: **NOT-YET, target grade 5, fails 3 — the
  SAME grade and count with a DIFFERENT C1 cell:** C1-2023 ST_GAS +3.86 → +2.16 TWh (FAIL →
  PASS — the Ravenswood object closes), C1-2024 CC_REGULAR +3.34 → +3.87 TWh, share 2.78 →
  3.18 pp (PASS → FAIL on the share band), C3a-2025 −11.2 → −10.5 %, C3c unchanged. **The
  first promotion in eight to re-key its own gate-(a) stamp** — the row's `detail` cites
  nyiso-185 and the guard reads 6/6 OK at `26c67788` — **with one half-miss disclosed:** its
  `corrected_by` field still reads audit v23's text (cosmetic, the guard does not read it;
  logged, not repaired — the standing duty fires on guard failures only). **Consequence for
  D45-R:** the NYISO keeper is nyiso-185, not nyiso-177; the charter reads the keeper from the
  shard and names it per leg, so nothing in it moves — annotated in the pack.
- **caiso-243 is MID-SOLVE** (checkpointed 2024 sidecars, PR #4680): the F923 low-volume
  fallback guard, i.e. the 2.8 GW / $736 per MWh data defect caiso-242 found — a CAISO
  promotion is imminent, which is exactly why `caiso-t1h/t1f` were left out of D45-R.

**AMENDMENT 3 (owner challenge, same sitting: *"Is there really nothing else unlocked or are you being lazy?"* — RECORDED AGAINST INTEREST: LAZY.)** The r#33 queue statement ("nothing else") was written from the r#32 queue rather than re-derived from what D46 and D45 had just unlocked. Re-derived from the committed artifacts, four items were unlocked and cheap, and the desk had labelled two of them "LOW EV" without measuring the precondition:

1. **The NEISO dates-OFF paired control (D46 routed item 1) — 7 minutes, and it is a POSTURE question, not a curiosity.** Q30 armed `fossil_announced_exits_enabled` as the default on MISO's evidence alone; rule 25 says every ISO carries its own verdict, and NEISO's own first measurement reads WORSE (recall 4/6 → 3/6, `false_retire` 0.263 → 0.315) on a leg that also carries the keeper-vintage axis. A paired control at HEAD with the field explicitly `False` (cache-neutral by b′-1; D44 §1) attributes the NEISO regression to the flip or clears it. If it is the flip, Q30 has a NEISO-side counter-example and the owner needs to see it — a default that improves MISO and degrades NEISO is exactly what rule 25 exists to catch. **Added to D45-R as leg 7** (suffixed key, never the bare one).
2. **ERCOT clears 14 CCS retrofits / 2,741.8 MW at carbon = 0 on the corrected constants (D46 routed item 2)** where PJM and MISO clear none. Either ERCOT's host economics genuinely differ (higher utilisation / spark) or the screen has an ERCOT-specific path — e.g. the 45Q window credit alone clearing a $1,521/kW retrofit without a carbon price, which real-world ERCOT gas fleets do not do. That is a forecast BEHAVIOUR question with a physical-plausibility flag, answerable zero-solve from the committed `ercot-2026-2030-d46-remeasure` evolution ledgers and the screen's own uplift arithmetic. **D49, half 1.**
3. **The MISO exit-side margin decomposition — the D43 construction mirrored onto exits, and its precondition is MET.** D46's MISO leg is diagnostics-on: `screen_signal_diag_<yr>_for_<yr+1>.npz` and the per-year `evolution_<yr>.json` ledgers are committed. MISO's largest remaining FC-3 miss is `retire.total_gw` −43.6 % after the dates flip — the UNDATED cohort under-retires while C3a says the LP under-prices by 12 %, which should retire MORE. D43 showed the entry under-build is dispersion the LP never priced; nobody has measured whether the exit under-retirement is the same wall (cohort margins clustered just ABOVE the bar, where price dispersion would push a tail below it) or a different object (the bar itself — FOM going-forward cost, or capacity revenue at the repaired RBDC). Zero-solve on committed dumps. **D49, half 2.** If it reads "same wall", the routing is closed honestly; if not, the MISO exit residual has a named lever for the first time since D32.
4. **The PJM accreditation-design devintage (D45 §2.3 items 1–2)** — identified WITH published sources and ZERO free parameters by D45's PJM half, which is complete: accredit thermal at UCAP (1 − EFORd) with the published pre-CIFP FPR for DY ≤ 2024/25 and switch to ELCC-class + post-CIFP FPR from 2025/26 exactly as the published design did (one vintage axis on `THERMAL_ACCREDITATION_BASIS_BY_ISO` + `resolve_forecast_pool_requirement`); DR as counted supply from the published BRA tables. Rule-14 sign: positions DOWN 6–9 points toward the curve, capacity revenue UP, retirements HARDER in the years the model over-retires. D45's own §9 (when written) names per-ISO repair lanes as the successor; the PJM one is ready now. **D48 — Phase 0 (build, default-off, pre-declare) unblocked immediately; its A/B solve is GATED on D45-R's PJM legs landing (collision on `pjm-t1h`).**

Two records corrections fold into existing lanes: **D47 gains item 5** — the board's `c_cost` fields for the t1f tier are corrected to D46's measured values (the 7–10× error is now a known false price on a live decision surface); **D45-R gains conditional CAISO legs** — if CAISO's keeper at launch is not `caiso-241` (caiso-243 is mid-solve), `caiso-t1h` / `caiso-t1f` are included (~35 min) rather than left for another sitting. And one correction to the r#32/r#33 record: the per-ISO dispersion siblings for ERCOT/CAISO/MISO/NEISO are no longer "blocked on a diagnostics-on solve" — D46 delivered those dumps; they remain QUEUED-NAMED on the D43 wall, but the honest label is "unblocked, low EV", not "blocked".

**What this desk got wrong, stated plainly:** it graded the queue by carrying forward its own prior sentence instead of re-reading each landed finding's routed list against the artifacts on main. The refresh protocol gains a step: **before writing "nothing else", list every routed item of every finding landed this sitting and state per item whether its precondition is met at the pin.**

**AMENDMENT 4 (lane capx D45-R, 2026-09-04 — recorded by the lane, not the desk: the §0ac.7 stale set CLOSES, CAISO excepted; D45 is CLOSED through §9):**

- **D45-R LANDED** (branch `claude/capx-d45r-close-jwq3bf`; `PREDECL-capx-d45r-2026-09-04.md`
  pushed before the first solve; finding `FINDING-capx-d45-pjm-nyiso-curves-2026-09-03.md`
  §4–§9 filled in place, §9 close-out line written). Eight solves, eight pre-declared cache keys
  realized exactly; every prior preserved at `-pre-d45r`; NOTHING ARMS; gate (a) untouched.
- **§0ac.7 stale-set inventory, final:** `pjm-t1h` · `nyiso-t1h` · `neiso-t1h` (now the SHIPPED
  posture per r#33; D46's armed record at `neiso-t1h-pre-d45r`) · `nyiso-t1f` · `pjm-t1f` ·
  `miso-t1f` → **CLOSED**. `caiso-t1h` / `caiso-t1f` → **STILL STALE** (keeper-vintage axis:
  caiso-241 → 243 promoted this window; the CAISO lane's, per amendment 2's standing clause).
  With D46 Stage 1 the whole set is closed except CAISO's two rows.
- **Stage 3 cost, MEASURED at the 5-year t1f grain (the D47b bracket resolved for PJM and
  MISO):** PJM 28.2 min / 9.0 GB solo; MISO 65.2 min / 10.0 GB solo (2030 alone 28 min; FC-8 CAVEAT on both); NYISO 16.0 min / 3.3 GB.
  Neither PJM nor MISO approached the 2 h STOP. The FF-3E full-horizon projections are
  untouched (still unmeasured at 25 yr).
- **The two arming questions, answered on the pre-stated conditions (finding §6):** NYISO
  curve-ON — DO NOT ARM (none of (a)/(b)/(c) met; +189 % is a position artifact: the requirement
  sits 2 GW low on the realized-peak basis and the NYC/LI/G-J locality is un-represented);
  PJM curve-ON over-fire — does NOT survive the corrected position (the fixed-anchor control
  fails nothing; the pair brackets the clearing half). No default moves in either ISO.
- **Routed:** the PJM/NYISO repair lanes the finding names (§2.3 items 1–3; §5.2.4 items 1–3,
  led by the requirement-on-the-published-ICAP-market-peak repair); the `-ff-t1-gate`
  `VERDICT_MAP` rows and the superseded t1f sidecars' `verdict_key` overrides left as D46 left
  theirs (records item); the PJM t1f CCS conversions at carbon = 0 vs D41 §4.3 (routed, not
  inferred); the NEISO coal-economic sign under the shipped vs armed bar (P11 miss).

## 0ac. Refresh #32 (2026-09-03, main HEAD `c73f78f5`) — nothing capx lands and the queue stays empty; the owner's backcast track promotes THREE keepers in one day, which widens the re-measure's stale set and leaves the forecast board's gate-(a) stamps stale on all three — R-T's at-source routing missed its first three tests

**0. FIRST ACT.** The handoff's newest-entry claim (§0ab = r#31) matched the ledger's actual
top entry on `origin/main`, so this sitting is r#32 and the delta is everything after
`68690427`. Main was FORCE-UPDATED between sittings (`158a6882…c73f78f5`); `68690427` is
still an ancestor of `c73f78f5`, so nothing this ledger cites was rewritten away. The r#31
desk's own commit (`a0167b04`) landed via PR #4631; its follow-on — the successor-handoff
rewrite (`83d2609f`, branch `capx-director-refresh-0z0e0f`) — was UNMERGED at refresh and is
cherry-picked into this sitting's push, re-pointed to r#32.

**1. GRADED (21 commits, 6 merges since `68690427`; zero of them capx):**

- **D44 — NOT LANDED.** `git log origin/main --grep` on D44 / fossil-dates-arm returns only
  the r#31 issuance commit; no `claude/capx-d44-*` branch on the remote; no open PR. Under the
  relaunch protocol (r#20/21) this is NOT graded lost — a solve-free records lane lands
  nothing observable until it pushes, and "silent" has meant "never dispatched" four times
  in this ledger (r#28: D31/D33/D30; r#20: four sessions). **Dispatch status ASKED (card
  C-1); the charter is RE-EMITTED verbatim from pack §D44, unchanged.**
- **D45 — NOT LANDED**, same evidence, same disposition. **Re-emitted verbatim from pack
  §D45.** One amendment recorded OUTSIDE the charter text: the NYISO keeper moved this window
  (below); the charter names no keeper id, so no text moves, but the per-leg vintage line the
  charter already requires must now name the keeper id per ISO alongside the fossil-dates
  posture. PJM's keeper is unchanged (`2026-08-15-pjm-162-inputclock`).
- **Owner/backcast track — THREE PROMOTIONS IN ONE DAY, each graded by content:**
  - **CAISO → `2026-09-02-caiso-239-b1-stgas`** (PR #4634, commit `c0cf3790`). The caiso-238
    object-2 charter's premise is FALSIFIED with zero solves: the funded scalar
    `offer_curve_by_group["ST_GAS"]["committed"]` reaches 2 of 25 ST_GAS tranches, both
    EIA-860 retired-window units at zero 2025 availability, and NONE of the three OTC
    steamers (`_offer_curve_for_group` returns `None` for `ST_GAS_PEAKER_PLANTS`, so they
    price off the uncited ERCOT-lineage literal `_DEFAULT_HR_MULT_BY_GROUP["ST_GAS"]["mc"]
    = 1.15`). Both chartered candidate values REFUSED; the repair RELOCATED to that literal as
    a gated per-ISO registry field (`caiso_st_gas_committed_measured`, rule 24), solved and
    registered at a C3a cost of +0.0001 / +0.0060 / +0.0001 $/MWh. Re-verified here from
    committed artifacts: **NOT-YET on C3a alone** (2024 +12.6 %, 2025 +15.6 %; 2023 PASS),
    C3c the lone ledgered caveat. `audit_keepers --iso CAISO` PASS 0/0. **Records
    inconsistency, recorded against the owner's track:** the finding and the calibration-log
    entry both open with "Keeper UNCHANGED at `2026-09-01-caiso-231-b1-ungrounded`", while the
    SAME commit re-keyed the shard, `status/CAISO.js` and the matrix to caiso-239. The shard
    is the promotion; the narrative was never updated. A one-line addendum is owed by the
    CAISO lane (the nyiso-177 §10 pattern is the model).
  - **MISO → `2026-09-02-miso-201-stbasis`** (PR #4630). The ST_GAS/ST_CHP analogue of the
    CC-only `unit_outage_lp_capacity_basis`, built in the OPPOSITE direction and for a
    measured reason (nothing raises a steam bin's LP capacity, so the NUMERATOR goes onto the
    LP's own basis; a nameplate denominator would leave 89 MW of phantom availability at a
    Ninemile Point that is entirely out). Single-field delta over the committed keeper
    recipe, S-0 bit-identical control, scorer committed blind, 32/55 steam bins (69.6 % of
    MW) eligible, +1.4–2.0 TWh/yr of wrongly-removed capability returned; **one frozen kill
    (K-3) FIRED on a single cell and is disclosed at full magnitude**; promoted under the
    owner's standing re-scoped bar. Re-verified: **NOT-YET on C3a-2025 alone (−12.4 %)**,
    membership unchanged. `audit_keepers` PASS 0/0.
  - **NYISO → `2026-09-02-nyiso-177-vintage-matched`** (PR #4632) — **BY OWNER RULING, the
    override class** (the nyiso-155/157/159 formula, verbatim: *"If structural integrity
    improves but gates regress that may still be a keeper"*). The lane's own §1–§9
    recommended AGAINST promotion and stand unedited; §10 records the override and corrects
    the lane's own under-weighting of two integrity gains (reproducibility of the outage
    extract — the superseded keeper's carried a null `derive_invocation` and cannot be
    regenerated at HEAD; and one availability basis across the tranche artifact and the
    outage extract). What it established first: nyiso-176's degradation was 100 % the
    UNGUARDED availability re-derivation the same gate imported, not the accurate
    attribution; the merit-order-guarded companion reproduces the keeper's Ravenswood
    envelope `np.array_equal`. Re-verified: **NOT-YET, target grade 6 → 5, fail set WIDENED
    to {C1-2023 ST_GAS +3.86 TWh, C3a-2025 −11.2 %, C3c}** — C3c is no longer lone, so the
    v3.3 standing rule is silent and it stands as a failure. No re-key duty (NYISO holds no
    marker). `audit_keepers` PASS 0/0.
  - **nyiso-178** (PR #4633, zero solves): the ST_GAS availability envelope is **NOT binding
    in any year in either direction** on the LP's own envelope (at ceiling 0/0/4 hours of
    8,760; never in a top-decile price hour; 2.2 GW of already-derated headroom unused at a
    $176/MWh mean in 2025) — the measured-availability family closes for ST_GAS in both
    directions, and the natural duty-curve successor is REFUTED on its own gate before a
    solve. **A new data point in the model-class-wall family** (a response deficit, not an
    availability one; nyiso-167's gain object again).
- **Forecast namespace: BYTE-UNCHANGED since `68690427`** (`git diff --stat` empty). Bare
  keys, GOLDEN-2, neiso-t3 all as at r#31. **Audit board: v22 unchanged**, no ruling past
  R-W; Q-4 still open (below).

**2. FOUND AGAINST THE RECORD (two items, neither this desk's to fix without a grant):**

- **The forecast gate-(a) stamps are STALE on all three promoted ISOs, and the tool says so:**
  `scripts/check_gate_a_provenance.py` at `c73f78f5` FAILS — CAISO cites the superseded
  `caiso-231`, MISO `miso-198`, NYISO `nyiso-159`. Every one of PRs #4634 / #4630 / #4632 set
  `keeper` in its shard and skipped **step 4 of `keepers/README.md`** — the R-T routing half
  ("a keeper-promotion PR re-keys the gate-(a) stamp IN THE SAME PR; the promoting lane's
  duty, not a follow-up and not the director's"). **This is the FOURTH instance of the class
  (v17 ×4, R-N CAISO, R-T MISO, now ×3) and the first three tests of the at-source routing
  ALL missed** — because the guard is not a required check (R-P's ruleset is still not in
  force, audit board v22) and a README step nobody greps is not a gate. Verdicts are UNMOVED
  (all three read `fail` on the marker before and after). The board's `isos/<ISO>/keeper`
  field is a SECOND, OLDER vintage on two rows (CAISO `caiso-220`, MISO `miso-191`) — two
  stale fields per row, not one. **Routed:** card **C-2** (a director one-push grant on the
  R-N/R-T pattern — one file, three rows, verdict-neutral — versus routing back to the three
  owner lanes); the audit desk owns the J-class record of the routing failure and the R-P
  consequence.
- The caiso-239 finding/log "Keeper UNCHANGED" headers vs the promoted shard (above).

**3. CONSEQUENCES FOR THE CAPX PROGRAM:**

- **The batched re-measure's stale set WIDENS — inventory standing here so pricing is one
  step when D44 lands (the r#31 rule: price once, run once).** Every registered forecast
  bundle of the three ISOs now sits on a superseded keeper recipe: MISO — `miso-t1h` and the
  D42 legs (`…-t1h-d42-*`, solved on the miso-200-era recipe), `miso-t1f`; CAISO —
  `caiso-t1f` (FFR-3A-2 vintage) and the D43 pair (`…-t1h-d43-control/-dispersion`, on
  caiso-231); NYISO — both nyiso t1h keys (`…-curve-t1h`, `…-realized-ffr3a3-t1h`, on
  nyiso-159 or older). Plus the r#30/r#31 axes already listed: the D41-stale CCS bundles
  (PJM/MISO CCS-affected t1h + GOLDEN-2's CCS leg) and the Q30-stale fossil-dates baselines
  (MISO first, every ISO's hindcast once D44 lands). **Nothing here is priced yet** — it
  cannot be until D44's flip is in HEAD, and re-measuring before that would run twice.
- **D45's NYISO leg rides nyiso-177 automatically** (a fresh container reads HEAD); the
  charter's own vintage line covers it (the amendment above). Its NYISO curve-ON
  adjudication inherits a WIDER fail set on the backcast side (C1-2023 ST_GAS) — a fact for
  the finding's position table, not a change to the charter.
- **The model-class wall is unchanged and gains a data point** (nyiso-178). Nothing new to
  charter into it; the dispersion siblings stay QUEUED-NAMED at LOW EV.

**4. DISPATCH: NOTHING NEW.** D44 + D45 re-emitted verbatim (chat, this sitting; the
committed charters in pack §D44/§D45 are the record — annotated there). Queue unchanged: (1)
the batched re-measure, ripening on D44; (2) dispersion siblings, LOW EV; (3) nothing else.

**5. PROTOCOL — audit board Q-4 ADOPTED by this desk.** The audit board's open proposal
(v18b Q-4: grep every ruling label of the sitting against `docs/` before a records lane
closes) is the refresh-protocol step this handoff already runs as read-step 7; it is now
recorded as ADOPTED here and was executed this sitting (R-series grep on the two cards:
R-N/R-T are the card-adjacent rulings on C-2 and are cited in it; nothing adjacent to C-1).
The audit desk may close Q-4 by citing this entry — this desk does not edit its board.

**6. CARDS PRESENTED (owner-tier; answers appended below as amendments):**
- **C-1 — D44/D45 dispatch status:** never dispatched (re-send) · dispatched and running
  (hold, grade next sitting) · lost (restart fresh from the committed charters).
- **C-2 — the three stale gate-(a) stamps:** grant this desk one push (one file,
  `program-status.json`, three `a_keeper_marker` rows + the two stale `keeper` fields,
  verdict-neutral, guard exit 0 after) · route back to the three owner lanes · leave for the
  audit desk's next cycle.

**AMENDMENT 1 (mid-sitting, after the C-1/C-2 answers; `origin/main` moved `c73f78f5` → `2b0b8796`, 30 commits, 8 merges, while §0ac.1–6 were being written — the r#25 pattern again, graded by content):**

- **C-1 answered "they have all landed I think" — and the owner was RIGHT, by content.** Every
  D44/D45 commit post-dates this sitting's pin. The §0ac.1 "NOT LANDED" grading was correct AT
  THE PIN and is wrong NOW; the re-emission is MOOT and withdrawn (nothing to paste).
  - **D44 LANDED** (PR #4639, `57088c33`): `fossil_announced_exits_enabled` ships **True**;
    CLAUDE.md step 0/step 1 + spec §5.1 amended (the "fossil is a default no-op" sentence is
    gone everywhere it lived); matrix base row re-stamped, MISO `K`, other ISOs default-on
    with own verdicts pending (rule 25); CHANGELOG; both pinned cache keys advanced BY DESIGN
    (b′-1's first ever declared flip — `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` gets its first
    entry). **Two things beyond the bare flip were needed to make it TRUE, both reported:** the
    hindcast harness PINNED the field to its own `False` on every invocation (the flip would
    have been inert for the entire T1-H lane), and four cache-key test assertions encoded
    "no default has ever flipped" as an invariant. Backcast byte-identical (forecast-mode
    load only). Its own close-out routes every pre-flip bundle to the batched re-measure —
    priced below.
  - **D45 — CHECKPOINT, NOT COMPLETE** (PRs #4643/#4647/#4649, branch since deleted): PJM
    L1 (live posture, diagnostics-on, key `ea767a6254b8e4af`, 16.4 min) SOLVED, registered
    as the bare **`pjm-t1h`** (HOLD, FC-3 FAIL, FC-7 CAVEAT; FFR-3A-3 preserved at
    `pjm-t1h-pre-d45`), scored **identical to the decimal** to the 2026-08-22 live leg. The
    PJM stage-2/3 result is real and large: **the "$0 where the model sits" is a BASIS
    artifact** — HEAD accredits on the 2025/26 ELCC-class design against a mixed-vintage
    composite requirement; restated on the auction's own UCAP basis the model sits 2–4 pts
    past the zero-cross at the market's committed quantity, **8–14 pts BELOW the published
    offered position the pre-declaration guessed** (P9 MISS, graded); and **the curve-ON
    over-fire does NOT survive the market's own price** — at the published cleared position
    the curve pays $15–21/kW-yr and **13.0 of the 18.1 GW of 2022 coal decisions would
    PASS** (median coal gap $14.8/kW-yr, not ~$40). The D6 object is the clearing half +
    basis devintage, not a curve shape; **no PJM default moves**; three identified repairs
    named with source (§2.3), not built. **OWED:** NYISO L2 (live, curve-OFF) + L3
    (curve-ON probe), PJM L4 (fixed-anchor control), and finding §4–§9 — all literal
    `[filled after …]` placeholders on `origin/main`; no `nyiso-*-d45` or `*-d45-fixed`
    bundle exists. Every D45 leg records the PRE-D44 posture
    (`fossil_announced_exits_enabled=False`) — a vintage fact the finding states, and it
    puts `pjm-t1h` in the re-measure set on the day it was registered. Per the r#20/21
    protocol: graded CHECKPOINT, not lost; if the owed half is still absent next sitting,
    ask. **The mechanism-class close-out line (§9) is not yet written, so the once-only
    question is NOT yet retired.**
- **C-2 granted — and SPENT on different rows than the card named.** The audit desk's
  records lane v23 (PRs #4645/#4646/#4648, at pin `c73f78f5`) had already re-keyed all
  three rows the card named (CAISO→239, MISO→201, NYISO→177) as its dispatched job 0
  widened to three by an in-session owner decision — and it independently found that
  **miso-200 (#4614) had ALSO skipped step 4, so the count was FOUR, not three; the r#31
  desk missed miso-200's stale stamp too — recorded against interest.** Then, after v23,
  **caiso-240 (#4641) and miso-202 (#4651) promoted and skipped step 4 AGAIN** — the fifth
  and sixth misses, within hours of the repair — and `check_gate_a_provenance.py` was red
  once more at this amendment's pin. **The grant was spent there:** two rows
  (CAISO→`2026-09-03-caiso-240-b1-stgas`, MISO→`2026-09-03-miso-202-unitclip`) + the
  derivation stamp, exactly the R-N/R-T leaf pattern (eight leaves; the dead
  `isos.<ISO>.keeper` field — no script or page reads it — left alone and disclosed);
  guard **exit 0**; verdicts unmoved. **Six consecutive misses of the at-source routing
  is the finding, not the stamps:** a README step nobody greps is not a gate; the durable
  fix is the owner's branch-protection flip (audit board W-2 / G2 leg 4), and this desk
  will not ask for a seventh grant.
- **Backcast track, post-pin:** **CAISO → `2026-09-03-caiso-240-b1-stgas`** (#4641; the
  rule-24 census of ALL 28 uncited `_DEFAULT_HR_MULT_BY_GROUP` literals on all six keepers,
  zero solves: **22 of 28 DEAD in every ISO**, five `mr` literals dead by construction, the
  largest live cell `COAL:mr` mostly priced-but-inert under take-or-pay; `ST_CHP` is the one
  class whose ENTIRE offer surface is uncited literals — an ask for MISO/PJM/NYISO/NEISO
  lanes under rule 25; the one groundable CAISO cell `ST_GAS:peak` armed measured;
  NOT-YET C3a alone, unchanged +12.6/+15.6 %; `audit_keepers` PASS). **MISO →
  `2026-09-03-miso-202-unitclip`** (#4651; the boundary-day double-count is REAL — all 845
  same-unit window overlaps are exactly 24.0 h, the `+ 1 day` fingerprint — repaired as a
  per-unit ceiling on a sum, all ten A/B gates pass; NOT-YET C3a-2025 alone −12.4 %;
  **and the C3a-2025 anatomy: it is not a level miss, it is entirely a missing scarcity
  tail — the SAME object as C3c**, so the outage family cannot reach it). **nyiso-179 /
  nyiso-180** (zero solves each): the ST_GAS offer position is NOT the governing object
  (2025 top-decile deficit = 62 % the model's own price level, 25 % offer position, 13 %
  dispatch); all four un-dispatched-in-the-money candidates CLOSE; the per-generator
  dispatch limit is LIFTED (a `class_band_hourly` sidecar now ships in the keeper bundle).
  Both are model-class-wall data points (the gain family).
- **Audit v23 landed** (#4645/#4646/#4648): **R-X and R-Y DISCHARGED** (GAP declarations
  filed, parity red cleared; the golden data tier GREEN and its cron REMOVED); **G2 leg 2
  SATISFIED — fast test tier green for the first time ever** (run 2351) — though the two
  post-v23 promotions re-reddened `test_live_board_passes` until this desk's re-key. Q-4
  executed by the audit desk itself (K-13: all 22 labels present). X-1: ruff is red on
  main from per-run probe scripts under `docs/handoffs/d37/` and `d45/` — the owner's
  decision whether session artifacts under `docs/handoffs/` are linted at all (X-1(ii)) is
  a question this desk endorses answering NO. X-2: stage-0 goldens regressed 7→4 of 7
  (CAISO/MISO/NYISO stale on the 09-02 promotions; now caiso-240/miso-202 make two of
  those re-captures stale AGAIN).

**7. THE RE-MEASURE, PRICED (the r#31 rule: one decision, one run — D44 has landed, so it
ripens now). What is stale, on three independent axes:** (i) **Q30/D44** — every
forecast/hindcast bundle solved before `57088c33` carries `fossil_announced_exits_enabled=
False` (ALL SIX ISOs; includes D45's L1, registered hours before the flip); (ii) **D41** —
the CCS fixed-cost constants (every bundle whose screen reached a CCS retrofit; PJM/MISO
t1h + GOLDEN-2's CCS leg); (iii) **keeper vintage** — CAISO (231→239→240), MISO
(198→200→201→202), NYISO (159→177) all superseded since their forecast bundles solved.

| class | keys that move | measured cost (committed wall times) | collision |
|---|---|---|---|
| **T1-H hindcasts** (2021–2025, 4 solved yrs) | bare `*-t1h` ×6 | NEISO ~6 min · PJM 16 min · MISO ~25 min · CAISO ~20 min · ERCOT/NYISO ~10–15 min ⇒ **≈1.5–2 h serial**, pairable except MISO/PJM | PJM + NYISO forecast surfaces are **D45's until it closes** |
| **GOLDEN-2** (neiso-t3, 2026–2050) | `neiso-t3` | **35 min** / 3.5 GB | none |
| **T1-F full-horizon** (2026–2050) | bare `*-t1f` ×6 | board `c_cost`: NEISO 1.0 h · NYISO 1.1 h · ERCOT 2.0 h · CAISO 2.8 h (pairable) · **PJM 7.3 h · MISO 10.1 h (solo, ~10 GB)** ⇒ **≈24 h serial, ≈19 h with the four pairable paired** | same D45 reservation on PJM/NYISO |

**The honest shape of the decision:** the hindcasts + golden are cheap (≈2.5 h) and move
every FC-3/FC-7 gate reading; the t1f tail is ≈80 % PJM+MISO and moves FC-1/FC-2 readings
that D41/Q30 touch materially in exactly those two ISOs. Nothing is priced against a
residual; every key re-registers preserve-then-overwrite with the pre-flip baseline kept
as a suffixed key. → **card C-3.**

**AMENDMENT 2 (the C-3 answer; `origin/main` `c6e46b49` — this desk's own r#32 push merged as PR #4642 and its branch deleted mid-sitting, the usual pattern):**

- **C-3 RULED → Q32: STAGED.** Owner's verbatim option: *"Staged: cheap set now, t1f tail
  later"*. **Stage 1 (dispatch now, ≈8 h wall):** ERCOT/CAISO/MISO/NEISO T1-H + GOLDEN-2 +
  the pairable t1f legs (NEISO/ERCOT/CAISO). **Stage 2 (gated on D45's §9 close-out
  landing):** PJM/NYISO t1h + NYISO t1f. **Stage 3 (owner-scheduled, not in the dispatch):**
  PJM t1f 7.3 h + MISO t1f 10.1 h, solo. **D46 ISSUED** (pack §D46; Opus; branch
  `claude/capx-d46-remeasure-batch`) — a baseline refresh with NO controls and NO arming:
  the three staleness axes were each measured on their own lanes (D42 / D41 / the backcast
  promotions), so D46 re-solves at HEAD, preserves every prior record at `<key>-pre-d46`,
  refreshes the board, and reports every gate flip at full magnitude under rule-14 sign
  discipline. Two records facts the charter states because the inventory found them: ERCOT
  and CAISO have NO bare `t1h` key today (their hindcasts live under long ids only), so D46
  mints `ercot-t1h` / `caiso-t1h` via `VERDICT_MAP` rows, pre-declared; and D45's own L1
  becomes `pjm-t1h-pre-d46` when Stage 2 runs.
- **Against interest, a push-protocol miss this sitting:** the amendment-2 write script
  aborted on an anchor mismatch AFTER appending the pack charter, and the shell continued to
  commit and push the pack alone (`5ff5acd7`) — a charter on `origin` with no ledger record
  for one push. Caught by the blob-verify line count (ledger unchanged at 3,009) and repaired
  in the next push. Lesson recorded: gate the commit on the write's success, never chain
  with `;`.
- **Standing consequence for later sittings:** the §0ac.7 stale-set inventory closes per
  stage as D46 lands; a keeper promotion in any ISO after D46's leg re-opens that ISO's row
  (keeper-vintage axis) — the same class as the gate-(a) stamp, and the same answer: the
  promoting lane owes the re-solve decision, this desk only records the staleness.

## 0ab. Refresh #31 (2026-09-02, main HEAD `68690427`) — the whole r#30 wave lands; the NEISO position is NAILED and the flip condition honestly fails anyway; the fossil-dates posture is decisively measured and ARMED (Q30); the dispersion family hits the model-class wall; the once-only D6+R3 charter is finally written

**1. GRADED (66 commits since `a5abe3fe`):**

- **D37 LANDED** (PR #4619, with a paired one-field control): **THE POST-WAVE YEARS NOW
  SCORE.** The armed positions land **+0.37 / −3.26 / +0.14 points of the real FCA 14/15/16**
  where the control reads +21.13 / −1.44 / −5.34 — superseding D40's own contaminated bound;
  the position defect is closed at NEISO. And the honest half: the lever's effect is
  **INVISIBLE in the FC-3 band list** it was routed through; retirements flip +51 % over →
  **−27 % under** (the MISO pattern repeating: faithful inputs expose the margin-side error);
  **storage stays at exactly 0.000 GW, refuting the lane's own headline prediction by its own
  pre-declared falsifier.** The pre-stated P9 flip condition (`retire.total_gw` in band AND
  `false_retire` in band AND clean LOYO — "any two of three is not enough") FAILS on
  retire.total_gw −27.1 % vs ±10 %, so **the recommendation executes itself: the shipped
  default stays OFF, the lever stays armed for the NEISO forecast lane's next measurement.
  No owner card — the pre-declaration governs.**
- **D42 LANDED** (PRs #4618/#4626; control + verified arm + ex-ante leg, ALL SUFFIXED, bare
  key untouched): honoring the owner's filed EIA-860 fossil retirement dates as an exogenous,
  vintage-gated step-1 input takes MISO T1-H **recall 5/19 → 16/19**, opens every non-coal
  exit class the floor held at zero, **displaces NOTHING the screen would have retired**
  (zero economic exits in every year, both legs), counters the deferral class per-unit with
  published re-filings (every one on file before its vintage year), and leaves the residual
  where the data says: the undated cohort + the December-dated 2026 roll. On the way it
  fixed I4 capacity accounting (announced_derates) and DISCLOSED a new shared-config-key
  case (census 15 → 16 — the D24 class; the (c′) guard is what makes this safe). **→ RULED
  Q30: ARM AS DEFAULT** (admissibility per rule 13 by the additions-pipeline symmetry;
  precision was never the bar). Execution = **D44**.
- **D43 LANDED** (PRs #4622/#4624/#4627) — an honest negative with the program's deepest
  insight of the week: the dispersion-carrying expectation **closes D39's under-expectation
  at the screen grain and is DECISION-INERT on the CAISO T1-H, because the dispersion the
  screen discards is dispersion the hindcast's OWN LP NEVER PRICED.** The under-build is
  upstream of the entry screen — it lives in the deterministic LP's price surface (the same
  model-class wall as the C3c ledger and the sub-unity gain). CAISO cell → **I**;
  `entry_dispersion_expectation_signal` shipped gated default-off with full rule-28 duties;
  the per-ISO routing table stands (NEISO bounded by the LP's own $0.1–4/kW-yr arbitrage;
  PJM/NYISO need a first diagnostics-on solve — folded into D45; ERCOT's tail composition is
  the FFR-8A successor, owner-gated `O`). The per-ISO dispersion A/Bs are QUEUED-NAMED at
  LOW EV on this insight — none dispatched.
- **Owner/audit tracks:** **MISO KEEPER → `2026-09-02-miso-200-unitroute`** (the CAMPD
  unit-outage class routing repaired at mixed-gas facilities; S-0 bit-identical control;
  **NOT-YET on C3a-2025 ALONE — unchanged in membership, SMALLER in magnitude**; "clears the
  ordinary bar, not only the owner's re-scoped one"). **nyiso-176**: the per-unit-attribution
  probe **REJECTED on its own R6** — it fixes C3a-2025 and breaks three other criteria; the
  keeper reproduces bit-identically (rule 1 in its purest form: the right number by a wrong
  mechanism, declined). **caiso-237** triaged the caiso-236 test debt; **caiso-238** filed
  its grounding charter (42 mis-classified scalars, four live residual DOF rows, two
  fundable asks) → **RULED Q31: FUND BOTH.** **Audit v22**: leg-2 refused a THIRD time, R-U
  discharged, R-W's fast-tier repair fixed 11 of 12 CI-visible failures by root cause.

**2. RULINGS (§3): Q30** — the fossil announced-date channel ARMS AS DEFAULT (spec §5.1 +
CLAUDE.md step-1 text amended by D44; the stale-bundle consequence joins the batched
re-measure decision). **Q31** — both caiso-238 asks FUNDED (the owner's backcast track
executes). And the **P9 non-flip recorded as self-executing** — D40's lever default stays
off by its own pre-declared condition; no discretionary act occurred.

**3. DISPATCH:** **D44 ISSUED** (Q30 execution: default flip + spec/CLAUDE.md amendment +
matrix re-stamp + CHANGELOG; Opus — ruled and mechanical, but it touches CLAUDE.md and the
spec, so rule-27 discipline is the charter's spine) · **D45 ISSUED — THE ONCE-ONLY D6+R3
JOINT CHARTER, finally written against what remains**: PJM + NYISO are the two
capacity-market ISOs no repair lane has touched — no diagnostics-on solve exists for
either, D28's NYISO curve-ON latent (+123 % retirements would arm; the flat $110 default
over-pays 2–6×) is unadjudicated, and the census-vs-cleared evaluation quantity has worked
patterns at MISO (supply_accounting_ratio) and NEISO (Net ICR) but nothing at PJM/NYISO
(rule 25: own parameters). Fable. **QUEUE:** the **post-repair re-measure batch** ripens
after D44 lands (one decision covering the D41-stale bundles + the Q30-stale forecast
baselines — priced next sitting) · the per-ISO dispersion A/Bs (named, LOW EV) · nothing
else — the capx queue is otherwise EMPTY for the first time since r#22.

## 0aa. Refresh #30 (2026-09-02, main HEAD `a5abe3fe`) — the repair wave converges: one dispersion term under-builds five ISOs, the CCS wave was two bad constants, the floor selects at random, and the NEISO requirement lever is built; two rulings (Q28/Q29); D37/D42/D43 issued

**1. GRADED (38 commits since `0a3d22c7`):**

- **D40 LANDED** (PR #4603): the NEISO adequacy requirement DEVINTAGED onto ISO-NE's
  published per-CCP Net ICR series (D33 R-A), one x-convention for position and curve (R-B),
  **BUILT DEFAULT-OFF and LOYO-scored on committed artifacts**: the denominator artifact is
  removed where the fleet is clean (**+21.4 → −2.1 pts at the 2023 entry**), the residual
  flips to the SHORT side D33 named, and the post-wave years are UNSCOREABLE until D37
  re-solves on a fleet the armed screens produced. Arming recommendation: arm for D37's
  measurement, do not flip the default → **RULED Q28 at the recommendation.**
- **D41 LANDED** (PR #4602): both CCS-retrofit fixed-cost legs re-identified onto the
  model's own ATB-2024 basis, cited — **and the 45Q-only retrofit STOPS CLEARING where
  carbon is zero.** The PJM/MISO cap-saturated CCS wave was an artifact of two
  mis-identified constants. Consequence carried as a NAMED QUEUE ITEM, not a dispatch: the
  registered t1f/full-horizon bundles are stale on this axis; the re-measure is BATCHED
  after the repair wave settles (one owner-cost decision, not per-lane re-runs).
- **D39 LANDED** (PRs #4599/#4604): the entry-stack under-build characterized cross-ISO —
  **ONE term: the energy leg's DISPERSION, discarded by the zone-flat tail-free stack
  re-price five ISOs share.** The attribute leg is EXACT (every RPS ISO's REC dual sits at
  its ACP — T16-A's finding generalizes), the capacity leg errs through POSITION (already
  owned by the D28/D33/D31/D40 chain, not the signal), and every VRE volume is CAP-set — so
  the signal lane can move TIMING and STORAGE, never the RPS volume. Routed: the zero-cost
  `entry_screen_diagnostics=True` precondition on every ISO's next solve (output-only, no
  cache-key term), and **CAISO FIRST** (largest committed expected-vs-realized gap, replay
  in place, capacity-leg correction measured inert — the cleanest single-term isolation in
  the program) → **D43, issued.**
- **D32 LANDED** (PR #4605): post-repair **the floor decides 100 % of MISO's exit
  composition**; the cross-fuel retention key has NO per-unit identification; the
  within-fuel tie-break NEVER fires (a float-noise defect, disclosed); selection is
  **statistically indistinguishable from random** against the real cohort. The one
  published per-unit driver that discriminates is the owner's FILED RETIREMENT DATE — which
  `forecast_fossil_retirement_economic=True` deliberately no-ops for fossil. R1-PRIMARY put
  the posture question to the owner with a pre-declared A/B → **RULED Q29: chartered
  (D42).** The precision-vs-admissibility argument and the additions-side symmetry (EIA-860
  proposed schedules are already a forecast input) are recorded as the deciding frame.
- **"capx D33" LABEL COLLISION, graded by content** (PRs #4596/#4606, branch
  `capx-d33-miso-additions-repair`): a lane reusing the D33 label executed a **MISO
  additions-under-build repair** (D31's routed FC-3 upstream object — not this desk's
  charter, and not the NEISO D33): coverage audit + siting identification, pre-declaration
  before the solve, a registered miso-t1h re-measure (the key's THIRD re-registration this
  week, preserve-then-overwrite held), **the exit side a measured NULL that formally amends
  D31 §7**, MISO matrix cell stamped. Recorded here as **D33-M** to keep the two D33s
  distinct; successor sittings cite it by branch + PRs, never by bare label.
- **Owner/audit tracks:** **stage-0 MISO captured** (R-Q third issue) — **five of six ISOs
  golden-covered, PJM the last gap**; the shrink-guard two-dot false positive recorded.
  **nyiso-175b** repaired the outage-extract routing defect + a CAMPD per-unit
  tranche-attribution defect (default-off companion), all four pre-solve gates passing.
  **xiso-7**: the `prb_follower` DOF under-count audited — real defect, ZERO incidence.
  **records v21**: the G2 leg-2 satisfaction claim REFUSED (run 2298 is not green) — the
  audit board declining its own good news. **perf-b**: ERCOT byte gate PASS, both
  normalizer grains gated. And the keeper-replay guard broken by caiso-236's rule-26
  deletion was caught and fixed in-wave.

**2. RULINGS (§3): Q28** — the Net ICR lever is ARMED FOR D37's MEASUREMENT ONLY; the
shipped default stays off pending D37's result. **Q29** — the fossil announced-date A/B is
CHARTERED (D42): a measurement of a posture, not a posture change; nothing arms until the
A/B and the owner both say so.

**3. DISPATCH:** **D37 ISSUED** (the NEISO T1-H at the armed posture — Net ICR lever ON per
Q28 + `entry_screen_diagnostics` on; pre-declaration-first from D40's screen-grain numbers;
Opus) · **D42 ISSUED** (the fossil announced-date A/B per D32 R1 + Q29; both legs
registered SUFFIXED, the bare key untouched — the posture returns to the owner with LOYO
evidence; Fable) · **D43 ISSUED** (the CAISO dispersion A/B per D39 §7 — the single-term
isolation; Fable). **Collision map:** D37 owns neiso-t1h + NEISO board; D42 owns the step-1
announced-retirement path + suffixed MISO records + the MISO shard; D43 owns the CAISO
entry-screen re-price + CAISO records — disjoint seams; all rebase-care on docs/.
**QUEUE:** D6+R3 (once-only) now waits ONLY on D37 (the last position evidence) — written
next sitting if D37 lands · the **post-repair-wave re-measure batch** (D41-stale bundles +
whatever D42/D43 arm) as ONE owner-cost decision · D20-family, D35-family: closed.

## 0z. Refresh #29 (2026-09-02, main HEAD `0a3d22c7`) — the whole five-lane wave lands; the MISO exit residual swings to −74.3 % UNDER on faithful inputs; the NEISO position defect is a requirement-vintage artifact with its repair data already in-repo; the CCS pace defect is two fixed-cost legs; FOUR lanes unlock

**1. GRADED (92 commits since `1aa8ac14`):**

- **D31 LANDED IN FULL** (PRs #4581/#4583/#4584/#4589): the Q24-funded PRA intake through the
  full data contract; the position audit CLOSES at a measured **0.8546 supply-accounting
  wedge** (new gated mechanism `supply_accounting_ratio`, rule 28 discharged); the RBDC gets
  its **published shape, validated to −0.4 % on the market's own revenue**; pre-declaration
  pushed before the solve and graded. **Exit-residual, rule 14's expected signature and
  starker than the charter imagined: +52.2 % OVER swings to −74.3 % UNDER** — a worse |error|
  than every predecessor, and the run localizes the remaining error more sharply than any
  before it (margin side). Routed: D32 keeps the non-coal channel (§5 measured the
  post-repair floor binding); a per-class SAC accreditation intake (published MISO SAC/DLOL
  workbooks — an owner intake decision when a lane needs it); the seasonal accreditation
  basis.
- **D33 LANDED** (PR #4569): **the NEISO accreditation basis is (approximately) the published
  one — the +21/+6/+7 position error is dominated by a REQUIREMENT-DENOMINATOR VINTAGE
  ARTIFACT** (a single-vintage composite ratio held flat across delivery years, while the
  published per-CCP Net ICR series is ALREADY COMMITTED IN-REPO), and the model's census
  supply is actually SHORT of what the real FCAs cleared. Routed R-A (devintage the
  requirement from the published Net ICR series, exactly as the code already prefers PJM's
  published FPR — `retirements.py:1086-1096` — with the card C-A hold-last convention) and
  R-B, both to a repair lane carrying rule-28 duties, default-off, **scored leave-one-year-out
  per rule 22 before any keeper moves** → **D40, issued**.
- **D30 LANDED** (PR #4565): **DEFECT-CANDIDATE on the FIXED-COST legs, not on 45Q.** The
  mechanism is the intended reading (45Q at statute over the statutory window; the cap binds
  everywhere, so the pace IS `ccs_retrofit_max_gw_per_year`); what wrongly clears the bar is
  (i) `fixed_om_gas_cc_ccs` (25) sitting BELOW `fixed_om_gas_cc` (30) since the G-32 ATB flip
  — the retrofit is PAID $5,000/MW-yr in fixed savings instead of charged the capture
  island's O&M — and (ii) `ccs_retrofit_capex_kw` (900, dollar-year unstated,
  `needs-citation`) at 59 % of the model's own ATB-2024 capture-island increment. Repair =
  re-identify both values from the ATB basis (rule 23: cites the data, never the residual)
  → **D41, issued**.
- **D35 LANDED** (PR #4574): the P2 gas leg re-scoped from a class label to **the model's gas
  partition**, pre-statement committed before the repaired checker ran, artifact-only
  re-score. **FC-6 LEAVES neiso-t3's FAIL set** — the verdict now reads HOLD on
  {FC-1, FC-2, FC-3, FC-4} with FC-5 and FC-6 both CAVEATs: both t3 instruments are fully
  scored, neither blocks. Cross-ISO consequence recorded (checker code is shared; verdicts
  stay per-ISO).
- **D38 LANDED** (PR #4568): D36's records executed + a derived-consumer staleness check and
  the blob verification recorded in its own finding.
- **Owner/audit tracks:** the **ERCOT 2023 carve-out golden is CAPTURED** via the
  golden-partition-carveout lane — **full ERCOT stage-0 coverage closed** (the r#26
  "not coverable without a schema change" blocker resolved); stage-0 also captured **CAISO
  (vs caiso-231) and NYISO (vs nyiso-159)** — four of six ISOs now golden-covered. **Audit
  v20**: rulings R-S..R-V recorded, the program UN-PARKED, post-pin motion annotated.
  **caiso-236**: the DOF ledger stopped attesting coal sigmoids that do not exist, CAISO's
  rebuilt, and the dead `caiso_bidir_intertie` mechanism + its fitted export cap DELETED
  (rules 23/26 — a fitted knob removed, not zeroed). **miso-200** (steam bid-side): the
  routing defect measured, **the arm KILLED at phase 0, no solve spent**; a gated
  `fac_group` mixed-facility short-circuit fix landed default-off; scorer committed BLIND;
  A/B control replayed at HEAD — mid-lane. **nyiso-174** adjudicated the East River
  crosswalk on the primary record; **nyiso-175** phase-0: the D-2 blocker is a grain
  difference, the CT deficit is TWO objects, both East River gates fail. **perf-b** is a
  live performance lane (CAMPD normalization ~40 % cut in the bench sub-phase, byte-gates
  before/after on NEISO+ERCOT, a reach limit recorded) — watch only. A ci-red repair and
  three ruff re-reddenings landed and were recorded by their lanes.

**2. THE UNLOCK COMPUTATION (the sitting's ask):** D31 landed → **D32 UNLOCKED**. D33
landed + golden closed → **D37's queue conditions met, but HELD one beat more**: D40's
requirement devintage is exactly what a T1-H re-run should carry, so D37 waits on D40's
arming decision (running it twice is the wasteful order); D36's `entry_screen_diagnostics`
precondition rides with it. D31+D33 landed → **D39 UNLOCKED** (phase-0, docs-only).
D30 landed → **D41 UNLOCKED** (the identified two-leg repair). **D6+R3 stays queued
DELIBERATELY**: D31's published RBDC (validated −0.4 %) and D33's requirement-vintage answer
resolve much of what the once-only clearing-half charter would have asked, and D40/D41 are
about to move the same screens — the charter is written AFTER those land, against what
remains. **ISSUED: D32 · D40 · D41 · D39.** Collision map: D32 owns the MISO floor-retention
seam; D40 owns the NEISO requirement seam + registry; D41 owns the retrofit-screen constants
+ citations; D39 is docs-only — disjoint; all four rebase-care on docs/ and ff-verdicts is
touched by NOBODY in this batch (D41 measures at screen grain, no golden re-solve licensed).

## 0y. Refresh #28 (2026-09-02, main HEAD `1aa8ac14`) — the storage question is ANSWERED (arbitrage-short, every year); the T16-A honesty clause FIRES as a real RPS/ACP finding; MISO promotes on pure structure; three silent lanes turn out never-dispatched

**1. GRADED (24 commits since `a2e80dbf`):**

- **D36 LANDED** (PR #4559): **the arbitrage leg is the short term in EVERY year, by
  $50–150/kW-yr; the RA leg is second-order and is the D28/D33 position object — two
  mechanisms, one seam.** Zero solves; the screen's own arithmetic re-run on the golden-2
  bundle + keeper hourlies + raw SMD LMPs. Why 2050/why iron-air answered in mechanism terms;
  three rule-13 repair routes identified + the honest DISPOSITION (the market's early build is
  procurement-channel-driven — a corridor explanation, not a model repair). Routed: (1) the
  three `capacity:storage` corridor rows re-authored with the procurement-channel explanation
  (→ **D38**, no verdict moves — already EXPLAINED); (2) `entry_screen_diagnostics` ON as the
  precondition for the NEXT NEISO solve, then the `entry_forward_expectation_signal` NEISO
  cell (`U`) is the chartered route for the arbitrage leg — cross-ISO, every screen, NOT a
  storage lane (→ named **D39**, queued); (3) a one-line golden-2 §6.1 wording correction
  (data-channel result, not D-3-rank; the rank is sign-preserving) (→ **D38**).
- **T16-A LANDED** (PRs #4555/#4558): both rungs solved (10.9 min, inside the Q27 pricing),
  **pre-registered outcome B — the honesty clause FIRED**: `rps_dual_over_acp` = 1.0 in BOTH
  rungs, the series is constant, and the FC-6 battery row stays **CAVEAT for a MEASURED
  reason** (all-constant [1.0, 1.0]) instead of an out-of-service SKIP. **The RPS/ACP finding,
  reported and never tuned toward: the REC dual sits at $50.00 — exactly the ACP ceiling — in
  all 25 years of BOTH arms while VRE grows 4.1 → 37.1 GW (9×). NEISO's RPS target is
  unreachable at every VRE volume the entry stack builds; the ACP escape column sets the
  attribute price in every year.** The unpredicted half at full magnitude: `entry_rate_limits`
  IS live in NEISO (8 of 18 metrics move) unlike the deleted knob's 18-of-18 identity. No
  third lever was tried (the clause held); the P2 FAIL untouched (D35's); no preserved key
  minted — the one moving leaf is a reason string becoming true, the interaction T16 §10
  anticipated. **Convergence note the director owns: T16-A's RPS-unreachable and D36's
  arbitrage-short point at the SAME under-building entry stack — the D39 object.**
- **MISO KEEPER → `2026-09-01-miso-198-oomlevel` (PROMOTED, owner's track):** the ST_GAS
  per-plant must-run floor LEVEL re-conditioned from the plant's operating range onto the
  out-of-merit phenomenon the floor represents (new field `st_gas_mustrun_oom_level`, gated).
  S-0 bit-identical through 39 commits of main, every pre-registered kill silent, the
  REVERSED direction confirmed, C8 improving in all three years, **no criterion status
  moving** — determination stays NOT-YET on {C3a-2025}: a structural improvement promoted
  without any gate movement, which is rule 1 working exactly as written. The scorer's
  mis-ordered INERT verdict line was DISCLOSED rather than repaired (right call — not its
  charter).
- **miso-199 CONCLUDED (kill):** the window-basis lever REFUSED on a frozen census that
  refuted the window premise — **the commitment-floor family CLOSES at MISO**; an X-2
  level-swap slot repaired and a silent no-op disclosed on the way. **nyiso-173 (kill):** the
  CC availability over-statement is provably INERT as a lever. **caiso-234 (kill):** the
  successor TOTAL-envelope estimator refused on its own pre-registered gates — G-LOYO fails
  34.2 % vs the 25 % bar — with the PRECOMMIT pushed before the DERIVATION (not just the
  solve) because it was a second estimator on once-used data; the stop fired, nothing armed.
  The kill discipline across all three tracks is in its best form of the program.
- **D31 / D33 / D30: NEVER DISPATCHED** (owner-confirmed at this sitting's card — the prompts
  had scrolled). Not lost, not stalled: never launched. **All three prompts RE-EMITTED
  verbatim from the pack at r#28 close** (a re-emission, not a re-issuance — the charters and
  branch stems are unchanged). D31 additionally still awaits the Q24 files; its charter
  already handles the files-missing case honestly.

**2. DISPATCH:** **D35 RELEASED AND ISSUED** (the P2 instrument-scope repair — the golden
session is closed and T16-A has landed, so the FC-6 checker + neiso-t3 surfaces are free;
Fable; artifact-only, the paired bundles exist) · **D38 ISSUED** (D36 routes 1+3: the
corridor-row re-author + the golden-2 wording correction; Opus, records-only) ·
**Named-queued: D39** (the entry-stack under-build object — T16-A outcome B + D36
arbitrage-short converge on it; route = `entry_screen_diagnostics` precondition + the
`entry_forward_expectation_signal` NEISO `U` cell; hold until D31/D33 land the
position/curve context) · **D37** stays queued behind D33 (its golden-close condition is
met). **In flight after r#28:** D35 · D38 · D31/D33/D30 (re-emitted, awaiting paste) ·
miso-200+ (owner's track continues).

## 0x. Refresh #27 (2026-09-01, main HEAD `a2e80dbf`) — GOLDEN-2 REGISTERS (HOLD; the first golden with a passing FC-7 and zero instrument-absence debt); the storage divergence SURVIVES the arming; T1.6 is deleted under rule 26 and Q27 re-points it; the NYISO lane lands four disciplined kills

**1. GRADED (81 commits since `a40cfc68`; grade-by-content):**

- **T3-NEISO-GOLDEN-2 REGISTERED** (PRs #4532/#4543/#4546/#4548; the owner reports the
  session STILL OPEN at this refresh — the lane stays open for further landings and its
  neiso-t3/FC-6 surfaces stay reserved, but the registration + finding §8 exit state are
  complete on main). **Verdict HOLD. FC-7 PASSES — the first golden in program history
  scored end-to-end with zero instrument-absence debt and a passing FC-7.** Solved 25/25 in
  35.1 min / 3.48 GB (inside budget), pre-declaration first, preserve-then-overwrite
  complete, DOF ledger 7/0, FC-5 re-dispositioned (54 rows, 0 UNEXPLAINED). **The
  campaign's object is answered: the armed storage-entry economics produce 720 MW of 100-h
  iron-air in 2050 and NOTHING in 2026–2049** — the corridor's largest divergence family
  (−56.2 % at the 2030/35/40 anchors) SURVIVES the arming; entry is late, single-tech,
  cap-bound, and vanishes under gas ×1.5. FC-6 at its own vintage: **P1 PASSES natively**
  (cum CO₂ 229.82 → 196.00 Mt, −14.7 % under a genuine +$25/t — the D26 construction at its
  second use) and **P2 FAILs as a NEW root-caused instrument-scope object**: the
  unabated-`gas_cc` leg crosses the CCS class migration (base holds ZERO unabated CC at 2050;
  gas ×1.5 stalls retrofits and builds MORE late CC — all-gas sign correct, row FAIL, left
  standing as scored). **Q25 IS SPENT** (this campaign only, executed once). Four routed
  items: (1) the storage value-stack timing question → **D36, issued**; (2) the P2
  instrument-scope repair → **D35, named-queued** (its surfaces are the open session's);
  (3) read D33's position finding against the §6.2 capacity-revenue delta decomposition when
  it lands; (4) FC-3's evidence vintage (no post-R-A NEISO T1-H) → **D37, named-queued**.
- **D34 LANDED** (PRs #4534/#4537): the below-base carbon_price guard + A/B regression
  evidence. Q26 executed; R4 closed.
- **D20 LANDED** (PR #4536): the seven legacy legs labeled and re-emitted **FC-7
  FAIL → CAVEAT, determinations unchanged**, control-first held. The §0s.5 decision is
  executed; a reconstruction can reach CAVEAT, never PASS.
- **T16 LANDED (not this desk's dispatch — the audit/plan-§2 track):**
  `renewable_buildout_pace` **DELETED under rule 26** (consumed by no model code — the D21
  "vacuous" caveat made structural), T1.6 marked OUT OF SERVICE, cache-key and full-suite
  controls taken against unmodified main, and the replacement-lever decision routed to the
  owner — taken this sitting as **Q27**. The lane also stated its D26-S interaction
  explicitly rather than leaning on a STOP rule — the collision-hygiene bar lanes should
  copy.
- **Owner backcast track:** the NYISO lane landed **FOUR disciplined kills on the gain
  object** — nyiso-169 (the zonal-gradient half is carried by NO binding constraint; 169b:
  the CC_CHP over-run is a FLOOR, not the duct-burner band), nyiso-170+b/c/d (the
  within-gas merit-order split is NOT an hourly displacement — layered pre-registered
  adversarial controls), nyiso-171 (the CC_CHP steam-host floor fails its own stop condition
  three independent ways), nyiso-172 (the ST_GAS deficit is a RESPONSE deficit, not a
  dropout — object relocated). The candidate space narrows honestly. **miso-198 MID-FLIGHT**
  (ST_GAS out-of-merit level A/B: prereg REVERSED the inherited direction, scorer committed
  before results, control leg BIT-IDENTICAL, arm solved — not yet registered). **caiso-232**
  split CAISO's C3a into level + shape (two defects); **caiso-233** derived the import spot
  depths and REFUSED the depth limb (both pre-registered gates FAIL, no solve). **Audit
  v19/v19b:** rulings R-J..R-R recorded; R-M applied by-sha after its target migrated keys;
  the dispatch-vs-launch check caught three non-launches in one sitting.
- **SILENT, not graded lost (relaunch protocol):** **D31** (most likely waiting on the Q24
  files — OWNER NUDGE: the three PRA postings + RBDC source unblock the primary lever) ·
  **D33** · **D30** (confirmed undispatched at r#26). All three prompts stand in the pack.

**2. RULING Q27 (§3):** T1.6 re-points to **`entry_rate_limits`** at the T16
recommendation. Execution = **T16-A** (Opus; ~12 min for 2 rungs + artifact-only re-score,
no golden re-solve), **HELD until the golden session closes** — it writes neiso-t3's FC-6
rows. The pre-registered honesty clause travels with it: the REC dual is pinned at the $50
ACP ceiling in both D21 rungs, so the lever may still not move it — that outcome is a real
RPS/ACP finding, reported, never a third lever tried.

**3. DISPATCH:** **D36 issued** (the storage value-stack timing decomposition — why the
armed economics clear nothing before 2050 against AEO's 1.76 GW by 2030; Fable, zero-solve,
docs-only, reads the registered golden-2 bundle — no collision with the open session).
**Held-dispatch: T16-A** (paste after golden-close). **Named-queued: D35** (P2
instrument-scope repair — same family as D23's P1 attribution; FC-6 checker + neiso-t3
surfaces) · **D37** (NEISO T1-H at the armed posture, the D4-M pattern — behind D33 and
golden-close). **In flight after r#27:** GOLDEN-2 session (open) · miso-198 (owner's) ·
D31 (awaiting Q24 files) · D33 · D30 (undispatched) · D36.

## 0w. Refresh #26 (2026-09-01, main HEAD `8462da22`) — the nine-writer wave lands 7-of-9 (two clean checkpoints, zero losses); D17's 14.7 GW is VINDICATED AS ARITHMETIC AND REFUTED AS A REMEDY (coal ate all of it — the floor-retention key owns exit composition); D28 decomposes the $0-curve object into a POSITION defect plus a clearing-half question; CAISO promotes; a card-duplication defect recorded against interest

**1. LANDING VERIFICATION — 12 PRs (#4509–#4520), graded by content:**

- **D27 LANDED (PRs #4512/#4519) — the wave's headline.** Pre-declaration pushed BEFORE the
  solve (`67594f08`), graded at full magnitude. **D17's ≈14.7 GW admission-headroom arithmetic
  is VINDICATED AS ARITHMETIC AND REFUTED AS A REMEDY**: every requirement-side number
  reproduces to the decimal and the cap duly releases (`entry_capped` −22.2 GW in 2023,
  −10.0 GW in 2024) — **and the entire released budget went to coal** (economic exits 11.9 →
  25.6 GW, 100 % coal, +106.3 % vs the 12.4 GW coal actual) while **gas_st/gas_cc/gas_ct/oil
  stay at exactly 0.000 GW**. G3's sign FLIPS (−27.7 % under → +52.2 % over);
  `retire.false_retire` flips PASS → FAIL (13.2 GW, 50 % of model). Mechanism, verified on
  source: **admission depth only ORDERS the candidate list — `_apply_reliability_floor`
  SELECTS, un-admitting in ascending going-forward-cost-per-firm-MW**, so exit composition is
  a pure function of per-fuel FOM ranking whenever the floor binds. Registered
  preserve-then-overwrite (`miso-t1h-pre-d27` kept); miso-t1h now HOLD on {FC-3} with FC-7
  moved FAIL → CAVEAT. Routed: **R2 capacity-revenue realism PROMOTED to primary lever**
  (published-data identification — → D31); **R5 NEW: the floor-retention key's
  exit-composition monopoly** (external observable: the real 2021–2025 cohort — 3 large gas
  steamers + a 158-unit small tail — is emphatically NOT FOM-rank-ordered; rule 21 forbids a
  tuned retention weight — → D32, queued). Tracked-set flag decided below (§0w.3).
- **D28 LANDED (PR #4511).** The $0-at-long-positions object is real in all four
  capacity-market ISOs but is **NOT one curve defect in four places** — the curves are (one
  MISO-specific exception) **published-faithful**; what is wrong is (a) **a POSITION defect**
  (in $0 screen years the model's accredited position sits **6–22 reserve-ratio points LONGER
  than the real market's cleared position** — PJM +9..+14, NEISO +21/+6/+7, MISO +11) and
  (b) **the clearing half** (the curve is evaluated at a census quantity where every real
  market clears supply against the curve). Census: 2 confirmed / 1 hindcast-confirmed /
  1 latent (NYISO: curve never consulted at default — flat $110 over-pays 2–6×; a curve-ON
  probe would arm at +123 % retirements — **that latent row is D6's evidence base**). Routed:
  R1 MISO repair lane after D27 (→ D31, now released), R2 NEISO position lane (→ D33),
  R3 the once-only cross-ISO clearing-half charter (queued jointly with D6). The rule-14
  block is explicit: EVERY faithful repair moves capacity revenue UP and the exit residual
  the WRONG way — nothing may be sized by what it does to that residual.
- **D24-R LANDED (PR #4514).** (c′)+(b′-1) exactly as ruled (Q20): the `is_cached`
  config-equality refusal + the declared-defaults append-only ledger; zero keys moved
  (assertion committed), zero caches invalidated, blob verification recorded in the finding.
  **The cache-key defect is closed forward**; the two historical pairs stay provenance-only,
  as ruled.
- **D29 LANDED (PR #4513).** `extract_trajectory` now carries generation-by-fuel + a real
  storage column; additive schema, zero solves. D25 §6.1's route is closed — the energy-mix
  corridor family becomes dispositionable for every future full-horizon run.
- **D26 = CLEAN CHECKPOINT, NOT A LANDING (PR #4520).** The instrument repair is in —
  `ScenarioConfig.carbon_price_delta` (default-0 exact no-op proven, cache key unmoved at
  HEAD and at the vintage pin, rule 28 discharged in the same commit: matrix row + all six
  shards, cells `·` instrument-plumbing) — and the **base-arm control reproduced the golden
  EXACTLY at vintage+repair**. The finding is committed with a literal **TBD-HEADLINE** and
  the full runbook for what is owed: the two paired 25-year arms (base + carbon_plus25),
  the paired-invariants scoring, and the neiso-t3 FC-6 re-score. **→ D26-S issued** (Opus —
  the runbook is literal). Owner cards (a) golden re-solve and (b) FC-6 survival STILL wait
  on it. Also surfaced for the owner, not ripe: **D23's R4 design question** (should
  `carbon_price` replace, floor, or stack on the program price) — hold until D26-S lands.
- **nyiso-168 LANDED (PR #4518, owner's track).** Phase-0, zero-solve, nyiso-167's probe
  re-run first and **bit-identical**. The 0.703 gain is a **SLOPE deficit in the ordinary
  50th–90th load band** — not the tail, not locational; four candidate causes killed by
  measurement; **the market's steepness there is measured NOT physical** (NYISO clears
  reserves above zero in ~100 % of DAM hours in every zone — mean $6–12/MWh, p50–90 up to
  $13–34 in 2025 — where the keeper clears ~zero in 99.6 % of hours); and **the one new
  mechanism the object points at is PROVABLY LP-INERT — killed ex ante**. An honest
  narrowing session: lines closed, nothing armed, keeper unchanged NOT-YET {C3a-2025, C3c}.
  Next: nyiso-169.
- **miso-197 = CHECKPOINT (PR #4510, owner's track).** Phase-0 frozen zero-solve: the
  CC_REGULAR over-dispatch census rule pre-registered (`_miso197_cc_overdispatch_phase0.py`,
  914 lines) before any adjudicating quantity. Mid-lane; grade next refresh.
- **caiso-231 PROMOTED TO KEEPER (PR #4515, owner's track): CAISO keeper →
  `2026-09-01-caiso-231-b1-ungrounded`.** The three un-grounded gas offer classes re-grounded
  on their own measured bid buckets; **nine ERCOT-inherited multipliers retire to measured**
  (a rule-25 debt paid), zero free parameters added; the pre-registered adverse C3a cost
  lands 4–13× SMALLER than bound (+0.03..0.06 $/MWh); every gate PASSES, no falsifier fires;
  determination **UNCHANGED — NOT-YET on C3a alone** (+12.55 % 2024 / +15.59 % 2025);
  `audit_keepers --iso CAISO` PASS 0/0. Promotion made on the owner's verbatim in-session
  standard (structural integrity over ~0.1 pp fit regression — rule 1 working). CAISO's
  terminal rest ends on its own lane's motion.
- **stage-0 capture NEISO+ERCOT LANDED (PRs #4509/#4517, audit track, owner ruling R-L).**
  The audit programme's first solve lane: both fidelity oracles **PASS** (NEISO 259/259,
  ERCOT-forward 271/271 flags identical, zero drift — goldens CURRENT); the ERCOT 2023
  carve-out config answered explicitly: **not coverable without a schema change**.
- **D30: NOT DISPATCHED** (owner-confirmed this sitting, relaunch protocol honoured — never
  graded lost). The pack §D30 prompt stays live.

**2. RECORDED AGAINST INTEREST — the Q22 card re-served an already-ruled question.** Audit
ruling **R-H** (the 2026-08-31 audit REFRESH sitting) had ALREADY ruled the nyiso-161
winter-face waiver card **Option A, NOT-YET STANDS**, and its first artifact landed at v18b
D-7 (`9e4291b6`, PR #4498) — **before the r#25 card set was served**. The r#24 watch line
("ruling R-H recorded and its card retired") was in this ledger and I did not chase WHICH
card before serving Q22. The owner ruled identically, so no state divergence exists —
**primacy is R-H's; Q22 stands as the owner's independent re-confirmation**, the §3 row and
the card-doc banner are corrected to say so, and the never-re-serve duty gains a concrete
step: **before serving any card, grep the audit board's ruling ledger (R-series) for
card-adjacent rulings**. (The audit board itself flags the same failure shape: two of its
own records lanes omitted R-H in parallel — "parallelism is not a completeness check".)

**3. DIRECTOR DECISIONS THIS SITTING:** (i) D27's tracked-set flag: the bundle-scoped
un-ignore of this one bundle's `evolution_*.json` **stands as scoped** (the NEISO-RC-R R4
precedent); no generalization of the T1-H slim-set convention until a second lane needs the
same evidence class — then it becomes a charter line, not a convention drift. (ii) D28's R3
(the once-only cross-ISO clearing-half charter) and **D6 are QUEUED JOINTLY** — D28's NYISO
latent row is D6's evidence base and the two questions share the curve-consultation seam;
they charter together after D31/D33 land per-ISO evidence, as one mechanism-class charter
with per-ISO parameters (rule 25). (iii) D32 (D27's R5 floor-retention monopoly) is
**named-queued behind D31** — same MISO evolution machinery, hard collision.

**4. RULINGS AND DISPATCH.** **Q24 — the MISO PRA/RBDC intake is FUNDED** (owner, this
sitting): the PRA Results Posting category rows (~5 numbers × 3 postings, the S-123
anchor-vintage document class) + the published RBDC shape source; misoenergy.org is
403-blocked in-session so the owner fetches out-of-session and hands the files to D31.
Explicitly recorded: **Q23 was FC-5-scoped and STANDS** — this is not a re-opening; D28
itself pre-argued the distinction. **Issued: D26-S** (the D26 runbook's solve half + FC-6
re-score under cross-lane re-grade; Opus) · **D31** (the MISO capacity-revenue repair —
position audit + measured RBDC shape, intake-funded, rule-14 sign discipline; Fable) ·
**D33** (the NEISO position lane, D28's R2 — accreditation basis + cleared-vs-qualified,
in-repo record only; its outcome INFORMS the golden card; Fable). **Collision map:** D26-S
solves in the pinned vintage checkout and writes neiso-t3 FC-6 rows + the D26 finding; D31
writes MISO forecast surfaces + screen code + the funded intake (no overlap with miso-197's
backcast namespace); D33 writes docs + NEISO position finding only, and must not touch the
golden's pinned inputs while D26-S runs; D30 (undispatched) is docs-only. Queue: D32 ·
D6+R3 (joint) · D30 (live).

**5. OWNER-TIER AFTER THIS SITTING:** (a)/(b) the golden re-solve + FC-6 survival — wait on
D26-S; (c) D23's R4 carbon-semantics design question — wait on D26-S; nothing else open.
Q20–Q24 all spent; the FC-5 source class stays closed (Q23).

*Mid-sitting amendment #1 (same sitting, main `8462da22` → `a40cfc68`; the r#26 push itself
survived a transport incident — see the last paragraph).* **THE WAVE KEPT LANDING WHILE §0w
WAS BEING WRITTEN, and it discharged this sitting's own dispatch:**

- **D26 COMPLETED ITSELF (PR #4522) — D26-S IS RETIRED UNRUN.** The lane's own session ran
  the owed arms and re-scored: **P1 FAIL → PASS on the repaired arm; neiso-t3 FC-6
  FAIL → CAVEAT; determination HOLD unchanged.** The D21 FAIL did NOT survive the instrument
  repair — the model's carbon response is confirmed correct-sign at measured magnitude, and
  the r#23 alarm is now closed at every layer (attribution → instrument → measurement). The
  r#20/21 relaunch lesson executed correctly this time: the checkpoint was graded a
  checkpoint, not a loss, and the lane finished on its own branch. D26-S's pack section is
  annotated retired; nothing was double-run.
- **miso-197 CONCLUDED (PR #4521, owner's track):** the +6.664 TWh CC-2024 excess is
  root-caused zero-solve to the chronic ~10 TWh/yr out-of-merit gas-steamer/CHP allocation
  defect, exposed at the CC line in the one year the 2.3×-over-elastic gas family lands on
  the actual level (intra-family reallocation) — eight witnesses ruled out on the frozen
  rule. Successor prereg (ST_GAS conduct re-identification) frozen in the finding §8; an
  incidental instrument caveat (bin-synthesis divergence at Cottonwood) handed to the
  `_CC_PMAX_RECONCILED_PLANTS` order-dependence charter. Keeper unchanged.
- **The audit director re-keyed CAISO's forecast gate-(a) stamp** to the live keeper
  `caiso-231-b1-ungrounded` (PR #4523) — the cross-program consequence of the promotion,
  taken by the right board.

**TWO MORE RULINGS (Q25/Q26, §3):** **Q25 — THE SECOND §2.1b CAMPAIGN IS AUTHORIZED, NOW**
(T3-NEISO-GOLDEN-2: BAU 2026–2050 at HEAD with the R-A-armed storage posture, its own FC-6
battery at its own vintage, full-rubric scoring, preserve-then-overwrite; Q13's
this-campaign-only scoping carries over). **Q26 — `carbon_price` KEEPS replace semantics +
gains a below-base validation guard** (→ D34; R4 is CLOSED — no successor re-opens it
without a new owner act). **Dispatched: T3-NEISO-GOLDEN-2** (Fable, neiso) · **D34** (Opus,
code) · **D20 RELEASED** (Opus, code — its hold was the scorer surface under active
re-scoring lanes; D26 and D27 have both landed). Collision map: GOLDEN-2 owns neiso-t3 +
the NEISO board block; D20 owns the seven legacy keys + the FC-7 scorer path (disjoint);
D34 owns the validation seam; D31/D33/D30 unchanged. **In flight after amendment 1:**
D31 · D33 · D30 (undispatched) · GOLDEN-2 · D34 · D20.

*Transport note for successors:* this sitting's push hung silently twice (2 m and 4 m
timeouts, zero output — NOT the fast-failing HTTP/2 defect, and NOT the r#23 auth failure;
the proxy status showed `uploadGateEnabled: true, uploadPauses: 232` with reads flowing).
The remedy that worked: rebase fresh, then ONE push attempt with a **long background window
(~9 m)** — the upload gate released and the push completed exit-0. Do not conclude
transport death from a 2-minute hang; do not fall back to `push_files` for ≥300-line files
(rule 27).

## 0v. Refresh #25 (2026-09-01, main HEAD `1658d8aa`) — TWO DIRECTORS RAN ON ONE PROGRAM and grade-by-content caught it; nyiso-167 re-attributes C3a-2025 to a CROSS-ISO sub-unity price-response gain (five of six keepers); FOUR owner rulings in one sitting (Q20–Q23); D24-R + D29 issued; the D26/D27/D28 charter gap is repaired

**0. THE SITTING ITSELF IS THE ANOMALY TO RECORD: two director instances, one program.** The
r#23 container's credentials RETURNED after its handoff was written: that session landed its held
ledger (PR #4503) and ran a full r#24 sitting (PR #4505, branch
`claude/market-sim-calibration-director-lckr9a`) — while the owner separately opened THIS
session from the r#23-era handoff prompt, which knew none of that. **Grade-by-content (the r#22
amendment) is what caught it**: fetch-first found the r#24 entry already at the top of the
ledger, so this sitting renumbered itself r#25 and graded only the delta, instead of re-grading
the r#23 wave as its stale prompt instructed and colliding with everything r#24 wrote. Standing
protocol for every successor, now in the handoff doc: **on session open, compare your handoff's
newest-entry claim against the ledger's actual top entry on main BEFORE grading anything** — a
handoff prompt is a snapshot that can be a full generation stale, and the ledger always wins.
The dead-container instance's branch is merged and deleted; this branch
(`claude/capx-director-refresh-0z0e0f`) is the live director line unless the owner says
otherwise. The r#23 patch-file contingency is fully moot (r#24 already said so; the handoff doc
now carries it).

**1. GRADED — the delta the r#24 ledger commit could not see** (nothing else landed since; no
open PRs, and the three surviving origin branches carry zero unmerged commits):

- **nyiso-167 LANDED (PR #4504, merged mid-r#24 after its ledger commit froze) — and it is the
  program's most consequential backcast result since the cascade repair.** Measured off the
  keeper's own committed artifacts, zero solve: NYISO's C3a-2025 (−11.5 %) is NOT a
  year-specific or winter-specific miss. The keeper's price response over all 36 training months
  is **one stable affine law — model = 0.703 × actual_RT + $11.03 (R² 0.910)** — reproduced
  independently by the price-vs-load decile gradient and the gas passthrough slope. A gain below
  1 makes the error a function of the year's price LEVEL: C3a clears ±10 % only for an annual
  actual mean inside **$27.8–56.0/MWh**; 2023 and 2024 sit inside, 2025 ($66.43) is 19 % above
  the edge, and that alone is the −11.5 %. **87.4 % of the nyiso-161 card's "winter face" is
  this same year-invariant gain** (winter-specific residue: −$0.51/MWh), answering the card's
  own eligibility test (a) **NO as written**. And the gain is a **cross-ISO property**: ERCOT
  0.347 / MISO 0.500 / PJM 0.668 / NYISO 0.703 / CAISO 0.837 / **NEISO 0.986** — every keeper
  but NEISO's carries a bounded C3a pass window in price level, and NEISO is the in-repo
  existence proof the deficiency is closable (measurement only; **no verdict transfers, rule 25
  held** — the lane said so itself). Three consequences: (i) **MISO's C3a-2025-only NOT-YET
  (−12.34 %) sits inside the same object** (gain 0.500, window $26.8–40.2 — informed ruling Q21);
  (ii) the nyiso-161 card's factual predicate dissolved (ruled Q22 this sitting); (iii) forward
  relevance the capx track must carry as a stated attribution limit: a sub-unity price-response
  gain in five of six keepers bounds any price-level-sensitive forecast leg — no gate moves on a
  measurement, but the gain is now the backcast track's unifying frontier across four ISOs.
- **The nyiso-165 verification finding LANDED (PR #4485)** — independent re-verification of the
  AS-reference repair plus the ALL-ISO reference-side cascade scan, discharging the r#23 "OWED:
  the cross-ISO cascade scan was not carried" item. Together with xiso-cascade (instrument
  side, PR #4497) the max-not-sum rule has now been carried to both halves of the program.
- **Owner backcast track (watch):** the C-1 ERCOT joint-wind charter PRECOMMIT + Amendment 1
  (Q15 armed the volume rule under it) and the R-D wind-entry closure MAP landed 08-31; the
  caiso-231 PRECOMMIT (un-grounded-class offer re-grounding) filed 09-01 — both mid-lane.
  *Mid-sitting amendment:* caiso-231's **A0 control bundle landed** (PR #4506, the keeper
  recipe replayed at HEAD) while this entry was being written — the lane is in its arm phase.

**2. FOUR OWNER RULINGS THIS SITTING (Q20–Q23, §3 table).** All four presented as one card set
with the evidence in front of the owner; all four ruled at the recommendation except Q23, where
the owner ruled tighter than the offer:

- **Q20 — D24 repair = (c′)+(b′-1), the zero-cost pair.** Wrong-serve becomes mechanically
  impossible at the `is_cached` seam; keys identify from the next default flip onward;
  0 keys move, 0 caches invalidated. Retroactive separation of the two historical collision
  pairs was NOT purchased ((b′-2) declined). Execution = lane **D24-R** (Opus).
- **Q21 — MISO D-4 posture = (iii), CONTINUE THE LANE** on the named candidates
  (`gas_coldsnap_derate` + `winter_fuelsec_posture` aimed at the named Jan-2025 −1.43 pp;
  `cc_duct_peaking` / `egrid_identity_heat_rates` / `tac_load_coverage`), with the cross-ISO
  gain object as the sharper target. Execution belongs to the owner's MISO backcast lane
  (miso-197+, after miso-196 lands) — recorded here, not chartered here.
- **Q22 — nyiso-161 winter-face waiver = OPTION A, no amendment.** NOT-YET stands; the card
  RETIRES answered-by-measurement (nyiso-167 supplied the probe its own test (a) called for);
  annotated in place at `docs/DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md`. The
  audit programme's parked-trigger row (ruling R-F) should retire on that board's next sitting
  — flagged there, not edited cross-program. No rubric class is created; the "only C3c is
  non-downgrading" line holds intact.
- **Q23 — FC-5 EXTERNAL SOURCES: NONE FUNDED.** Owner verbatim: "None — I'm not getting more
  data." All five ranked sources (NYISO Gold Book 2026, ISO-NE CELT 2026, NREL StdScen2024,
  MISO Futures, CAISO IEPR) are CLOSED as not-funded, the egress-blocked class included. FC-5
  rests permanently on the current anchor set: the CAVEAT is the steady state, and the
  single-source status of the t3-required table is a named, accepted limitation. **DO NOT
  RE-PRESENT absent a new owner act.** D25's §6.5 route is thereby fully resolved.

**3. DISPATCHED THIS SITTING — two lanes, both routed-execution:** **D24-R** (execute Q20:
(c′) refusal seam + (b′-1) declared-defaults append-only ledger, with a zero-key-move assertion
as its own merge gate; Opus — discretion spent in D24 §7) · **D29** (the D25 §6.1 routed
reporting fix: generation-by-fuel + a REAL storage column in
`run_full_horizon.extract_trajectory`, unblocking the 252 energy-mix corridor anchors for
future runs; Opus — the spec is written). **Collision map:** D24-R touches
`runner.py`/`scenarios.py`/cache guards + tests, no board surfaces; D29 touches
`scripts/run_full_horizon.py` + tests, no board surfaces; neither collides with in-flight D26
(neiso FC-6 row + instrument), D27 (MISO t1h key + board block) or D28 (docs only). If D29
lands before D27's solve starts, D27's bundle carries the new grain — desirable, not required;
neither waits on the other.

**4. THE D26/D27/D28 CHARTER GAP IS REPAIRED.** r#24 issued all three as self-contained chat
prompts, but the pack ends at D25 — no committed charter existed, which is the r#23 fragility
repeated (unlanded work is supposed to restart FRESH from the committed charter; there was
nothing to restart from). This sitting commits **reconstruction charters** (pack §D26/§D27/§D28)
built from §0u's dispatch record + the routed findings, each labeled: a running lane's own
prompt governs its run; the pack section is the charter of record for any relaunch. If any of
the three was in fact never dispatched, the pack section is now also the issuable prompt.

**5. QUEUE AFTER THIS SITTING:** **D6** (FC-3 curve-ON over-fire; still uncharted, HELD behind
D27 + D28 — all three touch the four capacity-market ISOs' T1-H/curve surfaces) · **D30, NEW
(named, uncharted):** the D25 §6.4 routed 45Q question — the CCS retrofit screen converts at
its 3 GW/yr cap even where the resolved carbon signal is ZERO (PJM/MISO, 45Q alone), reaching
2030 fleet fractions no external view reaches; with D23 having cleared the model's
carbon-response SIGN, the open question is whether that conversion PACE is the intended reading
of spec §5.6's economics — a divergence-vs-every-external-view mechanism question, HELD behind
D27 (same CCS/T1-H surfaces) and best chartered with D28's Phase-0 in hand · **D20** (director
decision taken, unchanged).

**6. OWNER-TIER STILL OPEN — deliberately NOT re-presented this sitting (both wait on D26):**
(a) the golden re-solve / second §2.1b campaign — live again since Q16's premise discharged,
decide AFTER the FC-6 P1 instrument repair; D25 §6.3 strengthened it (the zero-storage-entry
divergence is the corridor's largest cross-ISO family, −56 % to −96 %, four ISOs, and the R-A
arms would move exactly those rows); (b) whether `neiso-t3`'s FC-6 FAIL survives D26's
re-score — the affected lane's re-verification decides publication, per the cross-lane
re-grade rule.

*Mid-sitting amendment #2 (owner throughput ask: "is that all that can possibly run without
collision?"). Answer: NO — the five-prompt set was the charter-READY maximum, not the possible
maximum; the census found three more, and two holds confirmed real.* **Landed while asking:**
the r#25 refresh itself merged (PR #4507) and **miso-196 CONCLUDED** (PR #4508 — the
`cc_outage_derate_from_top` arm REJECTED on its own pre-registered kill, A/B registered),
which UNBLOCKS the Q21-ruled MISO continuation. **Newly dispatched/offered:** **D30 CHARTERED
AND ISSUED** (pack §D30; the D25 §6.4 45Q conversion-pace question, Phase-0 docs-only — its
two seams are written into the charter: PJM-primary while D27 re-measures MISO, and a hard
STOP-and-route at the capacity-revenue leg, which D28 owns; the "held behind D27/D28" was
sequencing preference, not collision, and dissolves under those two seam lines) ·
**nyiso-168 OFFERED** (backcast, owner's track: adjudicate the 0.703 price-response gain on
NYISO's own data — no NYISO session in flight, zero overlap with D26's neiso forecast
surfaces) · **miso-197 OFFERED** (backcast, owner's track: execute Q21's (iii) — the prompt
directs the session to the CURRENT shard verdicts + lever queue rather than hardcoding
miso-192's candidate list, part of which miso-193/194/195/196 have since adjudicated) · the
**audit programme's next sitting** is also collision-free anytime (its own board file; the Q22
parked-row retirement + Q20–Q23 absorption are waiting for it). **Holds CONFIRMED with
reasons:** D6 (uncharted BY DEPENDENCY — its scope is decided by D28's answer, and its MISO
leg collides with D27's t1h re-registration) · D20 (the scorer is a SHARED SURFACE: D26 and
D27 are both actively re-scoring/re-registering against live scorer semantics — a scorer
change mid-flight forces both to re-verify mid-lane; sequence after they land) · ERCOT
backcast (C-1 joint-wind mid-lane owns the ERCOT shard/log) · CAISO backcast (caiso-231 arm
phase owns the CAISO shard/log) · the golden re-solve (owner-gated behind D26 by design, §0v.6).
Ceiling statement, honestly: with D26/D27/D28/D24-R/D29 + D30 + nyiso-168 + miso-197 + the
audit sitting, every writable surface group in the program has exactly one owner — nothing
further can be added without pairing two writers on one surface.

## 0u. Refresh #24 (2026-09-01, main HEAD `1d280815`) — SIX OF SIX LAND; **THE t3 CEILING IS LIFTED**; and the r#23 "the model's economic core has a sign error" alarm is REFUTED — the instrument's premise was inverted, not the model

**0. The r#23 ledger LANDED.** Git credentials returned; the held commit rebased onto
`1d280815`, pushed, and both files blob-verified (ledger 1,862 lines, pack 2,590 — rule 27).
The patch-file contingency in the successor handoff is moot and should be struck on its next
edit. **The transport failure cost nothing**: the r#23 grading was done through the GitHub API
and every prompt was issued self-contained, so all six lanes ran and landed while the ledger sat
unpushed. Recorded because the instinct under a dead transport is to stop issuing work, and that
would have been the expensive choice.

**1. THE r#23 DISPATCH: 6 of 6 LANDED.**

- **D23 LANDED — AND IT REFUTES THE ALARM I RAISED, which is the most important line in this
  entry.** At r#23 I called the P1 carbon result "a claim about the model's fitness for the
  policy-scenario purpose the whole forecast program exists to serve" and made it the wave's
  headline. **That was wrong, and wrong in the direction of alarm** — the more expensive error
  for a director, because it sets the program's priorities. **Neither leg is a model defect; the
  model's carbon-price response has the RIGHT sign in both.** The root cause is the ARM
  CONSTRUCTION: a nonzero `ScenarioConfig.carbon_price` **REPLACES** the resolved carbon signal
  (documented, deliberate, single-consumer semantics — `policy/carbon.py::resolve_carbon_price`
  precedence (i)), and the NEISO base **already carries the projected RGGI trajectory** —
  $26.05/t in 2026 escalating at the published 7 %/yr RGGI CCR rate to **$132.16/t by 2050**
  (the EM-6 seam fix: "forecast carbon is no longer zero for a program ISO"). So the `carbon25`
  arm did not raise the carbon price, **it CUT it, in every year of the horizon** (−$1.05 in
  2026 widening to −$107.16 in 2050). +52.4 % cumulative CO2, ~3 GW less CCS and lower prices
  are all the model responding **correctly** to a large carbon-price DECREASE. **P1 measured the
  premise of its own pair.** Zero solves, precommit honoured, §6 scores its own pre-stated
  expectations including misses. The repairs routed are entirely instrument-side; no model
  parameter, threshold or expectation moved, and D21's FC-6 FAIL was deliberately left standing
  rather than quietly withdrawn. **Consequence needing a decision (item 3a): `neiso-t3`'s FC-6
  FAIL now rests, in its P1 leg, on an inverted premise.**
- **D25 LANDED — THE t3 CEILING OWNER RULING Q16 NAMED IS LIFTED.** The disposition table rubric
  §FC-5 requires a scoring session to author now exists: **78 rows across five bundles —
  37 IN CORRIDOR / 41 EXPLAINED DIVERGENCE / 0 UNEXPLAINED**, each explanation naming its
  mechanism with a citation. All five verdict keys re-score **FC-5 SKIPPED → CAVEAT**
  (control-first, every committed verdict reproduced byte-for-byte first), **no determination
  moves**, and **nothing on `neiso-t3` reads SKIPPED-required any more**. Two marks of a lane
  that understood its own hazard: §5 **subjects the zero-UNEXPLAINED count to an adversarial
  audit**, naming the two weakest explanations in the set and their falsifiers so a reviewer
  knows where to push (a corridor full of hand-waving would have been the instrument defeated
  permanently, since nobody re-audits a PASS); and when the batch landed on main mid-session it
  **rebuilt on `7b085947`, left D19's board writes intact, and incorporated D23's
  re-attribution into the affected CO2/CCS rows before pushing anything.**
- **D24 LANDED** — and the defect is real, bounded, and the protection against it is an accident.
  Exposure: **4 default-flip events / 7 registered fields** on main since 2026-07-26 (the other
  211 registered fields never moved), and **all 98 analyzable committed forecast run records drop
  at least one flipped field from their key.** Two demonstrated collision pairs: ERCOT
  `f061b264` (**the known-true positive, found independently — the method check the charter
  demanded, passed**) and **NEW: NEISO `07e416f3`** (capxd14/rcrepair, the absent-vs-armed-default
  form). Method verified three ways including exact reproduction of 94/98 recorded keys.
  **Consequence, honestly stated: all 99 keyed runs used DISTINCT cache roots, so both pairs are
  "collides and was re-solved anyway" — no cached result was ever served. The protection is the
  per-run `--out-dir` convention, which is INCIDENTAL AND UNDOCUMENTED.** Two by-products:
  the D4-I3 §5.1 group (`28cef350`, 7 runs) is **NOT** this defect (uniform effective posture, 7
  distinct roots) — narrowing R-5 zero-solve; and `cache_key` is non-identifying **in both
  directions** (one NEISO pair carries identical configs under two keys). Verdict linkage
  **reported, not acted on** (correct — that is the affected lane's): the NEISO T1-X FF-2D
  verdict and NEISO's `c_crossover_gap` gate leg rest on the `07e416f3` pair. Repairs priced
  against every committed config: **(a) 99/99 forecast + 63/63 backcast keys move · (b) same
  plus recurring churn · (b'-1) 0 keys · (c') 0 keys, 0 invalidations.** Fix NOT landed, per
  charter. **Owner decision (item 3b).**
- **D17-R LANDED** — the relaunch executed and the object is ATTRIBUTED. Outcome **(B),
  requirement/cap-side, thread (iii) CONFIRMED-PRIMARY**: gas/oil units DO fail the screen bar
  en masse and are then blocked at the admission cap (`entry_capped` **93.0 GW in 2023, 105.5 GW
  in 2024**), and that cap's requirement basis was the pre-S-123 composite S-123 measured as
  overstated. The hindcast-window analogue, computed for the first time: the corrected basis is
  worth **≈14.7 GW of admission headroom at the 2024 screen** (≈11.2 GW requirement overstatement
  + 3.5 GW missing external accredited firm) — **3.7–4.3× the entire missing non-coal exit
  target**. **And the repair is ALREADY SHIPPED AT HEAD**: all three S-123 operands are registry
  constants read through the same `resolve_adequacy_requirement_mw` / `accredited_firm_capacity_mw`
  seam the admission cap and execution floor call, so the committed FFR-2B/FFR-3A-3 numbers
  simply predate it. **Routed PRIMARY: a HEAD re-measure of the MISO T1-H leg** — a solve this
  lane correctly did not run (→ lane D27).
- **D19 LANDED** — records only, six chartered facts, **zero gate-leg status moves by the lane**,
  byte-identity asserted programmatically on everything not deliberately edited. It also absorbed
  a mid-session collision correctly: the audit programme's own gate-(a) repair (owner ruling
  **R-I**) flipped ERCOT while D19 was running, and D19 **kept that flip verbatim** and
  reconciled its remainder (`closed_on`, keeper display, `marker_complete`, and three further
  stale keeper-display fields the re-keyed cells exposed) rather than re-deciding it.
- **xiso-cascade LANDED — and the carried rule paid for the scan on its first ISO.** MISO's
  generator ASM MCPs nest by BPM-002 product substitution:
  **GENREGMCP ≥ GENSPINMCP ≥ GENSUPPMCP in 100.0000 % of 554,904 committed cells** (2023–2026,
  DA+RT, all zone rows). **Two live instruments summed them** — including the source of the
  published **"$484.87 = 118.8 % of the energy gap" headline, corrected to $193.30 = 47.3 %.**
  A claim that reserve prices covered *more than the whole* energy gap was, corrected, under
  half of it. Summed fields DELETED (rule 23 `[R-DELETE]`), the three frozen committed records
  annotated with dated `CORRECTION_2026-09-01_xiso-cascade` keys inserted programmatically from
  the acceptance record, an independent acceptance probe reproducing every committed summed
  value exactly, and 7 regression tests pinning the invariant. No determination, keeper, gate or
  matrix cell consumes the summed fields (enumerated call-site by call-site). **The nyiso-166 §2
  distinction was preserved** — nested REGION stacking is additive, DURATION/substitution
  products are not.

**2. A CROSS-ISO OBJECT SURFACED BY TWO INDEPENDENT LANES, and nobody owns it.** D17-R's
CONTRIBUTING cause is that MISO's screen bar fails **~118.5 of 142.6 GW of screened thermal in
2024** — the margin side does not over-reward gas/oil, **it under-rewards nearly everything** —
chiefly because the modelled capacity-revenue leg pays **$0 at every long reserve position**
(RBDC zero-cross at 1.05; $0 on every committed capped row) while MISO's real PRA cleared small
positive prices. **That is the SAME pathology NEISO-RC-R measured in its R2 leg** (the FCA
demand curve paying $0 past 8.3 % surplus, "near-inert at the model's long positions", where real
FCAs cleared $24–43/kW-yr). Two ISOs, two independently-derived curves, one shape of error:
**a modelled capacity-demand curve that pays nothing exactly where the model sits.** Note the
sign discipline — the fix direction is *more* capacity revenue at long positions, which makes
retirements *harder*, i.e. it moves D17's headline residual the wrong way. That is a rule-14
`[R-ACCURATE]` situation and must not be resolved by whichever direction helps a residual.
Chartered as **D28**, Phase-0, cross-ISO characterization only.

**3. OWNER-TIER ITEMS OPEN AFTER THIS REFRESH:**
- **(a) THE GOLDEN RE-SOLVE RETURNS AS A LIVE CARD.** Q16 HELD it on the explicit premise that
  FC-5 and FC-6 did not exist so no golden could grade better than HOLD. **That premise is now
  discharged** — D21 made FC-6 grade, D25 lifted FC-5, and `neiso-t3` no longer reads
  SKIPPED-required. The Q16 hold has therefore expired on its own terms and the second-campaign
  question is live again, **but it should be decided AFTER the FC-6 P1 instrument repair
  (item b)** — re-solving into a P1 whose arm construction is inverted would spend a campaign to
  re-measure a premise.
- **(b) Does `neiso-t3`'s FC-6 FAIL still stand?** Its P1 leg rests on D23's inverted premise.
  D23 deliberately left the verdict alone (correct — cross-lane re-grade). Lane **D26** repairs
  the arm construction and re-scores; whether the re-score publishes is the affected lane's
  re-verification, not D26's unilateral call.
- **(c) D24's repair option.** Four priced. **(c') costs 0 keys and 0 invalidations**, so there
  is a live cheap option; (a) moves 99/99 forecast + 63/63 backcast keys. Owner's call — the
  charter deliberately stopped at pricing.
- **(d) miso-192's D-4 posture options (i)/(ii)/(iii)**, still unruled · **(e) the nyiso-161
  winter-face waiver card**, parked with a fired trigger (audit R-F), still unruled · **(f)** the
  four portal-blocked FC-5 sources (StdScen2024 is unreachable by egress policy — a different
  class); D25's §5 names which would most change the picture.

**4. DISPATCH RECORD (post-r#24): THREE lanes issued** — **D26** (repair the FC-6 P1 arm
construction so P1 measures the model instead of its own premise, then re-score under the
cross-lane re-grade rule; Fable) · **D27** (D17-R's routed PRIMARY: the HEAD re-measure of the
MISO T1-H leg against D17's quantified ≈14.7 GW expectation; **Opus** — the discretion is spent
in D17's finding) · **D28** (the cross-ISO capacity-revenue-at-long-position object, Phase-0,
MISO + NEISO; Fable). **Collision map:** D26 writes `neiso-t3`'s FC-6 row and the FC-6 instrument;
D27 writes the MISO T1-H key and the MISO board block; D28 writes docs only. Distinct keys and
blocks, rebase-care in each. **QUEUED:** D6 (still uncharted) · D20 (director decision taken).

**5. BACKCAST/AUDIT WATCH.** **caiso-230 LANDED**: the above-floor C3a term decomposed to a kill,
no LP; records + matrix shard + lever queue stamped. **caiso-231 PRECOMMIT filed** (un-grounded-class
offer re-grounding) — mid-lane. **miso-196 in flight**: `cc_outage_derate_from_top` A/B
pre-registered, phase 0 cleared, **the A/B scorer written before any arm result exists** (the
right order). **Audit programme v18/v18b landed**: ruling **R-H** recorded and the card it decided
retired; the forecast gate-(a) rows guarded against the backcast store (F-5); the bench gate's
engine-drift arithmetic fixed (item 12); the parity allowlist replaced with a class-level
classifier (item 10); **ruling R-I** flipped ERCOT's gate (a), which D19 then reconciled.
**Stage-0 provenance repair landed**: per-entry golden provenance + a retention invariant.

## 0t. Refresh #23 (2026-08-31, main HEAD `240e80e4`) — SEVEN OF EIGHT LAND; the t3 ceiling is measurable and its first verdict is a FAIL; NEISO and NYISO take the program's FIRST CLEAN FC MAPS; two program-wide defects surface (a carbon price that RAISES CO2; one cache key covering two dispatches)

**0. TRANSPORT NOTE — this refresh is graded but NOT PUSHED, deliberately.** `git fetch`/`push`
fail this session with `could not read Username for 'https://github.com'` (the credential path
is gone; three retries with backoff, all identical — not a 408/500, so the HTTP/1.1 remedy does
not apply). The wave was therefore graded **through the GitHub API** — `list_commits` on `main`
plus the merged-PR list, which is exactly the content-not-branch-name method r#22's amendment
made standing, and it is strictly better evidence than a branch census would have been. **The
ledger and pack edits are written and committed LOCALLY and the push is HELD**, because the
only available transport is `push_files`, and rule 27 `[R-PUSH]` forbids rewriting an existing
≥300-line file from regenerated response content — which is precisely what pushing this
1,600-line ledger and 2,300-line pack through it would be. That is the rule working, not an
obstacle to route around: the incident behind rule 27 was a large file truncated over exactly
this path. **The push lands as-is the moment git transport returns.**

**1. LANDING VERIFICATION — 7 of 8 dispatched lanes landed** (six capx + the two offered
backcast prompts; `main` @ `240e80e4`):

- **D8-V LANDED** (PR #4483). **The program has its first two clean FC maps.** Both stopped
  flips re-verified through their affected lanes' own records and PUBLISHED: `neiso-t1f` and
  `nyiso-t1f` move PROMOTE-WITH-CAVEATS → **PROMOTE with caveats `[]`**, exactly the capx-D8 §6
  pre-registration. PJM's ledger built and committed (1 entry, 0 UNIDENTIFIED ⇒ FC-7
  CAVEAT → PASS, determination HOLD unchanged — not a stop, as pre-measured); MISO's built and
  committed (4 entries, 3 UNIDENTIFIED ⇒ FC-7 **stays** CAVEAT, the attestation debt NAMED and
  deliberately not attested — rule 21 honoured rather than cleared by invention). Controls
  first on all four keys, each reproducing its committed record byte-for-byte. Gate cells left
  untouched with their stale text **flagged to D19**, which independently confirms the r#22
  decision to queue D19 behind these writers.
- **D4-M LANDED** (PR #4481; the R-4 instrument grain `ed83115c` + the run `d110a13b`), and it
  is the richest result of the wave.
  - **It caught a posture change the pre-declaration could not have known about, and said so
    before grading anything.** Asserting from the run's own `run_config.json`, the measured
    posture is **FOUR levers, not two**: owner ruling R-A flipped `storage_entry_availability_gate`
    and `storage_entry_cost_normalized_rank` to defaults on 2026-08-31, *after* D4-I3's
    pre-declaration froze, while its whole basis (`d12c-armed`) ran both False. The lane graded
    P-1..P-8 **exactly as written**, at full magnitude, carrying that as a stated attribution
    limit — it did not re-base, reinterpret or quietly widen a single prediction. That is the
    pre-declaration discipline working under a moving posture.
  - **Grade: held on direction and on every structural claim; missed LOW on every magnitude.**
    P-1 HELD (2023 slack 0.1156 %, ≈12× the control). P-2 MISS 1.65×. P-3 HELD in kind, 1.67×
    (2024 opens at 0.0334 %). P-4 HELD (2025 clean). P-5 build HELD (28.587 GW) but RM MISS low
    (4.75/5.50 % vs ~6.1/6.8 %). P-6 consistent, not independently measured. P-7 MISS 1.35×.
    **P-8 UNMEASURED and recorded as unmeasured rather than estimated.** **No falsifier fired**;
    F-3 is closest at 77 % of its ceiling.
  - **THE SUBSTANTIVE RESULT — composition beat volume, in the mirror image of F-4.** Against
    `d12c-armed` the model built **MORE** (+2.7 %) and 2023 slack got **65 % WORSE** — the wrong
    sign under a pure volume account. This does not refute D4-I3's §2.2(a) monotonicity (a
    within-posture claim) but **corrects its magnitude**: the duration channel is ~0.05 pp here
    against an opposing volume move, so **composition is the larger channel at this posture, not
    the residual**. Storage power is identical (2,750 MW) while this run builds 100 %
    li_ion_4hr.
  - **The worse I3 was NOT repaired** — not by re-disarming, not by a volume knob, not by any
    parameter moved to close the breach. Exactly as D4-I3 §4 bound it. And the deficit is now
    located: **ERCOT retirements are 0.000 GW modelled against 2.294 actual**, so the gap is
    entirely entry-side. *(Note the rhyme with D3 and with D17's unstarted object: a second ISO
    whose economic screen executes no retirements at all.)*
  - **R-5 IS UPGRADED FROM HYPOTHESIS TO DEMONSTRATED MECHANISM** — see item 2.
- **D18 LANDED** (PR #4479). Census **re-derived by running the real checker at HEAD** and it
  matched the charter's list exactly — 13 runs, 15 idents. **14 of 15 point at a real record**;
  CAISO's 2021 I7 is declared **honestly untracked at root-cause grain**, with the explicit note
  that attributing it to FR-3 would have been fabricated. That is the charter's "say so
  explicitly rather than inventing an attribution" clause being honoured against the temptation
  to tidy. `dominant_open_causes.I3` de-ERCOT'd. Everything else in the file byte-unchanged.
  *(Dispatch hygiene: TWO D18 sessions ran — PRs #4479 and #4480, the second carrying no unique
  content. No harm; noted so the duplicate is not mistaken for a second finding.)*
- **D21 LANDED** (PRs #4477/#4478) — **the t3 FC-6 gate now grades, and its first verdict is a
  FAIL.** `neiso-t3` FC-6 moves SKIPPED-required → **FAIL**; determination stays HOLD, now on
  six failing gates + FC-5 unscored. Two sub-results matter more than the verdict:
  - **NEISO's entire pre-registered ladder is VACUOUS.** T1.6 is its whole battery — 2 rungs —
    and both solved **metric-identically across all 18 extracted values**, because
    `renewable_buildout_pace` **is consumed by no model code**. Both gate rows therefore pass on
    all-constant series ⇒ CAVEAT, never PASS (rubric FC-6.2, which this lane also *implemented*).
    The instrument tests nothing for NEISO, and now says so out loud.
  - **PAIRED P1 FAILS AT FULL MAGNITUDE: cumulative 2026–2050 CO2 RISES 210.52 → 320.84 Mt
    (+52.4 %) under `carbon_price=25`.** Located in the CCS retrofit screen (base retrofits the
    whole gas-CC fleet by 2040: 13,049 MW gas_cc_ccs / 0 unabated; the carbon arm keeps 4,000 MW
    unabated with ~3 GW LESS CCS) plus a same-fleet **2026 dispatch-level** rise (+0.21 Mt).
    Root cause routed, **nothing tuned**. See item 2.
  - Three pieces of instrument work rode along: it **repaired `_annual_co2_tons`** so P1 can
    score a forecast bundle at all (P1 had been SKIPping "emissions absent" on every forecast
    path since the 2026-07-12 weekly — a standing gap); it implemented FC-6.2's vacuity check;
    and **it caught its own data-vintage leak** — the first battery output was solved against a
    clean tree curated from CURRENT `data/raw`, which two post-golden intakes had moved for
    NEISO, so it DELETED that output and re-ran from the golden's own `9e56f0f` raw bytes. The
    base arm then reproduced the golden's trajectory exactly, all 25 years × 13 fields and the
    full I1–I14 vector. Self-caught, self-corrected, recorded.
- **D22 LANDED** (PR #4476) — and the root cause is worth more than the intake. **FF-0F built
  the machinery but gitignored BOTH ends of the raw→clean chain**, so nothing in the
  raw→clean→scorer path was ever committed and FC-5 had no table to read; the loader docstring's
  "regenerated from committed raw" **was not true**. Landed: AEO2025 committed and its fetch made
  **key-free** (28 keyed requests → 6, fitting the DEMO_KEY budget) with a **refusal on truncated
  fetch** (the API silently caps JSON at 5,000 rows, which would drop regions with no error —
  rule 5); ERCOT CDR 2025 and PJM Load Forecast 2026 **machine-extracted, never hand-transcribed**
  (the rule-5 fat-finger hazard, stated as the reason). Corridor table **1,025 rows from 3
  sources**; missing-source list **7 → 5**. Contract extension: `peak_demand` / `energy_demand` /
  `reserve_margin` quantities, with `reserve_margin` marked INTENSIVE so `iso_totals()` **raises**
  rather than summing a ratio across regions. The CDR's ELCC-derated peak-contribution basis
  rides as a caveat in every CDR row rather than being silently mixed with AEO nameplate
  (rule 11). **StdScen2024 is unreachable by egress policy; four other sources are
  reachable-but-portal-blocked.** **FC-5 still SKIPs pending an authored disposition table —
  by design**, so the ceiling is measurably closer but NOT yet lifted (item 3).
- **ercot-248 LANDED** (PR #4484) **and corrected my charter's premise — recorded against
  interest.** The funded "2024/2025 all-resource SCED intake" was **a RESTORE, not an intake**:
  those publications were fetched by ercot-183 on 2026-08-09 and untracked as gitignored payload
  by BLOAT-B-5 item A2 on 2026-08-15, so they are simply absent from a clone. **`SCED-CT/README.md`'s
  coverage table was written 2026-08-04 — five days BEFORE that intake — and I scoped the charter
  off it without checking whether a later intake had superseded it.** The lane also overrode my
  **placement instruction, correctly**: the consumers' corpus glob is `YYYY-MM.part*.parquet`, so
  the per-day route I specified would have produced an invisible corpus. Verified restore:
  700/700 publication days, **88,561,421 rows**, every delivery month complete, 0 duplicate days,
  0 deliveries past 2025-12-31 (rule 22 intact), only the known permanently-unreachable
  2024-01-10..23 gap; the delivery-2023 offer-wall derive **byte-identical before and after**;
  the 27 HASL-less RTC+B parts quarantined by content, reproducing the documented set exactly.
  It also corrected the corpus **recovery doctrine**: `SHA256SUMS.txt` **cannot** accept a
  re-fetch restore, because parquet bytes are writer-version specific (tracked shards
  parquet-cpp-arrow 24.0.0 vs this writer's 25.0.1) — so it stays the identity record of the
  original bytes and a **writer-independent manifest** (delivery day, row count, column count per
  part) is added alongside, with five structural checks. **Director lesson: a README's coverage
  table is a claim with a date on it. Check whether a later intake superseded it before scoping a
  charter from it.**
- **nyiso-165 + nyiso-166 LANDED** (PR #4473) — the prompt landed as **two** sessions: nyiso-165
  found the defects, established the blast radius and deferred the repair to a data lane;
  **nyiso-166 executed it**. Both defects repaired at source and the reference regenerated for
  **every year it carries, 2018–2026** (data prep applied consistently across all years, rule 22
  — no year solved, scored or registered). The mandatory acceptance test **passes**: hour-by-hour
  parity with `nyiso164_nyca_shortage_check.py` — the independent construction — **8,759/8,759
  mapped hours, both tiers, all three years**, tail table and the **0/65 ceiling test** matching
  exactly. Keeper `2026-08-30-nyiso-159-loss-surface` re-verifies **NOT-YET on exactly
  {C3a-2025 −11.5 %, C3c}**; `audit_keepers --iso NYISO` PASS 0/0. **Magnitude: levels were
  overstated 1.8×–2.9×** — the 2025 NYC max $5,568.18 → **$2,146.50**, and the finding's own
  verdict on that number is the right instinct to institutionalise: *"a published price above
  every published penalty factor is a construction error by inspection."* Two secondary repairs:
  a raw-CSV fallback in `derive_nyiso_rcpf_overlay` that **re-implemented BOTH defects, one
  missing file away from firing**, DELETED rather than fixed (rule 23 `[R-DELETE]`); and
  nondeterministic column order fixed so the artifact is byte-reproducible. 9 regression tests
  pin the cascade invariant, the MAX end-to-end, the std-clock identity and the nyiso-164 parity.
  - **CORRECTION TO MY OWN r#22 RECORD:** the DST mismatch is **5,712** hours (65.2 %), not the
    5,710 I carried from the audit; the two-hour difference is the boundary-spill row, which the
    repair now discards. Immaterial to every conclusion, corrected because it is cited.
  - **OWED, and not delivered: the cross-ISO cascade SCAN.** My prompt asked for the max-not-sum
    rule to be scanned across the other five ISOs' reserve constructions (ISO-NE's
    TMSR ≥ TMNSR ≥ TMOR named as the obvious candidate) and reported per ISO. The finding
    discharges the NYISO matrix duty (§10, no cell moves) but carries **no such scan**. The
    generalizable half of the C3c audit's gift is therefore still on the table — item 4(g).
- **D17 — NOT LANDED. No PR, no branch, no commits.** Verified **by content** this time (the
  merged-PR list plus `list_commits` over `main`), which is the r#22 lesson applied rather than
  re-learned. It is a zero-solve Phase-0 lane, so it should have been quick; per the standing
  relaunch protocol I do **not** grade it lost — the owner is asked (item 4a).

**2. TWO PROGRAM-WIDE DEFECTS SURFACED THIS WAVE, both bigger than the lanes that found them.**
Neither was the lane's object; both were found because a lane looked at its own evidence
honestly.

- **(i) A CARBON PRICE RAISES CUMULATIVE CO2 BY 52.4 %** (D21's paired P1). This is not a gate
  cosmetic — P1 is, in the rubric's own words, "the model's economic core", and a sign error
  there is a claim about the model's fitness for the entire policy-scenario purpose the forecast
  program exists to serve. Two distinguishable legs are already visible in the committed arm
  summaries: a **capacity-side** leg (the CCS retrofit screen retrofits ~3 GW LESS under the
  carbon price — plausibly because an unabated CC that runs less has a smaller incremental
  retrofit uplift, which would be a *real* economics result rather than a bug, and must be
  distinguished from one) and a **dispatch-side** leg (2026, SAME fleet, +0.21 Mt — a same-fleet
  dispatch CO2 rise under a carbon price is much harder to explain benignly, since merit-order
  switching should move the other way). Chartered as **D23**, Phase-0, precommit-first,
  zero new mechanism.
- **(ii) ONE CACHE KEY, TWO DISPATCHES, BY CONSTRUCTION** (D4-M's R-5 upgrade). `cache_key()`
  **drops `_CACHE_KEY_OPTIONAL_FIELDS` members at whichever value is the live default**, so
  D4-M's key `f061b264…` is byte-identical to `d12c-armed`'s **while both storage fields
  differ**. D4-I3 §5.1 had reported two committed records of one key disagreeing on three scored
  quantities and honestly declined to assert a cause; the cause is now demonstrated. The reach is
  program-wide: **every default flip silently makes previously-cached results collide with new
  ones**, so any cross-vintage comparison is suspect until characterized, and the board now
  stamps two runs at one `cache_epoch` at different postures. Chartered as **D24**, Phase-0
  characterize-and-propose ONLY — a fix changes keys globally and invalidates caches, which is
  an owner-cost decision, not a lane's.

**3. THE t3 CEILING, HONESTLY SCORED.** Q16's premise was that neither FC-5 nor FC-6 existed, so
no golden could grade better than HOLD. After D21+D22: **FC-6 exists and grades** (FAIL, on real
evidence), **FC-5 has its table but still SKIPs pending an authored disposition table**. So the
ceiling is one step from lifted, and the remaining step is judgment work, not intake — chartered
as **D25**. The golden's determination is unchanged at HOLD either way, and Q16's hold on the
re-solve therefore still stands on its own reasoning.

**4. OWNER-TIER ITEMS OPEN AFTER THIS REFRESH:** (a) **D17 — is its session still running?**
(nothing landed; not graded lost per protocol) · (b) the **P1 carbon-sign failure** — D23 is
chartered but its eventual repair may reach the CCS retrofit screen, a shipped mechanism ·
(c) the **cache-key defect's fix cost** — D24 characterizes; the fix invalidates caches
program-wide and is an owner call · (d) **miso-192's D-4 posture options (i)/(ii)/(iii)**, still
unruled · (e) the **nyiso-161 winter-face waiver card** — the audit refresh's R-F parked it with
a fired trigger and nyiso-166 confirms it stays "filed and unruled" · (f) whether to fund the
**four portal-blocked FC-5 sources** (StdScen2024 is unreachable by egress policy — a different
class) · (g) the **owed cross-ISO cascade scan**, offered as a backcast prompt.

**5. DISPATCH RECORD (post-r#23): FOUR lanes issued** — **D19** (board reconcile 2, RELEASED:
both blocking writers landed and D8-V explicitly flagged its stale gate text to it; Fable) ·
**D23** (the P1 carbon-CO2 sign failure, Phase-0 precommit-first; Fable) · **D24** (the cache-key
optional-fields defect, characterize-and-propose only; **Opus**) · **D25** (the FC-5 disposition
table, the ceiling's last step; Fable). Charters: four new pack sections. **Collision map:** D19
writes cross-ISO board prose + gate cells; D23 and D24 write docs only (both Phase-0, nothing
built); D25 writes the FC-5 disposition artifact and re-scores FC-5 keys. D19 vs D25 both touch
`program-status.json` — distinct blocks (cross-ISO prose vs FC-5 rows), rebase-care stated in
both, the r#19 precedent. **All four prompts were pasted to the owner in chat this sitting; the
pack sections and this entry are committed locally and their push is HELD per item 0.**

**6. BACKCAST-TRACK WATCH.** **caiso-229 LANDED** (PR #4482): Phase-0 kill of the caiso-227 §G
below-stack wedge, zero LP; `cc_committed_offer_margin` U → **R**, refuted **on sign** (CAISO's
measured committed band is 1.030 against an armed 1.000, so the ERCOT below-cost committed form
has no CAISO analogue and a measured-faithful repair would move the floor the wrong way);
evidence appended without verdict change to three sibling cells. **miso-195 LANDED**
(PRs #4471/#4474): the remove-only measured outage-envelope cap REFUTED at the pre-frozen gate
(W4 conversion 16.9 % vs 25 %, and W6 feasibility — 6 cap-caused violation days in 2025 where
capped availability fell below measured EIA-930 output); **every composition of
`miso_native_outage_source` at the public record's aggregate grain is now adjudicated**, which
closes a lever family rather than a single cell. **The audit-program refresh landed** (PR #4465):
board to v17, rulings R-D/R-F/R-G executed (ERCOT wind decision map, nyiso-161 parked with a
fired trigger, Leg-2 closed by archive). **One backcast prompt offered this sitting:** the
cross-ISO reserve-cascade scan nyiso-166 did not carry.

## 0s. Refresh #22 (2026-08-31, HEAD `d44446e0`) — the r#21 wave lands 3/4 (D3 · D4-I3 · D8-RE); ERCOT DECLARED complete + frontier; the C3c scarcity program opened, chartered and already spent Q1+Q2; four lanes issued (D8-V · D4-M · D17 · D18)

**1. LANDING VERIFICATION of the r#21 four-lane dispatch** (measured against `origin/main` @
`d44446e0` plus a pruned remote-branch census — every claim from commits/PRs, not recollection):

- **D3 LANDED** (PRs #4455/#4458, precommit `f281895b` + finding `2dd85f02`). The MISO t1h
  `retire.total_gw` PASS→FAIL flip is ATTRIBUTED, and the headline is better than the lane's
  own title: **"retirement-volume regression" is the wrong name for it.** The G3 cap-grain fix
  moved MISO coal TOWARD reality (over-retirement +18.4 % → +9.1 %); the band failed because
  the bug's +1.018 GW of excess coal exits had been **compensating for 3.458 GW of real
  gas/oil exits the economic screen produces at 0.0**. The post-fix FAIL value is
  byte-identical to what FFR-2B measured under a PAIRED CONTROL a day before the fix existed —
  the FAIL is the model's stable number and the knife-edge −9.8 % PASS is the artifact.
  Classes (a) scorer-grain and (c) basis/vintage REFUTED. Fix stays (rules 1/14). MISO G3
  board row refreshed; no gate moved, no matrix cell (nothing tested).
- **D4-I3 LANDED** (PR #4460, `d44696a3` + the FR-6 code-comment home `857e4bbf`). Zero-solve,
  and decisive on its own object: **ERCOT I3 slack is an under-build signature**, monotone in
  the year's total added GW across all eleven committed T1-H records (0 % at ≥48.0 GW, 0.01 %
  at 39.9, 0.07 % at 27.8) and monotone in the resulting reserve margin. **No committed ERCOT
  posture clears I3 and the I12 band together — they are one phenomenon, not two.** The lane
  also FROZE an eight-point pre-declaration (P-1..P-8) with four falsifiers for the first
  post-arming T1-H, and routed six repairs. Two measurement-integrity findings came with it:
  (§5.1) two committed records of ONE cache key disagree on three independent scored
  quantities, so **an ERCOT I3 magnitude is comparable only within a solve vintage**; (§5.2)
  the I3 instrument emits `% of load` and nothing else — no hours, no MW, no GWh.
- **D8-RE LANDED** (PR #4457, `fca34aae`) and **executed the cross-lane re-grade rule against
  its own interest**: one key re-emitted (`neiso-t1f-s4bcontrol`, FC-7 CAVEAT → PASS,
  determination unchanged), and **two committed-verdict flips STOPPED and routed** rather than
  published — `neiso-t1f` and `nyiso-t1f` each move PROMOTE-WITH-CAVEATS → PROMOTE with an
  empty caveat list, which would be NEISO's and NYISO's first clean FC maps. Controls first:
  each key re-scored without `--dof-ledger` reproduced its committed record byte-for-byte, so
  the ledger input is provably the only delta. PJM's and MISO's ledgers measured read-only.
- **NEISO-RC-R — NOT GRADED.** No branch `claude/capx-neiso-rc-repair` on the remote, no
  commits, no finding. Under the r#20/r#21 relaunch protocol that is **not evidence of loss**:
  the T3 golden was graded lost on exactly this signature and landed on its own. The question
  goes to the owner this sitting (item 6); the charter stays binding and unchanged either way,
  and **nobody launches a second one** until the answer is in.

**2. THE MARKER MAP MOVED — ERCOT IS THE THIRD `complete` ISO** (ercot-247, PR #4454,
`4bc8745a`; owner verbatim *"I think you can declare it complete / frontier"*). Verified in
`calibration-complete.json` this sitting: **`complete` = {ERCOT, NEISO, PJM}**, `final` still
EMPTY, `withdrawn` = {NYISO, CAISO}, freeze still tier-scoped to the locked test. ERCOT's entry
rests on the ercot-246 ruling (a partitioned keeper's ISO-level determination is the WORST
config determination over the DESIGNATED spans): forward config `2026-08-25-234-eastex-identity`
on {2024, 2025} CALIBRATED with C3c the lone ledgered caveat ×2, 2023 carve-out
`236-swcap-clip-k33` CALIBRATED with zero caveats, and the keeper's REGISTERED unrestricted
3-year NOT-YET stands published untouched. `audit_keepers` M1b was extended partition-aware in
the same commit. **Consequence for this track: ERCOT's gate (a) now passes on the literal
test**, which is a board fact no lane has yet written — routed into the next board reconcile
(item 5).

**3. THE C3c SCARCITY PROGRAM EXISTS, IS CHARTERED, AND HAS ALREADY SPENT BOTH ITS MEASURABLE
QUESTIONS** — the r#21 open card (b) is CLOSED by owner act. `docs/CHARTER-c3c-scarcity-program-2026-08-31.md`
scopes it and is worth reading for its cross-ISO census alone: **the blanket framing carried in
several ledgers is wrong** — "an hourly LP with $0 reserve offers cannot form the RT scarcity
tail" is not uniform, since PJM forms 54–67 % of its tail in the same LP and passes all three
years, against CAISO/NEISO's flat 0.00×. Both questions are now answered:
- **Q1 (pjm-164, PR #4456): PJM's reserve-dual channel is REAL, not the ercot-214 phantom.**
  The audit that could have invalidated a CALIBRATED keeper was run because it could, and it
  came back clean; PJM binds on reserve OPPORTUNITY COST (max dual $187.90, zero shortfall
  hours ever), which is real co-optimisation doing real work.
- **Q2 (nyiso-164, `e983bf50`): the pre-registered kill gate FIRES ON BOTH CLAUSES** — NYISO's
  C3c ledger is CONFIRMED on its own evidence, not corrected and not inherited from CAISO.
- **Q3 is an architecture decision, not a lane** (stochastic / multi-settlement representation
  vs rules 4, 8 and the no-MIP constraint), and the charter's own recommendation is NOT to open
  it. Put to the owner this sitting (item 6).

**4. QUEUE RELEASED, AND ONE LANE RE-SCOPED.** D4-I3's landing releases **D4-M**, the
measurement half — and the r#21 note "sequence D6 after D4-I3" was carrying a real ambiguity
which is corrected here: **D6 (the FC-3 curve-ON over-fire, four T1-H curve legs) is NOT the
vehicle for the ERCOT post-arming measurement.** ERCOT is curve-OFF (energy-only); the four
curve legs are the capacity-market ISOs. Folding an ERCOT measurement into a curve-ON lane
would have measured two things in one run and named it after the wrong one. So the ERCOT
post-arming T1-H is chartered on its own as **D4-M** (with D4-I3's R-4 instrument grain riding
in front of it, per that finding's own sequencing), and **D6 stays QUEUED and still uncharted**
— it needs a written charter before it can be dispatched, and its object is now partly
illuminated by D3 (MISO's FC-3 retirement half is a missing exit channel, not a volume miss).

**5. DIRECTOR DECISIONS TAKEN THIS SITTING** (recorded so they are not re-litigated):
- **The seven legacy legs' reconstructed `run_config`s (D8 §6, explicitly a director call):
  DO NOT ADOPT THEM AS ORIGINALS.** Adopting them would flip seven committed FC-7 `run_config`
  rows FAIL → PASS, and the scorer has no notion of a `reconstruction` label — so the flip would
  assert provenance the artifacts do not have, which is precisely what FC-7 exists to measure.
  The admissible route, if the debt is ever worth closing, is a scorer that RECOGNISES a
  `provenance: "reconstruction"` label and scores it **CAVEAT — never PASS**: the honest middle,
  and the same "report both bases, never silently replace" discipline signed as D-9(ii) and
  carried by NEISO-RC-R's R3(ii). That is a chartered lane of its own (queued as **D20**), not
  a records edit, and D8-V is explicitly barred from it.
- **Board cross-ISO prose is stale in four places and needs its own lane, not a rider.** The
  golden's own `flagged_not_edited` routed three (the `tier_ladder` T3 row still reads
  "deferred"; the `readiness` prose still calls a ten-hour golden a projection when the campaign
  MEASURED 29.2 min; `gate_reading`/`headline` were written for a board on which no ISO held
  leg (d) — NEISO now holds and has SPENT it), and item 2 adds a fourth (ERCOT's gate (a)).
  Queued as **D19**, deliberately AFTER D8-V and D4-M land so it reconciles to a settled board
  rather than to one being written under it (the D13 precedent).

**6. DISPATCH RECORD (post-r#22 sitting): FOUR lanes issued, collision-mapped.**
**D8-V** (FC-7 ledger completion — re-verify and publish the two stopped flips through each
AFFECTED lane's own record, then close PJM and MISO; Fable, because two ISO determinations
move) · **D4-M** (ERCOT post-arming T1-H against D4-I3's frozen P-1..P-8, with R-4's instrument
grain landed first; **Opus** — the discretion was spent ex ante, so this is execution) ·
**D17** (D3's routed PRIMARY: MISO's missing non-coal economic exit channel, Phase-0 zero-solve,
precommit-first; Fable) · **D18** (D4-I3's routed R-6: the 13 undeclared invariant rows and the
misattributing `dominant_open_causes.I3` line; **Opus**, records sweep). Charters: four new pack
sections.

**Collision map.** `ff-verdicts.json` + `program-status.json`: D8-V writes the NEISO/NYISO/PJM/
MISO **t1f** keys and FC-7 rows; D4-M writes the **ERCOT** block and its own new T1-H key —
distinct keys/blocks, rebase-care lines in both prompts, the r#19 precedent.
`invariant-failures.json`: D18 owns exactly the 13 enumerated PRE-EXISTING rows, D4-M owns only
the row for the run it registers (that file's own convention assigns a declaration to the
registering lane) — boundary stated in both. D17 writes docs only. And **if NEISO-RC-R is still
running**, its keys are the NEISO **crossover/capxd14** ones — D8-V is barred from `neiso-t1x`
and `neiso-t3` in its charter, so the two do not meet.

**THE CENSUS D18 ACTS ON WAS RE-DERIVED HERE, NOT TAKEN ON TRUST.** D4-I3 reported 13 sidecars
carrying an undeclared invariant FAIL; the director re-derived the set independently from the
committed sidecars this sitting and got the same 13, ident for ident. The list is written into
D18's charter with an instruction to verify it a third time and report any difference rather
than adopt either. (This container has no numpy — DATA PROFILE `code` — so the real checker
could not be run here; the reconciliation is arithmetic over the committed JSON.)

**7. OWNER-TIER ITEMS OPEN AFTER THIS REFRESH:** (a) **NEISO-RC-R — is its session still
running?** (blocks grading; relaunch protocol) · (b) the **T3 golden's R-A re-solve** — the
campaign records the PRE-R-A unarmed storage-entry posture, its headline structural result is
ZERO storage entry in 25 years, and R-A armed exactly the storage-entry mechanisms; a re-solve
is a SECOND campaign outside Q13's "this campaign only" scope, so it needs an owner act ·
(c) **C3c program Q3** (the probabilistic RT premium — an architecture decision the charter
recommends NOT opening) · (d) the **ERCOT 2024/2025 SCED conduct-corpus intake** (ercot-245's
named unblock, now that ERCOT is `complete` + frontier) · (e) the **nyiso-161 winter-face
waiver card**, still unruled — the owner took the C3c question in preference to it · (f)
**miso-192's D-4 posture options (i)/(ii)/(iii)**. **CLOSED since r#21:** the caiso-227 arm
funding (owner funded it; caiso-228 executed and it died at gate D1 with no solve) and the
chartering of the C3c program's first lane (item 3).

**8. BACKCAST-TRACK WATCH (deconfliction only).** **miso-193 CONCLUDED** (PRs #4462/#4463/#4464):
`cc_duct_peaking` examined end-to-end in MISO, both A/B legs registered, cell U → K, keeper
`2026-08-30-miso-191-bexit` unchanged (NOT-YET on {C3a-2025} alone). **caiso-228 CONCLUDED
without a solve** (PR #4461): the SoCalGas OFO gas-deliverability arm dies at gate D1 and the
kill is **size-independent** — the band's import limb is delivered across the WECC seam, so no
gas-side quantity mechanism of any magnitude can lift λ past $200 in CAISO's measured tail
hours; caiso-131 A3 answered negatively and conclusively. **pjm-164 / nyiso-164** are the C3c
program's Q1/Q2 (item 3). No backcast prompt is offered this sitting — the track has no owed
lane, only the owner cards at item 7.

**MID-SITTING AMENDMENT (same sitting, after the r#22 dispatch pushed and merged as PR #4469).
Four owner rulings taken, and the batch's first grading correction — made against my own
census, not someone else's.**

**A. NEISO-RC-R LANDED IN FULL — the owner was right and my census was wrong.** Not "still
running": PR #4467 was already merged when I asked. R2 (`eabbae85`), R1 (`aa9240a2`), R3
(`63a61a24`), R4 (`0f68e035`), the Phase-B precommit (`5ba8beb1`) and the graded verification
(`b7bc32c3`) are all on main. **Why I missed it: I censused by BRANCH STEM.** The charter names
`claude/capx-neiso-rc-repair`; the lane ran on `claude/neiso-rc-repair-fymtkz`, so a
`git branch -r | grep capx-neiso-rc` came back empty on a lane that had already landed.
**STANDING LESSON, and it is a sharper one than r#21's:** the relaunch protocol says an absent
branch is not evidence of loss — this says the branch census itself is not evidence of
anything. **Grade by CONTENT: `git log origin/main --grep=<LANE-ID>` and the merged-PR list,
never by branch name**, because a lane's branch stem is the session's to choose and only the
lane ID is stable. (r#21 recorded the first half of this lesson against interest; this is the
second half, recorded the same way.)

**What NEISO-RC-R measured, at full magnitude** (`FINDING-capx-neiso-rc-repair-*`, §10):
ONE treatment solve, the capxd14 launch verbatim at post-repair HEAD — **cache key identical,
because the repairs are input-level**. Registered preserve-then-overwrite (`neiso-t1x` → the
new run, control preserved verbatim as `neiso-t1x-pre-rcrepair`); **HOLD → HOLD, no committed
verdict flipped**, so the cross-lane re-grade rule never had to fire. The prereg splits:
- **The R2 curve leg MISSES, as its own mechanical amendment pre-declared** — the re-derived
  FCA curve is **near-inert at the model's long positions** (the 2024 screen sits at position
  1.295 and pays $0 under BOTH curves; the 2025 coal reversal survives the *less* generous
  curve on ~$205/kW-yr of reserve uplift). The degenerate $0 bar was not what was holding the
  composition.
- **The Mystic-instrument leg HITS:** 1,464 MW moves economic → confirmed (706.7 MW derate +
  706.7 drop + Potter 50.5), and **the derate half is visible ONLY through R3(iii)** — the
  `confirmed_derates` blind spot the charter predicted would silently swallow exactly these
  exits. Level ≈ control (3.635 vs 3.563 GW): **confirmed exits displace the floor budget
  ~1:1**, which is the honest reading of why a better instrument did not move the total.
- **The dual basis is the headline number:** vintage-consistent reads **+24.2 % OVER** where
  the full-window basis reads **−27.3 % UNDER**. Both are reported side by side per the signed
  D-9(ii) discipline; neither silently replaces the other. Recall 2/4 on the D-24 reachable
  set. R4 answers the Phase-0 open question: **Merrimack coal WAS decided in-window** (438.5 MW,
  loss-year 2023) and **REVERSED in 2025**.
- Misses recorded, nothing re-tuned (R6 held).

**B. THE C3c PROGRAM'S OWN AUDIT LANDED (PR #4466) AND IT RETRACTED A FALSE POSITIVE OF ITS
OWN.** An independent replication of Q1+Q2 under owner ruling R-E, run without sight of
pjm-164/nyiso-164 (whose verdicts stand first). **Q1 = REAL, replicated by a DIFFERENT
construction** (model positive-dual hours vs PJM's published reserve-market record, not model
tail vs actual LMP tail): the model requirement is an exact published identity in 26,229
family-hours with zero exceptions; ORDC shortfall is identically zero in all 52,560
family-hours, so the dual is opportunity cost bounded below the published $300 penalty step;
overlap with PJM's posted penalty-step intervals at **75–91× base rate, p ≤ 9.7e-11**; and the
model **under**-prices reality by 2.7–7×. **Q2 = CONFIRMED — after the session RETRACTED its
own opposite finding.** It first measured "reality WAS NYCA-short", then re-derived from raw
CSVs, reproduced nyiso-164 exactly including the ceiling test at 0 of 65 tail hours, and traced
the false positive to **two real defects in a committed reference**,
`data/raw/_validation-source/actual_as_reserve_NYISO.parquet`: (i) `build_reference` **SUMS**
`spin_10 + nonsync_10 + op_30` although NYISO's products are a **cumulative cascade**
(spin_10 ≥ nonsync_10 ≥ op_30 in **100.0000 %** of 289,344 rows), triple-counting one shadow
price; (ii) naive prevailing timestamps mapped positionally onto the fixed `Etc/GMT+5` 8760
clock, **off by an hour in 65.2 % of the year**. No keeper, scored result or determination
depends on that file — its sole consumer is the disarmed RCPF comparator — so it is **a trap
for diagnostic sessions, not a defect in any result**. Filed for repair, not repaired; the
defective probe is retained unrepaired as the reproducible record, marked SUPERSEDED. **The
generalizable instrument rule it hands to five other ISO lanes: a nested reserve cascade must
be MAXED, never SUMMED.** Routed here as the offered backcast prompt at item F.

**C. FOUR OWNER RULINGS — Q16 / Q17 / Q18 / Q19** (§3 rows added):
- **Q16 — the T3 golden's R-A re-solve: HOLD, AND FIX THE CEILING FIRST.** Not a deferral for
  cost: the reason is that **FC-5 and FC-6 are REQUIRED at t3 and neither instrument exists for
  any ISO**, so no golden can score better than HOLD regardless of model quality. Re-solving
  into an ungradeable ceiling would spend a second campaign to learn nothing. The golden stands
  as registered with its posture-epoch caveat visible, and **nothing quotes it as a post-R-A
  result**. Execution = the two ceiling lanes at item D.
- **Q17 — C3c program Q3 (the probabilistic RT premium): DO NOT OPEN**, at the charter's own
  recommendation. It collides with rules 4 `[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint,
  and crossing that residual needs a different model class. **The C3c program therefore CLOSES**
  having answered both measurable questions and confirmed the ledger for PJM and NYISO — a
  program that closes on evidence rather than drifting is the intended outcome, not a shortfall.
- **Q18 — the ERCOT 2024/2025 all-resource SCED conduct-corpus intake: FUNDED.** ercot-245's
  named unblock. Backcast-track, so it is OFFERED as a prompt (item F), not chartered here.
- **Q19 (implicit in Q16's wording, recorded so it is not re-litigated): the ceiling is built
  BEFORE any second golden**, in the order FC-6 then FC-5 — FC-6 because its tooling already
  exists (`scripts/run_driver_battery.py`) and it is merely un-run, FC-5 because its gap is an
  eight-source intake behind one new curated datatype.

**D. TWO MORE LANES ISSUED (Q16 execution), bringing this sitting to SIX:** **D21** (FC-6
driver-battery + paired P1–P3 for the golden — price the ladder before running it; Fable,
neiso) and **D22** (FC-5's `benchmark-corridor` datatype + the rubric §6 intake list —
**data-contract and intake ONLY, no scorer edit**, which is what keeps it clear of D8-V's live
re-scores; Opus, code). Charters: two new pack sections. **Collision map holds:** D21 writes
`neiso-t3`'s FC-6 row and the golden bundle — D8-V is barred from `neiso-t3`, D4-M is ERCOT,
and NEISO-RC-R has now LANDED so its `neiso-t1x` writes are settled history rather than live
contention. D22 writes `data/` + `data/dictionary/` + `scripts/data/` and touches no verdict
file at all.

**E. ALSO LANDED, watch only:** **miso-194** (PRs #4468 + `cd262385`/`c025a579`): the MISO
cold-snap gas derate is **REFUTED on W4 absorption** at phase-0 census, cell U → **I** (inert),
keeper unchanged — a clean negative, and the MISO lever queue is stamped.

**F. TWO BACKCAST-TRACK PROMPTS ISSUED to the owner this sitting** (offered and handed over,
never chartered as capx lanes — the backcast track is the owner's; the ercot-245-R / miso-191
precedent): **ercot-248**, the ERCOT 2024/2025 ALL-RESOURCE SCED conduct-corpus intake funded
by Q18; and **nyiso-165**, the AS-reserve reference repair routed by the C3c audit. Both
recorded in §2. Two things the director checked before writing them, so the prompts rest on
disk facts rather than on the findings' prose:
- **ercot-248's gap is exactly one span, and the fetcher already supports it.**
  `data/raw/ercot/SCED/` holds ALL-RESOURCE delivery 2022-12-31 … 2024-01-09 (315 shards);
  `SCED-CT/` holds CT-ONLY 2024-01-24 … 2025-12-31. The intake is the second span unscoped —
  the same `fetch_ercot_60day_sced_gen_resource.py` with `--resource-types` OMITTED. **The
  prompt is Opus, not the Sonnet an additive intake would normally get** (rule 27): the
  corpus README's own scope warning is that consumers glob `data/raw/ercot/` and
  `.../SCED/` and read every parquet found as an all-resource day, so a mis-placed or
  mis-typed shard SILENTLY understates every class share computed from the corpus — that
  placement call is infrastructure judgment, and the prompt requires an old-span
  before/after regression check to discharge it. Two live constraints carried in: MIS
  retention is a rolling ~2.3 yr so README Gap 1 **grows** and today's reachable boundary
  must be MEASURED, not assumed; and `--max-delivery-date` (2025-12-31) refuses 2026 days
  because H1-2026 is the locked-test tier — the prompt forbids overriding it.
- **nyiso-165 has a written acceptance test, so the repair is verifiable rather than merely
  plausible.** The corrected re-derivation reproduces $306.74 / $254.62 / $393.31 and 0-of-65
  tail hours; the prompt makes reproducing those the pass condition and forbids adjusting the
  target. It also requires the "no keeper depends on this file" claim to be RE-VERIFIED per
  consumer rather than inherited, with a stop if any committed determination would move
  (cross-lane re-grade). **The cross-ISO half is corrected from the audit's framing:** NYISO
  is the ONLY ISO with a committed `actual_as_reserve_*` reference, so there are no five
  sibling files to fix — the max-not-sum rule becomes a SCAN of the other ISOs' reserve
  constructions (ISO-NE's TMSR ≥ TMNSR ≥ TMOR the obvious candidate), reported per ISO and
  repaired in none of them (rule 25).


## 0r. Refresh #21 (2026-08-31, HEAD `50fd46c1`) — the relaunch wave LANDS 3/3 (D12-A-R · S-123-V-R · S-6-R); OWNER CORRECTION: the NEISO golden was NEVER LOST (still running) — T3-GOLDEN-R RECALLED unrun; MISO promotes miso-191; ercot-245 KILLED on its own census

**1. OWNER CORRECTION (this sitting): the T3 NEISO golden is STILL RUNNING.** r#20's grading
of T3 as "session lost mid-solve" was WRONG — recorded against interest (the branch census
read 0 unique commits and no registration, which is exactly what a long solve mid-flight
looks like; absence of landing is not evidence of loss). **T3-GOLDEN-R is RECALLED UNRUN**
(never dispatched — no branch, no commits; the pack §T3 relaunch annotation is amended to a
recall notice). NOBODY launches a second golden: the NEISO keys of `ff-verdicts.json` +
`program-status.json` remain the running session's to write, and the Q13 authorization
covers ONE campaign. Standing lesson for future relaunch sittings: before grading a
solve-carrying lane LOST, ask the owner whether its session is still running — a ~1 h+
solve lands nothing observable until it finishes.

**2. RELAUNCH-WAVE LANDINGS — 3 of the 3 dispatched capx relaunches landed:**
- **D12-A-R LANDED** (PR #4429): the orphan branch's work re-verified per the r#20 protocol
  and landed — `entry_margin_exhaustion` + `entry_forward_reserve_leg` armed as ERCOT
  forecast defaults per Q15, matrix stamped (cells → K-forecast-armed), the re-verification
  recorded in the finding (`3415f456`).
- **S-123-V-R LANDED** (PR #4441 + `99ffb2ce`): the verification re-measure run and
  registered, S-123 finding §6 FILLED with measured results, MISO board refreshed. The
  S-123 package is now COMPLETE (scoreboard row LANDED-PARTIAL → LANDED).
- **S-6-R LANDED** (PR #4436): `pjm-2026-2030-s6-ledger` registered, bare `pjm-t1f`
  re-scored preserve-then-overwrite, PJM board block refreshed. **Headline: PJM's FC-1 FAIL
  set is {I7, I12}, not I7 alone** — the measured three-year I7 fail set restated onto the
  board; the finding corrects the prior "I7 is the only FC-1 failure left" reading. (Stray
  duplicate branch `claude/capx-s6-pjm-ledger-relaunch-p5kb8w` points at already-merged
  commits, 0 unique — safe to delete.)
- Model-economy readback (r#20 item 4): S-6-R and S-123-V-R ran their pre-declared charters
  on **Opus** and landed clean — the doctrine's first confirming instances.

**3. QUEUE RELEASED BY THESE LANDINGS:** **D4-I3 dispatchable** (D12-A-R landed and
ercot-245 concluded — ERCOT surfaces free) · **D3 dispatchable** (S-123-V-R landed,
miso-191/192 concluded — MISO surfaces free; start-time collision check vs any new MISO
branch stays in its prompt) · **D6** next batch as before · **D8's verdict/board
re-emission stays DEFERRED behind the golden** (the last of the three namespace writers
still in flight) · **NEISO-RC repair phase** remains a next-batch decision on its landed
Phase-0 finding.

**4. BACKCAST/AUDIT MOVEMENT (watch only):**
- **ercot-245 CONCLUDED — KILLED on its own census** (PR #4443): K-A (ST mass), K-C (both
  years, all legs) and K-T (T-1 CC/ST, T-2 p95) all fire; **Phase-1 NOT licensed, the A/B
  license never spent** — the precommit's stop rule executed exactly. Per its §8, the
  2024/2025 all-resource SCED conduct-corpus intake is the named unblock — an owner call.
- **MISO KEEPER → `2026-08-30-miso-191-bexit`** (PR #4433): the miso-190-named successor
  executed (binning-aware exit-cohort delivery), A/B registered control + arm, matrix cell
  `partial_plant_exit_carry` R → K; determination **NOT-YET on {C3a-2025} ALONE**, C6
  attested. **miso-192 landed** (PRs #4437/#4440): D-4 posture sitting — `chp_btm_measured`
  REFUTED zero-solve (U → R); the D-4 posture question returns to the owner better-posed
  (three options, `FINDING-miso192-chp-btm-phase0-2026-08-31.md`).
- **NYISO:** nyiso-162 re-verified the parked Leg-2 object against the live keeper (R-C;
  PR #4431); **nyiso-163** (PR #4438) built + pre-validated the on-receipt AORR
  identifiability gate and verified the Leg-2 access route — winter face stays
  identification-blocked, determination NOT-YET on {C3a-2025, C3c}; **the owner's action is
  one request** (the Applications-layer AORR record). Next shorthand: nyiso-164.
- **CAISO:** **caiso-226 LANDED** (PR #4435) — the A3 OFO intake funded and executed through
  the full data contract (gas-ofo-events schema + immutable SoCalGas snapshots + rule-13
  adjudication); **the caiso-227 arm is PRE-REGISTERED and UNFUNDED — an owner call** (filed
  item 11). Terminal rest otherwise unchanged; next number caiso-227.
- **T1-H storage-entry Leg A ARMED** (PR #4442, owner ruling R-A). **C-1 joint wind A/B
  landed** (PRs #4430/#4432/#4439): both kill-gates PASS, joint posture NON-COMPLEMENTARY on
  wind. Audit records v16 refreshed (PR #4434).

**6. DISPATCH RECORD (post-r#21 sitting, owner: "issue prompts"):** THREE lanes issued,
collision-mapped — **NEISO-RC-R** (the repair phase: R2 curve re-derivation + R1 registry
intake + R3 scorer trio + R4, per the Phase-0 finding §6/§9; Fable, neiso; golden care lines
— never the t3 or bare neiso-t1f keys) · **D3** (the MISO t1h `retire.total_gw` PASS→FAIL
flip, attribution-first, zero-solve Phase 0, precommit-first; the I13 cobweb closure is
treated as OPEN, not a settled repair; Fable, miso) · **D4-I3** (ERCOT I3 scarcity-slack
half ONLY, card Y-C boundary respected; zero-solve breach-set measurement + pre-declared
post-arming expectation + the FR-6 code-comment home; **Opus** under the r#20
model-economy doctrine — the cause is already characterized, the lane measures and routes).
**D6 stays HELD one more batch** (its four T1-H curve legs are the natural post-arming
measurement vehicle and contend with D4-I3's expectation half — sequence D6 after D4-I3
lands). Charters: the three new pack sections.

**MID-SITTING AMENDMENT (same sitting, before this dispatch pushed):** the **T3 GOLDEN
LANDED** — the ORIGINAL running session finished its solve and registered the first §2.1b
full-horizon campaign (PRs #4447/#4452, branch `capx-t3-neiso-golden-r2-74wk0h`; the r#21
recall stands CORRECT — this is the original campaign completing, not a second launch; the
R-A posture-epoch caveat is recorded on its own record). Consequences executed here:
(a) **D8-RE is RELEASED and ISSUED** (fourth prompt this sitting, **Opus**) — all three
namespace writers (S-6, S-123-V, golden) have landed, so the deferred verdict/board
re-emission can run; (b) the NEISO-RC-R golden care line relaxes to the standing form
(never write the t3 or bare `neiso-t1f` keys — they are simply not its keys); (c) **D3's
start-time collision check has a live object**: `miso-193` (cc_duct_peaking, backcast) is
mid-A/B with sections pending — distinct namespace (backcast vs D3's forecast board), so
D3 proceeds but must not touch miso-193's surfaces. Also landed mid-sitting, watch only:
**ercot-246** (ISO-level determination of a partitioned keeper = worst config over
designated spans — ERCOT reads CALIBRATED), ercot-245's FINDING/log/matrix records
(PRs #4448/#4451), **caiso-227** (C3a-2025 root cause measured, honest null; Helms
ps-water-state intake landed, PR #4450), and **nyiso-163b** (owner ruling: the AORR access
route is CLOSED permanently and a C3c scarcity program OPENS — the NYISO route question has
moved; next NYISO lane is that program's, chartered on its own record).

**7. OWNER-TIER ITEMS OPEN AFTER THIS REFRESH:** (a) the nyiso-161 winter-face-waiver card +
the one-request AORR Applications-layer ask (nyiso-163); (b) miso-192's D-4 posture options
(i)/(ii)/(iii); (c) caiso-227 arm funding; (d) the ERCOT 2024/2025 SCED conduct-corpus
intake (ercot-245's named unblock); (e) the NEISO-RC repair-phase decision; (f) D8
re-emission timing once the golden lands.

## 0q. Refresh #20 (2026-08-31, HEAD `ee75a0b`) — THE RELAUNCH SITTING: the r#19 wave graded (four lanes LANDED, four sessions LOST); everything unlanded restarts FRESH; model-economy doctrine (Opus for pre-declared execution, Fable for adjudication)

**1. OWNER INSTRUCTION (this sitting):** relaunch the calibration workstream; anything that was
in flight and has not LANDED restarts fresh; assign Opus wherever the lane allows it, to
preserve Fable capacity. Sitting held in session branch
`claude/calibration-workstream-relaunch-bml7zm` (one sitting, one refresh, ledger edited from
there).

**2. LANDING VERIFICATION of the r#19 eight-lane wave** (measured against `origin/main` @
`ee75a0b` plus a pruned remote-branch census — every claim below is from commits/PRs, not
recollection):

- **LANDED (4):** **CAISO-224-FIN** (PR #4415, verified at §0p.6 — Q14 arc closed) ·
  **NEISO-RC Phase-0** (PR #4422 — finding-only as chartered; repair phase = next-batch
  decision) · **D16 seam guard** (PR #4423 — fail-closed refusal shipped) · **D8** (PR #4427 +
  `49400c5`/`298b8e8`/`e6b57c0` — the FC-7 instrument + the seven-leg run_config provenance
  record; **verdict/board re-emission still DEFERRED as chartered**, see item 5).
- **LOST (4) — session containers reclaimed before landing; per the owner instruction each
  restarts FRESH:**
  - **S-6**: the pre-declaration LANDED (PR #4418,
    `docs/handoffs/FINDING-capx-s6-pjm-ledger-2026-08-30.md`, which ends at the
    "*(Sections below were written AFTER the solve.)*" sentinel with nothing after it). The
    solve, the FC re-score, the `pjm-2026-2030-s6-ledger` registration, the
    preserve-then-overwrite verdict keys and the PJM board refresh are ALL owed. Branch
    `claude/capx-s6-pjm-ledger-uihbbp` open at 0 unique commits.
  - **S-123-V**: nothing landed — no branch, no commits; the S-123 §6 verification TBD is
    still open and the MISO 2.5× overshoot verdict still rests on unverified terms.
  - **T3 golden**: mid-solve loss. The enabling `register_forecast_run.py` fix LANDED
    (PR #4408); branch `claude/capx-t3-neiso-golden-74sq45` open at 0 unique commits; no
    registration, no verdict key, no board write ever happened.
  - **D12-A**: **ORPHAN BRANCH** `claude/capx-d12a-arming-0ibtzh` at 2 unmerged commits
    (`7585ed0` arms `entry_margin_exhaustion` + `entry_forward_reserve_leg` as ERCOT forecast
    defaults per Q15; `d851cb3` stamps the matrix; 801 insertions incl. `scenarios.py` /
    `iso_configs.py`) — pushed, never PR'd, never verified, NOT landed. The relaunch session
    treats that branch as EVIDENCE, never blind-merges it: re-verify the diff against the Q15
    ruling and the pack §D12-A charter (cache-epoch verification included, rule 27
    blob-verification on every ≥300-line file), then land it re-verified or redo it clean.

**3. RELAUNCH WAVE — four capx prompts re-issued.** Charters are UNCHANGED: the committed pack
sections (`capx-director-prompt-pack-2026-08.md` §§T3-NEISO-GOLDEN / D12-A / S-6 / S-123-V)
remain binding; each relaunch prompt carries only the deltas in item 2. Collision map
unchanged from r#19 (golden / S-6 / S-123-V write DISTINCT ISO keys of `ff-verdicts.json` +
`program-status.json`, rebase-care; D12-A writes ERCOT config/matrix only and touches neither).

**4. MODEL-ECONOMY DOCTRINE (owner instruction, standing):** a lane whose discretion was
already spent in a committed binding pre-declaration/precommit (constructions, kills and
decision rules frozen ex ante) is EXECUTION and runs on **Opus**; a lane that ADJUDICATES
(arming decisions, kill-grading on a novel object, mechanism design, determination/marker
consequences) stays **Fable**. Rule 27's floor is unchanged: Sonnet never touches
infrastructure; purely additive data-intake/docs lanes stay Sonnet-eligible. Applied:
**S-6-R / S-123-V-R / T3-GOLDEN-R → Opus** (fully pre-declared execution);
**D12-A-R → Fable** (forecast-default arming + orphan-branch adjudication). Director and
owner-sitting sessions stay Fable.

**5. QUEUE AFTER THIS BATCH:** D3 dispatches after S-123-V-R lands (same MISO board/verdict
surfaces) · D4-I3 after D12-A-R (ERCOT surface contention) · D6 next batch (likely
zero-solve-diagnosis scope) · **D8's deferred verdict/board re-emission stays deferred until
golden / S-6-R / S-123-V-R land** (they write sibling keys of the same files) · NEISO-RC
repair phase is a next-batch decision on its landed Phase-0 finding.

**6. BACKCAST-TRACK WATCH (deconfliction only — backcast prompts are handed to the owner, not
issued by this ledger):** **ercot-245 died mid-lane** — the precommit + Amendment 1 + the
680-line census probe LANDED (PRs #4417/#4421,
`docs/PRECOMMIT-ercot245-commitment-state-phase0-2026-08-30.md`), but the census run, kill
grading, FINDING, log entry and matrix evidence are owed; relaunch prompt handed to the owner
(**Fable**; dispatch strictly AFTER D12-A-R lands — shared ERCOT matrix shard). **nyiso-161**
delivered `DECISION-CARD-nyiso161-winter-face-waiver-2026-08-30.md` (PR #4420) — an OWNER
card, pending ruling; no NYISO lane until ruled. **caiso-225** watch sweep landed (PR #4425):
all armed watches NULL, terminal rest re-affirmed, next sweep DATED (≤ 2026-12-01) — no CAISO
relaunch. **miso-190 concluded REJECTED on its own PREREG** (kill 2; cell U→R, keeper
unchanged); its named successor (binning-aware unit-grain exit timing) is unchartered — a
miso-191 charter prompt is offered to the owner (**Fable**). **T1-H storage-entry Leg A
landed** (PRs #4419/#4426; both kill-gates passed, ERCOT cells U→O) — the successor is the
audit track's, not this wave's. Keepers, markers and the freeze verified unchanged this
sitting: `complete` = {NEISO, PJM}, `final` EMPTY, freeze tier-scoped to the locked test.

## 0p. Refresh #19 (2026-08-30, HEAD `c0a35ce`) — OWNER VOIDS THE CROSS-SESSION HEAVY-SLOT QUEUE; five lanes issued at once (S-6 · S-123-V · NEISO-RC · D16 · D8); max safe parallelism is the new doctrine

**1. STANDING DOCTRINE CORRECTION (owner instruction, r#19): THERE IS NO CROSS-SESSION HEAVY
SLOT.** The director had been serializing "heavy" solves (PJM 8.8 / MISO 9.6 GB "no-co-run")
across SESSIONS — an over-generalization of rule 12, whose memory cap governs concurrent
invocations on ONE box. Lanes run in isolated per-session containers with their own RAM;
the ONLY dispatch constraint is SESSION COLLISION — two lanes writing the same surfaces
(a shared JSON, a shard, a branch) or duplicating the same work. Recorded against interest:
S-6 was held four refreshes on this misreading; Q14's "S-6 after the finisher" sequencing is
VOIDED with its premise (the CAISO-224-FIN prompt's exit line annotated). Rule 12 continues
to bind INSIDE a session (years sequential; ~2 concurrent invocations per box).

**2. FIVE LANES ISSUED THIS SITTING (everything runnable, per the owner's ask), collision-
mapped:** **S-6** (PJM T1-F ledger run — first pack prompt written; one run, no control pair,
decomposed vs the committed pjm-t1f ledger; S-4b floor-retention analogue pre-declared as a
direction) · **S-123-V** (the MISO §6 verification re-measure — fills the TBD, registers,
refreshes the MISO block; stops-at-start if the original session is still mid-run) ·
**NEISO-RC** (the D14 retirement-composition Phase-0 — zero-solve attribution, finding-only,
candidate drivers pre-declared, repairs routed not built) · **D16** (the S-123-routed
armed-interface mc=0 seam defect — DIRECTOR MECHANISM DECISION: FAIL CLOSED, a hard refusal
in the holdout_policy pattern; the gas×HR fallback-price alternative deliberately NOT built
without its own charter — a guard is not a mechanism, no field, no matrix row) · **D8**
(FC-7's two halves: the DOF-ledger instrument + the seven-leg run_config provenance debt;
ALL verdict/board re-emission EXPLICITLY DEFERRED — three in-flight lanes write those files
on other keys). Shared-file collision handling: golden/S-6/S-123-V each write DISTINCT
keys/blocks of ff-verdicts.json + program-status.json with rebase-care lines; NEISO-RC/D16/
D8 write neither. Still runnable from prior sittings: **D12-A** (Q15 execution) and
**CAISO-224-FIN** (Q14 — no longer gates anything).

**3. QUEUE STATE AFTER THIS BATCH:** D3 (MISO retirement G3) held ONE refresh — same MISO
board/verdict surfaces as S-123-V (real collision, not slot doctrine); D4-I3 (ERCOT I3
half) held ONE refresh — ERCOT surface contention with D12-A; D6 (FC-3 curve-ON over-fire)
next batch, likely zero-solve-diagnosis scope. NEISO-RC's repair phase and D8's re-emission
follow-up are next-batch decisions on their findings.

**4. BACKCAST/AUDIT MOVEMENT (watch only):** ercot-244 arc CLOSED (records + matrix-card
adjudication block, PRs #4411/#4412). miso-m2m-flowgates raw mirrors tracked (PR #4409,
data intake). **nyiso-161 backcast lane OPEN** (`claude/nyiso-161-backcast-calibration-9734io`)
— deconfliction noted in the new prompts. The T3 golden branch open, still mid-solve, no
new commits. Keepers/markers/freeze unchanged (spot-verified r#18, no marker-file commits
since).

**5. DISPATCH CONFIRMED (owner, post-r#19): S-123-V, NEISO-RC, D16 and D8 ARE IN FLIGHT**,
joining CAISO-224-FIN (dispatched earlier under Q14), D12-A and the T3 golden — seven
concurrent capx lanes, the largest set to date. S-6 was briefly OWNER-HELD post-release,
then **LAUNCHED by the owner the same sitting** — EIGHT concurrent capx lanes. Next
refresh: verify landings across all eight, in whatever order they arrive.

**6. CAISO-224-FIN LANDED AND VERIFIED (PR #4415, same sitting):** the finisher executed the
precommit's §5 adjudication exactly — **R for keeper purposes (F1 fires ×3 + F2 fires)**,
both bundles registered on the backcast dashboard from the committed slim artifacts
(`2026-08-30-caiso-224-{a0-control,b1-fsno}`), the CAISO matrix cell stamped R with the
falsification citation, and the keeper VERIFIED UNTOUCHED (caiso-220-c1-crosswalk). The
owner's "mid keeper promotion" recollection resolved exactly as the precommit bound it: no
promotion, honest R, partition representation retained with W-2/W-3 as the upgrade feeds.
Q14's arc is fully closed.

## 0o. Refresh #18 (2026-08-30, HEAD `d2cd019`) — D12-C CONCLUDED: CONTRADICTION, nothing armed, Q15 card presented; D5-R completion CORRECTS the director's r#17 fifth-bundle call; S-123 lands 3 terms (verification pending the slot); the golden is mid-solve

**1. D12-C CONCLUDED — the CONTRADICTION branch executed, mechanically and honorably (PR
#4406; `FINDING-capx-d12c-confirm-pair-2026-08-30.md`).** G-1/G-2 EXACT (control reproduces
the committed bracket to the cent — the whole margin machinery byte-stable; armed cache key
bit-equal to the ex-ante prediction `f061b2646bfaac8b`). V-1/V-3/V-4/V-5 PASS: no phantom
(2025 builds nothing on −$34.5k/−$20.9k, D12's reason exactly), terminal RM 15.84 inside the
ex-ante [15.0, 21.0] (walk bracket carried down by exactly the pre-named live-VRE feedback),
2023/24 cc as declared, gas bands improve (cc lands EXACTLY on the 6.000 GW charter anchor,
err 8.756 → 5.756; ct err 3.879 → 1.621), B-2 survives (−12.95/+0.74/+9.05), and the gas half
of the exhaustion rule is LIVE for the first time (2024 ct exhausts at 500 MW sub-cap).
**The single miss — V-2: entering-2022 gas_cc 0 vs the declared [750, 1,250]** — is
decomposed at full magnitude: NOT a construction defect (start margin bit-identical
+$45,930.9), NOT a phantom; the offline walk that produced the window fielded ONLY
gas+storage, while the live walk fields every candidate class, so solar wins the early
tranches and exhausts cc's margin first — **MORE exhaustion by the same mechanism on the same
one-object margin**. A pre-declaration derivation error (§1 named the artifact for V-4's band
and failed to carry it into V-2), discovered after the arm ran, so it stands: tolerance NOT
widened post hoc (rule 21), nothing armed, cells stay `O`, both bundles registered
(`…-t1h-d12c-{control,armed}`). **The owner re-decides — Q15 card presented this sitting.**

**2. D5-R COMPLETION PASS (PR #4403, the original issued branch) — and it CORRECTS THE
DIRECTOR'S r#17 CALL, recorded here against interest:** the fifth bundle
(`neiso-2023-2027-crossover-capxd14`) was rescored after all via `--rescore-co2-grain`:
co2 +12.8/+10.6/−2.3 → **+12.8/+11.1/−1.8 %** — my r#17 "~0.004 % bound, no follow-up owed"
adjudication had read the 2023 family row alone (0.001 TWh); 2024/25 carry 0.085/0.082 TWh
of unsplit COAL → **+0.49 pp each**, seam-only, banded statuses unchanged. Pre-repair
baseline preserved as `neiso-t1x-pre-d5r` (the handoff's predicted suffix). The lane ALSO
executed the §0n.3 deferred records item itself: **[D5-R 2026-08-30] annotations now stand
on all three board co2 cells AND `gate_reading`** — that records item is CLOSED. Exit record
`FINDING-capx-d5r-scorer-coal-grain-2026-08-30.md`. Lesson stamped: a bound asserted from
one year's row of a three-year artifact is not a bound.

**3. S-123 LANDED-PARTIAL (PRs #4397/#4398/#4402; `FINDING-capx-s123-miso-adequacy-2026-08-30.md`):
all three terms SHIPPED from single published operands** — S-1 PRM re-vintage 0.179→0.157
(PY 2025-26 LOLE Module E-1 pair, −2,637.4 MW exactly the charter's number), S-2 external-ZRC
+3,505.9 MW (PRA posting p.22), S-3a LMR/DR fraction 0.0665940 (−9,236.8 MW) — 2026 position
−6,037.0 → +9,343.2 MW pre-solve, a 2.5× overshoot (the NYISO-intake honesty signature, not a
tuned closure). **§6 verification (the solo MISO 9.6 GB T1-F re-measure + FC-1 re-score) is
TBD — holding for the heavy slot.** D9 adjudicated UNREACHABLE at HEAD and routed (TVA
re-point + data prerequisite). **NEW DEFECT ROUTED TO THE DIRECTOR** (finding §5/§7 item 5):
armed-interface forecast years leave seam rows at their **mc=0 build placeholder** — queued
as a mechanism-decision candidate (D16) below.

**4. T3-NEISO-GOLDEN MID-SOLVE:** PREDECL §§1–4 merged (PR #4405 — Q13 cited verbatim, gate
legs re-verified live, budget declared) + registration-prep (PR #4408: t3-golden
classification + campaign gitignore block, S-4b slim-vs-heavy pattern). Branch open with no
further commits — the 25-year solve is running. Stamp on landing.

**5. CAISO-224-FIN NOT LANDED** (zero caiso-224 registrations; PR #4401 patched the
registry/payload parity CI gate to tolerate the two interim unregistered bundles — an
interim-state accommodation, not the finisher). **S-6 stays RELEASED-CONDITIONAL.**
**HEAVY-SLOT QUEUE (explicit, for dispatch):** golden (running, ~4.3 GB) → S-123's §6
verification (9.6 GB no-co-run) → S-6 (8.8 GB no-co-run; ALSO gated on CAISO-224-FIN
landing). The two no-co-run measures must not overlap each other either.

**6. BACKCAST/AUDIT (watch only):** ercot-244 opened AND **KILLED AT CENSUS** in one arc
(PRs #4404/#4407 — rtolhsl online-capability ceiling; precommit-first discipline again;
branch deleted). Keepers ×6, `complete`={NEISO, PJM}, `final` EMPTY, freeze tier-scoped:
ALL verified unchanged at `d2cd019`.

**7. THE r#18 SITTING — Q15 RULED: ARM BOTH FIELDS (§3).** The owner judged the D12-C record
confirming-in-substance under the finding's own §4.3 clause and directed the arming. Lane
**D12-A** issued (pack-canonical): zero-solve execution of exactly the §1.4 confirmation list
— ISOConfig `default_scenario_overrides` route (FFR-9C stage-B pattern), Q10+Q15 cited
verbatim with the V-2 miss described honestly, ERCOT matrix cells O → K-forecast-armed on
the registered pair, sister cells U, no re-registration (both bundles already registered).
Cross-track note carried into the prompt: the arming moves ERCOT forecast defaults under the
audit track's T1-H capacity-entry lane — their registered-posture controls are unaffected,
but any FUTURE bare invocation lands on the armed defaults; ERCOT matrix-shard rebase care.

## 0n. Refresh #17 (2026-08-30, HEAD `83c1c5a` → `a305f46` mid-refresh) — D5-R and S-4b BOTH LANDED-VERIFIED; NEISO leg (b) STRENGTHENS on the ARA-3 bar; leg-(d) card DUE THIS SITTING; D12-C mid-execution (PREDECL in)

**1. D5-R LANDED AND VERIFIED (PR #4388, branch `claude/crossover-co2-grain-repair-oycsy6`
— the lane picked its own branch name; same charter). Controls checked BEFORE the headline,
per the standing duty — ALL PASS:** NYISO co2 byte-identical ×3 (structural no-op); the
grain-reconciled `family_volume` gas_twh/coal_twh rows and flat rubric rows deep-equal every
ISO-year; C1 records, price_mean, price_shape, retirements, additions, capacity-track co2 all
deep-equal. Every re-scored cell landed within ±0.2 pp of D5 §5.2's pre-declared table
(tolerance was ±0.5). **Verdict outcomes exactly as pre-declared:** PJM co2 LEAVES the FC-4
FAIL set (2023/25 clear, 2024 CAVEAT 10.3 %); MISO co2 LEAVES it (2023/24 clear, 2025 CAVEAT
13.4 %); ERCOT 2023/24 STAY FAIL on the honest volume gap (−25.2/−23.2 %), 2025 PASS (+1.3 %);
NYISO untouched. No FC-4 category status flips (surviving price/volume rows still gate); no
§2.1b leg moves (leg (c) is measurement-keyed per Q7). Ancillary honesty fix shipped: the
`register_hindcast --preserve-invariants` fall-through that fabricated 13 vacuous PASS
invariant rows over an absent cache now reuses-or-omits, never recomputes.
`docs/handoffs/RESULT-crossover-co2-grain-repair-2026-08-30.md`.

**2. THE FIFTH BUNDLE, ADJUDICATED (the r#16 handoff's open question — the prompt named five
keys, the lane rescored four).** The committed NEISO bundle
(`neiso-2023-2027-crossover-capxd14`) was NOT put through `--rescore-co2-grain`; its verdict
re-emitted provenance-stamps-only via the standard 9-verdict path. Director verified the bound
directly from the committed score artifact: NEISO's model carries **0.001 TWh** of generic
`COAL` (`family_volume.coal_twh.model_twh`, `model_only_classes=["COAL"]`) → the grain drop
bounds at ~0.001 Mt on 25.4 Mt ≈ **0.004 % of co2 — below representable precision and far
inside the pre-declared ≲0.4 % ceiling**. The skip is materially sound; D14's measured
+12.8/+10.6/−2.3 % stand as the honest values. No follow-up owed.

**3. NEW NAMED RECORDS ITEM — board co2 annotation (deferred, deliberately).** The board's
ERCOT/PJM/MISO leg-(c)/T1-X cells and `gate_reading` quote co2 magnitudes (49.2/42.7/50.6 ·
45.1/40.4/54.2 · 63.3/58.9/75.5 %) from the LIVE gate keys — faithfully: those FFR-3A-3/-3A-4
bundles were never committed, so no zero-solve re-measure exists for them (RESULT §4) and the
rows stay as scored. But D5 established those magnitudes are **46–117 % scoring-instrument
error**, and the board says so nowhere — the program's classic stale-quote defect waiting to
happen. The fix is a [D5-R 2026-08-30]-style annotation on three cells + `gate_reading`
(pattern: the existing [CORRECTED 2026-08-24] notes), cross-referencing the repaired committed
ffr2a/capxd10 rows. **DEFERRED to the next records act** rather than chartered now: D12-C,
S-4b and S-123 are all in flight and may edit adjacent board blocks — a records lane touching
`program-status.json` mid-wave invites the same merge contention D13 was sequenced to avoid.
Leg-(c) statuses are unaffected either way (Q7: measured closes the leg, whatever it says).

**4. D12-C CONTROL REPRODUCIBILITY RE-VERIFIED AT THE NEW HEAD (cross-track threat checked in
code, not assumed).** The audit track's T1-H Phase-1 Leg A landed since D12-C's bracket was
committed (PRs #4386/#4389: `storage_entry_availability_gate` + `storage_entry_cost_normalized_rank`,
gated default-off, matrix rows registered; A/B driver probe). Both new fields ride
`run_capacity_hindcast.py`'s None-drop dict — "OMIT inherits the shipped defaults so the
control arm's cache key is untouched" — so D12-C's bare control still reproduces the committed
`28cef3500ec1fd9e` bracket. No prompt amendment needed. **Dedup boundary VERIFIED CLEAN:**
their commits touch `model/storage.py`, config, harness wiring and their own probe — no
entry-allocator surface, no `entry_margin_exhaustion`/`entry_forward_reserve_leg`. The ERCOT
matrix-shard rebase-care watch item stands.

**5. S-4b LANDED MID-REFRESH (PRs #4392/#4396, `claude/capx-s4b-neiso-ara-3jhedd`) — VERIFIED,
AND THE PRE-DECLARED FLIP-BACK DID NOT MATERIALIZE.** `FINDING-capx-s4b-neiso-ara-2026-08-30.md`:
- **The companion was LOCATED** (2026 CELT 4.1 CSO summary, column labelled "Includes ARA 3
  Results") — the "ship nothing" clause did not fire. Intake = FOUR values, zero free
  parameters, sha256-pinned sources: requirement factor 1.0024544 → **1.0286103**, DR fraction
  0.09701 → 0.08784, firm-import credit 567.0 → **409.31 MW** (same-cycle pairing rule; ARA-2
  2027/28 values on the record, not adopted).
- **The move is LARGER than charter-declared** (+651…686 MW/yr of requirement + −157.7 MW of
  import credit, vs the ≈+380 MW estimate), in the honest direction. The §4 arithmetic
  re-opened 2028 (−280.4) AND 2029 (−365.7) — yet **measured I7 holds PASS ×5**
  (+3,374.8/+810.2/+419.0/+333.6/+1,197.5 MW): the reliability floor (same requirement, second
  verb) answers the higher requirement by RETAINING **699.3 MW of 2027 gas-CC exits** (8
  tranches named; the exact mirror of S-4V's 324.9 MW loosening). Decomposition closes ≤0.1 MW
  every year; the control reproduces the S-4V ledger BIT-FOR-BIT (zero epoch drift — first
  NEISO lane with no drift disclosure needed); 2026 base-year isolation EXACT (−808.6 = −651.0
  − 157.7, endogenous response 0.0). Backstop did NOT fire (0 MW, builds identical both arms).
- **Bare `neiso-t1f` → PROMOTE-WITH-CAVEATS with STRICTLY FEWER caveats: FC-1 PASS (14/14 —
  the lone I12-2026 WARN cleared mechanically on the re-derived band), FC-2 PASS, FC-7 CAVEAT
  (program-wide DOF ledger), FC-8 PASS. Leg (b) does NOT flip back — it STRENGTHENS.**
  Preserve-then-overwrite honored: S-4V vintage kept at `neiso-t1f-s4hydro`, control at
  `neiso-t1f-s4bcontrol`; board NEISO block refreshed with D14's leg-(c) content verbatim.
- **Honesty notes carried at full magnitude (quote them with the clearances):** the 2028/2029
  I7 margins are FLOOR-DEPENDENT (+419.0/+333.6 riding on the 699.3 MW retention; without it,
  −280/−366), and each successive measurement has moved them DOWN (+545→+419, +469→+334). The
  floor is a standing structural mechanism (spec §5.2) measured against a zero-drift control —
  not a tuned input; nothing was re-tuned, the 0.7352 hydro factor untouched.
- **CONSEQUENCE: the Q11 hold is RESOLVED — the leg-(d) decision card is DUE and PRESENTED at
  THIS sitting** (§3 Q13). NEISO's legs: (a) pass · (b) pass, strengthened · (c) pass ·
  (d) none. Campaign cost (FF-3E): ~1.0 h full-horizon, ~4.3 GB — the cheapest in the program.

**6. D12-C IS MID-EXECUTION (not concluded):** its PREDECL commit landed (PR #4394,
`bf5e08f`) — verdict criteria V-1…V-5 with ex-ante tolerances ($0.05/MW-yr margin
reproduction; every tested margin ≥$5.7k from zero) committed BEFORE either invocation
launched, and the A/B probe extended with `--expect-delta` hard-gating the two-field arm as
the single logical delta. The confirm-vs-contradict record is still to come — the Q10
auto-arm-on-confirmation stands. **S-123: no branch, no landing.** The one deconfliction
delta for in-flight prompts: audit-track branch `claude/ercot-243-release-exit-r7owkv` open
(0 unique commits), covered by start-time `ls-remote` checks.

**7. S-6 / HEAVY SLOT:** caiso-224's **B1-arm solves are COMPLETE and committed** (PR #4395:
full `caiso224_b1_fsno` bundle slim files — 2023/24/25 system parquets, legitimacy
diagnostics, meta, run_config — plus the split-witness/F1-F2 artifact), but the lane is
UNCONCLUDED (no registration, no finding; further arms possible). No heavy solve is
*verifiably* in flight → S-6's release put to the owner at this sitting (they know whether
the caiso-224 session is still running) rather than guessed. Held pending that answer.

**8. BACKCAST/AUDIT MOVEMENT (watch only):** PJM stage-0 golden captured (`29a9cba`,
audit-track owner card 1 — pjm-162-inputclock 2023–2025, 256 flags/713 config keys, 0
drifted). **nyiso-160 CONCLUDED its records** (PR #4393): Leg-2 stop annotations finalized,
touchpoint-prep audit replay registered (keeper bit-identical at HEAD) — NYISO marker
re-entry remains an open backcast-track question. Keepers, markers (`complete`={NEISO, PJM}),
`final` EMPTY, tier-scoped freeze: all verified UNCHANGED at `a305f46`.

**9. THE r#17 SITTING — TWO RULINGS (§3 Q13/Q14):**
- **Q13 — NEISO leg (d) AUTHORIZED: the T3 BAU golden, 2026–2050, ~1.0 h / ~4.3 GB, this
  campaign only.** The FIRST §2.1b gate opening in program history, granted on S-4b's measured
  result exactly as Q11 sequenced it. Lane **T3-NEISO-GOLDEN** issued (pack-canonical):
  zero config invention (HEAD defaults + `--golden-posture --full-solve-authorized`), forecast
  namespace registration (`neiso-2026-2050-t3-golden-bau`), board leg-(d)/gate stamp citing
  the ruling, caveats carried verbatim, failure-record-is-the-deliverable clause.
- **Q14 — caiso-224 ran out mid-completion; the owner directed the director to draft the
  finisher (RECORDED BOUNDARY EXCEPTION: backcast-track completion work, chartered on
  explicit owner request — not a standing widening of the director's charter).** Lane
  **CAISO-224-FIN** issued (pack-canonical): ZERO-SOLVE — all solve artifacts committed;
  executes `PRECOMMIT-caiso224-fsno-arm-2026-08-30.md` §5/§6 faithfully. Director verified
  the committed record before drafting: **F1 fires all three years** (NP15↔FSNO binding
  0.3054/0.3547/0.3380 vs the 0.27 DMM ceiling) **and F2 fires** (arm split vector
  [1556,1359,1186] strictly year-ordered vs reality's non-monotone [1310,1691,1347]) ⇒ per
  the precommit's own rule the static DMM-cap arm reads **R for keeper purposes** — the
  owner's "mid keeper promotion" recollection does not match the pre-registered record, and
  the prompt binds the finisher to the precommit, never the recollection (a K reading stops
  for an owner card; the keeper is untouched either way). The honest headline both ways: the
  split RESTORATION is real (52/40/17 → 1556/1359/1186 vs reality 1310/1691/1347) AND both
  falsifiers fire. **S-6 → RELEASED-CONDITIONAL on CAISO-224-FIN landing** (its own prompt
  stays pack-canonical, unchanged).

## 0m. Refresh #16 (2026-08-30, HEAD `b5050e9`) — pre-launch check: the r#15 wave (D12-C · D5-R · S-4b · S-123) is CURRENT VERBATIM; backcast-only movement

**1. WAVE VERIFIED CURRENT.** No capx branch exists at `b5050e9`; the forecast surfaces
(`program-status.json`, `ff-verdicts.json`) are untouched since D14's board edit (`a65d4e5`).
All four prompts launch as written. Minor staleness, harmless by construction (each prompt
checks `git ls-remote` at start): D12-C's deconfliction line lists ercot-242 as in flight — it
has since CONCLUDED. S-6 STAYS HELD: caiso-224 is still actively solving (B1-arm 2023 sidecar
checkpoint landed this window).

**2. BACKCAST MOVEMENT (watch only, nothing touches this track's gates):**
- **NYISO keeper PROMOTED → `2026-08-30-nyiso-159-loss-surface`** (owner ruling; the measured
  zonal loss-surface A/B registered `nyiso-159-loss-{control,surface}`; fail set NARROWS;
  status part rebuilt after the frontier-withdrawal merge). Marker stays withdrawn — re-entry
  still requires a CALIBRATED keeper (Q5-W).
- **nyiso-160: winter-intake Leg 2 STOPPED WITH CAUSE — the AORR files are unproducible**;
  touchpoint-prep audit method recorded. WATCH: Leg 2 was the designated route back to
  CALIBRATED and marker re-entry for NYISO; with it stopped, the re-entry route is open
  question territory for the BACKCAST track (not this track's to charter), and the NEISO-led
  gate board is unaffected.
- **ercot-242 CONCLUDED** (room-axis Phase-1 armed probe REJECTED-AS-ARMED on its own gates,
  registered + escalated, matrix cell R; branch deleted). **ercot-243 opened and STOPPED at
  Phase-0 census** (population = h3068-2024 alone; K-1/K-3 kills fire — precommit discipline
  again). **o7 CLOSED** (HP-1 holds; the pricing channel ≈ zero; audit row closed).
  **miso-191** (miso-190's binning-aware successor) landed its PREREG + delivery commits and
  its branch is deleted — no MISO backcast branch in flight, S-123's check still passes.
- In flight at `b5050e9`: `caiso-backcast-next-run` (caiso-224) ONLY.

## 0l. Refresh #15 (2026-08-30, HEAD `a6e68e2`) — the ENTIRE four-lane wave LANDED (D13 · D14 · D12 · D5); NEISO is the first (a)+(b)+(c) ISO; three rulings (Q10/Q11/Q12); D12-C + D5-R chartered; S-4b + S-123 RELEASED

**1. WAVE OUTCOME — four dispatched, four landed, second consecutive 100 % cycle:**
- **D13 LANDED** (PR #4372): Q7 executed (ERCOT/PJM/MISO leg (c) fail → pass-on-measurement),
  S-5's PJM restatement applied (366 MW → 5,858 MW), D11-R/Q8 stamped, stale headline/gate_reading
  repaired, rule-27 blob verification recorded in the finding.
- **D14 LANDED** (PR #4376; `FINDING-capx-d14-neiso-t1x-2026-08-30.md`): NEISO's first-ever
  T1-X registered (`neiso-t1x`, FC-4 FAIL measured at full magnitude, quarantine PASS) —
  **NEISO IS THE FIRST ISO IN PROGRAM HISTORY WITH (a)+(b)+(c) ALL SATISFIED; only leg (d)
  remains.** Substantive findings: (i) NEISO is the SECOND no/low-coal counter-example
  (co2 +12.8/+10.6/−2.3 %), confirming D5's mechanism; (ii) **first crossover leg whose window
  executes economic exits** — and it shows a retirement COMPOSITION miss (gas_cc over-retired
  3.128 vs 1.884 GW actual; biomass/coal/gas_ct/oil exits missed entirely, recall 2/6);
  (iii) price miss concentrated in 2025 (−21.8 %), the same sign-flip year as NYISO.
- **D12 LANDED** (PR #4373; `FINDING-capx-d12-scarcity-basis-2026-08-30.md` + PREDECL): the
  adjudication is DECISIVE with zero solves — the shipped realized-prior-year reserve leg is a
  **cross-year phantom** (entering-2024: both gas margins NEGATIVE under the entering year's own
  expectation — gas_cc −$10.7k, gas_ct −$42.7k/MW-yr — yet 6 GW built on the phantom;
  entering-2025 repeats it at −$118.6k/−$111.4k with the realized annuity ≥ 4× the forward
  leg's maximum). Everywhere else the consistent basis changes NOTHING that was right
  (bang-bang ledger RM path unchanged; scored gas bands improve, CT |err| 3.879 → 0.879); under
  it the exhaustion rule's gas half goes live via the exact identity `r_walk = adder_current`.
  Shipped `entry_forward_reserve_leg` default-OFF, byte-identical off. Recommended arming BOTH
  fields together (§7 card).
- **D5 LANDED** (PR #4374; `FINDING-capx-d5-crossover-co2-2026-08-30.md`): the three-ISO
  crossover CO2 miss is a **SCORING-TAXONOMY DROP, not a model defect** —
  `score_crossover.py::model_co2_mt_fullplant` iterates bench intensity keys (coal-rank grain)
  so the model's generic-`COAL` generation contributes ZERO to scored CO2. Explains MISO
  97–117 % of the miss, PJM 75–98 %, ERCOT 46–103 %; NYISO control exactly zero; NEISO (D14)
  the confirming second control. **The forecast emission-rate derivation is EXONERATED**
  (own-rates within ±5 % of same-year bench intensities, every ISO-year). Third instance of the
  known class-grain seam (the other two already patched). Repair + pre-declared re-score table
  in §5.
- **miso-190 CONCLUDED** (PR #4370): the partial-plant exit-carry arm was **REJECTED on its own
  pre-filed S-1 kill**, both A/B legs registered, matrix cell U → R, keeper unchanged
  (miso-188-rvsscope), branch deleted. The PREREG discipline holding again.

**2. THREE OWNER RULINGS AT THE r#15 SITTING (decision cards — §3 Q10/Q11/Q12):**
- **Q10 (the Q8 re-decision) — CONFIRM-PAIR, THEN ARM.** Lane **D12-C** chartered: ONE
  arm-vs-control A/B on the ERCOT T1-H leg at the registered posture with the TWO fields
  (`entry_margin_exhaustion` + `entry_forward_reserve_leg`) as the single logical delta,
  measuring the closed loop D12 open-loop-predicted. **Arming auto-executes on a confirming
  record** (both flip to ERCOT forecast defaults, honestly described); a contradiction does NOT
  arm and comes back to the owner at full magnitude.
- **Q11 (NEISO leg (d)) — HOLD FOR S-4b FIRST.** S-4b dispatches now; the leg-(d)
  authorization card is RE-PRESENTED on its measured result. Rationale adopted: authorizing a
  campaign against a requirement bar a published filing already supersedes spends the compute
  on a known-stale bar; D14's retirement-composition finding is additional context.
- **Q12 — D5-R CHARTERED, FULL FIX** (D5's preference (a)): map coal to its supply class at
  gmModel-build time via the canonical taxonomy chain (one chain, rule 19), repairing the C1
  fuelmix coal rows (~60 TWh/ISO-yr phantom) in the same stroke; zero-solve re-score of the
  committed crossover bundles with D5 §5.2's pre-declared table as the honesty gate (NYISO
  exact no-op, NEISO ≲0.4 %, MISO coal_twh / PJM gas_twh rows untouched — any control movement
  stops the lane).

**3. RELEASES: S-4b RELEASED** (D14 merged — its gate) and **S-123 RELEASED** (the start-time
check PASSES at last: miso-190 concluded and its branch is deleted — after six consecutive
fails; D9 rides with it). **S-6 STAYS HELD**: caiso-224 is actively solving (hourly sidecar
checkpoints on its open branch) and ercot-242 is in flight — the PJM 8.8 GB no-co-run slot is
not free. Re-check next refresh.

**4. CROSS-TRACK: the audit-program director chartered the T1-H CAPACITY-ENTRY repair lane
(owner card 2 of its own sitting), and the deconfliction is CLEAN BY CONSTRUCTION** — its
precommit's step-0 DEDUP GATE cedes defect D-1 (the bang-bang allocator) to this track's
D11-R/D12 lanes explicitly, scoping itself to the storage leg (D-2+D-3) and wind leg (D-8/B-3).
Watch item: D12-C's arming (if confirmed) moves ERCOT forecast defaults under that lane —
its Phase-1 runs at its own registered-posture controls, so no collision, but both lanes touch
the ERCOT matrix shard (rebase care). Also executed at that sitting: **NYISO's frontier
declaration REVERTED (frontier = {PJM, NEISO})** with a machine-readable
`frontier.withdrawn` mirror in the keeper shard (keeper-auditor pass), and a cross-lane
re-grade rule. Backcast: ercot-242 opened (SCED room-axis extension of the armed RT wall,
`rt_room_path` gated field, precommit-first; branch in flight); caiso-224 A0 control complete
(G-CTRL bit-zero vs the caiso-220 keeper sidecars) with the FSNO variant seam landing; o7
delta-equality control scoped. — r#13 batch verified CURRENT (none dispatched yet); D5 issued as the wave's addition; backcast-only movement

**0. DISPATCH CONFIRMED (owner, 2026-08-30, post-r#14): D13, D14, D12 AND D5 ARE ALL IN
FLIGHT** — the full four-lane wave launched at once (largest concurrent capx set to date; all
light/zero-solve, no shared heavy slot; the one surface overlap, D13/D14 on the NEISO board
block, is handled by D14's rebase instruction). S-4b remains staged strictly behind D14's
merge; S-123 and S-6 stay held on Q9 (miso-190). Next refresh: check all four for landings,
merge-behind gaps, and cross-lane merge conflicts on program-status.json / ff-verdicts.json.

**1. THE r#13 BATCH IS CURRENT VERBATIM.** No capx branch exists at `1421c4a` (D13/D14/D12
undispatched; S-4b staged behind D14) and the surfaces they edit are untouched since r#13:
`program-status.json` and `ff-verdicts.json` last moved at D10's merge (`158a688`), so D13's
edit list is exact, D14 displaces nothing, and D12's evidence set is unchanged. The director
r#13 commit merged cleanly (PR #4362, no merge-behind gap).

**2. D5 ISSUED — the three-ISO crossover CO2 derivation question, now fully evidenced.**
D10's NYISO measurement (co2 10.1/10.3/3.9 %) completed the scope D2-B's re-scope predicted:
the 43–76 % miss is ERCOT/PJM/MISO's, and the discriminant hypothesis (what the three share
and NYISO lacks — a material coal fleet; the coal_twh crossover rows FAIL in ERCOT and PJM) is
PRE-DECLARED in the charter as a hypothesis to test, not assume. Zero-solve attribution lane
on the committed crossover bundles; no board edit (D13's or a later refresh's job); no tuning.

**3. BACKCAST MOVEMENT (all of it — no forecast-surface touches):** ercot-239 r2/r3: the
graded-ladder arm was A/B-REJECTED on its own kills (officials collapse to pre-k33; spur
74→11), escalated, and the owner sitting adjudicated promotion NOT RECOMMENDED — keeper
unchanged; h3068-2024 attributed (event-exit lag). ercot-241 phase-0 measured the off-core
conduct screen — kills clear, Phase-1 gate OPEN. caiso-224 minted `caiso_fsno_subzonal_topology`
(gated default-off, matrix row by its own lane) + G-CTRL comparator probe; branch in flight.
nyiso-159 landed `nyiso_zonal_loss_surface` (measured delivery-factor surface, PREREG-first).
Audit-records v15 cycle executed (four rulings, zero promotions).

**4. Q9 CHECK RE-RUN: miso-190 head unchanged (`9cd6dc6`), A/B still unregistered — STILL
RUNNING. S-123 fails a SIXTH consecutive check; S-6 stays held.** Housekeeping: the
`capx-s4-neiso-hydro-syqu7m` branch is a fully-merged stale leftover — safe for the owner to
delete. In-flight backcast branches: caiso-224, ercot-241, miso-190 (D12's start-time
deconfliction covers the ERCOT one).

## 0j. Refresh #13 (2026-08-30, HEAD `f9eb73c`) — ALL FIVE in-flight lanes LANDED (D10 · S-4V · S-5 · Q5-W · D11-R); NEISO takes the program lead with (a)+(b) both PASS; three owner rulings; D12/D13/D14 issued

**1. THE ENTIRE IN-FLIGHT SET CLEARED IN ONE MERGE WINDOW — five lanes, zero refusals, every
deliverable where its charter said it would be.**

- **Q5-W LANDED** (PR #4343, `ecc2d60`; `docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md`):
  NYISO's `complete` marker WITHDRAWN on the r#12 ruling, both surfaces in one session —
  `complete` = **{NEISO, PJM}**, board NYISO gate (a) PASS → fail. Keeper nyiso-157 untouched;
  validation-tier authorization lapsed with the marker; re-entry = new owner declaration on a
  CALIBRATED keeper (winter-intake route).
- **S-4V LANDED** (PRs #4337/#4353): the verification pair ran at one HEAD and **the bare
  `neiso-t1f` key flips HOLD → PROMOTE-WITH-CAVEATS** (treatment: I7 PASS all five years, sole
  WARN the pre-declared I12-2026 17.1 % vs 15.2 % cap; FC-1/FC-2/FC-7 all CAVEAT-not-FAIL).
  **Honest attribution recorded on the record: the CONTROL arm ALSO clears 2028 — epoch drift
  alone flips the year — so the flip is NOT solely S-4's factor; the factor's isolated effect is
  exact** (control preserved as `neiso-t1f-s4control`). Board NEISO block refreshed and the
  `hydro_accreditation` matrix cell re-stamped O → K by the lane itself. S-4's finding §5/§8
  TBDs filled. **S-4b UNBLOCKS.**
- **S-5 LANDED** (PR #4340; `docs/handoffs/FINDING-capx-s5-pjm-horizon-edge-2026-08-30.md`):
  hold-last-FPR implemented as the declared convention in `resolve_forecast_pool_requirement`
  (card C-A cited in code; zero DOF — the held value is the table's own last published entry),
  D-1 checker year-threading repaired (I7/I12 now grade the same bar the model builds to), and
  **PJM's 2030 I7 miss restates 366 MW → 5,858 MW (3.39 % of peak), 2029 plausibly joining**
  (flagged inference; S-6 measures it). No solve, no registration — the FINDING is the
  director's D7-class input, so **the board's PJM block restatement is OWED → carried by D13**.
  Rule-23 check done on publication terms: 2029/30 BRA is Dec 2026; intake pointer at the table
  edge. **S-6 UNBLOCKS** (held on the heavy slot, §0j.3).
- **D10 LANDED** (PR #4354; `docs/handoffs/FINDING-capx-d10-nyiso-t1x-2026-08-30.md`): NYISO's
  FIRST-EVER T1-X (`nyiso-2023-2027-crossover-capxd10`, ~10 min, <3 GB, shipped posture verified
  in the resolved config), **FC-4 measured and reported at FULL MAGNITUDE: FAIL** — price 2023
  +29.9 % / 2024 +2.5 % / 2025 −24.0 %; **co2 10.1 / 10.3 / 3.9 % — NYISO does NOT reproduce
  the program-wide 43–76 % crossover co2 miss** (D5 evidence: the derivation question is
  ERCOT/PJM/MISO's, not universal). Quarantine PASS (no H1-2026 read). Registered `nyiso-t1x`
  with run_config.json (no D8 debt). **Leg (c) closes on measurement: NYISO gate now
  (a) fail · (b) PASS · (c) PASS · (d) none.**
- **D11-R LANDED** (PR #4355; `docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md`):
  `entry_margin_exhaustion` shipped default-OFF (one field, both allocators, rule 19; matrix row
  + all-shard cells), zero-DOF confirmed (the walk re-invokes `runner._lookahead_reprice_signal`
  itself, delta-anchored; byte-identical off). A/B on ERCOT T1-H at the registered posture,
  control reproduces the committed bracket EXACTLY (RM 19.00→8.54→14.65→25.19, additions
  verbatim). **Four-anchor terminal RM: shipped 25.19 / disarm 40.24 / fwd-exp 40.38 / offline
  18.7 / LIVE ARM 22.02 % (−3.17 pp). B-2 cobweb SURVIVES** (−12.65/+5.20/+10.47 vs
  −10.46/+6.11/+10.54) — the implementation-sanity test passed. Named degradation vs offline:
  **the live reserve leg keeps the GAS half inert** (gas builds to caps in both arms; the
  prior-year realized ORDC leg carries the margin past exhaustion), so arming now = honest
  split "margin-exhaustion for VRE/storage, bang-bang for gas". Both arms registered
  `ercot-2021-2025-realized-t1h-d11r-{control,exhaustion}` with run_config.json; ERCOT matrix
  cell **O** (measured, owner escalation). Finding §5 recommends HOLD arming until D12. **D12
  RELEASES** (the r#8 ratified sequencing is satisfied — D11-R has reported).

**2. THE PROGRAM LEAD PASSES TO NEISO — the second ISO ever to hold (a)+(b), and the first to
hold them simultaneously with a live marker.** NEISO: (a) PASS (`complete` member, CALIBRATED
full-span keeper neiso-99-joint-p1) · (b) PASS (PROMOTE-WITH-CAVEATS on bare `neiso-t1f`) ·
(c) fail — the ONLY genuinely-unrun T1-X among the measured reading's fail set · (d) none.
**A NEISO T1-X (D14, issued this refresh) would make NEISO the first ISO in program history
with (a)+(b)+(c) all satisfied, leaving only leg (d) — the explicit owner authorization.**
NYISO holds (b)+(c) but fails (a) on the withdrawn marker.

**3. THREE OWNER RULINGS AT THE r#13 SITTING (decision cards, this session — §3 Q7/Q8/Q9):**
- **Q7 — leg-(c) semantics: MEASURED CLOSES THE LEG** (charter-literal §2.1b(c) + card A-A as
  signed). ERCOT/PJM/MISO leg (c) flips fail → pass-on-measurement (their FC-4 FAILs stay
  reported at full magnitude); NYISO's D10 PASS stands. The D7-era in-band reading is
  superseded; D10's cell claim about the other ISOs becomes true once D13 executes. Discovered
  and escalated this refresh: the board carried BOTH readings simultaneously (D7 wrote the
  measured ISOs fail-on-band; D10 wrote NYISO pass-on-measurement citing the others as pass —
  false at the time of writing).
- **Q8 — D11-R arming: HOLD until D12 adjudicates the scarcity basis** (the finding's own §5
  recommendation). Matrix cell stays O; the A/B is the standing measured record; re-decide on
  D12's report.
- **Q9 — miso-190: STILL RUNNING** (branch fully merged at `9cd6dc6` but the A/B solve is not
  yet registered — scorer committed before it runs). **S-123 start-time check FAILS a FIFTH
  time; S-6 held on the same heavy slot** (PJM 8.8 GB / MISO 9.6 GB are no-co-run). Both re-run
  next refresh.
- Also verified this sitting: the top-level board prose (headline/gate_reading) is STALE against
  its own NEISO/NYISO blocks — still says "no ISO holds (a) and (b) both" and "leg (c) fails
  for all six". D13 carries the reconcile.

**4. BATCH ISSUED (r#13): D13 BOARD RECONCILE (records; executes Q7 + the S-5 PJM restatement
+ D11-R/S-4V/D10 currency + the stale-prose repair), D14 NEISO T1-X CROSSOVER (the D10 analog;
the program's highest-value light lane), D12 SCARCITY-CONSISTENT DELTA BASIS (released by
D11-R's report; its result is the arming re-decision's input).** S-4b's prompt is written and
in the pack, **dispatch strictly after D14 merges** (both edit ff-verdicts.json + the NEISO
board block; S-4b's pre-declared arithmetic: +380 MW requirement vs the +229 MW post-hydro
clearance ⇒ 2028 plausibly RE-OPENS ≈ −151 MW and leg (b) may flip back — reported at full
magnitude if so, factor and requirement both sourced, nothing reverse-engineered). S-6 and
S-123 held on Q9. D5 stays queued, now carrying D10's evidence (NYISO co2 ~10 % ⇒ three-ISO
derivation question confirmed as the right scope).

## 0i. Refresh #12 (2026-08-30, HEAD `65a39e3`) — NYISO keeper → nyiso-157 (NOT-YET, fail set WIDENED); Q5's recurrence clause FIRED and the owner ruled WITHDRAW; FF-2D re-score benign

**1. NYISO'S KEEPER MOVED UNDER THE MARKER AGAIN — the Q5 fact pattern RECURRED.** nyiso-157
PROMOTED the eastern-seam PAR attribution to keeper (`2dc64b5`, PR #4323; keeper-auditor pass
PR #4326): keeper → **`2026-08-30-nyiso-157-par-attribution`**, promotion basis rules 14+1
(all four border-link caps now follow NYISO's measured P-32 schedules under the published PAR
attribution, zero free parameters; first real zonal price separation — CE utilisation
0.381 → 0.784 in 2025, Jan+Feb-2025 cutset binding 34 → 435 h), EXPLICITLY over TWO gate
regressions reported at full magnitude: C3a-2025 −10.8 → −12.0 % and C3b-2025 joining at a
knife-edge 0.203 vs the 0.20 bar (zero-delta control 0.197). Determination **NOT-YET on
{C3a, C3b, C3c}** — the fail set WIDENED — re-verified per D-5(b) without a solve, the stop
resolved by the owner's in-session standing formula (third application: nyiso-120/155/157).
The marker's own record names the deepened 2025 miss "the winter face of the nyiso-156
two-face object measured on an honest seam"; successor = intake Leg 2.

**2. THE OWNER RULED THE RECURRENCE AT THIS REFRESH'S DECISION CARD: WITHDRAW THE MARKER
(CAISO precedent), against the director's recommendation to adopt the standing formula —
recorded plainly.** The written reconciliation is now UNIFORM: **a `complete` marker cannot
stand on a NOT-YET keeper** (the 2026-08-06 CAISO precedent governs); the
structural-integrity formula remains the standard for KEEPER promotions (nyiso-155/157 stand
untouched as keepers) but no longer sustains a marker. Consequences: `complete` → {NEISO,
PJM} once executed; NYISO gate (a) flips to fail on the marker (leg (b) PROMOTE-WITH-CAVEATS
is untouched — no marker moves a bare verdict); NYISO's validation-tier (2020–2022)
touchpoint authorization lapses with the marker; re-entry is a NEW explicit owner
declaration, expected on the winter-intake route once the keeper again scores CALIBRATED.
**Execution chartered as Q5-W** (governance records lane, NOT a capx lane — it edits
calibration-complete.json + the board's NYISO gate (a), both surfaces in one session so they
cannot disagree; prompt canonical in the pack). Q5 CLOSES on this ruling — the recurrence
clause is discharged by uniformity, not by waiting. **The program's gate-board lead may pass
to NEISO on S-4V's measurement** (NEISO would be the only ISO with (a)+(b) both in reach).

**3. FF-2D RE-SCORE — MY NAMESPACE WAS TOUCHED BY AN OWNER LANE, AND IT WAS BENIGN
(verified, not assumed).** PR #4325 re-scored the 7 re-scorable FF-2D verdicts at HEAD
(`docs/FINDING-ff2d-verdict-rescore-2026-08-30.md`): **every one reproduces
byte-identically**; the diff is provenance-only (`scored_at_sha/date`); the FR-21 staleness
gate resets to Δ=0; the kill-rule did not fire. Bare keys unchanged (nyiso-t1f
PROMOTE-WITH-CAVEATS, all others HOLD). The board's verdicts are now *known* to describe
HEAD — strictly good for this track.

**4. OTHER BACKCAST MOVEMENT:** ercot-239 completed Phase-0 (PR #4331,
`FINDING-ercot239-missedevents-phase0-2026-08-30.md`): the 14-hour missed-event family is
**measured energy-lambda scarcity in tight-room hours no reserve adder carried** — model
ranks 12/14 inside its own bottom-5 % reserve room but prices it $0.00–$25.68; the
precommit's availability/outage/net-load-ramp priors are largely REFUTED (honest
prior-refutation); the object lands on the ercot-217 adjudicated conduct/model-class episode.
A successor **o7 attribution-harness precommit** landed ex ante (PR #4332: fleet-diff
de-laddering, swcap/markup/two-pass composition, HP-1..HP-3). caiso-221's records ARE on
main (verified `599f59b` reachable — the branch deletion lost nothing). Bench hygiene: 8
pre-stamp NEISO/PJM bench parts re-stamped (PR #4321/#4324). The backcast governance
director appended its 2026-08-30 sitting-execution entry (PR #4330).

**5. CAPX LANES: four in flight, nothing pushed yet** (S-4V, D10, S-5 dispatched this cycle;
D11-R since r#10; no capx branch at `65a39e3`). D10's WHY is now doubly stale (cites
nyiso-155 and gate (a) PASS) — the lane fetches fresh state and its charter (card A: close
leg (c) on measurement) is UNAFFECTED by the marker ruling, so it runs to completion; its
closing gate statement will read the live board. **S-123 START-TIME CHECK: FAILS a fourth
time** (miso-190 still the only branch in flight). Queue unchanged otherwise: D12 behind
D11-R's report, S-4b behind S-4V, S-6 behind S-5.

## 0h. Refresh #11 (2026-08-30, HEAD `9405aad`) — S-4's verification pair still owed → S-4V chartered; nyiso-157's Iroquois companion honestly REJECTED; ercot-239 opens

**1. THE FORECAST NAMESPACE IS BYTE-UNCHANGED since D7 (`ca8b749`, 2026-08-26)** — S-4's T1-F
verification pair, FC-1 re-score, leg registration and board refresh did NOT land in the merge
window; the board still shows NEISO FC-1 FAIL on the generic 0.50 the shipped 0.7352 replaced.
**S-4V is chartered this refresh** (the batch's one new lane): control/treatment pair at one
HEAD, FC-1 re-score, forecast-namespace registration (preserve-then-overwrite on the bare
`neiso-t1f` key), completion of the S-4 finding's §5/§8 TBDs in place, the NEISO
`hydro_accreditation` matrix-cell re-stamp S-4's §4 committed to, and the NEISO board block
refresh under D7-class records discipline (delegated to the lane). Expected effect,
pre-declared in the prompt from D2-B's committed arithmetic: hydro term 949.75 → 1,396.5 MW
(+446.7) against the 218 MW 2028 gap ⇒ 2028 clears by ≈ +229 MW on the D2-B basis; a
contradiction reports at full magnitude and never touches the sourced factor (rule 14).
If leg (b) flips on the measured determination, NEISO becomes the SECOND ISO with (a)+(b)
both PASS — its leg (c) then awaits a NEISO T1-X (a future D10 analog). S-4b stays queued
until S-4V lands.

**2. D11-R: still running, still nothing pushed** (no `capx-d11r` branch at `9405aad`;
owner-dispatched at r#10). D12 stays queued behind its report per the ratified sequencing.
D10 and S-5 remain unstarted — re-presented this refresh (D10 is still the highest-value
light lane).

**3. BACKCAST MOVEMENT (three commits since r#10):** nyiso-157 attested C6 on both Leg-1 A/B
bundles (`4d356f8`) and then solved the Iroquois companion arm — **REJECTED on its own
pre-filed W-gates** and registered anyway (`2026-08-30-nyiso-157-iroquois-companion`,
PR #4318; `2026-08-20-nyiso-147a-chp-btm` pruned for top-15 retention). The
prereg-before-solve discipline working exactly as designed: the companion was refuted by
gates frozen before the solve, and the Leg-1 PAR-attribution arm stands on its own A/B
(promotion decision still the backcast track's; branch open). **ercot-239 opened** (PR
#4320): PRECOMMIT-only Phase-0 driver characterization of the 14-hour missed-event family
(2023 carve-out lane object — model < $200 while actual ≥ $500; stated prior:
availability/outage/net-load-ramp representation, not offer curve; zero-solve, precommit
pushed before measurement). caiso-221's records commit sits on its branch unmerged;
miso-190's branch is open.

**4. S-123 START-TIME CHECK: FAILS a third time** (miso-190 in flight at `9405aad`). Held on
the check, re-run next refresh — no owner action needed.

**5. STATE VERIFIED UNCHANGED:** all six keepers as the r#10 watch table (ERCOT two-config
234+236, MISO miso-188-rvsscope, CAISO caiso-220, NEISO neiso-99, NYISO nyiso-155,
PJM pjm-162); `complete` = {NEISO, NYISO, PJM}, `final` EMPTY; freeze tier-scoped to locked
test. Bare verdicts: nyiso-t1f PROMOTE-WITH-CAVEATS, all others HOLD.

## 0g. Refresh #10 (2026-08-30, HEAD `9f73357`) — S-4 LANDED (factor 0.7352, verification pair pending); D11-R RUNNING; ERCOT becomes a two-config keeper

**1. S-4 LANDED — the second capx lane to complete, and it worked exactly as chartered** (PR
#4312, `docs/handoffs/FINDING-capx-s4-neiso-hydro-2026-08-30.md`). The NEISO hydro class factor
is SOURCED: **0.7352** = ISO-NE's own per-resource summer Seasonal Claimed Capability aggregated
over the active conventional-hydro fleet (August 2026 SCC Monthly Report, 244 assets,
1,396.472 MW) ÷ the model's own 1,899.5 MW accreditation basis — zero free parameters, shipped
as an explicit expression with the committed per-asset extract, provenance README, reproducible
fetch script and tests. The pre-declared direction (recorded before computation: <~0.39 flips
2027 FAIL, >~0.62 clears 2028) puts 0.7352 ABOVE the clearing threshold. **OUTSTANDING: the
T1-F verification pair had not completed at the finding draft** — headline items 2/3 read TBD,
and the forecast namespace is untouched, so FC-1's re-score, the leg registration and the board
refresh are still owed. The finding also surfaced successor work: ISO-NE's Nov 21 2025 ARA
filing implies **≈ +380 MW of requirement** (bigger than the old 218 MW gap) — queued here as
**S-4b** (NEISO requirement re-vintage on publication, rule 23), to be chartered once the
verification pair lands. The FCA-vintage half of S-4's own charter closed honestly as NO-SWAP
(CCP 2028/29 not yet published).

**2. D11-R IS RUNNING** (owner-dispatched this cycle; no branch pushed at fetch time). Its
prompt was merged one amend behind the final pack text — the D11-R deconfliction paragraph in
main still carries the stale "LIVE RIGHT NOW / three backcast sessions" snapshot (cosmetic; the
lane fetches fresh state regardless). Re-applied to the pack this refresh for the record.

**3. ERCOT IS NOW A TWO-CONFIG KEEPER** (owner ruling 3 of the 2026-08-26 sitting, executed
`db8836a5`): **forward keeper `2026-08-25-234-eastex-identity`** — "the configuration the MODEL
USES GOING FORWARD, forecast lane included"; CALIBRATED on its designated 2024–2025 span with
C3c the lone ledgered caveat ×2; its registered 3-year determination (NOT-YET on C3a/C3b-2023,
both 2023-only) stands untouched — plus the **2023 carve-out `236-swcap-clip-k33`**. Capx
consequences: (a) ERCOT's forecast-lane config of record is now eastex-identity — D11-R is
unaffected (it A/Bs both arms at its own fetched HEAD, which carries the eastex repair);
(b) the Q6 terrain moved by owner act, and Q6 stays RULED-HOLD — whether the two-config
structure satisfies §2.1b(2)(a)'s full-span requirement ripens only if a `complete` declaration
is ever considered, and is noted here rather than re-opened; gate (a) still fails on the absent
marker regardless.

**4. BACKCAST MOVEMENT:** **nyiso-157 registered the Leg-1 A/B** (control
`2026-08-30-nyiso-157-par-control` + arm `-par-attribution`, 2023–2025): the PAR attribution
restores a real downstate gradient — NYC−UW annual mean $0.59 → $10.00 in 2023 (measured
gradient ≈ $14.8), C3a-2023 +6.8 % → +1.0 % — and the Iroquois companion prereg is filed BEFORE
its solve; the lane continues (branch open, promotion decision the backcast track's). miso-190's
mechanism landed (`partial_plant_exit_carry`, gated default-off, unit-grain mid-window exits;
A/B scorer committed before it runs; branch open). caiso-221 killed the south-belly
surplus-pricing design object with measurement (branch open). Card 10: decision-1 (warm-start
flip) closed as CLOSED-OVERTAKEN.

**5. QUEUE STATE:** D10 remains the highest-value unstarted light lane (closes NYISO leg (c) on
measurement). **S-123's start-time check FAILS again** (miso-190 branch open) — held on the
check. S-5 ready (heavy re-score self-gates). S-4b queued pending S-4's verification pair. D12
queued behind D11-R per the ratified sequencing.

## 0f. Refresh #9 (2026-08-30, HEAD `a53b7b3`) — freeze goes TIER-SCOPED (card 6 executed); rubric v3.5 determination-neutral; still no capx lane started

**1. THE HOLDOUT SPEND FREEZE IS NOW TIER-SCOPED** (owner ruling 2026-08-26 card 6, executed
2026-08-30, `0589b6f`; record `docs/FINDING-holdout-governance-2026-08-26.md`): `active: true`
with `scope.tiers = ["locked_test"]` — the VALIDATION tier (2020–2022) is lifted from the freeze
and governed by the `complete` marker + `--holdout-authorized` alone, so the diagnostic
touchpoint loop is actually runnable for {NEISO, NYISO, PJM}; the locked test (2019/H1-2026)
stays frozen for every ISO and `final` stays EMPTY. Card 7 (`3643318`) added the standing
scheduling precondition to rule 22: an ISO is *eligible to be considered* for `final` only after
its 2020–2022 touchpoints have run and the loop has stopped surfacing repairs — eligibility is
never a grant. The CAMPD economic-layup charter is CLOSED WITH CAUSE in the same ruling (the
detector question stays open as a documented seam every keeper's availability envelope inherits).
**Director consequence: every pack prompt's freeze guardrail is updated to the tier-scoped
phrasing this refresh** — a capx lane touches neither tier, but this track does not quote stale
governance state. **Nothing else changes for capx lanes**: forecast-mode 2026+ stays
unrestricted, and no capx lane ever solves an out-of-training backcast year.

**2. RUBRIC v3.5 RESOLVED THE STANDING WATCH ITEM HARMLESSLY.** The xiso-6 diurnal
price-amplitude decision card (watched since r#6 as "could touch six determinations") was ruled
option (B): amplitude added REPORTED-ONLY and BAND-FREE — measured, published, no status, no
budget — and **re-verified determination-neutral over the 2026-08-30 six-keeper roster**
(`rule-history.md` changes table, 2026-08-30). Watch item CLOSED.

**3. BACKCAST MOVEMENT:** CAISO keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (the caiso-200
recipe replayed on the now-ACTIVE measured membership crosswalk — caiso-200 no longer reproduces
at HEAD; promoted by owner act on the pre-registered rule; CAISO holds no marker, no re-key due).
**miso-190 is in flight** (branch open: the partial-plant mid-window exit carry, miso-188's
named-not-built successor; PREREG frozen before the mechanism exists — the lane keeps validating
the S-123 hold). NYISO Leg-1 (eastern-seam PAR attribution) branch still open, nyiso-157 A/B
gate scorer filed before its solves. ERCOT: the O7 P0-seam Phase-0 landed ("restoration
escalates, exposure is inherent") plus two governance rulings (G-SPUR lidless count; the ≥$1,000
band-count 59 → 61 correction) — no ERCOT branch currently open. Forecast namespace:
**byte-unchanged**; board still NYISO (a) PASS · (b) PASS · (c) fail · (d) none, all others HOLD.

**4. CAPX LANES: none started** (no `capx-*` branch at `a53b7b3`). The r#8 batch stands: D10 +
D11-R + S-4 to dispatch (all light). S-5 ready — its heavy re-score self-gates on a free slot,
so it is safe to start as a fourth session any time. **S-123: the owner's hold-until-r#9 expired
and the r#9 start-time check FAILS** (miso-190 in flight) — it stays held on the check itself,
re-run every refresh; no new owner decision needed.

## 0e. Refresh #8 (2026-08-30) — no capx lane started; NYISO winter intake AUTHORIZED (backcast track); D11 RE-SCOPED to the D-1 volume rule

**1. NONE OF THE FIVE STANDING PROMPTS HAS BEEN STARTED.** `git ls-remote` at `d8d08ac`: no
`capx-*` branch exists. D10, D11, S-123, S-4 and S-5 all stand written in the pack. The board,
verdicts, markers and freeze are unchanged from refresh #7: NYISO (a) PASS · (b) PASS ·
(c) fail · (d) none, everyone else HOLD on FC-1; `complete` = {NEISO, NYISO, PJM}; `final` EMPTY;
holdout spend freeze ACTIVE. (Keepers: MISO moved mid-refresh — item 4.)

**2. BACKCAST MOVEMENT — nyiso-156b: the owner RULED the nyiso-156 card's Q1 as OPTION A, the
winter locational identification intake is AUTHORIZED** (PR #4295, `ab0513e`; spec
`docs/INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`). Two legs: **Leg 1** — the
eastern-seam PAR attribution from NYISO's own published NY-NJ PAR interchange percentages
(**session-executable, the owner gate on PREREG-nyiso126 is LIFTED**; adds an ABC→NYC AC border
path the model does not carry); **Leg 2** — MyNYISO as-enforced AORR access (owner-executable,
fail-closed). The ruling also corrected the stale "seam unidentifiable" record: nyiso-125's
refusal was discharged on identification by nyiso-126 the same day; the leg was
authorization-blocked, not identification-blocked. **Why this track cares — it bears directly on
Q5**: the card's §4 measures that closing the winter face alone (−$3.92/MWh of the annual lw mean)
returns C3a-2025 to ≈ −5.3 % (in band), whereupon C3c reverts to the lone failure, the standing
rule reclassifies it, and the determination returns **CALIBRATED**. Q5's tension (a `complete`
marker on a NOT-YET keeper) now has a live structural resolution path through the owner's own
backcast lane; the precedent-reconciliation question stays worth writing regardless (§3).
Also landed: the bench-fingerprint adjudication (PR #4293 — 11 "stale" bench parts adjudicated
UNLABELLED-not-wrong, measured over the complete builder-drift commit set; backcast dashboard
hygiene, no gate contact).

**3. D11 IS RE-SCOPED TO D11-R — THE D-1 BANG-BANG VOLUME RULE — and the pro-forma signal build
is HELD IN ABEYANCE.** Recorded under the remit refresh #7 claimed (the B-C signature chartered
the OBJECT — what the entry screen is meant to represent — not a particular lane). The evidence
that forces it: `FINDING-entry-signal-forward-expectation-2026-08-25.md` §3 — three signal
constructions spanning a ~$200/MWh swing in the entering-2024 mean produce one trajectory
(terminal RM 25.19 / 40.24 / 40.38 %), *"D-1 owns the trajectory; the signal lane should not be
re-chartered against it"* — and its §7 adjudication recommends exactly this: **"(b) first — rest
the signal lane and charter D-1's volume rule."** The construction is already named and
pre-measured: L-1b's **margin-exhaustion closure** (`FINDING-entry-signal-l1-2026-08.md` §2,
probe `scripts/probes/entry_signal_l1b_allocator_counterfactual.py`) — *build until the screen's
own repriced margin is exhausted, bounded by the same caps* — is the zero-DOF candidate, measured
offline at terminal RM 18.7 % vs the shipped 25.2 % with the B-2 cobweb surviving (real market
dynamics, NOT the target). D11-R productionizes it behind a NEW default-OFF ScenarioConfig field
and A/Bs it on an ERCOT T1-F leg. Margin exhaustion **is** the allocator half of the developer
pro-forma, so this stays inside the B-C charter. The signal-lane successor rung — the
scarcity-consistent delta basis, §4's named successor for the two-scarcity-objects defect — is
**queued as D12**, to run only if the owner continues the signal lane; the owner can override
either disposition at the finding's §7 escalation, which remains open.

**4. DECONFLICTION — THREE BACKCAST BRANCHES WERE IN FLIGHT** at `d8d08ac`
(`claude/caiso-c3a-overrun-closure-5n84mn`, `claude/ercot-backcast-calibration-9wkxrg`,
`claude/miso-188-rubric-failure-tuning-m1ph17`) — **and the MISO one MERGED MID-REFRESH**
(`212308b`, PR #4296): **miso-188 promoted a new MISO keeper, `2026-08-30-miso-188-rvsscope`**
(full-span, single delta `retiree_vintage_status_scope=true` — a NEW gated default-off field with
its rule-28c matrix row + cells minted; drops 28 dark retiree-channel units / 1,434 MW after the
phase-0 audit caught Grand Tower dispatching 4.8 TWh while CAMPD-dark for three years;
**C1 CC_REGULAR-2024 +8.037 → +6.820 PASS; determination narrows to NOT-YET on {C3a-2025}
ALONE**, promoted on the PREREG's own rule). Consequences: CAISO and ERCOT branches remain in
flight, so the ≤2-heavy cap must still be checked before any capx solve launches and D11-R's
deconfliction note stays sharp (ERCOT backcast live). **S-123's hold is DOWNGRADED to a
start-time check**: the MISO backcast lane is momentarily between sessions, so S-123 may start
whenever no new MISO backcast branch is in flight, its optional re-measure still gated on a free
heavy slot (MISO = 9.6 GB no-co-run). The batch issued this refresh stays deliberately all-light:
**D10** (NYISO T1-X, 2.82 GB), **D11-R** (Phase-0 zero-solve first), **S-4** (NEISO, 9.2 min).
S-5 stands ready (PJM quiet on the backcast side) for the next free heavy slot; S-6 strictly
after it.

**5. OWNER SITTING AT REFRESH #8 (2026-08-30, in-session decision cards) — FOUR RULINGS:**
- **Q5 → WAIT FOR WINTER INTAKE.** The precedent conflict (CAISO withdrawal vs nyiso-155
  structural-integrity promotion) is left standing unreconciled; the nyiso-156 winter-intake path
  is the designated resolution route (measured: winter-face closure alone returns the keeper to
  CALIBRATED). No marker moves; gate (a) stays PASS on the literal test. If the fact pattern
  recurs before the intake resolves it, the reconciliation question returns to the owner.
- **Q6 → HOLD, NO ACTION.** No direction is issued to the ERCOT backcast lane; revisit when it
  goes quiet. Gate (a) keeps failing on both counts meanwhile — recorded, not escalated further.
- **SIGNAL LANE → D11-R RATIFIED, D12 QUEUED.** The refresh-#8 re-scope is ratified at the
  finding's §7 escalation: volume rule first; D12 (scarcity-consistent delta basis) is chartered
  only after D11-R reports. The §7 escalation is now RESOLVED — (b) first, (a) queued behind it.
- **S-123 → HOLD UNTIL NEXT REFRESH.** This SUPERSEDES item 4's mid-refresh downgrade to a
  start-time check: the owner holds S-123 one more cycle to see whether a new MISO backcast
  session starts. Re-present at r#9.

**5b. POST-SITTING BURST (same day, `212308b` → `5ce92f4`) — two rulings validated within the
hour:** PR #4298 merged this ledger's refresh-#8 commit; PR #4297 merged the CAISO backcast
branch (caiso-220 records — CAISO no longer in flight); **PR #4299 merged miso-189** (phase-0
zero-solve refuting the Illinois scarce delivered-gas candidate) — a NEW MISO backcast session
did start immediately, exactly what the S-123 hold-until-r#9 ruling anticipated; PR #4301 landed
an ERCOT governance correction (≥$1,000 band count 59 → 61, owner ruling 2026-08-26); and
**PR #4300 shows nyiso-156 LEG 1 (the eastern-seam PAR attribution) ALREADY EXECUTING** —
nyiso-157 filed its A/B gate scorer (K1–K9) before the solves — so the Q5 wait-for-winter-intake
path is in motion, not hypothetical. ERCOT's backcast branch remains the one still in flight
alongside the NYISO Leg-1 branch.

**6. PACK CORRECTIONS with the reissue:** D10's WHY cited keeper
`2026-08-22-nyiso-152-duty-complete, CALIBRATED` — stale since the nyiso-155 promotion; now cites
the NOT-YET keeper with the Q5 posture stated (gate (a) taken as PASS on the literal test, not
re-read downward). Its guardrail "CALIBRATED with an owner-ratified frontier" likewise corrected
(frontier returned to the owner at the promotion). D7's row moves to LANDED (`ca8b749`, PR #4289
— was recorded in §0d but the scoreboard row still read ISSUED).

## 0d. Refresh #7 (2026-08-26) — D7 LANDED; ERCOT is CALIBRATED but 2023-ONLY; D11's premise is undercut

**1. D7 LANDED** (PR #4289, `ca8b749`) — the first dispatched capx lane to complete. Records-only,
two files, no solve. It carried the NYISO re-score onto the board **with the source finding's own
honesty note attached** (the 2026 leg was also flipped by −341.4 MW of epoch demand drift and would
have passed by a thin +332.9 MW without the intake, so the 2,749.9 MW credit buys structural margin,
not the sign), applied the signed card-A leg-(c) harmonisation, and carried the base-year I7
scoring instruction into the board's prose. **It re-read NYISO's four legs against the criteria
rather than asserting them** — including verifying full-span at the keeper's registry years — and
**recorded the Q5 tension while leaving the verdict unmoved**, exactly as chartered.
**NYISO's board gate now reads (a) PASS · (b) PASS · (c) fail · (d) none, `open: false`. No gate
opened; leg (d) is byte-unchanged for all six ISOs.**

**2. ERCOT IS NOW `CALIBRATED` — AND ITS KEEPER IS 2023-ONLY.** Keeper
`2026-08-25-236-swcap-clip-k33` (−7.3 % / 0.102 / 180) scores **CALIBRATED with an EMPTY failing
set** — the 2023 price object that card Y held open on 2026-08-24 has closed. But
`registry/2026-08-25-236-swcap-clip-k33.json` declares **`years: [2023]`**.
→ **Gate (a) now fails for ERCOT on TWO independent counts**: it is absent from `complete`, *and*
§2.1b(2)(a) requires a **FULL-SPAN** keeper (rule 16), which a 2023-only run is not. **This is the
note from refresh #6 becoming load-bearing.** A CALIBRATED determination is necessary but not
sufficient: **declaring ERCOT `complete` would NOT open its gate (a) while the designated keeper
covers one year.** ERCOT would need a full-span (2023–2025) keeper carrying the swcap-clip recipe
first. That is an owner-tier sequencing point, not a director action — **Q6**.

**3. D11's PREMISE IS SUBSTANTIALLY UNDERCUT by a lane I did not charter.** The ERCOT
`entry_forward_expectation_signal` A/B (`94463db`) built and measured a **THIRD** entry-signal
construction. Its result: P1 CONFIRMED (iron_air 3,000 MW enters all four steps), P2 CONFIRMED
(wind 1,092.2 MW enters), but **P3 OVERSHOOT SURVIVES — terminal RM 40.38 % vs disarm 40.24 % vs
control 25.19 %** — and its adjudication is the finding that matters:
**"the trajectory is invariant across all three measured signal constructions and D-1's bang-bang
volume rule owns it."** It also surfaced an unpredicted measured defect: *S_current's pro-forma tail
and the duals' realized overlay are two different scarcity objects*, making the entering-2024
composed level unphysical (mean −$48.22/MWh; solar capture −$185/MWh). Cell stays `O`;
owner decides the next rung.
→ **D11 as chartered would build a FOURTH signal construction against evidence that the signal is
not what owns the outcome.** Its Phase 0 must now absorb this: either re-point at **D-1's bang-bang
volume rule** (the thing measured to own the trajectory) or justify in writing why a pro-forma
construction still earns a session. The B-C signature chartered *the object*, not a particular
lane; re-scoping it on new measured evidence is within the director's remit and is recorded here.
**The "two scarcity objects" defect is itself a strong candidate lane** — it is a physical-coherence
problem in the entry screen's own inputs, not a signal-shape question.

**4. Also landed:** `audit_keepers` gained **check E11 — keeper-lineage recipe fidelity over the
full `solve_and_persist` kwarg surface**, which closes the "silently lost from the keeper lineage"
class that the nyiso-155 hydro repair was a victim of. MISO keeper re-keyed to
`2026-08-26-miso-187-nucavail` (NOT-YET, fuelmix + price_mean; `nuclear_unit_availability` U→K).
CAISO's caiso-220 replay is mid-solve (checkpoints only). ercot-237 Phase-0 band-swap
characterization is zero-solve.

---

## 0c. Refresh #6 — no lane started; three keeper promotions, and NYISO's gate-(a) BASIS moved under us

**1. NONE OF THE SIX PROMPTS HAS BEEN STARTED.** `git ls-remote` at `6af12ee`: no `capx-*` branch
exists except this ledger. D7, D10, D11, S-123, S-4 and S-5 all stand as written
(`docs/handoffs/capx-director-prompt-pack-2026-08.md`); the only thing that moved under them is
`main` (`99c8cf5` → `6af12ee`), which every prompt already handles by fetching fresh.

**2. NYISO'S KEEPER IS NOW NOT-YET, AND IT STILL HOLDS `complete`.** Promoted 2026-08-25:
**`2026-08-25-nyiso-155-hydro-repair`** (the hydro truncated-vintage repair pair
`hydro_backfill_year=2024` + `hydro_eia930_monthly=true`, zero fitted scalars), **NOT-YET on
price_mean + price_tail**. Promoted BY OWNER RULING on structural integrity over gate regression,
with **the D-5(b) worse-determination stop FIRED, ESCALATED, and resolved by that ruling**; the
determination is written explicitly into the marker (nyiso-120 precedent). C3a-2025 −8.1 → −10.8 %
because the truncation had been **masking ~2.7 pp of the real 2025 offer-level object**. **Frontier
status returned to the owner** — the 2026-08-23 ratification's CALIBRATED premise no longer holds.

→ **This moves the BASIS under my refresh-#5 headline, and I state it plainly rather than let it
stand.** Gate (a)'s literal test (charter §2.1b(2)(a)) is *a designated full-span keeper AND an
entry in the `complete` block*, and NYISO still satisfies both, so **gate (a) reads pass on the
test as written**. But the marker now rests on a NOT-YET keeper — **precisely the fact pattern that
withdrew CAISO's marker on 2026-08-06** ("a `complete` marker cannot stand on a NOT-YET keeper").
The two are reconciled only by the owner's explicit ruling. **That is an owner-tier question, not
mine: it is Q5.** Leg (b) is untouched — it is the forecast `nyiso-t1f` verdict
(PROMOTE-WITH-CAVEATS), which no backcast promotion can move.

**3. THE HYDRO TRUNCATION DOES NOT REACH OUR I7 PASS — verified, not assumed.** The backcast repair
fixes a 2025 hydro census truncated to **3 plants of ~147**. The forecast accreditation was already
immune by construction: `modelled_hydro_nameplate_mw` clamps the census to
`EIA923_LATEST_FINAL_VINTAGE`, and its docstring names this exact hazard — *"vintages after it are
monthly early releases carrying only the large reporters … so an unclamped year would accredit a
partial fleet."* So NYISO's forecast hydro credit (1,763.3 MW) was never computed on the 3-plant
vintage, and the extcap I7 PASS stands. **Also verified: the NYISO extcap registry entry survives
intact** at `capacity_market.py:2574` (`3_168.5 * (1.0 - 0.1321)`); the only change to that file
this cycle was CAISO's AS-revenue row.
**A consistency item for D7/D10, flagged not resolved:** the backcast now consumes the *repaired*
hydro input (147 plants, EIA-930 monthly pin) while the forecast consumes the *clamped complete
census*. Two constructions of one physical quantity. Not a defect I have established — a question
worth one paragraph in the next NYISO lane.

**4. ERCOT's keeper is now 2023-ONLY** — `2026-08-25-235-2023-discrete-k24`, NOT-YET on price_mean
(C3a-2023) alone, and **the first ERCOT run with C3b-2023 AND C3c-2023 both PASS**. It is registered
under the **rule-16 waiver the owner granted 2026-08-23, now SPENT**. No gate reading changes
(ERCOT fails gate (a) on the marker regardless) — but note for any future ERCOT declaration that
gate (a) also requires a **full-span** keeper, which a 2023-only keeper is not.

---

## 0. Refresh #5 — NYISO CLEARS FC-1. The program has its first ISO with legs (a) and (b) both passing.

**1. D2-NYISO-INTAKE LANDED and it worked** (PR #4259). NYISO added to
`ADEQUACY_EXTERNAL_TIE_FIRM_MW` on its **own published** external capacity — 2026 Gold Book
Table V-1, Summer-2026 net capacity purchases from external control areas, **3,168.5 MW ICAP,
sha-verified source** — converted to the model's UCAP requirement basis with the **same published
NYCA ICAP→UCAP factor the requirement side applies** (rule 19, one basis): 3,168.5 × (1 − 0.1321)
= **2,749.9 MW**. Corroborated against NYISO 2025 SOM Fig. A-97. Deliberately NOT the 900 MW HQ
dispatch floor, NOT the 4,350 MW Simultaneous Import Limit.
**The pre-declared honesty test passed: the value overshoots the 35.7 MW residual ~77×** — a real
accreditation, not a number tuned to the invariant.
**Re-scored leg `nyiso-2026-2030-extcap-capxd2`: 5/5 years, 14/14 invariants PASS.
FC-1 FAIL['I7'] → PASS. FC-2 CAVEAT → PASS. Determination HOLD → PROMOTE-WITH-CAVEATS.**
The 2026 accredited firm reproduced the pre-solve prediction to the digit (32,085.5 + 2,749.9 =
34,835.4 MW). Honest decomposition disclosed in the finding: HEAD demand drift since the FFR-3A-2
epoch (−341.4 MW peak) alone would have passed 2026 by a thin +333 MW; **the intake moves every
year to a structural +2.9–4.2 GW surplus.** Only remaining caveat is FC-7 — the program-wide
missing DOF-ledger instrument (lane D8).

**2. NYISO's §2.1b gate now reads (a) PASS · (b) PASS · (c) `fail` · (d) none.** *(Leg (c) was
`na` at refresh time; the owner's card-A signature harmonised it to `fail` — §3.)*
`frontend/data/forecast/program-status.json` was last touched 2026-08-24 05:55 and still carries
NYISO as FC-1 FAIL / gate (b) fail. **This is the D7 trigger, and it is immediate.** NYISO is the
first ISO in the program to clear both legs that depend on model quality; what remains is leg (c),
now chartered as a run (**D10**), and leg (d), owner authorization.

**3. D2-B LANDED** (PR #4258) and is the most substantial diagnosis this track has produced.
Three of four legs reproduced from committed artifacts with no solve — MISO 2026 and CAISO
2026–2030 **to the MW**, NEISO to the verdict's own rounding. Headlines:

- **MISO IS THE SECOND NYISO.** It credits **zero** external firm capacity while the forecast path
  floors a **1,400 MW Manitoba firm-hydro block at 100 % in every hour, default-on**. The registry
  now omits **exactly the two ISOs** that fail I7 with a default-on firm-import floor behind the
  miss. The registry's failure mode is **coverage, not basis** — every populated entry is
  accreditation-based and consistent with dispatch.
- **A second MISO defect, provable from the repo's own citation blocks:** the fallback requirement
  multiplies the **PY 2024-25** ICAP PRM (0.179) by the **PY 2025-26** ICAP→UCAP ratio, and that
  ratio's own cited source publishes ICAP 15.7 % / UCAP 7.9 % — contradicting the PRM it is
  multiplied with. Same-document PY 2025-26 pairing puts the requirement **2,637.4 MW lower = 44 %
  of MISO's 6,037 MW gap.** Correctly NOT shipped (solve-affecting, shares machinery with the
  backcast-reachable retirement floor), and routed with its expected effect stated in advance so it
  cannot be back-fitted.
- **NEISO's hydro fallback is load-bearing and decides the verdict's sign.** The generic
  `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50` (no ISO-published NEISO factor exists — an FFR-1C
  open item) contributes **949.75 MW against a 218 MW gap — 4.4×**. A class factor of 0.39 flips
  2027 to FAIL; 0.62 clears 2028 outright. **NEISO 2028 is not decidable at current input
  fidelity** and must be read as "within input uncertainty", not as a capacity-evolution defect.
- **PJM's 366 MW is an UNDERSTATEMENT, and my "PJM is the shortest path to T2" thesis is REFUTED.**
  The requirement factor falls **discontinuously at the published-FPR table edge** (2028→2029):
  beyond delivery year 2028/29 the model falls back to a composite whose IRM half is two vintages
  stale, dropping the bar **3.18 % of peak = 5,492 MW** at the 2030 peak. Against a hold-last-FPR
  requirement — the convention `forward_net_cone_anchor` already establishes elsewhere — 2030's miss
  is **~5.9 GW, not 366 MW, and 2029 plausibly fails too.** Every correction on both sides runs
  against leniency. PJM's supply side is **the one leg no committed artifact can reproduce.**
  *(Owner signed C-A 2026-08-25: hold-last-FPR is now the declared convention — §3.)*
- **CAISO's forks were already adjudicated by FFR-3P** and stand: fork 2 (fleet-snapshot vintage)
  dominates — base-year battery fleet 8,000 MW against a published **14,131 MW NDC**, ≥5,933 MW =
  **90 % of the base-year deficit**. D2-B adds the horizon evidence: the **14,043.6 MW
  administrative-CT backstop ladder and the 65.5 % backstop share are DOWNSTREAM artifacts of the
  input-vintage deficit, not independent defects.** Fix B-1 and most of the ladder never fires.
- **Program-wide:** no base-year I7 leg is a capacity-evolution defect, and neither backstop tuning
  nor floor relaxation is ever the answer to one. Carried into D7 as a scoring instruction.

**4. Method note worth carrying:** an evolution ledger's exits live in **two keys** —
`retirements` *plus* `confirmed_derates`. CAISO 2027 reads 1,491.0 MW in the first and 1,333.0 MW
in the second; summing only `retirements` under-counts the exit wave by 47 %. That is the repaired
I4/A1 leak working as designed — but any decomposition that forgets the second key mis-attributes
the gap.

---

## 1. Lane scoreboard

| lane | scope | status | branch | model | evidence / notes |
|---|---|---|---|---|---|
| **D1 BOARD-REFRESH** | Board vs live verdict records; A1/I4 cross-ISO | **LANDED** `c02f766` | `capx-d1-board-refresh-nfb31y` | Opus | 36 fields, 0 gates moved. |
| **D2-NYISO** | Root-cause NYISO I7 | **LANDED** `0a2238c` | `capx-d2-adequacy-nyiso-yxv6v0` | Opus | Adjudicated; shipped no fix, deliberately. |
| **D2-NYISO-INTAKE** | Gold Book external capacity | **LANDED — I7 CLEARED** `3786191` | `capx-d2-nyiso-extcap-sewmyx` | Fable | §0.1. First FC-1 PASS in the program. |
| **D2-B I7 LEDGER DECOMPOSITION** | Reproduce/decompose MISO, CAISO, NEISO, PJM | **LANDED** `5dda152` | `capx-d2b-i7-ledger-xaakeu` | Fable | §0.3. Six successor lanes named (S-1..S-6). |
| **D7-NYISO GATE RE-SCORE** | Refresh the board to the extcap re-score; re-read NYISO's four legs; **apply the card-A leg-(c) harmonisation** (CAISO + NYISO `na`→`fail`, `"c"` into both `closed_on`) | **LANDED** `ca8b749` (PR #4289) | `claude/capx-d7-nyiso-gate` | Opus | §0d.1. Board re-scored, no gate moved, Q5 tension recorded verbatim. |
| **D10 NYISO T1-X CROSSOVER** | Run NYISO's T1-X so gate leg (c) closes on a measured FC-4 | **LANDED** PR #4354 — FC-4 measured FAIL at full magnitude (price +29.9/+2.5/−24.0 %; co2 ~10 %, NOT the program-wide miss), quarantine PASS, registered `nyiso-t1x` with run_config.json; **NYISO leg (c) → PASS on measurement** | `claude/capx-d10-nyiso-t1x` | Fable | Card A's own consequence, executed. D5 evidence: the co2 derivation question is three-ISO, not universal. |
| **Q5-W NYISO MARKER WITHDRAWAL** | Execute the r#12 Q5 ruling: withdraw NYISO from `complete` (CAISO precedent, uniform), flip board gate (a), FINDING + audit | **LANDED** PR #4343 (`ecc2d60`) — both surfaces one session; `complete` = {NEISO, PJM}; NYISO gate (a) → fail | `claude/q5w-nyiso-marker-withdrawal` | Fable/Opus | Keeper untouched (nyiso-157 stands). Re-entry = new owner declaration on a CALIBRATED keeper. Validation-tier authorization lapsed. |
| **D11-R ENTRY VOLUME RULE (D-1)** | Productionize the L-1b margin-exhaustion closure — the measured zero-DOF volume rule — behind a default-OFF field; A/B on ERCOT T1-H | **LANDED** PR #4355 — `entry_margin_exhaustion` shipped default-OFF, zero-DOF confirmed; live arm 22.02 % vs shipped 25.19 (−3.17 pp), B-2 survives; gas half inert on the live reserve leg; matrix cell **O**; **arming RULED Q8: HOLD until D12** | `claude/capx-d11r-entry-volume-rule` | Fable | §0j.1. Both A/B arms registered on the forecast namespace with run_config.json. |
| **D12 SCARCITY-CONSISTENT DELTA BASIS** | Both `S` evaluations on one scarcity basis | **LANDED** PR #4373 — decisive, zero-solve: realized-r leg adjudicated a cross-year PHANTOM; `entry_forward_reserve_leg` shipped default-OFF; exhaustion's gas half goes live via exact identity; recommended arm-both (§7) → **Q10 ruled: confirm-pair then arm (lane D12-C)** | `claude/capx-d12-scarcity-basis` | Fable | Bang-bang RM path unchanged under the consistent basis; CT band \|err\| 3.879→0.879. |
| **D12-C ARMING CONFIRMATION PAIR** | ONE arm-vs-control A/B on ERCOT T1-H, the TWO fields as a single logical delta; **arming auto-executes on a confirming record** (Q10); a contradiction returns to the owner unarmed | **CONCLUDED — CONTRADICTION** PR #4406: V-2 cc window missed (0 vs [750, 1,250]); V-1/V-3/V-4/V-5 + G-1/G-2 all pass; divergence = pre-declaration derivation error (offline walk's restricted candidate set; live solar competition ⇒ MORE exhaustion, same mechanism); nothing armed, cells `O`, both bundles registered; tolerance NOT widened (rule 21) | `claude/capx-d12c-confirm-pair-oji8wv` | Fable | §0o.1. **Q15 re-decision card presented at r#18** — the protocol's own "owner may judge confirming-in-substance" clause. |
| **D13 BOARD RECONCILE** | Q7 execution + S-5 PJM restatement + landed-lane currency + stale-prose repair | **LANDED** PR #4372 — all five edits in; no gate opened; blob verification recorded | `claude/capx-d13-board-reconcile` | Fable/Opus | Board internally consistent again. |
| **D14 NEISO T1-X CROSSOVER** | NEISO's first-ever T1-X | **LANDED** PR #4376 — FC-4 measured FAIL (price +13.3/+7.9/−21.8 %; co2 +12.8/+10.6/−2.3 % — second no-coal control for D5), quarantine PASS, `neiso-t1x` registered; **NEISO = FIRST (a)+(b)+(c) ISO; leg (d) held for S-4b (Q11)** | `claude/capx-d14-neiso-t1x` | Fable | First T1-X with in-window economic exits: retirement COMPOSITION miss surfaced (recall 2/6) — a real successor object. |
| **S-123 MISO ADEQUACY PACKAGE** | S-1 requirement re-vintage + S-2 external-capacity intake + S-3 ledger differencing | **LANDED (complete)** PRs #4397/#4398/#4402 + **#4441 (S-123-V-R, Opus)** — three terms shipped (S-1 −2,637.4; S-2 +3,505.9; S-3a −9,236.8; 2026 position −6,037 → +9,343 MW, 2.5× overshoot, honest); **§6 verification re-measure LANDED at r#21** (registered, board refreshed, finding §6 filled); D9 adjudicated UNREACHABLE + routed | `claude/capx-s123-miso-adequacy-ukgiow` | Fable | §0o.3. Routed to director: the armed-interface **mc=0 seam placeholder** defect (→ D16 queued). Verify §6 fills on its next landing. |
| **S-4 NEISO HYDRO ACCREDITATION** | Per-resource ISO-NE SCC → class factor, replacing the generic 0.50 | **LANDED** PR #4312 — verification half chartered as **S-4V** (r#11) | `claude/capx-s4-neiso-hydro-syqu7m` | Fable | Factor 0.7352 sourced, above the pre-declared 0.62 clearing threshold. Finding §5/§8 TBDs are S-4V's to fill. |
| **S-4V NEISO VERIFICATION** | Complete S-4's owed §5: control/treatment T1-F pair at one HEAD, FC-1 re-score, forecast registration (preserve-then-overwrite on bare `neiso-t1f`), finding TBDs, NEISO `hydro_accreditation` cell re-stamp, NEISO board block refresh | **LANDED** PRs #4337/#4353 — bare `neiso-t1f` HOLD → **PROMOTE-WITH-CAVEATS** (I7 PASS ×5, sole WARN the pre-declared I12-2026); control preserved as `neiso-t1f-s4control`; matrix cell O → K; board block refreshed | `claude/capx-s4v-neiso-verification` | Fable | **Honest attribution: the control ALSO clears 2028 — epoch drift alone flips the year; the factor's isolated effect is exact.** NEISO takes the (a)+(b) lead. |
| **S-4b NEISO REQUIREMENT RE-VINTAGE** | Adopt the published Nov 21 2025 ARA filing pair | **LANDED** PRs #4392/#4396 — companion LOCATED (2026 CELT 4.1 "Incl. ARA 3"); 4-value zero-DOF intake (factor 1.02861, DR 0.08784, imports 409.31); move +651…686 MW/yr, LARGER than declared; **I7 holds PASS ×5** (floor retains 699.3 MW of gas-CC exits — decomposition ≤0.1 MW, zero-drift control, exact 2026 isolation); **leg (b) STRENGTHENS** (FC-1/FC-2 CAVEAT→PASS); 2028/29 margins floor-dependent, noted at full magnitude | `claude/capx-s4b-neiso-ara-3jhedd` | Fable | §0n.5. Q11's hold RESOLVED ⇒ leg-(d) card presented at r#17 (§3 Q13). |
| **S-5 PJM REQUIREMENT HORIZON-EDGE** | Implement hold-last-FPR + the D-1 checker repair; re-score PJM's T1-F leg | **LANDED** PR #4340 — hold-last-FPR in `resolve_forecast_pool_requirement` (zero DOF), checker year-threading repaired, **I7 2030 restates 366 MW → 5,858 MW, 2029 plausibly joins**; no solve, no registration; board restatement carried by D13 | `claude/capx-s5-pjm-horizon-edge` | Fable | The worse reported result, produced on purpose (the card's own arithmetic). 2029/30 intake pointer at the table edge (BRA Dec 2026). **S-6 unblocked.** |
| **S-6 PJM T1-F LEDGER RUN** | The minimum run that makes PJM's supply side observable, against the corrected (hold-last) bar | **LANDED PR #4436 (S-6-R, Opus)** — `pjm-2026-2030-s6-ledger` registered, `pjm-t1f` re-scored, board refreshed; **FC-1 FAIL = {I7, I12}**, three-year I7 fail set measured | `claude/capx-s6-pjm-ledger-r2` | Fable→Opus | §0q.2 + §0r.2. The corrected supply-side bar is now measured, not extrapolated. |
| **D5 FC-4 CO2 CROSSOVER** | Attribute the three-ISO crossover CO2 miss | **LANDED** PR #4374 — miss is a SCORING-TAXONOMY DROP (unmapped model-`COAL` → zero scored CO2): MISO 97–117 %, PJM 75–98 %, ERCOT 46–103 % of the miss; rate derivation EXONERATED (±5 %); controls clean → **Q12 ruled: D5-R full fix chartered** | `claude/capx-d5-crossover-co2` | Fable | Third instance of the known class-grain seam. |
| **D5-R SCORER COAL-GRAIN REPAIR** | Fix the seam at gmModel build (canonical taxonomy chain, rule 19 — also repairs the C1 fuelmix coal-row phantom), zero-solve re-score the committed crossover bundles | **LANDED** PR #4388 — every cell within ±0.2 pp of the §5.2 table; ALL hard controls pass (NYISO byte-identical, family rows deep-equal); PJM+MISO co2 leave the FC-4 FAIL sets, ERCOT 2023/24 stay FAIL honest; fifth bundle (neiso-capxd14) skip adjudicated sound at r#17 (generic-COAL 0.001 TWh ⇒ ~0.004 % bound) | `claude/crossover-co2-grain-repair-oycsy6` + completion `…-t6hoe2` | Fable | §0n.1–2 + §0o.2. **COMPLETION PASS PR #4403**: fifth bundle rescored (+0.49 pp 2024/25 — corrects the director's r#17 one-year-row bound), `neiso-t1x-pre-d5r` preserved, board co2 annotations EXECUTED (§0n.3 records item CLOSED). Live gate keys (ffr3a3/-3a4) still carry the mismeasured rows — bundles never committed, annotated in place. |
| **D3 MISO RETIREMENT / G3** | G3 cap-grain `retire.total_gw` t1h regression — attribution-first, zero-solve Phase 0 | **LANDED** PRs #4455/#4458 — flip ATTRIBUTED to class (b); the fix moved coal TOWARD reality (+18.4 %→+9.1 %) and the band failed because excess coal had been compensating **3.458 GW of real gas/oil exits the screen produces at 0.0**; post-fix value byte-identical to FFR-2B's paired control, so the knife-edge −9.8 % PASS was the artifact; classes (a)/(c) REFUTED | `claude/capx-d3-miso-retire-g3` | Fable | §0s.1. "Retirement-volume regression" retired as a framing. Routed PRIMARY → lane **D17**. |
| **D4-I3 ERCOT** | I3 scarcity-slack invariant (net-revenue half HELD under card Y-C) — zero-solve breach-set + pre-declared post-arming expectation + FR-6 code-comment home | **LANDED** PR #4460 — I3 is an **under-build signature**, monotone in added GW across 11 records; **no committed ERCOT posture clears I3 and the I12 band together** (one phenomenon, not two); P-1..P-8 + F-1..F-4 frozen for the measurement half; six repairs routed; two measurement-integrity findings (vintage-only comparability; the instrument emits no MW/hours/GWh) | `claude/capx-d4i3-ercot-slack` | Fable→**Opus** | §0s.1. Measurement half → lane **D4-M** (NOT D6 — ERCOT is curve-OFF; see §0s.4). R-6 → lane **D18**. |
| **D6 FC-3 CURVE-ON OVER-FIRE** | Four T1-H curve legs — the **capacity-market** ISOs (PJM/MISO/CAISO/NEISO), curve-ON | **QUEUED — STILL UNCHARTERED** (needs a pack section before it can be dispatched) | — | Fable | §0s.4. RE-SCOPED: it is NOT the vehicle for the ERCOT post-arming measurement (ERCOT is curve-OFF). D3 partly illuminates its MISO half. |
| **D4-M ERCOT POST-ARMING T1-H** | Grade D4-I3's frozen P-1..P-8 on the first T1-H at the armed D12-A posture; R-4 instrument grain first | **LANDED** PR #4481 — posture measured as **FOUR levers not two** (R-A armed two storage fields after the pre-declaration froze; graded as written with that as a stated limit); **held on direction and every structural claim, missed LOW on every magnitude, no falsifier fired**; **composition beat volume** (built +2.7 % MORE and slack 65 % WORSE — wrong sign for a pure volume account); ERCOT retirements **0.000 GW vs 2.294 actual**; **R-5 upgraded to a demonstrated mechanism** | `claude/capx-d4m-ercot-t1h` | **Opus** | Execution of a spent pre-declaration. A worse I3 is the correct result and may not be repaired in-lane. |
| **D8-V FC-7 LEDGER COMPLETION** | Publish D8-RE's two stopped flips through each affected lane's re-verification; close PJM + MISO ledgers | **LANDED** PR #4483 — **the program's FIRST TWO CLEAN FC MAPS**: `neiso-t1f` + `nyiso-t1f` → PROMOTE, caveats `[]`; PJM ledger 1/0 ⇒ FC-7 CAVEAT→PASS, HOLD unchanged; MISO 4 entries/3 UNIDENTIFIED ⇒ stays CAVEAT, debt NAMED not attested; four byte-exact controls; stale gate text flagged to D19 | `claude/capx-d8v-fc7-ledger` | Fable | Two ISO determinations move (NEISO + NYISO → PROMOTE, empty caveats). Barred from the legacy-leg run_configs (D20). |
| **D17 / D17-R MISO NON-COAL EXIT CHANNEL** | Why the economic screen executes ZERO gas_ct/gas_cc/oil exits vs 3.458 GW actual — Phase 0, zero-solve, precommit-first | **LANDED on relaunch** PRs #4487/#4494 — outcome **(B) requirement/cap-side**, thread (iii) CONFIRMED-PRIMARY: gas/oil fail the bar en masse then hit the admission cap (`entry_capped` 93.0 GW 2023 / 105.5 GW 2024); the corrected S-123 basis is worth **≈14.7 GW of headroom, 3.7–4.3× the whole missing-exit target**, and **the repair is ALREADY SHIPPED at HEAD** — routed PRIMARY is a HEAD re-measure (→ D27). Contributing cause with the OPPOSITE sign to the charter's thread (i): the bar under-rewards ~118.5 of 142.6 GW of thermal because capacity revenue pays **$0 at every long position** (→ D28) | `claude/capx-d17-miso-exit-channel` | Fable | D3's routed PRIMARY. Standing refusal: no FOM/threshold/lag identified from the retirement residual. |
| **D18 INVARIANT DECLARATION LEDGER** | Declare the 13 undeclared invariant FAILs; correct the misattributing `dominant_open_causes.I3`; make the standing-red CI job green | **LANDED** PR #4479 — census re-derived by running the checker at HEAD, matched exactly (13 runs / 15 idents); **14 of 15 cite a real record and CAISO's 2021 I7 is declared HONESTLY UNTRACKED** rather than fabricated; I3 cause line de-ERCOT'd (a duplicate session, PR #4480, carried no unique content) | `claude/capx-d18-invariant-ledger` | **Opus** | D4-I3's routed R-6. Census re-derived independently by the director. |
| **D19 BOARD RECONCILE 2** | The six stale cross-ISO board facts | **LANDED** PR #4492 — records only, **zero gate-leg status moves by the lane**, byte-identity asserted programmatically; absorbed a mid-session collision correctly by keeping the audit programme's own gate-(a) ERCOT flip (owner ruling R-I) VERBATIM and reconciling its remainder rather than re-deciding it | `claude/capx-d19-board-reconcile-2` | Fable | §0s.5. Reconcile to a settled board, not one being written under it (D13 precedent). |
| **D20 RECONSTRUCTED RUN_CONFIG PROVENANCE** | Scorer recognises `provenance: "reconstruction"`, CAVEAT never PASS, on the seven legacy legs | **LANDED** PR #4536 — seven legs re-emitted **FC-7 FAIL → CAVEAT, determinations unchanged**, control-first held | `claude/capx-d20-reconstruction-provenance-7amx23` | **Opus** | §0x.1. §0s.5 executed; the only route past CAVEAT on those legs is a genuine re-run, a charter decision. |
| **D26 FC-6 P1 ARM CONSTRUCTION** | Repair the paired-arm construction so P1 measures the model rather than its own premise; re-score `neiso-t3` FC-6 under the cross-lane re-grade rule | **LANDED IN FULL** PRs #4520 + #4522 — `carbon_price_delta` in (default-0 no-op proven, rule 28 discharged), base-arm control reproduced the golden EXACTLY, then the lane's own session ran the arms: **P1 FAIL → PASS on the repaired arm; neiso-t3 FC-6 FAIL → CAVEAT; HOLD unchanged.** The D21 FAIL did not survive the instrument repair — the carbon alarm is closed at every layer | `claude/capx-d26-p1-carbon-arm-t641px` | Fable | §0w.1 + amendment 1. The r#20/21 lesson executed right: graded checkpoint, not lost; finished on its own. |
| **D26-S FC-6 ARM SOLVES + RE-SCORE** | Execute the D26 finding's committed runbook | **RETIRED UNRUN** — D26's own session completed the owed half (PR #4522) before D26-S was dispatched | `claude/capx-d26s-arm-solves` | **Opus** | §0w amendment 1. Pack section annotated retired; nothing double-run. |
| **D27 MISO T1-H HEAD RE-MEASURE** | D17-R's routed PRIMARY: re-solve the MISO T1-H leg at HEAD, where the S-123 requirement repair is already shipped, against D17's quantified ≈14.7 GW expectation | **LANDED** PRs #4512/#4519 — **arithmetic VINDICATED to the decimal, remedy REFUTED: coal ate all of it** (exits 11.9→25.6 GW 100 % coal, +106.3 % vs actual; non-coal still 0.000 GW); G3 sign flips −27.7 %→+52.2 %, false_retire PASS→FAIL; the SELECTOR is `_apply_reliability_floor`'s cheapest-firm-per-MW retention key; `miso-t1h` re-registered preserve-then-overwrite, FC-7 FAIL→CAVEAT | `claude/capx-d27-miso-t1h-remeasure-9z817j` | **Opus** | §0w.1. Routes: R2 → D31 (primary lever), R5 → D32 (queued). Pre-declaration graded at full magnitude, misses included. |
| **D28 CAPACITY REVENUE AT LONG POSITIONS** | MISO's RBDC and NEISO's FCA curve BOTH pay $0 exactly where the model sits, while real PRA/FCA auctions cleared positive — one shape of error, two independently-derived curves | **LANDED** PR #4511 — the curves are **published-faithful** (one MISO exception); the object decomposes into a **POSITION defect** (model 6–22 reserve-ratio pts LONGER than real cleared positions) + the **clearing half** (curve evaluated at a census quantity where real markets clear supply against it); census 2 confirmed / 1 hindcast-confirmed / 1 latent (NYISO curve-ON +123 % = D6's evidence) | `claude/capx-d28-longposition-capacity-revenue-pnd1pc` | Fable | §0w.1. Routes: R1 → D31 · R2 → D33 · R3 queued jointly with D6. Rule-14 block explicit: every faithful repair moves the exit residual the WRONG way. |
| **D31 MISO CAPACITY-REVENUE REPAIR** | D27-R2/D28-R1: the PRA position audit + published RBDC shape, Q24-funded | **LANDED** PRs #4581–#4589 — the 0.8546 supply-accounting wedge measured (new gated `supply_accounting_ratio`, rule 28 discharged); RBDC published shape validated −0.4 %; **exit residual +52.2 % OVER → −74.3 % UNDER on faithful inputs** (rule 14's signature; error localized to the margin side) | `claude/capx-d31-miso-caprev-repair-xpzmx3` | Fable | §0z.1. Routes: D32 keeps the non-coal channel; SAC intake filed as an owner option. |
| **D32 FLOOR-RETENTION COMPOSITION MONOPOLY** | D27's R5 / D31's residual owner | **LANDED** PR #4605 — post-repair the floor decides **100 % of exit composition**; no per-unit identification in the cross-fuel key; the within-fuel tie-break NEVER fires (float-noise defect, disclosed); selection **indistinguishable from random** vs the real cohort; the one discriminating published driver is the filed retirement date the fossil channel no-ops → **Q29 → D42** | `claude/capx-d32-floor-retention-jbfyp1` | Fable | §0aa.1. Rule 21 held: no weight tuned, the dead end routed to a posture decision. |
| **D33 NEISO POSITION LANE** | D28's R2: accreditation basis + cleared-vs-qualified | **LANDED** PR #4569 — accreditation basis (approximately) PUBLISHED-FAITHFUL; **the +21/+6/+7 is a REQUIREMENT-DENOMINATOR VINTAGE artifact** (published per-CCP Net ICRs already in-repo); census supply actually SHORT of real cleared | `claude/capx-d33-neiso-position-8e9nzk` | Fable | §0z.1. Routes R-A/R-B → D40 (rule-28 duties, default-off, LOYO before any keeper moves). |
| **T3-NEISO-GOLDEN-2 (second §2.1b campaign)** | Owner ruling Q25: NEISO BAU 2026–2050 at HEAD with the R-A-armed storage posture, its own FC-6 battery at its own vintage, full-rubric scoring, preserve-then-overwrite | **REGISTERED** PRs #4532/#4543/#4546/#4548 (session still open at r#27 — surfaces reserved) — **HOLD; FC-7 PASSES (first golden ever); FC-6 FAIL on the NEW P2 only (P1 PASSES natively, −14.7 % CO₂ under +$25/t)**; storage: 720 MW iron-air at 2050, NOTHING 2026–2049 — the −56.2 % divergence family SURVIVES arming; 35.1 min/3.48 GB, DOF 7/0, FC-5 re-dispositioned 54/0. **Q25 SPENT** | `claude/capx-t3-golden-2-tm9eiy` | **Fable** | §0x.1. Four routed items → D36 (issued) · D35/D37 (queued) · a D33 cross-read. |
| **D35 P2 INSTRUMENT SCOPE** | Re-scope the FC-6 P2 gas leg | **LANDED** PR #4574 — re-scoped to **the model's gas partition**, pre-statement before the repaired checker, artifact-only re-score; **FC-6 LEAVES the neiso-t3 FAIL set** (HOLD on {FC-1..FC-4}; FC-5 + FC-6 both CAVEATs) | `claude/capx-d35-p2-scope-b5x2by` | **Fable** | §0z.1. Both t3 instruments now fully scored, neither blocking. |
| **D36 STORAGE VALUE-STACK TIMING** | GOLDEN-2 routed item 1 (the D25 §6.3 route): why the armed economics clear NOTHING before 2050 | **LANDED** PR #4559 — **the ARBITRAGE leg is short in EVERY year by $50–150/kW-yr; the RA leg is second-order and IS the D28/D33 position object** (two mechanisms, one seam); three rule-13 routes + the procurement-channel DISPOSITION; zero solves | `claude/capx-d36-storage-valuestack-gmelow` | **Fable** | §0y.1. Routes → D38 (records), D39 (named), D37 precondition (`entry_screen_diagnostics`). |
| **D38 D36-ROUTED RECORDS** | The corridor-row re-author + golden-2 annotation | **LANDED** PR #4568 — rows re-authored (no category/verdict moved), annotation in, staleness check + blob verification recorded | `claude/capx-d38-records-wfzdfx` | **Opus** | §0z.1. Done. |
| **D39 ENTRY-STACK UNDER-BUILD** | T16-A + D36 convergence | **LANDED** PRs #4599/#4604 — **ONE term: the energy leg's DISPERSION, discarded by the shared zone-flat tail-free stack re-price**; attribute leg EXACT (REC duals at ACP everywhere); capacity leg errs through POSITION (the D28-chain's, not the signal's); VRE volumes CAP-set (the signal moves timing + storage, never RPS volume). CAISO-first routing → **D43** | `claude/capx-d39-entry-underbuild-u198yd` | Fable | §0aa.1. The `entry_screen_diagnostics` precondition rides every next solve. |
| **D40 NEISO REQUIREMENT DEVINTAGE** | D33's R-A/R-B on the published Net ICR series | **LANDED** PR #4603 — BUILT default-off, LOYO-scored: **+21.4 → −2.1 pts at the clean 2023 entry**, residual flips to the predicted SHORT side; post-wave years unscoreable until D37; arming recommendation honored → **Q28** | `claude/capx-d40-neiso-devintage-4spxmd` | **Fable** | §0aa.1. Armed for D37's measurement only; default stays off. |
| **D41 CCS FIXED-COST RE-IDENTIFICATION** | D30's two defective legs re-identified on ATB-2024 | **LANDED** PR #4602 — both legs cited, dollar-year stated, needs-citation cleared; **the 45Q-only retrofit STOPS clearing where carbon is zero** — the PJM/MISO CCS wave was the two constants | `claude/capx-d41-ccs-fixedcost-cnlj5r` | **Opus** | §0aa.1. Stale-bundle re-measures batched as one future owner-cost item. |
| **D33-M MISO ADDITIONS REPAIR (label collision; not this desk's charter)** | A lane reusing the "D33" label executed the MISO additions-under-build repair (D31's routed FC-3 upstream object): coverage audit + siting identification, pre-declared solve, miso-t1h re-registered (third time, preserve-then-overwrite held), **the exit side a measured NULL amending D31 §7**, matrix stamped | **LANDED** PRs #4596/#4606 | `claude/capx-d33-miso-additions-repair-tr8yhp` | — | §0aa.1. Graded by content; cited by branch+PRs, never bare label — the NEISO D33 is a different lane. |
| **D42 FOSSIL ANNOUNCED-DATE A/B (Q29)** | The posture measurement | **LANDED** PRs #4618/#4626 — **recall 5/19 → 16/19; every non-coal class opens; ZERO screen displacement; deferral countered per-unit by published re-filings**; residual = the undated cohort + Dec-2026 roll; I4 accounting fixed; a new shared-key case DISCLOSED (census 15→16) | `claude/capx-d42-fossil-dates-ab-9p7erp` | **Fable** | §0ab.1. **→ Q30 ARM AS DEFAULT → D44.** |
| **D43 CAISO DISPERSION A/B (D39 §7)** | The single-term isolation | **LANDED** PRs #4622–#4627 — construction VALIDATED at both grains and **DECISION-INERT on the T1-H: the discarded dispersion is dispersion the LP never priced** — the under-build is upstream of the screen, at the model-class wall (the C3c/gain family); CAISO cell **I**; mechanism shipped gated default-off with full rule-28 duties | `claude/capx-d43-caiso-dispersion-1dfacx` | **Fable** | §0ab.1. Per-ISO siblings queued-named at LOW EV; PJM/NYISO preconditions folded into D45. |
| **D44 FOSSIL-DATES DEFAULT ARM (Q30)** | Flip the D42 channel default-on; amend spec §5.1 + CLAUDE.md step-1; matrix re-stamp; CHANGELOG | **LANDED** PR #4639 (`57088c33`) — default flipped, CLAUDE.md/spec/matrix/CHANGELOG amended, cache pins advanced by design (b′-1's first flip); plus the harness pin + four test assertions that would have made the flip inert, both repaired and reported. *(Graded NOT LANDED at r#32's pin `c73f78f5`; landed post-pin — §0ac amendment 1.)* | `claude/capx-d44-fossil-dates-arm` | **Opus** | Ruled + mechanical, but CLAUDE.md and the spec are core files — rule 27 is the charter's spine. The b′-1 declared-defaults ledger gets the flip's dated line. |
| **D45 — THE D6+R3 JOINT CHARTER (once-only)** | PJM + NYISO: first diagnostics-on T1-H solves at live posture; the NYISO curve-ON latent (+123 %, flat $110 over-pays 2–6×) adjudicated; the census-vs-cleared evaluation quantity per ISO (MISO/NEISO patterns as worked examples, own parameters per rule 25) | **CLOSED by D45-R (r#34) — the once-only question RETIRED**; D45 itself died after L1 (Q33). PRs #4643/#4647/#4649 — PJM L1 registered as bare `pjm-t1h` (HOLD; FC-3 FAIL, FC-7 CAVEAT; pre-D45 record preserved); **PJM's $0-at-position is a BASIS artifact (2–4 pts past the zero-cross on the auction's own UCAP basis) and the curve-ON over-fire does NOT survive the market's own price (13.0 of 18.1 GW of 2022 coal would pass at $15–21/kW-yr)**; no PJM default moves. **OWED: NYISO L2/L3, PJM L4, finding §4–§9 (placeholders on main); the §9 close-out is unwritten, so the once-only question is NOT yet retired.** All legs pre-D44 posture. | `claude/capx-d45-pjm-nyiso-curves` | **Fable** | The once-only cross-ISO clearing-half charter, written against what actually remains after the D31/D40 chain. D28's latent row is the D6 evidence base. |
| **D46 RE-MEASURE BATCH (Q32, staged)** | Baseline refresh of every forecast bundle stale on the Q30/D41/keeper-vintage axes; Stage 1 now (ERCOT/CAISO/MISO/NEISO t1h + GOLDEN-2 + pairable t1f), Stage 2 gated on D45's close-out, Stage 3 owner-scheduled (PJM/MISO t1f) | **STAGE 1 LANDED IN FULL** PRs #4661/#4668 — 8/8 pre-declared cache keys realized; the dates flip RE-ROUTES exits with a per-ISO sign (MISO recall FAIL→PASS; NEISO recall WORSE; ERCOT a window null that still worsened a row); GOLDEN-3 ends NEISO's CCS wave nine years early; t1f cost estimates 7–10× too high; no determination moved; re-dispatch correctly refused re-execution. **Stage 2 PENDING on D45's close-out; Stage 3 re-priced (card C-6).** `caiso-t1h/t1f` RE-OPENED by caiso-241. | `claude/capx-d46-remeasure-batch-oe1h77` (+ `-ofmvb8` re-dispatch) | **Opus** | §0ad.1. Routed: GOLDEN-3 attestation → D47; NEISO re-routing + ERCOT CCS queued-named LOW EV. |
| **D47 GOLDEN-3 ATTESTATION + D46 RECORDS** | Pre-declared attestation for the committed GOLDEN-3 bundle (FC-7 restored, no re-solve); the `-pre-d46` like-for-like table; the `neiso-t1h` posture disclosure | **ISSUED r#33** | `claude/capx-d47-golden3-attestation` | **Opus** | **LANDED** PRs #4691/#4699 (+ D47b): FC-7 restored by a pre-declared attestation (one row moved, HOLD unchanged); two `-pre-d46` baselines carry more axes than recorded; c_cost corrected (D46's 7–10× span-confounded; D45-R then measured 28/65 min). Routed items 2/4 → D51 rider, item 3 → card C-8. | §0ae.1. |
| **D45-R — D45 CLOSE-OUT + D46 STAGES 2/3 (Q33/Q35)** | The owed D45 legs at HEAD (NYISO L2 → bare `nyiso-t1h`, L3 curve-ON probe, PJM L1 replay → bare `pjm-t1h`, PJM L4 control), §4–§9 + the §9 close-out; plus NYISO/PJM/MISO t1f and the NEISO default-posture t1h | **ISSUED r#33** | `claude/capx-d45r-pjm-nyiso-close` | **Fable** | **LANDED — COMPLETE** PRs #4690/#4697/#4708: §4–§9 filled, §9 close-out written; 8/8 keys; NYISO curve-ON fires +189 % and is a POSITION artifact (requirement on the wrong peak basis + locality unrepresented) → DO NOT ARM; PJM no default moves; six bare keys current, priors at `-pre-d45r`; PJM t1f 28 min / MISO 65 min; leg 8 STOP-routed correctly (CAISO keys unchanged). **Leg 7 (NEISO dates-OFF control) pre-declared, NOT RUN — card C-7.** | §0ae.1. |
| **D48 PJM ACCREDITATION DEVINTAGE (D45 §2.3 items 1–2)** | UCAP (1 − EFORd) + published pre-CIFP FPR for DY ≤ 2024/25, ELCC-class + post-CIFP FPR from 2025/26; DR as counted supply — one vintage axis, zero free parameters, default-off; Phase 0 + pre-declaration now, A/B solve GATED on D45-R's PJM legs | **PHASE 0 LANDED (PR #4707); PHASE 1 LANDED (PRs #4716/#4718, `a1e72a99` — BEFORE the r#35 pin; graded one sitting late, §0ag.0)** — the accounting lands on the instrument to the MW, position +0.10/+0.26 pt, curve $0/$0/cap both arms, additions byte-identical; **FC-3 +1.403 GW of economic coal via the pipeline ADMISSION CAP** (a firm-MW budget ×1.25, the DR half +5.1 GW of it; 38 coal units re-ranked on per-unit EFORd); §5 (a) FAILS → **DO NOT ARM alone; arm WITH the clearing half**; `pjm-t1h-d48-devintage` HOLD | `claude/capx-d48-phase1-pjm-flfb0k` | **Fable** | §0ag.1. Routed: clearing half → D54 → **D57**; DR offered-vs-cleared probe pair + VRE ELCC limb queued-named. |
| **D49 TWO ZERO-SOLVE PHASE-0s ON THE D46 LEDGERS** | (1) why ERCOT clears 14 CCS retrofits / 2.7 GW at carbon = 0 where PJM/MISO clear none; (2) the MISO exit-side margin decomposition — is the −43.6 % under-retirement the D43 dispersion wall mirrored, or the bar? | **LANDED** PRs #4700/#4706 — half 1: a CONSTRUCTION SEAM (credit ∝ host CO2, capex flat per kW; D41 §4.3's zero-clearing never held at unit grain) → D50; half 2: NOT the D43 wall — the reserve POSITION netted twice (the 0.8546 ratio identified on a fleet still carrying the dated exits) → D51 | `claude/capx-d49-d46-phase0s-eaw7am` | **Fable** | §0ae.1. D49 §3: 'a term that should scale with the unit is held at a class constant, and a price object without a body supplies the hours.' |
| **D50 CCS CAPEX ∝ CAPTURED CO2 (D49 half 1)** | Scale the capture-island capex to the host's captured CO2 against the ATB reference host; CHP hosts excluded or rated electric-only; the p55470 row flagged — default-off, zero DOF; A/B on ERCOT/NEISO/PJM t1f; blast radius (every forecast cache key) measured before any flip | **CHECKPOINT** PR #4728 — `ccs_retrofit_capex_co2_scaling` built default-off + seam 2 + the p55470 flag; **ERCOT arm: 0 conversions vs 2,741.8 MW** (HOLD → HOLD); **NEISO arm: the 3 GW/yr cap still binds under RGGI** (who converts changes: CHP rows gone, 0.608 → 0.550 t/MWh; PROMOTE → PROMOTE). **OWED: the PJM arm, the blast radius, the arming recommendation, and `FINDING-capx-d50-2026-09-04.md` — cited by name in three shards, absent on main** → **D50-R** | `claude/capx-d50-ccs-capex-scaling-hkwpbe` | **Fable** | §0ag.1. Nothing arms until the finding exists. |
| **D51 MISO ACCOUNTING-RATIO RE-IDENTIFICATION (D49 half 2)** | Re-identify `ADEQUACY_INTERNAL_SUPPLY_ACCOUNTING_RATIO_BY_ISO['MISO']` net of the dated exits on the same PRA overlap years (rule 23: the posture changed the fleet it was identified on); A/B on `miso-t1h`; records rider (D47 items 2/4; oil-unscreened flag; leg 7 if C-7 says so) | **LANDED** PR #4729 — **0.8546 → 0.8934**, D31 reproduced to the decimal, one term moved; positions 1.0777/1.0194/0.9875 (2024 double-netting closed to 1.5 pts); PY2024 cliff crossed; cohort back in the floor-capped regime; 477.4 MW coal released at 1.1 % precision; BLK-10 gas_ct backstop stops firing; `miso-t1h-d51-ratio` HOLD. **Limbs (a)(b)(d) MET, (c) not met by the LETTER** → **card C-11**. **Rider (d) NEISO leg 7: P16 HIT, P17's counter-example limbs REFUTED — Q30 has no NEISO-side counter-example** (C-7 closed). Records rider done (Q37 rubric v1.1) | `claude/capx-d51-miso-ratio-rc83dw` | **Opus** | §0ag.1. Routed: admission-cap horizon headroom; backstop-after-storage; 2023/2025 ledger positions not reconstructing (queued-named); oil unscreened after 2022. |
| **D52 NYISO ADEQUACY DEVINTAGE (D45 §5.2.4 items 1–2)** | Requirement on the NYSRC ICAP-market FORECAST peak (Table D.2) + per-capability-year adopted IRM/derate — default-off, zero DOF; A/B on `nyiso-t1h`; then the L3 curve-ON probe re-run ONLY if the position lands within ±3 pts (the §6 re-open condition) | **LANDED** PR #4730 — requirement = Table D.2 to <1 MW; **positions +9.4/+5.2/+7.3 → −2.6/−1.8/−0.6 pts**, LOYO 3/3, **FC-3 byte-identical at the default**; D45 §5.2 corrected (screens priced 2.1–3.6 GW under the published bar every year); **curve-ON probe RAN: P9 (c) YES/(a) NO/(b) NO → curve stays OFF**; the over-fire relocates to the 2025/26 vintage ($28.65 vs market $51.36; Zone J $141) — the LOCALITY half. Recommends **ARM BOTH requirement gates** → **card C-12**; `nyiso-t1h-d52-devintage` + `-curveon` HOLD | `claude/capx-d52-nyiso-devintage-sl3rj2` | **Fable** | §0ag.1. Routes: locality → **D59**; the I7/I12 seam re-basing = a records lane, queued-named (director's call). |
| **D53 THE SECTOR GATE (D32 C5 / R3)** | Regulated-utility units (EIA-860 Sector 1) exit only via the instrument/filed-date channels; IPP/merchant units face the economic screen — a published per-unit partition, no weight; design doc first, then default-off build + A/B on `miso-t1h` (PJM gated on D48) | **LANDED (via #4766 + the branch's forced tip `107f8c79`) AND ARMED FOR MISO by in-lane owner instruction — Q43**: `_miso_config` override, bare `miso-t1h` → `c306ddc6d28c60c2` (the solved leg), D46 preserved at `miso-t1h-pre-d53`, MISO cell K, PJM untouched, t1f not re-solved. Graded at r#36 as: `retirement_sector_gate` default-off; bare-recipe arm reproduces D46 to the decimal; the failing census **76.75 → 17.46 GW with zero sector-1 rows**; the rider (gate + D51 ratio) fills the same 2022 headroom from the MERCHANT pool at **99.8 % plant-grain precision** (D51: 1.1 %), `false_retire` 0.0, recall 15/19; **all four limbs MET, recommendation ARM** — card when it lands. Two template tokens unfilled in finding §6 | `claude/capx-d53-sector-gate-redt3y` | **Fable** | §0ag.1. Routed: PJM leg → **D58**; additions mirror + CHP-host screen queued-named; harness HOLD-exit-code records item. |
| **D54 PJM CLEARING HALF — DESIGN (D45 §2.3 item 3)** | Clear the VRR curve against the fleet's net-ACR offer stack (Manual 18 §6 / MSOC) instead of evaluating it at the census; design + pre-declaration only; code and solve GATED on D48 landing | **LANDED** PR #4746 — the mechanism stated buildable without design choices, zero DOF; the zero-solve instrument puts the cleared position within **0.7/1.0/2.6 pts** of published and the price at **1.7×/2.4×/5.5×** — the CT/ST/oil E&AS operand is ZERO in the hindcast prices (~65 GW offered above the published price vs 9–20 GW uncleared); pre-declared as a MEASUREMENT of that operand; a build landing on the published price without an operand change is REFUSED. Seam list, arms A/B, seven STOPs written | `claude/capx-d54-pjm-clearing-design-fgpoog` | **Fable** | §0ag.1. Build → **D57**. D53 needs no design change (§4.7); NYISO is NOT this design (§4.9). |
| **D55 D32 R2 + R4 (correctness + diagnostic)** | Fix `_floor_retention_merit` key 1 to the class constant (float-noise defect: tie-breaks fire only within rounding buckets) + heterogeneous-pmax test; `plant_release_precision` in the reported block; A/B on `miso-t1h` to show cross-fuel composition unchanged and the within-coal release re-ordered | **LANDED** PR #4747 — repair exact, test added, scorer row shipped (13.5 % on D31); **`miso-t1h-d55-keyfix` byte-identical to D46** (the exhausted floor retains everything, so the order is unobservable on this recipe); replays show the fixed key releasing the CO2 tail where a floor did release; **stale-golden list EMPTY** (goldens are backcast captures — the charter's premise corrected) | `claude/capx-d55-retention-key-fix-xqrcfv` | **Opus** | §0ag.1. Routed: `co2_rate` in `pipeline_events` (ledger schema, queued-named). |
| **D56 NYISO `complete` RE-DECLARATION (Q38)** | Records lane: restore `complete.NYISO` on `2026-09-04-nyiso-188-combined` (keeper = keeper_at_declaration), determination re-verified artifact-only, withdrawn block preserved beneath, audit_keepers M1 PASS, gate-(a) row FAIL → PASS re-derived, board headline/gate_reading rewritten, byte-identity elsewhere | **NEVER LAUNCHED (r#36: no branch, no commit, marker unchanged) — and the keeper MOVED to nyiso-189 (CALIBRATED → CALIBRATED)** → re-issued as **D56-R** | `claude/capx-d56-nyiso-redeclaration` | **Fable** | §0ag.1. The charter's own STOP clause anticipated the move; the relaunch protocol restarts it fresh. |
| **D50-R D50 COMPLETION (PJM arm + blast radius + finding)** | The owed half of D50: `pjm-t1f-d50-ccscapex` (pre-declared 0 conversions vs 3,584.7 MW), the §6 blast radius (every key the flip advances + solve-minutes), the §8 arming recommendation, and `FINDING-capx-d50-2026-09-04.md` itself | **LANDED** PR #4768 — PJM 3,584.7 → **909.8 MW** (2028 closed; 2029 +157.7 = deferral, STOP 1 fired-and-diagnosed; the seam-3 price channel LIVE at 1.02–1.03× the bar); **MISO conditional leg 4,631 → 0 MW, capacity-identical**; blast radius: 7 bare keys, 4 already measured, residual **1.1 h**; fourth seam (ΔFOM/VOM) disclosed unbuilt; **ARM recommended → Q42 ARM** | `claude/capx-d50r-completion` | **Opus** | §0ag.3. Pre-declared execution; nothing arms. |
| **D56-R NYISO `complete` RE-DECLARATION on nyiso-189 (Q38 + C-10)** | D56's charter re-pointed at `2026-09-05-nyiso-189-steam-identity`; the frontier limb conditional on card C-10; R-AG/Q38 coexistence recorded in the finding | **LANDED** PR #4763 — `complete.NYISO` declared 2026-09-05 on nyiso-189, M1a/M1b PASS, validation tier re-authorized (nothing spent), gate (a) FAIL → PASS, guard 6/6, provenance re-stamped after its third rebase; **frontier NOT re-asserted (no Q39 at its pin) → Q39 ruled BOTH at r#37 → D56-R2** | `claude/capx-d56r-nyiso-redeclaration` | **Fable** | §0ag.3/§0ag.5. Records only; validation tier returns, nothing spent. |
| **D57 PJM CLEARING HALF — BUILD + A/B (D54 §7)** | `capacity_market_supply_clearing_by_iso` built to D54 §3/§7 (zero DOF), Phase-0 reproduction of the instrument, arms A (D48 ON + clearing ON) and B (clearing on HEAD basis) on `pjm-t1h`, seven STOPs, the E&AS operand measured | **LANDED + PROMOTED (Q44, in-session)** PRs #4761/#4775/#4786 — Phase 0 exact (0.000 $ / 0.000 pt); **cleared position within −0.5 / −1.0 / −2.8 pts of published; §3.5 identity holds in 8/8 screens; price 1.5–5.7× published — the CT/ST/oil E&AS operand is ZERO** (≥ 3.8 / 18.0 / 8.6 $/kW-yr per unit lands it); coal retained, gas-steam over-exits, HOLD both arms; 14 HIT / 4 SPLIT / 6 MISS. **JOINT PJM posture armed via `_pjm_config` overrides**; arm A = bare `pjm-t1h`; D45-R at `-pre-d57`; PJM cells K ×3; `pjm-t1f` left on a superseded posture → D60 | `claude/capx-d57-pjm-clearing-build` | **Fable** | §0ag.3. The D48 arming card is served on its result. |
| **D58 PJM SECTOR-GATE LEG (D53 item 1)** | `pjm-t1h-d58-sectorgate` vs the bare `pjm-t1h`: D45 L1's 111.7 GW 2022 failing pool on a merchant-heavy mix should shrink by a MINORITY; own census, own cell | **RELEASED (r#38): D53 merged ✓, D57 landed ✓ — dispatch AFTER D60 lands** (D60 writes the PJM board t1f row); control = the NEW bare `pjm-t1h` (the Q44 joint posture, key `f0e050e820c1159a`); Opus per R-AK | `claude/capx-d58-pjm-sectorgate` | **Opus** | §0ag.3. Confirmatory; pre-declared execution. |
| **D59 NYISO LOCALITY HALF (D45 §5.2.4 item 3 / D52 route)** | Design-first: the per-locality ICAP demand curves (NYC/LI/G-J) evaluated at the locality position on the committed LCR/import-limit rows — the SHORT-locality uplift the shipped Part-B gate does not carry; build default-off on the D52 posture; A/B on `nyiso-t1h`; then the SAME P9 probe re-run; the 2025/26 curve-vintage transcription check as a zero-solve step | **LANDED** PRs #4760/#4764 — `locality_capacity_curves` built (NYC/LI on their own published curves, §5.15.2 max, zero DOF, 15 tests); **A/B BYTE-IDENTICAL on every FC-3 row**: the model's NYC census sits +0.7–0.8 GW above the Gold Book, NYC reads 5–9 pts long, its curve pays BELOW NYCA; P9 one-of-three again → NYCA curve stays OFF; transcription check: intake exact, the 2025 SOM margin row a carry-over; **DO NOT ARM either (self-executing)**; cell **I** | `claude/capx-d59-nyiso-locality-3p7sju` | **Fable** | §0ah.1. Routed: the NYC census object → the owner's NYISO backcast track; the ARV annualization (CR-3) queued-named. |
| **D56-R2 NYISO FRONTIER RE-DECLARATION (Q39)** | Records lane: re-declare `frontier` on nyiso-189 in keepers/NYISO.json in the ERCOT/PJM/NEISO shape; marker `frontier_basis` names it; four-instrument alignment restored; byte-identity elsewhere | **LANDED** PR #4780 — frontier block live (prior ratification/reversion preserved beneath), `frontier_basis` rewritten with a WAS: clause, auditor PASS, guard 6/6 (no gate-(a) leaf moved), **all four instruments read {ERCOT, NEISO, NYISO, PJM}** | `claude/capx-d56r2-nyiso-frontier` | **Fable** | §0ah.3. Zero solves; nothing spent. |
| **D60 THE ARMING BATCH (Q40 + Q41 + Q42)** | Flip-first: `ccs_retrofit_capex_co2_scaling` default ON (b′-1 line), MISO `adequacy_accounting_ratio_dated_net` + NYISO `nyiso_requirement_forecast_peak` / `_vintage_factors` via `default_scenario_overrides`; every bare key pre-declared; t1h keys as documented byte-identical renames (priors preserved); `miso-t1f`, `nyiso-t1f`, `caiso-t1f`, `neiso-t3` RE-SOLVED with priors at `-pre-d60`; `ercot/neiso/pjm-t1f` = the D50 arms; board + shards + spec/CLAUDE.md/CHANGELOG | **RUNNING — legs 1–2 of 5 LANDED (r#39)**: flip commit + four renames (r#38); **`miso-t1f` re-solved** (the ratio moves the board: I12 +4 pts/yr, backstop −6.6 GW gas_ct, FC-2 row 4 FAIL → CAVEAT; sector gate moves nothing on exits, P18 vacuous; CCS null) · **`nyiso-t1f` re-solved — P10 STOP: PROMOTE → PROMOTE-WITH-CAVEATS on FC-7 alone (unattested rows), routed → Am.2 authorizes the Q37 attestation** · Addenda B/C pushed pre-solve · pending: `caiso-t1f`, `pjm-t1f` (Am.1, key `09996eca`), GOLDEN-3, finding §5 | `claude/capx-d60-arming-batch` | **Opus** | §0ah.3. ≈ 2.2 h sequential; first commit = ruff format on `new_entry.py` + the two nyiso-191 files. |
| **D60-R / D60-R2 THE D60 RELAUNCH** | The dead session's owed half: `caiso-t1f`, `pjm-t1f`, GOLDEN-3 re-solves with `-pre-d60` priors; Addendum D + the seven Q37 attestation rows + artifact-only re-scores; finding §5/§8 and close | **D60-R never launched; D60-R2 LAUNCHED + RUNNING (r#40, PR #4824)**: twin check clear, 17 keys unmoved across the nyiso-192 merge, Addendum D pushed before any row (six new (ISO, field) rows; D50's seventh dormant post-flip); two negatives pre-declared — `miso-t1f` FC-7 stays CAVEAT (five pre-batch overrides, outside Q37's limb → D63), CAISO's `negative_renewable_offers` caveat stays. Pending: legs 3–5, rows, re-scores, finding §5/§8 | `claude/capx-d60r2-completion` | **Opus** | §0aj am.1. D58 and the NYISO golden release on its landing. |
| **T3-NYISO-GOLDEN (the third §2.1b campaign; Q45)** | NYISO BAU 2026–2050 at HEAD on the armed posture (Q41 gates, Q42 CCS, D-5 frontier), its own FC-5 disposition table + FC-6 battery at its own vintage, registered `nyiso-t3`, full rubric | **HELD (r#40): Q46 landed — `complete.NYISO` WITHDRAWN, gate (a) FAIL; Amendment 1's precondition fails and Q45's premise has lapsed. Re-served only when a CALIBRATED NYISO keeper re-enters the marker** | `claude/capx-t3-nyiso-golden` | **Opus** (R-AK; pre-declared campaign) | §0ai.3. ~35–60 min / ~4 GB; the GOLDEN-2/3 recipe with NYISO's own registries. |
| **D64 THE D50 FOURTH SEAM — Phase 0 (CCS ΔFOM / capture VOM per captured tonne)** | Zero-solve: the published basis of the two fixed-cost legs, the zero-DOF construction, a re-screen of every committed post-Q42 CCS row (NEISO cap, PJM 2029's two converters), the blast radius, a D65 build charter or a 'no build' closure | **ISSUED r#40 ("issue prompts")** | `claude/capx-d64-ccs-fixedcost-seam` | **Fable** | §0ak am.1. Docs only; parallel-safe with D60-R2 and D61. |
| **D61 THE PJM CT/ST/OIL E&AS OPERAND — Phase 0 (D57 §4's successor)** | Zero-solve: which real revenue streams the hindcast price denies the CT / ST / oil fleets (reserves, uplift, black-start, reactive — vs the PJM SOM net-revenue tables as validation observables), whether the D12 scarcity-basis / reserve co-opt channel is the operand's home, the sign and size a faithful operand would carry into the D57 clearing, and a build charter — no coefficient (rule 21) | **ISSUED r#38** | `claude/capx-d61-pjm-eas-operand` | **Fable** | §0ai.4. The price ratio falling toward 1× WITHOUT a coefficient is the test D57 left. |
| **D37 NEISO T1-H AT ARMED POSTURE** | The armed re-measure + paired control (Q28) | **LANDED** PR #4619 — **post-wave years SCORE; armed positions +0.37/−3.26/+0.14 pts of the real FCAs** (control +21.13/−1.44/−5.34); FC-3 blind to the lever; retirements flip to −27 % under; storage 0.000 GW refutes its own headline by its own falsifier; **P9 flip condition FAILS → default stays OFF, self-executing** | `claude/capx-d37-neiso-t1h-armed-o98iy1` | **Opus** | §0ab.1. The position defect is closed at NEISO; the margin-side error is now the exposed object. |
| **T16-A T1.6 RE-POINT EXECUTION** | Owner ruling Q27: re-point T1.6 to `entry_rate_limits`, 2 rungs, artifact-only FC-6 re-score | **LANDED** PRs #4555/#4558 — **outcome B, the honesty clause FIRED**: REC dual at the $50 ACP ceiling in all 50 arm-years (VRE 4.1→37.1 GW), series constant, battery row **CAVEAT-measured**; the lever IS live (8/18 metrics move); no third lever tried; one leaf moves, no preserved key needed | `claude/capx-t16a-ladder-repoint-kk4vqy` | **Opus** | §0y.1. The RPS/ACP finding feeds D39. Q27 executed. |
| **D34 CARBON_PRICE BELOW-BASE GUARD** | Owner ruling Q26: replace semantics + the below-base forecast warning pointing at `carbon_price_delta` | **LANDED** PRs #4534/#4537 — guard in with A/B regression evidence recorded; R4 closed | `claude/capx-d34-carbonprice-guard-lfpeld` | **Opus** | §0x.1. Q26 executed. |
| **D23 P1 CARBON-CO2 SIGN FAILURE** | A carbon price RAISES cumulative CO2 +52.4 % — attribute the capacity-side and dispatch-side legs | **LANDED** PR #4490 — **NEITHER LEG IS A MODEL DEFECT; the model's sign is RIGHT in both.** `carbon_price` REPLACES the resolved signal, and NEISO's base already carries the RGGI projection ($26.05/t 2026 → $132.16/t 2050 at the published 7 %/yr CCR rate), so the `carbon25` arm **CUT** the carbon price in every year (−$1.05 → −$107.16). P1 measured the premise of its own pair. **This REFUTES the director's r#23 alarm** (§0u.1). Repairs instrument-side (→ D26) | `claude/capx-d23-p1-carbon-sign` | Fable | D21's routed object. P1 is the model's economic core; Phase-0, precommit-first, nothing tuned. |
| **D24 CACHE-KEY OPTIONAL FIELDS** | `cache_key()` drops `_CACHE_KEY_OPTIONAL_FIELDS` at the live default ⇒ one key, two dispatches across a default flip | **LANDED** PR #4496 — 4 flip events / 7 fields; **all 98 analyzable forecast records drop a flipped field**; two collision pairs (ERCOT `f061b264` the known-true positive found INDEPENDENTLY, + NEW NEISO `07e416f3`); **no cached result was ever served — all 99 runs used distinct roots, and that protection is the INCIDENTAL, UNDOCUMENTED per-run `--out-dir` convention**; D4-I3 §5.1's group narrowed OUT; four repairs priced ((c') = 0 keys, 0 invalidations), fix NOT landed → owner; **RULED Q20 at r#25 — (c′)+(b′-1), execution = D24-R** | `claude/capx-d24-cache-key-defect` | **Opus** | D4-M's R-5 upgrade. CHARACTERIZE AND PROPOSE ONLY — a fix invalidates caches program-wide, an owner cost decision. |
| **D24-R CACHE-KEY REPAIR (Q20 execution)** | Land (c′) — the `is_cached` config-equality refusal — and (b′-1) — the declared-defaults append-only drop comparison; zero keys move, zero caches invalidated, and the zero-key-move assertion is the lane's own merge gate | **LANDED** PR #4514 — both changes in, zero keys moved (assertion committed), tests + blob verification recorded; **the cache-key defect is closed forward**, the two historical pairs stay provenance-only as ruled | `claude/capx-d24r-cachekey-repair-hjz6un` | **Opus** | §0w.1. Q20 execution complete. |
| **D29 TRAJECTORY REPORTING GRAIN** | D25 §6.1 routed: `extract_trajectory` gains generation-by-fuel + a REAL storage column (today `storage_mw` reads `cap.get("storage")` over generator fuels — 0.0 by construction even for a 17 GW battery fleet); unblocks the 252 energy-mix corridor anchors for future runs | **LANDED** PR #4513 — the grain is in, additive, zero solves; D25 §6.1's route CLOSED | `claude/capx-d29-trajectory-grain-oi7yk7` | **Opus** | §0w.1. Future full-horizon bundles carry the energy-mix family. |
| **D30 45Q CONVERSION PACE** | D25 §6.4: is cap-saturated conversion intended? | **LANDED** PR #4565 — **DEFECT-CANDIDATE on the two FIXED-COST legs, not 45Q**: `fixed_om_gas_cc_ccs` 25 < host's 30 post-G-32 (retrofit PAID $5,000/MW-yr in fixed savings) and `ccs_retrofit_capex_kw` 900 needs-citation at 59 % of the model's own ATB-2024 increment; the mechanism itself is the intended reading, the cap binds everywhere | `claude/capx-d30-45q-pace-8udm1m` | **Fable** | §0z.1. Repair → D41 (re-identify from the ATB basis, rule 23). |
| **D25 FC-5 DISPOSITION TABLE** | Author the per-row disposition table so FC-5 can score at all — the t3 ceiling's last step | **LANDED** PR #4500 — **THE t3 CEILING IS LIFTED**: 78 rows, 37 IN CORRIDOR / 41 EXPLAINED / **0 UNEXPLAINED**, five keys FC-5 SKIPPED → CAVEAT, no determination moves, nothing on `neiso-t3` reads SKIPPED-required. §5 **adversarially audits its own zero-UNEXPLAINED count**; rebuilt mid-session on the landing batch, absorbing D19's board writes and D23's re-attribution before pushing | `claude/capx-d25-fc5-dispositions` | Fable | Judgment work, not intake. Divergence is not failure; UNEXPLAINED divergence is. Benchmarks are context, never fit targets. |
| **D21 FC-6 DRIVER BATTERY (t3 ceiling, half 1)** | Run the Tier-1 monotonicity battery + paired P1–P3 at the golden's config vintage, commit the machine output, re-score `neiso-t3`'s FC-6 | **LANDED** PRs #4477/#4478 — **FC-6 grades, and FAILs**: NEISO's whole 2-rung ladder is **VACUOUS** (`renewable_buildout_pace` is consumed by no model code) ⇒ CAVEAT; **paired P1 FAILS — cumulative CO2 RISES 210.52 → 320.84 Mt (+52.4 %) under carbon_price=25**; determination HOLD. Also repaired `_annual_co2_tons` (P1 could not score ANY forecast bundle), implemented FC-6.2, and **self-caught a data-vintage leak** and re-ran from the golden's own raw bytes | `claude/capx-d21-fc6-battery` | Fable | Q16/Q19 execution. Price the ladder BEFORE running it; a vacuous pass is a CAVEAT, never a PASS. |
| **D22 FC-5 BENCHMARK CORRIDOR (t3 ceiling, half 2)** | The `benchmark-corridor` curated datatype + the rubric §6 eight-source intake — **data contract and intake ONLY, no scorer edit** | **LANDED** PR #4476 — root cause: **FF-0F gitignored BOTH ends of the raw→clean chain**, so the loader's "regenerated from committed raw" was untrue. AEO2025 committed + fetch made key-free (28→6 requests) + truncation refused; ERCOT CDR + PJM Load Forecast machine-extracted; **1,025 rows / 3 sources, missing list 7→5**; StdScen2024 unreachable by egress policy. **FC-5 still SKIPs pending an authored disposition table — by design** (→ D25) | `claude/capx-d22-fc5-corridor` | **Opus** | Q16/Q19 execution. Benchmarks are context, never fit targets (rule 13). The no-scorer-edit boundary is what keeps it clear of D8-V's live re-scores. |
| **D8 FORECAST PROVENANCE DEBT + DOF LEDGER** | FC-7's two halves: the DOF-ledger instrument (every T1-F leg's caveat — NEISO's ONLY one) + the seven legacy legs' missing `run_config.json` | **LANDED r#21** (PR #4427) + **D8-RE LANDED r#22** (PR #4457): one key re-emitted, **two committed-verdict flips STOPPED and routed** under the cross-lane re-grade rule (`neiso-t1f`/`nyiso-t1f` → PROMOTE, empty caveats), PJM/MISO ledgers measured read-only | `claude/capx-d8-dof-ledger` → `claude/capx-d8-re-emission` | Fable→Opus | §0p.2 + §0r.6. The instrument is what stands between the program's best ISO and a clean FC map. |
| **D9 MISO SOCO FORECAST FALLBACK** | `ba_code="SOCO"` live only in the forecast path | **ADJUDICATED UNREACHABLE at HEAD, ROUTED** (S-123 finding §5 — TVA re-point + data prerequisite named) | — | Fable | Handed in by miso-183; closed as a lane, lives on as a routed intake item. |
| **D16 ARMED-INTERFACE mc=0 SEAM** | Armed-interface forecast years leave seam rows at their mc=0 build placeholder (S-123 finding §5/§7-5) | **ISSUED r#19** — director mechanism decision: FAIL CLOSED (hard refusal, holdout_policy pattern); fallback-price alternative deliberately not built without its own charter | `claude/capx-d16-seam-guard` | Fable | §0p.2. New defect found on the D9 trace, routed to this track 2026-08-30. |
| **NEISO-RC-R REPAIR PHASE** | Execute the Phase-0 finding's routed repairs: R2 FCA-curve re-derivation + R1 registry intake + R3 scorer trio + R4 reporting; R5 deferred, R6 standing refusal; PREREG-first verification pair (one T1-X treatment vs the committed capxd14 control) | **LANDED IN FULL** PR #4467 (R1–R4 + Phase-B prereg + graded verification) — R2 curve leg MISSES (re-derived curve near-inert at the model's long positions), **Mystic-instrument leg HITS** (1,464 MW economic→confirmed, the derate half visible ONLY through R3(iii)), level ≈ control (confirmed exits displace the floor budget ~1:1), **dual basis +24.2 % over vs −27.3 % under**, recall 2/4, Merrimack decided in-window and reversed 2025; `neiso-t1x` re-registered preserve-then-overwrite, HOLD→HOLD, no verdict flipped | `claude/neiso-rc-repair-fymtkz` (NOT the charter stem) | Fable | §0s amendment A. **The branch-stem census is what missed this landing — grade by `--grep=<LANE-ID>` and merged PRs, never by branch name.** |
| **D2-REMEASURE** | — | **RETIRED unrun** | — | — | Premise refuted at refresh #4. |

## 2. Backcast-track watch (last seen 2026-09-05 @ `4d4dc6ce`, refresh #40)

| item | state |
|---|---|
| **NYISO (r#40)** | **KEEPER → `2026-09-05-nyiso-192-astoria-panel` (Q46, in-lane owner ruling, #4817)**: NOT-YET grade 6 / fails 2 (C1-2024 CC_REGULAR +3.68 TWh; C3c not lone); the D-5(b) stop fired and the owner chose the cost — **`complete` + `frontier` WITHDRAWN (third time: 07-19, 08-30, 09-05), gate (a) FAIL, validation tier lapses**; bundle restored after the cleanup's prune. **nyiso-194**: the owner-named CC_REGULAR duct-burner tranche lever — phase 0 measured, two 2024 screens pre-registered, **BOTH KILLED on frozen structural gates** (S-3, D-2); no full span spent; keeper unchanged. T3-NYISO-GOLDEN HELD. |
| **CAISO (r#40)** | Keeper unchanged at 251. **caiso-252** (zero-LP): the C4 2025 cell is CC_REGULAR's DIURNAL error (90–95 % of gas-fleet MSE), the mirror of the model's too-flat import diurnal shape; the caiso-251 degradation is Aug–Dec, 56 % CC / 59 % CT; the CT miss is ONE plant (Panoche, NP15); 7/10 predictions falsified. The import diurnal SHAPE joins the import LEVEL (caiso-244) as the live object. |
| **Governance (r#40)** | **Rule 15 retention → KEEPER-ONLY** (G-1; owner ruling R-AQ card K; `prune_iso_runs.py` at every registration; git history the record). |
| **Audit programme (r#40)** | **Y-9**: the branch-protection flip is the OWNER'S CLICK-PATH (API proxy-refused, no MCP protection tool); the R-AE path-filter glob misses `docs/handoffs/FINDING-*.md` (76 findings unenrolled — a post-flip deadlock risk, flagged). **Y-10**: 20 bench parts re-stamped at `b2f21b9a`; the flip set CLEARED (ruff green at the pin); a bench-fingerprint-narrowing PROPOSAL (three moves on 09-05, none reached a payload; 53 % of the hashed surface is comments) for the owner. |
| **CAISO (r#39)** | **KEEPER → `2026-09-05-caiso-251-b1-nomargin`** (#4814): the gas offer carried NEISO's functional form; removed, CT_PEAKER's fuel coupling returns to its OASIS-measured 0.9–1.0 (from 0.53); **C3a FAIL → PASS in all three years; C4 PASS → FAIL on one cell; NOT-YET, the failure drops a tier**; first promotion under rule 29's G-SCREEN (2024 first). A wrong DOF count corrected against interest (9/6 unchanged; "removes a free parameter" withdrawn). Gate-(a) re-keyed by the lane. Golden two promotions stale. |
| **MISO (r#39)** | **KEEPER → `2026-09-05-miso-217-intermphys`**: the `phys_*` coverage gap closed (38.5 GW / 58.4 % of gas capacity back on the armed offer-margin mechanism); NOT-YET C3a-2025 alone. Step 4 skipped → re-keyed by the cleanup lane. **miso-218** (owner-requested ×1.10 offer-level scale): premise held, C3a-2025 closes — and it is NOT a keeper by pre-commitment (a fitted level scalar; breaks C1 ST_GAS-2024; C8 over budget); probe pruned. Two ruff-format reds from miso-217/218 on main. |
| **NYISO (r#39)** | Keeper at 189 ON MAIN; **the open branch `nyiso-192-frontier-adjudication-mo2nrq` carries an in-lane owner ruling (nyiso192-Q1 → pending Q46): promote `2026-09-05-nyiso-192-astoria-panel` (NOT-YET, grade 6, C1-2024 CC_REGULAR +3.68 TWh) and WITHDRAW `complete` + `frontier` under the Q5 uniform rule; gate (a) → FAIL.** Next lever named by the owner: the CC_REGULAR duct-burner peaking-tranche offer (measured identification, rule-29 screen). nyiso-193 filed the NYC steam delivered-gas intake spec + a D-2 unit-grain scorer card. D60 leg 2 disclosed NYISO's confirmed-exit channel EMPTY AT SOURCE. |
| **ALL ISOs (r#39) — THE CLEANUP** | Owner-directed DELETE-not-archive: `scripts/archive` (292 files), 1,229 record-only probes, 21 dead scripts, dead `src/`; `results/calibration` → six keepers + ercot-248 constituents (allowlist emptied); forecast: 36 sidecars + 109 hindcast dirs deleted, **zero verdict keys lost, every `-pre-d*` prior intact**. A D57 `run_config.json` committed with conflict markers by #4795 repaired. |
| **Governance (r#39)** | **Rule 29 clause (b): NO CONTROL SOLVES** — the committed keeper is the control; **G-DRIFT** (zero-LP code audit of every changed hunk on the backcast path, INERT-with-reason or LIVE) replaces them; a LIVE hunk alone earns a control solve. 2022 ERCOT/NYISO measured inputs extended for the validation touchpoint (data only, nothing spent). DOCS-B finalized (spec, manual, CHANGELOG). |
| **Audit programme (r#39)** | **v29 + v30**: R-AL (flip "doing it now") · R-AM (G2 at the flip) · R-AN (R-V keeper freeze lifts at G2) · R-AO (Y-8 bench regen, executed #4803). **Flip NOT LIVE (`protected: false` ×5), G2 NOT declared, keeper freeze on {ERCOT, NEISO, PJM} STILL IN FORCE**; ERCOT's keeper field moved under it (ercot-248) — unadjudicated. Stage-0 corrected to 2 of 7. Y-1 red again on five ruff files. |
| **ALL ISOs (r#38) — OWNER DIRECTIVE, SITE PRUNED TO KEEPERS ONLY** | `prune_iso_runs.py --force-uncite` (session ercot-248): ERCOT 15, CAISO 11, PJM 4, MISO 14, NYISO 14, NEISO 3 runs off the site (sidecar + payload + bundle dir); golden-referenced / allowlisted bundles kept on disk; `site_retention_note` in all six shards; run-id citations may now point off-site (stated). Top-15 retention superseded by keeper-only "for now". 15 golden entries carry a pruned provenance run (survivable via `keeper_snapshot`). |
| **ERCOT (r#38)** | **KEEPER → `2026-09-05-ercot248-two-config-keeper`** — the two configs registered as ONE composite run (2023 from 236-swcap, 2024/25 from 234-eastex; byte-copied, zero solve; CALIBRATED on the full span and both designated spans); shard `config_partition` run ids, the marker (D-5(b) re-verified), the gate-(a) stamp (R-T honoured) and the matrix stamp all re-keyed in one change. Guard 6/6. |
| **Governance (r#38)** | **Rule 29 `[R-SCREEN]`** (owner, 2026-09-05): screen a new backcast config on ONE pre-named year before the full span; structural STOP gate only; rule 16 untouched. Every backcast prompt this desk offers cites it. |
| **NYISO (r#38)** | Keeper unchanged at 189; **frontier RE-DECLARED (D56-R2, Q39)**. **nyiso-192**: the payload's CHP add-back instrument defect (35 % default vs the LP's measured hold-out) inflated the CC_CHP object three-fold — repaired, payload re-rendered; the Astoria merit-panel stack-duplicate defect measured (not Astoria-only) and A/B-armed as the one arm; `nyiso192_astoria_panel` = a parity-red checkpoint. |
| **MISO (r#38)** | Keeper unchanged at 213. **miso-215**: `phys_*` coverage gap real (58.4 % of assembled gas capacity), borrowing valid 9/9, arm adverse where it has magnitude → no A/B. **miso-216**: the gas-offer margin anchor's grain — no grain dominates, ≥ 87.8 % of the distortion is the fixed-margin FORM's; **NO CHANGE** recommended; CT_PEAKER −$10–20 bias on the packet's face. **miso-217**: the `phys_*` arm + scorer built blind (two ruff-format reds left on main). Forecast: sector gate + ratio armed (Q43/Q40). |
| **CAISO (r#38)** | Keeper unchanged at 246. **caiso-250**: the STORAGE cell is mostly caiso-168's adjudicated belly object (44–60 % inside its mask; Pacific 07–08 carries 9–24 % of the whole gap); HYDRO REFUTED as carrier. **caiso-251**: the gas-offer fuel-coupling form pre-registered; G-COUPLE PASSES (the armed fixed-margin form under-couples CT to half its fuel sensitivity); `caiso251_ctrl` = a parity-red checkpoint; branch `caiso-250-…-7tci3e` open. |
| **Audit programme (r#38)** | **v28 + v28b**: R-AH (flip on first 6-of-6 head) · R-AI (hold re-captures to the 09-07 clocks) · R-AJ (golden-tier CI proof then declare leg 1; R-V freeze question next) · R-AK (Opus for records/capture/small-repair lanes) — recorded three hours late, against interest; Z-4 CLOSED; X-6b first leg discharged; Y-7 formatted the six r#37 reds. **R-AK ADOPTED by this desk** (§0ai.2). |
| **NYISO (r#37)** | Keeper unchanged at nyiso-189. **nyiso-190**: the keeper's unmeasured justifying clause measured and REFUTED (keeper stands on its measured record). **nyiso-191**: `cc_capacity_reconcile` CC_CHP scope extension TESTED and REJECTED on rule 19 (artifact reverted). **`complete` RE-DECLARED (D56-R); frontier follows (Q39 → D56-R2).** D59 hands the backcast track the NYC census object: the model's NYC ICAP census sits +0.7–0.8 GW above the Gold Book Zone-J capability (the 2023-24 Peaker-Rule exit set the 2020-vintage fleet still carries). Stage-0 golden STALE vs 189. |
| **MISO (r#37)** | Keeper unchanged at miso-213. **miso-214** (zero solve): 62–70 % of the missed CT energy was produced BELOW the plant's own delivered cost at the market's price — unreachable by any price/offer mechanism; K-d fires, no A/B; an offer-form coverage gap named for miso-215. Forecast side: the sector gate ARMED for MISO (Q43); the ratio arms next (Q40, D60). |
| **CAISO (r#37)** | Keeper unchanged at caiso-246. **caiso-247**: the C3a residual is NOT hub-basis (4.0 / 3.6 % of the gap; the acquittal falsifier fires). **caiso-248 STOP-THE-LINE, against interest**: caiso-247's fleet rebuild carried 184 phantom biomass LP units (`inject_biomass_mustrun` from `solve_and_persist` locals, absent from `meta.json`, invisible to `run_year_kwargs`) — the BIOMASS headline WITHDRAWN, results 1–2 bit-identical and standing. **caiso-249**: the STORAGE bucket (43 / 55 % of the gap) is NOT a loss-surface artifact — no thermal unit marginal, price set by inter-temporal duals; the DOM_GAS/STORAGE split unquotable. |
| **CAISO (r#36)** | **KEEPER → `2026-09-05-caiso-246-b1-spot`** (#4751): the 2025 hub-overlay coverage gap was a GATE ARTIFACT; the arm covers Sep–Nov 2025 on the measured daily spot, the F923 fallback retired from the training window (0 reachable months in 36), three of six post-solve predictions falsified at full size; NOT-YET on C3a alone (2024 +12.3 / 2025 +11.4 %). **Re-keyed its own gate-(a) stamp** — the first CAISO promotion since R-T to carry step 4. caiso-245 (zero LP): the published RA-import allocations carry NO north over-import (the stop rule fired; the object → "RA import CAPABILITY forced as ENERGY"); its intake left the `test_clean_io` roster stale (repaired by this desk, §0ag.4). Stage-0 golden STALE vs 246. |
| **MISO (r#36)** | **KEEPER → `2026-09-05-miso-213-layering`** (#4748): the zonal basis was redundant on 923-priced cells; one default-off field, single-delta A/B vs the keeper, every kill silent, six object gates South→North; NOT-YET C3a-2025 alone (−12.38 → −11.75 %). **Stamp NOT re-keyed → ninth promoter miss; re-keyed here (eleventh firing).** Stage-0 golden STALE vs 213. |
| **NYISO (r#36)** | **KEEPER → `2026-09-05-nyiso-189-steam-identity`** (#4743): the owner's Bethlehem form B2 (`egrid_steam_collapse_heat_rates`, 38 CCs) built and A/B-solved; **CALIBRATED → CALIBRATED**, no rejection-rule flip; re-keyed its own stamp. D56's target moved under it → D56-R. Stage-0 golden STALE vs 189. |
| **Audit programme (r#36)** | **v27** (#4740): job 0 pre-empted by this desk; flip set 5 → 3 of 6 (all three in-flight lanes' loose ends — one repaired here, one clears on D53's merge, the parity red cleared by caiso-246's registration); Z-4 and X-6b routed here (answered §0ag.4/§0ag.5); R-AG first recorded in v27 itself. PERF-B s3 LANDED (#4745/#4752; the adaptive-pass reuse, `perfb-s3-before/after` golden manifests). |
| **CAISO (r#33)** | **KEEPER → `2026-09-03-caiso-241-b1-ctpeaker`** (#4663): CT_PEAKER `committed` ruled OUTSIDE the Lever-A refusal, grounded 1.350 → 0.991 (zero DOF), solved against a REAL control under two in-session owner rulings; the object SURVIVES (7 % closed); NOT-YET C3a alone. **caiso-242**: arm withdrawn by its own falsifier (availability never binds; gas-basis identity error 10–49 %); **DATA DEFECT: 2,816 MW priced at $736/MWh for all of Nov-2025** from one EIA-923 row, via empty `state` on 100 % of CAISO gas rows — the lane's next object. **Step 4 skipped again (7th)**; guard red on CAISO. |
| **MISO (r#33)** | **miso-203/204/205** (zero solves): tail is ENERGY not congestion; **the C3a comparator is ONE HUB (INDIANA.HUB) and the committed probe records are on a clock 1 h off (25 h post-Feb-29)** — annual means unaffected, no determination moves, hour-matched stats in miso-202/203 affected; solar is ABOVE normal in the object's hours, the anomaly is WIND, the driver is LOAD (miso-203's mechanism refuted). Single-hub comparator = owner scoring-reference item, NOT a capx or calibration lever. Keeper unchanged at miso-202. |
| **NYISO (r#35)** | **KEEPER → `2026-09-04-nyiso-188-combined` — CALIBRATED** (grade 7/8, fails 0, C3c ledgered): Astoria artifacts re-derived, `cc_capacity_reconcile` (−740 MW over 12 CC plants) closes C1-2024 and C3a-2025 −10.3 → −6.9 %; regressions in band and stated. **No marker requested by the lane → card C-9.** Stamp re-keyed by the lane. |
| **MISO (r#35)** | **KEEPER → `2026-09-04-miso-210-clock`** (#4724): the max-gen emergency-tier registry on the CST model clock, all ten A/B gates pass; NOT-YET C3a-2025 alone. **Stamp NOT re-keyed → standing duty executed (tenth guard firing, eighth promoter miss since R-T).** |
| **CAISO (r#35)** | **caiso-244** (zero LP): the import LEVEL object is the NORTH corridor — the `PNW_hydro_base` floor alone exceeds the measured PNW net import by +5–8 TWh/yr; the south is UNDER-imported; the fitted spot capacities are not where the level sits. Keeper unchanged at caiso-243. |
| **NYISO (r#34)** | **KEEPER → `2026-09-04-nyiso-187-astoria-routing`** (via nyiso-186 the same day; both owner rulings; both re-keyed their gate-(a) stamps — the streak is broken): the 2024 CC_REGULAR excess is three plants (Cricket Valley, Zeltmann/Poletti, Astoria II), no plant-level hypothesis fires; the Astoria split-facility remap (55375 → 57664); the CT/steam deficit is OUT-OF-MARKET commitment in every class-zone (nyiso-187). NOT-YET {C1-2024 CC_REGULAR +3.80, C3a-2025 −10.3 %, C3c}. |
| **CAISO (r#34)** | **KEEPER → `2026-09-04-caiso-243-b1-f923`**: the F923 low-volume defect repaired at ROOT — `bins_to_fleet` never passed `state`, so the donor-count guard was skipped fleet-wide; **THE SAME ON PJM/MISO/NYISO/NEISO** (all `plant_level_fleet=True`) — a cross-ISO data-integrity flag for the other four backcast lanes. NOT-YET C3a alone (2025 +14.4 %). Forecast cache keys UNCHANGED by the promotion (D45-R leg 8). |
| **MISO (r#34)** | miso-208 (supply-mix map: the market ran the model's peakers, less coal, more gas), miso-209 (partial-derate shape inert by construction; production extract empty), miso-210 in flight. Keeper unchanged at miso-202. D49 half 2 names the exit-side object (position netted twice) → capx D51. |
| **Audit programme (r#34)** | v25 + v26: Y-4 landed, path-filter trap CLOSED (and fired on a records PR), fast tier green, **R-AE flip set 5 of 6 — one keeper-recipe declaration from done**; R-AF (stage-0 re-capture policy) recorded nowhere; PERF-B s2 attributed `markup` and delivered the WS3-next charter; a NYISO stage-0 re-capture in flight. |
| **NYISO (r#33, post-push)** | **KEEPER → `2026-09-04-nyiso-185-family-hr` by owner ruling** (#4679): one field (`egrid_family_heat_rates`), zero DOF, control bit-identical; NOT-YET grade 5 / fails 3 with a DIFFERENT C1 cell — 2023 ST_GAS closes (Ravenswood), 2024 CC_REGULAR share opens; C3a-2025 −10.5 %. **First promotion in eight to re-key its gate-(a) stamp** (detail only; `corrected_by` stale — cosmetic, logged). |
| **CAISO (r#33, post-push)** | **caiso-243 MID-SOLVE**: the F923 low-volume fallback guard (caiso-242's 2.8 GW / $736 per MWh defect) — promotion imminent; `caiso-t1h/t1f` deliberately outside D45-R. |
| **NYISO (r#33)** | **nyiso-181/181b/182/183** (zero non-control solves): the in-the-money object was an offer-reconstruction artifact (3.8–9.1 → 0.06–0.07 TWh/yr); C1-2023 ST_GAS is **ONE PLANT — Ravenswood +5.47 TWh, ECONOMIC**, hidden by class-aggregate cancellation (which also hides ~1 TWh/yr of native-grain forced energy); availability refuted; **carrier = Ravenswood's heat-rate basis 9.50 vs measured 10.71 MMBtu/MWh**. Lever queue rewritten. Keeper unchanged at nyiso-177. |
| **Audit programme (r#33)** | **v24**: leg 2's green lost to the caiso-241 stamp; **R-AB flip 4-of-5 ready, the fifth IS the stamp re-key**; path-filter trap covers all five required checks; R-Z + R-AC executed (ruff clean). Seven gates: six exit 0, `check_gate_a_provenance` exit 1. |
| **CAISO (r#32, post-pin)** | **KEEPER → `2026-09-03-caiso-240-b1-stgas`** (#4641): rule-24 census of all 28 `_DEFAULT_HR_MULT_BY_GROUP` literals on all six keepers, zero solves — **22/28 DEAD in every ISO**; `ST_CHP`'s entire offer surface is uncited literals (an ask for MISO/PJM/NYISO/NEISO, rule 25); CAISO's one groundable cell `ST_GAS:peak` armed measured. NOT-YET C3a alone (+12.6/+15.6 %). **Skipped step 4 AGAIN** → re-keyed by this desk under C-2. |
| **MISO (r#32, post-pin)** | **KEEPER → `2026-09-03-miso-202-unitclip`** (#4651): the boundary-day double-count is real (845 overlaps, every one exactly 24.0 h), repaired as a per-unit ceiling on a sum; all ten A/B gates pass; NOT-YET C3a-2025 alone (−12.4 %). **C3a-2025 anatomy: entirely a missing scarcity TAIL — the same object as C3c**; the outage family closes. **Skipped step 4 AGAIN** → re-keyed under C-2. |
| **NYISO (r#32, post-pin)** | **nyiso-179 + nyiso-180** (zero solves): the ST_GAS offer position is not the governing object (62 % of the 2025 top-decile deficit is the model's own price level); all four un-dispatched-in-the-money candidates close; per-generator dispatch limit lifted (`class_band_hourly` sidecar ships in the keeper bundle). Keeper unchanged at nyiso-177. Gain-family data points. |
| **Audit programme (r#32, post-pin)** | **v23** (#4645/#4646/#4648): R-X + R-Y DISCHARGED (golden tier green, cron removed), **G2 leg 2 SATISFIED (fast tier green, first ever)**, all three 09-02 stale stamps re-keyed (job 0 widened to three by owner decision; miso-200 found as a fourth miss the r#31 desk also missed). X-1: ruff red from `docs/handoffs/d37|d45/` probe scripts — lint-scope decision owed to the owner. X-2: stage-0 goldens 7→4 of 7. |
| **CAISO (r#32)** | **KEEPER → `2026-09-02-caiso-239-b1-stgas`** (PR #4634): the caiso-238 object-2 premise FALSIFIED zero-solve — the funded `ST_GAS committed 0.81` scalar reaches 2 of 25 tranches (both retired, zero 2025 availability), none of the three OTC steamers, which price off the uncited `1.15` class literal; both candidates REFUSED, repair RELOCATED there as gated `caiso_st_gas_committed_measured`; C3a cost +0.0001/+0.0060/+0.0001 $/MWh. **NOT-YET on C3a alone** (2024 +12.6 / 2025 +15.6 %); `audit_keepers` PASS 0/0. **Records defect:** finding + log headers say "Keeper UNCHANGED at caiso-231" while the same commit promoted — addendum owed. **Gate-(a) stamp NOT re-keyed** (R-T step 4 skipped). |
| **MISO (r#32)** | **KEEPER → `2026-09-02-miso-201-stbasis`** (PR #4630): ST-side capacity basis put on the LP's own basis (numerator, deliberately opposite to the CC flag's denominator move); single-field delta, S-0 bit-identical, scorer blind, 32/55 steam bins; **one frozen kill K-3 FIRED on one cell, disclosed**; promoted under the owner's standing re-scoped bar. **NOT-YET on C3a-2025 alone (−12.4 %)**; `audit_keepers` PASS 0/0. **Gate-(a) stamp NOT re-keyed.** |
| **NYISO (r#32)** | **KEEPER → `2026-09-02-nyiso-177-vintage-matched` BY OWNER RULING** (PR #4632; the override class, lane's own §1–§9 recommended against and stand): nyiso-176's degradation was the unguarded availability basis, NOT the accurate attribution; guarded companion reproduces Ravenswood `np.array_equal`. **NOT-YET, grade 6 → 5, fail set WIDENED to {C1-2023 ST_GAS +3.86 TWh, C3a-2025 −11.2 %, C3c}** (C3c no longer lone). No marker, no re-key duty. **nyiso-178** (PR #4633, zero solves): the ST_GAS envelope is NOT binding in either direction — measured-availability family closed for ST_GAS; duty-curve successor refuted ex ante; a response deficit (the gain family). **Gate-(a) stamp NOT re-keyed.** |
| **Forecast board (r#32)** | **`check_gate_a_provenance.py` FAILS ×3** (CAISO/MISO/NYISO cite superseded keepers) — all three promotion PRs skipped `keepers/README.md` step 4 (R-T routing half); verdicts unmoved; R-P ruleset still not in force so nothing gated it. Fourth instance of the class. → card C-2. Namespace otherwise byte-unchanged. |
| **Audit programme (r#32)** | v22 unchanged; no ruling past R-W. Q-4 (grep-each-ruling step) ADOPTED by this desk (§0ac.5). The gate-(a) routing failure is the audit desk's J-class item to record. |
| **MISO (r#31)** | **KEEPER → `2026-09-02-miso-200-unitroute`**: the CAMPD unit-outage class routing repaired at mixed-gas facilities; S-0 control bit-identical (max_abs_diff 0.0); **NOT-YET on C3a-2025 ALONE — unchanged in membership, SMALLER in magnitude**; every pre-registered kill silent; both A/B legs dashboard-registered (rule 15). |
| **NYISO (r#31)** | **nyiso-176: the per-unit-attribution probe REJECTED on its own R6** — it fixes C3a-2025 and breaks three other criteria; the keeper reproduces BIT-IDENTICALLY at HEAD. Rule 1 at its purest: the right number by a wrong mechanism, declined. A `campd_per_unit_attribution` matrix row + six cells added; both NYISO per-unit companions regenerated on a consistent basis with a reproducibility gate over both derived solve inputs. |
| **CAISO (r#31)** | **caiso-237** triaged the caiso-236 test debt (three items filed); **caiso-238** grounding charter landed pre-registered — 42 mis-classified scalars, four live residual DOF rows, **two fundable asks → RULED Q31: FUND BOTH** (owner's track executes). |
| **Audit programme (r#31)** | **v22**: leg-2 refused a THIRD consecutive time (the board still declining its own good news), R-U discharged, R-W's fast-tier repair fixed 11 of 12 CI-visible failures by root cause (1 latent bonus, 1 routed). |
| **Stage-0 / audit (r#30)** | **MISO captured (R-Q third issue) — FIVE of six ISOs golden-covered; PJM is the last gap.** records v21 REFUSED the G2 leg-2 satisfaction claim (run 2298 not green) — the board declining its own good news. The keeper-replay guard broken by caiso-236's deletion was caught and fixed in-wave. perf-b: ERCOT byte gate PASS, both grains gated. xiso-7: `prb_follower` DOF under-count — real defect, zero incidence. |
| **NYISO (r#30)** | **nyiso-175b** repaired the outage-extract routing defect + the CAMPD per-unit tranche-attribution defect (default-off companion), pre-registered, all four pre-solve gates PASS, K2 amended the construction honestly. Mid-chain on the CT-deficit objects. |
| **Stage-0 / audit (r#29)** | **Four of six ISOs golden-covered**: CAISO (vs caiso-231) + NYISO (vs nyiso-159) captured, and the **ERCOT 2023 carve-out closed via the golden-partition-carveout lane** — the r#26 schema blocker resolved; full ERCOT coverage. **Audit v20**: R-S..R-V recorded, the program UN-PARKED. **caiso-236**: DOF ledger stopped attesting nonexistent coal sigmoids; CAISO's rebuilt; the dead `caiso_bidir_intertie` + fitted export cap DELETED (rules 23/26). **perf-b** live (CAMPD normalization −40 % in the bench sub-phase, byte-gates NEISO+ERCOT) — watch only. |
| **MISO backcast (r#29)** | **miso-200** (steam bid-side): the routing defect measured, **the arm KILLED at phase 0 — no solve spent**; gated `fac_group` mixed-facility fix landed default-off; scorer committed BLIND; control replayed at HEAD. Mid-lane. |
| **NYISO (r#29)** | **nyiso-174** adjudicated the East River class crosswalk on the primary record; **nyiso-175** phase-0: the D-2 blocker is a GRAIN difference, the CT deficit is TWO objects, both East River gates fail. The kill/narrowing streak continues (169–175). |
| **MISO (r#28)** | **KEEPER PROMOTED → `2026-09-01-miso-198-oomlevel`**: the ST_GAS must-run floor LEVEL re-conditioned onto the out-of-merit phenomenon (new gated field `st_gas_mustrun_oom_level`); S-0 bit-identical through 39 commits, every kill silent, the REVERSED prereg direction confirmed, C8 improves all three years, **no criterion status moves** — NOT-YET on {C3a-2025} stands; structure promoted without gate movement (rule 1). **miso-199** then REFUSED the window-basis lever on a frozen census — **the commitment-floor family CLOSES at MISO**; an X-2 slot repaired + a silent no-op disclosed. Next: miso-200. |
| **NYISO (r#28)** | **nyiso-173**: the CC availability over-statement is provably INERT as a lever — the kill streak on the gain object continues (169–173). Next: nyiso-174. |
| **CAISO (r#28)** | **caiso-234**: the caiso-233-specified TOTAL-envelope successor estimator REFUSED on its own pre-registered gates (G-LOYO 34.2 % vs 25 %, scarcity_interval with 2024 held out) — the PRECOMMIT pushed before the DERIVATION because it was a second estimator on once-used data. Stop fired; nothing armed; a DOF item escalated to the lane's own record. |
| **NYISO (r#27)** | **Four disciplined kills on the gain object in one cycle**: nyiso-169 (zonal-gradient half carried by NO binding constraint; 169b: the CC_CHP over-run is a FLOOR, not the duct-burner band) · nyiso-170+b/c/d (the within-gas merit-order split is NOT an hourly displacement — layered pre-registered adversarial controls) · nyiso-171 (CC_CHP steam-host floor fails its own stop condition three ways) · nyiso-172 (the ST_GAS deficit is a RESPONSE deficit, not a dropout — object relocated). Keeper unchanged; the candidate space narrows honestly. |
| **MISO backcast (r#27)** | **miso-198 MID-FLIGHT** (ST_GAS out-of-merit level A/B): the prereg **REVERSED the inherited direction**, the scorer was committed before any arm result, the control leg reproduced the keeper BIT-IDENTICAL, the arm is solved — not yet registered. Grade next refresh. |
| **CAISO (r#27)** | **caiso-232**: the C3a residual SPLIT into level + shape — the morning and December symptoms are two different defects. **caiso-233**: import spot depths derived; both pre-registered gates FAIL — the depth limb REFUSED without a solve. Lane self-driving post-promotion. |
| **Audit programme (r#27)** | **v19 + v19b**: rulings **R-J..R-R** recorded (six were unrecorded from one sitting — the R-H failure shape again, caught by the same verified-absent discipline); **R-M applied BY-SHA** after its target verdict migrated keys; the dispatch-vs-launch check caught **three non-launches in one sitting**. **T16 executed plan §2's ladder adjudication** (rule-26 delete; → Q27). |
| **CAISO (r#26)** | **caiso-231 PROMOTED: keeper → `2026-09-01-caiso-231-b1-ungrounded`** (PR #4515). Three un-grounded gas offer classes re-grounded on their own measured bid buckets; **nine ERCOT-inherited multipliers retired to measured** (rule-25 debt paid), zero free parameters; adverse C3a cost 4–13× under bound; determination UNCHANGED NOT-YET on C3a alone (+12.55 %/+15.59 % 2024/2025, OVER — note the sign differs from the NYISO/MISO gain story); `audit_keepers` PASS 0/0. Promoted on the owner's verbatim structural-integrity standard. Terminal rest ends on the lane's own motion. |
| **NYISO (r#26)** | **nyiso-168 LANDED** (PR #4518): the 0.703 gain is a **slope deficit in the ordinary 50th–90th load band**; four candidate causes killed by measurement; the market's steepness there measured **NOT physical** (reserves clear >0 in ~100 % of DAM hours every zone, keeper ~0 in 99.6 %); the one new mechanism is **provably LP-inert, killed ex ante**; nyiso-167's probe reproduced bit-identically first. Keeper unchanged. Next: nyiso-169. |
| **MISO backcast (r#26)** | **miso-197 CHECKPOINT** (PR #4510): the CC_REGULAR over-dispatch census rule frozen zero-solve (914-line pre-registered probe) before any adjudicating quantity. Mid-lane. |
| **Audit programme (r#26)** | **v18b's R-H has PRIMACY on the nyiso-161 ruling** (see §0w.2 — Q22 is the owner's re-confirmation). **Stage-0 capture NEISO+ERCOT landed** (owner ruling R-L, the audit track's first solve lane): both fidelity oracles PASS, goldens CURRENT; the ERCOT 2023 carve-out is **not coverable without a schema change** — answered explicitly. |
| **NYISO (r#25)** | **nyiso-167 LANDED** (PR #4504): C3a-2025 re-attributed to a **year-invariant price-response gain** — model = 0.703 × actual + $11.03 over all 36 training months; C3a passes only for an annual actual mean inside $27.8–56.0/MWh and 2025 ($66.43) is 19 % outside. 87.4 % of the nyiso-161 "winter face" is this gain (winter residue −$0.51/MWh) ⇒ card's eligibility test (a) NO ⇒ **ruled Q22, card retired**. Cross-ISO gains (measurement only, rule 25): ERCOT 0.347 / MISO 0.500 / PJM 0.668 / NYISO 0.703 / CAISO 0.837 / **NEISO 0.986 — the existence proof it is closable**. The gain is now the backcast track's unifying frontier across four ISOs; offer-side `gas_offer_net_revenue_margin` DECLINED on evidence (DO-NOT-REDO), verdict K unchanged. Separately **PR #4485** discharged the r#23 OWED item (reference-side all-ISO cascade scan). |
| **ERCOT (r#25)** | **C-1 joint-wind charter mid-lane** (owner's track): PRECOMMIT + Amendment 1 landed 08-31 (base refreshed onto `e52b90a`; Q15 armed the volume rule under this charter), plus the **R-D wind-entry closure MAP** (`docs/MAP-c1-wind-entry-closure-2026-09.md`). Watch only. |
| **CAISO (r#24)** | **caiso-230 LANDED** (PRs #4493/#4499): the above-floor C3a term decomposed to a kill, no LP; log, matrix shard and lever queue stamped. **caiso-231 PRECOMMIT filed** (un-grounded-class offer re-grounding) — mid-lane. |
| **MISO (r#24)** | **miso-196 IN FLIGHT**: `cc_outage_derate_from_top` A/B pre-registered, phase 0 cleared, **and the A/B scorer written before any arm result exists** — the right order. Separately, **xiso-cascade repaired a real MISO instrument defect** (ASM MCP cascade summed; the "$484.87 = 118.8 % of the energy gap" headline corrects to **$193.30 = 47.3 %**). |
| **Audit programme (r#24)** | **v18/v18b LANDED**: ruling **R-H** recorded and its card retired; forecast gate-(a) rows guarded against the backcast store (F-5); the bench gate's engine-drift arithmetic fixed (item 12); the parity allowlist replaced with a class-level classifier (item 10); **ruling R-I flipped ERCOT's gate (a)**, which lane D19 then reconciled. **Stage-0 provenance repair** landed (per-entry golden provenance + retention invariant). |
| **CAISO (r#23)** | **caiso-229 LANDED** (PR #4482): Phase-0 kill of the caiso-227 §G below-stack wedge, zero LP. `cc_committed_offer_margin` U → **R**, refuted **on sign** — CAISO's measured committed band is 1.030 against an armed 1.000, so the ERCOT below-cost committed form has no CAISO analogue and a measured-faithful repair moves the floor the wrong way. Evidence appended without verdict change to three sibling cells; keeper unchanged. |
| **MISO (r#23)** | **miso-195 LANDED** (PRs #4471/#4474): the remove-only measured outage-envelope cap REFUTED at its pre-frozen gate (W4 conversion 16.9 % vs 25 %; W6 feasibility — 6 cap-caused violation days in 2025 where capped availability fell below measured EIA-930 output). **Every composition of `miso_native_outage_source` at the public record's aggregate grain is now adjudicated** — a lever family closed, not a single cell. Keeper unchanged, zero LP. |
| **NYISO (r#23)** | **nyiso-165 + nyiso-166 LANDED** (PR #4473) — the offered prompt ran as two sessions (find/defer, then repair). Both reference defects fixed for 2018–2026, hour-by-hour parity with nyiso-164 (8,759/8,759, both tiers, three years), keeper re-verified NOT-YET on exactly {C3a-2025 −11.5 %, C3c}, `audit_keepers` PASS 0/0. Levels were overstated **1.8×–2.9×**. A defect-duplicating raw-CSV fallback DELETED (rule 23), artifact made byte-reproducible, 9 regression tests. **OWED: the cross-ISO cascade scan was not carried** — re-offered. |
| **ERCOT (r#23)** | **ercot-248 LANDED** (PR #4484) and **corrected the director's charter premise**: the funded intake was a RESTORE (shards fetched by ercot-183 2026-08-09, untracked by BLOAT-B-5 A2 2026-08-15; the README coverage table predates that intake by five days). Placement overridden correctly (consumers glob `YYYY-MM.part*.parquet`). 700/700 days, 88,561,421 rows, rule 22 intact, delivery-2023 derive byte-identical. Recovery doctrine corrected: SHA256SUMS cannot accept a re-fetch restore, so a writer-independent manifest rides alongside. |
| **Audit track (r#23)** | **Refresh landed** (PR #4465): board to v17 + §8 entry; rulings R-D/R-F/R-G executed — the ERCOT wind decision map, **nyiso-161 parked with a fired trigger** (the waiver card stays filed and unruled), Leg-2 closed by archive. |
| **NEISO (r#22, amendment)** | **NEISO-RC-R LANDED IN FULL** (PR #4467) — see the scoreboard row. It is a capx lane, listed here only because its `neiso-t1x` preserve-then-overwrite is the settled state any later NEISO lane rebases onto. |
| **C3c audit (r#22, amendment)** | **PR #4466** independently replicated Q1 (REAL, by a different construction: overlap with PJM's posted penalty-step intervals at 75–91× base rate, p ≤ 9.7e-11; the model UNDER-prices reality by 2.7–7×) and **RETRACTED its own Q2 false positive**, tracing it to two defects in the committed reference `data/raw/_validation-source/actual_as_reserve_NYISO.parquet` — `build_reference` SUMS a cumulative cascade (spin_10 ≥ nonsync_10 ≥ op_30 in 100.0000 % of 289,344 rows) and maps naive prevailing timestamps onto the fixed `Etc/GMT+5` clock, off by an hour in 65.2 % of the year. **No keeper or scored result depends on it** (sole consumer is the disarmed RCPF comparator) — a trap for diagnostic sessions, filed for repair. **Generalizable rule for five other ISO lanes: a nested reserve cascade must be MAXED, never SUMMED.** → offered backcast prompt. |
| **MISO (r#22, amendment)** | **miso-194 LANDED** (PR #4468): the MISO cold-snap gas derate is REFUTED on W4 absorption at phase-0 census; cell U → **I** (inert), keeper unchanged, lever queue stamped. A clean negative. |
| **Offered prompts (r#22)** | TWO handed to the owner this sitting, neither chartered as a capx lane: **(1) the ERCOT 2024/2025 all-resource SCED conduct-corpus intake** (funded by ruling Q18; ercot-245's named unblock; additive intake through the data contract) and **(2) the NYISO AS-reserve reference repair** (the C3c audit's routed defect pair + the max-not-sum cascade rule carried to the other five ISOs). |
| **C3c scarcity program (r#22)** | **CHARTERED and both measurable questions SPENT.** `docs/CHARTER-c3c-scarcity-program-2026-08-31.md`. **Q1 pjm-164** (PR #4456): PJM's reserve-dual channel is **REAL**, not the ercot-214 phantom — binds on opportunity cost, $187.90 max dual, zero shortfall hours ever. **Q2 nyiso-164** (`e983bf50`): the pre-registered kill gate FIRES ON BOTH CLAUSES — NYISO's C3c ledger CONFIRMED on its own evidence. **Q3 is an architecture decision** (stochastic/multi-settlement vs rules 4/8/no-MIP) the charter recommends NOT opening → owner card. |
| **MISO (r#22)** | **miso-193 CONCLUDED** (PRs #4462/#4463/#4464): `cc_duct_peaking` examined end-to-end, both A/B legs registered, MISO cell U → K, keeper `2026-08-30-miso-191-bexit` UNCHANGED (NOT-YET on {C3a-2025} alone). miso-192's D-4 posture options (i)/(ii)/(iii) still an open owner card. |
| **CAISO (r#22)** | **caiso-228 CONCLUDED WITHOUT A SOLVE** (PR #4461): the SoCalGas OFO arm dies at gate D1 and the kill is **size-independent** — the band's import limb is delivered across the WECC seam, so no gas-side quantity mechanism of any magnitude lifts λ past $200 in the measured tail hours. caiso-131 A3 answered negatively and conclusively; keeper `2026-08-26-caiso-220-c1-crosswalk` unchanged. The r#21 "caiso-227 arm funding" card is CLOSED (owner funded it; this is the result). |
| **ERCOT (r#22)** | **ercot-247: declared `complete` + frontier** (PR #4454) — the first ERCOT rule-22 marker, resting on the ercot-246 partitioned-keeper ruling. `complete` = {ERCOT, NEISO, PJM}. The 2024/2025 SCED conduct-corpus intake (ercot-245's named unblock) remains an open owner card. |
| **NYISO (r#22)** | The AORR access route is CLOSED permanently (owner, nyiso-163b); nyiso-164 is the C3c program's Q2. The **nyiso-161 winter-face waiver card is still unruled** — the owner took the C3c question in preference to it. |
| CAISO (r#17) | **caiso-224 mid-lane**: A0 control G-CTRL bit-zero vs caiso-220 sidecars; FSNO variant seam set at the orchestrator; B1 arm 2023+2024 hourly-sidecar checkpoints landed; split-witness + F1/F2 falsifier probe PRE-REGISTERED (`scripts/probes/_caiso224_split_witness.py`, 21:58Z). Branch merged+deleted mid-cycle; unregistered ⇒ heavy slot NOT verifiably free (S-6 held). |
| Audit track (r#17) | **T1-H Phase-1 Leg A landed** (PRs #4386/#4389): gated default-off `storage_entry_availability_gate` (D-2) + `storage_entry_cost_normalized_rank` (D-3), matrix rows registered, A/B driver probe in. **Dedup boundary verified clean in code** — `model/storage.py` + config + harness only; None-drop passthrough keeps unarmed cache keys untouched (D12-C control safe). **PJM stage-0 golden captured** (`29a9cba`, audit card 1: pjm-162-inputclock 2023–2025, 0 drifted keys). `claude/ercot-243-release-exit-r7owkv` open, 0 unique commits. |
| NYISO (r#16) | **Keeper → `2026-08-30-nyiso-159-loss-surface`** (fail set narrows, still NOT-YET; marker stays withdrawn per Q5-W). **nyiso-160 winter-intake Leg 2 STOPPED WITH CAUSE** (AORR files unproducible) — NYISO's marker re-entry route is an open BACKCAST-track question. |
| NYISO (r#13) | **nyiso-158 phase-0 winter-face diagnosis landed** (PR #4339): the binding-depth differential is the measured Transco TTC step; no measured driver reaches the sharpened Iroquois re-open bar (first leg closed, Leg-2-only); C3b-2025 is WHOLLY the two faces (98.4 % of sq error — either face alone restores the band); CE-util overshoot adjudicated not-an-envelope-defect. **nyiso-159 opened** (PR #4352): phase-0 loss-component measurement on the 36-month record + PREREG of the zonal loss surface. Both merged; no NYISO branch in flight. |
| ERCOT (r#13) | **ercot-240 CLOSED in one arc** (PRs #4341/#4344/#4345/#4348): the event-hour demand gap is adjudicated the DC-tie import identity. **ercot-241 opened + merged** (PR #4349): Phase-0 precommit for the off-core conduct-parameterization screen. ercot-239 Stage-A census + Stage-B A/B driver landed (PRs #4351 etc.); the o7 attribution harness landed (PR #4334). |
| CAISO (r#13) | caiso-222 owner-sitting rulings recorded (R-1 keeper-currency annotation, Q1 terminal rest, Q2 routes armed/declined; PRs #4333/#4342/#4346). **caiso-223 sub-zonal scope round landed** (PRs #4347/#4350): partition adjudicated, membership derived, 3-way LDF split measured (gates 13/13 PASS), sufficiency gap list filed. |
| Governance (r#13) | The 2026-08-30 PM sitting executed four rulings (v14 ordering deviation recorded, gates re-measured green); director-records v14 board refreshed at re-derived pin. |
| Branches in flight (r#13) | `miso-190-backcast-calibration-okt1cn` ONLY — fully merged at `9cd6dc6` but **A/B solve NOT yet registered (scorer committed before it runs); owner confirms STILL RUNNING (Q9). S-123 check FAILS fifth consecutive; S-6 held on the same heavy slot.** |
| NYISO (r#12) | **Keeper → `2026-08-30-nyiso-157-par-attribution`** (owner ruling, structural-integrity formula, third application; D-5(b) stop fired and resolved by the ruling; keeper-auditor PASS). Determination **NOT-YET on {C3a-2025 −12.0 %, C3b-2025 0.203 knife-edge, C3c silenced-lone}** — fail set WIDENED vs nyiso-155. 2023 +1.0 % / 2024 −2.0 % PASS; first real zonal separation (CE util 0.381→0.784). Marker re-keyed at promotion, then **WITHDRAWN by the r#12 Q5 ruling (execution: lane Q5-W)**. Successor: intake Leg 2 (winter face). |
| ERCOT (r#12) | ercot-239 Phase-0 COMPLETE: missed-event family = measured energy-lambda scarcity in tight-room hours no reserve adder carried; precommit's availability/outage/ramp priors REFUTED; object = offer-surface conduct off the August core (ercot-217 episode). Successor o7 attribution-harness precommit landed ex ante (PR #4332). Both branches merged & deleted. |
| Forecast namespace (r#12) | FF-2D re-score (PR #4325): all 7 re-scorable verdicts byte-identical at HEAD, provenance-only diff, FR-21 gate reset. Bare keys unchanged. Benign — verified, not assumed. |
| Branches in flight (r#12) | `miso-190-backcast-calibration-okt1cn` ONLY. **S-123 check FAILS on it — fourth consecutive refresh.** caiso-221 records verified on main (`599f59b`); branch deletion lost nothing. |
| NYISO (r#11) | nyiso-157: C6 attested on both Leg-1 A/B bundles (`4d356f8`); **Iroquois companion arm REJECTED on its own pre-filed W-gates**, registered `2026-08-30-nyiso-157-iroquois-companion` (PR #4318; nyiso-147a-chp-btm pruned, top-15). Leg-1 PAR-attribution arm stands; promotion decision the backcast track's; branch open. |
| ERCOT (r#11) | **ercot-239 opened** (PR #4320): PRECOMMIT-only Phase-0 driver characterization of the 14-hour missed-event family (2023 carve-out lane; model < $200 while actual ≥ $500; stated prior: availability/outage/net-load-ramp representation object). Zero-solve; precommit pushed before measurement. Branch open. |
| Branches in flight (r#11) | `caiso-south-belly-pricing-24uv07` (records commit unmerged) · `ercot-239-residual-queue-lbkvbf` · `miso-190-backcast-calibration-okt1cn` · `nyiso-eastern-seam-par-leg1-w7s8mm`. **S-123 check FAILS on the MISO one — third consecutive refresh.** |
| ERCOT (r#10) | **TWO-CONFIG KEEPER** (owner ruling 3, 2026-08-26, executed `db8836a5`): forward keeper **`2026-08-25-234-eastex-identity`** (2024–2025 designated span, CALIBRATED, C3c ledgered ×2 — "the configuration the MODEL USES GOING FORWARD, forecast lane included") + 2023 carve-out `236-swcap-clip-k33`. Registered 3-year NOT-YET (C3a/C3b-2023) stands published. Q6 terrain moved by owner act; Q6 stays RULED-HOLD (§0g.3). |
| NYISO (r#10) | **nyiso-157 Leg-1 A/B registered** (control + arm, 2023–2025): PAR attribution restores the downstate gradient (NYC−UW 2023 annual mean $0.59 → $10.00, measured ≈ $14.8; C3a-2023 +6.8 → +1.0 %); Iroquois companion prereg filed BEFORE its solve; lane continues, branch open. |
| MISO / CAISO (r#10) | miso-190 mechanism landed (`partial_plant_exit_carry`, gated default-off; A/B scorer committed before running; branch open). caiso-221 killed the south-belly surplus-pricing design object with measurement (branch open). Card 10: decision-1 warm-start flip CLOSED-OVERTAKEN. |
| Branches in flight (r#10) | `caiso-south-belly-pricing-24uv07` · `miso-190-backcast-calibration-okt1cn` · `nyiso-eastern-seam-par-leg1-w7s8mm`. **S-123 check FAILS on the MISO one.** |
| Governance (r#9) | **Freeze TIER-SCOPED** (card 6 executed `0589b6f`): validation 2020–2022 lifted for `complete` ISOs, locked test frozen for all, `final` EMPTY. Card 7 standing precondition on any `final` grant (touchpoints run + loop quiescent). CAMPD layup charter closed with cause. Rubric **v3.5** (diurnal amplitude REPORTED-ONLY) verified determination-neutral over all six keepers — the xiso-6 watch item CLOSES. |
| CAISO (r#9) | Keeper → **`2026-08-26-caiso-220-c1-crosswalk`** (caiso-200 recipe replayed on the active measured membership crosswalk; owner-act promotion on the pre-registered rule; no marker, no re-key due). |
| Branches in flight (r#9) | `miso-190-backcast-calibration-okt1cn` (partial-plant mid-window exit carry — miso-188's named successor; PREREG-first) · `nyiso-eastern-seam-par-leg1-w7s8mm` (Leg 1 executing; nyiso-157 gate scorer filed) · `holdout-governance-rulings-0826` (records lane). No ERCOT branch open; ERCOT landed O7 P0-seam Phase-0 + two governance rulings (G-SPUR lidless count, band count 59→61). |
| Branches in flight (r#8) | `caiso-c3a-overrun-closure-5n84mn` · `ercot-backcast-calibration-9wkxrg` still open; `miso-188-rubric-failure-tuning-m1ph17` MERGED mid-refresh (PR #4296). Heavy-slot deconfliction live for ERCOT/CAISO capx work; S-123 releasable on a start-time check (no new MISO branch in flight). |
| MISO (r#8, mid-refresh) | **Keeper → `2026-08-30-miso-188-rvsscope`** (full-span; NOT-YET narrowed to **{C3a-2025} alone**; single delta `retiree_vintage_status_scope=true`, new gated default-off field, matrix row + cells minted per rule 28c; 28 dark retiree-channel units / 1,434 MW dropped on the EIA-860 vintage-status oracle; promoted on the PREREG's own rule, keeper-auditor PASS). Named-not-built successor: the partial-plant mid-window exit gap (5.93 TWh 2023). |
| NYISO (r#8) | **nyiso-156b: Q1 ruled OPTION A — winter locational identification intake AUTHORIZED** (`ab0513e`, spec `INTAKE-SPEC-nyiso156-winter-locational-2026-08-30.md`; Leg 1 session-executable, Leg 2 owner-executable fail-closed). Measured expectation: winter-face closure alone returns the keeper to CALIBRATED via the C3c standing rule — the live path through Q5 (§0e.2). Seam "unidentifiable" record corrected (authorization-blocked, not identification-blocked). |
| Dashboard hygiene (r#8) | Bench-fingerprint adjudication landed (PR #4293): 11 "stale" bench parts = UNLABELLED, not wrong; measured over the full builder-drift commit set. |
| Keepers (refresh #7 — MISO since superseded by the r#8 row above) | **ERCOT `2026-08-25-236-swcap-clip-k33` — CALIBRATED, empty fail set, but `years: [2023]` (2023-ONLY; see §0d.2 / Q6)** · CAISO `2026-08-17-caiso-200-h1-memberpanel` (caiso-220 replay mid-solve) · **MISO `2026-08-26-miso-187-nucavail`** (NOT-YET) · NEISO `2026-08-17-neiso-99-joint-p1` · NYISO `2026-08-25-nyiso-155-hydro-repair` (NOT-YET) · PJM `2026-08-15-pjm-162-inputclock` |
| Keepers (refresh #6 — superseded) | **ERCOT `2026-08-25-235-2023-discrete-k24`** (NOT-YET, price_mean; **2023-ONLY**, rule-16 waiver SPENT) · CAISO `2026-08-17-caiso-200-h1-memberpanel` (unchanged) · **MISO `2026-08-25-miso-186-statusscope`** (NOT-YET, **fuelmix + price_mean** — two criteria, was C3a-2025 alone) · NEISO `2026-08-17-neiso-99-joint-p1` (unchanged) · **NYISO `2026-08-25-nyiso-155-hydro-repair`** (NOT-YET, price_mean + price_tail) · PJM `2026-08-15-pjm-162-inputclock` (unchanged) |
| Markers / freeze | `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; freeze **TIER-SCOPED since r#9** (locked test frozen for all; validation by marker + `--holdout-authorized`) — was blanket-ACTIVE through r#8 |
| Gate (a) | pass on the literal test: PJM, NYISO, NEISO. fail on marker: ERCOT, CAISO, MISO. **NYISO's BASIS CHANGED** — its marker now rests on a NOT-YET keeper (§0c.2, Q5). |
| Other refresh-#6 movement | xiso-6 opened a **DECISION CARD on the diurnal price-amplitude rubric** (a cross-ISO rubric question — watch it, it could touch six determinations). CAISO AS-revenue registry row populated (storage 14.82 $/kW-yr @ ref 5.517 GW). xiso-5/6 landed a thermal-tranche vintage sidecar + an arm-over-gap guard at the `bins_to_fleet` seam. |
| ERCOT | Card Y signed **Y-C** (hold open). Card Z signed **Z-A**: crosswalk repair — **EASTEX (East Texas GTC) replaces the mis-attributed NE_LOB** on Northeast→North, static 1300 → 2300. ercot-234 also re-pointed the official scorer's validation gate at the ercot-231 keeper (stale since promotion). |
| MISO | miso-184 **V-DEFECT-COUPLING** (matrix cell R). miso-185 **V-NEG-ABSENT** — the §6b firm-export re-open data does not exist (698 EQR seller-quarter reports, no qualifying firm-export obligation); re-open narrowed to contract-grain. **~1.3 GW scarce-export model-class concession** is the honest residual; a D-4 posture question goes to the owner. |
| CAISO | Quiet this cycle. |

**Deconfliction: clean.** D2-B explicitly stopped at a FINDING on the one MISO root cause that
reaches shared solve machinery (S-1), per its charter.

## 3. Owner-tier questions — THIRTY-ONE ANSWERED (Q5/Q6 r#8; Q5 re-ruled r#12; Q7/Q8/Q9 r#13; Q10/Q11/Q12 r#15; Q13/Q14 r#17; Q15 r#18 — all 2026-08-30; Q16/Q17/Q18/Q19 r#22, 2026-08-31; Q20/Q21/Q22/Q23 r#25 + **Q24/Q25/Q26 r#26 + Q27 r#27**, 2026-09-01; **Q28/Q29 r#30 + Q30/Q31 r#31, 2026-09-02**. Q22 carries an r#26 primacy correction — audit ruling R-H ruled the same card first; see §0w.2)

**r#40 (2026-09-05): Q46 RECORDED — the in-lane owner ruling on nyiso192-Q1 LANDED (#4817): NYISO → `2026-09-05-nyiso-192-astoria-panel` (NOT-YET), `complete` + `frontier` WITHDRAWN under the Q5 uniform rule, gate (a) FAIL. Consequence for this desk: Q45's premise lapsed → T3-NYISO-GOLDEN HELD by Amendment 1, no card. No new card. §0ak.3.**

**r#39 (2026-09-05): NO new numbered ruling. Two director decisions inside standing rulings — D60 Amendment 2 (the P10 STOP resolved under Q37's pre-declared follow-up-attestation limb) and T3-NYISO-GOLDEN Amendment 1 (the `complete` marker as a START precondition of Q45). PENDING Q46: the in-lane owner ruling on nyiso192-Q1 (promote the NOT-YET Astoria arm; withdraw NYISO `complete` + `frontier`) sits on an UNMERGED branch — numbered when it lands. Owner acts recorded unnumbered: rule 29 clause (b) [no control solves / G-DRIFT], the delete-not-archive cleanup directive. §0aj.3.**

**r#38 (2026-09-05): Q44 RECORDED (D57 in-lane: PROMOTE the joint PJM configuration) · Q45 RULED LIVE (C-14: AUTHORIZE the NYISO §2.1b campaign, dispatch after D60 lands) · D60 relaunch-protocol check: STILL RUNNING → §D60 Amendment 1. Owner acts recorded unnumbered: rule 29 [R-SCREEN], the keeper-only site prune, the ercot-248 consolidation. Audit R-AK adopted. §0ai.3.**

**r#37 (2026-09-05): FOUR CARDS RULED LIVE — Q39 (C-10) frontier BOTH · Q40 (C-11) ARM D51's ratio for MISO · Q41 (C-12) ARM BOTH D52 gates · Q42 (C-13) ARM the CCS capex default + schedule the 1.1 h re-measure; Q43 records the D53 in-lane MISO arming instruction (2026-09-05 04:17Z). Execution: D56-R2 (Q39), D60 (Q40–Q42). §0ah.3.**

**r#36 (2026-09-05): Q1–Q38 spent; NO new numbered ruling at the entry's writing. THREE cards presented — C-10 (the frontier leg of the NYISO re-declaration; Z-4; recommend re-declare `complete` + `frontier` together on nyiso-189), C-11 (arm D51's ratio for MISO; recommend ARM), C-12 (arm D52's two NYISO requirement gates; recommend ARM BOTH). Rulings, when given, are Q39–Q41 and go in the table below and in an amendment to §0ag. CROSS-DESK RULING RECORDED: audit ruling R-AG (2026-09-04 22:20Z, the audit sitting) routed the NYISO re-declaration to the calibration director for a RECOMMENDATION with no audit-lane marker edit; Q38 (23:18Z, this desk) ruled the execution 58 minutes later without sight of it (R-AG was unrecorded until audit board v27). Both are the owner's; they coexist; C-10 is the recommendation R-AG asked for.**

**r#35 (2026-09-04): Q1–Q37 spent. C-9 RULED the same sitting — Q38: re-declare NYISO `complete` on nyiso-188 via records lane D56 (§0af amendment 1).**

**r#34 (2026-09-04): Q1–Q35 spent. Two cards — C-7 (D45-R leg 7, the NEISO dates-OFF control: running / dead → D51 rider / drop) and C-8 (rubric §5 second limb for pre-declared follow-up attestations). RULED the same sitting — Q36 (leg 7 rides D51), Q37 (rubric §5 limb adopted); §0ae amendment 1. NO arming card from D45-R: both §6 recommendations are 'do not move a default' and self-execute.**

**r#33 (2026-09-04): Q1–Q32 all spent. Three cards presented and RULED the same sitting — Q33 (D45 dead → D45-R), Q34 (standing gate-(a) re-key duty, executed), Q35 (Stage 3 folded into D45-R). §0ad amendment 1.**

**r#32 (2026-09-03): NO new numbered ruling — Q1–Q31 all spent. Cards: C-1 (D44/D45 status) — owner: "they have all landed I think"; CONFIRMED by content post-pin (D44 landed; D45 checkpoint). C-2 (stale gate-(a) stamps) — owner: GRANT one push; SPENT on caiso-240/miso-202 (the rows the card named had been repaired by audit v23 in the same window). C-3 (the priced re-measure, §0ac.7) — RULED Q32: STAGED; D46 issued (amendment 2).**

Full signature record and the consequences adopted:
**`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5** (cards A/B/C/Y);
Q7–Q9 were ruled via in-session decision cards at r#13 and are recorded here + in §0j.3
(execution of Q7 = lane D13).

| # | question | resolution |
|---|---|---|
| **Q31** | caiso-238's grounding charter filed two fundable asks (four live residual DOF rows, 42 mis-classified scalars). Fund? | **RULED 2026-09-02 (r#31) — FUND BOTH.** The CAISO lane executes its own pre-registered charter; recorded here for the watch, executed on the owner's track. |
| **Q32** | Card C-3 (r#32): the post-repair-wave re-measure, priced — hindcasts+golden ≈2.5 h, the t1f tail ≈24 h serial (80 % PJM+MISO), PJM/NYISO surfaces reserved by D45. Which scope? | **RULED 2026-09-03 (r#32) — STAGED: cheap set now, t1f tail later.** Stage 1 dispatched as D46 (ERCOT/CAISO/MISO/NEISO t1h + GOLDEN-2 + pairable t1f); Stage 2 gated on D45's close-out; Stage 3 (PJM/MISO t1f) owner-scheduled. §0ac amendment 2. |
| **Q33** | Card C-4 (r#33): D45's owed half absent two sittings, branch deleted. Status? | **RULED 2026-09-04 (r#33) — DEAD; issue D45-R absorbing D46 Stage 2.** §0ad amendment 1. |
| **Q34** | Card C-5 (r#33): the seventh consecutive promoter miss of the R-T gate-(a) re-key; R-AB's flip blocked on the stamp. Who re-keys? | **RULED 2026-09-04 (r#33) — STANDING DUTY: this desk re-keys at every refresh** (R-N/R-T pattern, verdict-neutral, each event logged as a promoter miss); executed at once on caiso-241. §0ad amendment 1. |
| **Q35** | Card C-6 (r#33): Stage 3 re-priced 7–10× cheaper (PJM/MISO t1f ~45–90 min each). Fold in? | **RULED 2026-09-04 (r#33) — FOLD INTO THE D45-R BATCH** with a 2 h STOP per leg. §0ad amendment 1. |
| **Q36** | Card C-7 (r#34): D45-R's pre-declared leg 7 (NEISO dates-OFF control) never ran. Status? | **RULED 2026-09-04 (r#34) — D45-R is done; leg 7 rides D51 as an unconditional rider.** §0ae amendment 1. |
| **Q37** | Card C-8 (r#34): rubric §5 names only the producing session as attestation author; D47's pre-declared follow-up attestation had to be disclosed as a deviation. Add a limb? | **RULED 2026-09-04 (r#34) — ADOPT:** a follow-up lane may author iff pre-declared before authoring, attestation row only, artifact-only re-score. Recorded via D51's records rider (e). §0ae amendment 1. |
| **Q38** | Card C-9 (r#35): NYISO's keeper nyiso-188-combined is the first to read CALIBRATED; the `complete` marker was withdrawn 2026-08-30 with an explicit re-entry clause. Re-declare? | **RULED 2026-09-04 (r#35) — RE-DECLARE NOW via records lane D56.** Validation tier re-authorized, nothing spent; gate (a) flips to PASS; D-5(b) duty attaches. §0af amendment 1. Executed by D56-R on nyiso-189 (PR #4763). |
| **Q39** | Card C-10 (r#36/37): D56-R left `frontier` withdrawn; the four-instrument test is split on that leg alone (audit Z-4; R-AG asked for this recommendation). Re-declare frontier too? | **RULED 2026-09-05 (r#37) — RE-DECLARE FRONTIER ON nyiso-189 (both instruments, as the withdrawal removed both).** → D56-R2. §0ah.3. |
| **Q40** | Card C-11 (r#36/37): D51's `adequacy_accounting_ratio_dated_net` (0.8546 → 0.8934) — limb (c) fails by the letter, every substantive test holds. Arm for MISO? | **RULED 2026-09-05 (r#37) — ARM FOR MISO** via `default_scenario_overrides` (rule 25); bare `miso-t1h` re-keyed, `miso-t1f` re-solved, priors preserved. → D60. §0ah.3. |
| **Q41** | Card C-12 (r#36/37): D52's two NYISO requirement gates — positions to within ±3 pts, LOYO 3/3, shipped cost zero. Arm as NYISO's default? | **RULED 2026-09-05 (r#37) — ARM BOTH.** The NYCA curve stays OFF (P9 failed on D52 and D59). → D60. §0ah.3. |
| **Q42** | Card C-13 (r#37): D50/D50-R's `ccs_retrofit_capex_co2_scaling` — ERCOT/MISO closed, PJM −74.6 %, NEISO cap-bound; blast radius 1.1 h residual; fourth seam unbuilt. Arm as the default? | **RULED 2026-09-05 (r#37) — ARM AS DEFAULT AND SCHEDULE THE 1.1 h RE-MEASURE** (CAISO t1f, NYISO t1f, GOLDEN-3; priors preserved). → D60. §0ah.3. |
| **Q43** | (No card — an owner instruction given IN the D53 lane, 2026-09-05 04:17Z, on the measured A/B with all four limbs MET.) | **RULED IN-LANE — ARM the retirement-screen sector gate for MISO ONLY** (`_miso_config` override; dataclass default unchanged; bare `miso-t1h` → the solved leg; D46 preserved at `-pre-d53`; PJM untouched, D58 the discriminating test). Recorded here at r#37 so it never goes unrecorded (the R-AG lesson). §0ah.1. |
| **Q44** | (No card — an owner ruling given IN the D57 lane, 2026-09-05, on the measured A/B: the joint PJM flip's §8 recommendation.) | **RULED IN-LANE — PROMOTE the JOINT PJM configuration** (`pjm_accreditation_design_vintage` + `pjm_demand_response_supply` + `capacity_market_supply_clearing_by_iso["PJM"]`) via `_pjm_config` overrides; shared defaults untouched; arm A = bare `pjm-t1h`; D45-R at `-pre-d57`; the E&AS operand named as successor (→ D61); `pjm-t1f` re-measure → D60. Recorded r#38. §0ai.1. |
| **Q45** | Card C-14 (r#38): NYISO holds (a)+(b)+(c), `complete` + `frontier`, requirement gates armed. Authorize the §2.1b full-horizon campaign? | **RULED 2026-09-05 (r#38) — AUTHORIZE; DISPATCH AFTER D60's RE-SOLVES LAND** (one HEAD carries every armed posture before the golden is cut). → T3-NYISO-GOLDEN (pack), released-conditional. §0ai.3. **PREMISE LAPSED at r#40 (Q46 withdrew the marker); the campaign is HELD, not cancelled — re-served as a new card when NYISO re-enters `complete`.** |
| **Q46** | (No card — an owner ruling given IN the nyiso-192 lane on nyiso192-Q1, 2026-09-05: "Ok promote it … then tune the cc regular offer curve up for the duct burner peaking tranche".) | **RULED IN-LANE, LANDED #4817 — PROMOTE `2026-09-05-nyiso-192-astoria-panel` (NOT-YET; the D-5(b) stop fired and was chosen with its cost): `complete.NYISO` + the Q39 frontier WITHDRAWN under the Q5 uniform rule; gate (a) FAIL; validation tier lapses; `final` untouched; nothing spent.** The named lever (duct-burner tranche) was then screened and KILLED by nyiso-194 under rule 29. Recorded r#40. §0ak.2. |
| **Q30** | D42's A/B: filed EIA-860 fossil retirement dates as an exogenous step-1 input take recall 5/19 → 16/19 with ZERO screen displacement and per-unit published deferral counters. Arm as the default posture? | **RULED 2026-09-02 (r#31) — ARM AS DEFAULT.** The gated channel flips default-on (vintage-gated, reversal registry, screen on the residual fleet); spec §5.1 + CLAUDE.md step-1 amended to match; matrix re-stamped; the stale-bundle consequence joins the batched re-measure decision. Admissibility per rule 13 by the additions-pipeline symmetry — the old rationale was about precision, never admissibility. Execution = **D44**. *(Same sitting, recorded beside it: D37's P9 flip condition FAILED on its own terms — the Net ICR default stays OFF with no discretionary act; the pre-declaration governs.)* |
| **Q29** | D32's R1-PRIMARY: the floor's exit selection is measured indistinguishable from random, and the one discriminating published per-unit driver (filed retirement dates) is deliberately no-opped for fossil (`forecast_fossil_retirement_economic=True`). Charter the announced-date A/B? | **RULED 2026-09-02 (r#30) — CHARTERED (→ D42)**: the MISO 2021–2025 T1-H A/B, fossil EIA-860 planned dates as an exogenous step-1 input (vintage-gated 2020, reversal registry armed, economic screen residual) vs the shipped posture, LOYO-scored, pre-declared from D32's own numbers; the rule-19 dates-vs-screen reconciliation is designed in the charter; both legs SUFFIXED — **nothing arms until the A/B and the owner both say so.** |
| **Q28** | D40 built the NEISO Net ICR requirement lever (default-off, LOYO-scored; +21.4 → −2.1 pts at the clean 2023 entry; post-wave years unscoreable until D37). Arm? | **RULED 2026-09-02 (r#30) — ARM FOR D37's MEASUREMENT ONLY**, at D40's recommendation; the shipped default stays OFF pending D37's measured result. D37 carries the lever ON in its run_config plus the `entry_screen_diagnostics` precondition. |
| **Q27** | T1.6's lever `renewable_buildout_pace` was consumed by no model code and is DELETED (rule 26, lane T16); the FC-6 battery leg is OUT OF SERVICE and NEISO's FC-6 is structurally CAVEAT-at-best until a replacement lever is owner-signed. Which? | **RULED 2026-09-01 (r#27 sitting) — RE-POINT T1.6 TO `entry_rate_limits`**, at the T16 recommendation (real, cited, consumed, owner-armed, not metric-confounded; the adjudicated rejections — `eac_price_wind` confounded via max(eac, rps_shadow), `offshore_wind_available_year` inert in NEISO — stand). Execution = **T16-A** (Opus; 2 rungs + artifact-only re-score, no golden re-solve), HELD until the golden session closes. The pre-registered honesty clause binds: the REC dual is pinned at the $50 ACP ceiling in both D21 rungs — a non-moving lever is a real RPS/ACP finding, reported, never a third lever tried. The re-point-vs-amend question (T1.6's cell names an economic condition, not a config field) is verified and stated by the execution lane. |
| **Q26** | D23's R4, surfaced again by D26: `carbon_price` REPLACES the resolved signal — the exact trap the carbon25 arm fell into on an ISO whose base carries the RGGI trajectory. Replace, floor, or stack? | **RULED 2026-09-01 (r#26 amendment 1) — KEEP REPLACE + ADD THE GUARD.** Semantics unchanged (no registered-field meaning shift, no config archaeology); a loud validation warning fires when a forecast scenario's `carbon_price` sits below the resolved base trajectory in any year, pointing authors at `carbon_price_delta` for increments. Execution = **D34** (Opus). **R4 is CLOSED** — no successor re-opens it without a new owner act. |
| **Q25** | The golden re-solve, fully ripe at last: Q16's ceiling premise discharged (FC-5 CAVEAT via D25; FC-6 CAVEAT via D26's repaired P1, which PASSES), the standing golden still records the pre-R-A posture (headline: ZERO storage entry in 25 years) while R-A armed exactly the storage-entry mechanisms and D25 measured that family as the corridor's largest divergence. Authorize a second §2.1b campaign? | **RULED 2026-09-01 (r#26 amendment 1) — AUTHORIZED, NOW** (over the after-D33 and hold options). One campaign: **T3-NEISO-GOLDEN-2**, NEISO BAU 2026–2050 at HEAD with the R-A-armed posture, its own FC-6 battery at its own vintage (the D26 `carbon_price_delta` construction), full-rubric scoring, preserve-then-overwrite (the pre-R-A golden stays preserved with its posture-epoch caveat). Q13's "this campaign only" scoping carries over verbatim — a third campaign needs a new owner act. Execution = lane **T3-NEISO-GOLDEN-2** (Fable). |
| **Q24** | Fund the tightly-scoped MISO PRA/RBDC intake D31's identification needs (PRA Results Posting category rows, ~5 numbers × 3 planning-year postings + Initial PRMR, plus the published RBDC shape source — misoenergy.org 403-blocked in-session)? D28 pre-argued this is NOT the FC-5 class Q23 refused: one source, the S-123 anchor-vintage document class, ~15 numbers | **RULED 2026-09-01 (r#26 sitting) — FUNDED.** The owner fetches the postings out-of-session and hands the files to lane D31; the position audit and curve shape are then fully identified from published data (rule 14). **Q23 stands unchanged** — its FC-5 source class remains closed; this ruling neither re-opens nor narrows it. |
| **Q20** | D24 priced four repairs for the cache-key optional-fields defect — which lands? | **RULED 2026-09-01 (r#25 sitting) — (c′)+(b′-1), THE ZERO-COST PAIR, at D24's own recommendation.** (c′): a cache hit is REFUSED when the stored config differs on any common field or the requesting config carries a field absent from the stored one away from its registration-time default — wrong serve becomes mechanically impossible at the seam that already refuses contaminated keys. (b′-1): the drop comparison reads DECLARED defaults from an append-only ledger — keys identify from the next flip onward. 0 keys move, 0 caches invalidated. **(b′-2) retroactive separation DECLINED**; the two historical collision pairs stay unseparated (provenance annotation only). Execution = lane **D24-R** (Opus). |
| **Q21** | miso-192's D-4 posture options (i)/(ii)/(iii) — open since r#22, re-presented with nyiso-167's evidence (MISO keeper gain 0.500, C3a pass window $26.8–40.2/MWh; the same year-invariant object) | **RULED 2026-09-01 (r#25 sitting) — (iii), CONTINUE THE LANE** on the named candidates (`gas_coldsnap_derate` + `winter_fuelsec_posture` K@NEISO, aimed at the named Jan-2025 −1.43 pp; `cc_duct_peaking` + `egrid_identity_heat_rates` K@NYISO; `tac_load_coverage` K@CAISO), the cross-ISO gain object as the sharper target. Option (i)'s three-amendment ledgering is OFF the table (its v3.0 exhaustion predicate is contradicted by miso-192 §2.1 and the live gain object). Execution = the owner's MISO backcast lane (miso-197+, after miso-196 lands) — recorded, not chartered. |
| **Q22** | The nyiso-161 winter-face waiver card (parked with a fired trigger, audit R-F) — ruled at last, on nyiso-167's measurement | **CORRECTION r#26 (§0w.2): audit ruling R-H (2026-08-31 sitting, first recorded at v18b D-7, PR #4498 — BEFORE this card set was served) had ALREADY ruled this card Option A. Primacy is R-H's; Q22 stands as the owner's independent re-confirmation on nyiso-167's added evidence — same outcome, no divergence, and the duplication is recorded against interest.** Original entry: **RULED 2026-09-01 (r#25 sitting) — OPTION A, NO AMENDMENT.** NOT-YET stands; the card RETIRES answered-by-measurement: its own eligibility test (a) reads NO (87.4 % of the winter face is the year-invariant gain; the genuinely winter-specific residue is −$0.51/MWh — the blocked AORR input is not the object; removing Jan+Feb "merely helps"). No ACCESS-BLOCKED caveat class is created; the "only C3c is non-downgrading" line holds. Card annotated in place; the audit board's parked row flagged for retirement at ITS next sitting. |
| **Q23** | Fund any of the five missing FC-5 external sources (D25 §6.5 ranking: Gold Book → CELT → StdScen2024 → MISO Futures → CAISO IEPR)? | **RULED 2026-09-01 (r#25 sitting) — NONE. Owner verbatim: "None — I'm not getting more data."** All five CLOSED as not-funded, the egress-blocked StdScen2024 included. FC-5 rests permanently on the current anchor set; its CAVEAT is the steady state and the t3-required table's single-source status is a named, accepted limitation. **DO NOT RE-PRESENT absent a new owner act.** |
| **Q16** | The T3 NEISO golden records the PRE-R-A unarmed storage-entry posture and its headline result is ZERO storage entry in 25 years, while owner ruling R-A armed exactly the storage-entry mechanisms. Authorize a second §2.1b campaign to re-solve it? | **RULED 2026-08-31 (r#22 sitting) — HOLD, AND FIX THE CEILING FIRST.** The binding reason is not cost: **FC-5 and FC-6 are REQUIRED at t3 and neither instrument exists for ANY ISO**, so no golden can score better than HOLD regardless of model quality — a re-solve would spend a second campaign into an ungradeable ceiling. The golden stands as registered with its posture-epoch caveat VISIBLE, and nothing quotes it as a post-R-A result. Q13's "this campaign only" scope is untouched; no second campaign is authorized. Execution = lanes **D21** (FC-6) then **D22** (FC-5). |
| **Q17** | C3c program Q3 — the probabilistic RT premium: where the residual really is what a deterministic perfect-foresight hourly LP cannot contain (CAISO, MISO, NEISO, ERCOT's conduct variant), open the architecture program? | **RULED 2026-08-31 (r#22 sitting) — DO NOT OPEN**, at the charter's own §5/§6 recommendation. It collides with rules 4 `[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint; crossing that residual needs a different model class and would put three non-negotiable rules in play. **The C3c program CLOSES** having answered both measurable questions (Q1 REAL, independently replicated; Q2 CONFIRMED after a retraction) — closing on evidence, not drift. |
| **Q18** | Fund the ERCOT 2024/2025 all-resource SCED conduct-corpus intake — ercot-245's named unblock, filed when that lane killed itself at census? | **RULED 2026-08-31 (r#22 sitting) — FUND IT.** Backcast-track, so it is OFFERED to the owner as a prompt and recorded in §2, never chartered as a capx lane. Purely additive intake through the data contract; it unblocks the commitment-state object ercot-245 could not reach without licensing anything. |
| **Q19** | Ordering implicit in Q16, recorded so it is not re-litigated: which half of the t3 ceiling is built first? | **RULED 2026-08-31 (r#22 sitting) — FC-6 FIRST, THEN FC-5.** FC-6's tooling already exists (`scripts/run_driver_battery.py` + `check_forecast_invariants.py --paired`) and the gate is merely UN-RUN; FC-5's gap is an eight-source intake behind one new curated `benchmark-corridor` datatype (rubric §6). No second golden until both can grade it. |
| ~~Q7~~ | Leg-(c) semantics: the board carried BOTH readings (D7 wrote ERCOT/PJM/MISO fail-on-band; D10 wrote NYISO pass-on-measurement) | **RULED 2026-08-30 (r#13 sitting) — MEASURED CLOSES THE LEG**, per the charter-literal §2.1b(c) test ("measured and reported" + readiness green) and card A-A as signed ("closes on a measured FC-4"). ERCOT/PJM/MISO leg (c) → pass-on-measurement, FC-4 FAIL magnitudes stay at full magnitude; NYISO's PASS stands; the in-band reading is superseded. Execution = lane D13. No §2.1b gate opens (all three fail other legs). |
| ~~Q8~~ | Arm `entry_margin_exhaustion` as the ERCOT forecast default? (D11-R's escalation) | **RULED 2026-08-30 (r#13 sitting) — HOLD UNTIL D12**, at the finding's §5 recommendation. The gas half is inert on the live reserve leg, so arming now would bake in the VRE/storage-only split; D12 adjudicates the scarcity basis first and its report re-opens the decision. Matrix cell stays **O**. |
| ~~Q15~~ | The D12-C re-decision (Q10's contradiction branch): one V-2 window missed on a pre-declaration derivation error, every structural claim confirmed, conservative direction — arm? | **RULED 2026-08-30 (r#18 sitting) — ARM BOTH FIELDS** (`entry_margin_exhaustion` + `entry_forward_reserve_leg` → ERCOT forecast defaults), the owner judging the record confirming-in-substance per the finding's own §4.3 clause. The V-2 miss is described honestly in the arming citation; matrix cells O → K-forecast-armed on the registered pair's evidence; sister-ISO cells stay U (rule 26). Execution = lane **D12-A** (zero-solve; prompt in the pack). |
| ~~Q13~~ | NEISO §2.1b leg (d): first-ever full-solve authorization, presented on S-4b's measured result per Q11 | **RULED 2026-08-30 (r#17 sitting) — AUTHORIZED: the T3 BAU GOLDEN, NEISO, 2026–2050, budget ~1.0 h / ~4.3 GB (FF-3E), THIS CAMPAIGN ONLY.** The first §2.1b gate opening in program history. Caveats carried verbatim into the campaign record (floor-dependent 2028/29 I7; D14 exit-composition recall 2/6; FC-7 DOF gap); a gate-condition regression re-closes. Execution = lane T3-NEISO-GOLDEN (prompt in the pack). |
| ~~Q14~~ | caiso-224 / the S-6 heavy slot: is the CAISO session still solving? | **ANSWERED 2026-08-30 (r#17 sitting) — the caiso-224 session RAN OUT mid-completion** ("mid keeper promotion I think"); the owner directs the DIRECTOR to draft a finisher prompt (a recorded backcast-track boundary exception, owner-requested), then S-6 unblocks. Lane CAISO-224-FIN issued — zero-solve; it executes the PRECOMMIT's own §5 adjudication (measured record: F1 fires ×3 + F2 fires ⇒ R for keeper purposes, never auto-promoted), registers both bundles, stamps the matrix. **S-6 = RELEASED-CONDITIONAL on CAISO-224-FIN landing.** |
| ~~Q10~~ | The Q8 re-decision: D12 reported (phantom leg adjudicated; recommended arm-both) — arm? | **RULED 2026-08-30 (r#15 sitting) — CONFIRM-PAIR, THEN ARM.** Lane D12-C runs ONE arm-vs-control A/B (two fields, single logical delta) measuring the closed loop; **arming auto-executes on a confirming record**; a contradiction returns unarmed at full magnitude. |
| ~~Q11~~ | NEISO leg (d): first-ever full-solve authorization now live — sign? | **RULED 2026-08-30 (r#15 sitting) — HOLD FOR S-4b FIRST.** S-4b dispatches now; the leg-(d) card is re-presented on its measured result (a published filing supersedes the current requirement bar; D14's retirement-composition finding noted as context). |
| ~~Q12~~ | Charter the D5-R crossover-scorer repair (verdict-moving re-score)? | **RULED 2026-08-30 (r#15 sitting) — CHARTERED, FULL FIX** (D5 preference (a): canonical taxonomy-chain coal split at gmModel build; C1 coal rows repaired in the same stroke; §5.2 pre-declared table is the honesty gate). |
| ~~Q9~~ | Is the miso-190 backcast session still running? (governs the S-123 start-time check + S-6's heavy slot) | **ANSWERED 2026-08-30 (r#13 sitting) — STILL RUNNING.** S-123 held (fifth consecutive check fail); S-6 held on the heavy slot. Both re-checked every refresh. |
| ~~Q1~~ | ERCOT 2023 arc settled? | **ANSWERED** — card Y signed **Y-C**, hold open ⇒ D4 = I3-invariant half only. |
| ~~Q2~~ | Leg-(c) consistency (card A) | **SIGNED 2026-08-25 — (A-A), at the recommendation.** CAISO + NYISO move `na`→`fail`, `"c"` into both `closed_on`; NEISO unchanged. **NYISO T1-X chartered (D10)** so leg (c) closes on a measured FC-4. No gate opened; leg (d) untouched. |
| ~~Q3~~ | `entry_lookahead_reprice` disarm default (card B) | **SIGNED 2026-08-25 — (B-C), at the recommendation.** Shipped default HOLDS, cell stays `O`, no verdict minted. **Developer-pro-forma construction chartered (D11).** Neither known-wrong object is ratified. |
| ~~Q4~~ | PJM beyond-last-FPR convention (card C) | **SIGNED 2026-08-25 — (C-A), at the recommendation.** **Hold-last-FPR adopted**, bundled with the D-1 checker repair. PJM's I7 miss restates **366 MW → ~5.9 GW**, 2029 plausibly joining — a worse reported result, taken as the more honest bar. S-5 unblocked; S-6 strictly after. 2029/30 parameters intaken on publication (rule 23). |
| ~~Q5~~ | NYISO marker on NOT-YET keeper | **RE-RULED 2026-08-30 (r#12 decision card) — WITHDRAW THE MARKER (CAISO precedent), superseding the r#8 WAIT.** The recurrence clause fired (nyiso-157 promotion re-keyed the marker onto a second consecutive NOT-YET keeper, fail set widened). Written reconciliation, now uniform: a `complete` marker cannot stand on a NOT-YET keeper; the structural-integrity formula governs KEEPER promotions only. Execution = lane Q5-W. Re-entry is a new owner declaration once the keeper again scores CALIBRATED (winter-intake route). |
| ~~Q6~~ | ERCOT CALIBRATED but 2023-only | **RULED 2026-08-30 (r#8 sitting) — HOLD, NO ACTION.** No direction to the ERCOT backcast lane; revisit when it goes quiet. Gate (a) keeps failing on both counts meanwhile. |

**None of the four signatures** touched a backcast keeper, marker or matrix cell, lifted the
holdout freeze, authorized a §2.1b full-solve, or opened any ISO's gate.

### Q6 (refresh #7) — ERCOT is CALIBRATED but its keeper is 2023-only

**RULED 2026-08-30 (r#8 sitting): HOLD, NO ACTION** — no direction to the ERCOT backcast lane;
revisit when it goes quiet. The analysis below is preserved as the record the ruling was made on. `2026-08-25-236-swcap-clip-k33` scores **CALIBRATED with an empty failing
set**, closing the 2023 price object card Y held open two days earlier. But its registry declares
`years: [2023]`, so gate (a) fails on **two** counts: ERCOT is absent from `complete`, and
§2.1b(2)(a) requires a **full-span** keeper (rule 16), which this is not. **Declaring ERCOT
`complete` would therefore NOT open its gate (a).** To convert the CALIBRATED result into forecast
progress ERCOT needs a **full-span 2023–2025 keeper carrying the swcap-clip recipe**. Director
recommendation: **before spending any `complete` declaration, have the ERCOT lane re-solve the
swcap-clip recipe full-span** — the rule-16 waiver that licensed the 2023-only form was for the
backcast lane's regime argument and was never a forecast-gate instrument. Sequencing only; no
determination is questioned here.

### Q5 (refresh #6) — NYISO's `complete` marker now rests on a NOT-YET keeper

**RULED 2026-08-30 (r#8 sitting): WAIT FOR WINTER INTAKE** — the precedents are left standing
unreconciled and the nyiso-156 intake is the designated resolution route; no marker moves and
gate (a) stays PASS on the literal test. The analysis below is preserved as the record the
ruling was made on. NYISO's keeper moved to `2026-08-25-nyiso-155-hydro-repair` (NOT-YET on
price_mean + price_tail) and the marker was re-keyed to it, with the D-5(b) worse-determination
stop fired, escalated and resolved by an explicit owner ruling on structural integrity over gate
regression. **On 2026-08-06 the identical fact pattern — a `complete` marker whose keeper scored
NOT-YET — withdrew CAISO's marker outright**, on the reading that "a `complete` marker cannot stand
on a NOT-YET keeper". Both are now on the record and they point opposite ways.

**Why this track cares:** gate (a) is the only §2.1b leg that reads off the backcast marker, and
NYISO is the program's lead ISO — the one ISO whose legs (a) and (b) both pass. On the charter's
literal test (*designated full-span keeper AND an entry in `complete`*) gate (a) still passes, and
this director is NOT re-reading it downward on its own initiative. But the question of whether the
marker is sound is the owner's, and its answer decides whether NYISO's lead position is real.
**Director recommendation: state the reconciliation explicitly** — either (i) affirm that the
owner's structural-integrity standard permits a `complete` marker on a NOT-YET keeper, which
distinguishes the CAISO withdrawal on its own facts (CAISO's was a rubric re-score with no
compensating structural gain), or (ii) apply the CAISO precedent uniformly and withdraw. Option (i)
is the more defensible on this record, but either way the reconciliation should be **written**,
because the two precedents currently contradict each other and gate (a) hangs on which governs.
NYISO's **frontier** status has already returned to the owner on the same promotion.

*Refresh-#8 addendum:* the nyiso-156b ruling (winter intake AUTHORIZED, §0e.2) gives Q5 a live
structural resolution path — the card's §4 measures that winter-face closure alone returns the
keeper to CALIBRATED, which would re-key the marker onto a CALIBRATED keeper and dissolve the
tension prospectively. The written reconciliation of the two precedents remains worth having (it
governs the next time this fact pattern appears), but Q5 no longer blocks anything this track is
doing: gate (a) is taken as PASS on the literal test throughout.

## 4. Prompt issuance record

| date | lane | branch | model | profile | outcome |
|---|---|---|---|---|---|
| 2026-08-23 | D1 BOARD-REFRESH | `capx-d1-board-refresh` | Opus | code | **LANDED** |
| 2026-08-23 | D2 ADEQUACY — NYISO | `capx-d2-adequacy-nyiso` | Fable→Opus | nyiso | **LANDED** |
| 2026-08-24 | D2-REMEASURE | `capx-d2-remeasure-t1f` | Fable | all | **RETIRED unrun** |
| 2026-08-24 | D2-B I7 LEDGER | `capx-d2b-i7-ledger` | Fable | code | **LANDED** |
| 2026-08-24 | D2-NYISO-INTAKE | `capx-d2-nyiso-extcap-intake` | Fable | nyiso | **LANDED — I7 CLEARED** |
| 2026-08-24 | D5 CROSSOVER CO2 | `capx-d5-crossover-co2` | Fable | pjm | not started; **re-scoped r#5** |
| 2026-08-25 | **D7-NYISO GATE RE-SCORE** | `capx-d7-nyiso-gate` | Opus | code | issued (now also carries A-A) |
| 2026-08-25 | **S-123 MISO ADEQUACY PACKAGE** | `capx-s123-miso-adequacy` | Fable | miso | issued |
| 2026-08-25 | **S-4 NEISO HYDRO ACCREDITATION** | `capx-s4-neiso-hydro` | Fable | neiso | issued |
| 2026-08-25 | **D10 NYISO T1-X** | — | Fable | nyiso | chartered by card A; prompt written 2026-08-25 |
| 2026-08-25 | **D11 ENTRY-SIGNAL PRO-FORMA** | — | Fable | ercot | chartered by card B; prompt written 2026-08-25; **superseded by D11-R at r#8, never run** |
| 2026-08-25 | **S-5 PJM HORIZON-EDGE** | — | Fable | pjm | unblocked by card C; prompt written 2026-08-25; stands ready (heavy, solo slot) |
| 2026-08-30 | **D10 NYISO T1-X (reissued)** | `claude/capx-d10-nyiso-t1x` | Fable | nyiso | r#8 batch — pack corrected for nyiso-155 keeper state; **still unstarted at r#10** |
| 2026-08-30 | **D11-R ENTRY VOLUME RULE** | `claude/capx-d11r-entry-volume-rule` | Fable | ercot | r#8 batch — re-scoped per §0e.3; **RUNNING since r#10** |
| 2026-08-30 | **S-4 NEISO HYDRO (reissued)** | `claude/capx-s4-neiso-hydro` | Fable | neiso | r#8 batch — **LANDED at r#10** (PR #4312, verification pair pending) |
| 2026-08-30 | **S-4V NEISO VERIFICATION** | `claude/capx-s4v-neiso-verification` | Fable | neiso | r#11 batch — new charter (S-4's owed verification half); D10 + S-5 re-presented unchanged alongside it. **All three dispatched by the owner (in flight at r#12)** |
| 2026-08-30 | **Q5-W NYISO MARKER WITHDRAWAL** | `claude/q5w-nyiso-marker-withdrawal` | Fable/Opus | code | r#12 — governance records lane executing the owner's r#12 Q5 ruling (WITHDRAW, CAISO precedent). **LANDED at r#13** (PR #4343) — as did D10 (PR #4354), S-4V (PRs #4337/#4353), S-5 (PR #4340) and D11-R (PR #4355): the whole in-flight set |
| 2026-08-30 | **D13 BOARD RECONCILE** | `claude/capx-d13-board-reconcile` | Fable/Opus | code | r#13 batch — records lane: Q7 execution + S-5 PJM restatement + landed-lane board currency + stale-prose repair |
| 2026-08-30 | **D14 NEISO T1-X CROSSOVER** | `claude/capx-d14-neiso-t1x` | Fable | neiso | r#13 batch — the D10 analog on the new lead ISO; success ⇒ first (a)+(b)+(c) ISO |
| 2026-08-30 | **D12 SCARCITY-CONSISTENT DELTA BASIS** | `claude/capx-d12-scarcity-basis` | Fable | ercot | r#13 batch — released by D11-R's report; feeds the Q8 arming re-decision |
| 2026-08-30 | **S-4b NEISO ARA RE-VINTAGE** | `claude/capx-s4b-neiso-ara` | Fable | neiso | r#13 — prompt written; **dispatch strictly after D14 merges** (shared NEISO surfaces) |
| 2026-08-30 | **D5 CROSSOVER CO2 DERIVATION** | `claude/capx-d5-crossover-co2` | Fable | code (widen as needed) | r#14 — zero-solve three-ISO attribution. **LANDED at r#15** (PR #4374) — as did D13 (PR #4372), D14 (PR #4376) and D12 (PR #4373): the whole wave, second consecutive 100 % cycle |
| 2026-08-30 | **D12-C ARMING CONFIRMATION PAIR** | `claude/capx-d12c-confirm-pair` | Fable | ercot | r#15 batch — Q10 execution: confirm-then-arm, auto-arm on a confirming record |
| 2026-08-30 | **D5-R SCORER COAL-GRAIN REPAIR** | `claude/capx-d5r-scorer-coal-grain` → ran as `claude/crossover-co2-grain-repair-oycsy6` | Fable | code | r#15 batch — Q12 execution: full fix + zero-solve re-score under the pre-declared honesty gate. **LANDED at r#17** (PR #4388, controls verified) |
| 2026-08-30 | **S-4b (released)** + **S-123 (released)** | pack prompts | Fable | neiso / miso | r#15 — S-4b's D14 gate cleared; S-123's start-time check finally passes (miso-190 concluded). **S-4b LANDED at r#17** (PRs #4392/#4396) |
| 2026-08-30 | **CAISO-224-FIN** | `claude/caiso-224-fsno-finisher` | Fable | code | r#17 — owner-requested (Q14) backcast-track completion, boundary exception recorded; zero-solve. **LANDED PR #4415 (r#19 sitting): R per precommit §5, pair registered, matrix stamped, keeper untouched** |
| 2026-08-30 | **T3-NEISO-GOLDEN** | `claude/capx-t3-neiso-golden` | Fable | neiso | r#17 — executes the Q13 authorization: the program's FIRST §2.1b full-horizon campaign (NEISO 2026–2050 BAU golden, ~1.0 h / ~4.3 GB, this campaign only) |
| 2026-08-30 | **S-6 (released, conditional)** | pack prompt | Fable | pjm | r#17 — RELEASED-CONDITIONAL: dispatch strictly AFTER CAISO-224-FIN lands (Q14); no-co-run discipline vs the golden stated in both prompts |
| 2026-08-30 | **D12-A ARMING EXECUTION** | `claude/capx-d12a-arming` | Fable | code | r#18 — executes Q15 (ARM BOTH on the D12-C record judged confirming-in-substance); zero-solve; cache-key verification f061b2646bfaac8b; V-2 miss described honestly; ERCOT cells O → K-forecast-armed |
| 2026-08-30 | **S-6 PJM LEDGER RUN** | `claude/capx-s6-pjm-ledger` | Fable | pjm | r#19 — first pack prompt; released unconditionally (slot doctrine voided); briefly owner-held, then **DISPATCHED** |
| 2026-08-30 | **S-123-V MISO VERIFICATION** | `claude/capx-s123v-miso-verify` | Fable | miso | r#19 — fills S-123 §6; stops-at-start if the original session still runs. **DISPATCHED** |
| 2026-08-30 | **NEISO-RC PHASE-0** | `claude/capx-neiso-rc-phase0` | Fable | code | r#19 — D14 retirement-composition attribution, zero-solve, finding-only. **DISPATCHED** |
| 2026-08-30 | **D16 SEAM GUARD** | `claude/capx-d16-seam-guard` | Fable | code | r#19 — fail-closed refusal on the mc=0 armed-interface seam (director mechanism decision; fallback price deliberately not built). **DISPATCHED** |
| 2026-08-30 | **D8 DOF-LEDGER + PROVENANCE** | `claude/capx-d8-dof-ledger` | Fable | code | r#19 — FC-7 both halves; verdict/board re-emission explicitly deferred. **DISPATCHED — LANDED at r#20 (PR #4427; re-emission still deferred)** |
| 2026-08-31 | **S-6-R (relaunch)** | `claude/capx-s6-pjm-ledger-r2` | **Opus** | pjm | r#20 — pre-declared execution. **LANDED at r#21 (PR #4436): FC-1 FAIL = {I7, I12}** |
| 2026-08-31 | **S-123-V-R (relaunch)** | `claude/capx-s123v-miso-verify-r2` | **Opus** | miso | r#20 — pre-declared execution. **LANDED at r#21 (PR #4441): §6 filled, S-123 complete** |
| 2026-08-31 | **T3-GOLDEN-R (relaunch)** | — | **Opus** | neiso | r#20 — **RECALLED UNRUN at r#21 (owner correction: the original golden session is STILL RUNNING; r#20's LOST grading was wrong)**. Never dispatched; the original T3 issuance (r#17) stays the live lane |
| 2026-08-31 | **D12-A-R (relaunch)** | `claude/capx-d12a-arming-r2` | **Fable** | code | r#20 — orphan-branch adjudication. **LANDED at r#21 (PR #4429): re-verified and armed per Q15, matrix stamped** |
| 2026-08-31 | **NEISO-RC-R REPAIR PHASE** | `claude/capx-neiso-rc-repair` | **Fable** | neiso | r#21 batch — R2+R1+R3(+R4) per the Phase-0 finding; PREREG-first verification pair; golden care lines |
| 2026-08-31 | **D3 MISO RETIREMENT G3** | `claude/capx-d3-miso-retire-g3` | **Fable** | miso | r#21 batch — attribution-first zero-solve Phase 0 on the t1h `retire.total_gw` flip; precommit-first |
| 2026-08-31 | **D4-I3 ERCOT SLACK HALF** | `claude/capx-d4i3-ercot-slack` | **Opus** | ercot | r#21 batch — zero-solve breach-set + pre-declared post-arming expectation; net-revenue half stays HELD (card Y-C); D6 sequenced after it |
| 2026-08-31 | **D8-RE VERDICT/BOARD RE-EMISSION** | `claude/capx-d8-re-emission` | **Opus** | code | r#21 batch (mid-sitting release) — the D8-deferred re-emission, unblocked by the golden/S-6/S-123-V landings; records only, zero-solve |
| 2026-08-31 | **D8-V FC-7 LEDGER COMPLETION** | `claude/capx-d8v-fc7-ledger` | **Fable** | code | r#22 batch — re-verify + publish D8-RE's two STOPPED flips through each affected lane's own record; close the PJM + MISO ledgers; zero-solve. Barred from the legacy-leg run_configs (D20) and from `neiso-t1x`/`neiso-t3`/the ERCOT block |
| 2026-08-31 | **D4-M ERCOT POST-ARMING T1-H** | `claude/capx-d4m-ercot-t1h` | **Opus** | ercot | r#22 batch — grade D4-I3's frozen P-1..P-8 (+F-1..F-4) on the first T1-H at the armed D12-A posture; R-4 instrument grain lands first; a worse I3 is the correct result and may not be repaired in-lane |
| 2026-08-31 | **D17 MISO NON-COAL EXIT CHANNEL** | `claude/capx-d17-miso-exit-channel` | **Fable** | miso | r#22 batch — D3's routed PRIMARY; Phase-0 zero-solve, precommit-first; standing refusal on any FOM/threshold/lag identified from the retirement residual |
| 2026-08-31 | **D18 INVARIANT DECLARATION LEDGER** | `claude/capx-d18-invariant-ledger` | **Opus** | code | r#22 batch — D4-I3's routed R-6: declare the 13 undeclared invariant FAILs (census independently re-derived by the director), correct `dominant_open_causes.I3`, make the standing-red CI job green |
| 2026-08-31 | **D21 FC-6 DRIVER BATTERY** | `claude/capx-d21-fc6-battery` | **Fable** | neiso | r#22 amendment — Q16/Q19 execution, half 1 of the t3 ceiling: run the Tier-1 ladder + paired P1–P3 at the golden's vintage, commit the output, re-score `neiso-t3` FC-6. Price the ladder before running it |
| 2026-08-31 | **D22 FC-5 BENCHMARK CORRIDOR** | `claude/capx-d22-fc5-corridor` | **Opus** | code | r#22 amendment — Q16/Q19 execution, half 2: the `benchmark-corridor` datatype + rubric §6 intake. NO scorer edit (that boundary is what keeps it clear of D8-V) |
| 2026-08-31 | **D19 BOARD RECONCILE 2** | `claude/capx-d19-board-reconcile-2` | **Fable** | code | r#23 batch — released; six stale cross-ISO board facts incl. D8-V's flagged gate cells and the two new PROMOTEs |
| 2026-08-31 | **D23 P1 CARBON-CO2 SIGN FAILURE** | `claude/capx-d23-p1-carbon-sign` | **Fable** | neiso | r#23 batch — D21's routed object; Phase-0 precommit-first attribution of the +52.4 % cumulative-CO2 rise under a carbon price; capacity-side and dispatch-side legs both named, neither presumed |
| 2026-08-31 | **D24 CACHE-KEY OPTIONAL FIELDS** | `claude/capx-d24-cache-key-defect` | **Opus** | code | r#23 batch — D4-M's R-5 upgrade; characterize the blast radius and PROPOSE, fix nothing (a key change invalidates caches program-wide) |
| 2026-08-31 | **D25 FC-5 DISPOSITION TABLE** | `claude/capx-d25-fc5-dispositions` | **Fable** | code | r#23 batch — the t3 ceiling's last step; author dispositions so FC-5 scores, benchmarks stay context and never fit targets |
| 2026-08-31 | **D17-R (relaunch)** | `claude/capx-d17r-miso-exit-channel` | **Fable** | miso | r#23 reissue — nothing had landed; fresh from the committed §D17 charter, with D4-M's ERCOT zero-retirement observation added as a reason to check shared machinery, not as evidence |
| 2026-08-31 | **xiso-cascade (offered, backcast)** | `claude/xiso-cascade-scan` | **Fable** | code | r#23 — carry "a nested cascade must be MAXED, never SUMMED" to five ISOs, preserving the region-vs-duration distinction. **Found and repaired a real MISO defect** |
| 2026-09-01 | **D26 FC-6 P1 ARM CONSTRUCTION** | `claude/capx-d26-p1-arm-construction` | **Fable** | neiso | r#24 batch — D23's routed instrument repair; re-score under cross-lane re-grade. **Charter committed to the pack at r#25 (reconstruction — r#24 issued chat-only)** |
| 2026-09-01 | **D27 MISO T1-H HEAD RE-MEASURE** | `claude/capx-d27-miso-t1h-remeasure` | **Opus** | miso | r#24 batch — D17-R's routed PRIMARY, a solve, against a quantified pre-declaration. **Charter committed to the pack at r#25 (reconstruction — r#24 issued chat-only)** |
| 2026-09-01 | **D28 CAPACITY REVENUE AT LONG POSITIONS** | `claude/capx-d28-longposition-capacity-revenue` | **Fable** | code | r#24 batch — the cross-ISO $0-at-long-position object, Phase-0. **Charter committed to the pack at r#25 (reconstruction — r#24 issued chat-only)** |
| 2026-09-01 | **D24-R CACHE-KEY REPAIR** | `claude/capx-d24r-cachekey-repair` | **Opus** | code | r#25 batch — Q20 execution: (c′)+(b′-1) exactly, zero keys move (the assertion is the lane's own merge gate); no retroactive re-key |
| 2026-09-01 | **D29 TRAJECTORY REPORTING GRAIN** | `claude/capx-d29-trajectory-grain` | **Opus** | code | r#25 batch — D25 §6.1 routed: gen-by-fuel + a real storage column in `extract_trajectory`; additive schema, zero solves, committed summaries not regenerated |
| 2026-09-01 | **D30 45Q CONVERSION PACE** | `claude/capx-d30-45q-pace` | **Fable** | code | r#25 amendment-2 batch (max-parallel census) — D25 §6.4 routed; Phase-0 docs-only with the PJM-primary and STOP-at-capacity-leg seams |
| 2026-09-01 | **nyiso-168 (offered, backcast)** | `claude/nyiso-168-price-gain` (stem suggested; grade by content) | **Fable** | nyiso | r#25 amendment-2 — the nyiso-167 gain object (0.703) worked on NYISO's own data; DO-NOT-REDO discipline on the declined offer-side line |
| 2026-09-01 | **miso-197 (offered, backcast)** | `claude/miso-197-gain-frame` (stem suggested; grade by content) | **Fable** | miso | r#25 amendment-2 — Q21 (iii) execution, unblocked by miso-196's conclusion (PR #4508, arm REJECTED); session picks from CURRENT shard verdicts + lever queue, gain frame recommended. **Ran as `miso-cc-regular-overdispatch` — phase-0 checkpoint landed PR #4510 (grade-by-content)** |
| 2026-09-01 | **D26-S FC-6 ARM SOLVES + RE-SCORE** | `claude/capx-d26s-arm-solves` | **Opus** | neiso | r#26 batch — execute the D26 finding's committed runbook (two paired 25-yr arms at the pinned vintage, paired-invariants scoring, neiso-t3 FC-6 re-score, fill the TBD sections); cross-lane re-grade STOP rule |
| 2026-09-01 | **D31 MISO CAPACITY-REVENUE REPAIR** | `claude/capx-d31-miso-caprev-repair` | **Fable** | miso | r#26 batch — D27-R2/D28-R1, the PRIMARY lever; Q24-funded PRA/RBDC intake; rule-14 sign discipline (sized by published data only, never the residual) |
| 2026-09-01 | **D33 NEISO POSITION LANE** | `claude/capx-d33-neiso-position` | **Fable** | neiso | r#26 batch — D28-R2 (accreditation basis + cleared-vs-qualified), in-repo record only; informs the golden's interpretation (Q25 ran the campaign without waiting) |
| 2026-09-01 | **D26-S** | `claude/capx-d26s-arm-solves` | **Opus** | neiso | r#26 batch — **RETIRED UNRUN** (D26 completed its own runbook, PR #4522, before dispatch) |
| 2026-09-01 | **T3-NEISO-GOLDEN-2** | `claude/capx-t3-golden-2` | **Fable** | neiso | r#26 amendment-1 batch — owner ruling Q25: the second §2.1b campaign, armed posture, own FC-6 battery, preserve-then-overwrite |
| 2026-09-01 | **D34 CARBON_PRICE GUARD** | `claude/capx-d34-carbonprice-guard` | **Opus** | code | r#26 amendment-1 batch — owner ruling Q26: replace semantics + the below-base warning; R4 closed |
| 2026-09-01 | **D20 RECONSTRUCTION PROVENANCE** | `claude/capx-d20-reconstruction-provenance` | **Opus** | code | r#26 amendment-1 batch — released (hold dissolved by D26+D27 landing); §0s.5 decision executed, control-first on the seven legacy legs |
| 2026-09-01 | **D36 STORAGE VALUE-STACK TIMING** | `claude/capx-d36-storage-valuestack` | **Fable** | code | r#27 batch — GOLDEN-2 routed item 1 / D25 §6.3 route; zero-solve decomposition of why armed economics clear nothing before 2050 |
| 2026-09-01 | **T16-A T1.6 RE-POINT** | `claude/capx-t16a-ladder-repoint` | **Opus** | neiso | r#27 batch — Q27 execution; **HELD-DISPATCH until the golden session closes**; honesty clause binds |
| 2026-09-02 | **D35 P2 INSTRUMENT SCOPE** | `claude/capx-d35-p2-scope` | **Fable** | neiso | r#28 batch — released on golden-close + T16-A landing; artifact-only adjudication + repair of the FC-6 P2 leg |
| 2026-09-02 | **D38 D36-ROUTED RECORDS** | `claude/capx-d38-d36-records` | **Opus** | code | r#28 batch — the corridor-row re-author + the golden-2 §6.1 wording correction; records only |
| 2026-09-02 | **D31/D33/D30 RE-EMITTED** | (unchanged stems) | — | — | r#28 — owner-confirmed never dispatched; prompts re-sent verbatim from the pack, charters unchanged |
| 2026-09-02 | **D32 FLOOR-RETENTION MONOPOLY** | `claude/capx-d32-floor-retention` | **Fable** | miso | r#29 batch — unlocked by D31; the non-coal channel's owner; rule 21 forbids a tuned weight |
| 2026-09-02 | **D40 NEISO REQUIREMENT DEVINTAGE** | `claude/capx-d40-neiso-devintage` | **Fable** | neiso | r#29 batch — D33's R-A/R-B; in-repo Net ICRs; default-off + LOYO before any keeper moves |
| 2026-09-02 | **D41 CCS FIXED-COST RE-IDENTIFICATION** | `claude/capx-d41-ccs-fixedcost` | **Opus** | code | r#29 batch — D30's two legs re-identified from the ATB basis (rule 23); no golden re-solve licensed |
| 2026-09-02 | **D39 ENTRY-STACK UNDER-BUILD** | `claude/capx-d39-entry-underbuild` | **Fable** | code | r#29 batch — Phase-0 docs-only; T16-A outcome B + D36 converge; cross-ISO |
| 2026-09-02 | **D37 NEISO T1-H ARMED** | `claude/capx-d37-neiso-t1h-armed` | **Opus** | neiso | r#30 batch — Q28 posture (Net ICR lever ON for measurement, diagnostics on); pre-declared; makes D40's post-wave scoreable |
| 2026-09-02 | **D42 FOSSIL ANNOUNCED-DATE A/B** | `claude/capx-d42-fossil-dates-ab` | **Fable** | miso | r#30 batch — Q29; both legs suffixed; nothing arms without the A/B + the owner |
| 2026-09-02 | **D43 CAISO DISPERSION A/B** | `claude/capx-d43-caiso-dispersion` | **Fable** | caiso | r#30 batch — D39 §7 CAISO-first; the single-term isolation; default-off + matrix duties |
| 2026-09-02 | **D44 FOSSIL-DATES DEFAULT ARM** | `claude/capx-d44-fossil-dates-arm` | **Opus** | code | r#31 batch — Q30 execution: default flip + spec/CLAUDE.md amendment + matrix + CHANGELOG; rule-27 spine |
| 2026-09-02 | **D45 PJM+NYISO CURVES (once-only D6+R3)** | `claude/capx-d45-pjm-nyiso-curves` | **Fable** | pjm | r#31 batch — the joint clearing-half + curve-ON charter for the two untouched capacity-market ISOs; diagnostics-on first solves; own parameters per rule 25 |
| 2026-09-03 | **D44 + D45 re-emission — WITHDRAWN (moot)** | (unchanged stems) | Opus / Fable | code / pjm | r#32 — graded unlaunched at the pin; both landed post-pin (D44 complete; D45 checkpoint). Nothing re-sent. The pack's outside-the-charter D45 vintage note stands (NYISO keeper → nyiso-177). |
| 2026-09-03 | **D46 RE-MEASURE BATCH** | `claude/capx-d46-remeasure-batch` | **Opus** | ercot/caiso/miso/neiso (pjm/nyiso in Stage 2) | r#32 amendment 2 — owner ruling Q32 (staged); Stage 1 executable now, Stage 2 gated on D45's §9 close-out, Stage 3 not dispatched; no controls, no arming, priors preserved |
| 2026-09-04 | **D47 GOLDEN-3 ATTESTATION + D46 RECORDS** | `claude/capx-d47-golden3-attestation` | **Opus** | code | r#33 — pre-declared attestation for the committed GOLDEN-3 bundle (FC-7 restored without a re-solve), the `-pre-d46` caveat table, the `neiso-t1h` posture disclosure; records only |
| 2026-09-04 | **D45-R D45 CLOSE-OUT + D46 STAGES 2/3** | `claude/capx-d45r-pjm-nyiso-close` | **Fable** | pjm, nyiso, miso, neiso (incremental) | r#33 amendment 1 — Q33/Q35: the owed D45 legs at HEAD + the §9 close-out, absorbing Stage 2 and the re-priced Stage 3; priors at `-pre-d45r`; 2 h STOP per t1f leg |
| 2026-09-04 | **D48 PJM ACCREDITATION DEVINTAGE** | `claude/capx-d48-pjm-accreditation-devintage` | **Fable** | pjm | r#33 amendment 3 — D45 §2.3 items 1–2 built default-off + pre-declared now; A/B solve gated on D45-R's PJM legs landing |
| 2026-09-04 | **D49 D46 PHASE-0s (ERCOT CCS + MISO exit margin)** | `claude/capx-d49-d46-phase0s` | **Fable** | code | r#33 amendment 3 — zero-solve on the committed D46 ledgers and diagnostics dumps |
| 2026-09-04 | **D45-R / D47 AMENDED** | (unchanged stems) | Fable / Opus | — | r#33 amendment 3 — D45-R + NEISO dates-OFF control leg + conditional CAISO legs; D47 + the t1f `c_cost` correction; prompts re-emitted whole |
| 2026-09-04 | **D50 CCS CAPEX ∝ CAPTURED CO2** | `claude/capx-d50-ccs-capex-scaling` | **Fable** | ercot, neiso, pjm | r#34 — D49 half 1's three seams, default-off, A/B on three t1f legs, blast radius measured; arming returns as an owner card with the re-measure cost |
| 2026-09-04 | **D51 MISO ACCOUNTING-RATIO RE-IDENTIFICATION** | `claude/capx-d51-miso-accounting-ratio` | **Opus** | miso (+neiso if C-7) | r#34 — D49 half 2, rule-23 re-derivation on the dates-ON fleet, A/B on miso-t1h; records rider |
| 2026-09-04 | **D52 NYISO ADEQUACY DEVINTAGE** | `claude/capx-d52-nyiso-adequacy-devintage` | **Fable** | nyiso | r#34 — D45 §5.2.4 items 1–2, default-off, A/B on nyiso-t1h, curve-ON probe re-run only on the ±3-pt condition |
| 2026-09-04 | **D53 THE SECTOR GATE** | `claude/capx-d53-sector-gate` | **Fable** | miso (pjm gated) | r#35 — D32 C5/R3: design doc first, default-off build, A/B on miso-t1h; PJM leg gated on D48 landing |
| 2026-09-04 | **D54 PJM CLEARING HALF DESIGN** | `claude/capx-d54-pjm-clearing-design` | **Fable** | code | r#35 — D45 §2.3 item 3, design + pre-declaration only; code/solve gated on D48 |
| 2026-09-04 | **D55 RETENTION-KEY FIX + RELEASE PRECISION** | `claude/capx-d55-retention-key-fix` | **Opus** | miso | r#35 — D32 R2 + R4, zero DOF, A/B on miso-t1h, golden-staleness pre-declared |
| 2026-09-04 | **D56 NYISO COMPLETE RE-DECLARATION** | `claude/capx-d56-nyiso-redeclaration` | **Fable** | code | r#35 amendment 1 — owner ruling Q38; records-only; marker + M1 + gate-(a) re-derive + board; no solve, no spend. **NEVER LAUNCHED (r#36); superseded by D56-R** |
| 2026-09-05 | **D50-R D50 COMPLETION** | `claude/capx-d50r-completion` | **Opus** | pjm | r#36 — the owed PJM t1f arm, the §6 blast radius, the §8 recommendation, and the finding the shards already cite; nothing arms |
| 2026-09-05 | **D56-R NYISO COMPLETE RE-DECLARATION (relaunch on nyiso-189)** | `claude/capx-d56r-nyiso-redeclaration` | **Fable** | code | r#36 — D56 fresh from the committed charter on the moved keeper; the frontier limb conditional on card C-10; R-AG/Q38 coexistence recorded |
| 2026-09-05 | **D57 PJM CLEARING HALF — BUILD + A/B** | `claude/capx-d57-pjm-clearing-build` | **Fable** | pjm | r#36 — D54 §7 executed: gated field, Phase-0 instrument reproduction, arms A/B on `pjm-t1h`, seven STOPs, the E&AS operand measured; the D48 arming card rides its result |
| 2026-09-05 | **D58 PJM SECTOR-GATE LEG** | `claude/capx-d58-pjm-sectorgate` | **Opus** | pjm | r#36 — **RELEASED-CONDITIONAL**: after D53 merges AND D57 lands (PJM shard collision); D53 routed item 1 |
| 2026-09-05 | **D59 NYISO LOCALITY HALF** | `claude/capx-d59-nyiso-locality` | **Fable** | nyiso | r#36 — D45 §5.2.4 item 3 / D52 §8 route; design-first (the short-locality curve, not the shipped long-zone collapse); A/B on the D52 posture; the same P9 re-run; the curve-vintage transcription check folded in. **LANDED at r#37 (PRs #4760/#4764): inert on a long NYC census, cell I, DO NOT ARM** |
| 2026-09-05 | **D56-R2 NYISO FRONTIER RE-DECLARATION** | `claude/capx-d56r2-nyiso-frontier` | **Fable** | code | r#37 — owner ruling Q39; records only; keeper-shard `frontier` + marker `frontier_basis`; four-instrument alignment restored |
| 2026-09-05 | **D60 THE ARMING BATCH** | `claude/capx-d60-arming-batch` | **Opus** | miso, nyiso, caiso, neiso (incremental) | r#37 — owner rulings Q40/Q41/Q42 executed flip-first; every bare key pre-declared; t1h renames byte-identical by construction; four re-solves with priors at `-pre-d60`; ≈ 2.2 h sequential; ruff-format hygiene commit first. **CHECKPOINT at r#38 (flip + 4 renames landed; pjm-t1f STOP); Amendment 1 adds the pjm-t1f leg** |
| 2026-09-05 | **D60 AMENDMENT 1** | (same session) | **Opus** | + pjm | r#38 — the owner's "still running" answer: the `pjm-t1f` re-solve at `09996eca71ee80fd` (~28 min, PJM now free) added as the fifth re-solve; prior at `pjm-t1f-pre-d60`; nothing re-issued |
| 2026-09-05 | **T3-NYISO-GOLDEN** | `claude/capx-t3-nyiso-golden` | **Opus** | nyiso | r#38 — owner ruling Q45; **RELEASED-CONDITIONAL on D60's finding landing**; the GOLDEN-2/3 recipe on NYISO's registries; own FC-5 dispositions + FC-6 battery; `nyiso-t3` |
| 2026-09-05 | **D61 PJM E&AS OPERAND — PHASE 0** | `claude/capx-d61-pjm-eas-operand` | **Fable** | pjm (code first) | r#38 — D57 §4's named successor; zero-solve; the denied revenue streams sized against the SOM tables as observables; the D12 channel adjudicated as the home; a build charter, no coefficient |
| 2026-09-05 | **D60 AMENDMENT 2** | (same session) | **Opus** | — | r#39 — the routed P10 STOP resolved under Q37: pre-declare (Addendum D) then author the curated DOF-ledger rows for every field the batch armed; artifact-only re-score of the affected bare keys; FC-7 the only row that may move; priors untouched |
| 2026-09-05 | **D60-R THE D60 RELAUNCH** | `claude/capx-d60r-completion` | **Opus** | caiso, pjm, neiso | r#39 am.1 — the D60 session died after legs 1–2; fresh from §D60 + Am.1 + Am.2: three re-solves, Addendum D + rows + re-scores, finding §5/§8 |
| 2026-09-05 | **D64 THE D50 FOURTH SEAM — PHASE 0** | `claude/capx-d64-ccs-fixedcost-seam` | **Fable** | code | r#40 am.1 — D50 §8 Disclosure 1; zero-solve basis + re-screen + blast radius + D65 charter or closure; D61 re-emitted alongside (still unlaunched) |
| 2026-09-05 | **D60-R2 THE D60 RELAUNCH, RE-ISSUED** | `claude/capx-d60r2-completion` | **Opus** | caiso, pjm, neiso | r#39 am.2 — D60-R NEVER LAUNCHED (no branch / commit at `c3addecc`; R-AK's launch-failure class); same charter, fresh stem, a stops-at-start twin check, push-each-leg |
| 2026-09-05 | **T3-NYISO-GOLDEN AMENDMENT 1** | (pack §T3-NYISO-GOLDEN) | **Opus** | nyiso | r#39 — `complete.NYISO` present at start is a PRECONDITION of Q45; withdrawn ⇒ STOP and route (the pending nyiso-192 promotion) |

## 5. History (compacted)

- **Refresh #1 (08-23):** charter; first state read; D1 + D2-NYISO issued.
- **Refresh #2 (08-24):** D1 landed. Director hypothesised the I7 verdicts sat on a pre-FFR-1C
  HEAD; chartered D2-REMEASURE on it. **Later refuted — see #4.**
- **Refresh #3 (08-24):** no lane started; ercot-233 opened card Y; D9 handed in by miso-183.
- **Refresh #4 (08-24):** Q1 answered (Y-C). D2-NYISO landed and **refuted the pre-fix-HEAD
  hypothesis** — FFR-1C hydro was already inside the FFR-3A-2 verdicts (1,763.3 MW; pre-hydro
  ledger 30,322.2 MW = the board's stale "30.3 GW"). D2-REMEASURE retired unrun; D2-B and
  D2-NYISO-INTAKE issued in its place. Recorded against interest.
- **Refresh #5 (08-25):** D2-NYISO-INTAKE and D2-B landed; **NYISO cleared FC-1**. Cards A/B/C put
  to the owner and **all three signed at the recommendation** the same day (§3).

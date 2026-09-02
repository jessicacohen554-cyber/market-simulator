# Capacity-Expansion Workstream Director — Ledger

Standing coordination ledger for the capacity-expansion (Forecast Finalization Program) track.
Maintained by the director session on branch `claude/capx-director-ledger`; one refresh = one
commit when anything changes. The director charters sessions and tracks state — it never runs
solves, never edits `src/market_sim/`, and never charters backcast-calibration work (that track
is the owner's own CAISO/ERCOT/MISO sessions, watched here for deconfliction only).

**Charter date:** 2026-08-23 · **Last refresh:** 2026-09-02 (refresh #29) ·
**r#29 (HEAD `0a3d22c7`):** ALL FIVE re-emitted/issued lanes LAND (D31/D33/D30/D35/D38) — D31 swings the MISO exit residual to **−74.3 % UNDER on faithful inputs** (rule 14's expected signature, localized sharper than ever) · D33: the NEISO position is a **requirement-denominator VINTAGE artifact** (published Net ICRs already in-repo → D40) · D30: **DEFECT-CANDIDATE on two CCS fixed-cost legs, not 45Q** (→ D41) · D35: **FC-6 leaves the neiso-t3 FAIL set** (now CAVEAT; failing = FC-1..FC-4) · **UNLOCKED AND ISSUED: D32 · D40 · D41 · D39**; D37 held behind D40's arming; D6+R3 deliberately still queued (§0z) ·
*(previous)* **Last refresh #28:**
**r#28 (HEAD `1aa8ac14`):** D36 answers the storage question — **the ARBITRAGE leg is short in every year by $50–150/kW-yr; the RA leg is second-order and IS the D28/D33 position object** · T16-A lands outcome B — **NEISO's RPS is unreachable at every stack-built VRE volume** (REC dual at the $50 ACP ceiling in all 50 arm-years), battery row CAVEAT-measured · **MISO PROMOTES `2026-09-01-miso-198-oomlevel`** (no criterion status moves — structural improvement without gate movement) · D31/D33/D30 were NEVER DISPATCHED (owner-confirmed; prompts re-emitted) · D35 released, D38 issued (§0y) ·
*(previous)* **Last refresh #27:**
**r#27 (HEAD `a2e80dbf`):** GOLDEN-2 REGISTERED — verdict HOLD, **FC-7 PASSES (first on any golden)**, FC-6 FAIL on the NEW P2 only, storage entry survives arming as a −56.2 % divergence (720 MW iron-air, 2050 only); Q25 SPENT · D34 + D20 LANDED · T1.6 deleted under rule 26 and **Q27 re-points it to `entry_rate_limits`** · D36 issued; T16-A held for golden-close; D35/D37 named-queued (§0x) ·
*(previous)* **Last refresh #26:**
**HEAD at refresh:** `8462da22` — the nine-writer wave lands 7-of-9 with two clean mid-lane checkpoints (§0w.1); **D27 vindicates D17's arithmetic and refutes it as a remedy — coal ate all 14.7 GW** (§0w.1); CAISO promotes caiso-231 (§0w.5); the Q22/R-H duplication recorded AGAINST INTEREST (§0w.2); Q24 funds the MISO PRA/RBDC intake; D26-S/D31/D33 issued (§0w.4) · **Owner cards A/B/C SIGNED 2026-08-25; Q20–Q23 r#25; Q24 r#26** (§3)
**Handoff prompt for a successor director session:** `docs/handoffs/capx-director-handoff-2026-08-30.md` (base r#21 prompt + r#22 delta + r#24 amendment + **r#25 delta**; the ledger wins where they diverge)

---

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
| **D32 FLOOR-RETENTION COMPOSITION MONOPOLY** | D27's R5, now D31's routed residual owner: `_floor_retention_merit` makes exit composition a pure FOM ranking whenever the floor binds — vs a real cohort that is emphatically not FOM-rank-ordered (3 large gas steamers + a 158-unit tail) | **ISSUED r#29 (unlocked by D31)** | `claude/capx-d32-floor-retention` | Fable | Rule 21 forbids a tuned retention weight; the −74.3 % UNDER residual is context, never the identifier. |
| **D33 NEISO POSITION LANE** | D28's R2: accreditation basis + cleared-vs-qualified | **LANDED** PR #4569 — accreditation basis (approximately) PUBLISHED-FAITHFUL; **the +21/+6/+7 is a REQUIREMENT-DENOMINATOR VINTAGE artifact** (published per-CCP Net ICRs already in-repo); census supply actually SHORT of real cleared | `claude/capx-d33-neiso-position-8e9nzk` | Fable | §0z.1. Routes R-A/R-B → D40 (rule-28 duties, default-off, LOYO before any keeper moves). |
| **T3-NEISO-GOLDEN-2 (second §2.1b campaign)** | Owner ruling Q25: NEISO BAU 2026–2050 at HEAD with the R-A-armed storage posture, its own FC-6 battery at its own vintage, full-rubric scoring, preserve-then-overwrite | **REGISTERED** PRs #4532/#4543/#4546/#4548 (session still open at r#27 — surfaces reserved) — **HOLD; FC-7 PASSES (first golden ever); FC-6 FAIL on the NEW P2 only (P1 PASSES natively, −14.7 % CO₂ under +$25/t)**; storage: 720 MW iron-air at 2050, NOTHING 2026–2049 — the −56.2 % divergence family SURVIVES arming; 35.1 min/3.48 GB, DOF 7/0, FC-5 re-dispositioned 54/0. **Q25 SPENT** | `claude/capx-t3-golden-2-tm9eiy` | **Fable** | §0x.1. Four routed items → D36 (issued) · D35/D37 (queued) · a D33 cross-read. |
| **D35 P2 INSTRUMENT SCOPE** | Re-scope the FC-6 P2 gas leg | **LANDED** PR #4574 — re-scoped to **the model's gas partition**, pre-statement before the repaired checker, artifact-only re-score; **FC-6 LEAVES the neiso-t3 FAIL set** (HOLD on {FC-1..FC-4}; FC-5 + FC-6 both CAVEATs) | `claude/capx-d35-p2-scope-b5x2by` | **Fable** | §0z.1. Both t3 instruments now fully scored, neither blocking. |
| **D36 STORAGE VALUE-STACK TIMING** | GOLDEN-2 routed item 1 (the D25 §6.3 route): why the armed economics clear NOTHING before 2050 | **LANDED** PR #4559 — **the ARBITRAGE leg is short in EVERY year by $50–150/kW-yr; the RA leg is second-order and IS the D28/D33 position object** (two mechanisms, one seam); three rule-13 routes + the procurement-channel DISPOSITION; zero solves | `claude/capx-d36-storage-valuestack-gmelow` | **Fable** | §0y.1. Routes → D38 (records), D39 (named), D37 precondition (`entry_screen_diagnostics`). |
| **D38 D36-ROUTED RECORDS** | The corridor-row re-author + golden-2 annotation | **LANDED** PR #4568 — rows re-authored (no category/verdict moved), annotation in, staleness check + blob verification recorded | `claude/capx-d38-records-wfzdfx` | **Opus** | §0z.1. Done. |
| **D39 ENTRY-STACK UNDER-BUILD** | T16-A outcome B + D36 arbitrage-short converge: the entry stack under-builds vs both the RPS constraint and the corridor | **ISSUED r#29 (unlocked by D31+D33)** — Phase-0, docs-only, cross-ISO | `claude/capx-d39-entry-underbuild` | Fable | Not a storage lane, not an RPS lane; one mechanism question across every screen. |
| **D40 NEISO REQUIREMENT DEVINTAGE** | D33's R-A/R-B: resolve the NEISO adequacy requirement from the published per-CCP Net ICR series (already in-repo) instead of the flat single-vintage composite, the PJM-FPR pattern; R-B companion | **ISSUED r#29** | `claude/capx-d40-neiso-devintage` | **Fable** | Rule-28 duties (matrix row + shard cells, default-off); scored LEAVE-ONE-YEAR-OUT per rule 22 BEFORE any keeper moves. D37 waits on this lane's arming decision. |
| **D41 CCS FIXED-COST RE-IDENTIFICATION** | D30's two defective legs: `fixed_om_gas_cc_ccs` re-identified so the capture island is CHARGED not paid, `ccs_retrofit_capex_kw` re-cited on the ATB-2024 basis (dollar-year stated) | **ISSUED r#29** | `claude/capx-d41-ccs-fixedcost` | **Opus** | Rule 23: the re-derivation cites the ATB data, never the residual or the corridor. Screen-grain measurement only — NO golden re-solve is licensed (Q13/Q25 this-campaign-only stand). |
| **D37 NEISO T1-H AT ARMED POSTURE** | GOLDEN-2 routed item 4: FC-3's evidence carries the pre-arming leg; re-run the capacity hindcast at the armed posture | **QUEUE CONDITIONS MET at r#29, HELD one beat** — D40's requirement devintage belongs IN this re-run; waits on D40's arming decision; carries D36's `entry_screen_diagnostics` precondition | — | Opus | A solve; pre-declaration-first when chartered. Running it before D40 arms would measure a vintage about to change. |
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

## 2. Backcast-track watch (last seen 2026-09-02 @ `0a3d22c7`, refresh #29)

| item | state |
|---|---|
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

## 3. Owner-tier questions — TWENTY-SEVEN ANSWERED (Q5/Q6 r#8; Q5 re-ruled r#12; Q7/Q8/Q9 r#13; Q10/Q11/Q12 r#15; Q13/Q14 r#17; Q15 r#18 — all 2026-08-30; Q16/Q17/Q18/Q19 r#22, 2026-08-31; Q20/Q21/Q22/Q23 r#25 + **Q24/Q25/Q26 r#26 + Q27 r#27**, 2026-09-01. Q22 carries an r#26 primacy correction — audit ruling R-H ruled the same card first; see §0w.2)

Full signature record and the consequences adopted:
**`docs/DECISION-CARD-capx-director-open-rulings-2026-08-25.md` §5** (cards A/B/C/Y);
Q7–Q9 were ruled via in-session decision cards at r#13 and are recorded here + in §0j.3
(execution of Q7 = lane D13).

| # | question | resolution |
|---|---|---|
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

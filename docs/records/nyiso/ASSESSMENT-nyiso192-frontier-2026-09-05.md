# ASSESSMENT nyiso-192 — NYISO frontier status, re-assessed for card C-10 / Q39: every object opened since nyiso-154 enumerated and dispositioned; the top-of-queue object was THREE-QUARTERS an instrument artifact; the one live lever found was A/B-solved; and the honest verdict on the mechanism set is given below, with the one thing that stands between it and a safe declaration named

Session nyiso-192, 2026-09-05. This supersedes
`ASSESSMENT-nyiso154-frontier-2026-08-22.md` as the live NYISO frontier
statement. **Keeper at entry and at exit: `2026-09-05-nyiso-189-steam-identity`
— CALIBRATED** (C1 14/14 free 10/10; C2 / C3a / C3b / C4 / C6 / C8 PASS; C3a
+4.9 % / +1.7 % / −8.3 %; C3b 0.119 / 0.166 / 0.177; C1-2024 `CC_REGULAR`
+3.33 TWh / +2.8 pp against 3.0 pp; C3c the lone ledgered caveat at 3 / 0 / 4 h
vs RT 10 / 13 / 42), re-verified artifact-only in this session after its
payload was re-rendered (`calibration_verdict.py --run-id`: CALIBRATED, 1
ledgered caveat), `audit_keepers --iso NYISO` PASS. **Markers:** `complete.NYISO`
HELD and keyed to this keeper (D56-R; the D-5(b) duty was already discharged —
nothing re-keyed here); `final` empty; the locked-test freeze active and
unspent — every year solved, scored or read in this session is 2023–2025.
**Frontier: WITHDRAWN (2026-08-30) and NOT re-asserted here** — the declaration
is an owner act (card C-10 / Q39, unruled at HEAD); this assessment is written
to be citable as its basis either way.

**What this session did** (pre-registered and pushed before any solve:
`PREREG-nyiso192-frontier-adjudication.md` §0–§7): decomposed the two objects
nyiso-191 handed forward WITHOUT an LP; found and repaired an instrument defect
in the dashboard payload; replayed the keeper in place as the control
(bit-identical); re-rendered the keeper's payload on the repaired instrument;
found ONE live admissible lever while enumerating the record and A/B-solved it
(§3.3); and measured, on the current keeper, the C8 exposure nyiso-181
escalated. Solves: one in-place control replay + one arm. Records:
`docs/FINDING-nyiso192-frontier-adjudication-2026-09-05.md` and the
`_nyiso192_*.json` machine records under `results/calibration/`.

## 1. The owner's definition, applied — and why enumeration, not assertion

The standard is the owner's own: **"we have tested everything we could have."**
nyiso-154 (§1) satisfied it by closing four named lane items and showing the
remaining open set was owner-court plus the ledgered C3c. Since then thirty-odd
sessions (nyiso-155 → 191) opened, measured and closed objects, the keeper moved
eight times, the marker was withdrawn (Q5-W: a `complete` marker cannot stand
on a NOT-YET keeper — a keeper regression, not a collapse of the merits) and
re-declared (D56-R, on a CALIBRATED keeper), and the frontier fell with the
marker. nyiso-190 and nyiso-191 then opened objects that cut against the
exhaustion premise. §2 gives every one of them a disposition with its citation;
§3 reports the three things this session found that change the picture; §4
gives the verdict and the recommendation for Q39.

Vocabulary (fixed in the pre-registration §4): **CLOSED** (measured or solved
to a K / repaired input), **REJECTED** (tested and refused on a pre-registered
record — R or I), **INADMISSIBLE-BLOCKED** (cannot be identified or represented
at the current representation without an owner act — G or an identification
intake), **OWNER-HELD** (a decision only the owner can make), **LEDGERED**
(C3c), **STILL OPEN** (a lever a lane could test and has not).

## 2. The complete object set since nyiso-154 — every item dispositioned

| # | object (opened) | disposition | evidence |
|---|---|---|---|
| 1 | **Sithe Independence 54547 duty object** (nyiso-191 §6.1: "+3.19 / +3.48 TWh, CF 0.93 / 0.97 vs 0.62, un-owned") | **INADMISSIBLE-BLOCKED — and CORRECTED 3×.** The published magnitude was an INSTRUMENT ARTIFACT (§3.1): the LP over-run is **+0.17 / +1.04 / +1.31 TWh** (CF 0.66 / 0.88 / 0.94 vs 0.63 / 0.76 / 0.78 on available capacity). The `chp_layup_duty_curve` census rule declines it CORRECTLY (0 of 18 zero-median cells, online share 0.844, `operating`); a duty curve for a live merchant CC would pin conduct (rule 13). The residual is level-when-on with all four trains on at ~80 % of HSL; **half of 2024's** sits in hours where the model was in merit but the actual Zone-C price was below the plant's own SRMC (the compression / trough object, owner-court), and the rest is unidentifiable in-repo: no F923 delivered-gas filing, and a regulation / reserve reservation the representation does not carry (NYCA reserve families hydro-saturated at zero dual, nyiso-152) | `_nyiso192_sithe_duty_phase0.json`; FINDING §2 |
| 2 | **`ST_GAS` zonal placement** (nyiso-191 §6.3: NYC over, LI / CH under, sign-stable) | **TWO NAMED OWNERS, NEITHER A LANE LEVER.** NYC over ← the zonal delivered-gas basis (NYC steam at the Transco Z6 NY hub, $0.70–1.38 below the Iroquois Z2 reference; on the reference basis NYC in-merit share 0.31–0.53 → 0.04–0.12): a measured input (SOM Fig. A-6, reproduced by the repo's own monthly series) whose plant-specific basis for the three NYC steam plants is UNFILED (no F923) → **identification intake (OWNER-HELD)**; the only in-repo alternative (the LDC-delivered daily index the CT leg uses) is **REFUSED EX ANTE** — it shifts NYC steam by $34–53/MWh to an in-merit share of 0.4–1.1 %, leaving the class ~100 % floor-forced → C8 fails by construction → the market's NYC steam dispatch is out-of-market commitment → **cell G (INADMISSIBLE-BLOCKED)**. LI / CH under ← out-of-market commitment (nyiso-187, `b ≥ 0.50` in every downstate cell) + the compressed downstate premium (model LI −$2.9 / −$9.7 vs actual; C3a-2025 owner-court Q1). Ravenswood's heat-rate term is CLOSED (nyiso-185 K: 12.906 committed, the highest NYC steam HR). The Astoria-panel repair (row 10) is the one lever that reaches this pattern and it was solved | `_nyiso192_stgas_zonal_decomp.json`; FINDING §3 |
| 3 | **nyiso-190 plant-grain ±8 TWh misallocation** (nyiso-190 §3) | **INSTRUMENT DEFECT, CORRECTED**: gross over 11.9 / 11.3 / 11.2 → **8.4 / 7.0 / 6.9 TWh**; offsetting 7.4 / 8.2 / 9.3 → **8.4 / 7.0 / 6.9**. The non-CHP rows stand (Ravenswood +3.13 / +1.74 / +0.84 is the fleet's largest over-run in 2023 / 2024); the CHP rows are re-stated (Linden 50006 flips to −0.90 / −1.15 / −1.28 UNDER). The object shrinks by a third and does not vanish; what remains is dispositioned through rows 1, 2, 9, 10 | `_nyiso192_payload_addback_audit.json`, `_nyiso192_plant_grain_rerendered_keeper.json` |
| 4 | **`CC_CHP` widening of `cc_capacity_reconcile`** (nyiso-190 §4 → nyiso-191) | **REJECTED (R)** on rule 19 — `chp_layup_duty_curve` owns the class and binds tighter at all six cohort members; B2 held; no gate moved | FINDING-nyiso191 §3; matrix cell |
| 5 | **Pooled CT-only test dilution** (nyiso-191 §3.1 / §6.2) | **OWNER-HELD (cross-ISO derive lane)** — affects every ISO's `cc_capacity_reconcile` table; a rule-23 per-year test; not NYISO's to change unilaterally (rule 25) | FINDING-nyiso191 §3.1 |
| 6 | **C3a-2025 −8.3 %** | **OWNER-HELD** — DECISION-CARD-nyiso148 Q1, confirmed still pending; the year-invariant 0.70 price-response gain (nyiso-167) is a slope deficit whose one new mechanism is provably LP-inert (nyiso-168); the 2025 top-decile deficit decomposes 62 % onto the model's price level (nyiso-179) | nyiso-148 card; FINDING-nyiso167/168/179 |
| 7 | **Cell G `scuc_load_pocket_commitment`** | **INADMISSIBLE-BLOCKED** — nyiso-97 §5 forbids identifying it from observed unit conduct; the nyiso-160 access closure stands; nyiso-163 built the on-receipt gate; the owner-executable AORR fetch (INTAKE-SPEC-nyiso156 Leg 2) is the only route. Rows 2 and 8 land on it | nyiso-97/160/163/187/190 |
| 8 | **CT deficit / out-of-market commitment** (nyiso-170 → 175 → 187) | **INADMISSIBLE-BLOCKED (G)** + the owner-accepted CT markup trade; both East River gates failed on their pre-registered thresholds (nyiso-175); the crosswalk defect was probe-side (nyiso-174) | FINDING-nyiso175/187 |
| 9 | **D-2 / C8 grain under-count** (nyiso-181 §6) | **OWNER-HELD (scorer lane, cross-ISO) — NOW MEASURED ON THE CURRENT KEEPER (§3.2):** at unit grain, with D-2's own `at_floor_mask`, `ST_GAS` reads **0.393 / 0.414 / 0.305** forced against the committed plant-grain C8 of 0.197 / 0.236 / 0.183 and the 0.30 cap — every year above the cap. The determination's C8 PASS is instrument-dependent. Re-basing the scorer is code-generic across six ISOs and is not this lane's to do (rule 25); rule 20's escalation path (D-4 provenance + D-1 shape) would then decide | `_nyiso192_c8_unit_grain_keeper.json` |
| 10 | **Astoria merit-panel stack-duplicate defect** (nyiso-184 §4.1; carried unbuilt through nyiso-185…191) | **ADJUDICATED — A/B-SOLVED, OWNER CALL (§3.3).** The panel priced Astoria 8906's paired flue paths as two units at half their heat (SRMC halved inside the guard); repaired at one call site (the canonical normalizer's own correction), the extract re-derived under the keeper's committed invocation moves **106 Astoria windows out and 155 windows at fifteen OTHER plants in** — the guard's revealed clearing cost is built from Astoria's rows, so the whole steam fleet's availability moves (Ravenswood 2024 0.478 → 0.260, Arthur Kill 2024 0.907 → 0.453, Astoria 0.24 → 0.51, Northport 2023 0.527 → 0.368). Armed: every B2 prediction HELD; **C2 / C3a / C3b / C8 no flip** (C3a +4.8 / +3.2 / −7.3 %; C3b 0.118 / 0.172 / 0.167; C8 `ST_GAS` 17.1 / 23.8 / 18.6 %); **C1-2024 `CC_REGULAR` flips PASS → FAIL (+3.33 → +3.68 TWh, +2.8 → +3.0 pp)** so the arm reads NOT-YET (C3c no longer lone). Structural integrity: better in 2024 / 2025 (plant-grain offsetting 6.98 → 6.24, 6.92 → 6.41; Ravenswood 2024 +1.74 → +1.04, Arthur Kill 2024 +0.78 → −0.01, Ravenswood 2025 +0.84 → −0.01), worse in 2023 (8.41 → 8.67; Northport −0.63 → −1.11). The flip's root cause is the fill landing on `CC_REGULAR` — cell G. **Not rejected under the pre-registered rule; the call is the owner's (card §4).** Keeper unchanged; the repaired extract is bundle-local; the committed extract stays the keeper's pinned input | PREREG §7; FINDING §4; `nyiso192_astoria_panel` |
| 11 | **C3c** (summer downstate scarcity) | **LEDGERED** — the rubric v3.3 standing rule; its own diagnosis (nyiso-164); reported at full magnitude on every determination | keeper `determination_note` |
| 12 | **Winter downstate locational premium** (nyiso-154 item 2 → 156/158/160/161/163/167) | **RE-CLASSIFIED and closed as a distinct object**: 87.4 % of the "winter face" is the year-invariant price-response gain (row 6), the winter-specific residue is −$0.51/MWh (nyiso-167); the waiver card was RULED Option A (R-H / Q22) and retired; the AORR route stays owner-executable (row 7) | FINDING-nyiso167; DECISION-CARD-nyiso161 |
| 13 | **Congestion gradient** (nyiso-169) | **CLOSED / G** — four consistently-signed link terms cancel; ≥98.3 % of measured congestion forms with every posted interface off its limit; `measured_interface_limits` refused on NYISO's own measurement | FINDING-nyiso169 |
| 14 | **CC availability over-statement** (nyiso-172/173) | **REJECTED (I)** — real as a bound violation, provably inert as a lever (the model never reaches its CC envelope) | FINDING-nyiso173 |
| 15 | **`CC_CHP` hard floor** (nyiso-171) | **REJECTED** — a portfolio artifact; the class over-runs in 80 % of 2025's hours, which forbids every floor mechanism | FINDING-nyiso171 |
| 16 | **Un-dispatched in-the-money `ST_GAS`** (nyiso-179/180/181) | **CLOSED** — an artifact of the offer reconstruction; all four explanations close; the per-generator dispatch limit lifted | FINDING-nyiso180/181 |
| 17 | **Ravenswood availability / heat-rate basis** (nyiso-177/183/184/185) | **CLOSED** — availability refuted on its pre-registered gate (nyiso-183; the guard's classification sound on the evidence it was given); the 9.50 hand number replaced by the eGRID family rate, promoted K (nyiso-185). NB row 10 re-opens the guard's INPUT on new evidence, never its rule | FINDING-nyiso183/184/185 |
| 18 | **Astoria Energy II eGRID default / Astoria routing / ramp footprint / Bethlehem HR** (nyiso-186/187/188/189) | **CLOSED with keepers** — identity HR (186), split-facility routing (187), ramp + v2 emission footprint and `cc_capacity_reconcile` (188), `egrid_steam_collapse_heat_rates` (189). Bethlehem now sits ABOVE its CAMPD actual in all three years (nyiso-190 §6.3) — no in-merit headroom left; closed | FINDING-nyiso186–190 |
| 19 | **Input-artifact reproducibility gap** (nyiso-176) | **CLOSED** — attributed and wired; the extract re-derives byte-identically under its committed invocation (this session re-derived it) | FINDING-nyiso176/177 |
| 20 | **AS reference repair** (nyiso-165/166) | **CLOSED** — reference repaired, independently verified | FINDING-nyiso165/166 |
| 21 | **Zonal loss surface / PAR attribution / hydro repair** (nyiso-155/157/159) | **CLOSED (K)** — all three armed on the keeper lineage | matrix cells |
| 22 | **Zeltmann 56196 cold-weather record vs the pooled p99.9 cap** (nyiso-188 §, 21 h at up to 682 MW above a 560 MW cap in 2024) | **OBSERVATION, no admissible lever named** — a derive-rule question inside a cross-ISO frozen rule (rule 23 / 25); immaterial to every gate (≤ 0.01 TWh) | FINDING-nyiso188 |
| 23 | **NYISO parasitic factors absent; the v2 emission artifact's frozen 2018 / 2022 / 2026 rows** (nyiso-188) | **OBSERVATIONS, data notes** — no solve-affecting lever; carried | FINDING-nyiso188 |
| 24 | **Hydro 10-min AS certification + hour-by-hour water limit; CC cycling-cost identification; Q2 annotation** (nyiso-154 items 3–5) | **OWNER-HELD intakes**, unchanged (the certification item scoped only as the future `nyiso_spin_reserve_online` unlock) | ASSESSMENT-nyiso154 §2 |
| 25 | **`final` (locked-test) readiness** | **NOT-YET on the merits**, unchanged (2019 unsolvable at HEAD; cannot discriminate on C3c); a separate question from frontier | ASSESSMENT-nyiso154 §2 item 6 |
| 26 | **Forecast lane: eGRID 2025** | not a backcast object; carried (vintages through `egrid2024_data.xlsx` only) | nyiso-189 handoff |

Items settled since nyiso-154's table: the winter premium (re-classified, row 12),
the RAMP10 seams (inert, unchanged), the `online_rho` pair (R / G, unchanged),
the reserve-cohort duty (K, unchanged).

## 3. The three things this session found

### 3.1 The top-of-queue object was three-quarters an instrument artifact

`render_calibration_html`'s model-payload CHP add-back used the 35 % sector share
while the LP, under `nyiso_chp_btm_measured`, held out the MEASURED share (0 % at
Sithe). Every NYISO cogen's dashboard series carried `e_ann × 35 %` of flat
phantom energy — 6.6 TWh across the `CC_CHP` class in 2024, 2.14 TWh at Sithe
alone — on top of an LP that never dispatched it. Class totals and every gate are
untouched (C1 scores bundle class totals); what was wrong is the per-plant record
nyiso-190 and nyiso-191 built their objects on. Repaired at the call site
(`measured=_btm_run_measured`, the run's own hold-out; pinned by a source-reading
test), the keeper replayed in place (every committed sidecar byte-identical) and
its payload re-rendered: non-CHP plants byte-identical, the CHP class identity
closing to ≤ 0.0001 TWh, the pre-registered predictions for Sithe (+0.18 / +1.04
/ +1.31) and for the plant-grain totals (8.4 / 7.0 / 6.9) both HELD. The
fourteen other registered NYISO payloads still carry the defect (their slim
bundles have no dispatch parquet to re-render from) and are flagged, not
rewritten.

### 3.2 The keeper's C8 PASS is instrument-dependent

nyiso-181 §6 measured the D-2 plant-grain under-count on the superseded
nyiso-177 keeper and escalated it. On the current keeper's own unit-hourly
dispatch and floors, with D-2's own `at_floor_mask`, `ST_GAS` is forced at
**0.393 / 0.414 / 0.305** of its energy — every year above rule 20's 0.30 cap
that the committed plant-grain C8 reads as 0.197 / 0.236 / 0.183. The
mechanism is exactly the one nyiso-181 named: a unit pinned at its own floor
inside a plant whose other units run freely vanishes from the plant-total test
(Ravenswood's eight steam tranches beside its seven CC units). This is a
scorer-instrument fact, code-generic across six ISOs, and not this lane's to
re-base (rule 25); a re-based C8 breach would escalate to the rule-20 provenance
+ shape path, not fail automatically. It is reported here because a frontier
declaration's "CALIBRATED" limb would otherwise rest on a number the owner has
not seen.

### 3.3 The one live lever, adjudicated

The Astoria merit-panel stack-duplicate defect (nyiso-184 §4.1) was carried
unbuilt through seven sessions as "needs its own A/B on that lane". Under §4's
rule it alone forced NO, so it was adjudicated here (PREREG §7, pushed before
the arm). The repair is one call site — `build_merit_order_panel` now applies
the CAMPD stack-duplicate helpers `campd._normalize_campd` already applies, so
Astoria 8906's `31RH`/`32SH` and `51RH`/`52SH` pairs enter the guard as one
generator at its physical SRMC (panel HR 5.5 → 11.0). Re-derived under the
keeper's committed invocation the extract is NOT an Astoria-only change: 106
Astoria windows leave (its steam primaries lose most of their booked outages —
they were economic lay-ups priced as mechanical) and **155 windows at fifteen
other plants enter**, because the guard's revealed clearing cost is the
capacity-weighted p90 SRMC of the RUNNING units and Astoria's rows are in it.
Mean availability (the engine's own builder): Ravenswood `ST_GAS` 0.786 / 0.478
/ 0.309 → 0.786 / **0.260 / 0.121**; Arthur Kill 2024 0.907 → 0.453; Astoria
0.177 / 0.240 / 0.330 → 0.367 / 0.509 / 0.462; Northport 2023 0.527 → 0.368;
Roseton 2025 0.755 → 0.357. The pre-registration's own "Astoria-only" premise
was wrong and is recorded as such.

**The arm** (`2026-09-05-nyiso-192-astoria-panel`; control = the keeper itself,
bit-identical; G-DELTA `[]` — zero config change, the artifact alone; computed
attestation `gen_nyiso192_attestation.py`, six checks): every B2 prediction
HELD (Astoria rises in all three years, 0.62 → 0.98 / 0.66 → 1.21 / 1.16 → 1.48
TWh; Ravenswood falls in 2024 / 2025, 2.42 → 1.73 / 1.91 → 1.06, and is flat in
2023, +0.02; Roseton 2025 falls). **No rejection-rule flip**: C2 PASS, C3a
+4.9 / +1.7 / −8.3 % → **+4.8 / +3.2 / −7.3 %**, C3b 0.119 / 0.166 / 0.177 →
0.118 / 0.172 / 0.167, C8 `ST_GAS` 19.7 / 23.6 / 18.3 → 17.1 / 23.8 / 18.6 %
(unit grain 0.393 / 0.414 / 0.305 → 0.369 / 0.403 / 0.287). **C1-2024
`CC_REGULAR` flips PASS → FAIL: +3.33 → +3.68 TWh, +2.8 → +3.0 pp against the
3.0 pp band** — the 0.81 TWh of `ST_GAS` the repaired envelope removes in 2024
lands 0.35 on `CC_REGULAR` and 0.28 on `CC_CHP`; the arm therefore reads
NOT-YET (target grade 6, fails 2: C1 and C3c, the latter no longer lone).
Structural integrity is **mixed and stated at full magnitude**: the plant-grain
offsetting misallocation improves 6.98 → 6.24 (2024) and 6.92 → 6.41 (2025) —
Ravenswood 2024 +1.74 → +1.04, Arthur Kill 2024 +0.78 → −0.01, Ravenswood 2025
+0.84 → −0.01, the `ST_GAS` NYC over-run +2.24 → +1.31 and +0.41 → −0.07 — and
regresses 8.41 → 8.67 in 2023 (Northport −0.63 → −1.11 on its lowered 2023
envelope; NYC +4.26 → +4.60). Load-weighted price +0.7 $/MWh in 2024 / 2025
(C3a-2025 −8.3 → −7.3 %).

**Disposition: ADJUDICATED — the lever is no longer untested; the call is the
owner's** (pre-committed outcome "C1 flip only → owner call"). Rule 14 says the
repaired panel is the accurate input and the C1 regression is a discovered
root-cause issue — and the root cause is named: the fill lands on `CC_REGULAR`
because the market's NYC / LI steam dispatch is out-of-market commitment (cell
G, owner-closed). What the owner should weigh: promoting the arm under the
standing formula puts a **NOT-YET** keeper under the `complete` marker, which
the uniform Q5-W rule does not allow — the marker would fall again. The keeper
is therefore left unchanged, the committed extract stays its pinned input (so
it remains reproducible from committed bytes), the repaired extract and both
availability tables are preserved bundle-local, and the code repair ships
(byte-identical for every other ISO: the stack-pair registry is `{8906}`).

## 4. The frontier answer

> **THE ADMISSIBLE MECHANISM SET IS EXHAUSTED AT THE CURRENT REPRESENTATION — YES.**
> Every object opened since nyiso-154 carries a disposition with a citation
> (§2): closed or rejected on its own pre-registered record, identification-
> blocked or G-blocked at the current representation, owner-held, or ledgered.
> The one live lever the enumeration found (row 10) was A/B-solved in this
> session and is no longer untested; the two un-owned OBSERVATIONS (rows 22–23)
> name no admissible lever and are immaterial to every gate. No `O` / `U` cell
> in the NYISO column carries an admissible in-repo identification.
>
> **BUT A FRONTIER DECLARATION IS NOT RECOMMENDED NOW**, for two reasons that
> are the owner's to rule, not the lane's to solve:
> 1. **The keeper's "CALIBRATED" limb rests on an instrument the record now
>    contradicts** (§3.2): at unit grain, with the committed scorer's own mask,
>    `ST_GAS` is forced 0.393 / 0.414 / 0.305 against a 0.30 cap in every year.
>    A declaration made over that number would repeat the nyiso-130 pattern (a
>    claim falsified in the record it stands on). The scorer lane's re-base, or
>    the owner's explicit acceptance of the plant-grain instrument, comes first.
> 2. **The last adjudicated lever awaits its call** (row 10): the accurate
>    input flips C1-2024 and the arm reads NOT-YET; promoting it costs the
>    `complete` marker under Q5-W, holding it leaves the keeper on a pre-repair
>    input. Either is a legitimate owner ruling; a frontier declared before it
>    would be declared over a keeper the owner may be about to change.
>
> The declaration itself is an owner act. This assessment supports Q39 option
> (B) of the decision card — rule the two items, then re-declare on this
> assessment with no new solve — and is written to be citable for (A) or (C)
> as well.

What makes this different from nyiso-154's YES: the exhaustion premise was
re-enumerated over thirty-seven sessions, the top-of-queue object was shown to
be three-quarters an instrument artifact and the instrument repaired, and the
one lever that could have made the answer NO was solved rather than argued
around. What makes it weaker: the CALIBRATED limb is now known to be
grain-dependent, and that is stated here rather than discovered later.

**Addendum, nyiso-193 (2026-09-05, later the same day).** The owner ruled Q39 at r#37
(card C-10, option A) before this assessment was served, and D56-R2 executed it: `frontier`
is DECLARED on `2026-09-05-nyiso-189-steam-identity` at `origin/main`
(`docs/handoffs/FINDING-capx-d56r2-nyiso-frontier-2026-09-05.md`). §4's recommendation
stands as the lane's record; its two named conditions — the D-2 / C8 grain (§3.2) and the
Astoria-panel arm (§3.3, card question nyiso192-Q1, unruled) — are now conditions on the
declared frontier's durability. The successor records: the intake spec for the NYC steam
delivered-gas basis (`docs/INTAKE-SPEC-nyiso193-nyc-steam-delivered-gas-2026-09-05.md`) and
the scorer-lane card on re-basing D-2 / C8 to unit grain
(`docs/DECISION-CARD-nyiso193-d2-unit-grain-2026-09-05.md`).

## 5. What a ratified declaration would and would not claim

* It WOULD claim: the NYISO backcast lane has exhausted its admissible mechanism
  set at the current representation — every lever adjudicated on a pre-registered,
  solve-backed or provably-no-solve-needed record, with rejections and keepers
  alike standing on the dashboard and the matrix; the keeper is the most
  structurally faithful configuration tested (rule 1), CALIBRATED, with one
  ledgered limitation.
* It would NOT claim: that C3c is closed (ledgered, 3 / 0 / 4 vs 10 / 13 / 42);
  that the NYC steam fleet's delivered-gas basis or the load-pocket commitment
  is represented (both identification-blocked, rows 2 and 7); that the
  plant-grain misallocation is closed (6.9–8.4 TWh of offsetting error inside
  a pinned gas family, dispositioned but real); that C8 would pass at unit grain
  (§3.2 — it would not, on the committed scorer's own mask); that any
  out-of-training year has been touched (none has); or that `final` readiness
  follows (it does not, row 25).

*(nyiso-192, 2026-09-05.)*

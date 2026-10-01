# FINDING — caiso-278: **NO-GO. The staged ablation was ALREADY SOLVED, at full LP, eighteen sessions ago.** Its price footprint is a committed measurement — **+0.062 / +0.037 / +0.031 $/MWh**, i.e. **1.2–3.6 % of the object** — so the mechanism cannot be the carrier, and two standing DO-NOT-REDO items forbid proposing it as a C3a lever by name. **ZERO LP SPENT, ZERO SHARDS LAUNCHED.**

**Session caiso-278, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). No arm, no
`ScenarioConfig` field, no bundle, no run registered, no keeper changed in any ISO, no cell
verdict moved.** The charter this session inherited is
`docs/PRECOMMIT-caiso278-chp-offer-ablation-2026-09-12.md` (staged by the prior sitting at
`65c8e467`, banner: *"STAGED, NOT EXECUTED"*). It is **VOIDED, not executed** — annotated in
place, never rewritten.

---

## §0 — THE DECISION, AND WHY IT IS NOT A JUDGEMENT CALL

The charter put a genuine question: is ~20 min of LP worth pure diagnostic information, given
its own §5 concedes the arm **cannot be promoted in either direction**? That question never
had to be answered on taste, because **rule 29 `[R-SCREEN]` step 0 was not discharged**: *"An
arm that has a computable pre-solve gate does not reach a solve until that gate passes"*, and
it names the offer-array delta as the canonical ~90 s kill.

Discharging it took minutes and returned a stronger answer than a gate. **The exact A/B the
charter stages — `caiso_offer_surface_measured_ungrounded` armed versus off — was solved at
caiso-231 (2026-09-01), on three years, at full LP, with every gate scored and the prediction
pre-registered and pushed before either arm started.** The arm's result is not a forecast to
be measured; it is a committed number in this repository.

**NO-GO.** The charter is voided on measurement, not on cost.

## §1 — THE KILL: the ablation's own A/B, from the committed record

`results/calibration/FINDING-caiso231-ungrounded-offer-regrounding-2026-09-01.md` §3 — the
measured LP effect of arming this flag (the ablation is its mirror, to first order):

| year | first-order prediction (caiso-230 §H) | **MEASURED, solved** | ratio |
|---|--:|--:|--:|
| 2023 | +0.235 | **+0.062 $/MWh** | 0.26× |
| 2024 | +0.344 | **+0.037 $/MWh** | 0.11× |
| 2025 | +0.421 | **+0.031 $/MWh** | 0.07× |

Arming **raised** the annual load-weighted price by 0.03–0.06 $/MWh (C3a +4.0 → +4.1 %,
+12.45 → +12.55 %, +15.50 → +15.59 %). Ablating it therefore **lowers** price by about the
same, and the caiso-231 finding says why the first-order bound over-predicted 4–13× and that
it was not luck: *"when CC_CHP's econ ramp gets dearer the margin moves to the next-cheapest
rung instead, so the price rises far less than the offer did"*, with the re-dispatch measured
(**CT_CHP −0.30 TWh/yr displaced by CC_REGULAR +0.12…+0.19 and CC_CHP**).

The nine bands the ablation would move, from the same finding's §2 (armed → off):

| class | band | armed (measured bucket) | off (ERCOT-lineage) | ablation move |
|---|---|--:|--:|--:|
| CC_CHP | econ_low / econ_high / peak | 1.066 / 1.072 / 1.386 | 0.960 / 1.120 / 2.250 | −9.9 % / +4.5 % / **+62.3 %** |
| CT_CHP | econ_low / econ_high / peak | 1.145 / 1.166 / 1.166 | 1.200 / 1.200 / 1.400 | +4.8 % / +2.9 % / **+20.1 %** |
| ST_GAS | econ_low / econ_high / peak | 1.145 / 1.166 / 1.166 | 1.050 / 1.400 / 4.200 | −8.3 % / **+20.1 %** / **+260.2 %** |

## §2 — THE MAGNITUDE: the mechanism is ~1 % of the object it was proposed to carry

caiso-277's object is the 2023–2025 common-window bias, **+0.534 MMBtu/MWh, t = +4.03**. Those
are precisely the years caiso-231 solved, so no extrapolation is needed for the load-bearing
comparison:

| year | flag's measured $ effect | C3a gap (caiso-277 §2) | **share of gap** | dHR contribution | **share of +0.534** |
|---|--:|--:|--:|--:|--:|
| 2023 | 0.062 | +1.72 | **3.6 %** | +0.0069 | **1.3 %** |
| 2024 | 0.037 | +2.90 | **1.3 %** | +0.0086 | **1.6 %** |
| 2025 | 0.031 | +2.65 | **1.2 %** | +0.0066 | **1.2 %** |

**The largest marginal carrier's offer channel accounts for ~1 % of the bias it was staged to
explain, measured on the very years the bias lives on, by a solved LP.** That is the charter's
own §5 "the bias does NOT move" branch — reached at zero LP, on three years instead of one,
and with a number instead of a verdict.

## §3 — THE FIVE PRE-REGISTERED GATES WERE ALREADY ANSWERED, OR COULD NOT HAVE FIRED

| charter gate | status before any solve |
|---|---|
| **G-IDENT** (exactly one field moves) | Already verified at caiso-231, twice: *"exactly 9 bands change, 0 committed bands, 0 non-target classes"*, pre-solve and re-verified on the solved `run_config`. |
| **G-FOOT** (confined to the three classes) | Same measurement. `CC_REGULAR` / `CT_PEAKER` are arms of the *static* half and are untouched by this flag by construction (`_ungrounded_source` maps three keys). |
| **G-LIVE** (must not be inert) | Already **PASS**: max \|Δ\| **1,225 / 3,368 / 1,911 MW class-hour**, plus the −0.30 TWh/yr CT_CHP re-dispatch. The `I` verdict this gate exists to catch was foreclosed; the arm would have returned a known number. |
| **G-DIR** (bounded, stated direction) | Already characterised: the first-order bound over-predicts 4–13× because λ does not follow the repriced rung. |
| **G-COLLAT** (no load-bearing flip) | Already scored at caiso-231: G-C1 12/12 unchanged, G-C3b PASS, G-C2/C4/C8 PASS, falsifiers F1–F6 none fires. |

**Not one gate could have returned information the committed record does not already carry.**

## §4 — THE ONE THING 2022 WOULD HAVE ADDED, SIZED — AND IT ARGUES THE SAME WAY

caiso-231 solved 2023–2025, not 2022, so the charter's screen year is genuinely un-measured.
Sized on the charter's own §3 footprint basis (2022 $105.05 M against 2023 $88.27 M):

* footprint-scaled: **0.062 × 1.19 ≈ 0.074 $/MWh = 0.8 % of the +9.58 $/MWh gap**;
* with a **10× margin** for LP non-linearity: **0.74 $/MWh = 7.7 %** — and a 10× *under*-
  prediction would be a reversal of the only measured behaviour of this estimator class, which
  over-predicted by 4–13× in all three solved years.

**Disclosed against the kill, because it is the strongest argument the other way.** There is
one channel by which 2022 could behave qualitatively rather than proportionally differently:
the ablation raises the `ST_GAS` **peak** wall 1.166 → 4.200 (+260 %) and `CC_CHP` peak
1.386 → 2.250 (+62 %), and 2022 is the high-gas, high-price year in which scarcity walls bind
hardest. So 2022's response could exceed the footprint scaling.

**It strengthens the kill rather than weakening it, in both directions at once.** Raising those
walls moves 2022's price **UP**, away from the failing C3a and away from the bias; and the
walls being raised are exactly the ERCOT-lineage values rule 25 `[R-ISO-SCOPE]` condemned and
caiso-231 retired. The more live the arm turns out to be in 2022, the more emphatically
un-promotable it is — which is the charter's §5 conceded in advance, now with a mechanism
behind it.

## §5 — THE ARM IS ALSO FORBIDDEN BY NAME, TWICE OVER (rule 28(a))

This is not a `U` cell. `caiso_ungrounded_class_regrounding` is **`K`** in
`docs/codebase-site/data/mechanism-matrix/CAISO.js` — armed in the keeper, with its adverse
direction disclosed in the cell text. Two standing DO-NOT-REDO items name the proposal:

* **caiso-231 §8 item 2** — *"**Never propose this mechanism as a C3a lever** (caiso-230
  DO-NOT-REDO item 3, carried). It COSTS C3a +0.06 / +0.04 / +0.03; it is a rule-14/25
  structural repair and nothing else."*
* **caiso-231 §8 item 1** — *"Never re-test the three un-grounded classes' band level. They are
  now measured and armed."*

The charter staged this mechanism **against the C3a-2022 / dHR object**, which is the
proposal both items refuse; an ablation is a re-test of the band level, which is item 1. The
`_CAISO_OFFER_CURVE` consumer comment carries the same warning at the call site:
*"DISCLOSED DIRECTION: this makes C3a worse by a measured +0.235 / +0.344 / +0.421 $/MWh
(caiso-230 §H); it is a structural-integrity repair, **never a C3a lever**."*

**New evidence is what rule 28(a) requires to re-open an adjudicated cell, and caiso-277's
finding is not evidence on this question.** That the bias is CAISO-specific, systematic and
low-variance re-points the *search*; it says nothing about this mechanism's *magnitude*, which
is the only thing that could reopen the cell — and the magnitude is measured at ~1 %.

## §6 — WHAT THE CHARTER GOT RIGHT, AND WHAT IS VOIDED

**Voided:** §2 (the arm), §4 (the gates), §7 (the shard report) — the plan, and only the plan.

**Standing, untouched, and still the prior sitting's real product:** §1's five pre-solve kills
(the `caiso_import_hub_prices` "defect" REFUTED at its own gate; the static import ladder as
the wrong baseline; border carbon CORRECT; `caiso_asymmetric_path_ratings` already armed; the
CHP *heat rates* wrong-signed at `model_over_measured` p50 0.697, > 1 in 0 of 37) and §3's
footprint table, which this finding uses in §4. **Rule 28(a) covers all five: do not re-test
them.** This finding adds a sixth to the same list — the CHP/ST_GAS **offer** channel, killed
on its own solved A/B rather than on a fresh measurement.

## §7 — WHERE THE SEARCH RE-POINTS (open question, NOT a lever — rule 1 `[R-STRUCT]`)

Named because the closure would otherwise hide a lead, and **selected by nothing here**:

The offer channel is now spent on measurement, not on opinion — caiso-276 spent it including
CT_CHP, and §2 above bounds the remaining CHP/ST_GAS half at ~1 %. **caiso-277's second
signature is the one that survives: CAISO's dHR sd is 0.794, the LOWEST of seven ISOs, against
1.40–2.17 everywhere else.** An offer multiplier is a *conditional* price channel — it can only
move λ in the hours its class is marginal — so it produces scatter, not a low-variance offset.
A **small, always-on, structural posture** is what produces the measured signature.

CAISO's own keeper stamp already names such an object, and it is a **commitment/seam** object
rather than an offer one: *"SUCCESSOR OBJECT: CAISO COMMITMENT, not the import offer — the
belly gas deficit (model 1.5 GW vs actual 7.2 GW, 2024 lowest net-load decile) and the reversed
seam direction (model +2 GW import vs actual −1 GW export) are UNREPAIRED, and Arm A's
rejection proves neither is reachable from the import offer."* Both limbs are always-on,
CAISO-exclusive (no other ISO carries a WECC import seam at that scale), and of the right sign
to be read as a candidate — the model under-commits cheap in-basin gas in the belly and imports
into the same hours. Sizing them is **unmeasured**, and it is the next charter's job if there
is one.

The caution caiso-277 §6.4 attached carries forward unchanged: four ISOs sit *below* actual in
their latest year (ERCOT −6.85 %, PJM −7.77 %, NYISO −7.27 %, MISO −6.20 %), so anything that
lowered marginal offers program-wide pushes all four further out. Whatever is done must be
CAISO-scoped, which rule 25 requires anyway.

## §8 — DISCLOSURES AGAINST INTEREST

1. **The charter this session voided was written by the immediately prior sitting of this lane,
   and it stopped one step short of its own rule.** Rule 29 step 0 names the offer-array delta
   as the kill that precedes a screen; the charter wrote §3's footprint table (a *sizing* of the
   mechanism) and then went to gates without asking whether the mechanism's *price* effect was
   already on the record. It was, in the keeper's own lineage, disclosed at the consumer's call
   site and in the matrix cell text. **The lesson is caiso-277's own, one turn later: a premise
   is not measured until it is re-read** — and here the re-read was of this lane's own keeper.
2. **The mirror-image assumption is stated, not hidden.** caiso-231 measured arming; the charter
   staged ablating. Treating one as the negative of the other is exact only to first order — an
   LP is not symmetric about its own solution. What makes it safe here is the *scale*: the arm
   would have to be **~30–80× larger** in the ablation direction than in the arming direction to
   reach even a quarter of the object, and the measured non-linearity ran the other way (the
   bound over-predicted 4–13×). §4 discloses the single channel by which 2022 could break the
   proportionality, and that channel is adverse.
3. **This session spent no LP and therefore proved nothing new about CAISO.** Its entire product
   is a correct reading of committed artifacts. That is the cheapest useful outcome available,
   and it is also the weakest kind of evidence — it inherits every limitation of caiso-231's
   solve, including that the A/B ran on the *caiso-220-era* keeper, not the current
   `2026-09-12-caiso-275-gascoupling`. **Stated plainly: the flag's footprint has not been
   re-measured on the current keeper.** It is not worth a solve to do so — the intervening arms
   (egrid family, gas coupling) do not touch these three classes' bands, and no keeper change
   since caiso-231 moved the offer surface — but the number is, strictly, one keeper stale.
4. **Rule 15 `[R-DASHBOARD]` raises no duty**: zero LP ⇒ no bundle ⇒ nothing to register.
5. **Rule 28(b) moves no cell verdict.** This session armed and tested nothing; it read a solved
   A/B. The only matrix edit is an **evidence append** to the CAISO
   `caiso_ungrounded_class_regrounding` cell recording that the ABLATION direction is now killed
   too, verdict unchanged at **K**.
6. **Rules 32 / 33 are discharged vacuously.** No shard was launched, so there is none to
   archive and no shard branch to delete. The parent spent zero LP, as rule 32(a) requires of it
   in any case.

## §9 — A LIVE GATE FAILURE FOUND WHILE CLOSING OUT, REPORTED AND **NOT** SILENTLY FIXED

`scripts/check_registry_payload_parity.py` is **RED on `main` right now**, on five bundles.
Three are CAISO's, and they are the residue of caiso-275's own promotion:

```
results/calibration/caiso275_B_gascoupling_2023   (48 MB, 11 files tracked)
results/calibration/caiso275_B_gascoupling_2024   (91 MB, 13 files tracked)
results/calibration/caiso275_B_gascoupling_2025   (87 MB, 14 files tracked)
```
(the other two — `nyiso227_rebasis_span`, `spp36_2025` — belong to other lanes and are not
touched here, rule 25.)

These are the per-year shard legs that composed into the registered keeper
`caiso275_B_gascoupling_span`. They are **tracked** (force-added past `.gitignore`'s
`results/calibration/*/*.parquet` rule, the shard pattern), which is why gitignoring them does
not clear the gate — the checker enumerates the filesystem, and rule 32(d) required them to be
kept out of `main` in the first place.

**The load-bearing fact, measured:** the registered `_span` composite carries **no `dispatch/`
layer and no bundle-root `system.parquet`** — only `hourly/` sidecars. So these three legs hold
the **only per-plant record** (`dispatch/<year>_P1.parquet`) of the current CAISO keeper's
2023–2025 solves.

Each of the gate's three suggested exits fails for a different reason, so this is an owner call
and is left as one:

* **prune** — greens the gate, and destroys the keeper's only per-plant layer. Rule 15 does
  sanction this (*"a keeper replay is justified only for unit-level questions"*), so it is
  defensible; but it is a deletion of a result, and rule 31 `[R-RETAIN]` says the owner rules.
* **register** — refused by rules 16 / 29(2) / 32(d): per-year legs are never registered
  separately; the composite is the run.
* **`KEEP_REQUIRED_UNMAPPED_BUNDLES`** — **not available**, by the gate's own stated rule: *"A
  dir with solve output — parquet, metrics, an attestation — NEVER enters, however it is named
  or cited."* The allowlist has been deliberately empty since the 2026-09-05 keeper-only prune.

**Nothing was deleted and nothing was allowlisted.** Greening the gate from this lane is
impossible anyway — two of the five failures are other ISOs' — so the honest action is the
report. Recommendation, if a decision is wanted: **prune the three legs**, on the ground that
the owner has already ruled on promotion (2026-09-12, *"Promote arm b then"*), the legs are
superseded by the registered composite, and rule 15 routes unit-level questions to a replay.

## §10 — THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`), AND THE DECISION CARD

**There is nothing to promote: no arm was solved and no bundle was produced.**

Local, un-pushable state that will **not** survive container reclamation, stated because rule 31
requires the question asked rather than tidied away — no action is requested and nothing has
been deleted:

* `results/calibration/caiso275_B_gascoupling_{2022,2023,2024,2025,span}` and
  `caiso271_egrid_family_{2022,span}` are on local disk. The `271` pair is the superseded
  predecessor keeper, retained (per the handoff) only to reverse the caiso-275 promotion without
  a re-solve. **Correction to the handoff's own description: these are partly TRACKED, not
  gitignored** — which is §9's finding, and it means the committed slim files survive
  reclamation while the gitignored heavy layers do not.

**The card, with (a) now removed by measurement:**

1. ~~**Launch the ablation.**~~ **KILLED** — §§1–5. Already solved, ~1 % of the object,
   forbidden by name twice.
2. **CLOSE THE LANE.** CAISO is **CALIBRATED** on 2023–2025 with its single ledgered C3c;
   **23 of 24 keeper-years in the program pass C3a**, the sole exception being the folded
   CAISO-2022 rung, which rule 30(c) `[R-TOUCHPOINT-FOLD]` says never downgrades the ISO. This
   finding *is* that closure if you want it to be, and the lane's in-model lever queue has now
   measured empty from caiso-200 through caiso-278.
3. **RE-POINT AT THE COMMITMENT/SEAM OBJECT** (§7) — the belly gas deficit and the reversed
   seam direction, which the keeper's own stamp already names as the successor and which match
   caiso-277's low-variance signature in a way an offer multiplier structurally cannot. The
   zero-LP half (sizing both limbs from the committed `class_hourly` / `network_*` sidecars) is
   a parent-only session with no shard; only a confirming A/B would need LP.
4. **The §9 parity decision**, which is independent of 1–3 and is the only item here with a live
   CI consequence.

This session recommends **3 with 2 as its fallback**: the lane is closeable today on the record,
and if it re-opens, the honest object is commitment, not offers.

## §11 — RULE LEDGER

| rule | discharge |
|---|---|
| 1 `[R-STRUCT]` | No lever selected, no mechanism proposed, nothing tuned. §7 names an open question; §10 hands options to the owner. The kill is on magnitude and provenance, never on "the residual didn't move". |
| 14 `[R-ACCURATE]` | The kill *protects* a measured input: the ablation would revert nine measured band multipliers to ERCOT-lineage estimates, which this rule forbids. |
| 15 `[R-DASHBOARD]` | Zero LP ⇒ no bundle ⇒ no registration duty. |
| 25 `[R-ISO-SCOPE]` | CAISO only. No other ISO's keeper, log, shard or bundle touched — including the two non-CAISO parity failures in §9, which are reported and left. |
| 28(a) | **The operative rule.** The cell is `K` with a solved footprint and two DO-NOT-REDO items naming this proposal; caiso-277's finding is not new evidence on its magnitude. §6 carries all five of the charter's kills forward. |
| 28(b) | No verdict moves (nothing armed or tested). Evidence-only append to the CAISO `caiso_ungrounded_class_regrounding` cell, verdict unchanged at `K`. |
| 29 `[R-SCREEN]` | **Step 0 discharged, and it killed the arm** — which is the rule working as written: *"An arm that has a computable pre-solve gate does not reach a solve until that gate passes."* No screen was spent; clause (c) has no bundle to govern. |
| 30(c) `[R-TOUCHPOINT-FOLD]` | The folded CAISO-2022 rung's C3a miss is reported and downgrades nothing; the ISO's determination remains the 2023–2025 verdict. |
| 31 `[R-RETAIN]` | **Nothing deleted** — not the parity-red legs (§9), not the predecessor bundles (§10). The promotion question is asked explicitly and the ephemerality stated. |
| 32 `[R-SHARD]` | Parent spent zero LP; no shard launched. |
| 33 `[R-SHARD-ARCHIVE]` | Vacuous: no shard launched, none to archive, no shard branch to delete. |

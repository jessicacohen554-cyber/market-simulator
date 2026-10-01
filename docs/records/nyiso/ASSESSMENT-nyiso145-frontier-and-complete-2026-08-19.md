# ASSESSMENT nyiso-145 — frontier re-declaration, the `complete` posture, and the hydro-ramp blocker re-scoped

Session nyiso-145, 2026-08-19. Keeper at HEAD **`2026-08-18-nyiso-144-layup-exclusion`**,
unchanged — **nothing was promoted this session and no keeper shard was touched.**

---

## 0. THE ANSWER

* **Frontier: NOT-YET, and this session moves it FURTHER AWAY — by discovery,
  not by regression.** nyiso-144 assessed that the queue had "changed kind": four
  enumerable items, none of them open investigation, and a re-declaration
  "reachable in one more session once items 1, 2 and 4 are ruled on". That
  premise **no longer holds.** Job 3 found two lane-sized *modelling* objects
  that were not on the queue and are not decisions anyone can rule on — a CC
  over-cycling defect and a merit-order inversion inside CC_REGULAR (§2).
  Declaring frontier now would assert that NYISO's remaining queue holds no
  model-side work, which is false at HEAD.
* **`complete`: HELD, unchanged, and NOT re-keyed — correctly.** Rule 22 D-5(b)
  re-keys on a *promotion*; there was none. The entry's determination was
  nonetheless **re-verified from committed artifacts** this session and reads
  **CALIBRATED** (§3).
* **`final`: NOT PROPOSED.** The nyiso-142 / -143 record stands, and this session
  re-verified its live leg at HEAD rather than restating it (§4).
* **The item-1(a) data blocker is REAL but MUCH NARROWER than recorded** — the
  machine-capability half is already on disk, and two of the three obstacles are
  lane-sized code seams rather than a purchase (§5). This is surfaced, not acted
  on: no rho row was derived, no RAMP10 table was touched, no flag was armed.

---

## 1. THE FOUR ITEMS, RE-ASSESSED

| # | object | nyiso-144 status | status at the end of nyiso-145 |
|---|---|---|---|
| (a) | NYISO hydro 10-minute deliverable ramp | data intake; owner funding/scope; **the critical path** | **RE-SCOPED into three parts, only one of which is a purchase** (§5) |
| (b) | the `RHO_CLIP` band | owner D-5(b) | **DECISION CARD DELIVERED**, ruling pending (§6) |
| (c) | plant 7314's bridge over-run | lane-sized, offer/economics | **DIAGNOSED, and it dissolves into two BIGGER objects** (§2) |
| (d) | `nyiso_iroquois_winter_spread` arming + taxonomy | owner ×2 | **UNTOUCHED, and confirmed unchanged at HEAD** (§7) |

---

## 2. ITEM (c) — WHY IT MOVES THE FRONTIER VERDICT AGAINST RE-DECLARATION

Full record: `FINDING-nyiso145-cc-overcycling-and-d4-vintage-2026-08-19.md`.
The handoff's framing — "the bridge's single largest remaining D-4 unit-conduct
failure … an offer/economics defect" — was right that it is not a membership
defect, and wrong about its size and location in both directions.

**Smaller than framed, as a plant.** On the complete EIA-923 vintages plant 7314
is **1.01× (2023)** and **1.18× (2024)** of its metered net. Its 2025-only D-4
conviction is a **data-vintage artifact**: it is a CT-only CEMS reporter, the
rider's protective `ct_only` skip suppressed it in 2023–2024, and that skip
**cannot fire in 2025** because the preliminary EIA-923 vintage supplies no
`e_ann` (the ratio computes to exactly 1.00). C1 guards that vintage by name;
D-4's conduct rider has no vintage guard.

**Bigger than framed, as a fleet object.** Separating the probe's run-pattern
statistics from its energy ratios splits the residual into two distinct defects,
neither of which is a decision anybody can rule on:

* **(A) The big committed CCs are over-cycled.** Bethlehem Energy Center: **262–302
  model starts a year in runs of median 5–9 h**, against **5–7 real starts** in
  runs of median **487–1,217 h** and a metered on-share of 0.92–0.95. It is the
  fleet's largest bridge-floor consumer (779 / 490 / 485 GWh) *and* still
  **0.34×** of its 923 net at P1 in 2023. The defect survives into P1, the scored
  pass.
* **(B) Mothballed small CCs are run at 25×–225× their metered output.** Sterling
  **225×/130×**, Batavia **69×/114×**, Allegany **43×/33×**, Massena **27×/46×**,
  on-share 0.87–0.99 model against 0.01–0.07 metered — with **zero bridge floor**,
  because the nyiso-144 lay-up membership correction already removed it.

**(B) carries a direct implication for how the previous keeper reads.** The
nyiso-144 correction was right and its D-4 improvement is real, but the
manufactured energy at those plants **did not go away — it changed category from
*forced* to *economic*,** where D-2 and D-4 do not look. "D-4 unit-conduct
failures 17 → 3" measures the forcing, not the dispatch.

Both (A) and (B) are lane-sized model-side work needing their own
pre-registrations. **Their existence is the reason frontier cannot be
re-declared**, and it is a better reason than the one it replaces.

---

## 3. `complete` — THE POSTURE, STATED EXPLICITLY

**HELD. Not re-keyed, and no re-key was owed.** Rule 22 D-5(b) requires the
`complete` entry to track the ISO's *current designated keeper* and to be
re-verified **on promotion**. No promotion occurred: the keeper shard,
`calibration-complete.json` and every registry sidecar are byte-untouched by this
session.

**Determination re-verified anyway, from committed artifacts, no solve**
(`scripts/calibration_verdict.py --run-id 2026-08-18-nyiso-144-layup-exclusion`):
**CALIBRATED** under rubric v3.4 — C1 / C2 / C3a / C3b / C4 / C6 / C8 all PASS,
C3c the lone non-passing criterion, auto-ledgered under rule 22's C3c standing
rule (1 ledgered caveat, budget 1 of 1). Unchanged from nyiso-144.

*(A reader should not be alarmed by the bundle's own `metrics.json` reading
`NOT-YET` with reason "governance gate UNATTESTED": that file was written before
the attestation was added to the bundle, and the live scorer — which reads
`calibration_attestation.json` — returns C6 **PASS** and the determination
**CALIBRATED**. The keeper shard's determination note is correct.)*

**What `complete` authorizes here: nothing this session used.** It authorizes the
validation touchpoints (2022, and the ladder to 2020) and **the holdout spend
freeze suspends that authorization**. The freeze is `active: true` and unspent.
Every year solved, scored or read anywhere in this session is 2023, 2024 or 2025.

---

## 4. `final` — NOT PROPOSED, AND ONE LEG RE-VERIFIED AT HEAD

The nyiso-142 NOT-READY verdict and nyiso-143's re-verification stand, and this
session adds nothing to the case for a grant. It does re-check the live leg
rather than restate it:

* **H1-2026 remains unsolvable on the frozen keeper config.**
  `data/raw/NYISO-AS/requirements/` holds `NYISO_reserve_requirements_{2022,
  2023, 2024, 2025}.csv` — **2022–2025 only, no 2026 file** — against a loader
  that RAISES rather than falling back. Re-verified at HEAD this session.
* **2019** — unchanged: Indian Point 2/3 absent from every `eia860_generator*`
  vintage, one actual RT hour above $300 (so it cannot discriminate on C3c), and
  `data/raw/lmp-data/NYISO/` holds no 2019 file.
* NYISO's locked test is **NEVER GRANTED**, not spent (rule 22's D-23
  correction). Nothing here should be read as proposing it.

---

## 5. ITEM (a) — THE HYDRO-RAMP BLOCKER, RE-SCOPED (SURFACED, NOT ACTED ON)

nyiso-144 named this the critical path and typed it as *"a NYISO AS certification
/ capability-data intake — an owner funding and scope decision"*, on the ground
that NYISO hydro *"has NO CEMS and carries NO entry in
`fleet.RAMP10_FRAC_BY_GROUP` / `_BY_FUEL`, so its 10-minute headroom is a
COVERAGE GAP, not a measured zero."* Both halves of that are true at HEAD and are
re-confirmed here. **What is new is that the gap decomposes into three parts, and
only the third is a purchase:**

**(a1) The machine-capability half is ALREADY ON DISK, and it is not marginal.**
EIA-860 Schedule 3.1 reports `Time from Cold Shutdown to Full Load` per
generator, and for New York hydro:

| category | generators | nameplate MW |
|---|---:|---:|
| **`10M`** (full load within 10 minutes) | **331** | **5,689.9** |
| `1H` | 90 | 231.6 |
| `12H` | 3 | 1.4 |

**96.1 % of NY hydro nameplate is reported by the respondent itself as reaching
full load inside the 10-minute window.** That is the same field the repo already
curates as the `fast_start_mw` leg of the `ramp-capability` clean datatype, and
it is the same evidence class behind `RAMP10_FRAC_BY_GROUP`'s `CT_PEAKER = 1.00`
("simple-cycle fast-start, full in <10 min").

Two corroborating facts, both already in the repo: CAISO's
`CAISO_HYDRO_RAMP10_FRAC = 1.0` is grounded in **NREL WWSIS-2 / NREL/TP-5500-55588
App. H — "the same published source family as `fleet.RAMP10_FRAC_BY_GROUP`'s
thermal classes"**, i.e. class physics rather than a CAISO measurement; and its
stated reason for being ISO-scoped — *"only the CAISO design admits hydro
reserve"* — is **falsified at HEAD by NYISO's own keeper**, which arms
`nyiso_hydro_reserve_eligible` (nyiso-144 already noted this).

**(a2) Three LANE-SIZED SEAMS, which no amount of data can get past today.**

1. `fleet.withholding._ramp10_capability` applies the measured reconciliation
   only `if measured and frac > 0.0`. Hydro's class fraction is `0.0` (it is in
   neither table), so **a populated `ramp-capability` row for a NYISO hydro plant
   would be ignored.** The gate is structural, not a data gap.
2. `scripts/lib/ramp_capability/` carries `caiso.py`, `miso.py`, `pjm.py` and
   **no NYISO module**, so the datatype cannot be built for NYISO at all.
3. `ScenarioConfig.measured_ramp_capability` is **`False` on the keeper**, so
   even a built and reachable datatype would not be read.

**(a3) What genuinely remains unmeasured — and it is the part that matters.**
`10M` establishes the *machine*; a reserve product needs *deliverable energy*.
Conventional hydro's 10-minute headroom is bounded by water, not by governor
speed: a run-of-river unit at full flow has no headroom whatever its ramp rate,
and NYISO's own certification would reflect that. So the open questions are
(i) how much of that capability NYISO **certifies** as 10-minute reserve, and
(ii) the hour-by-hour water limit above the model's existing hydro min-flow
floors and monthly budgets. **That is the AS-certification intake, and it is
still an owner funding/scope decision.**

**Explicitly NOT done here**, per the handoff: no NYCA-wide `rho` row was
derived, no `RAMP10_FRAC_*` entry was added, `nyiso_spin_reserve_online` keeps
its `I`, and nyiso-110 §10's prohibition on measuring through the gap is
respected. The point of §5 is that the blocker the owner is being asked to fund
is **narrower and cheaper than the record says**, not that it is gone.

---

## 6. ITEM (b) — THE `RHO_CLIP` RULING, PREPARED NOT TAKEN

`docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md`. Headline: **all three
measured `online_rho` rows that exist in the repo** — NYISO's two and MISO's,
across 5.8 M online unit-hours at 80–96 % metered coverage — **fall below the 0.5
floor**, while **all three of their `rho_minload` counterparts fall inside the
band**. That pattern identifies the band as belonging to the *legacy min-load*
estimand and inherited unchanged onto the *as-operated* one. The floor is also
**anti-conservative in NYISO** (the gated row replaces the capability row, so
clipping up loosens the class's only bound by 2.49× / 1.66×) and **conservative
in MISO** (it adds) — one uncited number with opposite safety directions.

The card quantifies what each mutually-exclusive flag does at the measurement vs
at the floor, and puts three options with a session recommendation. **The band
was not changed and neither flag was armed**; both stay `U`.

---

## 7. ITEM (d) — UNTOUCHED, AND CONFIRMED UNCHANGED

`nyiso_iroquois_winter_spread` still has **no verdict-bearing cell in the NYISO
shard** — it appears only inside the `def:`/note text of the sibling
`gas_hub_basis_overlay` row, exactly as nyiso-143 filed it. The arming decision
remains the owner's D-5(b) call and the taxonomy remedy remains a base-row +
all-six-shards edit, out of a single-ISO lane's scope.
`docs/DECISION-CARD-nyiso143-iroquois-taxonomy-gap-2026-08-18.md`.

---

## 8. THE QUEUE AFTER THIS SESSION

| # | object | kind | who decides |
|---|---|---|---|
| 1 | **CC over-cycling** (Bethlehem 262–302 starts/yr vs 5–7) | **model-side, lane** | a NYISO lane |
| 2 | **Merit-order inversion on mothballed small CCs** (25×–225×) | **model-side, lane** | a NYISO lane |
| 3 | `RHO_CLIP` band | governance | owner (D-5(b)) — **card delivered** |
| 4 | NYISO hydro 10-min ramp: **certification + water limit only** | data intake | owner (funding/scope) |
| 4b | the three `ramp_capability` seams (§5) | model-side, lane | a NYISO lane |
| 5 | `nyiso_iroquois_winter_spread` arming + taxonomy | governance ×2 | owner |
| 6 | a vintage guard for D-4's conduct rider | model-side, lane | a NYISO lane |
| 7 | the Astoria campus benchmark attribution | data repair | a NYISO lane (needs its own pre-registration — it moves the target) |

Items 1, 2, 6 and 7 are new this session. **Frontier is NOT-YET on items 1 and 2
alone**, independent of every pending owner ruling.

## 9. GOVERNANCE RECORD

* **Holdout freeze ACTIVE and untouched**; 2023–2025 only, everywhere (rules 16 / 22).
* **Rule 15**: no registrable run was produced — the probe solves reproduce the
  keeper's own recipe with zero config delta and write no bundle. Nothing is
  being withheld from the dashboard.
* **Rule 28(b)**: the one mechanism tested (the class scope of
  `nyiso_downstate_ct_gas_daily`) is stamped **rejected** in the NYISO shard.
  No new `ScenarioConfig` field, so duty (c) is not triggered.
* **Rules 25 / 28(d)**: NYISO lane files only; no other ISO's shard, keeper shard
  or lane file touched. Every measured value here is NYISO's own, except the
  MISO `online_rho` row, which is **cited from MISO's committed artifact** for
  the cross-ISO band question and is not transferred as a verdict.
* **DO-NOT-REDO, carried forward**: the Zone-K A/B (nyiso-143), the bridge lay-up
  membership A/B (nyiso-144), the C3c tail anatomy (nyiso-144),
  `nyiso_spin_reserve_online`'s `I` (nyiso-110, confirmed nyiso-144), the
  commissioning curve (nyiso-133), fleet-CF composition (nyiso-136), BLOCKER-A/B/C
  and the cross-ISO queue (nyiso-122). **New to this list:** the LI CC/ST
  delivered-gas re-grounding is **refuted on measured evidence** (§4a of the
  finding) — do not re-propose it without new data.

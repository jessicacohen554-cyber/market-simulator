# FINDING — miso-148: the summer flat-derate double count is REPAIRED by a new class-agnostic basis-aware mechanism, and the repair CLOSES the summer availability hole while making the price gates WORSE — NOT promoted, ESCALATED to the owner

**Session:** miso-148, 2026-08-09, branch `claude/miso-148-cc-availability-l3czbc`.
**PREREG** `results/calibration/PREREG-miso148-cc-availability-summer-basis-2026-08-09.md`
pushed at **`456b376`** (blob `bd0a0a97`, 420 lines, verified against the
**fetched** remote ref) **BEFORE any adjudicating statistic**.

**Keeper at entry and at exit: `2026-08-05-miso-132b-cc-committed`** (bundle
`results/calibration/miso132_ccmin_B`) — **UNCHANGED. The arm is NOT promoted.**

**Runs registered this session (rule 15), both scored, both on the dashboard:**

| run | bundle | determination | fail set |
|---|---|---|---|
| `2026-08-09-miso-148-control` | `miso148_basis_A` | **NOT-YET** | {C3a} |
| `2026-08-09-miso-148-basis-aware` | `miso148_basis_B` | **NOT-YET** | **{C3a, C3b}** |

**Concurrent-session check at open and close: zero open PRs, zero other remote
MISO branches.**

---

## 1. Headline

Three results, in the order they matter.

1. **The mechanism the lane needed exists, and it is a pure basis correction
   with ZERO continuous degrees of freedom.** `summer_derate_basis_aware`
   applies the flat `_SUMMER_CLASS_DERATE` **only to units still carried on a
   nameplate basis** and suppresses it where `pmax` already IS a measured summer
   capability. It is class-agnostic (all four flat-derate classes), it changes
   nothing else, and it discharges every requirement miso-141 §11.2 set for the
   successor it specified but refused to build.
2. **It does what it claims: the SUMMER availability hole closes.** Measured
   fleet-side, monthly `AV_CC − A_CC` in Jun–Sep 2025 moves from
   **−2,296 / −2,451 / −2,157 / −1,560 MW** to **−373 / −369 / −77 / +419 MW**.
   Model available CC capability sitting *below* reality's observed CC
   generation — the indefensible object miso-147 identified — is essentially
   gone in the months where the double count applied.
3. **And it makes the price gates worse, in every year.** C3a
   **−0.49 / −6.01 / −14.15 %** → **−1.98 / −8.03 / −15.58 %**; C3b-2025 NRMSE
   **0.192 → 0.212**, through its 0.200 gate. The fail set grows from
   **{C3a}** to **{C3a, C3b}**.

**Under this session's OWN pre-registered decision rule the arm is therefore not
promotable** (PREREG §9(1) required G-L1c PASS **and** fail set ⊆ {C3a}; the
second condition failed). Under the owner's standing 2026-08-09 guidance —
*structural integrity may outrank gate regression* — this is exactly the case
that **escalates**: reported at full magnitude, never silently promoted, never
silently reverted. **§8 states the decision the owner is being asked to make.**

**The direction was disclosed in advance and is not walked back.** PREREG §6 P5
predicted, at 0.75, that C3a-2025 would get **worse**, because the repair adds
capability and the price effect is downward. It did. Nothing here is offered as
progress against the 2024/2025 level miss, and the charter's against-interest
bound is restated as binding: **2023 carries nearly the same CC gap and C3a-2023
PASSES**, so the composition defect never predicted closing 2025's −14.1 %.

---

## 2. Footing — reproduce-before-extend, PASSED with zero diffs

miso-147's three committed artifacts were re-run at HEAD and diffed
field-by-field against their committed copies: **`_miso147_footing.json` 0
diffs, `_miso147_headroom.json` 0 diffs, `_miso147_january.json` 0 diffs.**

* **G-F1** the six window deficits reproduce exactly
  (−4.750 / −8.333 / −10.676 / −10.671 / −30.999 / −30.435).
* **G-F2** 2025 RT > $200 count = **88** — footing only; the tail motivates
  nothing (C3c 1/1 SPENT).
* **G-F3** S1-2025 **AV 22,276 / A 24,890 / AV−A −2,613.6 MW**, and
  `AV_CC − A_CC` ×12 reproduces to the decimal.

---

## 3. L2 — the CC fleet/rating audit, and an instrument I had to repair

**Pre-registered branch: B-1 `basis_explained`. L1 proceeded.** But the gate
first returned **B-2**, and the reason is reported rather than reinterpreted.

**The gate's first implementation was narrower than its own pre-registered
wording.** G-L2a asks for CAMPD CC plants *"with no model counterpart"*; the
implementation compared against model **CC-class** plants only, and returned
1,466–1,542 MW of "missing" capacity — over the 1,000 MW B-2 bar. Measured, three
of those four plants **are** carried by the model, under other classes:

| plant | CAMPD | model | reading |
|---|---|---|---|
| 1391 Louisiana 1 | CC+ST_GAS, 5 units, peak 688 MW | CT_CHP 76.4 MW | **industrial CHP** (EIA-860 "Industrial CHP"), host steam held out behind the meter |
| 50625 ExxonMobil Beaumont | CC, 3 units, peak 1,050 MW | CT_CHP+ST_CHP 181.8 MW | **industrial CHP**, same boundary |
| 1404 Sterlington | CC, 1 unit, **peak 0 MW** | CT_PEAKER 45.6 MW (= its exact net-summer 45.5) | **never ran**; no defect |
| 55120 SRO Cogen | CC, 2 units, peak 484 MW | **ABSENT** | a cogen, and absent from EIA-860 entirely |

So the B-2 quantity on the gate's own wording is **one plant, 484–490 MW —
below the bar**, and it too is a cogen. The firing was the **industrial-CHP /
BTM boundary miso-147 §1 had already named**, not a merchant-CC population hole.
*A gate that can fire for a reason outside the thing it is gating must be able
to tell the two apart before its verdict is quotable* (miso-140b/141); both
views are now measured and reported separately.

**Merchant CC population and rating are sound, and drift:** model `pmax` vs
CAMPD p99 **net** reads **−0.06 GW (−0.21 %) 2023**, **−0.54 (−1.96 %) 2024**,
**−1.66 GW (−6.0 %) 2025**. The CHP boundary gap is stable at **−2.8 GW** every
year, by design. `cc_capacity_reconcile` caps 7 plants by 2,713.8 MW — a
**deliberate measured cap** to CAMPD demonstrated peak, never counted as missing
capacity (T6).

### 3.1 An L2 data defect, REPORTED and NOT REPAIRED — and it is cross-ISO

The 2025 drift has a single, exactly-identified cause:

* **2025 has no `data/raw/eia-860/vintage_2025/` directory**, so the fleet falls
  back to the canonical (2025 Early Release) sheet.
* That release **re-flags 4 of Cottonwood Energy's 8 CC rows `OA`** (standby).
  They are `OP` in vintage_2023 (1,145.2 MW) and vintage_2024 (1,138.8 MW).
* The operable loader carries `OP` only ⇒ the plant enters 2025 at **580.4 MW
  instead of 1,156.6 MW**.
* The mechanism built for exactly this case — `load_mothballed_but_operating`,
  armed on this keeper via `carry_operating_mothballs` — **returns `[]`**,
  because its `vintage_<year>` precondition is unmet.
* **CAMPD shows the plant ran all year: 4 units, p99 1,140.4 MW, peak 1,239 MW,
  4.70 TWh.**

Fleet-wide that is **9 rows / 594.7 MW** dropped from the 2025 MISO fleet that
were `OP` in vintage_2024, **576.2 MW of it Cottonwood**. Model availability
below observed generation is indefensible for any outage input (rule 14) — and
because the trigger is *"the solve year is past the newest committed vintage"*,
**this is live for EVERY ISO's 2025+ fleet, not MISO's alone**. It is therefore
**reported, not repaired**: the fix (fall back to the newest available vintage)
has cross-ISO blast radius and belongs to its own lane (rule 25). Filed for the
owner in §8.

---

## 4. The mechanism

**`ScenarioConfig.summer_derate_basis_aware: bool = False`** (default off ⇒
every existing bundle byte-inert), reachable via the generic `prb_overrides`
channel (`replay_keeper --set`), so `run_calibration_full`'s signature is
untouched.

**Identity, as a physical claim rather than a knob.** The flat derate
(`CC 10 %`, `CT 12.5 %`) *is* the nameplate → summer-peak ambient loss, so it
belongs only on a **nameplate-basis** capacity. On the per-plant EIA-860 path
`pmax` IS the published net-summer rating, which already embeds that loss.
When armed, the derate applies **only to units still on a nameplate basis**.

**Rule 19 `[R-ONE-MECH]` — the full enumeration was done from source before
anything was built**: statistical POF + WEFOR; `wefor_multiplier` /
`wefor_residual` (both inert here); the CAMPD historic outage overlay incl.
short-window and maxgen-event derates; `BIN_FORCED_DERATE_BY_YEAR`; the flat
derate itself; `temp_dependent_derate` (mean-anchored on CT_CHP/ST_CHP — a
reshape that never touches CC); `gt_ambient_derate` (measured PROVABLY INERT
for MISO); `cc_capacity_reconcile`; the COD ramp. The mechanism **replaces the
flat derate's application where the basis already carries it** — it stacks
nothing.

**What it deliberately is NOT.** No POF drop, no age-derate drop, no WEFOR
change, no capacity rescale — the four riders that made miso-141 §9 refuse
`cc_nameplate_summer_derate` as the repair. And **no off-summer leg**: that is a
separate defect with its own mechanism (`cc_winter_capability_basis`), and
MISO's measured Oct–Mar CC availability headroom is **positive**, so no evidence
asks for it.

**Corrupt filings, explicit rather than by silent clamp (miso-141 §11.2(c)).**
Plants filing summed net-summer above summed nameplate are clipped by the
always-on CC guard onto `max(nameplate, demonstrated_peak)` — a nameplate-like
basis — so they **KEEP** the derate, as do plants absent from EIA-860. Measured
on the 2025 fleet: **86.9 % of flat-derate MW admitted**; **7,255 MW across 9 CC
and 4 CT plants kept**.

**An error I made and had to fix, reported against interest.** My first
predicate re-derived the clean/corrupt split from the raw EIA-860 sheet. It is
wrong, and it is wrong in the exact way `_reconcile_cc_pmax_to_nameplate`'s own
docstring warns about: the plant-total-on-one-row pattern hides behind NaN
component rows the loader nameplate-fills, so **55380 and 55467 both read
"clean" on the raw sheet while the loader clips them by 1,028.6 and 353.3 MW**.
The predicate now reads the **guard's own recorded clip decision**. Had I not
caught it, ~740 MW of corrupt-filing capacity would have been silently
over-credited in summer.

**Degrees of freedom: ZERO continuous (rule 21).** A boolean over a data
predicate — no derate fraction, no per-class scale, no sweepable tolerance. **No
parameterised variant was built or solved**, because that would be precisely the
channel through which a residual could be fitted (T1).

---

## 5. G-L1 — identification, measured on the real fleet before the arm was solved

| gate | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **G-L1a** flat-derate MW **admitted** | **87.2 %** | **87.0 %** | **86.9 %** |
| **G-L1b** restored summer h12–17 MW | **4,936.8** | **4,867.5** | **4,671.4** |
| miso-141 G-4 committed (derate zeroed for *every* unit) | 5,933 | 5,853 | 5,686 |
| ratio | 0.832 | 0.832 | 0.822 |

The ~0.83 ratio is **the corrupt-filing treatment working as designed**, not a
miss: miso-141's figure zeroed the derate everywhere, including the plants this
mechanism deliberately excludes.

**By class, 2025:** CT_PEAKER **+2,550.8 MW**, CC_REGULAR +1,696.6, CC_CHP
+319.6, CT_CHP +104.3. **CT_PEAKER is the single largest contributor** — the
half miso-141 measured as having *no mechanism at all* and carrying the largest
gap. That is the class-agnostic design earning its keep.

**T3 construction check — PASS in all three years:** off-summer hours
byte-identical, non-admitted units byte-identical, and the per-class summer
ratio exactly `1/(1−d)` (1.111111 CC, 1.142857 CT).

**G-L1c — the gate the lane exists to pass: PASSES, and only half the object
moves.**

| S1 stratum `AV_CC − A_CC` | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| control | −1,226 | −1,608 | −2,614 |
| **arm** | **−217** | **−637** | **−1,755** |

but month-resolved the summer repair is near-complete —
**Jun–Sep 2025 −2,296 / −2,451 / −2,157 / −1,560 → −373 / −369 / −77 / +419 MW.**
The S1 stratum spans all twelve months, and **its non-summer half is the
commitment/displacement object miso-147 §4 named** — L3, observation only this
session, deliberately not armed. *(Monthly levels here are this probe's own
construction and sit ~200 MW off miso-147's committed table; the **delta** is
the quantity, measured on one construction throughout, and miso-147's own table
was separately reproduced with zero diffs.)*

---

## 6. K-gates, and K0's failure reported rather than redefined

* **K0 — FAILED AS WRITTEN.** The zero-delta control does **not** reproduce the
  committed keeper's class-hour sidecars: **max |Δ| 912.5 MW**, total absolute
  class drift **0.54 / 0.14 / 0.46 TWh** on ~500 TWh of annual dispatch (~0.1 %;
  largest single class ST_GAS **+0.25 TWh** against C1's ±8 TWh tolerance).
  * **Cause: HEAD drift since the keeper's own solve** (`git_sha 6b05f058`,
    2026-08-05). **Instrument limit disclosed:** that sha is **not reachable in
    this shallow clone**, so the drift cannot be bisected here; ~20 commits
    touched `src/market_sim/` in the window, at least one backfilling
    `unit_outage_lp_capacity_basis`, which MISO's historic outage overlay
    consumes.
  * **Proven NOT to be this session's edits, by measurement:** the drift's
    **full magnitude appears in non-summer hours of non-gas classes** (7,232
    nonzero cells in 2025 alone) — a region the mechanism cannot reach even when
    **armed**, and it is **off** in the control.
  * **Consequence, stated plainly:** the A/B is still interpretable because
    **both arms run at the same HEAD** and every quoted delta is
    **arm-vs-control**. **No arm-vs-keeper delta is quoted anywhere.**
  * **The scorecard, unlike the sidecars, barely moves:** control C3a
    −0.49/−6.01/−14.15 % and C3b 0.075/0.112/0.192 against the keeper's
    −0.4/−6.0/−14.1 and 0.075/0.112/0.191, same determination and same fail set.
    So the drift is **immaterial at the gated grain** — but see §8(3): MISO's
    designated keeper is **not bit-reproducible at HEAD**, which is a governance
    fact the owner should hold.
* **K1 single delta** — the arm's `run_config.json` differs in exactly the one
  new field. **K2 span** — `--year 2023 2024 2025`, one invocation each, years
  sequential (rules 12/16). **K3 balance** — `d_demand` **max 0.0 MW** in all
  three years. **K4 live** — confirmed twice: the loader logs
  *"SUPPRESSED for 1188 of 1264 flat-derate units … KEPT for 76"*, and dispatch
  moves (§7).

---

## 7. The arm's effect — every number arm-vs-control

**C3a mean LMP**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| control | −0.49 % | −6.01 % | −14.15 % |
| **arm** | **−1.98 %** | **−8.03 %** | **−15.58 %** |
| Δ | −1.49 pp | −2.02 pp | −1.43 pp |
| Δ $/MWh | −0.492 | −0.655 | −0.651 |

**C3b price duration/shape NRMSE** 0.075→0.082, 0.112→0.125, **0.192→0.212**
(gate 0.200).

**Class energy (2023, TWh):** CC_REGULAR **+3.16**, CC_CHP +0.46, CT_CHP +0.23
against COAL_PRB **−1.24**, import **−1.05**, ST_GAS −0.81, COAL_BIT −0.35,
CT_PEAKER −0.33; net −0.02. **The restored CC displaces coal and imports** —
the direction miso-147 measured as the composition defect.

### 7.1 MAY 2025 — the charter's mandatory report, and my prediction was WRONG

*A mechanism that does not report its May effect has not been measured.*

**May-2025: control +12.43 % → arm +12.41 %, Δ −0.006 $/MWh.** Materially
**zero**. The monthly Δ profile shows why:

`[0.0, 0.0, 0.0, 0.0, −0.006, −1.836, −2.448, −1.403, −1.276, −0.003, 0.0, 0.0]`

**The mechanism moves prices in Jun–Sep and nowhere else** — because
`_SUMMER_CLASS_DERATE` applies to Jun–Sep only. **May is not reachable by this
mechanism at all.**

This **refutes PREREG P7** (May improves, stated at 0.60) and, more usefully,
**sharpens miso-147 §6**: May's CC availability deficit (`AV_CC − A_CC` −1,201
MW in 2025) and the summer deficit are the *same symptom with different causes*.
The summer half is the flat-derate double count; **the May half is not, and is
still unexplained**. miso-147's "one object, both signs" reading holds as a
description of the symptom, **not** of the cause — and any successor that
expects a summer-availability fix to move May has over-read it.

### 7.2 C8 — shares rise, the criterion still passes

| ST_GAS forced share | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| control | 31.7 % | 33.0 % | 44.7 % |
| **arm** | **34.1 %** | **35.8 %** | **48.4 %** |

plus a **new** CT_PEAKER 2023 entry at **16.8 %** (above its 15 % peaker cap).
**C8 as a criterion PASSES in both arms** — every binding mechanism clears D-4
and the D-1 shape gates pass, so all are *grounded above budget*. But the
**shares rose**, which is the pre-registered kill gate. The cause is mechanical
and not a new forcing: restored CC displaces ST_GAS/CT_PEAKER **economic**
energy while their floored energy is unchanged, so the ratio rises. **No new
forcing id appears and no D-4 window breaks.**

---

## 8. Kill gates, the decision, and what the owner is being asked

| pre-registered kill gate | outcome |
|---|---|
| **C3b-2025 NRMSE ≤ 0.200** | **BREACHED** — 0.192 → **0.212** |
| C3a 2023/2024 stay PASS | **HELD** — −1.98 % / −8.03 %, both inside ±10 % |
| **MAY 2025 effect reported** | **REPORTED** — +12.43 % → +12.41 %, Δ −0.006 $/MWh |
| C1/C2 PASS on gated years | **HELD** — fuelmix PASS, sysvol PASS, both arms |
| **C8 no material class's forced share rises** | **BREACHED** — ST_GAS +2.4/+2.8/+3.7 pp (criterion still PASSES, grounded) |
| C3c 1/1 SPENT, motivates nothing | **HELD** |
| **fail-set ⊆ {C3a}** | **BREACHED** — {C3a, **C3b**} |

**The decision, taken under my own pre-registered rule.** PREREG §9(1) made an
arm a keeper candidate only if G-L1c passed **AND** the fail set stayed
⊆ {C3a}. G-L1c passed; the fail set did not. **So the arm is NOT promoted, and
the keeper is unchanged.** I have not redefined the rule after seeing the
number, and I have not reverted the mechanism either — it is committed,
default-off, matrix-registered and fully measured.

**What the owner is asked to decide (rules 1 + 14 vs the gate ledger):**

1. **Arm `summer_derate_basis_aware` on the MISO keeper?** It repairs a defect
   that is indefensible on its face — model available CC capability below
   reality's observed CC generation — with zero free parameters, and it is the
   mechanism miso-141 specified. The cost is C3a worse by ~1.4–2.0 pp in every
   year and C3b-2025 through its gate. Rule 1 `[R-STRUCT]` and rule 14
   `[R-ACCURATE]` both say a correct measured input stays in even when the fit
   worsens; the 2026-08-09 guidance says such a run *may* still be a keeper.
   **That call is the owner's, and this session declines to make it silently in
   either direction.**
2. **The four other ISOs.** CAISO / PJM / NYISO / NEISO all run
   `plant_level_fleet` with `cc_nameplate_summer_derate` armed — which routes CC
   through a measured per-plant ratio but leaves **CT_PEAKER / CT_CHP on the
   flat derate over a net-summer base**. The same double count is **live and
   unmeasured** on their CT classes. Their cells are `U`; no verdict transfers
   (rule 25).
3. **The 2025 vintage-fallback defect (§3.1), which is nobody's lane yet.** It
   drops 594.7 MW of demonstrably-operating MISO capacity from the 2025 fleet
   and, by construction, applies to **every ISO's 2025+ fleet**. Related: MISO's
   designated keeper is **not bit-reproducible at HEAD** (§6).

---

## 9. My prior, scored against interest

| # | prediction | P | measured | verdict |
|---|---|---:|---|---|
| **P1** | G-L2 returns B-1 `basis_explained` | 0.70 | B-1 **on the corrected instrument**; the first implementation returned B-2 on the CHP boundary | **RIGHT, but only after I repaired my own gate** |
| **P2** | ≥85 % of flat-derate MW admitted | 0.75 | 87.2 / 87.0 / 86.9 % | **RIGHT** |
| **P3** | restored 4.8–6.0 GW | 0.65 | 4.94 / 4.87 / **4.67** | **2 of 3 in band**; 2025 below it |
| **P4** | S1-2025 `AV−A` rises to −900…+500 MW | 0.70 | rises to **−1,755** | **WRONG** — it rises, but far less than I said; the S1 stratum's non-summer half is untouched |
| **P5** | C3a-2025 gets **worse** | 0.75 | −14.15 → **−15.58 %** | **RIGHT** (stated against interest before the solve) |
| **P6** | \|ΔC3a-2025\| < 1.5 pp | 0.60 | **1.43 pp** | **RIGHT** |
| **P7** | May-2025 over-pricing improves | 0.60 | **−0.006 $/MWh — no effect** | **WRONG, and instructively**: May is outside the derate's own Jun–Sep window, so the mechanism has no May channel (§7.1) |
| **P8** | fail set stays ⊆ {C3a} | 0.70 | **{C3a, C3b}** | **WRONG** |
| **P9** | mechanism armed AND solved | 0.65 | both | **RIGHT** |

**Where I was wrong, and what it cost.** (a) **P4 and P7 were the same error
twice** — I let miso-147's *stratum-level* and *symptom-level* framings imply
that a summer-availability repair would reach S1 and May. It reaches neither,
because both span months the flat derate never touched. The trap I wrote (T1,
"fixing the number") guarded against sizing the mechanism to the residual; it
did not guard against **over-reading which object a mechanism can reach**, and
that is the sharper lesson for the successor. (b) **P8 was optimistic** — I
priced C3b's 0.009 headroom as likely to survive a capability addition that
flattens the price duration curve; it did not, and the direction was
foreseeable. (c) **P1 was "right" only because I found my own gate's defect** —
had I taken the first B-2 at face value the session would have suspended L1 on
the industrial-CHP boundary.

---

## 10. Rule duties

* **Rule 15 `[R-DASHBOARD]`** — **both** runs registered this session, control
  and arm, with bundles, sidecars, run payloads, bench and
  `legitimacy_diagnostics.json`; keeper-only `hourly/` sidecars committed for
  both. Results lead from the dashboard, not from chat.
* **Rule 16 / rule 22 `[R-HOLDOUT]`** — 2023, 2024 and 2025, all three, one
  invocation per arm. **No year outside the training window was solved, scored
  or registered**; MISO holds no `calibration-complete` marker in either block.
* **Rule 28 `[R-MECH-MATRIX]`** — the new row `summer_derate_basis_aware` lands
  **in the same PR as the field** (28(c), CI-enforced); MISO's cell is **`O`** —
  chartered, built, arm solved and registered, **verdict pending the owner
  decision of §8(1)**. It is deliberately **not `R`**: the mechanism was not
  refuted, it was measured to be structurally correct at a fit cost. ERCOT `.`
  (CAMPD-bin nameplate basis — no double count to repair); the other four `U`
  (rule 28(d) — no verdict transfers). §5.4 queue stamped in the same session.
* **Rules 13 / 14** — an availability **INPUT**, never a dispatch pin; no
  CEMS/dispatch bridging (DO-NOT-REDO honoured); the accurate input is **not
  reverted to protect a number**, and the worse fit is reported, not buried.
* **Rule 19 / 21 / 24 / 25** — one mechanism with its enumeration (§4); zero
  continuous DOF with the ledger entry filed as *structural*, never *residual*;
  registered in `ScenarioConfig` and the run's `run_config.json`, with no
  env-var or hardcoded channel; nothing crossed an ISO boundary.
* **Rule 23 `[R-FROZEN-DERIVE]`** — `SUMMER_CLASS_DERATE`'s **value is
  untouched**; the mechanism changes *where it applies*, on a basis argument,
  and no parameter was re-derived against any residual.
* **Rule 27 `[R-PUSH]`** — the PREREG blob was verified against the **fetched**
  remote ref (the ffr-4e lesson); no file ≥300 lines was rewritten from
  regenerated content.
* **Cache-key hygiene, done the documented way.** A new `ScenarioConfig` field
  enters the cache-key hash and moved both pinned keys, which would have
  orphaned every on-disk cache and every keeper's addressed bundle.
  `summer_derate_basis_aware` is therefore registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` with its declared default, making it
  **cache-neutral at its default** so both pins hold **unchanged** — the
  nyiso-119 / caiso-186 discipline, and the step caiso-184 skipped. The
  literals were **not** re-baselined.
* **A second, independent corroboration of the K0 HEAD drift, measured.** In the
  `fleet / arrays / scenario / availability / derate` selection, HEAD carries
  **6 failing tests** — `test_fleet_arrays_golden` (ERCOT 2023, *availability*
  and *min_gen* hashes), `test_soundness` capacity-evolution, and 4
  `test_export` cases. They fail **identically at the pre-session base
  `51d4e98`** with none of this session's changes applied, so **this session
  adds ZERO new failures** — and the ERCOT golden moving on exactly the two
  arrays this lane touches is the same drift that failed K0, seen from a second
  instrument. **Main's regression suite is red independently of MISO**; filed
  for the owner alongside §8(3).
* **A HEAD bug fixed to unblock the lane**, reported separately: caiso-186 added
  `cc_winter_capability_basis` to `run_calibration_full`'s `run_year(...)` call
  without adding the parameter to `run_year`, and the kwarg is passed
  unconditionally — so **every calibration solve at HEAD, for every ISO**,
  raised `TypeError` before its first LP. Threaded exactly as its siblings are.
* **Nothing was written under `data/raw/`.** Probe hygiene
  (`_miso143_stack.hygiene()`) in every entry point; the CAMPD unit loader and
  strata reused from `_miso147_strata` (never `campd.load_campd_hourly`).

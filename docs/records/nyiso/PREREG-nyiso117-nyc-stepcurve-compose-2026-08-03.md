# PRE-REGISTRATION — nyiso-117: composing the NYC RCPF step curve onto the corrected CT artifact, and an ex-ante screen of SENY's curve

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (rule 16 —
one bundle per arm) · **Keeper at session start:**
`2026-08-03-nyiso160-ctmeter-screen-b` (CALIBRATED-WITH-CAVEATS, C3c the sole
ledgered caveat) · **Committed and pushed BEFORE either solve.**

---

## §1 — what this session is, and what it is NOT

Two orthogonal, composable corrections exist and only one of them is on the
designated keeper:

| correction | kind | where it lives now |
|---|---|---|
| the **CT heat-rate meter artifact** (rates diluted LOW) | a rule 14 `[R-ACCURATE]` **INPUT** fix | ON the keeper — `2026-08-03-nyiso160-ctmeter-screen-b`, promoted by **caiso-160**, a zero-config-delta replay of the nyiso-113 recipe |
| the **NYC locational RCPF demand-curve SHAPE** (`nyiso_nyc_rcpf_step_curve`) | a rule 14 `[R-ACCURATE]` **MECHANISM** fix | implemented, tested, merged, promoted at nyiso-115 — then **superseded within hours**, because its bundle used the PRE-FIX CT artifact |

Neither contains the other, so the composition is a **re-solve on a corrected
input**, not a re-opened question.

**This session does NOT re-derive, re-level or re-scope the mechanism.** The
$25/MW value is the published ASM §6.8 Reserve Capacity Penalty Factor, already
confirmed against measurement (nyiso-115 §3: the isolated NYC adder never
exceeds $25.00 in any of 26,301 hours, and the 10-minute product stacks to
exactly $50.00 in precisely the hours the 30-minute one sits at $25.00 — 5/5,
16/16, 98/98). The scope (`NYISO_RCPF_STEP_CURVE_FAMILIES` = the NYC pair) is
the **measurement's own boundary**, not a choice: NYC is the only locational
region whose published RCPF the measured market ever reaches. Both are frozen
under rule 23 `[R-FROZEN-DERIVE]` and restated in §7 as binding no-tuning
clauses.

**Evidence carried forward unchanged, not re-litigated.** The nyiso-115 ex-ante
screen (`scripts/probes/_nyiso115_nyc_rcpf_curve_screen.py` →
`results/calibration/nyiso115_nyc_rcpf_curve_screen.json`) stands on its own
instrument and is unaffected by a CT heat-rate artifact — it is a measurement of
**NYISO's posted prices**, not of the model. Only the *bundle's* CT input was
stale.

## §2 — arms

Both from the **designated keeper's** recipe over 2023, 2024, 2025 in one bundle
each (rule 16), launched concurrently (rule 12, 2-way cap):

| arm | bundle | delta |
|---|---|---|
| **CONTROL** | `results/calibration/nyiso117_control` | zero-delta replay of `nyiso160_ctmeter_screen_B` at THIS session's HEAD |
| **TREATMENT** | `results/calibration/nyiso117_nyc_stepcurve` | `--set nyiso_nyc_rcpf_step_curve=true` |

**A same-HEAD control is MANDATORY, not optional.** The keeper was solved at
`b8d5e04` on `claude/caiso-160-…`; this session's HEAD is `55ba07c`. FINDING-
nyiso114 §2 measured that a keeper arming a P0-run-pattern bridge does **not**
re-solve to byte-identity once main moves (max |Δprice| $9.0–10.6 attributable
entirely to main's drift). Every attribution below is **treatment-vs-control at
one HEAD**, never treatment-vs-keeper.

## §3 — GATES, each on an instrument that can observe what it claims

Reserve gates read `hourly/reserve_family_<year>.parquet` — the per-family dual,
requirement, held MW and ORDC shortfall. **Never** `system.parquet`'s
`reserve_price`, which is the cross-family SUM broadcast identically to every
zone and is inert by construction for any locational question (the nyiso-113
K3/K4 error).

| id | gate | pass condition |
|---|---|---|
| **G1** | the curve is armed, and the ramp is gone | `nyc_10min_total` / `nyc_30min_total` duals take the published **$25.00** in ≥ 1 hour, and take **no** interior-rung value ($3.125 … $21.875) in **any** hour, all three years |
| **G2a** | **scope — CONSTRUCTION leg (the kill leg)** | every non-NYC family's `requirement_mw` byte-identical to control in all three years |
| **G2b** | **scope — independent corroboration** | the solve log's ORDC step count falls by **exactly 14** (73 → 59 = 2 families × 7 lost rungs) and by nothing else, in both P0 and P1, all three years |
| **G2c** | scope — reported, **NOT a kill** | non-NYC `shortfall_mw` deltas reported; a change is a **finding to explain**, not automatically a leak (see §4) |
| **G3** | LP row identity | `held + shortfall ≥ requirement` everywhere, tight exactly where the family prices |
| **G4** | no feasibility damage | zero unserved-energy slack and zero dump in **both** arms, all three years |
| **G5** | span | 2023–2025 in one bundle per arm; **no** year outside 2023–2025 solved, scored or read (rule 22 — the holdout spend freeze is ACTIVE) |
| **G6** | scoring | `legitimacy_diagnostics.py` + `calibration_verdict.py` run per bundle; C1/C2/C3a/C3b/C3c/C4/C6/C7/C8 reported for BOTH arms against each other |

### §3.1 — why G2 is written this way (nyiso-115's lesson, inherited)

nyiso-115's G2 demanded byte-identity of `dual`, `requirement_mw`, `held_mw` and
`shortfall_mw` for every non-NYC family. **Three of those four are solved outputs
of a co-optimization**: changing one family's demand curve re-solves the joint
reserve/energy dispatch, so other families' held MW and duals move as an
**equilibrium response**. That gate could therefore only pass if the mechanism
did nothing — it could not distinguish a scope leak from the mechanism working,
and it failed uninformatively.

The question kill **K-C** actually asks — *did the mechanism touch a family it
was not scoped to?* — is a question about **CONSTRUCTION**. So the kill leg is
written on construction only:

* **`requirement_mw`** is a pure input (the balance-row RHS) → **G2a, the kill**.
* **the ORDC step vectors** are pure inputs → **G2b**, observed through the solve
  log's `%d ORDC steps` line (`pipeline/kwargs.py`), an instrument entirely
  independent of the parquet.
* **`dual` and `held_mw` for non-NYC families are EXPLICITLY NOT GATED.**
  Movement there is the expected equilibrium response (nyiso-115 measured
  exactly this: `held_mw` on slack families, and `seny_30min_total`'s 2025 dual
  responding to the intended NYC-inside-SENY nesting). They are **reported**.
* **`shortfall_mw` is reported but demoted to G2c.** nyiso-115 gated on it and
  it passed at 0.00e+00, but it is a **solved LP variable**, not an input — it is
  identically zero on the non-NYC families only because they are slack. Gating a
  kill on it would repeat the same category error at one remove. If it moves,
  that is explained, not automatically fatal.

### §3.2 — dtype, stated ex ante (nyiso-116's lesson)

The sidecar's numeric columns are **float32** (spacing 7.6e-06 – 6.1e-05 MW at
NYISO requirement magnitudes). Byte-identity gates are therefore asserted as
**exact equality of the float32 values** (Δ == 0.0), which two identically-
constructed input vectors satisfy exactly — **not** against a `1e-6` MW
tolerance the dtype cannot represent (the nyiso-116 G3/P4 failure).

## §4 — KILLS, each discharged BY MEASUREMENT

| id | kill | discharge |
|---|---|---|
| **K-A** | the effect is main's drift, not the mechanism | Every number is TREATMENT vs the **same-HEAD CONTROL** (§2). The keeper bundle is never differenced. Additionally reported: control-vs-keeper divergence, so the drift is quantified rather than assumed away. |
| **K-B** | the flag is inert | If G1 finds **zero** hours at $25.00, the mechanism did not arm on this input: report **INERT**, do not narrate a price delta, and do not promote. |
| **K-C** | the scope leaked | If **G2a** finds any non-NYC family's `requirement_mw` changed, or **G2b** finds a step-count change other than the 14 NYC rungs, the arm is **VOID** — a construction bug, not a result. |
| **K-D** | feasibility damage | If G4 finds slack or dump appearing where control had none, the arm is **NOT** promotable regardless of price movement. |
| **K-E** | the composition is not additive | If G1 passes but the CT-artifact fix has changed *which* hours the NYC pair binds so much that the mechanism's own effect cannot be read, that is reported as measured — it does not license changing either correction. |

## §5 — THE NULL, PRE-REGISTERED (not discovered afterwards)

**C3c is expected UNCHANGED, and this is stated in advance.** A step and a ramp
are **both $0 at or above the requirement**, so the family binds in the **same
hours** either way. This mechanism moves the **LEVEL** of the reserve price in
hours a family already binds and **cannot add binding hours**.

Therefore:

* it **cannot** close nyiso-110's everyday-reserve-formation gap (the model
  prices reserve in 17/6/34 hours against a measured NYISO DA spin price above
  $1 in **100 %** of peak-window hours), and **will not be reported as closing
  it**;
* a steeper curve makes shortfall more expensive to incur, so binding hours may
  **fall**. Any outcome on the C3c tail count is reported as measured, in either
  direction, and is **not** grounds for rejecting the mechanism (rule 1
  `[R-STRUCT]`).

The keeper's C3c caveat is expected to survive this session **unchanged**.

## §6 — TASK 2: an EX-ANTE screen of SENY's demand curve (`nyiso_ordc_measured_step_span`, cell `U`)

Pre-registered as a **separate mechanism with its own kill set** (rule 19
`[R-ONE-MECH]` — it must not be folded into the NYC flag), and screened the same
way nyiso-115 screened NYC: **on measurement, before any solve is contemplated.**

**The question.** nyiso-115 measured, and deliberately did not act on, that the
isolated SENY-only adder caps at exactly **$40.00** (52 hours of 2025) — the
issue-#1344 dynamic-requirement increment — while the model prices SENY
shortfall on a ramp to **$500**. nyiso-114 §3 further measured that the model
already reaches **$62.50** on SENY's first rung, i.e. **above** the measured
ceiling. **The direction here is OVER-pricing — the opposite of NYC.**

**The instrument** is identical and equally checked: `data/raw/NYISO-AS/
NYISO_as_da_<year>.csv`, differencing a SENY zone against a zone sharing every
region **except** SENY. SENY-only = `DUNWOD` − `CAPITL`.

**Pre-registered screen outcomes**, decided before the numbers are read:

| outcome | criterion | action |
|---|---|---|
| **S-MATCH** | the model's SENY curve already prices within the measured envelope | **CLEAN CLOSURE.** Record it, set the cell with the evidence, propose no lever. |
| **S-OVER** | the model's rungs materially exceed the measured ceiling in hours SENY binds | Record the magnitude and the hours. **No solve is spent in this session** — a SENY curve change is `nyiso_ordc_measured_step_span`'s mechanism and needs its own pre-registration and its own arm, which this session does not open (rule 19). |
| **S-INERT** | SENY never binds in the model, so its curve shape is unobservable | Record **unidentified**; no lever, cell unchanged from `U` on the shape question. |

**Binding on Task 2:** no parameter is introduced, changed or fitted; no solve is
launched for it; no NYC-arm outcome may be used to justify a SENY change or vice
versa.

## §7 — NO-TUNING CLAUSE (binding)

* **The $25/MW NYC RCPF is not a free parameter and will not be moved**, in
  either direction, for any reason. It is the published ASM §6.8 value.
* **The NYC-pair scope is not re-opened.** `NYISO_RCPF_STEP_CURVE_FAMILIES` is
  the measurement's boundary; East/LI/SENY keep the ramp in this session.
* **No family's requirement MW is touched** — not NYC's 500/1,000, not SENY's,
  not LI's, not East's. **`n_ramp` is not tuned.**
* **The CT heat-rate artifact fix is not touched.** It is the keeper's input and
  this session composes onto it; it is not re-derived, re-scoped or reverted.
* **SENY's measured-$40 ceiling is SCREENED AND REPORTED, NOT ACTED ON** (§6).
* Carried forward unchanged from prior sessions (rule 23 `[R-FROZEN-DERIVE]` —
  re-derive only on a SOURCE DATA change, never on a residual): the ramp
  envelope, the 227-3 compliance file, the LI reserve levels / $25 value /
  On-Peak calendar, the `nyiso_gas_bridge_*` measured min-load / min-run
  parameters, and now the NYC $25/MW RCPF and its NYC-pair scope.
* **C3c is CLOSED as a lever lane** (nyiso-115 §11 — both admissible routes shut
  on measurement) and is **not re-opened** here.
* **Promotion is decided on rule 1 `[R-STRUCT]` / rule 14 `[R-ACCURATE]`**, not
  on the residual. A structurally-correct published curve stays in even if the
  fit degrades; a degradation is reported as a discovered root-cause issue.

## §8 — DO-NOT-REDO check (rule 28a), stated rather than assumed

* `nyiso_nyc_rcpf_step_curve` is cell **`O`** — open, and open *because* nyiso-115
  yielded the keeper to caiso-160's input fix rather than because anything about
  the mechanism was refuted. Re-solving it on the corrected input is the
  explicitly-recorded next step, not a re-test.
* `nyiso_ordc_measured_step_span` is cell **`U`** — untested, never armed. A
  measurement-only screen (§6) is admissible against a `U` cell.
* No NYISO cell marked `R`/`I`/`G` covers either question. The June-2026
  `nyiso 25 rcpf-steep` probe remains **not a bar** (it transferred the
  NYCA-30min `critical = 0.75 × requirement` anchor to the locational products —
  a different parameterization from a different family — carried no matrix row,
  and was rejected on the **C3c tail count**, i.e. on fit, which rule 1 forbids
  as grounds for rejecting a structurally-correct mechanism).
* **NYISO's transfer queue is EMPTY.** nyiso-115 adjudicated the last five with
  zero solves (`maxgen_emergency_tier_pricing` `I`, `cc_committed_offer_margin`
  `G`, `measured_offer_surface` `G`, `reference_price_interface` `G`,
  `storage_vintage_ramp` `I`). None is re-tested.
* **The shared-field ratchet backlog in ERCOT (14), PJM (18), MISO (17) and
  CAISO (5) is THEIR lanes' work** (rule 25 / 28(d) — a census can mint a `U` and
  nothing more). This session only confirms the ratchet still reports **0** for
  NYISO.

## §9 — governance

* **Rule 16** — all three training years in one bundle per arm.
* **Rule 22** — the holdout spend freeze is **ACTIVE**. No year outside
  2023–2025 is solved, scored or read; no marker spent or requested.
* **Rule 15** — **both** arms registered on the dashboard in this session,
  keeper or not.
* **Rule 28(b)** — the `nyiso_nyc_rcpf_step_curve` cell is updated to its verdict
  in **this** session; `nyiso_ordc_measured_step_span`'s note records the §6
  screen outcome. No new `ScenarioConfig` field is added, so 28(c) does not
  apply.
* **Rule 27** — every push touching a file ≥ 300 lines is blob-verified.
* **Parallel-lane hazard** — other ISOs' sessions promote NYISO keepers
  (caiso-156/159/160 all did). `main` and `keepers/NYISO.json` are re-fetched and
  re-checked immediately before any promotion; conflicted paths are verified
  byte-identical to `origin/main` before being kept.

# PRECHECK — caiso-180: THE CAISO OUTAGE RE-AUDIT

**Pushed and blob-verified BEFORE any scored metric was read.** Nothing in this session's
scored surface — no C1/C2/C3a/C3b/C3c/C4/C6/C8 value, no class energy, no price — had been
looked at when this file was written. What HAD been read, and is reported below as part of
the pre-registration rather than concealed, is **input-side census only**: row counts by year
in four states of one CSV, that file's git history, its `plant_group` vocabulary, and the
byte-size of three companion files. Those are facts about an *input*, they are what Phase 0
was chartered to establish, and none of them is a model output.

Session: caiso-180. Branch `claude/caiso-180-outage-reaudit-cc5y2j`. **CAISO ONLY.**
Keeper at session start: `2026-08-06-caiso-175-tac-intake` (**NOT-YET**, rubric v3.1,
8 criteria, C3a the sole FAIL; C3c the sole ledgered caveat). DOF ledger 11 / 8.
CAISO does **not** hold `complete` (withdrawn by the owner 2026-08-06).
The holdout spend freeze is **ACTIVE**.

---

## 0. The scope discipline this session binds itself to, stated first

- **2023, 2024, 2025 ONLY.** No other year is solved, scored, registered, or read. One
  bundle per arm, all three years, rule 16 `[R-ALLYEARS]`. Years sequential inside a run,
  arms sequential (rule 12 `[R-PARALLEL]`).
- **`calibration-complete.json` and `holdout-freeze.json` are OWNER acts. This session
  writes NEITHER**, in any field, including the `intake_log`.
- **No other ISO's keeper shard, registry sidecar, status part or bench file is touched.**
- **No `ScenarioConfig` field is added, removed or re-valued.** The only thing that differs
  between arms is the *bytes of one data file*.
- The re-audit is a **measurement**, not a promotion. The pre-registered expectation is that
  the keeper designation is **unchanged** at the end of it (§6.4).

---

## 1. The object

At the **2026-07-24** CAMPD intake (`calibration-complete.json` → `intake_log`), on explicit
owner instruction, CAISO's unit-outage extract was **RE-DERIVED IN FULL** on the current
detector rather than merge-preserved — the other five ISOs kept their committed in-sample rows
byte-identical, CAISO alone did not. Its 2023–2025 rows changed:

> `2023 439->640, 2024 405->622, 2025 509->733`

The intake entry itself flagged the consequence and deferred it:

> *"this updates the CAISO keeper's in-sample outage input and closes CAISO's regenerate-lane;
> flagged for a CAISO re-audit/re-solve (rule 11: keep the accurate input, fix any root cause
> there), NOT solved or scored here."*

The keeper runs `outage_source="historic"` (`run_config.json` → `calibration_flags`), so it
**consumes that envelope**. No session has ever measured what the change did to it.
caiso-171's "Follow-on work" paragraph named the re-audit a **precondition for spending 2022**;
caiso-178 and caiso-179 each escalated it to the owner as still outstanding. It needs solves
and **no new data**.

---

## 2. PHASE 0 — recoverability. BOTH branches pre-registered; the outcome is recorded here

**The question.** Is the PRE-regeneration envelope recoverable from git history of
`data/raw/campd-unit-outages-CAISO.csv` (tracked)?

**Branch (a) — RECOVERABLE ⇒ a true A/B.** Arm A = fresh same-head CONTROL on the current
envelope; Arm B = the identical recipe on the reconstructed pre-regeneration envelope. This
measures the data change directly and is the honest audit.

**Branch (b) — NOT RECOVERABLE ⇒ forward-only characterisation** (window census by class and
zone, availability-envelope diagnostics, D-1/D-2/D-4) with **no counterfactual**, stating that
limit plainly rather than substituting a proxy baseline. Substituting a proxy is the caiso-123
failure mode and is forbidden here.

### 2a. OUTCOME: BRANCH (a) FIRES. The envelope is recoverable, and it reconciles EXACTLY.

The clone is shallow (271 commits at session start); the commit named in the session charter
was not present. `git fetch --deepen=200` (→ 2,796 commits) exposes the history. The file has
been touched by exactly two commits in the relevant span:

| state | commit | blob | rows | 2023 | 2024 | 2025 |
|---|---|---|---:|---:|---:|---:|
| **PRE** — pre-regeneration | `d7c9a53a` (= `49e85fb4^`) | `e40847c8` | 4,496 | **439** | **405** | **509** |
| **REGEN** — the 07-24 full re-derivation | `49e85fb4` *"campd-outage-backfill: re-derive CAISO in full (owner instruction)"* | `3dc01fae` | 5,138 | **640** | **622** | **733** |
| **GUARD** — merit-order-guard pass | `6a8f285c` *"neiso-65: adopt guard-corrected CAMPD extracts, all six ISOs + layup companions"* | `e0de2fc3` | 4,328 | **547** | **458** | **635** |
| **HEAD on disk** | — | — | 4,328 | 547 | 458 | 635 |

sha256: PRE `7f80b94e…55ece0`, REGEN `a3599090…4e85e9e`, GUARD `c4ded33d…f93ff5e`.
**GUARD is byte-identical to the current on-disk file** (`c4ded33d…` both sides), so the
recovered ladder terminates exactly at what the keeper reads today.

PRE's 439/405/509 and REGEN's 640/622/733 **reproduce the `intake_log`'s quoted figures
exactly, in both directions**. That is the identification: these are the right blobs, not
lookalikes.

### 2b. A SECOND, UNSTATED LAYER — found at Phase 0, and it changes the arm design

The charter (and the `intake_log`) describe **one** change. There are **two**, and the current
envelope is not the 640/622/733 state. The merit-order guard (charter §3, adopted at
`6a8f285c`) subsequently **removed** the economic-layup windows into the companion file
`campd-unit-outages-layup-CAISO.csv`. The arithmetic closes with **zero residual**:

| year | kept (GUARD) | layup companion | sum | `intake_log` REGEN |
|---|---:|---:|---:|---:|
| 2023 | 547 | 93 | **640** | 640 |
| 2024 | 458 | 164 | **622** | 622 |
| 2025 | 635 | 98 | **733** | 733 |

So the keeper's input has absorbed a **two-leg** change since its offer curves were identified:
`PRE → REGEN` (the regeneration, +46/+54/+44 %) and `REGEN → GUARD` (the guard, −14.5/−26.4/−13.4 %).
The legs push in **opposite directions** and are therefore capable of partially cancelling —
which is precisely why a single two-arm difference could report "immaterial" while both legs
are individually large. **Pre-registered consequence: the arm design decomposes both legs
(§3), and a null on the net difference does NOT license a null on either leg.**

---

## 3. The arms

Three arms, sequential, each a single bundle spanning 2023 + 2024 + 2025 (rule 16).
Reproduction is by **`--replay-bundle`**, whose documented contract is *"DIR/meta.json supplies
every solve kwarg … so a keeper/probe recipe reproduces without expressing it flag-by-flag"* —
i.e. **not a remembered CLI string**, as the charter requires.

```
uv run python scripts/run_calibration_full.py \
  --replay-bundle results/calibration/caiso175_tac_intake \
  --year 2023 2024 2025 \
  --out-dir results/calibration/<arm> --note "<arm note>"
```

| arm | envelope bytes at solve time | measures |
|---|---|---|
| **A0 — CONTROL** | GUARD = current on-disk (`c4ded33d…`) | the keeper's recipe at THIS head on the CURRENT envelope. Mandatory. |
| **A1 — PRE** | PRE (`7f80b94e…`) | the full pre-change state: what the keeper's calibration was identified against before 07-24. |
| **A2 — REGEN** | REGEN (`a3599090…`) | regeneration applied, guard NOT applied. |

Differences and what each is licensed to claim:

- **A1 → A2 = the REGENERATION leg alone.** This is the chartered object.
- **A2 → A0 = the GUARD leg alone**, re-measured on the *current* keeper (caiso-123 measured
  it on `2026-07-26-caiso120-meritguard-a1`, five keepers and one load-series correction ago;
  that attribution is **not** assumed to transfer and is not quoted as if it did).
- **A1 → A0 = the total unaudited input change** the keeper has absorbed.

**A2 is declared MANDATORY, not conditional**, because of §2b: without it the two legs are
confounded and a cancelling null would be uninterpretable. If A2 cannot be completed for
resource reasons, that is disclosed as a **partial audit** and the regeneration leg is reported
as **NOT ISOLATED** — never inferred by subtraction from an assumption about the guard leg.

### 3a. Envelope swapping — the mutable-file hazard, and how each arm is attested

All three arms read the same path. The file is swapped on disk between arms and restored to
`c4ded33d…` at session end. Adding a CLI/env override to point the loader elsewhere is
**forbidden** (rule 24 `[R-REGISTRY]`: no off-registry tuning channels), so swapping is the
only admissible mechanism.

The hazard is the one `gen_caiso175_attestation.py` names: *"the CSV is a single mutable file
that both arms cannot simultaneously evidence, and re-deriving it post-hoc would attest to
whichever state happened to be staged last."* **Pre-registered defence, fail-closed:**

1. The sha256 of the on-disk envelope is captured **immediately before** and **immediately
   after** each arm's solve; the two must be equal to each other and to that arm's intended
   state, or the arm is **void and re-run**. Both are recorded in the arm's attestation.
2. Each arm is independently evidenced **from its own solved output**, never from the on-disk
   CSV: the per-arm availability envelope is reconstructed from the bundle's own
   `hourly/class_hourly_<year>.parquet` and must order **A1 ≥ A0** and **A1 ≥ A2** in
   available thermal capability (fewer outage windows ⇒ more capability). An arm whose solved
   output does not evidence the envelope it claims fails closed.
3. `lru_cache` on the outage loaders is process-scoped; each arm is a **separate process
   invocation**, so no cache can leak across arms. Asserted, not assumed.

---

## 4. The control predicate — FAIL-CLOSED, key-by-key

caiso-175 measured incidental same-head code drift at **+0.168 / +0.049 / +0.115 $/MWh** on
load-weighted mean LMP — **larger than its own treatment**. Differencing this session's arms
against the keeper's *committed* metrics would therefore misattribute drift to the envelope.
**Every difference quoted in the finding is A-versus-A at the same head.** The keeper's
committed numbers appear in the finding only as a separately-labelled drift disclosure.

**The identity predicate (the caiso-175 predicate, not the caiso-174 one).** This session's
delta is a **data file**, not a `ScenarioConfig` field. Therefore all three arms'
`run_config.json["scenario_config"]` must be **IDENTICAL to each other and to
`results/calibration/caiso175_tac_intake/run_config.json`**, compared **key-by-key over all
692 keys**. **Any** difference at all — one key, any value — means the arms are not comparable
and the session **stops and reports that**, rather than proceeding with a caveat. No key is
exempted, no allow-list is written after seeing the diff.

Instrument: `scripts/probes/_caiso180_arm_identity.py`, which also asserts §3a's sha ladder.
It writes `results/calibration/_caiso180_outage_reaudit.json`.

---

## 5. The cheap rule-14 `[R-ACCURATE]` gate check — pre-registered as a QUESTION, not a lever

The keeper runs `unit_outage_short_windows=False`, `unit_partial_outage_windows=False`,
`unit_outage_maxgen_events=False`. The charter asks whether each is off **because the data is
genuinely empty**, or as an **unexamined default** — and to say which.

Pre-registered as the *check* (the on-disk facts below are input census, read at Phase 0; the
adjudication of what they mean is what §6.5 records):

- `campd-unit-outages-short-CAISO.csv` — 192 B, **header row only, zero data rows**.
- `campd-partial-outages-CAISO.csv` — 206 B, **header row only, zero data rows**.
- `data/raw/maxgen-events/` — contains **only** `miso/` and a README. **No CAISO file exists.**
- `campd-unit-outages-layup-CAISO.csv` — 81 KB, **810 data rows** (2018–2026).

Two candidate readings, both fixed in advance:

- **READING E — "empty by construction."** Both detectors are **coal-only**
  (`outages.py`: `unit_outage_short_derate_factors` filters `plant_group == "COAL"`; the
  partial detector's docstring declares *"the same identification guards as the short windows —
  coal-only detector"*). If CAISO's fleet carries no coal, the files are empty because the
  detector cannot by construction produce a CAISO row, arming the gates would be **provably
  inert**, and the OFF setting is **correct and examined** — not an unexamined default.
- **READING U — "unexamined."** If CAISO *does* carry coal, or if a maxgen/layup input exists
  that the model could consume but does not, that is a **rule-14 finding**.

**Binding clause.** A rule-14 finding here is **reported, NOT armed**. Arming any of these
gates would be a new mechanism requiring its own pre-registration, its own D-4 window and its
own matrix cell; this session does not have that authorization and will not take it by
inference. The layup companion is assessed separately: it is the guard's **record of what was
removed** (§2b's arithmetic closes to zero), so "not read by `src/market_sim`" is evaluated
against *that* purpose before any conclusion is drawn.

---

## 6. Gates and verdict branches — all fixed before any metric is read

### 6.1 Primary metric
**C3a load-weighted mean LMP % error, per year** — CAISO's one live FAIL
(2024 +11.7 %, 2025 +14.8 % on the keeper). Reported for all three years and all three arms.

### 6.2 Full reported surface (no cherry-picking)
All 8 rubric-v3.1 criteria (C1, C2, C3a, C3b, C3c, C4, C6, C8) × 3 years × 3 arms; per-class
annual energy; D-1 / D-2 / D-4 rows from each bundle's own `legitimacy_diagnostics.json`;
C8 forced shares; the availability-envelope census (§3a leg 2). **Every arm is registered on
the dashboard** (rule 15 `[R-DASHBOARD]`), probe and control alike, each with its own
`legitimacy_diagnostics.json` so **C8 stays SCORED**.

### 6.3 Materiality bar
**|Δ| ≥ 1.0 pp on C3a in any year** = **MATERIAL**, on any of the three differences. Chosen to
match the scale caiso-123 itself called material for the extract-content change (+1.24 % λ),
and set **before** any value was read. Sub-bar moves are reported at full magnitude and
labelled **immaterial**; they are never rounded to "no effect".

### 6.4 Verdict branches — and the rule-14 clause that governs all of them

**THE CURRENT ENVELOPE STAYS, IN EVERY BRANCH.** It is the accurate input: current detector,
plus the guard correction the charter adopted. Rule 14 `[R-ACCURATE]` is explicit that a
degraded criterion does **not** revert a correct measured input — the accurate envelope stays
and the residual becomes an **open root-cause issue**. Rule 1 `[R-STRUCT]` adds that a
structurally-correct input is never judged by whether it improves the fit.

- **BRANCH I — MATERIAL, and the current envelope scores WORSE.**
  This is the **rule-14 discovered-bug** signal: the keeper's offer curves were identified
  against the stale envelope and have been silently compensating for it. **No revert.** The
  finding names the compensating mechanism if the D-2 attribution identifies one, and files an
  **open root-cause issue**. Any re-tune is a *later, separately chartered* session, scored
  leave-one-year-out within 2023–2025 before promotion (rule 22).
- **BRANCH II — MATERIAL, and the current envelope scores BETTER.**
  Reported as a favourable measurement. **It is NOT a promotion basis** — C3a is a LIVE FAIL,
  and rule 1 forbids a C3a move being the *reason* for a promotion. The keeper's designation
  does not change on this evidence.
- **BRANCH III — IMMATERIAL on all three differences.**
  The keeper's scored surface is insensitive to the envelope change. The re-audit **CLOSES**,
  and the caiso-171 precondition is discharged **on this item only** — explicitly not a
  statement about the freeze, the marker, or any other precondition, both of which remain the
  owner's.
- **BRANCH IV — the CONTROL fails to reproduce the keeper.**
  If A0's `scenario_config` diverges from the keeper's (§4), the session **stops** and reports
  a reproduction failure. If the config is identical but A0's *metrics* differ from the
  keeper's committed metrics, that is same-head **code drift**: it is disclosed at full
  magnitude as its own finding, and the A-vs-A differences remain valid because they are all
  measured at this head.
- **BRANCH V — A2 not completed.** Partial audit; the regeneration leg is reported as
  **NOT ISOLATED** (§3).

Branches are not mutually exclusive: IV/V may co-fire with I–III and are reported alongside.

### 6.5 Rule-14 gate check verdict
Records **READING E or READING U per gate**, with the evidence, per §5. No gate is armed.

### 6.6 DOF ledger
Pre-registered **UNCHANGED at `n_entries` 11 / `n_residual` 8**. This session introduces no
free parameter — it swaps input bytes and measures. If either count moves, that is a defect in
this session and the attestation refuses to write.

---

## 7. DO-NOT-REDO carried into this session (rule 28 `[R-MECH-MATRIX]`, duty a)

Not re-opened, not re-tested, not re-derived here:

- **`battery_dispatch_adder` — a PERMANENT DECLARED-RESIDUAL DOF.** All three named exits are
  closed: caiso-176 exit 1 (confidential by tariff construction); caiso-178 exit 2 (spent and
  closed); caiso-179 exit 3 (spent and **REFUTED** at $28–$35/MWh). **Not re-derived** from
  NREL ATB, NREL cost benchmarks, PNNL-33283 or LFP warranty documentation — done end to end
  at machine precision, and the ATB publishes no per-MWh augmentation cost at all.
- Routing the LP through `_degradation_cost_per_mwh` — closed (DOF substitution).
- The AS-power-reservation family (caiso-74 / 127 / 129) — closed.
- An **N–S topology lever** (caiso-164 §0/§6) — **FORBIDDEN**.
- `caiso_ps_charge_shape_anchor` — stays **`G`**; the refusal rests on the input being walled.

## 8. Known-open, carried forward unchanged

1. **The N–S congestion majority** — model 5.2 / 2.4 / 2.9 % of the measured NP15–ZP26 basis;
   lever **FORBIDDEN**.
2. **C3a is an OPEN root-cause issue** whose closure route is the **walled** hourly PS water
   state — an owner-level data question, not a session lever. Not attempted here.
3. The DOF ledger's `battery_dispatch_adder` `root_cause` should be re-worded to *permanent
   declared residual* by a future **keeper-lane** session. Not this one.
4. `curate_dam_public_bids.py` cannot process a full CAISO year (~14.3 GB vs ~15 GB RAM,
   caiso-178). Unfixed; needs a data-contract session. **Nothing here depends on it.**

## 9. Deliverables

`PRECHECK-caiso180-outage-reaudit-2026-08-07.md` (this file, pushed first) ·
`FINDING-caiso180-outage-reaudit-2026-08-07.md` · three registered bundles with
`legitimacy_diagnostics.json` each · `scripts/probes/_caiso180_arm_identity.py` ·
`results/calibration/_caiso180_outage_reaudit.json` · CAISO matrix cell + §5.2 header stamped
in this session (rule 28 duty b) · `docs/calibration-log/caiso.md` entry.

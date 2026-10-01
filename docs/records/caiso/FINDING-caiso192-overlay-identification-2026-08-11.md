# FINDING — caiso-192 (lane 1): the mechanical-vs-economic split this lane was chartered to MAKE **HAS ALREADY BEEN MADE**. The merit-order guard is armed in the keeper's own overlay — proven **byte-identically** — so the arm's extract IS the control's extract. **NO ADOPTION, NO A/B, KILLED BEFORE SOLVE**, and the caiso-187 §3 object survives the instrument intact.

**Outcome: the lane's premise is refuted at its first check.** `GATESPEC-caiso192` §1 charters
this session to separate mechanical unavailability from economic layup "using the machinery
already shipped for exactly this question — `build_merit_order_panel` /
`filter_merit_order_layup` — **so that only MECHANICAL spans derate the LP**". Measurement
first, before any rate was computed: **that machinery is already applied to the extract the LP
derates from.** Re-deriving the CAISO extract WITH `--merit-order-guard` reproduces the
committed `data/raw/campd-unit-outages-CAISO.csv` **byte-identically** (sha256
`25360e90a9d11f32c293edf3224047da0d6fab447b551fac81b983e2da1166c6`); re-deriving WITHOUT it
yields a strict **superset** whose surplus is **exactly** the committed layup companion
(810 rows, set-equal, 0 rows lost).

So the "filtered extract" the A/B would arm **is the file the control already solves against**.
The pre-registered delta is empty by construction, and the gates fail besides.

Keeper **UNCHANGED** at `2026-08-09-caiso-188-d1-micseam`. **Zero LP spent. Nothing registered.
No data byte written. DOF ledger untouched.** Both holdout markers untouched (owner acts);
2023–2025 only (rule 22).

Pre-registration: `PRECHECK-caiso192-overlay-identification-2026-08-11.md`, commit `55f703b`,
**pushed to `origin` before the filtered extract was built and before any classification output
existed** (GATESPEC §7). Instrument: `scripts/probes/_caiso192_overlay_identification.py`.
Record: `_caiso192_overlay_identification.json`.

---

## 0. Direction-hazard regime (quoted verbatim from GATESPEC §0, as required, and binding here)

> The expected sign of this repair flatters C3a. C3a movement is therefore
> inadmissible as evidence for or against acceptance (rules 1, 13, 14). Acceptance is
> decided solely on the structural gates pre-registered below, authored by caiso-191
> before measurement. C3a is reported for transparency only. If gates pass and C3a
> worsens, the arm is still accepted (caiso-183 precedent). If gates fail and C3a
> improves, the arm is still rejected.

**Discharged, and it did real work here.** The rejection below rests on G-RATE, G-STAB and
G-SEP alone. **C3a was never read in this session — not as a level, not as a delta, not as a
tiebreak.** No solve ran, so no C3a value of this arm exists to report; the keeper's standing
+3.4 / +10.4 / +12.9 % is quoted nowhere in the decision path and is restated here only as the
unchanged incumbent state.

---

## 1. Rule 28 duty (a) — DO-NOT-REDO discharged

The CAISO in-model lever queue is **EMPTY and CLOSED** (matrix §5.2). This session is chartered
campaign work under owner ruling 1 (`caiso191-owner-rulings-2026-08-11.md`), not a new lever.
No cell adjudicated `R`/`I`/`G` was re-tested. The mechanism's own row,
`campd_outage_windows`, is CAISO cell **K** — and, as §5 records, **its note already carried
the fact this session re-measured**.

---

## 2. §A — THE REPRODUCTION, which is the whole finding

Both arms of the check were run through the shipped CLI end to end (a subprocess, not an
in-process reimplementation), over the extract's full derived span 2018–2026:

| derivation | sha256 | rows | vs committed |
|---|---|---:|---|
| committed `campd-unit-outages-CAISO.csv` | `25360e90…1166c6` | 4,328 | — |
| re-derived **WITH** `--merit-order-guard` | `25360e90…1166c6` | 4,328 | **BYTE-IDENTICAL** |
| re-derived **WITHOUT** the guard | `64502f67…472e0c` | 5,138 | strict SUPERSET, +810 / −0 |

And the surplus is not merely the same size as the guard's output — it **is** the guard's
output: `set(unguarded) − set(committed)` is **set-equal to the 810 rows of the committed
`campd-unit-outages-layup-CAISO.csv`** (`unguarded_minus_committed_equals_layup: true`), whose
group split is CC_REGULAR 309 / CT_CHP 213 / ST_GAS 156 / CC_CHP 132.

**Therefore the ARM cannot differ from the CONTROL.** The GATESPEC §6 arm is "control + the
filtered overlay extract"; the filtered overlay extract is byte-identical to the control's.
Solving the pair would have spent hours to measure a guaranteed zero.

### 2a. Three independent cross-checks, none of which this session chose

Each reproduces a figure published by an earlier session from a different code path:

| published | source | measured here | match |
|---|---|---|---|
| extract sha256 `25360e90` | caiso-183 (matrix `campd_outage_windows` note) | `25360e90` | ✅ |
| recipe `--iso CAISO --years 2018 … 2026 --merit-order-guard --hour-grain` | caiso-183 | reproduces byte-identically | ✅ |
| layup rows 93 / 164 / 98 (2023/24/25) | caiso-180 (`547+93=640, 458+164=622, 635+98=733`) | 93 / 164 / 98 | ✅ |
| `X_c` CC_REGULAR 0.2157 / 0.2621 / 0.3186 | caiso-187 §3a, shipped loader | 0.215691 / 0.262054 / 0.318613 | ✅ |

The last is the important one: **this session's implementation of the frozen caiso-187 §2
formula reproduces caiso-187's own published `X_c` to six decimals**, so the G-RATE basis is
the one the GATESPEC names and not a re-specification of it.

---

## 3. §B — what the guard already does, and how far short of the band that leaves the overlay

`X_c` through the SHIPPED loader `outages.unit_outage_derate_factors`, measured on the
committed extract (POST-guard, i.e. what the LP applies) and on the counterfactual PRE-guard
extract (committed ∪ the layup companion, written to a temp path — `data/raw` never touched):

| class | year | PRE-guard `X` | **POST-guard `X`** | guard already removes |
|---|---|---:|---:|---:|
| CC_REGULAR | 2023 | 0.230307 | **0.215691** | −1.46 pp |
| CC_REGULAR | 2024 | 0.279544 | **0.262054** | −1.75 pp |
| CC_REGULAR | 2025 | 0.338549 | **0.318613** | −1.99 pp |
| CC_CHP | 2023 | 0.176757 | **0.163439** | −1.33 pp |
| CC_CHP | 2024 | 0.246236 | **0.207902** | −3.83 pp |
| CC_CHP | 2025 | 0.291796 | **0.272236** | −1.96 pp |

*(Measured only after fixing a defect in this session's own probe: `unit_outage_derate_factors`
is `@lru_cache`d and the extract path is not among its arguments, so the first counterfactual
returned the cached committed-extract result and printed a spurious `0.0 pp` for every class.
Reported because it was caught by the result being too clean, and because a later session
reaching for the same measurement device will hit it too.)*

**The guard is armed, it is working, and it is small.** It moves CC_REGULAR by 1.5–2.0 pp
against a band that needs a further **7 to 17 pp** of reclassification. The 24–35 % removal
caiso-187 found is a **post-guard** number, and the residual is **not** economic layup of the
kind this instrument detects.

---

## 4. §C — G-SEP: the classifier separates cleanly; its SEASONALITY signature runs the wrong way

Capacity-weighted over span-hours, scope classes `{CC_REGULAR, CC_CHP}`, via the shipped
`MeritOrderPanel.out_of_merit_share`:

| year | reclassified (layup) OOM | retained (mechanical) OOM | separation | layup Mar–May | retained Mar–May |
|---|---:|---:|---:|---:|---:|
| 2023 | 0.9657 | 0.0611 | **90.46 pp** | 0.3119 | **0.4582** |
| 2024 | 0.9872 | 0.0440 | **94.31 pp** | 0.3522 | **0.4710** |
| 2025 | 0.9742 | 0.0449 | **92.93 pp** | 0.2501 | **0.3734** |

Legs (a) and (b) pass emphatically — the guard's own frozen near-binary identification
reproduces on CAISO, and the two populations are ~90 pp apart. **Leg (c) fails in all three
years, in the opposite direction to the one the GATESPEC predicted**: the RETAINED spans are
*more* spring-concentrated than the reclassified ones, not less.

That failure is informative rather than merely fatal. The GATESPEC expected the *economic*
spans to carry the spring-surplus concentration; measurement puts the spring shape on the
**mechanical** spans — which is the classic planned-maintenance signature caiso-187 §3c
described, sitting exactly where a planned-outage reading predicts it. It is evidence
**against** the residual being economic displacement, and it is why the failure of G-RATE is
not plausibly cured by a deeper version of this instrument.

**Fail-safe verified, not weakened (GATESPEC §4.1):** retained spans the panel cannot identify
— 15 / 28 / **164** in 2023 / 2024 / 2025 — carry no out-of-merit share and **stay mechanical**.
The 2025 jump is the fail-safe doing more work, in the conservative direction, in the year the
removal rate is highest. Nothing was done to reduce it.

---

## 5. THE CONTRADICTION, stated plainly

`FINDING-caiso187` §6 option 1 — the text the owner granted — reads: *"it is **not
data-blocked** … `outage_detect.py` already ships `filter_merit_order_layup` and
`build_merit_order_panel` — machinery built for exactly this question"*. That is true of the
machinery and **false of its application state**: the machinery was not merely available, it
was **already applied** to the very extract caiso-187 measured `X_c` on. `GATESPEC-caiso192`
inherited the reading and chartered an A/B whose two arms are the same file.

**The repo already knew.** Two committed records carry it explicitly:

* the matrix `campd_outage_windows` CAISO note (caiso-183): *"regenerable byte-identically from
  `derive_campd_unit_outages.py --iso CAISO --years 2018 … 2026 **--merit-order-guard**
  --hour-grain`"*, with the sha256 `25360e90` printed;
* the matrix `outage_artifact_provenance` row (xiso-2, 2026-08-02): *"all six re-derived at HEAD
  with the committed recipe (`--years 2018..2026 --merit-order-guard`) … ERCOT, **CAISO**, PJM,
  NYISO, NEISO all BYTE-IDENTICAL"*.

caiso-180 had additionally already **measured this mechanism's LP effect**: *"the GUARD leg is
INERT (−0.10 pp every year, favourable)"*. So the lane's arm was not only empty — it had been
solved and found inert eight sessions earlier.

**This is a pre-registration failure of the caiso-187 → caiso-191 chain, not a measurement
failure of the guard**, and it is exactly the caiso-188 §7 item 5 lesson recurring one row
over: *"check the DATA the gate resolves through"*. caiso-188 established that a `run_config`
flag recorded as armed does not prove the mechanism ran. **caiso-192 adds the mirror image: a
mechanism's machinery sitting un-called in a module does not prove it is un-applied — the
committed artifact may already be its output.** The cheap discriminator in both directions is
a byte-level re-derivation, which costs minutes.

---

## 6. GATE TALLY (GATESPEC §3 / §4 / §5)

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-RATE** | post-filter CC_REGULAR `X` ∈ [0.07, 0.15] in EACH year | **0.2157 / 0.2621 / 0.3186** | **FAIL** — all three years above the band (1.4× to 2.1× the ceiling). Not the below-0.07 over-reclassification kill; the plain band failure. |
| **G-STAB** | YoY ≤ 3 pp **and** 2025 ≤ 1.5 × 2023 | YoY **+4.64 pp**, **+5.66 pp**; ratio **1.4772** | **FAIL** — the YoY leg fails in both steps. The ratio leg passes (1.4772 ≤ 1.5) and does not rescue it. |
| **G-SEP** | (a) layup OOM ≥ 0.80 · (b) separation ≥ 30 pp · (c) layup Mar–May > retained Mar–May | (a) 0.966/0.987/0.974 ✅ · (b) 90.5/94.3/92.9 pp ✅ · (c) 0.312<0.458, 0.352<0.471, 0.250<0.373 ✗ | **FAIL** on leg (c), all three years, in the direction opposite the prediction. |
| **G-LOYO** | shipped constants AS SHIPPED; any new threshold pre-committed + LOYO-stable | **no new threshold, no new parameter**; `MERIT_RCC_PCTL 0.90`, `MERIT_OOM_FRAC 0.90`, `REAL_RUN_CF`, `MIN_REAL_RUN_HOURS`, `MERIT_HR_MIN/MAX` untouched | **PASS (vacuous)** — declared in PRECHECK §3 before any output existed; nothing to hold out. |
| **G-CONS** (§4 conservative defaults) | ambiguous stays mechanical · no partial-span splitting · no subset arming | fail-safe verified live (15/28/164 unidentified spans retained); windows whole; scope = the entire covered class population | **PASS** — verified and not weakened. |
| **§5 DOF** | ledger increase ⇒ automatic fail | ledger **untouched**, 11 / 8 | **PASS** |
| **§2 instrument closure** | no LMP/price series anywhere | **none read** — the only price series in the path is the delivered fuel price the shipped panel builds for itself | **PASS** |

**ALL GATES: 3 FAIL (G-RATE, G-STAB, G-SEP), 4 PASS. ADOPTED: NO.**

Per GATESPEC §5, any §3 gate failing ⇒ the filtered extract is not adopted, nothing is
promoted, and the cell is stamped from this evidence. **Kill before solve is the pre-registered
outcome and it is honorable.** The lane inventory is CLOSED; no improvised variant was
attempted, and none is proposed.

### 6a. The single-mechanism statement, and why it is NOT asserted

GATESPEC §6 requires verbatim in this FINDING: *"The A/B delta is the merit-order-filtered
CAISO outage extract; no other input, field, or constant differs."* **That sentence is quoted
here as a requirement and is expressly NOT asserted as a fact of this session**, because no A/B
exists to assert it of: the two arms' extracts are byte-identical (§2), so the delta is not
"the filtered extract" — it is **empty**. Asserting the sentence would describe a comparison
that was never run.

**CONTROL-ε: NOT MEASURED.** GATESPEC §6 requires the control to meet the ratified tolerance
(per year |ΔC3a| ≤ 0.1 pp, |ΔC3b| ≤ 0.005) and to quote its achieved deltas as the noise floor
*before any arm solves*. **No arm solved, so no control was run and no noise floor was
measured.** The control recipe's two environment conditions — the capacity-deliverability clean
partition materialized (the `seam import cap set to 16055 / 16452 / 16148 MW` log lines) and
`hydro_ror_split` explicitly False — were therefore **never exercised in this session** and
nothing about them is claimed. They remain owed by the next lane that solves.

---

## 7. Governance

**Rule 1 `[R-STRUCT]`** — the rejection is structural; C3a was never read, and the
direction-hazard clause is quoted at §0 and discharged. **Rule 13 `[R-MEASURED]`** — every
figure counted from a committed measured artifact; no measured outcome, price residual or
benchmark entered any input or any bar. **Rule 14 `[R-ACCURATE]`** — no accurate input was
reverted; the measured input was preferred and it refuted the charter. **Rule 15 / 16** — **no
run completed, so none is registered**; stated explicitly so the absence is not read as a
skipped registration (the caiso-187 and ercot-174 precedent). **Rule 19 `[R-ONE-MECH]`** — the
finding *is* a one-mechanism result: the mechanism is already the incumbent, so a second
application of it would have been a stack on itself. **Rule 21 `[R-DOF]`** — ledger 11 / 8
untouched; no parameter added, none retired. **Rule 22 `[R-HOLDOUT]`** — no year solved, scored
or registered; gate statistics restricted to 2023–2025; the extract's 2018–2026 span was read
as an INPUT for the byte-reproduction identity, which is data preparation, not a spend
(*"what is held out is the SCORE, never the DATA"*); `calibration-complete.json` /
`holdout-freeze.json` untouched. **Rule 23 `[R-FROZEN-DERIVE]`** — **no derive output was
committed and no constant re-valued**; the two re-derivations were written to a temp directory
and compared, and `data/raw` is byte-unchanged (the rule-23 licence the PRECHECK recited was
therefore never spent). **Rule 24 `[R-REGISTRY]`** — no new field, no env knob, no hand-edited
table. **Rule 25 `[R-ISO-SCOPE]`** — CAISO only; no other ISO's extract, cell, keeper or
constant touched, and no verdict transferred in or out. **Rule 27 `[R-PUSH]`** — PRECHECK
committed and pushed before the measurement existed; no file ≥300 lines rewritten from
generated content. **Rule 28 `[R-MECH-MATRIX]`** — duty (a) at §1; duty (b) discharged in this
session on the CAISO shard only.

**Environment disclosure.** The session's container came up with a **broken working tree**: an
empty git index, a checkout aborted partway through `data/`, and a stale `.git/index.lock`
(no live git process). `src/`, `scripts/`, `results/`, `docs/` and `frontend/` were absent. The
tree was restored from `HEAD` (11,754 files) and dependencies installed with `uv sync` before
any measurement; `git status` was clean at the branch point and the branch was cut from a
freshly fetched `origin/main` (`f6381c5`). No repository content was reconstructed by hand —
every file is the committed blob.

---

## 8. Known-open, carried forward

1. **The caiso-187 §3 object is UNEXPLAINED AND UNCHANGED.** CC_REGULAR removal 21.6 / 26.2 /
   31.9 %, growing +48 % in two years, against a ~10 % published planned-plus-forced
   expectation. This lane's instrument accounts for **1.5–2.0 pp** of it. The remainder is
   **not** merit-order economic layup, and §4's seasonality points at the planned-maintenance
   reading rather than the economic one.
2. **The lane-2 composition obligation is UNCHANGED and NOT re-based.** GATESPEC §8 and
   integration protocol §5 require re-verifying `X_c^filtered ≥ W_c` for CC_REGULAR and CC_CHP
   *if this lane's extract is accepted*. **It is not accepted**, so lane 2 composes on the
   committed extract exactly as caiso-187 measured it — and that measurement was already
   post-guard, so `X_c^filtered` **is** the `X_c` in caiso-187's table. The recheck is
   satisfied by identity, with no recomputation of lane 2's value: `X` 0.2157/0.2621/0.3186
   (CC_REGULAR) and 0.1634/0.2079/0.2722 (CC_CHP) against `W` 0.050 / 0.040. No promotion of
   this arm occurs, so the caiso-189 §8.3 C3c re-measurement obligation does not fire.
3. **The integration protocol's RUNG 1 is EMPTY.** Per §2 of the protocol a lane that
   kill-before-solves "is simply absent; the ladder renumbers by omission and does NOT backfill
   with a substitute." Wave 2 begins at the caiso-188 control with lane 2.
4. **A pre-registration hygiene item for the campaign, not a lane:** a gate spec that charters
   an arm should verify the arm's input is not already the incumbent — a byte-level
   re-derivation costs minutes and would have caught this before the owner spent a ruling on it.
   Filed as an observation; **no gate spec is amended by this session** (they are caiso-191's
   and the inventory is closed).
5. **The unguarded re-derivation is NOT a defect and is not filed as one.** The +810-row
   superset is the guard's own vetoes, reproduced exactly; the extract and its companion are
   mutually consistent and both re-derive.

---

## SESSION-REPORT caiso-192 overlay-identification

**STATUS:** COMPLETE — lane 1 measured, **killed before solve** on its own pre-registered gates.
Keeper UNCHANGED at `2026-08-09-caiso-188-d1-micseam`. Zero LP. Nothing registered. No data byte
written. DOF 11 / 8 untouched.

**GATES (per GATESPEC):** **G-RATE FAIL** (0.2157 / 0.2621 / 0.3186 vs [0.07, 0.15], all three
years above) · **G-STAB FAIL** (YoY +4.64 / +5.66 pp vs ≤3 pp; ratio 1.4772 ≤ 1.5 passes) ·
**G-SEP FAIL** on leg (c) (layup Mar–May 0.312/0.352/0.250 < retained 0.458/0.471/0.373 — the
opposite direction), legs (a) 0.966/0.987/0.974 ≥ 0.80 and (b) 90.5/94.3/92.9 pp ≥ 30 pp both
PASS · **G-LOYO PASS (vacuous** — no new threshold) · **G-CONS PASS** (fail-safe verified,
15/28/164 unidentified spans stay mechanical) · **DOF PASS** · **instrument closure PASS** (no
price series read anywhere). **3 FAIL / 4 PASS.**

**ADOPTED:** **NO.**

**A/B:** **KILLED BEFORE SOLVE** — and, independently, **impossible as specified**: re-deriving
with `--merit-order-guard` reproduces the committed extract **byte-identically** (sha256
`25360e90…1166c6`), so the arm's extract IS the control's. The unguarded derivation is a strict
superset whose +810 surplus is set-equal to the committed layup companion.

**CONTROL-ε:** **NOT MEASURED** — no arm solved, so no control was run. The ratified tolerance
(|ΔC3a| ≤ 0.1 pp, |ΔC3b| ≤ 0.005) was never exercised, and the control recipe's two environment
conditions (materialized capacity-deliverability partition; `hydro_ror_split` False) were not
verified in this session. Owed by the next solving lane.

**C3a (reported only):** **NOT READ.** No solve, so no arm value exists. The incumbent keeper's
standing +3.4 / +10.4 / +12.9 % is unchanged and played no part in the decision.

**MATRIX / LOG:** updated in-session — `campd_outage_windows` CAISO cell note stamped with this
lane's rejection (rule 28 duty b, rejected outcome included); `docs/calibration-log/caiso.md`
appended. Cell letter stays **K** (the mechanism is armed in the keeper — that is the finding).

**FILES PUSHED + PR:** `PRECHECK-caiso192-overlay-identification-2026-08-11.md` (pushed first,
commit `55f703b`) · `scripts/probes/_caiso192_overlay_identification.py` ·
`results/calibration/_caiso192_overlay_identification.json` · this FINDING ·
`docs/codebase-site/data/mechanism-matrix/CAISO.js` · `docs/calibration-log/caiso.md`.
PR: *caiso-192: overlay mechanical-vs-economic identification*.

**CONTRADICTIONS:** **One, material.** `FINDING-caiso187` §6 option 1 and `GATESPEC-caiso192`
both charter this lane as if the merit-order guard were an available **un-applied** fix. It was
already applied to the extract caiso-187 measured `X_c` on — so the published 21.6/26.2/31.9 %
is a **post-guard** figure, and the lane had no headroom from the outset. Two committed records
already said so (matrix `campd_outage_windows` caiso-183 note, printing both the
`--merit-order-guard` recipe and the sha256 `25360e90`; matrix `outage_artifact_provenance`
xiso-2 row), and caiso-180 had already measured this mechanism's LP effect as **INERT**
(−0.10 pp/yr). Also disclosed: a probe defect of my own (`@lru_cache` on
`unit_outage_derate_factors` silently returned the cached committed-extract result for the
counterfactual, printing a spurious 0.0 pp) — caught, fixed, reported.

**OPEN ITEMS / HANDOFF:** (1) the caiso-187 §3 object stands, with this instrument accounting
for only 1.5–2.0 pp of a 21.6–31.9 % removal, and §4's seasonality favouring the
planned-maintenance reading over the economic one; (2) integration-protocol RUNG 1 is **empty**
— Wave 2 starts from the caiso-188 control with lane 2, no backfill (protocol §2); (3) the
lane-2 `X_c^filtered ≥ W_c` recheck is **satisfied by identity** (caiso-187's `X_c` was already
post-guard) and lane 2's value is NOT recomputed; (4) the caiso-189 §8.3 C3c re-measurement does
not fire (no promotion); (5) environment: this container's working tree was restored from `HEAD`
before work began — see §7.

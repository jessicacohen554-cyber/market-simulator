# PREREG nyiso-211 — attribute the **Cricket Valley / CPV Valley CC_REGULAR deficit** to a step in the committed keeper lineage

**Session:** nyiso-211, NYISO backcast calibration. **Branch:**
`claude/nyiso-cc-regular-zonal-pa77pn`, off `main` `c7234b3b`. **Date:** 2026-09-07.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **Committed and pushed BEFORE any measurement is read.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads CALIBRATED with zero
failing criteria. Nothing in this session is selected because a residual moved
(rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`). The target is a **structural defect that C1
currently PASSES over**: the zonal cancellation nyiso-210 measured.

**Rule 22.** Every year read here is **in-sample (2023, 2024, 2025)**. 2022 is **not read at all**
by this pre-registration. 2020, 2021 and the locked test are untouched. No marker byte moves.

---

## 1. The object

nyiso-210 (`docs/FINDING-nyiso210-cc-regular-2022-zonal-cancellation-2026-09-06.md` §5) hands
forward one lead as "the sharper end":

> The Cricket Valley / CPV Valley deficit is monotone (−0.441 → −0.608 → −1.010 TWh at Cricket)
> and it is the *growing* half of the offset. nyiso-186 recorded Cricket Valley as the **largest
> positive** excess of 2023 (+1.24 TWh on its own basis); on the current keeper it is a
> **deficit**. Whatever moved it between those keepers over-corrected.

**This session's object is that swing, and only that swing:** which step of the committed keeper
lineage moved plant **57185 (Cricket Valley Energy, Capital_Hudson, 1,312 MW npl)**, and — if it
is a single step — whether that step also explains the deficit's **growth** across 2023→2025.

**The object is entirely in-sample and entirely answerable from artifacts already committed to
`main`. Zero LP is budgeted.** Rule 29 step 0 only. No screen is pre-registered, because phase 0
has not yet returned a lever; if it returns one, the screen year will be named in a **separate,
later** pre-registration, chosen by the mechanism's own measured footprint and never by a residual.

## 2. The instrument, and what was read before this document was written

### 2.1 The lineage, and which steps are single-flag isolable

Rule 15's keeper-only retention has pruned every NYISO bundle except three keeper-lineage runs
plus the touchpoint. The committed model-side anchors at **plant grain** are therefore exactly
four:

| anchor | source of per-plant model energy | isolable? |
|---|---|---|
| **nyiso-186 control** | `results/calibration/_nyiso186_cc_attribution.json` → `years.<y>.plants[].model_mwh` | bundle pruned; record only |
| **`2026-09-05-nyiso-192-astoria-panel`** | `frontend/data/backcast/runs/<id>.js` → `m_ann` / `m_mon` | — |
| **`2026-09-06-nyiso-196-extract-basis`** | same | **YES** — `meta.json` diff 192→196 is exactly one live flag, `unit_outage_extract_basis_share: absent → True` |
| **`2026-09-06-nyiso-202-startup-aware`** | same | **YES** — `run_config.json` diff 196→202 is exactly one live flag, `nyiso_gas_bridge_startup_aware: absent → True` (every other moved key is a new dataclass default or a forecast-only field) |

So the three steps are:

* **Δ₁ = 186 → 192** — **LUMPED and NOT isolable.** It spans several promotions whose bundles are
  pruned (nyiso-192's own sidecar records its parent keeper as `2026-09-05-nyiso-189-steam-identity`).
  A Δ₁ verdict names a *region of the lineage*, never a flag.
* **Δ₂ = 192 → 196** — **`unit_outage_extract_basis_share`, single flag.**
* **Δ₃ = 196 → 202** — **`nyiso_gas_bridge_startup_aware`, single flag.**

**Δ₂ is my preferred answer before measuring**, on the strength of nyiso-196's own registry
definition, which names the plant: *"Cricket Valley 57185 id-collision under-derate repaired"*.

### 2.2 Basis discipline (the handoff's binding instruction)

**CAMPD on both sides, in every year, at every anchor.** The measured side is
`frontend/data/backcast/bench/NYISO/<year>.json.gz` → `plants.<code>.c_ann` / `c_mon`, which is
the basis nyiso-210 §3 used. The nyiso-186 record carries its own CAMPD column
(`campd_cc_gross_mwh`) beside its E-923 column (`e923_cc_mwh`); **its E-923 column is not used**,
and its headline `E_twh` statistic — a one-sided positive-excess sum on the E-923 basis — is
**not** the quantity compared here. **No CAMPD-basis gap is ever quoted as a C1 number**
(C1 scores against bench `classFull`, which sits below the CAMPD plant sum by −0.44 / −2.38 /
−0.34 TWh in 2023/24/25 — nyiso-210 §6.3).

Because the measured side is constant within a year, **Δgap ≡ Δmodel at every step**, which is
what makes the decomposition exact and additive:

    Δ_total(186→202) = Δ₁ + Δ₂ + Δ₃    (identity, per plant, per year)

### 2.3 Instrument vocabulary — checked before this pre-registration

Per the handoff's binding method, the instrument's vocabulary was inspected first. What was read,
in full, before this document was written:

1. `_nyiso186_cc_attribution.json` **structure**, and the **one sample plant record it happened to
   print first, which is 57185 in 2023** — `model_mwh` 6,445,015; `e923_cc_mwh` 5,200,678;
   `campd_cc_gross_mwh` 5,321,416; `E_twh` 1.2443. **Disclosed, not concealed.** This fixes the
   186 anchor for Cricket Valley 2023 and therefore fixes the *sign* of Δ_total there; it does
   **not** fix Δ₁, Δ₂ or Δ₃, which is where every verdict below lives, and it says nothing about
   2024, 2025, CPV Valley, or the three over-runners.
2. The `meta.json` / `run_config.json` **flag diffs** in §2.1 — configuration, not results.
3. The three runs' registry **definitions** — run definitions, not scores.
4. `_nyiso196_rebuild_checks_2024.json` **structure** and its first ten `F2_identity` rows
   (plants 2500…50451). **57185's row was not read**, and no 2023 or 2025 rebuild exists yet.
5. `scripts/probes/nyiso210_cc_overrun_attribution.py` — the payload/bench decode path, reused
   verbatim so both sessions read the same instrument.

Nothing in the payloads of 192/196/202 has been read at plant grain.

## 3. Predictions

### 3.1 Instrument identities (must pass, or the affected anchor is dropped and said so)

* **I1 — the 186 anchor's measured side is the bench's.** For every CC_REGULAR plant carried by
  both `_nyiso186_cc_attribution.json` and the bench, in 2023/2024/2025:
  `|c_ann − campd_cc_gross_mwh/1e6| ≤ 0.02 × campd_cc_gross_mwh/1e6`.
  **If I1 fails**, the 186 anchor is not on the bench's CAMPD basis, Δ₁ is not comparable, and the
  attribution is reported on the **payload-only lineage 192→196→202** with the failure stated —
  never repaired into a pass.
* **I2 — payload plant sum reconciles to the bundle's own class total.** For each of 192/196/202
  and each of 2023/2024/2025: `|Σ_plants m_ann − class_hourly(CC_REGULAR, P1)| / class_hourly
  ≤ 0.05` (nyiso-210's tolerance, unchanged).
* **I3 — the rebuild instrument reproduces at HEAD.** `scripts/probes/nyiso196_rebuild_checks.py
  --year 2024` re-run at this session's HEAD reproduces the committed record's
  `mean_avail_keeper` and `mean_avail_arm` for **every** plant in `F2_identity` to 4 dp. **If I3
  fails**, no 2023/2025 rebuild is quoted and P6 is reported UNMEASURABLE.

### 3.2 The attribution — three mutually exclusive, jointly exhaustive outcomes

All measured on plant **57185**, year **2023**, CAMPD basis, with
`S = |Δ₁| + |Δ₂| + |Δ₃|`:

* **P1 (PREFERRED) — the extract-basis repair is the dominant mover.**
  Fires iff `|Δ₂| ≥ 0.60 × S` **and** `Δ₂ < 0`.
* **P2 — the mover is upstream of nyiso-192.** Fires iff `|Δ₁| ≥ 0.60 × S`. Then the swing belongs
  to a promotion whose bundle is pruned, `unit_outage_extract_basis_share` is exonerated, and the
  next session's object is a git-history question, not a flag.
* **P3 — diffuse.** Fires iff no step reaches `0.60 × S`. Then "whatever moved it over-corrected"
  is false as posed: no single promotion owns the swing.

(`Δ₃ ≥ 0.60 × S` is arithmetically possible and would fire neither P1 nor P2; it is folded into
**P3** by construction and will be **named explicitly** in the report if it occurs.)

### 3.3 The prediction declared to HURT the preferred answer

* **P4 — the repair is year-flat while the deficit grows, so P1 cannot be the whole story.**
  Fires iff **both**: (a) the coefficient of variation (population stdev / |mean|) of
  `Δ₂(57185)` across 2023/2024/2025 is **≤ 0.35**; and (b) the keeper's 57185 CAMPD-basis deficit
  grows monotonically in magnitude across 2023 → 2024 → 2025.
  **I expect P4 to FIRE.** A static id-collision repair on a fixed overlay should move a plant by
  a roughly year-stable amount, whereas nyiso-210 measured the deficit growing −0.441 → −0.608 →
  −1.010. If P4 fires alongside P1, then **P1 names the step that flipped the sign and explicitly
  does NOT explain the growth** — a second, growing object exists that this session has not named,
  and the report must say so at full strength rather than presenting P1 as a closed answer.

### 3.4 Controls and falsifiers

* **P5 — the lineage did not move the three persistent over-runners.** For each of **2539**
  (Bethlehem), **56196** (Zeltmann), **55375** (Astoria Energy) in 2023:
  `|Δ_total(186→202)| < 0.5 TWh`.
  **Falsifier:** if any of the three moves ≥ 0.5 TWh, the lineage redistributed *within* the class
  and nyiso-210 §5's "persistent over-runner" reading is partly lineage-induced, not a standing
  keeper property. Reported either way.
* **P6 — the repair's own measured footprint at 57185 is year-stable** (the pre-solve counterpart
  of P4(a), on the mechanism rather than on the dispatch). From
  `nyiso196_rebuild_checks.py --year {2023,2024,2025}`: the CV of
  `(mean_avail_arm − mean_avail_keeper)` at plant 57185 across the three years is **≤ 0.35**.
  Conditional on I3. If P6 and P4(a) disagree, the disagreement is the finding and is reported as
  such.
* **P7 (REPORTED ONLY, no verdict hangs on it) — CPV Valley moves with Cricket Valley at Δ₂.**
  `|Δ₂(56940)| ≤ 0.25 × |Δ₂(57185)|` is the *plant-specific-repair* reading; a larger move means
  the flag is a fleet-wide CC basis change rather than the named id-collision. Both readings are
  legitimate; this is characterization, not a gate.
* **P8 (REPORTED ONLY) — redistribution, not level.** CC_REGULAR class-grain
  `|Δ_total(186→202)|` on the CAMPD basis in 2023, indicative bar 0.5 TWh. If the class barely
  moves while 57185 moves ~1.5 TWh, the lineage redistributed inside the class.

## 4. What this session will NOT do

* **No solve, no screen, no arm, no bundle, no registration.** Rule 29(c) therefore has nothing to
  delete and rule 15 has nothing to register. G-DRIFT is not owed (no control is differenced for
  an arm); the nyiso-198 rebuild reproduction is run as an **environment check** only.
* **No mechanism, parameter, coefficient, offer curve, derive script, scorer, marker, keeper or
  gate is moved.** D-5(b) does not attach (no candidate).
* **Nothing is re-tested that nyiso-210 closed** — forcing as the CC_REGULAR driver, availability
  as a 2022 object, a fleet-wide fuel-level merit effect, `dual_fuel_switching`, the band axis for
  a model-vs-measured question — and nothing marked `R`/`I`/`G` in
  `docs/codebase-site/data/mechanism-matrix/NYISO.js` is re-tested.
* **No owner card is pre-judged.** All five pending NYISO rulings stay unruled. Whether C1 should
  see a zonal decomposition remains an owner question and is not asked here.
* **Rule 25:** NYISO only. The MISO gate-(a) provenance failure at HEAD is re-measured and
  reported, never repaired from this lane.

## 5. Honest-failure clause

nyiso-210 is the template **and** the cautionary tale: its pre-registered verdict fired while the
mechanism that verdict was declared to indicate was refuted on the same artifacts. If that happens
here — if P1 fires but the repair turns out not to be a repair, or if P4 fires and guts P1's
reading, or if I1 fails and the 186 anchor dissolves the swing itself — **both halves are
reported at full strength and no statistic is repaired into a pass.**

**A clean negative is the session's result, not a null.**

---

*(nyiso-211, pre-registered 2026-09-07, before any payload was read at plant grain.)*

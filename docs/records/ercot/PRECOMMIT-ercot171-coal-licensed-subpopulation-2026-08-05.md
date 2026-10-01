# PRECOMMIT — ercot-171: a LICENSED sub-population instrument for the 2023 COAL rows, to settle the two NOT-IDENTIFIABLE-2023 limbs

**Session ercot-171, 2026-08-05. PHASE 0 — NO LP, no solve, keeper UNCHANGED
(`2026-08-05-run168b-year-curves`), no `ScenarioConfig` field written.**
Committed and pushed **before** any derive or probe runs. Every threshold, band,
window and verdict branch below is fixed here and **may not be moved after
measurement, in either direction**.

## 0. The charter, and its authorization

ERCOT-169 measured the fuel-invariance claim of the three armed ERCOT margin
identifications and returned a split outcome: limb **B**
(`CC_COMMITTED_OFFER_LEVEL_BY_ISO`) **CONFIRMED**, limbs **A**
(`COAL_OFFER_MARGIN_LEVEL_BY_ISO`, ERCOT-137) and **C**
(`COAL_PEAK_OFFER_LEVEL_BY_ISO`, ERCOT-140) **NOT-IDENTIFIABLE-2023** — the
instrument's own ERCOT-138 §3.4 licensing test fails on the delivery-2023 COAL
rows (`curve_share` **0.9702**, full-day 0.9794, against the **0.9876** floor the
constants were licensed on). Per its pre-registered rule the verdict was withheld
**in both directions** and both extrapolation notes stand.

ERCOT-169 §6 handed the owner three options. **Owner adjudication, in-session
2026-08-05: option 2 — "charter a licensed sub-population instrument for the 2023
COAL rows."** That is this session's whole charter. It is the fresh adjudication
ERCOT-169 required; it does **not** authorize building or arming anything (§3).

**Limb B is out of scope.** It is already CONFIRMED and its extrapolation note is
already retired by verification. Nothing here touches it.

## 1. The construction

**Everything is imported, never re-implemented** — the ercot-169/170 discipline.
`scripts/lib/sced_corpus_instruments.py` supplies the delivery-year corpus
loader, the unchanged ercot-123/144 row filters, the CPT→CST conversion at
derivation, the `LIMBS` registry, the fuel basis and `assess_limb`'s
pre-registered arithmetic; `ercot123._decompose`, `ercot136._curve`/`._wq` and
`ercot138.measured_curves` are called verbatim through it.

**The verdict arithmetic is ERCOT-169's, UNCHANGED:**

```
level₂₀₂₃ = measured_instrument₂₀₂₃ − HR × (fuel₂₀₂₃ − anchor)      vs      armed constant
```

with the same constants: limb A `HR` 10.9832, coal anchor 1.7387, `fuel₂₀₂₃`
**1.8169**, armed 15.8807, band **±0.9300**; limb C `HR` 10.4100, gas anchor
2.2494, `fuel₂₀₂₃` **2.6012**, armed 35.1989, band **±2.5062**. Limb A's
instrument is ERCOT-136 `bot_p50`; limb C's is ERCOT-138 above-min-load `p90`.
Primary window **T1 = h11–22 CST, all 365 delivery days**; full-day reported as
**T2**, non-gating. Limb C's gas basis is re-established by the ercot-169
footing gate (a no-LP keeper reconstruction that must reproduce ERCOT-138 §J's
committed 2024/2025 `fuel_capwtd` within ±0.02 $/MMBtu); a footing failure is a
`NOT-IDENTIFIABLE` return exactly as ercot-169 specified.

### 1a. The sub-population — defined as a RULE, applied identically to every year

ERCOT-169 located the shortfall precisely: **Martin Lake units 1–3**
(`MLSES_UNIT1/2/3`, ~2.3 GW) carry `curve_share` **0.757 / 0.761 / 0.797** —
roughly a quarter of their online intervals submit no incremental curve — and it
is **seasonal** (monthly COAL `curve_share` 0.907 / 0.937 / 0.907 / 0.917 across
March–June 2023 against 0.995–1.000 in January and July–November).

* **S1 — RESOURCE-SCOPED (PRIMARY, the gated instrument).** Drop every COAL
  resource whose **own** delivery-2023 `curve_share` (on the T1 window, the
  ercot-123/144 filters unchanged) falls **below the 0.9876 floor**. The rule is
  stated at resource grain and is **not** a named exclusion list: whichever
  resources fail, fail. The instrument is then recomputed on the surviving
  population with every other step identical.
* **S2 — MONTH-SCOPED (REPORTED SENSITIVITY, explicitly NOT GATING).** Keep the
  delivery-2023 months whose COAL `curve_share` clears the floor. Declared
  non-gating **here, before measuring**, with the reason: dropping March–June
  changes the seasonal mix, and ERCOT-168 already established that 2023 ERCOT
  coal conduct is seasonally structured (the Aug–Oct repricing), so a
  season-selected level would bias limb C — a *top-of-curve* form — toward the
  scarcity season. It is reported because a large S1/S2 disagreement is itself
  diagnostic.

### 1b. The two gates — applied in order, both must pass

* **G-LIC — licensing.** The S1-restricted delivery-2023 COAL population must
  reach `curve_share` **≥ 0.9876** on T1. **This is the SAME floor ERCOT-169
  failed on; it is not lowered, and it is not lowered against the constants
  either** (the ercot-169 §1b symmetry: a biased instrument manufactures a false
  refutation exactly as easily as a false confirmation). If the restricted
  population still does not clear it, S1 has not produced a licensed instrument.
* **G-NEUT — neutrality, the load-bearing gate.** The **identical rule** applied
  to the four committed identification subsets
  (`2024_ercot74_tail_days`, `2024_ercot75_control_days`,
  `2025_ercot75_control_days`, `2025_ercot86_tail_days`, via
  `ercot123.load_sced`) must **reproduce each limb's committed constant within
  that limb's own band** — pooled exactly as the frozen derives pool, i.e.
  |pooled_restricted − armed| ≤ band (A ±$0.9300, C ±$2.5062). Per-subset values
  and their dispersion are reported alongside; **the gate is on the pooled
  re-identification**.

  *Why this gate exists, stated before measuring:* a coverage restriction is only
  admissible if it fixes **coverage** and not **level**. The 2024/25 subsets are
  the frames on which these constants were actually identified and on which they
  ARE licensed, so "does the restriction move the identification where the
  instrument already works?" is the direct test of that. A restriction that
  shifts the licensed years' identification is a level-selecting filter, and the
  2023 reading under it is not comparable to the armed constant.

* **Reported, NOT gating**: the cap-weight share the restriction removes in each
  year, the number of resources dropped per year, and the S2 sensitivity. These
  are disclosure, not bars.

**A footing check inherited unchanged:** before any 2023 number is taken, the
harness must reproduce the committed subset-class reads it did at ercot-169
(ERCOT-136 `bot_p50` 16.86 / 16.37 / 15.00 / 15.00 COAL; ERCOT-138 `p90`
34.82 / 34.82 / 43.00 / 48.01 COAL). A mismatch is a construction error and
stops the session — reported, not patched.

## 2. The decision rule — PRE-REGISTERED, per limb, independent, branches exclusive

Evaluated in order; the first branch that fires is that limb's verdict.

1. **NOT-IDENTIFIABLE-2023 CONFIRMED** — if **G-LIC fails or G-NEUT fails**. The
   sub-population route did not produce a licensed, level-neutral 2023
   instrument. Both extrapolation notes **stand**, ERCOT-169 §6 **option 1 holds
   by default**, no arm is named, and this session **files and stops**. The
   unlicensed magnitudes may be restated as magnitudes — never as verdicts, never
   as a licence to arm anything (rule 13 `[R-MEASURED]`).
2. **CONFIRMED** — G-LIC ∧ G-NEUT pass and **|Δ| ≤ band**. The armed constant
   *is* the 2023 level once the coverage defect is removed. Consequence, fixed
   here: the declared-extrapolation note is **RETIRED BY VERIFICATION** in that
   constant's `constants.py` block (its comment is the identification record) and
   in the matrix cell — **constants comment + matrix only, no solve, no new
   mechanism, no new DOF, keeper UNCHANGED**.
3. **REFUTED** — G-LIC ∧ G-NEUT pass and **|Δ| > band**. The 2023 level is
   licensed, neutral and different. A **year-keyed 2023 block** (the ercot-168
   `coal_perplant_offer_yearly` pattern, applied to these two margin forms)
   becomes a **NAMED CANDIDATE ARM**. **This session SPECIFIES it with the §3
   kill gates and STOPS.** Building/arming is a separate step requiring an
   explicit in-session owner direction — this precommit does not authorize it,
   and the compute reality is disclosed up front: a full-span `2023 2024 2025`
   A/B is two sequential three-year solves at ~10 GB RSS each on this box
   (rule 12 — years sequential, no concurrency).

**No bar is moved by this document after measurement.** If a restriction that
*nearly* licenses (say `curve_share` 0.985) is measured, that is a **fail**, and
it is reported as a fail.

## 3. If the arm is later built — kill gates, fixed HERE

Reached only under branch 3 **and** an explicit owner direction. Any A/B is
full-span `--year 2023 2024 2025` in **one bundle** (rules 15/16), and **every
run is registered whatever the outcome** (rule 15). The gate set is ERCOT-168's,
the direct precedent — same lane, same corpus, same per-year-2023 scoping:

* **G-BIT** — the arm is **2023-scoped by construction** (a year-keyed 2023
  block), so all **2024 + 2025** hourly sidecars (`class_hourly`, `system`,
  `reserve_family`) must be **sha256 byte-identical** A→B. Any 2024/25 movement
  is a scoping bug, not a result.
* **G-SPUR** — spurious mid-band tail-hour count must not increase in any year.
* **G-SHED** — shed-hour count must not increase in any year.
* **G-C3c** — the three ledgered tail counts (61/181, 25/53, 3/31) must not
  degrade.
* **G-DOF** — **zero** new fitted scalars (rule 20 `[R-DOF]`): every number is a
  measured instrument read, and a residual that can only be closed by a tuned
  value is an open root-cause issue, not a parameter.
* **G-D2** — no class may cross its rule-20 `[R-FORCED-BUDGET]` cap as a result.
* **Rule 22 LOYO** reduces to the per-year gate table by construction (the 2023
  table consumes only 2023 rows; 2024/25 byte-identical) — exactly as ERCOT-168
  recorded it.

Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such; gates are not
renegotiated after the solve.

## 4. Scope fences and DO-NOT-REDO honoured

Rule 23 `[R-FROZEN-DERIVE]`: this re-identification's trigger is a **data**
change — the ercot-157 delivery-2023 corpus landing — the same cite ERCOT-168 and
ERCOT-169 used. **No residual is consulted in either direction**; no bar,
threshold or band responds to a fit.

Standing, carried unchanged: per-year **CT** re-identification stays **REFUSED**
(ERCOT-147, modal identity 11/160 — this lane is not extended to CTs); lignite
offer **SLOPE** (ERCOT-143 as adjudicated); `coal_min_load_floor` both grains;
lignite daily unit commitment; coal seasonal **LEVEL** split; `coal_offer_level_
rebasis` `R`; `tranche_startup_amortization` `G`; ERCOT-168 **OPTION B**
(spread-regime-conditional top) stays **DEFERRED**; the "~8 GW cheap CC offline
block" **DOES NOT EXIST** (ERCOT-163); `energy_online_capability_cap` `R`
(ERCOT-159); `ercot_storage_rt_offer_surface` `R` (ERCOT-162); the ercot-167
SOC-reserve re-gate still waits on the H4-item-4 2024 maintenance-season
availability defect; the West/Panhandle topology split is **CLOSED**
(`docs/DIAGNOSIS-ercot-trough-price-formation-2026-07.md` §§7–10). **ERCOT-170's
item-11 result stands**: the CC headroom object is a capability object, its
per-unit crosswalk is `FILED-UNLICENSED`, and it is re-pointed to a data-intake
charter — untouched here.

**Governance.** Rule 22 `[R-HOLDOUT]`: delivery **2023 only** on the corpus side,
and the 2024/25 identification subsets are training-span probe days —
`load_corpus_year` refuses anything outside 2023–2025 by construction. ERCOT
holds no `complete` marker; no holdout year is read, solved or scored. Rule 25
`[R-ISO-SCOPE]`: ERCOT-scoped throughout. Rule 15: no solve ⇒ no bundle ⇒ no
dashboard registration. Rule 28(b)/(c): matrix §5.1 is stamped in this session
and any mechanism cell this session touches is re-cited, rejections included.

**Next shorthand: ercot-172.**

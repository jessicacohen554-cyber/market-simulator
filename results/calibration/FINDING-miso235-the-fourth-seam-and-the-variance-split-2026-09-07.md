# FINDING miso-235 — the keeper has FOUR priced seams, not three: the attribution instrument is repaired, handoff item 2's premise is REFUTED, and MISO's interchange deficit is 79–84 % MISSING NON-PRICE VARIATION — on the three seams that are NOT PJM

**Zero LP. No arm, no screen, no bundle, no registration, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22:
2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was solved, scored
or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration: `PREREG-miso235-manitoba-seam-and-the-sigma-question-2026-09-07.md`, pushed
at `7711b104` before any adjudicating quantity.** The supplementary measurement is governed by
`ADDENDUM-miso235-residual-character-2026-09-07.md`, pushed at `334ea981` **before the numbers it
governs**. Every decision rule applied below was fixed in one of those two documents; none was
written after seeing a number. This is the discipline miso-234 forfeited and it is the reason
this session is entitled to close a handoff item on its own numbers.

Probes: `scripts/probes/_miso235_seam_variance_decomposition_phase0.py` →
`_miso235_seam_variance_decomposition_phase0.json`;
`scripts/probes/_miso235_residual_character_addendum.py` →
`_miso235_residual_character_addendum.json`.

**Basis (PREREG §0b).** `P`, the correlation price, is the **Indiana-hub RT** series
(`_miso224_floor_anatomy_phase0.actual_zone_price`, `values="rt"` — the lane's scored basis).
Every **regressor** is the **Indiana-hub DA** series (the basis the seam ladders were Q-Q derived
against). They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's
measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything
here.

---

## 1. Provenance — the instrument reproduces miso-234 exactly before it repairs it

Run on one code path, the three-seam leg reproduces `_miso234_corr_overshoot_phase0.json` **to
the published digit** in every year: harness `corr(recon, committed)` **+0.9216 / +0.9432 /
+0.9673** against its +0.922 / +0.943 / +0.967; model PJM contribution **−0.3291 / −0.2922 /
−0.2907**, SPP **+0.0186 / +0.0132 / +0.0312**, South **+0.1036 / +0.1126 / +0.0803**; recon σ
**1,377.8 / 1,557.5 / 1,482.4 MW**. The measured side is byte-equal too (total corr **−0.0549 /
−0.0367 / −0.0203**), and so is the committed solve's own **−0.1095 / −0.1145 / −0.1128**. So
what follows is a repair of miso-234's instrument, measured against itself, not a different
instrument reaching a different answer.

## 2. Q1 — the four-seam reconstruction SUPERSEDES. Both pre-registered bars clear in all three years

**Established before the PREREG was written** (code and committed config, no adjudicating
quantity — PREREG §0a): the keeper's `run_config.json` carries **`miso_manitoba_seam: true`**;
`spec.get_interchange_spec` therefore **drops the MHEB firm block** (`miso_firm_imports` is gated
on `not miso_manitoba_seam`) and `build_interchange_fleet` appends **`MISO_MANITOBA_SEAM_SPEC`**
as a fourth priced neighbour; and miso-234's probe iterated `INTERFACE_NEIGHBORS["MISO"]`, which
carries only **PJM, SPP, South**.

| year | instrument | harness `corr(recon, committed)` | mean level error | recon σ (MW) | `corr(recon, P)` |
|---|---|---:|---:|---:|---:|
| 2023 | three-seam (miso-234) | +0.9216 | **607.9 MW** | 1,377.8 | −0.2069 |
| | **four-seam (the keeper's actual spec)** | **+0.9845** | **49.4 MW** | **1,349.7** | **−0.1015** |
| 2024 | three-seam | +0.9432 | 389.9 MW | 1,557.5 | −0.1664 |
| | **four-seam** | **+0.9745** | **41.6 MW** | **1,494.6** | **−0.0811** |
| 2025 | three-seam | +0.9673 | 112.6 MW | 1,482.4 | −0.1793 |
| | **four-seam** | **+0.9839** | **55.3 MW** | **1,431.4** | **−0.1139** |

**(I-1) corr rises: TRUE in all three years. (I-2) level error not worse: TRUE in all three
years.** The pre-registered condition is met, so **the four-seam reconstruction supersedes the
three-seam one as this lane's attribution instrument**, and miso-234 §4's attribution is
superseded with it.

The repair is not marginal. The level error falls **608 → 49 MW**, and the repaired
reconstruction's σ lands on the **committed** solve's own interchange σ to **0.2 / 17.0 /
3.9 MW** (1,349.7 / 1,494.6 / 1,431.4 against a committed 1,349.9 / 1,477.6 / 1,427.5) — the
reconstruction is now a near-exact proxy for what the LP actually did.

## 3. Q2 — handoff item 2's premise is REFUTED in all three years. Manitoba is armed, live, and about TWICE as price-responsive as the real seam

The handoff's item 2 reads: *"the model's firm block (`miso_firm_imports`) contributes ZERO by
construction."* The pre-registered rule refutes that iff the resolved spec carries the seam **and**
`σ(x_MB) > 100 MW` in every year.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model Manitoba σ (MW) | **515.7** | **486.7** | **302.9** |
| model Manitoba mean (MW, import-positive) | **+657.3** | **+431.5** | **−57.3** |
| measured Manitoba σ (MW) | 819.1 | 832.6 | 655.4 |
| measured Manitoba mean (MW) | +615.2 | +344.0 | −113.3 |
| model contribution to `corr(imports, P)` | **+0.1098** | **+0.0923** | **+0.0718** |
| measured contribution | +0.0568 | +0.0527 | +0.0340 |
| model : measured contribution ratio | **+1.93×** | **+1.75×** | **+2.11×** |

**REFUTED, in every year and by a factor of 3–5 on the bar.** The seam is not inert and it is not
a firm block: it is a two-way priced seam that **tracks the measured MHEB level closely**
(+657 / +432 / −57 against +615 / +344 / −113) and **reproduces the 2025 drought sign flip to a
net export** — the exact behaviour `miso-74`'s design record said the import-only annual-flat firm
block could not represent. Its price response is not missing; it is roughly **twice** the measured
one, with the correct sign.

### 3a. An EMPIRICAL corroboration, independent of the code reading

§2's decision rests on measured reconstruction statistics; the identification of *which object*
they belong to rests on §0a's code reading. One arithmetic check closes the loop without either.

`MISO_MANITOBA_FIRM_IMPORT_MW_BY_YEAR` is **726 / 531 / 224 MW** — a flat block with **zero**
variance and, in 2025, the wrong sign for a seam the measured record shows net-exporting. Had the
firm block been what the keeper dispatched, adding it to the three-seam reconstruction would have
moved the level by exactly those constants and left σ untouched. What actually closes the
three-seam reconstruction's **607.9 / 389.9 / 112.6 MW** level error down to **49.4 / 41.6 /
55.3 MW** is a reconstructed **Manitoba seam** of mean **+657.3 / +431.5 / −57.3 MW** carrying
σ **515.7 / 486.7 / 302.9 MW**. The block cannot produce that fit in any year, and in 2025 it has
the opposite sign. The keeper dispatched the seam.

**Handoff item 2 is CLOSED as already-armed, on this session's own pre-registered rule.** The
question it should have asked survives and is handed forward in §6: not the seam's price response,
which exists and is if anything too strong, but its **residual**, which is 55 / 54 / 37 % of the
measured seam's.

**No cell verdict moves** (PREREG §2, and rule 28(b) in its evidence-appending form): this session
tested nothing — `miso_manitoba_seam` was armed by an earlier keeper. Evidence is appended to the
`seam_flow_envelopes` cell, which carries `miso_manitoba_seam` in its armed-family list.

## 4. Q3 — THE ADJUDICATION. 78.5 / 79.4 / 83.5 % of the deficit is the residual leg, and PJM carries none of it

Per seam and year, `x_s(t) = a + β_s·z_s(t) + r_s(t)` with the exact identity
`Var(x) = β²Var(z) + Var(r)`, run identically on the measured record and on the repaired
reconstruction, on the regressor each seam's bands actually clear against (PREREG §3, DA basis).
Bars fixed ex ante: **β ratio ≥ 1.5 ⇒ PRICE-RESPONSE OVERSHOOT**; **residual-σ ratio ≤ 0.5 ⇒
MISSING NON-PRICE VARIATION**.

| year | seam | β model | β meas | β ratio | σr model | σr meas | σr ratio | **verdict** |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2023 | **PJM** | 43.16 | 48.93 | **0.88** | 1,489.8 | 1,568.2 | **0.95** | **NEITHER** |
| | SPP | 7.38 | 1.07 | 6.91 | 226.9 | 576.8 | 0.39 | MISSING NON-PRICE |
| | South | 20.14 | −1.91 | 10.54 | 324.0 | 855.8 | 0.38 | MISSING NON-PRICE |
| | Manitoba | 22.58 | 20.10 | 1.12 | 426.9 | 777.6 | 0.55 | NEITHER |
| 2024 | **PJM** | 32.26 | 41.78 | **0.77** | 1,621.0 | 1,508.1 | **1.07** | **NEITHER** |
| | SPP | 5.18 | −0.57 | 9.02 | 247.1 | 687.2 | 0.36 | MISSING NON-PRICE |
| | South | 15.08 | 2.59 | 5.83 | 394.6 | 871.1 | 0.45 | MISSING NON-PRICE |
| | Manitoba | 9.88 | 7.83 | 1.26 | 445.3 | 817.9 | 0.54 | NEITHER |
| 2025 | **PJM** | 28.87 | 25.06 | **1.15** | 1,592.1 | 1,615.8 | **0.98** | **NEITHER** |
| | SPP | 4.88 | 1.06 | 4.61 | 205.8 | 614.7 | 0.34 | MISSING NON-PRICE |
| | South | 8.69 | −5.43 | 1.60 | 312.0 | 998.6 | 0.31 | MISSING NON-PRICE |
| | Manitoba | 7.13 | 4.98 | 1.43 | 238.8 | 642.3 | 0.37 | MISSING NON-PRICE |

β in MW per $/MWh, import-positive.

**System split, on the pre-registered identity:**

| year | price leg | residual leg | **residual share** | Σ per-seam σ gap | total σ gap |
|---|---:|---:|---:|---:|---:|
| 2023 | +359.4 MW | **−1,310.9 MW** | **78.5 %** | −1,130.0 MW | −755.3 MW |
| 2024 | +305.2 MW | **−1,176.4 MW** | **79.4 %** | −1,045.2 MW | −524.8 MW |
| 2025 | +301.5 MW | **−1,522.7 MW** | **83.5 %** | −1,353.4 MW | −1,005.4 MW |

*(Disclosed, not buried: the per-seam legs sum over seams while the total σ gap also carries
cross-seam covariance, so the two differ by construction. Both are reported and neither is
presented as the other.)*

### 4a. The handoff's item-1 hypothesis is CONFIRMED at the system level and REFUTED where it pointed

The handoff wrote: *"That is missing NON-PRICE variation (outages, schedules, neighbour state),
not an over-strong price response. Establish which, from the measured record, before proposing
anything."*

**Established: missing non-price variation, 78.5 / 79.4 / 83.5 % of the deficit — and PJM
contributes essentially none of it.**

Per-seam σ, model against measured:

| seam | 2023 | 2024 | 2025 | σ deficit (MW) |
|---|---|---|---|---|
| **PJM** | 1,528.6 / 1,615.4 | 1,652.2 / 1,563.9 | 1,633.9 / 1,647.0 | **−86.8 / +88.3 / −13.1** |
| SPP | 279.5 / 577.3 | 276.6 / 687.3 | 250.3 / 615.4 | −297.8 / −410.7 / −365.1 |
| South | 414.2 / 856.2 | 495.7 / 872.6 | 385.9 / 1,008.6 | −442.0 / −376.9 / −622.7 |
| Manitoba | 515.7 / 819.1 | 486.7 / 832.6 | 302.9 / 655.4 | −303.4 / −345.9 / −352.5 |

**PJM's interchange variation is right-sized within 5 % in every year**, its price response is
right-sized (β ratio 0.88 / 0.77 / **1.15** — *under*-responsive in two of three years), and its
residual σ is right-sized (0.95 / 1.07 / 0.98). **100 % of MISO's interchange variance deficit
sits on the three seams that are not PJM.** The 4–9× headline is a statement about a
*contribution to a correlation*, not about the seam's response, and §5 separates the two.

### 4b. The addendum's qualification does NOT fire — PJM's NEITHER stands unqualified

`ADDENDUM-miso235-residual-character-2026-09-07.md` named the OLS's blind spot in advance (the
model clears on its own solved bus price, so model-price-driven variation lands in the residual)
and fixed a three-part qualification. **It fires for no seam in any year**
(`qualified_seams_all_years: []`), because the second leg fails decisively: `R²(model flow | the
model's OWN clearing spread)` is only **0.4946 / 0.2726 / 0.5302** for PJM against a 0.90 bar. The
model's PJM flow is *not* a pure function of its own spread either.

What the addendum does establish, reported and not gated:

| year | `corr(r_model, P)` PJM | `corr(r_measured, P)` PJM | ratio | `R²` meas flow on meas spread |
|---|---:|---:|---:|---:|
| 2023 | −0.3243 | −0.1260 | 2.57× | 0.0577 |
| 2024 | −0.3143 | −0.1234 | 2.55× | 0.0701 |
| 2025 | −0.2858 | −0.0621 | 4.60× | 0.0375 |

**The model's PJM residual is 2.5–4.6× more price-aligned than the measured seam's residual, at
the same residual magnitude.** So the PJM defect is not *how much* the seam varies and not *how
hard* it responds to the spread — it is **which hours** its non-spread variation lands in. That is
a different object from the one item 1 named, and §6 hands it forward as such.

The measured seams' own `R²` on their measured spread is the context that makes this legible:
PJM 0.0577 / 0.0701 / 0.0375, SPP **0.0017 / 0.0004 / 0.0025**, South **0.0008 / 0.0035 /
0.0198**, Manitoba 0.0988 / 0.0350 / 0.0394. **The real seams are almost entirely
non-price-driven** — the model gives three of them a price response (β 4.9–20.1) that the measured
record does not have (β −5.4 to +2.6 for SPP and South), and the model's only non-spread input is
the deterministic measured `(month × hod)` deliverability envelope.

## 5. Q4 — the re-based ratios, REPORTED and NOT GATED. The model reaches a near-right total by CANCELLATION

| year | | PJM | SPP | South | Manitoba | **model sum** | **measured** |
|---|---|---:|---:|---:|---:|---:|---:|
| 2023 | four-seam model contribution | −0.3359 | +0.0189 | +0.1058 | +0.1098 | **−0.1014** | −0.0549 |
| | measured contribution | −0.0778 | −0.0291 | −0.0048 | +0.0568 | | |
| | **model : measured ratio** | **+4.32×** | −0.65× | −22.04× | +1.93× | **1.85×** | |
| 2024 | model | −0.3045 | +0.0138 | +0.1174 | +0.0923 | **−0.0810** | −0.0368 |
| | measured | −0.0573 | −0.0372 | +0.0050 | +0.0527 | | |
| | **ratio** | **+5.31×** | −0.37× | +23.48× | +1.75× | **2.20×** | |
| 2025 | model | −0.3011 | +0.0323 | +0.0831 | +0.0718 | **−0.1139** | −0.0203 |
| | measured | −0.0326 | +0.0188 | −0.0405 | +0.0340 | | |
| | **ratio** | **+9.24×** | +1.72× | −2.05× | +2.11× | **5.61×** | |

Two things to carry, and they point opposite ways:

1. **miso-234's PJM headline SURVIVES the repair.** 4.23 / 5.10 / 8.92× becomes **4.32 / 5.31 /
   9.24×** — the missing seam moved the denominator, not the story. That number is **not**
   withdrawn and a successor should not treat it as an artifact.
2. **But the SYSTEM overshoot is roughly half what the old instrument said.** On the committed
   solve the ratio is **1.99× / 3.12× / 5.56×** (−0.1095 / −0.1145 / −0.1128 against −0.0549 /
   −0.0367 / −0.0203), and the repaired reconstruction agrees (1.85 / 2.20 / 5.61×); miso-234's
   three-seam reconstruction read −0.2069 / −0.1664 / −0.1793, i.e. it **doubled the very
   correlation it was attributing**. Any successor sizing this residual should target the
   committed 2.0–5.6×, never the reconstruction's 4–9× per-seam ratio.

**And the mechanism by which the model gets close is cancellation, not agreement.** PJM is 4–9×
too negative; South is wrong-signed and 2–23× too positive; Manitoba is ~2× too positive. They net
to something within a factor of two of measured in 2023. **This is the right total for the wrong
reasons**, and rule 1 `[R-STRUCT]` says so plainly: a residual that closes by cancelling errors is
an open structural item, not a calibrated one.

## 6. What is handed forward — NAMED, and NOT CHARTERED

No lever is proposed and nothing here licenses one.

1. **THE SUCCESSOR'S OBJECT IS THE THREE NON-PJM SEAMS' MISSING IDIOSYNCRATIC VARIATION** — SPP,
   South and Manitoba at 43–63 % of the measured σ, carrying 100 % of the system deficit, against
   measured seams whose own price `R²` is 0.0004–0.0988. Its admissible form under rule 13
   `[R-MEASURED]` is a **measured non-price input with a forward analogue** — a scheduled-interchange
   series, tie or neighbour outage windows, neighbour state — never a noise term, never a variance
   inflator, and never anything tuned to this σ. **Whether such a series exists for MISO's DIBAs
   is a data question this session did not answer**, and it is the first thing a successor should
   settle at zero LP.
2. **PJM's object is its residual's PRICE ALIGNMENT, not its magnitude** (§4b: 2.5–4.6× the
   measured alignment at 0.95–1.07× the magnitude). A hypothesis is **named and explicitly NOT
   MEASURED here**: the reconstruction has exactly two inputs — the ladder-vs-spread merit test and
   the measured `(month × hod)` deliverability envelope — and the envelope is a deterministic
   diurnal template, hence price-aligned by construction, where the real seam's non-spread
   variation is idiosyncratic. Testing that is a zero-LP successor measurement, not a lever.
3. **`miso_seam_neighbour_hourly_ladder` remains K and is untouched.** Nothing here licenses a
   re-derive or a damping factor on the PJM `delta_k` ladder, which is derived, frozen and pinned
   to its derive by test (rule 23 `[R-FROZEN-DERIVE]`); a factor swept against this residual is the
   rule 1 `[R-STRUCT]` fitted mechanism the handoff forbids, whatever §5 says.
4. **The South seam stays where miso-234 routed it** — upstream, in the South-gas price-out lane
   (`gas_marginal_commodity_pricing` **O** / `gas_variable_transport` **O**, owner-court). §4's
   South rows (β_measured **negative** in 2023 and 2025, price `R²` 0.0008–0.0198) **corroborate**
   the standing refusals `miso_south_firm_export_block` **G** (miso-182/185) and
   `miso_south_export_ladder_rt_tail` **R** (miso-184) on an independent instrument; neither is
   re-tested (rule 28(a)).
5. **The CC_REGULAR 2024→2025 shape emergence** (handoff item 3) is untouched and stays where
   miso-234 filed it.
6. **C3c** is untouched and stays the designated frontier (2026-07-20).

## 7. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number below the reconstruction's own harness is a solve result.
2. **The reconstruction is not the solve.** Harness `corr(recon, committed)` is +0.9845 / +0.9745 /
   +0.9839 — close, and closer than miso-234's, but not 1. Every model-side number is a
   reconstruction number and is labelled as one.
3. **The 2024 reconstruction is the loosest year** (`corr(recon, P)` −0.0811 against a committed
   −0.1145) and its attribution should be read with that in mind. 2023 and 2025 agree with the
   committed solve to 0.008 and 0.001.
4. **miso-234's PJM 4–9× is not withdrawn** (§5.1); what is superseded is its *instrument*, its
   system-level correlation, and its item-2 premise.
5. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
6. **MISO has no failing gate**, and nothing here proposes trading a passing one.

## 8. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; nothing was proposed, and §5's
cancellation reading is applied against the model, not in its favour. Rule 12 `[R-PARALLEL]`: no
LP was solved; nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement only; no measured outcome
enters any solve, and §6.1 states the admissibility test the successor's input must meet. Rule 14
`[R-ACCURATE]`: no input changed. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered
or pruned; MISO keeps exactly one registered run and the keeper's `hourly/` sidecars stay
committed. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training year was
solved, scored or registered. Rule 23 `[R-FROZEN-DERIVE]`: no derive was re-run; §6.3 restates the
freeze. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard, section
and lane only. Rule 27 `[R-PUSH]`: every pushed blob verified against local. Rule 28(a): the four
standing adjudications this touches (`miso_south_firm_export_block` **G**,
`miso_south_export_ladder_rt_tail` **R**, `internal_congestion_split` **G**,
`vre_reference_rate_curtailment_grossup` **K**) are corroborated, never re-tested; the queue item
taken is the handoff's item 1 with its item 2, which are one measurement. Rule 28(b): no verdict
moves; evidence appended in-session. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0
first, and it closed a queue item and re-routed another **before any solve was spent**, which is
the outcome the clause exists to produce.

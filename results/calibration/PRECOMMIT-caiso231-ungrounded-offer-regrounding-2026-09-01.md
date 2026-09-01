# PRECOMMIT — caiso-231: re-ground CAISO's THREE UN-GROUNDED gas offer classes (CC_CHP / CT_CHP / ST_GAS) on the measured buckets they are measured inside. A RULE 25 [R-ISO-SCOPE] + RULE 14 [R-ACCURATE] STRUCTURAL-INTEGRITY REPAIR THAT IS PRE-REGISTERED TO MAKE C3a WORSE

**Pushed BEFORE either arm is solved.** Session caiso-231 · 2026-09-01 ·
incumbent keeper `2026-08-26-caiso-220-c1-crosswalk` (NOT-YET; C3a the sole
load-bearing FAIL at +4.0 PASS / +12.5 / +15.5; C1 12/12 free 8/8;
C2/C3b/C4/C6/C8 PASS; C3c the single ledgered caveat, budget 1 of 1).

## §1 — the defect

`src/market_sim/pipeline/backcast_config.py::_CAISO_OFFER_CURVE` states, in
its own comment:

> *"CC_CHP / CT_CHP / ST_GAS below are PINNED to the values CAISO previously
> inherited from the generic ERCOT-lineage `else` branch. **They are NOT
> CAISO-grounded** — they are preserved verbatim ONLY so the neutral generic
> fallback (rule #24, added by the 2026-07 cross-ISO-bands scrub) does not
> silently change the caiso-51 keeper, which this scrub does not re-solve …
> Re-grounding these on CAISO's own DMM/CAMPD data is a separate, out-of-scope
> CAISO item."*

Three ERCOT-fitted band blocks therefore sit on CAISO's binding path. Rule 25
`[R-ISO-SCOPE]`: *"Tuned curves never cross ISO boundaries. A multiplier
fitted on one ISO's residual is that ISO's."* caiso-230 §4/§7 sized what they
price: on the 2025 annual load-weighted above-floor term, `CC_CHP:econ`
**+1.23**, `CT_CHP:committed` **+0.36** and `CC_CHP:committed` **+0.27**
$/MWh. This is not a cosmetic defect on a dormant path.

## §2 — the measured repair, and why it is admissible (rule 13 / rule 14)

`scripts/data/derive_caiso_offer_surface.py` derives CAISO's measured DAM band
multipliers from the 90-day-lag masked OASIS Public Bid Data. The bids carry
no fuel or physics columns, so resources are classified by the **Theil–Sen
slope of their body bid price on the measured CA-composite citygate** — a
fuel-price time-series identification of each resource's marginal heat rate —
and split at 8.4 MMBtu/MWh into a CC bucket and a CT bucket. The script
**discloses its own bucket membership**:

> *"Known contamination, disclosed not hidden: the three OTC/RMR steamers
> (ST_GAS: Alamitos / Huntington Beach / Ormond Beach, 2.9 GW, HR ~11.85) and
> priced CT_CHP curves land in the CT bucket when they pass the bidder gates;
> CC_CHP (HR 6.90) lands in the CC bucket. Both are near-SRMC bidders of the
> same fuel, statistics are cap-weighted MEDIANS … The masked ids cannot be
> plant-mapped, so the derive is per-CLASS only."*

So the measured CC bucket **is** the pooled CC_REGULAR+CC_CHP conduct and the
measured CT bucket **is** the pooled CT_PEAKER+CT_CHP+ST_GAS conduct. The
repair re-grounds each un-grounded class on the bucket it is measured inside:

| model class | measured source bucket | why |
|---|---|---|
| CC_CHP | measured `CC_REGULAR` bucket | derive: *"CC_CHP (HR 6.90) lands in the CC bucket"* |
| CT_CHP | measured `CT_PEAKER` bucket | derive: *"priced CT_CHP curves land in the CT bucket"* |
| ST_GAS | measured `CT_PEAKER` bucket | derive: the three OTC/RMR steamers land in the CT bucket |

**Rule 13 `[R-MEASURED]` admissibility.** The multipliers are measured OFFER
conduct, not a measured outcome: they are produced by a frozen derive script
from a public bid corpus, they regenerate for a forward year from that same
corpus, and they respond to changed conditions (a fleet that bids differently
measures differently). They are pooled 2023–2025, never per-year — caiso-229
§10 item 2 and caiso-230 DO-NOT-REDO item 3 both record that per-year measured
multipliers have no forward analogue and are inadmissible, and this precommit
does not use them. No value here is fitted to, selected against, or informed by
any residual. **Zero free parameters are added; nine fitted scalars are
retired.**

**Rule 19 `[R-ONE-MECH]`.** One mechanism, one phenomenon: the class's offer
LEVEL. It arms **exactly the three bands the incumbent
`caiso_offer_surface_measured` arms** (`econ_low`, `econ_high`, `peak`) and no
others. The measured `committed` band stays **unarmed for every CAISO gas
class** — the Lever-A inversion lesson (min-load self-commitment conduct
belongs to unit commitment, not the P1 offer) applied uniformly rather than
selectively. It is gated to require the incumbent flag, so an incoherent
half-measured surface cannot be built.

**Rule 25 semantics — multipliers transfer as multipliers.** Each band is
applied against each plant's OWN `Plant_Avg_HR`, which is the incumbent's
semantics for CC_REGULAR / CT_PEAKER and is what the derive's slope-based
classification identifies (a resource joins a bucket BECAUSE its measured
marginal heat rate matches that bucket). **The rejected alternative is named
here so it is not re-proposed:** rescaling each multiplier by
`base_HR_bucket / base_HR_class` to reproduce the bucket's measured $/MWh band
price. That is a new modelling choice rather than a transfer, and it moves
C3a further the wrong way (CC_CHP `econ_low` would land at 1.150, +19.7 %
against the armed 0.960, rather than 1.066 / +11.0 %). It is not armed.

## §3 — the exact, verified delta (measured pre-solve, no LP)

Verified at HEAD on the built config: **9 bands change, all three `committed`
bands are untouched, and no non-target class moves.**

| class | band | armed | measured | move |
|---|---|--:|--:|--:|
| CC_CHP | econ_low | 0.960 | 1.066 | **+11.0 %** |
| CC_CHP | econ_high | 1.120 | 1.072 | −4.3 % |
| CC_CHP | peak | 2.250 | 1.386 | −38.4 % |
| CT_CHP | econ_low | 1.200 | 1.145 | −4.6 % |
| CT_CHP | econ_high | 1.200 | 1.166 | −2.8 % |
| CT_CHP | peak | 1.400 | 1.166 | −16.7 % |
| ST_GAS | econ_low | 1.050 | 1.145 | +9.0 % |
| ST_GAS | econ_high | 1.400 | 1.166 | −16.7 % |
| ST_GAS | peak | 4.200 | 1.166 | −72.2 % |

## §4 — THE DIRECTION IS PRE-REGISTERED, AND IT IS ADVERSE

caiso-230 §H measured the first-order effect on the annual load-weighted price
by weighting each band's move by the zone-hours in which that class-band is the
marginal rung. Restricted to the nine bands this precommit arms:

| year | pre-registered C3a move | C3a now | C3a predicted | required move |
|---|--:|--:|--:|--:|
| 2023 | **+0.235** | +3.96 % (PASS) | ≈ +4.4 % (PASS) | 0.00 |
| 2024 | **+0.344** | +12.45 % (FAIL) | ≈ +13.4 % (FAIL) | −0.848 |
| 2025 | **+0.421** | +15.50 % (FAIL) | ≈ +16.7 % (FAIL) | −1.893 |

**This repair makes the sole failing gate worse in both failing years.** It is
filed and solved under rule 14 `[R-ACCURATE]` — *"never revert to an estimate
just because it fits the backcast better … Treat the worse fit as a discovered
bug: keep the accurate input, find and fix the real root cause"* — and rule 1
`[R-STRUCT]` — *"a real market behaviour stays in even if it makes the fit
worse"* — on the owner's standing 2026-09-01 instruction that a run whose
structural integrity improves while gates regress may still be a keeper.
**caiso-230 DO-NOT-REDO item 3 stands unamended: this is never to be proposed
as a C3a lever, and nothing here claims it is one.**

Note the arithmetic that makes the ask tractable: because C3a **already fails**
in 2024 and 2025, and 2023 carries **$7.56 of downward room** against a
predicted +$0.24, the repair is pre-registered to flip **no C3a year** from
PASS to FAIL.

## §5 — ARMS

Two arms, solved from the SAME committed control recipe via `--replay-bundle`
so the delta is exactly one flag (the nyiso-140 / caiso-224 pattern), both over
**2023 2024 2025 in one invocation, years sequential** (rules 12/16), launched
concurrently as two separate invocations (rule 12's cap of 2 for per-plant
multi-zone LPs):

* **A0 control** — `--replay-bundle results/calibration/caiso220_c1_crosswalk`
  at HEAD. Required because HEAD has advanced since the keeper was solved; the
  control isolates the mechanism's delta from HEAD drift.
* **B1 treatment** — the same, plus
  `--caiso-offer-surface-measured-ungrounded`.

## §6 — PRE-REGISTERED GATES (all scored on the committed artifacts of both arms)

**G-STRUCT — the reason to promote (hard, must PASS or there is no case).**
The solved `run_config.json` of B1 must carry measured values in all nine
bands, all three `committed` bands unchanged, and no non-target class changed;
and the DOF ledger's `offer_curve_by_group` residual scalar count must FALL by
**9** (112 → 103).

**G-LIVE — the mechanism must actually move the solve (hard).** Max |Δ| in any
class-hour MW between A0 and B1 must be > 0 (the nyiso-89 §4a liveness check).
An inert arm is rejected as inert, not promoted.

**G-CTRL — the control must reproduce the incumbent (hard).** A0's C3a must sit
within ±0.3 pp of the keeper's +4.0 / +12.5 / +15.5 in every year. A wider
drift means HEAD moved the recipe and the A/B is not clean; the session stops
and reports rather than promoting.

**G-C3a — disclosed regression, bounded (hard).** For each year, B1 − A0 on the
annual load-weighted price must lie in **[0, 3 × the §4 prediction]**
(2023 ≤ +0.71, 2024 ≤ +1.03, 2025 ≤ +1.26). A move outside that band means the
first-order arithmetic did not describe the object, and the arm is rejected
pending re-derivation. **C3a-2023 must remain PASS.**

**G-C1 (hard).** Free-class C1 must stay **8/8**; no free class may flip
PASS→FAIL. The pinned CC_CHP / ST_CHP cells are reported at full magnitude but
are not gated (they are the classes the rubric already excludes from the free
count).

**G-C3b (hard, the live tripwire).** Price duration/shape NRMSE must stay
≤ 0.20 in all three years. The incumbent is 0.100 / 0.177 / **0.180** — 2025's
margin is only **0.020**, and this is the gate most likely to catch the repair.

**G-C2 / G-C4 / G-C8 (hard).** No PASS→FAIL flip on system volume, fleet
hourly dispatch correlation, or forced-energy share.

**G-CAVEAT (hard).** The ledgered-caveat budget must stay **1 of 1** and no
protective caveat may appear.

**G-C6.** A fresh attestation is generated at promotion, with the DOF ledger
re-stated to show the nine retired scalars.

## §7 — FALSIFIERS (pre-registered kill conditions; any one REJECTS the arm)

* **F1** — any load-bearing criterion (C1 free, C2, C3b) flips PASS→FAIL.
* **F2** — C3a-2023 flips PASS→FAIL.
* **F3** — the arm is inert (G-LIVE fails): matrix cell → `I`, not promoted.
* **F4** — the C3a regression falls outside G-C3a's [0, 3×] band in any year.
* **F5** — C8 forced-energy share flips, or a protective caveat appears.
* **F6** — G-CTRL fails: the control does not reproduce the incumbent, so no
  comparison is licensed.

**Pre-registered outcome if any falsifier fires:** the arm is registered on the
dashboard as a REJECTED probe (rule 15 applies to rejected runs too), the
matrix cell is stamped with the refutation, and the keeper is UNCHANGED.

## §8 — LEAVE-ONE-YEAR-OUT (rule 22)

The mechanism has **zero free parameters** — every armed value is a pooled
2023–2025 measured median produced by a frozen derive script, and nothing is
identified against any year's residual. A leave-one-year-out **re-fit** is
therefore vacuous by construction: dropping a year changes no armed value.
What LOYO exists to catch — in-sample gain bought with out-of-sample
degradation — is instead reported as the **per-year gate table across all three
years** in §6, which is scored in full and which no year can be traded against,
since the same nine numbers are armed in every year. This is stated here, ex
ante, so the absence of a LOYO re-fit is a disclosed property of a zero-DOF
measured input and not an omission.

## §9 — HOLDOUT AND SCOPE

Solve span **2023 2024 2025** only. CAISO holds **no** `complete` and **no**
`final` marker; the holdout spend freeze is **ACTIVE**. No out-of-training year
is solved, scored or registered. `calibration-complete.json`,
`holdout-freeze.json`, every other ISO's shard and every other ISO's matrix
column are untouched.

## §10 — MATRIX DUTIES (rule 26)

A new `ScenarioConfig` field ships in this PR, so (c) a base row is added to
`docs/codebase-site/data/mechanism-matrix.js` with a cell line in **every** ISO
shard, and (b) the tested verdict plus evidence lands in the CAISO shard in
this same session — promoted or rejected.

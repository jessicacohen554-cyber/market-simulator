# RESULT (pjm-h9) — route (b) is **B-PARTIAL**: the gas-steam admixture can account for
# **a third to a half** of pjm-h8's committed-band correction, and for **none of it fully**

**Session** `pjm-h9` · **ISO** PJM · **Date** 2026-09-16 · **Base** `origin/main` @ `af764ec8`
**ZERO LP. NO SHARD.** Rule 32 `[R-SHARD]` (a) — the parent ran no LP and none was needed.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**
Pre-registration: `docs/PRECOMMIT-pjm-h9-coal-only-comparator-2026-09-16.md` (committed at
`eda1169d` **before** the corpus finished downloading; the three probes at `b73f846f`, before
any decisive number existed).

> ### ⚠ EVERY NUMBER BELOW IS **PROVISIONAL**. The pre-registered **G-REPRO hard stop FAILED.**
> My re-derivation does not byte-reproduce the frozen surface (129 of 432 cells). §3 measures
> exactly what drifted and shows the verdict is **invariant** to it — but the certification the
> PRECOMMIT required was not obtained, and nothing here is a certified number.

---

## 1. RESULT

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **φ(ŵ) — COAL `committed`** — worst-case share of h8's correction the admixture can explain | **0.367** | **0.560** | **0.546** |
| φ(ŵ) — COAL `mustrun` | 0.144 | 0.193 | 0.157 |
| **w½** — admixture needed to explain **half** | 0.26 | 0.17 | 0.17 |
| **w\*** — admixture needed to explain **all** | **0.52** | **0.35** | **0.39** |
| ŵ — the measured admixture | 0.189 | 0.189 | 0.189 |

**Pre-registered verdict, read on 2023 COAL `committed` as fixed in PRECOMMIT §4:
φ = 0.367 ⇒ B-PARTIAL** (the bands were < 0.25 ⇒ B-NO, > 0.75 ⇒ B-YES).

Two things follow, and they point opposite ways — which is what B-PARTIAL means:

* **The comparator is NOT exonerated.** At PJM's own measured gas-steam share of the
  `LONG_RUN` segment, the admixture can account for **37–56 %** of the correction h8 installed
  on coal's `committed` rung. h8's arm was, to that extent, an over-correction.
* **The comparator cannot rescue h8's arm either.** To explain the correction **in full** the
  admixture would have to be **35–52 %** of `LONG_RUN` capacity against a measured **18.9 %** —
  **1.9× to 2.8× too large in every year.** So **at least ~44 % of h8's committed-band
  correction survives any admixture story**, and the 12.70 TWh coal shortfall it produced is
  not an artifact of the blend.

## 2. HOW THE BOUND WORKS — and why nothing is classified

**The method the handoff specified is impossible, and that is the session's first result.**
PJM's `energy_market_offers` feed publishes a **MASKED `unit_code`** and **no fuel column**:
`AAAADQYJAg8BLjUxMzM5MDA3` → `\x00\x00\x00\r\x06\t\x02\x0f\x01` + `.51339007`, an opaque PJM
internal id with a plant-grouping structure and no crosswalk to any fuel registry this repo
carries. That is why the whole derive family states its rule as *"Segments are selected by unit
PHYSICS, never fuel labels"* (`derive_pjm_offer_surface.py` L15). **A coal-only ladder BY LABEL
is not obtainable from this source at any data cost** — re-fetching the corpus (36 month files,
**402 MB**, an order of magnitude under the README's "1–2 GB") does not change it.

What replaces it classifies nothing. The ladder is a **capacity-weighted median**, so writing
the blended CDF as a mixture with gas-steam weight `w` and using only route (b)'s own premise
that the admixture is **one-sided** (gas-steam bids dearer):

```
F_blend = (1-w)·F_coal + w·F_gas      ⇒      Q_blend(0.5(1-w)) ≤ median_coal ≤ Q_blend(0.5(1+w))
```

**exactly, for any gas-steam distribution.** `Q_blend` comes from the same histogram the frozen
derive already builds — the only change is emitting the quantile function instead of `p = 0.5`.
It is applied through the model's **own** targeting code (`_pjm_midcurve_context` /
`_pjm_midcurve_row_target`, with only the `LONG_RUN` table swapped), so every column is
byte-for-byte what the armed mechanism would apply. The bound composes to the row level because
`_pjm_midcurve_row_target` is a **positive**-weighted average of ladder cells and `w` is one
fleet-level share common to every cell.

**ŵ = 0.1893** is independent of all of this: the model's own PJM fleet maps **11,525.5 MW of
ST_GAS** and **49,371.7 MW of COAL** onto `LONG_RUN` (committed h8 ladder).

## 3. G-REPRO FAILED — what drifted, measured rather than asserted

| | |
|---|---|
| cells checked | 432 |
| **mismatches** | **129 (29.9 %)** — 2023: 52, 2024: 77, **2025: 0** |
| deviation | median **0.10** implied-HR (≈0.32 $/MWh), p90 0.30, **max 0.65**; 63/129 within ONE 0.05 grid cell |
| sign | 73 high / 56 low — **balanced, not a bias** |
| **segment membership** | **EXACT** — CT_FAST 1064, CC_LIKE 883, LONG_RUN 216, identical to the frozen provenance |
| **capacity weight per (segment, year, bin)** | **max \|rel diff\| = 1.6 × 10⁻³** against the committed summary CSV |

So the population, the physics segmentation and the net-load bin assignment all reproduce — to
**0.16 %** on the one year the committed CSV covers. What moved is a ~0.1 % slice of unit-hours
(PJM restates the feed), enough to nudge some capacity-weighted medians by a grid cell or two.
**2025 reproduces exactly; 2023 and 2024 do not.**

**The verdict is INVARIANT to it, and that is measured, not argued.** Running the bound with
the blend reference set to the **COMMITTED frozen ladder** instead of my re-derivation gives
**φ = 0.3673, w½ = 0.26, w\* = 0.52 — identical to four decimal places**
(`_pjm_h9_bound_applied_frozen.json` vs `_pjm_h9_bound_applied.json`). The bound is a
*difference of quantiles of one distribution*, so a common-mode reproduction error cancels.

**Nothing was adjusted to make them agree** (PRECOMMIT §5). The probe still exits non-zero, its
artifact is stamped `PROVISIONAL_g_repro_failed`, and reading it requires an explicit
`--allow-provisional` that is recorded in every output file.

## 4. M2 IS **VOID** BY ITS OWN PRE-REGISTERED CONDITION — and the failure is informative

M2 tried to split the masked fleet by measured fuel-cost passthrough (log-log elasticity of the
offer on the delivered-gas day price, calendar-month fixed effects; β≈1 gas, β≈0 coal).
**PRECOMMIT §6 required `CC_LIKE` ≥ 80 % gas-linked. It reads 49.1 %, so M2 IS DISCARDED** and
§1 rests on M1 alone, exactly as pre-registered.

Why it failed is worth recording: **R² ≈ 0.02–0.04 everywhere.** Within a calendar month,
PJM's submitted offers barely track the daily gas price **even for the CC fleet**, whose fuel
is not in doubt. The per-unit classifier therefore has no power.

**The bimodality control nevertheless PASSED, and it confirms the premise nobody disputed:**
`LONG_RUN`'s capacity-weighted β histogram is visibly bimodal — **59,061 MW at β ∈ [−0.125,
+0.125]** and a second broad mode of **19,756 MW at β ∈ [0.5, 1.0]** — while `CC_LIKE`'s mass
sits centred on 0.4–0.9. `LONG_RUN` really is a mixture. **No `w` is read off this**, because a
β≈0 spike also exists in `CC_LIKE` and the classifier is void.

## 5. THE OTHER READING — route (a) — IS NOW WELL-FOUNDED, at ZERO LP

Verified in the code rather than inferred: the LP is pure (**no MIP**), so it carries **no
minimum-run or minimum-down constraint at all**. Commitment rests entirely on `min_gen` floors
and the ISO-gated P1-native bridges in `pipeline/commitment.py`:

```
caiso_ra_mustoffer → CAISO     ercot_gas_commitment_bridge, ercot_ruc_commitment_floor → ERCOT
nyiso_gas_commitment_bridge → NYISO     spp_gas_commitment_bridge → SPP
miso_coal_night_floor → MISO
```

**FIVE ISOs carry one. PJM carries none** — its only entry in that module is
`energy_reserve_coopt`, which is not a commitment mechanism. **Nothing in the model bounds how
fast PJM coal starts and stops.** (Rule 25 `[R-ISO-SCOPE]`: MISO's coal floor is named to show
a **coal** commitment mechanism is an established object here, **not** as a transfer. pjm-142's
killed overnight **gas** bridge adjudicates nothing about a coal one.)

Measured in pjm-h8's arm, **per PLANT** (sum of every band = 0 **is** decommitment, not a band
backing down to min load), from its committed `dispatch/2023_P1.parquet`:

| | |
|---|---:|
| coal plants dispatching | 45 |
| **cycling / never off** | **38 / 7** |
| **starts in one year** | **2,151** |
| **on-blocks shorter than the segment's own 16 h `min_runtime`** | **806** |
| off-blocks shorter than 8 h | 1,335 |

For contrast, in the **keeper's** committed sidecar the COAL_BIT `committed` band aggregate has
**0 hours off and 0 transitions** across 8,760 h; in the arm it is off **638 h** across **104**
on-blocks, **42** of them under 16 h.

**STATED LIMIT, not buried:** there is **no per-plant control**. The keeper does not commit
`dispatch/`, so the keeper's own per-plant cycling is unmeasured and would cost a replay. The
one-sided reading stands on its own: whatever the keeper does, a fleet whose published physics
is `min_runtime > 16 h` cannot produce 806 sub-16 h runs, and the model has no constraint that
would stop it.

## 6. WHAT THIS DOES **NOT** ADJUDICATE

* **It proposes nothing and changes nothing.** Zero `ScenarioConfig` fields, zero free
  parameters, nothing swept, no derive output rewritten (rules 21/23/24).
* **It does not license reverting anything** (rule 14 `[R-ACCURATE]`).
* **It does not re-open the offer surface.** §1 is a statement about an *input's accuracy*, not
  a proposed value. Any coal-only comparator is a **new** object needing its own charter, its
  own footprint-named screen year and an owner ruling — and on this evidence it would have to
  be built without fuel labels, which is the hard part §2 names.
* **The B-PARTIAL split is a WORST CASE, not an estimate.** φ is the *most* the admixture could
  explain; the true coal-only ladder lies anywhere in `[lo, hi]`, and `hi` sits far above the
  blend. A reader who treats φ as "the admixture explains 37 %" has over-read it.
* **It says nothing about `gas_mid`** (still 3.40 live, rule-23 wart undiminished, standalone
  4.58 repair still unchartered) or about CC_LIKE min-load.
* **The 2020–2022 half of PJM's registered span is untouched** — the measured surface covers
  2023–2025 only.

## 7. TWO REPO FINDINGS

* **`data/raw/_validation-source/pjm_offer_midcurve_summary.csv` is a PARTIAL artifact.** The
  derive writes one row per (segment, year, bin) for every year it runs; the committed file
  carries **12 rows, 2024 only**, i.e. a stale overwrite from a `--years 2024` invocation. It
  is the only committed fingerprint of the surface's population and binning, so a future
  reproducibility check has two thirds of its evidence missing. Recorded, **not** regenerated —
  rule 23 `[R-FROZEN-DERIVE]` freezes the derive against anything but a source-data change, and
  this session has no such change to cite.
* **The frozen surface is no longer byte-reproducible from PJM's live feed** (§3). It is
  reproducible to 0.16 % in weight and ~0.1 implied-HR in value, which is fine for the use it
  is put to, but a future session should expect the drift rather than rediscover it.

## 8. RETRIEVABILITY & WHAT WAS SPENT

* **No LP, no shard, no container.** ~50 min of corpus fetch (36 files, 402 MB, gitignored
  under PJM's DataMiner2 redistribution restriction and **not committed**), ~3 min of probe.
* **Nothing deleted** (rule 31 `[R-RETAIN]`). pjm-h8's arm bundle was recovered at
  `b2b3d7d572ce56cd0fc25c4e08c8b46fce740be7` for §5, is gitignored, and is left in place.
  pjm-h7's bundle at `9be0e032e8f3832779b70472ae93813d63e2229a` is untouched.
* Committed artifacts: `results/calibration/_pjm_h9_{longrun_mixture_bound,bound_applied,
  bound_applied_frozen,fuel_elasticity,coal_cycling}.json` and the four probes.
* **The corpus is NOT recoverable from this repo** — re-fetch with
  `python scripts/data/fetch_pjm_energy_offers.py` (~50 min at 5-way concurrency; more than 5
  concurrent fetchers is **OOM-killed**, each peaks at ~2.4 GB against a 13.4 GiB cgroup).

## 9. THE OWNER QUESTIONS

1. **Does the coal-only comparator get a charter?** §1 says the admixture is worth **37–56 %**
   of h8's correction — real, and not enough to explain it. Building one means solving §2's
   masked-label problem, which M2 failed to do; a successor would need a different
   identification, not a re-run of mine.
2. **Does route (a) — a PJM coal commitment mechanism — get a charter?** §5 is the measured
   case: no min-run constraint anywhere in the LP, no PJM bridge where five other ISOs have
   one, and 2,151 coal starts a year in the only PJM run whose per-plant layer we can read.
3. **pjm-h7's and pjm-h8's promotions remain open and are carried forward unchanged.** Neither
   was touched by this session and nothing was deleted.
4. **Nothing here is promotable.** No bundle was solved, so there is no promotion question of
   this session's own — but §1's numbers are PROVISIONAL and should be quoted as such.

## 10. RULES

Rule 1 `[R-STRUCT]` (the decision rule was fixed before the corpus landed, contains no residual
and selected no parameter) · rule 13 `[R-MEASURED]` (the operand is PJM's own published offers)
· rule 14 `[R-ACCURATE]` (the whole question is an input's accuracy; nothing reverted either
way) · rule 19 `[R-ONE-MECH]` (§5 names the one seam a successor would occupy) · rule 21
`[R-DOF]` (zero free parameters, zero proposed values, nothing swept) · rule 23
`[R-FROZEN-DERIVE]` (the frozen surface was read and reproduced, never rewritten; §7's partial
CSV is recorded, not regenerated) · rule 24 `[R-REGISTRY]` (no new field) · rule 25
`[R-ISO-SCOPE]` (PJM's own offers and fleet; MISO's coal floor named, never transferred) ·
rule 28 `[R-MECH-MATRIX]` (b) (PJM's shard cell stamped this session) · rule 29 `[R-SCREEN]`
(clause 0 throughout; no arm, no screen, no LP) · rule 30(c) (no held-out year touches PJM's
determination) · rule 31 `[R-RETAIN]` (nothing deleted; h7's and h8's open promotions carried
forward) · rule 32 `[R-SHARD]` (a) (the parent ran no LP).

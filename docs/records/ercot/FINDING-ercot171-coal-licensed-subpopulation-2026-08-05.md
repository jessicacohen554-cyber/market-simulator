# FINDING — ercot-171: the licensed sub-population instrument, on the owner's adjudication of the ercot-169 §6 open decision. Limb A **CONFIRMED** (the coverage defect, not the level); limb C **NOT-IDENTIFIABLE-2023 CONFIRMED** (the same rule is a level-selecting filter on a top-decile statistic).

**Session ercot-171, 2026-08-05. NO LP, no solve, no mechanism armed, no
`ScenarioConfig` field, keeper UNCHANGED (`2026-08-05-run168b-year-curves`), both
matrix cells stay `K`, and BOTH CONSTANT VALUES ARE UNCHANGED (15.8807 /
35.1989 / 10.4100).** Charter: the **owner adjudication taken in-session
2026-08-05** on the ERCOT-169 §6 open decision — *option 2, "charter a licensed
sub-population instrument for the 2023 COAL rows."* Decision rule pre-registered,
committed and pushed **before** any derive ran:
`docs/PRECOMMIT-ercot171-coal-licensed-subpopulation-2026-08-05.md`. **No bar,
band, floor or window was moved after measurement.**

Probe: `scripts/probes/ercot171_coal_licensed_subpop_phase0.py` →
`results/calibration/ercot171_coal_licensed_subpop.json`. Harness:
`scripts/lib/sced_corpus_instruments.py`, **unchanged** — `LIMBS`, `assess_limb`,
`fuel_basis_by_year`, `coverage`, `curve_bottom`, `inc_bid_quantiles` all reused
verbatim, and through them `ercot123._decompose` / `ercot136._curve`,`._wq` /
`ercot138.measured_curves`.

## 0. Verdict

| limb | constant | G-LIC | G-NEUT | 2023 level | Δ vs armed | band | **verdict** |
|---|---|---|---|---|---|---|---|
| **A** | `COAL_OFFER_MARGIN_LEVEL_BY_ISO` (ERCOT-137) | **PASS** | **PASS** (15.4549, 0.46×) | **16.0111** | **+0.1304** | ±0.9300 | **CONFIRMED** (0.14×) |
| **C** | `COAL_PEAK_OFFER_LEVEL_BY_ISO` (ERCOT-140) | PASS | **FAIL** (54.3658, **7.6×**) | — | — | ±2.5062 | **NOT-IDENTIFIABLE-2023 CONFIRMED** |

1. **Limb A: the ERCOT-169 unlicensed reading was the COVERAGE DEFECT, not the
   level.** ERCOT-169 measured level₂₀₂₃ 17.5211, **+1.6404 = 1.76× band**, and
   correctly withheld the verdict. With the coverage defect removed by a
   year-neutral rule, delivery-2023 reads **16.0111 — +0.1304, 0.14× band,
   inside**. The armed constant **is** the measured 2023 level. Its
   declared-extrapolation note is **RETIRED BY VERIFICATION** (constants comment
   + matrix only): no solve, no new mechanism, no new DOF, keeper unchanged.
2. **Limb C: the same rule cannot reach it, and the neutrality gate is what
   caught that.** G-NEUT fails by **7.6× band** — the restricted 2024/25 pool
   reads **54.3658** against the armed 35.1989, and the re-derived gas slope
   moves 10.4049 → 8.9503. The restriction is a **level-SELECTING filter** on
   this limb, not a coverage fix, so its 2023 reading is not comparable. ERCOT-169
   §6 **option 1 holds by default**: the extrapolation note **STANDS**, **no
   candidate arm is named, and none may be built on this record** (rule 13).
3. **The mechanism of the split is structural, and it is the whole justification
   for pre-registering G-NEUT.** Limb A's statistic is a **capacity-weighted
   median of the curve BOTTOM**; limb C's is a **p90 of the TOP of the curve**.
   Dropping 18–28 % of the subsets' cap-weight barely moves a median
   (−0.4258 = 0.46× band) and moves a top-decile boundary violently
   (+19.17 = 7.6× band). Without the gate, limb C's 2023 "licensed" reading would
   have looked like a clean refutation and licensed an arm built on a filter that
   had itself moved the level by $19/MWh.
4. **Nothing here is a keeper candidate.** No solve was run and no solve-affecting
   value changed — the `constants.py` diff is **comment-only** (62 insertions /
   11 deletions, zero non-comment lines), and the three constants import
   unchanged. What improves is epistemic status, not dispatch.

## 1. Footing — the pipeline IS the derives' construction

Before any 2023 number was taken, the **unrestricted** pipeline was required to
reproduce the committed identification. It does, essentially exactly:

| check | reconstructed | committed |
|---|---|---|
| limb A pooled level (4 subsets, res-hours-weighted) | **15.8807** | 15.8807 |
| limb C pooled level (derive's own two-year slope, then pooling) | **35.1998** | 35.1989 |
| limb C implied gas slope | 10.4049 | 10.4100 |
| ERCOT-136 `bot_p50` per subset | 16.86 / 16.37 / 15.00 / 15.00 | identical |
| ERCOT-138 `p90` per subset | 34.82 / 34.82 / 43.00 / 48.01 | identical |
| ERCOT-138 §J fuel basis (no-LP keeper reconstruction) | PASS | ±0.02 $/MMBtu |

Because the unrestricted pipeline lands on the armed constants, **any movement
under the restriction is attributable to the restriction alone**.

## 2. G-LIC — the restriction, and what it removes

The rule (precommit §1a): **drop the COAL resources whose OWN `curve_share` falls
below the same 0.9876 floor.** Not a named exclusion list — whichever resources
fail, fail — and applied identically to every year.

* **Delivery-2023 (T1, h11–22 CST, 365 days):** `curve_share` **0.97022 →
  0.99969**, comfortably clearing the floor. Five resources drop —
  `CALAVERS_JKS2`, `MLSES_UNIT1`, `MLSES_UNIT2`, `MLSES_UNIT3`, `WAP_WAP_G8` —
  **26.1 % of the HSL-cap** (reported, non-gating). ERCOT-169's diagnosis is
  confirmed and extended: Martin Lake is the core of it, with two further
  resources joining it below the floor.
* **On the 2024/25 subsets** the same rule drops 4 / 0 / 1 / 3 resources
  (27.9 % / 0 % / 6.0 % / 18.2 % of cap) — i.e. it is **not** a 2023-only
  restriction, which is exactly why its neutrality is testable.

## 3. G-NEUT — the load-bearing gate, and the two limbs' opposite answers

| subset | `bot_p50` unrestr. → restr. | `p90` unrestr. → restr. |
|---|---|---|
| 2024 ercot74 tail | 16.86 → 15.91 | 34.82 → **75.01** |
| 2024 ercot75 control | 16.37 → 16.37 | 34.82 → 34.82 |
| 2025 ercot75 control | 15.00 → 14.73 | 43.00 → **53.00** |
| 2025 ercot86 tail | 15.00 → 14.55 | 48.01 → **75.01** |
| **pooled level** | 15.8807 → **15.4549** (Δ −0.4258, **0.46× band**) | 35.1998 → **54.3658** (Δ **+19.17, 7.6× band**) |

Limb A **passes**; limb C **fails**. The dropped resources were *holding the top
decile down*: removing them lifts `p90` to the ERCOT offer cap region on both
tail subsets. That is a level effect of the filter, not conduct.

## 4. Limb A's 2023 reading, and the caveat carried with it

Restricted delivery-2023, T1: measured curve bottom **16.87**; removing this
form's own fuel response (`10.9832 × (1.8169 − 1.7387) = +0.8589`) gives
**level₂₀₂₃ = 16.0111** against the armed **15.8807** — **+0.1304, 0.14 of the
±0.9300 band**. Full-day (T2) reads **16.0811**, also inside. Stable in both
windows.

**Caveat, stated alongside the verdict and not behind it.** The alternative
**month-scoped restriction (S2)** — pre-declared **REPORTED, NOT GATING**
*before* measuring, on the stated ground that season selection biases a coal
statistic ERCOT-168 showed is seasonally structured — licenses at **0.99818** but
reads level₂₀₂₃ **17.8411, +1.9604 = 2.11× band, OUTSIDE**. **The two routes
disagree for limb A.** The pre-declaration holds up on its own logic: S2 keeps
months {1, 7, 8, 9, 10, 11}, i.e. it drops Feb–Jun *and* Dec and keeps January
plus the whole summer scarcity season, which lifts a curve-**bottom** statistic
in exactly the direction observed (measured bottom 18.70 under S2 vs 16.87 under
S1). S1 is a *population* restriction that leaves the calendar intact; S2 is a
*calendar* restriction that leaves the population intact. Only S1 was gated, only
S1 was neutrality-tested, and only S1 passed a neutrality test — but the
disagreement bounds how strongly limb A's CONFIRMED should be read.

## 5. What is NOT claimed

* **Limb C is not refuted.** The pre-registered REFUTED branch was not reached
  for it either; G-NEUT fired first. Its extrapolation note stands and its
  unlicensed ERCOT-169 magnitudes (measured p90 $75.00, level₂₀₂₃ 71.3378,
  14.4× band) remain **magnitudes, not verdicts** — and explicitly not a licence
  to arm anything.
* **No arm, no solve, no DOF, no keeper movement.** Limb A's consequence is
  documentary by construction: the constant already carried this value.
* **The ercot-168 corroboration is not re-claimed for limb A.** ERCOT-169 read
  limb A's unlicensed +1.64 as pointing the same way as the ERCOT-168 2023 coal
  repricing. That reading is **withdrawn for limb A**: on the licensed
  instrument the 2023 min-load level is the armed one. ERCOT-168's per-plant
  repricing stands on its own evidence and is untouched; what dissolves is the
  *fleet-level min-load* corroboration, not the per-plant finding. Limb C's
  unlicensed magnitude still points that way and still cannot be certified.

## 6. Governance

* **No mechanism tested ⇒ no cell verdict minted** — both cells stay `K`; their
  notes are re-cited with the ercot-171 record (rule 28(b)). Matrix §5.1 **item
  14** added and stamped EXECUTED in the same session.
  `scripts/check_mechanism_matrix.py` **exit 0** (230 pre-existing warnings —
  anchor drift + the CAISO keeper-stamp drift, neither this session's).
* **No run produced ⇒ no dashboard registration** (rule 15). Keeper UNCHANGED.
* **Rule 22 `[R-HOLDOUT]`**: delivery-2023 corpus only; the 2024/25
  identification subsets are training-span probe days. Nothing outside 2023–2025
  was read, solved or scored; ERCOT holds no `complete` marker.
* **Rule 23 `[R-FROZEN-DERIVE]`**: no derive re-run, no measured-behaviour
  parameter re-identified, no constant value changed. The `constants.py` diff is
  **comment-only** and both blocks' comments are the identification record.
* **Rule 24/26**: nothing added, nothing zeroed — no re-armable knob created.
* **Rule 25 `[R-ISO-SCOPE]`**: ERCOT-scoped throughout.
* **Rule 27 `[R-PUSH]`**: `constants.py` edited locally (Edit tool) and
  blob-verified after push; no regenerated full-file content was pushed.

## 7. DO-NOT-REDO honored

Per-year CT re-identification stays REFUSED (ERCOT-147); lignite offer SLOPE
(ERCOT-143); `coal_min_load_floor` both grains; lignite daily unit commitment;
coal seasonal LEVEL split; `coal_offer_level_rebasis` `R`;
`tranche_startup_amortization` `G`; ERCOT-168 **OPTION B** stays DEFERRED; the
"~8 GW cheap CC offline block" DOES NOT EXIST (ERCOT-163);
`energy_online_capability_cap` `R`; `ercot_storage_rt_offer_surface` `R`; the
ercot-167 SOC-reserve re-gate still waits on the H4-item-4 defect; the
West/Panhandle topology split is CLOSED. **ERCOT-170's item-11 result stands**
untouched (the CC headroom object is a capability object; its per-unit crosswalk
is `FILED-UNLICENSED` and re-pointed to a data-intake charter).

**Next shorthand: ercot-172.**

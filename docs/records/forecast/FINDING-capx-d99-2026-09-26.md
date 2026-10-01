# FINDING — capx D99: T1.6 re-pointed to `entry_pipeline_aware_signal`; the NEISO REC dual leaves the ACP

**Lane:** capx **D99** · **Date:** 2026-09-26 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d99-t16-repoint` · **Authority:** OWNER RULING **Q72** (capx ledger §0bl / §3):
*"Re-point, 2041–2050 mean"* = DESIGN-capx-d97 §6 (a) + (a-2).
**Pre-registration:** `PRECOMMIT-capx-d99-2026-09-26.md`, pushed before any LP at
**`aa4e60ca0145953ef323b6fdadffae0dd1686ede`**, the SHA the shard was pinned to. The lane branch was later rebased
onto `origin/main` (`a59c4f6f`) for scoring.

---

## 0. THE VERDICT TRANSITION, AND THE OUTCOME LETTER

| | determination | FC-1 … FC-8 | caveats |
|---|---|---|---|
| **BEFORE** `neiso-t3` (capx D96) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT **CAVEAT** FAIL PASS | FC-5, **FC-6** |
| **AFTER** (D99) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT **PASS** FAIL PASS | FC-5 |

**FC-6 moves CAVEAT → PASS.** Its battery row changes from *"2 vacuous row(s): T1.6a (all-constant series
[1.0, 1.0]), T1.6b (all-constant series [1.0, 1.0])"* to *"all 2 gate rows PASS"*. Every other status, reason,
caveat and detail string is identical, and the paired P1/P2/P3 rows are unchanged because their inputs are
carried. The determination stays **HOLD**, because FC-1/2/3/4/7 still FAIL. The prior record is preserved
byte-equal at **`neiso-t3-pre-d99`**. `program-status.json` moves exactly one letter: NEISO `fc.FC-6`
CAVEAT → PASS.

**Outcome letter: A on the dual and on every score, with its volume clause NOT met.** The pre-declared A row
reads "`renewable_build_gw` long ≫ short (≥ 50 GW) **and** long final-year dual < 50".
* **The dual half is met.** The 2050 dual is 0.001, so `rps_dual_over_acp` is 0.0. The 2041–2050 mean is 0.4.
* **The volume half is not met.** `renewable_build_gw` is **38.802 GW** against 33.0 short: +5.8 GW, not ≥ 50.
* No other letter fits. It is not **B** (2050 is not back at the ACP), not **C** (the build did re-size), not
  **D** (the dual left the ACP) and not **E** (nothing rose). The realized state satisfies A's scoring cells and
  fails its volume premise.

It is reported as that. It is not rounded into a clean A, and no letter was re-drawn after the fact.

**In one sentence:** the lever reached the binder D97 named, and the REC dual left the $50 ACP for the first
time in any committed NEISO leg (2042). But the build was far smaller than designed: solar went margin-bound in
2035, and the entry screen then cobwebbed around the target exactly as DESIGN-d97 §2.3 predicted. The dual also
cleared while D97's own obligation reconstruction still shows the region 5 TWh short, so that reconstruction is
not the LP's row (§2).

---

## 1. THE RUNGS AT FULL MAGNITUDE

| metric | `vre_short` (= D96 `base`, reused) | `vre_long` (solved) | Δ |
|---|---:|---:|---:|
| key | `dbef1ecac9596c90` | `883f25eb5ee3e55e` (predicted, exact) | |
| `rps_dual_over_acp` (final year; T1.6a) | 1.0 | **0.0** (2050 dual 0.001) | −1.0 |
| `rps_dual_over_acp_mean_2041_2050` (T1.6b) | 1.0 | **0.4** | −0.6 |
| `renewable_build_gw` | 33.0 | **38.802** | +5.802 |
| VRE fleet 2050 (MW) | 37,100 | **42,902** | +5,802 |
| `entry_thermal_gw` | 7.4839 | **5.427** | −2.057 |
| `total_build_gw` | 41.2039 | 49.269 | +8.065 |
| `co2_mt_total` 2026–2050 | 151.2747 | **140.1085** | −11.166 (−7.4 %) |
| `reserve_margin_final` | 0.06107 | **0.08468** | +0.0236 |
| `retired_thermal_gw` (econ / exog) | 5.741 (2.6476 / 0.1432) | 10.342 (4.239 / 0.1432) | +4.601 |
| `lw_price` (mean zonal, $/MWh) | 61.123 | 56.938 | −4.185 |
| `gas_cc_twh` | 266.669 | 265.0611 | −1.608 |
| storage fleet (MW) / marginal ELCC | 3,355 / 0.38343 | 7,675 / 0.1573 | |
| wall / peak RSS | (D96: 33.4 min / 3.53 GB) | **37.0 min / 4.45 GB** | |

**The REC dual, year by year in `vre_long`** (the short rung is 50.0 in all 25 years):

| 2026–2041 | 2042 | 2043 | 2044 | 2045 | 2046 | 2047 | 2048 | 2049 | 2050 |
|---|---|---|---|---|---|---|---|---|---|
| 50.0 (every year) | **0.001** | 0.001 | 0.001 | 0.001 | 0.001 | 50.0 | 50.0 | 50.0 | **0.001** |

### 1.1 Why the build is 38.8 GW and not 55–66 (from the committed ledgers, `entry_decided_mw_by_tech`)

1. **2027–2034: the un-netting works exactly as D97 traced.** The long rung decides the full 2,000 solar +
   1,000 wind every year. The short rung alternates 1,198 / 1,802 MW of net flow. Commissioned VRE runs at
   **3,000 MW/yr 2030–2036**, which is the C = 3.0 GW/yr the design predicted in place of C/L = 1.5.
2. **2035–2037: solar goes MARGIN-bound, not cap-bound.** Wind-only decisions, 1,000 MW/yr, and **zero
   solar**, with the dual still at $50. DESIGN-d97 §1.4 item 1 ("VRE is cap-bound, not margin-bound, in every
   committed leg") held for every leg it measured. It **does not hold for the long rung past ~27 GW of VRE**.
   Solar's energy capture falls as the fleet saturates the midday hours (the I3 dump is already 2–8 % of the
   renewable pot in the base's 2043–2050), and the $66k/MW-yr REC credit no longer covers the gap.
3. **2038–2039: the shared 4 GW/yr ISO budget binds.** Solar re-enters at 1,500 MW, not 2,000, beside
   1,000 gas_cc and 550–877 gas_ct. D97 §2.5(b) flagged this risk ("the 4 GW/yr ISO budget may also start
   binding against VRE + thermal together"), and it happened.
4. **2042–2047: the cobweb.**
   * The dual reaches ≈ 0 in 2042, so the screen loses the REC credit.
   * Decisions go to **zero 2043–2047**. The fleet stalls at 39.9 GW while load grows, so the region falls
     short again and the dual returns to **50.0 in 2047–2049**.
   * The credit comes back, the screen re-decides 3 GW/yr in 2048–2050, and the 2050 commissioning tranche
     drops the dual to 0.001 again.
   * This is DESIGN-d97 §2.3's predicted cobweb, measured. Whether 2050 lands on the off-ACP side is the
     coin-flip P5 named.

**What that means for the instrument.** Under the pre-registered final-year scalar, this run would have
scored T1.6b on one year's side of a cycle whose phase happened to land off-ACP in 2050. The Q72 2041–2050 mean
reads **0.4**: 6 of 10 years off the ACP. It measures the regime and does not depend on where the 2050 phase
happens to land. That is the property sub-choice (a-2) was ruled for. Here both constructions happen to agree
on the sign.

---

## 2. PREDICTIONS, GRADED AS WRITTEN (PRECOMMIT §4.2)

**12 graded: 9 HIT, 2 MISS, 1 not gradable (a stated probability).**

| # | prediction | realized | grade |
|---|---|---|---|
| P1 | outcome **A or B** (joint ≈ 0.6) | A's scoring cells with its **volume clause failed**. No pre-declared letter fits exactly (§0) | **MISS**, graded strictly: the realized state is not a pre-declared row |
| P2 | `renewable_build_gw` long ∈ [55, 66], point 58 | **38.802** | **MISS**, by 16 GW below the band edge (§1.1: margin-bound solar, ISO budget, cobweb) |
| P3 | first off-ACP year ∈ [2038, 2043], point 2041 | **2042** | HIT (point off by one year) |
| P4 | window mean ∈ [0.2, 0.9], point 0.5 | **0.4** | HIT |
| P5 | P(2050 back at 50 \| off-ACP inside the window) ≈ 0.5 | not back (0.001), though 2047–2049 were | not gradable; one draw of a coin flip |
| P6 | `entry_thermal_gw` moves ≥ 0.5 GW | −2.057 GW | HIT |
| P7 | `co2_mt_total` long < short | 140.1085 < 151.2747 | HIT |
| P8 | `reserve_margin_final` moves | 0.06107 → 0.08468 | HIT (weak) |
| P9 | key `883f25eb5ee3e55e` exact | exact | HIT |
| P10 | wall ∈ [30, 50] min, RSS < 5 GB | 37.0 min, 4.45 GB | HIT |
| P11 | ledger-grain window mean = cache-grain | 0.4 = 0.4 | HIT |
| P12 | only FC-6 moves; paired rows identical | exactly that | HIT |

**The one-sentence summary, graded clause by clause:** *"Un-netting the pending stock roughly doubles NEISO's VRE
build to ~58 GW, the REC dual leaves the $50 ACP around 2041, and the 2041–2050 mean reads the regime (~0.5)
that the final-year point cannot — so T1.6b passes non-vacuously, while FC-6 clears to PASS only if the 2050
dual also stays off the ACP."*

| clause | verdict |
|---|---|
| doubles the VRE build to ~58 GW | **WRONG.** The *flow* doubles (3.0 GW/yr for seven years); the *build* is +18 %, 38.8 GW |
| the dual leaves the ACP around 2041 | RIGHT, one year late (2042) |
| the mean reads the regime, ~0.5 | RIGHT, 0.4 |
| T1.6b passes non-vacuously; FC-6 PASS only if 2050 also off-ACP | RIGHT on both. 2050 was off-ACP, so FC-6 PASS |

**The wrong clause fails for one reason: DESIGN-d97's zero-LP arithmetic held the fleet cap-bound for 25
years.** It is cap-bound for about seven (§1.1).

**A second measurement also contradicts the design's arithmetic, and this lane does not resolve it.** Re-run
D97 §7's own reconstruction (obligation = target × `total_gen_mwh`; eligible = wind + solar) over this bundle:

| `vre_long` year | obligation (TWh) | wind + solar (TWh) | reconstructed gap | LP dual |
|---|---:|---:|---:|---:|
| 2041 | 70.5 | 62.9 | 7.6 short | 50.0 |
| **2042** | 73.0 | 67.8 | **5.2 short** | **0.001** |
| 2045 | 78.6 | 72.3 | 6.3 short | 0.001 |
| 2047 | 80.7 | 73.3 | 7.4 short | 50.0 |
| 2050 | 83.9 | 77.2 | 6.7 short | 0.001 |

The LP reads the region as compliant in 2042–2046 and 2050 while the reconstruction still shows it 5–7 TWh
short. So D97 §1.2's reconstruction is **not** the row `_build_rps_row` builds. The row either counts a wider
eligible set (`eligible_gen_idx`, e.g. Class I hydro / biomass) or tests against a different base (demand
rather than total generation, which differ by net imports and storage losses). The discrepancy is roughly
constant, 5–7 TWh, which fits a fixed eligible block better than a base effect. **Not decomposed here**: §6
item 1. It explains why the dual moved on a fleet the design would have called short, and it means D97 §1.2's
"≈ 9 GW short at 2050" overstated the gap in the short rung too. No third lever was tried.

---

## 3. THE ACT (charter items 1–2) — LADDER, METRIC, PLAN §2, TESTS, CROSS-LANE RE-GRADE

As PRECOMMIT §1, unchanged since the push:

* **Ladder:** `run_driver_battery.py` T1.6 rungs → `{"entry_pipeline_aware_signal": False/True}`. The
  history of both prior levers is kept in place.
* **Metric:** `rps_dual_over_acp_mean_2041_2050`, with window `T16B_MEAN_WINDOW = (2041, 2050)` cited to Q72.
  It is emitted only when the window is complete. T1.6a is untouched.
* **Plan §2:** one appended sentence on the T1.6 row.
* **Tests:** the T16-A pin class now pins Q72, plus `TestT16bHorizonMeanMetric`.

**Scorer test lane:** `pytest tests/scoring`: 1,660 passed. 17 failures are environmental (un-hydrated data)
and are the **identical fail set on `origin/main`**.

**Cross-lane re-grade: no other registered verdict moves.**

| class | n | result |
|---|---:|---|
| re-scorable (`rescore_forecast_verdicts.py`), run at `main` and at this branch; re-run at the rebased HEAD | 25 | **25/25 `moved: nothing`**, output identical but for the wall-clock stamp |
| battery-bearing (`neiso-t3`, `neiso-t3-pre-d96`), re-scored over their committed inputs | 2 | both reproduce **non-provenance identical** under the new code |
| no tracked artifact | 83 | scorer path byte-unchanged (`forecast_verdict.py` not edited and does not import the battery) |

## 4. THE SHARD AND THE REUSE (rules 32 / 33 / 34 / 36)

* **`vre_short` was not solved.** G-DRIFT `5a48f437 → f1ea324a` was all-INERT: 20 code files and 20 data
  paths, classified hunk by hunk in PRECOMMIT §2.3. The resolved config keys to D96 `base`'s literal. The row
  was built at zero LP (`docs/handoffs/d99/battery_golden_rung.py reuse`) with two asserted inputs: 25/25
  ledgers byte-identical to D94 `vre_short`, and an identical trajectory.
* **`vre_long`: one shard, one 2026–2050 invocation.**
  * **Launch 1 never solved.** Its container came up on `main` (`f1ea324`) instead of the pinned SHA. It
    stopped at hard stop H1 exactly as instructed, pushed nothing, and was archived.
  * **Relaunch.** The shard checked out the pinned commit itself and cleared H1–H3. It pushed the full out-dir
    with a `.gitignore` negation and plain `git add`: **79 files** (`git ls-tree`, rule 34(d)).
* **Parent verification, before archiving:**
  * fetched the shard branch;
  * the diff outside the bundle is only the `.gitignore` negation;
  * pins, `entry_rate_limits` True, override, mode, ISO, 25 years and key all confirmed off `run_config.json`;
  * **recomputed the rung row from the fetched caches: byte-identical to the shard's.**
  * Then archived. **Both shard sessions are archived.**
* **Landed on `main` (rule 33(f)):**
  * the `vre_long` slim bundle (summary, run_config, `config.yaml`, `solve_surface.json`, 25 ledgers);
  * both rung rows;
  * the assembled battery JSON + md (`results/ff-t3-neiso-golden/d99/`);
  * `ff-verdicts.json` and `program-status.json`.

  Per-year parquets stay off `main` (`.gitignore` block added in the PRECOMMIT). The shard's cache-parquet
  branch is **not merged**, per the D94/D96 precedent.
* **Retrievability (rule 34(e)).**
  * Everything the verdict reads is on this branch, headed for `main`.
  * The `vre_long` parquets exist on shard branch `claude/capx-d99-vre_long`, which is transport and is cut
    when this PR merges, and in this container's working tree, which is ephemeral.
  * Leg SHAs, provenance only (rule 33(d)): slim `a45df4114d3b43617dd62ff82c97bfcc695d21f0`, parquets
    `9ed28efd3d3f3eaa659134b3c11ec2eafbd3d6e0`.
  * **Any per-hour question after the cut costs a re-solve:** ~37 min LP plus ~100 min of container
    preparation, as measured here.
* **Leftover ref the owner must remove:** `claude/capx-d99-vre_long`. A session cannot delete a ref, and no
  deletion was attempted. Launch 1 pushed no branch.
* **Key provenance:** `check_key_provenance.py` passes. 249 records, 193 reproduce, 28 no key, 28 mismatch,
  all known, lag or surface-recorded classes. `d99/vre_long` reproduces its own key.
* **Rule 28:** the NEISO `entry_pipeline_aware_signal` cell gets its first `ev` stamp and **stays `U`/`U`**
  (28(d): a ladder perturbation, not an arming adjudication). No field is added and no default moves.
* **Rule 31:** nothing was deleted. **Rule 27:** every pushed file of 300+ lines was blob-verified.
* **`src/` untouched.** The one `scripts/` edit is `run_driver_battery.py`, charter item 2.

## 5. THE RE-SCORE (charter item 5)

Controlled swap per D90-R A.2, run at the **final rebased HEAD** (`230baf5c`).

**Step 0.** `forecast_verdict.py --tier t3` over the standing record's committed inputs, with the D94 battery,
reproduces `ff-verdicts.json["neiso-t3"]` **non-provenance identical**.

**Step 1.** Only `--driver-battery` is swapped, to `d99/driver-battery-neiso-2026-09-26.json`. Result: §0.

Registered as `neiso-t3`, with the prior record byte-equal at `neiso-t3-pre-d99`. This lane was the sole
`ff-verdicts.json` writer.

## 6. NAMED AND LEFT

1. **D97 §1.2's obligation-vs-eligible reconstruction is not the LP's RPS row** (§2). The dual clears while the
   reconstruction shows a 5–7 TWh gap. The measurement is to read the row's eligible set and base for NEISO
   off `_build_rps_row` / `eligible_gen_idx` and reconcile per year. It is zero LP on committed code plus this
   bundle's parquets, which exist until the shard branch is cut. **No live owner exists.**
2. **The entry screen's REC-credit cobweb** (§1.1 item 4). The screen reads the prior year's binary dual, so it
   alternates between building everything the caps allow and building nothing. That is the anti-cobweb guard
   FFR-5C relocated to the price signal, and here it did not damp. This is **arming evidence for
   `entry_pipeline_aware_signal` in NEISO, not an arming decision** (rule 25). **No live owner exists**; an
   arming card would be the owner's to request.
3. **Solar going margin-bound at ~27 GW of VRE** (§1.1 item 2) falsifies DESIGN-d97 §1.4 item 1 for the long
   rung. That is recorded, and no lever follows from it (honesty clause).
4. DESIGN-d97 §5 items 1–5 (the OSW REC-credit inconsistency, the OSW procurement map, the NEISO queue-cap
   re-derivation, T1.6's nuclear clause, a stringency ladder) are unchanged by this lane. **Still no live
   owner.**
5. D96 §6 items 2 (FC-6 P1's horizon-edge sensitivity), 3 (I13 order nondeterminism) and 5 (every other T3
   golden's FC-6) are untouched. **Still no live owner.**

## 7. THE PROMOTION QUESTION

The forecast board has determinations, not keepers. The re-score is registered as `neiso-t3`. Two decisions are
the owner's:

* **(a)** Merge this as the standing `neiso-t3`. It is **FC-6 CAVEAT → PASS** and the determination stays HOLD.
* **(b)** Should the `vre_long` per-year parquets be kept anywhere beyond the shard branch that this PR's merge
  cuts? The verdict does not need them. §6 item 1's decomposition would, and without them it costs a re-solve
  (~37 min LP plus container preparation).

# FINDING — capx D94: `neiso-t3`'s FC-6 driver battery, re-measured on the post-D77 basis

**Lane:** capx **D94** · **Date:** 2026-09-24 · **Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `neiso`
**Branch:** `claude/capx-d94-fc6-driver-battery` · **Authority:** OWNER RULING **Q67** (capx ledger §0bj / §3)
**Pre-registration:** `PRECOMMIT-capx-d94-2026-09-24.md`, pushed before any LP at **`924017c856780bd4b7e989624d621e621c215f75`**
(the SHA both shards were pinned to)

---

## 0. THE VERDICT TRANSITION

| | determination | FC-1…FC-8 |
|---|---|---|
| **BEFORE** `neiso-t3` (capx D92, 2026-09-10) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |
| **AFTER** (FC-6 driver battery re-measured) | **HOLD** | FAIL FAIL FAIL FAIL CAVEAT CAVEAT FAIL PASS |

**Nothing in the verdict moved: every category, row, detail string, reason and caveat is identical.** Even
the FC-6 battery row's text is byte-identical, because both rungs still read `rps_dual_over_acp = 1.0`. The
prior record is preserved byte-equal at `neiso-t3-pre-d94`.

**In one sentence:** the battery now describes the same model as the verdict, and every level under it
moved a long way. CO2 fell by 39–42 %, retirements roughly doubled on the CCS wave, and the terminal margin
fell. **T1.6 still cannot discriminate.** Its lever (`entry_rate_limits`) does not reach NEISO's
wind/solar supply, which is **33.0 GW in both rungs**, and the REC dual sits at the $50 ACP in every
year of both rungs.

**What the old battery was, stated plainly.** The carried 2026-09-03 file came from
`run_driver_battery.py`, which solves a rung as `ScenarioConfig(iso, use_campd_bins=False, …)`. That means
dataclass defaults, legacy bins, and **neither `neiso-t3` pin**. It was a third model, not the
verdict's. Its rungs are now solved on the verdict's own golden recipe with both pins (§1). **The
pre → post deltas below therefore mix three things: D77, the recipe correction, and HEAD drift.** They
are not D77 alone, and this report does not attribute them to it.

---

## 1. THE PER-RUNG TABLE (pre-D77 2026-09-03 → D94), AT FULL MAGNITUDE

| metric | `vre_short` 09-03 | **`vre_short` D94** | `vre_long` 09-03 | **`vre_long` D94** |
|---|---|---|---|---|
| `co2_mt_total` | 246.3862 | **151.2747** (−38.6 %) | 275.4997 | **159.6764** (−42.0 %) |
| `retired_thermal_gw` | 2.012 | **5.741** | 3.005 | **4.788** |
| `economic_retired_thermal_gw` | 0.1603 | **2.6476** | 0.1603 | **2.6941** |
| `exogenous_retired_thermal_gw` | 0.13 | **0.1432** | 0.13 | **0.1432** |
| `reserve_margin_final` | 0.08368 | **0.06107** | 0.06353 | **0.05575** |
| **`rps_dual_over_acp`** | **1.0** | **1.0** | **1.0** | **1.0** |
| `renewable_build_gw` | 33.0 | **33.0** | 33.0 | **33.0** |
| `entry_thermal_gw` | 3.0089 | **7.4839** | 3.028 | **8.4371** |
| `total_build_gw` | 36.7289 | **41.2039** | 36.748 | **42.1571** |
| `gas_cc_twh` | 559.7369 | **266.669** | 657.2446 | **294.8396** |
| `coal_twh` | 0.3784 | **0.0** | 0.3784 | **0.0** |
| `lw_price` | 67.677 | **61.123** | 66.979 | **61.298** |
| `scarcity_hours` | 0 | 0 | 0 | 0 |
| storage (fleet MW / cap value / avg ELCC / long-dur share) | 3355.0 / 0.38343 / 0.88937 / 1.0 | **identical** | same | **identical** |
| `net_cone` | 108.94 | 108.94 | 108.94 | 108.94 |

| rung | cache_key (predicted = actual) | wall | peak RSS | solved at |
|---|---|---|---|---|
| `vre_short` | `1be407901f4f8000` | 37.4 min | 3,394 MB | `924017c8` |
| `vre_long` | `df7b178ae9ccbe41` | 33.5 min | 3,449 MB | `924017c8` |

**T1.6a** PASS "all ≤ 1.0", and **T1.6b** PASS "↓ [1.0, 1.0]". Both are PASS results on an all-constant
series, so FC-6 reads them as **VACUOUS**. That was true before and is true now.

### 1.1 Why the ladder cannot discriminate, and what would

* **The lever does not reach VRE.** NEISO wind/solar entry is bound by
  `QUEUE_CAP_PER_TECH_GW["NEISO"]` (wind 1.0 + solar 2.0 GW/yr, `config/capacity_market.py:5794`), netted
  against the 2-year commissioning pipeline. That netting is the documented `K−L+1 = 1` ratchet at
  `model/capacity_evolution/new_entry.py:1695–1706`, and it yields the alternating 1,802 / 1,198 MW/yr
  pattern that totals 33,000 MW. It binds **before** the `ENTRY_GROWTH_LIMIT_MULTIPLE` ladder does. The
  rung pair therefore holds VRE supply **identical**; the pre-D77 battery showed the same thing.
* **What the rungs actually differ in is thermal entry.** This is the confound `run_driver_battery.py`
  itself declares. Uncapping entry builds 1 GW more economic gas CC (8.0 vs 7.0 GW) and a smaller CCS
  retrofit wave: `gas_cc_ccs` is 6,402.8 vs 6,979.7 MW at 2030 and 1,859.0 vs 2,940.5 MW at 2050.
  Hence **+8.40 Mt CO2 (+5.6 %)**, a lower terminal margin, and **fewer** "retired" MW. That last point
  is because the metric counts a CCS conversion as a `gas_cc` drop.
* **The REC dual is pinned at the $50 ACP in all 25 years of both rungs.** It was also pinned in all
  four D92 paired arms, the carbon +$25 arm included. NEISO's target is unreachable at 1.5 GW/yr of net
  VRE flow.
* **What would discriminate:** a rung pair whose `renewable_build_gw` actually differs, meaning a
  lever on the queue-cap / pipeline binding (e.g. `entry_pipeline_aware_signal=True`, or a different
  `QUEUE_CAP_PER_TECH_GW["NEISO"]`). It would also need enough VRE to bring the dual off the ACP, which
  no committed NEISO leg has shown. **Owner ruling Q27 forbids trying a third lever inside the
  ladder**, so this is named here and not tried. Re-pointing T1.6 is an owner card.

---

## 2. PREDICTIONS, GRADED AS WRITTEN (PRECOMMIT §4)

**11 hits and 1 miss.** Four of the hits (P7, P8, P9, P11) were declared near-certainties in the PRECOMMIT
and are worth nothing. P10 was declared weak.

| # | prediction | realized | grade |
|---|---|---|---|
| P1 | `vre_short` CO2 ∈ [140, 170] | 151.2747 | **HIT** |
| P2 | `vre_long` > `vre_short` by +3…+20 %, ∈ [150, 195] | 159.6764, **+5.6 %** | **HIT** |
| P3 | `vre_short` retired ∈ [4.5, 6.5] GW | 5.741 | **HIT** |
| **P4** | `vre_long` retired **≥** `vre_short`, ∈ [4.5, 8.0] | **4.788 < 5.741** (in bracket, **wrong sign**) | **MISS** |
| P5 | `vre_short` RM ∈ [0.055, 0.075] | 0.06107 | **HIT** |
| P6 | `vre_long` RM < `vre_short`, ∈ [0.035, 0.070] | 0.05575 | **HIT** |
| P7 | `rps_dual_over_acp` = 1.0 on both | 1.0 / 1.0 | HIT — *near-certainty* |
| P8 | `renewable_build_gw` = 33.0 on both | 33.0 / 33.0 | HIT — *near-certainty* |
| P9 | T1.6a/b stay vacuous | both named vacuous | HIT — *near-certainty* |
| P10 | `vre_short` ≠ `d92/base` exactly, but CO2 within ±8 % | 293 differing cells, **−2.04 %** | HIT — *weak* |
| P11 | HOLD; every FC status/reason/caveat and the FC-6 detail identical | all identical | HIT — *near-certainty* |
| P12 | wall ∈ [28, 50] min, RSS < 5 GB | 37.4 / 33.5 min; 3.39 / 3.45 GB | **HIT** |

**Why P4 missed.** I carried the sign over from the pre-D77 battery, where `vre_long` retired +1 GW
more. On the golden recipe, uncapped entry **shrinks** the CCS retrofit wave (§1.1). Because the metric
books conversions as retirements, `vre_long` "retires" less. My reasoning assumed the CCS wave was
rung-invariant, and it is not.

**The one-sentence summary, graded:** *"moves every battery level a long way — CO2 down by about a third,
retirements more than doubled by the CCS wave, the terminal margin down — and moves no score, because the
lever cannot reach NEISO's VRE supply and the REC dual is pinned at the ACP."*

* CO2 "about a third": **roughly right.** The actual fall is 39–42 %, a little more than a third.
* Retirements "more than doubled": **right for `vre_short`** (2.01 → 5.74, ×2.9). **Wrong for
  `vre_long`** (3.01 → 4.79, ×1.6).
* Terminal margin down: **right** on both rungs.
* No score moves, and the lever/ACP account of why: **right.**

---

## 3. G-DRIFT

* **Config, zero LP.** `vre_short` is config-identical to the control, `d92/base`, apart from 38 fields
  added to the schema since then. Every one of those fields is registered and sits at its frozen drop
  value. `vre_long` adds exactly one real difference, `entry_rate_limits`. Both rung keys came out
  exactly as predicted (§1).
* **Key literal vs `dd8203a8bf1546b9`: two key-rule changes, neither a config difference.**
  1. `caiso_dsw_lateevening_clean` was registered after D92 solved. Un-dropping it reproduces
     `dd8203a8…` exactly.
  2. The NEISO solve-surface moved on `RGGI_MEMBER_STATES_BY_YEAR` (2020/2022 rows added). That change is
     inert for 2026–2050, because every lookup in that range resolves to 2025 or misses.
* **D93: this pinned SHA contains D93's registration.** `coal_mustrun_requires_measured_row` is dropped
  at its frozen value `"False"`. At the pre-D93 `6640becc`, the same `vre_short` config keyed
  `2336cd3641492c6d`.
* **Code and data: measured, not argued.** `vre_short` doubles as a same-HEAD control, and it does
  **not** reproduce `d92/base`. Against the committed control:
  * **293 trajectory cells differ.**
  * **Cumulative CO2: 154.4195 → 151.2747 Mt (−2.04 %).** Per year: 2026 +0.18, 2029 −0.22, 2030 −0.30,
    2050 −0.17 Mt.
  * **The 2030 CCS fleet: 6,648.3 → 6,979.7 MW.**
  * **RM₂₀₅₀: 0.0639 → 0.0611.**
  * Load-weighted prices move down ~0.1–0.4 $/MWh.

  The only LIVE hunk the audit found is **F1** (eGRID-2024 heat rates, merged 2026-09-24, whose own note
  says it invalidates every forecast at the same key). **The attribution to F1 is the likely one and is
  not proven.** D92's solve SHA (`aac390a6`) does not resolve in this grafted clone, so the full
  D92 → D94 window cannot be hunk-audited.
* **Consequence, declared in advance by PRECOMMIT §2.3.** `neiso-t3`'s FC-6 battery now sits on
  **post-F1** data, while its primary bundle, its paired block and its FC-5 table sit on **pre-F1**
  data. The T1.6 rows compare the two rungs to each other at one HEAD, so the battery is internally
  coherent. The verdict as a whole now spans two data vintages. The magnitude is small at the
  cumulative level (−2 %) and larger in the CCS fleet (+5 % at 2030).

---

## 4. THE RE-SCORE — A CONTROLLED SWAP

The re-score was run at the final rebased HEAD `7d167ed8`. First, `forecast_verdict.py --tier t3` over
the committed inputs reproduces `ff-verdicts.json["neiso-t3"]` NON-PROVENANCE IDENTICAL. Then **only
`--driver-battery`** was swapped, to `results/ff-t3-neiso-golden/d94/driver-battery-neiso-2026-09-24.json`.

**Result: identical in every non-provenance field.** Registered as `neiso-t3`, with the prior record kept
byte-equal at `neiso-t3-pre-d94`. **FC-7 did not move**; its inputs are carried, so D90-R Addendum B was
not triggered. `program-status.json` is untouched because no FC letter moved.

---

## 5. RULE 32 / 33 / 34 / 31 RECORD

* **The parent ran no LP.** Two shards were launched concurrently, each pinned to the full SHA with the
  hard stops in the prompt. Both cleared H1–H3.
  * Each committed **only** its own out-dir plus the `.gitignore` negation.
  * Each pushed its **full** out-dir (≈ 43–44 MB): a slim commit first, then the parquets.
  * Leg SHAs, as provenance only (rule 33(d)): `vre_short` `43f6bcfc…` → **`ce591e952537564012d581c52dbb8885087dcc6e`**;
    `vre_long` `16f45636…` → **`f36433cf375c9e2cf9a02bc5a7de91a30e072e6b`**.
* **Parent verification.**
  * Config signature and both pins were checked off each `run_config.json`.
  * **The parent recomputed both rung metrics from the fetched caches, and they match the shards'
    byte-for-byte.** The instrument's `co2_mt_total` equals the summary-grain Σ`co2_mt` on both rungs.
* **Assembly validation (before any LP).** The helper re-emits the committed 2026-09-03 battery JSON and
  markdown byte-identically.
* **Both shards are archived** (rule 33).
* **What landed on `main` (rule 33(f)).**
  * The battery JSON + md, both rung rows, and each rung's slim bundle: summary, run_config,
    `config.yaml`, `solve_surface.json`, 25 evolution ledgers. That is 1.9 MB.
  * The per-year cache parquets are **kept off `main`** by `.gitignore`. They exist on the two shard
    branches, which are transport, not storage. Re-deriving anything from them after those branches are
    cut costs **a re-solve (~35–40 min per rung)**.
* **Rule 31.** Nothing was deleted. The parquets are in this container's working tree and on the shard
  branches.
* **`check_key_provenance`.** Records rise 244 → 246 and reproduce 188 → 190; both D94 run_configs
  reproduce their own keys. The four `d92/*` rows are `G1_UNKNOWN` at this HEAD (§3's
  `caiso_dsw_lateevening_clean` lag class), and this lane did not add them to the exceptions list.
* **Rule 27.** Every pushed file of 300+ lines was pushed with `git push` as its exact on-disk bytes and
  blob-verified against the remote after the push.

---

## 6. NAMED AND LEFT

1. **Four new `G1_UNKNOWN` rows**, `d92/{base,carbon_plus25,gaspm5,gasup150}/run_config.json`. They are
   the `caiso_dsw_lateevening_clean` registration's lag class. **OWNER: the key-provenance desk (capx
   D85 / D91 / D93).**
2. **`neiso-t3`'s primary bundle, paired block and FC-5 table are pre-F1** (§3). **OWNER: the capx
   director's desk.** F1's note assigns forecast re-solves to "each forecast lane on its own cadence".
3. **T1.6 cannot discriminate in NEISO on this code** (§1.1). **OWNER: the owner.** Re-pointing a ladder
   needs a Q27-class ruling.
4. **Every other T3 golden's carried FC-6** (D92 §9.8) is out of this charter. **It still HAS NO LIVE
   OWNER.**

## 7. THE PROMOTION QUESTION

The forecast board has no keepers, so there is nothing to promote in rule 15's sense. The re-score is
already registered. Two decisions are the owner's:

* **(a)** Should `neiso-t3`'s **primary bundle, paired arms and FC-5 table be re-solved post-F1**, so the
  verdict sits on one data vintage again? Cost: 4 legs, ~2.5 h of LP, plus the FC-5 re-base.
* **(b)** Do you want a **Q27-class ruling to re-point T1.6** onto a lever that actually moves NEISO
  VRE supply?

The per-year parquets are in this container and on the shard branches, and **neither survives**: the
container is ephemeral and the branches are cut on merge. Everything the verdict needs is already on
`main`.

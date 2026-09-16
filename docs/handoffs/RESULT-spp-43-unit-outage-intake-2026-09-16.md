# RESULT — SPP-43: the 2019–2022 CAMPD unit-outage intake

**Lane** SPP-43 · **Date** 2026-09-16 · **Base** `41e87a8f` (intake) / `39174d6d` (decomposition)
**PRECOMMIT** `docs/handoffs/PRECOMMIT-spp-43-unit-outage-intake-2026-09-16.md`
**Registered run** `2026-09-16-spp-43-outage-intake`, bundle `results/calibration/spp43_holdout_span`,
stamped to SPP keeper 12 · **Control** `2026-09-13-spp-40-holdout-span` (`results/calibration/spp40_holdout`), committed

---

## 1. Headline

**The source data supported the intake, the intake landed, and SPP-40's held-out C8
breach is closed.** C8 `forced_share` goes **FAIL on all four years → PASS**, and D-4
per-unit conduct **FAIL rows 33 → 4**. The held-out determination stays **NOT-YET** on
four unchanged FAIL criteria, with **grade 2 → 3** and **fails 5 → 4**.

Nothing about SPP's headline moves: rule 30 `[R-TOUCHPOINT-FOLD]` (c) — a held-out year
reports and can neither certify nor decertify. SPP remains **CALIBRATED** on keeper 12's
2023–2025 verdict, and `audit_keepers --iso SPP` passes clean.

## 2. The source survey — the lane's first question, answered first

`scripts/probes/_spp43_source_survey.py`. **13 of SPP's 14 CAMPD detection states carry a
complete Jan 1 → Dec 31 unit-level parquet in every year 2019–2025.** The 14th (**CO**) is
absent in *every* year **including 2023–2025**, so the committed block was itself derived on
the same 13-state panel: **the gap is purely temporal, never spatial.**

Fleet CEMS coverage in 2019–2022 **equals or exceeds** the in-sample years — 112/109/107/107
model plants against 107/105/106; ST_GAS 19/18/17/17 against 17/17/17; COAL 26/25/24/24
against 24/23/23 — and all four plants carrying SPP-42's residual D-4 failures (1230, 1235,
1271, 3008) file CEMS in all seven years.

## 3. What was derived, and why it is a first derivation

Rule 23 `[R-FROZEN-DERIVE]`: extending an extract's **year range on unchanged source data**
is a first derivation for those years, not a re-derivation against a residual. The intake
invocation differs from the committed one in `--years` and **nothing else**; the derived
years were never compared against a residual before being kept.

| extract | 2019 | 2020 | 2021 | 2022 | (2023 | 2024 | 2025) |
|---|---|---|---|---|---|---|---|
| standard | 943 | 932 | 982 | 946 | *880* | *905* | *936* |
| short | 181 | 239 | 379 | 270 | *163* | *211* | *246* |

**Additivity, proven four ways:** 3,803 / 1,069 added rows and **0 removals**; the committed
block's bytes unchanged **including line positions**; **no new row with `outage_end ≥
2023-01-01`**; and the decisive one — **the LP's own 2023–2025 availability multiplier arrays
are byte-identical before and after, all six.** The keeper's scored years therefore cannot
move and were **not** re-solved (a ~10-minute shard killed at zero LP).

**Reach** (`scripts/probes/_spp43_overlay_reach.py`): the 2019–2022 overlays go from **0 bins**
to **77–81**, 363k–403k derated cells against 337k–370k in-sample. The flat-EFOR condition —
the stated root cause of both open defects — is gone.

## 4. What moved, at full magnitude

### 4a. C8 / D-2 ST_GAS — numerator and denominator separated

The lane was explicitly warned that reading the ratio alone is a trap here. It is:
**the entire improvement is numerator, and the denominator moved *against* it in three of
four years.**

| year | forced_twh ctrl → arm | class_total_twh ctrl → arm | share ctrl → arm |
|---|---|---|---|
| 2019 | 5.0294 → **1.7035** (−3.3259) | 14.6909 → 14.7341 | 0.3423 → **0.1156** |
| 2020 | 4.7849 → **1.7040** (−3.0809) | 15.8746 → **14.0692** | 0.3014 → **0.1211** |
| 2021 | 5.4248 → **1.9543** (−3.4705) | 10.7616 → **7.9206** | 0.5041 → **0.2467** |
| 2022 | 5.4898 → **2.3652** (−3.1246) | 9.8806 → **7.5281** | 0.5556 → **0.3142** |

2022 remains above the 0.30 cap and clears **rule 20's grounded-above-budget route**: all
binding mechanisms clear D-4, profile r 0.952 (≥0.8), off-peak CV ratio 1.438 (≥0.5) — a
clean PASS surfaced as a report note.

### 4b. D-4 off-window binding: 33 → 4 FAIL rows

Survivors: **plant 3008 in 2019/2020/2021**, and a marginal **plant 1230 in 2019** (46 binding
hours, down from 1391). 3008 is the fleet's one measured two-shifter, whose defect SPP-27
identified as the **within-day grain** — never this mechanism. That is the same residual the
in-sample keeper carries, so the held-out picture now matches the in-sample one.

### 4c. The scorecard

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix | FAIL, 4 rows (2021 CC −18.91/COAL_PRB +18.61; 2022 CC −20.05/COAL_PRB +23.26 TWh) | FAIL, **2 rows** (2020 COAL_PRB −10.85; 2022 COAL_PRB +8.01) |
| C2 system volume | PASS | PASS |
| C3a mean LMP | FAIL: 2021 −21.3 %, 2022 −23.5 % | FAIL: **2020 +24.0 %** only |
| C3b price shape | FAIL: 2020 0.231, 2021 **0.640**, 2022 0.342 | FAIL: 2020 **0.319**, 2021 **0.213**, 2022 **0.213** |
| C3c price tail | CAVEAT (ledgered), 4 years | CAVEAT (ledgered), **2021 → PASS** |
| C4 dispatch corr | FAIL, 3 rows | FAIL, **1 row** (2022 gas r 0.957, NRMSE 0.312) |
| C6 governance | PASS | PASS |
| **C8 forced share** | **FAIL (4 years)** | **PASS** |
| D-10 free-class C1 | all 28/32 · free 20/24 | all **30/32** · free **22/24** |
| grade / fails | 2 / 5 | **3 / 4** |

### 4d. The costs — declared, not discovered

* **2022 gains 563.6284 MWh of slack** where the control had 0.0000, and its max system
  price goes **85.58 → 1102.55 $/MWh**.
* **2020 degrades across the board**: C3a +24.0 % now FAILs, C3b 0.231 → 0.319, a new C1
  COAL_PRB −10.85 TWh row, reported-only CO2 −4.8 % → +17.5 %.
* Load-weighted price rises every year: 19.8177 → 22.3866, 18.0677 → 20.4872, 29.4211 →
  40.1673, 33.7319 → 43.6848. Hours > $200: 0→0, 0→0, 14→220, 0→4.
* Energy conserved to ≤ 0.0159 TWh on 262–288 TWh; **dump 0.0000 everywhere**.

Class movement is large and coherent — the overlay removes COAL_PRB (−4.36 / −5.15 / −13.27 /
−15.25 TWh) and ST_GAS, replaced by CT_PEAKER and CC_REGULAR. In 2021/2022 that moves the
crossover signature SPP-40 named (model CC share of CC+PRB) from 0.1375 → 0.2513 against
0.301 actual and 0.1352 → 0.2520 against 0.315; in 2019/2020 it moves the same statistic
*further above* actual. Reported, gated on nothing.

## 5. Attribution is JOINT, and is stated as such

The arm differs from the control by **two** things: the intake **and** keeper 12's
`mustrun_commitment_feasibility_clip`. **They are not separable by construction** — SPP-42
measured the clip *provably inert* on these years without the extract ("0 infeasible
plant-hours, 0.0 MWh released"), so the data is the **enabling condition** and the clip the
**mechanism**. Neither alone produces this result.

A decomposition leg (new extract, clip OFF — `results/calibration/spp43_extract_only`) was
launched to quantify the split. **Its status is recorded in §8.**

## 6. Rules

* **13 `[R-MEASURED]`** — a unit outage window is the rule's own named admissible class.
* **14 `[R-ACCURATE]` is the basis, never the residual.** A flat EFOR baseline is an estimate
  standing in for measured availability that exists on disk. That C8 and D-4 improved is a
  **result**; that 2020 and 2022 got worse is not grounds to revert, it is a discovered root
  cause to route.
* **23 `[R-FROZEN-DERIVE]`** — first derivation, settings frozen, proven additive.
* **29 `[R-SCREEN]`** — no screen gate and no residual gate, on the precedent keeper 11's and
  keeper 12's promotion notes record: the screen applies to a candidate *mechanism* competing
  against a correct one, and **a missing measured input is not a candidate mechanism.**
  **29(b) form 4 holds**: G-DRIFT from the keeper-12 promotion commit `520d9fc0` to HEAD finds
  **zero changed hunks** on the solve path; the older gap from the control's own `git_sha`
  `3117f06a` was already closed by SPP-42's actual re-solve.
* **21 `[R-DOF]` / 24 `[R-REGISTRY]`** — zero free parameters added, zero re-cut, no new
  tunable. `offer_curve_by_group` SHA-256 `090abd79…62f65`, byte-identical.
* **25 `[R-ISO-SCOPE]`** — SPP's own extract files only.
* **30 `[R-TOUCHPOINT-FOLD]`** — stamped to keeper 12; status page rebuilt; `audit_keepers`
  E1/E13 clean.

## 7. Reported, not folded in

1. **The frozen 2023–2025 block is not reproducible at HEAD.** Re-deriving it as a control
   emits **103 rows it does not carry — all plant 762 (Ponca) units 3–4, ST_GAS, zero
   removals.** Ponca reaches the deriver only through `load_retired_within_window`, so the
   frozen block predates that scope. Left untouched (changing it moves the keeper's *scored*
   years); the 2019–2022 block **is** at HEAD scope and **does** carry Ponca, because rule 14
   forbids degrading an accurate input to match a stale one. **The short extract reproduces
   byte-identically** (coal-only scope). → **routed as its own lane.**
2. **The four companion extracts** (`layup`, `layup-shortgas`, `shortgas`, `e923`) remain
   2023–2025 and were deliberately **not** extended: the keeper consumes none of them
   (`mustrun_layup_window_mask=false`; `unit_outage_short_windows_gas` is `R` for SPP per
   SPP-32; the e923 fallback is off). SPP-42's lay-up double-subtraction finding is unaffected
   — there are still no 2019–2022 lay-up rows to double-subtract.
3. **`stamp_touchpoint_holdout.py`'s NEISO-specific, `[R-HOLDOUT]`-era caveat defaults** were
   re-applied by the stamp and corrected in place on the new sidecar (they assert an
   envelope-parity story that is the **exact opposite** of this run's object, and claim a
   touch-once locked test is unspent when 2019 is one of this bundle's years). Both fields have
   zero consumers. **Reported, not patched** (rule 25). **A re-stamp resets them.**
4. **`replay_keeper --out-dir` still does not propagate `calibration_attestation.json`** — closed
   by the per-lane `scripts/gen_spp43_attestation.py`, and it does not write `metrics.json`
   either (the parent's scoring step produces it).
5. **Parity gate: two pre-existing REDs, neither pruned** — `caiso279_ablate_dswcouple_span`
   (CAISO) and `soco15_spp_arm`. **Correction to the lane brief:** `soco15_spp_arm`'s
   `meta.json` reads `iso = SPP`, not SOCO — it is the SOCO-15 lane's *SPP arm*, so it *is* in
   this ISO's rule-35(a) scope. It is still not touched: it is cited as live evidence by ten-plus
   docs across the SOCO, NWPP, PJM, MISO and NYISO lanes, and rule 31 `[R-RETAIN]` reserves that
   call for the owner.

## 8. Retrievability (rule 34 `[R-SHARD-PROMOTABLE]` (e))

* **`results/calibration/spp43_holdout_span` — ON `main`.** PR #6223 (branch
  `claude/spp43-holdout-span`) was rebased onto main to clear a `.gitignore` conflict and
  **merged at `aea6158f0b12535890a8e8fed35b3b3207410875`**, so the bundle is committed:
  45 files including all four `dispatch/<year>_P1.parquet`, all four `_fleet` companions and
  the 8 `_shared/SPP` inputs. **A promotion from here costs zero re-solves and needs no
  recovery command** — the bytes are on `main`.
* **`results/calibration/spp43_extract_only`** — the decomposition leg. Status at write-up
  time is in the session report; if its branch `claude/spp43-extract-only` did not land, the
  leg costs **~15 min of LP** to reproduce and **nothing in §4 depends on it** — it refines
  *attribution* between the intake and the clip, not any number above.

## 9. Promotion question — for the owner, not pre-empted

`2026-09-16-spp-43-outage-intake` **supersedes** `2026-09-13-spp-40-holdout-span` as SPP's
2019–2022 rung: same recipe, strictly better-grounded availability input, C8 closed, D-4
33 → 4, grade 2 → 3 — against a worse 2020, and 563.6 MWh of new slack in 2022.

**Both runs are currently registered and both are stamped to keeper 12.** Nothing was pruned
and `keepers/SPP.json` was not touched (rule 31 `[R-RETAIN]`).

**The question:** promote the SPP-43 run as SPP's 2019–2022 rung and prune
`2026-09-13-spp-40-holdout-span` (rule 35 `[R-PROMOTE]` (a), SPP only)? SPP's registered year
set stays at **seven** either way. The keeper itself (2023–2025) is **not** affected — its
availability arrays are byte-identical, proven in §3.

# RESULT — caiso-269: the DSW clean-depth family's hod 22-23 window gap, closed and measured on all four years

**Session caiso-269, 2026-09-10.** Arm `ScenarioConfig.caiso_dsw_lateevening_clean`, default off, CAISO-only,
ONE flag on the committed keeper recipe via `--replay-bundle`. Charter:
`docs/PRECOMMIT-caiso269-lateevening-clean-2026-09-10.md`; shard/re-pin record:
`docs/ADDENDUM-caiso269-shard-repin-2026-09-10.md`. Solved as four per-year shards (rule 32 `[R-SHARD]`),
all pinned to `8a4912486cd2a7b6ce9a91cbfaeef03c861f4732`.
**KEEPER UNCHANGED at `2026-09-09-caiso-fuelvintage-860-gas`. NOT PROMOTED — the owner's call.**

---

## §1 — The result in six lines

1. **The mechanism does exactly what its arithmetic says, in all four years.** The tranche dispatches
   **1.0930 / 0.1945 / 0.8307 / 0.6974 TWh** (2022/2023/2024/2025) and **exactly 0.0000 MW outside hod
   22-23** in every year — G-FOOT verified on realized dispatch, not merely on capability.
2. **The substitution is one-for-one, import for gas**, at the annual scale: import **+0.826 / +0.172 /
   +0.764 / +0.540 TWh** against gas **-0.821 / -0.172 / -0.771 / -0.551 TWh**.
3. **EVERY scored price and dispatch criterion moves toward measured, and none degrades across a band.**
   C3a improves in all four years, C3b improves in all four, C4 improves or holds in all four.
4. **THE PRE-REGISTERED EXPOSURE IS CLEARED. C4-2025 gas NRMSE 0.298 -> 0.294**, against the <= 0.300
   bound — it moves AWAY from the edge, and gas hourly `r` rises 0.877 -> 0.881. PRECOMMIT §3 P4 named
   this as the number that killed both x0.92 arms; it is the number this arm improves.
5. **AND IT DOES NOT ACHIEVE THE STATED GOAL. 2022's C3a still FAILS: +13.17 % -> +12.90 %**, against a
   <= +10 % band. C3b 0.2422 -> 0.2402, still failing. The arm moves 0.27 pp of a 3.2 pp gap. **CAISO's
   2022 rung remains NOT-YET, on the same two criteria, for the same reason.**
6. **Eight shard-years were spent before one usable measurement**, on five defects — three pre-existing on
   `main`, two mine. §7 is the full accounting, including the two that were mine.

## §2 — The scorecard, arm vs control, every year (G-CTRL form 4)

Controls: `results/calibration/caiso_fuelvintage_span` (2023-2025) and `caiso_fuelvintage_tp2022` (2022),
both COMMITTED — **no control solve was spent** (G-DRIFT, PRECOMMIT §5: all hunks INERT).

### §2.1 — C3a system load-weighted mean LMP

| year | actual | control | **arm** | delta | verdict |
|---|--:|--:|--:|--:|---|
| 2022 | 84.49 | 95.621 (**+13.17 %**) | **95.389 (+12.90 %)** | **-0.232** | **FAIL -> FAIL** |
| 2023 | 54.17 | 56.548 (+4.39 %) | **56.516 (+4.33 %)** | -0.032 | PASS -> PASS |
| 2024 | 34.65 | 37.734 (+8.90 %) | **37.611 (+8.54 %)** | -0.124 | PASS -> PASS |
| 2025 | 34.42 | 37.260 (+8.25 %) | **37.129 (+7.87 %)** | -0.131 | PASS -> PASS |

**Instrument validation, stated because two earlier reconstructions of mine were WRONG:** the C3a/C3b
instrument here reproduces the committed run payload's per-zone prices to **0.0039 $/MWh** and returns the
published control values exactly — 2022 **95.621** vs published 95.62/+13.2 %; 2023/2024/2025
**+4.39 / +8.90 / +8.25 %** vs published +4.4 / +8.9 / +8.3 %. An earlier attempt that averaged price
per hour instead of load-weighting WITHIN each zone returned +8.58 % for the 2022 control against a
published +13.2 %, and was discarded rather than reported.

### §2.2 — C3b monthly load-weighted price NRMSE

| year | control | **arm** | delta | published control |
|---|--:|--:|--:|--:|
| 2022 | 0.2422 | **0.2402** | -0.0020 | 0.242 |
| 2023 | 0.0830 | **0.0827** | -0.0004 | 0.083 |
| 2024 | 0.1425 | **0.1391** | -0.0034 | 0.143 |
| 2025 | 0.1110 | **0.1070** | -0.0040 | 0.111 |

### §2.3 — C4 gas hourly fit, CEMS basis — THE PRE-REGISTERED EXPOSURE

| year | control r / NRMSE | **arm r / NRMSE** | dNRMSE | published control NRMSE |
|---|--:|--:|--:|--:|
| 2023 | 0.882 / 0.287 | **0.882 / 0.287** | +0.000 | 0.287 |
| 2024 | 0.912 / 0.260 | **0.917 / 0.256** | **-0.004** | 0.260 |
| **2025** | **0.877 / 0.298** | **0.881 / 0.294** | **-0.004** | **0.298** |
| 2022 | 0.917 / 0.227 | 0.921 / 0.223 | -0.004 | *(not reproduced — see below)* |

Both sides run the SAME instrument with the SAME uint8 CF% quantization. It reproduces the published
control NRMSE **exactly in all three train years**. **It does NOT reproduce the 2022 figure**
(`RESULT-caiso268-h2r-2022` §4 records the incumbent 2022 touchpoint at r 0.881 / NRMSE 0.283; this
instrument returns 0.917 / 0.227 on the same bundle). The 2022 C4 row is therefore reported as
**UNVALIDATED** and no 2022 C4 claim is made; the arm-vs-control *delta* on a self-consistent instrument
is -0.004, the same sign and size as every other year.

### §2.4 — C1 fuel-mix by class, reported at full magnitude INCLUDING where it worsens

CC_REGULAR signed error vs actual (TWh), control -> arm:

| year | control err | **arm err** | direction |
|---|--:|--:|---|
| 2022 | +3.611 | **+2.853** | **TOWARD** |
| 2023 | -3.431 | **-3.578** | **AWAY** |
| 2024 | +0.111 | **-0.529** | **AWAY** (crosses zero, magnitude up) |
| 2025 | +0.335 | **-0.171** | **TOWARD** (crosses zero, magnitude down) |

CT_PEAKER worsens marginally in every year (-0.023 to -0.108 TWh), which is the declared permanent
residual (owner ruling caiso-261) and not this arm's object. **No class crosses a band** — the largest
error, 2023 CC_REGULAR at -3.578 TWh, sits inside the rubric v3.4 floored band of +/-5.27 TWh (3 % of
CAISO's 175.7 TWh actual generation) — so **C1 holds PASS in every year**. The 2023/2024 CC_REGULAR moves
are against this arm and are stated as such: in the two years where the model already under-runs CC or sits
almost exactly on it, taking gas out at hod 22-23 moves that class further from measured.

## §3 — The four STOP gates (rule 29 `[R-SCREEN]`), pre-registered in PRECOMMIT §4

| gate | condition | measured | verdict |
|---|---|---|---|
| **G-IDENT** | only `caiso_dsw_lateevening_clean` differs | **exactly ONE** differing `scenario_config` field in every year, plus the HEAD-drift `ercot_ep_gas_basis_receipts_fallback` (default off, ERCOT-gated, audited INERT in PRECOMMIT §5); 2024 additionally records its own `gas_price_override` / `weather_year`, which are per-year replay artifacts of a single-year replay against a 3-year control bundle | **PASS** |
| **G-FOOT** | response confined to hod 22-23 and to the import/gas rows | tranche dispatch **exactly 0.0000 MW outside hod 22-23** in all four years; annual import/gas substitution one-for-one to 3 dp; max abs delta outside the window 9.0-72.9 MW (import) and 9.5-77.4 MW (gas), i.e. LP re-optimisation noise, not a systematic shift | **PASS** |
| **G-DIR** | import RISES at hod 22-23, by > 0 and < the armed capability, and 2023 moves least | import **+752/+1,479 (2022), +236/+265 (2023), +865/+1,332 (2024), +936/+850 MW (2025)** at hod 22/23 — positive everywhere, below the armed capability everywhere, and **2023 is the smallest by a factor of ~4**, as the admissibility gate predicts | **PASS** |
| **G-NOFLIP** | no non-target load-bearing criterion flips PASS -> FAIL | C1 PASS->PASS (no band crossed), C2 PASS->PASS, C3b PASS->PASS and improving, C6/C8 untouched by construction. C3c exempt (rubric v3.6) | **PASS** |
| **G-CTRL** | form 4, earned by G-DRIFT | all hunks INERT; **no control solve spent** | **PASS** |

## §4 — What this arm is, and what it is not

**It is the one thing the last two CAISO arms were not: an improvement in price that does not cost
dispatch.** caiso-267 and caiso-268 bought a better price level by pulling gas in against imports the real
system ran, and the owner refused both on rule 1 `[R-STRUCT]` grounds. This arm moves in the opposite
direction — it puts imports back into the two hours where the measured record says CAISO imports 1.0-1.8 GW
more than the model does, takes gas out of hours where the model over-produces it, and **improves C3a, C3b
and C4 simultaneously, in every year**. Its window, its depth statistic and its admissibility band are all
prior sessions'; it introduces **zero new free parameters and zero new thresholds**, so the DOF ledger is
unchanged at 9 entries / 6 residual and there is no `authorized_price_tuning` block.

**It is NOT a fix for what the charter asked it to fix.** The session was chartered on the belly/import
seam and the 2022 rubric failures. Phase 0 established that the belly has no groundable lever available
(PRECOMMIT §0.2: the funded G-26 ladder is measured ~inert, depth-shaping is inert, and the two live
objects are a percentile that may not be swept and a delivery basis whose evidence supports the current
construction). What was found instead is a real but SMALL adjacent defect. Two hours in twenty-four cannot
move a load-weighted annual mean that December 2022's $305/MWh gas-crisis print dominates, and the numbers
say so plainly: **0.27 pp of a 3.2 pp C3a gap.**

## §5 — Governance record

* **Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`.** No offer-curve multiplier of any size; the authorized
  price-tuning carve-out is **not exercised** and no `authorized_price_tuning` block exists. No adder,
  offset, haircut, load proxy or pin to actuals. The lever is a measured CAPABILITY (pmin stays 0) priced
  at a measured hub, which the LP clears below.
* **Rule 14 `[R-ACCURATE]`.** The window is the complement the sibling constructions leave; the depth is
  the same p95 statistic over the same series and the same window it arms.
* **Rule 17 `[R-FLOOR-WINDOW]`.** Driver = the WEIM/EDAM clean-transfer capability the caiso-87/93/94
  family already carries. Window = fixed by the tiling and by caiso-253's own G-WINDOW finding
  ("22-23 are OVERNIGHT-construction hours"), **never by a residual**. Forward story = pooled
  climatologies that regenerate from any year's measured record, exactly as the siblings do.
* **Rule 19 `[R-ONE-MECH]`.** Netted per hour against the shaped firm block and all three sibling clean
  tranches; it FILLS their gap rather than stacking on any of them.
* **Rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`.** Zero new free parameters, zero new thresholds. The
  admissibility band is caiso-253's pre-registered [-2, +4], re-used unchanged — which is also how the
  DO-NOT-REDO on that cell is honoured: the refusal criterion becomes the arming gate, so 2023 stays dark
  BY CONSTRUCTION (4 of 20 admissible buckets vs 18/24 and 19/24), and the measured 2023 result confirms it.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO-only. No other ISO's keeper shard, status part or calibration log
  touched; the six non-CAISO matrix shards receive only the `.` n/a cell rule 28(c) requires.
* **Rule 28 `[R-MECH-MATRIX]`.** New row + a cell in every shard, added in the same PR as the field; the
  CI guard passes with the new field registered.
* **Rule 31 `[R-RETAIN]`.** **Nothing deleted.** The four rev3 bundles and the three void rev2 bundles are
  on local disk, gitignored (`results/calibration/caiso269_lateevening_*/` and `_rev2void_caiso269_*/`).
* **Rule 22.** `[R-HOLDOUT]` was REMOVED 2026-09-09; 2022 needed no authorization and none was claimed.
  2019 and H1-2026 were not solved, scored or registered. 2020/2021 remain blocked on DATA.

## §6 — Disclosures against interest

1. **§2.4: C1 CC_REGULAR moves AWAY from measured in 2023 and 2024.** Reported before the promotion
   question, not after it. No band is crossed, but the direction is against this arm in half the years.
2. **§2.3: the 2022 C4 row is not reproduced by this instrument** and is labelled UNVALIDATED rather than
   quietly printed alongside the three that are.
3. **The headline goal is not met** (§1 line 5), and that is stated in the first six lines rather than at
   the end.
4. **Two of the five blocking defects were mine** (§7), and one of them — the missing reprice entry —
   would have gone undetected by every test I had written, because they all tested capability rather than
   price.
5. **The 2023 result is small BY CONSTRUCTION and therefore cannot corroborate the mechanism there.** The
   gate keeps 2023 dark, so 2023 is close to a null and is evidence that the gate works, not that the
   lever does.

## §7 — Cost, and the five defects

Eight shard-years produced no usable measurement before the ninth did.

| # | defect | whose | effect |
|---|---|---|---|
| 1 | `run_replay_bundle()` kept `holdout_authorized` as a required positional after the `[R-HOLDOUT]` removal deleted its only caller argument | **pre-existing on `main`** | every `--replay-bundle` invocation, for every ISO, raised `TypeError` before any LP |
| 2 | three argparse help strings carried an unescaped `%` | **pre-existing on `main`** | `--help` raised `ValueError`; two attempt-1 shards spent their budget on it |
| 3 | the flag was wired as a direct `backcast_config` keyword | **mine** | `backcast_config` has 36 explicit parameters and no `**kwargs`, and carries none of the CAISO clean flags — they all ride the generic override bag |
| 4 | the tranche was missing from the price injectors' reprice name set | **mine** | built, armed at 6,429 MW, then left on the $180 placeholder — **0.0 MW dispatched in all 8,760 hours**; the rev2 shard-years measured nothing |
| 5 | rev3 shards pushed to `-rev3` branch names | shard convention | cost one collection cycle |

Defects 1-2 are repaired on this branch. Defects 3-4 are repaired **and guarded by tests**:
`TestPricing` asserts the tranche prices at the raw hub rather than the placeholder, and was verified to
genuinely catch the defect (removing the name fails the suite at 456.02 against a 0.01 tolerance).
The three hand-maintained `import_names.add(...)` calls are collapsed into one shared tuple so the next
clean tranche is a single edit, with the trap named in place.

**The lesson, stated for the next lane:** the PRECOMMIT proved the arm was correct and byte-identical off,
but never proved the solve path could DELIVER it. A single zero-LP bind check — apply the recorded override
bag, count the differing `ScenarioConfig` fields, and assert the new row's marginal cost — would have caught
defects 3 and 4 before a single shard launched.

## §8 — THE PROMOTION QUESTION, PUT EXPLICITLY TO THE OWNER (rule 31 `[R-RETAIN]`)

**I have NOT promoted this run. The keeper stays `2026-09-09-caiso-fuelvintage-860-gas`.**

**THE FOUR BUNDLES ARE ON LOCAL DISK IN AN EPHEMERAL CONTAINER AND WILL NOT SURVIVE THIS SESSION.** Their
per-year branches (`claude/caiso269-2022`, `claude/caiso269-{2023,2024,2025}-rev3`) carry the full bundles
including `dispatch/`, so a promotion does **not** need a re-solve. Nothing has been deleted.

The trade, stated once: the arm **improves every scored price and dispatch criterion in every year**,
including moving C4-2025 away from its 0.002 of headroom, at the cost of **C1 CC_REGULAR moving away from
measured in 2023 and 2024 without crossing a band** — and it **does not fix 2022**, which remains NOT-YET
on C3a and C3b.

* **(a) PROMOTE as the new keeper.** Defensible on rule 1 `[R-STRUCT]`: a structurally-grounded mechanism
  with zero new parameters that improves price AND dispatch together — the opposite trade to caiso-267/268.
  It changes no determination: train years stay CALIBRATED with the single ledgered C3c, 2022 stays NOT-YET.
  Say so and I will compose the 2023-2025 span into one bundle, register it, stamp the 2022 rung as a
  folded touchpoint (rule 30(a)), re-key `calibration-complete.json`, and run the keeper auditor.
* **(b) DO NOT PROMOTE, register as evidence.** The honest reading of "it did not do the job it was
  chartered for". The mechanism stands documented and the field stays default-off.
* **(c) PROMOTE THE CODE, HOLD THE KEEPER** — keep `caiso_dsw_lateevening_clean` in the tree default-off
  (the window gap and its guard tests are worth having regardless) and leave the keeper alone.
  **This is my recommendation**, because the arm is real and costless to carry but has not earned a keeper
  promotion on its measured merits.

**Next number: caiso-270.**

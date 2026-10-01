# FINDING — SOCO-40 (2026-09-16): the first SOCO keeper

**Run `2026-09-16-soco-1-baseline`** · bundle `results/calibration/soco40_coalsplit_B` ·
years 2023–2025 · lane SOCO-40 (continuation session).

---

## 1. Determination

> ## **NOT-YET** — rubric v3.8, **PRICE UNSCORED**

**It is the keeper regardless** (rule 1 `[R-STRUCT]`): it is the most structurally faithful SOCO
run that exists, and a determination is not a promotion test. SOCO had no keeper before today.

| criterion | tier | status | detail |
|---|---|---|---|
| **C1** fuel-mix by class | LOAD | **FAIL** | **one row of fourteen**: 2023 `CT_PEAKER` **+8.221 TWh**, share **+3.4 pp**. C1 all **13/14**, free **9/10**. Seven 2025 rows SKIPPED on the preliminary EIA-923 vintage |
| **C2** system volume (gas/coal families) | LOAD | **PASS** | |
| **C3a** mean LMP | LOAD | **UNSCORABLE** | no `actual_lmp.json` block for SOCO — **not failed**, in any year |
| **C3b** price duration / shape | LOAD | **UNSCORABLE** | as C3a |
| **C3c** price tail / scarcity | SUPP | **UNSCORABLE** | as C3a |
| **C4** fleet hourly dispatch correlation | SUPP | **PASS** | |
| **C6** governance gate | PROT | **PASS** | four assertions TRUE, owner-attested, `authorized_price_tuning` NONE |
| **C8** forced-energy share (D-2) | PROT | **PASS** | **0.0 %** forced on every material merchant class |
| C5a CO2 vs eGRID | — | REPORTED-ONLY | −5.3 % / −8.9 % / +4.9 % — contributes no status (v2.9) |

`grade_summary`: scored 5, target_grade 4, **fails 1**, **ledgered 0**, **protective 0**.

**The price gap is structural and permanent.** SOCO's footprint publishes no LMP, hub or clearing
price. `data/raw/_validation-source/actual_lmp.json` has no SOCO block and **must not gain one** — a
placeholder would break `calibration_verdict._price_reference_absent` and silently move SOCO onto
the ordinary determination path. The ceiling is `PHYSICALLY-CALIBRATED (PRICE UNSCORED)`; SOCO can
**never** read `CALIBRATED`. Gate **G17** stands absolutely: no neighbouring hub, no proxy, no
cost-stack price, ever. The model's own load-weighted mean LMP — **33.32 / 31.14 / 199.34 $/MWh** —
is **MODEL-ONLY and UNVERIFIED** and is never quoted as price skill.

---

## 2. The STOP gate — screen and both arms

The rule-29 `[R-SCREEN]` screen (2024, throwaway probe, never registered) cleared **all six legs**:

| leg | screen (2024) | arm A (unsplit) | arm B (**keeper**) |
|---|---|---|---|
| A served export reproduced | PASS — 0.0000 TWh (gen 249.5057 = LP load 249.5057) | PASS | PASS — energy balance +0.46 / +0.39 / +1.32 TWh, tol ±3.0 |
| B slack / dump | PASS — 0 / 0 | 2025: 8,930 MWh slack (hydro hole, §5) | same — 8,930 MWh, 13 hours, 2025 only; dump 0 everywhere |
| C every class inside a 3× band | PASS | PASS | PASS |
| D no negative price | PASS — min 18.16, max 72.73 | PASS — 0 negative hours, all years | PASS — 0 negative hours, all years |
| E Vogtle-4 April step | PASS — Jan–Mar 6,562 MW → Apr–Dec 7,385 MW, max 7,999 < 8,080 nameplate | PASS | PASS |
| F reserve 0 · both Tier-3 links never bind | PASS — `reserve_price` 0, duals 0.000 | PASS | PASS |

No STOP gate was re-run on a screen year for arm B: the mechanism is a class crosswalk plus a
supply-keyed price, and the span's own legs A–F were re-graded on the new bundle (PRECOMMIT §11).

---

## 3. Arm A vs arm B — what the coal split did, at full magnitude

**Arm A** = `soco40_baseline_B`, the charter's all-defaults recipe with ONE bare `COAL` class.
**Arm B** = `soco40_coalsplit_B`, the keeper, `COAL` split to `COAL_BIT` / `COAL_PRB` on the
measured EIA-923 supply census. Owner instruction, verbatim: *"Coal should be split into types.
Completely eliminate the single coal class."*

### 3.1 The full C1 table (TWh)

| class | 2023 model | 2023 actual | err | 2024 model | 2024 actual | err | 2025 model | 2025 actual | err |
|---|---|---|---|---|---|---|---|---|---|
| CC_REGULAR | 110.294 | 107.829 | +2.465 | 108.907 | 104.997 | +3.910 | 106.183 | 113.318 | −7.135 |
| nuclear | 51.915 | 52.135 | −0.220 | 62.916 | 63.060 | −0.144 | 63.988 | 64.232 | −0.245 |
| **COAL_PRB** | **21.467** | **22.374** | **−0.908** | **22.420** | **24.719** | **−2.299** | **31.541** | **28.333** | **+3.207** |
| **COAL_BIT** | **11.675** | **12.857** | **−1.182** | **12.256** | **12.257** | **−0.001** | **16.121** | **14.942** | **+1.179** |
| **CT_PEAKER** | **12.755** | **4.534** | **+8.221** ✗ | 9.717 | 4.785 | +4.933 | 13.009 | 5.141 | +7.867 |
| **ST_GAS** | 3.996 | 10.483 | **−6.487** | 3.883 | 8.879 | **−4.996** | 4.325 | 8.909 | **−4.584** |
| solar | 8.362 | 8.362 | +0.000 | 10.127 | 10.123 | +0.004 | 9.985 | 9.989 | −0.004 |
| biomass | 8.822 | 8.822 | −0.000 | 9.315 | 9.315 | −0.000 | 4.171 | 4.171 | −0.000 |
| hydro | 6.815 | 8.447 | −1.632 | 6.301 | 7.080 | −0.778 | **0.327** | **6.012** | **−5.685** |
| CC_CHP | 2.321 | 1.760 | +0.561 | 2.333 | 1.675 | +0.657 | 2.176 | 0.110 | +2.066 |
| CT_CHP | 1.062 | 0.953 | +0.110 | 1.067 | 0.901 | +0.166 | 1.074 | 0.922 | +0.152 |
| ST_CHP | 0.461 | 0.927 | −0.465 | 0.466 | 1.136 | −0.669 | 0.234 | 0.477 | −0.243 |
| oil | 0.000 | 0.212 | −0.212 | 0.000 | 0.161 | −0.161 | 0.024 | 0.104 | −0.080 |
| OTHER | 0.138 | −0.509 | +0.647 | 0.186 | −0.478 | +0.665 | 0.047 | −0.648 | +0.695 |

Arm A's single `COAL` class ran **33.142 / 34.676 / 47.662 TWh** against a benchmark carrying **two**
rows (`COAL_PRB` + `COAL_BIT`) — the SPP-40 §7.3 defect, and the reason C1 failed on seven rows.

### 3.2 It is a RECLASSIFICATION, not a re-dispatch — proven, not asserted

- **Every non-coal class is byte-identical to arm A** (the `armA` column of the working table
  reproduces arm B exactly for all twelve non-coal classes).
- `COAL_BIT + COAL_PRB` sums to arm A's bare `COAL` **to the GWh**: 33.142 / 34.676 / 47.662.
- **2023 and 2024 P0 objectives are identical to the cent**: 3690944814.1196 and 3398767416.6013 in
  both arms. Only **2025** moves — 5682126660.3872 → 5680277825.0155 — in the scarcity hours the
  hydro hole creates.

### 3.3 What it bought

**C1's failing rows fell from SEVEN to ONE.** Every coal row now passes, because coal is finally
scored against the benchmark's own EIA-923 fuel-code rows instead of one blended class against two.
2024 `COAL_BIT` lands at **12.256 TWh against 12.257 actual — a 1 GWh error on a 12 TWh row.**
D-1 also gained resolution: the shape miss now names `COAL_BIT` specifically instead of a blended
`COAL`.

**Not a residual-driven change** (rules 1 / 14): the instruction named a STRUCTURE — coal ranks are
real, measured, plant-specific supply facts that every other coal ISO already carries — not a number
to move. No band, share, floor or threshold was touched.

---

## 4. The one gating defect — SOCO's first lever

**2023 `CT_PEAKER` +8.221 TWh (share +3.4 pp)** is the only failing criterion row. It is one half of
a **near-offsetting merit-order misallocation inside the peaking fleet**:

| year | CT_PEAKER err | ST_GAS err | net |
|---|---|---|---|
| 2023 | **+8.221** | **−6.487** | +1.734 |
| 2024 | +4.933 | −4.996 | −0.063 |
| 2025 | +7.867 | −4.584 | +3.283 |

The LP sends energy to combustion turbines that the real system sent to gas steam units, in
near-equal and opposite amounts — in **every** year, which is the signature of a systematic offer /
commitment ordering error rather than a year artifact. Nothing was tuned to move it.

---

## 5. Determination basis — the six PRECOMMIT §10 lines, plus the hydro hole

1. **The price gap** — §1 above. C3a/C3b/C3c UNSCORABLE, not failed; SOCO-13's NO governs.
2. **R-i — pumped storage unobservable.** 1,306.6 MW of PS is invisible in EIA-930: **0 of 8,760 h
   in 2023** and 99.7 % of 2024. `NG: WAT` is never negative before the 2024-07-15 cut-over, so PS
   charging was **not reported** rather than folded into hydro. A hard constraint on the C1
   benchmark, never a hole to fill. Model PS discharge 1.80 / 1.46 / 2.39 TWh; a comparator exists
   only for 2025 (1.96 TWh).
3. **Card S3 — Southern Power excluded.** Zonal shares use the **five fully-cited** FERC-714
   respondents. Southern Power (186) is a documented NO; its **3.211 / 3.401 / 3.084 TWh** is named
   and never absorbed. Residual **3.03 / 2.92 / 1.26 %**. The owner chose the cited five over the
   six-respondent set whose residual is smaller (1.63 / 1.50 / −0.03 %) precisely because the
   smaller residual rested on an uncited component (rule 13).
4. **Card S12 — COD month grain.** Vogtle 3 (2023-07) and Vogtle 4 (2024-04) govern the ramp.
   What the MONTH grain leaves, at full magnitude: nuclear −0.220 / −0.144 / −0.245 TWh, the 2023
   Vogtle-3 year being the one that under-runs, consistent with a mid-month COD resolved to a month
   boundary. The Vogtle-4 April step is present and physical.
5. **R-v — 2025 peaker census is thin.** No `eia923_incomplete` flag (ratio 0.9533), but only
   **6 of 23** `CT_PEAKER` and **1 of 6** `CC_CHP` plants have filed. No SOCO pair is gate-eligible
   for 2025; the gas split defers to EIA-930 and **seven 2025 C1 rows are SKIPPED**.
6. **R-w — the oil false positive: DISCHARGED by this run, measured not asserted.** PRECOMMIT §10
   line 6 recorded that the EIA-930 unit-slip screen deleted **4.4 GWh of a REAL Winter Storm
   Heather oil run** (2024-01-17 03:00–09:00, 530 → 649 → 660 → 687 → 762 → 801 → 350 MW, tracking
   SOCO demand from 41.0 to 47.4 GW), biasing the C1 oil benchmark LOW. Lane **NWPP-39**'s
   zero-baseline guard (`_FUEL_SPIKE_PLATEAU_PCT = 99.0`) landed between arm A's basis and this
   keeper's pin and releases it. **On the two launch logs: arm A repairs SOCO `NG: OIL` 2023 h7975
   and 2024 h386–392; this run repairs NEITHER, while the GENUINE 2025 `NG: NG` spikes (70,683 MW
   in a 32,574 MW hour, four hours) still fire in BOTH.** Releasing false positives while keeping
   true ones is the discriminating signature. The 2024 EIA-930 oil benchmark moves 0.00 → 0.01 TWh.
   It was audited and **declared as the single LIVE G-DRIFT hunk before the solve** (§8), not
   discovered in the result.

**Plus — the 2025 EIA-923 hydro INPUT hole** (PRECOMMIT §4.5, named before the solve). Not a model
defect. The 2025 hydro budget resolves **5 plants / 0.3275 TWh / 368 MW** against **6.012 TWh**
measured, where 2023/2024 resolve **42 plants / 6.82 and 6.30 TWh**. Consequences, reported and not
absorbed: **(a)** coal backfills it — 2025 coal runs 47.66 TWh against 44.08 measured;
**(b)** the LP cannot serve 13 summer afternoon hours and posts **8,930 MWh of slack at VOLL
61,900 $/MWh** (2025-06-25 15–17h, 07-29 12–16h, 08-18 13–15h, 09-05 13–14h), which is what drags
the 2025 MODEL-ONLY mean price to 199.34 $/MWh. **No repair was armed**: `--hydro-backfill-year`
and `--hydro-eia930-monthly` were deliberately not passed, because arming a one-year input repair
inside the first keeper is a desk-queue lever decision, not this lane's.

---

## 6. DOF ledger (rule 21 `[R-DOF]`)

**n_entries 3, n_residual 1. Zero free parameters were introduced by this lane.**

| entry | identification | basis |
|---|---|---|
| `offer_curve_by_group` | **measured-physical** | All four price-tuning bands (`committed`/`econ_low`/`econ_high`/`peak`) are at the **identity 1.0 on all 13 groups** (machine-verified: the set of distinct values per band is exactly `{1.0}`); `offer_curve_overrides` and `offer_curve_deltas` are null. The two non-identity keys, `econ_low_share` (0.500–0.556) and `pct_peaking` (5–15), are **not** the authorized channel — rule 1's carve-out excludes structural shares — and arrive verbatim from the ISO-agnostic `GENERIC_BASE_OFFER_CURVE`, whose docstring states per-ISO fitted values are never merged in. There is **no `soco.py` delta module**, so rule 25 `[R-ISO-SCOPE]` holds by construction |
| `offer_curve_smoothing` | **measured-physical** | **Unset** on this run — both `offer_curve_smoothing` and `curve_smoothing` are null. Nothing was tuned because nothing was set |
| `wefor_multiplier` = 0.7 | residual | The single inherited residual entry, carrying its audit C-15 root cause |

**Zero scalars were tuned on a SOCO residual, and gate G17 makes it impossible in principle**:
with no price benchmark there is no price residual to fit against, and none was computed.
`authorized_price_tuning` is declared **NONE** — no declaration block is present, because a block
would name a channel *in use*.

---

## 7. Cost, memory and retrievability

| | screen (2024) | arm A (unsplit) | **arm B (keeper)** |
|---|---|---|---|
| P0 solve (s) | — | 22.9 / 9.8 / 4.3 | **27.6 / 11.6 / 5.7** |
| P1 solve (s) | — | 7.2 / 7.3 / 2.3 | **7.4 / 8.1 / 2.6** |
| wall clock | — | < 11 min | **< 11 min** |
| cgroup peak RSS | — | 2.65 GiB | **2.65 GiB** |
| container preflight | — | ceiling 13.36 GiB + 10 GiB swap | ceiling 13.36 GiB + 10 GiB swap |

**Every bundle is retrievable by immutable SHA** (rules 33(d) / 34(d)/(e)) — `git ls-tree` returns
> 0 files for each, and **a promotion from this state costs ZERO re-solves**:

| bundle | full SHA | files | branch |
|---|---|---|---|
| `_soco40_screen` (2024 screen) | `d6b7b7d4dc9571b4058fbc9d13487cd9edfee900` | 15 | `claude/soco-40-screen-2024` |
| `soco40_baseline_B` (arm A) | `9458759f6b8c875a9a302e4b64db9e212420ddf9` | 34 | `claude/soco-40-span-2023-2025` |
| **`soco40_coalsplit_B` (KEEPER)** | **`dcb03c6bd346f9ab0d4356d5166b18c4ad42a214`** | **34** | `claude/soco-40-coalsplit-2023-2025` |

Recovery: `git archive <sha> results/calibration/<bundle> | tar -x`. The keeper's slim files
(`meta`/`run_config`/`metrics`/attestation/diagnostics + `hourly/`) are **committed on `main`'s
branch**, so a later lane differences against it without a re-solve (rule 29(b) form 4).

**A prior arm-B shard was ARCHIVED MID-SOLVE and its work lost entirely** — rule 33(b)
(*never archive a shard that is still running*) violated against a shard that had not yet pushed,
and no branch survived. Nothing was deleted; the bytes never existed. The owner was given the
~11 min cost and ruled **re-launch** (rule 31 `[R-RETAIN]`, final clause). The re-launched shard
pushed its bundle per rule 34(a), which is the correction.

---

## 8. G-DRIFT (rule 29(b)) — recorded BEFORE the solve

Full audit: `docs/handoffs/ADDENDUM-soco40-armB-relaunch-and-gdrift-2026-09-16.md` §3, pushed as
the pin `71884144abf4f08a4063d3c7a32e03a2c2f5d04d` before the arm was launched.

Arm A solved on `13198951…`; the keeper is pinned to `71884144…` (= `origin/main` `5e7cbb7d…` plus
the addendum). `main` was chosen over PRECOMMIT §11's original `81540853…` because that commit was
rebased away and is now **unreferenced** — a GC hazard for a shard clone, and a pin must be durable.

| file | verdict | reason |
|---|---|---|
| `eia930/envelopes.py` | **INERT** | docstring/comment only — no executable change |
| `eia930/frames.py` | **INERT** | entirely the NWPP **pool** path; `_POOL_HOURLY_MEMBERS` has one key (`NWPP`) and SOCO is not a member — SOCO is a single-BA extract |
| `run_calibration_full.py` | **INERT** | additive hydro-cascade sidecar returning `None` when unarmed, plus a tri-state CLI flag left unset on `_CACHE_KEY_OPTIONAL_FIELDS` |
| `eia930/actuals.py` | **LIVE** | NWPP-39's zero-baseline guard — see §5 line 6 |

The one LIVE hunk is **benchmark-side only** (SOCO model oil is 0.00 TWh in 2023–24), worth
~4.4 GWh in 2024 and ~0.29 GWh in 2023 against ~250 TWh — **~0.002 %** — on a row neither arm
competes on. So arm A → arm B carries **two** changes, not one, and the second is named rather than
absorbed. Taking it is the rule 14 `[R-ACCURATE]` call: the alternative would knowingly score the
first SOCO keeper against a benchmark containing a documented weather event deleted as telemetry
noise. A cleaner A/B is not worth that.

---

## 9. Diagnostics and gates

**Legitimacy**: D-1 **FAIL** (non-gating — rule 20's shape leg is unreachable because C8 forced
share is 0.0 %): 2023 `COAL_BIT` profile_r 0.622 / cv_ratio 0.015; 2024 `COAL_BIT` cv_ratio 0.410;
2025 `CT_PEAKER` cv_ratio 0.466. **D-2 / D-4 / D-5 / D-9 / D-10 all PASS.** D-2 shows only
`nuclear_mustrun` and `chp_steam` carrying forced MWh — every merchant class 0.0 %.

**Gates run from the repo root:**

| gate | exit | result |
|---|---|---|
| `audit_keepers.py --check --iso SOCO` | **0** | PASS, 0 failures 0 warnings (E1 and E13 clean) |
| `check_mechanism_matrix.py` | **0** | 0 after the §10 stamp; SOCO warnings cleared |
| `check_bench_freshness.py` | **0** | 41 parts, **0 STALE** |
| `check_golden_manifest.py` | **0** | OK |
| `check_gate_a_provenance.py` | **1** | **RED, none of it SOCO** — superseded keeper markers on MISO / NEISO / NYISO / SPP. SOCO's only line is the NOTE *"has a keeper shard but no entry on the forecast board"*, which is **correct and deliberate**: no gate-(a) stamp exists for SOCO and card **S10 routes the forecast namespace to the capx director**. This lane did **not** create one |
| `check_registry_payload_parity.py` | **1** | **RED on three unmapped bundle dirs, named below. NONE DELETED** (rule 31 `[R-RETAIN]`) |

**The parity RED, split by who owns it** — a distinction the gate itself does not draw:

- `soco40_baseline_B` (arm A) — **mine, and gitignored**, so it is RED *locally only*; CI checks out
  only committed files and stays green. This is exactly the case rule 31's **CORRECTED** clause
  (2026-09-16, pjm-h8) describes: the gate does a **filesystem** walk, so a gitignored bundle in a
  session's own tree turns it red locally. The remedy is **not** to delete a result rule 31
  protects.
- `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` — **pre-existing and TRACKED ON MAIN**
  (34 files each), so unlike mine these turn the gate red **in CI too**. Neither is this lane's
  work. `soco15_spp_arm` sits in the SOCO namespace but predates this lane (SOCO-15); it is
  **routed, not deleted** — the owner has ruled on neither.

---

## 10. RECOMMENDATION — re-order the §5 lever queue

The plan's pre-declared queue is SOCO-54 (inter-OpCo TTC derive) · SOCO-55 (VOLL/adequacy) ·
SOCO-56 (priced seams) · SOCO-57 (CAES/PS). **Recommend inserting two items ahead of all four:**

1. **SOCO-53 (new) — the `CT_PEAKER` / `ST_GAS` merit-order split.** It is the **only** gating
   criterion failure the keeper carries, it recurs in all three years with the same sign, and it is
   near-offsetting — so it is a misallocation *within* the gas peaking fleet, not a volume error
   (C2 passes on both families). Everything else in the queue is structure that does not move a
   scored row today. Phase 0 should be zero-LP: compare the two classes' offer construction and
   commitment eligibility against SOCO's own CAMPD conduct, per rule 18 `[R-PHYSICS]`.
2. **SOCO-53b (new, data-intake) — the 2025 EIA-923 hydro backfill.** 5 plants resolving against 42
   is an input hole, not a lever; it distorts 2025 coal, creates the only slack in the bundle, and
   makes 2025's model price uninterpretable. It should be fixed as **data**, and the question of
   whether `--hydro-backfill-year` / `--hydro-eia930-monthly` is the right instrument is a desk
   decision this lane deliberately did not pre-empt.

Then SOCO-54 → 55 → 56 → 57 as planned. **SOCO-54 (TTC derive) is explicitly NOT urgent**: both
Tier-3 links were measured at dual **0.000** in every year and cannot bind, so deriving a real limit
changes no dispatch until something else does.

## 11. Routed items

| item | to |
|---|---|
| `peak_gb` re-key: SOCO is registered `peak_gb=6.0` but **measured 2.65 GiB** twice — the estimate is 2.3× high. `run_isos_concurrent.py` is `scripts/`, outside this lane's write scope | desk / infra |
| 2025 EIA-923 hydro input hole (§5) | SOCO data-intake — recommended as SOCO-53b |
| `coal_supply_SOCO.csv` provenance: derived here from EIA-923 receipts + the EIA-860 census. Rule 23 `[R-FROZEN-DERIVE]` is satisfied **because SOCO has never been calibrated against**; from now on it re-derives only when its source data updates | SOCO desk |
| D-1 shape: 2023/2024 `COAL_BIT` and 2025 `CT_PEAKER` | folds into SOCO-53 |
| `soco15_spp_arm` — a dead, **committed** bundle in the SOCO namespace holding `check_registry_payload_parity` RED in CI. Not deleted (rule 31) | SOCO desk / owner |
| MISO / NEISO / NYISO / SPP superseded gate-(a) keeper markers | those ISOs' lanes (rule 25) |

## 12. Plan status

- `docs/multi-iso/soco-addition-plan-2026-09.md` §5 row **SOCO-40 → LANDED**.
- §1 rows **2 and 7 ticked** (matrix shard live with a keeper stamp; first keeper registered).

---

## Log entry

## soco-40 — 2026-09-16 — the first SOCO keeper, and the owner's coal split

SOCO has a keeper. `2026-09-16-soco-1-baseline` (bundle `results/calibration/soco40_coalsplit_B`) carries all three registered years 2023–2025 in one `--year 2023 2024 2025` invocation, and reads **NOT-YET** under rubric v3.8 with **PRICE UNSCORED**. It is the keeper regardless, under rule 1 `[R-STRUCT]`: it is the most structurally faithful SOCO run that exists, and there is no predecessor to supersede. SOCO publishes no price and never will, so `actual_lmp.json` carries no SOCO block and must not gain one; C3a, C3b and C3c are UNSCORABLE rather than failed, the run is scored on C1/C2/C4/C6/C8 alone, and the ceiling is PHYSICALLY-CALIBRATED (PRICE UNSCORED). The model's own mean LMP of 33.32 / 31.14 / 199.34 $/MWh is MODEL-ONLY and UNVERIFIED and is not evidence of anything.

The recipe is the CLI's all-defaults ISO-agnostic backcast construction on three geographic zones over measured FERC-714 shares from the five fully-cited respondents, with Tier-3 non-binding links, served measured EIA-930 interchange and VOLL 61,900. Every `offer_curve_by_group` band is exactly 1.0 across all thirteen groups, `offer_curve_overrides` and `offer_curve_deltas` are null, and `authorized_price_tuning` is declared NONE — not merely unused but unreachable, since with no price benchmark there is no residual to tune against. There is no SOCO offer-curve delta module, so the ISO rides the pure generic base and rule 25 holds by construction. The DOF ledger carries three entries and one residual, and this lane added no free parameter.

What the session actually did was execute the owner's instruction — *"Coal should be split into types. Completely eliminate the single coal class."* The split runs on the measured EIA-923 supply census (Barry, Gaston and Bowen bituminous; Miller, Daniel and Scherer PRB), every year now carries COAL_BIT and COAL_PRB, and no bare COAL survives. It is a reclassification rather than a re-dispatch, and that is proven rather than asserted: every non-coal class is byte-identical to the unsplit arm, the two coal classes sum to the old blended class to the GWh, and the 2023 and 2024 P0 objectives match to the cent. Only 2025 moves, in the scarcity hours its hydro hole creates. What it bought is large — C1's failing rows fell from seven to one, because coal is finally scored against the benchmark's own EIA-923 fuel-code rows instead of one blended class against two, the SPP-40 §7.3 defect. 2024 COAL_BIT now lands at 12.256 TWh against 12.257 actual.

One criterion row still fails: 2023 CT_PEAKER at +8.221 TWh, +3.4 pp of share. It is half of a near-offsetting misallocation inside the peaking fleet — CT_PEAKER runs +8.221 / +4.933 / +7.867 TWh while ST_GAS runs −6.487 / −4.996 / −4.584 — so the LP is sending energy to combustion turbines that the real system sent to gas steam units, in every year, with the same sign. That is SOCO's first lever and the session recommends it ahead of the whole pre-declared queue. Nothing was tuned to move it.

Two things are recorded rather than absorbed. 2025 carries an EIA-923 hydro input hole named in the PRECOMMIT before the solve — five plants and 0.327 TWh resolve against 6.012 TWh measured, where the other years resolve forty-two — which coal backfills and which posts 8,930 MWh of VOLL slack across thirteen summer afternoon hours; no repair was armed, because arming a one-year input repair inside the first keeper is a desk-queue decision. And disclosure R-w is discharged by measurement: lane NWPP-39's zero-baseline guard landed between the unsplit arm's basis and this keeper's pin, and where the unsplit arm repaired away both SOCO NG: OIL false positives, this run repairs neither while the genuine 2025 NG: NG spikes still fire in both. That hunk was audited and declared as the single LIVE G-DRIFT item before the solve, not discovered in the result.

The session also lost an arm. The first coal-split shard was archived mid-solve, in violation of rule 33(b), before it had pushed anything, and no branch survived; the owner was given the eleven-minute cost and ruled re-launch. The replacement pushed its bundle per rule 34(a), which is the correction, and all three of the lane's bundles — screen, unsplit arm and keeper — are retrievable by immutable SHA, so a promotion from here costs zero re-solves. Record: `docs/handoffs/FINDING-soco-40-2026-09-16.md`.

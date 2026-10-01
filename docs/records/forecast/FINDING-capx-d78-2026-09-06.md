# FINDING — capx D78: the sector-gate / clearing seam REPAIRED and measured EXACT — a sector-1 unit offers again, the 2022 stack, price and price-taking block return to the control's to the digit, the failing pool shrinks by exactly the 226 sector-1 rows and no merchant row changes state; the rule-29 screen's sign-line gate G6 FIRED on a timing shift the cap re-fill creates, so this lane does NOT spend the full window

**Lane:** capx D78 (director r#47; **owner ruling Q53 = READING 1**, capx ledger §3, 2026-09-06).
Design `DESIGN-capx-d78-sector-gate-offer-seam-2026-09-06.md`; pre-registration
`PRECOMMIT-capx-d78-sector-gate-offer-seam-2026-09-06.md`, **pushed at `34d78e91` before any code
and before any solve**; build at `fd0d01e1`; instruments `docs/handoffs/d78/`.
**Branch:** `claude/capx-d78-sector-gate-offer-seam-d1tfcd`, off `origin/main` `ba894c9c` (main did
not move during the session: re-fetched before leg 3, still `ba894c9c`).
**Date:** 2026-09-06. **Model:** Fable. **DATA PROFILE:** `pjm`.

**NOTHING ARMS.** No new field, no default flip, no `_pjm_config` override, no parameter value, no
keeper, no marker, no registration. **The seam repair lands as code** (the ruled reading, the
gate's own definition, byte-identical off-gate and on MISO); **the full 2021–2025 window was NOT
spent** (§4); the three screen bundles are **deleted before merge** (rule 29(c)). PJM's
`retirement_sector_gate` cell stays **`O`** with this evidence.

---

## 0. Verdict (one paragraph)

**The decoupling does exactly what its arithmetic says, to the digit.** On D58's own 2021–2023
screen span, solved three ways at HEAD, the repaired arm's 2022 capacity auction is the
control's auction: 1,370 offers, 150,857.2 MW offered, 30,577.9 MW of price takers, 67.760 $/MW-day
at position 1.048349, every one of the 1,370 stack rows byte-identical (§3 G1/G2) — the 370
gated units with accredited MW (34,172.4 MW) are back in the stack at their net-ACR caps. The 2022
failing pool is the control's 677 rows / 29,727.9 MW **minus exactly the 226 sector-1 rows /
3,476.5 MW** = 451 rows / 26,251.4 MW, the 451 shared rows identical to the decimal, and **zero
merchant rows change state** — D58's 41 arm-only merchant rows / 2,910.2 MW are gone (G3). Zero
sector-1 and zero unknown-sector pipeline rows anywhere (G4); every non-target 2022 footprint key
identical (G5). And G0 — D58's arm and control reproduced at HEAD to the digit on both legs —
confirms the PRECOMMIT §2 audit that every hunk since D58's solve HEAD is INERT and the key move is
D65-B's CCS re-key. **One pre-registered gate fired.** G6 asked that executed economic exits not
rise in either screen year; 2022's rose 7,333.7 → 8,736.7 MW. The ledgers show why, unit by unit
(§4): the failing pool shrank exactly as G3 says, but the admission cap **re-filled** the budget
the 226 sector-1 rows freed — from lag-3 sector-1 coal executing in 2024 (−1,225.8 MW) to 70 capped
merchant gas-steam / CHP rows with lag 1 executing in 2022 (+1,871.4 MW), the same rows the control
executes in 2023. Decided MW moved 13,177.5 → 13,354.7 (+1.3 %); the window cohort is the same and
its timing moved a year earlier. That is the cap re-fill the PRECOMMIT's own §5 item 3 predicted
(HIT: 13,354.7 MW, band 11.5–13.5 GW), so G6 was over-strong against its own sibling — **but a
fired STOP gate is honored** (rule 29; the D62 discipline: a lane does not promote past its own
pre-registration however right the diagnosis). This lane spends no more LP; §8 says what should.

---

## 1. What was solved

| leg | code (HEAD guard) | recipe | key (pre-declared → realized) | wall | order |
|---|---|---|---|---:|---|
| **control-P** | `34d78e91` (phase-0 commit; `src/` byte-identical to `ba894c9c`), pinned worktree | bare `pjm-t1h`, gate off | `afda79ba04cbfdbf` → **match** | 18.9 min | first, solo |
| **D58's arm, seam as built** | `34d78e91`, pinned worktree | `--retirement-sector-gate` | `d527c3299b8c00b5` → **match** | 15.6 min | second, solo |
| **repaired arm** | `9fcdf19c` (build + cross-refs + runners), main tree | `--retirement-sector-gate` | `d527c3299b8c00b5` → **match** (same key by design §3.4) | 14.1 min | third, solo |

All: `--iso PJM --start-year 2021 --end-year 2023 --vintage 2020 --fuel-variant realized
--entry-screen-diagnostics`. Solve years **{2021, 2023}**, 2022 **bridged** and never scored
(`meta.json` on every leg; `holdout_freeze_active_at_launch: true`); no out-of-training year
solved, scored or registered. Sequential, PJM solo (rule 12). HEAD guard held on every leg. LP:
2021 cold 464–531 s + warm 114–122 s, 2023 cold 145–157 s + warm 33–39 s; no `MemoryError`; peak
RSS was not captured (`/usr/bin/time` is absent on this box — STOP 8's RSS half is unmeasured and
said so; wall is inside the D57 envelope of 14 min per solve year). `data/clean` was absent at
session start and rebuilt in full (`regenerate_clean.py`, 56 datatypes, exit 0) before any leg.

**The code delta between the two solve commits (`34d78e91..9fcdf19c`, `src/`): four files.**
`retirements.py` (+106/−) — the `exit_exempt_unit_ids` parameter, its docstring, the partition
after the clearing, two docstrings; `evolve.py` (+29/−) — the one call site and its comment;
`scenarios.py` (23 lines) — comment-only; `cache.py` (+20) — the epoch prose. The control is
unaffected by it (gate off ⇒ the new set is empty; asserted by T1 and shown by G0's control half
being solved on the pre-fix code and matching D58). **K-a did not fire** on any leg.

---

## 2. G0 — D58 reproduced at HEAD to the digit (the audit's own test)

| quantity (2022 screen) | D58 control | **control-P at HEAD** | D58 arm | **D58's arm at HEAD** |
|---|---:|---:|---:|---:|
| failing rows / MW | 677 / 29,727.9 | **677 / 29,727.898** | 492 / 29,161.6 | **492 / 29,161.580** |
| `n_offers` | 1,370 | **1,370** | 1,000 | **1,000** |
| `offered_mw` | 150,857.2 | **150,857.184** | 116,684.8 | **116,684.829** |
| `price_takers_mw` | 30,577.9 | **30,577.888** | 64,750.2 | **64,750.243** |
| price $/MW-day | 67.760 | **67.760162** | 61.207 | **61.206645** |
| arm-only merchant rows / MW | — | — | 41 / 2,910.2 | **41 / 2,910.2** |
| economic exits 2022 / 2023 (MW) | 7,333.7 / 3,105.5 | **7,333.7 / 3,105.455** | 7,790.9 / 3,310.9 | **7,790.87 / 3,310.852** |
| `sector_gated` 2022 | 384 / 41,221.6 | — | 384 / 41,221.6 | **384 / 41,221.629** |

**PASS.** The PRECOMMIT §2 G-DRIFT verdict — every solve-path hunk since `99c75b3d` INERT for this
recipe, the key move entirely D65-B's CCS re-key — is confirmed by measurement rather than
assumed. (2023, both legs, also to the digit: control 907 offers / 36,375.1 MW price takers /
67.760; D58's arm 659 / 70,194.6 / 67.760.)

---

## 3. The identities — G1 to G5, repaired arm vs control-P

### 3.1 The 2022 auction (G1, G2)

| quantity | control-P | **repaired arm** | D58's arm (for scale) |
|---|---:|---:|---:|
| `n_offers` | 1,370 | **1,370** | 1,000 |
| `offered_mw` | 150,857.184 | **150,857.184** | 116,684.829 |
| `price_takers_mw` | 30,577.888 | **30,577.888** | 64,750.243 |
| `requirement_mw` / `census_mw` | identical | **identical** | identical |
| price $/MW-day / position / `how` | 67.760162 / 1.048349 / marginal_offer_sets_price | **67.760162 / 1.048349 / marginal_offer_sets_price** | 61.206645 / 1.050012 |
| `offer_stack` rows identical (unit, fuel, offer ≤1e-9, `A_g` ≤1e-6, cleared) | — | **1,370 of 1,370; 0 changed, 0 one-sided** | — |
| sector-1 units in the stack / accredited MW | 370 / 34,172.356 | **370 / 34,172.356** | 0 / 0 |
| uncleared by fuel (accredited MW) | coal 5,376.3 · gas_cc 9,340.7 · gas_st 8,801.9 · oil 3,722.9 | **identical** | coal 4,457.0 · gas_cc 10,465.3 · gas_ct 1,200.4 · gas_st 8,084.7 · oil 2,997.5 |

**G1 PASS, G2 PASS.** 370 of the 384 gated units offer; the other 14 have no dispatch rows or zero
accredited MW and are outside the stack in the control too (D54 §3.2's last row).

### 3.2 The partition (G3)

| set | rows | MW | sectors |
|---|---:|---:|---|
| only in **control-P** (what the gate removed) | **226** | **3,476.523** | sector 1 ×226 — nothing else |
| in **both** | **451** | ctl 26,251.375 = arm **26,251.375** | identical to the decimal |
| only in the **repaired arm** | **0** | 0 | — (D58's arm: 41 / 2,910.2, sectors 2/3/5/7/4) |

**G3 PASS.** The repaired arm's failing pool is 451 rows / 26,251.4 MW by sector: 2 25,369.2 · 3
373.1 · 4 84.2 · 5 47.5 · 6 21.1 · 7 356.4 — the control's non-sector-1 pool to the decimal.

### 3.3 The convention's own identity (G4)

Zero sector-1 and zero unknown-sector rows in any `pipeline_events` row of 2021–2023;
`sector_gated` 384 units / 41,221.6 MW (2022), 191 / 38,619.7 (2023), zero unknown-sector
fail-open MW. **Sector-1 uncleared and retained (design §2.4): 226 units / 3,210.2 accredited MW
in 2022** — coal 1,127.7 · gas_cc 640.0 · gas_st 717.2 · oil 725.3 — which is **the identical row
set the exit decision releases** (the 226 of §3.2): the corrected D54 §3.5 identity holds exactly,
restricted to the decision partition. 2023: 39 units / 2,148.9 MW. **PASS.**

### 3.4 Footprint (G5)

2022: every key in `thermal_additions`, `renewable_additions`, `storage_additions`,
`announced_derates`, `confirmed_derates`, `ccs_retrofits`, `entry_decided_mw_by_tech`,
`peak_demand_mw`, `screen_peak_demand_mw`, `screen_adequacy_requirement_mw` identical to
control-P. 2023 (fleet-delta form): 837 shared offer rows identical, 0 changed; `requirement_mw`
156,782.0 identical; census 174,011.9 vs 175,317.5 (the exit delta); 841 offers vs the control's
907 (D58's arm: 659) — 70 units absent from the arm's 2023 stack are the merchant gas-steam / CHP
rows the arm executed in 2022 (§4), and 4 present only in the arm are the sector-1 Chesterfield /
ComEd gas-steam tranches the control executed in 2022; price 67.760 in both. **PASS.**

---

## 4. G6 fired — and what the ledgers say it is

| screen year | control-P | D58's arm | **repaired arm** | G6 (≤ control) |
|---|---:|---:|---:|---|
| executed economic exits 2022 (MW) | 7,333.7 | 7,790.9 | **8,736.687** | **FAIL** (+1,403.0) |
| executed economic exits 2023 (MW) | 3,105.455 | 3,310.852 | **2,884.292** | PASS (−221.2) |

**The decomposition** (`d78/exit_diagnosis.json`, unit by unit):

| 2022 screen | control-P | **repaired arm** | Δ |
|---|---:|---:|---:|
| `decided` (admitted by the cap) rows / MW | 79 / 13,177.472 | **128 / 13,354.701** | +177.2 (+1.3 %) |
| … of which executing **2022** (lag-1 fuels: gas_st, gas_cc, oil) | 7,333.7 | **8,736.687** | **+1,403.0** |
| … of which executing **2024** (lag-3: coal) | 5,843.772 | **4,618.014** | **−1,225.8** |
| `entry_capped` rows / MW | 598 / 16,550.426 | 323 / 12,896.674 | −3,653.8 |
| `floor_retained` / `throughput_deferred` | 0 / 0 | 0 / 0 | — |

**Arm-only 2022 executions: 70 rows / 1,871.4 MW** — gas_st 1,828.0 + gas_cc 43.4, sectors 2 ×4 ·
3 ×5 · 5 ×6 · 6 ×2 · 7 ×53 (the AEP-Ohio ST_CHP tranches, APS p3096's CC peak tranche, …) —
**every one `entry_capped` in the control and `decided + executed` in the arm.** **Control-only
2022 executions: 4 rows / 468.5 MW** — the sector-1 gas-steam tranches of Dominion p3775
(Chesterfield) and ComEd p972, gated in the arm. Net +1,403.0 MW.

**2023 closes the loop:** the control decides and executes **80 rows / 2,203.8 MW** the arm does
not — 70 of them *are the same 70 rows the arm already executed in 2022* (they are in the control's
2023 `decided` set, 108 rows / 3,105.5 MW, and absent from the arm's 2023 fleet) plus 10 sector-1
rows; the arm executes 17 merchant gas-CC rows / 1,982.6 MW the control capped. Window-level, the
merchant cohort is the same set of units, a year earlier.

**Reading.** The candidate-set gate did exactly what D53 §1.2 defines — the pool shrank by the
sector-1 rows and nothing else (G3). The R-NEW admission cap (`_apply_reliability_floor` on the
scheduled-exit counterfactual, FF-1A component 2) is a *budget*: removing 226 admitted-or-capped
sector-1 candidates — most of them lag-3 coal, which had been spending the 2024 budget — frees
room that the cap re-spends cheapest-firm-adequacy-first from the capped merchant pool, whose
marginal rows here are lag-1 gas-steam CHP. So per-year executions move **earlier**, not larger:
the identity a candidate-set gate obeys is on the decided cohort, not on the year of execution.
The PRECOMMIT's own §5 item 3 predicted precisely this re-fill (admitted 11.5–13.5 GW: **HIT at
13,354.7**); G6 asserted its opposite for the executed leg and was the over-strong sibling. **Rule
29's discipline is that the pre-registered STOP gate decides, and it decided: the full window is
not spent by this lane.** The number is reported at full magnitude either way; nothing about it
is a residual, and nothing about it is a defect in the seam repair.

---

## 5. The pre-declaration, graded at full magnitude

| # | prediction (PRECOMMIT §5) | outcome |
|---|---|---|
| 1 | 2022 stack, price, position identical to control-P | **HIT** — 1,370 / 150,857.2 / 30,577.9 / 67.760162 / 1.048349, every stack row identical |
| 2 | 2022 failing pool = 451 rows / 26,251.4 MW, exactly the control minus its sector-1 rows; no merchant row in either one-sided set | **HIT** — 451 / 26,251.375; one-sided sets 226 sector-1 / 0 |
| 3 | 2022 admitted re-fills to 11.5–13.5 GW, all non-sector-1 | **HIT** — 13,354.7 MW, zero sector-1 rows |
| 4 | 2022 economic exits ≤ 7,333.7; 2023 ≤ 3,105.5 | **MISS on 2022 (8,736.7, +1,403.0), HIT on 2023 (2,884.3)** — the G6 firing, diagnosed in §4 as the cap re-fill's timing shift |
| 5 | 2023 `n_offers` > 659, = control's minus the exit delta; shared offers identical; price unchanged | **HIT** — 841 (control 907, D58 659); 837 shared rows identical; 67.760 both |
| 6 | sector-1 uncleared-and-retained = the 226 released rows | **HIT** — 226 units / 3,210.2 accredited MW, the same row set as G3's control-only set |
| 7 | full window: `retire.total_gw` down, recall 11–13/20 | **NOT SPENT** (G6) |
| keys | all four as §4 of the PRECOMMIT, no collision | **HIT** — `afda79ba04cbfdbf`, `d527c3299b8c00b5` ×2 |
| G0 | D58 reproduced to the MW on both legs | **HIT** (§2) |

**Tally: 8 hits, 1 miss, 1 not spent.** The miss is the gate that stopped the window; its cause is
inside the pre-declaration's own re-fill prediction.

### 5.1 The dated block, reported without moving it (design §4.1)

The control's 2022 `price_takers_mw` (30,577.9) contains VRE, hydro, storage, imports, DR, dated
plants and retrofits; the dated component is **not separable from the committed ledgers** (a
dated unit has no `margins` row and no ledger block of its own). What the 2022 ledger does carry:
`announced_derates` 4 rows / 681.7 MW and `announced` (dated) retirements 3,478.6 MW executed in
2022 — the step-1b channel's *executed* half, not the pending block. Sizing the pending block is a
zero-LP read of the fleet against the exit registry and belongs to the D57-family card §8 routes.

---

## 6. Governance attestation

**Rule 1 `[R-STRUCT]`:** the mechanism is the tariff's must-offer rule (design §1); every gate
graded is an identity or a sign, none a band or a residual; the one firing gate is honored on
structure. **Rule 12:** PJM solo, three legs sequential, years sequential. **Rule 13 / 14:** a
published market rule regenerating per delivery year; the sign line was stated before the solve and
its violation is reported at full magnitude and diagnosed, not absorbed. **Rule 19 `[R-ONE-MECH]`:**
the D58 one-filter-two-jobs violation is removed — exit candidacy and capacity offering are two
declarations on two parameters, each with one consumer set (design §2). **Rule 21:** zero DOF.
**Rule 22:** solve years {2021, 2023}, 2022 bridged and never scored; nothing outside training
touched; the freeze asserted by every run banner. **Rule 24:** no tunable added or changed.
**Rule 25:** PJM's cell carries PJM's own letter; MISO's `K` untouched and byte-identical by test.
**Rule 27:** `retirements.py`, `evolve.py`, `scenarios.py`, `cache.py`, `test_capacity.py`, the
spec and the PJM shard edited locally and **blob-verified after push** (local `hash-object` =
remote blob on every file). **Rule 28(b):** PJM's shard only; no new row (no field). **Rule 29:**
phase 0 zero-LP and pushed first; the screen year named from the seam's own footprint; STOP-only
structural gates; a fired gate kills the window; the three bundles deleted before merge; every
number cited is in this document, `d78/screen_compare.json` and `d78/exit_diagnosis.json`.

**Stated deviations.** (i) The charter's literal start condition — D74's *screen* landed on main —
was not met (PRECOMMIT §0): D74's build hunks, the collision the hold protected, are on main; no
D74 screen landed during the session and main did not move, so no rebase was owed and no D74 hunk
could be dropped. (ii) RSS not captured (§1).

**Pre-existing reds on main, not this lane's** (each verified red on the pre-D78 commit): the
D65-B default-key pins `test_capacity.py::TestRetirementSectorGate::test_cache_key_registration_and_backcast_coercion`,
`test_capacity.py::TestPjmCapacitySupplyClearing::test_pjm_iso_override_arms_forecast_only` and
`test_vre_procurement_ffr5e.py::TestProcurementGate::test_default_cache_key_is_unmoved` (they pin
`e5ecd4105ada3e58` / `aef81c84c4609c76`, which D65-B moved to `547053bdfccd4264` /
`15a723ba3b6dc856`). Routed, not repaired here (D80's records lane owns main's reds).

---

## 7. Matrix (rule 28) and retention (rule 29(c))

- PJM's `retirement_sector_gate` cell stays **`O`** with this finding's evidence
  (`docs/codebase-site/data/mechanism-matrix/PJM.js`; `check_mechanism_matrix.py --base
  origin/main` exit 0). No other shard touched.
- D53 §1.8 and D54 §3.2 / §4.7 carry dated cross-references (`6a00c4c6`), never a rewrite.
- **All three screen bundles are deleted** (`results/hindcast/pjm-2021-2023-realized-t1h-d78-*`,
  the two in the pinned worktree and the one in the main tree); the worktree is removed. Nothing is
  registered on either dashboard.

---

## 8. Recommendation

1. **MERGE the seam repair as code, now.** It is the owner's ruled reading (Q53), the gate's own
   definition, one seam, zero DOF, byte-identical with the gate off and byte-identical on the only
   armed configuration that exists (MISO, clearing off — T2), and its PJM effect is measured exact
   (§3). It closes the D58 §3 defect and the rule-19 violation D58 named. Merging is not arming:
   `retirement_sector_gate` stays default-off and un-overridden for PJM.
2. **Re-charter the full 2021–2025 window (one lane, two legs, ~35 min)** with the sign line stated
   where a candidate-set gate can obey it — on the **decided cohort and the window total** (G3 is
   already that identity) — and per-year executions reported, not gated. The D58 §5 / PRECOMMIT §7
   flip condition (a) purity, (b) fidelity, (c) composition on the full-window `score.json`, (d)
   LOYO is then adjudicable; (a) and (b) already read MET on the screen span. Nothing in this
   finding predicts (c) or (d); §5 item 7 stays unspent.
3. **The dated-plant offer card (D57 family):** the identical seam reaches the pending dated block
   (design §4); the repair is one line (`_dated_exempt` → `exit_exempt_unit_ids`) and the owner's
   question is whether D54 §4.2's price-taker reading stands now that Q53 has ruled the sector
   case; its magnitude is a zero-LP read (§5.1).
4. **For the director's records:** PJM's shard cell `capacity_no_default_cap_convention` on main
   cites `FINDING-capx-d74-2026-09-06.md`, which does not exist (D74's screen is owed); and main
   carries the three D65-B key-pin reds of §6.

## 9. Reproduction

```
uv run python docs/handoffs/d78/keys_probe.py                      # keys at HEAD + the D65-B attribution
bash docs/handoffs/d78/run_screen.sh control-P                     # pre-fix code (34d78e91)
bash docs/handoffs/d78/run_screen.sh d58-arm --retirement-sector-gate   # pre-fix code
bash docs/handoffs/d78/run_screen.sh arm --retirement-sector-gate       # post-fix code (9fcdf19c)
uv run python docs/handoffs/d78/screen_compare.py --ctl <ctl> --d58 <d58> --arm <arm>
PYTHONPATH=docs/handoffs/d78 uv run python docs/handoffs/d78/exit_diagnosis.py --ctl <ctl> --d58 <d58> --arm <arm>
```

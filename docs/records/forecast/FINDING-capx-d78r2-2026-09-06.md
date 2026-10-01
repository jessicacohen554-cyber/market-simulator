# FINDING — capx D78-R2: the corrected W4 edge lands the arm EXACTLY on its exact-partition point value, the whole-ledger diff finds ZERO unclassified rows in five years — and W5′ fires again, this time falsifying my own ex-ante class declaration against the very document I cited

**Lane:** capx D78-R2 (director r#50, pack §D78-R2). **Date:** 2026-09-06. **Model:** Opus.
**DATA PROFILE:** `pjm`. **Branch:** `claude/capx-d78r2-full-window-2zudj4`.
Pre-registration `PRECOMMIT-capx-d78r2-full-window-2026-09-06.md`, pushed at **`2aa9d1e3`
before any LP**, with **ADDENDUM A** (the rebase + G-DRIFT re-audit), **ADDENDUM 1** (the W4′
band and the control's pre-arm bars) and **ADDENDUM 2** (the arm's HEAD-guard trip) each pushed
**before the leg or the grade it governs**, plus **CORRECTION 1**. Instruments
`docs/handoffs/d78r2/{keys_probe,window_compare2}.py`, committed before the first LP.

**NOTHING ARMS. `retirement_sector_gate` stays default-off and un-overridden for PJM.** No
`ScenarioConfig` field added or changed, no default flip, no `_pjm_config` override, no parameter
value, no keeper, no marker, zero DOF. The one code change is the **STEP 0 deletion**, which is a
removal and moves no key. The arm registers SUFFIXED as `pjm-t1h-d78r2-sectorgate`; the bare
`pjm-t1h` key is untouched; the control bundle is **deleted before merge** (rule 29(c)).

---

## 0. Verdict

**Three of the four flip-condition limbs are MET, the corrected W4′ edge is vindicated to the
milli-MW, the whole-ledger diff is clean in all five years — and limb (a) fails again, so the
pre-stated recommendation is HOLD-and-route.**

W1 / W2 / W3 **PASS in all five years**: the arm's failing pool is the control's minus rows that
are **100 % sector-1** (2022 26 / 1,993.188 MW; 2023 3 / 127.566; 2024 6 / 3,158.006), the
**arm-only set is EMPTY in every year**, every shared row's MW is identical, and **zero** sector-1
rows reach any decision ledger anywhere. **W4′ PASSES and lands on `9,394.156` MW — the
exact-partition POINT VALUE, to the milli-MW**, a fall of exactly the control's sector-1 decided
MW (`−2,120.754`); the repaired lower edge ADDENDUM 1 wrote down before the arm existed is
therefore not merely passed but *hit*, which is the strongest form this gate can take and is the
direct vindication of D78-R §4's diagnosis. The **whole-ledger diff (new this lane) finds ZERO
unclassified per-unit rows across five years and every block**: every differing `pipeline_events`
and `retirements` row is R1 sector-1, and **not one non-sector-1 unit changes state anywhere in
the window**. 2021 differs in **no block at all**. The 2022 auction is **byte-identical** on
identical fleets — 1,399 offers, 158,103.444 / 23,331.628 MW, 90.411052 $/MW-day, position
1.042601, requirement 163,268.9, same marginal unit, all 1,399 stack rows identical.

**But W5′ FIRED**, and — unlike D78-R's two firings, which were mis-derived edges — this one is a
**falsified prediction about the world**, and it falsifies my own ex-ante class declaration
against the very document I cited to make it. I declared `{gas_ct, gas_st, oil}` a year-invariant
zero-E&AS set on `FINDING-capx-d57` §0/§8.1's headline. **D57's own §4 table is per delivery year
and says, in its 2024/25 row, "the CT fleet's 2024 margin is small but non-zero."** The
measurement matches D57 exactly: in 2024–2025 all 404 shared `gas_ct` rows move, while **the 8
`oil` rows — the class that row DOES put at the full bar — move by exactly zero, in both years**.
Limb (a) is FAIL and §7's pre-stated rule returns **HOLD-and-route**.

`retire.total_gw` moving FAIL → PASS (18.058 → 15.937 against 15.062 actual) is reported at full
magnitude and is **explicitly not a criterion in either direction** (rule 14).

---

## 1. What was solved

| leg | recipe | key declared → realized | HEAD guard | wall |
|---|---|---|---|---|
| **control-P** | bare `pjm-t1h` | `a9c66d8ea25acb9d` → **match** | `65e12b21` **held** | 19:20:30 → 19:41:33 ≈ **21.1 min** |
| arm *(DISCARDED)* | `--retirement-sector-gate` | `bb6a60239d69508b` → match | **TRIPPED** (ADDENDUM 2) | 19:42:56 → 20:03:27 |
| **arm** | `--retirement-sector-gate` | `bb6a60239d69508b` → **match** | `68bbb025` **held** | 20:05:21 → 20:25:50 ≈ **20.5 min** |

All: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics`, through the committed
`docs/handoffs/d78r2/run_full.sh`. Solve years **{2021, 2023, 2024, 2025}**, **2022 bridged**;
PJM solo, legs sequential, years sequential (rule 12). `data/clean` was absent at session start
and was rebuilt in full first: **56/56 datatypes, 0 failures**.

**The first arm was discarded, not graded, and no number from it appears anywhere in this
document.** Its HEAD guard fired because *I* committed docs while it solved — `main` never moved
(`git rev-list --count HEAD..origin/main` = 0) and the solve-path diff across the whole window
spanning both legs is EMPTY, so the property the guard certifies demonstrably held. I could have
graded it on that reasoning, and D78-R's own §1 grades two legs whose guard shas differ by exactly
a docs commit. **The argument was declined**: PRECOMMIT §6 says a fired STOP is honored *however
right the diagnosis*, and a lane that reaches for a correct-sounding reason to walk past its own
gate has made that gate advisory. The distinction is real rather than convenient — D78-R's guard
never fired, because it pushed its addendum *between* legs; mine fired. The remedy cost 20.5
minutes. Full disclosure: ADDENDUM 2, pushed before the replacement leg ran.

## 2. G-DRIFT and the drift cross-check (ADDENDUM A)

`main` moved `e6a0402f` → `b22b91c3` (45 commits) before either leg. `constants.py` first:
**empty**. Eleven solve-path files, +1437 −48, **every hunk INERT, zero LIVE** — three are this
lane's own STEP 0, six are capx D79's additive `solve_surface` provenance stamps, one is another
ISO's artifact (`miso_ct_netload_drag.json`, rule 25), two are D79's new modules.

**D79 changes `cache_key()` itself, so its "moved zero keys" claim was MEASURED, not accepted on
its own comment**: `keys_probe.py` re-run at `b22b91c3` is byte-identical to its committed output
at pristine `e6a0402f`, and independently `moved_rows("PJM")` = `{}` with `SOLVE_EPOCHS` = `()`.

**An unplanned third confirmation.** This control was solved 45 commits after D78-R's, across
D67-ARM / D81 / D74 / D75-R / D79, and reproduces D78-R §4–§5 **to the digit**: window decided
11,514.910, sector-1 decided 2,120.754, `Σg_y` 1,003.400, `total_gw` 18.058 / err 0.199, recall
0.650 (13/20), `plant_recall_frac` 0.700, `false_retire` 8.065 GW / 0.447, `economic` precision
0.122, `all` 0.421. Recorded as a cross-check; **not** used as a control (both graded legs are
this lane's own, at one HEAD).

## 3. W1 / W2 / W3 — the identities, all five years (**PASS**)

### 3.1 W1 — candidate identity

| year | form | control-only rows / MW | sectors | arm-only | shared | shared MW identical | unexplained |
|---|---|---:|---|---:|---:|:--:|---:|
| 2021 | exact | 0 / 0 | — | **0** | 0 | ✓ | 0 |
| 2022 | exact | **26 / 1,993.188** | **sector 1 ×26 — nothing else** | **0** | 103 | ✓ | 0 |
| 2023 | fleet-delta | **3 / 127.566** | **sector 1 ×3** | **0** | 20 | ✓ | 0 |
| 2024 | fleet-delta | **6 / 3,158.006** | **sector 1 ×6** | **0** | 0 | ✓ | 0 |
| 2025 | fleet-delta | 0 / 0 | — | **0** | 0 | ✓ | 0 |

*(2023 is graded in the WEAKER fleet-delta form here, per the pre-LP instrument repair `ae5a3355`:
W1's identical-fleet form must run strictly BEFORE the first divergent year, and 2023 is that
year. It passes the strict form too — arm-only 0, every control-only row sector-1 — so the repair
costs nothing evidentially and is disclosed because it was made, not because it mattered.)*

### 3.2 W2 — decided-cohort composition

**ZERO** sector-1 rows in `decided`, `entry_capped`, `floor_retained`, `throughput_deferred`, any
`pipeline_events` row, and `retirements` with `reason == "economic"` — **in all five years**. Zero
unknown-sector pipeline rows in all five years.

### 3.3 W3 — decided-cohort provenance

**Zero** arm-only decided rows and **zero** arm-only executed rows in every year. Nothing entered
the arm's candidate universe that was not in the control's.

## 4. W4′ — the repaired edge is HIT, not merely passed (**PASS**)

| quantity | control-P | **arm** | Δ |
|---|---:|---:|---:|
| window **decided** MW | 11,514.910 | **9,394.156** | **−2,120.754 (−18.42 %)** |
| control's sector-1 **decided** MW (2022 1,993.188 + 2023 127.566) | **2,120.754** | — | — |
| **W4′ band (ADDENDUM 1, pre-registered)** | **[9,394.156 , 12,518.310]** | 9,394.156 | **ON the lower edge** |
| **point value (exact partition)** | **9,394.156** | **9,394.156** | **0.000** |

The arm's window decided total falls by **exactly** the control's sector-1 decided MW, to the
milli-MW, and **lands on the pre-registered point value with zero residual**. Nothing re-fills,
because under D67-ARM's published requirement the admission cap binds in **2024 alone**
(`capped_mw` = 0 in 2021/2022/2023/2025) — so the two years carrying the sector-1 decided MW have
no capped pool to draw from.

**This is the direct vindication of D78-R §4.** That lane measured the identical
`9,394.156` and its own gate refused it, because it had bracketed the downside by the admission
cap's granularity (`±Σg_y` = 1,003.400) instead of by the sector-1 decided MW the partition
removes (2,120.754). On the corrected edge the same measurement is a clean pass sitting exactly on
the predicted point. D78-R's `[10,511.510 , 12,518.310]` is superseded, not re-read.

## 5. W5′ — **FAIL**, and the failure is a falsified prediction, not a mis-derived edge

| year | form | `A_g` | fuel | offers | cleared flags | verdict |
|---|---|:--:|:--:|---|:--:|:--:|
| 2021 | exact | ✓ | ✓ | ✓ (empty stack) | ✓ | **PASS** |
| **2022** | exact | ✓ | ✓ | **all 1,399 identical** | ✓ | **PASS** |
| 2023 | exact (= D) | ✓ | ✓ | **all 849 shared identical** | ✓ | **PASS** |
| **2024** | post-divergence | ✓ | ✓ | **679 of 835 shared move** | 5 differ *(reported, not gated)* | **FAIL** |
| **2025** | post-divergence | ✓ | ✓ | **619 of 821 shared move** | 0 differ | **FAIL** |

`A_g` diff **0** and fuel diff **0** in every year: the structural limbs — the ones that would
signal a second seam — hold everywhere. The first divergent year **D = 2023**, computed from the
ledgers, and offers are exact through it, exactly as the propagation account predicts.

### 5.1 What fired, measured per fuel

The propagation limbs gate two falsifiable consequences: every unit in the declared zero-E&AS set
carries offer delta **exactly 0**, and every mover lies outside it. Measured, shared rows only:

| fuel | 2022 | 2023 | 2024 | 2025 | distinct control offers (2023 → 2024) |
|---|---|---|---|---|---|
| **oil** | 421 shared, **0 move** | absent | 8 shared, **0 move** | 8 shared, **0 move** | 1 (a single class-uniform bar, 76.1035) |
| **gas_st** | 118 shared, **0 move** | absent | absent | absent | 3 |
| **nuclear** | 31, 0 move | 31, 0 move | 31, **0 move** | 31, **0 move** | 1 (offer $0) |
| **gas_ct** | 404, **0 move** | 403, **0 move** | 404, **404 move** | 404, **404 move** | **12 → 72** |
| gas_cc | 237, 0 | 231, 0 | 212, 95 move | 212, 52 move | — |
| coal | 188, 0 | 184, 0 | 180, 180 move | 166, 163 move | — |

### 5.2 The diagnosis — and it condemns my declaration on its own citation

I declared `{gas_ct, gas_st, oil}` zero-E&AS **as a year-invariant class property**, citing
`FINDING-capx-d57` §0/§8.1: *"the gas-CT (404 units / 24.2 GW), gas-ST (115 / 8.8 GW) and oil
(421 / 3.7 GW) fleets carry exactly zero E&AS margin in the hindcast prices and offer at their
full bars."* **That headline is a statement about DY2022/23.** D57's §4 table, which
operationalizes it, is indexed **by delivery year**, and its 2024/25 row reads:

> units / firm MW **AT THE FULL BAR (zero E&AS)**: `oil 8 / 3,723` **(the CT fleet's 2024 margin
> is small but non-zero)**

So the document I cited says, in the row covering the years my gate failed in, precisely what my
gate then discovered. **I cited the headline instead of the table.** This is my construction
defect, in the same family as D78-R's W4 — a bound imported from one regime and applied to
another — and it is reported at full magnitude rather than smoothed over.

**The measurement matches D57 row by row**, which is why the failure is informative rather than
merely embarrassing:

- **oil** — the one class D57's 2024/25 row still puts at the full bar — moves by **exactly zero
  in both 2024 and 2025** (8 shared rows, one distinct offer). The prediction is *confirmed*
  exactly where D57 says it should hold.
- **gas_st** exits the shared stack after 2022 (D74's no-default-cap convention makes Steam Oil &
  Gas a $0 price taker outside the screen), so it was never testable in the failing years.
- **gas_ct** carries **12 distinct offers in 2022–23 and 72 from 2024** — a class at its bar has a
  class-uniform offer; acquiring a live margin is exactly what fans it out. The count moves in the
  same year D57 says the margin becomes non-zero.

**The mechanism is not implicated, and the propagation account is now positively confirmed rather
than merely diagnosed.** Every mover has a live E&AS operand; every class genuinely at its bar
(oil in every year it appears, gas_st in 2022, gas_ct in 2022–23, nuclear always) has offer delta
exactly zero. The direction is right too: the arm's offers are **higher** (e.g. 32.0691 →
33.1520 $/MW-day for the CT tranches), because the arm retires less, so the prior year's prices
are lower, so the E&AS margin is smaller and the net-ACR offer larger. That is the prior-year
price channel behaving as physics says it must.

**The gate is still honored.** Rule 29's discipline does not ask whether the diagnosis is right —
D78-R established that on two gates, and this lane exists because it did. Limb (a) is FAIL.

## 6. The WHOLE-LEDGER DIFF — zero unclassified rows, five years, every block (**PASS**)

New this lane, on `FINDING-capx-d81` §8 item 4's lesson that *an assertion list can only catch
what its author already thought of*. Every top-level block of every year's `evolution_<year>.json`
was differenced — the union of both legs' keys, not an allowlist — and each difference classified.

| year | blocks differing | per-unit rows differing | R1 sector-1 | R2 fleet-delta | **UNCLASSIFIED** |
|---|---|---|---:|---:|---:|
| 2021 | **none at all** | — | — | — | **0** |
| 2022 | 4 | `pipeline_events` 26, `retirements` 12 | **38** | 0 | **0** |
| 2023 | 10 | `pipeline_events` 17, `retirements` 3 | **20** | 0 | **0** |
| 2024 | 11 | `pipeline_events` 20, `retirements` 14 | **34** | 0 | **0** |
| 2025 | 9 | none | — | — | **0** |

**Not one non-sector-1 unit changes state anywhere in the window** — every per-unit difference in
five years is a sector-1 row, and even the R2 fleet-delta escape hatch is never used. **Zero
STOPs.**

The differing aggregates are named rather than waved at, and each is downstream of the arm
retiring less: `fleet_by_fuel_before/after`, `sector_gated` (absent in the control — the gate is
off), `screen_entering_firm_mw` (2023 174,996.123 → 175,713.339; 2024 173,736.876 → 174,575.279;
2025 144,448.854 → 146,120.478), `screen_reserve_position` / `capacity_reserve_position` /
`reserve_margin`, `entry_screen_diagnostics`, and the `capacity_clearing` scalars. Blocks that
fall to aggregate treatment because their rows carry no `unit_id` (`entry_pipeline`,
`entry_screen_diagnostics`) or that are absent from `PER_UNIT_BLOCKS` (`storage_additions`,
`locality_capacity`) are empty or unchanged in every year — stated so a reader can see the
declared classification left nothing hidden.

**The clearing, year by year.** 2022 is byte-identical on every scalar *including the marginal
unit*. 2023 keeps price 86.517664, position 1.044534 and the same marginal unit; only the census
and offer count move, by the fleet delta (+12 offers, +717.216 MW). 2024 and 2025 move through the
propagation: price 165.966209 → 165.252476 and **358.266988 → 236.945273**. The 2025 move is
large and has a clean cause: the control's cleared position is **0.998023**, *short* of the
requirement (144,164.350 vs 144,450.0) and so far up the steep part of the VRR curve, while the
arm's extra 1,671.625 MW carries it to **1.009595**. Reported, not gated.

## 7. Reported at full magnitude, never gated (rule 14)

| quantity | control-P | **arm** | note |
|---|---|---|---|
| **FC-3 `retire.total_gw`** (actual 15.062) | 18.058 · err 0.199 · **FAIL** | **15.937 · err 0.058 · PASS** | **NOT a criterion in either direction** |
| `unit_recall_gt300` | 0.650 (13/20) · FAIL | **0.550 (11/20)** · FAIL | falls, as a partition that removes matched sector-1 exits must |
| `plant_recall_frac` | 0.700 (14) | 0.700 (14) | unmoved |
| `false_retire` | 8.065 GW · 0.447 · FAIL | 7.166 GW · 0.450 · FAIL | |
| window `economic` release **precision** | 0.122 | **0.146** | **RISES** — limb (c) |
| window `all` release precision | 0.421 | 0.476 | |
| window **executed** economic MW | 11,514.910 | **9,394.156** | −2,120.754 |
| executed 2022 / 2023 / 2024 | 9,464.455 / 828.467 / 1,221.988 | 8,693.255 / 700.901 / **0** | per-year, reported |
| window retirements, all channels | 17,034.468 | 14,913.714 | |

`retire.total_gw` crossing FAIL → PASS is a **consequence** of removing candidates from a control
that over-retires (D58 PREDECL §3 P5). It is not evidence for the mechanism, and a worse band
would not have been evidence against it.

## 8. The flip condition, graded (PRECOMMIT §7)

| limb | condition | reading |
|---|---|---|
| **(a) purity** | W5′ on the full window | **FAIL** — structural limbs hold every year; exactness holds through D = 2023; the propagation limbs fire in 2024–2025 because my declared zero-E&AS class set was year-invariant where D57's own table is per-delivery-year (§5.2) |
| **(b) fidelity** | W1 + W2 + W3 | **MET** — the pool falls by exactly the sector-1 rows in every year, zero sector-1 rows in any decision ledger, zero unexplained rows |
| **(c) composition** | window `economic` precision ≥ control's, every row non-sector-1 | **MET** — 0.122 → **0.146**, and W2 gives every row non-sector-1 |
| **(d) LOYO** | no fold lost that the control holds | **MET** — but **NON-DISCRIMINATING on recall, as ADDENDUM 1 said BEFORE the arm ran**: the control holds no recall-PASS fold (−2023 8/12, −2024 11/19, −2025 13/19, all FAIL) and the arm holds none (6/12, 11/19, 11/19), so none is lost. `tr10a`/`tr10b` PASS on all three folds in both legs and do discriminate. |

**W4′ and the LEDGER diff are STOPs, not limbs** (PRECOMMIT §7): both PASS, so neither kills; by
construction neither can promote.

**§7's pre-stated rule:** *"Recommend HOLD-and-route if (a) fails."*

# **RECOMMENDATION: HOLD-and-route. NOT ARM.**

Held on limb (a) alone — **not** on the mechanism, whose fidelity (b), composition (c) and LOYO
(d) limbs are all MET, whose partition identity is exact in all five years, whose window total
lands on the pre-registered point value to the milli-MW, and whose whole-ledger diff finds zero
unclassified rows in five years and every block.

**What is different from D78-R, and it is not nothing.** D78-R held on limb (a) *and* a fired W4
whose edge was wrong. This lane repaired that edge and the arm **hit it exactly**; it added a
whole-ledger diff that could have found a second seam anywhere in five years and found none; and
its W5′ firing is no longer an un-carved-out propagation but a **specific, located, per-delivery-
year fact about the E&AS operand**, confirmed by the one class that still sits at its bar moving
by exactly zero. The evidentiary distance left to an arming recommendation is now one
pre-registration, not one investigation.

## 9. Routed to the director — what the successor must pre-register

1. **Declare the zero-E&AS set PER DELIVERY YEAR**, citing `FINDING-capx-d57` §4's table rather
   than its headline. On D57's own rows that is `{gas_ct, gas_st, oil}` for DY2022/23,
   `{gas_ct, gas_st}` for 2023/24, and **`{oil}` alone for 2024/25** — which is exactly what this
   lane measured.
2. **Better, derive it structurally on the CONTROL leg before the arm**, the way ADDENDUM 1
   derives the W4′ band: a class at its full bar has a **class-uniform offer** (oil 1 distinct
   value, nuclear 1, gas_st 3; gas_ct 12 while barred and 72 once live), so the set is readable
   from the control's own stack at zero LP. That keeps it a pre-registered structural derivation
   rather than a literature quotation, and it cannot be tuned against the arm because the arm does
   not exist yet. Guard against the obvious failure mode by requiring the derived set to be a
   subset of D57 §4's per-year set — a class the record does not put at its bar may not be
   admitted by the control's arithmetic alone.
3. **Re-solve is NOT required to settle this.** Both bundles carry their evolution ledgers, so a
   successor can re-grade W5′ on the corrected declaration from the committed artifacts. But
   under rule 29 a corrected gate is a *successor's* pre-registration, never a re-read of this
   one, and the arm bundle it re-grades must be one whose registration survives §10.

## 10. Governance attestation, limitations, retention

**Rule 1 `[R-STRUCT]`:** the mechanism is PJM's must-offer requirement plus an ownership
attribute; every gate graded is an identity or a control-derived bracket, none a residual; the
firing gate is honored on structure; and the one metric that improved (`retire.total_gw`) is
explicitly excluded from the determination. **Rule 12:** PJM solo, legs sequential, years
sequential. **Rules 13/14:** the sign line was stated before the solve on a quantity the mechanism
controls; every number is reported at full magnitude, my own construction error included.
**Rule 19:** no mechanism stacked; the D78 seam is used as merged. **Rule 21:** zero DOF — no
parameter set, and the only code change is a deletion. **Rule 22:** forecast-mode hindcast; solve
years {2021, 2023, 2024, 2025}, 2022 bridged; nothing outside training solved, scored or
registered in backcast mode. **Rules 24/25:** no tunable added or changed; PJM's cell only, on
PJM's own evidence. **Rule 26:** STEP 0 deletes the producer-less `exempt_unit_ids` rather than
documenting it as unused. **Rule 27:** every push of a ≥300-line file was blob-verified against
local. **Rule 28(b):** PJM's shard only; the mechanism-level row's stale `exempt_unit_ids`
description was repaired in the same PR that deleted the parameter. **Rule 29:** G-DRIFT before
any LP and re-audited after the rebase; the pre-declaration and every addendum pushed before the
leg or grade it governs; STOP-only structural gates; **two fired STOPs honored** (the HEAD guard,
by re-solving; W5′, by holding); the control bundle deleted before merge.

**Stated limitations.**
1. **`CORRECTION 1`**: PRECOMMIT §2 and ADDENDUM A §A.1 each claimed, as one of three reasons
   D78-R's bundles cannot serve as this lane's control, that its registered arm carries no
   evolution ledgers. **That is false** — the slim registered set includes all five. The claim is
   withdrawn; the decision stands on the other two reasons, either sufficient alone (its legs are
   19 files / +2,975 −54 behind HEAD on `retirements.py` / `capacity_market.py` / `adequacy.py`,
   and its control-P was deleted before merge). The merged PRECOMMIT was not silently rewritten.
2. **The W5′ class declaration was wrong**, §5.2, against the document it cited. The successor's
   repair is §9.
3. **Limb (d) is non-discriminating on recall** — the control holds no recall-PASS fold, so
   "loses no fold" is trivially satisfied on that leg. Said in ADDENDUM 1 before the arm ran, not
   after. `tr10a`/`tr10b` do discriminate and pass in both.
4. **The first arm leg was discarded** on a HEAD-guard trip caused by my own mid-leg docs commit
   (ADDENDUM 2). No number from it is cited.
5. **RSS not captured** (`/usr/bin/time` absent on this box), as in D78 / D78-R; wall is inside
   the D57 envelope on every solve year.
6. **Cleared-flag differences after D are reported, not gated** — declared in the PRECOMMIT
   before the solve, with the reason (the flag is downstream of the offer; gating it would gate
   the same propagation twice). Measured: 5 in 2024, 0 in 2025.

**Retention (rule 29(c)).** `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-control-P` is
**deleted before merge**; the arm keeps only its slim registered files. Every number this lane
will ever cite is in this document, the PRECOMMIT with its addenda and correction, and
`docs/handoffs/d78r2/{keys_probe,keys_probe_origin_main,control_band,window_compare2}.json`.

## 11. Matrix (rule 28) and registration

- PJM's `retirement_sector_gate` cell stays **`O`** (open) with this finding's evidence — the
  partition is now proven exact over the full window on a corrected edge and a whole-ledger diff,
  and the lane's own gate refuses promotion. `mechanism-matrix/PJM.js` only; no other shard.
- The arm registers SUFFIXED: `pjm-2021-2025-realized-t1h-d78r2-sectorgate` →
  **`pjm-t1h-d78r2-sectorgate`**, slim files only, **after D65-B-R's batch registers**
  (PRECOMMIT §8).
- **Board lock:** the registry sidecar and its `VERDICT_MAP` entry only; the `ff-verdicts.json` /
  `program-status.json` snapshot row is **held** — the board is not this lane's to write.

## 12. Reproduction

```
uv run python docs/handoffs/d78r2/keys_probe.py
bash docs/handoffs/d78r2/run_full.sh control-P
uv run python docs/handoffs/d78r2/window_compare2.py --ctl <ctl> --band-only   # the W4' band
bash docs/handoffs/d78r2/run_full.sh arm --retirement-sector-gate
uv run python scripts/score_capacity_hindcast.py --bundle <dir>
uv run python scripts/score_capacity_hindcast.py --bundle <dir> --flip-gate-extras
uv run python docs/handoffs/d78r2/window_compare2.py --ctl <ctl> --arm <arm>
```

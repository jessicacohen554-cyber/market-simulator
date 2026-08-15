# FINDING — ercot-202: the rule-18 grain repair, SOLVED — and `p6243` is not what the charter feared

**Session ercot-202, 2026-08-14. ERCOT only (rule 25).**
Branch `claude/ercot-195-lever-selection-scssqc` (the branch name carries a
stale shorthand — see §0).
Pre-registration:
`docs/PRECOMMIT-ercot202-rule18-grain-successor-2026-08-14.md`, pushed at
`f73b9a1` **BEFORE** any measurement, derive or solve.

Keeper at session start: **`2026-08-12-run192-arm-coal-peak`**
(`results/calibration/ercot192_arm_B`) — determination **NOT-YET**, fail set
**{C3a-2023, C3b-2023}**, C3c the single ledgered **CAVEAT ×3**.

| | result |
|---|---|
| **The defect is confirmed on this keeper** | The shipped row-grain gate rejects **0 of 636 / 636 / 652** CT bid rows. Vacuous in all three years. |
| **The corrected gate binds** | It excludes exactly **one** plant, `CT_PEAKER_South_Central_p6243`, in **2023 only**. |
| **The arm is MEASURED INERT** | Its entire effect across 26,280 solved hours is **1.2358 MW** moving CT_PEAKER → CC_CHP in **one hour** (2023 h2659), summing to zero. `system_2023.parquet` is **byte-identical**; 2024/2025 byte-identical 4/4. **C3a, C3b and C3c move in no year.** |
| **Every kill gate PASSES** | G-REPRO 12/12 · G-SHED 4/1/0→4/1/0 · G-C3c 58/22/1→58/22/1 · G-COAL148 0.0 TWh · G-SPUR 9/11/0→9/11/0 · G-SPAN 2.2e-05 % · G-OWNER · G-DOF · G-D2 · LOYO |
| **`p6243`'s 8 h min-down** | **CORRECT, and not a CAMPD artifact** — CAMPD is not even its source. The charter's fear is refuted on four instruments. |
| **Determination** | **NOT-YET {C3a-2023, C3b-2023}** — unchanged, exactly as the precommit said ex ante. |
| **Outcome** | Pre-registered branch **(i)**. **PROMOTED** under the direction-blind rule — **on legitimacy alone. No metric gain is claimed and none exists.** |

---

## 0. Shorthand

The task prompt opened this lane as **ERCOT-195** and the designated branch is
`claude/ercot-195-lever-selection-scssqc`. **`ercot-195` was already spent on
`main`** by the L-SCAR-SCREEN-2 session (2026-08-13), whose own record closes
*"Next shorthand: **ercot-202**."* This session is therefore **ercot-202** in
every artifact and log entry; the branch keeps its assigned name. Nothing else
about the lane changes.

---

## 1. What this lane is, and what card R-A permits

The **chartered ercot-187 successor**, open since 2026-08-10:
`FINDING-ercot186-rule18-grain-2026-08-10.md` §5 specified it, and ercot-187 was
diverted to the leap-day derive defect and the golden-hash attribution, so the
A/B it calls for had never been run.

The object is a **rule-18 `[R-PHYSICS]` licensing-gate correctness repair**, not
a residual lever. `ercot_faststart_pool_offer` is armed on the keeper, and its
eligibility test

```python
if float(getattr(gen, "min_down_hours", 0) or 0) > FASTSTART_POOL_MIN_DOWN_HOURS:
    continue
```

is evaluated on `econ*`/`peak*` bid rows, which fleet assembly deliberately
constructs with `min_down = 0` (a bid tranche must acquire no UC coupling). The
test is therefore **False for every row it can reach**, and the mechanism's
effective scope collapses onto its row universe `{"CT_PEAKER"}` — a hard-coded
class tuple, which is exactly what rule 18 forbids.

Card D3 fixed the reading in advance: *"an armed mechanism whose licensing gate
does not bind is a rule-18 defect independent of whether fixing it improves any
metric."* Card **R-A** (signed 2026-08-13) bars C3a-2023 spend and
C3b-2023-targeted determination rounds; this lane is neither, and **the C3b-2023
ceiling was stated in the precommit up front** (§0.3): Aug/Sep-2023 carries
**96.15 %** of the year's squared price-shape residual, so a run that were
perfect in all ten other months still reads **0.5923** against the 0.20 bar
(`ercot193_c3b_decomposition.json`). No arm in this lane can pass C3b-2023, and
none was claimed to.

---

## 2. SEAM PROOF — re-measured at this HEAD, on the run192 keeper fleet

`scripts/probes/ercot202_grain_seamproof.py` →
`results/calibration/ercot202_grain_seamproof.json`. **`ALL_ASSERTIONS_PASS =
true`; `ARM_IS_INERT = false`.**

Re-measured rather than inherited: ercot-186 measured on
`ercot185_shapedarm_B`, and the fleet basis has moved twice since (run191's
DAM-deriver repairs, run192's year-keyed coal `_peak` level). The ercot-186
probe is left byte-untouched — `scripts/probes/` is the frozen calibration
record (the ercot-187 discipline).

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **SP-2** CT bid rows / rejected by the shipped row gate | 636 / **0** | 636 / **0** | 652 / **0** |
| **SP-3** CT plants → eligible / **excluded** | 65 → 64 / **1** | 65 → 65 / **0** | 66 → 66 / **0** |
| **SP-3** plant min-down histogram | 1 h ×63, 2 h ×1, **8 h ×1** | 1 h ×64, 2 h ×1 | 1 h ×65, 2 h ×1 |
| **SP-4** armed == control | **False** | True | True |
| **SP-4** row-hours changed | **90,271** | 0 | 0 |
| **SP-4** rows priced, control → armed | **223 → 217** | 191 → 191 | 91 → 91 |
| **SP-4** max markup delta | **$1,709.62/MWh** | 0.0 | 0.0 |

**SP-1, restated and PASSING.** ercot-186 asserted the stamp equals the
ercot-176 max-over-rows read for *every* prefix, and that falsifier fired on 40
of 219. The precommit restated it as two separate facts, and both hold in all
three years:

* the stamp is **constant across every plant's rows** — PASS;
* it **equals the ercot-176 read on every prefix that HAS a committed tranche**
  (132 of 219 / 217 / 206) — PASS, zero mismatches.

The prefixes without a committed tranche are the defect's **second facet**, now
reported rather than gated: **40** of them diverge in each year, identically,
because assembly drops any tranche with `cap <= 0.5` MW, so a plant whose
committed band sits below that threshold emits no committed row and its physics
is recorded **nowhere in the fleet** — the ercot-176 row read returns 0 for it
too. The stamp does not depend on which tranches survive, so it repairs both
facets.

**SP-3b.** The two candidate reads differ on exactly **one** CT prefix
(`CT_PEAKER_Houston_p7325`) in every year and reach the **same eligibility set**,
so the SP-1 divergence is not separable on this gate's object. It binds only on
a tier with a LOWER bound (ercot-176's `[4, 8]` band is one).

**SP-5.** `FleetArrays` carries no field of either name and the only source
readers under `src/` are the model declaration, the writer and the licensing
read — PASS in all three years.

**Rule 24 bookkeeping, verified at HEAD**: the flag is cache-key registered and
dropped at its default — default key **`603c2498bf71d21d`** (unmoved, byte-equal
to ercot-186's record), armed key **`7ae1afee3aa73a63`** distinct.
`tests/iso/ercot/test_ercot_faststart_pool_offer.py` — **15 passed**.

### 2.1 P-2, the pre-registered scope claim: HELD on its own falsifier

The precommit killed the dead inertness prior and pre-registered the *measured*
scope instead, with an explicit falsifier: *"the excluded-plant set or the
moved-year set differs at this HEAD."*

**Neither differs.** Same single plant (`CT_PEAKER_South_Central_p6243`), same
single moved year (2023), 2024/2025 array-equal. The **magnitudes** moved —
90,271 row-hours rather than 76,845, and 223 → 217 rows priced rather than
173 → 168 — which is the fleet-basis drift the precommit named as the reason for
re-measuring rather than inheriting. (The extra rows are run188's
`ercot_econ_curve_top_refine`, which re-slices the econ ramp; the max markup
delta is **$1,709.62/MWh in both sessions**, to the cent.) No direction of price
effect was predicted, and none may be read from this table.

---

## 3. `p6243` — the charter's open question, SETTLED

`scripts/probes/ercot202_p6243_provenance.py` →
`results/calibration/ercot202_p6243_provenance.json`.

The charter asked: *is `p6243`'s assembled 8 h min-down **correct**, or a CAMPD
`Min_Down_Hours` artifact on a CT-classified plant?* — with rule 14
`[R-ACCURATE]`'s warning attached, *never assume it wrong because excluding the
plant is inconvenient.*

**Answer: it is CORRECT, and it is not a CAMPD artifact — CAMPD is not even its
source.** Four independent instruments agree.

**1. Provenance.** The value comes from `data/raw/reference/custom-bin-assignments.csv`,
not from CAMPD. That sheet classes plant 6243 **`ST_GAS`** and gives it
`Min_Run_Hours = 8`, `Min_Down_Hours = 8` — the standard gas-steam physics this
sheet carries, and consistent with the pool builder's own docstring
(*"ST_GAS by its 8-12 h min-down"*). The "CAMPD artifact" hypothesis dies on
provenance alone.

**2. EIA-860 — the plant is majority steam by nameplate.** Plant 6243 is
**Dansby**, and it is a mixed-prime-mover plant:

| generator | technology | prime mover | nameplate MW | online |
|---|---|---|---|---|
| 1 | Natural Gas Steam Turbine | **ST** | **105.0** | 1978 |
| 2 | Natural Gas Fired Combustion Turbine | GT | 49.1 | 2004 |
| 3 | Natural Gas Fired Combustion Turbine | GT | 49.1 | 2010 |

Total **203.2 MW** — exactly the bin sheet's `Nameplate_MW`. The 1978 steam
turbine is **51.7 %** of the plant.

**3. CEMS — the steam unit is the largest generator in every year.** CAMPD
unit-level gross load, `Roland C. Dansby Power Plant`:

| year | boiler (ST) | CT 2 | CT 3 | **steam share** |
|---|---|---|---|---|
| 2023 | 114.7 GWh | 54.1 | 54.0 | **51.5 %** |
| 2024 | 111.8 GWh | 39.1 | 31.1 | **61.4 %** |
| 2025 | 147.2 GWh | 46.2 | 43.7 | **62.1 %** |

An 8 h min-down is the right physics for that plant's dominant component.

**4. The codebase already names this plant as a coin flip.** `p6243` only enters
the pool's CT row universe at all because
`campd_bins._override_bin_class_from_eia923` replaces the curated class with the
EIA-923 dominant class per year — and for 2023 that margin is
**CT_PEAKER 50.1 % vs ST_GAS 49.9 %**, i.e. **0.2 percentage points**, in the
opposite direction to the CEMS record above. `eia860.mixed_fossil_plants`
already flags exactly this case, and its own source comment names the plant:
*"the dominant-share floor below which the plant is treated as genuinely mixed —
no single class earns the bin, so collapsing it to one class is a coin-flip that
can flip year-to-year (**e.g. Dansby 50/50 ST/CT**)."* `6243 ∈
mixed_fossil_plants(2023)` is **True**.

### 3.1 This is why the arm moves only 2023 — the whole of it

The per-year class override moves very few plants, and Dansby is the only one
whose curated min-down is not 1 h:

| year | gas plants reclassified by EIA-923 | which | curated min-down |
|---|---|---|---|
| 2023 | **3** | Powerlane CT→ST, Silas Ray CT→CC, **Dansby ST→CT** | 1, 1, **8** |
| 2024 | 1 | Silas Ray CT→CC | 1 |
| 2025 | 0 | — | — |

The arithmetic closes exactly: the curated CT count is 66; 2023 loses Powerlane
and Silas Ray and gains Dansby → **65 plants, 1 excluded**; 2024 loses Silas Ray
→ **65, none excluded**; 2025 → **66, none excluded**. The other two flips carry
min-down 1 h and would clear the 2 h bound either way.

### 3.2 What the gate is actually catching — and what is NAMED, not fixed

The corrected gate is right for **two independent reasons**: Dansby carries
genuine 8 h steam physics, *and* it should arguably not have been in the CT row
universe for 2023 at all. **A rule-18 physics gate is the only thing standing
between a 0.2 pp class coin-flip and a 1978 steam turbine being offered into a
pool defined as SCED-startable-intra-hour.** That is precisely what rule 18
exists for, and the vacuous gate could not do it.

**The bound was NOT moved to recapture the plant** — the ercot-176 discipline
(17 CC plants deliberately not recaptured) is standing and was not renegotiated.

Three items are **named and left untouched**, each needing its own precommit:

1. **The dispatch/scoring asymmetry.** `mixed_fossil_plants` neutralizes the
   coin flip on the **scoring** side (`apply_other_fossil_scoring`, whose own
   docstring says *"Dispatch is unaffected — the bin keeps its dominant-class
   offer curve"*), while **dispatch keeps the flipped class**. The scorer knows
   the assignment is unreliable; the offer path does not.
2. **Single-plant aggregation of mixed prime movers.** One LP unit blends a
   105 MW steam turbine with two 49 MW CTs, so the plant-grain physics read must
   return one number for two genuinely different technologies. Excluding the
   whole plant is the conservative and correct call at this grain, but it also
   withdraws the ~98 MW of genuine CT capability inside the same aggregate.
   That is a **fleet-representation** limitation, not a gate limitation.
3. **The sibling grain defect** at `model/commitment.py::_ra_bridge_unit_params`
   (the CAISO RA bridge) remains named and untouched (rule 25).

---

## 4. THE A/B — both arms registered, every gate passes, the arm is inert

Two full-span replays of the run192 keeper recipe on `replay_keeper.py`,
strictly sequential (rule 12), both registered (rules 15/16):

| | bundle | run id | determination |
|---|---|---|---|
| control | `ercot202_graincontrol_A` | `2026-08-14-ercot202-ctl-grain` | NOT-YET |
| arm | `ercot202_plantphysics_B` | `2026-08-14-ercot202-arm-plantphysics` | NOT-YET |

### 4.1 G-REPRO — the control reproduces the keeper exactly

All **12/12** committable hourly sidecars (`class_hourly` / `system` /
`reserve_family` / `storage` × 2023/2024/2025) are **byte-identical** to
`ercot192_arm_B` by sha256. HEAD drift is therefore excluded by measurement, and
every A/B difference below is the mechanism. This is the whole reason the
precommit required a same-HEAD control (§7 step 3), and it independently
re-confirms ercot-193's reproduction result on a fresh solve.

Both solves' own logs corroborate the seam proof from *inside* the LP:

* control — `physics gate min_down <= 2 h at row (pre-repair, vacuous) grain,
  0 plants excluded`, **223 / 191 / 91** pool rows;
* arm — `physics gate min_down <= 2 h at PLANT (ercot-186) grain, 1 plants
  excluded`, **217** rows in 2023.

That is SP-4's 223 → 217 reproduced in the live solve.

### 4.2 What the arm actually did

| year | sidecars identical (of 4) | verdict |
|---|---|---|
| 2023 | 3 / 4 — only `class_hourly` differs | `system_2023.parquet` **BYTE-IDENTICAL** |
| 2024 | 4 / 4 | **BYTE-IDENTICAL** |
| 2025 | 4 / 4 | **BYTE-IDENTICAL** |

The one differing frame contains exactly **two** changed rows:

| year | pass | class | hour | control MW | arm MW | Δ MW |
|---|---|---|---|---|---|---|
| 2023 | P1 | CC_CHP | 2659 | 3363.3655 | 3364.6016 | **+1.2358** |
| 2023 | P1 | CT_PEAKER | 2659 | 3556.4197 | 3555.1841 | **−1.2358** |

Total 2023 energy is unchanged (446.0816 TWh both arms). **That is the entire
measured effect of the mechanism.**

### 4.3 Why inertness is the finding, not a null

The seam proof measured this arm moving **90,271 row-hours**, withdrawing **6**
of `p6243`'s priced pool rows, at a max markup delta of **$1,709.62/MWh**. That
is a large offer-side move, and it produces a **1.24 MW** dispatch change and
**zero** price change.

The reason is visible in SP-6's row census: the withdrawn rows are one plant's
deep out-of-merit tranches — econ heat rates **13.18 → 21.55** MMBtu/MWh and
five `peak*` rows at **130.97** — which never clear at any price. Re-pricing
capacity the LP never dispatches changes nothing it clears on. **The repair
makes a vacuous rule-18 gate bind without disturbing the solution**, which is
the ideal outcome for a legitimacy correction and the reason branch (i) exists.

### 4.4 Kill gates — all live, all PASS

| gate | baseline (control) | arm | verdict |
|---|---|---|---|
| **G-SHED** (primary) | 4 / 1 / 0 | 4 / 1 / 0, identical hour lists | **PASS** |
| **G-C3c** max-zonal | 58 / 22 / 1 vs 181 / 53 / 31 | 58 / 22 / 1 | **PASS** |
| G-C3c demand-wtd (reported) | 57 / 22 / 1 | 57 / 22 / 1 | — |
| **G-COAL148** (live, D2 lineage) | 0.1213 / 0.1838 / 0.1095 TWh | rise **0.0 / 0.0 / 0.0** vs the 0.5 bar | **PASS** |
| **G-SPUR** | 9 / 11 / 0 | 9 / 11 / 0 | **PASS** |
| **G-SPAN** | — | max class energy move **2.2e-05 %** (2023 CT_PEAKER); 0 in 2024/25 vs the 0.5 % bar | **PASS** |
| **G-OWNER** | C3a-2024 −0.8 %, C3a-2025 −7.5 %, C3b-2024 0.135 | byte-identical | **PASS** |
| **G-DOF** | `n_entries` 18 / `n_residual` 6 | unchanged; zero new scalars | **PASS** |
| **G-D2** | D-4 FAIL rows `reliability_floor × CT_PEAKER` h14-21 ×3 yr | **identical A↔B**, no new row | **PASS** |
| **LOYO** | — | 2024/2025 byte-identical **is** the held-out evidence | **PASS** |

G-D2's baseline deserves one sentence, because both runs' legitimacy gate
reports `FAIL`: that is the **pre-existing** off-window-binding condition the
keeper already carries, and the keeper's and control's D-4 FAIL row sets are
identical. The precommit scored this gate as *"D-4 FAIL rows identical A↔B …
any new row is a failure"*, so the arm passes it. Nothing here is a regression
introduced by this session, and nothing here is repaired by it.

### 4.5 Determination, and what did NOT move

**NOT-YET, fail set {C3a-2023, C3b-2023}, on both arms — unchanged**, with C3c
the single ledgered CAVEAT ×3. Because `system_*.parquet` is byte-identical in
every year, **C3a-2023 (−33.2 %), C3b-2023 (0.604) and all three C3c tail counts
are numerically unchanged, not merely within tolerance.** No C3a-2023 claim is
made (Q-B final), no C3b-2023 round was run (card R-A), and the ~0.59
C3b-2023 ceiling stated in the precommit was never approached because nothing
moved.

### 4.6 Promotion — branch (i), on legitimacy alone

The precommit's **direction-blind rule** reads only (a) each live gate's
PASS/FAIL and (b) LOYO. All live gates PASS and LOYO clears, so the rule fires:
**PROMOTE**. Keeper → **`2026-08-14-ercot202-arm-plantphysics`**.

Stated plainly, as branch (i) requires: **the promotion buys no metric gain, and
none is claimed.** It is justified by the object alone — a keeper carrying an
armed mechanism whose licensing gate does not bind *is* the rule-18 defect,
whatever the numbers say (card D3). The two bundles are numerically identical in
every scored quantity, and both registrations say so, so the dashboard is never
read as two independent results.

Retention behaved exactly as pre-registered: registering the pair pruned
**`2026-08-06-run173b-event-cap-reconc`** and
**`2026-08-07-run176-control-offline-increment`** — the two the precommit named
before the fact.

### 4.7 RULE 26 IS NOT DISCHARGED, and the reason is measured

The precommit bound the promoting commit to deleting the transitional flag and
the pre-repair branch (rule 26 `[R-DELETE]`). **That cannot be done here without
breaking the keeper**, and the obstruction is a fact about the code, not a
preference:

`ScenarioConfig` is a **dataclass**, and `with_overrides` / `dataclasses.replace`
**raise `TypeError` on an unknown keyword**. The promoted keeper's `meta.json`
carries `ercot_faststart_pool_plant_physics` as a `prb_override`, so deleting
the field would make `replay_keeper.py` raise on this bundle — i.e. render the
keeper **unreplayable**, breaking every future control, re-gate and G-REPRO
check that the calibration lane depends on. Verified directly, not assumed.

**Named successor (its own precommit):** delete the field *and* the pre-repair
branch, making the plant-grain read unconditional, **and re-solve** so no bundle
references the flag.

The hazard rule 26 actually targets — *"a deprecated parameter that still parses
is a re-armable answer key"* — is **materially absent** here: this flag carries
**zero DOF**, no residual content, and no tunable value. It is a physics-grain
switch, not a fitted knob. That is a reason the deferral is safe, **not** a
reason to skip it; the successor stands.

---

## 5. HYGIENE — the ERCOT-137 anchoring convention: RE-FILED WITH A MEASUREMENT

`scripts/probes/ercot202_ercot137_anchoring.py` →
`results/calibration/ercot202_ercot137_anchoring.json`.

The ercot-192 DOF ledger left this open on the `coal_offer_margin_level /
_anchor` (ERCOT-137, limb A) entry: the identification pools the four subsets'
`bot_p50` **raw**, unanchored, while its registered anchor **1.7387** is the
three-year mean and the pool sits at the 2024/25 res-hours mean fuel **~1.7040**.

**What is new here is that the inconsistency is now grounded in the mechanism's
own identity, not in a foreign arithmetic.** `legacy_bins.py:1055-1059` applies

```python
mc[g, :] += coal_level - heat_rate[g] * coal_anchor - vom[g]
```

on top of an `mc` already carrying `heat_rate[g] * fuel[g,t] + vom[g]`, so the
offer the LP sees is

```
offer(g, t) = coal_level + heat_rate[g] * (fuel[g, t] - coal_anchor)
```

— i.e. **at delivered fuel == anchor the offer reduces exactly to `coal_level`**,
and the fuel-response slope is the unit's **own** assembled heat rate. The level
is therefore well-formed only if measured *at* the anchor. It is not. And this
is a **sibling inconsistency**, not an artifact of applying ERCOT-140's
arithmetic to it: ERCOT-139 removes its corpus's own measured fuel response and
ERCOT-140 anchors on its measured gas response; **ERCOT-137 alone pools raw**.

Resolved **per plant** rather than at one blended heat rate:

| | $/MWh | × band (±0.93) |
|---|---|---|
| capacity-weighted (HR 10.3411) | **+0.3588** | **0.386×** |
| minimum — Oak Grove (HR 9.49) | +0.3293 | 0.354× |
| maximum — San Miguel (HR 11.25) | +0.3904 | 0.420× |

**All ten coal plants sit inside the band, so arming is unchanged and nothing
was re-derived here** (rule 23 is not engaged by this session). The repair is
solve-affecting on every coal `_mustrun` row and therefore needs its own
precommit, A/B and gates; folding it into this lane's A/B would have made that a
two-delta comparison.

**An owner question is surfaced rather than taken.** Rule 23
`[R-FROZEN-DERIVE]` licenses a re-derivation when the **source data** updates
and forbids one because a residual moved. This trigger is **neither**: it is a
defect in the derivation's own convention, measured against the mechanism's own
identity, with no residual consulted anywhere. Whether that is an admissible
re-derivation trigger is an owner ruling, not a session call.

---

## 6. Governance

* **Rule 15 `[R-DASHBOARD]`** — both runs registered, committed and pushed in
  **this** session; the FINDING and the dashboard carry the result. Both bundles
  carry `metrics.json`, `legitimacy_diagnostics.json` and
  `calibration_attestation.json` (max-zonal C3c basis, `gen_ercot202_attestation.py`).
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one invocation and one bundle
  per arm. No single-year anything.
* **Rule 22 `[R-HOLDOUT]`** — every solve, score and read stayed inside
  {2023, 2024, 2025}. ERCOT holds no `complete` and no `final` marker, none was
  sought, and no `calibration-complete.json` re-key applies.
* **Rule 23 `[R-FROZEN-DERIVE]`** — **not engaged.** No derive was re-run and no
  artifact re-derived; this session changed only which rows are licensed to read
  a frozen artifact. The §5 hygiene item is a measurement, and its potential
  re-derivation is explicitly deferred to a named successor.
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field (merged at
  ercot-186), cache-key registered dropped-at-default and **verified at this
  HEAD**: default key `603c2498bf71d21d` unmoved, armed key `7ae1afee3aa73a63`
  distinct. Recorded in both bundles' `run_config.json`.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated throughout; only ERCOT's keeper
  shard, status part and matrix shard were touched. The sibling grain defect at
  `model/commitment.py::_ra_bridge_unit_params` (CAISO RA bridge) is **named and
  untouched**. No cross-ISO verdict minted.
* **Rule 26 `[R-DELETE]`** — **NOT discharged; see §4.7 for the measured
  obstruction and the named successor.** Recorded here rather than quietly
  skipped.
* **Rule 27 `[R-PUSH]`** — this session wrote **no** core source file: the
  mechanism substrate was already merged at ercot-186 and is byte-unchanged
  here. New files only (probes, attestation generator, docs, artifacts). Every
  push was blob-verified where it touched a ≥300-line file, and **no push ran
  while an LP solve was in progress** except small text/sidecar packs
  (≤3.6 MB), with the solve PID confirmed alive after each.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (a) the DO-NOT-REDO check preceded the
  precommit (the cell was `O`, nothing in the family adjudicated `R`/`I`/`G`);
  duty (b) `ercot_faststart_pool_plant_physics` stamped **`O → K`** with
  evidence in **this** session; duty (c) the row already existed (landed with
  the field at ercot-186); duty (d) no cross-ISO verdict. The shard's keeper and
  gates stamps and the §5.1 prose header were re-stamped on promotion;
  `check_mechanism_matrix.py` reports integrity OK, keeper stamps matching and
  prose headers matching.
* **GitHub Actions** — nothing offloaded; both solves ran in-session.

**Test state.** `tests/iso/ercot/test_ercot_faststart_pool_offer.py` — **15
passed**, including the four grain-repair cases.

**Inherited, unexpired.** The ercot-188/E2 **P0 bit-identity forfeiture** stands:
`ercot_econ_curve_top_refine` writes heat rates into the P0 objective on this
keeper lineage, so the offer-surface family's P0 bit-identity proof remains
forfeited and control-vs-arm differences are isolable by argument, never by
proof. Stated so §2's seam proof is not over-read.

**Next shorthand: ercot-197.**

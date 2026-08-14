# FINDING — ercot-196: the rule-18 grain repair, SOLVED — and `p6243` is not what the charter feared

> **STATUS: IN PROGRESS — this record is INCOMPLETE.** §1–§3 and §5 are final
> (seam proof, the `p6243` adjudication, and the ERCOT-137 hygiene re-file are
> all measured and settled). **§4, the A/B, is NOT YET WRITTEN**: the control
> and arm solves were still running when this file was first committed, so the
> headline table, the gate table and the governance block carry placeholders.
> **No A/B result, gate verdict, determination or promotion may be read from
> this file until this banner is removed.** Committed at this stage only
> because the session's settled measurements should not sit untracked.

**Session ercot-196, 2026-08-14. ERCOT only (rule 25).**
Branch `claude/ercot-195-lever-selection-scssqc` (the branch name carries a
stale shorthand — see §0).
Pre-registration:
`docs/PRECOMMIT-ercot196-rule18-grain-successor-2026-08-14.md`, pushed at
`f73b9a1` **BEFORE** any measurement, derive or solve.

Keeper at session start: **`2026-08-12-run192-arm-coal-peak`**
(`results/calibration/ercot192_arm_B`) — determination **NOT-YET**, fail set
**{C3a-2023, C3b-2023}**, C3c the single ledgered **CAVEAT ×3**.

<!-- HEADLINE-TABLE -->

---

## 0. Shorthand

The task prompt opened this lane as **ERCOT-195** and the designated branch is
`claude/ercot-195-lever-selection-scssqc`. **`ercot-195` was already spent on
`main`** by the L-SCAR-SCREEN-2 session (2026-08-13), whose own record closes
*"Next shorthand: **ercot-196**."* This session is therefore **ercot-196** in
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

`scripts/probes/ercot196_grain_seamproof.py` →
`results/calibration/ercot196_grain_seamproof.json`. **`ALL_ASSERTIONS_PASS =
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

`scripts/probes/ercot196_p6243_provenance.py` →
`results/calibration/ercot196_p6243_provenance.json`.

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

<!-- AB-SECTION -->

---

## 5. HYGIENE — the ERCOT-137 anchoring convention: RE-FILED WITH A MEASUREMENT

`scripts/probes/ercot196_ercot137_anchoring.py` →
`results/calibration/ercot196_ercot137_anchoring.json`.

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

<!-- GOVERNANCE -->

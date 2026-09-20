# RESULT — SPP-68: the wind curtailment CEILING, re-tested on all seven years against KEEPER 14. **REJECTED.**

**Verdict: the lane's own pre-registered kill condition fired on THREE of four limbs.
`spp_curtailment_ceiling` moves cell `O` → `R`. SPP's keeper is UNCHANGED at
`2026-09-20-spp-67-yearown-rate`. The promotion question is put to the owner in §9 and was
OPEN when this was written.**

PRECOMMIT: `docs/handoffs/PRECOMMIT-spp-68-curtailment-ceiling-retest-2026-09-20.md`, pushed at
`05b2231da6e2e70bf9a122cece864a7673e2b2f7` **before any shard was launched**.
Probes: `scripts/probes/_spp68_ceiling_phase0.py` (zero LP), `_spp68_arm_vs_control.py`,
`_spp68_compose_span.py`. Attestations: `scripts/gen_spp68_attestation.py`.
Registered: `2026-09-20-spp-68-ceiling-span` (2023-2025) + `2026-09-20-spp-68-rung-ceiling`
(2019-2022), both **NOT-YET**.

---

## 1. WHAT IT BUYS — stated first, at full magnitude, because it is large and real

Wind is the whole point of the mechanism and it does what its arithmetic says.

| year | bench (EIA-930) | keeper 14 | **ARM** | Δ wind | excess now | **excess ARM** |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 77.0300 | 78.2784 | **70.5989** | −7.6794 | +1.2484 | **−6.4311** |
| 2020 | 82.0300 | 90.6257 | **81.7145** | −8.9112 | +8.5957 | **−0.3155** |
| 2021 | 92.8600 | 101.8115 | **92.6159** | −9.1956 | +8.9515 | **−0.2441** |
| 2022 | 107.4400 | 117.4226 | **107.0530** | −10.3696 | +9.9826 | **−0.3870** |
| 2023 | 103.0500 | 111.9786 | **101.8483** | −10.1303 | +8.9286 | **−1.2017** |
| 2024 | 109.3200 | 121.4587 | **110.3348** | −11.1239 | +12.1387 | **+1.0148** |
| 2025 | 110.4600 | 121.9946 | **110.5287** | −11.4659 | +11.5346 | **+0.0687** |

**Six of seven years land within 1.21 TWh of actual**, against +8.60…+12.14 TWh now. That is the
largest single C1 improvement any SPP lever has produced. **It is not why this is `R`.**

## 2. WHY IT IS REJECTED — the pre-registered kill condition, limb by limb

### K-1 OVER-REMOVAL — **TRIPPED on 2019**

2019's arm wind lands **6.4311 TWh BELOW** the EIA-930 bench (limit: 2.00). The ceiling removes
energy SPP **actually delivered**.

The cause was measured at phase 0 and pre-registered, and it is **structural, not a level**: the
ceiling's depth is **pooled** (0.288137, centred on a ≈9.65 % published share) while keeper 14's
gross-up is sized by **each year's own** published rate. Expressed as a percentage of the same
year's gross-up headroom, the removal is:

| year | own rate | removal ÷ headroom | numerator (removal, TWh) | denominator (headroom, TWh) |
|---|---:|---:|---:|---:|
| **2019** | **1.591 %** | **614.8 %** | 7.656 | 1.2453 |
| 2020 | 9.650 % (ref) | 103.4 % | 9.063 | 8.7627 |
| 2021 | 9.650 % (ref) | 102.0 % | 10.112 | 9.9177 |
| 2022 | 9.357 % | 102.9 % | 11.416 | 11.0909 |
| 2023 | 8.493 % | 112.6 % | 10.766 | 9.5648 |
| 2024 | 10.561 % | 92.1 % | 11.883 | 12.9073 |
| 2025 | 9.896 % | 99.3 % | 12.044 | 12.1307 |

At 100 % the two mechanisms exactly cancel and wind returns to its delivered basis. Above 100 %
the ceiling eats delivered energy — 2.9 % of it in 2022, 12.6 % in 2023, ≈5.1 TWh in 2019.

This is a **rule 19 `[R-ONE-MECH]`** finding: two mechanisms answering *"how much wind is there"*
on inconsistent bases. **Both consistent repairs are refused in advance and neither was
attempted**: a per-year depth by rule 1 `[R-STRUCT]` condition (b) (one config across every scored
year), re-cutting the pooled depth by condition (c) (never swept against a gate).

### K-2 LOAD-BEARING REGRESSION — **TRIPPED, in all three keeper years**

| year | C3b keeper → ARM | C3a keeper → ARM |
|---|---|---|
| 2019 | 0.128 → 0.147 (PASS) | +7.7 % → +9.8 % (PASS) |
| 2020 | 0.273 → 0.357 (FAIL→FAIL) | +19.3 % → +25.9 % (FAIL→FAIL) |
| 2021 | 0.245 → 0.306 (FAIL→FAIL) | +2.7 % → **+11.6 % (PASS→FAIL)** |
| 2022 | 0.207 → 0.268 (FAIL→FAIL) | −4.0 % → +6.0 % (PASS) |
| **2023** | **0.168 → 0.250 (PASS→FAIL)** | +0.1 % → +9.6 % (PASS) |
| **2024** | **0.156 → 0.242 (PASS→FAIL)** | −1.6 % → +7.0 % (PASS) |
| **2025** | **0.157 → 0.265 (PASS→FAIL)** | +1.3 % → **+10.7 % (PASS→FAIL)** |

C3b worsens in **all seven** years and flips a load-bearing PASS → FAIL in **all three** keeper
years. Mean LMP rises in every year (+$0.43 … +$4.42).

### K-3 THE PRICE FLOOR — **TRIPPED in all six eligible years**

| year | keeper h ≤ −25.9 | ARM | ACTUAL RT h < 0 | ARM min price |
|---|---:|---:|---:|---:|
| 2019 | 0 | 0 | 547 | +16.580 |
| 2020 | 169 | **0** | 936 | +13.816 |
| 2021 | 494 | **0** | 1108 | +15.786 |
| 2022 | 483 | **0** | 995 | +17.392 |
| 2023 | 334 | **0** | 992 | +18.071 |
| 2024 | 346 | **0** | 1172 | +15.783 |
| 2025 | 293 | **0** | 1018 | +19.681 |

The model was **already** at 0.18–0.50× the market's negative-hour count. The arm takes it to
**zero**, and the minimum price from exactly −26.000 to **+13.8…+19.7**. This is the largest single
structural cost and it moves **away** from the market, not toward it.

### K-4 NEW FORCING — **HOLDS, and IMPROVES. Reported because it contradicts the prior screen.**

| year | keeper slack (MWh) | ARM slack | Δ | keeper hrs | ARM hrs |
|---|---:|---:|---:|---:|---:|
| 2022 | 274.5831 | 221.8979 | **−52.6852** | 3 | 2 |
| 2024 | 802.8046 | 784.6504 | **−18.1542** | 2 | 2 |
| 2025 | 76.8817 | 71.6648 | **−5.2169** | 1 | 1 |

Every other year is 0.0000 in both. Dump is 0.0000 everywhere. **SPP-63's G-4 failure
(0 → 211.208 MWh) does NOT reproduce on keeper 14** — the arm creates no new slack hour anywhere
and reduces slack wherever it exists. The lane predicted this limb might trip; it did not.

## 3. THE CHANNEL — why no depth could have fixed this, settled by a natural experiment

Four independent prior diagnoses agree (SPP-64 §3, SPP-47, SPP-50 §6, SPP-51): SPP wind is a
**bounded decision variable** bid at a flat `−ira_ptc_wind`, so it is the **only** unit that can
set a negative price, and **a unit held AT its bound is never marginal**. Lowering the bound
removes the model's only negative price-setter — at any depth.

**SPP-68 adds the experiment that settles it without a solve, and it was already in the committed
data: 2019.** Its gross-up headroom is **1.2453 TWh** against 8.8–12.9 elsewhere, and it already
carries **zero** negative hours and a minimum price of **+4.500**. The model's negative-price
regime *is* the gross-up headroom being spilled. Remove the headroom, remove the regime.

**The price rise tracks the negative hours removed, not the TWh removed** — which is why the lane's
own 2019 price prediction was wrong (§6): 2019 loses 7.68 TWh of wind and only $0.43/MWh, because
it had no negative hours to lose.

## 4. THE CEILING REMOVES THE RIGHT AMOUNT FROM THE WRONG HOURS

Measured **after** the PRECOMMIT was pushed and **before** any arm landed, so it cannot have been
fitted to a result. Both quantities binned on the net-load decile the ceiling itself keys on.

| year | corr(excess, removal) | excess in d0 | removal in d0 | concentration ratio |
|---|---:|---:|---:|---:|
| 2019 | 0.2024 | 85.54 % | 23.94 % | 0.280× |
| 2020 | 0.6165 | 52.16 % | 23.97 % | 0.460× |
| 2021 | 0.6581 | 46.90 % | 23.03 % | 0.491× |
| 2022 | 0.6670 | 44.54 % | 23.14 % | 0.520× |
| 2023 | 0.7007 | 48.47 % | 22.91 % | 0.473× |
| 2024 | 0.6674 | 41.88 % | 21.45 % | 0.512× |
| 2025 | 0.6047 | 45.69 % | 22.01 % | 0.482× |

The model's phantom wind sits **41.9–52.2 %** in the lowest net-load decile; the ceiling puts only
**21.5–24.0 %** of its removal there. It is broad and shallow — mean multiplier **0.914–0.917**,
deepest cut **0.712**, and the clip at 0 **never** binds (depth × max share = 0.288137 < 1, so no
hour is ever zeroed). Real congestion curtailment is the opposite shape: specific resources to zero
in specific hours behind a binding constraint. **The ceiling reproduces curtailment's annual VOLUME
and a modest tilt; it does not reproduce its CONCENTRATION.**

## 5. WHERE THE ENERGY WENT, and the footprint

Thermal absorbs the removed wind essentially one-for-one: **Σ thermal ÷ |Δ wind| = 0.997–1.000** in
every year.

| year | gas $ | COAL_PRB | COAL_LIGNITE | CC_REGULAR | CT_PEAKER | ST_GAS |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 2.57 | +3.8205 | +0.4055 | +2.3626 | +0.7591 | +0.1859 |
| 2020 | 2.03 | +2.8907 | +0.5868 | +5.1225 | +0.0545 | +0.0768 |
| 2021 | 3.72 | +6.6509 | +0.7501 | +1.4738 | +0.3163 | +0.0132 |
| 2022 | 6.45 | +7.6911 | +1.2125 | +1.4381 | +0.0950 | −0.0952 |
| 2023 | 2.54 | +3.6307 | +0.7911 | +4.4529 | +0.9239 | +0.1388 |
| 2024 | 2.19 | +3.8490 | +0.3842 | +5.2371 | +0.9012 | +0.5209 |
| 2025 | 3.52 | +5.9389 | +0.7288 | +4.0323 | +0.3357 | +0.1354 |

**The split is gas-price dependent**, which is merit order behaving correctly: at $6.45 gas (2022)
coal takes 74 % of the removed wind; at $2.03 (2020) CC takes 58 %.

**Footprint confinement — the ceiling claims WIND on both SPP zones and nothing else, and that
holds.** Nuclear and biomass move **exactly 0.0000 TWh** in every year; the largest non-thermal
drift anywhere is solar **+0.0457 TWh** (2025), with hydro ≤ 0.0044 and oil ≤ 0.0228 — second-order
dispatch responses to a changed net load, not the ceiling acting on them (solar takes no ceiling by
construction, `spp_curtail_multipliers` returns an explicit 1.0 array). Max non-thermal |Δ| is
**≤ 0.4 %** of the mechanism's own effect.

## 6. THE LANE'S OWN PREDICTIONS, SCORED HONESTLY

**P-1 wind — 7 of 7 HIT**, and this is the headline of the phase-0 method: the zero-LP arithmetic
predicted every solved year to within **0.0004–0.0638 TWh** (tolerance ±0.25, ±0.50 in 2019).

| year | predicted | actual | \|miss\| |
|---|---:|---:|---:|
| 2019 | 70.6223 | 70.5989 | 0.0234 |
| 2020 | 81.7418 | 81.7145 | 0.0273 |
| 2021 | 92.6605 | 92.6159 | 0.0446 |
| 2022 | 107.1168 | 107.0530 | 0.0638 |
| 2023 | 101.8479 | 101.8483 | **0.0004** |
| 2024 | 110.3313 | 110.3348 | 0.0035 |
| 2025 | 110.5410 | 110.5287 | 0.0123 |

**P-2 thermal split — 2 of 7 in band. WRONG, and wrong in a specific, informative way.** The
PRECOMMIT put COAL_PRB at 0.45–0.70 of |Δ wind| and CC_REGULAR at 0.18–0.42 in *every* year, using
SPP-63's 2025 measurement as the prior. It flagged the risk that keeper 13's coal floor would tilt
absorption toward gas — and then **still wrote a single band across all years**, which is the
error. Measured, the split swings with gas price: COAL_PRB 0.324 (2020, $2.03) to 0.742 (2022,
$6.45). A gas-price-conditioned band would have been right; a constant one could not be.

**P-3 C3a — 6 of 7 HIT.** The miss is **2019**: the lane predicted +12 to +19 % (a FAIL) and it
came in at **+9.8 % (PASS)**, a rise of only +2.1 pts. The reasoning error is named in §3 — the
lane sized the price effect off the TWh removed when it actually tracks the **negative hours
removed**, and 2019 had none.

**P-4 C3b — 5 of 7 inside the +0.04…+0.09 band; direction correct 7 of 7.** 2019 came in low
(+0.019) and 2025 high (+0.108). For the three keeper years the PRECOMMIT's explicit ranges were
2023 0.21–0.26 → **0.250** ✓, 2024 0.20–0.25 → **0.242** ✓, 2025 0.20–0.25 → **0.265** (just
above).

**P-5 negative-price collapse — HIT, 6 of 6.** Predicted "< 50 in every year"; measured **0**.

**The strongest counter-evidence the lane raised against itself was wrong, and it is scored as
such.** The PRECOMMIT flagged that 2019 has the smallest headroom AND the best C3b, which would
argue the ceiling should *help* price shape. It does not: C3b worsens in all seven years. The
cross-year correlation was confounded, as the PRECOMMIT itself said, and the within-year arm-vs-
control measurement beats it.

## 7. GOVERNANCE

* **Rule 29(b) form 4** — the control is keeper 14's / the rung's **committed bundle**, never a
  control solve. G-DRIFT found exactly **one** changed file on the whole audited solve path since
  the keeper's basis sha: `data/raw/_validation-source/nyiso_offer_level_dispersion.json`, a NYISO
  artifact SPP does not have — **INERT**.
* **Rules 21 / 24 DOF** — zero free parameters added. `spp_curtailment_ceiling` is a registered
  boolean, `spp_curtail_depth_wind` a registered float **at its declared dataclass default**,
  never swept. `build_dof_ledger.py --iso SPP --check` reads **current** on keeper 14 (5 entries /
  3 residual) and the arm introduces no entry.
* **Rule 23** — the depth is **frozen**. Its source rows are unchanged, and its identification
  `depth_y = published_share_y / wms_y` is a ratio in which the potential cancels, so keeper 14's
  year-own gross-up cannot move it. Reconciled on keeper 14's own potential it reproduces SPP-58's
  per-year values to **≤ 0.0015** — which validates the construction even as it rejects the arm.
* **Rule 25** — `offer_curve_by_group` SHA-256 **`090abd793b5fa5a7`**, byte-identical to keeper
  14's. Default-off byte-identity proven before the solve by construction (five source gates) and
  by census (46 committed run configs, 38 carry the field, **0** arm it in any ISO).
* **Rule 19** — verified in source before the solve: `data/renewables.py` skips
  `_oversupply_uncurtailed_cf` whenever the ceiling is armed, so the two can never both be live.
* **Rules 32 / 34 / 36** — seven shards, **one per year 2019-2025**, all at pinned HEAD
  `05b2231d`, each pushing its **full** bundle including `dispatch/<year>_P1.parquet`
  (`git ls-tree` returned 16 files for every leg). **The parent ran no LP.**

## 8. RETRIEVABILITY (rule 34(e)) — READ THIS BEFORE COSTING ANY FOLLOW-UP

**What is on `main`, and therefore permanent:** both registered composites,
`results/calibration/spp68_ceiling_span/` and `spp68_ceiling_rung/`, in their rule-15 slim shape
(`hourly/` sidecars + `run_config*.json` + `meta.json` + `metrics.json` +
`legitimacy_diagnostics.json` + `calibration_attestation.json`), plus both registry sidecars and
both run payloads.

**What is NOT:** the seven per-year leg bundles, which are **gitignored** in the parent tree (rule
32(d), discharged by `.gitignore` and never by `rm` — rule 31 `[R-RETAIN]`). Their shard branches
are **transport, not storage** (rule 33(f)(1)): the environment cuts an unmerged shard branch when
the parent's PR merges, and this lane's parent branch has already auto-merged once. The provenance
SHAs below identify which commit produced which leg; **they are not a recovery route, and any leg
not inside the registered composites must be costed as a RE-SOLVE (≈3-6 min per year).**

| year | shard branch | commit (provenance only) |
|---|---|---|
| 2019 | `claude/spp68-ceiling-2019` | `ab03fe06444b572d9c0009946d6b1383632a04ad` |
| 2020 | `claude/spp68-ceiling-2020` | `edae5ab8675e813482ef5c9a88c49ebc4be07bff` |
| 2021 | `claude/spp68-ceiling-2021` | `3696167ad7b4b2d512ae29354e8471007af7f6f7` |
| 2022 | `claude/spp68-ceiling-2022` | `4194309678f086e4e7f891918d87585f3b55a4ce` |
| 2023 | `claude/spp68-ceiling-2023` | `c25b2541fd6623e3f0b2b022def51ef13b42a25b` |
| 2024 | `claude/spp68-ceiling-2024` | `84944f0d61854231420dd6c53b4e9fbfecdde30b` |
| 2025 | `claude/spp68-ceiling-2025` | `5dd51f4f9590e7931a30d238b02e886e926a04e0` |

**The rule-33(d) hazard reproduced, and it is why the column above says "provenance only".** Two
shards force-pushed their branches AFTER the parent had already fetched and verified their bundles
— their own final reports name `1ec595e` (2020) and `2ba2431d` (2021), not the SHAs above. The
bytes this lane measured, composed, scored and registered are the ones at the SHAs in the table;
the branches have since moved. This is exactly the nyiso-229 behaviour rule 33(d) records, it cost
nothing here because the fetch-verify-then-archive order was followed, and it is one more reason a
shard branch is never a recovery route.

**All seven shards are ARCHIVED** (rule 33 `[R-SHARD-ARCHIVE]`), each after the parent had fetched,
checked out and verified its bundle (config signature on all six/seven fields + `git ls-tree`
returning 16 files). None was left alive. Solve cost, reported: **178-256 s per year**, peak
5.36 GiB — every leg far inside rule 32(b)'s 20-minute ceiling.

**No shard branch deletion was attempted** (rule 33(f)(5): the credential returns HTTP 403 on a ref
delete). The seven `claude/spp68-ceiling-<year>` refs are the owner's to clear if they want them
gone; the environment cuts them on its own when this lane's PR merges.

**Everything a promotion needs is already on `main`** — the composites are registered, so a
promotion is a keeper-shard edit plus `build_status.py`, with **zero re-solves**.

## 9. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — asked explicitly, and open

**The lane recommends AGAINST promotion**, on its own pre-registered kill condition: three of four
limbs tripped, both composites read NOT-YET, and the price channel is structurally wrong rather
than merely mis-levelled.

**But the owner's standing instruction on the previous SPP promotion was:** *"If structural
integrity improves but gates regress that may still be a keeper."* So the trade is put plainly:

| | keeper 14 | this arm |
|---|---|---|
| wind excess, 7 yr | +1.25 … +12.14 TWh | **−6.43 … +1.01 TWh** (6 of 7 within 1.21) |
| C3b, keeper years | 0.168 / 0.156 / 0.157 (PASS ×3) | 0.250 / 0.242 / 0.265 (**FAIL ×3**) |
| negative-price hours | 293–494 (market: 992–1172) | **0** |
| slack | 76.9 / 274.6 / 802.8 MWh | **falls** in all three |
| determination | CALIBRATED | **NOT-YET** |

**Nothing is deleted and nothing needs to be.** The composites are on `main`; a promotion costs no
LP. The seven gitignored leg bundles die with this container, and nothing depends on them.

## 10. WHAT IS STILL OPEN

* **R-bc is NOT closed.** The LP still spends 90.00–100.05 % of the gross-up headroom. What `R`
  forecloses is re-arming *this flag* and re-cutting *this depth* — nothing else. Note that
  SPP-51 §3 already killed the per-hour wind cap **row** at zero LP (identical feasible region as
  the bound, so its dual never enters λ), so the only live successors are a **finer SPP topology
  carrying the real export constraints**, or something else entirely.
* **The pooled-depth / year-own-rate inconsistency (§2) is a live design question** independent of
  this flag: any future curtailment mechanism must be sized on the same basis as the gross-up it
  is removing, or it double-counts in exactly the way 2019 shows.
* R-ba, R-be and C3c are untouched.
* The separate `[R-HOLDOUT]` footprint sweep is
  `docs/handoffs/FINDING-spp-68-deleted-rule-footprint-sweep-2026-09-20.md` — five live instances,
  the largest a hard `SystemExit` gate in `run_capacity_hindcast.py`. Filed as cards; nothing
  edited outside SPP.

## 11. TRAPS HIT, recorded so the next lane does not rediscover them

* **`build_dof_ledger.py <bundle>` WRITES unless `--check` is passed.** Running it without
  `--check` against the committed keeper bundle rewrote
  `spp67_yearown_span/calibration_attestation.json` (309 lines reordered). Reverted immediately
  with `git checkout --`; the keeper bundle is clean. **Use `--check` on a committed bundle.**
* Trap (l) reproduced exactly: `check_registry_payload_parity.py` walks the **filesystem**, so the
  seven gitignored leg dirs turn it RED locally while CI stays green. All seven unmapped dirs were
  confirmed to be this lane's own before proceeding — which is the check rule 31 requires, and the
  RED is **not** to be "fixed" by deleting a result.
* Trap (i) reproduced: a composed bundle's `calibration_flags.years` stays at the FIRST leg's year
  and must be patched. `shared_inputs` was **absent in keeper 14 too**, so that half of the trap
  did not apply here — worth knowing before hunting for it.

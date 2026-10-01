# PRECOMMIT (pjm-h7) — the JOINT arm: measured committed basis + re-centred `gas_mid`

**Session** `pjm-h7` · **ISO** PJM · **Date** 2026-09-14 · **Base** `origin/main` @ `c6c70190`
**ZERO LP IN THE PARENT** (rule 32 `[R-SHARD]` (a)). Every number below is
`run_calibration.run_year(fleet_only=True)` on the keeper bundles' own `meta.json`
recipes, artifact reads and code audits — the rule 29 `[R-SCREEN]` clause-0 path.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**

Chartered by the **OWNER RULING 2026-09-14** opening the `gas_mid` re-centring, which had
been escalated by `docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md` §9 and again by
`docs/RESULT-pjm-h6-route-a-replace-screen-2026-09-14.md` §5 and held inside the
owner-declared-closed **pjm-142 frontier**. The frontier's own closure note names the
re-opening condition — *"a NEW defect or a NEW measured identification with its own charter"* —
and this lane presents both: the rule-23 `[R-FROZEN-DERIVE]` wart (§1) and pjm-170's measured
EIA-923 delivered coal (§2). The ruling is the authority; this paragraph is the record of it.

This document is written **before any solve** and carries every number the lane will cite.

---

## 1. THE OBJECT — and the correction to h5 §9 that should be read first

The PJM bituminous supply passthrough sigmoid. Its LIVE resolved parameters, read off the
model's own `coal_sigmoid_params` resolver on the keeper's own config (not off a table
restated here):

| | floor | ceil | **gas_mid** | slope |
|---|---:|---:|---:|---:|
| `COAL_SIGMOID_DEFAULTS[("PJM","bituminous")]` | 0.76 | 1.32 | **3.40** | 2.5 |
| keeper override `coal_bit_sigmoid_overrides` | **0.65** | — | — | — |
| **LIVE RESOLVED (both keeper recipes, all six years)** | **0.65** | **1.32** | **3.40** | **2.5** |

**CORRECTION TO THE INHERITED DOCS, stated because it changes what a reader thinks the
object is:** h5 §9 reports the probe holding "floor 0.65" while `COAL_SIGMOID_DEFAULTS` ships
**0.76**. Both are right and neither is the whole story — the keeper *overrides* the floor to
0.65 in `coal_bit_sigmoid_overrides`. So the live curve is **one parameter further from its
table default** than either document says on its face. The passthrough numbers in h5 §9 are
unaffected (that probe resolved the live params at runtime), and this lane reproduces them
independently in §3.

**Provenance, as it stands in `scenarios.py` today:**

```
floor 0.82 -> 0.80 (run 19) -> 0.76 (2026-06-17) -> 0.65 (keeper override)   cited, residual-tuned
ceil  1.25 -> 1.32 ("PJM run 16: trims the dear-gas-2025 BIT over-run")      cited, residual-tuned
slope 2.5                                                                    generic default
gas_mid 3.40                                                                 *** NO DERIVATION ANYWHERE ***
```

`gas_mid` is the only parameter of the four with **no provenance comment of any kind**, and it
matches neither its own derive script nor the model's own fuel prices. That is the rule-23
`[R-FROZEN-DERIVE]` defect, and it lives inside an 8/8 keeper.

## 2. THE OPERAND IS DERIVED, NEVER CHOSEN (rule 21 `[R-DOF]`)

`derive_coal_sigmoid.py`'s own construction is `gas_mid = deliv × COAL_HR / CC_HR`, i.e. the
coal-vs-gas-CC merit crossover. Three values exist; the live one is none of them:

| basis | delivered coal $/MMBtu | `gas_mid` | admissible? |
|---|---:|---:|---|
| `derive_coal_sigmoid.py` at HEAD (ACR regional f.o.b. ÷ 0.85) | 4.307 | 7.08 | **NO** — pjm-170 measured this reconstruction **+54.6 % over** the model's own receipts; rule 14 `[R-ACCURATE]` bars transcribing an input known wrong |
| **the model's OWN measured EIA-923 receipts** (243 DIRECT rows, cap-wtd, pjm-170 §2.1) | **2.786** | **4.58** | **YES — the arm** |
| LIVE REGISTERED | — | 3.40 | **NO** — no derivation exists to defend it |

**ONE admissible operand, fixed before any solve, never swept.** Any value chosen *between*
3.40 and 7.08 because it scores well is precisely the fitted adder rules 1 `[R-STRUCT]` /
13 `[R-MEASURED]` forbid, and is refused. If the screen reads badly the answer is a root cause,
not a second centre — **this lane will not return with a swept value.**

**Rule 13's forward test is met:** 4.58 is a formula over the model's own delivered-fuel array,
so it regenerates for a forecast year from forward fuel prices and responds to changed
conditions. It is an input, not an outcome.

**What is NOT touched, and why** (rule 19 `[R-ONE-MECH]`, and the DO-NOT-REDO ledger):
the **ceil** alone is adjudicated **R** (pjm-170: C3a PASS → FAIL); the **full re-derivation**
`{floor 0.50, ceil 1.00, gas_mid 7.08, slope 1.0}` is killed at zero LP (pjm-h2b: coal cheaper
in all six years, 2020 the wrong way). `floor` / `gas_mid` / `gas_slope` remain OPEN per the
matrix; this lane moves **`gas_mid` and nothing else**, verified in §3 G-2.

## 3. PHASE 0 — ZERO LP, FOUR LEGS PER YEAR, ALL SIX YEARS

`scripts/probes/_pjm_h7_gasmid_joint.py`: 24 `fleet_only` rebuilds on the keeper bundles' own
recipes (2020-2022 → `pjm_d4_4_TP`, 2023-2025 → `pjm_d4_4_A`; PJM's keeper is partitioned, so
each leg is built on its own year's recipe and no cross-partition config enters a diff),
diffing the assembled P0 objective array `mc_base` row for row. Four legs:

* **CTL** — the keeper recipe as registered.
* **ARM_C** — `committed_band_measured_basis=True` (the pjm-h6 arm, killed alone at the 2023 screen).
* **ARM_G** — `coal_bit_passthrough_gas_mid = 4.58` alone.
* **ARM_J** — BOTH. **This is the arm under test.**

One declared simplification, inherited from pjm-h4 §2 / pjm-h6 §2 where it was verified rather
than asserted: `pjm_da_virtual_bids=False`, self-cancelling because every leg of every diff
carries it identically.

**ZERO NEW CODE.** The joint arm needs no `ScenarioConfig` field that does not already exist:
`committed_band_measured_basis` was built and merged by pjm-h6, and `coal_bit_passthrough_gas_mid`
is long-standing and reached through the keeper's own `coal_bit_sigmoid_overrides` dict. So there
is no new cache-key registration, no new matrix row, and `--no-` reaches the pre-arm posture by
construction. Only `docs/` and `scripts/probes/` are added by this lane.

### 3.1 G-1 CONFINEMENT — **PASS, all six years**

605-606 of ~2,978 rows move. Bands **exactly** `{committed, econ, peak}`; groups exactly
`{CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS}`, with **all** `econ`/`peak` movement
confined to `COAL` (the sigmoid is coal-only by construction). Row count, `unit_id` order and
`pmax` identical in every year and every leg (asserted in the probe, not eyeballed).

### 3.2 G-2 IDENTITY — **PASS, all six years, EXACTLY**

| leg | what it asserts | measured |
|---|---|---:|
| (i) | resolved `gas_mid` == 4.58 | **0.0** dev, 6/6 yrs |
| (i) | `floor` / `ceil` / `gas_slope` move | **0.0 / 0.0 / 0.0**, 6/6 yrs |
| (ii) | **ARM_J == ARM_C on every `committed` row** | **0.0**, 6/6 yrs |
| (iii) | **ARM_J == ARM_G on every non-`committed` row** | **0.0**, 6/6 yrs |
| (iv) | overlap residual `dJ-(dC+dG)` == `-dG` on coal `committed` | ≤ **7.1e-15**, 6/6 yrs |
| (iv) | that residual off those rows | **0.0**, 6/6 yrs |

Legs (ii) and (iii) are the **orthogonality identity**, pre-registered before it was run: under
REPLACE the `committed` band carries **no sigmoid**, so the re-centred centre *cannot* reach it;
and `gas_mid` touches only the sigmoid, so the measured basis *cannot* reach an `econ`/`peak`
row. Both hold at **exactly 0.0**, which means the joint arm is **literally h6's arm plus a coal
`econ`/`peak` discount** — the committed half is bit-identical, not merely similar. That is the
cleanest possible controlled design and it is what makes §5's bounds rigorous.

Leg (iv) is the arithmetic statement of **rule 19 `[R-ONE-MECH]`**: superposition
`dC + dG` FAILS by exactly `dG` on the 64 coal `committed` rows (**12,550.277 MW** — the same
12,550 MW h6's G-3 measured), because `ARM_G` alone reaches those rows and `ARM_J` cannot. **The
two halves are not separable.** h6 proved that empirically by screening one alone; this measures
it to machine precision.

### 3.3 G-3 MAGNITUDE — the pre-solve table

Mean bituminous passthrough on the keeper's own gas series, and the coal cap-weighted `Δ$/MWh`:

| yr | gas $/MMBtu | passthrough 3.40 → 4.58 | ARM_C coal | ARM_G coal | **ARM_J coal** | relief |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | 1.936 | 0.6744 → 0.6514 | +3.2105 | −0.2718 | **+3.0100** | 6.2 % |
| 2021 | 3.581 | 1.0105 → 0.7921 | +1.9942 | −2.5947 | **+0.0800** | 96.0 % |
| 2022 | 6.479 | 1.3150 → 1.2543 | +1.3180 | −0.8808 | **+0.6678** | 49.3 % |
| **2023** | 2.485 | 0.7573 → 0.6630 | +4.4882 | −1.7287 | **+3.2117** | 28.4 % |
| 2024 | 2.387 | 0.7530 → 0.6980 | +4.2813 | −0.9652 | **+3.5663** | 16.7 % |
| 2025 | 3.745 | 0.9645 → 0.7909 | +3.0507 | −2.8809 | **+0.9150** | 70.0 % |

Two independent reproductions, neither of them re-derived here: the `live 3.40` and `4.58`
passthrough columns reproduce **h5 §9's table to four decimals in all six years**, and the
`ARM_C` column reproduces **h6's phase-0 all-coal G-3 to four decimals in all six years**.

ARM_J per band (cap-wtd `Δ$/MWh`, MW):

| yr | `committed` (all 6 classes) | coal `econ` | coal `peak` | fleet | footprint $-MW |
|---|---:|---:|---:|---:|---:|
| 2020 | +3.733 (46,424) | −0.512 (18,339) | −0.570 (901) | +0.7850 | 183,247 |
| 2021 | +2.723 (46,345) | −4.886 (18,339) | −5.451 (901) | +0.1524 | 225,185 |
| 2022 | +2.483 (46,341) | −1.659 (18,339) | −1.851 (901) | +0.3989 | 163,203 |
| **2023** | **+5.212 (46,339)** | **−3.259 (18,339)** | **−3.624 (901)** | **+0.8585** | **304,583** |
| 2024 | +4.967 (46,340) | −1.826 (18,339) | −2.021 (901) | +0.9371 | 265,480 |
| 2025 | +3.878 (46,341) | −5.470 (18,321) | −6.048 (901) | +0.3559 | 288,194 |

**The relief ANTI-correlates with the bite, and that is a structural fact worth stating up
front rather than discovering in the result**: the re-centring gives back most where the
committed-basis arm bites least (2021 96 %, 2025 70 %) and least where it bites most (2024
16.7 %, **2023 28.4 %**). The sigmoid's centre matters at **mid** gas ($3.5-3.8); at the cheap
gas of 2023/2024 both centres sit near the floor, so the curve has little to give back there.

## 4. THE SCREEN — 2023, named on FOOTPRINT before the solve

**Screen year 2023.** It is the maximum of the ARM_J `footprint $-MW` column (304,583 >
2025's 288,194 > 2024's 265,480 > 2021 > 2020 > 2022), which is the mechanism's own measured
footprint per rule 29 `[R-SCREEN]` clause (1) — **never** the residual. (It is not the
largest-residual year either: that is 2020, which ranks **fifth** of six on footprint.)

### 4.1 G-CTRL — **form 4 is VALID. NO CONTROL SOLVE IS SPENT.**

pjm-h6's own 2023 control is **committed on `origin`** with its full per-plant layer
(17 files incl. `dispatch/2023_P1.parquet`), verified present this session by
`git ls-tree`, and h6 measured that it **reproduces the keeper**: COAL_BIT 105.152 vs the
keeper's scored 105.125 (gap 0.027 TWh, three orders below the ±8.00 band) and C1 **16/16**,
the keeper's committed headline exactly.

**G-DRIFT** (rule 29 `[R-SCREEN]` (b)), from that control's `git_sha` `46c5702d` to HEAD
`c6c70190`. Exactly **two** non-merge commits touch
`src/market_sim` / the two runners / `scripts/lib` / `data/raw/_validation-source` /
`data/raw/reference`, and **both classify INERT for a PJM backcast — measured, not asserted**:

| commit | verdict | reason |
|---|---|---|
| `3857d801` `coal-stocks` intake | **INERT** | adds ONE new file (`data/coal_stocks.py`, 127 insertions, **zero deletions**) and `grep` over `src/market_sim` + both runners finds **zero importers**. A caller-less module cannot enter a solve. |
| `f2191f5d` NWPP registration | **INERT** | (a) every shared-file hunk is one mechanical refactor — `ISO_TO_BA_CODE.get(iso)` → `ba_codes(iso)`, `== ba_code` → `.isin(codes)` — and **`ba_codes("PJM")` returns `("PJM",)`**, so membership over a 1-tuple is identical to scalar equality. Verified by *running the function*, not by reading its comment. (b) The single non-mechanical hunk adds eGRID boundary-HR repair plant **7350** (Coyote Springs, PGE/BPAT); PJM's own 2023 solved fleet carries **0 rows** for 7350 and 0 for 55641. |

**All hunks INERT ⇒ the keeper/h6 control IS the control** and the screen spends **one** LP.

### 4.2 THE GATE — pre-registered, STRUCTURAL, STOP-ONLY, never read on the target residual

The arm proceeds past the screen only if ALL hold. The gate **may kill the arm; it may never
promote one**; it contributes to no determination.

* **G-1 confinement** — only the §3.1 rows move. *(Already PASS at phase 0, six years.)*
* **G-2 identity** — the §3.2 legs. *(Already PASS at phase 0, six years, exactly.)*
* **G-3 SIGN/MAGNITUDE — the pre-registered INTERVAL.** Because G-2 (ii) proves the committed
  half is **bit-identical** to h6's arm, and G-2 (iii) proves the added half is a **pure
  discount** on 19,240 MW of coal `econ`+`peak`, the arm's 2023 COAL_BIT is bounded on **both**
  sides by numbers that are already measured rather than assumed:

  > **78.834 < COAL_BIT(ARM_J) < 105.152 TWh**
  > (lower = h6's armed value, upper = the control's value)

  A landing outside that interval means the mechanism is not doing what its own arithmetic
  says, and the arm STOPS.
* **G-4 NO NON-TARGET LOAD-BEARING FLIP** — no **non-target** load-bearing criterion (C1 on
  another class, C2, C3a, C3b) crosses PASS → FAIL against the control. **CC_REGULAR is the
  named watch**: it is what killed h6 (control 328.456 = +2.79 PASS → arm 339.154 = +13.48
  FAIL). Band ±8.00 TWh ⇒ the arm must land **CC_REGULAR ≤ 333.670 TWh**.

## 5. EXPECTED, REPORTED, GATING NOTHING — including the outcome that would kill it

**The naive linear expectation is that this still fails, and it is stated here so the result
cannot be spun either way.** h6 moved all-coal +4.4882 $/MWh and lost 26.318 TWh of COAL_BIT
(105.152 → 78.834), i.e. ≈ −5.86 TWh per $/MWh locally. ARM_J moves all-coal +3.2117, so a
locally-linear response predicts:

| | predicted | residual vs 103.026 actual | band ±8.00 |
|---|---:|---:|---|
| COAL_BIT | ≈ 86.3 TWh | ≈ **−16.7** | **FAIL** |
| CC_REGULAR (absorbing proportionally) | ≈ 336.0 TWh | ≈ **+10.4** | **FAIL** |

**Why that estimate may understate the relief, stated as a mechanism rather than a hope:** the
`committed` band is the **min-load** block — infra-marginal in nearly all hours, so raising it
displaces coal only by pushing whole plants out of merit — whereas the `econ` band is where
coal competes **at the margin** against gas CC. A $/MWh of `econ` discount and a $/MWh of
`committed` increase are not the same instrument, and a cap-weighted average over all coal rows
deliberately blurs that distinction. **Which one dominates is exactly what the screen measures,
and it is the reason a linear read is not admissible as a gate.**

**Neither number is a gate in either direction** (rule 1 `[R-STRUCT]`): G-3 is an interval on
what the mechanism *does*, G-4 is a non-target flip check. The target residual selects nothing.

**And the result is informative whichever way it lands**, which is why the LP is worth spending:

* **Relief large** ⇒ the h6 diagnosis is confirmed — the registered 0.548 was compensating for
  the mis-grounded centre — and the joint arm earns the six-year span.
* **Relief small** ⇒ the diagnosis is **incomplete**: something *else* is also being
  compensated, the span is never spent (~105 min saved), and the lane reports a narrowed
  root-cause question rather than a tuned parameter.

## 6. DOF LEDGER ENTRY (rule 21 `[R-DOF]`)

**Zero new free parameters, zero new fields, nothing swept.** The arm sets one existing
parameter to a value **derived** from the model's own measured delivered coal through the
derive script's own published construction (§2), and one existing boolean built by pjm-h6. No
`authorized_price_tuning` block is claimed or needed: this is not an `offer_curve_by_group` band
multiplier, so the rules 1/13 carve-out is **not** invoked and its conditions are not in play.

The single candidate operand was fixed in §2 **before** the phase-0 probe was written, and the
two rejected candidates are refused on **stated documentary grounds** (no derivation; a measured
+54.6 % input error), never on a score.

## 7. WHAT IS NOT TOUCHED

* `floor` (0.65 live / 0.76 table), `ceil` (1.32), `gas_slope` (2.5) — **unmoved, measured 0.0**.
  The ceil-alone arm and the full re-derivation stay adjudicated **R** (pjm-170, pjm-h2b).
* Route A REPLACE **as-is** stays **R** (pjm-h6). This lane does not re-run it; it carries it as
  the joint arm's first half, which G-2 (ii) proves is bit-identical.
* Reverting the committed band to 0.548 stays refused — rule 14 `[R-ACCURATE]` forbids burying
  the error back inside an inaccurate input.
* Standing escalations carried forward unchanged: PS-net-inclusive `OTHER` as the
  `gas_foldin_deflation` operand; the EIA-930 PJM 2021 `net_gen` corruption; the display-stale
  `volErr`/`nonFosErr` in the PJM 2021/2022 run payloads.
* The two pre-existing parity REDs (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) are
  neither PJM's nor touched here.

## 8. RULES

Rule 1 `[R-STRUCT]` (§4.2 the gate is structural and STOP-only; §5 direction reported and
gating nothing; the residual selects no parameter) · rule 13 `[R-MEASURED]` (§2 the operand is
a formulaic input with a forward analogue, not a fitted outcome) · rule 14 `[R-ACCURATE]`
(§2 the +54.6 % candidate is refused *because* it is inaccurate; §7 the accurate committed basis
is not reverted) · rule 19 `[R-ONE-MECH]` (§3.2 leg (iv) — the halves are measurably
inseparable, so they are screened as one) · rule 21 `[R-DOF]` (§6 zero free parameters, one
derived operand, nothing swept) · rule 23 `[R-FROZEN-DERIVE]` (§1 the defect this lane exists
for) · rule 24 `[R-REGISTRY]` (§3 zero new fields; the arm is requested per run on registered
parameters) · rule 25 `[R-ISO-SCOPE]` (PJM's own artifact and PJM's own curve; nothing transfers)
· rule 28 `[R-MECH-MATRIX]` (the `coal_passthrough_sigmoids` PJM cell is updated in this session)
· rule 29 `[R-SCREEN]` (clause 0 = this whole document; clause (1) screen year on footprint;
clause (b) G-DRIFT discharged at zero LP, form 4 valid) · rule 30(c) (no held-out year touches
PJM's determination) · rule 31 `[R-RETAIN]` (nothing deleted; the promotion question is put to
the owner) · rule 32 `[R-SHARD]` (a) (the parent runs no LP) · rule 34 `[R-SHARD-PROMOTABLE]`
(the shard pushes its bundle with the per-plant layer).

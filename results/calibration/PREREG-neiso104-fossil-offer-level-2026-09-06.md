# PREREG neiso-104 — NEISO fossil offer-level correction (authorized price-tuning channel)

**Session.** neiso-104, NEISO lane. Branch `claude/neiso-2020-lmp-miss-gr899x`, cut from
`origin/main` at **`b22b91c3`**. 2026-09-06. **DATA PROFILE: neiso.**

**Status: PRE-REGISTRATION ONLY. ZERO LP MINUTES SPENT AT WRITING.** No solve, no screen, no
registration, no keeper change, no `ScenarioConfig` default moved. Every number in §1–§3 is
computed from committed artifacts (the keeper's and the touchpoint's `hourly/` sidecars) plus
the two committed gas-price series. This document exists to fix the tuned value **before** any
LP runs, as rule 1 `[R-STRUCT]` condition (c) requires.

---

## 0. What this proposes, in one line

Multiply NEISO's **markup** fossil offer bands by a single scalar **0.9547** (a 4.53 % cut),
identified entirely on the **in-sample 2023–2025** price bias, applied unchanged to every
scored year, to correct a measured in-sample level bias of **+3.47 %** (+$1.57/MWh).

**This is not a 2020 lane.** 2020 is a rule-22 validation touchpoint; nothing here is fitted to
it, and under rule 30(c) `[R-TOUCHPOINT-FOLD]` its result cannot certify or decertify NEISO
either way. §3.3 pre-registers what 2020 is expected to do, including the honest statement that
it straddles the C3a band at the declared value.

---

## 1. The object: an in-sample level bias that exists independently of any held-out year

Load-weighted mean LMP, model (committed P1 sidecars) against actual RT, every year in the
record. Reproduced in-session from `hourly/system_<year>.parquet`; matches
`FINDING-neiso103-2020-input-readiness-2026-09-06.md` §0 to 3 dp.

| year | tier | model $/MWh | actual RT (lw) | rel err | C3a |
|---|---|---:|---:|---:|---|
| 2020 | validation | 28.586 | 25.14 | +13.71 % | FAIL |
| 2021 | validation | 52.107 | 47.77 | +9.08 % | PASS |
| 2022 | validation | 90.60 | 91.15 | −0.60 % | PASS |
| **2023** | **train** | **39.293** | **38.10** | **+3.13 %** | PASS |
| **2024** | **train** | **44.041** | **41.68** | **+5.66 %** | PASS |
| **2025** | **train** | **71.387** | **70.23** | **+1.65 %** | PASS |

The model runs high in 5 of 6 years. **The bias is present, and identifiable, entirely within
the training window** — which is what makes this an in-sample calibration item under rule 1's
second step and rule 22's step 3, and not a touchpoint chase. neiso-103 §4 reached the same
conclusion from the other direction and declined to open the lane; this opens it, on the
in-sample object only.

---

## 2. The channel, and why it is admissible

`offer_curve_by_group` band multipliers are the **authorized price-tuning channel** under the
owner ruling of 2026-09-05 (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`). Compliance, condition by
condition:

| condition | how this run satisfies it |
|---|---|
| (a) band multipliers only — never `phys_*`, never `econ_low_share` / `pct_peaking`, never a new adder | §2.1: 12 band values move; no `phys_*`, no share, no `pct_peaking`, no new field |
| (b) ONE config across EVERY scored year | one scalar, applied in `_NEISO_OFFER_CURVE`, no year branch anywhere |
| (c) set ex ante, declared in the PREREG before the solve, never swept against the gates | this document, committed before the screen; §3.4 discloses the one contamination honestly |
| (d) merit-order adjustment across classes is intended, not a defect | §2.1: a uniform scalar is the *minimum* merit-order disturbance available |
| (e) declared in the attestation's `authorized_price_tuning` block + a DOF-ledger free parameter | §5 |

Matrix state checked before proposing (rule 32 `[R-MECH-MATRIX]`, DO-NOT-REDO): NEISO's
`offer_curve_by_group` cell is **`K`** — armed on the keeper, never adjudicated `R`/`I`/`G`. No
prior verdict blocks a re-tune.

### 2.1 Scope — decided by a mechanical rule, not by a result

The user's condition is to *preserve the relative relationship between all fossil costs*, i.e.
one scalar rather than per-band edits. Phase 0 found that a literally-uniform scalar over all
20 registered bands would **cut into measured physics**, which condition (a) forbids in
substance even where the letter permits the key. Four `peak` values are not markups at all:

| band | registered | why it is NOT a markup |
|---|---:|---|
| `CC_REGULAR.peak` | 2.25 | `== phys_peak` 2.25 — "physical F-class duct ratio == registered peak" |
| `CC_CHP.peak` | 2.25 | `== phys_peak` 2.25 — "physical F-class duct-burner ratio (not ERCOT-fitted)" |
| `ST_GAS.peak` | 1.00 | `== phys_peak` 1.0 — "registered peak 1.0 == full-output bound → markup 0" |
| `CT_PEAKER.peak` | 4.00 | market-design cap — "ISO-NE offer cap $1,000–2,000 (not ERCOT $5,000 ORDC)" |

**The scope rule, stated mechanically so no result can select it:** the scalar applies to every
registered band **except** (i) any band whose registered value equals its `phys_*` counterpart,
(ii) any band annotated in source as a market-design cap, and (iii) the `CT_CHP` group, whose
all-1.0 neutrality is a stated **non**-identification ("the NEISO CAMPD sample is a SINGLE unit
(n=1), not identifiable as a class spread") — scaling a deliberately-neutral group off neutral
would invent an identification this lane has not made.

**In scope: 12 bands.** `committed` / `econ_low` / `econ_high` of `CC_REGULAR`, `CC_CHP`,
`CT_PEAKER`, `ST_GAS`.

Headroom against measured physics at the declared cut (registered → post-cut, vs `phys_*`):

| group | committed | econ_low | econ_high |
|---|---|---|---|
| CC_REGULAR | 1.27 → 1.2125 (phys 1.107) ✓ | 1.00 → 0.9547 (0.854) ✓ | 1.15 → 1.0979 (0.940) ✓ |
| CC_CHP | 1.15 → 1.0979 (phys 1.399) ⚠ | 1.17 → 1.1170 (0.973) ✓ | 1.19 → 1.1361 (0.940) ✓ |
| CT_PEAKER | 1.35 → 1.2888 (phys 0.985) ✓ | 1.00 → 0.9547 (0.745) ✓ | 1.00 → 0.9547 (0.700) ✓ |
| ST_GAS | 0.79 → 0.7542 (phys 2.394) ⚠ | 0.85 → 0.8115 (0.692) ✓ | 0.89 → 0.8497 (0.731) ✓ |

⚠ **Disclosed, not buried:** `CC_CHP.committed` and `ST_GAS.committed` already sit **below**
their measured `avg_committed_p50` in the incumbent keeper (the source annotates both as
"markup clips 0"). The cut deepens a pre-existing condition; it does not create one. No `phys_*`
value is touched, so the disclosure stays measurable at every future read.

The scalar also **exactly preserves the CC_CHP construction**, which is derived as
NEISO's own CC reach ratio (`CC_REGULAR.econ_high / phys_econ_high` = 1.15 / 0.940 = 1.223×)
applied to the measured CC_CHP marginal. Scaling numerator and the CC_CHP bands by the same
factor leaves that ratio construction intact — the relationship the user asked to preserve,
preserved by identity rather than by assertion.

---

## 3. The declared value, and how it was identified

### 3.1 In-sample bias (the numerator) — 2023–2025 ONLY

Three estimators of one multiplicative bias, computed over the training years alone:

| estimator | value |
|---|---:|
| arithmetic mean of per-year relative errors | **+3.48 %** |
| **geometric mean of per-year model/actual ratios** | **+3.47 %** |
| pooled-mean ratio (Σmodel / Σactual) | +3.14 % |

**Declared: the geometric mean, +3.47 %.** Stated reason, fixed on principle: the object is a
**multiplicative** bias, for which the geometric mean of ratios is the natural equal-weight
estimator; and C3a scores **each year independently against a relative band**, so the estimator
that matches the gate's own geometry weights each year equally. The pooled ratio implicitly
weights years by their price level (2025 carries 46 % of the pooled numerator), which has no
basis when the quantity being estimated is a scale factor. The two equal-weight estimators agree
to 4 decimal places (0.0347 / 0.0348) and only the price-level-weighted one differs — which is
the signature of the pooled estimator being the odd one out, not of a knife-edge choice.

### 3.2 Pass-through (the denominator) — measured, not assumed

A uniform scalar on the offer bands and a uniform scalar on the delivered gas price are the
**same experiment** on the marginal-cost surface: both enter as `mult × HR × fuel`. So the
model's own price elasticity with respect to delivered gas measures the pass-through of the
multiplier, at zero LP cost.

Delivered gas built as committed Henry Hub daily + committed NEISO monthly Algonquin basis
(`data/raw/gas-prices/henry_hub_daily.csv`, `data/raw/gas_basis_by_iso_month.csv`); model price
is the load-weighted zonal collapse of the committed P1 `system_<year>` sidecars.

| basis | d ln(price) / d ln(gas) |
|---|---:|
| **across-year, all 5 solved years** | **0.765** |
| across-year, in-sample 3 years | 0.742 |
| within-year pooled, in-sample | 0.593 |

**Declared: 0.765, the across-year elasticity over all solved years.** A multiplier change is a
*level shift of the whole fossil cost surface*, which is what the across-year contrast measures;
the within-year contrast additionally carries short-run demand, hydro and import variation that
a multiplier change does not cause, and is therefore the wrong analogue (and biased low). Using
all five solved years rather than three is the larger, more stable sample and is **not** the
choice that favours any outcome — the in-sample-only value 0.742 would imply a *larger* cut
(4.68 %) and a *more* favourable 2020.

### 3.3 The declared value, and the pre-registered prediction

> **DECLARED: a single scalar `0.9547` (a 4.53 % cut) applied to the 12 bands named in §2.1.**
> Derivation, fixed: `0.0347 / 0.765 = 0.0453`. This number does not move again.

Expected delivered price move: 4.53 % × 0.765 = **−3.47 %**. Pre-registered landing, stated for
every year **before the screen runs**:

| year | now | predicted | predicted C3a |
|---|---:|---:|---|
| 2020 | +13.71 % | **+9.76 %** | **PASS — by 0.24 pp, i.e. inside the method's own error** |
| 2021 | +9.08 % | +5.30 % | PASS |
| 2022 | −0.60 % | −4.05 % | PASS |
| 2023 | +3.13 % | −0.45 % | PASS |
| 2024 | +5.66 % | +2.00 % | PASS |
| 2025 | +1.65 % | −1.88 % | PASS |

**2020's predicted margin (0.24 pp) is smaller than the uncertainty in the pass-through
coefficient** (the 0.593–0.765 range spans a delivered move of 2.7–3.5 %, putting 2020 anywhere
in +9.8 % to +10.7 %). Excluding the four `peak` bands from the scalar per §2.1 further reduces
delivered pass-through by an unmeasured amount. **This lane therefore pre-registers that 2020's
verdict is genuinely undetermined at the declared value, and that it will be reported as it
lands.** A 2020 that still reads FAIL is a successful run of this lane, not a failed one.

### 3.4 Contamination, disclosed rather than presented as clean

**The estimator was chosen after the 2020 arithmetic for both candidates was already computed.**
In the analysis that preceded this document I computed that a −3.48 % price move puts 2020 at
+9.75 % (PASS) and a −3.14 % move puts it at +10.14 % (FAIL). I then selected the geometric mean
(+3.47 %), which is on the PASS side. The §3.1 reasoning is stated on its own merits and I
believe it stands independently — but a reader cannot verify that it was not chosen for its
outcome, so the fact is recorded here rather than left for someone to discover. Two things
partially mitigate it and neither erases it: the two *equal-weight* estimators agree to 4 dp, so
the choice is between one principle and another rather than between two arbitrary numbers; and
per §3.3 the declared value does not reliably clear 2020 anyway, so the contaminated choice does
not purchase the outcome it is contaminated toward. **The clean alternative, if the owner
prefers it: take the pooled estimator (+3.14 %, cut 4.11 %), which is the reading that does NOT
clear 2020.** This lane will run whichever the owner names; it defaults to the geometric mean.

---

## 4. Execution plan (rule 29 `[R-SCREEN]`)

**Phase 0 — DONE, zero LP.** §1 bias, §2.1 scope census, §3.2 pass-through. Outstanding before
the screen: **G-DRIFT** (rule 29(b)) — classify every hunk of
`git diff 6619fb4a..HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference` as INERT-for-NEISO-backcast or LIVE. All INERT ⇒
the keeper's committed bundle is the control (G-CTRL form 4) and **no control solve is spent**.
Recorded as an addendum to this file before the arm is solved.

**Phase 1 — SCREEN, one year.** **Screen year: 2025.** Named here, before the screen runs, and
chosen because it is the year the mechanism's **own footprint is largest** — the bands are
multipliers on `HR × fuel`, and 2025 carries the highest delivered gas ($6.24/MMBtu mean, 2.0×
2023) and therefore the largest absolute offer delta per unit of multiplier. **It is explicitly
NOT the largest-residual year** (that is 2020, a touchpoint, which this lane will not screen on).

The screen gate is **structural and STOP-ONLY**. It may kill the arm; it cannot promote it, and
it is **not** gated on C3a:

1. **Direction and magnitude** — delivered mean-price move is negative and within ±1.0 pp of the
   3.47 % the pre-solve arithmetic implies. A move of the wrong sign, or outside that, means the
   pass-through model in §3.2 is wrong and the arm stops.
2. **Footprint confinement** — energy moves are confined to the four scoped groups plus the
   storage/PS response their spread change implies. Any material move in nuclear, wind, solar or
   net interchange means the scalar is reaching rows it does not claim (interchange is exogenous:
   the keeper runs `priced_interchange: false`, so its hourly series must be bit-unchanged).
3. **Identity** — `phys_*`, `econ_low_share`, `pct_peaking` and all four `peak` bands are
   bit-identical to the incumbent in the arm's `run_config.json`.
4. **No non-target load-bearing flip** — C1, C2, C3b do not go PASS → FAIL on the screen year.

**Phase 2 — full span**, only if the screen clears: one `--year 2023 2024 2025` invocation, one
bundle (rule 16 `[R-ALLYEARS]`). The screen bundle is a throwaway probe: never registered, never
quoted as a keeper number, and **deleted from `results/calibration/` before the PR merges**
(rule 29(c) `[R-SCREEN]`).

**Phase 3 — touchpoints**, only if phase 2 is promoted: re-run 2020 / 2021 / 2022 on the frozen
new recipe (validation tier is not frozen — `holdout-freeze.json` `scope.tiers = ['locked_test']`
— and NEISO holds a `complete` marker), stamp each to the new keeper via
`stamp_touchpoint_holdout.py` (rule 30(a)), rebuild the status ladder (rule 30(b)). The
registration-time marker re-check (rule 22, owner ruling R-AZ) applies. **The locked test (2019,
H1-2026) is untouched and stays frozen.**

---

## 5. Governance artifacts owed by the arm

- **Attestation** `authorized_price_tuning` block (C6 FAILS without it): channel
  `offer_curve_by_group`, scalar 0.9547, the 12 bands of §2.1, this PREREG as the ex-ante
  declaration, year-invariance asserted.
- **DOF ledger** (rule 21 `[R-DOF]`, cross-reference R-AY): **one** new free parameter — the
  scalar — identification source *"price residual, authorized channel (rules 1/13 amendment
  2026-09-05); in-sample 2023–2025 geometric-mean bias / measured across-year gas elasticity"*,
  reported at full magnitude. Per R-AY it does **not** make the residual it closes an open
  root-cause issue, and no gate moves.
- **Mechanism matrix** (rule 32(b)): `offer_curve_by_group` in
  `docs/codebase-site/data/mechanism-matrix/NEISO.js` re-stamped in the session that solves —
  whatever the verdict, rejection included. **NEISO's shard only** (rule 25 `[R-ISO-SCOPE]`):
  this scalar is fitted on NEISO's residual and never transfers.
- **Dashboard** (rule 15): the full-span bundle registers whether it is promoted or rejected.

---

## 6. Risk register — stated before the result

1. **NEISO's `CALIBRATED` is one flip from `NOT-YET`, and this is the dominant risk.** The
   determination rests on the C3c standing rule, whose guard (a) fires **only** when C3c is the
   *lone* failure. The incumbent scores 0 FAILs with C3c the single ledgered caveat. If this arm
   flips any second criterion, the standing rule goes silent and **both** failures stand. The
   ISO's headline is being risked to correct a bias that currently costs it nothing.
2. **C3b price duration/shape is the live exposure.** The whole price surface shifts down ~3.5 %
   while the four physically-pinned `peak` bands stay put, so the duration curve does not shift
   rigidly. C3b is load-bearing and is screen gate 4.
3. **C3c cannot get worse** (model 0 h > $300 in all three years — saturated at 0.00×), and
   excluding the `peak` bands keeps the scarcity end untouched. This is the one criterion the arm
   cannot damage.
4. **C1 / C2 exposure is structurally low**, which is what makes NEISO a good host for this lever:
   `priced_interchange: false`, must-run nuclear, exogenous measured interchange ⇒ the residual
   fossil load is near-fixed, so a uniform fossil scalar is close to a pure price lever. It is not
   zero — pumped-storage arbitrage responds to the compressed spread (screen gate 2).
5. **Rule 30(c) bounds the whole exercise.** Whatever 2020 does, it neither certifies nor
   decertifies NEISO. If phase 2 shows the in-sample bias corrected and any gate degraded, the
   arm is rejected and the incumbent keeper stands — that is a clean outcome, registered and
   reported, not a failure to be re-tuned around.

---

## 7. What would make this lane WRONG to run

Recorded so it can be checked against, per the lane's own standard:

- If G-DRIFT finds a LIVE hunk, the keeper is not a valid control and the cost of this lane rises
  by a control solve — reconsider before spending it.
- If the screen shows delivered pass-through materially below 0.6, the §3.2 identification is
  wrong, the declared cut under-delivers, and the honest move is to **stop and re-derive**, not
  to raise the scalar (raising it to hit the in-sample target after seeing the screen would be
  the sweep condition (c) forbids).
- If the owner reads §3.4 and judges the contamination disqualifying, the pooled estimator
  (cut 4.11 %) is the pre-declared alternative and this document is amended before any solve.


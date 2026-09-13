# PRECOMMIT caiso-280 — does the CAISO import envelope understate deliverable import on 2022-12-23..31?

**Lane:** CAISO calibration. **Date:** 2026-09-13. **Predecessor:** caiso-279
(`docs/RESULT-caiso279-the-binding-object-is-the-import-envelope-2026-09-12.md`).
**LP budget: ZERO.** This session is one zero-LP measurement. Nothing is solved. Rule 32
`[R-SHARD]` (a) — the parent never solves — is not even reached, because no solve is chartered.

## 1. THE QUESTION, IN ONE LINE

caiso-279 established that on the hours carrying CAISO's 2022 C3a miss, lambda is set by an
**import-envelope shadow price**, not by any generator's offer — the solution is
quantity-constrained. This session asks the one question that decides whether that envelope is a
**defect** or **correct behaviour**:

> Did CAISO's MEASURED ACTUAL imports on 2022-12-23..31 exceed the cap the model applied?

## 2. WHAT THE ENVELOPE ACTUALLY IS — established before the measurement, from the code

`market_sim.data.eia930.envelopes.measured_corridor_flow_envelope`, applied as the import-direction
upper bound of the corridor interface groups (`model/transmission.build_caiso_corridor_flow_groups`):

- Per corridor, **net import = −Σ(EIA-930 `mw`) over that corridor's DIBAs** (EIA sign:
  + = CISO exports to the DIBA).
- Corridor membership, `model/interchange/spec.CAISO_CORRIDOR_DIBA`, split geographically at Path-15:
  **WECC_PNW** = BPAT, PACW, BANC, TIDC · **WECC_DSW** = AZPS, SRP, WALC, NEVP, IID, LDWP, CEN.
  All eleven CISO DIBAs are mapped, so the two corridors **partition the whole seam** — corridor
  total ≡ CISO total interchange.
- The cap is the **p95 of that year's own measured net import, bucketed by (month × hour-of-day)**
  (`CAISO_CORRIDOR_FLOW_PERCENTILE = 95.0`), clipped at 0.
- 12 × 24 = **288 buckets**, which is why caiso-279 measured **286 distinct limit values**. That
  arithmetic is the confirmation that the binding group limit IS this envelope.
- Stamps are mapped onto the model clock by `_caiso_interchange_model_clock`: lag **1 h in standard
  time**, 2 h in daylight time. December is standard time, so the December mapping is
  `model_stamp = local_time − 1h`.

### 2.1 THE CONSEQUENCE THAT SETS THE BAR — stated before any number is read

Because the cap **is a p95 of the very series it is compared against**, roughly **5% of each
bucket's own hours exceed it by construction**. A bare finding of "actual exceeded the cap in some
hours" is therefore **worth nothing** — it is the definition of a 95th percentile, not evidence of
a defect. Any honest test must beat that null.

It also cuts the other way, and this is the reason the test has power: the Dec 23–31 hours are
**inside the sample that built the December p95**. An extreme window drags its own buckets' p95
**up**, which makes exceedance **harder** to observe. The test is conservative in the correct
direction — against finding a defect.

## 3. THE DECISION RULE — FIXED HERE, BEFORE MEASURING (rule 1 `[R-STRUCT]`)

Two gates, **conjunctive**. Both must pass to declare a defect. Deliberately conservative: rule 1
and §4 of the charter both warn that widening a cap toward the residual is the forbidden move, so
the rule is built to make "defect" hard to reach, not easy.

**T1 — EXCEEDANCE RATE against the construction's own null.**
Over the 216 hours of 2022-12-23..31, count hours where measured corridor net import exceeds the
`limit_up` the LP actually saw. Declare UNDERSTATED only if **both**:
- (a) window exceedance rate **≥ 20%** of hours (4× the construction's 5% null; ~10 sd above the
  null's 10.8 ± 3.2 expected exceedances in 216 draws), **and**
- (b) window rate **≥ 2×** the Dec 1–22 rate, which is the empirical in-month control.

**T2 — MATERIALITY in MW.**
Mean over **all 216 window hours** of `Σ_corridor max(0, actual_net_import − limit_up)` — the mean
unserved import capability — must be **≥ 500 MW**. Anchor: the model's import is pinned at
**7,482.8 MW** on these days, so 500 MW is a **6.7%** understatement. Below that the object cannot
plausibly carry a 9-day window's share of a 1.130 $/MWh annual ask without an implausible price
elasticity; above it, displacing the marginal CC_REGULAR econ band is arithmetically open.

**VERDICTS:**
- **T1 and T2 both pass → THE ENVELOPE UNDERSTATES DELIVERABLE IMPORT.** A structural defect
  worth an arm — *subject to §4 below, which may still refuse the repair.*
- **Either gate fails → NOT MATERIALLY UNDERSTATED.** The model imports what the market did on
  these hours; the 2022 miss is **not reachable through import quantity**; the lane closes on 2022
  with no LP spent.
- Where T1 clears the null but misses the threshold, the verdict is the second one, **reported as
  the weaker statement it is** — "not materially understated", never "correct".

### 3.1 NET vs GROSS — the comparison is net-to-net, and this is a guard against myself

The prompt's item (a) asks for gross imports. Gross **will** be reported. But the **decision rests
on the NET comparison**, because the model's flow variable on that corridor is itself net and the
cap bounds that net variable. Comparing a gross actual against a net cap would manufacture an
exceedance out of a unit mismatch, in the direction that favours finding a defect. It is refused
here in advance.

`Σ_diba max(0, −mw)` across the 11 DIBAs is reported as the honest **lower bound** on gross import
(it recovers hours where CAISO imports from one neighbour while exporting to another; it cannot
recover simultaneous import+export *within* one DIBA seam, which EIA-930 nets away). The
gross−net wedge is reported as a diagnostic of how much the §4 standing annotation is worth,
**not** as an exceedance.

## 4. THE TRAP, RESTATED SO IT BINDS THE REPAIR AND NOT JUST THE MEASUREMENT

`caiso_firm_selfsched_floor` has carried a standing annotation since caiso-150: the shape basis is
EIA-930 **realised net** corridor interchange — an OUTCOME series used as a CAPABILITY cap, with
**no admissible measured replacement**; caiso-150 §H adjudicated the direction-splitting source
**unreachable from the public feed**.

**A cap that binds is not a defect.** CAISO's interties are scheduled, not free. Even if T1 and T2
both pass, the only admissible repair is a **measured** one that is right independent of what it
does to C3a. **No cap multiplier. No widening because the residual wants it.** If T1/T2 pass and no
admissible measured replacement exists, the honest finding is that the object is **identified and
not currently repairable**, and that is what will be written.

## 5. WHAT IS MEASURED (the prompt's four items)

For December 2022, reporting Dec 23–31 separately from Dec 1–22:
- **(a)** CAISO gross imports (`Σ max(0, −mw)`) and net interchange, per hour.
- **(b)** the two corridors' actual net flows, PNW and DSW separately (the record **does** split
  them — by DIBA, via `CAISO_CORRIDOR_DIBA`).
- **(c)** the model's envelope `limit_up` per hour, read **directly from the arm A bundle's
  `hourly/network_2022.parquet`** — the cap the LP actually saw — cross-checked against a clean
  re-derivation of the p95 construction to confirm the object is understood.
- **(d)** hours where actual > model limit, and by how much.

## 6. ARTIFACTS — and a correction to the charter's retrievability claim

- **Arm A** (2022 ablation) recovered at the immutable SHA
  `b17ac9d0f8b505d542f279356d5300888c69a70f` (branch `claude/caiso279-arm-2022`, which resolves).
  Only `hourly/network_2022.parquet` is checked out — a partial-clone discipline (never resolve a
  blob you do not intend to download). Already covered by the `.gitignore` block at lines 2061-2064.
- **Arm B (the 2023-2025 span) IS NOT LOST.** The charter states its push did not land and that
  `36ce217` does not resolve. **Both claims are false.**
  `results/calibration/caiso279_ablate_dswcouple_span/` is **tracked on `main`** with all 34 files
  including the per-plant `dispatch/` layer, added by commits `14081e9c` / `36ce2170`, which do
  resolve. The shard's per-file push strategy worked; only its final report was wrong. Nothing
  needs re-solving and its container need not be woken. Recorded because rule 34
  `[R-SHARD-PROMOTABLE]` (e) makes retrievability a reported fact, and a false "lost" is as
  expensive as a false "retrievable".
- **The caiso-279 record was recovered, not rebuilt**: `e24c0d90` is merged into `main` via
  PR #6082 and is HEAD's parent. All four of its files are present.

## 7. WHAT THIS SESSION WILL NOT DO

- No LP, under any verdict. A defect verdict earns an **arm proposal for the owner**, not a solve.
- No re-test of any DO-NOT-REDO cell (charter §5, items 1-7). None is touched.
- No unilateral action on the DA-basis rubric question (charter §6) — that is an owner ruling.
- No `rm` of any bundle (rule 31 `[R-RETAIN]`).

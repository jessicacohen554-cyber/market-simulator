# RESULT — nyiso-236: the rule-29 screen of `hydro_budget_period_by_instrument`

**Session** nyiso-236 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); this session ran ZERO LP).
**Date** 2026-09-16. **Pre-registration**
`docs/PRECOMMIT-nyiso236-hydro-budget-period-screen-2026-09-16.md`, which adopts
`results/calibration/PRECOMMIT-nyiso220-screen.md` in full — both pushed before the solve.
**Keeper** `2026-09-14-nyiso-235-gas-repair` — **UNCHANGED by this session.**

> ## THE SCREEN CLEARS. G1 · G2 · G3 · G5 PASS. G4 SPLITS EXACTLY WHERE IT WAS PREDICTED TO.
> **Saying it in the words the PRECOMMIT requires: `G4-as-written` FAILED**, on CT_PEAKER +4.53 %
> — **+0.0334 TWh, 0.02 % of ISO load**. `G4-material` PASSES. Whether the material form is the
> operative one is the **owner's** decision, not this session's (PRECOMMIT §5).
>
> **A screen may kill an arm; it may never promote one.** Nothing below promotes anything.

---

## 1. WHAT WAS SOLVED

One shard, one year, at the pinned SHA `e6dc1f6991058c1bb85075f9a543823beebdafdf`.
`scripts/replay_keeper.py results/calibration/nyiso235_gasrepair_span --years 2025
--out-dir results/calibration/nyiso236_hydroperiod_2025 --set hydro_budget_period_by_instrument=true`
— the keeper's frozen recipe replayed byte-faithfully with **one field** changed.

Solve wall time ~14.5 min. Bundle: **17 files**, including `dispatch/2025_P1.parquet`, the
bundle-root `system.parquet` and `hourly/unit_hourly_2025.parquet`.

**Config diff vs the keeper — every moved field accounted for:**

| field | keeper → arm | what it is |
|---|---|---|
| `hydro_budget_period_by_instrument` | `False` → `True` | **the arm** |
| `gas_price_override` | 6.45 → 3.52 | per-year (keeper's run_config records 2022, its first solved year) |
| `weather_year` | 2022 → 2025 | per-year |
| `gas_offer_margin_anchor_by_zone` | 2022 values → 2025 values | derived at solve time per (zone, year) |
| `mustrun_commitment_feasibility_clip` | `None` → `False` | a field materializing at its dataclass default |

`solve_surface.fingerprint` = **`bd2b4657f9b5df7e`**, identical to the keeper's.

**Control = the keeper's committed bundle** (rule 29(b) form 4), valid on this session's own G-DRIFT
(`docs/FINDING-nyiso236-the-anchor-grain-and-the-gas-slope-2026-09-16.md` §1). **No control solve
was spent.**

## 2. THE GATES

| gate | threshold, as written before the solve | measured | verdict |
|---|---|---|---|
| **G1 FEASIBILITY** | LP solves to optimality | optimal; **slack 0.000000 MWh / 0 h, dump 0.000000 MWh / 0 h** — identical to the keeper | **PASS** |
| **G2 IDENTITY** | annual hydro within 0.1 %, each month within 0.5 % | annual **−0.0000 %** (24.0589 → 24.0589 TWh); **worst month 0.000 %** | **PASS** |
| **G3 DIRECTION & MAGNITUDE** | cross-day footprint must FALL from 7.46 % into **1.0–6.0 %**, never to 0.00 | **7.46 % → 4.16 %** (cross-week 5.26 % → 2.52 %) | **PASS** |
| **G4-as-written** | every non-hydro class within 2 % | **CT_PEAKER +4.53 %** | **FAIL** |
| **G4-material** | 2 % on classes ≥ 2 % of ISO load, plus conservation | worst material class **CC_CHP −0.50 %**; hydro Δ −0.0000 TWh vs non-hydro Δ −0.0077 TWh | **PASS** |
| **G5 NO NON-TARGET FLIP** | no non-hydro load-bearing criterion flips PASS → FAIL | C3a **−9.09 % → −9.25 %** (both PASS, ±10 % band); C3b 0.1651 → 0.1660; gas family 69.6366 → 69.5870 TWh (**−0.07 %**), so C1 cannot move | **PASS** |

**G2 is the striking one.** The mechanism's whole claim is that it constrains *when within a month*
and never *how much*; every month reproduces to 0.000 %. That identity is what a screen exists to test.

**G3 lands mid-band and does not collapse to zero**, which is the other half of the pre-registered
test: 28.62 % of NYISO hydro MW is deliberately unconstrained (161 plants whose licence articles have
not been read), so a fall to 0.00 % would have meant the mechanism reached rows it does not claim.

### 2.1 The G4 failure, at full magnitude and without excuse

CT_PEAKER **0.7375 → 0.7709 TWh, +4.53 %**. In absolute terms that is **+0.0334 TWh on a 151.590 TWh
system — 0.02 % of ISO load.** Every class at or above the rule-20 materiality floor (3.032 TWh)
moves by ≤ 0.50 %: CC_CHP −0.50, import +0.25, ST_GAS +0.10, CC_REGULAR +0.02, nuclear and wind
0.00. Conservation is essentially exact: hydro −0.0000 TWh against a non-hydro total of −0.0077 TWh.

The PRECOMMIT declared this exact outcome **before the solve** and declined to loosen the threshold.
It stands as a FAIL of the form as written. What I will not do is treat it as a verdict on the
mechanism without saying which form produced it.

## 3. REPORTED, NEVER GATED

Rule 1 `[R-STRUCT]`: none of this earns the span, and none of it would have killed the arm.

**D-4 off-window binding — the gate that killed both CT_PEAKER arms.** The arm's 2025 failing set is
**one row**, and it is **byte-identical to the keeper's own 2025 row**: `reliability_floor × ST_GAS`,
plant 8006, 0.0002 TWh over 4 binding hours. **Zero arm-only failures.** D-1 and D-2 pass with zero
failures on both sides. This mechanism does not manufacture commitment, which is what stopped
`nyiso_ct_peaker_bands_measured` at nyiso-199 and again at nyiso-201.

**CT_PEAKER moves toward its actual.** The model runs 0.7375 TWh in 2025 against roughly 2.85 actual;
the arm adds 0.0334. The class that trips `G4-as-written` is the class this session's own Object B
measurement predicted was under-dispatched (`FINDING-nyiso236…` §5).

**Hydro shape, 2025 — the thing the owner asked about.** Against the EIA-930 `NG: WAT` meter:

| | keeper | arm |
|---|---:|---:|
| hourly r | 0.722 | **0.802** |
| model σ ÷ actual σ | 1.220 | **1.130** |
| r(hydro, own price) ÷ actual's | 1.47× | **1.33×** |
| annual energy error | −0.2 % | −0.2 % |

The over-variance roughly halves and the price-arbitrage excess falls by about a third, at a C3a cost
of 0.16 pp. **This is not why the arm clears** — the structural gates are — and it is recorded here
precisely so that it cannot be mistaken for the reason.

## 4. WHAT HAPPENS NEXT, AND THE RULE TENSION IN IT

The owner authorized the full span **as one shard per year, including 2022** (four shards, launched
at the same pinned SHA). This is recorded plainly because it reads against rule 32 `[R-SHARD]` (b),
which bans per-year fan-out for a registrable run, while rule 34 `[R-SHARD-PROMOTABLE]` (c) says to
"launch one shard for **each**" year. The tension is real and is resolved here on **measurement, not
preference**:

* Rule 32(b)'s stated mechanical basis is that "a shard can only push what `.gitignore` lets it commit
  — the slim set", so the legs cannot be recombined. **Rule 34(a) changed that**, and this session's
  screen shard demonstrated it: 17 files pushed over a plain `git push`, including `dispatch/` and the
  bundle-root `system.parquet`.
* **Composability was verified before the four shards were launched, not assumed**: every root-level
  artifact (`system`, `flows`, `storage`, `btm`, `dispatch/<year>_P1`) carries a `year` column, so the
  legs concatenate unambiguously. `meta.json` needs its `years`/`gas_prices` merged; `metrics.json`
  and `legitimacy_diagnostics.json` are regenerated across the composed span in the parent, zero LP.

**2025 is re-solved inside the span rather than reused from the screen** (rule 29 (2)), into
`nyiso236_hydroperiod_span2025`. Because the four legs run concurrently this costs no wall-clock.

Rule 16 `[R-ALLYEARS]` is met the way it has to be: **one registrable bundle covering the full
registry year union {2022, 2023, 2024, 2025}**, composed in the parent, registered once.

## 5. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

| bundle | where | promotion cost from this state |
|---|---|---|
| screen, 2025 | commit **`478267ba7f6c8df6a36a4db2f488e2f50481049a`**, branch `claude/nyiso-236-hydro-2025` — 17 files incl. `dispatch/2025_P1.parquet` and root `system.parquet` | zero re-solve; `git archive 478267ba7f6c8df6a36a4db2f488e2f50481049a results/calibration/nyiso236_hydroperiod_2025 \| tar -x` |

The screen bundle is **gitignored, not deleted** (rule 31 `[R-RETAIN]`; rule 29(c) governs what
reaches `main`, and `.gitignore` discharges it in full). Every number this session will ever cite
from it is in §2 and §3 above.

## 6. WHAT WAS NOT DONE

* **Nothing was promoted, and no run was registered.** The keeper, its determination, its DOF ledger
  and every matrix cell stand exactly as nyiso-235 left them.
* `hydro_budget_period_by_instrument` stays **`U`** in `docs/codebase-site/data/mechanism-matrix/NYISO.js`
  until the span is scored — a screen may not move a cell to `K`.
* **No period length was swept** (PRECOMMIT §2). One arm, one configuration: Niagara 24 h,
  St. Lawrence 168 h, the other 161 plants untouched.
* `hydro_ror_split` (`G`), the USGS inflow driver and the day-of-year climatology were **not
  re-opened** — nyiso-219 closed the latter two on measurement.

---

# ADDENDUM — THE FULL SPAN KILLS THE ARM AT G2, AND THE ROOT CAUSE IS NOT OVER-CONSTRAINT

Added 2026-09-16 after the four per-year span shards landed. **The arm is NOT PROMOTABLE.**

## A1. The four-year gate table

| yr | G1 | **G2** ann / worst mo | **G2** | G3 footprint | G3 | G4-written | G4-mat | C3a keeper→arm | G5 |
|---|---|---|---|---|---|---|---|---|---|
| 2022 | PASS | **−0.2155 % / 1.275 %** | **FAIL** | 6.36→4.00 | PASS | PASS | PASS | −9.67→**−8.90** | PASS |
| 2023 | PASS | **−0.0957 % / 0.838 %** | **FAIL** | 5.31→3.18 | PASS | CT_PEAKER −2.28 % | PASS | −1.14→−1.46 | PASS |
| 2024 | PASS | +0.0000 / 0.000 | PASS | 4.71→2.71 | PASS | PASS | PASS | −0.17→−0.20 | PASS |
| 2025 | PASS | −0.0000 / 0.000 | PASS | 7.46→4.16 | PASS | CT_PEAKER +4.53 % | PASS | −9.09→−9.25 | PASS |

**G2 is the identity gate and a KILL gate.** Hydro energy is **destroyed, not reallocated**:
**−55.2 GWh in 2022** (m11 −23.6, m03 −19.1, m04 −10.1 GWh) and **−25.5 GWh in 2023**.

**The one-year screen would have promoted this.** 2025 cleared G2 at 0.000 % in every month. This is
exactly what rule 16 `[R-ALLYEARS]` exists to catch.

## A2. ROOT CAUSE — measured, and it is NEGATIVE PRICES, not over-constraint

Per-plant dispatch (`dispatch/2022_P1.parquet`) shows Niagara pinned at **exactly its period budget**
(46,836 MWh) on 29 of 31 March days, at only **80.3 % of its capability** — so neither capability nor
the budget is the binding problem on normal days. The energy is lost on the *other* days, and those
days have one signature:

| month | days | Upstate_West price mean | hours ≤ $0 |
|---|---|---:|---:|
| m03 **shortfall** | 2 | **−$7.77** | 16 (33 %) |
| m03 at cap | 29 | +$30.90 | 0 (0 %) |
| m11 **shortfall** | 15 | **−$6.64** | 127 (35 %) |
| m11 at cap | 15 | +$29.94 | 4 (1 %) |

**The LP declines to run Niagara when Upstate_West goes negative.** Under the monthly budget it moves
that water to positive-price days; under a 24 h budget it cannot, so the water is deleted from the model.

**CORRECTION, recorded rather than quietly dropped.** An earlier reading in this session attributed the
loss to a collision with `hydro_dispatch_envelope`, on the grounds that the envelope tightened through
late March. That was **correlation, not cause, and it is withdrawn**: every losing month carries
300–600 GWh of monthly envelope headroom, the arm binds the ceiling *fewer* hours than the keeper
(2022: 1,089 vs 1,970), and the decisive November shortfall days have **zero** envelope-binding hours.
The Q2 RECONCILE posture is unaffected.

**Also withdrawn: the per-plant loss decomposition.** An attempt to split the 55.2 GWh between Niagara
and St Lawrence used "max observed period output" as a proxy for each plant's budget, which is not the
budget; it returned per-plant shortfalls larger than the fleet loss in three months, so it is
unreliable and is **not** carried forward. The per-plant split is an OPEN measurement.

## A3. THE LEADING REPAIR HYPOTHESIS — "use it or lose it" was implemented as only "lose it"

Niagara's registry entry is grounded on **0.244 h of measured pondage**: it cannot bank water across
days. The period cap implements that half. But the same physical fact carries a second half the
implementation does not: a run-of-river plant with no storage **cannot withhold either** — it passes
its inflow through the turbines or spills it, it has no fuel to save, and its avoidable cost of
generating is therefore zero, so it runs at negative LMP. The current constraint is an **upper bound**,
which hands the LP an option to withhold that the plant does not have.

**Candidate repair:** for a plant whose instrument establishes no pondage, the period energy constraint
should be an **equality / floor at the period allocation**, not a cap. Zero new parameters — the level
is the allocation `allocate_period_energy` already computes.

**It must NOT apply uniformly, and that asymmetry is instrument-grounded**: St Lawrence's 168 h entry
comes from the IJC **peaking-and-ponding** directive, which explicitly grants ponding, so it legitimately
may withhold within the week and keeps the inequality.

**This is a hypothesis, not a finding.** Its pre-solve test is stated in the handoff: check whether the
measured EIA-930 NYISO hydro meter actually holds up through hours when the real Upstate_West RT LMP was
negative. If measured hydro also falls back in those hours, the hypothesis is wrong and the defect is
elsewhere.

## A4. G4 IS MISCALIBRATED, INDEPENDENT OF THIS ARM

`G4-as-written` fails in 2 of 4 years, on CT_PEAKER, **in opposite directions** (−2.28 % in 2023,
+4.53 % in 2025) at magnitudes of 0.017 and 0.033 TWh — 0.01–0.02 % of ISO load — while `G4-material`
passes all four. A flat 2 %-per-class band on a 0.74 TWh class is not a bound on a mechanism's reach.

## A5. PROCESS — THE LEVER WAS BUILT AND NEVER RUN FOR EIGHT DAYS

`hydro_budget_period_by_instrument` was built by nyiso-220 on 2026-09-08, **with its screen PRECOMMIT
written and pushed**, and the screen was never executed; the cell sat at `U` through ~15 sessions while
the hydro residual was described as the lane's open item. A sweep this session finds **40 of NYISO's 50
`U` cells have a real `ScenarioConfig` field behind them**. Most are other lanes' rule-28(c) row seeds
and legitimately sit untested here. The distinguishable class — **a lever this lane built AND wrote a
screen for, then did not run** — is the one that cost the time, and `unit_outage_per_unit_clip`
(nyiso-211: "the flag is NOT inert here") is a second member.

## A6. RETRIEVABILITY — all four span legs

| year | branch | commit | files |
|---|---|---|---|
| 2022 | `claude/nyiso-236-hydro-2022` | `4f82866b64b9d96a9046ae33111a4f8c4b2089f8` | 17 |
| 2023 | `claude/nyiso-236-hydro-2023` | `5041ca0dcc20af10137bd8a0dd2d9090544a394e` | 17 |
| 2024 | `claude/nyiso-236-hydro-2024` | `eee2a08b6b7e8fe94bcea4ff0481a43c0dacf63f` | 17 |
| 2025 | `claude/nyiso-236-hydro-span2025` | `e77c597dc75fc287dbcd713868395300d5809a13` | 17 |

`git archive <sha> results/calibration/<dir> | tar -x`. All gitignored, not deleted (rule 31). The 2025
span leg reproduces the screen probe **byte-identically** (max |ΔMW| = 0.000000).

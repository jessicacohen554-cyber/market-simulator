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

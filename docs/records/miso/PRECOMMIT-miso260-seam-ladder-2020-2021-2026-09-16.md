# PRECOMMIT — miso-260: arm MISO's measured seam ladder in 2020 and 2021

```
SESSION  : miso-260        ISO: MISO        KEEPER: 2026-09-16-miso-259-coal-fuel
ARM      : MISO_SEAM_LADDER_BY_YEAR gains 2020 and 2021 — verbatim from the FROZEN
           scripts/data/derive_miso_seam_ladders.py. Zero new ScenarioConfig fields,
           zero free parameters, zero DOF. The gate (miso_seam_measured_ladder) and
           the 2022-2025 entries are UNTOUCHED.
BASIS    : rule 23 [R-FROZEN-DERIVE] — THE SOURCE DATA UPDATED on 2026-09-13.
           rule 14 [R-ACCURATE]  — a measured revealed supply curve replaces a
           gas-elastic proxy fitted on the 2023-2025 training window.
SCREEN   : 2020, ARM vs same-recipe CONTROL at the pre-arm SHA. Named HERE, before
           the screen runs, on the mechanism's OWN measured footprint (below) and
           NEVER on the residual.
```

Everything in this document was established at **ZERO LP**, from committed bytes.

---

## 1. WHAT THIS SESSION KILLED BEFORE SPENDING AN LP

The charter handed forward three levers. **Two are refuted by arithmetic, and a
fourth I opened is refuted by measurement.** Each kill is stated so the successor
does not re-spend it (rule 28 `[R-MECH-MATRIX]` DO-NOT-REDO).

### 1.1 Lever 1, the coal stock-CARRY — REFUTED ON MONOTONICITY, in every year

The charter called this *"the single lever most likely to help 2021's C1 and cost
nothing in 2022."* It cannot help any year, and the proof needs no solve.

A stock carry replaces twelve independent caps `burn[m] <= C` with twelve
cumulative caps `sum_{m'<=m} burn[m'] <= m*C`. **Every path feasible under the
no-carry form is feasible under the carry form** — `burn[m] <= C` for all `m`
implies `cum[m] <= m*C` — so the carry's feasible set STRICTLY CONTAINS the
incumbent's. A ceiling that can only be relaxed can only raise coal.

Coal under the keeper, from the committed run payload:

| yr | coal model | actual | error | gas error |
|---|---:|---:|---:|---:|
| 2020 | 199.42 | 191.67 | **+7.75** | −13.10 |
| 2021 | 237.19 | 239.10 | −1.91 | −29.92 |
| 2022 | 231.04 | 217.08 | **+13.96** | −29.31 |
| 2023 | 180.42 | 174.95 | **+5.47** | −34.89 |
| 2024 | 167.52 | 167.07 | **+0.45** | −30.51 |
| 2025 | 196.19 | 192.10 | **+4.09** | −32.01 |

Coal is OVER-predicted in five of six years and gas is UNDER-predicted in
**all six**. Coal displaces gas. So more coal is the wrong direction for the coal
error in 5/6 years and the wrong direction for the gas error in 6/6 — including
2021, where raising coal by relaxing the cap widens the −29.92 TWh gas miss.
**There is no year in which relaxing the coal ceiling helps.** A carry *with a
minimum operating stock* is a different, non-monotone mechanism and stays open;
a pure carry does not.

### 1.2 Lever 3, a CC_REGULAR level defect — PREMISE FALSIFIED

The charter proposed that the near-equal 2021/2022 misses "argue for a level
defect". Scored across the span the sign FLIPS:

| CC_REGULAR | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| model − actual (TWh) | **+5.92** | −9.46 | −9.47 | −6.39 | **+3.32** | −3.15 |

Not a level defect. (`COAL_BIT`, negative in five of six years at −7.00 / −8.36 /
+0.55 / −3.32 / −3.87 / −4.12, is the class that *does* look level-shifted, and is
a separate open object.)

### 1.3 A coal delivered-PRICE rule-14 repair — REFUTED ON COVERAGE

`FINDING-miso258` proved `_processed-legacy/eia923_monthly_fuel_costs.parquet`
incomplete for coal TONNAGE. It is natural to suspect the same of the delivered
PRICE it feeds through `coal_plant_monthly_pricing`. Measured against the newly
landed `coal-receipts` datatype on the LP's own coal footprint:

| yr | LP coal plants | legacy plants / plant-months / qw $/MMBtu | coal-receipts plants / plant-months / qw $/MMBtu |
|---|---:|---|---|
| 2020 | 85 | 52 / 559 / **1.913** | 52 / 559 / **1.907** |
| 2021 | 85 | 51 / 563 / **2.054** | 51 / 563 / **2.045** |
| 2022 | 85 | 47 / 525 / **2.229** | 47 / 525 / **2.266** |
| 2023 | 84 | 42 / 478 / **2.292** | 42 / 478 / **2.346** |

**Identical coverage, identical plant-months, price within 0.3-2.4 %.** The legacy
extract is deficient for tonnage and NOT for price. No repair available.

### 1.4 Lever 2, the seam-price proxy — the blocker is STALE, and THAT is the arm

`FINDING-miso252-seam-fallback-and-the-923-block-2026-09-10.md` §3(a) recorded the
2020-2022 seam ladder as blocked, naming
`eia-930-interchange/MISO interchange hourly.parquet` ("2023-2025") the **binding
blocker** and `actual_lmp_hourly_MISO.parquet` ("2022-2026") the blocker for the
earlier years. **Both were landed three days later and nobody re-checked:**

| commit | date | what it landed |
|---|---|---|
| `f9259f91` | 2026-09-13 | MISO 2020 + 2021 hourly DA/RT hub LMP (8,760 h each; 2021 DA 8,736) |
| `00249712` | 2026-09-13 | the interchange extract widened to **2020-2026** (PJM/SWPP/SOCO/MHEB all 8,760+ in 2020, 2021, 2022) |

Those two series are the **only** inputs to the primary Q-Q construction; the PJM
western-border price is a diagnostic anchor for the *neighbour overlays*, not an
input to the base ladder. So the base ladder is derivable now.

---

## 2. THE ARM

`MISO_SEAM_LADDER_BY_YEAR` gains 2020 and 2021, verbatim from the frozen
`scripts/data/derive_miso_seam_ladders.py`. **2022 was already armed by miso-252
on this identical basis** (its registry comment states the rule-23 trigger in the
same words), so this is not a new mechanism — it is the completion of a back-fill
that stopped because the price half had not yet landed.

### 2.1 The estimator is unmodified and demonstrably faithful

Run at HEAD, the frozen script reproduces **every previously-committed entry**:

> **256 of 256 entries over 2022, 2023, 2024, 2025 — max |derived − committed| =
> 0.0000.**

(`scripts/probes/_miso260_seam_phase0.py`.) The 2020/2021 rows come off the same
call, so they carry no new method, no new parameter and no fit. With the new rows
in place the table reproduces at **384 of 384**, which the existing
`test_incumbent_registry_reproduces_the_frozen_derivation` now enforces over the
whole span (it previously iterated the table, and the registry-coverage test is
extended from `(2023, 2024, 2025)` to all six years so an unarmed year cannot
reappear silently).

### 2.2 What it replaces — the incumbent's band grid is DEGENERATE

Measured off the keeper's own committed `unit_hourly` seam-band marginal costs:

| year · seam · dir | incumbent band 1 → band 8 | measured ladder band 1 → band 8 |
|---|---|---|
| 2021 South import | **41.97 → 41.97** (all eight identical) | 65.86 → 266.26 |
| 2021 South export | **37.97 → 37.97** (all eight identical) | 53.43 → 17.13 |
| 2021 Manitoba | **39.97 import AND 39.97 export** | imp 31.27 → 547.48, exp 26.52 → 14.21 |
| 2021 PJM import | 48.49 → 49.02 (**$0.53** over eight bands) | 16.17 → 82.19 |
| 2020 South | **26.55 / 22.55**, all sixteen bands | imp 25.69 → 81.95, exp 22.75 → 8.88 |

A band grid with no spread clears all-or-nothing. That is the bang-bang miso-252
§2.4 measured, and it is visible in the keeper's own dispatch: **four 2021 PJM
import bands sit within 1 % of their own maximum in EVERY hour of the year.** The
Manitoba row is worse than flat — import and export at the *same* price is a
same-seam wash the ladder's no-wash reconciliation forbids by construction.

### 2.3 THE MECHANISM'S OWN MEASURED FOOTPRINT — and the screen year

Model net seam flow (from the keeper's own `refimp`/`refexp` band rows) against
the EIA-930 measured net, per seam, TWh:

| yr | ladder? | PJM | SPP | South | Manitoba | **Σ \|err\|** |
|---|---|---:|---:|---:|---:|---:|
| **2020** | **no** | −26.40 | +2.61 | **+6.37** | +0.91 | **36.29** |
| **2021** | **no** | +10.36 | **−5.14** | **+9.35** | +0.56 | **25.41** |
| 2022 | yes | −2.90 | −2.25 | −0.82 | −2.87 | 8.84 |
| 2023 | yes | +1.65 | +0.30 | +2.01 | +0.15 | 4.11 |
| 2025 | yes | −1.99 | +0.01 | +2.84 | +0.37 | 5.21 |

Bold entries carry the **WRONG SIGN**: 2021 SPP model −2.98 against a measured
+2.15; 2021 South model +1.69 against −7.66; 2020 South model +3.44 against −2.93.

> **SCREEN YEAR = 2020**, because its Σ|per-seam error| of **36.29 TWh** is the
> largest measured footprint in the span and its PJM seam alone is off by
> **26.40 TWh**. This is a measured-footprint choice, exactly as rule 29
> `[R-SCREEN]` requires, and it is **not** the residual: 2021 carries the larger
> C3b miss (0.285 vs 0.246) and is NOT the screen year.

### 2.4 It cannot touch the train tier, by construction

`inject_miso_seam_ladder_prices` reads `MISO_SEAM_LADDER_BY_YEAR.get(year)`. The
2022-2025 entries are byte-identical, so **2023, 2024 and 2025 solve exactly as
the keeper did.** G-NOFLIP on the train tier is met structurally, not by
measurement. The neighbour overlays carry no 2020/2021 key and degrade to the base
ladder — the documented behaviour of `miso_seam_neighbour_*`, verified by reading
the injector, not a new path.

### 2.5 Rule 13 forward story, rule 24 registry, rule 25 scope

Rule 13 `[R-MEASURED]`: the ladder is a **revealed supply curve**, not an outcome
pinned back in — the LP still clears every band economically against its own
hourly internal price, nothing is forced, and at price extremes even the base band
backs off. The forward analogue is the pooled multi-year ladder the derive script
prints; forecast years keep the gas-elastic formula (the same two-track design as
`hr_by_year`). Rule 24 `[R-REGISTRY]`: no new tunable — the gate
`miso_seam_measured_ladder` is already a `ScenarioConfig` field and already in
`run_config.json`; what changes is which years that gate reaches, exactly as the
2022 addition did. **Stated plainly rather than buried**: because the table is not
a `ScenarioConfig` field and `model/interchange/spec.py` is explicitly OUT of the
`solve_surface.SURFACE_MODULES` scope, this change moves **no cache key** — so a
shard must solve cold, and the shard prompt carries that as a hard stop. Rule 25
`[R-ISO-SCOPE]`: MISO's own measured series only; no other ISO's table is touched.

---

## 3. PRE-REGISTERED STOP GATES — a screen may KILL an arm and NEVER promote one

Scored on the 2020 screen pair (ARM at this PRECOMMIT's SHA, CONTROL at the
pre-arm `origin/main`). **None is the target residual.** C3a/C3b are REPORTED ONLY
and are not gates; a screen gated on them would be the fitted-mechanism selection
rule 1 `[R-STRUCT]` forbids.

| gate | passes iff |
|---|---|
| **G-FOOTPRINT** | The arm reprices exactly the 64 MISO seam band rows (4 seams × 2 directions × 8 bands) and **nothing else**: every non-seam unit's `mc` is identical between the two bundles. |
| **G-DIRECTION** | Σ\|per-seam net-flow error\| against the EIA-930 measured net **FALLS** from the control's 36.29 TWh, and the 2020 South seam's sign error (+3.44 model vs −2.93 measured) is **corrected in sign**. |
| **G-SPREAD** | The bang-bang signature weakens: the number of seam band rows pinned within 1 % of their own maximum in ≥95 % of hours does not rise, and the South/Manitoba seams — degenerate in the control — show a non-zero band spread in the arm. |
| **G-NOFLIP** | No non-target **load-bearing** criterion goes PASS → FAIL in 2020. C1 is the live one (2020 currently passes every class); C2 and C4 must hold. |
| **G-BALANCE** | `slack` and `dump` both remain **0.0000 TWh**. A seam repricing that buys its flow change with unserved energy is not a repair. |

**A screen that kills the arm is the session's result**, reported with its numbers,
and the remaining years are never spent.

---

## 4. CONTROL, AND WHY I AM NOT CLAIMING G-DRIFT FORM 4

The keeper's recorded `git_sha` **`3b0a12b441d3c518742098713b203cafeb39f10e` IS
reachable** (unlike miso-259's, whose shard branch had been deleted — rule 33(d)).
But against it the solve path has moved **37 files / 3,274 insertions**, including
a new `model/lp/hydro_cascade.py` (+261) and `data/hydro.py` (+201), and this
session will not certify that hunk-by-hunk. Form 4 is therefore **NOT claimed**.

Instead the screen is a **same-recipe A/B one commit apart**: the control shard
pins `origin/main` as of this session's start, the arm shard pins this PRECOMMIT's
commit, and the ONLY solve-affecting difference between the two SHAs is the two
table entries. That is strictly better evidence than a drift audit — a two-commit
A/B cannot be contaminated by drift at all — and it costs one extra shard.

Recorded mechanically and worth keeping: MISO's solve-surface fingerprint is
`9f0845000dc8af6e` at both the keeper and HEAD (`moved: {}`), and this change
cannot move it because `model/interchange/spec.py` is out of scope.

---

## 5. SHARDING (rules 32 / 34)

The parent runs **zero LP** (rule 32(a)).

* **Screen**: two single-year shards, 2020 ARM and 2020 CONTROL, in parallel.
  Rule 32(b) expressly permits a single-year shard for a rule-29 screen.
* **Span, only if the screen clears**: **ONE shard**, one
  `--year 2020 2021 2022 2023 2024 2025` invocation, into ONE bundle, with a
  stated ~120-minute budget. This follows CLAUDE.md rule 32(b) as written rather
  than the per-year fan-out the charter recommends; the fan-out's composition
  traps (the `legitimacy_diagnostics.json` merge and the `_shared` input store)
  are then structurally absent. The divergence from the charter is deliberate and
  is reported.
* Every shard pushes its **whole** bundle to its own branch by a `.gitignore`
  NEGATION plus a plain `git add` — never `git add -f` (rule 34(a)).
* Recovery is recorded by **full SHA**, never branch name (rule 33(d)).

---

## 6. WHAT THIS ARM DOES NOT CLAIM

* It does not close the passthrough slope. `FINDING-miso256` §0's 4.63-against-8.41
  gas slope is a **coal-on-the-margin** object, and the phase-0 table in §1.1 shows
  its live form: gas under by 29-35 TWh in five of six years with coal over. That
  is the standing MISO defect and it is **not** this arm's.
* It does not touch C3c 2022, which is ledgered and non-downgrading.
* A held-out year can neither certify nor decertify the ISO (rule 30(c)). MISO's
  headline is the train tier, which this arm cannot move.

# PRECOMMIT — screening the MONTHLY ERCOT delivered-gas level anchor (ercot-254)

> Written and pushed **before any solve** (rule 29 `[R-SCREEN]`). Everything
> declared here — the arm, the screen year, the control form, the gate values and
> the rule-23 non-re-derivations — is fixed at this commit and is not rewritten
> afterwards. The measurement that motivates it is
> `docs/FINDING-ercot254-2021-offer-level-root-cause-2026-09-07.md`, which is
> zero-LP and read-only.

## 1. The arm — one delta, zero free parameters

`ercot_ep_gas_basis_monthly=true` (new ScenarioConfig field, default **False**,
ERCOT-gated, no-op unless `ercot_zonal_gas_basis` is also armed). It replaces the
annual mean in `ercot_electric_power_gas_basis` with the **same measured series at
its native monthly resolution**, `basis[m] = EP[m]/1.036 − HH[m]`, expanded through
`_shared._expand_monthly_to_hourly` — the identical hour→month seam the monthly gas
price it is added to already uses (rule 19 `[R-ONE-MECH]`).

* **No new data, no new source, no new scalar** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).
* **Mean-preserving by construction.** The mean is linear, so
  `mean(EP[m] − HH[m]) ≡ mean(EP) − mean(HH)`: the annual level is untouched and
  the whole change is a *relocation* of a measured quantity back to the months it
  was measured in (rule 14 `[R-ACCURATE]`). Only month-length weighting separates
  the two hour-weighted annual means — worth **0.350 $/MMBtu in 2021** and under
  **0.05** in every training year. Both figures are declared here, before the solve.
* **Forward-inert by construction.** A year with no EP rows returns `None` under
  both forms, so every forecast solve and every non-ERCOT solve is byte-identical.
* Registered in `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
  at `"False"` in the same commit as the field (the nyiso-119 discipline), so every
  existing ERCOT cache key — the designated keeper's included — is byte-stable.

## 2. The screen year, named ex ante on the mechanism's OWN footprint

**2025.** Chosen on the hour-weighted mean `|monthly − annual|` level correction —
the mechanism's own repricing magnitude, computed from the input file alone and
committed in the FINDING §6 **before this arm was built**:

| training year | mean \|Δ\| $/MMBtu | = $/MWh at CC hr 7.29 | max month \|Δ\| |
|---|---|---|---|
| 2023 | 0.1243 | 0.906 | 0.351 |
| 2024 | 0.2064 | 1.505 | 0.848 |
| **2025 — the screen year** | **0.2412** | **1.759** | **0.615** |

This is **not** the year with the largest residual and was never checked against
one. 2021 (footprint 8.183) is the *symptom* year and is **not** solved in this
session's screen: nothing may be identified on a held-out year (rule 22 step 3).

## 3. The control — G-CTRL **form 2** (same-HEAD A/B), and why not form 4

Rule 29(b) makes form 4 (the keeper's committed bundle as control) the default,
voidable only by a **LIVE** hunk in a `G-DRIFT` code audit. **G-DRIFT was run and
does not support form 4 here.** `git diff 0207d69daca8452a65200e63da3a57a00fbc19fe
HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` returns **172 files,
153,004 insertions / 28,339 deletions**, including `pipeline/solve.py` (+508),
`runner.py` (+1236), `results/cache.py` (+729) and `pipeline/backcast_config.py`
(+277). Classifying every hunk on that diff INERT is not a judgement this session
can make honestly, and rule 29(b) is explicit that a "files changed, therefore
void" heuristic with no audit behind it is not a reason to spend an LP — but the
converse also holds: an *unaudited* diff is not a licence to assert form 4.

So the screen spends **one control solve on the screen year only** — 2025 at HEAD
with the gate off — and the A/B is arm-minus-control at identical HEAD, identical
recipe, one flag apart. This is the strongest control form available and it costs
one extra single-year LP, not a span.

## 4. Gates — STRUCTURAL, and STOP-ONLY

The screen **may kill this arm; it may never promote it**, it contributes to no
determination, and **no gate is read against C3a or C1** — the two criteria the
FINDING predicts this mechanism moves. Reading a screen against its own target
residual is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one
year at a time.

**Zero-LP gates, evaluated BEFORE either solve** (clause 0 — an arm that fails one
never reaches an LP):

| id | question | STOP threshold |
|---|---|---|
| **G-1 IDENTITY** | On the reconstructed 2025 fleet, does the armed delivered-gas array equal the unarmed array plus the pre-computed `(monthly − annual)` level vector, unit-hour by unit-hour? | any \|residual\| > 1e-9 $/MMBtu ⇒ STOP |
| **G-2 CONFINEMENT** | Do only **gas** rows move, and does the 2025 move stay inside the mechanism's own arithmetic? | any non-gas row moves, **or** max \|Δ delivered\| > 0.62 $/MMBtu (the 0.615 max-month Δ + tolerance) ⇒ STOP |
| **G-3 LEVEL** | Is the annual hour-weighted delivered level essentially unmoved, as the mean-preservation identity requires? | \|Δ annual capacity-weighted delivered gas\| > 0.05 $/MMBtu ⇒ STOP |

**Post-solve gates (2025 arm vs 2025 control):**

| id | question | STOP threshold |
|---|---|---|
| **G-4 MAGNITUDE** | Does the price response have the order of magnitude the pre-solve delta implies (0.2412 $/MMBtu × ~7.3 heat rate ≈ $1.76/MWh at the gas margin)? | \|Δ system load-weighted LMP\| > $5.00/MWh ⇒ STOP (an order of magnitude past the arithmetic means something other than this term fired) |
| **G-5 NON-TARGET CRITERIA** | Does any **non-target** load-bearing criterion flip PASS → FAIL? | C2 or C3b flips PASS → FAIL ⇒ STOP |
| **G-6 PROTECTIVE** | Do the protective criteria hold? | C6 or C8 flips PASS → FAIL ⇒ STOP |
| **G-7 SHED** | Does the arm manufacture unserved energy? | arm slack or dump exceeds the control's by > 1.0 MWh ⇒ STOP |

**C1 and C3a are REPORTED at full magnitude in both arms and are gated in NEITHER
direction.** A C3a improvement in 2025 is not evidence for this arm and will not be
quoted as any; a C3a regression is not evidence against it either. What decides
promotion is the identification in §1 — a measured series used at the resolution it
was measured at — exactly as rule 1 requires.

## 5. What happens after the screen

* **Screen fails a gate** → the arm is killed, that is the session's reported
  result, and the remaining years are never spent.
* **Screen clears** → the full training span `--year 2023 2024 2025` as ONE
  invocation and ONE bundle (rule 16 `[R-ALLYEARS]`), gated and, if it clears,
  proposed for promotion. The 2021 rung is then **re-tested** as a rule-22
  touchpoint — step 4 of the touchpoint loop, never step 3 — and its result is
  reported, never tuned on. A held-out rung cannot decertify ERCOT either way
  (rule 30(c)); ERCOT's determination is and stays the train-tier verdict.

## 6. Declared non-re-derivations (rule 23 `[R-FROZEN-DERIVE]`)

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO` and `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["ERCOT"]`
(the 2.2494 shared anchor and the per-zone table) are **NOT re-derived in this
session**, in either arm. They are derived from the keeper reconstruction's own
resolved fuel array, which this change perturbs slightly in the training years, so
a re-derivation is arguable — and it is deliberately declined here so the screen
measures **one** delta. Any re-derivation is a separate, source-cited change under
rule 23 and never a residual-driven one.

Two further 2021-only defects the FINDING names are likewise **NOT touched** in
this session, so the screen stays single-delta: the absent 2021 West/Panhandle
`neg_day_freq` (which falls back to a 2024 default and produces inverted regimes),
and the `meta.json` mis-recording of `ercot_zonal_gas_basis` /
`ercot_west_netload_gas_shape` as `false` on runs that armed them.

## 7. Bundle retention (rule 29(c))

The screen bundle and its control are **deleted from `results/calibration/` before
this PR merges**. Every number this session will ever cite from them is written
into the session's RESULT doc, and git history is the record for the bytes.

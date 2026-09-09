# PRECOMMIT — nyiso-222: the owner-directed +5% offer-curve move

**Session:** nyiso-222 · **ISO:** NYISO (only) · **Date:** 2026-09-09
**Branch:** `claude/nyiso-offer-curve-plus5-u59cfj`
**Status:** written and pushed **BEFORE THE SOLVE** — rule 1 `[R-STRUCT]` condition (c).

---

## 1. The instruction, verbatim

> **Owner, 2026-09-09:** "Ok offer curve should be moved +5%".

This rides the **rule 1 `[R-STRUCT]` AUTHORIZED PRICE-TUNING CHANNEL** (owner amendment
2026-09-05), cross-referenced by rule 13 `[R-MEASURED]`'s single exception and rule 20
`[R-DOF]`'s R-AY cross-reference. Tuning the registered `offer_curve_by_group` band
multipliers on price is **NOT** the forbidden fitted adder. The five conditions:

| # | Condition | How it is discharged here |
|---|---|---|
| (a) | Bands only — never `phys_*`, never the structural shares, never a new adder | §2 + the §3 confinement proof: 40 bands over 4 authorized names, 0 violations |
| (b) | ONE config across EVERY scored year | One `--offer-curve-json`, one invocation `--years 2023 2024 2025`, one bundle |
| (c) | Ex ante, declared before the solve, **never swept** | This document, pushed pre-solve. §6 states the no-sweep commitment |
| (d) | Merit-order movement is INTENDED, not a defect | §5 predicts and welcomes the fossil↓ / imports↑ shift |
| (e) | Declared in the attestation's `authorized_price_tuning` block | §7; C6 FAILS without it |

---

## 2. The channel and its scope, exactly

**Move:** multiply by **1.05** the four authorized bands — `committed`, `econ_low`,
`econ_high`, `peak`.

**Never touched:** `phys_committed`, `phys_econ_low`, `phys_econ_high`, `phys_peak`
(measured physics); `econ_low_share`, `pct_peaking` (structural shares); no new adder,
offset, haircut or proxy anywhere.

**Delivery:** `replay_keeper.py --offer-curve-json`, which lands in
`offer_curve_overrides` and merges **per band** into `offer_curve_by_group`. Everything
not listed in the file is therefore untouched *by construction*, not by inspection.

**Scope = the 10 classes both present in NYISO's resolved table AND accepted by the
offer-curve router:** `CC_REGULAR`, `CC_CHP`, `CT_CHP`, `CT_PEAKER`, `ST_GAS`, `COAL`,
`COAL_BIT`, `COAL_LIGNITE`, `COAL_PRB`, `COAL_WC`.

**Two exclusions, both measured, stated rather than absorbed:**

1. **`CC_INTERMEDIATE` / `CT_INTERMEDIATE` / `ST_GAS_INTERMEDIATE`** — present in the
   resolved table but **refused by the router**, and **dead for NYISO regardless**: the
   keeper carries `cc_intermediate_split=False`, `ct_intermediate_split=False`,
   `st_gas_intermediate=False`. Excluding them costs nothing.
2. **`ST_CHP`** — router-valid, and NYISO genuinely dispatches it (1.447 TWh model in
   2025), but it has **no entry in NYISO's resolved `offer_curve_by_group`**. There is
   no registered band to scale. Inventing one would be a **NEW value, not a move**, which
   rule 1(a) forbids. It is therefore left alone, and its absence is a *known limit on the
   channel's reach*, not an oversight.

The scope is generated deterministically (never hand-typed) from the keeper's own
`run_config.json` — the generator is reproduced in §3.

---

## 3. Phase-0 confinement proof (zero LP) — **PASS**

Regenerated from `results/calibration/nyiso_fuelvintage_A/run_config.json` and re-verified
against it:

```
classes in base table: CC_CHP CC_INTERMEDIATE CC_REGULAR COAL COAL_BIT COAL_LIGNITE
                       COAL_PRB COAL_WC CT_CHP CT_INTERMEDIATE CT_PEAKER ST_GAS
                       ST_GAS_INTERMEDIATE
classes written:       CC_CHP CC_REGULAR COAL COAL_BIT COAL_LIGNITE COAL_PRB COAL_WC
                       CT_CHP CT_PEAKER ST_GAS
n_classes: 10    n_bands: 40

bands moved: 40   classes: 10
ratios all exactly 1.05: True
UNTOUCHED band names: committed, econ_high, econ_low, econ_low_share, pct_peaking, peak,
                      phys_committed, phys_econ_high, phys_econ_low, phys_peak
VIOLATIONS: NONE
  CC_REGULAR: committed 0.9->0.945,  peak 2.25->2.3625
  CT_PEAKER:  committed 1.35->1.4175, peak 4.0->4.2
  ST_GAS:     committed 1.05->1.1025, peak 4.2->4.41
```

(`committed`/`econ_low`/`econ_high`/`peak` appear in the UNTOUCHED list because they also
exist on the three **excluded** `*_INTERMEDIATE` classes, which the file deliberately does
not carry. The load-bearing readings are that **`phys_*`, `econ_low_share` and
`pct_peaking` never appear in the override**, and that every moved ratio is exactly 1.05.)

`parse_offer_curve_json` accepts the file without raising.

---

## 4. G-DRIFT — keeper `da2e7076` → HEAD `74671cca`

The keeper's `git_sha` **is reachable on `main`** (`git merge-base --is-ancestor` → yes),
so this is a normal diff, not a reconstruction. Audited paths: `src/market_sim`,
`scripts/run_calibration.py`, `scripts/run_calibration_full.py`, `scripts/lib`,
`data/raw/_validation-source`, `data/raw/reference`.

```
 src/market_sim/config/constants.py              | 65 ++++++++++++++++-----
 src/market_sim/config/solve_surface_declared.py |  1 +
 2 files changed, 55 insertions(+), 11 deletions(-)
```

| Hunk | Classification | Reason |
|---|---|---|
| `constants.py` — `NUCLEAR_MONTHLY_CF_BY_YEAR`, NEISO block | **INERT** | **Comment-only.** Filtering the diff to non-comment changed lines returns **zero lines**. No value moved. It is additionally inside NEISO's sub-dict, which a NYISO solve never reads. |
| `solve_surface_declared.py` — `+ "HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT": {"NYISO": "0d6bce3ba875ed62"}` | **INERT** | Pure timing/keying accounting. `DECLARED` is read at exactly one site — `solve_surface.py:330`, the frozen-drop lookup inside the fingerprint — whose consumers are `results/cache.py` (`cache_key`), `pipeline/persist.py` and `results/export.py`. It selects a **result-reuse directory** and the recorded `solve_surface.json`; it never reaches the LP matrix, the offer path or any bound. The underlying `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` **value** is unchanged in this window (the only `src/market_sim` value change would have shown in the diff above, and `constants.py`'s is comment-only). |

**ALL HUNKS INERT ⇒ G-CTRL form 4 is VALID and the committed keeper
`2026-09-09-nyiso-221-fuelvintage-span` IS the control. No control solve is spent**
(rule 29(b) `[R-SCREEN]`).

---

## 5. PRE-REGISTERED PREDICTIONS — written before any new number is read

**Baseline (keeper, committed):**

| Criterion | 2023 | 2024 | 2025 |
|---|---|---|---|
| C3a mean LMP (model vs actual RT-lw) | 33.65 / 32.25 = **+4.3%** | 40.15 / 38.12 = **+5.3%** | 61.60 / 66.43 = **−7.3%** |
| C3c hours > $300 (model vs RT actual) | 2 vs 10 | 0 vs 13 | 3 vs 42 |
| C8 ST_GAS forced share (cap 30%) | 16.1% | 20.9% | 18.1% |

**C3a tolerance, looked up first:** `PRICE_MEAN_TOL = 0.10`, `PRICE_MEAN_COMMERCIAL = 0.10`
(`scripts/calibration_verdict.py:585-586`) — **±10% target and commercial, coincident**.

### 5.1 C3a — UP in all three years, by LESS than 5%. **PASS predicted in all three.**

The direction **fights two of the three years**: the model is already *above* actual in
2023 and 2024 and below only in 2025, so a uniform +5% makes 2023 and 2024 **worse** and
2025 **better**. That is expected and is not a reason to alter the value.

The rise must be **less than the full 5%** because a large share of NYISO's
load-weighted hours are set by imports, hydro, nuclear and `ST_CHP` — none of which this
channel touches (`ST_CHP` by the §2 exclusion, the rest by having no offer band at all).
I estimate the marginal-hour **pass-through at 50–85%**, giving:

| pass-through | 2023 | 2024 | 2025 |
|---|---|---|---|
| 50% | +6.9% | +8.0% | −5.0% |
| **68% (central)** | **+7.9%** | **+8.9%** | **−4.1%** |
| 85% | +8.8% | +9.8% | −3.3% |
| 100% (mechanical ceiling) | +9.6% | +10.6% | −2.6% |

**Explicit verdict prediction: C3a PASSES in all three years — no PASS→FAIL flip.**
The arithmetic behind that call, and the one year that is genuinely at risk:

- **2023 CANNOT fail.** Even at 100% pass-through it lands at **+9.6% < 10%**. Failing
  requires **108.5%** pass-through, which the channel cannot mechanically produce.
- **2024 IS the year at risk.** It fails iff pass-through exceeds **88.8%**
  (headroom $1.78/MWh against a $2.01 full-pass move). My central estimate of 68% clears
  it, but the margin is thin and **I am pre-committing that a 2024 C3a FAIL is a live and
  named possibility, not a surprise.**
- **2025 CANNOT fail** and improves materially, from −7.3% toward roughly −4%.

### 5.2 C3c — **IMPROVES, and stays a ledgered CAVEAT.** Not a PASS.

The peak bands rise (`CT_PEAKER` 4.0→4.2, `ST_GAS` 4.2→4.41), so more hours clear >$300.
But the gate is **[0.5×, 2×] of the RT actual** (with a `|Δ|≤10h` leniency only when the
actual is <10h, which no year here satisfies), i.e. the model needs **≥5 h (2023),
≥6.5 h (2024), ≥21 h (2025)** from a base of 2 / 0 / 3. A 5% lift on the peak band cannot
move 3 → 21. **Prediction: C3c remains FAIL-reclassified-to-CAVEAT (`ACCEPTED MODEL-CLASS
LIMITATION`) in all three years**, still the single ledgered caveat, still counted at full
magnitude on the determination basis. Under rubric v3.3 that does not downgrade
`CALIBRATED`.

### 5.3 C1 — intra-fossil merit order barely moves; fossil↓ / imports↑.

The move is uniform across the ten scaled classes, so **relative** fossil merit order is
nearly unchanged; what shifts is **fossil versus the unscaled resources** (imports, hydro,
nuclear, `ST_CHP`). Predict **fossil energy slightly DOWN, imports slightly UP**.
`CC_REGULAR` is the big class and the tightest C1 cell is **2024 `CC_REGULAR` at +2.91 TWh
against a ±3.98 TWh band (+2.5pp against ±3pp share)** — the move pushes it **toward**
the band, so C1 should improve, most visibly in 2024. **Predict C1 stays PASS.**

### 5.4 C8 — forced share ticks UP; no cap crossed.

Floors are unchanged, so forced MWh is constant while fossil energy falls slightly ⇒ the
forced **share** rises. The binding class is `ST_GAS` at 16.1 / 20.9 / 18.1% against a
**30%** cap. A ≤5% fall in class energy raises those to at most ≈16.9 / 22.0 / 19.1%.
**Predict C8 stays PASS with no cap crossed.**

---

## 6. NO SWEEP — condition (c), stated in advance

**+5% is the OWNER'S EX ANTE VALUE.** It was set by the owner before any result exists and
**it will never be swept.** If it makes a gate worse — including the 2024 C3a FAIL named
explicitly in §5.1 — **that is REPORTED, not re-tuned.** Trying −5%, +2%, or any other
factor after seeing the result would be selecting a multiplier by which one makes a
criterion pass: precisely the per-criterion fitted-mechanism selection that condition (c)
refuses and that rule 1 `[R-STRUCT]` exists to forbid. There will be exactly one arm.

**Condition (b):** one config across all three scored years. No per-year value, now or
after the numbers land.

---

## 7. Governance owed by the run

- **Condition (e) + C6** — the attestation carries an `authorized_price_tuning` block
  naming the channel (`offer_curve_by_group` bands), the value (**×1.05**), and the owner
  ruling (2026-09-05 amendment to rules 1/13). **C6 FAILS without it.**
- **Rule 21 `[R-DOF]`** — `offer_curve_by_group` is now a **free parameter carrying a tuned
  value**. Its identification source is written as
  **"price residual, authorized channel (rules 1/13 amendment 2026-09-05)"** — the *ruling*,
  not a measured input — and reported at full magnitude on the determination basis. Per
  rule 20's R-AY cross-reference its presence does **not** by itself make the residual it
  closes an open root-cause issue, and **no gate moves**.
- **Rule 28 `[R-MECH-MATRIX]`** — update **only**
  `docs/codebase-site/data/mechanism-matrix/NYISO.js`, cell `offer_curve_by_group`.
- **Rules 29(c) / 31 `[R-RETAIN]`** — the bundle is **gitignored** (that, not `rm`, is what
  discharges delete-before-merge) and **NOTHING is deleted before the owner rules on
  promotion**. The promotion question is asked **explicitly** in the final report.
- **Rule 30(c)** — a held-out year never downgrades NYISO. The ladder is **2022 alone**;
  2020 and 2021 are data-blocked with both authorizations UNSPENT
  (`docs/FINDING-nyiso-2020-touchpoint-data-blocked-2026-09-09.md`).
- **If it promotes** — rule R-T / Q34 requires re-keying **both**
  `frontend/data/forecast/program-status.json` `gate.a_keeper_marker` **and** the NYISO
  keeper assertion in `tests/scoring/test_ff_readiness_battery.py`, **in the same PR**.

---

## 8. Disposition

Every criterion is reported at **full magnitude** and the **owner rules** under the
standing formula ("if structural integrity improves but gates regress that may still be a
keeper"). This session does **not** self-promote on an improved residual and does **not**
withhold on a worsened one. The owner set the value; this session measures and reports it.

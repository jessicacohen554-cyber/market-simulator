# ADDENDUM — nyiso-222: the 2022 validation touchpoint on the +5% arm

**Session:** nyiso-222 · **ISO:** NYISO · **Date:** 2026-09-09
**Pushed BEFORE the 2022 solve.** Extends
`docs/PRECOMMIT-nyiso222-offer-curve-plus5-2026-09-09.md`.

## 1. The instruction and the authorization

> **Owner, 2026-09-09:** "Ok you should be running 2022 bc that's the year that is off.."

**Authorization checked on latest `main` (`5c80dfdc`) BEFORE any LP:**

- 2022 is **validation tier** (rule 22 `[R-HOLDOUT]`).
- `calibration-complete.json` → **NYISO holds `complete`**, declared 2026-09-06 by owner
  ruling in session nyiso-209 ("Ok declare it and run 22"), and its `keeper` field is
  keyed to the current designated keeper `2026-09-09-nyiso-221-fuelvintage-span`.
  `withdrawn` is **empty**.
- `holdout-freeze.json` → `active: true` but **`scope.tiers = ["locked_test"]` only**; the
  file states the validation tier (2020–2022) was lifted 2026-08-26 and is governed by the
  `complete` marker + `--holdout-authorized` alone.
- `final` is **NOT** granted and no locked-test year is touched by this run.

**The spend is therefore authorized.** It is run with `--holdout-authorized`, and the
R-AZ registration gate re-checks the marker at registration.

## 2. What this run is, and what it can never be

It is the **+5% arm's frozen recipe replayed on a held-out year** — the same config, one
more year. Under rule 22 that makes it **iterable diagnostic evidence and model-SELECTION
evidence, never a certified out-of-sample skill number**, and under rule 30(c) **a
held-out year never downgrades NYISO**: the ISO's determination is the train-tier
(2023–2025) verdict and nothing else.

**THE +5% IS NOT RE-OPENED BY THIS RUN.** The value was set ex ante by the owner, declared
in the PRECOMMIT, and is **never swept** (carve-out condition (c)). Rule 22 additionally
forbids fitting *anything* to a touchpoint year. So whatever 2022 returns, **the multiplier
is not resized in response** — not to +8%, not to +12%, not back to +3%. Selecting a factor
because it makes a criterion pass is the fitted-mechanism selection both rules exist to
forbid, and doing it against a validation year is that same error twice.

## 3. THE 2022 BASELINE REFRAMES THE PROBLEM — price is not the only thing that is off

Scored from the committed keeper touchpoint `2026-09-09-nyiso-221-fuelvintage-tp2022`
(artifacts only, no solve). **DETERMINATION: NOT-YET**, on **three** failing criteria:

| criterion | 2022 value | band | verdict |
|---|---|---|---|
| **C1 fuelmix — CC_REGULAR** | model **36.553** vs actual **31.564** TWh = **+4.99 TWh, share +3.8pp** | ±3.5 TWh & ±3pp | **FAIL** |
| **C3a mean LMP** | model **69.92** vs actual **81.12** = **−13.8%** | ±10% | **FAIL** |
| **C3b price shape** | NRMSE **0.242** | ≤0.20 | **FAIL** |
| C2 gas family | 61.80 vs 56.98 TWh | via C1 | PASS (flags CC_REGULAR) |
| C3c tail | 10 h vs 101 h actual | [50.5, 202] | CAVEAT (ledgered) |
| C8 ST_GAS forced | 22.7% | <30% | PASS |

**The two big misses are one defect, and they point the same way.** The model generates
**5 TWh too much CC_REGULAR** while clearing **13.8% too cheap**. Too much cheap combined-
cycle energy is exactly what suppresses a price. That is why an offer-curve lift is a
*coherent* direction here in a way it was **not** in 2023/2024 (where the model was already
*above* actual and the lift could only hurt). The owner's instinct that 2022 is the year
this channel is aimed at is well-founded on the sign.

**Whether it is large enough is a different question, and §4 says no.**

## 4. PRE-REGISTERED PREDICTIONS — numbers before any number is read

Derived from nyiso-222's own measured **constant-dollar passthrough law** (RESULT §2.2),
not from a fresh guess. Measured passthrough vs mean price: 0.258 @ $33.65, 0.274 @ $40.15,
0.340 @ $61.60 $/MWh per 1% of band; least-squares `pt = 0.00297·price + 0.1566`, which at
2022's $69.92 model mean gives **0.364 $/MWh per 1%**.

| | prediction | verdict call |
|---|---|---|
| **C3a** | +$1.30 to +$2.20/MWh → model **71.2–72.1** → **−12.2% to −11.1%** (central ≈ **−11.6%**) | **STILL FAILS** ±10% |
| **C1 CC_REGULAR** | −0.1 to −0.4 TWh → **36.2–36.5 TWh**, still ≈ **+4.7 TWh** over | **STILL FAILS** |
| **C3b** | improves (model is *below* actual, so a lift helps here — the opposite sign to 2023/24) → **0.225–0.238** | **STILL FAILS** ≤0.20 |
| **C3c** | 10 h → 10–14 h vs 101 h actual | **stays ledgered CAVEAT** |
| **C8** ST_GAS | 22.7% → 22.4–23.1% | **PASS**, no cap crossed |
| **determination** | **NOT-YET, unchanged** — all three failing criteria improve, none closes | |

**PASS on C3a requires model ≥ $73.01, i.e. +$3.09/MWh. A 5% move buys ~$1.8 of it.**

### 4.1 Arithmetic that is NOT a proposal

At 0.364 $/MWh per 1%, closing the 2022 C3a gap would take a **~8.5% band lift (×1.085)**.
This number is recorded because it is the honest answer to the obvious next question, and
because computing it costs nothing. **It is not a recommendation and must not be adopted**:
adopting a multiplier *because it makes a criterion pass* is precisely what carve-out
condition (c) refuses, and fitting it to a **validation year** is what rule 22's touchpoint
loop forbids outright. If the level is to move again, the identification must come from
2023–2025 (the only place fitting ever happens) or from measured conduct — never from this
row.

**And it would not fix 2022 anyway.** Even a lift that lands C3a inside the band leaves
`CC_REGULAR` roughly **+4.8 TWh** over actual, because nyiso-222 measured the volume
response at only **−0.14 TWh per 5%**. The price and the volume miss are one defect —
too much CC — and the offer channel moves the *price* symptom ~35× more efficiently than
the *volume* cause. **The structural successor for 2022 is whatever is over-dispatching
CC_REGULAR, not a bigger multiplier.**

## 5. Method

One year, one invocation, the arm's exact frozen config:

```
uv run python scripts/replay_keeper.py results/calibration/nyiso_fuelvintage_A \
  --years 2022 --holdout-authorized \
  --offer-curve-json results/calibration/nyiso222_offer_curve_plus5.json \
  --out-dir results/calibration/nyiso222_offer_plus5_tp2022
```

Rule 16 `[R-ALLYEARS]` is not engaged: this is a **validation touchpoint**, which is a
single held-out year by construction, not a single-year keeper. The train-tier bundle
remains the full `--years 2023 2024 2025` span already registered.

On completion: stamp it to the keeper's lineage per rule 30 `[R-TOUCHPOINT-FOLD]`
(`stamp_touchpoint_holdout.py`), register it, rebuild the status ladder
(`build_status.py --iso NYISO`), and report every criterion at full magnitude.
Rule 31 `[R-RETAIN]`: the bundle is gitignored and **nothing is deleted** before the owner
rules.

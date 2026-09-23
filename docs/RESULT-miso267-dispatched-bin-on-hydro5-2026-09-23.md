# RESULT — miso-267: the dispatched-bin denominator on the hydro-5 keeper. An exact gate wash, again.

```
RUN     : 2026-09-23-miso-267-dispatched-bin  (results/calibration/miso267_dbd_span, 2020-2025)
RECIPE  : keeper 2026-09-22-hydro-5-miso-ror + unit_outage_dispatched_bin_denominator=true. ONE flag.
PREREG  : docs/PRECOMMIT-miso267-dispatched-bin-on-hydro5-2026-09-23.md (pinned 3ea64fa5, before any shard)
BENCH   : the parts miso-267 STEP 1 regenerated; registering this run moved NONE of the 44 (sha256)
VERDICT : full span NOT-YET (= keeper), train tier 2023-2025 CALIBRATED (= keeper). Keeper UNCHANGED.
```

## 1. The gate table

Both runs scored by `calibration_verdict.py` against the same committed bench.

| criterion | keeper (hydro-5) | **arm (miso-267)** |
|---|---|---|
| C1 fuel-mix | FAIL | **FAIL** |
| C2 system volume | PASS | **PASS** |
| C3a mean LMP | FAIL | **FAIL** |
| C3b price shape | FAIL | **FAIL** |
| C3c price tail | CAVEAT (ledgered) | **CAVEAT (ledgered)** |
| C4 dispatch corr | PASS | **PASS** |
| C6 governance | PASS | **PASS** |
| C8 forced share | PASS | **PASS** |
| **full span 2020–2025** | NOT-YET · 8 / 4 / 1 / 3 | **NOT-YET · 8 / 4 / 1 / 3** |
| **train tier 2023–2025** | CALIBRATED · 8 / 7 / 1 / 0 | **CALIBRATED · 8 / 7 / 1 / 0** |
| validation 2020–2022 | NOT-YET · fails C1, C3a, C3b | **NOT-YET · fails C1, C3a, C3b** |
| D-10 free-class C1 | 39/40 all · 29/30 free | **38/40 all · 28/30 free** |

*(grade summary = scored / target / ledgered / fails)*

**Identical determinations, grade summaries and failing criteria at every grain.** The one
number that is worse is D-10: one more failing C1 cell.

## 2. Which cells moved — prediction vs outcome

| cell | keeper | predicted (PRECOMMIT §5) | **arm** |
|---|---|---|---|
| C1 2020 COAL_BIT | −10.76 FAIL | ≈ −6.8 PASS | **−6.79 PASS** |
| C1 2021 COAL_BIT | −6.66 | ≈ −3.4 | −3.40 |
| C1 2022 COAL_PRB | +7.67 | ≈ +10.1 FAIL | **+10.04 FAIL** |
| C1 2022 CC_REGULAR | −7.69 | ≈ −9.1 FAIL | **−8.99 FAIL** |
| C1 2023 CC_REGULAR | −7.40 | ≈ −7.37 | −7.32 |
| C3a 2020 | +14.7 % FAIL | ≈ +13.0 % FAIL | +12.8 % FAIL |
| C3a 2022 | −9.5 % | ≈ −10.3 % FAIL | **−10.2 % FAIL** |
| C3a 2023 / 24 / 25 | +6.9 / +0.7 / −0.8 % | ≈ +5.8 / −0.1 / −1.7 % | +4.6 / −0.2 / −1.9 % |
| C3b 2021 | 0.307 FAIL | ≈ 0.307 FAIL | 0.307 FAIL |
| C3b 2020 / 2023 | 0.182 / 0.105 | — | 0.164 / 0.089 |

Every direction came out as registered, and every magnitude is within 0.2 of the prediction
except C3a 2023, which moved further (−2.3 pp against −1.1). **The pre-registered adverse
moves happened**: 2022 now fails C1 twice and C3a once.

**Per year:**

| year | keeper | arm |
|---|---|---|
| 2020 | NOT-YET (C1, C3a) | NOT-YET (C3a) |
| 2021 | NOT-YET (C3b) | NOT-YET (C3b) |
| 2022 | CALIBRATED | **NOT-YET (C1, C3a)** |
| 2023 / 2024 | CALIBRATED | CALIBRATED |
| 2025 | CAL-W-CAVEATS | CAL-W-CAVEATS |

## 3. What the mechanism did

Arm minus keeper, from both bundles' `hourly/` sidecars (`_miso267_shard_check.py` readout):

| TWh | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | span |
|---|---:|---:|---:|---:|---:|---:|---:|
| COAL_BIT | +3.97 | +3.26 | +0.88 | +0.72 | +1.20 | +1.51 | **+11.53** |
| COAL_PRB | +1.00 | +1.56 | +2.38 | +1.73 | +1.29 | +0.77 | **+8.73** |
| CC_REGULAR | −1.57 | −1.96 | −1.40 | −0.00 | −0.29 | −0.89 | −6.12 |
| import | −0.91 | −0.72 | −0.68 | −0.73 | −0.59 | −0.40 | −4.03 |
| CT_PEAKER | −0.66 | −0.65 | −0.20 | −0.82 | −0.97 | −0.58 | −3.88 |
| ST_GAS | −0.90 | −0.58 | −0.56 | −0.51 | −0.31 | −0.12 | −2.98 |
| CC_CHP | −0.71 | −0.69 | −0.29 | −0.26 | −0.26 | −0.22 | −2.43 |
| **price, $/MWh** | −0.45 | −0.82 | −0.54 | −0.74 | −0.29 | −0.51 | |

Coal is up in every year and every gas and import class is down. Total generation is
conserved to ±0.023 TWh (2021's −0.023 is storage round-trip loss, as in miso-266). The
span totals reproduce miso-266's arm-minus-control on the miso-264 base within 0.2 TWh per
class, so `hydro_ror_split` barely interacts with this flag.

**D-2 forced shares rise** as economic CT and steam-gas energy falls:

| forced share | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | cap |
|---|---|---|---|---|---|---|---|
| CT_PEAKER | 46.0 → 49.3 % | 49.7 → 52.7 % | 46.3 → 47.3 % | 25.4 → 27.1 % | 16.1 → 17.2 % | 16.8 → 17.6 % | 15 % |
| ST_GAS | 18.3 → 20.9 % | 28.2 → **31.4 %** | 27.4 → **30.7 %** | 14.4 → 15.6 % | 14.4 → 15.1 % | 19.2 → 19.7 % | 30 % |

CT_PEAKER is over its cap in every year on both runs. ST_GAS crosses the merchant cap in
2021–22. C8 still reads PASS on both through rule 18's grounded route (D-4 window plus D-1
shape).

## 4. Why the legs can be trusted

* **Every leg is the keeper plus exactly one flag**, with the 2023–25 reserve overlay
  included. `_miso267_shard_check.py` PASSes in the shard and again in the parent; the hydro
  classifier sha is `dc2a9d4be30a0727` in every year.
* **Identical inputs.** Every leg's `resolved_inputs` equals the keeper's for that year. The
  hydro-classifier and six outage-frame captures are byte-identical by content hash.
* **Composition.** The composer checked 12 must-agree fields and one solve-surface
  fingerprint (`c3ff7c56ddbb573d`) across the six legs. `stamp_config_partition.py --check`
  re-derives an overlay identical to the keeper's.
* **Benchmark.** The span rebuild of the benchmark frames reproduced the keeper's exactly
  (`campd-d57af607eaf4`, `eia923-df0d071d1ad9`, `eia930-b0a483cf7eed`). Two registrations
  left all 44 bench parts sha256-identical.
* **Attestation.** `scripts/gen_miso267_attestation.py` carries the keeper's DOF ledger
  verbatim: 43 entries, 2 residual, 0 added. It asserts `offer_curve_by_group`
  byte-identical (the rule-1 channel is untouched), and re-measured 4 price exceptions on
  this run's own records.

## 5. What it does not fix (routed, not absorbed)

* **The C3a price body.** A flat +$6–8/MWh across RT deciles 0–7, which CALIBRATED 2023 also
  carries (PRECOMMIT §1). The arm lowers price 0.3–0.8 $/MWh by displacing gas; it does not
  touch the offset. No admissible queue lever reaches a level offset without being a fitted
  adder.
* **The 2022 gas/coal substitution.** It is the named successor object for the second
  time: giving PRB capability back lengthens a class that was already long, and gas loses
  the energy. Rule 14 says a worse cell after an accurate input is a discovered bug, not a
  reason to drop the input.
* **Other open items:**
  * 84.5 % of the availability-ceiling contradiction survives (PRECOMMIT-miso266 §3.3).
  * The coal fleet runs long in trough hours (commitment side).
  * C3b 2021 is untouched.
  * CT_PEAKER and ST_GAS forced shares are worse (§3).

## 6. Where the bytes are, and what a promotion costs

* **Committed on this lane's branch:**
  * the composite's registered file set: slim files, `hourly/` sidecars, attestation and
    diagnostics;
  * `registry/2026-09-23-miso-267-dispatched-bin.json`;
  * `runs/2026-09-23-miso-267-dispatched-bin.js`.
* **A promotion costs ZERO re-solves.** The run is registered and scored. Promoting it
  means editing the keeper shard, re-keying `calibration-complete.json`, the gate-(a) row
  and the matrix stamp, then pruning the outgoing keeper (rule 35). The year set is
  unchanged (2020–2025).
* **The per-year full bundles** (with `dispatch/<Y>_P1.parquet`) sit on the shard branches
  `claude/miso267-dbd-<Y>`. Leg SHAs are recorded in `.gitignore` as provenance. They are
  transport, cut when this lane's PR merges (rule 33 (f)), and are not needed for
  promotion.
* **Local copies of the six legs are gitignored** and kept (rule 31).
  `check_registry_payload_parity.py` reads them as RED locally, as rule 31 predicts; CI does
  not see them.
* **`audit_keepers --iso MISO` reads E13 FAIL** because a registered run is neither the
  keeper nor stamped to it. That is the expected state until the owner rules: promote, or
  prune this run.

## 7. The promotion question (rule 31) — the owner's

**Recommendation: promote, on the owner's standing standard.** The standard is *"If
structural integrity improves but gates regress that may still be a keeper"*, and the owner
already ruled "promote" on this mechanism once (RESULT-miso266 §8). That promotion was
withdrawn only because of the hydro-5 collision.

* **For.** It repairs an identity the code claims and violates (`denom == cap_LP`) with zero
  free parameters. Every determination is unchanged, the train tier stays CALIBRATED, and
  the 2020 coal miss, this lane's charter object, closes.
* **Against.**
  * 2022 goes from CALIBRATED to NOT-YET on three pre-registered cells.
  * D-10 is one cell worse.
  * The CT_PEAKER and ST_GAS forced shares rise 1–3 pp.
  * Nothing in the rubric prefers this run to the keeper.

If declined, prune `2026-09-23-miso-267-dispatched-bin` to clear E13. The keeper then keeps
the frozen 50,365.4 MW coal denominator knowingly.

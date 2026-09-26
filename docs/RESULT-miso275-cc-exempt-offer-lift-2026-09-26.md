# RESULT — miso-275: CC exempt from the ×1.10 non-steam lift. Every C1 CC_REGULAR failure clears and the train tier returns to CALIBRATED 8/7/1/0. PROMOTED 2026-09-26.

```
LANE     : miso-275 (FINDING-miso274 §6 candidate 3; owner-authorized price-tuning channel)
PREREG   : docs/PRECOMMIT-miso275-cc-exempt-offer-lift-2026-09-26.md (pin e5acf0fe)
KEEPER   : 2026-09-25-miso-273-screened-coal (miso273_span) — unchanged, see §5
RUN      : 2026-09-26-miso-275-cc-exempt (results/calibration/miso275_span, 2019-2025), registered
DELTA    : offer_curve_by_group CC_REGULAR + CC_INTERMEDIATE committed/econ_low/econ_high/peak 1.1055/1.045/1.188/2.475 -> 1.005/0.95/1.08/2.25. DOF +0
CONTROL  : keeper bundle (G-DRIFT 09b152c5..e5acf0fe all INERT, rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape; unchanged criteria set);
           train 2023-2025 NOT-YET 8/6/1/1 -> CALIBRATED 8/7/1/0 (C3c the lone ledgered caveat)
```

## 1. Legs

All seven legs passed these checks on the parent's fetched bytes:
- `_miso275_shard_check` RECIPE: the leg differs from the keeper only in `offer_curve_by_group`, which equals the declared table exactly.
- Composer `MUST_AGREE` (now including `offer_curve_by_group`).
- `stamp_config_partition --check`; the partition is byte-identical to the keeper's.

Each shard also reported vintage / inputs / classifier / log PASS. Every leg's bundle has 17 files, including
`dispatch/<Y>_P1.parquet`. All seven shards were archived after their bytes were fetched and verified.

Deltas are leg minus keeper (TWh), plus the load-weighted internal price.

| year | leg commit (provenance) | CC_REGULAR | CC_CHP | COAL_PRB | COAL_BIT | ST_GAS | CT_PEAKER | import | LW price $/MWh |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 2019 | `dc0801ff` | +6.89 | −0.78 | −2.01 | −1.25 | −0.28 | — | −1.85 | 28.351 → 27.796 |
| 2020 | `f3ca8ff1` | +5.39 | −0.75 | −1.29 | −0.41 | −0.33 | −0.12 | −1.99 | 24.903 → 24.377 |
| 2021 | `ae9c0fbc` | +6.31 | −0.98 | −1.71 | −0.92 | −0.28 | −0.27 | −1.56 | 40.179 → 38.677 |
| 2022 | `9d247994` | +6.51 | −1.21 | −0.25 | −0.23 | −0.52 | −0.39 | −3.33 | 61.152 → 58.582 |
| 2023 | `b24ea885` | +5.46 | −0.90 | −0.92 | −0.18 | −0.59 | −0.63 | −1.99 | 33.855 → 33.256 |
| 2024 | `91834390` | +4.92 | −0.86 | −0.88 | −0.19 | −0.59 | −0.59 | −1.53 | 31.013 → 30.498 |
| 2025 | `fddff1ac` | +5.06 | −1.10 | −0.95 | −0.40 | −0.27 | −0.40 | −1.63 | 42.704 → 41.792 |

Every direction matches PRECOMMIT §5: CC up, coal / ST_GAS / imports down, price down in every year.

- **S-1** (recipe) holds.
- **S-2** (single delta) holds.
- **S-3** (slack) holds: zero slack in every year except 2024, where it is identical to the keeper at 18,531.5 MWh
  (7 zone-hours vs the keeper's 8).

## 2. Gates (live scorer, same bench parts for both runs)

| criterion-year | keeper miso-273 | miso-275 |
|---|---|---|
| C1 CC_REGULAR 2019 | −0.70 PASS | +5.98 PASS |
| C1 CC_REGULAR 2020 | −6.68 PASS | −1.41 PASS |
| **C1 CC_REGULAR 2021** | −13.69 **FAIL** | **−7.46 PASS** |
| **C1 CC_REGULAR 2022** | −10.47 **FAIL** | **−4.08 PASS** |
| **C1 CC_REGULAR 2023** | −8.85 **FAIL** | **−3.47 PASS** |
| C1 CC_REGULAR 2024 | −3.68 PASS | +1.22 PASS |
| **C1 COAL_PRB 2019** | +8.02 **FAIL** | **+6.01 PASS** |
| C1 ST_GAS 2019 | −8.19 FAIL | −8.46 FAIL |
| C3a 2019 / 2020 / 2021 | +7.3 / +8.3 / −1.1 % PASS | +5.2 / +6.0 / −4.8 % PASS |
| **C3a 2022** | −11.7 % FAIL | **−15.4 % FAIL** (worse, declared in §5) |
| C3a 2023 / 2024 / 2025 | +3.1 / −4.0 / −6.1 % PASS | +1.2 / −5.6 / −8.1 % PASS |
| C3b 2021 | NRMSE 0.280 FAIL | 0.290 FAIL |
| C3b other years | PASS | PASS (2022 0.157 → 0.192) |
| C3c 2022–2025 | CAVEAT (ledgered) | CAVEAT (ledgered), identical |
| C2, C4, C6, C8 | PASS | PASS |
| **train tier 2023–2025** | **NOT-YET 8/6/1/1** | **CALIBRATED 8/7/1/0** |
| full span 2019–2025 | NOT-YET (fuelmix, price_mean, price_shape) | NOT-YET (same three criteria) |

C1 cells without a value for 2025 carry no scored record in either run (identical).

## 3. Reading

**The mechanism does what FINDING-miso274 said it would.** The shortfall was merit, not availability. Taking the
×1.10 off the CC bands brings the CC econ offer to ~×1.02 over the measured heat rate. CC gains 4.9–6.9 TWh a year,
and all three out-of-band CC years land inside the band.

**The cost is price.** CC is on the margin in most gas-set hours, so price falls $0.5–2.6/MWh.
- C3a 2022, already the low side, goes from −11.7 % to −15.4 %.
- 2025 C3a moves from −6.1 % to −8.1 %, still inside the band.
- This is the hazard PRECOMMIT §5.3 declared before any shard ran. Under rule 1 (c) it selects nothing.

**What is left open:**
1. **C3a 2022 (−15.4 %)** is a low-side price level in the Elliott year: 116 RT hours > $200 against the model's
   0 (C3c). It is not a CC-volume object.
2. **C1 ST_GAS 2019 (−8.46)** is steam gas under-run in the oldest year. It was held out of the lift by the
   2026-09-05 ruling, and this arm leaves it untouched.
3. **C3b 2021 (0.290)** is the storm-month gas array. The owner ruled D1 = daily delivered price (PRECOMMIT §7.1).
   That is a successor lane, and it needs a daily regional gas hub intake for the MidCon / South zones.

**Correction to the PRECOMMIT, stated.** PRECOMMIT §1 / §0 originally said the lift's class scope narrows "from 11 to
9". The keeper table carries no bare `COAL` row: COAL-SUB already folded it into the four subclasses. So the lifted set
after this arm is **8** classes. The text was corrected in place after the pin. The arm table, the only thing the
shards read, is unchanged.

## 4. Where the bytes are

The composite `miso275_span` lands on `main` with this lane's PR. It holds:
- the slim bundle;
- the `hourly/` sidecars;
- the attestation, with `authorized_price_tuning` narrowed to this ruling and a new `miso275` block;
- the diagnostics;
- the registry sidecar and the run payload.

Promoting from there costs **zero re-solves**.

The per-year legs, including their `dispatch/`, are on this session's local disk only, gitignored. The leg SHAs above
are provenance, not storage (rule 33(d)). All 7 shards are archived.

## 5. Promotion

**Recommended.** The change is the owner's authorized channel, used under every carve-out condition:
- one table for all seven years;
- set ex ante from the pre-lift values;
- not swept;
- declared in the attestation, with DOF +0.

It restores MISO's CALIBRATED train-tier headline and clears four C1 failures. The cost is one existing C3a failure
getting worse (2022), stated at full magnitude.

Year set (rule 35(b)): outgoing {2019–2025}, incoming {2019–2025}, covered.

Not done pending the owner's ruling (rule 31):
- the keeper re-key in `keepers/MISO.json`;
- `build_status --iso MISO`;
- the attestation promotion stamp;
- `calibration-complete.json`;
- the rule-35 prune of `2026-09-25-miso-273-screened-coal`.

The matrix cell `offer_curve_by_group` stays **K**, with this evidence prepended.

## 6. Promotion executed (rule 35) — 2026-09-26

The owner ruled, verbatim: *"If it's an improvement structural or calibration then promote yes."* It is a calibration
improvement: the train tier goes from NOT-YET 8/6/1/1 to CALIBRATED 8/7/1/0.

1. **Year set checked before any deletion.** Outgoing {2019–2025}, incoming {2019–2025}: covered (rule 35(c)).
2. **Promoted.** `keepers/MISO.json` now names `2026-09-26-miso-275-cc-exempt`.
   - Both `config_partition` tiers were re-keyed to `miso275_span`; the partition is byte-identical.
   - `iso_determination` → **CALIBRATED**, and `status/MISO.js` rebuilt reads MISO: CALIBRATED.
   - The attestation carries a `miso275.promotion` stamp.
   - Matrix: keeper and gates stamps updated, the §5.4 header re-stamped, and `check_mechanism_matrix` is clean.
3. **Verified.** `audit_keepers --iso MISO` E1 resolves the incoming keeper.
4. **Pruned.** `prune_iso_runs.py --iso MISO --force-uncite` removed `2026-09-25-miso-273-screened-coal`: its sidecar,
   its payload and `results/calibration/miso273_span`. Governance citations are retained as history.
   `audit_keepers --iso MISO` now reads **PASS 0/0**.

`calibration-complete.json` carries no MISO entry, so it had nothing to re-key.

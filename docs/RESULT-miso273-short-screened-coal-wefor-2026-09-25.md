# RESULT — miso-273: the coal statistical-WEFOR stack is relieved. C3a 2019/2020 now PASS, and the relief exposes a larger CC_REGULAR shortfall. RECOMMENDED for promotion; the promotion edit was refused by the session permission policy.

```
LANE     : miso-273 (charter candidate 1)
PREREG   : docs/PRECOMMIT-miso273-short-screened-coal-wefor-2026-09-25.md (pin 09b152c5)
KEEPER   : 2026-09-25-miso-272-edwardsport-block (miso272b_span) — unchanged, see §5
RUN      : 2026-09-25-miso-273-screened-coal (results/calibration/miso273_span, 2019-2025), registered
DELTA    : wefor_residual_short_screened_coal=true + its input pair (screened set; short-coal +30 rows 2019-22). DOF +0
CONTROL  : keeper bundle (G-DRIFT all INERT, rule 29(b) form 4)
VERDICT  : full span NOT-YET (fuelmix, price_mean, price_shape); train 2023-2025 CALIBRATED 8/7/1/0 -> NOT-YET 8/6/1/1
```

## 1. Legs

All seven legs passed the shard check on the parent's fetched bytes:
- **recipe:** the keeper plus exactly the one field;
- **inputs:** every pin re-verified, including the new short-coal and screened-set shas;
- **hydro classifier** and **log markers**, including the relief's own line;
- **bundle:** 18 files per leg, each including `dispatch/<Y>_P1.parquet`.

Every leg was fetched and its bundle checked out before its shard was archived.

| year | leg commit | CC_REGULAR | COAL_BIT | COAL_PRB | CT_PEAKER | ST_GAS | import | LW price $/MWh |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 2019 | `44a543d8` | −4.18 | +1.50 | +6.31 | −0.25 | −1.42 | −1.02 | 29.319 → 28.351 (−0.97) |
| 2020 | `cee0ba72` | −2.88 | +1.89 | +5.31 | −0.88 | −1.25 | −1.21 | 25.594 → 24.903 (−0.69) |
| 2021 | `985328c2` | −5.92 | +2.42 | +8.24 | −1.27 | −0.81 | −1.62 | 42.475 → 40.179 (−2.30) |
| 2022 | `d836e700` | −3.42 | +1.90 | +5.01 | −0.63 | −0.75 | −1.82 | 62.667 → 61.152 (−1.52) |
| 2023 | `74a64567` | −3.14 | +3.62 | +5.76 | −2.28 | −1.39 | −2.04 | 34.750 → 33.855 (−0.90) |
| 2024 | `3b4ee44c` | −3.31 | +3.15 | +7.36 | −3.04 | −1.55 | −2.00 | 31.974 → 31.013 (−0.96) |
| 2025 | `ccad35dd` | −3.77 | +3.44 | +5.72 | −2.18 | −1.04 | −1.43 | 44.002 → 42.704 (−1.30) |

Every direction matches PRECOMMIT §5: coal up (mostly COAL_PRB), gas and imports down, price down in every year.

The composite `stamp_config_partition --check` passes, and the partition is byte-identical to the keeper's.

## 2. Gates (live scorer, same bench parts for both runs)

| criterion-year | keeper miso-272 | miso-273 |
|---|---|---|
| C3a 2019 | +11.0 % FAIL | **+7.3 % PASS** |
| C3a 2020 | +11.3 % FAIL | **+8.3 % PASS** |
| C3a 2022 | −9.8 % PASS | −11.7 % **FAIL** |
| C3b 2021 | NRMSE 0.305 FAIL | 0.280 FAIL |
| C1 CC_REGULAR 2021 / 2022 / 2023 | −7.91 / −7.09 / −5.76 TWh PASS | −13.69 / −10.47 / **−8.85** TWh **FAIL** (band ±8.00) |
| C1 ST_GAS 2019 | −6.82 PASS | −8.19 FAIL |
| C1 COAL_PRB 2019 | +1.71 PASS | +8.02 FAIL |
| C2, C4, C6, C8 | PASS | PASS |
| **train tier 2023–2025** | **CALIBRATED 8/7/1/0** | **NOT-YET 8/6/1/1** (only C1 CC_REGULAR 2023, 0.85 TWh outside the band) |

## 3. Reading

**The mechanism does what its identification says.** It removes 19–25 TWh/yr of double-counted coal unavailability, and the two C3a held-out failures it was aimed at now pass.

**The cost is on gas volume.** Coal now displaces CC_REGULAR that was already short:
- The keeper was already −5.8 to −7.9 TWh on CC_REGULAR in 2021–2023.
- Before this lane, the over-derated coal fleet had been propping CC volume up.
- This is rule 14's pattern: an accurate input makes the fit worse, which points at the thing it was compensating.

**The remaining objects are therefore the ones this arm uncovers:**
1. **The CC_REGULAR shortfall** (rule 14 root cause). Candidates:
   - the coal econ offer level against CC merit, which is the owner's rule-1 band-multiplier channel (charter candidate 3);
   - the CC outage numerator basis at block plants (charter candidate 2).
2. **C3a 2022 at −11.7 %** is now the low side. Price fell everywhere, so the overnight body and the coal offer level are the same question as item 1.
3. **C3b 2021** is still a gas-array object: owner decision D1 (charter candidate 4).

## 4. Where the bytes are

The composite `miso273_span` holds the slim bundle, the `hourly/` sidecars, the attestation (DOF entry and `miso273` block added), the diagnostics, the sidecar and the payload. It lands on `main` with this lane's PR, so promoting from there costs **zero re-solves**.

The per-year legs, with their `dispatch/`, are on this session's local disk only (gitignored). The leg SHAs above are provenance, not storage (rule 33(d)). All 7 shards are archived.

## 5. Promotion

**Recommended**, on rule 19 and rule 1: a measured double count is removed with zero free parameters. It meets the owner's standing ruling: *"If structural integrity improves but gates regress that may still be a keeper."*

It also costs MISO's CALIBRATED headline, which falls to NOT-YET on one C1 record 0.85 TWh outside its band. That trade is stated here, not hidden.

The first promotion step, editing `frontend/data/backcast/keepers/MISO.json`, **was refused by the session permission policy** ("Modify Shared Resources"). This is the same refusal miso-271 hit, which went through when the owner repeated the ruling. So none of the following has been done:
- the keeper re-key;
- `build_status --iso MISO`;
- the attestation promotion stamp;
- the rule-35 prune of `miso272b_span`.

The matrix cell stays **O** (tested, recommended, promotion pending).

Year set (rule 35(b)): outgoing {2019–2025}, incoming {2019–2025}, covered.

## 6. Promotion executed (rule 35) — 2026-09-26

The owner repeated the ruling, verbatim: *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper.."* On that instruction the keeper-shard edit was
retried and went through.

1. **Year set checked before any deletion.** Outgoing {2019–2025}, incoming {2019–2025}: covered (rule 35(c)).
2. **Promoted.** `keepers/MISO.json` now names `2026-09-25-miso-273-screened-coal`.
   - Both `config_partition` tiers were re-keyed to `miso273_span`; the partition is byte-identical.
   - The ISO headline was re-verified on the live scorer: **NOT-YET** (train tier 8/6/1/1).
   - `status/MISO.js` was rebuilt and reads MISO: NOT-YET.
   - The attestation was stamped with the ruling.
   - Matrix: keeper and gates stamps updated, `wefor_residual_short_screened_coal` O → **K**, and the §5.4 header updated.
3. **Verified.** `audit_keepers --iso MISO` resolves the incoming keeper. Its only failure is E13 for the outgoing
   `2026-09-25-miso-272-edwardsport-block`.
4. **NOT done — refused by the session permission policy.** The prune, `prune_iso_runs.py --iso MISO --force-uncite`,
   which would remove `2026-09-25-miso-272-edwardsport-block` (`miso272b_span`) and its sidecar and payload. The
   outgoing keeper therefore stays registered, and `audit_keepers` E13 stays red until the owner or a later session
   runs that one command.

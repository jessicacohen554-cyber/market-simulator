# RESULT — miso-268: the coal budget per coal yard. C1 passes in every year; PROMOTED.

```
RUN     : 2026-09-24-miso-268-coal-yard  (results/calibration/miso268_yard_span, 2020-2025)
RECIPE  : keeper 2026-09-23-miso-267-dispatched-bin + coal_fuel_inventory_plant_grain=true. ONE flag.
PREREG  : docs/PRECOMMIT-miso268-coal-yard-grain-2026-09-24.md (pinned 49c898c7; relaunched at bb31b95c, check-only fix)
BENCH   : committed parts; registering this run moved NONE of the 44 (sha256)
VERDICT : full span NOT-YET 8/5/1/2 (was 8/4/1/3); train 2023-2025 CALIBRATED 8/7/1/0 (unchanged). PROMOTED.
```

## 1. Gate table

| criterion | keeper (miso-267) | **arm (miso-268)** |
|---|---|---|
| C1 fuel mix | FAIL | **PASS** |
| C2 system volume | PASS | PASS |
| C3a mean LMP | FAIL | FAIL |
| C3b price shape | FAIL | FAIL |
| C3c price tail | CAVEAT (ledgered) | CAVEAT (ledgered) |
| C4 dispatch corr | PASS | PASS |
| C6 governance | PASS | PASS |
| C8 forced share | PASS | PASS |
| **full span** | NOT-YET 8/4/1/3 | **NOT-YET 8/5/1/2** |
| **train 2023–2025** | CALIBRATED 8/7/1/0 | **CALIBRATED 8/7/1/0** |

*(scored / target / ledgered / fails)*

## 2. Cells vs prediction (PRECOMMIT §4.1)

| cell | keeper | predicted | **arm** |
|---|---:|---|---:|
| C1 2022 COAL_PRB | +10.04 FAIL | +0.9 (−5.3 to +3.9) PASS | **−0.24 PASS** |
| C1 2022 CC_REGULAR | −8.99 FAIL | ≈ −3 (−7 to +2) PASS | **−3.66 PASS** |
| C1 2021 COAL_PRB | −0.10 | ≈ −5.3; FAIL possible | −4.86 PASS |
| C1 2020 COAL_BIT | −6.79 | ≈ −7.5; FAIL possible | −7.71 PASS |
| C1 2021 CC_REGULAR | −6.50 | — | −3.68 |
| C1 2023 CC_REGULAR | −7.32 | — | −6.64 |
| C3a 2022 | −10.2 % FAIL | toward zero; PASS likely | **−8.4 % PASS** |
| C3a 2020 | +12.8 % FAIL | +12.8 to +13.5 %, FAIL | +13.4 % FAIL |
| C3b 2021 | 0.307 FAIL | ≈ 0.30, FAIL | 0.309 FAIL |

Every direction and every band outcome came out as registered.

**Coal removed vs the static bound (TWh):**

| year | PRB | BIT | lignite | CC_REGULAR | price Δ $/MWh |
|---|---:|---:|---:|---:|---:|
| 2020 | −0.94 | −0.92 | +0.02 | +0.86 | +0.14 |
| 2021 | −4.76 | +0.26 | −0.97 | +2.95 | +0.65 |
| 2022 | **−10.29** | +0.28 | +0.47 | **+5.44** | **+1.48** |
| 2023 | −0.88 | −0.43 | −0.15 | +0.71 | +0.10 |
| 2024 | −0.03 | −0.43 | 0 | +0.28 | +0.03 |
| 2025 | −3.02 | −2.10 | +0.11 | +2.14 | +0.56 |

## 3. Structural gates (PRECOMMIT §5)

* **S-1 single delta:** PASS in every leg (shard check, per-year overlay included).
* **S-2 rows built and honoured:** PASS. No yard exceeds its budget in any year (max over-run
  ≤ 1.9 MMBtu, solver tolerance). Yards binding: 13 / 23 / 44 / 11 / 5 / 20 of 78 / 77 / 71 /
  66 / 63 / 57.
* **S-3 slack = dump = 0:** dump 0 everywhere. **2024 carries 26.9 GWh of slack (6 hours,
  hours 5700–5706), identical to the keeper's own.** Inherited, not introduced by this arm.
* **S-4 G-DRIFT:** all INERT (PRECOMMIT §3; re-checked at relaunch).

## 4. Still open (routed, not absorbed)

* **C3a 2020 +13.4 %** — the overnight price body (FINDING-miso268 §2). The arm moves it
  slightly away, as predicted.
* **C3b 2021 0.309** — February 2021 priced high on every day, not just during Uri (FINDING §1).
* D-2 CT_PEAKER forced share over its cap in every year; C8 via rule 18's grounded route
  (inherited).

## 5. Promotion (rule 31 trigger (i), rule 35)

Owner ruling 2026-09-24, verbatim: *"Is this a recommended keeper candidate? If so plz promote.
If structural integrity improves but gates regress that may still be a keeper.."* The session
recommended promotion. Executed in the order rule 35 fixes:

1. **Year set:** outgoing and incoming keepers both cover {2020–2025}; nothing is stamped to the
   outgoing keeper.
2. **Promote:** `keepers/MISO.json` (both partition tiers re-keyed), forecast gate-(a) row
   (`program-status.json`), matrix keeper/gates stamps, cell `O → K`, §5.4 header,
   `status/MISO.js` rebuilt (**MISO CALIBRATED**), attestation re-stamped with the ruling.
3. **Verify:** `audit_keepers --iso MISO` E1 resolved the incoming keeper before deletion.
4. **Delete:** `prune_iso_runs.py --iso MISO --force-uncite` removed the outgoing keeper's sidecar,
   payload and bundle; git history holds them.
5. **After:** `audit_keepers` 0/0; matrix, gate-(a) provenance, bench freshness (0 stale) green;
   44 bench parts unchanged; `stamp_config_partition --check` clean.

## 6. Where the bytes are

* **On this lane's branch → `main` at merge:** the composite's registered file set (slim files,
  `hourly/` sidecars, attestation, diagnostics), `registry/2026-09-24-miso-268-coal-yard.json`,
  `runs/2026-09-24-miso-268-coal-yard.js`. A promotion from this state costs zero re-solves.
* **Per-year full legs** (with `dispatch/<Y>_P1.parquet`): gitignored on local disk (rule 31) and
  on shard branches `claude/miso268-yard2-<Y>`. Leg SHAs are in `.gitignore` and the attestation as
  provenance only (rule 33(d)).
* **Shards:** first wave (6) archived after the check defect; second wave archived after their
  bytes were verified here.

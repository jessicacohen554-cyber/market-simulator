# RESULT — NYISO-NEXT-23: Transco Z6 NY daily gas on its flow day — 2026-10-01

```
PRECOMMIT : docs/records/nyiso/PRECOMMIT-nyiso-next23-z6-flow-date-2026-10-01.md (merged in #6980 before any shard)
PHASE 0   : docs/records/nyiso/FINDING-nyiso-next23-c3a-2025-phase0-2026-10-01.md
PIN       : f2b83ef24bec09672f3458bc946b811adab4aca4 (main)
ARM       : keeper recipe + nyiso_gas_flow_date=true (one delta, zero DOF)
RUNS      : 2026-10-01-nyisonext23-flowdate-span (2022-2025), 2026-10-01-nyisonext23-flowdate-2021 — REGISTERED, NOT PROMOTED
KEEPER    : 2026-10-01-nyisonext21-astoria-hr-span (+ -2021), unchanged
```

## 1. Gates (pre-registered)

| gate | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| G-1 leg acceptance (pin, one delta, inputs + offers identical) | PASS | PASS | PASS | PASS | PASS |
| G-2 NYC 2025-01-17 price falls | — | — | — | — | **PASS** ($187.43 → $70.13) |
| G-3 demand Δ ≤ 0.1 GWh, slack Δ ≤ 1 GWh | PASS (0 / 0) | PASS | PASS | PASS | PASS |
| G-4 C6 / C8 | PASS | PASS | PASS | PASS | PASS |
| G-5 no new D-4 FAIL row | **FAIL** | **FAIL** | **FAIL** | **FAIL** | PASS |

The G-5 rows are all `unit-conduct` rows on the NYISO gas commitment bridge. Each is a few hours on a
unit CAMPD shows offline that day (measured median 0 MW):

| year | plant | class | floored TWh | binding h | keeper row |
|---|---|---|---:|---:|---|
| 2021 | 57185 | CC_REGULAR | 0.0007 | 5 | pass (0.0047 TWh, 16 h) |
| 2022 | 2490 | ST_GAS | 0.0002 | 6 | pass (0.0003 TWh, 5 h) |
| 2023 | 8906 (Astoria) | ST_GAS | 0.0029 | 38 | pass (0.0002 TWh, 3 h) |
| 2024 | 55405 | CC_REGULAR | 0.0024 | 14 | pass (0.0027 TWh, 16 h) |

**Promotion rule (§5): G-5 fails, so the run is registered, not promoted, and the owner is asked.**
Probe: `scripts/probes/nyisonext23_gates.py`.

## 2. Criteria, keeper → arm (reported, not gating)

| | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|
| C3a | +2.9 → +3.5 % | −2.4 → **−1.7** | +1.2 → +1.7 | −4.0 → **−3.1** | −11.6 → −12.7 (FAIL) |
| C3b NRMSE | 0.108 → 0.116 | 0.155 → **0.150** | 0.122 → **0.119** | 0.113 → 0.117 | 0.181 → 0.195 |
| C3c >$300 h | 0 / 3 | 1 / 101 | 0 / 10 | 0 / 13 | 8 / 42 (all unchanged) |
| C1 / C2 / C6 / C8 | no status change in any year | | | | |

**Determinations unchanged:** span NOT-YET (C3a 2025; C3c 2022–2025 not lone), 2021 CALIBRATED, ISO
NOT-YET.

Load-weighted |error| against the zone-resolved RT improves in both years checked: 2025 −$0.24/MWh,
2022 −$0.82/MWh. C3a 2025 still worsens, because January's mean price falls $0.69. The oil cap clips
the re-dated spike days (the MLK package now sits on Sat–Tue at the cap), and the trade-day spikes
that had lifted weekday prices are gone.

## 3. Prediction check (PRECOMMIT §6)

- *C3b improves most in winter-heavy years (2022 first)*: **partly right.** 2022 and 2023 improve.
  2021, 2024 and 2025 get worse.
- *C3a 2025 moves < 1 pt and stays FAIL*: **missed.** It moved −1.1 pt, in the wrong direction, and
  stays FAIL.
- *No change to summer / RT spikes / C3c*: **right.**

## 4. Reading

The arm corrects the calendar semantics of a measured input. Each EIA print now sits on the day its gas
flows; G-2 confirms the 1/17 mis-dating is gone. It does not reach the 2025 level. That miss is the
dual-fuel parity cap (FINDING §2b), which now pins the correctly-dated cold days at about
$19.9/MMBtu × HR. Measured CAMPD shows 73–80 % of the capped NYC and Capital_Hudson MW burning < 1 %
oil on those days. **That cap is the next lever, and it is an owner decision card**, not a session call.

## 5. Retrievability

- `results/calibration/nyisonext23_span` and `results/calibration/nyisonext23_2021` (slim set,
  9.6 MB) are committed with their registrations.
- The full bundles, with `dispatch/<y>_P1.parquet`, are on local disk in this container and **will
  not survive it**. Per-year legs `nyisonext23_202[2-5]` are gitignored (rule 32 (d)).
- Leg provenance SHAs (rule 33 (d), not a recovery route): 2021 `9e41c83e`, 2022 `754298f3`,
  2023 `24012264`, 2024 `55b3c144`, 2025 `c03b1a60`.
- A promotion from this state needs **no re-solve**: `promote_keeper.py` reads the registered span and
  2021 bundles.
- Shards archived (all five).

## 6. Owner decision card

**Promote `2026-10-01-nyisonext23-flowdate-span` (+ -2021) despite G-5?**
- **Promote (override).** Rule 14: the convention is right, zero DOF. The four G-5 rows are
  0.2–2.9 GWh of bridge conduct, the queue's known object. C3a 2025 worsens 1.1 pt; no determination
  changes.
- **Keep keeper.** The run stays registered for the record and the matrix cell reads `O`.

Recommendation: **promote (override)**. The basis is structural, the precedent is NEXT-16, NEXT-18 and
NEXT-21, and every determination is unchanged.

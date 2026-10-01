# RESULT — R-CAISO-13 (2026-09-28): the battery "1 h late" is an EIA-930 clock defect; the arm is built, not yet solved

**Keeper unchanged:** `2026-09-28-caiso-r11-tacpst` (CALIBRATED, single ledgered C3c 2024). Fold
`2026-09-28-caiso-r11-tacpst-touchpoints` stays NOT-YET, reported only (rule 30(c)).

**Nothing solved.** This session sits at lineage depth 8, the nesting limit, so it cannot launch shards, and
rule 32(a) forbids the parent from solving. The arm `caiso_eia930_clock_repair` is merged (default off,
byte-identical). The 7-year solve is handed to R-CAISO-14 (`HANDOFF-r-caiso-14.md`).

**Owner card (2026-09-28):** clock fix → "Build + solve now".

**Probe:** `scripts/probes/_rcaiso13_storage_timing.py` → `results/calibration/_rcaiso13/storage_timing.json`.

## 1. The measured battery series is on the model clock; the model is not

- **The measured series is on the model clock.** CAISO Outlook "Total batteries" is stamped in prevailing Pacific time. The builder converts prevailing → UTC → fixed PST, hour-beginning.
- **The model is 1 h late in 2024–25.** Its battery net profile vs Outlook (Jun–Sep, correlation of the hour-of-day profiles):

| | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| r at lag 0 | 0.933 | 0.955 | 0.921 | 0.909 |
| r with model shifted +1 h | 0.963 | 0.945 | **0.993** | **0.996** |
| Model solar centroid (h PST, Jun–Sep) | 11.8 | 11.9 | **12.9** | **12.9** |

Solar noon at the fleet's longitude is about 12.0 h PST, so a 12.9 h solar centroid is physically impossible.

## 2. Root cause: EIA-930 CISO is published one hour late

Two clocks independent of EIA-930 agree:
- the OASIS SLD TAC actual load, which carries GMT stamps;
- solar geometry.

| Column family | Stamped 1 h late (hour-ending UTC) | Test |
|---|---|---|
| Generation, `NG:*`, interchange | 2023-11-01 08:00 → 2025-12-02 22:00 | d(NetGen−TI) vs d(TAC): best lag +1 in every month of the window, 0 outside. `NG: SUN` centroid 12.5–13.0 h inside vs 11.6–11.9 outside |
| Demand | 2022-06-16 08:00 → 2025-12-02 22:00 | d(Demand) vs d(TAC): best lag +1, r 0.96–0.999, every month. Hour-level scan pins the end. 06-14/15 are mixed and not asserted |

- The EIA API long series is byte-identical to the extract, so the error is EIA's.
- **caiso-75 read this backwards.** It used the generation frame as its reference clock, so it saw Demand late in Jan–Oct 2023 and "aligned" afterwards. In fact both were late after 2023-11. Its `caiso_demand_clock_realign` is superseded by the new arm (rule 19).

**What the keeper rides.** In Nov 2023–Nov 2025 the following are 1 h late:
- solar and wind CF;
- the WAT hydro envelope;
- interchange;
- the EIA-930 term of the caiso-80 supply-consistent demand.

The CEMS gas term is on its own, correct clock. That mismatch is itself a within-hour inconsistency in the demand series.

## 3. The arm (merged, default off)

`caiso_eia930_clock_repair` — gated, CAISO-only, zero parameters (rule 14):
- **Frame seam:** `frames._repair_clock_late_windows` runs inside `_repair_published_extract`, so every CISO reader sees the true hour. The window's last hour takes its two neighbours' mean.
- **Demand artifact:** `demand._repair_supply_consistent_clock` moves the caiso-80 artifact's EIA-930 term the same way; the CEMS and flat terms are untouched.
- **Supersession:** `caiso_demand_clock_realign` is superseded.
- **Where it is armed:** per solve, at both calibration seams.

**Verified at zero LP.** The repaired solar centroid is 11.5–12.0 h PST in every month of 2023–25. The off path is byte-identical. Rows changed, per year (Demand / NG: SUN / SC demand):

| Year | Rows changed |
|---|---|
| 2019–21 | 0 / 0 / 0 |
| 2022 | 4776 / 0 / 0 |
| 2023 | 8752 / 1140 / 1465 |
| 2024 | 8758 / 7666 / 8755 |
| 2025 | 8049 / 6943 / 8051 |

**Also in the merge:**
- 7 unit tests;
- the matrix row plus a cell in every ISO shard (CAISO `U`, solve pending);
- the cache key registered;
- solve-surface pins advanced (+1 declared row, no value moved).

## 4. What the clock does NOT explain: the evening ramp-peak gap

- **2023 has the biggest evening gap and no generation-frame defect.** So the clock is not the evening object.
- **Storage makes the plateau.** In an LP, a battery discharging strictly inside its bounds prices every such hour at one SOC dual. Measured:
  - price spread across interior-discharge hours: median $1.8–11.4/MWh;
  - interior-discharge hours: a median of 6–9 per day;
  - no SOC or power bound binds (R-CAISO-11).
- **Daily h18–22 price CV:** model 0.006–0.057 vs DAM 0.034–0.134.
- **Every remaining storage lever is on the do-not-redo list:** `storage_daily_cycling` G, the adaptive expectation I, the reserve co-opt inert, `battery_dispatch_adder` K at 0. **No admissible lever this session.**

## 5. Side observation (reported, not a lever)

The keeper's owner-signed caiso-80 supply-consistent demand sits **5–8 GW below** CAISO's metered TAC load at h6–12 in Jul–Aug 2024–25 (−1 to −2 GW in 2022).
- The clock repair closes only the h6–7 morning step.
- The midday level gap is the caiso-80 basis, which the owner signed. It is not re-opened here.

## Retrievability (rule 34(e))

- Nothing was solved.
- The probe, its JSON, the arm, the PRECOMMIT and the shard prompt are all on `main`.
- Next-link cost: 7 shards × ~25 min, in parallel.

# FFR-2B — Retirement-rule + entry-damper evidence (the owner's D-1/D-2 case)

**Charter.** FFR-2B of `docs/forecast-readiness-prompt-pack-2026-07.md` §Wave 2:
re-probe `retirement_rule="pipeline"` (audit **FR-4**) and the FF-2A entry
dampers (audit **FR-5**) at post-Wave-1 HEAD, and deliver the measured
before/after the owner sitting needs for decisions **D-1** and **D-2**. Amended
priority per pack §0d (2026-08-02): FH-1's §3.3 harness-defect gate FAILED — the
I6 over-retirement reproduces at the T1-FF posture — and the defect lives in the
retirement layer this session measures, so §4 adds an explicit **FH-4
cross-read**.

**This session changes no `ScenarioConfig` default and flips nothing.** The
flips are the owner's, executed at FFR-3A step 0. Rules 1, 5, 11, 12, 14, 15,
22, 24, 27, 28 govern.

---

## 0. Pre-registration (written and committed BEFORE any leg was solved)

Registered here so the §3 grading protocol of
`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` is honoured:
expectations first, measurement second. **Bands are imported by reference and
never restated looser.**

### 0.1 The arms

Six legs, all solved **COLD**. The 2026-08-02 cache epoch
(`src/market_sim/results/cache.py` ledger; pack §0c-3) invalidates every
forecast-mode bundle produced before the Wave-1 merges **at any solve year** —
FR-1/FR-2 change fleet MW from a confirmed exit's year+1 onward and FR-7 re-keys
the age-based availability escalation onto the solve year. Every leg below is a
forecast-mode leg with capacity evolution and aging-sensitive availability, so
**no committed BEFORE leg qualifies for reuse** under the pack §0c-9 duty — the
BEFORE arms are re-solved at HEAD too, which is also the only way the
before/after is measured on one tree.

| # | Leg | Instrument | Arms |
|---|---|---|---|
| 1 | `miso-2026-2030-t1f-base-ffr2b` | T1-F (2026–2030) | shipped defaults |
| 2 | `miso-2026-2030-t1f-dampers-ffr2b` | T1-F (2026–2030) | `pipeline` + `entry_rate_limits` + `entry_commissioning_lag` |
| 3 | `miso-2021-2025-cmc-legacy-ffr2b` | T1-H (2021–2025, 2022 bridged) | curve-ON, `legacy` |
| 4 | `miso-2021-2025-cmc-pipeline-ffr2b` | T1-H | curve-ON, `pipeline` |
| 5 | `pjm-2021-2025-cmc-legacy-ffr2b` | T1-H | curve-ON, `legacy` |
| 6 | `pjm-2021-2025-cmc-pipeline-ffr2b` | T1-H | curve-ON, `pipeline` |

Rule 12: strictly sequential — one invocation at a time (FFR-2C holds the
program's other concurrency slot), years sequential within each invocation,
≤5 solve-years per invocation. Rule 22: every leg is inside the training window
plus the enumerated `{2021}` hindcast seed; 2022 is bridged, never solved; the
T1-F legs are forecast-mode 2026+ and read no measured actuals. The holdout
freeze is not implicated and no marker is spent.

### 0.2 Pre-registered expectations

**D-1 (`retirement_rule`), per FF-1A's committed measurement
(`ff-retirement-rule-implementation-2026-07.md` §4–§7).** The redesign fixes
decision ORDER and COMPOSITION, not signal LEVEL — so:

- **E1.** MISO's gas_st false-retire collapses toward 0 under `pipeline`
  (FF-1A measured 8.643 → 0.0 GW); T-R10a/b PASS on the economic channel.
- **E2.** PJM's coal wave is recovered under `pipeline` (recall 0 % → ~76 %).
- **E3.** The LEVEL residuals persist and are NOT expected to close: MISO
  under-retires thermal, PJM over-retires coal depth. Both route to the revenue
  lane (BLK-6/BLK-9, RD-4) — never a fuel patch (rule 1).
- **E4.** If Wave 1 moved these numbers materially versus FF-1A's committed
  values, the movement is FR-1/FR-2/FR-7's, and is reported as such rather than
  re-attributed to the rule.

**D-2 (entry dampers), per FF-2A + audit FR-5/FR-13.**

- **E5 (the latent-defect test).** FR-13 said arming `entry_commissioning_lag`
  would make **I4 fail by the commissioned MW in every COD year**, because
  step-4.5 commissioned units entered the fleet before the additions baseline
  snapshot. FFR-1A is recorded as having fixed the accounting. Expectation:
  **I4 stays PASS with the lag armed.** An I4 failure here is a live FR-13
  regression and is reported as a blocker, not tuned around.
- **E6.** I13 (cobweb) is expected to improve or hold — the COD lag is the
  structural anti-cobweb.
- **E7.** BLK-10 backstop fired MW falls under `entry_rate_limits` (the ladder
  caps the one-pass full-deficit rebuild).

**FH-4 cross-read (§4).** I6 is `econ_mw / prior_thermal` per solve year against
a 20 % cap. Measured on both arms of legs 3–6. No claim about FH-1's own gate
probe is made from these legs, and the block is not declared lifted — that needs
a retirement-lane fix plus FH-1's own re-probe.

### 0.3 Harness work this session required

Both probe runners needed the arms exposed before anything could be measured;
neither change moves a default (`ScenarioConfig().cache_key()` verified
unchanged at `603c2498bf71d21d`).

1. **`scripts/run_capacity_hindcast.py`** — FFR-1D deleted the three FF-2A
   `--entry-*` flags on 2026-07-31 (rule 26, audit FR-15) because they wrote
   their state into a bundle's meta while arming nothing, and left the successor
   an explicit instruction: *"a session that needs them wires the passthrough for
   real, one line each; it does not resurrect a flag that lies."* This session
   is that successor. The meta entries are now read from the **solved config**,
   never from `args`, so the record cannot diverge from what was armed.
2. **`scripts/run_full_horizon.py`** — had no `--retirement-rule` and no entry
   arms at all, so the D-2 question could not be asked on a forecast-mode
   window. `reference_config()` now forwards all four; passing none of them is
   byte-identical to the pre-change reference forecast.

---

## 1. Measured results

_(populated after the legs land)_

## 2. D-1 decision box

_(populated after the legs land)_

## 3. D-2 decision box

_(populated after the legs land)_

## 4. FH-4 cross-read

_(populated after the legs land)_

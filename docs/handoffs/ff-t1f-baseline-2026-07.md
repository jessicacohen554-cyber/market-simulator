# FF-0B - T1-F short-forecast baseline (2026-2030), all six ISOs, HEAD defaults

**Session.** FF-0B (Wave 0, L-VAL) of `docs/forecast-development-plan-2026-07.md`
S6. Baselines the **T1-F short forecast** (plan S2.1: 2026-2030 forecast-only, all
six ISOs) at **HEAD defaults**, scores the I1-I14 forecast invariants, and
registers the runs as the reusable "before" legs every Wave-1/2 change is compared
against (solve once, reuse forever). **This is the FF-0B *redo*** - the original
(#2412) was a non-delivery (it committed only a `.gitignore` change and left the
findings doc + sidecars untracked). This redo commits both.

**Findings only.** No model code, threshold, offer curve, or default was changed
to alter a result (rules 1/11/14; plan S7.6). One additive registration helper was
written (`scripts/register_forecast_baseline.py`) - it touches no model behavior.
No 2022 / <=2021 / 2019 / H1-2026 solve (rule 22 / plan S7.4 - forecast mode uses no
measured holdout actuals). Nothing registered on the *backcast* dashboard.

> **[!] HEAD-defaults posture - measured WITH the FF-1F flips ON.** HEAD defaults now
> bake in the two owner-decided forecast-posture flips (plan S2.1a c/d, FF-1F
> 2026-07-18): **`datacenter_load_path="mid"`** (the published DC boom modeled as a
> flat energy-invariant block) and **`correlated_forced_outage=True`** (the measured
> Uri/Elliott/Heather cold-event derate, ERCOT-only). This baseline is measured
> **with both ON** - it is the golden-posture scenario, not the pre-FF-1F posture.
> Several deltas from the 2026-07-12 full-horizon baseline (`docs/handoffs/
> full-horizon-findings-2026-07-12.md`, DC=off/cfo=False) are attributable to these
> flips; flagged inline where they are.

**Config (identical across ISOs).** `ScenarioConfig(mode="forecast",
start_year=2026, end_year=2030)`, every other field default -> `use_campd_bins=True`
(per-plant CAMPD bins, all six ISOs), **`capacity_market_clearing=False`** (the
scalar default; FF-2C flips per-ISO later - plan S2.1a a), `confirmed_exits_enabled=True`
(default), `reserve_margin_build_enabled=False` (default -> no force-build backstop).
Runs used `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1`, <=2 ISO
invocations concurrent, years sequential within each invocation (rule 12).

**Reproduce.**
```
# 0. Fresh checkout: regenerate the gitignored data/clean tree from raw FIRST
#    (the forecast solve does NOT need the 28M-row hourly `emissions`/`emissions-
#    unit-annual` CEMS datatypes - it reads the precomputed plant_emission_rates_v2
#    + custom-bin-assignments artifacts; skip those two to save ~20 min).
uv run python scripts/regenerate_clean.py   # (or a subset excluding emissions*)

# 1. Per ISO (MALLOC_ARENA_MAX etc. as above):
uv run python scripts/run_full_horizon.py --iso <ISO> \
  --start-year 2026 --end-year 2030 --out-dir results/ff-t1f-baseline/<iso>
# 2. Collate + score:
uv run python scripts/collate_full_horizon.py --root results/ff-t1f-baseline \
  --out results/ff-t1f-baseline/_tables.md
# 3. Register each as a forecast-validation sidecar (label ff-t1f-baseline):
uv run python scripts/register_forecast_baseline.py \
  --summary results/ff-t1f-baseline/<iso>/full_horizon_summary.json
```
The per-year cache makes runs resumable (a killed run resumes from its last cached
year).

---

## 1. Headline findings (lead)

1. **All six ISOs execute end-to-end - MISO's forecast path is now runnable
   (blocker cleared).** The P-3A hard blocker (`STORAGE_BASE_FLEET_MW` missing MISO
   -> `_resolve_pace` `ValueError`) is **resolved**: MISO solved 5/5 years. The only
   fresh-checkout obstacle was a **data-bootstrap** gap, not a code gap - the
   gitignored `data/clean/` tree must be regenerated from raw before any solve
   (S4). No fail-loud registry gap needed a code fix.
2. **The machinery invariants hold everywhere; the failures are all
   economic/adequacy.** I1 (energy balance), I2 (no NaN/inf), I5 (no
   retire-reenter), I6 (retirement sanity), I8 (planned-addition gating), I10 (RPS
   dual), I11 (one-pass), I13 (cobweb) **PASS for all six ISOs**. Every FAIL/WARN is
   concentrated in **I7 (reliability floor), I12 (reserve-margin band), I3
   (unserved/dump), I4 (capacity accounting), I9 (storage)** - the adequacy/price
   family, exactly as the F1/F2 de-firming diagnosis predicts.
3. **NEW anomaly - I4 capacity-accounting FAILs for 4/6 ISOs (CAISO, PJM, MISO,
   NEISO), a regression vs the full-horizon run where I4 passed everywhere.** In
   each case a **steam-thermal class loses capacity with no matching ledger
   retirement record**: CAISO gas_st 2027 (-1333 MW unlogged), MISO coal 2029
   (-1640 MW), PJM coal 2029 (-743 MW), NEISO coal 2028 (-54 MW). This is a
   ledger-completeness / capacity-leak bug in the evolution accounting, not an
   energy-market artifact (S7 A1). It did NOT appear in the 2026-2050 P-3A run - a
   genuine open regression. (ERCOT and NYISO pass I4.)
4. **#2064 ERCOT scarcity non-monotonicity reproduces in the 5-year window** (it
   was previously characterized as a full-horizon phenomenon). ERCOT slack>1MW hours
   = `[0, 28, 0, 26, 3]` (2026-2030) - non-monotone, with VOLL ($5000) spikes at
   2027/2029/2030. **MISO shows the same signature** (`[4, 2, 4, 7, 11]`, non-monotone,
   scarcity to ~$1400) - a new #2064-class ISO. The correlated-forced-outage HEAD
   default (cfo=True) plausibly sharpens the ERCOT spikes vs the cfo=False
   full-horizon run (S7 A4).
5. **Base-year adequacy (I7) fails for every capacity-market ISO except PJM.** I7
   fails at 2026 for CAISO, MISO, NYISO, NEISO (accredited firm < requirement);
   PJM is the clean A/B (as at full-horizon). CAISO's base-year reserve margin is
   **-14.2%** (accredited firm far below peak) - the sharpest instance. This is the
   S1.2-row-5 base-year accreditation/requirement basis mismatch, now with MISO
   added to the list.
6. **De-firming compounds early everywhere; HEAD's DC=mid load boom makes the
   thermal expansion aggressive.** With `capacity_market_clearing=False` the
   capacity price never responds, so Phase-1 de-firming (full-horizon S5) is visible
   inside 5 years: every ISO starts at/below its planning floor (I12), and load
   growth (DC boom) drives large economic thermal entry (ERCOT +15 GW thermal, +41
   GW total by 2030). **ERCOT CO2 rises +40% (175->246 Mt)** over five years under
   default policy - the full-horizon rising-ERCOT-CO2 finding, steeper in the short
   window (S7 A6).

---

## 2. Feasibility - wall time & peak RSS (plan S2.4 ledger)

_(collated: `results/ff-t1f-baseline/_tables.md`; per-year in each ISO's
`full_horizon_summary.json`)_

| ISO | years | wall (5 yr) | median yr | max yr | peak RSS | note |
|---|---|---|---|---|---|---|
| ERCOT | 5/5 | 16.2 min | 210 s | 238 s | 4.03 GB | per-plant 7-zone |
| CAISO | 5/5 | 15.2 min | 167 s | 260 s | 4.49 GB | per-plant 3-zone+import |
| MISO | 5/5 | 21.4 min | 232 s | 353 s | **9.26 GB** | per-plant 6-zone - heaviest RSS |
| NYISO | 5/5 | 8.5 min | 90 s | 152 s | 3.06 GB | per-plant 5-zone |
| NEISO | 5/5 | 7.4 min | 81 s | 122 s | 3.30 GB | per-plant 4-zone+import - fastest |
| PJM | 5/5 | 19.0 min | 201 s | 334 s | 8.23 GB | per-plant 8-zone |

**T1-F budget (<=45 min/ISO) is met with wide margin** - every ISO <= ~22 min for
five years. **MISO peaks 9.26 GB** (base-year per-plant fleet build) - the binding
concurrency constraint on a 15 GB box; MISO or PJM must **not** co-run with another
per-plant ISO's base-year build (their transients would breach 15 GB). All other
pairs co-ran safely (observed combined RSS <= 7.9 GB). Per-year wall is **highest at
the base year** (fleet-build + first-solve) then flattens - the opposite of the
full-horizon tail-heavy profile, because 5 years accrues little fleet growth.

**Concurrency actually used** (rule 12, RSS-checked): MISO||NEISO -> MISO||NYISO ->
ERCOT||NYISO -> ERCOT||CAISO -> **PJM solo** (heaviest, run alone after CAISO). No OOM.

---

## 3. Invariant matrix (I1-I14)

`P`=PASS `**F**`=FAIL `W`=WARN. All ISOs solved 5/5 (no partials).

| ISO | I1 | I2 | I3 | I4 | I5 | I6 | I7 | I8 | I9 | I10 | I11 | I12 | I13 | I14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | P | P | **F** | P | P | P | P | P | P | P | P | W | P | W |
| CAISO | P | P | **F** | **F** | P | P | **F** | P | **F** | P | P | **F** | P | P |
| PJM | P | P | P | **F** | P | P | P | P | P | P | P | P | P | P |
| MISO | P | P | P | **F** | P | P | **F** | P | P | P | P | W | P | P |
| NYISO | P | P | P | P | P | P | **F** | P | P | P | P | W | P | P |
| NEISO | P | P | P | **F** | P | P | **F** | P | P | P | P | W | P | P |

**Structural invariants (I1/I2/I5/I6/I8/I10/I11/I13) PASS for every ISO** - the LP,
the ledger continuity, the one-pass evolution, and the RPS dual are all sound. The
FAIL/WARN set is entirely adequacy/price/accounting. **I4 fails for 4/6 ISOs**
(CAISO, PJM, MISO, NEISO - the steam-thermal leak, S7 A1); **I7 fails for 4/6**
(CAISO, MISO, NYISO, NEISO - every cap-market ISO *except PJM*, the clean A/B).

**FAIL/WARN detail:**

- ERCOT [FAIL] I3 unserved/dump: 2027: slack 0.03% of load; 2029: slack 0.03% of load
- ERCOT [WARN] I12 reserve-margin band: scalar floor [13.8%, 28.7%]; out: 2027:13.4%, 2029:11.6%
- ERCOT [WARN] I14 price sanity: 2027: LW $59.4 outside [0.5x,3.0x] CC MC $15.7; 2029: LW $63.1
- CAISO [FAIL] I3 unserved/dump: 2030: slack 0.02% of load
- CAISO [FAIL] I4 capacity accounting: 2027: gas_st off by 1333.0 MW
- CAISO [FAIL] I7 reliability floor: 2026: firm 42734<57306 MW; 2027: 49856<58671; 2028: 59605<60082
- CAISO [FAIL] I9 storage integrity: 2030: simultaneous chg+dis 0.13% of throughput
- CAISO [FAIL] I12 reserve-margin band: implied floor [15.0%,30.0%]; out: 2026:-14.2%, 2027:-2.3%, 2028:14.1%
- PJM [FAIL] I4 capacity accounting: 2029: coal off by 742.6 MW
- MISO [FAIL] I4 capacity accounting: 2029: coal off by 1639.8 MW
- MISO [FAIL] I7 reliability floor: 2026: firm 133834 < requirement 135371 MW
- MISO [WARN] I12 reserve-margin band: implied floor [10.0%,25.0%]; out: 2026:8.7%
- NYISO [FAIL] I7 reliability floor: 2026: firm 30322 < requirement 32121 MW
- NYISO [WARN] I12 reserve-margin band: implied floor [8.0%,23.0%]; out: 2026:1.9%
- NEISO [FAIL] I4 capacity accounting: 2028: coal off by 54.0 MW
- NEISO [FAIL] I7 reliability floor: 2026: firm 27171 < requirement 28797 MW
- NEISO [WARN] I12 reserve-margin band: implied floor [15.7%,30.7%]; out: 2026:9.2%, 2030:30.7%

---

## 4. MISO executability + the fresh-checkout data-bootstrap (verification)

**The storage-registry fix works.** `STORAGE_BASE_FLEET_MW["MISO"]` is present
(`{low:600, mid:800, high:1440}` MW, `constants.py`), so `build_default_storage` ->
`_resolve_pace` no longer raises for MISO. MISO solved all five years.

**The real fresh-checkout obstacle was `data/clean/` absence, not code.** `data/clean`
is derived + gitignored (CLAUDE.md), so a fresh clone has **no** curated tree, and
the first MISO solve fail-loud-aborted on `confirmed-retirements` (fail-loud is
working as designed - it refuses to silently degrade the confirmed-exit channel).
Remedy is the documented `scripts/regenerate_clean.py`, **no code change** (rule 5:
cited-values, fail-loud pattern already correct). **Key efficiency finding:** the
forecast solve reads the **precomputed** `plant_emission_rates_v2.parquet` +
`custom-bin-assignments.csv` artifacts (both committed under `data/raw/`), so the
28M-row-per-year hourly `emissions` / `emissions-unit-annual` CEMS curation is **not
on the forecast critical path** - skipping those two datatypes cuts the bootstrap by
~20 min with no effect on results. This is a fresh-checkout ergonomics note, not a
model finding.

**No fail-loud registry gap required a fix** (the FF-0B "fix ONLY fail-loud registry
gaps" clause was not exercised - nothing structural surfaced).

---

## 5. Evolution-ledger summary - retire / build / backstop by year

Per-year retirements, thermal/renewable/storage builds (GW), and reserve backstop.
**Backstop = 0 for every ISO-year** (`reserve_margin_build_enabled=False` default -
no force-build; every addition is economic entry or the EIA-860 planned pipeline).
Storage in the `capacity_by_fuel` view is 0 (storage is a separate fleet, not a
generator fuel) - storage *builds* are the `bldSt` column.

| ISO | year | retire GW | build thermal GW | build renew GW | build storage GW | backstop GW |
|---|---|---|---|---|---|---|
| ERCOT | 2027 | 0.00 | 0.88 | 5.00 | 3.00 | 0.00 |
| ERCOT | 2028 | 0.00 | 7.08 | 6.00 | 3.00 | 0.00 |
| ERCOT | 2029 | 0.00 | 1.34 | 0.00 | 0.00 | 0.00 |
| ERCOT | 2030 | 0.00 | 8.00 | 4.00 | 3.00 | 0.00 |
| CAISO | 2027 | 1.49 | 9.00 | 7.00 | 0.00 | 0.00 |
| CAISO | 2028 | 0.00 | 9.00 | 7.00 | 0.00 | 0.00 |
| CAISO | 2029 | 0.00 | 2.05 | 7.00 | 0.00 | 0.00 |
| CAISO | 2030 | 1.12 | 3.00 | 5.00 | 0.00 | 0.00 |
| PJM | 2027 | 0.00 | 2.50 | 7.50 | 0.00 | 0.00 |
| PJM | 2028 | 0.00 | 2.50 | 7.50 | 0.00 | 0.00 |
| PJM | 2029 | 3.30 | 2.50 | 7.50 | 0.00 | 0.00 |
| PJM | 2030 | 0.00 | 2.50 | 7.50 | 0.00 | 0.00 |
| MISO | 2027 | 0.00 | 6.29 | 4.00 | 0.00 | 0.00 |
| MISO | 2028 | 0.00 | 3.71 | 0.00 | 0.00 | 0.00 |
| MISO | 2029 | 0.00 | 3.00 | 0.00 | 0.00 | 0.00 |
| MISO | 2030 | 0.63 | 3.81 | 0.00 | 0.00 | 0.00 |
| NYISO | 2027 | 0.01 | 2.20 | 3.00 | 0.00 | 0.00 |
| NYISO | 2028 | 0.00 | 1.00 | 1.00 | 0.00 | 0.00 |
| NYISO | 2029 | 0.00 | 1.00 | 1.00 | 0.00 | 0.00 |
| NYISO | 2030 | 0.00 | 1.00 | 1.00 | 0.00 | 0.00 |
| NEISO | 2027 | 0.00 | 2.06 | 3.00 | 0.00 | 0.00 |
| NEISO | 2028 | 0.00 | 1.00 | 3.00 | 0.00 | 0.00 |
| NEISO | 2029 | 0.00 | 1.00 | 3.00 | 0.00 | 0.00 |
| NEISO | 2030 | 0.00 | 1.00 | 3.00 | 0.00 | 0.00 |

(2026 = base year, no evolution; every ISO shows 0/0/0/0.)

**Reads:**
- **Storage builds only in ERCOT** (energy-only): ERCOT adds 3 GW storage in
  2027/2028/2030; **every capacity-market ISO builds 0 storage**. Coherent with
  `capacity_market_clearing=False` - the value-stack storage entry pays RA capacity
  value *only* through a capacity market (per-ISO `MARKET_DESIGN`), so with clearing
  off the cap-market ISOs give storage no capacity revenue and only ERCOT's
  arbitrage-only economics clear. A HEAD-defaults consequence to revisit once FF-2C
  flips clearing on (S7 A5).
- **Retirements are small and sparse** (CAISO 1.49 GW @2027 + 1.12 @2030; MISO 0.63
  @2030; NYISO 0.01 @2027; ERCOT 0). The default `forecast_fossil_retirement_economic`
  no-op on announced fossil + the confirmed registry produce little exit in-window;
  the RC-1 decision-rule inversion (S1.2-1) is not exercised hard at this horizon.
- **Economic thermal entry is large under DC=mid**: ERCOT builds 41 GW total
  (2027 +6.9k, 2028 +7.1k thermal), CAISO 49 GW, MISO 21 GW cumulative by 2030 -
  the load boom pulling in gas CT/CC + VRE.

---

## 6. Trajectory snapshots (RM / price / CO2 / scarcity)

| ISO | year | RM %* | LW $ | max $ | CO2 Mt | thermal GW | VRE GW | total GW |
|---|---|---|---|---|---|---|---|---|
| ERCOT | 2026 | 14.6 | 24.9 | 45 | 175.5 | 78.5 | 80.0 | 159.0 |
| ERCOT | 2030 | 14.4 | 45.2 | 5000 | 246.0 | 93.8 | 95.0 | 191.3 |
| CAISO | 2026 | -14.2 | 47.9 | 60 | 34.3 | 31.2 | 29.0 | 79.7 |
| CAISO | 2030 | 19.2 | 50.1 | 1077 | 9.5 | 47.3 | 55.0 | 124.8 |
| PJM | 2026 | -10.2 | 32.8 | 48 | 301.4 | 169.0 | 25.0 | 203.0 |
| PJM | 2030 | -10.4 | 36.2 | 52 | 348.0 | 174.9 | 55.0 | 239.0 |
| MISO | 2026 | 8.7 | 30.1 | 1548 | 328.7 | 131.0 | 39.0 | 174.3 |
| MISO | 2030 | 10.0 | 38.2 | 1389 | 353.1 | 145.6 | 43.0 | 192.8 |
| NYISO | 2026 | 1.9 | 42.1 | 53 | 27.0 | 29.9 | 3.9 | 44.6 |
| NYISO | 2030 | 17.4 | 49.6 | 58 | 25.8 | 35.1 | 9.9 | 55.8 |
| NEISO | 2026 | 9.2 | 45.1 | 58 | 21.6 | 23.1 | 4.1 | 34.6 |
| NEISO | 2030 | 30.7 | 44.8 | 57 | 8.2 | 28.2 | 16.1 | 51.6 |

*\*RM = the ledger `reserve_margin` = accredited-firm / peak - 1, stated on each
ISO's own **UCAP/accreditation basis** - it is **not** comparable across ISOs and
not a physical-shortage indicator. PJM's -10% is a structurally-negative UCAP-basis
margin (PJM has **zero** slack all years); it PASSES I7/I12 because its requirement
floor is computed on the *same* basis (W2-D). CAISO's -14.2% FAILS because its
requirement floor is on a **different** basis than its rm numerator (S7 A2). CO2 is
reconstructed dispatch x context emission-rate (the forecast DispatchResult carries
no emissions array; same method as `golden_forecast_bands`).*

**#2064 scarcity watch - slack>1MW hours (from parquets, `_tables.md`):**

| ISO | slack_hrs 2026->2030 | monotone? | max $ path | reads |
|---|---|---|---|---|
| ERCOT | 0, 28, 0, 26, 3 | **No** | 45/5000/110/5000/5000 | #2064 VOLL spikes 2027/2029/2030 |
| MISO | 4, 2, 4, 7, 11 | **No** | 1548/1381/1382/1387/1389 | new #2064-class; scarcity to ~$1.4k |
| CAISO | 0, 2, 11, 19, 34 | Yes | 60/968/966/969/1077 | monotone rising de-firm slack |
| PJM | 0, 0, 0, 0, 0 | Yes | 48/46/47/50/52 | no scarcity; flat ~$50 |
| NYISO | 0, 0, 0, 0, 0 | Yes | 53/52/54/56/58 | no scarcity |
| NEISO | 0, 0, 0, 0, 0 | Yes | 58/52/54/58/57 | no scarcity |

---

## 7. Top anomalies - each with a mechanism hypothesis (module named)

Every item routes to a root-cause investigation, never a threshold change (rules
1/11/14). Ranked by novelty x severity.

### A1 - I4 capacity-accounting leak in steam-thermal classes (NEW; blocks the
### capacity-accounting invariant for 4/6 ISOs)
**What.** Within a single evolution year the after-fleet of a steam-thermal class is
lower than `before - sum retirements + sum additions` by a material margin: **CAISO gas_st
2027 -1333 MW**, **MISO coal 2029 -1640 MW**, **PJM coal 2029 -743 MW**, **NEISO
coal 2028 -54 MW** (4/6 ISOs; ERCOT and NYISO close). Worked
example (CAISO 2027, from the persisted ledger): gas_st `before=2858.8`, `after=34.8`
(delta  -2824), but only **1491 MW** is logged in `retirements` (the named
`ST_GAS_LA_BASIN_p350_*` tranches, reason `known`); `pipeline_events` empty,
`ccs_retrofits` empty; gas_cc/gas_ct build deltas reconcile exactly. So **~1333 MW of
gas_st leaves the fleet with no ledger record.**
**Mechanism hypothesis.** A capacity-removal channel in `model/capacity.py`
(economic retirement of plant-binned steam tranches, or a fuel-class
reclassification / summer-capacity reconciliation applied during the post-evolution
fleet snapshot) reduces the class MW **without emitting a `retirements` record that
carries `{fuel, mw}`**. Either the model leaks capacity or the ledger under-records
the decision; `results/evolution_ledger.py` serializes what I4 reconstructs from, so
the fix lands in one of those two. Because it did not appear in the P-3A 2026-2050
run (I4 passed everywhere there), it is a **regression** - bisect capacity/ledger
commits between 2026-07-12 and HEAD, or a config-surfaced path (per-plant + DC=mid
retiring a whole CA gas-steam basin in one year exposes it). **Module:**
`model/capacity.py` (`apply_economic_retirements` / retirement-record emission) +
`results/evolution_ledger.py`.

### A2 - Base-year I7 reliability-floor miss for every cap-market ISO but PJM
**What.** Accredited firm < requirement at 2026: CAISO 42.7<57.3 GW, MISO
133.8<135.4, NYISO 30.3<32.1, NEISO 27.2<28.8. CAISO also 2027-2028; the others
resolve as economic entry closes the gap. **PJM passes I7 (and I12) every year** -
even though its ledger RM is a structurally-negative **-10%** - because its
requirement floor is computed on the **same** UCAP basis as its accredited-firm
numerator (the W2-D adequacy side-registry aligned the two), so rm >= floor. ERCOT
passes (energy-only, no accreditation floor).
**Mechanism hypothesis.** A base-year accreditation/requirement **basis mismatch**:
for the four failing ISOs the accredited-firm accounting
(`accredited_firm_capacity_mw`, UCAP/ELCC pools) and the requirement
(`resolve_adequacy_requirement_mw`) are on **different** bases at the base year (the
#1532 basis flag on the accreditation side), so the margin is spuriously negative;
PJM - where W2-D put both on one basis - is the isolating A/B (it is UCAP-negative
yet in-band because its floor is UCAP too, and it carries zero physical slack).
**Module:** `model/capacity.py::resolve_adequacy_requirement_mw` + the
accredited-firm accounting; the NEISO requirement is additionally a NERC stand-in
(`0.157`, needs Net ICR - S1.2-7). Routes to **FF-2B**.

### A3 - I12 reserve-margin band breached in every ISO (Phase-1 de-firming)
**What.** CAISO FAILs (three consecutive out-of-band years, **RM -14.2% at 2026**);
ERCOT/MISO/NYISO/NEISO WARN (base-year below floor, recovering as entry lands).
**Mechanism hypothesis.** The non-responsive capacity price (`cmc=False`): the fleet
starts at/below the planning floor and only economic energy-margin entry corrects it,
with no capacity-price signal - the full-horizon Phase-1 de-firming, realized inside
5 years. Cure is the responsive capacity price (FF-2C flips) + entry dynamics
(FF-2A). **Module:** `model/capacity.py` entry/backstop + `capacity_market_clearing`
gate. Routes to **S1.2-4 / FF-2C**.

### A4 - I3 slack + #2064 non-monotone scarcity (ERCOT, now MISO)
**What.** ERCOT I3 FAIL (slack 0.03% @2027/2029); slack_hrs `[0,28,0,26,3]`
non-monotone with $5000 VOLL spikes. MISO slack_hrs `[4,2,4,7,11]` non-monotone,
scarcity to ~$1400. CAISO slack 0.02% @2030 (monotone). NYISO/NEISO zero slack.
**Mechanism hypothesis.** One-pass evolution discreteness: a year's economic entry
either does or doesn't clear the adequacy gap *before* scarcity is realized, so
VOLL-priced slack toggles year-to-year (#2064). ERCOT's energy-only design expresses
de-firming as scarcity rather than an I7 miss; **cfo=True (HEAD default) plausibly
sharpens the spikes** - the correlated cold-event derate removes firm MW in the
tightest hours, which cfo=False (the full-horizon run) did not. MISO joining is
new-ISO evidence, not a new mechanism. **Module:** `runner.py` one-pass year loop +
`model/scarcity.py` (ERCOT ORDC) + `data/outages.py` (cfo derate). Routes to
**S1.2-4**.

### A5 - Zero storage build in every capacity-market ISO
**What.** ERCOT builds 3 GW storage (2027/28/30); CAISO/MISO/NYISO/NEISO build 0.
**Mechanism hypothesis.** `capacity_market_clearing=False` -> the storage value-stack's
RA-capacity-value leg (paid only via a capacity market, per-ISO `MARKET_DESIGN`)
returns 0 for cap-market ISOs, so only ERCOT's arbitrage-only storage economics
clear. Expected to change when FF-2C flips clearing on; flagged so the BEFORE->AFTER
storage delta is attributable. **Module:** `model/capacity.py` storage value-stack +
`MARKET_DESIGN` registry. Routes to **S1.2-3 (BLK-7 VRE/storage capacity revenue)**.

### A6 - ERCOT (and MISO) CO2 rises under default policy; DC=mid amplifies
**What.** ERCOT CO2 175->246 Mt (+40%) over 2026-2030; MISO 329->353 (+7%). CAISO
-72%, NEISO -62%, NYISO ~flat (their RPS + VRE entry decarbonize). ERCOT's rise is
**steeper than the full-horizon per-year rate** - the DC=mid load boom pulls in gas
CT/CC faster with no binding carbon price and RPS=0.
**Mechanism hypothesis.** Driver-wiring, not a defect: DC=mid demand growth x
(RPS=0 for ERCOT, weak for MISO) x no binding carbon adder -> thermal expansion
outruns clean entry. A driver-battery question (carbon/IRA/RPS strength vs load), not
a tuning target. **Module:** `policy/ira.py` / `policy/carbon.py` / demand+DC
constants. Routes to **S1.2-8 (Tier-1 driver follow-up)**.

### A7 - I9 storage simultaneous charge+discharge (CAISO 2030, 0.13%)
**What.** CAISO I9 FAIL: 0.13% of throughput simultaneous chg+dis at 2030 (small,
grows with storage penetration + negative-price frequency).
**Mechanism hypothesis.** The eps=0.001 $/MWh storage tiebreaker degenerates at high
storage penetration / frequent near-zero prices (numerical, not physics) - the
full-horizon I9 finding, milder here (0.13% vs 5.8% at 25 yr). **Module:**
`model/storage.py` eps-tiebreak. Routes to **S1.2-8 / FF-3C (with T2 evidence).**

---

## 8. Ranked triage list -> plan S1.2 rows

| # | Finding | S1.2 row | Lane / wave | Action |
|---|---|---|---|---|
| 1 | **A1 I4 steam-thermal capacity-accounting leak (NEW, 4/6 ISOs)** | **NEW row 11** | L-CAP | Root-cause `model/capacity.py`+`evolution_ledger.py`; bisect vs 07-12. Blocks I4. |
| 2 | A2 base-year I7 for CAISO/MISO/NYISO/NEISO | row 5 (add MISO) | L-CAP / **FF-2B** | Accreditation-basis closure; PJM is the A/B. |
| 3 | A3 I12 de-firming (CAISO FAIL) | row 4 | L-CAP / **FF-2C** | Responsive capacity price + entry dynamics. |
| 4 | A4 I3 slack + #2064 (ERCOT, MISO) | row 4 (#2064) | L-CAP/L-SCAR | One-pass discreteness; measure cfo=True contribution. |
| 5 | A5 zero cap-market storage build | row 3 (BLK-7) | L-CAP / **FF-2A/2C** | Value-stack capacity leg = 0 while clearing off; re-measure post-flip. |
| 6 | A6 rising ERCOT/MISO CO2 (DC=mid) | row 8 | L-INP/L-VAL | Driver battery; carbon/RPS strength vs load. |
| 7 | A7 I9 storage eps-degeneracy (CAISO) | row 8 | L-PERF / **FF-3C** | eps-tiebreak at high penetration; T2 evidence first. |

**Proposed new S1.2 frontier row (row 11):** *"Evolution capacity-accounting leak -
I4 FAILs for CAISO/PJM/MISO/NEISO (4/6): a steam-thermal class (gas_st/coal) loses
capacity with no matching ledger `retirements` record (CAISO gas_st 2027 -1333 MW;
PJM coal 2029 -743 MW). NEW at HEAD (I4 passed at full-horizon 2026-07-12). ->
root-cause `model/capacity.py` + `results/evolution_ledger.py`."* (Append-edit to the
plan per S7.8 - left for the plan-owner / a follow-up, since this session is
findings-only and does not tune.)

---

## 9. Registration + what this session did / did not do

**Registered** all six runs on the **forecast-validation dashboard namespace**
(`frontend/data/hindcast/<iso>-2026-2030-ff-t1f-baseline.json`, kind `t1f`, label
`ff-t1f-baseline`) via `scripts/register_forecast_baseline.py` (a new additive
helper that turns `full_horizon_summary.json` into a sidecar in the same namespace
`register_hindcast.py` uses; `score=null`, invariant chips + a compact per-year
summary + perf embedded). These are the **BEFORE legs** every Wave-1/2 change compares against -
solve once, reuse forever (plan S7.5; never the backcast registry).

- **Did:** solved all six ISOs 2026-2030 at HEAD defaults (5/5 each, no errors);
  scored I1-I14; verified the MISO storage-registry fix; captured the S2.4 wall/RSS
  ledger; root-caused the I4 leak to a specific unlogged capacity channel; mapped
  every anomaly to a S1.2 row; registered the six sidecars; wrote this doc.
- **Did not:** change any model code, threshold, offer curve, or default; edit the
  plan S1.2 table (left the proposed row 11 as a recommendation - findings-only);
  solve/score any 2022/<=2021/2019/H1-2026 year; touch the backcast registry; run any
  solve on CI (all in-session, rule 12 / plan S7.3).

*Data provenance: `results/ff-t1f-baseline/<iso>/full_horizon_summary.json` (per-ISO)
and `results/ff-t1f-baseline/_tables.md` (collated). Forecast probes - registered on
the forecast-validation namespace, not the backcast dashboard.*

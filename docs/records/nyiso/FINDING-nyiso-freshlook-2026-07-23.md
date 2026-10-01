# FINDING — NYISO fresh-look (2026-07-23): candidate A (upstate-cheap) REFUTED with zonal evidence; C3c reframed as tail-compression; one grounded lever taken (ST_GAS overnight floor)

**Scope.** Fresh, broad re-scoping of NYISO's calibration misses off keeper
`nyiso-70` (`2026-07-22-nyiso-70-scr-edrp`, NOT-YET). Read-only zonal
decomposition of the committed keeper hourly sidecars + one instrumented 2023
solve + real NYISO zonal RT LMP (`data/raw/lmp-data/NYISO/20230601realtime_zone_csv.zip`,
June 2023, a shoulder **train** year — rule 22 compliant) + measured CAMPD
ST_GAS diurnal CF. Result: the handoff's **top** candidate (A, upstate-cheap /
Central-East decoupling) is **refuted for the off-peak trough** and **grounded /
settled for on-peak**; the dominant C3a miss remains the below-SRMC
price-formation limit the 2026-07-23 diagnosis (`FINDING-nyiso-2023-c3a-offpeak-diagnosis`)
already identified. One NYISO-contained, measured-data-grounded structural lever
was found and taken → bundle `nyiso71_stgas_overnight_floor`.

## 1. Candidate A (upstate-cheap / Central-East) — REFUTED off-peak, GROUNDED on-peak

Real vs model per-zone mean LMP, June 2023 shoulder (real from NYISO zonal RT
postings; model from the keeper sidecar):

| zone | real off-pk | model off-pk | real on-pk | model on-pk |
|---|--:|--:|--:|--:|
| Upstate_West | 19.9 | **32.4** | 29.5 | **40.5** |
| Capital_Hudson | 20.7 | 32.4 | 35.3 | 40.6 |
| NYC | 20.9 | 32.4 | 34.7 | 41.2 |
| Long_Island | 24.0 | 32.4 | 48.9 | 43.0 |
| **load-weighted** | **20.9** | **32.4** | **34.6** | **41.0** |

**Off-peak (the trough that drives C3a): real NYISO is FLAT across zones (~$21),
not upstate-cheap.** Congestion component ≈ $0 off-peak; Central-East does not
bind in reality OR the model off-peak. The uniform model floor is therefore
**structurally correct** — the miss is a pure **LEVEL** gap (+$11.5), not a
missing zonal structure. The handoff's premise ("restore upstate-cheap to pull
C3a down") does not hold off-peak.

**On-peak:** real DOES decouple (Central-East binds → upstate $29.5 « downstate
$35-49); the model under-decouples (upstate $40.5 ≈ Capital $40.6). But this is
**grounded/settled, not a fixable knob**:
- The Central-East limit is the **measured** NYISO posted DAM TTC (`derive_nyiso_central_east_ttc.py`;
  2023 monthly envelope 1450-1950 MW, June 1900) — cannot be tuned (rule 11).
- The instrumented solve shows Central-East flow only 386 (off) / 845 (on) MW,
  p95 1650 — it rarely reaches the limit because **upstate cheap-gen surplus is
  exhausted**: on-peak upstate nuclear (3270) + hydro (3742, 351 headroom) + gas-CC
  (694 avail / 680 run — the CC pmax 2049 is CEMS-outage-derated to 694) leave no
  surplus to fill the interface. Those outages are CEMS-verified and **settled**
  (`nyiso-outage-source-determination`, rule 11). Given the measured fleet the
  model is faithful; reality's stronger Central-East binding reflects
  hour-resolution outage timing the annual-window overlay cannot express.

The model's zonal gas basis (`nyiso_zonal_gas_hub.csv`: 2023 Upstate Tenn-Z4
$1.82, NYC Transco $1.94, Capital/LI Iroquois $3.28) and monthly gas seasonality
are present and correct; the model even carries cheap June CCs (~$15-16 mc
upstate/NYC) — they are simply exhausted, so the marginal is a dearer Iroquois CC.

## 2. C3a off-peak — confirmed below-SRMC limit (out of NYISO scope)

Consistent with the 2026-07-23 diagnosis: with grounded demand, imports (the
model imports MORE off-peak than the measured schedule), nuclear, hydro, gas
(ISO-month + measured zonal basis), RGGI, and CEMS-verified outages, the
full-SRMC LP troughs at ~$30-32 uniformly where reality troughs to ~$21. The
residual is the **below-SRMC overnight commitment-bid** price-formation gap
(committed thermal offering below full marginal cost to avoid a restart) — a
**cross-ISO methodology change** requiring model-wide validation, not a NYISO
calibration lever. No NYISO-contained mechanism closes it.

## 3. C3c reframed — tail COMPRESSION, not simple "over-scarcity"

2023 scarcity counts (model keeper vs actual RT):

| band | model (load-wt) | model (any-zone) | actual RT |
|---|--:|--:|--:|
| >$100 | 46 | — | 108 |
| >$300 | 3 | 22 | 10 |
| >$500 | 0 | — | 2 |
| >$1000 | 0 | — | 1 |

The model **under-populates** the $100-300 band (46 vs 108) and **never reaches
the extreme tail** (0 vs 2 above $500), while clustering 22 any-zone $300-500
downstate (NYC/LI, CT_PEAKER + reserve-dual) events. The C3c FAIL is a
distribution-**shape** problem (too many moderate, no extreme), not a uniform
over-scarcity to be dialed down. Sharpening it is a scarcity-pricing calibration
(rule-13 risk) — deferred, not taken.

## 4. Candidate E (CO2 / C5a) — CHP "2× emission" is arguably correct, tiny fleet

CT_CHP (0.109 tCO2/MMBtu) and ST_CHP (0.100) run ~2× the gas factor (0.0531) —
but this correctly captures **total stack CO2 incl. steam-host fuel** (matching
eGRID's total-mass basis), and the fleet is tiny (CT_CHP 258 + ST_CHP 249 MW).
Not a clean bug; the C5a 2025 +8.5% is dispatch-driven, not an emission-rate
error. Not taken.

## 5. Candidate D (ST_GAS overnight floor) — PROBED and REJECTED by the scorer

The one NYISO-contained, source-data-grounded shape lever. The NYC/LI ST_GAS
reliability floor carries a FLAT "persistent 24h base"
(`reliability_floor_coeffs_NYISO.csv`, threshold=-50 → binds all hours). Using
`derive_nyiso_st_reliability_floor.py`'s **own methodology** (cool-day
when-available CF p25) but per hour-of-day window, the 24h pool sits above the
overnight-only p25 (NYC 24h 0.496 vs HB0-6 0.430; LI 0.436 vs 0.308) — so
lowering the persistent base to the overnight p25 makes the modelled ST_GAS
off-peak profile diurnal instead of pinned flat.

**Full 3-year bundle `nyiso71_stgas_overnight_floor` (registered
`2026-07-23-nyiso-71-stgas-overnight`) — REJECTED, strictly worse than nyiso-70
(4 FAILs vs 3):**

| criterion | nyiso-70 | nyiso-71 | Δ |
|---|---|---|---|
| C7 diurnal shape (protective) | FAIL (0.483) | **PASS** | fixed |
| C1 fuel-mix (load-bearing) | PASS | **FAIL** | broke |
| C3b price shape (load-bearing) | PASS | **FAIL** | broke |
| C3a mean (load-bearing) | FAIL | FAIL (+~1pp) | worse |

**Why it fails — the flat over-floor is a NEEDED PROP, not an over-force.** The
decisive datum: the C1 ST_GAS bench is **8.70 / 11.07 / 16.00 TWh** (2023/24/25),
and nyiso-70 already **under-runs** ST_GAS (7.40 / 8.58 / 11.37, −15% to −29%).
ST_GAS is steam (expensive) and the model's economics barely run it above the
reliability minimum; the flat floor is what pushes ST_GAS *up* toward the bench.
Lowering the floor (→ 6.93 / 7.92 / 10.83) **worsens the under-run and breaks
C1**, and removing the floored must-run supply lifts the overnight trough
(worsening C3a/C3b). Fixing the flat SHAPE (C7) by lowering the floor
necessarily costs VOLUME (C1) and price fit (C3a/C3b) — a genuine three-way
conflict, not a free win. A morning-knot variant cannot rescue it: the bulk of
the volume loss is overnight (which must stay lowered for the shape), so C1
stays broken. **Not promoted; nyiso-70 held.** (Config reverted; the derive
script's `base_overnight` computation is documented in the finding, not shipped.)

**Deeper root uncovered (the real forward lever): ST_GAS is under-generated
15–29% vs bench in every year.** The C7 flatness is a *symptom* — the model
leans on the flat floor because steam-gas rarely clears economically, so the
floored share dominates and is flat. The faithful fix is to make ST_GAS run more
(and diurnally) on its own economics/reliability — an ST_GAS-economics lever
(offer/heat-rate/in-city must-run calibration), paired with which the
overnight-p25 floor shape becomes correct. That is a substantive new lever, out
of scope here; logged for a future session.

## 6. Recommendation

- **Candidate A is dead for the off-peak trough** (real NYISO off-peak is flat
  across zones) and grounded/settled for on-peak (measured TTC + CEMS outages).
  Do not pursue upstate-cheap decoupling as a C3a lever.
- The dominant C3a miss is the below-SRMC price-formation limit — a cross-ISO
  methodology item, not a NYISO knob. `nyiso-70`'s residual is a structural
  limit, as the 2026-07-23 diagnosis concluded.
- **Candidate D (ST_GAS overnight floor) is rejected**: the scorer shows the
  flat over-floor props up an ST_GAS class the model under-runs; correcting the
  floor shape breaks C1/C3b. `nyiso-70` remains the keeper.
- **Next lever = ST_GAS economics** (close the −15% to −29% ST_GAS
  under-generation with a diurnal in-city must-run / offer calibration), which
  would fix C1 and C7 together the faithful way. Not the below-SRMC trough
  lever, and not a floor tweak.

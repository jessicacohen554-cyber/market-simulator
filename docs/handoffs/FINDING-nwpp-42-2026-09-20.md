# FINDING — nwpp-42: NWPP's coal heat rate was an estimate, and it was wrong at every plant

**Lane:** NWPP-42 · **Date:** 2026-09-20 · **Branch:** `claude/nwpp-42-coal-shape-scop49`
**Pre-registration:** `docs/handoffs/PRECOMMIT-nwpp-42-2026-09-19.md`
**Outcome:** **PROMOTED** — `2026-09-20-nwpp42-measured-coal-heat` is NWPP's keeper.
**Determination:** `NOT-YET` (rubric v3.8, PRICE UNSCORED), unchanged, on `{dispatch_corr}` alone.

---

## 0. The one-paragraph version

NWPP's only remaining rubric failure is **C4 coal**, and the diagnosis routed to this lane was
that it is a **merit-order** defect rather than a shape defect. The cause is now named: NWPP takes
the legacy aggregate-fleet path, which prices coal on **eGRID's annual plant average**
`PLHTIAN / PLNGENAN`. Measured against the plants' own CAMPD-metered steady-state rates, that
estimate is **high at every one of the 12 covered plants** (98.2 % of NWPP COAL capacity),
cap-weighted **11.868 → 11.066 MMBtu/MWh (−6.8 %)**, and the error is **not uniform** — Hunter
1.2153× against Colstrip 1.0228×. The arm replaces the estimate with the measurement.
Rule 14 `[R-ACCURATE]`, not the residual. Against a paired per-year control, **nothing regresses**
and every C4 coal number moves toward the measured fleet; **C4 still FAILs** and is reported as
such. The lane also delivers **NWPP's own measurement of the rule-36 year-isolation artifact**,
which rule 36(f) records as unmeasured outside MISO.

---

## 1. The phase-0 fork, decided before any solve

The PRECOMMIT's §1 fork was (a) derive `bin_assignments_NWPP.csv` and put NWPP on per-plant CAMPD
binning, or (b) establish why (a) is out of reach and pick another lever.

**Fork (b) was taken, and the reason is structural rather than convenient.**
`bin_assignments_<ISO>.csv` is absent for **every** legacy-bin ISO, not just NWPP; NWPP is absent
from `CAMPD_BINNING_ISOS` by owner ruling N8 with gate G21 standing over it. Deriving it is a
multi-lane programme, not a lane's arm, and standing it up inside this lane would have been an
unreviewed change to the fleet representation of the ISO whose keeper was at stake. The bimodal
coal offer stack that (a) would address is still the named successor for C4 (§7).

Fork (b)'s lever was chosen from the same root-cause chain, one layer down: if the merit order is
wrong, the operands that set it are the fuel price and the heat rate. **Fuel prices were measured
and inside EIA's published state ranges, so they were ruled out.** The heat rate was not.

---

## 2. The defect, measured zero-LP before any solve

`derive_campd_coal_heat_rates.py` (new, the COAL sibling of the nyiso-89 CT deriver) reads EPA
CAMPD unit-level hourly `opTime` / `grossLoad` / `heatInput` over 2023-2025 and converts to a NET
basis with the committed `parasitic_load_factors.parquet` — **the same map the benchmark's net
actual uses**, so both sides of the comparison sit on one basis.

| plant | code | MW | eGRID | measured | ratio |
|---|---|---|---|---|---|
| Hunter | 6165 | 1363.0 | 13.3303 | 10.9688 | **1.2153** |
| North Valmy | 8224 | 268.0 | 13.1105 | 11.3634 | 1.1537 |
| Hardin | 55749 | 107.0 | 15.8428 | 14.3005 | 1.1078 |
| Wyodak | 6101 | 332.0 | 13.1065 | 12.0467 | 1.0880 |
| Huntington | 8069 | 909.0 | 11.6307 | 11.0325 | 1.0542 |
| Dave Johnston | 4158 | 745.0 | 12.2829 | 11.6458 | 1.0547 |
| TS Power | 56224 | 218.4 | 10.4648 | 10.2183 | 1.0241 |
| Colstrip | 6076 | 1480.0 | 10.5702 | 10.3342 | **1.0228** |
| Centralia | 3845 | 670.0 | 11.4151 | 11.1734 | 1.0216 |
| Naughton | 4162 | 357.0 | 11.6091 | 11.5094 | 1.0087 |
| Jim Bridger | 8066 | 1049.0 | 11.2457 | 11.1511 | 1.0085 |
| Bonanza | 7790 | 458.0 | 11.9190 | 10.9071 | 1.0928 |

12 plants, **7,956.4 of 8,104.4 MW = 98.2 %** of NWPP COAL capacity. Cap-weighted
11.868 → 11.066 (−6.8 %); generation-weighted 11.726 → 11.025 (−6.0 %).
Table md5 `8dd65f9e73352bcd73ef4f4ea11f35fd`.

**Why this is structure and not a fitted multiplier (rule 1 `[R-STRUCT]`).** The correction is
**near-zero exactly where the model already reproduces the measured shape, and largest where it
does not**: Colstrip's correction is 1.023× and its *measured* diurnal peak/trough is 1.07 — a flat
plant the model already reads flat; Hunter's is 1.2153× and its measured peak/trough is 1.62
against a model 1.00. A multiplier fitted on a residual has no reason to line up that way. A real
heat rate does.

### 2.1 Two declared departures from the CT deriver

Both on physics, both fixed ex ante in PRECOMMIT §4 before any solve:

1. **`opTime >= 0.99` steady-state screen**, not the CT deriver's `>= 0.8 × p95` loaded-window
   screen — a coal unit's *normal* operating range includes part load, so a near-peak screen would
   measure only its best hours.
2. **`primaryFuelInfo`, not `unitType`** — at Jim Bridger, Naughton and North Valmy the coal units
   and the gas-converted units are **both boilers**, and `unitType` cannot separate them.

Neither choice was selected by looking at a result. Band screens `[8.0, 25.0]` gross /
`[8.0, 27.0]` net; ≥200 qualifying hours; `heat_rate_gross_hsl` (the ≥p90 near-HSL window) is
computed and **reported but never applied**; only `flag=='ok'` rows are read by the loader.

---

## 3. What was built

| file | what |
|---|---|
| `scripts/data/derive_campd_coal_heat_rates.py` | the deriver (new) |
| `data/raw/_processed-legacy/campd_coal_heat_rates_NWPP.csv` | the table (new, 12 rows) |
| `ScenarioConfig.measured_coal_heat_rates` | the gate (new, default `False`, cache-key registered) |
| `data/fleet/campd_bins.measured_coal_heat_rates(iso)` | the loader (flag-filtered, `lru_cache`) |
| `data/fleet/eia860._rows_to_generators` | the seam, **class-gated on `group == "COAL"`** |
| `data/fleet/assembly.py` (3 sites) | config → kwarg |
| `run_calibration{,_full}.py` | `--measured-coal-heat-rates` |
| `tests/unit/data/test_measured_coal_heat_rates.py` | the guard (new) |
| `scripts/probes/_nwpp42_leg_check.py` | per-leg signature check (new) |
| `scripts/probes/_nwpp42_compose_span.py` | the rule-36 composer (new) |
| `scripts/gen_nwpp42_attestation.py` | the attestation (new) |

**Confinement.** The class gate means the arm cannot reach a gas, hydro, nuclear or renewable unit
even at a plant that has both: **Jim Bridger (8066) contributes COAL rows and ST_GAS rows from the
same `plant_code`, and only the COAL rows take the measured value** — guarded by test.

---

## 4. How it was solved, and why a control solve was spent

**Rule 36 `[R-YEAR-ISOLATION]` landed mid-lane** (owner ruling 2026-09-19, miso-262), while two
span solves were in flight. Both were one `--year 2023 2024 2025` invocation pinned to a SHA
predating the knob flip, so both carried `MARKET_SIM_WARMSTART_XYEAR` / `_P1_BASIS_SEED` **ON**.
They were interrupted, and the lane relaunched as **six single-year shards** — three arm, three
control — pinned to `b68673a99926a554d0a9e165f5bd06b890572c02`, verified an ancestor of all six
bundle commits with `git merge-base --is-ancestor`.

**Rule 29(b) normally forbids a control solve.** It was spent here because rule 36(e) **withdrew
the neutrality claims** that justified the warm-start knobs, so the incumbent keeper's 2024/2025
numbers carried a solve-path artifact of size unmeasured outside MISO. Form 4 could not be relied
on for **C4**, the criterion at issue. So: `arm(year) − ctl(year)`.

**Leg recovery, by full immutable SHA (rules 33(d) / 34(a)) — every shard pushed its FULL bundle
including `dispatch/<year>_P1.parquet`:**

| leg | sha |
|---|---|
| arm 2023 | `319bcd45af22d565e9d3f669186e8957bd6359a3` |
| arm 2024 | `914d14920b42246691358d144765a21f1bd2a9df` |
| arm 2025 | `a7cdbe591044f519c9f0fd47e87158dace231205` |
| ctl 2023 | `5cd3b862d3612fa87322e439c271b5c4d2507316` |
| ctl 2024 | `924fafa6e1883ec9b54a8d418d518d4a0208926b` |
| ctl 2025 | `637f71d021fb46f32b0e8f9f49bde73108207722` |

All six are reachable from `main` (each shard branch merged), so **a promotion costs zero
re-solves** (rule 34(e)).

**The signature check that nearly condemned a clean leg.** A naive `scenario_config` diff of a
single-year leg against the three-year keeper reports differences that are not mechanism changes:
the span config snapshots its **first** year, and four `ScenarioConfig` fields did not exist when
NWPP-41 solved. `_nwpp42_leg_check.py` therefore **classifies** each delta instead of counting it —
`YEAR` (verified against the keeper's own `meta.json` `gas_prices` map), `NEW-FIELD-AT-DEFAULT`
(admitted only when the value equals the dataclass default **and** `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`
declares it dropped at that value), or `LIVE`. All six legs PASS: the arm legs show **exactly one**
LIVE delta (`measured_coal_heat_rates None → True`), the control legs **zero**. The 2023 leg
returns zero year-carried deltas, which is what confirms the classification is correct rather than
permissive.

The composer verified before writing that **all 855 non-year-carried `scenario_config` fields agree
across the three legs**, that the solve-surface fingerprint is shared, and that each leg's
`gas_price_override` matches its **own** `calibration_flags.gas_prices` entry.

---

## 5. NWPP's measurement of the rule-36 artifact

Rule 36(f) states the artifact's size is **unmeasured outside MISO**. This is NWPP's measurement,
from the control span against NWPP-41's committed bundle.

**The split is clean:**

- **Annual class volume is unchanged.** `ctl − keeper = 0.000 TWh` for **every class in every
  year**, coal included, and the footprint total likewise.
- **Hourly allocation moves materially.** max |Δ| **765.2 / 817.1 / 817.9 MW**, Σ|Δ|
  **1.516 / 0.915 / 0.698 TWh** in 2023 / 2024 / 2025, concentrated in **hydro and CC_REGULAR**
  (2023: hydro 690.3 GWh, CC_REGULAR 516.6 GWh, COAL_PRB 271.5 GWh) — the flexible resources whose
  monthly energy budgets bind the annual total while leaving within-year placement free.
- **On the scored criteria it is negligible.** The control reproduces the keeper's C4 coal `r` to
  0.001 (0.539 / 0.547 / 0.502 against 0.539 / 0.546 / 0.502), its NRMSE exactly, and its C2 2025
  coal row exactly.

**MISO measured up to 24.18 TWh of annual class movement; NWPP measures 0.000.** The two are not
comparable and neither generalises — each lane owes its own measurement, and NWPP's is now on the
record. Practically: **form 4 against the committed keeper is reliable for NWPP** on annual volume
and on every scored criterion, though not on raw hourly series.

A second, smaller finding from the same comparison: the **benchmark itself moved** between the
NWPP-41 registration and this one (the rebuilt `eia923` shared input hashes differently). The
control is what shows that movement to be immaterial — it reproduces NWPP-41's scored numbers on
the *new* benchmark.

---

## 6. The gates, arm minus the paired control

| criterion | control | arm | verdict |
|---|---|---|---|
| C1 fuel-mix | PASS (18/18 all, 14/14 free) | PASS (18/18, 14/14) | → PASS |
| C2 system volume | PASS | PASS | → PASS |
| C3a / C3b / C3c | UNSCORED | UNSCORED | price unscored (v3.8) |
| **C4 dispatch correlation** | **FAIL** | **FAIL** | → FAIL |
| C6 governance | PASS | PASS | → PASS |
| C8 forced-energy share | PASS (0.0 % forced) | PASS (0.0 % forced) | → PASS |
| **determination** | NOT-YET `{dispatch_corr}` | NOT-YET `{dispatch_corr}` | unchanged |

**C4 coal, the criterion this lane exists for** (floors: `r ≥ 0.70`, `NRMSE ≤ 0.30`):

| year | `r` ctl → arm | NRMSE ctl → arm |
|---|---|---|
| 2023 | 0.539 → **0.570** | 0.301 → **0.292** ✅ inside the gate |
| 2024 | 0.547 → **0.559** | 0.397 → **0.387** |
| 2025 | 0.502 → **0.524** | 0.432 → **0.408** |

2023 now fails on the **correlation floor alone**. C4 **gas passes all three years** in both legs
and is untouched.

**Coal volume (TWh):**

| year | keeper | control | arm | arm−ctl | CEMS actual |
|---|---|---|---|---|---|
| 2023 | 39.613 | 39.613 | **41.549** | **+1.936** | 42.27 |
| 2024 | 27.008 | 27.008 | **27.390** | **+0.382** | 38.30 |
| 2025 | 27.207 | 27.207 | **28.317** | **+1.110** | 42.26 |

C2's 2025 coal row improves −29.3 % → −26.4 % (SKIPPED on the preliminary EIA-923 vintage, so it
gated neither way). Reported-only C5a CO2 improves −16.0 / −23.8 / −21.5 % → −14.4 / −23.5 /
−20.6 %, changing no determination (rubric v2.9).

**Nothing outside coal moves except as displaced merit order.** Hydro is **exactly flat** in all
three years (monthly budgets bind); the footprint total moves 0.000 / −0.001 / −0.002 TWh. The
displaced classes are CC_REGULAR (−1.900 / −0.105 / −0.846 TWh), CT_PEAKER and ST_GAS — the arm's
intended effect, not reach.

---

## 7. Pre-registered predictions, scored honestly

| # | PRECOMMIT §6 prediction | outcome |
|---|---|---|
| 1 | Coal volume rises materially, does **not** close the gap | **HELD** (+1.936 / +0.382 / +1.110; deficit still 0.7 / 10.9 / 13.9 TWh) |
| 2 | `r` improves; **not** predicted to reach 0.70 | **HELD in both halves** |
| 3 | 2023 is the **risk year**, may push a C1 row out of band | **DID NOT HAPPEN** — C1 stays 18/18 despite 2023 carrying the largest move |
| 4 | Zero movement outside coal | **HELD as intended** (hydro exactly flat; total within 0.002 TWh) |
| 5 | DOF unchanged at 3/3 | **HELD** |

**The kill condition, named rather than glossed.** PRECOMMIT §6 pre-registered: *a 2025 coal move
below 0.5 TWh ⇒ verdict I (inert), not a keeper.* 2025 moved **+1.110 TWh**, so it did not fire.
**But 2024 moved only +0.382 TWh, which is below that line** — had 2024 been the pre-registered
kill year, this arm would have read inert. That is a real weakness in the evidence and it is
recorded on the keeper's own determination basis, not buried here.

---

## 8. What this does NOT close

1. **C4 coal still FAILs** in all three years — `r` 0.570 / 0.559 / 0.524 against a 0.70 floor. The
   named residual driver is unchanged from NWPP-41: the coal offer stack is **bimodal** (a must-run
   tranche in the money essentially every hour against a far dearer economic tranche), so most
   model coal is price-insensitive and **a uniform heat-rate correction cannot produce the measured
   diurnal amplitude** (measured peak/trough 1.183 / 1.237 / 1.311 against a model ≈1.02). The
   structural successor is **per-plant CAMPD binning**, blocked on `bin_assignments_NWPP.csv`.
2. **Coal volume is still materially short** — 2025 model 28.32 TWh against 42.26 actual.
3. **Energy balance −10.02 TWh in 2025** against a ±3.0 tol (the served-interchange construction
   NWPP-40 declared). Carried, not absorbed.
4. **Chief Joseph's pond-balance dual** sits at a constant −325.17 $/kcfs·h for 5,808 hours of 2025
   with pond = 0 and spill = 0. Untouched by this lane, still the first cascade-specific question
   for a successor.
5. **C5a CO2** remains a reported-only FAIL in all three years.
6. Every NWPP-40 / NWPP-41 disclosure is **inherited verbatim** into this attestation.

---

## 9. Cross-ISO, deliberately not fixed here

The **eGRID annual-average heat rate is the default for every legacy-bin ISO**, so the same defect
is present wherever `use_campd_bins` is inert. Rules 25 `[R-ISO-SCOPE]` / 28(d): **nothing is
transferred.** `measured_coal_heat_rates` is registered **U (untested)** in all eight other ISO
shards, and each target lane must derive its own table from its own market's CAMPD record.
NWPP-41's separate **pooled-PRB-proxy defect** also still reaches MISO (12 plants), PJM (2) and
SPP (3-5) and is likewise not this lane's to fix.

---

## 10. Housekeeping and one pre-existing RED that is not this lane's

- **Registered:** `2026-09-20-nwpp42-measured-coal-heat` (rule 15). **Promoted** (rules 35(a)-(f)):
  year union `{2023, 2024, 2025}` enumerated **before** the prune, covered in full by the incoming
  keeper; `audit_keepers.py --iso NWPP` PASS (0 failures, 0 warnings) between promotion and prune;
  `prune_iso_runs.py --iso NWPP` removed the outgoing keeper's three stores. NWPP has no held-out
  year registered, so rule 35(c) is satisfied without a stamped rung.
- **The control is NOT registered** (rule 29(c)) and is **gitignored, never deleted** (rule 31).
  Every number cited from it is in this document; it recomposes for free from the three `mer` legs
  with `_nwpp42_compose_span.py`.
- **`check_registry_payload_parity.py` is RED locally** on nine unmapped dirs. Eight are this
  lane's own gitignored bundles — the expected local RED rule 31's 2026-09-16 correction describes;
  **none is tracked, so CI stays green.** The ninth,
  **`results/calibration/caiso279_ablate_dswcouple_span`, has 34 TRACKED files and is a genuine
  pre-existing RED belonging to the CAISO lane** — not touched here (rule 25). *(The second
  pre-existing RED this lane inherited, `soco15_spp_arm`, has since been cleared by its own lane.)*
- **22 pre-existing failures in `tests/scoring`** on `main`, confirmed identical with this lane's
  changes stashed. Reported, not repaired — they belong to the golden-manifest / forecast-parity
  lanes.
- `tests/unit/data/test_measured_coal_heat_rates.py` passes.

---

## 11. Recommendation as delivered

**PROMOTE** — acted on under the owner's standing ruling (*"If structural integrity improves but
gates regress that may still be a keeper"*), which this run satisfies on its easier limb:
**structural integrity improves and no gate regresses.** An estimate known to be wrong at every
covered plant is replaced by the measurement of the same quantity, with zero free parameters added,
and rule 14 `[R-ACCURATE]` says the accurate input is kept whatever it does to the residual. That
the residual also moves the right way on every number is reported, not claimed as the reason.

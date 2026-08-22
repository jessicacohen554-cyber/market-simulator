# FINDING — ercot-227: every 2023 conservatism factor carried to a SOLVED verdict — the AS-sequestration channel is closed

**Session:** ercot-227 (hub) · **Branch:** `claude/ercot-2023-summer-scarcity-9lg3nm`
**Charter:** the owner dispatch of ercot-226 as EXTENDED 2026-08-22 — *"Proceed
with all the factors to test not just 1 keep going"* — recorded verbatim in
`docs/PRECOMMIT-ercot226-held-sequestration-2026-08-22.md` §5.11 (Amendment 3).
**Predecessor:** `docs/FINDING-ercot226-held-sequestration-2026-08-22.md`.

## 0. What the extension changed

ercot-226 closed with four factors killed at Phase 0 *on measurement alone*
(F1, F1b, F3, F4) and one built-and-rejected (F2). The owner's order converts
every Phase-0 kill from **probe-terminating** into **probe-informing**: a
measured prior may predict a null, but only a solve may declare one. Amendment
3 therefore re-opened each killed factor as a build-and-solve obligation, and
this FINDING records the result of discharging all of them.

The distinction is not ceremonial. A Phase-0 kill says *"the input we would
feed the mechanism is ~zero"*; a solved null says *"the mechanism is wired,
armed on the real config, and provably changes nothing"*. Only the second
retires a hypothesis, because only the second rules out the mechanism finding
leverage through a path the screen did not measure.

## 1. THE FACTOR TABLE — solved verdicts

| factor | object | how it was carried | verdict |
|---|---|---|---|
| **F1** held-depth, rigid products | `max(plan, held)` on ECRS/RRS/RegUp from NP3-965 telemetered responsibilities | field built (`ercot_as_held_requirement`), **solved 2023** vs hub control | **MEASURED-INERT** (§2) |
| **F1c** cleared-vs-plan | `max(plan, cleared)` from the 60-day DAM awards | **measured zero**; identical to F1's arm by construction, folded into that solve | **MEASURED-ZERO** (§2.3) |
| **F1b** held-depth, NSPIN | same, NSRS column, non-rigid family | field built (`ercot_as_held_requirement_nspin`), **solved 2023** | *(§3)* |
| **F2** held-location | measured per-class allocation of the rigid holds | built (class families + conserving credit), solved at ercot-226 | **REJECTED-AS-ARMED**, direction negative |
| **F3** RUC / out-of-market commitment | measured ONRUC instruction state × LSL, class grain | derive + mechanism built (`ercot_ruc_commitment_floor`, MECH id 23), **solved 2023** | *(§4)* |
| **F4** operator load-forecast conservatism | DA-forecast bias as a reserve-demand adder | fetch attempted across every ERCOT surface (ercot-228) | **DATA-ABSENT** (§5) |
| **F5** deployment-design depth | anything beyond rigid-at-VOLL | representation audited feature-by-feature | **ALREADY-CARRIED** |

Committed record: `results/calibration/ercot227_probe_f1.json`,
`ercot227_f1_gates.json`, `ercot227_ruc_sizing.json`,
`ercot228_probe_f4.json`, plus ercot-226's `ercot226_probe_f2.json` and
`ercot226_helddepth_phase0.json`.

## 2. F1 — the held-depth object does not exist

**Mechanism.** `ercot_as_held_requirement` replaces each rigid family's
requirement with `max(plan_p(t), held_p(t))` inside the product loop of
`_ercot_multiproduct_design`, before the family split, so the LR/storage
credit re-masking and the withheld-family width follow automatically.
Rigid-window-masked (ECRS through the 2024-08-01 reform hour, RRS/RegUp
through RTC+B); absent file ⇒ zeros ⇒ exact plan fallback.

**It engages, and it changes nothing.**

| measurement | control | F1 arm |
|---|---|---|
| official C3a 2023 | −39.7 % | **−39.7 %** |
| official C3b NRMSE | 0.729 | **0.729** |
| official C3c model tail > $200 | 74 h (of RT 181) | **74 h** |
| rigid-family duals | — | **max\|Δ\| = 0.0** |
| shortfall hour-sets (all families) | — | **exactly unchanged** |
| `class_hourly` / `adaptive` sidecars | — | **exactly 0.0 apart** |
| adaptive spike days | 7 | **7** |
| G-CAP / G-SPUR / G-SHED / G-BAT / G-D2 / G-SHORTFALL | — | **all PASS** |

`system.price` differs by 1.6e-13 and `storage.charge_mw` by 6.1e-05 — LP
re-solve floating-point noise. `reserve_family.held_mw` (≤336 MW over 24
family-hours) and `network.mw` (≤247 MW) move as degenerate re-allocation
*within* the optimal face: which capacity holds the reserve and how flow
splits, at an unchanged objective and unchanged duals.

**Why.** The mechanism raised a requirement in **2 distinct hours of 2023** —
h5875 and h6831 — by at most **8.33 MW**, a total of 18.7 MWh across 26,280
rigid family-hours.

| product | plan mean | RT held mean | hours held > plan | max held − plan |
|---|---|---|---|---|
| RegUp | 394.1 MW | 301.0 MW | 2 | +10.4 MW |
| RRS | 2,902.8 MW | 1,096.2 MW | 0 | −1,125.2 MW |
| ECRS | 1,081.6 MW | 324.6 MW | 0 | 0.0 MW |
| NSPIN | 3,348.7 MW | 756.8 MW | 15 | +5.6 MW |

### 2.3 F1c — the DAM never cleared above plan either

The second admissible reading of the same waiver category asks whether the
*cleared* DAM quantity ever exceeded the published plan. Measured against
`ercot_2023_as_up_mw.parquet`:

| product | plan mean | cleared mean | hours cleared > plan | hours cleared < plan |
|---|---|---|---|---|
| RegUp | 394.08 | 394.08 | **0** | 0 |
| ECRS | 1,081.61 | 1,081.61 | **0** | 0 |
| NSPIN | 3,348.66 | 3,348.66 | **0** | 0 |
| RRS | 2,902.75 | 1,821.95 | **0** | 8,760 |

RegUp, ECRS and NSPIN cleared **exactly** the plan in all 8,760 hours
(max\|Δ\| = 0.0); RRS cleared *below* plan in all 8,760 (even its least-short
hour is 422 MW under, the load-resource and FFR tranches being counted
outside the DAM award columns). So `max(plan, cleared) ≡ plan`, and F1c's arm
is identical to F1's by construction — measured, not assumed.

### 2.4 The reading

**ERCOT never held or procured materially more ancillary service than its own
published plan in 2023.** The keeper's plan-based requirement is *already* the
ceiling of the measured procurement conservatism — on the day-ahead award side
exactly, and on the real-time telemetered side with 2 hours and 8 MW to spare.
The held-depth hypothesis is not merely unhelpful; its object is absent.

## 4. F3 — the RUC object is real, 6.7× larger than believed, and unrepresentable at the only admissible grain

This is the factor Amendment 3 changed most. ercot-226 killed it at Phase 0 on
*"no 2023 RUC MW data on disk"*. That premise was wrong, and the extension
caught it: the NP3-965 60-Day SCED corpus carries a `Telemetered Resource
Status` column whose **ONRUC** rows *are* the RUC-instructed unit-hours, with
LSL and HSL alongside. Deriving rather than assuming produced a second
correction:

**The 2023 RUC object is 6.7× larger than the prior lane measured** —
**2,031 distinct ONRUC unit-hours over 96 days** (7,963 SCED rows), against
the 303 unit-hours the ercot97 plant-grain lane found on its 2024/25 subset.
By class: ST_GAS 6,632 rows / 35 units (mean LSL 49.4 MW), CC_REGULAR 1,148 /
26 units (mean LSL 126.2 MW), CT_PEAKER 183 / 9 units; COAL none. Sizing
record: `results/calibration/ercot227_ruc_sizing.json`.

### 4.1 The D-9 boundary it had to clear first

The quarantined `ct_deployment_overlay` / `reliability_deployment_overlay` pin
measured **energy** — a realized outcome, rule-13 forbidden. F3 feeds the
**instruction state at the physical LSL**: an operator input of the
outage-window class, which rule 13 names as its own admissible example family.
Never realized output, never a per-unit crosswalk. D-9 passes in the arm
exactly as in the control. Rule 19 is honoured by max-composition with
tie-keeps-incumbent attribution, so the gas bridge (CC) and the ST_GAS
net-load drag remain the owners wherever they already floor at least as high.

### 4.2 The mechanism is live — and it fails on placement

| witness | control | F3 arm |
|---|---|---|
| floor cells tagged MECH 23 | — | **229,598** (229,190 from unfloored, 408 taken from the ST_GAS drag) |
| total min-gen | 95.4549 TWh | 95.5246 TWh (**+0.0097 TWh** attributable to RUC) |
| D-2 forced budget | PASS | **PASS** |
| D-9 overlay quarantine | PASS | **PASS** |
| D-4 **window** leg | — | **PASS**, off-window share 0.0 (by construction, as declared) |
| D-4 **unit-conduct** leg | — | **FAIL — 23 of 42 rows** |

The unit-conduct failure carries **0.0082 of the 0.0087 TWh** the mechanism
floors — **94 % of its energy** — over **1,886 binding unit-hours** on units
whose measured CEMS generation is **zero in the majority of the hours the
floor binds** (`measured_median_mw` 0.0, `measured_zero_share` 0.55–1.00).
Worst offenders bind 382, 358, 299, 279 and 255 hours apiece.

### 4.3 The cause is the GRAIN, not the driver

The measured ONRUC instruction names ~2,031 **specific** unit-hours on ~70
**specific** units. Barred from the per-unit crosswalk (item 11 / Q-B FINAL),
the mechanism distributes the class MW **pro-rata across every unit in the
class**. It therefore reproduces the class MW total correctly while
attributing it to units the measured record says were **offline**.

That is rule 17 `[R-FLOOR-WINDOW]` by its own definition — *a floor binding in
hours its own driver evidence says the unit is not running is a bug, whatever
it does to the residual* — and the residual question does not even arise here,
because the benefit is nil independently:

- `d_price_at_miss` **p50 = max = 0.0**; `improved_miss_hours` **= 0**. The
  floor moves nothing at any of the 114 missed scarcity hours.
- Official scores print the keeper digits unchanged (−39.7 % / 0.729 / 74 h).
- The probe-basis C3a is **0.01 pp worse** (−29.99 → −30.00), model mean
  38.81 → 38.80.

**F3 is refuted at the level of representability, not of data.** ERCOT's
out-of-market commitment is an inherently per-unit instruction, and this model
cannot place it per-unit under the standing Q-B closure. The class-grain form
is the only admissible grain, and it provably mis-locates the instruction.

**DO-NOT-REDO:** the class-grain pro-rata form is adjudicated by a solved D-4
unit-conduct failure with 94 % of its energy mis-placed. The only route back
is a **grain** change, which is separately closed by item 11 / Q-B FINAL and
would need its own owner instrument. The derive and the 2023 series stay —
they are the sizing record that overturned the ercot97 premise.

## 5. F4 — operator load-forecast conservatism: DATA-ABSENT (terminal)

Carried by the ercot-228 spoke, which discharged the Amendment 3 obligation
to *attempt the fetch at execution* rather than infer absence. The attempt log
(`results/calibration/ercot228_probe_f4.json`, `phase_a_attempt_log`) records
every ERCOT surface tried:

- **MIS report archive** (NP3-560-CD / NP3-561-CD, reportTypeIds 12311/12312):
  HTTP 302 into the SiteMinder market-participant **client-certificate wall**;
  the cert endpoint fails the TLS handshake without a participant certificate.
  The same wall `fetch_ercot_as_reports.py` re-verified 2026-07-10.
- **Public doc lists** for both report types: HTTP 200, 346 documents, but a
  **7-day rolling window** whose right edge always tracks *now*
  (2026-08-15 .. 2026-08-22). 2023 can never re-enter it.
- **ERCOT's own EMIL catalog**: `misDisplayDuration_i = 7` for both products —
  the 7-day retention is ERCOT's advertised design, not an outage.
- The one archive that does carry 2023 vintages — the credentialed Public Data
  API — requires the `data.ercot.com` subscription key the owner **permanently
  declined to procure** (2026-07-05, `ercot-as-coopt-plan-2026-07.md` §WS-E).

**DATA-ABSENT is the honest terminal verdict**: no curation, no precommit, no
mechanism build, no solve. The re-open route is recorded and does not require
reversing the key decision — the WS-E HSL precedent (the owner manually pulling
the 2023 NP3-560/561 archive through the Data Access Portal's *Search History*
UI) is already-authorized and would let Phases B–C execute as precommitted.

Note the standing prior survives regardless: ercot-216 §5 measured reality's
own ORDC at ≈ $1 with no window at the missed hours, and the precommit §1
channel doctrine binds — an ORDC-requirement mechanism carrying its
improvement through the model adder rather than through λ would fail adoption
even with the data in hand.

## 6. F5 — deployment-design depth: ALREADY-CARRIED

Audited feature-by-feature against the armed 2023 representation; every item
is already in the keeper:

- ECRS_withheld as a single full-width VOLL step; RRS/RegUp rigid through
  RTC+B — the maximal pre-reform no-release form, not an approximation of it.
- The LR-RRS (RRS-UFR) measured series: armed.
- Storage per-product AS awards with SOC-reserve backing: armed and
  measured-credited (telemetered/award means regup 205/269, rrs 882/844,
  ecrs 127/120, nonspin 16/15 MW). `ercot_storage_as_duration_gate` being
  default-off is *inert for the requirement side* precisely because storage AS
  enters as a measured credit rather than an endogenous offer — verified, not
  assumed.
- Online-NSPIN depth: routed to F1b rather than left implicit.
- The OBDRR048 floor date gate: armed.

There is no buildable delta here, which is why F5 is a measurement row and not
a probe.

# PREREG miso-208 — FIND THE 8–11 GW: what MISO's real summer-2025 afternoons did not have that the model does, measured per candidate, per population, zero-solve (2026-09-04)

**Session:** miso-208, branch `claude/miso-208-backcast-calibration-bbtzvb` off
`origin/main` `26c67788`. **Keeper at open: `2026-09-03-miso-202-unitclip`**
(bundle `results/calibration/miso202_unitclip_B`) — determination **NOT-YET**
on `{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested.

**This is a ZERO-SOLVE phase 0.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only;
MISO holds no `complete`/`final` marker; the locked-test freeze is active.
Committed artifacts + production loaders only. **Pushed BEFORE any statistic in
§3 is computed.** Every input in §1 is a prior session's committed record.

---

## 0. What the record check turned up before anything was measured

* **The miso-207 FINDING and its calibration-log entry never reached `main`.**
  PR #4678 merged only `_miso207_bound_the_shoulder.json` (+ the probe and the
  PREREG at `e5f179d8`); the branch was deleted afterwards. The charter's "read
  first" document does not exist. This session works from the JSON record, the
  PREREG and the charter's own headlines, and **writes the missing log entry as
  part of its own** (the numbers below marked *m207* are read from that JSON).
* **Rule 28(a).** Every candidate family touched here already carries a cell in
  MISO's shard: `campd_outage_windows` **K** with miso-195's remove-only cap
  **R** inside it; `temp_dependent_derate` **K** (cogen scope), merchant scope
  refused at miso-139/203; `m2m_seam_entitlement_cap` **G** (miso-176);
  `miso_seam_coincident_envelope` **R**; `miso_south_firm_export_block` **G**;
  `ordc_scarcity_overlay` **G**; `maxgen_emergency_tier_pricing` **K** (miso-70,
  ARMED in the keeper — 2025's Jun 23 Step-1 / Jun 24 Warning / Jul 29 Warning
  windows already reprice the load slack to the $500 Tier-1 floor);
  `unit_outage_maxgen_events` **K** (armed); `measured_ramp_capability` **U**.
  **No cell is re-tested.** This session is a quantity-identification hunt: it
  measures, from MEASURED sources, where the model's surplus supply sits
  relative to what MISO actually ran, and whether any admissible (rule 13)
  cause reaches ≥ 25 % of the gap in BOTH populations.

---

## 1. Inputs (read, not re-derived)

* **Object** (*m207*, 2025, INDIANA.HUB RT, model clock): SHOULDER = Jun–Jul
  hours ranked [p75, p99) by actual RT → **351 h**, 52 days, h10–h20; actual
  $90.82 (DA $83.36) vs model lw $47.09, gap **−43.73**, DA-foreseen 83 %.
  TAIL = ≥ p99 → **15 h**, actual $329.5 vs model $63.5 (miso-205 stamps).
  Setter CT_PEAKER econ in both (57 / 48 %); price − setter mc $0.59 / $2.73.
* **Cushion** (*m207* `setter_and_cushion`): SHOULDER idle within $20 of the
  zonal price **10.85 GW** mean (CT_PEAKER 6.56, ST_GAS 2.47, CC_REGULAR 1.05,
  COAL 0.31); within $50 12.9; within $100 14.3. TAIL: 3.18 / 4.46 / 5.58 GW.
* **Margins** (*m207*, corrected — never miso-203's): SHOULDER thermal avail
  83.1 GW, dispatch 66.8, requirement 6.8, broad margin **+9.48 GW mean /
  −5.16 min**, armed-class idle 12.3; TAIL avail 81.6, dispatch 74.5, broad
  margin **+0.14 mean / −5.22 min**, armed idle 5.5.
* **Supply response on the corrected stack** (charter): tail −3.7 GW → +$91,
  −5.1 GW → +$143 (22 % of the tail gap); shoulder ≈ 11 GW per $20.
* **Absorption arithmetic, inherited on its own terms:** miso-195 W4 measured
  the top-200 net-load set (not the shoulder): median removal 6.65 GW against
  median idle thermal 18.3 GW (leg A: 0 converting hours) and 10.95 GW idle
  CT_PEAKER+ST_GAS (leg B: 31/183 = 16.9 % vs the 25 % line); W6: 6 cap-caused
  feasibility-violation days in 2025 (Jun 23/24, Jul 23/28/29/30). miso-194 W4:
  1,219 MW cold-excess vs 12,861 MW headroom, 1.2 % converting.
* **Measured sources** (rule 13 — each a physical/market quantity with a
  forward analogue, entering as a diagnostic only):
  1. MISO MOM `OUTAGE` record, daily, by region × cause
     (`data/raw/miso-generation-outages/miso_outages_estimated_<y>.csv`,
     loader `miso_outages.miso_outage_mw_series`; UNPLANNED = Derated + Forced
     + Unplanned, miso-195's frozen basis). Forward analogue: the statistical
     outage stack.
  2. CAMPD unit-hourly gross load, 14 MISO states (`campd.load_campd_hourly`,
     `plant_hourly_net` with the parasitic factors; plants → model group via
     `derive_thermal_tranches._fleet_nameplate_and_group("MISO")` — the
     miso-197/198 WP-3 construction). Forward analogue: class conduct
     parameters (committed shares, online fractions).
  3. EIA-930 MISO by fuel (`MISO_fueltype.parquet`: COL NG NUC WND SUN WAT OTH
     BAT) and D / TI (`MISO_region.parquet`), UTC → model clock.
  4. M2M settlement (`M2M_Settlement_srw_2025.csv.gz`, HE EST) and the RDT /
     sub-regional PBC RT binding record (`miso_pbc_rt_2025.csv.gz`, 5-min EST).
  5. INDIANA.HUB published MEC / MCC / MLC (`lmp-data/MISO/miso_hub_lmp_2025_rt.csv.gz`).
  6. The declared-window registry on the model clock
     (`maxgen_events.load_maxgen_registry_model_clock("MISO")`; MISO model
     clock = `Etc/GMT+5`, EST year-round).
* **Fleet/offer instrument:** `_miso134.build_year`, BUNDLE re-pointed to the
  keeper, `weather_year` pinned, `mode="backcast"`; `mc_base` = P0 base cost
  (every "idle within $X" reads LOW by at most the P1 startup markup); the chain
  passes `[]` for retirees/imports — T-6 asserted per population (2023 shoulder
  is known to fail on the retiree channel, 6 % of coal cap — reported).

---

## 2. Reproduction and key pre-conditions (any failure stops the session)

* **N-1** the populations reproduce *m207*: 2025 threshold 373.02, 15 / 351
  hours, 52 shoulder days; the shoulder gap −43.73 ± 0.01; cushion within $20
  10.85 ± 0.01 GW (same instrument, same code path).
* **N-5** the armed outage envelope reproduces miso-195: 2025 annual-mean M
  **36.82 GW** and P_U **28.06 GW** to ± 0.15 GW (the fleet population is
  miso-195's `_THERMAL_GROUPS`; a larger miss means the instruments differ and
  item 1 is reported on BOTH bases).
* **V-KEY-930** the EIA-930 clock is verified, not assumed: the keeper's own
  demand vs EIA-930 D over Jun–Jul under shifts −2..+2 h; the winning shift is
  used for every 930 series and REPORTED. Pre-committed expectation: shift 0
  under `period − 5 h` (EST). A winner ≠ 0 is disclosed, not hidden.
* **V-KEY-LMP** the components file vs the committed zonal `rt`
  (INDIANA.HUB) under shifts −2..+2: the winning shift must reproduce the
  zonal series to r ≥ 0.999; MCC/MLC are then read at that shift.
* **V-KEY-M2M** the settlement file's hour-ending EST clock is miso-176's
  verified convention (shift 0 on the NERC-ID join, r = 0.9934) — inherited,
  applied as `HE − 1` hour-beginning on the EST model clock.
* **R-1 (G-D repair)** BEFORE repairing miso-203's block, its DEFECTIVE numbers
  are reproduced from its own hour set and capability construction
  (`idle_reserve_eligible_mw_mean_scarce` 44,263.3 / 53,757.6 / 54,104.6 to
  ± 5 MW); only then is the pooled coal dispatch subtracted.

---

## 3. Predictions and decision rules — each against its own population

"Gap" = model lw − actual RT (INDIANA.HUB), mean over the population; "lift" =
the price rise from removing X MW per hour up the keeper's OWN idle census
(*m207*'s `_seam_reprice`, generalized to a per-hour X); "share" = lift / |gap|.
**Licensing line, frozen: a candidate is chartered only if its measured,
forward-analogue MW yields share ≥ 0.25 in BOTH the shoulder and the tail.**
Anything under 25 % in either population is refused as a lever (it may still
be NAMED as identification).

### Item 0 — the supply-mix map (identification, never a lever)

Per population, model class dispatch (keeper `class_hourly`, coal pooled)
minus the measured fuel-type output (EIA-930) and, within gas, the CAMPD
prime-mover split by model group (matched plants only, coverage reported).

| # | prediction, 2025 SHOULDER (model − actual) | conf. | rule |
|---|---|---:|---|
| P0a | demand: model within ± 3 % of EIA-930 D | 0.7 | a miss > 3 % re-opens the load object (miso-205), not this one |
| P0b | **coal: model ABOVE actual by +2 to +6 GW** | 0.6 | mechanism rule: ≥ +4 GW ⇒ the object is (at least half) a **coal-availability** object at the class grain — the record's July peak (31.7 vs the armed 24.5 GW) lives here |
| P0c | **gas total: model BELOW actual by ≥ 2 GW** | 0.65 | the real market ran deeper into gas than the model — consistent with a hole upstream, inconsistent with a gas-offer object |
| P0d | net import: model ABOVE actual by +1 to +3 GW | 0.6 | the seam lane is closed (R/G); reported as identification only |
| P0e | wind: model = 1.05 × actual (± 0.01); solar: model = actual (± 100 MW) | 0.95 | identity checks (miso-206) |
| P0f | nuclear + hydro: within ± 1 GW combined | 0.7 | — |
| P0g | **model-excess supply** Σ_classes max(0, model − actual) over {coal, CC, ST_GAS, CHP, import, nuclear, hydro, other}: **4–9 GW** shoulder, **5–11 GW** tail | 0.55 | THE identification: if this lands inside the charter's 8–11 GW in the tail and ≥ 4 GW in the shoulder, the "8–11 GW" is a class-mix object and the map names its rows |
| P0h | the excess re-priced up the idle census: share **0.20–0.45** shoulder, **≥ 0.25** tail | 0.5 | this is what a complete, admissible cause would yield; every candidate below is measured against it |
| P0i | CAMPD split: actual **CT_PEAKER ABOVE model** by ≥ 1.5 GW; **CC_REGULAR model ABOVE actual** by ≥ 1 GW (miso-197's over-dispatch); ST_GAS model above actual | 0.6 / 0.55 / 0.5 | signs pre-committed; the CT row decides item 2 |

**Signs, tail vs shoulder:** every model − actual sign above holds in the tail
with larger magnitude (0.7). 2024 same signs, ~½ magnitude; 2023 coal sign may
flip (the over-priced year) — reported.

### Item 1 — the published unplanned-outage record, on the shoulder

| # | prediction (2025) | conf. | rule |
|---|---|---:|---|
| P1a | shoulder-day mean **P_U − M = +4 to +8 GW** (record above the armed envelope); tail days +5 to +9 | 0.65 | sign POSITIVE both populations (the July minimum inversion, miso-195 §2) |
| P1b | the record's **Central** region carries ≥ 50 % of shoulder-day unplanned MW | 0.6 | Central is where INDIANA.HUB sits |
| P1c | conversion in the shoulder: leg A (deficit > total idle thermal) ≤ 10 % of hours; leg B′ (deficit > idle within $20) 10–30 % | 0.6 | miso-195's 25 % line, read in the shoulder — a level congruence, NEVER a cap |
| P1d | lift share: shoulder **0.10–0.25**, tail **0.15–0.30** | 0.6 | REFUSE as a lever at < 0.25 in either; the cell stays R and the lane closed on its own W6 feasibility |
| P1e | W6 on the 52 shoulder days: ≥ 3 cap-caused violation days | 0.7 | the same fuel-identity defect that killed the cap (Jul 28: 4.6 GW of non-population MW) |

**Mechanism rule.** Item 1 cannot be chartered in any form the record can
carry (no fuel identity, daily grain, feasibility-violating); what it CAN do is
corroborate item 0's coal row: if P0b ≥ +4 GW AND P1a ≥ +4 GW on the same
days, the record and the class map agree that the model's coal fleet is
~4+ GW more available than MISO's was — an availability object whose
admissible successor form is a **fuel-identified, per-unit partial-derate
measurement** (CAMPD gross-load-below-capability windows — `unit_partial_outage_windows`,
default OFF in the keeper, forward analogue = derate rates), NOT the MOM cap.
That successor is NAMED here, checked against the shard before any charter,
and NOT built in this session.

### Item 2 — CT_PEAKER availability conduct

| # | prediction (2025) | conf. | rule |
|---|---|---:|---|
| P2a | matched-CAMPD CT_PEAKER nameplate ≥ 60 % of the model class capacity | 0.7 | coverage stated on every number |
| P2b | actual CT online share (MW-weighted, matched) in the shoulder **0.35–0.60**; model CT dispatch / capability **0.20–0.40**; **actual > model by ≥ 1.5 GW** | 0.6 | mechanism rule: if actual CT ≥ model CT + 1.5 GW the real CT fleet was RUNNING while the model's sat idle-but-cheap → the 6.6 GW CT cushion is **not a CT-availability object**; the hole is upstream (item 0's coal / CC / import rows). If actual CT ≤ model CT − 1 GW → a CT unavailability object (charter a measured CT availability check). Otherwise inert. |
| P2c | tail: actual CT ≥ model CT + 2 GW | 0.6 | same rule |

### Item 3 — deliverability to the pocket that sets INDIANA.HUB

| # | prediction (2025) | conf. | rule |
|---|---|---:|---|
| P3a | INDIANA.HUB **MCC** mean in the shoulder between −$5 and +$8; \|MCC\| ≤ 15 % of the gap; MLC ≤ $3; tail MCC ≤ 20 % of its gap | 0.7 | **identity rule: if the hub's congestion component is under 15 % of the gap, the shoulder is a SYSTEM-ENERGY object and deliverability to the pocket is refused by the price identity** (miso-206 §8.2: 88 % energy) |
| P3b | M2M: Σ MISO shadow in shoulder hours ≤ 1.5 × the other Jun–Jul daytime hours; binding-flowgate count ratio ≤ 1.5 | 0.6 | non-discriminating |
| P3c | RDT (South→North) RT-binding in ≤ 20 % of shoulder hours; ≤ 5 of 15 tail hours | 0.6 | — |
| P3d | MISO-South holds **20–40 %** of the within-$20 cushion; the model's zone-price spread (max − min over carry zones) in the shoulder ≤ $5 mean | 0.6 | the LP sees no congestion there |
| P3e | stranding the South cushion in RDT-binding hours: share ≤ 0.10 both populations | 0.75 | REFUSE; `m2m_seam_entitlement_cap` G untouched |

### Item 4 — declared-emergency conduct

| # | prediction (2025) | conf. | rule |
|---|---|---:|---|
| P4a | shoulder hours inside ANY declared window (advisory+): **15–35 %** of 351; inside Warning+ (tier-priced): ≤ 15 % | 0.6 | — |
| P4b | in-window hours carry **25–50 %** of the shoulder gap; the out-of-window shoulder (≥ 65 % of hours) has actual mean ≥ $70 | 0.5 / 0.6 | **decision: if out-of-window hours carry ≥ 50 % of the shoulder gap, the shoulder is NOT an emergency-declaration regime** — the in-window part is the ordc G's cousin (named, not built), the rest is the quantity object |
| P4c | tail: ≥ 8 of 15 hours inside a declared window | 0.6 | the tail IS event-coincident (Jun 23/24, Jul 28/29) |
| P4d | the keeper's armed tier floor does NOT print in any 2025 Warning+/Step-1 window hour (slack = 0, model price < $500 everywhere) | 0.85 | rule 17: the armed mechanism has its window and its driver; it does not bind because the LP has supply — the SAME 8–11 GW |

### Verdict

| # | prediction | conf. |
|---|---|---:|
| P9 | **No candidate reaches 0.25 in BOTH populations; nothing chartered; no solve.** Items 1/3/4 refused on their own rules; item 2 resolves to "not a CT object"; item 0 NAMES the class rows carrying the excess and the admissible successor form (per-unit partial derates) for the coal row | 0.75 |
| P10 | the excess identified by item 0 in the tail lands in **5–11 GW**, i.e. the charter's "8–11 GW of idle within $20" is the SAME quantity seen from the supply side | 0.55 |

**Signs against own populations, pre-committed:** coal excess POSITIVE, gas
deficit NEGATIVE, import excess POSITIVE, outage deficit POSITIVE — in both
populations, all three years for 2024/2025; MCC small both populations; tier
floor silent.

---

## 4. Re-scored inherited headlines (each a claim that may FAIL)

| # | headline | source | test |
|---|---|---|---|
| H1 | "the model's supply is 8–11 GW idle within $20 in the shoulder" | *m207* 10.85 GW | reproduced at N-1 AND matched against item 0's supply-side excess (P10) — a supply-side excess < 4 GW in the tail FAILS the "quantity object" reading |
| H2 | "the shoulder is DA-foreseen (83 %)" | *m207* | re-read on the DA-defined shoulder overlap (217/352) — reported |
| H3 | "reserves inert in Jun–Jul" (miso-153 D-4) | *m207* 6 regspin bind hours in the shoulder | counted against the declared-window hours: if the binding hours sit INSIDE windows the tier floor is the binder, not reserves |
| H4 | "the tail is an energy object (88 %)" (miso-204/206) | components | re-measured on the SHOULDER (P3a) — the tail claim is not assumed to transfer |
| H5 | "W6: 6 violation days" (miso-195) | record | re-derived on the shoulder days from the same construction (P1e) |
| H6 | "CT_PEAKER sets 57 % of shoulder zone-hours" (*m207*) | census | confronted with the measured CT conduct (P2b): a setter that reality was RUNNING is a stack-depth statement, not a CT statement |

---

## 5. Traps

| trap | counter-measurement |
|---|---|
| T1 the 930 clock | V-KEY-930 under shifts; the BALANCE EST-label defect (miso-206) is why the fuel-type file is keyed on its UTC `period`, never a local label |
| T2 CAMPD coverage | matched nameplate / class capacity per class; unmatched share stated; the class comparison is a class TOTAL vs matched plants — a lower bound on actual |
| T3 daily record vs hourly object | the MOM record is a daily total broadcast to hours (miso-195's own `_daily_to_hours`); the deficit on a shoulder HOUR is the day's — stated |
| T4 P0 base cost | every lift reads LOW by ≤ the P1 startup markup; reported as a lower bound |
| T5 a lever argued on the mean | shoulder bands (p75–90 / p90–95 / p95–99) reported for item 0's excess and every lift |
| T6 aggregate agreement ≠ hour-set correctness | every quantity per population, hour-matched |
| T7 the tier floor "silent" because no slack, not because no window | report slack, model price and demand-minus-capability inside each 2025 window |
| T8 leap year 2024 | `_hour_month` fixed clock; the 930 file dropped at Feb 29 |
| T9 the G-D repair moves the WRONG number | R-1 reproduces the defective block first; the repaired block keeps miso-203's OWN hour set and capability (not *m207*'s) so exactly one thing changes |

---

## 6. Stop rule

No lever is chartered and no LP is spent unless an item's measured,
forward-analogue reach is ≥ 0.25 in BOTH populations under §3's lift engine AND
its family is not R/I/G — in which case the outcome is a re-charter with a
rule-28(a) argument, still no solve this session. If nothing reaches, the
FINDING says so, names the class rows and the admissible successor form, and
the queue is re-ordered accordingly.

**Rule duties.** Rule 15: zero-solve, nothing registered. Rule 28(b): evidence
appended in MISO's shard to `campd_outage_windows` (shoulder-day congruence),
`temp_dependent_derate` (the repaired G-D margins), `m2m_seam_entitlement_cap`
(shoulder MCC / RDT), `maxgen_emergency_tier_pricing` (window census, tier
silence); no verdict moves; §5.4 stamp. Rule 28(c): no field. Rule 25: MISO's
files only. Rule 27: blob-verify after push. Second deliverable: miso-203's G-D
block repaired under the miso-206 record-repair pattern (`pre_repair` kept).

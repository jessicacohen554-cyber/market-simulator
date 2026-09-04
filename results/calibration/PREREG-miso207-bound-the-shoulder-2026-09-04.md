# PREREG miso-207 — BOUND THE SHOULDER: every live lever re-bounded against the p75–p99 population AND the 15-hour tail, zero-solve (2026-09-04)

**Session:** miso-207, branch `claude/miso-wind-availability-backcast-yr4i67`
(rebased onto `origin/main` `4b24ad3c`; the only `src/` drift since the keeper
is nyiso-184's default-off eGRID heat-rate field — no MISO effect).
**Keeper at open: `2026-09-03-miso-202-unitclip`** (bundle
`results/calibration/miso202_unitclip_B`) — determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone, C3c the single ledgered caveat, C6 attested.

**This is a ZERO-SOLVE phase 0.** Rule 22 `[R-HOLDOUT]` — 2023/2024/2025 only;
MISO holds no `complete`/`final` marker and the locked-test freeze is active.
Committed artifacts + the production fleet chain only. **Pushed BEFORE any
statistic on the shoulder population is computed.** No number in §3–§5 has been
measured; §1's inputs are prior sessions' committed records.

---

## 0. What the matrix check turned up BEFORE anything was measured (rule 28(a))

Two of the charter's four items carry a status the charter inherited stale:

* **Item 1, the D-2 5(i) seam object.** The owner's 5(i) ruling was NOT
  outstanding: it was GRANTED and EXERCISED at **miso-181**, and the chartered
  form (`miso_seam_coincident_envelope`) was REFUTED at its own pre-registered
  conditioning-sanity kill — cell **R**, "the D-2 lane closes end to end"; the
  lane fell back to D-3, which **miso-182** refused on data
  (`miso_south_firm_export_block` **G**). What miso-202/205/206 carried forward as
  "+3,673 MW, ruling outstanding" is a descriptive statistic of a CLOSED lane.
  This session measures the import excess in the shoulder as charged, and
  states it as evidence about a closed lane, not as a candidate.
* **Item 3, the overnight side.** miso-130 §6 named two successors; BOTH are
  already adjudicated: (a) synchronized-reserve online gating is **K**
  (`miso_reserve_online_gated`, miso-169/171, armed in the keeper);
  (b) the CC committed re-grounding is DONE in the keeper
  (`offer_curve_by_group.CC_REGULAR.committed = 1.005 = phys_committed`).
  The coal-side night levers are adjudicated: `miso_coal_night_floor` **I**
  (miso-113), `coal_prb_committed_dispatchable` **R** (miso-111),
  `coal_prb_committed_split` **R** (miso-112), `import_shape_lever` **G**
  (miso-123). `miso_cc_coal_rebalance` is a registered default-off field armed in
  zero MISO bundles, refused four times in the log for lack of a measured
  identification.
* **Item 2.** `measured_offer_surface` R (miso-151), `miso_offer_level_dispersion`
  R (miso-179: the model already carries 0.541× the book's across-unit spread and
  sits +$15 OVER the book at the median rank; the durable residual is a
  TOP-DECILE tail steepening), `miso_offer_spread_anchored` I (miso-180: the
  graft landed exactly and moved +0.13 pp). The commitment-floor family is
  closed by arithmetic (miso-199 §6: no floor at any level/window/membership
  closes the gap without pinning).
* **Item 4.** `measured_ramp_capability` U with three standing objections;
  `ramp_envelopes` I (miso-156: the model under-ramps reality at every quantile).

**No cell adjudicated R/I/G is re-tested here.** The deliverable is a bound per
item on the two populations, and an explicit rule-28(a) statement per family.

---

## 1. Inputs (read, not re-derived)

* Object: `actual_lmp_hourly_zonal_MISO.parquet`, hub `INDIANA.HUB`, cols `rt`
  AND `da`, on the model's fixed-CST non-leap 8760 (`_hour_month` construction).
* **Populations, per year, over Jun–Jul (1,464 h) ranked by actual RT:**
  **SHOULDER** = [p75, p99) → 351 h; **TAIL** = ≥ p99 → 15 h; **BODY-LOW** =
  < p50 → 732 h (the over-priced half); **NIGHT** = BODY-LOW ∩ h00–h05.
* Model: keeper `hourly/system_<year>.parquet` (P1; zone price, demand, slack),
  `class_hourly`, `reserve_family`, `storage`. Model price reported BOTH
  load-weighted (C3a's basis) and zone-mean.
* Fleet and offers: the production chain at HEAD through
  `scripts/probes/_miso134_ct_night_order_screen.build_year`, BUNDLE re-pointed to
  `miso202_unitclip_B`, `weather_year` pinned to the solve year (the miso-153 T-6
  repair). **Instrument caveats, stated up front:** (i) `mc_base` is the P0 base
  cost — the P1 startup markup is absent, so every "price − setter mc" reads HIGH
  and every "idle within $X" reads LOW by at most that markup; (ii) the chain
  passes `[]` for retiree-channel units and import generators (miso-134's
  construction), so the availability matrix is the operable fleet only; the
  T-6 feasibility gate (class dispatch ≤ assembled availability, per class,
  per hour of each population) is asserted and any violation is reported as
  the instrument's blind spot, not hidden.
* Margins for the tail: miso-203 G-D (30,533 MW broad, 5,621 MW armed idle, 2025).
  The shoulder's own margins are MEASURED here for the first time.

---

## 2. Reproduction PRE-CONDITIONS (any failure stops the session)

* **N-1** the TAIL set reproduces miso-205's 15 stamps and thresholds
  121.43 / 159.01 / 373.02.
* **N-2** the shoulder+tail+body-low band contributions reproduce
  `_miso202_c3a_2025_anatomy.json::a2b` (INDIANA lw 2025: +3.71 / −0.15 / −2.23 /
  −2.65 / −5.83 / −6.30, mean gap −13.44) to ±0.01.
* **N-3** T-6 feasibility: ≤ 1 % of (class × hour) cells in each population
  with dispatch > availability + 1e-6, and no violation > 2 % of class cap.
* **N-4** the top-200-demand setter census reproduces miso-153's headline to
  ±5 pp (CT_PEAKER 66.0 % in 2025) — the miso-153 instrument re-run on this
  keeper is the bridge between the two sessions' numbers.

---

## 3. Predictions and decision rules — each against its own population

"Gap" = model_lw − actual RT (INDIANA.HUB), $/MWh, mean over the population.

| # | prediction (2025 unless stated) | conf. | decision rule |
|---|---|---:|---|
| **P1 shoulder anatomy** | shoulder mean gap between **−35 and −55 $/MWh** (actual mean $95–120 vs model $50–60); the shoulder's DA-FORESEEN share `(model→DA)/(model→RT)` ≥ **0.60** (the deterministic-reachable half, miso-178 §3's "−11.7 pp in the body" re-scored on the C3a comparator) | 0.75 | reported; the DA share decides whether the shoulder is a deterministic-LP object at all (< 0.40 ⇒ the shoulder is RT-only class like the ordc G) |
| **P2 the shoulder's marginal unit** | setter census, carry-zone-hours: **CT_PEAKER ≥ 45 %** (econ sub-band), COAL family ≤ 25 %, CC_REGULAR ≤ 15 %; `price − setter mc` mean **< $5**; the actual RT exceeds the model's DEAREST in-merit mc by > $20 in ≥ 70 % of shoulder hours | 0.7 | mechanism rule: the shoulder is a **merit-ORDER** object only if the setter census differs from the tail's by ≥ 20 pp in the leading class; else it is the SAME stack at a different depth (a quantity/conduct object) |
| **P3 the shoulder cushion (THE BOUND)** | idle capability priced within **$20** above the zonal price: **≥ 4 GW** mean over the shoulder; within $50: ≥ 8 GW; broad reserve margin (Σ avail − Σ dispatch − requirement) **≥ 20 GW** mean, min ≥ 12 GW; armed-class (CT_PEAKER+CC_REGULAR) idle ≥ 6 GW | 0.7 | **licensing line, verbatim miso-203:** a supply-removal lever reaches the shoulder only if it removes ≥ 25 % of the broad margin THERE; a price-raising lever must move the dearest in-merit mc by ≥ the median shoulder gap |
| **P4 item 1, the seam in the shoulder** | import-class excess vs other Jun–Jul hours: **+1,200 to +2,400 MW** (smaller than the tail's +3,673; sign positive, all three years); re-priced up the shoulder's own idle census, removing ALL of it lifts the shoulder mean by **< $8/MWh** (< 20 % of the shoulder gap) | 0.7 | REFUSE-as-lever if lift < 25 % of the shoulder gap; the lane is R/G regardless (§0) — reported as evidence, nothing raised for a build |
| **P5 item 3, the night side** | NIGHT gap **+6 to +10** (model above actual, all three years); setter census: **COAL family ≥ 50 %** of night zone-hours, CC_REGULAR ≥ 15 %; model in-merit supply at the ACTUAL night price falls short of demand by **2–6 GW** (the miso-130 §4 "overnight supply hole", re-measured on the comparator) | 0.7 | mechanism rule: the night over-price is a SUPPLY-QUANTITY object (hole ≥ 2 GW) rather than a coal-offer-LEVEL object (hole < 1 GW and setter mc within $3 of actual) |
| **P6 item 4, ramp** | shoulder 3-h net-load ramp vs the other Jun–Jul DAYTIME (h10–h20) hours: ratio in **[0.8, 1.3]** (non-discriminating); reserve duals > $0.01 in **≤ 3** of 351 shoulder hours, ≤ 3 of 15 tail hours (any family) | 0.8 | REFUSE the ramp product if ratio < 1.5 AND binding hours ≤ 10 — the fourth objection stands with the three |
| **P7 the tail, re-bounded on the same instrument** | tail setter CT_PEAKER ≥ 60 %; idle within $20: ≥ 2 GW; within $50: ≥ 5 GW; the actual exceeds the model's dearest AVAILABLE tranche (CT_PEAKER peak, ~4× base) in ≥ 10 of 15 hours | 0.7 | states, in MW and $, what any tail lever must do: exhaust ≥ X GW of priced idle capability |
| **P8 re-scored inherited headlines (each may FAIL)** | (a) miso-153 "CT_PEAKER sets 66 %" holds at top-200 demand (N-4) AND in the shoulder (P2); (b) miso-178 "body deterministic-reachable" holds (P1 DA share ≥ 0.6); (c) miso-153 D-4 "reserves inert in Jun–Jul": ≤ 15 Jun–Jul hours with any family dual > $0.01 in 2025 (miso-202 A-3 found 12 regspin hours on miso-201); (d) miso-174 "seam reach $3.3–7.7 in scarce hours" ≤ $10 on the tail's idle census | 0.6 each | each scored RIGHT/WRONG in the FINDING |
| **P9 verdict** | **NOTHING reaches the shoulder at ≥ 25 % of its gap; no lever chartered; no solve.** Items 1 (closed lane) and 4 refused; item 2 stays R/I/G with an explicit 28(a) statement; item 3 named as a supply-quantity object whose named components are all adjudicated | 0.85 | §5 stop rule |

**Signs against own populations, pre-committed:** shoulder gap NEGATIVE (model
low) in 2024/2025, ≈ 0 in 2023; night gap POSITIVE all years; seam excess
POSITIVE in both populations all years; DA share of the shoulder gap POSITIVE and
majority.

---

## 4. Traps

| trap | counter-measurement |
|---|---|
| T1 instrument mc is P0 base | report the P1 startup markup's size from the keeper's `offer`/`tranche_startup` arrays if reachable; else bound: every "$ above price" figure is a LOWER bound on idle within $X |
| T2 the chain omits retirees/imports | T-6 per population; the import class is read from `class_hourly`, never from the assembled fleet |
| T3 zone-mean vs load-weighted | both reported; C3a's is load-weighted |
| T4 the shoulder is defined on RT; DA differs | P1 reports the population's DA mean and the DA-defined shoulder's overlap with the RT-defined one |
| T5 leap-year 2024 | `_hour_month`, never `pd.date_range` |
| T6 a bound argued on the mean when the object is a distribution | per-band (p75–90 / p90–95 / p95–99) setter census and cushion reported, not only the shoulder mean |
| T7 aggregate agreement ≠ hour-set correctness | every statistic is per population, hour-of-day matched where a diurnal driver is involved |

---

## 5. Stop rule

No lever is chartered and no LP spent unless some item's measured reach is
≥ 25 % of its population's gap under P3's licensing line AND the item's family
is not R/I/G — in which case the outcome is a re-charter with a rule-28(a)
argument, still no solve this session.

**Rule duties.** Rule 15: zero-solve, nothing registered. Rule 28(b): evidence
appended in MISO's shard to `miso_seam_coincident_envelope` (shoulder
measurement), `measured_ramp_capability` (fourth objection scored),
`diurnal_price_amplitude` (setter/cushion anatomy); no verdict moves; §5.4 stamp.
Rule 28(c): no field. Rule 25: MISO's files only. Rule 27: blob-verify after push.

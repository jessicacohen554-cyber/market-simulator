# PREREG miso-211 — THE RDT SOUTH→NORTH BINDING STATE: why the LP's corridor does not bind where MISO's did, and how much of the shoulder that could ever be worth (phase 0, zero-solve; a solve ONLY if the static reach clears its own line) (2026-09-04)

**Pushed BLIND** before any adjudicating statistic. Keeper at open
`2026-09-04-miso-210-clock` (bundle `miso210_clock_B`, PROMOTED miso-210),
determination NOT-YET on {C3a-2025 −12.3845} alone; C3c the single ledgered
caveat; C6 attested (41/2). Rule 22: 2023–2025 only. HEAD `a35c9f9b` (=
`origin/main`, zero drift). **No LP is planned**: every quantity below is
read from the keeper's committed/local sidecars (`hourly/system`,
`hourly/network` — link flows AND duals — `hourly/class_hourly`, `flows`) and
from measured in-repo series. The one solve this session may spend is the
R-4 A/B, and only if R-3 clears the line stated in §4.

---

## 1. What is settled, and what this session does NOT re-derive

* **The corridor in the keeper.** MISO-South ↔ MISO-Plains is a one-way pair
  (`iso_configs` L7) run through `apply_miso_rdt_tcdc` (K, `rdt_tcdc`) with
  `miso_rpe_pricing=true`: **S→N = three parallel tiers, 2,300 MW free
  (0.92 × 2,500), then 46 MW at $240 ($40 TCDC step 1 + $200 RPE), then
  154 MW at $700 ($500 + $200)**; N→S the same on 3,000 (2,760 / 55 / 185).
  `miso_south_seam_split=true` gives the South its own external bus
  (`MISO_external_South>MISO-South` only), so **no free bypass exists** around
  the pair — routing-around (charter R-2c) is closed by topology and is only
  VERIFIED here (§3 R-2c), not re-opened.
* **The measured record.** `data/raw/transfer-constraint-binding/MISO/`:
  RT sub-regional PBC rows exist ONLY when the RDT carried a nonzero shadow
  price; `RDT_SO_MW (South_North)` is the S→N constraint; 5-min EST interval
  starts (EST_TO_MODEL = −1). **The RDT limit-MW series is NOT published**
  (miso-183 H-1 closed negative: Data Broker dead, Data Exchange key-gated,
  no market report) — the PBC breakpoints are % of an unpublished modeled
  limit. Charter R-2(a) therefore cannot be measured directly; it is
  DISCRIMINATED from R-2(b) through the LP's own flow (§3).
* **What the lane already measured on the SCARCE set (47 h, 2025):** the
  real RDT bound S→N in 32/47 (any 5-min row) and N→S 0/47; the keeper (at
  miso-187) bound N→S in 7/47 and S→N 0/47; the model's South boundary net
  INFLOW +0.385 GW vs the measured −2.441 GW (outflow); the decomposition's
  dominant term is **~3.6 GW of South capacity idle above the Midwest price**
  (mc-idled — the EXHAUSTED offer family), not load (exonerated) and not the
  limit (miso-186 §1, §6; miso-187 §3). **On the SHOULDER (351 h) none of
  this has been measured** — miso-208 §4 measured only the binding SHARES
  (real S→N 50.4 % shoulder / 66.7 % tail / 32.5 % other daytime; keeper
  spread $1.36) and the strand lift (0.048 / 0.007). That is this session's
  gap to fill.
* **Cells NOT re-tested** (rule 28a): `measured_interface_limits` R
  (miso-174, the PJM/SPP seam imports), `m2m_seam_entitlement_cap` G
  (miso-176), `miso_south_firm_export_block` G (miso-182),
  `miso_south_export_ladder_rt_tail` R (miso-184). None is the internal RDT.

## 2. Populations and clocks (miso-207/208 construction, verbatim, re-pointed to the miso-210 keeper)

Jun–Jul, INDIANA.HUB RT: TAIL = actual ≥ p99 (15 h in 2025), SHOULDER =
p75–p99 (351 h), OTHER-DAYTIME = the rest at h10–h20. Gaps (keeper
load-weighted price − actual): 2025 shoulder −43.73, tail −636.86 (miso-207,
unchanged by miso-210 to the decimal). Model clock CST hour-beginning; the
PBC 5-min EST starts → CST hour H−1 (`_miso183.pbc_binding_hours`); regional
`rf_al`/`sr_gfm` HE k EST → CST hour k−2 (`_miso183.regional_series`).
"Real RDT bound S→N in hour h" = any 5-min `RDT_SO_MW` row in h (miso-208's
census; the majority-of-intervals variant is REPORTED).

## 3. Phase 0 — predictions, each with its mechanism

### R-1 — the LP's corridor state in the real binding hours

Per population and year, from `hourly/network_<year>.parquet` (the three
S→N tiers summed; the tier duals): S→N flow distribution, share of hours at
the free-tier limit (flow ≥ 2,300 − 1 MW), share with a positive dual, mean
headroom; the same for N→S; beside the measured `RDT_SO_MW` binding
indicator.

* **R-1a.** In the 2025 shoulder hours where the real RDT bound S→N, the LP's
  S→N flow reaches the 2,300 MW free tier in **< 10 %** of them (0.75) and
  its mean flow is **< 1,200 MW** (0.6). Mechanism: miso-208's $1.36 mean
  keeper spread is incompatible with a binding priced tier ($240 minimum).
* **R-1b.** The LP runs the corridor **N→S** (flow > 0 on the Plains→South
  pair) in **≥ 30 %** of those same hours (0.6) — the miso-186 "wheel runs
  backward" signature generalizes from the scarce set to the shoulder.
* **R-1c.** Tail: LP S→N binds in **0** of the 11 real-binding tail hours
  (0.8) (miso-187: S→N 0/47 on the scarce set, which contains the tail).
* **R-1d.** Real record in the corrected populations reproduces miso-208
  within ±2 pp (50.4 / 66.7 / 32.5 %) — a reproduction line, not a
  prediction.

### R-2 — WHY: three hypotheses, one measurement each

* **R-2a (limit).** Cannot be measured (no limit series). Discriminated: if
  R-1a holds (the LP's flow sits far below 2,300 in the real binding hours),
  the LEVEL of the limit is not what stops the LP from binding — a lower
  measured limit would bind a flow the LP does not send. **Predict: (a) is
  NOT the operative cause** (0.75). Reported: the ~92 % default vs the
  measured shadow-price step (≤ $40 ⇒ step 1; ~$500 ⇒ step 2) as the only
  published handle on the real limit's regime.
* **R-2b (South surplus).** Measured South boundary net `N_S = L_S − G_S`
  (`rf_al` actual load − `sr_gfm` RT SE generation; negative = South
  exports) vs the model's South boundary net (Σ into-South link flows: N→S −
  S→N + external_South), mean over the shoulder hours where the real RDT
  bound S→N. **Predict: measured ≤ −1.5 GW (outflow), model ≥ −0.5 GW
  (near balance or inflow); gap ≥ 1.0 GW (0.65).** Mechanism: the same
  mc-idled South block miso-186 measured at ~3.6 GW on the scarce set. The
  decomposition of the gap into (i) South generation model − measured by
  fuel family (gas/coal/nuclear) and (ii) South load model − measured is
  REPORTED per population; predict the generation term carries ≥ 70 % of it
  (0.6) and the model's South gas output sits BELOW measured (0.65).
* **R-2c (routing around).** Σ over links into MISO-South = the South zone's
  (demand − dispatch − storage net) to < 1 MW in every hour, with
  `MISO_external_South>MISO-South` the only non-RDT term. **Predict:
  identity holds; no bypass** (0.95). Verification of a topology fact.

**Decision rule for R-2:** if R-1a and R-2b hold, the data supports (b) — the
LP does not bind the corridor because its South has no surplus at the
Midwest price, and a measured RDT LIMIT would be the wrong lever (it caps a
flow the LP does not send). If R-1a FAILS (the LP flows ≥ 2,300 in ≥ 25 % of
the real binding hours but with duals the record contradicts), (a) is live
and R-4's form applies.

### R-3 — static reach on the miso-210 keeper, both populations, before any lever

Licensing line as every prior lane: **≥ 0.25 of the gap in BOTH populations.**

* **R-3a (strand, re-measured).** miso-208's construction verbatim — remove
  the within-$20 South cushion from the idle census in the hours the real
  RDT bound S→N, re-price up the keeper's own census (miso-208 `lift`).
  Predict **0.03–0.07 shoulder / ≤ 0.02 tail** (0.7) (miso-208: 0.048 /
  0.007 on the miso-202 keeper; miso-210 moved no shoulder/tail hour).
* **R-3b (separation ceiling).** In the hours the real RDT bound S→N, the
  measured Midwest−South separation on the SCORED comparator — INDIANA.HUB
  RT minus the mean of the four South hubs (ARKANSAS/LOUISIANA/MS/TEXAS) —
  minus the model's own Indiana−South zonal spread; lift = max(0, that),
  averaged over the population, over |gap|. This is the CEILING on what a
  corridor that bound exactly as MISO's did could add to the Indiana price
  with the model's South price held fixed. Predict **measured separation
  $8–20 mean in the binding shoulder hours; model $1–3; share 0.10–0.25 in
  the shoulder (0.6); ≤ 0.05 in the tail (0.85)** (the tail is a
  system-energy object, MCC 3.8 %, miso-208 §4). REPORTED beside it: the
  measured PBC S→N shadow price mean in the same hours (the constraint's own
  price, ≤ $40 in step 1).
* **R-3 verdict predicted: NOT CLEARED in either construction in the tail;
  NOT CLEARED in the shoulder (0.65).**

### R-4 — the lever, conditional

* If R-3 clears (both populations ≥ 0.25): the admissible form is a MEASURED
  hourly RDT limit (rule 13: a published transfer limit regenerable from the
  record; forward analogue = the seasonal RDT rating) as a `ScenarioConfig`
  field with a matrix row (rule 28c), single-delta A/B on the miso-210
  ten-gate scorer. **Predicted not to be reached (0.75).**
* If R-3 does not clear: mint the base row **`miso_rdt_measured_limit`**
  (field-less adjudicated mechanism-in-kind, the `miso_south_firm_export_block`
  precedent) with MISO cell **R** carrying the reach numbers and the (a)/(b)
  diagnosis; `.` in every other shard; no field, no solve. The `rdt_tcdc` K
  cell gets appended evidence (the binding-state measurement), verdict
  unchanged.

## 4. Kills and voids

* **N-1 footing:** the population gaps reproduce miso-207/208 on the
  miso-210 keeper to ±0.01 (shoulder −43.73, tail −636.86) and the real
  binding shares to ±2 pp; the model South boundary identity (R-2c) closes
  to < 1 MW. A footing failure STOPs before any verdict.
* **C3a is never a gate**; nothing here is a residual chase — the object is
  a measured binding state and a topology/supply question.

## 5. Reported against interest, in advance

* If R-2b's decomposition puts the gap on LOAD rather than generation, the
  miso-186 "load exonerated" reading does not transfer to the shoulder and
  is said so.
* If the measured separation in the binding shoulder hours is SMALL (< $5),
  the RDT is a minor price object even in the real market and the 50 %
  binding share was a red herring — said so.
* If R-3b clears the shoulder but not the tail (likely), the licensing rule
  refuses and the finding says the shoulder alone would have licensed it.

## 6. Governance

Zero-solve unless R-4 fires (then rule 15 registration, rule 12 concurrency,
the ten-gate scorer). Rule 28(b): `rdt_tcdc` evidence appended, the new row
+ six cell lines if minted (28c duty for a field-less row); §5.4 stamp. Rule
25: MISO's shard only. Rule 22: 2023–2025. Rule 13: `rf_al`/`sr_gfm`/PBC are
diagnostic reads, never LP inputs. Rule 27: blob-verify after push.
Instrument: `scripts/probes/_miso211_rdt_binding_state.py` → record
`results/calibration/_miso211_rdt_binding_state.json`.

Next shorthand after this session: **miso-212**.

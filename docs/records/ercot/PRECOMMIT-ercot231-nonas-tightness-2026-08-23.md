# PRECOMMIT — ercot-231: the NON-AS ENERGY/TIGHTNESS factor program — the last unswept surface behind the 2023 summer scarcity residual, enumerated completely, with identification instruments, kill preconditions and gates pinned BEFORE any measurement and BEFORE any solve

**Session ercot-231 (owner-dispatched program), 2026-08-23, branch
`claude/ercot-energy-tightness-channel-vm4w8k` (base = origin/main `55b20a5`).
Keeper at pin: `2026-08-20-ercot223-arm-eventrelease` (NOT-YET, fail set
{C3a-2023 −39.7 % (model 38.81 vs actual RT load-weighted 64.32), C3b-2023
NRMSE 0.729}, C3c ledgered CAVEAT ×3; 2024/2025 clean at +0.4 %/0.131/22 h
and −7.6 %/0.099/1 h; 2023 miss split 67 caught / 114 missed / 7 phantom of
the 181 actual-RT>$200 tail hours).** This file is pushed and blob-verified
BEFORE any Phase-0 measurement is computed on the 2023 data, BEFORE any
derive or fetch runs, and BEFORE any solve. Code reads, committed-artifact
reads (run_config, matrix cells, prior findings) and on-disk
file-existence/schema checks informed the enumeration below; no miss-set
statistic has been computed.

## 0. THE OWNER DISPATCH (the session charter IS the owner speaking —
X-1/X-2/B-1/ercot-226 signature-by-dispatch precedent)

The dispatch charters a precommitted Phase-0 factor program over "the
ENERGY/TIGHTNESS channel OUTSIDE AS procurement" — "the ercot-226 discipline
applied to the non-AS tightness surface" — with the sweep to cover at
minimum: outage/derate representation residuals beyond the armed measured
overlay and the executed items 20/24; DC-tie exports/imports at scarcity
hours; any measured supply-side quantity at the missed hours the model does
not carry; and demand-side representation residuals consistent with
backcast-measured-load doctrine. Carried forward by the dispatch, verbatim
obligations:

- **W-2 (probe protocol):** 2023-only solves are diagnostic probes; probe
  bundles stay LOCAL and gitignored, never dashboard-registered; the
  committed record is the probe JSON + gates JSON + the FINDING. Only a
  3-year bundle that clears adoption is registered (rule 15 in full).
- **The Amendment-3 solved-verdict obligation (standing owner order):** "a
  buildable factor with on-disk data gets a SOLVED A/B, not a paper kill."
  §5.4 kill preconditions are probe-informing PRIORS, not probe-terminating
  verdicts, for any factor with a buildable form and on-disk (or
  keyless-fetchable) data.
- **The honest prior, pre-registered (charter step 2):** the ERCOT queue
  holds no live in-model item and the adjacent closures are extensive — this
  sweep may terminate at MEASURED-EMPTY. That verdict is a deliverable, not
  a failure: it would complete the tightness side and leave every admissible
  surface measured dead.
- **The termination protocol (charter step 3):** if the sweep terminates
  empty, this session must NOT restore the Door-D rest posture on its own
  authority; the disposition goes to the owner — (a) restore Door D (rest
  until the 2026 SOM RTC+B-era anchors, ~mid-2027), the recorded fallback;
  or (b) card the seasonal end-of-season term, the only un-adjudicated named
  successor of the adaptive family, disclosing honestly that its identified
  role (the Oct→Nov off-ramp cliff, ercot-221 Amendment-2 G-DECAY) is a
  fall-shape object, not on its face a summer depth-count candidate.

## 1. THE OBJECT — what the measured record already pins, and the arithmetic
every factor below faces

- **The missed hours are MW-MATCHED.** At the C3c missed hours the model
  reproduces ERCOT's physical dispatch fuel-by-fuel (2023: gas −1,412 MW,
  coal +378, nuclear −7, renewables +504 on 72.5 GW; battery net within
  −102/+181 MW of measured BAT in 2024/2025), and **model demand equals the
  EIA-930 generation sum to 0.6 MW** — while clearing p50 $96.65 where
  ERCOT's own SCED λ cleared $456.81, with published RTORPA p50 $0.84, PRC
  p50 5.7–7.7 GW (never < 4,132 MW, 0 hours under the EEA-1 2,300 MW
  trigger), and telemetered RTOLCAP spare online capability 6.9–8.3 GW.
  "Same MW, no reserve scarcity, 3–5× the price ⇒ an energy-offer object at
  a matched clearing quantity" (FINDING-ercot216 §3/§5; the queue's ercot-216
  block). The 226/227 program then measured the AS-procurement side
  unreachable (`d_price_at_miss` p50 = max = 0.0 under every armed factor),
  and ercot-230 measured the conduct channel unable to bootstrap itself
  (keeper = the fixed point of the within-year adaptation map).
- **CHANNEL DOCTRINE (binding, inherited from PRECOMMIT-ercot226 §1):**
  admissible factors act on the ENERGY/TIGHTNESS channel — the supply
  physically available to SCED at the margin, and the demand it must serve —
  and move price ONLY through λ (energy-stack displacement), thereby also
  feeding the armed adaptive conduct mechanism more of its own spike days.
  NO factor may manufacture price through the ORDC-adder channel: reality's
  RTORPA at the target hours is ≈$1 (rule 1). Every probe reports channel
  attribution (§5.2) and the G-SHORTFALL subset gate (§5.3);
  improvement carried by manufactured reserve shortfall or by the model
  adder is a FAIL, whatever it does to C3a.
- **THE EX-ANTE ARITHMETIC, disclosed before any factor is measured.** The
  measured supply-curve slope at the model's 2023 clearing position is flat:
  ~1.6 $/MWh per GW (the ERCOT-154 measurement, carried unrefuted through
  the ercot-189 face-closure map), with the price cliff several GW up-stack
  (the item-11 object measured the phantom sub-λ̂ headroom at ~2.7 GW, and
  ERCOT-163 the CC depth at ~9× reality's). The official C3a-2023 bar
  arithmetic (ercot-189 §2.2–2.3, on the current keeper's −39.7 %): the
  114 missed hours are ~1.3 % of the year's hours; a quantity factor that
  displaces X GW at the miss set moves the missed-hour λ by ~1.6·X $/MWh
  unless it reaches the cliff, and moves ANNUAL load-weighted C3a by that
  times the miss set's load share (~2 %). **So even a full-GW sustained
  displacement at every missed hour buys O($0.03/MWh) annually — three
  orders of magnitude under the §5.5 adoption bar (1.5 pp ≈ $0.96/MWh) —
  unless it pushes the clearing point into the cliff, which the measured
  record locates ≥ ~2.7 GW away.** No factor below has a plausible measured
  magnitude near that; this is the quantitative form of the charter's
  honest prior, pre-registered so a null sweep cannot be read as a surprise.
- **What would still count:** a factor whose Phase-0 magnitude measures in
  the multi-GW range at the miss set (a genuine representation defect), or
  one that moves 2023 toward actual on the un-targeted measures (the
  ercot-221 promotion pattern) while structurally more faithful — escalated
  per §5.8, never self-promoted.

## 2. THE FACTOR TABLE

Each row: (a) external driver + citation; (b) identification source +
formula (zero residual-fitted scalars); (c) window/data-key; (d) predicted
sign on summer-2023 scarcity hours; DOF row; adjudicated-cell coincidences
named (rule 28(a) DO-NOT-REDO confrontation). Factor ids N1–N5.

### N1 — DC-tie interchange representation at the missed hours
- **(a) Driver:** ERCOT's five DC ties — DC-E (Monticello, ~600 MW) and
  DC-N (Oklaunion, ~220 MW) to SPP; Railroad DC (~300 MW), Eagle Pass
  (~36 MW) and Laredo VFT (~100 MW) to CFE/CENACE — ~1,256 MW total
  transfer capability (ERCOT DC-Tie Operations reference / CDR). Summer
  2023 scarcity evenings ran with material DC-tie activity; the measured
  hourly net flow is on disk (EIA-930 `ERCO hourly.parquet`,
  `Total interchange`, positive = net export).
- **(b) Identification — the representation as built:** the ERCOT backcast
  serves `demand + net_interchange` spread across zones **by the same
  load-share weights as demand** (`data/eia930/demand.py::load_demand`,
  ERCOT path; the netting is what makes model demand ≡ the EIA-930
  generation sum, the identity ercot-216 measured closing to 0.6 MW, and
  what item 11's charter records as "model demand basis verified correct —
  DC ties are netted"). Netting a measured flow is arithmetically
  equivalent to an explicit price-taking tie resource at any offer price
  below the clearing λ; the equivalence can break only on (i) zonal
  PLACEMENT (the spread puts tie MW in every load zone by load share, not
  at the tie-connected zones) or (ii) price-ELASTICITY (an explicit tie
  that would withdraw at the model's λ).
- **N1-P0 (measurement):** at the keeper 2023 miss set (the 114 hours,
  actual RT > $200 & keeper max-zonal ≤ $200, from the keeper's committed
  sidecar + `actual_tail`/actual LMP series): the distribution of measured
  net interchange (p10/p50/p90, import/export hour counts, max import), its
  share of the ~1,256 MW capability, and the same for the 67 caught hours
  as contrast. Re-verify the netting identity at the miss set (demand +
  interchange vs generation sum).
- **N1a — buildable arm: measured tie-zone attribution.** Replace the
  load-share spread of the interchange with attribution at the
  tie-connected model zones: SWPP flow → Northeast (DC-E, 600/820) and
  North (DC-N, 220/820); CEN flow → South (all three Mexico ties). The
  per-neighbor split comes from the EIA-930 BA-to-BA interchange product
  (`diba ∈ {SWPP, CEN}`), fetched by the STANDING keyless route
  (`scripts/data/fetch_eia930_interchange.py --ba ERCO --source bulk
  --years 2023 2024 2025` — the bulk six-month CSV family requires no API
  key; raw-immutability honored, new file only). Fallback if the fetch is
  unreachable from this environment: attribute the on-disk TOTAL by the
  fixed nameplate shares (Northeast 600/1256, North 220/1256,
  South 436/1256) — disclosed as the cruder form. **Formula:** the demand
  loader's `weights × interchange` term becomes `tie_map × interchange_n`
  per neighbor n (or `tie_map_total × interchange`), rows summing to the
  same system total every hour — the system energy balance is unchanged BY
  CONSTRUCTION; only zonal placement moves. New boolean
  `ercot_tie_zonal_interchange` (default False). Zero fitted scalars (the
  nameplate ratings are published design constants; the measured flows are
  the data).
- **(c) Window/data-key:** measured flows exist for ALL training years —
  unlike the 226 factors this driver is NOT 2023-keyed, so if the arm is
  anything but inert the 3-year retention test is §5.7's explicit-scoring
  branch, never the sha-identity branch. Forward story: a forecast year
  carries no measured flows; the netted/attributed interchange is
  backcast-measured-load doctrine (the flow rides the same measured-boundary
  status as load itself), and the forecast-side treatment (island, no
  interchange) is untouched by the flag.
- **(d) Predicted sign:** ≈ 0 on C3a-2023. At the top of the book ERCOT
  scarcity prices are system-wide (intra-ERCOT congestion at the missed
  hours is small; the load-weighted C3a moves only through zonal price
  dispersion). The arm is a fidelity refinement (PJM's per-border-zone
  attribution is the in-repo precedent, `pjm_zonal_interchange`), expected
  MEASURED-INERT at the C3a digit. Solved regardless (Amendment 3).
- **DOF row:** zero new fitted scalars; one boolean; the tie→zone map is a
  published-physical-location constant table.
- **Coincidences named:** `priced_interchange` ERCOT cell `.` (n/a — ERCOT
  has no interchange node; this arm does NOT create one, it re-places the
  existing netting); no adjudicated cell covers interchange zonal
  attribution for ERCOT. Rule 28(c): the new field gets its matrix base row
  + a cell in every ISO shard in the same push that lands the field.
- **N1b — priced/elastic DC ties: enumerated, expected NO-WINDOW/
  DATA-ABSENT (documentation row).** An elastic tie needs the neighbor's
  price: no SPP or CFE price series exists on disk (verified:
  `data/raw/lmp-data/` holds the six modeled ISOs only), and
  `data/neighbor_price.py` is the forecast-grade seam construction for
  import-node ISOs, not wired for ERCOT. And the window test is decisive
  independent of data: if the miss-set flows are imports near capability,
  an elastic representation could only WITHDRAW measured-delivered supply —
  contradicting measured flows (rule 14) to manufacture tightness (rule 1);
  if the flows are exports, elasticity would CUT exports and push λ DOWN
  (anti-helpful). **Kill precondition N1b-K (§5.4):** measured net flow at
  the miss set p50 an import ≥ 50 % of capability OR an export ⇒ no
  admissible window; recorded, no build, no solve (the F4-form terminal —
  data absent AND window absent).

### N2 — outage/derate representation residual beyond the armed measured channels
- **(a) Driver + the armed inventory (from the keeper's `run_config.json`):**
  `outage_source="historic"` + `historic_outage_overlay` (CAMPD measured
  outage windows, cell `campd_outage_windows` K), the measured 60-Day DAM
  availability family (`ercot_thermal_dam_availability` + `_hourly` +
  `_plant` + `_coal`, with `_coal_event_cap`/`_gas_event_cap` K and the
  reconciliation/unit-scoped variants R), `ercot_nuclear_unit_availability`
  K, `ercot_noncampd_plant_availability` armed,
  `coal_nameplate_summer_derate` K, and item 24
  (`ercot_partial_outage_shaped_derate` K, ercot-185). Item 20
  (`temp_dependent_derate`) is R — refused ex-ante at ercot-177 on measured
  grounds (the TX fleet's hot-hour envelope is FLAT at 40–46 °C; the DAM
  water-fill erases pre-overlay derates for the four covered classes,
  62.1/77.6 GW). **For the covered classes the class-hour availability mean
  is PINNED to measured DAM HSL by construction** — there is no free
  outage-depth residual there.
- **(b) N2-P0 (coverage measurement, not a mechanism):** at the miss set,
  the per-class decomposition of model available capacity
  (pmax × availability from the keeper's committed artifacts/replayed
  arrays) with each class labeled by its measuring instrument (DAM family /
  CAMPD windows / none), enumerating the classes whose availability is NOT
  measured-pinned: storage, the DAM-excluded CHP family (11.2 GW,
  `scenarios.py` DAM exclusion), hydro (no ERCOT fleet — the whole
  `hydro_*` matrix family is `.` for ERCOT), renewables (HSL basis — N3).
  The aggregate model-vs-telemetry comparator (rtolcap) is MEASUREMENT-ONLY
  context: feeding it is the adjudicated `ercot-219` R / dimensional wall,
  and B-2 stays UNSIGNED with a DO-NOT-SIGN recommendation — this program
  does not touch either.
- **N2a — battery availability/outage at scarcity: expected DATA-ABSENT at
  any admissible grain (documentation row with attempt log).** Driver:
  real 2023 battery outages/derates at scarcity hours. On-disk: none (CAMPD
  covers emitters; `caiso-dam-outages` is CAISO's). Reachable surfaces, to
  be attempted and logged (the ercot-228 obligation — attempt at execution,
  never infer): the ERCOT MIS outage-report family sits behind the same
  7-day rolling retention / client-certificate wall ercot-228 measured
  terminal for F4, and the credentialed Public Data API key is the owner's
  standing decline (2026-07-05). The one public long-retention aggregate
  (Hourly Resource Outage Capacity, NP3-233) is SYSTEM-grain — usable, if
  fetched, only as Phase-0 documentation, because feeding an aggregate
  outage MW into a per-class LP is the ercot-219-R aggregate form. Bounds
  that cap the object regardless: G-BAT (±25 % EIA-930 BAT) passes on the
  keeper, and ercot-216 measured battery net within −102/+181 MW of
  measured BAT (2024/2025). **Kill precondition N2a-K:** no per-unit or
  per-class measured ERCOT battery outage series on any reachable surface ⇒
  DATA-ABSENT terminal, attempt log committed in the probe JSON.
- **N2b — CHP-family availability depth: documentation row, no build.** The
  CHP family (CC_CHP 9,030 MW + CT_CHP 2,056 + ST_CHP 128) is DAM-excluded
  by design; its availability rides the CAMPD windows. The item-20 record
  measured CC_CHP capability RISING with temperature (−1.41 %/°C — the
  largest-magnitude slope in the fleet, NEGATIVE), so a summer
  derate/outage deepener for CHP is refuted by ERCOT's own measured
  parameterization (rule 25: only ERCOT's own slope is admissible, and it
  is the number that refutes it). The behind-the-meter/PUN half of the CHP
  question is item 11's candidate ("cogeneration behind private-use
  networks") — CLOSED, Q-B FINAL. No probe.
- **(d) Predicted sign for the family:** any residual-outage deepener is +
  through energy displacement, but the §1 arithmetic applies, and for the
  62-GW covered core the depth is measured-pinned already — the only
  un-pinned classes are bounded (batteries ±0.2 GW by the G-BAT record) or
  refuted (CHP). **Kill precondition N2-K:** no measured physical outage
  series exists on any reachable surface that the armed channels do not
  already carry ⇒ ALREADY-CARRIED verdict for the family (the F5 form:
  stated, measured, not solved).
- **Coincidences named:** `unit_outage_lp_capacity_basis` U /
  `unit_outage_short_windows` I / `cc_outage_derate_from_top` off /
  `unit_partial_outage_windows` off are alternative representations of the
  SAME CAMPD driver — rule 19 gives the armed overlay + shaped-derate
  ownership; arming any of them would stack a second mechanism on one
  phenomenon, and no evidence names the armed member as mis-measuring.
  They stay untested here (this program tests residual DEPTH, not
  re-plumbing of a carried driver).

### N3 — renewable delivery basis at the missed hours (the +504 MW wedge)
- **(a) Driver:** ercot-216 measured model renewables +504 MW OVER actual
  at the missed hours (on 72.5 GW installed). The representation: ERCOT
  wind/solar CF upper bounds are built from the NP6 HSL (uncurtailed
  potential) parquet and the model RE-CURTAILS endogenously under the
  modeled network (`data/renewables.py` module doctrine; measured GTC
  limits armed via `load_gtc_hourly` + `ERCOT_GTC_LINK_MAP`;
  `wtx_curtailment_driver` / `wtx_curtail_unpooled` K). A +504 MW delivery
  excess at the miss set says the model under-curtails reality by ~0.5 GW
  there — extra MC=0 supply suppressing λ by ~$0.8/MWh at the §1 slope.
- **(b) N3-P0 (measurement):** decompose the wedge at the miss set by
  technology (wind/solar, model dispatch vs EIA-930 actual) and by zone
  (where does the model deliver renewable MW that reality curtailed?), and
  against the built HSL series (measured curtailment = HSL − actual vs
  model curtailment = UB − dispatch).
- **(c) The adjudication frame:** an actual-generation UB pin is rule-13
  FORBIDDEN (the outcome-pin form named in the rule text); the HSL basis +
  endogenous re-curtailment is the deliberate rule-1 structure. The
  admissible buildable form is a MEASURED-LIMIT completion only: if P0
  attributes ≥ 300 MW of the wedge to a specific published 2023 GTC/IROL
  the armed `ERCOT_GTC_LINK_MAP` does not carry (a data-vs-data gap), the
  map completion is a rule-14 repair → built and solved. **Kill
  precondition N3-K:** wedge p50 < 300 MW at the miss set, OR not
  attributable to a specific uncarried published limit ⇒ documentation row
  — the wedge is the reduced-network topology-class residual, and the
  West/Panhandle split stays CLOSED (DIAGNOSIS §§9–10; not re-opened as a
  topology change).
- **(d) Predicted sign:** + but bounded ~$0.8/MWh at the miss set even if
  fully closed (0.5 GW × 1.6 $/MWh/GW) — under every bar by itself.

### N4 — demand-side representation residuals (backcast-measured-load doctrine)
- **(a) Driver + doctrine:** the backcast serves measured load; the ERCOT
  basis is EIA-930 `ERCO` metered demand + interchange (≡ generation sum,
  closing to 0.6 MW at the miss set per ercot-216), allocated to zones by
  ERCOT's OWN measured native-load weather-zone shapes
  (`zone-specific-demand/ERCOT_Native_Load_2023.xlsx`, 8 weather zones → 7
  model zones, `load_zonal_shares`). Measured load embeds the real 2023
  demand response (4CP avoidance, conservation appeals, large-flexible-load
  curtailment) — the doctrine's own content.
- **(b) N4-P0 (three measurements):**
  - **P0a — data quality at the miss set:** count of
    interpolated/screened demand hours among the 114 (the raw frame's NaN
    pattern; the `demand_dropout_screen` cell is I for ERCOT). Expected 0.
  - **P0b — basis cross-check, data-vs-data:** EIA-930 system demand vs the
    ERCOT native-load file's system total at the miss set (p50/p90 of the
    wedge, sign consistency). Expected < 100 MW (the same meter, two
    publications).
  - **P0c — zonal allocation:** verify the measured zonal-shares path is
    live for 2023 (non-None) and report the miss-set zonal load shares vs
    annual (does the allocation at scarcity differ materially from the
    load-share fallback the interchange spread uses — context for N1a).
- **N4a — buildable arm (conditional): demand-source refinement to the
  native-load basis.** Built ONLY if P0b measures a wedge ≥ 100 MW p50
  with consistent sign at the miss set (rule 14: prefer the more accurate
  measured series). Disclosures pinned now: the swap must keep the
  wind/solar/benchmark series clock-consistent (the demand loader's own
  warning — the native file rides a different clock convention than the
  EIA-930 frame), and G-BAT/G-SPUR baselines ride the EIA-930 frame — a
  basis swap that moves the benchmark seam fails its gates honestly.
  Expected: not built (P0b under threshold).
- **N4b — demand response / flexible load as a priced demand object:
  excluded-for-doctrine (documentation row).** Measured load already nets
  the response; re-adding curtailed load and pricing its re-entry would
  (i) double-count against the measured series and (ii) manufacture
  tightness reality did not have (PRC 5.7–7.7 GW at every missed hour).
  ERS: no window (0 EEA hours; PRC never < 4,132 MW — the ercot-216
  measurement that also keeps `maxgen_emergency_tier_pricing` windowless).
  Loads do not set SCED λ outside the AS families (closed by 226/227).
- **(d) Predicted sign:** P0a/P0b are integrity checks (expected null);
  a positive P0b wedge could carry either sign. **Kill precondition
  N4-K:** P0a = 0 interpolated hours AND |P0b wedge| p50 < 100 MW ⇒
  demand-side measured-faithful, documentation row, no build.

### N5 — measured supply at the missed hours the model does not carry
- **(a) Driver:** the fleet deliberately omits immaterial ERCOT classes:
  hydro (~570 MW nameplate; the `hydro_dispatch_envelope` /
  `hydro_min_flow_floor` / `hydro_ror_split` / `hydro_budget_*` cells are
  ALL `.` n/a for ERCOT), and any "other"/biomass residual outside the
  CAMPD+nuclear+renewable+storage universe. If reality dispatched material
  MW from an uncarried class at the missed hours, the model is TIGHTER than
  reality there (an anti-conservative omission — it RAISES model λ), and
  rule 14 requires carrying it even though adding supply moves C3a-2023
  AWAY from actual.
- **(b) N5-P0 (measurement):** EIA-930 by-fuel actuals at the miss set for
  the uncarried classes (hydro, other) — p50/p90 MW — plus the closure
  residual of the ercot-216 fuel table (gas −1,412 + coal +378 + nuclear −7
  + renewables +504 nets to ~−537; decompose the balancing +537 among
  battery/hydro/other model-vs-actual at the miss set).
- **(c) Buildable arm N5a (conditional):** if hydro-or-other p50 ≥ 100 MW
  at the miss set, the hydro intake path exists (generic
  `build_hydro_fleet` + EIA-923 monthly energy, the `hydro_level_923_hy`
  family) → built and solved under Amendment 3, with the materiality
  adjudication of the `.` cells re-opened BY MEASUREMENT (the only route
  that may re-open an n/a). Expected: p50 < 100 MW (ERCOT hydro is ~0.1 %
  of energy; summer drought evenings run it low), verdict
  BELOW-MATERIALITY, `.` cells stand.
- **(d) Predicted sign:** NEGATIVE on C3a-2023 (adds supply → λ down —
  faithful but anti-helpful; stated so the record cannot later read this
  row as a residual-closing lever).
- **Coincidences named:** PUN/self-serve generation → item 11, CLOSED
  (Q-B). Switchable units → carried in the fleet; their export state is
  inside the measured interchange (N1). Distributed PV → netted inside
  measured load AND excluded from EIA-930 solar — consistent on both sides
  of the balance by construction; documentation only.

## 3. EXCLUDED-FOR-STRUCTURE (recorded; no probes — carried forward with
citations, none re-opened)

- ORDC X-axis surgery / reserve-requirement deepeners / any adder-channel
  fix: NO WINDOW — RTORPA ≈ $1 at the target hours (ercot-216 §5); §1
  doctrine.
- Aggregate capability reconciliation in any form (ercot-219 R,
  dimensional; B-2 UNSIGNED, DO-NOT-SIGN); per-unit crosswalk (item 11,
  Q-B FINAL).
- The AS-procurement family in full (ercot-226/227: F1/F1b/F1c
  measured-inert/zero, F2 R negative sign, F3 R at the grain, F4
  data-absent terminal, F5 already-carried).
- The within-year conduct family at every member (Door A ×3; ercot-221/223
  armed; ercot-222 R; ercot-230 fixed-point inert). `ercot_adaptive_
  fixed_point` stays default-off; no re-arm without new evidence.
- Item 8 (closed unconditionally, ercot-224); ercot-162 offer surfaces;
  mid-band adder legs (ercot-214/215); the ercot-219 aggregate; regime
  lanes (ercot-217); item 20 re-open (temp derate — physics measured
  absent); West/Panhandle topology re-open (DIAGNOSIS §§9–10).
- `maxgen_emergency_tier_pricing` (ERCOT U): stays UNTESTED — its window is
  measured absent (0 EEA hours), and a windowless solve would test nothing;
  the U cell is documented, not spent, by this program.
- Sub-hourly interval scarcity (model-class, rule 8; 17 % of 2023 tail
  hours clear on minority intervals — ercot-216 §4).
- IMM-quantification-as-identification (card-W fence): the IMM record
  supplies drivers and windows only, never parameter values.
- DAM AS MCPCs / any measured PRICE fed as input (rule 13's forbidden
  form).

## 4. COMPLETENESS SWEEP (the charter's own four bullets, mapped onto the
LP's input surface)

The LP's per-zone energy balance is
`thermal + wind + solar + discharge − charge + net_flow + slack − dump =
demand`. Every term's 2023 input surface is now either armed-measured,
enumerated above, or cited-closed: **demand** (N4: level integrity, basis
cross-check, zonal allocation; DR/ERS excluded-for-doctrine),
**interchange inside demand** (N1: magnitude at miss set, placement arm
N1a, elasticity N1b), **thermal availability** (N2: DAM-pinned core, CAMPD
windows, items 20/24 executed; batteries N2a; CHP N2b), **renewable
bounds** (N3: HSL basis + measured GTC + the +504 wedge), **storage**
(conduct/AS families closed; availability N2a), **network limits** (measured
GTC armed; topology closed; N3-K's map-completion branch is the one live
route), **absent classes** (N5: hydro/other/PUN/DPV). The AS/reserve side
(the other constraint family) is closed by 226/227, and the conduct/offer
side by 221/222/223/230. **This program therefore completes the
enumeration of the 2023 tightness surface: a MEASURED-EMPTY verdict here
leaves no admissible un-swept input face on the year.**

## 5. PRECOMMITTED MEASUREMENTS, KILL PRECONDITIONS AND GATES

### 5.1 Inherited instruments (used verbatim; never edited)
- **Official scorer:** `scripts/probes/ercot226_official_score.py --bundle
  <dir> --years 2023`; VALIDATION GATE: on the keeper bundle it must print
  exactly −39.7 % / 0.729 / 74 h (2023), +0.4 % / 0.131 / 22 h (2024),
  −7.6 % / 0.099 / 1 h (2025) (`--validate-keeper`) before any probe is
  scored.
- **Gate wrapper:** `scripts/probes/ercot226_gates.py --control <ctl> --arm
  <arm> --years 2023 --out <json>` — G-CAP / G-SHED / G-SPUR banded +
  lidless report / G-BAT / G-D2 / G-SHORTFALL (the Amendment-1 subset
  form) + the summer block (caught/missed/phantom vs keeper 67/114/7,
  `d_price_at_miss` distribution, window concentration, calm-fortnight
  bias vs +15.44 %, channel attribution, adaptive diagnostics vs spike
  days 7). It imports the frozen ercot221_gates constructions — never
  edited.
- **A/B discipline:** control = `scripts/replay_keeper.py
  results/calibration/ercot223_release_arm --out-dir <ctl> --years 2023`;
  G-REPRO = NUMERIC identity (max|Δ| = 0.0 per numeric column of every
  hourly sidecar vs the keeper's committed sidecars) + the official scorer
  reproducing the printed digits. Arm = control recipe + a single `--set`.
  One solve at a time (rule 12); 6G swapfile; `MALLOC_ARENA_MAX=2`; env
  pins highspy 1.15.1 / pandas 3.0.5 / pyarrow 25.0.1 (verified installed:
  numpy 2.4.6, scipy 1.17.1, python 3.11.15).

### 5.2–5.3 Per-probe measurement and gate set
Identical to PRECOMMIT-ercot226 §5.2–§5.3 (with G-SHORTFALL in its
Amendment-1 subset form), reported per probe year on 2023.

### 5.4 Phase-0 kill preconditions (computed AFTER this file is pushed;
priors, not terminators — Amendment 3 governs)
- **N1b-K:** miss-set net flow p50 an import ≥ 50 % of the 1,256 MW
  capability OR an export ⇒ no admissible elastic window; documentation
  verdict (data absent AND window absent), no build.
- **N2-K:** no reachable measured physical outage series the armed channels
  do not carry ⇒ ALREADY-CARRIED (family verdict); **N2a-K:** no
  per-unit/per-class battery outage series reachable ⇒ DATA-ABSENT with
  attempt log.
- **N3-K:** renewable wedge p50 < 300 MW at the miss set OR not
  attributable to a specific uncarried published limit ⇒ documentation
  verdict (topology-class residual; GTC map stands).
- **N4-K:** P0a = 0 interpolated miss-set hours AND |P0b wedge| p50
  < 100 MW ⇒ demand-side measured-faithful; no build.
- **N5-K:** uncarried-class (hydro + other) p50 < 100 MW at the miss set ⇒
  BELOW-MATERIALITY; the `.` cells stand.
- **N1a has NO kill precondition** — it is buildable with on-disk (or
  keyless-fetchable) data and is SOLVED regardless of every screen
  (Amendment 3; the solve IS the measurement of its predicted inertness).
(The 100/300/500-class MW thresholds are ex-ante materiality floors of the
same family as ercot-226 §5.4 — small against the 2.7 GW wedge and chosen
before any measurement; none is tuned.)

### 5.5 Single-factor ADOPTION criteria (official basis — unchanged from
ercot-226)
- C3a-2023 improves ≥ 1.5 pp toward zero vs keeper −39.7 %;
- C3b-2023 ≤ 0.729 + 0.005;
- improvement window-concentrated and calm-fortnight clean (≤ +2 pp);
- channel attribution clean (λ-carried; no adder-carried improvement;
  G-SHORTFALL subset holds);
- G-CAP / G-SHED / G-BAT / G-D2 clean; G-SPUR banded within bar (lidless
  reported both forms);
- C8/D-2 forced-share clean, no new D-4 rows.
A factor that is measured-inert or that fails any gate stays default-off
with its verdict recorded (matrix cell + probe JSON + FINDING). A factor
that is inert on the scored digits but strictly more structurally faithful
(N1a's expected posture) is NOT self-adopted: it is named in the handback
for the owner's structural-standard call, with the flag left off — the
ercot-230 disposition, not the ercot-221 one, is the default here.

### 5.6–5.7 Combined-run and retention rules
As PRECOMMIT-ercot226 §5.6, plus: any adopted factor whose driver is
nonzero in 2024/2025 (N1a, N4a, N5a) replaces the sha-identity invariance
branch with explicit official scoring of 2024/2025 in the 3-year run
(G-OWNER retention: +0.4 % / 0.131 / 22 h and −7.6 % / 0.099 / 1 h remain
PASS); factors with 2023-keyed drivers keep the sha-identity branch.

### 5.8 Promotion / termination rule
If any factor clears §5.5, the combined 3-year path runs and W-4-style
promotion is escalated with the full keeper workflow (the X-2 keeper-file
prose rewrite and the ercot-216 C3c OPEN-RESIDUAL-LANE re-wording are owed
at the next promotion — charter deliverables). If NO factor clears —
the pre-registered expectation — the handback names each factor's verdict
verbatim and puts the §0 termination question (Door D restore vs the
seasonal-term card) to the owner. Borderline mechanical verdicts escalate,
never self-adjudicate.

### 5.9 The probe JSON schema
`results/calibration/ercot231_probe_<factor>.json`, the ercot-226 §5.9
schema with `probe: "ercot231"`, plus per-factor Phase-0 blocks
(`phase0 {...}` carrying the §5.4 measurements and, for documentation
rows, the attempt log in the ercot-228 `phase_a_attempt_log` form). Factors
terminating at Phase-0 commit a JSON with `arm: null` and
`verdict {adoption_pass: false, failed_criteria: [<kill id>]}`. Every
factor in §2 gets exactly one JSON — solved, documented, or killed — so
the FINDING's factor table is fully artifact-backed.

## 6. PRIORS (pre-registered expected branches)

- **P-1:** miss-set interchange is a net IMPORT at a large fraction of
  capability (the 2023 summer pattern) ⇒ N1b-K fires; N1a proceeds to its
  solve regardless.
- **P-2:** N1a is MEASURED-INERT on the official digits (zonal
  re-placement of ≤ ~1.2 GW cannot move system λ at uncongested top hours;
  any movement is confined to zonal dispersion within G-SPUR bands).
- **P-3:** N2 terminates ALREADY-CARRIED + N2a DATA-ABSENT; N2b stands
  refuted by the item-20 measurement without a solve.
- **P-4:** N3's wedge attributes to the reduced-network topology class ⇒
  N3-K documentation verdict.
- **P-5:** N4's integrity checks are clean (0 interpolated hours, wedge
  < 100 MW) and N5's uncarried classes are < 100 MW ⇒ both documentation
  rows.
- **P-6 (the program verdict):** no factor clears §5.5; the program
  terminates **MEASURED-EMPTY**, completing the tightness side per §4, and
  the handback puts the owner disposition question. The deliverable is the
  completed enumeration with every verdict artifact-backed — the charter's
  own framing.
- **P-7 (honest risk):** any P0 measurement that surprises (a multi-GW
  demand or interchange wedge, a material uncarried class) sends its factor
  to the solve path and is reported at full magnitude — that is what the
  measurements are for.

## 7. EXECUTION PROTOCOL

Single-session (no spokes). Order: this precommit pushed + blob-verified →
Phase-0 measurements (§5.4, all factors) → N1a fetch + build (field,
defaults, cache key, tests, matrix row + all-shard cells in the build
push) → control replay + G-REPRO → N1a arm solve → conditional arms
(N4a/N5a/N3 map-completion) only if their preconditions fire → probe JSONs
+ gates JSONs → FINDING + matrix ERCOT-cell stamps for everything tested
(rejections included) → calibration-log entry (consumes ercot-231; next
shorthand ercot-232; ercot-199 remains unclaimed) → handback. Fences:
years ⊂ {2023, 2024, 2025} with solves 2023-only under W-2 (rule 22; ERCOT
holds no `complete` marker — no 2022, no 2019, no H1-2026); ERCOT shards
and curves only (rule 25); blob-verify every pushed file ≥ 300 lines
(rule 27); `check_mechanism_matrix.py` exit 0 before every push (rule 28);
no CI solves, no new workflows, no PR; `git fetch origin main` + rebase
before every push; HTTP/1.1 fallback before any pack-size conclusion.

## 8. THE 2022 DUAL-CONFIG STANDING PROTOCOL (record only — NOT executed)

Unchanged from PRECOMMIT-ercot226 §7 / FINDING-ercot227 §9: ERCOT holds no
`complete` marker, so 2022 is untouched. When authorized, 2022 runs the
frozen keeper recipe under the pre-ECRS design against the same
measured-overlay discipline; N1a's driver (measured 2022 flows) would
regenerate from the same EIA-930 product if the flag is ever armed.

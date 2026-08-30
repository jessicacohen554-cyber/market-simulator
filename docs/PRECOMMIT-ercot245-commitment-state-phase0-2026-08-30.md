# PRECOMMIT — ercot-245 Phase-0 (2026-08-30): the PER-CLASS commitment-state (slow-start reachability) bound — zero-solve identification on the delivery-2023 all-resource SCED corpus + the FORWARD keeper's committed sidecars, chartered, constructed and kill-gated BEFORE any measurement

**Owner authorization: the ercot-245 session handoff (2026-08-30) IS the owner
charter that `FINDING-ercot244-online-cap-phase0-2026-08-30.md` §3 requires**
("a per-unit/per-class commitment-state representation of slow-start
reachability … a structural LP change needing its own owner charter and
precommit"). It charters a Phase-0 zero-solve identification of a PER-CLASS
availability-shaped reachability bound and licenses ONE forward-span A/B
(Phase-1, its own separate precommit) ONLY if this Phase-0 passes its own
declared kills. This document is pushed and blob-verified before any
measurement runs. Branch `claude/ercot-245-commitment-state-bzqneg`.
ZERO-SOLVE: no LP, no ScenarioConfig change, no matrix verdict move, the
two-config keeper untouched.

## 0. Standing verdicts this lane builds on, and what it may NOT touch

1. **The aggregate online-capability ceiling family is DEAD and stays dead.**
   `energy_online_capability_cap` ERCOT cell `R` (ercot-159 in-solve
   over-fire) + KILLED-AT-CENSUS (ercot-244: K-B reach 3/36, 3/31; K-C
   ordinary binds 979/858; K-A clean; every V-0 anchor exact). This lane
   never re-arms, re-grains or re-censuses ANY aggregate-RHS variant. The
   ercot-244 adjudication is this lane's premise: the defect is **HEADROOM
   ACCESS** — which cold slow units are reachable within the operating hour —
   and on a composition-correct keeper the model sits UNDER the aggregate
   measured ceiling at 33/36 and 28/31 missed hours, so any repair must
   discriminate at a grain the aggregate form cannot: per class.
2. **The ercot-163 refutation is acknowledged as the strongest standing
   prior AGAINST commitment-state discrimination, and is distinguished, not
   litigated.** ercot-163 (2026-08-04) measured the 2023 top-100 gap hours:
   the CC fleet was 96.4 % committed / 98.0 % loaded, offline-startable CC
   was 0.020 GW, and the "~8 GW cheap offline CC block" was a DAM-status
   artifact — NO commitment-state mechanism was chartered for THAT object.
   That object was the 2023 Aug/Sep afternoon energy-stack family (83/100
   hours Aug/Sep h12–19), which today belongs to the CALIBRATED zero-caveat
   2023 carve-out and is NOT this lane's object. This lane's object is the
   FORWARD span's evening/event misses, where the standing measurements run
   the other way: 17.05–22.94 GW of thermal HSL offline at evening events
   with real online cushions 0.92–2.80 GW (matrix §5.1 item 9 card), and the
   model's slow+held point above the measured TOTAL online capability in
   ~11 % of forward-span ordinary hours (ercot-244 §2.3). Whether per-class
   state discriminates the FORWARD misses is exactly what this census
   measures; ercot-163's result is carried as the reason the reach prior
   below is stated LOW-TO-UNCERTAIN, not as a fence.
3. **The ercot-241/242 adjudication supplies the direction:** the λ-band
   tight-room dependence is POSITION/PARTICIPATION-carried (paired Δ at
   0.9×HSL = +$0.20 CC / +$0.52 CT); three offer-side negatives stand
   (graded ladder R, room axis R, ercot-161/217 closures). The repair
   direction is the populations that carry the λ-band — participation /
   commitment state — never CC/CT repricing. This lane is that direction's
   Phase-0, from the quantity side.
4. **DO-NOT-REDO fence (this lane touches none of these):** the aggregate
   online-capability family — any RHS variant (ercot-244, on top of
   ercot-159 R); release-guard exit condition (KILLED, ercot-243); room-axis
   offer surface (R, ercot-242); graded static peak_ladder (R, ercot-239 r2
   FINAL); ercot-219 option-b (R); storage RT offer surface (R, Door A);
   topology splits (G); cross-year seed (R); adaptive fixed point (inert,
   ercot-230); seasonal end-of-season term (ercot-232); ORDC/adder channel
   closures; ercot-178/-180 grains (R); lowcurve/negative-offer variants;
   the demand-gap object (CLOSED, ercot-240: DC-tie identity). The
   ercot-239…244 committed measurements are READ, never re-run.
5. **Q-B FINAL / two-config discipline:** the keeper partition is untouched
   (forward `2026-08-25-234-eastex-identity` on {2024, 2025} + carve-out
   `2026-08-25-236-swcap-clip-k33` on 2023). No C3a-2023 spend; every 2023
   read below is identification or report-only context, never a score.

## 1. Object and basis

* **Object:** the FORWARD span's ledgered C3c missed-event tail, official
  basis reproduced verbatim (`ercot226_official_score.py` convention as
  re-implemented by the ercot-244 probe, reused): model tail = hours with
  MAX ZONAL system-sidecar `price` > $200 (NaN → −inf); actual tail = hours
  with `actual_lmp_hourly_ERCOT.parquet` `rt` > $200. **Missed set
  `M_y = {t : actual_rt > 200 ∧ model_maxzonal ≤ 200}`.** Committed
  populations this census must reproduce EXACTLY: |M_2024| = 36,
  |M_2025| = 31 (+ report-only |M_2023| = 115), model tails 22/1, actual
  tails 53/31 (`results/calibration/ercot244_online_cap_phase0.json`).
* **Model basis bundle:** the committed FORWARD keeper
  `results/calibration/ercot234_eastex_identity` (span verdict CALIBRATED on
  {2024, 2025}; C3c the lone ledgered caveat ×2). Its committed hourly
  sidecars are the model side; no solve, no replay. The bundle's 2023 year
  is the registered NOT-YET record's year (C3a-2023 −39.7 % on this config;
  the carve-out covers the year) — every 2023 model-dispatch-dependent
  number below is therefore DIAGNOSTIC-ONLY, never a gate.
* **Measured identification basis (the charter's list):** the delivery-2023
  all-resource NP3-965 SCED corpus (`data/raw/ercot/SCED/`, the ERCOT-157
  window, 323 tracked shards, 35.82M delivery-2023 rows, all 365 days);
  `rtolhsl` all three years (`ercot_<year>_ordc_reserves_hourly.parquet`);
  the EIA-930 wide extract (`ERCO hourly.parquet`, the ercot-243 mapping
  convention reused verbatim). **Validation-only supplement, declared here
  because it is tracked repo data at tip and the item-9 card designates the
  extracts "validation only":** the delivery-2025 tail-day extract
  `data/raw/ercot/60_DAY_SCED_DISCLOSURE_60d_SCED_Gen_Resource_Data_2025_
  ercot86_tail_days.parquet` (11 delivery days: 01-15, 02-19, 02-20, 05-16,
  05-30, 07-01, 07-11, 07-30, 10-21, 12-01, 12-15). It enters ONLY as
  transfer validation (T-1/T-3) and direct report evidence (D-V4/D-V5) —
  never as identification input, never as a fit input. The three companion
  extracts (2024 tail/control, 2025 control) are GITIGNORED and not on disk;
  they are NOT fetched (re-fetch is data intake — the §8 owner flag). The
  2024/2025 full all-resource corpus stays UNFETCHED and UNCHARTERED.
* **Scored years {2024, 2025}; 2023 identification + report-only.** Prep is
  unrestricted, spend is gated (rule 22 SPEND-ONLY): every read is years ⊂
  {2023, 2024, 2025}; no `--holdout-authorized` anywhere; the freeze stays
  untouched. Probe env: the keeper-pinned venv outside the project dir
  (python 3.11, pandas 3.0.5, pyarrow 25.0.1, numpy 2.4.6).

## 2. The constructions (fixed a priori; grading never re-selects them)

### 2a. Census classes — the grain the measurement supports

Four census classes k, each a (measured SCED `Resource Type` set ↔ model
set) pair. The SCED grain does not split CHP from merchant trains and does
not split PRB from lignite, so the census grain is technology-class:

| k | measured restypes | model F side (`class_hourly` klass) | model capability side (`plant_group`) |
|---|---|---|---|
| CC | CCGT90, CCLE90 | CC_REGULAR | CC_REGULAR |
| ST | GSREH, GSNONR, GSSUP | ST_GAS | ST_GAS |
| COAL | CLLIG | COAL_PRB + COAL_LIGNITE | COAL |
| NUC | NUC | nuclear (case-insensitive) | NUCLEAR (case-insensitive) |

* **CHP model classes (CC_CHP, ST_CHP) are EXCLUDED from the primary F side**
  (an unknown share of ERCOT cogeneration never telemeters to SCED — the
  ERCOT-151/163 crosswalk discipline). Measured sides keep every visible
  train of the type. Both choices are LOOSE-side for an upper-bound census
  (F smaller, CAP larger → fewer binds): the construction is biased toward
  inertness (K-B), never toward the ercot-159 over-fire, mirroring the
  ercot-244 design principle. The class-whole variant (CHP dispatch added,
  the `ERCOT_HELD_CLASS_GROUPS` precedent) is disclosed diagnostic D-V2.
* **Quick-start classes are NEVER capped** (SCGT90/SCLE90/DSL; model
  CT_PEAKER/CT_CHP/oil): rule 18 physics gating — the fast-start pool owns
  the offline-quick route, and the real market reaches its offline quicks
  within the hour. Storage, renewables, hydro: out of scope.

### 2b. Measured per-class state series (delivery-2023 corpus; 2025 extract days)

Committed conventions imported/reproduced VERBATIM from
`scripts/probes/ercot163_cc_commitment_state_census.py`: `_train`
(configuration-alias collapse — the ERCOT-151 config-inflation trap),
`_state_of` (telemetered status → {ONLINE, ONTEST, OFFLINE_STARTABLE,
OFFLINE_OTHER, OUT, TRANSITION, OTHER}), `_hoy` (SCED timestamp → fixed-CST
hour-of-year), and the `_cap_ref` construction (per-TRAIN p98 of ALL
telemetered HSL rows over the delivery year) applied to the widened
slow-class universe of §2a. Shard selection and delivery-year row filtering:
`derive_ercot_sced_offer_wall._sced_source_files` / `_delivery_year_rows`.
Per class k and hour t (hourly mean over the hour's SCED intervals):

    OnlineHSL_k(t)    = Σ telemetered HSL over rows with state ∈
                        {ONLINE, ONTEST, TRANSITION}
    StartableHSL_k(t) = Σ telemetered HSL over rows with state
                        OFFLINE_STARTABLE (OFFQS/OFFNS)
    CAP_k^meas(t)     = OnlineHSL_k(t) + StartableHSL_k(t)
    AvailRef_k(t)     = Σ cap_ref over trains whose state ∉ {OUT, ABSENT}
    ColdRef_k(t)      = Σ cap_ref over trains with state ∈
                        {OFFLINE_OTHER, OTHER}   (reported: the cold depth)

CAP_k^meas is the REACHABLE capability: what was online (ONTEST and
startup/shutdown transitions included — loose-side) plus what could come
online within SCED's horizon (the ERCOT-88 pool states). EMR and other
unmapped statuses land in OTHER = cold (their magnitude is reported; no
2024/2025 missed event was an EEA deployment). An hour with zero corpus
intervals → NaN, excluded from every census count (reported). The same
constructions run on the 2025 extract for its 11 delivery days, with a
per-day column-completeness assert (the 12-01/12-15 days may carry
RTC+B-format rows; a day whose required columns {SCED Time Stamp, Resource
Name, Resource Type, Telemetered Resource Status, HSL} do not read is
EXCLUDED and the exclusion reported — a declared coverage seam, never a
silent drop).

### 2c. Model-side per-class series (the committed sidecars + no-LP fleet reconstruction)

    F_k(t)          = Σ class_hourly `mw` over the k's klass set (P1)
    AvailModel_k(t) = Σ over fleet units g with plant_group ∈ k's set of
                      pmax[g] × availability[g, t]
    spare_k(t)      = AvailModel_k(t) − F_k(t)   (reported)

`AvailModel` comes from `scripts.lib.bundle_fleet.reconstruct_bundle_fleet`
on the forward bundle (fidelity-guarded, NO LP — the ercot-163/169/170
precedent), years sequential. **F is dispatch-only** — per-class AS-held
attribution does not exist in the sidecars (`reserve_family.reserve_class`
is a tier index). This is again loose-side: omitting class-held AS
understates F_k and can only miss binds. Disclosed diagnostic D-V1 adds the
ercot-244 `held_fast` total attributed to classes proportionally to their
share of slow dispatch (a constructed attribution — report-only, never
gating). "Binds" (zero-solve counterfactual, the ercot-244 grammar):
`F_k(t) > CAP_k(t)` at whichever grain is being censused; `B∪(t)` = any
census class binds at t; depth d_k = F_k − CAP_k.

### 2d. The transfer structure (2023-identified; zero fitted scalars)

The commitment-share relation, identified on 2023 measured data ONLY:

    nl(t)   = EIA-930 `Demand` − nan0(`NG: WND`) − nan0(`NG: SUN`)
    bins    = the 10 equal-count bins (deciles) of nl over the 2023 year;
              2024/2025 hours binned on the SAME 2023 edges, end-clamped
    c_k(b)  = Σ_{t∈b} CAP_k^meas(t) / Σ_{t∈b} AvailRef_k(t)      (2023)

Applied to the scored years:

    ĈAP_k,y(t) = c_k(b(nl_y(t))) × AvailModel_k,y(t)        y ∈ {2024, 2025}

Ten bins, one driver, ratio-of-sums per bin: no coefficient, margin, trim or
grain choice is available to fit (rule 23/24); the driver (net load) and the
denominator (the model's own availability-derated class capability) both
regenerate for a forecast year from forward drivers. NO season, hour-block
or lag conditioning — deliberately minimal, and deliberately NOT the
ercot-159 envelope grain. If commitment has memory/dynamics this form cannot
express, the transfer validation below fails HONESTLY and the lane records
it. Note the transferred instrument has no NaN seam of its own (nl and
AvailModel cover all 8760, including the 2025 RTC+B tail the aggregate form
had to exclude); T-2 alone inherits the rtolhsl NaN exclusion.

### 2e. The Phase-1 LP form (named now, built only if licensed)

A NEW row family `class_online_cap`: per census class k and hour t,
`Σ_{g∈k} P[g,t] ≤ ĈAP_k(t)` — 4 × 8760 availability-shaped upper-bound rows
over the generator P columns of the class members (vectorized, rule 2). NO
MIP, no integer state. Working ScenarioConfig field
`ercot_class_online_reachability_cap` (registered, default off,
backcast-mode-only: forecast → uncapped, the G4 seam; matrix row mode `B`;
final name + matrix row per `[R-MECH-MATRIX]` duty (c) in the Phase-1
precommit). Mutual exclusivity: hard error with every
`online_capacity_envelope` variant, with `ercot_ordc_only_scarcity`, and
with the retired `ercot_energy_online_capability_cap` gate.

## 3. `[R-FLOOR-WINDOW]` triple and `[R-MEASURED]` admissibility

* **(a) Driver:** ERCOT's real per-class commitment/online state — settled
  operator telemetry (NP3-965 telemetered resource status + HSL), not a
  price, not a dispatch outcome. Slow-start offline capability (min-down
  ≥ 4 h, startup ≥ $35/MW — unit physics, rule 18) is physically unreachable
  within SCED's horizon; OFFQS/OFFNS capability is reachable and is credited
  inside CAP.
* **(b) Binding window and why:** hours where the model's class dispatch
  exceeds the class's reachable (online + startable) capability — on the
  standing measurements, tight/event hours where reality committed lean and
  met the margin with quick-start/storage/import routes while the LP leans
  on cold slow capability. In ordinary hours the class caps must sit slack
  (the model's committed level below the class's typical online share).
  **The census IS the window verification** (the ercot-244 grammar): material
  ordinary-hour binding is the off-window signature and is kill K-C — a
  bound binding where its own driver evidence says the constraint was slack
  is a bug by definition, whatever it does to any residual.
* **(c) Forward story (rule 13's regeneration test):** the per-class online
  share regenerates forward as c_k(net-load bin) × the model's own
  availability-derated class capability — every input regenerates and
  responds to changed conditions (fleet change moves AvailModel; load/VRE
  growth moves the bin index), on the exact staged pattern of the armed
  reserve-side incumbent (`ercot_rtolcap_supply_cap_mw` → forward share
  formula). The model's own commitment layer (P0-detected run patterns + the
  physics-gated bridges) is the structural generator of online state
  forward; at Phase-1 the mechanism is backcast-mode-only, exactly like
  CAMPD outage windows — a measured physical availability state, admissible
  because the same quantity is producible for a forward year from forward
  drivers. The measured 2023 identification is collected once and applied
  consistently (rule 22: data is never held out; the spend gates only
  looking at out-of-training answers, and every read here is in-window).

## 4. Rule-19 `[R-ONE-MECH]` reconciliation (enumerated before any seam; precedence explicit, nothing stacked)

* **The DAM availability lane** (`ercot_thermal_dam_availability*` +
  partial-outage shaping + non-CAMPD/nuclear availability, armed) owns
  OUTAGES: per-unit derates on generator bounds. This bound owns ONLINE
  STATE among available units. The share c_k is outage-CLEANED on both sides
  by construction (numerator excludes OUT; denominator is cap_ref of
  non-OUT trains; applied against the availability-derated AvailModel), so
  the mechanisms compose without double-derate: physically, dispatch ≤
  online ≤ available ≤ installed.
* **The commitment bridges + posture floors** (`ercot_gas_commitment_bridge`
  min_load 0.574, `ercot_commitment_posture_min_load_frac`,
  `ercot_coal_min_config_floor`, `chp_export_floor_measured`, armed) own the
  LOWER bound at the P0→P1 seam. This family is the upper-bound counterpart:
  floors sit far below the class caps by construction (floor ≈ 0.574 ×
  committed-CC ≤ attained dispatch ≤ online capability). At Phase-1, P0
  solves WITH the caps so the bridges detect capability-consistent run
  patterns — composition through the existing seam. Never stacked; VOLL
  slack remains the LP's escape and is guarded at Phase-1 (zero-new-shed
  kill). The default-off measured commitment mechanisms
  (`ercot_ruc_commitment_floor` — ONRUC-instructed LSL floors;
  `ercot_as_held_location` — measured class-held AS) are NOT armed in the
  forward keeper; they are lower-bound/holding objects on the same driver
  and, were any ever co-armed, the floor ≤ cap nesting is physical and the
  writer of each side stays single.
* **The reserve supply cap** (`ercot_reserve_supply_cap` + `_net_credits`,
  armed) owns the RESERVE side (Σ R ≤ credit-netted measured RTOLCAP
  tiers). This family bounds per-class ENERGY dispatch only (F is
  dispatch-only by declaration), so the two are disjoint at the variable
  level and physically nested at capability level (procured AS ≤ online
  responsive capability; output ≤ online HSL). The credit series stay owned
  by the reserve machinery. D-V1 reports how much tighter class caps would
  read if class-held AS were attributed — report-only.
* **The fast-start pool** (`ercot_faststart_pool_offer`, armed) owns the
  offline-QUICK price route; quick classes are never capped here (§2a). The
  measured OFFQS/OFFNS capability of SLOW classes is credited inside
  CAP_k^meas, so the pool's population and this bound's population overlap
  nowhere (slow startable ≈ 0.02 GW measured, credited not capped).
* **The RT offer wall** (`ercot_offer_surface_cleared_share_rt`,
  mode=replace, armed) owns the PRICE of the online spare ladder; this
  family owns the QUANTITY of slow capability reachable — the ercot-241/242
  adjudication made structural: move the model's reachable POSITION
  honestly (a quantity bound) instead of re-pricing curves (the refused
  arm). ORDC/adaptive/ECRS machinery untouched; interactions flow through
  the LP's own arithmetic.
* **The aggregate `online_capacity_cap` LP slot** (`ReserveDesign`, retired
  R): never re-armed; the Phase-1 form is a NEW per-class row family with
  hard mutual exclusion (§2e).

## 5. The census (every quantity below is committed to the probe JSON; nothing else is measured)

Probe `scripts/probes/ercot245_commitment_state_phase0.py` →
`results/calibration/ercot245_commitment_state_phase0.json`.

* **V-0 anchors (measured first; any failure = STOP-AND-INVESTIGATE, no
  census is graded):**
  (a) model max-zonal tails reproduce 22 (2024) / 1 (2025) and actual tails
  53 / 31 EXACTLY; |M_y| reproduces 36 / 31 EXACTLY (and 115 for 2023
  report) — the ercot-244 committed populations;
  (b) EIA-930 lag-0 demand alignment (the ercot-243 assert, all years);
  (c) rtolhsl hod-17–21 means within ±3 GW of the card's 58.87 / 62.64 /
  67.81 GW;
  (d) corpus series identity: hourly Σ over ALL resource types of
  OnlineHSL (2023) vs measured `rtolhsl`: Pearson corr ≥ 0.985 and
  |median gap| ≤ 3 GW — the same-telemetry reconciliation;
  (e) capability-universe identity: the widened `_cap_ref` CC total
  reproduces the committed ercot-163 `fleet_cap_ref_gw` CC = 35.2601 GW
  within ±2 %;
  (f) extract identity: the 2025 extract parses exactly 11 delivery days;
  the count of M_2025 hours covered by readable extract days is REPORTED —
  coverage ≥ 16 of 31 makes T-3 gradeable (below the floor, T-3 is recorded
  N/A-coverage-limited, which is itself a §8-flag datum, not a kill).
* **Universe anchors (2023 annual means, per class; outside band =
  stop-and-investigate as a mapping/series identity question, not an
  adjudication):** AvailRef_k / AvailModel_k ∈ [0.80, 1.60]. (Measured ≥
  model is expected — visible cogens ride inside the measured universe for
  CC/ST; a large shortfall means the restype↔plant_group crosswalk is
  mis-scoped.)
* **Census rows, per grain and year:** the direct 2023 grain (F_k vs
  CAP_k^meas — DIAGNOSTIC-ONLY, the miscalibrated-year caveat); the direct
  2025 extract-day grain (F_k vs CAP_k^meas over covered hours); the
  transferred grain (F_k vs ĈAP_k, full 8760, scored years). For each: per
  class and union |B|, |B∩M|, |B∩hit|, |B∩ordinary| (actual < $150),
  |B∩buffer|, away-binds (model_dw ≥ actual, the ercot-244 direction
  convention), depth p50/p90 over B∩M and B∩ordinary, NaN/uncovered hour
  counts, and the per-hour records for every t ∈ B∪∩(M∪H).
* **Transfer validation (graded, §6 K-T):**
  T-1: per class, over readable 2025 extract-day hours:
  median |ĈAP_k − CAP_k^meas| / CAP_k^meas ≤ 0.15;
  T-2: containment against the ercot-244 aggregate
  CAP_agg = rtolhsl − Σ nonthermal EIA-930 netgen (construction reused
  verbatim, finite-rtolhsl hours only): hours with Σ_k ĈAP_k > CAP_agg
  ≤ 5 % of finite hours per scored year AND p95 overshoot ≤ 2 GW
  (corr reported, not gated);
  T-3 (gradeable only at coverage ≥ 16/31): any-class bind agreement
  between direct and transferred grains on covered M_2025 hours ≥ 60 %.
* **Disclosed diagnostics (report-only; none armable; no grading reads
  them):** D-V1 held-attribution variant (F_k + held_fast × class share of
  slow dispatch); D-V2 class-whole variant (CHP dispatch added to F);
  D-V3 the direct 2023 census (miscalibrated-year caveat); D-V4 the
  per-class headroom decomposition at covered M_2025 hours (model F/Avail/
  spare vs measured OnlineHSL/ΣBasePoint/spare/ColdRef — the forward-span
  per-class version of the card's 17–23 GW cold measurement); D-V5
  reality-side discrimination (measured per-class online share at covered
  M_2025 hours vs ordinary extract hours in the same net-load bins).
* **Priors (report-graded, not kills):** |M| exact anchors above; extract
  coverage expected ≥ 24/31 (the extract was built as the ercot-86 tail-day
  set). Reach prior: LOW-TO-UNCERTAIN — ercot-163 measured reality's slow
  fleet near-saturated at (2023) events, and this bundle's composition is
  correct on the span, so per-class binds at M require compositional skew
  the aggregate census could not see; the lane's decisive value is the
  adjudication either way. K-C prior: MATERIAL RISK — the standing ~11 %
  aggregate ordinary-hour excess (slow-heavy composition) may concentrate
  per-class; if it does, the kill fires and that IS the verdict (the
  instrument-form is wrong for the object), not a tuning invitation.

## 6. Kills (declared ex ante; graded on the scored years only; ANY kill ⇒ record and STOP — no Phase-1, no solve, the A/B license is never spent)

* **K-A — construction invalidity.** (i) CAP_k^meas ≤ 0 in more than 24
  covered 2023 hours for any class; (ii) F_k > CAP_k^meas in more than 25 %
  of covered 2023 hours for any class (mass violation at the measured grain
  = the restype↔class mapping or series is mis-scoped — the model's class
  energy passes C1 in all three years, so a quarter-of-the-year violation
  cannot be conduct); (iii) any V-0 / universe anchor failure that
  investigation attributes to the construction itself (the
  stop-and-investigate route resolving against the lane).
* **K-B — no reach.** On the transferred grain, |B∪∩M_y| / |M_y| < 0.20 in
  BOTH scored years. (The ercot-244 floor, unchanged, on the union across
  the four class bounds.)
* **K-C — off-window binding / away-from-actual (the over-fire signature,
  killed zero-solve).** On the transferred grain, in EITHER scored year:
  (i) |B∪∩ordinary| > 150; or (ii) |B∪∩ordinary| > |B∪∩M|; or (iii)
  away-binds > |B∪| / 3.
* **K-T — transfer invalidity.** T-1, T-2 or (where gradeable) T-3 fails.
  The 2023-identified structure does not transport to the forward span at
  the grain the on-disk data can check; the finding names the 2024/2025
  all-resource corpus intake as the identification unblock (§8) and the
  lane STOPS — the intake decision is the owner's, never a workaround.
* **K-E — non-expressibility (the charter's named kill).** If the
  constructions are valid (no K-A) and the reach/window/transfer kills
  still fire, the FINDING must adjudicate which residue killed: (grain) a
  per-class bound is too coarse and only per-unit forward-regime state
  could discriminate — the 2024/2025 corpus intake is the named owner ask;
  or (form) no admissible pure-LP availability-shaped bound can express
  headroom-price reachability on a composition-correct keeper at ANY grain
  — recorded as the structural conclusion for the owner, with the C3c
  ledger carried at full magnitude. Either way: record and STOP.
* Kills are direction-blind and the thresholds above are frozen: no
  post-hoc re-selection, re-scoping, re-binning or year-scoping to dodge a
  fired kill (rule 20). A fired kill is recorded at full magnitude in the
  FINDING, the matrix item-9 card and `energy_online_capability_cap` cell
  take an appended evidence note (the ercot-243/244 note-append precedent —
  no verdict move without a tested mechanism), and the calibration-log
  entry lands either way.

## 7. Decision rule and deliverables

* **All kills clear ⇒ Phase-1 opens** under the charter's own terms and
  ONLY those: a SEPARATE pushed + blob-verified precommit BEFORE any solve
  or derive; the mechanism as the registered default-off ScenarioConfig
  field of §2e with its matrix row added per duty (c), zero
  fitted-to-residual content; ONE forward-span A/B — control = replay of
  the committed forward keeper with G-REPRO (control sidecars sha-identical
  to the committed bundle BEFORE the arm is read), arm = the single delta;
  solve 2023 2024 2025 SEQUENTIALLY on the keeper's recorded env; score
  `--years 2024 2025`, 2023 side-effect-reported (two-config discipline).
  Phase-1 kills, declared now and frozen: C3a/C3b 2024 AND 2025 retained
  PASS; C3c no-worsen per year and the target counts must IMPROVE toward
  53/31 (else inert-recorded); ZERO new shed hours; lidless spur
  no-increase (either year); off-season intact; coal ≤ +0.5 TWh; CT/ST
  within ±1.0 TWh; G-BAT; G-REPRO; G-D2/D-4 with the mechanism's window
  declared explicitly (a commitment-state bound is floor-adjacent — its
  D-4 exposure is real). Both runs registered whatever the outcome
  (rule 15), matrix cell + calibration-log entry ercot-245 in-session.
  **BORDERLINE VERDICTS AND ANY KEEPER CONSEQUENCE ESCALATE TO THE OWNER,
  NEVER SELF-ADOPTED.**
* **Any kill fires ⇒** FINDING-ercot245 records it at full magnitude, the
  evidence notes land, log entry, STOP.
* **Amendment convention (the ercot-243/244 precedent):** implementation
  repairs that leave every declared construction unchanged (a column
  spelling, a dtype, an assert running on finite rows) are recorded in the
  FINDING as notes; any construction-affecting surprise is an AMENDMENT
  pushed before measurement proceeds.
* **Deliverable order (each pushed before the next starts; blob
  verification after every push touching a ≥300-line file):** (1) this
  precommit; (2) probe + JSON; (3) FINDING + matrix evidence notes +
  calibration-log entry; (4) Phase-1 (if licensed): precommit, then
  mechanism + tests, then A/B bundles + registration + payloads, then
  FINDING/log/matrix.

## 8. Owner-visible flag (not executed here, per the charter)

The 2024/2025 all-resource SCED conduct corpus intake (PRECOMMIT-ercot242
§6) remains the blocker on per-type forward-regime identification — the
per-unit/per-class online-state record for the exact years whose misses are
the object. The three gitignored probe-day extracts (2024 tail, 2024
control, 2025 control) are re-fetch-only and are NOT fetched here. If this
Phase-0 dies on identification coverage (K-T, or T-3 coverage-limited, or
the K-E grain adjudication), the FINDING names the intake as the unblock
and the decision is the owner's.

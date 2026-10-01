# FINDING — caiso-144: queue item 1 (the owed in-LP reserve co-opt test) is DISCHARGED EX ANTE — the builder the queue said to complete **is already complete in source**, and on the caiso-139 keeper's own committed bytes the completed design's requirement is covered with **≥ 854 MW of family-level slack in every one of 26,280 hours**, so every optimum of the armed LP carries zero shortfall and zero reserve duals. The caiso-137b overlay charter is ANSWERED NEGATIVE by measurement: the LOLP overlay fires in the WRONG hours (overlap with reality's tail: 1/47, 0/35, 0/8). The actual C3c tail is a WINTER-MORNING fuel/cold-snap tail the model prices at daily-spot SRMC ($138–181) — the residual above it is the probabilistic-RT premium the MISO/NEISO ledgers already name. **No in-model C3c lever remains; both blocked gates now sit on owner-level dispositions.**

**Keeper UNCHANGED:** `2026-07-29-caiso139-dump-guard-offer` (NOT-YET, fail
{C3a-2025, C3c-2023/24}). No LP built, no solver called, nothing armed, no
`ScenarioConfig` field added, no bundle produced — there is no keeper candidate
here. Instrument (committed): `scripts/probes/_caiso144_coopt_dormancy_gates.py`
(no LP, no solver; reads the keeper bundle's committed hourly sidecars, the
committed actual RT LMP series, the raw OASIS AS_REQ CSVs, and the design's own
constants from source).

---

## §A — the queue premise is STALE: the "incomplete" pergen builder was completed in source

Lever-queue item 1 (`docs/mechanism-testing-matrix.md` §5.2) reads "add
storage/hydro/RegUp-Down to the pergen builder first — documented gaps", citing
`docs/multi-iso/caiso-reserve-coopt.md` §"Documented gaps". Read off HEAD
source, two of the three gaps are **already closed**:

- **Storage** backs reserve through the duration-gated per-zone `RS[c,z]`
  columns (`_caiso_design` docstring: "Participation (issue #1492 design
  constraints 2/3, completed)"; ASSOC SOC gate at the published 30-minute
  sustain, `CAISO_AS_SUSTAIN_DURATION_H`).
- **Hydro** joins the pergen pool via `_caiso_reserve_eligible` (thermal
  `RESERVE_FUEL_TYPES` ∪ hydro) with its 10-minute deliverable ramp backfilled
  at `CAISO_HYDRO_RAMP10_FRAC = 1.0` (`caiso_pergen_structure`).
- **Regulation Up/Down** remains the one open gap, and stays walled as a
  *build*: no forward-derivable requirement series, and RegDown is a downward
  product the upward-headroom row does not model. It is however *measurable*
  (OASIS AS_REQ `RU_REQ_MIN_MW`), which is all §B needs.

The design-doc gaps section described the 2026-07-06 caiso-59 state, not HEAD
(`/sync-docs` fix applied with this finding). So "complete the builder, then
test" reduces to: **test the design as it stands** — which is decidable without
a solve.

## §B — the completed co-opt is EXACTLY inert on the caiso-139 keeper (no-solve proof)

Measured from the keeper's committed `unit_hourly_<y>.parquet` (per-unit `mw`
and hourly `cap_mw` = pmax × availability) + `system_<y>.parquet`, reproducing
the design's own arithmetic — pools = (zone, fuel) over eligible units with
ramp10 > 0; per-pool capability `min(Σ ramp10·avail, Σ (cap − P))`; requirement
`max(MSSC, 6 % load)` with the availability-aware plant-aggregated MSSC
(2,240 MW every year; Diablo Canyon):

| year | tier | min slack (MW) | p01 slack | mean slack | hours short |
|---|---|---|---|---|---|
| 2023 | T1 thermal-only (caiso-59 basis) | +285 | +2,863 | +8,670 | **0** |
| 2023 | T2 completed (+hydro) | **+854** | +3,765 | +12,019 | **0** |
| 2023 | T2 + flat max measured RegUp (1,200 MW) | −346 | +2,565 | +10,819 | 2 |
| 2024 | T1 thermal-only | +580 | +3,993 | +8,593 | **0** |
| 2024 | T2 completed (+hydro) | **+1,485** | +5,555 | +12,109 | **0** |
| 2024 | T2 + RegUp (744 MW) | +741 | +4,811 | +11,365 | **0** |
| 2025 | T1 thermal-only | +1,306 | +4,732 | +8,335 | **0** |
| 2025 | T2 completed (+hydro) | **+2,114** | +5,874 | +11,939 | **0** |
| 2025 | T2 + RegUp (894 MW) | +1,220 | +4,980 | +11,045 | **0** |

**Storage RS is EXCLUDED from every
supply tier**, so each slack is a strict lower bound on the completed design's
slack. The only two sub-zero hours anywhere (2023 h5442–5443, the Aug-16
evening peak, at the maximally conservative flat-1,200 MW RegUp tier) carry
**2,650 / 3,041 MW** of excluded storage-RS headroom (cap lower-bounded by the
year's own max realised discharge).

**Why this is a proof, not an estimate.** The reserve columns are costless;
shortfall steps are $100–700. At the keeper's optimum, allocate each pool
`R = cap_pool × req / Σcap` — every ramp bound and joint `P+R` row stays
*strictly* slack (Σcap exceeds req by ≥ 854 MW), dispatch unchanged, objective
unchanged. That extension is globally optimal (the energy part is already at
its unconstrained optimum and shortfall is avoidable at zero cost), and since
shortfall penalties are strictly positive, **every** optimum carries zero
shortfall; with strictly positive family slack the balance rows price at zero
by complementary slackness. The armed LP's prices and volumes are the keeper's,
up to the vertex degeneracy any re-solve already has. C3c contribution:
**exactly 0 hours**. The caiso-59 (~100 fired hours, 2023, thermal-only, on the
caiso-51-era keeper) and caiso-91 (scoped variant, duals $0 in all 26,280 h, on
caiso-90) measurements bracket this from both sides; on the current keeper even
the thermal-only tier never goes short.

**Disposition: queue item 1 is discharged ex ante — DO NOT SOLVE the A/B** (a
provably-inert arm is matrix code `I`, the caiso-137b rule). Matrix:
`energy_reserve_coopt` CAISO `U → I`, `reserve_pergen` CAISO `U → I`.

## §C — the C3c cross-check: the model is GW-deep in reserve exactly where reality was short

In the actual RT >$200 hours (the 47/35/8 hours C3c-2023/24 fails against and
2025's small-count passes against), the completed pool's slack is:

| year | n actual tail hours | min T2 slack in those hours | mean |
|---|---|---|---|
| 2023 | 47 | **+1,568 MW** | +10,246 |
| 2024 | 35 | **+1,632 MW** | +10,486 |
| 2025 | 8 | **+8,310 MW** | +9,373 |

No reserve co-optimization at ANY completion level can price reality's
scarcity hours while the model's own deliverable-reserve state there is slack
by 1.6–10.5 GW. **The in-LP route to C3c is closed as a matter of the model's
state, not of mechanism granularity** — the rule-19 "one scarcity owner"
question is now fully adjudicated on the in-LP side.

## §D — the caiso-137b charter question, answered by measurement: NO backcast overlay wiring

caiso-137b §4 left one question: should CAISO have a scarcity-pricing mechanism
in the scored backcast lane at all? The probe reproduces the forecast-path LOLP
overlay (`caiso_scarcity_overlay`: reserve_headroom → `LOLP × (VOLL − λ)`,
VOLL 2,000 / MCL 1,400 / σ 2,500) on the keeper's committed bytes with
`r_online` deliberately UNDER-stated (storage power cap lower-bounded by max
realised discharge; curtailed-VRE headroom excluded), so the adder is an
**over-estimate**:

| year | over-stated settle >$200 (dw λ) | actual RT tail | **overlap** | adder max IN actual tail hours | min r_online in tail hours |
|---|---|---|---|---|---|
| 2023 | 151 h | 47 h | **1 h** | $169 | 3,079 MW |
| 2024 | 71 h | 35 h | **0 h** | $73 | 4,266 MW |
| 2025 | 48 h | 8 h | **0 h** | $0.001 | 9,687 MW |

The overlay fires Apr–Nov in the hours the MODEL is tight, which are **not**
the hours REALITY was tight (winter mornings, §E): timing overlap ≤ 1 hour in
three years. Wiring it into the scored lane would (a) close nothing — 0 of the
2024 and 2025 actual tail hours are reachable even by the over-estimate — and
(b) invent a mis-timed tail (the real, non-bounded adder is far smaller —
caiso-137's counterfactual dw-means $0.14/$0.02/$0.0004 — but whatever it adds
lands in the wrong hours; 2025 would flip its current C3c small-count PASS
toward an invented-tail FAIL, the exact failure mode the rubric's small-count
guard exists for). **Charter answered: the backcast lane keeps NO scarcity
overlay.** This is a refusal on measurement, not on admissibility — matrix
`scarcity_pricing` CAISO note updated (the forecast-lane K is untouched).

## §E — what the actual C3c tail IS: a winter-morning fuel/cold-snap tail, already priced to its input ceiling

Decomposition of the actual RT >$200 hours (committed
`actual_lmp_hourly_CAISO.parquet`):

- **2023 (47 h):** 24 in January (hod peak 6–7 AM, 16/47 in hod 6–9) — the
  Dec-2022/Jan-2023 CA citygate blowout; 12 in Jul–Aug evenings; the rest
  scattered singles.
- **2024 (35 h):** 26 in January (overnight + morning + evening — the Jan-2024
  national freeze / MLK-weekend storm), 4 in July.
- **2025 (8 h):** Jan/Mar/Apr mornings (hod 5–9) only.

In those hours the model's energy-only max-zonal λ is mean $112/$123/$50, max
$181/$155/$62 — against actual RT mean $310/$283/$326, max $907/$897/$490. The
keeper **already carries the measured daily-spot fuel input at flow-date
placement** (`caiso_citygate_spot_level` + `caiso_citygate_flow_date`, both
armed): at Jan-2023's measured $16–18/MMBtu daily spot, marginal-HR SRMC is
$150–180 — exactly where the model prints. The wedge above it is the RT
premium above same-day fuel cost (deliverability/OFO events, cold-snap
WECC-wide import conduct, sub-hourly ramp formation) — the probabilistic /
administrative RT scarcity class that the MISO (miso101 ledger: "prices
probabilistic short-term risk a deterministic perfect-foresight hourly LP does
not contain") and NEISO ledgers already name, now with CAISO's own hour-level
corroboration: §C's 1.6–10.5 GW model reserve slack *in those hours*, and §D's
≤1-hour overlay overlap.

## §F — where this leaves the two blocked gates (the resolution map)

- **C3c-2023/24.** After this finding the in-model lever queue is EMPTY on
  every route: offer rungs (closed, caiso-131 §10), reserve tiers (closed, §B/
  §C), overlay wiring (refused, §D), fuel grain (already armed to its measured
  daily ceiling, §E). The live dispositions are exactly caiso-131 §9's A3/A4:
  - **A3 (data intake, unfunded):** the SoCalGas OFO declaration record —
    still the one intake that could make C3c-2024 reachable with an unfitted
    trigger; nothing in `data/raw/` carries it (re-verified this session).
  - **A4 (owner ledger):** ledger C3c-2023/24 as an ACCEPTED MEASURED-INPUT
    LIMITATION on the MISO/NEISO precedent (both ledgered, frontier-declared;
    CAISO carries 0 ledgered caveats against the budget of 3, and CAISO's
    evidence — §C/§D/§E — is now stronger than what either of those ledgers
    cited). Draft entries are staged in this finding's session log; adoption
    is an owner act (ERCOT-76 precedent: "ADOPTED LEDGER (owner, …)").
- **C3a-2025** is untouched by this finding and remains exactly where
  caiso-142/143 left it: diagnosed-unclosed, empty in-model queue, owner-level
  (land non-public hourly PS data, or accept — ledger or hold — per the
  nyiso-97-style call). Note the interaction caiso-131 §8 recorded: no C3c
  mechanism can be re-opened later that would spend C3a-2025's negative
  headroom.
- Ledgering C3c alone changes the determination only if C3a-2025 is also
  dispositioned: with C3c ledgered, C3a-2025 (+10.9 %, MODEL MISS) remains the
  sole NOT-YET blocker.

## §G — DO-NOT-REDO (new, binding)

- **Solving any CAISO backcast A/B on `energy_reserve_coopt` /
  `caiso_reserve_coopt` at any completion increment** (storage columns, hydro
  ramp, measured Reg add-on, posture/scoping variants). §B: family slack is
  strictly positive in every hour of every year at every tier on the current
  keeper — the arm is provably inert, and an inert arm is not solved (the
  caiso-137b rule). Re-open only on a keeper whose committed hourlies show the
  §B slack approaching zero (the probe re-runs in seconds on any bundle).
- **Proposing any backcast-lane scarcity overlay wiring for CAISO** (LOLP or
  derived): §D — timing overlap with the actual tail ≤ 1/90 hours over three
  years; it cannot close C3c and invents a mis-timed tail. (The forecast-lane
  overlay is untouched.)
- **Re-deriving the C3c tail as a summer-evening scarcity phenomenon.** §E: it
  is winter-morning fuel/cold-snap dominated (Jan 24/47, 26/35; hod 5–9).
- **Fuel-grain work aimed at C3c.** §E: the daily-spot + flow-date legs are
  already armed; the model already prints the measured daily-fuel SRMC ceiling
  in those hours. (pjm-139 W1's calendar-day scope bound also still applies.)
- Carried forward unchanged: every DO-NOT-REDO in FINDING-caiso143 §H,
  caiso-142 §K, caiso-141, caiso-138 §G, caiso-137b §6, caiso-131 §10.

Next number: caiso-145.

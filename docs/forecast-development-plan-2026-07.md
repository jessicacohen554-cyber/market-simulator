# Forecast Finalization Program (FF) — capacity expansion, retirement & forward validation

**Status: ACTIVE — the single coordinating plan for ALL forecast-side work.**
Produced 2026-07-17 (planning session — no LP solved, no parameter changed); verified
against `origin/main` HEAD `c95176e`. Every prior forecast plan is superseded as a
*coordination* document by this file (migration ledger §9); the absorbed lane docs remain
citeable as detailed technical specs where noted. Session labels here are `FF-<wave><letter>`;
prompts in §6. **Models: OPUS or FABLE only — Sonnet is never assigned in this program**
(CLAUDE.md rule 27; owner order).

**Owner charter (2026-07-17).** Finalize the forecast model and the capacity-expansion /
retirement infrastructure and test it iteratively — with the smallest possible solve
windows first. Initial testing uses **2026–2030 forecast-only** runs and **2023–2027
hindcast/forecast crossover** runs; only features/ISOs that pass the short-window gates
graduate to a **~10-year mid tier (2026–2035)**; only mid-tier passers reach the
**"golden" 25-year BAU solves (2026–2050)** — budgeted for as few attempts as possible.
Wall-clock frugality and agility govern every scheduling decision (§2.4). Hard
capacity-expansion design questions are grounded in commercial/academic practice
(GenX, ReEDS, US-REGEN, EPA IPM, PLEXOS, Aurora — §4) rather than invented locally.

---

## 0. Definition of done

The program is DONE when, per ISO:

1. A **golden 2026–2050 BAU bundle** exists, produced at HEAD defaults (plus the
   owner-decided DC-load posture), scored by the **forecast determination rubric** (§3)
   with no FAIL, registered on the forecast-validation dashboard with a
   **DOF-ledger attestation** (every free parameter → identification source; rule 21
   analogue), and reproducible from `run_config.json`.
2. The capacity-evolution skill claims are **measured, not asserted**: hindcast bands
   (retirements, additions, CO2) and crossover dispatch-gap numbers are on the dashboard,
   and `docs/forecasting-entry-exit-assessment.md` verdict rows are updated to match.
3. What remains unfit is **named** (the honest-unfit list, FF-4B) — locational siting,
   forward-auction timing, and anything still gated stays labeled, not implied-solved.

Out of scope for the iteration loop, by rule 22: the locked-test one-shots (2019,
H1-2026) and the 2022 validation year. They are owner-gated events run AFTER a keeper
config freezes, never inside this program's iterations (§2.3).

---

## 1. Current state (verified 2026-07-17, HEAD `c95176e`)

### 1.1 Built and working

| Area | State |
|---|---|
| Evolution loop | Steps 0–6 + RPS-as-LP-dual all implemented (`capacity.py::evolve_fleet`, `runner.py`): confirmed exits (default ON, forecast-only), announced retirements (fossil = economic-screen-governed), W2-C joint CCS retrofit-or-retire screen, economic retirements (attainable-margin basis, per-fuel thresholds, accredited reliability floor), EIA-860 planned pipeline, economic new entry (ATB-cited costs, Wright's-Law, queue caps, emerging techs), market-design-resolved reserve backstop, storage value-stack entry w/ ELCC + saturation. |
| Capacity-market instruments | Per-ISO `capacity_market_clearing` gate + eligibility registry (all OFF); published curve vintages PJM/NYISO/NEISO + MISO seasonal RBDC; PJM UCAP/FPR/ELCC basis (N-5 R1–R4); NEISO claimed-capability basis (R5b). ELCC curves (P-2C) landed. |
| Validation machinery | Forecast invariants I1–I14 + paired P1–P3 (`check_forecast_invariants.py`, CI-wired); evolution ledger per year; golden band fixture `tests/golden/ercot_2026_2040.*`; capacity-hindcast harness/scorer/register (24 bundles on the forecast-validation dashboard); full-horizon harness (`run_full_horizon.py` + collator); driver battery (24/25 Tier-1 PASS) + equilibrium battery; cross-model corridor vs AEO2025/StdScen/CDR/Gold Book/CELT (one unexplained divergence). |
| Forward inputs | Fuel forward curves (AEO paths + basis, hold-flat); demand = weather-year 2024 shape × per-ISO era-split growth; **data-center block mechanism landed** (`datacenter_load_path` off/low/mid/high + `DATACENTER_ADDITIONS_MW` anchors; `DATACENTER_ZONE_SHARE` still empty ⇒ load-share siting); forward per-plant CO2 estimator; IRA incl. **OBBBA wind/solar cliff 2027** + 45U/45Q/45V windows; state RPS/ACP + ZEC-style EAC prices; unified carbon resolver (RGGI/CARB adder vs mass-cap row); federal CES layer **W1+W2 complete** (resolver, consumer wiring, retrofit seam, reporting harness + premium-ladder configs, PJM adequacy intake W2-D, forecast hygiene W2-E). |
| Uncertainty machinery | PB-0…PB-4 landed (`matrix.py`, `uncertainty.py`, `structural_prior.py`, ensemble CLI, fan-chart page). PB-5 production band run deferred (G-35). |
| Recent owner workstream (PJM forecast) | Absorbed here: PJM blended state-RPS entry floor + ACP citations (restores renewable entry), W2-D adequacy side-registries (closes G10/I7-PJM), per-ISO modular exogenous AS revenue scaffolding, MISO storage-registry gap closed (fail-loud), market-design-dependent I12 floor. |

### 1.2 The measured frontier (ranked; each row names its lane §5 / wave §6)

1. **Retirement decision-rule inversion — NEW, blocks every flip.** RC-1A-D1 (2026-07-16)
   measured that `retirement_years_coal=3` (identified, correctly adopted) **eliminates**
   PJM's coal wave in-window (recall 76%→0) and **inverts** MISO onto gas_st (8.6 GW pure
   false-retire; LOYO-robust). Consecutive-loss counters with per-fuel thresholds race
   fuels against each other. → FF-0C (redesign memo, consult §4) then FF-1A ⛔.
2. **ERCOT screen revenue level + in-year scarcity formation — availability half LANDED
   (FF-1B, 2026-07-18), level residual open.** The correlated forced-outage derate
   (measured Uri/Elliott/Heather curves, default-off, owner flip pending) breaks the
   ORDC-$0 blocker *conditionally*: 2024 forms in-year scarcity on the un-staged fleet
   (mean $0.87/MWh, max $4,968 at Heather; CT screen 6.4→11.9 $/kW-yr ≈ 17.5 % of SOM 68)
   but is absorbed on the staged/threshold-3 full fleet, and Uri-2021 stays $0 because
   hindcast demand is shed-suppressed served load (a demand-input gap, not availability).
   Residual to SOM: ≈ 56 $/kW-yr event-year / ≈ 66 event-free (co-opt off) → still
   G-20/G-22's. See `docs/handoffs/ff-1b-correlated-availability-2026-07-17.md`.
3. **Entry stack — FF-2A LANDED (gated, 2026-07-18); ERCOT solar residual open.** Was: BLK-8
   solar (PJM price channel alone insufficient; owner's state-RPS attribute fix unmeasured at
   bands), BLK-7 VRE capacity revenue = 0, queue chunking / entry sizing (I13 cobweb), BLK-10
   backstop over-fire, and no interconnection/construction lag at all. Entry stack — FF-2A
   landed (gated): VRE capacity revenue measured near-pivotal (MISO 2025 −1.3k), BLK-10
   backstop 2.5 → 1.103 GW at the measured ladder, PJM solar +84 % → +48 %; ERCOT solar zero
   measured as a pure term-(a) price-signal residual (−9.7k best-year margin) — G-20/G-22
   lane. Integrated as real source + reproduced (`*-ff2a-r2` legs, score-identical) —
   `docs/handoffs/ff-entry-stack-completion-2026-07.md` §8.
4. **Non-equilibrium two-phase trajectory** (full-horizon P-3A): de-firm to ~2035 then
   cap-market over-build (RM→30–67%) / ERCOT chronic shortage + #2064 non-monotone
   scarcity. Cure = responsive capacity price (flips) + entry dynamics; re-measured at T2.
5. **Base-year adequacy accounting**: I7 FAILs at 2026 for CAISO/NEISO/NYISO (PJM now
   clean after W2-D — the working A/B); NEISO requirement is a NERC stand-in
   (`0.157`, needs Net ICR citation). → FF-2B.
6. **Inputs currency**: DC zone shares empty; growth/ATB/fuel/policy vintages unaudited
   at HEAD; `NEW_ENTRY_COSTS` hardcoded (ATB-cited) rather than reading the curated ATB
   datatype; hydro fleet silently drops ~3.3 GW (NYISO) past the last EIA-923 vintage.
   → FF-0D audit, FF-1C/FF-1E fixes.
7. **NYISO R5a** adjudicated-unimplemented (**owner decided Option B — NYCA-wide static
   proxy — FF-1F 2026-07-18, §2.1a**; implementation still pending) — curve-ineligible;
   **NEISO evidence-free** (no capacity hindcast at all). → FF-3D / FF-2B.
8. **Numerics**: storage ε-tiebreak degeneracy at high penetration (I9, CAISO →5.8% of
   throughput); RPS dual cobweb (I10 WARN). → FF-3C (with T2 evidence).
9. **Runtime**: late-horizon LPs grow super-linearly (PJM 2045–2050 ≈ 30–40 min/yr,
   9–10 GB RSS; two per-plant ISOs cannot co-run late years on a 15 GB box). → §2.4 rules
   now, FF-3C if T2 breaches budget.
10. **MISO forecast path unverified** since the storage-registry fix landed. → FF-0B.

### 1.3 Absorbed workstreams (state + what remains)

| Lane (old id) | Detailed spec (still citable) | Done | Remaining (now chartered here) |
|---|---|---|---|
| Retirement / flip-gate (RC-*) | `docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` (§2.1 gate, §3 T-R bands), flip memo 2026-07-16, D1 findings | RC-0A…RC-2B incl. D1 re-probe; per-ISO gate; vintages; seasonal MISO; R5b; coal threshold identified | Decision-rule redesign (FF-0C/1A), flips (FF-2C), NYISO R5a (FF-3D), NEISO first pair (FF-2B), BLK-10 re-measure (FF-1A/2A) |
| National CES (W*) | `docs/handoffs/national-ces-eac-premium-plan-2026-07.md` | Waves 1–2 fully merged (#2375–#2399): resolver, wiring, W2-C retrofit, reporting harness, W2-D, W2-E | W3-R readiness gate → W4 campaign → W5 optional (FF-3B; CES plan §7 R1–R4 map onto this program's gates) |
| PJM forecast workstream (owner) | commits on `claude/forecast-workstream-pjm-*` | state-RPS entry floor, W2-D adequacy, AS-revenue scaffolding, MISO storage registry, I12 floor | Multi-ISO adequacy basis (FF-2B), state-RPS pattern for other ISOs where cited (FF-2A), effect measurement (FF-0B/1A) |
| Capacity economics (CX-*) | `docs/handoffs/capacity-economics-plan-2026-07.md`, `cx4-datacenter-load-design-2026-07.md` | Floor accreditation redesign, joint FOM/scarcity protocol, DC-block mechanism | DC trajectories/siting currency + BAU posture (FF-1C); FOM default flip stays gated on screen-revenue work (tracked under FF-1B/2A) |
| Forecast validation (W0-P4) | `docs/handoffs/forecast-validation-program-2026-07.md` | Invariants, ledger, hindcast harness, goldens, dashboard page | Rubric + crossover instrument + tier gating (FF-0A/0E, §2–§3) |
| Probability bounds (PB-*) | `docs/handoffs/probability-bounds-plan-2026-07.md` | PB-0…PB-4 machinery | PB-5 production band — scheduled post-golden as FF-4C (owner call) |

---

## 2. Test-tier ladder & solve frugality

### 2.1 Tiers

| Tier | Window | Instrument | Purpose | Budget/ISO |
|---|---|---|---|---|
| **T0 smoke** | 1–3 yr (2026 or 2026–2028) | `run_full_horizon.py --end-year`, invariants | Per-feature probe before anything bigger. Default vehicle for iteration; prefer NEISO (~1.5–2 min/yr) or ERCOT (~3–8 min/yr). | minutes |
| **T1-F short forecast** | **2026–2030** | run_full_horizon + rubric | The owner's initial forecast-only test. All six ISOs. | ≲ 45 min |
| **T1-X crossover** | **2023–2027** | crossover harness (FF-0E): EIA-860 **2023-vintage** init, realized inputs 2023–2025, forward drivers 2026–2027 | Dispatch-side backcast→forecast input gap (scored 2023–2025 ONLY vs bench + vs the keeper's same-year scores) + 2-step capacity evolution vs registry actuals; 2026–2027 = invariants/plausibility only. Fully quarantine-legal (§2.3). | ≲ 45 min |
| **T1-H hindcast** | 2021–2025 (2020 vintage, 2022 bridged) | existing harness + pre-registered bands (program §1.4, T-R battery) | The capacity-evolution skill instrument — 4 scoreable years; KEEP as the primary retire/build scorecard (already built; cheapest signal per solve-year). | ≲ 1–2.5 h |
| **T2 mid** | **2026–2035** | run_full_horizon / `market-sim matrix` (BAU + stress cases) | Equilibrium behavior beyond the first entry waves; only T1-passing ISOs/features enter. | ≲ 2 h BAU |
| **T3 golden** | **2026–2050** | run_full_horizon, staged concurrency | The BAU deliverable. Only T2 passers. Target ≤ 2–3 attempts per ISO, ever. | 1.2–9 h |

**Promotion gates** (scored by the rubric, §3): T0→T1 = invariants I1–I14 no-FAIL on the
feature probe. T1→T2 = FC-1 PASS, FC-2 no-FAIL, FC-3/FC-4 within pre-registered bands,
FC-6 driver battery green. T2→T3 = adds FC-5 corridor conformance + stability through
2035 (no I12 breach trend, no I13). A feature that fails a gate goes back to its lane;
it does NOT ride along into longer solves "to see what happens."

### 2.1a Owner-decided forecast posture (FF-1F, 2026-07-18)

The owner fixed the default forecast posture for T1+/golden runs (§0 "produced at
HEAD defaults plus the owner-decided DC-load posture"). Recorded here per the
standing instruction (the Wave-1 FF-1C prompt, §6: "record the decision in this
plan §2.1 when made"); §7 binds. Two are `ScenarioConfig` default flips executed
in FF-1F; two are execution/design decisions carried by later, owner-gated lanes.

| # | Decision | Value | Execution |
|---|---|---|---|
| a | Capacity-market clearing (CR-1 sloped demand curve) | **ON for every ISO with a real capacity market** — PJM, MISO, NYISO, NEISO, CAISO (all but energy-only ERCOT) | **NOT flipped in FF-1F.** Executed per-ISO by readiness in **FF-2C** (owner-gated) via `capacity_market_clearing_by_iso`; the scalar `capacity_market_clearing` default stays OFF so no ISO clears before its lane is ready. |
| b | NYISO R5a reserve-requirement construction | **Option B** (NYCA-wide static proxy — not the lagged model-derived factor of Option A) | **FF-3D** (owner-gated) implements it and runs the first curve-ON probe. |
| c | `datacenter_load_path` default | **`mid`** (was `off`) — model the published DC boom as a flat, energy-invariant block (FF-1C §7) | **FF-1F** (`scenarios.py`). Forecast-only axis; `__post_init__` coerces it to `off` in backcast/hindcast, so keepers stay byte-identical. |
| d | `correlated_forced_outage` default | **ON** (was `False`) — the measured Uri/Elliott/Heather cold-event derate (FF-1B §3 recommendation) | **FF-1F** (`scenarios.py`). ERCOT-only curve; hard no-op in backcast (keepers byte-identical); hindcast legs inherit it on re-solve (a validation-lane consequence, not a keeper change). |

**FF-1F byte-identity attestation (c, d).** Backcast `cache_key` is **unchanged**
by the flip (DC coerces to `off`, and `backcast_config` pins
`correlated_forced_outage=False` so the derate flag keeps its old value); the
derate is additionally a mechanism-level no-op in backcast. The forecast default
`cache_key` shifts **as intended** — the golden posture is now a distinct
scenario. T0 evidence + citations: `docs/handoffs/ff-1f-posture-defaults-2026-07-18.md`.

### 2.2 The crossover instrument, precisely

`--vintage 2023` crossover mode (built by FF-0E on the hindcast harness): initialize
fleet + pipeline from `data/raw/eia-860/vintage_2023/`; 2023–2025 use realized demand
profiles and realized fuel (rule-13-admissible physical inputs); 2026–2027 use pure
forward drivers (growth-scaled demand, AEO fuel path, statistical outages — the forecast
methodology, no measured overlays by construction). Scoring:

- **Dispatch skill 2023–2025**: same metrics as the backcast scorer, reported side-by-side
  with the ISO's keeper backcast scores. The delta IS the backcast→forecast input gap —
  the honest answer to "how much accuracy do the measured overlays carry."
- **Capacity events 2023–2025** vs EIA-860 registry actuals (2 evolution steps — weak
  alone; T1-H remains the primary capacity instrument).
- **2026–2027**: invariants + benchmark-context only (announced pipeline, ISO forecasts).
  The scorer must structurally refuse to read bench/actuals for any year ≥ 2026.

### 2.3 Quarantine constraints (rule 22, applied to this program)

- Train years 2023–2025: solve/score freely, any mode. 2026+ **forecast-mode** solves are
  unrestricted (they consume no measured H1-2026 actuals by construction).
- **Never scored inside this program**: H1-2026 and 2019 (locked tests — one-shot,
  owner-run, after config freeze; ERCOT/PJM/MISO/CAISO also lack calibration-complete
  markers so scoring is CI-impossible anyway); 2022 (validation year — stays the
  evolved-never-solved bridge in every hindcast).
- Hindcast harness allowed solve years: {2021, 2023, 2024, 2025}; crossover adds
  {2026, 2027} as forecast-mode solves with the ≥2026 scoring refusal above.
- Forecast artifacts register on the **forecast-validation dashboard namespaces only**
  (`frontend/data/hindcast/`, future `frontend/data/forecast/`) — never the backcast
  registry; the backcast CI gates must never learn forecast namespaces.

### 2.4 Wall-clock & memory budget (measured anchors; rule 12 binds)

Measured: ERCOT ~3–8 min/yr (~3.6 GB); NEISO ~85 s median/yr (25 yr = 72 min, 3.9 GB);
CAISO ~470 s median/yr (25 yr = 179 min, 5.3 GB); PJM 2026 ≈ 380 s / 8.7 GB, late years
30–40 min / 9–10 GB (25 yr > 8 h); per-plant multi-zone LPs ≈ 8.6 GB each — **two cannot
co-run on a 15 GB box** (measured OOM, RC-1A-D1); CES 25-yr leg ≈ 4–5 h.

Standing scheduling rules:

1. Iterate features on NEISO/ERCOT T0 probes; touch PJM/CAISO only at gate time.
2. Years sequential within an invocation, ALWAYS; ≤ 2 concurrent invocations, and **1**
   when any per-plant multi-zone ISO is past ~2035 (or on a 15 GB box, whenever two
   per-plant ISOs would overlap at all — check RSS first).
3. Reuse committed bundles: BEFORE legs that are invariant to a change are never
   re-solved; the per-year cache makes killed runs resumable — resume, don't restart.
4. Batch related probes through `market-sim matrix` (one config, N cases) instead of N
   ad-hoc sessions.
5. Every session reports wall/RSS per solve-year in its findings doc; FF-3C triggers only
   on a measured budget breach at T2, not speculation.
6. Solves run in-session, never on CI runners (CLAUDE.md); no polling loops — background
   the invocation and check on completion.

---

## 3. Forecast determination rubric (FR) — charter for FF-0A ⛔

Precedent: `docs/calibration-determination-rubric.md` (backcast, C1–C8 + D-diagnostics).
The forecast analogue is **FF-0A's deliverable** (`docs/forecast-determination-rubric.md`
+ `scripts/forecast_verdict.py`), graded per ISO per tier from committed artifacts only
(ledgers, parquets, invariant output, benchmark tables) — no LP inside the scorer.
Category sketch (FF-0A finalizes metrics/thresholds, pre-registered before T1 scoring):

- **FC-1 Structural integrity** — I1–I14 (hard gate; I-thresholds stay owned by
  `check_forecast_invariants.py`, the rubric consumes its output).
- **FC-2 Adequacy & equilibrium behavior** — reserve margin within the market-design band
  every year; no I13 cobweb; backstop share of additions bounded; for curve-ON ISOs the
  position trajectory vs the ISO's own curve (T-R4 style); ERCOT scarcity-hour frequency
  inside an ORDC-design-plausible corridor.
- **FC-3 Capacity-evolution skill** — the T1-H hindcast bands (retirement recall /
  false-retire / timing; additions by tech; CO2 ±10%) + T-R rows; bands never widened.
- **FC-4 Crossover dispatch skill** — T1-X 2023–2025 vs bench, reported as
  (forecast-mode error) ÷ (keeper backcast error) per metric; FF-0A sets the acceptable
  input-gap multiple from the D-7 statmode evidence (overlay-carried skill differs by ISO).
- **FC-5 External corridor** — 2030/2035(/2040) capacity mix, energy mix, CO2 vs
  AEO2025 / NREL StdScen / ISO planning documents (CDR, PJM forecast, Gold Book, CELT,
  IEPR) with the cross-model-corridor divergence-explanation discipline. **Benchmarks are
  context, never fit targets** (rule 13); a divergence needs an explanation, not a nudge.
- **FC-6 Driver response** — Tier-1 monotonicity battery + paired P1–P3 invariants green
  at the current config.
- **FC-7 Provenance & DOF** — run_config completeness, DOF ledger with identification
  sources, no off-registry knobs (rule 24 sweep), defaults cited.
- **FC-8 Runtime feasibility** — wall/RSS within §2.4 budget (WARN-level, reported).

Golden bundles additionally carry the attestation of §0.1. The rubric versions like the
backcast one (v1.0 at FF-0A; changes are owner-signed amendments).

---

## 4. Methodology grounding — consult the field before inventing

**Standing order:** any session redesigning a capacity-expansion mechanism (retirement
rule, entry dynamics, capacity price interaction, foresight, load) MUST include a
research step against the references below (WebSearch/WebFetch where the proxy allows;
otherwise the on-disk corpus + a MANUAL-DOWNLOADS row), and its memo must state which
practice was adopted/adapted/rejected and why. Numbers entering the model carry citations
into `docs/parameter-citations.md` (rule 5). In-repo anchors first:
`docs/handoffs/cross-model-corridor-2026-07-13.md` (external-outlook corridor),
`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` §1 (the
commercial-practice scorecard that framed this program).

| Problem | Consult | What to take |
|---|---|---|
| Retirement economics / decision rule | **EPA IPM** (v6 / Post-IRA documentation: NPV going-forward cost vs revenue over a horizon, two-stage retirement), **ReEDS** (age-based lifetimes + operating-margin economic retirement, phased), Monitoring Analytics SOM avoidable-cost, **GenX** (endogenous retirement as decision variables) | Horizon/NPV framing vs consecutive-loss counters; how commercial models avoid per-fuel threshold races; lumpiness handling |
| Entry dynamics, build limits, foresight | **ReEDS** (growth constraints, interconnection supply curves, financing multipliers), **GenX** (build limits, perfect-foresight contrast), **PLEXOS LT / Aurora** (integer NPV build decisions, convergence iterations), LBNL *Queued Up* (interconnection lag empirics) | Myopic-loop damping practice; queue/lead-time representation; entry block sizing |
| Capacity market interaction | Brattle net-CONE / VRR studies, RTO planning parameters + filings (already intaken), **EPRI US-REGEN** capacity transitions | Position-responsive price dynamics; demand-curve interaction with entry/exit in LT models |
| ELCC / accreditation | E3 / Astrape ELCC studies, RTO ELCC filings (P-2C already cites) | Saturation shape sanity for FC-2 |
| Load & data centers | EIA AEO2025, ISO forecasts (ERCOT LFL, PJM 2026, Gold Book, CELT, IEPR), LBNL data-center reports | DC trajectory anchors + siting; growth-path corridor |
| Fuel | AEO2025 cases; NYMEX strips as near-term context (never a fit target) | Path plausibility bands for FC-5 |
| Scarcity / ORDC | ERCOT ORDC parameters + Potomac SOM; Hogan–Pope ORDC papers | Scarcity-frequency corridor; screen reserve-value level (BLK-6 anchor ≈ 68 $/kW-yr CT) |
| VRE/storage cost | NREL ATB 2024/2025 (curated datatype on disk), StdScen 2024 | Entry-cost currency; the wire-the-parquet decision (FF-1E) |

---

## 5. Lanes (parallel, file-ownership-disjoint)

Within a wave, sessions in different lanes run as parallel independent sessions. Two
rules prevent collisions: **(a)** a file is owned by exactly one lane per wave (table
below); **(b)** where two same-wave sessions must touch one file (rare, flagged in §6),
the later-listed session starts only after the earlier merges.

| Lane | Scope | Owned files (primary) |
|---|---|---|
| **L-CAP** capacity screens & clearing | retirement rule, entry stack, backstop, flips, adequacy bases | `model/capacity.py`, capacity fields in `scenarios.py`/`constants.py`, hindcast harness probe flags |
| **L-SCAR** availability & scarcity revenue | correlated forced outage / extreme-weather derate, screen reserve value, ERCOT level gap (consumes G-20/G-22, never extends it) | `data/outages.py`, availability seam in `runner.py`, `model/ancillary.py` exogenous-AS registry |
| **L-INP** forward inputs | demand growth + DC block currency, fuel/ATB/policy currency, hydro fix, planned-pipeline vintage | `data/*` loaders, demand/DC constants, `policy/ira.py` params |
| **L-VAL** validation & rubric | rubric + scorer, crossover harness, tier batteries, goldens, registration | `scripts/forecast_verdict.py`, `scripts/score_crossover.py`, `run_capacity_hindcast.py` CLI, `docs/forecast-determination-rubric.md` |
| **L-CES** CES campaign | W3-R gate, W4 campaign, W5 | CES configs, `report_ces_campaign.py` |
| **L-PERF** runtime & numerics | late-horizon LP growth, storage ε degeneracy, warm-start/HiGHS opts | solver/perf seams only, on measured evidence |
| **L-DASH** dashboard | forecast run explorer + status pages (§8, LAST) | `docs/codebase-site/`, `frontend/data/forecast/` |

---

## 6. Waves & prompt pack

Conventions (house style): waves sequential; prompts within a wave are independent
parallel sessions; `[FABLE]` = hard structural/adjudication work, `[OPUS]` = everything
Opus can genuinely carry (solve campaigns, intake, harness plumbing, spec'd execution);
`⛔` = gate. Every prompt implicitly begins: *Read CLAUDE.md and
`docs/forecast-development-plan-2026-07.md` (§7 standing constraints bind this session);
fresh branch off latest `origin/main`.* And ends: *push via `mcp__github__push_files`
only; verify any pushed file ≥300 lines (fetch-back or `git fetch` + empty-diff).* 

```
WAVE 0 (5 parallel, no shared files):
  FF-0A [FABLE] ⛔ forecast determination rubric + forecast_verdict.py     (L-VAL)
  FF-0B [OPUS]     T1-F baseline battery: 6 ISOs × 2026-2030 + triage      (L-VAL)
  FF-0C [FABLE]    retirement decision-rule redesign memo (no code)        (L-CAP)
  FF-0D [OPUS]     forward-inputs & policy currency audit (no defaults)    (L-INP)
  FF-0E [OPUS]     crossover harness (2023-vintage, 2023→2027) + scorer    (L-VAL)

WAVE 1 (after W0; FF-1A needs FF-0C + owner sign-off):
  FF-1A [FABLE] ⛔ implement retirement redesign + re-probe + LOYO         (L-CAP)
  FF-1B [FABLE]    correlated availability + screen reserve value          (L-SCAR)
  FF-1C [OPUS]     demand/DC currency + hydro fix                          (L-INP)
  FF-1D [OPUS]     first crossover runs ERCOT+PJM + input-gap report       (L-VAL)
  FF-1E [OPUS]     entry-cost & policy wiring (ATB parquet, IRA, RPS reg)  (L-INP, after FF-1C merges)

WAVE 2 (after W1):
  FF-2A [FABLE] ⛔ entry-stack completion (BLK-7/8/10, lag, sizing)        (L-CAP)
  FF-2B [OPUS]     adequacy-basis closure (I7 base-year; NEISO ICR+pair)   (L-CAP, after FF-2A merges)
  FF-2C [OPUS]     flip execution for owner-approved ISOs + gated re-runs  (L-CAP, after FF-2B; owner-gated)
  FF-2D [OPUS]  ⛔ T1 gate battery: 6 ISOs re-run + rubric verdicts        (L-VAL)

WAVE 3 (after FF-2D T1 gate):
  FF-3A [OPUS]  ⛔ T2 mid-horizon 2026-2035 + stress matrix                (L-VAL)
  FF-3B [OPUS]     CES W3-R readiness → GO/NO-GO → W4 campaign             (L-CES)
  FF-3C [FABLE]    performance & numerics (only on measured T2 breach)     (L-PERF)
  FF-3D [OPUS]     NYISO R5a implementation + first curve-ON probe         (L-CAP, owner-gated)

WAVE 4 (after T2 pass):
  FF-4A [OPUS]  ⛔ T3 golden 2026-2050 × 6 ISOs, rubric-scored, registered (L-VAL)
  FF-4B [FABLE]    golden attestation + verdict update + honest-unfit list (L-VAL)
  FF-4C [OPUS]     (optional, owner) PB-5 probability band production run  (L-VAL)

WAVE 5 (last):
  FF-5A [OPUS]     forecast run explorer + status dashboard build-out (§8) (L-DASH)
```

### Wave 0

#### FF-0A [FABLE] ⛔ — Forecast determination rubric + scorer

```
[FABLE] FF-0A — Author the forecast determination rubric (v1.0) + forecast_verdict.py

Read CLAUDE.md, docs/forecast-development-plan-2026-07.md §2-§4 (spec; §7 binds),
docs/calibration-determination-rubric.md (the backcast precedent to mirror),
docs/handoffs/forecast-validation-program-2026-07.md §1.4/§2.2 (hindcast bands +
invariants), docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §3 (T-R
battery), docs/handoffs/cross-model-corridor-2026-07-13.md (external corridor + the
divergence-explanation discipline), docs/handoffs/driver-battery-2026-07-12.md, and
scripts/check_forecast_invariants.py. Research step per plan §4: survey how commercial
practice judges capacity-expansion output (EPA IPM documentation, ReEDS Standard
Scenarios validation sections, CEMs literature on backtesting expansion models) and
record what you adopt/reject.

Deliver:
1. docs/forecast-determination-rubric.md v1.0 — categories FC-1..FC-8 per plan §3 with
   concrete metrics, thresholds, and per-tier promotion logic (T0→T1→T2→T3). Every
   threshold pre-registered with a rationale line; hindcast/T-R bands imported by
   reference, never restated looser. Include the golden-attestation checklist (DOF
   ledger, run_config reproducibility, honest-unfit list).
2. scripts/forecast_verdict.py — scores a forecast bundle (ledgers + parquets +
   invariant output + committed benchmark tables) per tier; no LP; one PASS/CAVEAT/FAIL
   line per category with offending values; --tier {t1f,t1x,t1h,t2,t3}; JSON sidecar
   output for the future dashboard. Unit tests on synthetic fixtures (trivial first).
3. Benchmarks it consumes must already be on disk — inventory what FC-5 needs vs
   data/raw/ and file intake gaps as a list for FF-0D (do NOT intake here).
No solve. No thresholds tuned to any existing run's numbers — pre-registration means
deriving them from design targets and external practice, then measuring.
```

#### FF-0B [OPUS] — T1-F baseline battery (6 ISOs × 2026–2030)

```
[OPUS] FF-0B — Baseline the T1-F short forecast: all six ISOs, 2026-2030, HEAD defaults

Read CLAUDE.md, docs/forecast-development-plan-2026-07.md §2 (§7 binds),
docs/handoffs/full-horizon-findings-2026-07-12.md (the 25-yr baseline + known issues),
docs/forecast-invariant-findings.md.

1. Run scripts/run_full_horizon.py --start-year 2026 --end-year 2030 per ISO, HEAD
   defaults, out-dirs results/ff-t1f-baseline/<iso>. Rule 12: years sequential; ≤2
   concurrent invocations; drop to 1 whenever two per-plant multi-zone ISOs would
   overlap (check RSS). MISO first — verify the storage-registry fix made its forecast
   path executable; if any ISO still cannot execute, root-cause and fix ONLY fail-loud
   registry gaps (cited values, fail-loud pattern) — anything structural is a finding.
2. Score each: check_forecast_invariants.py + collate_full_horizon.py; capture
   wall/RSS per year (plan §2.4 ledger).
3. Deliverable docs/handoffs/ff-t1f-baseline-2026-07.md: per-ISO invariant matrix,
   evolution-ledger summary (retire/build/backstop by year), top anomalies each with a
   mechanism hypothesis naming the module, and a ranked triage list mapped to plan §1.2
   rows (new items get new rows). Findings only — no tuning, no default changes.
4. Register the runs on the forecast-validation dashboard (register_hindcast.py
   namespace conventions; label "ff-t1f-baseline"). These are the BEFORE legs every
   Wave-1/2 change is compared against — solve once, reuse forever.
```

#### FF-0C [FABLE] — Retirement decision-rule redesign memo

```
[FABLE] FF-0C — Redesign the economic-retirement decision rule (memo, no code): kill
the per-fuel threshold inversion

Read CLAUDE.md (rules 1/13/14/21/23), docs/forecast-development-plan-2026-07.md §1.2-1
and §4 (§7 binds), docs/handoffs/position-calibration-d1-findings-2026-07-16.md
(§6/§7 — the blocker you are solving), docs/handoffs/retirement-dof-identification-
2026-07-15.md (the lag identification that must survive), docs/handoffs/
capacity-clearing-flip-memo-2026-07-16.md, and model/capacity.py::
apply_economic_retirements. MANDATORY research step (plan §4): EPA IPM retirement
formulation (NPV going-forward vs revenue over a horizon), ReEDS economic retirement,
GenX endogenous retirement, PLEXOS LT/Aurora integer NPV decisions — record
adopted/rejected per practice.

Memo docs/handoffs/ff-retirement-rule-redesign-2026-07.md:
(a) Diagnose why consecutive-loss counters with per-fuel thresholds structurally race
    fuels (the D1=3 gas_st inversion) — state the mechanism precisely.
(b) Candidate rules, each graded vs rules 13/21/23 (forward story, identification
    source, no residual fitting): (i) NPV-of-going-forward-window screen (uniform
    economic decision + per-fuel EXECUTION lag from the RC-0B lag tables — decision vs
    deactivation split); (ii) uniform identified decision threshold + per-fuel notice
    lag; (iii) margin-depth cohort thinning (worst-first partial waves); (iv) hysteresis
    band. Others you find in the literature are welcome — cite them.
(c) Pre-registered acceptance: the existing T-R battery unchanged + a new T-R10
    (no-inversion guard: no fuel with zero real exits in the window becomes the
    first-moving economic exit) + LOYO within 2023-2025. Bands never widened.
(d) Identification plan for every new parameter (what data pins it; what stays an
    open DOF), and an owner-decision box (options, recommendation, what each re-opens).
No code, no solve, no tuning. This memo gates FF-1A.
```

#### FF-0D [OPUS] — Forward-inputs & policy currency audit

```
[OPUS] FF-0D — Audit every forward input for currency and wiring (no defaults moved)

Read CLAUDE.md (rules 5/13/14/23), docs/forecast-development-plan-2026-07.md §1.2-6
(§7 binds), docs/handoffs/cx4-datacenter-load-design-2026-07.md (the DC spec — the
mechanism has since LANDED: scenarios.py datacenter_load_path + constants
DATACENTER_ADDITIONS_MW; DATACENTER_ZONE_SHARE is empty), and docs/handoffs/
nyiso-forecast-2035-2026-07-13.md (the hydro fleet-drop finding).

Audit, with per-item verdict CURRENT / STALE / UNWIRED and the citation trail:
1. DEMAND_GROWTH_RATES + DATACENTER_ADDITIONS_MW anchors vs the latest published ISO
   forecasts (ERCOT LFL officer update, PJM 2026 Load Forecast, Gold Book, CELT, IEPR,
   MISO futures); DATACENTER_ZONE_SHARE population sources (published siting only).
2. HENRY_HUB_TRAJECTORIES / coal / oil / uranium path vintages (AEO2025?).
3. NEW_ENTRY_COSTS + TECH_COST_MULTIPLIERS vs the curated NREL ATB datatype on disk —
   recommend wire-the-parquet vs re-derive-constants (rule 23 citation either way);
   check emerging-tech params (CCUS/H2/geothermal/offshore) and financing basis
   (single real_discount_rate vs ATB per-tech WACC — present the option, decide nothing).
4. policy/ira.py fields vs current statute (OBBBA cliff 2027 present — verify 45U/45Q/
   45V/other-clean phase-down values + windows); STATE_RPS_TARGETS/ACP registry currency;
   confirmed-retirements registry currency (any new instruments since intake).
5. EIA-860 planned-pipeline vintage; weather-year pool posture; hydro forecast fleet
   bug (data/hydro.py exact-year filter → charter the hold-last-vintage fix for FF-1C).
6. FC-5 benchmark-table gaps from FF-0A's inventory (if its list is merged; else leave
   a placeholder section).
Deliverable docs/handoffs/ff-inputs-currency-audit-2026-07.md + a prioritized fix/
intake list feeding FF-1C/FF-1E. Fetch public documents where the proxy allows; log
MANUAL DOWNLOADS NEEDED rows otherwise — never guess values. Audit only: no source
default changes in this session.
```

#### FF-0E [OPUS] — Crossover harness (2023-vintage, 2023→2027)

```
[OPUS] FF-0E — Build the T1-X crossover instrument on the hindcast harness

Read CLAUDE.md (rule 22 hard), docs/forecast-development-plan-2026-07.md §2.2-§2.3
(THE SPEC; §7 binds), scripts/run_capacity_hindcast.py + score_capacity_hindcast.py,
and pipeline/backcast_config.py (for which realized inputs the backcast path resolves —
you are reusing the rule-13-admissible physical ones only: demand profiles, fuel).

1. Extend run_capacity_hindcast.py: --vintage {2020,2023} (fleet + pipeline init from
   the named EIA-860 vintage; leakage guard generalized) and a crossover window
   (--start-year 2023 --end-year 2027): realized per-year demand + realized fuel for
   2023-2025; 2026+ switches to pure forward drivers (growth-scaled demand from the
   last realized year, AEO fuel path, statistical outages, no measured overlays —
   assert none of the backcast-gated loaders fire). No bridge year. Allowed solve years
   for crossover: {2023, 2024, 2025, 2026, 2027}; the harness's existing holdout guard
   stays intact for hindcast mode.
2. scripts/score_crossover.py: (a) dispatch skill 2023-2025 vs bench using the backcast
   scorer's metric definitions, emitted side-by-side with the ISO's committed keeper
   scores (the input-gap columns); (b) capacity events 2023-2025 vs registry actuals
   (reuse score_capacity_hindcast matching); (c) years ≥2026: invariants only — the
   scorer must REFUSE (raise) to read bench/actuals for any year ≥ 2026, with a test
   proving it (patch the loaders to raise). No H1-2026 file is ever opened.
3. Tests trivial-first (synthetic 2-zone fixture through the crossover path), plus the
   vintage-2023 leakage test (no unit absent from the 2023 proposed sheet enters).
4. Registration: crossover runs land on the forecast-validation dashboard namespace
   with kind "crossover". Update the harness docstrings + plan §2.2 if reality diverges.
No production defaults change. First real runs are FF-1D's, not yours (build ≠ run).
```

### Wave 1

#### FF-1A [FABLE] ⛔ — Implement the retirement redesign + re-probe + LOYO

```
[FABLE] FF-1A — Implement the owner-approved retirement decision rule; re-measure the
flip gate

Requires: FF-0C memo + owner sign-off on its decision box. Read CLAUDE.md, docs/
forecast-development-plan-2026-07.md §1.2-1 (§7 binds), the FF-0C memo, docs/handoffs/
position-calibration-d1-findings-2026-07-16.md, docs/handoffs/forecast-retirement-
calibration-plan-2026-07.md §2.1/§3 (gate + T-R bands — never restated looser).

1. Implement the approved rule in model/capacity.py::apply_economic_retirements.
   Every parameter in ScenarioConfig/constants with its identification citation
   (rules 5/21/23/24); legacy counter semantics preserved behind the old fields where
   feasible; byte-identity proven for configurations the redesign leaves untouched.
2. Re-run the measurement set, reusing committed BEFORE legs (never re-solve invariant
   legs): PJM + MISO curve-ON probe legs (2021-2025 realized, 2022 bridged, seasonal
   MISO grain) + ERCOT composition leg (lookahead+staged arms at HEAD). Rule 12:
   sequential years; on a 15 GiB box run the multi-zone legs sequentially (measured
   ~8.6 GB each).
3. Score: T-R1/T-R2/T-R3/T-R4/T-R5-inv/T-R7 + the new T-R10 no-inversion guard + LOYO
   within 2023-2025 (scorer-side folds). Re-measure BLK-10 (backstop MW fired) — the
   gap-register row requires it before any sizing rework. Grade the §2.1 flip-gate
   items 3-4 per ISO with MEASURED numbers.
4. Register runs (forecast-validation dashboard only); findings doc docs/handoffs/
   ff-retirement-rule-implementation-<date>.md with the per-ISO gate scorecard — this
   is the flip-decision input for FF-2C. A residual closable only by an unidentified
   value is an open blocker, written up, not a parameter (rule 21).
```

#### FF-1B [FABLE] — Correlated availability + screen reserve value

```
[FABLE] FF-1B — Give forecast-mode ERCOT a real availability distribution and a real
reserve-value signal (BLK-6's structural half)

Read CLAUDE.md (rules 13/19 hard), docs/forecast-development-plan-2026-07.md §1.2-2
(§7 binds), docs/handoffs/ercot-retirement-composition-2026-07-16.md Part D (the
availability design charter — stages; implement, don't re-design from scratch),
docs/handoffs/cross-model-corridor-2026-07-13.md §2 (SOM anchors), data/outages.py,
and the screen-revenue seam in model/capacity.py (screen_reserve_value_enabled).
HARD BOUNDARY: the backcast AS co-opt mechanism (G-20/G-22 lane) is consumed as-is
from main — never extended here. Rule 19: one mechanism per phenomenon — enumerate
what already derates availability in forecast mode before adding anything.

1. Implement the measured-admissible correlated forced-outage / extreme-weather derate
   for forecast/hindcast availability (EFORd-based, temperature/cold-snap-correlated;
   regenerates from weather-year + fleet physics; responds to changed conditions —
   the rule-13 test stated in the charter). Explicitly no double-count with the ORDC
   curve's own reserve-error convolution — document the seam. Default posture per the
   charter (present ON-for-forecast as the recommendation if the probe supports it;
   owner decides).
2. Probe: ERCOT hindcast legs with the derate armed — does in-year ORDC scarcity now
   form (the G-31 question)? Quantify the screen CT $/kW-yr against the SOM ≈68 anchor
   before/after (the BLK-6 residual re-measurement). Tests trivial-first.
3. Findings doc + dashboard registration. No fitted rents: whatever residual remains
   after the structural availability lands is handed to the G-20/G-22 lane with a
   number, never closed by an adder (rules 1/13).
```

#### FF-1C [OPUS] — Demand & DC currency + hydro fix

```
[OPUS] FF-1C — Bring demand-side forward inputs current (per FF-0D findings)

Requires FF-0D merged. Read CLAUDE.md (rules 5/13/23), docs/forecast-development-
plan-2026-07.md §1.2-6 (§7 binds), the FF-0D audit, docs/handoffs/
cx4-datacenter-load-design-2026-07.md (spec for the trajectory/siting tables).

1. Refresh DEMAND_GROWTH_RATES and DATACENTER_ADDITIONS_MW anchors to the FF-0D-cited
   published forecasts; populate DATACENTER_ZONE_SHARE from published siting only
   (no published decomposition ⇒ ships as load-share default, documented — never
   invented). Every number cited (parameter-citations.md).
2. Fix the hydro forecast fleet drop (hold-last-vintage hydro fleet/energy forward
   past the final EIA-923 year — the nyiso-forecast-2035 finding), mode-aware,
   backcast byte-identical, tests.
3. Present the BAU DC posture decision to the owner (datacenter_load_path default for
   T1+/golden runs: "off" vs "mid") with the corridor evidence — do not flip it
   yourself; record the decision in this plan §2.1 when made.
4. T0 smoke: NEISO + ERCOT 2026-2028 before/after, invariants green, demand deltas
   match the cited anchors. Findings + citations committed.
```

#### FF-1D [OPUS] — First crossover runs + input-gap report

```
[OPUS] FF-1D — Run T1-X for ERCOT + PJM; publish the backcast→forecast input gap

Requires FF-0E merged. Read CLAUDE.md (rule 22 hard), docs/forecast-development-
plan-2026-07.md §2.2-§2.3 (§7 binds), and the FF-0E harness docs.

1. Run crossover 2023→2027 for ERCOT and PJM (vintage 2023). Rule 12 concurrency; the
   two invocations may run concurrently only if RSS headroom is measured first.
2. Score with score_crossover.py: the input-gap table (forecast-mode 2023-2025 error ÷
   keeper backcast error, per metric per year), capacity events vs actuals, 2026-2027
   invariants + plausibility notes vs the announced pipeline and ISO forecasts
   (context only). Confirm by construction no bench/actuals read for ≥2026.
3. Deliverable docs/handoffs/ff-crossover-gap-2026-07.md: the measured input gap per
   ISO with a decomposition hypothesis per large gap (which forward driver, not which
   tuned overlay, explains it — route real driver defects to L-INP as new plan §1.2
   rows). Register runs on the forecast-validation dashboard.
Findings only — no tuning. If a gap is closable only by re-importing a measured
overlay into forecast mode, that is a FINDING about forecast-input quality, never a
change (rule 13).
```

#### FF-1E [OPUS] — Entry-cost & policy wiring

```
[OPUS] FF-1E — Wire entry costs to their curated source; fix policy-currency items

Requires FF-0D merged; starts after FF-1C merges (shared constants.py — rebase, don't
race). Read CLAUDE.md (rules 5/23/27), docs/forecast-development-plan-2026-07.md
§1.2-6 (§7 binds), the FF-0D audit, model/capacity.py entry-cost resolution, and the
curated ATB datatype + tests.

1. Execute FF-0D's recommendation on NEW_ENTRY_COSTS: wire the entry screen to the
   curated ATB parquet (loader-resolved, schema-validated) OR re-derive the constants
   from it — either way the values carry the ATB vintage citation and a test asserting
   source-consistency. TECH_COST_MULTIPLIERS/emerging-tech params reconciled likewise.
2. Apply the FF-0D policy fixes: IRA field corrections (values/windows), state RPS/ACP
   registry refresh, confirmed-retirements registry additions — all cited, all
   re-derivations citing the data change (rule 23), never a residual.
3. If FF-0D graded the financing basis worth changing: implement per-tech WACC as an
   OPTION (ScenarioConfig field, default preserving current behavior, ATB-cited) —
   flipping it is an owner decision for FF-2D's gate run, not yours.
4. T0 smoke (NEISO 2026-2028) before/after; entry-screen diagnostics ledger shows the
   cost-vintage deltas; invariants green; backcast byte-identity confirmed (entry
   screen is forecast-only, prove it stays that way). Citations + tests committed.
```

### Wave 2

#### FF-2A [FABLE] ⛔ — Entry-stack completion

```
[FABLE] FF-2A — Close the entry stack: VRE capacity revenue, sizing dynamics,
interconnection lag, lookahead posture

Requires FF-1A merged (capacity.py owner this wave; BLK-10 re-measure in hand). Read
CLAUDE.md, docs/forecast-development-plan-2026-07.md §1.2-3 (§7 binds), docs/handoffs/
blk8-solar-entry-decomposition-2026-07-15.md (term routing a-e), the flip memo R-8,
docs/gap-register-2026-07.md §3.9 (BLK-7/8/10), and the FF-1A findings. MANDATORY
research step (plan §4): ReEDS growth constraints + interconnection supply curves,
GenX build limits, LBNL Queued Up lag empirics, PLEXOS/Aurora lumpy-entry handling.

Work items, each cited + tested, LOYO-scored where a hindcast verdict flips:
1. BLK-7 / term (c): VRE (and storage where designs pay it) earns ELCC-accredited
   capacity revenue in the ENTRY screen through the same accreditation resolver the
   supply ledger uses (rule 19: one resolver).
2. Term (e) + BLK-10: entry/backstop sizing dynamics — replace the
   full-deficit-in-one-step patterns with rate-limited, need-proportional sizing whose
   parameters carry external identification (queue throughput, historical max annual
   build by tech/ISO — cited); re-measure I13/BLK-10 on the probe legs.
3. Interconnection/construction lag: economic entry currently commissions in-year —
   introduce a cited clearance→COD lag (LBNL queue medians by tech, or the EIA-860
   proposed-pipeline duration distribution already on disk). Forecast-only; ledger
   records both decision year and COD year.
4. Entry lookahead posture: entry_lookahead_reprice (G-30-validated, zero-DOF) —
   present the default-ON recommendation with the probe evidence; owner decides.
5. State-RPS attribute pattern: extend the owner's PJM blended-RPS entry floor to
   other ISOs ONLY where the same published-parameter construction exists (cited), and
   record where it does not.
Re-run the hindcast additions bands (ERCOT/PJM/MISO): the CES §7 R1 criterion (solar
recall > 0 in ERCOT and PJM within lane tolerance) is this session's headline metric.
Register; findings doc with per-term measured attribution; owner-decision box for the
posture items. No residual-fitted values anywhere (rules 1/13/14).
```

#### FF-2B [OPUS] — Adequacy-basis closure

```
[OPUS] FF-2B — Close the base-year adequacy accounting: CAISO/NEISO/NYISO I7, NEISO
requirement citation, first NEISO hindcast pair

Starts after FF-2A merges (capacity.py hand-off). Read CLAUDE.md, docs/
forecast-development-plan-2026-07.md §1.2-5/-7 (§7 binds), docs/handoffs/
full-horizon-findings-2026-07-12.md §4 (the I7 base-year table; PJM passes — your
A/B), docs/handoffs/ces-w1b-bau-smoke-2026-07.md (how W2-D closed PJM's gap),
docs/handoffs/capacity-clearing-flip-memo-2026-07-16.md §1.4/R-7, and the
accreditation-basis memo.

1. Per ISO (CAISO/NEISO/NYISO): reconcile the base-year accredited-supply ledger vs
   requirement on the ISO's own published basis — find the mis-pairing the PJM A/B
   isolates (DR/firm-tie side-registries, basis conventions). Fixes are published
   parameters with citations (the W2-D pattern), NEVER values tuned to clear I7
   (rule 13; the W2-D prompt says this verbatim — keep it).
2. NEISO requirement: replace the 0.157 NERC stand-in with ISO-NE's own Net ICR
   construction (cited) — the flip memo R-7(i).
3. NEISO per-vintage Pass-1B re-score (validate_capacity_prices, no LP), and the first
   NEISO capacity-hindcast PAIR (fixed-mode + curve-ON probe, 2021-2025, 2022 bridged)
   so NEISO's flip-gate items 3-4 become gradeable at all — score vs the T-R pattern
   with NEISO-specific pre-registered bands filed BEFORE the run.
4. Re-run the affected T1-F base years (T0-scale); I7/I12 verdicts move only via cited
   basis fixes. Register; findings doc; gap-register rows updated.
```

#### FF-2C [OPUS] — Flip execution (owner-gated)

```
[OPUS] FF-2C — Execute capacity_market_clearing flips for owner-approved ISOs

DO NOT START without: FF-1A + FF-2A findings in hand, and the owner's explicit per-ISO
sign-off on the flip decision (the RC-2B decision framework re-graded on FF-1A/FF-2A
measurements). Read CLAUDE.md, docs/forecast-development-plan-2026-07.md (§7 binds),
docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1/§2.3 F-9, the
accreditation-basis memo §4.3-R4, and the FF-1A/FF-2A findings docs.

1. One dedicated commit per approved ISO: per-ISO gate ON with the memo citation; the
   same commit executes R4 (legacy fixed net_cone_per_kw_yr re-derived to the
   published-basis figure, reconciliation test updated).
2. Gated re-runs: T1.7 net-CONE ladder + tornado capacity entries
   (run_driver_battery.py), equilibrium T-R5 rows on the flipped defaults
   (run_equilibrium_battery.py), hindcast re-scores for flipped ISOs. Register all on
   the forecast-validation dashboard.
3. Update docs/forecasting-entry-exit-assessment.md rows 7-12/14 with the measured
   post-flip evidence; refresh gap-register BLK-4/BLK-9 status; /sync-docs at end
   (methodology spec §5.9 + citations).
Rule 12 concurrency; 2022 bridged; nothing on the backcast dashboard.
```

#### FF-2D [OPUS] ⛔ — T1 gate battery

```
[OPUS] FF-2D — Score the T1 gate: six ISOs at HEAD, rubric verdicts, promotion list

Requires FF-0A rubric merged and Wave-1/2 lane merges complete (run at whatever HEAD
holds — record the SHA). Read CLAUDE.md, docs/forecast-development-plan-2026-07.md §2
(§7 binds), docs/forecast-determination-rubric.md, the FF-0B baseline doc.

1. Re-run T1-F (2026-2030 × 6 ISOs) at HEAD; re-run T1-X crossover (ERCOT+PJM; add
   MISO if its crossover inputs resolve); T1-H hindcast re-scores where Wave-1/2
   changes touched capacity behavior (probe legs only — BEFORE legs reused).
   Rule 12 scheduling per plan §2.4.
2. Score everything with forecast_verdict.py (t1f/t1x/t1h tiers); produce the per-ISO
   promotion table (T2-eligible: yes/no + blocking category rows); regression vs the
   FF-0B baseline (every metric that moved names the causal merge).
3. Golden fixture: if cited behavior changes moved the ERCOT 2026-2040 bands, regen
   via the established script citing the causal commits (rule 23 spirit) — never
   silently.
4. Deliverable docs/handoffs/ff-t1-gate-2026-XX.md + dashboard registration of all
   runs + rubric JSON sidecars. Promotion decisions are the owner's to confirm; your
   output is the measured scorecard. Findings only otherwise.
```

### Wave 3

#### FF-3A [OPUS] ⛔ — T2 mid-horizon + stress matrix

```
[OPUS] FF-3A — T2: 2026-2035 for promoted ISOs + the stress matrix

Requires FF-2D promotion list + owner confirmation. Read CLAUDE.md, docs/
forecast-development-plan-2026-07.md §2 (§7 binds), the rubric, matrix.py docs.

1. BAU 2026-2035 per promoted ISO (run_full_horizon). Then the stress matrix via
   market-sim matrix per ISO where T1 evidence justifies it: cases {BAU, DC-high,
   gas-high, gas-low, carbon-stress} (existing named-case machinery; cases are
   scenario axes, not tuned variants). Rule 12: this is the wave where late-horizon
   RSS starts to bite — serialize per-plant ISOs' post-2032 years; capture wall/RSS.
2. Score: rubric t2 tier (adds FC-5 corridor + stability-through-2035); paired
   invariants P1-P3 on the stress pairs; equilibrium read: does the two-phase
   de-firm→overshoot signature persist at the current mechanism set? (I12 trajectory
   is the fingerprint; compare against the P-3A tables.)
3. Deliverable docs/handoffs/ff-t2-gate-2026-XX.md: per-ISO T3-eligibility, FAIL rows
   routed to lanes (a failed ISO loops back — do NOT carry it to T3), wall/RSS ledger
   (FF-3C trigger data). Register runs + sidecars.
```

#### FF-3B [OPUS] — CES readiness → campaign

```
[OPUS] FF-3B — CES W3-R readiness verification; on GO, run the W4 campaign

Read CLAUDE.md, docs/handoffs/national-ces-eac-premium-plan-2026-07.md §7-§8 (the
lane spec — W3-R/W4-A/W4-B/W4-C prompts there remain binding), and docs/
forecast-development-plan-2026-07.md §2 (§7 binds; this program's FF-2A headline
metric IS the CES R1 criterion). Evaluate R1-R4 on then-current main with evidence;
write the GO/NO-GO doc the CES plan specifies. On GO (and owner confirmation): execute
W4-A/W4-B (ERCOT+PJM premium ladders, clean_capture, 2026-2050 — budget ~8-10 h wall
per ISO at 2-concurrent; per-year cache resumable) and W4-C synthesis per the CES
plan's own prompts, updated only for file/flag drift. On NO-GO: the blocking list
routes to this program's lanes and W4 waits.
```

#### FF-3C [FABLE] — Performance & numerics (conditional)

```
[FABLE] FF-3C — Late-horizon runtime + numerical hygiene (trigger: measured T2 breach
of the §2.4 budget, or I9/I10 FAILs persisting at T2)

Read CLAUDE.md (rule 2, rule 9), docs/forecast-development-plan-2026-07.md §1.2-8/-9
and §2.4 (§7 binds), docs/handoffs/full-horizon-findings-2026-07-12.md §2 (feasibility
data), docs/handoffs/wallclock-efficiency-plan-2026-07.md (what is already optimal —
do not re-litigate its explicit skips), and the FF-3A wall/RSS ledger.

Candidate work, adopt on measured evidence only, byte-identity or cited-behavior-change
discipline per item:
1. LP-size growth: audit unit-count growth from economic entry over the horizon;
   design + implement consolidation of same-tech/zone/cost entry vintages into blocks
   (structure-preserving; duals unaffected — prove on a fixture).
2. Storage ε degeneracy at high penetration (I9): diagnose whether the ε=0.001
   tiebreaker needs penetration-aware scaling or an SOC-linking cut — a NUMERICAL fix
   with an LP-theory justification, never a behavioral tune (rule 9 owns the ε).
3. RPS-dual cobweb (I10): evaluate binding-constraint smoothing practice from the §4
   references (how myopic CEMs damp constraint-price oscillation) — design memo +
   owner box if it changes economics; implement only mechanical stabilizations.
4. HiGHS options / warm-start applicability to the forecast year loop (wallclock plan
   P-4 protocol: bench-first, adopt on measured win).
Deliverable: findings + implemented items + refreshed §2.4 budget table.
```

#### FF-3D [OPUS] — NYISO R5a (owner-gated)

```
[OPUS] FF-3D — Implement the owner-selected NYISO ICAP/UCAP pairing option; first
NYISO curve-ON probe

DO NOT START without the owner's R5a decision (Option A lagged model-derived factor vs
Option B NYCA-wide static proxy — docs/handoffs/nyiso-neiso-capacity-pairing-
adjudication-2026-07-15.md §3; B needs the NYSRC Appendix D Table D.1.1 manual
download). Read that adjudication + the flip memo §1.3 + docs/
forecast-development-plan-2026-07.md (§7 binds). Implement the chosen construction
(cited; basis-consistency tests mirroring the PJM R2/R3 pattern); lift the
curve-eligibility block only when the pairing lands; run NYISO's first fixed/curve-ON
hindcast pair (2021-2025, bands pre-registered before the run, T-R pattern); grade
NYISO's flip-gate items; register + findings. The flip itself remains a separate
owner decision (FF-2C pattern).
```

### Wave 4

#### FF-4A [OPUS] ⛔ — T3 golden solves

```
[OPUS] FF-4A — The golden 2026-2050 BAU solves, all T2-promoted ISOs

Requires FF-3A T2 pass + owner confirmation of the golden config (incl. the DC posture
decision and any owner-flipped defaults — record the exact SHA + run_config). Read
CLAUDE.md, docs/forecast-development-plan-2026-07.md §0/§2 (§7 binds), the rubric.

1. Solve 2026-2050 per ISO with the staged schedule: small ISOs may pair (≤2
   concurrent); per-plant multi-zone ISOs (PJM/CAISO/MISO) run their post-~2035 years
   SOLO (measured 9-10 GB tails). Use the per-year cache: a stopped run resumes —
   plan the session in resumable chunks rather than one heroic invocation.
2. Score rubric t3 per ISO; register each bundle on the forecast-validation dashboard
   as a GOLDEN CANDIDATE with its rubric JSON + evolution ledgers + wall/RSS ledger.
3. Any FAIL: stop, route to the owning lane, do not iterate config inside this
   session (golden attempts are budgeted — a failed attempt's diagnosis is FF-4B's
   input, and the re-attempt happens only after the lane fix merges).
Deliverable: per-ISO golden-candidate table + docs/handoffs/ff-t3-golden-2026-XX.md.
```

#### FF-4B [FABLE] — Golden attestation & program close-out

```
[FABLE] FF-4B — Attest the golden bundles; update the verdict; name what remains unfit

Read CLAUDE.md (rule 21), docs/forecast-development-plan-2026-07.md §0 (§7 binds), the
FF-4A bundles + rubric output, docs/forecasting-entry-exit-assessment.md, the flip
memo, and every open plan-§1.2 row.

1. Per golden ISO: the DOF-ledger attestation (every free parameter → identification
   source; open DOFs listed as open, not hidden), rubric verdict summary, and the
   reproducibility check (run_config → same bundle).
2. Rewrite docs/forecasting-entry-exit-assessment.md verdict rows against the golden
   evidence (the P-3C convention: measured, adversarial, no celebration).
3. The honest-unfit list: what these goldens still cannot claim (locational siting,
   forward-auction timing, any ISO/mechanism still gated) — in the plan §0 terms.
4. Owner sign-off package: which bundles are promoted from candidate to GOLDEN;
   schedule the SEPARATE owner-gated events (PB-5 band run FF-4C; the rule-22
   locked-test one-shots per ISO once calibration-complete markers + freeze exist).
Memo session — no solve, no code, no tuning.
```

#### FF-4C [OPUS] — PB-5 probability band (optional, owner call)

```
[OPUS] FF-4C — Produce the first production probability band on the golden config

Owner-gated (G-35). Read docs/handoffs/probability-bounds-plan-2026-07.md (the spec —
sizing, sampler, structural prior, honest labels) + docs/probability-bounds-ercot-
2026-07.md (the 5-member pilot closeout) + docs/forecast-development-plan-2026-07.md
§2.4 (§7 binds). Execute the PB-5 batch per the PB plan's own sizing on the golden
ERCOT config (members via market-sim ensemble --sampler + --structural-prior;
rule 12 scheduling; resumable). Publish via export_forecast_bands.py to the fan-chart
page with the PB plan's honest-label discipline (dispatch-conditional caveats as its
§3.4 requires, updated for what the golden bundles now validate). Register + findings.
```

### Wave 5 — FF-5A dashboard: see §8 (run LAST).

---

## 7. Standing constraints (every FF session)

1. **Models:** OPUS or FABLE only, per the §6 label. Never Sonnet (rule 27).
2. **Git:** fresh branch off latest `origin/main`; push via `mcp__github__push_files`
   ONLY (never `git push`); after any push touching a file ≥300 lines, verify the blob
   (fetch-back compare, or `git fetch origin <branch>` + empty `git diff`) before the
   next commit; no placeholder/partial versions of existing files, ever.
3. **No CI offload:** no new GitHub Actions workflows; no solves/intakes on runners;
   solves run in-session (background bash), rule 12 discipline: years sequential within
   an invocation, ≤2 concurrent invocations, 1 when per-plant multi-zone RSS says so.
4. **Rule 22:** no solve/score/intake of 2022, ≤2021 (outside the hindcast's own
   {2021} allowance), 2019, or H1-2026; crossover scores stop at 2025; hindcast 2022
   stays an evolved-never-solved bridge; locked tests are owner-run one-shots outside
   this program.
5. **Registration:** forecast probes/hindcasts/goldens go to the forecast-validation
   dashboard namespaces in the producing session (rule 15 spirit); NEVER the backcast
   registry; backcast CI gates never learn forecast namespaces.
6. **No tuning:** findings-first sessions never fix; bands are never widened; a
   residual closable only by an unidentified value is an open blocker (rules 1/11/13/
   14/21/23); benchmark corridors are context, never fit targets.
7. **Registry discipline:** every tunable in `ScenarioConfig`/`constants.py` with a
   citation, visible in `run_config.json` (rules 5/24); one mechanism per phenomenon
   (rule 19); deleted means deleted (rule 26).
8. **Docs:** findings docs to `docs/handoffs/ff-*.md`; `/sync-docs` when a session
   settles methodology; this plan's §1.2 frontier table is updated by any session that
   closes or opens a row (append-edit, small commits).

---

## 8. Dashboard build-out — forecast run explorer & status pages (STUB — run LAST)

**Placeholder.** The forecast dashboard today is `docs/codebase-site/
forecast-validation.html` (self-contained hindcast scorecards + invariant chips,
regenerated by `register_hindcast.py` from `frontend/data/hindcast/*.json`) plus
`forecast-bands.html` (fan chart). It is deliberately minimal and stays that way until
the program has golden bundles worth exploring — build this **after Wave 4** (or when
the owner calls it). Scope sketch for the future session: a **forecast run explorer**
(sibling of `backcast-runs.html`) over a new registry namespace, and a **forecast
status page** (sibling of `calibration-status.html`) showing per-ISO tier/gate state.
Draft prompt (final wording may be refreshed at launch):

```
[OPUS] FF-5A — Build the forecast dashboard section: run explorer + status page

Read CLAUDE.md (Git §, GitHub Actions §), docs/forecast-development-plan-2026-07.md
§8 (§7 binds), scripts/register_hindcast.py + build_manifest.py (the two existing
patterns), docs/codebase-site/{forecast-validation,forecast-bands,backcast-runs,
calibration-status}.html, and the accessibility-audit skill notes.

1. Registry namespace: frontend/data/forecast/registry/<id>.json +
   runs/<id>.js mirroring the backcast sidecar/payload split, covering every FF run
   kind (t1f/t1x/t1h/t2/t3-golden/ces-campaign/pb-band) with rubric JSON embedded.
   Migrate register_hindcast.py into a general register_forecast_run.py (hindcast
   sidecars keep working; one registration path — rule 19 spirit).
2. docs/codebase-site/forecast-runs.html — run explorer (#iso=<ISO>&run=<id>):
   filterable by kind/tier/ISO; per-run page shows rubric category verdicts, evolution
   ledger tables (retire/build/backstop by year), invariant chips, capacity/CO2/price
   trajectory sparklines, wall/RSS, run_config link. Self-contained data island OR the
   deploy-built manifest pattern — pick ONE, document why, keep the backcast CI gates
   blind to the new namespace.
3. docs/codebase-site/forecast-status.html — per-ISO program status: tier reached,
   gate scorecard (rubric categories), golden/candidate state, flip-gate state, open
   plan-§1.2 rows. forecast-validation.html becomes a redirect stub or a section of
   the new page (keep old sidecar links working); forecast-bands.html links in.
4. Wire into deploy-pages.yml ONLY if the manifest pattern is chosen (no new
   workflows; extend the existing build step). Verify with the local file:// preview
   and the accessibility-audit skill. Update this plan §8 + CLAUDE.md rule-15 wording
   if registration mechanics changed. Push via mcp__github__push_files.
```

---

## 9. Doc migration ledger (2026-07-17)

In-file banners added where marked ⚑; everything is indexed here either way. "Record"
docs (findings, memos, decisions, hindcast reports) are NOT archived — they are the
evidence base and stay as-is.

| Doc | Disposition |
|---|---|
| `docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` ⚑ | Coordination → this plan (L-CAP); remains the lane's technical spec (§2.1 gate, §3 T-R bands, §5 data needs). Its §4 prompts are superseded by §6 here. |
| `docs/handoffs/national-ces-eac-premium-plan-2026-07.md` ⚑ | Coordination → this plan (FF-3B); W1+W2 merged; §7/§8 W3-R/W4/W5 specs remain binding and are invoked by FF-3B. |
| `docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md` ⚑ | ARCHIVED — waves executed; scorecard/battery definitions remain citable; successor lanes live here. |
| `docs/handoffs/forecast-validation-program-2026-07.md` ⚑ | ARCHIVED — machinery delivered (invariants, ledger, hindcast, goldens); hindcast band tables remain citable (FC-3). |
| `docs/handoffs/capacity-economics-plan-2026-07.md` ⚑ | ARCHIVED — stages executed; open remainders (FOM default flip, foresight posture) tracked as plan-§1.2/FF-1B/FF-2A items. |
| `docs/handoffs/cx4-datacenter-load-design-2026-07.md` ⚑ | Mechanism LANDED since authoring; remaining trajectory/siting/posture items = FF-1C. Spec stays citable. |
| `docs/handoffs/probability-bounds-plan-2026-07.md` ⚑ | Machinery landed; PB-5 scheduled as FF-4C (owner-gated). Spec current for FF-4C. |
| `docs/handoffs/probability-bounds-prompts-2026-07.md` | Companion prompts — superseded for scheduling by FF-4C; content current (ledger-marked only). |
| `docs/forecast-validation-plan.md` | Already SUPERSEDED-bannered (historical). |
| `docs/forecast-methodology-gaps-2026-06.md` | Already supersession-noticed → gap-register. Historical. |
| `docs/forecast-methodology-gaps-prompts-2026-06.md` ⚑ | STALE — do not execute; banner added. |
| `docs/multi-iso/neiso-forecast-prep-prompts.md` ⚑ | STALE — overtaken by NEISO forecast runs; banner added. |
| `docs/handoffs/confirmed-retirement-plan-2026-07.md` | EXECUTED design record (self-status'd; default ON since 2026-07-05). |
| `docs/handoffs/emissions-co2-rate-plan-2026-07.md`, `emissions-mass-cap-plan-2026-07.md`, `emission-control-retrofit-forward-channel-2026-07.md` | EXECUTED design records (self-status'd); retrofit channel stays gated-inert pending the E2 NOx/SO2 forward wave (tracked as an L-INP backlog item, chartered on FF-0D evidence). |
| `docs/forecasting-entry-exit-assessment.md` | LIVE verdict — updated by FF-2C/FF-4B. |
| `docs/forecast-invariant-findings.md`, `docs/gap-register-2026-07.md`, hindcast reports, `position-calibration*`, `capacity-clearing-flip-memo*`, `retirement-dof-identification*`, `blk8-*`, `full-horizon-findings*`, `cross-model-corridor*`, `driver-battery*`, `equilibrium-battery*`, `elcc-curves*`, `ces-w1b-*`, `ces-ci-*` | RECORDS — untouched, cited throughout. |

---

*Produced 2026-07-17 (planning session — no LP solved, no parameter changed, nothing
registered). Verified against `origin/main` HEAD `c95176e` and the three survey passes
recorded in this session. Owner decisions currently pending inside this program:
FF-0C decision box (retirement rule), DC BAU posture (FF-1C), entry-lookahead +
availability defaults (FF-1B/FF-2A boxes), per-ISO flip sign-offs (FF-2C), NYISO R5a
option (FF-3D), golden config freeze (FF-4A), PB-5 go (FF-4C).*

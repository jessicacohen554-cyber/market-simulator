# Model Positioning Matrix — refresh 2026-10 (AUDIT-E)

**STATUS: RECORD** — third-party audit deliverable E, refreshing
`docs/audit/model-positioning-matrix-2026-08.md` (the 2026-08-15 baseline, `9f48419`).
Repository claims verified at `origin/main` @ `d7ff7c20` (2026-10-02), read-only, no
solve. Comparator claims are from public documentation as of the auditor's knowledge;
none was operated hands-on; anything not independently documented is marked
**unverified**. Tags: **[vendor]** self-description, **[indep]** independent source.

## 1. "This model" column — cell-by-cell delta since 2026-08

| Axis | 2026-10 claim | Δ | Reason / citation |
|---|---|---|---|
| Category | Chronological zonal production-cost/price simulator (full-8760 LP, prices = duals) with a one-pass annual capacity-evolution wrapper; forecast 2026–2050, backcast for calibration | UNCHANGED | `CLAUDE.md` "What this is", rules 4/8/10 |
| Topology | **Nine** regions on one ISO-agnostic LP: ERCOT 7 / CAISO 6 / MISO 6 / PJM 8 / NYISO 5 / NEISO 5 / **SPP 2 / NWPP 5 / SOCO 3** zones (SOCO is a single BA with no LMP market; NWPP a WECC BA pool); pipe-and-bubble + interface groups; no PTDF/DC-OPF | CHANGED | zone lists counted in `src/market_sim/config/iso_configs.py::_{spp,nwpp,soco}_config` (lines 1809/2049/2314); `CLAUDE.md` "What this is" |
| Commitment / dispatch | Pure LP, P0 base-cost → P1 bid-cost, no MIP; P2 archived behind `--enable-legacy-p2`; three ISO-exclusive P1-native `min_gen` bridges (CAISO RA must-offer, ERCOT gas-CC, NYISO slow-start) sharing `model/commitment.py::caiso_ra_mustoffer_min_gen`; ERCOT offer-surface/negative-price variants default-off | CHANGED (sharpened) | `CLAUDE.md` "Dispatch and commitment"; `pipeline/solve.py` header (P1 warm-starts from P0 basis; cross-year warm start default off) |
| Chronology | Full 8760 always; **each backcast year solved alone in its own shard container, no cross-year state** (rule 36); forecast years sequential in one invocation | CHANGED | rules 8, 36; `MARKET_SIM_WARMSTART_XYEAR` / `MARKET_SIM_P1_BASIS_SEED` default off (`pipeline/solve.py:22-36`) |
| Price formation | LP duals on energy balance; in-LP reserve co-optimization incl. ERCOT ORDC steps; published-formula ORDC/RTORPA + NYISO RCPF overlays; REC = RPS-row dual; **one authorized price-tuning channel** (`offer_curve_by_group` bands, ex-ante, one value across years, ledgered) | CHANGED (channel now codified) | rule 1 amendment (owner 2026-09-05); `results/scarcity.py`, `results/rcpf.py` |
| Endogenous expansion | One-pass myopic screens (exits → announced → CCS → economic retirement → known additions → entry → optional backstop → RPS-dual dispatch); per-ISO arms (PJM capacity-market clearing, published adequacy requirement, VRE accreditation vintage, PJM/MISO sector gate); storage entry as value stack | CHANGED (arms added, posture same) | `CLAUDE.md` "Capacity evolution"; rule 10 |
| Validation regime | Machine-scored rubric (`scripts/calibration_verdict.py`, `iso_determination` worst-of over every registered year); **holdout tiers REMOVED 2026-09-09** — any year may be solved/scored/registered, no certified out-of-sample number; C3c lone-failure caveat kept (rule 22 `[R-C3C]`); PRECOMMIT/RESULT records (590 PRECOMMIT files under `docs/records/`); DOF ledger per keeper (rule 21); forced-energy budget (rule 20); mechanism-matrix test ledger (rule 28); public dashboard, keeper-only retention (rule 15) | **CHANGED (weakened on out-of-sample; strengthened on accounting)** | `docs/governance/rule-history.md` §18; `scripts/lib/holdout_policy.py` docstring ("NO LONGER AUTHORIZES ANYTHING") |
| Current determinations | **W0 EIA-860 settlement keepers promoted 2026-10-02 for all nine ISOs** (`frontend/data/backcast/keepers/*.json`, e.g. `2026-10-02-w0-pjm-fix2`, `2026-10-02-w0-soco-fix2`). ISO-level label read from `frontend/data/backcast/status/<ISO>.js`: MISO / NYISO / NEISO / SPP CALIBRATED; ERCOT / CAISO / PJM / NWPP / SOCO NOT-YET. **Not re-scored by this audit** | CHANGED | keepers JSON `keeper` field; status shards; `calibration-complete.json` carries PJM NOT-YET text dated 2026-09-30 and four `withdrawn` entries — a stale-text mismatch the auditor flags, not resolves |
| Reproducibility | `cache_key()` now carries a **solve-surface fingerprint** (seven registry modules, per-ISO projected, frozen declaration hashes; derived, never settable); every bundle records `solve_surface.json`; `run_config.json` is the recipe | CHANGED (new since 08) | `src/market_sim/config/solve_surface.py` (owner ruling Q54, capx D79) |
| Execution governance | Every solve in a shard; parent never runs an LP; one shard ≤ 20 min commit; full bundle pushed by `.gitignore` negation; promotion is one command with prune + audit; nothing deleted before owner ruling (rules 31–35) | CHANGED (new since 08) | `CLAUDE.md` rules 31–36; `scripts/promote_keeper.py`, `scripts/shard_prompt.py` |
| Solver / performance | HiGHS via `highspy`, direct CSC, dual simplex; ~183–339 s per ISO-year at ~13.2 M columns (2026-07 baseline) — **not re-measured**; per-year shard containers now the unit of wall-clock | UNCHANGED (number), CHANGED (regime) | `docs/records/misc/wallclock-baseline-2026-07.md`; `wallclock-desk-log-2026-09.md` |
| Data ecosystem | Nine-ISO US pipeline (EIA-860/923/930, EPA CAMPD/CEMS, eGRID, ISO disclosures) behind schema-validated raw→clean contract; blobless partial clone with declared data profiles; W0 adds published seasonal unit envelopes and vintage-dated EIA-860 retirements | CHANGED | `data/dictionary/`; `configs/data-profiles.yaml`; `docs/records/governance/closeout-2026-10/RESULT-closeout-b-w0-foundation-2026-10-02.md` |
| Forecast program | Phase A (infrastructure + ≤ 5-year POC) ACTIVE; all ISOs at **T1** (SPP T1-H hindcast); Phase B golden 2026–2050 solves DEFERRED behind §2.1b; gate (a) keeper marker re-keyed 2026-10-02, **fail** for 7 of 9 boards, pass PJM/NEISO on the 2026-09-06 board seed (stale vs the 2026-10-02 keepers) | CHANGED (program state), UNCHANGED (no golden solve exists) | `docs/forecast-development-plan-2026-07.md` §0/§2.1b; `frontend/data/forecast/program-status.json` (`generated` 2026-09-06) |
| License / users | Private, single-owner governance, no docket history, no external users | UNCHANGED | — |

Net: 11 of 13 cells CHANGED. The two substantive moves are (i) scope — six → nine
regions with full-span keepers everywhere; (ii) validation — the holdout regime is
gone and the accounting apparatus (shards, solve-surface key, DOF ledger, mechanism
matrix, promotion invariants) is heavier.

## 2. Capability matrix

| Tool | Category | Network | Commitment | Chronology | Price formation | Endogenous expansion | Published validation regime | License |
|---|---|---|---|---|---|---|---|---|
| **This model** | PCM + one-pass evolution wrapper | Zonal, 2–8 zones × 9 US regions, pipe-and-bubble | Pure LP; P0/P1 + physics-gated bridges | Full 8760, one year per container | LP duals + in-LP reserve/ORDC; published scarcity overlays; one declared band channel | Yes — myopic screens, non-equilibrium by design | Machine-scored rubric, pre-registered PRECOMMITs, public NOT-YET labels; **in-sample, no holdout** | Private |
| PLEXOS (Energy Exemplar) | PCM + CEM (LT/PASA/MT/ST) | Zonal + nodal | MILP SCUC, co-optimized reserves | 8760 to 5-min | Duals; administrative scarcity + VoLL | Yes (LT Plan) | Regulator-driven SEM/NERA backcast series [indep] | Commercial |
| Aurora (Energy Exemplar) | PCM + LTCE | Zonal (ATC links); nodal offered | Not publicly documented | Hourly/sub-hourly 8760 | Marginal unit sets zonal price; reserve-margin adder | Yes, iterative | IRP-docket benchmarking, no rubric [indep] | Commercial |
| EnCompass (Yes Energy) | Unified CEM + PCM | Zonal + nodal (shift factors) | SCUC/SCED, details not public | Annual to 1-min | Zonal + nodal LMP | Yes, integrated | Docket benchmarking, no rubric | Commercial |
| GenX (MIT/Princeton) | CEM, configurable ops | Zonal transport | LP / clustered UC / MILP UC | 8760 or representative periods | LP duals, VoLL | Yes, single optimization | Per-study, peer-reviewed | GPL-2.0 |
| PyPSA-USA | CEM + PCM framework | Nodal DC-OPF, 30–4,786 nodes, or zonal | LP; optional MILP UC | Flexible | Nodal duals, VoLL | Yes, incl. transmission | Per-study; PyPSA-Eur price retrospective is the open-model price hindcast | MIT |
| Switch 2.0 | CEM (Pyomo) | Zonal transport | Linearized or MIP UC | Sampled days, multi-period | LP duals | Yes | GE MAPS intercomparison (Hawaii) [indep] | Apache-2.0 |
| NREL ReEDS | CEM | 134 BAs, transport | Pure LP, no UC | Representative timeslices/days, 2-yr steps | Planning duals | Yes incl. retirements | Standard Scenarios; one builds hindcast (Cole & Vincent 2019) | BSD-3 (repo archived 2026, successor **unverified**) |
| EPA IPM (ICF) | CEM for regulatory impact | ~64–67 US regions, transport | LP, load-duration segments | Seasonal × load segments, run years to 2050 | Marginal-cost duals (no market emulation) | Yes, inter-temporal | EPA-published assumptions docs + docket review; no backcast rubric [indep: EPA Platform v6/2023 documentation] | Proprietary (EPA-contracted; outputs public) |
| EIA NEMS (EMM) | Integrated energy-economy; EMM electricity module | 25 EMM regions | LP dispatch over load segments (ECP/EFD) | Load-duration slices, annual to 2050 | Regional marginal cost + capacity payments | Yes | AEO retrospective reviews (EIA publishes own forecast-vs-actual) [indep]; model doc public | Public (code available; practical reuse limited) |
| E3 RESOLVE | CEM for IRP/policy (CPUC) | Zonal, few zones | LP, sampled days | Representative days, multi-period | Duals | Yes | CPUC docket review; RESOLVE→SERVM/PCM hand-off for ops validation [indep: CPUC IRP filings]; no backcast rubric | Open-sourced for CPUC (**license unverified**) |
| Dispa-SET (JRC/KU Leuven) | PCM / UC | Zonal, NTC | MILP UC (LP relaxation option) | Full 8760, rolling horizon | Duals, VoLL | No (separate) | Per-study (EU power system papers) | EUPL |
| Sienna / PowerSimulations.jl (NREL) | PCM framework (Julia) | Nodal (PTDF/DC-OPF) or copper-plate | Configurable: MILP UC, ED, templates | Simulation sequences, sub-hourly | Duals via JuMP | Companion (PowerSimulationsCapacityExpansion, **unverified**) | Per-study; software papers | BSD-3 |

Comparator rows for PLEXOS, Aurora, EnCompass, GenX, PyPSA, Switch, ReEDS carry the
2026-08 §3 fact-sheet sources unchanged; IPM, NEMS, RESOLVE, Dispa-SET and Sienna are
new rows compiled from public model documentation as of the auditor's knowledge and
should be read as **unverified** where tagged.

## 3. Validation norms — candid placement

The 2026-08 matrix said this repository's regime "exceeds the documented validation
practice of every surveyed comparator", resting on three legs: a machine-scored
rubric, a **three-tier fail-closed holdout** (train 2023–2025 / validation / locked
test with spend freezes), and pre-registration. On 2026-09-09 the owner removed the
holdout year machinery outright (`rule-history.md` §18, "Remove the holdout year
rule", scope "Year machinery only, keep C3c"). The record itself states the cost:
*"there is no longer a certified out-of-sample number anywhere in this program,
because no year is protected from being iterated against."* Measured effect at
removal: 0 determination flips over 15 registered runs — i.e. the scores did not
change, what is permitted did.

What that means against the comparators:

- **Hindcast:** every registered keeper is a full-span backcast (2019–2025 for most
  ISOs) scored against actuals with public per-criterion verdicts. Only the SEM/NERA
  PLEXOS series and the PyPSA-Eur retrospective publish anything comparable; NEMS
  publishes forecast-vs-actual retrospectives but of its own AEO, not a backcast of a
  frozen configuration. On hindcast transparency this model still leads.
- **Out-of-sample:** none. No comparator publishes a certified out-of-sample price
  number either, so the model is now **at parity**, not ahead. The claim "held-out
  year X scored Y" may no longer be made for any year.
- **Pre-registration:** 590 PRECOMMIT records, direction-blind promotion rules, and a
  rule-1 channel that must be declared ex ante. No comparator does this. But
  pre-registration without a protected year constrains *process*, not *information*:
  the same years are iterated on, and each PRECOMMIT is informed by every prior
  score on them. Also, closeout promotions now land on mixed-SHA legs with
  "zero-LP inert proofs" (PJM keeper note) — defensible, but a reviewer must trust
  the G-DRIFT classification rather than a re-solve.
- **Governance quality:** self-administered, single-owner; the regime demotes its own
  keepers (five of nine ISOs read NOT-YET today) and that candour survives the
  holdout removal. It has never faced an adversarial docket.

Honest placement: the model has moved from **"stricter than any comparator"** to
**"in-sample calibration with transparent, pre-registered accounting"** — better
documented than any comparator's calibration, but no longer offering a validation
category the comparators lack.

## 4. Where this model sits

**What it is.** A merchant-behaviour, zonal, full-chronology production-cost and
price simulator for nine US regions, with a myopic annual fleet-evolution wrapper
bolted directly onto the 8760 LP rather than soft-linked to a separate CEM. Its
nearest commercial siblings on formulation are the LP/heuristic-commitment zonal
tier (Aurora, legacy SEM-PLEXOS configurations); its nearest open sibling on
chronology is a GenX or PyPSA run forced to 8760 with LP UC. It is unusual in three
ways: in-LP ORDC/reserve co-optimization at zonal grain with published-formula
scarcity overlays; a reproducibility contract (solve-surface-keyed cache,
`run_config.json`, DOF ledger, per-year isolated containers) that no comparator
documents; and a public, machine-scored calibration dashboard that names its own
failures.

**What it is not.** It is not a nodal tool (no PTDF, no congestion/basis/FTR; GridView,
EnCompass nodal, PyPSA-USA nodal and Sienna all beat it there). It is not a
co-optimized capacity-expansion model (ReEDS, GenX, PyPSA-USA, Switch, IPM, NEMS,
RESOLVE solve investment jointly; this model screens one pass at a time and builds no
transmission). It is not an adequacy Monte-Carlo engine (no weather/outage draws).
It is not a validated forecaster: no golden 2026–2050 solve exists, the forecast
program is at T1 proof-of-concept for every ISO, and its gate-(a) board is stale
against the 2026-10-02 keepers. And after 2026-09-09 it carries no out-of-sample
certification.

**Who would and would not use it.** A trader, IPP or policy analyst who wants
transparent, reproducible hourly ERCOT/PJM/MISO-class price formation with explicit
scarcity mechanics, and who values being able to read every free parameter's source,
would prefer it to Aurora/PLEXOS/EnCompass *if* they can live with zonal resolution,
a private codebase and no vendor support. An IRP or regulatory filer would not: the
commercial tools have docket standing, nodal options and stakeholder-vetted
databases this model lacks. A national-scale decarbonization study would reach for
ReEDS/GenX/PyPSA-USA/IPM/NEMS, whose co-optimized expansion and transmission answer
the question this model deliberately refuses to pose at equilibrium. A European or
adequacy-focused user has no reason to look at it (US-only, no Monte Carlo;
Dispa-SET/Antares/Sienna fit better). Its genuine niche is narrow and real: a
calibrated-on-record, mechanism-audited US price simulator whose main competitive
asset is the honesty of its own ledger, not its formulation.

## 5. Discrepancies noticed while verifying (for the owner, not resolved here)

1. `frontend/data/backcast/calibration-complete.json` carries PJM determination text
   dated 2026-09-30 ("NOT-YET on 2026-09-30-pjm-next16-ovec") under a `keeper` of
   `2026-10-02-w0-pjm-fix2`, and lists ERCOT/CAISO/NYISO/SPP as `withdrawn` while
   their keepers JSON show 2026-10-02 W0 keepers. Either the re-key did not rewrite
   the determination text or the file is intentionally two-layered; a reader cannot
   tell which from the file alone.
2. `frontend/data/forecast/program-status.json` is `generated` 2026-09-06 but its
   gate-(a) rows say "RE-KEYED 2026-10-02 by promote_keeper.py" with `fail` for
   seven ISOs — the board mixes a month-old seed with a same-day stamp; NWPP and
   SOCO are absent from `isos` although they now carry keepers.
3. The 2026-07 wall-clock baseline (183–339 s per ISO-year, six ISOs) has not been
   re-measured for the three new regions or under per-year shard containers; the
   solver cell therefore reports a stale number and says so.
4. The 2026-08 matrix's "206 pre-registration documents" is now 590 PRECOMMIT files;
   the count was not audited for duplicates or withdrawn records.

---

*Prepared read-only at `d7ff7c20`, 2026-10-03, under a 10-minute budget. Comparator
claims not re-verified against live vendor documentation in this pass; repository
claims cite files at HEAD. Determination labels were read from committed status
shards, not recomputed.*

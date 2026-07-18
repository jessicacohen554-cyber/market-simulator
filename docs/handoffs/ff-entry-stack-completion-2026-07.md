# FF-2A — Entry-stack completion (2026-07-18)

**Charter.** `docs/forecast-development-plan-2026-07.md` §6 Wave 2, FF-2A: close
the entry stack — (1) BLK-7/term-(c) VRE capacity revenue in the entry screen,
(2) term-(e)+BLK-10 rate-limited need-proportional sizing, (3) a cited
clearance→COD interconnection/construction lag, (4) the `entry_lookahead_reprice`
posture recommendation (owner decides), (5) the state-RPS attribute pattern
beyond PJM where the published-parameter construction exists. Headline metric:
the CES §7 R1 criterion — **solar recall > 0 in ERCOT and PJM** on the re-run
hindcast additions bands. Everything lands as a default-off gate (byte-identical
defaults); nothing is residual-fitted (rules 1/13/14); probe runs register on
the forecast-validation dashboard only.

**State at session start (FF-1A / R-NEW committed artifacts, 2026-07-18):**
PJM solar recall is already > 0 under R-NEW+cmc (model 24.0 GW vs 13.07 actual —
the miss flipped from −100 % to +84 % over-build), ERCOT solar is still exactly
**0 vs 25.08 GW** even with the lookahead armed, and the PJM backstop still
over-fires: **2.5 GW** gas_ct in 2025 (down from 6.43 pre-R-NEW, vs 0.447 GW
actual) — the gap-register §3.9 BLK-10 gate for sizing rework is satisfied.

---

## 1. Methodology grounding (plan §4 — consulted before inventing)

| Practice | Source | Disposition |
|---|---|---|
| Relative growth constraint: annual installs hard-bounded at **200 % of the prior maximum** annual installation rate, by tech/region | NREL ReEDS Model Documentation (2025), growth-constraints section | **ADOPTED** verbatim as `ENTRY_GROWTH_LIMIT_MULTIPLE = 2.0` on a measured EIA-860 seed. The intermediate capital-cost penalty bands (10 % at 130–175 %, 50 % at 175–200 %) are **REJECTED**: a screening model has no capex-penalty channel, and porting them as revenue haircuts would be an unidentified tunable (rules 13/14). |
| Interconnection lag empirics: median **IA→COD ≈ 25 months** (projects built 2016–2023, 861-project sample); median IR→COD ≈ 5 yr (2022–23 builds); completion rates gas 31 % / wind 20 % / solar 13 % / batteries 11 % | LBNL "Queued Up" 2024 edition | **ADOPTED** (IA→COD → `ENTRY_COD_LAG_YEARS = 2` uniform; the screen's clearance ≈ executed IA + FID). Per-tech IA→COD medians are unpublished — LBNL notes batteries fastest / wind slowest — so the uniform median is the zero-DOF value; an EIA-860 proposed-pipeline per-tech refinement is recorded as future work. Completion rates NOT adopted as an entry haircut (they describe queue *requests*, not cleared decisions). |
| GenX `Max_Cap` build limits (total capacity per resource/zone) | GenX.jl documentation | **REJECTED for this gap** — total-resource-potential caps address a different constraint (resource supply curves) than annual throughput; the repo's static per-tech queue caps already play the annual role. |
| PLEXOS LT / Aurora lumpy integer entry with convergence iterations (build until marginal entrant NPV → 0) | PLEXOS LT / Aurora LT documentation practice | **REJECTED** — entry-until-zero-profit needs within-year price re-solve iteration, forbidden by the one-pass rule (rule 10). Recorded as the honest gap behind "need-proportional" demand-side sizing (§3.3). |
| Prescribed near-term builds from the actual in-flight queue (ReEDS prescribed capacity) | ReEDS documentation | **DEFERRED** — the model's `load_planned_additions` deliberately skips VRE rows (pool double-count guard). Without a vintage in-flight-queue seed, arming the COD lag in a vintage-start hindcast shifts the whole entry path late by construction (§4.3). Wiring the vintage proposed-sheet VRE queue as the lag's complement is the named follow-up. |

## 2. What landed (all gated, default-off, byte-identical at defaults)

| Gate (`ScenarioConfig`) | Mechanism | Identification |
|---|---|---|
| `entry_vre_capacity_revenue` | Wind/solar entry candidates earn `capacity_price_per_firm_mw_yr × resolve_renewable_capacity_credit(...)` — the SAME price seam thermal entry uses and the ONE adequacy-credit resolver (penetration-indexed published ELCC curves under `renewable_elcc_curves`), evaluated at the model's own installed nameplate; RA-saturated build zones collapse the payment (same locational gate as thermal). Energy-only ISOs price capacity at 0 → structural no-op (rule 19: ledger and payment can never diverge). Storage already earns its RA value in the storage value-stack screen — nothing added there (one mechanism per phenomenon, rule 19). | BLK-8 §4 measured the $0; the payment construction is the ISOs' own (PJM ELCC × clearing price etc.), zero new parameters |
| `entry_rate_limits` | Per-tech annual builds (economic screen) AND the reserve-margin backstop capped at `ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) × prior-max annual build`, seeded from the measured EIA-860 record at the run's vintage (`data.build_throughput.max_annual_build_gw_by_tech`, trailing `ENTRY_THROUGHPUT_WINDOW_YEARS = 10` window — vintage-respecting: a 2020-vintage hindcast reads `vintage_2020/`, IS-2020-clean) and **rising endogenously** as the model builds (prior max includes model years — the ReEDS relative-growth dynamic). Static per-tech caps and the ISO budget still bind on top; gas_ct economic entry and the backstop draw ONE budget (rule 19). Unseeded techs carry no ladder (rule 25 neutral fallback). | ReEDS 200 %-of-prior-max hard bound (cited); seed measured from EIA-860 (rule 13: regenerates per vintage) |
| `entry_commissioning_lag` | Economic entry decides in year Y, commissions at Y+2 (LBNL IA→COD median); pending (decided-not-online) MW are netted against the per-tech caps in later decision years — the developer's view of the queue, the structural anti-cobweb once decision and COD separate. Evolution ledger records `decision_year` + `cod_year` per entry (`entry_pipeline` events; item 3's ledger contract). | LBNL Queued Up 2024 (cited in `docs/parameter-citations.md`) |

Measured growth-ladder seeds (GW/yr, trailing 2011–2020 at the 2020 vintage —
what the hindcast probe legs run on):

| ISO | solar | wind | gas_cc | gas_ct |
|---|--:|--:|--:|--:|
| ERCOT | 2.473 | 3.472 | 2.570 | 0.785 |
| PJM | 1.220 | 1.271 | 11.664 | 0.551 |
| MISO | 0.618 | 4.367 | 1.723 | 0.742 |

So the ladder's binding first-year caps (2×seed) are: PJM gas_ct **1.10 GW**
(the BLK-10 rate limit — before-number 2.5 GW fired), PJM solar 2.44 GW
(vs the static 6.0 the R-NEW leg built at), MISO solar 1.24 GW, ERCOT solar
4.95 GW (≈ the static 5 — ERCOT sizing is essentially unchanged, which is the
honest expectation: ERCOT's solar zero is a price-signal term-(a) problem, not
a sizing problem — BLK-8 verdict, G-20/G-22 lane).

## 3. Measured results (probe legs, forecast-validation dashboard)

_Legs: `pjm-2021-2025-realized-cmc-ff2a` / `miso-2021-2025-realized-cmc-ff2a`
(the R-NEW cmc config + `--entry-vre-capacity-revenue --entry-rate-limits`) and
`ercot-2021-2025-realized-comp-ff2a` (the R-NEW comp config +
`--entry-rate-limits`; the VRE-capacity arm is a provable no-op in energy-only
ERCOT and is not armed). `--entry-screen-diagnostics` armed on all
(decision-neutral). `--entry-commissioning-lag` NOT armed (no vintage
in-flight-queue seed exists — §4.2). 2022 bridged, never solved (rule 22).
Zero leakage-guard violations. Registered sidecars:
`frontend/data/hindcast/{pjm,miso,ercot}-…-ff2a.json`._

### 3.1 Headline — CES §7 R1: solar recall (cumulative GW, 2021→2025)

| ISO | actual | R-NEW before | FF-2A probe | movement |
|---|--:|--:|--:|---|
| PJM | 13.07 | 24.0 (+84 %) | **19.32 (+48 %)** | recall > 0 ✓; the growth ladder cuts the over-build burst nearly in half toward actual |
| MISO | 18.65 | 12.0 (−36 %) | **3.71 (−80 %)** | recall > 0 but worse: the measured 0.618 GW/yr seed bottlenecks 2022–23 (built at ladder cap both years), and 2024–25 the signal itself dies (§3.3) — term (a), not sizing |
| ERCOT | 25.08 | 0.0 | **0.0 (−100 %)** | as pre-registered before the leg ran (§2): the sizing arm is near-inert in ERCOT (ladder caps ≈ static caps) and the zero is the starved capture price — now MEASURED per year in §3.3 |

**R1 verdict: PJM ✓ (recall > 0, over-build tightening), ERCOT ✗ (still 0).**
The ERCOT zero is *attributed, not closed*, by this session — consistent with
the BLK-8 decomposition (term (a) dominant, routed to the scarcity/lookahead +
G-20/G-22 screen-revenue lane). Every sizing/capacity-revenue term this
charter owns is now in place and measured; the ERCOT diagnostics quantify the
residual precisely: solar capture revenue 9.1k $/MW-yr in the 2022–23 screens
(pre-lookahead-formation years), 52.1k in 2024 and 44.4k in 2025 (lookahead
pro-forma active) against a 66.6k → 60.0k hurdle — best-year margin
**−$9.7k/MW-yr (2024)**, with the would-be capacity payment structurally $0
(energy-only). Closing ERCOT solar needs ~$10–16k/MW-yr more energy-side
signal, squarely the G-20/G-22 screen-revenue residual (flip memo R-4).

Notable side-movement (same legs): freeing the shared ISO queue budget from the
VRE burst lets thermal entry track actuals better — PJM gas_cc −41 % → **−28 %**
(6.12 vs 8.53 actual), MISO gas_cc −100 % → **−22 %** (3.0 vs 3.87 actual).
MISO's ramp SHAPE now matches reality: actual solar CODs ramp 1.19 → 1.33 →
2.76 → 6.22 → 7.15 GW/yr; the ladder builds 1.24 → 2.47 (then the signal dies),
where the un-laddered leg built 6+6 in the first two years and stopped — the
sizing dynamic is right, the surviving miss is the price signal.

### 3.2 BLK-10 — backstop over-fire (before → after)

| ISO | actual gas_ct GW | pre-R-NEW | R-NEW (before-number) | **FF-2A** | ladder cap (2×seed) |
|---|--:|--:|--:|--:|--:|
| PJM | 0.447 | 6.43 | 2.500 | **1.103** (`gas_ct_adequacy_2025`) | 1.102/yr |
| MISO | 1.379 | — | 0.000 | **0.000** | 1.484/yr |
| ERCOT | 3.692 | n/a | n/a (backstop off, energy-only) | n/a | — |

The PJM 2025 backstop clips exactly at the measured gas_ct throughput ladder
(2 × 0.551 GW 2011–2020 max annual build) — the full-deficit-in-one-step
pattern is gone; a residual deficit now carries to the next year's screen. The
remaining +147 % gas_ct error (1.103 vs 0.447) is the adequacy-need signal
itself (position/curve lane), no longer the sizing mechanism.

### 3.3 Term-(c) measured attribution (entry-screen ledger, $/MW-yr)

Per-candidate `capacity_revenue_per_mw_yr` from the armed legs (the same
diagnostic that measured the BLK-8 $0):

| ISO-year | tech | energy | attribute | **capacity** | annual cost | margin |
|---|---|--:|--:|--:|--:|--:|
| PJM 2022–24 | solar | 61.5k → 47.5k | 74.9k | **0** (position long → curve pays ~0) | 66.6k → 61.8k | strongly + |
| PJM 2025 | solar | 46.3k | 74.9k | **+13.0k** | 60.0k | + |
| PJM 2025 | wind | 76.6k | 121.8k | **+67.6k** | 26.5k | + |
| MISO 2024 | solar | 51.3k | 0 | 0 (position long) | 61.8k | **−10.5k** |
| MISO 2025 | solar | 48.5k | 0 | **+10.2k** | 60.0k | **−1.3k** |
| MISO 2025 | wind | 5.0k | 0 | **+9.4k** | 26.5k | −12.0k |

Two measured findings: (i) under the CR-1 sloped curve the VRE capacity payment
is *position-gated* — $0 while the fleet is long, ~$10–13k/MW-yr (solar) once
the 2025 position enters the priced region, matching BLK-8's ~$8–11k would-be
sizing; (ii) it is *nearly pivotal exactly where BLK-8 predicted the class of
miss*: MISO 2025 solar closes to −$1.3k/MW-yr — the payment alone recovers
~89 % of the residual gap in the year the signal is closest. In PJM the state
blended-RPS attribute (74.9k) dominates and solar clears with or without the
payment — there the binding constraint is sizing (the ladder), not revenue.

### 3.4 LOYO / retirement integrity

The entry arms leave the retirement record byte-identical to the R-NEW legs
(PJM model 15.643 GW, recall 13/17 = 76 %; MISO 8.839 GW, recall 13/17 = 76 %;
same LOYO folds: PJM −2023 1.0/−2024 0.0/−2025 0.75, MISO −2023 0.79/−2024
0.0/−2025 0.76; TR-10a/b PASS on every fold, both ISOs). No hindcast
retirement verdict flips, so no new mechanism-driven LOYO question is opened;
the additions-side changes are the measured effect of the entry gates alone.
ERCOT likewise: retirement identical to the R-NEW comp leg (1.87 GW gas_st,
same fold verdicts), additions byte-identical too — the ERCOT rate-limit arm
measured as a no-op on the whole scorecard, the honest confirmation that
ERCOT's entry problem is not a sizing problem.

## 4. Owner-decision boxes

### 4.1 `entry_lookahead_reprice` default posture (item 4 — boxed, NOT flipped)

> **Recommendation: default-ON for forecast-mode production runs.**
> Evidence: G-30 single-term isolation
> (`docs/hindcast-reports/ercot-g30-entry-lookahead-2026-07-08.md`) — a pure
> price-signal change, zero fitted parameters (re-price the entering year's
> known net load against the current fleet with the published ORDC curve; every
> input an existing model quantity, rule-13 admissible, G-30-validated,
> zero-DOF), which (i) unlocked the first non-zero ERCOT solar entry (0 → 4 GW),
> (ii) halted the gas_st over-retirement (8.83 → 1.87 GW), and (iii) carries the
> intended negative feedback (the 2024→2025 pro-forma weakens as 2024's entry
> re-fills the stack). It is the screen-side half of the pro-forma a real
> developer runs.
> Honest counter-evidence: the pro-forma's level is not validated — RC-2A
> measured the screen signal as bimodal (starved raw duals in first-wave years,
> 757 → 242 $/kW-yr pro-forma later, "neither physical"), and the FF-1A ERCOT
> leg ran lookahead-ON yet still delivered solar = 0, so the lookahead alone
> does not close BLK-8's term (a). Default-ON changes every forecast cell's
> screen signal; the T1 gate battery (FF-2D) would re-baseline.
> **Owner decides; nothing flipped this session** (the flag stays default-off;
> hindcast probe legs arm it explicitly as before).

### 4.2 FF-2A gate posture for the production forecast config

> The three new gates land default-off. The probe evidence in §3 is the input
> to the owner's arming decision for T1/T2 forecast runs:
> - `entry_vre_capacity_revenue` — structurally real in every capacity-market
>   ISO (the real RPM/PRA clears solar/wind at ELCC × clearing price);
>   recommended ON wherever `capacity_market_clearing` is armed, and inert in
>   ERCOT by construction.
> - `entry_rate_limits` — replaces the full-cap/full-deficit one-step patterns
>   with a measured throughput bound; recommended ON for forecast runs
>   (the one-pass loop otherwise has no sizing dynamics at all).
> - `entry_commissioning_lag` — real physics, but arming it WITHOUT the
>   vintage in-flight-queue seed (§1 last row) under-builds the first
>   lag-years by construction. Recommended: HOLD until the planned-VRE queue
>   seed is wired (named follow-up), then arm both together.

## 5. Item 5 — state-RPS attribute pattern (adjudicated, not extended)

The owner's PJM construction needs BOTH published halves: (a) per-state
renewable-tier schedules blended by published load shares, and (b) a published
$/MWh compliance-price ceiling (ACP) to cost the RPS row's escape column and
cap the REC dual. Adjudication per ISO:

| ISO | (a) schedules | (b) ACP ceiling | Outcome |
|---|---|---|---|
| CAISO / NYISO / NEISO / PJM | published | published | already entered (`STATE_RPS_FLOORS` + `STATE_RPS_ACP`) — verified, unchanged |
| **MISO** | published (MN 26.5 % by 2025 + Xcel 31.5 %, Minn. Stat. §216B.1691; MI 50 % by 2030 / 60 % by 2035, 2023 PA 235; …) | **NOT published** — MN and MI enforce through IRP/compliance-plan proceedings with no ACP rate; IL's ACP applies to its PJM (ComEd) side | **NOT extended.** Inventing a MISO ACP = uncited tunable (rules 5/13); floors without an ACP leave the escape column uncosted. Recorded in the findings here; the STATE_RPS_FLOORS comment carries the pointer once the core patch lands. |
| ERCOT | target met ~2009, inert | n/a | zero rows stay (correct) |

## 6. DOF ledger (new parameters, each with identification)

| Parameter | Value | Identification | Fitted? |
|---|---|---|---|
| `ENTRY_GROWTH_LIMIT_MULTIPLE` | 2.0 | ReEDS published hard bound (200 % of prior max) | no |
| `ENTRY_THROUGHPUT_WINDOW_YEARS` | 10 | declared windowing choice bounding the seed to the modern (post-LGIP) throughput regime LBNL measures; never residual-tuned (rule 23) | no (declared, flagged `modeled`) |
| `ENTRY_COD_LAG_YEARS` / default | 2 | LBNL Queued Up 2024 median IA→COD ≈ 25 months (2016–2023 builds) | no |
| growth-ladder seeds | derived | EIA-860 at the run's vintage, formulaic (`max_annual_build_gw_by_tech`) — regenerates per vintage, responds to data updates only | no |

Open (named, unclosed): demand-side entry sizing (how much a profitable tech
*wants* to build below its throughput cap) has no identified construction under
the one-pass rule — ReEDS/GenX size via optimization, PLEXOS/Aurora via
convergence iteration; a margin-proportional heuristic was considered and
REJECTED as an unidentified functional form. Wind over-build (PJM +271 % /
MISO +67 % / ERCOT +58 % pre-FF-2A) therefore remains bounded by caps, not
sized by demand — recorded against flip-memo R-8.

## 7. Scope discipline

No default changed; no band widened; no residual-fitted value anywhere. All
mechanisms behind default-off gates whose defaults are byte-identical (cache
keys stable at `b688aa11b5a8ea6a` — gates in `_CACHE_KEY_OPTIONAL_FIELDS`).
Probe legs register on the forecast-validation dashboard only; 2022 stays an
evolved-never-solved bridge; no holdout year (2022/≤2021 beyond the hindcast's
own {2021} allowance/2019/H1-2026) solved, scored, or read (rule 22 / plan
§7.4).

## 8. Push-channel constraint — APPLY THE PATCH FIRST

This session's environment blocks every git push through its proxy (HTTP 413
on all packs, measured down to a 1-line commit), and the MCP `push_files`
channel replaces whole files from response content — for the 200–500 KB
rule-27 core files that is exactly the response-truncation failure mode
rule 27 forbids (the FF-1A `capacity.py` truncation + restore commit
`dfeb5b1` is the in-repo precedent). Disposition:

- **Pushed whole and verified (md5 fetch-back; JSON artifacts additionally
  accepted at JSON-equality where the only delta is the `ensure_ascii`
  serialization of an em-dash in a prose note):** the new additive modules
  (`config/entry_config.py`, `data/build_throughput.py`,
  `tests/test_entry_stack_ff2a.py`), `scripts/run_capacity_hindcast.py`, the
  probe bundle slim files + sidecars + reports, and this doc.
- **`docs/handoffs/ff2a-core.patch`** carries the four core-file diffs
  (`scenarios.py` +55, `capacity.py` +297/−20, `runner.py` +52,
  `parameter-citations.md` +4), generated by git from the locally tested
  tree (195 + 8 tests green) and verified byte-identical on the remote
  branch AND to apply cleanly on `origin/main`
  (md5 `0993fbd8b3024e05ece6e7007a333577`). **`git apply
  docs/handoffs/ff2a-core.patch` from the repo root is the first step for
  anyone checking out this branch** — until then the pushed harness/tests
  reference ScenarioConfig fields the patch adds.
- Plan §1.2 frontier row 3 (entry stack) needs its append-edit once this
  lands; the one-line update: *"Entry stack — FF-2A landed (gated): VRE
  capacity revenue measured near-pivotal (MISO 2025 −1.3k), BLK-10 backstop
  2.5 → 1.103 GW at the measured ladder, PJM solar +84 % → +48 %; ERCOT solar
  zero measured as a pure term-(a) price-signal residual (−9.7k best-year
  margin) — G-20/G-22 lane."*

*Produced 2026-07-18 (FF-2A). Code verified against `origin/main` HEAD
`483ab0b`; probe legs registered same-session (sidecars
`{pjm,miso}-2021-2025-realized-cmc-ff2a`, `ercot-2021-2025-realized-comp-ff2a`).*

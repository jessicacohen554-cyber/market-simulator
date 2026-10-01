# FFR-6A — Margin-gap decomposition of the repaired retirement screen vs the Potomac-SOM net-revenue benchmark

**Session.** FFR Wave 6, MEASUREMENT lane (owner decision D-20(a), sitting Addendum U.4/U.5,
signed 2026-08-05). Branch `claude/ffr-6a-margin-gap-decomposition-f9suco`, off `origin/main`
`57120845`. **This lane tunes nothing, arms nothing, fixes nothing** — the deliverable is a
measured decomposition of the FFR-5D-M finding plus an admissibility verdict per candidate
fix; any fix is a separate charter on these findings. NO lift recommendation (U.2's
determination is the manager's).

**The measured fact this starts from** (FFR-5D-M, `docs/handoffs/ffr-5d-price-object-2026-08-05.md`
§3, probe `docs/handoffs/ffr-5d/paired-arm-probe-2026-08-05.json`, registered arms
`ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}`): under the unified+repaired price object
the retirement screen fails essentially the whole ERCOT merchant fleet (entry_capped 564 /
63.0 GW in 2024, 554 / 66.1 GW in 2025), the adequacy admission cap does ALL retention work,
and the model retires 10.9 GW of gas_st pre-window (actual gas_st exits in the scored
actuals: 0.0) instead of the real 1.534 GW. Either the screen object is missing a real
revenue leg or the bar is mis-leveled. This doc says which, with measured decomposition.

---

## 1. The benchmark (intaken this session, rule 13: validation only, never an input)

Potomac Economics ERCOT State-of-the-Market net-revenue estimates, transcribed under the
data contract into `data/raw/som-competitive-conduct/som_competitive_conduct.csv` (ERCOT
rows, source PDFs committed under `data/raw/ERCOT/`; every row carries source_doc +
source_page):

| year | new CT net rev ($/kW-yr) | new CC net rev ($/kW-yr) | CONE ($/kW-yr) | stack notes |
|---|---|---|---|---|
| 2023 | 224–257 | 228–272 | ~80–130 | ~HALF of net revenue = ECRS price effects (monitor's own attribution); stack = Reserves + Energy + ECRS Effects |
| 2024 | 68 | 89 | CT 102–106, CC 116–121 | stack = Reserves + Energy Sales |
| 2025 | 52.59 (Houston ~59, West up to 177) | 82.96 | planning 140 (legacy PNM 105) | PNM 2025 ≈ $79/kW |

Existing-unit cost benchmarks the SOM itself cites (2024 SOM PDF p.119–120): existing-coal
FOM **$61.60/kW-yr** (EIA), coal VOM $6.40/MWh, ERCOT coal fuel ~$8.50/MWh → coal marginal
cost **≈$23.18/MWh** ("profitable to run in many hours" at 2024 zonal averages
$29.58–35.33/MWh); nuclear total generating cost ≈$31.76/MWh (NEI 2023) vs 2023 average
price $65/MWh ("highly profitable").

SOM's net-revenue construction is the **same pro-forma as the screen's**: attainable
`max(0, price − mc, reserve)` against generation-weighted real-time settlement prices, new-unit
proxy assumptions (CT HR 10.5 / CC 7.0 MMBtu/MWh, VOM $4/MWh, 10 % outage). The standing
replica (`docs/handoffs/fom-scarcity-revenue-audit-2026-07-05.json`) reproduces the published
SOM values within 0.89–0.97 from measured hub RT prices + Henry Hub gas — i.e. **the screen's
pro-forma CONSTRUCTION is validated against its own external observable; what varies between
arms is the PRICE OBJECT it consumes.**

## 2. PRE-REGISTERED READS (written and committed BEFORE the re-run's ledgers were read)

**Committed-artifact base (already in hand, no solve):** the probe JSON's cohort bar
decompositions (shipped coal at the 2021/2024 screens; unified gas_st at the 2021 screen and
coal at the 2024 screen); FFR-5A §3's per-fuel into-2025 unrepaired-lookahead revenue stack
(coal 296.7 / cc 329.9 / ct 267.0 / st 216.1 / nuclear 522.8 $/kW-yr); the bars (ATB FOM ×
multiplier: gas_ct 21, gas_cc 30, gas_st 35, coal 45×1.3=58.5, nuclear 130 $/kW-yr); the SOM
rows of §1.

**The one read NOT persisted in committed artifacts** (charter's re-run condition, stated):
the **per-fuel bar decomposition of the entry_capped fleet at the repaired 2024/2025
screens** (and the non-cohort fuels at the 2021 screen). `_apply_pipeline_retirements`
attaches `margin_detail` to every `entry_capped` row (`retirements.py:1506`), but those rows
live only in the evolution ledgers (`evolution_<year>.json`), which were never committed —
the FFR-5D-M slim bundle carries only `crossover_score.json` + meta + run_config, and
`results/` died with that container. The probe JSON summarizes entry_capped as n/MW by fuel
only. **Therefore ONE re-run of the unified arm is permitted and performed** — invocation
verbatim from ffr-5d handoff §2 + its one flag (`--capacity-screen-unified-lookahead`),
single invocation, years sequential (rule 12), cold. The shipped arm is NOT re-run: its two
objects are already characterized per-fuel (raw-duals screens fail the entire merchant
fleet with cohort-level margins recorded; unrepaired-lookahead screens clear every fuel with
the per-fuel stack recorded above).

Reads fixed now, computed after the ledgers land:

* **R1 — per-fuel repaired-level margin table.** Cap-weighted over each fuel's
  `entry_capped` + `decided` rows at the 2024-ledger and 2025-ledger screens:
  `net_revenue`, `energy_margin`, `reserve_uplift`, `attribute_revenue`,
  `capacity_revenue`, `as_annual_credit`, bar, `screen_price_mean/max`,
  `reserve_signal_mean`, `mc_mean`, `availability_mean`. Expectation stated in advance:
  the probe's coal rows show `reserve_signal_mean = 0.0` and `reserve_uplift = $0.0` at the
  repaired screens — if that holds fleet-wide, the repaired object's AS/reserve leg is
  literally zero while SOM's stack is materially Reserves in every year.
* **R2 — measured-price replica per fuel (the "what should the object produce" column).**
  Extend the standing replica construction (same `Σ_t max(0, p_t − mc) × 0.9 / 1000`
  pro-forma, measured hourly ERCOT RT prices from
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`) to the screen's fuel-class
  mc levels: gas_cc / gas_ct at the SOM proxy assumptions (already validated 0.89–0.97 vs
  SOM), coal at the SOM-cited mc ≈ $23.18/MWh (2024; 2023/2025 via the same PRB
  fuel-cost basis), gas_st at HR ~10.5 × gas price + VOM. This is rule-13-admissible as a
  *diagnostic benchmark* (it consumes measured outcomes, so it can never be a screen input —
  it exists to size the gap between the model's price object and the measured price level).
* **R3 — the identity split of the gap.** For each fuel-year: gap(total) = [SOM or replica]
  − [screen margin] split into (i) price-level term (replica at measured prices minus screen
  energy margin — the price-object gap), (ii) reserve-leg term (SOM reserves share vs screen
  `reserve_uplift`), (iii) bar term (bar vs SOM-cited going-forward benchmarks). Attribution
  claim to test: the price-object term dominates and the reserve term is the whole remainder;
  the bar term is small.
* **R4 — the actual-exits bound (question c).** The scored actual exits decoded from
  `data/raw/_validation-source/capacity_actuals_ercot.csv` (2021–2025 window): J T Deely 1–2
  (plant 6181, 486+446 MW coal, EIA retirement year 2023 — physically ceased operation
  end-2018, CPS Energy municipal decision announced years ahead), Decker Creek 2 (plant
  3548, 405 MW gas steam, Austin Energy municipal, 2022), plus <100 MW small units; V H
  Braunig 1–2 (477 MW gas_st, NSO-confirmed 2025-03 exits) are ABSENT from the scored
  actuals (EIA status OS, not RE). Read: against measured prices (R2), were ANY of these
  margin-negative vs their bars in their exit years? Expectation stated in advance: no —
  2021–2023 were high-revenue years for every thermal class (SOM §1), so the real exits are
  instrument/announcement-driven, not margin-driven, and no admissible margin screen can
  catch them.

**Comparability caveat, stated in advance:** SOM's CT/CC numbers are *new-unit proxies*
(HR 10.5/7.0); the screen's fleet rows carry unit heat rates (worse), so fleet-average screen
margins should sit BELOW the SOM new-unit numbers even at a correct price level. The replica
(R2) at matched assumptions is the like-for-like column; SOM anchors the level and the
reserves share.

## 3. Measured results

*(filled after the re-run's ledgers were read; nothing above this line changed after)*

**The re-run reproduced.** Invocation verbatim (ffr-5d §2 + the one flag), cold, at branch
head `7022bfa4` (off `origin/main` `57120845`; the only diff to FFR-5D-M's `331ac576` in any
solve-affecting file is comments in `constants.py`). Runtime `cache_key=49eac64f146b3460` —
**identical to FFR-5D-M's recorded unified key** — and the regenerated `crossover_score.json`
is **byte-identical to the committed one** (absent from `git status`; only
`meta.json`/`run_config.json` timestamps+provenance moved, restored to the committed bytes
after the read). Cohort rows reproduce the probe JSON exactly (2022 gas_st decided 45 /
10,942.9 MW at net $17.90 vs bar $35.00; 2025 coal decided 11 at $0.04; every entry_capped
census identical). Artifacts: `docs/handoffs/ffr-6a/perfuel-margin-probe-2026-08-06.json`
(R1, via `scripts/probes/ffr6a_margin_gap.py`),
`screen-revenue-stack-log-2026-08-06.txt` (the runtime per-fuel diagnostic, nuclear
included), `measured-price-replica-2026-08-06.txt` (R2).

### 3.1 R1 + R2 — THE PER-FUEL GAP TABLE at the repaired level

Screen margins are cap-weighted over ALL screened rows of the fuel ($/kW-yr; every non-energy
leg — reserve uplift, attribute, capacity, AS credit — is **exactly $0.00** on every fossil
row at every repaired screen, so net = energy leg). "Replica" = the same pro-forma on
MEASURED hub RT prices (R2). SOM = the published new-unit proxy (§1).

**Into-2024 screen (2024-ledger; repaired object off the 2023 solve: p_mean $10.49,
p_max $24.4, reserve signal 0.000) vs measured 2024 (mean $26.82, max $3,060, 161 h > $100):**

| fuel | repaired screen | replica @ measured prices | SOM published | bar | screen ÷ replica |
|---|---:|---:|---:|---:|---:|
| coal | **0.17** | 75.4 | — ("profitable in many hours") | 58.5 | 0.2 % |
| gas_cc | **3.79** | 86.7 | 89 | 30.0 | 4.4 % |
| gas_ct | **0.43** | 65.6 | 68 | 21.0 | 0.7 % |
| gas_st | **1.17** | 65.6 | — | 35.0 | 1.8 % |
| nuclear | 132.8 (clears by 2.8) | 139.8 (energy-only) | — | 130.0 | — |

**Into-2025 screen (2025-ledger; off the 2024 solve: p_mean $9.54, p_max $46.2, reserve
signal 0.000) vs measured 2025 (mean $32.49, max $1,570, 217 h > $100):**

| fuel | repaired screen | replica @ measured prices | SOM published | bar | screen ÷ replica |
|---|---:|---:|---:|---:|---:|
| coal | **0.04** | 97.2 | — | 58.5 | 0.04 % |
| gas_cc | **3.25** | 76.4 | 82.96 | 30.0 | 4.3 % |
| gas_ct | **0.28** | 47.0 | 52.59 | 21.0 | 0.6 % |
| gas_st | **0.73** | 47.0 | — | 35.0 | 1.6 % |
| nuclear | 131.1 (clears by 1.1) | 181.6 (energy-only) | — | 130.0 | — |

The earlier screens, same run (`screen-revenue-stack` log): **into-2022** (Uri-overlay-priced
2021 object) coal 139.1 / gas_cc 137.2 / gas_ct 88.2 / nuclear 479.2 all clear; gas_st 19.5
fails (hourly avail 0.595 + 2021-basis mc $44.26) → the 10.9 GW wave — vs replica-at-measured-
2022 gas_st **129.7 vs bar 35** (clears 3.7×): the wave is a false exit of the price/
availability object, not of gas_st economics. **Into-2023** (growth-scaled 2021 object) coal
230.1 / cc 235.1 / ct 171.5 / st 140.9 — coincidentally near measured-2023 levels (replica
234.1 / 240.0 / 216.4 / 216.4) because the carried Uri overlay hours mimic 2023's ECRS
scarcity in magnitude; nothing fails. Then the object priced off a post-Uri solve collapses:
**both repaired forward screens sit at 0.04–4.4 % of the measured-price margin for every
fossil class**, and only the adequacy admission cap (plus, for nuclear, a ~$113/kW-yr
attribute floor consistent with the §45U credit at the object's ~$10 average price) prevents
a fleet-wide exit wave.

### 3.2 R3 — the identity split of the gap

Per fuel-year at the repaired screens, gap = replica − screen ($/kW-yr):

* **Energy price-level/tail term: 96–100 % of the gap, every fossil fuel, both years.**
  The object carries ZERO hours > $100 (max $24.4 / $46.2) while the measured tail
  (h > $100) alone carries **61.9 % of 2024 and 36.9 % of 2025** attainable margin (mc=$30
  basis; 87.6 % in 2023), and the object's mean ($9.5–10.5) sits at ~35 % of the measured
  mean — below coal's own marginal cost. gas_cc gaps: 82.9 (2024), 73.2 (2025); gas_ct 65.2 /
  46.7; coal 75.2 / 97.2; gas_st 64.4 / 46.3.
* **Reserve-product term: ≈ 0 at these screens.** The object's reserve signal is 0.000 —
  and the SOM 2024/2025 stacked figures show a visually negligible AS component for CT/CC
  (2024 AS cost of load $0.98/MWh vs $3.74 in 2023). The FFR-5A "$0.0 reserve leg"
  adjudication, RE-MEASURED at the repaired level as charter question (a) demanded:
  **still $0.0 on every row — but now measured to be consistent with the 2024/2025 market's
  own AS-product share.** The reserve GAP is a 2021/2023 phenomenon, and in 2023 it enters
  through the ENERGY price (ECRS price effects ≈ half of net revenue, monitor's own
  attribution), not the product leg.
* **Bar term: ≤ ~5 %, wrong sign to help.** Coal bar 58.5 vs the SOM-cited EIA existing-coal
  FOM 61.60 (−5 %); nuclear 130 vs NEI opex ≈ $150/kW-yr-equivalent; gas bars are ATB
  new-unit FOMs with no SOM contradiction. The bars are externally consistent.

### 3.3 R4 — the actual exits, decoded against measured margins

The scored 1.534 GW (from `capacity_actuals_ercot.csv`, spanning 2021–2025):

| unit | MW | fuel | actual year | nature of exit |
|---|---:|---|---|---|
| J T Deely 1+2 (plant 6181) | 932 | coal | 2023 (EIA) | **Paper event.** Announced June 2011; physically ceased operation Dec-2018; EIA-860 vintage-2020 status **OS** — and therefore NOT in the model's vintage-2020 CAMPD fleet (the FFR-5A coal cohort lists 9 plants; no p6181). No screen can retire a unit the fleet does not carry; the scorer's own target contains it. |
| Decker Creek 2 (plant 3548) | 405 | gas steam (actuals taxonomy: gas_ct) | 2022 | Austin Energy municipal fleet-plan exit. Replica-at-measured-2022 gas_st margin **129.7 vs bar 35** — margin-POSITIVE 3.7× at exit. Non-economic. |
| small units (52120, 52176, 56864, …) | ~180 | gas_ct/gas_cc/biomass | 2021–2024 | < 100 MW each, below the CAMPD per-plant fleet grain. |
| V H Braunig 1+2 (plant 3612) | 477 | gas_st | 2025-03 (NSO) | The one real >300 MW merchant-adjacent gas_st exit of the window — **ABSENT from the scored actuals** (EIA status OS, not RE, so `build_capacity_actuals` misses it). Carried EIA-860 planned-retirement-year **2024 at vintage 2020** — an announced date `forecast_fossil_retirement_economic=True` deliberately ignores for fossil; the confirmed-registry rows that do capture it carry instrument_date 2024-03, after the vintage-2020 information gate. |

**The bounding finding:** on measured prices every fossil class clears its bar in every
window year (minima: coal 75.4 vs 58.5 in 2024; gas_st 47.0 vs 35 in 2025) — ERCOT's true
margin-driven exit total in 2021–2025 is **≈ 0 GW**. Every real exit was an
instrument/announcement/fleet-plan event. A correct margin screen SHOULD execute
approximately nothing in this window; the 1.534 GW is not a margin-screen target, and no
admissible margin fix can (or should) close it.

## 4. The three answers

**(a) Which revenue legs does SOM count that the repaired object lacks?** Not a missing
PRODUCT leg — a missing PRICE. SOM's stack is Energy + Reserves(+ECRS effects); at the
2024/2025 screens the market's own AS-product share is ≈ 0 and the screen's $0.00 reserve
leg is consistent with it (§3.2). What the repaired object lacks is the **scarcity content
of the energy price itself**: the measured price duration curve puts 37–88 % of attainable
margin in hours > $100 (ORDC adders, RDPA, and in 2023 the ECRS-procurement price effects),
and the repaired stack-reprice generates literally zero such hours plus a mean at ~35 % of
measured (below coal SRMC). One number: gas_cc earns $86.7/kW-yr on measured 2024 prices
(SOM: $89) and $3.79 on the object. The FFR-5A reserve-$0.0 adjudication re-measured at the
repaired level stands — and is exonerated as the gap term for 2024/25; the 2023 reserve gap
is an energy-price phenomenon (ECRS ≈ half of net revenue).

**(b) Is the bar mis-leveled vs SOM's going-forward basis?** **No.** Coal 58.5 vs SOM-cited
EIA 61.60; nuclear 130 vs NEI ≈ 150 equivalent; gas ATB FOMs unchallenged by any SOM
number; CONE (102–140) is an ENTRY benchmark, correctly far above the retention bars. The
bar term is ≤ 5 % of any fuel's gap and its sign (slightly lenient coal bar) cannot produce
the observed fleet-wide failure. Every within-window failure/clearance flip is carried by
the price object.

**(c) Could a correct screen have caught the actual exits?** **No — measured decomposition
§3.3.** Deely is a paper event outside the fleet basis; Decker and Braunig were
margin-positive at exit on measured prices; the truly economic exit total in-window is
≈ 0 GW. This BOUNDS what any margin screen can do: the screen's job in this window is to
retire (essentially) NOTHING while the announced/confirmed channels and the actuals
target carry the instrument-driven exits. Both current failure modes — shipped "fail
everything at raw duals" and repaired "fail everything at the collapsed lookahead" — get
the in-window number right only through the admission cap, which is the D-20(a) sitting's
"the cap does all retention work" defect restated, now with its cause measured: **the
forward price object, not the margin construction (replica matches SOM 0.89–0.97) and not
the bar (§3.2).**

## 5. Admissibility verdict per candidate fix (rules 13/14/23)

| # | candidate fix | gap term | verdict |
|---|---|---|---|
| 1 | **Forward-object scarcity restoration from published market design**: make the unified lookahead's ORDC tail fire the way the real ORDC does — published ORDC parameters (X, μ, σ, VOLL), RDPA, post-RTC AS demand curves, forced-outage/net-load UNCERTAINTY at the hourly stack grain (the repaired tail computes ≈ 0 because a 22–32 % reserve-margin fleet with smooth availability never approaches the knee; the real 2024 market priced 161 h > $100 all the same) | energy tail (dominant, 96–100 %) | **ADMISSIBLE** (rule 13: reproducible market-design/physics inputs, forward analogue, condition-responsive). This is a STRUCTURAL diagnosis charter, not a parameter: why the model's pro-forma LOLP is ≈ 0 where the market's was not. Includes examining the arm's own fleet length (RM 21.9–31.8 %), which the object inherits. |
| 2 | **Measured AS requirement quantities** (ECRS/RRS/Reg/NSRS MW, incl. 2023 ECRS procurement) as reserve-signal inputs | 2023 energy-price ECRS term (~half of 2023 net revenue); 2021 reserves | **ADMISSIBLE** (rule 13 names "a measured ancillary-service power reservation" admissible; quantities regenerate from ERCOT's published AS methodology forward). The QUANTITIES are the input; the price outcome stays the model's. |
| 3 | **Re-level any bar/FOM/multiplier toward the residual** (make fewer units fail by lowering bars, or force exits by raising them) | bar | **INADMISSIBLE — refused by name** (rules 1/14/23: the bars are externally consistent within ~5 %; a bar moved at an entry_capped count is a level knob tuned at a residual). The only bar move with any basis — `fixed_om_coal` 45.0 → 47.4 so that ×1.3 hits EIA's 61.6 — is a rule-23 re-derivation available if its SOURCE data is re-cited, changes the failure pattern nowhere, and must NOT ride this finding. |
| 4 | **Scalar uplift/offset/multiplier on the lookahead signal** (any "add $X", "scale to SOM/actuals") | energy level | **INADMISSIBLE** (rule 13's forbidden branch verbatim: rescaling an input so the output lands on actuals; no forward analogue). |
| 5a | **Vintage fleet status hygiene**: exclude EIA-860 status-OS units (Deely) from the vintage base fleet — or at minimum from the actuals target | scoring target | **ADMISSIBLE** (rule 14: measured status data; regenerates per vintage). |
| 5b | **Actuals-target hygiene**: `build_capacity_actuals` counts EIA "RE" only — misses the real Braunig OS exits and counts Deely's paper date | scoring target | **ADMISSIBLE** data fix to the validation target (registry outcome facts, not model tuning). |
| 5c | **Honor announced fossil planned-retirement dates in hindcast arms** (Braunig's 2024 dates were IN the vintage-2020 sheet; `forecast_fossil_retirement_economic=True` ignores them by design) | channel assignment | **ADMISSIBLE-WITH-OWNER-DECISION**: information-gate compliant (the date is vintage data), but it reverses a documented design choice (fossil exits respond to conditions, not announcements) — a gated structural option for the owner, not a lane-level fix. |

## 6. Governance position

* **Nothing tuned, armed, promoted, or registered.** The re-run is a REPRODUCTION of the
  registered `ercot-2021-2025-t1ff-armr-ffr5d-unified` arm (same invocation, same runtime
  cache key `49eac64f146b3460`, byte-identical `crossover_score.json`) performed solely to
  read the never-committed evolution-ledger fields; the registered bundle's committed files
  are untouched (timestamp-only regen diffs restored to committed bytes). No new
  registration; the dashboard record stays FFR-5D-M's.
* **Rule 22:** solves {2021, 2023, 2024, 2025}, 2022 bridged (never solved); no
  out-of-training year touched; the T1-FF window remains inside the holdout-freeze
  carve-out. SOM intake covers 2023–2025 only (the reports' 2018–2022 history columns and
  any H1-2026 content deliberately NOT transcribed).
* **Rule 13 posture:** SOM rows and the measured-price replica exist as VALIDATION
  benchmarks; neither is wired into any solve path. The replica reproduces the standing
  audit construction (`fom-scarcity-revenue-audit-2026-07-05.json`) exactly on its CT/CC
  rows before extending to coal/gas_st/nuclear.
* **Rule 28(b):** the ERCOT `capacity_screen_unified_lookahead` cell keeps verdict **O**
  with this decomposition appended to its evidence (the cell's open question — arm or not —
  is the manager's U.2 determination; this lane supplies the candidate evidence for lift
  condition (i) and recommends nothing about the lift).
* **No lift recommendation.** FH-4/FH-5 remain BLOCKED by manager determination U.2.

### Recommendation card for the owner (fix charters, not fixes — none performed here)

1. **THE gap is the forward price object's missing scarcity content** (verdict row 1):
   charter a structural diagnosis of why the unified lookahead's ORDC tail is inert
   (pro-forma LOLP ≈ 0 on a 22–32 % RM fleet with smooth hourly availability) when the real
   2024/2025 market priced 161/217 h > $100 — published ORDC/AS-design inputs only; the
   fleet-length inheritance (additions 17 GW vs 55.4 actual) is part of the same knot.
2. **Retirement scoring should stop chasing 1.534 GW as a margin target** (verdict rows
   5a/5b): the window's true economic-exit total is ≈ 0; fix the actuals target (Deely
   paper date, Braunig omission, OS-status vintage handling) so the scorecard measures the
   screen against what a margin screen can legitimately see.
3. **The 2023 ECRS term has a clean admissible input** (verdict row 2) if/when the
   hindcast screens are asked to reproduce 2023-level revenues.
4. **Do not touch the bars** (verdict row 3) and **refuse any signal-scaling knob**
   (verdict row 4) — both are named residual-tuning channels.

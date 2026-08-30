# FINDING — capx-NEISO-RC Phase 0: attribution of the D14 retirement-composition miss

**Session:** NEISO-RC PHASE-0 (capacity-expansion / Forecast Finalization track, director
refresh #19 lane NEISO-RC). Branch `claude/capx-neiso-rc-phase0-c0q8qs`, off `3960244`.
**Charter:** ZERO SOLVES. Attribution of the capx-D14 retirement COMPOSITION miss
(`FINDING-capx-d14-neiso-t1x-2026-08-30.md` §0.2/§5: run
`neiso-2023-2027-crossover-capxd14` — gas_cc over-retired 3.128 vs 1.884 GW actual;
biomass / coal / gas_ct / oil exits missed entirely; recall 2/6) from COMMITTED artifacts
only. No mechanism change, no `ScenarioConfig` field, no matrix cell, no board edit, no
verdict touch. Repair chartering is the director's next-batch decision on this finding.

## 0. Headline

**The composition miss is not a margin-calibration error. It is the deterministic output of
three structural facts, each measured from committed artifacts:**

1. **The screen's bar is degenerate at a long reserve position — 93 % of the screened NEISO
   fossil fleet fails it together** (the whole oil and coal fleets and most of the gas fleet;
   nuclear and ~1.4 GW of the best gas clear it). With the model long on the FCA requirement, the CR-1
   sloped-curve capacity payment is $0 (the linear FCA curve zero-crosses at reserve position
   1.083), reserve uplift is 0.00 and attributes are 0, so screen net revenue is the bare
   energy pro-forma: 0.01–20 $/kW-yr against bars of 21–58.5 (committed S-4b ledger, §3.1).
   A bar everyone fails cannot allocate exits — it hands allocation entirely to the floor.
   Real recent FCAs cleared well above zero at comparable surplus (external context, to be
   sha-pinned by the R2 intake), so the $0 is a curve-shape artifact, not market fidelity.
2. **The reliability floor then sizes AND composes the exit wave.** Admitted exit MW ≈ the
   accredited surplus above the shared adequacy requirement (the level lands within +14 % of
   the in-window actual); the floor retains cheapest-$/firm-MW-yr first, and NEISO's
   `claimed_capability` basis makes firm = nameplate, so the cross-fuel retention order is
   EXACTLY the FOM constant ladder: gas_ct $21 < oil $25 < gas_cc $30 < gas_st $35 < coal
   $58.50. Oil and gas_ct are therefore retained wholesale — structurally, whatever their
   distress — and the released wave is drawn from the expensive end: coal, gas_st, gas_cc.
3. **Per-fuel execution lags then window the composition.** gas_cc/gas_st (lag 1) execute the
   next year — the 2024 wave; coal (lag 3) can never execute inside a 2023-start scored
   window (earliest decision = loss-year 2023 → execution 2026); gas_ct (lag 2) is moot
   (never admitted). What remains in-window is gas_cc + gas_st only, all 2024 — exactly what
   D14 measured.

On top of the mechanism, **the score's target is basis-misaligned to the run**: the
retirement bands grade the 2023-vintage crossover against the FULL 2021–2025 actuals registry
(measured §2.1 — the per-fuel actuals reproduce exactly as the 2021–2025 sum), so 1,866 MW
(37 %) of the 4,997 MW target physically ceased before the run's first fleet snapshot — two
of the six ≥300 MW recall members among them — plus 163.5 MW more that the vintage lists OS
(never loaded). ~41 % of the target is unreachable by construction, and the D-24 reachable-set
rule could exclude none of it because NEISO has no committed exit decode (fail-closed keeps
every row in). Measured against its reachable in-window target the model's exit LEVEL is
+20 % (3,563 vs 2,968 MW), not −29 %.

Biomass is the one fuel the screen structurally cannot see (`_THERMAL_FOM` has no biomass
entry — 1,047 MW in the fleet, zero pipeline events across every committed ledger), but its
in-window actual exits are 26 MW — immaterial.

## 1. PRE-DECLARATION (the charter's candidate drivers, and what distinguishes them)

The four candidate drivers stand PRE-DECLARED IN THE DISPATCH CHARTER itself (director
refresh #19, this lane's prompt) — that charter text, committed in the director ledger
before this session existed, is the ex-ante record:

- **(a) Screen materiality path** — the screen prices only classes with meaningful energy
  margins; small biomass/oil/ct classes never clear the screen's materiality path.
  *Distinguishing evidence:* the screened-unit set per fuel. If oil/gas_ct units are absent
  from the screen's margin evaluation (no margin rows at all), (a) holds; if they ARE
  priced and adjudicated, (a) is refuted in its stated form and the protection lies
  elsewhere.
- **(b) Per-fuel FOM/threshold inputs vs NEISO's actual exit economics.**
  *Distinguishing evidence:* the per-fuel bar sides (net revenue vs going-forward cost)
  and whether the per-fuel constants (FOM levels, execution lags), rather than the margin
  ordering, determine which fuels' failures become in-window exits.
- **(c) Non-economic instruments the forecast has no channel for** (age/permit/RMR/consent
  decree) — a REPRESENTATION gap, not a tuning gap. *Distinguishing evidence:* per
  actual-exit unit, the real-world exit instrument vs the run's admissible channels
  (confirmed registry rows + instrument dates vs the vintage cutoff 2023-12-31; the
  announced channel's fossil no-op).
- **(d) The gas_cc over-retirement as the mirror of (a)–(c)** — the screen concentrating
  ALL exit pressure on the one fuel it prices richly. *Distinguishing evidence:* whether
  the modeled gas_cc exit MW is sized/allocated by gas_cc's own margins or by a shared
  budget (e.g. the adequacy floor) that other fuels escape.

**Sequencing disclosure (recorded against interest).** This session's measurement did not
strictly follow "commit the skeleton, then measure": the READ-FIRST pass (D14/S-4b
findings, `crossover_score.json`, spec §5.2, screen code, the confirmed registry and the
actuals CSV) flowed directly into extracting the committed S-4b evolution-ledger margin
rows BEFORE this file was committed. The charter's (a)–(d) were fixed ex ante by the
dispatch prompt and are tested as chartered; nothing here was re-declared after the fact,
and the s4b-ledger extraction is reported at full magnitude in §3 whatever it says about
the candidates. The measurement sections (§0 headline and §2 onward) were completed and
inserted after this section's standalone commit (`2704312`).

## 2. The measured decomposition

### 2.1 The scoring basis: a 2021–2025 target against a 2023-vintage fleet

The crossover score's per-fuel "actual" reproduces EXACTLY as the full-window sum of
`data/raw/_validation-source/capacity_actuals_neiso.csv` (window 2021–2025 by construction,
per its own header): biomass 261.5 / coal 845.6 / gas_cc 1,883.7 / gas_ct 319.3 / gas_st
479.6 / oil 1,207.7 MW — matching the score's 262/846/1,884/319/480/1,208 to rounding.
`score_crossover.crossover_capacity_events` restricts MODEL events to ≤2025 but passes the
full actuals frame through (`scripts/score_crossover.py:822-842`), and
`score_capacity_hindcast.score_retirements` applies no year filter
(`scripts/score_capacity_hindcast.py:929`). This is coherent for the plain hindcast the
scorer was built for (vintage 2020 ⇒ 2021/2022 exits are in the fleet basis); reused verbatim
on a vintage-2023 crossover it is a basis misalignment: `load_retired_within_window` is
backcast-only (`src/market_sim/runner.py:1371-1389`), so the crossover's fleet is the bare
EIA-860 2023-vintage operable sheet — a unit that ceased in 2021/2022 does not exist in the
run and no channel can exit it.

Per-fuel split of the 4,997 MW target (from the actuals CSV, physical-cessation dating):

| fuel | 2021–22 (pre-vintage, NOT in fleet basis) | 2023–25 (in-window) | in-window detail |
|---|---:|---:|---|
| gas_cc | 139.3 | 1,744.4 | Mystic 8/9 (p1588: 4 GT + 2 ST), 2024 |
| gas_st | 126.6 | 353.0 | Middletown 2 + 3 (p562), 2025 |
| coal | 500.0 | 345.6 | Merrimack 2 (p2364), 2025 |
| oil | 720.0 | 487.7 | Middletown 4 (414.9), 2025 + 72.8 small |
| gas_ct | 144.9 | 174.4 | Androscoggin CT01–03 (163.5, **OS in the 2023 vintage**), 2023 + 10.9 small |
| biomass | 235.4 | 26.1 | small units only |
| **total** | **1,866.2 (37.3 %)** | **3,131.2** | |

The pre-vintage block includes Mystic 7 (oil 617, ret. 2021) and Bridgeport Harbor 3 (coal
400, ret. 2021) — recall members 1588_7 and 568_3. Additionally Androscoggin (55031, 163.5 MW
of the in-window gas_ct actual) is status OS in the vintage-2023 operable sheet, and the
fleet loader keeps only `status == "OP"` (`src/market_sim/data/fleet/eia860.py:929-931`) — it
was never in the fleet either. Total unreachable-by-construction ≈ 2,030 MW (40.6 % of the
target).

**Re-based level**: model 3,563 MW vs in-window actual 3,131 MW = **+13.8 %**; vs the
reachable in-window target (excluding Androscoggin) 2,968 MW = **+20.1 %** — an
over-retirement, the opposite sign of the scored −28.7 %. Per-fuel in-window: gas_cc 3,128 vs
1,744.4 (+79 %), gas_st 435 vs 353 (+23 %), everything else 0.

**Why D-24 didn't catch it**: the reachable-set rule excludes only on positive committed
evidence, and the per-unit exit-decode artifact it keys on exists for ERCOT alone
(`EXIT_DECODE_EVIDENCE`, `scripts/score_capacity_hindcast.py:530-538`; `load_exit_decode`
returns `{}` for every other ISO). Fail-closed then correctly keeps all six members in — the
rule is working as signed; it is evidence-starved for NEISO.

### 2.2 The channels available to this run

- **Confirmed (step 0)**: the NEISO registry (`data/raw/confirmed-retirements/neiso.csv`)
  holds exactly two rows — Merrimack 1/2, instrument the 2024-03-29 CWA consent decree,
  decree deadline 2028-06. The instrument POST-DATES the vintage cutoff 2023-12-31, so the
  hindcast information gate correctly withholds both rows; even if admitted, the decree year
  is outside the window. Mystic 8/9 are deliberately absent ("de-list bids REJECTED …
  retained via a separate FERC cost-of-service agreement, then retired in 2024 outside a
  cleared de-list bid — already historical/out of the forward window" — the registry's own
  curation note), and several de-list-bid tracker exits are held out on failed EIA-860
  identity matches. **The confirmed channel had nothing it could fire.**
- **Announced (step 1)**: the 2023 vintage DID carry Mystic 8/9's planned retirement 2024-06
  (all six units) — but fossil announced dates are a deliberate no-op
  (`forecast_fossil_retirement_economic=True`); Middletown and Merrimack carry NO planned
  date in the 2023 vintage. `hindcast_verified_announced_exits` is verification-only
  (suppresses cancelled exits, never injects one).
- **Economic (step 3)**: therefore the ONLY live exit channel — and every model exit is
  reason `economic` (D14 §5, the ledger read).

## 3. The mechanism, measured

The crossover's own evolution ledgers are not tracked (its bundle commits
`meta.json`/`run_config.json`/`crossover_score.json` only, like the NYISO capxd10 sibling).
The measured evidence below is the committed **S-4b T1-F NEISO pair**
(`results/ff-t1f-s4b-ara/neiso/NEISO/9a7f68fc7dcac931/evolution_2026..2030.json` — the same
screen, same fleet representation, same ISO, 2026 base), whose `pipeline_events` carry the
FFR-5A bar decomposition per unit. Crossover-specific numbers derived from it are labeled
inferred-with-mechanism, not measured.

### 3.1 The degenerate bar (S-4b treatment, 2027 screen — loss-year 2026)

Per-fuel capacity-weighted screen revenue vs bar, $/kW-yr, over ALL decided + entry_capped
rows:

| fuel | units | MW | net revenue | bar (GFC) | energy leg | reserve leg | capacity leg |
|---|---:|---:|---:|---:|---:|---:|---:|
| oil — capped (= the WHOLE 5,181.5 MW oil fleet) | 135 | 5,181.5 | 0.01 | 25.00 | 0.01 | 0.00 | **0.00** |
| gas_ct — capped | 88 | 1,279.8 | 1.51 | 21.00 | 1.51 | 0.00 | **0.00** |
| gas_cc — capped | 77 | 9,625.3 | 10.51 | 30.00 | 10.51 | 0.00 | **0.00** |
| gas_cc — decided | 18 | 2,136.0 | 7.84 | 30.00 | 7.84 | 0.00 | **0.00** |
| gas_st — decided | 11 | 95.8 | 2.24 | 35.00 | 2.24 | 0.00 | **0.00** |
| coal — decided (= the whole 108 MW coal fleet) | 3 | 108.0 | 0.77 | 58.50 | 0.77 | 0.00 | **0.00** |

332 tranches / 18,426 MW fail the uniform bar — **93.1 %** of the 19,794 MW screened
non-nuclear thermal fleet (`fleet_by_fuel_before`: gas_cc 12,886.0, gas_ct 1,460.6, gas_st
158.3, oil 5,181.5, coal 108.0). The 1,368 MW that clears it is the best of the gas fleet
(gas_cc 1,125 + gas_ct 181 + gas_st 62 MW, no events); nuclear (3,355.4 MW) also clears on
energy margins. The capacity
leg is $0 because the 2026 fleet is +3.4 GW long (S-4b §5.1), reserve position past the
NEISO FCA curve's zero-cross at **1.083** (`_NEISO_FCA_CURVE`,
`src/market_sim/config/capacity_market.py:957-961` — the FCA-11 geometry, linear to zero;
its own comment marks it "refined in CR-3"). Real FCAs at comparable surplus cleared in the
$2.00–3.58/kW-month range (~$24–43/kW-yr; FCA 15–18 — external context from public auction
results, NOT read from a committed artifact; the R2 intake pins the citations) — revenue the
screen credits as zero. With $24+/kW-yr credited, gas_ct (bar 21) passes outright and the
bar starts discriminating; at $0 nobody passes and the floor allocates everything.

Biomass: 1,047.2 MW in `fleet_by_fuel_before`, zero pipeline events in every committed
ledger — never screened (`_THERMAL_FOM`,
`src/market_sim/model/capacity_evolution/retirements.py:84-92`, has no biomass entry).

### 3.2 The floor as allocator

`_apply_pipeline_retirements` admits the year's failing candidates only up to the scheduled
adequacy requirement: `_apply_reliability_floor` un-admits candidates **cheapest
$/firm-MW-yr first** (`_floor_retention_merit` — GFC per firm MW, CO2 ascending, heat-rate
ascending tie-breaks; `retirements.py:1263-1283, 1361`). NEISO's accreditation basis is
`claimed_capability` ⇒ thermal firm fraction = 1.0 (`capacity_market.py:2443`,
`retirements.py:1162-1167`), so the cross-fuel order is exactly the FOM ladder:

    retained first ← gas_ct $21 · oil $25 · gas_cc $30 · gas_st $35 · coal $58.50 → released first

The S-4b 2027 events realize this exactly: oil 135/135 and gas_ct 88/88 entry_capped;
coal 3/3 and gas_st 11/11 admitted; gas_cc split (18 admitted / 77 capped — the marginal
fuel). Within a fuel, the CO2/heat-rate tie-breaks (not margin depth) pick which tranches
go — the admitted CC set spans depths 14.2–29.4 $/kW-yr while deeper-failing CC tranches
stay capped. **Total admitted MW ≈ the surplus above the requirement** — which is why the
crossover's LEVEL (3,563 MW) lands near the in-window actual (+14 %) while the composition
is entirely floor-shaped, and why the 2024 wave admitted ≈ the 2023 fleet's long position on
the FCA-17-vintage requirement (inferred-with-mechanism; the capxd14 ledgers are not
committed).

### 3.3 Lags window the composition; the bar oscillates

Committed lifecycle of the coal tranches (S-4b treatment — Merrimack-1 `COAL_North_p2364_*`):

| year | event | margin $/kW-yr | capacity leg $/kW-yr | note |
|---|---|---:|---:|---|
| 2027 | decided (×3, 108 MW) | 0.74–0.84 vs 58.50 | 0.00 | decided_year 2026, execute_year **2029** (lag 3) |
| 2028 | **reversed** (×3) | 118.5–119.4 vs 58.50 | **85.31** | the 2027 wave (−2.2 GW) pulled the position back inside the curve — the capacity payment flips $0 → $85/kW-yr and the whole fleet re-clears |
| 2029 | retired, reason **`confirmed`** | — | — | the consent decree executes (instrument 2024-03-29 IS admissible at a 2026 vintage) |

Three consequences carried back to the crossover:

- **Coal in-window exits are impossible by construction** in a 2023-start window: earliest
  decision is loss-year 2023 → execution 2026 (`retirement_execution_lag_coal=3`). Whether
  Merrimack was decided in the 2024 screen is unverifiable from committed crossover artifacts
  — and immaterial to the scored window either way.
- **The bar is a fleet-level relaxation oscillator**: one wave, then the capacity price
  switches on and everything reverses/re-clears — matching the crossover's "all exits 2024,
  none 2025" signature.
- **The T1-F contrast proves the confirmed channel works when the information gate admits
  the instrument** — the crossover's Merrimack miss is the vintage gate operating correctly
  on an instrument the world had not yet produced (2024-03-29 > 2023-12-31), i.e. a genuine
  information-set limit, not a bug.

## 4. Per-unit attribution (the ≥300 MW recall set, and each per-fuel miss)

| target | fuel, MW, actual year | in 2023-vintage fleet? | real-world exit driver | model outcome | attributed driver |
|---|---|---|---|---|---|
| 1588_ST85 / 1588_ST96 (Mystic 8/9 STs) | gas_cc, 2×315, 2024 | yes (planned ret. 2024-06 in vintage; announced channel no-ops fossil) | RMR/cost-of-service end 2024-06 (agreement public years pre-vintage; absent from registry as "historical") | **MATCHED** — economic exit 2024, plant-grain match | The floor released gas_cc at lag 1; the right units exited through a channel-substitution (economics standing in for the missing RMR instrument) |
| 1588_7 (Mystic 7) | oil, 617, **2021** | **no** (retired pre-vintage) | pre-window exit | unreachable | **Scoring-basis**: 2021–2025 target vs 2023-vintage fleet; D-24 evidence-starved (no NEISO exit decode) |
| 568_3 (Bridgeport Harbor 3) | coal, 400, **2021** | **no** | pre-window exit | unreachable | same |
| 2364_2 (Merrimack 2) | coal, 345.6, 2025 | yes (no announced date in vintage) | CWA consent decree (2024-03-29) + cleared no capacity Jun 2026+ | kept in-window | **(c) information gate** (instrument post-dates vintage — correctly withheld) + **(b) lag-3 censoring** (an economic decision cannot execute ≤2025); NOT a margin miss — coal fails the bar hardest of all (0.77 vs 58.50 in the twin) |
| 562_4 (Middletown 4) | oil, 414.9, 2025 | yes (no announced date in vintage) | owner deactivation 2025 (no planned date in the 2023 vintage — a post-vintage announcement on the EIA-860 record) | kept | **(d/b) floor allocation**: oil is 2nd-cheapest $/firm-MW — retained wholesale despite being the screen's most-distressed fuel (nr ≈ 0.01) |
| — Middletown 2/3 | gas_st, 353, 2025 | yes | same deactivation | covered in fuel-MW: model exits 435 gas_st in 2024 (−9 % per-fuel, timing −1 yr) | gas_st sits on the released side of the ladder at lag 1 — right side of the ladder, unit identity unverifiable from committed artifacts |
| — Androscoggin CT01–03 | gas_ct, 163.5, 2023 | **no (OS in vintage; `status=="OP"` filter)** | already ceased at vintage | unreachable | fleet-basis (same class as 1588_7/568_3, below the 300 MW recall bar — hits the per-fuel band only) |
| — biomass small | biomass, 26.1 in-window | in fleet, unscreened | various | kept | **(a, narrow form)**: biomass absent from `_THERMAL_FOM` — the one truly unpriced fuel |
| — model gas_cc excess | +1,384 vs in-window actual | — | — | 36-tranche wave over many plants | **(d)**: the surplus-sized wave lands almost entirely on gas_cc (the marginal released fuel at lag 1); the specific tranche set is CO2/heat-rate-ordered, unverifiable per-plant from committed crossover artifacts |

## 5. Driver adjudication against the pre-declaration

- **(a) Screen materiality path — REFUTED as stated.** Oil and gas_ct ARE priced, per-unit,
  every year (135 + 88 margin rows in the committed twin) and fail the bar HARDEST relative
  to revenue (oil nr 0.01 $/kW-yr). Nothing about small-class materiality protects them; the
  floor does. The narrow surviving form of (a) is biomass only — unpriced by construction,
  26 MW in-window.
- **(b) Per-fuel inputs — CONFIRMED, in a sharpened form.** Not "thresholds vs NEISO's exit
  economics" (under the pipeline rule the decision bar is uniform), but: (i) the per-fuel
  FOM constants ARE the floor's allocation ladder (claimed_capability makes firm=nameplate,
  so no unit attribute modulates them); (ii) the per-fuel execution lags decide what can
  land in-window (coal never, in a 2023-start window); (iii) the FCA curve's linear
  zero-cross at 1.083 is the switch that makes the whole fleet fail together and hands the
  floor the allocation. The composition is a deterministic function of these registry
  constants once the bar degenerates.
- **(c) Non-economic instruments — CONFIRMED for the named units, with a measured
  contrast.** Merrimack: consent decree post-dates the vintage (gate correct); the S-4b twin
  executes the same plant `reason: confirmed` at a 2026 vintage — the channel works when the
  information set contains the instrument. Mystic 8/9: the RMR/cost-of-service-end
  instrument (public years before the 2023 vintage) is absent from the registry by a
  curation-scope choice ("historical"), so the model reached the right exit through the
  economic channel instead. Middletown: deactivation announced post-vintage — genuinely
  unknowable, only economics could have reached it (and the floor retained it).
- **(d) gas_cc over-retirement as the mirror — CONFIRMED with the precise mechanism.** The
  exits are a BUDGET (the adequacy surplus), not per-fuel verdicts; the budget is allocated
  from the expensive end of the FOM ladder at lag 1 ⇒ gas_cc (+gas_st) absorb everything the
  other fuels are protected from. The +1,384 MW in-window gas_cc excess ≈ the exit pressure
  that belonged (in reality) to oil/coal/ct units the ladder retained or the lags censored.
- **(e) NOT pre-declared, reported at full magnitude: the scoring-basis misalignment** —
  37 % of the retirement target (and 2 of 6 recall members) pre-dates the run's fleet basis;
  +163.5 MW more is OS-filtered; D-24 is evidence-starved for NEISO; and the level verdict
  flips sign (−29 % → +14/+20 %) on the reachable basis.

## 6. Routed repair candidates (admissibility under rules 13/21/23 stated per item)

Repair chartering is the director's decision; nothing below was implemented, armed, or
tuned in this session.

- **R1 — NEISO confirmed-registry intake completion.** *Route: rule 23 publication-driven
  data intake; rule 13 admissible (enforceable public instruments, forward-reproducible;
  they regenerate for forward years from the same registry discipline).* Items the registry's
  own curation notes already name: (i) **Mystic 8/9's FERC cost-of-service/RMR end**
  (the agreement was public years before the 2023 vintage — exact instrument date for the
  intake pass to pin against the FERC docket; effective 2024-06) — this converts the
  program's largest NEISO exit from a floor-allocation coincidence into an
  instrument-driven exit; (ii) re-attempt the EIA-860 identity matches
  for the held-out de-list-bid tracker rows; (iii) the standing structural watch — restate
  the instrument bar in terms of ISO-NE's one-year deactivation-notification process (which
  is also the natural instrument class for Middletown/Montville-type exits). NO tunables.
- **R2 — FCA sloped-curve re-derivation (the CR-3 refinement the curve's comment already
  promises).** *Route: rule 23 (re-derive when source data updates — published MRI curve
  parameters / dynamic de-list threshold) + rule 14 (prefer measured data).* The linear
  FCA-11-geometry curve pays $0 past 8.3 % surplus where real FCAs 15–18 cleared $24–43/kW-yr.
  This is the input that degenerates the bar; with it repaired the screen discriminates and
  the floor returns to backstop duty. **Refused on its face** if done by fitting the curve to
  the retirement residual (rules 21/24) — the derivation must come from ISO-NE's published
  curve/auction parameters only.
- **R3 — NEISO exit-decode evidence + crossover target-window basis (scorer-side).** *Route:
  measurement-basis repair, zero solve; changes scoring semantics ⇒ owner/director sign-off
  per the D-24 / D-9(ii) precedent of signed scorer decisions.* (i) Build the FFR-7C-style
  per-unit exit decode for NEISO so D-24 operates on positive evidence (1588_7, 568_3,
  Androscoggin leave the denominator; Merrimack/Middletown get adjudicated margin notes).
  (ii) Give `score_crossover` a vintage-consistent retirement target (filter the actuals to
  years ≥ vintage+1, or report both bases side by side, the additions D-9(ii) pattern).
  (iii) **Close the `confirmed_derates` scorer blind spot**: `model_retirements` reads only
  the `retirements` ledger key (`scripts/score_capacity_hindcast.py:167-187`), and exits on
  plant-binned fleets can land in `confirmed_derates` (the established two-key fact —
  `evolve.py:403-417`); neither scorer reads that key today. Harmless in capxd14 (all exits
  economic `retirements` rows) but it will silently swallow exactly the exits R1 creates on
  binned NEISO plants — R1 and R3(iii) must land together.
- **R4 — decision-basis retirement diagnostic (report-only).** *Route: scorer-side reporting
  addition (the retirement mirror of the signed D-9(ii) additions decision-basis), zero
  solve.* Lag-censored decisions (coal decided → executes past the window) are invisible in
  the executed-MW score; reporting decided-in-window alongside executed would have shown
  whether Merrimack was decided. Requires the crossover bundle to commit its evolution
  ledgers (a tracked-set/gitignore policy change — the S-4b bundles already commit theirs).
- **R5 — biomass screen coverage.** *Route: mechanism change (new `fixed_om_biomass`
  ScenarioConfig field ⇒ rule 5 citation + rule 28(c) matrix row duty) — explicitly NOT this
  phase.* Materiality is low (26 MW in-window; 1,047 MW fleet) — recorded for completeness,
  not urgency.
- **R6 — REFUSED on its face:** tuning per-fuel FOM constants, execution lags, thresholds,
  or the demand curve against the retirement composition residual (rules 21/24; the charter's
  own refusal). Every repair above is publication-driven or measurement-side.

## 7. Honest notes

- **The floor retaining oil/CT mirrors a real NEISO behavior** (rule 1 caution for the
  repair lane): ISO-NE really does retain uneconomic oil steam for winter fuel security —
  Mystic's own RMR is the type case. The defect is not the floor's existence but the
  degenerate bar that hands it ALL allocation power; R2 restores the screen's
  discrimination, R1 gives the real retention/exit instruments their own channel.
- **2025 price sign-flip coupling (D14 §0.3, noted-not-chased per charter):** the 2024 exit
  wave removes 3.56 GW from the 2024/2025 fleets, which is directionally price-RAISING — it
  cannot produce the −21.8 % 2025 under-pricing and, if anything, damps it. The wave and the
  flip are adjacent but the sign rules out the wave as the flip's cause.
- **The n_gen 663→413 seam (2023→2024) is NOT the exit wave**: the NYISO capxd10 sibling
  drops 630→466 at the same seam with ZERO exits. It is the crossover-generic base-year
  representation seam — `evolve_fleet` re-collapses the raw non-binned units into
  efficiency-bin representatives after the first evolution (`evolve.py:907-910`),
  MW-conserving per fuel. No bearing on the composition; recorded so nobody chases it.
- **Sequencing (per §1's disclosure):** the S-4b ledger extraction preceded the §1 commit;
  drivers (a)–(d) stood pre-declared in the dispatch charter. Adjudications are reported at
  full magnitude including the refutation of (a).

## 8. Governance attestation

- **ZERO SOLVES.** Every number here is read from committed artifacts (the capxd14 bundle's
  three tracked files, the S-4b evolution ledgers, `capacity_actuals_neiso.csv`, the
  confirmed registry, the vintage-2023 EIA-860 parquet) or from code at HEAD, cited by path.
  No bench, no actual beyond the committed registry files, no out-of-training year touched;
  the holdout freeze is not implicated (nothing was solved or scored).
- **No mechanism change, no `ScenarioConfig` field, no matrix cell, no board edit, no
  verdict touch** — finding-only, per charter. The T3 NEISO golden lane's surfaces (BOARD
  block, t3 verdict key) were not read for editing and not written.
- **No re-derivation** of the two-key exits fact (taken as established per charter); the
  scorer's single-key read is reported as a measured code fact, not re-adjudicated.
- Rule 15 does not fire: no run was produced or registered. The deliverable is this finding.

## 9. For the successor / director

1. The repair batch order that follows from the attribution: **R2 (curve) + R1 (registry) +
   R3 (scorer trio) are the load-bearing three**; R1 without R3(iii) will under-count its own
   effect. R4 is cheap and makes every future crossover's lag censoring visible. R5 is
   optional completeness.
2. Do not grade a NEISO crossover retirement band against the raw −28.7 % headline until R3
   lands — the reachable-basis level is +14/+20 % over, and the sign matters for what R2
   would be expected to do (R2 should REDUCE exits by restoring capacity revenue, moving the
   level from +20 % toward 0, while un-concentrating the composition).
3. The S-4b bundles' committed ledgers are the measurement instrument of record for this
   screen on NEISO; a capxd14 ledger regeneration (a solve) is NOT needed for any claim made
   here — every crossover-specific statement that would need one is labeled
   inferred-with-mechanism.

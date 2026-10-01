# FINDING — capx D43: the dispersion-carrying entry expectation closes D39's one-signed under-expectation at the screen grain — and is DECISION-INERT on the CAISO T1-H, because the dispersion the screen discards is dispersion the hindcast's OWN LP never priced

**Lane:** capx D43 — the first repair measurement on D39's object
(`FINDING-capx-d39-entry-underbuild-2026-09-02.md` §0/§3.1/§7.2). Branch
`claude/capx-d43-caiso-dispersion`. **Date:** 2026-09-02. **HEAD at launch:** `dfc44d95`;
rebased onto `5f1e47a6` before the first push. **Pre-declaration:**
`PREDECL-capx-d43-caiso-dispersion-2026-09-02.md` — stage 1 (`cbdff559`) pushed before the
screen-grain probe ran, stage 2 (`c4ee7dd2`) pushed before the arm solve started; graded in
§5 at full magnitude. **Solves:** two CAISO T1-H legs (control + arm), in-session, ~10 min each.
**Mechanism:** `entry_dispersion_expectation_signal` (commit `9b0174b3`; gated, default-off,
zero DOF). **Nothing armed by default; the recommendation is §9's, the decision is the owner's.**

## 0. Verdict (one paragraph, then the table)

**The construction does what D39 asked of it, and it does not move a megawatt.** At the
screen grain, on the committed CAISO basis dumps and the keeper's realized surface (D39 §2's
instrument), each zone's realized price-duration curve indexed by the entering year's headroom
rank turns the shipped screen's one-signed under-expectation — peaker 0.06 / 0.00, CC 0.85 /
0.06 of the realized energy leg at entering-2024 / 2025 — into 7.6 / 6.3 and 3.2 / 0.83, flips
gas_cc, gas_ct and solar positive at entering-2024, and lifts li-ion 4 h arbitrage from $2.9k to
$55.8k against a realized $22.4k (§2). Scored EXACTLY in-run — the control's dumps now carry
the run's own duals, so its expectation is graded against the surface the hindcast itself
paid, no keeper stand-in (§3) — the same construction reads 1.41 (CC) / 2.03 (CT) at
entering-2024 against the shipped 0.92 / 0.57, and the arm solve reproduces the control's
every decision, addition, retirement and CO2 tonne (§4, PC1–PC2 as pre-declared). The reason
is the object, not the instrument: **the hindcast's own 2023 surface carries a $8.63/MWh
daily spread, 0 hours ≥ $100 and 0 negative hours where the keeper's carries $35, 699 and
4 %** — the realized dispersion D39 measured on the six keepers is the calibrated backcast's
(measured overlays, the CAISO scarcity overlay, must-run floors), and the forecast machinery's
LP prices a fraction of it. A dispersion-carrying expectation can only transplant the
dispersion the prior solve produced, and at the CAISO T1-H that is not enough to move gas_ct
(−$41k short at its best), storage (li-ion 4 h −$46k at the keeper's surface, −$105k at the
run's own), or any cap-set VRE volume (the $50 ACP credits $124–131k/MW-yr and every VRE
volume is the ladder's). The residual D39's instrument could not separate is now measured
with its own sign: at entering-2025 every construction, the dispersion arm included, sits at
0.21–0.36 of the run's own realized CC leg because 2025's level is 21 % above 2024's (gas $3.39
→ $4.73) and the seam prices S_entering on THIS year's `mc_cost` — a fuel-level lag the stack
and the constructions all share, named as the successor zero-DOF repair (§8), not run.
**CAISO cell: `I` (inert) for the T1-H lane at the D39 basis, construction VALIDATED** at both
grains; the under-build object moves one step upstream to the forecast lane's own price
formation (D36's "1/10–1/20 of the market's spread", here hindcast-vs-keeper), which no
entry-signal construction can manufacture (D39 §3.2's stated ceiling, now binding).

| grain | shipped → arm (expected ÷ realized, energy leg) | gas_cc / gas_ct / solar sign at entering-2024 | decisions moved | realized surface |
|---|---|---|---|---|
| screen grain, keeper realized (D39's instrument) | CC 0.85 → 3.21, CT 0.06 → 7.58 (2024); CC 0.06 → 0.83, CT 0.00 → 6.33 (2025) | − − − → + + + | n/a | `caiso231_b1_ungrounded`: spread 29, 85 h ≥ $100 (2024) |
| in-run, the hindcast's OWN duals (exact) | CC 0.92 → 1.41, CT 0.57 → 2.03 (2024); CC 0.03 → 0.21, CT 0.00 → 0.00 (2025) | − − − → − − − (RA anchor + ACP decide the volumes) | **0 MW** (every ledger row identical) | the run's own: spread 9.8, 4 h ≥ $100 (2024); 8.7, 0 h (2025) |

## 1. The mechanism — `entry_dispersion_expectation_signal` (gated, default-off, zero DOF)

**What the stack discards, in one line.** `_lookahead_reprice_signal` maps each entering
hour's net load to a merit-order time-mean marginal cost: a deterministic step function of
net-load position, tiled zone-flat, floored at the cheapest unit, with no tail where the
screens are tail-free. The model's own realized surface at the same net-load position is
a DISTRIBUTION — congestion, the CAISO overlay's scarcity, commitment and storage
inter-temporal duals, the negative trough — and D39 §3.1 measured that its LEVEL is close
to the stack's while its dispersion is what a CT's and a battery's entire margin is made
of.

**The construction.** The screens' price object becomes each zone's OWN realized
price-duration curve, indexed by the entering year's stack-headroom rank on the current
year's headroom distribution:

```
u[t]         = mid-rank empirical CDF of headroom_next[t] on {headroom_curr[·]}
signal[z, t] = quantile_(1 − u[t]) ( econ_prices[z, ·] )          (runner._dispersion_expectation_signal)
```

`headroom = top_of_stack − net_load`, both terms the lookahead instrument's own
`installed_headroom_mw` diagnostic: `headroom_next` from the S_entering evaluation the
seam already makes (entering-year demand, committed pipeline / unified repairs / storage
shave exactly as armed) and `headroom_curr` from the S_current evaluation at THIS year's
own dispatched demand with no pipeline terms — the pair `entry_forward_expectation_signal`
already shares (`_fwd_curr_state`). `econ_prices` is the prior solve's own zonal dual
surface with the run's scarcity overlay, the object the disarm fallback reads. An hour
whose forward headroom sits at the p-th percentile of this year's headroom earns this
zone's p-th-percentile realized price. That is the merit stack's own structural
assumption — price is a monotone function of net-load position — applied to the REALIZED
dual distribution instead of the time-mean MC step; and it is the developer pro-forma
object: the node's observed price-duration curve, re-indexed by the forward net-load
duration.

**Properties (unit-tested, `tests/unit/model/test_entry_dispersion_expectation_signal.py`).**
(a) Zero fitted parameters: no bandwidth, no elasticity, no scaling — the distribution IS
the identification (rule 21). (b) Regenerates every forecast year from in-model prior-solve
quantities only (rule 13). (c) Exact fixed points: at unchanged headroom every zone's price
multiset is reproduced exactly (mean, duration curve, hours ≥ $100, negative hours, zonal
spread in distribution); a dual surface that is itself monotone in headroom is reproduced
HOUR BY HOUR. (d) The ceiling is the dual surface: a forward hour tighter than any current
hour earns the zone's realized maximum, never a pro-forma tail (D39 §3.2's stated bound).
(e) Load growth, VRE potential, the committed pipeline and the storage shave all move the
RANK — nothing else is needed for them to act. (f) What it does NOT carry, stated before
the A/B: the prior year's LEVEL is the prior year's (the shipped stack prices S on this
year's `mc_cost` too, so control and arm share the same fuel lag and the A/B isolates
dispersion alone — D39's one term); cross-zone co-movement is comonotone by rank rather
than hour-aligned (each zone keeps its own duration curve); and the realized dispersion is
bounded by what the dispatch LP itself priced (a backcast-lane object in every ISO).

**Why a rank map and not the hour-aligned composition.** `entry_forward_expectation_signal`
transplants the residual by CALENDAR HOUR: `duals[z,t] + (S_next[t] − S_curr[t])`. A
scarcity residual pinned to hour t follows that hour even when the entering year's net
load has moved away from it, and the additive re-level can subtract a pro-forma tail from
realized duals — the ERCOT two-scarcity-objects defect
(`docs/FINDING-entry-signal-forward-expectation-2026-08-25.md` §4). A quantile map
conditions on the forward net-load POSITION and has no additive term, so that defect
cannot arise; it is also weather-year-alignment-free. The two are alternative
replacements of one object, so `__post_init__` refuses them together (rule 19), and
refuses the construction with `entry_margin_exhaustion` (the walk's delta is exact only
through maps affine in S_entering; a rank map is not). Requires `entry_lookahead_reprice`
(the headroom terms are the instrument's own); coerced off in backcast; registered in
`_CACHE_KEY_OPTIONAL_FIELDS` at its False default so every pre-existing cache key is
byte-stable (bare default key unchanged at `cedadc285f8603b9`, verified against HEAD's
`scenarios.py`; armed CAISO-forecast key `b1899bd44fcab6e0` vs `3803b40668078509` off).

**L-5 dump extension (output-only).** Under `entry_screen_diagnostics` the
`screen_signal_diag_<y>_for_<y+1>.npz` dump now also records `econ_prices_usd_mwh` — the
run's own prior-year duals — and, armed, `headroom_rank_next`, `signal_zonal_usd_mwh` and
the S_current internals (`fwd_curr_*`). With it a diagnostics-on run is self-contained
for D39 §2's expected-vs-realized instrument: the NEXT year's dump carries that year's
realized duals, so a run's own screen expectation is scored against its own realized
surface offline — no keeper stand-in, no replay. No config field, no cache-key term, no
solve-path change (the control reproduction below is the proof).


## 2. Screen grain — the construction on the D39 basis

### 2.1 Screen grain on the D39 basis (`--mode basis`): the committed dumps, the keeper's prior-year duals, the keeper's entering-year surface as realized

Five in-state zones (the seam node dropped from every arm, the L-1 convention); thermal legs on the zone mean at the screen's own recorded variable cost (gas_cc $33.46 / $41.90, gas_ct $48.32 / $60.38); storage at the entry seed; VRE on the EAC-only attribute basis the L-1 replay uses (the RPS dual is added at the composition grain, §3). `dual_prior_solve` = the raw prior-year duals hour-aligned; `fwd_expectation_prior_solve` = `entry_forward_expectation_signal` computed offline (S_current on the dump's own stack at the reconstructed current net load); `dispersion_prior_solve` = this lane's construction.

| entering | construction | mean $/MWh | daily top4−bot4 | h ≥ $100 | neg. hours | cross-zone spread | gas_cc leg $/MW-yr (÷ realized) | gas_ct leg (÷ realized) | li-ion 4 h arb. (÷ realized) | solar capture (realized) | signs cc / ct / solar / wind | storage clears |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2024 | **realized** (D39 §2 stand-in) | 36.88 | 29.08 | 85 | — | 2.97 | 75,631 | 18,817 | 22,363 | 0.768 | — | — |
| 2024 | `shipped_signal` | 39.63 | 12.71 | 0 | 0.0 % | 0.00 | 64,441 (0.852) | 1,102 (0.059) | 2,890 (0.129) | 0.900 | - / - / - / + | none |
| 2024 | `dual_prior_solve` | 54.45 | 34.98 | 699 | 4.0 % | 3.07 | 211,792 (2.800) | 115,379 (6.132) | 27,563 (1.233) | 0.802 | + / - / + / + | none |
| 2024 | `fwd_expectation_prior_solve` | 55.41 | 35.75 | 681 | 2.7 % | 3.07 | 215,735 (2.852) | 116,207 (6.176) | 27,067 (1.210) | 0.831 | + / - / + / + | none |
| 2024 | `dispersion_prior_solve` | 58.79 | 61.91 | 990 | 3.3 % | 2.41 | 242,523 (3.207) | 142,641 (7.581) | 55,808 (2.496) | 0.761 | + / + / + / + | none |
| 2024 | *headroom rank shift (mean u − 0.5)* | -0.0224 | *net load next / curr 19,695 / 19,092 MW* | | | | | | | | | |
| 2025 | **realized** (D39 §2 stand-in) | 37.78 | 28.87 | 0 | — | 3.91 | 30,596 | 531 | 25,623 | 0.793 | — | — |
| 2025 | `shipped_signal` | 35.54 | 14.36 | 0 | 0.0 % | 0.00 | 1,926 (0.063) | 0 (0.000) | 4,064 (0.159) | 0.843 | - / - / - / + | none |
| 2025 | `dual_prior_solve` | 36.88 | 29.08 | 85 | 7.4 % | 2.97 | 33,900 (1.108) | 8,666 (16.330) | 22,363 (0.873) | 0.769 | - / - / - / + | none |
| 2025 | `fwd_expectation_prior_solve` | 37.83 | 29.66 | 85 | 5.0 % | 2.97 | 33,607 (1.098) | 8,651 (16.301) | 20,901 (0.816) | 0.813 | - / - / - / + | none |
| 2025 | `dispersion_prior_solve` | 37.48 | 32.02 | 30 | 5.0 % | 2.25 | 25,478 (0.833) | 3,358 (6.328) | 18,250 (0.712) | 0.694 | - / - / - / + | none |
| 2025 | *headroom rank shift (mean u − 0.5)* | +0.0009 | *net load next / curr 17,727 / 17,663 MW* | | | | | | | | | |

Gates: shipped arm reproduces the committed L-1 replay [True, True]; 2024: reconstruction True (implied prior VRE min 91.1 MW, corr 1.0), multiset gate True (2 tied hours, max dev $0.01/MWh); 2025: reconstruction True (implied prior VRE min 138.4 MW, corr 1.0), multiset gate True (8 tied hours, max dev $0.0107/MWh); bundle key reproduced at HEAD: True (fields dropped since solve: ['caiso_bidir_intertie', 'renewable_buildout_pace']).

### 2.2 Stage-1 pre-declaration, graded (screen grain)

| item | pre-declared | measured | grade |
|---|---|---|---|
| PS0 gates | all pass | shipped arm reproduces the committed L-1 rows at both steps; reconstruction gate passes (implied prior VRE ≥ 91 / 138 MW, corr 1.000 with the dump's potential — the shipped path netted the un-curtailed VRE potential, so the reconstruction is exact); multiset gate passes to $0.011 over 2 / 8 tied headroom hours | **PASS** (the exact-multiset claim needed a tie tolerance, §1(c) amended: equal-headroom hours are priced equally by design) |
| PS1 dispersion, 2024 | daily spread ≥ 25, h ≥ $100 ≥ 300, cross-zone > 0 | 61.91 / 990 / 2.41 | **PASS** — and the spread OVERSHOOTS the duals' own 34.98 (§2.3) |
| PS1 dispersion, 2025 | spread ≥ 20; h ≥ $100 in 50–120 | 32.02; **30** | spread PASS; **h ≥ $100 MISS** — fewer tail hours than the 2024 duals' 85, because 2025's entering headroom duration has fewer extreme-tight hours (0.00 % tighter than any current hour) — the mechanism working in the realized direction (2025 realized: 0 h) |
| PS2 gas_cc 2024 | flips − → + | +$95.4k | **PASS** |
| PS2 gas_ct 2024 | stays −, leg ≥ $100k, + "possible, not predicted" | leg $142.6k, margin **+$14.5k** | **MISS** (flipped +; the comonotone spread, §2.3) |
| PS2 solar 2024 | does NOT flip; capture ≤ 0.75 (below the raw-dual 0.80) | capture 0.761 (< 0.802 ✓); margin **+$2.90/MWh** | **MISS on the sign** — the ratio fell as predicted but the arm's MEAN rose to $58.79 (2024's net load is 600 MW tighter than 2023's, rank shift −0.022), so 0.761 × 58.79 = $44.8 > LCOE $41.86; falsifier ("ratio not below the raw-dual arm's") did not fire |
| PS2 wind | + at both steps, capture ≥ 0.85 | + / +, 0.956 / 0.957 | **PASS** |
| PS2 storage | none clears; li-ion 4 h arbitrage $20–45k | none clears (li-ion 4 h −$46.1k, iron-air −$27.5k); arbitrage **$55.8k** (2024) / $18.2k (2025) | kill-gate **PASS**; 2024 arbitrage **MISS high** (2.5× the realized $22.4k — §2.3) |
| PS3 closure 2024 | cc 2–4, ct ≥ 3 | 3.21 / 7.58 | **PASS** |
| PS3 closure 2025 | cc 0.8–2.0, ct ≥ 5 | 0.833 / 6.33 | **PASS** (cc at the band's edge) |
| PS3 storage ratio | 0.6–1.3 | 2.50 (2024) / 0.71 (2025) | 2024 **MISS**, 2025 PASS |
| PS3 solar capture | within ±0.12 of realized 0.77 / 0.79 | 0.761 / 0.694 | **PASS** |
| PS3 falsifier | no 2024 ratio below the shipped | none | held |
| PS4 composition arm | within ±15 % of raw duals; keeps the solar flip | +1.9 % / +0.7 % / −0.9 % / −0.2 %; solar + | **PASS** |

Score: 10 of 14 pass; the four misses share one cause, measured in §2.3.

### 2.3 What the misses have in common — the rank map moves dispersion from BETWEEN days to WITHIN days

At unchanged headroom the construction reproduces each zone's price multiset, but not its
calendar: on the keeper's 2023 surface the system-mean daily top-4/bottom-4 spread goes from
$34.98 to **$66.25** while the standard deviation of daily means falls from $26.44 to $18.50
(2024 duals: 29.08 → 39.89 and 15.71 → 12.63). The cross-zone rows are not the cause — the
per-zone spreads equal the system's (35.14 vs 34.98; 66.25 vs 66.25). The cause is the
construction's own assumption: price is a monotone function of net-load position, so a mild
day's evening hours are priced at the annual evening quantile and its midday at the annual
trough quantile, whatever that day's level was. The realized surface is only half monotone in
headroom — Spearman(price, −headroom) = 0.54 (2023) / 0.63 (2024) — because the keeper's
level moves month to month with fuel (the Jan-2023 gas spike) and the CAISO overlay's
scarcity does not sit on the tightest installed-headroom hours. The consequence is exactly
the four misses: an intraday spread the storage screen reads as $55.8k (realized $22.4k),
a gas_ct tail that clears by $14.5k, and a solar mean that drifts up with the rank shift.
This is a property of every duration-curve method (it discards temporal correlation), and it
is the one structural amendment §8 names — conditioning the rank within a calendar window
(month) — as the successor, not run here (one construction per lane; nothing sized on this
residual).


## 3. The T1-H control — the D39 basis reproduced as a RUN, and what its ledgers add

`caiso-2021-2025-realized-t1h-d43-control` (bare recipe + `--entry-screen-diagnostics`,
key `3f924a5e9c5d57c3` at HEAD `5f1e47a6`). The D39 basis key `af508406` no longer
reproduces — two fields were deleted since its solve (`caiso_bidir_intertie`,
`renewable_buildout_pace`, rule 26) — but the RUN reproduces to the tonne: additions
6.0 / 8.0 / 3.0 / 11.838 / 0.0 GW (wind / solar / gas_cc / gas_ct / storage, decision basis),
retirements 2.24 GW, CO2 36.329 / 36.582 / 35.691 Mt, all identical to the committed
`caiso-2021-2025-realized-dumps` score. Vintage note (collision clause): D37/D42 share no file
with this lane; the control was solved at `5f1e47a6` + the D43 mechanism commit, whose unarmed
path this reproduction proves byte-identical.

### 3.1 In-run, exact (`--mode arm` on the CONTROL's dumps): the hindcast's OWN prior-year duals, its OWN realized entering-year surface


Same arithmetic, but every price surface is the control run's own — prior-year duals from the dump's `econ_prices_usd_mwh`, the realized 2024 surface from the 2024-for-2025 dump, the realized 2025 surface from `year_2025.parquet` (verified identical to the dump surface where both exist: max |diff| 0.0 on 2023 and 2024). No keeper stand-in anywhere in this table.

| entering | construction | mean $/MWh | daily top4−bot4 | h ≥ $100 | neg. hours | cross-zone spread | gas_cc leg $/MW-yr (÷ realized) | gas_ct leg (÷ realized) | li-ion 4 h arb. (÷ realized) | solar capture (realized) | signs cc / ct / solar / wind | storage clears |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| 2024 | **realized** (next dump) | 41.11 | 9.80 | 4 | — | 2.27 | 70,043 | 1,924 | 13,634 | 0.917 | — | — |
| 2024 | `shipped_signal` | 39.63 | 12.71 | 0 | 0.0 % | 0.00 | 64,441 (0.920) | 1,102 (0.573) | 2,890 (0.212) | 0.900 | - / - / - / + | none |
| 2024 | `dual_prior_solve` | 44.06 | 8.63 | 0 | 0.0 % | 1.69 | 94,646 (1.351) | 2,504 (1.301) | 7,474 (0.548) | 0.937 | - / - / - / + | none |
| 2024 | `fwd_expectation_prior_solve` | 45.02 | 13.87 | 0 | 0.0 % | 1.69 | 106,093 (1.515) | 9,245 (4.804) | 6,318 (0.463) | 0.970 | - / - / + / + | none |
| 2024 | `dispersion_prior_solve` | 44.57 | 10.24 | 0 | 0.0 % | 1.10 | 98,377 (1.405) | 3,903 (2.028) | 3,735 (0.274) | 0.939 | - / - / - / + | none |
| 2024 | *headroom rank shift (mean u − 0.5)* | -0.0224 | *net load next / curr 19,695 / 19,092 MW* | | | | | | | | | |
| 2025 | **realized** (year parquet) | 49.85 | 8.74 | 0 | — | 0.58 | 71,613 | 1,083 | 2,317 | 0.927 | — | — |
| 2025 | `shipped_signal` | 35.54 | 14.36 | 0 | 0.0 % | 0.00 | 1,926 (0.027) | 0 (0.000) | 4,064 (1.754) | 0.843 | - / - / - / + | none |
| 2025 | `dual_prior_solve` | 41.11 | 9.80 | 4 | 0.0 % | 2.27 | 17,893 (0.250) | 1,513 (1.397) | 13,634 (5.885) | 0.917 | - / - / - / + | none |
| 2025 | `fwd_expectation_prior_solve` | 42.05 | 17.13 | 4 | 0.0 % | 2.27 | 25,684 (0.359) | 3,358 (3.099) | 14,649 (6.323) | 0.954 | - / - / - / + | none |
| 2025 | `dispersion_prior_solve` | 41.04 | 11.40 | 0 | 0.0 % | 0.95 | 15,318 (0.214) | 0 (0.000) | 4,093 (1.767) | 0.907 | - / - / - / + | none |
| 2025 | *headroom rank shift (mean u − 0.5)* | +0.0009 | *net load next / curr 17,727 / 17,663 MW* | | | | | | | | | |

Gates: shipped arm reproduces the committed L-1 replay n/a (arm mode); 2024: reconstruction True (implied prior VRE min 91.1 MW, corr 1.0), multiset gate True (2 tied hours, max dev $0.0/MWh); 2025: reconstruction True (implied prior VRE min 138.4 MW, corr 1.0), multiset gate True (7 tied hours, max dev $0.0127/MWh); bundle key reproduced at HEAD: True (fields dropped since solve: []).

### 3.2 What the ledgers say that the replay could not

| year (decision) | rps_dual | VRE decided | gas_cc decided (margin, binding) | gas_ct decided (source) | storage | RM after |
|---|---:|---|---|---|---|---:|
| 2022 (bridge) | — | wind 3,000 + solar 4,000 (per-tech caps) | 1,000 (+$18.2k, `iso_budget`) | 4,402 (`reserve_backstop`) | 0 | — |
| 2023 | 50 | 0 / 0 (`per_tech_cap_zero`, the ladder's off year) | 1,000 (+$93.3k, `iso_budget`) | 5,281 (backstop) | 0 | 21.0 % |
| 2024 | 50 | wind 3,000 + solar 4,000 | 1,000 (**+$1,117**, `iso_budget`) | 1,676 (backstop); economic 0 (−$44.2k) | 0 | 17.6 % |
| 2025 | 50 | 0 / 0 | 0 (−$61.3k) | 478 (backstop); economic 0 (−$45.3k) | 0 | 28.2 % |

Three facts that fix the composition consequence before the arm ran (PREDECL §3): (i) the
attribute leg is the ACP in every year ($131k wind / $124k solar per MW-yr at the zone CF), so
VRE clears at its cap in every ladder-on year regardless of the energy leg — the volume is the
ladder's (D39 §5.2), and the replay's EAC-only solar sign is moot here; (ii) gas_cc clears
three screens at the 1,000 MW `iso_budget` cap on the $83.7k RA anchor (FFR-3W's 94–100 % of
CT revenue), so a larger energy leg cannot add a megawatt; (iii) every gas_ct megawatt is the
reserve-margin backstop, and the economic CT screen is $44–45k short with an 8 GW ISO budget
already spent by the VRE + CC rows in the ladder-on years — a clearing CT would be
budget-blocked at 0 MW anyway.

### 3.3 The exact in-run closure (§3.1) — the object D39 could not see

D39's instrument scored each screen against the KEEPER's realized surface and read the
CAISO CT at 0.07 / 0.00. Against the surface the hindcast itself paid, the shipped screen
reads **0.92 / 0.57** at entering-2024 — the under-expectation is real but a fraction of
D39's — and every construction reads 0.21–0.36 (CC) at entering-2025, where the realized
level jumped 21 % on the fuel price (mean $41.11 → $49.85) while the seam priced S_entering
on 2024's `mc_cost`. The hindcast's own surfaces: 2023 mean $44.06, daily spread $8.63, 0 h
≥ $100, 0 negative hours, li-ion 4 h arbitrage $7.5k; 2024 $41.11 / $9.80 / 4 h / 0 / $13.6k;
2025 $49.85 / $8.74 / 0 h / 0 / $2.3k. The keeper's, same years: $54.7 / $34.1 / 708 h /
4 % / $45.0k; $37.2 / $28.6 / 85 h / — / $35.5k; $38.2 / $28.0 / 0 h / — / $35.7k (D39 §2).
**The dispersion the screen discards is dispersion the forecast machinery's LP never
formed** — the keeper's is the calibrated backcast's (measured outage windows, F923 fuel,
CEMS rates, must-run floors, the CAISO scarcity overlay tuned on the backcast lane), and a
T1-H run carries none of the measured overlays by design. D39 §2 bounded this as
"second-order outside the tight step" from the ERCOT 2024 row; at CAISO it is first-order:
the keeper pays a new CT $18,817 / $531 per MW-yr in 2024 / 2025 and the hindcast pays it
$1,924 / $1,083.

## 4. The arm — `caiso-2021-2025-realized-t1h-d43-dispersion`

Key `21f7fa9d56282b22`; `run_config.json` differs from the control's in exactly one field
(`entry_dispersion_expectation_signal: False → True`); solved [2021, 2023, 2024, 2025],
bridged [2022]. The seam's own log lines, the object the screens consumed:

```
year 2023: dispersion-carrying signal for 2024 -- mean $44.60/MWh (duals $44.12, stack $39.63);
  h >= $100: 0 (duals 0, stack 0); daily top4-bot4 spread $10.11 (duals 8.37, stack 12.71);
  mean cross-zone spread $1.10; rank shift mean -0.022
year 2024: dispersion-carrying signal for 2025 -- mean $41.07/MWh (duals $41.12, stack $35.54);
  h >= $100: 0 (duals 4, stack 0); daily top4-bot4 spread $11.26 (duals 9.43, stack 14.36);
  mean cross-zone spread $0.95; rank shift mean +0.001
```

**Every ledger key identical to the control's in every year** — `entry_decided_mw_by_tech`,
`thermal_additions`, `renewable_additions`, `storage_additions`, `retirements`,
`reserve_margin`, `fleet_by_fuel_after`, `rps_dual` (checked programmatically, 5 × 8 keys,
zero diffs) — and the score is byte-identical except its timestamp (additions on both bases,
retirements, every band, CO2 to the tonne). What the arm changed is the screens' reading,
not their decision:

| decision year | tech | energy leg, control → arm ($/MW-yr) | margin, control → arm | build (both) | binding |
|---|---|---:|---:|---:|---|
| 2024 | gas_cc | 64,441 → **98,470** | +1,117 → **+35,146** | 1,000 / 1,000 | `iso_budget` (the RA anchor already clears it) |
| 2024 | gas_ct | 1,103 → 3,902 | −44,214 → −41,415 | 0 / 0 | unprofitable |
| 2024 | wind | 102,941 → 116,923 | +134,454 → +148,436 | 3,000 / 3,000 | `per_tech_cap` |
| 2024 | solar | 88,587 → 103,849 | +125,341 → +140,603 | 4,000 / 4,000 | `per_tech_cap` |
| 2025 | gas_cc | 1,927 → 15,311 | −61,345 → −47,961 | 0 / 0 | unprofitable |
| 2025 | gas_ct | 0 → 0 | −45,316 → −45,316 | 0 / 0 | unprofitable |
| 2025 | wind / solar | 92,179 / 74,393 → 107,417 / 92,426 | + / + | 0 / 0 | `per_tech_cap_zero` (ladder off-year) |

(The ledger's energy legs read the zone mean over all six rows, seam node included; the
probe's five-in-state-zone figures in §3.1/§4.1 differ by < 0.1 %.)

### 4.1 The arm's own in-run closure, exact — and the offline reproduction gate

`--mode arm` on the arm's dumps: `offline_reproduces_consumed_signal` **True** at both
steps (the construction recomputed from the dump's own duals and the seam's own two
headroom diagnostics equals `signal_zonal_usd_mwh` to the float); the multiset gate holds
(2 / 6 tied hours, max deviation $0.000 / $0.013). Against the arm's own realized surfaces
(which equal the control's, the fleet being identical): entering-2024 gas_cc **1.405**,
gas_ct **2.028**, li-ion 4 h arbitrage **0.274** of realized (control 0.920 / 0.573 / 0.212);
entering-2025 gas_cc 0.214, gas_ct 0.000 (control 0.027 / 0.000) — the fuel-level lag
(§3.3, §8.1) owns the 2025 row for every construction.

## 5. Stage-2 pre-declaration, graded (composition)

| item | pre-declared | measured | grade |
|---|---|---|---|
| PC0 arming reaches the solve | flag true; one field differs; key ≠ control | true; exactly one; `21f7fa9d` ≠ `3f924a5e` | **PASS** |
| PC1 decision-inert | every ledger row identical | identical, 5 years × 8 keys | **PASS** |
| PC2 score byte-identical | additions / retirements / CO2 / invariants | identical except timestamp | **PASS** |
| PC3 (conditional) | only if PC1 falsified | not reached | — |
| PC4 in-run closure 2024 | cc 1.2–1.6, ct 1.5–3.0, li-ion 0.2–0.5; offline == consumed | 1.405 / 2.028 / 0.274; True | **PASS** |
| PC4 falsifier | no 2024 ratio below the control's | none | held |
| PC5 reading | `I` for the T1-H lane, construction validated; object moves upstream | as stated | **PASS** |

Stage 2: 5 of 5. Stage 1: 10 of 14 (§2.2), the misses one measured cause (§2.3).

## 6. Cell verdict and dashboard

* **Matrix:** `entry_dispersion_expectation_signal` — base row added (rule 28c) with a cell in
  every ISO shard; **CAISO `I` / fc `I`** with this A/B as its evidence; ERCOT / PJM / MISO /
  NYISO / NEISO `U` with the routing note (rule 25: nothing transfers; each opens on its own
  dumps — since D43 a diagnostics-on solve commits the run's own duals, so the screen-grain
  replay scores the construction before any arm solve).
* **Forecast dashboard:** both legs registered SUFFIXED via `register_forecast_run.py --bundle`
  — `caiso-2021-2025-realized-t1h-d43-control` and `caiso-2021-2025-realized-t1h-d43-dispersion`
  (`frontend/data/hindcast/<id>.json`); the bare `caiso-2021-2025-realized` sidecar and every
  `ff-verdicts.json` key are untouched. Nothing on the backcast dashboard; no keeper, marker or
  freeze file written.
* **Committed artifacts:** the two slim bundles (score / meta / run_config / the two npz dumps,
  now carrying `econ_prices_usd_mwh`, `headroom_rank_next`, `signal_zonal_usd_mwh` and the
  `fwd_curr_*` internals on the arm), the two hindcast reports, and three probe artifacts —
  `results/calibration/entry_signal_d43_dispersion_replay_caiso.json` (screen grain, D39 basis),
  `entry_signal_d43_inrun_closure_caiso_control.json`, `entry_signal_d43_inrun_closure_caiso_dispersion.json`
  (exact in-run).

## 7. Cross-ISO code note — what the other lanes would run

The construction is shared code and touches every ISO's screens only when its ISO arms
the field; nothing here changes any ISO's default posture or cache key. What each other
lane runs, in D39 §7's routed order, with what it would need:

| ISO | precondition (D39 §7 item 1) | the lane's A/B | what the construction can and cannot move there (D39 §4) |
|---|---|---|---|
| MISO | the MISO-D33 baseline (landed) + its diagnostics-on dumps (`miso-d33-probe-entrydiag` already carries them; a re-dump at the D33 recipe adds `econ_prices_usd_mwh`) | `--mode basis` on those dumps + `miso198_oom_B`; then a T1-H control/arm pair on the D33 recipe | the peaker/CC energy leg (0.25 / 0.00 live); wind is cap-bound at 4,000 and cannot move; solar's clearing is the zone-resolved attribute + D31 capacity leg first |
| NEISO | D40 (landed) + the D37 diagnostics-on T1-H at the armed posture (expected side NOT yet committed) | the same two steps on the golden's own dumps | storage and CT/CC timing (2,243–2,446 h ≥ $100 the stack never handed the screen); VRE volume is cap-set; the REC dual is exact at the ACP; bounded by the LP's own $0.1–4/kW-yr arbitrage |
| PJM / NYISO | a first diagnostics-on solve at the LIVE stack posture (none exists) | same | NYISO's realized surface carries the widest zonal spread of the six ($4.8–12.2) — the construction's per-zone duration curves are exactly the object that spread lives in |
| ERCOT | none — its armed tail is a different object (`O`, owner-gated) | not chartered | the construction would compose with the FFR-8A tail only through the duals' realized overlay (no additive tail term), which is the successor the ERCOT finding named; untested, U |

One caution for any ISO whose screens carry a pro-forma tail (`scarcity_pricing_enabled AND
scarcity_price_overlay`, ERCOT only today): `entry_forward_reserve_leg` supplies the S_entering
adder as the reserve leg while the construction's energy leg carries the realized overlay
inside the duals — two scarcity objects joined by `max(energy, r)`, not summed; the pair is
admissible in code but is an untested posture to pre-declare, not to inherit.


## 8. What remains, and the successor constructions (named, not run)

1. **The fuel-level lag (the seam's, not this construction's).** `_lookahead_reprice_signal`
   prices S_entering on THIS year's `mc_cost` while the entrant's own variable cost uses the
   entering year's fuel driver (`resolve_annual_gas_price(config, step)` — the replay's
   $3.39 / $4.73). Every construction inherits it (entering-2025 CC 0.03–0.36 in-run). A
   forward-fuel stack — the same instrument with `mc_cost` re-evaluated at the entering year's
   resolved fuel and carbon, already in the run's hands — is zero-DOF and rule-13-admissible
   (the driver regenerates every forecast year). Not this lane's charter; named for the
   director.
2. **Within-window conditioning of the rank (the construction's own amendment).** §2.3
   measured that the annual rank map discards between-day level structure. Ranking headroom
   and reading the quantile within a calendar window (month) keeps the seasonal/fuel level
   where the LP put it while carrying the intraday distribution; the window is a calendar
   partition (the storage screen already uses a daily one), not a fitted parameter. Named,
   not run — one construction per lane, and nothing here is sized on the residual.
3. **The object itself is upstream of the screen.** With the run's own surfaces at 1/3–1/4
   of the keeper's daily spread and no tail, the forecast lane cannot price a peaker or a
   4 h battery into existence through any expectation construction; the CAISO backcast lane's
   C3c-ledgered dispersion (the keeper's own model-vs-market spread, D36 §3.3) is the smaller
   half of the gap, and the forecast-vs-backcast price-formation gap (overlays, floors, the
   overlay's arming in forecast mode) is the larger — a forecast-program dispatch object.

## 9. Recommendation to the owner (arming)

* **Do not arm `entry_dispersion_expectation_signal` as a CAISO default.** At the D39 basis it
  is decision-inert (PC1 held to the megawatt), so arming buys nothing and would change the
  cache key of every CAISO forecast; and where its screen-grain effect is largest (a tail-
  bearing surface) its within-day inflation (§2.3) over-states the peaker and storage legs.
* **Keep it as the measured, validated instrument it is** (cell `I`, construction validated
  at both grains, in-run offline reproduction exact) — the first entry-signal construction
  whose expectation can be graded against the run's own realized surface without a replay
  (the L-5 `econ_prices_usd_mwh` extension, output-only, default-safe: arm
  `entry_screen_diagnostics` on the next solve of every ISO, D39 §7 item 1, and the in-run
  closure table comes free).
* **Re-charter the under-build object one step upstream:** (a) the forward-fuel stack (§8.1)
  as the next zero-DOF screen repair, cross-ISO by construction; (b) the forecast lane's
  price-formation dispersion (§8.3) to the forecast program, with the hindcast-vs-keeper
  surface table of §3.3 as its Phase-0 measurement.

## 10. Governance attestation

Solves: the two CAISO T1-H legs of §3–§4, run in-session (no CI job; rule 12: years
sequential within each invocation; the control ran first so its ledgers could inform
stage 2 of the pre-declaration, the arm after that stage was pushed). Holdout: every solved
year is inside the plain-hindcast window {2021, 2023, 2024, 2025} with 2022 bridged; the
keeper sidecars read are 2023–2025 training years; no out-of-training year solved, scored
or registered; `--holdout-authorized` never needed or passed. Rule 15/forecast dashboard:
both legs registered SUFFIXED via `register_forecast_run.py --bundle` (ids
`caiso-2021-2025-realized-t1h-d43-control` / `-d43-dispersion`); the bare `caiso-2021-2025-
realized` sidecar and `ff-verdicts.json` are untouched; no backcast registry, keeper shard,
marker or freeze file written. Rule 28: base row + a cell line in all six shards in the same
PR; CAISO's cell carries this A/B's verdict; the five other cells are `U` with the routing
note (rule 25 — nothing transfers). Rule 13: the corridor's renewables rows and AEO appear
nowhere as targets; nothing was sized by a residual — the construction has no parameter to
size. Rule 27: every ≥300-line file (`runner.py`, `scenarios.py`, `run_capacity_hindcast.py`)
edited locally and pushed as on-disk bytes over `git push` on a freshly-rebased base, blob
sizes verified after push. Collision: D37 (NEISO) and D42 (MISO) share no file with this lane;
the shared entry-screen re-price code is unchanged in its unarmed path (control reproduction
in §3); vintage noted in §3.

## 11. Reproduction

```
# mechanism + probe + tests: commit 9b0174b3 (branch claude/capx-d43-caiso-dispersion)
uv run pytest tests/unit/model/test_entry_dispersion_expectation_signal.py -q     # 13 pass
# screen grain, zero solves
uv run python scripts/probes/entry_signal_d43_dispersion_replay.py --mode basis \
  --bundle results/hindcast/caiso-2021-2025-realized-dumps \
  --duals-bundle results/calibration/caiso231_b1_ungrounded \
  --out results/calibration/entry_signal_d43_dispersion_replay_caiso.json
# the two legs (data/clean regenerated first: PYTHONPATH=. uv run python scripts/regenerate_clean.py)
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
  --entry-screen-diagnostics --out-dir results/hindcast/caiso-2021-2025-realized-t1h-d43-control
uv run python scripts/run_capacity_hindcast.py --iso CAISO --start-year 2021 --end-year 2025 \
  --entry-screen-diagnostics --entry-dispersion-expectation-signal \
  --out-dir results/hindcast/caiso-2021-2025-realized-t1h-d43-dispersion
uv run python scripts/score_capacity_hindcast.py --bundle <each>
# exact in-run closure on each leg's own dumps
uv run python scripts/probes/entry_signal_d43_dispersion_replay.py --mode arm --bundle <leg> \
  --duals-bundle results/calibration/caiso231_b1_ungrounded --out results/calibration/entry_signal_d43_inrun_closure_caiso_<leg>.json
uv run python scripts/register_forecast_run.py --bundle <each leg>
```

The one pre-existing unit failure on `main` at this HEAD is noted, not touched:
`tests/unit/model/test_entry_vre_zone_selection.py::test_default_cache_key_is_byte_stable`
asserts the bare default key `603c2498bf71d21d`; HEAD's `scenarios.py` (before any D43 edit)
already hashes `cedadc285f8603b9` — a main-side drift belonging to whichever lane moved it,
and this lane's field leaves the key at exactly HEAD's value (verified by importing HEAD's
module side by side).

# Retirement-screen DOF identification & hindcast scoring adjudication — 2026-07-15 (RC-0B)

**Charter.** F-2 of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §1.1/§1.3, prompt
§4.2 RC-0B). Three deliverables: (a) identify the per-fuel loss-year thresholds
(`retirement_years_*`) from measured behaviour, (b) reconcile the FOM-only
going-forward-cost (GFC) construction against the published avoidable-cost bar, and
(c) adjudicate which real 2021–25 exits each retirement channel owns and define raw
vs information-set-adjusted scoring for `score_capacity_hindcast.py`. Ends with the
owner-decision box (d). **Memo only — no LP solved, no code or parameter changed,
nothing registered on any dashboard. Rules 1/13/14/21/23 govern throughout: findings
are identified from data or ledgered open; nothing is proposed because it would move
a hindcast residual.**

**RC-0A intake status (checked on disk 2026-07-15).** The RC-0A wave has NOT landed:
no `retirement-lane-intake-*.md`, no ACR/avoidable-cost datatype under
`data/raw/capacity-market/` (only `auction-price`, `demand-curve`, `elcc`), no
deactivation-notice citation rows in `docs/parameter-citations.md`, and plants 8907
(Indian Point) / 1715 (Palisades) are still absent from every
`capacity_actuals_*.csv` (RD-5 pending). Per the RC-0B prompt this memo therefore
proceeds on the **on-disk EIA-860 vintage history** (`data/raw/eia-860/vintage_2018`
… `vintage_2024` + the latest committed sheets — RD-7, the "Derive, no fetch" row),
and **flags the ACR half of §(b) as PENDING RD-4**. §(b) pre-registers the
reconciliation protocol and its break-even arithmetic so the grade is mechanical when
the data lands.

**Evidence base.** EIA-860 vintages 2018–2024 + latest committed sheets (on disk,
previously intaken); the four committed hindcast bundles' evolution ledgers
(`results/hindcast/{ercot-…-p2c,pjm-…-p2c-base,miso-…,nyiso-…}/…/evolution_*.json`);
`capacity-revenue-fom-ratio-2026-07-13.md` (BLK-9 ratios); `scenarios.py:283-366`;
`model/capacity.py` (`apply_confirmed_exits` / `apply_announced_retirements` /
`apply_economic_retirements`); `scripts/{run,score}_capacity_hindcast.py`;
`data/raw/confirmed-retirements/*.csv`. No 2022/2019/≤2021/H1-2026 market data was
read or scored (rule 22); the only 2022-dated artifact consumed is the committed
bundles' *evolution* ledger (fleet bookkeeping at the bridge step, the same events
the committed hindcast reports already describe — no bridge-year solve data exists).

---

## (a) Loss-year thresholds: what the announced→deactivation record identifies

### a.1 Semantics: what `retirement_years_*` actually compresses

`apply_economic_retirements` retires a unit the year its consecutive-loss counter
reaches the fuel's threshold, **effective immediately** (`capacity.py:1482-1486`).
Reality decomposes that interval into two parts:

```
loss onset ──(D: loss years until the owner decides/announces)──> announcement
           ──(L: announcement → physical deactivation: RTO notice, reliability
               review, decommissioning/fuel-contract wind-down)──> gone
threshold N models the TOTAL:  N ≈ D + L
```

EIA-860 identifies **L only** (first vintage whose operable sheet carries a Planned
Retirement Year, vs the retired sheet's actual Retirement Year). D — how many loss
years before an owner decides — is not observable from any on-disk source (it would
need unit P&L histories). Consequence, stated up front: **this data identifies a
per-fuel *lower bound* N ≥ median(L)** (since D ≥ 0). A threshold at or above the
bound is *consistent but not identified*; a threshold **below** the bound is
**mis-identified** — the model exits units faster than the measured
announcement-to-deactivation pipeline alone can physically deliver, before counting a
single decision year.

### a.2 Derivation (RD-7, reproducible — recipe in the appendix)

Universe: latest committed `eia860_generator_retired_and_canceled` sheet, `Status ==
"RE"`, Retirement Year 2019–2025 → 939 thermal units nationally, **583 mapped to the
six model ISOs** via the plant sheet's Balancing Authority Code (`BA_CODE_TO_ISO`).
For each unit, the first vintage data year (2018–2024) whose operable sheet carries a
non-null Planned Retirement Year strictly before the retirement year is the first
EIA-860-visible announcement; `lag = Retirement Year − first announcement data year`.

Caveats (all bias the lag **downward** or the sample smaller — none rescue a
too-short threshold):

- **Left-censoring:** a date already present in vintage 2018 (the earliest on disk)
  means the true announcement is older and the true lag longer. 66 % of announced
  coal units are left-censored.
- **Publication lag:** vintage *V* is collected during *V* and published mid-*V*+1;
  the underlying corporate/RTO announcement precedes the filing. Both effects make
  the EIA-860 lag a floor on the real public-notice lag.
- **Plant-sheet dropout:** the ISO mapping uses the *latest* plant sheet, which drops
  fully-retired plants (Indian Point's 8907 is unmapped this way — the same coverage
  mechanism as RD-5). 356 units fall outside the six ISOs or unmapped; per-fuel lag
  shapes are unaffected in direction, sample sizes are conservative.
- The `gas_st` split (NG + steam prime mover) is applied here because
  `scenarios.py` carries a distinct `retirement_years_gas_st`;
  `data.fleet._map_fuel_type` folds NG-ST into `gas_ct`, so this derivation's fuel
  grain is *finer* than the loader's, matching the ScenarioConfig grain.

### a.3 Measured lag distributions (six ISOs, retirements 2019–2025)

| fuel | n (GW) | never-announced pre-exit (% of MW) | lag yrs p25/p50/p75 | cap-wtd median | left-censored | ≥300 MW subset p50 |
|---|--:|--:|:--|--:|--:|--:|
| coal | 101 (25.6) | 12 % | 1 / **2** / 4 | **3** | 66 % | **3** (n=33) |
| gas_st | 53 (8.1) | 11 % | 1 / 1 / 1 | 1 | 35 % | 1 (n=10) |
| gas_ct | 161 (2.9) | 28 % | 1 / 2 / 3 | 2 | 60 % | — |
| gas_cc | 26 (1.2) | 14 % | 1 / 1 / 1 | 1 | 53 % | — |
| oil | 242 (2.4) | 19 % | 1 / 1 / 2 | 1 | 32 % | n=1 |
| nuclear | 0 usable | — | see a.5 | — | — | — |

Slippage (actual retirement year − first-stated planned year) has median 0 for every
fuel: **once a date is stated it is executed close to as-stated or not at all** —
the schedule's failure mode is reversal, not drift (see §c.3).

### a.4 Verdicts per field (rule 21 — identified / mis-identified / unidentifiable)

| ScenarioConfig field | current | measured lower bound (median L) | verdict |
|---|--:|--:|---|
| `retirement_years_coal` | 1 | 2 (unit) / **3** (capacity-weighted & ≥300 MW) — left-censored, so a floor | **MIS-IDENTIFIED (too short).** The only threshold sitting *below* its measured bound. Even with an instant decision (D=0), a coal unit's announcement→deactivation pipeline alone takes 2–3+ years; the screen currently exits coal in 1. |
| `retirement_years_gas_ct` | 2 | 2 | consistent, **not identified** (N = bound exactly; D unobservable). Stays; ledgered open. |
| `retirement_years_gas_st` | 2 | 1 | consistent, not identified. Stays; ledgered open. |
| `retirement_years_oil` | 2 | 1 | consistent, not identified. Stays; ledgered open. |
| `retirement_years_gas_cc` | 3 | 1 (n=26, small) | consistent, not identified. Stays; ledgered open. |
| `retirement_years_nuclear` | 3 | see a.5 (n≈2, coverage-gapped) | **unidentifiable** from this data. Stays; ledgered open. |
| `retirement_years_gas_cc_ccs` | 3 | no CCS retirement exists anywhere | **unidentifiable.** Stays; ledgered open. |
| `retirement_consecutive_years` (fallback) | 2 | n/a (never binds for the seven named fuels) | unidentifiable / dormant. Stays; ledgered open. |
| `retirement_fom_multiplier_coal` | 1.3 | external (Lazard-cited) | outside this derivation's scope, but **flagged into §(b)**: if an ACR-based coal GFC is adopted, the 1.3 regulatory-risk multiplier must be re-examined for double-counting (the monitors' avoidable-cost categories already carry compliance/insurance line items). |
| `retirement_fom_multiplier_{gas_*,oil,nuclear}` | 1.0 | neutral | no DOF (neutral band). |

Per the prompt: every "stays" above is an **open DOF-ledger row** (rule 21) — no
value is moved toward any hindcast residual, and the coal verdict cites only the lag
table, never the ERCOT over-retirement it happens to bear on.

### a.5 Nuclear: two datapoints, both outside the retired sheet

The retired sheet contains **zero** six-ISO nuclear retirements 2019–2025 — because
it omits plants 8907 and 1715 entirely (the RD-5 coverage gap). From the vintage
history directly: Indian Point 3 carried a planned 2021 date from vintage 2018
onward (announced via the 2017 Entergy/NY settlement → true lag ≈ 4 yr); Palisades
carried planned 2022 from vintage 2018 (announced 2016-12 → true lag ≈ 5–6 yr). Both
suggest nuclear L ≥ 3–4, consistent with the current 3 — but n = 2 with a known
coverage gap is not identification. Stays at 3; ledgered.

### a.6 The RD-6 notice periods, and the rule-19 overlap with `staged_oversupply_thinning`

The tariff deactivation-notice minimums (PJM Part V ≈ 90 days, ERCOT §3.14 NSO ≈ 150
days, MISO Attachment Y ≈ 26 weeks — **all pending RD-6 citation intake; treated as
unverified context, no citation row is written here**) are sub-annual: at the model's
1-year grain they cannot move any threshold. The EIA-860 lag is the binding
identification; RD-6's real customer is `staged_oversupply_thinning`'s citation.

That surfaces a **one-mechanism-per-phenomenon obligation (rule 19)** the owner box
must resolve: the measured lag L is *the same physical queue*
`staged_oversupply_thinning` models as a rate cap. If the coal threshold is raised to
carry D+L **and** staged thinning is armed, the deactivation queue is counted twice.
The two admissible compositions are stated as owner options in §(d) D1 — either the
threshold carries the measured total (staged thinning stays default-off), or the
threshold stays a pure decision lag and staged thinning carries the queue with its
own lead-time citation. Not both.

---

## (b) Going-forward cost: FOM-only vs the published avoidable-cost bar — protocol (ACR half PENDING RD-4)

### b.1 What the screen does today

`going_forward_cost = fixed_om_<fuel> × fom_multiplier_<fuel> × pmax_mw × 1000`
(`capacity.py:1386-1400`), with `fixed_om_*` ATB/Lazard-cited
(`scenarios.py:339-366`). The monitors' benchmark for the same decision — PJM Manual
18 / MSOC Avoidable Cost Rates, the Monitoring Analytics SOM avoidable-cost tables —
is built from **avoidable** categories: avoidable labor, maintenance,
materials/supplies, administrative, taxes/fees/insurance, and (in APIR variants)
carrying charges on avoidable project investment. ATB FOM is a class-average fixed
O&M, neither avoidable-scoped nor unit-specific. The two can differ in either
direction per class; **no number is asserted here** — the RD-4 intake is the
identification source (rule 23), and per rule 14 the measured bar is preferred once
it lands, with any breakage root-caused rather than reverted.

### b.2 Pre-registered reconciliation protocol (mechanical once RD-4 lands)

1. Build the per-class table: ATB-based `fixed_om_* × multiplier` vs (i) PJM default
   gross ACR by technology class (Manual 18/MSOC vintage-matched to 2021–25) and
   (ii) the SOM avoidable-cost table values, all in $/kW-yr, with the source row
   cited per cell.
2. **Materiality bar (pre-registered):** a class flips to the measured bar when the
   published avoidable-cost figure differs from the current GFC by more than the
   spread *between* the two published sources for that class (i.e., the data
   disagrees with us by more than it disagrees with itself). Below that, FOM-only
   stands and the row is recorded as reconciled.
3. Any flip is a cited data change (rule 23), lands in `ScenarioConfig` defaults with
   the citation, is LOYO-scored within 2023–2025 before promotion (rule 22), and is
   **justified only by the published number — never by the retirement count it
   produces** (rules 1/13; the flip-gate plan says this verbatim).
4. Re-run the BLK-9 ratio arithmetic (§b.3) and re-state the cliff positions in the
   ratio memo's format. Check the coal 1.3× multiplier for double-counting against
   the ACR categories (§a.4 flag).

### b.3 Break-even arithmetic, pre-registered now (no data needed)

BLK-9's ratio is `net_cone × (1−EFORd) / GFC`; fossil exit becomes arithmetically
possible in fixed mode only where GFC exceeds `net_cone × (1−EFORd)`. That break-even
GFC ladder is pure config arithmetic
(`capacity-revenue-fom-ratio-2026-07-13.md` inputs), so the RD-4 numbers can be
graded against it on arrival:

| ISO (net-CONE $/kW-yr) | coal (now 58.5) | gas_st (35) | gas_cc (30) | oil (25) | gas_ct (21) |
|---|--:|--:|--:|--:|--:|
| MISO (80) | **73.6** | 74.4 | 76.0 | 72.0 | 75.2 |
| NEISO (95) | 87.4 | 88.4 | 90.3 | 85.5 | 89.3 |
| CAISO (90) | 82.8 | 83.7 | 85.5 | 81.0 | 84.6 |
| PJM (100) | 92.0 | 93.0 | 95.0 | 90.0 | 94.0 |
| NYISO (110) | 101.2 | 102.3 | 104.5 | 99.0 | 103.4 |

Reading: **MISO coal is the only plausibly reachable cliff** — the measured bar would
need to clear ~$73.6/kW-yr vs the current $58.5 (+26 %), within the range monitors
have published for old coal. For gas_ct the bar would need $75–103/kW-yr, i.e.
3.5–5× the ATB class figure — outside anything an avoidable-cost table plausibly
reports. **Pre-registered conclusion: even a maximal defensible GFC correction
cannot reopen broad fossil exit under the fixed payment; the GFC fix is an
input-fidelity correction that may move the MISO coal cliff, while the binding fix
for BLK-9 remains the CR-chain sloped curve (flip-gate plan §2).** Stating this now
prevents the GFC lane from being graded as if it could close Direction 1.

### b.4 Expected downstream effects, named in advance

- Any GFC increase raises retire-ability *everywhere*, including ERCOT — where the
  screen already over-retires 15× on an understated revenue signal (BLK-6). A GFC
  flip must therefore be reported jointly with the T-R3 residual-gap measurement,
  and never adopted *because* it moves MISO coal (rule 1). The G-32 precedent
  applies: the 2026-07-07 FOM flip was adopted for input fidelity and explicitly
  credited with no retirement effect.
- Nuclear: `fixed_om_nuclear=130` is already avoidable-cost-flavored (NEI/EIA
  operating-cost surveys). Its sub-1.0 ratio (0.60–0.82 everywhere) is the §1.1
  inversion risk; an ACR-based restatement should cite the NEI/EIA series it
  replaces or confirm the current value as the measured bar.
- New entry is untouched (the entry screen carries its own LCOE FOM); only the
  retirement screen's bar moves.

---

## (c) Hindcast channel-split adjudication & scoring definitions

### c.1 What the committed bundles actually did (ledger evidence)

Reading every `evolution_*.json` in the four committed bundles:

| bundle | announced ("known") | economic | confirmed |
|---|---|---|---|
| PJM p2c-base | 2022: Byron 1/2 + Dresden 2/3 (4,097 MW nuclear) + 7 small biomass; 2025: 1 MW biomass | 0 MW ever | 0 rows ever |
| MISO | 2022: Palisades `1715_1` (768 MW); 2023: 16 MW biomass | 0 MW ever | 0 rows ever |
| NYISO | 2022: Indian Point 3 `8907_3` (1,036 MW) | 0 MW ever | 0 rows ever |
| ERCOT p2c | none | 2022: 13,961 MW; 2023: 1,870 MW; 2024: 6,965 MW | 0 rows ever |

Three structural facts fall out:

1. **The ledger cannot currently express the channel split.** The recorder's reason
   vocabulary is `{known, economic}` only (`capacity.py:3083,3142`): the snapshot
   for the "known" attribution is taken *before* step 0, so a confirmed exit of a
   unit-grain unit would be folded into `known`, and a confirmed **derate** of a
   plant-binned tranche (the ERCOT/CAMPD path) leaves every `unit_id` alive and is
   **invisible to the retirements ledger entirely**. Channel-attributed scoring
   (c.4) is impossible until the ledger reasons split.
2. **The committed hindcasts' as-of-2020 discipline on the confirmed/reversal
   channels is an accident of environment state, not enforcement.** Both
   `load_confirmed_exits` and `load_announced_reversal_plants` read the
   **gitignored** `data/clean/confirmed-retirements` partition and silently return
   empty when it is absent (`confirmed_retirements.py:92,167`). The committed
   ledgers prove it was absent in the run sessions: Byron/Dresden retired (the
   reversal set {6023, 869} would have suppressed them — the loader docstring
   *expects* that suppression to fire in a hindcast), and ERCOT's live Braunig 1/2
   rows (exit 2025, instrument dated **2024-03-13**) produced no 2025 event.
   **Re-running any committed hindcast after `regenerate_clean` would flip PJM by
   4.1 GW of nuclear false-retire and inject a post-2020 instrument into ERCOT,
   with zero config change.** This is a reproducibility land-mine for every RC-1A
   A/B leg and must be closed by plumbing, not luck (§d D4).
3. **Fossil economic exit is zero outside ERCOT** — the BLK-9 signature, reproduced
   exactly as the ratio memo predicts. Nothing in this memo re-litigates that; the
   split below defines what the screens are *graded on*, not why they miss.

### c.2 What was knowable as of the 2020 vintage (measured)

Share of each ISO's real 2021–25 thermal retirements whose unit carried an EIA-860
Planned Retirement date in a vintage ≤ 2020 (derivation §a.2; totals reconcile with
`capacity_actuals_*.csv` to within biomass exclusion + plant-sheet dropout):

| ISO | retired 2021–25 (GW) | as-of-2020-announced (GW / %) | coal specifically |
|---|--:|--:|---|
| MISO | 14.39 | **12.25 / 85 %** | 10.29 of 10.93 GW (94 %) |
| PJM | 10.93 | 5.73 / 52 % | 4.15 of 6.89 GW (60 %) |
| ERCOT | 1.51 | 0.93 / 62 % | 0.93 of 0.93 GW (100 % — J.T. Deely 1&2) |
| NEISO | 0.89 | 0.42 / 47 % | 0.40 of 0.50 GW |
| NYISO | 0.47 | **0.01 / 2 %** | (no coal) |
| CAISO | 0.26 | 0.01 / 3 % | (no coal) |

Two regimes: the coal-belt exits (MISO/PJM/ERCOT) were overwhelmingly *pre-announced,
knowable-in-2020* events; the NYISO/CAISO exits (gas_ct/oil peakers) were almost
entirely *unannounced* — no EIA-860 date ever appeared before the exit. Note for
RC-0A follow-up: the NYISO peaker wave has a knowable-as-of-2020 regulatory driver
(the NYSDEC "Peaker Rule", 6 NYCRR Subpart 227-3, adopted December 2019) that never
passes through EIA-860 planned dates — a candidate confirmed-registry/driver intake,
**pending its own citation row before any use**.

### c.3 …and how reliable that announced schedule was (the precision check)

Execution of the full vintage-2020 planned-retirement schedule (dates 2021–25, six
ISOs), against the latest sheets:

| fuel | scheduled GW | retired ≤2025 | still operable today | precision |
|---|--:|--:|--:|--:|
| coal | 25.55 | 14.51 | 10.31 | 57 % |
| gas_st | 8.50 | 2.11 | 6.39 | 25 % |
| gas_ct | 0.68 | 0.23 | 0.45 | 34 % |
| oil | 1.19 | 0.39 | 0.17 | 33 % |
| gas_cc | 1.78 | 0.02 | 0.01 | ~1 % (1.74 GW recategorized/unknown — data ambiguity, flagged) |
| **fossil total** | **37.7** | **17.3 (46 %)** | **17.3** | — |
| nuclear | 7.60 | 0 as-booked | 7.60 | **≈12 % incl. off-sheet IP3** |

The fossil schedule is a coin flip at the 5-year horizon — the **measured
justification for RC-3's fossil announced no-op** (`forecast_fossil_retirement_
economic=True`): honoring announced fossil dates verbatim would have retired ~2×
what executed. Nuclear is the extreme case: of ~8.7 GW of announced-as-of-2020
nuclear dates, only Indian Point 3 (1.04 GW, off the retired sheet per RD-5)
executed and stayed retired; Byron/Dresden were reversed by IL CEJA (2021-09-15),
Palisades executed then reversed by restart (~2025), Diablo Canyon extended by CA
SB 846 (2022-09). **Every reversal instrument is dated after 2020** — the class
failure is post-cutoff policy rescue, not schedule noise. And per §a.3, slippage on
executed dates is ~0: announced dates either execute on time or are reversed
outright. This sharpens the scoring problem: the announced channel's errors are not
timing errors, they are *information-set* errors.

### c.4 Channel ownership ruling (what each channel is graded on)

Under the harness's as-of-2020 information discipline (vintage cutoff **V =
2020-12-31**; anything whose instrument/announcement post-dates V is unknowable at
forecast start):

- **R1 — Economic screen owns ALL fossil exits** (announced or not): the fossil
  announced no-op stays, now with the §c.3 precision measurement as its evidence.
  The 46 %-precise announced schedule is admissible *information* but not an
  execution instrument; the screen must be able to find those exits from economics.
  (That it arithmetically cannot in capacity-market ISOs is BLK-9 — the flip-gate
  lane's object, not a scoring artifact.) The as-of-2020-announced subset (§c.2) is
  reported as a separate **announcement-assisted recall diagnostic** — a screen
  that cannot even recall the pre-announced 94 % of MISO coal is failing on the
  easiest tranche.
- **R2 — Announced channel owns non-fossil exits with a vintage-≤2020 date inside
  the horizon gate** (vintage + 5): in-window that is exactly Indian Point 3,
  Palisades, Byron/Dresden, plus small biomass. Nothing else.
- **R3 — Confirmed channel owns nothing in-window as of V.** No six-ISO registry
  row has both instrument_date ≤ V and exit_year ≤ 2025 that is live *as of V*.
  (Byron/Dresden's original PJM deactivation notifications, dated 2020-08-27, WERE
  live-and-binding as of V — their CEJA supersession is post-V. Under strict IS
  discipline they are as-of-2020 *confirmed* exits, which only strengthens the
  §c.5-1 reversal ruling below.) Braunig 1/2 (instrument 2024-03-13) is unknowable
  at V and must not fire in an as-of-2020 hindcast (§d D4).

### c.5 Scoring definitions: raw vs information-set-adjusted (for `score_capacity_hindcast.py`)

Both metrics are reported side by side on every hindcast; neither replaces the
other. **Raw** grades realized usefulness against latest truth; **IS-2020** grades
forecast skill against what was knowable at forecast start. Quoting only the more
flattering one is scoring abuse.

**Raw (unchanged G-31 grain, post-RD-5 target):** recall = per-fuel MW coverage of
≥300 MW actual exits; false-retire = per-fuel model MW in excess of actual;
actuals = `capacity_actuals_*.csv` after the RD-5 coverage fix.

**IS-2020 adjustments (deterministic, data-driven — no judgment calls at scoring
time):**

1. **Reversal exclusion (the Byron/Dresden class).** A model retirement qualifies
   iff (i) the exit was mandated by an announcement/instrument public on or before
   V, and (ii) every such instrument was superseded ONLY by counter-instruments
   dated after V (membership test = the confirmed-registry reversal rows:
   `superseded=true` with post-V superseding instrument). Qualifying MW is
   **excluded from IS false-retire** and reported as a separate
   `reversal_exposure_gw` line naming the reversing instrument. Raw scoring keeps
   it as false-retire. *Ruling: Byron/Dresden (CEJA 2021-09-15) qualify —
   information-set-correct, reality-reversed. Diablo Canyon (SB 846, 2022-09) will
   qualify for any future CAISO window reaching 2024–25.*
2. **Restart adjudication (Palisades).** Convention: **book the physical exit.**
   The RD-5-fixed actuals record Palisades as a 2022 retirement (the unit was
   deactivated ~3 years; the latest sheet's erasure of an executed exit is
   survivorship, not ground truth) and its restart as a ~2025 addition. The restart
   addition is **excluded from IS-2020 additions scoring** (post-V instrument,
   unknowable) but kept in raw. The model's 2022 announced-channel exit therefore
   scores as a correct recall in BOTH modes (±1 yr bridge tolerance per the
   committed NYISO report's convention). The alternative latest-sheet convention
   (Palisades never retired) is rejected because it would grade a correct 2022
   forecast as false using 2025 information.
3. **Coverage (Indian Point 3).** Pure RD-5 data fix, no IS logic: once plant 8907
   is in the actuals, the model's 2022 exit (real date 2021-04, within bridge
   tolerance) is a correct recall in both modes. NYISO's false-retire drops to ≈0
   (T-R8's pre-registered expectation).
4. **Channel attribution (prerequisite).** The evolution ledger's reason vocabulary
   must split into `{confirmed, announced, economic}` (today `known` conflates
   steps 0–1, and plant-binned confirmed derates are recorded nowhere — §c.1-1).
   Scoring then reports recall/false-retire per channel, so an economic-screen
   grade is never polluted by announced-channel events. Scorer + recorder change,
   owned by the RC-1A wave; scoring definitions here are written against it.
5. **Cutoff definition.** "Knowable at V" = EIA-860 planned date present in a
   vintage data year ≤ 2020, or a public instrument dated ≤ V. The vintage
   publication lag (vintage 2020 published mid-2021) is accepted and documented:
   for every in-window case the underlying announcement itself predates V
   (Byron/Dresden 2020-08-27; IP3 2017; Palisades 2016).

**What IS-2020 does to the committed headline numbers (stated for calibration of
expectations, not as a re-score):** PJM false-retire 4.10 GW → ≈0 (all four
nuclear units reclassified to `reversal_exposure_gw`; the 0.009 GW model biomass is
below the actual and never was excess); NYISO false-retire 1.04 GW → ≈0 (IP3
becomes correct recall via RD-5); MISO false-retire 0.77 → ≈0
(Palisades becomes correct recall); ERCOT unchanged (its 21.9 GW false-retire is
genuine over-retirement, no reversal/coverage component). The fossil recall
failures (−63 % / −95 % / −100 %) are **untouched by every adjustment** — scoring
hygiene does not move the BLK-9 miss one MW, which is exactly why these definitions
are safe to adopt.

---

## (d) Owner-decision box

**D1 — `retirement_years_coal` (the one mis-identified DOF).**

> **OWNER DECISION (2026-07-16) — RESOLVED: Option B adopted, RC-1A re-probe
> SKIPPED.** `retirement_years_coal` moved 1 → **3** in `scenarios.py`
> (default), cited to the §a.3 lag table only (the measured cap-weighted /
> ≥300 MW median, left-censored → conservative floor), never to a hindcast
> metric (rules 1/14). Landed by session **RC-D1** on identification alone.
> Per §a.6/rule 19 `staged_oversupply_thinning` stays default-off (the
> threshold now carries the D+L deactivation total). The §d-required
> LOYO-within-2023-2025 re-probe was **deferred by owner decision** (the owner
> skipped the RC-1A curve-ON re-probe); no hindcast LOYO was run, and RC-2B
> grades the gate analytically with this caveat. Byte-identity: the threshold
> is forecast-side capacity-evolution only, so every backcast keeper is
> byte-identical and no dashboard/keeper was touched.

- *Option A (status quo):* keep 1; ledger it open. Honest but knowingly retains a
  value below its measured floor.
- *Option B (recommended):* adopt the measured value on the capacity-weighted /
  large-unit basis: **coal = 3** (unit-median basis would say 2; the screen is
  graded in GW and the ≥300 MW recall population's median is 3; left-censoring
  makes 3 conservative-low). Identification source: §a.3 lag table (re-derives only
  when EIA-860 vintages update — rule 23). `staged_oversupply_thinning` then stays
  default-off and its charter narrows to intra-year wave shaping, because the
  threshold now carries the D+L total (rule 19, §a.6). Must be LOYO-scored within
  2023–2025 before promotion and reported **without** citing any hindcast
  improvement as justification (rules 1/22).
- *Option C:* keep coal=1 as a pure decision lag and arm `staged_oversupply_thinning`
  (default-on) as the deactivation-queue mechanism carrying L with the RD-6
  citation. Structurally coherent but pays the G-31 LP-size/runtime cost in every
  forecast run and leaves the 1-year decision component unidentified either way.
- *What B re-opens:* ERCOT first-wave timing shifts (the 2022 bridge wave thins) —
  the T-R3 reproduction values in the flip-gate plan §3 would need their BEFORE
  legs re-established; the G-30/G-31 probe conclusions about wave timing partially
  re-open; PJM/MISO are unaffected today (their screens retire nothing to delay).

**D2 — GFC basis (ACR half PENDING RD-4).** Adopt the §b.2 protocol now:
when RD-4 lands, flip any class where the published avoidable-cost bar clears the
pre-registered materiality test, per rule 14, citing only the published number.
Pre-registered reading (§b.3): only the MISO coal cliff (needs ≥ $73.6/kW-yr) is
plausibly in reach; the CR-chain remains BLK-9's binding fix regardless.
- *Re-opens:* BLK-9 ratio table restated; the coal 1.3× multiplier double-count
  check (§a.4); ERCOT screens see the same higher bar — must be co-reported with
  the T-R3 residual measurement, never adopted for its retirement effect.

**D3 — Scoring definitions (§c.5).** Adopt raw + IS-2020 dual reporting, the
reversal-exclusion rule, the Palisades physical-exit convention, and per-channel
attribution. Recommendation: adopt as specified.
- *Re-opens:* `score_capacity_hindcast.py` gains the IS-2020 pass and per-channel
  tables (scorer-only); the evolution-ledger reason split + confirmed-derate
  recording is a small recorder change (RC-1A prerequisite); RD-5 actuals fix must
  land first (T-R8 then re-scores committed bundles with no re-solve).

**D4 — Harness information gate (new finding, §c.1-2).** The confirmed/reversal
channels' as-of-2020 behavior currently depends on whether a gitignored clean
partition exists at run time — a 4.1 GW PJM swing and an ERCOT post-2020-instrument
leak (Braunig) are one `regenerate_clean` away from silently changing every A/B
leg. Recommendation: RC-1B absorbs a hindcast information gate — in hindcast mode,
confirmed rows and reversal suppressions apply **only** when instrument_date ≤ the
vintage cutoff, and the loaders' empty-on-absent fallback becomes loud (fail or
log-prominently) so environment state can never masquerade as discipline. Must land
**before** RC-1A's curve-ON probes, or their BEFORE/AFTER legs are not reproducible.
- *Re-opens:* nothing in committed results (they already behaved as-of-2020); it
  pins the behavior the committed bundles accidentally had.

---

## Appendix — derivation recipe (RD-7, reproducible)

Inputs (all on disk, immutable): `data/raw/eia-860/vintage_{2018..2024}/
eia860_generator_operable.parquet` (columns: Plant Code, Generator ID, Planned
Retirement Year), `data/raw/eia-860/eia860_generator_retired_and_canceled.parquet`
(Status == "RE", Retirement Year 2019–2025), `data/raw/eia-860/eia860_plant.parquet`
(Balancing Authority Code → `BA_CODE_TO_ISO`). Fuel mapping: model taxonomy with the
NG prime-mover split (CC movers {CA,CT,CS,CC} → gas_cc; ST → gas_st; else gas_ct);
coal = {BIT,SUB,LIG,ANT,WC,RC,SGC,CBL}; oil = {DFO,RFO,KER,JF,PC,WO,SGP}; NUC →
nuclear. Per retired unit key (plant, generator): first vintage data year < the
retirement year carrying a non-null planned date → `lag = retirement_year −
first_vintage`; `left_censored = (first_vintage == 2018)`; `known_2020 = date
present in vintage ≤ 2020`; §c.3 precision = vintage-2020 schedule rows (planned
2021–25) joined to the latest retired/operable sheets. Statistics in §a.3/§c.2/§c.3
round as shown. The derivation script is a session scratch artifact; this recipe is
the durable specification, and per rule 23 the numbers re-derive only when a new
EIA-860 vintage lands.

*Produced 2026-07-15 (RC-0B memo session — no LP solved, no parameter changed, no
dashboard touched, no holdout year read or scored). Successor input to RC-1A
(scoring), RC-1B (information gate), RC-2B (flip memo); supersedes nothing.*

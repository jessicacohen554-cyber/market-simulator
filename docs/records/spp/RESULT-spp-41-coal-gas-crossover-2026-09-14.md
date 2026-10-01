# RESULT — SPP-41: the coal↔gas merit-order crossover (card R-bf)

**Lane** SPP-41 · **Date** 2026-09-14 · **Base** `75f0e4561d13977477910077714c15a8dbc5132b`
· **Keeper** `2026-09-13-spp-38-vintage-cache` (keeper 11), bundle
`results/calibration/spp38_span` · DATA PROFILE `spp`

**ZERO LP. NO SOLVE. NO SCREEN SPENT. NO BUNDLE PRODUCED, so nothing is owed
under rule 15 `[R-DASHBOARD]` and nothing is at risk under rule 31 `[R-RETAIN]`.**
Every number below comes from `run_year(..., fleet_only=True)` rebuilds of the
keeper's own recipe (the assembled P0 objective the LP is handed), from committed
`hourly/` sidecars, from CAMPD, or from SPP's own published State of the Market
reports.

**Headline: the lane found the object, root-caused it to a missing per-ISO
derivation, found the one published instrument that reaches it — and then killed
every cheap lever, including the obvious one, at zero LP. No screen is
recommended. SPP's determination is untouched.**

---

## 0. Step 0 — the bracket cannot be narrowed. The 2025 vintage has not landed.

Re-ran `scripts/audit_eia923_completeness.py --year 2025` against the raw at
HEAD. It reproduces the committed part (`frontend/data/backcast/completeness/
eia923_2025.json`); the only movement is an immaterial-class rounding on
COAL_BIT. **Both families read INCOMPLETE, and every gate-relevant class reads
`gate: false`:**

| class | status | prior plants reporting | cur TWh | prior TWh |
|---|---|---|---|---|
| CC_REGULAR | INCOMPLETE | 17/22 (77 %) | 37.83 | 43.52 |
| COAL_PRB | INCOMPLETE | 26/29 (90 %) | 69.12 | 56.84 |
| CT_PEAKER | INCOMPLETE | 16/62 (26 %) | 3.98 | 15.08 |
| ST_GAS | INCOMPLETE | 20/36 (56 %) | 11.97 | 19.05 |
| COAL_LIGNITE | COMPLETE | 2/2 | 8.30 | 8.22 |
| CC_CHP | COMPLETE | 1/1 | 2.64 | 2.73 |

Gate-eligible (ISO, class) pairs for SPP 2025: **2**, neither of them the two
that matter. C1 `fuelmix` and C2 `sysvol` stay unscored on 2025, so the
crossover bracket stays **$2.57 (passes) – $3.72 (fails)**. Moved on without
spending an LP, as instructed.

---

## 1. Step 1 — phase 0. The arrays and the dispatch agree: **the offer construction is the object.**

Four `fleet_only` rebuilds (2024 / 2023 / 2021 / 2022), one per gas regime.
Probe: `scripts/probes/_spp41_crossover_phase0.py` (+ `_crossover_report.py`,
`_passthrough_and_crossing.py`).

### 1.1 The two stacks

| year | gas $/MMBtu | COAL_PRB pmax | PRB cw-mean fuel | CC_REGULAR pmax | CC cw-mean fuel |
|---|---|---|---|---|---|
| 2024 | 2.19 | 18,289.6 MW | **$1.769**/MMBtu | 9,955.3 MW | $2.783/MMBtu |
| 2023 | 2.54 | 18,476.3 MW | **$1.874** | 10,057.1 MW | $2.958 |
| 2021 | 3.72 | 18,457.9 MW | **$1.552** | 10,065.2 MW | $6.328 |
| 2022 | 6.45 | 18,459.8 MW | **$1.941** | 10,074.5 MW | $7.801 |

SPP's delivered coal is $1.55–$1.94/MMBtu and essentially flat — **+3.6 %**
from 2023 to 2022 while gas moved **+164 %**. That much is real and correct;
PRB contracts genuinely are mostly fixed.

### 1.2 The crossover, measured directly in the arrays

Fraction of CC_REGULAR committed+econ MW priced **above the dearest PRB row**:

| gas | year | CC MW behind the whole PRB stack |
|---|---|---|
| $2.19 | 2024 | 6.0 % |
| $2.54 | 2023 | **0.0 %** |
| $3.72 | 2021 | **97.1 %** |
| $6.45 | 2022 | 91.7 % |

Sweeping a hypothetical gas price against the 2022 fleet's own decomposition
(coal fuel held, gas fuel scaled — which is what the model itself does):

```
gas $2.00 → 14.2 %   gas $3.50 → 96.4 %
gas $2.50 → 45.5 %   gas $4.00 → 96.4 %
gas $3.00 → 80.3 %   gas $6.50 → 96.4 %
```

**The crossing sits at $2.33–$2.65/MMBtu and the model is fully saturated by
$3.50.** The dispatch bracket is $2.57 passes / $3.72 fails. **They agree.**
Per the lane's own decision rule, the offer construction is the object and the
lane proceeds rather than redirects. The plateau SPP-40 measured is visible in
the offer arrays with no solve at all.

---

## 2. Step 2 — what the arrays say is wrong

### 2.1 The passthrough sigmoid is **not being extrapolated. It is never evaluated.**

The question was whether `coal_prb_passthrough_sigmoid` is being asked a question
outside the range its anchors were identified in. It is not, because **SPP has no
anchors**:

- `COAL_SIGMOID_DEFAULTS` has **10 entries across ERCOT / MISO / PJM and no
  `("SPP", *)` key at all**;
- keeper 11 leaves all four `coal_prb_passthrough_*` scalars at `None`;
- so `fuel.trajectories.coal_sigmoid_params(cfg, "prb")` returns **`None`** for
  every supply, and `coal_passthrough_series` returns the **flat**
  `coal_prb_passthrough = 1.0`.

**Verified in the arrays, not read off the source.** Backing out
`(mc − vom) / (fuel × heat_rate)` per PRB econ row — the band multiplier is
already baked into `fleet_arrays.heat_rate`, so this isolates the passthrough:

| year | gas | implied PRB passthrough (p05 / p50 / p95) |
|---|---|---|
| 2024 | $2.19 | 1.00000 / 1.00000 / 1.00000 |
| 2023 | $2.54 | 1.00000 / 1.00000 / 1.00000 |
| 2021 | $3.72 | 1.00000 / 1.00000 / 1.00000 |
| 2022 | $6.45 | 1.00000 / 1.00000 / 1.00000 |

Exactly 1.0, **zero dispersion across 46 plants, gas-invariant across a 3× gas
range**. A live sigmoid would move this number (ERCOT's registered PRB curve runs
0.78 → 1.50 about `gas_mid` 2.85). **Keeper 11's `coal_prb_passthrough_sigmoid:
true` and `coal_prb_passthrough_tiered: true` are provably inert** — the xiso-3
"armed-looking but dead" shape. Rule 24 `[R-REGISTRY]`: SPP's `run_config.json`
and `meta.json` **overstate what the solve read**.

### 2.2 Root cause of the gap — the derivation chain was never run for SPP

```
data/raw/reference/coal_region_crosswalk.csv   → ISOs: CAISO ERCOT MISO NEISO PJM.  SPP ABSENT.
scripts/data/derive_coal_sigmoid.py            → iterates that crosswalk. Never ran for SPP.
data/raw/_processed-legacy/coal_sigmoid_params.csv → 10 rows, ERCOT/MISO/NEISO/PJM. SPP ABSENT.
config/scenarios.COAL_SIGMOID_DEFAULTS         → SPP ABSENT.
```

`coal_supply_SPP.csv` **does** exist, so SPP's per-plant rank tagging was done;
it is the **region crosswalk** — the upstream of the sigmoid derivation — that
was never built. SPP was onboarded without the coal-supply-chain derivation every
other coal ISO has.

### 2.3 **The obvious fix is dead. Killed at zero LP.**

`derive_coal_sigmoid.py`'s own header fixes `ceil = 1.0` **for every supply**
("coal's delivered cost does not follow the gas index … never a markup past it;
retires the inconsistent ceil>1.0 opportunity-cost story the D-8 audit flagged"),
and all 10 derived rows carry `ceil 1.0`. Applying that construction to SPP, at
both existing PRB shapes, against the hour-by-hour merit-order position:

| year | gas | now | ERCOT-PRB shape | MISO-PRB shape |
|---|---|---|---|---|
| 2024 | 2.19 | 34.2 % | **95.3 %** | **74.4 %** |
| 2023 | 2.54 | 39.5 % | **97.3 %** | **87.4 %** |
| 2021 | 3.72 | 95.0 % | 95.7 % | 95.7 % |
| 2022 | 6.45 | 96.7 % | **96.7 %** | **96.7 %** |

(share of CC econ MW priced above the PRB econ median; higher = more gas pushed
behind coal)

**Exactly inert in the two failing years** — at $6.45 a `ceil = 1.0` sigmoid
returns passthrough 1.000, which is what the model already does — and
**catastrophic in the two passing years**, pushing 2023 from 39.5 % to 97.3 %.
Running the repo's own sanctioned derivation for SPP would leave the defect
untouched and destroy both calibrated years. That arm is dead, for free.

### 2.4 The capacity-ceiling hypothesis is also dead, and it is dead on measurement

CAMPD census of the model's own 29-plant PRB set across every vintage on disk
(`scripts/probes/_spp41_coal_ceiling_census.py`), gross load:

| year | TWh (gross) | fleet CF | max hour | max 24 h | max 168 h | max 720 h |
|---|---|---|---|---|---|---|
| 2019 | 87.48 | 0.541 | 18.45 GW | 16.67 | 14.36 | 13.12 |
| 2020 | 77.65 | 0.479 | 19.35 | 15.70 | 14.29 | 13.48 |
| 2021 | 90.79 | 0.561 | **21.07** | 18.80 | 17.94 | 15.87 |
| 2022 | 89.57 | 0.554 | 20.13 | 18.48 | 16.94 | 15.97 |
| 2023 | 75.30 | 0.466 | 19.67 | 17.13 | 15.33 | 13.97 |
| 2024 | 72.14 | 0.445 | 19.95 | 15.59 | 13.61 | 12.48 |
| 2025 | 86.12 | 0.533 | 20.70 | 18.50 | 16.51 | 14.03 |

Model (committed sidecars, net): 2022 **101.25 TWh, peak 17.91 GW**; 2021
**98.80 TWh, peak 17.90 GW**.

**The excess is DURATION, not LEVEL.** The model's peak is **11 % below** the
measured 2022 maximum hour and below the measured max-24 h; its annual energy is
**~19 % above** the fleet's best measured year on a like-for-like net basis. And
per plant, **0 of 29 exceed their own CAMPD-demonstrated maximum** — every ratio
falls in 0.32–0.96. So `derive_coal_max_cf.py`'s demonstrated-capability ceiling
— the repo's one existing, physically-grounded, forecast-admissible coal ceiling
— **would not bind on a single SPP PRB plant.**

The four queue candidates (`coal_takeorpay_committed`,
`coal_prb_committed_dispatchable`, `coal_prb_committed_split`,
`coal_min_load_floor`) are all **commitment/floor** objects. They set where
coal's floor is; the defect is what coal **offers**. None of them is the object,
and stacking one on an unfixed offer is what rule 19 `[R-ONE-MECH]` forbids.
They stay `U`.

### 2.5 **The driver IS found, and it is published by SPP's own market monitor**

SPP's MMU publishes annual coal offer-price markups — *"the difference between
the market-based offer and the mitigated offer … weighted based on cleared
megawatts"* (ASOM 2024 fn. 135), i.e. **offer minus reference cost**, the exact
quantity the model sets to zero by construction.

| year | delivered gas | **MMU coal markup** | model markup |
|---|---|---|---|
| 2021 | $3.72 | **$6.02**/MWh | $0.00 |
| 2022 | $6.45 | **$21.12** | $0.00 |
| 2023 | $2.54 | **$6.88** | $0.00 |
| 2024 | $2.19 | **$4.29** | $0.00 |
| 2025 | $3.52 | **$5.81** | $0.00 |

Sources: `ASOM_2023.txt` L1419-21 / L24373-75, `ASOM_2024.txt` L13913-15,
`ASOM_2025.txt` L13585-87.

And the MMU names the 2022 driver explicitly (ASOM 2023 fn. 194):

> *"The increase in positive markup levels in 2022 was attributable to markups in
> coal and gas offers. Several coal resources experienced **coal deliverability
> issues as a result of rail limitations**, which resulted in many resources
> offering higher than typical mark-ups."*

So the physical scarcity the card asked about is **real and documented** — and
the market expressed it as an **offer markup, not an energy cap**. That is why
the ceiling census finds nothing: there was no ceiling, there was a price.

**It is the right sign and the right order of magnitude.** Hour-by-hour (annual
means are unusable in 2021 — Uri drags that year's mean delivered gas to
$6.42/MMBtu against a $4.17 hourly median):

| year | gas | model | +$5.81 flat | +MMU own-year | separation NEEDED | MMU measured | ratio |
|---|---|---|---|---|---|---|---|
| 2024 | 2.19 | 34.2 % | 18.2 % | 23.1 % | −$2.43 | $4.29 | — |
| 2023 | 2.54 | 39.5 % | 19.3 % | 16.4 % | −$0.61 | $6.88 | — |
| 2021 | 3.72 | 95.0 % | 71.3 % | **69.3 %** | **$9.04** | $6.02 | **1.50×** |
| 2022 | 6.45 | 96.7 % | 95.5 % | **65.0 %** | **$27.94** | $21.12 | **1.32×** |

The measured markup supplies **~two-thirds to three-quarters** of the separation
the two failing years need, and moves 2022 from 96.7 % → 65.0 %.

### 2.6 …**and no admissible parameterization reaches it.** This is the result.

1. **A same-year MMU markup overlay is backcast-only.** There is no MMU report
   for a forecast year, so it fails rule 13 `[R-MEASURED]`'s forward test. It
   would improve the backcast and give the forecast nothing — which rule 1
   `[R-STRUCT]` says is not what makes a keeper.
2. **The markup is NOT gas-keyed, so the sigmoid's functional form is the wrong
   shape for it.** Sorted by gas: $2.19→$4.29, $2.54→$6.88, $3.52→$5.81,
   $3.72→$6.02, $6.45→$21.12. Only 2022 is elevated, and the monitor attributes
   2022 to **rail**, not to gas. Fitting a four-parameter gas logistic to five
   points to capture one of them would attribute to gas what the monitor
   attributes to rail — and selecting that form because it closes our residual is
   exactly the fitted-mechanism selection rule 1 forbids. It is also precisely the
   D-8 weak identification `COAL_SIGMOID_DEFAULTS`' own header already flags.
3. **The rule-1 authorized band-multiplier channel is provably incapable of
   closing this.** Condition (b) requires ONE config across every scored year, and
   the real markup swings **5×** year-on-year ($4.29 → $21.12). Measured: a
   year-invariant +$5.81 leaves 2022 at 95.5 % (from 96.7 %) while pushing 2023
   from 39.5 % to 19.3 % — it does not touch the failing year and breaks the
   passing ones. Separately, SPP's `offer_curve_by_group` already carries the
   **identical 0.93** on all four bands of *both* `COAL_PRB` and `CC_REGULAR`, so
   moving it scales the two stacks together and cannot reverse their order.
4. **The MMU's own named driver — coal deliverability — would be forecast-
   admissible**, but nothing on disk reaches it: there is no coal receipts/stocks
   (EIA-923 Schedule-5 tonnage) intake, only the `coal_takeorpay_<ISO>.csv`
   purchase-type share. That is a data-intake decision, not a modelling one.

---

## 3. Step 3 — **no screen. No LP spent.**

The card's own stop condition is met: *"If no forecast-admissible instrument
reaches it, say so and stop — that is a legitimate result."* Every cheap lever is
dead on measurement, the obvious one (derive SPP's missing sigmoid entry) is dead
**and would actively regress two calibrated years**, and the one real driver is
blocked behind a data intake.

**Named structural successor for SPP's queue, entering as `U`:** a coal offer
markup keyed to **coal deliverability / stockpile days**, identified from the
MMU's published markup series against an EIA-923 Schedule-5 coal receipts-and-
stocks intake. Both halves are real and both are absent. Cost is an intake, not a
solve.

---

## 4. Cross-ISO: the object is **not** SPP-specific machinery — and that matters to NYISO

Rule 25 `[R-ISO-SCOPE]`: this fills no other ISO's cell and transfers no
parameter. But the card asked to say so explicitly if the object sits in shared
machinery, and it partly does. Census over every designated keeper's committed
`run_config.json`:

| ISO | offer-markup machinery armed | coal sigmoid armed → effective? |
|---|---|---|
| ERCOT | 5 mechanisms | *(none armed)* |
| PJM | `gas_offer_net_revenue_margin` | prb=INERT, **bituminous=LIVE, subbituminous=LIVE** |
| MISO | `gas_offer_net_revenue_margin` | *(none armed)* |
| NYISO | `gas_offer_net_revenue_margin` | prb=INERT (no entry) |
| NEISO | `gas_offer_net_revenue_margin` | prb=INERT (no entry) |
| CAISO | **NONE** | prb=INERT (no entry) |
| **SPP** | **NONE** | **prb=INERT (no entry)** |

Three things follow, all reported rather than acted on:

- **SPP and CAISO are the only keepers arming zero offer-markup machinery of any
  kind.** SPP's thermal classes bid exactly `fuel × HR × band_mult + vom`, coal
  and gas alike, while the MMU measures **positive** coal markups ($4.29–$21.12)
  and **negative** gas markups (monthly to −$14.54/MWh, ASOM 2025 §6). SPP is
  coal-dominant (18.5 GW PRB against 10.1 GW CC), so a zero markup on both sides
  binds harder there than anywhere else.
- **Five of seven keepers carry an armed-but-inert `coal_prb_passthrough_sigmoid`.**
  The xiso-3 shape is the majority state, not an SPP quirk. It is harmless where
  PRB is trivial; it is load-bearing in SPP.
- **`COAL_SIGMOID_DEFAULTS` and `coal_sigmoid_params.csv` disagree.** The live
  registry carries hand-tuned `ceil > 1.0` opportunity-cost curves (ERCOT prb
  1.50, PJM subbituminous 2.10) that the data-grounded derivation was written to
  retire and re-derives at `ceil = 1.0`. The derivation was never adopted. So the
  only curve *shape* in this repo that would address SPP's defect exists **only
  as an un-derived hand-tuned number**, which rule 25 refuses to transfer.

**For the NYISO lane specifically:** NYISO's gas-monotone tilt is a *different*
instance — NYISO does arm `gas_offer_net_revenue_margin`, so its gas markup
mechanism is live where SPP's is absent entirely. The shared **form** worth
comparing is that no ISO's offer construction responds to the fuel *level*, only
to the fuel *price*, except through the coal sigmoids and the `*_offer_margin`
family. No parameter is offered and no cell is filled.

---

## 5. Housekeeping

- **Parity gate still RED on exactly the two pre-existing non-SPP bundles**,
  unchanged at this base: `caiso279_ablate_dswcouple_span` and `soco15_spp_arm`.
  Rule 35 `[R-PROMOTE]` (a) is per-ISO — **not pruned by this lane**, reported
  only. (`soco15_spp_arm` carries "spp" in its name but is a SOCO bundle.)
- **Matrix (rule 28(b)):** `coal_passthrough_sigmoids` moves `U` → **`I`** for
  SPP on the §2.1 construction observation. The four floor/commitment candidates
  stay `U` — they were assessed and excluded as the object, not tested.
- **No keeper change, no registration, no re-stamp.** SPP's determination is
  unchanged: `CALIBRATED` on the 2023–2025 train-tier verdict, rule 30
  `[R-TOUCHPOINT-FOLD]` (c).
- The two shared-infra defects SPP-40 reported (`stamp_touchpoint_holdout.py`
  hardcoded NEISO caveat text; `gen_touchpoint_attestation.py`'s stale tier
  guard) were **not** re-discovered and are **not** touched — this lane
  re-registers nothing, so no re-stamp is owed.

## 6. Probes committed (all zero-LP, re-runnable)

| probe | what it establishes |
|---|---|
| `scripts/probes/_spp41_crossover_phase0.py` | `fleet_only` offer-array extraction, cached per year |
| `scripts/probes/_spp41_crossover_report.py` | the two stacks, per band; the crossover by year |
| `scripts/probes/_spp41_passthrough_and_crossing.py` | implied passthrough = 1.0 exactly; the crossing gas price |
| `scripts/probes/_spp41_coal_ceiling_census.py` | CAMPD fleet + per-plant demonstrated ceiling |

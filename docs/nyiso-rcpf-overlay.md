# NYISO RCPF scarcity-pricing overlay

**Status:** implemented (post-solve overlay), default off
(`ScenarioConfig.nyiso_rcpf_enabled`). NYISO only, system-wide (NYCA).
**Rule-19 reconciliation (2026-07-06, lane L-11):** the overlay and the in-LP
energy+reserve co-optimization (`energy_reserve_coopt`, the keeper-config
path, `config/reserve_config._nyiso_design`) price the same phenomenon —
reserve-shortage rent in the LBMP. Enabling both is now a **hard error** in
`_nyiso_design`: the overlay is the post-solve COMPARATOR for co-opt-off
runs only, never a stack on the co-opt duals. The condition-varying
requirement channel (issue #1344, `nyiso_dynamic_reserve_requirements`,
`data.nyiso_reserve_requirements` — awaiting the Ask-B intake,
`docs/handoffs/nyiso-data-asks-2026-07.md`) extends the in-LP families, not
this overlay.
**Code:** `src/market_sim/results/rcpf.py`,
`scripts/derive_nyiso_rcpf_overlay.py`,
constants `NYISO_RCPF_PRODUCTS` (`src/market_sim/config/constants.py`).
**Validated against:** `results/calibration/nyiso_cal_{2023,2024,2025}` vs
`data/raw/_validation-source/actual_lmp_hourly_NYISO.parquet` (NYCA-hub RT).

## Why

Like ERCOT (see `docs/ordc-overlay.md`), the dispatch model is a
perfect-foresight LP whose price is the demand-constraint dual with zero
unserved energy, so it **structurally cannot produce scarcity prices**. The
NYISO backcast clears a body around the right level but no tail: 2023 model
max $97/MWh vs actual $1,147; 2025 model max $138 vs actual $2,074. NYISO's
real RT price *is* energy plus reserve-shortage shadow prices — so the
faithful representation is a post-solve overlay that replicates actual price
formation, not a fit. The LP remains the validated volumes/emissions engine
and is byte-identical with the overlay on or off.

## The published mechanism (provenance)

NYISO prices real-time scarcity through its **Reserve Constraint Penalty
Factors (RCPF)** — stepped reserve *demand curves*, not an ERCOT-style
ORDC/LOLP curve. When dispatchable headroom falls below an operating-reserve
requirement, the demand curve sets the reserve clearing price, and through
energy/reserve co-optimization that shadow price flows into the LBMP. The
products are **nested** — 10-minute spinning ⊂ 10-minute total ⊂ 30-minute
total — so in a deepening shortage the penalties **stack** into the energy
price. That stacking is how NYISO RT LMP reaches the high-hundreds /
low-thousands off a ~$2,000/MWh energy offer cap.

Requirements (NYISO Transmission & Dispatch Operations Manual; 2025 largest
single contingency ≈ 1,310 MW): 10-min spinning = ½ contingency = 655 MW,
10-min total = contingency = 1,310 MW, 30-min total = 2× contingency =
2,620 MW.

Demand curve (NYISO MST Rate Schedule 4 / Ancillary Services Manual; the
NYCA 30-minute curve per FERC Docket ER21-502, effective 2021):

| Product            | Requirement | Max shadow price | Critical level |
|--------------------|-------------|------------------|----------------|
| NYCA 30-min total  | 2,620 MW    | $750/MWh         | 1,965 MW       |
| NYCA 10-min total  | 1,310 MW    | $750/MWh         | (ramp to 0)    |
| NYCA 10-min spin   | 655 MW      | $775/MWh         | (ramp to 0)    |

The NYCA 30-minute curve is a nine-step downward-sloping curve that reaches
its $750/MWh maximum at the 1,965 MW critical level (FERC ER21-502); the
overlay represents each product's curve as **piecewise-linear** between its
published anchors (requirement → $0, critical → max penalty). The anchors
trace to the tariff; the slope between them is linearised pending the full
nine-step table (WebFetch of NYISO/FERC source PDFs is unavailable in this
environment). **Nothing here is fitted to LMP residuals**, and every value is
a `ScenarioConfig` override (`nyiso_rcpf_products`).

## Model mapping (documented approximations)

* **Reserves** R = dispatchable-fossil available capacity (`gas_cc`,
  `gas_ct`, `gas_st`, `oil`, incl. the outage overlay/derates) minus their
  dispatch, plus storage headroom (power cap − discharge + charge). Nuclear
  is baseload (no reserve; its headroom ≈ 0 anyway), coal is retired in NY,
  and renewables/hydro are excluded (renewables provide no NYISO operating
  reserve; hydro headroom is energy-limited — a small conservative omission).
* **No on-line/ramp split.** The LP has no per-unit ramp-rate or commitment
  state, so it cannot distinguish 10-minute-capable from 30-minute-capable
  headroom. Every product sees the same R; the nesting is carried by the
  requirements (a shortfall deep enough to breach the 10-min requirement is
  by construction also short of the 30-min requirement, so the curves stack).
  This over-states 10-minute capability and only matters in already-critical
  hours.
* **System-wide (NYCA).** Locational reserves (East zones F–K = 1,200 MW;
  SENY 30-min = $500/MWh; NYC; Long Island) need per-zone headroom and land
  with the zonal-congestion fix — see the finding below. The system-wide
  overlay matches the NYCA-hub RT price the backcast reports.

## Update 2026-07-07 (G-20c): the downstate gate is (largely) lifted

The gating cause below — "static Gold-Book load shares never let downstate peak
hard enough to bind the interfaces" — is now **fixed**. The energy LP was
silently dispatching on the static per-zone `load_share` (all zones peaking the
same hour; NYC 0.28 / LI 0.12) because `eia_loader.load_zonal_shares` read the
measured hourly shares only from the **clean** parquet, which is derived and
gitignored (absent in a fresh clone) — so the measured "pal" actual-load (upload
U3) never reached the solve. `load_zonal_shares` now falls back to parsing the
raw file directly (rule 12: measured > estimate), so every zone gets its own
measured diurnal/seasonal shape. The measured shares put materially more load
downstate at peak (NYC 0.34, LI 0.17) and let downstate peak at its own hours.

**Result (keeper recipe + measured shares, run `2026-07-07-nyiso-56-measured-zonal`):**
the import-constrained NYC/SENY pocket now tightens in the real tight hours and
the **in-LP locational reserve co-optimization** (`energy_reserve_coopt`, 7
locational families) fires — 2023 NYC/Hudson LBMP reaches **$1,684/MWh** while
Upstate maxes at $152 (genuinely locational, as this section predicted). C3c tail
vs RT actual: 2023 **21 h vs 10 h** (was 0), 2025 14 h vs 42 h; C3a 2023 mean bias
−9.0% → +1.6% (vs DA); C1/C2/C4/C7 hold. The system-wide overlay curves in this
doc remain the co-opt-off comparator; nothing here was tuned. **Still open:** 2024
(a mild year) and the 2025 *deep* (>$300) tail stay under — the remaining
perfect-foresight import over-service. The next lever is downstate import
discipline: the **measured** NYC locality import limit is **2,875 MW** (curated
`capacity-deliverability` datatype) vs the model's 3,900 MW Dunwoodie-South
energy-TTC estimate, applied in the summer-peak window exactly as the Zone-K TSL
(`nyiso_li_lcr_tsl`, #1345) already applies the LI limit.

## Finding: the 2023–2025 tail is *locational*, and the overlay is gated by
## the LP's perfect-foresight headroom

*(Original finding, retained; the gate it describes is lifted by the 2026-07-07
update above.)* Run across all three keeper bundles, the system-wide overlay
fires **zero**
adder in every hour. The diagnostic (`--diagnostic`) localises why: even in
the actual >$300/MWh hours, the model's NYCA-wide reserve headroom is ~4–6 GW
(2023: median 5,954 MW, p5 3,981 MW), never approaching the 2,620 MW 30-min
requirement. The headroom *does* fall with price (2023: median 9,344 MW at
<$50 → 5,954 MW at >$300), so the mechanism is directionally right — it is
just ~3–4 GW too loose to bind.

The cause is structural, not a curve-calibration problem, and **must not be
papered over** (per the calibration methodology: a real input that makes the
backcast worse is a discovered bug elsewhere — fix the root cause, never bury
the error inside an inflated requirement or a headroom offset):

1. **The 2023 NY scarcity tail was locational.** In the model's tightest
   hours ~3.5 GW of imports plus idle gas leave 4–5 GW of NYCA-wide headroom;
   real RT spikes to $1,147 came from **downstate import-constrained pockets**
   (zones J/K behind binding Central-East / UPNY-SENY / Dunwoodie / Long
   Island interfaces) and the **locational** East/SENY/NYC/LI reserve
   requirements — none of which a NYCA-aggregate energy LP can see. This is
   the same root cause as the congestion/zones gap (`#1` in the scorecard):
   static Gold-Book load shares never let downstate peak hard enough to bind
   the interfaces.
2. **Perfect-foresight headroom bias + import over-service.** The energy LP
   commits with perfect foresight and treats imports as flexible cheap slack
   that backs down gas, so NYCA-wide capacity is never exhausted.

**Therefore:** the overlay is correct, parameter-honest infrastructure that
stays inert until the upstream physics lands. The path to the tail is, in
order: (a) per-zone hourly actual load (upload **U3**, now active) + the
TTC/interface audit so downstate binds; (b) **locational** East/SENY/NYC RCPF
products keyed off per-zone headroom (now implemented — see below); then (c)
the system-wide curves here bind naturally in genuinely NYCA-wide-tight hours
(e.g. extreme winter/summer capacity events). Forcing the system-wide curve
to fire now — by inflating requirements or subtracting a multi-GW headroom
offset — would bury the locational/import error, so it is deliberately not
done.

## The locational overlay (`--locational`)

With measured zonal load (upload U3) active, the per-zone diagnostic confirms
the locational thesis: in the 2023 actual >$300/MWh hours the **NYC** zone's
reserve headroom collapses to ~1,000 MW — exactly the NYC 30-minute reserve
requirement — while NYCA-wide headroom is still ~5 GW. The shortage is real
but lives *inside* the import-constrained NYC/SENY pocket, invisible to the
NYCA-aggregate energy LP.

`results.rcpf.locational_zone_adders` prices that shortage. NYISO's reserve
market is **nested and locational** (`constants.NYISO_RCPF_LOCATIONAL`):

| Region | Model zones (NYISO A–K) | Product | Requirement | Max penalty | Source |
|---|---|---|---|---|---|
| NYCA   | all five (system-wide) | 30-min total | 2,620 MW | $750 | FERC ER21-502 / SOM |
| East   | Capital_Hudson, Lower_Hudson, NYC, Long_Island (F–K) | **10-min** total | 1,200 MW | **$775** | SOM 2023–25 |
| SENY   | Lower_Hudson, NYC, Long_Island (H–K) | 30-min total | **1,300 MW** | $500 | SOM 2023–25 |
| NYC    | NYC (J) | 30-min + 10-min | 1,000 / 500 MW | **$25** | SOM 2023–25 |

Each region's reserve headroom is the **sum of its member zones'** dispatchable
headroom, and a zone's locational adder is the sum of the demand-curve prices
of every region that contains it (the NYCA system tier is added on top of all
of them). This reproduces the measured cascade tiers (`process_nyiso_as.py`):
A–E carry NYCA only, F adds East, G–K add SENY, J adds NYC.

**SENY MW resolved + all locational values grounded (2026-07-07, G-20c).** The
earlier `TODO(SENY-MW)` placeholder and the interim `$500` NYC penalty are
**superseded by the primary source** — the NYISO **State-of-the-Market** report,
which is in-repo (`data/raw/NYISO/NYISO-{2023,2024,2025}-SOM-*.pdf`) and states
the as-enforced locational products verbatim, identically across all three years
(2023 p.305 / 2024 p.297 / 2025 p.323, "Operating Reserves and Regulation"):
*10-minute East* 1,200 MW at **$775/MW**; *30-minute SENY* "at least **1,300
MW** for all hours" at $500/MW (an additional condition-varying increment binds a
subset of hours at $40/MW — the #1344 dynamic channel, not this static base);
*30-minute NYC* 1,000 MW and *10-minute NYC* 500 MW, each at **$25/MW**. So the
prior table was wrong on three counts — East was a *10-minute* $775 product (not
30-min/$500), SENY is **1,300 MW** (not the 1,100 MW nesting midpoint), and the
NYC-specific penalties are **$25** (not $500; the real downstate scarcity is
carried by the East $775 and SENY $500 tiers, not the small NYC-specific one).
In the live in-LP co-optimization (`reserve_config._nyiso_design`) the product
name sets the reserve class, so the corrected 10-minute East now draws only
quick-start {gas_ct, oil} headroom — the downstate F–K peaker fleet the real
market commits for reserve. **Nothing is fitted to LMP residuals** (rules 12/13);
each zone's modeled adder is validated against the measured per-zone RT reserve
price (the committed `actual_as_reserve_NYISO.parquet` carries a
`reserve_<model_zone>` column for all five model zones, built from the NYISO
OASIS RT ancillary-service archive, 2023–25, all 11 settlement zones).

Across all three keepers the NYC locational adder fires in the right hours and
its mean tracks the measured N.Y.C. reserve adder without tuning (2023:
model **$5.15** vs measured **$6.37**; 2024: $4.36 vs $7.64), producing a
downstate price tail to ~$1,100/MWh the energy-only LP could not. It still
*under-fires in incidence* (2023: 219 h vs measured 3,020 h; the gap widens in
the tight 2025 summer, $6.06 vs $28.73) because the LP's downstate headroom is
still too loose in the body — the perfect-foresight import over-service that
backs down NYC gas. That residual is the **import-discipline** lever (price
each import tranche from its neighbor's marginal cost), the next structural
step; the overlay quantifies exactly how much headroom the imports are giving
away, rather than hiding it.

## Measured validation (NYISO OASIS ancillary-service prices)

The published `NYISO_RCPF_PRODUCTS` curve values are not taken on faith. NYISO
OASIS real-time ancillary-service prices (`rtasp`, processed by
`scripts/process_nyiso_as.py` into `data/raw/_validation-source/actual_as_reserve_NYISO.parquet`)
give the **measured** per-zone reserve clearing prices — the empirical RCPF
realization — and the overlay report compares the model adder against them.

The 2023 RT data corroborates both the curve values and the locational
finding: the per-zone 30-min reserve price cascades from upstate (**WEST**
max **$662**, nonzero 196 h — right under the $750 NYCA cap) through the
East/SENY zones up to **N.Y.C.** (max **$727**, nonzero 515 h), and the
*stacked* reserve price reaches **$2,448** in NYC (how the LMP tail reaches
$1,147+). The measured NYCA (system-wide) reserve adder is >$0 in 629 h
(mean $2.20); the downstate NYC cascade in 3,020 h (mean $6.37) — ~5× the
NYCA incidence, i.e. the scarcity is overwhelmingly downstate. The overlay's
system-wide adder is $0.00 against all of it, which is the quantified,
measured version of the gating finding above.

## Usage

```
python scripts/derive_nyiso_rcpf_overlay.py results/calibration/nyiso_cal_2023 \
    [--years 2023 2024 2025] [--tag scenarioX] [--rebuild-availability] \
    [--diagnostic] [--locational]
```

Writes `availability_rcpf.parquet` (cached reserve-fleet availability,
reconstructed via `run_year(fleet_only=True)` — no LP re-solve) and
`scarcity.parquet` (per (year, hour): `reserves_mw`, `scarcity_adder`,
`lmp`, `lmp_scarcity`, and a per-product price column), next to the
energy-only LMP. `--diagnostic` prints the headroom-vs-actual-tail
localisation (the pre-adder gate) and exits.

`--locational` runs the per-zone overlay instead: it caches
`availability_rcpf_zonal.parquet` (per-model-zone reserve-fleet availability,
thermal dispatch and storage cap), writes `scarcity_locational.parquet` (long,
per (year, hour, zone): `reserves_mw`, `nyca_adder`, `locational_adder`,
`scarcity_adder`, `lmp`, `lmp_scarcity`), and prints each model zone's modeled
adder against the measured per-zone RT reserve price
(`data/raw/NYISO-AS/NYISO_as_rt_<year>.csv`). The LP is untouched — the
adder is post-solve, stacked onto the persisted zonal LBMP.

# FINDING — capx D61: the PJM CT / ST / oil "E&AS operand", adjudicated — the revenue the hindcast price denies those fleets is REAL but SMALL in the published record ($2–18/kW-yr, mostly uplift and reactive), its LP home (the reserve co-opt) is a disclosed architectural limit that yields $0–1.4/kW-yr at PJM scale, and the D57 price ratio is driven by two other objects: the going-forward BAR (ATB FOM vs PJM's own published default gross ACR) in 2022/23–2023/24, and the supply CENSUS in 2024/25–2025/26, where every offer already clears

**Lane:** capx D61 (director r#38), Phase-0 ADJUDICATION of the successor D57 §4 named. Branch
`claude/capx-d61-pjm-eas-operand`. **Zero solves.** Every model number is read from committed
artifacts — the D57 arm-A ledgers (`results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/
PJM/f0e050e820c1159a/evolution_<year>.json`, their `capacity_clearing.offer_stack` and
`pipeline_events`), the D57 instrument JSON (`docs/handoffs/d57/ab-compare-2026-09-05.json`),
the PJM backcast keeper's committed sidecars (`results/calibration/pjm_debugb_inputclock_A/hourly/
{reserve_family,system,class_hourly}_<year>.parquet`) and the recipes' `run_config.json`.
Every market number is a published observable (rule 13): the Monitoring Analytics SOM sections
fetched and hashed in `docs/handoffs/d61/som-sources-2026-09-05.md`, and the in-repo DataMiner2
reserve-market feeds (`data/raw/PJM-AS/`). Instruments and outputs: `docs/handoffs/d61/
offer-stack-census-2026-09-05.{py,json}`, `reclear-2026-09-05.{py,json}` (the committed stacks
re-cleared through the code's own `clear_capacity_supply_stack` + `capacity_supply_curve`;
reproduction of the committed clearing exact), `as-pools-2026-09-05.{py,json}`. **Nothing
built, nothing armed, no field, no matrix cell moved** (§5).

DATA PROFILE: `code` (the `data/raw/PJM-AS` feeds and `_validation-source` were already present).

---

## 0. The answer in one paragraph

D57 measured that the gas-CT / gas-ST / oil offers sit at their full bars because their screen
E&AS is exactly zero, and that a margin of ≥ 3.8 / 18.0 / 8.6 $/kW-yr would put them at the
published price. This lane finds: **(1)** the zero is exact and structural — in PJM's hindcast
recipe the screen sees the energy dual and nothing else (no reserve co-opt in the recipe, and the
runner wires reserve duals into the screen for ERCOT only), and the 2022/23 and 2023/24 offers
were built on the **2021** dispatch year because 2022 is the rule-22 bridge; **(2)** the revenue
the real fleets earned that the price denies is real but small — the SOM's existing-unit median
energy-plus-AS net revenue was **$2.2 / 18.3 / 5.0 / 8.2 per kW-yr for frame CTs** (2021–2024),
**$0** for oil/gas steam in every year, and it is mostly uplift and reactive, not energy or
reserves; in the two solved dispatch years the model's own CT E&AS (6.8 / 11.2) already sits at or
above that median; **(3)** the reserve co-opt is NOT the operand's home: PJM's published SR+NSR
settlements are $82–85 M/yr across a ≥ 60 GW eligible fleet (≤ $1.5/kW-yr for a CT even at the
record), and the model's own co-opt — the keeper's, which the forecast recipe does not carry — sums
its family duals to **$0 / $9 / $1,361 per MW-yr** (2023–2025) because reserve supply is 5–10× the
requirement (pjm-138 D5b, the LP-vs-MIP boundary); **(4)** re-clearing the committed stacks with
the SOM medians in place of the model's E&AS moves the price the WRONG way at the model's bars
(1.52× → 1.86×, 2.43× → 2.73×) because the model's coal and CC margins EXCEED the record's;
**(5)** what moves the ratio toward 1× with zero coefficients is the **bar** — PJM's own published
default gross ACR (Manual 18 §5.4.8.4(B), already intaken at `data/raw/capacity-market/
avoidable-cost-rate/pjm/pjm.csv`, the cap 61–74 % of resources actually elected in these BRAs)
in place of the ATB-FOM proxy: alone **1.52 → 1.06×, 2.43 → 1.56×** with the position within
+0.10 / −0.27 pt; with the SOM E&AS medians on top **0.87× / 1.28×** at +0.34 / −0.04 pt; **(6)**
in 2024/25 and 2025/26 no offer-side operand can move the price at all: every offer already
clears and the curve is read at the model's census position, 2.34 / 3.88 pt (3.9 / 5.8 GW of
accredited supply) below the published cleared position — a supply-census object (D48 §3.3 /
D52), not an E&AS one; **(7)** the gas-steam over-exit (9.5 vs 2.7 GW) survives every scenario —
real steam sellers cleared with $0 E&AS and 0 % cost recovery, i.e. they offered BELOW the cap;
that is the offer-convention limit D54 §2 item 4 stated, not a revenue stream. **Charter for D62
(§4): the PJM going-forward bar := the published default gross ACR (one bar, offer and exit,
rule 19), plus the tariff's own reactive component ($2,199/MW-yr, PJM's E&AS-offset input) as the
single out-of-market leg; the reserve co-opt arming and the 2024/25 census are two SEPARATE
director cards, stated with their costs.** Rule 21: no number in this finding is proposed as a
parameter; the published bar is the mechanism's own operand, and a lane that finds itself choosing
among its columns by the residual has crossed the line (§3).

---

## 1. The census of denied revenue

### 1.1 What the stacks say (arm A, UCAP basis; `offer-stack-census-2026-09-05.json`)

`EAS = bar − offer × 365 × a / 1000` $/kW-yr nameplate, censored at the bar when `offer = 0`.
The screen year → dispatch year map is **2022 → 2021, 2023 → 2021, 2024 → 2023, 2025 → 2024**:
2022 is the rule-22 validation-tier bridge (evolved, never solved), so the year after it "keeps
consuming the last solved year's prior_results" (`runner.py` §last_solved_year; ledger rows carry
the same `screen_price_max 52.77 / mean 36.96` in both the 2022 and 2023 screens).

| screen → DY (dispatch yr) | class | units / firm MW | at EXACTLY zero E&AS | E&AS p50 (MW-wtd mean) $/kW-yr | above the published price | D57's "≥ X to reach published" |
|---|---|---:|---:|---:|---:|---:|
| 2022 → 22/23 (2021) | gas_ct | 404 / 24,244 | **330 / 22,728** | 0.0 (0.0) | 404 / 24,244 | 3.8 |
| | gas_st | 115 / 8,802 | **115 / 8,802** | 0.0 | 115 / 8,802 | 18.0 |
| | oil | 421 / 3,723 | **421 / 3,723** | 0.0 | 421 / 3,723 | 8.6 |
| | gas_cc | 234 / 49,986 | 40 / 1,145 | 25.4 (19.8); 66 units at offer 0 | 157 / 22,357 | 12.7 |
| | coal | 165 / 32,411 | 2 / 30 | **55.4** (50.5); 62 at offer 0 | 48 / 7,110 | 41.7 |
| 2023 → 23/24 (2021) | gas_ct | 403 / 24,243 | 330 / 22,728 | 0.0 | 403 / 24,243 | 9.3 |
| | gas_st | 77 / 1,982 | 77 / 1,982 | 0.0 | 77 / 1,982 | 23.4 |
| | coal | 165 / 32,411 | 2 / 30 | 55.4 | 79 / 8,873 | 47.0 |
| 2024 → 24/25 (2023) | gas_ct | 404 / 24,244 | 0 | **6.8** (6.1) | 364 / 23,980 | 8.9 |
| | oil | 8 / 3,723 | 8 / 3,723 | 0.0 | 8 / 3,723 | 15.5 |
| | coal | 165 / 32,411 | 0 | **16.1** (13.4) | 165 / 32,411 | 48.4 |
| 2025 → 25/26 (2024) | gas_ct | 404 / 15,475 (ELCC) | 0 | **11.2** (10.5) | 0 | — |
| | coal | 157 / 28,874 | 0 | 19.6 (16.4) | 0 | — |

One correction to the record: D57 §4's table reads gas_ct "**404 / 24,244** at the full bar" in
2022/23; the instrument's own JSON (`eas_operand.gas_ct.n_at_full_bar`) reads **330 / 22,728**
at the bar and 404 / 24,244 **above the published price**. The oil and steam counts are as stated.

### 1.2 What the published record says the same fleets earned (SOM Tables 7-36 / 7-40; full rows in `d61/som-sources`)

Existing-unit **median** energy + ancillary net revenue (energy net of SRMC + uplift + regulation
+ synchronized reserve + black start + reactive), $/kW-yr:

| dispatch year | CT (frame; aero) | oil/gas steam | diesel | CC | coal | **model screen E&AS, same year**: CT / ST / oil / CC / coal |
|---|---:|---:|---:|---:|---:|---|
| 2021 | **2.2**; 6.9 | (0.8) | 10.6 | 27.8 | 27.2 | **0 / 0 / 0** / 25.4 / **55.4** |
| 2022 | **18.3**; 22.2 | 0 | 36.2 | 83.5 | 31.5 | *never seen — the bridge* |
| 2023 | **5.0** (all CT) | 0 | 0 | 55.1 | (7.9) | **6.8 / — / 0** / ≥ 30 / 16.1 |
| 2024 | **8.2** | 0.3 | 6.7 | 72.7 | 11.3 | **11.2 / — / 0** / ≥ 30 / 19.6 |

Read against §1.1: the D57 gap for CTs (≥ 3.8 in 22/23, ≥ 9.3 in 23/24) is of the same order
as what the real frame-CT fleet earned in **2021** (2.2) — i.e. the record does NOT show the CT
fleet holding the E&AS that would offer it at $50 / $34 from the model's $21/kW-yr bar; it held
$2–7. Steam held nothing in any year (median $0, E+AS cost recovery 0 %) and still cleared
(actual exits 2.7 GW against the model's 9.5). In the two solved dispatch years the model's CT
E&AS is at or **above** the record's median. The coal row is the surprise the other way: at 2021
prices the model credits coal **$55/kW-yr against a record median of $27**, twice the record —
which is why the model's coal cohort clears at the arm's dear price while the record's coal
median recovered 4–51 % of avoidable cost.

### 1.3 The streams, sized ($M/yr, then per class-kW), and which the LP can carry

| stream | 2022 | 2023 | 2024 | per class-kW (SOM ICAP) | LP-carriable? |
|---|---:|---:|---:|---|---|
| Energy net revenue | (in 1.2) | | | frame-CT median: see 1.2; new-entrant CT 44.6 / 106.8 / 60.3 / 73.0 (2021–24, 9,241 Btu/kWh) | **yes** — the energy dual (the price-formation tail: §2a) |
| Uplift (operating-reserve credits, T4-4) — CT | 174.5 | 92.8 | 119.9 | CT **7.6 / 3.6 / 4.7**; steam-other 39.8 / 19.8 / 71.1 → **7.5 / 5.5 / 24.8**; coal 1.0 / 1.2 / 2.4 | no — a non-convexity make-whole settlement; the LP prices no start/min-run shortfall |
| Reactive (Schedule 2), total | 385.5 | 389.1 | 380.7 | PJM's own offset counts **$2,199/MW-yr** (2024 SOM sec 10); new-entrant CT 2.4–2.9 | no — tariff revenue requirement, outside the LP |
| Synchronized reserve credits | ≈ 70 (Jan–Sep tier-2 + LOC; Oct–Dec net −2.6) | 73.0 | 74.1 | ≈ **1.2** over the ~60 GW online-eligible fleet | in principle (the co-opt); in fact §2a |
| Non-synchronized reserve credits | ≈ 15 Jan–Sep; Dec −23.8 (Elliott) | 9.0 | 10.2 | ≈ **0.4** over the 25.8 GW CT fleet | same |
| Secondary (30-min) | 0.7 | 1.2 | 2.3 | ≈ 0 | same; $0 MCP in 2023–24 |
| Regulation | 296.2 | 134.0 | 183.2 | a 525–800 MW product (RTO REG cleared mean 652–691 MW) | no — not modelled, not class-wide |
| Black start (Schedule 6A) | 68.6 | 67.3 | 73.8 | unit-specific, no public roster | no |

DataMiner2 scale check (`as-pools-2026-09-05.json`, RT, Σ cleared × MCP): SR RTO $83.4 / 37.0 /
70.4 / 108.8 M, PR RTO $38.9 / 34.4 / 75.7 / 110.5 M (2022–2025), REG $310 / 131 / 186 / 330 M;
DA SR RTO $67.7 / 63.0 / 129.8 M (2023–25). A MW assigned in EVERY interval would earn SR RTO
$67.6k / 13.3k / 24.5k / 38.7k per MW-yr — the price per assigned MW is high in scarce hours, the
pool is small, and the pool is what a class shares.

### 1.4 What the hindcast price can carry and what it structurally cannot — wired, read off code

- **Energy λ: yes.** `apply_economic_retirements` values `Σ_t max(0, price − mc, r) × cap` and
  the clearing offer reads exactly `net_revenue − capacity_revenue` (design §3.1; spec §5.9), so
  the offer inherits the screen's margin one-for-one.
- **Reserve duals: NO, for PJM, three times over.** (i) The runner builds `reserve_price_signal`
  from `reserve_price_by_family` only under `iso == "ERCOT" and ercot_thermal_as_endogenous`,
  else from the post-solve ORDC `overlay_adder` (`runner.py` "Reserve-price signal for next year's
  capacity screens"); PJM has no overlay (`scarcity_price_overlay=False`; matrix
  `ordc_scarcity_overlay` PJM = **G**, the co-opt owns the phenomenon), so the signal is `None`
  and `screen_reserve_value_enabled=True` is inert. (ii) The annual fallbacks are ERCOT's too:
  `thermal_as_revenue_per_mw_yr` is `None` unless `iso == "ERCOT"`, and `as_revenue_per_mw_yr`
  returns 0 because `AS_REVENUE_PER_KW_YR_BY_ISO` has no PJM entry — every PJM `pipeline_events`
  row reads `as_pricing: exogenous_flat`, `reserve_signal_mean 0.0`, `reserve_uplift 0.0`,
  `as_annual_credit 0.0`. (iii) Upstream of both: the `pjm-t1h` recipe solves with
  **`energy_reserve_coopt = False`** and every `pjm_reserve_*` off (`run_config.json`), whereas
  the PJM backcast keeper `2026-08-15-pjm-162-inputclock` solves with `energy_reserve_coopt +
  pjm_reserve_pergen + pjm_reserve_supply_cap` ON. The hindcast harness's stated footing for PJM
  is "the capacity-market footing (no ORDC overlay …)" (`run_capacity_hindcast.py::build_config`)
  — so there is no reserve dual in the T1-H price for the screen to miss. pjm-164's "the channel
  is REAL" is a statement about the **keeper**, and it is measured in §2a.
- **Structurally cannot:** uplift, reactive, regulation, black start (1.3) — none is an LP
  settlement in this model, and only reactive has a tariff form that regenerates forward (§2b).

### 1.5 A disclosure: the model's CT E&AS in solved years is near the record for the wrong reason

On the ACTUAL RTO RT LMP (`actual_lmp_hourly_PJM.parquet`) a CT at mc $50/MWh has a pro-forma
`Σ max(0, λ − mc)` of **39.3 / 205.3 / 12.2 / 24.2 / 67.4** $/kW-yr (2021–2025); on the keeper's
price (co-opt armed) the zone-median is **0.3 / 5.9 / 17.2** (2023–2025); the T1-H's 2021 price
never exceeds $52.77 in any zone. The model's tail is 3–6× too thin (pjm-138 D4; keeper hours
> $200: 4 / 10 / 32 vs 6 / 18 / 59). Yet the realized existing-CT median is only 2.2 / 18.3 / 5.0 /
8.2, far below the actual-LMP pro-forma, because real CTs capture a fraction of the price-duration
integral (starts, min-run, availability, DA scheduling). Two errors offset: the screen's
pro-forma optimism and the price's thin tail. That is stated, not corrected — the pro-forma is the
spec's construction (§5.2, the SOM new-entrant method) and the tail is the C3c program's object.

---

## 2. The home of the operand, adjudicated (rule 19 — one mechanism per phenomenon)

### 2a. The reserve co-opt channel — REAL, ARMED IN THE KEEPER, AND NOT THE HOME

Sized without a solve from the keeper's committed `reserve_family_<year>.parquet` (P1 families
`pjm_primary` + `pjm_primary_mad`, requirement 3.3–3.6 GW RTO / 2.7–2.8 GW MAD, held ≡
requirement, zero shortfall hours):

| year | binding hours (primary / MAD) | max dual $/MWh | **Σ dual, $/MW-yr held all year** (primary / MAD) | published SR+NSR credits $M | published SR requirement MW |
|---|---:|---:|---:|---:|---:|
| 2023 | 0 / 0 | 0 | **0 / 0** | 82.0 | 2,133 |
| 2024 | 2 / 2 | 8.5 | **9 / 10** | 84.3 | 2,346 |
| 2025 | 20 / 29 | 187.9 | **1,361 / 811** | (2025 report not yet published) | 2,295 |

The upper bound the ERCOT construction would credit a CT (`realized_thermal_as_revenue_per_mw_yr_
by_fuel`: headroom × binding dual, an UPPER bound per its docstring) is therefore **$0 / $0.01 /
$1.4 per kW-yr** — against D57's 3.8–18. The reason is measured and disclosed, not open: "the
model's reserve supply is 5–10× the requirement … the LP-vs-MIP boundary: with a continuous
commitment variable, fractional online capacity is free, so every idle unit's headroom is
synchronized-reserve-eligible" (pjm-138 D5b: "a disclosed architectural limit, not a calibration
gap"); pjm-164 §5.2: the channel "under-fires reality ~10×" and misses the winter face. And the
record itself caps what a faithful channel could pay a CT class: $82–85 M/yr of SR+NSR credits
spread over a ≥ 60 GW eligible fleet is ≈ $1.5/kW-yr, an order of magnitude under the 2022/23–
2023/24 gaps. **Verdict: the reserve co-opt is a real PJM mechanism the model carries in the
keeper, and it is not where the missing offer margin lives.** What DOES follow from §1.4(iii) is a
rule-1 consistency question the director should hold as its own card: the PJM forecast/hindcast
recipe prices energy WITHOUT the calibrated keeper's reserve co-opt (matrix `energy_reserve_coopt`
PJM backcast **K**, no `fc` stamp). Arming it is a structural-fidelity change to price formation,
with a stated cost — the per-generator co-opt is the "documented 15 GB memory tier" (spec.py
docstring) and the four-year T1-H already peaks at 9.1–9.3 GB on a 15 GB box (D57 §1) — and, on
this evidence, an expected E&AS effect of ≤ $1.4/kW-yr. It is not the D62 build.

### 2b. The non-market streams — rule 13 test applied stream by stream

| stream | forward form exists? | rule 13 | disposition |
|---|---|---|---|
| **Reactive** (Schedule 2) | yes — a FERC-approved per-unit revenue requirement; PJM's own capacity demand-curve E&AS offset carries it as a published per-MW-yr constant ($2,199/MW-yr in the 2024 record) that regenerates with every Net CONE filing | **PASS** — a tariff quantity, produced for 2035 from the then-current filing, responsive to nothing but the tariff (which is what it is) | admissible as the ONE out-of-market leg of the screen's margin; ~$2.2/kW-yr on every thermal class; moves the ratio 1.52 → 1.39, 2.43 → 2.23 (S1), no unit crosses the bar |
| **Uplift** (operating-reserve credits) | as a HISTORY, no — a class average of a settled outcome | **FAIL** as history | refused as an input. The only admissible form would be the model's OWN make-whole — the P1 startup-markup shortfall the LP's linear price leaves unrecovered, computed per unit from the model's own commitment pattern — which is not built and not chartered here. Even the observable class bound (CT 3.6–7.6, steam 5.5–24.8 $/kW-yr) is mis-allocated by a class average: the median frame CT earned $2.2 total in 2021, and S7 (bars + reactive + uplift bound) OVER-shoots 2022/23 to 0.67×. |
| **Regulation** | no class form: a 525–800 MW product cleared by whoever is cheapest (batteries, hydro, CCs) | **FAIL** for a class credit | refused; not an LP product in this model |
| **Black start** (Schedule 6A) | per-unit formula rate on a confidential roster | FAIL as a class average; per-unit not intakeable | refused |

### 2c. The three-year E&AS offset (design §4.8) — what it changes, and why it is not the operand

PJM's cap uses "the rolling simple average of such net revenues from the three most recent whole
calendar years" (Att DD §6.8(d)): the 2022/23 and 2023/24 BRAs (Jan 2022, Dec 2022) both read
2019–2021; 2024/25 (Jul 2023) reads 2020–2022; 2025/26 (Jul 2024) reads 2021–2023. Two facts:
(i) the model's 2021-only basis for the first two DYs is INSIDE the market's own window, so the
one-year form is not what puts those offers at zero; (ii) the 2022 dispatch year — the one year
in the record with high existing-CT E&AS (18.3) — can never enter a hindcast window, because it is
the rule-22 bridge; a three-year form would average it out even if it could. Re-clearing with the
SOM medians on the market's own information set (S3c) is **identical** to the dispatch-year form
(S3b) everywhere the tables reach. The horizon changes the information set, never the level, and
D54 §4.8's identity argument (one operand for offer and exit) stands. Not the operand.

### 2d. The arithmetic — what each object does INSIDE the D57 clearing, no coefficient (`reclear-2026-09-05.json`; the code's own clearing on the committed stacks; S0 reproduces the ledgers to the cent)

| scenario (what changes, and its provenance) | 22/23 ratio · Δpos | 23/24 | 24/25 | 25/26 | uncleared firm, 22/23 |
|---|---|---|---|---|---|
| **S0** committed arm A | 1.52× · −0.48 | 2.43× · −0.98 | 5.73× · −2.79 | cap · −3.88 | coal 5.4 · CC 2.1 · **ST 8.8** (oil marginal) |
| S1 + reactive $2.2/kW-yr (tariff; PASS) | 1.39 · −0.31 | 2.23 · −0.82 | 5.51 · −2.64 | cap | same |
| S2 S1 + uplift class bound (observable, NOT an input) | 1.37 · −0.29 | 2.21 · −0.80 | 5.42 · −2.59 | cap | same |
| **S3a** E&AS := SOM class medians, model bars | **1.86** · −0.91 | **2.73** · −1.23 | **6.84** · −3.50 | cap | ST 8.8 only |
| S4 coal bar at the published default ($80/MW-day = 29.2 $/kW-yr), else model | 1.36 · −0.27 | 1.99 · −0.62 | 5.04 · −2.34 (all clear) | cap | coal 0.1 · CC 2.1 · ST 8.8 · oil 3.7 |
| **S6** every bar := PJM's published default gross ACR (CT 18.25, CC 20.4, coal 29.2, steam/oil 23.4†, nuclear 162) | **1.06 · +0.10** | **1.56 · −0.27** | 5.04 · −2.34 | cap | coal 0.2 · CC 2.1 · ST 8.8 · oil 3.7 |
| **S3b** S6 bars + SOM E&AS medians | **0.87 · +0.34** | **1.28 · −0.04** | 5.04 · −2.34 | cap | ST 8.8 only |
| S7 S6 + reactive + uplift bound | 0.67 · +0.60 | 0.98 · +0.20 | 5.04 | cap | as S6 |

† Manual 18 publishes no steam oil & gas default through 2025/26 ("n/a"); the 2026/27 column
($64/MW-day) is the only published value and is used here as the observable bound, flagged.

**Reading, in the order of magnitude:**

1. **2024/25 and 2025/26 are not offer-side years.** Under every scenario that lowers coal's bar
   the 2024/25 clearing reads `all_offers_clear_curve_sets_price` at **$145.68 = the curve at the
   model's own census position 1.0321**, against the published cleared 1.0555: **2.34 pt × R
   166,810 = 3.9 GW** of accredited supply the model does not count (or requirement it
   overstates); 2025/26 likewise, 3.88 pt = 5.8 GW. D57's headline "5.7×" is therefore a
   QUANTITY artifact — the D48 §3.3 / D57 §3.2 reconstruction-limit object and D52's — and no
   E&AS operand of any size can touch it. This is the lane's most consequential finding.
2. **In 2022/23–2023/24 the object is the BAR.** The published default gross ACR alone puts the
   position within +0.10 / −0.27 pt and the price at 1.06× / 1.56×; the model's ATB bars are
   1.15× (CT), 1.5× (CC), 1.5× (steam, vs the 2026/27 column), 2.0× (coal) the numbers the
   market caps offers with, and 61–74 % of resources elected exactly that default cap in these
   BRAs (SOM Table 5-14/5-16). This is not a fitted level: it is the operand D54 §3.1 substituted
   an ATB proxy for and flagged in §6 item 2 — the mechanism's own published input (rule 14:
   measured over estimate; rule 25: PJM's own).
3. **E&AS at its measured magnitude is second-order and, at the model's bars, moves the price UP**
   (S3a): the record's coal and CC margins are lower than the model's, so a faithful E&AS makes
   the model's coal cohort dearer, not cheaper. The zero-E&AS CT/ST/oil plateau is real, and the
   record's own CT/steam E&AS would not have moved them to the published price from the model's
   bars either (§1.2). D57's "≥ 3.8 / 18.0 / 8.6" was the arithmetic of the wrong operand.
4. **The gas-steam over-exit is closed by nothing on this table.** 8.8 GW of steam is uncleared in
   every scenario, S3b included, because the real steam fleet cleared while earning $0 E&AS and
   recovering 0 % of avoidable cost (Tables 7-40/7-41) — it offered BELOW its cap, as regulated and
   self-supplied portfolios do. D54 §2 item 4 licensed "cap AS offer" as an upper bound;
   for steam the bound is loose. This is an offer-convention object for a successor of D54, not a
   revenue stream, and the D62 pre-declaration must state that steam stays over-exited.
5. **Composition under S6 (the D62 expectation):** coal uncleared 5.4 → 0.2 GW — BELOW the
   record's 6.5 GW UCAP, because the model's 2021 coal E&AS (55) is twice the record's (27); with
   the record's E&AS restored (S3b) coal's plateau sits AT the clearing price; CC 2.1 unchanged; oil 3.7 uncleared at the
   published-bar plateau (real diesel median E&AS 10.6 — S3b clears it); steam unchanged. On the
   EXIT side the halved coal bar (58.5 → 29.2) sits BELOW the model's 2021 coal E&AS (55) and
   ABOVE its 2023-dispatch E&AS (16.1 p50): the 2024 screen would then fail most of the coal fleet
   the 2021 prices kept — the record's coal recovered (7) % of avoidable cost in 2023 and 10.3 GW
   of PJM coal did exit in the window. Sign: economic coal exits UP from D57's 0.44 GW, gas-steam
   unchanged, the +4 GW 2023 CC entry weakened by the lower clearing price.

---

## 3. Rule 13 / 14 / 21 discipline, stated

- **Every candidate stream in §1–§2 is a published market-design or tariff quantity or an LP dual**:
  the energy dual and reserve duals (the model's own), the Manual 18 default gross ACR (the cap's
  published operand, intaken with source page), the E&AS-offset reactive component (PJM's own
  filing input), the SR/NSR/regulation/black-start settlements and uplift (SOM, DataMiner2). None
  was identified from the price residual; the residual is reported at full magnitude on every row
  of §2d, including the rows where the observable bounds over-shoot (S3b 0.87×, S7 0.67×).
- **What is REFUSED, by name:** any per-class E&AS uplift, adder, or "scarcity credit" sized to
  the D57 gap — D57 §4's "≥ 3.8 / 18.0 / 8.6" is a measurement, never an input; any historical
  uplift, regulation or black-start average (rule 13 FAIL); the ORDC overlay as a PJM screen
  signal (matrix G — a rule-19 stack on the armed co-opt); a "three-year" horizon adopted because
  it tempers a wave (§2c).
- **The falsifier for D62.** (i) A mechanism that lands the published price only via a fitted
  scalar is refused. (ii) The published-bar lever is admissible ONLY as the tariff's own number
  with its vintage rule fixed BEFORE the solve (the 2022/23-$ column through DY 2025/26; the
  2026/27-$ column after; steam's absence through 2025/26 handled by a stated rule, not a chosen
  number) — a lane that selects a column, an escalation, or a UCAP/nameplate convention by the
  residual has crossed into rule 21 territory and stops. (iii) A faithful operand that OVER-shoots
  (ratio < 1, as S3b's 0.87× in 2022/23) is a finding about the record's offer conduct, not a
  failure and not a reason to shade the bar back up. (iv) The 2024/25 ratio must NOT move under
  D62 — every offer clears there; if it moves, something other than the chartered mechanism
  moved (STOP).
- **Rule 22.** Nothing out-of-training was solved or scored; 2022 is discussed only as the bridge
  the hindcast harness already declares, and the SOM's 2022 rows are validation observables read
  beside a year the model never prices.

---

## 4. The build charter — for the director to issue as D62

**Mechanism (one object, two seams):** *PJM's published default gross ACR as the going-forward
bar of the retirement screen AND the sell-offer cap*, plus the tariff's reactive component as the
one out-of-market leg of the screen's margin.

- **Field(s):** one per-ISO gate in the `{iso: bool}` form the clearing half uses, default
  `None`, PJM armed via `iso_configs._pjm_config.default_scenario_overrides` only after the A/B
  (the D57 §8.1 pattern; every other ISO and every backcast keeper byte-identical — the screen
  never runs in backcast). No scalar field. The published values are DATA, not config: they
  already live in `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv` (Manual 18 Rev 62
  §5.4.8.4(B), two vintage columns); the reactive component is a one-row intake of the same
  data type (source: the PJM E&AS-offset / Net CONE filing the SOM cites, $/MW-yr per DY).
- **Seam 1 — the bar** (`retirements.py::apply_economic_retirements`, the line
  `going_forward_cost = getattr(config, fom_field) × multiplier × pmax × 1000`): resolve per
  ISO through a `resolve_going_forward_bar(iso, fuel, year)` that returns the published class
  value on nameplate (converted $/MW-day × 365 → $/kW-yr) when the gate is on, else the ATB path
  unchanged. Because the clearing's `offer_g = max(0, GFC_g − EAS_g)/(A_g × 365)` reads the SAME
  `going_forward_cost`, the offer and the exit decision stay one object (design §3.5 identity;
  rule 19). The coal `retirement_fom_multiplier_coal` does not apply under the published bar
  (the published number is already the avoidable cost "assuming the unit would otherwise
  retire", §5.4.4) — stated, not tuned.
- **Seam 2 — reactive** enters `net_revenue` BEFORE the capacity leg (inside the design's
  `EAS_g`), once, as `pmax × reactive_per_mw_yr` for every thermal unit — so the offer inherits it
  exactly as the screen does. It is the sole out-of-market credit (rule 19); no uplift, no AS
  annual rate.
- **Vintage rule (fixed before the solve):** DY ≤ 2025/26 reads the "through 2025/26" column
  (2022/23 $, nameplate); DY ≥ 2026/27 the second column; classes with "n/a" in the first column
  (steam oil & gas) read the first published value with the fact recorded in the ledger row —
  the lane may NOT pick between columns by result. UCAP conversion is the D48 seam's, untouched.
- **Data intake:** `pjm.csv` is in place; add the reactive component row(s) with source doc and
  page; extend the `capacity_market/avoidable-cost-rate` schema if a `cost_component =
  reactive_offset` value is new to it (`data-intake` skill, tmp-CLEAN_DIR test).
- **A/B (rule 29 form 4, no control solve):** control = the committed `pjm-t1h` bundle
  (`f0e050e820c1159a`, the D57 arm A) after a G-DRIFT audit of `git diff f0e050e…HEAD` on the
  solve path (D58 / D60 hunks must be classified INERT for this ISO or the control is re-solved).
  **Phase 0 (zero LP):** reproduce S0 and S6 of `reclear-2026-09-05.py` through the CODE path
  (the new resolver feeding `clear_capacity_supply_stack`) to 0.000 $/MW-day and 0.000 pt; STOP
  otherwise. **Screen year:** the 2022 screen (DY 2022/23) — the year the bar's footprint is
  largest (every CT/ST/oil offer sits on the bar plateau, coal's 2.0× gap is widest), named here
  before any solve; then the full T1-H window as one bundle.
- **Pre-declared signs per DY** (from §2d, S6 → S3b brackets): 2022/23 price ratio 1.52 → **≈
  1.06 (0.87–1.06)**, position −0.48 → +0.1 to +0.3 pt, coal uncleared 5.4 → ≤ 0.2 GW, steam 8.8
  GW UNCHANGED, oil 3.7 GW uncleared unless reactive+energy clear it; 2023/24 2.43 → **≈ 1.56
  (1.28–1.56)**, position −0.98 → −0.3 to 0; 2024/25 **5.73 → 5.04 and then FROZEN** (all offers
  clear; the residual is the census object, §2d item 1); 2025/26 unchanged (cap). FC-3:
  economic coal exits UP from 0.44 GW (the 2023-dispatch coal E&AS 16 sits under the 29.2 bar),
  gas-steam 9.5 GW unchanged, gas-CC 2023 entry reduced from +4 GW as the clearing price falls,
  `retire.total_gw` direction UP toward 15.06 actual with recall likely improving on the coal
  rows; the determination is expected to stay HOLD until the census and the steam convention
  land. Every miss reported at full magnitude.
- **STOPs:** Phase 0 mismatch; bare `pjm-t1h` key moved; any other ISO's key moved; a
  residual-selected column or convention (rule 21); 2024/25 price moving; the arm landing the
  price through any scalar not in `pjm.csv`; wall/RSS beyond the D57 envelope (14 min / 9.3 GB)
  without the co-opt.
- **Three SEPARATE cards, not D62's:** (a) the 2024/25–2025/26 supply census (3.9 / 5.8 GW below
  the published cleared position — D48 §3.3 / D52 object; the only lever for those years);
  (b) arming the keeper's reserve co-opt in the PJM forecast recipe (rule-1 price-formation
  consistency; cost = the 15 GB tier; E&AS effect ≤ $1.4/kW-yr on this evidence; never a
  price-landing device); (c) the below-cap offer convention for regulated / self-supplied
  steam (D54's successor; the steam over-exit's actual object).

**If the director prefers the narrow reading of D57's successor** — "add the missing CT/ST/oil
E&AS" — this finding's answer is that no admissible stream of the measured size exists to add
(§1.2, §2b), and that adding the measured ones at the model's bars moves the price the wrong way
(§2d S3a). The charter above is what the record supports.

---

## 5. Matrix (rule 28), records, collision

- **Lever-queue check (28a):** the PJM backcast queue is EMPTY and closed (pjm-153/155); this is
  a forecast-lane adjudication routed through the capx director's queue as D57 §4's successor.
  No cell adjudicated R/I/G is re-tested: `ordc_scarcity_overlay` PJM **G** and
  `reserve_deliverability_scoping` **I** are cited as adjudicated and left alone.
- **Cells (28b):** nothing tested — no probe, candidate or keeper — so no cell moves.
  `capacity_market_supply_clearing` PJM stays `fc: K` on the D57 ruling; `energy_reserve_coopt`
  PJM stays backcast K with no forecast stamp (the §2a card names the gap).
- **New mechanism (28c):** none added; D62 adds its row and six cells in its own build PR.
- **Records:** this finding; `docs/handoffs/d61/` (three instruments, their JSON outputs, the SOM
  source/sha record). No bundle, no registry, no board row, no keeper, no marker, no shard.
- **Collision:** docs only; D58 / D60 / T3-NYISO are solve lanes on other surfaces; D62 will
  touch `retirements.py` beside D57's settlement hunk and D53's (if landed) — noted for its
  rebase.

## 6. Governance attestation

Rules 13 / 14: every published figure is an observable compared against, never an input; the
D57 gap and every scenario ratio are reported at full magnitude, over-shoots included. Rule 19:
one bar for offer and exit, one out-of-market leg, one reserve mechanism (the co-opt, not an
overlay). Rule 21: zero parameters proposed; the admissible lever is the tariff's own published
number with a pre-fixed vintage rule. Rule 22: no out-of-training solve or score. Rule 25: PJM's
own rules, record and data; no other ISO's shard or verdict touched. Rule 27: docs only; no
source file edited. Rule 28: nothing tested, no cell moved; the D62 row is the build PR's duty.

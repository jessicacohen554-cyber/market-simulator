# DESIGN READ — capx D82: the PJM CT plateau and the per-delivery-year zero-E&AS operand

**Lane:** capx D82 DESIGN READ (director r#57, owner ruling **Q59**, capx ledger §0bb.3(a)).
**Branch:** `claude/capx-d82-ct-plateau-design`, fresh off `origin/main` `db0c1d85`. **Model:** Fable.
**DATA PROFILE:** `pjm` (only committed artifacts were read; `data/raw` was not needed).
**Date:** 2026-09-07.

**THIS IS A READ. Nothing is solved, armed, built, or recommended.** No `src/market_sim/` file,
no `ScenarioConfig` field, no matrix cell, no ledger row moves. The one instrument this read adds,
`docs/handoffs/d82/phase0-reclear-2026-09-07.py` (+ `.json`), is a zero-LP re-clear of the
REGISTERED `pjm-t1h` stacks through the code's own `clear_capacity_supply_stack` — the D57 / D61 /
pjm-eas form — and reads nothing but committed ledgers. Every number below is cited to a committed
artifact by section; every claim that could not be established is in §6.

---

## 0. The answer, question 3 first (the charter asks for it first at the close; it is put first here too)

**Q3 — no admissible operand of the size D57 measured exists, and the constructions that would
supply that size are backcast-only overlays. That closes D82 as an E&AS lane.** Stream by stream
(§3): the SOM class medians, the actual-LMP pro-forma, historical uplift, regulation and black
start all FAIL rule 13 `[R-MEASURED]`'s forward test — none regenerates for a forward year from
forward drivers (`FINDING-capx-d61` §2b; re-tested here, §3.1). The streams that PASS are three,
and each is measured, small, or refuted: the tariff reactive component ($2.2/kW-yr, built as
D62 seam 2, unarmed); the reserve co-optimization (forward-admissible, PJM's own keeper mechanism,
**screened and REFUTED** for this object on 2026-09-07 — `FINDING-pjm-eas-screen` §0–§2: 0.15 % of
the required magnitude, wrong sign, the PJM `energy_reserve_coopt` cell now `fc: "R"`); and the
model's own make-whole for its P1 commitment shortfall (admissible in form, unbuilt, unchartered,
bounded by the record at $3.6–7.6/kW-yr class-average and known to be mis-allocated by a class
average, D61 §2b). The record itself caps what a faithful operand could be: the SOM's existing
frame-CT median E&AS was **$2.2/kW-yr in 2021**, the one dispatch year both barred delivery years
price on (D61 §1.2, §2c); oil/gas steam **$0** in every year. **The model's zero is therefore within
~$2/kW-yr of the record for CTs and exact for steam and oil.** A forward-admissible repair moves the
plateau by the record's $2–7, not by the $3.8–18 D57 §4 arithmetic asked for — and D61 §2d S3a
already showed that the record's own E&AS at the model's bars moves the price the WRONG way.

**What the read establishes about the plateau itself (Q1–Q2, §1–§2).** The zero is exact and it is a
**construction** property of the T1-H price surface, not a data gap: an LP energy dual can never
exceed the marginal cost of the most expensive unit online, the registered `pjm-t1h`'s 2021 surface
peaks at **$52.7715/MWh in every zone** (below the CT/ST/oil marginal costs), and the PJM T1-H recipe
carries none of the three things that lift the calibrated backcast keeper's surface to a **$213.46
max** — the reserve co-opt (measured inert for this object), the `offer_curve_by_group` band
multipliers (the keeper's CC `peak` band is 5.0×; the hindcast's table is `{}`), or an ORDC overlay
(`G` for PJM). **The plateau's CONSEQUENCE is posture-dependent and is not present at HEAD.** In the
registered `pjm-t1h` (`fb16fda2ddb0a94a`, D67 published requirement + Q55 + Q56, ATB bars) the CT
plateau sits at 56.41–61.21 $/MW-day and **clears in full** in every delivery year (2022/23 price
90.41; 2023/24 86.52), CT exits are 0.000 GW, and it re-fills nothing (§1.2). The 24.2 GW uncleared
plateau D74 measured exists only under the JOINT unarmed D62 + D74 posture; re-cleared on HEAD's
committed stack at HEAD's armed requirement it is **7.0 GW of a 22.7 GW plateau**, not 24.2 (§1.4).
And because the plateau is the marginal class there, its exposure is a **knife edge on an exact
zero**: any positive CT operand — the record's $2.2 included — clears the whole class (§1.4).

**Q4 (§4):** the E&AS operand has one producer and a closed consumer set through one seam; if it
stopped being zero, what moves is the offer, the clearing price, the cleared set, the settled bar
test, the pipeline, the executed exits and every FC-3 band, the next year's census (and through it
DY 2024/25–2025/26), and — through `ClearedCapacityPrice` — thermal entry and storage entry. **Q5
(§5):** a zero-LP phase 0 exists and is already validated three times over; its gate is stated.

**§6 is not empty.** It carries a false-positive class in D78-R3's own structural corroboration, an
unmeasured axis (the offer bands) that this read could not difference at zero LP, the uncleared-≠-exit
convention that is the actual mechanism behind D74's 6.9 GW, and a published coincidence the read
cannot adjudicate.

---

## 1. Q1 — what the plateau is, mechanically

### 1.1 The object, read off the registered bundle (HEAD posture)

`results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/PJM/fb16fda2ddb0a94a/evolution_<y>.json`,
`capacity_clearing.offer_stack` rows `[unit_id, fuel, offer $/MW-day, accredited MW, cleared]`.
E&AS per unit recovered as D61 §1.1 does, `EAS = bar − offer × 365 × af / 1000` ($/kW-yr nameplate),
with `af` the UCAP class fraction the at-bar offers imply (`21000/365/61.2066 = 0.9400`; gas_st 0.93,
oil 0.90 — the same table D61 used) and the ATB bars the ledger rows record (`going_forward_bar_per_kw_yr`
35.0 gas_st / 30.0 gas_cc; 21.0 CT, 25.0 oil per D61 §1.1). Instrument output: `d82/phase0-reclear-2026-09-07.json`.

| screen → DY (dispatch yr) | class | units / firm MW | at EXACTLY zero E&AS | E&AS max · MW-wtd $/kW-yr | offer range $/MW-day (distinct) | clearing price | cleared? |
|---|---|---:|---:|---|---|---:|---|
| 2022 → 22/23 (2021) | gas_ct | 404 / 24,243.6 | **330 / 22,727.7** | 1.65 · 0.04 | 56.4069 – **61.2066** (12) | 90.4111 | **all** |
| | gas_st | 118 / 9,536.6 | 76 / 3,218.5 | 0.02 · 0.01 | 103.0421 – 103.1080 (3) | | **none** |
| | oil | 421 / 3,722.9 | **421 / 3,722.9** | 0.00 · 0.00 | 76.1035 (1) | | all |
| 2023 → 23/24 (2021) | gas_ct | 403 / 24,242.6 | 330 / 22,727.7 | 1.65 · 0.04 | 56.4069 – 61.2066 (12) | 86.5177 | all |
| | gas_st | 12 / 717.2 | 8 / 246.8 | 0.02 · 0.01 | 103.0463 – 103.1080 (2) | | none |
| 2024 → 24/25 (2023) | gas_ct | 404 / 24,243.6 | **0** | 10.50 · 4.10 | 30.5931 – 55.5070 (72) | 165.9689 | all |
| | gas_st | 12 / 717.2 | 0 | 5.24 · 4.38 | 87.6784 – 95.1807 (3) | | all |
| | oil | 8 / 3,722.8 | **8 / 3,722.8** | 0.00 | 76.1035 (1) | | all |
| 2025 → 25/26 (2024) | gas_ct | 404 / 15,474.7 (ELCC) | 6 / 9.5 | 15.85 · 3.50 | 18.3479 – 74.7505 (72) | 213.0564 (all clear) | all |
| | oil | 8 / 3,764.2 | 8 / 3,764.2 | 0.00 | 75.2672 (1) | | all |

This reproduces D78-R3 §3's per-DY set on the registered bundle rather than on its deleted control:
{gas_ct, gas_st, oil} at (or within $0.02/kW-yr of) zero in DY 2022/23; {gas_ct, gas_st} in 2023/24;
{oil} alone in 2024/25 and 2025/26 (where DY 2025/26 was NOT EVALUABLE from D57's table — here it is
readable and reads `oil` only). The `12 → 72` distinct-offer fan-out D78-R3 §4.2 reported is confirmed,
and its composition is now explicit: the 12 values in the barred DYs are **one** at-bar value (330
units at 61.2066, E&AS exactly 0) plus **eleven** small-positive values shared within plants (E&AS
≤ $1.65/kW-yr), i.e. the 74 CTs the pjm-eas screen also found moving (`FINDING-pjm-eas-screen` §2,
gas_ct n = 74).

### 1.2 What the plateau does at HEAD: nothing

At HEAD the CT plateau sits **below** the clearing price in both barred DYs (61.21 vs 90.41 / 86.52)
and clears to the MW. The 2022 uncleared set is coal 1,172.1 + gas_st 9,536.6 MW; 2023's is coal
2,076.2 + gas_st 717.2 + gas_cc 61.4; 2024's coal 5,878.4; 2025 clears everything (`capacity_clearing.
uncleared_mw_by_fuel`, all four years). No CT row appears in any `pipeline_events` block of the registered
bundle; `retirements` carry `gas_ct` 0.000 GW (`FINDING-capx-d78arm` §4: "gas_ct 0.000 and oil 0.051
unchanged"). **The object the charter names — "the cap's re-fill pool" — has no re-fill at HEAD** because
the admission cap's candidate pool is the uncleared set (D57 §3.4) and the plateau is not in it.

### 1.3 The three candidate causes, distinguished

| cause | test | reading |
|---|---|---|
| **(i) E&AS genuinely ≈ zero in these years** | the record: SOM existing-unit median energy+AS net revenue, D61 §1.2 (Tables 7-36/7-40) | **TRUE for steam and oil, NEAR-TRUE for CTs.** Frame CT **$2.2/kW-yr in 2021**, aero 6.9; oil/gas steam **(0.8) / 0 / 0 / 0.3**; and the two barred BRAs (2022/23, 2023/24) both read the 2019–2021 window (D61 §2c). The model's CT zero is within $2.2 of the record's median in the one dispatch year it prices on; steam/oil are exact. Not a defect. |
| **(ii) the hindcast price series cannot express scarcity revenue** | the surface: `screen_price_max_usd_mwh` **52.7715** in every PE row of 2022 and 2023, mean 36.9592 (`evolution_2022/2023.json`; pjm-eas PRECOMMIT §1A); the keeper's 2021 P1 surface **max 213.46, p99 91.67** (`pjm169_tp2022_2021_f2arm/hourly/system_2021.parquet`, pjm-eas PRECOMMIT §1A); the actual RT LMP pro-forma for a $50 CT **$39.3/kW-yr in 2021** (D61 §1.5) | **TRUE, and it is a construction property (§2), not data.** But it is only *half* a defect: D61 §1.5 measured that real CTs capture a fraction of the price-duration integral (record $2.2 against the actual-LMP pro-forma $39.3), so the thin tail and the pro-forma's optimism offset. The tail is the C3c program's object — a ledgered model-class limitation on the backcast keeper (rule 22 standing rule) — not an E&AS operand. |
| **(iii) the offer construction floors it** | the code: `retirements.py:2998` `offer = max(0, gfc − eas) / (a_mw × 365)`; `:3454–3459` `net_revenue = Σ max(0, price − mc, r) × cap` | **FALSE as a floor on E&AS.** The only floors are `max(0, ·)` per hour (a unit is never paid to run out of merit) and `max(0, ·)` on the offer (a unit covering its bar offers $0 — Manual 18's own rule, D54 §3.1). Neither creates the plateau; the plateau's VALUE is the bar (`GFC/(A×365)`, class-uniform because the bar is per class, D78-R3 §4.3) and its WIDTH is the class's accredited MW. What the construction does do is make the plateau's exposure a **knife edge** (§1.4). |

**The one model defect among the three is (ii), and it is a price-formation recipe defect, not an
E&AS-operand defect** — established from the code path in §2. The reading the charter suggested might
be a defect, (iii), is not one.

### 1.4 Where the plateau IS consequential — the joint D62 + D74 posture — re-cleared at HEAD's requirement (zero LP)

D74 measured the 24,244 MW uncleared CT plateau under D62's published bar + its own convention at a
requirement of **146,816.5 MW** (D74 §4, HEAD-at-the-time = D67's peak × FPR). D67-ARM has since armed
PJM's **published** Reliability Requirement — the registered 2022 screen's `requirement_mw` is
**163,268.9** (`evolution_2022.json`; `capacity_adequacy_requirement_published_by_iso {PJM: True}` in
`run_config.json`) — so the crossing sits 16.4 GW further up the stack than when D74 ran. Re-expressing
HEAD's committed 2022 stack under the two unarmed postures (`d82/phase0-reclear-2026-09-07.py`; S0
reproduces the committed clearing to 0.0000 $/MW-day and 0.0000 pt in 2022–2024, 5.0e-4 in 2025 — the
ledger's own `round(o, 4)` serialization, pjm-eas PRECOMMIT §1B):

| 2022 screen → DY 2022/23 | S0 (HEAD, ATB bars) | S62 (published bars + reactive, D62 posture) | **S74 (S62 + steam/oil → Q_0, D74 posture)** | D74 §4 (its own HEAD, R 146,816.5) |
|---|---|---|---|---|
| price $/MW-day · ratio vs $50 | 90.4111 · 1.808 | 62.2774 · 1.246 | **46.7822 · 0.936** | 46.7823 · 0.936 (control-P) / 41.27 (arm) |
| cleared position · Δ vs 1.0510 | 1.0426 · −0.84 pt | 1.0497 · −0.13 | **1.0537 · +0.27** | 1.0537 / 1.0551 |
| marginal plateau (class · MW at price) | coal · 904 | **gas_st · 6,081** | **gas_ct · 22,727.7** | gas_ct / curve-between |
| CT plateau: cleared / uncleared MW | 24,243.6 / **0** | 24,243.6 / **0** | **15,707.5 / 7,020.2** | control-P 12,555 cleared; arm **24,244 uncleared** (D74 §4.2 G1) |
| uncleared total MW by class | coal 1,172 · gas_st 9,537 | coal 94 · gas_st 3,218 · oil 3,723 | coal 238 · gas_cc 2,145 · **gas_ct 7,020** | coal 238 · gas_cc 2,052 · gas_ct 24,244 |
| E&AS that puts the CT plateau AT the price, $/kW-yr | −10.02 (already clears) | −5.32 | **0.00 — it IS the price** | — |

Three readings. **(a)** The charter's object exists only when BOTH D62 and D74 are armed: under D62
alone the marginal class is the zero-E&AS gas-steam plateau (62.28–62.34) and every CT clears; D74's
move of steam/oil into `Q_0` is what drops the crossing onto the CT plateau. **(b)** At HEAD's armed
requirement the exposed part of the plateau is **7.0 GW, not 24.2** — D67's published requirement,
armed after D74 measured, absorbs 17 GW of it; the price and position are identical to D74's control-P
because the crossing lands on the same plateau and the VRR curve fixes the position at which it does.
**(c)** The plateau is exposed only because its operand is **exactly** zero: the CT's re-expressed offer
under the published bar + reactive is 46.7822 = the price, so ANY positive CT E&AS — $0.01, or the
record's $2.2 — puts the entire 22.7 GW plateau below the price and clears it, moving the marginal to
gas_cc (52.61) or coal. The 6.9 GW of CT exits D74 §5.2 reports is the consequence of an exact zero
that is itself an artifact (§2), delivered through a convention this read names in §6.3. In 2023/24
under S74 the CT plateau already clears in full (52.27 > 46.78; E&AS-to-price −1.88); in 2024/25 and
2025/26 every offer clears in every scenario, as D61 §2d item 1 said no offer-side operand could touch.

### 1.5 A correction to D78-R3's structural corroboration

D78-R3 §4.2 read gas_ct's identical barred range in DY 2022/23 and 2023/24 ("byte-identical … a class
whose offer reads no price vector") as arm-free evidence for the zero. **That signature is produced by
the bridge, not by the zero.** Both screens price on the 2021 dispatch (2022 is the rule-22 bridge;
D61 §1.1; the identical `screen_price_max 52.77 / mean 36.96` in both years' PE rows), so EVERY class
whose units survive to the 2023 screen carries an identical range — D78-R3 §4.2's own table shows coal
`0.0000 – 174.2108` and gas_cc `0.0000 – 86.5177` identical in both DYs, and neither is at bar. Confirmed
on the registered bundle (§1.1: coal 39 → 36 distinct on the same range; gas_cc 18 → 18 on `0 –
86.5177`). What DOES evidence the zero is the distinct-offer count (one at-bar value carrying 330 of 404
units) and the committed `energy_margin_usd == 0` rows. The declared set stands; this corroboration does
not, and a successor must not cite it.

---

## 2. Q2 — data gap or construction gap? Construction, established from the code path

The E&AS operand `EAS_g` is the pre-capacity `net_revenue` of `apply_economic_retirements`
(`retirements.py:3446–3692`): `energy_margin + reserve_uplift + attribute + §45U + reactive + AS credit`.
Each leg, for PJM in the T1-H recipe, read off code and the registered `run_config.json`:

| leg | producer (code) | PJM T1-H state | source |
|---|---|---|---|
| energy margin `Σ max(0, λ − mc) × cap` | `retirements.py:3452–3455` on `prior_results.prices` = `econ_prices` = `result.prices` (`runner.py:3860`) | live — and **λ_max = 52.7715** in every zone carrying a decided unit, below gas_st mc 51.2–58.2 (PE rows), CC 44.8–56.2, oil 187–248 (D57 arm-A 2022 PE rows) | `evolution_2022.json`; `…-d57-clearing/…/evolution_2022.json` |
| reserve uplift `max(·, r)` | `reserve_price_signal` built only under `iso == "ERCOT" and ercot_thermal_as_endogenous`, else from `overlay_adder` (`runner.py:4644–4672`) | **None**: `energy_reserve_coopt=False`, `ercot_thermal_as_endogenous=False`, `scarcity_price_overlay=False` ⇒ `overlay_adder=None` (`runner.py:3861–3866`); every PE row `reserve_uplift_usd 0.0`, `reserve_signal_mean 0.0` | `run_config.json`; PE rows |
| AS annual credit | `as_revenue_per_mw_yr` — no PJM entry; `thermal_as_revenue_per_mw_yr` ERCOT-only | **0.0**, `as_pricing: exogenous_flat` on every PE row | PE rows; D61 §1.4(ii) |
| reactive (D62 seam 2) | `retirements.py:3639–3644`, rides `capacity_going_forward_bar_published_by_iso` | **0.0** — the gate is `None` at HEAD (D62 `fc: "O"`, DO-NOT-ARM §8) | `run_config.json`; PJM shard |
| attribute / §45U | RPS/EAC/clean-tier duals; nuclear only | 0 for CT/ST/oil (not eligible) | code |
| offer bands on the LP bids | `offer_curve_by_group` | **`{}`** in the T1-H; the keeper carries `CC_REGULAR {committed 1.0, econ_low 0.96, econ_high 1.5, peak 5.0, …}` etc. | `run_config.json` of both bundles |

**Why λ_max is $52.77 and not $213.** In an LP with no reserve co-optimization, no scarcity adder and
marginal-cost bids, the energy-balance dual equals the marginal cost of the marginal unit, so the most
expensive unit online earns `Σ max(0, λ − mc) = 0` identically — the top of the stack is inframarginal
in no hour. That is the "exactly zero", and it is a construction of the PRICE SURFACE the screen reads,
not of the screen. The PJM backcast keeper (`2026-08-15-pjm-162-inputclock`; `pjm_debugb_inputclock_A/
run_config.json`) prices with all three of `energy_reserve_coopt`, `pjm_reserve_pergen`,
`pjm_reserve_supply_cap` True AND the registered `offer_curve_by_group` bands; the T1-H prices with none
of them. `run_capacity_hindcast.py::_build_config` states the harness "must exercise the capacity
screens under the same price formation the forecast uses for the ISO" and, for PJM, that the master
scarcity flag is "a harmless no-op … RPM net-CONE × UCAP already enters the screens via
`capacity_revenue_per_mw_yr`" (lines 745–761) — a rationale D57 voided by replacing that exogenous
payment with a clearing whose input IS the E&AS margin (pjm-eas §3, last bullet). So the gap is a
**recipe** gap: the forecast lane prices PJM on a surface the calibrated keeper does not use.

**Which half of the recipe carries the tail is now partly measured.** The reserve co-opt half was
screened on 2026-09-07 (`FINDING-pjm-eas-screen`, PRECOMMIT pushed before any LP): armed in the T1-H
it fires (366 of 1,399 offers move) and moves λ_max **52.7715 → 52.3638** (down), the operand
0.0416 → 0.0411 $/accredited MW-day, the uncleared set identical to the milli-MW — because 51.0 GW of
deliverable ramp clears a 2.6 GW requirement (19×) and no ORDC step ever fires. The PJM
`energy_reserve_coopt` forecast cell is **`R`** with a DO-NOT-REDO. That leaves the **offer bands** as
the unmeasured axis of the surface difference (§6.2). It is not a data gap: no measured input is
missing from the T1-H that the keeper has; the two runs differ in which registered mechanisms are ON.

---

## 3. Q3 — what a non-zero operand would be derived from, and rule 13's forward test

### 3.1 Every candidate stream, tested by name

| candidate operand for CT / ST / oil | derivable from | rule 13 forward test — "could it be produced for 2035 from forward drivers, and respond to changed conditions?" | size at PJM scale | disposition |
|---|---|---|---|---|
| **A. the energy dual's tail** — the LP's own λ under the keeper's price formation (bands and/or co-opt) | the model's own solve | **PASS in form** — it is the model's price, regenerates every year, responds to fleet/load/fuel | co-opt half: **≤ $0.0005/MW-day** on the operand (pjm-eas §1–§2, REFUTED); bands half: **UNMEASURED** (§6.2). The keeper's own 2023–2025 zone-median CT pro-forma is $0.3 / 5.9 / 17.2 (D61 §1.5) | co-opt: **R**, closed. Bands: a recipe-consistency question (which registered mechanisms the forecast lane carries), owner-facing, not an operand repair — and rule 1's carve-out licenses the bands as a backcast price-tuning channel under conditions (a)–(e); whether a band tuned on backcast price belongs in the forecast surface is exactly the question the FR-22 parity family exists for (§6.2) |
| B. the reserve co-optimization's duals | the model's own solve | PASS in form | $0 / $0.01 / $1.4 per kW-yr upper bound (D61 §2a); measured **inert** on the operand (pjm-eas) | **closed (R)** |
| C. reactive (Schedule 2) | tariff revenue requirement; PJM's E&AS-offset input $2,199/MW-yr (`pjm.csv` row 17) | **PASS** — a filed constant, regenerates with each Net CONE filing | $2.2/kW-yr on every thermal class | built (D62 seam 2), rides the unarmed D62 gate; already inside §1.4's S62/S74 |
| D. the model's OWN make-whole — the P1 bid-cost (startup-markup) shortfall the linear price leaves unrecovered, per unit, from the model's own commitment pattern | the P0→P1 seam (`pipeline/solve.py`), not built | PASS in form (a model construction that regenerates) | unknown; the record's CT uplift class-average is $3.6–7.6/kW-yr and D61 §2b shows a class average OVER-shoots (S7 0.67×) | **unbuilt, unchartered**; the only forward-admissible stream of possibly material size, and it is a P1 commitment object, not a capacity-screen object |
| E. SOM existing-unit E&AS medians (Tables 7-36/7-40) | published outcome history | **FAIL** — a settled outcome, no forward form | CT 2.2 / 18.3 / 5.0 / 8.2; steam 0 | **backcast-only overlay → refused** (D61 §3 "refused by name") |
| F. the actual RT LMP pro-forma (`actual_lmp_hourly_PJM.parquet`) as the screen's price | measured outcome | **FAIL** — the answer, not an input (rule 13's "pinning the backcast to actuals") | $39.3/kW-yr for a $50 CT in 2021 (D61 §1.5) — and 18× the record's realized median | **backcast-only overlay → refused** |
| G. historical uplift / regulation / black-start averages | SOM settlements | **FAIL** (D61 §2b, each by name) | CT uplift 3.6–7.6 | refused |
| H. the three-year E&AS offset horizon (Att DD §6.8(d)) | the model's own ledgers | PASS in form | changes the information set, never the level: 2021 is inside the market's own 2019–2021 window for both barred BRAs; 2022 can never enter (the bridge) | not an operand (D61 §2c; D54 §4.8) |
| I. the D57 §4 "≥ 3.8 / 18.0 / 8.6 $/kW-yr" | the price residual | **FAIL** — a fitted per-class adder, rule 1/13/21 | — | forbidden; a measurement, never an input (D61 §3) |

### 3.2 The verdict on question 3

The only constructions that would supply the D57-sized operand (E, F, I) are backcast-only overlays or
fitted adders, and rule 13 refuses them. The forward-admissible streams (A–D) are, respectively:
half-refuted and half-unmeasured as a recipe question (A), refuted (B), $2.2 and already built (C), and
unbuilt with a record bound of a few $/kW-yr (D). **Against that stands the record's own answer: the
real CT class earned ≈ $2.2/kW-yr in the dispatch year both barred DYs price on, and steam/oil earned
nothing.** A faithful operand is therefore a small positive number — which, under the one posture where
the plateau matters (§1.4), clears the whole plateau at any value above zero, and under HEAD's posture
changes nothing because the plateau already clears. **D82 is not an E&AS lane.** What the object
decomposes into is (i) the bar (D62, `O`, its own card), (ii) the recipe-consistency question on the
forecast price surface (A's bands half; §6.2), and (iii) the uncleared-≠-exit convention (§6.3). None of
those is chartered by this read; each is named so the desk can decide whether any is.

---

## 4. Q4 — the blast radius: every consumer of `EAS_g` (rule 19 enumeration, complete before anything moves)

One producer: the margin loop of `apply_economic_retirements` (`retirements.py:3388–3760`), one value per
screened thermal unit per screen year, `margins[(g, net_revenue, gfc)]` + `margin_detail`. Consumers,
in order along the data flow, with what moves if the operand stopped being zero for CT / ST / oil:

| # | consumer | where | what moves |
|---|---|---|---|
| 1 | the sell offer `max(0, GFC − EAS)/(A×365)` | `retirements.py:2998` | the CT / ST / oil offers fall by `ΔEAS×1000/(af×365)` $/MW-day; the plateau's shape (class-uniform) breaks into per-unit values |
| 2 | the clearing: price, `how`, marginal unit, cleared set, `Q_0` untouched | `:3003–3008` → `adequacy.clear_capacity_supply_stack` | at HEAD (posture S0): nothing for CT/oil (already cleared); gas_st needs ≥ +4.31 $/kW-yr to reach 90.41 (§1.4 table, S0 column) — the record says steam earned 0. Under S74: any ΔEAS > 0 clears the whole CT plateau and re-prices at the next class |
| 3 | the settled bar test `eas + pay` vs `gfc` (I2: failing set = uncleared set) | `:3012–3022`, `:3836–3841`, `:3899` | the failing set follows the uncleared set exactly (D57 §3.3, D78 §3) |
| 4 | the pipeline: `decided` / `entry_capped` / `re_confirmed` / `reversed`, worst-first depth ordering by `net_revenue − gfc`, the admission cap's budget, execution after the per-fuel lag (gas_ct **2** yr, `scenarios.py:4019`) | `_apply_pipeline_retirements`, `:2617–2884` | which units enter, in what order, and when they leave; D74 §4.3 is the worked example of a re-fill |
| 5 | executed exits → `retirements[reason=economic]` → FC-3 bands (`retire.total_gw`, by fuel, `unit_recall_gt300`, `false_retire`, LOYO folds, T-R10a/b) | `evolve.py:768`; `score_capacity_hindcast.py` | every retirement band (D74 §5.2 shows the magnitudes when the plateau IS exposed: gas_ct 0 → 6.888 GW, recall 11 → 8/20, precision 14.8 → 2.6 %) |
| 6 | the next year's fleet → the accredited census → later DYs' `Q_0 + Σ A_g`, `census_position`, and where the curve is read when every offer clears | D74 §5.1 (the census channel: 2024/25 270.99 → 82.69 through +6,050 MW of census) | DY 2024/25–2025/26 price and position, I7's short position, the BLK-10 backstop's trigger |
| 7 | `ClearedCapacityPrice` → thermal entry's capacity term (price taker) | `capacity_market.py:1133–1152`; `new_entry.py:1081` | entry economics: D57 §3.5 P10 (+4,000 MW CC at $28.7/kW-yr), D74 §5.3 (FC-2 `gas_cc` PASS → FAIL through 82.69) |
| 8 | the same seam → storage entry | `storage.py:1637` | storage RA value (0 GW built in every PJM leg to date; D57 §3.5) |
| 9 | the same seam → `plant_financials.py:537`, `runner.py:2241`, `adequacy.py:663` | reporting / census-path callers | ledgers only |
| 10 | diagnostics: `_screen_stack` log (`:3847–3861`), FFR-5A `margin_detail` fields (`energy_margin_usd`, `reserve_uplift_usd`, …), `entry_screen_diagnostics` | ledger rows | no decision effect (rule 24) |

**Not consumers** (stated so nothing is assumed): the LP itself (no within-year feedback, rule 10); any
backcast (the screen never runs — every keeper byte-identical under any operand change); any other ISO
(rule 25 — PJM's operand is read from PJM's surface); the reliability floor's merit key (reads the bar,
`_floor_retention_merit` `:2454–2506`, not `EAS`) — though the floor's candidate set is #3's failing set;
the CCS retrofit screen (`evolve.py:664`, its own margin); the D67 requirement, the D48/Q55 accreditation
and the D76 peak (all on the demand/accreditation side of the clearing, untouched by `EAS`).

**What "stopped being zero" would mean at HEAD versus under S74** is the load-bearing distinction: at
HEAD, rows 1–2 move for CT/oil and nothing downstream does (they already clear); under the joint
D62 + D74 posture, rows 1–8 all move, discontinuously, at the first positive value.

---

## 5. Q5 — the zero-LP phase 0

**One exists, it is validated, and it is already the family's convention.** Three committed instruments
re-clear a committed `offer_stack` through the code's own `clear_capacity_supply_stack` +
`capacity_supply_curve` at the committed `price_takers_mw` / `requirement_mw`:
`docs/handoffs/d57/phase0-reproduction-2026-09-05.py` (0.000 / 0.000 on 16 rows),
`d61/reclear-2026-09-05.py` (S0 to the cent), `pjmeas/phase0-eas-operand-2026-09-07.py` (≤ 5.0e-4
$/MW-day, position exact, on the registered bundle) — and this read's `d82/phase0-reclear-2026-09-07.py`
reproduces S0 to 0.0000 in 2022–2024 (§1.4). D74 §4.2 G1 closed the loop in the other direction: the
SOLVED arm landed on its own pre-solve re-clear to **0.0001 $/MW-day and 0.00000 pt**. So for any
candidate operand that can be expressed per unit on the committed stack, the arm's clearing in the screen
year is computable before the LP to four decimals, and a solve that misses it is a STOP.

**The phase-0 gate a successor lane would have to pass before any solve** (rule 29(0)):

1. **Admissibility first, by name.** The candidate operand is one of §3.1's PASS rows (A-bands, C, D) or
   a new stream tested the same way in the PRECOMMIT; an E / F / G / I stream does not reach step 2.
2. **Per-unit re-expression on the committed stack** at HEAD's `requirement_mw` / `price_takers_mw`, in
   the pre-registered posture (HEAD's S0 or a declared arm posture), reporting price, position, `how`,
   the marginal plateau split, and the uncleared set by class (this read's instrument form).
3. **Liveness STOP.** If no offer crosses the committed clearing price in the screen year — the operand
   moves rows 1–2 of §4 and nothing else — the arm is INERT and does not solve (rule 29's inert-year
   clause). At HEAD's posture this is the expected reading for CT and oil (§1.4, S0 column).
4. **The point prediction** for the screen-year clearing (price to 1e-4, position to 1e-5, the uncleared
   set by class) is written into the PRECOMMIT; the solve must land on it (D74 G1 form) or STOP.

**What phase 0 cannot compute, and why** — the operand's VALUE under a price-formation change (§3.1 A):
no committed artifact carries the T1-H's hourly price vector (the hindcast parquets are gitignored; D78-R3
§3.1 already recorded `max |delta|` as unrecoverable), so a bands-armed surface must be solved to be read.
What CAN be computed at zero LP for that axis is the contrast the pjm-eas phase-0 D built — the same
units' pro-forma on the committed backcast surface (`pjm169_tp2022_2021_f2arm/hourly/system_2021.parquet`,
bands + co-opt) versus the hindcast's committed row values — which bounds the bands half from above once
the co-opt's measured −0.41 $/MWh is netted out (§6.2).

---

## 6. What this read cannot answer, and the false positives it went looking for

### 6.1 The false-positive class in D78-R3's structural corroboration (found — §1.5)

Cross-DY offer invariance is produced by the bridge and is shared by every surviving class; it is not
evidence of the zero. D78-R3's DECLARED set is unaffected (it rests on D57 §4's rows and on the
distinct-offer count), but its §4.2 "barred years byte-identical, live years not" sentence is void and
must not be cited by a successor. A second, smaller one in this read's own derivation: "at exactly zero"
is measured through a class-uniform `af` and the ledger's 4-decimal offer; a unit with E&AS < ~$0.005/kW-yr
reads as zero. The 76 / 118 gas_st count is therefore a lower bound on "≤ $0.02", not a count of exact
zeros (D61's 115 / 115 was arm A's fleet, a different vintage).

### 6.2 The offer-band half of the surface difference — UNMEASURED, and this read could not difference it at zero LP

The keeper's `offer_curve_by_group` bands (CC `peak` 5.0×, `econ_high` 1.5×, …) versus the T1-H's `{}`
is the largest remaining candidate for the $52.77 → $213.46 tail gap now that the co-opt is eliminated
(pjm-eas §5 lists five axes: mode, `scarcity_pricing_enabled`, fleet basis, demand basis, offer curves).
This read cannot attribute the gap among the remaining four without a solve, and it does not claim the
bands are it. What it can say: (i) `scripts/lib/forecast_parity_registry.py` carries **no** entry for
`offer_curve_by_group`, and `iso_configs._pjm_config` carries no band override, so the forecast lane's
neutral bands are a **default by omission**, not an adjudicated posture — which is the FR-22 parity
family's question, not D82's; (ii) rule 1's amendment licenses the bands as a price-tuning channel for
the calibrated span with a year-invariance condition — whether a band identified on backcast price is a
forward driver under rule 13 is an owner question this read does not pre-empt; (iii) a bands-armed T1-H
would re-key every PJM forecast bundle. **A successor that wants this measured owes a zero-LP bound first**
(§5, last paragraph) and then a ONE-year screen (§7), never a five-year arm.

### 6.3 Uncleared ≠ exit: the convention that actually delivers D74's 6.9 GW

In the record, an existing resource that does not clear a BRA is not a retirement — PJM's 2022/23
uncleared gas was 6.2 GW UCAP (D74 §2(1) validation observable) against 0.808 GW of actual CT exits in
the whole window (D74 §5.2). In the model, an uncleared unit is a failing screen (I2), enters the pipeline,
and executes after its lag unless it re-clears — and a CT decided on the 2021 surface re-screens in 2023
on the SAME surface (the bridge), so it cannot re-clear. Under the joint D62 + D74 posture that path is the
whole mechanism of the CT over-exit, and it would fire on §1.4's 7.0 GW at HEAD's requirement too. This
read cannot say whether that is a defect of the pipeline rule, of the identity, or of the bridge
(rule 22's); it is a D54-family / retirement-rule question, and it is the second thing the desk would
have to decide before the plateau could matter again.

### 6.4 A published coincidence this read cannot adjudicate

The 2022/23 BRA's RTO Resource Clearing Price was **$50.00/MW-day** (D57 §3.1, published row) and PJM's
default gross ACR for Combustion Turbine through DY 2025/26 is **$50/MW-day** (`pjm.csv` row 6, Manual 18
§5.4.8.4(B)). If the real marginal offers were CTs at their default cap with a small E&AS offset, the
market's own plateau sat where the model's does under S74 — and then the model's CT plateau being
marginal in that DY would be structurally RIGHT, and only its exit consequence wrong (§6.3). The SOM does
not publish the marginal resource type (D74 §2(1): must-offer-at-zero by type is confidential), so this
cannot be established from the record in the repo. It is recorded because, if true, it inverts the
charter's framing of the plateau as a defect.

### 6.5 What the CT's own marginal cost is in the T1-H

No CT row appears in any committed PJM `pipeline_events` block (CTs never fail at HEAD or in arm A), so
`mc_mean_usd_mwh` for the CT class is not readable from a committed ledger; the "below the CT's marginal
cost" statement in §2 rests on the 330 units' exact-zero margin (which implies `mc ≥ 52.77` in every
available hour) and on the CC / ST / oil ranges that bracket it. The D74 / D78 / pjm-eas control bundles
that carried `entry_capped` CT rows were deleted under rule 29(c). A successor's PRECOMMIT should name
this as a structure to preserve before deletion (D78-R3 §8 item iii's doctrine).

### 6.6 The recipe-consistency card is not this read's to write

D61 §4(b) named "arming the keeper's reserve co-opt in the PJM forecast recipe" as a separate owner card
on rule-1 consistency grounds; pjm-eas §4 restated it after refuting the co-opt as an operand repair. This
read adds the bands to the same card's scope (§6.2) and takes no position on it.

---

## 7. THE SCREEN SPECIFICATION a successor lane would pre-register — conditional, and not a recommendation

This section exists because rule 29 requires a design read to say what a screen would have to measure; it
does not say a screen should run. It applies only if the owner opens a lane on one of §3.1's PASS streams.

**Object under test.** ONE declared operand change (a §3.1 PASS row) on ONE declared posture (HEAD's
registered `pjm-t1h` `fb16fda2ddb0a94a` — under rule 29(b) form 4 the committed bundle IS the control; a
G-DRIFT audit from `db0c1d85` classifies every later solve-path hunk INERT or the arm earns a control for
the screen year only).

**Phase 0 (zero LP, before any solve; §5 gate):** admissibility by name; per-unit re-expression on the
committed 2022 stack; the liveness STOP; the point prediction (price 1e-4, position 1e-5, uncleared set by
class, marginal plateau split); the DOF ledger (zero, or the stream's own identification source — never
the residual). If the operand is §3.1-A (bands), phase 0 additionally bounds it from above by the
backcast-surface contrast net of the co-opt's measured −0.41 $/MWh, and states which registered fields
would move which cache keys (every PJM forecast key moves; every backcast key must not).

**Screen year, named on FOOTPRINT, never residual: the 2022 screen (DY 2022/23).** It carries the largest
zero-E&AS set — 943 gated rows / gas_ct 404 + gas_st 118 + oil 421 units, 37.5 GW firm (D78-R3 §3.2;
§1.1) — and the only year in which all three classes are at bar. Not 2024/25, where the set is 8 oil rows.
(The same footprint argument D61 §4 and the pjm-eas PRECOMMIT used; the residual is largest in 2024/25
and that is precisely why 2024/25 is not the screen year.)

**Structural gates (STOP-only; none reads a band or a ratio against the published price):**
- **G1 arithmetic** — the solved 2022 clearing lands on phase 0's point prediction to 1e-4 $/MW-day and
  1e-5 pt (D74 G1 form); miss ⇒ STOP.
- **G2 footprint** — only the declared classes' offers move; `Q_0`, `requirement_mw`, `census_mw`,
  `screen_peak_demand_mw`, `entry_decided_mw_by_tech`, `renewable_additions`, `announced` rows identical
  to the control; any other move ⇒ STOP.
- **G3 direction and order of magnitude** — the operand moves in the pre-declared direction (E&AS UP,
  offers DOWN) by within a pre-declared band; the wrong sign, or 1 % of the declared magnitude (the
  pjm-eas reading), ⇒ STOP.
- **G4 identity** — I2 holds (failing set = uncleared set to the unit; both one-sided sets empty).
- **G5 no non-target load-bearing flip** — 14/14 forecast invariants; every additions band identical in
  the screen span.
- **G6 keys** — bare `pjm-t1h` unmoved unless the arm is a declared default flip; no backcast key moves;
  no other ISO's key moves.

**STOP conditions beyond the gates:** any per-class adder, haircut, coefficient or "scarcity credit" sized
to D57 §4's gap (rule 1/13/21); a stream from §3.1 rows E–I; a screen year chosen after seeing 2024/25; a
control solve spent without a LIVE hunk; the bundle surviving to `main` (rule 29(c)); wall/RSS beyond the
D57 envelope without the co-opt (14 min / 9.3 GB) or the documented 15 GB tier with it.

**What the screen may not do:** promote (rule 29: a screen may kill an arm, never promote one); read
`retire.total_gw`, recall or `false_retire` as a gate in either direction; re-test `energy_reserve_coopt`
(`R`, DO-NOT-REDO) or `ordc_scarcity_overlay` (`G`) without new evidence.

---

## 8. Governance attestation and records

**Rule 1 `[R-STRUCT]`** — every reading is a structural or code-path fact; the one improvement any posture
shows against the published price (S74's 0.936×) is reported and argued from nowhere. **Rule 13 / 14** —
every published figure (RCP, cleared position, SOM medians, `pjm.csv`) is a validation observable or a
tariff input; nothing entered anything. **Rule 19** — the operand's producer and every consumer are
enumerated (§4). **Rule 21** — zero DOF proposed; no number in this document is a parameter. **Rule 22** —
no solve; 2022 discussed only as the bridge the harness declares. **Rule 25** — PJM's stacks, PJM's record.
**Rule 28** — nothing tested, no cell moves; `energy_reserve_coopt` (`R`), `ordc_scarcity_overlay` (`G`),
`capacity_going_forward_bar_published` (`O`), `capacity_no_default_cap_convention` (`O`) read and left.
**Rule 29** — this is the read that precedes any screen; §7 is the screen it would have to be. **Rule 27**
— docs and one read-only instrument; no source file edited.

**Records added:** this document; `docs/handoffs/d82/phase0-reclear-2026-09-07.py` and its `.json`
(the S0 / S62 / S74 re-clear of the registered stacks, every number in §1.4). **Nothing solved, armed,
built or recommended.** The capx ledger and the PJM matrix shard are the director's to stamp.

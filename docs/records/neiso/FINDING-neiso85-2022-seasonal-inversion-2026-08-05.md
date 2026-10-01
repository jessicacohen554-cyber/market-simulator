# FINDING — neiso-85: the NEISO 2022 seasonal price inversion is ONE object, and it is a defective fuel input

**Session:** neiso-85, 2026-08-05
**Scope:** Phase 0 only. **NO LP WAS BUILT. NO YEAR WAS SOLVED. NOTHING WAS SCORED OR REGISTERED.**
**Keeper:** UNCHANGED (`2026-08-05-neiso-83-ca1-reclass`).
**Mechanism cells:** UNCHANGED — no mechanism was tested (rule 28(d)).
**Verdict:** **ONE OBJECT.** **REFUSAL to charter a model mechanism, with cause.** The object is a
data-input defect with a named source, a measured magnitude, and a direct in-repo precedent for its fix.

---

## 0. Headline

The 2022 touchpoint's seasonal inversion — model 37–58 % **too low** in Jan/Feb/Dec and 48–111 %
**too high** across May–Oct — is **not two price-formation errors of opposite sign**. It is one
defective input, applied with the correct sign in every month.

**NEISO's delivered-gas price for 2022 is seasonally inverted**: the model burned gas at
**$6.09–8.68/MMBtu in winter and $13.79–19.20/MMBtu in summer**. That is backwards for New England,
where Algonquin is pipeline-constrained in winter and unconstrained in summer. **All three tuned
years carry the correct winter-peaking shape** (winter/summer ratio 2.39 / 3.78 / 4.61); 2022 alone
is inverted (**0.397**).

At a **single constant, already-committed heat rate and with zero fitted parameters**, that input
error explains **77.3 %** of the total monthly |price residual|, with **corr(residual, explained) =
0.978** and the **correct sign in all 12 months**.

Phase-0 step 2's confound fires. **This is a fuel-input error, not a dispatch or offer-curve error.**
Per the charter's own instruction, the lane stops there and does not proceed to a merit-order lever.

---

## 1. Governance posture

- **The holdout spend freeze was respected in full.** `holdout-freeze.json` is ACTIVE (re-armed
  2026-08-05). No solve, no score, no registration touched 2022 or any other out-of-training year.
- Everything below is measured from **committed artifacts**: the touchpoint sidecars
  (`results/calibration/neiso2022_touchpoint/hourly/{system,class_hourly,reserve_family}_2022.parquet`,
  `run_config.json`), the committed raw inputs (`data/raw/gas_basis_by_iso_month.csv`,
  `data/raw/gas-prices/`, `data/raw/eia-930/ISNE_fueltype_2022.parquet`), and the fuel-price
  resolution chain **evaluated as a pure function of `(config, year)`** — data inspection, not dispatch.
- **Rule 22 honoured.** 2022 is iterable validation evidence. It is used here only to say **where to
  look**. **No parameter was tuned against the 2022 residual**, and no number in this document is
  quoted as a certified out-of-sample skill claim. The charter's `+14.7 % / +23.1 %` figures are not
  used as skill numbers anywhere.
- **Rule 28 off-queue justification.** NEISO's lever queue is empty (spent at neiso-80/81). This is a
  **new object opened by holdout evidence that did not exist when the queue was closed**, not a
  re-test of a closed cell. No cell marked `R`/`I`/`G` was re-opened.
- The touchpoint bundle persists two passes (`P1`, `P2`) and is **scored on `P2`** (neiso-84 §3).
  Every model number below is read off `P2`.

---

## 2. Phase-0 measurement 1 — the fuel confound (tested FIRST, as instructed)

### 2.1 The model's own resolved delivered gas, by month ($/MMBtu)

Chain: `resolve_annual_gas_price` → `× gas_seasonal_shape` → `iso_monthly_gas_prices` (EIA-923
measured ISO-month) → `_hub_overlay_series` (measured hub basis) → `gas_daily_shape`
(mean-preserving within month).

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2022** | 6.74 | 6.09 | 6.26 | 8.13 | **13.79** | **16.70** | **18.30** | **19.20** | **16.88** | 10.74 | 8.79 | 8.67 |
| 2023 | 4.73 | 8.13 | 2.94 | 1.88 | 1.58 | 2.60 | 2.73 | 1.40 | 1.60 | 1.41 | 3.45 | 3.22 |
| 2024 | 7.68 | 3.49 | 1.63 | 1.51 | 1.60 | 1.92 | 1.84 | 1.62 | 1.81 | 1.79 | 2.26 | 9.13 |
| 2025 | 16.92 | 14.62 | 4.26 | 3.14 | 2.55 | 2.89 | 4.23 | 2.95 | 2.02 | 2.38 | 4.68 | 14.90 |

**Winter (Jan/Feb/Dec) ÷ summer (Jun–Aug):** 2022 **0.397 — INVERTED**; 2023 2.390, 2024 3.778,
2025 4.608 — all normal.

### 2.2 Which stage breaks it

Decomposed stage by stage (`_neiso85_gas_chain.json`):

- **Stage 3, the measured EIA-923 ISO-month series, is CORRECT for 2022** — Jan **16.27**, Feb
  **14.60**, Dec **15.38** against summer **5.27–8.77**. Right shape, and in family with the tuned
  years (2023 Jan 15.17, 2025 Jan 19.46). Receipts exist for **12/12 months**.
- **Stage 4, the hub-basis overlay, overwrites 100 % of 2022's hours and inverts it** — Jan
  16.27 → **6.74**, Aug 8.51 → **19.20**.

The overlay supersedes a correct measured series with a defective one.

### 2.3 Root cause: the basis source changes by year

`data/raw/gas_basis_by_iso_month.csv`, NEISO rows, `basis_usd_mmbtu` over Henry Hub:

| years | source | Jan | Jul | Aug | shape |
|---|---|---|---|---|---|
| **2015–2022** | `EIA N3050MA3 citygate - Henry Hub` | 1.19–5.16 | 4.21–**11.02** | 3.88–**10.39** | **SUMMER-peaking — INVERTED** |
| **2023–2025** | measured **ISO-NE MA gas index** (ISO newswire, per month) | 1.46 / 4.50 / **12.79** | 0.18 / −0.24 / 1.03 | −1.18 / −0.37 / 0.04 | **WINTER-peaking — correct** |
| **2026** | `EIA N3050MA3 citygate - Henry Hub` | 2.13 (Jan), 3.30 (Feb) | — | — | proxy (2 months only) |

**The EIA `N3050<state>3` series is an LDC city-gate *purchase-portfolio average*, not a marginal
wholesale spot.** In summer New England LDC throughput collapses, so fixed pipeline
reservation/demand charges are spread over a small volume and the **average** $/Mcf balloons — while
the **marginal** Algonquin basis, which is what a gas unit's offer actually tracks, goes to roughly
zero. Subtract Henry Hub and the resulting "basis" is inverted in its seasonality. It is a real
measured series used on the wrong boundary — the rule 14 `[R-ACCURATE]` misalignment clause exactly.

**The repo already caught this defect once, in the tuned window, and wrote the diagnosis down.** The
Aug-2025 row's own `source` field reads:

> *"interpolated from Jul (+1.03) and Sep (−0.95) measured ISO-NE MA index; **EIA N3050MA3 proxy
> (+13.46) rejected — low-volume summer LDC citygate average overstates marginal AGT basis** (actual
> Aug-2025 NEISO DA LMP $45.6 vs winter-level proxy implied $167)."*

That is the same failure mode, correctly diagnosed and rejected — **for that one month only**. The
2015–2022 rows were never revisited because those years were never solved.

**There is also a direct cross-ISO precedent already on the matrix.** CAISO's
`caiso_citygate_spot_level` (caiso-84, `FINDING-caiso-winter-gas-level-2026-07-15`) replaced *the
same EIA N3050 family* — described there as "the EIA N3050CA3 monthly LDC purchase-portfolio SURVEY,
which sits >1.2× spot in 24/33 covered months" — with a measured daily spot series, as "a rule-14
`[R-ACCURATE]` swap of one measured EIA series for another whose boundary matches the marginal-offer
representation, zero new fitted scalars."

### 2.4 Attribution — how much of the residual this input error accounts for

Single constant heat rate **7.340 MMBtu/MWh** (the committed NEISO CC_REGULAR cap-weighted p50 quoted
in the keeper shard's neiso-83 block). **Zero fitted parameters.** `explained = HR × (gas_used − gas_923)`.

| mon | gas used | gas (923) | Δgas | explained | model | actual | residual | unexplained |
|---|---|---|---|---|---|---|---|---|
| Jan | 6.74 | 16.27 | −9.53 | −70.0 | 61.5 | 148.7 | −87.2 | −17.2 |
| Feb | 6.09 | 14.60 | −8.51 | −62.5 | 55.4 | 108.7 | −53.3 | +9.2 |
| Mar | 6.25 | 6.85 | −0.59 | −4.3 | 56.8 | 66.4 | −9.6 | −5.2 |
| Apr | 8.13 | 4.86 | +3.27 | +24.0 | 67.1 | 59.4 | +7.7 | −16.3 |
| May | 13.79 | 5.27 | +8.52 | +62.5 | 109.3 | 74.8 | +34.5 | −28.0 |
| Jun | 16.70 | 5.86 | +10.84 | +79.6 | 136.0 | 71.7 | +64.3 | −15.3 |
| Jul | 18.30 | 8.77 | +9.53 | +70.0 | 166.7 | 90.7 | +76.0 | +6.0 |
| Aug | 19.20 | 8.51 | +10.69 | +78.5 | 178.7 | 96.0 | +82.7 | +4.3 |
| Sep | 16.88 | 7.49 | +9.40 | +69.0 | 130.2 | 61.4 | +68.8 | −0.2 |
| Oct | 10.74 | 3.77 | +6.97 | +51.2 | 92.5 | 52.3 | +40.2 | −11.0 |
| Nov | 8.79 | 5.04 | +3.76 | +27.6 | 79.9 | 67.4 | +12.5 | −15.1 |
| Dec | 8.67 | 15.38 | −6.71 | −49.2 | 76.7 | 121.5 | −44.8 | +4.4 |

- **corr(residual, explained) = 0.978**
- **share of total |monthly residual| explained = 77.3 %**
- MAE of monthly residual **$48.47/MWh → $11.02/MWh** once the input error is removed
- **sign correct in all 12 months**

This is a **diagnostic decomposition of an already-committed residual** — an attribution, not a
re-score, not a proposed correction, and not a tuned adjustment. No value here is written back into
any config, and the residual $11.02 MAE is **not** a forecast of what a corrected run would score.

---

## 3. Phase-0 measurement 2 — the summer marginal class, and the dual-fuel tell

The charter's test: *"If the model's summer marginal unit is a class the market was not running, that
is the object."* **It is, and spectacularly so.**

The inverted basis prices summer gas **above dual-fuel oil parity**, so New England's *winter*
fuel-security oil switch fires in **September**:

| | Jan | Feb | Jun | Jul | Aug | **Sep** | Oct | Dec |
|---|---|---|---|---|---|---|---|---|
| model gas $/MMBtu | 6.74 | 6.09 | 16.70 | 18.30 | 19.20 | **16.88** | 10.74 | 8.67 |
| **model oil, TWh** | 0.0002 | 0.0000 | 0.0082 | 0.0320 | 0.0700 | **2.1882** | 0.0000 | 0.0010 |
| **actual oil, TWh** (EIA-930) | **1.0151** | 0.1938 | 0.0044 | 0.0757 | 0.0242 | **0.0046** | 0.0023 | **0.4889** |

- Model oil Jun–Sep **2.2983 TWh** vs Jan/Feb/Dec **0.0012 TWh** — a **1,948 : 1** summer:winter ratio.
- The real fleet is the mirror image: **1.5039 TWh** in Jan/Feb/Dec (the January cold snap and Winter
  Storm Elliott) against **0.1089 TWh** Jun–Sep.
- September alone: model **2.1882 TWh** vs actual **0.0046 TWh** — **476×**. The model displaced
  ~2.2 TWh of CC gas (Sep CC_REGULAR 2.47 TWh vs 6.46 TWh in August) with oil that New England did
  not burn.

**The oil burn is seasonally transposed, exactly like the basis that drives it.** The dual-fuel
switch is a *correct mechanism receiving an inverted price signal* — which is why the object is the
input and not the mechanism.

For comparison, in the months where the input is least wrong the dispatch is right: model
CC_REGULAR Jul 6.42 / Aug 6.46 TWh against actual gas 6.73 / 6.84 TWh.

---

## 4. Phase-0 measurement 3 — the winter leg and the C3c dormancy

**Measured, not assumed**, from `reserve_family_2022.parquet` on the scored pass:

- **26,280 family-hours. `shortfall_mw` max = 0.0, nonzero count = 0. `dual` max = −0.0, nonzero
  count = 0.**
- Winter subset (Jan/Feb/Dec): **6,480 family-hours, 0 short, 0 nonzero duals.**

**The dormancy diagnosis is CONFIRMED: the model is never reserve-short in 2022, in any hour of any
month.** The ledgered C3c caveat's account of the winter build
(`neiso_gas_coldsnap_derate` + `neiso_winter_fuel_inventory` + `neiso_winter_fuel_mustrun`) being
dormant carries into 2022 unchanged.

**But the 2022 dormancy is downstream of the fuel defect, not independent of it.** The model's
January gas was **$6.74/MMBtu against a measured $16.27**. Winter never got tight because winter gas
was never expensive. Component A's oil budget cannot bind when the fuel-cost signal that would drive
the gas→oil switch has been removed — and the switch's own energy confirms this, having fired in
September instead.

**Consequence for the C3c lane:** the derate's depth/trigger — the charter's provisional object for
the winter leg — **cannot be identified on 2022 while the input is inverted.** Any depth tuned
against this winter residual would be absorbing a fuel-price error. That lane should not be opened
until the input is corrected.

---

## 5. ONE OBJECT OR TWO — the verdict (rule 19 `[R-ONE-MECH]`)

**ONE OBJECT.**

The two legs are the *same* defect observed through opposite signs of a single inverted seasonal
input. Evidence:

1. **One quantity, one sign convention.** `Δgas = gas_used − gas_measured` is **negative in Jan/Feb/Dec**
   and **positive in May–Oct**, tracking the residual with **r = 0.978** across all 12 months at one
   constant heat rate. A two-object explanation would need two mechanisms that happen to be
   collinear with a single input error in both magnitude and sign, in every month.
2. **One source-of-record change explains it.** Not a model change: the basis source switches from
   the EIA N3050 proxy (2015–2022) to the measured ISO-NE index (2023–2025) at exactly the boundary
   where the inversion appears and disappears.
3. **One mechanism carries both legs.** The overlay writes the full year — 8,760 of 8,760 hours.
4. **The dual-fuel tell is a single transposition**, not two independent errors: the oil that should
   have burned in Jan/Dec burned in Sep.

Rule 19 is therefore satisfied by **one fix**, and would be *violated* by chartering a winter
scarcity lever and a summer offer lever separately. Both would be fitting model structure to a
defective input.

---

## 6. REFUSAL — no mechanism is chartered, and why

Per the charter: *"A refusal backed by measurement is a full, publishable result here — do not
manufacture a lever to have something to arm."* This is that refusal.

**No `ScenarioConfig` field is proposed. No cell verdict is minted. The keeper is untouched.**

Four independent grounds:

1. **The object is not a mechanism.** A committed input row is wrong. Rules 1 `[R-STRUCT]` and 14
   `[R-ACCURATE]` both say: take the accurate data, fix the root cause, do not bury the error in a
   compensating model parameter. Any lever arming against this residual would be a fitted adder in
   substance (rules 1 / 13 / 26), whatever it was named.
2. **The defect is structurally invisible in the training window, so no lever could be honestly
   validated.** NEISO's 2023–2025 basis rows are **0 % proxy — 100 % measured ISO-NE index**. (The
   `is_proxy` detector was corrected mid-session: a bare `N3050` substring test mis-flags the
   Aug-2025 row, which *rejected* the proxy and interpolated the measured index. The corrected test
   anchors on the source string's prefix.) **A fix to the proxy rows is provably a no-op on
   2023–2025**, so the charter's mandatory leave-one-year-out A/B on the training years would return
   a null for *any* correct fix — it cannot discriminate. Arming a mechanism that *did* move
   2023–2025 would therefore be arming something that is **not** this defect.
3. **The correct fix needs no free parameter.** Replacing a mis-bounded measured series with a
   correctly-bounded measured one is a data correction with **zero DOF**, exactly as CAISO's
   `caiso_citygate_spot_level` was. A mechanism would add DOF to solve a problem that has none.
4. **The remaining $11.02/MWh unexplained residual is not yet a chartered object either.** It is
   small, unsigned-consistent, and measured *on top of* a defective input. Its structure cannot be
   read until the input is corrected. Charter nothing against it now.

---

## 7. What the fix actually is (for owner decision — NOT executed here)

**A data intake, not a model change.** Rule 22 channel 1 permits data intake for out-of-training
windows under explicit session-logged owner authorization, validated **no-LP only**. It is *not*
frozen by the holdout freeze, which covers solve/score/registration.

**Proposed scope:** replace NEISO's `EIA N3050MA3`-sourced rows in
`data/raw/gas_basis_by_iso_month.csv` with the measured ISO-NE Massachusetts gas index — the same
series already used for 2023–2025 — for the years an authorized intake covers. ISO-NE's monthly
wholesale-market recaps (the existing 2023–2025 provenance) publish the index historically, and
`data/raw/gas-prices/algonquin_citygate_daily.csv` is the natural second source but **currently
carries no 2022 rows** (coverage 2023–2025 only), so it would need extending as part of the same
intake.

**Pre-registered validation for that intake, no-LP (rule 22 channel 1):**

- **V1 — seasonality sign.** Corrected NEISO rows must satisfy `winter(Jan,Feb,Dec) −
  summer(Jun,Jul,Aug) > 0` in every year, matching 2023–2025 (+2.83 / +4.54 / +10.97) and reversing
  2015–2022 (−0.58 to −8.56).
- **V2 — in-sample invariance.** 2023–2025 rows must be **byte-identical** before and after. They are
  already measured; an intake that moves them has changed something it must not.
- **V3 — level plausibility against the independent 923 series.** The corrected hub-month level must
  not sit *below* the measured EIA-923 ISO-month delivered cost in Jan/Feb/Dec, the months where the
  constrained hub is by construction the dearer marginal source.
- **V4 — no residual fitting.** The intake commit cites the *data change* only (rule 23
  `[R-FROZEN-DERIVE]`), and must not reference any price residual, MAE, or gate score.

**Sequencing.** The intake is a prerequisite for any further NEISO out-of-training work. Re-solving
2022 afterwards would require a **separate** owner lift of the still-active freeze — which this
session does not request and does not recommend requesting until the intake has landed and passed
V1–V4.

---

## 8. Flags for the owner (surfaced, not acted on)

1. **The 2019 locked-test one-shot is exposed to this defect.** NEISO's 2019 rows are 100 % proxy with
   a **−6.71 $/MMBtu** inversion, and `gas_hub_basis_overlay` is **on by default for NEISO**
   (`pipeline/backcast_config.py:1422`), so the frozen `2026-07-07-neiso53-winter-fuelsec-coldsnap`
   config would have had to disable it explicitly to have escaped. That config is not in the working
   tree and this was **not** verified. **Nothing here proposes re-opening the one-shot** — it is
   SPENT and stands (rule 22). This is recorded so the spent number is *interpreted* correctly, not
   re-scored.
2. **2026 rows are 100 % proxy for every ISO**, including NEISO (Jan +2.13, Feb +3.30). Forecast-mode
   runs are unrestricted and the **crossover window includes H1-2026**, so this reaches a live
   forward lane. Only Jan/Feb 2026 carry rows; later 2026 months resolve to `None` and no overlay.
3. **CAISO is the other ISO that arms this overlay** (`backcast_config.py:1422`) and is **100 % proxy
   in all years including its tuned window**. Its basis seasonality is mild (−1.62 to +2.43 in
   2015–2022) and it already carries the `caiso_citygate_spot_level` correction on a *different*
   leg. Rule 25 `[R-ISO-SCOPE]`: **this is flagged for the CAISO lane, not adjudicated here**, and no
   CAISO cell is touched.
4. **The other four ISOs do not arm the overlay**, so their proxy-sourced rows are inert for now —
   but PJM (−1.46 to −4.06 in 2015–2019) carries a milder version of the same artifact should it
   ever be armed.

---

## 9. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | Honoured — no fitted adder; the object is an input, and the fix is a correctness fix, not a score fix. |
| 13 `[R-MEASURED]` | Honoured — nothing pinned to actuals; EIA-930 used only to falsify the model's oil timing. |
| 14 `[R-ACCURATE]` | The governing rule. A real measured series is used on the wrong boundary; the remedy is a correctly-bounded measured series, with the misalignment documented. |
| 16 `[R-ALLYEARS]` | N/A — no run produced. |
| 19 `[R-ONE-MECH]` | Explicitly adjudicated in §5: ONE object, one fix. |
| 22 `[R-HOLDOUT]` | Freeze respected; 2022 read-only; no tuning against it; no skill claim. |
| 23 `[R-FROZEN-DERIVE]` | Carried into the proposed intake's V4 gate. |
| 26 `[R-DELETE]` | N/A. |
| 28 `[R-MECH-MATRIX]` | Off-queue by necessity, justified in §1. No mechanism tested ⇒ no cell minted (duty d). No new `ScenarioConfig` field ⇒ duty (c) not engaged. §5.6 lever queue and the `gas_hub_basis_overlay` row note updated in this session (duty b, in spirit). |

---

## 10. Artifacts

| path | contents |
|---|---|
| `scripts/probes/_neiso85_seasonal_inversion_phase0.py` | Phase-0 sweep: resolved gas, model LMP, reserve families, class dispatch |
| `scripts/probes/_neiso85_gas_chain_decomp.py` | Stage-by-stage decomposition of the delivered-gas chain |
| `scripts/probes/_neiso85_attribution.py` | Residual attribution, the dual-fuel tell, blast radius |
| `results/calibration/_neiso85_phase0.json` | Phase-0 measurements |
| `results/calibration/_neiso85_gas_chain.json` | Per-stage monthly series + coverage |
| `results/calibration/_neiso85_attribution.json` | Attribution table, oil-by-month, blast radius |

All three probes are read-only and build no LP. Re-run with any Python having pandas/pyarrow and the
package installed.

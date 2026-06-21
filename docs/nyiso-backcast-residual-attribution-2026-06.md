# NYISO backcast — structure-first residual attribution (2026-06)

Keeper under diagnosis: **`nyiso 11 cc-steam rebaseline`**
(`results/calibration/nyiso-11-cc-steam-rebaseline`; flags `--iso NYISO --year
2023 2024 2025 --commitment --gas-monthly-actuals --priced-interchange`, git
`158f9e0`). Reproduced byte-faithfully into the scratch bundle
`results/calibration/_cg_nyiso_repro` (same headline: net interchange
−17.93 / −22.95 / −21.85 TWh for 2023/24/25, matching the registry's
−17.9 / −21.9). Goal: explain, mechanism by mechanism, **why** the modeled LMP
diverges from actual — not to tune the MAE down.

Starting residual (demand-weighted monthly LMP vs actual RT, this repro):
MAE **7.99 / 4.28 / 6.25** for 2023/24/25 (registry 8.20/4.74/5.98; the small
delta is the simple-vs-demand-weighted monthly mean — same shape).

## TL;DR attribution

| Mechanism | 2023 (MAE ~8.0) | 2024 (~4.3) | 2025 (~6.3) |
|---|---|---|---|
| **D** fuel-price shape (monthly-gas smear) | **dominant, ~4–5** (flat winter body over-price) | ~1 (Dec) | ~1 (winter body) |
| **A** import-node discipline | ~1.5–2 (under-import, **out of ±15% band**) | ~1 (over-import, in band) | **gates B** (over-import, diurnal corr −0.86) |
| **B** RCPF reserve scarcity (tail) | ~0 net (offsets D) | ~1 (Dec) | **dominant, ~4** (summer/winter downstate tail) |
| **C** downstate congestion / TTC | <1 (spread slightly wide) | ~0 (spread good) | downstream of B (spread too narrow) |
| **E** hydro / storage / nuclear refuel | ~0 — **ruled out** (volumes near-exact) | ~0 | ~0 |

The two years fail in **opposite directions for opposite reasons**: 2023
**over**-prices because a monthly-average gas spike is smeared flat across the
winter (D), and 2025 **under**-prices because the locational scarcity tail is
missing (B). They are not the same knob, and a single price-level lever would
trade one against the other.

---

## 1. Residual decomposition along every axis

### 1a. Time (month, then hour-of-day)

Monthly residual (model − actual RT, $/MWh):

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | **+44** | **+11** | **+12** | −2 | +3 | −2 | +4 | +2 | −6 | −3 | −2 | +6 |
| 2025 | **−12** | **−14** | +7 | +1 | +5 | **−14** | **−12** | +2 | +0 | −5 | −0 | −3 |

- **2023** MAE is ~70% the **Jan/Feb/Mar over-price** (Jan +44 alone is the
  single largest term in the whole three-year scorecard). The over-price is a
  **flat all-hours offset**, not a peak/ramp miss: in the Jan/Feb/Mar window the
  hour-of-day residual is +22…+26 even at 02:00–05:00 (overnight body), as high
  as the evening ramp. A flat offset that does not concentrate in the peak is
  the fingerprint of a **marginal-cost-level** (fuel-price) error, not a
  scarcity/ramp error.
- **2025** MAE is ~68% the **Jan/Feb + Jun/Jul under-price**, and that
  under-price **concentrates in the afternoon-peak / evening ramp** (Jun/Jul/Aug
  hour-of-day residual: −23 at 15:00, **−78 at 17:00**, −51 at 18:00/19:00),
  while the overnight body is slightly **over**-priced (+6…+10 at 01:00–09:00).
  Peak-concentrated under-pricing is the fingerprint of a **missing scarcity
  tail**.

### 1b. Duration curve (model vs actual RT percentiles)

| | series | mean | p50 | p90 | p95 | p99 | max |
|---|---|---|---|---|---|---|---|
| 2023 full | model | 35.9 | 29.8 | 58.1 | 79.8 | 91.4 | 254.9 |
| | actual | 30.3 | 26.3 | 42.2 | 52.2 | **119.7** | **1,146.9** |
| 2025 JJA | model | 50.1 | 48.9 | 67.7 | 78.4 | 104.1 | 232.3 |
| | actual | 57.9 | 41.9 | 80.9 | 98.3 | **574.9** | **2,073.9** |

Both years: the model clears a **body around the right level but no tail**
(2023 max $255 vs actual $1,147; 2025 max $232 vs actual $2,074). In 2023 the
body sits **above** actual (the D over-price); in 2025 JJA the body sits
slightly **below** but the p99/max gulf is enormous (B). High-price-hour counts
make it concrete:

- 2023 Jan/Feb/Mar: actual **59 h >$100, 11 h >$200**; model **0 and 0**.
- 2025 Jun/Jul/Aug: actual **47 h >$200, 26 h >$500**; model **4 and 0**.

### 1c. Zone level + west→east spread (model vs actual DA)

| year | zone | model | act DA | resid | | spread (E−Upstate) | model | act DA |
|---|---|---|---|---|---|---|---|---|
| 2023 | Upstate_West | 27.9 | 26.1 | +1.8 | | NYC−Upstate | **+12.5** | +7.9 |
| 2023 | NYC | 40.4 | 34.0 | +6.4 | | Capital−Upstate | +12.5 | +10.3 |
| 2023 | Long_Island | 40.4 | 40.8 | −0.3 | | | | |
| 2025 | Upstate_West | 54.1 | 55.9 | −1.8 | | NYC−Upstate | **+4.7** | +9.5 |
| 2025 | NYC | 58.7 | 65.4 | −6.7 | | Capital−Upstate | +4.6 | +9.3 |
| 2025 | Long_Island | 58.7 | 68.9 | −10.1 | | | | |

- **Upstate is right in level all years** (+1.8 / −1.8) — the Central-East TTC
  monthly envelope (U7) and the U9 import-node zone remap are doing their job;
  the upstate-cheap surplus is no longer trapped, and the west→east spread is
  the right sign and roughly the right magnitude in 2023/24.
- **The miss is downstate level, not upstate or the congestion incidence.**
  2023 over-prices NYC/Lower-Hudson by ~$6–7 (spread too **wide**, A:
  under-import forces NYC peakers); 2025 under-prices NYC/LI by ~$7–10 (spread
  too **narrow**, B: the missing downstate scarcity tail). The model collapses
  the four downstate zones (F–K) onto one price (NYC = Lower-Hudson =
  Long_Island within $0.05), so it cannot reproduce the Long_Island premium
  ($40.8 in 2023, $68.9 in 2025) — a known zonal-resolution limitation, second
  order to the level miss.

### 1d. Actual-price band (share of the $·h gap)

- **2023 Jan/Feb/Mar:** the 0–25 and 25–50 actual bands carry **+41% and +73%**
  of the $·h gap (model over-prices the cheap/mid body); the 100–200 and ≥200
  bands carry −9% and −6% (model under-prices the real tail). I.e. **+114% of
  the gap is body over-pricing**, partially offset by the missing tail.
- **2025 Jun/Jul/Aug:** the **≥200 band carries +133%** of the gap (47 h, actual
  $597 vs model $115); 100–200 and 75–100 each +19%. The 0–25 / 25–50 bands are
  −32% / −50% (the body over-prices and offsets). I.e. the residual **is** the
  scarcity tail.

---

## 2. Mechanism attribution (verified, not assumed)

### D — Fuel-price shape: the dominant 2023 driver (monthly-gas smear)

The NYISO measured monthly gas series the keeper burns (`gas_monthly_actuals`,
`iso_monthly_gas_prices`, $/MMBtu):

| year | Jan | Feb | Mar | Apr | … |
|---|---|---|---|---|---|
| 2023 | **10.02** | 5.62 | 3.13 | 1.93 | … |
| 2025 | 8.54 | 6.91 | 4.47 | 3.39 | … |

Jan-2023 at **$10.02/MMBtu** is a *volume-weighted monthly average* dominated by
the late-Dec-2022 / early-Jan cold snaps (Winter Storm Elliott and the January
cold). Applied **flat to all 744 January hours**, it prices every hour's
marginal gas CC (HR≈7) at ~$70/MWh and the peaking gas CT at ~$95 — producing
the flat $52–95 winter body. The duration curve confirms the model's Jan/Feb/Mar
p90 is $88 and max $95 (gas CT at $10 gas), not a flat $50; the dual-fuel
oil-parity cap (~$16/MMBtu distillate) is **not** crossed at $10 gas, so this is
gas, not oil — the units are not flipping to oil, they are burning
spike-priced gas every hour.

**The residual tracks the gas series, not load:** Jan ($10.0) **+44** → Feb
($5.6) **+11** → Mar ($3.1) **+12** → Apr ($1.9) **−2**. The over-price collapses
exactly as the monthly spike fades. A real January daily gas basis prices ~25
mild days at ~$3–5 (CC ≈ $30/MWh, matching actual ~$28–35) and ~5 cold days at
$20–40; the monthly mean smears the 5 cold days across the 25 mild ones.

**This is a *gas-series* artifact, and the fix is NOT simply "upload daily
data" — see §4b.** The keeper burns the EIA-923 monthly **receipt** cost
(`iso_monthly_gas_prices`), which is plant-average *delivered* cost (firm
pipeline + storage), winter-inflated and summer-deflated. Jan-2023's $10.02 is
the single worst month: it is **+$4.4 above** the EIA NY-citygate proxy already
in the repo (`gas_basis_by_iso_month.csv`, HH + N3050NY3 basis = **$5.60**),
consistent with late-Dec Winter Storm Elliott gas billed/stored into the January
receipt average (Feb's receipt−citygate gap is only +$0.28). It must **not** be
papered over by lowering the monthly gas uniformly — see the tested-and-rejected
citygate swap in §4b, which shows why.

### A — Import-node discipline: real, but bounded by an EIA-930/923 basis tension

Model vs measured (EIA-930) net interchange (import-positive TWh):

| year | model | measured | % | ±15% band | depth p99 (GW) | diurnal corr |
|---|---|---|---|---|---|---|
| 2023 | 17.93 | 23.45 | **76.5%** | [19.9, 27.0] **OUT** | model 3.31 / meas 4.91 | +0.69 |
| 2024 | 22.95 | 20.35 | 112.8% | [17.3, 23.4] in | — | +0.49 |
| 2025 | 21.85 | 19.09 | 114.5% | [16.2, 21.9] in | model 4.00 / meas 5.87 | **−0.86** |

Import tranche clearing (the gas-keyed ladder `IMPORT_TRANCHES_BY_YEAR`):

| 2023 tranche | $/MWh | cap MW | clears | TWh |
|---|---|---|---|---|
| HQ_hydro | 13.0 | 900 | 100% | 7.88 |
| IESO_Ontario | 22.5 | 1200 | 82% | 8.04 |
| PJM_west | 34.2 | 1100 | 24% | 1.97 |
| ISONE_tie | 39.9 | 800 | **1.5%** | 0.04 |
| import_scarcity | 68.4 | 1900 | **0.0%** | 0.00 |

**2023 under-import mechanism (verified):** the two deep blocks (ISONE_tie
$39.9, import_scarcity $68.4 — 2,700 MW of capacity) sit **above NYISO's 2023
price body** (~$28–40), so they never clear, and served imports cap at
~3.3 GW (HQ + IESO + part of PJM_west) vs a measured 4.9 GW p99. But the deep
imports reality served were **firm/scheduled HQ + Ontario baseload that flows
regardless of NY's hourly price**, not $68 scarcity economy energy — the ladder
mis-attributes firm depth to a gas-priced scarcity proxy.

**The catch (report-and-stop): closing the 2023 import gap breaks the gas-volume
band.** In-state gas is currently **+4.1% vs EIA-930 / −0.5% vs EIA-923**
precisely *because* the model under-imports. Serving the full −23.45 TWh wedge
would push ~5.5 TWh of in-state gas out → ~58 TWh ≈ **−9% vs EIA-923**, outside
the ±5% band. This is the documented **EIA-930 (operational) vs EIA-923
(accounting) basis floor**: the EIA-930 demand basis + the −23.45 wedge + the
EIA-923 gas total are not mutually consistent, and the priced node splits the
difference — gas in-band, **interchange out-of-band**. So the 2023 interchange
miss is *partly structural*; a ladder re-anchor cannot fully close it without
violating the gas band. **A is real but it is not the largest 2023 $ (D is), and
it is volume-constrained.**

**2025 over-import + diurnal mis-shape (verified):** 2025 is *in* the ±15% band
on level (114.5%) but the **diurnal hour-of-day profile is anti-correlated with
reality (−0.86)**: the static node clears a near-flat schedule (every tranche
available every hour), so it imports *too much on-peak* (suppressing the
afternoon/evening price) and too little overnight — the opposite of real
imports, which are deep overnight (cheap baseload) and back off on-peak when the
neighbors are also tight. This is what **gates B** (next).

### B — RCPF reserve scarcity: correct market design, gated by A's headroom

The locational RCPF overlay (`NYISO_RCPF_LOCATIONAL`, tariff-sourced RS4 / FERC
ER21-502) is **correct and stays as-is**. Re-run on the repro
(`derive_nyiso_rcpf_overlay --locational`), the per-zone modeled adder vs the
**measured** NYISO OASIS RT reserve price:

| year | zone | model adder mean | measured mean | model >$0 h | measured >$0 h |
|---|---|---|---|---|---|
| 2023 | NYC | **$64.16** | **$6.37** | 2,994 | 3,020 |
| 2025 | NYC | **$3.68** | **$28.73** | 260 | 4,007 |

The overlay **over-fires NYC ~10× in 2023** and **under-fires ~8× in 2025** —
both because it is gated on the energy LP's per-zone headroom, which A
contaminates:

- **2023:** import **under**-service → NYC backfills with in-zone gas → NYC
  dispatchable headroom too **tight** → RCPF over-fires (and the energy LBMP
  already over-prices NYC +$6.4, so stacking the overlay would **double-count**
  the congestion).
- **2025:** import **over**-service (flat, −0.86 diurnal) → NYC headroom too
  **loose** in the summer-peak hours → RCPF under-fires → the $200–2,000 tail is
  missing → 2025 under-prices.

System-wide, even in actual >$300 hours NYCA headroom stays 2.6–4.5 GW (p5–p50)
vs the 2,620 MW 30-min requirement, so the **system-wide** curve correctly fires
$0 — the scarcity is **locational** (the measured cascade WEST $2.20 →
N.Y.C. $6.37 in 2023, escalating to N.Y.C. **$28.73** in 2025). B owns the bulk
of the 2025 MAE and the 2023 tail, but it **cannot be applied cleanly until A
gives the LP the right per-zone headroom.**

> **Validation bug fixed this session:** `derive_nyiso_rcpf_overlay.py` and
> `analyze_lmp_residual.py` read the actual/measured series from the stale
> `inputs/calibration/` path (relocated to `data/raw/_validation-source/`,
> `paths.CALIBRATION_DIR`). The deriver therefore printed "--" for every measured
> column and NaN-filled the actual-RT MAE. Repointed to the live path — the
> measured per-zone reserve validation above now populates (it was the explicit
> "fix the measured-validation load" item).

### C — Downstate congestion / TTC: binding correctly; spread error is downstream

The Central-East monthly TTC envelope (U7, measured DAM postings ~1,750 MW 2023
→ 2,850 from Dec-2023) and the U9 import-node zone remap put Upstate at the
right level all years (§1c). The west→east **spread** is right in sign and
~right in magnitude in 2023/24 (NYC−Upstate model +12.5 vs +7.9; Capital +12.5
vs +10.3) and only collapses in 2025 (+4.7 vs +9.5) — but that 2025 collapse is
**downstream of the missing tail (B)**, not a TTC binding error: with no
downstate scarcity adder the four F–K zones cannot separate. C is not an
independent driver; the interfaces bind in the right hours.

### E — Hydro / storage / nuclear refuel: ruled out

Volumes are near-exact: 2023 hydro 28.38 vs 28.40 TWh budget (+0%), nuclear
27.49 vs 27.52 (−0.1%), wind 4.60 exact; 2025 hydro at the 21.05 TWh budget,
nuclear exact. None of these move the price residual — confirmed not drivers.

---

## 3. Ranked structural fixes

1. **D — source the Transco-Z6 NY / Iroquois Z2 *trading-hub spot* (monthly is
   enough), NOT the EIA citygate proxy.** Highest single-$ item (2023 winter
   +44/+11/+12). The two monthly series already in the repo bracket the truth
   but neither is it: EIA-923 **receipts** are winter-high (Jan $10.02), EIA
   **N3050NY3 citygate** is summer-high ($6.6 Jul → blows up summer, §4b). The
   marginal-spot index sits between them — low-$3–5 mild winter days, modest
   ~$1 summer basis. A monthly Transco-Z6/Iroquois spot (or its daily form for
   the cold-snap shape) fixes winter **without** the citygate's summer
   regression. **Measured input, zero tuning.** Until it lands, the Jan-2023
   over-price is correctly attributed to D and left in place — do **not** swap
   the whole series to the citygate proxy (§4b) and do **not** hand-edit single
   months.

2. **A — shape the priced node to the measured EIA-930 diurnal envelope
   (`--interchange-shaping`), then re-anchor the deep tranches.** The static node
   imports a flat schedule (2025 diurnal corr −0.86); the measured month×hour
   envelope (`measured_interchange_envelope`, p90, **no fitted constant**) caps
   each tranche to its historical diurnal level, reshaping the 2025 over-import
   off-peak and freeing NYC peak headroom for B. *(Tested this session — see
   §4.)* A finer split of the cheap HQ/Ontario **firm** baseload (so the deep,
   price-insensitive import is not mis-priced as $68 scarcity) is the follow-on,
   **bounded by the EIA-923 gas band** — the 2023 wedge cannot be fully closed
   without breaching ±5% gas, so target the *shape*, not the last TWh of level.

3. **B — re-run the locational RCPF overlay *after* A lands, not before.** The
   curve is correct (tariff-sourced); its 2023 over-fire / 2025 under-fire are
   pure headroom contamination. Once A gives the LP the right per-zone peak
   headroom, the NYC adder should track the measured $6.37 (2023) / $28.73
   (2025) without touching the demand curve. Two sub-items, both honest:
   (a) the validation path bug is **fixed** (§2.B); (b) `TODO(SENY-MW)` — the
   SENY 30-min requirement is still a **1,100 MW placeholder** (bracket midpoint
   of East 1,200 ⊇ SENY ⊇ NYC 1,000); source the published RS4 value before the
   SENY tier is trusted. **Do not** force the system-wide curve to fire by
   inflating requirements or subtracting a headroom offset — that buries A.

4. **C — zonal price resolution (F–K) is a second-order follow-on** to recover
   the Long_Island premium; not worth touching until A/B land.

---

## 4. Tested this session — interchange shaping (mechanism A) → REJECTED

Probe `_cg_nyiso_shape` = keeper config **+ `--interchange-shaping`** (the
measured EIA-930 month×hour-of-day p90 envelope caps each import tranche's
availability; no fitted constant). One mechanism changed; re-scored on price
**and** both volume bands:

| metric | year | keeper | + shaping | verdict |
|---|---|---|---|---|
| diurnal hod corr | 2023 | +0.69 | **+0.96** | shape fixed |
| | 2025 | **−0.86** | **+0.24** | shape fixed |
| net interchange (% of measured) | 2023 | 76.5% (OUT) | **60.6% (OUT)** | worse |
| | 2024 | 112.8% (in) | **74.9% (OUT)** | **band broken** |
| | 2025 | 114.5% (in) | **71.6% (OUT)** | **band broken** |
| gas vs EIA-930 | 2025 | −6.4% | **+5.0%** | band edge |
| monthly LMP MAE | 2023 | 8.0 | **9.6** | worse |
| | 2024 | 4.3 | **7.5** | worse |
| | 2025 | 6.3 | **8.3** | worse |

**The probe confirms the diagnosis but is the wrong tool.** It *proves* the 2025
diurnal defect is real and shapeable (corr −0.86 → +0.24). But the off-the-shelf
`interchange_shaping` is CAISO-shaped: it caps **gross** import availability to
the **net**-import p90 envelope, and per-(month, hour-of-day) bucket that p90 is
*tighter* than the keeper's flat economic clearing in most buckets — so it
**starves baseload imports** (all three years drop below the ±15% band, 2024/25
from in-band to out), substitutes in-state gas (2025 gas −6.4% → +5.0%), and
**raises every year's price MAE**. Per the methodology rule — *a fix that
improves one axis by breaking a volume band is a zero-sum trade; report and
stop* — **this run is rejected and the keeper stands.** Registered as a
documented negative result so it is not re-tried blindly.

The right NYISO tool is **not** a gross-import cap but either (a) a per-tranche
diurnal *re-weight* that preserves the annual import level while moving it
overnight, or (b) splitting the cheap HQ/Ontario blocks into a **firm**
must-flow tranche (priced ~$0, clears every hour like a real long-term schedule)
plus an economic remainder — so the deep, price-insensitive baseload import is
modeled as firm rather than as $68 scarcity that won't clear. Both are bounded
by the EIA-923 gas band (§2.A) and need their own guarded run.

## 4b. Tested this session — citygate hub-basis swap (mechanism D) → REJECTED

Probe `_cg_nyiso_citygate` = keeper **+ `--gas-hub-basis-overlay`**: replace the
EIA-923 receipt series with the monthly **EIA NY-citygate** level (HH +
N3050NY3 basis, `gas_basis_by_iso_month.csv`), zonal spread + dual-fuel cap
applied on top as before. Directly tests "use the monthly citygate data we
already have."

| metric | year | keeper (receipts) | + citygate | verdict |
|---|---|---|---|---|
| Jan resid | 2023 | **+44** | **+14** | winter fixed |
| Feb resid | 2023 | +11 | +10 | held |
| Jul resid | 2023 | +4 | **+46** | **summer blows up** |
| Aug resid | 2023 | +2 | **+42** | **summer blows up** |
| monthly LMP MAE | 2023 | 8.0 | **21.5** | far worse |
| | 2025 | 6.3 | **24.2** | far worse |
| gas vs EIA-923 | 2023 | −0.5% | **−9.4%** | **band broken** |
| gas vs EIA-930 | 2025 | −6.4% | **−13.4%** | **band broken** |
| net interchange | 2023 | 76.5% (OUT) | 97% (in) | (incidental) |

The citygate **nails the winter** (Jan CC cost $39 vs actual $38; the receipt
series' $10.02 was the artifact — the user's diagnosis is correct) **but
over-states summer by ~$10–13/MWh** (Jul citygate $6.6 → CC $46 vs actual
$36), because EIA's N3050NY3 "citygate" is an LDC/utility delivered price
carrying summer demand charges — **not** the power-plant marginal spot. Swapping
the whole series trades the winter over-price for a worse summer one (MAE 8→21)
and pushes gas out of the ±5% band. **Rejected per the volume-band + don't-trade
guardrail; keeper stands.** The finding refines mechanism D: the winter residual
*is* a gas-series artifact (not U4-daily-blocked as first written), but the
clean fix is the **Transco-Z6/Iroquois trading-hub spot**, a third series
distinct from both repo proxies — receipts (winter-high) and EIA citygate
(summer-high) bracket it. Registered as `nyiso 13 citygate-gas (PROBE)`.

## 5. What changed in code this session

- **Fixed** the stale validation path in `scripts/derive_nyiso_rcpf_overlay.py`
  and `scripts/analyze_lmp_residual.py` (`inputs/calibration` →
  `data/raw/_validation-source`, `paths.CALIBRATION_DIR`). This unblocked the
  measured per-zone RT-reserve validation (was printing "--") and the actual-RT
  MAE in the residual analyzer — the explicit mechanism-B "fix the
  measured-validation load" item. No model/dispatch code touched; volumes and
  prices are byte-identical.
- **No tuning.** No offer band, gas price, ladder, requirement or demand curve
  was changed. The keeper `nyiso 11 cc-steam rebaseline` remains the keeper.

## 6. Still-blocked / not-done (honest ledger)

- **Transco-Z6 NY / Iroquois Z2 trading-hub spot gas (monthly or daily)** —
  gates the dominant 2023-winter D residual. The repo's two monthly proxies are
  *not* it (receipts winter-high, EIA N3050NY3 citygate summer-high; §4b), so
  this is a genuine new data ask — a marginal-spot index, not the EIA citygate.
  Top data ask.
- **`TODO(SENY-MW)`** — the SENY 30-min reserve requirement is still a 1,100 MW
  placeholder (bracket midpoint East 1,200 ⊇ SENY ⊇ NYC 1,000). The published
  Rate Schedule 4 value requires the NYISO Ancillary Services Manual / RS4 PDF,
  which is not fetchable in this environment — **left as placeholder, not
  fabricated.**
- **Mechanism-A firm-import tranche / diurnal re-weight** — designed (§4) but
  not run; needs a guarded re-solve with the gas + interchange bands as
  guardrails.
- **2024 unit-level CEMS + `NYISO_2024_renewable_capacity.csv`** — note: 2024
  now runs in this 3-year bundle (the historic outage overlay covers it), but
  the older block note in `calibration-best-so-far-nyiso.md` predates it.

# FINDING — closeout-SPP-w2 / R-62 (zero LP): the 2024 mean-price shortfall is Sep–Oct Oklahoma congestion on top of the common upper-tercile compression

- **Owner ruling R-62** (2026-10-03, decision card, verbatim): *"Keep digging on 2024 price"*. Card: *"Charter a
  fresh look at the 2024 mean-price shortfall (−11.2%) beyond the closed queue … Zero-LP first."*
- **Lane:** closeout-SPP-w2, desk `session_01ERkBTm23ZAP4CTZnJVD9Ss`. Branch `claude/closeout-spp-w2`, cut from
  main `9e50c05e`.
- **Keeper (read only):** `2026-10-03-closeout-spp-nuc-keeper`, bundle `closeout_spp_nuc_span`.
- **LP spent:** zero. Nothing was armed, solved or registered.
- **Probe:** `scripts/probes/_closeoutsppw2_c3a2024_decomp.py` →
  `results/phase0/spp/_closeoutsppw2_c3a2024_decomp.json`.
  - Model side: the P1 zonal duals and demand (`system_<y>`) and the marginal flags (`unit_marginal_<y>`).
  - Actual side: SPP North/South hub RT and DA, weighted by the model's own zonal demand. This is the scorer's
    `rt_lw` construction, and it reproduces the scorer: 2024 −11.3 % against −11.2 %.
  - The extra reads in §2 use `actual_lmp_components_hourly_zonal_SPP` (MEC/MCC/MLC), SPP-57's
    `actual_lmp_hourly_area_SPP`, and `RTBM-BC-YEARLY-2023/2024`.

## 1. Decomposition (contribution to C3a, in points of the actual load-weighted mean)

### By actual-RT price tercile (system, demand-weighted)

| tercile | 2023 model / actual / pts | 2024 | 2025 |
|---|---|---|---|
| low | 12.80 / 2.56 / **+12.6** | 11.92 / 0.32 / **+14.2** | 15.75 / 2.30 / **+14.8** |
| mid | 25.82 / 20.97 / +6.2 | 23.54 / 18.78 / +6.0 | 29.64 / 23.13 / +7.4 |
| high | 30.64 / 48.22 / **−25.5** | 30.86 / 52.87 / **−31.6** | 35.56 / 56.83 / **−26.6** |
| **C3a** | **−6.7 %** | **−11.3 %** | **−4.4 %** |

- **Every train year has the same shape.** The model's price distribution is compressed: it is high in the low
  tercile and low in the upper tercile.
- **2024 is that same shape plus about 6 extra points in the upper tercile.**
- Against DA the upper tercile is still −23.4 pts in 2024 (DA lw 28.26; C3a vs DA −20.1 %). The compression is not
  an RT-only object.

### By model zone (hub reference)

| zone | 2023 model / actual / pts | 2024 | 2025 |
|---|---|---|---|
| SPP-North | 23.25 / 24.12 / −1.8 | 22.36 / 20.70 / **+3.4** | 26.76 / 28.69 / −3.4 |
| SPP-South | 23.83 / 26.37 / −4.9 | 22.83 / 30.52 / **−14.7** | 28.03 / 28.59 / −1.0 |

**The 2024 shortfall is entirely South.** The model's North is over the actual.

### By month (2024, pts)

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | **9** | **10** | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2024 | +0.3 | +1.1 | −1.4 | −1.3 | −0.2 | −0.1 | −2.7 | −2.3 | **−2.7** | **−3.3** | −0.6 | +1.7 |
| 2023 | +1.0 | −1.5 | +0.4 | −1.6 | 0.0 | −1.7 | −2.8 | −3.3 | **+0.9** | **+1.0** | +0.1 | +1.0 |

- July and August are short in every year: the summer upper tercile.
- **September and October are 2024's own increment**: −6.0 pts, against +1.9 in 2023.

**By hour of day (2024):** the model is over from 20:00 to 06:00 (+0.3 to +1.2 pts per hour) and under from 08:00
to 18:00. The peak miss is −3.4 pts per hour at 16:00. The model's diurnal amplitude is $14 against the actual's
$40.

**By model marginal class (2024):**
- Most of the miss sits in hours where the model has no thermal setter (renewables, curtailment or storage set
  the price): −7.4 pts on 47 % of the weight.
- The rest sits where a peaking class sets the price: ST_GAS −3.7, CT_PEAKER −2.7, hydro (storage-valued) −2.0.
- Base classes are over: CC_REGULAR +2.9, COAL_PRB +1.0.
- The pattern is the same in 2023 and 2025. 2024 differs mainly in the renewable-set hours (−7.4 vs −4.1 / −5.3).

## 2. Hub or body or reference basis? (the R-62 question)

### Reference basis: **not the cause**

| year | C3a vs hub LMP (scored) | vs system energy component (MEC) | vs DA | hub MCC, demand-weighted |
|---|---:|---:|---:|---:|
| 2023 | −6.6 % | **−18.6 %** | −14.7 % | −3.50 |
| 2024 | −11.2 % | **−19.2 %** | −20.1 % | −2.27 |
| 2025 | −4.3 % | **−16.1 %** | −9.3 % | −3.79 |

- Against SPP's system lambda (MEC) every train year is 16–19 % short.
- The hubs normally sit $2–4 *below* MEC (negative MCC), and that is what flatters 2023 and 2025.
- SPP-57's non-Oklahoma South area price (`p_s`, SPS + SWEPCO) is $30.95 in 2024, higher still than
  SPPSOUTH_HUB at $27.53.
- So no admissible reference basis (MEC, DA, area) lifts 2024. Each one makes it worse.

### The 2024-specific increment is South congestion

| year | South − North spread, RT hub: model / actual | of which actual MCC (RT / DA) | Sep–Oct actual MCC spread |
|---|---|---|---|
| 2023 | 0.62 / 1.95 | 1.83 / 2.65 | 5.68 |
| **2024** | **0.69 / 8.42** | **8.39 / 9.09** | **27.51** (DA 25.41) |
| 2025 | n/a / −0.13 | −0.13 / 0.80 | −0.54 |

- 2024's South premium is **100 % congestion component**, both RT and DA. It is planned and visible day-ahead,
  not RT scarcity. It peaks in Sep–Oct, when the actual South hub ran $42–44 against North at $12–18.
- **Which constraints carried it.** RTBM 2024 Sep–Oct rent, by |shadow price|:
  - Cimarron 345/138 kV XF (two elements, 12.4 %);
  - Osage–Webb Tap (5.1 %);
  - Russett–South Brown (3.8 %);
  - Penn–Santa Fe (3.3 %);
  - Division–Mustang (3.2 %);
  - SPS NM ties (3.1 %).
- These are **Oklahoma-internal and OKC load-pocket** elements. In 2023 the top was Charlie Creek–Watford, a North
  element.
- Top-10 share is 0.405. This is a pocket object, not a two-zone seam.
- **Counterfactual (zero LP, actual side only).** Remove the excess Sep–Oct S−N MCC (above 2023's 5.68 Sep–Oct
  level) from the actual South price. The 2024 actual lw falls 25.45 → 23.02, and **C3a reads −1.8 %**. Against
  zero excess it reads −0.7 %.
- So the out-of-band part of 2024 (−11.2 → −10.0 needs only 1.2 pts) is several times over this one object.

**Answer.**
- The shortfall is **upper-tercile compression common to every train year**, plus a **2024-specific Sep–Oct
  Oklahoma-pocket congestion premium** at the South hub.
- The premium is DA-visible and 100 % MCC, and it is worth about 9 pts.
- It is neither body nor scarcity, and not a reference-basis artifact.

## 3. Candidate screen (R-62 part 2). SPP.js cells were read first (rule 28)

| candidate | cell / prior | 2024 reach (zero LP) | verdict |
|---|---|---|---|
| measured RT scarcity / ORDC-equivalent | `energy_reserve_coopt` I (re-measured today: 0 bind h); `ordc_scarcity_overlay` U, rule-19 excluded while the co-opt family exists (SPP-55) | 2024's upper tercile averages $53; it is not scarcity hours. Reserve-short hours price at $32–36 (SPP-55). | **not chartered** |
| offer-cap / mitigation conduct, offer bands | rule-1 band channel; DO-NOT-REDO offer-band retunes; SPP-81b re-measured at SPP-109 §4 (no forward driver) | One band value across all years lifts 2019/20 (already +12/+28 %). A conduct markup is the C3c object (> $200), not the $53 tercile. | **not chartered** |
| wind-curtailment pricing | curtailment ceiling DO-NOT-REDO (SPP-94) | It acts on the **low** tercile (+14.2 pts, model $11.92 vs actual $0.32). Correcting it **lowers** C3a; it would help C3b only. | **not chartered** (wrong sign for C3a) |
| gas index basis (hub vs Panhandle/OGT) | `gas_monthly_actuals` U (price-family: SPP price ∦ gas, corr 0.27); `gas_plant_monthly_fuel_pricing` is on | Plant-level EIA-923 monthly delivered gas is already priced. Panhandle/OGT 2024 basis is negative against HH, the wrong sign. | **not chartered** |
| 2024 outage data recency | SPP-105/109 (R); MMU bands per year | SPP-109: the sub-5-day ST_GAS gap is ≈ 0.3 GW, and Z1/Z2 killed it. A supply cut raises North and South alike; the 2024 object is a **spread**. | **not chartered** |
| DA vs RT / MEC / area reference | rubric (rule 37) | Every alternative basis is worse (§2) | **not chartered** |
| **Oklahoma-pocket congestion, Sep–Oct 2024** (this decomposition) | `measured_interface_limits` O; `internal_congestion_split` U; SPP-57 three-zone OK pocket killed on its 2025 screen (links not live at FCITC 6,500/6,700 MW) | ~9 pts. The only object that reaches the band. | **data-limited**: see below |

**Why the Oklahoma object is not buildable from disk.**
- (a) The in-window RTBM yearly archives (2019–2024) carry shadow prices but **no effective-limit columns** (README
  status correction, SPP-29). A 2024-own limit therefore cannot be measured.
  - The keeper's N↔S 3,400 MW link is built from **2026** limits (rule-14 misalignment (i), `iso_configs.py`).
  - Its leave-2024-out width is 2,645–11,121 MW.
- (b) No SPP transmission-outage series is on disk. The Sep–Oct timing and the DA visibility point to planned
  transmission outages, e.g. at Cimarron XF. OASIS/CROW is blocked (README).
- (c) SPP-57 already showed that an FCITC-rated Oklahoma bubble does not bind. Re-cutting it without new limit data
  is a re-test without new evidence (rule 28).
- Any adder keyed to the observed spread would be the residual-driven channel rules 1 and 13 forbid.

**No candidate clears part (3).** No PRECOMMIT is written and no shards are launched.

## 4. Data ask (routes the Oklahoma object)

| ask | why | what it unlocks |
|---|---|---|
| **SPP RTBM binding-constraint files for 2023–2024 with the three effective-limit columns** (the v35 daily/monthly form; `portal.spp.org` `rtbm-binding-constraints`, the daily files) | gives an in-window limit for the SPP-53 construction, a rule-14 repair of the 2026-vintage TTC, and the first measured rating for the Cimarron/OKC pocket elements | a year-own N↔S TTC; re-opens SPP-57's Oklahoma pocket on new evidence |
| **SPP planned transmission outages, 2024** (CROW / OASIS outage export) | identifies whether the Sep–Oct Oklahoma binding is an outage window (a rule-13-admissible, forward-reproducible input: planned outage schedules exist ex ante) | a dated derate on the pocket's limit, with no fitted parameter |

Until one of these lands, C3a/C3b 2024 is a **data-limited** row. The draft ledger text in
`FINDING-closeout-spp-w2-2026-10-03.md` §5 should be re-worded from "sub-5-day ST_GAS" to "**Sep–Oct 2024
Oklahoma-pocket congestion (≈ 9 pts), transmission limits/outages not in window**". ST_GAS (≈ 0.3 GW) is the minor
term.

## 5. Rules

- **1 / 13:** no adder is proposed on the observed spread.
- **14:** the 2026-vintage TTC misalignment is restated with the in-window data that would repair it.
- **28:** `measured_interface_limits` (O) and `internal_congestion_split` (U) carry this evidence. No cell moved.
- **29 / 32:** zero LP.
- **37:** no reference basis is proposed; §2 shows every alternative basis is worse.

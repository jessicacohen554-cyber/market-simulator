# RESULT — SPP-50 (2026-09-20): Object A re-measured, and demoted

**Base:** `e5f966fd6574123923dad090e90742ce0c21b331` (`origin/main`). The handoff's
conditional base did not apply — `dc800903` (the SPP-49 promotion) **is** an ancestor of
`origin/main`, checked at session start, so `main` is the base.
**Keeper:** `2026-09-16-spp-42-commitment-feasibility` (`spp42_span_a`) — **UNCHANGED.**
**2019–2022 rung:** `2026-09-19-spp-49-benchmark-membership` (`spp49_benchmembership_span`)
— **UNCHANGED.**
**LP spent: none. Shards launched: none. Bundles produced: none. Runs registered: none.
Matrix cell letters moved: none.**
Rule 32 `[R-SHARD]` (a): the parent never solves, and nothing survived phase 0 that needed an
LP. Rule 28(b): no mechanism was tested, so no cell is minted or moved — evidence is appended
to existing cells and the letters are untouched, the SPP-47 precedent.

Reproducible probe: `scripts/probes/_spp50_curtailment_headroom_census.py`
(legs `elasticity` · `floor` · `headroom` · `census`). Every number below is read from
committed artifacts — the registered run payloads, the committed bench parts, the bundles'
committed `hourly/` sidecars, CAMPD and EIA-930.

---

## 0. Headline

1. **The elasticity survives in SIGN and collapses as a COEFFICIENT.** On the corrected
   bench SPP-47's own 2019–2022 window reads `r = +0.911` but slope **+2.209 TWh per
   $/MMBtu** — **half** the +4.081 it read on the uncorrected actual. The keeper years alone
   read **+9.942**; all seven years read **+1.660**. A coefficient that moves 4.5× between
   windows describes the residual, it does not explain it.
2. **The coal↔CC pair does not close.** The antisymmetry is real (`r = −0.967` over seven
   years) but the pair SUM is **−3.365 TWh** on average and negative in 6 of 7 years. It is
   not a swap; something underneath it is short.
3. **That something is exact.** Over the seven registered SPP years, mean wind excess
   **+10.1444 TWh** against mean fossil miss **−9.9895 TWh** — they cancel to **+0.1549 TWh**,
   **1.5 %** of either. SPP's entire C1 fossil shortfall is, arithmetically, its wind excess.
4. **The wind input is NOT the defect, and this is the part that decides the lane.** The
   excess reconciles to the codebase's own published constant:
   `_spp_wind_reference_curtailment_rate` = **0.0965013** gives a gross-up of **×1.106808**,
   and the model's delivered/actual wind ratio is **1.1068** in 2019 and 1.1015–1.1065
   elsewhere. The bound is the measured **uncurtailed potential**, built from SPP's own
   published curtailment MW. Under rules 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` it is correct
   and must stay.
5. **The defect is that nothing spends it.** `renewables.py` states the construction's own
   precondition — *"The LP then curtails endogenously"* — and the LP curtails **0.00–0.48 %**
   of the potential against the 9.65 % it grossed up. **In MISO it curtails 0.00 % in all six
   registered years, to five decimals.**
6. **So Object A is largely the shadow of an already-routed object.** The lane's
   recommendation is to charter the handoff's ALTERNATIVE **S-2 / `R-bc`** — curtailment as an
   LP constraint whose **dual** reaches the zonal price — and to stop treating the coal↔CC
   elasticity as SPP's leading C1 object. **Killing a lever cleanly is a result**; this one is
   not killed, it is demoted and re-attributed.

Rule 30(c) is untouched: the rung reports and cannot decertify. SPP's headline stays
**CALIBRATED** on 2023–2025; the rung stays **NOT-YET** with failing set `{C1, C3a, C3b, C4}`.

---

## 1. The elasticity, re-fit (phase 0 item 1)

Model side = the payload's `gmModel` (the **scored** model volume). Actual side = the
committed bench `classFull` (the **scored** actual, with `benchmark_membership_vintage_union`
armed). Gas price = SPP's own EIA-923 **annual volume-weighted** delivered price, which is
what the LP's plants pay under `gas_plant_monthly_fuel_pricing`.

| year | gas vw $ | coal vw $ | spread | COAL_PRB miss | CC_REGULAR miss | pair sum |
|---|---|---|---|---|---|---|
| 2019 | 2.094 | 1.608 | 0.485 | **−9.0615** | +4.5010 | −4.5605 |
| 2020 | 2.091 | 1.597 | 0.494 | **−10.1860** | +3.7155 | −6.4705 |
| 2021 | 9.917 | 1.647 | 8.269 | **+5.1780** | −6.1756 | −0.9976 |
| 2022 | 7.054 | 1.913 | 5.140 | **+7.8548** | −6.9898 | +0.8650 |
| 2023 | 2.835 | 1.803 | 1.032 | −1.3538 | −3.4615 | −4.8153 |
| 2024 | 2.555 | 1.675 | 0.880 | −1.3509 | −3.7814 | −5.1323 |
| 2025 | 3.003 | 1.704 | 1.299 | +3.6086 | −6.0529 | −2.4443 |

| window | n | r | slope (TWh/$) | zero-crossing |
|---|---|---|---|---|
| 2019–2022 (SPP-47's own window, corrected bench) | 4 | **+0.911** | **+2.209** | $5.99 |
| 2023–2025 (keeper years) | 3 | +0.785 | **+9.942** | $2.77 |
| **all seven registered years** | 7 | **+0.731** | **+1.660** | $4.68 |

**The benchmark correction halves the slope** (SPP-47: +4.081 on the uncorrected actual). The
sign is robust; the magnitude is not a coefficient anyone can carry forward.

**The pair does not close.** `corr(COAL_PRB miss, CC_REGULAR miss)` is −0.993 / −0.994 /
−0.967 over the three windows — a near-perfect swap in *shape* — but the mean pair **sum** is
−2.791 / −4.131 / **−3.365 TWh**. In 2023 and 2024 **both** legs are short, which a swap
cannot produce. SPP-47's "almost perfect antisymmetric pair" holds; its implication that the
object is a *redistribution* does not.

---

## 2. Where the coal miss actually lives (phase 0 item 2)

### 2.1 By band — it is NOT a commitment question

Model TWh, 2020 → 2022 (the largest sign flip in the window):

| band | Δ TWh |
|---|---|
| `mustrun` | **+0.1197** |
| `committed` | **+15.4410** |
| `econlo` | +7.0530 |
| `econhi` | +5.7865 |
| `peak` | +0.5473 |

The must-run band is **flat**; the entire swing is in the price-responsive bands. Band
utilisation confirms there is no capacity limit anywhere: COAL_PRB `econlo` runs at 0.363 of
its observed peak MW in 2020 and 0.529 in 2022, so ~26 TWh of `econlo` headroom alone sits
unused in the short year. The model does not clear coal because gas is cheaper, not because
coal cannot run.

### 2.2 By hour — and here the sign-stable half appears

CAMPD is **gross** and the bench is EIA-923 **net**, so the comparison that carries the
finding is deliberately **scale-free**: hourly MW as a fraction of *that side's own* annual
max, which no reconcile constant can move.

| year | act min | act p1 | act p5 | mod min | mod p1 | mod p5 | h mod = 0 | h below act p1 | TWh below | C1 miss |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | 0.175 | 0.225 | 0.266 | 0.067 | 0.126 | 0.191 | 0 | 734 | 0.6210 | −9.0615 |
| 2020 | 0.094 | 0.149 | 0.198 | **0.000** | 0.044 | 0.098 | **43** | 1130 | 0.8552 | −10.1860 |
| 2021 | 0.081 | 0.147 | 0.202 | **0.000** | 0.000 | 0.071 | **251** | 784 | 1.2451 | **+5.1780** |
| 2022 | 0.096 | 0.142 | 0.200 | **0.000** | 0.000 | 0.067 | **293** | 778 | 1.2120 | **+7.8548** |
| 2023 | 0.094 | 0.134 | 0.172 | **0.000** | 0.000 | 0.070 | **205** | 864 | 1.0383 | −1.3538 |
| 2024 | 0.110 | 0.142 | 0.174 | **0.000** | 0.000 | 0.088 | **181** | 1029 | 0.9725 | −1.3509 |
| 2025 | 0.102 | 0.146 | 0.195 | **0.000** | 0.000 | 0.094 | **149** | 652 | 0.9352 | **+3.6086** |

**SPP's real PRB coal fleet never falls below 8.1–17.5 % of its own annual max in any year.
The model takes it to exactly 0.0 MW.** This is sign-stable in **all seven** years — including
the three where the annual C1 row reads coal **LONG**, which is the whole point: an annual
number cannot see it.

### 2.3 The zero-coal hours are one market state, not a scatter

| year | h coal = 0 | h mustrun = 0 | mean price | mean net load | wind ÷ its own max |
|---|---|---|---|---|---|
| 2020 | 43 | 43 | **−24.58** | 1,912 | **0.881** |
| 2021 | 251 | 251 | **−24.21** | 1,865 | **0.857** |
| 2022 | 293 | 293 | **−25.37** | 1,871 | **0.858** |
| 2023 | 205 | 205 | **−25.30** | 2,078 | **0.879** |
| 2024 | 181 | 181 | **−24.42** | 1,636 | **0.866** |
| 2025 | 149 | 149 | **−22.53** | 1,676 | **0.844** |

Price pinned at the wind PTC floor (`ira_ptc_wind = 26.0`), net load at a quarter of its year
p10, wind near its annual maximum — and the coal **must-run band itself at zero in every one
of those hours**. A must-run floor reaching zero is not a floor defect; it is the floor being
out-competed by supply the LP has no way to refuse.

---

## 3. The object that is actually there (phase 0 item 3)

`_spp_wind_reference_curtailment_rate` = **0.0965013** (SPP MMU Annual State of the Market
curtailed MW ÷ SPP's own 5-minute metered delivered MW, training window 2023–2025) →
gross-up **×1.106808**. `renewables.py` is explicit about why:

> `_forecast_uncurtailed_cf`, *not* the delivered net-of-curtailment series consumed as the
> upper bound. **The LP then curtails endogenously** and the modeled-vs-reported curtailment
> gap is a diagnostic, never a fit target.

It does not.

| year | wind model | wind actual | ratio | intended curt. | **LP curt.** | **spent** | fossil miss | cancel |
|---|---|---|---|---|---|---|---|---|
| 2019 | 85.2609 | 77.0330 | **1.1068** | 9.65 % | **−0.00 %** | **0.0 %** | −11.3362 | −3.1083 |
| 2020 | 90.7698 | 82.0300 | 1.1065 | 9.65 % | 0.02 % | 0.2 % | −9.4830 | −0.7432 |
| 2021 | 102.3605 | 92.8580 | 1.1023 | 9.65 % | 0.40 % | 4.2 % | −8.0869 | +1.4156 |
| 2022 | 118.3346 | 107.4350 | 1.1015 | 9.65 % | 0.48 % | 5.0 % | −7.9034 | +2.9962 |
| 2023 | 113.7320 | 103.0490 | 1.1037 | 9.65 % | 0.28 % | 2.9 % | −10.4090 | +0.2740 |
| 2024 | 120.7043 | 109.3170 | 1.1042 | 9.65 % | 0.24 % | 2.5 % | −11.2923 | +0.0950 |
| 2025 | 122.0280 | 110.4570 | 1.1048 | 9.65 % | 0.19 % | 1.9 % | −11.4159 | +0.1551 |

**Mean wind excess +10.1444 TWh · mean fossil miss −9.9895 TWh · cancel +0.1549 TWh (1.5 %).**

**This is not new for 2023–2025 and is not presented as such.** SPP-51b / 51c / 58 measured
the same thing (`0.261 / 0.223 / 0.174 %` against 9.65 %, a 40–60× miss) and the
`vre_reference_rate_curtailment_grossup` and `spp_curtailment_ceiling` matrix rows already
name it. What this lane adds:

* **the 2019–2022 rung, never measured before** — and 2019 curtails **literally nothing**;
* **the arithmetic identity above**, which is what demotes Object A;
* **independent reproduction at a different keeper** (SPP-51c/58 measured on
  `2026-09-09-spp-52a-fossil-offer`; this is keeper 12 and the SPP-49 rung);
* **and the fact that the water-fill is ALREADY ARMED in both**
  (`vre_curtailment_oversupply_allocation = True` in `spp42_span_a` **and**
  `spp49_benchmembership_span`) and the LP still spends 0.00–0.48 %. The allocation repair
  landed and the headroom is still not consumed.

### 3.1 It is curtailment-shaped, not a scale defect

A flat multiplicative defect gives a flat per-decile ratio. It does not:

| year | screened h | hourly r | d1–d5 ratio | d8–d10 ratio | rise | d8–d10 share of excess |
|---|---|---|---|---|---|---|
| 2019 | 0 | 0.9324 | 1.064 | 1.152 | +0.088 | **67.6 %** |
| 2020 | 0 | 0.9325 | 1.060 | 1.159 | +0.099 | **71.5 %** |
| 2021 | 0 | 0.9478 | 1.047 | 1.169 | +0.122 | **79.2 %** |
| 2022 | 0 | 0.9378 | 1.048 | 1.160 | +0.112 | **71.8 %** |
| 2023 | 1 | 0.9437 | 1.053 | 1.166 | +0.113 | **75.3 %** |
| 2024 | 0 | 0.9350 | 1.051 | 1.157 | +0.106 | **67.6 %** |
| 2025 | 0 | 0.9306 | 1.056 | 1.162 | +0.106 | **69.9 %** |

The model's hourly wind **shape** is good (`r` 0.931–0.948). The excess concentrates in the
top three actual-wind deciles — the hours SPP really curtails — in every one of seven years.

---

## 4. Cross-ISO census (phase 0 item 4)

Rule 25 `[R-ISO-SCOPE]`: a census informs where to look. **No verdict transfers, and none is
claimed.**

| ISO | n yrs | wind ratio mean | sd | min | max | mean excess | mean fossil | cancel |
|---|---|---|---|---|---|---|---|---|
| CAISO | 4 | 1.0105 | 0.0028 | 1.0074 | 1.0140 | +0.196 | −3.869 | −3.672 |
| ERCOT | 5 | 1.0014 | 0.0054 | 0.9942 | 1.0056 | +0.147 | +0.390 | +0.537 |
| **MISO** | 6 | **1.0515** | **0.0000** | 1.0515 | 1.0515 | +4.640 | −16.566 | −11.926 |
| NEISO | 6 | 1.0000 | 0.0001 | 0.9999 | 1.0002 | +0.000 | −0.303 | −0.303 |
| NWPP | 3 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | −0.000 | −11.857 | −11.857 |
| NYISO | 4 | 0.9960 | 0.0065 | 0.9865 | 1.0000 | −0.019 | +0.775 | +0.756 |
| PJM | 6 | 1.0000 | 0.0000 | 1.0000 | 1.0001 | +0.000 | +12.798 | +12.798 |
| **SPP** | 7 | **1.1042** | 0.0020 | 1.1015 | 1.1068 | **+10.144** | −9.990 | **+0.155** |

* **SPP is the only ISO whose wind excess is double-digit**, by an order of magnitude.
* **MISO reads 1.05147 in all six years with sd 0.0000** — exactly its own gross-up factor
  (`_miso_wind_reference_curtailment_rate` 0.048947 → ×1.051466). The LP curtails **0.00 %**
  there too. **Reported, not acted on: that is MISO's lane's** (rule 25), and the
  `vre_reference_rate_curtailment_grossup` row already records it.
* The four ISOs at ≈1.0000 are `delivered_pinned` — no gross-up, so no headroom to leave
  unspent. Their fossil misses (NWPP −11.9, PJM +12.8) are **unrelated** objects: their wind
  excess is zero, so nothing cancels.
* **Only in SPP does the wind excess account for the fossil miss** (+0.155 TWh residual).

---

## 5. Two probe-side artifacts, named so they are not refiled as defects

Both were plausible, both were wrong, and both were on **my** side — the SPP-45/47 discipline
applied to this lane's own work.

* **Leap years.** The model's calendar is a flat 8760 h; EIA-930's 2020 and 2024 carry 8784.
  Compared index-for-index the hourly wind `r` reads **0.4262 / 0.5046**; dropping Feb 29 from
  the actual restores **0.9325 / 0.9350**. I nearly filed a wind-shape misalignment defect
  against the model's two worst C1/C3 years. The model was never misaligned.
* **A corrupt EIA-930 hour in 2023.** The raw SWPP `WND` series carries one **3,589,445 MWh**
  hour against a ~35 GW fleet, which alone drove a naive 2023 `r` of **0.1172** — in a
  **keeper** year. The bench builder already screens it: raw annual 106.639 TWh minus that
  hour is **103.050**, which is the committed bench `wind` value **103.0490**. The screen is
  the benchmark's own convention and the probe adopts it rather than inventing one. **No
  defect here either** — but the raw file does carry the bad hour, so any future probe reading
  `SWPP_fueltype.parquet` directly must screen it.

---

## 6. What this lane did NOT do, and why

* **No mechanism was tested**, so under rule 28(b) **no matrix cell letter is minted or
  moved**. `docs/codebase-site/data/mechanism-matrix/SPP.js` is annotated only where this
  lane's measurement bears on an existing cell's evidence.
* **No LP, no shard, no registration, nothing deleted.** Nothing survived phase 0 that needed
  a solve: the finding is a measurement on committed artifacts, and the object it routes to is
  already chartered.
* **DO-NOT-REDO was respected.** The offer-curve band multipliers were not re-proposed as the
  closer (SPP-47 refused them on the sign change; §1 above **strengthens** that refusal — the
  slope is now window-dependent as well as sign-flipping, so condition (b) of rule 1's
  carve-out is further out of reach, not closer). `mid_vintage_exit_carry` and
  `benchmark_membership_vintage_union` were not re-litigated. SPP's 2023–2025 bench staleness
  was not rebuilt.
* **SPP-63's failure is not re-run.** §2.3 and §3 say *why* the CF-upper-bound channel could
  not work and why `R-bc` proper is different: wind is bid at `−ira_ptc_wind = −$26.000` and
  is a bounded decision variable, so **a unit held at its bound is never marginal**. Lowering
  the bound moves the bound; it never gives the LP a reason to spill. `R-bc`'s content is that
  curtailment enters as a **constraint whose dual reaches the zonal price** — a different
  object from a ceiling on the bound, and the handoff is right that repeating the ceiling
  would be repeating a known failure.

---

## 7. Successors, ranked

| # | object | status | why |
|---|---|---|---|
| **S-1** | **`R-bc`** — curtailment as an LP constraint whose **dual** reaches the zonal price | already routed; **this lane promotes it to first** | §3: it is the arithmetic source of SPP's whole C1 fossil shortfall (cancel +0.155 TWh over seven years), it is the only object that also addresses C3b's floor half and the coal-floor collapse of §2.3, and its target is a **published, zero-DOF** number already in the codebase (9.65 %) |
| S-2 | `R-ba` — the ST_GAS/CT_PEAKER merit-order inversion | already routed (SPP-63) | ST_GAS short **−3.94 to −8.66 TWh in every one of seven years** and **worsening** (−5.06/−7.12/−9.09 across 2023–2025); gas-price-independent, so `R-bc` will not close it |
| S-3 | the coal↔CC elasticity (Object A) | **measured, demoted, still no lever** | §1: sign-robust, coefficient not; §3 re-attributes most of its magnitude. It should be re-measured **after** `R-bc` lands, not chartered ahead of it |

**On S-3, the warning SPP-47 filed still stands and is now stronger.** Rule 1 `[R-STRUCT]`'s
offer-curve carve-out cannot reach it: the required correction changes **sign** between 2020
and 2022 *and* its magnitude moves 4.5× between windows, so no single year-invariant
multiplier exists. Recorded again so the next lane does not rediscover it.

---

## 8. The promotion question (rule 31 `[R-RETAIN]`), asked explicitly

**There is nothing to promote and nothing at risk of being lost.** No bundle was produced, no
LP was spent, no run was registered; the keeper and the rung are untouched at HEAD. The whole
deliverable is this document, the committed probe
`scripts/probes/_spp50_curtailment_headroom_census.py`, the calibration-log entry and the
matrix evidence annotation — all on `claude/spp-50-coal-cc-elasticity-k3x5in`. Nothing sits on
ephemeral disk and no shard branch holds anything. **Retrievability: everything is committed;
a promotion from this state would cost zero re-solves because there is nothing here to
promote.**

**What the owner is actually being asked to decide is which object SPP charters next:**

1. **Charter `R-bc` (recommended).** Curtailment as an LP constraint whose dual reaches the
   zonal price — NOT another ceiling on the CF upper bound, which §6 explains cannot work and
   SPP-63 already spent a screen proving. It needs its own PRECOMMIT. It is the only object
   that reaches C1's fossil shortfall, C3b's floor half and the §2.3 coal-floor collapse at
   once, and its magnitude target is published and carries zero free parameters.
2. **Or charter `R-ba`** (the ST_GAS inversion), which `R-bc` will not close and which is
   getting worse year over year.
3. **Or keep Object A at the front regardless.** This session's reading, which is a
   recommendation and not a decision, is that it should not be: after §3 it is mostly a
   re-description of the wind headroom, and the part that is genuinely its own has no
   admissible lever.

A fourth item is **reported, not proposed**: MISO carries the identical unspent gross-up
(1.05147, sd 0.0000, six years, 0.00 % curtailed, +4.640 TWh/yr). That is MISO's lane's call
under rule 25 and this lane does not touch it.

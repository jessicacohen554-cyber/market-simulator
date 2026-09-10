# RESULT — miso-251 SCREEN shard: the MISO keeper on held-out 2022, REPAIRED zonal demand

```
SHARD           : SCREEN (re-solve of held-out 2022 on the corrected MISO zonal allocation)
SESSION         : miso-251
BRANCH          : claude/miso251-screen2022
PINNED SHA      : 34b0e557440b5ce956c73c75889f07a17761ac92   (verified, never pulled/rebased)
RUN ID          : 2026-09-10-miso-251-screen2022
BUNDLE          : results/calibration/miso251_screen2022
KEEPER REPLAYED : 2026-09-09-miso-250-ep-gas  (results/calibration/miso_fuelvintage_A)
SUPERSEDES      : 2026-09-10-miso-251-tp2022
CHARTER         : docs/PRECOMMIT-miso251-holdout-ladder-2026-09-10.md
DETERMINATION   : NOT-YET
```

**Headline — the zonal repair did NOT move the merit-order miss.** The 2022
touchpoint re-solved on measured hourly zone shares instead of flat sample
averages, and every load-bearing criterion lands within noise of the first
solve: coal is still **+50.5 TWh** over actual, gas-CC still **−15.7 TWh**
under, price still **−13.8 %**, and the model still never prices an hour above
**$95.19/MWh** in a year with 116 actual RT hours above $200. The reason is
visible in the input itself: the repair **reallocates 0.73 % of MISO load
between zones and changes the ISO total by exactly 0.000 TWh**. It was
nonetheless the right thing to do — rule 14 `[R-ACCURATE]` requires the
accurate input whether or not it helps, and this now removes zonal allocation
from the list of candidate explanations for the 2022 miss.

**Rule 30(c): this does not touch MISO's headline.** MISO's determination is the
train-tier 2023–2025 verdict (`CALIBRATED`) and nothing else. A held-out year is
iterable model-SELECTION evidence: it cannot certify and it cannot decertify.
Since `[R-HOLDOUT]` was removed (2026-09-09) that is true of every year.

---

## 1. Hard stops — all three PASSED

| # | check | value read | verdict |
|---|---|---|---|
| 1 | `git rev-parse HEAD` | `34b0e557440b5ce956c73c75889f07a17761ac92` | **PASS** |
| 2 | keeper `meta.json` | `iso MISO`, `years [2023, 2024, 2025]` | **PASS** |
| 2 | `CC_REGULAR.committed` / `CT_PEAKER.peak` / `summer_wefor_share_override` | `1.1055` / `4.4` / `1.0599` | **PASS** |
| 3 | `parse_miso_shares(2022, zones)` | **`(6, 8760)`** real array, not `None` | **PASS** |

Recorded before the first LP in `docs/ADDENDUM-miso251-screen-phase0-2026-09-10.md`
and pushed as the heartbeat, so the record could not be written to fit the result.

## 2. Config verification — MACHINE-PROVEN

A full `meta.json` diff of touchpoint against keeper, excluding provenance keys,
returns **13 differing leaves, of which exactly two are tunables**:

```
miso_measured_reserve_requirements : True -> False     <- declared delta 1
miso_reserve_online_gated          : True -> False     <- declared delta 2
```

The other eleven are year-provenance and nothing else: `gas_prices.2022 = 6.45`
replacing the keeper's 2023/24/25 entries, four per-year `shared_inputs` content
hashes (campd, eia923, eia930, capacity_deliverability), `basis_sha`, and the
container dict that nests the two flags. **Offer curves confirmed unchanged in
`run_config.json`**: `CC_REGULAR.committed 1.1055`, `CT_PEAKER.peak 4.4`,
`summer_wefor_share_override 1.0599`. Nothing was added, dropped, tuned or swept.

The degradation behaved exactly as the PRECOMMIT §3 predicted and reproduced the
first solve's figures to the MW: RBDC market-wide requirement **3,382 MW at h0**
(MSSC + regulating, flat), **12 ORDC steps ($200–$3,500)**, 3,027 reserve-eligible
units; zonal families armed at **2,161 MW** (`miso_zonal_or_miso_south`) and
**2,982 MW** (`miso_subregional_or_midwest`).

## 3. The blocker from the first solve is CLEARED

`gen_touchpoint_attestation.py` exited **0**:

```
recipe identity   : PASS — 0 differing shared meta.json keys outside the provenance
                    set and the 3 VERIFIED declared source-forced degradation(s),
                    each of which the generator admitted only because its touchpoint
                    value is the field's ScenarioConfig default (a disarm, never an arm)
solve-surface drift: +0 -0 kwargs (keeper 7167b99a -> replay a3c806ef)
tier              : validation      holdout years : [2022]
```

The parent's declared-degradation channel is the right shape: it admits a delta
**only when the value is the ScenarioConfig default**, i.e. only a disarm, so it
cannot be used to smuggle an arm past the machine check. **C6 now reads PASS.**

## 4. A/B against the first solve — LIKE-FOR-LIKE, both re-scored at HEAD

The charter's table quotes the first solve as scored on the day. Two of its
entries are **not** effects of the zonal repair but of HEAD moving underneath
(the parent built the 2022 tail artifact and gave the generator its channel), so
quoting them as improvements would be wrong. **Both runs are therefore re-scored
at this SHA** and the honest column is the third:

| | first solve, as-scored | first solve, **re-scored at HEAD** | **this solve (measured shares)** |
|---|---|---|---|
| determination | NOT-YET | NOT-YET | **NOT-YET** |
| C1 fuelmix | FAIL, 4 classes | FAIL, 4 classes | **FAIL, 4 classes** |
| C3a price_mean | −13.3 % | **−13.9 %** ($60.55 vs $71.01) | **−13.8 %** ($61.19 vs $71.01) |
| C3b price_shape | NRMSE 0.279 | **0.209** | **0.209** |
| C3c price_tail | SKIPPED | **CAVEAT** 0 h vs 116 h (0.00×) | **CAVEAT** 0 h vs 116 h (0.00×) |
| C4 dispatch_corr | FAIL coal r 0.741 / NRMSE 0.325 | same | **FAIL coal r 0.744 / NRMSE 0.324** |
| C6 governance | UNATTESTED | **PASS** | **PASS** |
| C8 forced_share | PASS (CT_PEAKER 24.9 %) | same | **PASS (CT_PEAKER 24.8 %)** |
| C5a co2 (reported-only) | +14.0 % | same | **+14.1 %** |
| COAL_PRB | +37.09 TWh | same | **+37.05 TWh** |
| COAL_BIT | +13.44 TWh | same | **+13.48 TWh** |
| CC_REGULAR | −16.41 TWh | same | **−15.74 TWh** |
| CT_PEAKER | +8.14 TWh | same | **+8.52 TWh** |
| model max hourly LMP | $95.19 | same | **$95.19** |
| model hours > $200 | 0 (actual 116) | same | **0 (actual 116)** |

**Read the last column against the middle one.** C3a moves +0.1 pp, C3b is
byte-identical at 0.209, C4's coal r moves +0.003, and the four C1 classes move
by −0.04 / +0.04 / +0.67 / +0.38 TWh against misses of 37, 13, 16 and 8 TWh.
`max hourly LMP` is **identical to the cent**. Every criterion keeps its verdict.

> A note on C3a's basis: the HEAD scorer masks both sides to the **10 fully-staged
> months** (Nov and Dec are dropped as partially-staged actual — MISO-2022 RT
> coverage is 86.3 %), which is why the actual reads $71.01 rather than the
> annual $69.87 and why the first solve's as-scored −13.3 % becomes −13.9 %.
> On the unmasked annual basis this solve reads $60.66 vs $69.87 = **−13.2 %**
> against the first solve's $60.55 = −13.3 %. Both bases are given rather than
> reconciled silently; on either, the movement is ~0.1 pp.

## 5. The numbers the charter asked for

### 5.1 Per-zone annual demand TWh — the input that actually changed

| zone | flat sample-average (first) | **measured shares (this)** | delta |
|---|---:|---:|---:|
| MISO-East | 158.200 | **159.584** | +1.384 |
| MISO-Illinois | 44.155 | **46.669** | **+2.514** |
| MISO-Indiana | 87.526 | **88.421** | +0.895 |
| MISO-Plains | 90.465 | **90.034** | −0.431 |
| MISO-South | 177.077 | **174.346** | **−2.731** |
| MISO-West | 95.756 | **94.126** | −1.630 |
| **TOTAL** | **653.179** | **653.179** | **0.000** |

(`MISO_external` and `MISO_external_South` are seam nodes carrying 0.000 TWh of
native demand in both runs.)

**This table is the explanation for §4.** The ISO total is unchanged to three
decimals — as it must be, since the repair is an allocation fix — and the total
reallocated is **4.79 TWh, 0.73 % of MISO load**. The largest single zone move is
MISO-South at −2.73 TWh (−1.5 % of its own demand). A 0.73 % reshuffle of *where*
load sits cannot plausibly close a **+50.5 TWh coal / −15.7 TWh gas-CC** merit-order
gap, and it did not. What it does change is the hourly *shape* per zone (MISO-South's
share swings 21.3 %→36.0 % across the year, which the flat average erased) — and
even that moved the reserve-price hour count only from 6 to 3 of 8,760.

### 5.2 Generation TWh by class, model vs actual

| class | model | actual | delta | model % | actual % | Δpp |
|---|---:|---:|---:|---:|---:|---:|
| CC_CHP | 16.793 | 18.954 | −2.161 | 2.57 | 2.95 | −0.38 |
| CC_REGULAR | 111.509 | 125.567 | **−14.057** | 17.05 | 19.52 | −2.46 |
| COAL | 0.367 | 0.000 | +0.367 | 0.06 | 0.00 | +0.06 |
| COAL_BIT | 81.326 | 67.843 | **+13.483** | 12.44 | 10.55 | +1.89 |
| COAL_LIGNITE | 6.380 | 6.457 | −0.076 | 0.98 | 1.00 | −0.03 |
| COAL_PRB | 185.803 | 148.752 | **+37.051** | 28.42 | 23.12 | +5.29 |
| CT_CHP | 5.628 | 7.513 | −1.885 | 0.86 | 1.17 | −0.31 |
| CT_PEAKER | 22.640 | 14.125 | +8.516 | 3.46 | 2.20 | +1.27 |
| OTHER | 12.523 | 12.523 | 0.000 | 1.92 | 1.95 | −0.03 |
| OTHER_FOSSIL | 0.000 | 8.976 | −8.976 | 0.00 | 1.40 | −1.40 |
| ST_CHP | 3.181 | 4.988 | −1.807 | 0.49 | 0.78 | −0.29 |
| ST_GAS | 16.124 | 12.113 | +4.011 | 2.47 | 1.88 | +0.58 |
| biomass | 8.709 | 8.709 | 0.000 | 1.33 | 1.35 | −0.02 |
| hydro | 9.244 | 10.598 | −1.354 | 1.41 | 1.65 | −0.23 |
| import (net) | −22.583 | 0.000 | −22.583 | −3.45 | 0.00 | −3.45 |
| nuclear | 86.608 | 91.353 | −4.745 | 13.25 | 14.20 | −0.95 |
| oil | 0.000 | 0.384 | −0.384 | 0.00 | 0.06 | −0.06 |
| solar | 4.541 | 4.541 | 0.000 | 0.69 | 0.71 | −0.01 |
| wind | 105.062 | 99.920 | +5.142 | 16.07 | 15.53 | +0.54 |
| **TOTAL** | **653.856** | **643.314** | **+10.542** | | | |

Model column is the P1 `class_hourly_2022` sum; actual is the bench `classFull`.
The C1 scorer works on the grid-delivered net-of-BTM basis, which is why its
CC_REGULAR reads −15.74 rather than this table's −14.06 — both are given rather
than reconciled silently.

### 5.3 Monthly load-weighted price vector ($/MWh)

| month | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11* | 12* |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **model (this)** | 52.39 | 55.28 | 54.02 | 56.13 | 65.78 | 66.33 | 68.74 | 72.65 | 62.95 | 53.03 | 55.09 | 60.46 |
| model (first) | 52.23 | 54.93 | 53.83 | 55.99 | 65.73 | 66.48 | 68.99 | 72.58 | 62.90 | 53.01 | 54.93 | 59.85 |
| **actual RT** | 53.97 | 46.74 | 49.64 | 68.24 | 76.22 | 85.95 | 88.40 | 100.80 | 78.24 | 60.18 | 38.41 | 22.82 |
| actual DA | 52.69 | 49.53 | 49.52 | 67.20 | 77.36 | 90.19 | 89.13 | 98.22 | 83.68 | 58.68 | 55.49 | 55.24 |

\* Nov and Dec are **dropped by the scorer** as partially-staged actual (the RT
series is 86.3 % complete for 2022); the actual RT figures there — 38.41 and
22.82 against a DA of 55.49 and 55.24 — are coverage artifacts, not market
outcomes, and must not be read as the model beating actual in Q4.

The shape miss is the model's flatness, unchanged by the repair: actual RT swings
46.74→100.80 (2.16×) across the ten scored months while the model swings
52.39→72.65 (1.39×). That is the same signature as the zero hours above $200.

### 5.4 Price and scarcity

| | model (this) | model (first) | actual RT |
|---|---|---|---|
| load-weighted mean LMP | **$60.66** | $60.55 | $69.87 |
| simple mean (zone-hour) | $59.56 | $59.52 | $69.90 (DA) |
| max hourly (system LW) | **$95.19** | $95.19 | $1,082.57 |
| p99 hourly | $86.73 | $86.85 | $238.67 |
| hours > $100 | **0** | 0 | 1,034 |
| hours > $200 | **0** | 0 | **116** |
| hours > $500 / > $1000 | 0 / 0 | 0 / 0 | 11 / 1 |

Zone-hours above $200: **0 of 70,080**. Load shed (slack): **0.0 MWh**. Reserve
price positive in **3** hours of 8,760 (first solve: 6). Actual counts are a
lower bound at 86.3 % RT coverage.

### 5.5 Solve wall-clock

Wall clock **11 min 44 s** (02:35:09 → 02:46:53 UTC). Engine-reported
`total = 674.2 s`, decomposed `data_prep 41.0 s · solve_p0 388.0 s · markup 17.9 s ·
solve_p1 161.3 s · results_write 66.0 s`. P0 cold: 328,607 simplex iterations,
objective 8,480,380,127.97. P1 warm: 95,979 iterations, objective 8,641,900,117.11.
Container 15.7 GiB RAM + 8.0 GiB swap. **Inside the 20-minute shard cap**
(rule 32 `[R-SHARD]` (b)); the first solve took 12 min 14 s.

## 6. Did the zonal repair move the merit-order miss? — plainly, NO

It did not. Coal is over by **+50.53 TWh** (PRB +37.05, BIT +13.48) against the
first solve's +50.53 (PRB +37.09, BIT +13.44) — a net movement of **0.00 TWh**.
Gas-CC is under by 15.74 TWh against 16.41, a 0.67 TWh improvement that is 4 % of
the miss and leaves the class comfortably outside its band. All four C1 classes
keep their FAIL. The price level moves 0.1 pp, the price shape not at all, and
the scarcity tail is identical at zero hours.

**This is a useful negative result, not a wasted solve.** The first solve's
allocation was genuinely wrong and rule 14 `[R-ACCURATE]` obliged the repair
regardless of its effect on the residual; having made it, zonal load allocation
is now **eliminated** as a candidate explanation for the 2022 miss, and the
remaining candidates are unchanged by it. The repair also stands on its own
terms: 2022 now uses the same measured-share construction as 2023–2025, so the
holdout rung and the training years are no longer built on different inputs —
which was a defect in the comparison itself, independent of any score.

Two observations offered as evidence only, **not** as proposals (the parent and
the owner decide, per the charter):

1. **The miss is a merit-order/offer-level phenomenon, not a spatial one.** Coal
   running 22.8 % over while gas-CC runs 12.5 % under, with the price 13.8 % low
   and a completely flat price shape, is the signature of coal offering too far
   below gas across the whole year — a fuel-price or offer-curve relationship,
   which a zonal reallocation cannot reach and did not.
2. **2022 gas is `6.45 $/MMBtu` against the keeper's 2.54 / 2.19 / 3.52.** The
   keeper's offer bands were identified on three years whose gas sat at a third
   of 2022's level. Whether a band calibrated in that regime transfers to a
   6.45 regime is a real question about the recipe's range — but it is the
   parent's question, and answering it inside this shard would be exactly the
   tuning the charter forbids. **No config change is proposed here.**

## 7. What this shard did NOT do

No tuning of any kind (no offer-curve change, no flag beyond the two mandated
`--set`s), whatever the numbers said. No edit under `src/` or `scripts/`. No
`build_manifest.py` / `build_status.py` / `prune_iso_runs.py` /
`stamp_touchpoint_holdout.py` / `keepers/MISO.json` / `status/MISO.js` /
mechanism-matrix / calibration-log touch. No PR. **No result deleted** — the
superseded `results/calibration/miso251_tp2022` bundle is intact on local disk
(rule 31 `[R-RETAIN]`), and re-scoring it at HEAD is what made §4's like-for-like
column possible.

**Rule 31 note for the parent:** both bundles are on this container's local disk
and **will not survive its reclamation**. If the composed holdout ladder needs
either, take them now.

# FINDING: SPP-85, SPP coal outage basis. The keeper's in-merit filter was never on for SPP (zero LP, 2026-09-26)

Lane: SPP-85 (SPP coal outage-basis reconciliation). Parent: SPP-84
(`FINDING-spp-84-published-outage-vs-keeper-2026-09-26.md` §5.1).

Keeper: `2026-09-24-r-spp-corrected-inputs`, bundle `results/calibration/rspp_span`,
`basis_sha` `ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`. Session base: `origin/main` `56272c15`.

Probes:
- `scripts/probes/_spp85_coal_window_attribution.py`, whose numbers are in `results/calibration/_spp85_coal_window_attribution.json`;
- `scripts/probes/_spp85_fleet_delta.py`.

This is phase 0: zero LP, no solve. The solve that followed it is pre-registered in
`PRECOMMIT-spp-85-netload-mask-repair-2026-09-26.md`. Its outcome is in the RESULT doc.

## 0. Headline

1. **The charter's question has a code answer before a data one.** The deriver's revealed-availability
   filter looks up an EIA-930 net-load mask by ISO in `scripts/lib/outage_detect._ISO_TO_BA`. **SPP was
   never in that map.**
   - As a result, `high_load_mask("SPP", …)` returns `None`, and `filter_revealed_outages` keeps **every**
     detected span, which is its documented no-mask no-op.
   - The keeper extract's `.meta.json` records `min_inmerit_hours 24` and `no_inmerit_filter false`. **That
     setting was never in effect.**
   - SPP-20 listed `outage_detect._ISO_TO_BA` as owed to the outage lane (FINDING-spp-20, "six-tuples"),
     and it was never landed.
   - SOCO and NWPP carry the same missing key (recorded for their lanes; rule 25).
2. **Rule-14 misalignment test: SPP's published series is usable as the reference (§1).**
   - **Boundary aligned.** At plant grain, keeper 2024 coal equals EIA-860 SWPP operating coal: 29 of 29
     plants match. The one extra plant, Harrington 6193, converted off coal in 2024. Capacity is on a
     summer basis: 18.57 GW keeper vs 19.20 GW EIA summer on the matched set. SPP's own coal online +
     outage reaches p99 21.6–22.5 GW, **at or above** the keeper's 19.2–21.3 GW pmax, so SPP's footprint
     is not smaller than the keeper's.
   - **Definition partly aligned, and one premise corrected.** SPP defines Reserve Shutdown as a CROW
     **Planned Outage** "for a reason of Reserve Shutdown" (RC Outage Coordination Methodology §3.2.1). The
     portal product counts "submitted CROW outages and offered Commit Status = OUTAGE". So SPP-84's working
     hypothesis, that the published series *excludes* reserve shutdowns, is **not supported by SPP's own
     documentation**. Whether the portal aggregate filters the RS reason out is undocumented.
3. **The deriver's own frozen test, with the mask live, removes 0.57–1.12 GW of the 1.18–3.40 GW coal
   excess (22–52 %; §2).** Almost all of that removal is the short and partial layers. The ≥ 5-day layer
   loses only 46 coal windows in seven years.
   - The repair is **admissible**: zero new parameters, the committed invocation, and exogenous net load
     plus the unit's own CEMS.
   - It is **material**: +0.51–1.04 GW of mean coal availability in every year, on coal rows only (§3).
   - It was therefore taken to a pre-registered 7-year control + arm solve.
4. **What it does not reach.** A winter-heavy residual of 0.6–2.5 GW (DJF 1.1–4.1 GW) remains. It sits in
   ≥ 5-day dead stops through tight hours, which the frozen test keeps. The LMP test cannot separate them
   (§2.3), and SPP's definition would count them if CROW-registered. **This lane cannot close that residual
   admissibly.** The existing admissible construction for it is the merit-order guard
   (`campd_outage_merit_order_guard`, SRMC vs the revealed running-capacity cost). It rides the per-unit
   family (`campd_per_unit_attribution`) and is named as the successor.

## 1. Rule-14 misalignment test (FINDING-spp-84 §3.3)

### 1a. Boundary

| year | keeper coal pmax GW | SPP coal online, mean | SPP coal outage, mean | online + outage, mean / p99 / max |
|---|---|---|---|---|
| 2019 | 21.32 | 14.48 | 5.28 | 19.75 / 22.47 / 24.23 |
| 2020 | 21.06 | 13.06 | 4.98 | 18.03 / 22.15 / 29.93 (glitch hour) |
| 2021 | 20.22 | 14.20 | 4.59 | 18.79 / 21.72 / 22.62 |
| 2022 | 20.22 | 14.35 | 4.56 | 18.90 / 21.60 / 22.96 |
| 2023 | 19.50 | 12.49 | 4.91 | 17.40 / 20.90 / 22.12 |
| 2024 | 19.24 | 12.24 | 4.93 | 17.18 / 21.18 / 23.14 |

Sources: portal `hourly-generation-capacity-by-fuel-type` (Coal Market + Coal Self) and
`capacity-of-generation-on-outage` (Coal MW), on the model clock. The 2025 zips of both are empty.

Plant grain (2024): EIA-860 (2025 ER, end-2024) SWPP operating coal is 29 plants, 20.28 GW nameplate /
19.20 GW summer. The keeper carries all 29, plus Harrington (6193, 668 MW; converted to gas in 2024,
absent from the end-2024 coal list). None are missing. Per-plant keeper MW sits at or below summer capacity.
Where it differs by more than 50 MW, the keeper is the lower one: La Cygne, Jeffrey, Iatan, Welsh,
Sooner, GREC, Nebraska City and five others. **Aligned.**

### 1b. Definition

- **What SPP counts.** Portal product: "7-day outlook of MW of generation on outage by fuel type,
  including submitted CROW outages and offered Commit Status = OUTAGE". It is published daily at 08:00 CT.
  The last snapshot of each hour is ≤ ~24 h ahead, so a forced outage that starts intraday enters on the
  next publication.
- **Reserve Shutdown.** "Resources in SPP are considered to be in a Reserve Shutdown outage status when SPP
  has approved an outage request via the CROW tool … These resources will be reflected in Planned Outage for
  a reason of Reserve Shutdown." (SPP RC Outage Coordination Methodology, V2.0 §3.2.1 and Rev 3.2 §3.2.1.)
  **So an RS registered in CROW is an outage on SPP's own books.** The hypothesis that SPP excludes reserve
  shutdowns is not supported. It would need the portal aggregate to filter the RS reason, which is
  undocumented.
- **Derates.** CROW request type "Derate: Generator or Resource maximum capability is lowered from normal
  operation" (§3.4). It is a submitted CROW outage, so it is most likely in the aggregate. That is not
  confirmed from product notes. It is immaterial here either way: the keeper's partial layer is
  0.06–0.17 GW.
- **Verdict.** The series is **usable as the reference.** It measures "unavailable to SPP commitment". A
  unit that is economically off but offered with a Market status is not in it, and it should not be an
  outage in the LP either. The LP should decline it on its own economics.

## 2. Unit-level attribution (every keeper coal window 2019–2024)

Classes follow the lane's pre-declared order. A window counts as **filter-dropped** when it is absent from
its layer's `-netloadmask-` companion: the same deriver at the committed invocation with the SWPP mask live.

(A day-grain re-application of the filter to the extract's own dates over-drops. Re-expanding a window to
whole days pulls the unit's running return-to-service hours into the span, which is 451 vs 46 on the main
layer. Only the hour-grain re-derivation is the test.)

### 2.1 GW (annual mean) by class, and the keeper − SPP excess after removing each class in order

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| keeper coal unavailable (SPP-84 measure) | 6.46 | 7.54 | 7.18 | 6.96 | 7.22 | 8.33 |
| SPP published coal outage | 5.28 | 4.98 | 4.59 | 4.56 | 4.91 | 4.93 |
| **excess, keeper − SPP** | **1.18** | **2.56** | **2.59** | **2.40** | **2.31** | **3.40** |
| (i) ≥ 5-day windows the filter drops | 0.02 (3) | 0.10 (9) | 0.04 (6) | 0.01 (3) | 0.05 (6) | 0.14 (13) |
| (ii) partial plateaus (all filter-dropped) | 0.13 (36) | 0.06 (29) | 0.08 (17) | 0.17 (37) | 0.11 (18) | 0.17 (41) |
| (iii-a) short windows the filter drops | 0.42 (125) | 0.53 (158) | 1.00 (282) | 0.84 (208) | 0.50 (121) | 0.60 (155) |
| **excess after the repair (i + ii + iii-a)** | **0.61** | **1.87** | **1.47** | **1.38** | **1.64** | **2.48** |
| (iii-b) short windows the filter keeps | 0.29 (56) | 0.35 (81) | 0.48 (97) | 0.30 (62) | 0.17 (42) | 0.27 (56) |
| excess after also removing all short | 0.32 | 1.52 | 0.99 | 1.08 | 1.47 | 2.21 |
| (iv) ≥ 5-day windows the filter keeps | 4.98 | 5.83 | 4.77 | 4.60 | 6.21 | 5.93 |
| non-window unavailability (rebuild − windows) | 0.62 | 0.67 | 0.80 | 1.04 | 0.17 | 1.21 |

Parentheses give the window count. Window MW is the unit's share of its plant × the keeper plant's coal
pmax, × (1 − derate) for plateaus. Concurrent units are summed and clipped at the plant. The rebuild
reproduces the keeper's unavailable MW to within the non-window remainder.

### 2.2 Season

Excess, DJF / JJA mean GW:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| before | 1.65 / 0.72 | 3.14 / 1.32 | 3.51 / 0.64 | 3.04 / 0.46 | 4.35 / 0.08 | 5.16 / 1.29 |
| after the repair | 1.11 / 0.23 | 2.50 / 0.72 | 2.02 / 0.11 | 1.58 / 0.06 | 3.52 / −0.45 | 4.07 / 0.48 |

The repair takes the summer excess to about zero. **The winter concentration survives.** It is carried by
(iv), which are ≥ 5-day dead stops (median span CF 0.027) that stayed down through tight hours.

### 2.3 Window character (medians over 2019–24)

| layer / verdict | n | duration d | span CF | share of hours RT LMP ≥ plant offer | SPP coal outage on window hours, GW |
|---|---|---|---|---|---|
| ≥ 5-day, dropped | 40 | 7.75 | 0.100 | 0.286 | 4.13 |
| ≥ 5-day, kept | 1,381 | 12.10 | 0.027 | 0.296 | 5.39 |
| partial, dropped | 178 | 7.00 | 0.485 | 0.308 | 4.96 |
| short, dropped | 1,049 | 2.00 | 0.199 | 0.292 | 4.72 |
| short, kept | 394 | 3.10 | 0.138 | 0.481 | 4.02 |

- **Dropped windows are units that were producing.** Short windows show a median span CF of 0.20, which
  is a two-shifting unit read as "not a real run" by the 24 h run rule. Partial plateaus are running
  plateaus by definition, so the revealed test always drops them. That is also why MISO and NYISO carry
  **zero** partial rows at the same invocation.
- **The LMP measure does not separate the classes** (0.29 vs 0.30). It is not what distinguishes an
  outage from economic idling here.

## 3. Rule 13, both directions, and rule 23

- **Removing a window.** The construction is the deriver's frozen `filter_revealed_outages`:
  - keep a span when the unit stayed down (CF < 0.05) through ≥ `min_inmerit_hours` of the local
    top-15 % EIA-930 net-load hours;
  - or keep it when it is a ≥ 5-day full stop (mean CF < 0.02);
  - drop it when the unit ran through those hours.

  Every input is exogenous measured net load plus the unit's own CEMS operation. It regenerates for any
  year with an EIA-930 and CAMPD filing, and it applies identically to every ISO whose key is present.
  It is **not** "the unit showed zero output, so it was available". A ≥ 5-day dead stop is always kept.
- **Restoring availability** does not pin output. The unit becomes available, and the LP decides whether
  to run it on its own offer. The 1,049 dropped short spans are mostly units cycling at CF ≈ 0.2, not dead.
- **A realized-LMP removal test is refused.** Removing a window because the realized RT price sat below
  the unit's offer feeds the scored price (C3a/C3b) back into the input. That is an outcome, not a
  forward driver (rule 13). It is reported (§2.3) and never used. The admissible price-free test for
  economic lay-up is the merit-order guard: SRMC against the revealed running-capacity cost, with
  measured heat rate × delivered fuel and no LMP.
- **Rule 23.** No frozen setting changes. The change is the missing BA key, and the basis is SPP's
  published outage. All of this was fixed in the PRECOMMIT before any price effect was computed.

## 4. LP-input delta (fleet_only, keeper recipe at HEAD)

Coal-only in every year. 12 of 15 LP arrays are byte-identical. The rows below give Δ available GW
(mean) and COAL_PRB / COAL_LIGNITE TWh, 2019 → 2025:

| year | Δ available GW | COAL_PRB TWh | COAL_LIGNITE TWh |
|---|---|---|---|
| 2019 | +0.51 | 4.20 | 0.26 |
| 2020 | +0.66 | 4.74 | 1.07 |
| 2021 | +1.04 | 8.06 | 1.08 |
| 2022 | +0.90 | 6.61 | 1.30 |
| 2023 | +0.58 | 4.67 | 0.44 |
| 2024 | +0.84 | 6.21 | 1.16 |
| 2025 | +0.81 | 6.31 | 0.80 |

`min_gen` moves because the incumbent coal must-run floor re-applies in restored hours: +1.90 TWh (2021)
and +1.54 TWh (2024). No new floor is added (rule 19).

## 5. Successors (owner-gated)

1. **SOCO / NWPP**: the same missing `_ISO_TO_BA` key, so their committed extracts' in-merit filters are also
   inert. Their own lanes, their own BA mapping and their own measurement apply (rule 25).
2. **SPP winter residual (0.6–2.5 GW, DJF 1.1–4.1)**: `campd_outage_merit_order_guard` on the per-unit
   family. It needs a `-perunitmerit-SPP` extract and `campd_per_unit_attribution` (a larger change: the
   tranche companion rides the same gate).
3. **Definition closure**: an SPP data request or FAQ citation on whether the portal aggregate filters the
   Reserve Shutdown reason. It decides whether the winter residual is "RS excluded from the reference" or
   "economic offline outside CROW".

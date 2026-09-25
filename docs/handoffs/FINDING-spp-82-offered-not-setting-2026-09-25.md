# FINDING — SPP-82: the +7.5 GW "offered but not setting price" is OFFLINE, UNCOMMITTED capacity (zero LP, 2026-09-25)

Lane: SPP-82. Parents: SPP-79 (`FINDING-spp-79-c3a-is-a-cancellation-2026-09-25.md`), SPP-80
(`FINDING-spp-80-upper-tercile-premium-2026-09-25.md`), SPP-81 / SPP-81b
(`FINDING-spp-81-residual-upper-tercile-2026-09-25.md`, `FINDING-spp-81-upper-tercile-residual-2026-09-25.md`).
Keeper: `2026-09-24-r-spp-corrected-inputs`, bundle `results/calibration/rspp_span`, `basis_sha`
`ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`. Session base: `origin/main` `d5d5e0e8`.
Probe: `scripts/probes/_spp82_offered_not_setting.py`. Numbers: `results/calibration/_spp82_offered_not_setting_phase0.json`.
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched. Nothing landed under `data/`.**

## 0. Headline

1. **Source survey: FAILED, as the charter allowed. SPP publishes no resource-level RTBM dispatch,
   commitment status or economic limit that can be joined to the masked `historical-offers` RCodes.**
   The resource-level split (a)/(b)/(c)/(d) the brief asked for cannot be done. That is the
   charter's stated SUCCESS outcome, and the resource-level leg stops here (§1).
2. **The aggregate split can still be done, and it names the owner.** The RTBM offer file lists
   **every** resource in **every** interval, offline ones included: the resource count and the
   offered MW are flat through the day, while SPP's published hourly **online** capacity swings by
   8 GW. SPP also publishes hourly online capacity by fuel, capacity on outage by fuel, and
   generation by fuel. On SPP-81b's exact sample (reproduced to the hour count and to three decimals
   of position), the ≥ $10 MW priced at or below MEC must be at least `B10 − C_th` offline, and the
   floor **doubles**: **≥ 7.0 / 7.6 GW (2019 / 2020) → ≥ 15.8 / 15.2 GW (2023 / 2024)**. Meanwhile:
   - online thermal capacity is flat to down (31.9 / 31.4 → 30.7 / 31.2 GW);
   - online undispatched headroom is 4.1 → 4.9 GW (+0.7);
   - thermal generation fell (27.8 / 27.3 → 25.9 / 26.3 GW);
   - thermal capacity on outage is flat (17.3 / 14.4 → 13.8 / 16.5 GW).

   **The +7.5 GW sits in (c), offline and not on outage, i.e. available but uncommitted: central
   estimate ≈ +8 GW, all of the step.** (b) online at its limit or ramp-limited can hold at most
   +0.7 GW; (a) dispatched fell by ~1.4 GW. (d) is not separable, and SPP-81b already bounded
   congestion at ~+0.02 / +0.03 of the position. The worst-case rigorous floor on (c) is +2.3 GW,
   and the gap between that floor and the central estimate is reported as **unidentified** (§2.3).
3. **Five-minute ramp limitation does not own it.** Hourly-mean minus interval-median MEC rose
   $0.8 / 1.3 → $2.5 / 2.5, which is about **$1.5 of a $14–17 level (~9 %)**. Measured at the
   interval median, the stack position still steps 0.656 / 0.648 → 0.762 / 0.792, **+0.125 / +0.136
   against +0.12 / +0.15 at the mean (~8 % carried)**. Rule 8 `[R-8760]` keeps the model hourly
   anyway (§3).
4. **Not RT-only.** On the day-ahead market's own upper tercile, the DA MEC per MMBtu steps like RT's:
   DA 13.6 / 12.0 → 15.5 / 15.0 HR, against RT 13.4 / 12.7 → 15.8 / 15.9 HR. The same-hour
   DA-vs-RT comparison was selection-biased because the hours were picked on RT. Caveat: virtuals
   drive DA toward expected RT, so DA is not independent evidence that SCUC produces the step (§3).
5. **Rule 13: the owner is a commitment STATE. The model has no forward-reproducible driver for it
   today.**
   - The measured online capacity is a market OUTCOME. Pinning the LP to it is forbidden, the same
     class as pinning CEMS generation. The `online_capacity_envelope` "measured" variant was
     rejected in ERCOT for this reason.
   - The forward drivers of commitment (per-class start-up, no-load, min-run) are unpublished for
     SPP (SPP-73).
   - The LP is pure LP with no MIP, and P2 is archived.
   - The commitment bridges are `R` (DO-NOT-REDO).

   **No mechanism, no PRECOMMIT, no shard (§4).**
6. **Coupling (SPP-79): the owner cannot carry the pairing.** There is still no admissible
   upper-tercile lever. **SPP-79's constraint stands: a body lever alone breaks 2023–25 C3a** (§5).

## 1. Source survey (the hard stop)

Route: `GET https://portal.spp.org/file-browser-api/?fsName=<fs>&path=/&type=folder`, anonymous. The
full product list was enumerated from the portal's own menu, `GET /api/menu/`: 148 leaves, 119 of them
file-browser products. Every candidate that could carry resource-level status or dispatch was opened
and its header read:

| product (`fsName`) | grain | content | joinable to RCode? |
|---|---|---|---|
| `historical-offers` (`RTBM-/DA-ENERGY-OFFERS`, `-OR-OFFERS`) | resource, hourly (5-min from 2023) | `RCode, MW1..10, Price1..10` (+`Use_Bid_Slope` DA) — **no status, no limits, no dispatch** | is the RCode source |
| `market-clearing-rtbm` (2023-09 →) | system, 5-min | Generation, NSI, SMP, reserves, **Capacity Available** | no |
| `effective-limits` (2022 →) | constraint, 5-min | constraint limits, shadow price | no |
| `hourly-generation-capacity-by-fuel-type` (2017 →) | BA × fuel, hourly | **online capacity** (Coal Market / Coal Self / Gas / …) | no (aggregate) |
| `capacity-of-generation-on-outage` (2016 →) | fuel, hourly | outaged MW by fuel | no (aggregate) |
| `headroom-and-floorroom` (2017 →) | system, hourly | DA market / DA RUC headroom & floorroom | no |
| `fuel-on-margin` (2015 →) | system, 5-min | marginal fuel list | no |
| `resource-uplift-report`, `make-whole-payment-report` | settlement location, monthly | uplift $ by **named** location | no — names, not masked codes, monthly |
| `operator-initiated-commitments` (2019 →) | event list | OOME / manual commitments | no |
| `rtbm-lmp-by-location` | settlement location, 5-min | LMP / MLC / MCC / MEC | no (prices) |

**RCode persistence** (the join key, if one had existed): masked codes persist across days
(RTBM 2024-07-16 ∩ 07-17: 940 of 943; 2019: 764 of 764) and across products (2019: all 764 RTBM hex
codes appear, `0_`/`1_`-prefixed, in the same day's DA file). **The `0_`/`1_` prefix is not a status
flag.** It is constant for 927 of 935 resources within a day and does not flip day to day with
commitment. A hex code can carry both prefixes as separate simultaneous submissions. **Nothing
published carries a masked RCode except the offer files themselves.** Resource-level split:
**impossible from public data.**

## 2. The aggregate split (SPP-81b's exact sample)

Sample reproduced from `_spp81b_offer_stack_position.py` exactly: non-scarcity RT upper-tercile hours,
2 days / month ex-Feb, the hourly row (≤ 2022) or the :30 interval (2023+). Hours: **352 / 335 / 341 /
341**. Position: **0.670 / 0.671 / 0.788 / 0.824**, which matches SPP-81b to three decimals.

### 2.1 The offer file contains offline resources

On 2019-07-16 the offer file holds 764 resources every hour, offering 82.7–83.2 GW (all prices <
$500). Published online capacity runs 52.4 → 60.0 GW over the same day, and online gas alone runs
14.4 → 21.2 GW. 2024-07-16 shows the same pattern: 932–939 resources and 90.7–91.9 GW offered,
against online capacity of 63.8 → 74.9 GW. **The offered stack is the whole registered fleet, online or
not.** SPP-81b's caveat was right, and it is now quantified.

### 2.2 Per-year means over the sampled hours (GW; `B10` = ≥ $10 offered MW at or below MEC)

| | 2019 | 2020 | 2023 | 2024 |
|---|---|---|---|---|
| `B10`, offered ≥ $10 at/below MEC | 38.88 | 39.03 | 46.50 | 46.46 |
| `T10`, offered ≥ $10 total | 58.20 | 58.19 | 58.99 | 56.41 |
| resources in the offer file (min–max) | 763–768 | 780–819 | 923–973 | 915–969 |
| `C_th`, **online** thermal capacity (non-wind/solar) | 31.89 | 31.44 | 30.73 | 31.21 |
| of which online gas / online coal | 13.01 / 15.14 | 13.59 / 14.35 | 14.49 / 12.82 | 15.05 / 12.89 |
| `G_th`, thermal generation | 27.75 | 27.29 | 25.86 | 26.34 |
| `C_th − G_th`, online undispatched headroom | 4.14 | 4.15 | 4.87 | 4.87 |
| thermal capacity **on outage** | 17.25 | 14.36 | 13.82 | 16.52 |
| **`max(0, B10 − C_th)`, floor on offline MW below MEC** | **7.48** | **8.20** | **15.84** | **15.62** |
| net load (sampled hours) | 28.11 | 27.66 | 25.94 | 26.46 |

### 2.3 Attribution of the step (2023/24 mean − 2019/20 mean)

`B10 = (a) dispatched + (b) online-undispatched + (c) offline (+ (d) not deliverable, inside the
others)`. The step is **ΔB10 = +7.53 GW**.

| part | measured bound / estimate | share of +7.53 GW |
|---|---|---|
| (a) dispatched below max (online, generating) | tracks `G_th`: **−1.42 GW** | none (negative) |
| (b) online at max / ramp-limited / constrained-off | ≤ Δ headroom: **≤ +0.72 GW** | ≤ ~10 % |
| (c) offline, not on outage (uncommitted) | central **≈ +8.2 GW**; the floor `B10 − C_th` itself rises **+7.9 GW**; rigorous worst case **≥ +2.3 GW** | **≈ all (central); ≥ 30 % (worst case)** |
| outage (inside "offline", if outaged units still offer) | thermal on outage **−0.64 GW** | none |
| (d) not deliverable | not separable in public data; SPP-81b: congestion mass ≈ +0.02 / +0.03 of +0.12 / +0.15 position (≈ 1–1.5 GW-equivalent) | ≤ ~20 %, and it sits inside (a)–(c) |
| **unidentified** | the gap between the worst-case floor and the central estimate | 0 % (central) to ~70 % (worst case) |

- **The central estimate assumes** that online resources' MW offered below $10 (`L_on`: nuclear,
  coal must-offer blocks, minimums) did not shrink between the pairs. Then online ≥ $10 below-MEC
  MW can move only with `G_th` and headroom, and (c) = ΔB10 − Δ(a) − Δ(b) ≈ 7.53 + 1.42 − 0.72 ≈
  **+8.2 GW**.
- **The rigorous worst case** lets `L_on` shrink by the whole fall in online coal (−1.8 GW, as if every
  lost coal MW had been offered below $10). It also lets the 2019/20 online-below-MEC MW sit at its
  minimum. Then (c) ≥ 7.53 − [(C_th,23/24 − G_th,19/20) + 1.8] = **+2.3 GW**. It is reported so that
  the "unidentified" line is honest, not because it is plausible. Nothing in the fuel data moves
  online cheap MW by 5 GW at flat online capacity.
- **What the step is, in words:** the real offers did not move in dollars (SPP-81b), and the MEC rose
  $9–18 through them. The ≈ 7.5 GW priced between the old and the new MEC are almost all **resources
  that were available, not on outage, and not committed.** The RTBM clears only on the online stack,
  so those MW cannot set price, and the online stack is flat in size. **The keeper's LP has no
  commitment state on these units: it treats every non-outaged MW as dispatchable.** That is
  consistent with its flat position (0.635 / 0.667 → 0.646 / 0.654, SPP-81b) and with the
  class-uniform ~$10 gap (SPP-81b §1).
- Offline offered MW **in total** (`T_all − C_all`) fell 36.3 → 32.4 GW (it includes VER nameplate
  minus availability). So the offline fleet did not grow; it got **cheaper relative to the MEC**.

## 3. Five-minute leg, and DA vs RT

Five-minute system MEC was read from the first row of every `rtbm-lmp-by-location` interval file in
the sampled hours (range reads, 11.8–12.0 intervals per hour; the hourly mean of those intervals matches
the committed hourly MEC to ≤ $0.31).

| | 2019 | 2020 | 2023 | 2024 |
|---|---|---|---|---|
| hourly-mean MEC, $/MWh | 29.24 | 25.32 | 38.44 | 43.52 |
| interval-median MEC, $/MWh | 28.41 | 24.05 | 35.97 | 40.99 |
| mean − median | 0.83 | 1.27 | 2.46 | 2.53 |
| hours with mean > median + $5 | 4.0 % | 6.6 % | 17.0 % | 20.2 % |
| top-2 intervals' share of the mean's excess | 1.20 | 0.93 | 0.98 | 1.02 |
| **stack position at the hourly mean** | 0.670 | 0.671 | 0.788 | 0.824 |
| **stack position at the interval median** | 0.656 | 0.648 | 0.762 | 0.792 |

- **Sub-hourly spikes rose, but they are a minority of the object.** In every year the hour's
  mean-over-median excess is about the size the top two intervals alone contribute (ratio 0.93–1.20),
  and spiky hours tripled. Their
  size is about **+$1.5 of the +$14–17 level**. At the median interval the position still steps
  **+0.125 / +0.136**, against +0.119 / +0.152 at the mean. **Ramp-limited intervals carry ~8–10 %.**
  Rule 8 `[R-8760]` keeps the model hourly by design, so a sub-hourly owner would not be a model
  lever in any case.
- **DA vs RT.** On each market's own upper tercile (p67 ≤ price < p99, ex-Feb, per MMBtu of
  delivered gas), the step appears in both. 2019 / 20 / 21 / 22 / 23 / 24 / 25:
  - RT: 13.39 / 12.67 / 10.27 / 11.22 / 15.79 / 15.91 / 13.86;
  - DA: 13.59 / 11.97 / 9.88 / 11.25 / 15.50 / 15.04 / 13.30.

  On the RT-selected hours, DA reads 35.8 / 28.0 → 37.6 / 38.2 $/MWh against RT 29.2 / 25.3 →
  38.4 / 43.3. That gap is selection bias from picking the hours on RT, not an RT-only object. **The
  object exists at hourly grain in an hourly SCUC market.** Virtual trading drives DA toward
  expected RT, so this shows the object is not a sub-hourly artifact. It does not show that SCUC
  commitment creates it.

## 4. Rule 13 test

**Owner: offline, available, uncommitted capacity priced below the MEC. Structurally, a commitment
state.** Could the LP carry it as a forward-reproducible structure?

- **As a measured availability derate (online capacity pinned to SPP's published hourly online MW):
  NO.** Online capacity is the market's own commitment outcome. Feeding it back pins the backcast
  to an answer with no forward analogue. It is the same class as pinning CEMS generation, and rule 13
  forbids it outright. The ERCOT `online_capacity_envelope_measured` variant was rejected on the same
  ground (base row note).
- **As a commitment structure driven by forward inputs (start-up, no-load, min-run economics that
  make an offline CT/ST not worth starting for a $5–15 margin): ADMISSIBLE IN PRINCIPLE, UNAVAILABLE
  IN PRACTICE.**
  - SPP publishes no per-resource or per-class commitment-cost parameters. The offer files are
    energy only, and the MMU ASOM gives fleet-average physicals (SPP-73).
  - The engine is pure LP with no MIP, and P2 is archived.
  - The three P1-native bridges are `R` in SPP. `spp_gas_commitment_bridge`, `gas_commitment_bridge`
    and `commitment_floor_window_netload` stay `R`. A bridge raises floors (forces MW on); it does
    not remove cheap offline MW from the price-setting stack, which is what this object needs.
- **As an interior (deliverability) constraint:** not separable in public data, and at most
  about a fifth by SPP-81b's congestion bound.

**No admissible mechanism exists today. No PRECOMMIT, no G-DRIFT, no shard, no solve.**
The admissible structure is a **commitment-state representation with measured per-class commitment
costs**. That needs a new source (an SPP per-class start-up / no-load publication, or an FERC Form
/ EQR-class derivation) plus a design lane for commitment in an LP engine. Record it as an open
root-cause issue under rule 21 `[R-DOF]`, not as a parameter.

## 5. Coupling (SPP-79)

**It cannot carry the pairing.** SPP-79 needs an upper-tercile lever that raises 2023–25's upper
tercile by a measured driver, to pair with a body-price lever and keep C3a in band. The owner is now
named: uncommitted cheap capacity. It has no admissible representation (§4). **SPP-79's constraint
stands unchanged: a body lever alone breaks 2023–25 C3a.**

## 6. Rules and state

- **Rule 1:** no multiplier touched. The 0.93 channel is year-invariant, and this object is a
  2023+ commitment-state effect it cannot and must not absorb.
- **Rules 13 / 14:** every input used is measured and public. The only structural candidate
  (measured online capacity) fails rule 13 as an outcome.
- **Rule 19:** no floor or bridge proposed. A bridge is also the wrong sign for this object.
- **Rule 21:** the SPP 2023+ upper-tercile level is an open root-cause issue, owner named
  (commitment state), unrepresentable today.
- **Rules 29(b) / 31–36:** no arm, no solve, no shard, no bundle. Nothing to promote and nothing
  stranded.
- **Rule 28(b):** evidence was appended in `docs/codebase-site/data/mechanism-matrix/SPP.js` to
  `online_capacity_envelope` (U → stays U, the measured-pin route noted as rule-13 inadmissible),
  `measured_ramp_capability` (stays U; five-minute leg ~8–10 %) and `offer_curve_by_group` (K;
  the object is not an offer-level effect). The §5.7 DO-NOT-REDO note sits above SPP-81b's.
- **Data:** nothing landed under `data/`. Every source was range-read or downloaded to session
  scratch and re-derivable by the probe. GENCAP / outage / fuel-on-margin / headroom year zips
  are 0.27–0.75 MB each (`/<y>/<y>.zip` under each `fsName`), `--zdir` in the probe.

## 7. Successors (in the order they would settle the remainder)

1. **Keeper side of §2.3:** rebuild the keeper fleet (`fleet_only`, as SPP-81b's `--cache`). Measure its
   available ≥ $10 MW in these hours against SPP's online `C_th`. If it exceeds online by ~15 GW in
   2023–24 and ~8 GW in 2019–20, that confirms the LP clears on capacity the market kept offline.
   Zero LP, ~90 s per year.
2. **A commitment-cost source for SPP** (per class, forward-reproducible). Without one, §4's
   structure cannot be armed.
3. **2025:** `historical-offers` has no 2025 year zip (per-day files only, SPP-81b). Sampling it per
   day would add the third train year.

## 8. Housekeeping owed to the owner (reported, not attempted)

Leftover shard branches from the R-SPP lane need the owner to remove them (sessions cannot delete refs,
rule 33(f)): `claude/rspp-2019`, `claude/rspp-2020`, `claude/rspp-2021`, `claude/rspp-2022`,
`claude/rspp-2023`, `claude/rspp-2024`, `claude/rspp-2025`.

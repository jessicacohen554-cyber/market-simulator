# FINDING — SPP-81b: who is marginal in SPP's 2023–24 upper tercile, and does anything own the ~3.3 HR? (zero LP, 2026-09-25)

Lane: SPP-81, second session (labelled **SPP-81b** here and in the matrix, to keep it apart from the
first SPP-81 session's `FINDING-spp-81-residual-upper-tercile-2026-09-25.md`, which merged earlier
the same day and covered heat-rate mix, gas timing and ramp/uncertainty products).
Parents: SPP-79 (`FINDING-spp-79-c3a-is-a-cancellation`), SPP-80 (`FINDING-spp-80-upper-tercile-premium`).
Keeper: `2026-09-24-r-spp-corrected-inputs`, bundle `results/calibration/rspp_span`, `basis_sha`
`ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`. Pin for this session: `5aa54184`.
Probes: `scripts/probes/_spp81b_upper_tercile_marginal_unit.py` (legs A–F) and
`scripts/probes/_spp81b_offer_stack_position.py` (leg G).
Hour set: SPP-80's, exactly (RT p67 ≤ RT < p99, February excluded, scarcity hours dropped).
**No LP. No shard. No bundle. No `src/` edit. No `ScenarioConfig` field. No multiplier touched.**

## 0. Headline

**No structural mechanism owns the ~3.3 HR. Its owner is UNIDENTIFIED, but it can now be located
more precisely than SPP-80/81 left it.**

1. **It is not a heat rate.** Within each year, the real upper-tercile MEC barely tracks monthly
   delivered gas: the slope is **0.27 $/MWh per $/MMBtu in 2019–20**, while the keeper's is 3.3–4.8.
   Held at the base slope, the object is a **gas-independent level shift of +$13.8 / +$17.1 /
   +$20.9 per MWh** (2023 / 2024 / 2025) on a base intercept of $25.8. The "~3.3 HR" is that
   level divided by gas. No part-load, incremental-HR or heat-rate-mix lever can have this shape.
2. **The real market did not offer higher.** In SPP's own RTBM offer data
   (`historical-offers`, 22 sampled days per year), the thermal offer stack priced ≥ $10
   got **cheaper per MMBtu** in 2023–24: q75 falls from 12.4 / 11.3 HR (2019 / 2020) to 9.8 / 9.1,
   and q90 from 19.1 / 17.0 to 15.7 / 13.8. This agrees with the MMU's most-negative markups.
3. **It cleared deeper into that stack.** The share of ≥ $10 offered MW priced at or below the
   hour's MEC is **0.670 / 0.671 / 0.680 / 0.707 / 0.788 / 0.824** for 2019–2024. The offered stack
   is the same size (56–61 GW), net load in the sampled hours is lower (25.9 / 26.5 vs
   28.1 / 27.7 GW), and yet **about +7.5 GW more offered capacity sits below the price and does not
   set it**. The step times exactly with the residual (flat through 2022, up in 2023–24).
   **The keeper's own position is flat** (0.635 / 0.667 → 0.646 / 0.654).
4. **What that step is not, measured.** Binding-constraint mass predicts a deeper position within
   each year, but applied across years it explains only about +0.02 / +0.03 of +0.12 / +0.15.
   2022 had the most congestion and the lowest residual. Committed gas was **not** scarcer: CAMPD
   online gas rose 13.8 / 14.2 → 16.1 / 15.9 GW with flat headroom. Fast-start pricing (May 2022) is
   dismissed by the MMU's own account: "very little change" in fast-start revenue, ~2.9 GW, 95–96 %
   cleared day-ahead. The class-aware fuel donor pool is inert. Leg 3's time shift is absent.
5. **So the object is "offered supply that does not set price", not "cost".** Candidates that a
   public source could still settle: offline offers (the RTBM offer file does not flag commitment
   status); 5-minute ramp or dispatch-limit binding; distributed-reference pricing of bottled
   supply beyond what shadow-price mass captures. None is a forward-reproducible measured input
   today (rule 13), and none is a keeper lever.
6. **Coupling (SPP-79): it cannot carry the pairing.** No measured driver was found that raises the
   2023–25 upper tercile, so there is still no upper-tercile lever to pair with a body-price lever.
   **SPP-79's constraint stands: a body lever alone breaks 2023–25 C3a.** No PRECOMMIT is written,
   and no shard is launched.

## 1. Leg A — the keeper's price setter in the real upper-tercile hours

For each hour and zone, the setter is the **available** keeper row whose assembled offer
(`mc_base`, fleet_only rebuild) is nearest the zone's P1 price. It is matched when within $1/MWh:
97–99 % of hour-zones.

| | 2019 | 2020 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| RT MEC ex-scarcity, $/MWh | 28.01 | 25.16 | 41.00 | 43.35 | 46.17 |
| keeper price, $/MWh | 26.98 | 25.22 | 31.09 | 32.16 | 35.34 |
| **gap** | **1.03** | **−0.06** | **9.90** | **11.18** | **10.83** |
| setter is gas | 77.9 % | 76.6 % | 82.7 % | 83.9 % | 90.1 % |
| setter CT_PEAKER / ST_GAS / CC_REGULAR / coal | 49 / 15 / 12 / 19 % | 51 / 13 / 9 / 18 % | 48 / 23 / 9 / 12 % | 58 / 15 / 8 / 13 % | 54 / 21 / 13 / 8 % |
| gas setter's offer HR (0.93 × measured) | 9.80 | 9.93 | 10.14 | 10.23 | 9.62 |
| gas setter's fuel, $/MMBtu (own F923 or pool) | 2.51 | 2.29 | 2.82 | 2.92 | 3.49 |

- **The keeper already reproduces the real class shift.** Its gas-set share rose, and its setter
  offer HR rose +0.3, matching CAMPD's stack shift (+0.2 to +0.46, SPP-81). It is **not**
  dispatching a lower-HR class in those hours. By setter share it is *more* CT-heavy than the MMU's
  real-time marginal frequencies.
- **The gap is uniform across the keeper's setter class** (RT MEC − keeper price, $/MWh):

| keeper setter | 2019 | 2020 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| CT_PEAKER | 1.23 | −0.84 | 10.40 | 9.80 | 10.75 |
| ST_GAS | −0.61 | 0.64 | 9.75 | 11.77 | 10.76 |
| CC_REGULAR | 3.07 | 0.25 | 8.58 | 11.38 | 12.39 |
| coal | 2.62 | −0.05 | 12.03 | 15.09 | 2.69 |

  A merit-order or class defect would load on one class. This one lifts every class by about $10,
  which is a level signature.

## 2. Leg C — measured heat rate of the units that are ON vs the keeper's offer

CAMPD SWPP-BA units in the tercile hours, over each unit's dispatchable range (SPP-81's proxy),
MWh-weighted. The keeper's offer heat rate is for the same plant and class:

| | CC CAMPD / offer | CT CAMPD / offer | ST_GAS CAMPD / offer |
|---|---|---|---|
| 2019 | 7.71 / 7.17 (0.930) | 9.88 / 9.15 (0.926) | 10.67 / 11.15 (1.045) |
| 2020 | 7.76 / 7.15 (0.922) | 9.80 / 9.08 (0.926) | 10.50 / 10.72 (1.022) |
| 2023 | 7.66 / 7.19 (0.938) | 10.31 / 9.65 (0.936) | 10.51 / 10.55 (1.004) |
| 2024 | 7.74 / 7.14 (0.922) | 10.36 / 9.73 (0.939) | 10.53 / 10.50 (0.997) |
| 2025 | 7.76 / 7.19 (0.926) | 9.89 / 9.31 (0.942) | 10.43 / 10.40 (0.997) |

- **The measured inputs track CAMPD year by year.** For CC and CT, offer ÷ CAMPD is the 0.93
  channel and nothing else (0.92–0.94). It is flat across years, so it cannot own a 2023+ object.
- **Part-load goes the wrong way.** The incremental HR (per-unit OLS slope of heat input on MW) is
  **7.7–8.2**, against an average of **8.8–9.1** on the same units. An incremental-cost offer would
  *lower* the model's price. The average HR at tercile operating points rose only +0.2 / +0.3
  (9.05 / 9.11 vs 8.92 / 8.82).
- **Rules 13 / 14 verdict: no part-load or incremental-HR gap exists to repair.** A tuned adder
  would be forbidden anyway (rule 1).

## 3. Leg D / E — cost coverage, timing, wind

Each running CAMPD gas unit's cost is its CAMPD heat rate × the keeper's own F923 plant-month gas
price, plus the keeper's VOM for its class.

| | 2019 | 2020 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| MEC − p90 dispatchable-unit cost, $/MWh | −6.99 | −5.81 | **+2.62** | **+0.39** | −0.50 |
| hours MEC exceeds EVERY running gas unit's cost | 3.2 % | 2.3 % | **9.2 %** | **14.5 %** | 9.4 % |
| keeper price − p90 cost, $/MWh | −8.02 | −5.75 | −7.29 | **−10.79** | **−11.33** |
| tercile hours in HE17–21 | 27.3 % | 30.7 % | 28.7 % | 30.1 % | 28.9 % |
| tercile hours in HE10–15 | 37.8 % | 40.9 % | 39.6 % | 39.6 % | 36.5 % |

- **Hour timing did not shift.** Evening-ramp hours are 27–31 % of the tercile in every year. Leg 3's
  hypothesis (upper-tercile hours moving into the post-solar evening ramp) is **not supported**.
  The commitment/bridge cells (`spp_gas_commitment_bridge`, `gas_commitment_bridge`,
  `commitment_floor_window_netload`) stay **R**: this lane brings no new evidence against the SPP-44 /
  SPP-73 DO-NOT-REDO notes.
- **Wind share does not own it.** On delivered gas, the premium over 2019–20 is present in every
  wind-share band: +2.2 / +3.7 / +4.2 / +3.1 HR in 2024 for ≤ 15 / 15–30 / 30–45 / > 45 %.
- **The keeper's gap has two parts, and only one is SPP-80's residual.**
  - The first part is the real price rising above the running fleet's cost. Measured against a
    2019–20 base, it is +9.0 / +6.8 / +5.9 $/MWh in 2023 / 2024 / 2025.
  - The second part is the keeper's price sitting under the real p90 unit's cost. It runs 19–23 % in
    2019–23 and **24–25 % in 2024–25**, about +3.9 / +4.4 $/MWh on the base. This is a year-invariant
    0.93 channel acting on a higher cost level, plus the keeper's cheaper setter mix. It is the
    reason 2025's gap ($10.8) matches 2023–24 even though SPP-80's 2025 residual is small (+1.87 HR).
  - **Reported at full magnitude. Not tuned.**

## 4. Leg G — the market's own offer stack (new source, zero LP)

SPP `historical-offers` RTBM energy offers are range-read from the year zips; nothing is written
under `data/`. The sample is 22 days per year: the 2 days per month (ex-Feb) carrying the most
tercile hours. Each day contributes every tercile hour, one snapshot per hour (the hourly row
through 2022, the :30 five-minute interval from 2023). The stack is every offer segment priced
in [$10, $500), MW-weighted.

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|---|
| hours sampled | 352 | 335 | 304 | 332 | 341 | 341 |
| MEC, $/MWh | 29.2 | 25.3 | 42.0 | 81.2 | 38.4 | 43.4 |
| offered ≥ $10 GW | 58.2 | 58.2 | 60.6 | 60.6 | 59.0 | 56.4 |
| q50 / q75 / q90 ÷ gas (HR) | 8.1 / 12.4 / 19.1 | 7.9 / 11.3 / 17.0 | 6.2 / 9.3 / 13.6 | 7.4 / 10.8 / 16.6 | 7.3 / 9.8 / 15.7 | 6.8 / 9.1 / 13.8 |
| MEC ÷ gas (HR) | 11.4 | 10.8 | 8.8 | 11.0 | 12.6 | 14.4 |
| **MEC position in the stack (share of MW at or below MEC)** | **0.670** | **0.671** | **0.680** | **0.707** | **0.788** | **0.824** |
| MW at or below MEC, GW | 38.9 | 39.0 | 41.2 | 42.9 | 46.5 | 46.5 |
| sampled net load, GW | 28.1 | 27.7 | 27.2 | 27.0 | 25.9 | 26.5 |
| binding shadow-price mass, $/interval | 604 | 534 | 1,063 | 1,906 | 1,102 | 1,715 |
| within-year OLS: position per GW net load / per $1k binding mass | .009 / .063 | .011 / .076 | .010 / .025 | .010 / .009 | .007 / .035 | .008 / .040 |
| **keeper's position in its own available ≥ $10 stack** | 0.635 | 0.667 | — | — | 0.646 | 0.654 |

- **Offers did not rise, in dollars or per MMBtu.** In dollars, q75 / q90 read 33.1 / 50.6 and
  26.7 / 40.1 in 2019 / 2020, and 30.5 / 48.4 and 27.8 / 42.3 in 2023 / 2024. That is flat, while
  MEC rose from 29.2 / 25.3 to 38.4 / 43.4. Per MMBtu they fell. Offer ÷ gas is diluted when gas is
  high (2021–22 read cheaper for that reason), but gas moved only +$0.8 between these pairs, so the
  dollar comparison is the clean one.
  - The cost-content hypothesis SPP-81 ranked first (mitigated-offer content, fuel-cost-policy
    premiums) predicts rising offers. At the stack level it is **refuted**: whatever cost sits
    inside real offers, the offered stack did not move up.
- **The price climbed the stack instead.** +7.5 GW more offered MW sat below the price at lower net
  load. Those MW were offered and cheaper than the MEC, and did not displace the setter.
- **The keeper cannot reproduce this.** Its position is flat, because its available stack has no
  offline-offer, 5-minute-ramp or interior-constraint dimension that could strand cheap MW.
- **Congestion (SPP-80's dismissal needs a correction).** SPP prices MEC at a distributed load
  reference, so bottled supply can raise the MEC while the hub's MCC stays near zero. **SPP-80's
  "hub MCC ≈ 0, so not congestion" does not by itself exclude congestion from the MEC.** Measured
  here, though, shadow-price mass explains only ~+0.02 / +0.03 of the step (within-year slope ×
  cross-year Δ, net of the net-load drop), and 2022 is a counter-example. Congestion is at most a
  minor share.
- **Committed gas (CAMPD, tercile hours):** online 13.8 / 14.2 / 13.4 / 15.9 / 16.1 / 15.9 / 15.5 GW
  (2019–25), headroom 3.3 / 3.3 / 4.0 / 4.7 / 3.8 / 3.6 / 3.9 GW, gas output 10.5 / 10.9 → 12.3 / 12.3
  GW. The committed fleet was not tighter, but gas replaced about 1.5 GW of other supply at flat
  net load.
- **Caveats, stated.**
  - The offer file carries no commitment status, so offline resources' offers are inside the stack.
    That is exactly why the level of "position" is not a clearing proxy; only its change is read.
  - 2023+ is sampled at one 5-minute interval per hour, against an hourly row before 2023, and
    that switch coincides with the step. **Checked and cleared.** On a 2024 re-cut (1 day per
    month, 179 hours), the :05, :30 and :55 snapshots give the identical position 0.845 and q90
    $43.33 / 43.34 / 43.33. Offers are effectively constant within the hour, so the snapshot choice
    does not move the stack.
  - 2025 has no year zip (HTTP 404) and is not sampled.

## 5. Leg B — class-aware fuel donor pool (an existing mechanism, never tested in SPP)

The SPP keeper prices every non-reporting gas plant from a class-blind **zone** pool. SPP-46
measured every SPP row's state field as empty, so the state tier is void. MISO arms
`class_aware_fuel_price_fallback` for exactly this reason, as a CC-dominated pool under-prices
CTs. This lane forced it on in a fleet_only rebuild (runtime patch, probe only) and measured:

| | 2019 | 2020 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| gas rows repriced | 393 | 420 | 398 | 410 | — |
| CT_PEAKER fuel (avail-weighted, tercile), base → class-aware | 2.85 → 2.93 | 2.40 → 2.43 | 2.96 → 2.90 | 3.18 → 3.13 | — |
| price shift, same setter row, $/MWh | +0.44 | +0.20 | −0.04 | −0.73 | −0.55 |
| price shift, merit re-clear at fixed quantity, $/MWh | +0.32 | +0.15 | +0.02 | −0.03 | −0.51 |

**Inert-to-adverse for this object.** It moves 2019–20 up and 2023–25 flat or down, the opposite of
what the object needs. It is a rule-14 input question in its own right. It is **not** tested as an
arm, and the `gas_plant_monthly_pricing` cell stays K.

## 6. What is left, and what could still identify it

**Owner of the ~3.3 HR, at full magnitude: UNIDENTIFIED.** It is a gas-independent real-time price
level of about +$14–17/MWh on the upper tercile (2023–24 vs 2019–20). The market reached it by
clearing about 12–15 points deeper into an offer stack that got cheaper per MMBtu, with about
+7.5 GW of offered sub-price capacity not setting price. It is **not** heat rate, part-load, class
mix, gas basis/timing, markup, scarcity, reserve procurement, hour timing, wind share, committed-gas
tightness, fast-start pricing or the fuel donor pool. Congestion carries at most about a fifth.

Sources that could settle the remainder, in order of how directly they would:
1. **Commitment status of offered resources in RTBM.** Is the +7.5 GW offline? SPP publishes
   resource-level RT dispatch with a lag (masked, `RTBM-…` in the Marketplace). Joining masked
   RCodes across the offer and dispatch files would split "offered below MEC" into
   dispatched / online-at-limit / offline.
2. **5-minute ramp-limited intervals.** If the hourly-mean MEC is driven by a minority of
   ramp-constrained five-minute intervals, the stack position of the hourly mean overstates the
   typical interval. The five-minute LMP components and the five-minute offers are both published.
3. **Distributed-reference congestion beyond shadow-price mass.** SPP's reference-bus / load-weight
   convention is published, so a successor can compute the MEC's own congestion loading directly.

**Rule 13 test.** (1) and (3) would be measured, forward-reproducible inputs only if they reduce to
a **structure** the LP can carry (a commitment state, an interior constraint). (2) is sub-hourly,
and rule 8 `[R-8760]` makes the model hourly by design. **Nothing here is a lever today. No
PRECOMMIT, no shard, no solve.**

## 7. Rules and state

- **Rule 1:** no multiplier touched. The object is year-specific and additive, so the carve-out's
  single year-invariant multiplier cannot be the channel. Choosing a value to close it would be the
  forbidden fitted selection.
- **Rules 13 / 14:** every input examined is measured. None moves the right way enough to be a
  candidate.
- **Rule 19:** no new floor or bridge proposed.
- **Rule 29(b) / G-DRIFT:** not engaged (no arm).
- **Rules 31–36:** no solve, no shard, no bundle. Nothing to promote, and nothing is stranded
  (rule 34(e)).
- **Rule 28(b):** evidence was appended in `docs/codebase-site/data/mechanism-matrix/SPP.js` to
  `offer_curve_by_group` (K), `measured_ct_heat_rates` (K), `gas_plant_monthly_pricing` (K; the
  class-aware leg) and `measured_ramp_capability` (U). **No cell verdict changed.** The §5.7
  DO-NOT-REDO note sits above SPP-81's.
- **Data:** nothing landed under `data/`. The offer sample is re-derived by the probe from the
  portal. The three SOM PDFs read for fast-start pricing (2022 p.91, 2023 pp.93–96, 2024 pp.79–81)
  match SPP-80's sha256 table and are not committed.

## 8. Housekeeping owed to the owner (reported, not attempted)

Leftover shard branches from the R-SPP lane, already landed through `rspp_span`, need the owner to
remove them (sessions cannot delete refs, rule 33(f)): `claude/rspp-2019`, `claude/rspp-2020`,
`claude/rspp-2021`, `claude/rspp-2022`, `claude/rspp-2023`, `claude/rspp-2024`, `claude/rspp-2025`.

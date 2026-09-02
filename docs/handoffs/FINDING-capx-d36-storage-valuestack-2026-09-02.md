# FINDING — capx D36: why the NEISO storage value stack clears nothing for 24 years — the arbitrage leg is the short term in every year, by $50–150/kW-yr; the RA leg is second-order and is the D28/D33 position object, not a second storage mechanism

**Lane:** capx D36 (Phase-0, decompose-only), charter `docs/handoffs/capx-director-prompt-pack-2026-08.md`
§D36 (r#27; GOLDEN-2 routed item 1, the D25 §6.3 route). **Docs only, ZERO solves.** Every
number below is read from the committed golden-2 bundle (`results/ff-t3-neiso-golden/bau/`,
cache key `706e7ba8e6582d42`, run_config git `f0a13bf5` on basis `5083e29e`, read at HEAD
`69b6c8d9`) or computed by re-running the entry screen's own arithmetic
(`src/market_sim/model/storage.py` — `compute_storage_annual_cost`, `estimate_capacity_value`,
`_degradation_cost_per_mwh`, `estimate_storage_revenue`) on that bundle's ledger, on the
NEISO keeper's committed hourly sidecars, and on the raw ISO-NE SMD hourly LMP files. No
mechanism, no `ScenarioConfig` field, no matrix cell, no keeper/board/verdict/marker/FC-row
write. The reconstruction script and its two CSV outputs are reproduced in §9; the four charts
are committed under `docs/handoffs/d36/`.

**Collision check at write:** D33 (NEISO position lane) has NOT landed — no
`FINDING-capx-d33-*` exists on `origin/main`; its charter is cited for the position half.
The golden-2 bundle did not move under this lane (same cache key and run_config sha as the
golden-2 finding §5).

## 0. Verdict (one paragraph)

The stack clears nothing in 2027–2049 because **the energy-arbitrage leg is short in every
year, for every admissible technology, by more than the RA leg could ever supply** — and the
shortfall is not a position artifact. Reconstructed exactly: the annualized cost of the
cheapest admissible machine is $117–157/kW-yr (iron-air 100 h) and $126–157/kW-yr (li-ion
4 h) across the horizon; the RA leg pays $0–88/kW-yr for iron-air and $0–53/kW-yr for li-ion
4 h, oscillating with the D28 entering-position swing; so the arbitrage the screen must find
is **$31–151/kW-yr (iron-air) and $77–154/kW-yr (li-ion 4 h)**. The screen's own arbitrage
formula, run on **real ISO-NE zonal LMPs for 2023, 2024 and 2025**, yields at most
$53/kW-yr for li-ion 4 h and $30/kW-yr for iron-air (real-time; day-ahead is roughly half) —
below the requirement in **every one of the 24 years, at the real market's price shape**.
On the NEISO keeper's own modelled 2023–2025 prices the same formula yields $0.1–5/kW-yr,
i.e. the model's price surface offers an order of magnitude less spread than the market's
(the C3c-ledgered flat tail seen from the storage side). And the forecast screen sees neither:
under `entry_lookahead_reprice` (the golden's posture) it prices arbitrage on a **static
merit-stack re-price** with **no scarcity tail** (`scarcity_pricing_enabled=false`), **no
negative prices** (floored at the cheapest unit's cost) and **no locational spread**
(zone-flat) — the two ends of the spread storage lives on are absent by construction, and the
LP's own 2,446 hours ≥ $100 and 6.6 % negative hours in 2050 never reach the screen. Entry
finally happens in 2050 because the carbon-escalated stack (RGGI $132/t) plus a 33 GW peak
widens the static-stack spread enough for the one machine whose per-cycle arbitrage does not
carry a $20/MWh degradation charge: the 100-h iron-air at a $1.67/MWh degradation cost. **The
RA leg is the same object D28 characterized and D33 is chartered to repair — one seam, one
position, one curve — but it is a second-order term for storage: even at net-CONE it caps
at $78/kW-yr (iron-air) / $47 (li-ion 4 h), and at the real FCAs' cleared positions
(1.033–1.045, $24–43/kW-yr) it pays only $19–31 / $11–18.** A D33 repair therefore cannot
make the stack clear earlier; in the golden's near-requirement years (2029–2031, 2035,
2047–2050) it would pay storage *less*. Conclusion: **D36 and D33 are two mechanisms** —
D33 owns the position; the storage divergence is owned by the arbitrage leg's price object
and by the cost side. The market's early build (AEO 1.76 GW by 2030; MA/CT procurement
statutes) is not a merchant arbitrage-plus-FCA outcome, so the honest answer for the corridor
row is a **DISPOSITION** (state-procurement channel, the D25 mechanism-3 family), plus two
identified rule-13 repair routes on the merchant stack itself (§7) that would move the level
without reaching the AEO number.

## 1. The mechanism as the golden exercised it (what exactly was evaluated)

`apply_storage_new_entry` (`storage.py:1817`) runs once per year 2027–2050 (2026 is the base
fleet) with, at the golden's run_config:

| term | construction at the golden posture | source |
|---|---|---|
| price object | `prior_results.price_signal` = the **look-ahead stack re-price** for the entering year (`entry_lookahead_reprice=true`, `entry_price_signal_alpha=1.0` pass-through): next year's net load searched into THIS year's merit stack of **time-mean full variable cost** against availability-derated capacity (`runner._lookahead_reprice_signal`, :605); `scarcity_pricing_enabled=false` ⇒ **no ORDC adder**; unified lookahead off ⇒ prior-year *realized* VRE as the net-load VRE term, no storage shave; output tiled zone-flat | `runner.py:3477, 3950-3952, 3993, 1983-1986` |
| arbitrage leg | `estimate_storage_revenue`: one cycle per window of `ceil(duration/12)` days (4 h/8 h/10 h/12 h → 365 daily cycles; 100 h → 40 nine-day cycles), charge the cheapest `d` hours, discharge the dearest `d`, best zone per window, margin = disc − chg/RTE − degradation, floored at 0 | `storage.py:1436` |
| degradation | `capex_per_kwh × 1000 / cycles × 0.25` ⇒ li-ion 4 h **$22.63/MWh**, 8 h $19.72, 12 h $23.43, flow $5.83, **iron-air $1.67** | `storage.py:1577`; `STORAGE_DEGRADATION_REPLACEMENT_FRACTION` |
| RA leg | `capacity_price_per_firm_mw_yr` at the ONE `curve_reserve_position` computed on the entering fleet (`runner.py:1830`) × `ELCC(duration)` (generic NREL/E3 table — NEISO publishes no storage class rating) × `(1 − 2,635/13,000)^1.5 = 0.712` (saturation derate on the existing PS + battery fleet) × deliverability factor 1.0 (gate off) | `storage.py:1596`; `capacity_market.py:715` |
| capacity price | NEISO FCA curve, **2027–2028 vintage hold-last for every screen year** (`resolve_demand_curve_vintage`), net-CONE $108.94/kW-yr, zero-cross 1.0582, cap 1.600 × net-CONE at 0.982 | `capacity_market.py:988, 1714-1734` |
| AS leg | `as_revenue_enabled=false` ⇒ **$0** in every year (NEISO has no registered AS rate anyway) | `ancillary.py:82` |
| cost | `capex_per_kw × (cum_GW/ref_GW)^(−lr) × (1 − 0.30 × ITC-fraction) × CRF(r=5.675 % real, 20 yr = 0.0849) + FOM`; ITC fraction 1.0 through 2033, 0.75 / 0.50 in 2034 / 2035, 0 from 2036; `cum_GW` = global reference + global annual adds × (year − 2026) (no local storage build to add before 2050) | `storage.py:1652`; `ira.py:299`; `WRIGHT_REFERENCE_GW`, `GLOBAL_ANNUAL_DEPLOYMENT_GW` |
| gates | D-2 availability (`STORAGE_TECH_AVAILABLE_YEAR`): li-ion ×3 (2012), flow (2017), iron-air (2024) admissible in every screen year; **compressed_air fail-closed (None) — the only gate that excluded anything**; D-3 cost-normalized rank: `margin / capex_per_kw`, **sign-preserving — it reorders clearing techs, it cannot create or remove a clearing** (its own docstring says so, `storage.py:1789`) | `storage.py:1756, 1789` |
| caps | budget = min(1,200 MW/yr, 13,000 − existing); per-tech share cap 0.6 × budget = 720 MW | `STORAGE_ANNUAL_BUILD_CAP_MW`, `STORAGE_TECH_BUILD_SHARE_CAP` |

Two consequences the golden-2 finding did not state:

1. **The arming could not have produced the 2050 entry.** D-2 only removes candidates and
   D-3 is sign-preserving, so on identical prices the armed screen clears a subset of what the
   unarmed screen clears. The difference between golden-1 (zero entry through 2050) and
   golden-2 (720 MW in 2050) is the **RC-R data channel** the golden-2 finding §6.2 already
   attributes the trajectory delta to — 2049 LP prices are tighter (2,243 h ≥ $100 vs
   golden-1's 1,339; 2050: 2,446 vs 1,531) because the re-timed exits retain less capacity.
   Golden-2 §6.1's "under the D-3 rank the clearing pick is the 100-h machine, where the
   pre-R-A absolute-margin rank had cleared nothing" is a misattribution of the *clearing* to
   the rank: the rank chose *among* clearers, and iron-air was the only one.
2. **The arbitrage leg is not persisted anywhere in the committed record.** The screen's price
   object is a runtime array; the L-5 dump that would have committed it
   (`entry_screen_diagnostics`, output-only, no cache-key term) was off. Everything in §3 about
   that leg is therefore a **bracket** (what the 2049 → 2050 flip pins) plus **anchors** (the
   same formula on measured price shapes), never the number the screen saw. That is a
   measured limitation of this Phase-0, stated up front; §7 names the zero-cost way to close
   it.

## 2. Exact reconstruction: the cost side and the RA leg, year by year

Position construction (the runner's, reproduced): the screen in year Y prices the fleet it
ENTERS with, i.e. the post-evolution fleet of Y−1 — ledger `reserve_margin_{Y−1}` is that
fleet's accredited firm ÷ peak_{Y−1} − 1 on the same `accredited_firm_capacity_mw` — against
year Y's requirement `1.02861 × peak_Y` (`(1 − 2,639.682/30,050) × (30,050/26,648)`, the
NEISO DR netting × Net-ICR margin, no published FPR). Every year-invariant credit (hydro
1,396.5 MW, HQ tie 409.3 MW, wind 0.16 / solar 0.18) cancels in the construction.

The table gives the two technologies that matter (the other three are dominated: li-ion 8 h
costs $232–275/kW-yr, li-ion 12 h $338–395, flow $265–357, every year). "Arbitrage required"
= cost − RA leg. "Residual at the real-market shape" subtracts the LARGEST arbitrage the screen
formula finds on any measured ISO-NE price year (§3: li-ion 4 h $52.5, iron-air $30.0, both
2025 real-time) — the most generous anchor, so a positive residual is a shortfall the price
shape cannot close.

| year | entering position | curve price $/firm-kW-yr | RA li-ion 4 h | cost li-ion 4 h | arb. required 4 h | residual 4 h @ real shape | RA iron-air | cost iron-air | arb. required iron-air | residual iron-air @ real shape | short term |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2027 | 1.110 | 0 | 0 | 142 | 142 | 90 | 0 | 131 | 131 | 101 | RA leg $0 (long) AND arbitrage |
| 2028 | 1.020 | 69 | 30 | 138 | 108 | 56 | 49 | 126 | 77 | 47 | arbitrage |
| 2029 | 1.004 | 100 | 43 | 135 | 92 | 39 | 71 | 123 | 52 | 22 | arbitrage |
| 2030 | 1.001 | 107 | 46 | 132 | 86 | 34 | 76 | 121 | 45 | 15 | arbitrage |
| 2031 | 0.996 | 124 | 53 | 130 | 77 | 24 | 88 | 119 | 31 | 1 | arbitrage |
| 2032 | 1.031 | 46 | 20 | 128 | 108 | 55 | 33 | 118 | 85 | 55 | arbitrage |
| 2033 | 1.045 | 27 | 12 | 126 | 114 | 62 | 19 | 117 | 97 | 67 | arbitrage |
| 2034 | 1.078 | 0 | 0 | 133 | 133 | 81 | 0 | 126 | 126 | 96 | RA leg $0 (long) AND arbitrage |
| 2035 | 1.008 | 94 | 40 | 141 | 101 | 48 | 67 | 135 | 68 | 38 | arbitrage |
| 2036 | 1.041 | 32 | 14 | 157 | 143 | 90 | 23 | 154 | 131 | 101 | arbitrage |
| 2037 | 1.036 | 38 | 16 | 155 | 139 | 86 | 27 | 152 | 125 | 95 | arbitrage |
| 2038 | 1.068 | 0 | 0 | 154 | 154 | 101 | 0 | 151 | 151 | 121 | RA leg $0 (long) AND arbitrage |
| 2039 | 1.054 | 9 | 4 | 152 | 149 | 96 | 6 | 150 | 144 | 114 | arbitrage |
| 2040 | 1.052 | 13 | 6 | 151 | 145 | 93 | 10 | 150 | 140 | 110 | arbitrage |
| 2041 | 1.046 | 25 | 11 | 150 | 139 | 87 | 18 | 149 | 131 | 101 | arbitrage |
| 2042 | 1.044 | 29 | 12 | 149 | 136 | 84 | 20 | 148 | 127 | 97 | arbitrage |
| 2043 | 1.038 | 36 | 16 | 148 | 132 | 80 | 26 | 147 | 121 | 91 | arbitrage |
| 2044 | 1.035 | 38 | 16 | 147 | 130 | 78 | 27 | 146 | 119 | 89 | arbitrage |
| 2045 | 1.029 | 50 | 21 | 146 | 125 | 72 | 36 | 146 | 110 | 80 | arbitrage |
| 2046 | 1.027 | 55 | 24 | 145 | 121 | 69 | 39 | 145 | 106 | 76 | arbitrage |
| 2047 | 1.021 | 67 | 29 | 144 | 116 | 63 | 48 | 145 | 97 | 67 | arbitrage |
| 2048 | 1.018 | 73 | 31 | 143 | 112 | 60 | 52 | 144 | 92 | 62 | arbitrage |
| 2049 | 1.012 | 84 | 36 | 143 | 107 | 54 | 60 | 144 | 83 | 53 | arbitrage |
| 2050 | 1.009 | 90 | 39 | 142 | 103 | 51 | 64 | 143 | **79 — CLEARED** | 49 | arbitrage (met by the stack signal, §3.1) |

All $/kW-yr. Reading the table:

- **The arbitrage leg is the short term in all 24 years.** Even crediting the screen with the
  best real-market price year on record, li-ion 4 h is short by $24–101/kW-yr and iron-air by
  $1–121/kW-yr — and the screen was NOT looking at the real market's shape (§3.2).
- **The RA leg is $0 in three years (2027, 2034, 2038) and, for li-ion 4 h, under $15 in six more** — the
  D28 oscillator: 2027 enters at 1.110 (the base fleet before the 2027 economic exit wave),
  2034 at 1.078 (before the CCS-exit wave), 2038 at 1.068 (before the Boston oil exit). In
  those years the position is past the published zero-cross and the leg reads $0. **Those
  are exactly the years D28 §2 names, seen from the storage stack.** Over the horizon the RA
  leg averages $22/kW-yr for li-ion 4 h and $36 for iron-air.
- **Cost side.** Li-ion 4 h: capex $1,810 → $1,707 learned in 2027 → $1,191 in 2050; the ITC
  takes it to $1,195 / $1,072 (2027 / 2030), so the annualized cost bottoms at **$126/kW-yr
  in 2033** and jumps to $157 in 2036 when the §48E credit phases out — the horizon's minimum
  cost is in the ITC window, and that is where the RA leg also peaks (2029–2031 at
  requirement), so **2029–2031 is the closest the stack ever comes for li-ion (required
  arbitrage $77–92)**, still $24–39 above the best real-market anchor. Iron-air: capex $2,000
  → $1,450 by 2050 (25 GW cumulative on a 1 GW reference, lr 0.10) with no ITC after 2035;
  cost $117–154, minimum $117 in 2033. FOM is $41 (li-ion) / $20 (iron-air) of every year's
  cost.
- **Two cost-side observations, identified from the code, not from the residual.** (a)
  `compute_storage_annual_cost` applies the learning rate as a direct exponent,
  `(cum/ref)^(−lr)`, while the thermal/VRE path's `new_entry.wright_cost` uses the documented
  per-doubling convention `exponent = −log2(1 − lr)`; on the SAME BNEF "18 % per doubling"
  input the storage path declines less (2050 li-ion multiplier 0.658 vs 0.514; iron-air 0.725
  vs 0.613). Under the per-doubling convention the 2050 li-ion 4 h cost would be ~$120/kW-yr
  and iron-air ~$124 — closer, still above every anchor. One learning formula per model is a
  rule-19 consistency item. (b) `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` was
  identified by caiso-179 as 19–35 % LOW against the PNNL-33283 cycle/retention pair and
  deliberately left; a corrected value moves li-ion's arbitrage leg DOWN (−$5–8/MWh more
  degradation), the wrong way for the corridor, and is stated here so it cannot be traded.

Charts: `d36/c1-stack-vs-cost.png` (cost line vs RA leg vs the anchor bands, per technology),
`d36/c2-position-and-price.png` (the entering position on the FCA curve and the price it
pays, with the real FCA 14–18 band).

## 3. The arbitrage leg: what the 2050 flip pins, and what measured price shapes say

### 3.1 The bracket from the bundle

The screen for 2049 (priced on the 2048 stack against 2049 net load) did not clear iron-air
at a required $83.4/kW-yr; the screen for 2050 (2049 stack, 2050 net load) cleared it at
$78.7. So the stack signal's iron-air arbitrage sat **below $83.4 in the 2049 screen and at
or above $78.7 in the 2050 screen** — the leg crossed ~$80/kW-yr at the horizon's edge, i.e.
a net margin of ~$20/MWh discharged over 40 nine-day cycles with the machine's 100 charge
hours priced at half weight (RTE 0.5 ⇒ the cheapest 100 hours of every 216 must average less
than half the dearest 100). Li-ion 4 h did not clear at $103.4 in 2050, so its daily net
spread (top-4 minus bottom-4/0.85 minus $22.63 degradation) averaged under $70.8/MWh on the
same signal. Both are consistent with a static stack whose floor is nuclear/CC-CCS variable
cost and whose top is CT/oil variable cost escalated by the RGGI path ($26 → $132/t; D23 §2):
the carbon escalation is what opens the stack's own spread through the 2040s, because it
raises CT (0.60 t/MWh) and oil (1.0 t/MWh) roughly ten times faster than 90 %-captured CC-CCS.
The FC-6 `gasup150` arm (no 2050 entry) is the same arithmetic from the other side: gas ×1.5
raises the CC-CCS charge floor, which iron-air pays twice over (RTE 0.5), faster than it
raises the CT discharge ceiling.

### 3.2 Anchors: the screen formula on measured price shapes (zero solves)

`estimate_storage_revenue` exactly as coded (duration-sized windows, best zone per window,
config RTE overrides 0.85 / 0.80, degradation as above) on three price surfaces:

| price surface | li-ion 4 h | li-ion 8 h | flow 10 h | iron-air 100 h |
|---|---:|---:|---:|---:|
| NEISO keeper `neiso99_joint_B` P1 hourly zonal duals, 2023 / 2024 / 2025 | 1.2 / 0.1 / 2.7 | 1.2 / 0.1 / 3.4 | 1.3 / 0.1 / 3.3 | 2.3 / 4.0 / 3.0 |
| ISO-NE SMD day-ahead zonal LMP, 8 load zones, 2023 / 2024 / 2025 | 10.4 / 12.6 / 29.1 | 11.0 / 13.9 / 27.6 | 14.2 / 16.8 / 28.6 | 16.8 / 17.0 / 15.4 |
| ISO-NE SMD real-time zonal LMP, 8 load zones, 2023 / 2024 / 2025 | 23.6 / 24.4 / **52.5** | 25.3 / 24.5 / 55.0 | 34.2 / 32.0 / 58.6 | 30.0 / 25.4 / 25.8 |
| arbitrage the golden's screen REQUIRED (2027–2050 range) | 77–154 | 151–270 | 190–361 | 31–151 |

Gross of degradation the real-time 2025 figures are $84 (4 h) / $104 (8 h) — the $22.6/MWh
degradation charge removes 37 % of li-ion's gross spread; iron-air's $1.67 removes 10 %.
Chart: `d36/c3-arbitrage-anchors.png`.

Three things this measures:

1. **The stack cannot clear li-ion at the real market's price shape in any year.** The
   requirement's minimum ($77, 2031) exceeds the best real-time anchor ($52.5, 2025 — a year
   with the Jan-2025 cold-snap spread) by $24, and the day-ahead anchor — the product a
   merchant battery is actually settled against for most of its energy — by $48. The
   requirement's typical value ($130–150 from 2036) is 2.5–3× the best anchor.
2. **Iron-air at the real shape ($15–30) is short in 23 of 24 years and within $1 in one
   (2031, when the curve pays 1.138 × net-CONE on the short side).** Its 100-hour cycle
   captures multi-day spread that is genuinely small in New England's price record, and its
   RTE 0.5 halves it again.
3. **The model's own calibrated price surface offers ~1/10–1/20 of the market's arbitrage.**
   The keeper's 2023–2025 duals give $0.1–5/kW-yr for every technology — the C3c-ledgered
   "model tail 0 h > $300 vs RT actuals 15/8/20" seen through a 4-hour window: no intraday
   tail, no negative trough. This is the part of the shortfall that IS the model's price
   formation, and it is a backcast-lane object (the ledgered C3c limitation), not a storage
   screen object.

### 3.3 The screen's price object is structurally blind to both ends of the spread

Under the golden's posture the storage screen never sees LP duals at all. It sees
`_lookahead_reprice_signal`: hourly price = the time-mean variable cost of the marginal unit
in a static merit stack at the entering year's net load. Consequences, each read from the
code (`runner.py:733-850`):

- **No scarcity tail.** `scarcity_pricing_enabled=false` ⇒ the ORDC adder branch is skipped;
  the signal's maximum is the dearest unit's time-mean cost (oil steam). The LP's 2,446
  hours ≥ $100/MWh and $393 maximum in 2050 (`full_horizon_summary` trajectory) are not in
  the screen's world; chart `d36/c4-lp-tail-vs-screen.png` shows what the LP priced that the
  screen was never handed.
- **No negative trough.** `np.searchsorted` into the cumulative stack floors at index 0 —
  the cheapest unit's cost — so the LP's 6.6 % (2050) negative-price hours, which are
  precisely the charge hours a battery is built for, price at nuclear/CC-CCS variable cost.
- **Zone-flat.** The signal is tiled across zones; `estimate_storage_revenue`'s best-zone
  selection is a no-op.
- **Time-mean cost.** Each unit's cost is its annual mean, so seasonal fuel shape (the
  Algonquin winter basis that drives New England's real spread) is averaged out of the
  stack.

This is the FINDING-entry-screen-t1h D-8 characterisation ("~90 % of the shipped signal's
dispersion is the ORDC adder; zone-flat by construction") in the one ISO where the adder is
gated off — leaving a stack with almost no dispersion at all. It is not a NEISO-specific
defect and it is not a storage-specific defect; it is the price object every capacity screen
consumes, seen from the one consumer whose value is *entirely* dispersion.

## 4. The binding-gate census

| gate / cap | bound in any year? | evidence |
|---|---|---|
| D-2 availability gate | **Yes, every year — on `compressed_air` only** (fail-closed `None`). Li-ion ×3, flow, iron-air admitted 2027–2050. Inert on the outcome: CAES costs $265+/kW-yr-equivalent and would not have cleared. | `STORAGE_TECH_AVAILABLE_YEAR`; §2 cost table |
| D-3 cost-normalized rank | **Never decisive** — sign-preserving; one clearer in 2050, so nothing to reorder. | `storage.py:1789` docstring |
| margin > 0 (the value stack itself) | **Bound 2027–2049 for every technology** — the object of this finding. | §2–§3 |
| `STORAGE_TECH_BUILD_SHARE_CAP` (0.6) | **Bound once, 2050, iron-air: 720 = 0.6 × 1,200.** The screen wanted more iron-air; nothing else cleared to take the remaining 480 MW. | `evolution_2050.json` |
| `STORAGE_ANNUAL_BUILD_CAP_MW` (1,200) | Never bound on its own (only through the share cap). | — |
| `STORAGE_DEPLOYMENT_CEILING_MW` (13,000) | Never bound (existing 2,635; penetration 0.203 fixed for 23 years, so the derate 0.712 is a constant on the RA leg). | ledger `storage_power_mw` |
| deliverability factor | Off (`capacity_deliverability_limits=false`) ⇒ 1.0. | run_config |
| `entry_margin_exhaustion` walk | Off ⇒ bang-bang split; irrelevant with one clearer. | run_config |

So the caps are innocent through 2049 and the share cap is the only thing that sized 2050.

## 5. One mechanism or two? — the D28 / D33 RA-leg question, answered

**Same object, yes.** The storage RA leg is priced through the identical seam
(`MarketDesign.capacity_price_per_firm_mw_yr`) at the identical `curve_reserve_position`
the retirement and thermal-entry screens receive (`runner.py:1830, 1905, 1997`). Every $0
in the RA column of §2 is a D28 §2 long-position year, and the 2031 over-payment (1.138 ×
net-CONE at position 0.996, $124/firm-kW-yr against real FCAs of $24–43) is D28's
"2.6 × reality when it dips" seen again. Nothing in the storage stack prices RA differently.

**One mechanism for the storage divergence, no.** Quantified:

| RA-leg scenario | li-ion 4 h $/kW-yr | iron-air $/kW-yr |
|---|---:|---:|
| golden as solved, horizon range (mean) | 0–53 (22) | 0–88 (36) |
| maximum the seam can pay at requirement (net-CONE × ELCC × 0.712) | 47 | 78 |
| at the real FCAs' cleared positions 1.033–1.045 (D28 §3: $24–43/kW-yr) | 11–18 | 19–31 |
| arbitrage still required with the RA leg at its MAXIMUM, vs best real-market anchor | 79–110 required vs 52.5 anchor | 39–76 required vs 30 anchor |

A D33 position repair moves the storage RA leg by at most the difference between its current
value and the real-position value: **up by ≤ $18 (li-ion) / ≤ $31 (iron-air) in the long
years, and DOWN by $20–35 / $35–57 in 2029–2031, 2035 and 2047–2050**, because in those years
the golden already pays more than the real market ever cleared. It would kill the
oscillator (D28's own description) and would make the stack clear *later*, not earlier —
the rule-14 sign discipline D28 §5 wrote for NEISO holds for the storage screen too. The
storage divergence is owned by the arbitrage leg (§3) and the cost side (§2), which D33 does
not touch. **Two mechanisms; D33 stays the position lane and is cited, not duplicated.**

## 6. Why 2050, why iron-air, why nothing before — stated once, in the mechanism's terms

- **Why iron-air:** it is the only admissible machine whose per-MWh degradation charge is
  negligible ($1.67 vs $20–23 for li-ion), whose ELCC is 1.0 (100 h clamps the generic
  table's 24-h endpoint) so its RA leg is the largest, and whose cost per kW-yr falls to
  parity with li-ion 4 h by 2045 ($146 vs $146) on its 1 GW-reference learning curve. Its
  100-hour window also lets it harvest multi-day stack spread that a daily-cycle machine
  cannot. Against that, RTE 0.5 is its handicap — which is why it cannot clear until the
  stack's ceiling exceeds twice its floor.
- **Why 2050:** the cost side is flat after the 2036 ITC step ($143–157), the RA leg climbs
  from $6 (2039) to $64 (2050) as the position walks down from 1.054 to 1.009, and the
  static-stack spread widens with the RGGI escalation and the 33 GW peak. The required
  arbitrage falls monotonically from $151 (2038) to $79 (2050) and the signal's iron-air
  arbitrage crosses it between the 2049 and 2050 screens (§3.1).
- **Why nothing before:** in the ITC window (2027–2033) the required arbitrage was as low as
  $31–52 (iron-air, 2029–2031) — the closest approach of the horizon — but the stack signal
  in 2029–2031 has no tail (LP: 6–52 hours ≥ $100, maximum $106–285) and a floor at CC-CCS
  cost, so a 100-hour machine paying its charge twice cannot find $31–52 there; and li-ion
  needed $77–92, above even the real market's best year. After 2036 the ITC is gone, the
  requirement is $100–154, and the RA leg is near zero through 2043.

## 7. What a repair would be identified FROM (rule 13), and the disposition

The corridor number (AEO2025 diurnal storage 1.76 GW by 2030 in New England, `ff-corridor`
storage rows at 2030/2035/2040, −56.2 %) is context, never a target. Three identified routes
on the merchant stack, one disposition on the divergence.

**R-1 — the arbitrage leg's price object (the first-order term).** Identified from the
model's OWN dispatch object, not from a residual: the entering-year zonal LP dual surface
carries the tail and the trough the stack re-price lacks. The repo already holds this as a
GATED default-OFF mechanism, `entry_forward_expectation_signal` (prior-year zonal duals
re-leveled by the lookahead's forward delta; zero fitted parameters, rule 21), matrix row
present, **NEISO cell `U` (untested)**, adjudicated so far only as an ERCOT T1-H arm. Its
storage-side effect is exactly the D-8 object: it restores dispersion. It is NOT a storage
mechanism and arming it moves every capacity screen (rule 19), so its charter is the
entry-signal lane's, not a storage lane's. **The zero-cost precondition, doable in any next
NEISO solve:** arm `entry_screen_diagnostics` (output-only, no cache-key term, no solve-path
change — the L-5 dump) so the stack signal the screen consumed is committed and the §3.1
bracket becomes a measurement. A second, smaller item on the same leg: with
`scarcity_pricing_enabled=false` NEISO's ORDC/tail is off for the screens by construction —
whether NEISO's screens should carry a scarcity tail is a capacity-economics question for
the NEISO lane, identified from ISO-NE's own Pay-for-Performance / reserve-constraint penalty
factors (published tariff values), never from this row.

**R-2 — the RA leg's accreditation basis.** NEISO's storage ELCC is the generic NREL/E3
duration table (no ISO-published class rating), which gives 4 h storage 0.60 and clamps
100 h at 1.00. The identification source is ISO-NE's own accreditation rule: the FCM
qualified-capacity treatment of Electric Storage Facilities in Market Rule 1 §III.13.1 for
the FCA vintages on disk, and the Resource Capacity Accreditation (RCA) reform — marginal
reliability-impact accreditation by resource class, filed by ISO-NE in 2025 for the first
prompt/seasonal auction (CCP 2028–29) — for the forward years. Both are published rules that
regenerate per delivery year and respond to the fleet's duration mix (rule 13). Note the
sign: RCA-style marginal accreditation compresses storage credit as penetration rises, so
this route is more likely to LOWER the 4-h leg than raise it. The position half of the RA
leg is D33's, unchanged.

**R-3 — the cost side.** (a) One learning-curve convention: `compute_storage_annual_cost`'s
direct exponent vs `wright_cost`'s per-doubling exponent (§2, item a) — identified from the
BNEF learning-rate definition the constant cites (per doubling), a code-consistency repair
worth ~$20/kW-yr on 2050 li-ion; (b) capex re-vintage on the NREL ATB 2025 storage tables
when intaken (`STORAGE_TECHS` is ATB 2024 Moderate re-based to 2026$; iron-air/flow/CAES rows
are `verified=0`); (c) the degradation fraction's caiso-179 identification (0.31–0.39), which
moves the wrong way and is recorded so it is not traded. None of the three reaches the
anchors: under (a) the 2050 li-ion requirement falls from $103 to ~$81/kW-yr, still above
the best real-time anchor and 2.8× the day-ahead one.

**The disposition (recommended for the corridor row).** With the RA leg at its maximum AND the
arbitrage leg at the real market's best year, li-ion 4 h is short in every year (§5 table),
i.e. **a faithful merchant arbitrage-plus-FCA stack does not build 1.76 GW of New England
batteries by 2030 on this cost basis.** What builds them in the market is the channel the
model deliberately excludes — the same channel D25 §4.3 mechanism 3 dispositioned for
offshore wind: state procurement and out-of-market contracts (the Massachusetts 2024 climate
statute's 5,000 MW storage procurement directive by 2030, Connecticut Public Act 21-53's
1,000 MW storage target, the MA Clean Peak Energy Standard credit stream — each an
enforceable public instrument to be confirmed at intake, and each formulaic in the rule-13
sense: a dated MW obligation, not a fitted quantity). AEO2025 itself carries these as policy
inputs. The recommended corridor-row text is therefore **EXPLAINED DIVERGENCE — procurement
channel unrepresented (D25 mechanism 3 family), with the merchant stack's own arbitrage
blindness (R-1) as the model-side residual**, replacing the current row's "the value stack
clears no tech" wording, which is true but attributes nothing. If the director later
charters a procurement-instrument channel (for OSW and storage together, since it is one
mechanism), its identification is those statutes' MW-by-year schedules, and it enters as a
known-additions row (step 4), never through the economic screen.

## 8. Exit state — what is routed

**Delivered:** the year-by-year short-term table (§2), the binding-gate census (§4), the
one-mechanism-or-two answer (§5: same seam, second-order for storage — two mechanisms), the
mechanism-terms answer to "why 2050 / why iron-air" (§6), three identified rule-13 repair
routes and the disposition (§7), four charts (`docs/handoffs/d36/`), the reproducible
reconstruction (§9). NO repair lands here.

**Routed to the director:**

1. **Corridor row disposition** (§7): re-author the three `capacity:storage` rows in
   `results/ff-corridor/dispositions/neiso-t3.json` with the procurement-channel explanation
   plus the R-1 residual — a FC-5 table edit this lane was barred from (the golden session may
   still be open); it changes no verdict (already EX).
2. **R-1 precondition** for the next NEISO solve of any kind: `entry_screen_diagnostics` on,
   so the storage screen's price object is committed (output-only). Then the entry-signal
   lane's `entry_forward_expectation_signal` NEISO cell (`U`) is the chartered route for the
   arbitrage leg — cross-ISO, every screen, not a storage lane.
3. **Golden-2 §6.1 wording:** the 2050 clearing is a data-channel result (RC-R exits → tighter
   2049 stack), not a D-3-rank result; the rank is sign-preserving. A one-line correction to
   that finding when its session closes.
4. **D33** proceeds unchanged; §5 gives it the storage-side consequence of its repair
   (down in the near-requirement years, up ≤ $31 in the long years) so the sign discipline is
   written before the lane lands.
5. **R-3(a)** learning-convention consistency — a small code repair with a rule-13 basis, for
   whichever lane next holds `model/storage.py` under its model assignment.

**Rule 28:** no mechanism tested, no field added, no cell moved; the two cells this finding
names (`entry_forward_expectation_signal` NEISO `U`, `storage_entry_*` NEISO `U`) are read,
not written — the golden-2 execution that armed the storage pair is that session's to stamp.

## 9. Reproduction (the instrument, committed inline)

Inputs: `results/ff-t3-neiso-golden/bau/{run_config.json, full_horizon_summary.json,
NEISO/706e7ba8e6582d42/evolution_<year>.json}`;
`results/calibration/neiso99_joint_B/hourly/system_{2023,2024,2025}.parquet` (P1 pass, zonal
`price`); `data/raw/lmp-data/NEISO/{2023,2024,2025}_smd_hourly.xlsx` (sheets ME/NH/VT/CT/RI/
SEMA/WCMA/NEMA, `DA_LMP` / `RT_LMP`, 8,760 rows each). Constants copied verbatim from
`config/capacity_market.py` (`STORAGE_TECHS`, `STORAGE_TECH_AVAILABLE_YEAR`,
`STORAGE_ELCC_BY_DURATION`, `STORAGE_ELCC_SATURATION_EXPONENT`,
`STORAGE_DEGRADATION_REPLACEMENT_FRACTION`, `STORAGE_DEPLOYMENT_CEILING_MW`,
`STORAGE_ANNUAL_BUILD_CAP_MW`, `_NEISO_FCA_CURVE`, NEISO net-CONE 108.94, the NEISO DR
fraction and Net-ICR margin) and `config/constants.py` (`WRIGHT_REFERENCE_GW`,
`GLOBAL_ANNUAL_DEPLOYMENT_GW`, `INFLATION_RATE`); `real_discount_rate` = 1.08/1.022 − 1.
The script (`recon.py`) re-implements the four storage.py functions line for line and writes
`stack.csv` (120 rows: year × tech, every column of §2) and `anchors.csv` (36 rows: source ×
year × tech); `charts.py` renders the four PNGs from those two files. Both scripts are
reproduced in the D36 session record; the CSV columns are the §2/§3 tables exactly. Checks
asserted at run: the run_config posture (`storage_entry_availability_gate`,
`storage_entry_cost_normalized_rank`, `storage_capacity_value`, `storage_degradation` true;
`as_revenue_enabled`, `entry_margin_exhaustion`, `capacity_deliverability_limits` false);
CRF 0.08490; requirement factor 1.02861 (= D28's); the 2050 iron-air requirement
$78.7/kW-yr < 2049's $83.4 (consistent with the ledger's single 2050 clearing).

## 10. Governance attestation

ZERO solves; no LP, no bench, no re-score, no registration; rule 15 does not fire. No
out-of-training year touched: the hourly sidecars read are the keeper's 2023–2025 training
years, the SMD files are raw published data, the golden is 2026+ forecast. Docs only: this
finding + four PNGs under `docs/handoffs/d36/`; no `src/`, no matrix shard, no
board/verdict/keeper/marker/FC-row file, no `neiso-t3` write. Rule 25 held: every number is
NEISO's own. Rule 14 sign discipline written where it bites (§2 item b, §5, §7 R-2/R-3c).
AEO's 1.76 GW appears only as corridor context (§7). Rule 27: no ≥300-line source file
touched.

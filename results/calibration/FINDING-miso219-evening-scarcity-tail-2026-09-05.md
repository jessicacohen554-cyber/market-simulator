# FINDING miso-219 — THE EVENING SCARCITY TAIL IS **UNREACHABLE BY ANY REGISTERED MISO FIELD**, and phase 0 proves it arithmetically rather than by assertion. The blocker is not a curve, a requirement, a penalty or a window — **it is that the LP is never short**, and the margin by which it is not short is 3.26× to 10.62× the published reserve requirement. **NO A/B CHARTERED. NOTHING MINTED. KEEPER UNCHANGED.** (2026-09-05)

**Session:** miso-219, branch `claude/miso-219-evening-scarcity-qrliuv`.
**Keeper at open AND at close: `2026-09-05-miso-217-intermphys`** (bundle
`results/calibration/miso217_intermphys_B`) — determination **NOT-YET on C3a-2025
alone (−12.297 %)**, C3c the single ledgered caveat (3/3), C6 attested, ledger 41/2.

**NO LP SOLVED. NO KEEPER MOVED. NO MECHANISM ARMED. NO RUN REGISTERED. NO
`ScenarioConfig` FIELD ADDED. NO PARAMETER SET. NOTHING WRITTEN UNDER `data/raw/`.**
Rule 22 `[R-HOLDOUT]` — 2023/2024/2025 only. Rule 15 `[R-DASHBOARD]` is not engaged:
no run was produced, so there is nothing to register (the miso-203 posture).

Instrument: `scripts/probes/_miso219_evening_tail_phase0.py` → record
`results/calibration/_miso219_evening_tail.json`. Every input is a committed
artifact of the keeper bundle or a primary measured source under `data/raw`.

---

## 0. Verdict in one paragraph

The charter's decision rule permitted an A/B only if phase 0 named a mechanism
that is (a) ONE `ScenarioConfig` field with ZERO free parameters already measured
or registered, (b) not a re-test of an adjudicated cell, and (c) able to move the
PRICE in those specific hours. **No candidate satisfies all three, and the reason
is a single measured quantity that refuses the entire family at once.** MISO's
keeper already arms every scarcity mechanism the registry holds for it — the
$3,500 RBDC, the zonal ORDC, the Midwest sub-regional family at the published
$200 RPE demand value, the online-gated Reg+Spin nest, per-generator reserve, and
the ELMP emergency tiers at the SOM-footnoted $500/$1,000 floors. **Every one of
them is conditioned on a shortage, and the LP never has one.** The market-wide
RBDC records **zero shortfall in all 26,280 hours of 2023–2025**; load slack is
**0.000 MWh in all 45 object hours**; and for the RBDC to bind at all the
requirement would have to be **10.62× (2023), 6.40× (2024), 3.26× (2025)** the one
MISO publishes — measured against the fleet's own *realized* annual ceiling, which
is the conservative reading, since nameplate headroom is far larger. The sharpest
single demonstration is 2025: **11 of the 15 object hours fall INSIDE a declared
MISO capacity-emergency window**, so the ELMP tier mechanism is armed, correctly
clocked and in-window — and contributes exactly **$0**, because it prices unserved
energy and there is none. Meanwhile the real market (A-3) priced those same hours
through an unambiguous co-optimized reserve-scarcity event: all three ASM products
clearing together at an object-hour mean of **$266 / $221 / $217** against annual
means of **$19.68 / $3.12 / $1.57**, with cleared MW *below* its annual mean. **The
model reproduces the physical state of the fleet in these hours to within 0.4
percentage points of the real fleet's own loading fraction (A-6) and prices it at
$81 instead of $718.** The failure is entirely in what the LP charges for the last
MW, and no registered field changes that.

---

## 1. A-0 — the object's own hours

Top-1 % of measured Jun–Jul RT price, hub `INDIANA.HUB`, on the committed scoring
instrument's fixed-CST non-leap clock (miso-204 §F / miso-206 repair). 15 hours per
year, 1,464 scored Jun–Jul hours.

| year | top-1 % cut | Jun–Jul actual mean | Jun–Jul actual median | object-hour actual mean | object-hour actual max |
|---|---:|---:|---:|---:|---:|
| 2023 | $121.43 | $31.76 | $27.19 | **$187.67** | $354.91 |
| 2024 | $159.01 | $33.25 | $25.51 | **$328.94** | $704.06 |
| 2025 | $373.02 | $53.40 | $36.23 | **$718.32** | $1,782.55 |

## 2. A-1 — WHAT SETS THE PRICE: three of the four channels are inert

| channel | 2023 | 2024 | 2025 |
|---|---|---|---|
| **energy-balance dual** (mean / max) | $36.76 / $43.04 | $39.47 / $51.34 | $80.93 / $181.19 |
| **reserve-family dual** (sum of family means) | **0.000 — INERT** | **0.000 — INERT** | $16.54 (regspin max $98.00, zonal-South max $7.55) |
| **ORDC shortfall** (hours of 15 with any) | **0 — INERT** | **0 — INERT** | **2** (regspin, max 471.4 MW) |
| **congestion** (mean / max zonal dispersion) | $0.43 / $4.17 | $0.69 / $10.00 | **$0.06 / $0.88 — INERT** |
| model annual max zone price | $234.04 | $500.00 | **$197.28** |
| actual annual max | $585.12 | $704.06 | **$1,782.55** |
| mean gap over the 15 hours | $150.91 | $289.47 | **$637.39** |

**The energy-balance dual carries essentially all of the model's price in these
hours, and it reaches $81.** The reserve channel is exactly zero in 2023 and 2024
and fires in 2 of 15 hours in 2025, capped at the $98 Reg+Spin step. Congestion is
inert — which **independently confirms miso-204's** published-component
decomposition (energy carries 93.1–125.5 % of the shortfall, congestion −23.3 %),
reached here from the model side rather than MISO's own MEC/MCC/MLC rows.

**Note the year that matters most.** 2025's model ceiling — $197.28 — is *lower*
than 2023's $234.04 and far below 2024's $500.00, in the one year the measured tail
explodes to $1,782.55. The model's price ceiling moves the wrong way.

**The peak tranche is not exhausted.** Scarcity-band dispatch in the object hours
is 575.5 / 901.8 / 1,722.3 MW against annual maxima of 3,774.9 / 3,623.7 / 2,974.3 MW
— in 2025 the object's hours use **58 %** of the peak band the year reaches
elsewhere. There is priced-below-$200 offer left when the real market is at $718.

## 3. A-2 — WHY THE ORDC NEVER CLIMBS: none of the three candidate causes

The charter named three candidates — requirement too small, held MW too large,
curve never consulted. **The measurement rejects the framing: the curve is
consulted every hour, the requirement is met every hour, and the surplus is so
large that no admissible requirement could change it.**

`miso_rbdc`, the family carrying the $3,500 `MISO_RESERVE_DEMAND_CURVE_MAX`:
**shortfall = 0.0 MW in 8,760 / 8,760 hours, in each of 2023, 2024 and 2025 —
26,280 hours, zero.** `held_mw` tracks `requirement_mw` to within ~1 MW annually.

A real inversion **does** exist and is worth naming, though it is not the binding
one. `miso_measured_reserve_requirements` sets the requirement from MISO's measured
*cleared* reserve MW, and cleared MW falls in a genuine shortage. So the model's
requirement **collapses in exactly the object's hours**:

| year | RBDC requirement percentile at the object hours | Midwest sub-regional | Reg+Spin |
|---|---:|---:|---:|
| 2023 | p73.6 | p60.2 | p70.5 |
| 2024 | p59.5 | p65.5 | p66.7 |
| **2025** | **p26.7** | **p20.7** | p79.6 |

In 2025 the market-wide operating-reserve requirement sits **below the level it
holds in 73 % of the year** in precisely the hours the real market was short. This
is already documented verbatim in `src/market_sim/data/reserve_requirements.py`
(*"in a genuine shortage interval cleared < requirement, so the requirement is
understated in exactly those hours … Any construction that undoes the dip … would
be residual-fitting around a shortage and is refused (rules 1/13)"*). **This
session does not re-open that refusal, and does not need to** — §4 shows repairing
it would be inert.

## 4. A-7 — THE REACHABILITY ARITHMETIC, which refuses the whole requirement family

A reserve family binds only when the requirement exceeds eligible headroom. Measured
against the fleet's **own realized annual-max thermal output** — deliberately
conservative; nameplate headroom is much larger and makes every multiple bigger:

| year | thermal in object hours | own annual ceiling | headroom | current RBDC req | req needed to bind | **multiple** |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 61,327 MW | 84,852 MW | 23,525 MW | 2,445 MW | 25,970 MW | **10.62×** |
| 2024 | 67,200 MW | 81,216 MW | 14,016 MW | 2,595 MW | 16,611 MW | **6.40×** |
| 2025 | 73,461 MW | 79,140 MW | 5,679 MW | 2,515 MW | 8,194 MW | **3.26×** |

**Every candidate requirement repair dies on this table.** Restoring the 2025
Midwest collapse in full is +463 MW. Reverting to the static published basis MISO's
own tariff implies (fleet MSSC + 400 MW ≈ 3.4 GW, the fallback rule 14 made the
model swap *away* from) is +0.9 GW, a 1.35× lift. Both are an order of magnitude
short of the 3.26× the tightest year requires. **There is no admissible requirement
that makes the RBDC bind**, so the requirement channel — repaired, reverted or
re-based — cannot reach the object.

## 5. A-5 — THE SHARPEST RESULT: the right mechanism, armed and in-window, firing on nothing

`maxgen_emergency_tier_pricing` is **armed in the keeper**. It reprices the
energy-balance load-slack cost to the SOM-footnoted $500 (Warning / Event Step 1)
or $1,000 (Event Step 2) emergency offer floor inside a **declared** window, on the
miso-210-repaired `Etc/GMT+6` model clock.

| year | declared window-hours in year | **object hours inside a declared window** | model slack in object hours | tier reachable |
|---|---:|---:|---:|---|
| 2023 | 72 | 0 / 15 | 0.000 MWh | no |
| 2024 | 7 | 0 / 15 | 0.000 MWh | no |
| **2025** | **108** | **11 / 15** | **0.000 MWh** | **no** |

2025's windows are the Jun 22–23 Max Gen Event Step 1 and Jun 23–24 Warning
(midwest), and the Jul 23–24 / Jul 28–29 footprint Advisory, Alert and Warning.
**MISO declared a capacity emergency across 11 of the 15 hours, the model knows it,
the mechanism is armed and correctly clocked, and it contributes exactly $0** —
because it prices unserved energy and the LP serves every MWh. (The cell already
carried a narrower version of this observation from a single hour; what is new is
that it holds systematically over the object's own hours, in the year the
determination turns on.)

Model slack across the whole year is 0 MWh (2023), 19,566.9 MWh over 7 hours
(2024 — the source of that year's $500.00 ceiling, i.e. the tier *does* print when
it can reach), and 0 MWh (2025).

## 6. A-3 — WHAT THE REAL MARKET DID: a co-optimized reserve-scarcity event

MISO-Wide RT ASM market clearing prices at the object's own hours. **Clock settled
empirically, not assumed:** correlating ASM `DEMREGMCP` against the committed LMP
instrument over four candidate offsets returns **r = 0.6314 / 0.6821 / 0.8162 at
the physical HE-EST → CST −2 h transform**, against 0.10–0.29 at every other
offset — so miso-167's convention is right and this block is built on it.

| product | 2023 obj / annual mean | 2024 obj / annual mean | 2025 obj / annual mean | 2025 obj max |
|---|---|---|---|---:|
| Regulating | $32.32 / $10.72 | $185.48 / $12.80 | **$266.18 / $19.68** | $1,151.23 |
| Spinning | $15.40 / $2.33 | $155.77 / $2.53 | **$221.22 / $3.12** | $1,097.25 |
| Supplemental | $0.13 / $0.37 | $139.18 / $0.71 | **$216.62 / $1.57** | $1,097.25 |

**All three products clear together at 14× their annual mean, and cleared MW does
not rise:** 2,487 / 2,966 / 2,577 MW in the object hours against annual means of
2,480 / 2,667 / 2,679 MW — in 2025 the market cleared **less** reserve than an
average hour while paying $266 for it. Quantity flat-to-down, price up 14×: that is
the demand-curve signature, and it is how MISO reached $718 mean RT LMP **while
serving all load**. The escalation across years (obj-hour reg MCP $32 → $185 → $266)
tracks the escalation in the model's own miss ($151 → $289 → $637) exactly.

## 7. A-6 — the fleet is NOT idle in the sense every reserve lever assumes

The carried-in premise "44.3 GW idle" is *nameplate* headroom. Against the fleet's
own realized ceiling, and against the real MISO fleet measured on the same clock
(EIA-930 NG+COL+OTH, the miso-156 instrument; measured record complete in all 45
object hours):

| year | model thermal, obj hours | % of own annual max | measured thermal | % of own annual max | model / measured |
|---|---:|---:|---:|---:|---:|
| 2023 | 61,327 MW | 72.3 % | 65,813 MW | 70.0 % | 0.932 |
| 2024 | 67,200 MW | 82.7 % | 74,410 MW | 82.4 % | 0.903 |
| 2025 | 73,461 MW | **92.8 %** | 81,315 MW | **92.4 %** | 0.903 |

**The model tracks the real fleet's loading fraction to within 0.4 percentage points
in every year.** It is not under-committed, not idle relative to reality, and in
2025 it is running at 92.8 % of the most it produces all year. The persistent 0.90
level ratio is an annual-mean property (0.893 / 0.899 annually), not an
object-hour one. **The model gets the physics of these hours essentially right and
the price wrong by $637.**

## 8. A-4 — the rule-19 census: there is no unarmed scarcity mechanism left

| mechanism | keeper state | reach in the object hours |
|---|---|---|
| `energy_reserve_coopt` | **ON** | dual 0.000 / 0.000 / $16.54 |
| `miso_zonal_reserves` (South, published ORDC steps) | **ON** | 0 shortfall hours, 3 yr |
| `miso_midwest_subregional_reserves` (+ `miso_rpe_pricing`, $200 RPE) | **ON** | 0 shortfall hours, 3 yr |
| `miso_reserve_online_gated` (Reg+Spin nest, RBDC steps) | **ON** | 2 hours in 2025, capped $98 |
| `miso_measured_reserve_requirements` | **ON** | requirement *falls* to p26.7 (§3) |
| `miso_reserve_pergen` | **ON** | pool gate never binding |
| `maxgen_emergency_tier_pricing` ($500 / $1,000) | **ON** | in-window 11/15, contributes $0 (§5) |
| `unit_outage_maxgen_events` | **ON** | — |
| `screen_reserve_value_enabled` | **ON** | retirement screen only |
| `scarcity_pricing_enabled` / `scarcity_price_overlay` | **OFF, correctly** | ERCOT post-solve overlay; cell **`G`** for MISO by owner ruling (miso-163, re-affirmed miso-204) |
| `ramp_limits` / `ramp_envelopes` | OFF | cell **`I`** for MISO (miso-156) — see §9 |

`MISO_RESERVE_DEMAND_CURVE_MAX` = $3,500; `MISO_RPE_DEMAND_VALUE` = $200;
`MISO_EMERGENCY_TIER1/2_OFFER_FLOOR` = $500 / $1,000; `voll` = `ordc_voll` = $5,000.
**Every published curve MISO has is in the model. None of them can be reached.**

## 9. WHY NO A/B IS CHARTERED — the candidates, and why each fails the decision rule

**`ramp_limits` — the strongest candidate, and it is DO-NOT-REDO.** Its own
docstring names this lane's object (*"forces the LP to either pre-position slow CC
before the evening ramp or clear fast resources at the ramp margin"*), and
`scenarios.py` names this lane's diagnosis outright (*"a zone-aggregate ungated
family clears inertly from ~10 GW of idle evening CC headroom at zero opportunity
cost — **the MISO lesson**, issue #1492"*). It is nevertheless **refused**: the cell
is **`I`** on miso-156's pre-registered kill rule (the model must out-ramp the
measured fleet at the p99 1-h move in ≥2 of 3 years; **it fires 0 of 3** — MISO's
model is *smoother* than the real fleet at every quantile, under-ramping by
12–41 %). **This session's A-6 is consistent with that, not new evidence against
it**, and no MISO ramp-envelope artifact exists (only NYISO/CAISO/PJM/ERCOT).
Rule 28(a) DO-NOT-REDO holds. PJM's `K` transfers nothing (rule 25).

**The requirement-repair family** — restoring the cleared-MW dip, or re-basing on
the published MSSC + regulating static — fails leg (c): §4 measures it inert by a
factor of 3.26–10.62×. It also runs into an existing documented refusal.

**Re-basing the ELMP tier from load-slack onto an emergency-range MW cohort** is
the one mechanism that is *structurally* right — it is what MISO actually does, and
§5 shows the model's slack mapping is the reason the armed tier cannot fire. But it
fails leg (a): the emergency-range MW is **neither already-measured nor
already-registered** in this repo. It would need a new `ScenarioConfig` field, a new
matrix row, and a new measured per-unit input — a build, not a single-delta A/B.
**It is named here as the successor's candidate, deliberately not chartered.**

**The offer-curve top end** is where the residual physically lives (§2: the peak
tranche is only 58 % used at $81 while the market is at $718), but that family is
exhausted on every MISO object — level `R` (miso-218), spread `I`, within-unit
surface `R`, anchor grain no-change (miso-216), `phys_*` coverage closed and armed
(miso-217). F-2 forecloses re-running or sweeping the level scale.

**Therefore: write the finding, mint nothing, stop** — the charter's own instruction
when the decision rule is not met.

## 10. What this session did NOT do, and what it must not be read as

* It did **not** re-open `ordc_scarcity_overlay` (`G`) — nothing here defeats
  miso-163 §1–§4's structural grounds, and a reachability measurement is not that.
* It did **not** re-open `ramp_envelopes` (`I`) — §9.
* It did **not** re-run or sweep the offer-level scale (F-2), test any
  heat- or peak-load-keyed capability removal (F-3, closed at miso-203), or present
  any CT movement as closing that class's gap (the miso-214 standing result: 62–70 %
  of the CT energy the model misses was produced below the plant's own delivered
  cost, and is unreachable by any offer or price mechanism).
* **Incidental methodological datum, recorded for reuse, undoing nothing:** the
  ASM clock is settled at the HE-EST → CST **−2 h** transform on an r = 0.63 / 0.68 /
  0.82 witness (§6). miso-214's no-shift reading was explicitly disclosed as such
  and served a different purpose; the correlation evidence simply makes the
  physical convention the one later probes should adopt.

## 11. The successor object, stated precisely for miso-220

The model reproduces the fleet's physical state in these hours to 0.4 pp (§7) and
prices it $637 low (§2). Every scarcity mechanism MISO publishes is armed and
unreachable, by 3.26–10.62× (§4, §8). The real market's own mechanism was a
reserve-demand-curve event with **fully served load** (§6) — a price the model has
no way to form, because every one of its scarcity channels is keyed to a physical
shortage rather than to a reserve-margin demand curve that prices *before* one.

Two heads remain, and **neither is a single-delta A/B**:

1. **The ELMP / emergency-supply mapping** (§9) — owner-court, because it needs a
   new measured input and a new field.
2. **The South PRICE separation** (miso-213 O-4 / miso-211 D-3, +$0.16 model vs
   +$58 measured) — untouched by this session and independent of everything above.
   Note §2 measures MISO-wide congestion as **inert** in the object's hours
   ($0.06 mean dispersion in 2025), which sharpens rather than answers that head.


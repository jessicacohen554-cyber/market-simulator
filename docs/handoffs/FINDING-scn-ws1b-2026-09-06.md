# FINDING — SCN-WS1b (r2): the six-ISO carbon paired probe

**Lane:** SCN-WS1b-r2 (relaunch/re-scope of SCN-WS1b) · **Model:** `claude-opus-5`
**Branch:** `claude/scn-ws1b2-carbon-sixiso-r4hm-t5hdbz` · **Date:** 2026-09-06
**Charter:** plan `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §7 "WS-1b" leg 1
(= §3 WS-1 items 4–6); desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#6 am.1.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-scn-ws1b-2026-09-06.md` (unedited) +
`docs/handoffs/PRECOMMIT-scn-ws1b-2026-09-06-ADDENDUM.md` (§(a)–(f), all pushed **before** the
first solve). **DATA PROFILE:** `all`.

---

## 0. Bottom line

<!-- FILL: headline after solves -->

---

## 1. The phase-0 result that re-scoped the lane (zero LP)

**The charter's leg 1 as written — six paired 2026-only T0 runs, REF vs `carbon_price_path=mid` —
is structurally unrunnable, and the reason is not the floor.**

`CARBON_PRICE_PATHS` (`src/market_sim/config/fuel_trajectories.py:1132-1137`) anchors **every**
registered RFF path at **$0 in 2026** — 2026 is the paths' common origin knot:

| path | **2026** | 2027 | 2028 | 2030 |
|---|---|---|---|---|
| zero | **0.0000** | 0.0000 | 0.0000 | 0.0000 |
| low | **0.0000** | 2.0000 | 4.0000 | 8.0000 |
| mid | **0.0000** | 3.7500 | 7.5000 | 15.0000 |
| high | **0.0000** | 7.5000 | 15.0000 | 30.0000 |

So **no `carbon_price_path` value of any kind can produce a signal in a 2026-only solve.** All
twelve chartered arms would have been six pairs of *byte-identical configs*, and ~82 minutes of LP
would have measured solver determinism rather than carbon.

Measured through the solves' own builder (`reference_config(iso, 2026, 2030, cmc=False)`),
instrument `docs/handoffs/scn-ws1b/phase0-recensus-path-2026-09-06.py`:

| ISO | REF 2026 | ARM 2026 | **Δ 2026** | Δ 2027 | Δ 2028 | Δ 2030 | cause of the 2026 null |
|---|---|---|---|---|---|---|---|
| ERCOT | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| CAISO | 30.0242 | 30.0242 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| PJM | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| MISO | 0.0000 | 0.0000 | **0.0000** | +3.75 | +7.50 | +15.00 | **RFF mid knot at 2026 is $0** |
| NYISO | 23.6363 | 23.6363 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |
| NEISO | 26.0545 | 26.0545 | **0.0000** | 0.00 | 0.00 | 0.00 | floor: program > path, every year |

**Two independent causes, and the charter anticipated only one.** The charter expected the arm to
be inert on CAISO / NYISO / NEISO (the S2 floor — correct, and confirmed) and **live on ERCOT /
PJM / MISO**. It is not live there at 2026: both arms resolve to $0 because the path's own 2026
knot is zero. Gate **G1 (premise)** therefore failed in all six ISOs, and under rule 29
`[R-SCREEN]` clause (0) the arms did not reach a solve.

**Re-scope, authorized by the desk and recorded in ADDENDUM §(f) before any LP:** extend to
`--start-year 2026 --end-year 2027` and score at **2027** — the first year the axis is live, and
still below `ccs_retrofit_available_year = 2028`, so ruling **S5**'s `gas_cc_ccs` hold does not
reach it and the pairs keep **zero CCS exposure**. Rule 29's own text prescribes this: *"a
mechanism measured INERT in the candidate screen year (screen it where it is live …)"*.

---

## 2. The resolved carbon trajectory under the S2 floor, per ISO

Resolved $/tCO2 through the live chain a solve uses, measured by the phase-0 re-census. **REF is
the campaign base** (every policy axis at its `ScenarioConfig` default, so `carbon_price_path`
= `"zero"`); **ARM** is REF + the one override `carbon_price_path="mid"`.

| ISO | state program? | REF 2027 | ARM 2027 | **Δ 2027** | arm at 2027 |
|---|---|---|---|---|---|
| **ERCOT** | no | 0.0000 | 3.7500 | **+3.7500** | **LIVE** |
| **PJM** | no | 0.0000 | 3.7500 | **+3.7500** | **LIVE** |
| **MISO** | no | 0.0000 | 3.7500 | **+3.7500** | **LIVE** |
| CAISO | CARB | 32.1259 | 32.1259 | **0.0000** | INERT (floor) |
| NYISO | RGGI | 25.2908 | 25.2908 | **0.0000** | INERT (floor) |
| NEISO | RGGI | 27.8783 | 27.8783 | **0.0000** | INERT (floor) |

**The floor is doing exactly what ruling S2 says it does.** On the three program ISOs the state
allowance price exceeds the RFF mid path in every horizon year, so `max()` returns the program and
naming a federal path changes nothing. On the three without a program the adder is `0.0`, so
`max(0.0, path)` **is** the path. One expression, both halves.

---

## 3. The paired T0 result at 2027

### 3.1 ERCOT — LIVE, and the mechanism is textbook

| metric | REF | CARB | Δ |
|---|---|---|---|
| resolved carbon $/t | 0.0000 | 3.7500 | **+3.7500** |
| **`emissions_mt`** (in-ISO, scored) | 255.9732 | 255.0452 | **−0.9280 (−0.36 %)** |
| **`import_co2_mt_reported`** | **0.0000** | **0.0000** | **0.0000** |
| load-weighted price $/MWh | 982.313 | 984.247 | **+1.934** |
| `unserved_mwh` | 4,621,769.86 | 4,621,769.86 | 0.0 |
| `clean_share` | 0.3519 | 0.3519 | 0.0 |

**The 2026 year of both arms is bit-identical** — `lw_price` 91.037 vs 91.037 — and they diverge
only at 2027. That is §1's arithmetic confirmed by measurement rather than asserted: the pair is a
genuine pair exactly where the RFF path becomes live, and a null everywhere before it.

**Coal→gas re-ordering, which the PRECOMMIT predicted for ERCOT, is visible and close to 1:1:**

| fuel | Δ CO2 (Mt) | Δ generation (TWh) |
|---|---|---|
| **coal** | **−1.3719** | **−1.2901** |
| **gas_cc** | **+0.5205** | **+1.2719** |
| gas_ct | +0.0525 | +0.1544 |
| gas_st | −0.1291 | −0.1707 |
| hydro / nuclear / solar / wind | 0.0000 | **0.0000 (exactly)** |

Coal sheds 1.29 TWh and gas-CC picks up 1.27 TWh at roughly the same energy — a merit-order
substitution, not a demand response. The CO2 falls because the substituted MWh carries ~0.41 t
rather than ~1.06 t. **Every zero-carbon class moves exactly 0.0000 TWh**, so the footprint claim
holds without qualification.

### 3.2 STOP-gate verdicts — ERCOT

| gate | verdict | detail |
|---|---|---|
| **G1** premise | **PASS** | Δ resolved carbon `+3.7500` = the pre-declared value exactly |
| **G2** CO2 does not rise | **PASS** | 255.9732 → 255.0452 Mt (−0.36 %) |
| **G3** price does not fall | **PASS** | 982.313 → 984.247 $/MWh (+1.934) |
| **G4** magnitude | **REPORTED MISS** | Δp/Δcarbon = **0.5157 t/MWh**, inside the structural bound [0, 1.08]; **above** my declared band [0.9, 1.5] $/MWh and above WS-4c's 1.68 point |
| **G5** fossil confinement | **PASS** | partition reproduces `emissions_mt`; no zero-carbon class books a CO2 decrease |
| **G6** import books no in-ISO CO2 | **PASS** | `emissions_by_fuel_mt["import"]` = 0.0 / 0.0 |
| **G7** no non-target flip | **PASS** | invariants identical: FAIL 1 / WARN 2 in **both** arms |
| **G8** unserved energy | **PASS** | unchanged (but see §3.3 — REF is already non-zero) |

**VERDICT: ARM NOT KILLED.** The gate promotes nothing.

### 3.3 THE CAVEAT THAT GOVERNS ERCOT'S PRICE NUMBER — read this before quoting +$1.934

**ERCOT's forecast REF is adequacy-collapsed at 2027, in both arms**, and the price level is
therefore **not campaign-grade**:

| | 2026 | **2027** |
|---|---|---|
| load-weighted price | $91.04 | **$982.31** |
| reserve margin | +3.3 % | **−6.5 %** |
| I3 slack | 0.06 % of load (55 h) | **0.68 % of load, 641 h, 4,621.8 GWh** |
| invariants | I3 **FAIL**, I12 WARN, I14 WARN | same |

This is the **known G-S4 ERCOT adequacy defect** the plan already records (§5.1 row 3: *"ERCOT
saturates … adequacy collapse, G-S4 stands"*), not something this arm caused — the two arms carry
it identically, which is why **G7 passes and G8's "no change" is truthful but not reassuring**.
The honest split:

- **ROBUST to the defect:** the **CO2 delta and the coal→gas re-ordering**. Those are merit-order
  effects — a carbon price reorders the stack by `rate × price` whether or not the stack clears
  the load — and both arms shed the same 4,621.8 GWh.
- **NOT campaign-grade:** the **price delta and the implied rate**. In 641 hours the price is set
  by scarcity, not by a fossil unit, and a carbon adder moves a VOLL-set price by ~$0. Those hours
  dilute Δp toward zero while still carrying load-weight.

**A structural consequence worth stating, because it cuts against my own miss:** if the scarcity
hours contribute ≈0 to Δp, then `0.5157 = (mean marginal fossil rate) × (fossil-marginal load
share)`, so the **true fossil-marginal rate is HIGHER than 0.5157** — consistent with coal being
marginal in a materially larger share of ERCOT's 2027 hours than either my band or WS-4c's
load-following rate assumed. **My G4 band is not merely "missed high"; it was built on the wrong
regime.** I did not revise it, and it is reported at full magnitude in §5.

**G8's design limitation, found by this result and worth carrying forward.** My PRECOMMIT wrote
G8 as *"`unserved_mwh` does not become non-zero in CARB while zero in REF"*. It passes here — and
it would have passed identically had REF been carrying 4.6 TWh of unserved energy for a reason the
arm was responsible for. The gate tests a **transition**, and cannot see a REF that is **already**
broken. A future paired-probe gate should assert a REF-side adequacy precondition, not only a
no-worsening condition. Flagged, not silently patched — the gate is pre-registered and stays as
written for this lane.

### 3.4 PJM — LIVE, campaign-grade, and every gate PASSES

**PJM is the clean measurement ERCOT could not be**: no unserved energy in either arm, load-weighted
price $42.39 → $44.53, and its one invariant failure (I7, accredited firm capacity below
requirement) is a **capacity-accreditation** shortfall carried identically by both arms, not a
dispatch collapse. Nothing here needs the §3.3 caveat.

| metric | REF | CARB | Δ |
|---|---|---|---|
| resolved carbon $/t | 0.0000 | 3.7500 | **+3.7500** |
| **`emissions_mt`** | 393.6225 | 380.1844 | **−13.4381 (−3.41 %)** |
| **`import_co2_mt_reported`** | 0.9141 | 1.3477 | **+0.4336** |
| load-weighted price $/MWh | 42.385 | 44.534 | **+2.149** |
| `unserved_mwh` | **0.0** | **0.0** | 0.0 |
| `clean_share` | 0.3459 | 0.3459 | 0.0 |

**STOP gate: 8 of 8 PASS. ARM NOT KILLED.** G4 lands *inside* my declared band ([1.5, 2.7] $/MWh)
at an implied rate of 0.5731 t/MWh.

**The coal→gas re-order is very large — the biggest single effect this lane measured:**

| fuel | Δ CO2 (Mt) | Δ generation (TWh) |
|---|---|---|
| **coal** | **−18.9888** | **−17.4134** |
| **gas_cc** | **+5.3620** | **+14.1015** |
| gas_ct | +0.1913 | +0.5044 |
| biomass | 0.0000 | +0.6439 |
| **import** | 0.0000 *(books no in-ISO CO2)* | **+2.0495** |
| hydro / nuclear / solar / wind | 0.0000 | **0.0000 (exactly)** |

**17.4 TWh of coal — 7.7 % of PJM's entire coal output — is displaced by a $3.75/t carbon price.**
That is the substantive PJM result and it is **2.3× larger than the top of my predicted band**
(§5). The mechanism is a narrow spread, not a big price: the adder is `$3.98/MWh` on coal
(1.06 t/MWh) against `$1.54/MWh` on gas-CC (0.41 t/MWh), so the *relative* shift is only
~$2.44/MWh — and PJM's coal and gas-CC marginal costs sit close enough together in 2027 that a
large mass of coal MWh lies inside that $2.44 window. **PJM's low-carbon-price switching is highly
elastic, and my band assumed it was not.**

### 3.5 A pattern across BOTH live ISOs: the price-setting unit is dirtier than the load-following unit

ADDENDUM §(g) pre-registered the question of whether WS-4c's marginal rate — measured under a
**load** increase, i.e. the units that *ramp* — would also describe a **carbon price**'s
pass-through, i.e. the unit that *sets price*. It stated in advance: *"Where my measurement departs
from WS-4c's point, that gap is itself the result."* **It departs, in the same direction, on both
live ISOs measured so far:**

| ISO | WS-4c implied rate (load-following) | **this lane (price-setting)** | ratio |
|---|---|---|---|
| ERCOT | 0.447 | **0.5157** | **1.15×** |
| PJM | 0.508 | **0.5731** | **1.13×** |

Two independent ISOs, two independent campaigns, the same ~13–15 % gap in the same direction.
**A plausible mechanism, offered as a hypothesis and not a claim:** coal is slow-ramping, so gas
answers an increment of *load* while coal continues to *set price* in a larger share of hours.
If that is right, the two rates are measuring genuinely different marginal units and neither is
"the" marginal rate — the correct one depends on the question asked. **This is n = 2 and one ISO
away from being a coincidence; MISO is the third live ISO and its result should be read as the
test of whether the pattern holds.**

### 3.6 MISO — LIVE, 8/8 PASS, and both my bands HIT

| metric | REF | CARB | Δ |
|---|---|---|---|
| resolved carbon $/t | 0.0000 | 3.7500 | **+3.7500** |
| **`emissions_mt`** | 370.4751 | 363.8337 | **−6.6414 (−1.79 %)** |
| **`import_co2_mt_reported`** | **0.0000** | **0.0000** | **0.0000** |
| load-weighted price $/MWh | 52.000 | 54.411 | **+2.411** |
| `unserved_mwh` | 199,592.22 | 199,592.22 | 0.0 |

**STOP gate: 8 of 8 PASS. ARM NOT KILLED.** Both pre-declared bands land: CO2 −1.79 % inside
[−0.8, −1.8] %, price +$2.411 inside [1.8, 3.3] $/MWh.

Coal → gas again, at MISO's larger scale: **coal −10.60 TWh**, gas_cc **+8.34 TWh**, gas_ct
+1.07, gas_st +0.47, biomass +0.59; hydro / nuclear / solar / wind all **exactly 0.0000**.

**Adequacy caveat, smaller than ERCOT's and stated anyway:** MISO carries I3 (19 h / 41 h of
slack, 0.02–0.03 % of load) and I7 in **both** arms, and 199,592 MWh of unserved energy unchanged
between them. Prices stay in a normal range ($52 → $54), so unlike ERCOT this pass-through number
is usable — but it is not a perfectly clean market either, and the 41 scarcity hours dilute Δp
slightly toward zero, i.e. the true fossil-marginal rate is a little **above** the 0.6429 measured.

### 3.7 THE n = 3 TEST — the direction holds, my magnitude claim does NOT

§3.5 recorded a ~13–15 % gap on two ISOs and named MISO in advance as the test. **MISO confirms
the direction and breaks the magnitude:**

| ISO | coal share of generation | WS-4c rate (load-following) | **this lane (price-setting)** | ratio |
|---|---|---|---|---|
| ERCOT | 14.1 % | 0.447 | 0.5157 | **1.15×** |
| PJM | 23.1 % | 0.508 | 0.5731 | **1.13×** |
| **MISO** | **35.0 %** | 0.484 | **0.6429** | **1.33×** |

**What survives:** the price-setting marginal rate exceeds the load-following rate in **3 of 3**
ISOs, measured by two independent campaigns on different questions. That is a real and consistent
result, and it means the two rates are **not interchangeable** — an emissions attribution that
uses one where the other belongs is wrong by 13–33 %.

**What does NOT survive — my own §3.5 framing, retracted here:** the gap is **not** a stable
~13–15 % correction. MISO's 1.33× sits well outside the ERCOT/PJM cluster, so at n = 3 the honest
statement is a **range of 1.13–1.33×**, not a constant.

**And the obvious mechanism does not cleanly explain it.** If the driver were simply "more
inframarginal coal ⇒ bigger divergence", the ratios would order with coal share. **They do not:**
PJM has 1.6× ERCOT's coal share and a *smaller* ratio (1.13 vs 1.15). Coal share alone therefore
fails to order three points, and **I am not going to fit a second variable to three observations
to rescue it.** The slow-ramping-coal story of §3.5 remains a plausible *direction* mechanism and
is now explicitly **not** established as a dose-response one.

**What would actually settle it** (named, not run — outside this lane's charter): the same
differencing on the three program ISOs, which this lane cannot supply because the arm is inert
there; or a decomposition of Δprice by marginal-fuel hour, which needs the hourly duals rather
than the annual scalars these T0 bundles export.

### 3.8 The INERT pairs — NEISO and NYISO, exact identity confirmed

The floor makes `carbon_price_path="mid"` a no-op on the state-program ISOs, so ADDENDUM §(f.2)
re-specified **G4 for these pairs as an exact-identity test** rather than a band: a **non-zero**
delta would be the failure, because it would mean something other than carbon moved between two
configs that resolve to the same carbon price in every hour.

| ISO | resolved $/t (both arms) | `emissions_mt` | lw price $/MWh | Δ on **every** metric |
|---|---|---|---|---|
| **NEISO** | 27.8783 | 17.1691 | 50.8530 | **0.000000** |
| **NYISO** | 25.2908 | 24.5911 | 49.1840 | **0.000000** |

**8/8 PASS on both.** Δ CO2 and Δ lw_price are `0.000000` to six decimals; every by-fuel and
by-zone row is identical; `unserved_mwh` 0.0 in all four arms. **This is §1's arithmetic converted
into a measurement.** It also exercises the harness: two runs differing in one field that the
resolver is supposed to neutralise produce byte-equal dispatch, which is a real (if narrow) check
that the S2 floor is wired where it claims to be.

**These two are also the cleanest runs of the lane** — REF and CARB each score **0 FAIL / 0 WARN**
across all 14 forecast invariants, against ERCOT's 1 FAIL/2 WARN, PJM's 1/1 and MISO's 2/1.

**What they are NOT evidence of.** They say a *federal RFF `mid`* price is a no-op where a state
program already charges more (RGGI $27.88 and $25.29 vs the path's $3.75 at 2027). They say
**nothing** about whether carbon pricing works in New England or New York — those ISOs are already
carbon-priced, at roughly **7×** the federal path's 2027 level. Quoting "no effect" from these
rows would invert their meaning.

### 3.9 A LEVEL result the zero deltas would otherwise hide

The leakage duty asks for `import_co2_mt_reported` **beside** `emissions_mt` as a number. On the
two RGGI ISOs the *delta* is zero — but the *level* is large:

| ISO | in-ISO `emissions_mt` | reported import CO2 | **import as % of scored in-ISO** |
|---|---|---|---|
| **NYISO** | 24.5911 | **10.1556** | **41.3 %** |
| **NEISO** | 17.1691 | **4.3493** | **25.3 %** |
| PJM | 393.6225 | 0.9141 | 0.2 % |
| ERCOT / MISO | 255.97 / 370.48 | 0.0000 | 0.0 % (no seam exists) |

**A campaign that reports only `emissions_mt` understates NYISO's carbon footprint by roughly two
fifths and NEISO's by a quarter**, before any policy is applied. This is a *standing* disclosure
property of the two import-heavy ISOs, not something a carbon arm creates — and it is exactly why
SCN-WS0's duty is to print the import line beside every headline rather than only when it moves.
It is reported here because a reader scanning §3.8's zero deltas would otherwise conclude these
ISOs have nothing to disclose.

## 4. LEAKAGE — `import_co2_mt_reported` beside `emissions_mt`, per ISO, as a number

<!-- FILL: completed as each ISO lands. ERCOT row below. -->

| ISO | Δ `emissions_mt` (Mt) | Δ `import_co2_mt_reported` (Mt) | % of headline displaced | tranche that moves |
|---|---|---|---|---|
| **NYISO** | **0.0000** (arm inert) | **0.0000** | n/a — no headline to displace | 6 carbon-bearing tranches exist and carry a **standing 10.1556 Mt**, but the arm does not move them: the RGGI program ($25.29/t at 2027) already exceeds the RFF mid path ($3.75), so `max()` returns the program and nothing in the ISO changes. **Level ≠ delta** (§3.9). |
| **NEISO** | **0.0000** (arm inert) | **0.0000** | n/a | 4 carbon-bearing tranches, **standing 4.3493 Mt**; inert for the same reason. |
| **MISO** | **−6.6414** | **0.0000** | **0.0 %** | **none built.** `IMPORT_ZONE` names `MISO_external` but `IMPORT_TRANCHES` has no MISO entry, so no tranche exists. **This zero is a MODEL-BOUNDARY artifact, not a physical claim** — MISO trades heavily with PJM and SPP in reality; the model has no seam for it. MISO's −6.64 Mt therefore carries **no leakage disclosure at all** and must be read as an **upper bound**. Flagged in the PRECOMMIT before the solve precisely so this null is not read as "MISO does not leak". |
| **PJM** | **−13.4381** | **+0.4336** | **3.2 %** | **the 2-tranche scarcity block** — import generation +2.0495 TWh. Predicted +0.03 to +0.23 Mt; **measured +0.4336, nearly 2× the top of my band** (§5). The tranches pay **no border carbon** while PJM coal's `mc` rises ~$3.98/MWh, so they get relatively cheaper. `emissions_by_fuel_mt["import"]` stays **0.0** in both arms — the import MWh never enters the scored in-ISO total (G6), it is disclosed beside it. |
| **ERCOT** | **−0.9280** | **0.0000** | **0.0 %** | **none — ERCOT has no import node at all** (0 import pseudo-generators; PRECOMMIT §2.2). The zero is a **construction fact, not a measurement**: there is no seam across which leakage could be observed, so ERCOT's headline cut carries **no leakage disclosure** and must be read as an **upper bound** on the real reduction. |

## 5. My misses, reported at full magnitude

Nine pre-declared numbers across the three LIVE ISOs (ADDENDUM §(d.2) for price and CO2,
PRECOMMIT §3.4 for leakage). **Six hit, three missed.** Every band below is quoted as pushed
before the solve; **none was revised after a result.**

| ISO | quantity | pre-declared | measured | verdict |
|---|---|---|---|---|
| ERCOT | Δ CO2 % | −0.2 to −0.8 % | **−0.36 %** | **HIT** |
| ERCOT | Δ lw price | $0.9 – 1.5 | **$1.934** | **MISS — 1.29× the top** |
| ERCOT | Δ import CO2 | exactly 0.0000 | **0.0000** | **HIT** |
| PJM | Δ CO2 % | −0.6 to −1.5 % | **−3.41 %** | **MISS — 2.27× the top** |
| PJM | Δ lw price | $1.5 – 2.7 | **$2.149** | **HIT** |
| PJM | Δ import CO2 | +0.03 to +0.23 Mt | **+0.4336** | **MISS — 1.89× the top** |
| MISO | Δ CO2 % | −0.8 to −1.8 % | **−1.79 %** | **HIT** (just inside) |
| MISO | Δ lw price | $1.8 – 3.3 | **$2.411** | **HIT** |
| MISO | Δ import CO2 | exactly 0.0000 | **0.0000** | **HIT** |

**Every miss is in the same direction: I under-predicted the response.** That is the useful
pattern in my own errors, and it has three distinct causes rather than one:

1. **PJM's CO2 miss (the largest) — I assumed the wrong elasticity.** My band came from scaling a
   $25/t prediction down by 0.15, which implicitly assumes the response is roughly linear in the
   carbon price. It is not, where a fleet has coal and gas-CC near parity: what matters is how much
   MWh sits inside the **$2.44/MWh relative shift**, and PJM's does. A carbon price acts on the
   *spread distribution*, not on a fleet-average rate — a mechanism my band's construction had no
   way to express.
2. **ERCOT's price miss — I banded the wrong regime.** §3.3: with 641 scarcity hours and a −6.5 %
   reserve margin, ERCOT 2027 is not the fossil-marginal market my band assumed. The measured
   0.5157 t/MWh is a *lower bound* on its fossil-marginal rate, not a central estimate.
3. **PJM's leakage miss — I mis-scaled a threshold effect.** I rescaled WS-0's $25/t leakage
   linearly to $3.75/t. But import tranches are **priced blocks**: they clear or they do not, and
   the fraction of hours in which a $3.98/MWh coal adder pushes a $46–60 block into merit is not a
   linear function of the adder. Rescaling a step response linearly under-predicts it.

**The honest summary of my prediction skill: direction 9/9, magnitude 6/9, and all three magnitude
errors are under-predictions.** The charter asked that misses be reported with the reasoning that
produced them; the reasoning above is what I would change, not the numbers I wrote.

**A prediction that was NOT mine and did better in one place, worse in another:** SCN-WS4c's
measured marginal rates (ADDENDUM §(g)) implied ERCOT $1.68, PJM $1.91, MISO $1.82. Measured:
$1.934, $2.149, $2.411. **WS-4c's points under-predict all three as well**, by 15 %, 12 % and
33 % — the same direction as my own error and the reason §3.7 treats the gap as a real result
rather than as noise.

## 6. Wall clock and peak RSS, per solve-year

Every arm ran **2 solve-years** (2026 as 2027's capacity-evolution prior; 2027 scored). Years
sequential within an invocation, always (rule 12 `[R-PARALLEL]`).

| ISO | arm | 2026 wall / RSS | 2027 wall / RSS |
|---|---|---|---|
| ERCOT | REF | 153.4 s / 3.50 GB | 127.0 s / 3.33 GB |
| ERCOT | CARB | 154.3 s / 3.50 GB | 128.4 s / 3.72 GB |
| PJM | REF | 389.3 s / **9.03 GB** | 201.1 s / 6.57 GB |
| PJM | CARB | 382.0 s / 8.97 GB | 185.6 s / 6.53 GB |
| MISO | REF | 446.2 s / **9.87 GB** | 211.1 s / 7.92 GB |
| MISO | CARB | 393.0 s / **9.90 GB** | 197.8 s / 7.95 GB |
| NEISO | REF | 112.5 s / 3.17 GB | 85.6 s / 3.04 GB |
| NEISO | CARB | 110.6 s / 3.25 GB | 78.6 s / 3.07 GB |
| NYISO | REF | 139.8 s / 3.24 GB | 121.1 s / 2.75 GB |
| NYISO | CARB | 140.1 s / 3.28 GB | 125.3 s / 2.74 GB |

**Twenty solve-years, 3,883 s = 64.7 min of LP** for the ten arms above (CAISO's pair is reported
in §6.1 when it lands). **Peak RSS 9.90 GB (MISO CARB 2026) on a 15 GB box.**

**That peak is why rule 12 `[R-PARALLEL]`'s one-invocation limit for per-plant multi-zone ISOs is
load-bearing rather than cautionary**: two concurrent MISO arms would have needed ~19.8 GB and
OOM-ed. The small ISOs (ERCOT / NEISO / NYISO, ~3.5 GB) ran both arms concurrently with no
contention, which is exactly the split the rule draws.

**2026 costs roughly 2× 2027 in every ISO** — the first horizon year builds the fleet and
capacity-evolution state that the second reuses. A lane budgeting T0 work from a per-solve-year
average will therefore under-budget a 2-year run by ~25 %.

## 7. LEG 2 IS HELD BY RULING S5

The NEISO/ERCOT T1-F **2026–2030 carbon ladder** (original PRECOMMIT §3.5) **was not run.**

**Why.** It spans 2028–2030, so it crosses `ccs_retrofit_available_year = 2028` (measured 2028 in
all six ISOs, original PRECOMMIT §2.3), so it moves `gas_cc_ccs`. SCN-WS2b measured that the CCS
emission-rate seam can make that CO2 answer **sign-wrong**: **+9.99 Mt as scored vs −6.01 Mt with
capture applied**, on NEISO 2030 (`FINDING-scn-ws2b-2026-09-06.md` §8). Ruling **S5** holds every
case carrying that exposure, and this ladder carries it in three of its five years.

**What is committed and unrun:** `docs/handoffs/scn-ws1b/launch_ladder.sh` and
`docs/handoffs/scn-ws1b/carbon-ladder-cases.yaml` (rungs `CARB-LO` / `CARB-MID` / `CARB-HI`).

**What releases it:** the capx lane's repair of the CCS emission-rate seam in
`src/market_sim/model/capacity_evolution/ccs.py` — **explicitly not this lane's file** (the routed
defect). After that repair the ladder runs as §3.5 specifies, with no other change. **Note the
form change carries into it:** §3.5's rungs were written as `carbon_price_delta` 15/25/50 while
D-1 was open; under the S2 floor the ladder should be re-expressed on the `carbon_price_path`
axis (`low`/`mid`/`high`), whose rungs are now meaningful — and which, per §1, only bites from
2027 on.

## 8. Scorecard rows and matrix cells landed

<!-- FILL -->

## 9. What remains for Stage A-LOAD

<!-- FILL -->

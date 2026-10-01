# FINDING — the T1-H capacity-expansion entry defect, root-caused

_2026-08-23 · ENTRY-SCREEN DIAGNOSTIC lane · **NO LP SOLVE, NO HINDCAST RE-RUN, NO
MECHANISM / DEFAULT / CONSTANT CHANGED.** Every number below is either read from a
committed artifact or computed by replaying committed code arithmetic on committed
constants and the committed screen-signal dumps. Charter: `model-methodology-spec.md`
§5.1 steps 3–6 + §5.5; program `docs/forecast-development-plan-2026-07.md` (T1-H)._

Subjects: the two T1-H capacity hindcasts merged at `fc9f9ec` —
**ERCOT** `ercot-2021-2025-realized-t1h-refresh` (registration `03df9c2`, bundle key
`28cef3500ec1fd9e`) and **CAISO** `caiso-2021-2025-realized` (registration `6987c49`,
bundle key `408f9199a82f5814`).

---

## 0. The one-paragraph answer

**Both ISOs' entry defects are downstream of a single object: in the T1-H forecast lane
no capacity screen ever sees a market price.** Under `entry_lookahead_reprice` — cell
`K`/`fc K` in *both* ISO shards, and armed in both runs — every screen (economic
retirement, CCS retrofit, economic new entry, storage entry) reads one re-derived
array from `runner._lookahead_reprice_signal`: a **marginal-cost step function
evaluated at net load** (`runner.py:768`, `prices_h = mc_sorted[min(idx, …)]`), plus an
optional ORDC scarcity adder, **broadcast identically to every zone**
(`runner.py:838`, `return np.tile(prices_h[None, :], (n_zones, 1))`; the runner's own
comment at `runner.py:3448` states it: *"system row; every zone identical"*). Measured
on the committed ERCOT dumps, that object's **energy-shape content is essentially nil**
— its daily top-4/bottom-4 spread is **$3.83–$8.44/MWh** in three of four decision
years — so **84–100 % of gas_cc's entry margin and 57–97 % of storage's arbitrage
spread is the ORDC adder, not the price shape**. CAISO ran with
`scarcity_price_overlay = False`, so **CAISO's entry signal carries no adder at all** and
is a pure MC step function: that is why CAISO storage entry is exactly zero while
ERCOT — an ISO with *no* capacity market and *no* AS credit — built 5 GW. On top of
that signal sits a **bang-bang allocator**: a technology that clears by \$1 builds its
*entire* cap (`new_entry.py:1441`; `storage.py:1897`), so the queue caps, not the
economics, are the forecast.

**CAISO's Path-15 belly and CAISO's storage miss are TWO OBJECTS, not one.** §5.

---

## 1. What each headline number actually came from

Every row cites the code path that produced it. "Replayed" means the arithmetic was
re-executed here on committed inputs and **reproduced the ledger exactly**.

### 1.1 ERCOT

| ledger line | mechanism, with citation | status |
|---|---|---|
| gas_cc **+3588 %** (9.0 GW model vs 0.244 actual), cap-bound every decision year | `new_entry.py:1441` `build_mw = min(group_remaining[group], remaining)` against `QUEUE_CAP_PER_TECH_GW["ERCOT"]["gas_cc"] = 3.0` (`capacity_market.py:3588`). The screen decides only the **sign**; the **cap** decides the volume. | **DEFECT D-1** |
| gas_ct **+105 %** (7.571 GW) | Same allocator; volume set jointly by `QUEUE_CAP_PER_TECH_GW["ERCOT"]["gas_ct"] = 3.0` and the shared `QUEUE_CAP_GW["ERCOT"] = 12` ISO budget (`new_entry.py:973`, `:1441`). **Not** the adequacy backstop — `resolve_reserve_margin_build_enabled` (`adequacy.py:421`) returns `MARKET_DESIGN["ERCOT"].capacity_market = False`, and the ERCOT shard's `reserve_margin_backstop` cell is `.`/`.` (n/a). | **DEFECT D-1** |
| storage **all 5 GW in 2023**, as `iron_air 3.0` + `flow_battery 2.0`, **no li-ion** | `storage.py:1892-1901`. **REPLAYED EXACTLY** (§2): on the committed signal, all six techs clear only in the entering-2023 year; the top-2 by absolute margin take `budget × STORAGE_TECH_BUILD_SHARE_CAP` and then the remainder. li-ion is **not unprofitable** — `li_ion_4hr` clears at **+\$1.47 M/MW-yr** — it is **6th of 6 on absolute \$/MW-yr** and the budget is gone. | **DEFECTS D-1, D-2, D-3** |
| storage carries **no availability-year gate** | `apply_storage_new_entry` iterates `STORAGE_TECHS` unconditionally (`storage.py:1855`), whereas the thermal path gates emerging techs through `_EMERGING_AVAILABLE_YEAR` (`new_entry.py:184`, `:258-263`). A 2023 ERCOT decision year therefore builds 3 GW of 100-hour iron-air and 2 GW of vanadium flow. | **DEFECT D-2** |
| wind **ZERO economic entry** (0.35 GW procured-only) while solar carries the VRE build | **Downstream of the signal, not of a wind mispricing.** Measured capture ratio vs the flat signal mean (§3): wind **0.743 / 0.494 / 0.805 / 0.927**; solar **1.745 / 2.581 / 1.379 / 1.027**. Because ~90 % of the signal's dispersion *is* the ORDC adder — a summer-afternoon object — solar is by construction correlated with the entry margin and wind anti-correlated. `new_entry.py:1182-1204` values each VRE candidate on `Σ_t cf_t·p_t`, so it faithfully transmits that. | **BEHAVIOUR B-3** (defect is upstream: D-8) |
| ORDC adder for capacity economics collapses; RM 19.0 → 8.5 → 14.7 → 25.2 % | Real cross-year cobweb of a one-pass, no-foresight entry loop on a scarcity-priced energy-only market. `capacity_screen_scarcity_restoration` = `fc K` in the ERCOT shard. | **BEHAVIOUR B-2** (amplitude set by D-1) |
| retirements **0 GW** 2021–2024 | `screen_reserve_value_enabled` reserve uplift + the scarcity-fat signal keep every unit above its bar; the report's own D-24 gate already finds **0 of 2** ≥300 MW target exits reachable. | **BEHAVIOUR B-4** |
| 2025: entire coal fleet (40 tranches, 14.0 GW) + 48 gas_st tranches fail the screen, all 88 held `entry_capped` | `retirements.py:1490-1510` — the joint-entry reliability floor un-admits candidates until scheduled accredited firm clears the shared PRM requirement. The **exit-side mirror of the same cobweb**: the 2025 signal is the year the adder is \$1.17/MWh. | **BEHAVIOUR B-2** |

### 1.2 CAISO

| ledger line | mechanism, with citation | status |
|---|---|---|
| storage **0 MW vs 15,147 actual** — the dominant miss | Not the ceiling and not the budget: `STORAGE_DEPLOYMENT_CEILING_MW["CAISO"] = 25_000` against a 2020-vintage measured seed, so `storage.py:1843-1845` never short-circuits. **Every tech's margin is negative** because the arbitrage term is ≈0: CAISO's `scarcity_price_overlay = False` ⇒ `adder = None` (`runner.py:772-773`) ⇒ the entry signal is a **pure MC step function** with no intraday shape. Break-even table in §4. | **DEFECT D-8** (signal), gated by **D-9** (no AS credit) |
| gas_ct **+8630 %** — 11,838 MW vs 136 actual, via `reserve_backstop` | `apply_reserve_margin_build` (`adequacy.py:485-488`) caps its build at **`QUEUE_CAP_GW["CAISO"] = 8.0 GW`**, the ISO TOTAL — **never** at `QUEUE_CAP_PER_TECH_GW["CAISO"]["gas_ct"] = 1.0`. Economic gas_ct entry *is* capped at 1.0. Two mechanisms build the same technology under two different caps. The growth ladder **is** shared (`adequacy.py:452-464`, `evolve.py:805-808`) — so **half** the rule-19 reconciliation was done and half was not. | **DEFECT D-5** |
| reserve margin ratchets 21.0 → 17.6 → 28.2 % | The backstop builds to the entering year's peak; nothing exits when the peak recedes, and the reliability floor then protects the CTs the backstop built. One-directional by construction. | **DEFECT D-6** |
| wind +757 %, solar −24 %, RPS dual pinned at the \$50 ACP | Renewables arrive as pace-ladder chunks because the entry signal cannot price them: same D-8 object. The ACP pin is the RPS constraint's escape valve, i.e. the LP reports "no buildable supply at any price the screen will clear". | **DEFECT D-8**, downstream |
| Diablo Canyon **false-retires 2.24 GW** | 2020-vintage EIA-860 carries the 2016 settlement dates; SB 846 (2022-09) post-dates the cutoff. | **BEHAVIOUR B-1 — correct ex-ante. Do not "fix".** |
| CO2 flat 36.3/36.6/35.7 Mt vs actual 26.1 → 18.7 | The integrated cost of the storage zero + the CT fill + Diablo. Not an independent defect. | derived |

---

## 2. The decisive measurement — the ERCOT storage screen, replayed exactly

`apply_storage_new_entry` (`storage.py:1756-1902`) was re-executed on the **committed**
`screen_signal_diag_*.npz` price signals and the **committed** constants
(`STORAGE_TECHS` `capacity_market.py:357`; `STORAGE_ANNUAL_BUILD_CAP_MW` `:532`;
`STORAGE_TECH_BUILD_SHARE_CAP` `:547`; `ira_itc_storage = 0.30`;
`real_discount_rate = (1.08/1.022) − 1 = 0.056751`; `_STORAGE_ECONOMIC_LIFE_YR = 20`).
ERCOT `MARKET_DESIGN.capacity_market = False` ⇒ capacity value \$0;
`as_revenue_enabled = False` in this run's `run_config.json` ⇒ AS credit \$0. **The stack
is pure arbitrage.**

| entering year | signal mean \$/MWh | adder mean | li_ion_4hr margin | iron_air margin | flow_battery margin | allocator result |
|---|--:|--:|--:|--:|--:|---|
| 2022 | 45.52 | 14.16 | −57,494 | −48,818 | −186,457 | **nothing** |
| **2023** | **390.96** | **347.71** | **+1,469,715** | **+2,914,066** | **+2,650,473** | **iron_air 3,000 MW + flow_battery 2,000 MW** |
| 2024 | 28.22 | 6.66 | −103,901 | −94,999 | −242,109 | **nothing** |
| 2025 | 19.47 | 1.17 | −143,996 | −137,367 | −289,622 | **nothing** |

margins in \$/MW-yr. **This reproduces the registered ledger exactly** ("all storage
enters 2023 as iron_air 3.0 GW … + flow_battery 2.0 GW", `03df9c2`), which closes the
attribution: no other mechanism is needed to explain the ERCOT storage line.

**Three things this measurement establishes that the ledger alone could not:**

1. **The screen is not discriminating between technologies on merit.** In 2023 *all six*
   techs clear, by 10–20×. The outcome is decided by rank-order plus a fixed share cap.
2. **The all-or-nothing pattern across years is the ORDC adder, not storage economics.**
   The adder mean moves by a factor of ~300 between adjacent decision years.
3. **li-ion's absence is an allocator artifact, not an economic verdict.** With an
   availability-year gate restricted to li-ion, the *same* signal and the *same*
   allocator yield **`li_ion_8hr 3,000 MW + li_ion_4hr 2,000 MW`** (arithmetic in §7,
   L-3).

---

## 3. The entry signal has almost no energy-price shape

Measured on the four committed ERCOT dumps. `price_base` is `mc_sorted[idx]`;
`adder` is the ORDC term.

| entering | base min | base p50 | base max | daily top4−bot4 spread, **base only** | same, **base+adder** | adder share of spread |
|---|--:|--:|--:|--:|--:|--:|
| 2022 | 24.84 | 29.21 | 55.80 | **8.44** | 76.50 | **89.0 %** |
| 2023 | 25.06 | 32.44 | 174.77 | **36.47** | 1,124.89 | **96.8 %** |
| 2024 | 16.36 | 21.85 | 32.73 | **4.42** | 37.62 | **88.2 %** |
| 2025 | 13.73 | 18.71 | 26.10 | **3.83** | 8.83 | **56.6 %** |

Share of the **gas_cc entry energy margin** (`Σ_t max(p−vc,0)`, `new_entry.py:1104-1108`,
at `vc = $30`) attributable to the adder alone: **83.6 % / 96.1 % / 99.9 % / 100.0 %**.
In the last two decision years the base merit price never exceeds \$30/MWh, so the
**entire** entry margin is the scarcity overlay.

**Why the base signal is shapeless, structurally.** It is a marginal-cost step function
evaluated at *net* load. Its floor is the cheapest **dispatchable** unit's MC; a
zero-MC renewable never sets it, because renewables are netted out of load rather than
priced into the stack. So the signal cannot represent a renewable-oversupply trough — a
negative or zero midday price — at all. **That trough is exactly where CAISO storage
arbitrage lives.**

---

## 4. CAISO storage: the exact break-even, and what would and would not close it

Non-arbitrage terms are exactly determined:
`MARKET_DESIGN["CAISO"].net_cone_per_kw_yr = 88.08` (`capacity_market.py:1216`);
`caiso_storage_nqc_accreditation = False` ⇒ generic ELCC table
(`capacity_market.py:2787`); `capacity_deliverability_limits = False` ⇒
`_deliverability_capacity_factor = 1.0` (`storage.py:1739-1740`);
`as_revenue_enabled = False` **and** `AS_REVENUE_PER_KW_YR_BY_ISO` has no CAISO row
(`ancillary.py:112-115`) ⇒ AS credit \$0.

Required arbitrage to clear (`$/MW-yr`), and the **raw round-trip spread the price shape
must deliver in EVERY arbitrage window of the year** to supply it:

| tech | capacity value | annual cost | required arbitrage | required \$/MWh spread, **every window** |
|---|--:|--:|--:|--:|
| li_ion_4hr | 52,848 | 148,485 | 95,637 | **88.14** (365 daily windows) |
| li_ion_8hr | 76,630 | 260,859 | 184,229 | 82.81 |
| **iron_air** | 88,080 | 138,859 | 50,779 | **14.36** (40 nine-day windows) |
| flow_battery | 81,914 | 294,319 | 212,405 | 64.03 |
| compressed_air | 76,630 | 170,460 | 93,830 | 35.88 |

**The sharpest number in this document: iron-air needs only a \$14.36/MWh spread over
9-day windows and still built zero.** Measured against §3 — a pure base-merit signal
delivers **\$3.83–\$8.44/MWh** daily — that is the confirmation that CAISO's entry
signal has no usable intraday shape whatever, and it is a *level* statement, not a
locational one.

**What the two gated CAISO arms would do (arithmetic, so no solve is needed to know):**

| arm | li_ion_4hr required spread | iron_air required spread | verdict |
|---|--:|--:|---|
| shipped | 88.14 | 14.36 | — |
| `caiso_ra_mpb_capacity_anchor` (138.36) | 67.47 | **1.79** | narrows; **does not close li-ion** |
| `caiso_storage_nqc_accreditation` (0.865) | 72.14 | 17.33 | narrows li-ion, **worsens iron-air** |
| both | 42.35 | 6.46 | still above the measured base-signal spread |

⇒ **Arming the anchor will not make CAISO storage appear**, because the binding term is
the arbitrage the signal cannot produce, not the capacity price. This is worth stating
plainly so a future lane does not spend a solve on that expectation.

---

## 5. Are the CAISO belly and the CAISO storage miss ONE object or TWO?

### **TWO OBJECTS.** Two independent measurements say so.

**Measurement 1 — the storage screen has no channel for a zonal spread.**
`runner.py:838` returns `np.tile(prices_h[None, :], (n_zones, 1))`; the runner asserts
it in its own log line at `runner.py:3448` (*"system row; every zone identical"*); the
storage screen consumes precisely that array
(`runner.py:1786`, `storage_screen_prices = prior_results.get("price_signal")`), and
CAISO's run had `entry_lookahead_reprice = True`. A north–south price split at Path 15
therefore **cannot reach the screen**: `estimate_storage_revenue`'s per-window
best-zone selection (`storage.py:1486`) is a no-op on a zone-flat array.

**Measurement 2 — the magnitudes are different in kind.** caiso-215 localises the belly
as a **redistribution**: south + ZP26 carries ~100 % of the net gap, NP15 under-prices,
and **the spread nets to ≈0 across the ISO**. The CAISO storage miss is a **system-level
level shift** of \$95,637/MW-yr for li_ion_4hr (§4). A redistribution that nets to zero
cannot supply a level shift of that size.

**The one honest caveat, stated so it is not lost.** They would become **one object**
under `entry_lookahead_reprice = False`, where the screens fall back to
`prior_results["prices"]` — the LP duals — and the best-zone selection becomes live.
That is not the configuration either run used, and the cell is `K`/`fc K` in both
shards. So: *not one object as configured; one object only under a posture nobody has
run.* That conditional is itself a measurement worth taking (L-1).

---

## 6. Defects vs correct-but-unflattering behaviour

### DEFECTS

- **D-1 — Bang-bang entry volume (BOTH ISOs, both screens).** `new_entry.py:1441` and
  `storage.py:1897`: a technology clearing by \$1 builds its full cap. There is no
  entry-until-margin-exhausted condition anywhere in step 5. The queue caps are
  ceilings being used as forecasts. This is the direct producer of ERCOT gas_cc
  +3588 % and of the 3.0/2.0 GW storage split.
- **D-2 — Storage entry has no availability-year gate.** `storage.py:1855` vs
  `new_entry.py:258-263`. The thermal path has the gate; the storage path does not.
- **D-3 — Storage merit metric + share cap.** Ranking is absolute \$/MW-yr
  (`storage.py:1888`) and the winner takes a fixed **volume** share, not a share of
  value. `STORAGE_TECH_BUILD_SHARE_CAP = 0.6` is documented *"Source: modeling
  assumption"* (`capacity_market.py:545-547`) — **a rule 5 `[R-NO-MAGIC]` finding: an
  uncited constant sitting in the entry path that alone determines the ERCOT
  technology split.** Reported, not fixed.
- **D-4 — `compute_storage_annual_cost` ignores per-tech life and per-tech WACC.**
  `storage.py:1681` uses `_STORAGE_ECONOMIC_LIFE_YR = 20` for **every** tech, while
  `STORAGE_TECHS` carries `lifetime_yr` 25 (flow_battery) and 40 (compressed_air) that
  **nothing reads**; and it uses flat `config.real_discount_rate` where the thermal/VRE
  path uses `resolve_real_discount_rate` (`new_entry.py:1119`). *Direction matters:*
  both biases push the long-life techs' cost **up**, so this defect works **against**
  flow_battery — it is a specification defect, **not** the cause of the flow_battery
  build. Recorded so a later lane does not mistake it for one.
- **D-5 — The adequacy backstop bypasses the per-tech queue cap (rule 19 half-done).**
  `adequacy.py:485-488`. See §7 L-2 for the arithmetic.
- **D-6 — The backstop ratchets and cannot unwind.** Structural one-directionality:
  built to a peak year, protected thereafter by the reliability floor.
- **D-7 — The entry-screen diagnostic dump is gated on the wrong flag.**
  `runner.py:3382`, `_diag = {} if unified_screens else None` — the
  `screen_signal_diag_*.npz` artifact is tied to `capacity_screen_unified_lookahead`, a
  *behavioural* gate, rather than to a diagnostics gate. CAISO ran with that flag off,
  so **its bundle has no dump and its entry screen cannot be diagnosed offline at all.**
  This is why several CAISO statements in this document are inferred from the ERCOT
  dump plus exact arithmetic instead of measured directly, and it is what forces a
  solve (§8).
- **D-8 — The capacity-screen price signal carries no energy shape (the root object).**
  `runner.py:768` + `:838`. Zone-flat; MC-step; renewables netted rather than priced;
  no congestion, no commitment markup, no storage opportunity cost. 84–100 % of every
  screen's margin is the scarcity/reserve overlay. **This is the single object that
  produces the CAISO storage zero, the ERCOT wind/solar inversion, and the shape of the
  ERCOT cobweb.**
- **D-9 — `as_revenue_enabled = False` in both runs** while the code's own docstring
  says omitting AS *"undervalues storage ~6x"* (`ancillary.py:8-12`). The registry is
  honest (only ERCOT is populated, `AS_REVENUE_PER_KW_YR_BY_ISO`), so this is a
  **posture** finding, not a mis-specification — but any CAISO storage lever must state
  that CAISO storage earns \$0 AS in this lane by construction.

### CORRECT-BUT-UNFLATTERING (rule 1 `[R-STRUCT]` cuts both ways)

- **B-1 — Diablo Canyon.** Honest ex-ante information-set miss. **Do not fix.**
- **B-2 — The ERCOT cobweb is a real energy-only dynamic.** A one-pass, no-foresight,
  adaptive-expectations entry loop against a scarcity-priced energy-only market
  *should* oscillate. "The number is wrong" is not evidence of a defect here. What D-1
  contributes is the **amplitude**, not the oscillation: a cap-bound build cannot
  under- or over-shoot proportionally to the signal, so each swing is maximal. The
  measurement that separates them is named in §7 L-1b.
- **B-3 — ERCOT wind's zero economic entry.** The VRE screen faithfully transmits the
  signal it is given (§3). The defect is D-8, upstream. Do not open a wind-screen lever.
- **B-4 — ERCOT retirements 0 GW.** Largely correct under information gating; D-24
  already finds 0 of 2 reachable ≥300 MW exits.
- **B-5 — `capacity_screen_unified_lookahead` off in CAISO** means CAISO's 2023 screens
  read a signal priced for the bridge year. Real, small, and *separate* from everything
  above; noted for completeness.

---

## 7. Lever queue — named, prioritised, per-ISO, each with its adjudicating measurement

**Rule 25 `[R-ISO-SCOPE]`: no verdict transfers.** Where a lever is listed for both ISOs
it enters each ISO's shard independently as `U` and each lane derives its own
parameters from its own market's data. **Rule 26 `[R-MECH-MATRIX]`: this lane tests
nothing and adds no cell.** Any NEW mechanism below needs its base row in
`docs/codebase-site/data/mechanism-matrix.js` plus a cell line in **every** shard, in
its arming PR.

### Matrix cells checked before writing this queue

`docs/codebase-site/data/mechanism-matrix/{ERCOT,CAISO}.js`, plus
`docs/mechanism-testing-matrix.md` §5.1 / §5.2:

| cell | ERCOT | CAISO | consequence for this queue |
|---|---|---|---|
| `entry_lookahead_reprice` | `K` / `fc K` | `K` / `fc K` | keeper — L-1 is a **measurement of its cost**, not a proposal to disarm it |
| `storage_entry_value_stack` | `K` / `fc K` | `K` / `fc K` | as above |
| `capacity_screen_unified_lookahead` | `O` / `fc K` | `U` / `U` | CAISO arming is open (also fixes D-7 for CAISO) |
| `capacity_screen_scarcity_restoration` | `O` / `fc K` | `U` / `U` | — |
| `entry_vre_capacity_revenue` | **`I` / `I`** | `U` / `U` | **DO NOT re-propose for ERCOT** (inert: energy-only pays \$0) |
| `entry_dampers` | **`I` / `I`** | `O` / `O` | **DO NOT re-propose for ERCOT** |
| `entry_pipeline_aware_signal` | `O` / `fc K` | `U` / `U` | armed in the ERCOT run, off in CAISO's |
| `reserve_margin_backstop` | `.` / `.` (n/a) | **`K` / `fc K`** | L-2 reconciles its **cap source**, never the mechanism |
| `caiso_ra_mpb_capacity_anchor` | `.` | `O` / `O` | open — but §4 shows it is **insufficient alone** |
| `caiso_storage_nqc_accreditation` | `.` | `O` / **`fc R`** | **DO NOT propose arming in the forecast lane** — `fc` is REJECTED (FFR-4E) |
| `ordc_scarcity_overlay` | **`R`** (ERCOT-97) | `K` | ERCOT backcast cell is refused; the forecast-lane adder is the separate `capacity_screen_scarcity_restoration` object |
| `capacity_deliverability` | `.` / `U` | `K` / `U` | forecast-lane cell `U` in both |
| `vre_procurement_additions` | `O` / `fc K` | `U` / `U` | armed in the ERCOT run only |

**Two fresh adjudications explicitly honoured, not re-opened:**
`miso_offer_level_dispersion` = `R` (miso-179) — untouched, MISO is out of scope here.
`ercot_adaptive_fixed_point` = MEASURED-INERT-AT-FIXED-POINT (ercot-230) — **checked and
found NOT to collide with L-1b.** ercot-230 iterated the *within-year backcast
offer-conduct* adaptation map (spikes → floors → spikes) and measured it converged after
zero passes. L-1b is a *cross-year capacity-entry* volume question in the forecast lane.
Different object, different lane, different year grain. Stating this explicitly is the
DO-NOT-REDO duty discharged, not waived.

---

### **L-1 (BOTH, highest value) — measure the cost of the shapeless entry signal.**
*Not a mechanism proposal. A measurement, taken before anyone proposes anything.*

- **Object:** `runner._lookahead_reprice_signal` (`runner.py:603-838`); D-8.
- **What it would touch if later armed:** nothing yet — this rung produces evidence only.
- **Measurement (no LP):** `scripts/probes/ffr9b_entry_screen_replay.py` already
  re-invokes `apply_economic_new_entry` / `apply_storage_new_entry` off a committed
  bundle. Replay both screens at the identical fleet state against
  `prior_results["prices"]` (the LP duals) instead of `price_signal`, and report the
  delta in (i) each tech's margin sign, (ii) the storage tech ranking, (iii) the
  wind/solar capture ratios. **This is exactly the counterfactual §5's caveat names**,
  and it decides in one pass how much of both ISOs' entry error is signal construction
  rather than screen specification.
- **Rule 19 `[R-ONE-MECH]`:** what already governs the entry price is
  `entry_lookahead_reprice` + `capacity_screen_unified_lookahead` +
  `capacity_screen_scarcity_restoration`. A future lever here must **REPLACE** the
  signal's construction, never stack a shape correction on top of it.
- **Blocker:** for CAISO this requires committed hourly LP prices from the hindcast
  bundle, which the CAISO bundle does not carry — see L-5 / §8.

### **L-1b (ERCOT) — separate the cobweb (B-2) from the bang-bang amplitude (D-1).**
- **Measurement (no LP):** off the same committed dumps, recompute each decision year's
  build under a **margin-proportional** volume rule bounded by the same caps, and
  compare the resulting reserve-margin trajectory to the registered
  19.0 → 8.5 → 14.7 → 25.2 %. If the oscillation survives, B-2 is confirmed as real
  market dynamics and D-1 owns only the amplitude; if it collapses, D-1 owns the
  oscillation itself. **Nothing downstream should be proposed until this is answered.**
- **Rule 21 `[R-DOF]` — stated in those words:** any *elasticity* or *damping* parameter
  chosen to make this trajectory match is **an open root-cause issue, not a parameter.**
  The only admissible closure is an equilibrium condition the model already contains
  (build until the screen's own repriced margin is exhausted), never a tuned coefficient.

### **L-2 (CAISO) — reconcile the adequacy backstop's cap with the per-tech queue cap.**
- **Field/constant:** `adequacy.py:485-488` (`QUEUE_CAP_GW` → should consult
  `QUEUE_CAP_PER_TECH_GW[iso]["gas_ct"]` as well). Cell: `reserve_margin_backstop`
  CAISO `K`/`fc K` — **the mechanism is a keeper and is not in question; only its cap
  source is.**
- **Rule 19:** this **RECONCILES**, it does not stack. Two channels already build
  `gas_ct` and already share the growth ladder (`evolve.py:805-808`); this makes them
  share the per-tech queue cap too, closing the half that was left open.
- **Measurement — already taken, arithmetic on the committed ledger:**

  | year | shipped | under the 1.0 GW/yr per-tech cap | deferred |
  |---|--:|--:|--:|
  | 2022 (bridge) | 4,402 | 1,000 | 3,402 |
  | 2023 | 5,281 | 1,000 | 4,281 |
  | 2024 | 1,676 | 1,000 | 676 |
  | 2025 | 478 | 478 | 0 |
  | **total** | **11,837** | **3,478** | **8,359** |

  vs **136 MW actual**: the error falls from **87×** to **26×**. **So this lever is
  real and necessary but is NOT the CAISO fix** — it removes two-thirds of the wrong
  technology and leaves an adequacy gap that D-8/L-4 must fill with the right one.
  Recording that here is the point: do not charter L-2 expecting it to close CAISO.

### **L-3 (BOTH) — availability-year gate on storage technologies.**
- **Field:** a `_STORAGE_AVAILABLE_YEAR` mapping consumed in `storage.py:1855`, built on
  the **same pattern** as `_EMERGING_AVAILABLE_YEAR` (`new_entry.py:184`) with years
  taken from the sources `STORAGE_TECHS` already cites (DOE LDES Liftoff for iron-air;
  PNNL-33283 for flow/CAES). **Zero DOF** — it is a first-commercial-COD date, rule 13
  admissible (it regenerates for any forward year and responds to actual deployment).
- **Rule 19:** nothing currently gates storage-tech eligibility, so this **replaces
  nothing and stacks on nothing** — it supplies a gate the thermal path already has.
- **Measurement — already taken (§2):** on the identical 2023 signal and the identical
  allocator, restricting the pool to li-ion yields **`li_ion_8hr 3,000 + li_ion_4hr
  2,000 MW`** instead of `iron_air 3,000 + flow_battery 2,000`. That converts ERCOT's
  storage error from *wrong technology and wrong volume* to *right technology, wrong
  volume* — which is what makes D-1 separately measurable afterwards.

### **L-4 (CAISO) — the storage-entry arbitrage term is the root-cause issue.**
- **Status: OPEN ROOT-CAUSE ISSUE, NOT A PARAMETER** (rule 21 `[R-DOF]`, in those
  words). §4 shows the gap is \$95,637/MW-yr for li_ion_4hr and that **no combination
  of the two gated CAISO capacity-price arms closes it**. Any adder, uplift, or
  multiplier that closed it would be tuned to the residual and is forbidden by rules
  1/13/21.
- **What may legitimately be chartered instead:** L-1 (does the LP dual carry the
  duck-curve shape the merit signal cannot?). If it does, the repair is a signal
  construction change, structural and zero-DOF. If it does not, the root cause is
  further upstream in CAISO's own price formation and belongs to the backcast lane —
  which is the *only* way the belly and the storage miss could ever become one object,
  and it would be established by measurement rather than assumed.
- **Explicitly refused:** proposing `caiso_storage_nqc_accreditation` for the forecast
  lane (cell `fc R`), and any storage-entry credit calibrated to the 15.1 GW actual
  (rule 13 `[R-MEASURED]` — pinning entry to observed CODs has no forward analogue).

### **L-5 (CAISO, cheap, enabling) — decouple the entry-screen diagnostic dump from `capacity_screen_unified_lookahead`.**
- **Field:** `runner.py:3382`; the natural home is the existing
  `ScenarioConfig.entry_screen_diagnostics` gate (already default-off,
  `new_entry.py:907-918`), which is the *diagnostics* flag this artifact belongs behind.
- **Rule 19:** replaces the wrong gate with the right one; adds no mechanism. Output-only
  — no cache-key term, no solve-path change (the FFR-8A control arm already proved that
  property for this dump).
- **Why it is on the queue at all:** without it, **no CAISO entry-screen question can be
  answered without a solve.** Everything in §4 had to be derived arithmetically because
  CAISO's bundle carries no dump. This is the cheapest lever here and it unblocks L-1.

### **L-6 (both, deferred) — the storage cost/life specification defects (D-4).**
Not a residual lever; a correctness repair. Have `compute_storage_annual_cost` read each
tech's own `lifetime_yr` and route through `resolve_real_discount_rate`. Note the sign:
it makes long-duration storage **cheaper**, i.e. it would push ERCOT *further* toward
iron-air/flow unless L-3 lands first. **Sequence L-3 before L-6.**

---

## 8. What this lane concluded requires a solve (charter item: name it, do not run it)

1. **CAISO entry-screen signal measurement.** CAISO's bundle has no
   `screen_signal_diag_*.npz` (D-7). The minimal solve is a **CAISO 2021–2025 T1-H
   re-run with `capacity_screen_unified_lookahead` armed** (or L-5 landed first, which
   removes the need entirely). **Decides:** whether CAISO's measured base-merit spread
   is below the \$14.36/MWh iron-air threshold, converting §4's inference into a
   measurement. **L-5 is strictly cheaper and should be done first.**
2. **L-1's CAISO half** needs committed hourly LP prices from a CAISO hindcast bundle;
   the ERCOT half may be replayable from committed artifacts today.
3. **Nothing else here needs a solve.** L-2's arithmetic, L-3's counterfactual, §2's
   reproduction, §3's shape measurement and §4's break-even are all closed on committed
   artifacts.

---

## 9. Rule compliance

- **Rule 1 `[R-STRUCT]`** — no lever proposes reaching a number through a mechanism that
  is not real. B-1/B-2/B-3/B-4 are explicitly protected from "fixing".
- **Rule 5 `[R-NO-MAGIC]`** — one uncited constant found in the entry path
  (`STORAGE_TECH_BUILD_SHARE_CAP`, D-3). **Reported, not fixed**, per charter.
- **Rule 13/14 `[R-MEASURED]`/`[R-ACCURATE]`** — no lever pins entry to observed CODs;
  L-3's dates are first-commercial-availability facts that regenerate forward.
- **Rule 19 `[R-ONE-MECH]`** — every lever states what already governs its phenomenon
  and whether it replaces or reconciles.
- **Rule 21 `[R-DOF]`** — L-1b and L-4 are labelled **open root-cause issues, not
  parameters**, in those words.
- **Rule 25 `[R-ISO-SCOPE]`** — no verdict transfers; cross-ISO candidates enter as `U`.
- **Rule 26 `[R-MECH-MATRIX]`** — this lane tested nothing and **adds no cell**. Cells
  checked are listed in §7. New mechanisms need a base row plus a cell line in every
  shard in their arming PR.
- **Out of scope, untouched:** every keeper shard, `calibration-complete.json`,
  `holdout-freeze.json`, the backcast registry, `program-status.json`.

---

## 10. Reproduction

Every measurement in §2/§3/§4 (and L-2/L-3's arithmetic) is re-takeable from committed
artifacts with **numpy only** — no pandas, no highspy, no solve, and a `code` data
profile:

```
python3 scripts/probes/entry_screen_t1h_phase0.py \
    --bundle results/hindcast/ercot-2021-2025-realized-t1h-refresh --iso ERCOT \
    --out results/calibration/entry_screen_t1h_phase0_ercot.json

python3 scripts/probes/entry_screen_t1h_phase0.py \
    --bundle results/hindcast/caiso-2021-2025-realized --iso CAISO \
    --out results/calibration/entry_screen_t1h_phase0_caiso.json

python3 scripts/probes/entry_screen_t1h_phase0.py \
    --bundle results/hindcast/caiso-2021-2025-realized --iso CAISO \
    --capacity-anchor-per-kw-yr 138.36 \
    --out results/calibration/entry_screen_t1h_phase0_caiso_mpb.json
```

The three artifacts are committed alongside this document. The ERCOT run's
`decision_years["2023"].storage_screen.allocator_result` is
`iron_air 3,000 MW + flow_battery 2,000 MW` — the registered ledger, reproduced. The two
CAISO runs carry the §4 break-even tables and a `warning` field recording that CAISO's
bundle has **no** `screen_signal_diag_*.npz` (defect D-7), which is precisely why only
the break-even half is populated there.

# FFR-4B — MISO solar revenue: published accreditation + VRE capacity payment

**Session:** ffr-4b, 2026-08-04. **Implementation lane** for owner decisions
**D-12** (wire MISO's published solar accreditation) and **D-2′** (arm
`entry_vre_capacity_revenue`), signed 2026-08-04, sitting Addendum O, taken
together as ONE lane. **MISO-scoped only** (rule 25 [R-ISO-SCOPE]).

Both changes are landed. Each is measured **alone**, against a paired control
built at this session's own base commit, in a 2×2 so neither is attributed to
the other.

> **What this lane is NOT.** It does not buy an FC-3 pass and was never
> expected to. The owner took both decisions on **rule-14 [R-ACCURATE]
> grounds and on the asymmetry**, not on expected band movement, and
> explicitly accepted that arming D-2′ **would not have moved the T1-H leg's
> FC-3 band at all** — a 2025 decision commissions at COD 2027, outside the
> 2021–2025 window. Nothing here was tuned toward a band. Two causes outrank
> this lane and are not its subject: the **missing procurement channel**
> (FFR-3V's own #1, owner card D-16, unsigned) and the **2024 entry price
> signal's missing ORDC tail** (FFR-4E, concurrent).

---

## 0. Headline

**Both decisions are landed, MISO-scoped, and each is measured alone.**

1. **D-12 (wire the accreditation).** `RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]`
   now carries a `solar` entry at **0.3875**, replacing the generic 0.18
   fallback. The seasonal→annual selection rule is **settled and grounded**
   (§2): the duration-weighted mean over MISO's four equal-length PRA seasons,
   which reduces to `(50+50+5+50)/4`. Measured alone with the gate off, it is
   **not inert, and its whole effect is in the RETIREMENT screen, not the entry
   screen**: 2024 economic retirements rise **11,931.6 → 13,524.3 MW
   (+1,592.7 MW, +13.3 %)**, because the reliability floor now has MISO's real
   accredited solar to work with.
2. **D-2′ (arm `entry_vre_capacity_revenue`).** Armed as MISO's forecast
   default via `ISOConfig.default_scenario_overrides`; the `ScenarioConfig`
   default stays `False`, so no other ISO moves. Measured alone, it is
   **inert in the 2022–2024 decision years** (MISO long, the VRR pays $0 to
   *every* technology — faithful) and **decisive in 2025**: solar's margin
   flips **−33,406 → +25,536 $/MW-yr** and it decides **1,236.4 MW**, MISO's
   first modelled solar entry anywhere in the window, with `binding_cap`
   moving `unprofitable` → `growth_ladder`.
3. **The two are additive and non-interacting**, and the wiring is *more*
   subordinate than FFR-3V's ranking implied: with the gate also armed it adds
   **$68,459/MW-yr of margin and ZERO extra megawatts**, because solar is then
   ladder-bound, not margin-bound.
4. **Nothing moves the band.** Cumulative *commissioned* build is **identical
   in all four arms** — solar 0.0 GW in every one — because the 2025 decision
   commissions at COD 2027, outside the 2021–2025 window. Caveat (i) is
   therefore **measured, not assumed**.
5. **The asymmetry is closed and the function is now symmetric** (§4): VRE was
   the only accredited resource class denied the payment while thermal entry,
   thermal retirement and storage entry all took it through the same seam —
   *while VRE's accredited MW already depressed the price those three
   collected*. Arming removes an exception; it adds no second channel.
6. **Relative size, stated plainly:** this lane is small next to the two causes
   that outrank it — the missing IRP/RFP/corporate-PPA procurement channel
   (D-16, unsigned) and the 2024 price signal's missing ORDC tail (FFR-4E).
   That is the correct relative size, not a disappointment.

---

## 1. State verified at this session's own head

Re-read at head, not taken from the dispatch prompt.

* `origin/main` = **`5eac75b0`** at fetch — the commit the prompt named. All
  four arms are built on it; the two treated arms differ from the control only
  by the change under test.
* Keeper shards read directly: ERCOT `2026-08-03-ercot158-pool-arm`, PJM
  `2026-08-04-pjm-152-collapse`, CAISO `2026-08-04-caiso-166-measured-dlap`,
  NYISO `2026-08-04-nyiso-125-seam-envelope`, NEISO
  `2026-08-04-neiso81-chpheatrate`, **MISO `2026-08-04-miso-127-onlinepmin`**.
  The matrix header's MISO stamp already matches; no keeper work was done here.
* Markers: `complete` = {NEISO, NYISO, PJM} — **MISO is in neither block**;
  `final` empty; **holdout freeze active**. Every solve in this lane is
  **forecast-mode** over the plain-hindcast allowed set {2021, 2023, 2024,
  2025} with 2022 bridged and never solved. **No out-of-training backcast
  year was solved, scored or read** (rule 22 [R-HOLDOUT]).
* `env | grep MARKET_SIM` — **empty**, so no cache-key shift (FFR-3F §5).
* Prerequisites run in order: `uv sync`, then `scripts/regenerate_clean.py`
  (50/50 datatypes regenerated, no failures, `git status --short` clean of
  tracked-file deletions afterwards).
* **Rule 12, and why this session ran the arms SEQUENTIALLY rather than at the
  permitted 2-way concurrency:** the container has **15 GB RAM / 4 cores**, and
  a single MISO solve holds **7.3 GB RSS** measured. Two concurrent MISO
  invocations would need ~14.6 GB against 15 GB total, so the RAM ceiling —
  not rule 12's cap — is binding here. Each arm is ~35 min wall-clock
  (four solved years at ~9 min each).
* **Which side of FFR-4C these measurements sit on: BEFORE it.** FFR-4C (D-13,
  the wind PTC 10-year window) is concurrent and also moves MISO entry-screen
  revenue — it *lowers* wind while this lane *raises* solar. Every number below
  is measured at base `5eac75b0`, i.e. with the **unwindowed** wind PTC still
  crediting 30 years. If 4C lands first, these numbers must be re-verified
  against the new base before being quoted; the *direction* of this lane's
  legs is independent of 4C (they act on solar's capacity revenue and on the
  adequacy ledger, not on wind's PTC), but the *levels* — and in particular
  wind's per-tech queue-cap competition with solar — are not.

### 1.1 The control is validated against FFR-3V to the dollar

The control arm resolved to cache key **`ca36ba26ebe1640f`** — byte-identical
to the key FFR-3V's own instrumented run minted — and reproduces its ledger
exactly: solar `binding_cap: "unprofitable"` in all four decision years at
margins **−26,446 / −22,681 / −35,946 / −33,406** $/MW-yr, wind profitable in
all four building **4,000 / 0 / 4,000 / 0** MW, reserve margin walking
**27.29 % → 20.66 % → 11.40 % → 17.32 %**, and the 2025 capacity payment
switching on at **$307,808** (gas CT) / **$311,083** (gas CC) per MW-yr. The
paired control is therefore the same object FFR-3V measured, and any delta
below is attributable to the change under test rather than to a moved base.

**Caveat (i) is visible mechanically in the control**, not just asserted: the
2025 decisions (gas_ct 1,483.8 MW + gas_cc 3,000 MW = 4,483.8 MW) appear in
the *screen* but **not** in the year's commissioned build, because
`ENTRY_COD_LAG_YEARS = 2` puts their COD in 2027 — outside the 2021–2025
window. Whatever this lane does to a 2025 decision cannot move this leg's FC-3
band. Cumulative *commissioned* build in-window, control: wind 4,000 MW,
storage 4,000 MW, planned gas_cc 1,146 MW.

---

## 2. The seasonal → annual selection rule, and what it is grounded in

**SETTLED HERE, not left implicit** (scope item 1). MISO's published solar
accreditation is **seasonal**; `RENEWABLE_ELCC_CURVES_BY_ISO` is **annual**.
That is a genuine time-aggregation misalignment of exactly the kind rule 14
[R-ACCURATE] says to **reconcile**, not to lift raw or to replace with a guess.

### 2.1 What is published, and what was already on disk

`data/raw/capacity-market/elcc/miso/miso.csv` carries two `MISO,solar`
`class_average` rows from the **PY 2025-26 Wind and Solar Capacity Credit
Report** cover-page Highlights:

| row | credit | seasons |
|---|---|---|
| default seasonal solar capacity credit | **50 %** | Summer / Fall / Spring |
| default solar capacity credit | **5 %** | Winter 2025-26 |

It is a **flat default, not a penetration curve** — MISO publishes no
probabilistic solar ELCC-vs-penetration series (its 15-year curve is for wind
only). The rows were intaken at P-0B/N6; only the wind rows were ever wired,
so MISO solar fell all the way down the CR-3.1 ladder — no rung-0 NQC entry,
no rung-1 curve, no rung-2 per-ISO point override — to **rung 3, the generic
0.18 flat fallback**, which contains no MISO content at all.

### 2.2 The rule

> **Duration-weighted mean over MISO's four PRA seasons**, which reduces to
> the equal-weighted arithmetic mean because the four seasons are
> equal-length quarters:
> **(50 + 50 + 5 + 50) / 4 = 38.75 % → `0.3875`**

Encoded as a **single-point (constant) curve**, `penetration_basis=None` — the
same shape the NYISO CAF entries use — because MISO published no axis and the
registry's intake discipline forbids fabricating one.

### 2.3 What it is grounded in

Two published facts and one property of this model.

**(a) MISO's Planning Resource Auction is seasonal, with four equal-length
seasons.** Since PY2023-24 (FERC-accepted seasonal resource-adequacy
construct, ER22-495; MISO Tariff Module E-1) MISO clears **four separate
seasonal auctions**, each with its own requirement and its own clearing price,
over a June 1 – May 31 Planning Year split into four **three-month** seasons:
Summer (Jun–Aug), Fall (Sep–Nov), Winter (Dec–Feb), Spring (Mar–May). A
resource is paid in **every** season on **that season's** accredited capacity.

**(b) Annual capacity revenue is therefore `Σ_s price_s × days_s × credit_s`.**
This model carries **one** annual capacity price per firm MW
(`MarketDesign.capacity_price_per_firm_mw_yr`) and **one** annual credit —
which is exactly the assertion that the four seasonal prices are equal. Under
that assertion the **revenue-preserving** annual-equivalent credit is the
duration-weighted mean of the seasonal credits, and equal-length seasons make
it the plain mean. The reconciliation is therefore *implied by the model's own
price representation*, not chosen to land on a number.

**(c) It does not carry the result.** Exact-day weighting (92 / 91 / 90 / 92
days) gives 142/365 = **0.3890**, a **+0.0015** difference — an order of
magnitude below the grain of the published 50 % / 5 % figures themselves. The
equal weights are the settled rule; the day-weighted variant is recorded only
to show the choice is immaterial.

### 2.4 The two readings that were rejected, and why

| reading | credit | rejected because |
|---|---|---|
| **summer-only** | 0.50 | pays the winter quarter a credit MISO does not grant — a raw lift of one season onto an annual grain, the misalignment rule 14 names |
| **peak-risk minimum (winter)** | 0.05 | right for a **single-requirement annual** construct (the selection some hydro/NQC registries use), **wrong for MISO**: MISO clears four seasons separately, so a resource is **not** denied its summer revenue because its winter credit is low. It would understate MISO's own payment by ~87 % |
| generic fallback (status quo ante) | 0.18 | not MISO data at all — the ISO-agnostic constant for ISOs with **no** published accreditation, while MISO has one on disk (rule 14) |

### 2.5 One credit, both consumers — deliberately

`resolve_renewable_capacity_credit` is **the ONE resolver every adequacy
consumer prices VRE accreditation through** (rule 19 [R-ONE-MECH]). The 0.3875
therefore serves **both** the entry screen's VRE capacity payment **and** the
adequacy ledger (retirement reliability floor, reserve-margin backstop, CR-1
reserve position). That is why the wiring leg is **not inert with the gate
off**, and why it had to be measured on its own arm — see §3.

---

## 3. The four arms — each change measured alone

Full 2×2, all four at base `5eac75b0`, all four with
`--entry-screen-diagnostics`, all other flags at the harness default (the
"all six solve-affecting flags omitted" posture FFR-3V used). **Cache keys were
checked distinct BEFORE any arm was read.**

| arm | registry | gate | out-dir | cache key |
|---|---|---|---|---|
| **CTL** | unwired (generic 0.18) | OFF | `results/ffr4b/ctl` | `ca36ba26ebe1640f` |
| **GATE** | unwired (generic 0.18) | **ON** | `results/ffr4b/gate` | `27597e342ed68fd1` |
| **WIRE** | **wired (0.3875)** | OFF | `results/ffr4b/wire` | *(see §3.3)* |
| **BOTH** | **wired (0.3875)** | **ON** | `results/ffr4b/both` | *(see §3.4)* |

The registry constant is **not** in the cache key (it is a `constants.py`
value, not a `ScenarioConfig` field), so CTL and WIRE resolve to the *same*
key and GATE and BOTH to the *same* key. **That is why each arm has its own
`--out-dir`**: the cache root is the out-dir, so no arm can silently read
another's cached solve. The unwired arms were run first, at the reverted
registry; the registry was restored only after both had exited.

### 3.1 Arm GATE — arming `entry_vre_capacity_revenue` alone

**Decision years 2022, 2023 and 2024: byte-identical to the control**, every
row, including the thermal rows. The capacity payment is $0 for **every**
technology in all three, so the gate has nothing to unlock. This is the
measured confirmation of FFR-3V's scoping claim, and it is *faithful* — the
real PY2021-22 PRA cleared at ≈$1,825/MW-yr.

*(Mechanism note, read off the arms: decision year N screens on year N−1's
`prior_results`. MISO's reserve margin is 11.40 % in 2024 — below its 13.75 %
requirement — but the **2024** decision screens on **2023**'s long position and
still sees $0. It is the **2025** decision, screening on 2024's short position,
that turns the payment on. The one-year lag, not the crossing year, is what
dates the effect.)*

**Decision year 2025 — the gate is decisive, exactly as measured-predicted:**

| candidate | capacity revenue $/MW-yr | margin CTL → GATE | build CTL → GATE |
|---|---|---|---|
| **solar** | **+58,942** (0.18 × $327,456 firm) | **−33,406 → +25,536** | **0 → 1,236.4 MW**, `binding_cap` `unprofitable` → **`growth_ladder`** |
| wind | +54,358 (0.166 clamp × $327,456) | +18,687 → +73,045 | 0 → 0 (`per_tech_cap_zero` — the pending row consumes the cap) |
| gas_ct | 307,808 (ungated, unchanged) | 182,447 (unchanged) | 1,483.8 MW (unchanged) |
| gas_cc | 311,083 (ungated, unchanged) | 175,844 (unchanged) | 3,000 MW (unchanged) |

This is **MISO's first modelled solar entry decision anywhere in the window**,
and the margin flip is to the dollar what FFR-3V's arithmetic predicted
(−33,406 + 58,942 = +25,536). Solar stops being rejected on economics and
starts being limited by the growth ladder — the failure mode moves from
**margin** to **cap**, which is the wind failure mode, i.e. the two VRE
technologies now fail the same way.

**And it moves ZERO MW inside the scored window.** Cumulative *commissioned*
build is **identical** in CTL and GATE — wind 4,000 MW, storage 4,000 MW,
planned gas_cc 1,146 MW — because the 1,236.4 MW solar decision carries
`ENTRY_COD_LAG_YEARS = 2` and commissions in **2027**. Caveat (i) is therefore
not an assumption carried into this lane; it is a **measured property of the
arm**. Anyone quoting this lane as an FC-3 movement is quoting it wrong.

### 3.2 Arm WIRE — wiring the accreditation alone, gate OFF

**This arm is the reason the lane had to be a 2×2, and its result is the one
a CTL-vs-BOTH comparison would have mis-attributed.** With the gate off, solar
earns **$0** of capacity revenue in every year of both arms — so *nothing* here
comes through the entry screen's payment. Everything below comes through the
**other** consumer of the same resolver: the **adequacy ledger**.

| year | reserve margin CTL → WIRE | what moved |
|---|---|---|
| 2021 | **27.2935 % → 28.5651 %** (+1.27 pp) | MISO's *existing* solar fleet is now accredited at 0.3875 instead of 0.18 |
| 2023 | **20.6571 % → 21.8597 %** (+1.20 pp) | same |
| 2024 | 11.3999 % → **11.3894 %** (−0.01 pp) | the extra accredited MW are **spent**, not banked — see below |
| 2025 | 17.3172 % → 17.3064 % (−0.01 pp) | same |

**The headline of this arm: 2024 economic retirements rise 11,931.6 MW →
13,524.3 MW, +1,592.7 MW (+13.3 %).** Crediting MISO's solar at its published
accreditation gives the **retirement reliability floor** more accredited firm
capacity to work with, so ~1.6 GW *more* thermal is allowed to leave. That is
why the 2024/2025 reserve margins come back almost exactly to the control: the
added accreditation is consumed by additional retirement rather than banked as
headroom.

Second-order consequences, all small and all in the same direction:

* the 2025 firm capacity price rises slightly (2024 closes fractionally
  tighter): gas_ct **307,808 → 309,051**, gas_cc **311,083 → 312,339** $/MW-yr;
* solar's own 2025 margin improves marginally on **energy** revenue alone
  (51,396 → 51,687 $/MW-yr) as the changed fleet re-prices the stack —
  **−33,406 → −33,115**, nowhere near a sign flip;
* cumulative *commissioned* build is **unchanged** (wind 4,000, storage 4,000,
  planned gas_cc 1,146 MW).

So: **the accreditation wiring is inert in the entry screen and materially
live in the retirement screen.** Had this lane run only CTL vs BOTH, +1.6 GW
of extra thermal retirement would have been booked against the capacity-revenue
gate, which did not cause a megawatt of it.

### 3.3 Arm BOTH — the landed configuration

2022, 2023 and 2024 are **identical to arm WIRE** (including the +1,592.7 MW
of 2024 economic retirement), because the gate is still inert in those years.
The whole of the interaction is in 2025:

| quantity | CTL | GATE | WIRE | **BOTH** |
|---|---|---|---|---|
| solar capacity revenue $/MW-yr | 0 | 58,942 | 0 | **127,401** |
| solar margin $/MW-yr | −33,406 | +25,536 | −33,115 | **+94,287** |
| solar `binding_cap` | unprofitable | growth_ladder | unprofitable | **growth_ladder** |
| **solar MW decided** | 0 | **1,236.4** | 0 | **1,236.4** |
| implied firm price $/MW-yr | 327,456 | 327,456 | 328,778 | 328,778 |
| 2024 economic retirement MW | 11,931.6 | 11,931.6 | **13,524.3** | **13,524.3** |

**The two legs are additive and non-interacting in outcome terms.** The gate's
solar decision (1,236.4 MW) is identical with and without the wiring; the
wiring's retirement delta (+1,592.7 MW) is identical with and without the gate.

**And the headline subordination result: the accreditation wiring buys solar
$68,459/MW-yr of extra margin and ZERO extra megawatts.** Once the gate flips
solar profitable, the binding constraint is the **growth ladder**, not the
margin — so a bigger margin cannot buy more build. D-12 is subordinate to
D-2′ exactly as FFR-3V ranked it, and *more* subordinate than expected: in
this window it buys **margin headroom, not build**. (It would stop being
merely headroom the moment the ladder is loosened — which is FFR-4A's
subject, not this lane's.)

### 3.4 Cumulative commissioned build: identical in all four arms

| tech | CTL | GATE | WIRE | BOTH |
|---|---|---|---|---|
| wind | 4,000.0 | 4,000.0 | 4,000.0 | 4,000.0 |
| storage | 4,000.0 | 4,000.0 | 4,000.0 | 4,000.0 |
| gas_cc (planned) | 1,146.0 | 1,146.0 | 1,146.0 | 1,146.0 |
| **solar** | **0** | **0** | **0** | **0** |

This is the single most important line in the lane for anyone reading it as a
scorecard result: **solar's in-window commissioned build is 0.0 GW in every
arm, so the T1-H leg's FC-3 solar band (model 0.0 vs actual 18.649 GW, −100 %)
is UNCHANGED by both decisions.** That is the outcome the owner signed for,
not a shortfall against it.

---

## 4. The thermal-vs-VRE asymmetry (scope item 4)

**Question as charged:** does arming VRE make the function symmetric, or does
it introduce a new inconsistency elsewhere? And, per rule 19 [R-ONE-MECH],
**what already pays VRE capacity value** before a second channel is added?

### 4.1 Enumeration — who is paid at the capacity seam, and behind what gate

There is exactly **one** capacity-price seam in the model,
`MarketDesign.capacity_price_per_firm_mw_yr`. Every call site, read at head:

| consumer | call site | accreditation resolver | gate | shipped default |
|---|---|---|---|---|
| **thermal new entry** | `new_entry.py:899` → `capacity_revenue_per_mw_yr` | `thermal_accreditation_fraction` | **none** | always paid |
| **thermal retirement screen** | `retirements.py:857` (`capacity_revenue_per_mw_yr`) | `thermal_accreditation_fraction` | **none** | always paid |
| **storage new entry** | `storage.py:1196` | `_elcc_for_duration` × saturation derate | `storage_capacity_value` | **ON** |
| **VRE new entry** | `new_entry.py:1012` | `resolve_renewable_capacity_credit` | `entry_vre_capacity_revenue` | **OFF** ← |

Nothing else pays VRE anything that is capacity value. The screen's other VRE
revenue terms are a different quantity in a different unit: merchant energy
(`estimate_expected_revenue`), and the **attribute** payment — the max of the
exogenous EAC, the federal CES premium and the RPS shadow price — which prices
a *clean-attribute MWh*, not a *firm MW*. VRE has no economic-retirement
screen at all, so there is no second VRE capacity channel to reconcile.

**So VRE was the only accredited resource class on the system denied the
payment**, and the gate was the whole reason.

### 4.2 Arming it makes the function symmetric — it does not add a channel

Arming `entry_vre_capacity_revenue` routes VRE through the **same** seam
(`capacity_price_per_firm_mw_yr`), at the **same** locational-deliverability
gate (`_zone_is_long`), on the credit from the **same** single adequacy
resolver the ledger itself uses. It is the *removal of an exception*, not the
addition of a mechanism: after this lane every resource class that is
**counted** in the adequacy ledger is also **paid** at the seam, on the
identical basis it is counted. Rule 19 is satisfied by construction — the
payment and the ledger read one resolver, so they cannot diverge.

### 4.3 The sharper form of the asymmetry, and why the wiring leg bites alone

The pre-lane state was worse than "VRE isn't paid". VRE's accredited MW
**already counted on the supply side** of the adequacy ledger
(`accredited_firm_capacity_mw` → reserve margin → `reserve_position` → the
sloped VRR price). So MISO solar was *depressing the very capacity price that
thermal and storage collected*, while collecting none of it itself.

That is also why **wiring the accreditation is not inert with the gate off**:
raising MISO solar's credit 0.18 → 0.3875 raises accredited firm capacity,
raises the reserve margin, and therefore **lowers** the capacity price paid to
thermal and storage. The two legs of this lane push the entry screen in
*opposite* directions and had to be arm-separated for exactly that reason —
see §3.

### 4.4 The one new inconsistency this lane does introduce

Honest disclosure rather than a clean bill. MISO's arming rides
`ISOConfig.default_scenario_overrides`, which the runner applies to any field
whose value **equals the ScenarioConfig default** (`runner.py:585-593`). An
explicit `--no-entry-vre-capacity-revenue` sets `False`, which *is* the
default, so **the override re-arms it** — the control arm the harness
docstring promises ("`--no-*` forces the control arm explicitly",
`run_capacity_hindcast.py`) is no longer reachable from the CLI for MISO on
this field. It is a pre-existing property of the per-ISO defaults mechanism
(ERCOT's `scarcity_price_overlay` and CAISO's `negative_renewable_offers`
carry it too), not something this lane invented — but this lane makes it bite
on a field controls are actively built against, which is why it is stated
here. **This lane's own controls were therefore run BEFORE the arming
landed**, at the base commit (§3). Fixing it properly means teaching
`run_scenario_iso` to distinguish "explicitly set to the default" from
"unset", which is shared infrastructure touching all six ISOs — out of scope
here, and handed on rather than silently absorbed.

---

## 5. What I did NOT separate

Stated explicitly, because the decomposition above is additive only where it
says it is.

* **I did not separate the two consumers of the accreditation change from each
  other inside arm WIRE.** The arm changes `resolve_renewable_capacity_credit`
  for MISO solar, and *every* adequacy consumer reads it at once — the
  retirement reliability floor, the reserve-margin backstop and the CR-1
  reserve position. §3.2 attributes the +1,592.7 MW to the **retirement floor**
  on the evidence that the delta lands entirely in the 2024 `economic`
  retirement row and that the backstop fires zero MW in either arm; it is
  **not** an arm that isolated the floor from the backstop.
* **I did not separate the 2025 capacity-price move from the fleet it came
  from.** The +$1,243/MW-yr on gas_ct between CTL and WIRE is the sloped VRR
  re-evaluated at a 2024 close that differs *because* 1.6 GW more retired. Price
  and fleet move together by construction; no arm holds one fixed.
* **I did not run a same-arm ablation of the selection rule.** The 0.50 /
  0.3875 / 0.05 readings in §2.4 are adjudicated on MISO's published market
  design, not on solved outcomes, and no arm was run at 0.50 or 0.05. That is
  deliberate — choosing among them by what a solve produces is precisely the
  fitted-input failure rules 1 and 13 forbid — but it means the *sensitivity*
  of these results to the selection rule is unmeasured.
* **I did not measure anything against FFR-4C.** Every arm is at base
  `5eac75b0`, i.e. **before** D-13's wind PTC window. Wind and solar compete for
  the same per-tech queue cap and ladder, so a lane that lowers wind's margin
  can change which technology consumes the cap in a year where both clear.
  These numbers do not survive 4C landing without re-verification (§1).
* **I did not touch, re-score or re-register the T1-H leg
  `miso-2021-2025-realized-ffr3a3`.** No number here supersedes a band on it.
  All four arms are unregistered forecast-family diagnostic probes under their
  own out-dirs, with no scored output (rule 15 registers *backcast* runs).
* **I did not address the two causes that outrank this lane**, and neither is
  in scope: the **missing procurement channel** (18.6 GW built on utility
  IRP/RFP and corporate PPAs against the ITC — FFR-3V's #1, owner card D-16,
  unsigned) and the **2024 entry price signal's missing ORDC tail** (FFR-4E,
  concurrent). Relative to those, this lane is small, and §6 says so plainly.
* **Rule 25 [R-ISO-SCOPE]:** every number here is MISO's own, from MISO's own
  published report and MISO's own code paths. Nothing was imported from another
  ISO's lane and nothing here fills another ISO's cell. The other four
  capacity-market ISOs remain `U` on the new matrix row and must derive their
  own accreditation from their own market's data.

---

## 6. What landed, and one drive-by fix

| file | change |
|---|---|
| `src/market_sim/config/capacity_market.py` | `RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]["solar"]` = single-point 0.3875, with the selection rule, its grounding, the rejected readings and the day-weighted sensitivity in the comment (rules 5/24 — value + citation in the registry, nothing in a per-plant dict or a `getattr` fallback) |
| `src/market_sim/config/iso_configs.py` | MISO `default_scenario_overrides = {"entry_vre_capacity_revenue": True}` — the established per-ISO default mechanism, rule-25 clean (it cannot leak to another ISO), recorded in `run_config.json`, and it enters the cache key |
| `src/market_sim/config/scenarios.py` | field docstring records the MISO-only arming; **the `ScenarioConfig` default stays `False`** |
| `tests/unit/data/test_renewable_elcc_curves.py` | two tests: 0.3875 **re-derived from the committed CSV rows** by the settled rule (so the constant cannot drift from its source, the PJM-blend precedent), and the constant-curve/ladder behaviour |
| `docs/codebase-site/data/mechanism-matrix.js` | **new row `entry_vre_capacity_revenue`** split off the `entry_dampers` family (rule 28(c)), cells `IUUKUU` — MISO **K**, ERCOT **I** (energy-only, provably $0), the other four **U** as separate per-ISO decisions; `elcc_accreditation`'s FFR-3V MISO caveat closed |
| `scripts/probes/ffr4b_read_arms.py` | the arm reader (reads `<out-dir>/MISO/<key>/`, never the out-dir root) |

**Drive-by, not part of this lane's mechanism:** `ercot_storage_rt_offer_surface`
was registered in `_CACHE_KEY_OPTIONAL_FIELDS` by ercot-162 (`48a158a6`)
without its `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` entry, leaving the HEAD-only
leg of `tests/unit/config/test_cache_key_default_flip_guard.py` **failing on
main for every session**. Verified pre-existing by stashing this lane's diff
and re-running at base. Added the one line the guard's own REMEDY prints; it
changes no cache key.

### 6.1 Cache-key consequence to expect

MISO forecast/hindcast runs that omit the flag now resolve to the **armed**
key (`27597e342ed68fd1` for this leg's configuration) instead of the unarmed
one. Existing cached MISO runs keep their keys and are not invalidated — but a
"re-run of the same command" on MISO will cold-solve rather than hit cache, and
that is correct: it is a different scenario.

### 6.2 Handed on

* **`run_scenario_iso` cannot distinguish "explicitly set to the default" from
  "unset"** (§4.4), so per-ISO default overrides swallow `--no-*` control arms.
  Pre-existing and shared by ERCOT/CAISO; this lane makes it bite on a field
  controls are actively built against. Fixing it touches all six ISOs and
  belongs to whoever owns the runner seam.
* **The growth ladder is now the binding constraint on MISO solar**, not its
  margin — so any further revenue-side work on MISO solar buys headroom, not
  megawatts, until the ladder question (FFR-4A) is settled.

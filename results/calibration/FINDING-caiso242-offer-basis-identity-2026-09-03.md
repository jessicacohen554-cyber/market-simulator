# FINDING — caiso-242: the CT_PEAKER residual is a PRICE defect, its diagnosis is a gas-basis identity error, the pre-registered falsifier KILLED the arm — and killing it exposed a live data defect worth 2.8 GW

**Session caiso-242, 2026-09-03. Branch `claude/caiso-ct-peaker-backcast-3ma46i`.**
Pre-registered in `PRECOMMIT-caiso242-offer-basis-identity-2026-09-03.md`
(`8be74e81`, pushed to `origin` **before the arm was designed, before its
footprint was measured and before any LP**).

**ZERO SOLVES. ZERO LP MINUTES SPENT.** Every number below is read from
committed artifacts or from `run_year(fleet_only=True)` fleet rebuilds of the
keeper's own recipe with **no flag delta**. Nothing armed, nothing registered,
no `ScenarioConfig` field added, **keeper unchanged**.

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read stayed inside **2023–2025**.

Keeper: **`2026-09-03-caiso-241-b1-ctpeaker`**, **NOT-YET**, C3a the sole
load-bearing FAIL — **unchanged, untouched**.

---

## §1 — HEADLINE

**The owner funded a solve. It was not spent, because the session's own
pre-registered falsifier fired first.** P-1 — written before `rho` was
computed, and specifying withdrawal rather than re-graining — failed at the
ISO-wide scope the owner selected. The arm was withdrawn. That is the
pre-registration working exactly as designed.

**Four results, in the order they were established:**

1. **THE CHARTERED QUESTION IS ANSWERED. Route (b) is FALSIFIED OUTRIGHT and
   route (a) binds.** CT_PEAKER availability **never binds in any hour of any
   year** — zero hours below 1 % headroom against a ~6 GW available envelope.
   The class is **priced out** in 80.7 / 89.5 / 90.7 % of hours.
2. **THE DIAGNOSIS: a gas-basis identity error.** Every armed CAISO band
   multiplier is, by the derive's own code, a ratio whose denominator is the
   **CA-composite citygate spot**; the solve evaluates it against the model's
   **delivered** series (EIA N3050CA3 + transport adder). Measured on the
   keeper, **every CAISO gas class's economic band is offered 10–49 % above the
   bid its own multiplier encodes** — CT_PEAKER's 2024 econ rungs at
   **$74.85/MWh** against a measured OASIS bid of **$58.66**.
3. **THE ARM IS WITHDRAWN. P-1 IS FALSIFIED.** The reconciliation ratio is
   admissible for CT_PEAKER (**0.7686 / 0.7761 / 0.7596**, dispersion **±0.0083**)
   and **inadmissible for CC_REGULAR** (**0.7294 / 0.6999 / 0.5533**, dispersion
   **±0.0881**, two of three years outside the registered `[0.72, 0.80]`).
   Withdrawn per §3.1, **not re-grained**, and **no LP spent**.
4. **AND THE FALSIFIER FOUND A REAL BUG — this is the session's most actionable
   result.** CC_REGULAR's 2025 outlier is not mechanism noise. **2,816 MW of
   CAISO gas (2,700 MW of it CC_REGULAR) is priced at $96.161/MMBtu — a marginal
   cost of $736/MWh — for all 720 hours of November 2025**, from a single
   EIA-923 row reporting a cost on **2 % of that plant's own normal monthly
   volume**. It reaches them because **`state` is empty on 100 % of CAISO's
   1,411 gas LP rows (29,319 MW)**, which silently disables the one fallback
   tier that carries a donor-count guard.

**The honest summary of the trade: the owner bought a solve and got a
withdrawal plus a bug. The bug is worth more.**

---

## §2 — THE CHARTERED OBJECT, RESOLVED ON MEASUREMENT

`scripts/probes/_caiso242_ctpeaker_anatomy.py` → `_caiso242_ctpeaker_anatomy.json`.

### §2.1 — ROUTE (b), AVAILABILITY: **FALSIFIED OUTRIGHT**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| class nameplate (MW) | 7,528.5 | 7,535.0 | 7,538.7 |
| available MW, mean | 6,306.5 | 6,315.5 | 6,341.6 |
| available MW, **p05** | 5,916.9 | 5,929.0 | 5,995.1 |
| dispatch (TWh) | 1.627 | 0.744 | 0.378 |
| **hours with < 1 % of nameplate headroom** | **0** | **0** | **0** |

Availability never binds. The class carries ≈ 6 GW available in 95 % of hours
and dispatches a mean of **186 / 85 / 43 MW**.

### §2.2 — ROUTE (a), PRICE: **BINDS**

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| hours cheapest **available** offer > price | **7,070** | **7,839** | **7,941** |
| share of year | 80.7 % | 89.5 % | 90.7 % |
| median gap ($/MWh) | +15.57 | +12.63 | +12.96 |
| cheapest offer / system price mean | 76.43 / 54.65 | 53.08 / 37.18 | 54.75 / 38.22 |

### §2.3 — THE CHARTER'S SUSPECTED INVERSION IS REAL, IS MANUFACTURED BY THE MARGIN MECHANISM, AND IS IMMATERIAL

Capacity-weighted assembled mc by band ($/MWh):

| band | MW | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|
| `committed` | 829.8 | 99.00 | 61.61 | 66.57 |
| `econc00…05` | 6,189.4 | 100.39 → 101.88 | 74.49 → 75.20 | 76.44 → 77.31 |
| `peak…peak5` | 623.5 | 109.92 | **71.92** | **76.59** |

In 2023 the curve rises correctly; in 2024 `peak` is the **cheapest** rung above
`committed`; in 2025 it sits between `econc00` and `econc01`. **The inversion is
not a property of the multipliers — `apply_gas_offer_margin` manufactures it,
and its sign is the sign of `anchor − fuel`:** econ carries `markup_hr` ≈ 4.99
MMBtu/MWh against peak's 1.805, so the adjustment moves econ 2.8× further —
down in 2023 (fuel 7.41 > anchor 4.796), up in 2024/2025.

**It is not the object.** It reorders 623.5 MW (8.3 %) against 6,189 MW, and in
≈ 90 % of hours **both** sides are above price, so the reordering cannot change
dispatch. The charter predicted the inversion from the raw multipliers; the
measurement locates its cause and sizes it out of contention.

### §2.4 — ROUTE (c) IS THE SAME DEFECT FROM THE OTHER SIDE

An offer surface pricing domestic CAISO gas ≈ 30 % above the market's own bids
makes imports win the evening ramp peakers should win. The keeper's
−8.4 / −7.6 / −5.6 TWh over-import and the −2.5 / −3.6 / −2.0 TWh CT_PEAKER
under-run are one defect with two signs. No import lever is proposed;
`IMPORT_TRANCHES[CAISO]` stays the standing unfunded object.

---

## §3 — THE DIAGNOSIS: A GAS-BASIS IDENTITY ERROR

`_caiso242_gas_basis_identity.json`, `_caiso242_passthrough_test.json`,
`_caiso242_roundtrip.json`.

### §3.1 — The two sides, from the two codebases' own lines

`derive_caiso_offer_surface.py`, static-band stage, **verbatim**:

```python
bids["gas"] = bids.day.map(gas)      # gas = _gas_staircase()  -> ca_composite_usd_mmbtu
bp["denom"] = base_hr * (bp.gas + CO2_FACTOR * bp.year.map(carbon))
bp["mult"]  = (bp.p - vom) / bp.denom
```

`data/fuel/hubs.py::apply_hub_basis_overlay` prices the same tranches at the
**EIA N3050CA3 monthly citygate + `CAISO_CITYGATE_TRANSPORT_ADDER` (0.46)**.
**A multiplier is dimensionless only with respect to its own denominator.**

### §3.2 — Measured

| | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| model delivered gas ($/MMBtu) | 7.4178 | 3.8416 | 4.5829 |
| derive denominator (CA-composite citygate) | 5.2831 | 2.4567 | 3.0593 |
| **difference** | **+2.1347** | **+1.3849** | **+1.5236** |
| ratio, carbon-inclusive | 1.298 | 1.310 | 1.327 |

**Model offer vs the measured bid the class's own multiplier encodes**, on the
econ rungs, capacity-weighted ($/MWh):

| class | 2023 | 2024 | 2025 |
|---|--:|--:|--:|
| CC_REGULAR | 70.91 vs 58.19 (**1.22×**) | 47.52 vs 37.18 (**1.28×**) | 57.71 vs 38.78 (**1.49×**) |
| CC_CHP | 70.31 vs 58.19 (1.21×) | 47.84 vs 37.18 (1.29×) | 48.40 vs 38.78 (1.25×) |
| **CT_PEAKER** | 101.13 vs 91.59 (1.10×) | **74.85 vs 58.66 (1.28×)** | **76.88 vs 61.16 (1.26×)** |
| CT_CHP | 102.06 vs 91.59 (1.11×) | 79.00 vs 58.66 (1.35×) | 78.95 vs 61.16 (1.29×) |
| ST_GAS | 172.42 vs 91.59 (1.88×) | 130.92 vs 58.66 (2.23×) | 133.63 vs 61.16 (2.19×) |

*(ST_GAS's 2.2× is **not** claimed as a finding: that class is the
`ST_GAS_PEAKER_PLANTS` bypass with its own base HR ~11.85 against the CT
bucket's 10.862, so the comparison carries caiso-230's known base-HR
misalignment. Reported for completeness, excluded from the claim.)*

### §3.3 — INDEPENDENT CORROBORATION, ALREADY COMMITTED, FOUND AFTER THE MEASUREMENT

`derive_caiso_offer_surface.py`'s own classifier reports, for the CT bucket, a
Theil–Sen slope of **9.2–10.4 MMBtu/MWh against the CA-composite citygate**
(0.85–0.96 × `base_hr` 10.862) with an implied non-fuel adder of **$9.6–12.7**.
**CAISO's CT bids track the CA-composite citygate at ≈ one base heat rate.**
The model prices them at `1.145 × base_hr × (composite × ≈1.5)`.

### §3.4 — A SECOND, INDEPENDENT MISMATCH IN THE SAME `denom` LINE

The derive states the identity it inverts against: *"a model tranche prices at
`mult × base_HR × gas + VOM + 0.057 × (mult × base_HR) × P_carbon`"*. **The
model does not do that.** It charges carbon at the fleet's **measured**
`emission_rate`, which for CT_PEAKER is **27 % below** `0.057 × tranche_HR`
(L2 = 0.727 / 0.727 / 0.723). So the derive's round-trip assumption is violated
on both legs of its own denominator — the gas index (L1 = 0.70 / 0.63 / 0.66)
and the carbon convention — **and they partly offset, which is very likely why
this survived caiso-51 → caiso-241 unnoticed.**

### §3.5 — THE FUEL-INVARIANT-MARGIN FORM IS FALSIFIED BY CAISO'S OWN OASIS RECORD

`caiso_offer_curve_measured.json::_provenance.per_year_band_mults` measures the
same multiplier in each year, across a 1.93× fuel swing:

| class · band | measured range | armed-implied range | ratio |
|---|--:|--:|--:|
| **CT_PEAKER `econ_low`** (1.145 / 1.158 / 1.147) | **0.013** | **0.2775** | **21.3×** |
| CT_PEAKER `econ_high` | 0.040 | 0.2756 | 6.9× |
| CT_PEAKER `peak` | 0.026 | 0.1004 | 3.9× |
| CC_REGULAR `econ_low` | 0.058 | 0.1391 | 2.4× |

**The measured multiplier is FLAT where the armed decomposition requires it to
swing by 0.28.** Full fuel passthrough with a near-zero fixed margin is what
CAISO's record shows; the armed form books **40 % of CT_PEAKER's econ offer as
fuel-invariant margin ($27.26/MWh at the anchor) on 82.1 % of the class's
capacity**. Recorded as a structural finding; **not armed, not proposed** — it
is a different object from §3.1–§3.2 and needs its own charter.

### §3.6 — WHAT THIS IS **NOT**

**It does not re-open caiso-229**, whose *"the marginal rung over-propagates
fuel"* hypothesis is REFUTED and stays refuted. caiso-229 measured a **coupling
slope** and found the model **UNDER**-coupled (Theil–Sen 2.18–4.34 vs a measured
6.7–7.4). This is a **denominator LEVEL** identity. A series shifted up relative
to another can simultaneously be less responsive to it — that is exactly what an
EIA monthly contract-weighted citygate plus a flat $0.46 tariff adder is against
a daily spot index. **Both hold; neither revives the other.**

**It does not re-open caiso-230**, which killed *raising un-grounded class bands
onto measured bucket values* on sign. This changes no band's grounding. And
caiso-230's own rule-14 caveat — *"the measured multiplier is defined against
its BUCKET base HR … so a naive transplant does not round-trip to the measured
bid level"* — is **the same failure mode diagnosed for the heat-rate leg of the
same denominator.** This session finds it in the gas-price leg, where it is
larger and affects the bands that were transplanted **correctly**.

---

## §4 — THE ARM IS WITHDRAWN. P-1 IS FALSIFIED. NO LP WAS SPENT.

### §4.1 — What was registered, before anything was computed

> **P-1** — `rho` lands in **[0.72, 0.80]** and its per-year dispersion is
> **≤ ±0.05**, so a single ISO scalar is admissible. *Falsified by any year
> outside, or dispersion > ±0.05 ⇒ **the arm is WITHDRAWN (§3.1), not
> re-grained**.*

### §4.2 — What was measured

Per-year `rho` = reconciled ÷ armed on `econ_low`:

| class | 2023 | 2024 | 2025 | dispersion | P-1 |
|---|--:|--:|--:|--:|---|
| **CT_PEAKER** | 0.7686 | 0.7761 | 0.7596 | **±0.0083** | **HOLDS** |
| **CC_REGULAR** | 0.7294 | **0.6999** | **0.5533** | **±0.0881** | **FAILS** |

**The owner selected the ISO-wide scope. At that scope P-1 is FALSIFIED on both
legs — range and dispersion — and the arm is withdrawn.**

### §4.3 — THE TEMPTATION, NAMED AND REFUSED

P-1 **holds** for CT_PEAKER alone — the scope the owner considered and did
**not** choose. Re-narrowing the scope *after* seeing which scope passes is
precisely the selection the pre-registration exists to prevent, and it is
**refused here**. Whether to re-put the narrow scope is an **owner decision for
a future session** (§8, ask 2), taken with this falsification on the record.

### §4.4 — AND THE WITHDRAWAL DOES NOT DEPEND ON THE §5 BUG

§5 shows CC_REGULAR's 2025 `rho` of 0.5533 is caused by a data defect; removing
it lifts 2025 to ≈ **0.7204** and the dispersion to **±0.0148**, inside the
registered bound. **But 2024's 0.6999 is outside `[0.72, 0.80]` on clean data
too**, so **P-1's range leg fails regardless and the withdrawal stands on its
own.** The two findings are independent, and it matters that they are: the bug
did not kill the arm, and the arm's death is not an argument about the bug.

---

## §5 — WHAT THE FALSIFIER FOUND: 2,816 MW OF CAISO GAS AT $736/MWh FOR A MONTH

### §5.1 — The observation

CAISO 2025 capacity-weighted delivered gas, by class, by month ($/MMBtu):

| class | Jan | … | Sep | Oct | **Nov** | Dec |
|---|--:|--|--:|--:|--:|--:|
| CC_REGULAR | 5.13 | … | 4.26 | 5.68 | **20.78** | 6.38 |
| CT_PEAKER | 5.13 | … | 4.45 | 4.64 | **6.08** | 6.38 |
| CC_CHP | 5.13 | … | 4.22 | 4.37 | **4.51** | 6.38 |

**In 2023 and 2024 every class carries the IDENTICAL series in all 12 months.**
The 2025 divergence begins in September — and the solve log says why:

```
hub-basis overlay (CAISO 2023, monthly): ... in 12/12 months
hub-basis overlay (CAISO 2024, monthly): ... in 12/12 months
hub-basis overlay (CAISO 2025, monthly): ... in  9/12 months
```

**The overlay covers 9 of 12 months in 2025.** In the three uncovered months the
F923 plant layer shows through — and it is carrying an artifact.

### §5.2 — The artifact, and the three compounding defects that deliver it

**D3 — the source row.** Plant **55077** (NV), EIA-923 Natural Gas:

| 2025 month | $/MMBtu | quantity |
|---|--:|--:|
| Jan–Oct | 2.373 – 11.304 | 115,774 – 674,308 |
| **Nov** | **96.161** | **5,234** |
| **Dec** | **67.900** | **7,808** |

**2 % and 3 % of that plant's own normal monthly volume.** A cost divided by a
near-zero volume is a fixed/reservation charge, **not a marginal delivered fuel
price**.

**D1 — `state` is EMPTY on 100 % of CAISO's gas fleet.** Measured: **1,411 of
1,411 gas LP rows, 29,319.3 of 29,319.3 MW**. `apply_plant_monthly_fuel_prices`
tries *"the plant's own state first (when at least
`nearby_fuel_price_min_state_plants` plants reported), otherwise the plant's
model zone."* With no state, **the state tier is skipped for the entire fleet**
— and that is the only tier carrying a donor-count guard (`min_state_plants = 2`,
resolved on this keeper).

**D2 — the zone tier has NO donor-count guard and NO volume guard.** Its pool for
these rows contains **exactly one** reporting plant — 55077 — and a
quantity-weighted mean over a pool of one returns that plant's price to five
decimals.

**The arithmetic that proves the path:** NV's ten reporting gas plants in
Nov-2025 have a quantity-weighted price of **$3.54**; CA's fifteen average
≈ $4.5. **Neither tier could produce $96.161 except from a pool of one.**

### §5.3 — The consequence, sized, and stated against interest

| | measured |
|---|--:|
| affected capacity | **2,816.3 MW** (67 LP rows, 7 plants) |
| of which CC_REGULAR | **2,700.1 MW** (55518 960.0, 55656 779.0, 55295 591.0, 55077 370.1) |
| CT_PEAKER / CT_CHP | 114.5 / 1.7 MW |
| **their mc, Nov 2025** | **$736.4/MWh** capacity-weighted |
| their mc, Oct 2025 | $102.7/MWh |
| step | **7.2×** |
| capability removed | up to **2.03 TWh** (2,816 MW × 720 h) |

**AGAINST INTEREST — the realized dispatch consequence is SMALLER than that
headline.** CAISO CC_REGULAR's 2025 monthly mean dispatch reads
Oct **4,476** → Nov **5,348** → Dec **5,106** MW: the class does **not** show a
November hole, because CAISO's other ~11 GW of CC absorbs the displacement.
**What is measured is capability removed and cost misallocated within the class
(plus displacement onto imports and peakers), not a class-level generation
collapse.** The full price and dispatch consequence is not established here and
would need a solve this session deliberately did not spend.

### §5.4 — Why no keeper caught it

2023 and 2024 have 12/12 overlay coverage, so the overlay overwrites the
fallback's output entirely and the defect is invisible. **It became reachable
only when 2025's overlay coverage fell to 9/12** — and 2025 is the training
window's worst C3a year (+15.5 %).

---

## §6 — THE CROSS-ISO CENSUS: THE PATHOLOGY IS NOT CAISO'S

`scripts/probes/_caiso242_f923_lowvolume_census.py` →
`_caiso242_f923_lowvolume_census.json`. Gas plant-months 2023–2025:
**15,385 rows, 466 plants**; price p50 **$3.41**, p99 **$26.97**, **max $198.46**.

Sweeping the cut (**none selected** — rule 5 `[R-NO-MAGIC]`; the repair's form is
an owner decision, §8 ask 3):

| qty ≤ (× plant-year median) | price ≥ (× plant-year VW) | rows | plants | median $ | max $ | **share of fleet gas volume** |
|---|---|--:|--:|--:|--:|--:|
| 0.02 | 2.0 | 43 | 33 | 27.59 | 198.46 | **0.0016 %** |
| 0.05 | 3.0 | 57 | 39 | 34.65 | 198.46 | 0.0044 % |
| 0.10 | 2.0 | 135 | 80 | 15.70 | 198.46 | 0.0255 % |
| 0.20 | 2.0 | 206 | 101 | 14.87 | 198.46 | 0.0507 % |

**That last column is the whole argument: these rows carry essentially none of
the fleet's gas, yet each one can set a plant-month's delivered marginal price —
and, through an unguarded fallback tier, other plants' too.** The worst rows span
**MN, CO, VA, MI, ND, MS, NC, AZ, NM** as well as CA/NV (226 rows over
$20/MMBtu: 93 / 53 / 80 by year), so **every ISO is exposed**. Under rule 25 the
*repair* is a source-data admissibility guard and therefore ISO-generic; any
*arm* stays its own lane's.

---

## §7 — PREDICTIONS, SCORED AGAINST INTEREST

| # | prediction | verdict |
|---|---|---|
| **P-1** | `rho` in [0.72, 0.80], dispersion ≤ ±0.05 | **FALSIFIED** at the ISO-wide scope (CC_REGULAR ±0.0881; 0.6999 and 0.5533 outside range). Holds for CT_PEAKER alone (±0.0083) — §4.3 refuses to use that. **Arm withdrawn.** |
| **P-2** | the arm does not close the CT_PEAKER gap either | **UNSCORABLE** — no solve. Registered, unspent; it must be re-registered by any future session that arms this. |
| **P-3** | G-STRUCT exact footprint | **UNSCORABLE** — the arm was withdrawn at §5.1 before its footprint was diffed. |
| **P-4** | the price move overshoots C3a in ≥ 1 year | **UNSCORABLE** — no solve. |
| **P-5** | C3a's 2023 verdict flips to a low-side FAIL | **UNSCORABLE** — no solve. |
| **P-6** | CT_PEAKER is still not the largest 2023 gas miss | **HOLDS on the keeper as it stands** (CC_REGULAR −3.079 vs CT_PEAKER −2.502); untouched by this session. |
| **P-7** | the DOF ledger does **not** move | **HOLDS trivially** — nothing was armed, so nothing could move it. Not claimed as a confirmation. |
| **P-8** | the arm is live in all three years | **UNSCORABLE** — no solve. |

**One scored prediction, and it is the one that killed the session's own arm.**
The four that would have flattered the arm (P-2, P-4, P-5, P-8) are unscorable
and are **not** quoted as anything.

---

## §8 — OWNER ASKS

1. **THE FUNDED SOLVE IS RETURNED UNSPENT.** The grant was given for an arm that
   its own falsifier withdrew. No LP was consumed; the grant is the owner's to
   re-issue, and this session does not presume it.
2. **RE-PUT THE NARROW SCOPE?** P-1 holds for CT_PEAKER alone (±0.0083, all three
   years in range). §4.3 refuses to take that scope on its own initiative. If the
   owner wants it re-put, it needs a **fresh precommit with a fresh falsifier** —
   the P-1 registered here is spent.
3. **THE F923 GUARD (§5, §6) — the repair's FORM is an owner decision, because
   every candidate contains a chosen number.** Three shapes, none selected here:
   (a) extend the existing `nearby_fuel_price_min_state_plants` guard to the
   **zone tier** (a guard that already exists, applied to a tier that lacks it —
   the smallest change, and it needs no new constant); (b) a **volume
   admissibility** guard on F923 rows (needs a threshold — a new parameter,
   rule 5); (c) **populate `state`** on the CAISO fleet so the guarded tier is
   reachable at all (a data-completeness repair, defect D1, no new parameter).
   **(a) and (c) together carry no free parameter and are this session's
   recommendation**, but neither is armed here.
4. **THE 2025 OVERLAY COVERAGE GAP** (9/12 months) is a separate data-intake ask:
   with 12/12 coverage the fallback would be unreachable in 2025 as it is in
   2023–2024. Not investigated further here.

---

## §9 — DO-NOT-REDO ADDS

1. **CT_PEAKER availability is CLOSED as a route.** Zero hours below 1 %
   headroom in any year, ~6 GW available in 95 % of hours. Never re-propose an
   availability explanation for the CT_PEAKER volume miss.
2. **The CT_PEAKER band-order inversion is MEASURED, EXPLAINED AND IMMATERIAL**
   (623.5 MW, both sides above price in ~90 % of hours). It is manufactured by
   `apply_gas_offer_margin` and its sign follows `anchor − fuel`. Do not
   re-propose it as a volume lever.
3. **P-1 of this precommit is SPENT.** Any future arm on the basis identity
   needs a new precommit and a new falsifier. Do **not** re-run this one at a
   narrower scope and read it as a pass.
4. **Never quote §H‴.** It was registered and never evaluated — the arm was
   withdrawn first. It is not evidence of anything.
5. **The measured-multiplier flatness (§3.5) is a SEPARATE object** from the
   basis identity (§3.1–§3.2). Do not merge them: one is a denominator, the
   other a functional form.
6. **Never treat the CAISO measured offer surface as round-tripping to the
   measured bid.** It does not, on either leg of its own `denom` line (§3.4).

---

## §10 — CARRIED, PROPOSE-ONLY, NOT STARTED

The CT_PEAKER root cause (**still open** — the diagnosis is established, the
repair is not); the F923 low-volume guard + the empty-`state` defect (§8 ask 3,
**cross-ISO, this session's strongest standing ask**); the 2025 overlay coverage
gap (§8 ask 4); the measured-multiplier flatness (§3.5); caiso-238 object 4
(`battery_dispatch_adder`, F2, materiality compounding 1.87 → 5.29 %); object 3
(own-curve shape derive); the SoCalGas OFO arm; the `IMPORT_TRANCHES[CAISO]`
LEVEL object; the DOF-provenance instrument ask (unchanged, unmoved — §0.5(2)).

**Deliverables:** `PRECOMMIT-caiso242-offer-basis-identity-2026-09-03.md`, this
finding, and four zero-LP probes with their artifacts —
`_caiso242_ctpeaker_anatomy`, `_caiso242_passthrough_test`,
`_caiso242_gas_basis_identity`, `_caiso242_roundtrip`,
`_caiso242_f923_lowvolume_census`. **No run registered (none produced), no
keeper change, no `ScenarioConfig` field added.**

**Next number: caiso-243.**

# FFR-3W — Decomposing CAISO's $40 k/MW-yr `gas_ct` entry-screen gap

**Lane:** DIAGNOSIS. No tuning, no promotion, no default flipped, no band widened.
**Date:** 2026-08-04. **Head:** `792d6fa3` (`origin/main`).
**CAISO keeper at this head:** `2026-08-04-caiso-166-measured-dlap` (read from
`frontend/data/backcast/keepers/CAISO.json`; the charter cited
`2026-08-04-caiso164-zonal-loss-surface`, which is that keeper's grandparent — the
re-verify-at-your-own-head instruction was exercised and the difference is immaterial to
this lane, which never touches the backcast leg).
**Solves run:** **none.** The charter says "bound it from committed artifacts first, and
only solve if the bound is not decisive." The bound is decisive in both directions (§5), so
this document is scored entirely from committed artifacts, `constants.py`, `data/raw/`, and
deterministic evaluation of the screen's own arithmetic. `scripts/regenerate_clean.py` was
started and then **killed** once the bound closed.

---

## 0. Headline — three findings, and the third is the one that matters

1. **The `unprofitable` VERDICT is a REAL market signal.** A new merchant CT in CAISO
   breaks even at a capacity price of **$10.88–11.36/kW-month**. CAISO's own published
   transacted RA price is **$11.10–14.51/kW-month**. The candidate sits essentially *on* its
   break-even line in a market that is **6.9 % long** on RA. "Do not build a merchant CT
   here" is the correct answer, and the screen is giving it.

2. **The $40 k MAGNITUDE is a screen defect, and it is ~100 % ONE TERM.** ≥94 % of the gap
   in every year is the **capacity-price anchor**. That anchor is the CAISO **CPM soft-offer
   cap**, whose own FERC provenance — carried verbatim in our `data/raw` — is
   *"$73.41/kW-yr **going-forward fixed cost** of a 550 MW **CC** reference unit × 1.20"*.
   It is a retention cost for an existing combined-cycle, used as the entry price for a new
   combustion turbine. Three independent basis mismatches, none of which is a residual
   argument (§2.3). Energy, AS and the cost stack are collectively ≤ 27 % of the gap in the
   best year and ≤ 0.1 % in the worst.

3. **FC-2 row 4's failure is NOT caused by the `gas_ct` screen — and "fixing" the screen
   would turn row 4 green for the wrong reason.** The backstop exists because the model's
   base-year CAISO fleet is **11,711 MW of accredited capacity short of the real CAISO**
   (FFR-3P Table 1.1), which is **1.78×** the 6,577 MW deficit that drives the entire
   14,043.6 MW build. Correcting the fleet alone moves the reserve position 0.8852 → 1.0896
   (11.5 % short → 9.0 % long), eliminating the need and collapsing row 4's numerator.
   Correcting the `gas_ct` term instead would move row 4 **just as far** (§5.2) — by building
   *the same 14 GW of CTs California does not need* through the economic channel rather than
   the administrative one. **Row 4 would read PASS while the model still over-builds 14 GW
   of firm capacity into a market that is already long.** That is a rule 1 `[R-STRUCT]` trap
   — the right number through a mechanism that isn't real — and it is the single most
   decision-relevant sentence in this document.

**Therefore: do not charter the capacity-anchor correction as a row-4 fix.** If it is
chartered at all it must be on its own rule-14 merits, and row 4 must be chartered against
the fleet-vintage cause (FFR-3P **B-1**).

---

## 1. The decomposition

Revenue side reproduced from FFR-3H §2.1 arm B (`--golden-posture --entry-screen-diagnostics`,
resolved key `0a41c0d0bd87eec2`). Cost side computed here from
`NEW_ENTRY_COSTS["gas_ct"]` + `_capital_recovery_factor`, which FFR-3H reported only as a
$128,112 total. The `results/ffr3h/` bundles were **not committed**, so the ledger rows are
carried from FFR-3H's tables and the cost stack is re-derived deterministically.

### 1.1 Cost stack — $128,111.6/MW-yr, identical in all four years and all six ISOs

| term | $/MW-yr | share | source |
|---|--:|--:|---|
| capex annuity — **return OF capital** | 47,623.3 | 37.2 % | $1,428.7/kW ÷ 30 yr |
| capex annuity — **return ON capital (financing)** | 52,588.3 | 41.0 % | CRF 0.070142 − 1/30, at `real_discount_rate` 0.056751 |
| **capex annuity, total** | **100,211.6** | **78.2 %** | $1,428.7/kW × CRF |
| **FOM** | **27,900.0** | **21.8 %** | ATB 2024 Moderate NG CT (F-Frame) @2026 |
| **TOTAL** | **128,111.6** | 100 % | |

Notes that matter:
* **No Wright learning.** `WRIGHT_REFERENCE_GW["gas_ct"]` is absent, so capex is flat across
  the horizon. The cost stack is **year-invariant** — every year's gap widening comes from
  the revenue side.
* **No per-tech WACC.** `per_tech_wacc_enabled` is False, so the single 5.675 % real rate
  governs. `ATB_TECH_WACC_REAL["gas_ct"]` is 5.3585 %, i.e. arming it would *lower* the
  hurdle by ~$4.0 k/MW-yr — but it is gated OFF pending FF-2D for an unrelated
  double-counting reason, and it is not this lane's to move.
* **The hurdle is well-anchored nationally and carries no California premium.**
  $1,428.7/kW sits inside the committed benchmark spread (`benchmarks_2026.csv`: AEO2026
  $1,158; Lazard 2025 $1,150–1,450; Brattle/S&L 2025 for PJM $1,339–1,495). There is **no
  CAISO-specific CT capex anywhere in the model** — CA labor, siting, permitting, SCR and
  emission-offset costs are all absent. **Correcting the cost side toward CAISO reality
  widens the gap, it does not close it.** Stated explicitly so no successor mistakes the
  cost stack for the defect.

### 1.2 Revenue side, per year (FFR-3H arm B; identical across arms A–D in the capacity term)

| year | energy(+reserve) | capacity | AS | revenue | cost | **margin** |
|---|--:|--:|--:|--:|--:|--:|
| 2027 | 5,343 | 82,795 | 0 | 88,138 | 128,112 | **−39,974** |
| 2028 | 4,305 | 82,795 | 0 | 87,100 | 128,112 | **−41,011** |
| 2029 | 2,081 | 82,795 | 0 | 84,876 | 128,112 | **−43,235** |
| 2030 | 27 | 82,795 | 0 | 82,823 | 128,112 | **−45,289** |

Capacity is **93.9 %** of revenue in 2027 and **100.0 %** by 2030. The capacity term is
`88.08 $/kW-yr × 1000 × 0.94` = $82,795.2, verified here to reproduce **invariantly at
reserve positions 0.84 / 0.90 / 0.95 / 1.00 / 1.10** — FFR-3H §2.2's invariance, reproduced
independently.

---

## 2. Which term is the gap? (the charter's "90 % one term" test)

### 2.1 Break-even capacity price — the cleanest statement of the gap

Holding energy and cost fixed, the capacity price that clears the candidate:

| year | energy $/MW-yr | break-even capacity $/kW-yr | $/kW-**month** |
|---|--:|--:|--:|
| 2027 | 5,343 | 130.60 | **10.88** |
| 2028 | 4,305 | 131.71 | **10.98** |
| 2029 | 2,081 | 134.08 | **11.17** |
| 2030 | 27 | 136.26 | **11.36** |

### 2.2 Against every capacity price CAISO actually publishes

All rows below are already committed at
`data/raw/capacity-market/demand-curve/caiso/caiso.csv` — nothing is fetched or derived here.

| published quantity | $/kW-mo | $/kW-yr | ⇒ revenue @0.94 |
|---|--:|--:|--:|
| CPM soft-offer cap 2023 | 6.31 | 75.72 | 71,177 |
| **CPM soft-offer cap 2024/25 — THE MODEL'S ANCHOR** | **7.34** | **88.08** | **82,795** |
| CPUC **System RA** 2023 | 11.10 | 133.20 | 125,208 |
| CPUC **System RA** 2024 | 14.51 | 174.12 | 163,673 |
| CPUC **System RA** 2025 | 11.87 | 142.44 | 133,894 |
| CPUC All-RA 2023 | 11.34 | 136.08 | 127,915 |
| CPUC Local RA 2023 | 11.21 | 134.52 | 126,449 |
| CPUC System incl. imports 2023 | 14.33 | 171.96 | 161,642 |

**The break-even band (10.88–11.36) sits inside the transacted band (11.10–14.51), and above
every CPM cap.** Moving the anchor alone closes the gap by:

| anchor | Δ $/MW-yr | 2027 | 2028 | 2029 | 2030 |
|---|--:|--:|--:|--:|--:|
| CPUC System RA 2023 | +42,413 | 106 % | 103 % | 98 % | **94 %** |
| CPUC System RA 2025 | +51,098 | 128 % | 125 % | 118 % | 113 % |
| CPUC System RA 2024 | +80,878 | 202 % | 197 % | 187 % | 179 % |
| 3-yr mean (12.49 $/kW-mo) | +58,130 | 145 % | 142 % | 134 % | **128 %** |

Against this, the **energy term tripled** — a correction far larger than any defect I can
identify in it — closes **26.7 % / 21.0 % / 9.6 % / 0.1 %**. The cost side's only
CAISO-specific correction is directionally adverse.

**Verdict on the charter's test: the gap is ≥94 % ONE TERM. It is the capacity price.**

### 2.3 Why the anchor is the wrong *kind* of object — three mismatches, none residual-based

The provenance is quoted in our own committed source row (FERC ER24-1225 letter order,
187 FERC ¶ 61,032, effective 2024-06-01), recorded at
`data/raw/capacity-market/demand-curve/caiso/caiso.csv`:

> *"$73.41/kW-yr **going-forward fixed cost** of 550 MW **CC** reference unit × 1.20 =
> $88.09/kW-yr = $7.34/kW-month"*

| # | mismatch | why it is a category error for this screen |
|---|---|---|
| **a** | **Going-forward cost, not entry cost** | A going-forward fixed cost is FOM + minimal sustaining capital for an **existing** unit. It contains **no capex annuity**. The screen compares it against a **new-entry gross fixed cost** that is 78.2 % capex annuity. The model's own going-forward analogue for a new CT is its FOM, $27.9/kW-yr. |
| **b** | **CC reference unit, not CT** | The cap is derived from a 550 MW combined-cycle. The candidate is a frame CT. Different capex/kW, different FOM/kW, different duty cycle. |
| **c** | **An administrative price CAP, not a market price** | It is a ceiling on what a CPM-designated resource may *offer* into CAISO's backstop procurement. A ceiling on backstop offers is not the price a new entrant is paid for RA. |

Each of these is established from the source document's own words and is **independent of
the $40 k residual** — which is what makes this a rule 14 `[R-ACCURATE]` finding rather than
a rule 1 `[R-STRUCT]` violation. FFR-3H §3.4 already observed (c); this document adds (a)
and (b) and the quantification, and **reaches the opposite conclusion from FFR-3H's "a level
re-anchor would not fix this"** — correctly, because FFR-3H's question was the *invariance*
(what makes the backstop necessary) while this lane's question is the *level* (what makes
the candidate unprofitable). Both are true; they are answers to different questions.

**This is NOT a recommendation to swap the anchor.** The obvious replacement has its own
rule-14 misalignment and is not a drop-in — see §4.

---

## 3. The reserve/AS term — "AS = 0" is a STRUCTURAL zero, not a reporting artifact

The charter asks which pricing path fired. Traced end-to-end and confirmed by direct
evaluation of the shipped `--golden-posture` CAISO forecast config:

| gate | value | consequence |
|---|---|---|
| `screen_reserve_value_enabled` | **True** (default) | the runner *tries* to supply an hourly reserve signal |
| `runner.py:2515-2543` ERCOT branch | requires `iso == "ERCOT"` | **cannot fire for CAISO** |
| `overlay_adder` (CAISO scarcity overlay) | **None** — `scarcity_pricing_enabled=False` and `caiso_scarcity_pricing=False`; `--golden-posture` sets neither | ⇒ `reserve_price_signal = None` |
| ⇒ `r_tech` in the screen | **None** | the hourly `max(energy, reserve)` leg **never applies** |
| `ercot_thermal_as_endogenous` | False | ⇒ `thermal_as_revenue_per_mw_yr = None` |
| ⇒ falls to `as_revenue_per_mw_yr` | `as_revenue_enabled=False` | returns **0.0** |
| …and even if armed | `AS_REVENUE_PER_KW_YR_BY_ISO` = **`['ERCOT']` only** | still **0.0** |

**Path 3 fired, and it returns zero through two independent gates.** Consequences:

* The $5,343 → $27 "energy" column is **pure energy margin**. The hourly best-use max was
  never applied, so — unlike the ERCOT case the code comment describes — **AS is not hiding
  inside the energy term here.** A CAISO `gas_ct` earns **literally no ancillary-service
  revenue** in the entry screen.
* This is a genuine under-credit: CAISO runs a real AS market (Reg Up/Down, Spin, Non-Spin)
  and a quick-start CT is a prime Non-Spin provider. `gas_ct` is in both
  `RESERVE_FUEL_TYPES` and `QUICK_START_FUEL_TYPES`, so the model *classifies* it as
  reserve-capable and then pays it nothing.
* **It is not quantifiable from committed artifacts** — there is no CAISO AS price anywhere
  in `data/raw/` (searched; only ERCOT carries a rate). Filed as **W-2** (§6) and listed in
  §7 as not separated.

Rule 19 `[R-ONE-MECH]` reconciliation, as the charter requires before proposing anything:
the three channels that could price this unit's reserve value are mutually exclusive by
construction in the code (hourly max ⇒ suppresses both annual credits; else the ERCOT
co-opt rate; else the flat exogenous rate). For CAISO **all three resolve to zero**. There
is nothing to stack on and nothing to replace — the slot is empty.

---

## 4. Capacity value — does the RA-saturation half zero it?

The charter asks explicitly. **No.**

* `_make_new_generator` resolves the thermal build zone via `_default_build_zone(iso_config)`
  → **NP15**, then `build_zone_long = _zone_is_long(deliverability_headroom, zone)`. When
  `build_zone_long` is True the capacity payment is set to **exactly 0.0** — so the
  RA-saturation half *can* zero this term.
* It did not. `capacity_deliverability_limits` resolves **False** in the shipped forecast
  posture (verified here by direct config read; FFR-3H §3.3 verified the same). With the
  flag off, `deliverability_headroom_by_zone` returns `{}` and `_zone_is_long` is
  short-circuit False. The $82,795 was never touched.
* **Which half:** the unvalidated **RA-saturation** half is the one that would apply here,
  and it is **inert in the forecast leg**. The measured-seam-import half (MIC → WECC_import)
  that the *backcast keeper* arms is a different code path and is not in this measurement at
  all. Backcast and forecast postures differ on this flag; a successor must not read the
  keeper's posture as describing the forecast leg.

**Does CAISO's RA payment reach this unit?** Yes — CAISO carries `capacity_market=True`, so
the payment is credited. It reaches it at the wrong price (§2.3), not at zero.

**The replacement is not a drop-in.** Under rule 14's own misalignment exception, the
CPUC System RA transacted price has two documented mismatches of its own:
1. It is a **whole-market weighted average dominated by existing resources**, whose
   going-forward costs are far below new-entry cost. A price that clears mostly-existing
   supply is not automatically the price a new entrant is paid — and the fact that
   California procures new firm capacity through **CPUC central-procurement orders** rather
   than through the RA price is itself evidence that the RA price does **not** call forth new
   entry.
2. It is priced per kW-month of **NQC**, whereas the screen applies a `1 − EFORd` = 0.94
   **UCAP** accreditation. Pairing an NQC-basis price with a UCAP-basis accreditation is
   exactly the basis-pairing error the accreditation-basis memo exists to prevent.

So the honest statement is: **the current object is provably wrong; the right object requires
a reconciled intake with its own citation and its own owner box.** A diagnosis lane may not
supply it. Filed as **W-1**.

---

## 5. Does FC-2 row 4 move? — bounded from committed artifacts, no solve

Row 4 (`docs/forecast-determination-rubric.md` §FC-2.4): cumulative `reserve_backstop`
thermal additions ÷ total additions (thermal + renewable + storage MW). **≤10 % PASS;
10–30 % CAVEAT; >30 % FAIL.**

Committed measurements (FFR-3P §AB table, control arm reproducing FFR-3H arm A at key
`e5822277b72184f6`):

| arm | Σ backstop MW | Σ additions MW | row 4 |
|---|--:|--:|--:|
| control (shipped) | 14,043.6 | 21,448.0 | **65.48 % FAIL** |
| `--caiso-nqc-accreditation` (FFR-3P) | 12,731.6 | 20,136.0 | **63.23 % FAIL** |

### 5.1 Why FFR-3P barely moved it — and why this case is different

FFR-3P removed **1,312 MW from the numerator and 1,312 MW from the denominator** (the
arithmetic is exact: 14,043.6−12,731.6 = 21,448.0−20,136.0 = 1,312). It reduced *need*, so
the MW vanished from both sides; at a ratio of 0.65 that barely moves the quotient. **That
is why a −1,312 MW result bought only −2.25 pp**, and it is the reason FFR-3P's outcome must
not be read as "row 4 is insensitive."

A `gas_ct` correction is a **channel substitution**, not a need reduction: the same physical
CT MW get built, through the economic screen instead of the backstop. The numerator falls;
**the denominator does not.** That is a far more leveraged move, and it is guaranteed by two
independent structural facts in the code:

* **The backstop is a strict residual channel.** Step 5 (economic entry) runs before step 6
  (backstop), and the backstop sizes itself off `accredited_firm_capacity_mw` *after* step 5
  has already added its units. Any MW economic entry builds is a MW the backstop does not
  need.
* **They share ONE growth-ladder budget.** `evolve.py:707-721`:
  `_gas_ct_rate_budget = max(0, entry_rate_caps_mw["gas_ct"] − _decided_mw_by_tech["gas_ct"])`
  is passed as the backstop's `rate_limit_mw`. In the rate-limited years (2027–29, per
  FFR-3H) economic `gas_ct` decisions are subtracted from the backstop's own allowance —
  "one physical queue (rule 19)". So in **both** regimes — need-limited and rate-limited —
  the substitution is ~1:1 in the numerator with the denominator held.

### 5.2 The bound

With the denominator held at 21,448.0 MW and `f` = the fraction of the 14,043.6 MW the
economic channel captures:

> **row 4 (f) = 0.6548 × (1 − f)**

| target | required `f` | economic MW required |
|---|--:|--:|
| **CAVEAT** (≤30 %) | **0.542** | 7,609 of 14,044 |
| **PASS** (≤10 %) | **0.847** | 11,899 of 14,044 |

**Does `f` get there?** If the candidate flips profitable, the economic screen decides first
and takes the whole shared ladder in 2027–29, leaving the backstop ~0 there; 2030 is
need-limited and would likewise be met economically. So `f → ~1` and **row 4 → ~0 %, PASS** —
*provided the candidate stays profitable as it builds*. It may not, because of FFR-3H §2.3's
ratchet: energy margin collapses 5,343 → 27 as CTs enter, so break-even rises to
$11.36/kW-month by 2030. At the **2024 ($14.51)** or **2025 ($11.87)** transacted price the
candidate clears at zero energy margin and `f ≈ 1` (PASS). At the **2023 ($11.10)** price it
clears in 2027–28 and stops in 2029–30, giving a partial `f` and landing between CAVEAT and
FAIL. That self-limiting behaviour is structurally *healthy* — it is what a working entry
equilibrium looks like — and it is the reason the landing cell cannot be pinned without a
chartered arm.

**Answer to the charter's question: YES, row 4 moves — materially, and plausibly all the way
to PASS.** The bound is decisive on *whether it moves* and on *the mechanism*; it is
deliberately not decisive on the exact landing cell, which depends on an anchor this lane may
not choose.

### 5.3 …and that is exactly why it must not be chartered as the row-4 fix

The competing cause closes row 4 **completely**, and it is the one that corresponds to
reality. From FFR-3P Table 1.1 (CAISO CY2026 Table 1.1 vs the model's base-year ledger):

```
base-year deficit driving the whole backstop : 57,306 − 50,729 =  6,577 MW
model-vs-real accredited fleet gap           :                  11,711 MW   = 1.78x the deficit
model  reserve position : 50,729 / 57,306 = 0.8852   (11.5 % SHORT)
real   reserve position : 59,069 / 55,276 = 1.0686   ( 6.9 % LONG)
corrected              : 62,440 / 57,306 = 1.0896   ( 9.0 % LONG)
```

The gap is **nameplate/fleet-vintage**, dominated by battery (−5,933), solar (−2,543),
hybrid (−1,484) and hydro (−1,670) MW the model's base fleet does not carry. **It is not an
accreditation-ratio claim:** FFR-3P's two retractions concerned the thermal (0.9457 vs
published 0.9537) and hydro (0.7041 vs published 0.6936) *class factors*, where the model is
already 0.8 % above and 1.1 pp generous respectively. Those retractions stand and are **not
reinstated here** — nothing in this document depends on either.

Because the fleet gap is 1.78× the deficit, **correcting the fleet eliminates the adequacy
need entirely**: position 0.8852 → 1.0896, requirement met, backstop → ~0, row 4 numerator →
~0, **PASS**. And it does so without building a single unnecessary CT.

The contrast is the finding:

| route | row 4 | 14 GW of CTs California doesn't need |
|---|---|---|
| correct the `gas_ct` capacity anchor | FAIL → ~PASS | **still built**, via the economic channel |
| correct the base-year fleet vintage (FFR-3P **B-1**) | FAIL → PASS | **not built at all** |

Both turn the gate green. Only one is the real market. **A session that fixes the anchor and
reports row 4 PASS will have moved the rubric without moving the model closer to CAISO** —
rule 1 `[R-STRUCT]`, stated before anyone measures it rather than after.

---

## 6. Open items — for the owner to charter or decline (nothing proposed as done)

| id | item | why it is not this lane's |
|---|---|---|
| **W-1** | The CAISO capacity anchor is the CPM soft-offer cap — an existing-**CC** going-forward cost used as a new-**CT** entry price (§2.3). The replacement needs a **reconciled** intake (NQC-vs-UCAP basis pairing; existing-weighted average vs new-entrant price), not a substitution. | Rule 14's misalignment exception requires a documented reconciliation and a citation; rule 24 requires it land in the registry. Diagnosis charter forbids both. **Must not be chartered as a row-4 fix** (§5.3). |
| **W-2** | A CAISO `gas_ct` earns **zero** AS revenue through all three mutually-exclusive channels (§3), in an ISO with a real Non-Spin market a quick-start CT is built to serve. | No CAISO AS price exists in `data/raw/` — this is a data intake with its own authorization, and the magnitude is unbounded from here. |
| **W-3** | **The thermal energy-margin term averages prices ACROSS ZONES** (`new_entry.py:860`, `prices.mean(axis=0)`) while the VRE path indexes the build zone (`prices_arr[zi]`). Since `max(·,0)` is convex, cross-zone averaging **systematically understates** a peaker's price-duration margin — the scarcity tail is averaged away before the max is taken. The thermal candidate is built at NP15 but priced on the ISO mean. | Direction is provable from Jensen; **magnitude is not bounded from committed artifacts** (needs per-zone forecast prices, which the uncommitted `results/ffr3h/` bundles would have carried). Bounded above by ≤27 % of the gap only because the whole term is small. |
| **W-4** | No **CAISO-specific** new-entry cost anywhere in the model — CA labor/siting/permitting/SCR/offsets absent; the $128,112 hurdle is the same national ATB number in all six ISOs. | Directionally **adverse** to the gap, so it is a completeness note, not a fix. Flagged so no successor "corrects" the cost side expecting the gap to close. |
| **W-5** | `results/ffr3h/` was never committed, so FFR-3H's per-candidate ledger rows had to be carried from its prose tables rather than re-read. | Process note. A decomposition sink whose output isn't committed cannot be re-decomposed by a successor — which is precisely what this lane hit. |

---

## 7. What this document did NOT separate (stated plainly)

* **The AS term's true magnitude.** Established as a structural zero through two gates
  (§3); *not* established what it should be. No CAISO AS price data exists in the repo.
* **The zone-averaging defect's magnitude (W-3).** Direction proven, size not measured. It is
  inside the $5,343 → $27 energy column, so it is bounded above by that column's size — but
  its share of that column is unknown.
* **Energy vs reserve within the "energy" column.** Moot here (the max leg never applied, so
  the column is 100 % energy), but only *because* the overlay is off. Under a posture that
  arms `caiso_scarcity_pricing` the two would be inseparable in the ledger as written.
* **The exact FC-2 row-4 landing cell** under a corrected anchor (CAVEAT vs PASS). Bounded
  to a formula and a threshold (§5.2); the landing depends on which anchor, which is W-1's
  owner box and not this lane's to pick.
* **Whether the 11,711 MW fleet gap is fully closable.** FFR-3P filed the storage half as
  **B-1**; the solar/hybrid/hydro halves are not separately adjudicated anywhere I found.
  §5.3's "PASS" for that route assumes the gap closes; it is 1.78× the deficit, so it has
  substantial margin, but partial closure gives partial relief.
* **Any MISO comparison.** Rule 25 `[R-ISO-SCOPE]`: FFR-3V was **not read, not cited, and no
  parameter imported**. Every number here is CAISO's own.

---

## 8. Governance

* **Rule 1 `[R-STRUCT]` / rule 11:** no adder, haircut, offset or value tuned to the 63.23 %
  residual appears anywhere. §5.3 exists specifically to stop the residual-closing move.
* **Rule 13 `[R-MEASURED]`:** every published number is quoted from a committed
  `data/raw/` row with its source document; nothing is fitted.
* **Rule 14 `[R-ACCURATE]`:** the anchor finding is grounded in the FERC order's own words,
  not in the fit. The replacement is explicitly held back for reconciliation rather than
  swapped in — §4.
* **Rule 19 `[R-ONE-MECH]`:** what already prices this unit's capacity and reserve value is
  enumerated before anything is proposed (§3 reserve — all three channels zero, nothing to
  stack on; §4 capacity — one seam, `capacity_price_per_firm_mw_yr`).
* **Rule 22 `[R-HOLDOUT]`:** **no year was solved at all.** Nothing out-of-training was
  touched, read, or scored. CAISO holds no `complete` marker and the spend freeze is ACTIVE;
  both are respected trivially by running no solve.
* **Rule 25 `[R-ISO-SCOPE]`:** see §7.
* **Rule 28 `[R-MECH-MATRIX]`:** **no matrix cell is stamped, because no mechanism was
  tested.** This session ran no solve, armed no flag and moved no default; duty (b) fires on
  the session that *tests* a mechanism. The CAISO lever queue (§5.2 of
  `docs/mechanism-testing-matrix.md`) was consulted and is backcast-scoped, so this
  forecast-lane finding is off-queue by construction and is filed as W-1/W-2 for chartering
  rather than entered as a cell.
* **Rule 15 / 16:** no run was produced, so there is nothing to register on either
  dashboard.

## 9. Reproduction

No solve. Every number is reproducible from this head with the environment only:

```bash
uv sync    # regenerate_clean.py is NOT needed — no solve is run

# cost stack, capacity term, and the invariance
uv run python -c "
from market_sim.config.scenarios import ScenarioConfig, resolve_real_discount_rate
from market_sim.config.constants import NEW_ENTRY_COSTS, EFORD
from market_sim.model.capacity_evolution.new_entry import _capital_recovery_factor
from market_sim.model.capacity_evolution.retirements import capacity_revenue_per_mw_yr
c = ScenarioConfig(iso='CAISO', mode='forecast'); ct = NEW_ENTRY_COSTS['gas_ct']
crf = _capital_recovery_factor(resolve_real_discount_rate(c,'gas_ct'), ct['lifetime_yr'])
print('fixed cost \$/MW-yr', (ct['capex_per_kw']*crf + ct['fom_per_kw_yr'])*1000)
for rp in (0.84,0.95,1.10):
    print(rp, capacity_revenue_per_mw_yr('CAISO','gas_ct',EFORD['gas_ct'],c,rp,2027))
"

# the AS path (all three channels -> 0)
uv run python -c "
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.constants import AS_REVENUE_PER_KW_YR_BY_ISO
c = ScenarioConfig(iso='CAISO', mode='forecast')
print(list(AS_REVENUE_PER_KW_YR_BY_ISO), c.as_revenue_enabled,
      c.scarcity_pricing_enabled, c.caiso_scarcity_pricing, c.ercot_thermal_as_endogenous)
"

# published capacity prices (committed, no fetch)
cat data/raw/capacity-market/demand-curve/caiso/caiso.csv
```

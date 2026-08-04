# FFR-4A — The entry growth ladder's `K = L` knife-edge: intent, map, derivation

**Lane:** derivation (owner decision D-14, sitting Addendum O, signed 2026-08-04).
**Charter:** the `K = L` knife-edge found by FFR-3V §5 is chartered as a DEFECT.
Derive, from the measured build record, the intended relationship between the
ladder multiplier `K` (`ENTRY_GROWTH_LIMIT_MULTIPLE`) and the COD lag `L`
(`ENTRY_COD_LAG_YEARS`).
**Head at start:** `origin/main` `5eac75b0`.
**Scope discipline:** no keeper promotion, no forecast-run registration, no tuning.
**Status of §1–§3:** written and committed BEFORE any counterfactual was run
(§4 is the pre-registered prediction; §5 the measurement).

---

## 0. Headline

The knife-edge is **not** a mis-set value of `K`. It is a **dimensional
double-count**: a *stock* (pending pipeline MW) is subtracted from two *flow*
caps (GW **per year**), both of which are annual-rate quantities by their own
citations. The general consequence, derived in §3.3 and validated against an
already-registered run, is:

> Netting a pipeline stock from an annual-flow cap `C` under a COD lag of `L`
> years caps the long-run **average** decision rate at `C / L`, not `C`.
> Where the cap is the *endogenous* ladder `K × prior_max`, the same netting
> additionally destroys the ratchet whenever `K ≤ L` — at `K = L` exactly, the
> growth factor is `K − L + 1 = 1` and the ladder can never rise.

`K` is **not** moved and `L` is **not** moved. Both survive the derivation with
their published citations intact — and `K = 2.0` is independently corroborated
below against the measured EIA-860 ratio distribution (p90 = 2.20–2.37). The
defect is a **third, uncited term** that neither citation authorises.

**Recommendation (rule 19 `[R-ONE-MECH]`):** the two guards are redundant on the
same object. Remove the pending-stock netting from the flow caps; relocate the
anti-cobweb guard to where its phenomenon actually lives (the entry screen's
price signal, §3.4) — that relocation is **escalated, not landed here**.

---

## 1. What the ladder is supposed to express (intent reconstruction)

### 1.1 The two guards have different origins, different citations, different objects

Repo history is squash-merged (`entry_config.py` carries a single merge commit),
so the intent record is the FF-2A completion handoff
(`docs/handoffs/ff-entry-stack-completion-2026-07.md`), which itemises the FF-2A
gates one row per gate. Two separate rows:

| gate | row | what it bounds | citation |
|---|---|---|---|
| `entry_rate_limits` (the ladder) | §"gates" line 38 | annual builds ≤ `ENTRY_GROWTH_LIMIT_MULTIPLE (2.0) × prior-max annual build`, seeded from EIA-860, **rising endogenously as the model builds** | NREL ReEDS 2025 growth-constraints section — "growth rates are not allowed to exceed 200 % of the prior maximum" annual **installation** rate |
| `entry_commissioning_lag` (the lag + netting) | §"gates" line 39 | decide in Y, commission Y+2; "pending (decided-not-online) MW are netted against **the per-tech caps** in later decision years — the developer's view of the queue, the structural anti-cobweb once decision and COD separate" | LBNL *Queued Up* 2024 (median IA→COD ≈ 25 months) for the **lag**; the **netting** carries no external citation in any row |

Three things follow, and they are the finding of this section.

**(a) The netting is not part of the ladder's intent.** The ladder row (line 38)
describes the cap and its endogenous rise and says nothing about netting. The
netting appears only in the *lag* row, as a property of the lag gate.

**(b) The documented netting target is the per-tech cap; the code nets both.**
Line 39 says "netted against the **per-tech caps**" — the language for
`QUEUE_CAP_PER_TECH_GW`. The shipped code
(`new_entry.py:1131–1148`) nets `_pending_by_tech` from **both** the per-tech
queue cap (`group_remaining`) **and** the ladder (`_ladder_remaining`), and its
own comment says so: *"netted from this decision year's per-tech / ladder
budgets."* **The ladder half of the netting is an implementation extension
beyond the documented intent, and it is the half that creates the knife-edge.**

**(c) The two guards prevent different things.** The ladder prevents
*physically undeliverable build rates* (supply chain / interconnection
throughput). The netting prevents *the same opportunity being re-decided every
year of the lag* — a developer-information problem, explicitly named
"pipeline-stuffing cobweb" in the code comment. These are different phenomena,
and stacking the second onto the first is precisely what rule 19
`[R-ONE-MECH]` forbids.

### 1.2 Both caps the netting touches are FLOWS, by their own citations

* `ENTRY_GROWTH_LIMIT_MULTIPLE` bounds "annual installation rate" (ReEDS) —
  GW **per year**.
* `QUEUE_CAP_PER_TECH_GW` is documented in `config/capacity_market.py:2879`
  verbatim as *"Per-technology **annual** interconnection queue caps
  (GW/yr) by ISO"* — GW **per year**.

`_pending_by_tech` is the **stock** of MW sitting in the pipeline (a sum over
`(L−1)` decision cohorts), in MW, with no time denominator. Subtracting it from
either cap is a units error, and the pathologies in §3.3 are its signature.

### 1.3 The asymmetry FFR-3V observed, located in code

FFR-2B measured MISO's gas_ct ladder *doubling* (1,350 → 2,700 → 5,241 MW)
while economic entry froze. The mechanism is one line:

* **Economic screen** (`new_entry.py:1141–1147`):
  `_ladder_remaining = max(0, entry_rate_caps_mw[tech] − pending_by_tech[tech])`
  — netted.
* **Reserve-margin backstop** (`evolve.py:708–713`):
  `_gas_ct_rate_budget = entry_rate_caps_mw["gas_ct"] − _decided_mw_by_tech["gas_ct"]`
  — netted only against **this year's** decisions, never against pending; and
  the backstop commissions **in-year** (`adequacy.py:497–500` appends the unit
  directly to the fleet, no `entry_pipeline` row), so it never *creates* a
  pending row either.

So the two consumers of the **same** ladder budget — which rule 19 declares to
be *one physical queue* — apply **different** netting. That inconsistency is
internal to the shipped code and independent of whether the netting is right.

---

## 2. The `(K, L)` map — is `K = L` reachable elsewhere, or unique to MISO solar?

`K = 2.0` is a **single global scalar** (`entry_config.py:25`), not per-tech or
per-ISO. `L = 2` for every entry technology and for the default
(`ENTRY_COD_LAG_YEARS = {wind: 2, solar: 2, gas_cc: 2, gas_ct: 2}`,
`ENTRY_COD_LAG_DEFAULT_YEARS = 2`).

> **`K = L` in 24 of 24 ISO × entry-tech cells, at both vintages. There is no
> cell off the knife-edge anywhere in the model.**

Seeds measured by re-running `data.build_throughput`'s own construction over the
EIA-860 vintages on disk (`ENTRY_THROUGHPUT_WINDOW_YEARS = 10`). `binds` is the
smallest of {ladder `K×seed`, static per-tech cap, ISO budget} in the first
decision year:

**vintage 2020 (COD window 2011–2020) — the capacity-hindcast lane**

| ISO | tech | seed GW | ladder | static | binds | K−L+1 |
|---|---|---|---|---|---|---|
| ERCOT | wind | 3.472 | 6.944 | 5.0 | per_tech_cap | 1.0 |
| ERCOT | solar | 2.473 | 4.946 | 5.0 | **growth_ladder** | 1.0 |
| ERCOT | gas_cc | 2.570 | 5.140 | 3.0 | per_tech_cap | 1.0 |
| ERCOT | gas_ct | 0.785 | 1.570 | 3.0 | **growth_ladder** | 1.0 |
| CAISO | wind | 1.968 | 3.936 | 3.0 | per_tech_cap | 1.0 |
| CAISO | solar | 2.839 | 5.678 | 4.0 | per_tech_cap | 1.0 |
| CAISO | gas_cc | 1.377 | 2.754 | 2.0 | per_tech_cap | 1.0 |
| CAISO | gas_ct | 2.201 | 4.402 | 1.0 | per_tech_cap | 1.0 |
| PJM | wind | 1.271 | 2.542 | 1.5 | per_tech_cap | 1.0 |
| PJM | solar | 1.220 | 2.440 | 6.0 | **growth_ladder** | 1.0 |
| PJM | gas_cc | 11.664 | 23.328 | 4.0 | per_tech_cap | 1.0 |
| PJM | gas_ct | 0.551 | 1.102 | 2.0 | **growth_ladder** | 1.0 |
| MISO | wind | 4.367 | 8.734 | 4.0 | per_tech_cap | 1.0 |
| MISO | solar | 0.618 | 1.236 | 6.0 | **growth_ladder** | 1.0 |
| MISO | gas_cc | 1.723 | 3.446 | 3.0 | per_tech_cap | 1.0 |
| MISO | gas_ct | 0.742 | 1.484 | 2.0 | **growth_ladder** | 1.0 |
| NYISO | wind | 0.238 | 0.476 | 1.0 | **growth_ladder** | 1.0 |
| NYISO | solar | 0.223 | 0.446 | 2.0 | **growth_ladder** | 1.0 |
| NYISO | gas_cc | 1.312 | 2.624 | 1.0 | per_tech_cap | 1.0 |
| NYISO | gas_ct | 0.512 | 1.024 | 0.5 | per_tech_cap | 1.0 |
| NEISO | wind | 0.358 | 0.716 | 1.0 | **growth_ladder** | 1.0 |
| NEISO | solar | 0.257 | 0.514 | 2.0 | **growth_ladder** | 1.0 |
| NEISO | gas_cc | 1.640 | 3.280 | 1.0 | per_tech_cap | 1.0 |
| NEISO | gas_ct | 0.540 | 1.080 | 0.5 | per_tech_cap | 1.0 |

**vintage 2024 (COD window 2015–2024) — the forecast lane.** Same census:
`K = L` in 24/24; the ladder is the first binder in **8** cells (ERCOT gas_ct,
CAISO wind, PJM gas_ct, MISO gas_ct, NYISO solar, NYISO gas_ct, NEISO wind,
NEISO solar), the static per-tech cap in the other 16. Full table in
`scripts/` reproduction below (§6).

**Reading.** The *knife-edge freeze* (ladder pinned at `1 × D_prev` forever)
binds in the **9 (v2020) / 8 (v2024) ladder-first cells**. In the remaining
cells the static per-tech cap binds first — but §3.3 shows the netting deforms
**that** cap too, by exactly the same mechanism, into an effective `C / L`.
**So the defect touches all 24 cells; only its signature differs.** This is a
ten-cell problem, not a one-cell problem.

---

## 3. The derivation

### 3.1 The recursion, stated generally

Let `D_Y` be the MW a tech decides in year `Y`, `L` the COD lag, `K` the ladder
multiple. Rows are removed from `entry_pipeline` at their COD **before** the
screen runs (`evolve.py:576–600`, step 4.5), so pending at the year-`Y` screen is

```
pending_Y = Σ_{i=1..L-1} D_{Y-i}
```

The ladder budget is `K × max(D_{<Y})`, and the shipped code offers

```
remaining_Y = K × max(D_{<Y}) − pending_Y
```

On a growing path (`max(D_{<Y}) = D_{Y-1}`) with a locally constant rate `D`:

```
remaining = (K − L + 1) × D
```

The growth factor is `K − L + 1`. It equals 1 — frozen — exactly at `K = L`;
it is **negative** (entry dies outright) for `L > K + 1`; it doubles as intended
only at `L = 1`, i.e. no lag. The shipped `(K, L) = (2, 2)` sits on the
knife-edge in every cell (§2).

### 3.2 What ReEDS actually bounds, and the correct transcription

ReEDS's published constraint bounds **annual installations** at 200 % of the
prior maximum **annual installations**. ReEDS has no separate decision→COD lag
in that constraint: decision year *is* installation year. Our model separated
the two.

Under the separation, each decision cohort maps **1:1** onto an installation
cohort exactly `L` years later. Therefore:

> Capping **decisions** at `K × prior-max decisions`, with **no stock
> deduction**, reproduces "installations ≤ `K` × prior-max installations"
> **exactly**. Any additional deduction enforces a constraint ReEDS does not
> publish and this repo does not cite.

This is a *transcription* argument, not a fit: it introduces no parameter, and it
leaves `K = 2.0` and `L = 2` untouched at their own citations. It is the
rule-23 `[R-FROZEN-DERIVE]`-admissible answer, because nothing in it responds to
a residual.

### 3.3 The general law the netting actually imposes (and its validation)

A constant decision rate `D` is feasible under a netted flow cap `C` iff
`D ≤ C − (L−1)D`, i.e.

```
D ≤ C / L
```

> **Netting a pipeline stock from an annual-flow cap halves it at L = 2 — for
> every cap the netting touches, ladder or static.**

This is not speculation; it is already **measured** in a registered run. FFR-3V
§5.1's MISO wind trace, reproduced to the MW against the registered leg, shows
wind alternating **4,000 / 0 / 4,000 / 0 MW** against its `C = 4.0 GW/yr` static
per-tech cap — mean **2.0 GW/yr = C / L**. The law predicts the observed
alternation and its mean exactly, on a cell where the *ladder* was never the
binder. That is the independent confirmation that the defect is the netting and
not the ladder multiple.

The two signatures are therefore:

| binding cap | signature | mean rate |
|---|---|---|
| ladder (`K × prior_max`, endogenous) | frozen at the seed's `K × D_seed` forever; ratchet dead | `K × D_seed`, never rises |
| static per-tech (`C`, exogenous) | alternating `C, 0, C, 0, …` | `C / L` |

### 3.4 The identifying data (rule 23)

Rule 23 `[R-FROZEN-DERIVE]` binds this lane hardest: the derivation must cite the
**data** that identifies it, never a residual. Three measured statistics, all
from the same EIA-860 source the ladder seed itself comes from
(`data.build_throughput`'s construction, both vintages on disk):

**(i) The observed record ratchets; the shipped mechanism admits no ratchet.**
For every ISO × entry-tech, the empirical analogue of the ladder ratio is
`r_Y = D_Y / max(D_{<Y})` — a *new annual-build maximum* is `r_Y > 1`:

| vintage (COD window) | ISO-tech-years | with a **new maximum** |
|---|---|---|
| 2020 (2011–2020) | 214 | **69 (32.2 %)** |
| 2024 (2015–2024) | 209 | **62 (29.7 %)** |

The shipped configuration admits a new maximum in **0 %** of years by
construction (`K − L + 1 = 1`). A mechanism that forbids what the source data
does roughly a third of the time is falsified by that data. **This is the
identification, and it is external, formulaic, and vintage-regenerating** —
it is recomputed from any EIA-860 release and responds to changed data, never to
a model residual (rules 13 / 23).

**(ii) `K = 2.0` is corroborated, and must not move.** The measured ratio
distribution across all cells:

| vintage | p50 | p75 | **p90** | p95 | exceeds K = 2.0 |
|---|---|---|---|---|---|
| 2020 | 0.512 | 1.167 | **2.374** | 3.852 | 24 / 214 (11.2 %) |
| 2024 | 0.552 | 1.237 | **2.196** | 3.318 | 24 / 209 (11.5 %) |

`K = 2.0` sits between the p75 and the p90 of the observed growth-ratio
distribution and is exceeded in ~11 % of ISO-tech-years. That is exactly what a
*hard bound that occasionally binds* should look like: it is neither slack nor
punitive on the measured record. **The data supports leaving `K` at its ReEDS
value** — which is also what the owner's card requires. Any proposal to raise
`K` to "unfreeze" the ladder would be moving a well-corroborated parameter to
compensate for an uncited term, i.e. burying the error inside an input
(rule 14 `[R-ACCURATE]`).

**(iii) `L` is untouched.** `L = 2` is LBNL *Queued Up* 2024's median IA→COD
(≈ 25 months, 861-project sample). Nothing in this derivation bears on it, and
per the charter it is a D-2 field under Addendum D's HOLD PROMOTION and sets the
D-9 censoring window. **Not changed here.** (§7 records the one place where a
finding *touches* `L` and why it is escalated rather than landed.)

### 3.5 Where the anti-cobweb guard actually belongs

Removing the netting removes a guard, and the guard's target is real. Its
target is **not** throughput; it is that the entry screen's revenue signal is
**blind to committed-but-not-online capacity**. Confirmed in code:
`runner.py::_lookahead_reprice_signal` builds the pro-forma price by pricing
next year's net load into the **current fleet's** merit stack
(`fleet_arrays.pmax`, `runner.py:518–527`) — the `entry_pipeline` rows do not
appear in that stack, and next year's VRE term is *this* year's realised output.
So a developer's pro-forma in this model genuinely cannot see two years of its
own committed pipeline, and will re-decide the same opportunity every lag year.

The structurally faithful fix (rule 1 `[R-STRUCT]`) is therefore to make the
pro-forma see the pipeline — add pending rows to the stack the signal prices
against, at their known MW and known COD year. That is zero-DOF (the rows are
already carried with `mw` and `cod_year`) and it puts one mechanism at one
phenomenon. **It is a revenue-side mechanism change with solve consequences and
is escalated, not landed in this derivation lane** (§7).

---

## 4. Pre-registered prediction (written and committed BEFORE measuring)

Instrument: a multi-year harness driving the **real**
`apply_economic_new_entry` (the shipped code path, not a hand trace), with
MISO's measured `vintage_2020` solar seed 0.618 GW, all techs profitable
(flat high price), the real ladder update from `runner.py:1153–1160`, and the
real step-4.5 pipeline commissioning. Two counterfactual arms are compared to
the shipped arm; each is produced by removing a netting term and nothing else.

**Arm 0 — shipped.** Prediction: decisions **frozen at 1,236 MW every year**,
first year onward; commissioned within 2021–2025 = **2.473 GW**. (This is a
*replication* prediction: matching FFR-3V §5's number validates the harness
before the counterfactuals are read.)

**Arm A — netting removed from the ladder only** (kept on the static per-tech
cap). Predicted MISO-solar decisions 2022→2025:
**1,236 → 2,473 → 3,527 → 2,473 MW**, then a permanent **3,527 / 2,473
alternation** (mean 3,000 MW = static cap 6,000 / L). Commissioned 2021–2025 =
**3.709 GW**; decisions 2022–2033 (a 2035-horizon proxy) ≈ **36.0 GW**.

**Arm B — netting removed from both flow caps.** Predicted decisions 2022→2025:
**1,236 → 2,473 → 4,946 → 6,000 MW**, then **6,000 MW/yr** (the static cap,
now the true binder). Commissioned 2021–2025 = **3.709 GW** (identical to Arm A
— only the 2022 and 2023 decisions reach COD by 2025, so the short window
cannot separate the arms); decisions 2022–2033 ≈ **62.7 GW**.

**Therefore, pre-registered:** the 2021–2025 hindcast window is **too short to
discriminate Arm A from Arm B** (both 3.709 GW), and neither reaches MISO's
18.649 GW actual — i.e. **this fix alone does not close FFR-3V's FC-3 miss**,
because the leg's solar decides zero for revenue reasons (§6.2 of that doc)
before any cap binds. The arms separate only on the **decision series** and on
horizons past 2026. Any claim that removing the netting "fixes MISO solar"
would be false, and is pre-registered as false here.

---

## 5. Measurement

*(§5 is appended after §1–§4 were committed; see the commit sequence in §6.)*

---

## 6. Reproduction

---

## 7. What I did NOT separate, and what is escalated

---

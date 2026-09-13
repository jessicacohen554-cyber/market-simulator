# PRECOMMIT (pjm-h5) — chartering the coal COMMITTED-band measured re-pricing

**Session** `pjm-h5` · **ISO** PJM · **Date** 2026-09-13 · **Base** `origin/main` @ `39a1c9a1`
**ZERO LP.** Everything below is `run_calibration.run_year(fleet_only=True)` on the keeper
bundles' own `meta.json` recipes plus artifact/config reads — the rule 29 `[R-SCREEN]` clause-0
path. No shard launched, no LP in the parent (rule 32 `[R-SHARD]` (a)).
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**

This document is written **before any solve** and carries every number the lane will cite, so
the ex-ante declarations below cannot be re-written to fit a result (rule 29 clause (b)/(c)).

---

## 0. TASK 0 — HOUSEKEEPING (done, committed)

* **S1 repaired.** `audit_keepers --iso PJM` failed S1: `frontend/data/backcast/status/PJM.js`
  stale against current verdicts. This is **main drift** from other lanes' engine commits, not a
  PJM change. `build_status.py --iso PJM` rebuilt it; `--check` reads in sync; PJM still
  **CALIBRATED**. Committed as `919cae51`.
* **The bench rebuild is JUDGED NOT NEEDED, on a code audit rather than a guess.**
  `check_bench_freshness --iso PJM` reads **0 STALE** (every part's payload fingerprint equals
  HEAD's) with a **soft engine-drift warning on all 6 parts**. That warning is a raw count of
  commits under `src/market_sim/data|config` — it fires on *any* lane's commit, which
  `bench_stamp.py`'s own docstring says is deliberate ("Folding them into the hash would mark
  every part stale after any lane's edit"). The two commits it counts, classified G-DRIFT-style:

  | commit | touches | verdict for the PJM bench |
  |---|---|---|
  | `0c0d2305` nyiso-232 | `config/scenarios.py` **+91 / −0** | **INERT** — a pure addition of a gated, default-off NYISO field. It changes no existing default, and the bench part is a function of `(year, iso)` + reference data, not of an offer-band flag. |
  | `9398000d` SOCO-15 | `data/cod_ramp.py`, `fleet/{__init__,arrays,eia860}.py` | **INERT for the bench.** Its whole effect is the `online_mask` built inside `FleetArrays` (`arrays.py`: `effective_cod`/`monthly_online_mask` → `generator_online_mask`) — a **model-side availability array**. The bench builder (`render_calibration_html.py`) reaches the engine only for `load_campd_bins` (the plant→class map, a parquet read), `apply_other_fossil_scoring`, and two path constants from `fleet.eia860`. None routes through `FleetArrays` or `cod_ramp`. It moves neither the plant→class map, nor CHP shares, nor the EIA-923 reconciliation — the three things the warning names. |

  Both INERT ⇒ the ~25 min zero-LP rebuild buys nothing measurable, and no C1 verdict in play is
  marginal (the three FAILs are 1.6–2.9× the 8 TWh band; the two PASSes are at 38–46 % of it).
  *Stated so it can be checked rather than trusted: `9398000d` DOES move the model side, so it is
  live for a future re-solve — it is inert for the BENCH only.*

---

## 1. THE LOAD-BEARING PREMISE — VERIFIED, WITH ONE CORRECTION

The card's premise is that coal's `committed` band is **not floored**, so re-pricing it moves
DISPATCH rather than only price.

**The code half is verified and it is stronger than the card stated.** `assembly.py` has exactly
two per-tranche floor seams, and neither can reach a coal `committed` tranche:

```python
sync_floor = cap if (coal_sync and suffix in ("mustrun", "sync")) else 0.0   # :1417
cc_floor   = cap if (cc_mustrun_frac > 0.0 and suffix.startswith("committed")) else 0.0  # :1423
```

`cc_floor` is the one that keys on `committed` — and `cc_mustrun_frac` is gated at `:1311` on
`group == "CC_REGULAR"` or `group == "ST_GAS"`, so **it can never fire on a coal group**.

**The correction: "not floored" is not literally true, and the measured number is 1.3 %.** The
composed `min_gen` array (`arrays.py::_compose_min_gen_floors`) does put a small floor on coal
`committed` — measured on the 2020 keeper fleet:

| group | band | n | cap MW | floored MWh | cap-hours | **% floored** |
|---|---|---:|---:|---:|---:|---:|
| COAL | **committed** | 64 | **12,550** | 1,426,506 | 109,938,000 | **1.30 %** |
| COAL | mustrun | 52 | — | 51,443,678 | — | (the floored band) |
| COAL | sync | 20 | — | 4,344,264 | — | (the floored band) |
| COAL | econ | 354 | — | 758,925 | — | small |
| COAL | peak | 63 | — | **0** | — | 0 |

**And the attribution makes the correction favourable to the card, not damaging.** Reading the
parallel `min_gen_mechanism` id array (`scripts/probes/_pjm_h5_mingen_attrib.py`):

> **100.00 % of the coal `committed` floor is `MECH_RELIABILITY_FLOOR` (id 4)** — 1,426,506 MWh
> across **5,160 of 560,640 cells (0.92 %)**. **Zero** of it is a commitment mechanism.

So the band carries **no commitment floor whatsoever**; the only `min_gen` on it is the system
reliability backstop firing in tight hours, which is a different object from offer pricing and
binds under scarcity regardless of what the band is offered at. **98.7 % of committed capacity-
hours (99.1 % of cells) are economic** — the premise holds, and this is a dispatch lever, not
only a price lever. Reported at 98.7 % rather than the card's 100 % because the difference is
measurable.

## 2. THE STRUCTURAL FINDING THAT REFRAMES THE ARM

The card frames coal's `committed` 0.548-vs-0.916 as "the LARGEST measured discrepancy in PJM's
coal offer surface". It is — but it is **not a coal defect**. It is the universal registered
posture of PJM's `committed` band, and the arithmetic says so on the keeper's own overrides
against the same artifact, under PJM's own registered convention
(`pipeline/backcast_config.py`: *"committed → avg_committed_p50; econ → marg_econ_{low,high}_p50"*):

| class | registered `committed` | measured `avg_committed_p50` | reg − meas | reg/meas |
|---|---:|---:|---:|---:|
| COAL_WC | 0.5120 | 0.916 | **−0.404** | 0.559 |
| **COAL_BIT** | **0.5480** | **0.916** | **−0.368** | **0.598** |
| CC_CHP | 1.0000 | 1.359 | **−0.359** | 0.736 |
| CT_CHP | 0.8640 | 1.163 | −0.299 | 0.743 |
| COAL_PRB / COAL_LIGNITE | 0.6840 | 0.916 | −0.232 | 0.747 |
| COAL (generic) | 0.6480 | 0.916 | −0.268 | 0.707 |
| CT_INTERMEDIATE | 1.0000 | 1.049 | −0.049 | 0.953 |
| CC_REGULAR | 1.0000 | 1.015 | −0.015 | 0.985 |
| ST_GAS | 1.0000 | 1.006 | −0.006 | 0.994 |
| CT_PEAKER | 1.0500 | 1.049 | +0.001 | 1.001 |

**10 of 11 registered classes sit BELOW their measured `avg_committed_p50`**, and COAL_BIT's
−0.368 is second, essentially tied with CC_CHP's −0.359.

**And the sign INVERTS on the econ bands** — 16 of 22 registered econ bands sit *above* their
measured marginal basis (CT_PEAKER econ_high +0.950, CC_REGULAR econ_high +0.448, ST_GAS
econ_low/high +0.281/+0.261). So the registered surface has a coherent shape: **a min-load block
bid below cost and incremental energy marked up.** That is not an error — it is what
`campd_tranche_fuel_frac`'s own docstring says the design intends: *"A passthrough < 1.0
price-takes (an already-online unit bids to clear rather than on full marginal cost); > 1.0 marks
the bid up to suppress over-dispatch."*

**Two consequences bind the charter.**

**(i) A coal-only arm is a SELECTION, not a substitution (rule 1 `[R-STRUCT]`).** Re-pricing coal
alone, while leaving CC_CHP at 1.0 against 1.359 and CT_CHP at 0.864 against 1.163, picks the one
class whose move helps the 2020 residual. The non-selective form — every class to its own
measured `avg_committed_p50` — is available at almost no extra cost (§3), so the selection buys
essentially nothing and costs the rule.

**(ii) The band is declared IN CODE as a price parameter, not a heat rate.**
`backcast_config.py:189` — *"Calibrated PJM thermal offer curve (per-class band heat-rate
multipliers on AHR × delivered fuel price). **Price-calibrated multipliers, not literal heat
rates.**"* And the model's own registered mechanism for reconciling bid against measured physics
(`gas_offer_net_revenue_margin`, `phys_*`) treats bid-below-phys as *legitimate price-taking with
the markup clipped to zero* — every PJM `phys_committed` line says so in its own comment
("avg_committed_p50 > bid → markup clips 0"). NYISO's lane reached the same reading independently
(`_nyiso232_st_gas_phase0.py`: committed "sits BELOW its own measured `phys_committed` 1.104, so
its markup clips to 0 in BOTH legs"). So rule 14 `[R-ACCURATE]`'s **misalignment exception** is
squarely in play: the measured quantity and the model parameter are not the same object.

*This does not by itself refuse the arm — it refuses the framing "rule 14 compels it". Rule 14
compels preferring measured data over an estimate **of the same quantity**; a price-calibration
parameter is a different quantity from a measured average min-load heat rate.*

## 3. (a) THE PRE-SOLVE OFFER-ARRAY DELTA — EXACT, PER YEAR, ON THE REAL KEEPER FLEET

Computed by diffing the model's own assembled P0 offer array `mc_base` between two
`fleet_only` builds — **not reconstructed arithmetic**. Probe:
`scripts/probes/_pjm_h5_committed_delta.py`. Three arms:

* **COAL** — the card's arm: every coal group's `committed` := 0.916.
* **ALL** — the non-selective substitution: every class's `committed` := its own measured value.
* **REPLACE** — the rule-19 form (§4): coal `committed` := 0.916 **and** the bituminous sigmoid
  removed from that band, so the effective basis IS 0.916 in every hour of every year.

**Confinement holds exactly**: in every arm the ONLY band that moves is `committed`, and only in
the targeted groups. `pmax` and availability are untouched (row count and `unit_id` order
asserted identical).

Capacity-weighted $/MWh. The COAL and ALL arms are **identical on every coal row** (the extra
classes ALL touches are non-coal), so the coal columns are shared:

| yr | **coal `committed` Δ$/MWh** | all-coal Δ | fleet Δ (COAL arm) | fleet Δ (ALL arm) | **footprint** 10³ MW·$/MWh |
|---|---:|---:|---:|---:|---:|
| 2020 | +6.0611 | +1.5407 | +0.3654 | +0.4366 | 76.1 |
| 2021 | +8.8636 | +2.2531 | +0.5349 | +0.6684 | 111.2 |
| **2022** | **+14.7560** | +3.7510 | +0.8906 | +1.1310 | **185.2** |
| 2023 | +10.1763 | +2.5868 | +0.6142 | +0.7101 | 127.7 |
| 2024 | +9.6961 | +2.4647 | +0.5852 | +0.6755 | 121.7 |
| 2025 | +11.5868 | +2.9390 | +0.6990 | +0.8373 | 145.4 |

**The card's indicative arithmetic is confirmed**: it predicted ≈ +$5.97/MWh for 2020 and the
exact figure is **+6.0611** (1.5 % high). The lever is real and it is **~5× the arm pjm-h4 killed**
(that one was +0.51 $/MWh all-coal in 2020; this one is +1.54).

**§2(i) quantified — the "selection premium" is small, which is why the selection is not worth
making.** Going from the coal-only arm to the non-selective ALL substitution moves the whole-fleet
number by only **+19 %** (2020: +0.3654 → +0.4366), because the classes coal-only omits are either
already at their measured value (CC_REGULAR 1.0 vs 1.015, ST_GAS 1.0 vs 1.006) or tiny (CC_CHP
557 MW, CT_CHP 202 MW at +6.13 / +6.10 $/MWh). **Coal is 84 % of the non-selective move.** So
restricting to coal buys ~nothing in effect and costs the rule-1 objection outright.

Rows moved, 2020: **64 of 2,981** (COAL arm), **276 of 2,981** (ALL arm), **64 of 2,981**
(REPLACE) — band `committed` only, groups exactly as targeted, in every year.

### 3.1 The REPLACE arm — measured, and it is a DIFFERENT SHAPE, not just a bigger number

| yr | **REPLACE** Δ$/MWh | COAL arm Δ$/MWh | REPLACE / COAL | REPLACE all-coal | REPLACE fleet | **REPLACE footprint** |
|---|---:|---:|---:|---:|---:|---:|
| 2020 | +12.6296 | +6.0611 | **2.08×** | +3.2105 | +0.7614 | 158.5 |
| 2021 | +7.8450 | +8.8636 | 0.89× | +1.9942 | +0.4735 | 98.5 |
| **2022** | **+5.1848** | **+14.7560** | **0.35×** | +1.3180 | +0.3129 | 65.1 |
| **2023** | **+17.6561** | +10.1763 | 1.73× | +4.4882 | +1.0657 | **221.6** |
| 2024 | +16.8422 | +9.6961 | 1.74× | +4.2813 | +1.0165 | 211.4 |
| 2025 | +12.0271 | +11.5868 | 1.04× | +3.0507 | +0.7255 | 150.9 |

**Read the 2022 row — it is the whole argument in one number.** In the dearest-gas year REPLACE
is **one third** of the card's arm (+5.18 vs +14.76), because the card's arm has the sigmoid push
the "measured" basis to **1.2045**, a 31 % overshoot of the 0.916 it claims to be installing.
REPLACE pulls it back to 0.916 and the delta shrinks accordingly. **A form that is smaller
exactly where the incumbent mechanism is most distorting is the one tracking the measurement.**

## 4. (b) RULE 19 `[R-ONE-MECH]` — WHAT ALREADY PRICES THIS BLOCK, AND THE EX-ANTE DECISION

**Enumerated.** Two mechanisms price the coal `committed` block, and they multiply:

1. **The band multiplier** (`offer_curve_by_group` COAL_BIT `committed` = 0.548) — the authorized
   price-tuning channel of the rules 1/13 amendment.
2. **The gas-keyed bituminous passthrough sigmoid** — PJM `{floor 0.65 (keeper override; shared
   default 0.76), ceil 1.32, gas_mid 3.40, gas_slope 2.5}`, applied as a **fuel fraction** through
   `campd_tranche_fuel_frac`, i.e. `mc = mult × base_hr × fuel × passthrough`.

*(Not in scope, verified absent from this keeper: the three take-or-pay committed discounts —
`coal_bit_committed_takeorpay`, `coal_committed_takeorpay_{all,regulated,sunk_fixed}` — and
`coal_econ_srmc_bound` are all off/absent in both bundles' `meta.json`, so the committed band
pays full delivered fuel under its supply passthrough and nothing else.)*

**THE DECISION, DECLARED EX ANTE: REPLACE, NOT RECONCILE, AND NEVER STACK.**

Substituting the multiplier while the sigmoid still scales the same block is **stacking**, and it
does not even deliver the measurement: the effective basis becomes `0.916 × passthrough`, which
**undershoots** the measured 0.916 in cheap-gas years and **overshoots** it in dear-gas years.
A substitution that lands on the measured value in *no* year is not a rule-14 substitution.

So the admissible form removes the sigmoid from the `committed` band only. The econ/peak bands
keep it, because its stated rationale — *"the gas price at which a gas-CC's fuel cost equals the
coal plant's"*, i.e. the merit-order crossover — is about **incremental** coal competing against
gas, which is what the econ bands represent. The min-load block is not competing for the marginal
MWh; it is the cost of being on. Under REPLACE the effective basis is **0.916 in every year and
every hour**, which is also what makes it year-invariant under rule 1 condition (b).

**THE MEASUREMENT THAT SETTLES IT.** Effective committed basis = multiplier × mean bituminous
passthrough, computed from the model's own `coal_passthrough_series` on the keeper's config:

| yr | passthrough | eff. **registered** (0.548 × pt) | eff. **substituted** (0.916 × pt) | **vs measured 0.916** |
|---|---:|---:|---:|---:|
| 2020 | 0.6744 | 0.3696 | 0.6177 | **−0.2983** |
| 2021 | 1.0105 | 0.5538 | 0.9257 | +0.0097 |
| 2022 | 1.3150 | 0.7206 | 1.2045 | **+0.2885** |
| 2023 | 0.7573 | 0.4150 | 0.6937 | −0.2223 |
| 2024 | 0.7530 | 0.4126 | 0.6898 | −0.2262 |
| 2025 | 0.9645 | 0.5286 | 0.8835 | −0.0325 |

> **The card's arm substitutes a single measured number 0.916 and delivers an effective basis
> that lands on it in ZERO of six years — 0.618 in 2020, 1.205 in 2022, a 95 % spread.** It
> undershoots the measurement by 0.298 in the cheapest-gas year and overshoots it by 0.289 in the
> dearest. **"We are substituting the measured physics" is therefore FALSE as implemented**, and
> that is arithmetic rather than opinion. Only REPLACE delivers 0.916 in every hour of every year.

*One thing this is NOT, stated so the argument is not overclaimed: the sigmoid's year-variation is
**not** a breach of the rules 1/13 condition (b) "one config across every scored year". The config
IS one value; the passthrough is a condition-responsive MECHANISM, which is what rule 13's forward
test wants, not a per-year fitted number. The objection to leaving it on this band is rule 19
(it already prices the block, so the substitution stacks) and rule 23 (§9 — its `gas_mid`
provenance), not condition (b).*

## 5. (c) THE DIRECTION — REPORTED, AND EXPLICITLY NOT A GATE

Rule 1 `[R-STRUCT]` forbids selecting a mechanism on whether it moves the residual, so this is a
report line and nothing else, **written before the screen exists**:

Dearer coal at min load pushes COAL_BIT energy **down**. It therefore helps **2020 (+22.83 TWh)**
and **risks 2023 (+2.10) and 2024 (−0.12)** — two training years whose COAL_BIT sits comfortably
inside the 8 TWh band on an 8/8 zero-caveat keeper. **A regression there is NOT a reason to
revert**: rule 14 is explicit — *"keep the accurate input, find and fix the real root cause."*
Equally, an improvement in 2020 is **not** what would license the arm; only the structural gate
in §7 can do that.

## 6. (d) THE SCREEN YEAR — NAMED ON FOOTPRINT, NOT ON THE RESIDUAL

Metric, fixed before the numbers existed: `|Δ$/MWh on the committed band| × committed-band
capacity`. This is the mechanism's own measured footprint, per rule 29's step (1).

**The screen year DEPENDS ON WHICH ARM IS CHARTERED, and that is itself a finding:**

| arm | 1st | 2nd | 3rd |
|---|---|---|---|
| COAL / ALL (card's form) | **2022** (185.2) | 2025 (145.4) | 2023 (127.7) |
| **REPLACE** (§4's form) | **2023** (221.6) | 2024 (211.4) | 2020 (158.5) |

**The card's form points at 2022 only because the sigmoid points there.** 2022 carries the
highest passthrough (1.315), and the card's arm multiplies by it — so the footprint metric is
being steered by the very mechanism §4 says does not belong on this band. Strip it and the
ranking follows what it should: the years with the dearest measured seam coal (2023 = 3.2250,
2024 = 3.1145 $/MMBtu).

**DECLARED: if the arm is chartered in its REPLACE form, the screen year is 2023.** Named on
footprint, pre-registered here, and **not** the biggest-residual year (that is 2020, at +22.83
TWh, which ranks 3rd on footprint). *The card predicted "likely 2023/2024, NOT 2020" and
instructed "compute it, do not assume" — computed, and the prediction holds for the admissible
arm.*

## 7. THE STRUCTURAL SCREEN GATE — PRE-REGISTERED, STOP-ONLY

Per rule 29, the gate may **kill** an arm and may **never promote** one, and it is never read on
the target residual. The arm proceeds past a screen only if ALL hold:

* **G-1 confinement** — only `committed` rows move; zero rows outside the targeted groups.
  *(Already measured PASS at phase 0 for all three arms.)*
* **G-2 identity** — the armed effective committed basis equals 0.916 to <1e-6 in every hour
  (REPLACE's defining claim). An arm that cannot hold its own identity is dead.
* **G-3 magnitude/direction** — the dispatch response has the sign and order of magnitude the
  pre-solve delta implies; COAL_BIT energy falls, and by a magnitude consistent with §3.
* **G-4 no load-bearing flip** — no non-target load-bearing criterion (C1 on another class, C2,
  C3a, C3b) crosses PASS → FAIL.
* **G-CTRL** — form 4 (the committed keeper bundle IS the control; no control solve), valid only
  on a clean **G-DRIFT** audit at the time the shard is launched.

## 8. DOF (rule 21 `[R-DOF]`) — ZERO NEW FREE PARAMETERS, AND THE TRAP NAMED

The operand is **not chosen**: `avg_committed_p50` is fixed by the convention already committed to
`backcast_config.py`, and the artifact carries exactly **one `COAL` row (n=65)**, so there is no
per-supply value to select between. Nothing in this charter is swept.

**The trap, restated as the card names it:** any value chosen *between* 0.548 and 0.916 is a
fitted adder and is refused. So is arming the substitution on the one class where it helps.

## 9. WHAT IS ESCALATED, NOT SETTLED IN-LANE

**(1) The `gas_mid` mis-grounding — TASK 2, measured here, and it is the SAME OBJECT as task 1.**
`derive_coal_sigmoid.py` builds the crossover as `deliv = ACR regional f.o.b. / 0.85`, then
`gas_mid = deliv × COAL_HR / CC_HR`. Three numbers exist and the live one is none of them:

| basis | delivered coal $/MMBtu | implied `gas_mid` |
|---|---:|---:|
| `derive_coal_sigmoid.py` at HEAD (ACR f.o.b. ÷ 0.85) | 4.307 | **7.08** (h2b §1.1) |
| the model's OWN measured EIA-923 receipts (243 DIRECT rows, cap-wtd) | **2.786** | **4.58** (pjm-170 §2.1) |
| **LIVE REGISTERED** | — | **3.40** |

The registered centre matches neither its own derive script nor the model's own fuel prices, and
it sits **$1.18–3.68/MMBtu low**, so the curve rises too early in gas-price space. That is a
rule-23 `[R-FROZEN-DERIVE]` wart living inside an 8/8 keeper (a parameter whose value moved off
its derive script's output on a volume residual).

**HOW THIS SESSION SETTLES IT, per the card's "settle them together or explicitly defer one":**
the §4 REPLACE decision **settles it for the `committed` band by removing the sigmoid from that
band entirely** — the mis-grounded centre then cannot reach the min-load block at all, in any
year. The **econ/peak half is explicitly DEFERRED and escalated**: those bands keep the sigmoid,
its centre is still mis-grounded there, and re-centring it is inside the **owner-declared-closed
pjm-142 price-formation frontier** (and adjacent to the `ceil` 1.32 question pjm-170 left open).
That is not a lane call.

**What the mis-grounding is worth, measured** (`scripts/probes/_pjm_h5_gasmid.py` — mean
bituminous passthrough on the keeper's own gas series under each candidate centre; floor 0.65,
ceil 1.32, slope 2.5 held fixed, only `gas_mid` moved):

| yr | gas $/MMBtu | **live 3.40** | model-consistent 4.58 | derive-at-HEAD 7.08 | live − consistent |
|---|---:|---:|---:|---:|---:|
| 2020 | 1.936 | 0.6744 | 0.6514 | 0.6500 | +0.023 |
| **2021** | 3.581 | **1.0105** | 0.7921 | 0.6508 | **+0.218** |
| 2022 | 6.479 | 1.3150 | 1.2543 | 0.9088 | +0.061 |
| 2023 | 2.485 | 0.7573 | 0.6630 | 0.6500 | +0.094 |
| 2024 | 2.387 | 0.7530 | 0.6980 | 0.6504 | +0.055 |
| 2025 | 3.745 | 0.9645 | 0.7909 | 0.7058 | +0.174 |

**The live centre inflates the passthrough in EVERY year**, by up to **+0.218** (2021) against
the crossover the model's own delivered coal implies — worth ≈ **$2.83/MWh** on the committed
band alone in 2021 (`0.548 × 11.176 × 2.1229 × 0.218`), and more on the econ bands above it.

**And a second observation worth recording, because it inverts the usual reading:** at its OWN
derive script's output (7.08) the sigmoid would sit at its floor 0.65 in **four of six years** —
i.e. nearly inert. **It is the drift of the centre from 7.08 down to 3.40 that gives the curve
essentially all of its effect.** A mechanism whose entire bite comes from a parameter that
matches neither its derive script nor the model's own fuel prices is a rule-23
`[R-FROZEN-DERIVE]` finding, not a calibration.

**(2) A SECOND parity RED has appeared on `origin/main`, and it is not PJM's.**
`check_registry_payload_parity` now fails on **two** bundles: the known
`caiso279_ablate_dswcouple_span` (CAISO's, the card says never `rm` it) **and**
`results/calibration/soco15_spp_arm`, committed by the SOCO lane at `59c045e1`
("SOCO-15 SPP arm: spp38_span recipe replayed at 4f33476c"). Both verified present on
`origin/main`, neither touched here. The card's "1 PRE-EXISTING RED" is now 2.

**(3) Standing escalations carried forward unchanged** (from the card; this session neither
settled nor disturbed any): PS-net-inclusive `OTHER` as the `gas_foldin_deflation` operand
(worth 9.3–9.8 TWh of held-out C1, zero determinations); the EIA-930 PJM 2021 `net_gen`
corruption (three cells in `EIA930_BALANCE_2021_Jul_Dec.parquet`, one reading ≈ 2³¹ — inert
today, latent trap); whether the coal sigmoid should be clipped at 1.0; and the display-stale
`volErr`/`nonFosErr` in the PJM 2021/2022 run payloads (no gate reads either; refreshing needs
the six-year re-solve).

## 10. THE CHARTER VERDICT — AND THE OWNER DECISION IT NEEDS

**The arm AS THE CARD FRAMES IT does not stand, and the reason is arithmetic rather than
judgement.** The card required it be argued as a rule-14 `[R-ACCURATE]` substitution "or not at
all". Argued that way it fails on the measurement it rests on: **the substitution delivers the
measured 0.916 in ZERO of six years** (§4 — 0.618 in 2020, 1.205 in 2022), because the sigmoid
still multiplies the same block. A substitution that never lands on its own measured value is
not a substitution. Add §2's two structural findings — coal-only is a **selection** among 10 of
11 classes that all sit below their measured basis, and the parameter is declared in code as a
**price-calibrated multiplier, not a literal heat rate** — and the rule-14 framing is not
available.

**This is NOT a pjm-h4-style kill.** Unlike the `phys_*` arm (inert on 56 % of the fleet,
sub-dollar everywhere), this lever is **real and large**: +6.06 to +14.76 $/MWh on 12.55 GW,
**~5× the arm h4 killed**, and 99.1 % of the band's cells are economic (§1). It has genuine
reach. What it lacks is an admissible *justification*, and there are exactly two routes to one —
**both of which are owner calls, not lane calls**:

| | **Route A — REPLACE** | **Route B — authorized price tuning** |
|---|---|---|
| basis | rule 14 `[R-ACCURATE]`, done properly | the rules 1/13 carve-out |
| construction | committed := 0.916 **and** the sigmoid removed from that band | band multiplier set to a declared value through `offer_curve_by_group` |
| delivers measured 0.916? | **yes, every hour of every year** | no — effective basis stays year-varying |
| selection? | none if applied to **ALL** classes (costs only +19 %, §3) | permitted — merit-order adjustment is the carve-out's *intended* effect |
| DOF (rule 21) | **zero** free parameters (operand fixed by the registered convention + a single-row artifact) | **one ledgered** free parameter; needs the `authorized_price_tuning` attestation block or **C6 FAILS** |
| build cost | a new `ScenarioConfig` field, cache-key registration, CLI flag, a matrix row + a cell line in **all 7 ISO shards** (rule 28(c)), tests — **~13 files** | config only, no new mechanism |

**RECOMMENDATION: do not spend an LP on this yet, and if it is spent, spend it on Route A applied
to ALL classes.** The reason is not the residual — it is what is at stake under the governance
rules, stated plainly:

> **The arm trades a residual that CANNOT downgrade PJM for a risk to the years that CAN.**
> Rule 30(c) is explicit that a held-out year never downgrades an ISO — PJM's determination *is*
> the 2023–2025 verdict, which currently reads **CALIBRATED, 8/8, zero caveats, empty basis**.
> The entire object of this lane (2020 COAL_BIT +22.83; CC_REGULAR 2021 +16.98 / 2022 +12.81) is
> held-out-year residual that cannot move that determination. Meanwhile the arm's own measured
> direction (§5) makes coal dearer in **every** year, including 2023 (+2.10) and 2024 (−0.12) —
> the two training years that DO set PJM's status.

That is not a reason to revert an accurate input — rule 14 forbids exactly that reasoning, and
if the owner rules the substitution correct then a worse 2023/2024 is a root-cause to chase, not
a veto. It **is** a reason to make the decision deliberately rather than by momentum.

**COST, if the owner charters it** (rule 34 `[R-SHARD-PROMOTABLE]` (c) — PJM's registered year
set is **2020–2025**, so a promotion is a **SIX-year** re-solve, not three):

* screen: **1 year, ~18 min** of shard LP (the screen year is §6's, named on footprint);
* span: **6 years in ONE shard, ~105 min** at the card's measured 17.6 min/PJM-year. Rule 32(b)
  bans a per-year fan-out; a per-plant multi-zone ISO takes a longer single shard with the budget
  stated in its prompt.

**PROMOTION QUESTION (rule 31 `[R-RETAIN]`), STATED EXPLICITLY:** *nothing was solved this
session, so there is nothing to retain, promote or lose.* No shard was launched, no bundle
exists, no LP ran in the parent. The question this session hands back is not "promote or not" —
it is **"which route, if any, should pjm-h6 build?"**

## 11. RULES

Rule 1 `[R-STRUCT]` (§2(i) selection; §5 direction reported, gating nothing; §7 structural gate)
· rule 14 `[R-ACCURATE]` (§2(ii) the misalignment exception, argued rather than asserted)
· rule 19 `[R-ONE-MECH]` (§4 REPLACE declared ex ante) · rule 21 `[R-DOF]` (§8 zero free
parameters) · rule 23 `[R-FROZEN-DERIVE]` (§9, the `gas_mid` wart) · rule 29 `[R-SCREEN]`
clause 0 (this whole document precedes any LP) · rule 30(c) (no held-out year touches PJM's
determination) · rule 31 `[R-RETAIN]` (nothing deleted) · rule 32 `[R-SHARD]` (a) (the parent
ran no LP).

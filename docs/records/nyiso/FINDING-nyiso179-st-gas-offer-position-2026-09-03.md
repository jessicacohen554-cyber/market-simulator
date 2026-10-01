# nyiso-179 — the NYISO `ST_GAS` offer POSITION is **NOT** the governing object: all three of the brief's starting points close on measurement, and the 2025 top-decile deficit decomposes 62 % onto the model's own price level (owner-court), 25 % onto offer position, 13 % onto dispatch against its own signal

**Session:** nyiso-179, NYISO backcast-calibration track, 2026-09-03.
**Keeper: UNCHANGED — `2026-09-02-nyiso-177-vintage-matched`** (bundle
`results/calibration/nyiso177_vintage_B1p`), determination **NOT-YET**, target
grade 5, fails 3 {C1-2023 `ST_GAS`, C3a-2025 −11.2 %, C3c}.
**ZERO SOLVES.** No parameter touched, no band swept, no arm built, no run
registered — **by the pre-registration's own stop conditions S1, S2 and S3, all
three of which fired.**
**Gates:** `results/calibration/PREREG-nyiso179-st-gas-offer-position.md`,
committed with the probe at `15f2d3e8` **before either ran**, including its §7
amendment (four construction defects found by CODE READING before commit) and
its §8 amendment (three more found by the probe's own OUTPUT, committed at
`5264cff2` before the corrected run).
**Machine artifacts:** `results/calibration/_nyiso179_st_gas_offer_position.json`
(gates) and `_nyiso179_g1_robustness.json` (post-gate robustness); probes
`scripts/probes/nyiso179_st_gas_offer_position.py` and
`nyiso179_g1_robustness.py`.

---

## 1. The one-paragraph answer

nyiso-178 closed the availability type and the offer-SHAPE type and handed
forward an offer **POSITION** object with three named starting points. **All
three close on measurement, for zero solves** — the `gas_st_committed_hr_mult`
1.32 is structurally unreachable on this keeper (G0 `INERT`), the armed
oil-parity cap already does the dear-hour fuel job (G2 `LINE CLOSED`: it reaches
83.4 % of the class and relieves \$2.37/MMBtu in 2025's top decile), and the
un-grounded `peak` 4.20 is not where the missing MW sits (G3
`PEAK-EXONERATED`). **And the type itself is refuted:** against the LP's own
marginal-cost array the model dispatches only **0.767 / 0.522 / 0.740** of the
`ST_GAS` its own offer puts in the money (G1 `NOT-OFFER-GOVERNED`), robust to a
strict-inequality sweep, to reserve holding, and to the P0/P1 bid-cost gap. The
substantive result is a **decomposition of the 2025 top-decile deficit** that no
prior session could compute: of the 1,155 MW gap between the measured fleet
(2,597 MW) and the model (1,442 MW), **62 % is capacity the model's own offer
would clear at the ACTUAL price but not at its own lower price** — i.e. it is
downstream of C3a-2025, which is owner-court — **25 % is offer position proper**,
and **13 % is capacity in the money at the model's own price that it still does
not run**. The offer-position lane is therefore **not the lever**; the dominant
term is blocked behind an owner decision, and the residual 13 % is a new named
object this session can bound but not adjudicate.

---

## 2. The instrument, and the four ways it was checked before it was believed

Zero solves. The exact LP marginal-cost array is rebuilt by **calling the
engine** — nyiso-178's validated `lp_fleet` (`load_or_synthesize_bins` →
`bins_to_fleet` → `generators_to_fleet_arrays`) then `resolve_fuel_prices` then
`assemble_mc`, on the keeper's own `run_config.json`. `resolve_fuel_prices`
applies the F923 overlay, the NYISO zonal gas basis and the dual-fuel oil cap
**inside one call, in that order** (read from `data/fuel/resolve.py`, not
assumed), and the keeper carries `carbon_price = nox_price = so2_price = 0`, so
`mc = heat_rate × delivered_fuel + vom` exactly.

| check | question | result |
|---|---|---|
| **V1(a)** | does the offer ramp rise across the bin's bands? | **PASS** — 11 bins, 0 violations |
| **V2** | does the envelope agree with nyiso-178's committed number? | **PASS** — max rel diff 1e-06 |
| **R1** | is `R < 1` a marginal-tranche accounting artifact? | **REAL** — no ε rescues it |
| **R2** | is the withheld capacity held for reserve? | **NO** — overlap ≈ 0 |
| **R3** | is the reconstruction the P1 **bid** cost or only the P0 base cost? | **CLOSED** — markup identically 0 |

**R3 deserves its own line, because it is the one that could have manufactured
G1's failure.** P1 clears on `mc_bid = mc_base + compute_monthly_markup(...)`
(`pipeline/solve.py:295`) while `assemble_mc` returns `mc_base`. Had `ST_GAS`
carried a markup, every in-the-money figure here would have been computed
against an offer **cheaper** than the one the LP actually cleared — inflating
`ITM`, deflating `R`, and fabricating the verdict. **The answer is structural,
not an estimate:** `commitment.py:312` reads
`if gen.fuel_type == "gas_st" and not gas_st_startup_cost: continue`, this
keeper carries `gas_st_startup_cost = False`, and every `ST_GAS` bin's
`fuel_type` is verified to be the `gas_st` the guard keys on. The markup is
**identically zero** and `mc_bid == mc_base` for the class. (`mc_bid_adjust` is
ERCOT-only; the three P1 bridges inject `min_gen` floors, never offer changes.)
**Standing condition:** this holds *because* `gas_st_startup_cost` is off — the
flag nyiso-172 refused two independent ways. A future keeper that arms it
invalidates this instrument until the markup is added.

### 2.1 V1(b) — the pricing rule, measured

The registered class curve prices **100 %** of the `ST_GAS` committed band
(1,874.7 MW) at a realised multiplier of exactly **[1.05, 1.05]**. Zero MW is
priced by the per-plant tranche sheet, and **zero** of the 11 NYISO `ST_GAS`
plants is an `ST_GAS_PEAKER_PLANTS` member. All three pricing routes are
therefore accounted for, and the class curve is the sole one live.

---

## 3. G0 — **INERT**: the brief's starting point (1) is structurally unreachable

`ScenarioConfig.gas_st_committed_hr_mult = 1.32` is consumed at **exactly one
site**, `offer_curves.split_gas_tranches`, which `bins_to_fleet` calls **only**
from its non-CAMPD limb under `not use_campd_bins and config.gas_offer_curve`
(`assembly.py:1912`) — the same limb whose coal sibling was **deleted as
unreachable** at ercot-188. This keeper runs `use_campd_bins=True` /
`plant_level_fleet=True`, so the limb is never entered and **the scalar cannot
price a single MW**. The measured corroboration agrees exactly: every committed
band resolves `base_hr × 1.05`, never `× 1.32` and never `× 1.15`.

**The rule-14 substitution the brief proposed is therefore not available, and
would not be needed if it were.** NYISO's own measured `avg_committed_p50` is
**1.104** (`nyiso_campd_marginal_hr_summary.csv`, base HR 10.614, n=25) and is
**already registered on the curve** as `phys_committed` — within 0.054 of the
live 1.05 band. The caiso-239 instrument does not transfer for a second,
independent reason the brief already flagged: `st_gas_committed_measured_bypass`
reaches only `ST_GAS_PEAKER_PLANTS` members, and **NYISO has none**. Adding a
NYISO entry to `ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO` would be an
unreachable registry entry — a rule-24 `[R-REGISTRY]` liability, not a repair.
**Not armed. DO-NOT-REDO absent a NYISO keeper that leaves the CAMPD path.**

---

## 4. G2 — **LINE CLOSED**: the armed oil-parity cap already does the dear-hour job

Rule 19 `[R-ONE-MECH]` in its intended form: enumerate the armed mechanism
before proposing a new one. `dual_fuel_switching` is **on** for this keeper.

| year | reach (MW / share) | bin-hours capped | top-decile capped | top-decile relief | uncapped → delivered gas |
|---|---|---|---|---|---|
| 2023 | 7,424 / 8,902 = **0.834** | 0.0020 | 0.0075 | \$0.281 | 3.40 → 3.12 |
| 2024 | 7,424 / 8,902 = **0.834** | 0.0060 | 0.0432 | \$0.117 | 4.34 → 4.23 |
| 2025 | 7,424 / 8,902 = **0.834** | 0.0152 | **0.0875** | **\$2.371** | **11.76 → 9.39** |

**The cap reaches 83.4 % of the class and bites hardest exactly where the brief
predicted it should** — 2025's top price decile, where delivered gas runs
\$11.76/MMBtu and the oil parity pulls it to \$9.39, a 20 % relief on the
class's dominant cost term. Both pre-registered legs clear (reach ≥ 0.50;
top-decile binding 0.0875 ≥ 0.05). **S2 fires: the downstate-basis /
`dual_fuel_switching` dear-hour line CLOSES, and no new fuel-side mechanism is
proposed.** `zonal_gas_basis`, `gas_hub_basis_overlay` and `dual_fuel_switching`
stay `K`, untouched.

**Re-open condition, stated:** a keeper whose `ST_GAS` oil-parity reach falls
below 0.50, or one in which the measured NY Harbor ULSD basis is shown wrong.

---

## 5. G3 — **PEAK-EXONERATED**: the un-grounded `peak` 4.20 is not where the missing MW sits

Band decomposition at the ACTUAL RT price, top decile. (`econ*` is the six
`econc00…econc05` slices the `_econ_curve_steps` ramp produces.)

**2025, mean actual price \$176.25 — model 1,442 MW, measured 2,597 MW:**

| band | capacity | ITM MW | OOM MW | OOM-hours share | mean mc |
|---|---|---|---|---|---|
| `committed` | 1,875 | 562 | 193 | 0.244 | \$107.0 |
| `econ*` | 5,692 | 1,654 | 700 | 0.270 | \$112.4 |
| **`peak`** | 1,335 | 97 | **452** | **0.806** | \$415.9 |

`peak`'s share of the class's out-of-the-money MW is **0.336**, below the
pre-registered 0.40 bar, and its OOM-hours share is **0.806**, below the 0.90
bar. **Two of the three conditions fail, so G3 = `PEAK-EXONERATED` and S3
fires: no band value is touched.** The `peak` 4.20 stays **un-grounded**, with
exactly the standing nyiso-169b recorded for the CC/CHP 2.25 — an F-class
constant with no NYISO measurement behind it, and
`nyiso_campd_marginal_hr_summary.csv` carries **no peak column** from which one
could be derived. Grounding it needs a new measured NYISO artifact, not a
sweep; the PREREG pre-declared that so this gate could not become a licence to
tune, and it did not.

**Why it was never going to be the carrier**, in one line: at \$415.9/MWh the
peak band is 2.4× the top-decile price. Even repriced to the very top of what
any defensible measurement could support, it enters the money in a handful of
hours — while 700 MW of *econ-band* steam sits out of the money at \$112 against
a \$176 price, which is the larger and more interesting number.

---

## 6. G1 — **NOT-OFFER-GOVERNED**: the type itself is refuted, and this is the session's main result

`ITM_model(t) = Σ_g pmax·availability·1{mc ≤ P_model[zone(g),t]}` using the
keeper's **own P1 zonal prices**; `R(t) = model_MW(t)/ITM_model(t)`.

| year | median `R` (bar ≥ 0.70) | aggregate `R`, all hours | aggregate `R`, top decile | mean ITM | mean model | mean envelope |
|---|---|---|---|---|---|---|
| 2023 | 0.775 | 0.767 | 0.872 | 1,786 | 1,370 | 3,420 |
| 2024 | **0.448** | **0.522** | 0.723 | 2,141 | 1,119 | 3,243 |
| 2025 | 0.816 | 0.740 | 0.905 | 1,544 | 1,143 | 3,702 |

**G1 fails on the pre-registered median leg in 2024 (0.448 against a 0.70
floor)**, and the aggregate report agrees (0.522). The withheld capacity is
**3.84 / 9.09 / 3.99 TWh** a year of steam the model's *own offer* prices into
the money and that it does not run.

**The failure survives every robustness check that could have excused it:**

* **R1 — not a marginal-tranche artifact.** Capacity within \$1/MWh of the
  clearing price is only **3.1 / 4.6 / 4.1 %** of `ITM`. Sweeping the bound from
  ε=0 to ε=\$5/MWh never brings all three years into band (2024 reaches only
  0.699 at ε=\$5, and a \$5 exclusion band is already far beyond anything the
  marginal-tranche argument supports). `eps_that_brings_all_years_into_band =
  None`.
* **R2 — not reserve holding.** A reserve family binds in **21 / 11 / 38** hours
  of 8,760, while withholding above 10 % occurs in **6,008 / 7,911 / 5,144**
  hours; the overlap is **0 / 2 / 0 hours**. This independently reproduces
  nyiso-152's finding that the NYCA reserve families essentially never bind.
* **R3 — not the P0/P1 bid-cost gap.** Structurally zero for this class (§2).
* **R4 — coherent.** In the 105 / 149 / 470 hours where nothing is in the money
  the model still runs 427 / 263 / 256 MW, which is the forced floor/bridge
  component and is ~20 % of the class mean — the right order, and it inflates
  `R` rather than depressing it.

**S1 fires. The offer-position type is REFUTED and no arm is built** — the same
standing on which nyiso-178 refuted the availability type and the shape type.

### 6.1 The one thing this session cannot adjudicate, stated plainly

**Why** in-the-money `ST_GAS` goes un-dispatched is **not identified here.** In a
pure LP, capacity with `mc` strictly below its own zone's dual and below its
bound should run, so the gap points at something the comparison does not model.
Three candidates are named, none adjudicable from committed artifacts:

1. **The armed `nyiso_zonal_loss_surface`** (nyiso-159 keeper) enters the energy
   balance as receiving-side loss fractions, so the correct test may be
   `mc ≤ δ_z × price_z` rather than `mc ≤ price_z`. **Bounded: NYISO marginal
   loss deviations are a few percent and cannot explain a 25–48 % gap**, but
   they are not zero.
2. **Any post-solve transform between the LP dual and the `price` column** of
   `hourly/system_<year>.parquet`.
3. **A capacity-basis mismatch** between `class_hourly`'s `mw` aggregate and the
   per-bin `pmax × availability` reconstructed here.

**The instrument that would settle it is per-generator model dispatch, which is
in no keeper artifact** — the standing nyiso-172 §2.5 / nyiso-173 limit, now
binding for the third consecutive session. A successor should treat *lifting
that limit* as the prerequisite, not open a lever against the un-dispatched MW
until one of the three above is ruled out.

---

## 7. The decomposition — what the session actually delivers

The chartered question was *what moves the class's offer position between
years*. The honest answer is that **for the 2025 top decile, the offer position
is the smaller half of the story**, and the numbers to see it were not available
until the LP's own offer stack was reconstructed.

2025 top decile, mean actual price \$176.25:

| quantity | MW | reading |
|---|---|---|
| measured CAMPD fleet | **2,597** | what the market ran |
| in the money at the **ACTUAL** price | **2,313** | what the model's offer would clear at the real price |
| in the money at the **MODEL'S OWN** price | **1,592** | what its offer clears at the price it forms |
| model dispatch | **1,442** | what it ran |

| term | MW | share of the 1,155 MW gap |
|---|---|---|
| model price below actual (2,313 → 1,592) | 721 | **62.4 %** |
| offer position proper (2,597 → 2,313) | 284 | **24.6 %** |
| un-dispatched at its own signal (1,592 → 1,442) | 150 | **13.0 %** |

**This is an ACCOUNTING decomposition at a fixed offer, not a causal one** —
raising the model's price would change dispatch, which would change the price,
and the three terms are not independent interventions. Stated that way it still
carries the session's conclusion: **the dominant term is the model's own 2025
price level, which is C3a-2025 (−11.2 %), which is owner-court**
(`DECISION-CARD-nyiso148-2025-level-remainder`, Q1 pending) **and which this
session is instructed not to open, and did not.** The `ST_GAS` C1-2023 lane and
the C3a-2025 lane are the **same object seen from two ends**, and that
identification is new.

### 7.1 G4 — the between-year channels, with its own bar's defect disclosed

| channel | contribution to ΔITM(2023→2025) | "share" |
|---|---|---|
| FUEL | **−740.8 MW** | −4.06 |
| PRICE | **+1,163.1 MW** | +6.37 |
| AVAILABILITY | **−239.9 MW** | −1.31 |
| **net** | **+182 MW** | 1.000 |

Band heat-rate and VOM drift are **exactly 0.0**, so the fourth channel is
confirmed structurally constant and the three-channel decomposition closes
(PREREG §7.3's `INVALID` branch does not fire).

**The pre-registered verdict reads `CARRIER IDENTIFIED` / `PRICE`, and the label
is an artifact.** The shares sum to 1.000 as a decomposition must, but the net
delta (+182 MW) is small against the channel magnitudes (240–1,163 MW), so the
`≥ 0.60` bar is satisfied by a near-cancellation rather than by one channel
dominating; the probe flags this in `share_denominator_is_small`. **The MW
contributions are the honest output**, and they say the between-year mover is a
**large delivered-fuel headwind** — gas ran \$3.40 → \$11.76/MMBtu in the top
decile — **partly offset by a larger price tailwind.** That is a real answer to
the chartered question, and it is consistent with §7: the fuel term moved
against steam and the model's price did not move up enough to compensate.

---

## 8. Honest expected value

**What is delivered.** All three of the brief's named starting points are closed
on measurement, for zero solves, on bars fixed before they were measured — one
of them (G2) by showing the armed mechanism already does the job, which is rule
19 working as intended rather than a null result. The offer-position type
handed forward by nyiso-178 is itself **refuted**, on an instrument checked four
independent ways, including one check (R3) that would have manufactured the
verdict had it gone the other way and was resolved structurally rather than by
estimate. Seven construction defects were caught and disclosed before they could
affect a conclusion — four by code reading before the probe was committed, three
by the probe's own output before the finding was written — and in every case the
instrument was replaced rather than the bar moved. **The decomposition in §7 is
the substantive new result:** it identifies the `ST_GAS` C1 lane and the
C3a-2025 lane as one object, and it sizes the offer-position component of the
2025 top-decile deficit at 25 %, which is the number that tells a successor not
to spend a solve there.

**What is NOT delivered, stated without softening.** **No keeper, no candidate,
no run, no repair.** C1-2023 `ST_GAS` is exactly where nyiso-177 and nyiso-178
left it: named, sized at +3.86 TWh, and open. Nothing here reduces it by a
single MWh. The §6.1 question — *why* 3.8–9.1 TWh/yr of in-the-money steam goes
un-dispatched — is **bounded but not answered**, and it is the largest loose
thread this lane now carries; a reader should not mistake "the offer does not
govern" for "we know what does". The §7 decomposition is an **accounting**
identity, not a causal one, and its dominant term routes into an owner-court
decision this session has no standing to resolve, so the practical effect is
that **the `ST_GAS` lane is blocked pending Q1 of
`DECISION-CARD-nyiso148-2025-level-remainder`** — that is a real constraint on
the next session, not a hand-off with work in it. The `peak` 4.20 remains
un-grounded, as it was. The missing rung (nyiso-177 §7.2 / nyiso-178 §9.2) is
**still unspent**.

---

## 9. Handed forward

1. **THE `ST_GAS` LANE IS BLOCKED ON C3a-2025.** §7 shows 62 % of the 2025
   top-decile deficit is the model's own price level. Do not open an `ST_GAS`
   offer lever expecting to move C1 until Q1 of
   `DECISION-CARD-nyiso148-2025-level-remainder` is answered.
2. **THE NEW OBJECT: un-dispatched in-the-money `ST_GAS`**, 3.84 / 9.09 /
   3.99 TWh a year, robust to R1/R2/R3. Three candidate explanations named in
   §6.1. **Prerequisite: per-generator model dispatch**, absent from every
   keeper artifact (nyiso-172 §2.5), now binding for a third session — lifting
   that limit is worth more than any lever currently queued.
3. **CLOSED (a) — `gas_st_committed_hr_mult` / the caiso-239 transfer.**
   Structurally unreachable (G0). NYISO's measured 1.104 is already registered
   as `phys_committed`; `st_gas_committed_measured_bypass` reaches only
   `ST_GAS_PEAKER_PLANTS`, of which NYISO has none. DO-NOT-REDO absent a NYISO
   keeper that leaves the CAMPD path.
4. **CLOSED (b) — the downstate gas basis + `dual_fuel_switching` in the dear
   hours.** The armed cap reaches 0.834 of the class and relieves
   \$2.371/MMBtu in 2025's top decile (rule 19). Re-open condition in §4.
5. **CLOSED (c) — the `peak` 4.20 as this signature's carrier.** `PEAK-EXONERATED`
   on both legs. It stays un-grounded; grounding it needs a new measured NYISO
   artifact (there is no peak column in
   `nyiso_campd_marginal_hr_summary.csv`), not a sweep.
6. **A STANDING INSTRUMENT CONDITION, newly recorded.** Every in-the-money
   figure in this finding is valid **because** `gas_st_startup_cost = False`
   (§2, R3). A keeper that arms it must add `compute_monthly_markup` to the
   reconstruction before reusing these probes.
7. **UNCHANGED and not opened:** C3c (no lever, SUPPORTING tier, not lone);
   C3a-2025 (owner-court); the measured-availability-input family, the merit
   guard and an `ST_GAS` duty curve (nyiso-178 DO-NOT-REDO);
   `gas_st_startup_cost` (nyiso-172, two refusals); the missing rung.

---

## 10. Governance

* **Rule 1 `[R-STRUCT]`** — no residual was consulted in choosing what to
  measure; every residual-adjacent quantity held at the start is disclosed in
  PREREG §0.1 as inherited from the brief. No mechanism adopted or rejected on
  whether it moved a fit.
* **Rule 13 `[R-MEASURED]`** — nothing pinned to actuals. The actual RT LBMP and
  the CAMPD fleet are comparison bases only, never inputs.
* **Rule 14 `[R-ACCURATE]`** — the one measured-for-estimate substitution the
  brief proposed was tested and found **structurally unavailable** (§3), not
  declined on fit.
* **Rule 19 `[R-ONE-MECH]`** — G2 is this rule executed: the armed channel was
  enumerated and measured before anything new was proposed, and it closed the
  line.
* **Rules 21 `[R-DOF]` / 23 `[R-FROZEN-DERIVE]`** — **zero parameters touched.**
  `THERMAL_AVAILABILITY`, `MERIT_OOM_FRAC`, `MERIT_RCC_PCTL`, every offer band
  and every hr-mult were READ and never written or swept. No artifact
  re-derived. G3's pre-declared refusal to choose a `peak` value from the
  residual held.
* **Rule 22 `[R-HOLDOUT]`** — every year read is 2023 / 2024 / 2025. NYISO is
  absent from both `complete` and `final`; **no marker was requested**; the
  holdout spend freeze is untouched.
* **Rule 15** — **no solve ran, so nothing is registered on the dashboard.** By
  design (S1/S2/S3), not omission.
* **Rule 24 `[R-REGISTRY]`** — no new tunable. §3 explicitly declines to add a
  NYISO entry to `ST_GAS_COMMITTED_MEASURED_HR_MULT_BY_ISO` because it would be
  unreachable.
* **Rule 25 `[R-ISO-SCOPE]`** — NYISO only. No other ISO's artifacts read or
  written; only the NYISO matrix shard edited. The CAISO 1.683 was read as a
  *derivation pattern* and its value transferred nowhere.
* **Rule 27 `[R-PUSH]`** — no existing file ≥300 lines rewritten; the two new
  probes are additive.
* **Rule 28 `[R-MECH-MATRIX]`** — five NYISO cells annotated, **no verdict moves
  and no field changed** (§11).

## 11. Matrix (rule 28 b)

Five NYISO cells annotated; **every verdict unchanged**, no field touched.
`offer_curve_by_group` stays **`K`**, `dual_fuel_switching` stays **`K`**,
`zonal_gas_basis` stays **`K`**, `gas_hub_basis_overlay` stays **`K`**,
`st_gas_committed_measured_bypass` stays **`.`**. Guard passes
(`scripts/check_mechanism_matrix.py`), shard passes `node --check`.

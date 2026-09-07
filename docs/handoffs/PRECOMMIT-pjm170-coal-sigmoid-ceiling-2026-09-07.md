# PRECOMMIT — pjm-170: the PJM bituminous coal-sigmoid CEILING

**Session** pjm-170 · **ISO** PJM · **Branch** `claude/pjm-coal-sigmoid-ceiling-a97so9`
**Written** 2026-09-07, **before** any build of the arm and before any solve
(rule 29 `[R-SCREEN]`; the two things that preceded it are recorded in §0).
**Keeper (unchanged by this card)** `2026-08-15-pjm-162-inputclock`.
**Control** `results/calibration/pjm169_tp2022_2021_f2arm`, year 2022 — committed,
F2-armed, G-CTRL **form 4**, zero control LP (§6).

---

## 0. What was done BEFORE this document, and why that is not a violation

Two things preceded this file, both ordered by the card itself, neither a build of
the arm and neither a solve:

1. **The rule-23 reconciliation of the two coal-sigmoid tables** (§3). The card's
   DO item 4 says the rule-23 question "must be answered IN the precommit" and
   orders the two tables "reconcile[d] … before proposing anything". Answering it
   required running `scripts/data/derive_coal_sigmoid.py --iso PJM`, which reads
   source data (EIA Annual Coal Report f.o.b., BLS PPI, EIA MER heat content, the
   delivery-mode commodity share, the EIA-923 gas trough, the model fleet) and
   writes the provenance artifact. It reads **no price, no actual and no
   residual**. The artifact it overwrote,
   `data/raw/_processed-legacy/coal_sigmoid_params.csv`, was **restored to its
   committed bytes immediately** (`git checkout --`; working tree clean, verified).
2. **The G-DRIFT code audit** (§6). Rule 29(b) requires it "recorded in the
   PRECOMMIT (or its addendum) before the arm is solved". It is a `git diff`
   classification; no build, no solve.

The **phase-0 census of the arm** (§7) and the **screen solve** (§8) both come
after this document, and the gates in §5 are fixed here, before either.

---

## 1. The object, and the defect claimed

**Object.** One number: the `ceil` asymptote of PJM's bituminous gas-keyed coal
passthrough sigmoid — `COAL_SIGMOID_DEFAULTS[("PJM", "bituminous")]["ceil"]`,
live value **1.32**. Nothing else. The passthrough multiplies a coal tranche's
**fuel term**:

```
passthrough(g) = floor + (ceil − floor) / (1 + exp(−gas_slope · (g − gas_mid)))
```

resolved for the keeper (`fuel/trajectories.py::coal_sigmoid_params`, table entry
overlaid with the keeper's explicit fields) at

| param | value | source |
|---|---|---|
| `floor` | **0.65** | keeper explicit `coal_bit_passthrough_floor` (table literal 0.76 overridden) |
| `ceil` | **1.32** | table literal — **the object of this card** |
| `gas_mid` | **3.40** | table literal |
| `gas_slope` | **2.5** | table literal |

**The defect, stated structurally and without reference to any residual.**

- (a) **`ceil` > 1.0 marks the bid ABOVE the plant's own measured delivered fuel
  cost.** The keeper runs `coal_plant_monthly_pricing = True`, so the quantity the
  passthrough multiplies is the plant's **measured EIA-923 monthly delivered coal
  price**. A multiplier of 1.32 therefore offers a measured cost input marked up
  32 %. Rule 13 `[R-MEASURED]` forbids "rescaling an input so the model's *output*
  lands on the actuals"; the coal sigmoid is **not** in the rules 1/13 authorized
  price-tuning carve-out, which is the `offer_curve_by_group` band multipliers
  (`committed`/`econ_low`/`econ_high`/`peak`) and nothing else.
- (b) **Its recorded provenance is 100 % residual.** `COAL_SIGMOID_DEFAULTS`'s own
  inline comment for this entry: *"Ceiling 1.25 -> 1.32 (PJM run 16): trims the
  dear-gas-2025 BIT over-run (+6.3 -> +3.3 TWh)"*. There is no source-data
  statement behind 1.32 — the value **is** a volume residual, written down.
- (c) **The measured source-data derivation for this exact (ISO, supply) pair says
  1.0** — §3.
- (d) **2022 saturates it.** The realized ceiling leverage (§2) is 99.8 % in 2022
  against an in-window maximum of 60.7 %, so in 2022 the bituminous bid is
  essentially *entirely* the asymptote of (a)/(b).

**What is NOT claimed.** Not that the sigmoid mechanism is wrong (it is
owner-sanctioned rule-1 offer-curve scope: a take-or-pay / mine-mouth / rail coal
contract makes delivered fuel cost mostly fixed, so a plant bids toward its own
sunk cost rather than chasing the gas index). Not that `floor`, `gas_mid` or
`gas_slope` are right — §3.4 routes them, un-adjudicated, to a successor. Not
anything about ERCOT's `ceil` 1.50 / 1.35 entries, which are another ISO's lane
(rule 25 `[R-ISO-SCOPE]`).

**The counter-argument, stated fairly.** The table's docstring names a second
physical story under which `ceil > 1.0` is coherent: an **opportunity-cost bidding**
basin "price[s] toward the gas-CC breakeven to capture margin while staying in
merit". That story is real, and it is why ERCOT's PRB entries carry `ceil > 1.0`.
Two things about it, both recorded here before the solve:
(i) the docstring itself calls the inconsistent per-ISO application of the two
stories "part of the D-8 weak-identification finding" — i.e. the project has never
adjudicated which basin gets which, so the story cannot be *cited* as the
identification of 1.32; and (ii) even taken at face value, the story bounds the bid
by the **gas-CC's** cost, which rises with gas without limit, while `ceil` is a
**constant multiplier on coal's own cost** that saturates. A saturating constant is
the wrong functional form for that story, and 2022 is precisely the regime where the
difference bites. Building the gas-CC-breakeven cap the story actually describes
would be a **new mechanism** needing its own charter (rule 19 `[R-ONE-MECH]`); it is
not this card, and this card does not foreclose it.

---

## 2. Screen year — declared on FOOTPRINT, before any measurement of a residual

**The footprint metric, declared here.** For a change to `ceil` the direct effect is
exactly `Δpassthrough(t) = s(g_t) · Δceil`, where

```
s(g) = 1 / (1 + exp(−gas_slope · (g − gas_mid)))   ( = ∂passthrough/∂ceil )
```

so the year in which the mechanism's own measured footprint is largest is the year
with the largest mean `s` — the fraction of the ceiling's leverage the year
realizes. Because `passthrough = floor + (ceil − floor)·s` is **affine** in `s`,
mean `s` is recoverable exactly from pjm-169 §7.2's committed census
(`results/calibration/_pjm169_f4_census.json`) with no new build:
`s̄ = (passthrough_mean − 0.65) / (1.32 − 0.65)`.

| year | passthrough mean (pjm-169 §7.2) | **realized ceiling leverage `s̄`** | × in-window max | hours on ceiling (§7.2) |
|---|---|---|---|---|
| 2021 | 1.1205 | 0.7022 | 1.157× | 16.7 % |
| **2022** | **1.3188** | **0.9982** | **1.645×** | **91.5 %** |
| 2023 | 0.9166 | 0.3979 | 0.656× | 0.0 % |
| 2024 | 0.8140 | 0.2448 | 0.403× | 0.0 % |
| 2025 | 1.0565 | **0.6067** (in-window max) | 1.000× | 8.5 % |

**SCREEN YEAR = 2022**, the largest measured footprint, 1.645× the in-window
maximum. It is the same year the "hours on ceiling" statistic names, so the metric
change does not move the choice — recorded so that nobody can read the metric as
having been picked to reach a year.

**This CORRECTS the card's own framing, and the correction is against my interest.**
The handoff says ~92 % of 2022's coal bid is set by "a parameter the training window
touches essentially never". On the leverage metric that is **false**: the ceiling
carries 39.8 % / 24.5 % / 60.7 % of its full leverage in 2023 / 2024 / 2025, mean
41.6 %. The ceiling is **materially identified in-window**; what 2022 does is
*saturate* it. Two consequences, both stated before the solve:
- the extrapolation claim is weaker than the card asserts, and the case for this
  card rests on §1(a)–(c) — provenance and admissibility — not on §1(d); and
- a change to `ceil` **will move 2023–2025 materially** (≈ 0.32 × 0.40/0.24/0.61 of
  the bituminous fuel term). The screen cannot see that, is not asked to, and
  **cannot promote anything** (§5).

Nothing in this section reads a price, an actual, or a residual.

---

## 3. Rule 23 `[R-FROZEN-DERIVE]` — the two tables, reconciled

Rule 23 freezes measured-behaviour parameters against residuals: they "re-derive
only when their *source data* updates — never because a residual moved", and "re-
derivation commits must cite the data change". `COAL_SIGMOID_DEFAULTS` is
explicitly residual-tuned, so this card owes a **source-data statement**. Here it is.

### 3.1 The two tables

**Table A — the live registry literal** (`config/scenarios.py::COAL_SIGMOID_DEFAULTS`),
what the solve reads, overlaid with the keeper's explicit fields:

```
("PJM","bituminous") = {floor 0.76→0.65 (keeper), ceil 1.32, gas_mid 3.40, gas_slope 2.5}
```

Provenance, from the entry's own inline comment: ceiling `1.25 → 1.32` at **PJM run
16** to trim a 2025 volume over-run; floor `0.82 → 0.80` at run 19, `0.80 → 0.76` on
2026-06-17, and `0.76 → 0.65` by the keeper's explicit override. **Every recorded
move of every parameter is a residual move.** No source data is cited anywhere.

**Table B — the source-data derivation** (`scripts/data/derive_coal_sigmoid.py`),
run 2026-09-07 at `--iso PJM`, output restored (§0):

```
PJM bituminous : n_priced 29, fob $3.661/MMBtu, deliv $4.307/MMBtu, hr_coal 11.02
                 → {floor 0.50, ceil 1.0, gas_mid 7.08, gas_slope 1.0}
                 regions ESC,IN,KY,MD,OH,PA,VA,WV
PJM subbituminous: {floor 0.77, ceil 1.0, gas_mid 3.715, gas_slope 2.5}  (not this card)
```

Inputs: EIA Annual Coal Report region f.o.b.-mine price + BLS coal-mining PPI
(the **#1803 intake**, `data/raw/coal-prices/`,
`docs/handoffs/coal-price-data-intake-2026-07.md`), EIA MER A5 heat content,
`COAL_DELIVERY_COMMODITY_SHARE`, `COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU`, EIA Table-8
representative heat rates, and the model's own fleet capacities. **No ISO
price/volume residual anywhere in the path** — the script's own honesty gate.

### 3.2 The committed provenance artifact has NO PJM row — and that is the finding

`data/raw/_processed-legacy/coal_sigmoid_params.csv` at HEAD carries **8 rows**:
ERCOT prb / prb_follower / lignite, MISO prb / prb_follower / bituminous / lignite,
NEISO bituminous. **PJM is absent.** The derive script's docstring says why: *"The
MISO rows are transcribed into `COAL_SIGMOID_DEFAULTS` as the registry-resident
literals (rule 24); other ISOs' rows are delivered but their live literals are left
unchanged (their re-solves are separate owner lanes)."*

So the position is: **the source-data re-derivation trigger already fired on
2026-07-09** — the #1803 intake — **and PJM's transcription was deferred to the PJM
lane, never refused.** MISO's bituminous row was transcribed *wholesale* at that
time and is live today at exactly the derived `{0.532, 1.0, 4.115, 1.092}`. This
card is that deferred lane.

**The rule-23 source-data statement, stated once:**

> The re-derivation is keyed to the **#1803 EIA Annual Coal Report f.o.b. + BLS PPI
> intake**, the same intake that re-grounded MISO's rows on 2026-07-09, applied now
> to the PJM (ISO, supply) pair whose transcription that lane explicitly deferred.
> It is **not** keyed to the 2022 residual, to any year's price error, or to any
> volume error. The 2022 residual is not read by the derivation, by the candidate
> value, or by any gate in §5.

### 3.3 The `ceil` rule is level-independent — which is why it, and only it, moves

Table B's four parameters do **not** rest on the same evidence:

- **`ceil` = 1.0** is a *structural* statement with no level in it: coal's delivered
  cost is not gas-indexed, so at dear gas the bid is its full measured delivered
  cost and never a markup past it. It is the same rule for every row of the
  committed artifact — ERCOT, MISO and NEISO alike all read `ceil 1.0` there.
  Its truth does not depend on what `deliv_mmbtu` is.
- **`floor` / `gas_mid` / `gas_slope`** are *level* parameters. `gas_mid = deliv ×
  HR_coal / HR_cc` and `floor = gas_min / gas_mid` both scale with the script's
  **reconstructed** delivered price ($4.307/MMBtu, lifted from an annual region
  f.o.b. by a commodity share). The model does not use that reconstruction: with
  `coal_plant_monthly_pricing = True` it prices each plant at its **measured
  EIA-923 monthly delivered cost**. If the two disagree, transcribing `gas_mid`
  would import a crossover computed against a price the LP never sees — a rule 14
  `[R-ACCURATE]` misalignment, not an accuracy gain.

**Declared here, before the measurement:** §7 phase 0 measures the model's own
capacity-weighted delivered coal $/MMBtu for the PJM bituminous fleet, per year,
and reports it against the script's $4.307. **The measurement is reported, and it
changes nothing about this card's arm either way** — the arm is `ceil` only,
because (i) `ceil`'s derivation is level-independent, (ii) rule 29's screen isolates
**one** declared delta, and (iii) the card's object is the ceiling. The
reconciliation's purpose is to say honestly whether the level parameters are
*eligible* for a successor card, not to select this card's value.

### 3.4 Routed, not absorbed

`floor` 0.65-vs-0.50, `gas_mid` 3.40-vs-7.08 and `gas_slope` 2.5-vs-1.0 are
**open, un-adjudicated, and out of scope here**. Their combined effect would be
large (Table B's curve reads ≈0.51/0.52 passthrough in every training year against
the live 0.81–1.06) and it is a different mechanism-in-kind — a level re-grounding,
not a ceiling admissibility question. They get their own PRECOMMIT, their own
phase 0 and their own screen, or they stay as they are. **This card does not touch
them and does not claim they are right.**

---

## 4. THE DISPLACEMENT-AWARE FOOTPRINT GATE (card DO item 2)

### 4.1 Why pjm-169's S4 could not do its job

pjm-169's S4 read *"every non-gas class < 1.0 % annual energy"* and failed the F4
arm on `COAL_BIT +3.28 %`. That document's own §9.2 diagnosed it: raising every gas
tranche's offer by $10.57/MWh **must** re-allocate through the merit order, and the
next unit up in PJM is coal — so the class move it caught was ordinary displacement,
"arguably the mechanism working, not a confound". The verdict stood, correctly,
because the gate was pre-registered. **The gate's defect is that it measured where
the DISPATCH MOVED, when the question it was asked is where the MECHANISM ACTS.**
Those are different objects: the first is the LP's business and re-allocates by
construction; the second is a property of the offer array and is fully observable
before any LP runs.

**pjm-169's F4 verdict is not reopened by this document.** F4 is REJECTED on its own
pre-registered gate and its matrix cell stays `R`. What is re-specified here is a
gate for **this** arm, in **this** PRECOMMIT, before **this** solve — the route
pjm-169 §9.2 named.

### 4.2 The specification

Two populations, both defined **before** the solve and both determined by the
mechanism's own arithmetic, not by an outcome:

- **DIRECT rows** — the LP rows whose own `mc` this mechanism changes. For a
  bituminous-`ceil` change: every coal tranche whose `coal_supply` tag is
  `bituminous` and whose supply passthrough is non-zero (i.e. non-`mustrun`).
  Predicted from the offer path; **enumerated in §7 before the solve**.
- **INDIRECT rows** — every other row in the LP. Free to move.

| limb | what it bounds | measured on | bound |
|---|---|---|---|
| **A — DIRECT PURITY** | where the mechanism ACTS | offer arrays, **zero LP** | the set of rows with `Δmc ≠ 0` equals **exactly** the predicted DIRECT set, in every hour; **zero** unpredicted rows |
| **B — RE-ALLOCATION, not creation** | that the dispatch response is a transfer | LP | `|Δ(total served energy)| ≤ 0.5 %` of annual load **and** `|Δ(slack + dump)| ≤ 0.1 %` of annual load |
| **C — DIRECT-CLASS SIGN** | that the direct class answers its own price | LP | the DIRECT rows' energy moves **UP** (their bid fell), by **≤ the zero-LP headroom bound** (§7): `Σ_t (pmax·availability − control dispatch)` over the DIRECT rows |

**Limb B places NO bound of any kind on any INDIRECT class's energy change.** A
gas-CC class shedding many TWh to coal is merit order doing its job and is
**reported, never gated**. That single sentence is the correction to S4.

**Why this is strictly stronger, not merely looser.** Limb A is a *zero-tolerance*
test on a population enumerated in advance — it catches a mechanism reaching a row
it never claimed (a mis-tagged supply, a `mustrun` band that should have passed 0.0,
a subbituminous or waste-coal plant swept in by a stem collision), which S4's energy
threshold could not see at all: a confound confined to a class that also displaces
is invisible to a class-energy test and fatal to limb A. Limb C catches the true
confound signature — a direct class moving **against** its own price change. What is
given up is only the ability to fail an arm for the LP re-allocating correctly,
which is not a capability worth having.

---

## 5. GATES — fixed here, before the solve. STOP GATE ONLY.

| # | gate | LP? | PASS condition |
|---|---|---|---|
| **S1** | identity of the resolution | no | arm resolves `{floor 0.65, ceil 1.00, gas_mid 3.40, gas_slope 2.5}`; control `{0.65, 1.32, 3.40, 2.5}`; **only `ceil` differs**, every other field equal to 1e-12 |
| **S2** | the identity it asserts | no | hourly `Δpassthrough(t) = s(g_t)·(1.00 − 1.32)` to ≤1e-12 against an independent evaluation of the logistic; `Δ → 0` as `g → −∞` |
| **S3** | direct `mc` delta — EXACT | no | measured mean `Δmc` over the DIRECT rows equals the §7 prediction to **≤1e-6 $/MWh**, and its sign is **negative**. (Both sides are computable at zero LP, so this is an identity check, not a bracket.) |
| **S4-A** | footprint — DIRECT PURITY | no | §4.2 limb A: zero unpredicted rows |
| **S4-B** | footprint — RE-ALLOCATION | yes | §4.2 limb B |
| **S4-C** | footprint — DIRECT-CLASS SIGN | yes | §4.2 limb C |
| **S5** | no non-target load-bearing flip | yes | no criterion that PASSes on the control 2022 FAILs on the arm 2022 |

**KILL RULE.** Any gate FAILs ⇒ the arm is dead, the remaining years are **never
spent**, nothing is promoted, and the failure is the session's reported result.

**S1–S4-A are zero-LP and run FIRST** (rule 29 clause 0). If any of them fails, **no
LP is spent at all**.

**The screen may kill; it may NEVER promote.** It contributes to no determination.
Clearing every gate licenses exactly one thing: proposing the full-span
`--year 2023 2024 2025` step as a separate act, on its own evidence.

**NOT gates, and never pass conditions — reported at full magnitude in the RESULT:**
C1 class errors (`CC_REGULAR`, `COAL_BIT`, every class), C3a `price_mean`, C3b
`price_shape`/NRMSE, C3c, the fuelmix error, the 2022 determination, the P0/P1
objectives, and any comparison of any of these to 2021 or to the training years.
**No gate above reads the target residual**, and no gate reads whether 2022 got
better. Saying so here, before the solve, is what stops it becoming one
(rule 1 `[R-STRUCT]`).

**Anti-sweep clause (rules 1(c)/13/23).** The candidate `ceil` is **1.0**, set by
the rule declared in §3 — the value `derive_coal_sigmoid.py` produces for
`("PJM","bituminous")` from the #1803 source data, the same rule that already set
`("MISO","bituminous")` live at `ceil 1.0` and that reads 1.0 on every row of the
committed provenance artifact. **One value. Every year. Declared before the solve.
Never swept.** No second value is screened, and if 1.0 fails a gate the answer is
that the arm is dead — not that another value is tried.

---

## 6. G-CTRL and G-DRIFT — zero control LP

**G-CTRL form 4.** The control is `results/calibration/pjm169_tp2022_2021_f2arm`
year 2022 — committed, F2-armed, the keeper recipe replayed on the 2022 touchpoint.
Rule 29(b): "stop doing control solves … just use the last keeper as the control."
**No control LP is spent.**

**G-DRIFT — the code-level drift audit**, discharged by classification, not by a
solve. Control `git.sha` = `f36cee6e` (an ancestor of HEAD `5930e533`). Audited:
`git diff f36cee6e HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source
data/raw/reference` — **55 files, +3,639 / −59**. Every hunk classifies **INERT**
for a PJM backcast:

| class | files | why INERT |
|---|---|---|
| **SPP registration** (lanes SPP-11/12/14/20/32/40) | `campd.py`, `fleet/models.py`, `zone_assignment.py`, `eia930/{frames,demand,envelopes,__init__}.py`, `renewables.py`, `paths.py`, `fuel/basis/meanzero.py`, `fuel/__init__.py`, `transmission_expansion.py`, `interchange/{spec,registry}.py`, `neighbor_price.py`, `backcast_config.py` (`_SPP_OFFER_CURVE`), `solve_surface.py`, `scripts/lib/{confirmed_retirements,load_forecast,nuclear_license_status,transmission_expansion}/`, all `data/raw` additions | another ISO's branch. **Verified additive, not just asserted**: `interchange/spec.py` has **zero** deleted lines; `TRANSMISSION_BASE_STATIC_VINTAGE` PJM stays 2024 (SPP 2026 appended); `_UNCURTAILED_FALLBACK_ISOS` and `_WIND_ZONE_SHAPE_ISOS` gain `"SPP"` only and never contained PJM; `actual_lmp.json` and `calibration_reference.json` **PJM subtrees hash-identical** (`b4edaf49c24e619c`, `a49af0099d47a1b0`) with only an `SPP` key and a `generated` stamp moving |
| **ERCOT-only** | `model/reserves/spec.py` (`_ercot_multiproduct_design`), `results/scarcity.py` (`ercot_as_measured_requirement_mw`), `fuel/basis/ercot.py`, `backcast_config.py` ORDC vintage, `run_calibration.py` GTC/WTX blocks + `_renewable_bound_is_delivered_pinned` | every hunk inside an `iso == "ERCOT"` guard or an ERCOT-only function; the ORDC block is byte-identical for 2022-2025 and for every non-ERCOT ISO |
| **MISO-only** | `interchange/miso.py` (`neighbour_hourly_spp`, default `False`), `run_calibration.py` MISO seam validation | MISO-gated |
| **NYISO-only, default-off** | `fleet/arrays.py` `_reconciled_summer_ratios` / `cc_summer_derate_reconciled_basis` | GATED default-off, absent from the keeper recipe; returns `{}` with no table |
| **PJM forecast-only** | `iso_configs.py::_pjm_config` `retirement_sector_gate: True` (capx D78-ARM, Q56); `scenarios.py`, `constants.py`, `capacity_market.py` new fields/tables (**pure additions, zero deleted lines**) | `scenarios.py:17531` coerces `retirement_sector_gate` to the dataclass default when `mode == "backcast"` — read, not taken on trust. Capacity evolution is never entered by a backcast |

**Machine-checked corroboration on the registry-value surface.** The capx D79
solve-surface fingerprint, projected to PJM, is **identical** at both revisions:

```
control run_config.solve_surface : fingerprint 0f749d17202c32d9, rows 211, moved {}, epochs [], git_sha f36cee6e
HEAD  surface_stamp("PJM")        : fingerprint 0f749d17202c32d9, rows 211, moved {}, epochs [], git_sha 5930e533
```

covering `constants`, `capacity_market`, `fuel_trajectories`, `ercot_envelopes`,
`plant_taxonomy`, `entry_config` and `offer_curve_base.generic` — the three largest
diffs in the table above among them.

**ALL HUNKS INERT ⇒ G-CTRL form 4 is valid and the committed control stands.** No
LIVE hunk, so no control solve is earned.

---

## 7. Phase 0 — the zero-LP census, declared before it runs

Probe: `scripts/probes/_pjm170_ceil_footprint.py` (new). Artifact:
`results/calibration/_pjm170_ceil_census.json`. It builds the control recipe's
resolved config through `run_calibration.run_year(..., fleet_only=True)` — the same
entry the solve uses — for each of 2021–2025, and reports:

1. **Resolution** — the resolved sigmoid params under control and arm (feeds **S1**).
2. **Leverage** — hourly `s(g_t)`, mean / p50 / fraction ≥ 0.99, per year
   (corroborates §2 against the config actually built, rather than against
   pjm-169's committed census alone).
3. **The DIRECT row set** — every LP row whose `mc` differs between the control and
   arm offer arrays (`mc_base` from the `fleet_only` exit, the assembled P0
   objective the LP is handed), and every row predicted to be in it. Feeds
   **S4-A** and enumerates the population §4.2 needs.
4. **The S3 prediction** — mean `Δmc` over the DIRECT rows, computed from
   `s(g_t) · (1.00 − 1.32) ·` each unit's own delivered fuel $/MMBtu × heat rate.
   Recorded **before** the solve; **S3 then requires the measured offer-array delta
   to equal it to ≤1e-6 $/MWh.**
5. **The headroom bound for S4-C** — `Σ_t (pmax · availability − control dispatch)`
   over the DIRECT rows, from the control bundle's committed
   `hourly/class_band_hourly_2022.parquet`.
6. **The §3.3 reconciliation measurement** — the model's own capacity-weighted
   delivered coal $/MMBtu for the PJM bituminous fleet, per year, against
   `derive_coal_sigmoid.py`'s reconstructed $4.307. **Reported; selects nothing in
   this card** (§3.3).

No price, no actual, no residual is read by the probe.

---

## 8. The screen invocation

```
.venv/bin/python scripts/replay_keeper.py \
    results/calibration/pjm169_tp2022_2021_f2arm \
    --out-dir results/calibration/pjm170_screen2022_ceil10 \
    --years 2022 --holdout-authorized \
    --set coal_bit_passthrough_ceil=1.0 \
    --note "pjm-170 SCREEN: single delta coal_bit_passthrough_ceil 1.32 -> 1.00"
```

**One declared delta.** F2 is armed on **both** sides by construction (the control
bundle is itself F2-armed), so F2 and this card are never confounded — the same
ordering device pjm-169 §8 used.

**Rule 22 authorization, checked at launch and re-checked at registration.** 2022 is
**validation** tier. PJM holds the `complete` marker
(`frontend/data/backcast/calibration-complete.json`, declared 2026-07-31, keyed to
keeper `2026-08-15-pjm-162-inputclock`). The holdout freeze is **tier-scoped to
`locked_test`** and explicitly does **not** cover 2020–2022. `--holdout-authorized`
is passed. **The screen bundle is never registered** (rule 29 clause 2), so the
registration marker gate is not reached at all.

**Rule 29(c) — DELETE BEFORE MERGE.** `results/calibration/pjm170_screen2022_ceil10`
is **deleted before this branch's PR merges**. This document and the session's
FINDING carry **every number this session will ever cite** from it. Git history is
the record for the bytes; an unregistered bundle reaching `main` is a parity-gate
RED, and `KEEP_REQUIRED_UNMAPPED_BUNDLES` is not the route.

**Box (pjm-169 §3.1a).** Swapfile armed with the keep-alive watchdog before the
solve; `MALLOC_ARENA_MAX=2`, single-threaded BLAS. One PJM invocation at a time
(rule 12).

---

## 9. What this card can and cannot end with

- **Every gate passes** → the arm survives the screen. The session reports that and
  **proposes** the full-span `--year 2023 2024 2025` step. It promotes nothing, and
  it states plainly that §2 predicts a material in-window move the screen never saw.
- **Any gate fails** → the arm is dead, 2023–2025 are never spent, and the failure
  is the result.
- **Either way**: the PJM matrix shard's `coal_passthrough_sigmoids` cell is
  re-stamped with this adjudication in this session (rule 32 duty b), the §3
  reconciliation is recorded whatever the verdict, and the §3.4 level parameters
  stay open and un-adjudicated.

---

## AMENDMENT 1 — limb A's prediction basis, sharpened. Written BEFORE any measurement exists.

**Status when written:** the phase-0 probe has not been run, the arm has not been
built, no `mc` delta of any kind exists, and no solve has happened. This amendment
is recorded, not silently applied (the pjm-169 §7.1 precedent).

**The defect in §4.2 limb A as first written.** It defines the predicted DIRECT set
as "every coal tranche whose `coal_supply` tag is `bituminous` and whose supply
passthrough is non-zero (i.e. non-`mustrun`)", and gates on that set being **exactly**
the moved set. The parenthetical is **wrong**, and reading
`data/fleet/legacy_bins.py::campd_tranche_fuel_frac` — not any measurement — shows it:

```
legacy_bins.py:449   if gen.unit_id.endswith("_sync"):    return 1.0
legacy_bins.py:451   if gen.unit_id.endswith("_mustrun"): ... return 0.0
```

`_sync` (the step-3a synchronization tranche, `coal_sync_srmc_tranche`, armed on this
keeper) returns a hard-coded **1.0** and never consults `passthrough_by_supply` at
all — by construction, because it bids its full SRMC while the contracted share is
carried by the fuel-free `_mustrun` band beside it. So a bituminous `_sync` row is
**tagged bituminous, carries a non-zero passthrough, and yet cannot move** when
`ceil` changes. Under the clause as first written it would land in
`predicted_not_moved` and fail the "equals exactly" reading of limb A — an arm killed
for the routing behaving exactly as its own code says it must. That is the same class
of gate mis-specification this card was chartered to correct (§4.1); catching it in
my own gate before the solve is the point of writing gates down first.

**The amendment.** Limb A's predicted DIRECT set is:

> every LP row whose generator carries the `coal_supply` tag `bituminous` **and**
> whose `unit_id` ends in neither `_mustrun` (fuel-free / take-or-pay sunk,
> `legacy_bins.py:451`) nor `_sync` (passthrough pinned at 1.0 by construction,
> `legacy_bins.py:449`).

Both exclusions are read off the routing code, cited by line, and neither is
selected by an outcome. **The gate is otherwise unchanged and reads exactly as
before:** the set of rows with `Δmc ≠ 0` must equal this set exactly — zero
unpredicted rows moving, and zero predicted rows failing to move.

**This makes the gate HARDER, not looser.** It removes two known-inert row families
from the prediction, so the surviving prediction is a tighter claim: every remaining
predicted row must now actually move, with no benign-non-mover left to absorb a
mistake. A mis-tagged plant, a supply-stem collision, or an overlay re-reading the
sigmoid elsewhere still fails it, exactly as before.

**Nothing else moves.** S1, S2, S3, S4-B, S4-C, S5, the kill rule, the candidate
value 1.0, the anti-sweep clause, the screen year and the control are all unchanged.

# FINDING (pjm-h2, part 2): it is NOT the coal sigmoid and NOT the CC offer bands —
# seven candidates killed at zero LP, and the one arm that survives is a MEASURED
# asymmetry in PJM's own offer registry

**Session** `pjm-h2` · **ISO** PJM · **Date** 2026-09-12 · **Base** `origin/main`
**ZERO LP.** The parent never solved and no shard was launched (rule 32 `[R-SHARD]` (a)).
**PJM keeper UNCHANGED: `2026-09-11-pjm-d4-4-gasoutage`, CALIBRATED, 8/8, zero caveats.**
Part 1: `docs/FINDING-pjm-h2-holdout-basis-2026-09-12.md` (the basis split).

---

## 1. THE TWO DIRECT QUESTIONS, ANSWERED WITH MEASUREMENT

### 1.1 "Do we have a coal sigmoid issue?" — **NO, and it is measurable three ways**

PJM bituminous runs a gas-keyed logistic `{floor 0.65, ceil 1.32, gas_mid 3.40, slope 2.5}`.
Its own code comment gives every parameter's provenance as a **2023-2025 volume residual**
("Ceiling 1.25 → 1.32 (PJM run 16): trims the dear-gas-2025 BIT over-run"; floor
0.82 → 0.80 → 0.76 → 0.65). That is a real rule-23 `[R-FROZEN-DERIVE]` wart. **It is
nonetheless not the C1 object**, measured on the keeper's own gas series:

| yr | gas $/MMBtu | **BIT passthrough** | hours pinned on an asymptote | model coal − 923 actual |
|---|---:|---:|---:|---:|
| **2020** | 1.94 | **0.674** | 0 % | **+23.1 TWh** |
| 2021 | 3.58 | 1.011 | 0 % | −0.5 |
| **2022** | 6.48 | **1.315** | **74.8 % at the CEILING** | +8.0 |
| 2023 | 2.49 | 0.757 | 0 % | +1.0 |
| 2024 | 2.39 | 0.753 | 0 % | −2.1 |
| 2025 | 3.75 | 0.965 | 8.5 % | +9.2 |

1. **2022 sits at MAXIMUM coal suppression (×1.315, 74.8 % of hours on the ceiling) and coal is
   still +8 TWh over.** The ceiling is not over-suppressing coal; lowering it makes the miss
   worse — which is exactly what pjm-170 measured (COAL_BIT +2.70 → +4.09 TWh).
2. **2020 sits at 0.674, statistically the same limb as the two PASSING years (0.753 / 0.757),
   and is +23.1 TWh over.** Same curve position, twelve times the error.
3. **2021's passthrough is 1.011 — the most cost-faithful value the curve takes in any year —
   and 2021's coal is the best-matched of the six (−0.5 TWh).** Its C1 failure is CC_REGULAR alone.

**A re-derivation makes 2020 worse, arithmetically.** The committed provenance artifact
`data/raw/_processed-legacy/coal_sigmoid_params.csv` already carries PJM's derived row —
`{floor 0.50, ceil 1.00, gas_mid 7.08, slope 1.0}`, delivered by `derive_coal_sigmoid.py` in
2026-07 and never transcribed (only MISO's rows were). Evaluated on the keeper's gas series it
gives passthrough **0.649 / 0.725 / 0.951 / 0.665 / 0.663 / 0.738** — **coal CHEAPER in every
year, most in the dear-gas years**, so it moves 2020 the wrong way and puts the 8/8 keeper's
2023/2024 coal at risk for a −0.09 passthrough shift. **Not proposed.** *(Its `gas_mid` also
rests on an ACR regional f.o.b. of $4.307/MMBtu where the model's own measured EIA-923 receipts
read $2.786 — a real rule-14/19 inconsistency, flagged by pjm-170 §2.1 and still open.)*

### 1.2 "Is it the CC_REGULAR offer curve?" — **NO: the object is ON-HOURS, not price position**

`pjm-h1` measured it today and I corroborate it: **CC_REGULAR is the only PJM class whose fleet
capacity factor does not track the meter** (cross-year r = **−0.183**, against COAL_BIT +0.912,
CT_PEAKER +0.896, ST_GAS +0.968, CC_CHP +0.775). The model runs PJM CC at **0.606-0.621 CF in
all six years** — a 1.5-point band — while the meter moves **5.8 points**. The split is
**on-hours**: model CC is online **+7.7 / +8.8 / +5.8 pp** too often in 2020-2022 against
**+4.6 / +4.8 / +3.7** in 2023-2025. A band multiplier moves a unit's *price position*; it does
not make a flat fleet responsive. **Tuning the CC bands here would be fitting a mechanism to a
residual** (rule 1 `[R-STRUCT]`).

### 1.3 "Market dynamics in those years?" — **YES, and it is a fleet-size × price-variance product**

PJM 2020-2022 carried **5-9 GW more coal** than 2023-2025 (model coal peak 37.3 / 40.6 / 36.7 GW
vs 31.3 / 32.8 / 31.4). Those years also had a far wider *realised* price distribution (COVID
demand collapse at $1.94 gas; the 2021 autumn gas run-up; 2022 at $6.48 with Winter Storm
Elliott). **The model's D-A diurnal price amplitude is 29.9-32.9 % of measured in EVERY year.**
A compressed price distribution produces flat dispatch; flat dispatch against a *big* coal fleet
is a large volume error, and against a *small* one it is not. That is why the same chronic
compression reads +23 TWh in 2020 and +1 TWh in 2023.

---

## 2. SEVEN CANDIDATES KILLED AT ZERO LP

Each is the obvious next lever and each would have cost a solve. Recorded so no successor spends one.

| # | candidate | cell | measured verdict |
|---|---|---|---|
| 1 | coal sigmoid **ceiling** | — | pjm-170 `R`; and §1.1 (2022 at max suppression, still over) |
| 2 | coal sigmoid **full re-derivation** | — | **KILLED HERE**: derived row moves coal CHEAPER in all six years (§1.1) |
| 3 | `gas_offer_margin_anchor_vintage` | `R` | pjm-169 S4 |
| 4 | `retiree_vintage_status_scope` | `U` | **KILLED HERE**: drops **7.5 MW** of PJM coal in *every* year (32-35 units, ~1.1 GW, gas-CT/biomass) — cannot be a 23 TWh object |
| 5 | partial derates / capability loss | `.` | **KILLED HERE for COAL** (pjm-h1 had killed it for CC): per-plant CEMS p99.5 capability is **flat across all six years** on every unit (e.g. 3944: 1937/1940/1934/1946/1941/1940 MW) |
| 6 | forcing / must-run | — | D-2: coal forced share **0.6-1.4 %** in 2020-2022 vs **4.0-4.1 %** in 2023-2024 — *least* where the surplus is largest |
| 7 | outage-extract coverage | — | **KILLED HERE**: PJM coal outage MW-days are flat — 20.4 / 18.4 / 18.5 GW-equiv in 2020-2022 vs 20.9 / 16.8 / 15.5 in 2023-2025; the bad years carry *more* detected outage |

**Instrument caveat on my CAMPD-basis numbers.** My CAMPD coal extraction sums ~12 % below the
bench's own `coal_cems` (2021: 147.3 vs 166.6 TWh), so the CAMPD *levels* in this session's
working notes are not quotable; the **shapes** (per-plant capability, per-year outage, decile
profile) are, and every gated number above is on the `classFull` / 923 basis the scorer uses.

---

## 3. THE ONE ARM THAT SURVIVES — a measured asymmetry inside PJM's own offer registry

**PJM's registered `offer_curve_by_group` carries a MEASURED physical basis for its GAS bands
and NONE for its COAL bands — and the measured coal row is committed and unused.**

`data/raw/reference/pjm_campd_marginal_hr_summary.csv` is the CAMPD marginal-heat-rate derive.
PJM's registered gas `phys_*` keys are that artifact, **byte for byte**:

| CC_REGULAR | registered | artifact column | value |
|---|---:|---|---:|
| `phys_committed` | **1.015** | `avg_committed_p50` | **1.015** |
| `phys_econ_low` | **0.87** | `marg_econ_low_p50` | **0.87** |
| `phys_econ_high` | **1.052** | `marg_econ_high_p50` | **1.052** |

The same artifact's **COAL** row reads `avg_committed_p50` **0.916**, `marg_econ_low_p50`
**0.803**, `marg_econ_high_p50` **0.809** — and **COAL_BIT's registered bands carry no `phys_*`
key at all**, so under `scenarios.py`'s own rule ("a band WITHOUT its `phys_*` key is neutral")
coal keeps the **fully fuel-scaled multiplicative markup** that `gas_offer_net_revenue_margin`
(PJM cell **`K`**, armed in the keeper at anchor 3.3483) exists to retire on gas.

**Why that is the mechanism and not the residual.** The multiplicative form's markup scales with
the fuel bill — the defect its own design doc names, "unidentified inside the homogeneous 2023–25
training gas window, rejected by the 2022 NEISO validation rotation". Coal's offer is keyed to
**gas** through the passthrough sigmoid, so coal's above-physical markup swings ×0.674 → ×1.315
across 2020-2022 while a real coal plant's start/no-load hurdle is a **$/MWh** quantity. PJM has
already accepted that argument for gas and holds the measurement for coal. **Rule 14
`[R-ACCURATE]`: prefer the measured input that exists.** Zero free parameters — every value is
read from the committed artifact and none can be chosen.

**STATUS — CORRECTED AFTER READING THE FIELD, AND IT MATTERS: this is a BUILD, not an arm.**
`coal_offer_net_revenue_margin` (cell `U`) as **implemented** is a different construction from the
route above: it is scoped to the CAMPD coal **`_mustrun` (min-load) tranche only**, and it requires
`coal_offer_margin_level` — "the measured RT curve bottom (60-Day SCED `Submitted TPO-Price1`,
cap-wtd p50)". That IS the ERCOT instrument PJM's masked DataMiner2 corpus cannot serve, so
**pjm-146's instrument block is correct for the field as it stands and the cell stays `U`.**

The `phys_*` route is therefore a **new gate** (rule 28(c): a new matrix row in the same PR), not
a flag to arm. What it inherits is the part that is *not* blocked: the identification instrument.
PJM's gas `phys_*` keys already come from `pjm_campd_marginal_hr_summary.csv`, that artifact
carries a COAL row, and the `offer_markup_hr` machinery
(`offer_curves.apply_gas_offer_margin`, `mc += markup_hr × (anchor − fuel)`) is generic. The
build is: register COAL `phys_*` from the artifact, resolve a coal anchor from the model's own
delivered-coal series, and gate the coal tranches into the existing seam under a rule-19
`[R-ONE-MECH]` **replacement** of the sigmoid's markup role.

### 3.1 What is still owed before any LP (rule 29 `[R-SCREEN]` clause 0)

0. **The build itself** — one new gate + a matrix row (rule 28(c)), with the COAL `phys_*` transcribed from the committed artifact and nothing chosen by hand.
1. **The pre-solve offer-array delta**, per band per year — `(mult − phys) × HR_base × (anchor −
   fuel(t))` on the real keeper fleet, with the sign and magnitude fixed in the PRECOMMIT before
   any solve. **This has NOT been computed and the arm must not reach a solve until it is.**
2. **The anchor's identification for coal** — the gas anchor is `_gas_series`'s training-window
   mean; coal's must be its own measured delivered series, and rule 19 `[R-ONE-MECH]` requires it
   to *replace* the sigmoid's role in setting the markup, never stack on it.
3. **The screen year, named on FOOTPRINT** — the largest `|mult − phys| × |anchor − fuel|` × coal
   energy, which on the §1.1 table is **2020** (the widest gap between the fitted multiplier and
   the measured physical basis), *not* the largest residual.

---

## 4. WHAT I ROUTE RATHER THAN OPEN

pjm-h1's surviving explanation — **price-distribution compression** — is corroborated here and
extended from CC to coal: the model's amplitude is ~30 % of measured in every year, and the two
classes it should pin are the two that miss. That lives in the **owner-declared-closed
pjm-142 price-formation frontier**. Re-opening it is an owner act, not a lane's. The arm in §3
is offered as the admissible alternative that does **not** require it.

## 5. RULES

Rule 29 `[R-SCREEN]` clause 0 (zero-LP phase 0 first; it killed four more candidates here).
Rule 28 `[R-MECH-MATRIX]` (a) (no `R`/`I`/`G` cell re-tested; §3's cell is `U`). Rule 1
`[R-STRUCT]` (no lever selected on the residual; §1.2 and §3 both state the structural basis).
Rule 30(c) (held-out years never downgrade PJM). Rule 31 `[R-RETAIN]` (nothing solved).
Rule 32 `[R-SHARD]` (a) (the parent never solved).

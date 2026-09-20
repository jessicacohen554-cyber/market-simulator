# PRECOMMIT — nwpp-44: the measured take-or-pay / regulated committed band, scoped by owner ruling

**Lane:** NWPP-44 · **Date:** 2026-09-20 · **Branch:** `claude/nwpp-44-coal-takeorpay-wm3ght`
**Base SHA (parent, pre-commit):** `5c0bec8bed4c7af73f81d7702a8cb6fb129d60d6`
**Keeper / control:** `2026-09-20-nwpp42-measured-coal-heat`, bundle `results/calibration/nwpp42_coalhr_span`, `git_sha b68673a99926a554d0a9e165f5bd06b890572c02`
**LP spent by this session: ZERO** (rule 32(a) `[R-SHARD]`). Every number below is zero-LP.

---

## 0. The one-paragraph version

NWPP-43 settled the structure and left ONE scoping question (its §7). The owner
ruled it on 2026-09-20: **Option B — the measured take-or-pay committed-band
discount applies to ALL regulated coal**, bituminous and PRB alike, so
`coal_prb_committed_dispatchable` is **NOT** armed and no rank carve-out is
applied. The owner separately directed that the contested prior art
(`coal_committed_takeorpay_sunk_fixed`, miso-96) be **answered in this PRECOMMIT
rather than ignored**; §3 answers it. This lane therefore arms exactly two
fields for NWPP in `backcast_config.py` — `coal_takeorpay_from_data` (already
present for MISO, extended by the same idiom) and
`coal_committed_takeorpay_regulated` (which `backcast_config` did not pass at
all). **Zero free parameters**: the discount is each plant's own measured
EIA-923 Schedule-5 contracted share and the scope is a published EIA-860
boolean. The G-DRIFT audit (§4) is clean at the row level, so rule 29(b) **form
4 is valid and no control solve is spent**. The offer delta is re-measured at
this lane's own base SHA (§5) and reproduces NWPP-43's row set and MW exactly.
§6 carries a sharper zero-LP prediction than NWPP-43 had, in the kill
condition's own currency — and it changes which limb this lane is actually at
risk on: **the overshoot limb is measurably out of reach in every year and
every coal class; the INERT limb is the live risk.** The kill condition is
carried **verbatim** from NWPP-43 and is not renegotiable after the fact (§7).

---

## 1. THE RULING, recorded before anything was measured against it

> **Owner, 2026-09-20, on PRECOMMIT-nwpp-43 §7 — Option B: all regulated coal
> (BIT + PRB).**

The question was whether to scope the committed-band discount to bituminous
only. It could not be settled from NWPP's data: the p25→median CF spread is
~9–20 pts in **both** ranks (BIT: Hunter 9.5, Huntington 15.5, North Valmy 7.1;
PRB: Colstrip 8.7, Wyodak 9.6, Hardin 14.0, Naughton 39.5). MISO measured PRB
committed bands cycling price-responsively even at regulated plants (miso-111),
but rule 28(d) keeps that verdict out of NWPP's cell.

**Why the ruling had to come from the owner and not from this lane.** Option A
is the option that removes the §6 overshoot risk and points the arm at the
deficit class. Selecting it *for that reason* is the fitted-mechanism selection
rule 1 `[R-STRUCT]` exists to forbid. The scope is fixed **ex ante**, by ruling,
and it is fixed to the option that is **harder** on this lane's own gate.

**What Option B is, structurally.** The measured contract share and the
published regulatory status are the whole story, with no rank carve-out layered
on top. A cost-of-service utility's coal offer is not scoped by what it burns;
it is scoped by who bears the cost.

---

## 2. What is armed, and what is not

| field | NWPP | every other ISO | why |
|---|---|---|---|
| `coal_takeorpay_from_data` | **True** | MISO True (unchanged), rest False | the share map; `campd_tranche_fuel_frac` needs it to carry the plant |
| `coal_committed_takeorpay_regulated` | **True** | False | the committed-band limb, scoped by EIA-860 `Regulatory Status == RE` |
| `coal_prb_committed_dispatchable` | **False** | False | **Option B**: no rank carve-out |
| `coal_committed_takeorpay_sunk_fixed` | False | False | would suppress the limb entirely — see §3 |
| `coal_bit_committed_takeorpay` / `_all` | False | False | superseded by the regulated scope (rule 19 `[R-ONE-MECH]`) |

Verified by construction at this lane's base SHA, all nine registered ISOs:

```
ERCOT  takeorpay=False committed_reg=False prb_disp=False
CAISO  takeorpay=False committed_reg=False prb_disp=False
PJM    takeorpay=False committed_reg=False prb_disp=False
MISO   takeorpay=True  committed_reg=False prb_disp=False   <- UNCHANGED
NYISO  takeorpay=False committed_reg=False prb_disp=False
NEISO  takeorpay=False committed_reg=False prb_disp=False
SPP    takeorpay=False committed_reg=False prb_disp=False
NWPP   takeorpay=True  committed_reg=True  prb_disp=False   <- this lane
SOCO   takeorpay=False committed_reg=False prb_disp=False
```

Rule 25 `[R-ISO-SCOPE]` is clean: nothing is transferred from MISO, no other
ISO's config moves, and every other ISO's keeper re-solves byte-identically.

**DOF ledger (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`): ZERO new free
parameters.** Both arms are booleans over measured inputs — the per-plant
contract share is EIA-923 Schedule-5 tonnage, the scope is the EIA-860
`Regulatory Status` boolean. Neither is a magnitude, neither was swept, and
both regenerate for a forward year from forward filings (rule 13
`[R-MEASURED]`'s forward test). `scripts/build_dof_ledger.py:1425` already
carries `coal_committed_takeorpay_regulated`, so the ledger line appears without
new plumbing.

---

## 3. ANSWERING THE CONTESTED PRIOR ART — owner-directed, not glossed

`coal_committed_takeorpay_sunk_fixed` exists to **suppress** exactly the
discount this lane arms, and its rationale is physics rather than an ISO
verdict:

> *"A take-or-pay contract is an obligation over an ACCOUNTING PERIOD (annual /
> monthly contracted tonnage), not a per-hour price. Over that period it is sunk
> in aggregate, so it does not enter the marginal cost of an incremental MWh
> unless the obligation would otherwise go unmet — a plant that over-fulfils its
> contract buys its marginal ton at SPOT. Applying `1 − share` as an
> unconditional per-hour multiplier on the committed band converts a sunk FIXED
> cost into a MARGINAL subsidy and makes that band inframarginal in all 8760 h."*
> (miso-96; rules 17 `[R-FLOOR-WINDOW]` / 19 `[R-ONE-MECH]`.)

**The answer, in three parts.**

**(a) It is an argument about a different object.** The miso-96 claim is about
CONTRACT ACCOUNTING: it says the contracted ton is not free at the margin. This
lane's limb is not making that claim. Its driver is **REGULATORY CONDUCT** — a
rate-regulated operator's offer is not a marginal-cost offer at all. The
committed band's price under this arm is not asserting "the fuel is free"; it is
asserting "this unit is self-committed and its owner is not choosing hour by
hour whether to run it." Those are different physical claims about different
objects, and miso-96 refutes only the first. The evidence that the second is the
live one in NWPP is structural and stated before the solve: **COAL_BIT, the
deficit class, is 81.7 % regulated** (2,998 of 3,668 MW) against 44.3 % for PRB
and 63.7 % for NWPP coal overall. The deficit is concentrated in the
most-regulated class.

**(b) It is measurably not a subsidy.** A subsidy moves one way. This arm moves
**both** ways, because the contract share is measured per plant rather than
assumed: the spot-heavy plants' `_mustrun` band gets **DEARER** (§5 — North
Valmy 0.5611 goes $4.50 → $27.47/MWh, Huntington $4.50 → $4.95, Hunter $4.50 →
$5.20, TS Power $4.50 → $8.99), because they now pay for the spot remainder the
uniform 100 %-sunk assumption was giving them for free. North Valmy's must-run
band leaves the money in 6,600 hours of 2024 that it was in before. A fitted
adder does not do that.

**(c) Where miso-96 lands a real hit, and it is recorded rather than absorbed.**
The arm **collapses `_mustrun` and `_committed` to the same price** at every
regulated contracted plant (§5.2 — p6165 both at $5.20, p8069 both at $4.95,
p8224 both at $27.47). That is the literal footprint of the miso-96 objection:
after the arm, the committed band is priced as though it were must-run, and it
binds in all 8760 h with **no window** (rule 17 `[R-FLOOR-WINDOW]`). This lane
does **not** claim that away. Two things bound it:

1. It is a **price**, not a floor. The committed band is still a dispatchable LP
   row with no `pmin` — the LP may leave it undispatched, and §6 measures that
   it does exactly that at North Valmy in 6,600 h of 2024. Rule 17 governs
   min-gen/commitment **floors**; this arm adds none.
2. Rule 19 `[R-ONE-MECH]` is satisfied by **replacement, not stacking**:
   `coal_bit_committed_takeorpay`, `coal_committed_takeorpay_all` and
   `coal_committed_takeorpay_sunk_fixed` all stay off, so exactly one mechanism
   prices the contracted committed band.

**(d) And the honest structural caveat, stated at the gate.** NWPP-43 §4.1
diagnosed the C4 defect as *"the coal stack has no rising curve above
must-run."* **This arm does not build one.** It makes the cheap block bigger —
`_mustrun` + `_committed` become one ~2,889 MW block at $4.50–$27 — and leaves
the `econlo` / `econhi` / `peak` shelf where it was, within $0.51/MWh of itself
at ~$42. The stack after the arm is still a two-step, just with a larger first
step. If C4 improves, it improves because coal's **volume** and its
**gas-price-independence** improve, **not** because the offer curve started
rising. Whatever this lane's gate says, the rising-curve defect stays open and
is **not** closed by a pass here.

---

## 4. G-DRIFT — form 4 is VALID, no control solve (rule 29(b))

`git diff b68673a9..5c0bec8b` over `src/market_sim`, `scripts/run_calibration.py`,
`scripts/run_calibration_full.py`, `scripts/lib`, `data/raw/_validation-source`,
`data/raw/reference`: **8 commits, 6 files.** Hunk classification:

| commit | change | verdict | reason |
|---|---|---|---|
| `49a8f17b` | `constants.py` — NWPP keys added to `REGIONAL_RENEWABLE_CF` | **INERT** | reporting-only table; the ONLY consumers are `scripts/build_mac_sidecar.py` and its derive script (verified by grep over `src/` + `scripts/`). Not a solve input. |
| `3fc20b97` | `constants.py` `PPA_COST_RECOVERY_YR`; `new_entry.py` `cf_override`/`life_override` | **INERT** | `new_entry.py` is capacity evolution — a `mode="backcast"` run never enters it. Both overrides default `None`, no `ScenarioConfig` field reaches them, and at `None` the function is byte-identical. |
| `aa4bb5b5`, `6769b6ed`, `75e57fd9` | CAISO citygate blackout bridge (`data/fuel/hubs.py`, `scenarios.py`) | **INERT** | gated on `caiso_citygate_blackout_bridge`, `bool = False`, absent from the keeper's recipe; the CAISO citygate series is not on NWPP's gas path. |
| `e63f730a` | spp-49 benchmark membership (`run_calibration_full.py`, `scenarios.py`) | **INERT** | gated on `benchmark_membership_vintage_union`, `bool = False`, absent from the keeper's recipe; a scoring-surface change, not a solve input. |
| `029ff0b2` | merge; adds `scripts/gen_soco53e_attestation.py` only | **INERT** | another ISO's attestation generator, on no solve path. |

**And the mechanical corroboration, which is stronger than the hunk reading.**
The capx-D79 solve-surface fingerprint was recomputed for NWPP in a sparse
worktree at the keeper's own `git_sha` and at this lane's base SHA:

```
keeper b68673a9 : fingerprint 1117290897294920   180 rows   (reproduces the
                  bundle's committed solve_surface.json EXACTLY)
base   5c0bec8b : fingerprint 141d23831b47ea8c   182 rows

row-level diff, NWPP:   MOVED: []   REMOVED: []
                        ADDED: ['PPA_COST_RECOVERY_YR', 'REGIONAL_RENEWABLE_CF']
```

**Zero of NWPP's own 180 surface rows moved.** The entire fingerprint delta is
the two ADDED reporting tables classified INERT above. **All hunks INERT ⇒ rule
29(b) form 4 is valid, the keeper's committed bundle IS the control, and no
control solve is spent.** NWPP-42 independently measured form 4 reliable for
this ISO (the rule-36 year-isolation artifact is 0.000 TWh of annual class
volume in every class and year, every scored criterion reproducing to 0.001).

---

## 5. THE MEASURED OFFER DELTA — re-measured at THIS lane's base SHA

`scripts/probes/_nwpp44_takeorpay_phase0.py`, rebuilding the keeper's own recipe
through the sanctioned `run_year(..., fleet_only=True)` path (whose `mc_base` is
the assembled P0 objective the LP is actually handed), CONTROL vs ARM, both legs
at the same SHA with only the two booleans differing.

### 5.1 The delta is perfectly confined, two-sided, and identical across years

| year | class · band | n | MW | ctl $/MWh | arm $/MWh |
|---|---|---|---|---|---|
| 2023 | COAL_BIT committed | 4 | 811.5 | 36.07 | 8.13 |
| 2023 | COAL_BIT mustrun | 3 | 590.3 | 4.50 | 9.49 |
| 2023 | COAL_PRB committed | 5 | 1,395.0 | 26.24 | 4.50 |
| 2023 | COAL_PRB mustrun | 1 | 91.9 | 4.50 | 9.38 |
| **2024** | **COAL_BIT committed** | **4** | **811.5** | **44.53** | **7.95** |
| **2024** | **COAL_BIT mustrun** | **3** | **590.3** | **4.50** | **9.24** |
| **2024** | **COAL_PRB committed** | **5** | **1,395.0** | **24.92** | **4.50** |
| **2024** | **COAL_PRB mustrun** | **1** | **91.9** | **4.50** | **8.99** |
| 2025 | COAL_BIT committed | 4 | 811.5 | 45.78 | 8.19 |
| 2025 | COAL_BIT mustrun | 3 | 590.3 | 4.50 | 9.57 |
| 2025 | COAL_PRB committed | 5 | 1,395.0 | 24.75 | 4.50 |
| 2025 | COAL_PRB mustrun | 1 | 91.9 | 4.50 | 9.10 |

**13 rows move of 641/642/646. NON-COAL ROWS MOVED: 0, in every year. Total
|Δ pmax| = 0.000000 MW. Moved capacity 2,888.8 MW, identical all three years.**

**Reconciliation with NWPP-43 §5, stated rather than smoothed.** The **row set,
the row counts and the MW are identical** (BIT committed 4 / 811.5; BIT mustrun
3 / 590.3; PRB committed 5 / 1,395.0; PRB mustrun 1 / 91.9). The **price levels
differ by $1–3/MWh** (NWPP-43 quoted 2024 BIT committed $46.31 → $10.53 against
this lane's $44.53 → $7.95). `mc_base` here is `(n_gen, 8760)` and several of
these rows are hour-varying under the keeper's armed PRB sigmoid, so the two
lanes are quoting different summary statistics over the same array; this lane's
figure is the **cap-weighted mean over all 8,760 hours** of the moving rows
only. G-DRIFT (§4) rules out a code cause: zero NWPP surface rows moved between
the two SHAs. Nothing downstream turns on the $1–3, and this lane cites **its
own** numbers.

### 5.2 The per-plant picture — where the two-sidedness actually is (2024)

| plant | rank | contract share | band | ctl mean | arm mean |
|---|---|---|---|---|---|
| 6165 Hunter | BIT | 0.9816 | mustrun | 4.50 | **5.20** |
| 6165 Hunter | BIT | 0.9816 | committed | 42.40 | **5.20** |
| 7790 Bonanza | BIT | 1.0000 | committed | 41.15 | **4.50** |
| 8069 Huntington | BIT | 0.9888 | mustrun | 4.50 | **4.95** |
| 8069 Huntington | BIT | 0.9888 | committed | 44.84 | **4.95** |
| **8224 North Valmy** | BIT | **0.5611** | mustrun | 4.50 | **27.47** |
| **8224 North Valmy** | BIT | **0.5611** | committed | 56.84 | **27.47** |
| 4158 Dave Johnston | PRB | 1.0000 | committed | 18.44 | **4.50** |
| 4162 Naughton | PRB | 1.0000 | committed | 35.18 | **4.50** |
| 6076 Colstrip | PRB | 1.0000 | committed | 26.50 | **4.50** |
| 6101 Wyodak | PRB | 1.0000 | committed | 20.99 | **4.50** |
| 8066 Jim Bridger | PRB | 1.0000 | committed | 37.99 | **4.50** |
| **56224 TS Power** | PRB | **0.9047** | mustrun | 4.50 | **8.99** |

Two things this table makes visible that an aggregate cannot:

* **the arm is two-sided at the plant level** — North Valmy's must-run band goes
  up by $23/MWh and TS Power's by $4.49, because their measured contract shares
  are 0.5611 and 0.9047 rather than the assumed 1.0;
* **`_mustrun` and `_committed` collapse to one price** at every plant carrying
  both. This is the miso-96 footprint, answered at §3(c) rather than hidden.

---

## 6. THE ZERO-LP PREDICTION, in the kill condition's own currency

Per moving row: the hours in which its assembled offer sits **below the
cap-weighted CC_REGULAR offer of the same hour**, times `pmax × availability`.
This is an **upper bound on the direct channel** — it ignores congestion,
hydro/import competition, must-run gas, the residual-load shape and the
price feedback of coal displacing gas, all of which can only reduce it.

| year | CC_REGULAR cap-wtd offer | class | in-merit bound ctl → arm | **Δ** |
|---|---|---|---|---|
| 2023 | $51.71 | COAL_BIT | 6.555 → 8.526 TWh | **+1.971** |
| 2023 | | COAL_PRB | 7.922 → 10.733 TWh | **+2.811** |
| **2024** | **$23.09** | **COAL_BIT** | **4.484 → 9.368 TWh** | **+4.884** |
| **2024** | | **COAL_PRB** | **4.756 → 10.204 TWh** | **+5.448** |
| 2025 | $26.90 | COAL_BIT | 4.671 → 9.560 TWh | **+4.889** |
| 2025 | | COAL_PRB | 6.408 → 10.070 TWh | **+3.661** |

### 6.1 What this says about each limb — and it is NOT what NWPP-43 expected

The C1 band is `±min(max(2 % ISO-load, 3 % actual-gen), 8 TWh)`. NWPP demand is
**270.5 / 277.6 / 288.7 TWh**, so the 2 %-of-load term dominates every coal
class and the band is **±5.41 / ±5.55 / ±5.77 TWh**.

Against the keeper's committed positions (COAL_BIT model 16.79 / 7.48 / 6.94 vs
actual 14.59 / 12.83 / 18.21; total coal model 41.55 / 27.39 / 28.32 vs actual
42.27 / 38.30 / 42.26):

* **THE OVERSHOOT LIMB IS MEASURABLY OUT OF REACH.** At **100 %** realization of
  the bound — which cannot happen — 2024 COAL_BIT reaches 7.48 + 4.884 =
  **12.36 TWh against an actual of 12.832**: still *under*, and far below the
  14.83 overshoot trigger. The same holds in 2025 (11.83 vs 18.21 actual).
  2023 COAL_BIT, the one row already over at +2.193, reaches at worst
  **+4.16 TWh** — inside its ±5.41 band, and +1.55 pp against the ±3 pp leg.
  COAL_PRB's worst case lands within ~+1 TWh of actual in every year.
  **So the §6(1) PRB overshoot risk NWPP-43 flagged, which Option B declined to
  remove, is bounded by measurement at less than the band in every year.**
* **THE INERT LIMB IS THIS LANE'S LIVE RISK.** The kill threshold is 2024
  COAL_BIT **+2.0 TWh**; the bound is +4.884. The arm must realize **41 %** of
  its own upper bound to survive. Since the bound ignores every competing
  resource, 41 % is not a formality.

**This is stated BEFORE the solve and it does not move the kill condition.**
NWPP-43 pre-registered a two-sided condition believing overshoot was the live
risk; the measurement says the opposite. The condition is carried **verbatim**
anyway (§7) — a pre-registered gate that is relaxed once its author learns which
limb binds is not a pre-registered gate.

### 6.2 Watch rows, named in advance

* **CC_REGULAR** absorbs the displacement. It is a C1 load-bearing row and this
  lane can push it out of band from the other side. Reported, not absorbed.
* **North Valmy (8224)** is the one plant the arm makes *dearer* on net. Its
  must-run band leaves the money in 6,600 h of 2024 (8,760 → 2,160 in-merit
  hours). If NWPP's C1 coal rows move the wrong way, this is the first place to
  look, and it is a **correct** consequence of a measured 0.5611 contract share,
  not a defect to tune away.

---

## 7. THE KILL CONDITION — carried VERBATIM from NWPP-43 §6. Not renegotiable.

2024 is the kill year: it is where the deficit lives, and it is the year
NWPP-42's condition would have fired on.

> **KILL — INERT limb:** 2024 **COAL_BIT** rises by **< 2.0 TWh** against the
> committed keeper ⇒ verdict **I (inert)**, not a keeper.
>
> **KILL — OVERSHOOT limb:** 2024 **COAL_BIT** overshoots the actual 12.832 TWh
> by **> 2.0 TWh** (i.e. model > 14.83), **or** any C1 coal row leaves its
> ±min(max(2 % ISO-load, 3 % actual-gen), 8 TWh) / ±3 pp band in any year ⇒
> verdict **R (rejected)**. Not renegotiable after the fact.

**C4 is the lane's GOAL but is NOT in the kill condition**, exactly as NWPP-43
wrote it: coal `r` ≥ 0.70 and NRMSE ≤ 0.30 are what a keeper needs, and they are
reported at full magnitude either way. **NWPP is PRICE UNSCORED** (rubric v3.8,
owner card S2): C3a/b/c are not scored in any year and this lane does not chase
price.

---

## 8. HOW IT IS SOLVED

Rule 36 `[R-YEAR-ISOLATION]`: **one shard per year** — 2023, 2024, 2025 — one
container each, one `--year <single year>`, composed by the parent with
`scripts/probes/_nwpp42_compose_span.py`. Rule 32(a): **this session never runs
an LP.** Every shard is pinned to the full 40-character SHA of the commit
carrying this PRECOMMIT, pushes its FULL bundle including
`dispatch/<year>_P1.parquet` via a `.gitignore` negation plus a plain `git add`
(rule 34(a)), and is archived once the parent has fetched, checked out and
verified it (rule 33(a)). Per rule 33(f) the shard branches are **transport, not
storage**: the parent lands the composed keeper bundle on `main` before this
lane's PR merges, and no leg SHA is treated as a recovery route.

Config signature each leg must show: `coal_takeorpay_from_data=True`,
`coal_committed_takeorpay_regulated=True`,
`coal_prb_committed_dispatchable=False`,
`coal_committed_takeorpay_sunk_fixed=False`, `use_campd_bins=True`,
`plant_level_fleet=True`, `mode=backcast`.

---

## 9. OPEN ITEMS — reported, never absorbed

* **`scripts/check_cache_key_registration.py` FAILS on `main` already.**
  `PPA_COST_RECOVERY_YR` and `REGIONAL_RENEWABLE_CF` have no `DECLARED` entry.
  **Verified pre-existing**: the identical failure reproduces on a clean HEAD
  with this lane's edit stashed. It is the marginal-abatement lane's to clear
  (its stated one-command remedy re-baselines names this lane has not measured),
  and repairing it here would touch every ISO. Not this lane's (rule 25).
* **The rising-curve defect stays open** — see §3(d). This arm enlarges the
  cheap block; it does not build a stack.
* **2023 COAL_BIT is already +2.193 TWh over** and this arm pushes it further
  over (bounded at +4.16 total, inside the ±5.41 band). Watch it.
* **The NWPP-40/41/42 attestations are wrong** about `use_campd_bins` being
  inert and `thermal_tranches_NWPP.csv` being unread — both false; the artifact
  is read, is a gate condition, and its per-plant shares set the keeper's coal
  tranches, so a regeneration WOULD move the keeper (rule 23
  `[R-FROZEN-DERIVE]` depends on knowing that). Recorded by NWPP-43; correcting
  the three attestations in place is still owed.
* **Jim Bridger (8066)** is absent from `thermal_tranches_NWPP.csv` and takes the
  `_DEFAULT_TRANCHE_PCT_BY_GROUP["COAL"]` (45/5/2) fallback for 1,049 MW — an
  estimate standing where a measurement could (rule 14 `[R-ACCURATE]`).
* **NWPP's FORECAST path** collapses coal to 9 heat-rate-bin units (`runner.py`
  never reads `plant_level_fleet`). Latent only because NWPP has no forecast
  lane (card N9).
* **Energy balance −10.02 TWh in 2025** against a ±3.0 tol (NWPP-40's
  served-interchange construction).
* **Chief Joseph's pond-balance dual** constant at −325.17 $/kcfs·h for 5,808
  hours of 2025 with pond = 0 and spill = 0 — still the first cascade question.
* **C5a CO2** a reported-only FAIL in all three years (−14.4 / −23.5 / −20.6 %).
* **21 pre-existing failures in `tests/scoring`** on `main` (golden-manifest /
  forecast-parity lanes) — re-verified by this lane as pre-existing, not
  repaired.
* `results/calibration/caiso279_ablate_dswcouple_span` parity RED — CAISO's.
* The cross-ISO PRB-proxy defect open in MISO / PJM / SPP — not this lane's.

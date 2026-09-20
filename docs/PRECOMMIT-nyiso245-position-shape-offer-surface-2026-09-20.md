# PRECOMMIT — nyiso-245: the MAPPING gate. A POSITION-CONDITIONED, SHAPE-ONLY measured offer surface for NYISO, and the six gates it must clear before a shard is spent

**Session** nyiso-245 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **zero LP in this container**).
**Date** 2026-09-20. **Base** `origin/main` at `5c0bec8b`.
**Keeper** `2026-09-19-nyiso241-ct-committed-measured`, bundle
`results/calibration/nyiso241_ctcommitted_span`, years {2022, 2023, 2024, 2025}. **UNCHANGED at
the time of writing.** ISO tier (2023–2025, rule 30 `[R-TOUCHPOINT-FOLD]` (c)) = **CALIBRATED**,
C3c the lone ledgered caveat.
**Predecessor** `docs/RESULT-nyiso244-the-object-is-in-the-body-not-the-top-2026-09-20.md` §7,
which set `measured_offer_surface` NYISO `U` → `G` and wrote a **two-limb re-open condition**.

**THIS FILE IS COMMITTED BEFORE ANY GATED NUMBER BELOW IS COMPUTED.** Every threshold, every
pass/fail bar, every scope rule and the no-substitute rules are fixed here, so no gate can be
written to fit a result (rule 1 `[R-STRUCT]`).

**What was measured BEFORE this file, and why each is admissible** (the same disclosure
nyiso-244 made, at the same grain):

| measured before | why it gates nothing |
|---|---|
| the keeper's own committed `run_config.json` (armed fields, registered bands) | a read of a committed artifact; no statistic |
| a **descriptive** P-27 column census (which columns exist, which are populated) | names the columns this document cites; no conditioned quantity |
| `_nyiso245_fleet_cache.py` — a dump of the keeper's assembled fleet arrays for 2022–2025 | INFRASTRUCTURE. A `fleet_only` rebuild persisted to `.npz` so the gated probes read it in seconds instead of re-running ~4 min/year. Every gated number is derived downstream from this dump, after this commit. |
| a read of `apply_miso_offer_surface` / `derive_miso_offer_surface.py` | a code read of the precedent form |

---

## 1. THE RE-OPEN CONDITION, QUOTED, AND HOW THIS DESIGN MEETS BOTH LIMBS

nyiso-244 §7 wrote the condition this document must satisfy. Quoted so it cannot be
paraphrased into something easier:

> The cell becomes live again if and only if **both** hold:
> 1. a surface form exists that prices the **econ/midcurve** rungs rather than the peak rungs …
>    and **§3.2 measures its reach at 74.5 %** of the object, which clears G3's bar; **and**
> 2. a cohort attribution passes a validation at least as strong as §4's — **or the form is
>    shown to need none.** … What it would still owe is the **mapping** — how a system-level
>    target is posted onto model rows — and that mapping is itself a modelling choice with the
>    same burden of validation the cohort just failed.

**Limb 1 — the form exists, and it is already in this repo, armed, for another ISO.**
`ScenarioConfig.miso_offer_surface_measured` (`data/offer_curves.py::apply_miso_offer_surface`,
derived by `scripts/data/derive_miso_offer_surface.py`) prices **every above-base tranche**, not
peak rungs. Its object is

```
p_j = step_mw_j / ecomax_mw                 own-curve POSITION, (0, 1]
D_j = price_j   - price_1                   own-curve RISE, $/MWh
mc[g, t] := mc[base(g), t] + D(p̄_g, state_bin(t), gas_bin(t))
```

**Limb 2 — THIS FORM NEEDS NO COHORT, AND THAT IS A PROPERTY OF THE OBJECT, NOT A CLAIM ABOUT
NYISO.** `D` is measured **within one unit, within one hour**, so it carries no unit identity, no
class, no fuel level and no market level: **a constant shift of a unit's entire submitted curve
cancels exactly.** `p` is likewise within-unit. Neither coordinate asks what the masked gen *is*.
MISO adopted this form *for exactly the reason NYISO needs it* — `derive_miso_offer_surface.py`'s
own header: *"Class-free by necessity, not by preference. MISO's masked corpus carries no fuel or
technology attribute and miso-138 built and REFUTED the offer-side class bridge, so every other
ISO's class-conditioned surface is unavailable here."* nyiso-244 §4 is NYISO's miso-138.

**And the shape-only property is what defeats the blocker nyiso-244 §6 flagged**: the two fleets
differ by a near-constant **~9.4 GW** at the top of the curve, so a LEVEL comparison between them
is uninterpretable. A within-unit rise is invariant to exactly that error. This is the same
reasoning MISO's derive states for a different reason (*"miso-145 measured MISO's real book as
$8–15/MWh CHEAPER than the model at matched position, so transferring level would move C3a the
WRONG WAY"*) — and NYISO's version of it is stronger, because NYISO's level error is a **scope**
error rather than a conduct difference.

**Rule 25 `[R-ISO-SCOPE]` — what is reused and what is refused.** Reused: the **method** (a
within-unit rise on a position coordinate), the **code path**, and the mechanism family's
**registered bin geometry**. Refused absolutely: **every MISO Δ value**. NYISO's artifact is
derived from NYISO MIS P-27 against NYISO's own delivered-gas series and NYISO's own net load.
No number crosses the boundary. This is the same line nyiso-244 §8 drew on NEISO's cohort method.

---

## 2. THE MECHANISM UNDER DESIGN

**`ScenarioConfig.nyiso_offer_surface_measured`** (new, default `False`), plus the artifact path
and the frozen geometries, a NYISO member of the position-shape family. Derive:
**`scripts/data/derive_nyiso_offer_surface.py`** over `data/raw/nyiso-bid-data/genbids` (NYISO MIS
**P-27**, intaken by nyiso-243).

**Corpus mapping, fixed here** (P-27 column → the derive's quantity; the descriptive census above
is what names them):

| P-27 column | quantity |
|---|---|
| `Masked Gen ID` | unit key |
| `Date Time` (UTC — nyiso-243's verified convention, `_std_hour`) | hour key |
| `Market` ∈ {`DAM`} | market |
| `Upper Oper Limit` | `ecomax_mw` |
| `Fixed Min Gen MW` | `ecomin_mw` (the first block's lower edge) |
| `Dispatch MW1..12` | `step_mw` (cumulative; the last populated block equals UOL) |
| `Dispatch $/MW1..12` | `step_price_usd_per_mwh` |
| `Self Commit MW1..4` (max) | `self_scheduled_mw` |

**Population rules — ADOPTED UNCHANGED from `derive_miso_offer_surface.py::prepare`, not
re-invented** (a re-invented exclusion set is a tuning channel): drop `ecomax ≤ 0`; drop fully
self-scheduled rows (`self_scheduled ≥ ecomax`); drop non-increasing MW; drop `p ∉ (0, 1]` or
zero width; `width_j = step_mw_j − step_mw_{j−1}` with the first block's predecessor at `ecomin`.
Estimator: **capacity-weighted median of `D` per cell**, weights = each step's own MW width, read
off a weighted histogram on a `0.05 $/MWh` grid — the family's own convention.

**FROZEN GEOMETRY — ZERO FREE PARAMETERS (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).**

| geometry | value | source, and why it is not a tuned number |
|---|---|---|
| position bins | `(0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0)` | the **mechanism family's** registered grid (`miso_offer_surface_position_bins`, already a `ScenarioConfig` field). Adopted unchanged **because inventing NYISO's own invites a sweep**; a bin geometry is not a fitted value. |
| net-load percentiles | `(0.80, 0.90, 0.97)` | the **registered cross-ISO** geometry, carried by five ISOs' surface fields already |
| gas bins | **terciles of NYISO's OWN pooled delivered-gas series** | the only NYISO-specific geometry, and it is a quantile of NYISO's own data, not a level |

**NEITHER GEOMETRY IS EVER SWEPT.** Any change to either after a gated number is computed
invalidates this PRECOMMIT and the session says so.

**Pooling (rule 13 `[R-MEASURED]`).** ONE artifact pooled over **2022–2025**, applied identically
to every year. A per-year surface is the same-year measured-outcome pin rule 13 forbids and is
refused here in advance.

---

## 3. THE SIX GATES. EVERY ONE BINDS. ANY FAILURE REFUSES BEFORE A SHARD.

### G1 — REACH. Does the form reach the object's rungs?

nyiso-242 phase 0D: the energy dual **is** the marginal tranche's offer, so only the **idle
sub-gate** capacity's offer can move it. The object is the **4,715.7 MW** idle below $300 in the
70 missed winter hours of 2022 — nyiso-242's number, carried unchanged so the two sessions'
arithmetic stays comparable.

The family's row gate is the **incumbent mechanism's own tag**, never a class tuple (rule 18
`[R-PHYSICS]`): `(offer_markup_hr > 0) & (~is_base)`, where `is_base` is the plant's first tranche
in fill order.

* **G1 PASSES** iff the idle sub-$300 capacity sitting on rows the NYISO row gate tags is
  **≥ 50 %** of 4,715.7 MW. **The bar is nyiso-244's own G3 bar, carried forward unchanged** so it
  cannot be accused of having been re-set to fit this form.
* **G1 FAILS** ⇒ the mechanism is refused, exactly as the peak-rung form was.
* **ONE ALTERNATIVE ROW GATE IS ADMISSIBLE, AND ONLY ONE, AND ONLY UNDER G2.** If the
  incumbent-tag gate misses but the **plant-structural** gate `~is_base` over the classes the
  corpus's own population represents clears the same 50 % bar, that gate may be taken **iff G2
  still passes on it** — i.e. iff the surface still REPLACES every armed mechanism on every row it
  would newly tag. It is admissible because it is defined by the model's own tranche structure
  (base vs non-base), which is a physics coordinate, not a class tuple. **No third row gate is
  available**, and in particular no gate defined by class membership, by zone, or by which rows
  happen to be idle — the last would be selection on the object itself.

### G2 — RULE 19 `[R-ONE-MECH]`, ON THE ECON RUNG THIS TIME

nyiso-244 discharged rule 19 for the **peak** rung. An econ-rung form owes it again, on different
rungs, against a **different** set of armed mechanisms — and NYISO has one that nyiso-244's
enumeration did not have to reach: **`nyiso_st_gas_econ_bands_deleaked` is ARMED in the keeper and
writes the ST_GAS econ bands** (to the rule-24/25 neutral `econ_low = econ_high = 1.0`).

* **G2 PASSES** iff all three hold:
  * **(a)** the enumeration is complete — every armed field that can write a NYISO **non-base**
    rung is named **from the keeper's own `run_config.json`**, not from memory;
  * **(b)** the surface **REPLACES, never stacks**. The form is an **assignment**
    (`mc[row] := mc[base] + Δ`), so it overwrites whatever any enumerated mechanism wrote into a
    tagged row. This is verified **numerically on the keeper's own arrays**, not asserted: for
    every tagged row, the post-surface value must be independent of the incumbent's contribution.
    Max residual incumbent contribution on a tagged row must be **exactly 0.0**;
  * **(c)** the mechanism is positioned against the de-leak's **own declared open root cause**.
    `backcast_config.py`'s comment states the de-leak *"does NOT identify the markup — the de-leak
    declared CC's own markup un-identified … the identification stays an OPEN ROOT CAUSE against
    NYISO scarcity/reserve (RCPF/AS) price formation, issue #1344."* A measured surface pricing the
    rise above that neutral band is **the successor that open item names**, not a second mechanism
    beside it. If instead the surface would sit *on top of* a de-leaked band while the de-leak
    remains armed and live on the same row, that is a stack and **G2 FAILS**.
* **G2 FAILS** ⇒ refuse, or re-scope to a replacement form. Never stack.

### G3 — THE CORPUS CARRIES THE OBJECT (shape, and it is a real offer curve)

Asserting the shape-only property is not measuring it. Three tests, all on NYISO's own corpus:

* **G3a — MONOTONICITY.** A real submitted curve rises. The measured Δ ladder must be
  **monotone non-decreasing in position** in **≥ 80 %** of populated (gas × state) cells.
* **G3b — THE CONDITIONING DRIVER RESPONDS, ON THE Δ OBJECT** (rule 13's forward test, re-done on
  the object actually transferred rather than on a level — this is the gate nyiso-244 G4 was, moved
  onto the right quantity). Δ at the **top position bin** must be **strictly larger in the tightest
  net-load bin than in the loosest**, measured **independently in each of 2022/2023/2024/2025**, in
  **≥ 3 of 4 years**. Bar carried unchanged from nyiso-244 G4.
* **G3c — CONTAMINATION, REPORTED AT FULL MAGNITUDE, NOT GATED.** P-27 is the whole NYCA internal
  fleet: nuclear, hydro and wind submit single-block price-taking curves whose Δ ≡ 0. Their weight
  is reported per position bin. **It is deliberately NOT a gate and NOT an exclusion**, for two
  reasons fixed here in advance: (i) the family's own population rules keep them, and re-inventing
  an exclusion set is a tuning channel; (ii) the bias is **conservative** — it pulls Δ *down*, so it
  can only make the mechanism weaker, never stronger. **If the session later wishes to exclude
  them, that is a DIFFERENT mechanism and needs its own PRECOMMIT.**

### G4 — NOT INERT (a reach test, explicitly NOT a fit test)

**Rule 1 `[R-STRUCT]` governs this gate and limits it.** A structurally-correct mechanism is
**never** judged by whether the residual moved, and is **never** rejected because it did not. So
this gate refuses **one thing only: inertness** — a mechanism that changes no offer is not a
mechanism (matrix verdict `I`).

* **G4 PASSES** iff, posting the measured Δ onto the tagged rows of the keeper's own 2022 arrays,
  the repriced rows carry **≥ 500 MW** of capacity whose offer moves by **≥ $1.00/MWh** in the
  median missed winter hour. A deliberately low bar: it separates "does something" from "does
  nothing", and nothing else.
* **REPORTED AT FULL MAGNITUDE, GATING NOTHING**: the induced movement in nyiso-244 §6.1's
  differenced statistic (model MW withdrawn from below $150 / $200 in the 70 missed hours, against
  the market's 7,674.5 / 6,202.5 MW and the model's current 3,610.7 / 1,213.1 MW), **and its sign**.
  **A movement in the wrong direction does not refuse the mechanism** — rule 1 forbids that
  reading — but it is reported, and it informs the owner's promotion decision (rule 31
  `[R-RETAIN]`), which is the owner's and not this session's.

### G5 — C1/C2 EXPOSURE, PRE-REGISTERED BEFORE THE SOLVE

**The standing bar this design must state plainly.** Raising the **econ** band is a far larger
intervention than raising a peak band: econ rungs are the **bulk** of capacity and sit at or near
marginal cost, so this surface will move **dispatch volumes**, not only price. Pre-registered here
so it cannot be discovered afterwards:

* **Measured at zero LP before any shard**, and stated in the RESULT whatever it shows: the share
  of the model's annual thermal energy sitting on repriced rows, and the median $/MWh the reprice
  moves them.
* **The arm's C1 and C2 are reported at full magnitude beside C3a/C3b/C3c**, in the same table, for
  **every** scored year — never a price table with the volume criteria omitted.
* **A C1/C2 DEGRADATION IS REPORTED, NEVER TRADED.** If the arm moves a load-bearing criterion
  (C1/C2/C3a/C3b) from PASS to FAIL in any scored year, the session's recommendation is **do not
  promote**, stated in the RESULT — and the run is still registered (rule 15 `[R-DASHBOARD]`) and
  the owner still rules (rule 31). The session does not delete it and does not quietly prefer the
  price improvement.

### G6 — RULE 13 `[R-MEASURED]` ADMISSIBILITY OF THE WHOLE CONSTRUCTION

* **G6 PASSES** iff all four hold: (a) all three conditioning drivers (own-curve position, net-load
  percentile **within the solve's own year**, delivered-gas bin) exist in a forecast year and
  respond to changed conditions; (b) the artifact is **pooled 2022–2025** and applied identically to
  every year — never per-year; (c) the artifact is **frozen and committed before the arm solves**
  (rule 23 `[R-FROZEN-DERIVE]`); (d) nothing measured is an **outcome** — Δ is a submitted offer,
  not a cleared price, a realised dispatch or a residual.

---

## 4. WHAT IS SPENT, AND WHAT IS NOT

**If every gate passes**, the arm is solved as **one shard per year** — rule 36
`[R-YEAR-ISOLATION]` (a), which is the one place rule 32 `[R-SHARD]` (b)'s fan-out ban does not
apply — for **all four keeper years {2022, 2023, 2024, 2025}** (rule 34 `[R-SHARD-PROMOTABLE]` (c):
all years go into keepers; rule 16 `[R-ALLYEARS]`). Each shard pushes its **full** bundle including
`dispatch/<year>_P1.parquet` (rule 34 (a): `.gitignore` NEGATION + plain `git add`, never
`git add -f`). The parent composes at zero LP, scores, and registers once.

**The control is the incumbent keeper's committed bundle** — rule 29 `[R-SCREEN]` (b), form 4. **No
control solve is spent.** A `G-DRIFT` code-level audit against the keeper's `git_sha` `5356fb71`
validates form 4 and is recorded in this document's addendum **before the arm is solved**.

**If any gate fails**, **no shard is launched** (rule 34: a solve that cannot back a promotion is
not spent), the cell is re-stamped with the measured reason, and the RESULT carries every number.

## 5. WHAT THIS SESSION WILL NOT DO

* **Not re-open** anything on rule 28 `[R-MECH-MATRIX]` (a)'s DO-NOT-REDO list: the NYISO tail
  availability family (refuted on two independent instruments), `nyiso_iroquois_winter_spread`,
  `temp_dependent_derate`, `cc_winter_capability_basis`, the ST_GAS availability blanket,
  `nyiso_hub_gap_month_level`, `tsa_transfer_derate`, `scuc_load_pocket_commitment`,
  `nyiso_synchronised_reserve`, `nyiso_incity_commitment_obligation`,
  `hydro_budget_period_by_instrument`, `cc_committed_offer_margin`, the RCPF/ORDC successor
  (foreclosed in full by nyiso-242 §4), or the peak-rung surface form nyiso-244 refused.
* **Not touch** 2025 summer, which nyiso-243 §4 separated out as a real-time shortage-pricing object
  an energy offer cannot reach.
* **Not revert** the keeper to "restore" the full-span headline (rule 1). NYISO is CALIBRATED on its
  ISO tier and that is not this session's to trade.
* **Not use** `MARKET_SIM_WARMSTART_XYEAR` or `MARKET_SIM_P1_BASIS_SEED` (rule 36 (d): both default
  off, and this session sets neither).

# FINDING — neiso-68 (LANE A of the STEP-3 charter work): the LP-side seam question is answered, and the answer is **NO** — the keeper LP would **not** decline the seam population. Against the model's own clearing prices the seam capacity is in merit on essentially every seam day (median in-merit share 100 %, 87.7–97.6 % of seam days repay the start at LP prices), seam days are statistically indistinguishable from the same units' running days (AUC 0.48–0.52), the LP's strict decline predictor fails the placebo in all three years, and restoring the envelope would inject a first-order 15–38 TWh of phantom dispatch or crush the calibrated price level. The envelope deletion is definitionally impure but **operationally load-bearing**: no mechanism the model currently carries — detector-side or LP-side — reproduces this population's behaviour (2026-07-26)

**Freeze status: STILL ACTIVE, and this finding does not lift it.** It closes
the LP-side lane (charter §9 "not settled" item 1) with a measured negative
and *strengthens* the standing recommendation to the owner (disposition (b),
carry the seam explicitly). **Only the owner lifts the freeze.**

Probe (committed, re-runnable, **no LP solve** — it reads the keeper replay's
committed hourly sidecars): `scripts/probes/_neiso68_lp_seam_screen.py`.

Context: `FINDING-neiso66-overcount-rootcause-2026-07-26.md` §5b argued on
rule 1 `[R-STRUCT]` grounds that the seam units (available-but-not-committed
capacity the detector books as outage) belong in the availability envelope as
*available*, with the LP declining them on its own commitment economics.
`FINDING-neiso67-...` settled only that the **detector** cannot identify them
from admissible inputs; it explicitly did not settle whether the **LP** would
decline them, and warned the null does not transfer across instruments. This
finding measures the LP side directly.

---

## §1 — the instrument, and the falsifiers stated before measurement

The reference is the keeper's **own solved clearing price**: the zonal energy-
balance duals of `neiso64_meritguard_a1` (the neiso-61 keeper recipe replayed
fix-in-place on the guard-corrected envelope — the bundle every current NEISO
number stands on), read from its committed `hourly/system_<year>.parquet`
sidecars at the scored bid-cost pass. This is a genuinely different object
from neiso-67's RCC (the CEMS-revealed p90 of running units' SRMC): the LP
price carries the keeper's offer multipliers, VOM, RGGI carbon cost,
fast-start markup and scarcity adders of whatever unit the *model* has on the
margin. Every unit-day construction (panel, SRMC, seam population, best-block
recovery, published control, placebo) is reused from the neiso-67 probe
unchanged; the only substitution is the reference price. All 89/84/83 panel
units zone-map, so each unit is priced at its own zone's dual.

The structural fact that frames the reading, measured from the keeper's own
`run_config.json` and the `ScenarioConfig` scope: **the NEISO keeper's only
commitment device on the CC main blocks is the offer-multiplier level.**
`tranche_startup_amortization` scopes to fast-start tranches (CT econ/peak +
the CC duct-burner peak band only — "a big CC's econ blocks are deliberately
excluded"), and every commitment bridge is off. So the LP's decline prediction
for a day is exact and strict: *no hour of the day clears against the offer.*

Falsifiers, stated up front, both directions live:

* §5b's operational claim ("restored, the LP declines them") is **falsified**
  if the seam unit-days are predominantly in merit at the keeper's own prices
  and offer levels.
* The opposite claim ("the LP cannot own this population") is **falsified** if
  the seam days are predominantly out of merit at LP prices **and** the
  LP-decline split meets the charter D1 identification standard against
  ISO-NE's published columns (sign-stable, above placebo).

Bias directions, all favouring the *other* outcome than the one found: the
keeper solved seam days **without** the seam capacity (its absence props the
price, overstating in-merit); the D1 SRMC omits VOM and RGGI (understating
unit cost, overstating in-merit)… both push toward "in merit", so they cannot
manufacture a decline result — and none was found. The offer-multiplier sweep
(bare → econ_high → committed, up to 1.27× on CC) bounds the second bias; the
price-feedback bound in §5 bounds the first.

## §2 — the LP's price surface sits ABOVE the detector's reference

Median $/MWh on seam days (LP zonal price vs RCC): **33.4 vs 29.6** (2023),
**34.5 vs 20.6** (2024), **44.0 vs 33.3** (2025) — gaps of +3.8 / +13.9 /
+10.7. The model's marginal unit prices in its VOM, carbon and markup; RCC by
construction does not. So on the LP instrument the seam is even *deeper* in
merit than the detector's reference made it. Whatever declines these units in
reality, it is not a price level the model fails to see — the model's price is
*higher*.

## §3 — seam days are indistinguishable from running days at the LP's prices

The neiso-67 §4 rematch, reference swapped to the LP price (seam = kept
booked-out unit-days; running = the same units' clean running days):

| year | seam days | median in-merit share (bare / econ / committed) | zero-clear share (bare → committed) | share `R_lp ≥ 1` seam vs running | AUC |
|---|---|---|---|---|---|
| 2023 | 6,905 | 100 % / 100 % / 100 % | 9.3 % → 14.6 % | **87.7 %** vs 89.1 % | 0.508 |
| 2024 | 5,057 | 100 % / 100 % / 100 % | 1.2 % → 3.0 % | **97.6 %** vs 93.5 % | 0.478 |
| 2025 | 3,011 | 100 % / 100 % / 100 % | 6.0 % → 13.1 % | **91.9 %** vs 90.4 % | 0.495 |

On the median seam day, *every* hour clears at every offer level up to the
keeper's committed 1.27×. The strict decline predictor (zero hours clear)
fires on 1–15 % of seam days — and fires **as often on days the units actually
ran** (5–15 %), which is why the AUC is a coin flip. The neiso-67 sign
inversion (idle days scoring *higher* recovery than run days on RCC, AUC
0.39–0.41) relaxes to indistinguishability on the LP price, but never to
discrimination. Robustness: identical zero-clear/`R_lp` numbers on the
pre-commitment base-cost pass (median seam-day spread +14.6 / +19.7 / +20.5
$/MWh there), so no pass choice is doing the work.

## §4 — the LP's decline signal fails the identification standard

The charter D1 test with the LP as reference: split idle capacity by "no hour
clears at the committed offer", score each half monthly against ISO-NE's two
published columns (idle population, placebo and no-split references as in
neiso-67 report C):

| year | LP declines (pred UNCOMMITTED) | r vs UNCOMMITTED | placebo p95 | no-split reference |
|---|---|---|---|---|
| 2023 | 1,446 MW | +0.58 | **+0.73** | +0.48 |
| 2024 | 677 MW | +0.51 | **+0.52** | +0.59 |
| 2025 | 1,360 MW | +0.65 | **+0.66** | +0.61 |

The split **clears the placebo in no year** (2023 is well below it; 2024 sits
below the *no-split* series too), and the identified capacity (0.7–1.4 GW) is
small against the 5.7–7.9 GW idle population and the 1.2–1.7 GW residual.
Compare the standard the D1 positive control set on this same instrument
family: vetoed windows +0.77 / +0.71 / +0.67 with kept windows at +0.08 /
+0.28 / +0.31 — a clean, sign-stable separation. Nothing resembling that
appears here. The LP's price surface does not carry the commitment
information the detector's admissible reference also failed to carry.

## §5 — restoring the envelope breaks the solution either way

First-order bound at fixed keeper prices: seam capacity × its in-merit hours =
**38.2 / 35.0 / 17.3 TWh** (bare SRMC; still 35.2 / 33.3 / 15.0 TWh at the
committed offer) of restored dispatch over the seam days — against ~120 TWh of
annual NEISO load, from windows whose *measured* interior generation is 99.8 %
zero (neiso-66 §3). Fixed-price screening is an upper bound, and the
dichotomy is exact: restored supply either dispatches (contradicting the
observed idleness) or depresses the calibrated price level until it stops
(contradicting the keeper's scored fit). The feedback needed to rescue the
claim is out of range by an order of magnitude: the guard's own comparable
envelope restoration moved mean LMP −7 to −9 % (≈ −$3–4/MWh, charter §5),
while the median seam-day spread is **+$15–21/MWh** — and a 27 % offer-level
increase (bare → committed, worth ≈ $4–7/MWh on these units) moved the
zero-clear share only 9 → 15 / 1 → 3 / 6 → 13 %. No plausible price feedback
turns a ~100 % in-merit population into a declined one.

## §6 — what this settles

**The answer to the Lane A question is NO, on both of its testable halves:**
the LP would dispatch, not decline, the seam capacity (§3, §5), and its
decline signal does not reproduce the published uncommitted shape (§4). The
population's behaviour is now measured to be irreproducible from *every*
instrument this program is allowed: marginal economics (neiso-66 §4),
commitment/start-cost economics (neiso-67), and the model's own price surface
(neiso-68). Real drivers of the decline — day-ahead forecast risk, gas
nomination and fuel-position economics, bilateral/capacity-obligation
posture, crew and maintenance scheduling — live outside both CEMS and the LP.

Consequences, stated carefully:

* **neiso-66 §5b's structural argument fails operationally on the current
  LP.** The units "belong in the envelope as available" only if something
  declines them; nothing in the model does, and the model's only
  decline-shaped device on CC main blocks (the offer level) is measured here
  as inert on this population. The detector's deletion of this capacity —
  definitionally a seam — is at present **the only mechanism in the system
  producing the observed non-operation**, which is why restoring guard-vetoed
  capacity raised CAISO prices in the re-audit and why removing this deletion
  without a replacement would break NEISO dispatch and prices outright.
* **An LP-side closure would be a NEW commitment mechanism, and rule 19
  `[R-ONE-MECH]` binds** — but note the direction: the existing bridges
  (`caiso_ra_mustoffer`, `ercot_gas_commitment_bridge`) are min-gen *floors*
  that force capacity ON. The seam needs the opposite device, a structural
  *decline* of in-merit capacity, which no current mechanism provides and
  whose driver is — per the three findings jointly — not identifiable from
  admissible inputs today. Building it without an identified driver would be
  a fitted withholding knob, exactly what rule 1 `[R-STRUCT]` and rule 12
  `[R-FLOOR-WINDOW]`'s logic (no mechanism without a driver, a window and a
  forward story) forbid.
* **What would falsify this finding's own conclusion:** a counterfactual
  solve with the seam restored in which prices fall enough to idle the
  restored capacity while the keeper's price fit survives. §5 bounds that as
  requiring ~4–5× the measured restoration price effect; anyone proposing an
  LP-side closure should run exactly that solve first and meet that bar.

## §7 — disposition consequence (recommendation only; the owner decides)

This finding **strengthens** the charter §9 recommendation and adds the
missing half of its evidence base:

* **Take disposition (b) — leave the availability envelope alone and carry
  the seam explicitly.** Both sides are now measured: the detector cannot
  *identify* the population (neiso-67), and the LP cannot *reproduce* its
  behaviour if handed it (neiso-68). Deleting it from the envelope is the
  one representation the program currently has that matches the measured
  world; the seam is carried as a documented, quantified scope difference
  between published unavailability and CEMS non-operation.
* **The §7 "Closed with cause" leg fits**: the over-count is explained,
  bounded, confirmed against a published instrument, and now shown to be
  closable by *neither* a detector change *nor* an envelope restoration on
  the current LP. That is a cause, not a stall.
* **The freeze-lift remains the owner's act** (`holdout-freeze.json`
  `lifts_when`; charter §6/§9). Its stated condition is met on the
  *explained* branch, with the measurement committed and re-runnable. No
  session lifts it by inference, and this one does not.

Caveats bounding the reading: keeper prices on seam days are solved without
the seam capacity (direction: overstates in-merit; bounded in §5), the D1
SRMC omits VOM/RGGI (same direction), day-grain metrics with the panel's
local-clock convention (a leap year's Feb 29 is dropped from the model clock
and excluded here; 2024 populations shrink by exactly one day accordingly),
and sub-day DST offsets are immaterial at day grain.

Nothing here changes a keeper, an extract, a default, or the guard. No LP
solve was run. No out-of-training year was touched. No dashboard registration
(findings-only session; rule 15 covers runs, not probes).

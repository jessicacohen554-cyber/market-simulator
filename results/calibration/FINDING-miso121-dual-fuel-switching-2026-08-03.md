# FINDING — miso-121: `dual_fuel_switching` at MISO is **FULLY IDENTIFIED but PRICE-INERT** → cell `U` → **`I`**

**Session:** miso-121, branch `claude/miso-121-dual-fuel-switching-bxpjo2`, off
`origin/main` at `f0b8c02`. **Keeper under test and UNCHANGED:**
`2026-08-03-miso-117b-ct-heat` (`results/calibration/miso117_ctheatrate_B`,
determination NOT-YET, sole FAIL C7 `COAL_PRB` ×3y, ledgered caveats 2/3
`{C3a, C3c}`).

**Pre-registration:** `PREREG-miso121-dual-fuel-switching-2026-08-03.md`,
written, committed and pushed **before any measurement**; its §8 amendment
fixed the Phase-1 gates K1–K7 and the disposition rule **before either arm
solved**. Nothing in §5 or §8.3 was re-designed after a number existed.

**Registered runs (rule 15):**

| arm | run id | bundle |
|---|---|---|
| A (control) | `2026-08-03-miso-121a-control` | `results/calibration/miso121_control_A` |
| B (treatment) | `2026-08-03-miso-121b-dual-fuel` | `results/calibration/miso121_dualfuel_B` |

---

## 1 — The verdict, and the rule that produced it

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — B records `dual_fuel_switching=true`, A `false`; both siblings (`dual_fuel_oil_reattribution`, `dual_fuel_oil_daily_parity`) OFF in **both** arms (rule 19) |
| **K2** control integrity | **PASS** — scorecard basis (same determination, all nine criterion statuses) **and** the strict-byte basis: **max \|Δ MW\| = 0.000000 on every one of 148,920 class-hours, all three years** |
| **K3** liveness | **FAIL** — dispatch leg clears 50 MW in **2024 alone** (0.0 / 912.5 / 16.0 MW); **price leg fails in every year: max zonal \|Δλ\| 0.0000 / 0.0003 / 0.0000 $/MWh vs the 0.10 bar** |
| **K4** single delta | **PASS** — the two scenario blocks differ in exactly one key |
| **K5** year span | **PASS** — both bundles `[2023, 2024, 2025]` (rules 16 / 22) |
| **K6** direction integrity | **PASS** — one-sided as the arithmetic requires: system λ never rises (0.0000 / −0.0003 / 0.0000) |
| **P1–P6** kills | **ALL PASS** — no kill fires |

**Disposition, by §8.4's pre-committed rule verbatim — *"K3 fails → cell `U` →
`I`, keeper unchanged, arm registered"*:** the MISO `dual_fuel_switching` cell
moves **`U` → `I`**. Arm B is **not promoted**. Keeper unchanged.

Every criterion is identical across keeper, control and arm:
`fuelmix PASS · sysvol PASS · price_mean CAVEAT · price_shape PASS ·
price_tail CAVEAT · dispatch_corr PASS · governance PASS · shape FAIL ·
forced_share PASS`; determination NOT-YET in all three.

---

## 2 — Nothing in the identification is retracted, and that is the point

This is **not** a mechanism that failed to identify. All three legs the queue
asked about are identified from **MISO's own data**, with **zero free
parameters**:

* **(a) CAPABILITY** — 371 / 371 / 369 gas tranches, **15,827 MW = 23.3 % of
  MISO gas capacity**, per-plant from the EIA-860 Multifuel schedule
  (`Switch Between Oil and Natural Gas? = Y` on a gas-primary unit).
* **(b) SWITCH PRICE** — **12 of 12 measured MISO F923 Petroleum months in
  every year** (20.36 / 18.22 / 17.21 $/MMBtu). The flat national
  `OIL_PRICE_PER_MMBTU` fallback is **never reached**. Rule 13 admissible: the
  forward analogue is an oil trajectory × the same capability roster.
* **(c) EVENT WINDOWS** — **observable in MISO's own CAMPD feed**:
  **90 / 459 / 452** gas-labelled unit-hours across **25 / 43 / 40 distinct
  units** lift from a p50 of **53.91 kg CO₂/MMBtu** (pipeline gas; EPA
  40 CFR 98 factor 53.06) into the **70–80 distillate band** — validated
  against CAMPD's **own** diesel-labelled units at p50 **73.65 / 73.46 /
  73.65**.

And the mechanism **genuinely fires**: the solve logs the cap applied to
371 / 371 / 369 tranches (15,827 / 15,827 / 15,825 MW), matching the Phase-0
census exactly. The miso-113 *"hook wired into `runner.py` only, invisible to
the calibration path"* hazard was checked for in advance and is **cleared by
measurement**, not by code-reading. The fuel deltas are enormous: max
**197.8 / 107.9 / 45.9 $/MMBtu**, delivered gas reaching 218.9 $/MMBtu against
oil at 17.7.

**A fully-identified, correctly-wired, genuinely-firing mechanism can still be
inert.** That is this row's result.

---

## 3 — MISO is inert for a **different reason** than the zonal anchor, and the two must not be conflated

`gas_offer_margin_zonal_anchor` (miso-119/120) is inert because a mean-zero
perturbation never reaches the price-setting tranches — a statement about
*where the perturbation lands*.

**This mechanism is inert because the underlying physical phenomenon is
negligible at MISO's scale** — a statement about *how big the real thing is*.
CAMPD's own meters put observed dual-fuel oil generation at **0.0023 / 0.0113 /
0.0128 TWh a year**, against ~17–23 TWh of capable-unit generation and a MISO
load in the hundreds of TWh: **of order 0.002 % of ISO energy.** No mechanism
reproducing a 0.002 % phenomenon can move an ISO-level annual price criterion,
however well identified it is.

That distinction is recorded so neither verdict is quoted as evidence for the
other (the rule-25 discipline applied *within* an ISO).

---

## 4 — The pre-registered over-switching risk did **not** materialise

K7 was written reported-only because Phase 0 could only set the model's binding
**tranche**-hours against CAMPD's observed **unit**-hours — incomparable
grains. The Phase-1 bundles carry `unit_hourly` sidecars the keeper lacks, so
the comparison is now **same-grain, in MWh**:

| year | model switched | CAMPD observed | ratio |
|---|---|---|---|
| 2023 | 0.00013 TWh | 0.00233 TWh | **0.06× (under-switches)** |
| 2024 | 0.03757 TWh | 0.01133 TWh | 3.3× |
| 2025 | 0.01096 TWh | 0.01284 TWh | **0.85×** |

CAMPD is a **stated lower bound** (only 49 of the 89 capable plants report to
it). The model does not systematically over-switch; in 2023 it under-switches.
**The risk named in advance as a possible black mark is reported as cleared.**

---

## 5 — The screen's own liveness statistic FAILED, against interest

This is the transferable lesson, and it is a **direct extension of the
miso-119 DO-NOT-REDO**.

§8.1 could not run L5 literally (the keeper bundle commits no generator-grain
P1 dispatch) and substituted **the p50 of \|Δoffer\| over BINDING gen-hours**:
**64.30 / 93.93 / 108.23 $/MWh** against a 0.10 bar. The realized price effect
is **0.0003 $/MWh** — the substitute over-predicted by roughly **five orders of
magnitude**.

miso-119 established that `max |Δoffer|` is an upper bound only and named the
capacity-weighted p50 as *"the predictive statistic"*. **The p50 over BINDING
hours is not predictive either — because binding is not marginality.**
Measured on the arms' own `unit_hourly` sidecars, the share of binding
tranche-hours that are also **partially loaded** (`0 < mw < cap_mw`, i.e.
genuinely price-setting) is:

| year | marginal ∧ binding | of binding | share | literal-L5 capw p50 |
|---|---|---|---|---|
| 2023 | **0** | 15,792 | **0.00 %** | undefined → predicts INERT ✓ |
| 2024 | 225 | 18,192 | 1.24 % | 1.29 $/MWh |
| 2025 | 63 | 11,568 | 0.54 % | 18.74 $/MWh |

In 2023 **no capable tranche is ever both binding and marginal**, which is
exactly why that year's price delta is an *exact* 0.0000. The literal L5 is a
large improvement — it calls 2023 correctly — but it would **still not have
prevented these solves**, passing in 2024 and 2025.

**DO-NOT-REDO, recorded for this row and the offer-perturbation class
generally:** the predictive ex-ante statistic is the **marginal share of
binding hours**, not any percentile of the offer delta. No future screen may
argue liveness from `max |Δoffer|` (miso-119) **or** from a binding-hour
percentile (this session). A sharper screen conditions on the P1 loading state
of the perturbed tranches.

---

## 6 — What moved (REPORTED; none of it is banked)

The direction and locus are **exactly** what the mechanism's arithmetic
requires, at an inert magnitude:

* **One-sided (K6).** The cap can only *lower* a capable unit's delivered fuel
  price, so system λ never rises: **0.0000 / −0.0003 / 0.0000 $/MWh**.
* **Winter-only.** The entire price effect sits in **winter 2024
  (−0.0013 $/MWh)** and is **exactly 0.0000 in every other season-year** — the
  locus the mechanism claims (cold-snap Chicago-citygate gas spikes past oil
  parity).
* **Dispatch.** 2024 only, ±0.0002 TWh: `CC_REGULAR` −0.0002 / `CT_PEAKER`
  +0.0002, `CC_CHP` −0.0001 / `ST_CHP` +0.0001.
* **P4 on the delta:** slack+dump **identical** between arms (0.0 / 19,059.283
  / 0.0 MWh in both) — the arm costs nothing at the scarcity edge.

**C7 `COAL_PRB` is untouched, exactly as pre-declared** (§6 P6 disclaimed any
C7 claim in either direction). It FAILs in both arms in all three years. **This
lever was never a C7 instrument and did not become one.** The C7 residual stays
where miso-113 routed it: the data-blocked miso-78/79 congestion +
sub-hourly-RT lane.

---

## 7 — Governance

* **Rule 15** — both arms registered in this session; top-15 MISO retention
  honoured (pruned `2026-07-28-miso-99b-chp-power` and
  `2026-07-29-miso-102b-sunkfixed`; neither is the keeper).
* **Rule 16** — one bundle each, `[2023, 2024, 2025]`, one invocation, years
  sequential inside it. **A per-year invocation chain was DISCARDED and both
  arms re-solved from scratch:** `replay_keeper` sets
  `kwargs["years"] = args.years`, so a `--years <one>` invocation writes
  `meta.json` with only that year — the sidecars accumulate but the provenance
  does not, and the finished bundle would have claimed `years: [2025]`,
  mis-stating K5 and rule 16. The only after-the-fact remedy would have been
  hand-editing a provenance artifact.
* **Rule 19 `[R-ONE-MECH]`** — nothing stacked; both sibling cells stay OFF in
  both arms and neither is adjudicated here.
* **Rule 21 `[R-DOF]`** — both arms carry a DOF ledger; arm B's one new entry
  (`dual_fuel_switching (MISO)`) is `measured/published` with
  `free_parameters_added: 0`. `n_residual` unchanged.
* **Rule 23 `[R-FROZEN-DERIVE]`** — the capable set is EIA-860's own boolean
  field and the parity price is MISO's own F923 receipt; neither was swept, and
  neither is re-derived against this arm's inert outcome (P5 holds).
* **Rule 25 `[R-ISO-SCOPE]`** — MISO's capability and oil price from MISO's own
  data. The PJM / NYISO / NEISO `K` verdicts on this row transferred nothing,
  and this `I` does not weaken them: their dual-fuel fleets sit on winter hub
  spreads (AGT / Transco) whose scale MISO's does not match.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only, in every phase. MISO holds no
  `calibration-complete` marker; Elliott (Dec 2022) was declared out of scope
  at §3 and never read.
* **Rule 28 duty (b)** — the matrix cell is stamped in this session.
* **Contamination declared** — this session read the miso-119/120 finding, the
  MISO lever queue, the matrix row and the mechanism's source before acting.
  What protects the result is that the decision rule was fixed by a
  pre-registration written before any measured quantity existed, and applied
  verbatim.

**Two probe defects were found and fixed BEFORE any adjudication**, both of
which would have produced a **wrong `I` on leg (c)**: (i) CAMPD's `facilityId`
is string-typed, so an int-valued filter matched **zero** rows — a hard-fail
guard now prevents route I-D firing on an empty query; (ii) the roster keys
**plants**, and MISO dual-fuel plants host **coal** units whose CO₂ intensity
(93–97 kg/MMBtu) sits **above** oil, so an open-ended threshold booked coal as
oil and over-counted **13×** (6,181 → 459 in 2024).

---

## 8 — Disposition and DO-NOT-REDO

**Cell:** `dual_fuel_switching` × MISO: **`U` → `I`**.
**Keeper:** unchanged (`2026-08-03-miso-117b-ct-heat`).
**Flag:** stays default-off, one CLI switch away.

**Do not re-test this cell without NEW evidence.** Admissible new evidence is
narrow and named:

* a **scored criterion at winter-event grain** (the rubric has none today —
  C3a/C3b/C3c are annual/ISO-level, and a 0.002 %-of-energy phenomenon cannot
  register there);
* a mechanism that **raises MISO's delivered winter gas** materially further
  past oil parity **under its own charter** (this row does not license one);
* an owner override of the prereg's K3 rule.

**Not** admissible: re-running the arm, sweeping anything (nothing here is
sweepable — both legs are measured registries), or arguing from the correct
one-sided direction and winter-only locus, which are already reported here and
did not make the mechanism live.

**A note for whoever revisits this on rule-1 grounds.** The mechanism is
structurally faithful, measured, zero-free-parameter, and reproduces observed
MISO behaviour at the right order of magnitude — it is *costless* to arm and
changes no score. Whether a keeper should therefore carry it as correct market
structure rather than leave it off is an **owner call**, not a session call,
and this session does not make it: the prereg's rule was `I`, keeper unchanged,
and that is what was applied.

**Every standing MISO bar carries forward unchanged:** the h14-21 `CT_PEAKER`
floor limb is not relaxed and `min_stable_pct` is not re-derived
(rules 1/14/23/25); `CC_CHP` volume and heat-rate questions stay closed
(miso-116/118); the trough-quantity question stays closed (miso-115/116);
`CT_CHP`/`ST_CHP` ratios stay VOID; `miso_cc_coal_rebalance`,
`miso_firm_import_floor` and `miso_pjm_lmp_import_pricing` stay refused; the
seam hod mis-shape stays unchartered; miso-89 stays ledgered; the regulated-PRB
family stays SPENT; `gas_offer_margin_zonal_anchor` stays `I`.

**Live queue head after this:** the **55088 Dearborn hybrid-cogen scope gate**
(miso-118 §5, named not chartered) — 13–17 % of CEMS fuel in zero-output
boilers inside the topping rate, so `CC_CHP`/`CT_CHP` tranches are +13–20 % too
dear; 1 of 14 plants, 515 MW. It needs its own pre-registration plus a derive
SCOPE-GATE change, admissible on rule 14 `[R-ACCURATE]` only, and rule 23
forbids re-deriving at a residual.

**Artifacts:** `_miso121_dual_fuel_ab.json` (the scored gates),
`_miso121_switched_volume.json` (K7 same-grain + literal L5),
`_miso121_dual_fuel_screen.json` + `PROBE-miso121-dual-fuel-screen-2026-08-03.txt`
(Phase 0), `PREREG-miso121-dual-fuel-switching-2026-08-03.md`,
`scripts/probes/_miso121_dual_fuel_screen.py`,
`scripts/probes/_miso121_dual_fuel_ab.py`,
`scripts/probes/_miso121_switched_volume.py`,
`scripts/gen_miso121_attestation.py`.

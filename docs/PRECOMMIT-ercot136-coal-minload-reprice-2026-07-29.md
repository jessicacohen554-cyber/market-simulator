# PRE-COMMIT — ERCOT-136 Phase 2: reprice the coal take-or-pay band onto its measured RT level

**Date** 2026-07-29 · **ISO** ERCOT · **Lane** ercot136-coal-headroom-conduct ·
**Status** **PRE-REGISTERED, NOT EXECUTED — BLOCKED ON THE SAME OWNER RULING (§0).**
Written and pushed **before any solve**. ·
**Phase 1** `docs/DIAGNOSIS-ercot136-coal-headroom-conduct-2026-07-29.md` ·
**Keeper** `2026-07-28-ercot116-regate-base` — **not touched by this document.**

---

## 0. The blocking gate — unchanged from ERCOT-135 §0, and it still binds

This arm **may not be solved** until the owner rules on **ERCOT-116 adoption**
(`ercot_thermal_dam_availability_coal`; `run_config.json` confirms it is `False`
in the keeper). The dependency is methodological, not procedural: on the pinned
fleet ~31/33/45 % of online coal plant-hours sit at the availability ceiling, so
an offer-curve change **cannot move them**, and any apparent gain would measure
the estimate rather than the mechanism (rule 14 `[R-ACCURATE]`).

Phase 1 does **not** lift that gate — it changes *which* arm is worth running
once the gate lifts. **ERCOT-135's Phase-2 width arm is superseded by this one**
(§6).

**If ADOPT** — proceed exactly as §§1–5, envelope ARMED in both arms.
**If DO-NOT-ADOPT** — this arm is **withdrawn, not re-scoped to the pinned
fleet.** A shape lever validated on a pinned block is not evidence
(`DIAGNOSIS-ercot134` §8).

## 1. The hypothesis, stated so it can fail

**H.** ERCOT coal's band-uniform over-run is caused by the **take-or-pay price
discount**, not by the take-or-pay *block*. The model prices **30 %** of coal
capacity at **$4.50/MWh** (`coal_tranche_1_fuel_passthrough = 0.00`, VOM only)
while the real fleet offers only **5.8–8.4 %** of its capability at or below
$4.50 and anchors its RT curve at a capacity-weighted p50 of **$15.00–16.86**
(Phase 1 §3). Because the block is **already floored twice**
(`ercot_coal_min_config_floor`, `coal_mustrun_per_plant` — Phase 1 §6), the
discount is redundant as a must-run device and survives only as a merit-order
distortion.

**H is FALSE if** repricing the band moves every price band roughly equally —
that is a level lever's signature, and ERCOT-132 leg B already refuted the level
on this class. In that case the defect is on the **gas side** of the ranking.

## 2. The arm

**Single delta**, on the keeper recipe with the ERCOT-116 envelope ARMED in
**both** arms:

* **BASE** = keeper recipe + `ercot_thermal_dam_availability_coal=true` — i.e.
  the registered `2026-07-28-ercot116-regate-arm` configuration re-solved fresh
  at HEAD. It is the correct control because the comparison must be made on the
  un-pinned fleet.
* **ARM** = BASE + `coal_tranche_1_fuel_passthrough` moved from its **fitted
  0.00** to the value that lands the fleet's resolved tranche-1 bid on the
  **measured RT curve bottom** (`Submitted TPO-Price1`, capacity-weighted p50,
  98.8–100 % coverage).

**Why this specific parameterisation:**

* **Zero new fields, zero new DOF.** `coal_tranche_1_fuel_passthrough` is an
  existing registered `ScenarioConfig` scalar (`scenarios.py:4854`). The change
  **retires a fitted value** — 0.00 asserts that ERCOT coal's min-load MWh costs
  nothing but VOM, which no measurement supports — and replaces it with a
  measured one. Per rule 21 `[R-DOF]` the residual-identified count must **fall
  by one, not rise** (gate (f)).
* **One scalar, not a per-plant surface.** A per-plant passthrough would be a new
  off-registry tuning channel (rule 24 `[R-REGISTRY]`). One ISO-level scalar,
  resolved and verifiable in `run_config.json`, is the minimal change.
* **`coal_tranche_1_frac` is NOT touched.** Phase 1 §4 / ERCOT-135 §4 measured
  the model's 0.30 as *smaller* than the measured min-load share (0.425–0.457
  here). Moving the share and the price together would be two mechanisms on one
  phenomenon (rule 19 `[R-ONE-MECH]`). **The share stays; only the price moves.**

**Explicitly NOT in the arm** (each already adjudicated): the offer LEVEL rebasis
(ercot132 leg B, CLOSED); the pooled `econ_high` 2.856 (ercot122 §5.2, barred);
the PRB/lignite passthrough sigmoid floors 0.76/0.675; any availability lever;
any new floor (Phase 1 §6 is an argument for *removing* a mechanism, and adding
a third floor would be the exact rule-19 stack it warns against).

## 3. Predictions — per band, written before the solve

Bands are `ercot127`'s fixed edges (`<15, 15-20, 20-25, 25-30, 30-35, 35-50,
>=50`), scored by `ercot128` §H (G1, fleet-aggregate loading vs RT price) against
the same actuals. BASE is the ERCOT-134 arm: **G1 1/21**, coal
**+6.5/+9.6/+11.4 TWh**, **C3a −35.3/−14.7/−13.2 %**.

| # | prediction |
|---|---|
| **P1** | **Arming + bite.** `run_config.json` carries the resolved passthrough and the resolved tranche-1 band; coal energy **falls** vs BASE by **4–10 TWh/yr**. |
| **P2** | **G1 improves from BASE's 1/21, landing 8–16/21.** Direction is the load-bearing claim; the range is honest uncertainty. |
| **P3** | **The improvement is concentrated in the LOW and MID bands** (`<15`, `15-20`, `20-25`) — where a \$4.50 block clears and a \$16 block does not. The `>=50` band moves **least** (< 3 pp): at scarcity prices both bids clear. |
| **P4** | **C1 coal returns toward band**: ARM lands within **±3.0 TWh** in all three years. |
| **P5** | **C3a improves** vs BASE by **≥ 4 pp** in every year — removing cheap coal lets gas set price more often. |
| **P6** | **Pin / impossible statistics UNCHANGED** vs BASE (within ±10 %): this arm touches price only. Scored by `ercot134_coal_availability_pin --bundle`. |
| **P7** | **ERCOT-116 shape metrics do not regress**: matched-band excess and monthly-ratio spread within 2.0 pp / 0.05 of BASE. |
| **P8** | **Basis check — the ERCOT-132-leg-B failure mode does not recur.** The **resolved** tranche-1 bid, read back from `run_config.json` / the LP seam, lands within **±\$1.00** of the measured `TPO-Price1` cap-weighted p50 in each year. (Leg B failed precisely here: a measured \$20.48 landed at \$23.38 through a basis mismatch.) |
| **P9** | **The model's cheap share collapses onto the measured one.** Re-running `ercot136_coal_headroom_conduct.py`'s §H comparison against the ARM's seam capture, the model's share offered ≤\$4.50 falls from **0.30** to **≤0.10**, against the measured 0.058–0.084. |

**Falsifier.** If G1 stays **≤ 3/21**, or the improvement is *uniform* across
bands rather than low/mid-concentrated (P3), **H is refuted**: a shape lever that
moves every band equally is behaving like a level lever, which ERCOT-132 leg B
already refuted, and the real defect is then on the **gas side** of the ranking.

## 4. The decision rule — fixed now

**Adoption requires ALL of:**

| # | criterion |
|---|---|
| (a) | **P1** holds — armed, in `run_config.json`, and biting. |
| (b) | **G1 ≥ 8/21** AND strictly better than BASE. |
| (c) | **P3** holds — the low/mid bands carry the improvement. |
| (d) | **No new C-gate FAIL** vs BASE. |
| (e) | **LOYO, per-year, 2-of-3 is FAIL.** The parameter is identified on **2024–2025 SCED only**, so its 2023 application is an **extrapolation**. This is the stricter gate `DIAGNOSIS-ercot123` §7.2 fixed for exactly this situation, and it is adopted verbatim — **not** the ordinary "at most one year may regress". |
| (f) | **DOF ledger does not grow, and should SHRINK** (rule 21): the transplanted level is a measured input with `lineage_solves 0`, so the residual-identified count must fall by one (the retired 0.00), never rise. |
| (g) | **P8** holds — the resolved band lands on the measured value. A basis-mismatched transplant is rejected even if the gates pass (the ercot132-leg-B precedent). |

A C1 or price-MAE gain **does not** license the mechanism if (b)/(c)/(e)/(g)
fail. The gates are fixed before the numbers exist precisely so a fit gain cannot
be retro-fitted into a justification (rule 1 `[R-STRUCT]`; the ercot132-leg-B
precedent, where C1 improved and the arm was still correctly rejected).

## 5. Execution constraints

Full span {2023, 2024, 2025} in ONE bundle per arm, years **sequential**, arms
sequential (rules 12/16). Both arms registered on the backcast dashboard with
hand-written sidecar definitions, rejection included (rule 15). Matrix cell
updated in the same session (rule 26b). Solves in-session, never CI. No holdout
year touched (rule 22). No keeper file touched without owner sign-off.

## 6. Relationship to the superseded ERCOT-135 Phase-2 arm

`PRECOMMIT-ercot135` proposed moving tranche-1 onto the measured **submitted DAM
offer floor** (~\$20.5). That arm is **superseded, not withdrawn on its merits**,
for two measured reasons from Phase 1:

1. **Wrong instrument.** The DAM corpus covers only 27.8–39.1 % of committed coal
   resource-hours; the RT corpus covers **98.8–100 %**. ERCOT coal transacts its
   incremental energy in real time (ERCOT-123 §7.1, reproduced at Phase 1 §1), so
   the RT curve bottom is the right anchor and the DAM submitted floor is a
   minority statistic.
2. **Wrong level, by ~\$4–5.** The measured RT anchor is **\$15.00–16.86**, not
   ~\$20.5. Using the DAM number would over-correct.

ERCOT-135's §6 constraint on any successor is **met** by this arm: it targets
curve **shape**, it has a pre-registered magnitude (the 3.2–4.2 GW excess, now
independently confirmed at 22–24 pp from the RT side, Phase 1 §5), and the
conduct question it said must be settled first **has been settled** (Phase 1 §§1–3).

## 7. The honest limit of this arm — stated before it runs

* **It cannot fix a gas-side defect.** If P3 fails, the residual is the gas
  offer surface's, and the successor is `FINDING-ercot117` §5.1 (the gas rebasis),
  not another coal probe. Coal's enumeration is otherwise exhausted
  (ERCOT-122…136).
* **The 2023 application is an extrapolation** and gate (e) is deliberately
  strict about it. No 2023 SCED disclosure exists on disk and none is sought:
  intake of an out-of-training year would need its own owner authorisation
  (rule 22), and 2023 is in-training, so the constraint here is data existence,
  not governance.
* **Even full adoption leaves C6 UNATTESTED** while residual-identified DOF
  entries persist, and leaves the C3c scarcity tail where ERCOT-99/101/107/108
  attributed it. Recorded so a pass is not over-claimed.

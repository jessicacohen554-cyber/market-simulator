# FINDING miso-228 phase 0 — THE CT_PEAKER ROOT CAUSE IS **OFFER LEVEL**, NOT A HOLD: the LP dispatches **more** CT than is in merit and leaves only **0.020 TWh** of in-merit headroom. The missing structure is the one band CT_PEAKER alone lacks — a measured per-plant must-run. **ZERO LP MINUTES. No arm run, nothing promoted, nothing licensed.**

**KEEPER UNCHANGED → `2026-09-05-miso-220-nonsteam-lift`** (CALIBRATED). This is the phase 0 of
the owner's decision of 2026-09-06 on the miso-227 escalation — option (c), *"fix CT_PEAKER,
then promote the pair"*, which is rule 1 `[R-STRUCT]`'s own prescription (*a real market
behaviour stays in even if it makes the fit worse — then fix the actual root cause*). Rule 29
clause 0: a zero-LP phase 0 runs before any solve is spent, and this one **killed the
session's own leading hypothesis** before it reached an LP.

Instrument: `scripts/probes/_miso228_ctpeaker_gap_phase0.py` → `_miso228_ctpeaker_gap.json`,
plus the committed `unit_hourly` / `class_band_hourly` sidecars.

---

## 0. The question, and the answer that reversed the hypothesis

miso-227 scored NOT-YET on one cell: CT_PEAKER-2023 at −8.29 TWh against ±8.00. The keeper
misses that class in **every** year — 2023 9.05 vs 17.04, 2024 13.12 vs 19.23, 2025 13.89 vs
19.29 — so the cell is a pre-existing ~8 TWh defect that the seam arm merely tipped over an
administrative line. This asked which half of the model owns it.

**The hypothesis this session opened with was wrong, and the LP said so.** A static merit
integration suggested CT_PEAKER was uniquely *under-dispatched* relative to its in-merit energy
(ratio 0.708 against CC_REGULAR's 0.999), which pointed at something holding in-merit capacity
out of dispatch — reserve co-optimization the obvious suspect. **The LP's own committed
`unit_hourly` refutes it:**

| CT_PEAKER, 2023, from the LP's own rows | TWh |
|---|---:|
| dispatched | **8.752** |
| capacity in merit (`mc < zone price`) | **7.158** |
| in-merit but UNDISPATCHED headroom | **0.020** |
| … of which carries a positive reduced cost | 0.003 |

**The model dispatches MORE CT than is in merit** (the excess is the committed/forced band) and
leaves 0.020 TWh — two tenths of one percent of the 8 TWh gap — unclaimed. **Nothing is holding
CT_PEAKER back.**

**Why the static probe misled, recorded so the next session does not repeat it.** It cleared
the **P0 base** offer basis (what `build_year` assembles) against **P1** prices. P1 is the
bid-cost pass — base **plus** the amortized startup markup — and that markup is class-dependent:
**CT_PEAKER +$4.51/MWh against CC_REGULAR's +$3.53** (cap-weighted). Comparing a P0 stack to a
P1 price manufactures phantom in-merit capacity, and it does so *worst* for the class with the
largest markup, which is exactly the class under investigation. **A merit test must clear the
same basis the price was formed on.** This is the sibling of miso-224's "assert liveness on the
chain the solve runs" and miso-225's "assert invariants where the config is complete".

## 1. So the defect is the OFFER LEVEL — and the real fleet is not energy-merit-driven at all

CT_PEAKER's modelled offers sit far above the price in the hours the real fleet ran
(2023, cap-weighted): P1 bid **$77.76**, percentiles p5 $36.9 / p25 $47.5 / p50 $57.8 / p75
$105.4, against a model price mean of **$34.64** and a measured hub mean of **$31.79**.

The corroborating measurement is already on the record: miso-224 §(ii) measured the **real**
market clearing **$10–20 in 1,765 hours of 2023** — below every thermal SRMC the model carries —
while the real CT fleet produced **17.0 TWh**. **Real MISO CTs run at prices far under their own
delivered incremental cost.** That is not an energy-merit outcome and no offer level can
reproduce it: it is self-commitment / RA / local-reliability / reserve-deployment duty.

Two consequences, both stated against the easy fix:

- **An offer haircut on CT_PEAKER is FORBIDDEN and would not even be right.** A multiplier tuned
  to close a volume residual is not the rule-1 authorized channel (that carve-out is price, one
  config, declared ex ante, never swept), and rule 13 `[R-MEASURED]` bars an adder tuned to a
  residual outright. It would also be modelling the wrong thing: the real energy is not priced
  into merit, it is committed.
- **The gap is not uniform across years and the offer stack is not uniformly wrong.** At the
  model's own price the P0 static reaches 19.50 TWh in 2025 against a 19.29 actual — the stack
  can reach the measured energy there — while 2023 falls short even at the *measured* price.
  Any fix must be checked per year, not fitted to 2023.

## 2. THE MISSING STRUCTURE, named from the model's own band table

Every fossil class in the MISO keeper is split into a measured price-taker `mustrun` band, a
take-or-pay `committed` band and a rising `econ` ramp — **except CT_PEAKER, which has no
`mustrun` band at all** (2023, TWh):

| class | `mustrun` | `committed` |
|---|---:|---:|
| COAL_PRB | **41.870** | 51.877 |
| COAL_BIT | **24.122** | 26.168 |
| COAL_LIGNITE | **2.471** | 2.868 |
| CC_REGULAR | 0.000 | 66.790 |
| **CT_PEAKER** | **0.000** | 2.487 |

And the keeper's own config says why: **`coal_mustrun_per_plant: True`**,
`st_gas_mustrun_per_plant: True`, **`ct_mustrun_per_plant: False`**.

Coal's band is miso-53's adjudicated representation — the per-plant CAMPD `_mustrun` fuel-free
price-taker band, measured from unit conduct, 29.3 % cap-weighted over 44 of 57 plants. It is
precisely the mechanism that lets a class run through hours its own offer loses **without a
floor and without a fitted adder**, and it is the structural analogue of what the real CT fleet
is observably doing. **CT_PEAKER is the one material class that does not have it.**

## 3. WHAT THIS DOES NOT LICENSE — the arm is NOT cleared, and that is why none was run

`ct_mustrun_per_plant` is an **existing registered `ScenarioConfig` field**, so arming it mints
no new tuning channel. But it is **not cleared to run**, on two counts found in this phase 0:

1. **It has NO matrix row in ANY ISO** (`mechanism-matrix.js` has no `ct_mustrun_per_plant`
   entry; every per-ISO shard reads absent). It is therefore **unadjudicated** — proposing it is
   not a rule-28 DO-NOT-REDO violation — but a PR that arms it owes the base row plus a cell
   line in all six shards, in the same PR (rule 28c).
2. **An open rule-13 `[R-MEASURED]` question is already on the record against it.** The ERCOT
   `scuc_load_pocket_commitment` cell distinguishes its own measured-instruction-state form from
   *"`ct_mustrun_per_plant` (**annual outcome commitment**)"*. If the band is keyed to an annual
   **outcome**, that is the shape rule 13 forbids — a measured outcome fed back to make the
   model reproduce it — and it would fail admissibility however good the fit. **This must be
   settled by reading the derive before an LP is spent**, and it is the first thing the
   successor does.

**Nothing here is a proposal.** No arm was run, no field was flipped, no bundle was produced,
the keeper is untouched, and the DOF ledger is unchanged at 41/2.

## 4. Governance

Zero LP minutes. Rule 29 clause 0: the phase 0 ran first and **falsified the session's own
hypothesis** at no solve cost — the outcome the clause exists to produce. Rule 19
`[R-ONE-MECH]`: what already floors CT_PEAKER is enumerated before anything is proposed — C8
reports it at **27.6 / 18.6 / 15.6 %** forced across 2023–25, *grounded* (every binding
mechanism clears D-4, profile r 0.93/0.96/0.98), so a new floor would stack on a mechanism that
is already working and already the fleet's largest forced share; the missing piece is an
**offer-side** band, not another floor. Rule 13: the admissibility question on the candidate
lever is raised **before** it is armed, not after it fits. Rule 22: 2023–2025 only. Rule 27
`[R-PUSH]`: files edited locally, pushed as on-disk bytes, blobs verified.

**Reported against this session**: the leading hypothesis it opened with (reserve
co-optimization withholding in-merit CT capacity) is **refuted by the LP's own reduced costs**
and is recorded here as refuted rather than quietly dropped; the static instrument that produced
it carried a P0-basis-versus-P1-price defect, stated in §0 with the measurement that exposes it.

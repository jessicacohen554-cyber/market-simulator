# nyiso-96 — the CT start-frequency lane: characterisation, and the fast-start amortization verdict

**Lane:** NYISO C3c, queue item 2 — CT start frequency
(`docs/mechanism-testing-matrix.md` §5.5).
**Keeper:** `2026-07-28-nyiso-92-hydro-envelope`
(`results/calibration/nyiso92_hydro_envfloor`), verified against
`frontend/data/backcast/keepers/NYISO.json` before any work was done.
**Pre-registration:** `docs/handoffs/nyiso96-preregistration.md` (written before
the A/B was launched).

---

## 1. What this session was asked to settle

C3c is NYISO's sole determination blocker and the lane has no remaining
congestion lever — items 1 (DA virtual depth, nyiso-94) and 1b (TSA transfer
derate, nyiso-95) are both closed ex ante on identification. The surviving
candidates are offer/commitment-side, and the head of the queue is the CT
start-frequency defect: the model starts the CT fleet far less often than
measured, and a majority of measured CT energy clears below its own SRMC.

The charter required the characterisation to **choose between two incompatible
lever families before anything was built**:

* **start economics** — start costs mispriced, so the marginal start decision is
  wrong. Instrument: `tranche_startup_amortization` (queue item 3). Signature:
  below-SRMC energy CONCENTRATED in a few short, high-value blocks.
* **commitment/obligation** — the fleet is online for a non-energy reason, so no
  offer-side price reaches it. Signature: below-SRMC energy SPREAD FLAT, and
  missing starts landing in hours the model already prices above class SRMC.

## 2. Characterisation (no LP spent — the keeper's committed sidecars)

`scripts/probes/nyiso96_ct_start_characterization.py` and
`nyiso96_ct_offer_reveal.py`, both reading only committed artifacts: the
keeper's own `unit_hourly_*` / `system_*` sidecars, the CAMPD bench, the
committed measured CT heat-rate table, the scored LMP parquet, and the keeper's
own downstate-CT delivered-gas seam — so the SRMC each plant is judged against
is the cost the LP charges it.

**The start deficit, plant-grain, on a common online bar:**

| year | measured starts | model starts | ratio | measured TWh | model TWh |
|------|-----------------|--------------|-------|--------------|-----------|
| 2023 | 3,737 | 987 | 3.79x | 1.880 | 0.323 |
| 2024 | 3,796 | 894 | 4.25x | 1.759 | 0.305 |
| 2025 | 3,528 | 2,048 | 1.72x | 2.217 | 1.070 |

**The run lengths are already right.** Model median run 6 h against a measured
5 h in every year; mean 6.29/6.26/8.62 vs 6.62/6.40/7.83; p90 11/11/16 vs
14/14/15. The model's blocks have the right *duration* — it simply makes about
a quarter as many of them. (This independently reproduces nyiso-90 §2 on a
different bar and a different keeper.)

**The decisive test — where the missing starts sit relative to the model's own
price.** Of the missing CT_PEAKER online-hours, the share in hours where the
model's own zonal price is **BELOW** the plant's measured SRMC:

| year | model price ≥ SRMC | model price < SRMC | share below |
|------|--------------------|--------------------|-------------|
| 2023 | 2,955 | 17,958 | 85.9 % |
| 2024 | 3,810 | 17,187 | 81.9 % |
| 2025 | 2,472 | 17,637 | 87.7 % |

**The below-SRMC energy is flat, not concentrated.** Ranking the measured
fleet's below-SRMC hours by depth, the deepest 10 % carry only 3.6/3.3/6.6 % of
that energy — barely above the same fleet's total-energy reference on the same
ranking (3.1/2.5/4.4 %). A start-recovery story concentrates its below-SRMC
energy in the tail of high-value blocks; this does the opposite.

**It is not an artifact of the hub price.** The scored series is the 11-zone
hub, but the fleet sits in NYC and Long Island. Measured from the raw 5-minute
RTD zonal files on disk, the sample premium is NYC $1.23/$2.80/$1.41 and Long
Island $7.42/$5.66/$2.10. Adding it, the share of measured CT energy clearing
**below its own SRMC at the fleet's own zonal price** is still
**66.0 / 52.6 / 53.0 %**. That number involves no model output at all.

**It is not availability.** CT_PEAKER class capacity in the keeper's sidecars
runs 2,131–2,350 MW against a p50 of ~2,197 — a ≤3 % derate. The class is
essentially fully available in the hours it is not started.

**Verdict of the characterisation: commitment/obligation, not start economics.**
Both discriminating signatures point the same way in all three years.

### 2a. One reading that does NOT survive, recorded so it is not repeated

The offer-side follow-up also measured each CT tranche's *capture rate* — the
share of hours where the model's own zonal price covers the plant's measured
SRMC in which the tranche actually produced. It comes back low (committed
0.05/0.05/0.08, econ 0.29–0.65, peak 0.015–0.019), which reads at first glance
as "the model bids its CTs above their own cost".

**That reading is wrong, and nyiso-91 §(i) already refuted it directly**: the
model's cheapest CT tranche is *measured* to bid at bare SRMC — the offer
intercept recovered from the solve returns VOM to the cent, `median offer −
direct = +0.00` in all three years. The capture-rate statistic is not
contradicting it. The denominator is affordability at the **plant** SRMC, while
each tranche carries its own heat-rate multiplier, so "affordable at plant
SRMC" is not "affordable at that tranche's own marginal cost"; the committed
and peak bands sit above the plant mean by construction. The capture rate is
therefore a description of the tranche ladder, **not** evidence of an
offer-curve markup to repair. There is no offer-level defect here, and this
session does not claim one.

## 3. Why the pre-identified lever was still tested, and what it is not

The characterisation selects the commitment family. Every commitment-side
candidate in reach is already adjudicated or governance-blocked:

* J/K in-city commitment obligation — built and tested (nyiso-83); moved
  CT_PEAKER by **+0.11 TWh** and was refuted as a floor substitute;
* published reserve tiers — closed in full (nyiso-84);
* `nyiso_gas_bridge_ct` day-ahead block commitment — built and eliminated
  (nyiso-90) at **+0.01–0.03 %** of the gap, because the runs it would extend
  are already the right length;
* windowed reliability floors — off by owner directive 2026-07-27, and rule 17
  [R-FLOOR-WINDOW] bars re-arming one to close this gap;
* the one surviving candidate — NYISO SCUC load-pocket security commitment with
  BPCG make-whole — is a sub-zonal data-intake and topology question needing
  owner scoping (nyiso-91), not a mechanism this session could build.

`tranche_startup_amortization` was therefore the last **buildable,
un-adjudicated, non-governance-blocked** cell in the queue, and it was tested to
close the matrix cell on a measured verdict rather than on direction alone.

**Rule 25 [R-ISO-SCOPE]:** no parameter is ported. The v3 measured basis reads
NYISO's own `campd_ct_run_lengths_NYISO.csv` (22 plants + a pooled class
fallback of 4.0 h, 34,057 measured runs); start costs are the already-cited NREL
table ($20/MW for CT_PEAKER/CT_CHP, $50/MW for the CC duct bands). Zero new
fitted scalars. Expected offer increment $20 ÷ ~4 h ≈ **$5/MWh**, as
pre-registered.

**Scope note.** The mechanism also carries the CC_REGULAR / CC_CHP **peak
(duct-burner)** band on the v2 P0 basis, so the delta is not CT-only; this is
the mechanism as designed, and it is why the CC classes move at all below.

---

## 4. A/B result

*(filled from `scripts/probes/nyiso96_ab_compare.py` — see §5 for the verdict.)*

---

## 5. Verdict

*(pending)*

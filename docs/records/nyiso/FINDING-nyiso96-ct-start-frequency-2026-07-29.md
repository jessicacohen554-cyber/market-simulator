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

Registered runs, same HEAD, all three years in one invocation each, one
mechanism-family apart: `2026-07-29-nyiso-96-control-zerodelta`
(`results/calibration/nyiso96_ctrl_zerodelta`) and
`2026-07-29-nyiso-96-ctamort` (`results/calibration/nyiso96_ctamort`).

**The control is a faithful baseline.** It reproduces the nyiso-92 keeper on
every number checked: CC_REGULAR 32.252 TWh in 2023, CT_PEAKER
0.524/0.459/1.516 TWh, C3c tail 3/0/7 h, C1 13/14 · free 9/10 with the sole
failing cell `2023 CC_REGULAR −3.05 TWh`.

**The mechanism is LIVE** (the nyiso-89 §4a check, run before anything was
read): max absolute hourly class delta 1,257 / 1,253 / 2,105 MW. This is not a
byte-identical no-op.

**CT_PEAKER, on one common bar (18/18/17 plants, both sides and the measured
series sharing one online threshold):**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| control TWh | 0.3234 | 0.3049 | 1.0696 |
| **arm TWh** | **0.2202** | **0.1875** | **0.7412** |
| Δ | −0.1032 (−32 %) | −0.1174 (−39 %) | −0.3284 (−31 %) |
| measured TWh | 1.8795 | 1.7588 | 2.2167 |
| control starts | 987 | 894 | 2,048 |
| **arm starts** | **719** | **582** | **1,453** |
| Δ | −268 (−27 %) | −312 (−35 %) | −595 (−29 %) |
| measured starts | 3,737 | 3,796 | 3,528 |
| start ratio | 3.79x → **5.20x** | 4.25x → **6.52x** | 1.72x → **2.43x** |

**Prediction 1 confirmed, and larger than forecast.** The pre-registration
expected "a few hundredths of a TWh"; the class actually loses 0.10–0.33 TWh,
about 6–20 % of its own gap, in the wrong direction. The start deficit — the
defect this lane exists to close — gets materially worse in every year.

**Prediction 2 confirmed.** Median run length 6→7 / 6→5 / 6→6 against a
measured 5 in every year: essentially unmoved, because the model's blocks were
already the right length and the v3 measured ceiling rarely binds.

**Prediction 3 REFUTED — and this is the decisive result.** C3c tail hours
>$300 are **3→3, 0→0, 7→7** against an actual 10/12/42. The lever buys
**exactly zero** tail hours. The one channel by which it could have helped the
lane's sole determination blocker is completely inert.

**Prediction 4 wrong in an important way — the arm CLOSES C1.** The displaced
energy lands on CC_REGULAR (+0.284/+0.496/+0.408 TWh) and ST_GAS
(+0.159/+0.183/+0.175), sourced from CT_PEAKER (−0.184/−0.190/−0.447), CT_CHP
(−0.121/−0.097/−0.056) and CC_CHP (−0.141/−0.363/−0.062). That +0.284 TWh walks
the knife-edge cell from −3.05 to −2.76 against its ±2.94 band, and it is the
control's ONLY failing C1 cell:

| criterion | control | arm |
|---|---|---|
| C1 fuel-mix (load-bearing) | **FAIL** (13/14 · free 9/10) | **PASS** (14/14 · free 10/10) |
| C3c price tail (supporting) | FAIL 3/0/7 | FAIL 3/0/7 — unchanged |
| C2 / C3a / C3b / C4 | PASS | PASS |
| C7 diurnal shape (D-1) | PASS | PASS |
| C8 forced share (D-2) | PASS | PASS |
| C6 governance | UNATTESTED (probe) | UNATTESTED (probe) |

**C1 is the ONLY criterion that differs between the two arms.** Every other
scored criterion — including both protective gates — is identical, so the whole
case for the arm rests on that single flipped cell, and the whole case against
it rests on §5.

---

## 5. Verdict — REJECTED, and rejected *despite* a better scorecard

**`tranche_startup_amortization` → NYISO `R`.** The arm is not promoted, and
the reason is rule 1 [R-STRUCT], not the residual.

This is the inverse of the owner's standing keeper clause. That clause admits a
run whose **structural integrity improves while gates regress**. This arm does
the opposite: it **flips NYISO's only failing load-bearing gate to PASS while
making the lane's dominant diagnosed structural defect 27–39 % worse.** Rule 1
addresses exactly this case — "never reach the right number through a mechanism
that isn't real", and "a more-accurate run that is missing real structure is
**not** a keeper."

**The mechanism is not real for this fleet, and the measurement says so.**

1. **The measured fleet does not price this way.** 53–66 % of NYISO CT energy
   clears **below its own bare SRMC at its own zonal price** (§2). A fleet
   running the majority of its energy below fuel cost is not adding a ~$5/MWh
   start-recovery markup on top of SRMC. This lever moves the model's offer in
   the *opposite* direction from the measured conduct of the fleet it
   represents.
2. **Start-cost recovery was already refuted on NYISO data.** nyiso-91's block
   test integrated each missed run whole — what a commitment actually decides —
   and found only 21.7/30.0/36.1 % profitable as blocks, with the median margin
   negative at **every** position h1–h7 inside the run. There is no
   loss-leading-start-then-earn-it-back shape to amortize against.
3. **There was no defect for it to fix.** The model's run lengths already match
   measured (§2), so the amortization horizon has nothing to correct — which is
   why prediction 2 held and the runs barely moved.
4. **It does not touch the lane's target.** C3c is bit-for-bit unchanged.

**How the C1 pass is actually produced, and why it must not be banked.** Both
CC_REGULAR and CT_PEAKER are *under*-produced against measured. The arm makes
the smaller shortfall (CT_PEAKER, model at 17 % of measured) worse in order to
shrink the larger one (CC_REGULAR), and the scored cell happens to land inside
its band on the way. No class is better represented afterwards — energy moved
between two classes that are both too low. Banking that C1 pass would bury the
peaker defect one layer deeper and advertise a closed gate the model has not
earned, which is precisely the failure mode rules 1 and 14 exist to prevent.

**This is an owner-visible call.** The arm produces a strictly better NYISO
scorecard than the current keeper (C1 PASS vs FAIL; every other criterion
identical). It is being left unpromoted on structural grounds. If the owner
prefers the gate, the run is registered and promotable — but the peaker
diagnosis in §2 and nyiso-90/91 would then need re-opening as a known,
deliberately-accepted misrepresentation rather than an open item.

**What this closes for the lane.** Queue item 3 is now adjudicated on measured
evidence rather than direction. With `da_virtual_bids` (nyiso-94, `G`),
`tsa_transfer_derate` (nyiso-95, `G`), block commitment (nyiso-90),
the J/K obligation (nyiso-83) and the reserve tiers (nyiso-84) all closed,
**NYISO's C3c lane has no remaining buildable in-model lever.** The surviving
candidate is unchanged from nyiso-91: NYISO SCUC load-pocket security
commitment with BPCG make-whole, which is a sub-zonal data-intake and topology
question requiring owner scoping before it is a mechanism question.

### DOF ledger (rule 21)

The arm adds **zero fitted scalars** and `n_residual` is unchanged. Both inputs
are measured/published and re-derive only on source-data updates (rule 23):
NREL `BIN_STARTUP_COST_PER_MW` ($20/MW CT, $50/MW CC duct bands), already cited
and in use for the committed tranche; and `campd_ct_run_lengths_NYISO.csv`
(22 plants + a pooled class fallback of 4.0 h over 34,057 measured runs),
derived from NYISO's own CAMPD unit conduct. No parameter is ported from
another ISO (rule 25) and none is fitted to a residual. The ledger entry is
recorded here for the rejected arm; no attestation is built because C6 is
correctly UNATTESTED for a probe.

### Reproducibility note for the next session

The nyiso-92 keeper does **not** replay in a fresh container without first
running `python scripts/data/curate_capacity_deliverability.py`. `data/clean/`
is derived and gitignored, `nyiso_li_lcr_tsl` defaults ON, and it lives only in
`run_config.json` — not `meta.json` — so `--replay-bundle` hard-fails with
"no published Long Island import limit ... available areas: []". Both arms hit
this identically; it is an environment-setup step, not a code or keeper defect.

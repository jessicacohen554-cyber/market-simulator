# FINDING — caiso-176: `battery_dispatch_adder` is WALLED, and CAISO's own bid stack refutes the replacement the ledger named

**Outcome: BRANCH II of the pre-registered verdict rule.** The DOF is **not closed**;
`battery_dispatch_adder = 5.0` stays exactly as it is. The wall is **filed with its instrument
committed** and re-checkable in minutes on any checkout.

**NO LP, NO SOLVE, no arm, no bundle, nothing registered — because nothing was run.** DOF ledger
unchanged at `n_entries` 11 / `n_residual` 8. Keeper unchanged at
`2026-08-06-caiso-175-tac-intake`. `holdout-freeze.json` and `calibration-complete.json`
UNTOUCHED.

Pre-registration: `PRECHECK-caiso176-frontier-dof-2026-08-06.md` §2.
Instrument: `scripts/probes/_caiso176_bidstack_reservation.py`.
Record: `results/calibration/_caiso176_bidstack_reservation.json`.

---

## 0. Headline

Three things, in the order they were found.

1. **The forward-valid replacement the DOF ledger names is ALREADY SPENT — both halves.** The
   ledger's `root_cause` reads *"forward-valid replacement is the measured AS power reservation
   (`storage_as_commitment`) + an ATB-derived degradation cost — open item to re-derive from
   those."* The AS half was probe-adjudicated **INERT** at caiso-74 and the family refuted by
   arithmetic at caiso-127/129. The degradation half was **built, A/B-solved and REJECTED** at
   caiso-100/101 on a pre-registered throughput guard. Neither is re-testable without new
   evidence (rule 28 DO-NOT-REDO). **This session did not re-run either.**
2. **The ATB route is now WORSE than when it was rejected, and the number says so.** On the
   constants of the day it produced **\$14.25/MWh**; on today's committed constants the same
   formula gives **\$22.63/MWh** — the capex constant moved 285 → 452.6 \$/kWh. It is further in
   the direction the volume guard rejected, so it is refused *a fortiori*.
3. **The one CAISO-own instrument nobody had read BOUNDS the parameter without a model, and the
   bound refutes \$22.63.** CAISO's Daily Energy Storage Report `bid_stack` sheet — committed
   since 2026-07-11 and recorded in its own README as *"retained but not curated"* — puts the
   fleet's discharge reservation price at **≤ \$15/MWh in all three years**. That is an
   independent, model-free corroboration of the caiso-101 rejection. **But it bounds; it does
   not identify** — every value in \$(0, 15]\ remains admissible, so the DOF does not close.

---

## 1. The named replacement, half by half — established, not re-run

| half | status | evidence |
|---|---|---|
| measured AS power reservation (`caiso_storage_as_reservation`) | **INERT**, then the whole AS-award family **refuted by arithmetic** — overnight upward award 334–713 MW against 2.1–3.1 GW of remaining headroom | caiso-74 (run `2026-07-11-caiso-74-storage-as`); caiso-127 / caiso-129 |
| ATB-derived degradation cost | **REJECTED PROBE** — the pre-registered two-sided ±15 % battery-only throughput guard hard-failed (2024 chg 6.77 < 7.40 TWh; 2025 10.28 < 11.07; discharge under floor in **all three** years) and 2025 evening discharge moved 0.64 TWh **away** from measured | caiso-100 §6 / caiso-101 (run `2026-07-19-caiso-100-cycling-cost`) |

caiso-101's structural finding is the one that matters here and it is carried forward verbatim:
**"the measured fleet buys its volume DESPITE a revealed \$11–17 conduct cost — battery charge
volume is inelastic to marginal cost."** A larger adder cannot be the answer to a fleet whose
volume does not respond to marginal cost.

### 1a. Why routing the LP through the existing degradation helper is NOT a closure

`model/storage._degradation_cost_per_mwh` computes
`capex_per_kwh × 1000 / cycles × STORAGE_DEGRADATION_REPLACEMENT_FRACTION`. Its third factor's
own constant block (`config/capacity_market.py`) describes it as *"a modeling simplification
grounded in NREL ATB augmentation costs and LFP warranty cycle life; **tunable**."*

Swapping a residual-identified 5.0 for a formula whose own allocation fraction is a declared
tunable is **DOF substitution, not DOF closure** — the free parameter moves, it does not go away.
Recorded here so no later session mistakes that route for a closure. (It is also a *rising*
substitution: the fraction sits in `capacity_market.py` where it currently serves the **entry
screen**, not the dispatch objective, so wiring it into the LP would additionally couple two
mechanisms that today are independent.)

---

## 2. The instrument — CAISO's own published storage bid stack

`data/raw/storage-as-awards/CAISO/storage-report-*.xlsx`, sheet `bid_stack`: the as-submitted
bid volume of the whole CAISO storage fleet, bucketed by offer price. **3,634,555 rows** read
across 12 committed quarterly files, 2023–2025, markets IFM + RTPD, resource classes LESR
(standalone + co-located battery — the class the LP models) and HYBD.

**The economic premise is one-sided and was declared before the numbers were read:** a rational
participant does not offer energy below its own marginal cost — the premise CAISO's own Default
Energy Bid mitigation machinery rests on — so **the lowest price bucket carrying material
discharge volume bounds the throughput cost from above**. The instrument can *refute* a candidate
value; it cannot *confirm* one. That asymmetry is the finding, not a limitation discovered
afterwards.

Neither candidate value the gates discriminate between was chosen by this session: **5.0** is the
committed keeper `run_config.json` field, **22.63** is arithmetic on committed constants.

---

## 3. Results — the three pre-registered gates

### G1 RESOLUTION — **PASS.** The published grain separates the two candidates.

Bucket vocabulary (11 price buckets + one non-price `SELF-SCHED` category):
`[-150,-100] (-100,-50] (-50,-15] (-15,0] (0,15] (15,50] (50,100] (100,200] (200,500]
(500,1e+03] (1e+03,2e+03]`.

**incumbent \$5.00 → `(0,15]` · ATB-derived \$22.63 → `(15,50]`.** Different buckets, so the
instrument can in principle discriminate.

### G2 MASS + STABILITY — **PASS.** The bound is \$15 and it does not move.

DAM (IFM) battery (LESR) discharge, share of **priced** bid volume (self-schedule excluded):

| bucket | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `[-150,-100]` | 0.04 % | 0.24 % | 0.18 % |
| `(-100,-50]` | 0.01 % | 0.30 % | 0.25 % |
| `(-50,-15]` | 0.12 % | 0.48 % | 0.34 % |
| `(-15,0]` | 0.29 % | 0.51 % | 0.66 % |
| **`(0,15]`** | **8.72 %** | **16.43 %** | **17.52 %** |
| `(15,50]` | 25.17 % | 29.78 % | 23.69 % |
| `(50,100]` | 26.26 % | 18.14 % | 24.32 % |
| `(100,200]` | 16.51 % | 7.57 % | 9.02 % |
| `(200,500]` | 10.07 % | 3.86 % | 1.82 % |
| `(500,1e+03]` | 12.81 % | 22.68 % | 22.19 % |
| | **100.00 %** | **100.00 %** | **100.00 %** |

**Implied upper bound on the fleet's discharge marginal cost = \$15/MWh in 2023, 2024 and 2025**,
at the ≥ 1 % *and* the ≥ 5 % mass threshold alike — so the answer is not an artifact of a
threshold choice. The `(0,15]` bucket is not a fringe: it carries **8.7–17.5 %** of all priced
DAM discharge volume, and its share **grows** as the fleet grows.

### G3 CONTAMINATION — **LOW, and it cuts the right way.**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `SELF-SCHED` share of all discharge volume (price-taking; excluded before any bound is read) | 0.33 % | 0.13 % | 0.10 % |
| priced at or below \$0 | 0.46 % | 1.54 % | 1.44 % |

The stack's low end is **not** a self-schedule artifact and **not** a negative-price artifact.
The `(0,15]` mass is genuine priced conduct.

### 3a. Reported against interest — the upper stack is exactly the equilibrium object the LP must not import

**12.8 / 22.7 / 22.2 %** of priced DAM discharge is offered in `(500,1e+03]`, near the bid cap.
That is opportunity cost and scarcity expectation, not marginal cost — the same object ERCOT-162
refused to transplant into the LP (*"a submitted SCED offer is an EQUILIBRIUM object that
presumes the scarcity the model lacks"*). It is reported because it **strengthens** the case
against reading the stack as a cost curve, and it is why only the **lower envelope** is used here.

### 3b. The other two panels, reported not used

* **RTPD (real-time) LESR** gives the same bound at the 5 % threshold in 2024/2025 (\$15) but
  \$50 in 2023 and \$0 at the 1 % threshold in 2024 — **less stable**, which is why the DAM panel
  is the one quoted. Real-time storage bids are more opportunity-cost-loaded, as expected.
* **Hybrids (HYBD)** bid deeply negative — the 1 % bound is `[-150,-100]` in every year, and
  `(-15,0]` alone carries 13.5 % of 2025 priced volume. Hybrids carry co-located solar and their
  discharge bid is a curtailment-avoidance object, not a battery throughput cost. **Not the LP's
  battery class, and not used.** Recorded so a later session does not mistake it for one.

---

## 4. What this establishes, and what it does not

**ESTABLISHED — model-free, on CAISO's own published data:**

* The CAISO battery fleet's discharge marginal cost is **≤ \$15/MWh**, stably, in all three
  training years.
* **\$22.63 is REFUTED** — the ATB-derived replacement is above the fleet's own revealed
  reservation price in every year. This is an **independent** corroboration of caiso-101's
  rejection: that verdict came from a solved A/B against a throughput guard, this one from the
  market's own submitted bids with no model in the loop. Two different instruments, same answer.
* The incumbent **\$5.00 is CONSISTENT** with the bound.

**NOT ESTABLISHED — and this is why the DOF stays open:**

* **The bound does not identify a value.** Every value in \$(0, 15]\ is equally consistent with
  it. Picking 5.0 *because it sits inside the bound* would be choosing a number the data does not
  determine; picking any other point in the interval would be worse. The published grain is
  15 \$/MWh wide exactly where the parameter lives.
* **A bid is not a marginal cost even at its lower envelope.** It is bounded *below* by marginal
  cost, which is what makes the one-sided inference valid — and is also precisely what stops it
  becoming a two-sided identification.

---

## 5. THE WALL — stated so it is re-checkable and so its exits are named

> **CAISO publishes no instrument that identifies a scalar battery discharge throughput cost.**
> The market-design object exists and is precisely defined — CAISO's Storage Default Energy Bid
> carries a cycle-cost / cell-degradation component in \$/MWh — but its values are **submitted
> per-resource from manufacturer documentation**, i.e. confidential and never published. The
> public aggregate substitute, the Daily Energy Storage Report bid stack, resolves the fleet's
> reservation price only to a **15 \$/MWh-wide bucket**, which bounds the parameter without
> determining it.

**Re-check cost:** `uv run python scripts/probes/_caiso176_bidstack_reservation.py`, ~5 minutes
over committed files, no network.

**What would close it (none available today, all named):**

1. **Per-resource CAISO storage DEB cycle-cost (`CD`) filings.** The exact object. Confidential
   by tariff construction — this is the primary wall and it is a disclosure wall, not a fetch
   task.
2. **A finer public bid-price grain.** `data/raw/caiso-public-bids` (OASIS `PUB_DAM_GRP`, full
   piecewise energy bid curves at masked-resource grain, 90-day lag) would give **actual
   breakpoint prices** rather than buckets. It is **gitignored and not on disk** — ~1,096 daily
   zips, ~0.5–0.9 GB, at OASIS's ~1-request-per-6-seconds rate limit. That is a real intake
   session with its own owner authorization, and it is the **single highest-value exit**: it
   would replace the 15 \$/MWh bucket with a price. It still returns a bid, so it would sharpen
   the bound rather than convert it into a two-sided identification — but a sharp bound at,
   say, ≤ \$6 would make the incumbent's admissible interval small enough to matter.
3. **An identified allocation basis for the degradation formula** — i.e. replacing
   `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` with a cited cell-versus-system cost split.
   That would make the ATB route a genuine closure instead of a substitution — but note the bound
   in §4 already refutes the value that route currently produces, so it would have to land
   **below \$15** to be admissible at all.

**DO-NOT-REDO from this session:**
* Re-arming the ATB-derived value at \$22.63 (or any value > \$15) — refuted twice over, by
  caiso-101's solved throughput guard and by CAISO's own bid stack.
* Re-testing `caiso_storage_as_reservation` as the adder's replacement — INERT at caiso-74,
  family refuted at caiso-127/129.
* Reading the bid stack's **upper** rungs as a cost curve (§3a), or the **hybrid** panel as a
  battery throughput cost (§3b).
* Selecting a value inside `(0,15]` because it sits inside the bound. The bound admits the whole
  interval; a point chosen from it is a fitted value wearing measured clothing.

---

## 6. Governance

* **Rule 13 `[R-MEASURED]`** — no price residual was read at any point in the derivation. Every
  gate is a property of published bid data.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing was transferred. ERCOT's \$10 and its refuted
  `ercot_storage_rt_offer_surface` were used only as *prior argument* about what a bid is; the
  measurement is entirely CAISO's own, and CAISO's cell is adjudicated on CAISO data.
* **Rule 28 duty (b)** — the `battery_dispatch_adder` matrix cell is updated in this same session
  and now carries the **caiso-100/101 CAISO adjudication it was missing entirely** (the note
  recorded only the ERCOT lane's history) plus this bound. The cell stays **`K`**: the parameter
  is armed on the keeper and unchanged.
* **Rule 20 `[R-DOF]`** — the ledger entry stays `identification: residual` and the count stays
  11 / 8. Its `root_cause` text, which still reads *"open item to re-derive from those"*, is now
  **known to be unachievable as written**; that is recorded here rather than silently edited,
  because the ledger is the keeper's attestation and rewriting it needs the keeper's own lane.
* **Rule 15** — nothing to register. No run was produced.
* **Rule 22** — 2023–2025 only, no solve of any kind, freeze untouched.

# PREREG nyiso-148 — the CHP lay-up duty split (`chp_layup_duty_split`)

Session nyiso-148. **Filed and committed BEFORE any arm solves.** Keeper at
HEAD `2026-08-19-nyiso-146c-state-scoped` (CALIBRATED, C3c the lone ledgered
caveat). Holdout spend freeze ACTIVE — years 2023, 2024, 2025 only, one bundle
per arm (rules 16 / 22). Frontier statement this lever addresses:
`ASSESSMENT-nyiso148-frontier-2026-08-21.md` §2.

---

## 1. THE OBJECT, AND WHY THIS LEVER

nyiso-147 PROVED the 2023 upstate price object with one measured field
(`nyiso_chp_btm_measured`: lw C3a-2023 +8.7 % → +1.5 %) and, in the same run,
proved it **unarmable** — restoring the CHP plants' true grid capacity exposes
two conduct defects the 35 % carve was masking. The first of them is this
lever's object:

> **Selkirk (10725) dispatches 730 GWh against a 92 GWh meter** once its
> capacity is restored — a merit-order inversion of the nyiso-145 defect-B
> class, on the CHP side, where `cc_reserve_duty_split` (CC_REGULAR-scoped)
> cannot reach it, and with **zero floor involved** (D-2 books CHP forcing at
> 0.38 % of CC_CHP energy, and the CHP classes are D-2-exempt): the energy is
> ECONOMIC, where D-2 and D-4 do not look.

---

## 2. PHASE 0 — the measurement, taken BEFORE the construction was chosen

Probe `scripts/probes/_nyiso148_chp_conduct_phase0.py`; record
`results/calibration/_nyiso148_chp_conduct_phase0.json` (+ `.csv`). **No LP.**
It reads two meters (EPA CAMPD unit-level hourly gross load; EIA-923 Page-1 net
generation), the model's own CHP population, and the frozen nyiso-147 share
artifact. It reads **no price residual, no D-4 verdict and no A/B gate**, which
is what makes any later agreement between its verdicts and the model's failures
evidence rather than circularity (rule 23 `[R-FROZEN-DERIVE]`).

### 2.1 The lay-up census applied beyond the bridge population

The nyiso-140/144 criterion **verbatim** — `median(grossLoad) == 0` in EVERY
(year, 4-hour block) cell of 2023–2025, on the units-summed PLANT series —
applied for the first time to the CHP classes, which the bridge census
(`TARGET_CLASSES = (CC_REGULAR, ST_GAS)`) excludes by design.

Of the 32 model CHP plants, 20 appear in CAMPD. Cell-count separation over
those 20:

| `cells_zero` | plants |
|---|---|
| 18 (qualifies) | **10** |
| 13 | 1 (Indeck-Corinth 50458, on-share 0.457) |
| 6 | 1 (World Generation X 54131) |
| 0 | 7 |

The separation is the same shape the bridge census reports: qualifiers stop at
18/18 and the nearest non-qualifier sits at 13/18.

### 2.2 THE GUARD THIS MEASUREMENT FORCED — a degenerate series is not lay-up

**Three of the ten 18/18 plants are CAMPD-INVISIBLE, not idle.** They carry an
identically-zero CAMPD series — `p99.5 HSL = 0.0 MW`, pooled gross `0.0 GWh`,
zero online hours — while EIA-923 reports substantial generation:

| plant | zone | LP grid MW | CAMPD p99.5 HSL | CAMPD gross (pooled) | EIA-923 net (pooled) |
|---|---|---|---:|---:|---:|
| 10025 RED-Rochester | Upstate_West | 46.7 | **0.0** | **0.0** | 949.5 GWh |
| 54099 Ticonderoga Mill | Upstate_West | 12.3 | **0.0** | **0.0** | 576.3 GWh |
| 50368 Cornell Ithaca Campus | Upstate_West | 12.7 | **0.0** | **0.0** | 439.1 GWh |

A naive extension of the criterion would convict all three. The census must
therefore **abstain** where the meter is silent: a plant whose CAMPD series is
identically zero carries no conduct evidence at all, so it receives no verdict.
This is a **degeneracy test, not a threshold** — `observed_hsl_mw > 0` — and
therefore carries **zero free parameters** (rule 21 `[R-DOF]`). Every one of the
seven qualifiers has an HSL of 54–355 MW and a pairwise-year CAMPD/EIA-923
coverage ratio of 1.04–1.49; every abstainer has exactly 0.0.

### 2.3 The qualifying cohort (7 plants), and where its bite actually is

`lp_grid_mw` is the capacity the LP carries (nyiso-147 phase-0c basis);
`measured` is that capacity re-based on the plant's own measured grid share,
i.e. what the arm-A base run carries. `metered CF` is against the plant's own
availability envelope, so it is the CF the LP is actually free to run it at.

| plant | zone | LP grid MW (ctl → measured) | mean avail | on-share | starts/yr | median run | metered CF on available |
|---|---|---|---:|---:|---:|---:|---:|
| **10725 Selkirk** | Capital_Hudson | 490.0 → **778.1** | 0.281 | 0.104 | 83 | 16 h | **0.050** |
| **54041 Lockport** | Upstate_West | 143.8 → **314.7** | **0.968** | 0.186 | 57 | 43 h | **0.036** |
| 54076 Indeck-Olean | Upstate_West | 58.9 → 90.1 | 0.090 | 0.094 | 120 | 13 h | 0.495 |
| 50450 Indeck-Oswego | Upstate_West | 49.0 → 76.2 | 0.269 | 0.166 | 187 | 12 h | 0.242 |
| 50451 Indeck-Yerkes | Upstate_West | 55.1 → 83.8 | 0.211 | 0.108 | 122 | 10 h | 0.165 |
| 50449 Indeck-Silver Springs | Upstate_West | 36.8 → 53.7 | 0.203 | 0.183 | 184 | 13 h | 0.503 |
| 10617 Beaver Falls | Upstate_West | 70.1 → 107.9 | **0.004** | 0.016 | 39 | 12 h | 1.628 |
| **cohort** | | **903.7 → 1 504.5** | | | | | |

Two findings that shape the expected effect and are recorded ex ante:

1. **The availability envelope already removes most of the small cohort**
   (Beaver Falls 0.004, Olean 0.090, Silver Springs 0.203, Yerkes 0.211,
   Oswego 0.269) — Beaver Falls is effectively out of the LP already
   (metered CF *exceeds* its available energy). The lever's material bite is
   therefore **Selkirk (778 MW at 5.0 % metered CF-on-available) and Lockport
   (315 MW at 3.6 %, reading 96.8 % AVAILABLE)** — 1.09 GW between them.
2. **The cohort is not mothballed; it is capacity-only.** On-shares of 1.6–18.6 %
   in short runs (10–43 h medians, 39–187 starts a year) with 82–95 % loading
   when on: these plants start, run and stop on price. Selkirk's own metered
   gross rises 156.9 → 107.7 → **384.8 GWh** across 2023/2024/2025 as prices
   rise. The correct representation is a **high offer**, not an absence.

### 2.4 Also measured, and deliberately NOT armed here (the candidate-(b) identification)

The live merchant cogens' duty statistics, recorded now so the successor leg
has a frozen identification and this session's delta stays single:

| plant | on-share | starts/yr | median run | loading-when-on p50 | metered CF on available |
|---|---:|---:|---:|---:|---:|
| 54547 Independence | 0.844 | 247 | 18 h | 0.712 | 0.849 |
| 50006 Linden | 1.000 | 2 | 13 148 h | 0.765 | 0.806 |
| 2493 East River | 0.999 | 6 | 1 674 h | 0.597 | 0.770 |
| 56259 Empire | 0.845 | 48 | 36 h | 0.692 | 0.714 |
| 54914 Brooklyn Navy Yard | 0.976 | 14 | 1 819 h | 0.858 | 0.819 |
| 54114 KIAC | 0.798 | 22 | 761 h | 0.529 | 0.558 |

These are the plants whose over-run drove nyiso-147's C1 failure (CC_CHP
+5.0 TWh; Independence at 1.36×/1.19×/1.26× of its meter). **No leg is armed for
them in this session** — they are a distinct construction (a duty/loading
representation, not a membership one) and would break the single-delta rule.

---

## 3. THE MECHANISM

### 3.1 What is built

* **`ScenarioConfig.chp_layup_duty_split: bool = False`** — GATED, default off,
  so every existing run is byte-identical. Generic name, **self-scoping through
  a per-ISO artifact** exactly like `cc_reserve_duty_split` (rule 25
  `[R-ISO-SCOPE]`: only NYISO has a census, so no other ISO's build changes, and
  NYISO's verdict transfers to no other ISO's cell).
* **`scripts/data/derive_campd_chp_layup_census.py`** →
  `data/raw/_processed-legacy/chp_layup_census_{ISO}.csv`: the §2.1 criterion +
  the §2.2 degeneracy guard, with the full population and its cell counts under
  `--detail` so a reader sees the separation rather than taking it on trust.
  **Frozen against residuals** (rule 23): re-derives only when a CAMPD or
  EIA-923 vintage lands.
* **`src/market_sim/data/chp_layup.py::load_chp_layup_census(iso)`** — the
  consumption seam. A missing artifact returns an empty set (normal state), and
  the consumer LOGS the membership it armed, so a run cannot silently claim a
  correction it never read.
* **The offer construction**, mirroring `cc_reserve_duty_split` limb for limb:
  a census plant's **CHP-class tranches** offer their whole dispatchable
  capacity at the class curve's PEAK band — `pct_mc = 0`, `pct_peak = room`.
  Applied at the **load-bearing** seam (`fleet/campd_bins.fleet_to_bins`) and
  mirrored at the **dashboard** seam (`data/offer_curves`), and in BOTH
  applied **LAST**, after every other pct override — the exact defect that made
  nyiso-146b's first solve inert, disclosed there and fixed there.

### 3.2 Rule compliance, stated ex ante

* **Rule 21 `[R-DOF]` / rule 5 `[R-NO-MAGIC]`: ZERO new scalars.** The level is
  the class's existing identified peak multiplier (`cc_duct_burner_peak_mult`,
  already in the DOF ledger); the membership is a plant-code SET from a conduct
  test with no threshold — the guard is a degeneracy test (`HSL > 0`), not a
  tuned cut.
* **Rule 13 `[R-MEASURED]`.** Could this quantity be produced for a forward year
  from forward drivers, and would it respond to changed conditions? **Yes** — the
  census regenerates from the CAMPD pipeline for any vintage, and a plant
  returning to service leaves the set on its own meter. It is an offer **SHAPE**
  from a measured duty signal, **never a pin**: dispatch above the peak band
  stays free, and the LP may still run a census plant as much as price justifies
  (which is exactly what the real Selkirk did in 2025).
* **Rule 14 `[R-ACCURATE]`.** The census replaces nothing accurate — today these
  plants carry the class default offer shape, which their own meters refute.
* **Rule 19 `[R-ONE-MECH]`.** Enumerated: what else shapes these plants?
  (i) the outage/availability envelope — already measured, and §2.3 shows it
  handles 5 of 7 and misses Selkirk/Lockport; the lever does NOT touch
  availability. (ii) `chp_steam` min-gen — 0.38 % of CC_CHP energy, and CHP is
  D-2-exempt. (iii) `cc_reserve_duty_split` — **CC_REGULAR-scoped, so the two
  populations are DISJOINT BY CLASS** and nothing stacks. No new floor is added
  and no existing floor's membership changes.
* **Rule 1 `[R-STRUCT]`.** The structural story is a real one: a semi-mothballed
  merchant cogen whose steam host is gone does not offer its full capability at
  SRMC into the day-ahead market — it is a capacity-only resource that offers
  high and runs on price. §2.3's on-shares, run lengths and 2025 rise are that
  behaviour.
* **Rule 28(c).** New `ScenarioConfig` field ⇒ matrix base row + a cell line in
  **every** shard, in this PR (CI enforces).

---

## 4. THE ARMS

Years **2023 + 2024 + 2025**, one bundle each, sequential (rules 12 / 16).

| id | recipe | purpose |
|---|---|---|
| **BASE** `nyiso148_base` | replay of `nyiso147_armA_recipe` (= `nyiso_chp_btm_measured` ON) | **Not a new arm** — a byte-identical reproduction of the already-registered `2026-08-20-nyiso-147a-chp-btm`, run only to recover the per-plant `dispatch/` parquets its committed bundle does not carry. Started before this prereg was filed, deliberately and disclosed: it introduces no untested mechanism and can produce no new evidence about one. |
| **ARM D** `nyiso148_armD` | BASE + `chp_layup_duty_split` | the single delta under test |
| **ARM E** `nyiso148_armE` | ARM D + `cc_reserve_duty_split` | **CONDITIONAL** on ARM D clearing D-K1–D-K6; scored on `PREREG-nyiso146b §ARM C`'s STANDING gates, which are **not re-litigated** (the ≥ 80 % bars stand as written) |

The **CONTROL for reporting** is the keeper `2026-08-19-nyiso-146c-state-scoped`,
whose byte-identical replay with HEAD-vintage diagnostics is the committed
`nyiso147_control`.

---

## 5. KILL GATES (ARM D)

Scored from the two bundles' own artifacts by
`scripts/probes/_nyiso148_ab_gates.py`; the criteria leg merges from
`calibration_verdict.py` after registration.

* **D-K1 — exactness.** Exactly ONE `scenario_config` field differs BASE → ARM D:
  `chp_layup_duty_split`. Any other diff FAILS.
* **D-K2 — liveness** (the anti-inert gate, nyiso-146b's lesson). The census
  arms exactly **7** NYISO plants; in ARM D every census plant's MINIMUM tranche
  offer rises to its class peak band (≥ 1.8× its BASE minimum offer); and **no
  non-census CHP plant's tranche offers change at all**.
* **D-K3 — the object.** Per census plant, P1 model energy against that plant's
  own metered CAMPD gross, per year. All three legs must hold:
  1. the cohort's aggregate **phantom** energy, `Σ max(0, model − metered)`,
     falls by **≥ 60 %** BASE → ARM D;
  2. **Selkirk's** model/metered ratio falls **below 2.0×** in every year
     (BASE: 7.9× in 2024);
  3. **no overkill** — no census plant falls below **0.25×** its own metered
     energy in any year. A mechanism that zeroes a plant that demonstrably runs
     is wrong in the other direction, and this leg is what stops the lever from
     becoming an absence.
* **D-K4 — no new conduct failures.** Zero NEW D-4 off-window rows and zero new
  D-1 gate failures vs BASE; every C8 record unchanged or improved. The leg adds
  no forcing whatsoever, so a rise in any mechanism's forced share means it is
  doing something other than re-shaping offers.
* **D-K5 — criteria, no PASS → FAIL vs the KEEPER.** No load-bearing criterion
  (C1 / C2 / C3a / C3b) may FAIL on ARM D where the keeper PASSes; C6 / C8
  unchanged. **This is the promote bar** — the keeper is CALIBRATED and a
  candidate must not be worse.
* **D-K6 — the 2025 recovery.** `|C3a-2025|` falls by **≥ 40 %** from the BASE's
  −12.2 % (i.e. to ≤ 7.3 %), **AND** C3a-2023 stays inside the ±10 % band.

## 6. PREDICTED DIRECTION, DECLARED EX ANTE

So that a surprise is legible rather than rationalised afterwards:

1. **2025 recovers materially.** Removing ~1.09 GW of in-merit, metered-idle
   upstate/Capital-Hudson capability from the base offer band raises the 2025
   level, which the BASE under-prices by 12.2 %.
2. **2023 RISES from +1.5 %, and this is the composite's main risk.** The same
   cheap phantom energy that the lever removes was partly holding 2023 down —
   the nyiso-146b joint object, one level up. D-K6's ±10 % leg is where this
   bites, and it is the leg most likely to fail.
3. **C1 CC_CHP improves but does not close.** The BASE's +5.0 TWh over-run is
   driven mostly by the LIVE cogens (§2.4), which this lever does not touch;
   expect roughly the cohort's share of it and no more.

## 7. PRE-DECLARED DISPOSITIONS

* **D-K1–D-K6 all clear** → ARM D is a promote candidate; solve ARM E and, if it
  clears its standing gates, promote the composite with the full rule-22 D-5(b)
  re-key and determination re-verification.
* **D-K5 clears, D-K6 misses** → ARM D is **REJECTED-AS-ARMED**, the recovered
  share of the −12.2 % is quantified, and an **owner decision card** is written
  for the remainder: the 2025 dear-gas level is a distinct object
  (assessment §2.3), and the choice between a partially-recovered composite and
  the incumbent is the owner's.
* **D-K3 fails** → the duty-split construction is wrong for this population;
  verdict **R** for the cell, and the finding states which conduct statistic
  *would* reproduce the measured behaviour.
* **Any outcome**: BOTH runs are registered on the dashboard in this session
  (rule 15, rejections included) and the NYISO matrix shard is stamped
  (rule 28b).

## 8. GOVERNANCE

* Holdout freeze **ACTIVE**; 2023–2025 only; nothing out-of-training is solved,
  scored, registered or read.
* The measured BTM share artifact is **frozen and untouched** (rule 23) — this
  session does not re-derive it and does not re-open its values.
* DO-NOT-REDO honoured: no min-run work, no unscoped online-hours leg, no LI
  CC/ST basis extension, no 7314 lever, no Zone-K bound, no `RHO_CLIP`, no
  Iroquois winter spread, no Astoria attribution, no re-derivation of the BTM
  shares against any residual.
* Flynn's start-count excess is open and is **not** this session's lever.

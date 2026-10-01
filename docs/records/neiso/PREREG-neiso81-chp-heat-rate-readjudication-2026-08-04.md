# PRE-REGISTRATION — neiso-81: re-adjudicating `measured_chp_heat_rates` at NEISO

**Session:** neiso-81 · **ISO:** NEISO · **Date:** 2026-08-04
**Model:** Opus (rule 27 `[R-PUSH]` — scope arms a `ScenarioConfig` field and may
promote a keeper)
**Designated keeper (the A/B base):** `2026-08-03-neiso-caiso156-meter-screen`
(bundle `results/calibration/neiso_c156_meter_screen_B`), determination
**CALIBRATED-WITH-CAVEATS**, 0 FAILs, 1 ledgered caveat (C3c), C1 all 12/12 ·
free 8/8.
**Phase-0 probe:** `scripts/probes/_neiso81_chp_phase0.py` · record
`results/calibration/_neiso81_chp_phase0.json`

**THIS DOCUMENT IS PUSHED BEFORE EITHER ARM SOLVES.** Every property, threshold,
falsifier, verdict branch and the promotion standard itself is fixed here in
advance. No number below was seen from a solved arm; every Phase-0 number was
measured from committed artifacts and one fleet-loader rebuild, with no LP.

---

## §1 — what is being re-adjudicated, and why now

`measured_chp_heat_rates` NEISO is cell **`O` (open)**. neiso-70 (2026-07-31)
measured the arm LIVE with **every pre-registered gate PASSING** — zero criterion
regressions across all 70 scored records, C1 all 12/12 · free 8/8, C3c
bit-identical — and stamped `O` rather than `K` for exactly one reason: **fit on
the repriced class degrades.** CC_CHP crossed from over- to under-generating in
every year. neiso-70's own §6 records that the artifact is ACCURATE (CEMS 4/4
within 1 %, median 1.00000) and that rule 14 `[R-ACCURATE]` forbids reverting to
the eGRID estimate because it fits better.

Two things have changed since:

1. **The owner's standing standard, stated 2026-08-04:** *"if structural
   integrity improves but gates regress that may still be a keeper."* That is the
   standard neiso-70 did not have, and it is what authorises this
   re-adjudication. It is the same standard under which NYISO's identical arm
   (nyiso-120) was escalated and then owner-ruled PROMOTE.
2. **The artifact was corrected.** neiso-80 re-derived
   `chp_power_only_heat_rates_NEISO.csv` under the miso-122 dark-fuel scope gate
   (19 → 22 columns; `(1595, CC_CHP)` 9.5584 → 9.4423).

**RE-MEASURED FROM SCRATCH.** neiso-70's numbers are NOT reused as this arm's
result: they were measured against a **different keeper** (the neiso-61 recipe)
and a **pre-gate-3 artifact**. Price and dispatch response is not stable across
keepers (miso-124), so the whole A/B is re-solved against the keeper actually
replayed.

---

## §2 — DO-NOT-MISREAD ledger, applied ex ante (all seven)

| # | rule | how it binds this session |
|---|---|---|
| miso-119 | `max abs Δoffer` is an UPPER bound only (over-predicted by two orders of magnitude) | neiso-70's 204.6 MW is quoted only as a bound, never as this arm's magnitude |
| miso-121 | **binding is not marginality**; the predictive ex-ante statistic is MARGINAL SHARE | §4 P10's headroom is labelled an upper bound; marginal share is post-solve only and no ex-ante magnitude is claimed |
| miso-122 | `max_abs_class_hour_mw` is NOT a mechanism magnitude — read per-class ENERGY deltas | every adjudicating statistic in §6 is a per-class **energy** delta; class-hour maxima are liveness only |
| miso-124 | price response is NOT stable across keepers | a same-HEAD **zero-delta control arm A** is solved first and every delta is quoted against it, never against the committed keeper |
| miso-125 | a WRONG-SIGN magnitude is a denominator defect | §6 A/B asserts the expected sign per class and treats a sign violation as a statistic defect, not a result |
| miso-126(a) | a fleet-loader firing check is NOT sufficient proof — prove firing at TWO grains | **grain 1** = P1 pre-arm loader check (done, §4); **grain 2** = P6 post-arm per-class ENERGY delta. `tests/unit/data/test_cc_steam_part_capacity.py::TestBackcastFleetSourcing` **RUN AND PASSING** this session |
| miso-126(b) | a magnitude violating a CONSERVATION LAW is a boundary defect in the statistic | P7 scores the FULL identity over `class_hourly` + storage + `system`, not `class_hourly` alone |
| neiso-80 | **an artifact the keeper does not consume is score-inert by construction** | checked FIRST: the keeper's own `run_config.json` records `measured_chp_heat_rates = false`. **This arm's entire point is that it FLIPS that flag** — which is precisely why neiso-80 owed no solve and this session does |

**MEASUREMENT TRAP (miso-116):** `load_fleet_from_csv` defaults
`measured_chp_heat_rates=False`. Every probe's model side is built from the
**keeper's `run_config.json`**, never the loader defaults
(`_neiso81_chp_phase0.keeper_config`).

---

## §3 — DO-NOT-REDO (rule 28a). These are CLOSED and are NOT re-opened to rescue the arm

* **NO CC_CHP host-steam floor for NEISO, and `chp_steam_floor_p25` is NOT
  armed.** neiso-71 closed this: NEISO's merchant CC_CHP genuinely carries no
  host-steam obligation (the non-Kendall CC_CHP floor totals **15.0 MW** across
  all seven plants), and a Kendall-based floor would be a FITTED parameter
  (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`). **This session builds no floor.**
* **Kendall's capacity basis is ADJUDICATED-ARTIFACT** (neiso-73). Not re-opened.
* **`cc_steam_part_capacity` NEISO is `I`** (neiso-80), proven by a
  byte-identical armed fleet. Not re-tested, and **not stamped by this session in
  either outcome.**
* `da_virtual_bids` NEISO is `R`; `pumped_storage_cycling_depth` NEISO is `G`.

---

## §4 — CONSTRUCTION PROPERTIES: the load-bearing assumptions, numbered, each with its own falsifier

The miso-125/126 discipline. Properties **P1, P2, P3, P8, P9, P10** are measured
**pre-solve** and their falsifiers are evaluated here; **P4, P5, P6, P7** are
post-solve and are evaluated by the A/B scorer against the thresholds fixed now.

### P1 — WIRING: the flag reaches the LP seam at the keeper's own config (grain 1)

Rebuilt through the runner's own chain (`load_or_synthesize_bins` →
`build_base_fleet`) at the designated keeper's `ScenarioConfig`, flag off → on,
on the **corrected** artifact:

| | value |
|---|---|
| generators moved | **20 / 602** |
| MW moved | **271.008** |
| CC_CHP cap-wt heat rate | 8.1437 → **10.3632** (**+27.25 %**), 320.6 MW |
| CT_CHP cap-wt heat rate | 6.2962 → **6.7784** (**+7.66 %**), 74.5 MW |
| CC_REGULAR cap-wt heat rate | 9.0829 → 9.0829 (**+0.00 %**), 14,043.5 MW |

**Falsifier:** zero generators moved / zero heat-rate delta ⇒ the arm is inert by
wiring, cell **`I`**, **no solve spent** (the ERCOT-146 outcome).
**NOT FIRED — the arm is live at the seam.** NEISO takes the non-ERCOT branch of
`load_or_synthesize_bins` (only `iso == "ERCOT"` reads the curated sheet), so it
is not ERCOT-146.

### P2 — THE CORRECTED ARTIFACT IS THE ONE UNDER TEST, AND ITS ACCURACY CLAIM RE-VERIFIES

`data/raw/_processed-legacy/chp_power_only_heat_rates_NEISO.csv`, 40 rows × **22
columns** (gate-3 vintage), flag census `not_unfired_topping` 22 / `ok` 12 /
`no_egrid_row` 5 / `basis_mismatch` 1. Applied population: CC_CHP 3 rows /
378.2 MW, 6.9636 → 9.4576; CT_CHP 9 rows / 51.5 MW, 8.7009 → 11.5146.
**CEMS reconciliation re-verified this session: 4/4 covered rows within 1 %,
median ratio 1.00000.**

**Falsifier:** any covered row's `cems_vs_egrid_total` outside (0.9, 1.1) ⇒ the
measured-accuracy premise fails and the cell goes **`R`**. **NOT FIRED.**

### P3 — THE SCOPE-GATE WALK-BACK IS SMALL AND MUST NOT BE QUOTED AS CLOSING THE OVERSHOOT

At the LP seam the corrected artifact gives **+27.25 %** against neiso-70's
**+27.96 %** — a **0.71 pp** walk-back, **2.54 %** of the move that produced the
overshoot. (neiso-80 §1.1 measured **2.15 %** on the artifact population; both
are about one part in forty.) **This does NOT close the overshoot and no
statement in this session's finding may imply it does.** No falsifier — this
property exists to bound the claim in advance.

### P4 — SINGLE DELTA (post-solve)

The two arms' `run_config.json` `scenario_config` blocks differ in **exactly one
key**, `measured_chp_heat_rates`.
**Falsifier:** ≥ 2 differing keys ⇒ the A/B is invalid; **no verdict is written**
and the arms are re-solved (the nyiso-120 KE5 outcome).

### P5 — CONTROL INTEGRITY (post-solve, miso-124)

Arm **A is a zero-delta same-HEAD control**, solved FIRST. Every delta in §6 is
quoted **B − A**, never B − committed keeper. Scored on **two bases**: the
*scorecard* basis (same determination structure as the committed keeper) is the
**gate**; the stricter *byte* basis (class-hour for class-hour, < 1e-6 MW) is
computed and **REPORTED** — a byte miss is same-HEAD drift, a separately
reported finding, not a failed gate (the caiso-146 / neiso-69 / neiso-70 K2
precedent).
**Falsifier (gate):** control A's determination structure differs from the
committed keeper's ⇒ report the drift and gate on the scorecard basis; if the
determination itself differs, the base is not the keeper and the A/B is
re-scoped.

### P6 — POST-ARM FIRING (grain 2 of miso-126(a))

Per-class **ENERGY** delta B − A on CC_CHP is non-zero in every year.
**Falsifier:** `|Δ CC_CHP energy| == 0` ⇒ the flag was *recorded* but never
*applied* — "the mechanism was never applied", not "the mechanism is inert" —
cell **`I`**, and the loader-forwarding guard is re-run.
`tests/unit/data/test_cc_steam_part_capacity.py::TestBackcastFleetSourcing`
(which generalises the guard to **every** boolean `ScenarioConfig`-backed keyword
of `load_fleet_from_csv`) was **run this session and PASSES**.

### P7 — CONSERVATION (miso-126(b))

The FULL balance identity, per hour, over `class_hourly` + storage + `system`
sidecars — not `class_hourly` alone:

```
Σ d_class + d_discharge − d_charge + d_slack − d_dump − d_demand == 0
```

**Falsifier:** any hour breaching a 1e-6 relative tolerance ⇒ the magnitude
statistic has a BOUNDARY defect; **re-scope the statistic before any verdict is
written.**

---

## §5 — THE LOAD-BEARING QUESTION, PRE-REGISTERED AS SUCH — AND ONE HALF IS ALREADY FALSIFIED, PRE-SOLVE

> **Is the CC_CHP overshoot a class-attribution artifact of the
> CC_CHP/CC_REGULAR boundary, rather than a dispatch error?**

### P8 — SHARED REGISTRY. **The attribution-artifact reading is FALSIFIED.**

Measured pre-solve at the keeper's config:

| class | units | plants | capacity |
|---|---|---|---|
| CC_CHP | 19 | **7** | 320.6 MW |
| CC_REGULAR | 214 | **29** | 14,043.5 MW |

* **Plants in BOTH classes: NONE.** The two sets are disjoint.
* **Artifact CC_CHP plants absent from the model's CC_CHP class: NONE.**
* The benchmark side is `classFull[k] = e923_bench[k] − btm[k]`, which buckets
  EIA-923 per-plant net generation through the **same**
  `plant_taxonomy.classify_plant` registry the model fleet uses.

⇒ **ONE REGISTRY, APPLIED TWICE.** The CC_CHP / CC_REGULAR split is consistent on
both sides of the comparison, so a CC_CHP-vs-CC_REGULAR movement is a **real
per-class reallocation, not a bookkeeping seam.**

**THIS SESSION WILL NOT ARGUE THE ATTRIBUTION-ARTIFACT CASE.** It is killed here,
before any solve, exactly as miso-125's lever was. Whatever the promotion case
turns out to be, it may not rest on P8.

**Falsifier (recorded for completeness):** a non-empty
`plants_in_both_classes`, or an artifact CC_CHP plant sitting in the model's
CC_REGULAR class, would have made the boundary genuinely ambiguous. Neither
occurs.

### P9 — RESOLVABILITY. **This is the surviving half, and it is the one that matters.**

C1's per-class volume band is `min(2 % of ISO load, 8 TWh)`. Compare it to the
repriced class's **entire annual grid-delivered actual**:

| year | C1 volume band | CC_CHP actual | actual ÷ band | resolvable? |
|---|---|---|---|---|
| 2023 | ±1.955 TWh | 1.072 TWh | **0.548×** | **NO** |
| 2024 | ±2.103 TWh | 1.124 TWh | **0.534×** | **NO** |
| 2025 | ±2.066 TWh | 1.194 TWh | **0.578×** | **NO** |

**A class whose whole annual output is roughly half its own tolerance cannot be
discriminated by its C1 row in either direction** — zero generation and double
generation both PASS. Three further facts compound it, all from the keeper's own
scorecard: CC_CHP is **D-10 `pinned` and `excluded_from_free`**, so the arm
cannot move the free-class score by construction (neiso-70 §3); its **2025 C1 row
is SKIPPED** on preliminary EIA-923 (3/7 plants missing, 57 % reporting), so only
2023 and 2024 are scored; and CHP classes are exempt from **both** C7 and C8 by
**explicit class list** — not by the 2 % materiality floor — so CHP D-1/D-2
numbers are diagnostics and never a passed gate (the caiso-147 protective-framing
correction).

**Falsifier:** if any year's CC_CHP actual is **≥** that year's band, the class
IS resolvable in that year and its degradation must be scored as a real
regression on a **gated** quantity, which would move the verdict to
STOP-AND-ESCALATE regardless of the rest. **NOT FIRED in any of the three
years.**

### P10 — SUBSTITUTION HEADROOM. **Upper bound only.**

| | value |
|---|---|
| CC_CHP repriced band traversed | 8.1437 → 10.3632 MMBtu/MWh |
| CC_REGULAR capacity **cheaper** than the repriced CC_CHP | **12,313.0 MW (87.7 %)** |
| CC_REGULAR capacity **inside** the traversed band | **7,315.3 MW** |
| CC_REGULAR total / cap-wt HR | 14,043.5 MW @ 9.0829 |

Per miso-119/121 this is **headroom, never a magnitude**: capacity that *could*
absorb the displaced energy. Marginal share is the predictive statistic and is
observable only post-solve.

**Falsifier:** if **less than 70 %** of the CC_CHP energy delta is absorbed by
CC_REGULAR — i.e. the displaced energy lands on oil / imports / CT_PEAKER /
slack / dump instead — then this is a merit-order defect reaching beyond the CC
pair, the promotion case changes character, and the verdict routes to
STOP-AND-ESCALATE.

---

## §6 — WHAT IS **NOT** PREDICTED (miso-124), stated against interest

**Magnitude is not predicted, and neiso-70's numbers are not this arm's result.**
The current keeper is not neiso-70's control: it carries
`nuclear_unit_availability` (neiso-71), the neiso-72 hydro window and the
caiso-156 CT meter screen. Its **CC_REGULAR C1 error has ALREADY shrunk** — the
keeper's own scorecard reads **−0.38 TWh (2023) / −0.11 TWh (2024)** against
neiso-70's control values of −0.471 / −0.340.

**Therefore the counterweight has LESS ROOM than it did at neiso-70, and the
combined CC_CHP + CC_REGULAR improvement that neiso-70 reported MAY NOT
REPLICATE.** This is stated in advance, against interest, because it is the
single most likely way this arm fails its own promotion bar in §7.

**Only the SIGN is predicted:** CC_CHP energy falls, CC_REGULAR energy rises,
total generation ≈ 0, load-weighted λ rises.

---

## §7 — THE PROMOTION STANDARD ITSELF, STATED EX ANTE IN NUMBERS

The owner's standing standard (2026-08-04) is *"if structural integrity improves
but gates regress that may still be a keeper."* Both halves are given numeric
content here so the verdict cannot be written after the fact.

### 7.1 — "STRUCTURAL INTEGRITY IMPROVES" means all four of:

* **S1 — an ESTIMATE is replaced by a MEASUREMENT.** The incumbent is eGRID's
  **steam-credited** `PLHTRT`; the replacement is eGRID's own published
  `(PLHTIAN + CHPCHTI)/PLNGENAN` on the **same net denominator** (no gross-to-net
  factor), dark-fuel scope-gated per miso-122, CEMS-reconciled **4/4 within 1 %,
  median 1.00000**. Rule 14 `[R-ACCURATE]`. **[PRE-VERIFIED at P2.]**
* **S2 — ZERO free parameters.** The DOF ledger stays at the keeper's **12
  entries / 5 residual**. Nothing is swept against a residual; rule 23
  `[R-FROZEN-DERIVE]` is satisfied because the re-derivation was driven by the
  miso-122 measured scope change, never by a residual.
* **S3 — NO new mechanism surface.** One boolean already in `ScenarioConfig`
  (`scenarios.py:2006`); no floor, no adder, no override map, no new registry
  entry. Rules 19 `[R-ONE-MECH]` / 24 `[R-REGISTRY]`.
* **S4 — LIVE at both grains and conservation-clean:** P1 ✓ (pre-solve), P6 and
  P7 post-solve.

### 7.2 — REGRESSION THAT IS ACCEPTED, in numbers

* **A1** CC_CHP's own C1 |error| may worsen by **any amount that keeps its row
  PASS**, i.e. |model − actual| ≤ **±1.955 TWh (2023) / ±2.103 TWh (2024)**.
  Justified **solely by P9 (unresolvable)** — never by P8, which is falsified.
* **A2** CT_CHP's C1 |error| likewise within band. The artifact's CT_CHP leg
  covers 19.3 % of capacity and **0.0 % of metered energy** (neiso-70 §1), so it
  is not identification in either direction and is reported, never cited as
  evidence.
* **A3** Load-weighted λ may rise up to **+1.0 pp of level** in any year.
  Keeper C3a headroom to the ±10 % band is **6.7 / 4.1 / 7.1 pp** (currently
  +3.3 % / +5.9 % / +2.9 %); at neiso-70's measured push
  (+0.157 / +0.111 / +0.309 $/MWh against levels 39.168 / 43.982 / 72.042) that
  is **+0.40 / +0.25 / +0.43 pp**, so a C3a PASS→FAIL would need roughly **ten
  times** the expected push.
* **A4** CC_CHP / CT_CHP **D-1 `cv_ratio` and `profile_r` may degrade without
  limit**, and CC_CHP's D-2 forced share likewise: CHP classes are exempt from
  C7 **and** C8 by explicit class list, so these are diagnostics and never a
  passed gate. (neiso-70 measured `cv_ratio` 2.814 → 6.99 etc.; a repeat is
  expected, reported, and not a gate.)

### 7.3 — REGRESSION THAT IS **NOT** ACCEPTED — each routes to STOP-AND-ESCALATE, never to a silent promotion

* **N1** — any criterion crossing **PASS → FAIL**.
* **N2** — the re-verified determination being **WORSE** than the incumbent's
  (CALIBRATED-WITH-CAVEATS, 0 FAILs, 1 ledgered caveat). **Rule 22 D-5(b) is
  mandatory and OUTRANKS the owner's standing standard: a worse re-verified
  determination STOPS the promotion and escalates to the owner rather than being
  silently written.**
* **N3** — C3c degrading from its ledgered CAVEAT, or a **new caveat slot** being
  spent.
* **N4** — total generation moving by more than **±0.05 %**, or slack / dump
  rising in any year.

---

## §8 — VERDICT LADDER, fixed before any solve

| branch | condition | outcome |
|---|---|---|
| **V1** | P1 or P6 falsified | cell **`I`**; the mechanism was never applied at NEISO |
| **V2** | P4 or P7 falsified | **INVALID** — no verdict, statistic re-scoped, arms re-solved |
| **V3** | P2 falsified | cell **`R`** — the measured-accuracy premise fails |
| **V4** | S1–S4 hold · none of N1–N4 fires · **and** the combined CC_CHP + CC_REGULAR grid-delivered \|error\| (the identified aggregate, per P9) **improves in at least one of the two scored years and worsens by no more than 0.50 TWh in the other** | **`K` — PROMOTE** |
| **V5** | S1–S4 hold, but any of N1–N4 fires **or** the combined-CC \|error\| worsens in **BOTH** scored years | **STOP-AND-ESCALATE to the owner; keeper UNCHANGED.** Recommendation stated on the owner's standing standard; the cell keeps **`O`** with the escalation recorded — the nyiso-120 precedent, where the owner subsequently ruled PROMOTE |
| **V6** | none of the above | cell stays **`O`** |

**The 0.50 TWh threshold in V4 is anchored, not fitted:** it is **one quarter of
the model's own declared per-class C1 volume tolerance** (±1.955 / ±2.103 TWh)
and ≈ 0.9 % of the combined-CC actual (53.4 / 57.7 TWh). It is fixed here and
will not be moved.

---

## §9 — the A/B recipe

* Same-HEAD replay via `scripts/replay_keeper.py` on the designated keeper
  bundle `results/calibration/neiso_c156_meter_screen_B`.
* **`--years 2023 2024 2025` in ONE invocation** — never a per-year chain
  (`replay_keeper` sets `kwargs["years"] = args.years`, so a chain writes
  `meta.json` with only the LAST year and silently breaks K5 and rule 16
  `[R-ALLYEARS]`).
* **Arm A — `neiso81_control_A`:** zero-delta, no `--set`. Solved and quoted
  first.
* **Arm B — `neiso81_chpheatrate_B`:** `--set measured_chp_heat_rates=true`.
* Post-solve order: `dashboard_add_run.py` (top-15 retention) →
  `legitimacy_diagnostics.py --bundle <dir> --iso NEISO --years 2023 2024 2025
  --json-out <dir>/legitimacy_diagnostics.json` →
  `gen_neiso81_attestation.py` + `build_dof_ledger` →
  `calibration_verdict.py --run-id <id> --write-metrics` → the A/B scorer
  `scripts/probes/_neiso81_chpheatrate_ab.py`.

---

## §10 — governance

* **Rule 22 `[R-HOLDOUT]`** — `--year` is strictly **{2023, 2024, 2025}**. NEISO's
  locked test is **SPENT and never re-grantable** (2026-07-07,
  `2026-07-07-neiso53-winter-fuelsec-coldsnap`), and the **holdout spend freeze
  is ACTIVE** and outranks every marker. No out-of-training year is solved,
  scored or touched. NEISO holds a `complete` marker, so **D-5(b) applies to any
  promotion**: re-key `calibration-complete.json` with a determination
  **re-verification** on committed artifacts, and a worse determination stops the
  promotion (N2).
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one bundle per arm.
* **Rule 15 `[R-DASHBOARD]`** — **every** completed run is registered
  in-session, control and arm alike, keeper or rejected.
* **Rule 25 `[R-ISO-SCOPE]`** — MISO's, CAISO's, PJM's and NYISO's `K` on this
  mechanism transfer **nothing**. NEISO's parameters come from NEISO's own
  artifact, derived on NEISO's own data. No file outside the NEISO lane is
  re-derived and no cell outside NEISO is stamped.
* **Rule 26 `[R-REGISTRY]`** — the arming is visible in `run_config.json`.
* **Rule 28b `[R-MECH-MATRIX]`** — the tested cell is stamped in **this** session
  whatever the outcome, refusal included.
* **Rule 27 `[R-PUSH]`** — Opus; any push touching a file ≥ 300 lines is
  blob-verified immediately after.

---

## §11 — the named secondary, if the arm is refused on its merits

`6081_CA1` sits in the LP as a **96.0 MW `oil` generator with an EMPTY
`plant_group`** while its three CC1-block CT siblings are CC_REGULAR/`gas_cc`,
and CAMPD meters the block on Pipeline Natural Gas at units 001/002/003 with **no
CAMPD unit for CA1 at all**. That is a **classification/repricing** question
needing its own charter and its own measured identification — the plant meters
only 73–91 GWh/yr gross, so it is a **correctness** question before a magnitude
one. `cc_steam_part_capacity` NEISO stays **`I`** either way and is **not**
stamped for it.

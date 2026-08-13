# FINDING — miso-156: MISO's C3a miss is a **MARGINAL-UNIT IDENTITY** failure, the **COST-LEVEL channel runs BACKWARDS**, and **BOTH queued Phase-1 levers are adjudicated against — one REJECTED, one INERT**

**Session** miso-156 · **ISO** MISO · **Date** 2026-08-13 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**PREREG** `results/calibration/PREREG-miso156-c3a-three-channel-decomposition-2026-08-13.md`,
pushed at **`162a51d`**, blob **`7f124d18`**, **verified byte-identical against the
FETCHED remote ref** before any adjudicating statistic was computed (rule 27
`[R-PUSH]`).

**NO SOLVE. NO RUN REGISTERED. NO `ScenarioConfig` FIELD ADDED. KEEPER
UNCHANGED.** Rule 15 `[R-DASHBOARD]` is not engaged — no backcast run was
produced. **TWO CELL VERDICTS ARE MINTED** (rule 28(b)), both from measurement:
`gas_hub_basis_overlay` MISO **`U` → `R`** and `ramp_envelopes` MISO
**`U` → `I`**.

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds **neither**
`complete` nor `final`. No holdout year was read, solved, scored or registered.

**BRANCH TAKEN: B-IDENT** (PREREG §6).

---

## 1. Headline

The decomposition is on the **exact C3a grain** — its `gap` reproduces the
registered miss to the cent — and it says three things:

| 2025, annual (the adjudicating cell) | $/MWh | share of gap |
|---|---|---|
| **gap** (actual − model) | **+7.082** | 100 % |
| **Δ₁ marginal-unit IDENTITY** | **+11.966** | **169.0 %** |
| **Δ₂ delivered-fuel COST LEVEL** | **−6.156** | **−86.9 %** |
| **Δ₃ ABOVE-COST** | **+1.272** | 18.0 % |

1. **The identity channel owns the miss** — and it grows the way the failure
   grows: Δ₁ = **+1.294 / +2.037 / +11.966 $/MWh** across 2023/2024/2025, a
   **9.2×** increase into the failing year.
2. **The cost-level channel has the WRONG SIGN.** The model's delivered gas is
   **above** measured in all three years — by **+0.348 / +0.092 / +0.892
   $/MMBtu** against the pre-registered primary (hub-month spot) and by
   **+1.543 / +1.005 / +1.010** against a second measured comparator
   (EIA delivered-to-electric-power). Correcting the model's fuel to measured
   would **lower** its prices by $6.16/MWh in 2025 and make C3a **materially
   worse**.
3. **The class is already right; the POSITION IN THE STACK is not.** At the
   top-200 demand hours of 2025 the model's marginal tranche is `CT_PEAKER` in
   **74.1 %** of zone-hours against **69.0 %** implied by the market — but the
   model's implied heat rate there is **11.93** MMBtu/MWh against the market's
   **28.83**. The model reaches the right *kind* of unit and stops less than
   half-way up it.

**And both levers the lane's queue named for this branch are now adjudicated
against, neither on "the residual didn't move":**

* **`gas_hub_basis_overlay` → `R`.** Its own measured input points the wrong way
  (result 2), and for MISO it would **replace** a faithful per-plant F923
  measurement with one flat ISO-wide hub series — a rule 14 `[R-ACCURATE]`
  regression, MISO not being NEISO.
* **`ramp_envelopes` → `I`.** MISO's model **under-ramps** the measured fleet at
  every quantile in every year — |1-h move| ratio **0.59/0.73/0.83** (2023),
  **0.63/0.72/0.83** (2024), **0.66/0.79/0.88** (2025) at p50/p90/p99. PJM armed
  this mechanism because its model *out*-ramped the real fleet 1.4–1.7× at p99;
  **MISO's own data says the opposite**, so a ramp envelope can only smooth a
  fleet that is already too smooth. Rule 25 `[R-ISO-SCOPE]` working in the
  direction that costs a lane its lever.

---

## 2. Validity gates — all run BEFORE any adjudicating statistic

| gate | result |
|---|---|
| **V1** — reproduce the registered C3a | **PASS 3/3.** −1.993 / −8.031 / −15.590 % against the published −1.98 / −8.03 / −15.58 %; deltas **−0.013 / −0.001 / −0.010 pp** against a ±0.5 pp bar |
| **V1b** — the measured side is the scorer's own basis | **PASS 3/3.** The load-weighted measured mean reproduces `bench.avgLMP.rt_lw` to **−9.1e−5 / +2.0e−5 / −9.9e−5** relative |
| **V2** — rebuilt floors reproduce miso-155's record | **FAIL 2 of 3 — S-FLOORBLIND FIRED** (§3) |
| **V3** — the decomposition identity, elementwise | **PASS 3/3.** Max abs residual **5.7e−14 / 1.1e−13 / 2.3e−13** against a 1e−9 bar |
| **V4** — the reconstruction is the keeper's fleet | **PASS 3/3.** `n_gen` 2929 / 2923 / 2923; carry zones 6 |

**Environment integrity:** `git status --short | grep -c '^ D'` = **0**; no
`.venv` shipped (built from `requirements.txt`); `data/clean` empty and
`curate_capacity_deliverability.py` wrote **776 MISO rows**.

---

## 3. S-FLOORBLIND fired — debugged, disclosed, and then shown to be **provably immaterial to every number in this finding**

**The magnitudes, in full.** Rebuilt CT reliability floor against miso-155's
committed `FLOOR_source`:

| year | rebuilt | miso-155 | Δ | floored CT rows | fleet floor |
|---|---|---|---|---|---|
| 2023 | 2.8805 TWh | 2.8457 | **+1.22 %** | **160** vs 158 | 117.462 vs 117.439 TWh |
| 2024 | 2.8836 TWh | 2.8773 | **+0.22 %** | **151** vs 150 | 120.694 vs 120.700 TWh |
| 2025 | 2.8677 TWh | 2.8677 | **+0.00 %** | **153** vs 153 ✓ | 121.859 vs 121.859 TWh ✓ |

**2025 — the year the whole finding adjudicates on — reproduces EXACTLY**, to
the last committed digit and the exact floored-row count.

**Debugged, per the PREREG's "stop, debug, disclose" instruction. Two hypotheses
were put up and BOTH were REFUTED BY MEASUREMENT, including my own:**

1. *"The demand basis differs."* **REFUTED.** The keeper's committed system-parquet
   demand and the production `load_demand(include_interchange=True|False)` agree
   at **640.9927 TWh** for 2023 and give the **identical 103 flagged net-load
   days**; the marginal days sit 0.02–0.14 GW from the 78.52 GW threshold, so the
   flagging is not the difference.
2. *"miso-155 read its floors from the CONTROL bundle `miso155_p0_C`, not this
   keeper, and the two solves diverge most in 2023."* This was **my own
   hypothesis, and it is REFUTED**: re-running the floor rebuild on the control
   bundle's own committed demand returns the **identical** 2.8805 TWh / 160 rows
   (2023) and 2.8836 TWh / 151 rows (2024). The demand is the same in both
   bundles.

**Confirmed matching:** 12 enabled limb specs — the exact count the solve log
records ("12 enabled limb spec(s) applied from RELIABILITY_FLOOR_REGISTRY") —
the production engine asserted by `__module__`, and `weather_year` pinned per
solve year.

**The cause of the 2023/2024 residue is NOT RESOLVED.** It is reported at full
magnitude and left open.

**Why it cannot touch a single number here, measured rather than argued.** The
floors-OFF twin — a perturbation ~80× larger than the V2 miss — moves the
decomposition by **0.0000 $/MWh in all 27 cells** (3 years × 3 grains × 3
channels). **Reported against interest: the floors leg was the PREREG's §2
centrepiece and it added NOTHING to this instrument.** The reason is structural
and is stated so a successor does not repeat the build: `HRmax` is a
headroom-masked *maximum* over ~1,450 gas tranches whose owner always has
headroom, and `G_mod` is capacity-weighted — neither quantity can see a floor.
**miso-155's mandate ("any probe scoring a floored class must read the floors")
is satisfied here vacuously, because this probe scores no floored class.**

**A durable, separate result the attempt produced.** `results/calibration/*/floors/`
is **GITIGNORED** (`.gitignore:443`), so **no committed bundle carries
`floors/<year>_P1.npz`** and miso-155's read-the-bundle correction is **not
reproducible from a fresh checkout**. The production-engine rebuild in
`_miso156_c3a_decomposition.model_year` is the reproducible substitute, and on
2025 it is exact. A successor that genuinely needs floors should use it and gate
it, not re-solve.

---

## 4. The decomposition, at full magnitude, all years and all grains

`Δ₁ + Δ₂ + Δ₃ ≡ P_act − P_mod`, exactly (V3). Load-weighted, six carry zones.

| year | grain | gap | **Δ₁ identity** | **Δ₂ cost level** | **Δ₃ above-cost** |
|---|---|---|---|---|---|
| 2023 | **annual** | +0.668 | **+1.294 (193.7 %)** | −0.637 (−95.4 %) | +0.011 (1.7 %) |
| 2023 | Jun+Jul | +1.440 | −5.090 (−353.4 %) | +6.531 (+453.4 %) | +0.000 (0.0 %) |
| 2023 | top-200 | +12.716 | +3.681 (28.9 %) | +8.706 (68.5 %) | +0.330 (2.6 %) |
| 2024 | **annual** | +2.608 | **+2.037 (78.1 %)** | +0.287 (11.0 %) | +0.284 (10.9 %) |
| 2024 | Jun+Jul | +6.535 | +6.405 (98.0 %) | −0.750 (−11.5 %) | +0.880 (13.5 %) |
| 2024 | top-200 | +18.798 | +17.988 (95.7 %) | −1.339 (−7.1 %) | +2.149 (11.4 %) |
| 2025 | **annual** | +7.082 | **+11.966 (169.0 %)** | −6.156 (−86.9 %) | +1.272 (18.0 %) |
| 2025 | Jun+Jul | +19.824 | +18.171 (91.7 %) | −2.673 (−13.5 %) | +4.326 (21.8 %) |
| 2025 | top-200 | +74.030 | +58.321 (78.8 %) | −2.437 (−3.3 %) | +18.146 (24.5 %) |

**B-IDENT is met on its own terms:** Δ₁ ≥ 50 % at the adjudicating annual grain
(**169.0 %**), and the market's implied heat rate lands **inside the model's own
gas heat-rate range in 96.9 %** of Jun+Jul 2025 hours against a pre-registered
≥ 60 % bar. **B-ABOVE does not fire on the primary basis** (Δ₃ 18.0 % < 40 %).

### 4.1 The §3.1 census — the class is right, the position is not

Capacity-weighted class of the model tranche sitting at each implied heat rate:

| year | top-200, market-implied | top-200, model's own |
|---|---|---|
| 2023 | CT_PEAKER 41.0 %, CC_REGULAR 36.0 % | CT_PEAKER 69.4 %, CC_CHP 14.5 % |
| 2024 | CT_PEAKER 62.0 %, ST_GAS 13.0 % | CT_PEAKER 68.8 %, ST_GAS 16.6 % |
| 2025 | **CT_PEAKER 69.0 %**, CC_REGULAR 14.0 % | **CT_PEAKER 74.1 %**, ST_GAS 13.2 % |

Mean implied heat rate, model vs market: **11.93 vs 28.83** (2025 top-200),
**9.64 vs 14.94** (2025 Jun+Jul), **7.99 vs 11.29** (2025 annual). At the
*median* Jun+Jul hour the two sit almost on top of each other (fleet percentile
**0.463 vs 0.483**) — **the identity gap is entirely in the upper tail of
hours**, which is the same object miso-152 described as "the model forms no
summer peak at all", measured in heat-rate units.

### 4.2 S-CEIL fired, and its sensitivity is reported because it cuts against the branch

`HRmax` is owned by a tranche carrying **0.0025 %** of gas capacity at a heat
rate of **113.88** MMBtu/MWh — far under the 0.5 % trigger. Re-running the whole
decomposition on the capacity-weighted **p99** ceiling (**43.69**), as
pre-registered:

| year | grain | Δ₁ | Δ₃ |
|---|---|---|---|
| 2025 | annual | +9.915 (140.0 %) | **+3.323 (46.9 %)** |
| 2025 | Jun+Jul | +12.702 (64.1 %) | +9.795 (49.4 %) |
| 2025 | top-200 | +37.287 (50.4 %) | **+39.180 (52.9 %)** |

**Stated against the branch: on the p99 ceiling Δ₃ crosses the 40 % B-ABOVE
threshold at the annual grain (46.9 %) and at top-200 (52.9 %).** Δ₁ still
clears 50 % on both grains, so B-IDENT is taken on the primary basis — but the
honest reading is that **the above-cost share is basis-sensitive between 18 %
and 47 %**, and that upper figure bounds how much of the annual gap any
identity lever can reach. That residue is **C3c-adjacent**: this session does
**not** touch the C3c ledger, proposes no tail mechanism, and tunes nothing to
the tail.

---

## 5. The priors, scored — one confirmed, one missed high, one refuted with the wrong sign

* **(iii) ABOVE-COST: CONFIRMED AS STATED.** Registered 5–25 %, centre 15 %;
  measured **18.0 %** (2025 annual, primary basis). The only prior that landed.
* **(i) IDENTITY: DIRECTION CONFIRMED, MAGNITUDE ABOVE THE BAND.** Registered
  45–80 %, centre 60 %; measured **169.0 %**. My bands were built assuming three
  non-negative channels; Δ₂'s negative sign pushes Δ₁ above 100 % by
  construction. The band was mis-specified, not merely mis-centred, and I say so.
* **(ii) COST LEVEL: REFUTED, AND ON THE WRONG SIDE OF ZERO.** Registered
  5–35 %, centre 20 %; measured **−86.9 %**. **S-FUEL does not fire** (it needs
  ≥ +50 %); **S-SIGN FIRES**, which is the stronger and less comfortable outcome
  — I pre-registered a channel as a candidate *contributor* and it is a
  candidate *worsener*.
* **P-4 (year ordering): CONFIRMED.** Δ₁ = +1.294 / +2.037 / +11.966 — the
  dominant channel is **9.2× smaller** in the passing year.

### 5.1 S-2023 also fired, and the pre-registered consequence is honoured

2023's gap is **+0.668 $/MWh** (~2 % of price) while Δ₁ is **193.7 %** and Δ₂
is **−95.4 %** of it — channels cancelling in the passing year, exactly the
S-2023 condition. **Per the trigger's own instruction, the 2025 attribution is
labelled PROVISIONAL.** Bounding the provisionality with numbers: the cancelling
pair in 2023 is ±$1.3 against 2025's ±$12.0, so the 2025 attribution is not an
artifact of the same cancellation — but it is not independently confirmed by
2023 either, and 2023's Jun+Jul cell (Δ₁ **−5.090**, Δ₂ **+6.531**) is where the
cancellation is largest. That cell is driven by the 2023 Chicago-citygate basis
(the primary `G_act`) running **+2.12 / +1.55 $/MMBtu** over Henry Hub in
June/July 2023 — a citygate print that carries LDC distribution charges a power
plant does not pay, i.e. a known upward bias in `G_act` for that window. That
bias makes the S-SIGN result **conservative**: on the delivered-to-electric-power
comparator, which has no such charge, the model's gas is **higher still**
(+1.543 $/MMBtu in 2023).

---

## 6. Traps — every counter-measurement, at full magnitude

| # | Counter-measurement | Result |
|---|---|---|
| **T-1** | Bundle repointed and asserted | **PASS** — `_miso134.BUNDLE` repointed to `miso148_basis_B`, asserted at import |
| **T-2** | Zero 3-argument `getattr(` on the offer path | **PASS** — count **0**; all three candidates replaced by direct attribute access after asserting the fields are required (`reliability_floor_overrides`, `ReliabilityFloorSpec.enabled`, `Generator.plant_group`), so a rename fails loudly. `ruff` clean on both probes |
| **T-3** | Disbelieve clean zeros | **PASS, AND IT PAID AGAIN** — the floors-OFF twin returned Δ = **0.0000** in all 27 cells; that zero was given a second derivation (the structural argument in §3) rather than accepted, and it is the reason §3's conclusion is stated as "cannot matter" rather than "did not matter" |
| **T-4** | Production types only | **PASS** — every array from `generators_to_fleet_arrays`; no `SimpleNamespace` |
| **T-5** | `MISO_external*` are IMPORT NODES | **PASS** — asserted 6 carry zones; import nodes excluded from every aggregate |
| **T-6** | `weather_year` pinned per solve year | **PASS** — `dataclasses.replace(cfg, weather_year=y)`; V1's 3/3 reproduction is its control |
| **T-7** | An inert instrument looks like a fix | **PASS** — every channel reported in **$/MWh** as well as share |
| **T-8** | Production functions, never re-implementations | **PASS** — `inject_reliability_floor.__module__` asserted; the measured LMP reader is the production `derive_miso_hub_lmp` path |
| **T-18** | The floors are gitignored | **DISCLOSED AND MEASURED** (§3) |
| **T-19** | A floored tranche is not marginal | **VACUOUS HERE** — the census is computed on heat rates, not on a marginal-tranche search, so no floored row can be mistaken for a price-setter |
| **T-20** | `IHR` explodes for small `G` or `P < V` | **PASS** — excluded, never clipped: **42 / 24 / 6** zone-hours (**0.080 / 0.046 / 0.011 %**) |
| **T-21** | Congestion makes "the marginal unit" a fiction in a zone-hour | **REPORTED, AND IT IS LARGE** — cross-zone spread > $1/MWh in **21.1 / 24.4 / 54.2 %** of hours. The adjudicating annual figure is the **ISO load-weighted** aggregate, and the per-zone cells are reported in the record |
| **T-22** | Hub-vs-zonal basis mismatch masquerading as a channel | **CAUGHT AND FIXED MID-SESSION.** The first construction averaged the eight named hubs equally — four of which map to MISO-South — and read **6–7 % below** the bench. Replaced by the committed `actual_lmp_hourly_MISO.parquet`, whose load-weighted mean reproduces the gated `rt_lw` to **32.847/32.301/45.455** against **32.85/32.30/45.46** (gate V1b). The per-zone hub series is reported as a **labelled companion** and runs **−7.9 / −9.0 / −7.2 %** below the primary |
| **T-23** | Δ₃ defined off an unbounded max | **S-CEIL FIRED; sensitivity reported** (§4.2) |

---

## 7. Phase 1 — the lever followed the decomposition, and the decomposition killed both candidates

### 7.1 `gas_hub_basis_overlay` MISO **`U` → `R`**

Rejected on **two grounds, neither of them the residual** (rule 1 `[R-STRUCT]`):

1. **Its own measured input points the wrong way.** The model's delivered gas is
   already **above** both measured comparators in all three years (§1 result 2).
   The overlay would *cut* the model's gas by $0.89/MMBtu in 2025. It is not a
   candidate for a level deficit; it is a candidate for making one.
2. **Rule 14 `[R-ACCURATE]`.** `apply_hub_basis_overlay` **replaces** every gas
   unit's price with one ISO-wide hub-month series, *"superseding both the
   ISO-month EIA-923 series and the per-plant F923 overwrite"*
   (`data/fuel/hubs.py:1268-1272`). That is right for NEISO — two plants report
   Schedule-5 receipts — and wrong for MISO, where miso-153 Ground 3 measured the
   model reproducing across-plant delivered-gas dispersion at **5.321 → 3.593 →
   3.413 $/MMBtu** against an F923 source of **5.657 → 3.748 → 3.679**. Arming it
   would trade a faithful per-plant measurement for a flat one.

Rule 19 `[R-ONE-MECH]` note: MISO's ISO-wide gas **level** remains owned by the
F923/EIA-923 series alone. `miso_zonal_gas_basis` (armed) is **mean-zero** by
construction and owns only the north/south gradient; `miso_winter_citygate_daily`
(armed) is **Dec/Jan/Feb and mean-preserving within month**. Neither can move a
June/July level, and neither is changed here.

### 7.2 `ramp_envelopes` MISO **`U` → `I`**

The identification was **pre-checked before any solve**, with its kill rule fixed
before the numbers were read: *the model must out-ramp the measured fleet at the
p99 1-h move in ≥ 2 of 3 years, else the lever is inert.* Model P1 thermal
dispatch (committed `class_hourly`) against measured EIA-930 MISO thermal
(`NG`+`COL`+`OTH`), same fixed-CST clock, same non-leap calendar:

| year | p50 | p90 | **p99** | max | Jun+Jul p99 |
|---|---|---|---|---|---|
| 2023 | 0.59 | 0.73 | **0.83** | 0.74 | 0.84 |
| 2024 | 0.63 | 0.72 | **0.83** | 0.17 | 0.81 |
| 2025 | 0.66 | 0.79 | **0.88** | 0.77 | 0.87 |

**The kill rule fires 0 of 3.** MISO's model is *smoother* than the real fleet at
every quantile of every year — it under-ramps by 12–41 %. A ramp envelope
constrains movement; applied here it would tighten a fleet that already moves too
little, which cannot lift a marginal unit and would push the residual further the
wrong way. **PJM's `K` transfers nothing** (rule 25 `[R-ISO-SCOPE]`): pjm-140
armed `ramp_limits` because its model out-ramped the real fleet **1.4–1.7×**;
MISO measures the reciprocal.

*(The 2024 `max` ratio of 0.17 is a single measured 45,174 MW EIA-930 1-h step —
an obvious reporting artifact. It is reported rather than dropped; the p99 is the
quoted statistic precisely because it is insensitive to it.)*

### 7.3 `measured_ramp_capability` stays **`U`** — deliberately not minted

This session measured **fleet** ramp, not the **per-asset reserve qualifier**,
so no verdict is minted on it. Two committed measurements now stand against it
and a successor must confront both: MISO's model under-ramps its own fleet
(§7.2), and miso-153's D-4 found reserves **INERT at the summer peak** — zero
binding hours, zero shortfall, dual $0.00, across all three families × three
years × 1,464 Jun+Jul hours. A qualifier that tightens a constraint which never
binds cannot move a price.

---

## 8. Where this leaves the lane

**Established, and a successor should not re-derive it:**

1. MISO's C3a miss is **marginal-unit identity in the upper tail of hours**, not
   a level offset and not a markup deficiency (the IMM's +3.0 % / −2.5 %
   price-cost mark-up with a de-minimis output gap already said the market clears
   at cost; this measures the model side and agrees).
2. **The delivered-fuel channel is exhausted and points the wrong way.** Any
   future proposal to lift MISO's price level through gas must first explain why
   the model's gas should be *higher* than both measured comparators.
3. **The class is right and the stack position is wrong**: `CT_PEAKER` is
   marginal in 74.1 % of 2025's top-200 zone-hours, at an implied heat rate of
   11.93 against the market's 28.83.
4. **The queue's two named identity levers are closed** (`R` and `I`).

**The lever queue is therefore EMPTY of named, un-adjudicated candidates, and
this session does not invent one.** What the measurement leaves open, stated as
a question rather than a lever: **what makes the model's CT stack stop climbing
at ~12 MMBtu/MWh when 28.8 is inside its own fleet's range?** The two enumerated
possibilities — a too-large idle cushion at the peak (miso-153 D-1: 16.2 GW idle,
55.8 % of CT's own availability, 6.31 GW within $20/MWh of the clearing price)
and the C3c-adjacent above-cost residue (§4.2, 18–47 % basis-sensitive) — are
**not adjudicated here**, and the second is governed by the C3c ledger's
frontier designation. Opening either needs its own charter, its own measured
identification, and an owner decision; **rule 20 `[R-DOF]` forbids closing the
remainder with a tuned value**, and the against-interest arithmetic below
constrains any candidate before it is built.

**AGAINST-INTEREST BOUND, now computed rather than restated.** 2023 passes C3a at
−1.98 %, and the bound makes a lever lifting 2023's mean by more than **+3 %** a
REGRESSION. **2023's own identity gap is +$1.294/MWh on a model mean of $32.18 —
+4.02 %.** So **a lever that closed 100 % of the identity channel uniformly would
BREACH the bound by ~1.0 pp.** Any Phase-1 candidate must either close ≤ **74 %**
of 2023's Δ₁ or be scoped so that it binds where 2023's Δ₁ is not — and 2023's
Jun+Jul Δ₁ is **negative** (−5.090), so a summer-scoped mechanism has room the
annual figure hides. **This number is on the record before any lever exists, so
it cannot be re-derived to fit one.**

---

**Artifacts.** Probes `scripts/probes/_miso156_c3a_decomposition.py` and
`scripts/probes/_miso156_ramp_precheck.py` (both `ruff` clean). Records
`results/calibration/_miso156_c3a_decomposition.json`,
`results/calibration/_miso156_ramp_precheck.json`. PREREG `162a51d`, blob
`7f124d18`. Keeper `2026-08-09-miso-148-basis-aware`, **unchanged**.

# PRE-REGISTRATION miso-115 — is MISO's overnight trough marginal unit mis-specified?

**Written and committed BEFORE any measurement was taken.** Session miso-115,
2026-08-02, branch `claude/miso-115-trough-marginal-unit-lx2apo`, off
`origin/main` at `b9a96a9`. Phase 1 is a **no-LP measurement**; no solve is
spent until this document's decision rule returns a verdict.

## 1. The question

miso-114 §2.2 decomposed MISO's overnight price residual into (a) a near-flat
**level offset of +$4…+$8/MWh across net-load deciles 0–8** and (b) a top-decile
convexity deficit (miso-89's ledgered object, out of scope here). §2.3 showed
the model reaches the trough by filling a 1.5–1.7 GW import hole and a 3.4–3.9
GW gas hole with 2.6–3.7 GW of extra coal **while keeping 1,907 / 2,415 / 2,350
MW of `CT_PEAKER` + `ST_GAS` generating at h1–h3**.

> **Measured question.** What is MISO's *CAMPD-observed* CT + gas-ST generation
> at h1–h3, 2023–2025, against the model's 1,907 / 2,415 / 2,350 MW?

EIA-930 cannot answer this — it does not split gas by prime mover. CAMPD's
facility-level `unitType` does, which is why this measurement is available now
and was not available to miso-114.

## 2. Why the answer is decisive — and why it is about IDENTITY, not QUANTITY

miso-114 measured the model's own local stack slope in the overnight window at
**0.24–0.40 $/MWh per GW**. At that slope, a level offset of $6/MWh would
require a **~20 GW** quantity error. No plausible commitment error is that big.

So the level offset **cannot** be a quantity defect. It can only be the
**identity and price of the unit setting the trough price**. That makes the
measurement below a test of identity: if the real MISO fleet does not run
peaking/steam gas overnight and the model does, then a peaking-band offer
(CT heat rate ≈ 10–11 MMBtu/MWh) is clearing MISO's trough where reality clears
it on a combined-cycle or coal band. That is a structural mis-specification with
a measured identification, and it is chartable.

## 3. Quantity definition (fixed before measuring)

* **Model side** — `class_hourly_<year>.parquet`, `pass == "P1"`, keeper bundle
  `results/calibration/miso109_hy_level_B`, classes `CT_PEAKER` + `ST_GAS`,
  column `mw`, averaged over model hours with `hour % 24 ∈ {1,2,3}`. This is
  **generation**, not committed capacity — miso-114's "online" wording notwith-
  standing, `class_hourly.mw` is the LP's dispatched MW.
* **CAMPD side** — the apples-to-apples comparable is therefore **gross load
  (MW), not nameplate**: hourly gross load of MISO units whose facility-level
  `unitType` is a **combustion turbine** or a **gas-fired steam turbine**,
  averaged over the same three hours of the same 8760-hour calendar.
* Commitment-side quantities (units with non-zero operating time, and their
  capacity) are reported as **descriptive secondaries**. They are **not** gates
  — the model number they would be compared against does not exist.

## 4. Decision rule — PRE-REGISTERED

Let `R_y = measured_CAMPD_y / model_y` for `y ∈ {2023, 2024, 2025}`.

| verdict | condition | consequence |
|---|---|---|
| **MIS-SPECIFIED** | `R_y ≤ 0.60` in **≥ 2 of 3** years **and** `R_y < 1` in **all 3** | Trough marginal unit is mis-specified. Structural cause, measured identification → **charter Phase 2**: prereg with gates + kills, then **one** single-delta A/B against a same-HEAD zero-delta control. |
| **COMPARABLE** | `R_y ≥ 0.75` in **≥ 2 of 3** years | The level offset is a **pricing** question on the same units. Say so, narrow the family, **stop**. No solve. |
| **INCONCLUSIVE** | anything else (incl. `0.60 < R_y < 0.75` majority, or split signs) | **Defaults to refuse.** An inconclusive measurement is not a charter. Report the number, narrow the family, stop. |

The middle band defaults to *refuse* deliberately: this lane's discipline
(miso-103/104/105/107/108) is that a refusal on measurement is a full result,
and a ~3 h / ~15.5 GB MISO per-plant A/B is not spent on an ambiguous signal.

## 5. Kills — conditions that void the verdict regardless of `R_y`

Any of these forces **INCONCLUSIVE** and no charter:

1. **K1 coverage.** CAMPD reports only units subject to Part 75 (broadly ≥25 MW
   fossil serving a generator). If CAMPD-covered CT + gas-ST **capacity** in
   MISO is materially below the model's `CT_PEAKER` + `ST_GAS` capacity, a
   generation shortfall is a coverage artifact, not a market fact. Reported as
   a capacity ratio; **> 20 % capacity shortfall voids** a MIS-SPECIFIED verdict
   (it cannot void COMPARABLE, which is the conservative direction).
2. **K2 footprint.** MISO membership is **not** state-wise — IL, IN, MI, MO and
   WI are split with PJM. The MISO unit set must come from the repo's existing
   plant→ISO registry / class crosswalk (**rule 24 `[R-REGISTRY]`**: no hand map).
   If > 15 % of matched capacity cannot be resolved to an ISO, void.
3. **K3 clock.** CAMPD is stamped in **local standard time** with no DST shift;
   the model's hour index convention must be established from the repo, not
   assumed, and the two must be aligned before the h1–h3 slice is taken. A
   mis-aligned clock moves the trough and voids the comparison.
4. **K4 calendar.** 2024 is a leap year; Feb 29 is dropped so both sides are the
   same 8760 hours (rule 8 `[R-8760]`).
5. **K5 class-mapping fidelity.** The CT/ST split must use the repo's existing
   taxonomy crosswalk. If the model's `CT_PEAKER` / `ST_GAS` classes contain
   units that CAMPD's `unitType` would map elsewhere (or vice versa), the
   mapping asymmetry is reported and, if it exceeds 20 % of either side's
   capacity, voids.

## 6. Bars this session inherits and will not cross

* **No `miso_cc_coal_rebalance`.** Its target is defined against another *model*
  quantity with no measured identification — rules 5 `[R-NO-MAGIC]` / 21
  `[R-DOF]` / 24 `[R-REGISTRY]`, whatever it does to the residual.
* **No `miso_pjm_lmp_import_pricing`** for this defect (refuted ex ante,
  miso-114 §4).
* **No** chartering the seam hour-of-day mis-shape as a C7/C3a instrument
  (real, but 4–7 % of the residual — rule 1 `[R-STRUCT]` only).
* **No** re-opening the top-decile convexity deficit (miso-89, ledgered) and
  **no** re-licensing `miso_firm_import_floor` (an outcome pin, rule 13).
* **No** re-test of the SPENT regulated-PRB self-commitment family
  (`coal_prb_committed_dispatchable` miso-111 R, `coal_prb_committed_split`
  miso-112 R, `miso_coal_night_floor` miso-113 I).
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; MISO holds no calibration-complete
  marker, so no holdout year is touched, in measurement or in any solve.

## 7. If Phase 1 refuses

The cross-ISO queue (`docs/mechanism-testing-matrix.md` §5.4) items still
genuinely untested at MISO, in the order this session would consider them:
**item 4 `measured_ct_heat_rates`** (audit-grade; MISO derives its own artifact
per rule 25 — and it lands directly on this same trough marginal-unit question,
which is why it comes *after* Phase 1), **item 5 `dual_fuel_switching`**, and
**`gas_offer_margin_zonal_anchor`** (MISO cell `U`; PJM's `I` transfers nothing
per pjm-144).

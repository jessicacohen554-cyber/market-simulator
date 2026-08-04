# PREREG miso-125 — the CHP **prime-mover** rate split: one eGRID plant rate spanning two machines

Session miso-125, 2026-08-04, branch `claude/miso-125-backcast-calibration-en6kbc`,
off `origin/main` at `d7363b0e`. **Written and committed BEFORE any statistic,
any derive and any solve** (the nyiso-120 standard, which is stricter than
"before any arm").

Current MISO keeper: `2026-08-04-miso-124-dualfuel-rearm`
(`results/calibration/miso124_dualfuel_B`), determination `NOT-YET`, sole FAIL
C7 `COAL_PRB` diurnal shape ×3y, ledgered caveats {C3a, C3c}.
`audit_keepers --iso MISO` 0/0.

---

## 1. The lever, and why this one

`docs/mechanism-testing-matrix.md` §5.4 and miso-122 §7 handoff item 4 leave
exactly two named-but-unchartered successors. miso-123 took the seam one and
**closed the whole availability-ceiling class**. This session takes the other:

> miso-118 H-E — the `CT_CHP`-side plant-level rate at MISO 55088 Dearborn.

It is MISO's **only** remaining named, un-adjudicated, non-data-blocked §5.4
item. Everything else is spoken for: the C7 `COAL_PRB` regulated-self-commitment
family is closed (`R`/`R`/`I`, rule 19 `[R-ONE-MECH]` forbids a fourth
mechanism), items 1–2 are data-blocked at a **sourcing** step (Form 580 count,
`docs/handoffs/miso-coal-contract-tonnage-data-ask-2026-07.md` §8), item 3 is
`R` ex ante, items 4/5/6 are `K`/`I`/`I`, miso-122 executed the hybrid-cogen
scope gate and miso-123 closed the seam hour-of-day lane.

### 1.1 Scope discovery recorded up front — the brief's items (A) and (B)

The session brief offered three items. Two are **not** taken here, on evidence
found before anything was written:

* **(A) NYISO 2493 East River is SPENT.** `nyiso-120` (2026-08-04, commit
  `1f552be8`) already re-derived the NYISO artifact with the miso-122 gate and
  registered `2026-08-04-nyiso-120a-control`. On disk, 2493/`CT_CHP` already
  reads `below_credited` with `dark_fuel_share` 0.375058, and
  `FINDING-nyiso120-eastriver-scope-gate-2026-08-04.md` answers the open
  question the brief posed ("which meter is wrong"): **neither — they agree to
  1.0 %**, and `PLHTIAN` is already the power train's fuel, so the add-back was
  double-counting. That session's §4–§7 are unwritten and its **arm B has not
  solved** (`_nyiso120_scope_gate_ab.json` absent) — it is a live NYISO lane
  mid-flight, and this session does not step on it (rule 25 `[R-ISO-SCOPE]`).
* **(B) NEISO 1595 Kendall is live but NOT taken.** NEISO's artifact carries no
  `dark_fuel_share` column at all, so it is un-re-derived. It stays NEISO's.

Taking (C) keeps this session inside MISO's own lane, on MISO's own keeper,
with MISO's own data — rule 25 clean by construction.

### 1.2 The defect, at grain

`scripts/data/derive_chp_power_only_heat_rates.py` writes **one row per
`(plant_code, plant_group)`** and
`market_sim.data.fleet.campd_bins.measured_chp_heat_rates` applies it on that
**pair**. But the *rate itself* comes from `egrid_chp_split(vintage)`, which is
**plant**-grain: `(PLHTIAN + CHPCHTI) * (1 - dark_share) / PLNGENAN`, one number
per ORIS code. So a plant hosting two prime movers gets **the same rate on both
rows** — the row keying advertises a per-class rate the derive never computes.

Measured on the committed artifact (`chp_power_only_heat_rates_MISO.csv`, HEAD):

| plant | class | capacity MW | `heat_rate` applied | `heat_rate_credited` | flag |
|---|---|---|---|---|---|
| 55088 Dearborn Industrial Generation | `CC_CHP` | 350.0 | **6.9573** | 6.3464 | `ok` |
| 55088 Dearborn Industrial Generation | `CT_CHP` | 165.0 | **6.9573** | 6.3464 | `ok` |

A combined cycle and a simple-cycle turbine are different machines. MISO's own
`ok` population separates them: `CC_CHP` rows run 6.96–11.21, `CT_CHP` rows
8.05–12.42. **6.9573 is at the bottom of the CC band and below the entire CT
band** — the blend charges the 165 MW `CT_CHP` tranche a combined-cycle heat
rate. `measured_chp_heat_rates = True` is armed on the keeper
(`miso124_dualfuel_B/run_config.json`), so both rows are live in the LP today.

### 1.3 Charter grounds, stated up front and binding

This is a **rule 14 `[R-ACCURATE]`** item and **NOTHING ELSE.** It changes the
**grain** of an existing measured input inside the already-armed
`measured_chp_heat_rates` mechanism — the rule 19 `[R-ONE-MECH]`-correct shape,
identical to miso-122's. **No new `ScenarioConfig` field, no new matrix row, no
change to arming.**

* It is **NOT** chartered as a C7 `COAL_PRB` instrument. It cannot close C7 and
  no result here may be quoted as C7 progress.
* It is **NOT** chartered as a C3a or C3c instrument.
* It **ships, or is refused, on whether the input is more accurate — whatever
  it does to the residual** (rule 1 `[R-STRUCT]`, both directions). A worse fit
  is a discovered bug elsewhere, not grounds to revert (rule 14).

---

## 2. The construction, fixed before measurement

For plant `p`, from the **same vintage year** as `--vintage` (no vintage mixing),
over CAMPD unit-level rows, restricted to **power-train** units — those with
annual `grossLoad > 0`, i.e. the exact complement of scope gate 3's dark set, so
the dark boiler fuel is removed **once**, by gate 3, and can never re-enter here.
Prime-mover family `m` from the `unitType` prefixes already in the module
(`_CC_PREFIX = "combined cycle"`, `_CT_PREFIX = "combustion turbine"`):

```
f_m = Σ heatInput over power-train units of family m  ÷  Σ heatInput over ALL power-train units
g_m = Σ grossLoad  over power-train units of family m  ÷  Σ grossLoad  over ALL power-train units

hr_m = hr_plant × (f_m / g_m)
```

Four properties, all asserted in the probe rather than assumed:

1. **Generation-share preserving by construction.** `Σ_m g_m · hr_m = hr_plant ·
   Σ_m f_m = hr_plant`. The split is a pure **reallocation inside the plant**:
   the plant's total fuel charge at its own generation mix is unchanged, and
   **zero re-basing is smuggled in** alongside the correction.
2. **A ratio of shares, never a level.** It requires the gross-to-net parasitic
   factor to be common **across families at one plant** — not equal to 1, and
   not reconciled to eGRID's level. That is strictly weaker than the level
   reconciliation the module docstring rules out (`compute_parasitic_factors`
   cannot supply a CHP-specific gross-to-net ratio), and it is the same
   share-not-subtraction discipline gate 3 uses.
3. **Strict no-op where the phenomenon is absent.** A single-family plant gets
   `f_m = g_m = 1` and a byte-identical rate. **No threshold** (rule 5
   `[R-NO-MAGIC]`), so every non-mixed plant in every ISO is unchanged.
4. **Computed over all target-class rows present, applied only to `ok` rows.**
   A plant whose `CT_CHP` row is excluded still contributes its CT fuel and
   generation to the shares — because the plant rate *blends that CT in*, so the
   surviving `CC_CHP` row is only correct once it is netted out. A CEMS family
   with no target-class row (an ST train) participates in both denominators and
   receives no applied row.

Zero fitted parameters (rule 24 `[R-REGISTRY]`). Nothing is swept against a
residual. Rule 23 `[R-FROZEN-DERIVE]`: the re-derivation cites a **scope-gate /
grain logic change on measured grounds**, never a residual — the same warrant
miso-122 and nyiso-120 used.

**Rule 13 `[R-MEASURED]` admissibility.** A machine's fuel-conversion intensity
is a physical property, the same class as the CAMPD min-stable loads and the
CO2 rates. It regenerates forward from the published pipeline (every CAMPD year
carries `unitType` + unit-grain `heatInput`/`grossLoad`; every eGRID vintage
carries both halves) and responds to changed conditions — a plant that
re-configures its trains regenerates different shares. It is an **INPUT**, never
a measured outcome fed back to close a residual.

---

## 3. Kill criteria, pre-declared and in order

**KE1 — prime-mover resolvability (data-side gate).** CAMPD at 55088 must resolve
**≥ 2 distinct power-train families**, and every power-train unit must map to
exactly one family by `unitType` prefix. Guards, both mandatory:
(a) the `facilityId` filter must return **> 0 rows** — CAMPD `facilityId` is
**STRING**-typed and an int filter silently matches zero (miso-121 hit this
twice), so the probe reuses the module's own `pd.to_numeric(..., errors="coerce")`
pattern and **asserts non-empty**; (b) the plant's recomputed CEMS annual total
must reproduce the committed artifact's `cems_heat_mmbtu` for the same year.
**FAIL ⇒ the split is undefined**; the item closes as a **data-side null** — not
an `I`, no solve, no derive change.

**KE2 — population scope.** Enumerate every MISO `(plant, class)` row whose plant
carries ≥ 2 target-class rows, and report which are `ok`. Pre-declared
expectation from the committed artifact: **exactly one applied plant, 55088,
350.0 MW `CC_CHP` + 165.0 MW `CT_CHP` = 515.0 MW**. (50973, 56309 and 58161 also
appear twice but are `not_unfired_topping` on both rows, so nothing is applied
there.) A larger enumeration is in scope; a smaller one contradicts the artifact
and stops the session.

**KE3 — INERT-BY-ARITHMETIC (zero-solve route).** Compute `hr_CC`, `hr_CT`.
Declare **`I` with zero solves** if `max_m |hr_m / hr_plant − 1| < 0.02`.
Ground, stated as arithmetic and not as a preference: the LP prices
`mc = hr × fuel`, and at the keeper's own gas ($2.54 / $2.19 / $3.52 per MMBtu,
`miso124_dualfuel_B/meta.json`) a 2 % move on 6.9573 is 0.139 MMBtu/MWh =
**$0.35 / $0.30 / $0.49 per MWh** — narrower than the plant's own tranche offer
steps, so no tranche can change rank against its neighbour. If KE3 fires the
derive change **still ships** (rule 14: accuracy is the ground); what KE3
adjudicates is only whether an LP A/B is *warranted*.

**KE4 — INERT-BY-MARGINALITY (zero-solve route), per miso-121.** Read the
keeper's **committed** `hourly/class_hourly_<year>.parquet` sidecars — no
replay. Declare **`I` with zero solves** if, in all three years, the `CC_CHP` and
`CT_CHP` classes jointly (a) hold < 1 % of price-setting hours where the sidecar
resolves marginality, and (b) sit at a bound (floor / must-run / `pmax`) in
> 99 % of hours, i.e. the LP has no freedom to respond to a cost change. The
probe reports whichever of these the sidecar schema actually supports and says
so explicitly rather than substituting a proxy.

**KE5 — control integrity** (only if it goes live). A same-HEAD zero-delta arm A
must reproduce the incumbent keeper's scorecard **exactly** — determination,
all nine criterion statuses, ledgered caveats. Every A/B delta is quoted against
arm A, never against the committed keeper.

**KE6 — firing proof.** This is an **INPUT-DELTA** lever, so the warm-P1
heuristic does **not** apply: a heat rate enters at fleet load and **both**
passes carry it. Firing is proven two ways, not inferred: (a) a pre-arm
`load_fleet_from_csv` check reading the 55088 `CT_CHP` generators' `heat_rate`
before and after the artifact change; (b) a post-arm **per-class energy** delta.
A null is not trusted until both fire.

---

## 4. The four DO-NOT-MISREAD guards, applied ex ante

* **miso-119** — `max |Δoffer|` is an **upper bound only**; it over-predicted the
  realized price effect by two orders of magnitude. No liveness claim here rests
  on the heat-rate delta's magnitude.
* **miso-121** — **binding is not marginality.** The p50 over binding hours
  over-predicted by five orders. KE4 is written on **marginal share**, and no
  screen in this session argues liveness from any percentile of an offer delta.
* **miso-122** — `max_abs_class_hour_mw` is **not** a mechanism magnitude at
  MISO: it reads 912.5 MW for unrelated levers because it lands on the import
  class where one seam band flips. This session reads **per-class ENERGY
  deltas** and will not quote that statistic.
* **miso-124** — the price response is **not stable across keepers** (the same
  flag moved max zonal |dLMP| 0.0003 on miso-117b and 1.383 on miso-122b,
  because the scope gate changed *which unit is marginal*). No price magnitude
  is carried in from miso-122's 0.049 / 0.039 / 0.075; any bar is re-measured
  against `miso124_dualfuel_B`, the keeper actually being replayed.

---

## 5. What is settled and is NOT re-opened (rule 28a DO-NOT-REDO)

* **C7 `COAL_PRB` regulated self-commitment — CLOSED** (miso-111 `R` / 112 `R` /
  113 `I`, confirmed 114). Not touched, not measured, not quoted.
* **Seam hour-of-day shape — CLOSED at miso-123**, all three mechanism classes
  spent (price / ceiling / floor). No envelope statistic is re-derived and
  `miso_seam_flow_percentile` is not swept.
* `dual_fuel_switching` `K` (armed, tested verdict INERT),
  `gas_offer_margin_zonal_anchor` `I`, `hydro_budget_nameplate_aware` `I`,
  `pjm_da_virtual_bids` `R` ex ante, `measured_ct_heat_rates` `K`,
  `measured_chp_heat_rates` `K` + hybrid-cogen scope gate EXECUTED (miso-122).
* **Data-blocked, not attempted:** the C7 `COAL_PRB` cost-side and
  contract-tonnage routes. The bounded next step there is a **sourcing pass**,
  not a solve.

---

## 6. Rule duties this session owes

* **Rule 15** — every completed run registered on the backcast dashboard in this
  session, keeper *or* rejected. If a zero-solve route (KE1/KE3/KE4) adjudicates
  the item, this prereg's obligation is discharged by **explicitly stating that
  the no-LP phase produced no run**.
* **Rule 16** — if it goes live, `--years 2023 2024 2025` in **ONE**
  `replay_keeper.py` invocation per arm, one bundle. Never a per-year chain
  (`kwargs['years'] = args.years`, so a chain writes `meta.json` with only the
  last year and silently breaks K5).
* **Rule 22** — `--year` strictly `{2023, 2024, 2025}`. MISO holds **no**
  `calibration-complete` marker, so no holdout year may be solved, scored **or
  read**. LOO within training years before proposing any promotion.
* **Rule 25 `[R-ISO-SCOPE]`** — this is MISO's lane. The re-derive runs for MISO;
  the other four ISO artifacts are regenerated **only** to demonstrate the
  strict no-op, and any ISO whose bytes move is reported and **not** shipped
  from this session.
* **Rule 26** — arming visible in `run_config.json` (unchanged here: the input
  moves, not the flag; the artifact change is the delta and is committed).
* **Rule 28b** — the `measured_chp_heat_rates` × MISO cell and the §5.4 queue
  prose are stamped in **this** session, inert and rejected outcomes included.
* **Rule 27 `[R-PUSH]`** — exact on-disk bytes; blob-verify line count + hash
  after any push touching a ≥ 300-line file (`mechanism-matrix.js`,
  `mechanism-testing-matrix.md`, `derive_chp_power_only_heat_rates.py`,
  `docs/calibration-log/miso.md` all qualify).

---

## 7. Deliverables

| artifact | path |
|---|---|
| this prereg | `results/calibration/PREREG-miso125-chp-prime-mover-split-2026-08-04.md` |
| no-LP probe | `scripts/probes/_miso125_chp_prime_mover_split.py` |
| probe record | `results/calibration/_miso125_prime_mover_split.json` |
| probe transcript | `results/calibration/PROBE-miso125-chp-prime-mover-split-2026-08-04.txt` |
| A/B scorer (if live) | `scripts/probes/_miso125_pm_split_ab.py` |
| A/B record (if live) | `results/calibration/_miso125_pm_split_ab.json` |
| finding | `results/calibration/FINDING-miso125-chp-prime-mover-split-2026-08-04.md` |

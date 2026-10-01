# PRECOMMIT — caiso-243: the F923 low-volume fallback defect — repair form (a)+(c), owner-chosen, pushed BEFORE any arm is coded and BEFORE any LP

**Session caiso-243, 2026-09-04. Branch `claude/caiso-f923-lowvolume-defect-dnegou`
(fresh off `main` `b168260e`).** Parent object: `FINDING-caiso242-offer-basis-identity-2026-09-03.md`
§5–§6 and §8 ask 3 — the three compounding defects (D1 empty `state`, D2 an
unguarded zone tier, D3 a fixed charge over a near-zero denominator) that deliver
one EIA-923 row (plant 55077, NV, **96.161 $/MMBtu on 2.6 % of its own normal
volume**) to **2,816.3 MW of CAISO gas for all 720 hours of November 2025**.

CAISO holds **no `complete` and no `final` marker**; the holdout spend freeze is
**ACTIVE**; every read below and the one solve stay inside **2023–2025**.

Keeper at open: **`2026-09-03-caiso-241-b1-ctpeaker`**
(`results/calibration/caiso241_b1_ctpeaker_committed`, `git_sha 607f9324`),
**NOT-YET**, one load-bearing FAIL — C3a **+3.9 / +12.3 / +15.5 %** (2023 PASSES;
model 56.29 / 38.92 / 39.74 vs RT 54.17 / 34.65 / 34.42 $/MWh; required move
**0.00 / −0.805 / −1.878 $/MWh** to the ±10 % band), C3c the single ledgered
caveat (2023, 2024; 2025 PASSES at 0 h vs 8 h), C1 12/12 free 8/8 (2025 C1 is
SKIPPED on the preliminary EIA-923 vintage — **2025 class energies are not
gated**), C2 / C3b / C4 / C8 PASS, C6 attested, `audit_keepers --iso CAISO`
PASS 0/0, DOF ledger 9 entries / 6 residual.

---

## §0 — WHAT THIS SESSION IS, AND THE DISCLOSURES THAT CONDITION IT

### §0.1 — This is a DATA-INTEGRITY repair, not a calibration lever, and its form was chosen by the owner

caiso-242 §8 ask 3 named three candidate shapes and deliberately selected none.
This session **measured each shape's footprint first (zero LP, §2), put the
measured choice to the owner, and the owner chose (a)+(c) — both armed — and
G-CTRL form 2** (§0.4). The repair is armed for **structural integrity**: the
fallback's own documented design (*"the plant's own state first … otherwise the
plant's model zone"*, `plant_prices.py`) is restored from the plant's real
EIA-860 state, and the donor-count guard the registry already carries
(`nearby_fuel_price_min_state_plants`, resolved **2** on this keeper) is
extended to the one tier that lacked it. **Zero new numbers, zero free
parameters** (rule 21 `[R-DOF]`).

### §0.2 — FULL DISCLOSURE: everything measured BEFORE this push

Following caiso-242 §0.2: the diagnostic phase came before this push, so every
number already measured is reproduced in §2 rather than registered as a
prediction; §4's predictions are confined to the **solve outcomes**, which are
unmeasured.

**Read:** the caiso-242 finding + precommit (§0.5 / §3.3 — §H‴ is NEVER quoted:
it was registered and never evaluated), caiso-241 §7–§10, caiso-240 §7,
caiso-239 §8, caiso-230 §9, the caiso.md tail, the `CAISO.js` cells
`measured_offer_surface` / `gas_hub_basis_overlay` / `gas_plant_monthly_pricing`,
`keepers/CAISO.json`; `data/fuel/plant_prices.py` (`apply_plant_monthly_fuel_prices`,
`_NearbyFuelPrices`), `data/fuel/resolve.py` (apply order: plant-monthly →
hub overlay → zonal basis → dual fuel), `data/fuel/hubs.py::apply_hub_basis_overlay`,
`data/eia923.py` (`state_month_price_grid`, the never-wired `plant_state_map`),
`data/fleet/assembly.py::bins_to_fleet`, `data/fleet/eia860.py`,
`data/fleet/__init__.py` (`Generator.state`, `FleetArrays.state`),
`scripts/run_calibration.py::run_year` (the fuel chain after `apply_monthly=False`),
`scripts/run_calibration_full.py::run_replay_bundle`, `scripts/replay_keeper.py`,
`scripts/gen_caiso241_attestation.py`, the keeper's `meta.json` /
`run_config.json` / `metrics.json` / `hourly/` sidecars, `gas_basis_by_iso_month.csv`,
`data/raw/eia-860/eia860_plant.parquet`, `_caiso242_f923_lowvolume_census.{py,json}`.

**Measured before this push (two probes, ZERO LP, NOTHING ARMED):**

| probe | artifact | what |
|---|---|---|
| `scripts/probes/_caiso243_fallback_footprint.py` | `_caiso243_fallback_footprint.json` | each candidate form as a monkeypatch on the F923 seam inside the real `run_year(fleet_only=True)` rebuild of the keeper recipe; cell-by-cell fuel-price diff; tier attribution; D1 root cause |
| `scripts/probes/_caiso243_price_envelope.py` | `_caiso243_price_envelope.json` | the two-sided price-leg envelope from the ASSEMBLED offers (`mc_base`) each variant hands the LP, against the keeper's own zonal price × demand |

**NO CODE ON THE SOLVE PATH HAS BEEN CHANGED. NO `ScenarioConfig` FIELD EXISTS
YET. NO LP HAS RUN.** The arm is implemented after this push; its G-STRUCT
check (§5.1) is that the implementation reproduces the probe's cached
`(a)+(c)` fuel-price array **byte for byte**.

### §0.3 — HARD STOPS

Training window only; all three years in **one invocation and one bundle**
(rule 16), **sequential** (rule 12), **never two CAISO solves concurrently**
(each 3-year LP holds ~6.5 GB; two OOM-killed this container at caiso-241). No
`calibration-complete.json`, no `holdout-freeze.json`, no other ISO's keeper
shard, matrix shard or bundle touched. **The GUARD is ISO-generic; the ARM is
CAISO's alone** (rule 25 `[R-ISO-SCOPE]`): both fields default OFF, so every
other ISO's keeper replays byte-identical, and the other lanes' exposure (§2.6)
is filed as asks, never armed here. No P2. No off-registry knob (rule 24). No
derive script re-run (rule 23). No threshold is chosen (rule 5): form (b) is
NOT armed, and §2.5 records why the owner declined it.

### §0.4 — G-CTRL: FORM 4 IS VOID BY ITS LETTER; FORM 2 BINDS AND IS THE OWNER'S CHOICE

caiso-242 §5.2's form 4 (code-path emptiness) is **void by its letter**: between
the keeper's `git_sha 607f9324` and HEAD (`b168260e`, 54 commits) exactly ONE
commit touches the solve path — `b9384baf` *"Apply ruff format to the seven
remaining source/test files (R-Z)"* — on `data/fleet/campd_bins.py` (−4/+2 lines)
and `data/offer_curves.py` (+15/−3). **Both files are AST-IDENTICAL to the
keeper's blobs** (`ast.dump` equality, measured), i.e. the change is
formatting only. That is reported, not used: the falsifier as written fires.

What binds instead is **caiso-240's form 2 — dispatch identity in a
measured-inert year** — because this arm has **two** of them: §2.3 measures the
`(a)+(c)` fuel-price footprint at **exactly 0 rows in 2023 and in 2024** (the
hub-basis overlay covers 12/12 months in both, so every gas cell the fallback
writes is overwritten). The owner's caiso-241 §B2 carve-out is explicit: *"an
arm with even one inert year takes the caiso-240 dispatch-identity leg and
spends nothing."* **Owner decision, this session: form 2 — no control solve.**
G-CTRL **PASS** iff the arm's 2023 and 2024 class energies reproduce the keeper's
to **0.001 TWh in every class** (caiso-240 §0.7(1)). **FALSIFIER:** any inert-year
class moving by more — then the arm cannot be attributed and the session spends
a control (form 3) before claiming anything. The three fallback forms the owner
did not choose (form 3, form 4′ = AST-identity) are recorded here so a future
session does not re-argue them.

### §0.5 — DO-NOT-REDO ACKNOWLEDGED (rule 28(a))

Re-read in full: caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8,
caiso-230 §9. Not re-opened, not re-proposed, not offered as a C3a instrument:
CT_PEAKER availability (CLOSED); the CT_PEAKER band-order inversion (measured,
explained, immaterial); caiso-242's P-1 (SPENT — no basis arm here, at any
scope); §H‴ (never quoted); the gas-basis identity and the fuel-invariant-margin
flatness (two separate objects, neither touched); caiso-229 / caiso-230
(refuted / sign-killed, untouched); `CT_PEAKER.committed` (CLOSED at 0.991);
the measured bid committed multipliers; any cross-ISO value transfer; EIA-930's
CISO NG cell; `_DEFAULT_HR_MULT_BY_GROUP`; the five gas `mr` literals;
`ST_GAS:econ`; the `ST_GAS_PEAKER_PLANTS` scope split; the W-1/W-2/W-3 sweep
(dated ≤ 2026-12-01).

### §0.6 — THE DIRECTION IS FAVOURABLE TO THE SOLE FAILING GATE — FOR THE THIRD SESSION RUNNING — AND THAT IS A DISCLOSURE, NEVER AN ARGUMENT

Restoring ~2.4 GW of cheap CC (and re-tiering 25.6 GW of CA gas onto a
6-reporter state mean) in September–November 2025 puts more, cheaper supply
into the stack in the training window's worst C3a year, so **C3a-2025 moves
DOWN** (required move −1.878 $/MWh). caiso-241 and caiso-242 both had to make
the same disclosure. **Three consecutive favourable-direction repairs in one
lane are stated as such**: it is a property of where the lane's remaining
defects sit (every one an over-priced or withheld domestic gas offer that lets
imports win), and per rule 1 `[R-STRUCT]` it is **not** an argument for this
repair. The promotion rule (§5.7) keys on **structure**, and C3a's verdict, in
either direction, is excluded from it.

**And the second half cuts the other way, stated before the solve:** the
September leg of the repair moves the two pool-of-one zones **UP**
(3.849 → 4.19 $/MMBtu, +2.5…+5.5 $/MWh on 2.45 GW), and the price-leg envelope
(§3) has a positive upper limb (+0.311 $/MWh) for that reason.

### §0.7 — TWO INHERITED INSTRUMENT DEFECTS, ADOPTED

1. **The price-leg envelope is a LOOSE two-sided bound and the volume leg gets
   NO falsifier** (caiso-242 §0.5(1), from caiso-241 §8.1: the price leg is
   conservative, the volume leg anti-conservative). §3's envelope is quoted as
   the falsifier; class-energy expectations (§4 P-4/P-5) are predictions, never
   bounds.
2. **The DOF ledger cannot see this repair either** (caiso-242 §0.5(2)): it
   adds no scalar and removes none. P-7 predicts it does not move, and no DOF
   progress is claimed from the counter. The provenance-instrument ask is
   re-filed unchanged (§6).

---

## §1 — THE RULING: WHY (a)+(c), IN THE OWNER'S WORDS AND IN MEASUREMENT

### §1.1 — D1's ROOT CAUSE, located in code (ISO-generic)

`data/fleet/assembly.py::bins_to_fleet` constructs every `Generator(...)` of the
CAMPD-bin / `plant_level_fleet` path **without a `state` argument**;
`Generator.state` defaults to `""` (`data/fleet/__init__.py`), and
`generators_to_fleet_arrays` copies that emptiness into `FleetArrays.state`.
Only the EIA-860 loader path (`data/fleet/eia860.py`) ever sets it. **So every
ISO whose keeper runs `plant_level_fleet=True` — CAISO, PJM, MISO, NYISO, NEISO
(all five, measured from their keepers' `run_config.json`) — has an empty state
tier**, and the `plant_level_fleet` field's own docstring (*"each generator
retains its EIA plant code, plant group and state"*) describes a property the
CAMPD-bin path never had. Measured on the keeper rebuild: **1,401 / 1,406 /
1,411 of 1,401 / 1,406 / 1,411 gas rows empty in 2023 / 2024 / 2025**.

### §1.2 — The tier attribution on the keeper's own path, 2025 live months (Sep–Nov)

Only **7 CAISO-fleet gas plants report in F923 at all** in 2023–2025 (422,
55077, 55985, 56476, 56532, 57027, 57978). The zone pools are therefore tiny
and two of them are **pools of ONE in every one of the 36 months**:

| tier the keeper actually uses | zone | MW (per month) | plants |
|---|---|--:|---|
| zone pool = 2 | LA_BASIN | 9,035 | 50 |
| zone pool = 3 | NP15 | 8,575 | 71 |
| default (the F923 ISO-month volume-weighted series) | ZP26 | 3,309 | 38 |
| **zone pool = 1 (55077, NV)** | **SP15_rest** | **2,446** | 8076, **55295, 55518, 55656**, 57977, 58122 |
| **zone pool = 1 (55985)** | **SDGE** | **2,203** | 23 |
| own | NP15 / SDGE / LA_BASIN / SP15_rest | 4,863 / 1,677 / 1,112 / **370 (55077 itself)** | 7 |

The SP15_rest pool of one is the caiso-242 defect (Nov 96.161 → 2,446 MW).
**SDGE is the same structure with a sane donor** (4.524 in Nov): a pool-of-one
guard cannot tell the two apart, which is exactly why (a) alone is a guard and
(c) is the repair.

### §1.3 — Why (a)+(c), and what each does on CAISO

* **(c) `fleet_state_from_eia860`** — stamp each CAMPD-bin generator's `state`
  from `data/raw/eia-860/eia860_plant.parquet` (`Plant Code → State`, 17,043
  plants; already a solve-path source via `zone_assignment.py` and
  `eia860.py::_eia860_plant_sector`). This makes the designed state-first tier
  reachable: every CA plant's gap-fill month is priced from the **6-reporter
  CA state pool** (55077 is NV and is excluded from it by construction).
  **It is the root-cause repair of D1.**
* **(a) `nearby_fuel_price_zone_donor_guard`** — the zone tier requires at
  least `nearby_fuel_price_min_state_plants` distinct reporters in the
  zone-month, exactly as the state tier already does; a pool of one returns
  NaN and the plant falls to the next series. **It is the repair of D2**, and
  on CAISO it is **measured INERT on top of (c)** (§2.3: `(a)+(c)` is
  byte-identical to `(c)`), because every CA recipient is served by the state
  tier before the zone tier is consulted. It is armed anyway, at the owner's
  choice, as the generic protective guard — a lane whose state pool is thin
  (NV-like: one reporter) would otherwise fall straight into an unguarded
  pool of one.

### §1.4 — Why this is OUTSIDE every closed cell

This changes no offer multiplier, no band grounding, no margin mechanism, no
basis series and no overlay. It changes **which measured F923 receipts a
non-reporting plant inherits** in the months the hub overlay does not cover —
a source-data admissibility question in the fuel layer, one level below every
offer-side object the lane has adjudicated. `gas_plant_monthly_pricing` (the
matrix row that carries the fallback) stays `K`; the two new fields are new
rows (§7).

---

## §2 — WHAT WAS MEASURED (all pre-push, all zero LP)

`_caiso243_fallback_footprint.json`. Every variant is the keeper recipe rebuilt
through `run_year(fleet_only=True)` with one patch on the F923 seam; the diff is
against the unpatched rebuild, cell by cell (generator × hour).

### §2.1 — Coverage: the defect is reachable in exactly three months of the window

`gas_basis_by_iso_month.csv` carries CAISO rows for **12/12 months in 2023 and
2024 and 9/12 in 2025 (Sep, Oct, Nov missing)**. The overlay overwrites every
gas cell in a covered month, so the fallback is live **only in 2025-09/10/11**.

### §2.2 — Footprints, 2025

| form | rows | MW | months | Nov cap-wt $/MMBtu, before → after | by group (MW) |
|---|--:|--:|---|---|---|
| **(a)** | 225 | **4,649.3** | 9, 10, 11 | 52.74 → 4.45 (SP15_rest 96.161 → 4.4487; SDGE 4.524 → 4.4487) | CC_REGULAR 3,040.7 · CT_PEAKER 1,547.2 · CC_CHP 49.1 · CT_CHP 12.3 |
| **(c)** | 1,322 | **25,568.3** | 9, 10, 11 | 13.47 → 4.38 (every CA plant → the CA state mean 4.3811) | CC_REGULAR 12,647.7 · CT_PEAKER 7,254.9 · ST_GAS 2,946.8 · CC_CHP 1,695.0 · CT_CHP 1,023.9 |
| **(a)+(c)** | 1,322 | 25,568.3 | 9, 10, 11 | **BYTE-IDENTICAL to (c)** (`max|Δ| = 0.0`) | — |
| (b) at qty ≤ 0.02 × median & price ≥ 2× | **0** | 0 | — | **the tightest swept cut MISSES the motivating row** (55077-Nov quantity is 2.62 % of its 2025 median; Dec is 3.91 %) | — |
| (b) at ≥ 0.05 / 3.0 (and 0.10, 0.20) | 239 | 6,125.2 | 11 | 55077's own 370 MW 96.161 → 4.38, **plus** a −0.068 $/MMBtu shift on the 3.3 GW ZP26 default tier (the ISO-month series loses the row) | — |

The **Sep leg moves UP** under (a) and (c): SP15_rest 3.849 → 4.17 / 4.19
(+2.5…+5.5 $/MWh on 2.45 GW). The **Oct leg** removes 55077's own (normal-volume)
11.304 from its 2.45 GW of neighbours (−52…−115 $/MWh). **Non-gas rows moved: 0
in every form.**

### §2.3 — Inertness: 2023 and 2024

`(a)+(c)` rebuilt for 2023 and 2024: **0 rows, 0 cells moved** in each. These
are the form-2 G-CTRL years (§0.4).

### §2.4 — The residual NO form except (b) touches, stated before the solve

**Plant 55077 (Desert Star, NV, 370.1 MW CC_REGULAR) keeps its OWN reported
96.161 $/MMBtu for November 2025 under (a)+(c)** — mc ≈ $736/MWh for 720 hours.
Tier 1 (*"the plant's own measured months win outright"*) is not a fallback and
is untouched by either guard. This is D3, and it remains **open**, sized: 370 MW
× 720 h = 0.27 TWh of capability, 13 % of the caiso-242 headline.

### §2.5 — Why (b) is NOT armed (owner decision, this session)

Every candidate cut is a NEW parameter pair with no measured identification
(rule 5) — the census sweep is a sensitivity table, not a derivation — and the
tightest cut does not even catch the row that motivated it. The owner declined
it; it stays an ask (§6), with the measured facts above attached so it is not
re-derived.

### §2.6 — Cross-ISO exposure (asks for those lanes, never arms — rule 25)

By each ISO's own plant set (`build_zone_lookup`), gas plant-months 2023–2025,
rows at qty ≤ 2 % of the plant-year median AND price ≥ 2× its VW mean:

| ISO | rows | plants | anomalous rows | plants | max $/MMBtu | rows > $20 | keeper: nearby fallback / gas monthly / hub overlay |
|---|--:|--:|--:|--:|--:|--:|---|
| CAISO | 245 | 7 | 1 | 1 | 96.16 | 7 | on / on / on (9/12 in 2025) |
| PJM | 894 | 29 | 4 | 3 | 191.64 | 14 | on / on / **off** |
| MISO | 3,832 | 116 | 12 | 9 | 198.46 | 79 | on / on / **off** (class-aware pools) |
| NYISO | 179 | 5 | 0 | 0 | 11.86 | 0 | on / on / on |
| NEISO | 45 | 2 | 0 | 0 | 19.62 | 0 | on / on / on |
| ERCOT | 813 | 27 | 1 | 1 | 56.36 | 15 | off / off / off |

PJM and MISO have **no hub overlay**, so their fallback layer is live in all 36
months and their state tier is equally empty (§1.1). Whether a pool-of-one zone
serves an anomalous row there is **not measured here** — it is those lanes'
first probe, and both fields ship default-off for them to arm.

---

## §3 — THE ESTIMATOR: the price-leg envelope on the ASSEMBLED offers

`_caiso243_price_envelope.json`. For each variant, using the `mc_base` array the
LP is handed (fuel + VOM + carbon + NOx + margin reform), against the keeper's
zonal P1 price and demand:

* **LOWER limb:** in every live-month zone-hour where the keeper's price
  exceeds the cheapest repriced tranche's NEW offer, the price falls to that
  offer. Ignores residual demand, imports and the other ~11 GW of CC — a large
  overstatement of the fall.
* **UPPER limb:** in every live-month zone-hour the price rises by the largest
  positive offer move among the repriced tranches (the September leg).

| year | form | ΔC3a envelope ($/MWh, annual load-weighted) |
|---|---|---|
| 2023 | (a)+(c) | **[0, 0]** — falsifier is byte-identity (§0.4) |
| 2024 | (a)+(c) | **[0, 0]** — same |
| 2025 | (a) | [−0.377, +0.038] |
| 2025 | **(a)+(c)** | **[−2.634, +0.311]** |
| 2025 | (b) ≥ 0.05 (not armed) | [−0.073, 0] |

Per zone in the live months the keeper's price already sits above the
repriced tranches' OLD cheapest offer in 1,693–1,942 of ~2,184 hours for
NP15 / LA_BASIN / SDGE / ZP26 (they were in merit at the old price too) and in
**588** hours for SP15_rest (old cheapest 243.81 mean — out of merit); after the
repair SP15_rest is in merit in 1,683 hours. The lower limb is therefore
dominated by re-tiering that changes offers by < $1/MWh on units already
marginal, not by the 2.45 GW coming back — which is why §4 P-2 predicts the
measured move lands far inside it.

---

## §4 — PREDICTIONS, REGISTERED AGAINST QUANTITIES NOT YET MEASURED

Written to be **uncomfortable**: P-2, P-4, P-5 and P-6 constrain the session's
own claim; P-7 predicts its instrument stays blind.

| # | prediction | falsified by |
|---|---|---|
| **P-1** | 2023 and 2024 class energies reproduce the keeper's to **0.001 TWh in every class** (G-CTRL form 2 binds) | any inert-year class moving more ⇒ form 2 fails, a control is spent |
| **P-2** | **the repair does NOT close C3a-2025 and delivers at most a third of its requirement**: ΔC3a-2025 ∈ **[−0.60, 0.00] $/MWh** against a required −1.878, and C3a's verdict is unchanged in every year (2023 PASS, 2024 FAIL, 2025 FAIL) | ΔC3a-2025 < −0.60, or > 0.00, or any verdict flip |
| **P-3** | ΔC3a-2023 = ΔC3a-2024 = **0.000** exactly | any non-zero move |
| **P-4** | **CC_REGULAR's 2025 energy rises by less than 0.5 TWh** (the caiso-242 against-interest reading — cost misallocated within the class, no class-level hole — holds); the November-2025 monthly mean rises by < 500 MW from 5,348 | ≥ 0.5 TWh, or ≥ 500 MW in November |
| **P-5** | **the repair WORSENS the CT_PEAKER volume miss**, marginally: CT_PEAKER-2025 energy falls (from 0.378 TWh) because cheaper CC re-enters the Sep–Nov stack; and imports-2025 fall by less than CC_REGULAR rises | CT_PEAKER-2025 rising, or imports falling by more than CC_REGULAR rises |
| **P-6** | C1 stays 12/12 free 8/8, C3b / C8 / C6 verdicts unchanged, C3c-2025 stays PASS at 0 h > $200 (the keeper has 0 such hours in every month), caveat budget 1 ledgered / 0 protective | any verdict change |
| **P-7** | the DOF ledger does **not** move (9 / 6) | any change in its counts |
| **P-8** | G-STRUCT exact (§5.1): the implementation's 2025 fuel-price array is byte-identical to the probe's cached `(a)+(c)` array (1,322 rows, 25,568.3 MW, Sep–Nov), the `(a)`-only path reproduces the cached `(a)` array (225 rows), and every non-gas row, every other ISO's fleet and both flags-off are byte-identical to today | any cell differing |

---

## §5 — GATES, EACH WITH A FALSIFIER

### §5.1 — G-STRUCT (pre-solve, zero LP)
**PASS** iff P-8 holds: the coded mechanism reproduces the measured footprint
byte for byte, in every year, and flags-off is byte-identical to HEAD.
**FALSIFIER:** any cell differing ⇒ the code, not the probe, is wrong; fixed
before any LP, and the fix is disclosed.

### §5.2 — G-CTRL (form 2, owner's choice — §0.4)
**PASS** iff P-1. **FALSIFIER:** an inert-year class moving > 0.001 TWh ⇒ a
control solve is spent (form 3) and the fallback is reported as such.

### §5.3 — G-INERT
**PASS** iff 2025 is not byte-identical to the keeper (it cannot be — 1,322
rows move) — and, stated for the record, iff 2023 and 2024 ARE (that is the
form-2 leg, not a separate inertness claim).

### §5.4 — G-C1
**PASS** iff C1 stays ≥ 12/12 and ≥ 8/8 free and no class in band leaves it.
*(2025 C1 is SKIPPED on the preliminary vintage, so this gate is 2023/2024, i.e.
the inert years — it can only fail through G-CTRL.)*

### §5.5 — G-C3b, G-C8, G-CAVEAT, G-C6
**PASS** iff C3b's verdict is unchanged; C8 stays PASS with no new D-2/D-4
mechanism (the arm adds no floor); the caveat budget stays ≤ 1 ledgered / 0
protective; C6 is attested on the registered bundle.

### §5.6 — G-C3a — envelope leg only
**PASS** iff ΔC3a-2025 ∈ **[−2.634, +0.311]** and ΔC3a-2023 = ΔC3a-2024 = 0.
**FALSIFIER:** outside ⇒ an estimator or mechanism defect, reported, **never
re-fitted**. **The verdict leg is deliberately NOT a promotion condition**
(§0.6): P-2 predicts no verdict changes; if one does, it is reported at full
size and excluded from §5.7.

### §5.7 — THE PROMOTION RULE, FIXED NOW
Promote **iff** G-STRUCT, G-CTRL, G-INERT, G-C1, G-C3b, G-C8, G-CAVEAT, G-C6 and
the envelope leg of G-C3a all pass. **The basis is structural**: a documented
tier order is restored from the plant's own EIA-860 state, and a guard already
in the registry is extended to the tier that lacked it, at zero free
parameters, removing a 96.161 $/MMBtu fixed charge from 2.45 GW of CAISO gas
for a month. C3a's verdict, in either direction, is reported and excluded.
**If every gate passes and C3a does not move at all, the arm is still promoted**
— a data-integrity repair is a keeper because it is right, not because it
helps.

---

## §6 — OWNER ASKS CARRIED (none presumed)

1. **(b) — the D3 residual** (§2.4/§2.5): 55077's own November row stays. Any
   volume-admissibility guard needs an identified threshold; the measured fact
   that the 2 % cut misses the row is attached so it is not re-derived.
2. **The 2025 overlay coverage gap** (caiso-242 §8 ask 4): with 12/12 rows the
   fallback would be unreachable in 2025 as in 2023–2024. Unchanged.
3. **Other lanes** (§2.6): PJM and MISO carry the same empty state tier with no
   overlay and measurable anomalous rows; the fields ship default-off for them.
4. **The DOF-provenance instrument** (caiso-241 §8.2): re-filed, unmoved —
   this is the sixth consecutive repair the counter cannot see.
5. The rest of caiso-242 §10, untouched: the narrow-scope basis arm, the
   fuel-invariant-margin flatness, the residual CT_PEAKER root cause,
   caiso-238 objects 3/4, the SoCalGas OFO arm, `IMPORT_TRANCHES[CAISO]`.

---

## §7 — WHAT THE ARM WILL BE (designed AFTER this push; recorded here so the design cannot drift)

* `ScenarioConfig.fleet_state_from_eia860: bool = False` — in
  `bins_to_fleet`, stamp `Generator.state` from the EIA-860 plant table by
  plant code (a cached `eia860_plant_states()` next to `_eia860_plant_sector`).
* `ScenarioConfig.nearby_fuel_price_zone_donor_guard: bool = False` — in
  `_NearbyFuelPrices`, a zone reporter-count grid; the zone tier fills only
  months with ≥ `nearby_fuel_price_min_state_plants` distinct reporters.
* Both: registered in `_CACHE_KEY_OPTIONAL_FIELDS` + defaults (nyiso-119
  discipline), threaded through `run_year` → `build_calibration_config`,
  `solve_and_persist` → `meta.json`, and `--replay-bundle` overrides
  (`--fleet-state-from-eia860`, `--nearby-fuel-price-zone-donor-guard`).
* Two new mechanism rows (`fleet_state_from_eia860`,
  `nearby_fuel_price_zone_donor_guard`) in `mechanism-matrix.js` with a cell
  line in every ISO shard (rule 28(c)); unit tests under `tests/unit/data/`.
* The solve: `--replay-bundle results/calibration/caiso241_b1_ctpeaker_committed
  --year 2023 2024 2025` with both flags, ONE bundle
  `caiso243_b1_f923_fallback_guard`; post-solve chain per the handoff; C6
  attested; registered in this session as keeper or rejected probe (rule 15).

# RESULT — SPP-75: the gas half of the low side (who runs gas when SPP RT < 0, and why)

**Zero LP. No shard, no solve, no bundle, no `ScenarioConfig` field, keeper untouched.**
Pre-registration: `docs/handoffs/PRECOMMIT-spp-75-gas-low-side-2026-09-23.md`, pushed at `ecfbda5a`
before any attribution number was read. Base `efb7ec3d`. Probes: `scripts/probes/_spp75_gas_low_side.py`
(part A), `_spp75_fleet_membership.py` (part B, `fleet_only` rebuild, one interpreter per year),
`_spp75_chp_floor_delta.py` (part C). Outputs: `results/calibration/_spp75_gas_low_side.json`,
`_spp75_chp_floor_delta.json`.

---

## 0. Headline

- **The hypothesis is mostly wrong.** Most of the gas running in RT<0 hours is **not** CHP or
  industrial must-run. **77–83 % of the gap is utility and IPP combined cycles** (plus some
  ST_GAS). They are online in about half of those hours at about 40 % of their ordinary-hour
  output, so they are price-responsive and not flat. That is commitment behaviour, the object
  SPP-44 and SPP-66 were rejected on. No measured, forward-reproducible driver for it exists on
  disk.
- **CHP is real but small.** SPP's two metered steam hosts, Eastman Cogeneration (CC_CHP) and
  Black Hawk Station (CT_CHP), run flat (RT<0 output ÷ ordinary-hour output 0.84–0.88). The model
  floors them at 34–47 % of capacity against a measured 92–93 %. This accounts for **11–17 % of
  the gap**.
- **An admissible lever for the CHP piece already exists and is off for SPP: `chp_steam_floor_p25`.**
  It is a level-source swap on the existing `MECH_CHP_STEAM` floor, reads committed artifact
  columns, and needs no new field and no new DOF. Sized at zero LP it lifts SPP's CHP floor
  **165 → 410 MW** in every hour (+245 MW). That is **14 % of the 2020 gap and 10 % of 2022's**,
  below the pre-registered 50 % bar. **No shard was launched.** This is put to the owner (§6).
- **Missing or mis-zoned units explain nothing** (0–1 %).

## 1. The gap, reproduced (P1)

Mean over measured RT ≤ 0 hours; EIA-930 SWPP NG vs rung P1 gas classes (CC_*, CT_*, ST_*), MW.

| year | RT≤0 hours | EIA-930 NG | model gas | **gap G** | CAMPD gas (gross) | κ = CAMPD ÷ 930 |
|---|---:|---:|---:|---:|---:|---:|
| 2019 | 547 | 4,466 | 4,141 | 325 | 4,469 | 1.00 |
| **2020** | **936** | 4,083 | 2,326 | **1,757** | 4,077 | **1.00** |
| 2021 | 1,108 | 2,825 | 637 | 2,188 | 2,783 | 0.98 |
| **2022** | **995** | 3,014 | 561 | **2,453** | 2,988 | **0.99** |

κ ≈ 1 means CAMPD's SWPP-BA gas units cover the EIA-930 series. Gross-vs-net and the missing
<25 MW units roughly cancel, so the unit-level attribution below needs no rescaling.

## 2. Attribution (PRECOMMIT §2): measured MW in RT≤0 hours minus the model's matching classes

| object | 2020 measured | 2020 model | **2020 share of G** | 2022 measured | 2022 model | **2022 share of G** | flat ratio (RT≤0 ÷ MID2), 2020 / 2022 |
|---|---:|---:|---:|---:|---:|---:|---|
| (i) CHP / industrial vs CC_CHP+CT_CHP+ST_CHP | 453 | 158 | **17 %** | 424 | 148 | **11 %** | **0.84 / 0.87 (flat)** |
| (ii) utility/IPP non-CHP CC + ST_GAS vs CC_REGULAR+ST_GAS | 3,229 | 1,767 | **83 %** | 2,176 | 277 | **77 %** | 0.44 / 0.41 (responsive) |
|   of which CC | 2,567 | 1,487 | | 1,753 | 143 | | |
|   of which ST_GAS | 662 | 281 | | 423 | 133 | | |
| CT (non-CHP) vs CT_PEAKER | 395 | 400 | 0 % | 387 | 137 | 10 % | 0.39 / 0.43 |
| (iii) CAMPD units whose plant is absent from the rebuilt fleet | 7 | — | **0 %** | 14 | — | **1 %** | — |

Shares sum to ≈ 100 %: each share is (measured − model) ÷ G, and κ ≈ 1.
(iii) also finds **0 MW** under a non-gas model class.

**What (ii) is.** The CCs are ordinary utility and IPP units: GREC, Riverton, Hobbs, Arsenal Hill,
State Line, Harrison County, Oneta, Green Country, Redbud, Mustang. They are online in 42–53 % of
RT≤0 hours (MW-weighted), and in those hours produce 41–44 % of their MID2 output. No large
(ii) unit meets the flat test (online ≥ 90 % of RT≤0 hours and ratio ≥ 0.8). The only 2020 flat
non-CHP units total 41 MW of CT.

**Year pattern.** Across 2019–2022 the model's CC+ST output in RT≤0 hours is
**3,548 / 1,767 / 426 / 277 MW**. Measured is **3,507 / 3,229 / 2,070 / 2,176 MW**.

- At $2.57 gas (2019) the model keeps its CCs on, and the gap is only 325 MW.
- As gas rises ($2.03 → $3.72 → $6.45), the model decommits them in the low hours. The real fleet
  does much less of that.

That pattern is the model's commitment responding more strongly to fuel price than the real
fleet's does. It is not a missing physical must-run.

## 3. The CHP piece, sized (part C)

`assembly.py` sets the grid floor to `pmin_cf × (1 − btm) × nameplate`. `chp_steam_floor_p25` swaps
`pmin_cf` for the artifact's `steam_level_cf` wherever that is higher. The fleet dump carries
post-BTM `pmax`. Check: the control floor, 165 MW, reproduces the rung's CHP output in RT≤0 hours
(158 / 148 MW; the difference is the availability clip).

| plant (class) | post-BTM pmax | `chp_pmin_cf` → `steam_level_cf` | floor MW, control → arm | CAMPD gross in RT≤0 hours, 2020 / 2022 |
|---|---:|---|---|---|
| Eastman Cogeneration (CC_CHP) | 271.2 | 33.7 % → 91.8 % | 91.4 → **248.9** | 250 / 217 |
| Black Hawk Station (CT_CHP) | 143.1 | 47.1 % → 93.3 % | 67.4 → **133.5** | 203 / 207 |
| 12 small EIA-923 cogens (ST/CT_CHP) | ~180 | mixed | 7 → 28 | — |
| **total** | **~597** | | **165 → 410 (+245)** | **453 / 424** |

The arm reaches **245 ÷ 1,757 = 14 %** (2020) and **245 ÷ 2,453 = 10 %** (2022) of G. It stops
at 90–97 % of the measured CHP group's RT≤0 output, so it does not overshoot.

The EIA-923 independent bound agrees. The SWPP gas CHP=Y fleet averages **551 / 538 MW**
(2020 / 2022) against the model's CHP classes at **261 / 192 MW**: a flat-CHP reach of 290 / 346 MW.

## 4. Predictions, scored

| # | prediction | outcome |
|---|---|---|
| P1 | G reproduces 1.75 / 2.45 GW | **HIT** (1,757 / 2,453 MW) |
| P2 | κ in [0.8, 1.1] | **HIT** (1.00 / 0.99) |
| P3 | (i) < 50 %; EIA-923 flat bound < 0.6 GW | **HIT** (17 % / 11 %; 290 / 346 MW) |
| P4 | (ii) ≥ 50 %, mostly at or near min load | **half.** Share HIT (83 % / 77 %). Min-load MISS: 1,162 ÷ 3,229 = 36 % and 830 ÷ 2,176 = 38 % of (ii)'s RT≤0 MW is at ≤ 1.2 × min load. The instrument is crude (the plant's EIA-860 NG min load is split evenly across its CAMPD units). The flat-ratio reading (0.41–0.44 of MID2) points the same way: part-loaded, not pinned at min load. |
| P5 | (iii) < 15 % | **HIT** (0 % / 1 %) |
| P6 | CHP flat ≥ 0.8; non-CHP CC/ST < 0.8 | **HIT** (0.84 / 0.87; 0.44 / 0.41) |
| P7 | no admissible lever; route to commitment | **HIT** for the ≥ 50 % object. A smaller admissible sub-object (CHP, §3) was found and is put to the owner, not built. |

## 5. Verdict (PRECOMMIT §3)

| object | share of G (2020 / 2022) | measured, forward-reproducible driver? | admissible |
|---|---|---|---|
| (i) CHP / industrial | 17 % / 11 % | **yes.** Host steam demand, via the committed multi-year `steam_level_cf` (loading-when-on, CAMPD). Rule-13 forward-valid; already registered as `chp_steam_floor_p25`. | **yes, but below the 50 % bar** |
| (ii) utility/IPP CC + ST_GAS | 83 % / 77 % | **no.** Part-loaded, price-responsive units. The only measurement naming them is their observed online state, which SPP-46 already adjudicated as an outcome (rule 13 fail). | **no.** Commitment family, R cells stand. |
| (iii) membership / zoning | 0 % / 1 % | — | nothing to fix |

**New evidence against the R cells, and why it does not re-open them.** SPP-44/66 had no
unit-level attribution in RT<0 hours; this lane does. It confirms the gas half is the committed CC
fleet: the same plants and conduct the bridge targeted. It adds one fact: **the model's low-hour CC
commitment is far more gas-price-elastic than the real fleet's** (§2 year pattern). It does not
supply what the R cells need, which is a measured driver for *why* real CCs stay on at negative
prices. Candidates (self-commitment for multi-day economics, gas-nomination and ratable-take
constraints, bilateral obligations) each have no SPP-published, forward-reproducible input on
disk. **Routed, not built.**

## 6. Rung rows, each tagged with its owning object

| row | value | owning object |
|---|---|---|
| C3a 2020 | +15.5 % | Low-side thermal: the coal half is `coal_sync_ensemble_level` (K, armed); the gas half is **(ii) commitment, 77–83 %, no admissible driver**, with CHP at 11–17 % (admissible, §3). Plus the ordinary-hour stack level (SPP-74 §3b, no driver). |
| C3b 2020 | 0.257 | same as C3a 2020 |
| C3b 2021 | 0.234 | Uri February (ledgered wedge; 0.071 without it) |
| C3b 2022 | 0.208 | Upper-tercile offer shape (xiso-refused) |
| C1 COAL_PRB 2022 | +9.60 TWh (band ±8.00) | SPP-69 §4 coal/gas crossover. This lane adds that 2022 gas under-runs by 2.45 GW × 995 h ≈ **2.4 TWh in RT≤0 hours alone**, which is (ii). |
| C2 gas 2022 | NRMSE 0.321 (band 0.30) | same crossover; (ii) is part of its low-hour shape |

**Expected effect of the CHP arm, if the owner charters it (not solved).**
- +245 MW of flat gas in every hour, about +2.1 TWh/yr.
- In RT≤0 hours wind is the marginal unit, so most of it displaces wind. The effect on price
  there is expected to be small.
- C3a 2020 will not pass on this alone. The piece is ≤ 14 % of the gas half, and the gas half is
  one of three contributors.
- C2 gas 2022 moves the right way in direction; its size is unknown without a solve.
- C1 COAL_PRB 2022 could move either way.

## 7. Rules and state

- Rules 1/13/14: nothing built. EIA-930, CAMPD and RT LMP are diagnostics only. The CHP level
  source is committed, multi-year and forward-valid.
- Rule 19: the only candidate is a level swap on the one existing CHP floor (`MECH_CHP_STEAM`),
  not a second floor.
- Rule 21: zero new parameters. `steam_level_cf` is a committed measured column. No bundle exists,
  so `build_dof_ledger --check` had nothing to check.
- Rule 25: no field added, and SPP's own artifact only.
- Rule 17: window = all hours; measured flat (RT≤0 online share 0.88–0.98 at both hosts).
- Rule 28: SPP cells updated. `chp_steam_following` U → **O** (open: measured and admissible, not
  solved). Evidence notes appended to `spp_gas_commitment_bridge` (R stands). DO-NOT-REDO block
  added to `docs/mechanism-testing-matrix.md` §5.7.
- **Keeper untouched.** `audit_keepers --iso SPP`: PASS, 0 failures, 0 warnings. `check_mechanism_matrix --base origin/main` and `check_cache_key_registration` both OK.
- Every number is model-SELECTION evidence.

## 8. Cost and retrievability

0 LP minutes. No shards, no bundles, nothing to archive or retain. Everything reproduces from
`main` with the three probes. **If chartered:** the CHP arm is seven shards (rule 36, 2019–2025),
each solving control and arm, with the existing flag `chp_steam_floor_p25=true` as the single delta.

---

## 9. THE CHP ARM — SOLVED (owner charter 2026-09-24, "Yes charter the CHP fix")

Seven shards, one per year, pinned to `79dcc45a`, each solving its own control and arm (PRECOMMIT §5).
All seven self-checks PASS: control = keeper recipe, arm = control + `chp_steam_floor_p25` only.
**Every control reproduces its keeper exactly** (max |Δ class TWh| 0.0000). Leg commits (provenance only,
rule 33(d)): 2019 `29a206aa…`, 2020 `a97be806…`, 2021 `98db111d…`, 2022 `381a9fe8…`, 2023 `89bc112c…`,
2024 `83095fbe…`, 2025 `ee05728f…` (full SHAs in `.gitignore` comment). Shards archived.

### 9.1 Arm − control

| year | CHP TWh | CHP MW in RT≤0 h | wind MW in RT≤0 h | CC_REGULAR TWh | COAL_PRB TWh | mean price $/MWh | model hours ≤ $0 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2019 | +0.83 | +144 | −6 | −0.26 | −0.37 | −0.05 | +3 |
| 2020 | +0.99 | +177 | −51 | −0.32 | −0.31 | −0.23 | +44 |
| 2021 | +1.32 | +170 | −74 | −0.52 | −0.37 | −0.44 | +27 |
| 2022 | +1.33 | +193 | −78 | −0.55 | −0.40 | −0.44 | +39 |
| 2023 | +0.25 | +95 | −51 | −0.06 | −0.09 | −0.14 | +30 |
| 2024 | +0.22 | +81 | −47 | −0.06 | −0.03 | −0.12 | +21 |
| 2025 | +0.28 | +112 | −55 | −0.03 | −0.14 | −0.14 | +28 |

The added CHP mostly displaces **CC_REGULAR and coal, not wind**. In most RT≤0 hours the model's
price is still positive, so thermal is marginal there, not wind. 2023–2025 move less because the
control's CHP already ran near the new floor on economics (control ≈ 386–405 MW mean).

### 9.2 Scored rows (control → arm)

| row | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| C3a (scorer basis) | +1.64 → +1.59 $ | **+15.5 → +14.2 %, FAIL** | +0.71 → +0.27 $ | −2.15 → −2.60 $ | −0.25 → −0.39 $ | −0.63 → −0.74 $ | unchanged status |
| C3b (SPP-74 instrument) | 0.125 → 0.123 | **0.256 → 0.242, FAIL** | **0.238 → 0.252, FAIL** | **0.209 → 0.211, FAIL** | ↓ 0.003 | ↓ 0.000 | ↓ 0.002 |
| C1 COAL_PRB 2022 | | | | **+9.60 → +9.20 TWh, FAIL** (band ±8.00) | | | |
| C1 CC_REGULAR 2022 | | | | **−7.55 → −8.09 TWh: PASS → FAIL** | | | |
| C4 gas NRMSE | 0.141 → 0.143 | 0.213 → 0.213 | 0.289 → 0.278 | **0.321 → 0.311, FAIL** | 0.183 → 0.180 | 0.215 → 0.213 | 0.245 → 0.241 |

G-4 (`screen_collateral_gate.py`, arm and control both scored against the registered keeper/rung):
**0 status flips in 2019–2021 and 2023–2025**. **One flip, 2022 C1 CC_REGULAR PASS → FAIL.** It is a
rung year, so under rule 30(c) it cannot decertify SPP. Its cause is §9.1's displacement: the
floor pushes CC_REGULAR further below an actual it already under-ran. G-4 also shows ST_GAS 2022
forced share PASS → FAIL **on the control too**. That is instrument drift: the registered rung
passes that row as "grounded above budget", which the screen instrument cannot evaluate. It is
not an arm effect.

The C3b rows for 2023–2025 are direction only. For those years the scorer's actual is load-weighted
on a basis my instrument does not reproduce (the scorer puts keeper C3b at 0.166 / 0.158 / 0.152).

### 9.3 Predictions (PRECOMMIT §5), scored

| # | prediction | outcome |
|---|---|---|
| Q1 | CHP +1.0–2.2 TWh | **2 / 7** (2021, 2022). 2019–2020 slightly low; 2023–2025 low because control CHP already ran near the floor |
| Q2 | CHP in RT≤0 h +180–250 MW | **1 / 7** (2022); 81–177 elsewhere |
| Q3 | wind falls by 60–100 % of Q2 | **0 / 7, wrong mechanism** (4–58 %). Thermal, not wind, is marginal in most of those hours |
| Q4 | price falls by < $0.30 | **5 / 7**; falls in all seven; 2021/2022 fall $0.44 |
| Q5 | C3a 2020 down < 1 pp, stays FAIL | **half**: stays FAIL; moved 1.37 pp |
| Q6 | no status flips 2023–2025 | **HIT**. Unpredicted: the 2022 CC_REGULAR flip |
| Q7 | control reproduces keeper < 0.05 TWh | **HIT** (0.0000, all seven) |

### 9.4 Structural gate

- **K-1 over-forcing (pre-registered): PASS in every gated year.**
  - Arm CHP in RT≤0 hours: 354 / 335 / 302 / 341 MW, vs measured 437 / 453 / 431 / 424.
  - Annual mean arm CHP: 385 / 375 / 331 / 344 / 414 / 427 MW, vs EIA-923 522 / 551 / 520 / 538 / 595 / 615.
  - 2025 (402 vs a partial 532) is reported, not gated.
- **D-4 unit conduct (not pre-registered; found in the regenerated diagnostics): FAIL at one plant,
  every year.**
  - The plant is **Lake Road (MO), 2098, ST_CHP**. Its artifact `steam_level_cf` is 4.9 % against
    `chp_pmin_cf` 0.0, so the swap creates a 4.6 MW floor where none existed. Its own CAMPD meter
    is at zero **78–97 %** of hours.
  - This is exactly the caiso-293 rule-17 defect: `on_freq × p50(loading)` (0.246 × 19.9 %) held
    as a 24/7 trickle.
  - Energy is tiny (0.02–0.04 TWh/yr), but rule 17 treats a floor binding while its driver says the
    plant is offline as a bug by definition, whatever its size.
  - Eastman (55176) and Black Hawk (55064), the two plants the arm was built for, **pass**.
  - The existing repair, `chp_steam_duty_window`, would hold 18.5 MW only in Lake Road's top-25 %
    load hours. It likely still fails there, because the plant's meter reads zero in more hours
    than that window leaves out. Not solved.
- D-2/C8: the CHP classes are exempt by construction (`d2_exempt_classes`). No other D-row changes
  verdict.

### 9.5 Recommendation (the owner decides; rule 31)

**Do not promote as solved.** It does what it was built for:
- The two metered steam hosts reach 90–97 % of their measured output.
- No gated over-forcing.
- Every price row moves the right way in 2020.
- C4 gas 2022 improves.

But it introduces a new rule-17 failure at Lake Road, and a new C1 flip (2022 CC_REGULAR, rung
only). The clean form is the same swap **scoped away from cyclers**. Nothing on `main` offers that
without either the duty window (probably insufficient at Lake Road) or a new eligibility
condition (a new field, zero-DOF if keyed on the artifact's own `status == ok` and
`on_frac ≥ 0.9`). Both are successor work.

Rule 1 permits promotion anyway on structure, since the two target hosts are the object and
Lake Road's floor is 4.6 MW. If the owner chooses that, the Lake Road D-4 FAIL must be carried as
a named defect.

### 9.6 Retrievability (rule 34(e))

- **Composed bundles:** `results/calibration/spp75_chp_rung` (2019–2022) and `spp75_chp_span`
  (2023–2025) exist **on this session's local disk only**. So do all 14 per-year legs, gitignored,
  not deleted (rule 31).
- **Shard branches:** transport, and will be cut when this lane's PR merges (rule 33(f)).
- **Promotion cost:**
  - While this session is alive: zero LP (register, promote, audit, prune).
  - After it ends: seven shards of ~10–25 min each, run in parallel.

### 9.7 Owner ruling (2026-09-24): "Don't promote"

**Not promoted.** It is also not a keeper candidate under the owner's standing test ("structural
integrity improves but gates regress may still be a keeper"): the structural leg itself regresses,
since the arm adds a new rule-17 D-4 FAIL at Lake Road (2098) in all seven years. The keeper stays
`2026-09-22-hydro-5-spp-floor`. Nothing was registered, so nothing needs pruning. The local bundles
may now be removed under rule 31 trigger (i); they are gitignored and die with the container.
Cell `chp_steam_following` moves O → **R** (owner-declined). Re-open only in the scoped form: the
level swap limited to non-cycling hosts.

# RESULT — CAISO: the 2019-2022 retiree window + the measured monthly gas LEVEL

**Session:** `caiso-fuelvintage-1` · **2026-09-09** · branch `claude/caiso-fuelvintage-1`
· **SCOPE: CAISO ONLY** (rule 25 `[R-ISO-SCOPE]`).
**Pre-registration:** `docs/PRECOMMIT-caiso-fuelvintage-2026-09-09.md`, pushed before the first LP.
**Predecessor's zero-LP pass, merged and carried forward:** `docs/FINDING-caiso-fuelvintage-1-2026-09-09.md`.
**Owner ruling carried (handoff §A7):** *"these should be promoted as keepers on both 860 and gas
shape counts regardless of inertness."*

---

## 1. Headline

| | |
|---|---|
| **Card B — the measured monthly gas LEVEL** | **PROVABLY INERT for CAISO**, established at **zero LP cost** and then confirmed in dispatch. Not "near-inert" as pre-registered — **exactly** inert. |
| **Card A — the 2019-2022 retiree window** | **NOT inert in 2023**, and CAISO **independently corroborates the PJM lane's redistribution defect** at ~14× PJM's relative size. Charter task 3 **fails in 2023 by design of the defect**, holds in 2024/2025. |
| **G-CTRL form 4** | **FALSIFIED for CAISO** — and the repo's own solve-surface fingerprint names the two constants that did it, at zero LP cost. |
| **The 2020/2021 touchpoints** | **UNREACHABLE at HEAD** — blocked on missing *data*, not on a marker. |
| **What was promoted** | Both changes are carried by the registered runs; the **keeper promotion is put to the owner** (§7), because rule 22 D-5(b) forbids writing a worse determination silently. |

---

## 2. Card B — the fuel seam is exactly inert, on two independent legs

### 2a. Coverage (2019-2021): the admission test refuses the year

`iso_electric_power_monthly_level('CAISO', y)`:

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **None** | **None** | **None** | 12 mo | 12 mo | 12 mo | 12 mo |

California prints only 11 of 12 N3045 months in each of 2019/2020/2021, so the seam's own
admission test refuses those years and CAISO's existing construction stands **byte-for-byte**.
Verified rather than assumed, exactly as the handoff §5 asked. Admitted annual means 9.486 /
7.033 / 3.606 / 4.275 $/MMBtu (2022-2025), reconciling the phase-0 table to three decimals.

### 2b. Ordering (2022-2025): the seam is superseded before it reaches the LP

Two `fleet_only` rebuilds per year on the keeper's own recipe, seam OFF vs ON
(`scripts/probes/_caiso_fuelvintage_phase0.py <year> B`):

| CAISO 2023 | shape | cells moved | max &#124;Δ&#124; |
|---|---|---|---|
| `fuel_prices` | (1910, 8760) | **0 / 16,731,600** | **0.0000000000** |
| `mc_base` (the offer the LP solves on) | (1910, 8760) | **0 / 16,731,600** | **0.0000000000** |

The predecessor pass measured the same identity in **all four** ADMITted years. The cause is the
keeper's own `gas_hub_basis_overlay` (SoCal / PG&E Citygate), which the solve log measures
repricing **1,443 gas generators at the measured hub spot in 12/12 months** of 2023, plus
`gas_plant_monthly_fuel_pricing = True` overwriting what remains with each plant's own F923 print
(81 priced from their own plant, 1,376 gap-filled). A measured constrained-hub index supersedes a
state-average delivered cost — which is the ordering the seam was deliberately given, and rule 19
`[R-ONE-MECH]` working as intended.

**The sharpest case, pre-registered before the solve and answered:** CAISO **Dec-2022** is
**16.058 $/MMBtu** below measured (~120 $/MWh at a CC heat rate) — the western gas crisis, and
CAISO's one materially reachable ISO-month. The PRECOMMIT §3c predicted **0 cells moved and C3b
unchanged to three decimals**, and that is what it is: the seam is superseded **exactly where it
would have bitten hardest**, because the Dec-2022 spike is already in the hub index the keeper
uses.

**The one place the seam does write, and why it still cannot reach the LP** (predecessor's
measurement, carried): the ISO-level `_gas_series` — which keys **only** the coal passthrough
sigmoid — moves in Sep/Oct/Nov 2025 by up to 0.535 $/MMBtu. It reaches nothing: **CAISO carries no
coal**, and `mc_base` is bit-identical in 2025 regardless.

**Disposition.** Inertness is **not** a disqualifier under the owner's §A7 ruling, and this lane
does not treat it as one. It is reported at full magnitude as *what the promotion is worth for
CAISO*: the mechanism is **not refuted** — it is **unreachable behind a strictly better measured
series**. A CAISO arm becomes meaningful only if the hub overlay is disarmed or its plant-layer
coverage falls below 12/12. Matrix cell `O → I`.

---

## 3. Card A — the retiree window is NOT inert in 2023, and CAISO corroborates PJM

Two fleet builds per year on the keeper recipe, swapping **only** the retiree parquet vintage
(HEAD's 2019-window vs a `planned_retirement_year >= 2023` filter reproducing pre-`7934e92c`).
Nothing under `data/raw` modified.

| CAISO | 2023 | 2024 | 2025 |
|---|---|---|---|
| LP rows (HEAD vs pre) | 1,910 / 1,846 | 1,904 / 1,840 | 1,909 / 1,845 |
| **injected rows' effective MW-h** | **0.0000000000** | **0.0000000000** | **0.0000000000** |
| shared-row max &#124;Δ pmax&#124; | 144.000 MW | 144.000 MW | 144.000 MW |
| shared-row max &#124;Δ availability&#124; | 0.0 | 0.0 | 0.0 |
| **shared-row Δ effective MW-h** | **+3,367,624.32 (+0.8478 %)** | **0.000000** | **0.000000** |

**The handoff §A9 is half right, and it is not the half that matters.** §A9 measured the
**COD mask** and closed the case as a false alarm. That half is confirmed here independently, to
ten decimals: the injected rows deliver **exactly zero**. But §A9 measured the *unit-level mask*
and never measured the *plant-level binned capacity* — and CAISO's fleet is **plant-binned**, so
the binning folds a dead unit's nameplate into the plant total **before** the tranche split, where
the mask never sees it.

**Root cause — the very plant §A9 said to stop looking at:**

```
plant 356  AES Redondo Beach (ST_GAS, LA basin)
  gen 7          480 MW  retired 2019-10   <- injected, correctly masked offline, delivers 0
  gens 5, 6, 8           retired 2023-12   <- online through 2023, and they ABSORB gen 7's 480 MW
```

| row | pre-`7934e92c` | HEAD | Δ |
|---|---|---|---|
| `ST_GAS_LA_BASIN_p356_committed` | 249.0000 | 393.0000 | **+144.0000** |
| `ST_GAS_LA_BASIN_p356_econc00…05` (×6) | 76.0833 | 120.0833 | **+44.0000** each |
| `ST_GAS_LA_BASIN_p356_peak` | 124.5000 | 196.5000 | **+72.0000** |
| **total** | | | **+480.0000 MW** |

144 + 6×44 + 72 = **480.0 MW exactly** — gen 7's whole nameplate, dispatchable in 2023 as CAISO
gas-ST, nine quarters after it stopped existing. **2024/2025 are clean because the leak needs a
surviving sibling**: after plant 356's Dec-2023 retirement the COD ramp zeroes the whole plant, so
the same +480 MW of `pmax` never becomes effective capacity.

**Independent corroboration of a cross-ISO defect.** The PJM lane found the same defect class in
`docs/FINDING-pjm-retiree-window-redistribution-2026-09-09.md` (W H Sammis, 720 MW of coal,
**+0.0615 %** of PJM's 2023 effective capacity). CAISO's leak is **+0.848 %** — **~14× PJM's in
relative terms** — and on **gas-ST rather than coal**, so this is a second mechanism class, not a
repeat of the same one. That finding's cross-ISO table lists CAISO at 480.0 MW; **confirmed here
as exact and fully realised in 2023.**

**NOT repaired by this lane, and the reason is scope.** The fix belongs in the shared
plant-binning path, so it moves every ISO's fleet in every year and would invalidate other lanes'
in-flight LPs. Rule 25 `[R-ISO-SCOPE]` makes that an owner-level call about the program's frozen
recipe, and the PJM lane has already routed it. **Charter task 3's STOP was honoured: this lane
stopped, measured, root-caused, and routed — it did not wave the delta through and did not
silently repair a shared path mid-flight.**

---

## 4. G-DRIFT — the code audit is impossible, the measured replacement FALSIFIED form 4, and the fingerprint named the cause

**The code audit cannot be run at all.** The keeper records `git_sha: e162147b`, and that object
**does not exist in this repository** (not a valid object name; absent from
`docs/governance/citation-commit-map.txt`; unreachable from all 543 commits on every ref). This is
the same unresolvable-`git_sha` finding the PJM lane reached independently.

**G-DRIFT-M**, pre-registered in PRECOMMIT §1, replaced it: 2024 and 2025 must return
max |class-hour delta| = 0.000000 MW against the committed keeper, because **both** of this lane's
changes are measured **exactly zero** there. **They did not:**

| vs committed keeper | max &#124;class-hour Δ&#124; | nonzero cells | Δ mean price |
|---|---|---|---|
| 2023 | 1,053.00 MW | 2,077 / 122,640 | +0.0033 $/MWh |
| 2024 | **1,979.84 MW** | 2,194 / 122,640 | +0.0085 $/MWh |
| 2025 | **1,585.38 MW** | 2,209 / 122,640 | — |

**So G-CTRL form 4 is FALSIFIED: the committed keeper is not a bit-faithful control at HEAD.**
`demand`, `slack`, `dump` and `reserve_price` are **exactly identical** in every year, so this is
dispatch/price reshuffling, not an input change on the load side.

**The cause, named at zero LP cost by the repo's own instrument** (capx D79 solve-surface
fingerprint):

| bundle | date | fingerprint | rows |
|---|---|---|---|
| `caiso262_2022_touchpoint` | 2026-09-07 | `f4057d6db19fe8d3` | **202** |
| `caiso267_fossil92` | 2026-09-09 | `cba92d202f32f9fd` | **204** |
| **this lane's runs** | 2026-09-09 | `cba92d202f32f9fd` | **204** |

CAISO's solve surface gained **exactly two rows** and changed fingerprint between 2026-09-07 and
2026-09-09. Diffing the surface modules names them:

1. **`EGRID_CT_HR_PHYSICAL_FLOOR`** — a CT heat-rate physical floor. **`CT_PEAKER` is the class
   that moves in every single year** (−0.0063 / −0.0063 / −0.0032 TWh in 2023/2024/2025).
2. **`F923_GAS_PRICE_PLAUSIBILITY_BAND`** — the F923 gas-price plausibility screen band. CAISO's
   own solve log prints it repricing plants: *"F923 gas-price plausibility screen for 2023 (CAISO,
   band [0.5, 2.0] × state N3045 reference) … 3 high → reference (3 plants)"*.

(The third and fourth names added to `constants.py` in that window,
`ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU` and `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`, are **not** in
CAISO's projected surface — the ISO projection drops them, which is why the count moves by exactly
two and not four.)

Both are gas/CT-side, which is precisely where every observed delta lives. **The movement is HEAD
drift, not this lane's two changes** — which phase-0 proved are exactly zero in 2024 and 2025.
G-DRIFT-M did its job: it detected drift the code audit *could not have been run* to find, and the
fingerprint attributed it, for zero LP.

---

## 5. The 2020/2021 touchpoints are blocked on DATA, not on a marker

CAISO holds `complete`, so 2020/2021/2022 are authorized. **2020 and 2021 are nevertheless
unsolvable at HEAD**, and the block is upstream of the LP:

- `data/raw/reference/caiso-supply-consistent-demand/` carries **2022, 2023, 2024, 2025 only**.
  The keeper's demand basis does not exist for 2020/2021, and the solve fails closed:
  *"caiso_supply_consistent_demand: no artifact for 2020 … run
  scripts/data/derive_caiso_supply_consistent_demand.py"*.
- The derive **cannot** simply be extended: `YEARS = (2022, 2023, 2024, 2025)` and it requires a
  per-year **bench part** carrying a CEMS anchor, and `frontend/data/backcast/bench/CAISO/` holds
  **2022-2025 only**. It also carries a per-year `_ANNUAL_GUARD` band, which would have to be set
  for a year nobody has ever scored.

**Cross-ISO context** (bench-part coverage): NEISO 2020-2025, PJM/ERCOT 2021-2025, **CAISO
2022-2025**, NYISO 2022-2025, MISO 2023-2025. **CAISO's validation ladder bottoms out at 2022 at
HEAD** — the 2020/2021 rungs are a data-intake task (unrestricted under rule 22, which holds out
the *score* and never the *data*), not an LP task, and they are named here rather than left as a
silent gap. **2019 stays REFUSED** for every ISO (locked tier, `final` empty, freeze ACTIVE).

The handoff's *"CAISO's FIRST validation touchpoints"* is also wrong: **2022 was already spent
three times** — `caiso-262`, `caiso-265` and `caiso-267` — and 2022 is validation tier, which
rule 22 makes **iterable by design**, so re-spending it is its purpose, not a second consumption
of a one-shot.

---

## 6. What was solved, scored and promoted

Four CAISO invocations, all local, years sequential within each, two concurrent at a time
(rule 12 `[R-PARALLEL]`), `scripts/prepare_solve_container.py` run first (§A6 — 8 GiB swap
provisioned, arena/thread pins exported; peak was comfortable and nothing was OOM-killed).

| run | years | disposition |
|---|---|---|
| `caiso_fuelvintage_SPAN` → `caiso_fuelvintage_span` | 2023, 2024, 2025 (**one invocation**) | **registered `2026-09-09-caiso-fuelvintage-860-gas`, PROMOTED TO KEEPER** |
| `caiso_fuelvintage_H2` → `caiso_fuelvintage_tp2022` | 2022 (`--holdout-authorized`) | **registered `2026-09-09-caiso-fuelvintage-2022-touchpoint`, stamped and folded** |
| `caiso_fuelvintage_T1` / `_T2` | 2023+2024 / 2025 | superseded shards, kept on disk (see §6a) |
| `caiso_fuelvintage_H1` | 2020, 2021 | **never solved — blocked on missing data, §5** |

### 6a. A defect of MINE, found and fixed rather than reported as a result

The first attempt composed T1 (2023-2024) and T2 (2025) into one bundle by hand. **T1 and T2
carry different year-scoped `eia923` / `eia930` / `campd` snapshots**, so the composed bundle
scored 2025 against T1's — and C4-2025 came back **`r=None, NRMSE=8.406`** against the keeper's
0.877 / 0.298. That is a broken measurement, not a physical result, and reporting it as a C4
regression would have been wrong. It was re-solved as **one invocation over 2023-2025**, which
also restores the keeper's own input snapshot (`eia923-8ca120c6637d`, identical to
`caiso260_demand_vintage`'s). **C4 then PASSES.** Rule 16 `[R-ALLYEARS]`'s "one bundle" is
recorded here as also meaning *one input snapshot*; hand-composition across shards is not
equivalent, and this lane recommends the sharding guidance in the handoff §A1 be amended to say so.

### 6b. The determination

`scripts/calibration_verdict.py --run-id 2026-09-09-caiso-fuelvintage-860-gas`:

| criterion | tier | arm | incumbent keeper |
|---|---|---|---|
| C1 fuel-mix by class | load-bearing | **PASS** | PASS |
| C2 system volume | load-bearing | **PASS** | PASS |
| C3a mean LMP | load-bearing | **PASS** | PASS |
| C3b price duration/shape | load-bearing | **PASS** | PASS |
| C3c price tail / scarcity | supporting | **CAVEAT [ledgered]** — model 23 / 0 / 0 h vs RT actual 47 / 35 / 8 | CAVEAT [ledgered] |
| C4 fleet hourly dispatch corr. | supporting | **PASS** | PASS |
| C6 governance | protective | **PASS** (attested at registration) | PASS |
| C8 forced-energy share | protective | **PASS** | PASS |
| **DETERMINATION** | | **CALIBRATED** | CALIBRATED |

Reported-only, at full magnitude: C5a CO2 vs eGRID 2023 **−11.0 %** (FAIL, not gated); D-A
diurnal amplitude 69.2 % of measured in 2023 (hod r +0.957, phase OK).

**Rule 22 D-5(b) is satisfied:** the re-verified determination is **CALIBRATED**, i.e. *not
worse* than the one the `complete` marker was declared on, so the escalation branch did not fire
and the marker was re-keyed (`keeper` → the new run, `determination` re-verified without a solve,
`keeper_at_declaration` untouched). `audit_keepers --iso CAISO` and `build_status --check --iso
CAISO` both PASS after the promotion.

### 6c. Dispatch response, arm minus the committed keeper (TWh)

Reported in full, and **not** offered as evidence for the mechanism — §4 shows most of it is HEAD
drift, not this lane's changes:

| year | CT_PEAKER | CC_REGULAR | ST_GAS | import | other |
|---|---|---|---|---|---|
| 2023 | −0.006271 | +0.004917 | +0.000320 | +0.001274 | solar −0.000050, hydro −0.000011 |
| 2024 | −0.006269 | +0.006214 | +0.001641 | −0.001255 | CC_CHP −0.000051 |
| 2025 | −0.003199 | +0.003139 | +0.000034 | +0.000885 | solar −0.000328 |

**The signature that matters:** `ST_GAS` moves *more* in 2024 (+0.001641 TWh) than in 2023
(+0.000320), although the 480 MW leak exists **only** in 2023. So the leak is **not** what these
deltas are made of — plant 356 is high-heat-rate steam far up CAISO's stack and clears rarely,
exactly as the PRECOMMIT §4 predicted ("ST_GAS up, price down, both small"). The common
CT_PEAKER↓ / CC_REGULAR↑ pattern present in **all three years plus 2022** is the HEAD-drift
fingerprint of §4.

### 6d. The 2022 validation touchpoint (rule 30 `[R-TOUCHPOINT-FOLD]`)

Stamped to the new keeper with **recipe identity PASS (0 differing keys)** and folded into its
report — it is the keeper's frozen recipe on a held-out year, which is what rule 30 asks for.

| 2022 rung | vs in-sample |
|---|---|
| C1 fuel-mix, C2 volume, C4 dispatch corr., C6, C8 | **held** (PASS) |
| C3c price tail | **improved** (CAVEAT → PASS) |
| C3a mean LMP | **degraded** — FAIL at **+13.2 %** |
| C3b price duration/shape | **degraded** — FAIL at **NRMSE 0.242** |

**Rung determination NOT-YET.** Per **rule 30(c)** this **does not downgrade CAISO**, whose
determination is the train-tier verdict and stays **CALIBRATED**; and per rule 22 a validation
number is iterable model-*selection* evidence that must never be quoted as a certified
out-of-sample skill number. The Card A capacity delta in 2022 is +60.1 MW, and the measured
dispatch response is correspondingly immaterial (largest class move **0.010 TWh** on a ~220 TWh
system) — **exactly the pre-registered prediction that a large 2022 move would be a bug, not a
win.**

---

## 7. THE PROMOTION QUESTION, PUT EXPLICITLY TO THE OWNER (rule 31 `[R-RETAIN]`)

**Nothing has been deleted and nothing has been pruned.** Every bundle this session produced is
on local disk; the gitignored solve families (`results/caiso_fuelvintage_{SPAN,T1,T2,H2}`) hold
the full outputs, and the two registered bundles are committed slim, matching the keeper's shape.
**The superseded `caiso260_demand_vintage` keeper is deliberately NOT pruned**, departing from
rule 15's keeper-only sweep — rule 31 outranks it while an owner decision is open, and the
ercot-255 incident is why.

**The question.** The §A7 ruling — *promote both regardless of inertness* — was made when every
document asserted Card A was **inert in 2023-2025**. §3 shows it is not: the promoted keeper's
2023 carries **480 MW of gas-ST that retired in October 2019**. Inertness was never the issue the
ruling anticipated. So:

> **Promote now, or hold for the plant-binning fix?** The promotion is executed as ruled, and the
> determination is unchanged at **CALIBRATED**, so nothing is worse. But CAISO's designated keeper
> now knowingly contains a 2023 fleet defect whose repair lives in the shared plant-binning path.
> **(a) Keep it** — the retiree window is the *accurate* fleet input (rule 14), the leak is a
> separate binning bug, and holding the input hostage to the bug inverts rules 1/14. **(b) Hold
> it** — re-designate `caiso-260` (intact, zero cost) until the binning fix lands, then re-solve.
> **This lane recommends (a)**, with the binning fix raised as its own cross-ISO owner item.

**These bundles do not survive this session's container.** If the answer is (b), or if any further
measurement is wanted from these solves, say so before the container is reclaimed; otherwise a
re-solve costs ~35 min for the span and ~13 min for the 2022 rung.

**A second, separable owner item this lane raises rather than acts on:** CAISO's validation ladder
**cannot reach 2020 or 2021** until the supply-consistent demand artifact and the
`bench/CAISO/` parts are built for those years (§5). That is unrestricted data-intake work under
rule 22, and it is the precondition for the touchpoint loop the `complete` marker was granted for.

---

## 8. Gate state at the end of this session

| gate | result |
|---|---|
| `build_status.py --check --iso CAISO` | **PASS** — *"status parts in sync (1 keepers: CAISO)"* |
| `audit_keepers.py --iso CAISO` | **PASS** — 0 failures, 0 warnings (keeper, holdout, marker, status) |
| `check_mechanism_matrix.py --base origin/main` | **PASS** (exit 0); the CAISO keeper-stamp drift it flagged was this lane's and is cleared |
| `check_registry_payload_parity.py` | **FAILS on 10 bundles, ALL of them `ercot261_*` and ALL already on `origin/main`** — zero CAISO rows; pre-existing and the ERCOT lane's (rule 25) |
| `check_cache_key_registration --base origin/main` | known-red on `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`, pre-existing, not this lane's |

**The handoff §8 CAISO status RED was already cleared** by caiso-267's rebuild before this session
started — verified, not assumed, and nothing was written to repair it.

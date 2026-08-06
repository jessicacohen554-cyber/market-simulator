# FFR-7B — The RPS/clean-tier repair: Arm 1 LANDED COMPLETE AND MEASURED; Arms 2–3 handed off

**Lane:** implementation (owner decision D-22(a), sitting Addendum V.5/V.6, signed 2026-08-06).
**Spec:** `docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md` (FFR-6B) — implemented, not
redesigned. **Head at lane start:** `origin/main` `a9e1d084` (the prompt's `e2ea0b59` had moved:
miso-135/caiso-176 merged; keepers re-verified from the shards — CAISO already
`2026-08-06-caiso-175-tac-intake`). Main moved TWICE more mid-lane (`1af56e4a`, then `156b6e7d`
— the v3.1 re-score + the **nyiso-128 promotion**, which changed NYISO's keeper to
`2026-08-06-nyiso-128-control` after this lane's measurement ran; see §3.4). `complete` =
{CAISO, NEISO, NYISO, PJM}; `final` EMPTY; holdout freeze ACTIVE and never approached (every
solve here is in-sample 2023–2025).

## 0. Headline

* **ARM 1 IS LANDED AND MEASURED.** The tier/eligible-set level fix for NYISO, NEISO, CAISO:
  each renewable row now carries its statute's RENEWABLE trajectory and statute-defined
  eligible set. Zero free parameters, no new `ScenarioConfig` field, no gate flag. The code
  merged to main mid-lane (owner fast-merge of the pushed branch, commits `45fafa9c..d0f860e6`);
  the paired-control registration followed on the re-based branch.
* **Backcast contact: NONE — proven by code path, then MEASURED as ordered.** Same-head
  paired controls on each affected ISO's keeper recipe, 2023–2025: **BYTE-IDENTICAL in all
  three ISOs** (NYISO 25/25, CAISO 22/22, NEISO 28/28 parquet outputs sha256-equal;
  `results/calibration/_ffr7b_arm1_ab_compare.json`). No keeper metric moved → **no
  promotion hold**. Registered as `nyiso-129 / caiso-177 / neiso-84 ffr7b-arm1-zerodelta`.
* **Three pre-existing main breakages found and fixed in passing** (§4): nyiso-128's
  UNREGISTERED cache-key field (the FFR-5E §6.2 hazard class this lane was told to guard —
  found live on main: pinned default key moved `603c2498…`→`318c2203…`, every default-key pin
  test failing at clean `e2ea0b59`/`a9e1d084`); a repo-wide-red ruff F841 pair; and the
  constants-facade completeness test missing `STORAGE_MEASURED_BASE_FLEET_ISOS`.
* **Arms 2 and 3 are HANDED OFF, not landed** (§6): never land a partial arm — the remaining
  budget after Arm 1's measurement, the flaky push transport (§5), and main's merge velocity
  made a complete Arm-2 landing unsafe. Design-to-implementation notes are embedded below.

## 1. Arm 1 — what landed (commits `45fafa9c..d0f860e6`, now in main)

### 1.1 Trajectory corrections (`STATE_RPS_FLOORS`, `config/capacity_market.py`)

Every level web-verified against primary statute text 2026-08-06 (URLs in the parameter
registry entries for `state_rps_floors.*` / `rps_eligible_fuels_by_iso.*`):

| ISO | was (2026/30/40/45) | now | statutory basis |
|---|---|---|---|
| NYISO | .40/.70/**1.00**/**1.00** | .40/.70/**.70**/**.70** | PSL §66-p(2)(a): 70% renewable by 2030, NO post-2030 renewable %; the 100x40 zero-emission standard (§66-p(2)(b), nuclear-counting) leaves the row |
| CAISO | …/.50/.60/**.80**/**1.00** | …/.50/.60/**.60**/**.60** | §399.15(b)(2)(C) verified verbatim: "not less than 60 percent" ALL subsequent years; SB 100/SB 1020 zero-carbon (§454.53: 90x35/95x40/100x45) leaves the row |
| NEISO | .30/.45/**.70**/**.80** ("CES blend") | **.29/.40/.48/.50** | per-state NEW-renewable (Class I/RES) blend on the ACP block's load shares (MA .48/CT .24/NH .09/ME .09/RI .06/VT .04): MA c.25A §11F (30/40, +1%/yr → 50/55), CT §16-245a (40x30, flat), RI §39-26-4 (41/72 → 100x33), ME §3210 + LD 1868 2025 (33/50 → 60x40 flat), NH RSA 362-F:3 (15.7 flat), VT Act 179 new-renewable tiers (Tier I EXCLUDED — counts HQ large hydro; VT is 4% of load so its tier-attribution uncertainty moves the blend < 1 pp). Blend: .292/.396/.480/.504, stored rounded |

One deviation from FFR-6B §8.2's parenthetical, honored on the primary source: **biomass and
biogas are NOT in PSL §66-p(1)(b)** (legacy PSC Tier-1 orders admitted some biomass; the
statute does not) — NYISO's set gains hydro and offshore wind, not biomass. Second statutory
update caught by verification: **ME LD 1868 (2025)** extends Class IA to 50% by 2040 (Class
I+IA 60x40) — the blend does not plateau ME at 2030.

### 1.2 Eligible sets (`RPS_ELIGIBLE_FUELS_BY_ISO` — new cited table)

Data, not hardcoded class tuples (FFR-6B §6.3(2)): resolved against `FUEL_TYPE_MAP` at
`model.lp.rows._resolve_rps_eligible_gen_idx`; unknown names hard-error; **nuclear refused by
name** (CX-6a — a clean tier that counts nuclear is a separate row family, never a widening).

| ISO | set | note |
|---|---|---|
| NYISO | wind, solar, offshore_wind, **hydro** | §66-p(1)(b): existing hydro counts (NYPA Niagara/St. Lawrence) — the 20.2 pp under-count |
| CAISO | wind, solar, offshore_wind, **geothermal, biomass** | §25741(a); small hydro ≤30 MW statutorily eligible but EXCLUDED as misaligned (rule 14 exception): the single `hydro` class aggregates it with non-eligible large hydro (~10% of CA load); residual ~1 pp under-count is within the PJM/MISO folded-in tolerance |
| NEISO | wind, solar, **offshore_wind** | 225 CMR 14.05; small biomass/hydro stays folded (~3.8 pp, FFR-6B §8.2 convention) |
| PJM / MISO / ERCOT | no entry (None) | wind+solar-only row, byte-identical |

Plumbing: `_build_rps_row` gains `eligible_gen_idx` (thermal-block columns for eligible
non-W/S classes); `rps_eligible_fuels` threads runner → `DispatchSpec` (UNSET default —
omitted key, backcast kwargs key-set unchanged) → `solve_dispatch` → `build_constraints`.
The stale "moot for ERCOT/PJM" CES-suppression comment fixed in `runner.py` +
`policy/federal_ces.py` (FFR-6B §5.4), and the spec's superseded nuclear-counting RPS block
re-written (`model-methodology-spec.md`).

### 1.3 Deliberately NOT changed (so it is not read as an omission)

* `_RPS_ELIGIBLE_FUELS` / `_RENEWABLE_NEW_FUELS` (capacity screens) stay wind/solar-only:
  candidates are wind/solar; existing non-VRE renewables' attribute revenue stays on `eac_*`.
  Widening the retirement screen's REC credit to existing hydro/geothermal/biomass units is a
  real follow-up question, but a second mechanism change — not the diagnosed defect.
* ACP ceilings unchanged. PJM/MISO trajectories/sets unchanged (adjudicated sound).

### 1.4 Byte-identity proof (test, not assertion)

`TestRPSConstraint::test_rps_eligible_default_set_is_byte_identical` — `build_constraints`
with `rps_eligible_fuels=None` vs explicit `("wind","solar")`: identical matrix and bounds,
on a fleet holding a hydro unit so a widened set DOES differ (non-vacuous, asserted). Plus
hydro-counting dual semantics, nuclear/unknown refusals, statutory pins
(`tests/unit/policy/test_rps.py`), FH-2 forecast-era pins deliberately updated
(NEISO 2026 → 0.29; CAISO 2045 → 0.60).

## 2. Forecast-side consequence (the mechanism removed)

Before: three rows demanded clean-tier out-year shares of a wind+solar-only LHS → duals
pinned at the ACP ceiling for the whole horizon → `rps_shadow_price` fed a permanent
$40–50/MWh entry subsidy to every VRE candidate (FFR-6B §8.3). After: the row demands the
statute's renewable share of the statute's eligible set. The $/MW sizing still needs a
forecast pair (FFR-6B §11 left it open); the natural instrument is a bounded 2026+ A/B once
Arm 3's family exists, registered to the FORECAST namespace only.

## 3. Arm 1 measurement — the Addendum-D paired controls

### 3.1 Protocol

`scripts/replay_keeper.py <keeper bundle> --out-dir results/calibration/ffr7b_arm1_<iso>_{ctrl,arm}`
— control at branch base `a9e1d084` (detached, unmodified tree), arm at the Arm-1 commits.
`MARKET_SIM_WARMSTART_XYEAR=0` pinned by the tool (year-1 basis cache hard-OFF: both sides
cold, byte-comparable); no `--reuse-solved` (no cache can leak between phases); years
2023–2025 sequential per invocation. **Invocations SERIAL: two concurrent zonal 3-year
replays OOM-killed this 15 GB box** (CAISO at 6.9 GB RSS, `oom-kill` in dmesg) — rule 12's
≤2-concurrent allowance does not fit this container class; the CAISO control was re-run
alone. Comparator: `scripts/probes/ffr7b_arm1_paired_control_compare.py` (sha256 per parquet
+ numeric max-|Δ| fallback).

### 3.2 Result — zero delta, everywhere

| ISO | keeper recipe | parquets compared | byte-identical | determination (arm) | = keeper? |
|---|---|---|---|---|---|
| NYISO | nyiso-125-seam-envelope | 25 | **25/25** | NOT-YET (price_mean; C3c ledger carried) | **verbatim** |
| CAISO | caiso-175-tac-intake | 22 | **22/22** | CALIBRATED-WITH-CAVEATS (C3a, C3c) | **verbatim** |
| NEISO | neiso-83-ca1-reclass | 28 | **28/28** | CALIBRATED-WITH-CAVEATS (C3c) | **verbatim** |

Full hash tables: `results/calibration/_ffr7b_arm1_ab_compare.json`. **No keeper metric
moved; no promotion hold.** Registered (rule 15) as
`2026-08-06-nyiso-129-ffr7b-arm1` / `2026-08-06-caiso-177-ffr7b-arm1` /
`2026-08-06-neiso-84-ffr7b-arm1`, attestations carried from the byte-identical keepers.
Controls NOT separately registered — byte-identical duplicates whose content is fully
attested by the committed hashes (registering both would spend retention slots on identical
payloads; the neiso-83 control-zerodelta precedent registered its control because it was a
distinct code state under test, which these are not).

### 3.3 Why zero-delta was provable ex-ante (and measured anyway, as ordered)

`get_rps_target` / `get_rps_acp` / `get_rps_eligible_fuels` have exactly one consumer seam
(`runner.py`), gated on `config.rps_enabled`; `pipeline.backcast_config.
build_calibration_config` hard-sets `rps_enabled=False`; all three keeper `run_config.json`s
record it false. The prompt's "backcast RPS rows of three keeper ISOs" premise is FALSE at
this head — no backcast builds an RPS row at all. The paired controls were still worth
running: they measured that the IMPLEMENTATION (signature changes through rows/model/
solve_dispatch/spec, the new resolver, the spec-field addition) is also byte-inert, not just
the constants.

### 3.4 The mid-lane NYISO keeper change

Main promoted `2026-08-06-nyiso-128-control` (solar market-generator basis lane) AFTER this
lane's measurement ran on nyiso-125 (the keeper at lane start, per the re-verified state).
The zero-delta conclusion is recipe-independent — the `rps_enabled=False` gate is ISO-wide
and recipe-agnostic, and nyiso-128's recipe differs only in fields orthogonal to the RPS
path — so the measurement was NOT re-run against the new keeper. A future session wanting
belt-and-braces can replay `ffr7b_arm1` against `nyiso128_control` and will get the same
28-file identity.

## 4. Pre-existing main breakages fixed in passing

1. **nyiso-128's `nyiso_solar_market_generator_basis` landed UNREGISTERED** in
   `_CACHE_KEY_OPTIONAL_FIELDS` — its mere addition moved the pinned default cache key
   `603c2498bf71d21d` → `318c22035173707c` and broke every default-key pin test on main
   (verified failing on unmodified checkouts of `e2ea0b59` AND `a9e1d084`). Backfilled
   (registry + defaults ledger, the documented ercot-162/FFR-4B remedy); default key
   restored; `check_cache_key_registration` passes (140 registered). Exactly the FFR-5E §6.2
   hazard class the FFR-7B prompt flags — found live on main, not caused here.
2. **ruff F841 × 2** in `scripts/gen_miso126_attestation.py` (merged red in PR #3559) —
   failed the repo-wide lint lane; unused locals removed.
3. **`test_constants_facade::test_moved_surface_is_complete`** was failing on main:
   FFR-4D's `STORAGE_MEASURED_BASE_FLEET_ISOS` was facade-re-exported but never added to the
   test's frozen inventory. Backfilled (plus the new `RPS_ELIGIBLE_FUELS_BY_ISO`).
4. **Mechanism-matrix line anchors** repaired (`--fix-anchors`, digits only) after the
   registration shifted `scenarios.py` line numbers.
5. **Parameter registry regenerated** (first re-run since 2026-08-05): 14 new entries — the
   3 eligible-set rows (cited) plus 11 catch-ups from FFR-5C/5D/5E, ercot-167/168,
   nyiso-127/128, neiso-83, caiso-175 sessions that had not re-run the generator.

Six OTHER fast-tier failures reproduce at clean `a9e1d084` and were NOT touched (out of
scope, left for their owners): `test_ercot_thermal_as_endogenous` ×2,
`test_ff_readiness_battery::test_marker_state_reflects_committed_markers`,
`test_forecast_parity` ×2, `test_outages::test_unknown_iso_degrades_to_empty`. (The v3.1
re-score merged mid-lane may have addressed some; not re-verified here.)

## 5. Operational notes a successor should not rediscover

* **The container's git clone is SHALLOW, and shallow push breaks the proxy relay**: every
  `git push` (even zero-object ref pushes) died with 408/500 + "remote end hung up" while
  fetch worked — the receive-pack POST carries ~16 KB of `shallow` advertisements the relay
  mishandles. **`git fetch --unshallow origin` fixed push entirely.** Do this FIRST in any
  session that must push from this environment.
* **Two concurrent 3-year zonal replays OOM a 15 GB box** (§3.1) — serialize; rule 12's
  concurrency allowance presumes a larger container.
* `scripts/regenerate_clean.py` reported **2/50 datatypes failed** (identities lost to a
  `tail`-truncated log; the three ISOs' replay inputs were unaffected — all six replays ran
  clean). Re-run with full logging if a later solve hits a missing partition.
* The owner merges pushed branches within minutes and deletes them: re-fetch + re-base
  (`git checkout -B <branch> origin/main` + cherry-pick unmerged work) rather than assuming
  branch continuity. The registration commit was landed exactly that way.

## 6. Arms 2–3 — HANDED OFF (never land a partial arm)

Everything below is design-to-implementation distillation from FFR-6B, verified against the
code at this head; no Arm-2/3 code was written.

### 6.1 Arm 2 — K-row generalization, MISO armed only

1. `model/lp/layout.py`: `n_rec_acp` is already a count — K regions ⇒ `n_rec_acp = K`
   (K × T ACP columns); generalize `rec_acp_col(t)` → `(k, t)`.
2. `model/lp/costs.py:248-250`: the ACP block assignment broadcasts; pass a `(K,)` price
   vector for per-region ACPs (MISO: all $30, `STATE_RPS_ACP` — per-region refinement not
   required, FFR-6B §3.4).
3. `model/lp/rows.py`: `_build_rps_rows` — per region r: +1 on W/S columns of
   `eligible_zones(r)` (zone-index filter on the same arange expression), +1 on region r's
   ACP columns, RHS = Σ_{(z,w)∈obligated} w × target_r(y) × Σ_t demand[z,t]. K=1/mask=all
   must be BYTE-IDENTICAL — prove with a regression test (the Arm-1 test pattern), not an
   assertion.
4. `model/lp/model.py`: dual recovery becomes a K-slice at the same end anchor
   (`row_dual[-(n_reserve+K):-n_reserve]`, mind n_reserve=0); mass-cap recovery's
   `rps_present` becomes K. `rps_shadow_price`: scalar when K==1 (consumer-value-identical);
   when K>1 a per-zone vector `p[z] = max{dual_r : z ∈ eligible_zones(r)}` (FFR-6B §3.2),
   plus per-region duals exposed for diagnostics.
5. **REQUIRED COMPANION** — per-zone credit at the three consumers (`new_entry.py:935,1111`,
   `retirements.py:1961`) via a shared helper (scalar passes through; vector indexes by the
   candidate's/unit's zone). A scalar left in place would broadcast MISO-East's dual to an
   Arkansas candidate and rebuild the defect.
6. Gate flag (default OFF, forecast-mode, MISO-only arming in runner), registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` + defaults ledger IN THE SAME COMMIT, matrix row minted in
   the same PR (rule 28c; CI enforces).
7. The MISO state-row table (cited constants, ALL from the existing `STATE_RPS_FLOORS["MISO"]`
   comment block — no new derivation): MN (host West, share .77, .26/.40/.55/.55, eligible =
   Midwest footprint i.e. all zones except MISO_South); MI (East, .57, .35/.50/.60/.60,
   eligible = East ONLY — MCL 460.1029/MIRECS, the restriction that IS E-1); WI (East, .43,
   flat .10, Midwest); IL (Illinois, 1.0, .25/.40/.50/.50, eligible = Illinois — CEJA IPA
   narrow reading, documented); MO (Plains, .43, flat .15, Midwest). MT EXCLUDED (the §1.4
   ±.0345 bracket — one EIA-861 line to close, recorded open).
8. Tests: flag-off byte-identity (multi-zone toy + K=1 legacy path); armed toy where the
   East row is unsatisfiable by Plains wind (mask binds); blend reproduction
   Σ rhs_r / demand ≈ .1139/.1606/.1981 at 2026/30/40 (FFR-6B §1.5); per-zone credit wiring
   (East candidate sees East dual; South candidate 0).
9. Measurement: bounded 2026+ MISO forecast pair (off vs armed), registered via
   `register_forecast_run.py` to `frontend/data/forecast/` — NEVER the backcast registry.
10. **E-1 NEVER ACQUIRES A BUILD LIMB** — the row's only output is a price (state it in the
    gate-flag comment and the rows builder docstring). PJM/NEISO zonal rows REFUSED ON
    STRUCTURE (FFR-6B §7) — do not build them.

### 6.2 Arm 3 — clean-tier row family, MISO-West + MISO-East only

Second INDEPENDENT row family on Arm 2's machinery (never a widened renewable row), second
default-OFF forecast gate. Rows: MN carbon-free (§216B.1691 subd. 2g: 80% 2030 / 90% 2035 /
100% 2040; qualifying set includes HYDROGEN and BIOMASS → nuclear, hydro, wind, solar,
hydrogen_ct, hydrogen_ccgt, biomass) and MI clean (2023 PA 235: **80% 2035** — the interim
knot MISSING from the old code comment — /100% 2040; qualifying admits QUALIFIED CCS GAS →
+ gas_cc_ccs; eligible zone East). **Illinois gets NO row — recorded null** (CEJA is a
source-side phase-out, not an LSE share obligation). Qualifying sets are per-statute DATA
resolved via `FUEL_TYPE_MAP` (rule 18 spirit). Composition (rule 19, FFR-6B §6.4): the clean
dual enters the EXISTING `max(eac, rps_shadow)` doctrine for nuclear/hydro — never a sum;
`federal_ces_replaces_state_rps` suppresses the state CLEAN rows too; a wind MWh satisfying
both its renewable row and its clean row is CORRECT (two constraints, one MWh) with generator
credit = max(), never sum. **A 100%-by-2040 clean row MUST carry a feasibility escape**
(reuse the $30 MISO proxy or a cited alternative, documented) — a hard row is an
infeasibility bomb. **The §45U-vs-clean-dual composition for nuclear is OPEN and blocks
ARM 3's ARMING ONLY, not its implementation** (§45U(b)(2) gross-receipts phase-down implies
phase-down-then-add, not max(); unresolved — put it in the gate-flag code comment verbatim).

## 7. Rule discharges

Rule 5/13: every level/set carries a statute citation in the constants block + parameter
registry (web-verified 2026-08-06, URLs recorded). Rule 14: statutory inputs replace
mis-tiered estimates; CAISO small-hydro and VT Tier-I exclusions are documented misalignment
reconciliations. Rule 15: three completed runs registered same-session with bundles +
sidecars + payloads (parity-checked); retention swept (nyiso-119 pruned post-merge). Rule 19:
one row family per phenomenon — clean tiers left the renewable row and exist nowhere yet.
Rule 22: solves 2023–2025 only; freeze never approached. Rule 24: no new tunables (surface =
two cited statutory tables; the one registration touched was nyiso-128's backfill). Rule 25:
per-ISO statutes only; nothing crossed. Rule 27: all pushes over `git push` with exact
on-disk bytes; branch tip + blob shas verified against the remote after each push. Rule 28:
no mechanism tested or armed; no new flag ⇒ no matrix row (Arms 2/3 mint theirs); anchor
digits repaired only.

## 8. What I did NOT do

No solve/scoring outside 2023–2025; no keeper change of my own (NYISO's changed upstream);
no capacity-screen REC-credit widening (§1.3); no $/MW sizing of the removed subsidy (§2);
no Arm-2/3 code; no PJM/NEISO zonal-row work (REFUSED, FFR-6B §7); did not identify the two
failed regenerate_clean datatypes (§5); did not re-run the paired control against the
newly-promoted nyiso-128 keeper (§3.4, recipe-independence argued on the gate).

# FFR-7B-2 — Arms 2 and 3 of the RPS/clean-tier repair: K-row compliance regions + clean-tier family (MISO)

**Lane:** implementation (owner decision D-22(a), sitting Addendum V.6; continuation chartered
at Addendum X.2/X.3). **Spec:** FFR-7B §6 design-to-implementation notes
(`docs/handoffs/ffr-7b-rps-clean-tier-repair-2026-08-06.md`) implementing FFR-6B
(`docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md` §§3, 6) — implemented, not
redesigned. **Head at lane start:** `origin/main` `dd4e919c` (the prompt's `97e37b0f` had moved;
keepers re-verified from the shards at this head — ERCOT `2026-08-05-run168b-year-curves`,
PJM `2026-08-04-pjm-152-collapse`, CAISO `2026-08-06-caiso-175-tac-intake`, NYISO
`2026-08-06-nyiso-128-solar-basis`, NEISO `2026-08-05-neiso-83-ca1-reclass`, MISO
`2026-08-05-miso-132b-cc-committed`). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY;
holdout freeze ACTIVE and never approached — every solve here is forecast-mode 2026+ (the
rule-22 clause explicitly permits it: no measured H1-2026 actual is read or scored).

## 0. Headline

* **ARM 2 IS LANDED COMPLETE**: the K-row per-state RPS compliance-region generalization
  (FFR-6B E-1), MISO-armed-only behind `miso_rps_compliance_regions` (default OFF), with the
  per-zone credit companion at all three capacity-screen consumers, the same-commit cache-key
  registration, the same-PR matrix row, the full §6.1(8) test set, and the bounded 2026–2030
  MISO forecast pair (off vs armed) registered to the FORECAST namespace (§3).
* **ARM 3 IS LANDED COMPLETE AS AN IMPLEMENTATION, ARMING BLOCKED AS ORDERED**: the
  clean/carbon-free tier row family (FFR-6B E-2) — MN carbon-free + MI clean on the Arm-2
  machinery, per-statute qualifying sets as data, Illinois a recorded null, per-row feasibility
  escapes, the rule-19 `max()` composition — behind `miso_clean_tier_rows` (default OFF). The
  §45U-vs-clean-dual composition is OPEN and blocks ARMING ONLY, stated in cited comments at
  the gate flag and at the retirement-screen composition site (§5).
* **Byte-identity of every unarmed path is proven, not asserted**: the pinned default cache key
  `603c2498bf71d21d` verified unchanged with both fields present; K=1/mask=all reproduces the
  legacy single row byte-identically by regression test; every default-key pin test passed at
  the base commit BEFORE any edit (the FFR-5E §6.2 guard the prompt ordered) and after.

## 1. Arm 2 — what landed (commit `d0085e16` + the runner arm `86e84ea8`)

Follows FFR-7B §6.1's nine steps verbatim:

1. **Layout** (`model/lp/layout.py`): `n_rec_acp` is a K count (region-major ACP block);
   `acp_col(t, k=0)`.
2. **Costs** (`model/lp/costs.py`): the ACP block takes a `(K,)` per-region price vector
   (scalar legacy path unchanged; shape-checked).
3. **Rows** (`model/lp/rows.py::_build_rps_region_rows`): per region r, +1 on the W/S columns
   of `eligible_zones(r)` (zone-index filter on the same arange expression — rule 2: the only
   Python loop is over K ≤ 6 regions, the `_build_mass_cap_rows` shape), +1 on region r's OWN
   ACP column, RHS `Σ_z frac[r,z]·Σ_t demand[z,t]`. Mutually exclusive with `rps_target`
   (rule 19 — the grain REPLACES the ISO-wide row). K=1/mask=all byte-identity is a
   REGRESSION TEST (`tests/unit/model/test_dispatch.py::TestRpsComplianceRegionRows::
   test_k1_all_zones_reproduces_legacy_row_byte_identical`, dyadic demand so RHS summation
   order is exact), with a masked contrast asserted non-vacuous.
4. **Dual recovery** (`model/lp/model.py`): K-slice at the same end anchor
   (`size − n_reserve − K`), mass-cap recovery counts the family size. `rps_shadow_price` stays
   a scalar float on the legacy path (type-asserted) and becomes the per-zone consumer vector
   `p[z] = max{dual_r : z ∈ eligible_zones(r)}` under the grain; the raw `(K,)`
   `rps_region_duals` ride `DispatchResult` and the parquet metadata (round-trip tested), and
   the runner logs the per-region duals per year.
5. **REQUIRED per-zone companion**: all three consumers — `new_entry.py` (both attribute
   sites) and `retirements.py` — resolve the credit at the candidate's/unit's zone via the ONE
   shared helper `policy.rps.rps_credit_for_zone` (scalar passes through; a vector indexes by
   zone; a vector with no zone context yields 0.0, never the broadcast max). The VRE candidate
   zone is the same `get_renewable_zone` target the shape-aware revenue screen already uses.
6. **Gate flag** `miso_rps_compliance_regions` (default OFF, forecast-mode, MISO-only arming in
   `runner.py`; the CES suppression covers the region rows identically), registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` IN THE SAME COMMIT
   (the nyiso-119 discipline). Armed key `50798fab664bac31` verified distinct; default key
   byte-stable.
7. **The MISO state-row table** `MISO_RPS_COMPLIANCE_REGIONS` (`config/capacity_market.py`,
   re-exported via the constants facade + completeness-test inventory): MN (West, .77,
   .26/.40/.55/.55, Midwest footprint), MI (East, .57, .35/.50/.60/.60, East ONLY —
   MCL 460.1029), WI (East, .43, flat .10, Midwest), IL (Illinois, 1.0, .25/.40/.50/.50,
   Illinois — the CEJA narrow reading, documented), MO (Plains, .43, flat .15, Midwest).
   Every number copied from the cited `STATE_RPS_FLOORS["MISO"]` derivation, none re-derived.
   **MT EXCLUDED** — the FFR-6B §1.4 ±.0345 bracket, recorded open (one EIA-861 line).
8. **Tests** (all passing): K=1 byte-identity + masked contrast; mutual-exclusion; per-row-ACP
   requirement (feasibility escape is not optional); the armed mask-binds toy (an
   East-restricted row Plains wind cannot satisfy escapes at its own $30 ACP, dual pinned at
   30, while the footprint row stays slack at 0; per-zone vector [0, 30] asserted); blend
   reproduction Σ rhs/demand ≈ .1139/.1606/.1981 at 2026/30/40 against the model's own zone
   load shares (`tests/unit/policy/test_rps.py::TestMisoComplianceRegions`); per-zone credit
   wiring (East candidate sees East's dual, South candidate 0; scalar pass-through; no-context
   degrades to 0); row-count year-invariance (layout/cache identity from the table alone);
   topology-drift KeyError; legacy scalar type contract; parquet round-trip.
9. **Measurement**: §3.

**E-1 NEVER ACQUIRES A BUILD LIMB** — stated in the gate-flag comment, the rows-builder
docstring and the constants table: the rows' only output is a price; a force-build limb would
stack against FFR-5E's procurement channel (the rule-19 failure FFR-5B refused). PJM/NEISO
zonal rows were NOT built (refused on structure, FFR-6B §7 — their matrix cells are `·`).

## 2. Arm 3 — what landed (commit `fa9b5da` range; ARMING BLOCKED)

Follows FFR-7B §6.2 + FFR-6B §6.3/§6.4:

* **A second, independent row family** on the Arm-2 machinery — `_build_rps_region_rows` with
  `acp_k0 = K_rps` (the clean escape columns occupy the region-major slots AFTER the RPS
  family's) and per-region qualifying generator columns via `_resolve_clean_region_gen_idx`,
  which ADMITS NUCLEAR (the deliberate difference from the renewable resolver's CX-6a refusal)
  and hard-errors on unknown names. Dual layout `[… | mass_cap | rps K1 | clean K2 | reserve]`.
  The clean family REQUIRES the Arm-2 family (refused loudly at the runner, the model and the
  assembler — FFR-6B §6.2: the dependency is strict and one-directional).
* **Rows**: MN carbon-free (§216B.1691 subd. 2g: 80/90/100% by 2030/35/40; qualifying =
  nuclear, hydro, wind, solar, hydrogen_ct, hydrogen_ccgt, biomass; Midwest-footprint
  eligibility) and MI clean (2023 PA 235: **80% by 2035** — the interim knot the old code
  comment missed — /100% by 2040; qualifying adds gas_cc_ccs; East-only eligibility).
  **Illinois: NO row — recorded null** in the `MISO_CLEAN_TIER_REGIONS` comment (CEJA is a
  source-side phase-out, not an LSE share obligation). Qualifying sets are per-statute DATA.
* **Trajectory convention**: ZERO before each statute's first knot
  (`policy.clean_tiers._clean_tier_target`) — deliberately NOT the RPS edge-hold, which would
  compel 80% carbon-free in 2026. Obligations reproduce the FFR-6B §6.2 adjudication table
  (West .616/.693/.770, East 0/.456/.570 at 2030/35/40 — tested to 3 places).
* **Feasibility escape**: every clean row carries its own escape column at the $30
  `STATE_RPS_ACP["MISO"]` proxy — REUSED AND DOCUMENTED (neither MN nor MI publishes a $/MWh
  clean buyout; compliance is physical with PUC/MPSC-set penalties), because a hard
  100%-by-2040 row is an infeasibility bomb.
* **Rule-19 composition (FFR-6B §6.4), implemented exactly**: the clean dual enters the
  EXISTING `max(eac, rps_shadow)` doctrine at all three capacity screens — the first LP row
  that pays nuclear/hydro at all — via `policy.clean_tiers.clean_credit_by_fuel` (runner-side
  mapping of the raw `(K2,)` duals) + `clean_credit_for_zone` (fuel- AND zone-resolved: a
  gas_cc_ccs unit in MISO-West earns nothing from MN's row, whose carbon-free definition
  excludes CCS gas — tested). `federal_ces_replaces_state_rps` suppresses the state clean rows
  too (same runner branch — under a pure-federal counterfactual neither family is built).
  **Wind-satisfies-both-rows is CORRECT and matrix-asserted**: the wind column carries +1 in
  both families' rows (two constraints, one MWh), with each family escaping through its OWN
  ACP slot (asserted per-slot); the generator's credit is `max()`, never the sum.
* **THE §45U COMPOSITION IS OPEN AND BLOCKS ARM 3's ARMING ONLY** (FFR-6B §6.4/§11, carried
  verbatim in cited comments on the `miso_clean_tier_rows` field and at the retirement-screen
  composition site): §45U(b)(2)'s gross-receipts phase-down implies phase-down-then-add, not
  `max()`. As implemented, §45U folds into `eac_price` by `max()` upstream, so the clean dual
  composes `max(max(eac, §45U), clean)` — the existing doctrine, documented as PROVISIONAL.
  The flag must not be armed in a keeper or forecast default until the owner resolves it;
  bounded default-off probe pairs are its only use.
* **Gate flag** `miso_clean_tier_rows` registered (cache-key + defaults ledger) IN THE SAME
  COMMIT; matrix row minted in the same PR; `--miso-clean-tier-rows` probe arm on
  `run_full_horizon.py`.
* **Tests** (all passing): clean-requires-rps refusal; nuclear satisfies the clean row (dual 0)
  and stripping nuclear from the qualifying set pins the dual at the $30 escape; the
  wind-in-both-rows + per-slot-ACP matrix assertions; unknown-fuel refusal; the FFR-6B §6.2
  obligation table; Illinois null; zero-before-first-knot; MI East-only; year-invariant row
  count; fuel-and-zone credit mapping (`tests/unit/policy/test_clean_tiers.py`,
  `tests/unit/model/test_dispatch.py::TestCleanTierRegionRows`).

## 3. Measurement — the bounded 2026–2030 MISO forecast pairs

**Protocol.** `run_full_horizon.py --iso MISO --start-year 2026 --end-year 2030
--golden-posture` (5 solve-years — the §2.1b schedulable cap, years sequential in one
invocation), three legs run SERIALLY on the 15 GB box (peak RSS ≈ 9.6 GB/leg, wall
≈ 62 min/leg): the shipped-default control, `--miso-rps-compliance-regions` (Arm 2), and
`--miso-rps-compliance-regions --miso-clean-tier-rows` (Arm 3 — its control IS the Arm-2
armed leg, §6). Cache keys distinct by construction and verified: control `0723d2cc432fa346`,
Arm-2 armed `ff144cd25848e4d8`. Registered to the FORECAST namespace only (rule 15's
forecast clause — `register_forecast_run.py --summary`, committed sidecars
`frontend/data/hindcast/miso-2026-2030-ffr7b2-rpsk-{ctrl,armed}.json` + the Arm-3 leg;
the backcast registry untouched). Q.2: this run-producing measurement is chartered
explicitly by D-22(a)/X.2 (the prompt orders the bounded pair).

### 3.1 Arm 2 pair — the grain is visible in exactly the right place, and nowhere else

Per-region duals (the armed leg's year-parquet metadata; $/MWh):

| year | MN | **MI** | WI | **IL** | MO | control ISO-wide dual |
|---|---|---|---|---|---|---|
| 2026 | 0 | **30.00** | 0 | 0 | 0 | 0 |
| 2027 | 0 | **30.00** | 0 | **30.00** | 0 | 0 |
| 2028 | 0 | **30.00** | 0 | **30.00** | 0 | 0 |
| 2029 | 0 | **30.00** | 0 | **30.00** | 0 | 30.00 |
| 2030 | 0 | **30.00** | 0 | **30.00** | 0 | 30.00 |

* **Michigan's in-state row pins at its ACP ceiling in EVERY year** — MCL 460.1029's
  restriction cannot be met from MISO-East generation, the 24.7 pp deficit FFR-6B §2.2
  measured, now live as a $30 REC price in that compliance market. **Illinois pins from
  2027.** The three delivery-based standards (MN/WI/MO — Midwest-footprint eligibility)
  stay slack at 0: Iowa/Plains wind covers them, which is real (those statutes DO accept
  regional certificates). The control's single ISO-wide row is slack until 2029 — the
  Iowa-surplus-pays-Michigan's-bill arithmetic the grain exists to fence off, reproduced
  exactly.
* **Per-zone consumer vector** `p[z]` (W/P/IL/IN/E/S): `[0, 0, 30, 0, 30, 0]` from 2027 —
  an East or Illinois candidate sees the REC signal; a South/Arkansas candidate sees 0.
  The control broadcasts its scalar (0 through 2028, then 30) to EVERY zone — including
  the 2029 5,650 MW **MISO-South** solar build, which the armed grain correctly credits
  NOTHING (South is outside every eligibility geography). The broadcast defect is
  therefore not hypothetical: the control paid an ineligible-zone candidate the ISO dual
  in both build years.
* **Dispatch, prices, builds and retirements are IDENTICAL across the pair** — lw_price
  38.08/38.11/38.45/39.99/46.90 $/MWh, VRE 39.0→49.0 GW, 2030 retirements 633 MW, all
  equal to the digit. Structural reading, pre-stated rather than discovered: the RPS
  row family re-prices *compliance* (which escape column absorbs the shortfall, and what
  a certificate is worth where) without moving *energy* (wind/solar dispatch at MC≈0 is
  already bound by CF×capacity in both arms), and the window's only VRE addition is an
  adequacy-backstop build (5,650.2 MW solar, MISO-South, identical in both arms — 
  adequacy-driven, not credit-driven, so removing the mis-broadcast credit moved no MW
  here). THE MECHANISM'S OUTPUT IS A PRICE (E-1's charter), and in this window that is
  exactly what it changed: where the REC price exists, and who may earn it. A window in
  which entry is margin-decided (not backstop/ladder-bound) is where the zonal credit
  will move MW; that is a later, owner-charterable measurement, not this one.
* I7 (accredited firm < requirement, 2026–27) and I12 (reserve-margin band WARN) fire
  identically in both legs — the known pre-existing MISO forecast conditions, untouched.

### 3.2 Arm 3 leg — clean-tier rows on top of the Arm-2 grain

<!-- ARM3_LEG_RESULTS -->

## 4. Byte-identity evidence (per arm)

* Pinned default cache key `603c2498bf71d21d` UNCHANGED with both fields present (asserted by
  the standing pin tests, run at the clean base first per the prompt's guard, and re-run after
  each registration); armed keys distinct (`50798fab664bac31` for Arm 2 alone).
* `check_cache_key_registration.py`: 145 registered fields, all resolve, all declared defaults
  match HEAD.
* K=1/mask=all → legacy row: identical matrix AND bounds (regression test, dyadic demand).
* Flag-off LP paths: the legacy scalar-row code path is UNTOUCHED when the region kwargs are
  absent (they are `UNSET`-omitted from the dispatch key set — the FFR-7B Arm 1 discipline),
  and the full non-MISO surface never constructs a region spec at all.
* Unarmed-vs-base solve-level byte-identity was NOT separately measured by paired replay: the
  off-path code is structurally unreached (same argument class as FFR-7B §3.3), the K=1
  identity is matrix-proven, and every keeper backcast sets `rps_enabled=False` so no backcast
  builds any RPS row. The 979-test model suite, the dispatch suite (92 tests incl. the new
  families) and the persisted-identity pins all pass at head.

## 5. What is deliberately NOT here

* **No Arm-3 arming, no keeper contact, no backcast contact**: both flags default OFF; every
  solve in this lane is forecast-mode 2026–2030; no backcast registry file was touched
  (rule 15's forecast-namespace clause — the backcast CI gates never learn these ids).
* **No per-region ACP refinement** (FFR-6B §3.4: a refinement, not a requirement — all five
  RPS regions and both clean rows carry the $30 MISO proxy).
* **No MT row** (the §1.4 bracket stays open as one EIA-861 line).
* **No PJM/NEISO zonal rows** (refused on structure, FFR-6B §7).
* **No capacity-screen REC-credit widening** (`_RPS_ELIGIBLE_FUELS`/`_RENEWABLE_NEW_FUELS`
  stay wind/solar — the FFR-7B §1.3 boundary; the clean family reaches nuclear/hydro through
  the attribute seam, not by widening the renewable screens).
* **No §45U composition decision** — named, cited, blocking arming only.

## 6. What I did NOT separate (stated per the charter)

* The Arm-2 and Arm-3 code shares one branch and one PR (`claude/ffr-7b-rps-arms-2-3-ygqgfc`),
  in strictly ordered commits (Arm 2 complete and pushed before any Arm-3 commit); the
  measurement pairs share the control leg (the Arm-3 pair's control IS the Arm-2 armed leg),
  so the Arm-3 delta is measured against Arm 2 armed, not against the shipped default — the
  two arms' effects are separable from the three registered runs, not from two independent
  pairs of four.
* `policy/rps.py` hosts both the RPS trajectory functions and the region machinery (one
  module, one interpolation helper); `policy/clean_tiers.py` is separate because its
  qualifying-set semantics (nuclear admitted) must never be importable as the renewable row's.

## 7. Rule discharges

Rules 2/3/4: vectorized builders (loop over K ≤ 6 only), renewables stay decision variables,
prices stay LP duals (each region dual IS a REC price). Rule 5/13: every constant is a
statutory level or a measured load share, copied from the cited derivation with citations in
the constants blocks. Rule 11: every new public function carries a docstring. Rule 19: one row
family per phenomenon — the K-row grain REPLACES the ISO-wide row (mutual exclusion enforced);
the clean family is separate from the renewable family by construction; attribute revenue is
`max()`, never a sum, at every consumer. Rule 22: no solve outside forecast-mode 2026+; freeze
never approached. Rule 24: the entire new tunable surface is two default-OFF gate flags plus
two cited statutory tables; both flags cache-key-registered with defaults declared in the same
commits. Rule 25: MISO-only arming; the four exact-row ISOs stay byte-identical; PJM/NEISO
refusals carried. Rule 27: all pushes over `git push` with exact on-disk bytes; remote tip +
per-file blob SHAs verified after every push (every ≥300-line file checked). Rule 28: both
matrix rows minted in the same PR as their fields; anchors repaired digits-only
(`--fix-anchors`); no cell verdict beyond `O` claimed. Q.2 (owner standing instruction):
the run-producing measurement here is chartered explicitly by D-22(a)/X.2 (the prompt orders
the bounded pair), supersedes nothing on the dashboard, and its findings are
mechanism-structural — a later keeper promotion re-points nothing in it.

## 8. Operational notes

* `git fetch --unshallow origin` FIRST in any session that must push from this container class
  (FFR-7B §5's relay bug reproduces otherwise).
* The ruff-autofix PostToolUse hook DELETES a just-added import whose uses land in a later
  edit (F401) — add usages first, import last, or in one edit. It bit this lane twice
  (runner.py, evolve.py), both caught by lint before commit.
* `scripts/regenerate_clean.py` completed 50/50 datatypes clean in this container (the FFR-7B
  §5 2/50-failure caveat did not reproduce).
* Two MISO 5-year forecast legs were run SERIALLY (the FFR-7B §3.1 15 GB OOM precedent).

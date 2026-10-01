# PRE-DECLARATION — capx D63: the MISO + CAISO curated DOF rows (owner ruling Q37 limb), and D62's suffixed board registration

**Lane:** capx D63. **ZERO LP** — no solve, no re-solve, no control. Records and one
committed table only.

**Charter:** capx director prompt pack §D63 (dispatched r#46 am.1) + **owner ruling Q37**
(capx ledger §3, r#34, rubric §5 second limb: *a follow-up lane may author an attestation
iff **PRE-DECLARED BEFORE AUTHORING**, attestation row only, artifact-only re-score*) +
`FINDING-capx-d60-2026-09-05.md` §8 (the six rows D60-R3 wrote, and the **two negatives it
routed here**) + `PREDECL-capx-d60-2026-09-05.md` **Addendum D** (the shape this
pre-declaration copies).

**This document is pushed BEFORE a single row is authored**, which is the whole content of
Q37's limb: D46 refused to author an instrument *after* reading that it failed a row, D60
leg 2 refused it again, and the limb exists so the fix can be taken in the honest order.

---

## §0. What is being repaired, stated once

FC-7's DOF-ledger row scores a ledger entry carrying the literal token `unattested`
**exactly as it scores a missing ledger** — CAVEAT at t1, FAIL at t3
(`scripts/forecast_verdict.py::_dof_ledger_row`).
`scripts/build_forecast_dof_ledger.py` emits that token for any non-default solve-affecting
field with **no curated identification row**, and it *reports* identification, never supplies
it (rule 21 `[R-DOF]`). So a field whose identification is **already committed to the
repository**, armed without its curated row, mechanically degrades FC-7 — a **measurement
gap, not a model gap**. D60-R3 closed six such gaps and **routed two blunt negatives**
(D60 §8): MISO's five remaining registry overrides and CAISO's one. Those two negatives are
this lane's entire object.

**What this lane may NOT do**, stated before it starts: it may not arm anything, change any
`ScenarioConfig` field or value, re-solve anything, edit a verdict by hand, or widen its own
scope to make a row read PASS. A field whose identification cannot be cited from a
**committed** document gets **NO row** — it stays UNIDENTIFIED and this document says why.

---

## §1. THE SCOPE IS SIX FIELDS, NOT SEVEN — measured from the committed ledgers

The charter names *"the SEVEN fields"* and then enumerates six by name plus *"any other
`unattested` entry the committed `miso-t1f` / `caiso-t1f` `dof_ledger.json` carries"*.
**There is no seventh.** Measured, before any row was written, from the two committed
artifacts:

| bundle | ledger | entries | UNIDENTIFIED (`unattested`) |
|---|---|---|---|
| `miso-t1f` | `results/ff-t1f-d60/miso/dof_ledger.json` | 7 | **5** — `entry_vre_capacity_revenue`, `entry_vre_zone_selection`, `miso_clean_tier_rows`, `miso_rps_compliance_regions`, `retirement_sector_gate` |
| `caiso-t1f` | `results/ff-t1f-d60/caiso/dof_ledger.json` | 2 | **1** — `negative_renewable_offers` |

The identified remainder is already curated: MISO's `adequacy_accounting_ratio_dated_net`
(D60-R3's row) and `forecast_xyear_warmstart` on both (the D-10 posture row). **Six rows
are owed; six are declared below.** The count deviation from the charter's "seven" is
recorded here rather than silently reconciled.

Every one of the six carries `provenance: "iso-registry"` in the committed ledger, i.e. the
**mechanical registry match already succeeded** for each — which is the gate every row below
requires.

---

## §2. THE SIX ROWS, EXACTLY AS THEY WILL BE WRITTEN

All six go in **`CURATED_IDENTIFICATIONS` in `scripts/build_forecast_dof_ledger.py`** — the
capx-D8 / D8-V instrument, the same committed, reviewed surface D50's, D52's and D60-R3's
rows live in. **No `run_config`, no solve, no verdict edited by hand.**

Every row is keyed **`(ISO, field)`** — never `("*", field)` — so it is **rule 25
`[R-ISO-SCOPE]`-scoped by construction**: it cannot identify another ISO's value even if that
ISO later arms the same field. Every row carries **`requires: "iso-registry"`**, so the
builder applies it **only** when the run's value byte-matches the live registered override; a
run carrying the field from anywhere else stays UNIDENTIFIED and the artifact records the
refusal.

Every one of the six values is a **boolean `True`**, so the builder's magnitude guard
(`design-decision` may never identify a numeric magnitude) is satisfied for all six by
construction, and no row identifies a number.

| # | key | ident. | source — what identifies the value | committed evidence | rule 13: regenerates forward? | rule 21 DOF |
|---|---|---|---|---|---|---|
| 1 | `("MISO", "entry_vre_capacity_revenue")` | `design-decision` | **Owner decision D-2′** (owner sitting Addendum O, signed 2026-08-04; lane FFR-4B). MISO's Planning Resource Auction **accredits and pays** wind and solar like any other Planning Resource, so a MISO forecast that denies VRE entry the RA payment is not modelling MISO's market. Before it, VRE was the only accredited class on the system denied that payment while thermal entry, the thermal retirement screen and storage entry all took it through the **same** seam (`MarketDesign.capacity_price_per_firm_mw_yr`) — and VRE's accredited MW were already on the supply side of the adequacy ledger. Arming removes an exception; it adds no second channel (rule 19 `[R-ONE-MECH]`). | `src/market_sim/config/iso_configs.py::_miso_config` `default_scenario_overrides` cite block; `docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md` §3.3 / §7 item 1a | **Yes.** The payment is the ISO's own published auction accreditation, read through the existing price seam in any forward year; it responds to a changed fleet and a changed clearing price by construction. | **Zero.** A one-bit exception removal — no MW, no price and no share is chosen. |
| 2 | `("MISO", "entry_vre_zone_selection")` | `design-decision` | **capx D33.** MISO is the ISO where single-bucket VRE siting is not merely coarse but **wrong in kind**: `RENEWABLE_ZONE_ALLOCATION` sent every economically-entered solar MW to MISO-South, the one model zone excluded from every state compliance region's eligible-zone mask (`MISO_RPS_MIDWEST_FOOTPRINT_ZONES` — AR/LA/MS/E-TX carry no standard), so the screen priced new solar at a $0 REC credit while the run's own zonal REC vector peaked at the $30/MWh ACP. A siting-representation repair, not a level. | `_miso_config` cite block; `docs/handoffs/FINDING-capx-d33-miso-additions-repair-2026-09-02.md` §2 | **Yes.** The selection reads the run's own zonal REC vector and eligible-zone masks in whatever year it runs; nothing is fixed to a measured outcome. | **Zero.** A selector over existing zones and existing masks; no share or allocation weight is chosen. |
| 3 | `("MISO", "miso_rps_compliance_regions")` | `design-decision` | **Owner decision D-26** (sitting Addendum Y.4, signed 2026-08-06; lane ARM-MISO). The single MISO-wide RPS row silently asserts **free intra-ISO REC trade**, which is FALSE in MISO (MCL 460.1029 restricts Michigan credits to in-state systems; CEJA's centralized IPA procurement; MN's delivered-to-retail construction) — the ISO-wide row let Iowa's surplus pay Michigan's bill. Armed, that row is **replaced** (rule 19, never stacked) by K=5 per-state compliance-region rows, each with its statute's eligibility mask, obligated-load RHS and its own $30 ACP escape. | `_miso_config` cite block (owner ruling D-26); `docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md` §3.1; both lane gates proven by `tests/unit/config/test_miso_rps_region_arming.py` | **Yes.** Every obligation is copied from the cited `STATE_RPS_FLOORS["MISO"]` derivation, which regenerates from statute and obligated load for any forward year and responds to a changed fleet through the LP dual. | **Zero fitted parameters** — every obligation is a statutory quantity; the row's only output is a price. |
| 4 | `("MISO", "miso_clean_tier_rows")` | `design-decision` | **Owner decision D-29** (sitting Addendum AK.8, signed 2026-08-11; lane ARM-3-ARM). Adds a **second independent** row family riding the Arm-2 K-row machinery (the dependency is strict and one-directional; the runner refuses the clean family without the compliance-region grain): MN carbon-free (Minn. Stat. §216B.1691 subd. 2g) and MI clean (2023 PA 235 / MCL 460.1029), each with its statute's eligibility mask, obligated-load RHS and its own $30 ACP escape. Both blockers are closed on the record — the §45U composition by owner D-28 option A, and the zone-mask defect by ARM3-FIX. | `_miso_config` cite block (owner ruling D-29); `docs/handoffs/arm3-fix-zone-mask-2026-08-09.md` §4 (R1–R5 on the fixed rows) | **Yes.** Every obligation is copied from the cited `MISO_CLEAN_TIER_REGIONS` derivation; MI's RHS is 0 until its statutory 2035 start and binds thereafter, which is a forward-native construction, not an extrapolated fit. | **Zero fitted parameters** — statutory obligations only; capacity events are identical to the digit in the measured pair, the row's only output being a price. |
| 5 | `("MISO", "retirement_sector_gate")` | `design-decision` | **capx D53**, armed for MISO ONLY by owner instruction on the measured A/B. A **pure candidate-set partition** of the retirement screen: 59 GW of regulated-utility capacity whose owners never subject it to a merchant test is removed from a merchant screen, so the pool the reliability floor masks is the merchant pool (10 % real-exit density instead of 4 %) and the floor's release lands at plants that actually exit (99.8 % plant-grain precision instead of 1.1 %). All four pre-stated limbs read MET. | `_miso_config` `default_scenario_overrides` `retirement_sector_gate` cite block; `docs/handoffs/FINDING-capx-d53-2026-09-05.md` §6 (the four limbs) and §6.1 (the arming, and its records-side consequences) | **Yes.** The partition reads the `Sector` column every ISO's EIA-860 plant table already carries, for whatever fleet the forecast year holds — the same posture class as ruling Q30's date channel. | **Zero.** A partition of the candidate set; no threshold, share or MW is chosen, and every retirement row was measured byte-identical on the bare recipe. |
| 6 | `("CAISO", "negative_renewable_offers")` | `design-decision` | The representation of **CAISO's actual renewable offer conduct**: California renewables bid **below $0** in oversupply to keep producing for their RPS/REC and federal-PTC value, so in the spring-midday solar glut the marginal (curtailed) unit clears negative (measured 2024 RT `da_pct`: p5 −$10, p1 −$24, min −$41). The model's wind/solar are availability-capped LP slices carrying a $0 (solar) or −PTC (wind) offer that are never marginal, so without it the model floors at $0. The gate is CAISO's by the **ERCOT-65 rule-25 adjudication** recorded in the same registry block, and it carries **no magnitude**: the floor level lives in the separate field `renewable_keep_running_value`, which this run holds at its shipped default and which therefore is not an entry of this ledger. | `src/market_sim/config/scenarios.py::negative_renewable_offers` + `renewable_keep_running_value` cite blocks (CA RPS PCC1 REC $10–25/MWh; federal §45 wind PTC ≈ $28/MWh; the ERCOT-65 rule-25 scope ruling); `src/market_sim/config/iso_configs.py::_caiso_config` `default_scenario_overrides` cite block; mechanism `policy.eac.apply_negative_renewable_offer_floor`, tested `tests/test_negative_renewable_offers.py`; **the CAISO backcast keeper record** — keeper `2026-09-05-caiso-252-b1-notrim` carries `negative_renewable_offers: True` at `renewable_keep_running_value: 20.0` in its committed `results/calibration/caiso252_b1_notrim/run_config.json`, and the CAISO mechanism-matrix cell reads **`K`** on the caiso-216 measurement (`FINDING-caiso216-belly-lever-plan-2026-08-23.md`, `_caiso216_belly_surplus.json` B3) | **Yes.** The conduct it represents is a standing property of an RPS/PTC-supported fleet in oversupply, and the offer is computed from the run's own credits in whatever year it runs; nothing is pinned to a measured price or volume. | **Zero** *for this entry*: the gate is a boolean and identifies no number. The **level** ($20/MWh) is a separate registered field at its shipped default with its own cited identification, outside this ledger's non-default scope. |

**Why `design-decision` and not `published` for all six.** Every value here is a **boolean
gate** selecting *which representation* the model uses — an accreditation payment, a siting
resolver, a compliance grain, a screen partition, an offer floor. None is a magnitude read
off a document, which is what `published` means in this taxonomy. `design-decision` is the
token the builder admits for exactly that, and only for non-magnitude values; the builder
refuses it on a number and would refuse it here if any of the six ever carried one.

---

## §3. THE EXPECTED READINGS — pre-declared, before the rows exist

Computed from the two committed ledgers and the two committed verdicts, which are already
public in `FINDING-capx-d60-2026-09-05.md` §8 and §8.2 (so nothing here is read for the first
time after the fact).

| bare key | ledger today | ledger after the six rows | FC-7 now | FC-7 after | caveats now | caveats after | determination now → after |
|---|---|---|---|---|---|---|---|
| `miso-t1f` | 7 entries, **5 unattested** | 7 entries, **7 identified / 0 unattested** | **CAVEAT** | **PASS** | `FC-7 provenance & DOF`, `FC-8 runtime feasibility: over runtime budget` | `FC-8 runtime feasibility: over runtime budget` | **HOLD → HOLD** |
| `caiso-t1f` | 2 entries, **1 unattested** | 2 entries, **2 identified / 0 unattested** | **CAVEAT** | **PASS** | `FC-7 provenance & DOF` | *(none)* | **HOLD → HOLD** |

**Neither determination moves, and that is the pre-declaration, not a hope.** Both runs read
HOLD on `FC-1 structural integrity (I1-I14) FAIL` + `FC-2 adequacy & equilibrium behavior
FAIL`, and a caveat retiring cannot clear a *reason*. MISO's FC-1 keeps `['I12','I7']`;
CAISO's keeps `['I12','I7']`. **This lane closes a measurement gap and moves no model
result.** If either determination moves, that is §4's STOP.

Board (`frontend/data/forecast/program-status.json`) after the re-scores:

| ISO row | `fc["FC-7"]` | `t1f_determination` |
|---|---|---|
| MISO | `CAVEAT` → **`PASS`** | `HOLD` → `HOLD` (unchanged) |
| CAISO | `CAVEAT` → **`PASS`** | `HOLD` → `HOLD` (unchanged) |

Nothing else on either row is touched, and **no other ISO's row is touched at all** — the six
rows are keyed to MISO and CAISO and cannot reach NYISO, PJM, NEISO or ERCOT.

---

## §4. FC-7 IS THE ONLY ROW THAT MAY MOVE — anything else is a STOP

A `CURATED_IDENTIFICATIONS` row is read by **one consumer**,
`build_forecast_dof_ledger._apply_curation`, and it can set only an entry's
`identification` / `status` / `source` / `evidence` / `provenance`. It **cannot** reach a
`ScenarioConfig` field, a cache key, a solve, a trajectory, an invariant or any other FC
category. So the re-scores of §5 step 3 are **artifact-only in the strict sense**: same
bundle, same bytes, same cache key, a re-run of `forecast_verdict.py --tier t1f` over a ledger
whose *labels* changed.

**Therefore: FC-7 is the only row that may move.** If any other row moves — any FC-1
invariant, FC-2, FC-3, FC-4, FC-5, FC-6, FC-8, or a determination changing for any reason
other than FC-7's own status — that is a **model effect these rows cannot own**, and it is
**STOP-and-report**: reported at full magnitude, escalated, **not registered**. Measured
row-by-row across all eight categories of both bundles, with a control reproduction of each
committed verdict from the committed artifacts run **first**, so the ledger input is provably
the only delta (the capx-D8-RE / D60-R3 protocol).

**STOP D63-1** — any non-FC-7 row moves on either bundle.
**STOP D63-2** — either determination moves.
**STOP D63-3** — a curated row is **REFUSED** by its own gate (`curation_refused` present on
any of the six entries), i.e. the registry match this pre-declaration asserts does not hold.
**STOP D63-4** — the re-score changes a bundle's cache key, `run_config`, or any
scorer-derived field outside FC-7.
**STOP D63-5** — the board write collides with a live D60-R4 write (see §6).

---

## §5. D62's SUFFIXED REGISTRATION — pre-declared

The second half of the charter: register capx D62's arm on the forecast board **suffixed**,
which D62 withheld behind D60-R3's ownership of `ff-verdicts.json`.

* **Key:** `pjm-t1h-d62-pubbar`. **The bare `pjm-t1h` is UNTOUCHED** — it stays D57 arm A
  (`f0e050e820c1159a`), which is this arm's own control.
* **Already committed and requiring no change:** the hindcast sidecar
  `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar.json`, the bundle
  `results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/`, and the `VERDICT_MAP` row
  `"pjm-2021-2025-realized-t1h-d62-pubbar": "pjm-t1h-d62-pubbar"` in
  `scripts/register_forecast_run.py`. The run is also already in the Y-24
  `registration_ratchet_baseline` (`frontend/data/hindcast/invariant-failures.json`), so the
  invariant-declaration gate is satisfied for it and **this lane declares no invariant
  failure and adjudicates none**.
* **What is missing and what this lane adds:** the `ff-verdicts.json` entry for that key —
  the FF-2D verdict snapshot the generated registry sidecar and run payload bake from.
* **How the verdict is produced:** `scripts/forecast_verdict.py --tier t1h` on the bundle's
  **committed** artifacts (`--hindcast-score .../PJM/b98060898fceb3da/score.json`,
  `--run-config .../run_config.json`), the same invocation that reproduces D57's committed
  `forecast_verdict.json` — verified by reproducing D57's committed verdict **first**, before
  D62's is written. **No solve, no re-score of any other key.**
* **Pre-declared reading:** determination **HOLD**, on `FC-3 capacity-evolution skill (T1-H
  hindcast) FAIL` — D62 §5.4 measures `retire.total_gw` 18.702 → 20.144 against an actual
  15.062 and unit recall 0.60 → 0.55, both worse than the control, and FC-3 is the gating
  category at t1h. FC-7 expected CAVEAT (the bundle carries no DOF ledger). FC-1 / FC-8
  expected SKIPPED (no committed invariant record, no perf ledger), as on D57.
* **Provenance string:** **D62's own verdict text**, not this lane's. The note carries D62
  §8's verdict verbatim in substance — **DO-NOT-ARM as it stands**, its own pre-registered
  **STOP 5 FIRED** (the 2024/25 price moved 165.84 → 188.57 $/MW-day, through the census
  rather than the offer side), FC-3 worse where it already failed, and 4.137 GW of oil
  over-exiting — set against what the measurement does establish (2022/23 clearing price
  1.522× → **0.936×** the published RCP at a cleared position −0.477 → **+0.267** pt, at
  **zero free parameters**, with `additions.gas_cc` FAIL → PASS). **NOTHING ARMS**: no
  `_pjm_config` override, no default flip, no `ScenarioConfig` change of any kind.
* **What registering it does NOT do:** it does not promote D62, does not move PJM's
  `t1h_determination` or any board gate row, and does not touch the bare `pjm-t1h`. If any of
  those moves, that is **STOP D63-2** applied to PJM.

---

## §6. ORDER, AND THE D60-R4 COLLISION

**D60-R4 is the sole writer of `ff-verdicts.json` / `program-status.json` until its PR
merges** (charter). State at this lane's start, measured with `git fetch origin --prune`:

* D60-R4's commits are on `origin/main` (`5d639e31`, `fc8e2921`, `f4ebc611`, via merged PRs
  #5093 and #5097) and **no `claude/capx-d60r4-*` branch exists on origin**.
* **But D60-R4 is not finished**: its `Addendum E.4 — The control's result` is committed
  **empty** ("*Written after the solve; empty at pre-declaration time*"), so its earned
  control solve is outstanding and a further push from it is possible.

**Therefore this lane treats D60-R4 as LIVE and takes the charter's conservative branch:**

1. **Step 1** — this pre-declaration, pushed first, before any row exists. *(No board file
   touched.)*
2. **Step 2** — the six rows in `CURATED_IDENTIFICATIONS` + the extended test module, pushed.
   *(No board file touched.)*
3. **Re-check `origin/main` for a D60-R4 board write**, and **rebase between (never during)
   steps**.
4. **Step 3** — the two artifact-only re-scores and D62's registration, which are the only
   commits that write `ff-verdicts.json` / `program-status.json`. If a D60-R4 write lands in
   between, this lane rebases onto it and re-runs the re-scores at that HEAD rather than
   merging two snapshots by hand.

Its control bundle is registered **nowhere** by its own §E.3 ("*registered NOWHERE, and its
bundle is deleted before the PR merges*"), so the collision surface is its board **provenance
text**, not a verdict key this lane writes. The two lanes' keys are disjoint in any case:
D60-R4 reads PJM `t1f` and NEISO `t3`; D63 writes MISO `t1f`, CAISO `t1f` and the new PJM
`t1h-d62-pubbar`.

---

## §7. GOVERNANCE

* **Rule 21 `[R-DOF]`** — the ledger REPORTS identification and never supplies one. Every
  row above cites a document **already committed** before this lane opened; **no value is
  chosen here**, and all six values are booleans, so no row identifies a magnitude. A field
  whose identification could not be cited would get **no row** — and this lane found none such
  among the six.
* **Rule 22 `[R-HOLDOUT]`** — no out-of-training year is solved, scored or registered. The
  two re-scored bundles are 2026–2030 forecast-mode runs; D62's is a 2021–2025 realized
  hindcast. No marker, no freeze, no tier is read or written.
* **Rule 24 `[R-REGISTRY]`** — no tunable is added, moved or renamed;
  `CURATED_IDENTIFICATIONS` is a **reporting** table read by one consumer and cannot change a
  solve.
* **Rule 25 `[R-ISO-SCOPE]`** — every row is keyed `(ISO, field)`, **never** `("*", field)`.
  MISO's five rows cannot identify a CAISO value and CAISO's cannot identify a MISO one;
  asserted by test.
* **Rule 27 `[R-PUSH]`** — `scripts/build_forecast_dof_ledger.py` (1,158 lines),
  `frontend/data/forecast/ff-verdicts.json` and `program-status.json` are edited **locally**
  and pushed as the exact on-disk bytes, with a **blob verification** after each push.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell moves.** This lane tests no mechanism, proposes
  no lever and adds no `ScenarioConfig` field. Nothing in the matrix is touched.
* **Rule 29 `[R-SCREEN]`** — not applicable: zero LP, no arm, no screen, no control solve.

---

*capx D63 · 2026-09-06 · pre-declared before authoring, per owner ruling Q37.*

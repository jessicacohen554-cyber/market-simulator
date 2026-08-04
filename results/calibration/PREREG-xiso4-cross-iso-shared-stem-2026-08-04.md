# PREREG — xiso-4: the CROSS-ISO SHARED-STEM rule-28(c) backlog

**Date:** 2026-08-04 · **Lane:** cross-ISO hygiene (`xiso-1/2/3` predecessors) ·
**Base:** `origin/main` @ `d7363b0e` · **Branch:** `claude/cross-iso-shared-stem-backlog-s4sn78`

**Written and committed BEFORE any matrix byte was written.** Nothing below is retro-fitted.

> **SUPERSEDED IN FLIGHT — READ THIS FIRST, AND READ THE REST AS WHAT IT NOW IS.**
> While this pre-registration was being written against `origin/main` @ `d7363b0e`, a
> **concurrent session, `xiso-3`, closed the identical backlog** and merged to main
> (`de247065`, PR #3442/#3444; main moved `d7363b0e` → `fe90fb8f` mid-session, discovered on
> the first push). **This session therefore executed NO registration** — every one of the 46
> fields was already registered when its first push attempt landed.
>
> The document is kept, unedited below this note, for the one thing it is now good for:
> it is the **timestamped record that the §5 registration map was derived independently**,
> from the code, before its author had seen xiso-3's. That is what makes the 43-of-46
> agreement in `FINDING-xiso4-cross-iso-shared-stem-2026-08-04.md` §2 a real cross-check
> rather than a restatement. Read §5 as an independently-derived comparison map, §6/§7 as
> criteria scored against **xiso-3's** work rather than this session's, and the whole as
> verification — **not** as a claim that this session closed anything. It did not.
>
> Two numbers below are wrong and are corrected rather than edited away: §1/§7 say **seven**
> fields are armed on two keepers at once (§5's own table lists all of them, and xiso-3
> counts **nine** — the three `ct_drag_*` scalars were collapsed to one line in the prose but
> not in the table), and §5's `coal_lignite_passthrough_sigmoid` is declared here as a "+1
> adjacent addition" when xiso-3 had already registered it. xiso-3's counts are the correct
> ones.

**Keepers at this HEAD, read from the shards, ALL UNCHANGED by this session:**
ERCOT `2026-08-03-ercot158-pool-arm` · CAISO `2026-08-04-caiso164-zonal-loss-surface` ·
PJM `2026-08-03-pjm-151-seam-envelope` · MISO `2026-08-04-miso-124-dualfuel-rearm` ·
NYISO `2026-08-03-nyiso-119-seny-increment` · NEISO `2026-08-03-neiso-caiso156-meter-screen`.
`complete` = {NEISO, NYISO, PJM}; `final` = EMPTY; **holdout spend freeze ACTIVE.**

> The handoff quoted MISO's keeper as `2026-08-04-miso-122b-scope-gate` (nyiso-121's
> contemporaneous value). At this HEAD the MISO shard reads
> `2026-08-04-miso-124-dualfuel-rearm`. Re-read, not assumed; the census keys on the
> shard, so every MISO count below is against miso-124.

---

## §1 — the measured backlog AT THIS HEAD (re-swept, not inherited)

`scripts/mechanism_matrix_gap_sweep.py`, all six ISOs, run at `d7363b0e`. The committed
sweeps predated this HEAD by 62 commits and were regenerated rather than trusted.

| ISO | family | absent | prose-only | armed-no-cell | **shared-gap** | live-but-invisible |
|---|---|---|---|---|---|---|
| ERCOT | 86 | 0 | 0 | 0 | **14** | 12 |
| CAISO | 62 | 0 | 0 | 0 | **5** | 1 |
| PJM | 35 | 0 | 0 | 0 | **18** | 0 |
| MISO | 25 | 0 | 0 | 0 | **17** | 12 |
| NYISO | 41 | 0 | 0 | 0 | **0** | 0 |
| NEISO | 20 | 0 | 0 | 0 | **0** | 0 |

**Every own-family column is confirmed closed at HEAD** (ercot-156 / caiso-161 / pjm-151 /
neiso-78 / nyiso-113+121). The shared-stem counts are **byte-identical to the handoff's**
(PJM 18, MISO 17, ERCOT 14, CAISO 5) — 62 commits moved neither.

**45 DISTINCT shared fields**, overlapping across ISOs. Seven are armed on **two** keepers
at once; the rest on one. The machine-readable list is
`results/calibration/_matrix_gap_sweep_<ISO>.json`, regenerated in this session's first
commit — **it, not this document and not any row's prose, is the census of record.**

## §2 — the method, and why it is registration-on-rows and NOT prose

nyiso-121 FINDING §6.2 measured the failure mode this lane must not repeat: **naming a
shared field as a bare literal inside a row's `note:` makes the sweep count it
`prose_only` — "mentioned", never registered — and it LEAKS ACROSS COLUMNS**, dropping the
field from *both* arming ISOs' lists on one lane's prose (ERCOT silently went 12 → 11).

The mechanism is in `mechanism_matrix_gap_sweep.coverage()`: a field reads `own_row` only
if its **literal name appears in the row body BEFORE the `note:` key**. So:

* **REGISTER** = the literal field name as a sub-scalar entry in an existing family row's
  **`def:`** (the nyiso-114 escape-hatch template, as used by neiso-78, caiso-161 and
  nyiso-121). This is the only thing that clears the gap.
* **DO NOT ENUMERATE** the 45 literals in the `matrix_gap_census` note, in any other row's
  `note:`, or anywhere else in `mechanism-matrix.js` prose. The census row gets a **count
  plus a pointer to the sweep JSON**, per nyiso-121's own correction to its precedent.
* Naming them in **this markdown** is safe and deliberate — `.md` files are not scanned by
  the sweep. The traceable list lives here and in the JSON; the matrix carries the
  registrations.

**Home-row test (binding): CODE-LEVEL MECHANISM OWNERSHIP, never theme.** Each field's home
is the row whose mechanism its consumer actually implements or gates, cited by call site.
This is the guard against the caiso-161 §2 defect's newest variant (nyiso-121 §4):
`miso_manitoba_seam` was prose inside `diagnostics_plant_set`, *a row about probe plant
sets* — a mention on the WRONG family row **reads as correct coverage to a human** and is
as invisible as no mention.

## §3 — kill rules (a breach of any is visible in the diff)

* **K-1 — MINT NO MECHANISM VERDICT.** Not one of the 183 rows' 6-char `cells:` strings may
  change. Zero, including the `matrix_gap_census` audit row: NEISO's `O` there is NEISO's
  lane's call (nyiso-121 §6.1, rules 25 / 28(d)), and this lane inherits that restraint.
  **This is stricter than every predecessor closure, each of which minted one audit cell.**
* **K-2 — TRANSCRIPTION ONLY.** Every verdict-bearing sentence added must restate an
  adjudication **already on the record**, with its citation (keeper DOF ledger entry,
  calibration-log entry, FINDING, or the row's own existing note). No new judgment.
* **K-3 — an armed field with NO adjudication anywhere is a FINDING, not a cell.** If a
  field is armed on a keeper and the record carries no identification for it, it is
  reported as a live-but-invisible lever and left `U`-equivalent; the census does not
  manufacture its verdict.
* **K-4 — NO VERDICT CROSSES AN ISO BOUNDARY (rule 25 / duty d).** A shared *stem* is not a
  shared *verdict*. For every field armed in two ISOs, **both** ISOs' adjudications are
  transcribed separately with separate citations, or the un-evidenced ISO is reported under
  K-3.
* **K-5 — NO SOLVE, NO MECHANISM CHANGE.** No LP is built. No `ScenarioConfig` default,
  band, keeper, derive script or `backcast_config` value is touched. No year outside
  2023–2025 is solved, scored or read; the holdout freeze is respected trivially because
  nothing is solved at all. **This lane needs no LP: every claim is decidable from
  committed configs, the matrix source, and the code's own gate structure.**
* **K-6 — NO ROW DELETIONS, NO NEW ROWS.** Registration is additive into existing `def:`
  fields. (Rule 26 `[R-DELETE]` candidates, if any surface, are *reported*, not executed —
  removing a field is a mechanism change a census may not make.)

## §4 — declared scope, stated exactly so it cannot be quietly widened

**IN:** the **45** shared (non-ISO-prefixed) `ScenarioConfig` fields that some ISO's
**designated keeper** arms away from its shipped default while no matrix row carries their
literal — i.e. `shared_matrix_gaps_absent + shared_prose_only` in the six committed sweeps.

**PLUS ONE declared adjacent addition, +1 = 46:** `coal_lignite_passthrough_sigmoid` —
non-default in 11 ERCOT bundles but **False on the ERCOT keeper**, so the keeper-keyed
shared census does not see it, while the broader `live_but_invisible` view does. It is the
literal sibling of two fields already being registered on the same row. Registering it
costs one identifier and closes a real gap; declaring it here keeps the count honest.

**OUT, reported not registered** (each with its reason, in the FINDING):

* `retirement_years_coal`, `federal_ces_ccs_capture_fraction`, `coal_bit_committed_takeorpay`
  — non-default in 1–3 *probe* bundles, armed on **no** keeper. Outside the
  armed-on-a-keeper boundary this lane declares.
* `forecast_xyear_warmstart` (CAISO's single live-but-invisible slot) — same reason.
* `ercot_gas_commitment_bridge` — an **ISO-stem** field, already `own_row` via the
  stem-aware family census (row `gas_commitment_bridge`); it appears in
  `live_but_invisible` only because that metric's literal-match leg is stem-blind. A known
  metric asymmetry, not a gap. Not this lane's (and not a gap in any lane's).

## §5 — the registration map, fixed BEFORE editing: 46 fields → 18 EXISTING rows → 0 new rows

Each home cited by consumer call site. `[E C P M N Q]` = the row's existing cells.

| # | home row | cells | fields registered (arming ISO) | code-level ownership |
|---|---|---|---|---|
| 1 | `coal_passthrough_sigmoids` | `KKKRK.` | `coal_prb_passthrough_floor`, `coal_prb_follower_floor`, `coal_lignite_passthrough_floor`, `coal_lignite_passthrough_ceil`, `coal_lignite_passthrough_sigmoid` (E); `coal_bit_passthrough_sigmoid`, `coal_bit_passthrough_floor`, `coal_sub_passthrough_sigmoid`, `coal_sub_passthrough_floor` (P) | all are `COAL_SIGMOID_DEFAULTS` supply-key tiers of this row's own mechanism (`scenarios.py:5900-5932`, `:6432-6433`; follower tier `:5906-5915`) |
| 2 | `netload_drag_floors` | `KRKURU` | `gas_st_drag_seasonal` (E); `ct_drag_cap`/`_intercept`/`_slope_per_gw` (C, P); `gas_st_drag_cap`/`_intercept`/`_slope_per_gw` (P) | the curve coefficients read by `data/fleet/floors.py:324-326, 389-391` inside this row's two appliers |
| 3 | `wefor_statistical_stack` | `KKKKKK` | `wefor_residual` (E, P), `wefor_residual_groups` (E), `gas_st_wefor_base_override` (M) | the residual cap + its group scope + the ST_GAS base of this row's WEFOR stack (`data/fleet/arrays.py:609-615`) |
| 4 | `offer_curve_by_group` | `KKKKKK` | `ct_intermediate_split` (P, M), `ct_intermediate_cf_threshold` (P), `cc_intermediate_split` (M), `st_gas_intermediate_split` (M), `offer_curve_smoothing_mid` (E, P), `cc_outage_derate_from_top` (C, P) | the splits re-route a cohort between this row's named curves (`data/offer_curves.py:289`); smoothing is its econ-ramp shape (`fleet/assembly.py:663`); the derate re-fills the same tranches in heat-rate order (`fleet/arrays.py:1786`) |
| 5 | `p1_bidcost_pass` | `KKKKKK` | `gas_st_startup_cost` (E, M), `coal_warm_committed` (M) | both are class-scope gates in the SAME `model/commitment.py` markup loop this row is defined by (`:302`, `:312`) |
| 6 | `tranche_startup_amortization` | `GGKKKK` | `tranche_startup_conditional_runs` (P, M) | the v4 condition-keyed horizon of this row's own amortization (requires its v3 leg) |
| 7 | `temp_dependent_derate` | `UKRKGK` | `temp_derate_classes`, `_hourly_grain`, `_mean_anchored`, `_slope_ct_chp`, `_slope_st_chp` (M) | the scope, input grain, anchor and slopes of this row's curve |
| 8 | `st_gas_mustrun_p25` | `..UKIU` | `st_gas_mustrun_p25_level` (M) | the row's own level leg; def carries only the abbreviation `p25 level :6513` |
| 9 | `chp_steam_following` | `KKKKKK` | `chp_export_floor_measured` (E), `chp_steam_floor_p25` (C) | both set this row's `pmin_cf`; def carries only `(+export_floor_measured, steam_floor_p25)` |
| 10 | `coal_takeorpay_committed` | `...K..` | `coal_takeorpay_from_data` (M) | the row's own from-data leg; def carries only `_from_data :4880` |
| 11 | `coal_mustrun_per_plant` | `KKKKKK` | `coal_mustrun_online_pmin` (P), `coal_sync_srmc_tranche` (P) | steps 2 and 3a of the SAME per-plant coal must-run rebuild; the sync tranche **requires** the online-Pmin flag |
| 12 | `cc_nameplate_summer_derate` | `UUUUKU` | `coal_nameplate_summer_derate` (E) | `fleet/arrays.py:762` calls it, in its own comment, "the coal analogue of the CC/CT `cc_nameplate_summer_derate`" |
| 13 | `dual_fuel_switching` | `U.KKKK` | `oil_primary_bin_fuel` (E) | the oil-primary complement of `fleet.dual_fuel_plant_groups`, which excludes these units *because* they are already oil (`fleet/assembly.py:200`) |
| 14 | `gas_monthly_actuals` | `GKK.KK` | `gas_hh_monthly_shape` (E) | the monthly-gas family's SHAPE leg beside this row's LEVEL leg (`data/fuel/trajectories.py:258`) |
| 15 | `gas_plant_monthly_pricing` | `GKKKKK` | `class_aware_fuel_price_fallback` (M) | the row's own class-aware donor tier; def carries only `class_aware :7074` |
| 16 | `unit_outage_short_windows` | `IIKKIR` | `unit_outage_maxgen_events` (M) | the **third** window shape of the family whose first two this row already registers |
| 17 | `plant_level_fleet` | `.KKKKK` | `carry_operating_mothballs` (M) | `fleet/eia860.py::load_mothballed_but_operating`, the same EIA-860 per-plant fleet-build seam this row is |
| 18 | `storage_measured_anchors` | `KK....` | `storage_as_commitment` (E) | the shared master gate of the ERCOT storage-AS award family this row's def already registers |

**Rows 12, 13 and 14 are the delicate ones, and are flagged HERE rather than discovered
later:** in each, the arming ISO's existing cell adjudicates a **sibling leg** of the
family, not the leg being registered — `cc_nameplate_summer_derate` ERCOT `U` is the *CC*
leg; `dual_fuel_switching` ERCOT `U` is the *switching* leg; `gas_monthly_actuals` ERCOT
`G` is the *level* swap. Per K-1 the cells stay put; per K-2 each registered leg carries
its own transcribed verdict and citation in the row's note. This follows the established
convention (`storage_measured_anchors` already hosts `caiso_storage_as_reservation` as
INERT/refuted under a `K` cell). It is stated up front because it is exactly the shape a
later auditor would otherwise read as a silent mismatch.

## §6 — pre-registered observations, with PASS / FAIL / UNINFORMATIVE fixed in advance

Written on **CONSTRUCTION and GATE STRUCTURE**, never on a solved dual (nyiso-115 G2 /
nyiso-118: a scope question gated on a dual can only pass when the mechanism does nothing).

### O-1 — CAISO's CT-drag coefficients are unreachable on the keeper

**Claim to test:** the caiso-164 keeper sets `ct_drag_cap=0.36`, `ct_drag_intercept=-0.1124`,
`ct_drag_slope_per_gw=0.00901` (CAISO's own derived values) while `ct_netload_drag=False`.

* **PASS** if the only consumers of the three scalars sit behind the `ct_netload_drag` gate,
  making them provably unable to change any LP coefficient on this keeper.
* **FAIL** if any consumer reads them ungated.
* **UNINFORMATIVE** if the gate's value cannot be established from the committed config.

Recorded either way. **This does NOT license a cell change** (CAISO's `netload_drag_floors`
cell is already `R`, caiso-140) and does **not** license a rule-26 `[R-DELETE]`: the fields
are live for ERCOT/PJM, so only CAISO's *values* would be residue, and pruning a per-ISO
default is a mechanism change (rule 28(d)).

### O-2 — does any registered field lack an adjudication? (the K-3 trigger)

For each of the 46, look for an identification in: the arming keeper's
`calibration_attestation.json` DOF ledger → `docs/calibration-log/<iso>.md` →
`results/calibration/FINDING-*` → the home row's existing note. **Every field with none is
listed by name in the FINDING as a live-but-invisible lever**, and no verdict is written for
it. A count of zero such fields would be the surprising outcome, not the expected one.

## §7 — success criteria, scored in the FINDING exactly as written here

1. **Shared-gap → 0 in all six ISOs.** ERCOT 14→0, CAISO 5→0, PJM 18→0, MISO 17→0,
   NYISO 0→0, NEISO 0→0, on a post-edit re-sweep.
2. **`scripts/check_mechanism_matrix.py` PASSES**, and the ratchet baseline
   `mechanism-matrix-gaps.json` `shared_armed_on_keeper` block is **0 for all six** and has
   only SHRUNK.
3. **Every `cells:` string byte-identical — all 183 rows, zero mints (K-1).** Row count
   183 → 183, zero new rows, zero deletions.
4. **THE CROSS-COLUMN LEAK CHECK, in the form this lane's shared registrations require.**
   nyiso-121's criterion 4 ("the other five ISOs' counts must not move") is *unsatisfiable
   here by construction*: seven fields are armed on two keepers at once, so registering one
   correctly MUST drop it from both ISOs' lists. The honest form, and the one scored:
   1. **4a — predicted counts.** `live_but_invisible`: ERCOT **12 → 2**, MISO **12 → 3**,
      CAISO **1 → 1**, PJM **0 → 0**, NYISO **0 → 0**, NEISO **0 → 0**. ERCOT's surviving
      two are `ercot_gas_commitment_bridge` and `retirement_years_coal`; MISO's surviving
      three are `retirement_years_coal`, `federal_ces_ccs_capture_fraction`,
      `coal_bit_committed_takeorpay` — all four distinct fields declared OUT in §4.
   2. **4b — the anti-leak invariant.** For **every** (ISO, field) pair that leaves that
      ISO's shared-gap or live-but-invisible list, BOTH must hold: (i) that ISO's own
      keeper or bundles actually arm the field, and (ii) the home row carries a **cited,
      pre-existing** adjudication for **that** ISO. **No field may drop out of an ISO's
      list merely because another ISO's registration named it.** Scored per pair, in a
      table, for all seven double-armed fields.
   3. **4c — family counts.** All six stay at 0 absent / 0 prose-only / 0 armed-no-cell. No
      `ScenarioConfig` field is added or removed, so family sizes move only if main does.
5. **O-1 and O-2 reported with their pre-registered verdicts**, including any FAIL, and
   including a full by-name list under K-3.
6. **Rule 27 `[R-PUSH]`:** `mechanism-matrix.js` is >300 lines — edited locally with the
   Edit tool, pushed as exact on-disk bytes, and the pushed blob **verified byte-for-byte**
   (line count + sha256) before the next commit.

## §8 — what this session will NOT do

* **No lever is tested, chartered or queued in any ISO.** In particular **MISO's C7
  COAL_PRB** is not opened: nyiso-121 §8 states plainly that no MISO lever is tested,
  chartered or queued, and that census surfaced no never-adjudicated armable candidate. A
  new MISO lever requires its own identification from MISO's own data first (rule 25), which
  is a solving lane's work, not a census's.
* **No keeper, determination, `calibration-complete.json` entry or holdout marker is
  touched.** No promotion occurs, so rule 22 D-5(b) does not fire and no determination
  re-verification is owed.
* **No dashboard run is registered** — rule 15 is satisfied vacuously because no run is
  produced (no LP, no solve), the ercot-156 / caiso-161 / nyiso-121 precedent.

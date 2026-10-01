# FINDING — caiso-236: the keeper's DOF ledger over-counted its residual by two entries, one of them a row for parameters that do not exist

**Session caiso-236, 2026-09-02. Branch `claude/caiso-dof-residual-audit-7nvz6x`,
cut fresh from `origin/main` (`4692598f`). Pre-registered in
`results/calibration/PRECOMMIT-caiso236-dof-residual-ledger-audit-2026-09-02.md`,
pushed BEFORE any classification was computed.**

**NO SOLVE WAS RUN. NO SCORED NUMBER MOVED. C3a WAS NOT THIS SESSION'S OBJECT
AND IS NOT ARGUED FROM ANYWHERE BELOW** (rule 1 `[R-STRUCT]`; PRECOMMIT §0.3).
This is a rule-21 `[R-DOF]` / rule-26 `[R-DELETE]` ledger-integrity pass,
admissible under the caiso-201 resting ruling because it is not a lever hunt.
Every number is read from the keeper's own committed
`run_config.json` + `hourly/` sidecars or from importing the code; the
instrument is `scripts/probes/_caiso236_dof_residual_classifier.py`.

Keeper throughout: **`2026-09-01-caiso-231-b1-ungrounded`** (bundle
`results/calibration/caiso231_b1_ungrounded`), **NOT-YET**, C3a the sole
load-bearing FAIL. **The keeper is UNCHANGED** — no re-solve, no
re-registration, no promotion. CAISO holds no `complete` and no `final` marker;
the holdout freeze is active; every read stayed inside 2023–2025.

---

## §1 — HEADLINE

| | before | after |
|---|---|---|
| ledger entries (`n_entries`) | 11 | **9** |
| residual-identified (`n_residual`) | 7 | **6** |
| residual entries **deleted from the code** | — | 1 (`CAISO_BIDIR_EXPORT_CAP_MW`, with its whole mechanism) |
| residual entries that were **never real** | — | 1 (`COAL_SIGMOID_DEFAULTS[CAISO]` — a PHANTOM row) |
| entries whose ledger TEXT was false for this keeper | — | 2, corrected in place |
| solves run | — | **0** |

**The two headline defects.**

1. **A PHANTOM ROW.** `COAL_SIGMOID_DEFAULTS[CAISO]` attested **four fitted
   scalars that do not exist**. `COAL_SIGMOID_DEFAULTS` holds keys for ERCOT,
   MISO and PJM only — **no `("CAISO", *)` key of any kind** — and the keeper
   sets none of the four `coal_<supply>_passthrough_{floor,ceil,gas_mid,gas_slope}`
   overrides, so `coal_sigmoid_params` returns `None` for **every** supply and
   `coal_passthrough_series` falls back to the flat passthrough (`1.0` = full
   delivered cost, the identity). `coal_prb_passthrough_sigmoid: true` in the
   keeper's config is a toggle armed over nothing. The generator emitted the row
   off the **toggle alone**, never checking that a curve resolves.
2. **A DEAD RE-ARMABLE KNOB, NOW DELETED.** `CAISO_BIDIR_EXPORT_CAP_MW = 4,361
   MW` was read only by `caiso_bidir_intertie`, which is `False` on the keeper
   **and `False` in the `ScenarioConfig` defaults** — unreachable in every
   shipped configuration, while one CLI flag could re-arm it. That is exactly
   rule 26's "a deprecated parameter that still parses is a re-armable answer
   key", and the row's own `root_cause` named the exit verbatim: *"R5-delete the
   `caiso_bidir_intertie` mechanism (rule 26)"*. Deleted in full.

---

## §2 — THE CLASSIFICATION

Classes are the pre-registered ones (PRECOMMIT §1). **(c) is fail-closed**: its
action is "report and do not touch", so ambiguity can only make the pass more
conservative.

| # | entry | class | the evidence line |
|---|---|---|---|
| 1 | `offer_curve_by_group` | **(c)** LIVE + MATERIAL | `use_campd_bins` and `plant_level_fleet` both `true`; 13 groups populated with non-unit bands. Read on every keeper solve. |
| 2 | `offer_curve_committed_below_floor[CAISO]` (`ST_GAS` 0.81) | **(c)** LIVE + MATERIAL | Same path. Materiality screen **FAILS both legs**: ST_GAS is 0.0964 / 0.2931 / 0.0487 % of dispatch (2024 over the 0.10 % line) across 978 / 875 / 134 hours = 11.16 / 9.99 / 1.53 % of hours (all three over the 1.0 % line). |
| 3 | `offer_curve_smoothing` (n 6, exp 1.0) | **(c)** LIVE + MATERIAL | `n = 6 > 0` makes `bins_to_fleet` render the econ ramp as a 6-slice rising curve (`_econ_curve_steps`) rather than two flat blocks — not an identity. |
| 4 | `COAL_SIGMOID_DEFAULTS[CAISO]` | **PHANTOM** | No `("CAISO", *)` key exists; no keeper override set; `coal_sigmoid_params(CAISO, s) is None` for all six supplies; flat fallback `coal_prb_passthrough = 1.0`. **There is no parameter to classify.** |
| 5 | `battery_dispatch_adder` (5.0 $/MWh) | **(c)** LIVE + MATERIAL | Storage discharge is 6.20 / 9.65 / 13.43 TWh = **2.96 / 4.46 / 6.38 %** of modelled dispatch in 4,046 / 4,082 / 4,291 hours. Two orders of magnitude past the screen. |
| 6 | `WECC_import_simultaneous.cap_mw` (7,500) | **(a′)** KEEPER-DEAD, LANE-LIVE | §3 below. Superseded on this keeper by the MIC partition; still the operative cap of every forecast-mode run. **Not deletable.** |
| 7a | `IMPORT_TRANCHES[CAISO]` | **(c)** LIVE + MATERIAL, already DECLARED | `get_interchange_spec` reads the ladder DIRECTLY to build the six per-hub corridor import legs even though `spec.import_tranches` is empty under `use_corridors`. Its `spot_capacity` DOF is closed as NOT IDENTIFIABLE (caiso-233/234/235) and permanently declared to the owner. |
| 7b | `EXPORT_TRANCHES[CAISO]` | **(a′)** KEEPER-DEAD, LANE-LIVE | §4 below. **Not deletable.** |
| + | `CAISO_BIDIR_EXPORT_CAP_MW` (4,361) | **(a)** TRUE DEAD → **DELETED** | §5 below. |

**Class counts: (a) 1 · (a′) 2 · (b) 0 · (c) 5 · PHANTOM 1.**

**(a′) is a class the pre-registered taxonomy did not have, and it is disclosed
as an amendment rather than folded into (a) or (c).** It is "dead under the
keeper's gates, but read by another SHIPPED configuration" — in both cases the
`ScenarioConfig` DEFAULTS, which is what a forecast-mode CAISO run solves on.
Deleting such a value is a **mechanism change**, not a ledger repair, so rule 26
does not reach it and the honest action is to fix the ledger's *claim*, not the
scalar. The PRECOMMIT anticipated the shape (§0 of the instrument names it) but
not that two of seven rows would land there.

**No entry classified (b), so under PRECOMMIT §4.1 no A/B solve was run.** The
byte-identity apparatus of §4.2–§4.3 was never needed and is not claimed.

---

## §3 — ENTRY 6: THE ROW'S PREMISE *AND* ITS caiso-188 MEASUREMENT ARE BOTH STALE

The row says `where: iso_configs.py CAISO interface_limits (fallback;
capacity_deliverability_limits OFF only)`, and then its `source` says caiso-188
**measured that qualifier failing** — total import pinned at exactly 7,500.0 MW
in 764/477/809 hours of 2023/24/25 on every CAISO bundle from caiso-175 onward
"the designated keeper caiso184_c1_lpbasis included", because Part A resolves
through the gitignored, disposable `data/clean/capacity-deliverability/`
partition that no solve auto-builds.

**On THIS keeper both readings are wrong, measured here:**

* `run_config.json` → `resolved_inputs.seam_import_cap` records
  `source = "mic_partition"` with cap **16,055 / 16,452 / 16,148 MW** for
  2023/24/25 — the published branch-group MIC sum — which
  `apply_interchange_topology` then applies through
  `apply_deliverability_seam_limit`. The baked 7,500 is **replaced, not used**.
* The bundle's own P1 hourlies agree. Net seam position reaches **9,631.0 /
  9,169.0 / 10,545.5 MW** and stands **above 7,500 MW in 835 / 533 / 803
  hours**, with **exactly zero hours pinned at 7,500.0** in any year.

caiso-188's finding stays true of the caiso-175…184 bundles it measured; what
changed is the keeper. And **caiso-188's own open item (1)** — *"nothing
COMMITTED yet records which cap a bundle solved against; the durable fix is to
persist the resolved seam cap into run_config.json"* — **is DISCHARGED**: the
`resolved_inputs` block this classification read is that persistence, and it is
what let the question be answered without a solve.

**Why it is not deleted.** `capacity_deliverability_limits` **defaults to
`False`**, so the baked 7,500 remains the operative seam cap of every
forecast-mode CAISO run. Deleting it would change a shipped lane's solve.
Open item **O-1 (forecast/backcast parity, issue #1373)** stays the correct
exit; rule 26 does not reach this scalar. The row keeps its `residual` class and
gains the measurement.

---

## §4 — ENTRY 7b: THE LEDGER'S ASSERTION IS NOW ESTABLISHED FROM CODE — AND STILL NOT DELETABLE

The row asserted *"`EXPORT_TRANCHES[CAISO]` is NOT on this keeper's binding path
at all"*. That was an **assertion**, the same shape caiso-188 caught on entry 6,
so it was re-established rather than cited:

* `get_interchange_spec` sets `export_tranches = []` whenever `use_corridors`,
  which `caiso_per_hub_intertie` makes true.
* `build_caiso_per_hub_intertie` bounds each hub's export leg at its **physical
  corridor TTC** via `_caiso_corridor_export_cap_mw` (COI 4,800 / Path-46 10,623
  MW), never at a ladder rung.
* The only injector that could reprice the rungs
  (`inject_caiso_import_solar_shape`) matches export sinks by **pooled-node
  uid** (`WECC_import_export_solar`), which the per-hub legs
  (`WECC_PNW_export_WECC_PNW`, …) cannot match.
* Built at both configurations: **keeper → 0 export tranches; `ScenarioConfig`
  defaults → 2.**

So the claim is now measured, not asserted. But that last line is also why it is
**(a′) and not deletable**: `caiso_per_hub_intertie` **defaults to `False`**, so
the pooled-node ladder — export rungs included — is what a forecast-mode CAISO
run solves on.

---

## §5 — THE ONE DELETION, AND WHY IT COST NOTHING

`caiso_bidir_intertie` was `False` on the keeper **and** `False` in the
`ScenarioConfig` defaults; no committed artifact anywhere in `results/` or
`frontend/` records it `true`. Its builder existed only to be reachable by
`--caiso-bidir-intertie`, and it carried the fitted **4,361 MW** aggregate
export cap. Deleted in full (16 files): the `ScenarioConfig` field, the CLI flag
and its plumbing in both runners, the `get_interchange_spec` ladder rung, the
`build_caiso_bidir_intertie` / `inject_caiso_bidir_intertie_prices` pair, the
`CAISO_BIDIR_IMPORT_CAP_MW` / `CAISO_BIDIR_EXPORT_CAP_MW` / `_CAISO_BIDIR_EXPORT_NAME`
constants, the facade exports, the registry skip-guard, the DOF-ledger row, its
tests, and the now-orphaned frozen derive script
`scripts/data/derive_caiso_export_cap.py` (its sole product was the deleted
constant).

**The deletion is CACHE-KEY NEUTRAL and therefore solve-neutral at the config
level.** `scenarios._CACHE_KEY_RETIRED_FIELDS` exists precisely to make rule-26
deletion affordable — it re-inserts a deleted field's old default before
hashing — so `caiso_bidir_intertie: False` was registered there and **both
pinned cache-key literals are unmoved** (`test_persisted_identity.py`'s default
and backcast pins, plus the eight per-mechanism arming-key tests, all green).
No on-disk cache is orphaned and no keeper's reproducibility is touched. A
retired entry is not a zombie knob: it lives only inside the hash, cannot be
assigned, and cannot be read by any solve path.

**Deliberately NOT touched**: `scripts/archive/run_caiso45_export_sink.py` and
`run_caiso48_solar_decommit.py`, and `scripts/probes/_caiso186os_dof_repair.py`.
Those are the historical record (`scripts/archive/` is "retired one-off run
drivers … not maintained"; `scripts/probes/` is the calibration record) and
neither imports a deleted symbol.

---

## §6 — THE PREDICTIONS, SCORED

PRECOMMIT §3 committed to a class for each of the eight objects before any code
was read. **Five clean hits, one partial, two misses.**

| # | predicted | actual | |
|---|---|---|---|
| 1 | (c) | (c) | **HIT** |
| 2 | (c) | (c) | **HIT** |
| 3 | (c) | (c) | **HIT** |
| 4 | (b), or (a) if no PRB key | **PHANTOM** | **MISS** — §6.1 |
| 5 | (c) | (c) | **HIT** |
| 6 | (c), *explicitly against the charter's expectation* | **(a′)** | **MISS** — §6.2 |
| 7a | (c), DECLARED | (c), DECLARED | **HIT** |
| 7b | (a) | (a′) — liveness right, deletability wrong | **PARTIAL** |
| + | (a) | (a), DELETED | **HIT** |

**§6.1 — Entry 4 missed in an instructive way.** Both pre-registered branches
assumed a parameter existed. The materiality screen was even computed and
**FAILED**: CAISO coal is 0.0442 / 0.0248 / 0.0393 % of dispatch (inside the
0.10 % threshold) but runs at a ~14 MW floor in **8,760 of 8,760 hours** in every
year — 100 % against a 1.0 % threshold — so under the pre-registered decision
rule the row would have been **(c)**, and the predicted (b) neutralization would
have been refused. That is the screen working as designed. It is moot: the row
attests parameters that do not exist for CAISO at all, which no branch of the
taxonomy covered.

**§6.2 — Entry 6 is the miss worth stating loudest, because it went against
me.** The charter named entry 6 "the prime candidate" for (a); the PRECOMMIT
predicted **(c)** on the ledger's own committed caiso-188 measurement, and
registered that disagreement in advance. **The charter was right and the
prediction was wrong** — Part A resolves on this keeper. The lesson is the one
caiso-188 itself taught: a ledger row's prose about which cap bound is evidence
about the bundle it was written for, not about the current keeper, and the fix
caiso-188 asked for (persisting the resolved cap) is what made re-checking it
free.

**§6.3 — A pre-registration arithmetic error, disclosed.** PRECOMMIT §3.5
predicted "residual 7 → 6" (**correct**) and "`n_entries` 11 → 10" (**wrong**:
it counted entry 4's removal against the residual total but forgot it also
removes an entry). The actual is **11 → 9**. The error was in the prediction,
not the outcome.

---

## §7 — THE PHANTOM IS NOT CAISO-ONLY (reported, NOT acted on)

The generator emitted `COAL_SIGMOID_DEFAULTS[<ISO>]` from an armed sigmoid
**toggle** without checking that `COAL_SIGMOID_DEFAULTS` (overlaid by the
explicit `coal_<stem>_*` fields) actually resolves. The fix — count a toggle only
when its supply's parameter set resolves — **can only remove over-counted rows,
never add one**. Measured against every ISO's current keeper bundle:

| ISO | keeper | effect of the fix |
|---|---|---|
| ERCOT | `2026-08-25-234-eastex-identity` | none — its curves resolve |
| PJM | `2026-08-15-pjm-162-inputclock` | none |
| MISO | `2026-09-01-miso-198-oomlevel` | none |
| **CAISO** | `2026-09-01-caiso-231-b1-ungrounded` | **−1 row (this session's, regenerated)** |
| **NYISO** | `2026-08-30-nyiso-159-loss-surface` | **−1 phantom row, `COAL_SIGMOID_DEFAULTS[NYISO]`** |
| **NEISO** | `2026-08-17-neiso-99-joint-p1` | **−1 phantom row, `COAL_SIGMOID_DEFAULTS[NEISO]`** |

**Only CAISO's attestation was regenerated.** NYISO's and NEISO's committed
attestations belong to their lanes and are left exactly as they are — this
session does not rewrite another lane's committed artifact (rule 25
`[R-ISO-SCOPE]` discipline). **They are handed to those lanes as an open item**:
each carries one phantom residual row, and re-running
`scripts/build_dof_ledger.py <bundle> --iso <ISO>` discharges it. Nothing
reddens in the meantime — `audit_keepers` E8 checks that the ledger *exists* and
that residual rows carry a root cause, never that it is current against the
generator, and no CI workflow runs `build_dof_ledger --check`.

**Baseline honesty:** PJM, CAISO, NYISO and MISO keepers were **already** stale
against the generator at `origin/main` before this session (PJM and MISO by
large margins — 19 vs 14 and 38 vs 25 entries — because those lanes hand-add rows
the generator does not emit). CAISO's was NOT: committed 11 = generated 11, so
the CAISO regeneration carries **only** this session's two corrections and
nothing else.

---

## §8 — A SECOND LEDGER-GENERATOR DEFECT, FIXED IN PASSING

Regenerating the CAISO ledger would have **silently deleted** the 2,152-character
hand-written `note` on `offer_curve_by_group` — the caiso-220/231 correction
recording that five of CAISO's groups are now MEASURED, so the row's
`identification: "residual"` **overstates** it. That note is precisely the
disclosure rule 21 exists to preserve, and no generator writes it.
`build_dof_ledger._carry_hand_notes` now carries a committed row's hand-written
note onto its regenerated twin — surviving rows only, and only where the rebuild
supplies no note of its own, so a row the generator no longer emits still takes
its note with it. Verified: the note survives, and
`build_dof_ledger --check` reports the CAISO ledger **current** (i.e. the
regeneration is now idempotent).

---

## §9 — THE LEDGER AS IT NOW STANDS

`n_entries = 9`, `n_residual = 6`:

| identification | entry |
|---|---|
| residual | `offer_curve_by_group` — (c), + caiso-236 note |
| residual | `offer_curve_committed_below_floor[CAISO]` — (c), + screen result |
| residual | `offer_curve_smoothing` — (c), + the cross-ISO observation of §10 |
| residual | `battery_dispatch_adder` — (c) |
| residual | `WECC_import_simultaneous.cap_mw` — (a′), premise corrected (§3) |
| residual | `IMPORT_TRANCHES/EXPORT_TRANCHES[CAISO]` — 7a (c) DECLARED, 7b (a′) (§4) |
| measured | `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` |
| measured | `caiso-plant-hub-membership crosswalk` |
| measured-physical | `reliability_floor coefficients` |

**Four of the six residual rows are LIVE AND MATERIAL and were not touched.**
Grounding a live residual is a funded-object question under the caiso-201
resting ruling, not a ledger-audit session's to take. They are named for the
owner and left alone: `offer_curve_by_group`, the `ST_GAS 0.81` committed band,
`offer_curve_smoothing`, `battery_dispatch_adder`.

---

## §10 — OPEN ITEMS HANDED ON

1. **NYISO and NEISO each carry one phantom `COAL_SIGMOID_DEFAULTS[<ISO>]` row.**
   Discharged by re-running the generator on their own keeper bundles, in their
   own lanes (§7).
2. **`offer_curve_smoothing` is classed `residual` but sits at the SHARED
   default.** `n = 6` / `exp = 1.0` are the `ScenarioConfig` defaults and all six
   ISO keepers run `n = 6` (stated in `fleet/assembly.py` at the
   `ercot_econ_curve_top_refine` gate), so calling it a CAISO residual overstates
   it the way `offer_curve_by_group` was already known to. **Recorded as an
   observation, deliberately not re-classed**: that is a cross-ISO judgement
   (rule 25) no single-ISO lane may make.
3. **The `prb_follower` tier is UNDER-counted for ERCOT and MISO.** When
   `coal_prb_passthrough_tiered` is armed alongside the prb sigmoid,
   `prb_follower_passthrough_series` consumes a *second* four-parameter set
   (`("ERCOT", "prb_follower")`, `("MISO", "prb_follower")`) that the ledger's
   `n_scalars = 4 × len(sigmoids)` never counts. This session's fix only REMOVES
   over-counted rows and deliberately did not change any other ISO's count;
   correcting an under-count belongs to those lanes.
4. **O-1 forecast/backcast parity (#1373) is unchanged and now better
   evidenced**: the fitted 7,500 is dead on the keeper and live in forecast, which
   is precisely the parity gap O-1 names (§3).
5. **`WECC_EXPORT_CAP_MW`** (`spec.py`, `= EXPORT_TRANCHES["CAISO"][0][1]` = 2,500)
   has no consumer anywhere in `src/` or `scripts/` — only a facade re-export and
   its membership test. It is NOT a rule-26 candidate (it derives from a
   lane-live ladder rather than being a retired mechanism's fitted residue) and
   was left alone; noted so a later pass need not re-derive the observation.
6. **Pre-existing test failures, unrelated to this session and unchanged by it.**
   `tests/unit` + `tests/iso` + `tests/regression` were run in full at this HEAD:
   **5,196 + 413 passed, 6 + 7 failed**, and **every one of the 13 failures was
   verified failing at `origin/main` before any edit** —
   `test_caiso_locational_as::test_families_zone_masks` (the FSNO sub-zonal
   partition), `test_cache_config_agreement::test_fourteen_groups_split_two_and_twelve`,
   the four `test_export::TestExportScenarioJson` cases, and the
   `test_soundness.py` end-to-end family. **This session introduces ZERO new test
   failures**, and `tests/unit/config` (656 passed, 13 skipped) plus every
   cache-key pin is green.

---

## §11 — WHAT THIS SESSION DID NOT DO

* No solve, no scoring, no registration, in any year. No dashboard run
  registration is due: **rule 15 attaches to completed calibration runs, and
  this session produced none.**
* No keeper change, no promotion, no `keepers/CAISO.json` edit, no
  `calibration-complete.json` touch, no holdout-freeze touch.
* No mechanism proposed, tested, or re-opened; no cell verdict moved. The
  mechanism-matrix edits are a base-row retirement note (rule 28(c), for a
  deleted `ScenarioConfig` field) and one CAISO-shard evidence append (rule
  28(b)) — `scripts/check_mechanism_matrix.py` passes.
* Nothing in the DO-NOT-REDO list (PRECOMMIT §0.4) was re-opened. The
  import-depth object stays CLOSED and permanently declared; no fourth
  construction was proposed.
* **No number in this document is a price residual, and no conclusion here
  depends on one.**

*Written 2026-09-02, session caiso-236. Instrument:
`scripts/probes/_caiso236_dof_residual_classifier.py`. Pre-registration:
`results/calibration/PRECOMMIT-caiso236-dof-residual-ledger-audit-2026-09-02.md`.*

# FINDING — xiso-7: the `prb_follower` DOF under-count is REAL IN THE GENERATOR and INERT ON EVERY KEEPER

**Session xiso-7, 2026-09-02.** Pre-registration:
`results/calibration/PRECOMMIT-xiso7-prb-follower-dof-undercount-2026-09-02.md`
(pushed before any keeper artifact was opened). Instrument:
`scripts/probes/_xiso7_prb_follower_dof_probe.py`. Transcript:
`results/calibration/_xiso7_prb_follower_dof.json`.

**No LP solved. No bundle. No scoring. No dashboard registration. No keeper
changed. No CAISO artifact, config or number touched.** Takes option B of the
three items caiso-236 handed on (`FINDING-caiso236-…` §10.3).

---

## §1 — HEADLINE

The under-count caiso-236 named is **real in the generator and structural** — and
it fires on **NO current keeper of any ISO**. The affected set is **EMPTY**.

Two things follow, and they point in opposite directions:

1. **The fix lands anyway**, by the pre-registered decision rule §4(a): a
   generator that will attest every *future* keeper must count a parameter set the
   solve demonstrably consumes. It is now counted, pinned by eight tests, and
   **provably fires** — a constructed ERCOT config moves 4 → 8 scalars — while
   moving **no committed number anywhere**.
2. **caiso-236 §10.3 was wrong on its own facts.** It named ERCOT and MISO as
   lanes that "under-count their own residual". Neither does, and neither could:
   **both have `coal_prb_passthrough_sigmoid = False`**, so the conjunction that
   gates the follower tier cannot fire on either. The item was handed to two lanes
   that had nothing to discharge. **This document withdraws that half of §10.3.**

The session also found **two things caiso-236 did not predict**, one of which is a
**live red gate on `main` that caiso-236 itself created** (§7), now fixed.

---

## §2 — THE DEFECT, RESTATED FROM SOURCE

`prb_follower` is the one coal passthrough tier with **no sigmoid toggle of its
own**. Its gate is the conjunction

```
coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered
```

(`src/market_sim/data/fleet/assembly.py:1774`), and when it fires,
`prb_follower_passthrough_series` resolves a **second** four-parameter set —
`COAL_SIGMOID_DEFAULTS[(ISO, "prb_follower")]` overlaid by the explicit
`coal_prb_follower_*` fields — routed to PRB plants whose per-plant must-run floor
is at or below `coal_prb_follower_mustrun_max`, **alongside** the baseload prb
curve (both maps are kept; the tiered branch does not overwrite).

`build_dof_ledger.config_entries` enumerated only the five
`coal_*_passthrough_sigmoid` toggles and emitted `n_scalars = 4 * len(sigmoids)`.
`coal_prb_passthrough_tiered` appeared nowhere in the generator. **Those four
scalars were attested nowhere**, for any ISO, ever.

Only two `prb_follower` sets exist, and both differ from their baseload twin — so
neither is an alias and both are genuinely separate fitted surfaces:

| pair | floor | ceil | gas_mid | gas_slope |
|---|---|---|---|---|
| `("ERCOT","prb")` | 0.78 | 1.50 | 2.85 | 2.5 |
| `("ERCOT","prb_follower")` | **0.68** | **1.35** | 2.85 | 2.5 |
| `("MISO","prb")` | 0.687 | 1.0 | 3.187 | 2.5 |
| `("MISO","prb_follower")` | **0.598** | 1.0 | 3.187 | 2.5 |

**Why an under-count earns a session when caiso-236's over-count fix was safe.**
An over-count is the conservative direction — the attestation claims *more* fitted
surface than exists, which never misleads a reader about how much of the model is
fitted. An **under-count states fewer free parameters than the solve consumes**,
which is exactly the disclosure failure rule 21 `[R-DOF]` exists to prevent.

---

## §3 — THE CENSUS

All six designated keepers, read from their committed bundles' `run_config.json`:

| ISO | keeper | `prb_sigmoid` | `tiered` | follower resolves | **UNDER-COUNTED** |
|---|---|:--:|:--:|:--:|:--:|
| ERCOT | `2026-08-25-234-eastex-identity` | **False** | True | True | **no** |
| PJM | `2026-08-15-pjm-162-inputclock` | True | True | **False** | **no** |
| CAISO | `2026-09-01-caiso-231-b1-ungrounded` | True | True | **False** | **no** |
| NYISO | `2026-08-30-nyiso-159-loss-surface` | True | True | **False** | **no** |
| NEISO | `2026-08-17-neiso-99-joint-p1` | True | True | **False** | **no** |
| MISO | `2026-09-01-miso-198-oomlevel` | **False** | **False** | True | **no** |

**Every keeper misses the gate, and the two families miss it for opposite
reasons:**

* **ERCOT and MISO have the follower curve but not the toggle.** ERCOT's keeper
  runs `coal_perplant_offer_curves` (ERCOT-144), whose armed harness disarms the
  sigmoids — so ERCOT carries **no `COAL_SIGMOID_DEFAULTS[ERCOT]` row at all**.
  MISO's keeper arms **no coal sigmoid toggle whatsoever**, so the
  `measured-physical` MISO branch of the generator is likewise dead at the current
  keeper. These are the two ISOs caiso-236 §10.3 named.
* **PJM, CAISO, NYISO and NEISO have the toggle but not the curve.** All four arm
  the full conjunction, and none has a `(ISO, "prb_follower")` registry entry, so
  `prb_follower_passthrough_series` falls back to the baseload prb curve and
  **consumes no additional parameters**. The resolve gate is doing its job.

---

## §4 — THE PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| **P-1** | affected set = **{MISO}** | **MISS** — affected set is **EMPTY**. MISO arms neither toggle. |
| **P-2** | ERCOT NOT affected: `coal_perplant_offer_curves` armed, sigmoids disarmed, no sigmoid row | **CONFIRMED** on all three legs |
| **P-3** | correction = +4 scalars, +0 entries | **MOOT** (no affected keeper). Verified instead on a constructed config: ERCOT baseload-only 4 → tiered 8, one row. |
| **P-4** | added MISO scalars are `measured-physical`, `n_residual` unmoved | **MOOT** (no affected keeper) |
| **P-5** | `coal_prb_follower_mustrun_max` uncounted, and at its 25.0 default | **CONFIRMED, both halves** — uncounted by every row, and exactly 25.0 on all six keepers |
| **P-6** | affected lane's ledger stale ⇒ surgical route | **MOOT** — no ledger edit was due anywhere |
| **P-7** | fix moves no keeper's generated ledger | **CONFIRMED** — all six byte-identical pre/post (`n_entries` 9/14/9/7/6/25, `n_residual` 6/6/6/5/4/2, unchanged) |
| **P-8** | gates green, no new test failures | **CONFIRMED** — see §8 |

**P-1 is the session's substantive miss**, and it is a miss in the *direction that
matters*: the pre-registration inherited caiso-236's claim that MISO under-counts,
and measurement refuted it. The instrument was built to test the claim rather than
to confirm it, which is why the refutation surfaced at all.

---

## §5 — THE FIX

`scripts/build_dof_ledger.py`, mirroring the caiso-236 over-count fix directly
above it:

* **`_prb_follower_engaged(sc, iso)`** — the conjunction plus the same
  resolve-or-nothing discipline as `_coal_sigmoid_resolves`. An incomplete
  parameter set makes the solve fall back to the baseload curve, so it attests
  nothing.
* **`tiers = sigmoids + [follower]`**, and `n_scalars = 4 * len(tiers)` in **both**
  the MISO `measured-physical` branch and the generic `residual` branch. For MISO
  the class is right without further argument: `scripts/data/derive_coal_sigmoid.py`
  **also emits the `prb_follower` row**, so the follower four-set carries the same
  frozen-derive provenance as its baseload twin.
* **The row's emission now gates on `tiers`, not `sigmoids`.** The follower set can
  resolve for an ISO whose *baseload* prb pair does not (explicit
  `coal_prb_follower_*` fields are enough), and the tier is then live and is the
  row's only engaged parameter set. Under the old `if sigmoids:` that row would
  have vanished entirely — an under-count of four scalars **and** a whole row.

**Tests: `tests/scoring/test_build_dof_ledger_coal_sigmoids.py`, 8 cases, all
passing.** No test covered this generator's counting at all before — the caiso-236
fix shipped untested — so the file pins **both** gates.

The load-bearing case is `test_gate_agrees_with_the_solve`: over six (ISO,
override) combinations it asserts `_prb_follower_engaged` equals
`coal_sigmoid_params(cfg, "prb_follower") is not None` — the resolver the dispatch
itself calls. **The ledger's gate is now pinned to the solve's**, so the
attestation cannot drift from what the model consumes in either direction.

---

## §6 — TWO FINDINGS NOT PREDICTED (reported, and one already on record)

**U-1 — PJM's committed ledger OVER-counts the sigmoid row by 4 scalars, and
caiso-236's §7 table missed it.** PJM arms three toggles (`prb`, `bit`, `sub`) but
`("PJM","prb")` does not exist, so only two resolve: committed `n_scalars = 12`,
generator `n_scalars = 8`. caiso-236 §7 recorded PJM as **"none — its curves
resolve"**, which is true of the *row* (bit and sub keep it alive) but not of its
*scalar count*: that table tracked row removals and was blind to a partial
over-count inside a surviving row. **This is the same family as the NYISO/NEISO
phantom rows of option A, and it is handed to the PJM lane on the same terms** —
discharged by re-running `build_dof_ledger.py` on its own keeper, in its own lane.
Not touched here (rule 25 `[R-ISO-SCOPE]`; and PJM's ledger is hand-augmented, 19
committed vs 14 generated, so a blind regeneration there would destroy rows).

**U-2 — ERCOT's keeper carries a dormant fitted follower floor behind the disarmed
toggle. ALREADY ON RECORD; this session adds one thing.** ERCOT's keeper sets
`coal_prb_follower_floor = 0.76` explicitly (the registry value is 0.68) while
`coal_prb_passthrough_tiered = True` remains armed — both inert only because
`coal_prb_passthrough_sigmoid` is False. **xiso-3 already established this**, with a
measured Δ = 0.0 and a separating positive control
(`FINDING-xiso3-shared-stem-backlog-2026-08-04.md` §4, row
`ERCOT | coal_prb_follower_floor | 0.76 | sigmoid AND tiered (first conjunct
False) | 0.0`), and filed it **unadjudicated**. The increment here is only this:
the inert scalar is also **absent from the DOF ledger**, so re-arming one boolean
would add an *undisclosed* fitted parameter. After this session's fix it would at
least be **counted** the moment it went live. Whether the dormant value is
cosmetic, a rule-19 `[R-ONE-MECH]` question or a rule-26 `[R-DELETE]` candidate
remains for a lane that may adjudicate ERCOT — **a census may not** (rule 28(d)),
and this one does not.

---

## §7 — OUT-OF-PRECOMMIT REPAIR: caiso-236's rule-26 deletion LEFT A RED GATE ON `main`

**Disclosed separately from §4 because it is not a pre-registered result.** It was
found by the charter's own instruction to baseline test failures at `origin/main`
before attributing any to this session.

The charter lists thirteen tests red at HEAD, all in `tests/unit`, `tests/iso` and
`tests/regression`. **`tests/scoring` was not in that list and carried seven more**,
verified failing at clean `origin/main` with this session's work stashed. Their
error named the cause outright:

```
SystemExit: meta.json keys not bound to solve_and_persist kwargs:
['caiso_bidir_intertie'] — extend replay_keeper._REMAP/_IGNORE deliberately;
silent drops are the miso-50..53 regression class
```

caiso-236 deleted `caiso_bidir_intertie` from `ScenarioConfig` under rule 26 and
registered it in `scenarios._CACHE_KEY_RETIRED_FIELDS` — but **not** in
`scripts/replay_keeper.py`'s own parallel registry `_RULE26_DELETED_UNCONDITIONAL`.
Every keeper meta of **all six ISOs** records the key, so `build_kwargs` hard-errored
on all of them and the keeper-replay guard family went red. caiso-236 §11's "this
session introduces ZERO new test failures" was measured over `tests/unit` +
`tests/iso` + `tests/regression`; `tests/scoring`, which is where this guard lives,
was not run.

**Fixed here**, because it is a protective gate broken on `main` by the very
session whose open items this charter continues, the remedy is the one the error
prescribes, and it restores a guard rather than relaxing one:

* `"caiso_bidir_intertie": ("CAISO", (False, None))` added to
  `_RULE26_DELETED_UNCONDITIONAL`.
* The registry's second element may now be a **tuple of inert values** whose first
  element is the canonical unconditional behaviour (`_rule26_inert`). This was
  necessary, not cosmetic: all six keepers record the key as **`None`** — the
  tri-state CLI's "flag never set" — not `False`. Declaring the inert set per field
  keeps that from becoming a blanket "`None` is always safe" rule, which would be
  **false** for a deleted field whose default was the other polarity. Both existing
  entries keep their scalar form and their exact behaviour.
* **The strictness is preserved:** a bundle recording `True` — the fitted 4,361 MW
  aggregate export cap that no longer exists at HEAD — still hard-errors as
  historical-record-only. Census of every keeper meta: **all six record `None` at
  top level, none inside an override dict, and none records `True`.**

`tests/scoring/test_replay_keeper_strict.py::test_all_keeper_metas_build` is green
again.

**The other six `tests/scoring` failures are pre-existing, unrelated, and NOT
fixed here** — they belong to other lanes and to this container's data profile:

* `test_forecast_parity.py::test_all_six_keepers_resolve` — `ercot_adaptive_event_release`
  and `ercot_storage_adaptive_expectation` are armed in the ERCOT keeper with no
  forecast-orchestrator consumer and no declaration in
  `scripts/lib/forecast_parity_registry.py`. **An ERCOT/forecast-lane item.**
* `test_ff_readiness_battery.py` (5) — `ERCOT:confirmed_retirements [MISSING]
  clean partition unbuilt (data/clean is gitignored)`, i.e. an artifact of this
  session's `DATA PROFILE: caiso` hydration, plus a NYISO marker-state expectation
  (`'withdrawn' == 'complete'`). **Not code defects of this session's making**;
  the data-derived ones would likely resolve under a wider profile.

---

## §8 — GATES

* `scripts/audit_keepers.py --iso <ISO>` — **PASS, 0 failures / 0 warnings, on all
  six ISOs** (ERCOT, PJM, CAISO, NYISO, NEISO, MISO).
* `scripts/check_mechanism_matrix.py` — **exit 0**, integrity OK, keeper stamps and
  §5.x prose headers match every shard. Its anchor warnings are pre-existing
  line-number drift in `src/market_sim/config/scenarios.py`, **a file this session
  never touched**.
* `tests/scoring/test_build_dof_ledger_coal_sigmoids.py` — **8 passed** (new).
* `tests/unit` — **5 failed**, exactly the charter's baselined set
  (`test_cache_config_agreement::test_fourteen_groups_split_two_and_twelve` plus the
  four `test_export::TestExportScenarioJson` cases). **No new failures.**
* `tests/scoring` — **7 failed at clean `origin/main` → 6 after §7's repair.** The
  net movement of this session on the whole suite is **one test fixed, none broken.**

---

## §9 — WHAT THIS SESSION DID NOT DO

* No solve, no scoring, no bundle, no dashboard registration, in any year or ISO.
  Rule 15 `[R-DASHBOARD]` attaches to completed calibration runs; this session
  produced none.
* **No ledger edit on any keeper** — the fix moves no committed number (P-7), so no
  attestation needed rewriting and no other lane's committed artifact was touched.
* No keeper change, no promotion, no `keepers/<ISO>.json` keeper-id edit, no
  `calibration-complete.json` touch, no holdout-freeze touch. **No out-of-training
  year was solved, scored or registered.**
* No mechanism proposed, tested or re-verdicted; no `ScenarioConfig` field added or
  removed; **no mechanism-matrix cell moved.**
* Options **A** (NYISO/NEISO phantom rows) and **C** (O-1 forecast parity, #1373)
  are untaken and left exactly as caiso-236 left them.
* Nothing in the PRECOMMIT §0.4 DO-NOT-REDO list was re-opened. The import-depth
  object stays CLOSED and permanently declared. `caiso_bidir_intertie` was **not**
  re-added — §7 registers its *deletion* with the replay guard, which is the
  opposite move.
* **No number in this document is a price residual, and no conclusion here depends
  on one.**

---

## §10 — OPEN ITEMS HANDED ON

1. **PJM's committed ledger over-counts its sigmoid row by 4 scalars** (12 vs 8,
   §6 U-1). PJM lane, same discharge as option A. caiso-236 §7's PJM row —
   "none" — should be read as "no row removed", not "no change".
2. **Options A and C remain open exactly as caiso-236 left them**: the NYISO and
   NEISO phantom `COAL_SIGMOID_DEFAULTS[<ISO>]` rows (their own lanes), and O-1
   forecast/backcast parity #1373 (the forecast program).
3. **`coal_prb_follower_mustrun_max` is a free parameter counted by no ledger row**
   (P-5). It sits at its 25.0 default on all six keepers and is inert on all six, so
   nothing is currently misstated — but the moment any lane arms the follower tier
   it becomes a fifth uncounted scalar. Deliberately **not** folded into this
   session's fix: it is a tier-split threshold, not a sigmoid parameter, and
   classifying it is a judgement for a lane that may adjudicate its ISO.
4. **`_CACHE_KEY_RETIRED_FIELDS` and `replay_keeper._RULE26_DELETED_UNCONDITIONAL`
   are two hand-maintained registries of the same fact, with no test tying them
   together** (§7). That is what let caiso-236's deletion pass CI and break the
   replay guard. A guard asserting every `_CACHE_KEY_RETIRED_FIELDS` entry appearing
   in a committed keeper meta is declared in the replay registry would close the
   class. Not built here — it is infrastructure beyond this charter, and it wants
   an owner's view on which registry is canonical.
5. **The ERCOT dormant follower floor (§6 U-2) remains unadjudicated**, as xiso-3
   left it.

*Written 2026-09-02, session xiso-7.*

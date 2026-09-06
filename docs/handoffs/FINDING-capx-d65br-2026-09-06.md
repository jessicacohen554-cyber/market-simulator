# FINDING — capx D65-B-R: the coupled-arming BATCH under corrected per-ISO gates

**Session:** capx D65-B-R · **Date:** 2026-09-06 · **Branch:** `claude/capx-d65br-batch-nmrwww`
**Authority:** OWNER RULING **Q47** (*"Arm coupled, after D60-R3"*), completed under **director
adjudication r#48 §3(a)** (`capx-director-ledger-2026-08.md` §0as.3) — D65-B's G1 and G3 were
**charter defects**, the ERCOT screen is **NOT re-run**, and the batch proceeds under structural
gates re-derived per ISO from **D64 §2.4's own rows**.
**Pre-registration:** `PRECOMMIT-capx-d65b-2026-09-06.md` **Addendum C**, committed and pushed
(`5c82c9d7`) **before any batch leg solved**.

---

## 0. The verdicts

*(filled at the close of the batch)*

---

## 1. Step 0 — G2 made evaluable, at zero LP

D65-B could not evaluate its own G2 gate: `evolve_fleet` recorded a conversion as
`{unit_id, mw, from_fuel, to_fuel}` and **dropped** the `retrofit_log` that carries the island
sizing, so the seam's own identity and host band had to be reconstructed offline from CAMPD
(FINDING-capx-d65b §6.4) — the D65 §3d defect class, *a diagnostic blind to the mechanism it exists
to make visible.*

Each `ccs_retrofits` ledger row now carries the screen's own values for **`capex_scale`,
`fixed_cost_scale`, `retrofit_capex_per_mw`, `annual_net_savings_per_mw`** (the in-window uplift),
**`vom_adder_per_mwh`**, and the host's pre-conversion **`old_hr` / `old_emission_rate`**. The last
two are what remove the offline CAMPD step: the `er`/`phys` band a host-population gate is stated
over is now read straight off the bundle.

**Cache-neutral, asserted rather than argued** (this lane's batch is itself a re-key event, so a
step-0 key move would be indistinguishable from Act B's): no `ScenarioConfig` field bears any of
these names, none is a `cache_key_drop_defaults()` member, and an unarmed run writes the inert
`1.0` scales so the row shape does not depend on which gates are armed.
Guard: `test_ccs_retrofit.py::TestRetrofitLedgerCarriesTheScalingRecord` (4 cases).

## 2. Step 1 — the re-pin holds and G-DRIFT is all-INERT

**1a — 14 / 14 bare keys UNMOVED** at HEAD against PRECOMMIT §3's POST-D65B column. No
re-declaration owed, no moving hunk to name.

**1b — G-DRIFT `002cfa8d → 2485e611`, `constants.py` FIRST: ZERO hunks there** — the check a matched
cache key cannot make, because `constants.py` is outside the key. 13 files / +733−54, classified
hunk by hunk with each gate **measured**; the full table is PRECOMMIT Addendum C §C.0. The load-
bearing one: **D78's `exit_exempt_unit_ids` is INERT because the arming intersection is empty** —
the sector gate is on at **MISO alone** and MISO's D57 clearing is **off**; PJM is the converse
(clearing on, gate off) — and D78's own byte-identity test for the clearing-off case passes under
both decision rules. **Every hunk INERT, zero LIVE**, so no control solve is earned and G-CTRL
form 4 is valid.

**1c — an independent confirmation stronger than the bare-key match.** For all seven legs, undoing
*exactly the two D65-B acts* on the leg's HEAD-resolved config reproduces its **committed pre-D65-B
bundle key to the digit** (Addendum C table). So the recipe reconstructed here **is** the
incumbents' recipe, and the only thing moving each solve key is the two acts.

## 3. What this session found that was on nobody's list

### 3.1 D65-B's screen ran WITHOUT `--golden-posture`

Measured by rebuilding the screen's own HEAD (`a5c30c6a`) out of `git archive` and enumerating the
recipe grid. Both of D65-B's declared keys reproduce on the **shipped**-posture row
(arm `d0fb7534671b4c91`, control `6cfa33538294713c`) and **neither** on the golden one
(`9b9e5a48e3ca5c8e` / `0c3e9cd5b5993bdf`, which is the batch's ERCOT leg).

So the screen screened a **neighbouring config**, not the one the board's `ercot-t1f` row carries.
Consequences, recorded in Addendum C §C.1 **before the batch ran**:

1. The screen's arm-vs-same-HEAD-control differencing is **valid, for the shipped posture**, and its
   mechanism evidence is untouched — a control of 0 rows in every year reproducing D64 §2.4's ERCOT
   census, an arm of 7 rows at `er/phys` 0.9458–1.0000, the 2030 cap binding exactly.
2. **The ERCOT leg below is the FIRST golden-posture measurement of the coupled arm**, gated on its
   own rows and reported against D64 §2.4 — never netted against the screen's.
3. The ERCOT golden-posture key is **identical at `a5c30c6a` and at HEAD**, which re-confirms
   step 1b across the whole window rather than only from `002cfa8d`.

This overturns no adjudication and re-opens no gate. It is recorded because a screen that screened a
neighbouring config is a fact about the evidence.

### 3.2 Two cache-key pins were red on `main`, and they are this lane's family's debt

`test_capacity.py::test_pjm_iso_override_arms_forecast_only` and
`::test_cache_key_registration_and_backcast_coercion` fail on clean `main`. Both were written
2026-09-05 and broken the next day by **D65-B's Act B**, which is not a `_CACHE_KEY_OPTIONAL_FIELDS`
member and therefore re-keys every config unconditionally. **Measured, not assumed:** undoing the
two acts restores all four previous literals exactly, so the refresh is a re-key refresh with a
named cause and the Q44 posture each test asserts is unchanged.

## 4. The gate grader, and its validation

Addendum C's G0'/G1'/G2'/G5' are graded from **committed-shape artifacts only** (the per-year
evolution ledgers), which is the point of step 0. Validated before use against two committed D50
bundles, where it reproduces **D64 §2.3's own numbers exactly**: PJM 2029 = **2 rows / 909.8 MW**;
NEISO 2028/29/30 = **15 / 2,982.2**, **12 / 2,996.7**, **12 / 2,982.6 MW**. On those pre-step-0
bundles it correctly reports **G2' NOT EVALUABLE** — the defect step 0 removes.

## 5. The batch

*(filled per leg)*

## 6. Governance

*(filled at the close)*

# ADDENDUM to PRECOMMIT-nyiso-fuelvintage-1 — the PROMOTION leg (owner ruling §A7)

**Session:** `nyiso-fuelvintage-1` (v4 relaunch, `session_01SvrWuTXxLxC1YRf2oZcGd9`), 2026-09-09.
**Written and pushed BEFORE the composed bundle is scored.** Nothing below is chosen by a number.

---

## 1. What this addendum changes, and why

The v3 run of this session landed both zero-LP verdicts and, on the **pre-A7** guidance in
PROMPT 3 (*"If it is near-inert as predicted, LEAVE THE FLAG OFF for the rest of the session"*),
concluded: **"THE ORDERING IS RIGHT AND THE FLAG STAYS OFF."** That disposition is
**SUPERSEDED** by the owner's ruling of the same day (handoff §A7, verbatim): *"these should be
promoted as keepers on both 860 and gas shape counts **regardless of inertness**."*

**Near-inertness is now a reported property, not a reason to withhold.** So:

- `gas_electric_power_monthly_level` is **ARMED** in NYISO's keeper recipe.
- The 2019–2022 retiree window is already unconditional (an artifact, no flag) and rides in.
- The matrix cell moves **`I` → `K`**, carrying the inertness measurement forward verbatim
  rather than discarding it.

**What arming buys, stated honestly.** At HEAD it buys **nothing measurable**: the Transco Z6 hub
overlay covers 12/12 months of every year 2019–2025 and is applied last, so the seam's level has
no month to survive into, and the LP's own input arrays are byte-identical either way (§3). What
it buys structurally is a **fallback level**: in any month the hub index does not cover, NYISO's
gas would otherwise fall back to the annual trajectory × generic climatological shape, and with
the flag armed it falls back to that month's **measured** state-blended delivered cost instead.
That is the rule-19 ordering working as designed — three strictly-ordered levels, each superseding
the last — and it is why arming a measured-inert mechanism is not a no-op in principle.

## 2. The four solve shards are being run IN THIS CONTAINER, not delegated

The v3 run launched five cloud shards. **T1 (2023 2024) and T2 (2025) both completed and were
archived without pushing a branch**, so their bundles went with their containers — the rule-31
`[R-RETAIN]` failure mode the ercot-255 incident is named for, arriving by a different route
(container reclamation rather than `rm`). H1 was superseded by H1b (2021 only) after the 2020
data-block finding; H1b and H2 are still running in their own containers and cannot be messaged.

This session therefore **re-runs the solves locally**, where the artifacts survive to the end of
the session and can actually be registered. It is also cheaper: this container's `data/clean/`
tree is already built (§7 of the FINDING measures that rebuild at 30+ minutes per container).
Rule 12 `[R-PARALLEL]` is respected — **two concurrent invocations, years sequential within each**.

## 3. The measurement that lets one bundle serve both postures

Extended to the holdout years, on the **sanctioned** reconstruction
(`replay_keeper.run_year_kwargs`, the STRICT meta→kwarg mapping, not the parameter-name filter
the v3 phase-0 probe used) — `scripts/probes/nyiso_fuelvintage1_card1_holdout.py`:

| year | n_gen | max abs Δ `fuel_prices` | max abs Δ `mc_base` | verdict |
|---|---|---|---|---|
| 2021 | 870 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2022 | 873 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |
| 2023 | 870 | 0.0000000000 | 0.0000000000 | **BYTE-IDENTICAL** |

This confirms the v3 result for 2023 on a stricter reconstruction and **extends it to the two
years the validation touchpoints actually spend**, so a flag-off touchpoint and a flag-on
touchpoint are the *same solve*, measured rather than inferred from the coverage table. The
model's own 2023 log states the mechanism: *"hub-basis overlay (NYISO 2023, daily): 492 gas
generators repriced at the measured hub spot in **12/12 months**"*.

*(Correction to the v3 PRECOMMIT's §2b-equivalent reading, and to my own first pass:
`gas_plant_monthly_fuel_pricing` is **not absent** for NYISO. It is set by
`pipeline/backcast_config.py:2178` as `gas_plant_monthly_fuel_pricing=(iso != "ERCOT")`, so it is
**True for every non-ERCOT backcast** and simply never appears in a recipe or a `run_year` kwarg —
which is why a `meta.json` or `run_year_kwargs` read cannot see it. §A2's claim is right; the way
to check it is the config builder, not the recipe.)*

## 4. THE PROMOTION GATE — pre-registered, before the composed bundle is scored

The composed 2023–2025 bundle is promoted to NYISO's keeper **iff** its re-verified determination
is **not worse** than the incumbent's (`2026-09-07-nyiso-213-summer-seam`: CALIBRATED, grade 7/8,
0 fails, C3c the lone ledgered caveat), scored artifact-only via
`scripts/calibration_verdict.py --run-id <id>` with no re-solve. This is rule 22's D-5(b)
discipline applied to the promotion itself: **a worse determination STOPS the promotion and
escalates to the owner; it is never silently written.**

If the gate stops the promotion, both changes are still reported at full magnitude and the
bundles are retained (rule 31) — the owner rules, not this session.

## 5. What the committed keeper can and cannot be a control for

The v3 G-DRIFT found **two LIVE hunks** and predicted, before any solve, that the committed keeper
is therefore **not** a valid control for a `max |class-hour delta| = 0.000000 MW` claim. That
prediction is **confirmed by the 2025 solve** and quantified in the RESULT. Charter task 3 is
discharged by the v3 artifact-swap instrument, which cancels both LIVE hunks by construction —
**not** by the dispatch comparison, which cannot separate them. No control solve was spent
(rule 29(b)).

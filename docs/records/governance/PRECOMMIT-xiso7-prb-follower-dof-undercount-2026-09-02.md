# PRECOMMIT — xiso-7: the `prb_follower` DOF under-count in `build_dof_ledger`

**Written 2026-09-02, BEFORE any keeper artifact was opened.** Pushed before any
measurement in §3 was computed (the caiso-234 pre-registration tightening, kept
at caiso-235 and caiso-236).

---

## §0 — GOVERNANCE, SCOPE, AND WHAT THIS SESSION IS NOT

### §0.1 The charter object

This session takes **option B** of the three items caiso-236 handed on
(`FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md` §10.3): the DOF
ledger generator **under-counts** the free parameters of the tiered PRB coal
passthrough. Options A (the NYISO/NEISO phantom rows) and C (O-1 forecast parity,
issue #1373) are **not** taken and are left exactly as caiso-236 left them.

### §0.2 This is NOT a CAISO session and NOT a C3a session

The CAISO lane is **rested at NOT-YET by owner ruling** (caiso-201, 2026-08-17):
no further CAISO calibration session without new funded data, and the in-model
lever queue is empty. **No part of this session touches the CAISO keeper, the
CAISO configuration, any CAISO scored number, or the C3a residual.** Nothing here
is argued from a price residual; no price residual is computed. The four LIVE AND
MATERIAL CAISO residuals caiso-236 named for the owner (`offer_curve_by_group`,
the `ST_GAS 0.81` committed band, `offer_curve_smoothing`,
`battery_dispatch_adder`) are funded-object questions and are **not** touched.

### §0.3 No solve, no bundle, no dashboard registration

Scorer-only, as caiso-236 specified for this option: **zero LP solves, zero
bundles, zero scoring, zero dashboard registration**, in any year and any ISO.
Rule 15 `[R-DASHBOARD]` attaches to *completed calibration runs*; this session
produces none. No keeper changes, no promotion, no `keepers/<ISO>.json` keeper-id
edit, no `calibration-complete.json` touch, no holdout-freeze touch. Every read
stays inside committed artifacts; **no out-of-training year is solved, scored, or
registered** — CAISO holds no `complete` and no `final` marker and the holdout
freeze is ACTIVE.

### §0.4 DO-NOT-REDO (rule 28(a)) — nothing below is re-opened

The import-depth object entire (DOF `spot_capacity` permanently DECLARED NOT
IDENTIFIABLE after caiso-233/234/235); the price Q-Q route
`derive_caiso_import_tranches.py` and all five priced rungs including the two firm
ones; re-grounding CC_CHP / CT_CHP / ST_GAS or the two committed bands
(caiso-230/231); `caiso_solar_cap_at_delivered`; `ramp_envelopes`;
`caiso_corridor_export_path`; `caiso_p1_export_sink_seam`;
`caiso_da_rt_two_settlement`; `cc_committed_offer_margin`; `storage_daily_cycling`;
the sub-zonal congestion route (CEII-blocked). **`caiso_bidir_intertie` does not
exist** — deleted at caiso-236 under rule 26 `[R-DELETE]` and registered in
`scenarios._CACHE_KEY_RETIRED_FIELDS`; it is not re-added and not "restored". The
two standing owner objects (PS water-state; the 8,800 MW re-open) are untouched.

### §0.5 Why an under-count is worth a session when caiso-236's over-count fix was safe

caiso-236's fix could **only remove** over-counted rows. An over-count is the
*conservative* direction: the attestation claims more free parameters than exist,
which is embarrassing but never misleads a reader about how much of the model is
fitted. **An under-count is the dangerous direction** — the keeper's rule 21
`[R-DOF]` attestation states *fewer* free parameters than the solve actually
consumes, which is precisely the disclosure failure rule 21 exists to prevent.
That asymmetry, not the size of the number, is this session's justification.

---

## §1 — ESTABLISHED FROM SOURCE AT PRE-REGISTRATION TIME (not predictions)

These are code reads made while scoping, **before** this document was written and
before any keeper artifact was opened. They are recorded here as *established*,
NOT scored as predictions, so that §3's predictions are honestly separated from
what was already known.

* **E-1.** `prb_follower` has **no toggle of its own**. Its gate is the
  conjunction `coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered`
  (`src/market_sim/data/fleet/assembly.py:1774`); when it fires, PRB plants whose
  per-plant must-run floor is `<= coal_prb_follower_mustrun_max` swap the baseload
  prb series for the follower series.
* **E-2.** `prb_follower_passthrough_series` (`data/fuel/trajectories.py:363`)
  calls `coal_sigmoid_params(config, "prb_follower")`, which resolves
  `COAL_SIGMOID_DEFAULTS[(ISO, "prb_follower")]` overlaid by any explicitly-set
  `coal_prb_follower_{floor,ceil,gas_mid,gas_slope}` field, and returns `None`
  (falling back to the baseload prb curve, **no new DOF**) when the four-parameter
  set is incomplete.
* **E-3.** `COAL_SIGMOID_DEFAULTS` holds exactly two `prb_follower` keys —
  `("ERCOT", "prb_follower")` (floor 0.68 / ceil 1.35 / gas_mid 2.85 / gas_slope
  2.5, `scenarios.py:15186`) and `("MISO", "prb_follower")` (floor 0.598 / ceil
  1.0 / gas_mid 3.187 / gas_slope 2.5, `scenarios.py:15266`) — and in **both**
  cases at least one value differs from that ISO's baseload `prb` row, so the
  follower set is a genuinely distinct four-parameter surface, not an alias.
* **E-4.** `scripts/build_dof_ledger.py::config_entries` enumerates **only** the
  five `coal_*_passthrough_sigmoid` toggles and emits
  `n_scalars = 4 * len(sigmoids)`. `coal_prb_passthrough_tiered` appears nowhere
  in the generator, and `prb_follower` appears nowhere in
  `_COAL_SIGMOID_TOGGLE_SUPPLY`. **The under-count is therefore structural in the
  generator, independent of any keeper.**
* **E-5.** `scripts/data/derive_coal_sigmoid.py` **does** emit a `prb_follower`
  row (lines 328-341: "PRB baseload also spawns the low-must-run follower tier").
  So for **MISO** — the one ISO whose `COAL_SIGMOID_DEFAULTS` row the ledger
  already classes `measured-physical` on the strength of that frozen derive script
  — the follower four-set carries the *same* provenance as the baseload four-set.
* **E-6.** `coal_prb_passthrough_tiered` defaults to `False`
  (`scenarios.py:8480`) and is cache-key group 3 (`scenarios.py:15728`), as are
  all five `coal_prb_follower_*` fields (`scenarios.py:15729-15733`).

---

## §2 — THE INSTRUMENT

`scripts/probes/_xiso7_prb_follower_dof_probe.py`, written for this session. It:

1. reads each of the six designated keepers' `run_config.json` from its committed
   bundle (identity taken from `frontend/data/backcast/keepers/<ISO>.json`);
2. evaluates, per keeper, the three-part gate of E-1/E-2 — `sigmoid` armed,
   `tiered` armed, `("ISO","prb_follower")` resolving under the same overlay rule
   the solve uses;
3. reports, per keeper, the committed ledger's `n_entries` / `n_residual` /
   sigmoid-row `n_scalars`, the generator's current output, and the generator's
   output **after** the fix;
4. reports `coal_prb_follower_mustrun_max` per keeper and whether any ledger row
   accounts for it.

It **writes nothing** and solves nothing. Raw output is committed as
`results/calibration/_xiso7_prb_follower_dof.json`.

---

## §3 — PRE-REGISTERED PREDICTIONS (scored in the FINDING, misses included)

* **P-1 — incidence.** Exactly **one** of the six designated keepers arms the full
  E-1 gate and resolves a follower set. **Predicted: MISO only**
  (`2026-09-01-miso-198-oomlevel`), with **ERCOT NOT affected**.
* **P-2 — why ERCOT is predicted out.** ERCOT's keeper
  `2026-08-25-234-eastex-identity` is predicted to arm
  `coal_perplant_offer_curves`, whose armed harness "strips the COAL_* groups from
  `offer_curve_by_group` and **disarms the sigmoids**"
  (`build_dof_ledger.py:339-344`), so ERCOT is predicted to carry **no**
  `COAL_SIGMOID_DEFAULTS[ERCOT]` row at all and the follower count is moot there.
  *(This prediction is deliberately at risk: caiso-236 §10.3 named ERCOT **and**
  MISO as under-counting lanes. If P-2 holds, caiso-236's §10.3 ERCOT half was
  itself wrong, and this document says so.)*
* **P-3 — magnitude.** On each affected keeper the correction is exactly
  **+4 scalars**, and **+0 entries** — i.e. it lands as a bump to the existing
  `COAL_SIGMOID_DEFAULTS[<ISO>]` row, not as a new row.
* **P-4 — identification class.** Because of E-5, the four added MISO scalars are
  **`measured-physical`**, not `residual`: `n_residual` does **not** move, and
  MISO's keeper gains **no** new residual DOF. *(Predicted consequence: the
  under-count is real but is a disclosure defect, NOT a hidden fitted surface.)*
* **P-5 — a second uncounted scalar.** `coal_prb_follower_mustrun_max` is engaged
  by the same gate, is counted by **no** ledger row, and is therefore a second
  uncounted parameter. **Predicted: it is uncounted (TRUE), and the affected
  keeper carries the DEFAULT 25.0** — i.e. latent, never tuned.
* **P-6 — regeneration safety.** The affected lane's committed ledger is
  generator-STALE beyond this correction (caiso-236 §7 measured MISO at 38
  committed vs 25 generated, the excess being rows the lane hand-adds), so a full
  `build_dof_ledger.py` regeneration would **destroy** hand-added rows. **Predicted:
  stale, regeneration UNSAFE, surgical route taken** (§4(c)).
* **P-7 — no collateral movement.** With the fix applied, re-running the generator
  against all six keepers changes the generated ledger of **no ISO except the
  affected one(s)**: same `n_entries`, same `n_residual`, same per-row `n_scalars`
  everywhere else.
* **P-8 — gates.** `scripts/audit_keepers.py --iso <affected>` PASSes **before and
  after**; `scripts/check_mechanism_matrix.py` passes; `tests/unit` shows **no new
  failures** beyond the 13 baselined at `origin/main`.

---

## §4 — DECISION RULE, FIXED IN ADVANCE

* **(a) The generator fix lands regardless of P-1's outcome.** Counting a
  parameter set the solve demonstrably consumes is a correctness fix in
  lane-neutral infrastructure (the same standing caiso-236's own fix had), so it
  lands with a unit test **even if no current keeper is affected**. If P-1 returns
  the empty set, the FINDING reports that null and the fix is defensive only.
* **(b) Form of the fix.** Count the follower four-set **only** when all three of
  E-1/E-2 hold — `coal_prb_passthrough_sigmoid` armed **and**
  `coal_prb_passthrough_tiered` armed **and** `("ISO","prb_follower")` resolving
  under the overlay rule. This mirrors `_coal_sigmoid_resolves` exactly and, like
  it, can never attest a parameter the solve does not consume.
* **(c) Ledger application is SURGICAL, never a regeneration**, wherever the
  committed ledger is stale beyond this correction (P-6). "Surgical" means: change
  the `n_scalars` (and the row's engaged-via/source text) on the **one** row the
  corrected generator itself would now emit differently, and change **nothing
  else** — no other row, no verdict, no gate, no determination, no keeper id. If
  the committed ledger turns out to be generator-CURRENT, regenerate instead
  (cheaper and self-verifying).
* **(d) Rule 25 `[R-ISO-SCOPE]` disposition, stated in advance.** caiso-236 left
  NYISO's and NEISO's phantom rows alone because those are **over**-counts —
  conservative, harmless to a reader. This session corrects an **under**-count,
  the direction that actively misstates a keeper's fitted surface, and does so by
  importing **no value across any ISO boundary**: an `n_scalars` correction moves
  no parameter, no curve and no verdict. Should the affected lane's owner prefer
  the correction re-done in-lane, the surgical form (c) is trivially revertable in
  one hunk. The affected lane's `docs/calibration-log/<iso>.md` records the edit,
  and `docs/calibration-log/governance.md` records the cross-cutting audit.
* **(e) STOP conditions.** If applying the fix would move any keeper's
  **determination**, any **gate verdict**, any **scored number**, or `n_residual`
  in a way that adds a residual DOF to a lane that is not this session's to fund —
  the session **stops**, applies nothing, and reports. A DOF-ledger audit may
  correct a count; it may never change what a keeper claims to have achieved.

---

## §5 — WHAT THIS SESSION WILL NOT DO

* No LP solve, no scoring, no bundle, no dashboard registration (§0.3).
* No mechanism proposed, tested, re-opened, or re-verdicted; no
  `ScenarioConfig` field added or removed; therefore **no mechanism-matrix cell
  moves** (`check_mechanism_matrix.py` is run to confirm green, not to record a
  verdict).
* No CAISO artifact, config, or number touched (§0.2).
* Nothing in §0.4 re-opened.
* **No number in the FINDING will be a price residual, and no conclusion will
  depend on one.**

*Session xiso-7. Successor object of
`FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md` §10.3.*

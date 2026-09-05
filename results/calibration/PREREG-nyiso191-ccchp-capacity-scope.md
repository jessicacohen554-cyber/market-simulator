# PRE-REGISTRATION — nyiso-191: the `CC_CHP` scope extension of `cc_capacity_reconcile` — and the DISCLOSURE, before any solve, that the object the handoff named is **NOT the object this mechanism reaches**

**Session:** nyiso-191, NYISO backcast-calibration track, 2026-09-05.
**Branch:** `claude/nyiso-191-ccchp-capacity-scope`, fresh off `origin/main` at
`c234d4da` (carries PR #4759 the nyiso-190 finding, PR #4760 the capx D59
`locality_capacity_curves` row, PR #4765).
**Keeper at entry:** `2026-09-05-nyiso-189-steam-identity` — CALIBRATED, grade 7,
fails 0, C3c ledgered; C1-2024 `CC_REGULAR` +3.33 TWh / +2.8 pp against a
±3.82 TWh / 3.0 pp band (headroom 0.49 TWh / 0.2 pp).
**Markers: D56 HAS LANDED.** `complete.NYISO` exists at this HEAD, already keyed
to the current keeper `2026-09-05-nyiso-189-steam-identity`, with its
determination re-verified without a solve by the D56-R records lane, and
`scripts/audit_keepers.py --iso NYISO` PASSes (M1 clean). **The rule-22 D-5(b)
duty is therefore already discharged and this session re-keys nothing.** The
validation tier (2020–2022) is authorized by that marker; **this session solves
training years only (2023–2025) and requests no marker.** `final` is empty; the
locked-test freeze is active.

**THIS DOCUMENT IS COMMITTED AND PUSHED BEFORE THE DERIVE IS EDITED AND BEFORE
ANY SOLVE OF THIS SITTING.** No LP artifact of this sitting exists at the time
of writing.

---

## §0 — DISCLOSURE 1: THE HANDOFF'S PREMISE IS REFUTED, AND IT IS REFUTED BEFORE THE BUILD

The nyiso-190 handoff opened this session on three named plants — Sithe
Independence 54547 (+3.19 TWh over its measured 2024 output), Brooklyn Navy
Yard 54914 (held at ≥95 % of nameplate for 6,200–8,200 h/yr against zero
measured hours) and Empire 56259 — on the reasoning that
`cc_capacity_reconcile`'s `CC_REGULAR` scope filter is what keeps the mechanism
off them. **Phase 0 (`scripts/probes/nyiso191_ccchp_scope_phase0.py`, NO LP,
every constant imported frozen from the derive) shows the frozen population rule
reaches NONE of the three:**

| plant | model cap (MW) | CAMPD p99.9 (MW) | what the frozen rule does | why |
|---|---|---|---|---|
| **Sithe Independence 54547** | 1,157.8 | **1,170.0** | **RAISE +1.1 %** | its demonstrated peak *exceeds* model capacity — there is no phantom capacity to cap |
| **Brooklyn Navy Yard 54914** | 322.0 | 234.0 | **SKIP** | CT-only CEMS reporter (EIA-923 net > 1.1× CAMPD gross) — the frozen `_CT_ONLY_RATIO` guard declines it, correctly |
| **Empire Generating 56259** | 653.7 | 626.9 | **no row** | 1.043× — inside the frozen `_CAP_MARGIN` of 1.10 |

**The consequence is a correction to the record, stated here rather than
discovered later:** Sithe's +3.19 TWh over-run is **NOT a capacity defect**. The
plant demonstrably reached 1,170 MW; the model's error is that it runs it at an
annual CF of 0.93 against a measured 0.62 — a **duty / availability** defect,
which a capacity bound cannot fix and which this mechanism would very slightly
*worsen* (the raise row). That object is re-queued in §5, not addressed here.

## §0b — DISCLOSURE 2: WHAT THE WIDENING *DOES* REACH, AND THAT IT IS MEASURED IN ADVANCE TO BE NEARLY ENERGY-INERT

Widening the screened class set from `("CC_REGULAR",)` to
`("CC_REGULAR", "CC_CHP")` adds **8 rows and loses none** (15 → 23):

| plant | model → reconciled MW | Δ | mode |
|---|---|---|---|
| Selkirk Cogen 10725 | 753.8 → 378.0 | −49.8 % | cap |
| Lockport Energy Associates 54041 | 221.3 → 142.3 | −35.7 % | cap |
| Indeck Yerkes 50451 | 84.8 → 54.6 | −35.6 % | cap |
| World Generation X 54131 | 65.7 → 45.8 | −30.3 % | cap |
| Indeck Oswego 50450 | 75.4 → 58.5 | −22.4 % | cap |
| CH Resources Beaver Falls 10617 | 107.8 → 84.6 | −21.6 % | cap |
| Indeck Olean 54076 | 90.6 → 80.9 | −10.7 % | cap |
| Sithe Independence 54547 | 1,157.8 → 1,170.0 | +1.1 % | raise |

**Net −542.5 MW of LP capacity.** Measured against the keeper's own registered
per-plant hourly dispatch, the model energy sitting **above** these proposed
caps is **0.0000 / 0.0143 / 0.0000 TWh** in 2023 / 2024 / 2025 — the whole of it
at World Generation X in 2024 (6,145 hours marginally above a 45.8 MW cap). Six
of the seven capped plants never come within 2–3× of their cap in any hour of
any year (Selkirk's model maximum is 156 MW against a 378 MW cap; Lockport's 49
against 142). **So the arm is expected, on evidence gathered before it is built,
to be very nearly energy-inert, and it CANNOT close the C1-2024 `CC_REGULAR`
cell** (0.014 TWh against a +3.33 TWh miss).

**Why it is still run, stated before the result:** the license is **rule 14
`[R-ACCURATE]` plus rule 13's forward test**, not the residual. Six plants carry
20–50 % of LP capacity above anything they have ever demonstrated; that is a
misrepresentation of measured capability whether or not it binds in a backcast
year, and it **would** bind in a forecast year in which those plants become
economic. Removing phantom capacity regenerates from any CAMPD vintage and
responds to changed conditions. Under rule 1 `[R-STRUCT]` the reason to run this
is that the model carries capability the plants do not have — **never** what it
does to a gate. Second-order effects are the genuine open question the A/B
answers: capacity sets every tranche's MW (`pct_mr`/`pct_mc`/`pct_econ`/
`pct_peak`), so the offer-curve *shape* and the reserve-eligible MW move even
where energy does not.

## §0c — Everything else read

`docs/FINDING-nyiso190-cc2024-displacement-provenance-2026-09-05.md` (§§2–6);
`docs/DECISION-CARD-nyiso190-cc2024-cell-disposition-2026-09-05.md` §4;
`results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md` §5;
`docs/FINDING-nyiso188-astoria-footprint-cc-reconcile-bethlehem-2026-09-04.md` §3;
`docs/mechanism-testing-matrix.md` §5.5; NYISO shard cells
`cc_capacity_reconcile` (K), `scuc_load_pocket_commitment` (G),
`egrid_steam_collapse_heat_rates` (K); CLAUDE.md rules 1, 5, 12–16, 19, 21–25,
27, 28. **Code read in full:**
`scripts/data/derive_cc_capacity_reconcile.py` (every constant and both screen
branches); `src/market_sim/data/fleet/campd_bins.py::_reconcile_cc_capacity`
(the apply — **keyed on `plant_code` only, class-agnostic, so NO apply-side
change is needed**) and its `fleet_to_bins` call site;
`campd.DEFAULT_PARASITIC_LOAD_PCT` (**`CC_CHP` = 0.025, identical to
`CC_REGULAR`**, so the derive's `_CC_NET_OF_GROSS` = 0.975 is already the right
net-of-gross factor for the widened class and **no constant is added**);
`cc_summer_derate_ratio` / `cc_summer_capacity` (confirmed to cover the CHP
plants — Sithe, Empire, BNY all present, so the summer-derate rescale works
unchanged).

**Structural safety check, measured (no LP):** the apply is keyed on
`plant_code` while `fleet_to_bins` emits **one row per (plant, class)**, so a
cap row on a multi-class plant would cap its other classes too. **In NYISO this
hazard does not exist** — no plant carries both `CC_REGULAR` and `CC_CHP`, and
every `CC_CHP` plant is pure-play (share ≥ 0.96; the only non-1.00, Riverbay
52168 at 0.96, is declined anyway by the CT-only guard). The latent hazard is
recorded in §5 for other ISOs; it is **not** fixed here (rule 19: one change per
sitting, and no other ISO's artifact is touched).

---

## §1 — THE BUILD (exactly what changes)

**One derive, no new mechanism, no new `ScenarioConfig` field.**
`cc_capacity_reconcile` is ALREADY `True` on the keeper; what changes is the
committed **artifact** it reads. Concretely, in
`scripts/data/derive_cc_capacity_reconcile.py`:

1. `_model_cc_capacity(iso, year)` gains a `classes: tuple[str, ...]` parameter
   in place of the hard-coded `"CC_REGULAR"` comparison; the pure-play share is
   measured over that same set (unchanged semantics at the default).
2. A `--classes` CLI argument, **defaulting to `CC_REGULAR`** — so every other
   ISO's committed table (`CAISO`, `ERCOT`, `MISO`, `NEISO`, `PJM`) re-derives
   **byte-identically** at HEAD (rule 25 `[R-ISO-SCOPE]`: nothing crosses an ISO
   boundary, and no other ISO's artifact changes).
3. The raise-mode `Plant_Group` filter and the log strings read the same set.
4. Each row gains a `plant_group` column (provenance; the apply ignores unknown
   columns, so this is additive and backwards-compatible).

**ZERO new constants, ZERO retuned constants, ZERO new DOF entries.** Every
threshold — `_CAP_MARGIN` 1.10, `_MIN_DELTA` 0.01, `_PURE_PLAY_CC_SHARE` 0.90,
`_CT_ONLY_RATIO` 1.1, `_CAP_FEASIBLE_CF` 0.90, `_CC_NET_OF_GROSS` 0.975 — is the
frozen one, unmodified, and each is asserted equal to its pre-change value by
the phase-0 record. **NYISO's committed invocation becomes**
`--iso NYISO --mode both --classes CC_REGULAR CC_CHP --years 2023 2024 2025`.

---

## §2 — THE A/B

**Control:** same-HEAD replay of the keeper on committed artifacts —
`scripts/replay_keeper.py 2026-09-05-nyiso-189-steam-identity --out-dir
results/calibration/nyiso191_control --years 2023 2024 2025`.
**Arm:** the identical recipe with only the re-derived
`cc_capacity_reconcile_NYISO.csv` in place —
`results/calibration/nyiso191_ccchp_scope`. Years sequential within each
invocation, the two invocations concurrent (rule 12). One bundle each, all three
years (rule 16).

**G-DELTA (the pre-registered identity of the change):** the ONLY difference
between control and arm is the reconcile table, and that table must differ from
the committed one by **exactly the 8 rows of §0b** — the 15 existing rows
byte-identical in `plant_code`, `reconciled_mw` and `mode`. Any other row
movement is a **stop**: it would mean the class widening perturbed the
`CC_REGULAR` screen, and the arm is abandoned until root-caused.

---

## §3 — THE BARS (fixed before the derive is edited)

**V1 — control identity.** The control must be **bit-identical** to the keeper
(0 of 52,560 hourly zonal prices differing in each year). If not, the instrument
is not the keeper and every bar below is reported UNEVALUABLE.

**V2 — other-ISO invariance.** Re-running the derive at the DEFAULT `--classes`
for each of ERCOT / CAISO / MISO / NEISO / PJM must reproduce that ISO's
committed table byte-for-byte on `plant_code`, `reconciled_mw`, `mode`. A
mismatch is a stop (rule 25).

**B1 — ENGAGEMENT.** The arm's fleet must carry the 7 capped plants at their
reconciled MW and Sithe at 1,170.0 MW. Verified on the arm's own fleet build.
Not engaged ⇒ the arm is **INERT**, reported as such (matrix `I`), never as a
pass.

**B2 — MY OWN PREDICTION, FALSIFIABLE.** Phase 0 predicts ≤ 0.05 TWh of NYISO
total-generation redistribution attributable to the caps.
> **If |Δ NYISO total fossil generation| > 0.05 TWh in any year, my phase-0
> reasoning was WRONG.** The arm is then not reported as "accurate but inert";
> the discrepancy is root-caused first (rule 11), and no promotion claim is made
> until it is explained.

**B3 — THE GATES (the rejection rule).** The arm is **REJECTED** iff any of
**C2 / C3a / C3b / C8** flips PASS → FAIL. Per the owner ruling carried into
this session, **C1-2024 `CC_REGULAR` flipping PASS → FAIL is NOT an automatic
rejection** — it is reported at full magnitude alongside the structural-integrity
evidence and the promote/reject call goes to the owner, never decided here on the
residual.

**B4 — STRUCTURAL INTEGRITY (the actual license).** Reported whatever the gates
do: (a) total phantom LP capacity removed (MW, and as a share of the affected
plants' capacity); (b) `scripts/probes/nyiso190_plant_grain_posthoc.py` re-run
against the arm — the per-plant over/under table and the gross-misallocation
total, control vs arm; (c) each capped plant's model annual CF before and after,
against its measured CF.

---

## §4 — PRE-COMMITTED OUTCOMES

* **B1 engaged, B2 holds, B3 no flip** → a keeper candidate on rule 14
  `[R-ACCURATE]` + rule 13 (forward-regenerating measured capability), with the
  near-inert energy effect stated as the headline, not buried. Recommendation
  made under the owner's standing formula; the promotion is executed only if the
  recommendation is *promote*.
* **B1 not engaged** → reported **INERT**; matrix cell records the widening as
  tested-and-inert; no promotion.
* **B2 falsified** → root-cause before any claim; the arm is not registered as a
  candidate until the extra movement is explained.
* **B3 flip in C2/C3a/C3b/C8** → **REJECTED**, reported at full magnitude with
  the structural evidence; no promotion under any reading.
* **C1-2024 flip only** → reported at full magnitude, structural integrity
  stated, call put to the owner.

Every arm solved is registered on the dashboard whatever the outcome (rule 15),
the matrix cell + evidence updated in this session (rule 28), and a bit-identical
control added to `check_registry_payload_parity.KEEP_REQUIRED`.

---

## §5 — STOPS, and what is NOT touched

* **S1** — no second mechanism. Only the derive's class scope changes; no
  `ScenarioConfig` field is added, and no other flag moves (rule 19).
* **S2** — **Sithe's duty defect is NOT addressed.** §0 shows it is not a
  capacity object. It is measured and re-queued; no availability, outage or
  duty lever is built here.
* **S3** — no other ISO's artifact is re-derived or committed (rule 25). V2
  proves invariance; the tables themselves are not rewritten.
* **S4** — the `plant_code`-keyed apply's multi-class hazard is **recorded, not
  fixed** — it does not arise in NYISO, and fixing it would be a second change
  in one sitting.
* **S5** — C3a-2025 (−8.3 %) is `DECISION-CARD-nyiso148` Q1, owner-court,
  untouched. Cell **G** (`scuc_load_pocket_commitment`) stays `G`; nyiso-97 §5
  and the nyiso-160 access closure stand.
* **S6** — **no marker is requested**, no holdout year is solved, scored or
  registered; 2023–2025 only. D-5(b) is already discharged (§ header) and this
  session re-keys nothing.
* **S7** — object 2 of the handoff (the `ST_GAS` internal misallocation:
  Ravenswood +1.74 / Arthur Kill +0.78 over vs Northport −1.78 / Bowline −0.92
  under) is a **measurement only** if solve budget remains, and no lever is
  proposed from it in this session.

## §6 — GOVERNANCE

Rule 1: bars and outcome branches fixed and pushed before the derive is edited
and before any solve; the phase-0 refutation of the session's own premise is
disclosed here rather than after the result. Rule 5 / 21 / 24: zero new
constants, zero retuned constants, zero new DOF entries, no off-registry
channel — the widening is a scope argument to an existing frozen rule. Rule 13:
the demonstrated peak regenerates from any CAMPD vintage and responds to changed
conditions. Rule 14: the license. Rule 19: one mechanism, one change. Rule 23:
the derive re-derives on a source-data (or, here, an explicit scope) change, and
the change is cited. Rule 25: `--classes` defaults to the current behaviour so
no other ISO moves; V2 proves it. Rules 15 / 28: registration and matrix duties
discharged in this session. Rule 27: on-disk bytes pushed, every ≥300-line blob
verified after each push.

*(nyiso-191, 2026-09-05. Pushed before the derive was edited and before any solve.)*

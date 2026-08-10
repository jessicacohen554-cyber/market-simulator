# FINDING — ercot-186: the rule-18 grain defect is CONFIRMED, is WORSE than the card described, is NOT inert — and the session's own pre-registered stop rule fired

**Session ercot-186, 2026-08-10, HEAD `fe9fa97f`. ERCOT only (rule 25).**
Authorization: owner sitting 2026-08-09, decision card **D3 option (ii)**
(`docs/DECISION-CARD-ercot182-c3a2023-reachability-2026-08-09.md` §4(b2) + §10),
sequenced after D2 — which landed as the current keeper.

Pre-registration: `docs/PRECOMMIT-ercot186-rule18-grain-2026-08-10.md`, pushed
at `2e8f879e` **BEFORE** any measurement or solve.

Keeper at session start and at session end, **unchanged**:
`2026-08-09-ercot185-shaped-partial` (bundle
`results/calibration/ercot185_shapedarm_B`), **NOT-YET {C3a-2023, C3b-2023}**.

> **NO RUN WAS SOLVED AND NO RUN WAS REGISTERED.** Stated up front so the
> absence is never read as a skipped registration (rules 15/16 — the ercot-175
> §0 / ercot-176 Amendment-3 precedent): the precommit's own decision rule
> fired before the A/B, and this session honoured it. Nothing was solved, so
> there is nothing to put on the dashboard. See §4.

---

## 1. Headline

| | result |
|---|---|
| **The defect is REAL** | SP-2: the shipped row-grain gate rejects **0 of 486 / 486 / 497** CT bid rows. It is vacuous in all three years, exactly as card D3 stated. |
| **The defect is WORSE than described** | SP-1 (FAILED): **40 of 219** plant prefixes record their physics on **no row at all** — not merely on the committed row only. |
| **The repair is NOT inert** | SP-4: 2023 moves **76,845 row-hours**, **173 → 168** rows priced, max markup delta **$1,709.62/MWh**. 2024/2025 array-equal. |
| **The standing prior is FALSIFIED** | The matrix note's *"CT physics is uniform at min-down 1 h"* is wrong: 2023 carries a CT plant at **8 h**. |
| **Session outcome** | **STOP at the seam proof, per the precommit's own §3/§7 rule.** No A/B, no registration, keeper untouched, matrix cell stays `O`. |

The code substrate is merged, **default-off and inert at default** — SP-5 proves
nothing reads the new fields but the licensing gate, and SP-2 proves the shipped
gate is byte-unchanged with the flag off.

---

## 2. What was measured

`results/calibration/ercot186_grain_seamproof.json`, probe
`scripts/probes/ercot186_grain_seamproof.py`, run on the **real keeper fleet**
for 2023/2024/2025 with no LP built (rule 22: no year outside {2023, 2024, 2025}
was touched).

### 2.1 SP-2 — the defect, confirmed on the object

| year | CT bid rows in the pool's universe | rejected by the shipped row-grain gate |
|---|---|---|
| 2023 | 486 | **0** |
| 2024 | 486 | **0** |
| 2025 | 497 | **0** |

The gate is `skip if min_down_hours > FASTSTART_POOL_MIN_DOWN_HOURS`, evaluated
on rows that all read `min_down_hours = 0`. It is False for every row it can
reach. Its only real filter is its row universe — `{"CT_PEAKER"}` — i.e. the
hard-coded class tuple rule 18 `[R-PHYSICS]` forbids. Card D3's statement of the
object is **verified**, and the ercot-176 §5 annotation carried since 2026-08-07
was accurate as far as it went.

### 2.2 SP-1 — FAILED, and the failure is the finding

Pre-registered claim: the stamped plant physics equals the ercot-176
Amendment-2 read (`max over the plant's rows of min_down_hours`) for every
prefix. **Falsifier: any prefix where they differ.**

**It fired: 40 of 219 prefixes diverge, identically in all three years.**

| group | mismatching prefixes | of which have a `committed` tranche |
|---|---|---|
| CC_CHP | 19 | 0 |
| CT_CHP | 17 | 0 |
| ST_CHP | 2 | 0 |
| CC_REGULAR | 1 | 0 |
| CT_PEAKER | 1 | 0 |
| **total** | **40** | **0** |

The cause is mechanical and single. Assembly drops any tranche whose capacity
is `<= 0.5` MW (`if cap <= 0.5: continue`). A plant whose committed band is
below that threshold — every CHP-dominated plant, whose capacity sits in
`mustrun` — therefore emits **no committed row**, and since the committed row is
the *only* row assembly stamps the physics tags on, that plant's physics is
recorded **nowhere in the fleet**. The ercot-176 read returns `0` for it.

So the grain defect has **two facets**, and D3 named only the first:

1. *(named)* physics on the committed tranche only ⇒ a bid-row gate reads 0;
2. *(new, measured here)* **for a plant with no committed tranche, the physics
   is not in the fleet at all** ⇒ *any* read that recovers it from the rows —
   including ercot-176's — returns 0.

The stamp does not depend on which tranches survive, so it repairs both. That
is a *better* construction than the one SP-1 asserted equivalence to; it is
still a falsified assertion, and §4 treats it as one.

### 2.3 SP-3 / SP-3b — the corrected gate's measured scope

| year | CT plants | eligible | **excluded** | plant min-down histogram |
|---|---|---|---|---|
| 2023 | 65 | 64 | **1** | 1 h ×63, 2 h ×1, **8 h ×1** |
| 2024 | 65 | 65 | 0 | 1 h ×64, 2 h ×1 |
| 2025 | 66 | 66 | 0 | 1 h ×65, 2 h ×1 |

The single exclusion is **`CT_PEAKER_South_Central_p6243`**, assembled min-down
**8 h** and min-run **8 h** — four times the tier's 2 h SCED-startable bound. It
is a CT-classified plant whose measured commitment physics is not a CT's.
**The bound was not moved to recapture it**, and will not be: it was fixed ex
ante at the existing constant and the ercot-176 precedent (17 CC plants
deliberately not recaptured) is the standing discipline.

**SP-3b, the decisive scoping fact for the successor:** over the pool's own row
universe the two candidate reads differ on exactly **one** prefix
(`CT_PEAKER_Houston_p7325`, stamped 2 h vs row-read 0 h) and **both are ≤ 2 h**,
so they reach the **same eligibility set in every year**. The SP-1 divergence is
therefore **not separable on this gate's object** — it changes no gate outcome
here. It matters for any *future* tier with a lower bound (ercot-176's `[4, 8]`
band is exactly such a tier), which is why it is recorded rather than waved
through.

### 2.4 SP-4 — the repair is NOT inert, and the falsified prior

| year | armed == control | row-hours changed | rows priced (control → armed) | max markup delta |
|---|---|---|---|---|
| 2023 | **False** | 76,845 | **173 → 168** | **$1,709.62/MWh** |
| 2024 | True | 0 | 173 → 173 | 0.0 |
| 2025 | True | 0 | 91 → 91 | 0.0 |

Pre-registered prediction **P-2** — the standing on-the-record prior, quoted
from the matrix note (*"not currently believed to change WHICH rows are
priced (CT physics is uniform at min-down 1 h), so this is a loss of PROTECTION,
not a known mis-scoping"*) — is **FALSIFIED for 2023**. The mis-scoping is real,
not merely a lost protection.

**No claim is made about the direction of the price effect**, and none may be
inferred from the table. Composition is *replace-by-mask*: withdrawing pool
ownership of five rows returns those row-hours to the other surfaces' markup,
which is not ordered against the pool's by construction. **The sign is
unmeasured because nothing was solved.**

### 2.5 SP-5 — the source-side stamp is inert

`FleetArrays` carries no attribute of either name, and the only source readers
anywhere under `src/` are the model declaration (`fleet/__init__.py`), the
writer (`fleet/assembly.py`) and the licensing read
(`fleet/offer_surfaces.py::_plant_unit_physics`). A field nothing else reads
cannot move an array. PASS in all three years.

---

## 3. What was built (merged, default-off)

* `Generator.plant_min_run_hours` / `plant_min_down_hours` — the plant's own
  assembled physics, stamped by `assembly.py` on **every** tranche row. The
  UC-coupling tags `min_run_hours`/`min_down_hours` are **untouched**, so no bid
  tranche acquires commitment coupling (assembly's own standing constraint).
* `fleet/offer_surfaces.py::_plant_unit_physics` — the ercot-176 Amendment-2
  per-plant read generalized to a shared helper, reading the **max of both**
  fields.
* Both fast-start pool bodies (stepped, and the ercot-178/180 `contpct` body)
  evaluate the **same unchanged bound** `FASTSTART_POOL_MIN_DOWN_HOURS = 2.0` at
  plant grain under `ScenarioConfig.ercot_faststart_pool_plant_physics`
  (default off).
* **Zero new fitted scalars** (G-DOF by construction). No min-run bound added.
  No artifact re-derived — rule 23 is not engaged at all: this session changes
  only *which rows are licensed to read* a frozen artifact.
* Cache-key registered dropped-at-default: default key **`603c2498bf71d21d`
  unmoved**, armed key **`7ae1afee3aa73a63`** distinct.
* Four trivial-case tests, including one that pins the *defect* (a slow plant's
  bid rows priced anyway at default) and one that pins the no-committed-tranche
  case SP-1 surfaced.
* **The flag is TRANSITIONAL.** Once a keeper carries it armed, the flag and the
  pre-repair branch should be deleted outright (rule 26 `[R-DELETE]`) — it is an
  A/B switch, not a standing option. Named here so it is not left to rot.

---

## 4. WHY THIS SESSION STOPPED

The precommit, §3 and §7 step 1:

> *"**Any SP falsifier fires ⇒ stop, report, register nothing.**"*
> *"SP-1 … SP-5 all PASS — else stop, report, register nothing."*

SP-1's falsifier fired. **No A/B was solved and no run was registered.**

Three things make that the right call rather than a technicality, and they are
stated in ascending order of importance:

1. **The alternative is self-refuting.** This session's entire object is a
   licensing gate that does not bind. Reasoning past a gate of my own that *did*
   bind — on the ground that I had already seen the outcome and liked the look
   of it — would reproduce the exact failure being repaired.
2. **The amendment route was closed by timing.** The ercot-176 precedent allows
   a pre-solve amendment when a seam proof surfaces a structural code fact
   (Amendment 2 did exactly that). But ercot-176's amendment was written *before
   any measurement of its arm*; here SP-4 landed in the same probe run, so any
   amendment I wrote would be authored with the arm's effect already known.
   That is the contamination pre-registration exists to prevent, and knowing
   SP-3b makes it *worse*, not better: I would be amending an assertion whose
   failure I had already established changes nothing about my preferred answer.
3. **The stakes are precisely where ERCOT is weakest.** The arm is inert in
   2024 and 2025 and moves **only 2023** — the single year carrying **both** of
   ERCOT's failing criteria (C3a-2023 −32.5 %, C3b-2023 0.602). A 2023 price
   number produced under a contract whose stop rule had already fired is a
   number nobody should rely on, least of all in the year the program is
   actively trying to close.

**What is NOT claimed by stopping.** The repair is not withdrawn, doubted, or
weakened. It remains correct on its merits, and rule 1 `[R-STRUCT]` continues to
govern its successor: a worse fit would not be grounds to revert it. The stop is
about *when a number may be produced*, not about whether the physics is right.

---

## 5. Successor round — what ercot-187 must pre-register

The construction is already fixed and merged; the successor re-registers it
**with the seam proof's premise corrected** and solves the A/B that this session
did not.

1. **SP-1 restated correctly.** Assert what is actually true and now measured:
   the stamp equals `max(stamped, max-over-rows)` by construction, and it equals
   the ercot-176 read **exactly on the prefixes that have a committed tranche**
   (179 of 219) — with the 40 no-committed-tranche prefixes named as the second
   facet, not as a falsifier.
2. **P-2 restated.** The inertness prior is dead. Pre-register the *measured*
   scope instead: 2024/2025 array-equal, 2023 moves 76,845 row-hours via the
   single exclusion of `p6243`, with **no direction predicted**.
3. **Everything else carries verbatim** — the same unchanged bound, the same
   kill gates (G-SHED primary 4/2/0; G-C3c 61/23/3 vs 181/53/31; G-COAL148;
   G-OWNER protecting C3a-2024/2025 PASS and C3b-2024 ≤ 0.20; G-SPAN; G-SPUR;
   G-DOF; G-D2; rule-22 LOYO), the same A/B via `replay_keeper.py` on
   `ercot185_shapedarm_B`, and **the same three-branch honest-outcome clause,
   which is now the load-bearing one**: the arm moves only 2023, so branch (iii)
   — a worse fit is not grounds to revert — is the branch most likely to fire.
4. **Retention.** ERCOT is at **15** registered runs; the pair still evicts
   `2026-08-04-run162a-storage-rt` and `2026-08-04-run162b-storage-rt`.

**A question the successor should answer while it is there, and not defer
again:** is `p6243`'s assembled 8 h min-down *correct*, or is it a CAMPD
`Min_Down_Hours` artifact on a CT-classified plant? Rule 14 `[R-ACCURATE]` says
prefer the measured value and fix the root cause if it looks wrong — it does not
say assume it wrong because excluding the plant is inconvenient. Either way the
gate's grain is right; what is open is one plant's input.

---

## 6. Governance

* **Rules 15/16** — nothing solved, so nothing registered; the absence is
  declared here rather than left to inference. No single-year anything.
* **Rule 22 `[R-HOLDOUT]`** — every read stayed inside {2023, 2024, 2025};
  ERCOT holds no `complete` and no `final` marker and none was sought. No
  out-of-training year was solved, scored, read or registered.
* **Rule 23 `[R-FROZEN-DERIVE]`** — **not engaged**: no derive was run, no
  artifact re-derived, no constant re-valued.
* **Rule 24 `[R-REGISTRY]`** — one registered `ScenarioConfig` field, cache-key
  registered dropped-at-default in the same commit as the field.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT-gated throughout. The sibling grain defect
  at `model/commitment.py::_ra_bridge_unit_params` (the CAISO RA bridge, which
  already carries its own class-table workaround for the zero-physics case) is
  **named and untouched**.
* **Rule 26 `[R-DELETE]`** — the transitional flag's deletion condition is
  written into the field's own docstring and §3 above.
* **Rule 27 `[R-PUSH]`** — every push touching a ≥300-line file was
  blob-verified against the **remote** before the next commit: `assembly.py`
  (1,734), `offer_surfaces.py` (3,819), `fleet/__init__.py` (650),
  `scenarios.py` (13,033), `mechanism-matrix.js` (2,556), the pool test file
  (380). All byte-identical; no file shrank.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (a) the DO-NOT-REDO check preceded the
  precommit; duty (b) both cells stamped in this session
  (`ercot_faststart_pool_plant_physics` stays **`O`**, verdict not reached;
  `ercot_faststart_pool_offer` stays **`K`** with its ercot-176 annotation
  replaced by the measured record); duty (c) the row landed with the field;
  duty (d) no cross-ISO verdict minted.
* **GitHub Actions** — nothing offloaded; the probe ran in-session.

**Test state.** The fleet/offer/scenario/cache-key sweep is **718 passed, 6
failed**; the 4 new pool tests pass and the file's full 15 pass. **All six
failures reproduce at clean HEAD `fe9fa97f` with this session's changes
stashed** — verified by stashing and re-running both sets — so none is caused
here, and none is fixed here:

* `tests/regression/test_fleet_arrays_golden.py::…_ercot_2023_golden`
  (`min_gen`, `availability`) — the same keeper-reproduction drift ercot-173 §5
  recorded and ercot-174/185 carried. **This is exactly why the successor's A/B
  must be a same-HEAD pair** rather than a comparison against the committed
  keeper's ledgered numbers.
* `tests/regression/test_soundness.py::…test_capacity_evolution_changes_fleet`
  and the four `tests/unit/results/test_export.py::TestExportScenarioJson`
  cases — all a `RuntimeError` out of
  `src/market_sim/data/confirmed_retirements.py:168`, an environment/data
  condition unrelated to this session's scope. Reported, not adopted.

**Next shorthand: ercot-187.**

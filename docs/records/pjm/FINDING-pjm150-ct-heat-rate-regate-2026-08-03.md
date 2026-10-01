# FINDING — pjm-150 / PJM: the CT meter screen was already promoted, and the re-gate proves the keeper still reproduces

**Session:** pjm-150 · **Date:** 2026-08-03 · **ISO:** PJM
**Pre-registration:** `PREREG-pjm150-ct-heat-rate-regate-2026-08-03.md`
**Outcome:** **NO PROMOTION SOUGHT AND NONE NEEDED.** The chartered A/B was moot
before this session opened. The compute went to the one gate it left unmeasured,
which **PASSES**: the PJM keeper is bit-identical at HEAD.

Run registered: `2026-08-03-pjm-150-ct-regate` (bundle
`pjm150_ctmeter_regate_A`). Keeper unchanged: `2026-08-03-pjm-147b-chp-heat`.

---

## 1. Headline

| | |
|---|---|
| chartered task | run the CT heat-rate meter-screen A/B for PJM, promote if it holds |
| actual state | **already run and already promoted, at `pjm-147`, ~5 h before the handoff was written** |
| what was run instead | the **K2 bit-identity re-gate** — one arm, not two |
| K1 zero recipe changes | **PASS** (5 value diffs, every one an enumerated moved default) |
| K2 control integrity | **PASS — max \|ΔMW\| = 0.000000, all three years, 499,320 P1 class-hours** |
| K3 liveness | **n/a** — no A/B exists; not re-derived (pjm-147 published it) |
| K4a model criteria | **PASS — zero flips of the eight model-determined criteria** |
| K4b governance | flips `PASS → UNATTESTED`; **bookkeeping, disclosed** (§5) |
| K5 span | **PASS** — 2023 / 2024 / 2025 in one bundle; holdout freeze untouched |

Two results worth the compute, neither of them the chartered one:

1. **The caiso-146 HEAD-drift item is answered in the negative for PJM** (§3).
2. **The `pjm-149` D-2 attribution fix is measured exactly, with zero
   confounding** — and it is **larger in PJM than that session projected** (§6).

---

## 2. The premise was stale, and the evidence is in the repo

The handoff's framing — *"PJM is the LAST of the four artifact-consuming ISOs not
re-based … cut twice before (caiso-158, caiso-159) purely on box size"* — came
from `FINDING-caiso160` §7 item 1. It was **already false when written**, because
`pjm-147` ran PJM's leg in parallel and promoted the result.

Verified in this session from the repo's own bytes, not from prose:

| check | result |
|---|---|
| commits touching `campd_ct_heat_rates_PJM.csv` on **any ref** | exactly two: `c9a370d`, then the fix `f6238a5` (2026-08-03 00:05:32) |
| keeper `pjm147_chp_B` `run_config.git.basis_sha` | `217e5b19…` (2026-08-03 01:57:04) |
| `f6238a5` ancestor of `217e5b1`? | **YES** |
| artifact md5 at the keeper's own basis commit | **`32c26167d83869cff798a2f5cb274106`** = the POST-FIX blob |
| keeper tree `dirty` / `changed_files` | `false` / `[]` |
| keeper `measured_ct_heat_rates` | `true` |

The keeper **consumed the corrected artifact at solve time**. Its own committed
side-artifact says so — `_pjm147_k2_drift.json`: *"this comparison is the PJM leg
caiso-158 deferred as its follow-up item 2"* — as does
`docs/mechanism-testing-matrix.md` §5.3: *"The control arm is caiso-158's
follow-up item 2, **now discharged**."*

### The artifact delta, re-measured here

| | pre-fix `f6238a5^` | post-fix `HEAD` |
|---|---|---|
| md5 | `8d48c2bb98d2ce044bed2a438d4b87ec` | `32c26167d83869cff798a2f5cb274106` |
| rows / applied | 71 / 71 | 71 / 71 |
| applied capacity | 23,161.8 MW | 23,161.8 MW |
| cap-weighted applied HR | **11.5817** | **11.6511** |

Δ = **+0.0694** (unrounded +0.06935), the smallest of the six ISOs. 63 plants
move — 58 dearer, 5 cheaper, 8 unchanged — **zero flag changes**, `n_units` 281
both sides. Largest movers: Darby 10.5885 → 12.6954, Dick's Creek 19.5996 →
20.7765, AMP-Ohio Napoleon 14.8685 → 15.7673.

**Both figure-pairs in circulation are correct.** The handoff quotes 11.5817 →
11.6511 (all 71 applied rows); `pjm-147`'s promotion note quotes 11.4749 →
11.5556 (the 63 *changed* rows, 19,887.2 MW). Re-measured here, each reproduces
its own population exactly. They were never in conflict.

**Consequence:** arm B's condition *is* the incumbent's condition. Solving it
again would re-derive a merged result at ~3 h of per-plant multi-zone LP and
would re-test a cell adjudicated `K` — barred by rule 28a and by caiso-158 §7.

---

## 3. What was run, and what it buys

`pjm-147` states plainly that its own K2 strict-byte gate **FAILED by
construction**: its comparison ran `pjm143_hy_level_B` (pre-screen artifact,
*older HEAD*) → `pjm147_control_A` (post-screen, current HEAD), so the CT effect
it published is confounded with intervening `src/market_sim` movement. That is a
disclosed limitation of a promoted result, not a defect in it — but it left PJM
the one consumer ISO with **no bit-identity evidence at all**, while **11
`src/market_sim` commits** landed between `217e5b1` and `origin/main`.

`caiso-146` recorded *documented-inert* commits nonetheless leaving a CAISO
keeper's sidecars diverging **up to 3.2 GW on a class-hour**, cause still
unidentified. `caiso-160` closed that item for NYISO by measurement. It was
untested for PJM.

### K2 result: bit-identical

The arm replays the `pjm147_chp_B` recipe **cold** at this HEAD against the
**same** artifact, with **no `--set`** — so the config delta is structural, not
asserted.

| year | max \|ΔMW\|, any P1 class-hour | rows compared | arm total | keeper total |
|---|---|---|---|---|
| 2023 | **0.000000** | 166,440 | 787.9277 TWh | 787.9277 TWh |
| 2024 | **0.000000** | 166,440 | 816.8304 TWh | 816.8304 TWh |
| 2025 | **0.000000** | 166,440 | 847.9046 TWh | 847.9046 TWh |

**The caiso-146 HEAD-drift item is answered in the negative for PJM.** Whatever
produced CAISO's 3.2 GW divergence does not reach this ISO either. **The item
stays open for CAISO** — closed now for NYISO (caiso-160) and PJM (here).

**Fresh-evidence provenance.** 2023 and 2024 were solved fresh in
`pjm150_regate_y24`; 2025 solved fresh in the final bundle, which byte-copied the
first two forward. Every year is therefore fresh evidence — the `--reuse-solved`
copies aggregate solves that this session performed, they do not stand in for
one.

---

## 4. K1 — five value diffs, all moved defaults, all derived for PJM

`config_drift` cannot distinguish a changed recipe from a shipped default that
moved (caiso-160 §4): the field is present on both sides with different values
either way. Five appear. **None is a recipe choice**, and PJM's list was derived
here rather than inherited from caiso-160's NYISO one (rule 25 `[R-ISO-SCOPE]`):

| field | commit | why it cannot reach a PJM backcast |
|---|---|---|
| `retirement_rule` | `24b1602` | capacity-evolution step 3 |
| `entry_rate_limits` | `3e33f15` | capacity-evolution step 5 |
| `entry_commissioning_lag` | `3e33f15` | same step-5 entry path |
| `net_cone_forward_escalation` | `e6f0cdb` (owner D-3a) | forward net-CONE, priced only for the evolution screens |
| `caiso_ra_min_load_frac` | `a0fc302` 3(b) | rule-25 re-scope; **recording** change |

**The shared reason is firmer than the one caiso-160 recorded.** It is not that
the evolution loop is mode-gated — it is not: `evolve_fleet` has no `backcast`
branch at all, and `runner.py` enters it for every year after the first. It is
that **the calibration harness never reaches that loop**:
`run_calibration_full.solve_and_persist` loops `for year in years` and calls
`run_calibration.run_year` per year — a standalone per-year backcast solve that
builds that year's own historical fleet. `runner.py`'s multi-year path is not
used by this lane. Anyone re-deriving a `DEFAULT_MOVES` list from
"forecast-mode-only" will eventually be wrong; from "the harness does not call
it" they will not.

`caiso_ra_min_load_frac` is verified for **PJM**: both readers
(`pipeline/commitment.py:207`, `:1582`) sit behind
`caiso_ra_mustoffer and iso == "CAISO"`, and this bundle carries
`caiso_ra_mustoffer=False` **and** `iso="PJM"` — either condition alone closes
it. Worth flagging separately: it also **overrides the replayed `meta.json`
kwarg**, so a replay cannot re-assert the keeper's 0.26 even though the keeper
records it at top level.

Schema drift, zero behavioural content: **arm-only** `electrification_path`,
`electrification_percentile`, `nyiso_nyc_rcpf_step_curve` (added after the keeper
solved); **keeper-only** `ct_committed_hr_override` / `ct_econ_hr_override` /
`ct_peak_hr_override` (1.1 / 1.2 / 1.4), deleted by `a0fc302` under rule 26
`[R-DELETE]`. That deletion was checked against **PJM's** recipe rather than
assumed: both former readers sat in the `else` of `if offer is not None` gated on
`group == "CT_CHP"`, and PJM carries a truthy `offer_curve_by_group["CT_CHP"]`,
so control never reached the limb.

**Every one of these is a hypothesis; K2's 0.000000 MW is the evidence.** One
non-zero MW would have voided the lot.

---

## 5. K4 — the eight model criteria are identical; the ninth is bookkeeping

| | keeper | arm |
|---|---|---|
| determination | CALIBRATED | NOT-YET |
| grade | 9 scored / 9 target / 0 ledgered / 0 fails | 8 / 8 / 0 / 0 |
| C1 fuelmix · C2 · C3a · C3b · C3c · C4 · C7 · C8 | PASS | **PASS — all eight** |
| C6 governance | PASS | **UNATTESTED** |
| C1 headline | all 16/16 · free 12/12 | **identical** |

C6 reads the bundle's rule-21 attestation, which a probe arm does not carry and
which no solve can produce — the same `UNATTESTED → NOT-YET` bookkeeping
`caiso-159` §3 documented on arms that reproduced their incumbent exactly. **It
is reported, not absorbed**, and the gate scorer splits K4 rather than papering
over it.

No attestation was authored, deliberately: nothing is being promoted, and
minting governance claims for a bundle nobody promotes would assert more than
this session earned. Given K2 = 0.000000 MW on every class-hour, the eight
model-determined verdicts are not merely equal but **provably** equal —
identical dispatch cannot score differently.

---

## 6. Second result: the pjm-149 D-2 fix, measured exactly — and bigger in PJM than projected

Because the dispatch is **bit-identical**, any difference between the keeper's
committed `legitimacy_diagnostics.json` and the arm's is **definitionally not a
solve difference**. This bundle is therefore the first in the repo carrying PJM
D-2 attribution generated at current HEAD over a keeper-identical dispatch — a
free, zero-confound measurement of the `pjm-149` attribution-path fix
(`f46bdfd`), which that session deliberately did **not** regenerate.

Measured, keeper-committed → arm:

* **D-1 · D-4 · D-5 · D-9 · D-10 — row-for-row unchanged**, all pass flags equal.
  (D-1 `passed: False` is pre-existing on both sides; it sits on classes the
  rubric skips as immaterial, and **C7 PASSes**.)
* **D-2: 32 rows → 42.** Ten additions, zero removals:
  * `nuclear_mustrun` ×3 (272.02 / 270.59 / 269.33 TWh, `share_of_class` 1.0) —
    **exactly the shape pjm-149 predicted**;
  * `CC_CHP:chp_steam` ×3, `CC_CHP:reliability_floor` ×2, `ST_CHP:chp_steam`,
    `COAL:chp_steam` — the CHP classes pjm-148 §4 had believed payload-absent.
* **32 of the shared rows change value**, several materially:
  `CT_CHP:chp_steam` share **0.0024 → 0.2399** (2023), **0.0013 → 0.1804**
  (2024), **0.0153 → 0.2780** (2025), riding a `class_total_twh` re-basis
  4.558 → 1.5256; `ST_CHP:chp_steam` 0.0 → 0.0353 / 0.0205.

**This exceeds what pjm-149 §7 projected for PJM** — that table reads
*"+3 each (`''` nuclear)"* with **+0** summary rows, and its gate A2 asserts
*"additions only … no pre-existing row … altered outside the affected classes."*
Here PJM gains **ten** rows and **32 shared rows move**.

**Stated carefully, because the two measurements are not the same experiment.**
pjm-149's A1 baseline was a **pre-fix regen taken in-session at its HEAD**; mine
compares the **committed** keeper artifact (generated at pjm-147's HEAD) against
one generated **now**. So my delta is the whole diagnostics-code distance between
those two points, of which `f46bdfd` is the leading but not necessarily the sole
contributor. What is certain, and is the useful part: **none of it is dispatch**,
and a reader diffing the two committed files today sees all of it. Confirming the
attribution belongs to the pjm-149 lane, not this one (§8 item 2).

**No gate moves.** C8 PASSes on both sides — the C8-gated class barely shifts
(`CT_PEAKER:ct_netload_drag` 0.1072 → 0.1058, 0.1221 → 0.1194, 0.1097 → 0.1088),
and the large movers are `CT_CHP` / `ST_CHP` / `CC_CHP`, all **C7- and
C8-exempt** by explicit class list. **No determination changes and no keeper is
invalidated** — the same conclusion pjm-149 reached, now on measured bytes rather
than a projection.

---

## 7. Also found (each cost real time; none is in the charter)

1. **The handoff's rule-12 chain does not work.** `--out-dir X --reuse-solved X`
   raises `shutil.SameFileError` at
   `run_calibration_full._copy_reused_year:2978` — the reuse path `copy2`s each
   dispatch parquet from source to destination, and in a self-reuse those are the
   same file. It fails **late**, after the recipe match passes and after a year
   has already solved. `pjm-147` never hit it because it chained through a
   **separate** directory (its meta records `source_bundle pjm147_chp_B_y24`).
   The driver now takes explicit `--out` / `--reuse-from` and refuses self-reuse
   up front.
2. **`--reuse-solved` has three independent tree-cleanliness refusals**, and two
   of them cost a solve here: (a) the working tree is dirty under
   `src`/`scripts`/`data`; (b) the **prior bundle** was itself solved from a dirty
   tree; (c) **anything under those paths changed between the prior bundle's
   commit and HEAD** — including the session's own probe-script commit. (a) only
   ever surfaces as a mid-run WARNING that silently downgrades the chain into a
   full re-solve of every year. **Do not commit under `scripts/` between links of
   a chain.**
3. **A stray formatter diff was sitting on `main`** (`gen_nyiso115_attestation.py`).
   Harmless as lint; not harmless as a chain blocker, per (2a). Committed.
4. **`pjm_da_virtual_bids` needs a gitignored raw feed that was absent**, and
   `virtual_bids.py` raises `FileNotFoundError` rather than no-opping (correctly —
   "the mechanism never silently no-ops"). `data/raw/pjm-da-virtuals/` held only
   its README. Re-fetched **2023–2025 `hrl_da_incs_decs` only** via
   `scripts/data/fetch_pjm_da_virtuals.py`; the layer then armed on 128
   pseudo-unit rows per year. **Any future PJM session on a fresh container must
   do this before solving.** Three other empty raw dirs were surveyed and cleared
   as non-blocking: `pjm-energy-offers` (no `src/` reader), `lmp-components` (no
   `src/` reader), `ramp-capability` (declares "no raw files of its own" —
   derived from `eia-860` + `campd-unit-level`, both present).
5. **`regenerate_clean` ran 50/50 with ZERO failures.** The documented
   `[FAIL] ancillary-services: exit -6` teardown false alarm did **not** fire.
   The known-false-alarm note stays useful, but it is not deterministic.
6. **Do not resize swap while a job is running.** `swapoff` forces swapped pages
   back into RAM and OOM-killed a 20-minute-old `regenerate_clean`. Self-inflicted;
   recorded so the next session does not repeat it.
7. **`hydro-plant-modes` is CAISO-only by construction**, so the PJM warning
   *"no hydro-plant-modes clean partition for PJM"* is structural, not an
   environment gap. The keeper hit it too.
8. **The session ordinal `pjm-149` was double-issued.** `d338ba6` had already
   spent it on the D-2 floor-attribution session (filed under
   `docs/calibration-log/governance.md`, which is why `pjm.md`'s *"Next
   shorthand"* counter never advanced). This session took **pjm-150**.

---

## 8. DO-NOT-REDO

* **Do not run the PJM CT meter-screen A/B.** It ran at `pjm-147` and the
  corrected artifact is in the live keeper. §2 is the provenance chain; check it
  before believing any handoff that says otherwise.
* **Do not re-test `measured_ct_heat_rates` as a mechanism.** Input correction,
  zero `ScenarioConfig` surface. PJM's cell stays `K`; only the note/evidence
  moved (rule 28b).
* **Do not read K2 = 0.000000 as evidence the screen does nothing.** It says the
  *keeper reproduces*, nothing about the artifact's effect — which `pjm-147`
  measured as dispatch-live (CT_PEAKER −0.924/−0.657/−0.899 TWh) and
  score-neutral.
* **Do not treat a committed keeper bundle as a same-HEAD control** without first
  checking whether `src/market_sim` moved. Here it had, 11 times.
* **Do not justify a `DEFAULT_MOVES` entry with "forecast-mode only."** It is not
  true of `evolve_fleet`, which has no mode branch. The true reason is that the
  calibration harness never calls it (§4).
* **Do not "fix" a `config_drift` value-diff by editing the allowlist to pass.**
  The entry is the hypothesis; K2 is the evidence.
* **Do not re-open the caiso-158 / caiso-159 / caiso-160 DO-NOT-REDO lists.**
  All stand.

---

## 9. Follow-up lane items (not done here)

1. **The caiso-146 HEAD-drift item stays open for CAISO** — closed for NYISO
   (caiso-160) and PJM (here), both by measurement, both bit-identical. CAISO is
   the only ISO where a keeper's sidecars have actually been seen to diverge, and
   it is still unexplained.
2. **pjm-149 should confirm §6 against its own A1 baseline.** Its §7 table
   projects `+3 / +0 / +0` for PJM; the measured committed-vs-HEAD distance is
   `+10` rows with `32` shared rows moved. Either its projection understated PJM
   or another diagnostics change contributes. No verdict depends on the answer —
   C7/C8 pass either way — but the record should be right.
3. **`cache_key` blindness to input-artifact provenance** — caiso-158 §8.1,
   still open, and its config-layer sibling (caiso-160 §4) with it. Both want the
   same fix: hash what was actually consumed.
4. **`DEFAULT_MOVES` still lives in per-session generators** (caiso-160 §7.3).
   It is now been re-derived independently three times; it belongs beside
   `config_drift` in a shared module — with §4's corrected justification, not the
   forecast-mode one.
5. **Fix `_copy_reused_year` to tolerate self-reuse** (§7.1), or document the
   separate-directory chain as the only supported form. The handoff prompt in
   circulation prescribes the broken one.

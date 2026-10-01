# PRE-REGISTRATION — pjm-150: the CT heat-rate meter screen re-gate for PJM

**Session:** pjm-150 · **Date:** 2026-08-03 · **ISO:** PJM
**Charter as handed:** "Run the CT heat-rate meter-screen A/B for PJM and promote
it if it holds" (handed as *pjm-149*; see §0 on the id).
**Status:** the chartered A/B is **MOOT — already run and already promoted.** This
pre-registration amends the charter to the one gate it left unmeasured.

---

## 0. Session id

The handoff names this session `pjm-149`. That id is **already spent**: PR-merged
commit `d338ba6` ("pjm-149: file the census, the finding and the governance
entry") landed `FINDING-pjm149-d2-floor-attribution-path-2026-08-03.md` and
`f46bdfd` on `main` earlier today. Two sessions were handed the same ordinal.
This one takes **pjm-150** so neither record is overwritten. No other change.

---

## 1. The premise is stale — measured, not assumed

The handoff's framing — *"PJM is the LAST of the four artifact-consuming ISOs not
re-based … cut twice before (caiso-158, caiso-159) purely on box size"* — was
inherited from `FINDING-caiso160` §7 item 1. **It was already false when written.**
`pjm-147` ran PJM's leg the same day and promoted the result.

Provenance chain, verified in this session from the repo's own bytes:

| check | result |
|---|---|
| fix commit `f6238a5` | `2026-08-03 00:05:32 +0000` |
| commits touching `campd_ct_heat_rates_PJM.csv` on **any ref** | exactly two: `c9a370d`, then `f6238a5` |
| PJM keeper `pjm147_chp_B` `run_config.git.basis_sha` | `217e5b19…` (`2026-08-03 01:57:04`) |
| `f6238a5` ancestor of `217e5b1`? | **YES** |
| `git show 217e5b1:…campd_ct_heat_rates_PJM.csv \| md5sum` | **`32c26167d83869cff798a2f5cb274106`** = the POST-FIX blob |
| keeper `run_config.git.dirty` / `changed_files` | `false` / `[]` |
| keeper `scenario_config.measured_ct_heat_rates` | `true` |

The keeper therefore **consumed the corrected artifact at solve time**. Its own
committed side-artifact says so in as many words —
`results/calibration/_pjm147_k2_drift.json`: *"this comparison is the PJM leg
caiso-158 deferred as its follow-up item 2"* — as does the mechanism-matrix doc
§5.3: *"The control arm is caiso-158's follow-up item 2, now discharged."*

### The artifact delta, re-measured here rather than trusted

Both blobs read directly out of git, `flag == 'ok'` rows weighted by
`class_capacity_mw`:

| | pre-fix `f6238a5^` | post-fix `HEAD` |
|---|---|---|
| md5 | `8d48c2bb98d2ce044bed2a438d4b87ec` | `32c26167d83869cff798a2f5cb274106` |
| rows / applied | 71 / 71 | 71 / 71 |
| cap-weighted applied HR | **11.5817** | **11.6511** |

**Δ = +0.0693** (handoff: +0.0694 — rounding), the smallest of the six ISOs.
63 plants move, 58 dearer / 5 cheaper / 8 unchanged; **zero flag changes**;
`n_units` 281 both sides. Restricted to the 63 changed plants (19,887.2 MW) the
cap-weighted rate is **11.4749 → 11.5556**, which reproduces `pjm-147`'s promotion
note *exactly*. The two figure-pairs in circulation are the same measurement over
different populations, not a discrepancy.

**Conclusion.** Arm B's condition *is* the incumbent's condition. There is no A/B
to run: the treatment is already the keeper, already promoted, already scored
CALIBRATED 9/9. Solving it again would re-derive a merged result at a cost of
~3 h of per-plant multi-zone LP, and would re-test a cell adjudicated `K` —
barred by rule 28a and by caiso-158 §7's DO-NOT-REDO.

---

## 2. What is actually still open, and why it is worth one arm

**K2 has never been measured for PJM.** `pjm-147` states plainly that its own K2
strict-byte gate **FAILED by construction**: its comparison was
`pjm143_hy_level_B` (pre-screen artifact, *older HEAD*) → `pjm147_control_A`
(post-screen, current HEAD), so the CT effect it published
(CT_PEAKER −0.924/−0.657/−0.899 TWh) is confounded with whatever `src/market_sim`
moved between the two solves. That is a disclosed limitation of a promoted
result, not a defect in it — but it leaves PJM the one consumer ISO with **no
bit-identity evidence at all**.

And `src/market_sim` **has** moved since the keeper solved — **11 commits**
between `217e5b1` and `origin/main` (`01b6a6a`), among them `a0fc302`
(deletes the `ct_*_hr_override` triple), `9a54412` (reserve balance-row activity
moved inside the co-opt branch), `9df32c2` (per-family reserve duals),
`24b1602` / `3e33f15` (capacity-evolution default flips), `e6f0cdb`
(net-CONE forward mode), `0233913` (undeclared-default-move guard).

`caiso-146` recorded *documented-inert* commits nonetheless leaving a CAISO
keeper's sidecars diverging **up to 3.2 GW on a class-hour**, cause still
unidentified. `caiso-160` answered that item in the negative for NYISO **by
measurement**. It is still open for CAISO and **untested for PJM**.

So the amended charter is **one arm, not two**:

> Cold-solve the `pjm147_chp_B` recipe, unchanged, at **this** HEAD against the
> **same (corrected)** artifact, and diff every P1 class-hour against the
> committed keeper's own sidecars.

Because the keeper already carries the corrected artifact, this single arm is
simultaneously the charter's control **and** its treatment — which is exactly
what makes it a clean drift test.

---

## 3. Gates (registered before the arm solves)

| id | gate | pass condition |
|---|---|---|
| **K1** | zero recipe changes vs `pjm147_chp_B` | `config_drift()` value-diffs empty, or every one enumerated in `DEFAULT_MOVES` **with the commit that moved it and why it cannot reach a PJM backcast** |
| **K2** | control integrity | max \|ΔMW\| on any P1 class-hour vs the committed keeper = **0.000000**, all three years |
| **K3** | liveness | **not applicable — no A/B exists.** The artifact's PJM effect is already published by pjm-147 and is NOT re-derived here |
| **K4** | no criterion regresses | all 9 verdicts, the grade summary and the C1 headline identical to the keeper (9 scored / 9 target / 0 ledgered / 0 fails) |
| **K5** | span | `[2023, 2024, 2025]` in ONE bundle (rule 16), holdout freeze untouched (rule 22) |

`DEFAULT_MOVES` is **derived for PJM in this session** from PJM's own recipe and
PJM's own reachability — `caiso-160`'s NYISO list is **not** reused (rule 25
`[R-ISO-SCOPE]`, and caiso-160 §4's own instruction). The allowlist is a
hypothesis; **K2 is the evidence**. One non-zero MW voids it.

### Pre-solve K1 screen (no LP spent)

`replay_keeper.build_kwargs(meta)` carries **`measured_ct_heat_rates: true` and
`measured_chp_heat_rates: true`** through the `prb_overrides` channel — verified
before any solve, per the charter's pipeline rule 3. Neither appears at
`meta.json`'s top level; both ride `coal_prb_sigmoid_overrides`.

Three fields the keeper records are **deleted** from `ScenarioConfig` at HEAD:
`ct_committed_hr_override` (1.1), `ct_econ_hr_override` (1.2),
`ct_peak_hr_override` (1.4), removed by `a0fc302` under rule 26 `[R-DELETE]`.
Checked for PJM specifically rather than inherited: both readers
(`data/fleet/assembly.py`, `data/offer_curves.py`) sat inside the `else` of
`if offer is not None`, gated on `group == "CT_CHP"`, and **PJM's keeper carries a
truthy `offer_curve_by_group["CT_CHP"]`** (committed 0.864 / econ 0.864 / peak
1.008 …), so control never reached that limb on this recipe. Predicted inert —
and K2 measures it.

`capacity_market_clearing_by_iso` (keeper `None`, HEAD default arms PJM) is
coerced to `None` in `__post_init__` whenever `mode == "backcast"`, explicitly to
hold backcast keepers byte-identical. Predicted inert; K2 measures it.

---

## 4. Pipeline rules (carried verbatim from the charter)

1. **COLD-SOLVE.** `results/PJM` scrubbed before the arm; the log must say `(cold)`.
   `cache_key` hashes config fields only and cannot see input bytes.
2. **ORDER: solve → register → diagnostics → re-score.** `legitimacy_diagnostics.json`
   AFTER registration (D-2's rule-20 materiality guard reads `total_load_mwh`
   from the run payload); then `calibration_verdict.py --write-metrics`.
3. **NO `--set`.** The recipe is replayed from the keeper's own `meta.json`, so
   the config delta is structural rather than asserted.
4. **RE-DIFF AT PROMOTION TIME** if this session ever reaches a promotion.

Rule 12 per-year invocation chain (one bundle, rule 16):
`--years 2023` → `--years 2023 2024 --reuse-solved <self>` → `--years 2023 2024
2025 --reuse-solved <self>`. Reused years byte-copy forward and are **not fresh
evidence**; the finding will say so.

---

## 5. BINDING NO-TUNING CLAUSE

Carried verbatim from `PREREG-caiso156` §7. This is an **input correction**: the
corrected artifact **ships regardless of outcome**. If any measurement here comes
back adverse, that is a **discovered bug elsewhere** under rule 14
`[R-ACCURATE]` — open a root-cause item. **Never** revert to the diluted meter,
**never** re-level the band, the trust gate, the cap percentile, or any `pjm_*`
field in response.

Additionally, and specific to this session: **no promotion is sought.** The
keeper already carries the treatment. If K2 comes back non-zero, the deliverable
is a filed defect, not a keeper change.

---

## 6. Rule-28 duties

* **28a.** PJM's lever queue (`docs/mechanism-testing-matrix.md` §5.3) is cited.
  This session proposes **no lever** and goes **off-queue by necessity**: its
  chartered item is already discharged (§1). `measured_ct_heat_rates` PJM is `K`
  and is **not re-tested as a mechanism** — it has zero `ScenarioConfig` surface
  and is an input correction (caiso-158 §7 DO-NOT-REDO).
* **28b.** The `measured_ct_heat_rates` row's **note/evidence is extended** for
  PJM in this session; the **cell stays `K`**. No verdict moves; no keeper block
  re-stamp unless a promotion occurs (it will not).
* **28c.** No new `ScenarioConfig` field is added.

## 7. Rule-22 posture

PJM holds a `complete` marker (validation 2022 **only**) and is **absent** from
`final`. This session solves **2023–2025 only**. No holdout year is touched, no
holdout spend is requested, and the spend freeze is untouched.

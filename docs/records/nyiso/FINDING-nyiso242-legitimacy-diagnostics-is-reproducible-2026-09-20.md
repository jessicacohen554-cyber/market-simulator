# FINDING — nyiso-242: `legitimacy_diagnostics.py` is REPRODUCIBLE. The reported defect was a misdiagnosis, and behind it sit two real ones

**Session** nyiso-242 (rule 32 `[R-SHARD]` (a) — **zero LP, no shard**). **Date** 2026-09-20.
**Scope** the unowned debt item three NYISO handoffs carried forward: *"`legitimacy_diagnostics.py`
IS NOT REPRODUCIBLE on nine measured columns … It is a GATING artifact (C8, rule 20's
conditional-pass path). NOBODY OWNS THIS."*
**Shared scorer — rule 25 `[R-ISO-SCOPE]`.** The fix is written and measured but **NOT landed as a
regeneration**: no committed artifact is rewritten, so **no ISO's determination moves today**. The
nyiso-232/233 precedent governs — a shared scorer change is put to the owner with a cross-ISO
census, not decided by a NYISO lane.

> ## HEADLINE
> 1. **THE SCRIPT IS BYTE-DETERMINISTIC.** Two back-to-back runs on the identical bundle are
>    **sha256-identical**. The "non-reproducibility on nine measured columns at the 3rd decimal"
>    reported in `RESULT-nyiso240` §A.6 and carried forward three times is **not nondeterminism**.
> 2. **IT IS A SILENT DISPATCH-SOURCE SUBSTITUTION, and it is far larger than nine columns.**
>    Re-run against the keeper **with its `dispatch/` layer restored** and the committed artifact
>    reproduces: **18 differing leaves of 1,851 and ZERO gating numerics**. Re-run **without** it —
>    which is the normal state, because `dispatch/` is gitignored and absent from every committed
>    bundle — and **1,416 leaves move, 148 of them gating numerics**. Two different data sources,
>    no record of which one ran.
> 3. **A SECOND, SYSTEMATIC DEFECT: the rule-20 materiality guard is DISABLED in 285 of 315
>    committed D-2 rows (90 %), across EVERY ISO.** The artifact is written **at solve time, before
>    the run is registered**, so the registry sidecar the denominator came from does not exist yet
>    and `load_share` is `null`. NEISO's keeper publishes **five D-2 FAILURES on classes at
>    0.08–0.80 % of load** — classes rule 20 says are *"reported by the D-1/D-2 diagnostics but
>    never gated"*.
> 4. **A THIRD: when the denominator IS computed, it is wrong by ~2.25×.** It summed `fuelRows`,
>    which **omits hydro** (26.2 of NYISO's 152.7 TWh in 2022) and **subtracts** net interchange a
>    net importer's load includes. NYISO 2022: **67.92 TWh against a true 152.68**. Understating the
>    denominator inflates every class's share, so the 2 % floor bound at roughly 1 %.
> 5. **NO DETERMINATION IS CURRENTLY WRONG, and I checked rather than assumed.** `calibration_verdict`
>    computes its **own** materiality from its **own** `_total_load` (verified correct for all nine
>    ISOs) and never reads the artifact's `load_share` / `immaterial` / `passed`. NEISO scores
>    end-to-end as **C8 PASS, determination CALIBRATED**, with those five classes correctly SKIPPED.
>    **This corrects my own framing when I proposed this work**: I said "a gate that doesn't
>    reproduce is a determination that doesn't reproduce". Measured, that is false here. The gating
>    *artifact* is wrong; the *gate* is not — saved by an undocumented redundancy.

---

## 1. THE MEASUREMENT THAT RESOLVES IT

`nyiso241_ctcommitted_span` (NYISO keeper), against its own committed `legitimacy_diagnostics.json`:

| run | dispatch layer | differing leaves (of 1,851) | **gating numerics differing** |
|---|---|---:|---:|
| A | absent (`main` state) | 1,416 | **148** |
| B | absent — repeat of A | 1,416 | 148 |
| **C** | **restored from `2d15779b98…`** | **18** | **0** |

**A and B are sha256-identical**, which settles determinism. C reproduces the committed artifact on
every gating value, which settles the cause: the artifact was written when `dispatch/` existed
locally; every re-run from a clean checkout silently takes the other path.

The two paths are not interchangeable, and the code already says so —
`build_plant_matrices`' docstring: *"the CAMPD-bench-keyed dashboard run payload — which carries
only plants with a CEMS meter, so at PJM it dropped all 14 CC_CHP plants and at every ISO the
nuclear must-run block (17–90 TWh/yr). **The committed keeper corpus is SPLIT across the two
paths**, which is what made the attribution silently non-comparable between bundles."*

The 18 residual leaves are all `load_share` (and one `immaterial` that follows from it) — which is
§2.

---

## 2. THE RULE-20 MATERIALITY GUARD IS OFF IN 90 % OF COMMITTED ROWS

`total_load_mwh` is read from the **registry sidecar**. The artifact is written by the solve, and a
run is registered *after* it is solved — so at write time `sidecar is None`, the denominator is
missing, and `load_share` is `null`. `immaterial` is then `False` for every class, so **every class
is gated**, including ones rule 20 exempts.

Census over every committed bundle carrying a D-2 summary:

| | rows |
|---|---:|
| D-2 summary rows across 19 committed bundles | 315 |
| **with `load_share: null` — guard disabled** | **285 (90 %)** |

The two exceptions (`pjm_d4_4_A`, `pjm_debugb_inputclock_A`) were evidently regenerated after
registration and carry 6 immaterial rows each.

**What it produces.** NEISO's keeper `neiso112_mer_span` publishes `D2.passed = False` on five
failures, every one of them below the floor on the correct `max(model, actual)` basis:

| year | class | model TWh | actual TWh | max | ISO load | share | rule 20 |
|---|---|---:|---:|---:|---:|---:|---|
| 2020 | COAL | 0.060 | 0.000 | 0.060 | 78.32 | **0.08 %** | immaterial |
| 2020 | CT_PEAKER | 0.240 | 0.624 | 0.624 | 78.32 | **0.80 %** | immaterial |
| 2023 | CT_PEAKER | 0.400 | 0.472 | 0.472 | 82.02 | **0.57 %** | immaterial |
| 2024 | ST_GAS | 0.050 | 0.124 | 0.124 | 90.83 | **0.14 %** | immaterial |
| 2025 | ST_GAS | 0.070 | 0.313 | 0.313 | 94.58 | **0.33 %** | immaterial |

MISO's, PJM's and SPP's D-2 failures are on genuinely material classes (CT_PEAKER at 11–29 TWh) and
are **real** — this does not excuse them.

---

## 3. THE DENOMINATOR ITSELF WAS WRONG BY ~2.25×

`load_payload_total_load_mwh` summed `fuelRows[*].m`, documented as *"the model's served-energy
balance, i.e. total load"*. It is neither. NYISO 2022, from the keeper's own payload:

```
gas 63.5 + coal 0.67 + nuclear 26.75 + wind 4.7 + solar 0.11 + interchange (−27.81) = 67.92 TWh
```

* **hydro is absent from `fuelRows` entirely** — 26.2 TWh, the single largest omission;
* **net interchange is SUBTRACTED**, when NYISO imports ~27.8 TWh that its load consumes.

True load is **152.68 TWh** — confirmed three independent ways: the payload's own zone demand, the
bundle's `hourly/system_2022.parquet` demand sum (152.682), and `calibration_verdict._total_load`
(152.68). A denominator ~2.25× too small inflates every class's share, so rule 20's 2 % floor bound
at roughly 1 % — over-strict, in the same direction as §2.

The correction's size is ISO-specific in exactly the way the omitted terms predict: the old/new
`load_share` ratio is **2.25× (NYISO**, huge hydro + huge imports), **1.15× (NEISO)**, **1.07×
(SOCO**, little of either**)**.

---

## 4. THE FIX, AND WHY IT IS VERDICT-NEUTRAL

Three changes to `scripts/legitimacy_diagnostics.py`, all provenance or denominator — **no
diagnostic's computation changes**:

1. **`dispatch_source` is stamped per year into the machine artifact**, exactly as
   `plant_class_vote_basis` already is, and for the identical stated reason: *"recorded into the
   committed artifact so a fallback … can never be silent."*
2. **`load_payload_total_load_mwh` now sums the payload's per-zone demand** — the same field, from
   the same block, that `calibration_verdict._total_load` uses, so the quarantine gate and the
   rubric scorer draw **one** line rather than two.
3. **`load_bundle_total_load_mwh` is added as a fallback** from the bundle's own
   `hourly/system_<year>.parquet` (a rule-15 keeper sidecar, present in every committed bundle), so
   the guard is populated **at solve time** when no registry sidecar exists. Absent sidecar still
   returns `None` — the guard stays disabled rather than silently substituting.

**Cross-ISO A/B, old code vs new on the same dispatch path** (rule 25's census):

| ISO | D-2 rows | **`forced_share` rows moved** | `immaterial` | `D2.passed` | old/new `load_share` |
|---|---:|---:|---|---|---:|
| NYISO (parquet path) | 17 | **0** | 0 → 4 | — | 2.25× |
| NEISO (payload path) | 24 | **0** | 17 → 18 | True → True | 1.15× |
| SOCO (payload path) | 12 | **0** | 0 → 0 | True → True | 1.07× |

**`forced_share` — the only D-2 field `calibration_verdict` reads — moves in ZERO rows.** PJM could
not be A/B'd in this container: it raises `FileNotFoundError` on a missing
`transfer-interface-limits` clean partition, identically on old and new code, and is unrelated to
this change.

**Nothing is regenerated.** Determinations read the *committed* artifacts, which this change does
not rewrite; every ISO's verdict is byte-identical until its own lane re-runs the diagnostic. That
is the safe ordering and it is deliberate.

Guards, in `tests/scoring/test_legitimacy_diagnostics.py` (101 passing in that file):

* `TestMaterialityDenominator` — three tests pinning the `fuelRows` regression **by name and by
  number** (the fixture reproduces the 67.92-vs-152.68 shape), the solve-time bundle fallback, and
  the dispatch-source stamp.
* `TestScorerDoesNotTrustArtifactMateriality` — **the guard §5 says was missing.** It walks
  `calibration_verdict.py`'s AST and fails if the scorer ever subscripts or `.get()`s
  `load_share` / `immaterial`, and separately pins `_total_load` to zone demand. This is the
  redundancy that kept a wrong artifact from being a wrong verdict; it is now a property under
  test rather than an accident.

---

## 5. WHAT I GOT WRONG, AND WHAT IS STILL OPEN

**My own framing when I proposed this work was wrong** and it is worth naming because it drove the
priority: I said an unreproducible scoring gate *"undermines every ISO's determination"*. Measured,
it does not. `calibration_verdict` recomputes materiality from its own correct denominator and
never trusts the artifact's `load_share` / `immaterial` / `passed`. The real severity is lower and
different: **a committed, published gating artifact whose fields disagree with the scorer that
gates on it**, held safe only by a redundancy nobody documented as a safety property.

**Still open, and not this session's to close:**

* **Every committed artifact carries the defects until its lane regenerates.** That is a
  per-ISO action under rule 25, and the owner's call — it is why nothing was regenerated here.
* **`tests/scoring` carries a pre-existing failure baseline on clean main, and this change adds
  none — measured by A/B rather than asserted.** Stashing the change and re-running the whole
  suite gives **22 failed / 1,547 passed**; with the change, **22 failed** and the passing count
  rises by exactly the new tests. **The failure sets are identical**, and all of them sit in
  `test_golden_manifest_provenance.py` (ERCOT partition capture keys), untouched by this work.
  Note the baseline is **22, not the 20 the handoffs record** — it drifted by two before this
  session and still has no owner.
* ~~**The redundancy that saved this should be a test, not luck.**~~ **CLOSED in this session** —
  `TestScorerDoesNotTrustArtifactMateriality` (§4) now fails if `calibration_verdict` ever reads
  `load_share` or `immaterial` from the artifact. It was untested, and a future refactor that
  "simplified" the scorer to trust the artifact would have converted this latent defect into
  silently wrong determinations.

---

## 6. GOVERNANCE

* **Rule 25 `[R-ISO-SCOPE]`** — shared scorer. Measured across three ISOs before proposing, nothing
  regenerated, put to the owner. The nyiso-232/233 precedent, followed rather than cited.
* **Rule 27 `[R-PUSH]`** — Opus session; `legitimacy_diagnostics.py` (3,545 lines) edited **locally
  with Edit**, never rewritten from generated content, and the pushed blob verified byte-identical.
* **Rules 21 / 24** — zero free parameters, zero new literals, no `ScenarioConfig` field touched.
* **Rule 28 `[R-MECH-MATRIX]`** — no mechanism was tested; no cell moves.
* **Rules 31 / 32 / 33 / 34** — zero LP, no shard, nothing deleted.
* **Rule 15 `[R-DASHBOARD]`** — no run produced; no keeper, sidecar or payload touched.

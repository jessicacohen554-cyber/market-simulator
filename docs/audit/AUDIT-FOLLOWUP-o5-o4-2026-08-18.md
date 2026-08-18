# AUDIT-FOLLOWUP — gap-register rows O5 and O4 (2026-08-18)

Charter: re-verify each row against current `main` (keepers and benches moved
repeatedly — re-derive, never trust the register's snapshot), root-cause from
committed artifacts only, then disposition. **No LP solve was run. No holdout
year was touched. No solve-affecting change is proposed in this document.**

Verified at `origin/main` @ `d1932e8` (2026-08-18). Deliverables: row O5
annotated + its residual fixed in-session with tests; row O4 annotated with a
re-measurement and an owner decision card (§2.4); DEBUG row B1 annotated as
stale; ledger at §4.

---

## 1. Row O5 — NEISO legacy-P2 anomaly

### 1.1 Re-verification: CLOSED, and it re-verifies STRONGER than as written

The row was closed by session neiso-99 on 2026-08-17, *after* this follow-up's
charter was drafted (the charter still describes neiso-98's sharpened, open
version). The closure re-verifies at HEAD, and on a **newer keeper set than
neiso-99 could cite** — ERCOT and CAISO have both been promoted since that row
was written (`ercot213` → `2026-08-17-ercot215-arm-decontam`, `caiso-197` →
`2026-08-17-caiso-200-h1-memberpanel`). Re-derived from each designated keeper's
own bundle `meta.json` this session:

| ISO | keeper at HEAD | `commitment` | `passes` |
|---|---|---|---|
| ERCOT | `2026-08-17-ercot215-arm-decontam` | `false` | `["P1"]` |
| CAISO | `2026-08-17-caiso-200-h1-memberpanel` | `false` | `["P1"]` |
| PJM | `2026-08-15-pjm-162-inputclock` | `false` | `["P1"]` |
| MISO | `2026-08-16-miso-160-wefor-shape` | `false` | `["P1"]` |
| NYISO | `2026-08-16-nyiso-140-layup-exclusion` | `false` | `["P1"]` |
| NEISO | `2026-08-17-neiso-99-joint-p1` | `false` | `["P1"]` |

All six designated keepers are on the production P0/P1 basis. The anomaly's
substantive claim — that NEISO's published numbers and scored determination came
from the archived pass — no longer holds for any ISO, and the property survived
two keeper promotions that happened after it was established.

### 1.2 Root cause of the RESIDUAL: the seam was closed at two of three paths

neiso-99 closed the propagation seam at `run_replay_bundle` and
`replay_keeper.main` — the two paths that rebuild solve kwargs from a committed
`meta.json` *after* the CLI gate `_enforce_legacy_p2_gate` has already run on
parsed args. **There is a third such path, and it was gated by neither that gate
nor the rule-22 holdout gate:**

`scripts/knob_jacobian.py::solve_year` (the standing D-11 knob-perturbation
diagnostic) reconstructs kwargs via `replay_keeper.build_kwargs(meta)` and calls
`rcf.solve_and_persist(**kwargs)` directly. Two independent exposures, both
measured at HEAD rather than argued:

1. **Archived P2.** `enforce_legacy_p2_kwargs` was not called, so a bundle
   recorded with `commitment=true` re-armed the archived pass silently — exactly
   the mechanism by which P2 crossed three NEISO keeper generations. This is
   **live, not hypothetical**: two committed bundles still carry
   `commitment=true` (`neiso86_2022_corrected`, `neiso97_dstrepair_A`).
2. **Holdout year.** `enforce_holdout_year_gate` lives at the *entry points*
   (`run_calibration_full.main`, `run_calibration.main`, `run_replay_bundle`,
   `replay_keeper.main`) and **never inside `solve_and_persist`**. `--year` on
   this script is a free `int`, so `--year 2019` would have solved a locked-test
   year — under an ACTIVE spend freeze — with nothing to stop it. The module's
   own docstring asserted it "never touches the 2022/H1-2026 quarantine, rule
   22"; that was an intention, not an enforcement.

Rule 22 names three gates (the CLI year gate,
`legitimacy_diagnostics.run_d6_quarantine`, `audit_keepers`). This solve path sat
outside all three.

A fourth `build_kwargs` call site, `run_calibration_full.py:3015`, was checked
and is **not** an exposure: it reconstructs the prior bundle's kwargs only to
*compare* them against the current run's for `--reuse-solved` eligibility, and
never solves from them.

### 1.3 Second residual: the closure shipped with no regression test

`grep` over all 460 test files finds **zero** references to `legacy_p2` at HEAD.
The gate that closes a governance seam which crossed three keeper generations
undetected had no test pinning it in either direction.

### 1.4 Disposition — REAL and SOLVE-NEUTRAL, fixed in-session

Both residuals are fail-closed guards on paths that are advisory and never a
keeper: they change no solve's numbers, they only refuse a solve that would
otherwise run ungated. Fixed here per the charter's solve-neutral disposition:

- `scripts/knob_jacobian.py` — `solve_year` now calls
  `enforce_holdout_year_gate` and `enforce_legacy_p2_kwargs` before it reaches
  `_load_reference()` or the solve; `--holdout-authorized` and
  `--enable-legacy-p2` added to the CLI and threaded through `compute_jacobian`
  via `functools.partial`; the module docstring's rule-22 claim rewritten from
  an assertion into a citation of the enforcement.
- `tests/regression/test_recipe_replay_gates.py` (new, 10 tests + 6 subtests) —
  pins the gate's semantics (every name in `LEGACY_P2_KWARGS` refused
  individually; the unlock works; the refusal is a **hard fail that does not
  mutate the recipe**, since a silent rewrite is the miso-50..53
  lossy-reconstruction class), pins that **all three** replay paths call the
  gate, and pins the two knob-jacobian refusals plus the unchanged
  production-recipe path — asserting `solve_and_persist` is never reached.

Verified: refusal on `--year 2019` fires on the **freeze** branch, ahead of both
the flag and the marker. `ruff check` / `ruff format --check` clean;
`tests/scoring/test_knob_jacobian.py` + `test_negative_control.py` + the new file
= 46 passed; `scripts/check_mechanism_matrix.py` green. No `ScenarioConfig` field
added, so no mechanism-matrix row is due (rule 28c).

---

## 2. Row O4 — Holdout-freeze premise

### 2.1 Re-verification: the numeric premise SURVIVES the guard

The row cites the neiso-63 finding (CC outage booking 23–46 % against a real
EFOR+planned norm of ~10–15 %). Since that finding, the merit-order guard was
**adopted** (charter §8, 2026-07-26) and every ISO's extract re-derived guard-on,
so the premise had to be re-measured rather than carried forward. Probe
`scripts/probes/audit_followup_o4_cc_envelope.py` →
`results/calibration/_audit_followup_o4_cc_envelope.json` (committed artifacts
only, no LP), `CC_REGULAR` capacity-weighted share of the capacity-year, windows
clipped per calendar year, denominator the union of kept + reclassified units:

| ISO | 2023 kept | 2024 kept | 2025 kept | pre-guard 2023–25 |
|---|---|---|---|---|
| ERCOT | 15.5 % | 16.2 % | 16.8 % | 19.6 / 21.0 / 20.3 % |
| CAISO | 25.8 % | 31.3 % | 36.7 % | 27.4 / 33.1 / 39.0 % |
| PJM | 18.2 % | 16.2 % | 17.0 % | 19.7 / 17.2 / 18.3 % |
| MISO | 16.9 % | 17.9 % | 21.4 % | 17.9 / 18.4 / 22.1 % |
| NYISO | 25.4 % | 29.6 % | 35.8 % | 41.4 / 40.8 / 42.5 % |
| NEISO | 32.9 % | 27.4 % | 14.2 % | 36.3 / 33.7 / 20.7 % |

**The pre-guard column reproduces the row's 23–46 % range** (17.2–42.5 % on this
construction), which is the check that my measurement matches the finding's.
Post-guard the envelope is **14.2–36.7 %**, and **17 of 18 ISO-years remain above
the 15 % norm ceiling**. The guard removed 1–16 pp — real, but it did not bring
the envelope into the norm band in any ISO but NEISO-2025.

**So the row's headline is NOT stale.** Every current keeper does still inherit
an availability envelope well outside the published-outage norm.

### 2.2 What HAS moved: the interpretation, and the charter's own status

What the register calls "still open" is, on the committed record, **closed on
evidence** as a *detector* question. Charter §9 records four investigative lanes,
all negative, none of which the register's one-line routing note reflects:

| lane | verdict | evidence |
|---|---|---|
| published-side re-measure | **PASSED** | neiso-66 §5b — residual tracks ISO-NE's published `uncommitted_available_gen_nonfast_mw` at +0.70…+0.85, **anti**-correlated with published outages (−0.85…−0.86) |
| commitment-economics discriminator | **NEGATIVE** | neiso-67 — per-unit AUC 0.47–0.57 over 18 configuration-years, below the marginal test in every one; sign inverts on the seam population |
| LP-side closure | **NEGATIVE** | neiso-68 — restoring the envelope injects a first-order **15–38 TWh of phantom dispatch**; no plausible price feedback (≈ −$3–4/MWh) closes it |
| cross-ISO day-grain replacement | **NEGATIVE** | 180 cells, candidate beats incumbent in 82 — a coin flip, median gain −0.0003 |

The over-count is a **definitional seam** — CNOG/ISO-NE publish *unavailability*,
the CEMS detector measures *non-operation* — confirmed against a published
instrument and shown not to be closable by any discriminator the admissible
inputs support. On that reading the gap to the ~10–15 % norm is **expected rather
than defective**, and the envelope deletion is "definitionally impure but
operationally load-bearing": the only mechanism in the system producing the
observed non-operation. §9 accordingly recommends **closing the charter with
cause and lifting the freeze fully**.

There is also live downstream evidence that the corrected envelope is being
consumed productively rather than sitting inert: NYISO's current keeper is
`nyiso-140-layup-exclusion`, a rule-17 `[R-FLOOR-WINDOW]` repair whose whole
object exists *because* the guard correctly un-booked lay-up — Port Jefferson
(2517) went to ~100 % model availability and was absorbing 72.6 % of what the
Long Island ST_GAS limb forced. Zero free parameters; registered under rule 1
even though it makes the volume residual worse.

### 2.3 What the freeze currently costs, measured

- **`complete` marker holders: NEISO, NYISO, PJM.** `final` is **empty** —
  deliberately, owner 2026-07-31 ("Neither is final").
- **Out-of-training runs registered at HEAD: exactly two**, both 2022, both under
  narrow owner lifts — `2026-08-06-neiso-2022-corrected-basis` and
  `2026-08-05-pjm-2022-touchpoint` (26 registered runs total at HEAD).
- **Locked-test spends ever: zero.** No 2019 or H1-2026 year has been solved,
  scored or registered for any ISO (owner decision D-23).
- **NYISO has held `complete` since 2026-07-31 and has never spent a
  touchpoint** — its validation ladder has been blocked by the freeze for its
  entire existence as a `complete` ISO.
- All three `complete` holders now read **`CALIBRATED`** (rubric v3.3,
  2026-08-17). At the last freeze sitting on 2026-08-06 none of them did.

The freeze's own `lifts_when` reads: *"either the corrected detector is adopted
and each affected ISO's keeper is re-audited on the corrected envelope, or the
charter is closed with cause and the extract is confirmed fit for purpose."*
**Both branches now read as satisfied on the committed record** — branch 1 by §8
(adopted; all six ISOs carry a registered re-audit arm), branch 2 by §9's
close-on-evidence. The freeze nonetheless remains ACTIVE, correctly: lifting is
an owner act and no session takes it by inference (§6, and the freeze file's own
`lifts_when`).

### 2.4 OWNER DECISION CARD — the CAMPD layup charter and the spend freeze

> **Evidence first.** `frontend/data/backcast/holdout-freeze.json` (`active:
> true`, declared 2026-07-25, re-armed 2026-08-06);
> `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §8 (adoption) and
> §9 (four-lane close-on-evidence + recommendation);
> `results/calibration/_audit_followup_o4_cc_envelope.json` (this session's
> re-measurement); `frontend/data/backcast/calibration-complete.json`.

**The question.** The freeze's stated lift condition is met on both of its
branches and the charter recommends closing with cause. Does the owner take that
step, or hold again?

**What is genuinely open is one thing only: the disposition act.** The detector
question is answered; the residual is explained, quantified, and bounded to a
definitional scope difference; the alternative directions are refuted by
measurement. Nothing further is buildable on the evidence — §9's option (a), a
commitment-aware second discriminator, is precisely what rule 1 `[R-STRUCT]`
forbids reaching for (a mechanism with no measured discriminating power).

**What is new since the owner last held (2026-08-06).** The owner was asked this
exact question that day and chose the narrow NEISO-2022 lift instead. Since then:
(i) all three `complete` holders now read `CALIBRATED` — none did on 2026-08-06;
(ii) NYISO's keeper turned over twice and its current keeper is itself a repair
*of* a corrected-envelope consequence, showing the envelope is being consumed
correctly downstream; (iii) the third-party audit (2026-08-15) elevated this row
to the largest open threat to the accuracy claims; (iv) this session's
re-measurement puts a number on the post-guard envelope for the first time
(14.2–36.7 %, 17/18 ISO-years above norm) rather than reasoning from the July
pre-guard figure.

**Quantified impact of holding.** Three `CALIBRATED` ISOs cannot spend an
iterable, re-spendable, model-selection-only validation year. NYISO has never
spent one. The touchpoint loop (rule 22: run → diagnose → re-train on 2023–2025
→ re-test) is the program's designed instrument for surfacing input defects, and
it has surfaced exactly that twice already (neiso-85/86's inverted gas basis).
The cost of holding is not a delayed skill claim — validation years are never
skill claims — it is the diagnostic loop staying shut.

**Quantified impact of lifting.** Bounded and reversible on the validation tier
by construction: 2020–2022 are iterable, re-spendable, and never a certified
out-of-sample number. The locked tier (2019, H1-2026) is untouched by this
decision either way — `final` stays empty and would need its own separate
declaration. The irreversible risk is confined to the locked tier, and no option
below touches it.

**Options.**

- **(A) Close the charter with cause, lift the freeze for the VALIDATION tier
  only, leave `final` empty. ← RECOMMENDED.** Takes §9's recommendation on its
  merits while conceding nothing on the touch-once tier. It matches the
  asymmetry the owner has twice relied on in the narrow lifts (iterable years
  are re-spendable; locked ones are not) and simply stops re-litigating it
  case-by-case. The 14.2–36.7 % envelope is carried **explicitly as a documented
  definitional seam** in the freeze file's closing entry and in each keeper's
  disposition note — not silently accepted — so any future reader sees the
  measured number and the four negative lanes together.
- **(B) Hold again, unchanged.** Defensible only if the owner judges the seam
  itself (not the detector) still a live threat to what a validation year would
  mean. But nothing further is measurable on the current evidence, so holding is
  an indefinite hold, not a wait for a pending result — and it should be recorded
  as such rather than as "lifts when the residual is explained", which is a
  condition that has now been met.
- **(C) Another narrow single-purpose lift** (e.g. NYISO 2022 only, re-arm
  after). The lowest-variance step and consistent with the two precedents; it
  gets NYISO its first touchpoint. But it is the third narrow lift on the same
  standing question, and each one spends an owner sitting to authorize a year
  the tier already exists to make spendable.

**Why (A).** The freeze was declared to stop a validation or locked-test year
being scored against an envelope that was "about to change materially". It has
changed, the change is adopted and measured, and the remaining gap is the one
thing a detector change provably cannot fix. Under rule 1 `[R-STRUCT]`, holding
a governance freeze open against a residual that four independent lanes have
shown is not closable is no longer preserving evidence — it is deferring a
decision the evidence has already made available. Recommend (A), with the
seam carried explicitly and the locked tier untouched.

**STOP.** Execution — editing `holdout-freeze.json`, closing the charter, or
solving any out-of-training year — is a separate signed charter. Nothing in this
session touched the freeze, the markers, or any holdout year.

---

## 3. Incidental — DEBUG row B1 is STALE

Measured while tracing the holdout gate's call sites for §1.2. Row B1 states
that `scripts/run_calibration.py` "carries no holdout year gate — the one solve
entry point outside the three-gate enforcement", citing "no `holdout_policy`
import in the script". **It does carry the gate**, at
`scripts/run_calibration.py:5888`:

```python
rcf.enforce_holdout_year_gate(args.year, iso, args.holdout_authorized)
```

It delegates to `run_calibration_full.enforce_holdout_year_gate` rather than
importing `holdout_policy` directly — deliberately, "rather than a second copy of
the policy (the `replay_keeper.py` / `backfill_nonfossil_hourly.py` pattern)",
per the comment above the call — which is why the import-grep that produced the
row missed it. The script's own module docstring says so at line 15. Row
annotated; no code change needed.

Note the irony worth recording: B1 named the wrong script. The real ungated solve
entry point was `knob_jacobian.py` (§1.2), which no row had.

---

## 4. Ledger — §8 gap-register changes made by this session

| row | action | disposition |
|---|---|---|
| O5 | annotated | **CLOSED** re-verified at HEAD on a newer keeper set than the closing session could cite; a **residual was found and FIXED in-session** (third ungated recipe-replay solve path + zero test coverage). No owner action outstanding. |
| O4 | annotated | **OPEN — owner decision card at §2.4.** Numeric premise re-measured and **survives** the guard (14.2–36.7 %, 17/18 ISO-years above norm). The *detector* question is closed on evidence across four lanes; what is open is the disposition act alone. Recommendation: option (A). |
| B1 | annotated | **STALE** — the cited gate exists at `run_calibration.py:5888` via delegation. No code change. |

Artifacts added: `scripts/probes/audit_followup_o4_cc_envelope.py`,
`results/calibration/_audit_followup_o4_cc_envelope.json`,
`tests/regression/test_recipe_replay_gates.py`. Changed:
`scripts/knob_jacobian.py` (two fail-closed guards + CLI flags + docstring).

*No LP solve was run; no holdout year was solved, scored or registered; no rubric
band was moved; no keeper, marker, or freeze file was touched; no mechanism-matrix
cell verdict moved.*

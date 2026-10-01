# FINDING — ercot-187: the ERCOT golden-hash drift is FULLY ATTRIBUTED to one owner-adopted CAMPD extract correction, ERCOT-185 is EXONERATED, and the golden is regenerated on that attribution

**Session:** ercot-187, 2026-08-10, branch `claude/ercot-leap-day-golden-hash-y39dp8`.
**Scope:** hygiene. **No mechanism armed, no `ScenarioConfig` field, no LP solved,
no run registered, no matrix cell minted, no year outside {2023, 2024, 2025}.**
**Keeper at entry and at exit: `2026-08-09-ercot185-shaped-partial` — UNCHANGED,
and untouched by anything here.**

---

## 1. Headline

The `test_fleet_arrays_golden` drift (ERCOT 2023, the `availability` and
`min_gen` hashes) is **outcome (a): explained by a landed, owner-adopted
change** — but **not** the one the session was opened on.

* **The cause is `6a8f285c` — "neiso-65: adopt guard-corrected CAMPD extracts,
  all six ISOs + layup companions" (2026-07-26 00:36 UTC)**, the merge of the
  merit-order guard the owner **ADOPTED** in
  `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §8 (verdict dated
  the same day). It reaches the fixture through exactly one file,
  `data/raw/campd-unit-outages.csv`.
* **The attribution is byte-exact, not inferred.** HEAD code with that one file
  reverted to its pre-guard blob reproduces **the original golden hashes on both
  fields, exactly**. So the model code is **provably inert across the entire
  drift** and this single authorized data correction owns **100 %** of it.
* **ERCOT-185 is EXONERATED by direct measurement, not by argument.** Both
  hashes are **byte-identical at `776bbf6b` (2026-08-08, before the ercot-185
  lane) and at HEAD (`fe9fa97f`, after it landed and was promoted)**. The
  session's opening hypothesis — that the day-shaped partial plateau fed these
  arrays — is **refuted**.
* **The golden is therefore regenerated**, with the attribution recorded in the
  fixture docstring and the commit. Exactly two fields move; the other 16 and
  `n_gen` (1,166) are unchanged.

**Two premises in the ercot-187 brief are corrected, both against interest:**
neither the failing set nor its tier is what was reported (§5).

---

## 2. The measurement

One probe reproduces `test_fleet_arrays_golden`'s own `_build_fixture_arrays` /
`_field_hashes` (frozen fixture: ERCOT, 2023, 8760 h, gas 2.13) and prints the
two hashes. Everything below is that probe, one run per state, ~70 s each.

**Three distinct states, not two:**

| state | `availability` | `min_gen` | `n_gen` | mean availability |
|---|---|---|---|---|
| committed golden | `15ff784ec04c…` | `25492e1ab661…` | 1166 | 0.7364 |
| capture-commit tree `635b95ee` / `3b7a893e` | `ac212cdc208f…` | `157f149a89b4…` | 1166 | 0.8194 |
| `776bbf6b` **and** HEAD | `e9aa3702f9f9…` | `553d02460f83…` | 1166 | 0.7615 |

The golden did not reproduce at **its own capture commit** — which is what makes
a naive commit bisect dead-end, and is exactly the trap that would have made
"regenerate on sight" bury the real object.

**The resolution: a single input, at three blobs.** `data/raw/campd-unit-outages.csv`
was traced as one of only 22 files the fixture opens (Python audit hook over
`open`), and it is the only one whose blob explains anything. Held at HEAD in
every other respect:

| `data/raw/campd-unit-outages.csv` held at | result | equals |
|---|---|---|
| **`59f8bc30`** (2026-07-24, `campd-outage-backfill 2018-2026`) | `15ff784ec04c…` / `25492e1ab661…` | **THE GOLDEN, exactly** |
| **`6a8f285c`** (2026-07-26, the guard adoption) | `e9aa3702f9f9…` / `553d02460f83…` | **HEAD, exactly** |
| **absent** (its state in the `635b95ee` tree) | `ac212cdc208f…` / `157f149a89b4…` | the capture-commit tree |

That closes it three ways at once:

1. **The golden's own provenance.** The fixture was captured on a working tree
   carrying this file at the content later committed as `59f8bc30` — i.e. the
   backfill existed in the capture container ~26 h before it was committed, and
   `635b95ee` therefore cannot reproduce its own golden. Not non-determinism,
   not an environment, not an uncommitted code state: one uncommitted **data**
   file, now identified by blob.
2. **The drift.** `59f8bc30 → 6a8f285c` is the whole of it.
3. **Code is inert.** HEAD code + the pre-guard blob = the original golden, bit
   for bit. Nothing in `src/` moved these arrays between 2026-07-23 and today.

**Direction and magnitude match the authorized change's own disclosure.**
`6a8f285c`'s message states the ERCOT reclassification as **1,352 windows /
3,986 GW-days** of economic layup leaving the mechanical extract for the
`campd-unit-outages-layup-*.csv` companion "which no loader reads by default"
(charter §3a D2). Removing outage windows returns capacity, so mean ERCOT 2023
availability rises **0.7364 → 0.7615 (+2.51 pp)**, and the file trace confirms
the companion is indeed never opened. `min_gen` moves with it because it is
scaled by the same availability envelope.

**Hypotheses tested and killed, so they are not re-opened:**

* **ERCOT-185 (the brief's hypothesis)** — identical hashes either side of it
  (`776bbf6b` vs HEAD). Independently: the mechanism is default-off with its own
  SP-3 identity proof, the fixture never opens `campd-partial-outages-shaped.csv`,
  and swapping `campd-partial-outages.csv` to its capture blob is **byte-inert**
  on both fields.
* **Environment / dependency drift** — the hashes are identical under
  ad-hoc `pip install -e .` (pandas 3.0.5 / pyarrow 25.0.1) **and** under
  `uv sync` (pandas 3.0.3 / pyarrow 24.0.0), and `uv.lock` is byte-identical at
  `635b95ee`, `776bbf6b` and HEAD.
* **The `data/clean` "data-lane" hypothesis** —
  `docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md` §6 listed this test as
  **"DATA (probable, UNCONFIRMED)"** and said not to close it without a
  provisioned clean store. **It is now closed, and it was wrong for this test:**
  the fixture makes **zero** clean-store probes at the default environment
  (`market_sim.data.outages._use_clean()` is gated on `MARKET_SIM_USE_CLEAN`,
  default off), instrumented by wrapping `clean_io.clean_exists`/`read_clean`.
  Arming the clean path is not the capture state either — it changes `n_gen`
  to 1,152, while the golden's 1,166 matches the raw path exactly.

## 3. Disposition — regenerate, and why that is the conservative call here

The fixture's docstring governs regeneration: "never to make a failing gate
pass — only under an owner-authorized behavior change, with the reason recorded
in the commit." Both conditions are met, on the record:

* **Owner-authorized behavior change.** Charter §8, owner verdict 2026-07-26:
  "each ISO's committed extract is re-derived guard-on and committed together
  with its `campd-unit-outages-layup-<ISO>.csv` companion — **the availability
  envelope every keeper reads now excludes the reclassified economic-layup
  windows**." That sentence *is* this drift.
* **Reason recorded**, in this FINDING, in the fixture docstring and in the
  regeneration commit.

The golden was simply never re-captured when that envelope moved — the "stale
golden" `docs/handoffs/ffr-1b-solve-year-availability-2026-08-01.md` §8 named ("stale golden — audit FR-26's family")
and no lane owned. **No keeper is affected**: the ERCOT keeper was solved
2026-08-09/10, two weeks *after* the guard landed, so the regenerated golden
moves the fixture **onto** the keeper's actual input basis rather than off it.

Regeneration is scorer/test-side only: **no LP, no re-solve, no bundle regen, no
registration** (unlike `tests/golden/ercot_2026_2040`, whose reseed is a
15-solve-year invocation under a separate signed authorization — that waiver is
untouched and is not invoked here). Verified: **exactly two of the 18 field
hashes change**, `n_gen` and the fixture block are unchanged, and the test
passes.

## 4. Why this was not, in fact, stop-the-line — stated explicitly

The brief's option (b) was "an unattributed change to a keeper input". The
measurement says the opposite on both halves: the change is **attributed** (one
blob, one commit), and it is the **adopted** output of a charter the owner
signed, whose ERCOT magnitude was disclosed in the commit that made it. What
went wrong was **not** a silent input change — it was that **no gate noticed the
golden had gone stale for fifteen days**, which is §5.

## 5. Two corrections to the brief's premises, and the standing hole they expose

**(a) The failing set is not six real failures — it is one, plus five
unprovisioned-data failures.** Measured this session at HEAD:

| test(s) | verdict |
|---|---|
| `test_fleet_arrays_golden` (2 hashes) | **REAL** — the attributed drift above; now green |
| `test_soundness::TestEndToEnd` capacity-evolution | **DATA** — `RuntimeError: confirmed-retirements: clean partition for ERCOT is absent`; green after `curate_confirmed_retirements.py` |
| 4 × `test_export::TestExportScenarioJson` | **DATA** — same `RuntimeError`; all 4 green after the same build |

`tests/regression/test_soundness.py` then runs **29 passed, 1 failed**, the
single failure being `TestPerformance::test_full_ercot_8760_timing` at
**31.13 s against a 30 s budget** on this 4-core box — a machine-speed artifact,
**not** touched here (loosening a perf budget to make it pass is exactly what
the golden discipline forbids).

**(b) None of the six is in the fast tier, so "the fast tier is red" is not the
shape of the problem.** Under CI's own expression
(`-m "not slow and not integration and not fulldata"`) all six are **deselected**:
`test_fleet_arrays_golden` 1 deselected, `TestEndToEnd` 6 deselected,
`TestExportScenarioJson` 4 deselected.

**(c) MEASURED, after this session's changes: the fast tier is 6,620 passed /
2 failed, and neither failure is any of the six.** Full serial run at this
branch (`-m "not slow and not integration and not fulldata"`, 18 m 35 s):
6,620 passed, 20 skipped, 49 deselected, 2 xfailed, 432 subtests passed, **2
failed** — both `tests/iso/ercot/test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion`,
on `ValueError: retirement_rule='pipeline' requires a simulation year`. That is
the **pre-existing** failure `ffr-3d` §6 already triaged as "REAL — D-1 fallout
… a test not updated for the flip → retirement lane (FFR-3C owns
`retirement_rule`)", it is **outside this branch's entire change surface** (six
files: the derive + its new test, the golden JSON + its fixture docstring, this
FINDING and the calibration log — nothing under `model/` or `tests/iso/`), and
it is **not touched here** (rule 25 — it is another lane's cell). **This
session adds ZERO fast-tier failures.**

**The hole that follows, filed for the owner (not fixed here — it is CI-policy
scope).** These guards live in tiers **CI never runs**: the `fast-tests` job
deselects them by mark, and a CI runner has neither `data/raw` nor `data/clean`
to run them with. So the one gate that watches the ERCOT availability envelope
went red on 2026-07-26 and was seen only as incidental noise in seven subsequent
sessions' triage tables (caiso-143, ffr-1b, ffr-3d, ffr-3u, ffr-5c, f2-45u,
miso-148) —
each correctly noting it was pre-existing, none owning it. **A golden nothing
schedules is not a guard.** Two candidate closures, both cheap, neither taken
unilaterally: a data-provisioned scheduled lane, or a committed staleness
expiry for this fixture on the `tests/golden/staleness_waiver.json` pattern.

## 6. Rule compliance

* **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`** — the accurate input is kept and
  the fixture moved onto it. Nothing was reverted to protect a hash.
* **Rule 25 `[R-ISO-SCOPE]`** — ERCOT only; the shared extract's other five ISO
  blocks are untouched and no other ISO's fixture, keeper or cell is edited.
* **Rule 28 `[R-MECH-MATRIX]`** — **no cell minted**: no mechanism was proposed,
  armed, tested or refuted. ERCOT-185's own cell stands as its lane set it; this
  session only measured that it is not implicated.
* **Rule 22 `[R-HOLDOUT]`** — the only year touched is 2023, in-sample.
* **Rule 27 `[R-PUSH]`** — no file ≥300 lines rewritten from regenerated
  content; edits are local and pushed as on-disk bytes.
* **Rule 15 `[R-DASHBOARD]`** — not engaged: no run was solved or registered.

**Instruments** (session-local, not committed): a fixture-hash probe, a
`clean_io` call tracer and a `sys.addaudithook` file-read tracer. Every number
above is reproducible from committed artifacts plus `git`.

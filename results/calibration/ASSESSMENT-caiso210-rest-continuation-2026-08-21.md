# ASSESSMENT — caiso-210: Branch A executed (**REST CONTINUES**). Full record re-verified on committed bytes at a HEAD that had moved again — and **one new defect found**: a cross-ISO **STALE BENCHMARK** flag now fires on all three CAISO bench parts. Measured here and **it is stamp-absence, not drift** — CAISO's parts are content-reproducible at HEAD. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); owner packet unchanged at **TWO** items (2026-08-21)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts and from git. **No mechanism was tested, so rule 28b does not attach
and no cell verdict moves** (the caiso-206 / caiso-207 / caiso-208 / caiso-209
precedent, applied identically).

---

## §0 — Which branch, and why

The charter is explicit: **Branch A is the default and executes unless an owner
order says otherwise; Branch B opens *if and only if* the owner funds
tail-formation object (a) or (b).** No funding order issued into this session.

So caiso-203 **ruling 2 (FINAL)** governs, and it funds neither object. The
blocker is not a planning obstacle to route around — it is the finding itself:
the in-model lever queue is **empty with every cell adjudicated**, re-proven by
measurement at caiso-205 (the last chartered lever came back byte-identical in
2023/2025; floor max $14.5 in 2024 — *an inert arm is not a lever*), and the
required move is a broad **~$2–3/h level-down across the sub-$60 buckets**
(caiso-202 §B) for which **no admissible in-model instrument exists** (§F).
Reaching C3a through a §F-killed lever would be a rule-13 act; **NOT-YET is the
honest fallback** (ruling 5).

**Branch A executed. Nothing solved, nothing armed, nothing registered.**

### A note on this session's number

The charter delivered to this session is the **caiso-209** charter, but caiso-209
had already executed and merged (commit `0cd6e2d`, in `origin/main`; its
assessment is `ASSESSMENT-caiso209-rest-continuation-2026-08-21.md`, closing
*"Next number: caiso-210"*). This session is therefore **caiso-210**, and the
charter it carries is **one session stale** in one concrete respect, which
matters and is recorded here: its guardrail line still reads *"C3b
(0.097/0.174/0.181 vs 0.20)"* — the triplet caiso-209 measured to be the
**superseded caiso-197 keeper's**. See §1 row 12: the corrected baseline is
re-verified independently this session.

---

## §1 — Standing state re-verified (committed bytes only)

I re-verified rather than carried forward, because **HEAD had moved past the
caiso-209 baseline** — `origin/main` at **cf7b3fd**, against the **6fa0de2**
caiso-209 recorded. That decision is what surfaced §2.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly; rubric **v3.4**; basis *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` carries no ISO; CAISO in `withdrawn` — **in neither grant block** |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25, re-armed 2026-08-06) |
| 8 | registrations | registry sidecars + run payloads | keeper + the caiso-205 pair — all three **present and tracked**, years `[2023, 2024, 2025]` each — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 33 · I 15 · R 9 · O 6 · G 5 = 132** — exactly caiso-209's re-baseline; the charter's 131 is superseded |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, keeper stamps match, **§5.x prose headers match every `keepers/<ISO>.json`** (the NYISO header warning caiso-209 observed is **gone**), *"0 unresolvable beyond the ratchet"* |
| 11 | **gate-posture cross-check** (caiso-208's addition) | shard `gates` stamp + §5.2 header read back against the verdict | **BOTH CURRENT** — caiso-209's repair held on both surfaces |
| 12 | **gate-MAGNITUDE cross-check** (caiso-209's extension) | `calibration_verdict.py --json` → `criteria.price_shape.records` | **C3b NRMSE 0.098 / 0.179 / 0.182** vs ≤0.20 — **independently re-read, not carried forward.** caiso-209's correction is confirmed |

**Scorecard, re-verified in full** (`grade_summary`: scored 8, ledgered 1,
fails 1):

| criterion | tier | status | magnitude (2023 / 2024 / 2025) |
|---|---|---|---|
| C1 fuel-mix | load-bearing | **PASS** | **12/12 rows, free 8/8** |
| C2 system volume | load-bearing | PASS | — |
| C3a mean LMP | load-bearing | **FAIL** — the SOLE load-bearing failure | **+4.1 % (PASS) / +12.8 % / +15.7 %**, judged vs ACTUAL RT LMP only |
| C3b price shape | load-bearing | PASS | **NRMSE 0.098 / 0.179 / 0.182** vs ≤0.20 |
| C3c price tail | supporting | **CAVEAT** (the single ledgered) | 0 h vs 47 h; 1 h vs 35 h; **2025 PASS** |
| C4 dispatch corr | supporting | PASS | — |
| C6 governance | protective | PASS | — |
| C8 forced share | protective | PASS | — |

Caveat budget: **ledgered 1 of 1, protective 0 of 0** — at budget, not over it.
**C3c standing rule correctly silent**: guard (a) is *lone failure only*, C3a
also fails, so the determination stays **NOT-YET** and C3c reads CAVEAT (never
PASS) at full magnitude, as designed.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B.

---

## §2 — THE NEW FACT: a **STALE BENCHMARK** flag now fires on all three CAISO bench parts — and it is **stamp-absence, not drift**

**No prior CAISO record carries this**, and it is the one substantive thing this
session adds. caiso-206 through caiso-209 saw no such warning; it appears on
every CAISO scorer invocation at this HEAD.

### 2.1 What fired, and where it came from

`audit_keepers.py`, `build_status.py` and `calibration_verdict.py` all now print:

```
[!] STALE BENCHMARK: CAISO part(s) 2023.json.gz, 2024.json.gz, 2025.json.gz were
    NOT written by the builder at HEAD (fingerprint ded4ca25749a). C1's metered
    actuals below may not be reproducible …
```

It is **foreign in origin**: commit **`e113118`** (2026-08-21 05:27 UTC, session
**nyiso-148**, owner ruling *"sweep and fix"*) — which landed **after** caiso-209
committed at 03:05 UTC. That commit introduces `scripts/lib/bench_stamp.py`
(a `meta.builderFingerprint` on every part), `scripts/check_bench_freshness.py`
(HARD on fingerprint mismatch **or absence**, SOFT on intervening engine
commits), and the scorer's warning line.

The defect it addresses is real and serious: a bench part is refreshed only when
a registering bundle happens to carry the benchmark inputs, and the parts are
byte-deterministic, so a part that goes un-refreshed shows **no git diff and no
warning** while the builder moves underneath it. On NYISO, regenerating moved
CC_REGULAR-2024's metered actual by **~4 TWh and flipped every registered NYISO
run to NOT-YET, the keeper included**.

**Sizing at this HEAD** (`check_bench_freshness.py --warn-only`): **20 parts
checked, 17 STALE, 0 with engine drift** — five of six ISOs (CAISO, ERCOT, MISO,
NEISO, PJM). Only NYISO's three are current, because nyiso-148 regenerated them
itself. **Every one of the 17 carries no fingerprint at all** (`(none: predates
the stamp)`), CAISO's three included — verified by direct read of
`meta.builderFingerprint` on each part.

So the flag is, on its face, a **mechanism-introduction artifact**: it fires on
absence for every part written before 2026-08-21. It cannot, by construction,
distinguish *"written by a builder identical to HEAD's"* from *"written by a
materially different builder"*. That distinction is what actually matters to
CAISO's C1 verdict, and it is answerable from git.

### 2.2 The measurement: **CAISO's parts ARE content-reproducible at HEAD**

CAISO's three parts were last written at **`fce890d`** (2026-08-17 20:49 −0700).
Taking each tier in turn:

**(a) The HARD tier — `BUILDER_SOURCES`, the four scripts the fingerprint
hashes.** Exactly **two** commits since `fce890d`, and I verified each myself
rather than accept the commit messages:

* **`01db36d`** (nyiso-147, `render_calibration_html.py`) adds a `measured=`
  path to `_btm_share`. It is reached only through
  `if meta.get("nyiso_chp_btm_measured") and meta.get("iso") == "NYISO"`, which
  leaves `_btm_measured = None` for every other ISO; `_btm_share` then short-
  circuits on `if measured is not None and …` and takes the **unchanged**
  branch. CAISO's keeper meta carries neither key. **Provably inert for CAISO**,
  double-gated.
* **`e113118`** (nyiso-148, `backcast_artifacts.py` + `bench_stamp.py`)
  changes `write_bench_part` to add **exactly one key**,
  `meta.builderFingerprint`. The `bench` payload is untouched.

**(b) The tier that is covered by NEITHER check.** The functions that actually
compute a part's numbers — `_benchmark_eia923_frame`, `_campd_hourly_frame`,
`_eia930_frame`, `_fleet_group_by_code`, `_parasitic_factor_map`,
`rebuild_benchmark`, and the five helpers `_benchmark_eia923_frame` delegates to
— all live in **`scripts/run_calibration_full.py`**, which is in neither
`BUILDER_SOURCES` nor `ENGINE_PATHS`. **Twelve** commits landed on that file
since `fce890d`. Hashing each function's source at `fce890d` against HEAD:

| function | verdict |
|---|---|
| `_eia930_frame`, `_eia930_frame_generic`, `_fleet_group_by_code`, `_campd_hourly_frame`, `_benchmark_eia923_frame`, `rebuild_benchmark`, `_parasitic_factor_map` | **all IDENTICAL** |
| `_plant_class_shares`, `_backfill_eia923_with_campd`, `_eia923_frame`, `_backfill_chp_eia923_from_donor`, `_backfill_renewables_eia930` | **all IDENTICAL** |

Twelve for twelve, byte-identical.

**(c) The SOFT tier — the engine import closure.** 21 commits landed under
`ENGINE_PATHS` since `fce890d`, but the benchmark's actual closure is untouched:

* `eia923.py`, `campd.py`, `plant_taxonomy.py`, `eia_loader.py`,
  `iso_configs.py` — **0 commits each**.
* `load_fleet_from_csv` (what `_fleet_group_by_code` calls) lives in
  `fleet/eia860.py` — **0 commits**, hash identical.
* `chp_btm_pct` — hash **identical**; `01db36d` only *adds* a NYISO-only
  sibling `measured_chp_btm_pct_nyiso()` beside it.
* `fleet/__init__.py` changed, but by **+5 purely additive re-export lines**;
  `load_fleet_from_csv` and `__all__` are untouched.

The 15 engine files that did change are dispatch / commitment / offer machinery
(`offer_curves`, `outages`, `reserve_*`, `perplant_min_run`, `chp_layup`,
`fleet/{arrays,assembly,campd_bins}`, `constants`, `scenarios`) — outside the
benchmark path.

**Conclusion: for CAISO the HARD flag is stamp-absence alone.** The committed
parts' `bench` payload is what the builder at HEAD would produce. **C1's 12/12
PASS is reproducible, and the keeper's determination is unaffected.**

**Two honest limits on that conclusion**, stated rather than buried:

1. **This is a static reproducibility argument, not a byte-level
   regeneration.** I did not re-run the builders. The container has **no
   scientific stack** (`numpy` is absent, which is also why the stdlib-only
   scorer runs here at all), and the keeper's `_shared/CAISO/` input store and
   dispatch parquets are **not committed** — only the slim bundle is. A
   regeneration would be the stronger evidence; it was not available.
2. **One of my own checks was vacuous on first pass, and I corrected it.**
   `src/market_sim/data/fleet.py` **does not exist** — `fleet` is a package — so
   its initial "0 commits" carried no information. Re-run against
   `fleet/eia860.py` and `fleet/__init__.py`, it is the result reported above.
   Flagged because the same trap will catch the next session that checks a
   closure by file path.

### 2.3 Two defects in the new checker — routed OFF this lane (rule 25)

Both belong to nyiso-148's mechanism, not to CAISO, and neither is CAISO's to
repair. Recorded because sizing them is what this session was positioned to do:

* **D1 — COVERAGE GAP.** The five benchmark-frame builders live in
  `scripts/run_calibration_full.py`, which is in **neither tier**. That file is
  where a part's numbers are actually produced. A real change there would move
  every ISO's actuals and be **invisible to both the HARD fingerprint and the
  SOFT engine count** — which is precisely the failure mode the stamp was built
  to catch. That the twelve commits since `fce890d` happened to leave those
  functions untouched is luck this time, not coverage.
* **D2 — THE SOFT TIER IS UNREACHABLE FOR EXACTLY THE PARTS THAT NEED IT.**
  `check_bench_freshness.py` `continue`s immediately after the HARD branch, so
  engine drift is **never computed for a stale part**. With 17 of 20 parts
  stale, the summary line **"0 with engine drift" is vacuous for all 17** — it
  reads as reassurance and carries no information. The soft tier only begins
  reporting once every ISO has regenerated, i.e. it is dark for the entire
  period during which it is most needed.

### 2.4 What CAISO can, and cannot, do about it

**The sanctioned fix path is not available to this lane.** The warning
prescribes `run_calibration_full.py --rebuild-benchmark <bundle>` then
`dashboard_add_run.py`. For CAISO's keeper that cannot run: only the **slim**
bundle is committed (`calibration_attestation.json`, `hourly/`,
`legitimacy_diagnostics.json`, `meta.json`, `metrics.json`, `run_config.json`),
the `_shared/CAISO/` store its `meta.json` points at is **absent from disk**,
and `rebuild_benchmark` ends in `report_run(bundle)` over dispatch parquets that
were never committed. Restoring CAISO's stamp therefore requires a **re-solve** —
a Branch B act, which no funding order authorizes.

**And it is not needed for correctness.** §2.2 establishes the numbers are
reproducible; what is missing is the *stamp*. The two facts together give the
recommendation:

> **CAISO's bench stamp should be restored as a by-product of the next CAISO
> solve, whenever one is funded — not as an errand of its own.** Regenerating
> ahead of that would also be premature on nyiso-148's own sequencing, which
> keeps the benchmark **root cause OPEN and chartered BEFORE any
> re-calibration**.

---

## §3 — The owner packet, unchanged at **TWO** items

Carried from caiso-208 §3 / caiso-209 §4 with no new evidence in either
direction. **§2 does not add a third item** — it is a records-and-diagnosis
finding with no CAISO decision attached and no available action, exactly as
caiso-209's §3 was.

### (1) Fund a tail-formation object

| object | status | measured reach |
|---|---|---|
| **(a) PS water-state hourly intake** | declined **3×** | **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move **at its most favourable bound** |
| **(b) import spot-capacity derivation** | not funded | direct λ share **< 5 %** of the positive gap |

**Neither closes C3a on its own arithmetic.** If no funding order issues, **rest
is correct**. Should one issue, Branch B's pre-registration must state up front
what a **partial** close is worth and what verdict a partial earns — object (a)
cannot reach the number even at its most favourable bound.

### (2) F-3 — arming posture of `caiso_ra_mpb_capacity_anchor`

Built, measured, merged, **default-OFF**, keeper-inert by construction. Arming
is an owner decision. FFR-4F's pre-registered **trap test fired**: total thermal
built is **identical to the megawatt** in both arms (10,186.3 MW), and the only
change is **the label on 1,000 MW**. FC-2 row 4 improves *solely* because
capacity moved into a channel the numerator does not count — **channel
substitution, not a gain**.

**Recommendation, for the owner's convenience only: keep default-OFF** absent a
reason unrelated to row 4.

---

## §4 — DO-NOT-REDO

Everything in caiso-206 §B, caiso-207 §5, caiso-208 §4 and caiso-209 §5 carries
forward **verbatim**. In particular: the caiso-202/203/204/205 lists; the FFR-4F
A/B and the 138.36 anchor derivation; the anchor's `O` cell means *adjudicated,
merged, arming owner-pending* — **never** *untested*; the swept
`frontend/data/hindcast/` sidecars **stay swept**; the C3a basis is CLOSED
(actual RT LMP only); the v3.4 C1 re-score is **not** open (C1 passes 12/12,
free 8/8); the retained v3.3 promotion-time blocks are **not** live; the census
is **132**, not 131; and **C3b's baseline is 0.098/0.179/0.182** — do not read it
as a regression, and do not "fix" it.

**Added by this session:**

1. **Do not re-derive the CAISO bench-staleness exposure.** It is measured in
   §2.2: two builder commits both provably inert for CAISO, twelve frame-builder
   functions byte-identical, and the engine import closure untouched. The flag is
   **stamp-absence**. Re-running the git archaeology expecting a different answer
   is a frozen cell.
2. **Do not regenerate CAISO's bench parts on this lane.** It cannot run without
   a re-solve (§2.4), it is not needed for correctness, and it is premature on
   nyiso-148's own sequencing while the root cause is open.
3. **Do not read "0 with engine drift" as evidence of anything** for a stale
   part — the checker never computes it (§2.3 D2).

**New evidence still means exactly one thing: a keeper whose own scored path
spikes.**

---

## §5 — Filed items

1. **Stale DOF-ledger text** — `offer_curve_by_group` still reads
   `"identification": "residual"` on the keeper attestation, overstating the
   residual content for CAISO's CC_REGULAR / CT_PEAKER bands (measured from
   OASIS `PUB_DAM_GRP` since 2026-08-02, caiso-202 §H). **Re-verified still open
   by direct read of the ledger's 10 entries this session.**
2. **Diagnostics vintage drift** — keeper-vintage `legitimacy_diagnostics.json`
   differs from fresh bundles on one D-4 row (chp_steam plant 10034). Carried.
3. **Site retention** — the caiso-205 pair postdates the keeper and comes off at
   the next promotion in the ordinary way. Not an anomaly.
4. **Session mechanics** — regenerate `data/clean` before any solve; **ONE**
   CAISO 3-year invocation at a time (~13.3 GiB cgroup cap). Note additionally:
   **this container has no scientific stack** (`numpy` absent), so any solve or
   benchmark rebuild needs one installed first.
5. **C3b magnitude on the keeper's own assessment** (caiso-209) — a session that
   produces a **promotion** should re-measure and re-state the whole scorecard
   from the verdict output rather than carrying rows forward.
6. **NEW — CAISO's bench parts are unstamped.** Not a correctness defect
   (§2.2), but the parts will keep tripping the HARD flag on every scorer run
   until regenerated, and the fix needs a solve (§2.4). **Discharge as a
   by-product of the next funded CAISO solve** — verify with
   `check_bench_freshness.py --iso CAISO` afterwards.

Items 1, 2, 5 and 6 are fixable only at a session that produces a solve or a
promotion; none is fixable without one.

**Routed OFF this lane (rule 25):**

7. **The two checker defects, D1 and D2** (§2.3) — nyiso-148's mechanism.
   Route to that lane or to governance. D1 is the substantive one: the tier that
   produces the numbers is covered by neither check.
8. **The five-ISO regeneration and the CI gate.** nyiso-148 deliberately did not
   wire `check_bench_freshness.py` in as a hard gate ("nineteen of twenty
   committed parts are stale, so gating now would red-light every PR"). The
   sequence it names — each ISO regenerates, then the gate goes on — is a
   **program-level** schedule, not something any single ISO lane can complete.
   CAISO's own leg is filed item 6 and is blocked on funding.
9. **Program-wide stale registration citations.** `cccc911` (2026-08-19) swept
   all 187 canonical `frontend/data/hindcast/` sidecars, so every ISO's citations
   of registered forecast-run ids point at runs no longer on the forecast
   dashboard — including the **shared** `mechanism-matrix.js` base-row text for
   `caiso_ra_mpb_capacity_anchor`. Fixing only CAISO's would make the shared file
   inconsistent. **Still routed.** *(The NYISO §5.x prose-header warning
   caiso-209 observed is now **resolved** — the guard reports headers matching
   every keeper shard. The `scenarios.py` anchor line-number drift remains at
   **0 unresolvable beyond the ratchet**.)*

---

## §6 — Governance

* **Rule 1 `[R-STRUCT]`.** Nothing tuned to a residual; no mechanism added,
  armed or removed. §3(2) explicitly declines to recommend arming for the row-4
  improvement, because that improvement is channel substitution.
* **Rule 12 `[R-PARALLEL]` / mechanics.** No solve run, so neither the year loop
  nor the memory cap was engaged.
* **Rule 13 `[R-MEASURED]`.** No measured outcome fed back; §0 records why
  reaching C3a through a §F-killed lever would be a rule-13 act.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced, so no registration is
  due.** The caiso-134/140/150/202/206/207/208/209 disposition applies unchanged.
* **Rule 16 `[R-ALLYEARS]`.** All three CAISO registrations carry
  `[2023, 2024, 2025]`; no single-year bundle exists on the lane.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO absent
  from both `complete` and `final` (it sits in `withdrawn`); freeze **ACTIVE**.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The shared `mechanism-matrix.js` was
  not touched; the two checker defects and the program-wide sweep consequence are
  *reported*, not repaired.
* **Rule 27 `[R-PUSH]`.** Opus. **No source file under `src/market_sim/` was
  modified** — the deliverable is records only. Every edited file was edited in
  place, never regenerated from response content.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does not
  attach and no cell verdict moves.** The `gates` stamp edit is a
  records-truthfulness refresh on the caiso-208 / caiso-209 / neiso-100
  precedent, not a verdict change; the §5.2 prose block records the session. The
  census is **unchanged at 132** from caiso-209's re-baseline.

---

## §7 — Record changes

- **This file**; `docs/calibration-log/caiso.md` caiso-210 entry; matrix §5.2
  caiso-210 block; CAISO shard `gates` stamp refreshed with the §2 finding.
- **Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, every
  bench part, and every source file: UNCHANGED.** No run registered (none
  produced). No cell edited by this lane. **Nothing regenerated** — in
  particular, no bench part was rewritten.

Next number: **caiso-211**.

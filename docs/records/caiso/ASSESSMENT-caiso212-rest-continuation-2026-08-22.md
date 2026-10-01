# ASSESSMENT — caiso-212: Branch A executed (**REST CONTINUES**). Full record re-verified on committed bytes at a HEAD that moved heavily (35 commits since caiso-211's tip) — and the session's one chartered addition executed: the **frame-builder re-hash across `fce890d..HEAD`**. The builder fingerprint has MOVED (`ded4ca25749a` → `dbea7bf45111`), so the caiso-210/211 identity terms are dead; the stamp-absence conclusion was **RE-DERIVED from scratch on this session's own measurement and HOLDS** — the caiso-210 twelve hash byte-identical (twelve for twelve, again) and the one changed frame builder, `_btm_frame`, is **proven CAISO-inert at three independent levels**. Keeper unchanged at `2026-08-17-caiso-200-h1-memberpanel` (NOT-YET); owner packet unchanged at **TWO** items (2026-08-22)

**No solve. No probe. No LP was spent, no bundle produced, no dashboard
registration due.** Everything below is measured from already-committed
artifacts and from git. **No mechanism was tested, so rule 28b does not attach
and no cell verdict moves** (the caiso-206 … caiso-211 precedent, applied
identically).

---

## §0 — Which branch, and why

The charter is explicit: **Branch A is the default and executes unless an owner
order says otherwise; Branch B opens *if and only if* the owner funds
tail-formation object (a) or (b).** No funding order issued into this session.

So caiso-203 **ruling 2 (FINAL)** governs, and it funds neither object. The
blocker is unchanged: the in-model lever queue is **empty with every cell
adjudicated**, re-proven by measurement at caiso-205; the required move is a
broad **~$2–3/h level-down across the sub-$60 buckets** (caiso-202 §B) for
which **no admissible in-model instrument exists** (§F). Reaching C3a through a
§F-killed lever would be a rule-13 act; **NOT-YET is the honest fallback**
(ruling 5).

**Branch A executed. Nothing solved, nothing armed, nothing registered.**

*(Numbering consistent: the charter delivered is the caiso-212 charter and
caiso-211 closed "Next number: caiso-212".)*

---

## §1 — Standing state re-verified (committed bytes only)

`origin/main` at **c55da9c** against the **317be02** caiso-211 measured from —
**35 commits (12 merges), 185 files, +27,789/−4,214**: nyiso-149 (benchmark
root cause CLOSED + the first NYISO keeper CALIBRATED on the authoritative
benchmark, PR #4183), miso-175 (PR #4182), ercot-226 (PRs #4184/#4186),
site-facts-2 (PR #4187), the NEISO mystic-rescore (PRs #4185/#4188). Every
standing number below was re-measured at this HEAD, never carried.

| # | check | instrument | result |
|---|---|---|---|
| 1 | keeper identity | `keepers/CAISO.json` | `2026-08-17-caiso-200-h1-memberpanel` — **unchanged** |
| 2 | determination | `calibration_verdict.py --run-id <keeper>` (never a solve) | **NOT-YET**, reproduced exactly; rubric **v3.4**; `reasons` = *"undocumented out-of-tolerance (FAIL) criteria: price_mean"* |
| 3 | keeper text truthfulness | `audit_keepers.py --iso CAISO` | **PASS, 0 failures / 0 warnings** |
| 4 | status sync | `build_status.py --iso CAISO --check` | *"status parts in sync (1 keepers: CAISO)"* |
| 5 | DOF ledger | keeper `calibration_attestation.json` | **10/7** (`n_entries: 10`, `n_residual: 7`) |
| 6 | holdout posture | `calibration-complete.json` | `complete` = {NEISO, NYISO, PJM}; `final` carries no ISO; CAISO in `withdrawn` — **in neither grant block**, and its withdrawn entry is **byte-equal across the whole delta** |
| 7 | spend freeze | `holdout-freeze.json` | **ACTIVE** (`active: true`, declared 2026-07-25) |
| 8 | registrations | registry sidecars + run payloads | keeper + the caiso-205 pair — all three **present and tracked**, years `[2023, 2024, 2025]` each, payloads on disk — **no out-of-training year touched** |
| 9 | matrix cell census | CAISO shard | **K 64 · U 33 · I 15 · R 9 · O 6 · G 5 = 132** — exactly as the charter pre-registered; **n/a 92 → 94**, the whole delta being the two foreign rule-28c `·` cells (`miso_seam_envelope_hour_ending_key`, ad0f85a miso-175; `hindcast_verified_announced_exits`, 9c5a635 — `fc: "U"`). The CAISO shard's total movement across the delta is **+2 lines**, those two cells |
| 10 | matrix integrity | `check_mechanism_matrix.py` | **exit 0**, *"integrity OK"*, keeper stamps match every `keepers/<ISO>.json`, §5.x prose headers match every keeper shard, *"0 unresolvable beyond the ratchet"* |
| 11 | **gate-POSTURE cross-check** (caiso-208's protocol) | shard `gates` stamp + §5.2 header read back against the verdict | §5.2 header **CURRENT**. Shard stamp: open-gate content current, but its **HEAD-relative bench-staleness facts are superseded** (fingerprint, commit counts — §2), so the stamp is **refreshed this session** on the caiso-208/209/210 records-truthfulness precedent |
| 12 | **gate-MAGNITUDE cross-check** (caiso-209's protocol) | `calibration_verdict.py --json` | **every recorded magnitude re-read independently and confirmed** — scorecard below; nothing carried forward unread |

**Scorecard, re-stated in full from this session's own `--json` read**
(`grade_summary`: scored 8, target_grade 6, commercial_grade 0, ledgered 1,
fails 1):

| criterion | tier | status | magnitude (2023 / 2024 / 2025) |
|---|---|---|---|
| C1 fuel-mix | load-bearing | **PASS** | **12/12 rows, free 8/8** (pinned: CC_CHP, ST_CHP) |
| C2 system volume | load-bearing | PASS | — |
| C3a mean LMP | load-bearing | **FAIL** — the SOLE load-bearing failure | model/actual $/MWh **56.40/54.17 (+4.1 %, PASS) / 39.07/34.65 (+12.8 %) / 39.82/34.42 (+15.7 %)**, judged vs ACTUAL RT LMP only |
| C3b price shape | load-bearing | PASS | **NRMSE 0.098 / 0.179 / 0.182** vs ≤0.20 — 2025 margin **0.018**, composition watch live |
| C3c price tail | supporting | **CAVEAT** (the single ledgered) | 0 h vs 47 h; 1 h vs 35 h; **2025 PASS** (0 h vs 8 h) |
| C4 dispatch corr | supporting | PASS | — |
| C6 governance | protective | PASS | — |
| C8 forced share | protective | PASS | — |

Caveat budget: **ledgered 1 of 1, protective 0 of 0** — at budget, not over it.
**C3c standing rule correctly silent**: guard (a) is *lone failure only*, C3a
also fails, so the determination stays **NOT-YET** and C3c reads CAVEAT at full
magnitude, as designed.

**Foreign movements verified legitimate, not assumed:** the
`calibration-complete.json` delta (453 ± lines) is a re-serialization plus the
**NYISO re-key at its nyiso-149 promotion** (keeper
`2026-08-19-nyiso-146c-state-scoped` → `2026-08-22-nyiso-149-duty-curve`,
determination CALIBRATED **re-verified at the promotion without a solve**, rule
22 D-5(b)) — structural key-diff shows **zero keys added or removed**, the
`note` and all 17 `intake_log` entries intact, and CAISO's `withdrawn` entry
byte-equal. **Zero movement across the whole delta** in
`calibration_verdict.py`, `audit_keepers.py`, `build_status.py`,
`holdout_policy.py`, `check_mechanism_matrix.py`, `check_bench_freshness.py`
and `bench_stamp.py`.

**Branch A discipline honoured:** no solve, no probe, no re-litigation of the
C3a basis (CLOSED — caiso-203 ruling 1), no re-run of the caiso-204
identification, the caiso-205 A/B, or the FFR-4F anchor A/B.

---

## §2 — THE SESSION'S ONE ADDITION, EXECUTED: the frame-builder re-hash across `fce890d..HEAD` — the fingerprint has MOVED, the caiso-210/211 terms are dead, and the stamp-absence conclusion **RE-DERIVES AND HOLDS on this session's own measurement**

The charter was explicit that the caiso-210/211 conclusion does **not**
automatically carry at this HEAD: its own terms were *identical fingerprint AND
frame functions byte-identical*, and `scripts/run_calibration_full.py` — the
file that holds the number-producing tier — has now moved, **including hunks in
`_btm_frame`**, the function nyiso-149 proved feeds the bench part. Both terms
were re-measured. One is dead; the conclusion survives on new evidence.

### 2.1 What moved

* **`BUILDER_SOURCES` (the HARD-tier hash set) now carries THREE commits since
  `fce890d`**, not caiso-210's two: `01db36d` and `e113118` (both adjudicated
  at caiso-210) plus **`28ac3c2`** (nyiso-149, 2026-08-22 03:24 UTC — the
  bench-basis pin, on `render_calibration_html.py`). `render_backcast.py`: 0
  commits. Consequence: **the builder fingerprint at HEAD is `dbea7bf45111`** —
  computed independently from `bench_stamp.builder_fingerprint()` and matching
  the banner every CAISO scorer invocation now prints. The caiso-211 §2(2)
  argument ("identical fingerprint ⇒ conclusion carries") is **no longer
  available**, exactly as the charter anticipated.
* **`scripts/run_calibration_full.py` now carries 15 commits since `fce890d`**
  (the caiso-210 twelve plus `0948504`, `28ac3c2`, `ad0f85a`), the file moving
  11,965 → 12,263 lines.

### 2.2 The measurement: twelve for twelve identical; `_btm_frame` changed and **provably CAISO-inert**

**(a) The caiso-210 twelve.** Extracting `run_calibration_full.py` at
`fce890d` and at HEAD and hashing each top-level function's source (AST
segment, sha256): `_eia930_frame`, `_eia930_frame_generic`,
`_fleet_group_by_code`, `_campd_hourly_frame`, `_benchmark_eia923_frame`,
`rebuild_benchmark`, `_parasitic_factor_map`, `_plant_class_shares`,
`_backfill_eia923_with_campd`, `_eia923_frame`, `_backfill_chp_eia923_from_donor`,
`_backfill_renewables_eia930` — **all IDENTICAL. Twelve for twelve, again.**
A full census of every changed top-level function in the file returns exactly
four: `_btm_frame`, `solve_and_persist`, `run_p2_layer`, `main` — and grep of
the latter three's diffs for bench/btm-relevant lines shows their **entire**
bench-adjacent movement is threading the new `nyiso_chp_btm_measured` flag.

**(b) `_btm_frame` — newly in scope because nyiso-149 proved the BTM channel
feeds the part** (the NYISO drift was the bench subtrahend inheriting the
registering run's flag through `btm.parquet`). It **CHANGED**
(`578ee1f7…` → `83066f44…`), and is CAISO-inert at three independent levels,
each read from the code, not the commit message (the 01db36d method):

1. **Its own gates.** The measured-share override block is reached only through
   `if iso == "NYISO":`; inside it, mutation of the *run-basis* map is
   additionally gated on `nyiso_chp_btm_measured` (default `False`). For CAISO,
   `share_bench_by_plant = dict(share_by_plant)` and is never touched, so
   `btm_bench_by_class` short-circuits to `dict(btm_by_class)` — **no second
   compute path even executes** — and the coal-cogen leg adds the same `_add`
   to both maps. The frame's new `btm_bench_twh` column therefore **duplicates
   `btm_twh` value-for-value for CAISO** (the function's own comment states
   this; the measurement confirms the gates enforce it).
2. **Its callee closure on the CAISO path, hashed across the full range.**
   `_classify_f923` IDENTICAL; `compute_must_run_emissions`
   (`results/emissions.py`) 0 commits; `chp_btm_pct` (`data/chp.py`) hash
   IDENTICAL (the file's one commit, 01db36d, only ADDS the NYISO-only sibling
   `measured_chp_btm_pct_nyiso`); `CHP_BTM_PCT_BY_SECTOR`
   (`config/constants.py:467`) block hash IDENTICAL; `coal_chp_overrides`
   (`data/coal.py`) 0 commits; `BIN_GROUP_TO_FUEL` (`fleet/eia860.py`) 0
   commits; `fleet/__init__.py` **+6/−0, purely additive re-exports** over the
   full range. `load_campd_bins`/`campd_bins_path` sit in the **ERCOT-only
   branch** — CAISO's `bins` frame is built from `group_by_code`, i.e. from
   `_fleet_group_by_code` (IDENTICAL) over `load_fleet_from_csv`
   (`fleet/eia860.py`, 0 commits).
3. **The consumer — `28ac3c2` itself, the commit that moved the fingerprint.**
   Its render change does two things, both read directly: (i) `_btm_share`'s
   measured map is now resolved by **artifact presence** (`if meta.get("iso")
   == "NYISO":`) instead of the run flag — the FLAG half of 01db36d's double
   gate is removed **by design** (that flag-dependence WAS the NYISO root
   cause), while the **ISO half — the gate that shields CAISO — is retained**,
   so `_btm_measured` stays `None` for CAISO and every `_btm_share` call takes
   its unchanged branch; (ii) three consumption points substitute
   `btm_cls_bench` for `btm_cls` (`classFull`, `_coal_grid`, `btmClass`), with
   an explicit fallback — `"btm_bench_twh" if … in _by.columns else "btm_twh"`
   — for bundles predating the column. **CAISO's committed keeper bundle
   predates the column**, so a regeneration of CAISO's parts from the committed
   bundle at HEAD consumes the identical `btm_twh` values; a hypothetical fresh
   CAISO solve would carry the duplicated column and land on the same values.
   Both maps are consumed dict-keyed by class, so the frame's new sorted row
   order is payload-inert.

**Conclusion: for CAISO the HARD flag remains STAMP-ABSENCE, not drift** — the
committed parts' `bench` payload is what the builder at HEAD would produce,
**C1's 12/12 PASS is reproducible, and no determination changes.** The
conclusion no longer rests on caiso-210's terms (those are superseded); it
rests on this section's own hashes and gate reads at `c55da9c`.

Sizing at this HEAD (`check_bench_freshness.py --warn-only`): **20 parts
checked, 17 STALE** — NYISO's three are the current ones (regenerated and
stamped `dbea7bf45111` at its own promotion) — and the *"0 with engine drift"*
line is **still vacuous for all 17** (D2 below).

**The same honest limit as caiso-210 §2.2 applies:** this is a static
reproducibility argument, not a byte-level regeneration — the container has no
scientific stack (`numpy` absent, confirmed again; the stdlib-only scorer is
why Branch A runs at all), and the keeper's `_shared/CAISO/` store and dispatch
parquets are not committed, so regeneration still requires a re-solve (Branch
B, unfunded).

### 2.3 Cross-lane item 1 DISCHARGED AS CHARTERED: nyiso-149 did **NOT** repair the checker — D1 and D2 both stand, and D1 is now **demonstrated**, not hypothetical

The charter asked this session to verify whether nyiso-149's root-cause
closure also repaired the two checker defects. Read at HEAD:

* **D1 stands.** `bench_stamp.BUILDER_SOURCES` is still exactly the four
  scripts (`render_calibration_html.py`, `render_backcast.py`,
  `backcast_artifacts.py`, `bench_stamp.py`) and
  `check_bench_freshness.ENGINE_PATHS` still
  `("src/market_sim/data/", "src/market_sim/config/")` —
  `scripts/run_calibration_full.py`, the file that computes every part's
  numbers, is **in neither tier**. And D1 is no longer a hypothetical: 28ac3c2
  changed `_btm_frame` — a function **proven bench-feeding by nyiso-149
  itself** — and the fingerprint moved only because the same sweep also touched
  `render_calibration_html.py`. **Had the `_btm_frame` change shipped alone,
  the fingerprint would not have moved.** The unwatched tier has now actually
  moved, benignly this time.
* **D2 stands.** `check_bench_freshness.py` still `continue`s immediately after
  the HARD branch (line 120), so engine drift is never computed for a stale
  part and the summary line stays vacuous for all 17.

**Both remain routed OFF this lane (rule 25)** — nyiso-148/149's mechanism, a
cross-lane or governance session's to fix. The verification the charter asked
for is recorded; the item is **retained**, not dropped.

---

## §3 — The owner packet, unchanged at **TWO** items

Carried from caiso-208 §3 / caiso-209 §4 / caiso-210 §3 / caiso-211 §3 with no
new evidence in either direction. §2 adds no third item — it is a
records-and-diagnosis re-derivation with no CAISO decision attached.

### (1) Fund a tail-formation object

| object | status | measured reach |
|---|---|---|
| **(a) PS water-state hourly intake** | declined **3×** | **62.1 % / 10.4 %** of the required 2024 / 2025 C3a move **at its most favourable bound** |
| **(b) import spot-capacity derivation** | not funded | direct λ share **< 5 %** of the positive gap |

**Neither closes C3a on its own arithmetic.** If no funding order issues,
**rest is correct**. Should one issue, Branch B's pre-registration must state
up front what a **partial** close is worth and what verdict a partial earns.

### (2) F-3 — arming posture of `caiso_ra_mpb_capacity_anchor`

Built, measured, merged, **default-OFF**, keeper-inert by construction. Arming
is an owner decision. FFR-4F's pre-registered **trap test fired**: total
thermal built is **identical to the megawatt** in both arms (10,186.3 MW), and
the only change is **the label on 1,000 MW** — FC-2 row 4 improves solely by
channel substitution.

**Recommendation, for the owner's convenience only: keep default-OFF** absent a
reason unrelated to row 4.

---

## §4 — DO-NOT-REDO

Everything in caiso-206 §B, caiso-207 §5, caiso-208 §4, caiso-209 §5,
caiso-210 §4 and caiso-211 §4 carries forward **verbatim**, with **one entry
superseded in place**:

1. **The bench-staleness adjudication now stands on caiso-212 §2 terms, not
   caiso-210's.** Do not re-derive the CAISO exposure absent **new movement**
   past `c55da9c` in the frame-builder set (the twelve + `_btm_frame` and its
   CAISO-path callees) or in `BUILDER_SOURCES`. The adjudicated state: builder
   fingerprint **`dbea7bf45111`**; three BUILDER_SOURCES commits since
   `fce890d`, all three provably CAISO-inert; twelve frame builders
   byte-identical; `_btm_frame` changed and CAISO-inert at three levels; the
   flag is **stamp-absence**. A moved fingerprint or a changed frame-builder
   hash at a future HEAD is new evidence and re-opens the cell **on its own
   terms** — exactly as this session's charter did; anything short of that is a
   frozen cell.
2. Do not regenerate CAISO's bench parts on this lane (needs a re-solve —
   Branch B only); do not read *"0 with engine drift"* as evidence for a stale
   part (D2: the checker never computes it).
3. All prior entries: the caiso-202/203/204/205 lists; the FFR-4F A/B and the
   138.36 anchor derivation; the anchor's `O` cell means *adjudicated, merged,
   arming owner-pending*, never *untested*; the swept `frontend/data/hindcast/`
   sidecars stay swept; the C3a basis is CLOSED (actual RT LMP only); the v3.4
   C1 re-score is not open (12/12, free 8/8); the retained v3.3 promotion-time
   blocks are not live; the census is **132**; **C3b's baseline is
   0.098/0.179/0.182** — not a regression, not a thing to "fix".

**New evidence still means exactly one thing: a keeper whose own scored path
spikes** — plus, for entry 1 only, measured movement in the named builder set.

---

## §5 — Filed items

All carried, none discharged (each is fixable only at a session that produces a
solve or a promotion); re-verification status noted where this session touched
one:

1. **Stale DOF-ledger text** — `offer_curve_by_group` still reads
   `"identification": "residual"` on the keeper attestation (CAISO's
   CC_REGULAR / CT_PEAKER bands measured from OASIS `PUB_DAM_GRP` since
   2026-08-02, caiso-202 §H). **Re-verified still open by direct read of the
   attestation's 10 entries this session** (so are the sibling
   `offer_curve_committed_below_floor[CAISO]` and `offer_curve_smoothing`
   rows).
2. **Diagnostics vintage drift** — keeper-vintage
   `legitimacy_diagnostics.json` differs from fresh bundles on one D-4 row
   (chp_steam plant 10034). Carried.
3. **Site retention** — the caiso-205 pair postdates the keeper and comes off
   at the next promotion in the ordinary way.
4. **Promotion-session duty** — re-measure and re-state the whole scorecard
   from the verdict output; never carry rows from a superseded run.
5. **CAISO's bench parts are unstamped** — still tripping the HARD flag on
   every scorer run, **now against fingerprint `dbea7bf45111`** (the banner's
   fingerprint moved with 28ac3c2; the parts still carry none). Re-confirmed
   NOT a correctness defect at this HEAD (§2.2). **Discharge as a by-product of
   the next funded CAISO solve**; verify afterwards with
   `check_bench_freshness.py --iso CAISO` AND re-run the keeper verdict, since
   regeneration CAN move C1's actuals (the NYISO ~4 TWh precedent). Note for
   that session: the regenerated parts will consume the committed bundle's
   pre-column `btm.parquet` via the `btm_twh` fallback — value-identical by
   §2.2(b)3 — and a full re-solve would emit the new `btm_bench_twh` column,
   equal for CAISO by construction.
6. **Session mechanics** — regenerate `data/clean` before any solve; **ONE**
   CAISO 3-year invocation at a time (~13.3 GiB cgroup cap); no scientific
   stack in this container class (`numpy` absent, confirmed) — install before
   any solve or benchmark rebuild.

**Routed OFF this lane (rule 25):**

7. **The two bench-freshness checker defects D1/D2** — **verified NOT repaired
   by nyiso-149 this session (§2.3)**, and D1 upgraded from hypothetical to
   demonstrated. Still nyiso-148/149's mechanism; still a cross-lane or
   governance fix.
8. **The five-ISO bench regeneration + CI-gate sequence** — program-level;
   NYISO's leg done again at its nyiso-149 promotion (its three parts carry the
   current stamp); CAISO's leg is filed item 5, funding-blocked.
9. **Program-wide stale registration citations** — `cccc911` (2026-08-19)
   swept all 187 canonical `frontend/data/hindcast/` sidecars; citations of
   registered forecast-run ids, including the **shared** `mechanism-matrix.js`
   base-row text for `caiso_ra_mpb_capacity_anchor`, point at runs no longer on
   the forecast dashboard. Fixing only CAISO's would make the shared file
   inconsistent. Route to a cross-lane or governance session.

---

## §6 — Governance

* **Rule 1 `[R-STRUCT]`.** Nothing tuned to a residual; no mechanism added,
  armed or removed. §3(2) again declines to recommend arming for a channel-
  substitution improvement.
* **Rule 12 `[R-PARALLEL]` / mechanics.** No solve run; neither the year loop
  nor the memory cap engaged.
* **Rule 13 `[R-MEASURED]`.** No measured outcome fed back; §0 records why
  reaching C3a through a §F-killed lever would be a rule-13 act.
* **Rule 15 `[R-DASHBOARD]`.** **No run was produced, so no registration is
  due.** The caiso-134/140/150/202/206…211 disposition applies unchanged.
* **Rule 16 `[R-ALLYEARS]`.** All three CAISO registrations carry
  `[2023, 2024, 2025]`; no single-year bundle exists on the lane.
* **Rule 22 `[R-HOLDOUT]`.** No year solved, scored or registered. CAISO
  absent from both `complete` and `final` (it sits in `withdrawn`, entry
  byte-equal across the delta); freeze **ACTIVE**. The NYISO re-key is that
  lane's D-5(b) duty discharged at its own promotion — foreign and verified
  structurally lossless here.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The shared `mechanism-matrix.js`
  was not touched; the checker defects are *verified and reported*, not
  repaired; the two foreign `·` cells were *measured*, never edited; no other
  ISO's record was modified.
* **Rule 27 `[R-PUSH]`.** Fable. **No source file under `src/market_sim/` was
  modified** — the deliverable is records only. Every edited file was edited in
  place, never regenerated from response content.
* **Rule 28 `[R-MECH-MATRIX]`.** **No mechanism was tested, so duty (b) does
  not attach and no cell verdict moves.** The §5.2 prose block records the
  session; the shard `gates` stamp is refreshed as a records-truthfulness act
  (its bench-staleness facts were superseded — the caiso-208/209/210
  precedent), not a verdict change. The census is **unchanged at 132**.

---

## §7 — Record changes

- **This file**; `docs/calibration-log/caiso.md` caiso-212 entry; matrix §5.2
  caiso-212 block; CAISO shard `gates` stamp refreshed with the §2
  re-derivation.
- **Keeper, markers, holdout freeze, DOF ledger, every matrix cell verdict, the
  §5.2 header, every bench part, and every source file: UNCHANGED.** No run
  registered (none produced). No cell edited by this lane. Nothing regenerated.

Next number: **caiso-213**.

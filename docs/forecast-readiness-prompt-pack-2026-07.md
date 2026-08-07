# Forecast-readiness remediation — prompt pack (FFR waves)

**Execution vehicle for `docs/forecast-readiness-audit-2026-07.md` §4** (findings FR-1..FR-27).
Produced 2026-07-30 against `origin/main` HEAD `fd60eef`. **REFRESHED 2026-07-31 against HEAD
`7b8c36a`** — §0a records everything that moved in between (all six keepers, the two-block
marker restructure, the active holdout freeze, determinations); code-side, **zero FFR items
were executed between the two dates** (re-verified at file:line 2026-07-31), so every prompt's
technical content stands. **§0b (2026-08-02) supersedes that last clause: Wave 1 is now MERGED
7/7, and §W1-X — the Wave-1 close checklist — is the live gate on Wave 2 and FH-4/FH-5. Read
§0b before dispatching anything. §0c (2026-08-02) then DISCHARGES that gate: §W1-X is closed,
the single cache epoch is taken, and Wave 2 + FH-4/FH-5 are released — so read §0b for the
state Wave 1 left and §0c for what the close changed, §0c winning wherever they differ.** The
refresh also folds in the commercial-practice peer review
(`docs/forecast-readiness-peer-review-2026-07.md`): one added session (FFR-2E, the FR-14
coverage hole), FFR-PA promoted to dispatch-with-Wave-1 (2026-08-22 deadline), and the standing
disclosure list (peer review §4) that every forecast deliverable now carries. This pack extends
the FF program (`docs/forecast-development-plan-2026-07.md`) with remediation waves; it does
**not** supersede that plan — its §7 standing constraints bind every session below, and the FF
wave manager may adopt these rows into its ledger as `FFR-*`. FF Wave 4 (golden solves) remains
WITHDRAWN; this pack schedules **nothing** beyond T0/T1 windows.

**Solve-window cap (owner standing instruction 2026-07-31 + plan §2.1b):** every test/probe
forecast invocation in this pack is limited to **~3–5 solve-years** — enough to exercise and
debug mechanisms, never a full horizon. No invocation may exceed 5 solve-years; full-horizon
(25-year) runs happen only under a separate, explicit, session-logged owner authorization per
§2.1b(d). Do not burn compute proving what a 5-year window already proves.

**House conventions (as FF §6):** waves are sequential; prompts within a wave are independent
parallel sessions unless flagged; `[FABLE]` = hard structural/adjudication work, `[OPUS]` =
spec'd execution, solve campaigns, intake, plumbing (never Sonnet — rule 27); `⛔` = gate.

**Every prompt implicitly begins:**
*Read CLAUDE.md, `docs/forecast-readiness-audit-2026-07.md` (your FR items + §4 row), and
`docs/forecast-development-plan-2026-07.md` §7 (binds). Fresh branch off latest `origin/main`;
`git config user.email noreply@anthropic.com && git config user.name Claude`.*

**Every prompt implicitly ends:**
*Push via `mcp__github__push_files` (server-side; session clones are history-grafted and raw
`git push` of a rebased branch 413s) or a verified small-pack `git push`; blob-verify any pushed
file ≥300 lines (fetch back, compare). Register every run on the forecast-validation namespace
in the producing session (`scripts/register_forecast_run.py`; NEVER the backcast registry).
Update the mechanism-matrix cell for any mechanism you test, rejections included (rule 28).
Findings doc to `docs/handoffs/ffr-<id>-<topic>-<date>.md`. No tuning: a residual closable only
by an unidentified value is an open blocker, written up (rules 1/13/14/21). Any invocation that
solves forecast years stays ≤5 solve-years (§2.1b + owner instruction 2026-07-31); any
forecast-facing deliverable carries the standing disclosure list
(`docs/forecast-readiness-peer-review-2026-07.md` §4).*

---

## 0a. State delta — 2026-07-31 refresh (read before dispatching anything)

Everything below changed between the audit/pack production (2026-07-30, HEAD `fd60eef`) and this
refresh (2026-07-31, HEAD `7b8c36a`). ~200 commits of backcast-calibration work merged; **no FFR
session ran** (no `docs/handoffs/ffr-*` exists; every FR code finding re-verified open).

**1. Keepers — all six moved.** Sessions must use the sharded store
`frontend/data/backcast/keepers/<ISO>.json` at their own HEAD, never ids quoted in a doc:

| ISO | At pack production | At this refresh (2026-07-31) |
|---|---|---|
| ERCOT | ercot140 | `2026-07-31-ercot145-gas-daily-shape` |
| CAISO | caiso139 | `2026-07-31-caiso148-nuclear-availability` |
| PJM | pjm-137 | `2026-07-31-pjm-143b-hy-level` |
| MISO | miso-101b | `2026-07-31-miso-109b-hy-level` |
| NYISO | nyiso-100 | `2026-07-31-nyiso105-chp-heat-rates` |
| NEISO | neiso-61 | `2026-07-31-neiso-71-nucavail` |

**2. Markers — the two-block restructure landed, and part of owner decision D-5 is EXECUTED.**
`calibration-complete.json` now has two independent blocks (owner decision 2026-07-31):
`complete` = validation tier (2022 + backward ladder, iterable) and `final` = locked-test tier
(2019/H1-2026, touch-once) — **deliberately empty** ("Neither is final"). `complete` now holds
**{NEISO, NYISO, PJM}**: PJM declared 2026-07-31 (CALIBRATED, zero caveats, at pjm-140), NYISO
re-declared 2026-07-31 (CALIBRATED-WITH-CAVEATS, C3c ledgered, at nyiso-100 — the old withdrawal
is marked superseded), NEISO re-scoped validation-only (its locked test has **NEVER BEEN
GRANTED** — *corrected 2026-08-06, D-23; this read "its locked test is SPENT, never
re-grantable", which was false: no NEISO 2019/H1-2026 year has ever been solved, scored or
registered. NEISO stays validation-only either way and the correction grants nothing*).
Consequences for this pack: the FFR-2D D-5 briefs are rewritten (see the prompt);
gate (a) of §2.1b is now arguably met by THREE ISOs, not one — but §2.1b(a)'s text predates the
two-block split and still cites the superseded NYISO withdrawal, so the reconciliation of
"gate (a) keys on `complete`" is itself a D-5 residue item. All three markers record the
keeper-at-declaration (pjm-140 / nyiso-100 / neiso-54-lineage), which now lags the dashboard
keepers — the marker format freezes the keeper for the one-shot score, so treat
"re-key vs by-design snapshot" as an owner question (in 2D), not a defect. One live doc
inconsistency to carry, not resolve: PJM's marker text says the CI marker gate is tier-agnostic
while CLAUDE.md rule 22 (amended 2026-07-31) says enforcement is tier-aware.

**3. HOLDOUT SPEND FREEZE is ACTIVE** (`frontend/data/backcast/holdout-freeze.json`, declared
2026-07-25, HELD 2026-07-26; cause: the CAMPD economic-layup outage over-count). While active,
NO out-of-training year (anything outside 2023–2025) may be solved/scored/registered for ANY
ISO, marker or not. **It does NOT touch this pack's work**: forecast-mode 2026+ solves, T1-F/
T1-X/T1-H windows as specified (T1-X scoring stops at 2025), and in-sample 2023–2025 work are
all outside its scope, and data intake stays open under session-logged owner authorization.
State this in-session rather than self-blocking; equally, never read a marker as spendable —
each carries a `freeze_interaction` clause saying it grants nothing while the freeze stands.

**4. Determinations moved.** PJM **CALIBRATED** (re-verified 9/9 in both pjm-143 A/B arms);
NEISO / NYISO / CAISO **CALIBRATED-WITH-CAVEATS** (ledgered C3c-family caveats); ERCOT NOT-YET
{C3a,C3b,C3c,C7} (C6 now ATTESTED and passing); MISO NOT-YET (sole blocker C7 COAL_PRB shape).
Four of six ISOs now hold a calibrated-grade backcast — the Phase-4 gate-open order (PJM →
NEISO → …) strengthens.

**5. `program-status.json` is internally inconsistent** — still the 2026-07-20 board except one
hand-edited NYISO gate-(a) row (2026-07-31). Its PJM/NEISO rows are now factually wrong (PJM
holds a marker; NEISO is not "the ONLY ISO meeting gate (a)"). Unchanged instruction: **do not
hand-edit it further** — FFR-3A regenerates it from re-scored evidence; until then, this §0a is
the drift record.

**6. Cache-epoch debt grew.** `scenarios.py` gained fields twice since the audit (ercot148,
miso-111) with no epoch bump; any 2026+ bundle cached since 2026-07-29 predates both the
pending FR fixes AND this config drift. §W1-X's single bump now also invalidates those.

**7. Forward hydro climatology fixed** (miso-110 `forecast_monthly_hydro` mode B→BF; MISO
forward level 10.244→9.312 TWh, PJM 15.875→9.254 TWh) — the one forecast-lane code change since
the audit. FFR-1C's accreditation work is orthogonal (capacity credit, not energy budget); cite,
don't re-diagnose. Also landed: the NYISO D-5 downstate parity wiring (2026-07-30) that FR-22
generalizes from, and `nyiso_central_east_measured_ttc` adjudicated K-backcast/**G-forecast**
(measured TTC explicitly refused a forward channel — transmission-expansion registry owns
forward TTC).

---

## 0b. State delta — 2026-08-02 (Wave 1 is MERGED; §W1-X is the live gate)

Everything below changed between the 2026-07-31 refresh (HEAD `7b8c36a`) and this entry
(HEAD `a92ae97`). §0a's items 1–7 stand except where superseded here.

**1. WAVE 1 IS FULLY MERGED — 7/7.** The "zero FFR items executed" statement in §0a and the
pack header is SUPERSEDED. All seven lanes are on `main` with findings docs committed:

| Lane | PR | Merged | Findings doc (`docs/handoffs/`) |
|---|---|---|---|
| FFR-1A (FR-1/2/13/23) | #3248 | 2026-08-01 | `ffr-1a-confirmed-exit-accounting-2026-07-31.md` |
| FFR-1B (FR-7/8/12) | #3239 | 2026-08-01 | `ffr-1b-solve-year-availability-2026-08-01.md` |
| FFR-1C (FR-3) | #3243 | 2026-08-01 | `ffr-1c-hydro-accreditation-2026-07-31.md` |
| FFR-1D (FR-10/11/15/24/25/26) | #3245 | **2026-08-02** | `ffr-1d-enforcement-wave-2026-07-31.md` |
| FFR-1E (FR-22) | #3246 | 2026-08-01 | `ffr-1e-forecast-parity-check-2026-07-31.md` |
| FFR-PA (FR-18, time-sensitive half) | #3247 | 2026-08-01 | `ffr-pa-confirmed-retirements-refresh-2026-07-31.md` |
| FFR-PB (FR-20 M1/M2) | #3244 | 2026-08-01 | `ffr-pb-atb-statute-intake-2026-07-31.md` |

Acceptance highlights, for sessions citing rather than re-deriving: 1A arm-1 is dispatch-inert
on both probe ISOs (NEISO+PJM T1-F 2026–30 value-identical, objective equal to the last
decimal) and closes I4 on both; 1B proved backcast byte-identity across **all six** keeper
configs (102/102 input-surface hashes); 1C closed NYISO's I7 gap 98 % (−1,799 → −36 MW), CAISO
41 %, MISO 20 % with the residuals FILED not closed; 1E resolved **474 armed mechanisms** and
filed **8 with no forecast-side consumer** (armed in five of six keepers) — filed, not fixed.
**No keeper moved and no stop-the-line fired in Wave 1.**

**2. §W1-X — ~~THE LIVE GATE, not yet run~~ → DISCHARGED 2026-08-02, see §0c.**
*(This item is kept as written because it is the brief §W1-X was dispatched against; §0c
reports what each of its points came to. Both flagged extras were closed: the parity job is
in `ci.yml`, and 1D's attestation was re-confirmed against the merged tree.)* No
`docs/handoffs/ffr-w1x-*` exists; the cache-epoch bump (§0a item 6, now also covering the
FR-1/2/7/8 output change under unchanged keys) is UNTAKEN. Wave 2 and FH-4/FH-5 stay shut
until it reports green. Two items beyond the checklist's four now belong to it:
- **FFR-1E's `ci.yml` parity job is still unwired.** 1D owned `ci.yml` in Wave 1 and added only
  the forecast-INVARIANTS job (FR-24, `ci.yml:99`). `scripts/check_forecast_parity.py` and
  `scripts/lib/forecast_parity_registry.py` are on `main` and pass, but nothing in CI runs
  them. The job to add is carried verbatim in the 1E findings doc §6 (`forecast-parity-guard`,
  stdlib-only), plus its path-filter extension.
- **1D's attestation describes a PRE-REBASE tree.** PR #3245 was rebased from base `255c015`
  onto `6e98263` before merging (30 files/+2,136 → 34 files/+2,234), and its `scenarios.py`
  hunk had to be reconciled against FFR-1B's `__post_init__` commit (`ba49be2`), which merged
  first. §W1-X re-confirms it against the merged content.

**3. Keepers moved again — ERCOT twice since §0a.** Read the shards at your own HEAD; these are
recorded only to show the rate of drift:

| ISO | §0a (2026-07-31) | Now (2026-08-02) |
|---|---|---|
| ERCOT | ercot145-gas-daily-shape | `2026-08-01-ercot149-gas-event-cap` (via ercot148, PR #3260) |
| CAISO | caiso148-nuclear-availability | `2026-07-31-caiso-151-firm-selfsched` |
| NYISO | nyiso105-chp-heat-rates | `2026-08-01-nyiso109-zonal-margin-anchor` |
| NEISO | neiso-71-nucavail | `2026-07-31-neiso-72-hy-window` |
| PJM | pjm-143b-hy-level | unchanged |
| MISO | miso-109b-hy-level | unchanged |

**4. Markers and the freeze are UNCHANGED** from §0a: `complete` = {NEISO, NYISO, PJM},
`final` = empty, holdout freeze **ACTIVE** (last action 2026-07-26 *held*). Nothing in Wave 1
touched an out-of-training year.

**5. Wave FH has not launched** — no `docs/handoffs/fh-*` exists. FH-1/FH-2/FH-3 are ungated
(parallel with Wave 2); ~~FH-4/FH-5 remain gated on §W1-X's epoch bump~~ → **FH-4/FH-5 are
UNBLOCKED as of 2026-08-02** (§0c-3 for the epoch's scope, §0c-9 for dispatch). They must
solve **cold** — the epoch invalidates exactly the caches they would re-use.

**6. Dispatch state at this entry** *(superseded by §0c-9 — §W1-X has since closed and
FFR-2D has merged; the release ORDER below still stands)*. Launchable immediately:
~~**§W1-X close**~~, **FH-1**, and ~~**FFR-2D**~~ (docs-only, reads no cache, so not
gated). Staged behind the §W1-X green-light: FFR-2A / 2B / 2C / 2E — recommended release
2C+2A first (2C is nearly no-LP), then 2B, then 2E; 2A and 2B must coordinate their PJM
windows explicitly (rule 12: ≤2 concurrent solve invocations, PJM and MISO legs never
co-run).

---

## 0c. §W1-X close report — 2026-08-02, WAVE 1 IS CLOSED

**This is the discharge of the §0b-2 gate.** §0b records the merged Wave-1 state as the
§W1-X session found it; §0c reports what that session did and what every downstream wave
must now carry. Where the two disagree, §0c wins. Full record:
`docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`.

**1. All seven Wave-1 lanes are MERGED** — merge shas, for the per-merge audits below:
FFR-1A `1eeef40` (#3248) · 1B `255c015` (#3239) · 1C `50c5193` (#3243) · 1D `24665ee`
(#3245) · 1E `f5c462b` (#3246) · PA `5118288` (#3247) · PB `64905b4` (#3244). (§0b-1 has
the lane/finding/doc table.)

**2. §W1-X is DISCHARGED — all four items.** (a) The 1A-arm-1 / 1B / 1D keeper
byte-identity attestations are present and re-confirmed against the *merged* tree and the
*current* keeper set; **no keeper moved** (all six cache keys byte-identical across each of
the three `scenarios.py`-touching merges, verified in one path context per comparison). 1D's
post-rebase `scenarios.py` reconciles cleanly with 1B's earlier-merged `__post_init__`
commit: every guard and coercion in the merged file is attested by exactly one findings doc.
(b) **THE SINGLE CACHE EPOCH IS TAKEN — 2026-08-02**, for FR-1/FR-2/FR-7/FR-8. (c) The
three-limb regression audit passes: no band widened, **zero** `ScenarioConfig` fields
added/removed/re-defaulted across the entire wave (668 either side of all seven merges), no
out-of-training year solved, scored or registered — every Wave-1 registration is
forecast-mode 2026+ on `frontend/data/hindcast/`, ≤5 solve-years. (d) FFR-1E's held
`forecast-parity-guard` job is in `ci.yml`.

**3. The cache epoch — scope, because every downstream solve depends on it.** The epoch is a
dated ledger entry in `src/market_sim/results/cache.py`'s docstring (there is deliberately
no `CACHE_EPOCH` token — see the close doc §2.1 for why, and for the two-surface split
between key *advances* and same-key *invalidations*). It invalidates **every cached bundle
produced in forecast mode** (`mode="forecast"`, including `hindcast=True` and T1-X crossover
legs) before the Wave-1 merges — **any solve year, not only 2026+**, because FR-8 reaches a
crossover's realized 2023–2025 legs. It does **not** invalidate backcast caches or any
keeper bundle. It subsumes the §0a-6 debt. **Run the purge in the ledger on any checkout
predating 2026-08-02 before your first solve; solve cold.**

**4. The stale `PINNED_DEFAULT_CACHE_KEY` is REPAIRED at its root**, closing the item 1B §6
and 1D §8.2 both handed here. Cause: `coal_prb_committed_dispatchable` (#3207, miso-111) and
`coal_prb_committed_split` (#3232, miso-112) shipped default-off but unregistered in
`_CACHE_KEY_OPTIONAL_FIELDS`, moving the default key twice. Registered, not re-pinned; the
key is back at `603c2498bf71d21d` and four pinned-literal tests across two BLOCKING CI jobs
are green. `check_cache_key_registration.py` only fires its new-field check with `--base` —
i.e. on the PR that adds the field — so **a lane adding a `ScenarioConfig` field must not
rely on a later session noticing**.

**5. One rule-13 hole closed, three judgement calls filed.**
`ercot_dam_availability_gas_event_cap` (ERCOT-149, landed after 1D wrote the family) is now
in `_BACKCAST_ONLY_OVERLAY_FIELDS` beside its coal sibling. `caiso_firm_import_selfsched_clip`,
`coal_prb_committed_split` and the `gas_offer_margin_*` anchors are filed for their own lanes
(close doc §5.2). **The FR-11 family has no CI guard of its own** — a standing hazard for
every parallel lane that adds a measured overlay; a checker is proposed to L-INP.

**6. Two tests are RED on `origin/main`, neither from Wave 1** (close doc §5.4):
`test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` (the fixture
still encodes `complete = {NEISO, NYISO}`; PJM declared 2026-07-31 — governance lane) and
`test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty` (data
lane). Both in the fast tier. Do not attribute them to Wave 1.

**7. Unchanged from §0a/§0b:** the keeper set (ERCOT `2026-08-01-ercot149-gas-event-cap` · PJM
`2026-07-31-pjm-143b-hy-level` · CAISO `2026-07-31-caiso-151-firm-selfsched` · NYISO
`2026-08-01-nyiso109-zonal-margin-anchor` · NEISO `2026-07-31-neiso-72-hy-window` · MISO
`2026-07-31-miso-109b-hy-level` — still read them at your own HEAD), the two-block marker
restructure (`complete` = {NEISO, NYISO, PJM}, `final` EMPTY), the **active holdout freeze**,
and `program-status.json`'s internal inconsistency (still FFR-3A's to regenerate).

**8. One dated deadline to carry into a wave plan:** `tests/golden/staleness_waiver.json`
hard-fails `test_golden_fixture_config_identity_is_current` on **2026-10-31**; resolving it
is owner decision D-7 (a 15-solve-year reseed).

**9. Dispatch state after the close** (supersedes §0b-6). **Wave 2 is RELEASED** —
FFR-2A / 2B / 2C / 2E may dispatch on §0b-6's recommended order (2C+2A, then 2B, then 2E;
2A and 2B coordinate their PJM windows explicitly, rule 12). ~~**FH-4/FH-5 are UNBLOCKED**
alongside FH-1/2/3.~~ → **CORRECTED by §0d: the §W1-X condition is discharged, but FH-1's
§3.3 harness-defect gate FAILED after this section was written — FH-4 is BLOCKED.** FFR-2D has merged (#3262, the D-1..D-7 owner-sitting packet), so the
owner sitting is the next coordination event, not a Wave-2 prerequisite. Two duties the
epoch imposes on Wave 2, stated once here so no lane re-derives them: **FFR-2A's T1-X legs
are exactly what the epoch invalidates** (FR-8 reaches their realized years — purge and
solve cold), and **FFR-2B may reuse a committed BEFORE leg only if FR-1/2/7/8 provably do
not touch it** — a forecast leg with capacity evolution, or any aging-sensitive
availability, is not such a leg.

---

## 0d. FH-1 landed and its acceptance gate FAILED — FH-4 stays blocked (2026-08-02)

**Read this before dispatching FH-4 or FH-5.** §0c was written by the §W1-X session, which
merged at 04:55; FH-1 merged at 05:11 (PR #3269). §0c's "FH-4/FH-5 are UNBLOCKED" is therefore
true only of the condition §W1-X owned. FH-4's `REQUIRES` line names **two** conditions, and
the second has since failed.

**1. The instrument shipped.** `--forward-from-base` (T1-FF) is on `main` with both arms wired,
the four sub-2026 leaks closed (planned additions, emission-rate window, hydro climatology, the
silent gas back-hold), the rule-22 carve-outs moved into `scripts/lib/holdout_policy.py` with
the harness fail-closed against the freeze file, the scorer's symmetric `< 2023` refusal, 28
contract tests and the rule-28c matrix row. Findings doc:
`docs/handoffs/fh-1-full-forward-harness-2026-08.md`. Arm K at base 2023 **hard-errors** by
design until FH-3 lands `hindcast_asknown_aeo2023` — it refuses to substitute a different
vintage, which would be the §4-row-7 trap in another costume.

**2. The §3.3 harness-defect gate REPRODUCED — stop-the-line for Phase A.** Probe: ERCOT, base
2023, vintage 2023, 2023–2025, Arm R, 3 solve-years, registered on the hindcast namespace
(`ercot-2023-2025-t1ff-armr-fh1gate`, `kind="full_forward"`).

| Year | Prior thermal | Econ retired | I6 |
|---|---|---|---|
| 2023 | 78.2 GW | 0.00 GW | 0.0 % |
| 2024 | 78.2 GW | 0.00 GW | 0.0 % |
| 2025 | 78.5 GW | **21.05 GW** | **26.8 % — FAIL** (cap 20 %) |

The full FC-1 signature reproduces, not just I6: **I6 FAIL / I7 FAIL / I12 WARN** — the same
triple `ff-t1-gate-2026-07.md` §4.2 adjudicated on the vintage-2023 T1-X crossover (25.6 %).
The run itself is mechanically clean (zero leakage-guard violations, both Arm R weather rebinds
fired, hydro pinned to base, gas on `hindcast_realized`, freeze legality printed) — **the defect
is the retirement layer, upstream of T1-FF**, exactly as the T1-X adjudication said. It follows
the harness posture, not the input stack. Nothing was tuned in response (rule 1 / rule 14).

**3. Consequences, binding on any session that touches Wave FH:**
- **FH-4 does not start.** Its own `REQUIRES` demands this gate PASSED. The block lifts only
  when a retirement-lane fix lands **and** a re-probe passes — not by re-reading the evidence.
- **The probe's skill numbers are GATE CONTEXT ONLY** (price gaps 2.1/54.0/2.3, fuel-mix gaps
  9.8/13.6/28.1 vs keeper `ercot149`). They must never be quoted as T1-FF skill: 2024's price
  is dominated by the pre-wave tight fleet and 2025's mix by the post-wave gutted one.
- **The fix belongs to the already-chartered retirement lanes** (FF-1A R-NEW pipeline / the G-31
  screen-grain root cause / the FFR retirement-calibration lane) — **not** to a new FH session
  and not to a parameter. This is why **FFR-2B is now the highest-value Wave-2 session**: it
  owns the retirement-rule evidence (D-1/D-2) for the very layer blocking FH-4, so its output
  feeds both the owner sitting and the FH unblock. Recommended Wave-2 release order is amended
  to **2B + 2C first**, then 2A, then 2E (2A and 2B still coordinate PJM windows, rule 12).
- **FH-2 and FH-3 are unaffected** and may dispatch in parallel with Wave 2. FH-3 additionally
  unblocks Arm K at base 2023.

**4. Keeper drift since §0c:** CAISO → `2026-07-31-caiso153-reid-b` (PR #3267). Read the shards
at your own HEAD.

---

## 0e. State delta — 2026-08-03: the T1-F half is COMPLETE, the instruments are REPAIRED, G-31 is CHARTERED, and rule-12 concurrency is per-PROMPT

**Read this before dispatching anything.** It corrects two things earlier records got wrong and
records two owner decisions. HEAD at writing: **`01b6a6a`**, zero open PRs. Re-verify at your own
HEAD — this program's state has moved ~200 commits inside a single manager session.

**1. Correction: the FFR-3A T1-F half is COMPLETE for ALL SIX ISOs.** Manager notes carried
forward a "PJM and MISO were still solving at write-up" claim. The committed record disagrees:
`docs/handoffs/ffr-t1-regate-2026-08-02.md` §6.5 tables NEISO, NYISO, PJM, MISO, ERCOT and CAISO
all at **5/5 solve-years**, plus the ERCOT pre-decision control. PJM and MISO landed before the
doc was committed. **All six determinations are HOLD; nothing is promoted; nothing is
registered.** FFR-3C has since added the **MISO control arm** that §6.5b named as the single
highest-value next measurement, so that item is closed too.

**2. Correction: FFR-3D REPAIRED four of FFR-3A's blockers — it was not triage-only.**
`docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md`: blocker 5 (dishonest zero-year console
line), **blocker 7** (`run_full_horizon` never wrote `run_config.json`, so **FC-7 failed on every
T1-F leg by construction**) and **blocker 8** (FC-2 row 4 SKIPPED everywhere; BLK-10 now scorable)
are all fixed at `34c2f25`; blocker 4 (optional-field cache-key hazard) is repaired structurally
at `0233913`. Only **blocker 6** (24 pre-existing test failures on main) is triage-without-fix.
Plus the three signed instrument decisions: **C.4(c) un-pin** (`36ef1a1`), **C.4(a) single posture
reader** (`83efe6c`, NYISO now resolves curve-OFF), **D-3a `reindex_gross`** (`e6f0cdb` — its
byte-identity claim was **FALSE as shipped**, was repaired, then confirmed exactly; read FFR-3D §4
before quoting it).

*Consequence for the battery's remaining half:* the four T1-H curve legs must **RE-SOLVE, not
re-score** — `36ef1a1` moves their solved config from harness-local `False` to the shipped `True`
on `correlated_forced_outage` and `entry_lookahead_reprice`. The FFR-3A confound (regate §6.2) is
therefore gone, and the T1-H legs are measured on the shipped posture for the first time.

**3. Owner decision D-8 (sitting Addendum F.1) — queue latency and queue throughput are TWO
mechanisms; the G-31 fix lane is CHARTERED.** Bounds: the cheap **G3 cap-grain** fix lands first
(thread the execution year into the pipeline admission cap; no new parameter); any throughput term
is **externally identified from the EIA-860 retired sheet**, never fitted to a residual; test set
is **ERCOT + PJM only** (MISO retires nothing economically in a T1-F window and cannot exercise the
mechanism — FFR-3C §3.2); LOYO within 2023–2025 and a **paired control** before promotion. This
does **not** lift the FH-4/FH-5 block, promote anything, or unarm D-1/D-2 — Addendum D's HOLD
PROMOTION, FIND ROOT CAUSE stands and both mechanisms **stay armed**.

**4. Owner decision (sitting Addendum F.2) — rule 12's concurrency cap is PER PROMPT, not per
program.** Owner, verbatim: *"These run in separate sessions so there's no limit to solve slots as
long as there's only 2 per PROMPT."* Each dispatched session may run ~2 concurrent solve
invocations; independent sessions do not contend, because they do not share a container.
Unchanged, because they are per-container limits: years **sequential within an invocation**,
**≤2 concurrent invocations within one session**, **PJM and MISO never co-run within a session**
(~8.6 GB each), **≤5 solve-years per invocation**. *Dispatch consequence:* lanes queued **solely**
for slot contention — **FFR-SC** and the **FFR-SA close-out** — dispatch concurrently with the
battery, not behind it. A lane is now held only for evidence dependency or an owner decision.

**5. Standing, unchanged.** HOLDOUT FREEZE **ACTIVE** (all ISOs, both tiers) — it blocks
out-of-training **backcast** years and does **not** block forecast-mode 2026+, T1-F/T1-X/T1-H/T1-FF
work, or in-sample 2023–2025. `complete` = {NEISO, NYISO, PJM}; `final` = **EMPTY**, deliberately;
NEISO's locked test has **NEVER BEEN GRANTED** (*corrected 2026-08-06, D-23 — previously
"is SPENT and never re-grantable"; `final` stays EMPTY either way*). **CACHE EPOCH 2026-08-02** — every pre-epoch
forecast cache is invalid, so forecast work solves COLD by design. **FH-4/FH-5 stay BLOCKED**: the
block lifts only when a retirement-lane fix **lands** and FH-1's §3.3 gate **re-probes green**.
`data/clean` is a hard prerequisite for every forecast leg (≈65 min / 50 datatypes / 1.6 GB) and
needs `pip install tzdata` or `ercot-wtx-congestion` fails with `ZoneInfoNotFoundError`.

**6. Keeper drift since §0d.** All six moved. Read the shards at your own HEAD
(`frontend/data/backcast/keepers/<ISO>.json`); at `01b6a6a` they are ERCOT
`2026-08-02-ercot150b-zonal-anchor` · PJM `2026-08-03-pjm-147b-chp-heat` (CALIBRATED 9/9) · CAISO
`2026-08-03-caiso156-meter-screen-b` · NYISO `2026-08-03-nyiso-117-nyc-rcpf` · NEISO
`2026-08-03-neiso-caiso156-meter-screen` · MISO `2026-08-03-miso-117b-ct-heat`.

---

## 0. Wave map (dispatch at a glance)

| Wave | Sessions (model) | Parallel? | Solves? | Gate to next wave |
|---|---|---|---|---|
| **W1 fix** ✅ **CLOSED 2026-08-02** | 1A (F), 1B (F), 1C (O), 1D (O), 1E (O) **+ PA (O, promoted from WP — 2026-08-22 deadline)** | yes — file-disjoint; 1D's `ci.yml` hunk precedes 1C's (flag §W1) | T0 probes + ≤2-ISO T1-F acceptance probes only | **MET.** All seven lanes merged; **§W1-X discharged 2026-08-02** — attestations confirmed (no keeper moved), **cache epoch bumped ONCE** (FR-1/2/7/8; invalidates every pre-Wave-1 **forecast-mode** cache at ANY solve year, backcast/keepers untouched), regression audit 3/3 PASS, FFR-1E's parity job in CI. Record: `docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`; scope + purge: §0c-3 |
| **W2 evidence** | 2A (O), 2B (O), 2C (O), 2D (F), 2E (O) | yes — ≤2 concurrent solve invocations (rule 12) | T1-X ×3, T1-H probe legs, T0/T1 probes, capacity-hindcast re-runs (no-LP-heavy) | evidence docs committed → **OWNER SITTING** |
| **⛔ OWNER** | decision batch D-1..D-7 (audit §4 Phase 2) | one sitting | none | signed decisions |
| **W3 re-baseline** | 3A (O), 3B (O) | 3B first or parallel (3B lands schema, 3A populates) | the ONE consolidated battery: T1-F ×6 + T1-X folds + T1-H re-scores + FC-6 | boards regenerated & current |
| **WS structural** | SA (F), SB (F), SC (O) | yes | T0 smoke only; everything ships **default-off/no-solve** so the W3 baseline stays valid | owner arming decisions (later) |
| **WP intake** | PA (O), PB (O) | parallel-**anytime** (data/docs only, no solve) | none | — |
| **WFH hindcast** | FH-1 (F) ✅ merged, FH-2 (O), FH-3 (O), then FH-4/FH-5 (O) ⛔ **STILL BLOCKED — see §0d** | FH-2/FH-3 yes — parallel with W2. FH-4/5 had TWO conditions: (i) W1 merge + §W1-X epoch bump — **MET 2026-08-02**; (ii) **FH-1's §3.3 harness-defect gate PASSED — FAILED 2026-08-02, the I6 over-retirement REPRODUCES at the T1-FF posture (26.8 % vs the 25.6 % T1-X reference).** FH-4 does **not** dispatch until a retirement-lane fix lands and a re-probe passes. When it does: solve **COLD** — the epoch invalidates every pre-2026-08-02 forecast-mode cache, exactly what these legs would have re-used (§0c-3 purge) | FH-4: 3 solve-yr × 6 ISOs × 2 arms; FH-5: 4 solve-yr | forward-mode skill measured → feeds §2.1b(c) "worth-the-compute" evidence |
| **WG gate-open** | per-ISO, order: PJM → NEISO → MISO → ERCOT → NYISO → CAISO | — | **HELD.** Prompts re-authored at gate-open per §2.1b(d); not included here by design (FF Wave-4 withdrawal stands) | — |

**Lane threads (sequential per lane across waves):**
L-CAP: 1A → 2B → (owner D-1/D-2) → 3A → WG · L-SCAR: 1B → 3A · L-VAL: 1D/1E → 2A/2E → 3B/3A ·
L-INP: 2C + WP → SA/SB · governance: 2D → owner sitting → 3A step-0.

**FR coverage ledger (every audit finding → exactly one owner):** FR-1/2/13 → 1A · FR-3 → 1C ·
FR-4/5 → 2B → owner D-1/D-2 · **FR-6 → no dedicated session by design**: the ERCOT scarcity
slack is expected to move with D-1/D-2 + the 1A/1B fixes and is re-measured at 3A; if it
survives the re-baseline it becomes a chartered L-SCAR structural session at WG-ERCOT, never a
tuned patch · FR-7/8/12 → 1B · FR-9 → 2A · FR-10/11/15 → 1D · FR-14 → 2E · FR-16 → SA ·
**FR-17 → owner D-7 weather-posture box** (2D/3A; ensemble machinery exists — this is a
decision, not code) · FR-18 → SB/PA · FR-19 → 2C → owner D-3 · FR-20 → PB/SC · FR-21 → 3B/3A ·
FR-22 → 1E · FR-23 → 1A/3B · FR-24/25/26 → 1D · FR-27 → 3B (stub) + WG (full).

**Efficiency rules baked into this pack** (why the ordering is what it is):

1. **No solve before its inputs settle.** T1-X re-runs sit in W2 because the 1B fix
   (`weather_year=2025` Martin Lake leak) changes every crossover comparator — running them in W1
   would burn the solves twice. The full 6-ISO battery runs ONCE, in W3, after the owner batch.
2. **One cache-epoch bump**, at Wave-1 close (§W1-X) — not per session. Every W1 session ships
   code + byte-identity proofs + minimal acceptance probes; bulk re-solving waits for W3.
3. **Reuse committed BEFORE legs** — never re-solve a leg your change provably doesn't touch;
   resume killed runs from the per-year cache (FF §2.4-3).
4. Rule-12 concurrency: ≤2 concurrent solve invocations; PJM/MISO (≥8.6 GB) never co-run.

---

## Wave 1 — structural fixes + guardrails (5 parallel sessions)

File-ownership (one owner per file this wave): 1A `model/capacity_evolution/{evolve,retirements}.py`
+ `results/evolution_ledger.py` + `scripts/check_forecast_invariants.py` · 1B `data/fleet/*` +
`model/reserves/spec.py` · 1C `model/capacity_evolution/adequacy.py` + `config/capacity_market.py`
(new constants) — **not** `runner.py` · 1D `runner.py` (CLI guards) + `config/scenarios.py` +
`.github/workflows/ci.yml` + `scripts/{pb5_*,golden_forecast_bands,check_registry_payload_parity,
register_forecast_run tests}` · 1E new `scripts/check_forecast_parity.py` (its `ci.yml` hunk lands
only **after 1D merges** — flagged serialize).

### FFR-1A [FABLE] — Confirmed-exit accounting: ledger the derates, complete the exits

```
[FABLE] FFR-1A — Close the I4/A1 capacity-accounting leak (FR-1), the partial-year exit
ghost (FR-2), and the latent additions-baseline gap (FR-13)

Read (beyond the implicit set): audit §3.1 FR-1/FR-2 + §3.2 FR-13 + FR-23;
src/market_sim/model/capacity_evolution/{evolve.py,retirements.py};
results/evolution_ledger.py; scripts/check_forecast_invariants.py (I4);
docs/handoffs/confirmed-retirement-plan-2026-07.md (registry semantics).

Two arms, two commits, strictly in this order:

ARM 1 — bookkeeping (dispatch-inert by construction):
1. Write the documented-but-never-written `confirmed_derates` ledger rows in the
   derate branch of apply_confirmed_exits (unit_id, fuel, mw_before, mw_after,
   derate_mw), and the documented `reason` split (`confirmed`|`announced`) at the
   retirement recorder. new_events() creates the key.
2. Teach check_i4_capacity_accounting to close the per-fuel balance including
   derates: fleet_after == fleet_before − retirements − confirmed_derates + adds.
3. Move the step-4.5 additions baseline snapshot ABOVE the commissioned-unit
   insert (FR-13) so a future entry_commissioning_lag arming ledgers its MW.
4. Add the missing reconciliation unit test at the evolve_fleet seam (per fuel,
   trivial 2-unit fixture first — the test FR-26 says would have caught FR-1).
5. Fix the FR-23 docstring drift in the SAME commit (evolution_ledger.py schema
   text ↔ writers now true; retirements.py:109-114 hydro claim — delete or
   correct; hydro itself is FFR-1C's, do not touch adequacy.py).
   Acceptance: dispatch/LP output byte-identical (ledger-only change); I4 now
   PASSES on re-probed T1-F for NEISO and PJM (audit: both clear FC-1 on this
   fix alone) — probe exactly those two ISOs, 2026-2030, nothing else.

ARM 2 — behavioral (separate commit, cited):
6. Complete partial-year confirmed exits in year+1 (FR-2): a registry row with
   exit_month ≤ 6 derates to its annual-average factor in effective_year and to
   its full reduced factor the following year. Cite each affected registry row
   in the commit. T0 probes NEISO+ERCOT before/after; then re-probe PJM + NEISO
   T1-F (Brandon Shores/Wagner + Merrimack are the live cases).
   Expect retirement-MW deltas — attribute them in the findings doc; do NOT
   re-tune anything in response (rule 1).

Do not: touch adequacy.py, arrays.py, runner.py, or any default; widen any band;
run any window >5 solve-years. Do NOT bump the cache epoch here (§W1-X owns it) —
your acceptance probes use isolated --out-dir caches.
Deliver: findings doc with the per-ISO I4 before/after and the Arm-2 MW deltas;
matrix row for the ledger fields if any ScenarioConfig field is added (none expected).
```

### FFR-1B [FABLE] — Solve-year availability: the fleet ages, measured events stay in backcast

```
[FABLE] FFR-1B — Key thermal availability to the SOLVE year (FR-7); gate the measured
2025 derate out of forecast (FR-8); fix the weather_year-keyed regime/reserve lookups (FR-12)

Read: audit §3.2 FR-7/FR-8/FR-12; src/market_sim/data/fleet/arrays.py
(:392,:568,:581,:688 and the 3 sibling BIN_FORCED_DERATE_BY_YEAR reads at
:1292,:1380,:1450); data/fleet/eia860.py:2411-2429; model/reserves/spec.py
(:1220,:1237-1239,:1303-1305 and the weather_year lookups at :1896,:2228,:2533,
:2875); results/scarcity.py:643-661 (ercot_market_regime — the correct seam).

1. FR-7: feed the age model the solve year (already available in
   _availability_matrix as `year`), not config.weather_year. Weather-shape
   lookups that genuinely mean "the pinned weather 8760" keep weather_year —
   separate the two meanings explicitly at each site. Assert entrant age ≥ 0 in
   a unit test; add a T0 forecast probe showing monotone availability aging.
2. FR-8: gate BIN_FORCED_DERATE_BY_YEAR (all 4 read sites) behind
   mode=="backcast" (or outage_source=="historic") so the Martin Lake 2025 event
   can never reach a forecast/crossover year. The table header already declares
   the retirement path for the entry — honor it, don't delete the entry.
3. FR-12: route the ERCOT non-releasable-withholding regime test through
   ercot_market_regime(year, config); sweep the reserve layer's
   int(config.weather_year) artifact lookups — each becomes solve-year-keyed
   (where the artifact has a forward story) or hard-gated backcast-only (where
   it is a measured record). One line each in the findings doc: which, why.
   Add the missing __post_init__ guard: bare ercot_multiproduct_as_coopt in
   forecast without ercot_as_forward_requirement is the same hard error the
   endogenous variants already raise.

BYTE-IDENTITY IS THE ACCEPTANCE BAR: in backcast weather_year == solve year, so
every change above must be a no-op there — prove dispatch byte-identity on all
six keeper configs (the FF-1F attestation pattern) before anything else. If any
keeper moves, STOP and file it as a finding (rule 11) — do not adjust.
Do not: touch evolve.py/retirements.py (FFR-1A's), adequacy.py (1C's),
runner.py/scenarios.py beyond the one guard (1D owns scenarios.py — coordinate
the single __post_init__ hunk with 1D's session or land it via 1D; flag in PR).
No cache-epoch bump here (§W1-X).
Deliver: findings doc with the site-by-site disposition table + byte-identity
attestation + the T0 aging probe.
```

### FFR-1C [OPUS] — Hydro in the accredited ledger (I7/A2)

```
[OPUS] FFR-1C — Accredit hydro in accredited_firm_capacity_mw at its published
per-ISO credit (FR-3)

Read: audit §3.1 FR-3; docs/handoffs/ff-2b-adequacy-basis-2026-07.md §"hydro"
(the spec: CAISO 3,601 MW / NYISO 3,343 MW / NEISO 30 MW dispatched-but-
unaccredited); src/market_sim/model/capacity_evolution/adequacy.py:131-198;
data/hydro.py (capacity source); docs/parameter-citations.md.
Context (2026-07-31): the forward hydro ENERGY climatology was fixed after the
audit (miso-110, forecast_monthly_hydro mode B->BF; PJM forward level
15.875->9.254 TWh). That is the energy-budget channel — your ACCREDITATION
term is orthogonal to it; cite it, do not re-diagnose or touch it.

1. Add the hydro term inside adequacy.py: hydro nameplate (from the hydro
   fleet/capacity loader, resolved for the solve year — NOT via the persistent
   fleet, which never contains hydro) × the ISO's PUBLISHED accreditation basis:
   CAISO NQC/RA counting, NYISO UCAP derate, MISO SAC wet/dry, NEISO/PJM/ERCOT
   per their published constructions. Every credit a cited constant in
   config/capacity_market.py (rules 5/13) — NEVER a value tuned to clear I7.
   Where no published basis exists, document and use nameplate × published
   class derate with the citation; no invented numbers.
2. Unit test asserting which fuels enter the accredited ledger (the FR-26
   missing test) — hydro present, and the known FF-2B gap magnitudes reproduced
   on a fixture.
3. Re-probe I7 at T0/T1 scale for CAISO/NYISO/MISO only (the three failing
   ISOs). Movement must be attributable to the cited credits alone.
Do not: touch runner.py (the firm_clean_mw display seam rides FFR-3B — flag it),
evolve.py, arrays.py; do not "fix" any remaining I7 gap with anything but a
cited published parameter — a residual is a finding.
Deliver: findings doc with per-ISO before/after I7 margins + citations table;
parameter-citations.md rows.
```

### FFR-1D [OPUS] — Enforcement wave: make the written rules executable

```
[OPUS] FFR-1D — CI + guards + config hygiene (FR-24, FR-25, FR-10, FR-11, FR-15,
FR-26-cheap)

Read: audit §3.5 FR-24/FR-25 + §3.2 FR-10/FR-11/FR-15 + FR-26;
.github/workflows/ci.yml; scripts/run_full_horizon.py:114-155
(assert_schedulable — the pattern to extend); config/scenarios.py __post_init__
(:8698-9144) + _CACHE_KEY_OPTIONAL_FIELDS.

1. CI (FR-24): add a no-solve job running check_forecast_invariants.py over the
   committed t1f/hindcast sidecars in frontend/data/hindcast/ (artifact-level —
   no LP); add frontend/data/{hindcast,forecast}/** to ci.yml path filters; add
   a mode/kind assertion to check_registry_payload_parity.py so a forecast run
   can never register into the backcast namespace. Correct the FF plan §1.1
   "CI-wired" sentence to describe what is now true.
2. §2.1b guard (FR-25): extract assert_schedulable to a shared helper and call
   it from EVERY schedulable entry point: market-sim run/sweep/ensemble/matrix
   (runner.py CLI), pb5_member_slice.py, pb5_assemble.py,
   golden_forecast_bands.py seed. Tests: >5 unauthorized years refused from
   each; 5 allowed; authorized 25 allowed.
3. Config hygiene: correlated_forced_outage backcast coercion in __post_init__
   (FR-10, one line, the datacenter_load_path pattern — prove backcast cache
   keys unchanged); hard forecast-mode errors for the backcast-only overlay
   family (FR-11 — the gas_price_factor pattern; enumerate all ~20 in the
   findings doc, guard each); delete the three inert FF-3D CLI flags + their
   ScenarioConfig fields (rule 26 — deleted means deleted); dedupe
   _CACHE_KEY_OPTIONAL_FIELDS (FR-15).
4. Cheap test debt (FR-26): registration-path smoke test (reindex over a tiny
   fixture namespace, assert chips/manifest well-formed); golden-fixture
   staleness expiry (test FAILS when any cache-key-affecting default differs
   from the seed's run_config — turning the frozen fixture from silent to
   loudly-stale; do NOT reseed, that is owner-authorized D-7).
NOTE: ci.yml is yours this wave; FFR-1E lands its parity job only after you
merge. scenarios.py is yours; FFR-1B's one AS-guard hunk lands through you or
after you merge (coordinate — flagged in both prompts).
Mechanism-matrix duty: field deletions + any new field ⇒ matrix rows same PR.
Deliver: findings doc listing every guard added + every field deleted; CI green.
```

### FFR-1E [OPUS] — Backcast→forecast parity check (the D-5 gap, generalized)

```
[OPUS] FFR-1E — A standing no-solve parity check between keeper postures and the
forecast orchestrator (FR-22)

Read: audit §3.5 FR-22; docs/FINDING-nyiso102-d5-parity-wiring-2026-07-30.md
(the incident: three NYISO downstate mechanisms existed only on the backcast
path); frontend/data/backcast/keepers/<ISO>.json (keeper flag surfaces);
runner.py (forecast orchestrator seams).

1. scripts/check_forecast_parity.py: for each ISO's current keeper run_config,
   enumerate armed solve-affecting mechanisms; assert each has (a) a forecast-
   orchestrator consumer, or (b) an explicit entry in a small committed registry
   (data or module constant) declaring it backcast-only-by-design with one line
   of why (e.g. measured overlays, rule 13). Fail loud on any mechanism in
   neither set. No LP anywhere.
2. Seed the registry honestly: sweep the six current keepers; every mechanism
   lands in (a) or (b) or becomes a FILED FINDING in your findings doc (the
   next D-5). The NYISO downstate family must pass (a) — it was wired
   2026-07-30.
3. Tests trivial-first (synthetic keeper config). CI wiring: add the job to
   ci.yml ONLY AFTER FFR-1D merges (file owned by 1D this wave).
Do not: wire any mechanism you find missing (that is a follow-up finding with
its own session — this session builds the detector).
Deliver: parity report for all six ISOs + the registry + findings doc.
```

### §W1-X — Wave-1 close checklist ✅ **DISCHARGED 2026-08-02** — `docs/handoffs/ffr-w1x-wave1-close-2026-08-02.md`

1. All five merged; keeper byte-identity attestations from 1A-arm-1/1B/1D present.
   → **PASS ×3.** All seven lanes merged. Attestations re-confirmed against the *merged*
   tree and the *current* keeper set; 1D's post-rebase `scenarios.py` reconciles cleanly
   with 1B's earlier-merged `__post_init__` hunk. **No keeper moved.**
2. **Bump the operator cache epoch ONCE** (`results/cache.py` documented mechanism) — FR-1/2/7/8
   change forecast output under unchanged keys; stale 2026+ cached bundles must not be reused.
   → **TAKEN 2026-08-02** as a dated ledger entry in `results/cache.py`'s docstring (no
   `CACHE_EPOCH` token — close doc §2.1). Invalidates every pre-Wave-1 **forecast-mode**
   cache at **any** solve year (FR-8 reaches a crossover's realized years); backcast caches
   and keeper bundles untouched. Purge command in the ledger — **solve cold**. Root-cause
   repair of the stale `PINNED_DEFAULT_CACHE_KEY` landed with it (§0b-4).
3. Confirm no Wave-1 session widened a band, moved a default (other than the enumerated
   guard/coercion/deletion set), or touched an out-of-training year.
   → **PASS / PASS / PASS**, per-merge evidence in the close doc §3.
4. Green-light Wave 2. → **GREEN**, and **FH-4/FH-5 unblocked** *(the §W1-X condition only —
   see §0d: FH-1's own §3.3 gate has since FAILED, and FH-4 remains blocked on that separate
   condition)*. Two carry-forward duties: FFR-2A's T1-X legs are exactly what the epoch
   invalidates (solve cold), and FFR-2B may reuse a committed BEFORE leg only if FR-1/2/7/8
   provably do not touch it.

---

## Wave 2 — evidence for the owner sitting (5 sessions; ≤2 concurrent solve invocations)

### FFR-2A [OPUS] — Crossover seam + T1-X refresh (ERCOT/PJM/MISO)

```
[OPUS] FFR-2A — Fix the crossover neighbor-gas seam (FR-9), diagnose the vanished
MISO crossover, re-run T1-X on the fixed availability envelope

Read: audit §3.2 FR-9 + §3.5 FR-21 (comparator staleness); runner.py:1352;
data/neighbor_price.py:206,481; scripts/run_capacity_hindcast.py (crossover
mode); scripts/score_crossover.py + scripts/_ff2d_crossover_adapter.py;
docs/handoffs/ff-t1-gate-2026-07.md §4.2-4.3.

1. FR-9: neighbor seam honors crossover_forward_gas_path for forward years and
   uses _hold_flat_extrapolate instead of raw dict indexing; extend
   assert_forward_drivers to cover the neighbor seam and weather_year-keyed
   overlays (belt-and-braces with FFR-1B's fix).
2. Diagnose why the FF-2D MISO crossover never registered (T0-scale repro of
   its first forward year; the audit's hypothesis is the seam KeyError —
   confirm or refute, one line).
3. Fold the two FF-2D L-VAL follow-ups: serialize refusal_marker + the flat
   metrics list inside score_crossover.py itself (retire the adapter), and add
   the fractional family-volume metrics (gas_twh/coal_twh) the rubric's FC-4
   rows need — currently uncovered, never silently passed.
4. Re-run T1-X 2023-2027 for ERCOT, PJM, MISO at post-W1 HEAD (the 1B fix
   changes the comparators — that is WHY this is Wave 2). Score with
   forecast_verdict --tier t1x against the CURRENT keepers' committed scores;
   note in the findings doc that CO2 remains reconstruction-basis-partial
   (treat price as load-bearing). Rule 12: ≤2 concurrent; PJM solo if RSS says.
   Quarantine: scoring stops at 2025; ≥2026 refusal tests must still pass.
Deliver: input-gap table vs current keepers + registered runs + findings doc.
```

### FFR-2B [OPUS] — Retirement-rule + entry-damper evidence (the D-1/D-2 case)

```
[OPUS] FFR-2B — Re-probe retirement_rule="pipeline" and the entry dampers at
post-W1 HEAD; deliver the owner's D-1/D-2 evidence (FR-4, FR-5)

Read: audit §3.1 FR-4/FR-5 + §3.3; docs/handoffs/ff-retirement-rule-
implementation-2026-07.md (the implemented rule + its probe arms);
docs/handoffs/forecast-retirement-calibration-plan-2026-07.md §2.1/§3 (T-R
bands — never restated looser); docs/handoffs/ff-entry-stack-completion-2026-07.md.

1. Probe arms at post-W1 HEAD, reusing every committed BEFORE leg that is
   invariant (never re-solve unchanged legs): PJM + MISO curve-ON T1-H legs
   (2021-2025, 2022 bridged) with retirement_rule=pipeline; MISO T1-F with
   pipeline + entry_rate_limits + entry_commissioning_lag armed (FR-13 is fixed
   by FFR-1A, so the commissioning ledger is now sound — verify I4 stays green
   with the lag armed, the latent-defect test).
2. Score: T-R battery + T-R10 no-inversion guard + LOYO within 2023-2025
   (scorer-side folds); re-measure I13 (cobweb) and BLK-10 (backstop MW) on the
   armed arms. Bands never widened.
3. Deliver the D-1/D-2 owner box: measured before/after per ISO, what each flip
   re-opens (expected: nothing — both are identified constructions), and your
   recommendation. The flips themselves are the OWNER's (executed in FFR-3A
   step 0) — do not change any default in this session.
Rule 12: the two multi-zone curve legs are ~8.6 GB each — sequential, never
co-run with FFR-2A's PJM leg (coordinate solve windows with the dispatcher).
Deliver: findings doc + registered probe runs + the decision box.
```

### FFR-2C [OPUS] — Net-CONE currency + FF-G3 activation evidence (the D-3 case)

```
[OPUS] FFR-2C — Re-anchor stale net-CONE vintages from PUBLISHED results; prepare
the FF-G3 escalation decision (FR-19)

Read: audit §3.4 FR-19; docs/handoffs/ff-g3-net-cone-forward-2026-07.md (design
landed, inert; D1-D5 open); config/capacity_market.py:1231-1418.

1. Rule-23 data-change re-derivations, one commit per ISO, each citing the
   published instrument: PJM 2028/29 BRA clearing (325.69 $/MW-day — the +34%
   the audit flags), and NYISO/MISO/NEISO wherever a newer published vintage
   exists than the on-disk last (verify each; no value without its citation).
   Reconciliation tests updated in the same commits.
2. Populate the FF-G3 owner box D1-D5 with the measured spread each escalation
   option implies vs hold-last (no default flip — decision is the owner's).
3. T0 smoke (NEISO 2026-2028) before/after the re-anchors; capacity-price
   validation script re-run (validate_capacity_prices, no LP).
Constants collide with nobody this wave (FFR-1C merged in W1). Matrix duty if
any new ScenarioConfig field appears (none expected).
Deliver: findings doc + citations + the D-3 box.
```

### FFR-2E [OPUS] — Validate the SHIPPED capacity-price posture (FR-14)

```
[OPUS] FFR-2E — Make the capacity-hindcast instrument exercise the production
curve-ON capacity-price formation (FR-14; peer-review bucket-A addition)

Read: audit §3.2 FR-14; docs/forecast-readiness-peer-review-2026-07.md §3.1
(the "validate the configuration you ship" row); scripts/run_capacity_hindcast.py
(:256-258, the capacity_market_clearing_by_iso=None default);
config/scenarios.py (the curve-ON production defaults for PJM/MISO/CAISO/NEISO);
docs/capacity-price-forward-methodology-2026-07.md; ff-t1-gate FC-3 rows.

1. Teach run_capacity_hindcast.py to run the SHIPPED posture: default the
   hindcast's capacity-market clearing to the production ScenarioConfig
   defaults (sloped VRR where the ISO ships curve-ON), with an explicit
   --fixed-net-cone flag preserving the old comparison arm. Never silently
   change what an existing committed FC-3 verdict means — new runs are new
   evidence rows, old sidecars stand as scored.
2. Re-run the T1-H capacity-hindcast legs for the curve-ON ISOs (2021-2025
   window, ≤5 solve-years per invocation, rule-12 concurrency; reuse every
   committed leg the posture change provably does not touch).
3. Score FC-3 on BOTH arms; the findings doc states, per ISO, whether the
   shipped posture's build/retire path diverges from the fixed-price arm and
   which arm the T1 gate evidence should cite (recommendation only — the
   rubric-text change, if any, is FFR-3A/3B's).
Do not: change any ScenarioConfig default; touch the rubric scorer beyond
reading it; exceed 5 solve-years in any invocation.
Deliver: findings doc + registered runs + the per-ISO posture-divergence table
(feeds the D-1/D-3 owner boxes — a sloped-curve validation posture changes what
those flips are judged against).
```

### FFR-2D [FABLE] — Governance brief: the owner sitting's packet

```
[FABLE] FFR-2D — Assemble the owner-decision packet (docs only, no code, no solve)
— REWRITTEN 2026-07-31: part of D-5 is already EXECUTED by the owner

Read: audit §2, §4 Phase 2; pack §0a (the state delta — your ground truth for
what already happened); frontend/data/backcast/calibration-complete.json (the
two-block restructure + all three `complete` entries verbatim);
frontend/data/backcast/holdout-freeze.json; keepers/<ISO>.json (all six);
docs/forecast-development-plan-2026-07.md §2.1b;
docs/forecast-readiness-peer-review-2026-07.md §3.3 (the D-7 weather box).

1. One packet doc (docs/handoffs/ffr-owner-sitting-<date>.md): the decision
   batch with, per item: what it changes, the evidence doc (FFR-2A/2B/2C/2E
   outputs as they land), what it re-opens, recommendation, sign-off line.
   The batch as of 2026-07-31: D-1 retirement-rule flip, D-2 damper arming,
   D-3 net-CONE currency, D-4 fuel option A/B, D-5-residue (below), D-6-residue
   (below), D-7 golden-run posture (now TWO sub-questions: fixture reseed
   authorization AND weather posture — single pinned draw labelled
   weather-conditional vs weather-year ensemble golden; peer review §3.3.3).
2. D-5 residue (the marker briefs are OBSOLETE — do not write a PJM
   calibration-complete memo; the owner declared PJM 2026-07-31, and NYISO was
   re-declared, NEISO re-scoped, all in the two-block restructure). What
   remains for the owner:
   (a) §2.1b(a) reconciliation: the plan's gate-(a) text predates the
   complete/final split and still cites the superseded NYISO withdrawal —
   propose the one-paragraph amendment (gate (a) keys on `complete`; `final`
   is never required for forecast work) for owner sign-off, executed by
   FFR-3B.
   (b) Marker keeper-snapshot policy: all three `complete` entries freeze the
   keeper-at-declaration (pjm-140 / nyiso-100 / neiso-54-lineage), which lags
   the dashboard keepers (pjm-143b / nyiso105 / neiso-71). Lay out re-key vs
   by-design-snapshot ONCE, as policy, not per-ISO briefs; note the freeze
   makes this non-urgent (nothing is spendable while it stands, and the
   freeze-lift is the owner's alone, outside this program).
   (c) Flag (do not resolve) the tier-agnostic-vs-tier-aware enforcement
   wording inconsistency between PJM's marker text and CLAUDE.md rule 22.
3. D-6 residue: the NYISO C3c adjudication is DONE (owner accepted the
   ledgered caveat; NYISO is CALIBRATED-WITH-CAVEATS with a validation
   marker). What remains: the FF-3D pair-evidence regeneration order (rule-11
   taint on the R5a Option-B pair) — schedule it or explicitly wontfix it.
4. Keep the packet strictly decision-support: no recommendation dressed as a
   default change, no number without its measured source.
Deliver: the packet, cross-linked from the audit doc (one-line edit).
```

**⛔ OWNER SITTING** — decisions D-1..D-7 signed (or explicitly deferred, which re-scopes FFR-3A
step 0 to the signed subset). Nothing in Wave 3 starts before this.

---

## Wave 3 — re-baseline (the single consolidated battery)

### FFR-3B [OPUS] — Staleness machinery + bookkeeping reconciliation (land first or parallel)

```
[OPUS] FFR-3B — Make verdict/HEAD drift detectable; reconcile the stale registries
(FR-21, FR-23, FR-27-cheap)

Read: audit §3.5 FR-21/FR-23; scripts/register_forecast_run.py;
frontend/data/forecast/{program-status.json,ff-verdicts.json} (schema only —
do NOT hand-edit contents; FFR-3A regenerates them).

1. Schema: every verdict/board artifact carries scored_at_sha + cache_epoch +
   scored_at_date (register_forecast_run + the battery emitters). FFR-3A
   populates them.
2. CI staleness check (WARN-level): flags when solve-affecting paths
   (src/market_sim/**, the schedulable scripts) have moved ≥N commits past the
   newest scored_at_sha on the board — the audit's "ten days dark" failure mode
   becomes visible. WARN, not FAIL (backcast velocity must not be blocked).
3. Bookkeeping desync (FR-21/FR-23): FF plan §1.2 + WAVE FI rows to landed
   truth (G2/G3/G5 landed, G4 memo-only); gap-register rows; wave-manager
   ledger gains the FF-G rows + these FFR rows; ercot.md:336 ERCOT-93 claim
   corrected (machinery NOT merged, patch rotted); firm_clean_mw display seam
   from FFR-1C's flag; forecasting-entry-exit-assessment.md headline re-graded
   post-flip (state what FF-2C changed; keep every measured claim sourced).
   ALSO (2026-07-31 refresh): execute the SIGNED D-5(a) §2.1b(a) amendment
   (gate (a) keys on the `complete` block; drop the superseded NYISO-withdrawal
   example); fix the mechanism-matrix header `keepers:` object in
   docs/codebase-site/data/mechanism-matrix.js (ERCOT/CAISO entries lag their
   per-column re-stamps) and the two stale "Built 2026-07-27 keeper snapshot"
   header lines (matrix .js + mechanism-testing-matrix.md) — header hygiene
   only, never a cell verdict.
4. Add the forecast DOF-ledger builder STUB chartered honestly (FR-27): emit
   the ledger skeleton from run_config with identification-source fields left
   explicitly UNATTESTED — turning FC-7's silent CAVEAT into a fillable
   artifact. (Full attestation is WG/Phase-B work.)
Deliver: findings doc; CI check live; docs reconciled — every claim it corrects
cites where the truth now lives.
```

### FFR-3A [OPUS] ⛔ — Execute signed decisions + re-score everything

```
[OPUS] FFR-3A — Execute the signed owner decisions, then re-run the T1 gate
battery at the post-fix HEAD and regenerate every board

Requires: Wave 1 + 2 merged, owner sitting done, FFR-3B schema landed.
Read: audit §4 Phase 3; docs/handoffs/ff-t1-gate-2026-07.md (the battery recipe
to mirror); docs/forecast-determination-rubric.md; the signed packet.

0. One dedicated commit per SIGNED decision, each citing the sign-off (FF-2C
   pattern): retirement_rule default (D-1), damper arming (D-2), net-CONE
   escalation choice (D-3), fuel option (D-4), D-5 residue actions (any
   marker re-key + the §2.1b(a) amendment ride FFR-3B, not marker files
   here — the PJM/NYISO/NEISO `complete` declarations already happened
   2026-07-31, see §0a), D-6 residue (FF-3D pair regeneration order), golden
   reseed IF authorized (D-7 — it is a 15-solve-year invocation; run it ONLY
   under its own written authorization, --full-solve-authorized, per
   §2.1b(d); apply the SIGNED weather-posture choice — single-draw goldens
   carry the weather-conditional label from the peer review's disclosure
   list).
1. The consolidated battery, rule-12 scheduled (pairing: light ISOs pair, PJM
   solo, MISO solo; budget ~1 day wall): T1-F 2026-2030 × 6 ISOs; T1-H re-scores
   (re-solve ONLY legs the signed decisions touch — a flipped retirement rule
   touches all four curve legs; an unflipped one means scorer-only); fold
   FFR-2A's T1-X (re-run only if a signed decision moved dispatch); FC-6 driver
   battery at the CURRENT posture (first time since 2026-07-12 — required for
   any future T1→T2 promotion); FF-3E readiness battery re-run.
2. Score with forecast_verdict per tier; regenerate ff-verdicts.json,
   program-status.json (from the new evidence — gate (a) rows now carry the
   HEAD keepers + the marker actions), the FF-3E scorecard, and the mechanism-
   matrix header re-stamp. Every artifact carries scored_at_sha + cache_epoch
   (FFR-3B schema).
3. Deliverable docs/handoffs/ffr-t1-regate-<date>.md: per-ISO promotion table,
   regression vs FF-2D with every moved metric naming its causal commit, and
   the refreshed per-ISO §2.1b gate scorecard for the owner. Promotion/gate-open
   decisions remain the owner's; your output is the measured scorecard.
Do not: tune anything in response to a re-score; widen bands; touch
out-of-training years; exceed 5 solve-years in any single invocation (the
golden reseed, if authorized, is its own separately-authorized invocation).
```

---

## Wave S — structural mechanisms (default-off / no-solve; W3 baseline stays valid)

### FFR-SA [FABLE] — Load-shape evolution (FF-G4 Option B, implement)

```
[FABLE] FFR-SA — Implement the FF-G4 Option-B load-shape mechanism (additive EV +
heat-pump end-use layers), DEFAULT OFF (FR-16)

Read: docs/handoffs/ff-g4-load-shape-design-memo-2026-07.md (the decided design
— implement, don't re-design); audit §3.4 FR-16; runner.py:274-289
(_scale_demand); data/datacenter.py:312 (electrification_shape stub).

1. Implement per the memo: cited end-use shapes, additive layers over the
   weather-8760, ScenarioConfig field(s) default OFF, backcast/hindcast-coerced
   (the datacenter_load_path pattern), cache-key-registered, matrix rows in the
   same PR. Every parameter cited (parameter-citations.md).
2. Acceptance: backcast byte-identity; T0 smoke NEISO then PJM 2026-2028 armed
   vs off — the ISO-NE winter-peak trajectory becomes EXPRESSIBLE (directional
   check vs CELT, context not fit target); invariants green.
3. Owner box for arming posture — no default flip here.
Rule 19: enumerate what already shapes demand (DC block) and document the seam —
one mechanism per phenomenon, additive layers must not double-count DC MW.
```

### FFR-SB [FABLE] — Nuclear-registry consumption design memo (no code)

```
[FABLE] FFR-SB — Design how the FF-G5 nuclear license/SLR registry enters the
exit path WITHOUT a second exit mechanism (FR-18/BLK-9; memo only)

Read: docs/handoffs/ff-g5-nuclear-registry-2026-07.md (registry + loader, 59
units, consumed by nothing); audit §3.3/§3.4; model/capacity_evolution/
retirements.py (the ONE exit path); confirmed-retirement-plan (instrument bar).
Research step (FF §4): how IPM/ReEDS treat license horizons vs economic exit.

Memo (docs/handoffs/ffr-sb-nuclear-consumption-<date>.md): candidate designs
graded vs rules 13/19/23 (license ceiling as an availability horizon vs a
confirmed-exit-grade instrument vs an announced-retirement date source), what
each regenerates from for a forward year, identification per parameter, an
owner-decision box. Explicitly: NO second exit mechanism — the design must
compose with the existing screen/registry. No code, no solve.
```

### FFR-SC [OPUS] — FF-G1 transmission A/B + input refresh follow-ups

```
[OPUS] FFR-SC — Run the owed FF-G1 T1-F A/B (transmission expansion gate);
execute surviving small input refreshes

Read: docs/handoffs/transmission-expansion-grounding-2026-07.md + the fast-tier
D2 apply note (engine landed 2026-07-26, default off, A/B never run); audit
§3.3/§3.4 FR-20.

1. T1-F A/B (one ISO with committed instruments, e.g. PJM or CAISO 2026-2030,
   gate off vs on): invariants, price/flow deltas at the registered interfaces,
   findings + registered runs. No default flip — owner box.
2. Input refreshes as data lands from WP: ATB 2025/2026 re-derive of
   NEW_ENTRY_COSTS (rule 23, cited; tests updated), demand-anchor bumps to the
   2026 Gold Book / MISO LTLF vintages where FF-G4 D4 flagged them.
Rule 12; ≤5 solve-years; registration + matrix duties standard.
```

---

## Wave P — parallel-anytime intake (data/docs only; no solve; dispatch whenever)

### FFR-PA [OPUS] — Confirmed-retirements re-query (time-sensitive)

```
[OPUS] FFR-PA — Refresh the confirmed-retirements registry; adjudicate the
Eddystone §202(c) expiry (FR-18) — DATA ONLY

Read: data/raw/confirmed-retirements/ (+README, vintage 2026-07-05); audit
§3.4 FR-18; docs/handoffs/confirmed-retirement-plan-2026-07.md (instrument bar).

1. Re-query every ISO's rows: the PJM Eddystone DOE §202(c) order expires
   2026-08-22 — record the successor state (renewed / lapsed / superseded)
   WHEN PUBLISHED, never speculatively; Brandon Shores/Wagner FERC extension
   status; MISO Attachment Y cross-check (the never-done item); NYISO stays an
   honest zero unless a real enforceable instrument exists.
2. Every row change carries its public instrument citation (the plan's bar);
   registry README vintage updated; loader tests green. Propose (don't build)
   a quarterly re-query cadence line for the plan.
No solve; no CI workflow (owner-billed runners); rule 22 untouched.
```

### FFR-PB [OPUS] — Cost/policy vintage intake (M1/M2 closure)

```
[OPUS] FFR-PB — Land ATB 2025 (or 2026) and the §45Y/48E primary-statute
verification (FR-20; FF-0D M1/M2) — DATA + CITATIONS ONLY

1. M1: fetch/land the newer NREL ATB electricity workbook through the
   data-intake contract (schema'd, curated partition); do NOT re-derive
   NEW_ENTRY_COSTS here (FFR-SC executes the re-derive against this data).
2. M2: verify the 2033-36 "other-clean" phase-down steps against primary
   statute/Treasury text; correct scenarios.py citation comments (values only
   if the primary source differs — rule 23 citation either way).
3. Where the proxy blocks a source, log MANUAL DOWNLOADS NEEDED rows — never
   guess values.
```

---

## Dispatch cheat-sheet (owner)

1. **Now:** launch FFR-1A/1B/1C/1D/1E in parallel, **plus FFR-PA in the same wave** (its
   Eddystone §202(c) checkpoint is 2026-08-22) and FFR-PB anytime. Watch for the two
   byte-identity attestations (1A arm-1, 1B) — a keeper that moves is a stop-the-line finding.
2. **Wave-1 close:** run §W1-X (single cache-epoch bump), then launch FFR-2A/2B/2C/2E (≤2 solve
   sessions at a time; PJM/MISO legs never co-run) + FFR-2D.
3. **Sitting:** decide the FFR-2D packet (D-1..D-4, D-5/D-6 residues, the two-part D-7).
4. **Then:** FFR-3B, then FFR-3A (the one big battery, ~1 day wall). Its output is the refreshed
   §2.1b scorecard — the gate-open conversation happens on THAT, per ISO, PJM first.
5. **Anytime after W3:** FFR-SA/SB/SC (default-off; baseline stays valid).
6. **WG (gate-open per ISO)** stays held: prompts are re-authored at gate-open under §2.1b(d) —
   this pack deliberately contains none (FF Wave-4 withdrawal stands).
7. **Wave FH (forward-mode hindcast, T1-FF)** — its own pack:
   `docs/hindcast-forward-plan-2026-07.md`. Runs the model in FORECAST configuration over historic
   years (base 2023 → 2023-2025, then base 2021 → 2021-2025) with **no measured overlays**, scored
   2023-2025 against bench + keeper comparators; the keeper→ArmR→ArmK spread measures what the
   overlays are worth and what driver-forecast error costs. Launch FH-1/2/3 alongside Wave 2;
   **FH-4/5 only after §W1-X** (FR-7/FR-8 would corrupt every weather-pinned historic solve, and
   the epoch bump keeps stale 2026+ bundles out). Its output is the missing capacity-expansion
   skill measurement the peer review names as bucket-C item 7.

*Produced 2026-07-30; refreshed 2026-07-31 @ HEAD `7b8c36a` (state delta §0a; FFR-2E added,
FFR-PA promoted, peer review `docs/forecast-readiness-peer-review-2026-07.md` folded in). No LP
solved, no parameter changed, nothing registered by the pack itself.*

---

## Wave 3 lanes — dispatch ledger and the UNDISPATCHED prompts (added 2026-08-04, HEAD `a7966013`)

These lanes were authored by the workstream manager after the Wave-3 battery and dispatched
from chat. **They are written into the pack here because a prompt that exists only in a chat
session is lost when that session ends** — the same failure that lost a prior manager's
decision cards. The dispatch ledger below is the authoritative record of which ran.

### Dispatch ledger

| Lane | Purpose | State at 2026-08-04 `a7966013` |
|---|---|---|
| FFR-3A-2 / 3A-3 | Close the T1 battery; boards | **RAN.** `docs/handoffs/ffr-3a2-battery-close-2026-08-03.md`; 18 hindcast sidecars + `ff-verdicts.json` registered |
| FFR-3H | CAISO 65.5 % backstop diagnosis | **RAN.** `docs/handoffs/ffr-3h-caiso-backstop-2026-08-04.md` |
| FFR-SC-2 | FF-G1 CAISO transmission A/B | **RAN.** Gate INERT in CAISO and PJM; independently replicated |
| FFR-SA-close | PJM load-shape smoke | **RAN.** Off-leg 2026–2028, invariants PASS |
| FFR-3J | Kill-resume discriminator | **PARTIAL** — instrumentation landed (`ef5695b0`); the drill was never re-run. Superseded by FFR-3M below |
| FFR-3L | ERCOT T1-X price-2025 attribution | **RAN** |
| FFR-3N | FH-1 I12 inversion attribution | **RAN** — arms pre-registered before solving |
| FFR-3P | CAISO accreditation ledger | **RAN**, incl. a paired NQC arm and two self-retractions |
| FFR-3Q | Window re-cut under G.5(a) + D-9 | **RAN.** Task 0 rule-22 **VERIFIED**; Task 2 escalated (sitting Addendum J) |
| **FFR-3K** | **FC-7 for T1-H / T1-X** | **NEVER DISPATCHED** — prompt below. FFR-3Q re-confirmed the defect is live |
| **FFR-3M** | **Kill-resume adjudication** | **NEVER DISPATCHED** — prompt below |
| **FFR-3R** | **Record-provenance defect class** | **NEVER DISPATCHED** — prompt below |

Each prompt below is self-contained but its `VERIFIED STATE` block is a **snapshot**: re-verify
HEAD, keepers, markers and the freeze at your own HEAD before acting. Main moved ~150 commits in
four hours on 2026-08-04 and all six keepers changed inside three days.

### FFR-3K [OPUS] — FC-7 for the T1-H and T1-X tiers (the unfixed analogue)

```
[OPUS] FFR-3K — Fix FC-7 for the T1-H and T1-X tiers. This is the UNFIXED ANALOGUE of a
bug already fixed once, and it must land BEFORE the next battery.

=== VERIFIED STATE (snapshot 2026-08-04 @ a7966013 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT ercot158-pool-arm ·
PJM pjm-151-seam-envelope · CAISO caiso164-zonal-loss-surface · NYISO nyiso-120-c119-scope ·
NEISO neiso-caiso156-meter-screen · MISO miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast
out-of-training only). Cache epochs 2026-08-02 + 2026-08-03b.
PREREQUISITES IN ORDER: `uv sync` (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which is not a data
problem), THEN scripts/regenerate_clean.py (~65 min) only if you need a smoke leg.
Rule 12's cap is PER PROMPT (sitting Addendum F.2). Rule 27: scripts/run_* — Opus/Fable only,
never a full-file rewrite from response content.

=== THE BUG ===
`run_capacity_hindcast.py` writes `run_config.yaml`; FC-7 row 1 requires `run_config.json`.
FC-7 therefore fails on EVERY T1-H and T1-X leg by construction and carries no information
about leg quality. FFR-3Q re-confirmed it is still live.
This is the exact defect FFR-3D fixed at `34c2f25` — but only in `run_full_horizon.py`. READ
THAT COMMIT and REUSE its `write_run_config` rather than writing a second implementation.
`ea7cd5d` fixed a crash in that repair; confirm you are past it and inherit the fix.

=== WHY IT MUST LAND FIRST ===
FFR-3A-2 deliberately did not fix it: authoring the artifact after seeing the score is what
rubric §4 forbids. The same logic binds you in reverse — this lands as an INSTRUMENT change
BEFORE the next battery scores anything, never as a retrofit. Do NOT hand-author a
run_config.json into any already-scored bundle and do not re-score a committed leg to pick
up the fix.

=== SCOPE ===
1. Emit run_config.json from run_capacity_hindcast via the same writer run_full_horizon uses.
   Keep the .yaml if anything reads it — check before deleting.
2. A test that would have caught this: assert the artifact FC-7 reads exists after a minimal
   hindcast run. One per tier if the paths differ.
3. Verify no keeper moves and no cache key moves — artifact emission must be solve-inert. A
   keeper that moves under it is STOP-THE-LINE.
4. Check whether any OTHER runner has the same gap. Two instances of one defect was a
   coincidence; a third would be a pattern and finding it is cheap.
5. State plainly that every committed T1-H/T1-X FC-7 verdict predating your fix is an
   INSTRUMENT ARTIFACT, not a leg-quality signal.

=== TRAPS ===
Push 413 has two causes — a stale tracking ref of a deleted merged branch (`git remote prune
origin`) or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase); FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files. The
documented cache-purge command deletes TRACKED files; `git status --short` after. Shell cwd
persists between Bash calls.

Deliverable: docs/handoffs/ffr-3k-fc7-hindcast-<date>.md. Small lane; do not expand it.
```

### FFR-3M [OPUS] — Adjudicate FF-3E part c (the discriminator is already built)

```
[OPUS] FFR-3M — Run the instrumented kill-resume drill and adjudicate FF-3E part c.
The discriminator is BUILT. Nobody ran it.

=== VERIFIED STATE (snapshot 2026-08-04 @ a7966013 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ the shards yourself): ERCOT ercot158-pool-arm · PJM pjm-151-seam-envelope ·
CAISO caiso164-zonal-loss-surface · NYISO nyiso-120-c119-scope · NEISO
neiso-caiso156-meter-screen · MISO miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast
out-of-training only). Cache epochs 2026-08-02 + 2026-08-03b.
PREREQUISITES IN ORDER: `uv sync` (~2 min) THEN scripts/regenerate_clean.py (~65 min).
Rule 12's cap is PER PROMPT (Addendum F.2).

=== WHERE THIS STANDS ===
FF-3E part c (kill-resume) FAILs at HEAD where FF-2D recorded GREEN for all six ISOs: the
first freshly-solved year after a resume has identical aggregates and identical evolution
counts but different byte hashes on dispatch AND price (FFR-3A-2 §6.4). Cross-year warm start
is RULED OUT (MARKET_SIM_WARMSTART_XYEAR defaults off).
FFR-3J (`ef5695b0`) built the discriminator and STOPPED THERE — it never re-ran the drill.

=== READ ef5695b0's COMMIT MESSAGE FIRST — it corrected the test ===
The originally pre-specified `_arr_hash(np.sort(arr))` sorts along the LAST axis, so it is
invariant to reordering hours WITHIN a row but NOT to a permutation of the rows themselves —
exactly what the ordering hypothesis names. Run literally it would have pointed at alternate
optima for an ordering fault. FFR-3J records BOTH:
  *_sorted_hash    literal last-axis sort (continuity)
  *_multiset_hash  np.sort(arr, axis=None) — sees through any permutation
  *_shape          because tobytes() cannot separate (a,b) from its (b,a) twin
READ THE VERDICT OFF `*_multiset_hash`. Two synthetic tests already pin the discriminator.

=== THE ADJUDICATION ===
* multiset MATCHES, byte differs -> MECHANISM 1, ARRAY ORDERING. A determinism bug in the
  cache-reload path. FIXING IT IS IN SCOPE (plumbing, not model behaviour). Add a regression
  test. A keeper that moves under a determinism fix is STOP-THE-LINE.
* multiset ALSO differs -> MECHANISM 2, ALTERNATE OPTIMA. DO NOT PIN A BASIS. Write it up as
  an owner design question with the trade stated: determinism vs solver freedom, and cost.

Attribute WHEN it broke if a bisect is bounded; say so plainly if it is not. Update the FF-3E
scorecard entry for part c.

=== DO NOT ===
Do not widen the drill's tolerance or make it compare aggregates instead of hashes — the
aggregates ALREADY match, and that is the entire finding. Do not disable the drill.

Deliverable: docs/handoffs/ffr-3m-kill-resume-verdict-<date>.md. Small lane.
```

### FFR-3R [OPUS] — Make the record-provenance defect class structurally impossible

```
[OPUS] FFR-3R — Make the "recorded config diverges from solved config" defect class
STRUCTURALLY IMPOSSIBLE. Four instances have now been patched one at a time.

=== WHY THIS LANE EXISTS ===
Four separate lanes each independently found one defect: a run's recorded metadata sourced
from the CLI `args` namespace rather than the ScenarioConfig the solve ran on, so the record
says something the run did not do.
  FFR-1D — "a meta entry sourced from a flag that armed nothing"
  FFR-3D — entry_lookahead_reprice / correlated_forced_outage: once C.4(c) made the flags
           tri-state, bool(None) stamped `false` on legs that ran the shipped `True`
  FFR-2E — capacity_market_clearing: a flag-sourced value mis-classified every
           shipped-posture leg as curve-OFF, because forecast_verdict._curve_on reads it
  FFR-3L — retirement_rule: MISSED by the FFR-3D sweep, so every leg omitting
           --retirement-rule recorded `null` rather than the rule it solved
Each fix is correct and each carries a comment explaining why THAT key is solved-sourced.
That is the problem: correctness is per-key and maintained by comment. **Your job is the
class, not a fifth key.**

=== VERIFIED STATE (snapshot 2026-08-04 @ a7966013 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ the shards yourself): ERCOT ercot158-pool-arm · PJM pjm-151-seam-envelope ·
CAISO caiso164-zonal-loss-surface · NYISO nyiso-120-c119-scope · NEISO
neiso-caiso156-meter-screen · MISO miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. FREEZE ACTIVE (irrelevant — you
should need NO solve). PREREQUISITE: `uv sync` (~2 min). Rule 27: scripts/run_* — Opus/Fable
only, never a full-file rewrite from response content.

=== THE DISTINCTION THAT SCOPES YOU ===
`args` -> config is LEGITIMATE and NOT your target; run_calibration_full.py alone has ~50
such entries that BUILD the config, which is what a CLI is for. The defect is exclusively in
the RECORD: any artifact describing what a run did (meta.json, run_config.json, registration
sidecars, attestations) whose value is read from args instead of the solved config. If you
are editing config CONSTRUCTION you have left your scope.

=== SCOPE ===
1. CENSUS FIRST. Enumerate every record-artifact field, across every runner and every
   registration/attestation writer, that is args-sourced. Table it with a verdict per field:
   DIVERGENT-NOW / CANNOT-DIVERGE-TODAY-BUT-FRAGILE / DELIBERATELY ARGS-SOURCED. The census
   is a deliverable even for fields you do not change.
   Known starting points in run_capacity_hindcast.py's meta dict (verify at your HEAD):
   energy_only_floor, limited_foresight_dispatch, entry_screen_diagnostics are still
   bool(args.*). capacity_market_clearing_forced looks DELIBERATE (it records the force flag,
   distinct from the resolved capacity_market_clearing key above it) — confirm before
   touching, and if deliberate, KEEP it and say so.
2. MAKE THE CLASS IMPOSSIBLE. Do not hand-patch three more keys and add three more comments —
   that is the pattern that produced this lane. Derive the config-describing keys from the
   config object, with a short explicit allowlist for genuinely args-sourced ones, each
   carrying its one-line reason. Property to guarantee: a new ScenarioConfig field cannot be
   recorded from args without someone deliberately opting it in.
3. A TEST THAT FAILS ON INSTANCE FIVE. Assert every meta/run_config key naming a
   ScenarioConfig field equals the solved config's value, allowlist the only exemption. Prove
   it catches the real historical bug (omitted tri-state flag whose shipped default is True).
4. SAY WHAT THE EXISTING RECORD IS WORTH. Per key: from what date, which artifacts, and
   whether any PUBLISHED VERDICT depended on it. FFR-2E is the precedent that matters —
   _curve_on reads capacity_market_clearing to classify legs, so a wrong value changed a
   classification, not just a label. Do NOT retro-edit committed sidecars.
5. CHECK THE OTHER RUNNERS: run_full_horizon.py, run_calibration_full.py, run_calibration.py,
   and the register_* / attestation writers.

=== DO NOT ===
Do NOT change any default, config value, cache key, or anything solve-affecting. RECORD-ONLY:
prove `cache_key(ScenarioConfig())` is identical before and after and that no keeper moves.
Do NOT retro-edit committed artifacts. Do NOT revert or "simplify away" another lane's fix —
the four existing solved-sourced keys are correct; you are generalizing them. Do NOT expand
into config construction. Do NOT add a GitHub Actions workflow (private repo, billed
runners); extend ci.yml if CI enforcement is wanted.

Deliverable: docs/handoffs/ffr-3r-record-provenance-<date>.md — the census table with a
verdict per field; the structural change and the property it guarantees; the test and its
proof against the historical bug; the per-key statement of which committed records are
unreliable and whether any published verdict depended on them; and an explicit list of any
runner or writer you did NOT audit.
```

---

## §0f — Wave-3 ledger CORRECTION and the four lanes dispatched 2026-08-04 @ `145e4c5f`

Read this **after** the Wave-3 ledger above; it supersedes that ledger's status column.
Decision citations: sitting **Addendum K** (`docs/handoffs/ffr-owner-sitting-2026-08-02.md`).

**Ledger correction (Addendum K.4).** FFR-3M **LANDED** (`4c403dd9`) and FFR-3R **LANDED**
(`0f788c29`); do not re-dispatch either. **FFR-3K is still undispatched and its defect is live
at HEAD** (`run_capacity_hindcast.py` **L1419**, not L1303 as FFR-3Q §3.5 cites — the line
moved, the defect did not). **FFR-3Q Task 1 never reported** (§0/§2.2/§4 all `*(pending)*`;
zero `ffr3q-*` sidecars among the 132 in `frontend/data/hindcast/`), so **FH-4/FH-5 is NOT
lifted** and the re-probe is re-dispatched below as FFR-3Q-2.

**Two decisions signed 2026-08-04:** **D-9 = (ii) COD-shifted scoring** (Addendum K.2) and
**D-10 = `forecast_xyear_warmstart` OFF for forecast bundles** (Addendum K.3). FFR-3S and
FFR-3T implement them.

**Landing order.** FFR-3K and FFR-3S are both **instrument** changes and both land **before
the next battery scores anything**. FFR-3T shifts every forecast cache key and must be
sequenced against FFR-3Q-2. FFR-3Q-2 is independent of all three and starts immediately.

### FFR-3K [OPUS] — FC-7 for the T1-H and T1-X tiers (unchanged charter, refreshed header)

The prompt body in the Wave-3 section above stands as written. Replace only its VERIFIED STATE
header with the `145e4c5f` header used by the three prompts below, and correct the line
reference: the defect is at **L1419**, `config.to_yaml_full(args.out_dir / "run_config.yaml")`.

### FFR-3Q-2 [OPUS] — re-run the FFR-3Q Task 1 re-probe (the FH-4/FH-5 gate)

```
[OPUS] FFR-3Q-2 — Solve and report the FFR-3Q Task 1 re-probe. FFR-3Q pre-registered this
posture and then never solved it; you are finishing exactly that task and nothing else.
This lane GATES the FH-4/FH-5 lift, which is a MANAGER box — you do not lift it, you do not
declare it liftable, and reporting green does not lift it (sitting Addendum I.1).

=== VERIFIED STATE (2026-08-04 @ origin/main 145e4c5f — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; NYISO moved 7x in 4 days):
ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-03-pjm-151-seam-envelope ·
CAISO 2026-08-04-caiso164-zonal-loss-surface · NYISO 2026-08-04-nyiso-120-c119-scope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: calibration-complete.json `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY.
HOLDOUT FREEZE ACTIVE (holdout-freeze.json) — it blocks out-of-training BACKCAST solve/score/
registration only. It does NOT block T1-FF windows, forecast-mode 2026+, or in-sample work.
Cache epochs 2026-08-02 (all forecast) + 2026-08-03b (NYISO-forecast-scoped). Forecast work
solves COLD — deliberate, not a bug to route around, and results/ is gitignored so "expect
cache hits" is never a valid budget in a fresh container.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly
like a data problem and is not one), THEN scripts/regenerate_clean.py (~63-65 min, 50
datatypes, 1.6 GB). On the uv path the tzdata/ZoneInfoNotFoundError trap does not arise.
Rule 12 is PER PROMPT (Addendum F.2): years sequential within an invocation, <=2 concurrent
invocations, <=5 solve-years per invocation, PJM and MISO never co-run. Rule 27: Opus/Fable
only for src/ and scripts/run_*; never a full-file rewrite from response content.

=== WHAT IS ALREADY DONE — DO NOT REDO IT ===
Read docs/handoffs/ffr-3q-window-recut-2026-08-04.md in full first.
- Task 0 (rule-22 legality of a base-2021 T1-FF window) is VERIFIED BY EXECUTION. The
  existing carve-out covers it: HINDCAST_SOLVE_YEARS = {2021,2023,2024,2025} (four solve-
  years, under the <=5 cap), 2022 BRIDGED (evolved across, never solved, data never read),
  scoring bounded to 2023-2025 on both sides, vintage 2020 enumerated and <= base 2021.
  Nothing was widened and no marker was spent. Do NOT re-derive this and do NOT edit
  holdout_policy.py.
- Task 2 (D-9) is done and became sitting Addendum J; D-9 has since been re-signed as (ii).
  Not yours.
- §2.1 pre-registers your posture and pairing. Honour it as written; changing a pre-registered
  read after the fact is the thing the pre-registration exists to prevent.

=== YOUR TASK: solve the two arms and fill §2.2, §0 and §4 ===
ERCOT, Arm R (hindcast_realized gas + per-solve-year weather), base 2021 / vintage 2020,
window 2021-2025, shipped capacity-price posture, D-1 and D-2 ARMED, exit_rate_limits at its
default OFF, hindcast namespace, meta.kind="full_forward".
  Arm A — primary, shipped default: retirement_rule=pipeline   (expected key b99600bceb8cb6b8)
  Arm B — paired control, explicitly labelled: retirement_rule=legacy  (key 5c352508039513da)
RE-VERIFY both keys and the field-by-field asdict diff at YOUR head before solving: the diff
must contain EXACTLY ONE entry (retirement_rule). If it does not, STOP and report — something
landed between FFR-3Q and you. Confirm `env | grep MARKET_SIM` is empty (a MARKET_SIM_DATA_ROOT
outside REPO_ROOT shifts the cache key for a reason that is not a config difference — FFR-3F
§5). Arm B is the ONE place Addendum D's HOLD-PROMOTION permits unarming D-1: an explicitly
labelled control. Do not unarm anything anywhere else.

=== THE PRE-REGISTERED READS (FFR-3Q §2.1, verbatim in force) ===
1. PRIMARY: `pipeline_events` per year. The whole point of the re-cut is that the retirement
   layer becomes observable. Both prior probes returned ZERO events in every arm, which is why
   both were uninformative. If this window ALSO returns zero, THAT IS THE HEADLINE FINDING and
   I6/I7/I12 are reported as invariant-BY-VACANCY, never as a pass.
2. The mechanical prediction behind G.5(a): L_coal=3 means only a 2021 or 2022 screen decision
   can execute in-window (2024/2025). The re-cut succeeds or fails on whether those two screens
   produce candidates. Report the candidate count per screen year explicitly.
3. I12 is MEASURED here, not attributed — FFR-3N owns the attribution (it concluded storage
   accreditation, not the retirement rule; read it). Report only whether the longer window
   moves it, and note its WARN previously had INVERTED sign (over-retiring -> retiring nothing).
4. The exit-throughput cap is OBSERVED, not armed. exit_rate_limits stays default-OFF.
   _apply_exit_throughput_cap only fires when a year's `due` set is non-empty, so the
   reportable precondition is whether `due` is EVER non-empty. It has never bound in any full
   solve in either test ISO — a measured null, not an untested mechanism.

=== HOW TO READ THE RESULT (Addendum G.2 — three binds) ===
(a) The earlier FH-1 green was NOT the fix's: a paired pre-fix control returned it identically.
(b) I12's WARN had inverted sign. (c) Zero pipeline_events means the retirement layer was
UNTESTED, not validated. A green on a posture that cannot exercise the mechanism is not a pass.
Say which of these your result is, and do not round a vacancy up to a pass.

=== SEQUENCING ===
FFR-3T (owner decision D-10) flips `forecast_xyear_warmstart` to False, and that field is an
INCLUDED cache-key field, so it shifts every forecast cache key. PIN YOUR HEAD for the duration
of your solves, RECORD the warm-start value both arms actually ran with, and do not rebase
mid-flight. Your A/B pairing is internal, so a flip landing after you is not a threat to it —
an unrecorded flip landing DURING it is.

=== TRAPS ===
Push 413 has two causes: a stale tracking ref of a deleted merged branch (`git remote prune
origin`), or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase, measured 647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never fall back to push_files
for a >=300-line file — it takes content as a string, the exact full-file rewrite rule 27
forbids. The documented cache-purge command deletes TRACKED files (410 committed artifacts
once); `git status --short` after any purge. Shell cwd persists between Bash calls. Evolution
ledgers live at <out-dir>/<ISO>/<cache_key>/, NOT the out-dir root, and load_ledgers_for_run
returns {} rather than raising — a wrong path silently reads as "no evolution happened".
A REQUEST-side cache_key() is NOT the key a run is recorded under (FFR-3A-2 §1.2).

=== DELIVERABLE ===
Register both arms to frontend/data/hindcast/ with meta.kind="full_forward" (NEVER the backcast
registry). Fill FFR-3Q's §0 headline, §2.2 Result and §4 by APPENDING an addendum to
docs/handoffs/ffr-3q-window-recut-2026-08-04.md — do not rewrite that file. Rule 28: stamp the
mechanism-matrix cell + citation in THIS session, rejections included. State explicitly that
the FH-4/FH-5 lift is the manager's call and that you are not making it.
```

### FFR-3S [OPUS] — implement D-9(ii), COD-shifted additions scoring

```
[OPUS] FFR-3S — Implement owner decision D-9(ii): score capacity ADDITIONS against the year
the model DECIDED to build, not the year the unit commissions. Signed 2026-08-04, sitting
Addendum K.2. This is an INSTRUMENT change and it lands BEFORE the next battery scores
anything — never as a retrofit to an already-scored bundle.

=== VERIFIED STATE (2026-08-04 @ origin/main 145e4c5f — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT 2026-08-03-ercot158-
pool-arm · PJM 2026-08-03-pjm-151-seam-envelope · CAISO 2026-08-04-caiso164-zonal-loss-surface
· NYISO 2026-08-04-nyiso-120-c119-scope · NEISO 2026-08-03-neiso-caiso156-meter-screen ·
MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast
out-of-training only; it does not block forecast-mode or in-sample work). Cache epochs
2026-08-02 + 2026-08-03b. PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — no Python env
ships in the container; skipping it makes regenerate_clean.py report "50/50 datatype(s)
failed", which is not a data problem), THEN scripts/regenerate_clean.py (~65 min) ONLY if you
need a smoke leg. Rule 12 is PER PROMPT (Addendum F.2). Rule 27: Opus/Fable only for
scripts/score_*; never a full-file rewrite from response content.

=== THE DEFECT, AND WHY THE OWNER CHOSE THIS REMEDY ===
`evolve_fleet` books an entry decision at year Y into `entry_pipeline` with
cod_year = Y + ENTRY_COD_LAG_YEARS[tech] (= Y+2 for wind/solar/gas_cc/gas_ct).
`score_capacity_hindcast.model_additions` reads additions by the ledger year they COMMISSION
in. In the 2021-2025 T1-H window that means the 2024 and 2025 decision cohorts commission in
2026/2027 and are NEVER SCORED — half the solved decision years are invisible.
The censoring is PERMANENT and no window length removes it: forward requires scoring 2026
(a locked-test year; `final` EMPTY; freeze ACTIVE) and 2027 (no actuals), and _validate_window
hard-caps a non-crossover window at end<=2025; backward hits the 2021 demand floor and 2020's
validation tier. Read FFR-3Q §3.2 for the full argument — do NOT re-derive it, and do NOT
attempt to widen any window. This is a SCORER change and touches no out-of-training year.

=== SCOPE ===
1. Score an addition against its DECISION year, not its COD year. The decision year is
   recoverable from the entry_pipeline ledger; derive it, do not reconstruct it by subtracting
   a lag constant unless you first verify the ledger records nothing better.
2. Make the basis EXPLICIT and RECORDED in the sidecar — a reader must be able to tell which
   basis a verdict used without reading code. A verdict whose basis is implicit is the
   record-provenance defect class FFR-3R just closed; do not re-open it. Reuse
   scripts/lib/run_record.py (FFR-3R, 0f788c29) rather than adding a parallel channel.
3. Keep the COD basis computable and reported alongside, so the two are comparable within a
   single new sidecar even though old and new sidecars are not comparable to each other.
4. Tests: one that fails under the old basis and passes under the new, on a case where a
   decision cohort falls outside the scored window; and one asserting retirements-side scoring
   is untouched.
5. VERIFY SOLVE-INERTNESS: no cache key moves, no keeper moves. Report
   cache_key(ScenarioConfig()) and the six per-ISO 2023 backcast keys before and after, the
   way FFR-3R did. A keeper that moves under a scorer change is STOP-THE-LINE.

=== THE COST YOU MUST STATE, NOT SOFTEN ===
The owner signed this knowing it: the additions metric now MEANS something different, so
EVERY historical additions verdict is non-comparable to new ones, and THE FF-2D REGRESSION
BASELINE STOPS BEING USABLE FOR ADDITIONS SPECIFICALLY. Retirements-side comparability is
unaffected. Put this on the peer-review §4 standing disclosure list
(docs/forecast-readiness-peer-review-2026-07.md) in this session.
DO NOT retro-edit any committed artifact and DO NOT re-score a committed leg to pick up the
change. Any re-measurement is a future battery's job, run forward on the new basis.
DO NOT tune anything to make a band pass. If MISO's FC-3 additions still fail on the new
basis, that is the finding — MISO is the only registered T1-H leg with an empty retirement-
FAIL set, its model solar build is 0.0 GW against an 18.649 GW actual, and a 2-year COD shift
cannot explain a zero. Report it; do not close it.

=== TRAPS ===
Push 413: `git remote prune origin` (stale ref of a deleted merged branch) or `git fetch
origin main` + rebase (stale origin/main defeats delta compression). FETCH MAIN BEFORE
DIAGNOSING. Never push a >=300-line file via push_files. The documented cache-purge command
deletes TRACKED files; `git status --short` after. `git checkout origin/main -- <path>` STAGES
those files — `git restore --staged` after inspecting another lane's state. Shell cwd persists.

Deliverable: docs/handoffs/ffr-3s-cod-shifted-scoring-<date>.md + the peer-review §4 entry.
Rule 28: stamp the mechanism-matrix cell in this session if you touch a matrix-tracked field.
```

### FFR-3T [OPUS] — implement D-10, warm-start off for forecast bundles

```
[OPUS] FFR-3T — Implement owner decision D-10: set forecast_xyear_warmstart=False for forecast
bundles. Signed 2026-08-04, sitting Addendum K.3, on FFR-3M's measured adjudication.

=== VERIFIED STATE (2026-08-04 @ origin/main 145e4c5f — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT 2026-08-03-ercot158-
pool-arm · PJM 2026-08-03-pjm-151-seam-envelope · CAISO 2026-08-04-caiso164-zonal-loss-surface
· NYISO 2026-08-04-nyiso-120-c119-scope · NEISO 2026-08-03-neiso-caiso156-meter-screen ·
MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast
out-of-training only). Cache epochs 2026-08-02 + 2026-08-03b. PREREQUISITES IN ORDER:
`uv sync` FIRST (~2 min — no Python env in the container; skipping it makes regenerate_clean.py
report "50/50 datatype(s) failed", which is not a data problem), THEN
scripts/regenerate_clean.py (~63-65 min) if you solve anything. Rule 12 is PER PROMPT
(Addendum F.2): years sequential, <=2 concurrent invocations, <=5 solve-years each, PJM and
MISO never co-run. Rule 27: Opus/Fable only for src/market_sim/ and scripts/run_*.

=== THE DECISION AND ITS EVIDENCE — READ FIRST, DO NOT RE-ADJUDICATE ===
docs/handoffs/ffr-3m-kill-resume-verdict-2026-08-04.md. FF-3E part c = MECHANISM 2, ALTERNATE
OPTIMA, cause confirmed causally by its cell C: the flag warm-starts each year from the prior
year's in-process basis; a resumed run has no basis to inherit, solves that year cold, and
lands on a different vertex of a degenerate optimal face. Cell A's cached years are BIT-
IDENTICAL — the resume plumbing is sound; all divergence is in the first freshly-solved year.
Owner took Option 2. Option 3 (pin a basis) was put with its measured cost and REFUSED: it
would let a solver setting silently select which marginal units retire, because the retirement
screen reads per-unit dispatch volumes (ERCOT: objective relD 8.3e-4, max |D zonal price| 0.19
$/MWh). Do not implement any form of basis pinning, tie-break, or ordering freeze.

=== SCOPE ===
1. Make False the effective value on the FORECAST path. Decide and JUSTIFY IN WRITING whether
   that is a changed ScenarioConfig default or a forecast-path override, and say what it does
   to the backcast path — the owner signed "for forecast bundles", so a change that silently
   also alters backcast solves EXCEEDS the decision and is not yours to make.
2. THIS SHIFTS EVERY FORECAST CACHE KEY. forecast_xyear_warmstart is an INCLUDED cache-key
   field (src/market_sim/config/scenarios.py ~L486-493; the comment there states False "enters
   the key as a distinct scenario"). Confirm that at your HEAD, MEASURE the before/after keys,
   and declare a CACHE EPOCH in the ledger at src/market_sim/results/cache.py with its reason.
   Report the six per-ISO 2023 BACKCAST keys before and after too: if scope 1 is correct they
   are UNCHANGED, and that is the check that proves you did not exceed the decision.
3. Re-run the kill-resume drill (scripts/ff_readiness_battery.py kill-resume, the FFR-3J
   ef5695b0 discriminator) on the shipped config and record the result. FFR-3M measured GREEN
   for this posture in its cell C; reproducing that is confirmation, not a new claim. If it is
   NOT green, STOP and report — that means the cause was not fully identified, and you write
   that up rather than chasing it.
4. A test that pins the forecast-path value, so a future default flip cannot silently revert it.
5. Rule 28: forecast_xyear_warmstart's matrix cell + citation updated in THIS session.

=== SEQUENCING — YOU ARE NOT ALONE ON THIS FILE ===
FFR-3Q-2 is solving a paired ERCOT T1-FF A/B under the OLD default and has been told to pin its
HEAD. Before you push the flip, CHECK for in-flight forecast solve lanes (docs/handoffs/ for
today's date, the PR list open AND closed, and recent origin/main commits — merged branches are
deleted, so `git branch -r` is not an activity signal). If a lane is mid-flight, say so in your
write-up with what you did about it. Absence of a PR is NOT absence of a running session: every
session burns ~65 min on prerequisites before it pushes anything. Report "no evidence yet",
never "not running".

=== WHAT NOT TO DO ===
Do not widen a tolerance, do not disable the drill, do not pin a basis, and do not tune
anything to make a drill pass. The ~2.3x P0 speedup loss is an ACCEPTED cost of the decision,
not a regression to mitigate — if you find yourself designing a way to keep it, you are
re-litigating a signed decision. Measure the horizon-scale cost and report it plainly instead.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN BEFORE
DIAGNOSING. Never push a >=300-line file via push_files (it takes content as a string — the
full-file rewrite rule 27 forbids); scenarios.py is ~9,800 lines, so edit locally and
`git push`, then VERIFY THE PUSHED BLOB (line count + hash vs local) before the next commit.
The documented cache-purge command deletes TRACKED files; `git status --short` after. Shell cwd
persists between Bash calls.

Deliverable: docs/handoffs/ffr-3t-warmstart-off-<date>.md — the scope-1 justification, the
before/after key measurements on BOTH paths, the declared cache epoch, the drill result, and
the measured horizon-scale solve-time cost.
```

### FFR-3K [OPUS] — complete dispatched prompt, header refreshed to `145e4c5f`

Supersedes the Wave-3 section's copy of this prompt (whose VERIFIED STATE header and line
reference are stale). Paste this one.

```
[OPUS] FFR-3K — Fix FC-7 for the T1-H and T1-X tiers. This is the UNFIXED ANALOGUE of a bug
already fixed once, and it must land BEFORE the next battery.

=== VERIFIED STATE (2026-08-04 @ origin/main 145e4c5f — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; NYISO moved 7x in 4 days):
ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-03-pjm-151-seam-envelope ·
CAISO 2026-08-04-caiso164-zonal-loss-surface · NYISO 2026-08-04-nyiso-120-c119-scope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: calibration-complete.json `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY.
HOLDOUT FREEZE ACTIVE (holdout-freeze.json) — out-of-training BACKCAST solve/score/registration
only; it does NOT block forecast-mode 2026+, T1 windows, or in-sample 2023-2025 work.
Cache epochs 2026-08-02 (all forecast) + 2026-08-03b (NYISO-forecast-scoped).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly
like a data problem and is not one), THEN scripts/regenerate_clean.py (~63-65 min, 50
datatypes, 1.6 GB) — ONLY if you need a smoke leg.
Rule 12 is PER PROMPT (sitting Addendum F.2): years sequential within an invocation, <=2
concurrent invocations, <=5 solve-years each, PJM and MISO never co-run. Rule 27:
scripts/run_* is Opus/Fable only, and never a full-file rewrite from response content.

=== THE BUG ===
`run_capacity_hindcast.py` writes `run_config.yaml`; FC-7 row 1 requires `run_config.json`.
FC-7 therefore fails on EVERY T1-H and T1-X leg BY CONSTRUCTION and carries no information
about leg quality. The defect is at **L1419** at this HEAD:
    config.to_yaml_full(args.out_dir / "run_config.yaml")
(FFR-3Q §3.5 cites L1303 — the line moved, the defect did not. Re-locate it yourself.)
This is the exact defect FFR-3D fixed at `34c2f25` — but ONLY in `run_full_horizon.py`. READ
THAT COMMIT and REUSE its writer rather than writing a second implementation. `ea7cd5d` fixed
a crash in that repair; confirm you are past it and inherit the fix. FFR-3R (`0f788c29`) has
since landed `scripts/lib/run_record.py`, which DECLARES a record's config-describing block
and BUILDS it from the solved config — build on that, not around it.

=== WHY IT MUST LAND FIRST ===
FFR-3A-2 deliberately did not fix it: authoring the artifact after seeing the score is what
rubric §4 forbids. The same logic binds you in reverse — this lands as an INSTRUMENT change
BEFORE the next battery scores anything, never as a retrofit. Do NOT hand-author a
run_config.json into any already-scored bundle, and do NOT re-score a committed leg to pick up
the fix. FFR-3S (owner decision D-9(ii)) is the other instrument lane landing before the next
battery; you are independent of it.

=== SCOPE ===
1. Emit run_config.json from run_capacity_hindcast via the same writer run_full_horizon uses.
   Keep the .yaml if anything reads it — CHECK before deleting.
2. A test that would have caught this: assert the artifact FC-7 reads exists after a minimal
   hindcast run. One per tier if the paths differ.
3. Verify no keeper moves and no cache key moves — artifact emission must be SOLVE-INERT.
   Report cache_key(ScenarioConfig()) and the six per-ISO 2023 backcast keys before and after,
   the way FFR-3R did. A keeper that moves under it is STOP-THE-LINE.
4. Check whether any OTHER runner has the same gap. Two instances of one defect was a
   coincidence; FFR-3R found a fifth instance of the sibling class, so a third here would be a
   pattern and finding it is cheap.
5. State plainly that EVERY committed T1-H/T1-X FC-7 verdict predating your fix is an
   INSTRUMENT ARTIFACT, not a leg-quality signal. Do not retro-edit those artifacts.

=== TRAPS ===
Push 413 has two causes: a stale tracking ref of a deleted merged branch (`git remote prune
origin`), or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase, measured 647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never fall back to push_files
for a >=300-line file — it takes content as a string, the exact full-file rewrite rule 27
forbids; run_capacity_hindcast.py is well past that, so edit locally, `git push`, then VERIFY
THE PUSHED BLOB (line count + hash vs local) before the next commit. The documented cache-purge
command deletes TRACKED files (410 committed artifacts once); `git status --short` after any
purge. `git checkout origin/main -- <path>` STAGES those files — `git restore --staged` after.
Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-3k-fc7-hindcast-<date>.md. Small lane; do not expand it.
Rule 28: stamp any mechanism-matrix cell you touch in THIS session.
```

---

## §0g — FFR-3Q-2 STRUCK; FFR-3U dispatched (2026-08-04 @ `8b920ed6`)

Read after §0f, which it corrects. Decision record: sitting **Addendum L**.

### ~~FFR-3Q-2~~ — **RETRACTED. DO NOT RUN THE §0f BLOCK.**

It instructs the base-2021 T1-FF window, which **solves 2022** — a validation-tier holdout year
under an active freeze (Addendum L.1; `4724fa83`). The retraction reason is a manager error
recorded at L.3: §0f's prompt asserted FFR-3Q Task 0's "VERIFIED by execution" and told the
session **not to re-derive it**, when that determination had certified `_validate_window` (the
guard) and not `runner.is_bridge` (what actually decides which years are solved). The
pre-registration in FFR-3Q §2.1 survives and is reused verbatim **after FFR-3U lands**.

### Unchanged and runnable now: **FFR-3K** (§0f, FABLE) · **FFR-3S** (§0f, OPUS) · **FFR-3T** (§0f, OPUS)

FFR-3T's §0f hold is **RELEASED** — it existed only because FFR-3Q-2 was to be solving on the
old cache key. With 3Q-2 struck, no forecast solve lane is in flight; landing D-10 now means
FFR-3U's eventual re-probe runs on the settled posture. Its prompt's SEQUENCING section still
applies as an in-flight check; there is simply nothing to wait for.

### FFR-3U [OPUS] — fix the bridge/un-bridge seam, and discharge D-11's conditions

```
[OPUS] FFR-3U — Fix the harness seam that let a base-2021 T1-FF window SOLVE a validation-tier
holdout year, and discharge the three conditions owner decision D-11 attached to the no-spend
determination. This lane BLOCKS G.5(a)'s gate re-cut and therefore FH-4/FH-5.

=== VERIFIED STATE (2026-08-04 @ origin/main 8b920ed6 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; NYISO moved 7x in 4 days):
ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-03-pjm-151-seam-envelope ·
CAISO 2026-08-04-caiso164-zonal-loss-surface · NYISO 2026-08-04-nyiso-120-c119-scope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: calibration-complete.json `complete` = {NEISO, NYISO, PJM} — ERCOT IS NOT IN IT;
`final` = EMPTY. HOLDOUT FREEZE ACTIVE (holdout-freeze.json) and it outranks both blocks.
Cache epochs 2026-08-02 (all forecast) + 2026-08-03b (NYISO-forecast-scoped).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly
like a data problem and is not one), THEN scripts/regenerate_clean.py (~63-65 min) ONLY if you
need a smoke leg. Rule 12 is PER PROMPT (Addendum F.2). Rule 27: src/market_sim/ and
scripts/run_* are Opus/Fable only, and never a full-file rewrite from response content.

=== READ FIRST ===
docs/handoffs/ffr-3q-window-recut-2026-08-04.md §2.2, §2.2.1 (root cause), §2.2.4 (successor
items), and sitting Addendum L (docs/handoffs/ffr-owner-sitting-2026-08-02.md). Do not
re-derive the diagnosis; it is measured and correct. YOUR JOB IS THE FIX, THE TEST, THE PURGE
AND THE AUDIT — not the re-probe, which is a later lane on your output.

=== THE DEFECT (measured, do not re-litigate) ===
Two predicates disagree about what a "forward year" is.
  runner.py:  is_bridge = (config.hindcast and year in HINDCAST_BRIDGE_YEARS
                           and not config.is_crossover_forward_year(year))
T1-FF sets crossover_forward_year = base_year. At base 2021 EVERY year >= 2021 is a "crossover
forward year", so 2022 is un-bridged and SOLVED — and 2026, a LOCKED-TEST year, would be too if
a window reached it. Meanwhile _validate_window computes its solve-year set from the --crossover
flag (False for T1-FF), so it dropped 2022 as a bridge and NEVER POLICY-CHECKED IT: the
fail-closed check never saw the year because the guard deleted it first. The un-bridging clause
is CORRECT for a genuine T1-X crossover (forward years 2026/2027, forecast mode, no measured
actuals) — do not delete it, scope it.

=== SCOPE ===
1. FIX THE SEAM. Scope the un-bridging clause to genuine crossover forward years
   (crossover=True AND year >= 2026), not to any year above crossover_forward_year. Close BOTH
   exposures — 2022 and 2026.
2. ONE DEFINITION, NOT TWO. _validate_window must policy-check every year the runner will
   ACTUALLY solve, sharing a single predicate with the runner rather than computing its own set
   from a different flag. This is rule 19 [R-ONE-MECH] applied to the guard itself; two
   mechanisms deciding one question is what produced the breach.
3. TESTS THAT WOULD HAVE CAUGHT IT: (a) at base 2021, assert is_bridge(2022) is True and that
   realized solved_years EXCLUDES 2022; (b) the class-level test — a PARITY assertion between
   _validate_window's solve set and the runner's realized solved_years, which catches this whole
   family rather than this instance; (c) the 2026 analogue.
4. THE BANNER MUST NOT BE ABLE TO LIE. The harness printed "bridges [2022, 2026] are never
   solved or read" and then broke it — a false assurance from the same script is the most
   dangerous property here. Either derive the banner from the same predicate the runner uses, or
   assert at completion that realized solved_years matches what the banner promised and FAIL
   LOUDLY if not. A governance banner that is not mechanically tied to behaviour is decoration.
5. DISCHARGE D-11's THREE CONDITIONS (owner, Addendum L.2 — the no-spend determination is
   CONDITIONAL on these, and reverts to "ERCOT 2022 is SPENT" if any cannot be met):
   a. DELETE the two quarantined FFR-3Q bundles, not merely flag them.
   b. INVALIDATE cache keys b99600bceb8cb6b8 (arm A) and 5c352508039513da (arm B). Without
      this a later run with the same config silently CACHE-HITS the contaminated 2022 solve and
      inherits the breach with no banner at all. THIS IS THE CONDITION THAT PROTECTS THE TIER —
      if you can do only one thing in this lane, do this one, and say how you verified it.
   c. DISCLOSE the incident on the peer-review §4 standing disclosure list
      (docs/forecast-readiness-peer-review-2026-07.md), not buried in a lane doc.
   Report explicitly, per condition, whether it is discharged. If one cannot be, SAY SO — the
   determination flips, and that is the owner's to absorb, not yours to paper over.
6. AUDIT THE EXPOSURE. FFR-3Q §2.2.4 item 4 flags this as reasoned-not-audited: no prior T1-FF
   window contains a bridge year (all were base 2023 / 2023-2025), so exposure LOOKS nil — but
   that is reasoning from a window list. CONFIRM it against the committed sidecars: check every
   registered leg's solved_years for a bridge year. State it as an audit result, not an
   expectation. If ANY committed artifact solved 2022 or 2026, that is a second STOP-THE-LINE
   and you report it rather than fixing it.

=== WHAT YOU DO NOT DO ===
Do NOT re-run the FH-1 §3.3 gate. Do NOT solve any T1-FF window. Do NOT lift FH-4/FH-5 — that
is a MANAGER box (Addendum I.1) and reporting green does not open it. Do NOT touch
holdout_policy.py's tier sets, markers, or holdout-freeze.json. Do NOT widen a window to make
anything legal. Your fix must make the ILLEGAL WINDOW FAIL CLOSED, never make the illegal solve
permitted. If your change causes a previously-passing legal window to fail, that is a finding to
report, not a threshold to relax.

=== VERIFY SOLVE-INERTNESS ON THE LEGAL PATH ===
Report cache_key(ScenarioConfig()) and the six per-ISO 2023 backcast keys before and after. A
guard fix must not move a key or a keeper; if one moves, STOP-THE-LINE and report. Also confirm
the legal postures still validate: _validate_window(2023, 2025, crossover=False,
forward_from_base=True) and the plain T1-H window (2021-2025, 2022 bridged) must both still pass,
and the T1-H realized solved_years must remain [2021, 2023, 2024, 2025].

=== TRAPS ===
Push 413 has two causes: a stale tracking ref of a deleted merged branch (`git remote prune
origin`), or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase, measured 647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never fall back to push_files
for a >=300-line file — it takes content as a string, the exact full-file rewrite rule 27
forbids; edit locally, `git push`, then VERIFY THE PUSHED BLOB (line count + hash vs local).
THE DOCUMENTED CACHE-PURGE COMMAND DELETES TRACKED FILES — it removed 410 committed evidence
artifacts once, and you are running a purge on purpose, so this trap is aimed straight at you:
`git status --short` immediately after, and `git checkout --` anything tracked that vanished.
`git checkout origin/main -- <path>` STAGES those files; `git restore --staged` after. Shell cwd
persists between Bash calls.

=== DELIVERABLE ===
docs/handoffs/ffr-3u-bridge-seam-<date>.md: the fix and why it is scoped rather than deleted;
the parity test and what class it closes; the banner remedy; a per-condition discharge statement
for D-11 a/b/c with HOW each was verified; the exposure audit as a result; and the before/after
key measurements. Rule 28: stamp any mechanism-matrix cell you touch in THIS session. State
plainly that the gate re-cut is a LATER lane and that FH-4/FH-5 remains a manager box.
```

---

## §0h — Wave-3 status refresh and three new lanes (2026-08-04 @ `bf43122e`)

Read after §0g. Decision record: sitting **Addendum M**.

**Status corrections to §0f/§0g:** **FFR-3K LANDED** (PR #3502) — its "never dispatched" status
line in §0f and sitting K.4 is retired. **FFR-3S LANDED** (#3501). **FFR-3T LANDED** (#3498/#3504).
**FFR-3U has NEVER STARTED** — no branch, no doc, seam open at `runner.py:927`, and D-11's
conditions are undischarged. **~~FFR-3Q-2~~ remains STRUCK** (§0g).

**Rule 25 notice for FFR-3V and FFR-3W:** they investigate the same *shape* of defect in two
markets. They are **two lanes**. Neither imports the other's verdict, parameters or diagnosis,
and neither may cite the other as evidence. If run concurrently they must not share a session.

### FFR-3V [OPUS] — MISO's entry screen decided ZERO solar for three straight cohorts

```
[OPUS] FFR-3V — Find out why MISO's entry screen builds NO solar in an ISO that added 18.6 GW
of it. This is a DIAGNOSIS lane. You are not permitted to close the residual by tuning.

=== VERIFIED STATE (2026-08-04 @ origin/main bf43122e — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; NYISO moved 7x in 4 days):
ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-03-pjm-151-seam-envelope ·
CAISO 2026-08-04-caiso164-zonal-loss-surface · NYISO 2026-08-04-nyiso-120-c119-scope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: calibration-complete.json `complete` = {NEISO, NYISO, PJM} — MISO IS NOT IN IT;
`final` = EMPTY. HOLDOUT FREEZE ACTIVE — out-of-training BACKCAST solve/score/registration only;
it does NOT block forecast-mode 2026+, T1 windows, or in-sample 2023-2025 work.
Cache epochs 2026-08-02, 2026-08-03b, and NEW 2026-08-04 (D-10 warm-start OFF for forecast
bundles — EVERY FORECAST KEY MOVED; see src/market_sim/results/cache.py). Forecast work solves
COLD and results/ is gitignored, so "expect cache hits" is never a valid budget.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly
like a data problem and is not one), THEN scripts/regenerate_clean.py (~63-65 min, 50 datatypes,
1.6 GB). Rule 12 is PER PROMPT (Addendum F.2): years sequential within an invocation, <=2
concurrent invocations, <=5 solve-years each, and MISO is ~8.6 GB per solve — NEVER co-run it
with PJM in one session. Rule 27: Opus/Fable only for src/market_sim/ and scripts/run_*.

=== THE FINDING YOU ARE INHERITING (measured; do not re-derive) ===
docs/handoffs/ffr-3s-cod-shifted-scoring-2026-08-04.md §6. MISO's registered T1-H leg
`miso-2021-2025-realized-ffr3a3` (entry_commissioning_lag: true) fails FC-3 additions on ALL
FIVE techs; solar is model 0.0 GW vs actual 18.649 GW (-100%). It is also the ONLY registered
T1-H leg of any ISO with an EMPTY retirement-FAIL set — its retirement half passes cleanly.
FFR-3S PROVED the new decision-year basis cannot explain it: with a 2-year COD lag and a 2021
window start, the 2021/2022/2023 decision cohorts commission in 2023/2024/2025 — INSIDE the
window, already visible under the OLD COD basis. The COD-basis solar total is 0.0 GW, so those
three cohorts decided ZERO solar. Only 2024/2025 were censored. A 2-year shift cannot explain
a zero. THIS IS AN ENTRY-SCREEN ROOT CAUSE, NOT A SCORING ARTIFACT — that is established, and
re-arguing it is not your lane.

=== YOUR QUESTION ===
Why does the entry screen decide zero solar in MISO for three consecutive decision years?
Work the screen, not the score. Candidate directions, none privileged — enumerate and TEST,
do not pick the first plausible one:
  - the screen's solar revenue side (energy value at MISO's solar-hour prices; whether RA /
    capacity value is credited, and at what accreditation);
  - its cost side (capex vintage, IRA/ITC treatment, financing assumptions);
  - eligibility/gating — is solar reaching the screen at all, or filtered before it
    (queue/interconnection representation, resource availability, a zero build cap, a share cap
    such as STORAGE_TECH_BUILD_SHARE_CAP's analogue);
  - the D-2 dampers (entry_rate_limits / entry_commissioning_lag) suppressing it — note
    Addendum D's HOLD PROMOTION: you may measure them in an EXPLICITLY LABELLED paired control,
    and you may NOT unarm them anywhere else or recommend a revert;
  - whether MISO's planned-additions channel (EIA-860 proposed pipeline, step 4) is delivering
    solar that the ECONOMIC screen (step 5) then never adds to.
Instrument the screen directly — dump the per-technology screen inputs and the pass/fail margin
per decision year. A margin of "-$X/MW-yr in every year" is a finding; "solar never entered the
candidate set" is a DIFFERENT finding. Distinguish them explicitly; they have different fixes.

=== RULES THAT BIND THIS LANE HARDEST ===
Rule 1 [R-STRUCT] and rule 11: DO NOT tune a parameter to make solar build. A residual closable
only by an unidentified value is an OPEN BLOCKER you write up, not a knob you turn. If you find
the screen is right and the INPUT is wrong (a capex, a CF, an accreditation), rule 14
[R-ACCURATE] says use the accurate value and open the root cause — and if the fit gets worse,
that is a discovered bug, not a reason to revert.
Rule 25 [R-ISO-SCOPE]: CAISO has a structurally similar finding under FFR-3W. DO NOT read it as
evidence, do not import its parameters, do not cite it. Derive MISO's answer from MISO's data.
Rule 28: stamp any mechanism-matrix cell you test in THIS session, rejections included.

=== SCOPE DISCIPLINE ===
Diagnose and write up. Do NOT promote a keeper, do NOT flip a default, do NOT widen a band.
If the fix is obvious and small, PROPOSE it with its evidence and let the owner charter it —
a diagnosis lane that also lands the fix has no independent check on the fix.
If you need a solve: MISO, in-sample years only (2023-2025 backcast, or forecast-mode 2026+),
<=5 solve-years, sequential, and NEVER 2022/2019/2020/2026-backcast — MISO holds no marker and
the freeze is ACTIVE. If your question genuinely requires an out-of-training year, STOP and
escalate; that is exactly the breach Addendum L records.

=== TRAPS ===
Push 413 has two causes: a stale tracking ref of a deleted merged branch (`git remote prune
origin`), or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase). FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files. The
documented cache-purge command deletes TRACKED files; `git status --short` after. Evolution
ledgers live at <out-dir>/<ISO>/<cache_key>/, NOT the out-dir root, and load_ledgers_for_run
returns {} rather than raising — a wrong path silently reads as "no evolution happened", which
in THIS lane would look exactly like your finding. Verify the path before believing a zero.
A REQUEST-side cache_key() is NOT the key a run is recorded under (FFR-3A-2 §1.2).
MARKET_SIM_DATA_ROOT outside REPO_ROOT SHIFTS the cache key (FFR-3F §5) — check `env | grep
MARKET_SIM` is empty. Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-3v-miso-entry-screen-<date>.md — the instrumented screen dump,
the candidate directions you tested and eliminated, the distinguished finding (margin vs
candidate-set), and what you did NOT separate.
```

### FFR-3W [OPUS] — CAISO's entry screen prices a gas_ct $40k/MW-yr underwater, every year

```
[OPUS] FFR-3W — Diagnose why CAISO's entry screen finds a gas_ct unprofitable by ~$40,000/MW-yr
in every year of every arm, and what that does to FC-2 row 4. DIAGNOSIS lane; no tuning.

=== VERIFIED STATE (2026-08-04 @ origin/main bf43122e — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT 2026-08-03-ercot158-
pool-arm · PJM 2026-08-03-pjm-151-seam-envelope · CAISO 2026-08-04-caiso164-zonal-loss-surface
· NYISO 2026-08-04-nyiso-120-c119-scope · NEISO 2026-08-03-neiso-caiso156-meter-screen ·
MISO 2026-08-04-miso-124-dualfuel-rearm.
Markers: `complete` = {NEISO, NYISO, PJM} — CAISO IS NOT IN IT; `final` = EMPTY. HOLDOUT FREEZE
ACTIVE (out-of-training BACKCAST only; forecast-mode 2026+ and in-sample 2023-2025 unrestricted).
Cache epochs 2026-08-02, 2026-08-03b, and NEW 2026-08-04 (D-10 warm-start OFF for forecast
bundles — EVERY FORECAST KEY MOVED; src/market_sim/results/cache.py). Forecast solves COLD.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — no Python env ships in the container;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which is NOT a data
problem), THEN scripts/regenerate_clean.py (~63-65 min). Rule 12 is PER PROMPT (Addendum F.2):
years sequential, <=2 concurrent invocations, <=5 solve-years each. Rule 27: Opus/Fable only.

=== THE FINDING YOU ARE INHERITING (measured; do not re-derive) ===
FFR-3H cause 2: a CAISO gas_ct is unprofitable in the entry screen in EVERY YEAR OF EVERY ARM
by $39,974-45,316/MW-yr. Diagnosed and unowned since sitting Addendum J. Related, and read
before you start:
  - FFR-3P (docs/handoffs/ffr-3p-caiso-accreditation-*.md): arming the IDENTIFIED VRE
    accreditation moved FC-2 row 4 from 65.48% to 63.23% — still FAIL — with ZERO invariant
    flips, and retirements / renewable builds / storage builds / CO2 identical to the digit.
    Its non-obvious result: 2027-2029 do not move by a megawatt because the backstop is
    RATE-limited there, not need-limited, so the entire -1,312 MW lands in 2030. FFR-3P ALSO
    RETRACTED TWO OF ITS OWN CLAIMS (a "+1,735.8 MW thermal under-credit" and a "+1,681 MW hydro
    under-credit"): CAISO's published fleet thermal credit is 0.9537 vs the model's 0.9457, so
    the model is 0.8% ABOVE, and published fleet hydro is 0.6936 vs the model's 0.7041, already
    1.1pp generous. Both errors came from inferring a partition where the ISO publishes the
    whole class's realized ratio. DO NOT REINSTATE EITHER CLAIM.
  - The CAISO keeper enables capacity_deliverability_limits (caiso-51 lineage); in a backcast
    only the measured-seam-import half fires (MIC -> WECC_import). The RA-saturation half is
    UNVALIDATED in any keeper. If your diagnosis touches it, say which half.

=== YOUR QUESTION ===
Is the $40k/MW-yr gap a REAL market signal or a screen defect? CAISO is a market where new
gas_ct genuinely is hard to justify, so "unprofitable" may be CORRECT — in which case the
finding is that FC-2 row 4's failure is NOT caused by the gas_ct screen and the real cause is
elsewhere, and saying so is a complete and valuable result.
Decompose the $40k. Per year, per arm, report the screen's revenue stack against its cost
stack: energy margin, RESERVE/AS value (screen_reserve_value_enabled and which pricing path
fired), CAPACITY value (does CAISO's RA payment reach this unit, and does
capacity_deliverability_limits' RA-saturation half zero it?), against FOM + capex + financing.
A gap that is 90% one term is a different finding from one spread evenly. Then answer whether
FC-2 row 4 moves at all if the gas_ct term were corrected — bound it from committed artifacts
first, and only solve if the bound is not decisive.

=== RULES THAT BIND THIS LANE HARDEST ===
Rule 1 [R-STRUCT] / rule 11: no adder, no haircut, no value tuned to close the 63.23% residual.
Rule 14 [R-ACCURATE]: if an input is an estimate where CAISO publishes the real number, use the
real one even if the fit worsens, and open the root cause. FFR-3P's retraction is the standing
warning here: prefer the ISO's PUBLISHED whole-class realized ratio over any partition you
infer, and if you find yourself deriving a component the ISO publishes in aggregate, stop.
Rule 25 [R-ISO-SCOPE]: MISO has a structurally similar entry-screen finding under FFR-3V. DO NOT
read it, cite it, or import its parameters. CAISO's answer comes from CAISO's data.
Rule 19 [R-ONE-MECH]: before proposing anything, enumerate what ALREADY prices this unit's
capacity and reserve value; replace or reconcile, never stack.
Rule 28: stamp any matrix cell you test in THIS session, rejections included.

=== SCOPE DISCIPLINE ===
Diagnose and write up. Do NOT promote, do NOT flip a default, do NOT widen a band. Propose a
fix with evidence and let the owner charter it. In-sample or forecast-mode years only; CAISO
holds no marker and the freeze is ACTIVE — an out-of-training year is the Addendum L breach.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST.
Never push a >=300-line file via push_files. The documented cache-purge command deletes TRACKED
files; `git status --short` after. Evolution ledgers live at <out-dir>/<ISO>/<cache_key>/, and
load_ledgers_for_run returns {} rather than raising — a wrong path reads as "no evolution
happened". MARKET_SIM_DATA_ROOT outside REPO_ROOT shifts the cache key (FFR-3F §5). Shell cwd
persists between Bash calls.

Deliverable: docs/handoffs/ffr-3w-caiso-entry-screen-<date>.md — the per-term decomposition of
the $40k, the real-signal-vs-defect determination, the bound on FC-2 row 4, and what you did
NOT separate.
```

### FFR-3X [FABLE] — stop the FF-2D helper from overwriting a producer artifact

```
[FABLE] FFR-3X — Add the refuse-if-exists guard FFR-3K identified, and close FFR-3R §6.1.
Small lane. Do not expand it.

=== VERIFIED STATE (2026-08-04 @ origin/main bf43122e — RE-VERIFY AT YOUR OWN HEAD) ===
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE. Cache epochs
2026-08-02, 2026-08-03b, 2026-08-04 (D-10). PREREQUISITE: `uv sync` FIRST (~2 min — the
container ships NO Python environment). You should not need regenerate_clean.py; if you think
you do, you have over-scoped. Rule 27: Opus/Fable only for scripts/ — never a full-file rewrite
from response content.

=== THE DEFECT (FFR-3K §6, measured) ===
FFR-3K made the capacity-hindcast and full-horizon harnesses write their own `run_config.json`
from the SOLVED config. `scripts/_ff2d_emit_run_config.py` is now a HISTORICAL-bundle helper —
but run on a post-fix bundle it will SILENTLY OVERWRITE the producer-written artifact with a
`meta.json`-reconstructed one. That is a provenance DOWNGRADE and it is exactly the defect class
FFR-3R closed structurally (scripts/lib/run_record.py, 0f788c29): a record field sourced from
something other than the config the solve actually ran on.

=== SCOPE ===
1. REFUSE IF EXISTS. The helper must not overwrite a producer-written run_config.json. Fail
   loudly with a message naming the bundle and saying why, rather than skipping quietly — a
   silent skip and a silent overwrite are both invisible, and only one of them is safe.
   Provide an explicit override flag ONLY if you can name a real use for it; if you cannot,
   do not add one.
2. Close FFR-3R §6.1: the helper's HINDCAST arm still reads `meta.json` rather than the
   producer artifact. Read FFR-3R §6.1 for what it says is open and fix that arm's source.
3. A test that fails without the guard: run the helper against a bundle that already has a
   producer-written run_config.json and assert the file is unchanged (compare hash) and the
   helper errored.
4. Solve-inert by construction, but PROVE it: report cache_key(ScenarioConfig()) before and
   after. This touches no ScenarioConfig field, so rule 28 needs no matrix cell — say so
   explicitly rather than leaving it unstated.

=== WHAT NOT TO DO ===
Do NOT retro-edit any committed bundle. Do NOT re-run the helper across historical bundles to
"normalize" them — that is the overwrite you are preventing, applied at scale. Do NOT rewrite
run_record.py; build on it.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST.
Never push a >=300-line file via push_files. The documented cache-purge command deletes TRACKED
files; `git status --short` after. Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-3x-emit-guard-<date>.md. Keep it short.
```

---

## §0i — WAVE 4: the five lanes chartered by the signed N-cards (2026-08-04 @ `49aac023`)

Decision record: sitting **Addendum O**. Wave 3 is closed (Addendum N.1); do not re-dispatch any
FFR-3x lane. **~~FFR-3Q-2~~ remains STRUCK** (§0g) — FFR-3Q-3 below replaces it on the FIXED seam.

**Concurrency:** all five may run as independent sessions (rule 12 is per prompt, Addendum F.2).
**One coupling:** FFR-4B and FFR-4C both touch entry-screen revenue in MISO — 4B raises solar,
4C lowers wind. Each carries its OWN paired control at its OWN base commit; whichever lands
second re-verifies against the new base and re-checks its matrix cell survived (miso-124 lost a
matrix merge race).

### FFR-4A [OPUS] — D-14: derive the ladder's K/L relationship from the measured record

```
[OPUS] FFR-4A — Owner decision D-14, signed 2026-08-04 (sitting Addendum O): the entry growth
ladder's K = L knife-edge is CHARTERED AS A DEFECT. Derive the intended relationship between the
ladder multiplier K and the COD lag L from the MEASURED BUILD RECORD. This is a derivation lane.

=== VERIFIED STATE (2026-08-04 @ origin/main 49aac023 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; they move several times a day):
ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-04-pjm-152-collapse ·
CAISO 2026-08-04-caiso-166-measured-dlap · NYISO 2026-08-04-nyiso-120-c119-scope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE — out-of-training
BACKCAST solve/score/registration only; forecast-mode 2026+ and in-sample 2023-2025 unrestricted.
Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10 warm-start OFF for forecast bundles —
every forecast key moved; src/market_sim/results/cache.py).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly like
a data problem and is NOT one), THEN scripts/regenerate_clean.py (~63-65 min) only if you solve.
Rule 12 is PER PROMPT (Addendum F.2). Rule 27: Opus/Fable only for src/market_sim/.

=== THE FINDING YOU ARE INHERITING (measured; do not re-derive) ===
docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §5. The ladder lets year Y build K x the
prior year's decisions, then nets off decisions already pending. With a COD lag of L years, (L-1)
cohorts are always pending when the screen runs, so remaining = (K - L + 1) x D_prev. At the
shipped K = 2.0 and L = 2 that is exactly 1 x D_prev: the doubling and the netting CANCEL
EXACTLY, and economic entry is pinned at 2x the measured seed forever. The knife-edge is K = L
and the shipped values sit on it. MISO solar's ceiling is 2.473 GW in-window (-86.7% FC-3 band)
even with a perfect revenue side; removing only the lag lifts it to 14.655 GW (-21.4%), at which
point the 6.0 GW per-tech queue cap binds instead.
The corroboration that makes it a defect rather than a curiosity: MISO's gas_ct ladder DOES
double (1,350 -> 2,700 -> 5,241 MW, FFR-2B) — but that channel is the RESERVE-MARGIN BACKSTOP,
which commissions IN-YEAR and so never nets a pending row. The SAME ladder ratchets for the
backstop and freezes for economic entry. That asymmetry is your subject.

=== WHAT YOU ARE AUTHORIZED TO DO, AND WHAT YOU ARE NOT ===
AUTHORIZED: derive, from the MEASURED build record, what relationship between K and L reproduces
observed entry behaviour — i.e. what the ladder is supposed to express. Rule 23
[R-FROZEN-DERIVE] IS THE RULE THAT BINDS THIS LANE HARDEST: a measured-behaviour parameter
re-derives only when its SOURCE DATA updates, never because a residual moved. Your derivation
commit must cite the DATA that identifies the value — an EIA-860 build-record statistic, a
queue-to-COD conversion rate, something external. If your answer is "the value that makes MISO
solar build", you have written the thing this rule forbids.
NOT AUTHORIZED: moving K off 2.0 by taste. The owner's card says so in terms. Nor may you
change L (ENTRY_COD_LAG_YEARS) as a convenience — it is a D-2 field under Addendum D's HOLD
PROMOTION, and it also sets the D-9 censoring window, so a change there has scorer consequences
outside your lane. If your derivation implies L should change, REPORT that as a finding and
escalate; do not land it.

=== SCOPE ===
1. State the ladder's INTENT precisely from the code and its citations: what is the mechanism
   supposed to prevent, and is the netting of pending cohorts part of that intent or an
   independent guard that was added later? Read the history — if the doubling and the netting
   were introduced by different commits for different reasons, that is the finding.
2. Establish whether K = L is REACHABLE for other techs/ISOs or unique to this pairing. Report
   the (K, L) pair per technology and per ISO, and mark which sit on, above or below the
   knife-edge. A defect that binds in one cell is a different problem from one that binds in ten.
3. Derive the intended relationship with its identifying data cited. If the honest answer is
   "the two guards are redundant and one should be removed" (rule 19 [R-ONE-MECH]), say so —
   that is a legitimate outcome and probably the cleanest one.
4. Whatever you propose, PREDICT its effect before measuring it, and record the prediction first.
5. Rule 24 [R-REGISTRY]: any value you land appears in ScenarioConfig/constants.py with its
   citation. Rule 28: matrix cell + citation in THIS session.

=== SCOPE DISCIPLINE ===
This is a DERIVATION lane. Do not promote a keeper, do not register a forecast run, do not tune.
If the derivation lands a value, it lands with a paired control and its prediction on record.
If you cannot identify a value from data, THAT IS THE DELIVERABLE — an open blocker, written up
(rule 11). A residual closable only by an unidentified value is not a parameter.

=== TRAPS ===
Push 413 has two causes: a stale tracking ref of a deleted merged branch (`git remote prune
origin`), or a stale local origin/main defeating delta compression (`git fetch origin main` +
rebase). FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files — it takes
content as a string, the full-file rewrite rule 27 forbids; scenarios.py is ~9,900 lines, so edit
locally, `git push`, then VERIFY THE PUSHED BLOB (line count + hash vs local). The documented
cache-purge command deletes TRACKED files; `git status --short` after. `git checkout origin/main
-- <path>` STAGES those files; `git restore --staged` after. Shell cwd persists between calls.

Deliverable: docs/handoffs/ffr-4a-entry-ladder-<date>.md — the intent reconstruction, the (K, L)
map across techs and ISOs, the derivation with its cited identifying data (or the open blocker),
your recorded prediction, and what you did NOT separate.
```

### FFR-4B [OPUS] — D-12 + D-2′: MISO's solar revenue side, in one lane, D-12 first

```
[OPUS] FFR-4B — Owner decisions D-12 and D-2' , signed 2026-08-04 (sitting Addendum O), taken
together as ONE lane because D-12 SIZES D-2'. Wire MISO's published solar accreditation, THEN arm
entry_vre_capacity_revenue, with a paired control. MISO-scoped only.

=== VERIFIED STATE (2026-08-04 @ origin/main 49aac023 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT ercot158-pool-arm ·
PJM pjm-152-collapse · CAISO caiso-166-measured-dlap · NYISO nyiso-120-c119-scope ·
NEISO neiso-caiso156-meter-screen · MISO 2026-08-04-miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM} — MISO IS NOT IN IT; `final` = EMPTY. HOLDOUT FREEZE
ACTIVE. In-sample 2023-2025 and forecast-mode 2026+ are unrestricted; NEVER 2022/2020/2019/
2026-backcast. Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — no Python env ships in the container; skipping
it makes regenerate_clean.py report "50/50 datatype(s) failed", which is NOT a data problem),
THEN scripts/regenerate_clean.py (~63-65 min). Rule 12 PER PROMPT: years sequential, <=2
concurrent invocations, <=5 solve-years each; MISO is ~8.6 GB per solve — NEVER co-run with PJM
in one session. Rule 27: Opus/Fable only for src/market_sim/.

=== THE EVIDENCE (measured; do not re-derive) ===
docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §§4, 7. MISO solar is a MARGIN finding, not
a candidate-set or damper finding — solar reaches the screen every decision year and is rejected
on economics before any cap is consulted. The internal control: WIND BUILT 4.0 GW in the same
window through the same code path, the same zonal-CF mechanism and the same caps.
D-12: MISO's published solar accreditation is ALREADY INTAKEN AND CITED at elcc/miso/miso.csv and
simply not read into RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]. Unwired the model uses 0.18; the
season-weighted published value is 0.3875. Solar's 2023 break-even: $37.59/MWh at 0.18 vs
$29.41/MWh at 0.3875, against a MISO modelled price level of ~$30-40/MWh.
D-2': entry_vre_capacity_revenue is default-OFF. The payment resolves cleanly today
($79,800 x 0.18 = $14,364/MW-yr) and moves solar's break-even from $41.9-48.9 to $34.8-41.8/MWh.
THE DECISIVE ASYMMETRY: the THERMAL branch already takes the same payment UNGATED at
$75.8k-117.3k/MW-yr. VRE is gated off; thermal is not; both are inside one function.

=== SCOPE, IN THIS ORDER ===
1. D-12 FIRST. Wire the published accreditation from elcc/miso/miso.csv into
   RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]. SETTLE THE SEASONAL->ANNUAL SELECTION RULE IN THIS LANE
   — do not leave it implicit, and cite what the selection rule is grounded in. Rule 14
   [R-ACCURATE]: the accurate value is on disk and cited, so it goes in whatever it does to a fit.
2. MEASURE D-12 ALONE against a paired control before touching D-2'. The two must be separable;
   if you arm both in one step you cannot attribute either.
3. THEN D-2'. Arm entry_vre_capacity_revenue, MISO-SCOPED. Rule 25 [R-ISO-SCOPE]: other ISOs
   with a capacity market in MARKET_DESIGN are SEPARATE per-ISO decisions and are NOT authorized
   here — do not arm them, and do not derive their parameters from MISO's.
4. Report the thermal-vs-VRE asymmetry explicitly: state whether arming VRE makes the function
   symmetric or introduces a new inconsistency somewhere else (rule 19 [R-ONE-MECH] — enumerate
   what already pays VRE capacity value before adding a second channel).
5. Rule 24 [R-REGISTRY]: every value in ScenarioConfig/constants.py with its citation; nothing in
   a per-plant dict or a getattr fallback. Rule 28: entry_vre_capacity_revenue's matrix cell +
   citation updated in THIS session — it is a ScenarioConfig mechanism, so CI enforces the row.

=== WHAT THE OWNER ACCEPTED, SO YOU DO NOT RE-OPEN IT ===
THIS PAIR WILL NOT BUY AN FC-3 PASS ON ITS OWN. If the ladder freeze survives FFR-4A's
derivation, this moves MISO solar from a -100% band to about -86.7%. The decisions were taken on
RULE-14 GROUNDS, NOT ON EXPECTED BAND MOVEMENT, and must not be judged by it. Do not tune
anything to close the remaining gap; the ceiling is FFR-4A's subject, not yours.

=== COORDINATION ===
FFR-4C (D-13, the wind PTC window) is running concurrently and also touches MISO entry-screen
revenue — it LOWERS wind while you RAISE solar. Build your paired control at YOUR base commit; if
4C lands first, re-verify against the new base before quoting any number, and re-check your
matrix cell survived the merge (miso-124 lost a matrix merge race). Say in your write-up which
side of 4C your measurements sit on.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST. Never
push a >=300-line file via push_files; scenarios.py is ~9,900 lines — edit locally, push, then
VERIFY THE PUSHED BLOB. The documented cache-purge command deletes TRACKED files; `git status
--short` after. Evolution ledgers live at <out-dir>/<ISO>/<cache_key>/, NOT the out-dir root, and
load_ledgers_for_run returns {} rather than raising — a wrong path silently reads as "no evolution
happened", which in an entry-screen lane looks exactly like a null result. MARKET_SIM_DATA_ROOT
outside REPO_ROOT shifts the cache key (FFR-3F §5) — check `env | grep MARKET_SIM` is empty.
A REQUEST-side cache_key() is NOT the key a run is recorded under (FFR-3A-2 §1.2). Shell cwd
persists between Bash calls.

Deliverable: docs/handoffs/ffr-4b-miso-solar-revenue-<date>.md — the selection rule and its
grounding, D-12 measured alone, D-2' measured on top, the asymmetry statement, and what you did
NOT separate.
```

### FFR-4C [FABLE] — D-13: window the §45 wind PTC to its statutory 10 years

```
[FABLE] FFR-4C — Owner decision D-13, signed 2026-08-04 (sitting Addendum O): window the section
45 wind PTC to its statutory 10 years. Bounded lane. Zero free parameters.

=== VERIFIED STATE (2026-08-04 @ origin/main 49aac023 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT ercot158-pool-arm ·
PJM pjm-152-collapse · CAISO caiso-166-measured-dlap · NYISO nyiso-120-c119-scope ·
NEISO neiso-caiso156-meter-screen · MISO miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE — in-sample
2023-2025 and forecast-mode 2026+ only. Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — no Python env in the container; skipping it
makes regenerate_clean.py report "50/50 datatype(s) failed", which is NOT a data problem), THEN
scripts/regenerate_clean.py (~63-65 min) if you solve. Rule 12 PER PROMPT. Rule 27: Opus/Fable
only for src/market_sim/ — never a full-file rewrite from response content.

=== THE DEFECT (FFR-3V §6, measured) ===
The section 45 wind PTC is credited over the plant's FULL 30-YEAR BOOK LIFE with no statutory
window. The solar ITC in the same file is booked correctly. The remedy has ZERO FREE PARAMETERS
— one published statutory number, 10 years — and an existing precedent to copy in the same file:
the `_ccs_45q_window_years` pattern (see also ira_45q_credit_window_years in ScenarioConfig).

=== SCOPE ===
1. Window the PTC on the existing pattern. Reuse it; do not invent a second mechanism (rule 19
   [R-ONE-MECH]).
2. Cite the statute for the 10 years in the code comment (rule 5 [R-NO-MAGIC]) and in
   docs/parameter-citations.md.
3. A test asserting the credit stops at year 10 of the plant's life, and one asserting the solar
   ITC path is unchanged.
4. Measure the effect on wind additions in at least one ISO with a paired control, and RECORD
   YOUR PREDICTION BEFORE MEASURING.
5. Rule 24 [R-REGISTRY]: the window length lives in ScenarioConfig/constants.py with its citation.
   Rule 28: matrix cell + citation in THIS session.

=== THE PART THAT GETS MIS-HANDLED — READ TWICE ===
EXPECT WIND ADDITIONS TO FALL. MISO currently builds 4.0 GW against 7.2 GW actual, so this
correction moves a passing-ish number FURTHER FROM the actual. UNDER RULE 1 [R-STRUCT] THAT IS
THE FAITHFUL DIRECTION AND THE FIX STAYS IN. The owner signed it knowing this (Addendum O.2).
If the band worsens, that is a DISCOVERED UNDER-BUILD elsewhere on wind's revenue side — write it
up as an open root cause (rule 11) and hand it on. DO NOT REVERT, do not soften the window, do
not add a compensating adder, and do not delay the commit until something offsets it. A lane that
reverts this because the residual moved has misread the decision.

=== COORDINATION ===
FFR-4B (D-12 + D-2') is running concurrently and also touches MISO entry-screen revenue — it
RAISES solar while you LOWER wind. Build your paired control at YOUR base commit; if 4B lands
first, re-verify against the new base before quoting a number, and re-check your matrix cell
survived the merge (miso-124 lost a matrix merge race). State which side of 4B your measurements
sit on.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST. Never
push a >=300-line file via push_files. The documented cache-purge command deletes TRACKED files;
`git status --short` after. Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-4c-wind-ptc-window-<date>.md. Keep it short. Do not expand scope
into the wider IRA treatment; if you find another credit with the same defect, REPORT it and let
the owner charter it.
```

### FFR-4D [OPUS] — D-15: charter CAISO FC-2 row 4 against the FLEET-VINTAGE cause

```
[OPUS] FFR-4D — Owner decision D-15, signed 2026-08-04 (sitting Addendum O): FC-2 row 4 is
chartered against the FLEET-VINTAGE cause (FFR-3P B-1). The CAISO capacity-anchor correction is
NOT chartered and is NOT your lane — see the refusal below, which is the point of this charter.

=== VERIFIED STATE (2026-08-04 @ origin/main 49aac023 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; CAISO has moved repeatedly):
ERCOT ercot158-pool-arm · PJM pjm-152-collapse · CAISO 2026-08-04-caiso-166-measured-dlap ·
NYISO nyiso-120-c119-scope · NEISO neiso-caiso156-meter-screen · MISO miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM} — CAISO IS NOT IN IT, and caiso-171 has just assessed
the CAISO frontier as "`complete` is NO for now, and the blocker is governance" (read it).
`final` = EMPTY. HOLDOUT FREEZE ACTIVE — in-sample 2023-2025 and forecast-mode 2026+ only.
Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — no Python env ships in the container; skipping
it makes regenerate_clean.py report "50/50 datatype(s) failed", which is NOT a data problem),
THEN scripts/regenerate_clean.py (~63-65 min). Rule 12 PER PROMPT. Rule 27: Opus/Fable only.

=== THE EVIDENCE (measured; do not re-derive) ===
docs/handoffs/ffr-3w-caiso-entry-screen-2026-08-04.md and ffr-3p-caiso-accreditation-*.md.
FC-2 row 4's driver is a base-year CAISO fleet 11,711 MW SHORT of the real CAISO on accredited
capacity (FFR-3P Table 1.1) — 1.78x the 6,577 MW deficit that drives the entire 14,043.6 MW
build. Correcting the fleet alone moves the reserve position 0.8852 -> 1.0896 (11.5% short ->
9.0% long) and collapses row 4's numerator.
Also established, and NOT to be reinstated: FFR-3P RETRACTED its own "+1,735.8 MW thermal
under-credit" and "+1,681 MW hydro under-credit" claims. CAISO's published fleet thermal credit
is 0.9537 vs the model's 0.9457 (the model is 0.8% ABOVE) and published fleet hydro is 0.6936 vs
0.7041 (already 1.1pp generous). Both errors came from INFERRING A PARTITION WHERE THE ISO
PUBLISHES THE WHOLE CLASS'S REALIZED RATIO. That is the standing methodological warning for this
lane: prefer the published whole-class realized ratio; if you find yourself deriving a component
the ISO publishes in aggregate, STOP.

=== YOUR TASK ===
Find and fix the 11,711 MW base-year accredited-capacity shortfall. Work the FLEET, not the
screen. Where is the capacity missing — units absent from the base fleet, units present but
under-accredited, a vintage/as-of misalignment in how the base year is assembled, or a class the
crosswalk drops? Decompose the 11,711 MW by cause with the megawatts attributed, and fix what is
a genuine data or wiring defect under rule 14 [R-ACCURATE].

=== THE REFUSAL THAT IS THE POINT OF THIS CHARTER ===
DO NOT CORRECT THE CAISO CAPACITY-PRICE ANCHOR AS A ROUTE TO ROW 4, and do not quote a row-4
improvement obtained that way. FFR-3W measured that correcting the anchor moves row 4 JUST AS FAR
— by building the same 14 GW of CTs California does not need, through the economic channel
instead of the administrative one. Row 4 would read PASS while the model still over-builds 14 GW
of firm capacity into a market that is 6.9% LONG on RA. That is rule 1 [R-STRUCT] verbatim: the
right number through a mechanism that isn't real. The owner declined it explicitly.
(The anchor IS mis-specified — >=94% of a $40k/MW-yr gap, a 550 MW COMBINED-CYCLE retention cost
used as the entry price for a new COMBUSTION TURBINE. It may be chartered LATER on its own
rule-14 merits, by someone else, with a charter stating it is not a row-4 fix. Not you, not now.)

=== SCOPE DISCIPLINE ===
If the shortfall turns out to be partly legitimate — a real difference between our zonal
representation and CAISO's RA accounting boundary — rule 14's misalignment exception applies:
document it explicitly and prefer a RECONCILED version of the real data over a guess. Do not tune
the fleet to hit a reserve position. If row 4 does not clear after the fleet is right, THAT IS
THE FINDING; write it up (rule 11).
CAISO holds no marker and the freeze is ACTIVE — in-sample or forecast-mode years only. Rule 25:
this is CAISO's lane; do not import a MISO/PJM parameter or verdict. Rule 28: matrix cell +
citation in THIS session.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST. Never
push a >=300-line file via push_files. The documented cache-purge command deletes TRACKED files;
`git status --short` after. Evolution ledgers live at <out-dir>/<ISO>/<cache_key>/ and
load_ledgers_for_run returns {} rather than raising. MARKET_SIM_DATA_ROOT outside REPO_ROOT
shifts the cache key (FFR-3F §5). Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-4d-caiso-fleet-vintage-<date>.md — the 11,711 MW decomposed by
cause with megawatts attributed, what was fixed and what is a documented boundary misalignment,
row 4's position after, and an explicit statement that the anchor route was not taken.
```

### FFR-3Q-3 [OPUS] — the FH-1 §3.3 gate re-probe, on the FIXED seam

```
[OPUS] FFR-3Q-3 — Solve and report the FH-1 §3.3 gate re-probe. This finishes FFR-3Q Task 1,
which was pre-registered and then never solved, and whose first attempt hit the rule-22 breach
that FFR-3U has since fixed. Owner authorized the dispatch 2026-08-04 (sitting Addendum O).
THE FH-4/FH-5 LIFT IS A MANAGER BOX (Addendum I.1). You do not lift it. Reporting green does not
lift it. Say so in your write-up.

=== VERIFIED STATE (2026-08-04 @ origin/main 49aac023 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT 2026-08-03-ercot158-
pool-arm · PJM pjm-152-collapse · CAISO caiso-166-measured-dlap · NYISO nyiso-120-c119-scope ·
NEISO neiso-caiso156-meter-screen · MISO miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM} — ERCOT IS NOT IN IT; `final` = EMPTY. HOLDOUT FREEZE
ACTIVE and it outranks both blocks. Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10
warm-start OFF for forecast bundles — EVERY FORECAST KEY MOVED, so you solve COLD; results/ is
gitignored, so "expect cache hits" is never a valid budget in a fresh container).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly like
a data problem and is NOT one), THEN scripts/regenerate_clean.py (~63-65 min, 50 datatypes,
1.6 GB). Rule 12 PER PROMPT: years sequential, <=2 concurrent invocations, <=5 solve-years each.
Rule 27: Opus/Fable only for src/ and scripts/run_*.

=== WHAT CHANGED SINCE THE FAILED ATTEMPT — READ BOTH ===
docs/handoffs/ffr-3q-window-recut-2026-08-04.md (the pre-registration in §2.1 SURVIVES VERBATIM;
§2.2 is the STOP-THE-LINE record) and docs/handoffs/ffr-3u-bridge-seam-2026-08-04.md (the fix).
FFR-3U scoped the un-bridging clause to genuine T1-X crossover forward years, so at base 2021 the
runner AGAIN BRIDGES 2022 (validation tier) and 2026 (locked test). _validate_window now
policy-checks the set the RUNNER will actually solve, through the runner's own predicate. The
launch banner's promise is derived from that same predicate and ASSERTED AGAINST THE REALIZED
LEDGERS at completion — a mismatch is a hard SystemExit, not a warning.
BEFORE YOU SOLVE, VERIFY THE FIX HOLDS AT YOUR HEAD: assert is_bridge(2022) is True at base 2021
and that the harness's declared solve set is [2021, 2023, 2024, 2025] with 2022 bridged. If your
run's realized solved_years include 2022, STOP IMMEDIATELY — that is a second rule-22 breach, you
quarantine and report, you do not proceed and you do not patch the guard yourself.

=== THE POSTURE (FFR-3Q §2.1, in force verbatim) ===
ERCOT, Arm R (hindcast_realized gas + per-solve-year weather), base 2021 / vintage 2020, window
2021-2025, shipped capacity-price posture, D-1 and D-2 ARMED, exit_rate_limits default OFF,
hindcast namespace, meta.kind="full_forward".
  Arm A — primary, shipped default: retirement_rule=pipeline
  Arm B — paired control, explicitly labelled: retirement_rule=legacy
RE-VERIFY the two cache keys and the field-by-field asdict diff at YOUR head before solving: the
diff must contain EXACTLY ONE entry (retirement_rule). FFR-3Q measured b99600bceb8cb6b8 /
5c352508039513da, but D-10's cache epoch has since moved forecast keys — SO EXPECT THESE TO
DIFFER, and note that FFR-3U INVALIDATED those two specific keys by design (D-11 condition b), so
a refusal on them is CORRECT BEHAVIOUR, not a bug. Report the new keys. Confirm `env | grep
MARKET_SIM` is empty (FFR-3F §5). Arm B is the ONE place Addendum D's HOLD PROMOTION permits
unarming D-1: an explicitly labelled control. Unarm nothing anywhere else.

=== THE PRE-REGISTERED READS (do not select a read after the fact) ===
1. PRIMARY: pipeline_events per year. The purpose of the re-cut is that the retirement layer
   becomes OBSERVABLE. Both prior probes returned ZERO events in every arm, which is why both
   were uninformative. IF THIS WINDOW ALSO RETURNS ZERO, THAT IS THE HEADLINE FINDING and I6/I7/
   I12 are reported as invariant-BY-VACANCY, never as a pass.
2. L_coal = 3 means only a 2021 or 2022 screen decision can execute in-window (2024/2025). Report
   the candidate count per screen year explicitly — the re-cut succeeds or fails on that.
3. I12 is MEASURED here, not attributed. FFR-3N attributed the inversion to storage accreditation,
   not the retirement rule — read it. Report only whether the longer window moves it, and note
   its WARN previously had INVERTED sign (over-retiring -> retiring nothing).
4. The exit-throughput cap is OBSERVED, not armed. exit_rate_limits stays default-OFF;
   _apply_exit_throughput_cap only fires when a year's `due` set is non-empty, so the reportable
   precondition is whether `due` is EVER non-empty. It has never bound in any full solve.

=== HOW TO READ THE RESULT (Addendum G.2 — three binds) ===
(a) The earlier FH-1 green was NOT the fix's — a paired pre-fix control returned it identically.
(b) I12's WARN had inverted sign. (c) Zero pipeline_events means the retirement layer was
UNTESTED, not validated. A GREEN ON A POSTURE THAT CANNOT EXERCISE THE MECHANISM IS NOT A PASS.
State which of these your result is, and do not round a vacancy up to a pass.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN BEFORE
DIAGNOSING. Never push a >=300-line file via push_files. The documented cache-purge command
deletes TRACKED files; `git status --short` after. Evolution ledgers live at
<out-dir>/<ISO>/<cache_key>/, NOT the out-dir root, and load_ledgers_for_run returns {} rather
than raising — a wrong path silently reads as "no evolution happened", which in THIS lane is
indistinguishable from your primary finding. VERIFY THE PATH BEFORE BELIEVING A ZERO.
A REQUEST-side cache_key() is NOT the key a run is recorded under (FFR-3A-2 §1.2). Shell cwd
persists between Bash calls.

=== DELIVERABLE ===
Register both arms to frontend/data/hindcast/ with meta.kind="full_forward" — NEVER the backcast
registry. Report by APPENDING an addendum to docs/handoffs/ffr-3q-window-recut-2026-08-04.md
(do not rewrite that file) or a new ffr-3q3-<date>.md that it links. Rule 28: matrix cell +
citation in THIS session. State explicitly that the FH-4/FH-5 lift is the manager's call and that
you are not making it.
```

---

## §0j — AMENDMENT to §0i: FFR-4B's evidence is superseded; FFR-4E added (2026-08-04 @ `c7d806eb`)

Correction record: sitting **Addendum P**. FFR-3V reopened and re-measured AFTER §0i was written.

**Dispatch as written:** FFR-4A, FFR-4C, FFR-4D, FFR-3Q-3 (§0i). FFR-4C's case is *strengthened*
— the screen credits wind **$86,549/MW-yr** vs solar **$26,787–32,873/MW-yr**, which FFR-3V names
as the mechanical origin of the leg's inverted tech mix (model wind 43.7 % / solar 0.0 % vs actual
22.5 % / 58.3 %). Add that line to its evidence block.

**FFR-4B: replace its `=== THE EVIDENCE ===` block with the corrected one below.** The rest of
its prompt stands. Two substantive changes: the capacity payment is **$0 in 2022–2024 and
$327,456/MW-yr firm in 2025**, not a flat $14,364/MW-yr; and the lane order is amended — FFR-3V
now ranks **arming as 1a** and **wiring as 1b, subordinate**, because the accreditation only
bites where the payment is non-zero.

```
=== THE EVIDENCE (measured; corrected 2026-08-04, sitting Addendum P — do not re-derive) ===
docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §§3.1, 3.3, 4.6b, 7. MISO solar is a MARGIN
finding — solar reaches the screen every decision year and is rejected on economics before any
cap is consulted. Internal control: WIND BUILT 4.0 GW through the same code path and caps.
Solar is `binding_cap: "unprofitable"` in ALL FOUR decision years, margins
-26,446 / -22,681 / -35,946 / -33,406 $/MW-yr for 2022/2023/2024/2025.

THE CAPACITY PAYMENT IS NOT A STANDING ANNUAL NUMBER. MISO's modelled reserve margin walks
27.3% -> 20.7% -> 11.4% -> 17.3% against a 13.75% requirement:
  2022-2024 decision years: payment is $0 FOR EVERY TECHNOLOGY, thermal included. MISO is LONG
    and its VRR pays nothing above a ~1.02 position. THIS IS FAITHFUL, NOT BROKEN — the real
    PY2021-22 PRA cleared at ~$1,825/MW-yr. Do not "fix" it.
  2025 decision year: the payment switches ON at $327,456/MW-yr firm and is the entire reason
    gas CC and CT flip profitable and build 4.48 GW.
So entry_vre_capacity_revenue is INERT WHILE THE ISO IS LONG AND DECISIVE THE MOMENT IT TIGHTENS.

THE ASYMMETRY, MEASURED: in 2025 the UNGATED thermal branch takes $307-311k/MW-yr while solar is
denied its share by a default-off gate. Crediting even the generic 0.18 fallback gives solar
$58,942/MW-yr and flips its margin from -$33,406 to +$25,536. That asymmetry is inside ONE
function and the code already exists. It is the sharpest single asymmetry the lane found.

D-12 (wire the accreditation) is SUBORDINATE to D-2' and only bites where the payment is
non-zero: MISO's published solar accreditation is already intaken and cited at elcc/miso/miso.csv
and simply not read into RENEWABLE_ELCC_CURVES_BY_ISO["MISO"]. Unwired the model uses the generic
0.18; the published season-weighted value is 0.3875 (2023 break-even $37.59 vs $29.41/MWh).
Rule 14 [R-ACCURATE]: the accurate value is on disk, so it goes in whatever it does to a fit.

TWO CAVEATS YOU MUST CARRY, BOTH MEASURED:
  (i) ARMING D-2' WOULD NOT HAVE MOVED THIS LEG'S FC-3 BAND AT ALL — a 2025 decision commissions
      at COD 2027, outside the 2021-2025 window. Do not report a band movement as this lane's
      result and do not tune toward one.
  (ii) TWO CAUSES OUTRANK THIS LANE and are NOT yours: the missing procurement channel (FFR-3V's
      own #1 — 18.6 GW was built on utility IRP/RFP and corporate PPAs against the ITC, a channel
      apply_economic_new_entry represents NOWHERE; owner card D-16), and the 2024 entry price
      signal's missing ORDC tail (FFR-4E below). If your result looks small next to those, that
      is the correct relative size and you say so.

LANE ORDER AMENDED: arm-then-wire is acceptable (FFR-3V ranks arming 1a, wiring 1b). Either
order is fine; what is NOT optional is that the two are measured SEPARABLY against a paired
control, so neither is attributed to the other.
```

### FFR-4E [OPUS] — the 2024 MISO entry price signal has no ORDC tail

```
[OPUS] FFR-4E — Diagnose why the entry price signal's lookahead stack carries no scarcity tail,
and whether that is the largest suppressor of MISO entry. DIAGNOSIS lane. Chartered by the
workstream manager (sitting Addendum P.3b), NOT by an owner card — because it investigates
whether an EXISTING overlay is wrongly off, not whether to add a mechanism. If your answer turns
out to require a NEW mechanism, STOP and escalate; that is an owner decision.

=== VERIFIED STATE (2026-08-04 @ origin/main c7d806eb — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; NYISO has moved EIGHT times in
five days): ERCOT 2026-08-03-ercot158-pool-arm · PJM 2026-08-04-pjm-152-collapse ·
CAISO 2026-08-04-caiso-166-measured-dlap · NYISO 2026-08-04-nyiso-125-seam-envelope ·
NEISO 2026-08-03-neiso-caiso156-meter-screen · MISO 2026-08-04-miso-126-steampart-b.
Markers: `complete` = {NEISO, NYISO, PJM} — MISO IS NOT IN IT; `final` = EMPTY. HOLDOUT FREEZE
ACTIVE. NOTE (caiso-171, 0043fc22): THE MARKER AND THE FREEZE ARE ORTHOGONAL — a freeze SUSPENDS
the authorization a marker grants, it does not withdraw the marker; NYISO and PJM were declared
complete six days INTO the freeze. Do not reason that a freeze blocks a marker.
In-sample 2023-2025 and forecast-mode 2026+ only; NEVER 2022/2020/2019/2026-backcast.
Cache epochs 2026-08-02, 2026-08-03b, 2026-08-04 (D-10).
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly like
a data problem and is NOT one), THEN scripts/regenerate_clean.py (~63-65 min). Rule 12 PER
PROMPT; MISO is ~8.6 GB per solve — never co-run with PJM in one session. Rule 27: Opus/Fable.

=== THE FINDING YOU ARE INHERITING (measured; do not re-derive) ===
docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §3.2 and §0. In the 2024 decision year the
entry price signal's MAXIMUM HOURLY PRICE is $39/MWh against solar's $43.18/MWh break-even MEAN.
The margin is not close — it is UNREACHABLE. Cause named: `scarcity_price_overlay: False` leaves
the lookahead stack with NO ORDC TAIL AT ALL. It also zeroes the peaker outright: gas_ct variable
cost $41.39 exceeds the $39 ceiling, so no CT can ever clear. FFR-3V calls this "the largest
single suppressor of MISO entry in 2024/2025 — upstream of every revenue lever below."

=== YOUR QUESTION ===
Is the overlay's absence from the lookahead stack a DEFECT or a deliberate scoping choice?
Establish, in this order:
1. WHERE the flag is set for the entry/lookahead path specifically, and whether it differs from
   the dispatch path the same run uses. A price signal that the screen sees but the dispatch does
   not (or vice versa) is one mechanism answering to two definitions (rule 19 [R-ONE-MECH]).
2. WHETHER IT IS ISO-WIDE OR MISO-SPECIFIC. Report the flag's effective value per ISO on the
   entry path. Rule 25 [R-ISO-SCOPE]: if it is off everywhere, that is a program-wide finding and
   each ISO's remedy is still its own decision — do not arm another ISO from MISO's evidence.
3. WHAT THE TAIL WOULD BE WORTH, bounded from committed artifacts before you solve. The screen
   reads an annual price signal; quantify how many hours of what price the ORDC tail contributes
   and what that does to a peaker's and a solar unit's margin. If the bound is decisive you may
   not need a solve at all.
4. WHETHER THE $39 CEILING IS ITSELF FAITHFUL. A modelled ISO whose annual maximum hourly price
   is $39/MWh has no scarcity hours of any kind, which is a strong claim about MISO. Check it
   against MISO's actual 2024 price distribution — if the real market had hours above $39, the
   lookahead stack is not representing the market, and that is the finding regardless of the flag.

=== RULES THAT BIND THIS LANE HARDEST ===
Rule 1 [R-STRUCT] / rule 11: if arming the overlay makes a band worse, KEEP IT and open the root
cause — a real market behaviour stays in. Equally, do NOT arm it because it improves a residual;
arm it (or propose arming it) because the price signal the screen reads should be the price
signal the market forms. Rule 14 [R-ACCURATE]: prefer the measured MISO price distribution over
any modelled proxy when checking limb 4.
DO NOT tune the ORDC parameters. DO NOT add a scarcity adder. If the overlay is correctly off for
a stated reason, say so and the finding is that the ENTRY SCREEN needs a different price basis —
which you report, not implement.

=== SCOPE DISCIPLINE ===
Diagnose and write up; propose with evidence and let the owner charter the fix. Do not promote,
do not flip a default, do not widen a band. Rule 28: stamp any matrix cell you test in THIS
session, rejections included.

=== COORDINATION ===
FFR-4B (D-12 + D-2') and FFR-4C (D-13) are running concurrently on the same MISO entry screen.
Your finding is UPSTREAM of both — if it holds, their levers operate on a price signal that
cannot clear solar in 2024 regardless. Say so plainly; do not soften it to avoid stepping on
their results, and do not wait for them.

=== TRAPS ===
Push 413: `git remote prune origin`, or `git fetch origin main` + rebase. FETCH MAIN FIRST. Never
push a >=300-line file via push_files. The documented cache-purge command deletes TRACKED files;
`git status --short` after. Evolution ledgers live at <out-dir>/<ISO>/<cache_key>/, NOT the
out-dir root, and load_ledgers_for_run returns {} rather than raising — a wrong path silently
reads as "no evolution happened". MARKET_SIM_DATA_ROOT outside REPO_ROOT shifts the cache key
(FFR-3F §5). Shell cwd persists between Bash calls.

Deliverable: docs/handoffs/ffr-4e-entry-price-scarcity-<date>.md — where the flag is set and
whether the two paths agree, the per-ISO map, the bounded value of the tail, the limb-4 check
against MISO's actual price distribution, and what you did NOT separate.
```

## §0k — WAVE 5 OPENS: FFR-5A dispatched; D-16 and D-17 put to the owner (2026-08-05 @ `4d8f0c06`)

Sitting record: **Addendum R** (which also discharges Q.2's FFR-3Q-3 keeper-sensitivity exposure
by measurement — the ercot-165 promotion moved no shipped default; the one shipped delta since
the arms' base is D-13's `ira_ptc_credit_window_years=10`). Wave 4 is closed (Addendum Q).
FFR-5A below is manager-chartered (R.4, the FFR-4E precedent class). FFR-5B (D-16(a)) and
FFR-5C (D-17(a)) dispatch only on their signatures; their prompts are appended here at dispatch
time. ~~FFR-3Q-2~~ remains STRUCK (§0g).

### FFR-5A [FABLE] — why does the soft latch reverse an 8.2 GW coal exit cohort at its own execute_year?

```
[FABLE] FFR-5A — Why does the soft latch reverse an 8.2 GW coal exit cohort at its own
execute_year? ROOT-CAUSE DIAGNOSIS lane (Wave 5). Chartered by the workstream manager (sitting
Addendum R.4; same manager-charterable class as FFR-4E): it diagnoses why an EXISTING mechanism
behaves as measured. It lands no fix, flips no default, tunes nothing, promotes nothing. If the
root cause turns out to need a NEW mechanism (hysteresis, distress memory, a changed bar), STOP
and escalate — that is an owner card.

=== VERIFIED STATE (2026-08-05 @ origin/main 4d8f0c06 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; all six moved during Wave 4):
ERCOT 2026-08-04-ercot165-unpooled-share · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-04-caiso-172-measured-path15 · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-04-neiso81-chpheatrate · MISO 2026-08-04-miso-127-onlinepmin.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE — it blocks
out-of-training BACKCAST solve/score/registration only; it does NOT block this lane's
forecast-mode hindcast window. The 2021-2025 window with 2022 BRIDGED (evolved, never solved,
its data never read) is legal by the enumerated carve-out in scripts/lib/holdout_policy.py;
ERCOT holds no marker and needs none for it. The marker and the freeze are orthogonal
(caiso-171): a freeze SUSPENDS what a marker grants, it does not withdraw the marker.
Cache epochs 2026-08-02 / 2026-08-03b / 2026-08-04 (D-10: warm-start OFF for forecast bundles —
deliberate, not a bug to route around). results/ is gitignored: a fresh container has NO cache;
budget for COLD solves.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min — the container ships NO Python environment;
skipping it makes regenerate_clean.py report "50/50 datatype(s) failed", which reads exactly
like a data problem and is NOT one), THEN scripts/regenerate_clean.py (~63-65 min, 50 datatypes,
1.6 GB). Rule 12 PER PROMPT (Addendum F.2): years sequential within an invocation; <=2
concurrent invocations; <=5 solve-years per invocation. Rule 27: FABLE/OPUS only (this prompt is
FABLE — src/ instrumentation is in scope).

=== THE FINDING YOU ARE INHERITING (measured, FFR-3Q-3; do not re-derive the record) ===
docs/handoffs/ffr-3q3-gate-reprobe-2026-08-04.md §§3.1-3.5, §7. At the five-year re-cut (ERCOT
T1-FF, Arm R, base 2021 / vintage 2020, window 2021-2025 with 2022 bridged, shipped defaults =
D-1 pipeline rule + D-2 dampers armed):
- The 2021 loss-year screen decides a 29-unit / 8,218 MW ALL-COAL cohort (execute_year 2024).
  2023 re-confirms all 29. 2024 — the cohort's own execute_year — REVERSES all 29.
  `executed` = 0, in every year, in both arms. 1,205 pipeline_events total; 58.7 GW refused by
  the admission cap.
- THE REVERSAL RUNS COUNTER TO PRICE DIRECTION: the 2024 screen re-clears coal on 2023 dispatch
  ($15.77/MWh system mean) that had FAILED on 2021's richer $23.40; 2024 is the cheapest year in
  the window ($13.62). Max hourly price $68.78 (2021) — no scarcity anywhere. The vintage-2020
  fleet carries a 48.5% reserve margin.
- FIRST SUSPECT, flagged by FFR-3Q-3 and deliberately not adjudicated: the reserve leg of the
  attainable margin (`screen_reserve_value_enabled` is ON).
- Against 1.534 GW of actual ERCOT exits 2023-25: shipped `pipeline` retires 0.000 GW (recall
  0/3); `legacy` retires 17.309 GW (97.1% false). Both FAIL, in opposite directions. This is why
  FH-4/FH-5 stay blocked (Addendum Q.1): the EXIT half of the retirement layer has never once
  executed in any full run.

=== WHERE THE MECHANISM LIVES ===
src/market_sim/model/capacity_evolution/retirements.py, `_apply_pipeline_retirements`:
- Soft latch (component 3), ~lines 1440-1456: per pipelined unit,
  `failing = net_revenue < going_forward_cost`; a not-failing year emits `reversed` and pops the
  unit from the pipeline. ONE non-failing year reverses. The docstring (~1385-1389) states the
  intent: "one good year no longer erases the distress history unless it actually restores
  viability."
- The margins come from upstream via prior_results (the year-1 dispatch): the attainable
  pro-forma Σ_t max(0, price − full variable cost, reserve price) × pmax × availability
  (CLAUDE.md capacity-evolution step 3), against FOM-only going-forward cost (coal FOM ×1.3).
- Execution (component 4) fires at decided_year + L_f (coal L=3); the reliability floor
  (component 5) and the exit-throughput cap sit AFTER the latch — nothing downstream ever fires
  when the latch reverses first.

=== STEP 0 — REPRODUCE BEFORE YOU DIAGNOSE (Addendum R.1; J.1 discipline) ===
The FFR-3Q-3 arms are NOT byte-reproducible at your HEAD: D-13 (`ira_ptc_credit_window_years=10`,
commit 7bdc58c6) moved a shipped forecast-path default since their base 68e7bfcd, and the cache
keys moved with it. The ercot-165 keeper promotion moved NO shipped default (its fields land
False/"tie"; ERCOT's ISOConfig untouched) — measured in Addendum R.1; do not re-litigate it.
1. Re-run Arm A ONLY at your HEAD (the legacy control is NOT needed — this lane diagnoses the
   latch, not the A/B split): scripts/run_capacity_hindcast.py, ERCOT, vintage 2020, window
   2021-2025, full-forward, Arm R — reproduce FFR-3Q-3 §2's posture EXACTLY as recorded, with
   every optional flag OMITTED so shipped defaults inherit. Before any downstream read, verify
   the realized run_config shows: retirement_rule=pipeline, entry_rate_limits=True,
   entry_commissioning_lag=True, exit_rate_limits=False, crossover_solve_year_weather=True,
   gas_price_path=hindcast_realized. One invocation, 4 LP years (2021, 2023, 2024, 2025),
   sequential; expect a NEW cache key and a COLD solve.
2. Verify the reversal reproduces: read the evolution ledgers at <out-dir>/ERCOT/<cache_key>/
   (NEVER the out-dir root — load_ledgers_for_run returns {} on a wrong path, and in THIS lane a
   silent {} is indistinguishable from a finding; assert the path exists and enumerate
   evolution_*.json first). Read decided_year off the event rows, not the ledger year (the 2022
   ledger carries decided_year=2021 rows — ffr-3q3 §3.2 records the trap).
3. If the reversal does NOT reproduce, THAT is the finding: attribute against the enumerated
   D-13 delta (the only shipped solve-affecting change since 68e7bfcd) and stop — do not force
   the phenomenon back into existence.

=== YOUR QUESTION, DECOMPOSED ===
1. DECOMPOSE THE BAR, both sides, per unit, for the 29 units, at each screen year: energy leg,
   reserve leg, going-forward cost. Instrument the screen so `pipeline_events` rows carry
   net_revenue, going_forward_cost, and the reserve-leg share (a ledger enrichment — new row
   fields, no behavior change, no tunable; rule 24 untouched). Which leg moves 29 units from
   failing at $23.40-mean prices to clearing at $15.77-mean? Quantify: how much of the 2023
   attainable margin is reserve-price hours vs energy?
2. IS THE BAR THE SAME OBJECT YEAR OVER YEAR? Same availability, pmax, fuel-cost basis, FOM
   multiplier, same reserve-price source (co-opt duals vs ORDC adder — which one is live here,
   given `ercot_thermal_as_endogenous`'s state in this posture?)? A basis drift between the 2021
   screen and the 2023 screen would explain counter-price recovery with no economics at all.
3. ADJUDICATE INTENT VS CODE: the docstring says one good year should NOT erase distress "unless
   it actually restores viability"; the code reverses on ONE non-failing year. Either the 2023
   re-clear is a genuine viability restoration (latch behaved as designed; the defect is
   upstream in the margin), or the margin computation overstates viability (the latch's INPUT is
   the defect). Check the design record for what "restores viability" was intended to mean —
   the RC-0B / retirement-calibration lane docs under docs/handoffs/ (see
   docs/handoffs/forecast-retirement-calibration-plan-2026-07.md and its lineage).
4. CLASSIFY THE FIX — ESCALATE, DO NOT LAND: (a) computation defect in the bar (wrong year's
   prices, wrong reserve source, wrong availability/basis) => defect, escalate with the exact
   line; (b) the latch needs memory/hysteresis => NEW mechanism, owner card, design nothing;
   (c) everything computes as specified and an oversupplied 48.5%-RM fleet SHOULD retain coal on
   model economics => the defect is elsewhere (the real exits happened for reasons the screen
   cannot see — say so plainly; that REFRAMES FH-4/FH-5, it does not unblock them).

=== RULES THAT BIND HARDEST ===
Rule 1 [R-STRUCT] / rule 11: no tuning toward the actual 1.534 GW; if the faithful computation
retires nothing, that is the finding. Rule 19 [R-ONE-MECH]: do not propose a second
latch/floor/counter stacked on the unexplained residual of this one. Rule 23 [R-FROZEN-DERIVE]:
derive nothing from the exit residual. Rule 24 [R-REGISTRY]: no new knob; the ledger enrichment
adds row fields, not parameters. Rule 28: economic_retirement_screen ERCOT `fc` stays O unless
your evidence earns a verdict; stamp any cell you adjudicate in THIS session, with citation.
FH-4/FH-5: the lift is a MANAGER box (Addendum I.1). You report; you do not lift; green does not
lift.

=== REGISTRATION ===
If your step-0/1 run completes, register the arm to frontend/data/hindcast/
(scripts/register_hindcast.py, slim files, meta.kind="full_forward", id
ercot-2021-2025-t1ff-armr-ffr5a-pipeline) exactly as FFR-3Q-3 did. It is EVIDENCE, expected to
be superseded when keepers settle (Q.2) — say so in the sidecar notes. NEVER the backcast
registry (frontend/data/backcast/ is not yours to touch).

=== TRAPS ===
Push 413 has two causes: a merged branch's stale tracking ref (`git remote prune origin`) and a
stale local origin/main defeating delta compression (`git fetch origin main` + rebase — measured
647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files
(string-content full-file rewrite — the exact thing rule 27 forbids). The documented cache-purge
command deletes TRACKED files — `git status --short` after any purge; restore with
`git checkout --`. `git checkout origin/main -- <path>` STAGES those files — `git restore
--staged` after. Shell cwd persists between Bash calls. MARKET_SIM_DATA_ROOT outside REPO_ROOT
shifts the cache key (FFR-3F §5). A REQUEST-side cache_key() is NOT the recorded key (FFR-3A-2
§1.2) — take the key from the runtime `cache_key=` log line. The stop-hook reports unverified
commits on already-merged shared history: if `git rev-list --count origin/main..HEAD` is 0 you
have nothing to amend.

Deliverable: docs/handoffs/ffr-5a-soft-latch-<date>.md — step-0 reproduction status (including
the realized-config verification), the per-unit bar decomposition, the year-over-year basis
audit, the intent-vs-code adjudication with the design-record citation, the fix CLASS with its
escalation, and what you did NOT separate.
```

### FFR-5B [OPUS] — design the procurement-channel mechanism for VRE entry (D-16(a); NO implementation)

Signed 2026-08-05 (Addendum R.5). Dispatched with FFR-5A and FFR-5C.

```
[OPUS] FFR-5B — Design the procurement-channel mechanism for VRE entry (D-16(a) scoping; NO
implementation). STRUCTURAL SCOPING lane (Wave 5), chartered by owner decision D-16(a) (sitting
Addendum R.3/R.5, signed 2026-08-05). The deliverable is a DESIGN plus a rule-13 [R-MEASURED]
admissibility argument. No code lands, no solve runs, no parameter is proposed as a number, no
default moves. If your design work convinces you an implementation shortcut is safe, it is not:
implementation is a SEPARATE owner decision, and your job includes drafting its card.

=== VERIFIED STATE (2026-08-05 @ origin/main 243b4ab1 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; all six moved during Wave 4):
ERCOT 2026-08-04-ercot165-unpooled-share · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-04-caiso-172-measured-path15 · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-04-neiso81-chpheatrate · MISO 2026-08-04-miso-127-onlinepmin.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (it blocks
out-of-training BACKCAST solve/score/registration only — irrelevant to this no-solve lane). The
marker and the freeze are orthogonal (caiso-171): a freeze SUSPENDS what a marker grants, it
does not withdraw the marker. This lane reads docs + code + committed data only; if you run
Python for data inspection, `uv sync` first (~2 min — the container ships NO Python
environment). scripts/regenerate_clean.py is NOT needed (no solve). Rule 27: OPUS/FABLE.

=== THE GAP (measured; do not re-derive) ===
FFR-3V (docs/handoffs/ffr-3v-miso-entry-screen-2026-08-04.md §3.1, §7 proposal 1) + sitting
Addendum P.3(a) + card D-16 (end of Addendum P): MISO built 18.649 GW of solar 2021-2025 while
BOTH revenue levers the entry screen can see are correctly ~zero (PRA cleared ~$1,825/MW-yr; the
11% RPS is slack at 16.9% modelled VRE share). The build happened on utility IRP/RFP procurement
and corporate PPAs against the ITC — a long-term contracting channel `apply_economic_new_entry`
represents NOWHERE (it screens merchant energy margin only). FFR-3V's rule-1 reading, adopted by
the owner: closing this with a revenue adder tuned until solar clears is the fitted-adder
failure rule 1 forbids. Internal control that makes the gap sharp: wind built 4.0 GW through the
same code path and caps.

=== YOUR QUESTION ===
Specify what a structurally faithful procurement channel would have to BE. The design answers,
in order:
1. WHAT DRIVES PROCUREMENT VOLUME as a forward-regenerating input. Rule 13's admissibility test,
   verbatim: could this same quantity be produced for a forward year from forward drivers, and
   would it respond to changed conditions? Candidates to evaluate (not exhaustive, none
   pre-approved): announced utility IRP targets/portfolios, state clean-energy statutes beyond
   the modelled RPS constraint, corporate PPA demand, the interconnection queue's
   signed-IA/executed-GIA cohort (EIA-860 proposed-pipeline statuses). For each: what data
   identifies it, at what vintage, with what forward analogue, and how it responds to changed
   conditions.
2. WHERE IT ENTERS the capacity-evolution loop (spec §5.1: step 4 known additions vs step 5
   economic entry vs a new step), and how it composes with the caps FFR-4A audited — it must not
   become a second netting or a second ladder (rule 19 [R-ONE-MECH]), and it must state its
   interaction with D-17's chartered fix (FFR-5C, running this wave).
3. HOW IT FAILS SAFE: what stops it from degenerating into "paste the actual build in" (the
   rule-13 forbidden pole — pinning to observed outcomes)? Draw the line between an
   announced-procurement INPUT (admissible — the confirmed-exits analogue) and a
   measured-outcome PIN (forbidden) explicitly, including the hindcast information gate
   (instrument_date <= the vintage cutoff; precedent
   docs/handoffs/confirmed-retirement-plan-2026-07.md).
4. SCOPE per rule 25 [R-ISO-SCOPE]: MISO evidence charters MISO. State per-ISO data availability
   for the channel without arming anywhere; every other ISO enters as its own later decision.
5. VERDICT: a rule-13 admissibility argument for the recommended design — or a finding that NO
   admissible design exists. The null is a valid deliverable; say it plainly rather than forcing
   a design.

=== RULES THAT BIND HARDEST ===
Rule 1 [R-STRUCT] (structure first; no fitted adders). Rule 13 [R-MEASURED] (the admissibility
test IS your rubric). Rule 19 [R-ONE-MECH]. Rule 24 [R-REGISTRY] (any future tunable must be
named for ScenarioConfig/run_config in the design). Rule 25 [R-ISO-SCOPE]. Rule 28 (a design
alone changes no matrix cell; if you nonetheless adjudicate one, stamp it in-session with
citation).

=== DELIVERABLE ===
docs/handoffs/ffr-5b-procurement-channel-design-<date>.md: the candidate-driver evaluation
(limb 1), the insertion-point design (limb 2), the fail-safe line (limb 3), the per-ISO scope
map (limb 4), the admissibility verdict (limb 5), what you did NOT decide, and a PROPOSED OWNER
CARD for the implementation decision (measured consequence, named recommendation, the wrong
option with its real cost) ready for the manager to put. Do not open the implementation.

=== TRAPS ===
Push 413 has two causes: a merged branch's stale tracking ref (`git remote prune origin`) and a
stale local origin/main defeating delta compression (`git fetch origin main` + rebase — measured
647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files
(string-content full-file rewrite — rule 27). Shell cwd persists between Bash calls. The
stop-hook reports unverified commits on already-merged shared history: if
`git rev-list --count origin/main..HEAD` is 0 you have nothing to amend.
```

### FFR-5C [OPUS] — land the entry-cap fix: un-net the stock from the flows; give the pro-forma eyes (D-17(a))

Signed 2026-08-05 (Addendum R.5). Dispatched with FFR-5A and FFR-5B.

```
[OPUS] FFR-5C — Land the entry-cap fix: un-net the stock from the flows; give the pro-forma
eyes (D-17(a), sitting Addendum R.2/R.5, signed 2026-08-05). IMPLEMENTATION lane (Wave 5) for
FFR-4A's E-1 + E-2, landed TOGETHER (rule 19): remove the pending-stock netting from both flow
caps AND include pending entry_pipeline rows in the lookahead price signal's stack, as ONE gated
ScenarioConfig field, DEFAULT OFF, with its matrix row in the same PR (rule 28c — CI enforces)
and a paired-arm measurement. The shipped path stays BYTE-IDENTICAL until armed, and you prove
that with a regression test.

=== VERIFIED STATE (2026-08-05 @ origin/main 243b4ab1 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF; all six moved during Wave 4):
ERCOT 2026-08-04-ercot165-unpooled-share · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-04-caiso-172-measured-path15 · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-04-neiso81-chpheatrate · MISO 2026-08-04-miso-127-onlinepmin.
Markers: `complete` = {NEISO, NYISO, PJM}; `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast
out-of-training only). The marker and the freeze are orthogonal (caiso-171).
PREREQUISITES: `uv sync` FIRST (~2 min — the container ships NO Python environment; skipping it
makes any repo script fail in ways that read like data problems and are not).
scripts/regenerate_clean.py (~63-65 min) ONLY if a test you need reads the clean store — the
FFR-4A harness pattern reads committed EIA-860 vintages and shipped code; decide before spending
the hour. Rule 12 PER PROMPT; this lane needs NO LP solve (see SCOPE DISCIPLINE). Rule 27:
OPUS/FABLE; new_entry.py and runner.py are core src/ — edit locally, push exact on-disk bytes,
verify the blob after any push touching a >=300-line file.

=== THE DEFECT (measured, FFR-4A; do not re-derive) ===
docs/handoffs/ffr-4a-entry-ladder-2026-08-04.md. The pending-pipeline STOCK (`_pending_by_tech`,
MW, no time denominator) is netted from two annual-FLOW caps (new_entry.py:1131-1148): the
endogenous ladder `K × prior_max` and the static per-tech queue cap C. Consequences, derived
(§3) and MEASURED through the shipped code path (§5): long-run average decisions capped at C/L;
the ratchet's growth factor K−L+1 = 1 at the shipped (K,L)=(2,2) — frozen — in 24/24 ISO×tech
cells at both vintages; MISO wind's registered 4,000/0/4,000/0 alternation (mean 2,000 = C/L
exactly) is the static-cap signature. K=2.0 (ReEDS 200%; between the measured p75 and p90 of the
EIA-860 growth-ratio distribution) and L=2 (LBNL Queued Up median IA→COD) both keep their
citations — DO NOT MOVE EITHER. The documented intent (ff-entry-stack-completion-2026-07, gates
line 39) nets the PER-TECH cap only; the ladder half is an uncited implementation extension
(FFR-4A §1.1(b)). E-2 (FFR-4A §3.5): runner.py::_lookahead_reprice_signal prices next year's
net load into the CURRENT fleet's merit stack only (runner.py:518-527) — pending entry_pipeline
rows (known mw, known cod_year) are invisible to the pro-forma, so it re-decides the same
opportunity every lag year. THAT information gap is the real cobweb; the netting was guarding it
at the wrong object.

=== WHAT YOU LAND ===
1. ONE gated ScenarioConfig field (name it well — e.g. entry_pipeline_aware_signal — and justify
   the name in its docstring), DEFAULT OFF, visible in run_config.json (rule 24), matrix row in
   the SAME PR (rule 28c). OFF ⇒ shipped behavior byte-identical: add the regression test that
   drives apply_economic_new_entry through a multi-year path with the field off and asserts the
   shipped decision series (FFR-4A §5.2 Arm 0: MISO solar frozen at 1,236 MW/yr) is unchanged.
2. ARMED ⇒ (i) the stock netting is removed from BOTH `_ladder_remaining` (new_entry.py:
   1141-1147) and `group_remaining` (new_entry.py:1131-1137); (ii) pending entry_pipeline rows
   enter the merit stack `_lookahead_reprice_signal` prices against, at their mw, from their
   cod_year forward. ZERO new tunables — the rows already carry both fields. If you cannot do
   (ii) without inventing a parameter, STOP and escalate to the manager; do not invent one.
3. The backstop asymmetry (FFR-4A §1.3: evolve.py:708-713 nets only this-year decisions;
   adequacy.py:497-500 commissions in-year with no pipeline row) is NOT yours to reconcile.
   Record that the armed path leaves it unchanged; flag in the handoff if your change makes the
   inconsistency WORSE, with the mechanism.
4. PAIRED-ARM MEASUREMENT on the FFR-4A harness pattern (the real apply_economic_new_entry, the
   real ladder update runner.py:1153-1160, the real step-4.5 commissioning evolve.py:576-600;
   scripts recorded in FFR-4A §6): shipped vs armed, on MISO solar (ladder-first cell) AND MISO
   wind (static-cap-first cell). Check against FFR-4A's measured series (§5.2): armed must
   restore the ratchet (solar 1,236 → 2,472 → 4,944 → 6,000, then the static cap as the true
   binder) and kill the wind 4,000/0 alternation. Any deviation from the §5.2 Arm B series is a
   finding to explain, not to tune away.
5. E-3 goes in the field's docstring: under the OLD construction the growth factor K−L+1 hits
   zero at L=3 (economic entry shuts off entirely) — the armed path removes that trap; record it
   so no future per-tech L refinement re-introduces it blind.

=== SCOPE DISCIPLINE ===
NO LP solve, NO forecast/hindcast registration, NO keeper contact, NO default flip, NO arming in
any ISOConfig default_scenario_overrides. The field ships OFF everywhere; arming anywhere is a
separate owner decision informed by your paired-arm measurement. Pre-registered and carried
(FFR-4A §4/§5.4, owner-accepted at Q.3): this fix does NOT rescue MISO solar's FC-3 band — that
leg's solar dies on revenue before any cap is consulted. If your handoff or PR reads as "fixes
MISO solar", it is wrong; say the numbers are cap CEILINGS, not builds.

=== RULES THAT BIND HARDEST ===
Rule 1 [R-STRUCT] (no tuning to bands). Rule 19 [R-ONE-MECH] (E-1 and E-2 land together — the
guard RELOCATES; it neither vanishes nor duplicates). Rule 23 [R-FROZEN-DERIVE] (the
identification is FFR-4A §3.4's EIA-860 statistics — cite, never re-derive from a residual).
Rule 24 [R-REGISTRY]. Rule 27 (push-integrity: exact bytes; blob verification after any push
touching a >=300-line file). Rule 28c (matrix row in the same PR; CI enforces).

=== COORDINATION ===
FFR-5A (soft-latch root cause, retirements.py) and FFR-5B (procurement design, docs-only) run
this wave as independent sessions. Your src/ overlap with them: NONE (you: new_entry.py,
runner.py, tests; 5A: retirements.py + instrumentation). The one shared surface is
docs/codebase-site/data/mechanism-matrix.js — whichever session lands second re-checks its cell
survived the merge (the O.3 discipline; miso-124 lost a cell to exactly this race).

=== TRAPS ===
Push 413 has two causes: a merged branch's stale tracking ref (`git remote prune origin`) and a
stale local origin/main defeating delta compression (`git fetch origin main` + rebase — measured
647 KB -> 21 KB). FETCH MAIN BEFORE DIAGNOSING. Never push a >=300-line file via push_files
(string-content full-file rewrite — rule 27). The documented cache-purge command deletes TRACKED
files — `git status --short` after any purge; restore with `git checkout --`.
`git checkout origin/main -- <path>` STAGES those files — `git restore --staged` after. Shell
cwd persists between Bash calls. The stop-hook reports unverified commits on already-merged
shared history: if `git rev-list --count origin/main..HEAD` is 0 you have nothing to amend.

Deliverable: the PR (field + both halves + tests + matrix row) and
docs/handoffs/ffr-5c-entry-cap-fix-<date>.md — the byte-identity proof, the paired-arm series
against FFR-4A §5.2, the backstop-asymmetry statement, and what you did NOT separate.
```

## §0l — Wave 5 continues: FFR-5D, FFR-5E and the CAISO grant dispatched (2026-08-05 @ `5543c4c0`)

Sitting record: **Addendum S** (Wave-5 refresh: FFR-5A/5B adjudicated, three cards signed).
FFR-5A and FFR-5B are LANDED; FFR-5C is IN FLIGHT (PR #3577). **FFR-5D and FFR-5E both branch
AFTER #3577 merges** — step 0 of each verifies. The CAISO grant lane is independent of all
three. Adjudicated and carried: the reserve-leg suspect is DEAD (FFR-5A measured $0.0 both
screens — do not re-suspect it); the D-13 hash-out means "same cache key" does NOT imply
byte-identity across the D-13 boundary.

### FFR-5D [FABLE] — one price object for the capacity screens, with its level repaired (D-19(a))

```
[FABLE] FFR-5D — Unify the capacity screens on the lookahead price object and repair its level
(owner decision D-19(a), sitting Addendum S.3/S.5, signed 2026-08-05). IMPLEMENTATION lane
(Wave 5): ONE gated ScenarioConfig field, DEFAULT OFF; armed, every capacity-evolution screen
(retirement pipeline, economic entry, storage) consumes the SAME price object — the lookahead
stack-reprice — for the entering year, bridge-adjacent years included, AND the lookahead's
three measured completeness gaps are repaired. Shipped path byte-identical until armed, proven
by a regression test. This lane arms nothing, promotes nothing, tunes nothing.

=== VERIFIED STATE (2026-08-05 @ origin/main 5543c4c0 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT
2026-08-04-ercot165-unpooled-share · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-05-caiso-174-measured-fleet · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-04-miso-127-onlinepmin.
Markers: `complete` = {NEISO, NYISO, PJM} at dispatch; a concurrent governance lane is
executing the SIGNED CAISO grant, so CAISO may appear in `complete` at your head — correct
either way, re-read the file. `final` = EMPTY. HOLDOUT FREEZE ACTIVE (backcast out-of-training
only — this lane's T1-FF window is legal by the enumerated carve-out; ERCOT holds no marker and
needs none; 2022 is BRIDGED, never solved, its data never read). Marker and freeze are
orthogonal (caiso-171).
Cache epochs 2026-08-02/03b/04 (D-10 warm-start OFF for forecast bundles). results/ gitignored
— COLD solves. D-13 HASH-OUT HAZARD (FFR-5A §1): ira_ptc_credit_window_years hashes out at its
shipped default, so an identical cache key does NOT imply byte-identical behavior across the
D-13 boundary — never reuse a pre-D-13 warm dir.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min), THEN scripts/regenerate_clean.py
(~63-65 min). Rule 12 PER PROMPT: years sequential; <=2 concurrent invocations; <=5 solve-years
each. Rule 27: FABLE (runner.py is core).

=== STEP 0 — PRECONDITION AND LANDED-CODE RE-READ ===
1. PR #3577 (FFR-5C, entry_pipeline_aware_signal) MUST BE MERGED before you branch. If it is
   still open, STOP and report to the manager — do not base off its branch and do not race it.
2. Re-read `_lookahead_reprice_signal` AS LANDED (it now carries the pipeline-aware gating
   FFR-5C added) and `runner.py:2536-2553` (the price_signal seam and the rule-22 bridge guard
   at 2545-2546). Line numbers in this prompt are from FFR-5A at its base — re-locate, do not
   trust them.

=== THE EVIDENCE YOU ARE IMPLEMENTING AGAINST (measured, FFR-5A; do not re-derive) ===
docs/handoffs/ffr-5a-soft-latch-2026-08-05.md. The decide screen for any base-year cohort in a
bridged window consumes raw duals + overlay (bridge guard suppresses the lookahead when the
entering year is the bridge); every re-screen consumes the lookahead. Measured on the 29-unit /
8,218 MW coal cohort: decide $22.4/kW-yr vs $58.5 bar (raw object, p_mean $29.38); reverse
$341.5 — 6x the bar, 100% energy leg (lookahead object, p_mean $65.38 vs raw-2023 $15.77);
consistent-basis counterfactual $1.3/kW-yr, 0/29 clear. Reserve leg $0.0 at BOTH screens —
adjudicated, not a suspect. The as-built lookahead's level defects (§2a): (i) the stack is
THERMAL-ONLY — storage never enters; (ii) net load subtracts PRIOR-YEAR VRE OUTPUT, not
entering-year capacity; (iii) capacity is derated by TIME-MEAN availability applied to peak
hours. Jointly they manufacture 122 pro-forma scarcity hours (>$200; 88 h >$1000, max $5000) on
a 34.8%-RM fleet, so every fuel clears its bar by 4-13x and nothing ever retires. Neither
current object resolves the real 1.534 GW of 2023-25 ERCOT exits (raw fails the whole 66.9 GW
merchant fleet; lookahead fails no one). FFR-4A/FFR-5C's pipeline-awareness is the FOURTH gap,
already landed by #3577 — do not re-implement it; compose with it.

=== WHAT YOU LAND ===
1. ONE gated field (name it — e.g. capacity_screen_unified_lookahead — justify in the
   docstring), DEFAULT OFF, in run_config.json (rule 24), matrix row in the SAME PR (rule 28c).
   OFF => byte-identical shipped behavior, proven by a regression test over the capacity-
   evolution path.
2. UNIFICATION (armed): every capacity screen consumes the lookahead object for its entering
   year, INCLUDING bridge-adjacent years. Rule-22 compliance is by CONSTRUCTION, not by
   exception: for a bridged entering year the lookahead prices the growth-scaled demand
   fallback the full-forward leg already uses for forward years (FFR-5A §2a) — zero measured
   reads of the bridged year. The bridge guard's rule-22 PURPOSE stays satisfied; what changes
   is that the screens no longer fall back to a different OBJECT there. Do not remove any
   quarantine assertion — the no-read contract is re-verified in your paired runs.
3. REPAIRS (armed), each from EXISTING model state, zero new tunables: (i) storage enters the
   stack (power caps from the evolved storage fleet, with an energy/duration-limited treatment
   derived from already-carried storage parameters); (ii) entering-year VRE capacity (the
   evolved fleet's wind/solar MW x the model's own CF basis) replaces prior-year realized
   output; (iii) peak-hour-appropriate availability (the outage model's hourly availability
   already exists — use its peak-window values, not the annual time-mean). IF any repair cannot
   be built without inventing a parameter, STOP on that repair and escalate it — land the rest.
4. PAIRED-ARM MEASUREMENT on the FFR-5A posture (ERCOT T1-FF, vintage 2020, window 2021-2025,
   Arm R, shipped defaults otherwise; FFR-5A §1 records the exact invocation): shipped vs
   armed. PRE-REGISTER the reads BEFORE solving: (a) the cohort's event sequence
   (decided/re_confirmed/reversed/executed); (b) the enriched pipeline_events bar decomposition
   (FFR-5A's ledger fields — they persist; use them, do not re-instrument); (c) the fleet-wide
   entry_capped census; (d) scored thermal exits vs the 1.534 GW actual. STATE THE HONEST
   EXPECTATION: the armed arm may STILL not resolve real exits — that is a finding, not a
   failure, and no repair may be tuned toward 1.534 GW (rule 1). Two invocations max
   (shipped/armed), 4 LP years each, sequential, cold.
5. Register both arms to frontend/data/hindcast/ (register_hindcast.py, slim files,
   meta.kind="full_forward", ids ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}) — evidence,
   expected to be superseded when keepers settle (Q.2). NEVER the backcast registry.
6. LOYO 2023-2025 discipline: this lane arms nothing; any future promotion/arming decision
   scores leave-one-year-out first (rule 22) — say so in the handoff so the next session
   inherits the duty.

=== RULES THAT BIND HARDEST ===
Rule 1 [R-STRUCT]: no repair is tuned toward the exit residual; the repaired level is a
measurement. Rule 19 [R-ONE-MECH]: one object, one gate; do not leave a second screen-price
path armed anywhere. Rule 22: the bridge stays unsolved and unread — your unification changes
the OBJECT, never the data diet. Rule 23: repairs derive from model state/source data, never
from a residual. Rule 24: one field, registered. Rule 27: runner.py is core — edit locally,
push exact bytes, verify blobs. Rule 28: matrix row in the same PR; stamp any cell your paired
arms adjudicate, rejections included. FH-4/FH-5: the lift is a MANAGER box (Addendum I.1); you
report, you do not lift.

=== TRAPS ===
Push 413: `git fetch origin main` + rebase FIRST; `git remote prune origin` for stale refs.
Never push_files a >=300-line file. Cache-purge deletes TRACKED files — `git status --short`
after; `git checkout origin/main -- <path>` STAGES — `git restore --staged`. Shell cwd
persists. MARKET_SIM_DATA_ROOT outside REPO_ROOT shifts the key. Recorded key = runtime
`cache_key=` line, not request-side. Evolution ledgers at <out-dir>/<ISO>/<cache_key>/;
load_ledgers_for_run returns {} on a wrong path; decided_year is on the event rows, not the
ledger year. Stop-hook on merged history: rev-list count 0 => nothing to amend.

Deliverable: the PR (field + unification + repairs + tests + matrix row) and
docs/handoffs/ffr-5d-price-object-<date>.md — the byte-identity proof, the paired-arm
pre-registered reads with the bar decompositions, what the armed object does to the cohort AND
to real-exit resolution, which repairs landed vs escalated, and what you did NOT separate.
```

### FFR-5E [OPUS] — the near-term VRE procurement channel (D-18(a))

```
[OPUS] FFR-5E — Implement the near-term VRE procurement channel (owner decision D-18(a),
sitting Addendum S.2/S.5, signed 2026-08-05). IMPLEMENTATION lane (Wave 5) for FFR-5B's
recommended design — the design doc IS the spec; implement it, do not redesign it:
docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md §§2-3 (mechanical seam,
composition, gates) with §5.1 the admissibility contract. Default OFF; arming anywhere,
including MISO, is a SEPARATE owner decision (rule 25).

=== VERIFIED STATE (2026-08-05 @ origin/main 5543c4c0 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ the shards YOURSELF): ERCOT 2026-08-04-ercot165-unpooled-share · PJM
2026-08-04-pjm-152-collapse · CAISO 2026-08-05-caiso-174-measured-fleet · NYISO
2026-08-04-nyiso-125-seam-envelope · NEISO 2026-08-05-neiso-83-ca1-reclass · MISO
2026-08-04-miso-127-onlinepmin.
Markers: `complete` = {NEISO, NYISO, PJM} at dispatch (a concurrent governance lane executes
the signed CAISO grant — re-read at your head); `final` = EMPTY. HOLDOUT FREEZE ACTIVE. Marker
and freeze orthogonal (caiso-171). Forecast-mode 2026+ is unrestricted; NEVER a 2022/2019/
H1-2026 backcast or scoring against their actuals.
PREREQUISITES: `uv sync` FIRST (~2 min). regenerate_clean.py (~63-65 min) only if your
measurement solves; the channel's data path reads committed data/raw/eia-860 vintages directly.
Rule 12 PER PROMPT: <=5 solve-years per invocation, years sequential, <=2 concurrent. Rule 27:
OPUS/FABLE (src/ capacity-evolution is core).

=== STEP 0 — PRECONDITION AND LANDED-CODE RE-READ ===
1. PR #3577 (FFR-5C) MUST BE MERGED before you branch — it changes the entry budget netting
   your §2.3 composition nets against. If still open, STOP and report.
2. Re-read new_entry.py's budget code AS LANDED (entry_pipeline_aware_signal exists now) and
   FFR-5B §2.3's composition rule against it: the channel's current-year commissioning flow is
   netted from the economic screen's budgets AS A FLOW (MW commissioning in year Y against year
   Y's caps) — it must NOT recreate the stock-from-flow netting FFR-4A diagnosed and D-17
   removed. If the landed 5C shape makes §2.3 ambiguous, escalate to the manager with the exact
   seam rather than guessing.

=== THE DESIGN YOU ARE IMPLEMENTING (FFR-5B; do not re-derive, do not widen) ===
One field: `vre_procurement_additions_enabled: bool = False` (forecast-mode-only). Data: the
run's own EIA-860 vintage's proposed-generator sheet, construction-committed statuses U/V/TS
ONLY (the status set is a cited code constant; eia860.py already excludes P by name), through
the EXISTING vintage information gate (active_eia860_dir + Effective Year >
operable_vintage_year). Zone-assigned MW into `renewable_additions`; every MW tagged
source:"procured" (the §3.5 attribution requirement — additions must be scoreable by channel);
the channel falls SILENT past the data horizon (empty pipeline past V+4 is correct behavior,
not a bug). Zero free parameters — the whole registry surface is the one gate flag + the
existing data path (FFR-5B §2.5), and any expansion of that surface is visible against the
design doc by construction.

=== GUARDS YOU CARRY (the card's teeth) ===
1. THIS DOES NOT CLOSE MISO's 18.649 GW, BY DESIGN: a vintage-2020 hindcast may see 1.034 GW
   committed. Your handoff says so before any number. Anyone widening the status set, vintage,
   or horizon to improve MISO has spent the guard (rule 1 arriving as a status filter) — the
   signed card explicitly REFUSED option (b).
2. HINDCAST ARM BLOCKED: FFR-3V §6.1 (hindcast renewable pools seed from the canonical
   constant, MISO solar 7,000 vs 2,056 MW actual at vintage 2020) must close before ANY
   hindcast measurement of this channel, or injected MW double-count invisibly. Do NOT run a
   hindcast arm; state the block. Plain 2026+ forecast measurement is unaffected.
3. Measurement: shipped vs armed paired control at your own base commit, the cheapest honest
   instrument — prefer exercising the evolve/step-4 path directly (the FFR-4A harness pattern);
   a bounded 2026+ MISO forecast pair is permitted if you need the full loop (<=5 solve-years
   per invocation; register any full runs to frontend/data/forecast/ via
   register_forecast_run.py, NEVER the backcast registry, noting Q.2 supersession). No keeper
   contact, no default flip, no ISOConfig override.
4. Matrix row for vre_procurement_additions_enabled in the SAME PR (rule 28c — CI enforces);
   stamp any cell your measurement adjudicates, rejections included.

=== RULES THAT BIND HARDEST ===
Rule 13 [R-MEASURED]: the channel reads the proposed sheet (filed BEFORE outcomes), never the
operable sheet (the outcome) — §3.1's instrument gate is the admissibility boundary; crossing
it anywhere fails the lane. Rule 14: face-value U/V/TS, no realization multiplier (§3.4 option
(a) — a realization treatment would be a future frozen-derive with its own citation, not this
lane's). Rule 19: the channel is step-4's VRE limb — it must not become a second ladder or a
second netting. Rule 23: nothing derives from a residual. Rule 24: one field, registered.
Rule 25: no arming. Rule 27: exact bytes, blob verification. Rule 28c.

=== TRAPS ===
Push 413: fetch main + rebase first; prune stale refs. Never push_files a >=300-line file.
Cache-purge deletes tracked files. Shell cwd persists. Stop-hook on merged history: rev-list
count 0 => nothing to amend. The D-13 hash-out hazard (FFR-5A §1): same cache key does not
imply byte-identity across the D-13 boundary — never reuse a pre-D-13 warm dir.

Deliverable: the PR (field + channel + source attribution + tests + matrix row) and
docs/handoffs/ffr-5e-vre-procurement-channel-<date>.md — the byte-identity proof, the paired
measurement, the §2.3 composition statement against the landed 5C netting, the hindcast-arm
block statement, and what you did NOT separate.
```

### CAISO-GRANT [OPUS] — execute the signed CAISO `complete` declaration

```
[OPUS] CAISO-GRANT — Execute the CAISO `complete` declaration (owner-signed 2026-08-05,
sitting Addendum S.4/S.5 — cite this as the session-logged authorization). GOVERNANCE lane:
committed artifacts only, NO solve, NO scoring, NO year touched, NO dashboard run produced.
The freeze is untouched and stays active; the grant authorizes CAISO's validation ladder and
NOTHING else; `final` is not touched.

=== VERIFIED STATE (2026-08-05 @ origin/main 5543c4c0 — RE-VERIFY AT YOUR OWN HEAD) ===
CAISO keeper: 2026-08-05-caiso-174-measured-fleet (READ frontend/data/backcast/keepers/
CAISO.json yourself; if it has moved again, STOP and report to the manager — the grant is
keyed to the keeper the recommendation was made on, and a newer keeper needs a fresh
determination check, not a silent re-key). Markers: `complete` = {NEISO, NYISO, PJM}; `final`
EMPTY; holdout-freeze.json ACTIVE. Basis on record: caiso-171 (assessment YES, criterion per
Addendum P.6), caiso-172 (closed the one gating item, PGE-TAC weight, MEASURED), caiso-174
(PR #3578: FFR-4D epoch re-solved, keeper on the measured fleet, `complete` re-recommended
YES). PREREQUISITES: `uv sync` (~2 min) for the verdict/audit scripts; regenerate_clean.py NOT
needed.

=== WHAT YOU DO, IN ORDER ===
1. READ the NYISO and PJM `complete` entries in
   frontend/data/backcast/calibration-complete.json — they are your TEMPLATE. The file's own
   note documents the field contract; D-5(b) (Addendum C.1) defines `keeper` (current,
   re-keyed on promotion) vs `keeper_at_declaration` (frozen at declaration).
2. VERIFY THE DETERMINATION without a solve:
   `uv run python scripts/calibration_verdict.py --run-id 2026-08-05-caiso-174-measured-fleet`
   (committed artifacts only). Record its determination verbatim in the entry. If the script
   fails or the run's committed bundle is incomplete, STOP and report — never hand-write a
   determination.
3. WRITE the CAISO entry: keeper = keeper_at_declaration = 2026-08-05-caiso-174-measured-fleet;
   the verified determination; declaration date 2026-08-05; authorization citation (sitting
   Addendum S.4/S.5); a `locked_test` note reading "never authorized" (CAISO's locked test is
   NOT granted by this — absence from `final` with this note is the contract). Do not touch any
   other ISO's entry, the freeze file, or `final`.
4. RUN `uv run python scripts/audit_keepers.py --iso CAISO` (M1 must pass) and
   `scripts/check_mechanism_matrix.py` (should be untouched — you change no cell; a warning
   delta means you did something wrong).
5. One-line record in docs/calibration-log/caiso.md citing the grant + authorization; commit
   everything in ONE small commit; push (fetch main + rebase first); verify the pushed
   calibration-complete.json blob matches local.

=== WHAT THIS DOES NOT DO ===
No 2022 solve/score/registration — the FREEZE IS ACTIVE and outranks the marker
(holdout-freeze.json's own text); the grant stores the authorization the freeze suspends.
No keeper change, no dashboard run, no matrix cell. Rule 22's tier map is unchanged.
If ANY check above fails, report the failure — do not improvise a repair.

=== TRAPS ===
Push 413: fetch main + rebase first. calibration-complete.json is small — push_files is
acceptable for it, but the one-commit git push path is preferred since audit outputs may touch
nothing else. Shell cwd persists. Stop-hook on merged history: rev-list count 0 => nothing to
amend.

Deliverable: the merged commit + a SHORT note docs/handoffs/caiso-complete-grant-2026-08-05.md
recording the verified determination, the M1 pass, and the citation chain
(caiso-171 → caiso-172 → caiso-174 → Addendum S.4/S.5).
```

**§0l post-script (same session, minutes later):** PR #3577 MERGED at `f664d37c` while this
section was being pushed — FFR-5D/FFR-5E's step-0 precondition is ALREADY SATISFIED; the
verification step in each prompt now passes trivially. Dispatch all three immediately.

## §0n — §0l prompts RE-DISPATCHED after owner confirmed they were never pasted (2026-08-05 @ `70acd78c`)

The §0m manager continuation session re-verified state end-to-end and asked the owner about
the silent canary (CAISO-GRANT: zero evidence >1 h after the §0l dispatch — no branches, no
PRs open or closed, no handoffs, CAISO absent from `complete`). **Owner answer: the §0l
prompts were never pasted into sessions.** All three (FFR-5D, FFR-5E, CAISO-GRANT) were
re-dispatched in chat, verbatim from §0l, each with the following dated note prepended inside
the block (recorded here so the pack matches what was dispatched):

> [RE-DISPATCH NOTE 2026-08-05, manager, @ origin/main 70acd78c — supplements the VERIFIED
> STATE header below, which is retained from the original 5543c4c0 dispatch: ERCOT keeper is
> now 2026-08-05-run167b-soc-reserve (ercot-167 promotion, PR #3580); the manager verified
> ercot_storage_as_soc_reserve and every ercot_storage_as_* sibling ships default False at
> this HEAD, so the SHIPPED posture (and FFR-5D's paired-arm comparability) is unchanged.
> CAISO keeper verified still 2026-08-05-caiso-174-measured-fleet — the CAISO-GRANT
> precondition holds. PR #3577 is merged; step-0 passes. All other header state re-verifies
> unchanged; re-verify at your own head as ordered.]

Re-verification results backing the note (all read at `70acd78c`, 2026-08-05):
- **§0m check (a) PASS:** `ercot_storage_as_soc_reserve: bool = False` (scenarios.py:6044)
  and all `ercot_storage_as_*` siblings default False/off. The run167b promotion moved keeper
  JSON only — no shipped default flipped. No stop-the-line for FFR-5D.
- **§0m check (b) PASS:** CAISO keeper shard reads `2026-08-05-caiso-174-measured-fleet`.
- Keepers otherwise as §0m; `complete` = {NEISO, NYISO, PJM}; `final` EMPTY; freeze ACTIVE.
- Landed since §0m was written, both outside the FFR/FH lanes: nyiso-127 REJECTED at kill
  gate K3 (PRs #3584/#3586, keeper stays nyiso-125) and miso-131 dead at prerequisite 1,
  zero solves (PR #3585).
- **New trap for future sessions:** these containers are SHALLOW clones (`.git/shallow`, 7
  graft boundaries). `git fetch` may report a spurious "(forced update)" on main and
  merge-base/ancestry queries return garbage (this session measured contradictory answers).
  Never diagnose a history rewrite from a shallow clone — check `git rev-parse
  --is-shallow-repository` first.

## §0m — MANAGER CONTINUATION HANDOFF (written 2026-08-05 ~06:25Z @ `b4581c49`)

The predecessor manager session (Addenda R/S) ends here. The block below is the continuation
prompt for the NEXT manager session — re-issue it verbatim. It supersedes the pre-R manager
handoff as the current manager brief; the decision record itself remains
`docs/handoffs/ffr-owner-sitting-2026-08-02.md`.

```
[FABLE] FFR/FH WORKSTREAM MANAGER — continuation session

You are the workstream manager for two coupled programs in /home/user/market-simulator: the FFR
forecast-readiness remediation waves and the Wave FH forward-mode hindcast program. You dispatch
parallel session prompts to the owner, track lane state, run wave-close checklists, put owner
decision cards, and keep the owner-decision record honest. You do NOT execute lane work
yourself.

=== READ FIRST, IN THIS ORDER ===
1. CLAUDE.md — the 28 non-negotiable rules. Rules 1, 11, 12, 13, 14, 15, 19, 22, 23, 24, 25,
   27, 28 bind every prompt you write.
2. docs/handoffs/ffr-owner-sitting-2026-08-02.md — THE DECISION RECORD. READ ADDENDA C THROUGH
   S BEFORE THE PACKET BODY; they supersede it. ~45 decisions are signed across them. J.1, L.3
   and P.1 are MANAGER ERROR CORRECTIONS, and R.1 + S.1 are the measure-don't-inherit standard
   applied to a predecessor's own handoff — read all five as worked examples of the standard
   you are held to. S is the newest: the Wave-5 refresh sitting (FFR-5A/5B adjudications,
   D-18(a)/D-19(a)/CAISO-grant signatures).
3. docs/forecast-readiness-prompt-pack-2026-07.md — the execution vehicle. Read state deltas
   §0a→§0m newest-LAST. §0l carries the three IN-FLIGHT lane prompts and the "#3577 merged"
   postscript. Dispatch FROM this file; WRITE every prompt you dispatch INTO it.
4. docs/forecast-readiness-audit-2026-07.md (FR-1..FR-27, the WHY) and
   docs/forecast-readiness-peer-review-2026-07.md §4 (standing disclosures).
5. Wave-5 evidence, all landed 2026-08-05: ffr-5a-soft-latch-2026-08-05.md (the price-object
   root cause), ffr-5b-procurement-channel-design-2026-08-05.md (the partition + card D-18),
   ffr-5c-entry-cap-fix-2026-08-05.md (entry_pipeline_aware_signal). Wave-4 docs are
   background.

=== VERIFIED STATE — origin/main b4581c49, 2026-08-05 ~06:20Z. RE-VERIFY BEFORE DISPATCHING. ===
Main advanced ~20 merges during the predecessor's ~5.5-hour session and the ERCOT keeper moved
DURING the writing of this handoff. Never quote state from a doc, including this one. Check
docs/handoffs/ AND the PR list (open AND closed) — sessions merge without announcing and merged
branches are deleted, so `git branch -r` is not an activity signal. ZERO OPEN PRs DOES NOT MEAN
NOTHING IS RUNNING: a solve session burns ~65 min on prerequisites before it pushes. Report
"no evidence yet", never "not running".

Keepers (READ frontend/data/backcast/keepers/<ISO>.json YOURSELF): ERCOT
2026-08-05-run167b-soc-reserve (moved ~06:15Z with PR #3580 — the ercot-167 storage-AS
SOC-reserve arm) · PJM 2026-08-04-pjm-152-collapse · CAISO 2026-08-05-caiso-174-measured-fleet
· NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO 2026-08-05-neiso-83-ca1-reclass · MISO
2026-08-04-miso-127-onlinepmin.

Markers: `complete` = {NEISO, NYISO, PJM}. THE CAISO GRANT IS OWNER-SIGNED (Addendum S.4/S.5)
BUT NOT YET EXECUTED — the CAISO-GRANT governance lane writes it; watch for CAISO appearing in
`complete`. NEISO's `complete` entry is correctly re-keyed to neiso-83 (D-5(b) executed by the
promoting session; verified in S). `final` = EMPTY; NEISO's locked test has **NEVER BEEN
GRANTED** (*corrected 2026-08-06, owner decision D-23 — this read "is SPENT, never
re-grantable"; the artifact record carries no NEISO 2019/H1-2026 solve of any kind. `final`
stays EMPTY and the correction grants nothing; citation chain
`results/calibration/ASSESSMENT-neiso87-declaration-2026-08-06.md` §1 →
`docs/third-party-peer-review-2026-07.md` §6.3 item 1 → D-23 / sitting Addendum X.6*).
HOLDOUT FREEZE ACTIVE — it blocks out-of-training BACKCAST solve/score/
registration only; forecast-mode 2026+, the T1 windows, and in-sample 2023-2025 are unaffected.
THE MARKER AND THE FREEZE ARE ORTHOGONAL (caiso-171): a freeze SUSPENDS what a marker grants;
NYISO and PJM were declared complete six days INTO the freeze. Any session reasoning otherwise
has it backwards; say so.

CACHE: epochs 2026-08-02 / 2026-08-03b / 2026-08-04 (D-10: warm-start OFF for forecast
bundles — deliberate). results/ is gitignored — fresh containers solve COLD; "expect cache
hits" is never a valid budget. NEW HAZARD (FFR-5A §1): D-13's `ira_ptc_credit_window_years`
hashes OUT at its shipped default, so an IDENTICAL cache key spans behaviorally different
configs across the D-13 boundary — never reuse a pre-D-13 warm dir, never read byte-identity
into "same key".

TWO PREREQUISITES for every solve lane, IN ORDER: `uv sync` FIRST (~2 min — the container
ships NO Python environment; skipping it makes regenerate_clean.py report "50/50 datatype(s)
failed", which reads exactly like a data problem and is not one), THEN
scripts/regenerate_clean.py (~63-65 min, 50 datatypes, 1.6 GB).

=== THE OWNER'S STANDING INSTRUCTION (Addendum Q.2) — UNCHANGED AND BINDING ===
BUILD MECHANISMS AND ARCHITECTURE. DO NOT COMMISSION WORK A KEEPER PROMOTION INVALIDATES.
Keepers moved constantly through Waves 3-5 and not one lane was re-run for it. What a
promotion invalidates is a registered forecast/hindcast RUN (scripts/check_forecast_parity.py
resolves the CURRENT keeper). Do NOT commission a full T1-H / T1-X / T1-FF battery
re-measurement until keepers settle. A run-producing lane is chartered only when its question
has no committed-artifact answer — FFR-3Q-3, FFR-5A and FFR-5D all qualified on that test.

=== IN FLIGHT — YOUR FIRST TRACKING DUTY ===
Three lanes dispatched 2026-08-05 ~05:00-05:20Z (complete prompts: pack §0l, ON MAIN):
- FFR-5D [FABLE] — D-19(a): unify the capacity screens on the lookahead price object AND
  repair its level (storage into the stack; entering-year VRE capacity; peak-hour
  availability), ONE gated default-OFF field, paired arms on the FFR-5A posture, registered to
  the hindcast namespace. THIS IS THE FH-4/FH-5-RELEVANT MEASUREMENT.
- FFR-5E [OPUS] — D-18(a): the near-term VRE procurement channel
  (vre_procurement_additions_enabled, U/V/TS statuses, step-4 limb; FFR-5B's design doc IS the
  spec). Its HINDCAST arm is BLOCKED by FFR-3V §6.1 until that closes; plain 2026+ forecast
  measurement is unaffected.
- CAISO-GRANT [OPUS] — execute the signed `complete` declaration keyed to
  2026-08-05-caiso-174-measured-fleet (calibration_verdict.py --run-id, committed artifacts,
  never a solve; audit_keepers M1 after). THE CANARY: needs only `uv sync`, should push within
  ~30 min of starting.
AS OF 06:20Z: NO EVIDENCE FROM ANY OF THE THREE — no branches, no PRs, no handoffs, CAISO not
in `complete`. The canary's silence suggests the prompts may not have been pasted yet: ASK THE
OWNER rather than assume, and re-send from §0l if needed. The step-0 precondition (#3577
merged) is satisfied on main (f664d37c).
TWO CHECKS THAT ARE YOURS, NOT THE LANES':
(a) The §0l prompts embed the PRE-run167b ERCOT keeper in their state headers — harmless by
    design (every prompt orders re-verification), but run the R.1-style check yourself: verify
    ercot-167's new fields (ercot_storage_as_soc_reserve and any siblings) landed default-off/
    neutral in scenarios.py, so the SHIPPED posture the in-flight lanes inherit is unchanged by
    the promotion. If a shipped default DID flip, that is stop-the-line for FFR-5D's paired-arm
    comparability — measure first, then decide.
(b) The CAISO-GRANT prompt orders a STOP if CAISO's keeper has moved off caiso-174. It has NOT
    as of this writing — re-verify at your head; if a caiso-175 lands first, the grant needs a
    fresh determination check, never a silent re-key.

=== DONE — DO NOT RE-DISPATCH, DO NOT RE-LITIGATE ===
FFR Waves 1 and 2 (12/12), Wave S, Wave 3 (all lanes), Wave 4 (4A/4B/4C/4D/4E + 3Q-3) all RAN.
Wave 5: FFR-5A, FFR-5B, FFR-5C all LANDED AND MERGED. The T1 battery is CLOSED, scored and
registered. ~~FFR-3Q-2~~ was STRUCK (Addendum L.3) and must never be run.

=== ADJUDICATED SINCE Q — cite, never re-derive, NEVER RE-SUSPECT ===
- FFR-5A: the soft-latch reversal is ROOT-CAUSED. The bar's PRICE OBJECT changes between
  screens — decide screens are bridge-adjacent and consume raw duals + overlay (the rule-22
  guard suppresses the lookahead there); every re-screen consumes the lookahead stack-reprice
  (mean $65.38/MWh vs raw $15.77). On a consistent basis there is NO reversal. THE RESERVE-LEG
  SUSPECT IS DEAD ($0.0/kW-yr at both screens). The latch's logic matches its design record;
  its INPUT was the defect. Hysteresis is MOOT (no band < $283/kW-yr survives a 6×-bar
  clearance). NEITHER consistent basis resolves the real 1.534 GW of ERCOT exits — raw duals
  fail the whole 66.9 GW merchant fleet, the as-built lookahead fails no one; the pipeline's
  output was determined by bridge geometry, not unit economics. Reproduced at HEAD on the
  recorded key 6a824992b5fb1baf.
- R.1: FFR-3Q-3 stands as-measured at base 68e7bfcd (a stated limitation, not a
  keeper-insensitivity claim); the ercot-165 promotion moved no shipped default.
- FFR-5B: D-16's gap PARTITIONS. Near-term committed procurement = real missing mechanism,
  rule-13 ADMISSIBLE (→ D-18). Long-run policy procurement = REFUSED a channel (rule 19); the
  real defect is the RPS LP row's SPATIAL GRAIN (one ISO-wide row against a load-weighted
  state blend dilutes binding statutes to slackness) → escalations E-1/E-2, UNCHARTERED.
  Corporate-PPA / beyond-horizon residual = NO admissible representation; disclosed null;
  sizing it is a cheap committed-artifact follow-up.
- The FFR-4A chain is CLOSED: D-17 → FFR-5C landed entry_pipeline_aware_signal (default-OFF,
  matrix row, byte-identity proven).

=== SIGNED DECISIONS — cite Addendum + item, never re-derive ===
Everything in the pre-R register stands: D-1/D-2 armed with Addendum D's HOLD PROMOTION (the
one unarming exception is an explicitly-labelled paired control), D-3 series, D-4, D-5(a-c)
with D-5(b) RE-KEY ON PROMOTION, D-6, D-7, D-8 + F.2 (rule 12 is PER PROMPT), D-9(ii)
COD-shifted scoring, D-10 warm-start override, D-11 discharged, D-12 + D-2' MISO-scoped, D-13
statutory PTC window, D-14, D-15, the NUCLEAR BOX (DB-A ignore licences; DB-C
regulatory_order the only exogenous nuclear exit). New this cycle, all signed 2026-08-05:
D-16(a) scoping → FFR-5B RAN. D-17(a) → FFR-5C RAN. D-18(a) VRE channel → FFR-5E chartered.
D-19(a) lookahead unify+repair → FFR-5D chartered. CAISO `complete` GRANTED → CAISO-GRANT
chartered. Consequences are recorded once in R.5/S.5 — a lane that re-opens them has misread
the record.

=== STOP-THE-LINE, STANDING ===
FH-4/FH-5 ARE BLOCKED AND ONLY A MANAGER LIFTS THEM (Addendum I.1). Refused FOUR times;
current determination Q.1 plus S.5's rider: the exit half of the retirement layer cannot be
validated until D-19(a)'s work (FFR-5D) lands AND its measurement shows the exit path
exercisable on a defensible object. FFR-5D reporting green does not lift. A cohort executing
under the unified object is NECESSARY evidence, not sufficient — adjudicate against Addendum
G.2's three binds (a control that flips identically is not the fix's green; watch inverted-sign
invariants; vacancy is not validation).

=== OPEN QUEUE ===
1. Track the three in-flight lanes to landing; adjudicate each (matrix stamps, registration
   hygiene, handoffs); run the Wave-5 close when all three are in. Record in Addendum T.
2. After FFR-5D's measurement: the FH-4/FH-5 lift determination is YOURS.
3. FFR-5B E-1/E-2 (RPS row spatial grain + clean/carbon-free tiers) — "the largest single
   finding in this lane"; put the scoping card at the owner's next sitting. E-1 and E-2 settle
   TOGETHER, not separately.
4. FFR-5B §5.4 residual sizing — cheap, committed-artifact, manager-charterable.
5. FFR-3V §6.1 hindcast renewable-pool vintage leak — BLOCKS FFR-5E's hindcast arm; unowned.
6. FFR-4D row-4: the 52.7 % accreditation-rate/class-boundary half — unowned.
7. The CAISO capacity anchor — D-15 posture unchanged: only on its own rule-14 merits, with a
   charter stating it is not a row-4 fix.
8. Pre-existing test failures on main — unowned.
9. Once CAISO-GRANT executes: D-5(b) applies to every future CAISO promotion; audit M1 runs on
   keeper-shard edits.

=== STANDING CONSTRAINTS FOR EVERY PROMPT YOU WRITE ===
- <=5 solve-years per invocation (owner standing instruction + §2.1b).
- Rule 12 PER PROMPT (F.2): years sequential within an invocation; <=2 concurrent invocations
  within a session; PJM and MISO never co-run in one session (~8.6 GB each). Independent
  SESSIONS do not contend — dispatch as many as you like.
- Rule 27: FABLE or OPUS only for src/market_sim/, scripts/run_*|score_*, CLAUDE.md, the spec,
  .github/workflows/. Managers are FABLE.
- Registration: forecast → frontend/data/forecast/ via register_forecast_run.py; T1-FF →
  frontend/data/hindcast/ with meta.kind="full_forward". NEVER the backcast registry.
- Rule 28: the session that tests a mechanism updates its matrix cell + citation in the SAME
  session, rejections included; a new ScenarioConfig field needs its row in the same PR (CI
  enforces).
- No new GitHub Actions workflows for tasks (private repo, billed minutes).

=== KNOWN TRAPS — PASS THESE INTO EVERY PROMPT ===
- PUSH 413 HAS TWO CAUSES: stale tracking ref of a deleted merged branch (`git remote prune
  origin`) and a stale local origin/main defeating delta compression (`git fetch origin main`
  + rebase; measured 647 KB → 21 KB). FETCH MAIN BEFORE DIAGNOSING.
- NEW (predecessor session, twice): the owner merges manager-branch PRs FAST and the merge
  deletes the remote branch — a later `git push --force-with-lease` then fails "stale info".
  Fix: `git remote prune origin`, rebase onto fresh main, plain `git push -u` recreates the
  branch. Rebase before EVERY push; main moves several times an hour.
- Never push_files a >=300-line file (string-content full-file rewrite — rule 27's forbidden
  act). The documented cache-purge command deletes TRACKED files — `git status --short` after
  any purge. `git checkout origin/main -- <path>` STAGES — `git restore --staged` after.
  Shell cwd persists between Bash calls. The stop-hook flags unverified commits on
  already-merged shared history: rev-list count 0 ⇒ nothing to amend.
- Evolution ledgers live at <out-dir>/<ISO>/<cache_key>/, never the out-dir root;
  load_ledgers_for_run returns {} on a wrong path — in retirement/entry lanes a silent {} is
  indistinguishable from a real null; VERIFY THE PATH BEFORE BELIEVING A ZERO. decided_year is
  on the event rows, NOT the ledger year (the 2022 ledger carries decided_year=2021 rows).
- A REQUEST-side cache_key() is NOT the recorded key (FFR-3A-2 §1.2) — take it from the
  runtime `cache_key=` log line. MARKET_SIM_DATA_ROOT outside REPO_ROOT shifts the key
  (FFR-3F §5). The D-13 hash-out hazard (above). results/ and forecast bundles die with the
  container.

=== HOW TO WORK ===
- Lead with dispatch, not narration. When the owner says go, emit COMPLETE COPY-PASTE PROMPT
  BLOCKS — one fenced block per session, fully self-contained, verified state EMBEDDED, NOT
  REFERENCED, with model assignments. Never make the owner assemble a prompt from pieces.
- Re-verify before every wave AND before every claim: HEAD, keepers, markers, freeze, PR list
  open+closed, whether a lane already landed. A "not started" claim goes stale in minutes.
- UPDATE THE PACKET IN THE SAME SESSION THAT LEARNS A FACT; write every dispatched prompt INTO
  the pack; CORRECT BY ADDENDUM, never by rewriting an earlier record. Cards and prompts
  delivered only in chat get lost.
- VERIFY, DON'T INFER. J.1, L.3, P.1 record inherited-symptom, guard-level-as-runtime, and
  superseded-number errors; R.1 and S.1 show the standard applied to a predecessor's own
  beliefs. A "do not re-derive" clause covers only claims verified AT THE LEVEL OF THE
  BEHAVIOUR the lane exercises. Read the artifact.
- Write for a reader who does not hold the jargon; spell out what a decision changes before
  naming it.
- Owner decisions: give the MEASURED consequence, NAME YOUR RECOMMENDATION, INCLUDE the option
  you think is wrong with its real cost, offer clickable option cards. If the owner picks
  against you, record it once with its consequence and proceed — no re-litigating.
- Findings-first: no session tunes to close a residual; a keeper moving under a supposedly
  inert change is stop-the-line; a charter whose premise is refuted is the system working
  (FFR-4D, FFR-4E, and miso-131 all did it right).

=== YOUR IMMEDIATE QUEUE ===
1. Re-verify state end-to-end. Start with the two checks in "IN FLIGHT" above: the ercot-167
   shipped-default check (run167b promotion), and the CAISO keeper still being caiso-174.
2. Check the three in-flight lanes for evidence. If the CAISO-GRANT canary is still silent,
   ask the owner whether the §0l prompts were pasted, and re-send them from the pack if not.
3. As each lane lands: adjudicate it, verify rule-28/registration hygiene, record in Addendum
   T; when all three are in, run the Wave-5 close.
4. After FFR-5D's measurement lands: make the FH-4/FH-5 lift determination (I.1 — yours
   alone), against G.2's binds and S.5's rider.
5. Put the FFR-5B E-1/E-2 scoping card at the owner's next sitting.
6. Do NOT commission a T1 battery re-measurement (Q.2). Keepers are still moving — ERCOT moved
   during this handoff's writing.
```

## §0o — Wave-5 adjudication + FFR-5D-M continuation dispatched (2026-08-05 @ `34473b0c`)

All three §0l lanes ran after the §0n re-dispatch. **CAISO-GRANT LANDED CLEAN** (PR #3599 —
CAISO in `complete`, determination scorer-verified, M1 PASS, freeze-outranks proven live).
**FFR-5E LANDED CLEAN** (PR #3602 chain — byte-identity proven against a field-absent base,
netting demonstrated at the MISO queue cap, hindcast arm correctly BLOCKED per FFR-3V §6.1).
**FFR-5D landed its implementation but its paired-arm measurement NEVER RAN** — handoff §3/§4
are empty placeholders and no ffr5d hindcast registrations exist. Full adjudication: sitting
Addendum T. Wave-5 close and the FH-4/FH-5 lift both wait on the measurement below.

NEW STANDING TRAP (from the grant lane, Addendum T.1): the `ruff-autofix.sh` PostToolUse hook
reflows `src/market_sim/config/constants.py` (3,960 → 9,508 lines) on ANY `.py` Write/Edit —
check `git status --short` before staging, restore the file's exact HEAD bytes, never push the
reflow.

### FFR-5D-M [FABLE] — run FFR-5D's pre-registered paired-arm measurement

```
[FABLE] FFR-5D-M — Execute FFR-5D's PRE-REGISTERED paired-arm measurement (continuation of
owner decision D-19(a); charter: sitting Addendum T.3). The implementation is LANDED and
ADJUDICATED (PR #3601 chain): capacity_screen_unified_lookahead (default OFF), the screen
unification, the three level repairs, the matrix row, and the pre-registered reads all sit on
main. Your job is ONLY the measurement half its session never completed: run the two
invocations EXACTLY as pre-registered, execute the committed read-out probe, register both
arms, and fill the handoff's empty §3/§4. You change NO model code, arm nothing, promote
nothing, tune nothing. If the arms surface a code defect, STOP and report to the manager —
do not fix-and-rerun inside this lane.

=== VERIFIED STATE (2026-08-05 @ origin/main 34473b0c — RE-VERIFY AT YOUR OWN HEAD) ===
ERCOT keeper: 2026-08-05-run168b-year-curves — it has moved TWICE since FFR-5D branched
(run167b soc-reserve, then run168b year-curves). The manager ran the R.1-style check at
34473b0c: ercot_storage_as_* and coal_perplant_offer_yearly ALL ship default False, so the
SHIPPED posture your arms inherit is unchanged from the FFR-5A posture. Re-verify at your
head: if any ScenarioConfig default has flipped since, STOP and report before solving —
paired-arm comparability is the lane's foundation.
Markers: `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY; HOLDOUT FREEZE ACTIVE (the
2026-08-05 lift was spent and RE-ARMED — PJM/NEISO 2022 only, an owner act, done). This
lane's T1-FF window is legal by the enumerated carve-out; ERCOT holds no marker and needs
none; 2022 is BRIDGED — never solved, its measured data never read.
Cache epochs 2026-08-02/03b/04; results/ gitignored — COLD solves, no cache budget. D-13
hash-out hazard: identical cache key does NOT imply byte-identity across the D-13 boundary.
PREREQUISITES IN ORDER: `uv sync` FIRST (~2 min), THEN scripts/regenerate_clean.py
(~63-65 min, 50 datatypes — budget for it). Rule 27: FABLE/OPUS; this lane writes docs +
frontend/data/hindcast/ + probe outputs only.

=== WHAT YOU RUN (pre-registered in docs/handoffs/ffr-5d-price-object-2026-08-05.md §2 —
run VERBATIM, no flag added or dropped) ===
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-shipped

uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr5d-unified

Rule 12 (F.2, per prompt): the TWO invocations MAY run as concurrent background jobs (<=2);
years are sequential WITHIN each invocation (the runner does this — do not parallelize the
year loop). 4 LP years each (2022 bridged). Take each run's cache key from its runtime
`cache_key=` log line, never from a request-side cache_key() call.

=== THE READS (fixed BEFORE the original session solved — read, do not re-decide) ===
Execute scripts/probes/ffr5d_paired_arm.py against both out-dirs. The four reads are handoff
§2 (a)-(d): (a) coal-cohort event sequence (decided/re_confirmed/reversed/executed by ledger
year — decided_year is ON THE EVENT ROWS; ledgers live at <out-dir>/ERCOT/<runtime-key>/,
and a silent {} from a wrong path is indistinguishable from a real null — VERIFY THE PATH
BEFORE BELIEVING A ZERO); (b) the enriched pipeline_events bar decomposition (FFR-5A's
persisted ledger fields — no re-instrumentation); (c) the fleet-wide entry_capped census;
(d) scored thermal exits vs the 1.534 GW actual.
THE HONEST EXPECTATION IS ALREADY ON RECORD (handoff §2, committed before solving): the
armed arm may STILL not resolve the real exits — whatever it shows is a FINDING, not a
failure, and NO repair may be tuned toward 1.534 GW (rule 1). If the cohort still reverses,
or nothing ever fails, or everything fails — that number goes to the manager as-is.

=== WHAT YOU DELIVER ===
1. Register BOTH arms to frontend/data/hindcast/ (register_hindcast.py, slim files,
   meta.kind="full_forward", ids ercot-2021-2025-t1ff-armr-ffr5d-{shipped,unified}) — NEVER
   the backcast registry. Evidence runs, expected to be superseded when keepers settle (Q.2).
2. Fill handoff §3 (measured results: the four reads, both arms, side by side) and §4
   (governance position) by APPENDING under the existing placeholder lines — nothing above §3
   changes (pre-registration integrity: the §2 expectations must remain verifiably
   pre-solve). State explicitly which shipped-expectation reproductions held (§2a/§2c) — a
   shipped arm that does NOT reproduce FFR-5A's recorded values is stop-the-line evidence of
   drift, report it before interpreting the armed arm.
3. Rule 28(b): stamp any matrix cell your arms adjudicate (the row exists — no new field).
4. A SHORT report to the manager: the four reads, whether G.2's three binds have anything to
   say (a control that flips identically is not the fix's green; watch inverted-sign
   invariants; vacancy is not validation), and NO lift recommendation — the FH-4/FH-5 lift
   determination is the MANAGER'S (Addendum I.1), not this lane's.

=== TRAPS ===
NEW: the ruff-autofix PostToolUse hook reflows src/market_sim/config/constants.py on ANY .py
Write/Edit (3,960 -> 9,508 lines) — after writing any Python (probe tweaks, scratch
helpers), `git status --short` and restore constants.py to exact HEAD bytes; NEVER stage or
push the reflow (rule 27). Push 413: fetch main + rebase first; prune stale refs; the owner
merges fast and deletes branches. Never push_files a >=300-line file. Cache-purge deletes
TRACKED files. Shell cwd persists. Stop-hook on merged history: rev-list count 0 => nothing
to amend. MARKET_SIM_DATA_ROOT outside REPO_ROOT shifts the cache key. results/ dies with
the container — commit registrations and handoff BEFORE any long tail work.
```

## §0p — FFR-5D-M landed; Wave 5 CLOSED; FH-4/FH-5 lift HELD (2026-08-05 @ `8693b75d`)

FFR-5D-M executed the pre-registered measurement (PR #3611) and was adjudicated CLEAN. The
manager's lift determination (Addendum U.2): **FH-4/FH-5 stay BLOCKED** — G.2 bind 2 fails
(0 → 10.9 GW of the wrong fuel, executed pre-window), bind 3 fails (in-window both arms
execute nothing), and at the repaired price level the admission cap, not unit economics, does
all retention work. Wave 5 is CLOSED (Addendum U.3). Two cards are at the owner: D-20
(repaired-level margin-gap decomposition) and E-1/E-2 (RPS spatial grain + clean tiers,
settled together). Lane prompts follow the owner's signatures — none are dispatched from this
section yet.

**§0p addendum (same sitting):** both cards SIGNED as recommended (Addendum U.5) — D-20(a)
charters FFR-6A, E-1/E-2(a) charters FFR-6B (with the §5.4 residual sizing as a rider).
Wave 6 opens with the two prompts below.

### FFR-6A [FABLE] — decompose the repaired-level margin gap (D-20(a))

```
[FABLE] FFR-6A — Decompose the repaired-level retirement margin gap against the measured
Potomac-SOM net-revenue benchmark (owner decision D-20(a), sitting Addendum U.4/U.5, signed
2026-08-05). MEASUREMENT lane, Wave 6. THE MEASURED FACT YOU START FROM (FFR-5D-M, handoff
docs/handoffs/ffr-5d-price-object-2026-08-05.md §3, probe JSON docs/handoffs/ffr-5d/
paired-arm-probe-2026-08-05.json, registered arms ercot-2021-2025-t1ff-armr-ffr5d-{shipped,
unified}): under the unified+repaired price object the retirement screen fails essentially
the whole ERCOT merchant fleet (entry_capped 554-564 units / 63.0-66.1 GW in 2024/2025), the
adequacy admission cap does ALL retention work, and the model retires 10.9 GW of gas_st
(actual gas_st exits: 0.0) pre-window instead of the real 1.534 GW. Either the screen object
is missing a real revenue leg or the bar is mis-leveled. Your job: say WHICH, with measured
decomposition and an admissibility verdict per candidate fix. You tune nothing, arm nothing,
fix nothing in this lane — the fix is a separate charter on your findings.

=== VERIFIED STATE (2026-08-05 @ origin/main 8693b75d — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ the shards YOURSELF): ERCOT 2026-08-05-run168b-year-curves · PJM
2026-08-04-pjm-152-collapse · CAISO 2026-08-05-caiso-174-measured-fleet · NYISO
2026-08-04-nyiso-125-seam-envelope · NEISO 2026-08-05-neiso-83-ca1-reclass · MISO
2026-08-05-miso-132b-cc-committed (NEW this morning). Markers: `complete` = {CAISO, NEISO,
NYISO, PJM}; `final` EMPTY; HOLDOUT FREEZE ACTIVE (2023-2025 in-sample work and the T1-FF
carve-out unaffected). capacity_screen_unified_lookahead ships default OFF. Wave 5 is
CLOSED; FH-4/FH-5 remain BLOCKED by manager determination U.2 — this lane's output is the
candidate evidence for lift condition (i), and the lift is the MANAGER'S, not yours.
PREREQUISITES: `uv sync` (~2 min). regenerate_clean.py (~63-65 min) ONLY if you re-solve —
prefer not to (below).

=== WHAT YOU MEASURE ===
1. COMMITTED-ARTIFACT-FIRST. The registered ffr5d arms carry the per-screen bar
   decompositions (FFR-5A's persisted ledger fields: energy_margin_usd, reserve_uplift_usd,
   going_forward_cost_usd, screen_price_mean/max, availability, mc, as_pricing) in the probe
   JSON and slim bundles. Build the per-fuel margin-gap table at the repaired level FROM
   THOSE before considering any solve. A re-run of the unified arm (invocation: ffr-5d
   handoff §2, verbatim + its one flag) is permitted ONLY if a read you need was not
   persisted — state which, and budget rule 12 (<=2 concurrent, years sequential, cold).
2. THE BENCHMARK: Potomac/ERCOT State-of-the-Market net-revenue estimates by technology for
   2023-2025 (public, measured; the screen's own cited definition — "Potomac-SOM net
   revenue", CLAUDE.md capacity-evolution step 3). Intake under the data contract if not
   already on disk (data/raw/ + schema; in-sample years only, no authorization needed —
   confirm nothing you intake touches an out-of-training year). Compare, per fuel:
   (i) SOM measured net revenue vs (ii) the shipped screen object's margin vs (iii) the
   repaired screen object's margin vs (iv) the bar (FOM-based going-forward cost, per-fuel
   thresholds).
3. THE DECOMPOSITION QUESTIONS, pre-register your reads before computing:
   (a) Which revenue legs does SOM count that the repaired object lacks (AS/reserve revenue
       at the repaired level? energy uplift? bilateral)? The FFR-5A reserve-leg $0.0
       adjudication was measured on the OLD objects — at the repaired level it is an OPEN
       question, not a settled one; re-measure, don't inherit.
   (b) Is the bar consistent with SOM's going-forward-cost basis (FOM levels, per-fuel
       multipliers), or mis-leveled against it?
   (c) Does the real 2023-2025 SOM data show the actual exits (coal 0.932 / gas_ct 0.502 /
       gas_cc 0.080 GW) as margin-negative units a correct screen COULD have caught — or
       were those exits non-economic (a finding that bounds what any screen can do)?
4. ADMISSIBILITY VERDICT per candidate fix (rules 13/14/23): for each gap term, state
   whether a fix is a reproducible physical/market input with a forward analogue, a
   frozen-derive re-derivation (citing its source-data change), or inadmissible (a level
   knob tuned at a residual — name it as such and refuse it).

=== RULES THAT BIND HARDEST ===
Rule 1: the deliverable is a decomposition, not a better exit number; nothing is tuned
toward 1.534 GW. Rule 13: SOM data enters as a benchmark for VALIDATION of the screen's
completeness, never as an input that pins the screen to actuals. Rule 23: no derive script
changes here. Rule 24/25/28: no new fields, no arming, stamp any cell you adjudicate.
Rule 27: FABLE; if you touch scripts/, exact bytes + blob verification.

=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit
(3,960 -> 9,508 lines) — `git status --short` after any Python write; restore exact HEAD
bytes; never stage the reflow. Push 413: fetch main + rebase first; owner merges fast,
prune stale refs. Never push_files a >=300-line file. Evolution ledgers at
<out-dir>/<ISO>/<runtime-key>/ — a silent {} from a wrong path is indistinguishable from a
real null. results/ dies with the container — commit findings early and often. Shell cwd
persists. Stop-hook on merged history: rev-list 0 => nothing to amend.

Deliverable: docs/handoffs/ffr-6a-margin-gap-decomposition-<date>.md — the per-fuel gap
table (SOM vs shipped vs repaired vs bar), the three pre-registered answers (a)-(c), the
admissibility verdict per candidate fix, and a recommendation card for the owner. NO lift
recommendation — U.2's determination is the manager's.
```

### FFR-6B [OPUS] — E-1/E-2 scoping: zonal RPS grain + clean tiers, settled together (E-1/E-2(a))

```
[OPUS] FFR-6B — Scope the RPS row's spatial grain (E-1) and the clean/carbon-free tiers
(E-2) TOGETHER (owner signature at sitting Addendum U.5, 2026-08-05; the escalation record
is FFR-5B docs/handoffs/ffr-5b-procurement-channel-design-2026-08-05.md §5.3). DESIGN-ONLY
lane on the FFR-5B pattern: NO code, NO ScenarioConfig field, NO schema, NO solve, NO
matrix cell, NO dashboard contact. The deliverable is a design doc + an implementation card
the owner can sign, exactly as FFR-5B produced for D-18. RIDER (second, bounded
deliverable): the FFR-5B §5.4 residual sizing — committed-artifact-only computation of
realized COD minus the vintage-gated committed pipeline, per ISO-year (the disclosed-null's
named size). No solve for the rider either.

=== VERIFIED STATE (2026-08-05 @ origin/main 8693b75d — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers (READ the shards YOURSELF): ERCOT 2026-08-05-run168b-year-curves · PJM
2026-08-04-pjm-152-collapse · CAISO 2026-08-05-caiso-174-measured-fleet · NYISO
2026-08-04-nyiso-125-seam-envelope · NEISO 2026-08-05-neiso-83-ca1-reclass · MISO
2026-08-05-miso-132b-cc-committed. `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY;
HOLDOUT FREEZE ACTIVE (irrelevant to this lane: no solve, no year touched).
PREREQUISITES: `uv sync` (~2 min) for any committed-artifact reads; nothing else.

=== E-1 — THE ZONAL RPS ROW (the finding you design against, FFR-5B §5.3) ===
_build_rps_row builds ONE ISO-wide annual row against a load-weighted blend of state
obligations, dissolving binding state statutes into a slack ISO-wide average. The claimed
fix is a spatial-grain correction under rule 14, zero new tunables, using the per-state ->
per-zone reconciliation FFR-5B says is "already derived inside STATE_RPS_FLOORS['MISO']'s
own comment block". YOUR SCOPING DUTIES: (1) VERIFY that reconciliation claim at
implementation grain — read the actual constants/comment blocks for EVERY multi-state ISO
(MISO, PJM, NEISO, NYISO trivially single-state? verify, don't assume), and state per-ISO
whether zone-resolved obligations are derivable from committed data or need intake;
(2) design the row structure (per-state rows mapped onto zones? per-zone rows? what the REC
dual means at each grain — one dual per row is the REC price of WHAT market); (3) state the
LP-size and degeneracy consequences (rule 2 vectorization, one row per state-year vs one);
(4) interaction with the RPS-as-constraint architecture (CLAUDE.md steps 4-5: "RPS is not a
force-build step") and with FFR-5E's procurement channel (rule 19: the channel is committed
near-term procurement; the RPS row is the statutory driver — they must not double-count the
same MW); (5) per-ISO scope under rule 25 — which ISOs get zonal rows in the first
implementation and why.

=== E-2 — THE CLEAN/CARBON-FREE TIERS (settled WITH E-1, never separately) ===
The tiers are represented NOWHERE; MN/MI/IL's strongest statutory drivers are invisible.
FFR-5B deliberately did not settle whether a second, nuclear-counting clean-energy row is
real or would be slack for the same aggregation reason as E-1. YOUR DUTY: adjudicate this
EX-ANTE from committed artifacts — per state: statutory clean/carbon-free requirement
trajectory vs existing qualifying generation (nuclear + hydro + renewables as each statute
defines) at the zonal grain E-1's design produces. If the row binds nowhere within the
model horizon at honest levels, the verdict is "designed but slack — do not build" and that
verdict goes in the card (that outcome is the system working, not a failed lane). If it
binds somewhere, design the row (statute-defined qualifying set as data, not hardcoded
class tuples — rule 18's spirit; interaction with the REC dual and EAC/CES machinery in
policy/).

=== RULES THAT BIND HARDEST ===
Rule 13/14: statutes and their levels are measured inputs with forward analogues; cite
every level (docs/parameter-citations.md pattern). Rule 19: one mechanism per phenomenon —
the design must state exactly what already floors/forces the same MW (RPS row, EAC, IRA,
FFR-5E channel) and how double-counting is excluded. Rule 25: per-ISO derivation, no
cross-ISO transfer of levels. Rule 28: NO matrix row now (nothing lands); the future
implementation PR adds its row. Rule 5: no magic numbers in the design — every proposed
constant carries its citation.

=== THE RIDER — FFR-5B §5.4 residual sizing (bounded, committed-artifact-only) ===
Compute, per ISO-year in the available vintage windows: realized COD MW (from committed
EIA-860 operable/monthly data ALREADY on disk — read-only; this is a sizing of a disclosed
limitation, not a model input, so the operable sheet is legal HERE and only here) minus the
vintage-gated committed (U/V/TS) pipeline MW the FFR-5E channel would inject. The result is
the named size of the corporate-PPA / beyond-horizon residual FFR-5B disclosed as having no
admissible representation. Report the table + method in the handoff; it feeds no mechanism.

=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit —
`git status --short` after any Python write (scratch helpers included); restore exact HEAD
bytes; never stage the reflow. Push 413: fetch main + rebase first; owner merges fast,
prune stale refs. Never push_files a >=300-line file. Shell cwd persists. Stop-hook on
merged history: rev-list 0 => nothing to amend.

Deliverable: docs/handoffs/ffr-6b-rps-grain-clean-tiers-<date>.md — the E-1 design with the
per-ISO reconciliation verification, the E-2 ex-ante bind/slack adjudication and (if it
binds) its design, the double-count exclusion statement, the §5.4 residual table, explicit
"what I did NOT decide", and the implementation card for the owner's signature.
```

## §0q — Wave 6 landed same-day; cards D-21/D-22 at the owner (2026-08-06 @ `e2ea0b59`)

FFR-6A and FFR-6B both LANDED and adjudicated CLEAN (Addendum V). Headlines: the retirement
margin gap is the forward price object's missing scarcity content (bars exonerated, reserve
leg exonerated, refusals recorded); ERCOT's true in-window economic-exit total is ≈ 0 GW —
1.534 GW was never a margin-screen target; the RPS row's real defects are MISO's forbidden
intra-ISO REC trade, MISO-only clean-tier binding, and a three-ISO clean-on-renewable-row
mis-encoding whose ACP-pinned dual is an unstatutory $40–50/MWh entry subsidy. FFR-6B's
proposed card renumbered D-19 → **D-22** (collision with the spent D-19). FH-4/FH-5 still
HELD, conditions restated (V.3: α/β/γ). Cards D-21/D-22 are at the owner; Wave-7 prompts
follow the signatures.

**§0q addendum (same sitting, 2026-08-06):** signatures in (Addendum V.6) — D-21(a)
DEFERRED (owner, against recommendation: the FH-4/FH-5 lift path is parked until re-opened);
D-21(b) hygiene-only, 5c REFUSED; D-22(a) one-lane-three-arms. Wave 7 = FFR-7A + FFR-7B.

## §0r — Wave-7 prompts (2026-08-06 @ `e2ea0b59`)

### FFR-7A [OPUS] — retirement scoring-target hygiene (D-21(b))

```
[OPUS] FFR-7A — Fix the retirement scoring target so it measures what a margin screen can
legitimately see (owner decision D-21(b), sitting Addendum V.5/V.6, signed 2026-08-06;
evidence base FFR-6A docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md §3.3 and
verdict rows 5a/5b). DATA/SCORER lane: no model mechanism, no ScenarioConfig field, no
arming, no keeper contact. 5c (honoring announced fossil planned-retirement dates in
hindcast arms) is REFUSED by the owner — do not implement it, do not re-propose it.

=== VERIFIED STATE (2026-08-06 @ origin/main e2ea0b59 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT 2026-08-05-run168b-year-curves · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-06-caiso-175-tac-intake · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-05-miso-132b-cc-committed (READ the shards
yourself). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY; HOLDOUT FREEZE ACTIVE.
PREREQUISITES: `uv sync` (~2 min); regenerate_clean.py only if a scorer path needs CLEAN
inputs you touch — likely NOT needed; state what you actually ran.

=== THE MEASURED DEFECTS YOU FIX (FFR-6A §3.3 — verify each at your head, then fix) ===
1. (5b) `build_capacity_actuals` counts EIA status "RE" only: it BOOKS J T Deely's 932 MW
   at its 2023 paper date (physically ceased 2018, status OS at vintage 2020, absent from
   the model's vintage-2020 CAMPD fleet basis) and MISSES V H Braunig 1+2's real 477 MW
   2025 exit (status OS, never RE). The target must count physical exits (status
   transitions to OS/RE with actual cessation dates) and must not contain units the vintage
   fleet basis cannot carry.
2. (5a) Vintage fleet-status hygiene: units already status-OS at the run's vintage (dead
   before the window) must not sit in the actuals target a hindcast arm is graded against —
   whether by excluding them from the target, or from the vintage base fleet, or both;
   justify the choice against the information gate (everything used is vintage-visible or
   outcome-registry data used ONLY as a validation target, rule 13's benchmark branch).
=== WHAT YOU DO ===
1. Fix the builder (scripts/ data path for capacity_actuals) generically — the status-
   handling fix is structural, not an ERCOT patch. Cite the EIA-860 source fields (rule 23:
   the re-derivation cites its source data). Tests: the Deely row leaves the ERCOT target,
   the Braunig rows enter it, and a no-change ISO's target is byte-identical.
2. Regenerate the target artifact(s); report the per-ISO delta table (MW added/removed by
   fuel-year) in the handoff — every changed row named and sourced.
3. RE-SCORE, COMMITTED-ARTIFACT-ONLY (no solve): the two registered ffr5d arms' retirement
   scorecards against the corrected target. Expected per FFR-6A: the shipped arm's in-window
   "0.000 GW executed" grades correctly against a ≈0 GW economic-exit truth; the unified
   arm's false 10.9 GW wave still FAILS (it is a real defect of the price object, not the
   target — D-21(a) owns it and is DEFERRED). If the re-score surprises either way, report
   before interpreting.
4. Do NOT re-register the ffr5d arms and do NOT touch their committed bundles; the re-score
   table lives in your handoff. Rule 28: stamp only if you adjudicate a matrix cell
   (unlikely — no mechanism changes here).
=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit —
`git status --short` after every Python write; restore exact HEAD bytes; never stage the
reflow. Push 413: fetch main + rebase first; owner merges fast, prune stale refs. Never
push_files a >=300-line file. Shell cwd persists. Stop-hook on merged history: rev-list 0
=> nothing to amend. results/ dies with the container — commit early.

Deliverable: the PR (builder fix + tests + regenerated target) and
docs/handoffs/ffr-7a-scoring-target-hygiene-<date>.md — the per-ISO delta table with per-row
sources, the ffr5d re-score table, the 5c refusal restated, and what you did NOT change.
```

### FFR-7B [FABLE] — the RPS/clean-tier repair, three arms in order (D-22(a))

```
[FABLE] FFR-7B — The RPS/clean-tier repair: one lane, three arms, IN ORDER (owner decision
D-22(a), sitting Addendum V.5/V.6, signed 2026-08-06; the design and every level/citation:
FFR-6B docs/handoffs/ffr-6b-rps-grain-clean-tiers-2026-08-05.md — it IS the spec; implement,
do not redesign). If budget runs short: LAND ARM 1 COMPLETE AND MEASURED, hand off the rest
— never land a partial arm. E-1 NEVER ACQUIRES A BUILD LIMB (the row's only output is a
price). The §45U-vs-clean-dual composition for nuclear is OPEN and blocks ARM 3's ARMING
ONLY, not its implementation (state it in the code comment and handoff).

=== VERIFIED STATE (2026-08-06 @ origin/main e2ea0b59 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT 2026-08-05-run168b-year-curves · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-06-caiso-175-tac-intake · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-05-miso-132b-cc-committed (READ the shards
yourself). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY; HOLDOUT FREEZE ACTIVE
(in-sample 2023-2025 paired controls are unaffected). PREREQUISITES IN ORDER: `uv sync`
(~2 min), then scripts/regenerate_clean.py (~63-65 min) before any solve. Rule 12 PER
PROMPT: <=5 solve-years per invocation, years sequential within one, <=2 concurrent
invocations. Rule 27: FABLE (policy/ LP rows + new_entry consumers are core; exact bytes,
blob verification).

=== ARM 1 (FIRST, standalone-landable) — tier/eligible-set level fix: NYISO, NEISO, CAISO ===
The measured defect (FFR-6B §8): clean-tier statutory targets encoded on the renewable-only
row (NYISO 2040:1.00 = CLCPA zero-emission; NEISO's "CES blend"; CAISO 2040:0.80/2045:1.00 =
SB 100) with eligible sets under-counting what the statutes count (NYISO by 20.2 pp — CLCPA
70% counts existing hydro; CAISO by 7.1 pp — geothermal, biomass, small hydro), pinning the
row's dual at the ACP ceiling: an unstatutory $40-50/MWh entry subsidy. THE FIX: per-ISO
cited constant corrections — the RENEWABLE row carries the statute's RENEWABLE trajectory
and its statute-defined eligible set (data, not hardcoded class tuples — FFR-6B §6.3(2)'s
FUEL_TYPE_MAP resolution pattern); the clean-tier years leave the renewable row (their
representation is Arm 3's, MISO-only for now — NYISO/NEISO/CAISO clean rows are NOT built
here, rule 25: no MISO result transfers). Every level cites its statute
(docs/parameter-citations.md pattern; FFR-6B §3.4/§6.1 carry the citations).
CRITICAL — BACKCAST CONTACT IS POSSIBLE AND MUST BE MEASURED, NOT DISCOVERED: these
constants feed the backcast RPS rows of three keeper ISOs. Run the D-1/D-2 paired-control
discipline (Addendum D): same-head control vs corrected arm on each affected ISO's keeper
recipe, 2023-2025 (this is in-sample, freeze-irrelevant; <=5 solve-years per invocation —
budget one ISO at a time, NYISO and CAISO first as the largest corrections). Report deltas;
if a keeper metric moves, HOLD PROMOTION and report to the manager — a keeper moving under
an accurate-input correction is rule 14 working, adjudicated at a sitting, never silently
promoted (and never reverted to the wrong constant to protect a fit, rule 14's core clause).
=== ARM 2 — K-row generalization, MISO ARMED ONLY ===
Generalize _build_rps_row to K rows, each (obligated_zones, eligible_zones, RHS, ACP);
today's behaviour is the K=1/mask=all special case, so the four non-MISO ISOs are
BYTE-IDENTICAL BY CONSTRUCTION — prove it with a regression test, not an assertion. One
default-OFF, forecast-mode gate flag arms MISO's state-group rows (FFR-6B §3: East/Plains
splits, the verified STATE_RPS_FLOORS reconciliation; zones are exact state unions).
REQUIRED COMPANION (FFR-6B card Arm 2): rps_shadow_price becomes PER-ZONE at its three
consumers (new_entry.py entry credit x2, retirements.py screen) — a scalar left in place
would broadcast MISO-East's dual to an Arkansas candidate and rebuild the defect. PJM/NEISO
zonal rows are REFUSED ON STRUCTURE (FFR-6B §7) — do not build them.
=== ARM 3 — clean-tier row family, MISO-West + MISO-East ONLY ===
Second independent row family (never a widened renewable row), second default-OFF gate flag;
qualifying sets are per-statute data (MN carbon-free includes hydrogen+biomass; MI clean
admits qualified CCS gas — FFR-6B §6.3); rule-19 composition per §6.4: the clean dual enters
the EXISTING max(eac, rps_shadow) doctrine for nuclear/hydro (never a sum);
federal_ces_replaces_state_rps suppresses state clean rows too; the wind-MWh-satisfies-both-
rows case is CORRECT (two constraints, one MWh) with generator credit = max(), never sum;
the §45U composition question is left OPEN in a cited comment — ARMING BLOCKED on it.
Illinois gets NO row (recorded null — CEJA is not an LSE share obligation).
=== EVERY ARM ===
Matrix rows for every new flag in the SAME PR (rule 28c); byte-identity of every default-off
path proven by test; cache-key registration for new fields (_CACHE_KEY_OPTIONAL_FIELDS —
the FFR-5E §6.2 precedent: an unregistered field silently invalidates every cached bundle);
zero free parameters (the tunable surface is two gate flags + cited statutory tables);
measurement of armed behavior via the cheapest honest instrument (evolve-path harness or
bounded 2026+ MISO forecast pair; register any full runs to frontend/data/forecast/ via
register_forecast_run.py, NEVER the backcast registry).
=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit —
`git status --short` after every Python write; restore exact HEAD bytes; never stage the
reflow (and your Arm-1 constants edits must be the ONLY constants.py delta you push — diff
it line-by-line before staging). Push 413: fetch main + rebase first; owner merges fast,
prune stale refs. Never push_files a >=300-line file. Shell cwd persists. Stop-hook on
merged history: rev-list 0 => nothing to amend. results/ dies with the container. The D-13
hash-out hazard: same cache key does not imply byte-identity across the D-13 boundary.

Deliverable: the PR(s) (arms in order, each complete) and
docs/handoffs/ffr-7b-rps-clean-tier-repair-<date>.md — per-arm: what landed, byte-identity
proof, the Arm-1 paired-control keeper deltas (with HOLD-PROMOTION posture if any moved),
the Arm-2 regression proof + per-zone dual wiring, the Arm-3 composition statement with the
open §45U question, and what you did NOT separate.
```

## §0s — FFR-7A landed (target GREW); rule-22 regime change; FFR-7C dispatched (2026-08-06 @ `82765525`)

FFR-7A adjudicated CLEAN with a properly-escalated surprise: the corrected ERCOT thermal
target is 2.294 GW (was 1.534) and Sandy Creek (1,008 MW coal, fleet-carried) is now its
largest in-window exit — FFR-6A's "≈0 GW economic exits" bound is CAVEATED until re-derived.
Rule 22 was rewritten by owner clarification (holdout is on the SCORE; intake unrestricted;
2020–2022 iterative touchpoints; 2019 one-touch) — prompts from here carry the new regime.
FFR-7B Arm 1 code is on main; controls/handoff pending. FFR-7C below.

### FFR-7C [OPUS] — re-derive the exit decode on the corrected target (Addendum W.4)

```
[OPUS] FFR-7C — Re-derive FFR-6A's exit decode on the CORRECTED retirement target (manager
charter, sitting Addendum W.4; evidence chain FFR-6A §3.3 → FFR-7A §4/§9.1). COMMITTED-
ARTIFACT measurement lane: no solve, no model change, no arming, no keeper contact. THE
QUESTION: FFR-6A bounded ERCOT's true margin-driven exits at ≈0 GW from a four-row decode of
the OLD target; FFR-7A's corrected target (thermal 1.534 → 2.294 GW) contains +1.7 GW of
physical exits that decode never saw — foremost Sandy Creek (56611_S01, 1,008 MW
supercritical coal, OP through RY2024, OS in RY2025, PRESENT in the vintage-2020 fleet
basis, retirable by a screen). Was ANY newly-visible exit margin-driven? Restate the bound.

=== VERIFIED STATE (2026-08-06 @ origin/main 82765525 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT 2026-08-05-run168b-year-curves · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-06-caiso-175-tac-intake · NYISO 2026-08-04-nyiso-125-seam-envelope · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-05-miso-132b-cc-committed (read the shards
yourself). Freeze ACTIVE — irrelevant here (no solve, no out-of-training score; per the
2026-08-06 rule-22 clarification the holdout is on the SCORE, and this lane scores nothing
out-of-training). FFR-7B may land mid-session — it does not touch your inputs.
PREREQUISITES: `uv sync` (~2 min) only.

=== WHAT YOU DO ===
1. INPUTS, all committed: FFR-7A's corrected target + docs/handoffs/ffr-7a/target-delta.csv
   (334 rows, per-row sourced); FFR-6A's replica method + artifacts (docs/handoffs/ffr-6a/,
   the measured-price replica and SOM benchmark, 2023-2025); the committed fleet/CAMPD data
   for unit characteristics (heat rate, VOM, fuel) of each newly-visible exit unit.
2. For EVERY corrected-target ERCOT in-window thermal exit ≥ 100 MW (Sandy Creek, Braunig,
   and the rest of the +1.7 GW): compute the FFR-6A-style pro-forma margin AT MEASURED
   PRICES for its exit-decision years vs its fuel's bar (same construction FFR-6A §3.1
   validated against SOM 0.89-0.97 — reuse its scripts/probes machinery; extend, don't
   fork). PRE-REGISTER the unit list and the decision rule (margin < bar in the year before
   exit ⇒ economically consistent exit) BEFORE computing any margin.
3. RESTATE THE BOUND: ERCOT's margin-consistent exit total 2021-2025 on the corrected
   target, per unit, with the per-unit evidence. State plainly which of FFR-6A's four
   conclusions survive (the gap decomposition and bar exoneration are untouched by the
   target — say so explicitly if verified) and which needed this re-derivation.
4. REPORT — DO NOT RE-OPEN — the implication for D-21(a) (DEFERRED by the owner, V.6): if
   Sandy Creek's exit was margin-driven, the corrected screen has a real in-window
   economic-exit target and the price-object diagnosis gains a validation case; if not, the
   ≈0 bound is restored at the larger denominator. Either way the manager brings it to the
   owner; you recommend nothing about D-21(a) or the FH-4/FH-5 lift.
5. Also REPORT (not decide) FFR-7A §9.3: whether an OP-only vintage gate would change the
   corrected target (row count + MW), as a measured table the owner can decide on.
6. Rule 28: no mechanism tested — no matrix cell expected; stamp only if you genuinely
   adjudicate one.

=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit —
`git status --short` after every Python write; restore exact HEAD bytes; never stage the
reflow. Push 413: fetch main + rebase first; owner merges fast, prune stale refs. Never
push_files a >=300-line file. Shell cwd persists. Stop-hook on merged history: rev-list 0
=> nothing to amend. The gas_st↔gas_ct taxonomy seam (FFR-7A §4.1) is KNOWN and OUT OF
SCOPE — note where it touches your rows, change nothing.

Deliverable: docs/handoffs/ffr-7c-exit-decode-corrected-target-<date>.md — the
pre-registered unit list + decision rule, the per-unit margin table with evidence, the
restated bound, which FFR-6A conclusions survive, the D-21(a) implication (reported, not
recommended), and the §9.3 OP-only table.
```

## §0t — Wave 7 closed; FFR-7B-2 dispatched; cards D-23/D-24 at the owner (2026-08-06 @ `97e37b0f`)

FFR-7C: the ≈0 bound SURVIVES on the corrected target (0 of 2,294 MW; Sandy Creek clears
1.25×) — FFR-6A's price-object and bar conclusions verified untouched; the window can only
FALSIFY a screen via exits, never confirm one (positive validation is price-side). FFR-7B
Arm 1: statutory corrections landed, paired controls BYTE-IDENTICAL ×3 ISOs, no promotion
hold; Arms 2–3 handed off → FFR-7B-2 below. neiso-87: the NEISO locked-test SPENT claim is
FALSE (incl. CLAUDE.md) → card D-23. **EXECUTED 2026-08-06** by the NEISO-RECORD governance
session: the record now reads **NEVER GRANTED**; 20 live files corrected (neiso-87 estimated
13 — the reconciliation, and the ~22 `results/calibration/` session records deliberately left
as history, are in `docs/handoffs/neiso-record-correction-2026-08-06.md`). Nothing granted;
`final` still EMPTY, freeze still ACTIVE. Full record: Addendum X.

### FFR-7B-2 [FABLE] — Arms 2–3 of the RPS/clean-tier repair (D-22(a) continuation)

```
[FABLE] FFR-7B-2 — Implement Arms 2 and 3 of the RPS/clean-tier repair (owner decision
D-22(a), sitting Addendum V.6; continuation chartered at Addendum X.2/X.3). THE SPEC IS
TWO DOCUMENTS, IN ORDER: FFR-7B's §6 design-to-implementation notes
(docs/handoffs/ffr-7b-rps-clean-tier-repair-2026-08-06.md — code-verified pointers: LP
layout/costs/rows/model touch points, the per-zone dual companion, the MISO state-row table
with citations, the test list) and FFR-6B (docs/handoffs/ffr-6b-rps-grain-clean-tiers-
2026-08-05.md §§3, 6) where §6 defers. Implement, do not redesign. ARM 2 LANDS COMPLETE
BEFORE ARM 3 BEGINS; if budget runs short, land Arm 2 complete and hand off Arm 3 — never a
partial arm. E-1 NEVER ACQUIRES A BUILD LIMB. The §45U-vs-clean-dual composition is OPEN
and blocks ARM 3's ARMING ONLY (cited comment + handoff statement).

=== VERIFIED STATE (2026-08-06 @ origin/main 97e37b0f — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT 2026-08-05-run168b-year-curves · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-06-caiso-175-tac-intake · NYISO 2026-08-06-nyiso-128-solar-basis · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-05-miso-132b-cc-committed (READ the shards
yourself; keepers move mid-lane — FFR-7B had two move under it; re-verify before any
paired measurement). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY; freeze ACTIVE
(all your solves are in-sample or forecast-mode). Arm 1 is ON MAIN (statutory
STATE_RPS_FLOORS + RPS_ELIGIBLE_FUELS_BY_ISO) — your base includes it.
PREREQUISITES IN ORDER: `uv sync` (~2 min), then scripts/regenerate_clean.py (~63-65 min)
before any solve. Rule 12 PER PROMPT: <=5 solve-years per invocation, years sequential
within one, <=2 concurrent invocations. Rule 27: FABLE (model/lp is core; exact bytes, blob
verification).

=== ARM 2 — K-row generalization, MISO ARMED ONLY (7B §6.1 steps 1-9 ARE the plan) ===
Follow the nine steps verbatim: layout n_rec_acp=K + rec_acp_col(k,t); costs (K,) ACP
vector; _build_rps_rows per-region masks + RHS; dual recovery K-slice with
rps_shadow_price scalar at K==1 / per-zone max-over-eligible vector at K>1; the REQUIRED
per-zone credit companion at new_entry.py + retirements.py via a shared helper; the gate
flag (default OFF, forecast-mode, MISO-only arming) registered in
_CACHE_KEY_OPTIONAL_FIELDS + defaults ledger IN THE SAME COMMIT (nyiso-128's unregistered
field was found live on main — run the default-key pin tests FIRST and confirm they pass at
your base before you start, so you never debug someone else's red); matrix row same PR
(28c). The MISO state-row table and MT-exclusion are in §6.1(7) with citations — copy, do
not re-derive. Tests per §6.1(8): flag-off byte-identity (toy + K=1 legacy), armed
mask-binds toy, blend reproduction (Σ rhs/demand ≈ .1139/.1606/.1981 at 2026/30/40),
per-zone credit wiring. K=1 BYTE-IDENTITY IS A REGRESSION TEST, NOT AN ASSERTION.
Measurement: bounded 2026+ MISO forecast pair (off vs armed), <=5 solve-years each,
registered to frontend/data/forecast/ via register_forecast_run.py (NEVER the backcast
registry), Q.2 supersession noted.
=== ARM 3 — clean-tier row family, MISO-West + MISO-East ONLY (7B §6.2 + FFR-6B §6.3/§6.4) ===
Second independent row family on Arm 2's K-row machinery; second default-OFF gate flag
(same-commit cache-key registration, same-PR matrix row); per-statute qualifying sets as
DATA (MN carbon-free incl. hydrogen+biomass; MI clean incl. qualified CCS gas); rule-19
composition per FFR-6B §6.4 — clean dual enters the EXISTING max(eac, rps_shadow) doctrine
for nuclear/hydro (never a sum); federal_ces_replaces_state_rps suppresses state clean rows
too; wind-satisfies-both-rows is CORRECT with generator credit = max(); §45U composition
OPEN — ARMING BLOCKED, stated in a cited comment. Illinois: NO row (recorded null).
Measurement: extend the Arm-2 forecast pair or a separate bounded pair; same registration
rules.
=== TRAPS ===
The ruff-autofix hook reflows src/market_sim/config/constants.py on ANY .py Write/Edit —
`git status --short` after every Python write; restore exact HEAD bytes; never stage the
reflow; your constants edits (if any) must be the only constants.py delta you push. Push
413 + flaky transport: 7B §5's operational notes are REQUIRED READING — fetch main + rebase
before every push; owner merges fast and deletes branches (`git remote prune origin`).
Never push_files a >=300-line file. Shell cwd persists. Stop-hook on merged history:
rev-list 0 => nothing to amend. results/ dies with the container — commit registrations and
handoff before tail work. The D-13 hash-out hazard stands.

Deliverable: the PR(s) (Arm 2 complete; Arm 3 complete or handed off) and
docs/handoffs/ffr-7b2-rps-krow-clean-rows-<date>.md — per-arm: byte-identity proof, the
armed measurement with per-region duals shown, the per-zone credit wiring evidence, the
Arm-3 composition statement with the open §45U question, and what you did NOT separate.
```

**§0t addendum (same sitting):** D-23 and D-24 SIGNED (Addendum X.6). Two further prompts:

### NEISO-RECORD [OPUS] — execute the signed D-23 record correction

```
[OPUS] NEISO-RECORD — Correct the false NEISO locked-test record (owner decision D-23,
SIGNED at sitting Addendum X.6, 2026-08-06 — cite that signature as the session-logged
authorization; the finding is neiso-87 results/calibration/ASSESSMENT-neiso87-declaration-
2026-08-06.md §1, independently corroborated by docs/third-party-peer-review-2026-07.md
§6.3 item 1). GOVERNANCE lane, committed artifacts only: NO solve, NO scoring, NO year
touched, NO grant of anything. The correction changes the record from "SPENT, never
re-grantable" to "NEVER GRANTED"; NEISO's `final` readiness answer (NOT YET, neiso-87 §3)
is untouched and nothing here authorizes a 2019/H1-2026 spend.

=== WHAT YOU DO ===
1. Reproduce neiso-87 §1's artifact search at YOUR head first (no registry entry, no
   bundle, no bench row, no 2019 actuals row; locked_test_scored_on names a 2023-2025
   config) — if ANY 2019 artifact exists that neiso-87 missed, STOP and report; do not
   correct a record you have not re-verified.
2. Edit, in ONE commit where possible: frontend/data/backcast/calibration-complete.json
   (NEISO locked_test/locked_test_note + final._note — quote the old text in the new note's
   genealogy: "previously misrecorded as SPENT 2026-07-07; corrected per D-23"); CLAUDE.md
   rule 22 (the "NEISO is the latter" clause and any SPENT language — CLAUDE.md is core:
   Edit locally, push exact bytes, verify the blob after push, rule 27);
   frontend/data/backcast/holdout-freeze.json where it repeats SPENT; the 2022 touchpoint
   registry sidecar; docs/mechanism-testing-matrix.md; docs/calibration-log/neiso.md (10
   entries — append a correction note at each or one dated correction entry the others
   reference, do NOT rewrite historical entries, correct-by-addendum); the handoff/audit
   docs that repeat it second-hand (grep 'SPENT' + 'locked test' repo-wide; neiso-87 §1
   counts 13 files — enumerate YOUR OWN list at your head and reconcile any difference).
3. Every edit carries the citation chain (neiso-87 §1 → peer review §6.3 → D-23/X.6).
4. Run scripts/audit_keepers.py --iso NEISO (must pass) and confirm
   holdout_policy.authorized still returns NEISO/locked_test = False (the correction must
   not accidentally grant).
5. docs/handoffs/neiso-record-correction-<date>.md: the re-verification, the file list with
   before/after, the audit results.
=== TRAPS ===
CLAUDE.md and any >=300-line file: local Edit + git push exact bytes + blob verification —
NEVER push_files. The ruff-autofix hook reflows constants.py on any .py write — you should
write no Python except possibly a grep helper; `git status --short` before staging. Push
413: fetch main + rebase first. Correct-by-addendum in logs; never rewrite history entries.
```

### SCORE-GATE [OPUS] — execute the signed D-24 recall-gate redefinition

```
[OPUS] SCORE-GATE — Redefine the >=300 MW retirement recall gate against the REACHABLE set
(owner decision D-24, SIGNED at sitting Addendum X.6, 2026-08-06; evidence FFR-7C
docs/handoffs/ffr-7c-exit-decode-corrected-target-2026-08-06.md §5 + Addendum X.1).
SCORER-ONLY lane: no model mechanism, no ScenarioConfig field, no solve, no keeper contact.

THE CHANGE: in score_capacity_hindcast's recall metric, a target exit counts as a gate
member ONLY IF (i) the unit exists in the run's fleet basis (vintage fleet), AND (ii) its
exit is reachable by an admissible channel: economic (no exclusion recorded) OR
instrument-driven with instrument_date <= the run's vintage cutoff (the confirmed-exits
information gate's own rule). Unreachable exits are EXCLUDED from the denominator and
listed in a NON-GATED diagnostic line (unit, MW, driver, why unreachable: post-vintage
instrument / no instrument / not in fleet) so the blind spot stays visible on every report.
Empty member set => the gate reports n/a, never 0/N. Reachability classification uses
committed artifacts only: the corrected target, data/raw/confirmed-retirements/,
FFR-7C's per-unit decode (docs/handoffs/ffr-7c/exit-decode-2026-08-06.json) for the
economic exclusion evidence — cite per unit, no speculation; a unit with no evidence either
way stays IN the member set (fail-closed: the gate only excludes on positive evidence).

DO: implement + tests (ERCOT corrected target => members = {} => n/a with a 5-row
diagnostic; a synthetic margin-driven exit => member); re-emit the ffr5d arms' scorecards
committed-artifact-only (no solve) and show before/after in the handoff — do NOT touch
their registered bundles; check no other gate consumes the recall metric downstream (grep
the scorer + CI) and report what does. Rule 28: scorer change, no mechanism — no matrix
cell expected. Deliverable: the PR + docs/handoffs/score-gate-recall-redefinition-<date>.md
(the member rule as implemented, per-unit classification table with citations, before/after
scorecards, downstream-consumer check).
=== TRAPS ===
The ruff-autofix hook reflows constants.py on ANY .py write — `git status --short` before
staging; restore exact HEAD bytes; never push the reflow. Push 413: fetch main + rebase
first. Never push_files a >=300-line file. Stop-hook on merged history: rev-list 0 =>
nothing to amend.
```

## §0u — Wave 7 fully discharged; cards D-25/D-26 at the owner (2026-08-06 @ `2f4792cd`)

FFR-7B-2 landed Arms 2–3 complete (D-22(a) fully discharged; MI row pins $30 every year, IL
from 2027, delivery-based states slack — the grain is real and confined); NEISO-RECORD
executed D-23 (record reads NEVER GRANTED everywhere, nothing granted); SCORE-GATE executed
D-24 (reachable-set recall + unreachable diagnostic). Keepers unmoved. Full adjudication:
Addendum Y. No lane is in flight; remaining work is owner-gated (D-21(a) deferred, cards
D-25/D-26, §45U design) or unowned housekeeping (Y.2). Prompts follow signatures.

**§0u addendum (same sitting):** D-25 and D-26 SIGNED (Addendum Y.4). Two prompts:

### TAXONOMY [FABLE] — the gas_st↔gas_ct fuel-classing fix (D-25)

```
[FABLE] TAXONOMY — Add the gas_st branch to data.fleet._map_fuel_type and carry the
reclassification through honestly (owner decision D-25, SIGNED sitting Addendum Y.4,
2026-08-06; evidence FFR-7A §4.1, FFR-7C §1.1 note, SCORE-GATE handoff §1). THE RISK THE
MANAGER FLAGS UP FRONT: _map_fuel_type feeds BOTH the scoring-target builder AND the legacy
fleet loader — non-ERCOT ISOs' class structure can change, which changes SOLVES. This is a
potentially keeper-moving accurate-data correction (rule 14): it runs under the Addendum-D
paired-control + HOLD-PROMOTION discipline, and a keeper metric moving is a REPORT, never a
silent promotion and never a reason to revert the accurate classing.

=== VERIFIED STATE (2026-08-06 @ origin/main 2f4792cd — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT 2026-08-05-run168b-year-curves · PJM 2026-08-04-pjm-152-collapse · CAISO
2026-08-06-caiso-175-tac-intake · NYISO 2026-08-06-nyiso-128-solar-basis · NEISO
2026-08-05-neiso-83-ca1-reclass · MISO 2026-08-05-miso-132b-cc-committed (read the shards
yourself). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY (NEISO reads NEVER
GRANTED post-D-23); freeze ACTIVE — all paired controls are in-sample 2023-2025.
PREREQUISITES IN ORDER: `uv sync`, then regenerate_clean.py (~63-65 min) before any solve.
Rule 12 PER PROMPT: <=5 solve-years per invocation, sequential within one, <=2 concurrent;
PJM and MISO never co-run in one session. Rule 27: FABLE; exact bytes + blob verification.

=== WHAT YOU DO, IN ORDER ===
1. MEASURE THE BLAST RADIUS FIRST, NO EDIT: for every ISO, enumerate the units
   _map_fuel_type currently classes gas_ct that are physically gas STEAM (EIA-860
   prime-mover ST + gas fuel; cross-check CAMPD unitType where covered). Per-ISO table:
   units, MW, share of class. THE ERCOT CAMPD-BIN PATH IS UNAFFECTED BY CONSTRUCTION
   (fuel classing there comes from CAMPD binning) — verify and state it rather than assume.
2. THE FIX: add the gas_st branch (prime-mover-based, cited to the EIA-860 field — rule 23);
   regenerate affected CLEAN artifacts and the scoring targets (FFR-7A's builder + the
   corrected targets); per-ISO before/after delta tables for BOTH the fleet classing and
   the targets in the handoff.
3. PAIRED CONTROLS (Addendum D), only for ISOs whose step-1 table is non-empty: same-head
   control vs reclassed arm on the affected ISO's keeper recipe, 2023-2025, budget rule 12
   (largest-impact ISO first; if >2 ISOs are affected, run the top two and hand off the
   rest with the harness committed). BYTE-IDENTICAL => say so and move on. Any metric move
   => HOLD PROMOTION, report the delta, keeper adjudication is the manager/owner's.
4. Re-emit (committed-artifact, no re-solve, no bundle mutation) the ffr5d arms' scorecards
   and the SCORE-GATE diagnostic on the reclassed targets — the Braunig rows should now
   carry gas_st and their bar should be the gas_st bar; state what changes in the
   unreachable-exits diagnostic.
5. Rule 28: no new ScenarioConfig field expected (a taxonomy fix, not a mechanism) — but if
   any solve-affecting behavior needs a gate to keep keepers byte-stable pending
   adjudication, STOP and consult the manager rather than inventing an ungated flip that
   moves keepers silently.
=== TRAPS ===
The ruff-autofix hook reflows constants.py on ANY .py write — `git status --short` after
every Python write; restore exact HEAD bytes; never stage the reflow. Push 413: fetch main
+ rebase first; owner merges fast, prune stale refs. Never push_files a >=300-line file.
results/ dies with the container — commit the delta tables and handoff before tail work.
Cache keys from the runtime line. Evolution-ledger path trap stands.

Deliverable: the PR(s) + docs/handoffs/taxonomy-gas-st-<date>.md — the blast-radius table,
the fix with citations, per-ISO before/after deltas, the paired-control results with
HOLD-PROMOTION posture if anything moved, the re-emitted scorecard/diagnostic deltas, and
what you did NOT separate.
```

### ARM-MISO [OPUS] — arm miso_rps_compliance_regions for MISO forecast runs (D-26)

```
[OPUS] ARM-MISO — Arm miso_rps_compliance_regions for MISO forecast runs (owner decision
D-26, SIGNED sitting Addendum Y.4, 2026-08-06; measured basis FFR-7B-2 §3.1 — MI pins $30
every year, IL from 2027, delivery-based states correctly slack, control blind until 2029).
SMALL GOVERNANCE/CONFIG lane, the D-2' pattern.

WHAT YOU DO: (1) Add the MISO ISOConfig.default_scenario_overrides entry arming
miso_rps_compliance_regions (follow the entry_vre_capacity_revenue / D-2' precedent
exactly: config/iso_configs.py::_miso_config, cited comment naming D-26/Y.4).
(2) VERIFY the flag's forecast-mode gate means backcast solves are untouched: run the
existing flag-off/K=1 byte-identity tests plus a targeted assertion that a backcast-mode
MISO ScenarioConfig resolves the K=1 path even with the override present; if the gate is
mode-checked at consumption (not construction), prove it with a test, not a comment.
(3) Matrix: re-stamp the miso_rps_compliance_regions MISO cell armed-K (rule 28b, citation
D-26 + the ffr7b2-rpsk pair ids). (4) check_mechanism_matrix.py + the fast tier of the
config/model unit tests; report their state honestly (pre-existing failures enumerated,
not absorbed). (5) NOTE in the handoff: miso_clean_tier_rows stays UNARMED (blocked on the
open §45U composition — D-22/X.2; not this lane's decision), and Arm-3's armed-leg
registration already on the dashboard is measurement evidence, not an arming.
NO solve is required; the FFR-7B-2 registered pair IS the evidence. If you believe a
confirmation solve is needed, say why to the manager first rather than running one.
=== TRAPS ===
The ruff-autofix hook reflows constants.py on ANY .py write — `git status --short` before
staging; restore exact HEAD bytes. Push 413: fetch main + rebase first. Never push_files a
>=300-line file. Stop-hook on merged history: rev-list 0 => nothing to amend.

Deliverable: the PR + docs/handoffs/arm-miso-rps-regions-<date>.md — the override entry,
the backcast-untouched proof, the matrix re-stamp, and the §45U/Arm-3 unarmed statement.
```

## §0v — ARM-MISO discharged; TAXONOMY controls pending (2026-08-07 @ `0e47ab67`)

D-26 EXECUTED (MISO forecast default armed, backcast-untouched proven by test, matrix
O → K). D-25's fix is ON MAIN (CAISO/PJM/ERCOT byte-identical; MISO/NYISO/NEISO carry a
14-bin heat-rate residue) but its MISO/NYISO paired-control RESULTS ARE NOT — the merged
handoff carries a live placeholder; NEISO tail handed off with harness. HOLD PROMOTION
until they land. PARALLEL SESSIONS: MISO/NYISO/NEISO solves at HEAD are on the reclassed
fleet — small metric deltas vs keepers are D-25's, cite Addendum Z.2. No new dispatch this
cycle; next manager action is tracking the control results (re-charter from the committed
harness if silent — the FFR-5D-M pattern).

**§0v addendum (2026-08-07 @ `638cd378`):** three further prompts. TAXONOMY-M is
CONDITIONAL — the owner pastes it ONLY if the TAXONOMY session is no longer running (its
controls may still be solving); its step 0 also self-checks. FFR-3V-FIX and HOUSE-1 are
independent parallel lanes from the Y.2 queue, dispatchable at will.

### TAXONOMY-M [OPUS] — collect/run the D-25 paired controls (CONDITIONAL)

```
[OPUS] TAXONOMY-M — Finish D-25's paired-control measurement (continuation; charter
Addendum Z.2, the FFR-5D-M pattern). STEP 0, HARD STOP: read
docs/handoffs/taxonomy-gas-st-2026-08-07.md §4 at YOUR head — if
RESULTS_PLACEHOLDER_PAIRED_CONTROLS is GONE, the original session finished; report that
and END. Also STOP if a branch claude/fuel-taxonomy-gas-st-* exists with commits newer
than the handoff. Otherwise: the fix is ON MAIN (PR #3691), the harness is committed in §4
(control tree via git archive + replay_keeper per arm), and your job is ONLY the controls:
(1) MISO pair and NYISO pair, same-head control-vs-arm on each keeper's committed bundle,
2023-2025, phased exactly as §4's memory note orders (never two large-ISO solves at once;
PJM/MISO never co-run); (2) the NEISO tail (9.3 MW, two CHP bins) with the same harness;
(3) replace the §4 placeholder with the results table (per-ISO: metric deltas or
BYTE-IDENTICAL) by editing the handoff IN PLACE below §4's header — nothing above it
changes; (4) HOLD-PROMOTION posture: any keeper metric that moves is a REPORT to the
manager, never a promotion, never a revert of the taxonomy; (5) no dashboard registration
(these are verification runs — register only if the manager's standing convention for
zero-delta verification runs applies, i.e. follow what FFR-7B Arm 1 did: register the
verification trio to the backcast dashboard as its runs were; mirror that convention, cite
it). PREREQUISITES: uv sync, then regenerate_clean.py (~63-65 min) before solving.
Rule 12 PER PROMPT. TRAPS: ruff-autofix reflows constants.py on any .py write — git status
--short before staging; push 413 — fetch main + rebase first; results/ dies with the
container — commit the filled §4 immediately after each pair completes, not at the end.
Deliverable: the filled §4 + a short report (deltas, posture).
```

### FFR-3V-FIX [OPUS] — close the hindcast renewable-pool vintage leak (unblocks FFR-5E's hindcast arm)

```
[OPUS] FFR-3V-FIX — Close FFR-3V §6.1: hindcast renewable pools seed from the canonical
forecast constant instead of the vintage-measured fleet (manager charter from the Y.2
unowned queue; the finding: a capacity hindcast is mode="forecast"+hindcast=True, so
load_renewable_profiles' is_backcast gate falls through to RENEWABLE_INSTALLED_MW — MISO
solar seeds 7,000 MW against 2,056 MW actual at vintage 2020, 3.4x over. This is the
BLOCKER on FFR-5E's hindcast arm: injected procured MW double-count invisibly on an
inflated pool).

=== VERIFIED STATE (2026-08-07 @ origin/main 638cd378 — RE-VERIFY AT YOUR OWN HEAD) ===
Keepers: ERCOT run168b-year-curves · PJM pjm-152-collapse · CAISO caiso-175-tac-intake ·
NYISO nyiso-128-solar-basis · NEISO neiso-83-ca1-reclass · MISO miso-132b-cc-committed
(read the shards). `complete` = {CAISO, NEISO, NYISO, PJM}; `final` EMPTY; freeze ACTIVE
(hindcast T1-FF windows are the enumerated carve-out; you solve nothing out-of-training).
NOTE: D-25's taxonomy paired controls may be in flight in a parallel session — they touch
MISO/NYISO/NEISO backcast replays, not your hindcast path; do not be surprised by small
keeper-metric deltas discussed in Addendum Z.2. PREREQUISITES: uv sync, then
regenerate_clean.py before any solve. Rule 12 PER PROMPT. Rule 27: OPUS ok.

=== WHAT YOU DO ===
1. VERIFY the leak at your head first (FFR-3V §6.1's numbers re-derived: the pool a
   vintage-2020 MISO hindcast actually seeds vs the vintage-2020 EIA-860 measured VRE
   fleet). State the per-ISO, per-tech gap table.
2. THE FIX: in hindcast runs, seed the renewable pools from the RUN'S OWN VINTAGE EIA-860
   measured fleet (rule 13: measured physical input, information-gate compliant — the
   vintage sheet is what a run at that vintage may know; rule 14: measured beats the
   canonical constant). Respect the existing vintage machinery (active_eia860_dir); no new
   tunable — if you cannot build it without inventing a parameter, STOP and escalate. Gate
   ONLY if needed for byte-stability of existing registered hindcasts — prefer an ungated
   accurate-data fix IF the only affected artifacts are hindcast runs (which are Q.2
   evidence, expected to be superseded); state your choice and why. Plain forecast (non-
   hindcast) runs are UNTOUCHED — prove by test.
3. MEASUREMENT: a bounded before/after hindcast pair (ERCOT or MISO, the FFR-5A posture,
   <=5 solve-years, sequential; register to frontend/data/hindcast/ NEVER the backcast
   registry) showing the corrected pool sizes and what moves. Pre-register the reads.
4. Matrix/rule 28: if you add any ScenarioConfig field, its row rides the same PR; stamp
   what you adjudicate. Handoff states explicitly: FFR-5E's HINDCAST ARM IS NOW UNBLOCKED
   (or still blocked and why) — that sentence is the deliverable the manager is waiting on.
=== TRAPS ===
ruff-autofix reflows constants.py on any .py write — git status --short before staging.
Push 413: fetch main + rebase first. Never push_files a >=300-line file. Cache keys from
the runtime line; the D-13 hash-out hazard; results/ dies with the container.
Deliverable: the PR + docs/handoffs/ffr-3v-fix-<date>.md (gap table, the fix + gating
choice, the paired measurement, the unblocked/blocked statement).
```

### HOUSE-1 [FABLE] — the ruff-autofix hazard and the red-main CI gap

```
[FABLE] HOUSE-1 — Two infrastructure repairs from the manager's Y.2 unowned queue
(sitting Addenda T.1 and X.2 record the incidents). NO model behavior may change: every
edit is hooks/lint/CI config or test wiring.

1. THE RUFF-AUTOFIX HAZARD (T.1): .claude/hooks/ruff-autofix.sh runs whole-tree
   `uv run ruff format .` on ANY .py Write/Edit, which reflows
   src/market_sim/config/constants.py 3,960 -> 9,508 lines (the file is not in
   pyproject.toml extend-exclude and main's own bytes fail `ruff format --check`). Every
   session since has carried a manual trap. FIX: (a) scope the hook to format ONLY the
   file(s) actually edited (not the tree); (b) add constants.py (and any other core file
   failing --check at HEAD — enumerate them) to extend-exclude with a comment citing this
   charter — do NOT reformat the files themselves (a 5,500-line rewrite of a core file is
   rule 27's forbidden act even when AST-identical; the exclusion is the fix). Verify: an
   Edit to a scratch .py leaves constants.py untouched; ruff format --check on the
   excluded set is quiet by exclusion.
2. THE RED-MAIN CI GAP (X.2): FFR-7B found every default-cache-key pin test FAILING on
   clean main (nyiso-128's unregistered field) yet merges proceeded. Diagnose WHY CI did
   not stop it: are tests/regression/test_persisted_identity.py + the default-key pin
   tests in the ci.yml test job? Advisory or blocking? Report the actual mechanism, then
   make the MINIMAL change so a moved pinned default key blocks a PR (add the test file(s)
   to the blocking job, or a dedicated quick job — no new workflow file; extend ci.yml;
   no scheduled triggers, private-repo minutes rule). Also enumerate (report-only, fix
   nothing) the current pre-existing failures on main's fast tier so the baseline is
   finally written down (FFR-5E counted 13 environmental; pin the list).
Rule 27: FABLE for .github/workflows + hooks; exact bytes; blob verification on any
>=300-line file you touch. TRAPS: the hook you are editing is the one that reflows
constants.py — verify git status --short after every .py write DURING this lane too; push
413 — fetch main + rebase first.
Deliverable: the PR + docs/handoffs/house-1-lint-ci-<date>.md (hook before/after, the
exclusion list with --check evidence, the CI-gap mechanism found and the minimal fix, the
pinned baseline failure list).
```

## §0w — TAXONOMY complete; D-27 signed; NYISO-PROMOTE dispatched (2026-08-07 @ `d3340718`)

D-25 fully executed (controls in, HOLD PROMOTION honoured, deltas small/physical/no gate).
AA.2: MISO's keeper re-scores NOT-YET at HEAD under rubric v3.1 — pre-existing drift, the
MISO lane's to settle, MISO taxgs promotion DEFERRED on it (D-27). NYISO promotes:

### NYISO-PROMOTE [OPUS] — promote the NYISO taxonomy arm (D-27)

```
[OPUS] NYISO-PROMOTE — Promote 2026-08-07-nyiso-131-taxgs-arm to NYISO keeper (owner
decision D-27, SIGNED sitting Addendum AA.4, 2026-08-07; evidence taxonomy-gas-st handoff
§4.1: verdict-identical to the standing keeper, deltas <=0.02 $/MWh, registered and scored
— NO SOLVE). GOVERNANCE lane, committed artifacts only.

STEP 0: verify NYISO's keeper is still 2026-08-06-nyiso-128-solar-basis and the arm bundle
+ registry sidecar exist at your head; if the keeper has moved, STOP and report (the
promotion was adjudicated against nyiso-128 — a newer keeper needs fresh adjudication).
THEN, per the CLAUDE.md promotion protocol: (1) edit frontend/data/backcast/keepers/
NYISO.json -> keeper 2026-08-07-nyiso-131-taxgs-arm with a note citing D-27/AA.4 + the
taxonomy handoff §4.1 (carry forward the nyiso-128 recipe genealogy — the arm IS the
nyiso-128 recipe on the corrected taxonomy); (2) rebuild status/NYISO.js
(build_status.py --iso NYISO); (3) D-5(b) RE-KEY: NYISO holds `complete` — update its
entry's keeper field AND re-verify the determination against the new run
(scripts/calibration_verdict.py --run-id 2026-08-07-nyiso-131-taxgs-arm, committed
artifacts, never a solve); a WORSE determination STOPS the promotion and escalates —
expected: identical CALIBRATED-WITH-CAVEATS; (4) matrix header re-stamp (keeper ids +
open gates) + re-check the NYISO column (rule 28); (5) calibration-log entry
(docs/calibration-log/nyiso.md, one dated entry citing D-27); (6) audit: audit_keepers.py
--iso NYISO (M1) must pass — then run the calibration-keeper-auditor convention your head
uses for keeper-shard edits; (7) one small commit, push (fetch main + rebase first),
verify the pushed shard blob. DO NOT touch MISO's shard or any other ISO's files (D-27
defers MISO explicitly).
TRAPS: ruff-autofix reflows constants.py on any .py write — git status --short before
staging. Push 413: fetch main + rebase first. push_files acceptable only for the small
JSON/js files. Stop-hook on merged history: rev-list 0 => nothing to amend.
Deliverable: the merged commit + a SHORT note docs/handoffs/nyiso-taxgs-promotion-
<date>.md (the re-verified determination, M1 pass, matrix re-stamp).
```

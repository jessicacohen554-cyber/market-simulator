# Calibration Log — governance / cross-ISO

Continuation of `docs/calibration-log.md` (frozen archive, entries through
2026-07-19) for cross-ISO entries: rubric amendments, owner rulings, audits and mechanisms spanning multiple ISOs (single-ISO work goes to that ISO's own file). Same entry format — `## YYYY-MM-DD — title`,
newest at the BOTTOM. Only this lane's sessions append here, so parallel
per-ISO calibration sessions never conflict (the per-ISO lane convention,
2026-07-19; see `frontend/data/backcast/keepers/README.md`).

## 2026-07-19 — Per-ISO keeper lanes: keepers.json + status.js sharded; CAISO keeper record reconciled; #2558 partial registration flagged

**What changed (process, no solve, no model change).** Keeper promotions used
to rewrite three cross-ISO shared files — `frontend/data/backcast/keepers.json`,
the monolithic generated `status.js` (single-line ~200 KB, plus an embedded
timestamp, so ANY two rebuilds conflicted), and the tail of
`docs/calibration-log.md` — so concurrent promotions in different ISOs always
collided and forced rebases. All three are now sharded per ISO:
`keepers/<ISO>.json` (+ `index.json`, `README.md`), `status/<ISO>.js` (+ the
deterministic, timestamp-free `status/shared.js` rubric block), and
`docs/calibration-log/<iso>.md`. `scripts/lib/keeper_store.py` is the single
reader/writer (legacy-monolith fallback for old checkouts/fixtures);
`build_status.py`/`audit_keepers.py` gained `--iso` lane scoping (the S1 sync
check is scoped so a stale part in another lane cannot fail this lane's
audit); `bc-data.js` composes the shards client-side with a monolith fallback;
the keeper-audit hook, auditor agent, calibration-report skill, and retention
protection all read the store. Retired monoliths are gitignored so a stale
tool cannot resurrect them. Status parts were migrated VERBATIM from the HEAD
`status.js` bytes (no re-derivation on an incomplete checkout).

**Collision damage witnessed while migrating (three separate divergences in
one day — live proof of the disease).** (a) At the morning HEAD, `status.js`
(built 09:29 by the caiso-101 session) carried CAISO = `caiso-101` while
`keepers.json` still said `caiso-97` — the owner-authorized caiso-99 →
caiso-101 promotions were merge-clobbered out of `keepers.json`. (b) By
mid-afternoon other sessions had promoted `ercot86-rt-wall-fullspan` and
`caiso-102-hourfix` and rebuilt `status.js` (15:17), manually re-reconciling
the earlier clobber. (c) `nyiso-64-outage-refix` was then promoted AFTER that
15:17 build, leaving `keepers.json` (nyiso-64) and `status.js` (nyiso-63)
divergent AGAIN at the moment of this migration. The shards were split from
the newest state (`keepers.json` @ `6b5b6c4`); status parts were migrated
verbatim from the 15:17 `status.js` bytes for ERCOT/PJM/CAISO/MISO/NEISO (all
four rebuild-able lanes reproduce byte-for-byte, timestamps aside), and the
NYISO part was rebuilt fresh against the shard's `nyiso-64` (its bundle IS
committed): **NYISO = nyiso-64 = CALIBRATED-WITH-CAVEATS** — the corrected-
outage re-calibration recovered same-day, which the stale monolithic
`status.js` never showed.

**Pre-existing sidecar-only registrations flagged, NOT fixed here (need their
owning sessions to re-push artifacts):** three runs were registered without
their `runs/<id>.js` payloads — `2026-07-13-neiso-60-phantom-outage` (payload
AND `results/calibration/` bundle missing; its status part therefore still
carries the degraded 15:17 verdict — the FINDING doc says the true
determination is CWC, but the repo cannot substantiate it until the bundle
lands), `2026-07-13-nyiso-63-phantom-outage` (payload + bundle missing;
superseded as keeper by nyiso-64 but still parity-failing), and
`2026-07-13-nyiso-64-outage-refix` (the CURRENT NYISO keeper — bundle
committed but payload missing, so it is invisible in the Run Explorer). This
is the exact failure mode the calibration-report skill warns about; the
parity CI gate was removed 2026-07-14, so nothing caught it.
`check_registry_payload_parity.py` fails on all three; `audit_keepers` E1
fails NEISO + NYISO. Repair = regenerate each payload where its bundle lives
(`dashboard_add_run.py` re-registration, or re-push from the producing
session; NEISO also needs its bundle), then `build_status.py --iso NEISO`.

## 2026-07-19 — gas_daily_shape §3.7 interp-mislocation fix: all-ISO A/B (true-date + trade-date staircase); PJM + MISO keepers advanced

**Task (standing correctness follow-up from the miso-72 winter lane, spec
`docs/handoffs/miso-winter-fuel-security-design-2026-07.md` §3.7 — NOT a miso-N
session).** `gas_daily_shape_factors` resampled each month's Henry Hub daily
quote LIST with an even-spread `np.interp`, mislocating any convex single-day
spike bracketed by a trading-holiday gap (the Jan-12-2024 Heather Friday print
priced Jan-13) and linearly smearing every peak between quotes. Fix (PR #2565,
merged to main this session): a dated HH loader (`_henry_hub_daily_dated`, raw
+ clean branches) + `_trade_date_staircase` — quotes sit on their TRUE trade
dates, non-trading days carry the last trade forward (staircase, never an
interpolation across a gap; trade-date, not flow-date, because the HH daily
spot prints the price of its own trading day, unlike the next-day-delivery
citygate indexes that keep `_flow_date_staircase`). Mean preservation per month
holds EXACTLY by construction (divisor = the staircase's own calendar-day
mean), subsuming the G-A1 renormalization — no forcing. Rule 23: zero new
parameters; the fix re-derives from source-data handling only. Unit tests:
spike-on-true-date, holiday-gap staircase (Fri covers Sat/Sun/Mon), gap-free
month identity, no-quote months all-ones, off-state byte-inert (booby-trapped
loader).

**Affectedness (keeper `run_config.gas_daily_shape`):** CAISO/PJM/MISO/NEISO/
NYISO true, ERCOT false (byte-inert, no ERCOT arm). MISO's
`miso_winter_citygate_daily` supersedes only Chicago-zone winter cells; the
national shape is live everywhere else.

**A/B (rule 15: both arms registered, whatever the verdict).** Per ISO: main =
fixed code, base = pre-fix code (66879ac), SAME data + keeper recipe both arms
via `replay_keeper.build_kwargs`, full span 2023-2025 one bundle each. Both
arms inherit the 2026-07-19 +1h frame-defect fix (7e29e44), so base ≠ the
registered keeper bundle byte-for-byte; the A/B isolates the §3.7 fix alone.
Registered pairs: `2026-07-19-{caiso,pjm,miso,neiso,nyiso}-gasshape-interpfix`
(+`-base`).

**Result — the expected signature everywhere, and nothing else (rules 13/14):**
annual mean LMP moves ≤$0.10/MWh in every ISO-year; hourly relocation
concentrates exactly in the gap-bracketed spike windows.

- **PJM**: mean Δ ≤$0.01 all years; 2024 max |Δ| $81/MWh at h359 (the Heather
  weekend), 2025 max $54 (Jan cold snap); 647/1353/1903 hours >|$1|. Verdict:
  **CALIBRATED**, every scored criterion PASS (base identical minus C7/C8
  scoring). **Keeper advanced** to `2026-07-19-pjm-gasshape-interpfix`
  (owner-authorized in-session).
- **MISO**: mean Δ +0.00/+0.10/+0.08; 2024 max |Δ| $60 at h358, 2025 max $36;
  409/1217/1327 hours >|$1|. Verdict: NOT-YET on the same ledgered irreducible
  {C3a-2025, C3c} tail as miso-75 (out of scope), C3a-2025 improves −15.3% →
  −15.1%. **Keeper advanced** to `2026-07-19-miso-gasshape-interpfix`
  (owner-authorized in-session).
- **CAISO**: 2023/2024 price-identical (the measured citygate daily overlay
  supersedes the national shape); 2025 mean −$0.04, 207 hours >|$1|, max $22.
  **No keeper action**: the CAISO keeper advanced to caiso-102-hourfix
  mid-session (PR #2563), so this A/B (caiso-97 recipe) registers as probes.
- **NEISO / NYISO**: exactly price-inert all years — the hub-basis daily
  overlays (AGT / Transco legs) replace the gas rows in every covered month, so
  the national shape never reaches dispatch. Registered as inertness probes; no
  keeper action (NYISO's keeper also advanced mid-session to nyiso-64).

**Ops.** Ten full-span solves, years sequential within each invocation, arms
concurrent for CAISO/NEISO/NYISO, PJM/MISO solo (P1 peaks ~15/11 GB; 12 G swap
file); base arm from a sparse pre-fix worktree via `MARKET_SIM_DATA_ROOT`.
Fresh-checkout restorations: `transfer-interface-limits`/`ramp-capability`/
`capacity-deliverability`/`winter-fuel-inventory`(+NYISO) clean partitions
rebuilt, `pjm-da-virtuals` re-fetched (fail-loud caught it). Retention sweep
pruned pjm-102/102b, caiso-84-gas-spot, miso-70-tier-base.

## 2026-07-24 — CROSS-ISO: the CAMPD unit-outage detector books economic layup as outage in ALL SIX ISO extracts

Escalated from the NEISO lane (`neiso-63`, 2026-07-24; evidence
`results/calibration/FINDING-neiso63-campd-economic-layup-2026-07.md`). Data-layer
audit only — no solve, no keeper change, no parameter touched, any ISO.

**Finding.** `scripts/lib/outage_detect.py::filter_revealed_outages` keeps a down
span when it is down through ≥24 local high-net-load hours, or when it is a
≥5-day full stop below `FULL_STOP_OVERRIDE_CF`. Its override docstring states the
governing premise — *"economic idling backs down but does not fully stop for
weeks"* — which is **false for a gas CC priced out of merit for weeks**. Both
surviving branches therefore keep exactly the windows a sustained economic layup
produces. Validated against ISO-NE's published Section 3 outage series for NEISO:
the detector reproduces the published series in autumn (0.86–1.06×), when real
maintenance dominates, and diverges 1.76–2.76× in winter, when New England CCs
are priced out by basis.

**Scope — every ISO.** CC capacity-year booked as outage, 2023–2025: ERCOT 24 %,
MISO 23 %, PJM 23 %, CAISO 37 %, NEISO 39 %, **NYISO 46 %**; PJM COAL 42 %,
MISO COAL 30 %. Real CC EFOR + planned maintenance is ~10–15 % combined. Median
repeat-event count is 3–7 separate "outages" per unit-year (max 26, ERCOT).

**Why 2026-07-19 missed it.** That re-audit screened the ERCOT-79 *daily-cycling*
phantom (overnight gaps folded into one summer-long window). This is a different
fingerprint — multi-week full stops, seasonally anti-correlated with the
published maintenance profile — and passes the daily-cycling screen cleanly.

**Consequence.** Where a keeper's offer curves were calibrated against the
over-counted envelope they are co-dependent on it (rule 11). Demonstrated for
NEISO: relieving the over-count moved mean LMP −7 to −9 % and halved h>$200.
Each ISO needs the same published-vs-detector check before its keeper is trusted
on availability; the four DAM-first gates wired 2026-07-24 (`caiso_dam_outages`,
`miso_native_outage_source`, `neiso_operable_capacity_availability`,
`pjm_dam_availability`) supply the instrument for CAISO/MISO/NEISO/PJM at no
solve cost. ERCOT and NYISO have no native gate and need another cross-check.

**Ruled out as fixes** (tested on NEISO, recorded so they are not rebuilt):
unit-level frequency filtering (fixes shape, destroys level — the contamination
is **window-level**) and common-mode/class-simultaneity discrimination (seasonal
correlation worse than no filter at every threshold, because genuine shoulder
maintenance is itself clustered). Leading candidate is a **merit-order guard**
(delivered fuel price × heat rate; rule-13 admissible), which is a mechanism
change requiring its own charter, a frozen design, and LOYO scoring (rule 22).

**Recommended governance posture.** No marker or frontier withdrawn on this
finding alone — unlike nyiso-63 the NEISO determination held and the fit
improved. But holdout spending should be frozen across ISOs until the detector
settles, since validation/locked years scored against an availability envelope
that is about to change are wasted signal.

## 2026-07-26 — CROSS-ISO VERDICT: merit-order guard ADOPTED-AS-IMPROVEMENT; holdout freeze HELD

**Owner charter verdict** (campd-economic-layup-fix-charter-2026-07.md §8, out of
the three options on record — adopt+lift, adopt+hold, close-with-cause): **adopt
+ hold the freeze.**

**Adopted.** The neiso-64 merit-order guard (charter §3a frozen design: a window
is economic layup when the unit's measured `SRMC = HR × delivered fuel price`
exceeded `RCC(t)` — the capacity-weighted p90 SRMC of the units measured running
that hour — for ≥90 % of its hours) merges into `scripts/lib/outage_detect.py` /
`scripts/data/derive_campd_unit_outages.py`, default-off
(`MERIT_ORDER_GUARD_ENABLED = False`, `--merit-order-guard`). Every ISO's
committed `campd-unit-outages[-<ISO>].csv` is re-derived guard-on; the vetoed
windows move to `campd-unit-outages-layup-<ISO>.csv` companions no loader reads
by default. Evidence basis: placebo-graded validation against each ISO's
published instrument (ERCOT 3/3, NEISO 2/3, MISO 2/3, PJM 1/3 with baseline r
already +0.90, CAISO 0/3 honest null, NYISO no instrument), the ISO-NE
outage/uncommitted positive control, and the NEISO keeper re-audit
(`2026-07-25-neiso-64-meritguard-a1`: C3a and C3b improve in all three years,
nothing regresses — fix-in-place, keeper unchanged).

**Not a closure.** NEISO 2023–24 still runs 1.29–1.36× a whole-fleet published
total on a thermal-only extract, so a residual over-count survives the guard.
The neiso-63 finding stays open on that residual.

**Freeze HELD.** `holdout-freeze.json` stays `active=true` (history entry
2026-07-26). No out-of-training year is solved, scored, or registered anywhere
until the owner lifts it explicitly.

**Follow-ons this session:** cross-ISO keeper re-audits on the corrected
envelope (ERCOT first — 3/3 placebo, largest reclassification share — then PJM,
MISO, CAISO, NYISO; 2023–2025 one bundle each, rule 16; both arms registered,
rule 15, with A0 = the keeper itself since the guard is byte-inert off), and the
CAMPD↔CAISO resource crosswalk (turns the weakest instrument into per-resource
ground truth; dedupe the raw parquet to one row per outage mrid first).

## 2026-07-26 — caiso-123: the CAISO "RE-TUNE REQUIRED" cell of the guard re-audit rests on a CONFOUNDED A0 — trigger withdrawn as stated, re-derived onto the 07-24 extract-content change; guard's own isolated effect is −0.18 % (favourable)

**Notification to the campd-economic-layup charter lane** (charter §8 amended in
place; full record `results/calibration/FINDING-caiso123-c3a-drift-attribution-2026-07-26.md`):

- The CAMPD unit-outage extracts were **derived-not-committed until 07-24**
  (no `campd-unit-outages*.csv` main extract exists in any pre-07-24 tree, any
  ISO); every session derived its own. The CAISO keeper
  (`2026-07-23-caiso-netrev-margin-keeper`) solved on a session-local
  **partial** derivation whose bytes are unrecoverable and which **no full
  derivation regenerates** (keeper-era script re-run reproduces today's full
  in-window mass to 0.1 MW).
- PR #2842 committed a light partial CAISO extract; PR #2844's owner-ordered
  "re-derive in full" added 642 genuinely-new 2023–25 windows (504
  CC_REGULAR). Every post-07-24 solve reads the full envelope. Same-HEAD
  isolation: extract content **+1.24 % λ-2025 / CC_REGULAR −0.49 TWh /
  import +0.42 TWh**; the guard step alone **−0.18 %** (caiso-122, confirmed
  directionally at today's HEAD).
- The caiso-120 A0/A1 (+10.0 → +11.1 % C3a-2025) therefore conflated the
  extract-content change with the guard: "A0 = the keeper by construction"
  held for the guard *flag*, not the extract *file*. **Do not re-tune on that
  number.** The re-derived predicate: the keeper's C3a-2025 PASS leaned on the
  non-reproducible light envelope (rule-11 class); any honest full derivation
  fails C3a-2025 by ~+1.1 pp. CAISO re-tune vs. the residual-over-count
  investigation (freeze lift condition) sequencing is an owner call.
- NYISO's cell is unaffected by this confound (#2842/#2844 touched only the
  CAISO extract). The A0-validity lesson generalizes: a re-audit's "A0 = the
  keeper" holds only if EVERY input byte is unchanged, and derived-not-committed
  inputs violate that silently. `basis_sha` (landed, caiso-123) plus the
  recommended derived-input content-hashing in `shared_inputs` close this
  class.

## 2026-07-26 — CAMPD economic-layup charter, LANE B: the day-grain `R < 0` cut does NOT replace the guard's window-grain cut (cross-ISO, no lane number)

Charter/cross-ISO session; **no per-ISO lane number claimed**. Measurement only —
no guard change, no extract re-derive, no LP solve, no keeper touched, no
dashboard registration.

`FINDING-neiso67-...` §6 item 2 flagged the day-grain best-block `R < 0` cut
(out of merit across the best feasible ≥ min-run block in the DA horizon) as a
possible **replacement** for the merit-order guard's window-grain out-of-merit
cut, in its existing marginal lane (rule 19 `[R-ONE-MECH]` — never an addition).
Validated on every ISO carrying a published anchor (charter §4): **CAISO** (CNOG
revision-aware build only, neiso-66 §1), **MISO**, **PJM**, **ERCOT** (with its
offered-vs-available caveat), **NEISO**. **NYISO excluded — no anchor, and none
improvised.** Sweep `--rcc-pctl {0.50, 0.75, 0.90, 0.99} × --horizon
{24, 48, 72}` × 2023–2025 = **180 cells**, each on the full D1 standard.
Probe: `scripts/probes/_campd_daygrain_crossiso.py`.

**NEGATIVE on all three legs of the stated bar.** The candidate beats the
incumbent in **82/180** cells (median Δ **−0.0003**, |Δ| < 0.02 in 159/180); it
is sign-stable across all three years in **9/60** configurations, every one of
those gaining +0.002 to +0.017; and it clears the proportion-matched placebo in
**101/180** cells against the incumbent's **105/180**, the 14 disagreements
favouring the incumbent 9–5. No reference-price level and no horizon rescues it
— lengthening the horizon makes it monotonically worse on NEISO and moves
nothing elsewhere.

**Why the flagged observation looked strong.** Its `+0.63…+0.79` vs
`+0.08…+0.31` compared the **two opposite sides of the guard's own split** —
an identified-layup series against the guard's KEPT/mechanical series. Against
the correct comparator, the guard's own VETOED series, D1 already stood at
+0.77 / +0.71 / +0.67 vs the candidate's +0.70 / +0.74 / +0.53 (NEISO,
p90/h24, vs published `uncommitted_available_gen_nonfast_mw`).

**Why the head-to-head is flat.** The two cuts select the same windows —
Jaccard 0.77–0.97 (median 0.92); over 15,782 scored windows the day-grain cut
vetoes **127** the incumbent does not (0.8 %) and the incumbent vetoes **144**
the day-grain cut does not (0.9 %), and on NEISO and CAISO the candidate's veto
set is a strict **subset** of the incumbent's in every year. The block integral
changes the verdict on ~1 window in 60.

**Controls.** The re-implemented incumbent reproduces each ISO's **committed**
kept/layup split on **99.1–99.8 %** of windows; the ported machinery reproduces
neiso-67's own idle-capacity band (812 MW/+0.70, 1,104/+0.80, 1,071/+0.64 vs
812/+0.70, 1,114/+0.79, 1,074/+0.63) and the charter D1 anchors (NEISO 2023
baseline 1.52×/+0.53, guard-on 1.37×/+0.69, vetoed-vs-UNCOMMITTED +0.77).

**Consequences.** No guard change is proposed, so the charter §5 blast radius is
not reopened and no rule-22 leave-one-year-out obligation arises. `MERIT_OOM_FRAC`
was held at 0.90 for both cuts throughout (rule 23 — re-tuning it to flatter one
cut would be fitting to a residual). **The freeze stays ACTIVE**; Lane B was
never one of its conditions, and only the owner lifts it. Charter §9 updated.
Record: `results/calibration/FINDING-campd-daygrain-crossiso-2026-07-26.md`.

## 2026-07-26 — CAMPD economic-layup charter: the PJM keeper re-audit cell is RESOLVED (pjm-129, RE-TUNE REQUIRED) and its RAM block is CLOSED — the "≥24 GB" conclusion was wrong

Charter cell (`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §5/§8),
executed in the PJM lane as **pjm-129**. Registered arm
`2026-07-26-pjm-129-meritguard-a1` (2023/2024/2025, one bundle, rule 16; rule 15).
Full record: `results/calibration/FINDING-pjm129-keeper-reaudit-meritguard-2026-07.md`;
per-ISO entry in `docs/calibration-log/pjm.md`.

**Verdict:** `CALIBRATED` 10/10 → **`NOT-YET` 7/10, RE-TUNE REQUIRED** on C3a-2025
(−9.3 → −10.6 %), C3c tail 2024 (0.50× → 0.39×) and 2025 (0.66× → 0.47×), plus
C1-2023 CC_REGULAR (−7.87 → −8.10 TWh, 0.10 TWh past an 8 TWh band). Isolation, not
attribution: a same-HEAD probe with the extract reverted to the keeper's blob
reproduces the keeper's committed 2025 hourly sidecars at `max|diff| = 0` on every
column, so post-keeper **code** drift is **$0.000** and the guard/extract owns
**100 %** of the −$0.518 (−1.3 pp) move. Rule-11 discovered bug; corrected extract
stays in (rule 1); nothing tuned; keeper designation unchanged (owner call).

**With this cell, all six ISOs carry a registered re-audit arm** — NEISO and ERCOT
fix-in-place, CAISO / NYISO / MISO / PJM re-tune-required. What remains under the
charter is the **owner's freeze-lift decision** (§9) plus four keeper-lane re-tunes.
**The freeze stays ACTIVE and this session does not lift it.**

### A governance correction worth carrying: a resource conclusion was wrong for two sessions

Two prior sessions concluded the PJM replay "needs a ≥24 GB environment" after
SIGKILLs at 15.9 GB, and that conclusion propagated into `RESULTS-neiso65-...` §3e,
the PJM log, and this charter. It was wrong. Measured per solve-year from the
release-block telemetry already in the code:

| year | `resident` after release | single-year `peak` |
|---|---|---|
| 2023 | 1.06 GB | 14.87 GB |
| 2024 | 1.19 GB | 14.94 GB |
| 2025 | 1.26 GB | 15.06 GB |

`peak(N+1) + floor(N)` = **15.93 GB at year 2**, reproducing the reported 15.9 GB
kill to 0.03 GB at the year both attempts hit it. **The year loop is not leaking**
(its `del` + `gc.collect()` + `malloc_trim` block releases to a floor that
miso-90/92 already attributed and reduced 35 %); the **single-year LP peak is the
ceiling**, and one fresh process per solve-year fits every PJM year in the standard
15.7 GB box. The recipe was already documented in `pjm121_ccbelt`'s **own
attestation** ("one fresh process each, ~15 min/year, peak ~14.8 GB"), and
miso-92/93 had already established it for MISO. Two lessons:

1. **A resource verdict is a measurement, not an inference from a kill.** "OOM at
   year 2" plus "2023 fits alone" was read as *the box is too small*; the two
   numbers that discriminate leak-vs-ceiling were one already-emitted log line
   away, and were never read. Quote `resident` and `peak` before asking for
   hardware.
2. **Cross-lane findings did not reach the lane that needed them.** miso-90/92
   attributed this floor and miso-93 used the staged recipe to land a MISO 3-year
   bundle in this same container, *before* the second PJM attempt concluded ≥24 GB.
   The blocked-cell text in `RESULTS-neiso65-...` §3e and the PJM log should be
   read as superseded.

---

## 2026-07-27 (miso-95) — derived artifacts carry no vintage stamp, and all five `thermal_tranches_<ISO>.csv` are provenance-orphaned

Cross-ISO, no-solve. Full evidence:
`results/calibration/FINDING-miso95-thermal-tranches-provenance-2026-07.md`.

**Finding.** None of the five committed `thermal_tranches_<ISO>.csv` artifacts
reproduces from a HEAD re-derive on any constructible input vintage. Two of the
staleness axes are cross-cutting and neither was caught by an existing gate:

1. **The merchant-CC summer-capacity guard** (`fleet/eia860.py::_reconcile_cc_pmax_to_nameplate`).
   Every artifact was derived with `apply_cc_summer_guard=False`; disabling it
   reproduces `nameplate_mw` exactly on all 848 rows across MISO/PJM/CAISO/NYISO/NEISO.
   Because the tranche percentages are ratios over that nameplate and the model
   applies them to the **guarded** pmax, ~**1,090 MW** of CC min-stable floor is
   understated one-sided across the five ISOs (MISO ~766 MW). This landed as a
   **code** change, so rule 23 `[R-FROZEN-DERIVE]`'s source-data trigger never
   fired and nothing downstream re-derived.
2. **An upstream CAMPD-hourly / parasitic-factor vintage move**, visible as a
   small two-signed ±10–400 h drift on ~84 of MISO's 198 `ok` rows. **Not
   recoverable**: the repo is a shallow clone and `git log` on
   `data/raw/campd-unit-level/` returns a single merge commit.

**Two governance gaps, both owner calls.**

* **(a) No derived artifact records the vintage of the raw data it was built
  from.** A `campd_vintage` provenance header (fetch date + per-source file hash)
  written by every `derive_*` / `curate_*` script would have answered this session
  in one `head -1`, and would make "does this artifact reproduce?" a check rather
  than a multi-arm investigation. Generalizes well past the tranche family.
* **(b) Rule 23's trigger is data-only, so a code change to a deriver's *inputs*
  silently orphans its outputs.** The CC guard is the worked example: correct
  change, correctly landed, and five downstream artifacts quietly stopped
  matching the fleet the LP runs on. Candidate: a CI check that re-derives the
  cheap artifacts and fails on drift, or at minimum a registry of
  `deriver → committed artifact` edges checked when a deriver's input path changes.

**Also itemized (LANE 2 residue).** `6a8f285` stripped rows from all six ISOs'
std unit-outage extracts (MISO −2,424, PJM −3,246, NYISO −3,037, NEISO −1,294,
CAISO −810, ERCOT −3,484) and re-derived no downstream artifact.
`campd-unit-outages-short-PJM.csv` is the one stale, un-actioned consumer with a
live flag (`unit_outage_short_windows`) and a clean single-delta A/B available —
its MISO twin's control passed in miso-94. Solve-side exposure is already covered
by pjm-129 and miso-93/94 and should not be re-run.

## 2026-07-27 (nyiso-86) — the demand-basis wedge is a FLEET-WIDE property: screened across all six keepers, MISO carries the largest (+3.7 %/+3.1 % of load)

The nyiso-86 reconciliation (`docs/FINDING-nyiso-calibration-reconciliation-2026-07-27.md`
§2.1–§2.3) found NYISO's only load-bearing C1 fail is dominated by a
**demand-basis wedge**: the model serves the BA-reported metered-load basis
(EIA-930 Demand ≡ NYISO pal, verified identical) with a lossless LP, while C1
scores plant-metered EIA-923 + tie-metered imports — a +2.1–2.9 %-of-load gap
absorbed entirely by the free gas family. Since the wedge is a property of the
scoring design, it was screened across ALL SIX current keepers from committed
payloads + bench parts (no solves; balance closure over classFull keys verified;
2025 excluded as preliminary-vintage):

| ISO | 2023 / 2024 wedge (TWh) | % of load | disposition |
|---|--:|--:|---|
| ERCOT | −2.2 / +0.7 | ≈0 % | generation-referenced native load; nothing to do |
| PJM | −0.3 / +5.9 | ≤0.7 % | no wedge; ~7 TWh internal export-accounting ambiguity noted for the PJM lane |
| NEISO | +0.7 / +1.2 | ~1 % | real, under-band; record only |
| **MISO** | **+23.8 / +19.7** | **+3.7 / +3.1 %** | largest in the fleet — 3× MISO's 8 TWh C1 band cap; MISO lane must run the NYISO chain of custody and identify its own factor |
| CAISO | −4.8 / −7.4 | −2.3 / −3.5 % | NOT a loss wedge (wrong sign): model imports +8.0/+10.3 TWh over the measured net interchange — a seam-volume reconcile, no demand gross-up until that is resolved |
| NYISO | +2.9 / +4.2 | +2.0 / +2.8 % | lane nyiso-87 (td_loss_factor + CHP pair) |

Protocol (rule 25/23-clean): one existing field — `td_loss_factor`
(scenarios.py:4412, default 0.0 everywhere) — identified per ISO from that
ISO's own measured 923+NI-vs-served-load reconciliation, armed only in that
ISO's keeper lane with LOYO, never bulk-applied. The screen is not an
identification: a wedge can be seam accounting (CAISO's is) rather than
losses, so each lane repeats the chain of custody (930 demand vs native load
files vs 923+NI) before choosing a value. The fix is a gross-up to the
generation basis, not a demand-source swap — where the BA reports its metered
load to EIA-930, the native load files are the same series.

## 2026-07-27 (cross-ISO) — merit-order guard FALSE-NEGATIVE audit: no CONFIRMED cell; 4× SUSPECT on tight-hour placement only, population test clean everywhere

Owner-raised question, pre-registered no-LP probe over all six ISOs ×
2023–2025 (`scripts/probes/guard_falseneg_audit.py`, verdict rules committed
before the run). Full evidence:
`results/calibration/FINDING-guard-falseneg-audit-2026-07-27.md`.

**Verdicts (pre-registered, unmet-means-dead):** ERCOT / CAISO / NEISO / PJM
**SUSPECT** (D3 tightness placement fires, D2 population test clean);
MISO **CLEAN** (both discriminators clean, the guard's intended signature);
NYISO **UNVERIFIABLE** (no published anchor; none improvised).

**The strong form of the hypothesis is refuted:** in all 15 anchored
ISO-years the DROPPED windows sit at or below the placebo p50 against the
published mechanical-outage series (NEISO's two-population instrument shows
them tracking published UNCOMMITTED at +0.67…+0.77 instead, reproducing the
charter §3a D1 control exactly). The guard selects the layup population it
was designed to select. Secondary: the guard-KEPT extracts track their
published instruments at r +0.61…+0.95 in every anchored ISO-year — the
NEISO positive control generalizes to all five anchored ISOs at no solve
cost.

**What survives is hour-grain:** D3 fires in 10/15 anchored cells — the
returned capacity sits on the tightest net-load quartile at near-uniform
rates (PJM worst: 3/3, ~2.8–5.0 GW per average tight hour, the C3c-relevant
magnitude) — but the post-hoc length-preserving placement null (disclosed at
the site, never a verdict input) attributes most of that to window-length
composition: kept windows are strongly tight-avoiding (below null p5 in
18/18 cells), dropped windows weakly so. Whether "weakly tight-avoiding" is
just layup timing or dilution by a broken-while-uneconomic sub-population is
unmeasurable on committed instruments — hence SUSPECT, not CONFIRMED or
CLEAN.

**PJM consequence:** no named root cause is handed to the PJM re-tune;
FINDING-pjm132 §5's frontier assessment stands unchanged. The lane hands the
G-20b/G-22 reserve-tightness question a quantified SUSPECT-grade lead, not a
cause. **Recommendations:** NYISO anchor intake (converts UNVERIFIABLE to
measurable); any within-window tight-hour treatment is a separate owner memo
that must confront charter §3a D2's "not shortened" decision and neiso-68
(rule 19 — replacement, never stacking). No guard parameter moves on this
finding (rule 23); SUSPECT is not to be quoted as CONFIRMED downstream. No
solve ⇒ nothing registered (rule 15).

## 2026-07-28 — Bench multi-class collapse: cross-ISO scorer fix, committed artifacts migrated, all keepers re-scored — no gate moves

**What changed (scorer-only; no LP, no mechanism, no keeper change).** The
nyiso-88 §5 defect — `render_calibration_html.build_payload` keying `mw_p`/
`grp_p` by `plant_code` while iterating `(plant_code, klass)`, collapsing every
multi-class plant's whole measured series onto its alphabetically-last class
and dropping the other classes' model dispatch — is characterized across all
six ISOs, fixed, and the committed artifacts migrated in place. Per-plant
bench/payload entries are now keyed `"<code>"` (single-class, byte-unchanged)
/ `"<code>:<KLASS>"` (per class slice); measured series split on a measured
basis ladder (CAMPD unit-level hourly shares → EIA-923 per-prime-mover monthly
→ EIA-860 nameplate proration, used once) in `scripts/lib/bench_multiclass.py`;
migration `scripts/migrate_bench_multiclass.py`; probe
`scripts/probes/bench_multiclass_collapse.py` (correction table produced BEFORE
the fix); pinned by `tests/scoring/test_bench_multiclass_split.py`; contract
§3.2/§3.3 updated. Blast radius measured: MISO 12–13 % of benched CEMS energy
(whole coal plants scored as CT_PEAKER, ±20–25 TWh/yr/class), NYISO ~10–12 %,
PJM 2.5 %, CAISO/NEISO ≤0.2 %, ERCOT 0 (binning books one class per plant).

**Re-score result: every keeper's determination and every criterion/record
status is UNCHANGED.** NYISO C1 CC_REGULAR 2023 (−2.78 of ±2.94) is
bit-identical — C1's classFull/gmModel never routed through the collapsed
grouping, so the nyiso-89 keeper's thin C1 margin was never contaminated. The
real damage was in the D-1 shape actuals and the MISO C2 coal anchor: MISO
CT_PEAKER cv_ratio 2.26→1.01 (the "model too peaky" signal was benchmark
contamination), coal_cems 176→192.5 TWh, NYISO/PJM CT_PEAKER cv_ratio toward
the model — all inside bands. Discovered and left for owner scoping: MISO
ST_CHP model diurnal profile is anti-correlated with its true actual
(profile_r ≈ −0.75..−0.80; ungated/exempt today). Full record:
`docs/FINDING-bench-multiclass-collapse-2026-07-28.md`;
`results/calibration/bench_multiclass_collapse.json` +
`bench_multiclass_migration_report.json`.

## 2026-08-01 — xiso-1: diurnal price-amplitude compression is SYSTEMIC at all six ISOs (cross-cutting audit, NO LP)

**Arm A of the xiso-1 brief. No LP solved, no config changed, no bundle
produced, no keeper touched, no dashboard registration** (rule 15
`[R-DASHBOARD]` binds bundles; there is none — same disposition as
neiso-71/73/74). Record:
`results/calibration/FINDING-xiso1-diurnal-price-amplitude-is-systemic-2026-08-01.md`,
transcript `PROBE-xiso1-diurnal-amplitude-audit-2026-08-01.txt`, probe
`scripts/probes/_xiso1_diurnal_amplitude_audit.py`.

**The question.** neiso-74 sized NEISO's keeper at 24–30 % of the measured
diurnal price amplitude with level and phase both correct, and left open
whether that was NEISO-specific. Two other ISOs already carried a same-shaped
finding by different routes (miso-89, pjm-139/140/141), but nobody had measured
all six with one construction.

**The construction** (portable, zero LP, no re-solve): each ISO's CURRENT
keeper — resolved live from `frontend/data/backcast/keepers/<ISO>.json` through
the registry, so the probe re-reports against whatever the keepers are —
`hourly/system_<year>.parquet` `pass == "P1"`, zone duals load-weighted by the
model's own hourly zonal demand (the C3a basis; `price` is already the
delivered price, overlays folded in by `_system_frame`), against the committed
`data/raw/_validation-source/actual_lmp_hourly_<ISO>.parquet` hub DA/RT. Both
sides are already on the model's chronological 8760 calendar, so they pair
hour-for-hour with no re-keying — that is what makes one construction serve six
ISOs. Validated by reproducing neiso-74's NEISO numbers exactly on the swapped
loader.

**The answer: systemic.** All **36** ISO × year × benchmark cells compress, in
the same direction, with the same signature — daily MAX under-priced in
**36/36** (−7.5 % … −65.5 %), daily MIN over-priced in **36/36** (+5.9 % …
+146.0 %), hour-of-day amplitude **19.9–92.2 %** of measured (mean **40.5 %**
vs DA, **43.9 %** vs RT) while the annual LEVEL is right to a mean absolute
**7.1 %** and the PHASE is right in **34/36** rows (hour-of-day correlation
+0.853…+0.980). Per-ISO amplitude vs DA, 2023/24/25: ERCOT 52.9/38.2/36.7
(2023 uninterpretable — its level is −36.4 %), CAISO 46.5/52.9/**75.9**, PJM
31.6/36.5/34.2, MISO 34.0/36.3/25.2, NYISO 52.0/50.9/44.5, NEISO
27.1/**23.6**/29.9.

**Controls, all reported against interest.** Simple-zone-mean instead of
load-weighted moves amplitude ≤4.3 pp. MISO's committed hourly ZONAL actual has
a *smaller* hour-of-day range than the hub, so scoring on it **softens** the
finding (25.2 → 26.5 % in 2025). $200 body-censoring *raises* several RT ratios
(MISO 2025 12.2 → 17.9 %), confirming part of the raw RT daily spread is
genuinely the price tail — which is why the tail-insensitive hour-of-day range
is the quoted statistic and the raw daily-spread ratio is not. CAISO 2025 vs RT
reads **92.2 %**, one ISO-year where the defect is nearly absent — the strongest
evidence against reading this as a mechanical property of a dual-priced LP.

**Reconciliation, not re-discovery (rule 19 `[R-ONE-MECH]`).** pjm-141's
31/33/32 %, miso-89's 29–47 %, nyiso-109's 69/49/45 % and neiso-74's 24–30 % are
four constructions of THIS defect at four ISOs. Treat the existing ISO-local
diagnoses as its local reports; do not re-derive them.

**Cross-ISO attribution.** In every ISO the peaking/oil classes are ALREADY
ONLINE at the overnight trough (2/4 to 4/4 classes), so the same offer band is
marginal at both ends of the day. The two ISOs where a zero-MC block absorbs
95–99 % of the model's own diurnal demand swing (ERCOT/CAISO solar) are the
LEAST compressed; the four where a thermal class absorbs it are the MOST. Stated
as an observation on six points — not a mechanism, not a lever.

**Rubric gap re-filed, scorer NOT changed (OWNER CALL).** No load-bearing
criterion sees this at ANY ISO: C3a is a level test, C3b
(`calibration_verdict.py::score_price_shape`) is a TWELVE-MONTH load-weighted
NRMSE for **every** ISO and is structurally blind to hour-of-day, C3c is a
tail-hour count, and C7/D-1 scores class *dispatch* shape (SKIPPED at NEISO).
Sharpest statement of the gap: **PJM's keeper is fully `CALIBRATED` —
`price_mean`/`price_shape`/`price_tail` all PASS — at 31.6/36.5/34.2 %
amplitude.** neiso-74 filed the question for NEISO; this audit shows it is the
rubric's at all six. The statistic, if the owner wants it gated, is already
computed and costs zero LP.

**What this licenses.** A *structural* account is now one cross-ISO question
rather than six ISO-local ones, and each lane has its own measured size.
It opens **no adjudicated cell** (PJM's family is owner-closed with an empty
lever queue; NEISO §5.6 item 1 still needs its own owner charter — neiso-74 gave
it a target, not a charter, and this audit grants none), **transfers no verdict**
(rule 25 `[R-ISO-SCOPE]`), and **licenses no parameter** — an adder sized to a
~38 pp amplitude gap is a value fitted to a residual (rules 5/21/24), and the
defect being systemic makes that more tempting and no more admissible. A
successor must not be graded on the amplitude ratio alone: neiso-74's caveat
generalizes (NEISO's real PS fleet realizes only 45 % of the DA-price
perfect-foresight optimum).

**Governance.** Years 2023–2025 only; holdout spend freeze ACTIVE, nothing
outside the training window read (rule 20 `[R-HOLDOUT]`). Matrix row
`diurnal_price_amplitude` added, cells `UUGGOU` (rule 28c); §5.7 audit row
updated; keeper stamps re-checked (`check_mechanism_matrix.py` clean).

**DO-NOT-REDO:** do not re-measure cross-ISO diurnal amplitude by hand — re-run
`scripts/probes/_xiso1_diurnal_amplitude_audit.py`, which reads the live keeper
store. Next cross-cutting shorthand: **xiso-2** — §5.7's oldest open audit, the
post-guard re-derivation sweep of outage-derived artifacts across all six ISOs
(flagged 2026-07-26, still unaudited, mechanical and no-LP).

## 2026-08-02 — xiso-2: post-guard provenance census of the outage-derived artifacts — §5.7's OLDEST open audit CLOSED, and NO KEEPER IS AFFECTED (cross-cutting audit, NO LP)

**The flagged risk was real but has largely already been discharged.** The
2026-07-26 flag — "downstream derived artifacts not yet re-derived post-guard, an
open cross-ISO audit" — has sat unaudited since the merit-order guard was adopted.
It is now answered for all six ISOs, mechanically and at **zero LP**: no solve, no
scoring, no registration, no bundle. Probe
`scripts/probes/_xiso2_outage_artifact_provenance_census.py`, record
`results/calibration/FINDING-xiso2-outage-artifact-provenance-census-2026-08-02.md`,
transcript `PROBE-xiso2-outage-artifact-provenance-census-2026-08-02.txt`.

**The construction.** The guard-landing boundary is commit `6a8f285c5`
(2026-07-26 00:36 UTC, neiso-65, "adopt guard-corrected CAMPD extracts, all six
ISOs + layup companions"). Membership is tested with `git merge-base --is-ancestor`
rather than by date string — which matters, because the one keeper-consumed
artifact in the census was re-derived **the same calendar day** as the guard.
Producers were split into **real readers** (an actual file read) and **docstring
mentions**: the naive grep returns ~60 files, most of which never open an extract,
and seven are excluded by inspection and enumerated so the exclusion is checkable.

**The answer: 5 of 6 extracts re-derive BYTE-IDENTICALLY at HEAD.** Each ISO was
re-derived with the committed recipe (`--years 2018 … 2026 --merit-order-guard`)
and md5-compared: **ERCOT, CAISO, PJM, NYISO, NEISO all match exactly.** That is a
strong positive control on the whole family — the detector is deterministic, the
committed extracts are authentic, and the guard's classification reproduces.

**MISO is the sole mismatch, and it is fully attributed and training-clean.** Its
re-derivation is a strict **superset** — **+17 windows, 0 lost, ALL 17 of them 2022
`COAL`** — and its layup companion is **byte-identical**, so the guard's own
classification reproduces exactly; the 17 are in *neither* committed file, i.e.
never detected rather than detected-and-vetoed. Not detector drift: nothing has
touched the detector or `data/raw/campd-unit-level/` since the guard. Root cause is
a **source-data change** — commit **`5cd937407` (2026-07-31), "fill the CISO/MISO
2022 wide-hourly hole"** — which took MISO's EIA-930 2022 from **7 rows to 8,760**
(8,757 non-null `Demand`); the revealed-availability filter needs that system load,
so the 2022-only, coal-only signature is exactly what it predicts. **The 2023–2025
training window is IDENTICAL row-for-row** (3,659 rows each side), so the entire
divergence sits inside the **2022 validation holdout** and **no MISO keeper reads a
stale byte**. Re-derivation is rule-23 **admissible** (a cited data change), **not
urgent**, must cite `5cd937407`, and must **not** ride along in a calibration
session. **Against interest:** the same commit filled CISO's 2022 hole and **CAISO
still reproduces byte-identically** — the 930 fill is not a universal invalidator,
and the MISO result does **not** transfer (rule 25 `[R-ISO-SCOPE]`).

**No keeper consumes a stale outage-derived artifact, at any ISO.** The only
keeper-consumed artifact downstream of an extract is NYISO's NYC/LI/Capital
`ST_GAS` reliability-floor limbs, and **nyiso-81 re-derived them 18 hours AFTER the
guard the same day** — clean. The other five ISOs' `reliability_floor_coeffs_*.csv`
are **not** downstream of the outage extracts at all (no `*_drag` or
`derive_reliability_coeffs` producer reads one), so their 06-30…07-08 dates are not
a staleness finding. Two artifacts *are* genuinely pre-guard and **neither is
keeper-consumed**: `MAINTENANCE_MONTHLY_SHAPE` (2026-06-25, **forecast-mode only**,
default on) and `caiso-dam-resource-crosswalk.csv` (2026-07-19, **zero** code
consumers — provably inert, a documentation artifact). `data/clean` is gitignored
and has no staleness surface by construction.

**One live code defect found and FIXED.** `derive_maintenance_shape.py` pooled
`glob(campd-unit-outages*.csv)`. Since the guard, that glob also matches the six
**`-layup-` companions — the economic-idling windows the guard EXISTS to veto, so
pooling them partially INVERTS the guard** (rule 19 `[R-ONE-MECH]`) — plus the
`-e923-` non-CAMPD fallback, the `-short-` and `-maxgen-` companions: **24 files /
58,744 rows drawn where 6 / 39,755 were intended, +47.8 % row inflation.** It was
harmless when the constant was baked (no companions existed on 2026-06-25) and went
live as they accumulated. The selector now enumerates `_STANDARD_EXTRACTS`.
**Reported against interest:** the constant does **not** reproduce under *either*
selector, and the corrected one is **not uniformly closer** (CT_CHP 0.595 → 0.710,
ST_GAS 0.350 → 0.417, ST_CHP 0.362 → 0.428 max |Δ|) — **fixing the glob does not
restore it.** It is genuinely stale w.r.t. the 07-24 backfill *and* the guard, both
source-data changes, so re-derivation is rule-23 admissible — and was
**deliberately NOT done**: the arm is a census, not a re-derive-and-commit sweep,
and this is a forecast-lane input whose refresh belongs to a session that can gate
it. Its annual POF budget is conserved by construction (month-weighted mean 1), so
staleness moves maintenance *between* months, never its total.

**Filed, not fixed (rule 24 `[R-REGISTRY]`).** `maintenance_monthly_shape` is a
solve-affecting `ScenarioConfig` field **absent from the mechanism matrix**; CI
grandfathers it because `check_mechanism_matrix.py` diffs new fields against the PR
base. Its per-ISO forecast-lane verdicts have never been tested, so this session
did not invent them.

**Governance.** Zero LP; nothing solved, scored or registered, so nothing is
registered on the dashboard (the neiso-71/73/74 + xiso-1 disposition, rule 15).
Only **bytes** were compared — which rule 20 `[R-HOLDOUT]` explicitly permits on
out-of-training data — and the **holdout spend freeze remains ACTIVE and
untouched**. No keeper changed, no `ScenarioConfig` field added or changed. Matrix
row `outage_artifact_provenance` added, cells `IIIOII` (MISO `O` for its
outstanding admissible 2022 re-derivation, the other five `I` as measured-inert);
the `campd_outage_windows` note's standing "downstream artifacts unaudited" claim
is retired; §5.7 updated and §4 item 4 amended.

**DO-NOT-REDO:** do not re-census by hand — re-run the probe (census + glob
measurement in ~1 min; `--verify-extracts DIR` for the byte half). Next
cross-cutting shorthand: **xiso-3** — §5.7's remaining open items are the registry
hygiene fixes from §4.6 (dangling `--ramp-limits`, inert-default flags — now joined
by the `maintenance_monthly_shape` matrix gap above) and the forecast-lane
inheritance review of keeper-only `BF` mechanisms; the `thermal_tranches_<ISO>.csv`
provenance item remains blocked at HEAD (miso-95).

## 2026-08-02 — xiso-3: rule-20 forced-share / D-4 window census on all six current keepers — ALL SIX PASS C8 (cross-cutting audit, NO LP)

**Arm A of the xiso-3 charter** (primary/recommended): the first census of rule 20
`[R-FORCED-BUDGET]`'s **full conditional-pass logic** across every current keeper at
once, scored entirely from the committed `legitimacy_diagnostics.json` artifacts.
Zero LP by construction — the C8 gate is scorer-only. Probe
`scripts/probes/_xiso3_forced_share_d4_census.py`, transcript
`results/calibration/PROBE-xiso3-forced-share-d4-census-2026-08-02.txt`, record
`results/calibration/FINDING-xiso3-forced-share-d4-census-2026-08-02.md`.

**Method is the production scorer, not a re-implementation.** The probe loads each
keeper's committed artifacts via `calibration_verdict.load_artifacts`, runs the full
`determine_from_artifacts` verdict, and re-derives every escalation through the
rubric's own helpers (`score_forced_share`, `_binding_merchant_mechs`,
`_d4_provenance`, `_d1_shape`, `_class_load_share`). It reads the keeper ids LIVE
from `frontend/data/backcast/keepers/<ISO>.json`, so a re-run after any keeper swap
re-scores the new keeper automatically. It additionally cross-checks every committed
D-4 row against the HEAD `D4_WINDOWS` registry (window drift) and sweeps latent D-4
coverage on material classes below their caps.

**The answer: ALL SIX KEEPERS PASS C8 — zero FAILs, zero exceptions-ledger flips,
zero D-4 window drift.** Reported against interest: full compliance is the
deliverable. ERCOT / CAISO / NYISO / NEISO pass on volume alone (every material
class within its cap; closest anywhere: NYISO ST_GAS 27.5 % vs 30 % in 2024, ERCOT
ST_GAS 20.1 % vs 30 % in 2025; NEISO's over-cap shares all sit on immaterial
classes, reported never gated). **PJM and MISO pass through the
grounded-above-budget escalation** (7 class-years, clean passes surfaced as report
notes per the rule): PJM CT_PEAKER 15.2/15.4/15.8 % vs the 15 % peaker cap
(`ct_netload_drag` h15-21 + `st_netload_drag` h0-23, both 0.0 % off-window; D-1
profile_r 0.930–0.975, cv_ratio 0.697–1.044) and PJM ST_GAS-2025 40.0 % vs 30 %
(all-hours drag; r 0.897, cv 2.244) — its 2023/24 shares (52.2/48.7 %) are
immaterial-skipped at 1.4/1.6 % of load, the 2 % materiality line doing exactly the
work the 2026-07-06 owner amendment specified; MISO ST_GAS 33.1/34.4/45.5 % vs 30 %
(`reliability_floor × ST_GAS` + `st_gas_mustrun_per_plant`, both all-hours BY
DRIVER, 0.0 % off-window; r 0.954–0.974, cv 1.278–1.565), material by only
0.2–0.7 pp. MISO COAL — 27–32 % of load, the fleet the rule most exists for — is
forced 0.2–0.4 %.

**Informational yield: a five-fact LATENT D-4 coverage map** (nothing gated today —
the provenance leg is only consulted above the cap; each fact is where a FUTURE
escalation would fail C8 for a missing declaration, correctly per rules 12/17):
`reliability_floor` binds material CC_REGULAR (ERCOT 0.8–2.1 %, PJM-2025 2.9 %,
MISO ≤0.1 %, NEISO 0.4–0.8 %) and COAL (PJM 0.1–0.3 %, MISO 0.2–0.4 %) with no
class-applicable `D4_WINDOWS` entry (the registry covers CT_PEAKER / CT_CHP /
ST_GAS only); and CAISO's `ra_mustoffer_bridge` — its **sole** non-exempt binder
(CC_REGULAR 6.8–9.6 %, the closest latent class at 9.6 vs 30) — is the only
mechanism binding a material class with **no `D4_WINDOWS` entry of any kind**. The
natural declaration, if ever needed, is the all-hours-by-driver shape the other
commitment bridges carry, plus a regenerated CAISO bundle so the row exists
(rule 20's regeneration clause). **No entry was minted this session** — a rule-17
declaration needs its own per-ISO driver evidence, and a census is not the session
to mint five. Headroom is large everywhere; no keeper is one re-tune away from an
undeclared-window FAIL.

**Two artifact-vintage observations, neither a defect.** (a) The baked
`lower_bound` label over-hedges: the committed D-2 rows DO attribute the P1-native
seam bridges where armed (CAISO `ra_mustoffer_bridge` 3.3–3.4 TWh/yr, ERCOT
`gas_commitment_bridge`, NYISO `nyiso_gas_commitment_bridge`) — which the
`run_year(fleet_only=True)` recompute path cannot reconstruct (the G-06 comment in
`scripts/legitimacy_diagnostics.py`) — so the artifacts were generated from
solve-time floors and the quoted shares are solve-exact; the label is conservative
legacy-P2-era text. (b) The baked D-2 verdicts read `FAIL` for the seven escalated
rows; the HEAD scorer re-scores them into grounded passes — the rubric-v2.2
measured-share-overrides-baked-verdict design working as built, not drift.

**Context, not census news:** full determinations at HEAD are PJM CALIBRATED,
CAISO/NYISO/NEISO CALIBRATED-WITH-CAVEATS, ERCOT and MISO NOT-YET — on the
C3-family/C7 gates the matrix per-ISO headers already record (ERCOT: C3a/C3b/C3c +
C7 2023-lignite; MISO: C7 COAL_PRB, its sole failing criterion). C8 is not among
any ISO's failing criteria, and nothing moved this session.

**Governance.** Zero LP; nothing solved, scored-new, or registered (the
neiso-71/73/74 + xiso-1 + xiso-2 disposition, rule 15). Every scored year is inside
2023–2025 (probe-asserted), so the **holdout spend freeze remains ACTIVE and
untouched**. No keeper changed, no `ScenarioConfig` field added or changed, rule 25
throughout — verdicts, windows and grounded passes are strictly per-ISO. Matrix row
`forced_share_d4_census` added, cells `IIIIII`; §5.7 updated.

**DO-NOT-REDO:** do not re-census by hand — re-run the probe (~1 min, zero LP; it
re-scores the live keepers). Next cross-cutting shorthand: **xiso-4** — §5.7's
remaining open items are unchanged from xiso-2's list: the registry hygiene fixes
from §4.6 (dangling `--ramp-limits`, inert-default flags, the
`maintenance_monthly_shape` matrix gap), the forecast-lane inheritance review of
keeper-only `BF` mechanisms, and the `thermal_tranches_<ISO>.csv` provenance item
(blocked at HEAD, miso-95); Arm C's pjm-144 PREREG-without-outcome question also
remains unclaimed.

## 2026-08-02 — caiso-155: three legitimacy-harness defects fixed (plant-set drop; rebuild override-channel threading; G-06 bridge carve-out); no keeper verdict moved

The caiso-151 §F diagnostics plant-set defect is closed ISO-generically, and
the census surfaced two deeper reconstruction-fidelity defects (the
floors-rebuild's dropped generic override channels — which both LOST
channel-armed floors and HALLUCINATED replaced legacy ones — and G-06's
RA-only bridge subtraction). All three fixed in
`scripts/legitimacy_diagnostics.py` with tests; census + A-ladder +
production-rubric re-score on record. NO committed artifact regenerated:
both pre-registered regen instruments failed their gates honestly (A1b:
solve-state floors; D-13: measured degenerate-vertex non-reproduction of the
caiso153 solve — same duals, class dispatch shuffled ≤2 GW — carrying
caiso-154 §H's "reproductions are not a standing guarantee" from artifacts
to solves). Main entry `docs/calibration-log/caiso.md`; record
`results/calibration/FINDING-caiso155-diagnostics-plant-set-2026-08-02.md`;
matrix audit row `diagnostics_plant_set`.

## 2026-08-03 — caiso-159: a designated keeper's committed bundle was CORRUPT ON MAIN, and a rule-22 marker breach had been failing `audit_keepers` for a day (governance repair, NO LP)

Two governance defects found and closed while executing the caiso-158 promotion
charter. Neither was in scope; both are recorded because they are the kind that
survive by looking like nothing.

**(1) Committed merge-conflict corruption inside the designated NYISO keeper.**
A rename/rename merge between the nyiso-113 and caiso-158 branches was resolved
by committing the CONFLICTED content into BOTH paths. Eight JSON files across
`nyiso113_lilocational_B` (the KEEPER), `nyiso113_control_A` and
`nyiso_c156_meter_screen_B` carried live `<<<<<<<<`/`========`/`>>>>>>>>`
markers on main.

The markers were the visible half. The damaging half is that **git auto-merged
the NON-conflicting regions from the wrong side**, so the keeper's committed
scorecard asserted `governance: UNATTESTED` and `grade_summary` 8/7 when its own
attestation makes it PASS and 9/8. Those lines sit OUTSIDE every marker — a
marker scan would have called the file clean after stripping. Repair is
therefore a WHOLE-BLOB restore from the last-good commit (`81d61f1`), not marker
editing. `nyiso_c156_meter_screen_B` had no clean blob anywhere (its pre-rebase
commit `794e42f` is unreachable) and was reconstructed by side selection, which
is lossless because a two-sided conflict interleaves only the differing hunks.

Blast radius MEASURED, not assumed: `runs/<id>.js` embeds no scorecard and
`status/<ISO>.js` is regenerated by re-running the scorer against the bundle's
(intact) attestation, so the dashboard never displayed a wrong number and
nothing needed re-solving. Standing order: **never hand-resolve a rename/rename
conflict in bundle JSON — restore each side's blob whole.**

**(2) rule-22 D-5(b) marker breach, closed.** `scripts/audit_keepers.py` check
M1a was FAILING on main before this session touched anything: the nyiso-113
promotion (2026-08-02) moved `keepers/NYISO.json` but never re-keyed
`calibration-complete.json`, whose `complete.NYISO.keeper` still named the
superseded `2026-08-02-nyiso112-ramp-plus-peaker`. Re-verified from committed
artifacts only (no solve): nyiso-113 scores CALIBRATED-WITH-CAVEATS with 1
ledgered caveat, unchanged from the declaration-time basis, so the re-key is
safe and applied with `keeper_at_declaration` preserved. `audit_keepers` now
passes 0 failures / 0 warnings across all six ISOs plus the holdout, marker and
status checks.

**(3) A promotion premise that expired mid-flight — the transferable one.** The
caiso-158 handoff listed three promotable ISOs. Re-diffing each arm against the
CURRENT designated keeper (not the one current when the arms were chartered)
showed NYISO's keeper had moved to nyiso-113, which arms
`nyiso_li_locational_reserve`; the NYISO arm carries it FALSE. Promoting it
would have dropped a PUBLISHED Zone-K reserve requirement to gain an input
correction — a rule 14 [R-ACCURATE] regression in the name of rule 14. NYISO was
NOT promoted; CAISO and NEISO were. **An A/B is only promotable against the
keeper it was controlled on: re-diff at PROMOTION time, because a parallel
per-ISO session can promote underneath you while your arms solve.**

Evidence: `results/calibration/FINDING-caiso159-ct-heat-rate-promotion-2026-08-03.md`.

---

## 2026-08-03 — pjm-149: D-2/D-4 floor attribution was DISPATCH-PATH-dependent; fixed, and the committed corpus was found split across both paths

Cross-ISO scoring-infrastructure charter opened from the pjm-148 side finding.
**Zero LP, no keeper touched, no artifact regenerated, no determination moved at
any of the six ISOs.** Evidence:
`results/calibration/FINDING-pjm149-d2-floor-attribution-path-2026-08-03.md`;
pre-registration pushed at `01cb248` before any measurement that decided the
contract; machine record `results/calibration/_pjm149_census.json`.

**(1) The defect.** `scripts/legitimacy_diagnostics.py` built the D-2/D-4 row set
as a comprehension over the *dispatch map*, so a plant that was FLOORED but
absent from that map was dropped silently — no row, no failure, no note. The map
is the solve's `dispatch/<year>_<pass>.parquet` (gitignored ⇒ absent from every
committed bundle) or else the CAMPD-bench-keyed run payload, which carries only
metered plants. Measured at all six current keepers: **2–130 dropped floored
plants per ISO-year, 23–272 TWh/yr** of floor energy invisible to a file that
rule 18 `[R-FORCED-BUDGET]` is scored *entirely* from. caiso-155's `pseudo_pids`
had re-admitted only the `plant_code <= 0` family; the general rule now **subsumes**
it (rule 19 `[R-ONE-MECH]`, not a second parallel mechanism).

**(2) The finding nobody could see: the committed corpus is SPLIT across both
paths.** `legitimacy_diagnostics.json` is written *during* the producing run,
while `dispatch/` still exists, but re-scored later from the committed slim file
set. Which path an artifact was born on is recorded nowhere. Fingerprinted on the
`''` bucket: **CAISO / MISO / NEISO / NYISO are parquet-born** (complete);
**ERCOT / PJM are payload-born** (missing the nuclear block). Two keepers' and
four keepers' artifacts were never comparable documents. **Standing consequence:
a scorer whose output depends on which gitignored artifact happens to be on disk
must say so in the artifact — path provenance is now recorded in the D-2/D-4
notes.**

**(3) Why nothing was regenerated — the transferable call.** The obvious cleanup
(re-scoring every keeper under the fix) is exactly wrong here: four of six
committed artifacts are parquet-born, so regenerating them on the only path now
available would **replace measured dispatch with a bound** — a rule 14
`[R-ACCURATE]` regression performed in the name of tidiness. The per-ISO delta was
measured and *reported* instead (FINDING §7). **A scorer fix does not entitle you
to re-run the scorer over artifacts that were produced with better inputs than
you now have.**

**(4) The contract, justified rather than inherited.** A floored plant the
dispatch map does not cover enters with `disp := its own floor`. This extends
caiso-155's floor-energy convention, but on a stronger footing: forced energy
sums dispatch over at-floor hours only ⇒ floor energy is an **upper bound on the
numerator**; LP feasibility (`P ≥ min_gen`) ⇒ it **understates the denominator**.
So the reported `forced_share` is an **UPPER BOUND**, and since rule 18 fails
HIGH the bound is *sound on a pass* and *indeterminate on a fail*. A breach is
deliberately **not** suppressed — silently weakening rule 18 would be worse than
an over-strict flag — it is stamped `upper_bound: true`, annotated in
`calibration_verdict.score_forced_share`, and escalates. Validated against ground
truth: on the parquet-born `pjm144_control_A` the convention reproduces the true
nuclear row **exactly** (272.0222 / 270.5943 / 269.3312, delta +0.0000 in all
three years).

**(5) A side finding's example was wrong, and checking it was the charter's
job.** pjm-148 §4 attributed PJM's missing `CC_CHP chp_steam` row to those 14
plants being absent from the payload. **All 14 are PRESENT** in the payloads of
pjm-144, pjm-146 and pjm-147 alike; PJM's dropped population is 17 plants, every
one nuclear. The real cause is a **distinct second defect** — the payload-decoded
and parquet dispatch series disagree about whether a *covered* plant is at its
floor (6–7 CC_CHP plants carry a 3.7–4.0 TWh `chp_steam` floor and clear it by
8.9–239 MW in all 8,760 hours, far outside quantization). Settling it needs both
series for one bundle, i.e. a solve; filed as the named successor, not chased.
**A defect report's mechanism claim is a hypothesis; the charter that inherits it
verifies the example before building on it.**

**(6) A third path asymmetry, recorded not fixed.** The D-2 materiality guard
reads `total_load_mwh` from the payload sidecar, so an in-run parquet-path
generation has `load_share = None` and gates *every* class. At
`pjm144_control_A` that alone flips ST_GAS 2023–25 between FAIL and
pass-immaterial while the shares agree to ~1 pp. Not a keeper; pre-dates this
session's change.

Gates: A2 confined-delta PASS (additions only; D-1 byte-identical at all six);
**A3 determination invariance PASS at all six ISOs** through the production
rubric — zero criterion-record status differences, identical `grade_summary`;
A4 parquet-path no-op tested rather than asserted, with its two structural
exceptions recorded; A5 eight new tests including a regression guard that
reproduces the *old* comprehension and asserts it loses the plant; A6
`tests/scoring/` 900 passed with 4 pre-existing `test_ff_readiness_battery.py`
failures verified pre-existing by re-running with the changes stashed.

---

## nyiso-121 (2026-08-04) — MISO's rule-28(c) matrix column CLOSED; the six-lane census backlog is discharged

**Cross-ISO audit action, logged here rather than in `miso.md`** because it was performed
from the NYISO lane on MISO's column and touches no MISO mechanism, keeper or determination
— and because a MISO calibration session may be active (the keeper is same-day).
**Zero solves. Zero years touched. No `ScenarioConfig` value, constant or derive script
changed. Both ISOs' keepers unchanged.**

**What closed.** MISO was the **last** ISO with an open own-family column. All **8 absent +
4 prose-only** `miso_*` fields — **7 ARMED on keeper `2026-08-04-miso-122b-scope-gate` with
no cell anywhere**, the 227-3 shape — are registered as **literal sub-scalar entries on 7
existing family rows**. **169 → 169 rows (zero new).** One cell mint: `matrix_gap_census`
MISO `O` → `K`, an **audit status**, per the ercot-156 / caiso-161 / pjm-151 precedent.
**Zero mechanism verdicts** — every verdict-bearing sentence transcribes an adjudication
already on the record with its citation. Ratchet baseline MISO **8 → 0**.

With ERCOT, CAISO, NEISO, PJM and NYISO already closed, **the six-lane backlog nyiso-113/114
measured (161 absent, 95 armed-but-cell-less) is fully discharged.**

**A new invisibility variant, recorded for every lane.** Beyond the caiso-161 §2
abbreviation/stale-anchor defect (which recurred here as `miso_pjm_lmp :2914`, not a
`ScenarioConfig` field, anchored on an unrelated comment block), `miso_manitoba_seam` —
ARMED on the keeper — was prose-only inside **`diagnostics_plant_set`**, a row about probe
plant sets. **A mention on the wrong family row is as invisible as no mention, and unlike a
glob or a stale anchor it reads as correct coverage to a human auditor.**

**A governance correction that binds the next lane (FINDING §6.2).** The pre-registered
criterion "the other five ISOs' counts must not move" **fired on this session's own first
draft**: enumerating MISO's 17 shared-stem literals — as ercot-156, caiso-161 and pjm-151
each did — took **ERCOT from 12 to 11**, because a field armed on both keepers was newly
counted "mentioned". **One lane's prose silently dropped a field from BOTH lanes' lists with
no ERCOT session registering anything.** Naming a shared field as a bare literal makes the
sweep count it mentioned — the very "a mention is not a registration" defect the census
exists to close — and it **leaks across columns**. The enumeration was withdrawn for a count
plus a pointer to the committed `_matrix_gap_sweep_<ISO>.json`.

> **Standing consequence: the enumerated shared-field lists left in `matrix_gap_census` by
> the earlier column closures are PROSE, NOT REGISTRATIONS. Trust
> `results/calibration/_matrix_gap_sweep_<ISO>.json` over the row's text.**

**Two armed-but-dead observations, filed and NOT adjudicated (rule 28(d)).** Measured on
**construction** — no LP, no solve, no dual (the nyiso-115 G2 / nyiso-118 lesson):
`miso_pjm_border_anchor` is **provably unobservable** on the MISO keeper, displaced by
`miso_seam_measured_ladder`; all 48 seam rows exactly equal (`np.array_equal`, float32) in
all three years, with a positive control that separates. Likewise `miso_firm_imports` is
dropped by `miso_manitoba_seam`. **Neither is a rule 26 `[R-DELETE]` candidate** (both are
built, reachable, default-off mechanisms at their documented defaults, displaced by
documented alternatives). Whether arming both halves of an either/or pair is cosmetic or a
rule 19 `[R-ONE-MECH]` question **belongs to a lane that may adjudicate MISO.**

**A pre-registered prediction recorded as WRONG rather than redefined (FINDING §6.1):** the
prereg predicted the cells string `KKKOKO` → `KKKKKK`, assuming NEISO's audit cell was
already `K`. It is not; minting it is NEISO's lane's call. Only index 3 moved.

**Named successor:** the **cross-ISO shared-stem backlog** (PJM 18, MISO 17, ERCOT 14,
CAISO 5, overlapping, all armed on keepers with no cell) is the only remaining rule-28(c)
debt. That lane must **register these fields on rows, not enumerate them in prose.**

Evidence: `results/calibration/PREREG-nyiso121-miso-matrix-column-2026-08-04.md` (pushed
before any row was written) · `FINDING-nyiso121-miso-matrix-column-2026-08-04.md` ·
`scripts/probes/_nyiso121_miso_border_anchor_displacement_probe.py` →
`nyiso121_miso_border_anchor_displacement_probe.json` · sweeps `_matrix_gap_sweep_*.json`.

## 2026-08-04 — xiso-3: the CROSS-ISO SHARED-STEM backlog CLOSED — both halves of the rule-28(c) census now read zero, and line-anchor decay is now GATED (cross-cutting audit, NO LP)

**Cross-ISO audit, logged here rather than in any ISO's file** because it touches every
ISO's column and no ISO's mechanism, keeper or determination. **Zero solves. Zero years
touched. No `ScenarioConfig` value, constant or derive script changed. All six keepers
unchanged. NO CELL MINTED ANYWHERE** — stricter than the five column closures that preceded
it, each of which minted its own audit status.

**What closed.** The cross-ISO shared-stem backlog was the LAST rule-28(c) debt and the
successor nyiso-121 named. All **45 distinct SHARED (non-ISO-prefixed) fields** — **54
(ISO, field) pairs**, nine armed in two ISOs at once — that a designated keeper **ARMS with
no matrix cell anywhere** are registered as **literal sub-scalar entries on 19 EXISTING
rows' defs**, each home chosen on a **cited code read site** rather than on theme.
**169 → 169 rows (zero new).** Ratchet `shared_armed_on_keeper` CAISO 5 / ERCOT 14 /
MISO 17 / PJM 18 → **0 0 0 0**. With every own-family column already closed, **both halves
of the census now read zero and both are ratcheted.**

**Mechanical cause — the caiso-161 §2 abbreviation defect, three more times, and it is now
the single most common cause of matrix invisibility on the record.** Seven registrations
already existed but only as ABBREVIATIONS no literal-matching checker could resolve: a bare
**`etc.`** standing in for THREE armed fields at once, plus `(+seasonal)`, `p25 level`,
`class_aware`, `_from_data`, `conditional runs` (the field name written with a space), and
`outage_source=historic :7709`, whose anchored token is not a field at all.

**LINE-ANCHOR DECAY IS NOW MEASURED, REPAIRED AND GATED (the nyiso-121 suggestion, built).**
nyiso-121 found all 20 MISO anchors stale and deliberately filed a checker as tooling work.
Measured file-wide here the decay is **near-total: 163 of 167 checkable anchors did not
resolve, only 4 did** (120 of 152 field-style, 43 of 43 row-id style), most off by
900–1,400 lines because `scenarios.py` grew under them. **161 repaired mechanically**,
verified **digits-only** (with every `:\d+` normalised, before and after are byte-identical).
`scripts/check_mechanism_matrix.py` now carries a standing anchor leg — field-style, row-id
and file-in-range checks, a **shrink-only ratchet** (`mechanism-matrix-anchors.json`, now
**EMPTY**) and a **`--fix-anchors`** path so compliance is one command rather than a tax on
every `scenarios.py` PR. **Existence is gated FIRST**, which preserves the deliberate
`miso_pjm_lmp :2914` defect QUOTATION — do not "fix" it. The check is also what verified
this session's own 54 registrations (field anchors 124 → 178, all resolving).

> **Standing consequence: the ratchet proves an anchor points at the field it NAMES; it
> cannot tell a correct literal from a wrong one. The literal field name remains the
> durable identifier — only a human can tell whether it is the right field to name.**

**Seven armed-but-dead pairs in TWO ISOs, filed and NOT adjudicated (rule 28(d)).** Measured
on **CONSTRUCTION** — no LP, no solve, no dual (the nyiso-115 G2 / nyiso-118 lesson), built
twice at one HEAD with `np.array_equal` on float32, exact equality and not a tolerance.
Four ERCOT coal passthrough scalars (`coal_prb_passthrough_floor` 0.76,
`coal_prb_follower_floor` 0.76, `coal_lignite_passthrough_floor` 0.675,
`coal_lignite_passthrough_ceil` 1.0) sit behind rank sigmoid gates the ercot158 keeper sets
False; three CAISO CT drag coefficients sit behind `ct_netload_drag=False`. All five arms
Δ = **0.0 exactly**, and **all five positive controls separate** (0.58–0.74 on the
passthrough multiplier, 80.1 MW on `min_gen`), so the silence is the mechanism's and not the
instrument's. Those two `run_config.json` files **overstate what the solve read** — the
caiso-161 §5 / pjm-151 / nyiso-121 G-1 shape in a third and fourth ISO. **The CAISO result
is CONSISTENT with that family's existing CAISO `R`**, not in tension with it. Whether an
inert fitted scalar is cosmetic, a rule-19 `[R-ONE-MECH]` question or a rule-26 `[R-DELETE]`
candidate belongs to a lane that may adjudicate that ISO.

**THE MANDATORY POSITIVE CONTROL CAUGHT TWO DEFECTS IN THE SESSION'S OWN INSTRUMENT, which
is the argument for it being mandatory rather than advisory.** (a) A pooled control over all
four ERCOT fields separated — but only on the prb and lignite floors; it **never exercised
`coal_prb_follower_floor`'s read path at all**, so that field's silence would have been an
artifact. (b) The per-field rewrite then reported one control **VOID**, because the probe's
emulation of `assembly.py`'s tiered branch **overwrote** the baseload prb entry while the
real code keeps BOTH maps and routes only low-must-run plants to the follower — the
instrument was blind to the very field it was testing. Neither was found by inspection.

**A pre-registered criterion FIRED and is recorded rather than redefined (FINDING §6).**
Criterion 6 — the nyiso-121 §6.2 guard restated for the lane it was filed for — flagged
`coal_lignite_passthrough_sigmoid` leaving ERCOT's live-but-invisible list without being one
of the 45. **Measured**: an audit of **all 24** fields newly mentioned by this session finds
**every one is an `own_row` `def:` registration, with ZERO prose-only mentions introduced**.
The departure is one of seven COMPANION gates/thresholds the registrations name in a def,
because naming a scalar while hiding its own gate would be the very defect above. **The
criterion's guard HOLDS; its wording was too narrow.** Corrected form, stated rather than
applied silently: every departure must be a `def:` registration on the row whose code owns
it, pre-declared or not, and any non-pre-declared departure must be itemized.

**ONE declared cell mismatch left unresolved on purpose:** `coal_nameplate_summer_derate` is
ARMED on the ERCOT keeper while its only code-level home row (`cc_nameplate_summer_derate`)
reads ERCOT **`U`** — correctly, since that row's own CC flag is False there. Resolving it
would be minting a verdict, so it is stated in the registration and **filed for the ERCOT
lane**.

**What the next lane inherits.** Not a backlog — three filed, un-adjudicated items, each
belonging to a lane that may adjudicate its own ISO: **ERCOT** (four unreadable scalars plus
the cell mismatch), **CAISO** (three unreadable coefficients), and **NEISO**, whose
`matrix_gap_census` audit cell is still `O` while its own-family sweep reads 20/0/0/0 —
that mint is NEISO's lane's call, not this one's.

Evidence: `results/calibration/PREREG-xiso3-shared-stem-backlog-2026-08-04.md` (pushed
before any row was written, any anchor repaired or the probe run) ·
`FINDING-xiso3-shared-stem-backlog-2026-08-04.md` ·
`scripts/probes/_xiso3_shared_stem_gate_probe.py` → `xiso3_shared_stem_gate_probe.json` ·
sweeps `_matrix_gap_sweep_*.json` · ratchets `mechanism-matrix-gaps.json` (shared block now
empty) + `mechanism-matrix-anchors.json` (empty).

## xiso-4 — the shared-stem lane arrived after xiso-3 had closed it: independent VERIFICATION, plus one live-but-mislabelled cell (2026-08-04)

**No matrix byte written. No cell minted. No registration made. No LP, no solve, no keeper,
default or band moved.** This lane opened against `d7363b0e` on the same charter xiso-3 was
already executing; main moved to `fe90fb8f` mid-session and the collision surfaced on the
first push, **before any edit**. The correct response to finding your lane already closed is
to verify it and stop.

**Verified independently at `fe90fb8f`:** shared-gap **0 in all six ISOs**, both ratchet
blocks 0, `check_mechanism_matrix.py` PASS (integrity OK, **0 unresolvable anchors**, keeper
stamps match every shard), and all 46 fields `own_row` with **exactly one `def:` home each**.

**The cross-check, and why the earlier commit's timestamp is what makes it worth anything.**
This session derived its own home-row map from the code before seeing xiso-3's (committed as
`PREREG-xiso4-…` prior to the collision). The two maps **agree on 43 of 46**. The three that
differ — `oil_primary_bin_fuel`, `gas_hh_monthly_shape`, `cc_outage_derate_from_top` — are
defensible either way, and in two of them **xiso-3's tie-breaker is the better rule**: match
the home row's cell to the ISO's actual arming, which avoids the leg mismatch xiso-3 then had
to declare for `coal_nameplate_summer_derate`. Two counts in the xiso-4 prereg were wrong and
xiso-3's are right (nine double-armed fields, not seven; `coal_lignite_passthrough_sigmoid`
already in the 45) — corrected in place rather than edited away. Pre-registered criterion 4a
— the six post-closure live-but-invisible counts **and the six surviving fields by name**,
predicted before the closure was known — measured **EXACT**.

**THE NEW ITEM, on a row no census can see.** `gas_st_startup_spread` has its **own row**, so
`coverage()` returns `own_row` and both halves of the rule-28(c) sweep are blind to it by
construction — the ratchet reads zero and is correct to. Proven on CONSTRUCTION (no LP, no
solve, no dual): `backcast_config.py:1692` arms it for **every** ISO unconditionally;
`solve.py:259` is its only plumbing; `commitment.py:321` is its only read and sits **nine
lines after** `:312-313`'s `if gen.fuel_type == "gas_st" and not gas_st_startup_cost:
continue`; and `eia860.py:1897` maps `ST_GAS → gas_st`, so that skip is **total for exactly
the class the flag selects**. ⇒ with `gas_st_startup_cost` off the flag cannot move one LP
coefficient. At the six keepers it is **UNREACHABLE in CAISO, PJM, NYISO and NEISO** — and
**NYISO's `K` is the row's only non-`U` cell** (armed-looking but dead, the caiso-161 §5 /
pjm-151 / nyiso-121 G-1 / xiso-3 §4 shape, reaching a matrix *cell* for the first time rather
than an unregistered scalar) — while **ERCOT's and MISO's `U` are the mirror error**, sitting
on a mechanism both keepers actually run. **NOT ADJUDICATED, no cell moved (rule 28(d)):**
three lanes' calls. The confirming A/B is xiso-3's own instrument, cheap and LP-free.

**Also filed, reported not fixed:** `scenarios.py:850` describes `carry_operating_mothballs`
as "INERT since 2026-07-17" — an annotation belonging to `historic_outage_overlay` (`:1928`),
whose comment block (`:1913-1927`) sits between them. The field is live on the MISO keeper
with its own `measured-physical` DOF entry, and miso-88 measured its effect. A live measured
overlay labelled inert is a rule-13 `[R-MEASURED]` provenance hazard, not a census's
unilateral core-file edit.

**The sharpened standing risk.** Both ratchets now read zero, and a mechanism can still be
mislabelled in the matrix without either moving. The remaining exposure is no longer
*unregistered* mechanisms — it is **registered ones whose cell asserts something the code
contradicts**, and nothing in CI looks for that. xiso-3's gate-reachability probe, run across
every keeper-armed flag that has a gate, would be the third ratchet.

Evidence: `results/calibration/PREREG-xiso4-cross-iso-shared-stem-2026-08-04.md` (committed
before any matrix byte and before the collision was known; carries the independently-derived
map) · `FINDING-xiso4-cross-iso-shared-stem-2026-08-04.md`.

**AMENDMENT (2026-08-04, same day, after the first merge) — the anchor gate needed a blame
split, and the need was demonstrated by main itself.** The check shipped with a hard
`--base` failure and an empty ratchet; within the day main merged lanes that inserted
fields into `scenarios.py` and **214 anchors re-staled**, all below the insertion points,
with nothing in the matrix touched. The next lane's PR would have FAILED on drift it did not
cause. The ratchet cannot fix this by construction — a freshly repaired file has an empty
baseline, so the next insertion produces hundreds of un-baselined findings at once. Under
`--base` the check now splits by BLAME, the same rule `keeper_drift` already uses: an anchor
stale at HEAD but not at the base **fails** that PR; an anchor stale at **both** only
**warns** and belongs to whoever last moved `scenarios.py`. Verified three ways — clean tree
exits 0, a PR breaking one anchor exits 1, and a tree carrying the base's own 221 stale
anchors exits 0 with 221 `pre-existing` warnings. **General lesson: a gate keyed on absolute
line numbers in a file every lane edits cannot hard-fail on INHERITED state — a gate that
gets disabled protects nothing.** (FINDING §10.)

## 2026-08-06 — Rubric v3.1 (owner amendment): C3c is the only ledgerable caveat; C7 retired; CAISO reverted to NOT-YET and its complete + frontier labels stripped

**Owner directive (verbatim).** *"Any ISOs backcast calibrated with caveats on
LMP exceeding 10% from actual should be reverted to not yet, frontier and
complete labels stripped. 3c3 is only acceptable ledgered caveat, and to be
frank I don't even know why c7 matters and I think we should drop it from the
calibration report and declaration altogether if no other commercial grade
model is gating or publishing on that."*

**Scorer-only. No LP was solved, no bundle regenerated, no keeper changed, no
mechanism tested, no holdout year touched.** Every number below comes from
re-scoring committed artifacts with `scripts/calibration_verdict.py --run-id`.

### (a) Ledgering restricted to C3c alone

`calibration_verdict.LEDGERABLE_CRITERIA = {"price_tail"}`, enforced
fail-closed in `_apply_ledger`: an exceptions-ledger entry naming any other
criterion is ignored and the `FAIL` stands, whatever its `kind` or reason.
Existing entries are **not deleted** — they stay on their bundles' attestations
as the historical record of what was accepted and why — they simply stop
reclassifying, so keepers re-score in place.

Rationale, on this rubric's own §8 evidence: C3c is the one criterion with **no
published commercial comparable at all** (nothing commercial or public
publishes tail-hour-count accuracy), so a documented, exhaustion-cited bound is
its honest reporting form. Every other criterion is scored against a published
comparable, and for those the band **is** the certification claim. C3a mean LMP
is the case that forced it: ledgering a mean-LMP miss beyond ±10% certified a
price level the model does not reproduce.

Both caveat budgets collapse as an arithmetic consequence (caveats aggregate
per criterion): protective **1 → 0** — no protective criterion is ledgerable,
so a C8 forced-share `FAIL` is `NOT-YET` full stop, which *hardens* rule 20
enforcement rather than relaxing it — and non-protective **3 → 1**. Both checks
are kept as defense-in-depth invariants against a silent re-widening.

### (b) C7 diurnal shape retired outright

Dropped from the calibration report **and** the determination. The owner's
condition — *if no other commercial grade model is gating or publishing on
that* — is met on evidence this rubric already carried before the amendment:
§8's comparables row scores the protective gates *"beyond commercial
practice"* and states that C7/C8 gate *"the diurnal shape and forced-energy
share **no external model reports**"*. Every graded criterion here is two-band
scored against a published comparable; C7's `r ≥ 0.8` / CV-ratio `≥ 0.5` were
self-set numbers gating a determination against nothing external.

A **full removal**, harder than the C5a/C5b/C5c retirements that left those
criteria `REPORTED_ONLY`: `score_shape` and `C7_GATED_CLASSES` are **deleted**
per rule 26 `[R-DELETE]`, so the gate cannot be silently re-armed.

**The D-1 measurement is NOT retired, deliberately.**
`legitimacy_diagnostics.py` still computes the diurnal rows and writes them to
every bundle, and **C8 still gates on them** through `_d1_shape` — rule 20
`[R-FORCED-BUDGET]` makes an over-budget class's conditional pass depend on its
D-1 profile clearing `profile_r`/`cv_ratio`. The caiso-42 flat-floor signature
(model off-peak CV 0.000 vs a real 0.35–0.45) used to be caught twice; it is
still caught by C8's escalation, which is the better-aimed of the two because
it reads the D-1 row for **whichever class is actually being forced** instead
of a hard-coded class tuple. Pinned by
`DeterminationTests.test_flat_floor_forces_not_yet`.

### Effects — all six keepers re-scored from committed artifacts

| ISO | keeper | before | after | why |
|---|---|---|---|---|
| **CAISO** | `2026-08-06-caiso-175-tac-intake` | CALIBRATED-WITH-CAVEATS | **NOT-YET** | C3a 2024 +11.7% (model $38.63 vs actual $34.60), 2025 +14.8% ($39.46 vs $34.39) — ledgered since caiso-145, now `FAIL`. 2023 +4.2% passes. |
| **MISO** | `2026-08-05-miso-132b-cc-committed` | NOT-YET | NOT-YET | C3a 2025 −14.0% moves `CAVEAT → FAIL` and becomes the sole blocker; the previous blocker (C7 COAL_PRB 2025, cv_ratio 0.338) is retired, not fixed. |
| NEISO | `2026-08-05-neiso-83-ca1-reclass` | CALIBRATED-WITH-CAVEATS | unchanged | C3a `PASS` all years; C3c its only caveat. Dormant C1/C2/governance entries were reclassifying nothing. |
| PJM | `2026-08-04-pjm-152-collapse` | CALIBRATED | unchanged | Zero caveats, zero fails. |
| NYISO | `2026-08-06-nyiso-128-control` | CALIBRATED-WITH-CAVEATS | unchanged | C3a PASSES all three years (+6.2 / −1.7 / −7.0 %); C3c its only ledgered caveat. *(Scored on the keeper NYISO promoted 2026-08-06, after this amendment was written against `2026-08-04-nyiso-125-seam-envelope`. That run was NOT-YET on a C3a 2025 −10.2 % `FAIL` that was never ledgered, so it was unaffected by the amendment either way — the promotion, not v3.1, is what moved NYISO.)* |
| ERCOT | `2026-08-05-run168b-year-curves` | NOT-YET | unchanged | C3a 2023 −32.2%, C3b already failing. |

C7 was `PASS` on CAISO/NYISO/PJM/ERCOT, `SKIPPED` on NEISO and `FAIL` on MISO,
so its retirement changes only MISO's reported basis — and MISO's label is
unaffected because C3a fails it independently.

### Governance consequence — CAISO `complete` + frontier withdrawn

A `complete` marker cannot rest on a `NOT-YET` keeper, so the CAISO entry moved
from `complete` to `withdrawn` in
`frontend/data/backcast/calibration-complete.json` (declared 2026-08-05,
withdrawn 2026-08-06 — a one-day marker). Rule 22's D-5(b) re-verification
branch is satisfied *against interest*: the re-verified determination is
**worse** than the one the marker was declared on, which is exactly the
stop-and-escalate case; here the owner is the escalation's author and the
disposition is withdrawal.

**Nothing was spent, so nothing is lost.** The validation tier (2022) was
authorized but never spent — the holdout spend freeze was active for the
marker's entire life. The touch-once locked test (2019, H1-2026) was **never
authorized** (CAISO never appeared in `final`) and stays fully available to a
re-calibrated keeper. With the marker gone the tier-aware gates
(`scripts/lib/holdout_policy.py`) re-block every CAISO out-of-training
solve/score/registration — verified: `authorized(CAISO, validation)` is now
`False`.

**The frontier evidence is not retracted; the frontier *claim* is.** The walled
hourly PS water state (FINDING-caiso141), the export/absorption family rejected
on sign (caiso-142 §H), the closed offer rungs (caiso-131 §10) and the inert
reserve co-optimization (caiso-144 §B/§C) all stand as adjudicated and remain
DO-NOT-REDO under rule 27. What is withdrawn is the claim that an empty in-model
lever queue on C3a is a terminal state. On a criterion that cannot be ledgered,
an empty queue is an **open root-cause item** (rule 1 `[R-STRUCT]`, rule 20
`[R-DOF]`), not a documentable bound. The open lane is the +793 MW belly wedge
FINDING-caiso140 §B measures from the LP dispatching a 2,078 MW pumped-storage
fleet on economics alone; the identifying data is non-public and an owner-level
acquisition. Nothing here licenses closing C3a with an adder, haircut or any
value tuned to the level residual (rules 1/13).

### Files touched

`scripts/calibration_verdict.py` (v3.1: `LEDGERABLE_CRITERIA`, budgets,
`score_shape`/`C7_GATED_CLASSES` deleted) · `scripts/build_status.py`,
`scripts/score_crossover.py`, `scripts/legitimacy_diagnostics.py` (C7 references)
· `tests/scoring/test_calibration_verdict.py` (ledger + C7 coverage re-based;
the flat-floor regression now pins the C8 path) · `CLAUDE.md` rule 20 ·
`docs/calibration-determination-rubric.md` (banner, §1, §2, §3, C7 section, §8,
§9) · `docs/codebase-site/calibration-rubric.html` ·
`docs/codebase-site/data/mechanism-matrix.js` (gates board + header stamp) ·
`frontend/data/backcast/calibration-complete.json`,
`frontend/data/backcast/keepers/CAISO.json`,
`frontend/data/backcast/status/*.js`.

`scripts/audit_keepers.py` PASSes 0 failures / 0 warnings after the change.

**Known-stale, flagged not repaired** (pre-existing, belongs to those lanes):
the mechanism matrix's NYISO gate cell still describes the nyiso-109 basis and
calls the determination CALIBRATED-WITH-CAVEATS though nyiso-125 scores
NOT-YET; and its NEISO cell still calls NEISO the "only calibration-complete
ISO", untrue since NYISO and PJM were declared on 2026-07-31.

## 2026-08-09 — Rubric v3.2: the C3c standing rule fires in EVERY year (+ a defect that was suppressing it)

**Session:** neiso-keeper-87-control · **Owner amendment**, verbatim: *"make sure c3c is an
acceptable caveat for any holdout or training year"*. Cross-ISO, scorer-only: **no solve, no
bundle regeneration, no keeper change, no mechanism tested, no matrix cell moved.** Every run
re-scores in place from its committed artifacts.

**(a) The widening.** `calibration_verdict._apply_c3c_standing_rule` was declared 2026-08-06 for
**out-of-training years only**; it now fires on 2023–2025 as well. A **lone** C3c failure with the
governance gate passing reclassifies to a ledgered CAVEAT (`ACCEPTED MODEL-CLASS LIMITATION`) and
the run reads CALIBRATED-WITH-CAVEATS instead of NOT-YET.

This resolves an ambiguity in the original directive, which itself said *"holdout years **and
testing years**"* while the implementation read it as validation + locked tiers. **It is not a
loosening of the band.** Band, tier and reported magnitude are identical in every year; in-sample
the same reclassification was already reachable through an explicit exceptions-ledger entry — and
that is the route **every current keeper carrying a C3c caveat actually used**. The split governed
who typed the justification, not what a run could claim, and since v3.1 C3c is the only ledgerable
criterion at all. The guards are untouched: **lone failure only** (any second failing criterion and
the rule is silent and every failure stands, C3c's included — so it can only fire on an
otherwise-clean model), **governance must PASS**, **supporting-tier-only fail-closed**, **never
CALIBRATED**, and the caveat still spends the single ledgerable slot.

**(b) A defect found while verifying (a), which was suppressing the rule as originally declared.**
"Lone" was measured over **every** scored record — including the REPORTED-ONLY streams the rubric
has demoted out of the determination, i.e. C5a `co2`, removed at v2.9 because eGRID's latest
released vintage is 2024. An unrelated `co2` FAIL therefore silenced the rule even though co2
contributes no status, no caveat budget and no reason line. Caught by measurement, not inspection:
the first blast-radius pass returned **0 changed runs**, which was wrong for
`2026-08-06-nyiso-130-control` — a run whose own determination basis reads *"undocumented
out-of-tolerance (FAIL) criteria: price_tail"* and nothing else. Instrumenting the predicate showed
it seeing `[('co2', 2025), ('price_tail', 2023), ('price_tail', 2024)]`. "Lone" is now measured over
`CRITERIA` membership. **This under-fired out-of-training years too, so (b) is a correction, not
part of (a).**

**Effect, measured over all 66 registered runs against a pre-change snapshot rather than asserted:**

| | |
|---|---|
| determinations changed | **2**, both NYISO **non-keeper** probes |
| which | `2026-08-06-nyiso-130-control`, `2026-08-06-nyiso-130-n11-tsl` — NOT-YET → CALIBRATED-WITH-CAVEATS (C3c FAIL → CAVEAT; nothing else moves) |
| unlocked by | **(b)**, the defect fix — not by the widening |
| keepers changed | **none**, all six ISOs (ERCOT NOT-YET, CAISO NOT-YET, MISO NOT-YET, PJM CALIBRATED, NYISO CALIBRATED-WITH-CAVEATS, NEISO CALIBRATED-WITH-CAVEATS) |

Every keeper is unchanged because each either has no C3c failure, already carries an explicit
ledger entry for it, or fails a second criterion so the lone-failure guard keeps the rule silent.
**`2026-08-06-pjm-158-novirtual-disarmed` is a lone C3c failure and still does NOT reclassify** —
its C6 is UNATTESTED, which is guard (b) doing its job.

`RUBRIC_VERSION` 3.1 → **3.2**. Committed per-bundle `metrics.json` files are deliberately NOT
bulk-regenerated: they are already spread across versions 2.5–3.1 by convention, being the snapshot
taken when each run was registered. The live verdict is always `calibration_verdict.py --run-id`,
and `build_status.py` regenerates the dashboard's per-ISO status shards from that same scorer (done
this session, all six). `audit_keepers` 0 failures / 0 warnings. Eight new tests pin the rule:
`tests/scoring/test_calibration_verdict.py::C3cStandingRuleTest`, including one that pins the
reported-only-`co2` case directly.

## 2026-08-12 — ercot-190 addendum CLOSED: the C3c scarcity-tail limitation now carries into the forecast namespace (doc-only, NO solve)

**Session:** FC-DISCLAIMER-1 · **Authority:**
`docs/DECISION-CARD-ercot189-c3a2023-after-the-offer-family-2026-08-11.md` RESOLUTIONS
addendum, signed with card Q on 2026-08-12: *"the §5 `readiness_limits` price-tail
disclaimer follow-up is **AUTHORIZED** as a named, doc-only open item for the forecast
lane … It is not implemented by this signature."* This session implements it, and the
item is now **CLOSED**. Doc-only, forecast namespace: **no solve, no scorer change, no
FC gate/verdict text, no rubric edit, no backcast file, no keeper movement, no matrix
cell.**

**What the addendum was for.** Card Q §5 fact 4 recorded that the C3c limitation is
**propagated NOWHERE in the forecast namespace** — no forecast gate, caveat or disclaimer
carried it, and `readiness_limits` (then five entries, none price-tail) was named as its
natural home under *every* option the card put. So a consumer reading the §2.1b board
could not learn that the model under-forms the RT scarcity tail, though the backcast side
has ledgered it as an accepted model-class limitation since rubric v3.1/v3.2.

**Landed.** A sixth `readiness_limits` entry — *"Scarcity-tail price formation"* — in the
committed board seed `frontend/data/forecast/program-status.json`, rendered by
`docs/codebase-site/forecast-status.html` under "Readiness limits (documented, not bugs)":
an LP on competitive/measured-cost offers under-forms the RT scarcity tail (accepted
model-class limitation, C3c ledgered); measured on ERCOT 2023, a scarcity-concentration
year carries up to **−$14/MWh (−22% of level)** annual load-weighted price bias,
concentrated in **~2% of hours**; non-concentration years score within band. A one-line
cross-reference was added at forecast plan §0 item 4 — the "what remains unfit is
**named**" clause, which is that plan's disclaimers home (it has no other limits section).

**Every figure is read off the committed evidence, not re-derived** —
`results/calibration/ercot189_c3a_c3c_overlap.json`: `decomposition.sets.h_tail_181`
contributes **$14.273/MWh** of the 2023 gap over **181 hours** (181/8760 = 2.07% of hours;
14.273 / 64.32 = 22.2% of the bench actual `rt_lw` of $64.32), and
`baseline_gate.guards_2024_2025` reads 2024 **+1.2% PASS** / 2025 **−8.0% PASS** — the
"non-concentration years score within band" half of the sentence.

**Scope note.** The generated namespace files (`program-status.js`, `manifest.js`,
`registry/`, `runs/`) are gitignored and rebuilt by the Pages deploy from this seed
(forecast plan §8), so the disclaimer reaches the live board on the next deploy with
nothing further committed. The seed's `generated` / `sources` / `refresh` provenance block
is deliberately untouched: this session measured nothing and refreshed no board reading,
so the FFR-3A-3 provenance stamp still describes exactly what produced the board.

**Governance.** Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registers — this is a
board-seed edit, not a registration. Rule 22 `[R-HOLDOUT]`: no year solved, scored or
registered. Rule 25 `[R-ISO-SCOPE]`: the limitation is stated as a model-class property
and its magnitude explicitly labelled ERCOT-2023-measured; no other ISO's evidence is
claimed or imported. Rule 27 `[R-PUSH]`: the seed is edited in place (+4 lines); no source
file ≥300 lines rewritten from regenerated content. Rule 28 `[R-MECH-MATRIX]`: no
mechanism tested and no cell minted — a doc-grade governance follow-up (precedent: the
ercot-182 / ercot-189 sittings, which touched only their card and the log).

## 2026-08-12 — F1 EXECUTED: the data-provisioned test tier is SCHEDULED (card F; the golden's fifteen-day silence closed)

**Session:** f1-golden-tier, branch `claude/f1-golden-tier-schedule-5c7nyf`. Cross-ISO CI
infrastructure — **no lever, no `ScenarioConfig` field, no solve, no run registered, no keeper or
matrix movement.**

**Authority.** Decision card F, signature **F1 — "schedule the data-provisioned tier"**, owner-signed
2026-08-11 (`docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md`). That signature is the
explicit cron sign-off CLAUDE.md's GitHub-Actions rule requires on this private repo, and it is
cited in the workflow header.

**The gap closed.** `test_fleet_arrays_golden` went red 2026-07-26 and was carried as incidental
noise by seven sessions because CI's fast tier deselects it
(`-m "not slow and not integration and not fulldata"`) and a runner had neither `data/raw` nor
`data/clean` (FINDING-ercot187 §5: "a golden nothing schedules is not a guard").

**What landed.**

* **`.github/workflows/golden-data-tier.yml`** — durable workflow: `workflow_dispatch` + weekly
  cron (`37 5 * * 1` UTC). Runs the exact complement of the fast tier
  (`-m "slow or integration or fulldata"`), serial per rule 12, minus three machine-speed
  performance/benchmark classes deselected with reasons in the header (`TestPerformance`,
  `TestFullYearPerformance`, `TestSolverBenchmark` — shared-runner speed is not a model property;
  they stay in the local full lane, budgets untouched). Provisioning: non-cone sparse checkout of
  the audited `data/raw` paths (~1.5 GB of the 7.5 GB tracked; measured by a process-tree
  file-open audit over full local provisioning + tier runs, validated 419/419 tracked audited
  paths in a sparse scratch worktree) plus in-job `regenerate_clean.py` of nine datatypes and a
  year-scoped `curate_emissions.py --years 2023` (full-span is ~3.5 min/year × 9 years with a
  ~6.5 GB RSS peak; the tier's only emissions consumer reads 2023).
* **`scripts/check_data_tier_report.py`** (+ 7 hermetic tests, fast tier) — the loud-failure half
  of the F1 contract: any test skipped for a missing `data/raw`/`data/clean` input FAILS the run,
  and the golden must be present AND green in the junit report, so a future `-m`/marker drift that
  deselects it (the exact card-F failure mode) is a red run, not silence.

**The tier, run this session (locally, exact workflow command): 42 passed / 2 failed / 2 skipped
(both benign env-gated: `RUN_SLOW_FORECAST`, `RUN_GOLDEN_FORECAST`), 3 m 28 s serial.
`test_fleet_arrays_golden` is GREEN** (ercot-187's regeneration holds; nothing regenerated here).
The guard verdict on the report: clean — no data-missing skips, golden ran and passed. The two
reds are pre-existing HEAD failures the newly-provisioned tier SURFACED, both attributed, neither
touched here (both are other lanes' cells; silent-green by narrowing the tier was refused):

1. **`test_ff_readiness_battery::test_build_registration_scorecard_no_iso_gate_open`** — every
   ISO's `config_green` is False on the `cache_key_stable_round_trip` check.
   Attribution, measured not inferred: `ScenarioConfig.cache_key()`'s drop-if-default comparison
   is type-strict (`scenarios.py:12319`, `payload_dict.get(name) == getattr(defaults, name)`), and
   exactly two `_CACHE_KEY_OPTIONAL_FIELDS` members have tuple defaults —
   `miso_offer_surface_netload_pcts` and `miso_offer_surface_position_bins`, registered 2026-08-11
   by the MISO offer-surface lane. A yaml round-trip coerces them to lists, so a from-yaml config
   at pure defaults hashes differently from a fresh one (02d559f6a00f24b7 vs 789aa8f81999a13e).
   The four older `*_offer_surface_netload_pcts` tuple fields are NOT cache-key-registered, which
   is why this was green at ercot-187's 2026-08-10 census. The fast-tier twin
   (`test_config_completeness_cache_key_stable_round_trip`) fails at HEAD too — this is ambient
   main red, owned by the MISO offer-surface / cache-key lane (the fix direction — normalizing the
   comparison — moves no fresh-config keys, but it is cache-key infrastructure with its own
   guard discipline, not this session's).
2. **`test_consume_lmp::test_clean_backed_lmp_matches_raw_loader`** — PJM RTM 2024 clean-vs-raw
   parity, max |raw−clean| = $408.70. Previously never ran (skipped for the absent clean slice —
   nothing ever provisioned it; this is the tier doing its job on first light). Attribution: a
   DST clock-basis disagreement — the 5,703 differing hours are exactly the 2024 DST window
   (spring-forward through fall-back), and inside it the two series are equal modulo a one-hour
   shift. The `data/dictionary` lmp schema (tz-aware UTC `interval_start`) is the contract to
   adjudicate against; owned by the LMP data-contract lane.

**Fences held:** no per-task workflow (this is the one durable tier card F scoped); no solve; no
keeper/matrix movement; rule 27 (workflow files edited locally, pushed as on-disk bytes,
governance-log blob verified after push).

## 2026-08-12 — g3-delete: `split_coal_tranches` + the six `coal_tranche_*` scalars DELETED (ercot-188 G#3 owner ruling executed; cross-ISO hygiene, NO LP)

**What.** Rule 26 `[R-DELETE]` executed on the signed ercot-188 ruling
(`docs/DECISION-CARD-ercot188-open-owner-rulings-2026-08-11.md` §G.3): the legacy
non-CAMPD coal take-or-pay split `offer_curves.split_coal_tranches` (and its
`_coal_tranches` helper) is deleted, together with the six registered scalars
`coal_tranche_{1,2,3}_frac` / `coal_tranche_{1,2,3}_fuel_passthrough` — deleted,
not zeroed, exactly as the ruling orders ("a deprecated parameter that still
parses is a re-armable answer key").

**The proof came first, as the ruling requires — every registered bundle, not just
the six keepers.** Probe
`scripts/probes/ercot188_g3_split_coal_tranches_unreachability.py` (committed
evidence `results/calibration/ercot188_g3_unreachability_proof.json`): all **158**
committed `run_config.json` under `results/` (calibration, hindcast, ffr*
experiments) and all **66** backcast registry sidecars carry
`use_campd_bins=True`, every ISO is in `CAMPD_BINNING_ISOS`, and each ISO's bin
artifact exists in-repo (ERCOT curated CSV; five `thermal_tranches_<ISO>.csv`) —
so `build_dispatch_fleet` takes the CAMPD limb everywhere and the else limb that
held the sole `split_coal_tranches` call site is dead for the entire registered
corpus. This generalizes miso-128 §4's dynamic MISO adjudication (fleet assembled
twice under perturbed fractions, zero delta).

**Mechanics.** The six defaults (0.30/0.00, 0.25/0.35, 0.45/1.00) move HASH-ONLY
into `scenarios._CACHE_KEY_RETIRED_FIELDS` (the nyiso-114 `ct_*_hr_override`
pattern) — every historical cache key and the golden forecast fixture stay
byte-stable (pin-guard tests green) and nothing can be re-armed. The non-CAMPD
else limb now passes coal through unsplit at full fuel cost (gas split unchanged).
TIER_TAGS entries, the `data.fleet` facade re-export, the facade-census test
lists, the runner mock patch, and the split-specific unit tests are removed;
`TestCoalTranches` keeps the `apply_coal_tranches` fuel-frac arithmetic test on a
directly-built fixture (the CAMPD-path contract). The DOF-ledger
`coal_take_or_pay_tranches` entry retires with a closure note — **issue #1336
(re-ground the step sizes) is CLOSED BY DELETION**. Registry hygiene:
`frontend/data/parameters.json` / `docs/parameter-citations.md` drop their seven
stale entries (hand-pruned; the full registry regen carries 62 unrelated backlog
entries and was NOT ridden along). Matrix duties (rule 28): the
`coal_takeorpay_committed` base-row def/note record the execution,
`--fix-anchors` repairs the line-anchor drift my `scenarios.py` edit caused, and
§5.7 of `docs/mechanism-testing-matrix.md` carries the cross-ISO record.
`check_mechanism_matrix.py` exits 0 with zero warnings.

**Fences honored.** NO solve, NO keeper movement, NO cell verdict moved, no other
cleanup. Historical records (probe scripts ercot135/136, _miso128/129, DIAGNOSIS/
PRECOMMIT docs, committed `run_config.json` artifacts) are untouched — the
serialized keys in immutable run artifacts are the record of what those runs
carried, and the canonical loaders filter to known fields. Pre-existing, unrelated
at HEAD: `ci_refactor_guards.py` fails on `gen_caiso189_attestation.py`
referencing `gen_caisoNNN_attestation.py` (fails identically with this session's
changes stashed; belongs to the caiso-189 lane). Fast-tier result: **6694
passed, 5 failed — all five reproduce byte-identically on `origin/main`**
(verified in a worktree with main's own `src/` on `PYTHONPATH`):
`test_ercot_thermal_as_endogenous.py::TestScreenMutualExclusion` (2),
`test_ff_readiness_battery.py::test_config_completeness_*` (2),
`test_cache.py::TestConfigSidecar::test_config_yaml_present_alongside_parquet`
— environment-dependent at HEAD, not this lane's fallout; the cache-key
round-trip reproduces CLEAN standalone against this branch's config layer.

## 2026-08-15 — SITE RETENTION, all six lanes: the backcast pages reduced to the CURRENT keepers, their out-of-sample touchpoints and the LIVE remediation record (70 → 12 runs)

**Owner directive, this session:** the Run Explorer and Calibration Status pages
must show the **current keeper runs and results**, and any run **prior to the
keeper**, or **rejected wholesale after it as offering no new mechanism for
closing the C calibration gates**, comes off the site. This generalises the
2026-08-09 NEISO/PJM directive (recorded in those two lanes'
`site_retention_note`) to every ISO. **NO SOLVE RAN. No keeper moved, no verdict,
caveat, frontier declaration, mechanism-matrix cell or holdout posture changed.**

**FIRST, THE PART THAT WAS ALREADY CURRENT — verified, not assumed.** The
Calibration Status page renders from `status/<ISO>.js`, and
`scripts/build_status.py --check` re-scores **every** ISO's current keeper bundle
with `calibration_verdict.py` at this HEAD and compares: **6/6 in sync**, before
and after this change. So the determinations the page shows —
**ERCOT NOT-YET · PJM CALIBRATED · CAISO NOT-YET · NYISO CALIBRATED-WITH-CAVEATS ·
NEISO CALIBRATED-WITH-CAVEATS · MISO NOT-YET**, rubric v3.2 — are the actual
current model results, including the two promotions landed today (nyiso-135
promoting `2026-08-08-nyiso-133-cod-arm`, and ERCOT's
`2026-08-15-ercot204-rule26-delete`). What was stale was the **run roster**: 70
registered runs, 58 of them superseded probe/control pairs the keepers had already
passed by.

**AFTER (12 runs).** ERCOT 1 · PJM 5 · CAISO 1 · NYISO 1 · NEISO 2 · MISO 2.

| ISO | kept | ground |
|---|---|---|
| ERCOT | `2026-08-15-ercot204-rule26-delete` | keeper IS the newest run |
| PJM | `2026-08-04-pjm-152-collapse`, `2026-08-05-pjm-2022-touchpoint`, both `2026-08-06-pjm-158` arms, `2026-08-15-pjm-162-inputclock` | keeper + NOT-YET 2022 touchpoint + the live post-touchpoint remediation record (DA-virtual question OPEN; DEBUG-B input-clock repair is a keeper CANDIDATE) |
| CAISO | `2026-08-09-caiso-188-d1-micseam` | keeper IS the newest run |
| NYISO | `2026-08-08-nyiso-133-cod-arm` | keeper IS the newest run; no touchpoint exists (holdout freeze ACTIVE) |
| NEISO | `2026-08-14-neiso-93-envelope`, `2026-08-06-neiso-2022-corrected-basis` | the 2026-08-09 rule, unchanged: keeper + a PASSING 2022 touchpoint |
| MISO | `2026-08-09-miso-148-basis-aware`, `2026-08-13-miso-155-control-p0` | keeper + the one post-keeper run that is not a rejected mechanism (miso-155 closed the lane's standing instrument blocker) |

**PRUNED ON THE "REJECTED WHOLESALE" GROUND rather than on age** — the two cases
the directive's second clause exists for, both POST-keeper:

* **`2026-08-11-miso-151-{control,offer-surface}`** — MISO `measured_offer_surface`,
  "chartered, built, solved, REGISTERED and REJECTED" (miso-151), cell **U → R**.
  Refused *although* the arm improved both failing gates (C3a-2025 −15.6 → −14.9 %,
  C3b-2025 NRMSE 0.212 → 0.207), because its identification was refuted by the
  session's own G-1/G-5 measurements. No admissible mechanism toward C3a/C3b.
* **`2026-08-14-pjm-161-{control,event-cap}`** — `pjm_measured_outage_event_cap`,
  **refuted by its own pre-registered predictions**, cell **R**, a null result in
  the top-1 % net-load hours. pjm-162 then closed the whole
  "model envelope vs PJM's published aggregate" family **DO-NOT-REDO** and
  redirected the lane (PJM's scarcity defect is not an availability defect). The
  control measures nothing without the arm.

Everything else pruned pre-dates its lane's keeper, including four keepers' own
zero-delta A/B controls (the 2026-08-09 NEISO precedent for pruning a control) and
`2026-08-14-ercot202-arm-plantphysics`, the immediate predecessor keeper — whose
12 committed hourly sidecars are **sha256-identical** to the promoted ERCOT bundle,
so removing it loses no number.

**Mechanics and what dangles.** `scripts/prune_iso_runs.py --iso <ISO>
--force-uncite` per lane, deleting the registry sidecar, `runs/<id>.js` and the
mapped `results/calibration/<bundle>/` together (the three-store discipline).
`--force-uncite` was required and used deliberately: run-id citations in
`keepers/<ISO>.json`, `calibration-complete.json` and the mechanism-matrix shards
now point at runs no longer on the site. **Nothing is retracted** — every pruned
run's determination stands and its durable evidence is retained in full
(`results/calibration/FINDING-*`, `docs/calibration-log/<iso>.md`, the matrix
cells, git history). Each lane's `site_retention_note` names its own pruned ids
and its own dangling citations.

**Gates, all green after the prune:** `check_registry_payload_parity.py` (12 runs,
0 orphans, 0 dangling ablation refs) · `audit_keepers.py --check` **0 failures /
0 warnings** · `build_status.py --check` **6/6 in sync** ·
`check_mechanism_matrix.py` integrity + anchors + keeper stamps + §5.x prose OK ·
`build_manifest.py` assembles 12 runs across all six ISOs with every keeper year
present (NEISO/PJM additionally 2022 from their touchpoints).

## 2026-08-17 — RUBRIC v3.3 (owner amendment): a ledgered C3c caveat is REPORTED, not determination-DOWNGRADING — NYISO and NEISO keepers now read CALIBRATED

**Owner directive, verbatim.** *"NYISO should be declared calibrated. C3c is an
acceptable miss and shouldn't change a declaration from calibrated to calibrated
with caveats because it's a known model limitation that's been ledgered."*

**What changed (scorer-side only — NO SOLVE, no mechanism change, no keeper
promotion).** `calibration_verdict.determine_from_artifacts` no longer counts a
LEDGERED caveat toward the downgrade from `CALIBRATED` to
`CALIBRATED-WITH-CAVEATS`. Because ledgering has been restricted to C3c alone
since v3.1 (`LEDGERABLE_CRITERIA`), the amendment can say exactly one thing and
cannot reach any other criterion. It **withdraws** the v3.0–v3.2 clause *"never
`CALIBRATED`"*, which is left verbatim in the prior rubric entries and in
CLAUDE.md rule 22 guard (d) as annotated genealogy.

**Why this is a reporting change, not a band change.** The C3c band, tier and
measured magnitude are untouched, and the criterion still reads `CAVEAT` and
**never `PASS`** — so `grade_summary.target_grade` does not absorb it. The miss
is still printed at full magnitude, still listed in `caveats.ledgered`, still
counted in `grade_summary.ledgered`, and now **named on the determination basis
of a `CALIBRATED` run** (the reason line is emitted on both branches, last, so
it never displaces a downgrading reason from `headline()`). Silence in any of
those channels is what would have made this an escape hatch.

**What still binds.** The ledger entry (or the C3c standing rule's auto-entry
with its exhaustion citation) is still required. The budgets are untouched and
are checked **before** the new branch — >1 ledgered or >0 protective caveats is
still `NOT-YET`, so the 1-slot ledgered budget is now the *sole* numeric bound
on what may be carried without a downgrade. Every other caveat route still
downgrades: commercial-band target misses, protective-gate caveats, `SKIPPED`
criteria, data-blocked years. And the `FAIL` path is untouched — a C3c miss that
is not ledgerable, because a second criterion also fails or governance does not
pass, still stands as a `FAIL` and still carries the run to `NOT-YET`. A run
reads `CALIBRATED` only when a ledgered C3c is its **single** blemish.

**Effect, MEASURED over all 26 registered runs against a pre-change snapshot
rather than asserted.** Six determinations change, all `CALIBRATED-WITH-CAVEATS
→ CALIBRATED`, all of the same shape (lone ledgered C3c; zero band caveats, zero
protective caveats, nothing `SKIPPED`, nothing data-blocked):

| run | ISO | keeper? |
|---|---|---|
| `2026-08-16-nyiso-140-layup-exclusion` | NYISO | **KEEPER** |
| `2026-08-17-neiso-99-joint-p1` | NEISO | **KEEPER** |
| `2026-08-08-nyiso-133-cod-arm` | NYISO | no |
| `2026-08-17-nyiso-142-stackdup` | NYISO | no |
| `2026-08-17-neiso-97-dstrepair` | NEISO | no |
| `2026-08-06-neiso-2022-corrected-basis` | NEISO | no |

No `NOT-YET` is reclassified in either direction, and CAISO / ERCOT / MISO / PJM
are **unchanged** (each keeper either fails a criterion outright or carries no
ledgered C3c). Every keeper re-scores in place from its committed artifacts.

**THE NEISO FLIP IS A CROSS-ISO CONSEQUENCE, CARRIED OPENLY.** The amendment was
requested for NYISO; NEISO's keeper moved because the verdict scorer is **one
instrument**. An ISO-scoped verdict rule would be an off-registry tuning channel
in spirit (rules 24 `[R-REGISTRY]` / 25 `[R-ISO-SCOPE]`), so there is no honest
way to move NYISO's determination without moving every run of the same shape.
Flagged to the owner rather than suppressed; NEISO's keeper shard carries its own
`determination_amendment` note saying so.

**HOLDOUT POSTURE UNTOUCHED — nothing became spendable.** Both ISOs keep
`complete` (validation tier) only, both stay **absent** from `final`, and the
2026-07-25 holdout spend freeze remains **ACTIVE** and outranks every marker. A
determination is not an authorization: no out-of-training year may be solved,
scored or registered for any ISO while the freeze stands.

**A latent defect fixed in the same session** (`audit_keepers._asserted_determination`).
The determination-token extractor scanned token-list-first (longest token first,
anywhere in the text), so a determination named in a marker's deliberately
**preserved genealogy** (`|| PRIOR TEXT, preserved: CALIBRATED-WITH-CAVEATS on
<superseded run> …`) outranked the entry's own leading claim — an accurate marker
could not be written without deleting its history. It now scans by **position**,
taking the longest token at the earliest position, and a position filtered out as
naming another run's recipe takes its own prefix with it (the regression the
first cut of this fix introduced, caught by its own test). E5 and M1b are
otherwise unchanged.

**Records updated:** `scripts/calibration_verdict.py` (v3.3 + tests),
`scripts/audit_keepers.py` (+ tests), `docs/calibration-determination-rubric.md`
(banner, §2 decision logic + determination table, §9), `CLAUDE.md` rule 22 guard
(d), `docs/governance/rule-history.md` §4, both keeper shards
(`determination_amendment`), both `complete` markers (re-keyed per rule 22
D-5(b) — the determination **improves**, so the worse-determination stop does not
fire), both keeper registry sidecar definitions, both mechanism-matrix shard
`gates` stamps, and all seven `status/` parts (`build_status.py`).

**Gates:** `audit_keepers.py --check` **0 failures / 0 warnings** ·
`build_status.py --check` in sync · `check_mechanism_matrix.py` integrity +
anchors + keeper stamps + §5.x prose OK · scoring tests **162 passed** (the 4
`test_ff_readiness_battery` failures on this checkout are a pre-existing,
unrelated unbuilt-`data/clean` environment artifact — reproduced with the change
stashed).

## 2026-08-18 — RUBRIC v3.4 (owner amendment): the C1 volume band is floored at the share leg's own materiality — CAISO keeper C1 2023 CC_REGULAR flips FAIL → PASS

**Session caiso-c1-lmp-pricing. Owner directive verbatim:** *"Ccgt is fine at
-1.8% for passing c1 gate … I want … a shift that declares c1 for 2023
calibrated."*

**THE CHANGE.** C1's volume leg becomes
`vol_band = min(max(2.0% of ISO load, 3.0% of ACTUAL total generation), 8 TWh)`
(`calibration_verdict._fuelmix_vol_band`, shared by `score_fuelmix` and the C2
preliminary-family fallback). **No new constant:** the floor is
`FUELMIX_SHARE_PP` (3.0) applied to the actual-side generation total — the same
±3.0-pp-of-mix materiality the share leg already declares.

**WHY IT IS A COHERENCE REPAIR, NOT A RESIDUAL FIT.** On a deep net-importing
ISO the 2%-of-load term could bind *tighter* than the rubric's own declared
mix-materiality on the same class — CAISO 2023: ±4.15 TWh (2% of 207.4 TWh
load) vs ±5.27 TWh (3% of 175.7 TWh actual generation) — failing a class whose
miss the share standard calls fine (CC_REGULAR −4.24 TWh = −2.4% of actual
generation, share −1.8 pp). The floor is measured in raw |model−actual| TWh
over the **actual** generation denominator, deliberately not `share_pp`, which
a system-total shrink (over-import displacing the class) flatters: the same CC
row reads −1.8 pp on share but −2.4 pp of actual gen, and the floor gates on
the un-flatterable −2.4. Unchanged: the 8 TWh cap (large-ISO bands
bit-identical), the ±3.0 pp share leg (MISO CC_REGULAR +47 TWh / +7.7 pp still
fails both legs), and the 2%-of-load term wherever it is wider.

**EFFECT AT AMENDMENT, MEASURED over all 26 registered runs against a
pre-change snapshot rather than asserted:** exactly **one row** flips — CAISO
keeper `2026-08-17-caiso-200-h1-memberpanel` C1 2023 CC_REGULAR FAIL → PASS
(|−4.244| ≤ 5.272), taking its C1 criterion FAIL → PASS. The determination
stays **NOT-YET** on the standing C3a mean-LMP miss (+12.8/+15.7% in
2024/2025), which is now the **sole** load-bearing gate on the CAISO lane. No
other record of any run of any ISO changes status; no determination label
changes anywhere. No solve ran. The two nyiso-143 registrations that landed on
main mid-session (after the snapshot) were verified separately: NYISO's floor
does bind (band ±2.94–3.03 → ±3.80–4.08), but no gated row of either run sits
between the old and new bands, so both are status-identical under v3.4.

**WHAT THE BAND SHIFT DOES NOT DO.** The CC-side under-dispatch / over-import
residual (caiso-121 surplus-belly, caiso-135 ride-through, caiso-140 §B) is
unchanged as a structural object — the amendment changes what the rubric
charges for it, not the physics. The C3a lane inherits it: the same over-import
conduct that flattered the share leg is a named suspect in the 2024/2025 price
level overrun.

**Records updated:** `scripts/calibration_verdict.py` (v3.4 + tests),
`scripts/lib/rubric_consts.py` (+ `fuelmixVolGenFloorFrac` export + test),
`docs/calibration-determination-rubric.md` (banner, §C1, §C2 deferral text, §8
comparables row, §9), `docs/codebase-site/js/backcast-runs.js`
(`volInTol`/`volBand` mirror), `frontend/data/backcast/rubric-consts.js`
(regenerated), the CAISO keeper shard `disposition_note` + registry sidecar
`definition` (dated v3.4 re-score preambles, promotion-time text preserved
verbatim), the keeper bundle `metrics.json` (re-written by
`--write-metrics`), and all seven `status/` parts (`build_status.py`).

**Gates:** `audit_keepers.py --iso CAISO` **0 failures / 0 warnings** ·
`build_status.py --check` in sync (6/6) · verdict + rubric-consts suites **133
passed** · scoring lane **1033 passed** (the 4 `test_ff_readiness_battery`
failures and 1 `test_crossover_harness` failure on this checkout are
pre-existing unbuilt-`data/clean` environment artifacts — reproduced with the
change stashed) · ruff clean.

## 2026-08-20 — D-2/D-4 UNIT-GRAIN FLOOR-CLASS ATTRIBUTION (miso-171 carry-forward a): the plant-grain mis-attribution is repaired in the scorer, every designated keeper re-scored, ZERO determination movement

**Scorer-only, no LP, no rubric change.** `legitimacy_diagnostics.py` gains
`FloorClassMatrix`: the plant-hour FLOOR class under the same
maximum-composition rule as the plant-hour mechanism (the class of the unit
contributing the largest floor that hour; empty groups impute to the plant
majority first — #1488 unchanged). D-2 mechanism attribution and D-4
(mechanism × class) selection key on it, so a mixed-class site's
minority-class floor is charged to the class that CARRIES it, never the
plant label (the miso-170 K-1 forensic: plant 1104's CT_PEAKER floor
convicted under ST_GAS's conduct row). Row-label attribution is preserved
behind `floor_klass=None` — legacy artifacts re-score byte-identically.

**Re-score of all six designated keepers** (regen before/after on one
rebuilt-floors baseline; verdicts on in-place-swapped diagnostics, bundles
restored byte-identical; record
`results/calibration/_miso171_d4_attribution_rescore.json`, report
`RESULT-miso171-d4-attribution-repair-2026-08-20.md`):
**zero determination flips in any ISO; the charter's other-ISO escalation
trigger does not fire.** ERCOT/CAISO/NYISO/NEISO: zero deltas of any kind.
MISO: ~0.3 TWh/yr of reliability_floor energy re-attributed ST_GAS/CC →
CT_PEAKER, zero C8 record flips (CT_PEAKER-2023 lands 15.17 % vs the 15 %
cap and grounds). PJM: the mirror-image case — the repair flips C8
CT_PEAKER 2023/2024/2025 **FAIL → PASS on the regen baseline**
(mis-attributed ST_GAS floors had pushed CT_PEAKER to 16.4–16.8 % vs 15 %).

**Disclosed, pre-existing, NOT repaired here (owner-relevant):** on the
regen baseline the PJM keeper reads NOT-YET on forced_share (ST_GAS-2025 C8
FAIL) while its committed artifact reads CALIBRATED — the same
regenerated-vs-committed exposure family miso-169 K-3 disclosed for MISO,
now measured at PJM; this repair narrows it (3 of the 4 regen-baseline C8
failures were the mis-attribution) but does not close it. CAISO's regen
baseline carries 23 D-4 row failures absent from its committed artifact
(C8/determination unchanged). Raised with the two standing C8 rubric design
questions (denominator = model's own class output; no materiality floor
inside the provenance leg) in the RESULT §5 — owner decisions, not a
session's.

## 2026-08-22 — RHO_CLIP floor DELETED (owner ruling, card nyiso-145 option A) — cross-ISO flag for the MISO lane

Owner ruling (session nyiso-151, rule 22 D-5(b)): `RHO_CLIP` moves
`(0.5, 4.0) → (0.0, 4.0)` in `src/market_sim/data/online_reserve_rho.py` —
option A of `docs/DECISION-CARD-nyiso145-rho-clip-band-2026-08-19.md`, on the
card's own recommendation (the floor had no primary citation, no physical
basis, and was inherited across a change of estimand; every measured row on
two ISOs' fleets sat below it). Every measured `online_rho` now solves at its
own measurement; the 4.0 ceiling keeps its min-load derivation.

**MISO LANE ITEM (rule 25 — flagged here, not executed):** MISO's armed
`miso_reserve_online_gated` keeper solved at the floor (0.5, measured
0.1764). Its committed bundle stands as solved; any FUTURE replay/re-solve of
the recipe now uses the measured 0.1764, which TIGHTENS the additive coupling
row (the conservative-at-floor direction miso-169 recorded inverts to
measured-at-meter). The MISO lane should re-gate its keeper recipe against
the measured coefficient on its own schedule and re-stamp its shard. NYISO's
current keeper arms neither gated flag, so this change is byte-inert for
every registered NYISO run.

## 2026-08-22 — `_ramp10_capability` measured-reconciliation seam: cross-ISO code note from the NYISO lane (nyiso-152 phase-0)

The NYISO lane's phase-0 measurement
(`results/calibration/FINDING-nyiso152-phase0-reserve-posture-overturned-2026-08-22.md`)
adjudicated the "hydro RAMP10 seams" queue item **provably LP-inert for
NYISO** (its reserve design consumes no ramp10 quantity). The two code seams
the item recorded are real, and they now belong to the lanes whose designs DO
consume ramp10 (ERCOT supply caps, PJM/MISO/CAISO pergen deliverable-ramp
pools) — rule 25 `[R-ISO-SCOPE]`, each lane decides on its own evidence:

* `src/market_sim/data/fleet/withholding.py::_ramp10_capability` reconciles a
  measured unit cap onto the class fraction only `if measured and frac > 0.0`
  — a fuel whose `RAMP10_FRAC_BY_FUEL` entry is absent/0.0 (hydro everywhere;
  CAISO backfills hydro separately via `CAISO_HYDRO_RAMP10_FRAC`) can never
  receive measured capability through this seam even where data exists
  (EIA-860 Sch. 3.1 flags 96.1 % of NY hydro nameplate `10M`; other states
  unmeasured here).
* `scripts/lib/ramp_capability/` has per-ISO modules for some lanes and not
  others; a lane arming `measured_ramp_capability` should verify its own
  module exists rather than assuming the flag is live.

No lane's verdict, keeper or matrix cell is touched by this note; it is
discovery hand-off only.

---

## 2026-08-25 — rubric v3.5: the diurnal price-amplitude call is ANSWERED (owner, option B)

Session `xiso-amplitude-rubric-card`. **No LP solved, no keeper moved, no
determination re-written, no dashboard registration.**

The owner call filed by **neiso-74** and re-filed by **xiso-1** on 2026-08-01 —
should the rubric gain a diurnal price-amplitude criterion? — is **answered:
OPTION B, REPORTED-ONLY and BAND-FREE** (card
`docs/DECISION-CARD-xiso-diurnal-amplitude-rubric-2026-08.md`, ruled 2026-08-25).

**What made it answerable** was measuring what the answer would *do*, which
neither prior filing had: `scripts/probes/_xiso6_amplitude_criterion_band_probe.py`
swept 10 candidate bands × 6 ISOs × 3 candidate tiers offline over the committed
records. A *gating* criterion is **vacuous** below a 25 % amplitude floor (every
keeper passes, one at 20.8 %) and **universal** above 45 % (5–6 of 6 ISOs FAIL,
all three `CALIBRATED` determinations lost), with **no external comparable**
anywhere in the 20–45 % window to anchor a band — the same ground **C7 was
retired on at v3.1**. v3.5 therefore applies v3.1's own disposition to prices:
**gate not built, measurement kept.**

**Cross-lane facts established, none of them transferred (rule 25):**

* **It is one STATISTIC, not one OBJECT** (rule 19 `[R-ONE-MECH]`). Four ISOs
  have now decomposed their own cell and they **disagree** — NYISO
  reserve-dominated (reserve-stripped energy swing 117/97/107 %, i.e. essentially
  no energy-side defect), NEISO explicitly *not* NYISO's (reserve 33/43/32 %,
  over-dear trough), MISO a two-sided night floor, CAISO south-concentrated with
  NP15 **under**-priced in its mid bucket. ERCOT and CAISO carry no ISO-local
  amplitude decomposition. This is why one criterion could not have graded them.
* **The cancellation coupling**, measured for the first time: trough over-priced
  in **18/18** ISO-years, and a peak-only repair flips **load-bearing,
  non-ledgerable C3a** PASS → FAIL at PJM 2023, CAISO 2024 and NEISO 2024.
* **NEISO's PS DO-NOT-REDO is NOT lifted by this ruling**, in either direction —
  it is a mechanism finding (the storage block is already optimal for the price
  signal it is shown), and a rubric disclosure changes no dispatch. The open act
  there is a **charter for the neiso-76 stack-traversal route**, put to the owner
  and not opened here.

**Two defects fixed in passing, filed rather than buried:**

* `REPORTED_ONLY` records were **computed and silently dropped** since v2.9 —
  only `CRITERIA` members reach `per_criterion`, so C5a `co2` reported nothing.
  A `reported` block now carries them into the verdict, `render_text` and
  `metrics.json`.
* **`lmpDeltaHr`'s `-32768` NaN sentinel**, read unmasked, inflates MISO 2025's
  amplitude from 20.8 % to **186.9 %** (hour 8759 has no committed actual). The
  scorer masks it and drops the day. **FILED FOR OTHER LANES:** at least seven
  committed probes decode `lmpDeltaHr` directly and may carry the same
  corruption wherever an actual is missing — each lane should check its own.

**Determination-neutrality is verified, not asserted:** all 55 registered runs
re-scored before and after — zero determination diffs, zero per-criterion status
diffs, zero caveat/grade-summary diffs; 161 D-A records, 0 skipped. Pinned by
`DiurnalAmplitudeReportedOnlyTests.test_IT_CANNOT_GATE`.

Pre-existing at HEAD and **not touched** (verified identical on a clean
baseline, forecast lane): 5 failures in `tests/scoring/test_ff_readiness_battery.py`
and `tests/scoring/test_forecast_parity.py`.

No lane's verdict, keeper or matrix cell verdict is touched by this amendment.

---

## 2026-08-25 — audit_keepers E11: keeper-lineage recipe fidelity extended to the FULL `solve_and_persist` kwarg surface (the nyiso-108→155 silent-de-arm guard)

Chartered by `docs/FINDING-nyiso-hydro-truncation-repair-2026-08.md` §2/§6
(the "own charter" successor item), landed from session nyiso-156. The
incident class: `hydro_backfill_year`/`hydro_eia930_monthly` are
`solve_and_persist` kwargs, not `ScenarioConfig` fields, so the
"all scenario_config fields identical" lineage-fidelity checks used across
the nyiso-125..133 window were structurally blind to them, and an armed,
owner-promoted keeper mechanism (nyiso-108) fell out of the keeper lineage
with no de-arm decision anywhere — the miso-50..53 lossy-reconstruction
class landing in the keeper lineage itself.

**The guard:** `scripts/audit_keepers.py` check **E11**. Whenever an ISO's
keeper shard records a structured lineage (`superseded.former_keeper` — the
NYISO convention), the auditor diffs the current keeper bundle's full
recorded recipe — `run_config.json`'s scenario block ∪ `meta.json`'s
solve-kwarg surface (the `_config_block` merge pattern of
`scripts/probes/_nyiso155_hydro_repair_ab.py`, generalized) — against the
former keeper's bundle. A kwarg whose recorded value changed **FAILs unless
declared in the shard's prose**; a kwarg recorded only by the former bundle
(codebase field deletion, the rule-26 class) WARNs; fields born between the
solves are reported, never gated (their declaration duty belongs to the
rule-28 matrix CI). Meta provenance keys mirror `replay_keeper._IGNORE`,
pinned by `tests/scoring/test_audit_keepers_lineage.py` so the duplicated
stdlib-only set cannot drift. Because the auditor runs on every keeper-shard
edit (the `calibration-keeper-auditor` agent), the check fires exactly at
promotion time, when both bundles are on disk.

**Live behaviour at introduction:** NYISO (the one shard with the structured
record) reads OK — the 152→155 diff is exactly the two DECLARED hydro-repair
keys plus 4 born-at-default fields; every other lane reads OK with a
"not applicable" note. **The guard arms lane-by-lane as shards adopt the
`superseded.former_keeper` convention at their next promotion** — a lane
that wants the protection writes the structured block instead of (or beside)
its free-form supersession prose. No verdict, keeper, or matrix cell moves.

## 2026-08-30 — Q5 RE-RULED at capx r#12: NYISO `complete` marker WITHDRAWN (CAISO precedent applied UNIFORMLY) — the written reconciliation lands

**Owner ruling, capacity-expansion director refresh-#12 decision card** (recorded
`docs/handoffs/capx-director-ledger-2026-08.md` §0i.2 and §3 Q5; option selected
on the card, verbatim label: *"Withdraw the marker (CAISO precedent)"*),
superseding the r#8 WAIT-FOR-WINTER-INTAKE ruling after Q5's recurrence clause
fired: the nyiso-157 promotion (2026-08-30) re-keyed the marker onto a **second
consecutive NOT-YET keeper** with the fail set widened (nyiso-155 {C3a-2025,
C3c} → nyiso-157 {C3a-2025 −12.0 %, C3b-2025 0.203 knife-edge, C3c
silenced-lone}). Executed by the Q5-W governance records lane — **records only:
no solve, no re-score, no keeper change**. Record:
`docs/FINDING-q5w-nyiso-marker-withdrawal-2026-08-30.md`.

### The uniform rule — what Q5's written reconciliation says

**A `complete` marker cannot stand on a NOT-YET keeper.** The 2026-08-06 CAISO
precedent governs every recurrence, whatever produced the NOT-YET — a rubric
re-score (CAISO) or a structure-over-gates keeper promotion (NYISO). The
**structural-integrity formula remains the standard for KEEPER promotions** —
nyiso-155 and nyiso-157 stand untouched as keepers, and the keeper shard was not
touched — **but it no longer sustains a `complete` marker** on a NOT-YET
determination. The two precedents that pointed opposite ways (ledger §3 Q5) are
reconciled in writing, the way the director asked; the owner took option (ii)
(uniform withdrawal) over the director's recommended option (i), recorded
plainly.

### Governance consequence — NYISO `complete` withdrawn

The NYISO entry moved from `complete` to `withdrawn` in
`frontend/data/backcast/calibration-complete.json` (declared 2026-07-31,
withdrawn 2026-08-30), in the CAISO precedent's recorded form: the withdrawal
entry preserves `keeper_at_declaration` (2026-07-30-nyiso-100-silretire), the
full `rekey_history` (11 promotions), the frontier history, and the prior
2026-07-19 phantom-outage withdrawal verbatim (nested as
`prior_withdrawal_2026_07_19`) — nothing erased. `complete` = **{NEISO, PJM}**.

**Nothing was spent, so nothing is lost.** Verified from the committed record at
withdrawal: all 15 NYISO registry sidecars declare solve years ⊂ {2023, 2024,
2025} and `bench/NYISO/` holds exactly 2023/2024/2025 — no NYISO
out-of-training year was ever solved, scored or registered, in the freeze era or
in the four-day 2026-08-26 → 2026-08-30 spendable window. **The validation-tier
(2020–2022) touchpoint authorization lapses with the marker**: the tier-aware
gates (`scripts/lib/holdout_policy.py`) re-block every NYISO out-of-training
solve/score/registration — verified post-edit, `authorized(NYISO, 2022)` is now
`False`. The locked test (2019, H1-2026) was never authorized and is unaffected;
`holdout-freeze.json` untouched (locked test stays frozen for every ISO).

**Both surfaces flipped in one session** (the charter's point — they cannot
disagree): the forecast board `frontend/data/forecast/program-status.json` NYISO
gate leg (a) moves pass → **fail** on the marker, `marker_complete` → false,
`closed_on` → ["a","c"], keeper display re-keyed to nyiso-157, headline +
gate_reading rewritten. Leg (b) untouched (PROMOTE-WITH-CAVEATS is the bare
`nyiso-t1f` verdict; no marker moves a bare verdict); legs (c)/(d) untouched; no
forecast-provenance stamp fields written (the D7 discipline). NYISO's gate reads
**(a) fail · (b) PASS · (c) fail · (d) none** — no ISO now holds (a)+(b) both.

**Re-entry** is a NEW explicit owner declaration once NYISO's designated keeper
again scores CALIBRATED (expected route: `INTAKE-SPEC-nyiso156-winter-locational`
Leg 2 + the C3c standing rule — the intake authorization is unaffected; rule 22:
what is held out is the score, never the data). `scripts/audit_keepers.py`
passes clean after the change (M1 iterates {NEISO, PJM}; no NYISO entry to
verify once absent).

## 2026-08-30 — TWO OWNER RULINGS (director decision cards): the CROSS-LANE RE-GRADE RULE (re-verify required) and the NYISO FRONTIER REVERT (frontier = {PJM, NEISO})

**Authority.** Owner rulings 2026-08-30, served as decision cards in the
program-director session and executed in-session the same sitting. Records
only: no solve, no re-scoring, no determination change, no mechanism cell
moved. Durable copies: this entry + the keeper-shard edit below + the audit
plan §8 ledger.

**Ruling 1 — CROSS-LANE RE-GRADE: RE-VERIFY REQUIRED (standing rule).** The
question carried since the nyiso-143 D-4 rider (one lane's scorer change
flipping a shared-benchmark determination) and given a second instance by
#4343 (the capx Q5-W lane writing this program's marker file): may one lane's
act re-grade another lane's/program's committed record? **Ruled: a scorer or
shared-file change that flips another ISO's or another program's committed
state requires the AFFECTED lane's own re-verification (rule 22 D-5(b)
style: from committed artifacts, never a solve) BEFORE the flip publishes.**
Uniform rules (like Q5-W's "a `complete` marker cannot stand on a NOT-YET
keeper") remain legal — the affected lane confirms rather than vetoes; a
re-verification that DISAGREES stops the flip and escalates to the owner.
Retires owner-queue item "cross-ISO scorer-change precedent" (carried since
v13). Both historical instances stand as correct in substance; neither is
re-opened.

**Ruling 2 — NYISO FRONTIER REVERTED; the frontier set is {PJM, NEISO}
ONLY.** Owner, verbatim: *"NYISO is not frontier it was reverted bc it's not
yet so it's PJM and NEISO only."* Executed as an append-only
`reverted_2026-08-30` key in the `frontier` block of
`frontend/data/backcast/keepers/NYISO.json` (the 2026-08-23 ratification and
its R-1 currency annotation are retained verbatim as the dated historical
record; the new key is the live state: NYISO holds NO frontier declaration).
`status/NYISO.js` regenerated (`build_status.py --iso NYISO`;
`shared.js` rebuilt byte-identical); `audit_keepers.py` PASS 0/0 post-edit.
**Effect: all four instruments now align — CALIBRATED = `complete` =
forecast gate-(a) passers = frontier = {PJM, NEISO}.** Retires v15
owner-queue item 1 (the frontier currency question) by making the marker
the master: a frontier ratification does not survive its ISO leaving
CALIBRATED/`complete`; re-entry is a fresh owner ratification on a
then-current assessment.

## 2026-08-31 — THE C3c SCARCITY PROGRAM OPENED BY OWNER RULING: the cross-ISO "hourly LP cannot form the tail" framing is FALSIFIED as a blanket claim, and two ledger entries are put in question in OPPOSITE directions (zero solve; cross-ISO records lane)

Owner ruling, verbatim: **"Open c3c scarcity question"** — taken in preference to
ruling the nyiso-161 winter-face waiver card, and immediately after the owner
permanently closed the NYISO AORR access route (*"I'm not getting new data access
so just kill that request on 1"*). Scoped and costed before any commitment in
`docs/CHARTER-c3c-scarcity-program-2026-08-31.md`. **Nothing armed, promoted or
adjudicated; no keeper, shard, marker, determination or matrix cell moves.**

**(1) The blanket framing is FALSIFIED.** Measured across all six designated
keepers from committed artifacts: **PJM PASSES C3c** at 0.67 / 0.56 / 0.54× of
its actual >$200 tail, in the SAME ISO-agnostic LP, solver and code path in which
**CAISO and NEISO form 0.00× in every year**. ERCOT 0.40/0.42/0.03×, MISO
0.10/0.16/0.01×, NYISO 0.10/0.00/0.02×. Several ledgers carry "an hourly LP with
$0 reserve offers cannot form the RT scarcity tail" as though it were uniform; it
is a spectrum with a working example at the top, and it should stop being written
as one phenomenon.

**(2) New cross-ISO measurement — the reserve-binding census** (from the
`reserve_family_<year>.parquet` sidecars, the only artifact in which a family's
binding is observable). PJM binds on OPPORTUNITY COST with **zero shortfall ever**
and duals to **$187.90**. NYISO binds only its CHEAP locational families ($25/$40
caps) while every NYCA-level product ($750/$775) never binds, capping its total
hourly reserve adder at **$90**. NEISO's three families are **entirely inert** —
zero duals, zero shortfall, all three years. CAISO has **no reserve family at
all** (`caiso_reserve_coopt=False`).

**(3) Two ledger entries are now in question, in OPPOSITE directions.**
* **NYISO's C3c caveat may be WRONGLY INHERITED.** Its lane adopted the
  cross-ISO probabilistic-premium diagnosis established on CAISO/MISO/ERCOT, but
  NYISO's own timing does not match it: in 2025 the model goes reserve-short in 24
  hours and **20 (83 %) are hours reality priced >$300**, in June–July — the
  summer scarcity days that constitute C3a-2025's summer face. CAISO's closure
  rests on the exact opposite measurement (caiso-144 §C/§D: 1.6–10.5 GW of model
  slack in reality's tail hours; overlay-to-reality overlap 1/47, 0/35, 0/8).
  NYISO is short in the right hours and cannot PRICE them. Artifact:
  `results/calibration/_nyiso163b_c3c_reserve_timing.json`.
* **PJM's C3c PASS has never been audited for the ercot-214 phantom signature.**
  ERCOT's ercot-213 tail gains were measured at ercot-214 to ride an AS-product
  shortfall-ramp leak — a price-formation channel the market does not have — and
  were removed at ercot-215, after surviving a promotion. PJM passes on duals to
  $187.90 with zero shortfall in every hour, and the same audit has not been run.
  **If that channel is phantom, a CALIBRATED keeper is resting on it.** The
  charter ranks this Q1, ahead of everything else, precisely because a passing
  criterion resting on a phantom channel is worse than a failing one.

**(4) What is CLOSED and must not be re-proposed** (rule 26 DO-NOT-REDO). The
naive program — "port PJM's scarcity formation to the other ISOs" — is dead on
three independent records: **CAISO** closed on model STATE not mechanism
granularity (`energy_reserve_coopt` CAISO **I**; caiso-144 §B: ≥854 MW family
slack in every one of 26,280 hours, so every optimum carries zero shortfall and
zero duals; §D refuses a backcast overlay ON MEASUREMENT, the LOLP overlay firing
Apr–Nov when reality was tight on winter mornings; §E identifies CAISO's real tail
as a winter-morning fuel/cold-snap tail already priced to its input ceiling);
**ERCOT** closed on the ercot-95…163 / 214…231 exhaustion record with the tail
established as CONDUCT-made on the energy offer stack (measured RTORPA p50 ~$1–5,
PRC p50 ~5.8 GW at the missed hours — reality had no reserve scarcity to recover);
**MISO/NEISO** ledgered to the probabilistic-RT-premium class (miso-101).
Adjudicated cells: `ordc_scarcity_overlay` CAISO K / NEISO K / PJM G / MISO G /
ERCOT R / NYISO ·; `energy_reserve_coopt` CAISO I, others K;
`dynamic_reserve_requirements` NEISO R; `reserve_deliverability_scoping`
CAISO/PJM I.

**(5) The program as chartered.** **Q1** PJM phantom-channel audit (zero solve;
may invalidate a CALIBRATED keeper — that is the point). **Q2**, gated on Q1
returning REAL: is NYISO short on the right PRODUCT, not just the right hour — a
QUANTITY question (was reality NYCA-level short?) with an explicit kill gate that
CONFIRMS NYISO's ledger if reality shows no NYCA shortage. **Q3** the
probabilistic-RT-premium class is an ARCHITECTURE decision colliding with rules 4
`[R-DUALS]`, 8 `[R-8760]` and the no-MIP constraint — **not recommended as a
calibration lane**. Q1+Q2 are two zero-solve sessions and will NOT by themselves
close C3c anywhere; what they settle is whether the C3c ledger is telling the
truth about PJM and NYISO.

**(6) The standing guard, restated because this lane is where it matters most.**
No fitted scarcity adder, no tuned VOLL, no raised published demand curve, no
ORDC offset swept against a residual. NYISO's $25/$40/$750/$775 are SOM-published
and cited in `model/reserves/spec.py`; changing one to reach a residual is rule
13 `[R-MEASURED]` / rule 1 `[R-STRUCT]` forbidden and is the exact ERCOT-214
failure. **Every candidate is timing-checked against reality BEFORE it is
priced**, on the caiso-144 §D construction. Verdicts stay per-ISO (rule 25): a
PJM finding enters other shards as `U`.

**(7) Matrix.** No cell moves — nothing was tested, armed or adjudicated.

## 2026-08-31 — FOUR OWNER RULINGS (director REFRESH sitting, decision cards): R-D C-1 wind TERMINAL REST + MAP · R-E the C3c program's Q1+Q2 CHARTERED AND CHAINED · R-F the nyiso-161 winter-face card DEFERRED with a dated re-serve trigger · R-G nyiso-160/leg2 CLOSED BY ARCHIVE

**Authority.** Owner rulings **2026-08-31**, served as decision cards in the
program-director REFRESH sitting and answered by the owner. Recorded by the
dispatched **audit-program rulings-records lane** under the standing recorded
deviation: **the director pushes nothing; records land through the dispatched
lane; THE OWNER MERGES.** **ZERO SOLVES** (rule 22 `[R-HOLDOUT]`); **no keeper,
shard, marker, determination, holdout file, `ScenarioConfig` default or matrix
**verdict letter** moves** in any of the four. Durable copies: this entry, the
per-ISO log entries named below, the new decision map, the two ERCOT matrix
cells' evidence stamps, and the audit plan §8 ledger + board v17.

**Base for every figure below: `d44446e0` (merge of #4464)**, re-derived at that
pin by the records lane — nothing carried from the dispatch.

---

**Ruling R-D — C-1 WIND: TERMINAL REST AT THIS REPRESENTATION GRAIN + DECISION
MAP.** On `docs/FINDING-c1-joint-wind-ab-2026-08-31.md` (owner ruling R-B's
chartered A/B; both kill-gates **PASS**; joint posture **`NON_COMPLEMENTARY`**).
Executed per the **caiso-222 §1(c) option-3 pattern** (owner ruling R-3,
2026-08-30): the residual is designated **ATTRIBUTED AND CLOSED at this grain**
with a map attached rather than an open investigation.

* **The measurement the ruling rests on.** The joint arm builds wind **1.442 GW**
  — to the megawatt the committed signal-alone arm's number — so it closes
  **8.87 %** of the **12.313 GW** ERCOT wind entry miss and **the volume rule
  contributes exactly ZERO wind** on a dual-based level, against a naive sum of
  the singles of **13.77 %** and a best single of 8.87 %. The walk is **live, not
  inert**: it changes **exactly one decision** in the whole 2021–2025 window —
  entering-2023 solar **5,550 MW → 0** — with every other decision byte-identical
  to the pure disarm arm. The volume rule's own **4.91 %** under the shipped
  signal is identified as a **shipped-signal artifact** (solar exhausting *below*
  its cap freed shared queue budget wind cleared into; on the dual level wind
  already clears on merit in the 2022 step).
* **The attribution.** A **zone-flat, ORDC-dominated signal at hub grain**:
  `zonal_mean_range` and `hourly_cross_zone_spread` measured **exactly 0.0**,
  ~90 % of what dispersion the object carries is the ORDC adder, and the West
  build zone reads capture **0.494 / 0.805 / 0.927** on the shipped signal
  against **0.988 / 0.988 / 1.055** on the model's own duals.
* **What is ruled, and what is NOT.** Further pursuit **at this representation
  grain** is NOT THE ROUTE. **Nothing is armed** — the ERCOT entry screen keeps
  its shipped posture (`entry_lookahead_reprice` stays `ScenarioConfig` default
  `True`, verified in `scenarios.py` at the pin) — and **nothing is rejected**:
  both cells are **measured and rested unadopted**. **91.1 % of the miss stays
  OPEN and is published at full magnitude**, as is the dual level's adequacy cost
  (terminal RM 25.19 → 38.84 %, **+13.65 pp**) and the one band that worsens
  (solar Δ|err| **+0.1410**). Every addition band still FAILs in both arms.
* **Re-open conditions, exhaustive:** (1) a **NEW MEASURED DRIVER** admissible
  under rule 13 `[R-MEASURED]` — never a residual-fitted adder, capture factor or
  build target (rules 1 `[R-STRUCT]`, 21 `[R-DOF]`); (2) an **OWNER-CHARTERED
  REPRESENTATION-GRAIN CHANGE** — the caiso-223 class, *a program, not a lever*,
  earning its arming separately. **Neither route may be opened by re-running a
  lever at hub grain.**
* **Records:** `docs/DECISION-MAP-ercot-wind-entry-2026-08-31.md` (new) ·
  `docs/calibration-log/ercot.md` 2026-08-31 R-D entry · R-D ruling stamps
  appended to the **evidence strings only** of `entry_lookahead_reprice`
  (**cell K / fc O**) and `entry_margin_exhaustion` (**cell O / fc K**) in
  `docs/codebase-site/data/mechanism-matrix/ERCOT.js` — **no verdict letter
  changes**, `check_mechanism_matrix.py` exit 0 after the edit. Retires board v16
  owner-queue item 2.

---

**Ruling R-E — THE C3c SCARCITY PROGRAM: Q1 + Q2 CHARTERED AND CHAINED; Q3
UNOPENED AND UNRECOMMENDED.** On `docs/CHARTER-c3c-scarcity-program-2026-08-31.md`
(filed at nyiso-163 under the owner's *"Open c3c scarcity question"* ruling,
recorded in this log's 2026-08-31 entry above). **Q1 — the PJM phantom audit —
first**; **Q2 opens only on Q1 = REAL**; **Q3 (the probabilistic-RT-premium
class) is an ARCHITECTURE decision colliding with rules 4 `[R-DUALS]`, 8
`[R-8760]` and the no-MIP constraint, and is NOT opened and NOT recommended as a
calibration lane.** Executed by its own dispatched lanes, not here.

**🟢 STATE AT THIS PIN, RE-DERIVED RATHER THAN CARRIED: BOTH CHARTERED QUESTIONS
HAVE ALREADY REPORTED.** The dispatch that produced this record described Q1/Q2
as pending; at `d44446e0` they are landed findings:

* **Q1 = REAL** — `docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md` (pjm-164,
  #4456, zero solve). PJM's reserve-dual channel is **not** the ercot-214 phantom:
  in 2025 the model tail overlaps reality's tail **14 of 32** hours (0.44 of the
  model tail, 0.24 of the actual), **13** of them with a positive reserve dual,
  and reality was pricing reserve scarcity through the same mechanism on published
  DataMiner2 MCPs. 2023–24 have near-zero overlap but near-zero reserve
  involvement, so the mis-timing there is not the reserve channel's. Three honest
  caveats recorded, **none determination-level**. **Consequence: the
  determination-integrity branch does NOT open** — no PJM keeper is resting on a
  phantom channel, and no PJM card is owed.
* **Q2 = CONFIRM** — `docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`
  (nyiso-164, #4459, zero solve). The pre-registered kill gate **fires on both
  clauses**: reality's NYCA-tier reserve price never exceeds the concurrent LMP in
  **65/65** tail hours (median 0.54–0.65× LMP; a declared NYCA-wide pick-up covers
  only **8/65**), and the model carries **5.08 / 3.92 / 2.99 GW** of
  reserve-carrying thermal headroom (lower bound) against a 2,620 MW NYCA
  30-minute requirement, with the NYCA families at **zero dual and zero shortfall
  in all 26,280 hours**. **NYISO's C3c ledger is CONFIRMED on NYISO's own
  evidence rather than by inheritance**, the nyiso-163b inheritance question is
  settled, and the lane closes. This does **not** close C3c and does **not** move
  C3a-2025.
* **The reversal is reported, not buried** (the charter asked for it): nyiso-163b's
  timing overlap was not wrong, its *interpretation* was — split by tier, model and
  reality **agree at the locational tier** (both bind) and **agree at the NYCA
  tier** (neither is short), and NYCA is the tier that would have to be short for a
  system-wide price tail to be a reserve phenomenon.
* **The standing guard held in both lanes:** no SOM-published RCPF value
  ($25/$40/$750/$775) was proposed for change **in any form, including as a
  sensitivity** — the exact ercot-214 failure rules 13 `[R-MEASURED]` and 1
  `[R-STRUCT]` exist to prevent. **No matrix cell moves in either lane** (nothing
  tested, armed or adjudicated); **no holdout spend** (2023–2025 only).

---

**Ruling R-F — the nyiso-161 WINTER-FACE WAIVER CARD: DEFERRED, WITH A DATED
RE-SERVE TRIGGER.** **Neither option A (NOT-YET stands) nor option C (CALIBRATED)
is ruled.** The card **stays filed** and moves from *open-undecided* to **PARKED —
re-serve when the C3c program's Q1/Q2 report lands** (the R-E lane's finding is
the trigger; had Q1 returned PHANTOM the re-serve would have happened immediately
on that finding instead). **NYISO's determination stays NOT-YET on
{C3a-2025 −11.5 %, C3c} — unchanged, restated, not re-derived downward.**

**🟠 THE TRIGGER IS ALREADY SATISFIED AT THIS PIN.** Q1 (REAL) and Q2 (CONFIRM)
both landed before this record was written, and Q1 returned REAL rather than
PHANTOM, so the deferral's *branch* is the ordinary one and its *condition* is
met. **The card is therefore PARKED-AND-RE-SERVABLE — servable at the next
sitting, not waiting on a report.** Recording it any other way would leave a
later reader expecting a report that has already arrived. Nothing about the
deferral itself is re-opened by this: the owner deferred, and only the owner
un-defers.

Standing context the card must be read with, unchanged: **the AORR access route
is PERMANENTLY CLOSED by owner decision** (nyiso-163b, verbatim *"I'm not getting
new data access so just kill that request on 1"*), so the winter face of
C3a-2025 is **permanently unidentifiable from obtainable data** and nyiso-97 §5
re-open **condition 3 is WITHDRAWN** (conditions 1 and 2 remain live passive
watch items). **Option B (CALIBRATED-WITH-CAVEATS) is dominated** — marker
re-entry requires CALIBRATED, not CWC (Q5-W) — and **the precedent surface is not
NYISO-only**: CAISO's standing C3a residual has both lever routes CEII-blocked
(caiso-218/219) and would have an immediate claim on any access-blocked caveat
class. Records: `docs/calibration-log/nyiso.md`, continuing its 2026-08-31
entries.

---

**Ruling R-G — nyiso-160 / leg2: CLOSED BY ARCHIVE.** On
`docs/FINDING-nyiso-leg2-reverify-2026-08-31.md` (nyiso-162, #4431, executing
owner ruling R-C zero-solve on committed artifacts), the owner ruled **archive**.

The re-verification dissolved the question it was ordered to answer: **there is
NO candidate.** The leg2 session produced a **stop with cause at access**, not an
object — no pre-registration, no armed mechanism, no A/B pair, no control — and
its sole registered run, `2026-08-30-nyiso-160-tpaudit-replay`, is the keeper's
own recipe re-established at HEAD. Re-verified against the live keeper on four
independent legs: **zero solve-affecting levers differ**; **zero record-level
scorecard differences** across 60 scored records (the only difference anywhere is
the C6 attestation narrative string); **max |Δ| = 0 over 1,043,280 hourly data
rows**; `metrics.json` 58 of 60 leaves identical (the 2 are `run_id` and `label`).
The equality is **structural, not coincidental**. Promotion would have been a
formal no-op that *weakened* the keeper designation's evidentiary basis; archiving
costs nothing evidentially, since the touchpoint-prep verdict is durable in the
committed artifact, the two findings and the log entries.

**The parked session is already archived; this records the closure.** The
registered runs and the findings **stay on the record**. The promote-or-archive
item is retired **for good** — it is not re-servable, because the object it named
does not exist. Keeper `2026-08-30-nyiso-159-loss-surface` and its NOT-YET
determination are **untouched**; `audit_keepers.py --iso NYISO` PASS 0/0 at the
pin. **No matrix cell moves** (nothing was tested; `scuc_load_pocket_commitment`
stays **G** carrying the nyiso-160 access-stop on its evidence line). Records:
`docs/calibration-log/nyiso.md`, continuing its 2026-08-31 entries.

---

**Matrix (rule 26 `[R-MECH-MATRIX]`).** Duty (b): the only shard touched by this
sitting's records is `mechanism-matrix/ERCOT.js`, and only the **evidence strings**
of the two joint-wind cells — R-D adjudicates a *disposition*, not a verdict, so
**no cell letter moves in any shard**. Duty (c) does not fire: no `ScenarioConfig`
field was added. `check_mechanism_matrix.py` exit **0** after the edit.

**Gates at the pin, all five re-run with exit codes captured directly:**
`audit_keepers` **exit 0, PASS 0/0** · `check_registry_payload_parity` **exit 0,
58 runs / 93 bundle dirs / 0 known-unsynced** · `check_mechanism_matrix` **exit 0,
194 field + 49 row + 152 path** · `check_forecast_staleness` **exit 0, Δ = 1 of
10** · `check_bench_freshness` **exit 0, 20 parts, 0 STALE, 19 with engine
drift**.

## 2026-08-31 — C3c scarcity program, Q1+Q2 CLOSED: the cross-ISO synthesis both executing lanes deferred — Q1 REAL (twice, independently), Q2 CONFIRMED (twice, the second by a lane that first got it wrong), and the program's honest yield

**Cross-ISO entry, written under owner ruling R-E** (2026-08-31 director refresh
sitting, which chartered and chained Q1 and Q2 of
`docs/CHARTER-c3c-scarcity-program-2026-08-31.md` in one grant). **Zero solve
across every lane below; committed artifacts and published data only; no holdout
year touched by any of them.** Both executing lanes deliberately left this file
alone pending the other (`pjm-164`: *"Cross-ISO governance log deliberately
untouched (nyiso-164 possibly parallel)"*; `nyiso-164`: *"the cross-ISO synthesis
is a later, separate step"*). This is that step, written by the lane that ran both
legs and can therefore report the pair.

**(1) Three lanes, two questions, and a duplication worth recording.** Q1 and Q2
were each executed **twice, in parallel, by lanes that could not see each other**:

| question | first execution | replication | agree? |
|---|---|---|---|
| Q1 — is PJM's reserve dual REAL or the ercot-214 phantom? | **pjm-164** (`docs/FINDING-pjm164-c3c-phantom-audit-2026-09-01.md`) → **REAL** | **pjm-165** (`docs/FINDING-c3c-q1-pjm-phantom-audit-2026-08-31.md`), different construction → **REAL** | **yes** |
| Q2 — was NYISO reality NYCA-short in its tail hours? | **nyiso-164** (`docs/FINDING-nyiso164-c3c-product-level-2026-09-01.md`) → **CONFIRMED (not short)** | **nyiso-165** (`docs/FINDING-c3c-q2-nyiso-nyca-shortage-2026-08-31.md`) → first **NOT short-confirmed**, i.e. the OPPOSITE; **retracted** on re-derivation, reproducing nyiso-164 exactly | **yes, after correction** |

The duplication cost sessions and should not recur — a charter chaining two
questions in one grant needs one lane, or explicit lane assignment per question.
**It also bought something real:** Q1 now has two independent constructions
agreeing, and Q2 survived an adversarial attempt that reached the opposite answer
and had to be refuted on measurement. A CONFIRM that has withstood a genuine
contrary reading is stronger than one that was never challenged.

**(2) Q1 = REAL, and what it licenses.** PJM forms part of its scarcity tail
through in-LP energy/reserve co-optimization on a **published requirement** and a
**published demand curve**, timed to the real market's own posted scarcity
intervals, at a level **below what that market actually paid**. The four
independent legs (pjm-165 §2–§5): provenance an exact identity in 26,229
family-hours; ORDC shortfall identically zero in all 52,560 family-hours so the
dual is opportunity cost bounded below the published $300 penalty step (observed
max $187.90); overlap with PJM's posted penalty-step and shortage intervals at
**75–91× base rate, p ≤ 9.7e-11**; and the model under-pricing reality by 2.7–7×.
The ercot-214 failure mode — a channel manufacturing price the market does not
have — is structurally excluded, in the strong sense that the model never buys
reserve above what PJM's own curve says PJM would pay.

**Narrowed, by both lanes independently:** PJM's C3c is scored on the
**energy-only** dual (no settlement overlay in any year), and the reserve channel
is load-bearing in **2025 only** — 2023's tail forms with the family never binding
all year, 2024's with a maximum dual of $8.49. **Cite 2025, not 2023, as the
existence proof.** The charter's "PJM's C3c PASS rides reserve duals to $187.90"
is true of one year in three.

**(3) Q2 = CONFIRMED, and the inheritance question is settled — against the
charter's own suspicion.** Charter §3 suspected NYISO's C3c caveat had inherited a
CAISO/MISO diagnosis its own reserve timing did not support. Measured, it had not.
Split by tier: at the **locational** tier the model binds in reality's tail hours
and so does reality (agreement — and the genuine difference from CAISO, whose
model had slack in every family); at the **system (NYCA)** tier neither is short
(also agreement) — and NYCA is the tier that would have to be short for a
system-wide price tail to be a reserve phenomenon. **The residual above the
model's $90 locational adder is not a missing reserve product.** C3c stands as a
ledgered model-class limitation on NYISO's own evidence rather than by
inheritance. The decisive instrument is the **ceiling test** — a reserve holder's
opportunity cost is bounded by LMP, an RCPF shortage price is not; the NYCA-tier
price never exceeds the concurrent LMP in **0 of 65** tail hours, at a stable
~0.54–0.65×.

**(4) The one instrument lesson, and it is cross-ISO.** nyiso-165's false positive
came from two defects in the **committed** reference
`data/raw/_validation-source/actual_as_reserve_NYISO.parquet`, not from its own
arithmetic: (A) `process_nyiso_as.py::build_reference` **sums** `spin_10 +
nonsync_10 + op_30`, but NYISO's products are a **cumulative cascade** —
`spin_10 ≥ nonsync_10 ≥ op_30` in **100.0000 % of 289,344 rows** — so the sum
triple-counts one shadow price (exactly 3.0× in 28–79 % of priced hours); and (B)
it maps naive **prevailing** timestamps positionally onto the model's fixed
`Etc/GMT+5` 8760 clock, off by an hour in **65.2 % of the year**. **No keeper, no
scored result and no determination depends on it** (sole consumer:
`derive_nyiso_rcpf_overlay.py`, the co-opt-off comparator, disarmed in the
keeper) — it is a trap for diagnostic sessions, and it caught one. Filed for
repair; not repaired in a zero-solve measurement session.

**The generalizable rule this earns:** *a derived reserve-price reference is not a
substitute for the ISO's raw posting, and a nested reserve cascade must be
**maxed**, never summed.* Every ISO here posts nested reserve products
(PJM PR ⊇ SR; NYISO NYCA ⊃ East ⊃ SENY ⊃ NYC/LI; ISO-NE and MISO likewise), so
the same error is available in five other lanes. pjm-165 §6(b) records the
matching exposure on the PJM side — `_dt_ept` is prevailing while the model clock
is `Etc/GMT+5`, and an offset scan shows the model's series running ahead (best
lag −1 in 2023/2025); its overlaps are reported at the conservative lag 0 and are
a lower bound. **That PJM placement question is flagged and NOT diagnosed** — it
is the `pjm-162` "inputclock" family and belongs to a PJM lane.

**(5) The program's honest yield, against what the charter predicted.** The
charter said Q1+Q2 "will not, by themselves, close C3c anywhere; what they settle
is whether the C3c ledger is telling the truth about PJM and NYISO." That is
exactly what happened. **It is telling the truth about both** — PJM's PASS rests
on a real channel (narrower than claimed, and correctly cited to 2025), and
NYISO's caveat is correctly ledgered on its own evidence. **No determination, no
keeper, no marker, no caveat and no matrix cell moves anywhere as a result of this
program.** Q3 (the probabilistic-RT-premium model class) is untouched and remains
what charter §5 called it: an owner-level architecture decision colliding with
rules 4 `[R-DUALS]` and 8 `[R-8760]` and the no-MIP constraint, **not recommended
as a calibration lane**.

**(6) Guard compliance, restated because this is the lane where it matters.** No
fitted scarcity adder, no tuned VOLL, no raised published demand curve, no ORDC
offset swept against a residual. **No SOM- or Manual-11-published value
($25/$40/$750/$775; $300/$850/190 MW) was changed, proposed for change, or tested
as a sensitivity by any of the three lanes.** Every candidate was timing-checked
against reality before being priced, on the caiso-144 §D construction. Verdicts
stayed per-ISO (rule 25): the PJM finding entered no other shard, and the NYISO
finding entered none.

**(7) Matrix.** **No cell moves in any shard, across all three lanes.** Rule 26
duty (b) is not triggered by any of them — every leg is a measurement on committed
artifacts and published raw, and none tested, armed or adjudicated a mechanism;
duty (c) not triggered (no new `ScenarioConfig` field anywhere).
`energy_reserve_coopt` stays **K** in PJM and NYISO on their existing evidence.

**(8) Open, and whose it is.** (a) The `actual_as_reserve_NYISO.parquet` repair —
data lane or owner grant, spec in nyiso-165 §4. (b) The PJM prevailing-vs-standard
requirement placement — a PJM lane, spec in pjm-165 §6(b). (c) The **nyiso-161
winter-face waiver card** stays FILED AND UNRULED; under ruling R-F it was parked
on this report and the **DIRECTOR re-serves it**. What our result implies, stated
and not ruled: the corrected Q2 measurement **strengthens** the card's
characterisation of its summer face as "the ledgered C3c limitation seen in the
mean" — had nyiso-165's first reading stood, that half would have been a published
reserve-shortage quantity the model fails to bind, i.e. a defect contradicting the
card. It does not stand. This bears on the summer half only, is a statement about
characterisation rather than arithmetic, caveat budget or the standing rule, and
**rules nothing**.

---

## 2026-09-02 — xiso-7: the `prb_follower` DOF under-count is REAL IN THE GENERATOR and INERT ON EVERY KEEPER — and caiso-236's rule-26 deletion had left a red guard on `main`

**Cross-ISO entry. Zero solve, zero bundle, zero scoring, zero dashboard
registration; committed artifacts and source only; no holdout year touched; no
keeper changed and no CAISO artifact, config or number touched** (the CAISO lane
is rested at NOT-YET, caiso-201). Takes **option B** of the three items caiso-236
handed on (`FINDING-caiso236-dof-residual-ledger-audit-2026-09-02.md` §10.3).
Pre-registration
`results/calibration/PRECOMMIT-xiso7-prb-follower-dof-undercount-2026-09-02.md`
(pushed before any keeper artifact was opened), record
`results/calibration/FINDING-xiso7-prb-follower-dof-undercount-2026-09-02.md`,
instrument `scripts/probes/_xiso7_prb_follower_dof_probe.py`, transcript
`results/calibration/_xiso7_prb_follower_dof.json`.

**(1) The defect is real and structural.** `prb_follower` is the one coal
passthrough tier with **no sigmoid toggle of its own** — its gate is the
conjunction `coal_prb_passthrough_sigmoid AND coal_prb_passthrough_tiered`, and
when it fires it resolves a **second** four-parameter set alongside the baseload
prb curve. `build_dof_ledger`'s `n_scalars = 4 * len(sigmoids)` enumerated only the
five `coal_*_passthrough_sigmoid` toggles, so those four scalars were attested
**nowhere, for any ISO, ever**. An over-count (caiso-236's half) is the
conservative direction; an **under-count states fewer free parameters than the
solve consumes**, which is the disclosure failure rule 21 `[R-DOF]` exists to
prevent.

**(2) It fires on NO keeper of any ISO — and caiso-236 §10.3 is WITHDRAWN in
part.** That item named ERCOT and MISO as lanes that "under-count their own
residual". **Neither does, and neither can: both have
`coal_prb_passthrough_sigmoid = False`.** ERCOT's keeper runs
`coal_perplant_offer_curves` (ERCOT-144), whose harness disarms the sigmoids, so it
carries no `COAL_SIGMOID_DEFAULTS[ERCOT]` row at all; MISO's keeper arms no coal
sigmoid toggle whatsoever. The other four ISOs arm the full conjunction but have no
`(ISO,"prb_follower")` entry, so the follower falls back to the baseload curve and
consumes nothing. **The affected set is EMPTY.** The session's pre-registered P-1
(affected = {MISO}) is therefore a **MISS**, inherited from caiso-236's claim and
refuted by measurement.

**(3) The fix lands anyway, by the pre-registered rule.** A generator that will
attest every *future* keeper must count a set the solve demonstrably consumes.
`_prb_follower_engaged` applies the same resolve-or-nothing discipline as
`_coal_sigmoid_resolves`; `n_scalars` now counts `tiers`, and the row's **emission**
gates on `tiers` too (the follower can resolve for an ISO whose baseload prb pair
does not — under the old `if sigmoids:` that row vanished entirely). Verified to
move **no committed number**: all six keepers' generated ledgers are byte-identical
pre/post. `tests/scoring/test_build_dof_ledger_coal_sigmoids.py` (8 cases) pins
**both** gates — this generator's counting had no test at all, the caiso-236 fix
included — and its load-bearing case asserts the ledger's gate equals
`coal_sigmoid_params(cfg, "prb_follower")`, **the resolver the dispatch itself
calls**, so the attestation cannot drift from the solve in either direction.

**(4) OUT-OF-PRECOMMIT REPAIR — caiso-236 broke the keeper-replay guard on `main`.**
Found by the charter's own instruction to baseline failures at `origin/main`. The
charter's thirteen known-red tests are all in `tests/unit` / `tests/iso` /
`tests/regression`; **`tests/scoring` was not in that list and carried seven more**,
verified failing at clean `origin/main`. caiso-236 deleted `caiso_bidir_intertie`
under rule 26 and registered it in `scenarios._CACHE_KEY_RETIRED_FIELDS` — but not
in `replay_keeper._RULE26_DELETED_UNCONDITIONAL`, its parallel registry. Every
keeper meta of **all six ISOs** records the key, so `build_kwargs` hard-errored on
all of them. (caiso-236 §11's "ZERO new test failures" was measured over
`tests/unit` + `tests/iso` + `tests/regression`; `tests/scoring`, where the guard
lives, was not run.) **Fixed**, as the error message itself prescribes:
`"caiso_bidir_intertie": ("CAISO", (False, None))`. The registry's second element
may now be a **tuple of inert values** (`_rule26_inert`), which was necessary — all
six keepers record the key as **`None`**, the tri-state CLI's "never set", not
`False` — and is declared per field so it never becomes a blanket "`None` is always
safe" rule, which would be false for a deleted field whose default was the other
polarity. **The strictness is preserved:** a bundle recording `True` still
hard-errors as historical-record-only, and a census confirms none does.
`test_replay_keeper_strict::test_all_keeper_metas_build` is green again.

**(5) Two findings not predicted.** **U-1: PJM's committed ledger over-counts its
sigmoid row by 4 scalars** (12 vs 8 — it arms `prb` over a non-existent
`("PJM","prb")` pair). caiso-236 §7 recorded PJM as "none", which is true of the
*row* (bit and sub keep it alive) but blind to a partial over-count **inside** a
surviving row. **Handed to the PJM lane** on the same terms as option A; not
touched here (rule 25, and PJM's ledger is hand-augmented so a blind regeneration
would destroy rows). **U-2: ERCOT's dormant `coal_prb_follower_floor = 0.76` behind
the disarmed toggle is ALREADY ON RECORD** at xiso-3 (measured Δ = 0.0 with a
separating control, filed unadjudicated); the only increment is that it is also
**absent from the DOF ledger**, so re-arming one boolean would add an *undisclosed*
parameter — after this fix it would at least be counted. **A census may not
adjudicate** (rule 28(d)), and this one does not.

**(6) Gates.** `audit_keepers --iso <ISO>` **PASS 0/0 on all six ISOs**;
`check_mechanism_matrix.py` **exit 0** (its anchor warnings are pre-existing
line-number drift in `scenarios.py`, a file this session never touched); **no
mechanism-matrix cell moved** — no mechanism was proposed, tested or re-verdicted
and no `ScenarioConfig` field was added or removed. `tests/unit` fails exactly the
charter's baselined five, no new. `tests/scoring` **7 red at `origin/main` → 6**;
the remaining six are other lanes' or this container's `DATA PROFILE: caiso`
hydration (an ERCOT forecast-parity registry gap; `ERCOT:confirmed_retirements
[MISSING] clean partition unbuilt`; a NYISO marker expectation). **Net movement of
this session on the whole suite: one test fixed, none broken.**

**(7) Open, handed on.** PJM's 4-scalar over-count (U-1); options **A**
(NYISO/NEISO phantom rows) and **C** (O-1 forecast parity, #1373), untaken and left
exactly as caiso-236 left them; `coal_prb_follower_mustrun_max` is a free parameter
counted by no row (inert at its 25.0 default on all six keepers, so nothing is
currently misstated — deliberately not folded in, as classifying a tier-split
threshold is a judgement for a lane that may adjudicate its ISO); and the class
defect behind (4) — **`_CACHE_KEY_RETIRED_FIELDS` and
`replay_keeper._RULE26_DELETED_UNCONDITIONAL` are two hand-maintained registries of
the same fact with no test tying them together**, which is exactly what let a
rule-26 deletion pass CI and break the replay guard. A guard asserting every
retired field appearing in a committed keeper meta is declared in the replay
registry would close the class; not built here, as it wants an owner's view on
which registry is canonical.

## 2026-09-05 — OWNER DIRECTIVE, ALL LANES: the dashboard shows the KEEPER ALONE per ISO; ERCOT's two-config keeper is registered as ONE run (ercot-248)

Verbatim: *"Combine the ERCOT calibrated keeper config into one run for the run
explorer html page … then remove all the others that aren't that keeper so it's
just showing one run. Also prune all the other non keeper runs from there so just
show the keeper for each ISO for now."* Executed in session ercot-248
(`docs/calibration-log/ercot.md` ercot-248 has the full record). Per lane, with
`scripts/prune_iso_runs.py --force-uncite`: ERCOT 15 → keeper
`2026-09-05-ercot248-two-config-keeper`; CAISO 11 → `2026-09-05-caiso-246-b1-spot`;
PJM 4 → `2026-08-15-pjm-162-inputclock`; MISO 14 → `2026-09-05-miso-213-layering`;
NYISO 14 → `2026-09-05-nyiso-189-steam-identity`; NEISO 3 →
`2026-08-17-neiso-99-joint-p1`. No keeper, verdict, caveat, frontier declaration
or holdout posture moved; every pruned run's evidence stays in the FINDING
records, the per-ISO logs, the matrix cells and git history. Bundles a
regression-golden manifest or the parity allowlist names are retained on disk
(the prune script now honours both). Generalises the 2026-08-15 site-retention
directive to "keeper only, for now".

## 2026-09-06 — OWNER INSTRUCTION, ALL LANES: a held-out year renders AS A YEAR — rule 30(a)'s Validation Touchpoints panel is DELETED, not hidden (neiso-103)

**Owner instruction, verbatim:** *"the formatting on the html dashboard for holdout years shouldn't
be any different than the 3 training years, it should show the results in the report view on run
explorer and does not need a special designation."*

**Presentation only. ZERO LP. No solve, no score, no registration, no prune, no keeper change, no
marker or freeze change, no mechanism tested, no matrix cell verdict moved.** Genealogy:
`docs/governance/rule-history.md` §14 (§12 gained a forward pointer).

**The defect.** Rule 30 (2026-09-05) folded a touchpoint into its keeper to stop it publishing as a
SECOND CARD for a configuration the keeper already publishes — then mandated that the folded years
render as columns of a separate *Validation Touchpoints* panel. That fixed the two-cards defect and
introduced a smaller one of the same kind. `renderReport` drew its year set from `runYears()` — the
run's OWN solve years — so a folded year was **absent from every report table and chart** and
reachable only through four designations: the panel, a `Held out (rule 22)` optgroup in the year
dropdown, a ` — validation holdout` suffix on each entry, and a "*<year>* is a held-out year"
banner. Four labels for a year that is, by rule 30's own reasoning, the same recipe as the three
beside it.

**The fix.** The Report's year set is now `selectableYears()` — own ∪ folded, globally ascending —
so a folded year is an ordinary year column everywhere the page names a year. The panel, optgroup
split, tier suffix and banner are **DELETED, not hidden** (rule 26 `[R-DELETE]`: a dead render path
is a re-armable answer), with `TIER_LABEL`, `HOLDOUT_VERDICT`, `renderHoldoutPanel`,
`renderHoldoutPanelCombined`, `holdoutYearBanner` and `foldedHoldoutBlocks`
(`docs/codebase-site/js/backcast-runs.js` 2,655 → 2,450 lines, +64/−270). Folded payloads now load
EAGERLY at run load, because a report rendering every year at once cannot wait for a lazy fetch.

**Effect, measured by rendering all six ISO keeper pages in headless Chromium — not by reading the
diff:**

| ISO | report years before | report years after | dropdown | panel | banner |
|---|---|---|---|---|---|
| NEISO | 2023–2025 | **2020–2025** | flat, 0 optgroups | gone | gone |
| PJM | 2023–2025 | **2021–2025** | flat | gone | gone |
| ERCOT | 2023–2025 | **2022–2025** | flat | gone | gone |
| CAISO / MISO / NYISO | 2023–2025 | 2023–2025 (unchanged) | flat | n/a | n/a |

The three ISOs with no folded touchpoints are the negative control and are unchanged, footnote
included (they render none). The three `file://` console errors are blocked external CDN fetches
(d3, Google Fonts) that a control on unmodified `main` reproduces identically.

**Three guardrails held.** (a) **Rule 30(c) untouched — no determination moves**: no scorer path was
modified (`git diff` names no `.py` on the verdict path) and all three affected keepers re-score
`CALIBRATED` byte-identically. (b) **Rule 22's tier caveat SURVIVES** as a single footnote naming
the held-out years and restating 30(c) — dropping it entirely would have put the amendment in
conflict with rule 22 rather than with 30(a) alone. (c) **The amendment is written down**: CLAUDE.md
rule 30(a) now carries it with an explicit *do not restore the panel*, and
`tests/scoring/test_holdout_render_parity.py` (10 tests) pins it in CI.

**Unchanged and not re-litigated:** the fold itself, the `holdout.keeper` stamp,
`stamp_touchpoint_holdout.py`'s output (docstring only), the deep-link redirect, clause (b)'s
Calibration Status **holdout ladder** (per-year by design, a different surface), and clause (c).
Grants nothing about which years may be solved: markers, the holdout freeze
(`scope.tiers=['locked_test']`) and the registration marker gate are untouched.

**Test-quality note (neiso-102 lesson, applied to my own guard).** The new guard ships with negative
controls that mutate the source back toward the pre-amendment shape. The FIRST draft's control
**failed**, correctly: it mutated `const years = selectableYears();` with `str.replace(…, 1)`, which
hits the run loader (line 972), not `renderReport` (line 1171) — a control that would have proven
nothing. It now splices through `render_report_body`. A guard written the same day as the change it
protects is exactly where this failure mode lives.

## 2026-09-06 — neiso-107: the per-year ladder's spurious governance FAIL is fixed IN THE CALLER — 12 rows move, 0 determinations move, rule 1 (b)'s equality untouched

**Cross-ISO governance session, ZERO LP minutes.** Run as a governance session rather than a NEISO
calibration lane precisely because the fix changes MISO's published status part as well as NEISO's —
which is why neiso-106 escalated instead of patching (rule 25 `[R-ISO-SCOPE]`). Diagnosis, blast
radius and the proposed fix were already on record in
`results/calibration/FINDING-neiso106-per-year-ladder-governance-defect-2026-09-06.md`, now annotated
RESOLVED.

**The defect.** `build_status.build_years` — the rule 30(b) per-year ladder — scores each year in
isolation via `cv.determine(run_id, years=[year])`. That `years` subset propagated into the C6
governance gate, where rule 1 `[R-STRUCT]` condition (b) compares the `authorized_price_tuning`
declaration's `years_held` against the scored span as an **exact set**. For any run that legitimately
declares the channel, a one-year display subset made the comparison `{2023,2024,2025} != {2023}` and
returned FAIL. Result: **`NOT-YET` on EVERY year of two ISOs' `CALIBRATED` keepers**, on the exact
surface rule 30(b) designates for the holdout ladder.

**The fix is one operand, in the caller.** `calibration_verdict.determine_from_artifacts` now keeps
the run's own unfiltered scored span (`run_scorable_years`) and passes THAT to `score_governance`.
`years` still restricts which criterion-YEARS are scored; it no longer narrows the run-level question
rule 1 (b) asks about the run's configuration. The same line fixes the two partition-span callers
(`build_status` line 661, `audit_keepers` line 306), which had the identical category error under the
two-config keeper ruling.

**The equality is NOT relaxed to a subset test, deliberately.** A subset test would let a genuinely
per-year `years_held` pass rule 1 (b) — the exact failure mode the condition exists to catch. Both
halves are pinned by `tests/scoring/test_calibration_verdict.py::PerYearGovernanceScopeTests`
(5 tests, 3 subtests). All five FAIL against the pre-fix line, verified by reverting it; two of them
are the negative control — a declaration held on one of three scored years still FAILs on the full
span **and** on the single year it was held on, which is the hole a subset test would have opened.

**Measured effect, over all 14 registered runs on `main` at `b7ff89ca` (before/after snapshot of
every full-span and every per-year verdict — 37 per-year rows in total).**

- **Run-level determinations moved: 0.** Nothing that gates, and nothing rule 30(c) makes an ISO's
  determination, changes anywhere.
- **Per-year rows moved: 12**, in exactly the runs that declare the channel — MISO
  `miso-232-hourly-seam` (keeper), NEISO `neiso-105`, NEISO `neiso-106` (keeper), NEISO
  `neiso-106-touchpoints-2020`. Every one goes `NOT-YET [gov FAIL]` → its true per-year verdict:
  `CALIBRATED` on 2020–2024, `CALIBRATED-WITH-CAVEATS` on 2025 for a real reason
  (`unscored criteria: fuelmix, sysvol` — the 2025 EIA-923 completeness gate), never the spurious one.
  (Measured three times: first against `49773428` — 15 rows over 16 runs, MISO keeper `miso-230`;
  again after the rebase onto `dd78f46b`; and again on the salvage rebase onto `b7ff89ca`, where
  the MISO lane's own prunes/promotion had moved that ISO's keeper. Same defect, same repair,
  0 run-level moves all three times.)
- **Status parts rebuilt: `status/NEISO.js` and `status/MISO.js` only** — the two
  `build_status.py --check` named stale; the other four ISOs' parts were never touched, and the gate
  now passes for all six keepers.
- **`shared.js` carries NO change here.** The drift this session originally picked up (a lane had
  added `SPP` to the C3c threshold list without rebuilding the derived part) was repaired on `main`
  by the MISO lane at `2f9cd4d8` before this rebase. `build_status.py --iso` still rewrites the file
  unconditionally, but it is deterministic, so the rebuild is a byte-for-byte no-op and the file is
  left out of this commit.

**`RUBRIC_VERSION` stays 3.6.** No criterion band, tier, ledger route, caveat budget or determination
rule moved. The rubric was always right; the caller was asking it the wrong question, so there is no
new rubric to version. The module header records this in place, above `RUBRIC_VERSION`, as an
explicit NOT-A-RUBRIC-CHANGE entry so a later reader does not mistake the moved rows for a
loosened gate.

**Gates re-run green on the salvage rebase (`b7ff89ca`):** `build_status.py --check` (6/6),
`audit_keepers.py` (0 failures, 0 warnings, all six ISOs + holdout/marker/status checks),
`check_registry_payload_parity.py` (14 runs, 47 bundle dirs, 0 known-unsynced tolerated),
`tests/scoring/test_calibration_verdict.py` (151 passed, of which the 5 new
`PerYearGovernanceScopeTests` all FAIL against the pre-fix line). **Pre-existing and NOT mine:**
`tests/scoring/` has **16 failures on unmodified `main`** and the SAME 16 on this branch — verified
by capturing both failure sets and diffing them, identical, with the branch's pass count rising
1483 -> 1488 (the 5 new guards). They are the forecast-parity / FF-readiness / scenario-campaign
lanes (`test_forecast_parity`, `test_ff_readiness_battery`, `test_scenario_campaign_configs`,
`test_collate_scenario_campaign*`, `test_crossover_harness`, `test_gate_a_provenance`), all
untouched here; `main` being red on FR-22 parity is a standing condition this salvage neither
causes nor repairs.

**Nothing else moved.** No keeper, keeper shard, marker, holdout freeze, matrix shard or locked-test
year was touched; no run was registered or pruned; no ScenarioConfig field was added. NEISO's C3c
frontier stays closed pending its own owner charter, and the rule 29 `[R-SCREEN]` screen-year
amendment filed in PREREG-neiso106 §7 remains the owner's call, unamended here.

## 2026-09-13 — OWNER RULING: the PJM price-formation frontier (pjm-142) is RE-OPENED

**Owner, in session, verbatim: *"I don't care if it touched frontier do 2"*** — where option 2, put
to the owner alongside a coal-`phys_*` build and chosen over it, was *"re-open the pjm-142
price-formation frontier"*. Recorded here because re-opening an owner-declared-closed frontier is a
governance act and the closure is cited across several lanes.

**WHAT IS SUPERSEDED, and only for the PJM lane.** `FINDING-pjm138` §6's DO-NOT-REDO ("Do not
propose a reserve/scarcity mechanism for PJM") and `FINDING-pjm141` §5.3's terminal state ("a
DIAGNOSED, UNCLOSED structural limitation with no admissible in-model lever"). Nothing else in
either document moves; every other DO-NOT-REDO bullet in both stands, and no other ISO is touched
(rule 25 `[R-ISO-SCOPE]`).

**WHAT THE RULING DOES *NOT* LICENSE, stated at the gate.** (a) **No MIP** — the Stack mandate is
untouched and the arm taken is pure LP. (b) **No adder** — `ordc_scarcity_overlay` stays `G`; a
post-solve administrative scarcity overlay is refused by rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`
and the owner did not waive them. The frontier being open changes which *structural* mechanisms may
be proposed, not which *fitted* ones may be armed.

**WHAT WAS DONE UNDER IT.** Lane `pjm-h3` armed **one** field, `pjm_reserve_pergen_sync` (the
Manual 11 §4.2/§4.3.3 SYNCHRONIZED reserve sub-product split: measured RTO `sr_req_mw` + nested MAD
`mad_sr_req_mw` balance families on the published two-step ORDC rows, a per-pool SYNC/NON-SYNC
column split, and P0-derived online scoping of the SYNC caps). **Zero parameters fitted to the price
residual.** Prerequisites `energy_reserve_coopt` + `pjm_reserve_pergen` were already in the keeper.
Pre-registration: `docs/PRECOMMIT-pjm-h3-reserve-sync-2026-09-13.md`, pushed at
`ed6bb0996d2685884d1f05eb105c3bef4dea138c` before any solve.

**THE RULE-28(a) NEW EVIDENCE, since the standing verdict on that field is an owner closure on
MERIT rather than a structural refutation** (*"SYNC product split owner-closed on merit for PJM
($0-10 vs $75-200 need)"*): the $75-200 comparator was pjm-84/85's afternoon scarcity band. The
target measured since is an order of magnitude smaller — pjm-141 §5.1 puts the peak under-pricing at
**−$7.62 / −$11.37 / −$22.19** — and PJM's own published MAD synchronized-reserve price at h16-18 is
**$3.89 / $8.19 / $9.49**, i.e. **43 % / 72 % / 43 %** of it. A mechanism worth $0-10 is a rounding
term against $75-200 and a major fraction against $7.62-$22.19; the closure's own arithmetic inverts
on the corrected target.

**THE MEASUREMENT THAT MOTIVATES IT** (zero LP, committed sidecars + `data/raw/PJM-AS/`): the
model's reserve dual is non-zero in **0.02 / 0.07 / 0.02 %** of hours in 2020/2021/2022 against
PJM's published **45.7 / 60.3 / 61.3 %**, at an annual mean of **$0.194 / $0.005 / $0.003** against
**$1.71 / $3.89 / $9.19**. PJM's price is peaked **3.0×-22.0×** (h16-18 ÷ h01-04) in all six years —
shape-only and tight-hours-only, which is exactly what pjm-138 §7 lead 1 said a successor must be.

**WHAT IS NOT CLAIMED.** The reserve credit does not touch the **overnight** half of the amplitude
deficit (pjm-141 §5.1 point 3, pjm-138 §7 lead 2, both re-confirmed): PJM's overnight reserve price
is small and the model's is zero. The overnight **+$6.82 / +$5.78 / +$3.40** over-pricing remains an
open structural limitation, and pjm-142's measured slope (2.88 / 3.37 / 2.57 GW per $1/MWh) says
closing it needs **9-20 GW** of stack movement that no queued lever supplies.

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

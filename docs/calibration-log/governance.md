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

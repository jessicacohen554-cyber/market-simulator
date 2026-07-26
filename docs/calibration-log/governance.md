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

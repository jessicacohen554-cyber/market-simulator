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

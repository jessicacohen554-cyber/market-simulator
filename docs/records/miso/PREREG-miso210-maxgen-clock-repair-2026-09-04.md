# PREREG miso-210 — THE MAX-GEN CLOCK REPAIR: one hour late in two armed keeper mechanisms, repaired as structure (rule 1), adjudicated as a single-delta A/B against a bit-identical control (2026-09-04)

**Pushed BLIND** before any window is re-placed, before the deriver is re-run on
the corrected clock, and before either leg is solved. Keeper at open:
`2026-09-03-miso-202-unitclip` (bundle `miso202_unitclip_B`), determination
NOT-YET on {C3a-2025 −12.3845} alone, C3c the single ledgered caveat, C6
attested (ledger 41/2). Rule 22: 2023–2025 only. HEAD at open: `8f5cb32c`
(miso-208 #4705 and miso-209 merged; the branch is AT `origin/main`, zero
drift). Measured before this file was written: `git diff --stat 1aab8d41 HEAD`
over `src/`, the runners, the scorer and `data/raw/campd-unit-outages*` /
`data/raw/maxgen-events` is **EMPTY** — the keeper's solve path is byte-identical
at HEAD; installed highspy 1.14.0 / numpy 2.4.6 / scipy 1.17.1 / pandas 3.0.3 /
pyarrow 24.0.0 / pydantic 2.13.4 / Python 3.11.15 match the keeper's
`environment` block exactly.

---

## 1. The defect, as settled (not re-derived here)

miso-208 §0 item 2: the model clock is **CST hour-beginning** (two r = 1.000
witnesses — keeper demand vs EIA-930 D; the INDIANA.HUB LMP HE file vs the
committed zonal `rt`). MISO market time is EST, and the registry's endpoints
are declared in EST (`data/raw/maxgen-events/README.md`, unchanged by this
session). `maxgen_events.MODEL_TZ_BY_ISO["MISO"] = "Etc/GMT+5"` therefore
converts every `start_utc`/`end_utc` onto **EST**, and both armed consumers
place their windows **one hour LATE on the model clock**:

* `maxgen_emergency_tier_pricing` (K) — slack repriced to the $500 / $1,000
  tier floors in Warning+ windows (`emergency_tier_slack_cost`);
* `unit_outage_maxgen_events` (K) — the M-2 revealed derates
  (`campd-unit-outages-maxgen-unitroute-MISO.csv`, 2,174 rows, 5 blocks),
  whose deriver (`derive_campd_maxgen_outages.MODEL_TZ = "Etc/GMT+5"`) emits
  `window_start`/`window_end` on the same EST clock and the loader applies
  them on the model clock through `outage_hour_mask`.

A mechanism firing in the wrong hours is a rule-1 / rule-17 `[R-FLOOR-WINDOW]`
defect whatever it does to the fit. That is the whole justification; **no
number below is**.

## 2. The repair — P-4, the ONE-MECHANISM statement, written first

This changes **WHERE** two armed mechanisms fire, never **WHAT** they do. **No
new `ScenarioConfig` field, no new mechanism, no matrix row (rule 28c does not
fire).** The delta is:

1. `src/market_sim/data/maxgen_events.py`: `MODEL_TZ_BY_ISO["MISO"]`
   `"Etc/GMT+5"` → **`"Etc/GMT+6"`** (UTC−6 = CST, the measured model clock).
   The floor/ceil, half-open, region-crosswalk and `min` semantics are
   untouched.
2. `scripts/data/derive_campd_maxgen_outages.py`: `MODEL_TZ` →
   `"Etc/GMT+6"` so the emitted `window_start`/`window_end` are on the model
   clock, **plus the DA hub LMP record (`he01`–`he24`, hour-ending EST) shifted
   by the SAME −1 h onto the model clock** so guard 2's in-merit certificate
   compares the same physical hours as before. The frozen guards ($150, 2 h,
   ±45 d, best-hour credit, disjointness, F3) are untouched (rule 23: this is
   a deriver clock repair, not a re-derivation against a residual; the commit
   cites the miso-208 witnesses, not a residual).
3. Both MISO M-2 extracts re-derived by that script
   (`campd-unit-outages-maxgen-MISO.csv` and the `-unitroute-` companion the
   keeper reads) — the ONLY data change.
4. The registry (`data/raw/maxgen-events/miso/miso.csv`, its README, the
   schema, the curation parser) is **unchanged**: the endpoints are correctly
   declared in EST; only the model-clock conversion was wrong.

**What the repair does NOT touch, named:** the CAMPD per-unit gross grid is on
plant-local standard time (the deriver's own caveat: "≤ 1 h skew … made robust
by the best-event-hour credit"). On the EST placement the skew sat on MISO's
CST-majority plants; on the corrected placement it sits on the EST minority
(IN, MI, KY). Not a second delta; recorded, not repaired.

Both legs solve the keeper's committed recipe via `--replay-bundle`
(`miso202_unitclip_B`), so **S-1 is restated for a code+data delta**: the two
legs' `scenario_config` blocks must be IDENTICAL (zero field diffs); the legs
differ in exactly the repair commit(s) (recorded `git.sha`) and the extract
bytes (recorded sha256 of the file each leg read).

## 3. Phase 0 — zero-solve, predicted before it is computed

### P-1 — the exact hour sets (arithmetic, stated now; the keeper's values in them predicted)

On the corrected clock every window moves ONE HOUR EARLIER: each block **gains
its declared first hour** (the hour the EST placement started too late to
cover) and **loses the hour after its declared end** (which the EST placement
wrongly covered). Model hours, CST hour-beginning:

| block (EST declared) | armed today (CST, wrong) | corrected (CST) | gained | lost |
|---|---|---|---|---|
| 2023-08-24 12:00→24:00 step2 ($1,000) + M-2 | Aug 24 12:00–24:00 | **Aug 24 11:00–23:00** | Aug 24 11:00 | Aug 24 23:00 |
| 2024-08-26 13:00→20:00 warning ($500) + M-2 | Aug 26 13:00–20:00 | **Aug 26 12:00–19:00** | Aug 26 12:00 | Aug 26 19:00 |
| 2025-06-23 step1 + 06-24 warning, midwest ($500) + M-2 (merged) | Jun 23 00:00–Jun 25 00:00 | **Jun 22 23:00–Jun 24 23:00** | Jun 22 23:00 | Jun 24 23:00 |
| 2025-07-24 advisory (M-2 only) | Jul 24 00:00–Jul 25 00:00 | **Jul 23 23:00–Jul 24 23:00** | Jul 23 23:00 | Jul 24 23:00 |
| 2025-07-28 12:00→07-30 00:00 advisory+alert+warning (M-2 merged; tier = warning Jul 29 only) | Jul 28 12:00–Jul 30 00:00 (tier Jul 29 00–24) | **Jul 28 11:00–Jul 29 23:00** (tier Jul 28 23:00–Jul 29 23:00) | Jul 28 11:00 (tier: Jul 28 23:00) | Jul 29 23:00 |

Predictions on the KEEPER's own hourly (control) values in those hours:

* **P-1a (2023).** Keeper INDIANA-carry load-weighted price at the gained hour
  (Aug 24 11:00) EXCEEDS the lost hour (23:00) — daytime vs night — and idle
  thermal at 11:00 is BELOW 23:00. Slack 0 in both. Confidence 0.8 / 0.8 / 0.8.
* **P-1b (2024).** The window's 19.4 GWh of $500-floor slack is carried by its
  MIDDLE hours; the LOST hour (19:00 CST = 20:00 EST, the last declared hour)
  carries **≤ 25 %** of it (0.65). The GAINED hour (12:00 CST) has slack 0 and
  a keeper price **< $500** in the control (0.7) — so on the corrected clock it
  does not print the floor.
* **P-1c (2025).** All gained/lost hours are 23:00 night hours except Jul 28
  11:00 (M-2 only, no tier): slack 0 and idle thermal > 5 GW in every one of
  them (0.9).

### P-2 — the M-2 extract re-derived on the corrected clock (scratchpad first)

* **P-2a (certificate invariance — a soundness line, VOID if it fails).** With
  the LMP record shifted with the registry, guard 2's `n_cert` per registry
  row is **IDENTICAL** to today's (same physical hours), the same 5 windows
  qualify, the same 5 blocks form. A change means the LMP shift is wrong
  (0.9).
* **P-2b.** Per block, row count within **±3 %** and total derate MW within
  **±5 %** of the committed extract (10,171 / 10,311 / 3,066 / 10,902 / 7,424
  MW; 474 / 467 / 295 / 484 / 454 rows) — only the best-window-hour credit can
  move, and by ≤ 1 h at a window edge (0.7). Direction NOT predicted (the
  credit can go either way). Grand total 41,874 MW within [39.8, 44.0] GW.
* **P-2c.** F3 engages on the same blocks as today (currently none) (0.8);
  guard 4 disjointness asserts clean (0.9).

### P-3 — static reach on the corrected Warning+ hours (does the 2025 tier floor become reachable?)

**Predict NO.** min over the corrected 2025 Warning+ hours of the keeper's idle
thermal ≥ **2.0 GW** (today 2.18 GW on the EST placement; the corrected set
swaps one 23:00 for another 23:00 in each block) and the keeper's
demand-minus-capability never exceeds 0 there (0.85). **This RE-SCORES
miso-208's "tier floor silent in every 2025 Warning+ hour" as a claim on the
corrected clock, and it MAY FAIL** — if it fails, the finding says so first.

### P-4 — stated in §2.

### Placement verification (V-KEY-LMP), before any solve

The corrected placement is checked against the LMP file's own HE stamps, not
against the registry's arithmetic: the committed zonal `rt` (model clock) must
equal the INDIANA.HUB `_rt` HE record placed at EST_TO_MODEL = −1 at r = 1.000
over each window's days (re-establishing miso-208's key), and the corrected
window hours must be exactly the model hours whose EST HE labels lie inside the
declared window. Hard void if the key does not reproduce.

## 4. The A/B — gates, frozen, with the sign and the mechanism beside each

Control `miso210_control_A` = the keeper recipe re-solved at HEAD (`8f5cb32c`,
old constant, old extract), all three years in ONE invocation, years
sequential (rules 12/16). Arm `miso210_clock_B` = the same recipe at the repair
commit with the re-derived extract. Scorer `_miso210_ab_gates.py`, the
miso-202 ten-gate scorer re-pointed, with S-1/S-2/S-3 restated for a
code+data delta and pushed with this file.

| gate | rule | prediction (conf.) | mechanism |
|---|---|---|---|
| **S-0** control integrity | bit-identical to the keeper's 9 committed sidecars, `max_abs_diff` 0.0; drift DISCLOSED, then STOP and diagnose before the arm | PASS (0.9) | zero solve-path drift measured at open; environment identical |
| **S-1** single delta | `scenario_config` IDENTICAL; legs differ by the repair commit + the extract bytes only | PASS by construction | no field exists |
| **S-2** placement liveness | the arm's tier-cost array differs from the control's in EXACTLY the gained+lost hours of each Warning+ block (per zone-in-region), and the M-2 derate arrays' non-unity hour set is the control's shifted −1 h — off the production loaders, no solve | PASS (0.9) | a shift by one constant can move nothing else |
| **S-3** certificate invariance | P-2a; HARD VOID | PASS (0.9) | same physical hours both sides |
| **K-1** C1 band ±8.00 TWh | no band exit; **bound**: the whole delta is ≤ Σ_blocks derate MW × 2 h ≈ 0.02 / 0.02 / 0.04 TWh (2023/24/25) plus ≤ 0.02 TWh of 2024 slack-to-dispatch conversion, against a tightest headroom of 0.512 (ST_GAS-2024) | SILENT (0.95); max class-year move ≤ 0.05 TWh (0.9) | one hour of derate per block edge |
| **K-2** C3b | no PASS→FAIL; \|Δ\| < 0.002 every year | SILENT (0.85) | ≤ 6 hours per year re-placed |
| **K-3** D-4 | zero NEW off-window binding (neither maxgen mechanism carries a D4 row by construction; floors could move only at block edges) | SILENT (0.75) | availability edge moves ≤ 1 h |
| **K-4** D-1 | no PASS→FAIL | SILENT (0.85) | as K-2 |
| **K-5** status flips | zero PASS→non-PASS | SILENT (0.8) | as K-2 |
| **K-6** DOF | attestation REAL on both legs (generated by the gen_miso202 pattern; refused if empty); **no new ledger entry** — the arm adds no parameter, it corrects a constant to a measured clock (two r = 1.000 witnesses) | PASS, n_entries 41 → 41, n_residual 2 | — |

**C3a — REPORTED at full magnitude, NEVER a gate, NEVER the justification (rule 1).** Signs pre-registered against each year's own hours:

* **2023:** Δ ∈ [−0.05, +0.10] pp (0.7). Mechanism: 10.2 GW of derate moves
  from Aug 24 23:00 (night) to 11:00 (late morning); the $1,000 floor did not
  print at either hour (P-1a), so the only channel is the derate edge.
* **2024:** Δ **UP (less negative)**, ∈ [0, +1.5] pp (0.65). Mechanism: the
  slack the keeper carried at $500 in the LOST hour (19:00 CST) is re-priced
  to the marginal supply above $500 or to VOLL; the GAINED hour (12:00) does
  not print (P-1b). This is the one place the repair can move a scored price
  by more than noise — and if it moves C3a-2024 toward actual, that is **NOT
  evidence for the repair**; it would be reported identically had it moved
  away.
* **2025:** Δ ∈ [−0.05, +0.10] pp (0.75). Mechanism: the tier windows swap one
  23:00 for another (P-1c); the M-2 edge at Jul 28 11:00 adds 7.4 GW of derate
  to one morning hour. The 15-hour tail (13/15 in h18–h21) is untouched by
  every edge. **C3a-2025 stays NOT-YET.**

**C8** (ST_GAS forced share): |Δ| < 0.0005 every year (0.85).

**Verdict predicted:** KILLS SILENT and the arm MOVED values (through 2024's
lost-hour slack) → keeper candidate on its own gates (0.65); INERT (no scored
value beyond epsilon — if 19:00 CST carried no slack and no edge converts)
(0.30); a kill fires (0.05). **Promotion rule, as miso-202:** structural
repair, single delta, all gates passing → PROMOTE; a fired kill is an OWNER
DECISION under the standing structural-integrity bar with every regression
disclosed side by side; the scorer never promotes on that branch. An INERT
arm is STILL promoted — a wrong clock is wrong at any magnitude, and the
repair is justified as a defect repair, not by its size (miso-202 §6a).

## 5. Reported against the promotion, in advance

* If S-0 drifts, nothing is scored until the drift is explained; a partial
  bundle is deleted, never reused (miso-202 §6g).
* The 2024 C3a move, whichever way it lands, is disclosed with the slack
  MWh in the gained/lost hours beside it.
* The CAMPD plant-local skew (§2) is named as the residual clock question
  for the deriver — cross-ISO in principle (every ISO's CAMPD grid is
  plant-local), so for the director, not this lane.
* miso-208's `_miso208_find_the_supply.py::window_masks` applies its own
  EST_TO_MODEL = −1 on top of the loader; after the repair a re-run would
  double-shift. The probe is a committed record and is annotated, not
  re-run.

## 6. Governance

Rule 15: BOTH runs registered (dashboard, run payloads over `git push`),
`legitimacy_diagnostics --json-out` for both. Rule 28(b): stamp
`maxgen_emergency_tier_pricing` and the `unit_outage_short_windows` row
(carrying `unit_outage_maxgen_events`) in MISO's shard, §5.4 stamp. Rule
28(c): no field. Rule 25: MISO's shard only. Rule 27: `maxgen_events.py` and
the deriver edited locally with the Edit tool, never rewritten whole;
blob-verify after push. Rule 22: 2023–2025 only. Rule 13: the corrected clock
is a measured property of the model's own hour index. If promoted:
`keepers/MISO.json` + `build_status.py --iso MISO` + `audit_keepers --iso MISO`.

Next shorthand after this session: **miso-211**.

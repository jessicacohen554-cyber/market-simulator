# FINDING — ercot-243 (2026-08-30): the event-exit-hour census KILLS the release-guard exit-condition lane — the 2024/2025 population is h3068-2024 ALONE (K-1), 2025 carries ZERO adaptive floors so it cannot contribute, the model's exit timing is RIGHT at 11 of the 12 real event collapses, and the trailing-edge structural candidate would surrender one correctly-held hour (K-3: h2828 release-WRONG) — no repair is identifiable against a population of one, and the lane STOPS with no threshold touched

**Session ercot-243, branch `claude/ercot-243-release-exit-r7owkv`.
ZERO-SOLVE — every number read from the FORWARD keeper's committed
2024/2025 sidecars (`results/calibration/ercot234_eastex_identity`), the
committed actuals, the EIA-930 wide extract and the measured
ORDC/reserves series.** Precommit
`docs/PRECOMMIT-ercot243-release-exit-phase0-2026-08-30.md` pushed +
blob-verified (045cd014) BEFORE any measurement; V-0 exact (model 798.20 /
actual 110.41 / floor 523.12, the p_hat × VOLL identity closing to $0.01).
Probe `scripts/probes/ercot243_release_exit_phase0.py` →
`results/calibration/ercot243_release_exit_phase0.json` (committed). No
lever, no solve, no gate change, no matrix verdict moved; the two-config
keeper untouched. One implementation repair, construction unchanged: the
lag-correlation alignment assert runs on finite rows (the EIA-930 2025
extract carries NaN Demand hours); lag-0 asserted in both years
(corr 0.9996 / 0.9998).

## 0. Verdict in five lines

1. **K-1 FIRES: the census population is {h3068-2024} alone.** Across all
   17,520 forward-span hours, exactly ONE hour carries the full exit-lag
   signature (A1–A3 + M1–M6) — h3068 itself, reproduced with every leg the
   ercot-239 attribution named (floor $523.12 held, families at the
   $416.67 step, NonSpin/ORDC-total short, storage 0 → 1,065.7 MW re-timed,
   net-load gap +334 MW, measured RTORPA $8.95 / RTORDPA $3.43).
2. **2025 cannot contribute, structurally:** the forward keeper's 2025
   adaptive sidecar carries ZERO floored window hours (the ercot-221
   self-extinction persists in the current config), so the guard has
   nothing to hold and no exit edge to lag. 2024: 563 floored / 5
   guard-released window hours — the ercot-223 breadth unchanged.
3. **The model's exit timing is otherwise RIGHT:** of the 12 actual
   first-collapse hours after real events (actual ≥ $500 within 6 h, first
   hour < $200) that reached the model-side classification, the model had
   ALREADY released at 11 (stratum S3). S1 = S2 = 0 — no extended holds, no
   non-guard exit lags. h3068 is a genuine singleton, not the visible tip
   of a family.
4. **K-3 ALSO FIRES: the trailing-edge structural candidate does not
   separate.** The trailing set (floored window hours after the day's
   first guard release) has exactly two members, both 2024 hod-20:
   h3068 (release-RIGHT, actual $110.41) and h2828 (Apr 28, release-WRONG:
   actual $238.04 was still elevated — releasing it surrenders a
   correctly-held hour). Honest nuance, reported not scored: at h2828 the
   $285.52 floor was INFRAMARGINAL — storage discharged 1,195.6 MW through
   it — so a release there is plausibly near-inert; but the declared T2 bar
   is mechanical and zero, and K-1 stops the lane regardless.
5. **Disposition per the precommit's kill rule:** no Phase-1 precommit, no
   A/B, no threshold search — the A/B license is NOT spent. The exit-edge
   object remains a named, fully-attributed member of the forward span's
   ledgered C3c family (2024 22/53), carried at full magnitude. A
   threshold-form re-identification is additionally NOT measurable
   zero-solve (the pass-1 settle series is not a committed artifact —
   verified; h3068's $675 exists only in the ercot-223 record), and any
   pass-1-settle instrumentation is a future owner charter, not this
   lane's.

## 1. The census record (all rows in the committed JSON)

| measure | 2024 | 2025 |
|---|---|---|
| floored window hours (floor ≥ $10) | 563 | **0** |
| guard-released window hours | 5 | 0 |
| census population (A1–A3 + M1–M6) | **1 (h3068)** | 0 |
| S1 extended holds | 0 | 0 |
| S2 non-guard exit lags | 0 | 0 |
| S3 model already released at collapse | 11 (both years pooled) | — |
| trailing set | h2828 (WRONG), h3068 (RIGHT) | — |

Prior check: declared 1–3 (point 2), observed 1 — inside the prior, no
order-of-magnitude breach; the signature construction is neither looser
nor tighter than the object.

## 2. What the kill establishes for the queue

* **The h3068 repair direction is CLOSED on current evidence.** Per
  `[R-FLOOR-WINDOW]` and the precommit, no exit-condition change — neither
  the zero-constant trailing-edge form nor any re-identified threshold —
  may be identified against a single hour. The one-hour-late event exit is
  real, fully attributed (ercot-239 r3), and NOT repairable without either
  (a) new exit-lag hours arising in future data, or (b) a pass-1-settle
  instrumentation charter that would let a threshold form be identified
  against a measured margin distribution rather than one anecdote.
* **The guard itself is unblemished by this census:** its 5 realized-spike
  releases in 2024 stand, 2025 is untouched by construction, and the only
  other trailing-hold (h2828) held a floor the dispatch cleared straight
  through. The census found no case where the guard's HOLD manufactured a
  phantom event tail beyond h3068.
* **DO-NOT-REDO entry:** the release-guard EXIT condition (trailing-edge
  structural form AND threshold re-identification form) is adjudicated
  KILLED-AT-CENSUS 2026-08-30; do not re-open without new evidence — a new
  exit-lag hour in future-year data, or an owner instrumentation charter.

## 3. Owner-visible flags (not executed, per charter)

1. **The 2024/2025 all-resource SCED conduct corpus intake**
   (PRECOMMIT-ercot242 §6) remains the blocker on the forward-regime SCED
   conduct identification; SCED-CT is re-fetch-only and CT-only (corpus
   README read; the data is not "missing", it is unfetched). Unchartered —
   flagged only.
2. If the owner wants the h3068 singleton repaired despite the census, the
   admissible route is the instrumentation charter above (persist the
   pass-1 settle series as a sidecar column in a future solve lane, then
   identify the exit threshold against the measured margin distribution) —
   its cost is one sidecar column, its benefit one hour of one year at
   current evidence.

## 4. Hygiene

Zero-solve; years read ⊂ {2024, 2025}; no `--holdout-authorized`, freeze
untouched; ERCOT surfaces only; no run produced (rule 15 not triggered —
nothing to register); matrix: evidence NOTE appended to the
`ercot_storage_adaptive_expectation` cell (verdict K unchanged) in the
ERCOT shard, per the precommit's §5 permission; calibration-log entry
ercot-243 added; every deliverable pushed off the fresh-main base with
blob verification on ≥300-line files; no workflows, no CI solves; the
ercot-241/242 committed measurements were read, never re-run.

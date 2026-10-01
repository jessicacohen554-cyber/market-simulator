# ADDENDUM miso-233 — the 2023 SCREEN CLEARS ALL FOUR PRE-REGISTERED GATES. Full span launched.

Written when the screen was scored and the span launched, **before any span year's bundle
exists**. Bars are the ones fixed in `PRECOMMIT-miso233-spp-hourly-seam-2026-09-07.md` §4
and pushed at `79f73030`; the scorer `scripts/probes/_miso233_screen_gates.py` was written
and pushed **while the screen LP ran**, before the arm's bundle was opened. Machine record:
`results/calibration/_miso233_screen_gates.json`.

**Arm:** the miso-232 keeper recipe with the single field
`miso_seam_neighbour_hourly_spp=true`, 2023 only, via `replay_keeper --set`. Verified from
the bundle's own `run_config.json`: the flag AND its parent both read `true`.

## The gates

| gate | bar (fixed ex ante) | measured | verdict |
|---|---|---|---|
| **G-1 confinement** | slack ≤ keeper's 0.0000 TWh; dump = 0; wind/solar/nuclear/hydro each within 0.05 TWh | slack **0.0000**, dump **0.0000**, all four must-take classes **0.000 TWh** moved | **PASS** |
| **G-2 footprint scale** | \|Δ annual gross imports\| ≤ 1.5 TWh | 44.763 → **44.166 TWh**, Δ **−0.597** | **PASS** |
| **G-3 direction** | `corr(imports, own hub price)` may not RISE more than +0.05 | +0.1754 → **+0.0712**, change **−0.1042** | **PASS** |
| **G-4 no collateral flip** | zero PASS→FAIL on C1/C2/C3a/C3b/C6, real scorer in memory vs the keeper's committed verdict | **0 flips** | **PASS** |

`scripts/screen_collateral_gate.py --bundle _miso233_spp_screen --keeper-run-id
2026-09-06-miso-232-hourly-seam`. Nothing was registered; the bench is the committed parts.

## What the screen showed — reported, and NONE of it was gated

**The target residual moved, and it is recorded here as an observation, not as a gate.**
The PRECOMMIT put the decile slope under `reported_not_gated` precisely so that this number
could not select the arm:

- **2023 price-decile slope d1−d10 on the measured Indiana hub price: +138.7 → +402.4 MW**,
  against a measured **+1,303**. The static phase-0 instrument predicted the SPP seam's own
  slope would move +243 MW; the LP delivered +264 MW on the system total — the same
  direction and order of magnitude the pre-solve arithmetic implied, which is the only
  thing a screen is entitled to conclude.
- `corr(imports, measured price)` −0.0823 → **−0.1095** against a measured **−0.136**.
- Collateral, non-gate: **6 of 8 scored C1 cells move toward actual** — CT_PEAKER
  −3.292 → **−3.052**, COAL_PRB −1.995 → −1.768, COAL_BIT −3.063 → −2.952, CC_CHP
  −2.038 → −1.991 — and **2 away**: CC_REGULAR −6.313 → **−6.445** and ST_GAS
  +0.290 → +0.409. C2 gas −14.07 → −13.80 and coal −5.59 → −5.25, both toward. C3a
  +2.05 → **+2.12 %** (away, far inside ±10 %).
- **The CC_REGULAR-2023 give-back that miso-232 opened as future work gets slightly WORSE
  here** (−6.313 → −6.445). Named now, before the span, so the span's write-up cannot
  present it as a new discovery.

## What clearing the screen does and does not authorize

Rule 29 `[R-SCREEN]`: **a screen may kill an arm and may never promote one.** Clearing these
four gates authorizes exactly one thing — spending the remaining two years as one
`--year 2023 2024 2025` invocation and one bundle (rule 16). It is not a determination, and
the span is scored on `scripts/calibration_verdict.py` against the miso-227 promotion rule
(promote on CALIBRATED / CALIBRATED-WITH-CAVEATS; on a load-bearing NOT-YET, report and
escalate rather than decertify).

**Every non-claim in PRECOMMIT §6 stands unchanged**, in particular: this does not close the
slope-magnitude gap, it removes ONE of the two cancelling seams and leaves **South**
(−919 / −1,135 / −827 MW, the larger contributor) untouched on the incumbent anchor; the
admissibility statistic does not support the arm and the case rests on rule 14; and the
keeper's own provenance — its span solved under owner re-charter after the miso-231 screen
was killed on G-1 by 0.0183 — travels forward.

**Rule 29(c):** the screen bundle `results/calibration/_miso233_spp_screen` is **DELETED
before this branch merges**. Every number this session will ever cite from it is in this
document and in `_miso233_screen_gates.json`; git history is the record.

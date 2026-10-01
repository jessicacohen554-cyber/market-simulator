# FINDING capx-D5-R — the crossover co2 class-grain repair: scorer fix verified landed, the fifth bundle (NEISO) rescored, verdicts/board re-emitted under the pre-declared honesty gate

**Session.** capx-d5r-scorer-coal-grain (capacity-expansion / Forecast Finalization track),
chartered at director refresh #15 under the owner's **Q12 ruling** (full fix, D5 preference (a) —
`docs/handoffs/capx-director-ledger-2026-08.md` §0l.2/§3 Q12). Branch
`claude/capx-d5r-scorer-coal-grain-t6hoe2`, created fresh off `origin/main` at `e72e20f`;
main advanced 27 commits mid-session (S-4b, S-123, director r#17), so the delivery was
**rebuilt identically on `bd97c6e`** — every zero-solve step re-run at the new HEAD, controls
re-verified, anchors re-asserted against the S-4b/S-123-refreshed board (§6 reconciles the
r#17 adjudications). 2026-08-30. **Zero-solve:** yes — no LP solved, no model input/rate/curve/default changed
(rule 13: scorer-side only), no out-of-training year touched, freeze posture untouched (neither
tier read), no backcast surface edited. **Rule 28:** no mechanism tested, no `ScenarioConfig`
field added — no matrix row or cell.

---

## 0. Headline

**The Q12 repair is COMPLETE, and the honesty gate holds.** Two sessions delivered it:

1. **The scorer fix and the four-bundle rescore had ALREADY LANDED on main** when this session
   started, via the sibling repair session (PR
   [#4388](https://github.com/jessicacohen554-cyber/market-simulator/pull/4388), commits
   `3d58495` + `d2a318c`, record
   `docs/handoffs/RESULT-crossover-co2-grain-repair-2026-08-30.md`): `build_gmmodel` now splits
   generic-`COAL` generators to their supply class through the keeper's own canonical chain
   (`run_calibration_full._coal_supply_class` on `_plant_codes_from_unit_ids` — one taxonomy
   chain, rule 19 `[R-ONE-MECH]`), a zero-solve `--rescore-co2-grain` mode re-derives committed
   parquet-less bundles, and the ERCOT/PJM/MISO-ffr2a + NYISO-capxd10 bundles were rescored with
   verdicts re-emitted. This session **verified** all of it at HEAD (33 scorer tests + 9
   register tests pass; the charter's two required test shapes are present:
   `test_build_gmmodel_splits_generic_coal_to_supply_class` /
   `..._numeric_head_for_non_ercot` — the synthetic two-plant fixtures through the mapping,
   both unit-id shapes — and `test_coal_grain_rescore_is_a_noop_without_coal`, the no-coal
   control regression).
2. **This session completed the charter's remainder:** the FIFTH committed bundle —
   `neiso-2023-2027-crossover-capxd14`, registered by D14 *before* the repair landed — rescored
   zero-solve; `neiso-t1x` re-emitted from the scorer with its pre-repair baseline preserved
   verbatim as **`neiso-t1x-pre-d5r`** (the namespace's preserve-then-overwrite convention);
   D5-R instrument notes added to the three coal-ISO live keys whose bundles are uncommitted;
   the §2.1b board (`program-status.json`) updated everywhere it cites an FC-4 co2 magnitude,
   with the `d5r_co2_grain_repair` provenance block; and this record written.

**NO GATE LEG MOVES** (§5). **Every deviation from the charter as written is reported at full
magnitude** (§4): the three coal-ISO live keys could not be overwritten by the scorer (their
bundles were never committed — annotated instead, never hand-derived), and NEISO's 2024/2025
movement (+0.493/+0.492 pp) exceeds the pre-declared ≲0.4 % bound by ~0.09 pp for an
arithmetically exact reason (the bench COAL_BIT intensity is 1.386 t/MWh, not the ~1.0 the
bound assumed) while remaining seam-only.

## 1. Diff summary (this session; all zero-solve)

| file | change |
|---|---|
| `results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json` | `--rescore-co2-grain`: co2 rows 2024/2025 re-derived (+0.49 pp each; 2023 +0.004 pp, unchanged at 4-dp rounding), `rescore_co2_grain` provenance block, capacity-track `actual_basis` label. Deep-diff verified **seam-only**: 11 diffs total, every one on the co2 seam or a provenance/basis label; family_volume, C1 records, price rows, retirements/additions untouched. |
| `docs/hindcast-reports/neiso-2023-2027-crossover-capxd14-crossover-2026-08-30.md` | Re-score section appended (the T-R8 pattern, auto-emitted). |
| `frontend/data/hindcast/neiso-2023-2027-crossover-capxd14.json` | Re-registered via the single `register_forecast_run.py --bundle … --preserve-invariants` path; 14 diffs, all the same seam + fresh provenance stamps; committed invariant block preserved. |
| `frontend/data/forecast/ff-verdicts.json` | `neiso-t1x` re-emitted from the scorer (`rescore_forecast_verdicts.py --apply`; co2 2024 \|10.6 %\|→\|11.1 %\| in the FC-4 detail, statuses unchanged, determination HOLD); **`neiso-t1x-pre-d5r`** added — the pre-repair record verbatim plus a provenance note; D5-R instrument notes appended to `ercot-t1x`, `pjm-2023-2027-crossover-ffr3a3-t1x`, `miso-2023-2027-crossover-ffr3a4-t1x` (`notes` array only — no scored value touched). The 8 other tracked verdicts re-scored identically and their pure provenance re-stamps reverted to keep the diff minimal. |
| `frontend/data/forecast/program-status.json` | §3 below: re-scored magnitudes + citations on every FC-4-co2-citing string, the `d5r_co2_grain_repair` block, a sources entry. Asserted in the edit script: no `fc` scorecard, no gate `status`/`open`, no determination field moved. |
| `docs/handoffs/FINDING-capx-d5r-scorer-coal-grain-2026-08-30.md` | This record. |

`scripts/score_crossover.py` itself is **untouched by this session** — the fix was verified
already landed (commit `3d58495`), not re-implemented.

## 2. The honesty gate — D5 §5.2 measured vs pre-declared, CONTROLS FIRST

### 2.1 NYISO (the primary control — must be an EXACT no-op)

**CONFIRMED.** The sibling's rescore of `nyiso-2023-2027-crossover-capxd10` left every co2
err/signed/status byte-identical in all three years (no coal family, no bench coal intensity —
structurally zero unsplit energy to value); re-verified here from the committed
`rescore_co2_grain` block and by this session's re-run of the verdict scorer, which moved
nothing (`moved: nothing`, determination HOLD → HOLD). Live rows stay **+10.1 / +10.3 /
+3.9 %** exactly as pre-declared. No `nyiso-t1x-pre-d5r` copy was added: the repair superseded
nothing there (an identical measurement is not a superseded baseline), and the pre-repair
bytes remain reachable at commit `3d58495`.

### 2.2 NEISO (the second control, D14 finding 1 — pre-declared bound ≲0.4 %)

| year | signed before | after | Δ (pp) | unsplit COAL TWh | bench ī (t/MWh) | FC-4 band (K1.5) |
|---|--:|--:|--:|--:|--:|:--|
| 2023 | +12.81 % | +12.81 % | +0.004 | 0.001 | 0.8573 | CAVEAT → CAVEAT |
| 2024 | +10.60 % | +11.09 % | **+0.493** | 0.085 | 1.3862 | CAVEAT → CAVEAT |
| 2025 | −2.34 % | −1.85 % | **+0.492** | 0.082 | 1.3862 | PASS → PASS |

**DEVIATION, reported at full magnitude:** 2024/2025 exceed the ≲0.4 % bound by ~0.09 pp.
The cause is exact and pre-decomposable: D14's bound ("≤0.085 TWh … bounded ≲0.4 % of scored
CO2") implicitly priced the dropped energy at ~1.0 t/MWh; NEISO's bench `COAL_BIT` intensity
is **1.3862** t/MWh in 2024/2025 (0.8573 in 2023), and 0.085 × 1.3862 / 23.905 = +0.493 pp.
The movement equals `unsplit_twh × ī / egrid` to the fourth decimal in every year and the
deep-diff shows **nothing but the co2 seam moved** — so the gate's mechanism test ("any
control movement beyond the seam means the fix touched more than the unmapped-coal seam —
STOP") does **not** fire: the movement *is* the seam, at the pre-declared TWh magnitudes, at
the bench's own measured intensity. Banded statuses and the HOLD determination are unchanged.

### 2.3 The three coal ISOs (measured on the committed bundles, by the sibling; re-verified here)

FC-4 co2 signed error after repair (pre-declared D5 §5.2 in parentheses; declared tolerance
±0.5 pp for the (b) arithmetic):

| ISO | 2023 | 2024 | 2025 | outcome (as pre-declared) |
|---|--:|--:|--:|:--|
| ERCOT (K=1.5) | **−25.2 %** (−25.3) | **−23.2 %** (−23.2) | **+1.3 %** (+1.3) | 2023/24 STILL FAIL — the honest volume gap; 2025 PASS |
| PJM (K=3.0) | **−7.4 %** (−7.6) | **−10.3 %** (−10.5) | **−1.1 %** (−1.3) | co2 leaves PJM's FC-4 FAIL set (2023/25 PASS, 2024 CAVEAT); FC-4 stays FAIL on coal_twh 2024 |
| MISO (K=3.0) | **+1.2 %** (+1.2) | **−1.8 %** (−1.9) | **+13.4 %** (+13.4) | co2 leaves MISO's FC-4 FAIL set (2023/24 PASS, 2025 CAVEAT); FC-4 stays FAIL on its volume rows |

Every cell within ±0.2 pp of pre-declared. **Family-row controls hold:** MISO's `coal_twh` and
PJM's `gas_twh` rows (already grain-reconciled by `_family_volume`) are deep-equal before/after
in every ISO-year, as are all C1 records, price rows, and capacity blocks (sibling's semantic
check, §3 of its RESULT doc; re-confirmed on the committed artifacts here).

### 2.4 C1 fuelmix rows — before/after (charter reporting duty)

The **(a)** fix repairs the phantom C1 coal-rank rows (model `COAL_PRB`/`COAL_BIT`/… read 0.0,
~60 TWh/ISO-yr of scoring-artifact error) **at source, for every future scoring that has
dispatch parquets**. The committed bundles were rescored through the **(b)-arithmetic**
`--rescore-co2-grain` path, which by design values the unsplit energy at family grain and
**does not rewrite the C1 per-class rows** — so the committed records' C1 coal rows are
byte-unchanged (before = after), the family `gas_twh`/`coal_twh` rows were already
grain-reconciled, and no phantom row is banded anywhere (C1 never gated the mismatched rows).
The phantom rows disappear from the record the first time each leg is re-solved and scored
natively on the repaired scorer.

## 3. Verdicts and board — what moved, before → after

**ff-verdicts.json (45 keys, was 44):**

- `neiso-t1x` (live): co2 2024 \|10.6 %\| → \|11.1 %\| in the FC-4 dispatch-skill detail
  (2023 unchanged at rounding; 2025 is a PASS row, \|2.3 %\| → \|1.9 %\| in the score
  artifact); every banded status identical; determination **HOLD → HOLD**; provenance
  re-stamped `e72e20f26c72`.
- `neiso-t1x-pre-d5r` (NEW): the pre-repair record verbatim + provenance note — the preserved
  superseded baseline, per the namespace convention (`neiso-t1f-ffr3a2` precedent).
- `ercot-t1x`, `pjm-2023-2027-crossover-ffr3a3-t1x`, `miso-2023-2027-crossover-ffr3a4-t1x`:
  scored content **untouched**; one D5-R note each (see §4.1) naming the pre-repair instrument,
  the DROP share, and the repaired committed re-measure key.

**program-status.json:** every string citing an FC-4 co2 magnitude now carries the repair —
`headline`, `gate_reading`, ERCOT `blocking_rows[3]` + leg-(c) detail + `gate.note`, PJM
`blocking_rows[1]` + leg-(c) detail, MISO `blocking_rows[3]` + leg-(c) detail (including the
retirement of "MISO's is the LARGEST measured co2 gap in the program" as an instrument
artifact), NYISO leg-(c) detail (control confirmation), NEISO `blocking_rows[3]` + leg-(c)
detail (numeric update **+12.8/+10.6/−2.3 → +12.8/+11.1/−1.8 %**). New top-level
`d5r_co2_grain_repair` block: the repair, the verdict movement, the measured honesty gate, the
instrument property, and the no-gate-moved statement. New `sources` entry documenting the
`-pre-d5r` suffix convention. The board's `fc` scorecards, every gate `status`/`open` field,
and every determination field are **byte-identical** (asserted programmatically in the edit
script before writing).

**Instrument property recorded (D5 corollary 2, charter duty):** as constructed, the FC-4 co2
metric applies bench intensities to the model mix on both sides — it scores **volume/mix +
class mapping, never rate error**. The emission-rate derivation is measured separately (D5 §2
own-rate comparison: within ±5 % in every ISO-year — exonerated). Documented in
`d5r_co2_grain_repair.instrument_property` and in each live-key note; not "fixed", per the
charter.

## 4. Deviations from the charter as written — all reported, none absorbed

### 4.1 The three coal-ISO live keys were ANNOTATED, not overwritten

The charter instructed preserve-then-overwrite of all five live keys. That instruction rests
on the premise that the live keys are backed by the committed crossover bundles; it holds for
`nyiso-t1x`/`neiso-t1x` but **not** for the other three: `ercot-t1x` carries the FFR-3A-2
re-measure and the PJM/MISO keys carry the FFR-3A-3/-4 legs, whose bundles were **never
committed** (D5 §1.1; `results/ffr3a2..4` are gitignored by design — only scorecards/READMEs
survive, and those carry category statuses, not the numeric rows the rescore arithmetic needs).
So for those records exactly two overwrite routes existed, and both fail honesty:

- **hand-deriving** their repaired co2 from unsigned detail strings plus prose-inferred signs —
  the session deciding, not the scorer, which the charter itself forbids ("you decide nothing,
  the scorer does"); or
- **displacing** them with the rescored ffr2a-based verdicts — which would silently swap this
  program's newest price/volume measurements for an older leg's (the ffr2a legs measured a
  configuration FFR-3A-3 explicitly re-measured *because* it was superseded by the G3
  cap-grain fix; e.g. ERCOT's live price-2025 22.5 % FAIL would vanish), violating the
  namespace's own rule that a run never renders a verdict its own score contradicts.

The executed treatment: the records **stand as measured, at full magnitude**, each carrying a
D5-R note naming the defect, its DROP share, and the repaired committed re-measure
(`ercot-t1x-ffr2a` / `pjm-t1x-ffr2a` / `miso-t1x-ffr2a`); the board carries the repaired
magnitudes beside every citation. Consequently there are no `-pre-d5r` copies for these three
(nothing was overwritten) — the suffix exists where the convention applies,
`neiso-t1x-pre-d5r`. Any future re-solve of these legs scores through the repaired
`build_gmmodel` automatically.

### 4.2 NEISO's 2024/2025 movement exceeds the pre-declared ≲0.4 % by ~0.09 pp

§2.2. Mechanism-exact (seam-only, `unsplit × ī`), cause identified (ī = 1.386 vs the ~1.0 the
bound assumed), statuses unchanged. Reported, not absorbed; the re-score is committed because
the gate's operative test — movement confined to the unmapped-coal seam — is verified, and the
numeric bound was the estimate of that seam, not a separate constraint.

### 4.3 The work landed in two sessions

The scorer fix + four-bundle rescore landed via PR #4388 (a sibling execution of the same Q12
ruling) between this lane's issuance (r#16 verified the wave current at `b5050e9`) and its
launch. This session did not re-implement or duplicate any of it: it verified the landed state
at HEAD (tests, controls, expectation table) and executed the remainder (NEISO, `-pre-d5r`,
live-key notes, board, this record). The director's ledger row for D5-R should count **both**
PR #4388 and this branch as the lane's delivery.

### 4.4 Report-only observations (no action taken)

- NEISO's capacity-track co2 block reads `"actual": {}` with an `actual_basis` label of "STATE
  SUM over none" — NEISO is in neither `ISO_CAMPD_STATES` nor `ISO_CAMPD_FACILITY`, so the
  capacity-track co2 has no actual for it (a pre-existing property of the D14 registration; the
  FC-4 co2 metric, which this lane repaired, is unaffected). Cosmetic label; left as-is.
- The live `ercot-t1x` record's FC-4 rows mix legs (price from FFR-3A-2, the board's leg-(c)
  provenance naming FFR-3A-3) — pre-existing board archaeology, outside this lane's scope,
  unchanged by the annotations.

## 5. NO GATE LEG CHANGES — the explicit statement

Leg (c) statuses **do not move in any ISO**: the leg closes on a MEASURED FC-4 (owner ruling
Q7, "measured closes the leg"), and **a re-scored measurement is still measured**. Legs
(a)/(b)/(d) read no FC-4 co2 magnitude. Every FC-4 category verdict is unchanged — ERCOT still
FAIL (price + volume + the honest co2 volume error), PJM still FAIL (coal_twh 2024), MISO
still FAIL (gas_twh 2024), NYISO still FAIL (price/gas_twh), NEISO still FAIL
(price/gas_twh/coal_twh) — and every t1x determination stays HOLD. Every gate stays
`open: false`. Nothing was promoted, nothing was tuned, and no residual miss was chased: the
honest misses stay with their owners exactly as D5 §5.3 assigned them (ERCOT's crossover
volume gap → ERCOT forecast lane; the three-ISO 2025 coal over-dispatch → the
evolved-fleet/2025-vintage question; NYISO's gas over-dispatch → D10's open item; NEISO's
gas over-dispatch and retirement composition → D14's findings).

## 6. Reconciliation with director refresh #17 (landed mid-session)

Refresh #17 (`docs/handoffs/capx-director-ledger-2026-08.md` §0n) adjudicated two things this
delivery must be read against:

- **§0n.2, "the fifth bundle, adjudicated … no follow-up owed."** The director bounded the
  NEISO grain drop from the **2023 family row alone** (0.001 TWh → "≈0.004 % — below
  representable precision") and concluded D14's +12.8/+10.6/−2.3 % stand as the honest
  values. The measured rescore (this delivery, §2.2) shows that bound holds **only for
  2023**: the 2024/2025 rows carry **0.085/0.082 TWh** of unsplit model coal at the bench's
  1.386 t/MWh — **+0.493/+0.492 pp**, two orders of magnitude above the 0.004 % read, and
  the repaired honest values are **+12.8/+11.1/−1.8 %**. The r#17 conclusion that the
  *sibling's skip* warranted no urgent follow-up was reasonable on its materiality; the
  single-year bound underneath it is corrected here, by measurement, as this lane's charter
  ordered. No banded status moves either way.
- **§0n.3, the board co2 annotation, "DEFERRED to the next records act"** (to avoid mid-wave
  `program-status.json` contention with D12-C/S-4b/S-123). S-4b and S-123 have since landed
  and merged; this delivery is rebased onto their board state (`bd97c6e`), every edit anchor
  re-asserted against the refreshed blocks, and D12-C's pending surface (ERCOT matrix shard /
  T1-H probe) does not intersect it. The named records item — a `[D5-R 2026-08-30]`-style
  annotation on the three cells + `gate_reading`, cross-referencing the repaired committed
  rows — is exactly what §3 ships. The deferral is thereby **discharged**, not overridden.

## 7. Guardrail attestation

Zero LP solves; zero backcast-surface edits; no out-of-training year solved, scored or read
(every input was a committed 2023–2025 artifact; the rescore path's bench loaders are
`_assert_scoreable_year`-guarded); holdout freeze untouched (tier-scoped, neither tier
approached). No measured-outcome feedback (rule 13): bench data entered only through the
scorer's own intensity reconciliation, never a model input. No new GitHub Actions workflow; no
CI compute. Data profile stayed `code`. `scripts/score_crossover.py` untouched by this session
(fix verified landed at `3d58495`); no backcast scorer imports the changed seam — the keepers
score through `calibration_verdict.py`, whose `PLANT_GROUP_MEMBERS` bridge (rubric v2.8)
already handled it, and the backcast side is measured unchanged (the sibling's rescore
re-emitted no backcast artifact; `audit_keepers`/matrix guards pass at this HEAD). Tests: 42
passing in `tests/scoring/test_score_crossover.py` + `test_register_hindcast_collision.py`.

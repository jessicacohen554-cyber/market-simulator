# PREREG — nyiso-155: the chartered hydro truncation repair, re-armed on the nyiso-152 keeper (pushed BEFORE any measurement)

**Session:** nyiso-155, 2026-08-25. **Charter:** `docs/mechanism-testing-matrix.md`
§5.5 item 12 tail (the nyiso-107 block) — the owner's 2026-07-31 decision was
"report + charter, do not arm from this session"; THIS is the chartered session.
**Keeper under test (control basis):** `2026-08-22-nyiso-152-duty-complete`
(bundle `results/calibration/nyiso152_armSE`), determination **CALIBRATED**
(C1 14/14 · free 10/10; C2/C3a/C3b/C4/C6/C8 PASS; C3a +5.3 / −2.7 / −8.1 %;
C3c the lone ledgered caveat, model 1/0/0 h vs RT 10/13/42 h > $300),
**FRONTIER-RATIFIED 2026-08-23**. **Solve HEAD:** `ac194ba` (= origin/main at
session start). **Rule 12:** control and arm run as two concurrent invocations,
years 2023 2024 2025 sequential within each (rule 16 `[R-ALLYEARS]`).

---

## §0 — DISCOVERED BEFORE MEASUREMENT, reframing the session: this is a RE-ARM after a SILENT DE-ARM

The charter (nyiso-107, 2026-07-31) chartered the arm. The record shows it was
then **executed once**: session **nyiso-108** (2026-07-31,
`FINDING-nyiso108-hydro-input-repair-2026-07-31.md`) armed the pair as a
pre-registered A/B, and the arm was **PROMOTED to keeper** by explicit owner
override, moving the matrix cell `hydro_vintage_input_repair` NYISO **U → K**,
where it still stands. nyiso-109 (2026-08-01) then closed the C3a-2023 breach
the repair exposed, restoring CALIBRATED-WITH-CAVEATS.

**The current keeper does not carry the repair.** Re-verified in this session
from artifacts, not prose:

- `results/calibration/nyiso152_armSE/meta.json`:
  `hydro_backfill_year = null`, `hydro_eia930_monthly = false`.
- The keeper's own committed `hourly/class_hourly_<year>.parquet` sidecars sum
  hydro to **28.3833 / 27.8294 / 21.0482 TWh** — bit-identical to the
  nyiso-107 UNREPAIRED numbers, 2025 being the truncated 3-plant budget spent
  exactly.
- Every on-disk NYISO recipe/bundle meta from nyiso-144 (2026-08-18) through
  nyiso-154 reads `None / False`; the nyiso-114 base recipe
  (`_nyiso114_baseattrib_2024/meta.json`, 2026-08-02) still read
  `2024 / True`.
- `docs/calibration-log/nyiso.md` contains **no de-arm decision** — the last
  mention of `hydro_backfill` is the nyiso-107/108/109 arc.

So the pair fell out of the keeper lineage **between nyiso-114 (2026-08-02) and
nyiso-144 (2026-08-18), silently**. The structural mechanism is identifiable:
`hydro_backfill_year` / `hydro_eia930_monthly` are `solve_and_persist` **kwargs,
not `ScenarioConfig` fields**, so the lineage-reconstruction fidelity checks the
intermediate sessions used ("all 680 `scenario_config` fields verified
identical", nyiso-128) are structurally blind to them — the miso-50..53
lossy-reconstruction class, landed in the keeper lineage itself. The exact
commit cannot be pinned from this clone (the intermediate bundles were pruned
2026-08-15 and their blobs stripped by the 2026-08-16 history rewrite); the
finding records the interval and the mechanism.

**Consequences for this session:** (a) it is a **re-arm of an adjudicated-K
cell onto the current keeper recipe** — not a first test, so no R/I/G re-test
discipline is implicated; (b) the silent de-arm is itself a **governance
finding** (an unregistered recipe change in the keeper lineage) and is reported
whatever the A/B outcome; (c) the stale matrix evidence (`K` citing nyiso-108
against a keeper that no longer carries the flags) is repaired by this
session's shard update.

## §1 — The fact table, re-verified at dispatch from the keeper metas (bundle paths cross-checked against registry sidecars)

| ISO | keeper | bundle | `hydro_backfill_year` | `hydro_eia930_monthly` |
|---|---|---|---|---|
| **NYISO** | 2026-08-22-nyiso-152-duty-complete | nyiso152_armSE | **None** | **False** |
| ERCOT | 2026-08-25-234-eastex-identity | ercot234_eastex_identity | None | False *(hydro 0.017–0.463 TWh/yr, immaterial)* |
| CAISO | 2026-08-17-caiso-200-h1-memberpanel | caiso200_h1_memberpanel | 2024 | True |
| PJM | 2026-08-15-pjm-162-inputclock | pjm_debugb_inputclock_A | 2024 | True *(pin internally refused, PS fold)* |
| MISO | 2026-08-22-miso-177-rho-measured | miso177_rho_B | 2024 | True *(pin internally refused, PS fold)* |
| NEISO | 2026-08-17-neiso-99-joint-p1 | neiso99_joint_B | 2024 | True |

NYISO remains the sole ISO running a **material** hydro class (26.5 TWh/yr,
~18 % of generation, 2025 EIA-923 vintage retention 2.0 %) on the unrepaired
truncated input.

## §2 — The arms

- **CONTROL** — zero-delta replay of the committed keeper recipe at HEAD:
  `python3 scripts/replay_keeper.py results/calibration/nyiso152_armSE
  --out-dir results/calibration/nyiso155_hydro_control --note "nyiso-155
  zero-delta control (hydro truncation repair A/B)"`
  → registered as `2026-08-25-nyiso-155-hydro-control`.
- **ARM** — the identical recipe plus exactly the pair:
  `python3 scripts/replay_keeper.py results/calibration/nyiso152_armSE
  --out-dir results/calibration/nyiso155_hydro_repair
  --set hydro_backfill_year=2024 --set hydro_eia930_monthly=true
  --note "nyiso-155 hydro truncation repair arm (backfill 2024 + EIA-930
  monthly level pin)"`
  → registered as `2026-08-25-nyiso-155-hydro-repair`.

Zero fitted scalars; two existing `solve_and_persist` kwargs; no new
`ScenarioConfig` field; no derive script touched (rule 23
`[R-FROZEN-DERIVE]`); rule 13 admissibility unchanged from the adjudicated row
(an inflow budget that regenerates forward via `forecast_monthly_hydro`;
declared `backcast_only` MechanismSpec).

**HEAD drift audit (charter obligation, done before this push):** the keeper's
solve sha `372f50b` → HEAD `ac194ba` moves 19 files / +949 lines over
`src/market_sim` + `scripts/run_calibration_full.py` + `scripts/lib` (12
non-merge commits: ercot-230/231/234, miso-180/183/186, caiso-217,
entry-signal L-5, capx-d2). All are other-ISO-gated or default-off; the one
NYISO-touching commit (capx-d2, `ADEQUACY_EXTERNAL_TIE_FIRM_MW`) sits in the
forecast-side adequacy backstop. `data/raw` NYISO drift: README-only.
**Inertness is NOT assumed** — gate G1 decides it empirically, which is why the
control is re-solved rather than reused.

## §3 — Gates, fixed before any solve

| # | Gate | Bar | Class |
|---|---|---|---|
| G1 | **IDENT** | Control vs committed keeper bundle: per-year `hourly/class_hourly_<y>.parquet` and `hourly/system_<y>.parquet` compare with max abs delta **exactly 0.0** on dispatch MW and price | **STOP** |
| G2 | **SINGLE-DELTA** | Arm meta vs control meta differ in exactly `{hydro_backfill_year: None→2024, hydro_eia930_monthly: False→True}` (timestamps/ids/provenance excluded) | **STOP** |
| G3 | **INPUT EFFECT** | Arm hydro budgets land on the 930 levels ≈ 26.8365 / 26.7463 / 24.0625 TWh; 2025 LP hydro fleet 3 → ~147 units; Δbudget ≈ −1.5668 / −1.1287 / +3.0143 TWh (nyiso-107 §E). Deviations are reported and explained, never tuned toward | report |
| G4 | **HYDRO VOLUME** | Expected ≈ −0.2 % each year. **TAUTOLOGICAL BY CONSTRUCTION** — see §4 | report |
| G5 | **SHAPE** | Hydro hourly r + hour-of-day profile vs EIA-930 `NG: WAT` (gap-masked), and P-63 monthly seasonal shape r — arm vs control, per year, full magnitude, direction-blind | report |
| G6 | **DETERMINATION** | `calibration_verdict.py` on the arm's committed artifacts reads **not worse than the keeper's**: CALIBRATED with at most the lone ledgered C3c. **ANY DOWNGRADE (CALIBRATED → anything) OR LOSS OF THE FRONTIER BASIS ESCALATES TO THE OWNER AND IS NEVER SELF-ADJUDICATED** | **STOP** |
| G7 | **CRITERIA DETAIL** | Every criterion, arm vs control, at full magnitude (rule 14: adverse moves are reported, never patched). Pre-declared risk from the nyiso-108 record: removing ~1.55 TWh of phantom 2023 zero-MC hydro lifts C3a-2023 by ≈ +1.5–2 pp (control +5.3 % ⇒ expected ≈ +7 %, inside ±10 %). If it crosses the band, that is G6 territory | report |
| G8 | **LEGITIMACY** | No new failing D-row (D-1/D-2/D-4) on the arm vs control; C8 PASS | **STOP** |

**G1 failure branch (pre-committed):** the A/B stays internally valid (same
HEAD both arms), measurement completes, both runs are registered (rule 15),
the drift magnitude is reported — and **no promotion is self-adjudicated**:
the keeper-not-reproducing state is the nyiso-128 K6 / 2026-07-26
de-designation class and goes to the owner.

## §4 — THE HONESTY CONSTRAINT, carried verbatim into every artifact of this session

A 930 LEVEL PIN MAKES THE HYDRO **VOLUME** STATISTIC NEAR-TAUTOLOGICAL
(≈ −0.2 % BY CONSTRUCTION — budget and benchmark become the same series). It is
admissible under rule 13 `[R-MEASURED]` as an INFLOW BUDGET THAT REGENERATES
FORWARD, but it MUST BE **DECLARED, NEVER BANKED AS AN IMPROVEMENT**. Every
hydro-volume number this session reports carries the label **"tautological by
construction"** at every mention, and NO claim of skill is made from it, in
any direction. Dispatch **SHAPE** (G5) stays the free output and is the only
place a real hydro result can live. If any promotion argument leans on the
volume statistic in any form, the argument is void. (Consistent with the
scorer: `calibration_verdict.py` already lists hydro as a D-10 pinned class —
"L6 hydro (monthly budgets)" — and C1 gates only the gas/coal families, so
hydro volume is not a gated row; the scored movement that matters is the
1:1 fossil displacement, which is reported under G7 at full magnitude.)

## §5 — Promotion rule (direction-blind, fixed here, before any number exists)

**The basis of this repair is INPUT ACCURACY** (rule 14 `[R-ACCURATE]` +
rule 1 `[R-STRUCT]`), not the residual and not the (tautological) volume
statistic:

1. **PROMOTE the arm to keeper iff G1, G2, G6 and G8 all pass.** G3–G5 and G7
   are report-class and carry no promotional weight in either direction.
2. **If the accurate input makes any fit worse, the accurate input still
   stays** and the worse fit is a DISCOVERED defect somewhere else, named as
   an open root-cause item (the nyiso-108 → nyiso-109 pattern) — never a
   reason to revert to the truncated series, soften the backfill, or add a
   compensating adjustment.
3. **Any determination downgrade or loss of the frontier basis: NO promotion,
   ESCALATE to the owner** with the full record. This session never
   self-adjudicates that trade. The truncated-input keeper stays designated
   until the owner decides; the finding still stands.
4. Whatever the outcome, **both runs are registered on the backcast dashboard
   in this session** (rule 15 — keeper or rejected probe alike), the finding
   is written, and the NYISO matrix shard cell (`hydro_vintage_input_repair`)
   is updated with the nyiso-155 evidence, including the silent-de-arm record
   (duty 28(b)).
5. On PROMOTE, in order: hourly sidecars committed with the bundle; keeper
   shard `frontend/data/backcast/keepers/NYISO.json` re-keyed;
   `calibration-complete.json` re-keyed **with the determination re-verified
   from committed artifacts BEFORE the promotion commit** (rule 22 D-5(b) —
   a worse re-verification stops the promotion and escalates); matrix §5.5
   prose header re-stamped; `calibration-keeper-auditor` run `--iso NYISO`.

## §6 — Hard rails

Years **{2023, 2024, 2025} only** — the holdout spend freeze is ACTIVE and
outranks NYISO's `complete` marker; `--holdout-authorized` is never passed;
2019/H1-2026 are NEVER GRANTED. No other ISO's file moves (rule 25
`[R-ISO-SCOPE]`). No new workflows; solves run in this session's container.
Push after each solved year; run payloads travel over `git push`
(≥ `push_files`' cap); every push touching a ≥300-line file is blob-verified
(rule 27 `[R-PUSH]`).

# FINDING — nyiso-155: the chartered hydro truncation repair, re-armed on the NYISO keeper — and the discovery that it had been armed once and silently lost

**Session:** nyiso-155, 2026-08-25. **Charter:** `docs/mechanism-testing-matrix.md`
§5.5 item 12 tail (the nyiso-107 block; owner decision 2026-07-31 "report +
charter, do not arm from this session" — this is the chartered session).
**Prereg:** `results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md`,
pushed and blob-verified BEFORE any measurement (commit `19f379d`).
**Keeper under test:** `2026-08-22-nyiso-152-duty-complete`
(bundle `results/calibration/nyiso152_armSE`), CALIBRATED, frontier-ratified
2026-08-23. **Solve HEAD:** `ac194ba`. **Gates record:**
`results/calibration/_nyiso155_hydro_repair_ab.json`
(probe `scripts/probes/_nyiso155_hydro_repair_ab.py`).

**THE HONESTY CONSTRAINT, first because it governs every number below:** under
the EIA-930 monthly level pin, the hydro **VOLUME** statistic is
**NEAR-TAUTOLOGICAL BY CONSTRUCTION** — the budget and the benchmark become the
same series, so the ≈ −0.2 % volume error the arm reads is plumbing, not skill.
It is admissible under rule 13 `[R-MEASURED]` as an inflow budget that
regenerates forward (`forecast_monthly_hydro`), but it is **DECLARED, NEVER
BANKED AS AN IMPROVEMENT**. Every hydro-volume number in this finding carries
the label **(tautological by construction)**. Dispatch **SHAPE** (§4) is the
only place a real hydro result can live, and the promotion argument (§6) leans
on no volume statistic in any form.

---

## §1 — The fact, re-verified at this session from artifacts (not prose)

| ISO | keeper | `hydro_backfill_year` | `hydro_eia930_monthly` |
|---|---|---|---|
| **NYISO** | 2026-08-22-nyiso-152-duty-complete | **None** | **False** |
| ERCOT | 2026-08-25-234-eastex-identity | None | False *(0.017–0.463 TWh/yr, immaterial)* |
| CAISO | 2026-08-17-caiso-200-h1-memberpanel | 2024 | True |
| PJM | 2026-08-15-pjm-162-inputclock | 2024 | True *(pin internally refused, PS fold)* |
| MISO | 2026-08-22-miso-177-rho-measured | 2024 | True *(pin internally refused, PS fold)* |
| NEISO | 2026-08-17-neiso-99-joint-p1 | 2024 | True |

Read from each keeper bundle's `meta.json`, bundle paths cross-checked against
the registry sidecars. NYISO ran a **material** hydro class — 26.5 TWh/yr,
~18 % of its generation, 2025 EIA-923 vintage plant retention **2.0 %** — on
the unrepaired truncated input: its keeper's own committed
`hourly/class_hourly_<y>.parquet` sidecars sum hydro to
**28.3833 / 27.8294 / 21.0482 TWh** *(volume — tautology does not apply to the
bare arm, but these are the unrepaired numbers nyiso-107 measured)*, the 2025
figure being the truncated 3-plant budget spent exactly.

## §2 — Discovered before measurement: the repair was ARMED ONCE and SILENTLY LOST

This charter was **already executed**: session **nyiso-108** (2026-07-31,
`FINDING-nyiso108-hydro-input-repair-2026-07-31.md`) armed exactly this pair as
a pre-registered A/B and the arm was **PROMOTED to keeper by explicit owner
override** (its C3a-2023 cost, +8.6 → +10.2 %, was a discovered defect that
nyiso-109 then closed on measured grounds). The matrix cell
`hydro_vintage_input_repair` NYISO has read **K** ever since, citing nyiso-108.

The pair then **fell out of the keeper lineage silently**:

- `_nyiso114_baseattrib_2024/meta.json` (nyiso-114 base recipe, 2026-08-02):
  **2024 / True** — still armed.
- Every on-disk NYISO recipe/bundle meta from nyiso-144 (2026-08-18) through
  nyiso-154: **None / False**.
- `docs/calibration-log/nyiso.md`: **no de-arm decision anywhere** — the last
  mention of `hydro_backfill` is the nyiso-107/108/109 arc.

**The structural mechanism:** `hydro_backfill_year` / `hydro_eia930_monthly`
are `solve_and_persist` **kwargs, not `ScenarioConfig` fields**, so the
lineage-reconstruction fidelity checks used across the nyiso-125..133 window
("all 680 `scenario_config` fields verified identical", nyiso-128) are
**structurally blind to them** — the miso-50..53 lossy-reconstruction defect
class, landed in the keeper lineage itself. The exact dropping commit cannot be
pinned from this clone: the intermediate bundles were pruned from the site on
2026-08-15 (owner retention directive) and their blobs stripped by the
2026-08-16 history rewrite. The interval and mechanism above are the record.

**Governance consequence (reported, not adjudicated here):** an armed keeper
mechanism was de-armed with no decision, no log entry, and no matrix update —
the matrix cell claimed K against keepers that did not carry the flags for
~three weeks. A durable guard would extend the lineage-fidelity check from the
scenario block to the full `solve_and_persist` kwarg surface (the
`_config_block` merge in this session's gates probe is the pattern); left for
its own charter.

## §3 — The A/B: arms, gates, and the drift audit

- **Control** `2026-08-25-nyiso-155-hydro-control`
  (`results/calibration/nyiso155_hydro_control`) — the keeper's recipe replayed
  zero-delta at HEAD `ac194ba` via `scripts/replay_keeper.py`.
- **Arm** `2026-08-25-nyiso-155-hydro-repair`
  (`results/calibration/nyiso155_hydro_repair`) — identical plus exactly
  `--set hydro_backfill_year=2024 --set hydro_eia930_monthly=true`.
  Zero fitted scalars, no new fields, no derive script touched.

**HEAD drift audit** (prereg §2): keeper solve sha `372f50b` → `ac194ba` moves
19 files / +949 lines over the LP surface (ercot-230/231/234, miso-180/183/186,
caiso-217, entry-signal L-5, capx-d2); NYISO-relevant data drift nil.
Inertness was **not assumed** — gate G1 decided it empirically:

- **G1 IDENT:** <G1_RESULT — control vs committed keeper, max |Δdispatch| and
  max |Δprice| per year>
- **G2 SINGLE-DELTA:** <G2_RESULT>
- **G8 LEGITIMACY:** <G8_RESULT>

## §4 — Results

### §4.1 Input effect (G3, report-class)

<TABLE: per-year hydro TWh A/B, delta vs the nyiso-107 §E expectations
−1.5668 / −1.1287 / +3.0143>

### §4.2 Hydro volume (G4 — TAUTOLOGICAL BY CONSTRUCTION, never banked)

<TABLE: A/B vs as-scored benchmark and vs P-63; every number labelled
(tautological by construction) on the arm side>

### §4.3 Hydro dispatch SHAPE (G5 — the only load-bearing hydro evidence)

<TABLE: hourly r, daily r, hour-of-day profile r + swing vs gap-masked EIA-930
NG: WAT; monthly seasonal shape r vs P-63; annual peak month>

### §4.4 Scorecards and side effects at full magnitude (G6/G7, rule 14)

<TABLE: determination + per-criterion statuses, keeper / control / arm;
C3a per year; C3c counts; per-class TWh deltas (the 1:1 fossil displacement);
mean λ>

## §5 — Determination and the pre-registered promotion rule

<VERDICT under prereg §5: G1/G2/G6/G8 status; the promotion decision;
escalation state if any. The basis is INPUT ACCURACY (rules 14 + 1), not the
residual and not the volume statistic.>

## §6 — What this changes on the record

<matrix cell update; keeper re-key if promoted (D-5(b) re-verification);
registration ids; what remains open>

---

Evidence in-repo: `results/calibration/_nyiso155_hydro_repair_ab.json`,
`scripts/probes/_nyiso155_hydro_repair_ab.py`,
`results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md`,
registered bundles `nyiso155_hydro_control` / `nyiso155_hydro_repair`.

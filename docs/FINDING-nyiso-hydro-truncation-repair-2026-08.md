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

- **G1 IDENT: FAIL.** The control is NOT bit-identical to the committed keeper
  in 2023/2024; 2025 is EXACTLY identical:

  | year | max \|Δdispatch\| MW | max hourly \|Δλ\| $/MWh | annual mean λ Δ |
  |---|---|---|---|
  | 2023 | 658.4 | 2.18 | **+0.016** |
  | 2024 | 457.9 | 2.61 | **+0.018** |
  | 2025 | **0.0** | **0.0** | 0.000 |

  **Attribution, measured:** all nine pinned input extracts (EIA-930, EIA-923,
  CAMPD, five outage extracts, capacity deliverability) are content-identical
  by hash; zonal demand, reserve requirements, slack and dump are
  bit-identical; hydro and import annual energies are identical to 4 dp and
  only **reshuffle within the year** (January-2023 shuffles at unchanged
  prices); net class-energy moves are ≤ 0.027 TWh; the recorded package
  environment (highspy 1.14.0, numpy 2.4.6, scipy 1.17.1) is identical. This
  is the **same-objective alternative-optima signature** — a
  matrix-construction-order perturbation from the HEAD drift selecting a
  different vertex of the same optimal face, with dual degeneracy repricing
  tied hours by ladder-rung gaps — NOT an input-series change (every measured
  input surface checked is identical) and not a solver-version change. At the
  **scorecard basis** the control is determination-identical to the keeper:
  **CALIBRATED**, C3a +5.3 / −2.6 / −8.1 % (keeper recorded +5.3 / −2.7 /
  −8.1), C3c 1/0/0 h ledgered. The prereg's pre-committed G1 failure branch
  applies: measurement completed, both runs registered, drift reported —
  **no promotion self-adjudicated.**
- **G2 SINGLE-DELTA: PASS** — the arms' recorded configs (meta ∪ scenario
  block) differ in exactly `{hydro_backfill_year: None→2024,
  hydro_eia930_monthly: False→True}`.
- **G8 LEGITIMACY: PASS** — zero new failing D-rows on the arm; C8 PASS both
  arms.

## §4 — Results

### §4.1 Input effect (G3, report-class)

| year | control hydro TWh | arm hydro TWh | Δ TWh | nyiso-107 §E expected (budget) |
|---|---|---|---|---|
| 2023 | 28.3833 (154 units) | 26.8328 (155 units) | **−1.5505** | −1.5668 |
| 2024 | 27.8294 (147 units) | 26.7390 (147 units) | **−1.0904** | −1.1287 |
| 2025 | 21.0482 (**3 units**) | 24.0589 (**147 units**) | **+3.0107** | +3.0143 |

The measured deltas match the nyiso-108 A/B's measured dispatch deltas
(−1.5505 / −1.0904 / +3.0107) **exactly** — the re-arm reproduces the
2026-07-31 arm to 4 decimals. The 2025 LP hydro fleet is restored 3 → 147
units.

### §4.2 Hydro volume (G4 — TAUTOLOGICAL BY CONSTRUCTION, never banked)

| year | control vs bench | arm vs bench *(tautological by construction)* | control vs P-63 | arm vs P-63 |
|---|---|---|---|---|
| 2023 | +1.26 % | −4.28 % *(tautological by construction)* | +4.41 % | −1.29 % |
| 2024 | +1.33 % | −2.64 % *(tautological by construction)* | +3.16 % | −0.88 % |
| 2025 | −12.68 % | −0.19 % *(tautological by construction)* | −13.20 % | −0.78 % |

Under the 930 pin the budget and the benchmark are the same series, so the
arm-side numbers are **plumbing, not skill** — no claim is made from them in
any direction. (The scorer already treats hydro as a D-10 pinned class; C1
gates only the gas/coal families. The benchmark itself did not move with the
registration — the nyiso-149 `btm_bench_twh` flag-independence pin held: zero
`bench/NYISO/` diffs.)

### §4.3 Hydro dispatch SHAPE (G5 — the only load-bearing hydro evidence)

Against gap-masked EIA-930 `NG: WAT` (the scorer's own series) and NYISO MIS
P-63 (EIA-independent):

| year | hourly r A→B | daily r A→B | hod profile r A→B | hod swing MW (meas / A / B) | monthly r vs P-63 A→B | peak month (P-63 / A / B) |
|---|---|---|---|---|---|---|
| 2023 | 0.7392 → 0.6908 | 0.5157 → 0.4312 | 0.9856 → 0.9707 | 1305 / 1561 / 1644 | 0.9925 → 0.9880 | 1 / 1 / 1 |
| 2024 | 0.7946 → 0.7555 | 0.7203 → 0.6451 | 0.9885 → 0.9788 | 1405 / 1633 / 1652 | 0.9851 → 0.9911 | 3 / 3 / 3 |
| 2025 | **0.5621 → 0.7118** | **0.3161 → 0.4367** | 0.9879 → 0.9838 | **1830 / 1049 / 1903** | **0.9251 → 0.9943** | 5 / 5 / 5 |

Direction-blind reading: **2025 — the repaired year — improves on every shape
statistic**: hourly r +0.15, daily r +0.12, monthly seasonal r 0.925 → 0.994,
and the hour-of-day swing recovers from 1,049 MW (the truncated 3-plant fleet
physically could not produce the real diurnal swing) to 1,903 MW against a
measured 1,830. **2023/2024 shape degrades moderately** (hourly r −0.048 /
−0.039, daily r −0.085 / −0.075): re-allocating those years' budgets to the
930 monthly levels shifts within-year timing away from the 923 monthly pattern
the control followed. Reported at full magnitude; not patched (rule 14).

### §4.4 Scorecards and side effects at full magnitude (G6/G7, rule 14)

| | control | arm |
|---|---|---|
| **Determination** | **CALIBRATED** (C3c the lone ledgered caveat) | **NOT-YET** (`price_mean`, `price_tail`) |
| C1 / C2 / C3b / C4 / C6 / C8 | PASS | PASS |
| C3a mean LMP | +5.3 / −2.6 / −8.1 % (all PASS) | +6.8 / −1.7 / **−10.8 % FAIL (2025)** |
| C3c >$300 h (model vs RT) | 1/0/0 vs 10/13/42 — CAVEAT (ledgered) | 1/0/0 vs 10/13/42 — **FAIL** |
| mean λ $/MWh | 33.96 / 37.13 / 61.04 | 34.45 / 37.46 / 59.24 |

**C3c's evidence is BIT-IDENTICAL between the arms** (1/0/0 h in both). It
reads FAIL on the arm only because the rule-22 standing rule's guard (a) —
*lone failure only* — is silenced by the C3a failure. No C3c evidence moved.

**The C3a story is the nyiso-108 pattern, transposed to 2025.** Removing
phantom 2023/2024 hydro lifts those years' prices (+$0.49 / +$0.33): 2023
+5.3 → +6.8 % (in-band — nyiso-109's zonal margin anchor, which closed the
+10.2 % breach the 2026-07-31 arm exposed, holds), 2024 **improves** −2.6 →
−1.7 %. Restoring the missing 3.01 TWh of real 2025 hydro softens 2025 by
−$1.79/MWh: −8.1 → **−10.8 %**, 0.8 pp past the −10 % band edge. The
truncated input was **masking ~2.7 pp of a real, pre-existing 2025
under-pricing**: the keeper's in-band C3a-2025 was partly an artifact of
3 TWh of missing zero-MC energy being priced by fossil units. The root cause
is not the hydro input — it is the **already-open 2025 offer-level object**
(`DECISION-CARD-nyiso148-2025-level-remainder-2026-08-21.md`, owner Q1
pending: $6.57 of an $8.07/MWh gap), whose true magnitude this repair
reveals to be ~$1.79/MWh larger than the truncated-input keeper showed.

Side effects: fossil displacement is 1:1 with the hydro delta in every year —
2023 +1.57 TWh gas (CC_REGULAR +0.69, CC_CHP +0.45, ST_GAS +0.33), 2024
+1.11 TWh gas, 2025 −3.15 TWh fossil (CC_REGULAR −1.29, ST_GAS −0.75,
CC_CHP −0.73, CT/ST/oil/import the remainder). Slack and dump 0.0 in both
arms.

## §5 — Determination under the pre-registered promotion rule: NO PROMOTION — ESCALATED TO THE OWNER

Prereg §5: promote iff G1, G2, G6, G8 all pass. **G1 FAILS** (HEAD drift live
on 2023/2024, degenerate-reshuffle class) and **G6 FAILS** (determination
downgrade CALIBRATED → NOT-YET on C3a-2025). Per the prereg's §5.3 — *any
determination downgrade or loss of the frontier basis escalates to the owner
and is never self-adjudicated* — **the keeper is UNCHANGED**
(`2026-08-22-nyiso-152-duty-complete`), no re-key, no D-5(b) write, the
frontier block untouched, and the decision is the owner's. Both runs are
registered either way (rule 15).

**What rule 14 says, and what it does not.** The basis of this repair is
INPUT ACCURACY: the truncated 2025 vintage is *wrong* (2.0 % plant retention,
falsified independently by P-63 to within 0.6–1.3 % of EIA-930), and the
worse 2025 fit under the accurate input is a **discovered defect** in the 2025
price level, not a reason to keep the wrong input. This session does not
revert the finding, soften the backfill, or add any compensating adjustment —
and equally it does not overwrite a CALIBRATED, frontier-ratified keeper with
a NOT-YET run on its own authority. The precedent is exact: nyiso-108's
identical trade (C3a-2023 +8.6 → +10.2 %) was promoted only by **explicit
owner override** of its own prereg, and the successor session (nyiso-109)
closed the exposed root cause on measured grounds within a day.

**The owner's decision, framed:**

1. **Promote the arm** (the nyiso-108 precedent): accept NOT-YET on C3a-2025
   −10.8 % as a discovered defect carried openly, with the 2025 offer-level
   object (already owner-court) as the named successor — its magnitude is now
   known to be ~$1.79/MWh larger than the truncated-input baseline showed.
   This is the rule-1/rule-14 structurally-faithful choice; it costs the
   CALIBRATED determination and the frontier basis until the 2025 level
   object closes.
2. **Hold the keeper, charter the 2025 level root cause first** (the
   sequencing choice): the keeper stays CALIBRATED on the truncated input —
   with this finding on record explicitly stating that its C3a-2025 −8.1 %
   carries ~2.7 pp of truncation masking — and the repair is re-armed
   in the same A/B as the 2025 offer-level fix, where the two together are
   expected to land in-band. Honest only because this finding is registered
   and the masking is now on the record.
3. Also on the table: the **G1 drift** — the control (registered,
   CALIBRATED, determination-identical to the keeper criterion-for-criterion)
   is a valid re-key target under the nyiso-128b stale-baseline precedent if
   the owner wants the designated keeper to reproduce at HEAD.

## §6 — What this changes on the record

* **Registered:** `2026-08-25-nyiso-155-hydro-control` (CALIBRATED) and
  `2026-08-25-nyiso-155-hydro-repair` (NOT-YET), full 2023–2025 span each
  (rule 16), bundles `nyiso155_hydro_control` / `nyiso155_hydro_repair`.
  Automatic top-15 retention pruned `2026-08-19-nyiso-146b-reserve-duty` and
  `-reserve-inert`.
* **Keeper UNCHANGED**; no shard re-key; frontier block untouched; the
  promotion decision is escalated to the owner (§5).
* **Matrix:** `hydro_vintage_input_repair` NYISO cell **K → O** (LIVE,
  unrefuted, armed on no keeper — the nyiso-128 solar-basis convention), with
  the silent de-arm and this A/B in the evidence. The keeper never stopped
  being *scored* correctly — the cell letter was what had gone stale.
* **The silent de-arm is on the record** (§2): an armed keeper mechanism
  left the lineage with no decision, because the lineage-fidelity checks are
  blind to `solve_and_persist` kwargs. Successor guard (own charter): extend
  keeper-lineage fidelity checks to the full kwarg surface.
* **The 2025 offer-level object's true magnitude** is ~$1.79/MWh larger than
  the truncated-input baseline showed (§4.4) — recorded for the owner's
  pending Q1 on `DECISION-CARD-nyiso148-2025-level-remainder`.
* **No out-of-training year touched**; the holdout spend freeze is ACTIVE and
  untouched; zero fitted scalars; no new `ScenarioConfig` field; no derive
  script edited.

---

Evidence in-repo: `results/calibration/_nyiso155_hydro_repair_ab.json`,
`scripts/probes/_nyiso155_hydro_repair_ab.py`,
`results/calibration/PREREG-nyiso155-hydro-truncation-repair-2026-08-25.md`,
registered bundles `nyiso155_hydro_control` / `nyiso155_hydro_repair`.

---

## §7 — ADDENDUM 2026-08-25: the escalation is RESOLVED — OWNER RULED PROMOTE

Owner decision on the §5 escalation, same day, verbatim: *"Is this a
recommended keeper candidate? If so plz promote. If structural integrity
improves but gates regress that may still be a keeper.."* The arm **is** the
recommended candidate on the rules-14+1 basis (§5), and it is **PROMOTED**:
NYISO keeper → `2026-08-25-nyiso-155-hydro-repair`, superseding
`2026-08-22-nyiso-152-duty-complete` — the nyiso-108/nyiso-120 override class,
recorded as an override, never as the prereg's verdict. The determination
**NOT-YET is written explicitly on owner instruction** (nyiso-120 precedent):
the D-5(b) worse-determination stop fired, was escalated (§5), and this ruling
resolves it — nothing was silently written. Executed in the promotion commit:
keeper shard re-key + chained promotion note; `calibration-complete.json`
NYISO entry re-keyed with the explicit NOT-YET; registry sidecar re-defined as
KEEPER with a `market_story`; matrix cell `hydro_vintage_input_repair`
**O → K**; shard keeper/gates stamps and the §5.5 prose header re-stamped
(prior records preserved verbatim); `status/NYISO.js` rebuilt
[NYISO: NOT-YET]; `audit_keepers --iso NYISO` run via the keeper-auditor.
**Frontier:** the 2026-08-23 ratification's basis keeper is superseded and its
CALIBRATED premise does not hold on the new keeper — the ratification record
is preserved verbatim as the owner-act genealogy and the frontier status
question returns to the owner. **Named successor, unchanged:** the 2025
offer-level object (`DECISION-CARD-nyiso148-2025-level-remainder`, owner Q1
pending), whose true magnitude this repair revealed; the hydro input is now
correct and must not be re-tuned to bury that miss (rule 14).

# PREREG — caiso-156: the shared CT heat-rate derive's hour-grain physical-band screen (the caiso-146 §2.4 meter-data defect, chartered cross-ISO)

**Written and committed BEFORE the derive script is edited and BEFORE any
artifact is re-derived or arm solved** (house rule; caiso-139..155 precedent).
Everything below — the exclusion rule, expected directions, solve scope, gates,
kill conditions — is fixed at this commit. No gate is added, dropped or
re-thresholded after a derive or a solve.

* **Session:** caiso-156 (CAISO/cross-ISO calibration).
  **Branch:** `claude/caiso-156-ct-heat-rate-sl7uv1`.
* **Charter:** the caiso-146 §2.4 side finding, filed there as a cross-cutting
  item ("an hour-grain screen would move three committed keepers' inputs, so it
  needs its own charter, not a CAISO calibration session") and carried unowned
  through caiso-147..155. This session is that charter.
* **This is an INPUT CORRECTION (the caiso-152/153 class), NOT a mechanism
  cell.** No matrix cell is re-tested and no new `ScenarioConfig` field exists.
  Matrix duty is note/evidence updates on the `measured_ct_heat_rates` row plus
  rule-15 dashboard registration of both arms per solved ISO (rule 28b).
* **Rule 23 `[R-FROZEN-DERIVE]`:** the re-derivation commit cites the
  METER-DATA defect below — never any residual. No residual moved anywhere in
  the selection of this lever: it was pre-measured at caiso-146 §2.4 before any
  of the current keepers existed.
* **Rule 22:** solve years are 2023 2024 2025 ONLY. PJM and NEISO hold
  `complete` (validation tier), CAISO and NYISO hold NONE, no ISO holds
  `final`, and the holdout spend freeze (`holdout-freeze.json`) is ACTIVE and
  outranks everything. `--holdout-authorized` is not passed; no out-of-training
  year is solved, scored or registered; no marker is written.
* **Rule 25 `[R-ISO-SCOPE]`:** the screen is ISO-generic data integrity inside
  the shared derive (the caiso-147 "gate fixed ISO-generically" class), carries
  zero parameters of its own, and transfers no verdict: each solved ISO's A/B
  is adjudicated on its own bundle only.

---

## 1. The defect (measured, carried since caiso-146) and the rule that fixes it

`derive_campd_ct_heat_rates.py` declares a physical plausibility band
`[6.0, 25.0]` MMBtu/MWh — "a DATA-INTEGRITY guard on the meter, not a tuning
knob: below ~6.0 the row is a mis-tagged combined cycle, above ~25.0 it is a
broken heat-input or gross-load channel" — but applies it only to the PLANT
AGGREGATE. A loaded hour whose own implied rate is below 6.0 (physically
impossible for a simple-cycle machine: > 56 % HHV efficiency) is a meter
defect by the derive's own declaration, yet it enters
`sum(heatInput)/sum(grossLoad)` and dilutes the unit's rate LOW without ever
tripping the plant flag. caiso-146 §2.4 measured the bias in every ISO probed
and Delano Energy Center (58122) is the poster child: loaded-hour rates p05 =
0.81 / p25 = 3.20 against a median of 7.89, dragging the plant to 6.5725 —
below any real simple-cycle machine, above the 6.0 plant floor, flag `ok`.

**The exclusion rule, frozen here, ZERO new parameters:**

1. Inside each unit's loaded window (unchanged: hours ≥ 0.8 × its own p95
   gross load), an hour is EXCLUDED from the heat-rate sums iff its hourly
   implied rate `heatInput/grossLoad` falls outside the derive's own declared
   physical band `[_HR_MIN, _HR_MAX]` = [6.0, 25.0] — BOTH sides, the band
   applied at the grain where the defect lives. No new constant is introduced;
   the plant-aggregate flag stays exactly as it is.
2. The existing trust gate `_MIN_LOADED_HOURS` (50) is evaluated on the
   IN-BAND (valid) loaded hours: a unit whose meter is so defective that fewer
   than 50 trustworthy loaded hours remain has no measured rate and drops,
   exactly as a unit that never reached the loaded window drops today. A plant
   losing all units falls back to eGRID (the loader's existing behaviour for
   absent rows).
3. Nothing else changes: cap percentile, loaded fraction, generation weights
   (all-hours `gross_mwh`, unchanged by the screen), parasitic net conversion,
   plant-aggregate band flag, and the `flag == "ok"` application rule are all
   untouched.

The window/cap selection is deliberately left on raw `grossLoad` (a gross-load
meter fault is a different, unmeasured defect; this screen is scoped to the
heat-input channel the caiso-146 evidence names).

## 2. The pre-derive measurement (probe, read-only, run before this commit)

`scripts/probes/_caiso156_hourly_band_screen.py` (committed with this prereg)
extends `_caiso146_hourly_hr_integrity.py` to BOTH band sides, all six
committed artifacts, the valid-hours consequence, and a faithfulness check —
its as-is reconstruction reproduces every committed `heat_rate_gross` to
≤ 5e-5 in all six ISOs, so the screened preview is computed by the derive's
own recipe. Transcript: `results/calibration/PROBE-caiso156-band-screen-2026-08-02.txt`.

| ISO | sub-6.0 loaded hours | > 25.0 loaded hours | applied map (net, cap-wt) | applied map (net, gen-wt) | units dropping < 50 valid h |
|---|---|---|---|---|---|
| CAISO | 2,537 / 73,346 (3.46 %) | 0 | 9.6603 → 9.8362 (+0.176) | 9.0601 → 9.1789 (+0.119) | 0 |
| NYISO | 3,704 / 151,014 (2.45 %) | 0 | 12.0769 → 12.4355 (+0.359) | 10.6822 → 10.7950 (+0.113) | 1 (Gowanus CT03-6) |
| PJM | 8,435 / 544,586 (1.55 %) | 252 (0.046 %) | 11.5817 → 11.6511 (+0.069) | 11.2841 → 11.3601 (+0.076) | 0 |
| MISO | 1,290 / 433,271 (0.30 %) | 66 (0.015 %) | 11.8677 → 11.8972 (+0.030) | 11.4266 → 11.4390 (+0.012) | 1 |
| NEISO | 311 / 15,329 (2.03 %) | 0 | 9.6291 → 9.8006 (+0.171) | 9.1828 → 9.2771 (+0.094) | 1 |
| ERCOT | 4,141 / 328,302 (1.26 %) | 0 | 11.8796 → 11.9425 (+0.063) | 11.6779 → 11.7370 (+0.059) | 0 |

The caiso-146 §2.4 low-side numbers reproduce exactly (3.46 / 2.45 / 1.55 /
0.30 %). The high side exists only in PJM (252 h) and MISO (66 h) and is an
order of magnitude smaller than the low side everywhere it exists. Largest
applied-row movers: CAISO Delano 6.5725 → 9.4213 (+2.85, back inside the
physical band), PJM Darby 10.5885 → 12.6954 (+2.11), NYISO Gowanus 15.2804 →
16.9538 (+1.67, one unit dropped) / Narrows 15.7537 → 16.7814 (+1.03), NEISO
Potter 8.8734 → 9.2711 (+0.40).

## 3. Keeper arming — VERIFIED per bundle (never assumed), and the solve scope it fixes

Read from each committed keeper bundle's `meta.json` this session:

| ISO | keeper | arms `measured_ct_heat_rates`? | channel |
|---|---|---|---|
| CAISO | `2026-07-31-caiso153-reid-b` (`caiso153_reid_B`) | **YES** | `coal_prb_sigmoid_overrides` |
| PJM | `2026-07-31-pjm-143b-hy-level` (`pjm143_hy_level_B`) | **YES** | `coal_prb_sigmoid_overrides` |
| NYISO | `2026-08-01-nyiso109-zonal-margin-anchor` (`nyiso109_zonalanchor_B`) | **YES** | `coal_prb_sigmoid_overrides` |
| NEISO | `2026-07-31-neiso-72-hy-window` (`neiso72_hy_window_B`) | **YES** | `coal_prb_sigmoid_overrides` |
| MISO | `2026-07-31-miso-109b-hy-level` (`miso109_hy_level_B`) | **NO** — flag absent from meta | — |
| ERCOT | `2026-08-01-ercot149-gas-event-cap` | inert by wiring (ERCOT-146, cell `I`) | — |

**The handoff premise "moves THREE committed keepers' inputs" is corrected on
the record to FOUR:** NEISO armed the artifact at neiso-70 (2026-07-31, the
same day as, and after, the caiso-146 measurement that counted three), and the
probe now measures NEISO's bias at cap-wt +0.171 — the same order as CAISO's
+0.176 and larger than PJM's +0.069. A keeper-consumed input that moves this
much cannot be corrected blind.

**Solve scope, fixed here:**

* **A/B lanes (2 arms × years 2023 2024 2025, one bundle per arm, rule 16):
  CAISO, NYISO, PJM, NEISO** — every ISO whose keeper consumes the artifact.
* **MISO: artifact re-derived, NO solve.** Its keeper does not consume the
  artifact (verified above), so no keeper input moves; arming the flag in MISO
  would be TESTING the mechanism there (matrix cell `U`, MISO's own lane,
  which currently has no live lever) — out of this charter.
* **ERCOT: artifact re-derived, NO solve** (inert by wiring, ERCOT-146; the
  artifact is evidence for the ERCOT-147 successor lane and must stay
  consistent with the fixed derive).
* **NEISO scope guard:** this lane touches ONLY the CT heat-rate artifact via
  the keeper's already-armed flag. The caiso-154 §F offer-surface
  tail-sensitivity item and everything else in the NEISO frontier charter
  remain owner-gated and untouched (`neiso_offer_surface_conditional` stays
  False/dormant; no NEISO offer-surface derive is run).
* **NYISO scope guard:** nyiso-110's pre-registered peak-half spin-online arm
  is a different, ACTIVE lane. This session replays the nyiso109 keeper recipe
  byte-identically (zero flag deltas) and arms nothing from that prereg; no
  collision.

## 4. Arms — zero config deltas; the delta is the artifact bytes

Both arms of every ISO replay the CURRENT keeper's own `meta.json` at HEAD via
`scripts/replay_keeper.py`, `--years` defaulted to the bundle's [2023, 2024,
2025], years sequential inside each invocation (rules 12/16), ONE solve
running at a time on this 15 GB box (caiso-146..155 gotcha; the caiso-146
concurrency licence is NOT exercised).

| ISO | arm A (control) | arm B (treatment) |
|---|---|---|
| CAISO | `results/calibration/caiso156_meter_control_A` | `results/calibration/caiso156_meter_screen_B` |
| NYISO | `results/calibration/nyiso_c156_meter_control_A` | `results/calibration/nyiso_c156_meter_screen_B` |
| PJM | `results/calibration/pjm_c156_meter_control_A` | `results/calibration/pjm_c156_meter_screen_B` |
| NEISO | `results/calibration/neiso_c156_meter_control_A` | `results/calibration/neiso_c156_meter_screen_B` |

* **Arm A** solves at the PRE-FIX tree: committed artifact bytes exactly as on
  `origin/main` today (the caiso-146-era derive output). It is the same-HEAD
  zero-delta control D-13 makes mandatory (caiso-155 §D: committed keeper
  bundles do NOT reproduce in this container — a committed-vs-B comparison
  would conflate vertex/stack drift with the lever).
* **Arm B** solves at the POST-FIX tree: HEAD plus exactly one commit carrying
  the derive-script screen + the six re-derived artifacts (+ their `_units`
  detail files). That commit touches NOTHING under `src/` and no other
  `scripts/` consumer — solver bytes identical across arms, verified before
  arm B starts (`git diff --stat` of the fix commit shows only
  `scripts/data/derive_campd_ct_heat_rates.py`,
  `data/raw/_processed-legacy/campd_ct_heat_rates_*` and docs).
* Both arms pass `--set measured_ct_heat_rates=true` — VALUE-IDENTICAL to the
  keeper's own channel state (verified §3), so the merged config is unchanged;
  the override exists solely so `replay_keeper` mints a fresh dated run id
  instead of restoring the keeper's date (its zero-override date-restore
  branch), keeping A and B honestly dated as new runs. Config equality between
  arms is gate K4.
* Solve order: all four A arms first (NEISO → CAISO → NYISO → PJM), then the
  fix commit, then the four B arms in the same order. If the session dies
  mid-way, completed arms register and the FINDING records the cut.
* `legitimacy_diagnostics.json` is generated IN-SESSION immediately after each
  arm's solve, from the arm bundle's own real `floors/*_P?.npz`
  (`scripts/legitimacy_diagnostics.py --bundle <arm> --iso <ISO> --json-out
  <arm>/legitimacy_diagnostics.json`) — never post-hoc, never from a rebuild,
  never from a replay of a different bundle (caiso-155 A1b/D-13). Expected
  ADDITIVE vs the committed keepers' artifacts: the caiso-155 plant-set fix
  makes firm-import D-2/D-4 rows visible (class `""`, exempt mechanisms) in
  CAISO/NYISO arms. A C7/C8 verdict flip attributable to those rows is a REAL
  finding and is reported as such, not dismissed as scorer noise.

## 5. Predicted directions — frozen before any derive or solve

The screen RAISES CT heat rates everywhere (§2: every measured energy-weighted
and applied-map delta is positive). SRMC moves by ΔHR × gas ≈ +$0.3/MWh at the
class level (gen-wt +0.08..0.12 × $2.2-3.5/MMBtu), with plant-level outliers
to +$7-10/MWh (Delano, Darby, Gowanus/Narrows).

1. **CT_PEAKER energy FALLS or is flat in all four solved ISOs** (dearer
   class, all four under- or correctly-produced). Predicted magnitudes:
   CAISO −0.00 to −0.15 TWh/yr (the caiso-146 full −0.884 gen-wt swap moved
   the class +0.2..+0.6 TWh/yr; this claws back ~13 % of that markdown);
   NYISO/NEISO smaller; PJM smallest (+0.076 gen-wt on an 11.28 base,
   0.7 %) — **PJM may be score-inert** (K3 reports it either way).
2. **No displaced-class sign prediction** is made beyond "the energy returns
   to the next merchant class (CC_REGULAR) or imports" — reported both ways
   (caiso-146 §5.3 discipline).
3. **λ / C3a nudges UP in peak hours** (dearer peakers set price in fewer,
   dearer hours). **CAISO C3a-2025 is a ledgered +11.0 %-high caveat and this
   moves it ADVERSELY (up).** Stating before solving: the expected magnitude
   is well under the ledger's 1.0 pp materiality trigger (the full caiso-146
   swap, 7.5× larger gen-wt, moved C3a-2025 only 0.3 pp); if it nonetheless
   moves ≥ 1.0 pp, the pre-committed response is the ledger discipline —
   report, LOYO-score (§7), never tune. The correction is chartered on rule
   14 accuracy and is NOT a C3a lever; an adverse C3a move does not revert it
   (rule 14: worse fit = discovered bug elsewhere, the accurate input stays).
4. **C3c tail counts essentially unchanged** in all four (a +$0.3/MWh class
   SRMC shift cannot manufacture or delete $200+ tail hours; NYISO's C3c is
   ledgered ahead of nyiso-110 and this arm must not be read as its lever).
5. **C7/D-1 CT_PEAKER shape moves little; C8 forced share may RISE slightly
   in NEISO** (neiso-70 measured the same mechanism's arming collapsing the
   CT floor share by making CTs cheaper; a partial claw-back makes the floor
   marginally more load-bearing again). A C8 breach of the 0.15 peaker cap in
   any arm is a protective FAIL (§6).
6. **MISO/ERCOT artifacts change as measured** (§2, +0.030/+0.063 cap-wt) with
   zero solve consequences this session.

## 6. Gates

Construction gates (all must pass, else the arms are not comparable):

* **K1 — artifact fidelity.** Arm A's tree carries the pre-fix artifact bytes
  (git-clean at the pre-fix HEAD); arm B's tree carries the post-fix bytes
  (git-clean at the post-fix HEAD). Recorded per arm: `git_sha` in meta.json +
  the artifact file's md5 at solve time, stated in the FINDING.
* **K2 — control integrity.** Arm A reproduces its ISO's committed keeper
  scorecard: same determination, same per-criterion statuses (values may
  drift; D-13 says vertices do). A status flip in a CONTROL is a stop-the-lane
  event for that ISO: reported, not scored against the lever.
* **K3 — liveness, reported not gated.** `max |Δ CT_PEAKER class-hour MW|`
  between arms, per year. Unlike a mechanism A/B there is no `I` verdict at
  stake — an input correction ships regardless — but a score-inert PJM/etc. is
  stated plainly so the registration does not oversell it.
* **K4 — config equality.** Arm A and arm B `run_config.json` differ only in
  provenance (timestamp, git_sha, note, basis_sha). Any ScenarioConfig-field
  diff fails the pair.
* **K5 — year span.** Every bundle carries exactly [2023, 2024, 2025].
* **K6 — the correction is not driven by drops.** The three dropped units
  (Gowanus CT03-6, one MISO unit, one NEISO unit) are each < 1 % of their
  ISO's applied-map energy; the FINDING reports each ISO's applied-map delta
  recomputed WITH the dropped units retained (screened rates, no trust gate)
  and it must agree in sign and to within 25 % in magnitude — else the screen
  is doing selection work beyond meter hygiene and the lane stops.

Determination gates, per solved ISO (baselines: that ISO's committed keeper
scorecard + its committed `legitimacy_diagnostics.json`):

* **Protective:** C7 `profile_r ≥ 0.80` / `cv_ratio ≥ 0.50` where gated (C7 is
  scorer-skipped for NEISO — never quoted as passed there, rule from
  neiso-70); C8 forced share ≤ 0.15 (peaker cap) on gated classes; D-4
  off-window binding 0.000 on every non-exempt mechanism.
* **Scored:** C1, C2, C3a, C3b, C3c, C4 + determination, reported per arm per
  year, movement in both directions.

## 7. Promotion rule, LOYO, and what a bad result does NOT do

* **The corrected artifacts ship regardless of arm outcomes** (rule 14): they
  are the accurate input. A degraded score is a discovered-bug signal for a
  root-cause lane, never a revert of the screen.
* **Per-ISO keeper promotion of arm B** happens iff: K1–K6 pass, arm B has no
  protective FAIL, no load-bearing criterion flips PASS → FAIL vs arm A, and
  the determination is no worse than the committed keeper's. Otherwise the
  committed keeper STANDS (on the stale artifact, disclosed on the dashboard
  note) and the mismatch is filed as that ISO's lane item.
* **LOYO (rule 22): the screen has zero fitted parameters**, so
  leave-one-year-out reduces to the no-held-out-degradation check
  (ERCOT-145 A-2 / caiso-146 §8 precedent): promotion of any arm B whose
  |ΔC3a| ≥ 1.0 pp in any year — or any load-bearing criterion band change —
  requires the three per-year deltas to agree in sign with the pooled delta
  (no single year drives the movement). Computed from the registered bundles'
  per-year metrics; no extra solve.
* **The two CAISO ledgered caveats (C3a-2025, C3c) are not re-litigated**: no
  new evidence against the named caiso-140..144 cells is claimed, and neither
  caveat is quoted as closed or as justification for anything here.

## 8. Deliverables (rule 15 / 28b), regardless of verdict

* All EIGHT arm bundles registered on the backcast dashboard
  (`dashboard_add_run --bundle <ABSOLUTE> --label ...`), sidecars +
  `runs/<id>.js` payloads + changed `bench/` committed; payload commits pushed
  via `git push` after a fresh rebase on origin/main (413/pack discipline),
  `push_files` for small text; blob verification after any ≥300-line push
  (rule 27).
* Labels: CAISO `caiso156 meter control A` / `caiso156 meter screen B`; NYISO
  `nyiso caiso156 meter control A` / `... screen B`; PJM `pjm caiso156 meter
  control A` / `... screen B`; NEISO `neiso caiso156 meter control A` /
  `... screen B`. No other lane's session numbering is minted.
* `legitimacy_diagnostics.json` per arm, generated in-session (§4).
* The `measured_ct_heat_rates` matrix row note + per-ISO evidence citations
  updated in `docs/codebase-site/data/mechanism-matrix.js` this session; cells
  E/M stay `I`/`U` (no ERCOT/MISO solve; nothing tested there).
* FINDING doc + `docs/calibration-log/` entries (caiso lane + affected-ISO
  logs) with a DO-NOT-REDO section; keeper shard edits + `build_status.py
  --iso` + keeper-auditor agent per promoted ISO only.

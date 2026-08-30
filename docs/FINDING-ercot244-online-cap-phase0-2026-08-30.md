# FINDING — ercot-244 (2026-08-30): the rtolhsl-based energy-side online-capability ceiling is KILLED AT CENSUS — K-B and K-C fire in BOTH scored years (2024: 985 binds, 979 ordinary vs 3 missed; 2025: 865 binds, 858 ordinary vs 3 missed; away-binds over half), the construction itself is VALID (K-A clean, every V-0 anchor exact), and the adjudication is structural: on a composition-correct keeper an AGGREGATE online-capability ceiling has nothing left to grab at the missed events — the ercot-159 reach was an artifact of that era's composition error — while its binding mass lands in ordinary hours the driver says are slack

**Session ercot-244, branch `claude/ercot-244-online-cap-xi7kvo`. ZERO-SOLVE**
— every number below is read from the FORWARD keeper's committed sidecars
(`results/calibration/ercot234_eastex_identity`), the committed actuals, the
EIA-930 wide extract and the measured ORDC/reserves series. Precommit
`docs/PRECOMMIT-ercot244-online-cap-phase0-2026-08-30.md` pushed +
blob-verified (52ab16e5, sha256 ee49f6ff) BEFORE any measurement; probe
`scripts/probes/ercot244_online_cap_phase0.py` →
`results/calibration/ercot244_online_cap_phase0.json` (committed). **The
Phase-1 A/B license is NOT spent** — no lever, no solve, no ScenarioConfig
change, no matrix verdict move; the two-config keeper untouched. One
implementation repair, construction unchanged (the precommit's amendment
convention): the fast-product held MW is summed over the time-DISJOINT
`X_withheld` / `X_released` window families (`model/reserves/spec.py` ~1620 —
the 2024-08-01 ECRS reform and RTC+B gates split a straddling year's product
into disjoint-window families; the plain-name assert would have missed 2025's
un-split `ECRS` and under-counted post-reform 2024).

## 0. Verdict in six lines

1. **K-C fires in both scored years, on all three legs.** 2024: 979 ordinary
   binds (bar 150), ordinary > missed by 979:3, away-binds 528 of 985
   (> ⅓). 2025: 858 / 858:3 / 424 of 865. The ercot-159 over-fire signature
   — 523 ordinary binds that cascaded to fabricated scarcity in-solve — is
   reproduced on the current keeper at roughly double the scale, before any
   LP was built. That is exactly what this Phase-0 existed to detect.
2. **K-B fires: reach 8.3 % / 9.7 %** (3 of 36 missed hours in 2024, 3 of 31
   in 2025), far below the 0.20 floor in both years. The instrument cannot
   address the object.
3. **K-A is CLEAN, which makes the kill an adjudication, not a data
   artifact:** CAP ≤ 0 in zero hours; `P_slow` alone exceeds CAP in 0 (2024)
   / 1 (2025) hours. The ceiling is a sane, physically-scaled series (CAP
   mean 43.9 / 47.1 GW vs model fast-tier point mean 38.6 / 39.8 GW; the
   model sits ~4.7–6.5 GW BELOW it at the median hour).
4. **Every V-0 anchor reproduced exactly:** model tails 22 / 1 and actual
   tails 53 / 31 to the hour; EIA-930 lag-0 alignment (corr 0.9996/0.9998);
   and the rtolhsl hod-17–21 means land on the card's figures to the
   hundredth (58.873 / 62.641 / 67.806 GW vs 58.87 / 62.64 / 67.81) — the
   series identity is beyond question.
5. **No disclosed variant changes the shape.** D-V1 (credit-augmented,
   +LR +storage awards ≈ +3 GW looser): binds drop to 210 / 314 but the
   missed-set reach drops to 0 / 2 while 209 / 309 stay ordinary. D-V2 (no
   OTH/WAT subtraction): 834 / 833 binds, 829 / 826 ordinary, missed 2 / 3.
   The ordinary-dominated shape is invariant to every loosening direction
   measured.
6. **Disposition per the precommit's kill rule:** record and STOP. No
   Phase-1 precommit, no A/B, nothing armed. Matrix cell
   `energy_online_capability_cap` stays **R** with this census appended as
   an evidence note (the ercot-243 note-append precedent); calibration-log
   entry ercot-244; the forward span's ledgered C3c (2024 22/53, 2025 1/31)
   is carried at full magnitude, un-repaired by this lane.

## 1. The census record (full detail in the committed JSON)

| measure | 2023 (report-only) | 2024 | 2025 |
|---|---|---|---|
| missed set \|M\| (actual > $200 ∧ model ≤ $200) | 115 | 36 | 31 |
| binds \|B\| (F > CAP, finite cap) | 1,818 | 985 | 865 |
| B ∩ M | 6 | **3** | **3** |
| B ∩ hit tail | 0 | 0 | 0 |
| B ∩ ordinary (actual < $150) | 1,804 | **979** | **858** |
| away-binds (model_dw ≥ actual) | 1,048 | 528 | 424 |
| reach \|B∩M\|/\|M\| | 0.052 | 0.083 | 0.097 |
| depth p50 at B∩M / B∩ordinary (MW) | 1,993 / 1,350 | 683 / 1,316 | 3,635 / 1,708 |
| depth p90 at B∩ordinary (MW) | 3,343 | 3,868 | 4,497 |
| P_slow alone > CAP (K-A ii) | 39 | 0 | 1 |
| CAP ≤ 0 hours (K-A i) | 0 | 0 | 0 |
| NaN-cap hours (RTC+B tail, excluded) | 0 | 0 | 648 |

Levels (GW, annual means): CAP 41.0 / 43.9 / 47.1; F 37.8 / 38.6 / 39.8
(P_slow 33.3 / 32.8 / 33.4 + held_fast 4.5 / 5.8 / 6.4). The six 2023 and
six 2024/2025 missed-hour bind records (hour, actual, model, F, CAP, depth)
are itemized in the JSON's `bind_hours_missed_hit`.

D-V3 (reserve-cap nesting at B hours): the armed credit-netted RTOLCAP cap
holds p50 slack ≈ 1.4 GW against the model's held fast reserves at the
binding hours, with p10 NEGATIVE (−1.6 GW) in 2024/2025 — at a tenth of the
binding hours the armed reserve cap is itself at or past its own margin, so
part of the energy-side ceiling's would-be regime is already owned by the
armed instrument (the K-B "already owned" face, measured).

## 2. The structural adjudication — why an aggregate ceiling cannot express this object

1. **At the missed events the model sits UNDER the measured ceiling** (33 of
   36 missed hours in 2024, 28 of 31 in 2025 do not bind). This is not a
   looseness accident; it is arithmetic on a composition-correct keeper.
   The forward keeper passes C1/C2/C3a on its span, so its slow-thermal
   utilization tracks reality's slow-thermal generation hour by hour — and
   reality's own generation respects reality's own online HSL by physics.
   A ceiling on UTILIZATION (dispatch + held reserves ≤ online capability)
   can therefore only bind where the model's composition deviates ABOVE
   reality's online total. The card's defect is not utilization — it is
   **HEADROOM**: the LP prices 15.3–17.5 GW of supply-curve room above the
   operating point at marginal cost where reality's online cushion was
   0.92–2.80 GW with 17–23 GW cold. An aggregate utilization cap does not
   touch the headroom's PRICE or REACHABILITY at hours where utilization
   fits under it — which, on a calibrated model, is nearly every event
   hour.
2. **The ercot-159 reach is thereby explained, not contradicted.** The
   envelope reached the 2023 tail ($105 → $813 at the missed set) on the
   ercot158-era keeper because THAT model over-dispatched slow thermal at
   events (C3a-2023 −24.5 % era, composition wrong); the cap bit into real
   utilization excess. Seventeen promotions later the composition error is
   gone, and with it the reach: 3 hours a year. The mechanism family's
   apparent power was borrowed from a defect that has since been repaired
   by other means.
3. **The ~1,000 ordinary binds per year are the real, standing measurement
   this census leaves behind:** in ~11 % of forward-span hours the model's
   slow-fossil+nuclear dispatch plus thermal-held fast AS exceeds ERCOT's
   ENTIRE measured online capability net of non-thermal generation, by
   1.3–1.7 GW at the median bind and ~4 GW at p90. Because every
   approximation in CAP is loose-side (curtailment headroom, idle storage
   capability, the whole online quick-start HSL ride inside it), the
   violation is real a fortiori: at those hours the model leans on MORE
   slow-thermal capability than the real system had online in TOTAL. That
   is the ercot-159 postmortem's "commitment level in ordinary hours"
   object, now measured on the current keeper with a cleaner instrument —
   the model runs a slow-heavy composition in ordinary hours where reality
   committed lean and met the margin with quick-start/storage/import
   routes. Arming the ceiling would reprice ~1,000 such hours (528/424 of
   them already at-or-above actual) to move 3 — indefensible under
   `[R-FLOOR-WINDOW]` and refuted before the LP.
4. **Conclusion: the aggregate online-capability ceiling FAMILY — any RHS
   variant (SCED conditional envelope, rtolhsl-derived hourly, credit
   -augmented, subtraction variants) — is the wrong instrument FORM for the
   forward-span C3c object.** The defect the object needs expressed is
   which COLD SLOW UNITS are reachable within the hour (per-unit/per-class
   commitment state, participation), not how much aggregate capability the
   committed fleet may use. That is the same residue ercot-242 recorded
   ("participation/commitment state, not CC/CT offer re-pricing") arrived
   at from the opposite (offer) side.

## 3. What the kill establishes for the queue

* **DO-NOT-REDO entry:** the energy-side AGGREGATE online-capability
  ceiling is adjudicated KILLED-AT-CENSUS on the forward span (this
  finding) on top of its standing R (ercot-159, 2023 in-solve). Do not
  re-open any aggregate-RHS variant — envelope, hourly, credit-augmented,
  subtraction-set — against these residuals or this object without new
  evidence of a different KIND (a changed keeper whose ordinary-hour
  composition no longer violates the measured online total, or a per-type
  measured decomposition that turns the aggregate form into a per-class
  one).
* **The named successor object (unowned, unchartered — an owner decision,
  not this lane's):** a PER-UNIT/PER-CLASS commitment-state representation
  of slow-start reachability — which cold units can come online within the
  hour, at what notice — i.e. the "commitment level in ordinary hours"
  object from the ercot-159 postmortem plus the participation axis from
  ercot-241/242, now supported by §2.3's standing ordinary-hour
  composition measurement. Any such successor is a structural LP change
  needing its own owner charter and precommit; the aggregate row this lane
  tested is measured incapable of standing in for it.
* **The forward span's ledgered C3c stays the honest record** (2024 22/53,
  2025 1/31, ACCEPTED MODEL-CLASS LIMITATION, non-downgrading under rubric
  v3.3) — unmoved by this lane, as the precommit's kill rule requires.

## 4. Owner-visible flags (not executed, per charter)

1. **The 2024/2025 all-resource SCED conduct corpus intake**
   (PRECOMMIT-ercot242 §6) remains the blocker on any forward-regime
   per-type identification — including the per-class decomposition that
   §3's DO-NOT-REDO names as the one route back to a ceiling-shaped
   instrument, and any per-unit commitment-state successor's measured
   basis. SCED-CT is re-fetch-only and CT-only (corpus README read; the
   data is unfetched, not missing). Unchartered — flagged only.
2. The §2.3 ordinary-hour composition measurement (model slow+held above
   the measured online total in ~11 % of forward-span hours) is a standing
   structural observation about the current keeper, recorded here for a
   future owner charter; no lane owns it today.

## 5. Hygiene

Zero-solve; reads ⊂ {2023, 2024, 2025}; no `--holdout-authorized`; the
holdout freeze untouched; ERCOT surfaces only (rule 25); no run produced
(rule 15 not triggered — nothing to register); matrix: evidence NOTE
appended to the `energy_online_capability_cap` cell (verdict R unchanged)
in the ERCOT shard per the precommit §6; calibration-log entry ercot-244;
the ercot-239/240/241/242/243 committed measurements were read, never
re-run; every deliverable pushed on the designated branch with blob
verification on ≥300-line files; no workflows, no CI solves. Environment:
probe run under the keeper-pinned env (python 3.11.15, pandas 3.0.5,
pyarrow 25.0.1, numpy 2.4.6) in a venv outside the project directory.

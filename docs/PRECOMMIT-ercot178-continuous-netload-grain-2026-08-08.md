# PRECOMMIT — ercot-178: CONTINUOUS net-load-percentile conditioning of the ERCOT measured offer-surface family (`ercot_offer_surface_continuous`)

**Session ercot-178, 2026-08-08. Pushed BEFORE any derive, any measurement of the
arm, and any solve.** Charter: the ercot-178 handoff (matrix §5.1 item 21), on
the ercot-177 diagnosis (`docs/DIAGNOSIS-ercot177-c3a2023-anatomy-2026-08-07.md`
§4): the armed measured offer surfaces' conditioning-bin grain dilutes the top
of the distribution — the p97–p100 bin pools 263 hours whose actual prices span
$198–$5,046 (25×) under ONE measured ladder, while the tail population (>$200)
is the top 2.07 % of the year, so the p97 edge sits BELOW the phenomenon.

Object: **C3a-2023** (−32.4 % scorer, keeper
`2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b});
owner standing instruction 2026-08-07: get 2023 under 10 % **while not
disturbing 2024/2025** (both currently PASS C3a; 2025 at −9.1 %). C3b-2023
(0.602) is the same hours. C3b-2024 (0.205) is a DIFFERENT root (frozen ceiling
lane) and is NOT chased here.

Everything below — form, construction, guards, kill gates, falsifiers,
predictions — is fixed HERE and is not renegotiated after the solve.

---

## 0. The rule-28(a) DO-NOT-REDO check (run FIRST, before this precommit)

Performed before anything was designed, per the ercot-177 lesson (a stale cell
mis-chartered that session; the check now precedes pre-registration):

* **No ERCOT cell adjudicates this lever.** `measured_offer_surface` ERCOT is
  `K` (the armed family). No matrix row, no §5.1 item, and no calibration-log
  entry has ever tested a finer or continuous conditioning grain at ERCOT: the
  edges `[0.8, 0.9, 0.97]` in `ercot_offer_surface_netload_pcts` (and the wall
  artifacts' own finer `[0.25 … 0.97]`) came in with their mechanisms and were
  never separately adjudicated. `grep netload_pcts docs/calibration-log*` → no
  hit.
* **The PJM clause in the `measured_offer_surface` row does NOT close this.**
  pjm-141's D-BIN note bars "re-bin it so it binds" *at PJM* — a cell whose
  verdict is `R`, where the proposed re-bin was aimed at the residual with
  unchanged source data. ERCOT's cell is `K`; this session's form (a) has **no
  edge at all** (nothing to re-bin); and the change is a grain refinement of an
  armed keeper mechanism — the exact class of ERCOT-96's day→hour grain switch
  of the ERCOT-95 mechanism (rule 19: a grain switch of one mechanism, never a
  second mechanism).
* Lanes NOT entered (all closed, per the handoff and ercot-177 §6): ORDC /
  RTORPA / RTORDPA (closed against ERCOT's own published adders), reserve level
  (triple-corroborated over-holding), temp-derate (`R`), offline-increment
  slow-start (`I`), event-cap ceiling (FROZEN, memo PENDING), every lane in §9.

## 1. Form election: (a) CONTINUOUS — stated before measuring anything

**Form (a) is elected: remove the step entirely.** The measured ladder is
interpolated continuously in within-year net-load percentile instead of being
stepped across bins.

* **Why (a):** the dilution is caused by the STEP — a single conditional ladder
  averaged across a pooled mixture cannot reproduce either end of the pool
  (diagnosis §4: 2.05× short at p97.0–99.0, 3.75× at p99.0–99.5, 1.75× at
  p99.5–100). Removing the step removes the pooling. Critically, form (a) has
  **no edge to fit**: the corpus's own hours supply the interpolation nodes, so
  there is no free parameter to sweep and the rule-20 hazard (an edge chosen
  against the residual — the ORDC-offset re-sweep failure class) cannot arise.
* **Form (b) (finer edges above p97) is the unexecuted FALLBACK.** It is NOT
  built, NOT derived, NOT measured in this session. If (a) fails its gates, (b)
  requires its own precommit with edges identified from submitted-offer conduct
  structure (never from realized prices) and a pre-stated bin bound — left to a
  successor.

## 2. The mechanism — ONE default-off gate, zero fitted scalars

`ScenarioConfig.ercot_offer_surface_continuous: bool = False`. ERCOT-only.
Default off. Registered in the matrix in the same PR (rule 28(c)).

**What it switches:** the conditioning GRAIN of the four armed members of the
ERCOT measured offer-surface family, coherently — the exact pattern of
`pjm_offer_surface_within_season` (one gate switches the family's conditioning,
with a vintage guard):

| member | stepped artifact (frozen, untouched) | continuous vintage (new) |
|---|---|---|
| conditional peak surface | `offer_curve_dam_hrmults_condbinned.json` | `offer_curve_dam_hrmults_contpct.json` |
| cleared-share wall (boundary + DAM ladder) | `ercot_dam_cleared_share_condbinned.json` | `ercot_dam_cleared_share_contpct.json` |
| RT/SCED leg (ladder; mode `replace`) | `ercot_sced_offer_wall_condbinned.json` | `ercot_sced_offer_wall_contpct.json` |
| fast-start pool (pool_frac + ladder) | `ercot_faststart_pool_condbinned.json` | `ercot_faststart_pool_contpct.json` |

**Node construction (the derive side).** Each continuous artifact computes the
IDENTICAL statistic its stepped derive computes, keyed per HOUR node instead of
per bin — no new statistic, no new estimator, no new clamp, no new quantile
grid:

* A node is a corpus delivery hour. Its x-coordinate is that hour's within-year
  net-load percentile — the derives' existing conditioner, UNCHANGED
  (`_netload_pct(year)` = EIA-930 demand − wind − solar, `rank(pct=True)`, for
  the cleared-share/RT/pool derives; `netload_pct_by_hour()` for the
  conditional-surface derive — each derive keeps its own existing conditioner).
* The node's values are the stepped derive's own per-bin statistics computed on
  the hour's own rows: MW-weighted quantiles of segment multipliers at the
  UNCHANGED `LADDER_QUANTILES` (`[0.1, 0.3, 0.5, 0.7, 0.9]`); per-hour
  `cleared_share` = Σcleared/Σlive over that hour's site-rows; per-hour
  `pool_frac` by the pool derive's own construction; per-hour conditional
  peak ladder = the per-resource top-of-curve multiplier within that hour,
  reduced by the same `_peak_ladder_from`, with the SAME all-hours `floor_mult`
  clamp and HCAP cap.
* An hour with no measured rows for a class contributes NO node (absence
  disclosed in coverage counts, never imputed).
* Hours with EXACTLY tied percentile ranks (rank ties, and — for the pooled
  conditional surface — the same rank from different years) are pooled into one
  node by the same MW-weighted reduction over their combined rows. This is the
  only cross-hour pooling anywhere, it is forced by x-monotonicity, and it
  introduces no parameter.
* **Year scoping preserved EXACTLY:** RT and pool vintages stay year-scoped
  with NO pooled fallback (a year absent behaves byte-identically to today);
  the cleared-share vintage carries per-year tables plus the pooled fallback
  exactly as its stepped form; the conditional vintage stays pooled across the
  disclosure years exactly as its stepped form. Derive span: delivery years
  2023–2025 (the training window; the RT stepped artifact's 2022 table is NOT
  reproduced in the continuous vintage — 2022 is quarantined for solves anyway,
  and a future authorized touchpoint session re-derives with 2022 included
  under the data-prep-unrestricted clause).
* **Provenance tag:** every continuous artifact carries
  `_provenance.conditioning = "continuous-netload-pct"` plus the full source
  inventory and per-class node-coverage counts.

**Apply construction (the solve side).** In the four ERCOT builders
(`offer_surfaces.py`), when the gate is armed:

* The solve-hour conditioner is the same model net load the builders already
  receive (`demand − solar − wind`); its per-hour percentile is
  `rank(pct=True)` within the solve year — the mirror of the derive's
  construction (today: `np.quantile` thresholds + `searchsorted`; the
  continuous form ranks instead of bins; both are the year's own empirical
  distribution, forward-native, rule 13).
* Every per-bin lookup `value_b[hour_bin]` becomes
  `np.interp(p_t, node_pct, node_value)` per ladder rung / boundary /
  pool_frac. Interpolation is linear between nodes and CLAMPED FLAT beyond the
  terminal nodes (np.interp semantics): above the tightest measured hour the
  surface holds that hour's measured conduct — nothing is extrapolated beyond
  what was posted.
* ALL downstream arithmetic is UNCHANGED: the rel geometry
  (`rel = (s_g − bnd)/(1 − bnd)`, per-hour `bnd` making rel time-varying — the
  span-branch precedent at `offer_surfaces.py:1691`), the `× gas_day(t)`
  normalization, the `min(target, cap_frac × VOLL)` cap, the
  `max(0, target − mc_base)` markup, the conditional surface's `ratio ≥ 1`
  clamp and per-rung cap, the pool's `own_mask` replace-by-mask composition,
  and the additive composition at the `mc_bid_adjust` seam. No hour loops
  (rule 2): the interpolations are vectorized.
* `ercot_offer_surface_netload_pcts` is NOT consulted under the gate (it
  remains the legacy form's field, untouched at its default). Hard errors
  (loud, never silent) when the gate is armed with: `ercot_offer_surface_min_bin
  != 0`, or any of `ercot_offer_surface_cleared_share_state` / `_steam` /
  `ercot_shoulder_online_span` / `ercot_offer_surface_lowcurve[_floorscoped]` /
  `ercot_offer_surface_midcurve_conditional` / `ercot_offline_commit_offer`
  armed — those members' geometry is not migrated in this session, and a
  mixed-grain family is the half-migrated state the PJM vintage guard exists to
  prevent. (All are off in the keeper recipe; the errors protect successors.)
* A vintage guard mirrors `_assert_surface_vintage`: the gate requires the
  `continuous-netload-pct` tag in every loaded artifact; arming the gate
  against a stepped JSON (or the legacy path against a continuous JSON) is a
  hard error.
* **P1-only, exactly as today:** the family already applies at the
  `mc_bid_adjust` seam; P0 run lengths and the startup-amortization coupling
  are untouched by construction.

**Forward story (rule 13), inherited unchanged:** the conditioner is the year's
own (simulated, in a forecast) net-load percentile; the surfaces are conditional
submitted-offer conduct. The grain change alters no input class and no forward
regeneration path: a forward year ranks its own simulated net load exactly as it
binned it today, and the year-scoped artifacts behave for absent years exactly
as today.

## 3. Identification discipline and the rule-20 bound

* **ZERO fitted scalars, zero chosen edges, zero chosen grids.** The node grid
  is the corpus's own hours; the ladder quantile grid, clamps, caps,
  conditioners, class scopes, row scopes and composition are all inherited
  byte-unchanged from the armed family. Nothing in the derive or the apply path
  reads realized prices, clearing outcomes, or any residual — the derives read
  SUBMITTED offer curves (and awards for the cleared-share boundary, exactly as
  today).
* The maximum-bins question of form (b) is dissolved by form (a): there are no
  bins.
* **If the honest grain refinement lands short of the −10 % bar, that is the
  result.** It is reported at full magnitude with the residual named. No
  post-hoc edge, no scalar, no stretching. A residual that could only be closed
  by a tuned value is an open root-cause issue, not a parameter (rule 20).

## 4. Rule-19 reconciliation — enumerated against every armed surface pricing the same rows

The grain change alters LEVELS per hour; it alters NO row-hour ownership. The
composition arithmetic (sum of disjoint row-sets; pool replace-by-mask) is
byte-unchanged code. Enumerated per the handoff's requirement:

| armed mechanism | rows it owns | relation of the grain change |
|---|---|---|
| `ercot_offer_surface_cleared_share` (DAM wall) | merchant CC/CT `econ*` tranches | **REPLACED grain** — same rows, same boundary/ladder statistics, conditioning bin → continuous percentile. Ownership unchanged. |
| `ercot_offer_surface_cleared_share_rt`, mode `replace` | the same rows, RT-measured years | **REPLACED grain** — the year-scoped SCED ladder re-keyed per node; `replace` composition against the DAM leg unchanged (an RT-populated hour takes the RT value; hours with no RT node at interp support keep the DAM basis exactly as unmeasured bins do today). |
| `ercot_offer_surface_conditional` | `peak*` rungs of CC_REGULAR / CC_CHP / CT_PEAKER / ST_GAS | **REPLACED grain** — same per-resource top-of-curve statistic, same `floor_mult`/HCAP clamps, bin ladder → node ladder. DISJOINT rows from the wall (peak vs econ), unchanged. |
| `ercot_faststart_pool_offer` | merchant CT rows above the measured offline-pool boundary | **REPLACED grain** — `pool_frac` and ladder per node; `own_mask` replace-by-mask composition and its precedence over every other surface unchanged. **Carried, not touched:** the rule-18 grain defect (tranche rows read `min_down = 0`, so the physics gate admits every CT bid row — the ercot-176 Amendment-2 finding, owner item). This lever conditions the pool's PRICE; it neither uses nor repairs the row-admission gate. Fixing that defect moves the keeper and needs its own pre-registered round. |
| `ercot_gas_commitment_bridge` | committed-CC `min_gen` floors | **DISJOINT by object** — a bound vs a bid price. Untouched. |
| P1 startup amortization | every started run's bid | **UNCHANGED composition** — the family's markup already composes additively with the amortized markup at the `mc_bid_adjust` seam; the grain change adds no new interaction. |
| `coal_perplant_offer_yearly` + coal offer lanes | coal rows | **DISJOINT by class.** Untouched. |
| ST_GAS drag / steam structure | ST_GAS quantities | **DISJOINT by object** (floors/quantities vs bids); the steam wall extension (`_steam`) is unarmed and hard-errors with the gate (§2). |
| `ercot_offer_surface_midcurve_conditional` | (unarmed) same econ rows | mutual-exclusion hard error inherited; additionally hard-errors with the gate (§2). |

No row-hour gains or loses an owner under the gate; therefore no row-hour has
two owners iff the control has none — which the control's own composition
already enforces (`np.where(own_mask, …)`, mutual-exclusion errors).

## 5. Seam proofs — run and committed BEFORE any solve (the ercot-173/174/176 SP pattern)

A probe (`scripts/probes/ercot178_contpct_seamproof.py`) executes and commits a
JSON record before the LP pair starts. Any assertion failing stops the session.

* **SP-1 — out-of-scope byte-identity.** Gate ON: every non-ERCOT ISO's
  builders return `None` (unchanged); ERCOT rows outside the family's class/row
  scopes carry zero markup exactly as control.
* **SP-2 — gate-off no-op.** Gate OFF at HEAD: each builder's markup array is
  sha256-identical to the pre-change HEAD's (the control path is untouched
  code; asserted anyway per builder, per year).
* **SP-3 — LEGACY-ENCODING BYTE-IDENTITY (the handoff's critical proof).** With
  the gate ON but each continuous artifact replaced by a STEP-ENCODED node
  table — nodes placed at the solve year's own hour percentiles, each node
  carrying the frozen stepped artifact's value for that hour's legacy bin — the
  composed `mc_bid_adjust` is BYTE-IDENTICAL (sha256) to the gate-OFF control,
  for 2023, 2024 and 2025. This demonstrates the change is GRAIN, not level:
  the continuous machinery reproduces the step exactly when fed the step.
* **SP-4 — composition/ownership invariance.** Gate ON with the real continuous
  artifacts: the pool's `own_mask` row-hours and the wall/conditional row sets
  are IDENTICAL to control (ownership never moves); on pool-owned row-hours the
  composed markup equals the pool's alone; on wall rows it equals
  wall(+conditional where classes overlap rows — none do) alone.
* **SP-5 — mechanism-internal no-markdown.** `markup ≥ 0` everywhere; the
  conditional ratio ≥ 1 clamp holds; no row's P1 bid ever falls below its BASE
  bid. **Deliberately NOT claimed:** that no bid falls below the CONTROL's
  walled bid — rank-local conduct sitting below a bin's pooled average IS the
  de-dilution, in both directions (the diagnosis's over-priced overnight body
  is the other face of the same defect). The 2024/2025 protection is §6's
  gates, not a markdown clamp.
* **SP-6 — artifact integrity.** The four FROZEN stepped artifacts are
  byte-untouched (sha256 before/after the derive runs); the continuous
  artifacts carry the vintage tag, source inventories, and per-class node
  coverage; the RT/pool vintages carry NO pooled fallback and NO 2022 table.
* **SP-7 — registry/guard integrity.** The gate hard-errors on each §2
  forbidden combination (asserted by constructing each); `node --check` on the
  matrix JS; `check_mechanism_matrix.py` exit 0 with the new row.

## 6. Kill gates — inherited from PRECOMMIT-ercot172 §5 via the ercot-176 re-statement discipline

The owner's non-disturbance requirement is a HARD GATE, stated first:

* **G-OWNER (2024/2025 non-disturbance, hard).** 2024 keeps its C3a PASS.
  2025's C3a does not worsen beyond −9.1 %. No class's annual energy moves
  > 0.5 % in 2024 or 2025. No year's shed count rises. **An arm that fixes 2023
  by overshooting 2024/2025 is a REJECT, not a partial success.**
* **G-BIT — declared N/A pre-solve, with reason** (the ercot-176 precedent,
  exactly as PRECOMMIT-ercot172 §5 instructs): this rule is year-agnostic — the
  continuous artifacts cover all three training years, so no year is expected
  byte-identical. Replaced by G-SPAN′.
* **G-SPAN′ (replaces G-SPAN).** 2023 is this arm's object, so G-SPAN's energy
  clause does not apply there. Protective intent preserved: the out-of-object
  years must not degrade — 2024 C3a PASS kept, 2025 C3a not beyond −9.1 %, and
  in 2024 and 2025 no class's annual energy moves more than 0.5 % (G-OWNER's
  clauses, restated as the G-SPAN′ inheritance). Tail-count and shed clauses
  kept verbatim for all three years.
* **G-SHED — protective half verbatim.** No year's shed count may rise (2023
  currently 3; 2024 has 2; 2025's counted at scoring). The success half of
  ercot-172's G-SHED addressed the 2024 shed and is N/A to this object.
* **G-SPUR — verbatim (primary falsifier).** The spurious mid-band tail-hour
  count must not increase in ANY year. The net-load-percentile conditioning is
  the protection: a loose hour has a low rank and reads a low node.
* **G-C3c — verbatim.** The three ledgered tail counts (2023 61/181, 2024
  25/53, 3/31 in 2025) must not degrade.
* **G-COAL148 — verbatim.** Coal dispatch above the measured-window ceiling may
  not rise more than 0.5 TWh in any year.
* **G-DOF — verbatim.** Zero new fitted scalars (§3). The DOF ledger's
  `n_residual` does not grow.
* **G-D2 — verbatim.** No class's forced share may cross its rule-20 cap.
  (Expected trivially satisfied: the family touches no bound.)
* **Rule 22 LOYO — verbatim.** Leave-one-year-out within 2023–2025 before any
  promotion. In-sample gain with held-out degradation is overfitting, not
  skill.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported as such and registered
anyway (rules 15/16).** The gates are not renegotiated after the solve.

## 7. Predictions — pre-registered, adjudicated at full magnitude whatever they read

* **P-1 (C3a-2023 direction).** C3a-2023 improves from −32.4 %. Direction is
  implied by the diagnosis's slice table (rank-local top conduct sits above the
  pooled top-bin ladder in every top slice); **no magnitude is promised**. The
  required move for the bar is +$14.44/MWh annual load-weighted (Aug+Sep
  $78.52 → ~$128); an arm far below that is reported as
  directionally-right-but-insufficient with the residual named.
* **P-2 (likeliest failure, stated now).** Rank-local SUBMITTED conduct may
  still under-reach the actual $1,890 energy-component formation at the very
  top — reality's marginal price can form above any single submitted-curve
  quantile (e.g. on the last accepted step's position far up a steep curve — a
  quantity-position phenomenon the ladder's level statistics cannot see). If
  the arm lands materially short, that residual is named as the remaining
  object; it is NOT chased with a scalar.
* **P-3 (formation must be matched, not invented).** 2023 tail-hour gains must
  land in hours that are ACTUAL tail hours. Tail mass on quiet days is a G-SPUR
  failure and is reported as such.
* **P-4 (C3b).** C3b-2023 (0.602) improves iff P-1 does (same residual).
  C3b-2024 (0.205) has a separate root (the two shed evenings; frozen lane) and
  is NOT expected to move materially; if the 2024 surface refinement happens to
  move it under 0.20, that is reported as a side effect, not chased. If
  C3b-2024 degrades, G-SPAN′/G-OWNER fire.
* **P-5 (the body correction).** The overnight/mid-band over-pricing the
  diagnosis measured (h00–h09 +$2–5; +6,823 $·MWh-hours in the $0–50 band) may
  REDUCE under rank-local body nodes — an improvement if it appears, and a
  disturbance risk bounded by G-OWNER's 2024/2025 clauses.
* **P-6 (D-2/D-4 vacuous).** Zero forced energy attributable to the family in
  every year — it prices bids, touches no bound. A non-zero D-2 attribution is
  a stop-the-line implementation error.

## 8. The LP pair, registration, and promotion protocol

ONE pair, `--year 2023 2024 2025` each, years sequential within each invocation
(rule 12), SAME-HEAD (no rebase between solves), detached under `nohup`, via
`scripts/replay_keeper.py results/calibration/ercot176_control_A --out-dir …`:

* **CONTROL** — the run176 keeper recipe replayed at THIS session's HEAD, zero
  deltas.
* **ARM** — control + `ercot_offer_surface_continuous=true` (`--set`). Single
  delta.

Both solves run in-session (never CI). Concurrency per rule 12: the two
invocations may run concurrently only if the first solve's steady-state RSS
confirms two fit in 15 GB; otherwise sequential. **BOTH runs are registered
whatever the outcome** (rules 15/16), with `legitimacy_diagnostics.json` and
`calibration_attestation.json` written before scoring. If the arm is PROVABLY
inert before solving (byte-identical composed bids in all three years), the arm
is not solved and the proof is the record (the ercot-176 Amendment-3
precedent) — stated now so an absent arm registration is never read as a
skipped rule-15 duty.

Promotion (only if every §6 gate passes AND LOYO clears): re-key
`frontend/data/backcast/keepers/ERCOT.json`, `build_status.py --iso ERCOT`,
`calibration-keeper-auditor` agent. ERCOT holds no `complete` marker, so no
`calibration-complete.json` re-key applies. Matrix duties in the same session:
§5.1 item 21, the new row for `ercot_offer_surface_continuous`, cell verdicts
(rejection/inert included), header re-stamp if the keeper changes.

## 9. Scope fences — DO-NOT-REDO honoured in full

Not entered, not re-litigated, not re-tested: the ORDC / RTORPA / RTORDPA lane
(CLOSED at ercot-177 against ERCOT's own published adders — no `ordc_*`
parameter is touched: `ordc_voll`, `ordc_lolp_sigma_mw`, `ordc_mcl_mw`,
`ordc_lolp_shift_sigma`, `ordc_multistep_floor`, `ordc_lolp_params_path` all
stay at keeper values); the reserve LEVEL (CLOSED, triple-corroborated — model
holds MORE than ERCOT's measured PRC); `temp_dependent_derate` (`R`, owner
closure 2026-07-09, cell corrected at ercot-177; CC_CHP measured −1.41 %/°C
sign-inverted); the offline-increment SLOW-START tier (`I`); the ERCOT-151
§0.2 premise (REFUTED, never quoted forward); the event-cap CEILING LANE
(FROZEN — `DECISION-MEMO-ercot-148149-doublecount-2026-08-07.md` ruling
PENDING; not acted on); blanket `min()` (`R`); unit-scoped (`R`); the 2023
depth/excess-cheap-depth premise (REFUTED); the reserve-side family (CLOSED;
over-holds 2.87 GW p50); NO ramp mechanism (`ramp_envelopes` `R`, w_ramp/M
0.26); `ercot_storage_rt_offer_surface` (`R`); `energy_online_capability_cap`
(`R`); the CC-headroom crosswalk (FILED-UNLICENSED); ALL coal offer lanes
(CLOSED); per-year CT re-identification (REFUSED); West/Panhandle (CLOSED);
ercot-172's C3 (REFUSED, rule 13); no per-hour telemetered-HSL cap; no
aggregate capability cap; no capability/availability mechanism of any kind
(that face is closed on measurement, ercot-177).

## 10. Governance

* **Rule 22 `[R-HOLDOUT]`:** `--year 2023 2024 2025` only. ERCOT holds no
  `complete` and no `final` marker; 2022/2021/2020/2019/H1-2026 are not
  solved, scored, read or registered. The RT stepped artifact's existing 2022
  table is not read; the continuous derives emit 2023–2025 only.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the four FROZEN stepped artifacts are not
  re-derived and stay byte-identical (SP-6). The continuous artifacts are a NEW
  VINTAGE for a NEW pre-registered gate — the `pjm_offer_surface_within_season`
  precedent — computing the identical statistics from the identical sources
  with only the conditioning key refined; the trigger is the ercot-177
  structural diagnosis of the conditioning design, pre-registered here BEFORE
  any measurement, never a residual sweep.
* **Rule 24 `[R-REGISTRY]`:** ONE new `ScenarioConfig` field, present in
  `run_config.json`. No env-var knob, no per-plant dict, no `getattr` fallback
  literal.
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-gated everywhere; every other ISO
  byte-identical (SP-1). No parameter crosses an ISO boundary.
* **Rule 26 `[R-DELETE]`:** nothing deprecated, nothing zeroed. The stepped
  form remains the default and fully live.
* **Rule 27 `[R-PUSH]`:** `offer_surfaces.py`, `scenarios.py`, the four
  derives and `run_calibration.py` are ≥300-line files — edited locally, pushed
  as exact on-disk bytes, blob-verified against the REMOTE (sha + line count)
  before the next commit, on both transports.
* **Rule 28 `[R-MECH-MATRIX]`:** §5.1 gains item 21; the new row lands in the
  SAME PR as the `ScenarioConfig` field (duty c); cells updated with this
  session's outcome, rejection included (duty b).
* **GitHub Actions:** no workflow added; both solves run in-session.

---

**Next shorthand: ercot-179.**

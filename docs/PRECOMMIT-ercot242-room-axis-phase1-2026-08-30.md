# PRECOMMIT — ercot-242 (2026-08-30): PHASE-1 of the SCED room-conduct lane — the room-axis EXTENSION of the armed RT wall, built as declared here, armed on ONE 2023 probe solve on the k33 carve-out, kill-gated, registered, verdict unrewritten, keeper consequence ESCALATED

**Session ercot-242, branch `claude/ercot-242-sced-phase1-sb3zj7`.** Executes
the Phase-1 that `docs/PRECOMMIT-ercot241-offcore-conduct-phase0-2026-08-30.md`
§4 opened (gate measured OPEN on all four legs,
`docs/FINDING-ercot241-offcore-conduct-phase0-2026-08-30.md` §4: kills K-1/K-2/
K-3 clear; gate (ii) 12/12 reach; gate (iii) CC 4 / CT 3 contrast bins > 1.25×;
gate (iv) occupancy ×35–670 over floor). This precommit is pushed and
blob-verified BEFORE any derive, measurement, or solve runs. It is written
around the five FINDING-ercot241 §5 design constraints, restated here as
binding terms. The two-config keeper (forward `2026-08-25-234-eastex-identity`
2024–2025, 2023 carve-out `2026-08-25-236-swcap-clip-k33`) is untouched by this
round unless the owner acts on the escalation.

## 0. Standing closures this round sits under (cited, not re-tested)

* **The dependence being parameterized is POSITION/PARTICIPATION-carried, not
  repricing** (FINDING-ercot241 §0.3: paired position-fixed M-3 Δ ≈ +$0.20/
  +$0.52 at 0.9×HSL while the pooled tight/loose p90 contrast runs 2.3–22.5×).
  The candidate prices the measured tail STATE of the online spare under
  tightness — exactly what the armed net-load wall already does, conditioned
  finer. No claim of tightness-triggered repricing conduct is made, and a fit
  gain that could only be read as repricing conduct (M-3 ≈ nil refutes it) is
  not a keeper argument (owner standing note 2026-08-30).
* **DO-NOT-REDO cells stand:** graded static `peak_ladder` (R, ercot-239 r2 —
  adjudication FINAL), ercot-219 option-b (R), storage RT offer surface (R,
  ercot-162/Door A — no storage-scoped parameterization), topology splits (G),
  cross-year seed (R), ORDC/adder channel closures, ercot-178 continuous /
  ercot-180 top-scoped grains (R), lowcurve/negative-offer variants. The room
  axis is none of these: its driver (measured reserve room) is absent from
  every adjudicated cell (ercot-241 §0 restated).
* **ercot-217/Q-B:** this lane is the ONE admissible direction ercot-239 §6.1
  named (a measured conduct parameterization from the 60-Day SCED corpus),
  owner-chartered — it supersedes the no-lever posture FOR THIS LANE ONLY.
* **h2058 is expected OUT OF REACH** (coal+ST_GAS-carried, March outage
  season, UNMATCHED controls — FINDING-ercot241 §5.5): the declared expected
  reach is the 11-hour conduct core; h2058 is graded report-only, never
  load-bearing. The wind pair {6399, 7145} stays queued and untouched.
* **Forward span:** the 2024/2025 regime needs its OWN per-regime zero-solve
  identification (the all-resource SCED corpus at tip is delivery-2023; the
  gitignored `SCED-CT/` corpus is re-fetch-only and CT-only). The 2023 surface
  is NOT transferred across regimes; the forward round is chartered separately
  (§6). This round solves 2023 only, on the carve-out config, under the
  standing rule-16 waiver for carve-out rounds.

## 1. The mechanism, declared ex ante

### 1.1 Gate and scope

New `ScenarioConfig` field **`ercot_offer_surface_cleared_share_rt_room`**
(bool, default off) + **`ercot_offer_surface_cleared_share_rt_room_path`**
(str | None). ERCOT-gated (rule 25); requires
`ercot_offer_surface_cleared_share_rt` armed (hard error otherwise — the room
axis conditions the RT ladder, it has nothing to condition without it);
refuses to arm together with `ercot_shoulder_online_span` or a
conditioning-grain vintage (`ercot_offer_surface_continuous` /
`ercot_offer_surface_top_scoped`) — one vintage per family, the ercot-181
guard pattern. Default off is byte-identical off by construction (the off path
never loads the room artifact). Registered in `_CACHE_KEY_OPTIONAL_FIELDS` +
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` + the tier-tag table IN THE SAME COMMIT
as the fields (the nyiso-119 discipline), with the matrix row +
a cell line in every ISO shard in the same PR (rule 28(c)).

### 1.2 Artifact derivation (FINDING-ercot241 §5.1–§5.2)

`scripts/data/derive_ercot_sced_offer_wall.py --room-binned` →
`data/raw/_validation-source/ercot_sced_offer_wall_roombinned.json`.
A room-axis EXTENSION of the armed RT wall's measured spare ladder — the
frozen derive's constructions VERBATIM (imported, never copied):
`_sced_source_files(2023)` shard selection, `_delivery_year_rows`,
`Resource Type ∈ {CCGT90, CCLE90} → CC / {SCGT90, SCLE90} → CT`, the derive's
own ON-status filter, `_coerce_sced_numeric`, the `_chunk_segments` CPT→CST
clock and Feb-29 drop, `_spare_segments` Base-Point→HASL SCED2 slices,
HCAP clip, HR-multiplier = price / delivered-gas day (`_gas_day_series`), and
`_netload_pct(2023)` on the frozen `NETLOAD_PCT_EDGES`. Two within-convention
notes, declared now:

* **Status filter**: the derive's own `startswith("ON")` (no ONTEST
  exclusion) — REQUIRED by the parent-identity anchor below; the ercot-241
  probe's additional `!= "ONTEST"` was that probe's own declared convention.
* **Statistic**: exact `_weighted_quantiles` per cell (the derive convention);
  the probe's M-4 histogram (≤ 2 % grid error) was the Phase-0 screen. Cell
  values may therefore differ from the FINDING's table by small amounts; the
  identification margins (contrast ratios 2.3–22.5× vs a 1.25× gate; occupancy
  ×35–670 over floor) dwarf both deltas. Neither note adjusts anything.

Per (class ∈ {CC, CT} × armed net-load bin × room bin) the artifact carries:

* the MW-weighted `LADDER_QUANTILES` ladder of spare-segment HR-multipliers —
  **the WHOLE table, inversions included** (CT bins 2–3 and CC bin 6 invert;
  zero fitted scalars means no cherry-picking cells);
* the cell's measured position tail above p90 (`lib.positiontail.tail_support`
  on the cell's own population — the ercot-181 statistic; the k33 base config
  arms `ercot_offer_surface_position_tail`, so the extension must complete the
  position axis with the identical rule: empty tail ⇒ the p90 end-clamp,
  byte-identical);
* occupancy disclosure (segments, resource-intervals, distinct delivery days).

**Room axis:** measured `rtolcap` year-fraction-≤ percentile (NaN-dropped)
from `data/raw/ercot/ercot_2023_ordc_reserves_hourly.parquet` — the ercot-241
§2 construction verbatim — on the DECLARED fixed grid, edges
(0.02, 0.05, 0.10, 0.175, 0.30, 0.50, 0.70) → 8 bins (a grid convention fixed
ex ante at ercot-241, like the net-load edges; not a fitted scalar; never
adjusted). The artifact embeds the year's hourly room-bin index
(`room_bin_hourly["2023"]`, 8760 ints, −1 where rtolcap is NaN) so the apply
seam reads the artifact alone — the measured backcast overlay pattern, no new
runtime data loader.

**Corpus-integrity anchor (stop-the-line, the ercot-181 pattern):** the same
derive pass re-computes the ungrouped per-(class × net-load bin) ladder from
the union of all room bins (NaN-room segments included) and it must REPRODUCE
the frozen `ercot_sced_offer_wall_condbinned.json` 2023 ladders byte-exactly
(same `[q, round(m, 3)]` encoding). A mismatch means the corpus or a
construction drifted: STOP, record an Amendment, fix the drift first — never
paper over. YEAR-SCOPED (rule 13): 2023 only; no pooled fallback; a year
absent from the room artifact leaves the incumbent RT basis byte-identical.
FROZEN AGAINST RESIDUALS (rule 23): re-derive only on a SCED/ORDC source-data
update, never because a residual moved.

### 1.3 Apply seam (FINDING-ercot241 §5.1 — one mechanism, finer conditioning)

Extends `build_ercot_offer_surface_cleared_share_markup`'s RT leg
(`ercot_offer_surface_cleared_share_rt`, mode=replace) in
`src/market_sim/data/fleet/offer_surfaces.py`. For each hour whose measured
room bin is present (≥ 0) and whose (class, hour's net-load bin, room bin)
cell is measured, the RT ladder read — SAME boundary test, SAME rel geometry,
SAME `np.interp`, SAME gas-day normalization, SAME VOLL cap, SAME
`max(0, target − mc_base)` markup — uses the cell's ladder (+ its tail, via
the existing `_positiontail_xy`) instead of the year-level net-load-bin
ladder (+ tail). Hours with NaN room, unmeasured cells, and years absent from
the room artifact keep the incumbent position-tail RT basis BYTE-IDENTICAL.
Nothing else moves: the DAM boundary, econ*-row scope, ST_GAS exclusion
(rule 19), the state-weight exclusion on the RT leg, the faststart-pool
replace-by-mask composition, and the P1-only `mc_bid_adjust` seam are all
unchanged. ONE mechanism, finer conditioning — never a stacked adder or floor
(rule 19 `[R-ONE-MECH]`). Geometry asserts at load: net-load edges +
quantiles must equal the DAM wall's; the room artifact's parent ladders must
equal the armed RT artifact's year ladders (both descend from the frozen
stepped artifact); room-edge count must match the embedded hourly index
range. A conditioning-vintage tag (`room-binned-rtolcap-pct`) guards both
directions: the room gate refuses a non-room artifact and every other path
refuses a room one.

### 1.4 Conditioning variable and the forward story (rule 13, rule 17)

* **Driver:** measured real-time online reserve capability (RTOLCAP) as a
  within-year percentile — a physical/market state (how much online spare the
  fleet actually holds), not a price outcome. Admissibility test: a forecast
  year regenerates the same quantity from the model's OWN reserve-room state
  (the co-optimized reserve headroom / ORDC room the model already computes
  per hour — the same state ercot-239 used to show the model ranks 12/14
  events in its own bottom-5 % room), and it responds to changed conditions
  (fleet, load, VRE all move it). The measured series is used in backcast
  exactly as CAMPD outage windows are: a measured input with a declared
  forward-native analogue. **The forward analogue is DECLARED here, not
  armed:** wiring the model's own room percentile as the forecast-year
  conditioner is the forward round's work (§6), after its own per-regime
  identification — this round scopes the room axis to backcast-2023 via the
  artifact's year-scoping, and a forecast year simply finds no year table
  (inert, byte-identical).
* **Window/driver/forward story (rule 17):** the mechanism has no hour
  window — it is a conditioning surface over all 8,760 hours, armed wherever
  the year's measured room bin and the cell exist; its driver is the room
  state; its forward story is the model-state analogue above.

### 1.5 The double-counting risk, named (FINDING-ercot241 §5.4)

M-2/M-3 established that the measured tight-room elevation is carried by
POSITION (Base Points ride deep, leaving the steep tail as spare) and
PARTICIPATION, not repriced curves. In the LP, position is ENDOGENOUS —
dispatch already rides up the same ladder — so a room-conditioned ladder
risks double-counting the position effect: the surface says "at tight room,
the spare that remains is priced at the tail", and the LP's own dispatch
motion partially reproduces that on the unconditioned ladder. Whether the
finer conditioning adds truth or double-counts is EXACTLY what the probe
solve's gates adjudicate — the year's 8,748 non-event hours (off-season kill,
spur no-increase, officials) are the instrument. **A gate miss is the
round's verdict, recorded at full magnitude, not reframed, not
re-thresholded.**

## 2. The solve (ONE armed 2023 probe on the k33 carve-out)

* **Base:** `results/calibration/ercot236_k33_clip` (`run_config`/`meta`
  as committed — the carve-out keeper's recorded recipe verbatim).
* **Armed member** (`results/calibration/ercot242_room_armed`):
  `python scripts/replay_keeper.py results/calibration/ercot236_k33_clip
  --years 2023 --out-dir results/calibration/ercot242_room_armed
  --set ercot_offer_surface_cleared_share_rt_room=true --note "ercot-242
  Phase-1: room-axis extension of the armed RT wall (this precommit §1)"`.
  Solve env = the keeper's recorded env (highspy 1.15.1 / pandas 3.0.5 /
  pyarrow 25.0.1 — installed and verified BEFORE solving; the ercot-212/239
  lesson); cross-year warm-start pinned off by `replay_keeper` itself.
  This is the round's ONE solve. Years ⊂ {2023}; no `--holdout-authorized`;
  no marker touched; freeze respected.
* **Control = the COMMITTED keeper record** (no control solve): officials
  C3a −7.3 % / C3b 0.102 / C3c 180 asserted zero-solve by
  `ercot226_official_score.py --validate-keeper` (V-0k) before any armed
  scoring; kill baselines read from the committed
  `ercot236_k33_clip/hourly/` sidecars. Freshness basis: the ercot-239 r2
  control replay (same-day, 2026-08-30) reproduced the keeper's officials TO
  THE DIGIT at current HEAD lineage. **Drift contingency, declared:** if V-0k
  fails, or the armed run moves in a region the mechanism cannot reach in a
  way only HEAD drift explains, STOP, record an Amendment, and run ONE
  control replay (`replay_keeper` on the keeper bundle, no overrides) as the
  drift diagnostic — the keeper restated, never a second armed member; the
  A/B then re-bases to control-vs-armed and BOTH register (the ercot-239 r2
  G-REPRO branch). Absent drift, only the armed run registers a new id.
* **Scoring probe:** `scripts/probes/ercot242_room_ab.py` (the
  `ercot239_gradedladder_ab.py` template with control = the committed keeper
  bundle) → `results/calibration/ercot242_room_ab.json`. Officials via
  `ercot226_official_score.py --bundle`; legitimacy diagnostics regenerated
  by `replay_keeper`'s own post-step (C8/D-family scored from the committed
  artifact).

**Kills — the ercot-239 r2 set VERBATIM, measured vs the control (a fired
kill ⇒ REJECTED-AS-ARMED; the run still registers per rule 15):**

* **K-SHED:** any new shed hour (slack > 1e-6 in an hour the control has
  none) — the ercot-235 G-SHED-NEW construction.
* **K-OFFSEASON:** in any month ∈ {1–5, 10–12},
  |armed − actual| > |control − actual| + $5 on the demand-weighted monthly
  mean — the ercot-235 construction.
* **K-COAL148:** 2023 coal (LIGNITE+PRB) energy rise vs control > 0.5 TWh.
* **K-SPUR:** lidless spur count (#{model ≥ 150 & actual < 150}, ercot-225
  Option A) exceeds the control's — the no-increase A/B bar.
* **K-CTST:** |Δ annual energy| vs control > 1.0 TWh for CT_PEAKER or ST_GAS
  — the ercot33 CT↔ST amortization-coupling failure mode at 8× margin.
* **K-DOF (zero new fitted scalars):** the artifact and seam carry measured
  levels and the two fixed ex-ante grids ONLY. If at any point a scalar,
  offset, rescale, or cell edit is needed to make the mechanism behave, the
  round STOPS and records that as its verdict — such a value is an open
  root-cause issue, never a parameter (rule 21).

**Report-only (never selection):** the 14-hour family series recomputed on
the armed run (which of the 12 object hours move, and to what); the model
price at each object hour vs control; band counts vs the DERIVED actual
counts (the ercot-238 ruling-1 discipline, `actual_band_counts` construction
imported); banded spur decomposition; clip-saturated hours; monthly table;
C3c tail count; RT-leg row counts armed vs control.

**Expected reach (declared, graded in the FINDING):** the 11-hour conduct
core is the object; h2058 is graded but never load-bearing. There is exactly
ONE armed member — no sweep, no grid, nothing to select; every score is an
outcome reported at full magnitude.

## 3. Outcome rules (fixed ex ante)

1. **Any kill fires → REJECTED-AS-ARMED.** Register the armed run (rule 15,
   sidecar marked rejected probe), stamp the new mechanism's ERCOT matrix
   cell **R** with the evidence citation, log, keeper untouched — AND still
   escalate the record to the owner with the structure case and the gate
   deltas side by side (owner standing note 2026-08-30: if the
   room-conditioned wall is the structurally correct representation, a
   gate/residual regression is not by itself disqualifying — the owner
   decides; conversely a fit gain through refuted repricing conduct is not a
   keeper argument).
2. **Kills clean AND every official criterion holds or improves →** register
   as CANDIDATE, stamp the cell with the measured verdict, and **ESCALATE as
   keeper-candidate — NEVER self-adopt.** Any keeper/`config_partition`
   consequence is the owner's act (the ercot-241 §4 Phase-1 terms; stricter
   than the r2 rule-2 standing-signature branch, which this round does NOT
   invoke).
3. **Any other outcome** (kills clean but a criterion regresses; any
   borderline reading) → register + ESCALATE with the full A/B table and the
   [R-STRUCT] framing; NO re-key.

Under every outcome: the mechanical verdict is recorded UNREWRITTEN; the
matrix cell is stamped in-session (rule 28(b)); the run registers on the
dashboard with its bundle per rule 15 (rejections too); the calibration-log
entry (shorthand ercot-242) and the FINDING are pushed in-session.

## 4. What this round may and may not do

One armed 2023-only solve (plus, ONLY under the declared drift contingency,
one control replay); no other year solved, scored, or registered; no
`--holdout-authorized`; rule 25: ERCOT surfaces and data only; the two
keeper configs untouched by the session (escalation only); no edit to any
frozen artifact (`ercot_sced_offer_wall_condbinned.json`,
`_positiontail.json`, the DAM wall) — the room artifact is a NEW file; no
constant changes; no workflow files; capx-* files off-limits. Deliverables
pushed as produced, in order: (1) this precommit (blob-verified before
anything runs); (2) the derive extension + ScenarioConfig fields +
cache-key registration + matrix row/cells + tests; (3) the derived room
artifact; (4) the armed solve bundle (slim) + A/B JSON + registration +
FINDING + log + matrix stamp. Push transport per CLAUDE.md Git & Pushing
(small packs off a fresh main base; HTTP/1.1 fallback on 408/500 before any
pack-size conclusion; blob-verify every pushed file ≥ 300 lines).

## 5. Amendment protocol

Any construction found broken (a column absent, a source misread, an assert
mis-specified) is recorded as a numbered Amendment in this file — what
changed and why, BEFORE the measurement or solve it covers is used — and
pushed. Kill thresholds and outcome rules in §2–§3 are never amended after
the armed solve starts; a threshold discovered to be wrongly SPECIFIED (not
wrongly valued) stops the round instead.

## 6. The forward-span charter (named, not executed here)

The eventual prize is the FORWARD span (a mechanism that lands the 2024/2025
C3c misses simply PASSes and the ledger goes inert), but it requires its own
per-regime zero-solve identification round first: (a) corpus — the
all-resource delivery-2024/2025 SCED corpus is not at tip (SCED-CT is
re-fetch-only, CT-only, delivery 2024-01-24+; read the corpus README before
concluding data is missing — intake is its own owner-visible task); (b) the
same M-1..M-4 screen on the 2024/2025 event families with their own kills
and gate; (c) the forward-native conditioner (the model's own room
percentile) declared and validated against the measured series in-sample
before any forecast-mode arm. The 2023 surface is never transferred across
regimes (ercot-241 dispatch discipline).

# PRECOMMIT — ercot-180: TOP-SCOPED conditioning grain of the ERCOT measured offer-surface family (`ercot_offer_surface_top_scoped`), form (b)

**Session ercot-180, 2026-08-08. Pushed BEFORE any derive, any corpus
measurement, and any solve.** Charter: FINDING-ercot178 §7a — the named
successor to the form-(a) CONTINUOUS rejection (`ercot_offer_surface_continuous`,
cell `R`, §5.1 item 21). This session mints §5.1 item 22.

Object: **C3a-2023** (−32.4 % on keeper
`2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b});
owner standing instruction 2026-08-07: get 2023 under 10 % **without disturbing
2024/2025** (both PASS C3a; 2025 at −9.1 %). C3b-2024 (0.205) is a DIFFERENT
root (frozen ceiling lane, memo PENDING) and is NOT chased here.

**The honest budget is fixed up front (ercot-178 P-3 decomposition): the
offer-formation share of the form-(a) evidence is ~+$2.6/MWh — about 18 % of
the +$14.44 the bar needs, NOT 57 %.** A top-scoped arm that lands short of
−10 % is an acceptable, reportable outcome; "this family is EXHAUSTED at
~$2.6/MWh" is an admissible, pre-registered verdict. No mechanism is stretched,
no scalar invented, to reach the bar (rule 1 [R-STRUCT], rule 23 [R-DOF]).

Everything below — form, edges instrument, construction, guards, kill gates,
falsifiers, predictions, and the separately-bounded marginal-position
DIAGNOSTIC — is fixed HERE and is not renegotiated after the solve.

---

## 0. The rule-28(a) DO-NOT-REDO check (run FIRST)

* `ercot_offer_surface_continuous` is `R` — **form (a) is adjudicated and is
  not re-armed or re-tested here.** Form (b) is a DIFFERENT scope (finer edges
  above p97 only; the body bins byte-identical), named by the rejection record
  itself (FINDING-ercot178 §7a, matrix row note) as requiring its own
  precommit. This is that precommit — a successor, not a re-test.
* No other ERCOT cell adjudicates a top-scoped grain. §5.1 items 1–21 checked;
  the ercot-178 DO-NOT-REDO §0 findings carry forward unchanged.
* Lanes NOT entered (all closed): ORDC/RTORPA/RTORDPA (closed against ERCOT's
  own published adders — no `ordc_*` parameter is touched), reserve LEVEL
  (triple-corroborated over-holding), temp-derate (`R`), offline-increment
  slow-start tier (`I`), event-cap ceiling (FROZEN, memo PENDING, not acted
  on), blanket `min()` (`R`), unit-scoped (`R`), 2023 depth premise (REFUTED),
  reserve-side family (CLOSED), ramp mechanisms (`R`), storage RT surface
  (`R`), `energy_online_capability_cap` (`R`), CC-headroom crosswalk
  (FILED-UNLICENSED), ALL coal offer lanes (CLOSED), per-year CT
  re-identification (REFUSED), West/Panhandle (CLOSED), ercot-172's C3
  (REFUSED), every capability/availability face (closed on measurement,
  ercot-177), ERCOT-151 §0.2 (REFUTED).

## 1. Form election — stated before measuring anything

**Form (b) is elected as FINER STEPPED SUB-BINS above p97 only**, applied
coherently to the four armed family members, encoded as step-encoded node
tables consumed by the merged (default-off) form-(a) interpolation machinery:

* **Below p97 every artifact is the frozen stepped artifact's own values,
  byte-identical** — no body repricing, no sparse-year bridging, by
  construction. The SP-3-proven ULP-pair step encoding
  (`_interp_rows` np.interp-bit-compatibility, ercot-178) is inherited as the
  sub-p97 proof basis.
* **Above p97, at most MAX_EDGES new edges** (§2 instrument) split the former
  p97–p100 bin into stepped sub-bins. Each sub-bin's values are the stepped
  derives' OWN statistics (identical estimator, clamps, quantile grid,
  conditioners, class/row scopes) computed on the rows falling in the sub-bin
  — bounded reach, exactly like every existing bin.
* **The rejected alternative is named a NON-GOAL:** corpus-hour interpolation
  nodes above p97 (`--continuous` restricted to the top slice) re-import the
  sparse-year bridging channel in miniature (2024/2025 RT/pool bases are
  561/500 sample-day nodes) and are NOT built. Likewise a node-density-gated
  year scope is NOT elected: it would arm different grains in different years
  (a per-year design choice = a DOF hazard); the sub-bin fallback rule below
  handles thin years conservatively instead.
* **Zero-support rule (forced, not chosen):** a class-year sub-bin above p97
  with NO measured rows inherits its parent former-top-bin value from that
  year's own frozen stepped artifact — i.e. it behaves byte-identically to
  today. Never NaN (that would be a level change), never a cross-year borrow,
  never an interpolation. Sub-bins with any nonzero row count use their own
  rows, exactly as every stepped bin does today (no new minimum-support
  parameter is introduced). Per class-year sub-bin row/interval/MW coverage is
  disclosed in provenance (the 2024/2025 sample-day disclosure duty).

**Family coherence:** all four members (conditional peak surface,
cleared-share wall, RT/SCED leg, fast-start pool) receive the SAME new edges —
one family, one grain (the form-(a) precedent and the mixed-grain hard-error's
rationale). Year scoping, pooled-vs-per-year structure, fallback behavior,
clamps and composition are inherited byte-unchanged from each member's stepped
form.

## 2. The edge-identification instrument — fixed BEFORE looking at the corpus

**Residual-blind by construction: the instrument reads SUBMITTED offer curves
only. It never reads realized prices, clearing outcomes, LMPs, model outputs,
or any residual.**

* **Corpus:** the delivery-2023 NP3-965 60-Day SCED Gen Resource Data corpus
  (the only full-coverage year: 7,917 hour-nodes; 2024/2025 are sample-day
  corpora and are NOT used to place edges). The edges are positions on the
  within-year net-load RANK axis, so the same edges apply to every year's
  derive — inputs are prepared once and applied consistently across all years
  (rule 22's data-consistency clause).
* **Statistic:** per (hour, resource) top-of-curve conduct = the MW-weighted
  distribution of the resource's LAST-3 finite SCED2 segment prices as
  delivered-gas HR multipliers (HCAP-clipped, the wall derive's own
  convention), per family class, restricted to ON-status merchant rows —
  reusing the wall derive's parsers unchanged.
* **Break detection:** for hours ranked > 0.97, scan candidate edges on the
  top-slice hours' own rank grid. At each candidate e, split hours into
  (prev_edge, e] vs (e, next_edge] and compute the MW-weighted two-sample
  Kolmogorov–Smirnov distance between the two sub-populations' top-of-curve
  multiplier distributions (per class, and capacity-weighted pooled across the
  family classes). A SHAPE BREAK is a local maximum of the KS profile with
  (i) each resulting sub-bin holding ≥ 30 hours of 2023, and (ii) a
  day-block permutation p-value < 0.01 (permuting whole days, not hours, to
  respect serial correlation). Recursive: after an edge is accepted, re-scan
  within each resulting sub-bin under the same bars.
* **MAX_EDGES = 2 (hard bound).** At most two new edges — three sub-bins of
  the former top bin. Rationale fixed ex-ante: the committed ercot-178 §4
  node-median table shows exactly two shape regimes above the pooled ladder
  (≈p99 and ≈p99.5 in its reporting slices); more grain than the sample-day
  years can support is the form-(a) failure re-imported. If the instrument
  finds FEWER than 2 admissible breaks, fewer edges are used; if it finds
  NONE, the form-(b) lever is reported EXHAUSTED-AT-IDENTIFICATION (no
  admissible conduct structure above p97) and NO derive or solve occurs —
  that is a legitimate session outcome, registered as such in the matrix.
* The instrument's constants (last-3 segments, ≥30 hours, p < 0.01, day-block
  permutation, MAX_EDGES = 2) are identification-instrument constants fixed
  here, never swept, never revisited after the corpus is read.
* Probe: `scripts/probes/ercot180_topcurve_edge_id.py`; committed record:
  `results/calibration/ercot180_edge_identification.json` (KS profiles,
  chosen edges, per-sub-bin hour/interval/MW counts for 2023, and 2024/2025
  coverage counts as disclosure).

## 3. The mechanism — ONE default-off gate, zero fitted scalars

`ScenarioConfig.ercot_offer_surface_top_scoped: bool = False`. ERCOT-only.
Default off. Matrix row in the same PR (rule 28(c)). Cache-key registered
dropped-at-default in BOTH registries in the same commit (the nyiso-119
discipline); the pinned default key must not move.

* **Artifacts:** four `*_topscoped.json` vintages in
  `data/raw/_validation-source/`, derived by new `--top-scoped` modes on the
  four existing derive scripts. The four FROZEN stepped artifacts
  (`*_condbinned.json`) and the four FROZEN form-(a) artifacts
  (`*_contpct.json`, the `R` record) are byte-untouched.
* **Vintage tag:** `_provenance.conditioning = "topscoped-netload-bins"`,
  guarded in BOTH directions (the form-(a) vintage-assert pattern): the new
  gate refuses stepped or contpct artifacts; the legacy path and the form-(a)
  gate refuse topscoped artifacts.
* **Encoding:** the whole (frozen-below-p97 + sub-binned-above-p97) piecewise-
  constant ladder is step-encoded as ULP-pair nodes (`[edge, v_below]`,
  `[nextafter(edge, 1), v_above]`, flat terminal clamps) and consumed by the
  merged `_interp_rows`/`_contpct_curve` machinery — ZERO new solve-side
  machinery. Below-p97 edges and values are read from each frozen stepped
  artifact's `_provenance.netload_pct_edges` and its own tables, never from
  derive-module constants.
* **Mutual exclusion:** arming BOTH `ercot_offer_surface_top_scoped` and
  `ercot_offer_surface_continuous` is a hard error. The form-(a) compat guard
  is SHARED: the new gate hard-errors with `ercot_offer_surface_min_bin != 0`
  or any unmigrated family member armed (state / steam / span / lowcurve ×2 /
  midcurve / offline-commit) — that guard is intentional and is not weakened.
* `ercot_offer_surface_netload_pcts` is NOT consulted while armed. All
  downstream arithmetic (rel geometry, gas-day normalization, VOLL cap,
  `max(0, target − mc)`, ratio ≥ 1 clamp, `own_mask` replace-by-mask,
  additive `mc_bid_adjust` composition, P1-only seam) is byte-unchanged.
* **Forward story (rule 13), inherited:** a forward year ranks its own
  simulated net load and reads conditional submitted-offer conduct; the new
  edges are fixed rank positions identified from conduct structure, not from
  outcomes, and regenerate identically for any year.

## 4. Rule-19 reconciliation

Identical to PRECOMMIT-ercot178 §4 (grain, not ownership; the Amendment-1
SP-4a/4b restatement carried verbatim), with one addition: **below p97,
ownership CANNOT move vs control** because the pool boundary reads
byte-identical sub-p97 `pool_frac` values — asserted as part of SP-3′. Above
p97 the boundary is the measured boundary at its honest grain (disclosed,
SP-4b). The rule-18 fast-start-pool row-admission defect (tranche rows read
`min_down = 0`, making the physics gate vacuous) is CARRIED, NOT TOUCHED, and
enumerated here as the standing owner item — this lever conditions the pool's
PRICE only; fixing row admission moves the keeper and needs its own
pre-registered round.

## 5. Seam proofs — run and committed BEFORE any solve

Probe `scripts/probes/ercot180_topscoped_seamproof.py`; committed record
`results/calibration/ercot180_topscoped_seamproof.json`. Any assertion failing
STOPS the session.

* **SP-1** — gate ON: every non-ERCOT ISO's builders return None; out-of-scope
  ERCOT rows carry zero markup exactly as control.
* **SP-2** — gate OFF at HEAD: builder markups sha256-identical to control.
* **SP-3′ (THE form-(b) core proof, all 3 years)** — gate ON with the REAL
  topscoped artifacts: on every solve hour whose within-year net-load rank is
  ≤ 0.97, the composed `mc_bid_adjust` rows AND the pool `own_mask` are
  BYTE-IDENTICAL to the gate-off control; and the arm differs somewhere above
  0.97 in 2023 (else the arm is provably inert and is not solved — the
  ercot-176 Amendment-3 precedent, stated now).
* **SP-3″ (null encoding)** — topscoped tables carrying the new edges but the
  frozen parent top-bin value in EVERY sub-bin compose byte-identical to
  control EVERYWHERE, all 3 years: the added edges are GRAIN, never level.
* **SP-4a** — exclusivity: every row-hour has exactly one owner. **SP-4b** —
  the share of row-hours whose owner flips vs control is disclosed (expected
  confined to rank > 0.97; a sub-p97 flip is an SP-3′ failure).
* **SP-5** — no-markdown: markup ≥ 0, ratio ≥ 1 clamp holds, no P1 bid below
  BASE bid.
* **SP-6** — the four frozen stepped artifacts byte-identical to HEAD after
  the derives run. **SP-6′** — the four frozen `_contpct.json` form-(a)
  artifacts byte-identical to HEAD (the `R` record survives).
* **SP-7** — guard integrity: each forbidden combination raises (min_bin ≠ 0;
  each unmigrated member; BOTH grain gates armed; new gate × stepped artifact;
  new gate × contpct artifact; form-(a) gate × topscoped artifact).
  `check_mechanism_matrix.py` exit 0 with the new row.
* **SP-8** — artifact conformance: provenance edges == the committed
  edge-identification JSON's edges, count ≤ MAX_EDGES; sub-p97 node values
  byte-equal the frozen stepped ladders; vintage tag correct; per class-year
  sub-bin coverage present.

## 6. Kill gates — inherited from PRECOMMIT-ercot178 §6 verbatim, with the §7a promotion

* **G-SHED — PROMOTED TO PRIMARY FALSIFIER (ercot-178 §7a): no year's shed
  count may rise** above its control count (control at last scoring: 2023 = 4,
  2024 = 2, 2025 = 0; re-read from this session's fresh control at scoring).
  A 2023 C3a gain bought by shedding is a REJECT however small the
  class-energy movement — the ercot-48/49 manufactured-shortage signature,
  twice-rejected. If the top-scoped arm re-manufactures shed, the top-scoped
  form is REJECTED and the family's grain lane is reported CLOSED at the
  measured offer-formation budget.
* **G-OWNER (hard, owner).** 2024 keeps its C3a PASS; 2025's C3a does not
  worsen beyond −9.1 %; no class's annual energy moves > 0.5 % in 2024 or
  2025. An arm that fixes 2023 by overshooting 2024/2025 is a REJECT.
* **G-BIT — declared N/A pre-solve, with reason:** the topscoped artifacts
  cover all three training years (their above-p97 sub-bins are populated
  per-year), so no year is expected byte-identical. Replaced by G-SPAN′.
* **G-SPAN′.** 2023 is the object; out-of-object years must not degrade —
  G-OWNER's clauses restated; tail-count and shed clauses kept verbatim for
  all three years.
* **G-SPUR — verbatim.** Spurious mid-band tail hours must not increase in
  ANY year.
* **G-C3c — verbatim.** 2023 61/181, 2024 25/53, 2025 3/31 must not degrade.
* **G-COAL148 — verbatim.** Coal above the measured-window ceiling ≤ +0.5 TWh
  in any year.
* **G-DOF — verbatim.** Zero new fitted scalars; `n_residual` does not grow.
* **G-D2 — verbatim.** No class's forced share crosses its rule-20 cap.
* **Rule 22 LOYO — verbatim.** Leave-one-year-out within 2023–2025 before any
  promotion.

**Failing any live gate ⇒ REJECTED-AS-ARMED, reported and registered anyway
(rules 15/16). The gates are not renegotiated after the solve.**

## 7. Predictions — adjudicated at full magnitude whatever they read

* **P-1 (direction and honest ceiling).** C3a-2023 improves from −32.4 %, by
  **≤ ~$2.6/MWh** (the form-(a) offer-formation share) and plausibly $1–2 —
  part of the form-(a) top movement WAS the shed channel this form must
  suppress. The bar (+$14.44) is NOT expected to be reached. Landing short is
  the honest result and is reported at full magnitude with the residual named.
* **P-2 (the residual, carried twice-measured).** The p97–99 slice's 169
  rank-local walls sit AT the pooled level (ercot-178 §4), so that slice's
  formation barely moves. What remains after this arm is a QUANTITY-POSITION
  phenomenon (the last accepted step's position far up a steep curve — ERCOT's
  own SCED system_lambda $1,889.63 at hours the model prices $360), which NO
  conditioning-grain lever can see. It belongs to the §8 diagnostic and an
  ercot-181 charter, NOT to this arm and NOT to a scalar.
* **P-3 (shed suppression is the design's primary test).** The repriced top
  sub-bins clamp at 0.95 × VOLL, so hours whose residual demand cannot clear
  below that shed at $5,000. If the finer grain still pushes ≥ 1 new hour into
  shed in any year, G-SHED fires and P-3 reads FAILED — the form-(b)
  hypothesis (that top-scoping alone suppresses the shed channel) is
  falsified.
* **P-4 (C3b).** C3b-2023 (0.602) improves iff P-1 does. C3b-2024 (0.205,
  frozen lane) is not expected to move materially; if it degrades, G-SPAN′/
  G-OWNER fire.
* **P-5 (no body movement, by construction).** Sub-p97 composed bids are
  byte-identical (SP-3′), so the form-(a) body-repricing disturbance channel
  is absent. 2024/2025 movement is confined to their own above-p97 hours;
  class-energy shifts are expected within the 0.5 % cap — if they are not,
  G-OWNER fires and the confinement hypothesis is falsified.
* **P-6 (D-2/D-4 vacuous).** Zero forced energy attributable to the family;
  it prices bids, touches no bound. A non-zero D-2 attribution is a
  stop-the-line implementation error.
* **P-7 (the marginal-position diagnostic, §8).** Expected: at the top-100
  missed 2023 hours the actual marginal price forms at a position materially
  higher on the accepted resource's own submitted curve than the model's
  marginal row sits on its class curve. If the measured position wedge is
  ≈ 0, the quantity-position lane is REFUTED BEFORE IT OPENS and the honest
  end state of the 2023 tail is the ledgered model-class C3c caveat — that
  refutation is as valuable as a confirmation and is reported either way.

## 8. The marginal-position DIAGNOSTIC — pre-registered, separately bounded (the ercot-179 fold-in)

The unexecuted ercot-179 Phase-0 lever-B measurement, run in THIS session
AFTER the A/B is adjudicated (never before — its hour selection reads the
control residual, so it must not precede or inform the arm's identification):

* **Instrument:** for the top-100 2023 hours by load-weighted actual-minus-
  control price gap: from the delivery-2023 SCED corpus, the marginal
  resource's LAST ACCEPTED MW position on its own submitted curve (accepted
  MW ÷ curve total MW, and the multiplier at that position); from the control
  bundle's hourlies, the model's marginal class/tranche and its position on
  its class curve. Output: the distribution of the position wedge and the
  share of the top-100-hour marginal-price gap it explains.
* **Bounds:** NO LP, NO mechanism, NO ScenarioConfig field, NO scalar. It is
  a DIAGNOSTIC in the DIAGNOSIS-ercot177 class: residual-reading is licensed
  for diagnosis and charter-sizing ONLY, and its output is barred from
  parameter identification in this session (rule 13's diagnostic-probe
  clause).
* **Deliverable:** `results/calibration/ercot180_marginal_position.json` + a
  "what remains" section in FINDING-ercot180 that either charters the
  ercot-181 quantity-position lane (with its own precommit, not written here)
  or refutes it (P-7).

## 9. The LP pair, registration, retention

ONE pair, `--year 2023 2024 2025` each, years sequential, the two invocations
STRICTLY SEQUENTIAL (rule-12 memory cap, measured at ercot-178: two ERCOT
per-plant solves do not fit 15 GB), same HEAD, no rebase between solves, via
`scripts/replay_keeper.py results/calibration/ercot176_control_A`:

* **CONTROL** — zero deltas, `--out-dir results/calibration/ercot180_control_A`.
  Expected array-equal to `ercot178_control_A` prices (the keeper's fourth
  consecutive reproduction at a new HEAD); asserted at scoring.
* **ARM** — single delta `ercot_offer_surface_top_scoped=true`,
  `--out-dir results/calibration/ercot180_topscoped_B`.
* If SP-3′ proves the arm inert (no above-p97 difference), the arm is NOT
  solved and the proof is the record (ercot-176 Amendment-3 precedent).
* `legitimacy_diagnostics.json` + `calibration_attestation.json` written
  BEFORE scoring. BOTH runs registered whatever the outcome (rules 15/16).
* **Retention intent (stated now):** ERCOT sits at exactly 15 registered runs;
  this pair evicts `2026-08-04-159-control-zerodelta` and
  `2026-08-04-159-energy-capability-cap` (the two oldest, both from the
  adjudicated-inert ercot-159 lane).
* Promotion only if every §6 gate passes AND LOYO clears: re-key
  `keepers/ERCOT.json`, `build_status.py --iso ERCOT`,
  `calibration-keeper-auditor --iso ERCOT`. No `calibration-complete.json`
  re-key (ERCOT holds no `complete` marker).

## 10. Governance

* **Rule 22:** `--year 2023 2024 2025` only; edges identified on delivery-2023
  conduct apply to all years as consistent input prep (no out-of-training year
  is solved, scored, read or registered).
* **Rule 23:** the frozen stepped and contpct artifacts are not re-derived
  (SP-6/SP-6′). The topscoped artifacts are a NEW VINTAGE for a NEW
  pre-registered gate, identical statistics, only the top-bin conditioning
  refined; the trigger is the ercot-178 §7a structural charter, never a
  residual sweep.
* **Rule 24:** ONE new ScenarioConfig field, in `run_config.json`, cache-key
  registered dropped-at-default. No env-var knob, no fallback literal.
* **Rule 25:** ERCOT-gated everywhere (SP-1).
* **Rule 26:** nothing deprecated, nothing zeroed; the stepped form remains
  the default; the form-(a) machinery stays merged default-off.
* **Rule 27:** `offer_surfaces.py`, `scenarios.py`, the four derives are
  ≥300-line files — edited locally, pushed as exact on-disk bytes,
  blob-verified against the REMOTE before the next commit, on both
  transports. Run payloads go over `git push` (pack-size rule).
* **Rule 28:** §5.1 gains item 22; the new row lands in the SAME PR as the
  field (duty c); cells updated with this session's outcome, rejection or
  exhaustion included (duty b).
* **GitHub Actions:** no workflow added; every derive, probe, solve, score
  and registration runs in-session.

---

**Next shorthand: ercot-181 (the quantity-position lane, iff §8 sizes it).**

# FINDING — O7 Phase 1 executed: HP-1 HOLDS (the de-laddered leg's P0 is hash-provably bit-identical to the keeper's), and the decomposition lands a surprise — the ladder's pricing channel at the keeper's own commitment state is ≈ ZERO, so the refinement's whole +$2.24/MWh rides commitment + interaction

**Date:** 2026-08-30 · **Lane:** O7 attribution harness (the finding-§5 partial,
owner Door-2 ruling at the 2026-08-30 director sitting) · **Branch:**
`claude/o7-attribution-harness-fjuvgd` · **Charter:**
`docs/FINDING-o7-p0-seam-restoration-2026-08-26.md` §5 · **Precommit:**
`docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md` (pushed before any solve;
its HP-1..HP-3 predictions are scored below, none renegotiated) · **Artifact:**
`results/calibration/o7_attribution_harness_2023.json` (committed with this
finding). **Keeper artifacts read, never written** — the `ercot236_k33_clip`
bundle, the dashboard, the keeper shard and the registered numbers are all
untouched, per the ruling's boundary.

---

## 0. Headline

The harness ran its precommitted real-year exercise — **2023 on
`ercot236_k33_clip`, the CALIBRATED 2023 keeper, three sequential legs**
(control C / keeper A / de-laddered L, each a full two-pass per-plant ERCOT
solve replayed through `replay_keeper.build_kwargs` →
`solve_and_persist` with `MARKET_SIM_WARMSTART_XYEAR=0`):

1. **HP-1 CONFIRMED — attribution is restored by construction.** On both
   energy-solve calls, leg L's P0 is **bit-identical to leg A's** on every
   hash the precommit named: `r0.dispatch`, `r0.prices`, the objective bits,
   the full P0 composite, the startup markup, the P1 min-gen floors (the armed
   gas-commitment-bridge scaffolding), `mc_base`, and the committed-row run
   stats row-for-row. The counterfactual FINDING-ercot188 §6.2 said "does not
   exist" now exists as an instrument, hash-proven.
2. **HP-2 MEASURED, AND IT IS THE FINDING: the pricing channel is ≈ zero.**
   `lw(A) − lw(L) = −$0.0196/MWh` on the 2023 annual load-weighted price —
   two orders of magnitude below the transported +$1–3/MWh order, and the
   opposite sign. The precommit pre-named exactly this outcome as reportable:
   *"a measured ≈ 0 pricing channel with HP-1 intact would itself be a
   finding (the ladder pricing out entirely through commitment)"*. That is
   what was measured. The whole A/B is **+$2.2381/MWh** (A − C, 56.4408 vs
   54.2028), so **commitment + interaction carries +$2.2576/MWh — effectively
   the entire effect** (§3 for why the residual-rung disclosure makes the
   near-zero pricing leg interpretable rather than paradoxical).
3. **HP-3 CONFIRMED — the inherent P0 exposure reproduces at the 236 recipe:**
   control-vs-keeper, **74 of 132 committed rows / 12,380 MW** change P0
   commitment state (keeper +11 starts, +45 committed on-hours vs control) —
   strikingly consistent with the 188-era 73/132 / 12,474 MW measured on a
   different recipe. The forfeiture story stands; nothing needs
   re-examination.
4. **One stop-and-diagnose event, disclosed at full magnitude** (§4): the
   harness's own internal control halted the first de-laddered leg on a
   **1-ULP floating-point reassociation** (10 coal `_peak` rows, max
   8.5e-14 $/MWh, relative 1e-15) in a plant-level aggregate that SCHEME R1
   conserves exactly in value. The control was **scoped, not weakened**:
   bitwise stays mandatory on every row Δmc reads or aligns to; rows outside
   Δmc's support get a 1e-9 $/MWh tolerance with every nonzero pair disclosed
   in the artifact. No prediction was touched; toy tests pin all three edges.

**O7 closes per the Door-2 ruling's own closure language:** *attribution
restored by construction (hash-proven bit-identical-P0 leg); bit-identity of
R1's own arm/off comparison recorded as INHERENTLY forfeit — a property of the
mechanism, not of its wiring — per FINDING-o7-p0-seam-restoration §2.* Keeper
untouched.

---

## 1. What ran

| leg | recipe | fleet rows | wall (2 calls) | scored lw $/MWh |
|---|---|---|---|---|
| C control | keeper recipe, `ercot_econ_curve_top_refine=False` via `prb_overrides` | 1,780 | 566.6 + 635.2 s | 54.2028 |
| A keeper | keeper recipe exactly as recorded, capture-only | 2,320 | 916.7 + 903.7 s | 56.4408 |
| L de-laddered | keeper recipe + Δmc merged into the composed `mc_bid_adjust` | 2,320 | 908.6 + 960.9 s | 56.4604 |

Each leg ran as its own subprocess (fresh deterministic heap), sequentially
(rule 12), through the SAME entry point the A/Bs use, with the wrapper
monkey-patching `scripts.run_calibration.run_energy_solve` inside the probe
process only. Solve directories were temporary; the captures live in the
session scratchpad and the committed artifact is the decomposition JSON. The
keeper recipe's adaptive two-pass fired exactly twice per leg as the precommit
fixed; leg L's pass-2 storage floor responded to leg L's own pass-1
de-laddered prices (the recipe held fixed, per the precommit's channel
definition).

**Δmc as built** (precommit §1.1–§1.2, all asserts green): 108 refined plants,
648 target sub-slice rows (m=6 → m′=11 everywhere R1 fired), 1,672 equal
pairs checked (756 candidate pairs bitwise-equal, the rest per §4), capacity
conservation exact (`parent/m` and sum-to-parent at 1e-6 MW). |Δmc| max
$17.45/MWh on a target row-hour; **capacity-weighted mean Δmc =
−6.5e-16 $/MWh — machine zero**, the first direct measurement of the charter
finding's §2.2 sharpening that the refined ladder is capacity-weighted-
mean-preserving over the top block. SWCAP composition guard: clip level
$4,999.99, max Δ-row `mc_base` $464.04 — margin 10.8×, the precommit's
"order 10×" prediction, so the pre-P0 clip is a no-op on every row Δmc
touches and the composed semantics are exact. `markup[target rows] == 0`
held; `p1_bid_max_target` was `None` as recorded.

**Provenance.** Control and keeper legs ran at the harness tree on base
`f9eb73c`; main advanced to `2c4996f` (#4356–#4367, 16 `src/` files) and this
branch was rebased onto it while the re-run de-laddered leg was mid-solve
(imports already resolved). The proof does not rest on that narrative:
**`mc_base_hash_equal`, the P0 hashes, the markup and the floors are measured
bit-identical between legs A and L**, so tree motion demonstrably did not
reach the compared pair — HP-1 is exactly the guard that would have caught it.
`git diff origin/main..HEAD -- src/` is empty at the harness-run commit
(`7c023a9`): the disarmed path is HEAD itself (rule 1 inertness, precommit
§3).

## 2. The decomposition, at full magnitude

On the scored pass-2 P1, system load-weighted:

| scalar | A keeper | L de-laddered | C control | pricing (A−L) | whole A/B (A−C) | commit+interaction (L−C) |
|---|---|---|---|---|---|---|
| lw price $/MWh | 56.4408 | 56.4604 | 54.2028 | **−0.0196** | **+2.2381** | **+2.2576** |
| p50 hourly | 24.666 | 24.701 | 24.763 | −0.035 | −0.097 | −0.062 |
| p95 hourly | 58.375 | 58.644 | 59.381 | −0.269 | −1.006 | −0.738 |
| p99 hourly | 390.94 | 391.44 | 312.51 | −0.50 | +78.44 | +78.94 |
| max hourly | 4,999.99 | 4,999.99 | 4,999.99 | 0 | 0 | 0 |
| hours ≥ $1,000 | 57 | 57 | 45 | 0 | +12 | +12 |
| shed MWh | 0 | 0 | 0 | 0 | 0 | 0 |

The identity `(A−C) = (A−L) + (L−C)` is exact by arithmetic; `L−C` is
commitment **plus interaction**, never a pure commitment number (finding §5
limit iii). The tail tells the same story as the mean: the +78 $/MWh p99 move
and all 12 added spike hours sit ENTIRELY in the commitment+interaction leg —
the bit-identical-P0 pair differs by −0.50 at p99 and 0 spike hours.

**P0-side physical context** (from the captures): P0 total energy 303.4809
TWh in A and L (bit-identical) vs 303.4809 TWh in C — conserved to
3.8e-05 TWh, the 188-era order. The armed bridge's floored volume is
identical A vs L (95.4577 GWh-scale min-gen mass, hash-equal) and differs in
C (95.5086) — the P0 exposure reaching P1 *bounds*, measured live at the 236
recipe.

## 3. Why a ≈ zero pricing channel is coherent — the residual-rung disclosure

The precommit's §1.3 residual disclosure is what makes the near-zero A−L leg
interpretable. Measured on the assembled P1 bid across each refined plant's
sub-slices:

| | cap-wtd mean annual spread | max hourly spread |
|---|---|---|
| A keeper | $647.81/MWh | $4,699.59 |
| L de-laddered | $646.08/MWh | $4,697.88 |

Δmc de-ladders **`mc_base` only** — the finding's formula, by construction —
and the measurement shows the assembled bid's rung structure across the top
sub-slices is dominated by the **P1-only offer-surface family held fixed in
leg L** (the conditional / cleared-share / fast-start-pool surfaces, keyed to
each row): flattening the `mc_base` heat-rate rung removed ~$1.73/MWh of a
~$648/MWh cap-weighted spread. Two consequences, stated honestly:

* **What HP-2 measured is exactly the finding-§5 channel:** the base-cost
  ladder's own P1 repricing, at the keeper's real commitment state, with
  every other keeper mechanism fixed. That channel is ≈ zero (−$0.02/MWh).
  The 188-era +$1.99/MWh quantity-fixed IQR arithmetic — an invariant-
  quantity mirror, not an LP — does not survive contact with the real LP's
  re-optimization: transported as "context, not a gate", and the measurement
  overrides it (rule 1: the verdict never keyed on direction).
* **What it does NOT say:** that the refinement is priceless. The refinement's
  effect at the 236 recipe is +$2.24/MWh — it simply travels through the P0
  commitment state (74 rows / 12.4 GW, the bridge floors, run lengths) and
  the LP's joint re-optimization, not through the ladder-as-P1-bid. And the
  sub-slice rows themselves carry the (held-fixed) measured offer surfaces
  that exist because the rows exist; de-laddering those would be a different
  instrument than the one the finding chartered and the precommit fixed.

This is the sharpest form of the program's own prior: FINDING-ercot188 §6.2
("there is no counterfactual in which the ladder moves and the commitment
does not") — now with the counterfactual manufactured, the split is measured
instead of argued, and the answer is that the commitment side is not merely
confounded with the effect, it **is** the effect.

## 4. The stop-and-diagnose event (construction deviation, disclosed)

The first de-laddered leg halted on the harness's own §1.2 internal control:
`mc_base` differed between the coarse and refined builds on rows the
refinement cannot touch. Diagnosed before anything was changed (a no-solve
seam capture + row-level comparison):

* **10 pairs of 1,672 differ — all coal `_peak` rows** (the ERCOT-140
  gas-anchored coal-peak margin path), max |diff| **8.526513e-14 $/MWh —
  1 ULP, max relative 1e-15** — a plant-level aggregate that R1 conserves
  exactly in value (the refinement is capacity-weighted-mean-preserving, §1)
  but reassociates in floating point when the plant's row count changes.
* **Zero of these rows are in Δmc's support**: their Δ rows are zero and no
  Δ value reads them. A bitwise control there measures summation order, not
  the construction.
* **Response:** the control was scoped — candidate (econc) pairs, i.e. every
  coarse row Δmc reads and every refined row it aligns to, stay **bitwise**
  at full precommit strength; non-candidate pairs get a 1e-9 $/MWh tolerance
  with each nonzero pair disclosed in the artifact (all 10 are, with unit
  ids), and anything beyond FP-reassociation magnitude still stops. Committed
  as its own reviewed change with three new toy tests (1-ULP on a candidate
  row still stops; 1-ULP on a non-candidate row passes disclosed; 1e-6 on a
  non-candidate row stops). No precommit *prediction* was touched; this is
  measurement scaffolding meeting real FP behaviour, recorded rather than
  suppressed.

## 5. Predictions scored (precommit §2 — none renegotiated)

* **HP-1 (bit-identity): CONFIRMED**, both calls, every named hash, run stats
  row-for-row. The stop-rule never fired on the falsifier.
* **HP-2 (instrument sensitivity): the instrument is live but the channel is
  ≈ zero** — lw(A) − lw(L) = −$0.0196/MWh against a transported order of
  +$1–3/MWh. Reported at full magnitude as the precommit's own "would itself
  be a finding" branch. Strictly, "leg L's scored P1 differs from leg A's" is
  TRUE (it does, in every scalar) — the surprise is the size and sign.
* **HP-3 (control-side reproduction): CONFIRMED nonzero** — 74/132 rows,
  12,380 MW, fresh at the 236 recipe.

## 6. Governance

* **Rule 1 `[R-STRUCT]`:** measurement scaffolding only; `git diff
  origin/main..HEAD -- src/` empty; leg A was the live inertness check
  (capture-only wrapper, pass-through). No verdict here keys on fit
  direction; nothing is promoted, demoted, or re-tuned on these numbers.
* **Rule 13 `[R-MEASURED]` / finding §5 limit (ii):** leg L is an instrument,
  never registered, never dashboarded, never scored against actuals; its
  solve directories were temporary. The committed outputs are the
  decomposition JSON + this finding.
* **Rule 22 `[R-HOLDOUT]`:** every solve year = 2023. Rule 16: a single-year
  identity probe is a throwaway diagnostic, never a keeper.
* **Rules 5/20/24:** zero new tunables, fields, or env knobs (the one env
  write is the standing `MARKET_SIM_WARMSTART_XYEAR=0` replay pin).
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-only, hard-asserted on the replayed meta.
* **Rule 26 duty (b):** the `ercot_econ_curve_top_refine` cell in the ERCOT
  matrix shard is evidence-stamped by this session (verdict untouched — K as
  adjudicated at ercot-188; nothing was mechanism-tested for arming).
* **Rule 27 `[R-PUSH]`:** all pushes over `git push` on a fresh-fetched base;
  the ≥300-line probe and test files blob-verified after push (line counts +
  hashes equal).
* **Audit row O7** (`docs/audit/third-party-audit-2026-08.md`): closed by
  this finding per the Door-2 ruling; closure text updated in the same
  session (the finding-§8 assignment of the O7 row to the executing session).

## 7. Evidence chain

`results/calibration/o7_attribution_harness_2023.json` (HP-1 per-call hash
table, the full decomposition, the Δmc diagnostics incl. the 10 disclosed FP
pairs, per-leg captures) · `scripts/probes/o7_attribution_harness.py` + 17
toy tests (`tests/test_o7_attribution_harness.py`) ·
`docs/PRECOMMIT-o7-attribution-harness-2026-08-30.md` ·
`docs/FINDING-o7-p0-seam-restoration-2026-08-26.md` §2/§5/§6 ·
`results/calibration/ercot236_k33_clip/{meta.json,run_config.json}` (read
only) · FINDING-ercot188 §6.2 and `ercot188_p0_delta.json` (cited, not
re-derived).

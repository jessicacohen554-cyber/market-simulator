# FINDING — ercot-180: the TOP-SCOPED conditioning grain (form b) is EXHAUSTED-AT-IDENTIFICATION, matrix §5.1 item 22

**Session ercot-180, 2026-08-08.** Charter: FINDING-ercot178 §7a (the named
successor to the form-(a) continuous-grain rejection) — finer stepped
sub-bins above p97 only, edges identified from submitted-offer conduct
structure, never realized prices. Object: **C3a-2023** (−32.4 % on keeper
`2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b});
owner standing instruction: under 10 % without disturbing 2024/2025.

Pre-registration: `docs/PRECOMMIT-ercot180-top-scoped-grain-2026-08-08.md`,
pushed BEFORE any derive, any corpus measurement, and any solve. It fixed the
edge-identification instrument, its bars, MAX_EDGES = 2, the kill gates
(G-SHED promoted to PRIMARY), the honest ceiling (≤ ~$2.6/MWh), the
EXHAUSTED-AT-IDENTIFICATION outcome as admissible, and the §8
marginal-position diagnostic — all before the corpus was read.

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `ercot_offer_surface_top_scoped` — form (b), finer stepped sub-bins above p97 of the four armed measured offer surfaces |
| **Verdict** | **EXHAUSTED-AT-IDENTIFICATION** (cell `R`). The pre-registered instrument found ZERO admissible conduct-structure breaks above p97; per the precommit, NO derive, NO seam proof on artifacts, NO LP pair, NO run registered |
| **Decisive number** | Best candidate edge rank **0.99486** (≈ the p99.5 boundary the ercot-178 §4 table anticipated): KS **0.0878**, day-block permutation **p = 0.017** vs the pre-registered **p < 0.01** bar |
| **Keeper** | **UNCHANGED** — `2026-08-07-run176-control-offline-increment`; the gate-off compose at session HEAD is byte-identical to the ercot-178 recorded control sha |
| **Matrix** | `ercot_offer_surface_top_scoped` row added with the field (rule 28(c)), cell `U → R`; §5.1 item 22 |
| **What remains** | The QUANTITY-POSITION instrument — sized by the §4 marginal-position diagnostic below; ercot-181 charter conditions in §5 |

## 1. The DO-NOT-REDO check (rule 28(a), run before pre-registration)

`ercot_offer_surface_continuous` is `R` — form (a) is adjudicated and was not
re-armed or re-tested; form (b) is the rejection record's own named successor
(a DIFFERENT scope, not a re-test). No other ERCOT cell adjudicates a
top-scoped grain. Every closed lane in the handoff's fence list stayed
closed; the frozen ceiling lane was not entered.

## 2. What was built (merged default-off; the arm was never armable)

The precommit's build order put the identification BEFORE the derive, so the
session built the scaffolding, then measured, then stopped:

* **Gate:** `ScenarioConfig.ercot_offer_surface_top_scoped = False`,
  cache-key registered in BOTH registries in the same commit; the pinned
  default key `603c2498bf71d21d` verified unmoved, the armed key hashing
  distinctly (`947ae05c71c7ee87`).
* **Guards:** `_TOPSCOPED_TAG = "topscoped-netload-bins"` with the vintage
  assert mode-aware in both directions; `_contpct_mode()` hard-errors when
  both grain gates are armed; the form-(a) compat guard (min_bin ≠ 0, seven
  unmigrated members) is SHARED, not weakened.
* **Machinery:** the shared ULP-pair step-encoder
  (`scripts/lib/topscoped_encode.py` — no representable query point inside
  any transition, exact-boundary hours read the LOWER bin exactly as the
  solve-side stepped control assigns them), `--top-scoped` modes on all four
  family derives (frozen stepped + contpct artifacts never touched), and the
  full seam probe (`scripts/probes/ercot180_topscoped_seamproof.py`,
  SP-1..SP-8 with SP-3′ sub-p97 byte-identity and SP-3″ null encoding) —
  **authored, never run**: with zero accepted edges there was no artifact to
  prove.
* **Control-path integrity at HEAD:** the gate-off composed `mc_bid_adjust`
  for 2023 reproduces the ercot-178 recorded control sha byte-for-byte
  (`25a4ba69…`), on the post-merge HEAD carrying the caiso-183/184, miso-144
  and FFR-8A merges — the stepped path is untouched by this session's edits.

## 3. The identification — the decisive result

`scripts/probes/ercot180_topcurve_edge_id.py` executed §2 of the precommit
verbatim (constants fixed before looking: last-3 finite SCED2 steps of
ON-status merchant gas as delivered-gas HR multipliers, HCAP-clipped,
MW-weighted; two-sample KS between below/above rank sub-populations, pooled
across CC+CT deciding, per-class reported; ≥ 30 hours of 2023 per sub-bin;
day-block permutation p < 0.01; MAX_EDGES = 2; delivery-2023 corpus only —
7,917 full-year hour-nodes; N_PERM = 999; KS on a 1024-point common quantile
grid, disclosed). Record:
`results/calibration/ercot180_edge_identification.json`.

* **Population measured:** 263 hours above p97, **403,007 top-of-curve
  segment rows** (~1,530 rows/hour).
* **Result: ZERO accepted edges.** The scan's argmax sits at rank
  **0.99486** — splitting (218, 45) hours, almost exactly the p99.5 boundary
  where the ercot-178 §4 node-median table showed the 4–6× rank-local
  structure — with KS **0.0878** and **p = 0.017**. The bar is 0.01. Because
  the permutation p-value is monotone in the statistic against the same
  null, the argmax's failure closes every smaller candidate a fortiori: the
  verdict is exact under the fixed instrument, not an artifact of testing
  one candidate.
* **Coverage disclosure (the sparse-year story, quantified again):** above
  p97 the sample-day corpora carry 50 hours (2024) and 42 hours (2025) vs
  2023's 263 — reaffirming that no identification could responsibly be
  placed on those years.

**The structural reading (rule 1).** The dilution ercot-177/178 measured is
real — the §4 node-median table stands. What THIS instrument adjudicates is
different and sharper: the rank-local structure visible in per-hour ladder
MEDIANS does **not** survive as a pooled MW-mass distributional break with
day-block significance. The top-of-curve extremes are thin-MW: a few hours'
walls reach 2,463× gas at their p90 rungs, but the MW behind those rungs is
a sliver of the slice's mass, and day-block permutation (the honest null for
serially-correlated conduct) absorbs the rest. **Conditioning grain has no
admissible edge left above p97.** Both grain forms are now adjudicated `R` —
form (a) on its REACH (ercot-178), form (b) on its IDENTIFICATION — and the
family's honest offer-formation budget (~$2.6/MWh, ercot-178 P-3) is
unreachable by finer conditioning of the level statistics.

**What is NOT done:** the instrument is not re-designed after seeing the
answer (a per-hour-median statistic, a looser p-bar, an hour-level
permutation would each be a post-hoc sweep — the exact rule-20/23 hazard the
precommit exists to prevent). The p = 0.017 near-miss is reported at full
magnitude; a FUTURE re-identification is admissible only under a new
precommit on new evidence (e.g. a full-year 2024/2025 NP3-965 intake
enlarging the corpus), for which the merged scaffolding makes the build a
derive-and-prove session, not a rebuild.

## 4. The marginal-position diagnostic (precommit §8 — the ercot-179 fold-in)

*(Run after the adjudication above, on the standing keeper control; NO LP,
no mechanism, no scalar; hour selection reads the control residual under the
rule-13 diagnostic license and its output is barred from parameter
identification.)*

<!-- MARGPOS-RESULTS -->

## 5. What remains, and the ercot-181 condition

With both conditioning-grain forms closed, the C3a-2023 tail residual's only
remaining named object is the **quantity-position phenomenon**: reality's
marginal price forming at a position far up a steep submitted curve (ERCOT's
own SCED system_lambda $1,889.63 at hours the model prices ~$360), which no
LEVEL statistic of any conditional ladder can see. The §4 measurement above
is its sizing evidence. Opening that lane requires its own precommit
(instrument, admissibility case, kill gates — G-SHED PRIMARY carried
forward), per the standing discipline; this finding charters it iff §4
measures a material wedge, and refutes it (P-7) iff the wedge is ≈ 0.

## 6. Predictions adjudicated (precommit §7, at full magnitude)

* **P-1 (direction, ≤ ~$2.6 ceiling):** NOT REACHED — no arm existed to
  move C3a. The sharper truth subsumes it: the ceiling cannot be spent by
  this family at all.
* **P-2 (the p97–99 slice barely moves; the residual is quantity-position):**
  STANDS, now on three measurements — carried to §5.
* **P-3 (shed suppression the primary test):** NOT REACHED (no arm); G-SHED
  was never risked because nothing was armed.
* **P-4 (C3b):** NOT REACHED (no arm).
* **P-5 (no body movement by construction):** the sub-p97 byte-identity
  design was never exercised on artifacts; the gate-off control-path sha
  match (§2) is the session's realized integrity evidence.
* **P-6 (D-2/D-4 vacuous):** NOT REACHED (no arm; no bound was ever touched).
* **P-7 (the marginal-position expectation):** adjudicated in §4.

## 7. Governance

* **Rules 15/16:** NO run was produced — the precommit's
  exhausted-at-identification clause states this explicitly so the absent
  registrations are never read as a skipped duty (the ercot-176/177
  precedent). The keeper and its registration are untouched.
* **Rule 22:** identification on delivery-2023 only; `--years` never left
  {2023, 2024, 2025} in any tool invocation; no out-of-training year read.
* **Rule 23:** zero fitted scalars anywhere; the instrument's constants were
  fixed pre-read and never revisited; the frozen stepped and contpct
  artifacts are byte-untouched (no derive ran).
* **Rule 24:** ONE ScenarioConfig field, registered dropped-at-default in
  both cache-key registries in the same commit.
* **Rule 26:** nothing deleted; the form-(a) machinery stays as merged; the
  form-(b) scaffolding is merged default-off with a hard error on arming
  without artifacts (loud, never silent).
* **Rule 27:** every push blob-verified against the remote (sha + line
  count) for ≥300-line files; mid-session PR #3747 merged and auto-deleted
  the branch — the merged-PR protocol was followed (rebase of the unmerged
  commit onto the new main, force-with-lease to the recreated branch).
* **Rule 28:** duty (a) the DO-NOT-REDO check preceded pre-registration;
  duty (b) the cell verdict `U → R` + citation landed in-session; duty (c)
  the row landed in the same PR as the field; duty (d) no cross-ISO verdict
  minted. §5.1 item 22 added.
* **Owner item carried, not touched:** the rule-18 grain defect
  (`min_down = 0` on econ*/peak* tranche rows making the fast-start pool's
  physics gate vacuous) — enumerated in the precommit §4, unchanged.
* **GitHub Actions:** nothing offloaded; every probe and check ran
  in-session.

# FINDING — ercot-178: the CONTINUOUS net-load-percentile conditioning grain (`ercot_offer_surface_continuous`), matrix §5.1 item 21

**Session ercot-178, 2026-08-08.** Charter: the ercot-178 handoff on the
ercot-177 diagnosis (`docs/DIAGNOSIS-ercot177-c3a2023-anatomy-2026-08-07.md`
§4) — the armed measured offer surfaces' stepped conditioning bins dilute the
top of the distribution (the p97–p100 bin pools 263 hours whose actual prices
span 25×; the tail population is the top 2.07 % of the year, ABOVE the p97
edge). Object: **C3a-2023** (−32.4 % on keeper
`2026-08-07-run176-control-offline-increment`, NOT-YET, fail set {C3a, C3b});
owner standing instruction: under 10 % **without disturbing 2024/2025**.

Pre-registration: `docs/PRECOMMIT-ercot178-continuous-netload-grain-2026-08-08.md`
(pushed BEFORE any derive or measurement; + its pre-solve Amendment 1). Form
(a) CONTINUOUS elected: no edge to fit, nodes = the corpus's own hours,
identical statistics, zero fitted scalars.

**STATUS: SOLVES IN PROGRESS — verdict sections below are filled at scoring.**

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `ercot_offer_surface_continuous` — continuous conditioning grain of the four armed measured offer surfaces |
| **Verdict** | *(pending the pre-registered A/B)* |
| **Keeper** | *(pending)* |

## 1. The DO-NOT-REDO check (rule 28(a), run before pre-registration)

No ERCOT cell adjudicates the conditioning grain; the edges came in with their
mechanisms and were never separately tested (`grep netload_pcts` finds no
calibration-log entry). The PJM D-BIN clause ("no admissible re-bin") is
PJM's: an `R` cell, a residual-aimed re-bin with unchanged source data. This
session's form (a) has no edge at all and refines an armed `K` mechanism —
the ERCOT-96 grain-switch class (rule 19). The ORDC/RTORPA lane, the reserve
level, temp-derate, the ceiling lane and every §8 fence stayed closed.

## 2. The mechanism as built

ONE default-off ERCOT-only gate switches the family coherently (the
`pjm_offer_surface_within_season` pattern):

* **Artifacts** — four `_contpct.json` vintages derived by `--continuous`
  modes from the SAME frozen sources as the stepped vintages; the stepped
  artifacts are byte-untouched (SP-6, sha-verified vs HEAD). Vintage guard in
  both directions (`_provenance.conditioning = "continuous-netload-pct"`).
* **Node grain** — a node is a corpus hour at its within-year net-load
  percentile rank; values are the stepped derives' own statistics computed on
  the hour's rows (MW-weighted `LADDER_QUANTILES` ladders; per-hour
  `cleared_share` = Σcleared/Σlive; per-hour `pool_frac`; per-hour
  conditional peak ladder with the unchanged all-hours floor + HCAP clamps).
  Rank-tied hours pool their rows (forced by x-monotonicity; the only
  cross-hour pooling). Node coverage: DAM wall ~7,342/7,872/7,900 nodes per
  class-year; RT wall 7,917 (2023, full-year corpus) and 561/500 (2024/2025 —
  the SAME sample-day basis the stepped bins pooled, disclosed); pool CT
  7,878/550/500; conditional (pooled years) per-class node tables.
* **Apply** — solve hours rank their own net load (`rank(pct=True)`, the
  mirror of the derive conditioner; forward-native, rule 13); every per-bin
  lookup becomes `np.interp` over the nodes (end-clamped — nothing is
  extrapolated beyond the tightest measured hour); ALL downstream arithmetic
  (rel geometry, gas-day normalization, VOLL cap, `max(0, target − mc)`,
  ratio ≥ 1 clamp, `own_mask` replace-by-mask, additive `mc_bid_adjust`
  composition, P1-only seam) is the stepped bodies' own, with
  `_interp_rows` implemented np.interp-bit-compatibly.
* **Hard errors** — armed with `min_bin != 0` or any unmigrated family member
  (state / steam / span / lowcurve ×2 / midcurve / offline-commit): eight
  combinations, all verified to raise (SP-7).
* **Cache key** — registered dropped-at-default (the nyiso-119 discipline):
  the default key equals origin/main's exactly; an armed run hashes
  distinctly.

## 3. The seam proof (committed pre-solve: `ercot178_contpct_seamproof.json`, ALL_ASSERTIONS_PASS)

* **SP-3, the critical demonstration:** with the gate ON but each continuous
  artifact replaced by a STEP-ENCODED node table (nodes at the solve year's
  own hour ranks carrying the frozen stepped artifact's per-bin values), the
  composed `mc_bid_adjust` is **byte-identical (sha256) to the gate-off
  control in all three years** — the machinery reproduces the step exactly
  when fed the step, so the arm's delta is GRAIN, never level.
* SP-4a exclusivity: every row-hour has exactly one owner (pool markup alone
  on pool-owned row-hours; conditional + wall sum elsewhere) — true, all
  years. SP-4b (Amendment-1 disclosure): the pool ownership margin moves
  0.65 % / 1.53 % / 1.30 % of row-hours vs control — the measured boundary at
  its honest grain.
* SP-5 no-markdown (markup ≥ 0, ratio ≥ 1): true. SP-1 non-ERCOT all-None:
  true. SP-2 gate-off is the untouched control path (sha recorded). SP-6
  stepped artifacts byte-identical to HEAD after the derives ran: true.
* The arm is a REAL delta in every year (composed sha differs from control) —
  unlike ercot-176's provably-inert tier, this pair solves.

## 4. The measured de-dilution, seen in the artifact before any solve

RT 2023, CT class, HR-multiplier space — the stepped top bin (p97–p100,
pooled) ladder [p10..p90] is **[13.5, 20.2, 38.3, 154.7, 596.0]**. The node
medians inside that former bin:

| rank slice | n nodes | median node ladder [p10..p90] |
|---|---|---|
| p97–99 | 169 | [14.2, 21.3, 38.7, 105.2, 578.8] — ≈ the pooled ladder |
| p99–99.5 | 43 | [14.6, 38.3, 84.2, 170.3, 599.0] |
| **p99.5–100** | **44** | **[15.4, 143.4, 462.0, 782.6, 2463.1]** |

The pooled ladder ≈ the p97–99 sub-population; the top 44 hours' measured
conduct — p50 rung 462 vs pooled 38, p90 rung 2463 vs 596 (reaching the
HCAP wall) — is what the step averaged away. CC is tamer at the medians with
the same structure in the extremes. This is the diagnosis's 1.75–3.75×
dilution, measured in the offer artifact itself; the pre-registered P-2 risk
(the p97–99 slice's walls barely move) is visibly live.

## 5. The A/B (pre-registered §8: control + arm, 2023–2025, sequential, same HEAD)

*(pending — control `ercot178_control_A`, arm `ercot178_grain_B`)*

## 6. Kill gates (pre-registered §6, adjudicated at full magnitude)

*(pending)*

## 7. Predictions adjudicated (pre-registered §7)

*(pending)*

## 8. Governance

*(completed at session close; includes: rule 22 — training years only; rule
23 — stepped artifacts untouched, new vintage for a new pre-registered gate;
rule 24 — one field, cache-key-registered; rule 25 — ERCOT-gated, SP-1; rule
27 — every ≥300-line push blob-verified vs remote; rule 28 — item 21 + row +
cell in-session. Environment notes: the repo-wide pinned default cache key
`603c2498bf71d21d` already mismatches at origin/main in this container
(computed `efd1cda1683a0ebe` with and without this session's field — the
field provably moves nothing); the NEISO nuclear-availability unit test
expects an empty crosswalk this regenerated clean tree now populates. Both
pre-existing, neither caused nor repaired here. The 60-Day DAM offers tidy
parquet was rebuilt from the immutable raw shards (deterministic parse; the
2023–2025 37/38-col vintage lacks the three-part columns, so the parser
gained the absent-column guard — the same convention its carry-column fill
already used; the 48-col 2026 refetches are outside the surface's pooled
span and were excluded from the rebuild).*

**Next shorthand: ercot-179.**

# PRECOMMIT — ercot-218 / THE DIRECT SOC/AS-POSITION DRIVER LANE (Phase-0): the ercot-211 identifiability instrument re-run with the measured AS-state driver swap

> **Status: PRE-REGISTERED. Pushed BEFORE any delivery-2023 row is read by this
> instrument.** Read-only measurement on committed corpora. NO LP, no solve, no
> year scored, no run registered, no `ScenarioConfig` field, no mechanism-matrix
> cell verdict, no keeper contact. The verdict is MECHANICAL under §6 and is
> binding on the session that writes it.
>
> Keeper at precommit (resolved fresh from
> `frontend/data/backcast/keepers/ERCOT.json` at this session's fetch):
> **`2026-08-17-ercot215-arm-decontam`** — determination NOT-YET, fail set
> {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c the ledgered CAVEAT ×3
> (68/181, 22/53, 1/31).
>
> Charter: the **ercot-218 owner dispatch itself** — the owner card that
> ercot-211's handback item (ii) required ("a direct SOC/AS-position driver
> from the committed 60-Day DAM ESR data … would need a NEW owner card stating
> why it is not a re-run of a stopped lane"). Why it is not a re-run of a
> stopped lane: ercot-211 adjudicated the **PROXY** driver family
> (SOC/availability proxied by `HSL/HSL_ref`, AS position proxied by the
> aggregate `(HSL−HASL)/HSL`); this lane measures the identifiability of the
> **DIRECT** family under its own card and fits nothing to a residual. The
> ERCOT §5.1 lever queue holds no live un-adjudicated in-model item — **this
> lane is off-queue by the dispatch**, and says so.

---

## 0. WHAT IS BEING MEASURED, IN ONE SENTENCE

Does replacing the ercot-211 instrument's proxied SOC/AS-position drivers with
the **measured per-product AS-responsibility state** change its verdict — in
particular, how much of T5's model-free tie-pair violation (storage 95.1 %,
max irreducible error $2,487.50/MWh) survives when driver-indistinguishability
is measured on the **true AS state**?

**Prior stated honestly (per the dispatch): the null expectation is
NOT-TRANSFERABLE again.** The proxy version failed model-free; the
direct-vs-proxy delta is itself a deliverable either way.

## 1. THE DATA PREMISE, MEASURED FIRST — what "the committed 60-Day DAM ESR disclosures" turn out to be

The dispatch (following ercot-210 finding §6.2 / the ercot-211 handback item
(ii)) names "the committed 60-Day DAM ESR disclosures" as the source for
"per-hour measured ESR SOC, AS responsibility by product (RRSFFR/ECRSS/NSPIN/
REG), and telemetered capability". Inventoried before this design was fixed:

1. **The `60d_DAM_ESR_Data` family is an RTC+B-era artifact and does not
   exist for the test years.** ERCOT ADDED the per-day `60d_DAM_ESR_Data` CSV
   to the NP3-966 daily bundle at the RTC+B go-live: from delivery day
   2025-12-06 storage leaves `Gen_Resource_Data` (no PWRSTR rows) and
   reappears as combined `ESR` resources. This is the repo's own intake
   record (`docs/calibration-log.md`, the ERCOT-66 intake;
   `scripts/data/fetch_ercot_60day_gen_resource.py` — "ESR_Data exists only
   from the RTC+B go-live (delivery 2025-12-06 / publication ~2026-02-04);
   earlier bundles simply have no such member"). The two committed files are
   `60_DAY_DAM_DISCLOSURE_60d_DAM_ESR_Data_2026_Jan-Mar.parquet` (verified
   this session: 183,881 rows, delivery span **2025-12-06 .. 2025-12-31**)
   and `..._2026_Mar-Jul.parquet` (H1-2026 deliveries — **not read**, rule 22
   hygiene). The whole family lies **after the SCED-corpus lane's stop date
   (delivery 2025-12-04)** — it has zero overlap with the instrument's fit or
   test populations.
2. **The family carries NO SOC column even in the RTC+B era.** Verified this
   session: 38 columns, the same layout as `60d_DAM_Gen_Resource_Data`
   (awards, submitted curve steps, HSL/LSL envelope, per-product AS awards).
   No state-of-charge quantity of any kind.
3. **Measured per-hour ESR SOC for 2023–2025 therefore exists in NO committed
   corpus**, and the repo's intake record identifies no pre-RTC+B ERCOT
   disclosure that publishes it. Integrating `Telemetered Net Output` to a
   SOC estimate is a *construction* (unknown initial condition and
   efficiency), not a measurement, and is REFUSED here (rule 13 discipline —
   the same line the RTC+B adapter draws for `HASL`).
   **The SOC half of handback item (ii) is unbuildable on committed data for
   the backcast span.** That is a P0-A finding, recorded as a standing data
   blocker in §6's close-out, not a reason to skip the AS half.
4. **What IS committed and measured for 2023–2025 — the direct AS state**:
   the NP3-965 SCED Gen Resource corpus itself carries five per-product
   telemetered AS-responsibility columns in its audited 108-column consumer
   union — `Ancillary Service REGUP`, `Ancillary Service RRS`,
   `Ancillary Service RRSFFR`, `Ancillary Service NSRS`,
   `Ancillary Service ECRS` — per resource per SCED interval, on the very
   rows the instrument already reads. Verified this session on tracked
   shards: fully populated (non-null share 1.000 on PWRSTR rows, pub
   2024-03), 41.7 % of PWRSTR row-intervals carrying a positive
   responsibility; the ECRS column is **absent from pre-2023-06 shards**
   (107-column vintage) because the product did not exist — a true zero, not
   missingness. `RRSFFR ≤ RRS` holds on only 90.1 % of PWRSTR rows, so **no
   nesting construction is assumed**: the five columns enter verbatim as
   separate non-negative quantities.
5. **The DAM-side alternative is recorded and NOT used.** The committed
   `60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_{2023..2025}` files carry
   hourly per-product DAM AS awards (RegUp/RegDown/RRSPFR/RRSFFR/RRSUFR/
   NonSpin/ECRSSD) for PWRSTR rows. Three reasons the SCED-side responsibility
   is the primary: (a) it is the **real-time** AS state (awards can be
   traded/reassigned intraday; the telemetered responsibility is what the
   resource actually carries at the interval the offer clears against);
   (b) it lives on the same rows as the response — zero join surface, zero
   clock risk (the ercot-216 §6 clock discipline is BINDING on new probes,
   and an Hour-Ending CPT join is exactly the surface it warns about);
   (c) the DAM family's 2023 coverage holes (the permanent Oct-2023 MIS hole,
   deliveries 2023-10-02..11-01; no committed Dec-2023 window) sit in the
   test year. No DAM file is read by this probe.

**Corpus recovery, named in advance.** The instrument's fit years need the
untracked NP3-965 window (pubs 2024-04..2026-02, 673 shards). The git pin
route is DEAD since the 2026-08-16 history rewrite; recovery is the corpus
README's route 3 salvage — `git fetch origin refs/pull/3978/head` (the last
fully-tracked post-slim corpus) with lazy blob restore of the top-level
window only — verified against the tip `SHA256SUMS.txt` (the post-slim hashes
ARE the untracked bytes' hashes) before any row is read. The
`rtcb-format-2026/` quarantine is **not restored and not read**; globs stay
non-recursive; the lane stops at delivery 2025-12-04. The deliveries
2024-01-10..23 MIS gap is carried exactly as at ercot-211 (excluded by
absence, counted in coverage).

## 2. THE DRIVER SWAP — the ONLY change to the instrument

Everything below names the ercot-211 instrument
(`scripts/probes/ercot210_conduct_transfer_phase0.py`, pre-registered in
`docs/PRECOMMIT-ercot210-conduct-transfer-phase0-2026-08-16.md`). The new
probe (`scripts/probes/ercot218_direct_driver_phase0.py`) is that instrument
with the driver set swapped and nothing else: same unit of observation, same
population discipline (above-LSL SCED2 segments capped at HASL, ERCOT-154/161,
telemetered-ONLINE, ONTEST excluded, absolute $/MWh), same responses
(`p50`/`p90`/`s500`, headline STORAGE `p50` / THERMAL `p90`), same fit window
(delivery-2024/2025, tightness ≥ p90), same transfer target (delivery-2023
≥ p98, post-ECRS primary), same folds (out-of-year; LOYO across 2023 months;
the 2024→2025 within-regime control), same candidate-form family and CV
selection rule (5-fold day-block CV, fit years only, forms frozen before any
2023 read), same T1–T5 bands and counting rules verbatim (§4).

**The swap:**

| ercot-211 driver | ercot-218 driver |
|---|---|
| `x3` AS position **proxy** = MW-weighted mean of `(HSL − HASL)/HSL` | **five measured per-product shares**, MW-weighted means over the same segment population: `x3_regup = REGUP/HSL`, `x3_rrs = RRS/HSL`, `x3_ffr = RRSFFR/HSL`, `x3_ecrs = ECRS/HSL`, `x3_nspin = NSRS/HSL` (each from its `Ancillary Service <svc>` column) |
| `x4` SOC/availability **proxy** = MW-weighted mean of `HSL / HSL_ref` (per-resource delivery-year p98 HSL) | **UNCHANGED** — retained as the telemetered-capability driver. Its SOC-proxy role **cannot** be replaced: no measured SOC exists for the span (§1.3). Dropping it would only make T5 ties easier and bias the test toward non-identifiability; keeping it is the conservative direction. |
| `x1`, `x2`, `x5` | unchanged (within-year PRC percentile; RTOLCAP percentile; summer flag) |

Handling rules, fixed now: per-segment-row share = `AS_p / HSL` where
`HSL > 0`, else NaN (the x3 guard, verbatim); per-(hour, class) value =
MW-weighted mean; residual NaN → per-column median fill (the ercot-211
treatment, verbatim); the ECRS column absent in pre-2023-06 shards → share
0.0 (product nonexistence, a true zero); no clipping, no nesting arithmetic,
no derived total — columns enter verbatim. The proxy `x3_old` is computed
alongside on the same rows (for §4's decomposition only; it is NOT a driver
of any fitted form in this probe).

**Quantity-only, auditable**: the reserves-parquet read set stays
(`hour`, `prc`, `rtolcap`) and the refused set stays (`system_lambda`,
`rtorpa`, `rtoffpa`, `rtordpa`); the five AS-responsibility columns are MW
quantities; no settlement price, LMP, RTSPP, DAM price, MCPC or model output
is read anywhere. Both sets are written into the output JSON.

## 3. COVERAGE FALSIFIER — pre-registered, per the ercot-211 lesson

ercot-211's first execution was a false verdict caught only by its
pre-registered coverage block ("a pre-registered coverage requirement is a
cheap falsifier and every future Phase-0 here should carry one"). This run's
requirements, judged before any gate is read:

- corpus restore verified `sha256sum -c` against the tip `SHA256SUMS.txt`
  for every restored shard (996 top-level entries expected OK; the 27
  quarantine entries are not restored and are reported as deliberately
  absent);
- fit hours with offer rows ≥ 2,400 (2024) and ≥ 2,300 (2025); test hours
  175/175 (2023) — the ercot-211 achieved coverage, reproduced;
- a non-empty selected-form map for both classes;
- the AS-responsibility non-null share per year is reported; a year whose
  PWRSTR AS columns are majority-null is a STOP (measured expectation: 1.000).

A verdict computed from a run failing any of these is NOT a measurement and
is not reported as one.

## 4. THE GATES — T1–T5 verbatim, plus the pre-registered T5 decomposition

T1–T5 thresholds, bands, headline statistics, fold rules, named-months
clause (Aug-2023 AND Sep-2023), admissibility constant (`FOLD_MIN_HOURS = 10`)
and the verdict rule are **copied verbatim** from the ercot-210 precommit §7 —
including the constant its §3.2 measured as unsatisfiable for post-ECRS 2023
(the named-months clause is what decides T1/T2 there, exactly as at
ercot-211, and the relaxed-to-≥1 diagnostic is re-reported, gating nothing).
The fitted forms use the swapped driver vector; T3's contrast, T4's
2024→2025 control and the CV selection all inherit it mechanically.

**T5 (the decisive gate) on the direct vector**: a τ-tied pair ties on ALL
scaled drivers `[x1, x2, x3_regup, x3_rrs, x3_ffr, x3_ecrs, x3_nspin, x4]`
(τ = 0.05, identical `x5`), band and counting rule verbatim (< 10 % of tied
pairs may exceed T1's band; `n_pairs > 0` required).

Pre-registered readings, fixed before any number exists:

- **Vacuity**: with 8 tie coordinates instead of 4, the tie count can
  collapse. If `n_pairs = 0` for a class, the mechanical gate FAILS as
  written and the finding reports T5 as **VACUOUS for that class** — ties
  eliminated, model-free non-identifiability *not demonstrated* — never as
  "the drivers fixed it" and never re-thresholded to manufacture pairs.
- **The direct-vs-proxy decomposition (THE deliverable)**: on the same rows,
  T5 is also computed on the proxy vector `[x1, x2, x3_old, x4]`
  (reproducing ercot-211's construction; expected ≈ 95.1 % storage
  violation). Reported per class: (a) the proxy tie-pair count and violating
  count; (b) of the proxy-TIED pairs, the fraction still tied on the direct
  vector; (c) of the proxy-VIOLATING pairs, the fraction still tied on the
  direct vector (the violation mass the true AS state fails to separate) and
  the max irreducible error among them; (d) T5-direct at full magnitude.
  This answers the dispatch verbatim: "how much of T5's tie-pair violation
  survives when driver-indistinguishability is measured on the TRUE SOC/AS
  state" — with the SOC coordinate honestly absent because it is unmeasured
  (§1.3), so the claim is scoped to the TRUE AS STATE + telemetered
  capability.

## 5. WHAT THIS SESSION WILL NOT DO

No LP, no solve, no year scored, no run registered, no dashboard contact, no
`ScenarioConfig` field, no CLI flag, no constant, no derive touched, no
mechanism-matrix cell VERDICT (Phase-0, nothing tested — the ercot-214/217
note-only precedent; an attribution note on the ERCOT shard is the only
matrix contact), no `.github/workflows/*.yml`, no other ISO, no other branch,
no PR (push-and-stop on `claude/ercot-218-direct-driver-5ckiur`; the owner
merges). Rule 22: {2023, 2024, 2025} only — the 2026-deliveries ESR file and
the RTC+B quarantine are not read; no marker sought. Rule 27: files ≥300
lines edited locally and blob-verified after push. DO-NOT-REDO honoured:
Door A conduct-function fitting is not re-run (this is the DIRECT family
under its own card, fitting nothing to a residual); item 11 (Q-B FINAL),
`energy_online_capability_cap` (R), `ercot_storage_rt_offer_surface` (R),
the mid-band spill lane (CLOSED ercot-215), LOLP arming (ercot-206 B0),
V0/ercot-201 (no tightness-conditioned R_f — conditioning here is the same
within-year percentile rank the ercot-210 precommit fixed), 28a, and the
regime lane (CLOSED ercot-217) are all untouched.

## 6. THE VERDICT RULE — binding, no partial credit (the dispatch's precommitted rule, restated)

```
TRANSFERABLE      iff  T1 AND T2 AND T3 AND T4 AND T5 all PASS
NOT-TRANSFERABLE  otherwise
```

- **TRANSFERABLE** → a DRAFT Phase-1 charter may be written and escalated to
  the owner — NOT armed, NOT solved this session — carrying the
  identification, its DOF rows, and a direction-blind kill-gate table
  inheriting ercot-213 §3 + G-CAP + G-SPUR at the 9/11/1 energy-made
  baseline.
- **Anything less** → **the lane CLOSES**; **Door D is CONFIRMED as the
  floor**; the ERCOT backcast lane **RESTS** pending the 2026 SOM
  RTC+B-era anchors (~mid-2027), recorded as the ISO's standing data
  blocker alongside (a) the 2025 EIA-923 final-vintage re-derivation (the
  five C1 gas-class SKIPs), and (b) **new, from §1**: measured per-hour ESR
  SOC does not exist in any committed or published pre-RTC+B disclosure —
  the SOC half of item (ii) is permanently unbuildable for the 2023–2025
  span, and first becomes buildable (if at all) only in the RTC+B era.
- No re-specification, no second driver set, no widened band, no "close
  enough" narrative. T5 governs how a failure is described (model-free
  non-identifiable at this grain vs in-regime-identifiable-but-not-
  transferring), exactly as at ercot-210 §7.1 — with the vacuity reading of
  §4 available to describe an empty tie set honestly.

Q-B FINAL and R-A are cited and honoured: **no C3a, C3b or C3c value is
computed in any year**; every such number in this lane's artifacts is a
committed-artifact citation. Every 2023 quantity this probe measures is a
measured offer-curve/telemetry statistic entering as the transfer test's
evaluation target only (measured-vs-measured, rule 13); nothing feeds any
model input. This dispatch does NOT re-suspend Q-B.

**Keeper at session start and (by construction) at session end:**
`2026-08-17-ercot215-arm-decontam`.

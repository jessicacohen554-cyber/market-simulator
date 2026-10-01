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

---

## 0. Verdict

| | |
|---|---|
| **Lever** | `ercot_offer_surface_continuous` — continuous conditioning grain of the four armed measured offer surfaces |
| **Verdict** | **REJECTED-AS-ARMED** on its own pre-registered kill gates (G-OWNER/G-SPAN′ ~20×, G-SHED, G-C3c), with the mechanism evidence REAL and LARGE: **C3a-2023 −32.4 % → −19.7 %** (+$8.18/MWh, the largest single-mechanism 2023 move on the ERCOT record), C3b-2023 0.602 → 0.349, 2025 C3a −9.1 % → ≈ −4 %, C3c-2024 crosses INTO band |
| **Runs** | control `2026-08-08-run178-control` (NOT-YET {C3a, C3b} — reproduces the keeper byte-identically); arm `2026-08-08-run178-continuous-grain` (NOT-YET; PROBE — REJECTED-AS-ARMED), both registered |
| **Keeper** | **UNCHANGED** — `2026-08-07-run176-control-offline-increment` (the ercot-176 owner ruling was session-specific; this control's outputs are array-equal to the keeper's, so a re-key would change nothing) |
| **Matrix** | `ercot_offer_surface_continuous` row added (rule 28(c), same PR as the field), cell `U → R`; §5.1 item 21 |
| **Successor** | form (b) — finer edges ABOVE p97 only, conduct-identified (§7a below); NOT built here |

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

Both solved at HEAD `fa72e921`, sequentially (the rule-12 OOM disclosure:
two ERCOT per-plant solves do not fit this 15 GB box), via
`replay_keeper.py` off `ercot176_control_A`; single delta
`ercot_offer_surface_continuous=true`.

* **The CONTROL reproduces the run176 keeper BYTE-IDENTICALLY** — the price
  series are array-equal in all three years (lw 43.453 / 31.762 / 33.378) —
  the solve-level half of SP-2, and the keeper's third consecutive
  reproduction at a new HEAD.
* **The ARM (sidecar lw basis, scorer numbers in §6):**

| year | control lw | arm lw | Δ | direction |
|---|---|---|---|---|
| **2023** | 43.453 | **51.633** | **+$8.18** | actual 64.32: −32.4 % → **≈ −19.7 %** |
| 2024 | 31.762 | 33.282 | +$1.52 | moves toward actual |
| 2025 | 33.378 | 35.249 | +$1.87 | −9.1 % → ≈ −4 % (improves) |

* Tail counts (scorer basis, the payload's judged quantity): 2023 > $200:
  **61 → 57** while > $1000 (lw): 22 → 29 — the de-dilution is TWO-SIDED
  exactly as §4 anticipated: the extreme hours reprice up toward their
  rank-local measured conduct while p97–99 hours (whose pooled rungs were
  LIFTED by the extremes — pooled p70 154.7 vs their own 105.2) reprice
  down, dropping mid-tail hours below $200. 2024: 25 → 28 (into band);
  2025: 3 → 0.
* **Dispatch composition moves everywhere** — the walls also reprice the
  BODY, and the 2024/2025 RT/pool node bases are sample-day-thin (561/500
  nodes), so the continuous form bridges sample-day conduct across the whole
  rank axis where the stepped bins bounded each measurement's reach:

| class (share) | 2023 | 2024 | 2025 |
|---|---|---|---|
| ST_GAS (~4 %) | +5.1 % | **+9.7 %** | **+12.7 %** |
| CT_PEAKER (~1.5 %) | +2.3 % | **+8.7 %** | **+11.4 %** |
| CC_REGULAR (~31 %) | −1.8 % | **−3.0 %** | −2.5 % |
| COAL_PRB (~9 %) | +2.3 % | **+2.8 %** | +0.9 % |

* **Shed hours rise:** 2023: 4 → 14; 2024: 2 → 3; 2025: 0 → 0.

## 6. Kill gates (pre-registered §6, adjudicated at full magnitude) — **REJECTED-AS-ARMED**

| gate | reading | verdict |
|---|---|---|
| **G-OWNER / G-SPAN′** (2024/2025 class energy ≤ 0.5 %) | 2024 ST_GAS +9.7 %, CT +8.7 %, CC −3.0 %; 2025 ST_GAS +12.7 %, CT +11.4 %, CC −2.5 % | **FAIL — by ~20× the cap, multiple classes, both years** |
| **G-SHED** (no year's shed count may rise) | 2023 4 → 14, 2024 2 → 3 | **FAIL** |
| **G-C3c** (61/181, 25/53, 3/31 must not degrade) | scorer basis: 2023 **61 → 57** (0.34× → 0.31×, away from 181); 2025 **3 → 0** (0.10× → 0.00×); 2024 25 → 28 (0.47× → 0.53×, crosses INTO the [0.5×, 2×] band) | **FAIL** (2023, 2025) |
| G-SPUR (spurious mid-band tails must not increase) | 2024's +3 tail hours accompany a C3b-2024 degradation (0.205 → 0.208) — the 2024 disturbance face; 2023/2025 tail counts FELL (no spurious mass added there) | adverse on 2024, subsumed by G-OWNER |
| G-COAL148 (coal above-ceiling ≤ +0.5 TWh) | COAL_PRB +2.8 % of ~24 TWh ≈ +0.7 TWh total dispatch in 2024 (ceiling-scoped measure in the verdict) | adverse-direction, reported |
| G-DOF (zero fitted scalars) | zero created — the node tables carry no parameter | PASS |
| G-D2 (forced-share caps) | the mechanism touches no bound; floors byte-inherited | PASS (diagnostics committed per bundle) |
| Rule 22 LOYO | not reached for promotion (the arm is rejected); the identification is residual-free by construction, and the per-year deltas above are the held-out evidence | n/a |

**Adjudication: the arm FAILS its pre-registered gates and is
REJECTED-AS-ARMED** — registered on the dashboard per rules 15/16 with this
verdict. The owner's non-disturbance requirement was a hard gate: an arm that
moves 2023 by +$8.2 while shifting 2024/2025 dispatch composition by 9–13 %
in minor classes is a reject, not a partial success.

## 7. Predictions adjudicated (pre-registered §7)

* **P-1 (direction):** CONFIRMED — C3a-2023 improves −32.4 % → ≈ −19.7 %
  (+$8.18/MWh of the required +$14.44). No magnitude was promised; the honest
  reading is **directionally-right-but-insufficient** even before the gate
  failures.
* **P-2 (likeliest failure):** PARTIALLY the named failure and partially a
  sharper one. As named: the p97–99 slice's rank-local walls sit AT the
  pooled level (§4), so those 169 hours' formation barely moves and the bar
  is not reached. Sharper: the de-dilution is two-sided — the pooled bin was
  not only diluting the top, it was SUBSIDIZING the mid-top — and at body
  ranks the 2024/2025 sample-day node bases generalize thinner than the bins
  did, moving out-of-object years the gates protect.
* **P-3 (formation matched, not invented):** **FAILED, and this is the
  decisive result of the session** (quantified post-registration, 2026-08-08,
  from the committed sidecars + `actual_lmp_hourly_ERCOT.parquet`).
  **67.5 % of the +$8.18/MWh comes from 10 NEW load-shed hours at VOLL**
  (+$5.53 of +$8.18); all 14 arm-shed hours together carry 68.0 %. Only
  **+$2.62/MWh (32 %) is offer-based formation in non-shed hours.** The shed
  hours are real tight hours (not spurious timing — Jun 20, Aug 17/24/25/26/27/30,
  Sep 7 afternoons), but the arm prices them by PHYSICAL SHORTAGE and
  **overshoots the actual by > 1.5× in 7 of 10**, egregiously at
  2023-08-26 18:00 (actual **$570** → arm **$5,000**, 8.8×) and 2023-08-27
  15:00 (actual **$359** → arm **$5,000**, 13.9×). Reality had **4 hours
  ≥ $4,500 in all of 2023** (max $5,046); the arm posts 14 shed hours at
  ~$5,000+. This is the **ercot-48/49 signature verbatim** — "it manufactured
  the tail through physical shortage … right-number-wrong-mechanism",
  REJECTED WITH CAUSE by the owner 2026-07-09 — and it is why this arm is
  **not a keeper on structural grounds, independent of its gate failures**:
  rule 1 `[R-STRUCT]`'s "never reach the right number through a mechanism that
  isn't real" bites directly. ERCOT shed no firm load in these hours.
* **P-4 (C3b):** CONFIRMED on 2023 (0.602 → **0.349** — the shape improves
  with the object, as predicted: one residual) and FIRED as the named risk on
  2024 (0.205 → **0.208**, degrading past the ≤ 0.20 bar it already missed —
  the composition shift's shape face).
* **P-5 (body correction):** CONFIRMED in direction (overnight/mid-band
  walls reprice down) and CONFIRMED as the disturbance channel G-OWNER
  fires on.
* **P-6 (D-2/D-4 vacuous):** CONFIRMED — no bound touched; floors
  byte-inherited from P0 (which is bit-identical by the P1-only seam). D-2
  passes on both bundles; the D-4 `reliability_floor × CT_PEAKER` off-window
  row is the keeper's own standing state (control 96.6/98.2/98.0 % — the arm
  slightly improves it to 92.3/95.5/89.7 %), inherited, not an arm effect.

## 7a. The named successor — what this rejection actually licenses

The rejection is of the ARM'S REACH, not the mechanism class, and the record
now measures exactly where the reach went wrong:

1. **The dilution is PROVEN; its cure is only one-third proven.** Rank-local
   conduct above p99 is 4–6× the pooled rungs (§4), and repricing it moved
   C3a-2023 by +$8.18/MWh — but **only +$2.62 of that is offer-formation**;
   the other +$5.53 is manufactured VOLL shortage (P-3). **The successor's
   honest budget is therefore ~$2.6/MWh from this family, not $8.2**, against
   the +$14.44 the bar needs. A top-scoped variant must be gated on
   `shed_hours must not rise in ANY year` as a PRIMARY falsifier, not an
   inherited protective clause.
2. **The damage came from everywhere else the continuous form reaches:** the
   BODY (rank-local walls reprice down where the pooled bin subsidized them —
   the composition shifts and C3b-2024), and the SPARSE YEARS (2024/2025
   RT/pool bases are 561/500 sample-day nodes vs 2023's 7,917 — interpolation
   bridges sample conduct across the whole rank axis where the stepped bins
   bounded each measurement's reach).
3. **Form (b) — finer edges ABOVE p97 ONLY — avoids both by construction:**
   below p97 the stepped bins stay byte-identical (no body repricing, no
   sparse-year bridging — the sample-day years' p97+ slice is where their
   samples concentrate), and the refinement lands only where the dilution is
   proven. Its precommit must fix, before measuring: the edge-identification
   instrument (submitted-offer conduct structure in the SCED corpus — e.g.
   where the per-resource top-of-curve distribution's shape breaks — NEVER
   realized prices), the maximum number of new edges, and the same
   G-OWNER/G-SHED/G-C3c gates verbatim. The SP-3-proven interpolation core
   and the `_contpct` derives are reusable; a top-scoped variant can also be
   expressed as a node table that is step-encoded below p97 and continuous
   above it — zero new machinery.

**Honest sizing against the owner's bar, carried forward:** the arm's
headline was +$8.18 of the needed +$14.44, but **net of the manufactured
shortage it is +$2.62 — about 18 % of the bar, not 57 %.** A top-scoped
variant keeps the offer-formation share and must SUPPRESS the shed channel
(the repriced top rungs clamp at 0.95 × VOLL = $4,750, so any hour whose
residual demand cannot clear below that sheds at $5,000 — the mechanism by
which measured conduct becomes false shortage). The body-side over-pricing
correction is forfeited, and it was disturbance rather than gain everywhere
it mattered. If the honest top-scoped refinement lands short
of −10 %, what remains is the p97–99 slice's formation — reality's marginal
price there forms above any submitted-curve level statistic (the P-2 residual,
now measured twice), and that residual belongs to a quantity-position
instrument (the last accepted step's position), not to more conditioning
grain.

## 8. Governance

* **Rules 15/16 `[R-DASHBOARD]`/`[R-ALLYEARS]`:** BOTH runs registered, all
  three years each, in-session: `2026-08-08-run178-control` +
  `2026-08-08-run178-continuous-grain` (the arm marked PROBE —
  REJECTED-AS-ARMED in its sidecar). Determinations scored on committed
  artifacts with attestations present (C6 PASS both): both NOT-YET, control's
  fail set {C3a, C3b} identical to the keeper.
* **Rule 22 `[R-HOLDOUT]`:** `--year 2023 2024 2025` only; no out-of-training
  year solved, scored, read or registered. LOYO for promotion: not reached
  (the arm is rejected); the identification is residual-free by construction
  and the per-year deltas in §5 are the held-out evidence.
* **Rule 23 `[R-FROZEN-DERIVE]`:** the four frozen stepped artifacts are
  byte-identical to HEAD (SP-6, sha-verified). The `_contpct` vintages are a
  NEW artifact family for a NEW pre-registered gate (the
  `pjm_offer_surface_within_season` precedent), identical statistics, only
  the conditioning key refined.
* **Rule 24 `[R-REGISTRY]`:** ONE `ScenarioConfig` field, in
  `run_config.json`, cache-key-registered dropped-at-default (the default key
  provably unmoved: `efd1cda1683a0ebe` with and without the field).
* **Rule 25 `[R-ISO-SCOPE]`:** ERCOT-gated everywhere; SP-1 non-ERCOT
  all-None, all years.
* **Rule 26 `[R-DELETE]`:** nothing deprecated, nothing zeroed; the stepped
  form remains the default and the continuous machinery stays merged
  default-off for the successor.
* **Rule 27 `[R-PUSH]`:** every push touching a ≥300-line file blob-verified
  against the REMOTE. Mid-session the branch was merged (PR #3723) and
  auto-deleted; the merged-PR protocol was followed (rebase of unmerged
  commits onto the new main, branch recreated via API, push, re-verify).
* **Rule 28 `[R-MECH-MATRIX]`:** duty (a) the DO-NOT-REDO check ran first
  (§1); duty (b) the cell verdict `U → R` + this citation landed in-session;
  duty (c) the row was added in the same PR as the field; duty (d) no
  cross-ISO verdict minted.
* **GitHub Actions:** no workflow added; every solve, derive, diagnostic,
  registration and score ran in-session.

**Environment notes (pre-existing, disclosed, not repaired here):** the
repo-wide pinned default cache key `603c2498bf71d21d` already mismatches at
origin/main in this container (computed `efd1cda1683a0ebe` with and without
this session's field); the NEISO nuclear-availability unit test expects an
empty crosswalk this regenerated clean tree now populates;
`emissions-unit-annual` regenerates 2018–2021 + 2023–2025 (no 2022 in the
curated span). The 60-Day DAM offers tidy parquet was rebuilt from the
immutable raw shards (deterministic parse; the 2023–2025 37/38-col vintage
lacks the three-part columns, so the parser gained the absent-column guard —
the same convention its carry-column fill already used; the 48-col 2026
refetches are outside the surface's pooled span and were excluded).

**DO-NOT-REDO honoured in full** — the ORDC/RTORPA lane, the reserve level,
temp-derate, the offline-increment tier, the event-cap ceiling lane (memo
still PENDING, not acted on), blanket `min()`, unit-scoped, the depth
premise, the reserve-side family, ramp mechanisms, the storage RT surface,
`energy_online_capability_cap`, the CC-headroom crosswalk, coal offer lanes,
per-year CT re-identification, West/Panhandle, ercot-172's C3, and every
capability/availability face stayed closed. §6's C3b-2024 bonus lane (the
frozen ceiling memo) was not entered.

**Next shorthand: ercot-179.**

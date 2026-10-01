# PRECHECK — caiso-178: the OASIS `PUB_DAM_GRP` intake, and whether it converts the caiso-176 `battery_dispatch_adder` BOUND into an IDENTIFICATION

**Session:** caiso-178 · branch `claude/caiso-178-public-bids-lfqw6q` · 2026-08-06
**Keeper at session start:** `2026-08-06-caiso-175-tac-intake` — determination **NOT-YET**
under rubric v3.1 (C3a FAIL 2024 +11.7 % / 2025 +14.8 %; C3c the sole ledgered caveat;
**8** criteria — C7 is RETIRED and `score_shape` is deleted). DOF `n_entries` 11 /
`n_residual` 8.
**CAISO ONLY.** No other ISO's keeper shard, registry entry or status part is touched.

**This document is written and pushed BEFORE any bid price is read.** At the time of
writing, exactly two things have been read out of the OASIS corpus: (a) that one sample
day downloads and is a valid zip (2024-01-10, 366,685 B), and (b) nothing else — the
first parse attempt failed on a missing interpreter dependency and was not retried before
this file was written. **No price, no MW value, and no aggregate of either has been read.**

---

## 0. What this session may not do (stated first, so nothing below can quietly override it)

* **The HOLDOUT SPEND FREEZE is ACTIVE** (`frontend/data/backcast/holdout-freeze.json`,
  declared 2026-07-25, narrowly lifted for NEISO-2022 only and **re-armed** 2026-08-06)
  and it **outranks any marker**. Solve years are **2023 / 2024 / 2025 only**, ONE bundle
  per arm (rule 16), years sequential, arms sequential (rule 12). `--holdout-authorized`
  is not used and would refuse anyway.
* **`holdout-freeze.json` and `calibration-complete.json` are OWNER ACTS.** This session
  writes neither. (It has no re-key duty either — see §0a.)
* **STATE CORRECTION, recorded rather than assumed.** This session's own handoff and the
  §5.2 matrix header both assert CAISO "holds `complete`". **It does not.** The committed
  `calibration-complete.json` carries CAISO under **`withdrawn`** (`declared` 2026-08-05,
  `withdrawn` 2026-08-06, `keeper_at_withdrawal` = the current keeper), withdrawn by owner
  directive on the rubric-v3.1 amendment because a `complete` marker cannot rest on a
  NOT-YET keeper. Nothing was ever spent under it. The §5.2 header's "not withdrawn by a
  NOT-YET determination (NYISO precedent)" sentence is **stale** and is corrected in this
  session under rule 28 duty (e). **This changes nothing about what this session may do** —
  the freeze already restricted it to 2023–2025 — but it is not left standing as an error.
* **Both walls stay walled.** C3a on non-public hourly pumped-storage water state
  (FINDING-caiso141; re-verified 5/5 `unchanged` on live bytes at caiso-176) and C3c on
  the SoCalGas OFO declaration record. `caiso_ps_charge_shape_anchor` stays **`G`** — that
  refusal rests on **the input being walled**, not on C3a's ledger status, so rubric v3.1
  does **not** reopen it and this session does not touch it.
* **An N–S topology lever against KNOWN-OPEN 1 stays FORBIDDEN** (caiso-164 §0/§6).

### 0a. Rule 22 authorization: none is required, and why

TASK 1 fetches **2023, 2024 and 2025 only** — the training window. `fetch_caiso_public_bids.py`
enforces this itself (`DEFAULT_YEARS` + an `ap.error` on any out-of-window `--years`). The
rule-22 spend gate governs **solving, scoring and registering** an out-of-training year;
intake inside the training window is not gated at all, and under the 2026-08-06 owner
clarification data intake is not gated by window in the first place ("what is held out is
the SCORE, never the DATA"). No marker is read, needed, or written.

---

## 1. TASK 1 — the intake

**What is fetched:** `data/raw/caiso-public-bids/zips/<YYYYMMDD>_PUB_BID_DAM_v3_csv.zip`,
one OASIS `PUB_DAM_GRP` GroupZip per DAM trade date, 2023-01-01 … 2025-12-31 (1,096 dates),
at the fetcher's 6 s inter-request spacing (OASIS returns an HTTP-200 AUP-violation HTML
page when polled faster). Both the downloader and the curator already exist and are
committed — `scripts/data/fetch_caiso_public_bids.py`, `scripts/data/curate_dam_public_bids.py`,
`scripts/lib/dam_public_bids/caiso.py` — so TASK 1 is an *execution*, not a build.

**What is committed and what is not.** The zips are **gitignored** by the
`pjm-energy-offers` precedent (~0.5–0.9 GB). Committed instead: the **derived artifact**
and **its deriver**, exactly as the rule-15 discipline requires the instrument to be
re-checkable.

**Coverage is reported honestly and nothing is silently dropped.** The fetcher already
distinguishes a genuine OASIS archive hole (an `ERR_CODE 1000` "No data returned" XML
inside a valid zip — e.g. 2023-06-01) from a rate-limit failure, and logs each. The
derived artifact carries, per year: dates requested, dates present, dates missing (listed),
and the row/resource counts that survived each classifier stage. **If any date is missing
for any reason, it is named in the finding.** No cap, no sample, no top-N truncation is
applied anywhere in the derivation; if one becomes necessary for memory it is logged as a
dropped-coverage note, per rule 15's no-silent-caps discipline.

---

## 2. TASK 2 — what is being asked, and why the caiso-176 wall is the thing to beat

caiso-176 established, **model-free**, that CAISO's DAM battery discharge marginal cost is
**≤ \$15/MWh in all three years** — from the `bid_stack` sheet of CAISO's own Daily Energy
Storage Report. That **BOUNDS** the parameter; it does not **IDENTIFY** it, because the
published grain is a **15 \$/MWh-wide bucket exactly where the parameter lives**
(`(0,15]`, carrying 8.72 / 16.43 / 17.52 % of priced DAM discharge volume).

`PUB_DAM_GRP` carries the **actual piecewise breakpoint PRICES** at masked-resource grain.
It therefore attacks the wall at precisely the point the wall is made of — resolution.
It cannot remove the wall's other half: a bid is bounded **below** by marginal cost, which
is what makes the one-sided inference valid and is also exactly what stops it becoming a
two-sided identification. **So the expected outcome is a sharper bound, and a sharper bound
is a result.** The one route to a genuine identification is §4's mass-point test, and it is
gated hard.

### 2a. The two instruments are complements, and that is the design

| | grain | labels | what it gives |
|---|---|---|---|
| Daily Energy Storage Report `bid_stack` (caiso-176) | **15 \$/MWh buckets** | **LABELLED** — `RES_TYPE` ∈ {LESR, HYBD}, `STATE` ∈ {CHARGE, DISCHAR} | a bound, no resolution |
| OASIS `PUB_DAM_GRP` (this session) | **exact \$/MWh breakpoints** | **MASKED** — no fuel, no location, no technology | resolution, no labels |

Each supplies exactly what the other lacks. **That is why the caiso-176 instrument becomes
this session's CLASSIFIER VALIDATOR** (§3, H1b): CAISO's own labelled aggregate is used to
check a price-blind classifier built on the unlabelled corpus. No new assumption is
imported to do it.

---

## 3. The classifier — declared in full, and PRICE-BLIND by construction

The whole identification hinges on identifying a battery in a masked corpus. The classifier
is stated here **before any price is read**, and its defining property is that
**no price enters it at any stage**. It uses only: `resource_type`, `product`, the sign and
symmetry of the bid curve's **MW axis**, and **hour counts**. Every price-side result is
therefore an out-of-construction test of it.

### 3a. Stages

* **S0 — universe.** `resource_type == "GENERATOR"` (drops participating LOAD and
  INTERTIE), `product == "EN"`, `row_kind == "segment"`. Self-schedule rows are excluded
  from the priced stack before anything is read, exactly as caiso-176 did.
* **S1 — withdrawal-capable resource-hour.** Within one `(resource_seq, interval_start_utc)`
  EN curve: `min(segment_mw) ≤ −1` **and** `max(segment_mw) ≥ +1`. Only a resource that can
  *absorb* energy bids a negative cumulative-MW range; the schema documents this range as
  the "pumped/storage withdrawal range".
* **S2 — set `S`, storage-like resource-year.** A `(resource_seq, year)` is in `S` if it is
  withdrawal-capable in **≥ 50 %** of its EN curve-hours that year **and** has **≥ 500** EN
  curve-hours that year (so nothing is classified off a handful of hours).
* **S3 — set `B`, battery-like.** `S` restricted by **power symmetry**
  `sym = |p05(min_mw)| / p95(max_mw) ∈ [0.5, 2.0]`. A battery's charge and discharge
  ratings are near-equal; a **HYBD** resource carries co-located solar, so its absorb range
  is small relative to its injection range and it falls out. (caiso-176 §3b established the
  hybrid panel is *not* the LP's battery class and must not be read as one.)
* **S4 — set `B_noPS`, battery-like minus pumped storage.** From `B`, exclude any resource
  that is (i) ≥ 200 MW `p95(max_mw)`, (ii) present with ≥ 500 EN curve-hours in **all three**
  years, and (iii) drifts < 10 % in `p95(max_mw)` across those years — i.e. large, stable
  and pre-existing, which the battery fleet's 2023→2025 doubling is not. The excluded set's
  aggregate MW is reported against the known **~2,078 MW** CAISO pumped-storage fleet
  (FINDING-caiso140 §B) as a check on the exclusion.

**Headline set = `B_noPS`.** `S` and `B` are reported alongside as sensitivities.

### 3b. Known contamination and the SIGN of its bias — stated before the answer

Every contaminant this classifier can admit biases the estimate in the **same direction**:

| contaminant | its conduct | bias on a lower envelope |
|---|---|---|
| HYBD hybrids | bid **deeply negative** (caiso-176 §3b: `[-150,-100]` is the 1 % bound in every year) | **DOWN** |
| pumped storage | very low throughput cost | **DOWN** |
| participating load | excluded at S0 | — |

So contamination can only make the measured floor **too low**, i.e. only ever push toward
*changing* the incumbent. **A high result is therefore trustworthy and a low result is the
one that must survive §3c.** This asymmetry is declared now, not discovered later.

### 3c. The classifier's ERROR RATE — how it is measured, and the tolerance, both fixed now

An error rate cannot be *stated* before measurement; what can be fixed before measurement
is **the measurement and the threshold it must clear**. Both are fixed here:

* **H1a — CAPACITY.** Σ `p95(max_mw)` over `B_noPS`, per year, against the independently
  measured CAISO battery envelope **4,256.5 / 6,914.6 / 9,550.3 MW**
  (`caiso_storage_shape_anchor`, caiso-174). **PASS** iff within **±25 %** in all three
  years **and** the growth ordering 2023 < 2024 < 2025 is reproduced.
* **H1b — PRICE-BUCKET AGREEMENT (out-of-construction).** The classified set's DAM
  discharge **priced-volume shares**, bucketed into caiso-176's 11 published buckets, against
  the committed **IFM|LESR** shares in `results/calibration/_caiso176_bidstack_reservation.json`.
  **PASS** iff **mean absolute deviation across the 11 buckets ≤ 5.0 pp in each year** AND
  the lowest bucket carrying ≥ 1 % of priced volume is the **same** bucket as the published
  panel's in **≥ 2 of 3** years.
* **H1c — SENSITIVITY (robustness, not agreement).** The headline statistic (§4) is
  recomputed on `S`, `B`, `B_noPS` and at symmetry thresholds {0.3, 0.5, 0.7}. **If the
  headline moves by more than \$1.00 across that grid, the classifier is declared NOT
  ROBUST** and this session reports a wall regardless of what §4's mode test does.

**Verdict on the classifier:** VALIDATED iff H1a **and** H1b pass and H1c holds;
PROVISIONAL iff exactly one of H1a/H1b passes (⇒ the session may report a **bound only**,
never an identification); FAILED iff neither passes (⇒ §5 BRANCH III).

---

## 4. The statistic — the LOWER envelope of the discharge curve, never the upper rungs

**What is measured.** For each `(resource, hour)` curve in the classified set, the price at
which the resource offers its **first discharge MWh**:

* `p_hi` = price at `min{segment_mw : segment_mw ≥ 0}` — the first breakpoint on the
  discharge side. **Conservative** (biased UP).
* `p_lo` = price at `max{segment_mw : segment_mw ≤ 0}` — the step-convention price that
  applies at MW = 0⁺ when no breakpoint sits exactly at zero. **Aggressive** (biased DOWN;
  can be a charge-side price).

The true discharge reservation price is **bracketed** by `[p_lo, p_hi]`. **The headline uses
`p_hi`**, because only `p_hi` is unambiguously an offer to *discharge*. `p_lo` and the share
of curves where the two differ (i.e. no breakpoint at exactly 0 MW) are both reported.

**Why the lower envelope and not the stack.** A storage energy bid is an **opportunity-cost**
object — the value of holding stored energy for a later hour — which the LP already generates
endogenously through SOC + RTE. The upper rungs are equilibrium objects that presume the
scarcity the model lacks (ERCOT-162; caiso-176 §3a, where 12.8/22.7/22.2 % of priced DAM
discharge sits near the bid cap in `(500,1e+03]`). **Only the lower envelope is used**, and
the upper stack is reported solely as evidence *against* reading the corpus as a cost curve.

**Fleet aggregation.** Per resource-year, `q05_r` = 5th percentile of `p_hi` over that
resource's storage hours — its own best hour, when its continuation value is nearest zero and
its bid collapses toward its irreducible throughput cost. Fleet statistic = **median over
resources of `q05_r`**, with the full cross-resource distribution (p10/p25/p50/p75/p90)
reported. Resource-weighted, not hour-weighted, so one heavily-bidding resource cannot set
the fleet number.

**The mass-point (MODE) test** — the only route to an identification:

* the distribution of `p_hi` over battery discharge resource-hours on a **\$0.25 grid**;
* the modal bin and its share; the share within **±\$0.50** of the mode; the top 5 modal
  values;
* the same computed **weighting each RESOURCE equally**, so a spurious fleet mode
  manufactured by one bidder is excluded.

---

## 5. THE VERDICT RULE — all three branches, fixed before the outcome is read

* **BRANCH I — IDENTIFIES.** Requires **ALL** of:
  1. classifier **VALIDATED** (§3c);
  2. a **dominant mass point**: one \$0.25 bin (or a ±\$0.50 window) carries **≥ 20 %** of
     battery discharge resource-hours in **each** of 2023 / 2024 / 2025, and the same modal
     value survives the resource-equal weighting;
  3. **stability**: the three yearly modal values lie inside a **\$1.00** window;
  4. the modal value is **> \$0** — a \$0 or negative mode is a price-taking or
     curve-crossing artifact, **not** a cost, and is reported as such rather than adopted;
  5. **admissibility**: the value is **≤ \$15**, the caiso-176 bound. A value > \$15 is
     refuted twice over (§6) and would instead be read as *evidence the classifier is
     contaminated*, not as a new parameter.

  ⇒ identified value = the 3-year modal value, rounded to \$0.25. **This is not "a value
  picked from inside (0,15]"** — the DO-NOT-REDO forbids *choosing* a point because it sits
  inside the bound; a mass point is *determined by the data*, and if no mass point exists,
  BRANCH I does not fire. That distinction is the whole gate.

* **BRANCH II — SHARPER WALL.** Classifier VALIDATED or PROVISIONAL, but the mass-point test
  fails. Then: report the **new bound** (the fleet median of `q05_r` and its distribution),
  **leave `battery_dispatch_adder = 5.0` exactly as it is**, file the wall with the
  instrument committed, and say so plainly. **No arms, no solve, no bundle, nothing
  registered.** This is a result, not a failure to produce one.

* **BRANCH III — NO INSTRUMENT.** Classifier FAILED (H1a and H1b both fail). Then: report
  that `PUB_DAM_GRP` does not admit a validated battery classifier at masked grain, the
  caiso-176 wall stands **unchanged**, and the corpus's cost is recorded so no later session
  re-spends it expecting a different answer.

### 5a. If BRANCH I fires — the A/B, fixed now

* **Arm A — CONTROL**, the caiso-175 keeper recipe replayed unchanged **at this session's
  head**. **MANDATORY**: caiso-175 measured incidental code drift at
  **+0.168 / +0.049 / +0.115 \$/MWh** on load-weighted mean LMP — *larger in every year than
  its own treatment* — so differencing against the keeper's committed metrics **would
  misattribute**. Reproduction is by **`scenario_config` identity**, verified key-by-key
  against the committed keeper `run_config.json` fail-closed (the `gen_caiso175_attestation.py`
  method), not by trusting a remembered CLI string.
* **Arm B — TREATMENT**, identical but for the **one derived scalar**.
* Both arms: **2023 / 2024 / 2025 in ONE bundle** (rule 16), years sequential, arms
  sequential (rule 12), both **REGISTERED** (rule 15, keeper and probe alike) with
  `legitimacy_diagnostics.json` generated **per bundle** so C8 stays SCORED.
* **The caiso-101 throughput guard is re-imposed as a REPORTED quantity** on any arm solved —
  it is the gate that killed the last attempt on this same parameter.
* **Promotion basis — rule 14 `[R-ACCURATE]`.** A **DEGRADED criterion does NOT revert a
  correct measured input**: rule 14 makes a worse fit on accurate data a *discovered bug*,
  and the input stays while the residual becomes an open root-cause issue.
* **C3a is a LIVE FAIL, so a C3a move is REPORTED, never the promotion's basis** (rule 1
  `[R-STRUCT]`). A measured input is not adopted because it moved the residual, and not
  rejected because it didn't.

---

## 6. DO-NOT-REDO — carried verbatim from caiso-176, and binding on this session

* **Any value > \$15** — refuted **twice**: caiso-101's solved ±15 % battery-only throughput
  guard, and CAISO's own bid stack. The ATB route recomputes to **\$22.63** on today's
  constants (capex 285 → 452.6 \$/kWh) — *further* in the rejected direction, refused
  *a fortiori*.
* **`caiso_storage_as_reservation` as this parameter's replacement** — INERT at caiso-74,
  the whole AS-award family refuted by arithmetic at caiso-127/129.
* **Routing the LP through `_degradation_cost_per_mwh`** — imports the declared-**TUNABLE**
  `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25`. **DOF SUBSTITUTION, not closure.**
* **The bid stack's upper rungs, and the HYBRID panel, are NOT cost curves** (§3a/§3b of the
  caiso-176 finding).
* **A value picked from inside (0,15] BECAUSE it sits inside the bound** is a fitted value
  wearing measured clothing. §5's mass-point gate is what separates a *determined* value
  from a *chosen* one.

---

## 7. Governance fixed in advance

* **Rule 13 `[R-MEASURED]`** — no price residual is read at any point in the derivation.
  Every gate is a property of published bid data. The corpus is a rule-13-admissible
  measured market input only in the direction used here (a bound / a revealed convention);
  it is never fitted to a residual.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing is transferred. ERCOT's \$10 adder and its refuted
  `ercot_storage_rt_offer_surface` inform *what a bid is*, nothing more; every number here
  is CAISO's own.
* **Rule 20 `[R-DOF]`** — the DOF ledger entry is edited **only** if BRANCH I fires and the
  arm is promoted. Under BRANCH II/III it stays `identification: residual`, 11 / 8, with the
  new bound recorded in the finding rather than silently written into the attestation.
* **Rule 28 duty (b) + (e)** — the `battery_dispatch_adder` matrix cell and the §5.2 header
  are updated in **this same session**, whatever the branch, including the stale
  `complete`-marker sentence corrected in §0.
* **Rule 15** — any completed run is registered, keeper and probe alike. Under BRANCH II/III
  there is nothing to register because nothing is run.
* **Rule 22** — 2023–2025 only, freeze untouched, no marker written.
* **Rule 27 `[R-PUSH]`** — this session is Opus. Any push touching a file ≥ 300 lines is
  blob-verified immediately after.

## 8. Known-open, carried forward untouched

1. **The N–S congestion majority** — the model reproduces 5.2 / 2.4 / 2.9 % of the measured
   NP15−ZP26 basis. Named; no lever chartered; the N–S topology lever stays **FORBIDDEN**
   (caiso-164 §0/§6).
2. **C3a is an OPEN root-cause issue**, not an accepted limitation. Its closure route is the
   **walled** hourly pumped-storage water state — an owner-level data question, not a
   session lever.
3. **CAISO's 2023–2025 outage windows were regenerated on the current CAMPD detector**
   (intake_log 2026-07-24) and **the re-audit that entry flagged is STILL OUTSTANDING.** It
   is a precondition for spending 2022 and is raised to the owner in this session's finding.

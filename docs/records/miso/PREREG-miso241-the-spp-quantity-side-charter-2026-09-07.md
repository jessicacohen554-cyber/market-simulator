# PREREG miso-241 — the SPP quantity-side charter: **does a DOF-free form exist?** — and the instrument repair the question forced

**Pre-registration, pushed BEFORE any adjudicating quantity.** Every decision rule applied by
this session is fixed in this document (or in an ADDENDUM pushed before the numbers it governs).
**Zero LP** — no arm, no screen, no bundle, no registration, no field, no cell verdict.
Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly` (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training year will be
solved, scored or registered. MISO carries exactly **one** registered run (rule 15).

**Queue item taken (rule 28(a)): item 1, THE SPP QUANTITY-SIDE CHARTER** — miso-237's named
successor, the handoff's RECOMMENDED item and the only queue item with a form-tested admissible
object behind it (miso-236 found the driver, miso-237 form-tested it as quantity-side).

---

## 0. Standing facts, CODE AND COMMITTED CONFIG ONLY — established before this PREREG, non-adjudicating

No adjudicating quantity was computed before this document was written and pushed. The following
are readings of source and of the keeper's committed `run_config.json`.

* **F1.** The keeper's `run_config.json` carries `miso_seam_neighbour_hourly_ladder: true` **and**
  `miso_seam_neighbour_hourly_spp: true` (also `miso_manitoba_seam`, `miso_south_seam_split`,
  `miso_seam_flow_limit`, `miso_seam_export_limit`, `miso_seam_envelope_merit_cap`,
  `miso_seam_envelope_hour_ending_key`, `miso_seam_neighbour_anchored_ladder`,
  `miso_seam_measured_ladder`). `git.sha = e852c85c`.
* **F2.** `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[y]["PJM"]` and
  `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR[y]["SPP"]` each carry **BOTH** an `import` and an
  `export` row of eight offsets, in every year.
* **F3.** `inject_miso_seam_ladder_prices` merges the WHOLE per-seam dict
  (`ladder = {**ladder, **hourly}`, then `{**ladder, **spp_rows}`) and registers the seam in
  `anchors`; `_inject_seam_ladder` then applies `mc[row,:] = anchor + prices[k]` to **every**
  reference-price row of that seam — `import` **and** `export` alike. So on the keeper the PJM and
  SPP **export** bands are priced at `neighbour_hub(t) + δ_k^export`, cleared against the
  **spread**, not at a scalar cleared against the bus-price **level**.
* **F4.** The lane's four-seam reconstruction — `scripts/probes/_miso235_seam_variance_decomposition_phase0.py`
  line 233, copied unchanged by miso-236/237/238/239/240 — prices the export leg of **every** seam
  from `MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"]` and clears it on `p_bus < price_k`.
  **On PJM and SPP that is not what the keeper does** (F2/F3). South and Manitoba are unaffected
  (the overlay does not cover them). This is a defect in **this lane's instrument**, not in the
  keeper, not in any input and not in any registry table.
* **F5.** `SPP.interface_limit_mw = 4000`, `SEAM_FLOW_TRANCHES = 8` ⇒ band width `w = 500 MW`
  (PJM 7300/8 = 912.5; South 3000/8 = 375). `MISO_SEAM_DIBA["SPP"] = ("SWPP", "SPA")`.
* **F6.** The SPP seam's only quantity channel today is the measured `(month × hod)` p90
  deliverability envelope (`measured_seam_import_envelope`, import and export directions,
  `MISO_SEAM_FLOW_PERCENTILE = 90`, `hour_ending_key=True` on the keeper), applied as a
  merit-order waterfall (`miso_seam_envelope_merit_cap=True`): band `k`'s available width is
  `clip(env − k·w, 0, w)`, so `Σ_k bound_k = min(env, limit)` exactly.

**Why F4 is in scope and not a detour.** The charter's deliverable (a) — *what form could a
quantity-side neighbour-state mechanism take on the MISO–SPP tie* — cannot be answered without
knowing **which LP object actually sets that seam's quantity**, and that is measured on the lane's
reconstruction. An instrument that misprices the seam's live export leg cannot answer it. So the
repair is a precondition of the queue item, not a second topic.

## 0b. Basis discipline (carried from miso-234 §0a and restated at 235–240)

The Indiana-hub **RT** series (`_miso224_floor_anatomy_phase0.actual_zone_price`, `values="rt"`)
builds the finite-hour `ok` mask **byte-identically to miso-236/237/238/239/240**, so the hour set
is the predecessors'. Every merit signal and every regressor is the Indiana-hub **DA** series (the
basis the ladders were Q-Q derived against); the SPP seam's anchor is the measured **SPP NORTH hub
DA** (`measured_miso_spp_hub_prices`), the identical series the keeper solved on. RT and DA
correlate only +0.402 / +0.424 / +0.553 and are **never interchanged**. miso-240 Q-C2 confirmed the
lane's `da` really is `INDIANA.HUB` DA (1.0000 / 1.0000 / 1.0000), so the label is used and the
RT/DA split is named on every statement. miso-232's measured decile column
(+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here.

## 1. The provenance gate — SEVEN legs. If any fails, the instrument is BROKEN and NOTHING in §3–§5 is read

| leg | what it reproduces, in the predecessor's own metric | bar |
|---|---|---|
| **G-P1** | miso-235's `sigma_measured_mw` + `sigma_resid_measured_mw` (4 seams × 3 yr × 2) | ≤ 0.5 MW |
| **G-P2** | miso-236's **gated** `delta_r2_A_nohydro` (9 cells) | ≤ 0.005 |
| **G-P3** | miso-235's INCUMBENT four-seam `harness_corr_recon_vs_committed` **and** `mean_abs_level_error_mw` (3 yr × 2) | ≤ 0.002 / ≤ 0.5 MW |
| **G-P4** | miso-238's PJM `sat_share` (0.1740 / 0.0068 / 0.0000), on **miso-238's own all-8-bands predicate** | ≤ 0.002 |
| **G-P5** | miso-239's PJM `γ_MERIT` column (−870.18 / −930.93 / −791.43 MW/z), partial OLS | ≤ 0.5 MW/z |
| **G-X0** | the PJM export leg identically zero on the INCUMBENT reconstruction (miso-239's leg) | exactly 0 |
| **G-ID** | the prefix/band-count identity on **both legs of both reconstructions, all four seams**: `imp ≡ min(env_i^eff, n_i·w)` and `exp ≡ min(env_e^eff, n_e·w)`, with `n` the in-merit count | ≤ 1e-6 MW, and **zero** prefix violations |

`env^eff = min(env, interface_limit)`. **G-ID is a falsifiable claim, not bookkeeping**: it holds
only if each seam's in-merit set really is the prefix `{0 … n−1}`, i.e. only if the ladder is
monotone in the clearing direction on both legs. The count of hours in which it is not is reported
and gated at zero.

**Every gate is written to survive a predecessor artifact being missing**: a leg whose committed
predecessor JSON is absent is reported as `SKIPPED — artifact absent` with the path named, and the
remaining legs still bind. `origin/main` is re-read immediately before the probe runs and again
before the FINDING is written, because a parallel MISO lane landed its record mid-miso-239.

**If any leg fails:** the failure is published FIRST, at full magnitude; the repair is declared in
a pushed ADDENDUM **before** the repaired numbers exist; **no bar moves**; a repair that makes the
gate stricter is preferred; and if the failing run already emitted values this session was not
entitled to read, that is said and the repair is PROVEN unable to move them by exact comparison
against the committed pre-repair artifact (miso-240 §0a/§0b is the template).

## 2. Q-0 — THE INSTRUMENT REPAIR (GATED). It decides which reconstruction §3 reads

Two reconstructions, **identical in every other respect** — same `ok` mask, same envelope calls,
same `merit_cap` waterfall, same import legs, same South and Manitoba legs:

* **INCUMBENT** — miso-235's, byte-for-byte: every seam's export bands priced from
  `MISO_SEAM_LADDER_BY_YEAR[y][seam]["export"]`, cleared on `p_bus(t) < price_k`.
* **REPAIRED** — the seams the keeper's hourly overlay covers (PJM, SPP) take their export prices
  from the **same registry entry `_inject_seam_ladder` applies**: `anchor(t) + δ_k^export`, cleared
  on `p_bus(t) < anchor(t) + δ_k^export`, where `anchor` is that seam's measured hourly neighbour
  price. South and Manitoba are untouched.

**DECISION RULE — miso-235's own superseding rule, adopted verbatim and unchanged** (the rule by
which miso-235 superseded miso-234's three-seam instrument):

* **(I-1)** harness `corr(recon, committed)` **RISES** in all three years, **and**
* **(I-2)** `mean_abs_level_error_mw` is **NOT WORSE** in all three years.
* **REPAIRED SUPERSEDES** iff both hold. **INCUMBENT STANDS** otherwise — and in that case §3 is
  read on the INCUMBENT and this session publishes, against interest, that the lane's instrument
  does not match the keeper's construction on the SPP export leg **and reproduces the committed
  series better anyway**, which is a disclosure about the reconstruction's agreement, not a defence
  of it.

**Reported beside the gate, not gating:** per-seam σ and mean under both variants; the SPP export
leg's mean, σ and max MW under each; the share of hours in which the two variants' SPP export legs
disagree; and every predecessor model-side column recomputed on the superseding instrument.

**Fixed here, whatever Q-0 returns:**

1. This repairs **this lane's reconstruction** only. It changes **no** keeper, **no** input, **no**
   registry table, **no** derive and **no** solve. Rules 23 `[R-FROZEN-DERIVE]` and 14
   `[R-ACCURATE]` are untouched: no ladder is re-derived, no envelope value changes, no interface
   limit moves.
2. **The gated verdicts of miso-236 (SPP ADMISSIBLE) and miso-237 (SPP QUANTITY-SIDE) CANNOT move**,
   because both are computed on the **measured** seam flow and the **measured** residual and read
   no model reconstruction at all. This is fixed here so that no §2 result can be read as
   disturbing them.
3. The predecessor columns that **could** move are model-side and are named here in advance:
   miso-235 §4/§5's **SPP** rows (model σ, β, β ratio, σ_r, σ_r ratio, the four-seam contribution
   and its ratio), miso-237 §3b's **SPP** transmission ratios, and miso-238's reported **SPP** rows.
   Each is recomputed on the superseding instrument and **both values are printed**. If a
   verdict LETTER in miso-235 §4's SPP row changes, that is published as a superseding of
   **that row** under miso-235's own I-1/I-2 rule — the same rule by which miso-235 superseded
   miso-234 — and never as a withdrawal of anything else.
4. **PJM's columns are expected to be unaffected because `G-X0` says its export leg is identically
   zero, but that expectation is TESTED, not assumed**: the repaired PJM export leg is computed and
   its max |MW| reported. If it is non-zero, that is published at full magnitude and miso-239's
   `MERIT = g(s) − ḡ` identity — which *uses* the zero — is reported as resting on the incumbent
   instrument, with the repaired value beside it.

## 3. Q-1 — WHERE IS THE SPP SEAM'S QUANTITY SET? (GATED)

On the superseding reconstruction, using the exact identity G-ID verifies, each leg of each hour is
classified by **which argument of the `min` binds**:

* `CEILING-SET` iff `env^eff ≤ n·w` **and** `n ≥ 1` — a marginal change in the ceiling changes the
  leg's flow.
* `MERIT-SET` iff `n·w < env^eff` — a marginal change in the merit signal changes the leg's flow.
  (`n = 0` is merit-set: the leg is at zero and raising the ceiling does nothing.)
* Exact ties (`env^eff == n·w`) are counted as CEILING-SET and their share is reported separately.

**`ceiling_active_share`(year)** = share of `ok` hours in which **at least one** of the SPP seam's
two legs is CEILING-SET. **`merit_active_share`** is its mirror.

**DECISION RULE, gated on SPP** (PJM / South / Manitoba reported, never gated):

* **CEILING-SET SEAM** iff `ceiling_active_share ≥ 0.50` in **all three years**.
* **MERIT-SET SEAM** iff `ceiling_active_share < 0.10` in **all three years**.
* **MIXED** otherwise.

**READINGS, fixed here before the numbers:**

* **CEILING-SET** ⇒ the SPP seam's quantity is set by the deterministic `(month × hod)` template in
  the majority of hours. A quantity-side neighbour-state mechanism then **has** a live channel and
  **that channel is the ceiling** — i.e. the one object rule 14 `[R-ACCURATE]` protects and this
  lane's standing freeze forbids changing. It also explains, without being tuned to it, why
  miso-237 measured the SPP seam as under-transmitting **both** state blocks (0.07–0.28× on MISO's
  own): a calendar template cannot carry either.
* **MERIT-SET** ⇒ the ceiling is not the channel, a ceiling-side mechanism is structurally
  near-inert, and the charter must name a different object or refuse.
* **MIXED** ⇒ reported as such; it closes nothing on its own and the charter states what share of
  hours each candidate could reach.

**Reported, not gated:** `mean n_i`, `mean n_e`; `σ(env_i)`, `σ(env_e)` against the model's SPP net
σ and the measured SPP σ; `corr(model SPP net, env_i)`; and the share of hours the SPP seam sits at
exactly zero on both legs.

## 4. Q-2 — DOES THE ENVELOPE'S OWN ESTIMATOR CARRY THE NEIGHBOUR-STATE SIGNAL? (GATED)

**Measured data only.** No model quantity is read; nothing is built into any input; nothing is
armed. This measures whether the one construction whose estimator is *already in the codebase*
would have a footprint at all.

Construction — the envelope's own estimator, on a partition refined by neighbour state:

* Source: `data/raw/eia-930-interchange/MISO interchange hourly.parquet`, net import per seam per
  timestamp, `hour_ending_key=True` — the identical source, sign convention and hour key
  `measured_seam_import_envelope` uses.
* Conditioning variables, **both pre-registered**: `nl_nbr` = SWPP+SPA `Demand (MW) (Adjusted)`
  − wind − solar; `vre_nbr` = SWPP+SPA wind + solar. Built by miso-236's identical `ba_series`
  construction on the same UTC join, from `data/raw/eia-930/EIA930_BALANCE_*.parquet`.
* Within each `(month × hod)` bucket carrying **≥ 12** finite paired samples (floor fixed here),
  split by tercile of the conditioning variable and take the **same p90** in each tercile.
* `spread(bucket) = p90(T3) − p90(T1)`, T3 = high. The statistic is the **sample-weighted mean
  spread** over buckets, per year, per direction (import and export).
* **Null:** 200 within-bucket permutations of the conditioning variable, seed **20260907** (fixed
  here); `z = (spread_real − mean(spread_null)) / std(spread_null)`.
* **Materiality:** `|spread_real| ≥ 0.10 × mean(env)`, that seam-year's own committed envelope mean
  in the same direction. A scale-free floor taken from the model's own object, **not** from any
  residual and **not** from miso-236's sizing, which stays un-targetable.

**DECISION RULE, gated on SPP:**

* **FOOTPRINT PRESENT** iff, for **at least one** conditioning variable and **one** direction:
  `|z| ≥ 3.0` in all three years **and** the materiality bar clears in all three years **and** the
  sign is identical in all three years.
* **INERT** iff for **both** variables and **both** directions `|spread_real| < 0.02 × mean(env)`
  in all three years.
* **NOT MEANINGFUL** otherwise, and it attaches nothing in either direction.

**READINGS, fixed here:** FOOTPRINT PRESENT means the candidate whose estimator is the envelope's
own does carry measurable neighbour-state signal — which makes it a **well-posed owner question**
and **nothing more**. It does not charter, arm, size, name a field or license anything, and the
standing freeze still refuses it. INERT means the charter can refuse without needing the freeze at
all. Every number here is **declared UN-TARGETABLE before it is computed** (rules 1 `[R-STRUCT]` /
13 `[R-MEASURED]`): no successor may size, scale or tune any mechanism to make a modelled quantity
land on it.

**Reported beside it, never gated:** the same columns for PJM, South and Manitoba; the same columns
with **MISO's own** net load as the conditioning variable (the comparator miso-237 §3b's
under-transmission finding invites); and the per-year bucket count clearing the sample floor.

## 5. Q-3 — THE CHARTER. The candidate enumeration and the DOF rule, FIXED HERE BEFORE ANY NUMBER

The candidate set is fixed here so that it cannot be tailored to the measurements. A candidate
discovered later may be **added and named**, but must be labelled **POST-HOC** and its addition
must be shown not to change the verdict.

| id | candidate form | where it acts |
|---|---|---|
| **C1** | **State-conditioned deliverability envelope** — the same p90 on a `(month × hod × neighbour-state bin)` partition | the import/export ceiling |
| **C2** | **Neighbour-surplus cap** — cap SPP import at (neighbour capacity − neighbour net load) × a tie share | the ceiling |
| **C3** | **Neighbour-state derate window** — SPP bands derated when the neighbour's state crosses a threshold | the ceiling, windowed |
| **C4** | **Explicit neighbour supply stack** — SWPP+SPA as a modelled zone with its own load, VRE and fleet behind the tie's TTC | replaces the priced-band seam entirely |
| **C5** | **Neighbour state inside the merit test** — `δ_k` or the offered price made a function of neighbour state | the price/merit channel |
| **C6** | **Re-conditioned envelope** — replace the calendar partition with a neighbour-state partition | the ceiling |
| **C7** | **Measured tie or neighbour-fleet outage windows** — a physical availability event on the interface or behind it | the ceiling, event-driven |

**C7 carries a data census leg**, settled in the probe the way miso-236 settled the
scheduled-interchange question: does this repository hold **any** measured MISO–SPP tie outage /
derate series, or any SPP reliability-event (EEA / conservative-operations) log? The answer is
recorded whatever it is, with the paths searched named.

**DOF CLASSIFICATION RULE, fixed here.** A candidate is **DOF-FREE** iff every constant it
introduces is either (i) produced by an estimator **already in the codebase** reading a committed
measured source, or (ii) fixed by an identity or a published external definition — **and** none is
selected by, or selectable against, any residual, gate or scored criterion. A candidate is
**ADMISSIBLE** iff it is DOF-free **and** rule-13 `[R-MEASURED]` admissible (the same quantity is
producible for a forward year from forward drivers and responds to changed conditions) **and**
satisfies rule 19 `[R-ONE-MECH]` by **REPLACING or RECONCILING** with the SPP seam's existing
mechanisms rather than stacking on them **and** breaches no standing freeze.

**CHARTER VERDICT RULE, fixed here:**

* **CHARTERED** iff at least one candidate is ADMISSIBLE. The charter then writes deliverables
  (a) form, (b) rule 13 in full, (c) rule 17 `[R-FLOOR-WINDOW]` in full, (d) rule 19 in full — and
  still **names no field and arms nothing**.
* **REFUSED — NO DOF-FREE FORM** iff no candidate is DOF-free. Deliverable (c) is then recorded as
  **not owed**, exactly as miso-240 §6(c) recorded it, and (d) is written anyway.
* **REFUSED — FREEZE-BOUND** iff the only DOF-free candidate(s) breach a standing freeze. The
  deliverable is then the **owner question**, stated precisely, with Q-1's and Q-2's measurements
  attached and the freeze named. This session does not lift a freeze and does not ask to.

**The rule-19 enumeration is written whatever the verdict** (miso-240 §6(d)'s discipline). What
already sets the MISO–SPP seam on the keeper: the armed hourly SPP neighbour anchor
(`miso_seam_neighbour_hourly_spp`, band `k` at `spp_hub(t) + δ_k`, **import and export**, F2/F3);
the frozen Q-Q `δ_k` ladders (`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`, derived, frozen,
pinned to their derive by test); the incumbent MISO-hub Q-Q ladder it displaces
(`MISO_SEAM_LADDER_BY_YEAR["SPP"]`); the measured `(month × hod)` deliverability envelope in both
directions with the merit-order waterfall (`miso_seam_flow_limit`, `miso_seam_export_limit`,
`miso_seam_envelope_merit_cap`, `miso_seam_envelope_hour_ending_key`); the seam's 4,000 MW
interface limit and its eight 500 MW bands; the `MISO_external` border-link TTCs; the 8,700 MW
`MISO_simultaneous_import` SIL; and the published CIL/CEL deliverability groups.

## 5.2 What this session does NOT license — restated BEFORE the numbers, and it binds for EVERY outcome

1. **NOTHING HERE LICENSES TOUCHING THE LADDER OR THE ENVELOPE.** The PJM and SPP `δ_k` ladders stay
   derived, frozen and pinned to their derives by test (rule 23); the measured `(month × hod)`
   envelope stays a measured input (rule 14). **No re-derive, no damping factor, no change of `K`,
   no re-spacing of `δ_k`, no envelope change, no interface-limit change, no percentile change.**
   Q-2 **measures** a candidate partition; it does not build one, and a measured footprint is not a
   licence.
2. **Nothing here is a tuning target.** No successor may size, scale, tune or select any mechanism
   to make a modelled σ, share, correlation or MW value land on a number produced by this session
   (rules 1 / 13). miso-236's 328.6 / 341.7 / 207.5 MW sizing stays **un-targetable** and is not
   re-quoted as a target; the committed-solve system ratio 1.99 / 3.12 / 5.56× is the lane's stated
   object and is not a target either.
3. **No adjudicated cell is re-tested** (rule 28(a)). Standing and untouched: queue item 1 (the
   external-bus price) **CLOSED**; the per-seam external-node split **REFUSED at zero LP**; the
   saturation hypothesis **REFUTED**; miso-239's Q-A **MIXED** and Q-C **SURVIVES**; the
   `(month × hod)` template hypothesis **REMOVED**; the PJM import/export asymmetry **CLOSED FOR
   PJM**; South's neighbour-state route **CLOSED**; `miso_manitoba_seam` **CLOSED as already-armed**;
   `internal_congestion_split` **G**; `vre_reference_rate_curtailment_grossup` **K**;
   `measured_interface_limits` **R**; `miso_rdt_measured_limit` **R**;
   `miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
   `miso_south_gas_delivered_cost_basis` **R**. **Q-B (miso-240 §7.4) stays UNRESOLVED** and is not
   re-litigated here.
4. **No cell verdict moves**; rule 28(b) attaches in its evidence-appending form only, in MISO's
   shard only (rule 25 `[R-ISO-SCOPE]`).
5. **No promotion, no decertification.** MISO is CALIBRATED today and nothing here trades a passing
   gate. C3c is untouched and stays the designated frontier; no LP is authorized there and none is
   sought.
6. **No field is minted and nothing is armed**, whatever the charter verdict. A CHARTERED verdict
   names an object for a successor and an owner; it does not create a `ScenarioConfig` field.
7. **The model side is a RECONSTRUCTION** (miso-235's four-seam form, harness `corr` +0.9845 /
   +0.9745 / +0.9839 on the incumbent), labelled as one wherever it appears. **2024 is the loosest
   year** and every 2024 reading is reported with that stated.

## 5.3 Disclosure duties this session accepts in advance

* If the provenance gate fires on this session's own instrument, the failure is published **first**,
  at full magnitude, and the repair is declared in a pushed ADDENDUM before the repaired numbers
  exist (§1).
* Every column is labelled **GATED** or **REPORTED**, and a reported column is never converted into
  a verdict however suggestive — miso-240's Q-B is the standard.
* Any quantity computed but not named in this PREREG or a pushed ADDENDUM is labelled **POST-HOC**
  and shown arithmetically to move no verdict.
* A pre-registered mapping that turns out to over-claim is **withdrawn as an interpretation** with
  the arithmetic left standing (miso-239 §0b), and a suspicion raised in advance that this
  session's own gate refutes is recorded as refuted (miso-240 §0d).
* Where this session's statistic is **not** a predecessor's, it says so before the number is read
  (miso-237 §0).

## 6. Governance

Rule 1 `[R-STRUCT]`: nothing is proposed, selected or judged by a residual; every gate is
structural; every number is declared un-targetable before it is computed. Rule 12 `[R-PARALLEL]`:
no LP; nothing runs on CI. Rule 13 `[R-MEASURED]`: measurement only; no input changes and no
measured outcome enters any solve; §5's admissibility rule is fixed before the numbers, and
miso-236 PREREG §2c's named inadmissible forms (the DIBA interchange series itself, neighbour Net
Generation as a whole, any noise term, variance inflator, damping factor or tuned scalar) bind here
unchanged. Rule 14 `[R-ACCURATE]`: no input changes; the measured envelope is untouched. Rule 15
`[R-DASHBOARD]`: no run is produced, so nothing is registered or pruned; MISO keeps exactly one
registered run and the keeper's `hourly/` sidecars stay committed. Rule 17 `[R-FLOOR-WINDOW]`: no
floor is added; §5 fixes when the leg is owed and when it is not. Rule 19 `[R-ONE-MECH]`: no
mechanism is added; the enumeration is written regardless. Rule 21 `[R-DOF]`: **41/2, unchanged**;
every instrument here carries **zero** free parameters except the two explicitly declared design
constants of Q-2's null (200 permutations, seed 20260907) and its sample floor (12), none of which
can move a verdict's direction. Rule 22 `[R-HOLDOUT]`: 2023–2025 only. Rule 23 `[R-FROZEN-DERIVE]`:
no derive is re-run. Rule 24 `[R-REGISTRY]`: no field is created. Rule 25 `[R-ISO-SCOPE]`: MISO's
shard, section and lane only. Rule 26 `[R-DELETE]`: a defective predicate is replaced, never left
behind a flag. Rule 27 `[R-PUSH]`: on-disk edits only; every pushed blob ≥ 300 lines is verified
against local after push. Rule 28(a): queue item 1 (the SPP quantity-side charter) is taken and
named here. Rule 28(b): evidence-append form only. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP
phase 0, and no screen is chartered.

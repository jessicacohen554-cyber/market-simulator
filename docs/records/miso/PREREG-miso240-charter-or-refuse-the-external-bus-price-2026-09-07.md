# PREREG miso-240 — CHARTER OR REFUSE queue item 1: the model's own external-bus price `s = p(MISO_external) − p(PJM_border)`. Four gated legs, zero LP, zero DOF

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a
pre-registration and correctly forfeited its right to close or re-open anything on its own
numbers; miso-235, miso-236, miso-237, miso-238 and miso-239 each did. This session follows them.

**Keeper `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF 41/2. **MISO HAS NO FAILING
GATE**, and there is no rubric failure anywhere in the program, so nothing here targets one.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training
year is solved, scored or registered. MISO carries exactly ONE registered run (rule 15).

**ZERO LP IS PLANNED.** No `ScenarioConfig` field is created or armed, no bundle is produced, no
run is registered or pruned, the keeper is not replayed and not touched.

**Queue item taken: item 1** (rule 28(a)), the successor question miso-239 §6 NAMED and
explicitly did NOT charter. The handoff fixes what a charter owes at zero LP **before any field
is named**: (a) how `MISO_external`'s price is FORMED in the LP, and whether its own-net-load
response is a modelling artefact or a real seam property; (b) what the MEASURED analogue of `s`
is and on which basis, NAMED; (c) rule 17 `[R-FLOOR-WINDOW]` in full; (d) rule 19
`[R-ONE-MECH]` — enumerate everything already setting the PJM seam and say REPLACES or
RECONCILES, never stacks. **A DOF-free construction is the bar. If no DOF-free form exists,
saying so and stopping is a complete session result**, and this PREREG fixes the rule that would
produce that outcome before the numbers.

---

## 0. State of the record and of the basis — STATED FIRST, BEFORE ANY NUMBER

### 0a. `origin/main` was re-read at the moment this PREREG was written, not only at session start

miso-239 ADDENDUM §4's instruction, adopted. At `origin/main` = **`d2080978`** (2026-09-07) the
miso-235 / miso-236 / miso-237 / miso-238 / miso-239 records are **all complete** — FINDINGs,
PREREGs, ADDENDA, probes and phase-0 JSONs. §1's gate reproduces the two predecessor columns
this session actually stands on **from scratch** anyway, in the predecessors' own metrics, so it
survives any of them being absent (the property miso-239's G-P4 was written for and which it
demonstrated). `main` is re-read again before the first push.

### 0b. Basis discipline (carried verbatim from miso-234 §0a / 235 §0b / 236 §0b / 237 §0b / 238 §0b / 239 §0c — it bit a first draft)

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. The lane's scored basis. Builds the finite-hour `ok` mask byte-identically to
  miso-236/237/238/239, so the hour set is the predecessors'.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the
  basis of the regressor `p1 = da − p_border` and of every merit signal.

They correlate only +0.402 / +0.424 / +0.553 and are never interchanged. miso-232's measured
decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by anything here, and
miso-233's own measured South column is not restated as miso-232's.

### 0c. What was established BEFORE this PREREG was written — CODE READING ONLY. No adjudicating quantity is among them.

1. **`MISO_external` is a ZERO-LOAD TRANSSHIPMENT NODE, appended to the topology by
   `import_nodes.extend_with_import_node`** as `Zone(name="MISO_external", load_share=0.0)`
   plus its border links from `spec.IMPORT_NODE_LINKS["MISO"]` —
   `MISO-Illinois` 3,300 · `MISO-Indiana` 2,000 · `MISO-East` 2,000 · `MISO-West` 4,000 ·
   `MISO-South` 3,000 MW. On the keeper (`miso_south_seam_split: true`)
   `miso.split_miso_south_external_node` re-homes the South link onto
   `MISO_external_South`, so the shared node keeps **four** border links, all to Midwest zones.
2. **The keeper's four priced seams are hosted as PSEUDO-GENERATORS INSIDE that node.**
   `import_nodes.build_reference_price_node` places `SEAM_FLOW_TRANCHES = 8` import bands
   (`pmax = limit/8`, `pmin = 0`) and 8 export bands (`pmax = 0`, `pmin = −limit/8`) per seam in
   the ISO's `IMPORT_ZONE`; PJM, SPP and Manitoba land in `MISO_external`, South alone in
   `MISO_external_South` via `zone_overrides`. Their marginal cost is injected hourly by
   `inject_reference_price_mc` / `_inject_seam_ladder`.
3. **So `p(MISO_external)` is the LP dual on a zero-demand energy balance whose only terms are
   the seam bands and the four border-link flows.** Three code facts bound what can set it:
   * the four border links are **lossless** `TransferLink`s with `flow_cost = 0.0` and
     `is_bidirectional = True` (`miso_zonal_loss_surface` is **False** on the keeper, and
     `apply_miso_zonal_loss_links` splits **Midwest-internal** links only);
   * for a lossless zero-cost link, an **interior** flow forces the two zones' duals equal, a
     flow at `+ttc` gives `p_border ≥ p_ext`, at `−ttc` gives `p_border ≤ p_ext`;
   * a **partially dispatched** seam band forces `p_ext` to that band's injected mc — for PJM's
     armed hourly anchor that is exactly `p_border(t) + δ_k`, i.e. `s(t) = δ_k`.
   `EXTERNAL_SIMULTANEOUS_LIMITS["MISO"]` adds one aggregate `InterfaceLimit`
   (`MISO_simultaneous_import`, 8,700 MW, bidirectional) on the **signed sum** of the border
   links, which can wedge `p_ext` away from every zone price at once.
4. **The Midwest-internal links carry a 40,000 MW `_placeholder_ttc`**
   (`iso_configs._miso_config`), so internal *link* capacity effectively never binds; what binds
   internally are the published per-zone **CIL/CEL** `InterfaceLimit` groups
   (`build_miso_deliverability_groups`). The code states in `split_miso_south_external_node`'s
   own docstring that the shared bus lets the LP wheel between border zones "through the
   external zone's energy balance without touching any priced seam band", and
   `build_miso_deliverability_groups` states that "External-node border links are NOT members"
   of the CIL/CEL groups. **Both are docstring facts, not measurements**, and §3d measures the
   only footprint of them observable from prices alone.
5. **A zone-resolved MEASURED MISO price series exists on disk.**
   `data/raw/lmp-data/MISO/README.md` documents
   `scripts/derive_miso_hub_lmp.py` → `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`,
   hub → model zone: `MINN→MISO-West`, `ILLINOIS→MISO-Illinois`, `INDIANA→MISO-Indiana`,
   `MICHIGAN→MISO-East`, `ARKANSAS/LOUISIANA/TEXAS/MS→MISO-South`; **`MISO-Plains` has no hub**.
   Its existence is a file fact; whether it is USABLE as the measured analogue of `s` is
   §3c's gated question and is not assumed.
6. **`MERIT = g(s) − ḡ` exactly on PJM**, `g(x) = Σ_k b̄_k·1[x > δ_k]`, `K = 8` — miso-239's
   G-X0 (PJM export leg identically 0.000000 MW) and §0d(2), re-verified here as §1's G-X0.
   This is the arithmetic §3b rests on and it was established before any data.
7. **miso-239's `γ_np(s)` column is REPORTED-NOT-GATED and chartered nothing** (its §4, its
   PREREG §4). This session does not treat it as a verdict; §3b tests whether it is *evidence at
   all*, and the test is declared here before it is run.

---

## 1. The provenance gate — reproduce the PREDECESSORS before reading anything new

Fixed ex ante. **Nothing in §3 is read or published unless all five legs clear.** Reference
values are read from the committed predecessor JSONs **and** cross-checked against the values
the handoff quotes, both restated here before recomputation.

| leg | what it reproduces | reference | bar |
|---|---|---|---|
| **G-P1** | miso-239's `γ_MERIT` (PJM, partial OLS) | −870.18 / −930.93 / −791.43 MW/z | ≤ 0.5 MW/z |
| **G-P2** | miso-239's channel shares `σ_LIN` / `σ_CURVE` / `σ_STEP` | 0.6679/0.3063/0.0259 · 0.2839/0.6816/0.0345 · 0.7312/0.2210/0.0479 | ≤ 0.005 |
| **G-P3** | miso-239's two ventile columns `γ_np(p1)` and `γ_np(s)` | −677.62 / −662.69 / −590.15 and −15.70 / +2.00 / −4.41 MW/z | ≤ 0.5 MW/z |
| **G-P4** | miso-238's `γ_model` (PJM) | −866.18 / −1043.37 / −843.45 MW/z | ≤ 0.5 MW/z |
| **G-X0** | the PJM export leg is identically zero, all three years | exactly 0 | exact 0 |

Two identity legs, also gating:

* **G-ID1** — the band-count identity `g(s) ≡ G_{n−1}` (the ladder is sorted, so the in-merit
  set really is `{0..n−1}`): `≤ 1e-6` MW.
* **G-ID2** — the **support identity** §3b rests on: the residual of `MERIT` on ventile dummies
  of `s` is **exactly zero** on every ventile bin containing no `δ_k`, and likewise for the
  `p1`-mirror in §3b: `≤ 1e-9` MW. If this fails, §3b's mechanism claim is wrong and §3b is
  declared BROKEN and not read.

**If any leg fails, the instrument is declared BROKEN, the failure is published, and NOTHING in
§3 is read.** miso-238 §0's discipline, adopted whole — its gate fired on its own instrument.

## 2. The tie tolerance, fixed here before any number

`τ = $0.01/MWh`, used by §3a and §3d to decide whether two duals are the *same* dual. It is a
numerical tie tolerance on an LP dual, not a tunable: **`τ = $0.001` and `τ = $0.10` are
computed and REPORTED as a declared sensitivity in the same run**, and if the §3a or §3d verdict
differs under any of the three the verdict is published as **FRAGILE** and closes nothing.

## 3. The four gated legs, with every decision rule fixed here, before the numbers

All on the `ok` mask, all three years, PJM the gated seam (the only seam where
`MERIT = g(s) − ḡ`, §0c(6)).

### 3a. Q-A (GATED) — HOW IS `p(MISO_external)` FORMED? Deliverable (a)

Per hour, classify `p_ext` into three mutually exclusive, exhaustive classes over
`B = {MISO-Illinois, MISO-Indiana, MISO-East, MISO-West}` (the shared node's four border zones
on the keeper's topology, §0c(1)):

* **ZONE** — `∃ z ∈ B : |p_ext − p_z| ≤ τ`.
* **BAND** — not ZONE, and `p_ext` ties within `τ` an injected offer level of a seam hosted in
  `MISO_external`: PJM import `p_border(t) + δ_k^PJM`, SPP import `spp_hub(t) + δ_k^SPP`,
  Manitoba import `δ_k^MB`, or any of those seams' export levels `λ_k`.
* **NEITHER** — otherwise.

**Verdict ladder, read in this order, all three years or MIXED:**

1. **INTERNAL-PRICE FORMATION** iff `share(ZONE) ≥ 0.50` in all three years.
2. **SEAM-SELF-REFERENTIAL** iff `share(BAND) ≥ 0.50` in all three years.
3. **MIXED** otherwise.

**The reading of each verdict is fixed HERE, before the numbers:**

* **INTERNAL-PRICE FORMATION ⇒ `s`'s own-net-load response is a REAL property of a MISO energy
  price, NOT a modelling artefact.** `p_ext` is then a Midwest zonal dual — a price that
  responds to MISO net load because MISO's price does — and the answer to item 1's own question
  *"is its own-net-load response a modelling artefact or a real seam property?"* is **REAL**.
  A large response is then not by itself a defect, and **no artefact exists at the `s` side to
  charter**.
* **SEAM-SELF-REFERENTIAL ⇒ the merit test is degenerate** (`p_ext` is set by the very offer it
  is tested against, so `s(t) = δ_k` by construction) and item 1 has a genuine artefact.
* **MIXED ⇒ closes and licenses nothing**, exactly as miso-239 PREREG §3a's MIXED did.

**REPORTED, NEVER GATING:** the per-zone tie share; the number of `B`-zones tied per hour; the
share where all four tie (one Midwest price); the share where `p_ext = min_{z∈B} p_z` and where
`p_ext = max_{z∈B} p_z`; and the same census on `MISO_external_South`. No verdict reads any of
them.

### 3b. Q-B (GATED) — IS miso-239's `γ_np(s)` COLUMN EVIDENCE AT ALL? A declared PLACEBO

miso-239 §4 published `γ_np(s)` = −15.70 / +2.00 / −4.41 MW/z (1.8 / 0.2 / 0.6 % of `γ_MERIT`)
against `γ_np(p1)` leaving 78 / 71 / 75 % standing, labelled it **REPORTED, NOT GATED**, and
chartered nothing on it. The handoff carries it forward as *"This EVIDENCE points at `s` itself"*.
**This leg tests whether it is evidence, and the test is a placebo declared before it is run.**

The mechanism claim, stated before the numbers: `MERIT = g(s) − ḡ` is **measurable with respect
to `s`**, so residualizing it on a partition of the `s`-line leaves a residual supported ONLY on
the partition cells that straddle a `δ_k` — at most 8 of 20 ventile bins. If that is what the
column measures, the same annihilation must occur for **any** series put through the same
construction, including one with **no model price in it at all**.

**The placebo, fixed here.** Define `MERIT_p1(t) = g(p1(t)) − mean` — the SAME frozen ladder
function `g` (same `b̄_k`, same `δ_k`) evaluated on the **measured** spread `p1` instead of the
model spread `s`. It contains no model bus price anywhere. Compute
`γ_np(p1 | MERIT_p1) = γ( resid( MERIT_p1 | [1 | ventiles(p1)] ) )` with miso-237's
`ventile_dummies(·, bins=20)`, and the mirror `γ_np(s | MERIT_p1)`.

**Verdict, all three years:**

* **SELF-CONDITIONING ARTEFACT** iff `|γ_np(p1|MERIT_p1)| ≤ 0.25·|γ(MERIT_p1)|` in all three
  years **and** miso-239's `|γ_np(s)| ≤ 0.25·|γ_MERIT|` reproduces (G-P3).
* **NOT AN ARTEFACT** iff `|γ_np(p1|MERIT_p1)| ≥ 0.50·|γ(MERIT_p1)|` in all three years.
* **MIXED** otherwise.

**ABSOLUTE FLOOR:** read only where `|γ(MERIT_p1)| ≥ 100` MW/z in all three years; below it the
leg reads **NOT MEANINGFUL** and nothing attaches — the role miso-238's 200 MW/z floor and
miso-239's 100 MW/z sub-floor played.

**The reading is fixed HERE:** **SELF-CONDITIONING ARTEFACT ⇒ the s-vs-p1 ventile contrast
restates the code fact `MERIT = g(s)`, which miso-239 PREREG §0d(2) established BEFORE any data,
and carries NO information about `s` as an object.** The handoff's *"points at `s` itself"*
reading is then **withdrawn as over-reading** — a withdrawal of an interpretation, on the
miso-239 §0b pattern, with the arithmetic untouched. **Nothing miso-239 published moves**: it
labelled the column reported-not-gated, said in advance it "cannot move a verdict", and
chartered nothing on it. Reported beside the verdict, never gating: `n_impure`, `h_impure` and
the pure-bin support identity (G-ID2), which are the *mechanism* of the artefact.

### 3c. Q-C (GATED) — DOES A MEASURED ANALOGUE OF `s` EXIST AT THE MODEL'S OWN PRICE LOCATION? Deliverable (b)

`s = p_ext − p_border` and `p1 = da − p_border` share the border leg exactly, so
**`s − p1 = p_ext − da`**: the entire difference between the model's merit signal and the
pre-registered regressor is the model's external-bus price against the measured **Indiana-hub
DA**. If §3a returns INTERNAL-PRICE FORMATION, `p_ext` is a *Midwest zonal* dual, and the
Indiana hub is only one of four candidate locations for its measured analogue.

Candidate, NAMED with its basis: **`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`**,
per model zone, on the **DA** basis (the basis `δ_k` was Q-Q derived against, §0b) with the
**RT** basis reported beside it and never interchanged.

**Verdict, fixed here — an existence-and-usability gate, three legs, all required:**

* **EXISTS** iff (i) the parquet carries all four `B` zones in all three years; (ii) hourly
  coverage on the fixed 8,760 grid is `≥ 0.95` per zone-year on the DA basis; and (iii) its
  `MISO-Indiana` DA column reproduces the lane's own `da` series (from
  `scripts/data/derive_miso_seam_ladders.load_joined`) to `≤ $0.01/MWh` in `≥ 99 %` of `ok`
  hours — the provenance link that makes it a **re-location of the lane's existing measured
  object**, not a new dataset.
* **DOES NOT EXIST** otherwise, with the failing leg named.

**REPORTED, NEVER GATING and explicitly NEVER A TUNING TARGET** (rules 1 / 13): per border zone
`z`, `corr(p_meas,z^DA − p_border, s)` and `corr(·, p1)`; the zone-matched analogue
`s_meas(t) = p_meas,ẑ(t)^DA(t) − p_border(t)` with `ẑ(t)` the zone `p_ext` ties in hour `t` from
§3a, and `corr(s_meas, s)`, `corr(s_meas, p1)`. **No successor may size, scale, tune or select
any mechanism to make a modelled quantity land on any of these** — the restriction miso-236
ADDENDUM §A, miso-237 PREREG §4, miso-238 PREREG §5.3 and miso-239 PREREG §5.3 fixed for theirs.

### 3d. Q-D (GATED) — IS THE SHARED STAR NODE COUPLING BORDER ZONES? Deliverable (d)'s live alternative

The shared node hosts PJM, SPP and Manitoba against **one** `p_ext`, and its four border links
can set that dual from **any** of the four Midwest border zones — including a zone on the other
side of the footprint from the seam being tested. Measured from duals alone:

* `share_west_sets` — `p_ext` ties `MISO-West` and `p_ext < min(Illinois, Indiana, East) − τ`
  (the PJM seam's merit test priced at the SPP/Manitoba-facing zone);
* `share_east_sets` — `p_ext` ties one of `{Illinois, Indiana, East}` and `p_ext < p_West − τ`
  (the SPP/Manitoba seams priced at a PJM-facing zone);
* reported beside them: `share_all_four_tied`, the mean `|p_ext − p_z|` gap in each set, and the
  implied `Δs` in $/MWh.

**Verdict, all three years:**

* **STAR-COUPLING LIVE** iff `share_west_sets + share_east_sets ≥ 0.10` in all three years.
* **STAR-COUPLING INERT** iff `< 0.02` in all three years.
* **MIXED** otherwise.

**The reading is fixed HERE.** **INERT ⇒ the candidate is CLOSED at zero LP and no solve is ever
spent on it.** **LIVE ⇒ a DOF-free candidate EXISTS and is handed forward as a NAMED charter,
not armed and not screened in this session**: the per-seam external-node split — the exact
transform `miso.split_miso_south_external_node` already performs for South, over the tie
geography already committed in `IMPORT_NODE_LINKS["MISO"]`'s own comment ("the 7,300 MW eastern
(PJM/IESO) seam envelope splits across its three physical border zones — Illinois, Indiana,
East; West carries the SPP/Manitoba 4,000 MW seam"). **The footprint is a footprint, never a
target** (rules 1 / 13): no successor may size anything to it.

**Rule 28(a), stated in advance:** this is **NOT** `internal_congestion_split`, which stands
**G** at MISO on miso-79's NO-BUILD (88–99.7 % of internal congestion mass is intra-LBA) and is
neither re-tested nor re-opened here. That cell is about representing congestion the six-zone
topology does not carry; §3d is about whether the appended external node **bypasses the CIL/CEL
groups the six-zone topology already carries**. They are different objects and this session says
so before its numbers.

## 4. The charter deliverables (c) and (d) — what will be WRITTEN, and the standard it must meet

The FINDING will carry all four legs of the charter the handoff specifies, and **whichever way
§3a–§3d read**:

* **(a)** answered by §3a + §0c(1)–(4), code reading and measurement together.
* **(b)** answered by §3c — NAMED, with its basis, or NAMED ABSENT with the failing leg.
* **(c) rule 17 `[R-FLOOR-WINDOW]` in full** — external driver, the hours the candidate may
  bind and why, and how it regenerates in a forecast year — written for whatever candidate
  §3d leaves standing, or recorded as **not owed because no candidate stands**.
* **(d) rule 19 `[R-ONE-MECH]`** — the enumeration of everything already setting the PJM seam
  is written out in the FINDING whatever the verdicts: the armed hourly PJM neighbour anchor
  (`miso_seam_neighbour_hourly_ladder`, band `k` at `p_border(t) + δ_k`), the frozen Q-Q `δ_k`
  ladder, the measured `(month × hod)` deliverability envelope
  (`miso_seam_flow_limit` / `miso_seam_export_limit` / `miso_seam_envelope_merit_cap` /
  `miso_seam_envelope_hour_ending_key`), the export ladder on the `p_bus` LEVEL, the per-link
  border TTCs, the 8,700 MW `MISO_simultaneous_import` SIL, and the CIL/CEL deliverability
  groups — with the candidate declared to **REPLACE** or **RECONCILE**, never to stack.
* **The bar is a DOF-FREE construction.** miso-233 promoted on zero fitted parameters. **If no
  DOF-free form exists, this session says so and stops**, and that is its complete result.

## 5. What this session cannot do, stated before the numbers

1. **No lever is armed, screened or solved.** Zero LP. A charter names an object and states
   whether a DOF-free form exists; it does not arm one, and §3d's LIVE branch explicitly
   hands forward rather than screens.
2. **NOTHING HERE LICENSES TOUCHING THE LADDER OR THE ENVELOPE — WHATEVER THE ANSWER.** The PJM
   and SPP `δ_k` ladders stay derived, frozen and pinned to their derives by test (rule 23
   `[R-FROZEN-DERIVE]`); the `(month × hod)` deliverability envelope stays a measured input
   (rule 14 `[R-ACCURATE]`). **No re-derive, no damping factor, no smoothing, no change of `K`,
   no re-spacing of `δ_k`, no envelope change, no interface-limit change.** miso-238 PREREG §5.2
   and miso-239 PREREG §5.2 both fixed this in advance for exactly the outcomes they got; it
   binds here identically and it binds whatever §3 returns.
3. **Nothing here is a tuning target.** No successor may size, scale, tune or select any
   mechanism to make a modelled `γ`, share, correlation, price gap or footprint land on a number
   produced by this session (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`). miso-236's
   328.6 / 341.7 / 207.5 MW sizing stays **un-targetable** and is not re-quoted as a target.
4. **No adjudicated cell is re-tested** (rule 28(a) DO-NOT-REDO). Standing and untouched:
   the saturation hypothesis **REFUTED** (miso-238); the SPP neighbour-state channel
   **QUANTITY-SIDE**, its object NAMED and **NOT CHARTERED** (miso-237); South's neighbour-state
   route **CLOSED** (miso-236 D-4); `miso_manitoba_seam` **CLOSED as already-armed** (miso-235);
   the `(month × hod)` template hypothesis **REMOVED** (miso-236 §3); the PJM import/export
   asymmetry **CLOSED FOR PJM** (miso-238 §4 — §1's G-X0 *uses* that closure, it does not
   re-litigate it); `internal_congestion_split` **G**;
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `miso_south_firm_export_block` **G**;
   `miso_south_export_ladder_rt_tail` **R**; `miso_south_gas_delivered_cost_basis` **R**.
   miso-239's own MIXED stands as MIXED and this session does not re-run its ladder.
5. **No cell verdict moves in either direction.** This session tests no mechanism, so rule 28(b)
   attaches only in its **evidence-appending** form (the miso-206 / miso-234 / miso-235 /
   miso-236 / miso-237 / miso-238 / miso-239 / neiso-100 / caiso-206 no-solve precedent), in
   **MISO's shard only** (rule 25).
6. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not
   trade a passing gate for anything (miso-227 promotion rule).
7. **C3c is untouched** and stays the designated frontier (2026-07-20). No LP is authorized
   there under this handoff and none is sought.
8. **The model side is a RECONSTRUCTION where §1 uses one** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839) and is labelled as one. **But §3a and
   §3d are NOT reconstructions** — they read the keeper's own committed P1 zonal duals directly
   from `hourly/system_<year>.parquet`, which is the strongest evidence class this lane has.
   That distinction is stated here so neither is mistaken for the other. 2024 remains the
   loosest reconstruction year and every 2024 reconstruction reading is reported with that said.
9. **This session claims no predecessor verdict as its own.** §1 republishes miso-238's and
   miso-239's columns as provenance legs only.

## 6. Deliverables

* `scripts/probes/_miso240_external_bus_price_charter_phase0.py` →
  `results/calibration/_miso240_external_bus_price_charter_phase0.json`.
* `results/calibration/FINDING-miso240-*.md` carrying **every number this session will ever
  cite**, and the four-leg charter (a)–(d) with its DOF-free verdict.
* Evidence appended to MISO's matrix shard + the `§5.4` queue stamp (rule 25, rule 28(b)
  evidence form).
* `docs/calibration-log/miso.md` entry.

## 7. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed on a residual,
sized, swept or selected, and every number this session produces is declared un-targetable in
§5.3 before it is computed. Rule 12 `[R-PARALLEL]`: no LP is solved; nothing runs on CI.
Rule 13 `[R-MEASURED]`: measurement only — no input changes and no measured outcome enters any
solve; §3c names a measured series as a candidate DIAGNOSTIC BASIS and explicitly not as an
input to any clearing price (substituting a measured MISO price for the LP's own dual would be
pinning an output, which stays forbidden). Rule 14 `[R-ACCURATE]`: no input changed; §5.2
forbids touching the measured envelope. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing
registered or pruned; MISO keeps exactly one registered run and the keeper's `hourly/` sidecars
stay committed. Rule 17 `[R-FLOOR-WINDOW]`: no floor added; §4 writes the argument a candidate
would owe. Rule 19 `[R-ONE-MECH]`: no mechanism added; §4(d) writes the enumeration whatever the
verdict. Rule 21 `[R-DOF]`: **41/2, unchanged**; every instrument here carries **zero** free
parameters, `τ` included (§2 declares its sensitivity in advance). Rule 22 `[R-HOLDOUT]`:
2023–2025 only; MISO holds no `complete` marker. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run,
and §5.2 forbids one whatever the verdict. Rule 24 `[R-REGISTRY]`: no field created. Rule 25
`[R-ISO-SCOPE]`: MISO's shard, section and lane only. Rule 26 `[R-DELETE]`: nothing zeroed in
place. Rule 27 `[R-PUSH]`: every pushed blob verified against local; no regenerated full-file
push of an existing ≥300-line source file. Rule 28: queue item 1 named in §0/§3; evidence-append
form only. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0, and this session IS that
phase 0; no screen is chartered here and §3d's LIVE branch hands a candidate forward for a
successor's own pre-registered screen rather than spending one.

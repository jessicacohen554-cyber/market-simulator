# PREREG miso-235 — the fourth seam the attribution instrument omitted, and whether MISO's interchange under-variation is an over-strong price response or a missing non-price one

**Pushed BEFORE any adjudicating quantity is computed.** miso-234 did not push a pre-registration
and correctly forfeited its right to close or re-open any cell on its own numbers; this session
does not repeat that. Every decision rule below is fixed here, before the probe is written.

**Keeper `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF 41/2. **MISO HAS NO FAILING
GATE.** Nothing here targets a rubric failure, because there is no object for one. Rule 22:
2023–2025 only; MISO holds no `complete` marker and no out-of-training year will be solved,
scored or registered.

**ZERO LP IS PLANNED.** No `ScenarioConfig` field is created or armed, no bundle is produced, no
run is registered or pruned, and the keeper is not touched. If a measurement below turned out to
license a screen, the screen would be chartered in a successor with its own PREREG — it is not
chartered here.

---

## 0. Lever-queue selection (rule 28(a))

This session takes the handoff's **item 1** — the PJM seam's 4–9× correlation over-response —
and its **item 2** (Manitoba's price response), because **they are one measurement**: item 2's
object is a seam that item 1's instrument does not contain. Item 3 (CC_REGULAR 2024→2025 shape)
is left where miso-234 filed it.

The handoff's own instruction on item 1 is the charter: *"That is missing NON-PRICE variation
(outages, schedules, neighbour state), not an over-strong price response. Establish which, from
the measured record, before proposing anything."* §3 below is that establishment, and it is the
whole of the session's adjudicating work.

### 0a. What was established BEFORE this PREREG was written, and is therefore disclosed, not claimed

Three facts, all read from code and committed config — **no adjudicating quantity among them**:

1. `results/calibration/miso233_sppseam_K/run_config.json` carries **`miso_manitoba_seam: true`**
   alongside `reference_price_interface: true` and `miso_seam_measured_ladder: true`.
2. `spec.get_interchange_spec` (src/market_sim/model/interchange/spec.py) therefore **drops the
   MHEB firm block** (`miso_firm_imports` is gated on `not miso_manitoba_seam`) and
   `build_interchange_fleet` appends **`MISO_MANITOBA_SEAM_SPEC`** as a fourth priced neighbour
   with two-way bands.
3. `scripts/probes/_miso234_corr_overshoot_phase0.py` iterates
   `INTERFACE_NEIGHBORS["MISO"]`, which contains **only PJM, SPP and South** — the Manitoba seam
   is added dynamically at `get_interchange_spec` and is not in that static registry.

So the handoff's item 2 — *"the model's firm block (`miso_firm_imports`) contributes ZERO by
construction"* — rests on a premise this session has reason to doubt. **Doubting it is not
refuting it**: the seam could be armed and still inert. §2 fixes the rule that decides which.

### 0b. Basis discipline (carried from miso-234 §0a — it bit a first draft there)

Every price statement this session makes names its basis. The two instruments are **not** the
same series and correlate only +0.402 / +0.424 / +0.553:

* **Indiana-hub RT** — `_miso224_floor_anatomy_phase0.actual_zone_price(year)["MISO-Indiana"]`,
  `values="rt"`. This is the lane's scored basis and the price `P` in every correlation below.
* **Indiana-hub DA** — the basis `MISO_SEAM_LADDER_BY_YEAR` was Q-Q derived against, and the
  basis of every **spread regressor** in §3.

miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated as reproduced by
anything here.

---

## 1. Q1 — INSTRUMENT. Does the repaired four-seam reconstruction supersede miso-234's three-seam one?

The probe rebuilds every model seam band from the keeper's **committed** sidecars and the frozen
ladders/envelopes, exactly as `_miso234_corr_overshoot_phase0.py` does, and **adds the Manitoba
seam** (`MISO_MANITOBA_SEAM_SPEC`, `interface_limit_mw` 2900, 8 bands, priced by the frozen
`MISO_SEAM_LADDER_BY_YEAR[year]["Manitoba"]` against the `MISO_external` bus, capped by the
measured two-way MHEB `(month × hod)` envelope). Nothing is re-derived (rule 23).

**DECISION RULE, fixed ex ante.** The repaired reconstruction supersedes the three-seam one as
this lane's attribution instrument **iff BOTH hold in ALL THREE years**:

* **(I-1)** `corr(recon, committed import series)` is **higher** than the three-seam value, and
* **(I-2)** `|mean(recon) − mean(committed)|` is **not higher** than the three-seam value.

If either fails in any year, **both instruments are reported side by side and NEITHER
supersedes**; no re-attribution is claimed and §4's re-based ratio is withdrawn.

Both reconstructions are recomputed in this session on one code path, so the comparison is not
against a quoted number.

## 2. Q2 — Is handoff item 2's premise ("Manitoba contributes zero by construction") true?

**DECISION RULE, fixed ex ante**, on the reconstructed model Manitoba flow `x_MB`:

* **REFUTED** iff the resolved keeper spec carries the Manitoba seam **and** `σ(x_MB) > 100 MW`
  in every year. The item is then closed as **already armed**, and the real question it should
  have asked — whether the armed seam's price response is the *right* one — is the object §3
  measures.
* **CONFIRMED** iff `σ(x_MB) ≤ 100 MW` in every year (armed but inert). The item survives as
  written and is handed forward unchanged.
* **MIXED** otherwise, and reported as mixed with no closure either way.

**In every branch NO CELL VERDICT MOVES.** Nothing is tested here — `miso_manitoba_seam` was
armed by an earlier keeper, not by this session — so rule 28(b) attaches only in its
evidence-appending form, following the miso-206 / miso-234 / neiso-100 / caiso-206 no-solve
precedent. Evidence is appended to the `seam_flow_envelopes` cell (which carries
`miso_manitoba_seam` in its armed-family list) and to `seam_neighbour_hourly_ladder`.

## 3. Q3 — THE SESSION'S ADJUDICATING QUESTION. Over-strong price response, or missing non-price variation?

For each seam `s` and year, on the **measured** flow and again on the **reconstructed model**
flow, one OLS on the price signal that seam's bands actually clear against:

    x_s(t) = alpha_s + beta_s * z_s(t) + r_s(t)

with the exact variance identity `Var(x_s) = beta_s^2 * Var(z_s) + Var(r_s)`. Regressors, named
by basis, chosen to match the model's own clearing construction and **fixed here**:

| seam | model band clears on | regressor `z_s` (all DA basis) |
|---|---|---|
| PJM | hourly neighbour anchor | MISO Indiana hub DA **−** PJM border price |
| SPP | hourly neighbour anchor (miso-233) | MISO Indiana hub DA **−** SPP NORTH hub DA |
| South | FIXED MISO-hub Q-Q ladder | MISO Indiana hub DA (level) |
| Manitoba | FIXED MISO-hub Q-Q ladder | MISO Indiana hub DA (level) |

Sign convention **import-positive** throughout.

**CLASSIFICATION RULE, fixed ex ante**, per seam-year:

* **PRICE-RESPONSE OVERSHOOT** iff `|beta_model| / |beta_measured| >= 1.5`.
* **MISSING NON-PRICE VARIATION** iff `sigma(r_model) / sigma(r_measured) <= 0.5`.
* Both may hold. The seam's **headline** classification is whichever leg carries the larger
  absolute share of that seam's sigma gap, split by the identity:
  * price leg = `|beta_model| * sigma(z) - |beta_measured| * sigma(z)`
  * residual leg = `sigma(r_model) - sigma(r_measured)`
* Neither trigger firing ⇒ **NEITHER**, reported as such.

The **system-level** answer to item 1 is the sum of the per-seam legs across all four seams,
reported as a percentage split of the total sigma gap
(`sigma_total_model - sigma_total_measured`). **That split is this session's deliverable.**

**Why this is admissible and is not a fitted anything.** It is a measurement on the measured
record and on the keeper's own committed output. It identifies no parameter, changes no input,
and selects nothing. Rule 13 `[R-MEASURED]`: no measured outcome is fed into any solve — no solve
runs.

## 4. Q4 — The re-based PJM ratio (REPORTED, NOT GATED)

miso-234 published PJM model:measured contribution ratios of **4.2× / 5.1× / 8.9×** on the
three-seam instrument. Two facts make that number the wrong size and both are reported beside it:

* the identity's denominator `sigma_total` is the **reconstruction's**, so a missing seam
  inflates every contribution; and
* the reconstruction's own `corr(recon, P)` was **−0.2069 / −0.1664 / −0.1793** against the
  **committed** solve's **−0.1095 / −0.1145 / −0.1128** — i.e. the instrument nearly doubles the
  correlation it is attributing.

The repaired ratio is reported for the successor's benefit only. **No decision attaches to it**,
and it is conditional on Q1 clearing (I-1)+(I-2).

## 5. What this session cannot do, stated before the numbers

1. **No damping factor, no re-derive.** The PJM `delta_k` ladder is derived, frozen and pinned to
   its derive by test (rule 23 `[R-FROZEN-DERIVE]`); a factor swept against this residual is the
   rule 1 `[R-STRUCT]` fitted mechanism. Nothing measured below can license one, whatever it says.
2. **No re-test of an adjudicated cell** (rule 28(a) DO-NOT-REDO):
   `miso_south_firm_export_block` **G**, `miso_south_export_ladder_rt_tail` **R**,
   `internal_congestion_split` **G**, `vre_reference_rate_curtailment_grossup` **K**,
   `measured_interface_limits` **R**, `miso_rdt_measured_limit` **R**,
   `miso_south_gas_delivered_cost_basis` **R**. Where a number here touches one it corroborates
   it; the standing adjudication remains the finding.
3. **No promotion, no decertification.** MISO is CALIBRATED today and this session does not trade
   a passing gate for anything (miso-227 promotion rule).
4. **C3c is untouched** and stays the designated frontier (2026-07-20). Its charter is a new
   admissible measured identification, never an offer adder tuned to the tail, and no LP is
   authorized there under this handoff.

## 6. Deliverables

* `scripts/probes/_miso235_seam_variance_decomposition_phase0.py` +
  `results/calibration/_miso235_seam_variance_decomposition_phase0.json`.
* `results/calibration/FINDING-miso235-*.md` carrying every number this session will ever cite.
* Evidence appended to the MISO shard (rule 25: MISO's shard only; rule 28(b) evidence form).
* `docs/calibration-log/miso.md` entry.

## 7. Governance declared in advance

Rule 1 `[R-STRUCT]`: no mechanism is judged by a residual; nothing is proposed. Rule 12: no LP,
nothing on CI. Rule 13 `[R-MEASURED]`: measurement only, no input changed. Rule 15
`[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO keeps exactly one
registered run. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged.
Rule 22 `[R-HOLDOUT]`: 2023–2025 only. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run. Rule 24
`[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO only. Rule 27 `[R-PUSH]`: every
pushed blob verified against local. Rule 28: queue item named above; evidence-append form only.
Rule 29 `[R-SCREEN]`: clause 0 — zero-LP phase 0 first, and this session is that phase 0.

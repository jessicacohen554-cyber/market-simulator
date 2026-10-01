# PRE-REGISTRATION — nyiso-114: the per-family reserve-dual sidecar, and the nyiso-113 keeper confirmation run

**Date:** 2026-08-03 · **ISO:** NYISO · **Years:** 2023, 2024, 2025 (one bundle,
rule 16) · **Keeper under confirmation:** `2026-08-02-nyiso-113-li-locational`
(bundle `results/calibration/nyiso113_lilocational_B`) · **Committed and pushed
BEFORE the confirmation replay was launched.**

---

## §1 — what is being built, and why it is not a lever

nyiso-113 §8 recorded a standing gap in **all six ISOs**: no committed bundle
anywhere persists a **per-family reserve dual**.
`DispatchResult.reserve_price_by_family` is `(T, n_fam)` in memory (it is what
`results/scarcity.py` consumes) and is discarded at persist time, while
`system_<year>.parquet`'s `reserve_price` is the per-hour **sum across
families**, a single `(T,)` system-level series written **identically into every
zone's rows** (`run_calibration_full.py` `_system_frame`). It has no zone index
and no family index. A locational reserve family's binding is therefore
invisible in every committed artifact, and a gate specified on that column reads
inert **by construction** — which is exactly how nyiso-113's own pre-registered
K3/K4 gates came to be invalid.

This session persists it: `hourly/reserve_family_<year>.parquet`, long form, one
row per (family, hour):

| column | source | meaning |
|---|---|---|
| `year`, `pass`, `hour` | harness | the usual sidecar keys |
| `family` | `ReserveDesign.families[f].name` | e.g. `li_30min_total` |
| `reserve_class` | `ReserveFamily.reserve_class` | eligibility class index |
| `dual` | `DispatchResult.reserve_price_by_family[:, f]` | the family's own balance-row shadow price |
| `requirement_mw` | `ReserveFamily.requirement` | that family's hourly MW requirement |
| `shortfall_mw` | **new** `DispatchResult.reserve_shortfall_by_family[:, f]` | its cleared ORDC shortfall MW |

`shortfall_mw` is new LP output: the ORDC block is **family-major** (family `f`
owns the next `counts[f]` columns of `[_ordc_off, _ordc_off + n_ordc_steps)`, per
`_build_reserve_rows`), so a family's shortfall is the sum of its own steps. It
is needed because the dual alone is ambiguous — a positive dual at **zero**
shortfall is the requirement binding against real headroom, while a positive
shortfall names the ORDC step that *set* the price.

**This is an instrument, not a mechanism.** It adds **no `ScenarioConfig`
field**, no CLI flag, no LP row, no column, no cost. `reserve_shortfall_by_family`
is read off the already-solved primal; nothing else in the solve reads it.
Rule 24 `[R-REGISTRY]` is not engaged (there is no tunable). It gets a matrix row
under rule 28(c) as a **cross-ISO instrumentation row**, the same shape as the
existing `diagnostics_plant_set` audit row — not a verdict cell on a lever.

**No backfill.** Bundles solved before this change do not get the sidecar; it is
written going forward. Backfilling would require re-solving every keeper, and a
NYISO replay is not guaranteed to reproduce a keeper vertex-for-vertex (below).

## §2 — the confirmation run, and its ONE honest risk

**Arm:** `results/calibration/nyiso114_lilocational_confirm` — a **zero-delta**
replay of `nyiso113_lilocational_B` across 2023–2025, no `--set`, run purely to
emit the new sidecar. No config field changes. No keeper is promoted, demoted or
re-keyed by this session.

**The risk, stated ex-ante.** The NYISO keeper arms
`nyiso_gas_commitment_bridge`, a **P0-run-pattern** bridge. caiso-155 measured
that this family of mechanisms is **vertex-dependent**: an in-place caiso153
replay reproduced system duals and prices byte-identically while `class_hourly`
and `storage` shuffled by up to 1,997 MW at identical shapes, and the NYISO
replay was declined there on the same dependence. So a replay's *floors* are
not necessarily the keeper's floors. What this session needs from the replay is
narrower — the reserve-family duals — but the fidelity must be **measured, not
assumed**, and gate G1 does exactly that. A replay that fails G1 does not get
quietly reported as the keeper's numbers.

## §3 — construction gates (all measured on committed artifacts)

| id | gate | pass condition |
|---|---|---|
| **G1** | **replay fidelity** | the replay's `system_<year>.parquet` reproduces the committed keeper's `price` and `reserve_price` columns to `max abs diff ≤ 1e-6 $/MWh` in all three years. **If G1 fails**, the divergence is reported with its measure and every §4 result is labelled as measured on a *re-solve*, not on the keeper — never silently. |
| **G2** | **instrument well-formed** | the sidecar exists for 2023/2024/2025; row count = `n_fam × 8760` per year; no NaN. |
| **G3** | **LP identity, per family-hour** | `Σ_{z ∈ family} R[z,t] + shortfall[f,t] == requirement[f,t]` to `1e-3 MW`, for **every** family and hour, reconstructed from the solve's own reserve dispatch. |
| **G4** | **sum identity** | `Σ_f dual[f,t] == system reserve_price[t]` to `1e-6`, i.e. the new sidecar decomposes exactly the series bundles already carried. |
| **G5** | **write-invariance** | the sidecar is write-only: `objective_value`, `price` and every scored metric are unchanged by its presence. Established by construction (no LP object is touched) and evidenced by G1. |
| **G6** | **span** | 2023–2025 in ONE bundle (rule 16); no year outside 2023–2025 is solved or scored (rule 22 — the holdout spend freeze is ACTIVE). |

## §4 — the pre-registered PREDICTIONS about the nyiso-113 keeper

These are falsifiable statements made **before** the sidecar existed, taken from
nyiso-113 §7's Zone-K headroom probe. They confirm or refute a **promoted**
keeper's mechanism; they do not re-litigate its promotion, and **no outcome here
changes the keeper**.

| id | prediction | source |
|---|---|---|
| **P1** | `li_30min_total` has `dual > 0` in **at least** the 5 hours 2025 h4193–4195 and h4217–4218 (the June 24–25 event). | nyiso-113 §7 headroom probe |
| **P2** | nyiso-113 measured the **system** dual moving in *those five hours plus five more* in 2025. The sidecar must **attribute** all ten to named families. No gate on *which* — that is the information the instrument buys. A hole (a system-dual move in an hour where **no** family's dual is positive) would falsify the instrument itself. | nyiso-113 §7 |
| **P3** | `li_10min_total` has `dual == 0` in **every hour of every year** — Zone-K quick-start headroom bottoms out at 596.8/490.7/379.7 MW, i.e. 3.2–5.0× the 120 MW requirement. | nyiso-113 §7 |
| **P4** | **2024:** no LI family binds in any hour. | nyiso-113 §7 |
| **P5** | **2023:** the LI families bind in exactly 2 hours. | nyiso-113 §7 |

**Interpretation rule, fixed now.** A refuted prediction is a finding about the
**nyiso-113 headroom screen**, reported as such — not a defect in the keeper and
not a reason to change any parameter. In particular, if P1/P5 miss, the correct
conclusion is that the headroom screen (an *ex-ante* proxy) mispredicted the
solved dual, which is precisely the thing a per-family dual exists to settle.

## §5 — kill conditions

* **K-A** — the sidecar's presence changes any solved number (G1 fails **and**
  the divergence is attributable to this change rather than to the known
  P0-pattern vertex dependence): the instrument is reverted, not tuned.
* **K-B** — G3 or G4 fails: the extraction is wrong (a mis-partitioned ORDC
  block would silently attribute one family's shortfall to another). Revert; do
  not ship a sidecar that mislabels families.
* **K-C** — the design's family count disagrees with the solved dual's column
  count: the writer already refuses to emit a frame in this case (no frame is
  strictly better than a mislabelled one) and the run reports it.

## §6 — NO-TUNING CLAUSE (binding)

Nothing in this session may change a solve-affecting value.

* **No `ScenarioConfig` field is added, removed or re-defaulted** by the sidecar
  work. The confirmation arm carries **zero** config deltas from the keeper.
* The LI reserve levels (120 MW / 270 / 540 MW), the published $25/MW
  demand-curve value, and the MST §2.15 On-Peak calendar are **frozen** —
  nyiso-113's own no-tuning clause carries over unchanged and this session
  neither re-derives nor re-fits any of them.
* The `nyiso_gas_commitment_bridge` measured min-load / min-run parameters, the
  ramp envelope, and the 227-3 compliance file are **frozen** (rule 23
  `[R-FROZEN-DERIVE]`): no re-derivation, for any reason, in this session.
* If a prediction in §4 misses, the response is a **written finding**, never a
  parameter change. A residual that moves because a number was chosen to move it
  is what rules 1 and 23 forbid.

## §7 — governance

* **Rule 16** — 2023, 2024, 2025 in one bundle for the arm.
* **Rule 22** — the holdout spend freeze is ACTIVE. No year outside 2023–2025 is
  solved, scored, or read. No marker is spent, requested, or implied.
* **Rule 15** — the arm is registered on the backcast dashboard in this session,
  whatever it shows.
* **Rule 28(b)/(c)** — the instrumentation row lands in
  `mechanism-matrix.js` in this same session, and no existing cell verdict is
  touched by it.
* **Rule 21** — no DOF is added: the sidecar has no free parameter.

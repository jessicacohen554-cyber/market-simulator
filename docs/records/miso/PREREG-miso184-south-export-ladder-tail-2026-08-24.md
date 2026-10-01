# PREREG miso-184 — the SOUTH EXPORT-LADDER SCARCE-TAIL session: is the Q-Q derivation's DA price basis a methodology defect, and if so, is a corrected-basis re-derivation the licensed repair?

**Session miso-184 (2026-08-24).** Registered **BEFORE any adjudicating
quantity is computed.** Executes the queue head installed by miso-183
(`FINDING-miso183-south-seam-basis-2026-08-24.md` §5/§8 item (5), matrix §5.4
stamp miso-183). **OWNER ENGAGEMENT RECORDED:** the handoff prompt launching
this session is the owner engaging miso-183 §8 item (5) — the rule-23
adjudication of the ladder derivation's DA-vs-RT basis is hereby chartered by
the owner, and the same charter pre-authorizes the conditional repair + A/B
(control = the keeper recipe; arm = corrected South export bands only) with
the pre-registered structural prediction below. The owner posture directive
(2026-08-24, the authorizing message): *"If structural integrity improves but
gates regress that may still be a keeper"* — applied verbatim in §6.

Keeper `2026-08-22-miso-177-rho-measured` (`miso177_rho_B`); determination
NOT-YET on C3a-2025 alone, C3c the single ledgered caveat. **Mechanism-in-kind
(named now so rule 26(b) is decidable): `miso_south_export_ladder_rt_tail`.**
A cell is minted in MISO's shard on ANY tested outcome — including "the
methodology is adjudicated sound, re-derivation refused" and "defect
established, basis repair refuted" — because unlike miso-182/183 this session
DOES test a mechanism-in-kind the moment §4's probe computes the candidates'
as-armable tail behaviour.

## 0. What has been looked at, and what has not (the pre-registration boundary)

Before writing this document the session read only:

* committed prior findings, preregs, probe sources and their committed values
  (miso-174/177/178/182/183; `_miso183_south_basis_decomposition.json`'s
  producing probe source; the miso-177 PREREG/RESULT pair for the A/B recipe);
* code: `scripts/data/derive_miso_seam_ladders.py` (the object under
  adjudication), `model/interchange/spec.py` (the registered
  `MISO_SEAM_LADDER_BY_YEAR` values and the South seam spec:
  `interface_limit_mw=3000`, `border_zones=("MISO-South",)`, `ba_code="SOCO"`),
  `model/interchange/import_nodes.py` (band construction: import bands
  `[0, step]`, export bands `[-step, 0]`, `step = limit/8`; the
  `_inject_seam_ladder` row-match; the no-wash clamp in `_derive_one`:
  every export band ≤ `min(import) − 0.01`), `scripts/replay_keeper.py`;
* schemas ONLY of: the keeper hourly sidecars (column names, zone list —
  which shows `MISO_external_South` — and klass list),
  `data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`
  (columns `year/hour/hub/zone/rt/da`; MISO-South = ARKANSAS/LOUISIANA/MS/
  TEXAS hubs; years 2022–2026 present; 350,400 rows; **three sample
  MISO-South 2025 rows seen for column semantics** — h0–h2 ARKANSAS.HUB,
  disclosed), `results/outputs.py::to_parquet` (the full per-year parquet
  carries `flows` and `demand` columns);
* environment facts: 15 GB RAM / no swap yet / 4 cores / 20 GB free disk;
  the miso-169 memory recipe (8 GB swapfile, `MARKET_SIM_HIGHS_THREADS=4`,
  3-year invocation peak ~13.0 GB).

**No statistic over any measured hourly series has been computed for this
session** — no flow duration, no quantile, no coincidence count, no simulated
clearing. The registered ladder VALUES (spec.py constants) and the committed
miso-174/182/183 statistics quoted below are prior sessions' committed
numbers, restated not re-derived.

## 1. The object (committed; restated)

The armed 2025 South export ladder is
`(53.00, 44.14, 37.04, 32.38, 29.43, 26.61, 24.29, 22.35)` — a
willingness-to-pay sink curve that shuts off entirely once MISO's internal
price clears $53.00, against a scarce set (summer ∩ hub RT > $200; n =
11/14/47 in 2023/24/25) averaging $479 in 2025. Committed record: the model
withdraws its South export in its own scarce hours (2025 annual 0.750 →
scarce 0.177 GW) while the measured seam holds or expands (1.031 → 1.368 GW)
— miso-182, on the pool basis. miso-183 established basis-free that the real
South pushed **−2.441 GW** out across its boundary complex in the 2025 scarce
set (floor ≥ 0.93 GW conservative) and that the real RDT bound S→N in 32/47
of those hours (N→S in 0), while the keeper binds N→S in 9/47 and S→N never.
The pool-basis +1.19 GW is retired as the quotable size and is NOT quoted as
one here; the committed `O_y` values appear below only where a prior
committed statistic is restated.

**The suspected defect (miso-183 §5, verbatim in kind):**
`derive_miso_seam_ladders.py` Q-Q couples the measured flow-duration curve to
**DA hub LMP** quantiles (`sigma_k = Quantile_DA(P[flow < -L_k])`), while the
scored scarce set is an **RT** phenomenon that DA foresaw only in part — so a
deep-export band priced at a DA quantile may be structurally unable to follow
the seam into RT scarcity.

**Declared a priori (analysis, no data needed) — the representability frame.**
Under ANY single price basis `B`, the Q-Q machinery's simulated export at hour
`t` is `X(t) = Σ_k step · 1[B_t < σ_k]` with `σ_k = Quantile_B(d_k)`,
`d_k = P[flow < −L_k]` — a monotone non-increasing function of the RANK of
`B_t`. Export survives an hour whose `B`-rank is `u` only in bands with
`d_k > u`. Therefore a basis repairs the scarce tail **iff the scarce hours
are NOT the extreme upper ranks of that basis** (the hub bases in scarce hours
are near rank 1.0 by construction of the scarce set, so they can carry tail
export only if the measured export durations `d_k` are themselves extreme,
≥ ~0.995), **or** the basis decouples from the hub in scarce hours (the
South-zone bases: the measured record shows real S→N binding, i.e. real South
price separation BELOW the hub, in most 2025 scarce hours). This frame is
fixed BEFORE measurement so that a "defect established but not repairable by
any admissible basis" outcome (V-DEFECT-COUPLING, §4) is a pre-declared
branch, not a post-hoc rationalization.

## 2. The instrument (frozen construction)

One read-only probe, `scripts/probes/_miso184_ladder_tail_methodology.py` →
`results/calibration/_miso184_ladder_tail_methodology.json`, committed with
this PREREG **before it is run**. Frozen constructions, carried verbatim:

* **Row set:** the derive script's own — `load_joined()` (EIA-930 DIBA pooled
  onto seams by `MISO_SEAM_DIBA`, hour-ending−1 → fixed non-leap 8760;
  `interpolate(limit=3)`), per year the `g3` rows non-NaN on
  `da` + PJM + SPP + South, additionally requiring finite `rt` (and finite
  South-zone price for the B2/B3 legs); every leg reports its row coverage,
  overall and within the scarce set.
* **Hour sets:** the miso-174/178/183 masks verbatim — `annual`; `summer`
  (Jun 1–Sep 30); `scarce` = summer ∩ hub RT > $200 from
  `actual_lmp_hourly_MISO.parquet` (n = 11/14/47 reproduced as a footing
  gate).
* **Bands:** the South seam's 8 export bands at midpoint depths
  `L_k = (k − 0.5) × 3000/8` MW (187.5 … 2812.5), `step = 375` MW.
* **Sign:** seam `flow` is import-positive (the derive's own convention);
  net EXPORT `E = −flow`; simulated export-side clearing
  `X = Σ_k step · 1[price < σ_k]` (GW, export-positive).
* **Candidate bases** (all zero-free-parameter, all already-intaken measured
  series; the frozen Q-Q machinery byte-for-byte — same depth grid, same
  quantile call, cents rounding, and the same-seam no-wash clamp against the
  UNCHANGED registered DA import ladder of the same year, since the license
  moves ONLY the South export bands):
  * **B1 — RT hub** (`rt`, `actual_lmp_hourly_MISO.parquet`): the charter's
    named candidate.
  * **B2 — South-zone DA** (hub-mean of the four MISO-South hubs,
    `actual_lmp_hourly_zonal_MISO.parquet` `da`).
  * **B3 — South-zone RT** (same file, `rt`). Physically motivated by the
    derive's OWN docstring reconciliation ("the coupling anchor is the MISO
    hub-mean DA LMP … not the border-zone LMPs the seam physically clears
    against") and by the LP fact that the South bands clear against the
    model's MISO-South price.
* **2025 is load-bearing** (the C3a year, the charter object); **2023
  concurrence reported; 2024 reported-only** (the disclosed EIA-930
  internal-inconsistency year — the miso-183 treatment).

### Stage F — footing (STOP gates, not verdicts)

F-1: scarce-set sizes reproduce 11/14/47. F-2: the frozen machinery re-derives
the registered `MISO_SEAM_LADDER_BY_YEAR` byte-equal (every seam, both sides,
all three years, to the cent; any |Δ| > $0.01 on any band → STOP, instrument
bug, report). F-3: the derive's own unconditional P9 export-volume
reproduction for the South seam is reported per year (the construction's
design guarantee — context for how tail-specific any failure is).

### Leg A — does the derivation reproduce its own target in the scored tail? (defect establishment)

`E_meas(y)` = scarce-mean measured South net export (GW);
`X_DA(y)` = scarce-mean export-side simulated clearing of the REGISTERED
ladder driven by measured DA (the derive's own offline-P9 convention,
restricted to the scarce mask); `GAP_DA(y) = E_meas − X_DA`. The full net sim
(import side included, both sides driven by DA) is reported alongside,
never gated.

* **Defect line (2025, both must hold):** `GAP_DA ≥ 0.5 GW` **AND**
  `X_DA ≤ 0.5 × E_meas`. (0.5 GW ≈ half the miso-183 conservative
  boundary-complex floor of 0.93 GW; the second clause makes "reproduces less
  than half its own target flow in the tail" the operative sentence.)
* 2023 concurrence reported against the same lines; 2024 reported-only.
  The defect is established or not **on 2025 alone**.

### Leg B — the coincidence orientation (diagnosis; reported, one declared line)

Per band k: unconditional `d_k` vs conditional `c_k = P[flow < −L_k | scarce]`.
Spearman rank correlation of `flow` vs each basis (annual, reported).
**Orientation line (reported as the mechanism diagnosis, no arm hangs on it):**
`c_1 ≥ d_1` in 2025 — the export presence does NOT thin in the scarce tail —
falsifies the willingness-to-pay ordering the Q-Q assumes for this seam's
export side.

### Leg C — basis attribution: which candidate, as-armable, carries the tail?

Per candidate B and year: `σ_k^B = round(Quantile_B(d_k), 2)` then the no-wash
clamp vs the registered DA import ladder (`min(import) − 0.01` = $50.98 /
$57.85 / $68.45 in 2023/24/25); `X_B(y)` = scarce-mean export-side clearing
driven by B. Reported per candidate: the derived (pre-clamp) and armable
(post-clamp) tuples, the clamp's bite (bands touched, and the unconditional
export-duration distortion it introduces), `X_B` with and without the clamp,
and the full-net variant (import side at the registered DA ladder, driven by
B) — the last reported-only, with the import side's own tail behaviour
carried to §5 as a NAMED, not-built object if it shows.

* **Repair line (2025):** `X_B ≥ 0.5 × E_meas` **as-armable (post-clamp)**.
* **Non-inversion (2023):** `X_B(2023) ≥ X_DA(2023) − 0.1 GW`. 2024
  reported-only.
* **Selection rule if several candidates clear both:** the largest
  as-armable `X_B(2025)`; exact tie → B1 (the charter's named candidate).
  Selection is thus on the derivation's own tail-reproduction metric — never
  on any LP residual.

## 3. Anti-sweep (binding)

The row set, hour sets, band grid, sign conventions, the candidate list
{B1, B2, B3}, the clamp treatment, every numeric line in §2 (0.5 GW / 0.5× /
0.1 GW / $0.01 / the selection + tie-break rule) and the §4 mapping are
**frozen by this document**. No alternative basis, threshold, set, or
statistic may be computed after seeing a result, and none may be quoted from
this session. Reported-only statistics never migrate into a gate. A result
against interest is reported at full magnitude. If any input turns out
missing/deficient (e.g. zonal file gaps), the affected candidate is dropped
with the deficiency disclosed — never patched ad hoc.

## 4. Verdict mapping (frozen)

| verdict | pre-registered condition (2025) | consequence |
|---|---|---|
| **V-SOUND** | Leg A defect line NOT met | The DA basis is adjudicated methodologically adequate in the scored tail; rule 23 stands, NO re-derivation, nothing armed. Matrix cell `miso_south_export_ladder_rt_tail` minted **R** ("adjudicated not-a-defect on the derivation's own construction"). |
| **V-DEFECT-BASIS** | Leg A met AND ≥1 candidate clears the Leg C repair + non-inversion lines | **The methodology defect is ESTABLISHED and basis-attributable.** The §6 repair is licensed: re-derive the South EXPORT bands only, winning basis, frozen machinery, zero new free parameters, derive commit citing THIS adjudication (never the residual); then the §6 A/B. Cell minted from the A/B outcome (K/R/I). |
| **V-DEFECT-COUPLING** | Leg A met AND NO candidate clears | The defect is established but **no admissible basis swap can carry the measured tail** — the monotone price coupling itself is the limiting construction for this seam's export side. NO arm (an armed swap would be exactly the "level adder wearing a repair's name" the charter kills). Cell minted **R** for the rebasis mechanism; the finding hands the owner the corrected object (a scarcity-coincident export mechanism class outside the ladder license, coupled to the standing Midwest-slope internal-direction object). |
| **MIXED** | any component pattern satisfying no row | Reported at full magnitude; no threshold moved; owner escalation. |

## 5. Conditional repair (only under V-DEFECT-BASIS; declared now, built then)

* New constant `MISO_SOUTH_EXPORT_LADDER_TAIL_BY_YEAR` (2023/2024/2025
  tuples, the winning basis, as-armable = post-clamp values) beside the base
  ladder; the base `MISO_SEAM_LADDER_BY_YEAR` stays **byte-identical** (rule
  23 — no unrelated ladder moves; the DA table remains the default).
* New `ScenarioConfig` field **`miso_south_export_ladder_rt_tail: bool =
  False`** (MISO-only, rule 25; backcast ladder years only). When armed,
  `inject_miso_seam_ladder_prices` overwrites ONLY the South seam's 8 export
  band rows with the corrected tuple after the base injection. Zero new
  numeric free parameters: every number is a quantile of a measured series at
  the structurally fixed depth grid (identification recorded in the DOF
  ledger against this adjudication).
* Matrix duty (c): the new field's row lands in
  `docs/codebase-site/data/mechanism-matrix.js` plus a cell line in EVERY ISO
  shard (MISO's carrying the verdict; the other five `·`), in the same push.

## 6. The conditional A/B (gates and kills fixed NOW)

Control and arm are `replay_keeper` replays of `miso177_rho_B` at HEAD, run
SEQUENTIALLY (rule 12 — one plant-level MISO LP at a time on this 15 GB
container, miso-169 memory recipe: 8 GB swapfile,
`MARKET_SIM_HIGHS_THREADS=4`), each the FULL span 2023 2024 2025 in ONE
invocation (rule 16):

```
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso184_tail_A \
  --note "miso-184 CONTROL: byte-faithful keeper replay at HEAD (miso_south_export_ladder_rt_tail default off)"
python3 scripts/replay_keeper.py results/calibration/miso177_rho_B \
  --out-dir results/calibration/miso184_tail_B \
  --set miso_south_export_ladder_rt_tail=true \
  --note "miso-184 ARM: South export bands re-derived on the corrected basis (single delta; adjudication PREREG-miso184)"
```

Registration ids `2026-08-24-miso-184-control` / `2026-08-24-miso-184-tail`
— **BOTH registered whatever the outcome** (rule 15, full span, rule 16),
whatever basis wins (the finding and run definition state the basis).

* **S-0 CONTROL INERTNESS (ABANDON).** Every scored sidecar of the control
  (`class_hourly`/`system`/`storage`/`reserve_family` × 3 years)
  value-identical to the committed keeper's. Anything else ⇒ HEAD drift —
  STOP, report, no arm conclusion (the miso-177 R-0 discipline).
* **S-1 EXACTNESS (KILL).** The arm's `run_config.json` records the field
  true (control false/absent); the armed South export band mc rows equal the
  frozen derived tuples; the base ladder rows byte-identical between legs.
* **S-2 DIRECTION (the charter's structural gate).** On the frozen scarce
  mask (from ACTUALS — identical for both legs), the arm's 2025 scarce-hour
  N→S binding count under the miso-183 spread classifier (verbatim: spread =
  P1 `price(MISO-South) − price(MISO-East)`; N→S ≡ spread > $1 and not the
  RPE ±$1 band) must **FALL below the control's** (committed keeper: 9/47).
  Reported alongside, never gated: the S→N count (measured record: 32/47
  any, 9/47 majority) and the full classifier composition, all years.
* **S-3 OUTFLOW (the charter's structural gate).** The arm's 2025 scarce-mean
  model South boundary-complex net inflow `N_S^m` — computed EXACTLY from
  each leg's full solve outputs (link `flows` into MISO-South, the seam-band
  net at `MISO_external_South` included), verified against the zonal energy
  balance (residual < 1 MW) — must move from the control's value **toward
  the measured −2.441 GW by ≥ 0.1 GW**. (miso-183's model interval mid for
  the keeper: +0.35 GW scarce.)
* **THE CHARTER KILL.** An arm that improves C3a-2025 while BOTH S-2 and S-3
  fail is a level adder wearing a repair's name → REJECTED regardless of
  every other number.
* **S-4 CONDUCT (KILL).** Zero D-4 conduct failures on the arm's regenerated
  `legitimacy_diagnostics.json`, zero NEW vs the control; C8 PASS all years.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill).** The
  complete verdict scorer on both legs; C3a all years, C1/C2/C3b/C3c, every
  regression reported at full magnitude. Movements outside the commercial
  band (±10 %) in 2023/2024, or any criterion PASS→FAIL flip, fire the
  **owner-escalation path**, never an auto-reject and never an auto-keeper:
  per the owner posture directive (§ preamble, verbatim) a
  structure-right/gates-regressed arm is escalated with both faces at full
  magnitude (the ercot-231 precedent), and a promotion additionally requires
  the standing leave-one-year-out scoring within 2023–2025 (rule 20/22) and
  the rule-21 DOF ledger.
* Registration + matrix stamp + calibration-log entry in-session regardless
  of outcome; a keeper candidate additionally fires the
  calibration-keeper-auditor on promotion.

## 7. DO-NOT-REDO and governance

**DO-NOT-REDO** (miso-183 §9 carried in full): `miso_south_firm_export_block`
`G` (re-open only per miso-182 §6b; §5's ladder-tail license is a DIFFERENT
mechanism-in-kind — a price-responsive sink curve, nothing forced);
`miso_seam_coincident_envelope` `R`; `measured_interface_limits` `R`;
`m2m_seam_entitlement_cap` `G`; `import_shape_lever` `G`;
`internal_congestion_split` `G`; `zonal_loss_surface` `R`; within-unit
`measured_offer_surface` `R`; `gas_hub_basis_overlay` `R`; `ramp_envelopes`
`I`; `dam_availability_rebasis` `R`; the ordc/reserve and dispersion
families; the `miso_offer_spread_anchored` unspent re-open clause (untouched;
this session may not be cited as graft evidence). The miso-183 basis
adjudication is CLOSED (V-TRADE, three-legged refutation): this session does
not re-litigate it and does not quote the pool-basis +1.19 as the object's
size. `ba_code="SOCO"` stays a FORECAST-lane rule-14 item — out of scope.
The internal RDT direction (the too-cheap Midwest stack) is NOT this
session's lever: S-2 is its MEASUREMENT, not its repair.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; MISO holds
neither marker (fail-closed); the spend freeze ACTIVE and untouched; no
re-key owed. Rule 23: the ladder is frozen against residuals — the ONLY
re-derivation this session may commit is the §5 corrected-basis one under an
ESTABLISHED V-DEFECT-BASIS, citing the methodology finding. Rule 1
`[R-STRUCT]`: the A/B is adjudicated on structure first (S-2/S-3); backcast
fit alone neither saves nor kills the arm. Rule 12: years sequential within
each invocation; the two invocations sequential on this container. Rule 15:
every completed solve registered. Rule 24: the new field (if built) lives in
`ScenarioConfig` and the run's `run_config.json`. Rule 26: §5.4 queue stamp +
calibration-log entry + MISO shard cell in-session; the new-field matrix row
in the same push as the field. Rule 27 `[R-PUSH]`: exact on-disk bytes; every
pushed blob ≥ 300 lines verified. No new `.github/workflows`. Owner decision
points (D-4 posture; the promotion call under a split verdict) restated in
the finding, decided by the owner, not here.

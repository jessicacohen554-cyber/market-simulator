# PRECOMMIT — ercot-219 (OPTION-B PHASE-1): the ercot-218b three-stage structural artificial-shortage mechanism, built under B-1 and armed A/B on the ercot-215 keeper recipe, judged ONLY by the card-§4 direction-blind gate table

**Session ercot-219, 2026-08-18, branch
`claude/ercot-219-option-b-phase1-5cs9bf`. PUSHED AND BLOB-VERIFIED BEFORE ANY
SOLVE.** Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json`:
**`2026-08-17-ercot215-arm-decontam`** — determination NOT-YET, fail set
{C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c the ledgered CAVEAT ×3
(68/181, 22/53, 1/31). RETENTION HOLD honoured:
`2026-08-16-ercot213-ctl-headbase` and `2026-08-15-ercot204-rule26-delete`
are NOT pruned this session.

## §0 CHARTER, SIGNATURE, AND QUEUE POSITION

This session executes §5 of
`docs/DECISION-CARD-ercot218b-artificial-shortage-structural-2026-08-18.md`
(the card), whose **B-1 is SIGNED (owner, by dispatch of ERCOT-219,
2026-08-18)** — the signature is appended verbatim at the foot of the card
(commit `ecbad28`), constituted by the owner's dispatch per the card's closing
clause and the X-1/X-2 signature-by-dispatch precedent. B-1 authorizes ONE
scoped exception: the measured **aggregate-capability reconciliation**
(NP6-905 quantity columns only, never a price column), applied consistently
across all backcast years under rule 14's reconciled-real-data clause, with
runs carrying it marked `capability-reconciled` and the C6 attestation naming
the signature. Every per-unit and per-price form stays closed (ERCOT-159/163
adjudications untouched; item 11 Q-B FINAL).

**Off-queue status, stated per rule 28(a):** the ERCOT §5.1 queue holds no
live un-adjudicated in-model item (FINDING-ercot218 §0 — the lane CLOSED and
the ISO RESTED on Door D). This lane is off-queue **by the owner dispatch of
ERCOT-219 itself and the signed card** — the dispatch is the charter.

**Pre-solve basis measurement, committed with this precommit:**
`scripts/probes/ercot219_basis_phase0.py` →
`results/calibration/ercot219_basis_phase0.json` (read-only, no LP,
quantity-only; the actual-RT read enumerates gate hour sets only). Its numbers
are cited below as `basis_phase0`.

## §1 THE DELTA — the keeper recipe + THREE booleans, zero fitted scalars

Three NEW `ScenarioConfig` fields, all **default False** (keeper-reproducing),
all reachable only under `iso == "ERCOT"`, armed via the replay `--set`
channel (recorded in `meta.json`'s `coal_prb_sigmoid_overrides` /
`prb_overrides` block and in `run_config.json.scenario_config`, rule 24):

1. **`ercot_capability_reconciliation`** — stage 1, the B-1 keystone.
   Backcast-only measured availability overlay
   (`_BACKCAST_ONLY_OVERLAY_FIELDS`).
2. **`ercot_exhaustion_expectation`** — stage 2, the within-day exhaustion
   probability from the model's own post-reconciliation state.
3. **`ercot_storage_reservation_offer`** — stage 3, the P1-only storage
   reservation-price discharge offer. Armed without stage 2 it is a loud
   `ValueError` (nothing to price), never a silent no-op (rule 5).

All three register in `_CACHE_KEY_OPTIONAL_FIELDS` +
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit (the nyiso-119
discipline), so the pinned default cache key `603c2498bf71d21d` is UNMOVED
(seam proof SP-4) and `tests/test_persisted_identity.py` still passes.

### §1.1 Stage 1 — capability reconciliation (card §7 items 1–2, PINNED)

**Basis column: `rtolhsl`** (NP6-905-CD "Real-Time On-Line High Sustainable
Limit", MW — the total online-capability aggregate;
`scripts/data/fetch_ercot_ordc_reserves.py`, `data/raw/ercot/
ercot_<yr>_ordc_reserves_hourly.parquet`, hourly-meaned SCED intervals on the
fixed non-leap CST clock). **`rtolcap` is REFUSED as the basis**, on two
grounds: (a) it is a ramp-limited reserve-*headroom* quantity, not a
capability aggregate — dimensionally the wrong object for an energy-side
availability reconciliation; (b) it is already the armed reserve-side
supply-cap input (`ercot_reserve_supply_cap` →
`results/scarcity.ercot_rtolcap_supply_cap_mw`, reading `rtolcap`/`rtoffcap`),
and rule 19 forbids one telemetry column owning two mechanisms. The energy
side and the reserve side thus carry DISJOINT NP6-905 columns.

**The telemetered thermal aggregate** (all measured, quantity-only,
committed):

```
T_tel(t) = rtolhsl(t) − wind_hsl(t) − solar_hsl(t) − storage_capability(t)
```

with `wind_hsl`/`solar_hsl` from `data/raw/ercot-hsl/
ercot_<yr>_hsl_hourly.parquet` and `storage_capability` from
`data/raw/ercot-storage-capability.csv` — the SAME committed series the armed
`ercot_storage_capability_measured` mechanism already uses, so no new source
enters the registry.

**The boundary misalignment, measured and documented (rule 14 clause):**
`basis_phase0.closure_2023_t_tel_vs_sced_truth` — against the SCED-corpus
all-thermal online-HSL truth (the ERCOT-155 census taxonomy,
`derive_ercot_energy_online_capability._scan`), `T_tel` tracks at
**corr 0.9957** with a **stable −4.05 GW level offset** (p10 −5.43 / p50
−3.98 / p90 −2.80 GW; hour-of-day profile flat −3.8…−4.2 GW; summer-evening
mean −3.99 GW). A stable level offset at 0.996 shape correlation is a
population-boundary term — the cogen/PUN boundary the NP6-905 aggregate and
the SCED-corpus population draw differently — not noise and not a shape
signal. **The reconciliation therefore EXCLUDES the model's CHP classes
(`CC_CHP`, `CT_CHP`, `ST_CHP`, 13.2 GW nameplate) from BOTH sides**: they are
the model's representation of exactly that cogen/PUN population, they stay on
their own measured availability basis (CAMPD windows + `wefor_residual`, the
DAM family's own exclusion rationale), and the offset is thereby kept OUT of
the scalar instead of imported as ~4 GW of spurious over-tightening.

**The reconciliation arithmetic (single hourly scalar, tighten-only):**

```
N(t)  = Σ pmax·avail over model rows with fuel_type ∈ {nuclear, hydro}
M(t)  = Σ pmax·avail over merchant thermal rows
        (not CHP, not nuclear, not hydro — the {CC_REGULAR, CT_PEAKER,
         ST_GAS, COAL*} population)
s(t)  = clip( (T_tel(t) − N(t)) / M(t), 0, 1 )
availability[merchant, t] *= s(t)
```

* `s ≤ 1` — **tighten-only, never loosen**: availability never rises above
  its CAMPD-outage-derated (and DAM-rescaled, and event-capped) level, and a
  fully-outaged unit stays at zero — the card's "floor at the
  CAMPD-outage-derated level, never resurrect an outaged unit", satisfied by
  construction.
* Any hour with a NaN in any input series → `s(t) = 1` (overlay inert that
  hour, count reported). **The 2025 post-RTC+B tail: exactly 648 hours,
  8112–8759 (2025-12-05 00:00 on), where the fetch preserves the ended ORDC
  regime's series as NaN, never fabricated** (`basis_phase0.
  np6905_null_patterns`; `docs/ercot-reserve-supply-scarcity-handoff-2026-06.md`
  Task A). The overlay is inert there — which is also the regime fact: RTC+B
  removed the sequestration design the mechanism represents.
* Real hydro/other online HSL not subtracted from `T_tel` (~0.3–0.5 GW) is a
  small UNDER-tightening bias — the conservative direction — disclosed here.
* Applied **inside `data/fleet/arrays.py::_apply_outage_overlays`, after the
  DAM-rescale + ERCOT-148/149 event-cap blocks and before
  `_compose_min_gen_floors`**, so every min-gen floor is clamped to the
  post-reconciliation `pmax × availability` and the LP stays feasible by
  construction. Gate: `iso == "ERCOT" and config.mode == "backcast" and
  config.ercot_capability_reconciliation`.

**Rule-19 single-owner resolution (card §7 item 2, PINNED):** the thermal DAM
availability rescale (`ercot_thermal_dam_availability{,_hourly,_plant}` +
event caps) remains the owner of **class/plant-grain day-ahead declared
availability** — the within-fleet allocation and shape. Stage 1 becomes the
owner of **the aggregate real-time online level**, and ONLY that: it is a
single hourly scalar computed against the POST-DAM-rescale aggregate, so
whatever the DAM rescale already removed is never removed twice, and it is
tighten-only, so it never fights the DAM rescale's restore direction. The
CAMPD outage overlay's ownership (unit outage events) is untouched — the
scalar multiplies its output and can only deepen it. One phenomenon, one
owner per grain; the D-2/D-4 availability-overlay attribution note carries
this composition (G-D2).

### §1.2 Stage 2 — the exhaustion expectation (zero new scalars)

Computed in the shared backcast driver (`scripts/run_calibration.py::
run_year`) immediately before `run_energy_solve`, from quantities already in
scope — nothing new enters the registry:

```
cap_total(t) = Σ pmax·avail (ALL thermal rows, post-stage-1)
             + Σ storage_power_cap
             + Σ_z wind_cf·wind_cap + Σ_z solar_cf·solar_cap
H(t)         = cap_total(t) − Σ_z demand(z,t) − AS_seq(t)
P_exhaust(t) = max over h ∈ [t .. end-of-day(t)] of LOLP(H(h))
```

* **Window convention (card §7 item 3, PINNED): remainder-of-operating-day**
  — the card-§2 formula itself, `[t .. end-of-day]` on the fixed-CST calendar
  day (a 365×24 reverse cumulative maximum; rule 2 vectorized). The
  fixed-evening-block alternative is refused: it would add a window choice
  the card's own formula does not carry.
* **Load basis (card §7 item 3, PINNED): the solve's own zonal demand sum**
  — the measured backcast load already carried as the LP's demand input. No
  second load series enters.
* **`AS_seq(t)` = the sum of the armed `*_withheld` reserve families' LP
  requirement rows** — `ECRS_withheld` (rigid whole-2023 and 2024
  h < 5088, the release-reform boundary) + `RRS_withheld` + `RegUp_withheld`
  (rigid to RTC+B), exactly as `model/reserves/spec.py::
  _ercot_multiproduct_design` builds them for this keeper, **post-credit**
  (the LR RRS-UFR and storage AS-award credits are already netted in those
  rows). The design is re-derived via the same `get_reserve_design` call the
  solve uses — zero re-implementation of window logic, zero drift surface.
* **`LOLP(·)` is the model's OWN registered curve, evaluated through the
  registered machinery**: `results/scarcity.resolve_lolp_params(config,
  hours)` (flat `ordc_lolp_mu_mw = 0`, `ordc_lolp_sigma_mw = 1400`,
  `ordc_lolp_shift_sigma = 0.5`, `ordc_mcl_mw = 3000` — all existing cited
  constants, `config/scenarios.py:2833-2868`) and the registered normal-CDF
  form (`scarcity.py:238-268`): `LOLP = 1 − Φ((H − MCL − μ_eff)/σ)`,
  administratively 1.0 at `H ≤ MCL`, `μ_eff = μ + shift·σ`. The FULL-tier
  form (the total-curve evaluation), pinned as the convention.
* **The ercot-206 B0 distinction, stated explicitly as the dispatch
  requires:** B0 (no LOLP-table arming as a PRICE mechanism) is UNTOUCHED.
  The in-LP ORDC demand curve, the written adder and every price channel are
  byte-unchanged by stage 2. The `ordc_lolp_*` constants enter here as an
  **EXPECTATION input** — the probability argument of a reservation price —
  not as a price table; the only price formed from it is stage 3's offer,
  which then clears (or does not) through the LP like any other offer.
* Renewable bounds enter UNcurtailed (`wind_cf·wind_cap` before the WTX
  corridor ceilings): the corridor binds West export at high-wind hours,
  ~zero at evening exhaustion hours; convention disclosed.

### §1.3 Stage 3 — the storage reservation-price offer (zero new scalars)

```
P1 discharge offer[s, t] = max( vom_base[s], P_exhaust(t) × ordc_voll )
```

* `ordc_voll` = the registered $5,000 (16 TAC 25.509, `scenarios.py:2833`),
  read from the run's resolved config (override-applied in `run_year`; the
  keeper records 5000.0). `vom_base[s]` = the keeper's existing per-unit
  storage discharge cost (`battery_dispatch_adder = 10.0` on ERCOT batteries,
  a registered keeper constant) — since `vom_base ≥ ε` by construction, the
  card's `max(ε, ·)` floor is subsumed, and the raise-only form keeps the
  keeper's ordinary-hour storage dispatch untouched wherever
  `P_exhaust × VOLL` is below the existing offer. This is what makes the
  mechanism **self-extinguishing** (card §2): as `P_exhaust → 0`
  (post-reform, post-RTC+B, forecast years without sequestration) the offer
  collapses to the keeper's own, rather than to a new ε-level channel that
  would re-price every ordinary hour.
* **Seam (PINNED, with the measured reason):** the card names the
  `mc_bid_adjust` seam; measured at build time, that seam's `(n_gen, T)`
  array reaches ONLY the thermal P-block columns
  (`model/lp/costs.py:97` vs the storage block at `:112-120`) — storage
  discharge cost is a separate `(n_storage,)` objective input. Stage 3
  therefore applies at **the SAME P0→P1 seam in `pipeline/solve.py::
  run_energy_solve`** through a new `p1_storage_discharge_cost` parameter:
  P0 (commitment discovery) solves first on the untouched base cost, then the
  `(n_storage, T)` reservation array re-costs the storage discharge columns
  for the P1 clearing solve only — an objective-coefficient change exactly
  like the thermal `mc_bid` re-cost, warm-start preserving on the live model
  and threaded into the kwargs on the cold-rebuild path. **P0 untouched, by
  construction and by seam proof.**
* **Energy-only (card §7 item 4, PINNED):** no AS-product opportunity-cost
  floor is built — out of scope by the card's own default.
* The adaptive/backward-expectation extension (June/July cap-parking,
  September's August-informed pricing) is **OUT OF SCOPE** — its own future
  card only (card §2 stage 3).

## §2 IDENTIFICATION / DOF LEDGER (card §3, verbatim; target zero fitted scalars)

| quantity | source | fitted? |
|---|---|---|
| aggregate capability series | published NP6-905 telemetry, committed, quantity-only | no — measured (B-1) |
| sequestered AS MW | measured ASPLANNP433 plan + armed withholding families | no — already keeper inputs |
| LOLP μ/σ, MCL | registered `ordc_lolp_*`, `ordc_mcl_mw` (published ORDC basis) | no — existing cited constants |
| cap | `ordc_voll` = $5,000 (16 TAC 25.509) | no |
| window / load-basis conventions | precommit-pinned conventions with citations | no (conventions, disclosed) |

Supplementary measured inputs of the stage-1 netting (`wind_hsl`,
`solar_hsl`, `storage_capability`) are committed quantity series already in
the registry's orbit (the storage series is an armed keeper input). **Any
quantity that cannot be sourced this way during the build is a STOP** — the
mechanism is not built with a fitted stand-in (rules 5/13/23; card §3).

## §3 KILL GATES (card §4, VERBATIM) — direction-blind, pre-registered, inherited baselines

The A/B (control = the ercot-215 keeper recipe, replayed; arm = control +
stages 1–3) is judged ONLY by this table, never by the sign of any residual
move (the ercot-204/213/215 discipline):

| gate | rule |
|---|---|
| G-CAP | 0 protocol-cap violations (λ + adders ≤ VOLL) in all 26,280 hours |
| G-SPUR | spurious mid-band hours vs the 9/11/1 energy-made baseline, bar +5/yr (ercot-213 §3 inheritance) |
| G-SHED | no new load-shed hours vs the keeper's 0/1/0; identical-hour-list check |
| G-OWNER | C3a-2024 PASS, C3a-2025 PASS, C3b-2024 ≤ 0.20 all retained |
| G-BAT | storage net discharge at actual-tail hours within ±25 % of measured EIA-930 BAT where the series exists (2024/2025) — the ercot-162 collapse falsifier |
| G-EXH | reported, not gated: the count and calendar of model exhaustion-regime hours per year (the 2023-vs-2024/25 contrast is the mechanism's own signature) |
| G-DOF | ledger delta = the B-1 series only; zero fitted scalars; n_residual not increased |
| G-D2 | no new D-4 off-window rows; stage-1/stage-3 attribution rows present with declared windows (rules 17/19/20) |
| G-REPRO | control replays the keeper's committed determination before the arm is read |
| LOYO | parameter-free rule → structurally N/A, declared pre-solve; per-year deltas stand in its place (ercot-173/213 precedent). If ANY scalar ends up identified, full LOYO 2023–2025 before promotion |

**Verdict rule (card §4, verbatim):** any gate FAIL ⇒ REJECTED-AS-ARMED at
full magnitude, recorded unrewritten; owner promotion over a mechanical kill
remains an explicit owner act (the ercot-188/213/215 pattern), never the
session's. **This session does not promote.**

### §3.1 Measurement conventions per gate (pinned ex ante)

* **G-CAP** — `scripts/probes/ercot213_anchor_gates.py` on both members
  (written `ordc_adder ≤ VOLL − λ` in every solved hour).
* **G-SPUR** — model ∈ [150, 500) while actual RT < $150, from the committed
  `system_<yr>.parquet` vs the actual series; baseline hour SETS inherited
  from the keeper: 2023 = {5438, 5439, 5443, 5660, 5684, 5731, 5804, 5821,
  5822}, 2024 = {336–339, 345–349, 2540, 2829}, 2025 = {3355}
  (ercot-215 G-EXACT). Bar: ≤ +5 per year vs 9/11/1.
* **G-SHED** — keeper shed = 0/1/0 with the single 2024 hour h3067;
  identical-hour-list comparison on both members.
* **G-OWNER** — the armed member's own official scorecard
  (`scripts/calibration_verdict.py`, committed artifacts only).
* **G-BAT** — model storage net discharge (`Dis − Chg` from
  `hourly/storage_<yr>.parquet`, summed over units) vs EIA-930 `BAT`
  (`data/raw/ERCO_fueltype.parquet`), summed over the ACTUAL RT>$200
  tail hours that fall inside the BAT series' coverage, |model/actual − 1| ≤
  0.25. **Clock discipline (ercot-216 §6, BINDING):** 930 `period` is
  hour-ENDING UTC → shift −1 h to hour-beginning, convert to CST, map onto
  the fixed non-leap clock date-wise (2024's post-Feb-29 hours land 24 h
  later in real time than the naive 8760 label). **Coverage measured ex
  ante** (`basis_phase0.gbat_coverage`): 2024 BAT starts 2024-11-06 → **9 of
  53** tail hours measurable; 2025 → **31 of 31**. 2024's thin coverage is
  disclosed here, before any solve; the gate reads only covered hours, and
  the covered-hour count is reported with the verdict.
* **G-EXH** — reported per year: (a) **exhaustion-regime hours** =
  `LOLP(H(t)) ≥ 0.5` (the stack effectively exhausted at that hour's own
  margin — parameter-free threshold: the curve's own median point), with the
  monthly calendar; (b) alongside, hours with `P_exhaust(t)·VOLL ≥ $1,000`
  (reservation offers in the spike range). Both definitions pinned here,
  before any solve.
* **G-DOF** — `scripts/build_dof_ledger.py` on both bundles: the arm's delta
  vs control = the B-1 measured-series entry only; `n_residual` not
  increased; zero fitted scalars.
* **G-D2** — `legitimacy_diagnostics.json` on both bundles: D-4 FAIL row set
  unchanged (the 3 pre-existing `reliability_floor × CT_PEAKER` h14-21
  rows); the stage-1 availability-overlay attribution note and the stage-3
  offer-channel attribution note PRESENT on the armed bundle with their
  declared windows (stage 1: all-hours, a standing measured physical state;
  stage 3: the within-day exhaustion window its own driver defines).
* **G-REPRO** — the control replay's own official determination must
  reproduce the keeper's committed determination (NOT-YET, fail set
  {C3a-2023, C3b-2023}, C3c ledgered CAVEAT ×3 at 68/181, 22/53, 1/31)
  BEFORE the arm is read. Sidecar sha256s vs the keeper bundle reported at
  full magnitude alongside (12/12 expected on an ERCOT-effective-unchanged
  tree; any drift reported, and score-inert drift does not fail the gate —
  the ercot-213 G-REPRO′ reading).
* **LOYO — declared N/A PRE-SOLVE, here:** the three stages carry **zero
  fitted scalars** — every input is a committed measured series, an armed
  keeper input, or a registered cited constant, and every convention is
  pinned in this document before any solve. Nothing is identified on any
  year, so leave-one-year-out is structurally N/A; per-year deltas stand in
  its place. If ANY scalar ends up identified during the build, that is a
  §2 STOP first, and full LOYO 2023–2025 before any promotion talk second.

### §3.2 The honest expected-landing statement (NOT a gate, NOT a basis)

Unlike ercot-215 (post-solve delta, exact counterfactual), this delta moves
MW: no exact pre-solve scorecard exists. Stated risk zones, direction-blind:
stage 1 embeds realized commitment into the availability envelope
consistently across ALL hours (B-1's accepted tension), so ordinary-hour
tightening may move mid-band prices (G-SPUR exposure) and 2024/2025 criteria
(G-OWNER exposure); stage 3 raises storage offers wherever the within-day
window carries exhaustion risk (G-BAT exposure if the model's batteries
withdraw where reality's discharged). The arithmetic sanity check from the
measured margins (RTOLCAP median at the 2023 tail ~6.5 GW, sequestered AS
~5.1 GW ⇒ H ~1–4 GW ⇒ reservation offers ~$1,500–5,000, against the measured
Aug-2023 storage p50 $3,361) is context, not a prediction, and no gate reads
it. Q-B/R-A: every 2023 price number in the A/B is side-effect reporting at
full magnitude — the gate table contains no 2023 price criterion by design.

## §4 SEAM PROOFS (before any A/B solve; committed as `results/calibration/ercot219_seamproof.json`)

* **SP-1 gate-off byte-identity ×3 years (array grain):** at HEAD with all
  three fields at default, the assembled ERCOT fleet availability matrix and
  the P1 storage cost inputs are byte-identical to the pre-edit tree for
  2023/2024/2025 (the overlay/expectation/offer code is unreachable at
  default). The FULL-SOLVE gate-off identity is then proven by the control
  replay itself (G-REPRO: determination reproduction + sidecar sha256s) — the
  ercot-215 pattern, where the control doubles as the whole-solve gate-off
  proof.
* **SP-2 cross-ISO byte-identity, ARMED (all five non-ERCOT ISOs):** with all
  three booleans forced TRUE on CAISO/PJM/MISO/NYISO/NEISO configs, each
  ISO's assembled availability matrix and storage-cost inputs are
  byte-identical to gate-off (the `iso == "ERCOT"` gates make the arm
  unreachable), proven at the assembly grain per ISO (the ercot-188 SP-2
  reconstruction pattern; full non-ERCOT solves are not licensed by rule 25
  and not needed — the gate is upstream of every LP input).
* **SP-3 no-price-input audit:** the stage-1/stage-2 code paths read ONLY
  the named quantity columns — `rtolhsl`, `wind_hsl_mw`, `solar_hsl_mw`,
  `capability_mw`, the AS-plan requirement rows, and model-internal arrays.
  The proof JSON writes the READ set and the REFUSED set
  (`system_lambda`, `prc`, `rtorpa`, `rtoffpa`, `rtordpa`, `rtolcap`,
  `rtoffcap`, every LMP/RTSPP/DA series, every model price output) — the
  `basis_phase0.mechanism_read/mechanism_refused` sets, re-asserted against
  the shipped code.
* **SP-4 cache-key discipline:** pinned default key `603c2498bf71d21d`
  UNMOVED with the three fields registered dropped-at-default; the armed
  ERCOT key distinct. `tests/test_persisted_identity.py` green.

## §5 EXECUTION

* **Solve environment PINNED** (the keeper's `meta.environment`, the
  ercot-213/215 standing note): python 3.11.15, highspy 1.15.1, numpy 2.4.6,
  scipy 1.17.1, pandas 3.0.5, pyarrow 25.0.1, pydantic 2.13.4 (+ openpyxl,
  tzdata), venv **OUTSIDE the project directory** (`/home/user/solve-env`) —
  the `.claude/hooks/ruff-autofix.sh` `uv run` re-sync trap makes `.venv`
  unpinnable.
* `data/clean/gtc-limits` regenerated from `data/raw` before any replay (the
  keeper arms `ercot_gtc_limits_measured`; expected partition rows
  13,452 / 15,273 / 21,864 for 2023/24/25).
* **Control:** `scripts/replay_keeper.py results/calibration/
  ercot215_decontam_B --out-dir results/calibration/ercot219_control_A`
  — full span `2023 2024 2025` in ONE invocation, years SEQUENTIAL (rule 12).
* **Arm:** same + `--set ercot_capability_reconciliation=true --set
  ercot_exhaustion_expectation=true --set ercot_storage_reservation_offer=true
  --out-dir results/calibration/ercot219_optionb_B`.
* The two members run **sequentially, never concurrently** (~12.7 GB peak RSS
  each on a 15 GB box).
* **G-REPRO is read BEFORE the arm** (card §4): the control's determination
  must reproduce the keeper's, or the line stops.
* **Registration (rule 15):** BOTH members register on the backcast registry
  with payloads — intended ids `2026-08-18-ercot219-ctl-headbase` /
  `2026-08-18-ercot219-arm-optionb` — bundle slim files + sidecar + run
  payload + changed bench committed and pushed the same session; run payloads
  over `git push` (HTTP/1.1 fallback on a hung push, the fh-5 §6 note).
  Roster: ERCOT holds 5 registered runs; +2 = 7, under top-15, no eviction;
  the RETENTION HOLD pair is not pruned.
* **The armed member's attestation is marked `capability-reconciled` and its
  C6 text names the B-1 signature** (B-1's own condition). The mechanical
  verdict is recorded unrewritten; **promotion is a separate owner decision
  on the recorded verdict — NOT taken in-session** (dispatch order).
* **Matrix (rule 28c + duty b):** a NEW base row for the mechanism family
  (`ercot_artificial_shortage_pricing`, mechanism-level, naming all three
  fields) in `docs/codebase-site/data/mechanism-matrix.js` + a cell line in
  EVERY ISO shard (ERCOT with the tested verdict + evidence; the five others
  `·` n/a by the rule-25 gate), stamped in the same session, rejections
  included. `scripts/check_mechanism_matrix.py` exit 0.
* FINDING doc + `docs/calibration-log/ercot.md` entry under **ercot-219**
  (ercot-199 remains unclaimed).

## §6 FENCES AND STANDING RULINGS (cited, never re-litigated)

Rule 22: {2023, 2024, 2025} only; no marker sought; no out-of-training year
solved, scored or registered. Rule 25: ERCOT only — every stage gates on
`iso == "ERCOT"`, and SP-2 proves the armed cross-ISO no-op. Rule 27: edits
local, exact on-disk bytes pushed, ≥300-line pushed files blob-verified on
both transports. Rules 5/23/24: three registered `ScenarioConfig` fields, no
env-var knob, no off-registry channel, nothing derived from a residual.
No new workflows, no cron, no CI job; solves run in-session. No PR
(push-and-stop on the designated branch; the owner merges).

DO-NOT-REDO honoured (card §6, unchanged): Door A conduct-function fitting
(NOT-TRANSFERABLE ×3, ercot-210/211/218) — nothing here fits a conduct
function; `ercot_storage_rt_offer_surface` (R) — no measured offer surface is
fed, the stage-3 offer is computed from the model's own state; item 11
per-unit crosswalk (Q-B FINAL) — B-1 is the aggregate route BECAUSE the
per-unit route is closed, and no per-unit capability object is built; the
mid-band spill lane (CLOSED, ercot-215) and the regime lane (CLOSED,
ercot-217) — no regime parameter is added, the 2023 distinction emerges from
carried inputs; LOLP-table arming as a PRICE mechanism stays B0 — §1.2 states
the expectation-input distinction explicitly. Q-B FINAL / R-A: every 2023
price number is side-effect reporting at full magnitude, never a basis, never
a gate — the card's gate table contains no 2023 price criterion by design.

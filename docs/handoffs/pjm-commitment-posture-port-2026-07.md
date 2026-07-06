# PJM commitment-posture lever — port + honesty gate

**Date:** 2026-07-06. **Lane:** Wave-3 PJM L-13 continuation. **Status: §A PORTED
2026-07-06 (`pjm_commitment_posture`, GATED default-off) — the MISO commitment-posture lever
generalized to PJM, shared code not forked. Honesty-gate criteria pre-committed below BEFORE the
A/B solve (the MISO-lane discipline; miso-43 precedent). A/B probe `pjm-82` scored full-span
2023–2025; result recorded in §4 whatever the outcome (rules 15/16).**

Companion to `docs/multi-iso/miso-scarcity-posture-design-2026-07.md` §A (the design of record — this
note does NOT redesign the mechanism, it records the port and PJM's measured gate) and
`docs/handoffs/pjm-reserve-ordc.md` Phase 2 (the pergen reserve co-opt the posture sits on, landed
PR #1500, probed as pjm-81).

## 1. Why — the pjm-81 blocker

Probe `pjm-81` (`2026-07-06-pjm-81-coopt-pergen`) proved that PJM's published Manual-11 two-step
ORDC, wired per-generator with measured ramp caps and both nested balance families (RTO + MAD),
**fires ~once in 26,280 h**: exactly one nonzero in-LP reserve price (2025-06-23 h19, $46.47
opportunity cost, LMP → $158.61), **C3c 0 h vs 6/18/59**. Its own attribution (rule 14): with
~33–45 GW of measured-deliverable pool headroom against a ~3.3 GW measured Primary requirement, the
perfect-foresight pool margin binds essentially never. The remaining blocker is **Phase-1 commitment
posture** — the LP's online reserve never thins from ~14 GW toward PJM's real ~3 GW, because keeping
capacity online costs nothing in the no-commitment P1. That is exactly the phenomenon MISO's
`miso_commitment_posture` lever owns.

## 2. The port (what changed — not a new design)

Shared code, PJM gate added; zero mechanism divergence from MISO:

- `config/scenarios.py`: `pjm_commitment_posture: bool = False` (TIER_TAGS = 1).
- `config/reserve_config.py::_pjm_design` pergen branch: when the flag is on, calls the **same**
  `_posture_pool_params(fleet_arrays, pergen_gen_idx, pergen_col, n_r, iso)` MISO uses (already
  ISO-agnostic — takes `iso`), threading `posture_pools/mlf/startup` into the returned
  `ReserveDesign`. The dispatch U/SU columns, min-load coupling, startup charge, and online-gated
  reserve cap are the unchanged shared machinery in `model/dispatch.py`.
- `pipeline/kwargs.py`: a PJM posture log line mirroring the MISO one.
- `scripts/run_calibration_full.py`: `--pjm-commitment-posture` arg + config wiring +
  `run_config.json` record.
- `scripts/report_pjm_posture_gate.py`: the PJM honesty gate (this note's §3), ported from
  `report_miso_posture_gate.py`.

**ramp10 (rule 14, per the task):** the posture reserve cap `R ≤ ramp10_p·U` uses
`FleetArrays.ramp10` reconciled to the **measured ramp-capability datatype** (`--measured-ramp-
capability`; EIA-860 Schedule 3.1 "10M" fast-start floor + CAMPD CEMS hourly-envelope ceiling,
`data/clean/ramp-capability`, PJM registered). The A/B probe sets `measured_ramp_capability=True`;
`run_config.json` records it. Same measured input pjm-81 used — no new data.

**Parameters (rule 13/17a/24 — zero fitted):** `mlf` = CEMS-measured `committed_pct` min-stable-
when-online percentile (WWSIS-2 `MIN_STABLE_PCT_PHYSICAL` class gap-fill), startup $/MW + min-down h
from the NREL/SR-5500-55433 class tables, fast-start exemption on pool physics (min-down ≤ 2 h AND
startup < $30/MW — rule 18, never class tuples). Forward-regenerating; identical machinery serves
forecast years.

## 3. Honesty gate — PRE-COMMITTED before the solve (the MISO pattern)

**The gate is level + event-day direction against measured PJM reserve-market data, NEVER the price-
tail residual (rules 1/13).** The >$150/$200 tail count and C3a/b/c are the *readout*, reported in §4,
but they are **not** the accept/reject criterion. Measured source: `data/raw/PJM-AS/
reserve_market_results_<year>.parquet` (PJM Data Miner RT reserve market results, 5-min, by
`locale`∈{PJM_RTO, MAD} × `service`∈{REG, SR, PR, 30MIN}). Scored by
`scripts/report_pjm_posture_gate.py`, all three years.

**Measured comparators (annual-mean cleared MW, computed 2026-07-06, embedded so the gate is
falsifiable before the solve):**

| year | SR cleared | REG cleared | **online target (SR+REG)** | Primary (PR) cleared | MAD PR share |
|------|-----------|-------------|----------------------------|----------------------|--------------|
| 2023 | 2295 | 668 | **2964** | 3235 | 0.80 |
| 2024 | 2619 | 670 | **3289** | 3522 | 0.75 |
| 2025 | 2544 | 670 | **3214** | 3489 | 0.76 |

The online target is Synchronized Reserve + Regulation — the reserve products that by design must be
supplied by **online** units, the direct measured analogue of the model's postured online headroom.
(30MIN, ~15–21 GW, is deliberately excluded: it is largely non-synchronized/offline quick-start, not
online headroom.) Primary Reserve (PR = SR + non-sync 10-min) is reported as an upper-bound
reference.

### Pre-committed criteria (decision made BEFORE looking at the tail)

- **G-P1 (level) — the decisive gate.** Modeled postured online headroom (Σ postured pools `U − P`,
  the capacity the LP holds online beyond dispatch) vs the measured online target (SR+REG).
  **PASS** iff `ratio = mean(headroom)/mean(SR+REG) ∈ [0.7, 1.5]` in **all three years**. The two
  are different boundaries (model headroom includes non-cleared economic margin; the measured target
  excludes offline supplemental), so the band, not equality — but a ratio outside [0.7, 1.5] means
  the linear relaxation is not holding a physically honest amount of capacity online. **MISO
  precedent: FAIL at 3.71–4.24×** (`miso-43`, `SUMMARY-posture-gate.md`); the pjm-81 attribution
  anticipates the same ~4–5× for PJM.
- **G-P2 (event-day direction).** Daily Pearson `r` between (a) modeled reserve/balance price and the
  measured PJM_RTO SR MCP, and (b) modeled online headroom and measured cleared SR MW; plus the
  top-20 measured SR-MCP event-day same-direction count (headroom below its median OR reserve price
  above its median). **PASS** iff both daily `r > 0` AND same-direction ≥ 12/20, in ≥ 2 of 3 years.
- **G-P3 (locational split, diagnostic).** Model MAD-zone share of postured online headroom vs the
  measured MAD share of cleared PR (~0.75–0.80). Reported; **advisory** (a rule-14 boundary
  reconciliation — the model's 8-zone topology vs PJM's RTO/MAD nesting), not a pass/fail gate.

### Decision rule (pre-committed)

The lever is **ACCEPTED as keeper-eligible retained structure** only if **G-P1 PASSES in all three
years AND G-P2 PASSES**. Otherwise it **stays `pjm_commitment_posture=False` (default-off)**, the
failure modes are named (§4, the miso-43 precedent), and **no posture parameter is tuned against the
residual** (rules 1/13 — the pooled linear relaxation either holds an honest online level or it does
not; there is no admissible knob to make it, because every input is measured/published/physics). A
keeper swap is the owner's decision regardless (rule: keeper swaps are owner decisions).

## 4. A/B probe result (`pjm-82`) — recorded whatever the outcome

- **A (posture-off) = `pjm-81`** (`pjm_reserve_pergen` + `measured_ramp_capability`, posture off) —
  the registered ablation twin (rule 21). The `pjm_commitment_posture` diff is a verified no-op when
  off (`tests/test_commitment_posture.py::TestPjmPortSharesMechanism::test_pjm_off_emits_no_posture`),
  so pjm-81 is the exact A comparator on this branch HEAD.
- **B (posture-on) = `pjm-82`**: A + `--pjm-commitment-posture`, full-span 2023–2025, single bundle,
  sequential years (rules 12/16).

_(Filled in after the solve: G-P1/G-P2/G-P3 numbers from `SUMMARY-posture-gate.md`; C3a/b/c and
>$150/$200 tail hours as the readout; disposition; named failure modes if the gate fails.)_

## 5. Guardrails honoured

- Rule 1/11: structural mechanism, judged on measured-behaviour fidelity, not MAE. Retained/rejected
  on the gate, never the tail.
- Rule 13/17: measured/published/physics inputs only; NOT a floor (forces no energy — the min-load
  term binds only capacity the LP itself keeps online); no window, no D-2 id, no forward-story gap.
- Rule 14: `pjm_commitment_posture` diagnosis of the CC/ST_GAS substitution (issue #1483) is
  **diagnose-and-file only** — no second mechanism, no offer-band edits in this session. See §6a.
- Rule 18: fast-start exemption on pool physics, never class names.
- Rule 19/20: one mechanism per phenomenon (the posture owns the P1 online-reserve-level phenomenon;
  it is NOT stacked on the CT evening reliability floor or CHP steam floors — different phenomena).

## 6. Issue #1483 (ST_GAS volume driver) — diagnose-and-file only

_(Filled in from the probe artifacts: whether the posture shifts CC↔ST_GAS/CT substitution, appended
to issue #1483. No mechanism built, no offer band touched — rule 14.)_

### 6a. C8 (CT_PEAKER drag) denominator note for the owner

If the posture probe changes the `CT_PEAKER` energy denominator materially vs pjm-81, that fact is
appended to `docs/handoffs/pjm-c8-drag-memo-2026-07.md` §6a for the owner. **The C8 drag decision is
the owner's — this lane does not adjudicate it** (rule 14; keeper swaps are owner decisions).

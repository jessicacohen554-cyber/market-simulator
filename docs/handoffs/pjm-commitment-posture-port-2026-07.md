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
- **B (posture-on) = `pjm-82`** (`2026-07-06-pjm-82-commitment-posture`, bundle
  `results/calibration/pjm82_commitment_posture`): A + `--pjm-commitment-posture`, full-span
  2023–2025, single bundle, sequential years (rules 12/16). 23 of 39 pools postured (fast-start
  CT/oil exempt by physics), mlf 0.10–0.61 (CEMS committed_pct), startup $37–100/MW (NREL tables).

### Honesty gate: REJECT (decided before the tail, per §3)

`SUMMARY-posture-gate.md` (scored 2026-07-06):

| year | model online headroom | measured online (SR+REG) | ratio | G-P1 | G-P2 dir |
|------|----------------------|--------------------------|-------|------|----------|
| 2023 | 9298 MW | 2964 MW | **3.14** | FAIL | FAIL (13→15/20 but r_price nan) |
| 2024 | 9492 MW | 3289 MW | **2.89** | FAIL | PASS (13/20) |
| 2025 | 8539 MW | 3214 MW | **2.66** | FAIL | PASS (14/20) |

**G-P1 (the decisive gate) FAILS all three years** — modeled online headroom is 2.66–3.14× the
measured online reserve, outside the pre-committed [0.7, 1.5] band. (Better than MISO's 3.71–4.24×,
but the same structural failure, not a pass.) G-P2 direction passes 2024/25 only. **Per the §3
decision rule (G-P1 must pass all years AND G-P2), the lever is REJECTED.**
`pjm_commitment_posture` stays default-off. No posture parameter was tuned against the residual
(rules 1/13) — there is no admissible knob: every input is measured/published/physics.

### The readout (reported, NOT the gate) — criterion-comparable to pjm-81

- **C3c price tail: still 0 h** (model 0 h vs RT 6/18/59; vs 2025 DA actual 51 h). **>$200 and
  >$150 tail hours: 0** in all three years (system LMP max ~$141). Identical to pjm-81 — the
  posture does **not** unblock scarcity pricing.
- C3a −8.3 % (2024, caveat) / −13.5 % (2025, FAIL); C3b NRMSE 0.185/0.175/0.197 (commercial band).
  All criterion-comparable to pjm-81 (dispatch is ~byte-comparable at class grain).
- C1 all 14/16 · free 10/12; C4/C5a PASS. NOT-YET (C6 unattested — probe).

### Named failure modes (the miso-43 precedent — why the level fails)

The pooled **linear** UC relaxation cannot hold an honest online level under perfect-foresight
dispatch. `U[p,t]` is continuous, so the LP keeps *fractional* online capacity across the 23 pools
at near-zero marginal cost: the min-load coupling only forces `Σ P ≥ mlf·U` (it does not force `U`
*up*), and the annual startup charge, amortized over 8760 h of foreknown load, is a negligible
per-MWh adder against the value of universal deliverable headroom. So `U` sits near the economic
dispatch envelope (~9 GW of postured-pool headroom) instead of collapsing to the ~3 GW real
synchronized reserve — exactly the MISO miso-43 mechanism (there 3.7–4.2×). The honest online-level
collapse needs **integer** commitment (a MIP `u∈{0,1}` per unit-hour), which the LP-only mandate
(P1 is THE run, no MIP — CLAUDE.md Stack/Dispatch) excludes. This is a representation boundary, not
a tuning gap; it is logged, not closed here.

### Disposition

Keeper stays `2026-07-05-pjm-77-ct-relfloor` (owner decision regardless — keeper swaps are the
owner's). pjm-82 is a **rejected probe**, registered per rules 15/16. The `pjm_commitment_posture`
code stays in-tree, GATED default-off (a re-armable measured mechanism, not a fitted knob — rule 26
does not apply; nothing was tuned). The pjm-81 conclusion stands unchanged: the PJM C3 tail is
blocked on the LP-vs-MIP commitment representation, and the posture lever — the strongest admissible
**linear** proxy — does not bridge it.

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

The posture probe **rules commitment posture OUT as an ST_GAS volume driver** — it moves the
CC↔ST_GAS substitution the WRONG way. Class totals, pjm-82 (posture on) − pjm-81 (posture off):

| year | CC_REGULAR Δ | ST_GAS Δ | CT_PEAKER Δ |
|------|-------------|----------|-------------|
| 2023 | +1.37 TWh (289.8→291.2) | −0.28 (18.57→18.29) | −0.32 (25.37→25.05) |
| 2024 | +1.74 TWh (316.6→318.3) | −0.30 (16.23→15.93) | −0.10 (20.69→20.59) |
| 2025 | +1.50 TWh (302.0→303.5) | −0.18 (19.07→18.89) | −0.22 (33.06→32.84) |

The CEMS min-load coupling `Σ P ≥ mlf·U` on the **postured CC pools** pins a little more CC baseload
online, so posture *adds* ~1.5 TWh/yr to CC_REGULAR (already the over-run class, #1483) and *shaves*
ST_GAS/CT — the opposite of the missing driver. So commitment posture is **not** candidate #4; the
#1483 driver still lies among RMR/must-run, local deliverability, or per-plant HR error (the issue's
listed candidates). Appended to issue #1483. No mechanism built, no offer band touched (rule 14).

### 6a. C8 (CT_PEAKER drag) denominator note for the owner

**The posture does NOT move the CT_PEAKER denominator materially** (2024: 20.69→20.59 TWh, −0.10;
the breach-year forced share stays **12.0 %**, D-2 numerator 2.49→2.47 TWh). So the C8 §6a
conclusion is unchanged by this probe. A one-line null-result note is appended to
`docs/handoffs/pjm-c8-drag-memo-2026-07.md` §6a. **The C8 drag decision is the owner's — this lane
does not adjudicate it** (rule 14; keeper swaps are owner decisions).

# FINDING — the C3c adder object is the ORDC curve's ARGUMENT, not its steepness: the model prices reserve *shortfall against its own requirement* where ERCOT prices *online capability* (ercot-253, phase 0)

> **Phase 0, read-only** (rule 29 clause 0): no LP, no solve, no arm, **no matrix
> cell verdict minted**. Identified on the TRAINING years 2023-2025 ONLY (rule 22
> step 3), from the designated keeper's own committed `reserve_family_<y>.parquet`
> sidecars and ERCOT's measured `ercot_<y>_ordc_reserves_hourly.parquet`. Keeper
> `2026-09-05-ercot248-two-config-keeper`; nothing here reads 2021 or 2022.
> Probe: `scripts/probes/ercot253_c3c_adder_distribution.py`.

## 1. The question, and where it came from

`RESULT-ercot252` §5.1 read the 2022 rung — mean +9.3 % while the tail stayed at
half the actual — as *"the adder is spread across too many mid-band hours and not
steep enough in the true tail"*, and routed the object here to be identified
in-sample. That reading is **half right and half backwards**, and the half that is
backwards matters more than the half that is right.

## 2. What the keeper's own sidecars say

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| hours the model writes an ORDC adder | **573** | **191** | **67** |
| hours ERCOT's published RTORPA writes one | **1,705** | **560** | **253** |
| model writing hours ⊂ published writing hours | **yes** | **yes** | **yes** |
| Σ adder $ — model / published | **25,219 / 8,281** | **3,277 / 1,777** | 28.9 / 530.7 |
| p99 adder on own writing hours — model / published | **1,040.78 / 96.22** | **540.24 / 77.93** | 6.77 / 11.12 |
| max adder — model / published | **5,000.00 / 650.82** | **760.22 / 252.69** | 15.04 / 414.12 |

2025 measured coverage is 8,112 h (the RTC+B tail carries no RTOLCAP/RTORPA); 2023
and 2024 are complete at 8,760 h.

Band by band (model / published), 2023:

| band $/MWh | [0.01,1) | [1,10) | [10,50) | [50,150) | **[150,500)** | **[500,1000)** | **≥1000** |
|---|---|---|---|---|---|---|---|
| 2023 | 265/519 | 99/186 | 36/68 | 9/29 | **19/9** | **7/2** | **7/0** |
| 2024 | 96/100 | 25/52 | 10/17 | 5/5 | 2/4 | **3/0** | 0/0 |

**The model writes in FEWER hours than the published ORDC, never more — one third
of them in 2023 and 2024, a quarter in 2025 — and its writing hours are a strict
SUBSET of the published ones in all three years. It then writes far too much in
the hours it does reach:** three times the published adder dollars in 2023, 1.8×
in 2024, a p99 an order of magnitude high, and seven hours ≥ $1,000 in 2023
against a published year whose largest adder all year was $650.82.

So the "too many mid-band hours" half is **wrong by a factor of three, in the
opposite direction**; the "shape not level" half is **right**, and sharper than
stated: the model under-writes every band below $150 and over-writes every band
above it. *(No number in `RESULT-ercot252` is retracted: its 811 hours are the
reserve-supply **cap** rows, a different family row from the ORDC total dual read
here. What was wrong was the inference, not the measurement.)*

## 3. The cause: the two curves are functions of DIFFERENT QUANTITIES

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| model `held_mw` p50 (the ORDC family's argument) | 8,545 | 7,682 | 7,410 |
| model `requirement_mw` p50 | 8,550 | 7,686 | 7,410 |
| hours with `held ≥ requirement` | **93.5 %** | **97.8 %** | **99.2 %** |
| measured RTOLCAP p50 (the published curve's argument) | **12,745** | **16,197** | **18,551** |
| mean (RTOLCAP − held) | **+5,028 MW** | **+9,063 MW** | **+11,922 MW** |

**The model's ORDC family prices off reserve cleared to its own requirement** —
`held` tracks `requirement` to within a handful of MW in 93-99 % of hours, by
construction. **ERCOT's ORDC prices off RTOLCAP, total online reserve
capability**, which sits a mean 5.0 / 9.1 / 11.9 GW above what the model's family
holds and is a different physical quantity, not a mis-scaled version of the same
one.

That single substitution produces the whole observed signature:

* a function of *shortfall against a requirement* is **exactly zero** until the
  requirement is actually violated → too few writing hours, and every one of them
  a genuine violation, which is why they are a strict subset;
* once violated it descends a VOLL-anchored curve with nothing above it → far too
  large when it fires, reaching $5,000 where the published year's maximum was
  $651;
* the published curve is a continuous LOLP on *capability*, so it writes small
  amounts often — 519 hours in the sub-$1 band alone in 2023 — which the model
  structurally cannot produce.

The steepness is not the defect. **Evaluated on its own axis the model's curve is
FLATTER than the published one over most of the range** (at 4,000-5,000 MW: model
p50 $15.04 vs published $250.61; at 5,000-6,000 MW: $1.30 vs $27.95). It only
looks steeper because its argument sits thousands of MW lower, so it is read far
down its own tail.

## 4. Why this also explains the lane's three previous repairs

`ercot_multiproduct_as` is `K` with three adjudicated legs — netting (ercot-212),
the published `(VOLL − λ)` anchor (ercot-213) and counterpart decontamination
(ercot-215) — and each was **REJECTED-AS-ARMED on a tail or spurious-hour gate**
even though each was, on its own terms, correct. All three repaired the price
**FORM**: what to anchor against, which counterpart to use, which cap binds.
**None touched the ARGUMENT.** On this reading that is why none of them could fix
the tail: the form was being corrected on a curve evaluated at the wrong
quantity, so the hours were still the wrong hours.

This is offered as a coherent account of the lane's history, **not** as a
re-adjudication: no cell verdict moves, and every prior verdict stands as
recorded.

## 5. The lever this names — proposed, NOT armed

**Price the ORDC family off a capability-based reserve argument** — the online
reserve headroom the model already computes for the `ercot_reserve_supply_cap`
(whose whole construction is a measured RTOLCAP comparison, so the quantity is
already in hand) — instead of cleared-to-requirement `held_mw`.

Not armed, and not proposed for arming this session. Under rule 29 it owes a
PRECOMMIT, a zero-LP phase 0 sizing the response on the committed sidecars, ONE
screen year chosen where its own footprint is largest (**not** where the residual
is), STOP-only gates never read against C3a/C3c, the keeper's committed bundle as
the control under a G-DRIFT audit, and deletion of the screen bundle before merge.

**Matrix check performed (rule 26(a)):** `ordc_scarcity_overlay` is `R`;
`ercot_multiproduct_as` is `K` with the three legs above; the published two-basis
form (ercot-213 increment (c)) remains **NOT BUILT**. The argument substitution is
adjacent to that increment but distinct from it — two-basis is about *which
bases* are summed, this is about *what quantity* the curve reads — and it
re-tests no cell marked `R`/`I`/`G`. **No cell is edited by this FINDING**; the
ERCOT shard gains an evidence citation only.

## 6. Honest limits

1. `held_mw` and RTOLCAP are compared **as each curve's own argument**, which is
   the point, but they are not two measurements of one quantity — no claim is
   made that the model's held reserve "should equal" RTOLCAP.
2. The reserve-supply cap is armed in all three keeper years, so `held` is already
   capped at RTOLCAP; it sits far below the cap because the requirement, not the
   cap, is what binds. The cap is doing its job and is not implicated.
3. 2025 is the weakest year in every direction — 648 uncovered measured hours, a
   published maximum ($414.12) landing in the ≥12,000 MW reserve bin where no
   curve should write, and a model that writes only $28.9 all year. The 2023 and
   2024 evidence carries this finding; 2025 is reported, not relied on.
4. Nothing here is identified on, or reads, a held-out year.

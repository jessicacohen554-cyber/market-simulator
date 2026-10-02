# PRECOMMIT closeout-CAISO wave 1, arm 2 (runs second): `caiso_zonal_gas_basis` full span, rule-14 fidelity arm (2026-10-02)

Written before any solve. Plan §3.7 step 2; owner ruling R-14 ("`zonal_gas_basis` 2021 carve-out accepted as rule-28
new evidence … two sequential full-span arms with the 2024 and C4-2025 tripwires"). Phase 0:
`FINDING-closeout-caiso-w1-phase0-2026-10-02.md` §2. **SOLVES HELD** until the W0 foundation lane
(`claude/closeout-b-w0-foundation`) merges and the desk releases this lane.

## 0. Phase-0 verdict, and the desk ruling that follows from it

The charter's pre-fixed reading for step 0c was **≥ 2 pp projected on C3a 2021**. Measured: **+0.01 pp**. The mechanism
is the shared mean-zero capacity-weighted core, so NP15 −0.49 $/MMBtu is paid for by south +0.41. The load-weighted λ
moves $0.00/MWh on the gated months. The route this arm was chartered for (C3a 2021 +12.5 % → ≤ +10 %) is **closed at
zero LP**.

**Desk ruling (2026-10-02, after the W0 merge `306f2c00`).** Arm 2 still runs, as the owner ruled under R-14 ("two
sequential full-span arms"). It runs **second, after arm 3**, and is declared as follows:
- It is a **rule-14 fidelity arm with NO gate claim.** CAISO's zones buy at two separately traded citygate hubs, and
  the model prices both off one composite. Phase 0 shows the arm delivers that N–S gradient (NP15 −1.5 to −2.8 $/MWh,
  south +0.6 to +2.5 in 2021). No C3a, C1 or C4 closure is claimed for it, in this PRECOMMIT or in its RESULT.
- **Its only kill rules are the two tripwires:** C3a 2024 (+1.5 pp) and C4 2025 (NRMSE 0.30).
- It promotes on structure only if nothing regresses (§5).

**Zero-LP preflight on release.** The 0c sizing above was taken on the pre-W0 fleet. On 306f2c00 the 2021 fold
recipe builds 1,767 units, not 1,633, and the applied 2021 spread is −0.52 / +0.38 $/MMBtu. Before any arm-2 shard
launches, 0c and the 2024 tripwire are re-sized with `scripts/probes/_closeout_caiso_w1_basis_tail.py basis` on the
**control's own P0 sidecars**: arm 3's keeper if it was promoted, else the post-W0 CAISO keeper. The readings are
recorded in this file's addendum. A 2024 projection above +1.5 pp stops the arm at zero LP.

## 1. Mechanism, driver, forward story (rule 13)

- `caiso_zonal_gas_basis` (`data/fuel/basis/caiso.py`): every in-CAISO gas unit's delivered price moves by its zone's
  measured citygate basis vs Henry Hub (`data/raw/caiso_zonal_gas_hub.csv`; PG&E Citygate for NP15/ZP26, SoCal
  Citygate for LA_BASIN/SDGE/SP15_rest; month-balanced weekly Wednesday prints), minus the gas-pmax-weighted mean.
- Measured, year-varying, no fitted scalar. Backcast-only: there are no hub rows in forward years, and the registry
  basis carries the forecast.
- Applied spreads ($/MMBtu, north / south): 2021 −0.492 / +0.410; 2024 **+0.286 / −0.253** (sign reversed); 2025
  −0.097 / +0.087. 2019 has no table row, so the flag is a no-op there (`_zonal_gas_basis_by_zone` returns None). 2020
  carries −0.161 measured N−S.
- Rule 19: one mechanism per phenomenon. The arm adds no layer. It replaces one composite with two measured hubs at
  the same aggregate level.

## 2. Exact config delta

- One field: `--set caiso_zonal_gas_basis=true`. Nothing else moves.
- Recipe (control): **arm 3's keeper if arm 3 promoted, else the post-W0 CAISO keeper** (W0 step 4). Arm 3 runs
  first (desk ruling, §0).
- Not the incumbent `rcaiso20_A_span` / `rcaiso20_A_tp_2019_2021`. HEAD's EIA-860 Final 2025 swap (#7015) changes
  the 2025 fleet by 83 units, which is LIVE (FINDING §4), so the incumbent bundle cannot be the control for an arm
  solved on HEAD.

## 3. Shards (rules 32, 34, 36)

Seven shards, one per year 2019–2025, pinned to the full 40-char release SHA. The parent never solves.

```bash
SHA=<release SHA, full 40 chars>
python3 scripts/shard_prompt.py --iso CAISO --all-years --sha $SHA --lane closeout-caiso-w1-a2 \
    --bundle results/calibration/<post-W0 CAISO span> --set caiso_zonal_gas_basis=true \
    --note "closeout-caiso-w1 arm 2: measured zonal citygate basis (R-14)"
python3 scripts/shard_prompt.py --iso CAISO --all-years --sha $SHA --lane closeout-caiso-w1-a2 \
    --bundle results/calibration/<post-W0 CAISO fold> --set caiso_zonal_gas_basis=true \
    --note "closeout-caiso-w1 arm 2: measured zonal citygate basis (R-14)"
```

- Extra hard stop per shard (THE ARM): the solve log must print `CAISO zonal gas basis (<year>)` with the spread pair
  above. 2021: `−0.49..0.41`; 2024: `−0.25..0.29`; 2025: `−0.10..0.09`.
- 2019 prints nothing (no table row). Its bundle must be byte-identical in class TWh to the baseline's 2019 leg.
- Compose with `scripts/probes/_miso260_compose_span.py`, score with `calibration_verdict.py` +
  `legitimacy_diagnostics.py`.
- G-DRIFT at release (rule 29(b)): classify every hunk between the baseline bundle's `basis_sha` and the release SHA
  on the CAISO backcast path. Any LIVE hunk earns a same-SHA control span before this arm is read.

## 4. Pre-fixed readings (first-order, P0 marginal set; FINDING §2)

| Gate | Baseline (incumbent) | Projected Δ | Bar |
|---|---|---|---|
| C3a 2021 | +12.5 % FAIL | +0.01 pp | **report only, no gate claim** (fidelity arm, §0) |
| **C3a 2024 tripwire** | +4.7 % | **+0.43 pp** | **KILL if Δ > +1.5 pp** |
| **C4 2025 tripwire** | NRMSE 0.288 | ±0.09 $/MMBtu spread, ~±1 $/MWh on the gas stack | **KILL if NRMSE > 0.30** |
| C3a 2022/2023/2025 | +8.6 / +6.3 / +6.6 % | not sized (2025 not sizeable on HEAD vs the keeper fleet) | no new FAIL |
| C3b, C1, C2, C8 | PASS (2022–25) | N–S re-dispatch only | no new FAIL; C8 CC_REGULAR ≤ 30 % |
| 2019 | baseline | 0 (no basis row) | byte-identical class TWh |

## 5. Decision rule (pre-registered; desk ruling 2026-10-02)

- **KILL** (no promotion, RESULT + matrix cell R): either tripwire fires. These are the arm's only kill rules.
  - C3a 2024 rises more than +1.5 pp over the control.
  - C4 2025 NRMSE exceeds 0.30.
- **PROMOTE on structure** (rule 1 / rule 14: a structurally real measured input stays even when the fit is neutral)
  only if nothing regresses against the control:
  - no gate in any scored year moves from PASS to FAIL or CAVEAT;
  - the span keeper stays CALIBRATED with no new caveat;
  - both tripwires hold;
  - 2019 is byte-identical.
- **Otherwise**, if a non-tripwire gate regresses, do not promote. The RESULT carries the regression to the owner as
  a card; it is not a kill.
- The fold's determination is reported. No C3a/C1/C4 improvement is claimed or credited.
- Rule 21: zero free parameters added; the DOF ledger is unchanged.

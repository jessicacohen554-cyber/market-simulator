# PRECOMMIT R-CAISO-16 — interchange lag under `caiso_eia930_clock_repair` (2026-09-30)

Owner card 2026-09-30: next link = "Interchange lag". Handoff: `docs/handoffs/r-caiso-15/HANDOFF-r-caiso-16.md`.
Written after phase 0 (zero LP) and before any shard is launched.

## 1. Phase 0 result — neither (a) nor (b) as posed

Probes (zero LP, measured inputs only, rule 23):
- `scripts/probes/_rcaiso16_interchange_lag.py` → `phase0-feed-lag-scan.csv`
- `scripts/probes/_rcaiso16_ti_vs_tac.py` → `phase0-ti-vs-tac.csv`

**1a. The per-DIBA feed IS the extract's `Total interchange`.** On the pinned read-seam clock
(`_CAISO_INTERCHANGE_LAG_STD_H=1` / `_DST_H=2`), Σ legs equals the extract TI to < 1 MW:

| Reference | Window | Best lag (both regimes) | Exact-match share at best lag |
|---|---|---|---|
| REF-U extract TI unrepaired | 2019–2022, 2023 pre-window | 0 | 0.97–1.00 |
| REF-U extract TI unrepaired | IN window, 2023–2025 | 0 | 1.000 |
| REF-R extract TI **repaired** (R-CAISO-15 arm) | IN window, 2023–2025 | **−1** | 1.000 (lag-0 share ≤ 0.002) |
| REF-R extract TI repaired | outside window | 0 | 0.97–1.00 |

So the pinned lags are right in every regime and window. The feed differs from the repaired reference
only because the repair moved TI.

**1b. The independent clocks say TI is NOT late; NG is.**

*OASIS SLD TAC regression.* The model is d(TAC) ~ d(NG shifted j) + d(−TI shifted k), where +1 means published
1 h late. Values are R².

| Year / window | (0,0) | NG+1, TI 0 | NG+1, TI+1 |
|---|---|---|---|
| 2023 pre | **0.968** | 0.564 | 0.746 |
| 2023 IN | 0.288 | **0.784** | 0.452 |
| 2024 IN | 0.479 | **0.979** | 0.701 |
| 2025 IN | 0.365 | **0.958** | 0.621 |

*Counterparty mirrors.* BPAT, PACW and NEVP file their own `diba == CISO` legs, read on an honest Pacific clock
with no correction. They match CISO's legs at **lag 0**, exact share 0.99–1.00, inside the window and on both
sides of its edges (2023 pre, 2023 IN, 2024, 2025 IN, 2025 post).

R-CAISO-13's `d(NetGen − TI)` vs TAC test saw the NG half. The generation family wrongly included
`Total interchange`.

**1c. Consequence in the keeper.** Two seams shift TI 1 h early inside `2023-11-01 08:00 .. 2025-12-02 22:00` UTC:
the frame seam and the caiso-80 demand term (`NetGen − NG_cell − TI`). The demand error is −ΔTI each hour. It
nets to zero energy (|net| ≤ 0.004 TWh/yr) but has a systematic diurnal shape.

| Year | In-window h | mean \|err\| MW | p95 MW | max MW | hod-mean err, 05–08 PST | hod-mean err, 15–16 PST |
|---|---|---|---|---|---|---|
| 2023 | 1,465 | 443 | 1,500 | 3,854 | demand low by 0.1–1.2 GW | high by 0.5–1.3 GW |
| 2024 | 8,760 | 525 | 1,625 | 4,526 | low by 0.6–0.9 GW | high by 1.0–1.2 GW |
| 2025 | 8,054 | 569 | 1,822 | 5,273 | low by 0.8–1.1 GW | high by 1.2–1.5 GW |

Independent-clock check of the demand itself: hourly steps vs OASIS TAC, in-window.

| Year | Series | corr(dD, dTAC) | RMSE(dD − dTAC) MW |
|---|---|---|---|
| 2024 | keeper (TI shifted) | 0.641 | 1,068 |
| 2024 | **fix (TI unshifted)** | **0.806** | **710** |
| 2025 | keeper (TI shifted) | 0.500 | 1,313 |
| 2025 | **fix (TI unshifted)** | **0.673** | **924** |

**Owner card 2026-09-30:** "Narrow the repair (Recommended)".

## 2. The build (rule 14 source repair, rule 19 same flag, zero parameters, frozen inputs untouched)

- `data/eia930/frames.py::_CISO_CLOCK_FAMILY_COLUMNS["generation"]` becomes `NG: *` + `Net generation`.
  `Total interchange` is dropped.
- `data/eia930/demand.py::_supply_consistent_eia930_term` becomes `NetGen − NG_cell`. The TI term stays on its
  own clock.
- No other seam carries TI: the HSL generation term, the battery envelope and the benchmark e930 NG cells are
  unaffected. The benchmark `interchange` series now follows the frame, which is correct.
- Off path: byte-identical. `_repair_clock_late_windows` returns the same object when unarmed.
- Tests: `tests/unit/data/test_caiso_eia930_clock_repair.py`.
  - The window test now asserts that TI is unmoved.
  - New unit test: the caiso-80 term excludes TI.
  - New live test: armed frame TI is byte-identical to unarmed, and still equals the feed on the pinned
    clock (> 99 % of hours within 1 MW).
- **Census row #2 (per-DIBA feed): CLOSED — correct by measurement.** No reader change.
- **Census row #3 (DSW clean-depth / surplus / wedge / import-tranche constants): CLOSED — none move.**
  They read the feed through `_caiso_interchange_model_clock`, and the feed is on the true clock.
- Cache key: no field or registered constant value changes, so the key is unchanged. This follows the
  R-CAISO-15 seam precedent. Provenance is the pinned SHA in every leg's `run_config.json` `git`.

## 3. Arm-liveness hard stop (per year, at the build)

Fields: Demand · NG: SUN · caiso-80 · HSL solar · HSL wind · Total interchange (the count of frame-column or
series hours that differ, armed vs unarmed).

| Year | Output |
|---|---|
| 2019 / 2020 / 2021 | `0 0 0 0 0 0` |
| 2022 | `4776 0 0 0 0 0` |
| 2023 | `8752 1140 1466 1140 1454 0` |
| 2024 | `8758 7666 8753 7664 8743 0` |
| 2025 | `8049 6943 8048 6943 8031 0` |

The last field is the discriminator: R-CAISO-15's build reads non-zero there in 2023–25.
The battery envelope stop is unchanged (no TI).

## 4. G-DRIFT: keeper legs `789c70a0` → build

Five non-merge commits touch the solve-path set. All are INERT for a CAISO backcast:

| Commit | Verdict | Reason |
|---|---|---|
| a16e4828 NYISO-NEXT-15 | INERT | `nyiso_import_landing_band`, default off, NYISO-gated |
| 3901ae61 PJM-NEXT-13 | INERT | `pjm_replacement_cost_fuel`, default off, PJM-gated; PJM reference tables |
| 2386952f R-ERCOT-17 | INERT | pooled South-Texas basis, default off, ERCOT-gated |
| 853ff96f NYISO-NEXT-13 | INERT | forecast parity registry declaration only |
| 431bbb16 R-CAISO-15 | INERT for the solve | zero-LP benchmark rebuild, already how the incumbent was scored |

**Prediction:** the 2019–2022 legs reproduce the incumbent's committed legs. The change is inert there by
construction, since the generation window opens 2023-11-01.

## 5. Solve plan (rule 36, the parent never solves)

- Seven shards, one per year 2019–2025, from `docs/handoffs/r-caiso-16/shard-prompt.md`.
- Pinned to the full SHA of this lane's build merge.
- `{SRC}` = `rcaiso15_A_tp_2019_2021` (2019–21) / `rcaiso15_A_span` (2022–25).
- Out-dirs `rcaiso16_A_{Y}`, branches `claude/r-caiso-16-A-{Y}`.
- The recipe is the keeper recipe unchanged (the arm is already `true`). Only the code differs.

## 6. Decision rule (pre-registered)

Promote on structure (rule 14) iff all three hold:
1. **2022–25 stays CALIBRATED** under the rubric at HEAD, with the ledger budget as the incumbent's.
2. **The repair is complete for TI.** The hard stop's TI field reads 0 in every year, and no remaining TI reader
   under the flag is shifted.
3. **The 2019–2022 legs reproduce the incumbent.** Max |Δ class TWh| ≤ 0.01 per year versus the committed
   incumbent hourlies. Otherwise the drift is investigated before any promotion.

Any other outcome, for example 2022–25 falling to NOT-YET, goes to the owner as a decision card.

Reported, never a criterion (rule 1):
- C3a, C3b and C4 movement in 2023–25;
- the in-window hod demand profile;
- the fold's (2019–21) determination (rule 30(c)).

## 7. Open observation, not acted on (outside this lane's scope)

On the TAC regression, 2019–2021 (outside any registered window) prefer NG −1 h / TI 0 or NG 0 / TI +1 over
(0,0): 2021 R² 0.826 / 0.803 vs 0.736. The evidence is weaker (R² ≤ 0.83) and possibly a TAC-file clock
artifact. It is recorded as a candidate next link, not built.

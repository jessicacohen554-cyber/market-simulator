# FINDING caiso-289 — the blackout bridge's evidence was re-measured on the repaired series; it survives, its footprint collapses, and the flag turns out to carry a SECOND mechanism nobody declared

**Lane:** CAISO calibration · **Date:** 2026-09-20 · **ZERO LP** (rule 32
`[R-SHARD]` (a): the parent never solves — and this session launched no shard either, because
every question below is arithmetic over committed artifacts).
**Keeper untouched:** `2026-09-20-caiso-288-citygate-recovery` is not re-solved, re-scored or
re-registered by this session. **No solve-affecting line was changed.**

Harness: `scripts/probes/caiso288_blackout_census.py` (extended in place, as the handoff
directed, rather than writing a third probe) → `results/calibration/_caiso289_postrepair_audit.json`.

---

## 0. The answer in one paragraph

caiso-288 recovered **85 published citygate prints** and promoted the keeper on them. That
repair silently invalidated the evidence base of the *sibling* lane's mechanism,
`ScenarioConfig.caiso_citygate_blackout_bridge` (PR #6371, merged, default off), because both
of its identification gates had been measured on the unrepaired series. Re-running them:
**both verdicts survive and every number moves.** But the footprint audit that the repair made
possible returns something neither lane looked for — **the single flag moves two independent
things**, and in 2022 and 2023 the one it moves is *not the bridge*. It is an undeclared switch
of the year-start left-edge convention in `_flow_date_staircase`, worth **−$62.12/MWh of CC
marginal cost over 72 hours in 2023**, through a code path shared with MISO. The bridge itself
is now **inert in 2022 and 2023** and reaches only the two Thanksgiving weeks caiso-288's G-DUP
guard deliberately refuses.

---

## 1. G-FILL re-run: the construction still wins, on 3,382 more withheld days

The synthetic holdout — every fully-measured 8 / 12 / 15 / 19-day window, interior withheld,
each construction scored against the withheld truth — grows **33,216 → 36,598** withheld
measured citygate days. Rule 23 `[R-FROZEN-DERIVE]`: this re-derivation is cited to a
**source-data change** (+85 prints) and to no residual.

| construction | MAE | bias | RMSE | p95\|e\| |
|---|--:|--:|--:|--:|
| (a) hold-last (current behaviour) | 0.796 | +0.040 | 2.596 | 2.200 |
| (b) linear interpolation | 0.574 | +0.034 | 1.999 | **1.508** |
| (c) **HH-basis (the mechanism)** | **0.531** | **+0.019** | **1.898** | 1.517 |

HH-basis still wins on MAE, bias and RMSE **at every gap length** (8/12/15/19 individually) and
on the spike case — left anchor in the series' top decile, where hold-last's systematic high
bias is **+0.907 $/MMBtu** (MAE 3.376) against HH-basis's **+0.221** (MAE 1.997).

**Reported against the mechanism** (rule 1 `[R-STRUCT]` — a real result that doesn't flatter it
is still the result): on **p95|e| it is now marginally BEHIND linear interpolation**, 1.517 vs
1.508. It wins the body and the bias and ties the far tail. That was not visible pre-repair.

## 2. G-CENSUS re-run: `_GAS_BLACKOUT_MIN_GAP_DAYS = 6` survives, on a different histogram

The probe's docstring has always promised this table; **the code never actually printed it**
until this session, so the figures quoted in `hubs.py` could not be checked against a run. They
can now, and they were wrong — not by anyone's error, but because the series changed underneath
them.

| | gap 1 | 2 | 3 | 4 | 5 | 8 | 9 | 12 | 15 | 19 | **blackouts** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| pre-repair (1,805 gaps) | 1401 | 2 | 312 | 52 | 3 | 17 | 1 | 9 | 7 | 1 | **35** |
| **post-repair (1,890 gaps)** | 1472 | 6 | 325 | 57 | 9 | 13 | — | 5 | 3 | — | **21** |

The verdict is **unchanged and for the same reason**: the histogram is still **empty at 6 and
7**, so thresholds 6, 7 — and now 8, the next occupied bin — select the **identical 21 gaps**.
The value remains non-selectable against any result (rules 1 `[R-STRUCT]`, 5 `[R-NO-MAGIC]`).
Fourteen of the 35 "blackouts" were measurements all along.

## 3. G-FOOT289 — the new gate, and the decision-relevant one

**What the bridge would now touch, armed over the repaired series.** 19 of the 21 remaining
blackouts are **2018–2020**, outside every scored CAISO year. Only two fall in a scored year,
and they are exactly the pair caiso-288's **G-DUP guard refuses** (EIA re-served 2024's
Thanksgiving table verbatim under 2025 dates, so neither can be told from the other):

| year | (A) bridge-interior days | mean $/MMBtu | implied CC mc | (B) left-edge days | mean $/MMBtu | implied CC mc |
|---|--:|--:|--:|--:|--:|--:|
| 2022 | **0** | — | — | 3 | +1.430 | **+$10.64/MWh** |
| 2023 | **0** | — | — | 3 | −8.350 | **−$62.12/MWh** |
| 2024 | 11 | +0.198 | +$1.47/MWh | 2 | −0.470 | −$3.50/MWh |
| 2025 | 11 | +0.391 | +$2.91/MWh | 2 | −0.220 | −$1.64/MWh |

**This retires the scoreboard's adjudication as a guide to arming.** `_caiso288_blackout_
scoreboard.json` scored the bridge over the **14 recoverable** blackouts (MAE 1.513 vs the
staircase's 3.354; losing to the naive staircase in 4 of 14). Every one of those 14 gaps is now
**measured**, so the armed bridge never touches them. The "systematic high bias where the
residual lives" and the "loses 4 of 14" both describe a footprint the flag **cannot have**. The
honest post-repair evidence for the construction is §1's synthetic holdout, not the scoreboard —
and the scoreboard's real finding stands unchanged and unarguable: **recovery beat estimation,
0.000 against 1.513.**

## 4. THE FLAG CARRIES TWO MECHANISMS, AND ONLY ONE IS DECLARED

Column (B) above is not the bridge. It is a **year-start left-edge convention switch**, and it
fires in every year with a January gap whether or not a blackout is anywhere near.

`_flow_date_staircase` (`data/fuel/hubs.py`) has two branches:

* **unbridged** — reindexes on **one year's** stamps, then `.ffill().bfill()`. Flow days before
  the year's first print take the year's **first January trade**, by back-fill.
* **bridged** — reindexes on the **full multi-year** series (it must, to bracket a December
  blackout against the next January), so those same days **forward-fill from the previous
  December's last trade**.

The docstring asserted the bridged array "is byte-identical to the unbridged one in any year
whose gaps are all packages." **That is false**, and 2022/2023 are the counterexample: both
carry no blackout at all post-repair, and both still move three days. Corrected in place.

**It is not a wash — the back-fill is the artifact.** On the repo's own documented flow-date
convention (a trade on T prices flow on T+1; Friday's trade covers the holiday-extended
weekend package), flow day 2023-01-01 was priced by the **2022-12-30 trade at $15.31**. The
unbridged branch instead assigns it the **2023-01-03 trade at $23.66** — a trade that had not
yet happened and that prices 2023-01-04's flow:

| year | last Dec trade (ffill, bridged) | first Jan trade (bfill, unbridged) | Δ |
|---|--:|--:|--:|
| 2022 | 2021-12-30 = 7.09 | 2022-01-03 = 5.66 | +1.43 |
| **2023** | **2022-12-30 = 15.31** | **2023-01-03 = 23.66** | **−8.35** |
| 2024 | 2023-12-29 = 2.98 | 2024-01-02 = 3.45 | −0.47 |
| 2025 | 2024-12-31 = 2.90 | 2025-01-02 = 3.12 | −0.22 |

So the model currently burns gas at **$23.66/MMBtu on 1–3 January 2023**, set by a
look-ahead print, when the trade that actually priced those flow days printed **$15.31**. That
is a rule 14 `[R-ACCURATE]` construction defect of exactly the caiso-288 class — found on the
source convention, not on a residual.

**Stated so it cannot be mistaken for a motive:** CAISO's 2023 C3a residual is **+3.796 %**
(model high), and correcting this would push gas *down* at the start of 2023 — i.e. the right
way. That is an **outcome, not the reason**, and it is not why this is being reported. The
reason is that the construction contradicts the repo's own stated flow-date semantics. Per rule
1 `[R-STRUCT]` the direction of the residual is not evidence either way.

### Why this lane did not fix it

`_flow_date_staircase` is **shared**: `data/fuel/basis/miso.py` builds both the MISO citygate
and the Chicago daily series through it, and `scripts/data/derive_miso_gas_variable_transport.py`
calls it too. Correcting the left edge is therefore a **cross-ISO, solve-affecting** change that
would move MISO's keeper as well as CAISO's. A CAISO lane does not get to make that call
unilaterally — it is routed, not taken. **Nothing in this session changes solve behaviour.**

## 5. A seventh pre-existing test failure, now repaired

The handoff lists 6 pre-existing failures on clean main. There is a **7th**:
`tests/iso/caiso/test_caiso288_blackout_bridge.py::test_bridge_moves_december_2022_down_and_
november_2022_up`, failing with `assert np.float64(0.0) < -1.0`.

It fails **for the correct reason**: it asserts December 2022 falls >$1/MMBtu under the bridge,
and post-repair those days are measurements, so the delta is exactly 0.0. The sibling lane wrote
it against the unrepaired series and the recovery landed after it merged.

Replaced (not restored — rule 26 `[R-DELETE]`) by `test_december_2022_is_measured_not_bridged`,
which pins the opposite and says why, plus two new guards:
`test_the_flag_also_switches_the_year_start_left_edge` (pins the §4 confound so it cannot be
silently "fixed" as a bridge regression) and
`test_bridge_is_inert_in_2022_and_2023_over_the_repaired_series` (pins §3's footprint). All 7
pass.

## 6. What changed on disk

Documentation, tests and one probe. **No solve-affecting line**, no `ScenarioConfig` default, no
constant, no threshold, no offer-curve multiplier; the DOF ledger is untouched at 9/6 and no
registered run's score moves.

* `scripts/probes/caiso288_blackout_census.py` — G-CENSUS now prints the histogram its docstring
  always promised; G-FOOT289 added; JSON sidecar emitted.
* `src/market_sim/data/fuel/hubs.py` — histogram block, `_basis_bridge_blackouts` G-FILL figures
  and `_flow_date_staircase`'s false byte-identity claim, all restated with provenance.
* `src/market_sim/config/scenarios.py` — the field comment's stale 35-gap / 33,216-day / Dec-2022
  evidence restated, and the confound named at the gate.
* `tests/iso/caiso/test_caiso288_blackout_bridge.py` — §5.
* `docs/codebase-site/data/mechanism-matrix/CAISO.js` — cell `O` → `I` (rule 28 `[R-MECH-MATRIX]`
  duty b).

## 7. OPEN — for the owner

1. **The left-edge repair (§4).** Cross-ISO and solve-affecting: CAISO **and** MISO. Worth
   −$62.12/MWh of CC marginal cost over 72 h of 2023 on the CAISO side alone; MISO's exposure is
   unmeasured. Route it as its own object, or leave it documented and inert?
2. **`caiso_citygate_blackout_bridge` (§3).** Post-repair it is worth ~11 days each in 2024/2025
   and nothing in 2022/2023. Recommendation: **do not arm it for CAISO price work** until the
   §4 confound is separated out — otherwise arming a CAISO mechanism silently buys a shared
   convention change. The construction itself is sound (§1) and the field can stay default-off
   on main at no cost.
3. **Still unruled from caiso-286/287/288:** `results/calibration/caiso279_ablate_dswcouple_span`
   is a CAISO parity RED on main (34 committed files, unmapped to any sidecar). One
   `prune_iso_runs.py` call. Four sessions have now asked.
4. **Still unruled:** the `caiso_ra_bridge_startup_aware` 42–60 % drop-rate admissibility
   question (caiso-287 §5) — a rules 1/13 question, not a lane's to decide.

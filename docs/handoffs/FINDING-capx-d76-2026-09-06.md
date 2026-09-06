# FINDING — capx D76 phase 0: the capacity-screen seam peak is synthesized in **every** hindcast year of **every** ISO, the census measures it at −23.3 % to +15.4 %, and the six screen years are fixed

**Lane:** capx D76 (director r#47, re-emitted after never being dispatched). Branch
`claude/capx-d76-peak-census-fjw289`, fresh off `origin/main` `131291b5`.
Charter: pack §D76 + `FINDING-capx-d67-2026-09-06.md` §2.2 (the mechanism) and §8(a) (the route).
**PHASE 0 IS ZERO LP AND IS THE WHOLE LANE.** Nothing is armed, no config changed, no solve run;
every number below is read from committed artifacts or computed from demand arrays and the shipped
resolvers. Instruments: `docs/handoffs/d76/peak_census.{py,json}` and
`docs/handoffs/d76/i7_i12_reading.{py,json}`, both zero-LP, plus the D67 probe
`docs/handoffs/d67/gdrift_peak_probe.py`, **extended in place** (charter: "extend, do not fork") with
the seam helpers this census imports — its own committed `gdrift_peak_probe.json` re-derives
**byte-identically** after the refactor, verified by diff.
DATA PROFILE: `code` was declared; `data/raw` was already hydrated in this container, and the census
needs the demand arrays (six ISOs × 2021–2027) to reproduce the seam.

---

## 0. Verdict in one paragraph

**The predicate holds exactly as issued, and it is worse than the PJM case that surfaced it.** The
capacity screens' peak is built on the GROWTH path at the top of `runner.py`'s year loop
(lines 2029-2031) while the LP takes the measured hindcast branch 500 lines later (line 2540), so in
**every** hindcast year that is not the weather year the screens test a synthesized peak against
which the same year's LP dispatches a different, measured load. Across the six bare T1-H recipes the
gap runs **−22,702 MW (−15.18 %) to +12,886 MW (+15.42 %)**, and on the T1-X crossover recipes
**−19,721 MW (−23.31 %) to +2,495 MW (+8.61 %)** — every ISO, every non-weather year, no exceptions;
ERCOT's 13.48 %/yr near rate makes it the largest proportional offender and PJM's the largest
absolute. The requirement error tracks it almost exactly (**−24,741 MW to +13,808 MW**) in four of
six ISOs; **NYISO is already requirement-moot at HEAD** — not by D67 but by the D52 gates
`nyiso_requirement_forecast_peak` / `nyiso_requirement_vintage_factors`, which `_nyiso_config` arms
by default, giving a measured **0.0 MW** requirement delta in every year against peak deltas of
1.6–2.9 GW. **D67 moots nothing at HEAD**: Q52 ruled ARM but the arming leg has not landed —
`capacity_adequacy_requirement_published_by_iso` resolves `None` on `main` — and once it does it
moots the REQUIREMENT for **PJM only**, in all five in-table delivery years. The peak still reaches
the floor, the backstop, the entry screen, the accreditation census and the CR-1 position in every
ISO regardless (§4). **The HIT/MISS reading is mostly MISS and is reported as such**: 2 HIT / 7 MISS
over the nine gradable ISO-years, with three ISOs `UNOBSERVABLE` because their frontier bundles
predate the D52 screen-ledger fields — and the reason is instructive rather than exculpatory. In
2023/24 the fleets sit 2.3–13.8 GW **above** requirement, so a 3.8–17.2 GW cumulative bar
understatement is absorbed by slack and never surfaces as a position failure. In the one observable
year where the slack is exhausted — **PJM 2025, I7 FAIL by 2,841 MW on a −14,759 MW cumulative seam
error** — the sign matches. The defect is therefore real everywhere and *board-visible* almost
nowhere yet, which is an argument for repairing it before it is load-bearing, not after.

**A second gap, surfaced not absorbed:** the charter asks whether the delta's sign matches "the FC-1
I7/I12 residual **on the board**". There is no such residual. **FC-1 reads `SKIPPED` — "no committed
invariant record" — on all 49 T1-H entries in `frontend/data/forecast/ff-verdicts.json`, all six
ISOs.** Every I7/I12 number in §3 is reconstructed here from the bundles' own committed ledgers with
the shipped checker's own imported thresholds. Whether that is worth closing is the director's call;
it is named here rather than papered over.

---

## 1. The predicate, VERIFIED (not discovered)

The charter states the predicate as a precondition of issuing. It was verified against the code
before anything else was done, and reproduced numerically.

**(a) The two demand paths, in `runner.py`.** At the top of the year loop:

```python
# runner.py:2029-2031  — the CAPACITY-SCREEN seam, growth path, ALWAYS
year_demand = _scale_demand(base_demand, wx_config, year)
year_demand = add_load_layers(year_demand, config, iso, year, zone_names)
peak_demand = float(year_demand.sum(axis=0).max())
```

and 500 lines further down, after the fleet has already evolved against that peak:

```python
# runner.py:2537-2548  — the LP's own basis, measured in a hindcast
if config.hindcast and not config.is_crossover_forward_year(year):
    year_demand = year_base_demand          # load_demand(iso, YEAR, ...) — measured
else:
    year_demand = _scale_demand(base_demand, wx_config, year)
    year_demand = add_load_layers(year_demand, config, iso, year, zone_names)
peak_demand = float(year_demand.sum(axis=0).max())
```

**(b) `_scale_demand` de-grows.** `runner.py:459-470`: for `year < config.weather_year` it returns
`base_demand / Π(1 + rate)` over `[year, weather_year)` — the deliberate FH-2 backward branch, which
warns and proceeds. It is a pure scalar on the whole array, so the seam peak is exactly the weather
year's measured peak times the compounded factor.

**(c) The recipe resolution that arms it.** `run_capacity_hindcast.build_config` (lines 780-791):
a plain hindcast keeps `ScenarioConfig().weather_year` = **2024** and a crossover pins
`CROSSOVER_FORWARD_YEAR - 1` = **2025**; both set `demand_growth_vintage = None` and
`solve_year_weather = False`. Measured on all six ISOs (`peak_census.json`): `weather_year` 2024 /
2025, `demand_growth_vintage` `None`, `crossover_solve_year_weather` `False`, `hindcast` `True` —
**the director's r#46 census confirmed, ISO by ISO, at HEAD.**

**(d) The D67 numbers reproduce.** The extended probe re-run at HEAD returns PJM
−10,818.907 / −7,573.683 / −3,976.665 / **0.000** / +4,386.151 MW against the committed D57 arm A,
digit for digit, with the 2024 row at 0.000 MW as its own faithfulness check, and
`gdrift_peak_probe.json` unchanged byte for byte.

**(e) The screens do not bind in the window's first year.** `runner.py:2125` guards the
requirement/position block on `prior_results is not None`, so 2021 (t1h) / 2023 (t1x) writes a
`screen_peak_demand_mw` no screen consumed. Confirmed in every committed D52-era ledger:
2021's `screen_adequacy_requirement_mw` is `null`. The binding years are **2022-2025** (t1h) and
**2024-2027** (t1x), and the census marks them.

---

## 2. The census — six ISOs, both recipe shapes, at HEAD (zero LP)

`docs/handoffs/d76/peak_census.py`. "seam" is `runner.py`'s screen peak; "measured" is the same
`load_demand(iso, year, …)` call the LP's hindcast branch makes; "req Δ" is
`resolve_adequacy_requirement_mw` at HEAD on the seam peak minus the same resolver on the measured
peak — the operand error the screens actually consumed. "binds" is (e) above.

### 2.1 Bare T1-H (`weather_year = 2024`, `--vintage 2020`, 2021-2025)

Near-term growth rate read at HEAD, per ISO: CAISO **3.2425 %**, ERCOT **13.4813 %**,
MISO **5.4816 %**, NEISO **0.7446 %**, NYISO **1.1815 %**, PJM **6.4645 %**.

| ISO | year | seam peak MW | measured MW | Δ MW | Δ % | req Δ MW | binds |
|---|---|---:|---:|---:|---:|---:|---|
| CAISO | 2021 | 43,228 | 43,615 | −387 | −0.89 % | −445 | no |
| CAISO | 2022 | 44,630 | 51,104 | **−6,474** | **−12.67 %** | −7,445 | Y |
| CAISO | 2023 | 46,077 | 44,007 | +2,070 | +4.70 % | +2,380 | Y |
| CAISO | 2024 | 47,571 | 47,571 | **0** | 0.00 % | 0 | Y |
| CAISO | 2025 | 49,113 | 43,860 | **+5,253** | **+11.98 %** | +6,042 | Y |
| ERCOT | 2021 | 58,163 | 72,776 | −14,613 | −20.08 % | −15,658 | no |
| ERCOT | 2022 | 66,004 | 79,407 | **−13,403** | **−16.88 %** | −14,362 | Y |
| ERCOT | 2023 | 74,902 | 84,617 | −9,715 | −11.48 % | −10,410 | Y |
| ERCOT | 2024 | 85,000 | 85,000 | **0** | 0.00 % | 0 | Y |
| ERCOT | 2025 | 96,459 | 83,573 | **+12,886** | **+15.42 %** | +13,808 | Y |
| MISO | 2021 | 103,576 | 114,226 | −10,650 | −9.32 % | −10,726 | no |
| MISO | 2022 | 109,254 | 116,392 | −7,138 | −6.13 % | −7,189 | Y |
| MISO | 2023 | 115,243 | 120,781 | −5,538 | −4.59 % | −5,578 | Y |
| MISO | 2024 | 121,560 | 121,560 | **0** | 0.00 % | 0 | Y |
| MISO | 2025 | 128,223 | 118,661 | **+9,562** | **+8.06 %** | +9,631 | Y |
| NEISO | 2021 | 23,721 | 25,101 | −1,380 | −5.50 % | −1,419 | no |
| NEISO | 2022 | 23,898 | 24,233 | −335 | −1.38 % | −345 | Y |
| NEISO | 2023 | 24,076 | 23,475 | +601 | +2.56 % | +618 | Y |
| NEISO | 2024 | 24,255 | 24,255 | **0** | 0.00 % | 0 | Y |
| NEISO | 2025 | 24,436 | 25,898 | **−1,462** | **−5.65 %** | −1,504 | Y |
| NYISO | 2021 | 27,986 | 30,919 | −2,933 | −9.49 % | **0** | no |
| NYISO | 2022 | 28,317 | 30,505 | −2,188 | −7.17 % | **0** | Y |
| NYISO | 2023 | 28,651 | 30,206 | −1,555 | −5.15 % | **0** | Y |
| NYISO | 2024 | 28,990 | 28,990 | **0** | 0.00 % | 0 | Y |
| NYISO | 2025 | 29,333 | 31,857 | **−2,524** | **−7.92 %** | **0** | Y |
| PJM | 2021 | 126,888 | 149,590 | **−22,702** | **−15.18 %** | −24,741 | no |
| PJM | 2022 | 135,091 | 148,528 | −13,437 | −9.05 % | −14,604 | Y |
| PJM | 2023 | 143,824 | 147,605 | **−3,781** | **−2.56 %** | −4,122 | Y |
| PJM | 2024 | 153,121 | 153,121 | **0** | 0.00 % | 0 | Y |
| PJM | 2025 | 163,020 | 160,560 | +2,460 | +1.53 % | +2,307 | Y |

The 2024 row is 0.000 MW in all six ISOs by construction (the growth factor is 1 at the weather
year) and doubles as the census's own faithfulness check, exactly as it did for D67.

### 2.2 T1-X crossover (`weather_year = 2025`, `--vintage 2023`, 2023-2027)

| ISO | year | seam peak MW | measured MW | Δ MW | Δ % | req Δ MW | binds |
|---|---|---:|---:|---:|---:|---:|---|
| CAISO | 2023 | 41,148 | 44,007 | −2,859 | −6.50 % | −3,288 | no |
| CAISO | 2024 | 42,483 | 47,571 | **−5,088** | **−10.70 %** | −5,852 | Y |
| CAISO | 2025 | 43,860 | 43,860 | 0 | 0.00 % | 0 | Y |
| ERCOT | 2023 | 64,896 | 84,617 | **−19,721** | **−23.31 %** | −21,132 | no |
| ERCOT | 2024 | 73,645 | 85,000 | **−11,355** | **−13.36 %** | −12,167 | Y |
| ERCOT | 2025 | 83,573 | 83,573 | 0 | 0.00 % | 0 | Y |
| MISO | 2023 | 106,648 | 120,781 | −14,133 | −11.70 % | −14,234 | no |
| MISO | 2024 | 112,495 | 121,560 | **−9,065** | **−7.46 %** | −9,130 | Y |
| MISO | 2025 | 118,661 | 118,661 | 0 | 0.00 % | 0 | Y |
| NEISO | 2023 | 25,517 | 23,475 | +2,042 | +8.70 % | +2,100 | no |
| NEISO | 2024 | 25,707 | 24,255 | **+1,452** | **+5.98 %** | +1,493 | Y |
| NEISO | 2025 | 25,898 | 25,898 | 0 | 0.00 % | 0 | Y |
| NYISO | 2023 | 31,117 | 30,206 | +911 | +3.02 % | **0** | no |
| NYISO | 2024 | 31,485 | 28,990 | **+2,495** | **+8.61 %** | **0** | Y |
| NYISO | 2025 | 31,857 | 31,857 | 0 | 0.00 % | 0 | Y |
| PJM | 2023 | 141,654 | 147,605 | −5,951 | −4.03 % | −6,488 | no |
| PJM | 2024 | 150,811 | 153,121 | **−2,310** | **−1.51 %** | −2,517 | Y |
| PJM | 2025 | 160,560 | 160,560 | 0 | 0.00 % | 0 | Y |

**2026 and 2027 are FORWARD years and carry no defect**: past
`crossover_forward_year` the LP takes the growth branch too (`runner.py:2537`), so both paths are the
same object, there is no measured load to compare against, and the growth path there **is** the
forecast methodology (rule 13's forward test). The census marks them `—` rather than manufacturing a
gap. This is why the phase-1 gate must be hindcast-scoped (§4).

### 2.3 What D67 moots, and what it does not

- **At HEAD, nothing.** `capacity_adequacy_requirement_published_by_iso` resolves **`None`** on
  `main` `131291b5`. Owner ruling **Q52 = ARM for PJM** is served and the D67-ARM leg is ISSUED /
  DISPATCHABLE (`capx-director-ledger-2026-08.md` §3, pack §D67-ARM), but it has not landed, so the
  in-table-moot claim below is prospective and stated as such.
- **Once armed: PJM only, and then completely, for the T1-H window.**
  `RTO_RELIABILITY_REQUIREMENT_MW_BY_ISO["PJM"]` carries 2021/22 (166,355.1), 2022/23 (163,268.9),
  2023/24 (163,166.2), 2024/25 (164,107.6) and 2025/26 (144,450.0) — **every solve year of the
  2021-2025 recipe**. Verified peak-independent by construction: with the gate armed the resolver
  returns the identical MW at a 100 GW and a 160 GW peak in all five years. So D67 removes the "req
  Δ" column of §2.1's PJM block entirely (−24,741 / −14,604 / −4,122 / 0 / +2,307 → all 0). It does
  **not** reach the crossover's 2026/27, where no RR row is published — but those are forward years
  with no defect anyway.
- **No other ISO is in the registry**, so D67 moots the requirement nowhere else.
- **NYISO is already requirement-moot at HEAD, by a different mechanism.** `_nyiso_config`'s
  `default_scenario_overrides` arm `nyiso_requirement_forecast_peak=True` **and**
  `nyiso_requirement_vintage_factors=True`, so the requirement is the published ICAP-market forecast
  peak × the capability year's adopted IRM, and the model's peak drops out. Measured: **req Δ = 0.0
  MW in every NYISO row of both recipes**, against peak deltas up to 2,933 MW. This is a capx D52
  gate, not D67, and it is worth naming because it changes what phase 1 can expect to move in NYISO.
- **The floor and the backstop still read the peak everywhere, PJM and NYISO included.** Mooting the
  requirement removes one of six consumers. The retirement reliability floor, the reserve-margin
  build backstop, the thermal entry screen, the accreditation census (penetration-indexed ELCC and
  the D48 DR-as-supply hold-last) and the CR-1 position all take the seam peak directly. The full
  enumeration is §4.2 — it is the rule-19 list phase 1 owes before it changes anything.

---

## 3. The screen year, fixed; and the HIT/MISS reading

### 3.1 The six screen years — FIXED HERE, before any solve (rule 29 `[R-SCREEN]`)

**Selection rule, declared before it was evaluated:** the screen year is the year of the mechanism's
own largest measured footprint (|Δ| in MW) among years that both (i) **bind** — the screens actually
consume the seam peak, §1(e) — and (ii) **solve**, since 2022 is the T1-H bridge year (evolved,
never solved, its data never read under rule 22) and cannot carry a scoreable non-target check. The
2024 row is 0 by construction, so the choice is between 2023 and 2025. **This is the mechanism's own
footprint, never a residual** — nothing here was selected by looking at a gate outcome.

| ISO | screen year | Δ MW | Δ % | runner-up |
|---|---|---:|---:|---|
| CAISO | **2025** | +5,253 | +11.98 % | 2023 (+2,070) |
| ERCOT | **2025** | +12,886 | +15.42 % | 2023 (−9,715) |
| MISO | **2025** | +9,562 | +8.06 % | 2023 (−5,538) |
| NEISO | **2025** | −1,462 | −5.65 % | 2023 (+601) |
| NYISO | **2025** | −2,524 | −7.92 % | 2023 (−1,555) |
| PJM | **2023** | −3,781 | −2.56 % | 2025 (+2,460) |

**The operational consequence the director should see before releasing phase 1.** The T1-H window
floor is fixed at 2021, so a screen "on year Y" is the invocation `--start-year 2021 --end-year Y`.
For the five ISOs whose screen year is 2025 **the screen IS the full span** (four solves: 2021, 2023,
2024, 2025 — 2022 is the bridge) and rule 29 buys no LP. Only PJM gets a genuine early screen
(2021-2023, two solves, half the span). Two facts bear on any decision to narrow the window, offered
as data rather than as a proposal:

1. The mechanism's **largest** deltas are 2021 (−387 to −22,702 MW) and 2022 (−335 to −13,403 MW),
   and neither is reachable as a scored screen year — 2021 does not bind, 2022 does not solve.
2. A **2021-2023** window nevertheless *exercises* the mechanism at 2022's large delta, because the
   bridge year evolves the fleet against the seam peak even though it never solves
   (`runner.py:2440-2461` writes the bridge's `screen_ledger_fields`). For CAISO, ERCOT, MISO and
   PJM that window carries the two largest binding deltas at half the LP cost, and rule 29's
   structural STOP gate — "the arm's screen peak = the measured peak to the MW; every non-peak
   operand byte-identical" — is checkable on both the 2022 bridge ledger and the 2023 solved ledger.

The screen years in the table are what this lane fixes. Narrowing the window to 2021-2023 for the
four ISOs where it is cheaper is the director's call, and is not made here.

### 3.2 The HIT/MISS reading — 2 HIT, 7 MISS, 3 ISOs unobservable. **Not a gate.**

**There is no board residual to read.** FC-1 is `SKIPPED` — *"no committed invariant record
(summary.invariants / --invariants)"* — on **all 49** `tier: "t1h"` entries in
`frontend/data/forecast/ff-verdicts.json`, all six ISOs, `caiso-t1h` / `ercot-t1h` / `miso-t1h` /
`neiso-t1h` / `nyiso-t1h` / `pjm-t1h` included. The board's I7/I12 rows belong to the **T1-F** runs
(2026-2050), whose solve years are all at or beyond the weather year: there `_scale_demand` runs
FORWARD, the growth path is the methodology, and this defect cannot reach them. So the residual is
**reconstructed** in `docs/handoffs/d76/i7_i12_reading.py` from each ISO's frontier T1-H bundle's own
committed ledgers, using `check_forecast_invariants`'s own `Thresholds`, `FIRM_CLEAN_FUELS` and
`_thermal_mw` **imported rather than restated**, so the reading cannot drift from the gate it
reconstructs. `accredited_firm = peak_demand_mw × (1 + reserve_margin)` against
`adequacy_requirement_mw` — both already committed, both on the MEASURED peak, which is precisely
the mismatch: **the checker grades on the measured peak while the screens built to the seam peak.**

**The predictor is CUMULATIVE, not per-year**, because the mechanism is path-dependent: a unit the
screens released in 2022 against a too-low bar is gone in 2025 too, and a backstop MW not built is
not built. So year Y is graded on `Σ(seam − measured)` over every binding year through Y. Δ < 0 ⇒
the screens tested a bar that was too low ⇒ under-retention/under-build ⇒ predict SHORT (I7 FAIL or
I12 below band). Δ > 0 ⇒ predict LONG.

| ISO | year | Δ MW | cum Δ MW | accredited firm | requirement | I7 slack MW | I7 | I12 | reading |
|---|---|---:|---:|---:|---:|---:|---|---|---|
| CAISO | 2021/23/24/25 | — | — | 44,069 / 53,269 / 55,932 / 56,243 | 50,157 / 50,608 / 54,707 / 50,439 | −6,088 / +2,661 / +1,225 / +5,804 | FAIL / PASS ×3 | BELOW / IN ×3 | **UNOBSERVABLE** |
| ERCOT | 2021/23/24/25 | — | — | 78,895 ×3 / 83,466 | 78,895 ×4 | 0 ×3 / +4,571 | PASS ×4 | n/a (energy-only) | **UNOBSERVABLE** |
| NEISO | 2021/23/24/25 | — | — | 32,136 / 30,773 / 31,379 / 29,034 | 30,762 / 29,636 / 30,347 / 28,865 | +1,373 / +1,137 / +1,032 / +169 | PASS ×4 | IN-BAND ×4 | **UNOBSERVABLE** |
| MISO | 2023 | −2,876 | −4,908 | 124,809 | 121,644 | +3,165 | PASS | IN-BAND | MISS |
| MISO | 2024 | 0 | −4,908 | 124,738 | 122,429 | +2,309 | PASS | IN-BAND | MISS |
| MISO | 2025 | +6,667 | +1,759 | 127,934 | 119,509 | +8,425 | PASS | IN-BAND | **HIT** |
| NYISO | 2023 | −1,565 | −3,775 | 34,745 | 34,559 | +186 | PASS | IN-BAND | MISS |
| NYISO | 2024 | 0 | −3,775 | 35,829 | 33,398 | +2,431 | PASS | IN-BAND | MISS |
| NYISO | 2025 | −2,513 | −6,288 | 36,439 | 34,058 | +2,381 | PASS | IN-BAND | MISS |
| PJM | 2023 | −3,781 | −17,219 | 174,676 | 160,904 | +13,772 | PASS | IN-BAND | MISS |
| PJM | 2024 | 0 | −17,219 | 175,356 | 166,810 | +8,546 | PASS | IN-BAND | MISS |
| PJM | 2025 | +2,460 | −14,759 | 147,764 | 150,605 | **−2,841** | **FAIL** | **BELOW** | **HIT** |

Bundles read: `caiso-…-t1h-d46`, `ercot-…-t1h-d46`, `miso-…-t1h-d53-sectorgate-d51ratio`,
`neiso-…-t1h-d46`, `nyiso-…-t1h-d52-devintage`, `pjm-…-t1h-d74-nodefaultcap`.
`UNOBSERVABLE` means the bundle predates capx D52 and carries **no** `screen_*` ledger keys, so the
delta its OWN screens saw cannot be recovered — grading it against the HEAD delta of §2.1 would be
grading a different recipe's number, and is refused. Their §2.1 deltas stand as the magnitude phase 1
will face; they are not a reading.

**What the MISSes mean, stated against interest.** They are not evidence that the defect has the
wrong sign. In 2023 and 2024 the fleets sit **2.3-13.8 GW above** their requirement, so a cumulative
bar understatement of 3.8-17.2 GW is absorbed by slack and never manifests as a position failure —
"MISS" here reads *the defect is not the binding constraint in that year*, and the test is
structurally incapable of firing while the floor holds the fleet that far clear. In the single
observable year where the slack is gone — **PJM 2025, I7 FAIL by 2,841 MW and I12 below band on a
−14,759 MW cumulative seam error** — the sign matches. MISO's 2025 HIT is the mirror case: the
cumulative flips positive (+1,759 MW) and the fleet is long by 8,425 MW.

**The honest summary for the director: the defect does not explain a board row today, because the
board carries no T1-H FC-1 row at all and the two ISOs where it could have shown are cushioned. It
explains exactly one observable position failure (PJM 2025), and it is a rule-14 construction defect
on its own terms regardless of what any residual does — a synthesized historical peak in place of the
measured load the same LP dispatches.**

---

## 4. Phase 1 — the seam, every consumer of it, and the collisions

**Not built. This section is the enumeration rule 19 `[R-ONE-MECH]` requires before a floor or a
replacement is added, produced ahead of the work rather than alongside it. Arming is the
director's.**

### 4.1 The seam

**One seam, three lines**: `runner.py:2029-2031`, the assignment of `peak_demand` at the top of the
year loop. The phase-1 gate — `capacity_screen_peak_measured_hindcast: bool`, default-off, registered
in `ScenarioConfig` (rule 24 `[R-REGISTRY]`), zero scalar fields — makes that peak the **measured**
year's peak, under the identical branch predicate the LP already uses 500 lines down:

```python
if config.hindcast and not config.is_crossover_forward_year(year):
```

**It REPLACES the de-grown peak; it does not stack on it** (rule 19). Forecast years have no measured
load, so the gate is inert there by construction and the growth path remains **the** forecast
methodology — rule 13 `[R-MEASURED]`'s forward test is satisfied because the measured hindcast peak
is a reproducible physical input for the year in question, not a fitted answer, and the forecast
branch is untouched. Every non-hindcast run, every forecast year of a crossover, and every backcast
is byte-identical with the gate on or off.

**Cost note for the implementation:** the measured array is *already loaded* in the same year's
iteration, but **later** (`year_base_demand`, line 2472) than the seam needs it. Phase 1 must either
hoist that load or take its peak separately; a second `load_demand` call is correctness-neutral but
doubles the year's demand I/O, so the hoist is preferred and must be shown not to move
`year_base_demand` itself.

### 4.2 Every consumer of the seam peak (the rule-19 enumeration)

The seam peak flows to **six** places directly, and through the fifth to five more. Nothing else in
`runner.py` reads it: `peak_demand` is REBOUND at line 2548 to the LP/measured basis, so everything
downstream of the fleet build (results, ledger `peak_demand_mw`, `reserve_margin`,
`adequacy_requirement_mw`, scarcity, the D52 `_next`-year accounting at 4728-4812) is already on the
measured peak and is **out of scope** — which is exactly why the two disagree.

| # | site | consumer | gate | in scope |
|---|---|---|---|---|
| 1 | `runner.py:2059` | `capacity_reserve_position(..., peak_demand, year)` — the CR-1 sloped-curve reserve position, threaded verbatim into all three screens | `capacity_market_clearing_by_iso` | yes |
| 2 | `runner.py:2098` | `locality_peak_by_zone = peak_demand × zone.load_share` — capx D59 NYISO locality positions/prices | `locality_capacity_curves` (default off) | yes |
| 3 | `runner.py:2127` | `resolve_adequacy_requirement_mw(config, iso, peak_demand, year)` → ledger `screen_adequacy_requirement_mw` | none (observability) | yes |
| 4 | `runner.py:2135` | `accredited_firm_capacity_mw(..., peak_demand_mw=peak_demand, ...)` → ledger `screen_entering_firm_mw` | none (observability) | yes |
| 5 | `runner.py:2266` | `evolve_fleet(..., peak_demand_next=peak_demand)` → `peak_demand_used` (`evolve.py:356-359`) | none | yes — expands below |
| 6 | `runner.py:2180` | ledger `screen_peak_demand_mw` — capx D52 observability | none | yes (the field's meaning changes) |

`peak_demand_used` inside `evolve_fleet` reaches:

| # | site | consumer |
|---|---|---|
| 5a | `evolve.py:738` | `apply_economic_retirements(..., peak_demand_used, ...)` — **the retirement reliability floor**, which resolves the requirement on it (`retirements.py:2450, 2865`) and credits renewables at `peak_demand_mw=` it (`retirements.py:2463, 2858`) |
| 5b | `evolve.py:978` | `apply_new_entry_screen(..., peak_demand_mw=peak_demand_used, ...)` — the thermal entry screen; note `_admission_cap_horizon` (`retirements.py:342-345`) then grows it AGAIN across the execution lag |
| 5c | `evolve.py:1041` | `accredited_firm_capacity_mw(..., peak_demand_mw=peak_demand_used, ...)` — the backstop's firm census |
| 5d | `evolve.py:1061` | `apply_reserve_margin_build(fleet, firm_mw, peak_demand_used, ...)` — **the reserve-margin adequacy backstop** |
| 5e | `evolve.py:1094` | the backstop's log line (reporting only) |

And within 5a/5b/5c the peak reaches two further gated terms that are easy to miss:
`resolve_renewable_capacity_credit(..., peak_demand_mw=...)` — the **penetration-indexed ELCC**
curves (`adequacy.py:349-357`, gated `elcc_curves_enabled` / `nqc_curves_enabled`) — and
`resolve_demand_response_supply_mw(..., gross_adequacy_requirement_mw(config, iso, peak_demand_mw,
accreditation_year))` — the capx **D48 DR-as-supply hold-last** (`adequacy.py:390-400`). Both sit on
the SUPPLY side, so mooting the requirement (D67 for PJM, D52 for NYISO) does **not** take the peak
out of those two ISOs' screens.

Storage entry consumes the seam peak only indirectly, via consumer 1's `reserve_position`, which the
runner threads to all three screens so adequacy is priced off one object (rule 19).

### 4.3 Phase-1 STOP gates (structural, per rule 29; recorded now so they cannot be written to fit)

1. The arm's `screen_peak_demand_mw` **equals** the year's measured peak to the MW, in every binding
   year, and equals the ledger's own `peak_demand_mw` in every solved year.
2. Every non-peak operand is byte-identical to the control — the fuel path, the fleet vintage, the
   outage overlay, every gate in §4.2's gate column.
3. The footprint is confined to the rows §4.2 names; no other ledger field moves except through them.
4. No non-target load-bearing criterion flips PASS → FAIL.

**G-CTRL form 4 is VOID for every ISO** and a control at HEAD is earned: D67 §2.2 established that
`DEMAND_GROWTH_RATES["PJM"]["mid"]["near"]` moved 0.036 → 0.064645 in the SCN-LOAD refresh, and every
committed T1-H bundle is PRE-hunk on `DEMAND_GROWTH_RATES` — the §2.1 growth rates read at HEAD are
not the rates any committed bundle was solved on. Differencing an arm against those bundles would
attribute the demand-table refresh to the gate.

### 4.4 Collisions — audited, and CLEAR

- **The wallclock P1 basis seed (#5091).** Classified: **no collision.** The merge `c316b2fa` touches
  `CHANGELOG.md`, `docs/cross-year-warmstart.md`, `docs/handoffs/wallclock-baseline-2026-07.md` and
  two `results/regression-goldens/wc-b-*/manifest.json` — no source at all; the code change
  (`bf37a0dc`, "Seed the cold-rebuilt P1 from the same year's P0 basis") is on
  `src/market_sim/pipeline/solve.py`, not `runner.py`.
- **`runner.py`'s year-loop preamble is otherwise quiet.** The most recent `runner.py` commit,
  `2c5b8242` (SCN-WS3b, clean-tier voluntary row), has hunks at lines 168, 1241-1296, 2939 and 4596 —
  **none inside 2000-2200**.
- **The D67 lane owns `gross_adequacy_requirement_mw`** — the requirement resolver. This lane owns
  the **peak** and does not touch it, exactly as chartered. The two compose cleanly: D67 removes the
  peak from PJM's requirement, this gate corrects the peak everywhere it is still read (§2.3).
- **`docs/handoffs/d67/gdrift_peak_probe.py` was edited** to factor out the seam helpers. This is a
  read-only diagnostic instrument, not a solve-path file; the edit is behaviour-preserving and its
  committed JSON re-derives byte-identically (verified by diff before and after).

### 4.5 Blast radius, stated plainly

The gate changes the screen operand of **every hindcast bundle in the repository** — all 24 committed
T1-H/T1-X recipes, six ISOs — and therefore every FC-1 and FC-3 T1-H row on the forecast board. It is
an **owner card**, not a lane decision, and nothing here arms it. Registration follows D65-B-R's batch
merge. Matrix duty (rule 28 `[R-MECH-MATRIX]`): the new `ScenarioConfig` field needs its row in
`docs/codebase-site/data/mechanism-matrix.js` plus a cell line in all six shards **in the phase-1
PR** — CI enforces that half. Nothing is stamped in phase 0, because nothing was tested.

---

## 5. Reproduction

```bash
.venv/bin/python docs/handoffs/d67/gdrift_peak_probe.py    # §1(d), byte-identical JSON
.venv/bin/python docs/handoffs/d76/peak_census.py          # §2, ~6 min, zero LP
.venv/bin/python docs/handoffs/d76/i7_i12_reading.py       # §3.2, seconds, committed artifacts only
```

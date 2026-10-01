# DESIGN CARD — NYISO-NEXT-19: CENTRAL EAST as a shift-factor flowgate — 2026-10-01

- **Session:** NYISO-NEXT-19 (orchestrator; zero LP in this container, rule 32 (a)).
- **Queue item:** 1, the CENTRAL EAST object. The handoff asked for a design card before any build.
- **Probe (zero LP):** `scripts/probes/nyisonext19_ce_shiftfactor.py` → `results/calibration/_nyisonext19_ce_shiftfactor.json`.
- **New evidence:** NYISO RT 5-min zonal **congestion components** (`data/raw/lmp-data/NYISO`). No prior NYISO lane has used them. Every earlier CE design was identified on the flow side (CE ~ TE, NEXT-16/17).
- **Status:** design only. No code, no solve, no PRECOMMIT. This card needs owner decisions (§6).

## 1. What the market's prices say CE is

RT intervals where F (CAPITL) sits more than $5 above E (MHK VL) on congestion: 46,695 in all, 45,882 of them in 2022 (42 % of 2022's 108,047 intervals; 2022 is the one full year in the repo).

**One binding element.** The first component of the zone × interval congestion matrix carries **79 %** of the variance (then 10 %, 6 %).

**Shift factors relative to F** (median, IQR over all 46,695 active intervals; the 2022-only medians are within 0.01; congestion taken relative to zone E):

| zone | A–E (WEST…MHK VL) | **F** CAPITL | G HUD VL | H MILLWD | I DUNWOD | J NYC | K LONGIL |
|---|---|---|---|---|---|---|---|
| ratio to F | −0.04 to +0.01 | **1.00** | 0.66 (0.54–0.69) | 0.68 | 0.67 | 0.67 (0.56–0.71) | 0.68 |

**CE congestion tracks CE loading** (2022, hourly):

| measured CE flow / posted limit | < 0.70 | 0.70–0.85 | 0.85–0.95 | ≥ 0.95 |
|---|---|---|---|---|
| hours | 612 | 2,978 | 4,292 | 876 |
| mean F − E congestion, $/MWh | 10 | 17 | 39 | **90** |

**Reading.** When CE binds, the market prices all of A–E at one level, **F carries the full CE shadow price, and every zone from G to K carries about two-thirds of it.** That is a textbook single flowgate: a MW withdrawn in F loads CE 1.5× as much as a MW withdrawn in G–K, because part of any G–K delivery travels on the non-CE TOTAL EAST paths.

## 2. Why every transport-link design failed

A transport link can give a downstream zone either the **full** shadow price (it sits behind the link) or **none** (it has a slack parallel path). It cannot give it **two-thirds**.

| design | F gets | G–K gets | result |
|---|---|---|---|
| keeper: one UW→CH link at the TE envelope | μ | μ | link never binds, μ ≈ 0 |
| NEXT-17 (A): UW→F + UW→G–I links | μ | 0, via the slack UW→LH path | UW→LH absorbs the transfer; CE link binds < 1 % in 2024–25 |
| NEXT-16 DF: TE ≤ CE limit / α | μ | μ | a fixed CE share of TE; exceeded by measured TE in ~30 % of 2021–22 hours |

The market's structure, F > G ≈ H ≈ I ≈ J, with power flowing F → G, is **not reachable** by any choice of transport caps. That is why the routes have run out. It is also why lowering upstate offers would be wrong: the missing object is a network term, not a supply cost.

## 3. Proposed construction: a zonal shift-factor flowgate

On the existing `nyiso_fg_split` topology (Capital_Hudson = F; Lower_Hudson = G+H+I), add **one row per hour**:

```
CE(t) = k_F · W_F(t) + k_GK · W_GK(t)  ≤  CE posted limit(t)
```

- `W_F` = net withdrawal of F; `W_GK` = net withdrawal of G–K. Both are linear in link flows that already exist: flows into the zone from every link, including the import-node links.
- Sending zones A–E and the western import nodes have shift factor 0 (§1). This is the reference.
- `k_GK / k_F = r ≈ 0.67`, identified from the **prices** (§1).
- `k_F` is the one absolute scale. Identify it from **measured flows**: `CE = k_F · (r·TE + (1−r)·W_F)` over the binding regime, one value per network vintage.
- **Routing-invariant by construction.** The row depends on net withdrawals only, so the LP gains nothing by rerouting UW→LH→CH. That is the loophole that sank design A.
- The existing UW→CH / UW→LH transport links stay as thermal envelopes (TE p90, unchanged). The flowgate is a second constraint on the same flows, not a replacement cap.
- **Duals give the market's price shape:** `LMP_F − LMP_UW = μ·k_F` and `LMP_GK − LMP_UW = μ·k_GK`. No price is pinned (rule 4 `[R-DUALS]`).
- **Vectorized:** a sparse hour-diagonal block (`kron(I_T, coeff_row)`), no hour loop (rule 2).
- **One mechanism** (rule 19): it replaces nothing and stacks on no floor. The DF cap (never built) and `nyiso_fg_split`'s standalone use (R) are its predecessors, not peers.

### Free parameters (rule 21 DOF ledger)

| parameter | value | identification | forward story (rule 13) |
|---|---|---|---|
| `r` = k_GK / k_F | 0.67 (pre-AC-Transmission) | RT congestion-component ratio, median | network property; changes only with new lines |
| `k_F` | TBD (expected ~0.7–0.8) | through-origin fit of measured CE on TE and W_F | same |
| CE limit(t) | posted hourly | `interface-flows` `positive_limit_mw` | monthly posted profile, as today |

Neither `r` nor `k_F` is tuned against a price or volume residual. Both are network properties the market reveals.

## 4. Zero-LP pre-check, before any code (gates fixed now)

The next lane builds measured `W_F(t)`: F hourly load, minus F-sited generation (CAMPD + hydro + the F import-node share), using the `nyiso_fg_split` county map. Then, per year 2021–2025:

| gate | test | pass |
|---|---|---|
| **P-1** physical exceedance | share of hours where the measured flowgate LHS exceeds the posted CE limit by > 5 % | ≤ 10 % (the tolerance the keeper's TE p90 envelope already carries) |
| **P-2** binding lift | measured F − E congestion in the top-decile flowgate-loading hours ÷ in all hours | ≥ 2.0 |
| **P-3** r stability | monthly median r within ±0.10 of the vintage value | ≥ 10 of 12 months |

- **If P-1 or P-2 fails:** the 5-zone model cannot carry CE. The CE-hour spread goes in the ledger as a model-class limitation, and the lane moves to queue items 2–4. That is a legitimate end state, not a reason to re-tune.
- The DF route failed the analog of P-1 at ~30 %. The added `W_F` term is what this design brings; it is the reason the CE share of TE varies. Whether it closes the gap is unknown until P-1 runs.

## 5. Known risks, stated before any solve

1. **July–August 2022: r ≈ 0.33–0.37**, not 0.67. A second element, most likely an F → G path, binds in summer. One flowgate will mis-price those months. Report it; do not add a second row to fix it without its own evidence.
2. **2021 has no RT component data** in the repo. 2022 is the same network vintage (before the NY Transco AC Transmission project, Dec 2023), so 2021 can borrow r, as a declared rule-14 alignment.
3. **Post-Dec-2023 vintage is under-identified.** 2023–2025 hold only 813 active intervals, scattered over 9 partial months, with inconsistent ratios (0.32 / 1.00 / 3.8). That is not enough to identify r. CE rarely binds after the upgrade, so the flowgate matters little there, but the r value still needs a full year.
4. **Loop flow and PAR schedules** (Lake Erie loop, Ramapo, St. Lawrence) move CE flow with no zonal injection change. The fit residual shows up as P-1 exceedance; it is not modelled away.
5. **Rule-13 reading.** Shift factors identified from market prices are a network property, not a price level. Still, they come from an outcome series. This needs an owner ruling (§6, decision 2).

## 6. Owner decisions on this card

1. **Proceed to the §4 pre-check** (zero LP, next lane), or ledger CE now as a model-class limitation and move on to items 2–4?
2. **Rule 13:** are shift factors identified from RT congestion-component *ratios* admissible as a measured network input? The alternative is published NYISO shift factors, if a source can be found. None is in the repo today.
3. **Data intake** (needed for P-3 and for the post-2023 r): the NYISO RT zonal LBMP archive (P-24B, public) for 2021 and full 2023–2025, about 48 monthly zips, `DATA PROFILE: nyiso`.

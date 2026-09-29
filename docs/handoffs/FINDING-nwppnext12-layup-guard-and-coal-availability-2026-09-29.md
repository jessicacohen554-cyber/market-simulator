# FINDING — NWPP-NEXT-12: lay-up guard, Boardman membership, coal availability (ZERO LP)

Keeper #16 (`2026-09-29-nwppnext10-exit-month-routing`) stands while this is written. Every number below is zero-LP:
four re-derives of the NWPP CAMPD outage extract at HEAD (`scripts/data/derive_campd_unit_outages.py`, years
2019–2025), the merit panel `scripts/lib/outage_detect.build_merit_order_panel`, and a `fleet_only` rebuild of keeper
#16's recipe (`scripts/probes/_nwppnext10_coal_availability_census.py` with its `BUNDLE` repointed at
`nwppnext10xy_span` and one extra variant).

## 1. The four re-derives

| extract | invocation | windows | COAL TWh-eq | CC_REGULAR TWh-eq |
|---|---|---:|---:|---:|
| committed `campd-unit-outages-NWPP.csv` | standard | 5,058 | 74.87 | 166.27 |
| HEAD re-derive, standard | same invocation | 5,064 | 79.91 | 166.27 |
| standard + `--merit-order-guard` | | 5,016 | 72.64 | 166.27 |
| `--per-unit-crosswalk` | | 2,067 | 79.91 | 106.28 |
| `--per-unit-crosswalk --merit-order-guard` | (the `-perunitmerit-` family) | 2,019 | 72.64 | 106.28 |

TWh-eq = unit MW × window days × 24, summed over 2019–2025 (an outage-capacity measure, not energy lost).
CC_CHP, CT_CHP, ST_CHP and ST_GAS are identical in all five.

## 2. Lever 3: the merit-order guard does not separate lay-up on NWPP coal

### 2.1 What it reclassifies

48 windows, **all coal**, 7.27 TWh-eq: North Valmy 8224 (21), TS Power 56224 (9), Hardin 55749 (8), Jim Bridger 8066
(7), Hunter 6165 (1), Naughton 4162 (1), Hunter-3 Apr 2023 (1). It does **not** touch Centralia 2020 Mar–Jul or North
Valmy 2020 Jan–Jun (the handoff's two named windows), and it keeps all six Boardman windows (§4) as mechanical.

### 2.2 Separation test

For every standard-extract coal window, I computed the window's out-of-merit share and the same unit's out-of-merit
share over the **whole year**:

| unit-year annual out-of-merit share | coal windows | reclassified |
|---|---:|---:|
| ≥ 0.8 | 27 | 24 |
| ≤ 0.2 | 271 | 4 |

The window shares look bimodal (276 windows ≤ 0.1, 47 > 0.9), but the bimodality comes from the **unit**, not the
window. Why:

- The panel's revealed clearing cost is the 90th capacity-weighted percentile of **CEMS fossil** SRMC. On NWPP it is
  a flat band: 2020 p5–p95 = $26.3–30.2/MWh, 2023 $31.6–44.2. That band excludes hydro and imports, which set NWPP's
  spring margin, so it cannot see the hydro-season economics that make coal idle.
- The band sits on Bridger's own cost. In 2020, BW71 (measured HR 10.31, SRMC median $28.71) reads 8 % out of merit
  and BW73 (HR 10.69, $29.77) reads 100 %. A 4 % heat-rate difference flips a whole unit-year.
- High-cost rail-coal units (North Valmy $58/MWh, TS Power $51 in 2023) read out of merit all year, so every window
  they have is reclassified, maintenance included.

Four windows do show window-specific signal (Hunter 3 Apr 2023, Naughton 2 Oct 2022, North Valmy 2021, Hardin 2021).
That is too little to identify a mechanism, and the unit-rank effect dominates.

**Verdict: the guard does not separate idling from mechanical outages on NWPP's coal panel. Stop, per the handoff.
Matrix cell `campd_outage_merit_order_guard` → R (phase 0, identification).**

### 2.3 The per-unit crosswalk is a different, larger question

Arming the guard at runtime requires `campd_per_unit_attribution` too. On NWPP that re-routes **3,000 CC windows**:
Clark 2322 loses all 2,951 (its units leave CC_REGULAR under the crosswalk), and Silverhawk 55841 drops from 63 to 17.
Coal is byte-identical. That is a CC-routing question with its own identification owed. It is not lay-up, and it is not
armed here. Cell → O.

## 3. Lever 2: coal availability below measured generation

### 3.1 Most of the "shortfall" was a census artifact

The NEXT-10 census compared coal generators' available energy against the **whole-plant** EIA-923 net. Two plants
carry gas conversions:

- Naughton 4162: unit 3 runs on gas, 0.03 / 0.20 / 0.39 / 0.66 / 0.91 / 1.19 / 0.60 TWh of NG in 2019–2025.
- Jim Bridger 8066: units 1–2 run on gas from 2024, 2.99 / 2.71 TWh of NG in 2024 / 2025.

Against coal-fuel 923 only (BIT/SUB/LIG/RC/WC), neither plant is short in any year.

| year | coal-only shortfall, TWh | material plants |
|---|---:|---|
| 2019 | 0.22 | Centralia 7790 0.18 |
| 2020 | 0.21 | Centralia 3845 0.17 |
| 2021 | 0.60 | Colstrip 6076 0.53 |
| 2022 | 0.56 | Colstrip 0.43 (binding: model 10.43 = available 10.43) |
| 2023 | 0.38 | Colstrip 0.26 (binding: model 10.55 = available 10.56) |
| 2024 | 0.04 | — |
| 2025 | 0.61 | 10784 / 57915 carry zero availability (0.28 / 0.20) |

These are under 1 % of NWPP coal energy.

### 3.2 The source of the base availability

`fuel_trajectories.THERMAL_AVAILABILITY` gives every coal subclass the NERC-GADS tuple (POF 0.07, WEFOR 0.12 + age
escalation, derate 0.03). The keeper drops POF (`coal_drop_pof`), scales WEFOR by `wefor_multiplier = 0.7`, and leaves
`wefor_residual = None`. So the "0.89" is 1 − 0.7 × 0.12 − 0.03 = 0.886, before age escalation.

That statistical term is applied **on top of** the measured CAMPD ≥ 5-day, short (< 5-day) and partial windows. The
measured ≥ 5-day coal windows alone are ~10.7 TWh-eq/yr, against a statistical WEFOR of roughly 7–9 TWh/yr on
NWPP's coal fleet. The statistical term is therefore largely a double count. `wefor_residual` exists for exactly this
case (ERCOT 0.02, PJM 0.015, CAISO/MISO 0.0).

### 3.3 Why it is not solved in this lane

- The zero-DOF relief is miso-273's `wefor_residual_short_screened_coal`, with `wefor_residual = 0.0` identified by the
  caiso-187 formula max(0, W_s − X_s). It is fail-closed on `unit_outage_dispatched_bin_denominator`, which NWPP does
  not arm. That is a second mechanism, and it moves every class's outage denominator.
- The keeper's `wefor_multiplier = 0.7` scales the same term. It is a ledgered free parameter, and relief would make
  part of it moot. The two need to be read together.
- The payoff on the scored surface is small (Colstrip 0.26–0.43 TWh).

**Routed to NWPP-NEXT-13 as a phase-0 lane:** derive the NWPP screened set (`--short-windows --emit-screened-set`),
compute W_s vs X_s per year, and census `unit_outage_dispatched_bin_denominator` on its own before any solve.
Cells `wefor_residual` and `wefor_residual_short_screened_coal` → O.

## 4. Lever-3 item 3 (Boardman): a membership defect, not a detection gap

NEXT-11 wrote that Boardman's whole-plant spring stops are "undetectable by the peer-online rule". That is wrong. The
HEAD deriver detects them through the full-stop override (plant CF < 0.02 for ≥ 5 days). The committed extract simply
never **scanned** facility 6106.

| window | days | unit MW |
|---|---:|---:|
| 2019-03-15 .. 07-01 | 107.8 | 623 |
| 2019-10-23 .. 10-28 | 5.0 | 623 |
| 2019-11-02 .. 11-12 | 10.8 | 623 |
| 2020-02-13 .. 03-14 | 30.2 | 612 |
| 2020-03-25 .. 07-13 | 109.5 | 612 |
| 2020-10-15 .. 12-31 | 77.5 | 612 (the retirement) |

- The re-derive with `--membership-vintage-union` adds exactly these six rows and nothing else.
- The guard keeps all six as mechanical: Boardman's 2019 annual out-of-merit share is 0.04, and 2020's is 0.00.
- The existing PJM-NEXT-2 mechanism, `unit_outage_membership_repair`, is built for exactly this defect: the committed
  extract unchanged (first 5,058 rows byte-identical), plus the rows of never-scanned facilities.
- Fleet-only census on keeper #16's recipe: coal available energy −1.60 TWh (2019) and −2.02 TWh (2020). 2021–2025
  are byte-identical.
- The keeper's own Boardman dispatch in those windows is ≈ 0.3 TWh (2019) and ≈ 0.75 TWh (2020), from the payload's
  monthly means.

This is a clean rule-14 arm with zero free parameters. It is solved in
`PRECOMMIT-nwppnext12-boardman-membership-2019-2025-2026-09-29.md`. It cannot move C4 coal 2023, because Boardman retired in
October 2020.

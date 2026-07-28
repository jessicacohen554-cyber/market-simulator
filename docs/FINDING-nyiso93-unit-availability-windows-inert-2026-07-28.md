# FINDING — nyiso-93: the measured unit-availability window family is INERT in NYISO (ex-ante, 2026-07-28)

**Verdict: `unit_outage_short_windows` + `unit_partial_outage_windows` are
INERT for NYISO — adjudicated ex-ante, NO SOLVE SPENT.** Both companion
extracts derive to **zero rows** across 2023–2025, and the reason is not that
the detector found no windows: it is that the detector found **no coal**.
NYISO has carried **0.0 MW of coal-class capacity** in every scored year, and
its CAMPD states report **zero coal unit-years** over the whole window. The
mechanism has an empty input population on both grains it touches.

Matrix cell `unit_outage_short_windows` × NYISO: **U → I**
(`docs/codebase-site/data/mechanism-matrix.js`, cat `outage`). Lever-queue
basis: `docs/mechanism-testing-matrix.md` §5.5 NYISO item 5
("`unit_outage_short_windows` — derive for NYISO; cheap grain test") — this
closes that queue item.

Reproduce: `uv run python scripts/probes/nyiso93_unit_window_census.py`.

---

## 1. The one-line reason

**The detector is coal-only by construction, and NYISO stopped burning coal in
2020.** Every guard downstream of that — the CF ≥ 0.55 when-operable baseload
screen, the revealed-availability in-merit filter, the plateau constants — is
never reached, because the population they filter is empty before they run.

## 2. What was derived (Step 1)

Both artifacts were derived on the frozen constants, coal-only scope, and the
when-operable baseload guard exactly as shipped — nothing loosened
(rule 23 `[R-FROZEN-DERIVE]`):

```
uv run python scripts/data/derive_campd_unit_outages.py --iso NYISO --short-windows   --years 2023 2024 2025
uv run python scripts/data/derive_campd_unit_outages.py --iso NYISO --partial-windows --years 2023 2024 2025
```

| artifact | rows | windows/yr | distinct units | MW-days removed | class mix |
|---|---|---|---|---|---|
| `data/raw/campd-unit-outages-short-NYISO.csv` | **0** | 0 / 0 / 0 | 0 | 0 | — |
| `data/raw/campd-partial-outages-NYISO.csv` | **0** | 0 / 0 / 0 | 0 | 0 | — |

Both files are committed with their full header rows — a real, valid,
empty extract, not a missing file.

## 3. Why they are empty — grain 1: the detector's input

The short/partial guard is `unit_is_coal[uid]`, i.e. CAMPD
`primaryFuelInfo ∈ {"coal", "coal refuse"}`
(`scripts/data/derive_campd_unit_outages.py`, the
`if args.short_windows or args.partial_windows:` block). Census of every
unit-year in NYISO's CAMPD states (`campd.states_for_iso("NYISO")` = `NY`,
`NJ`):

| year | pipeline nat gas | diesel oil | residual oil | other oil | nat gas | wood | **coal** |
|---|---|---|---|---|---|---|---|
| 2023 | 276 | 73 | 10 | 6 | 3 | 3 | **0** |
| 2024 | 249 | 73 | 10 | 3 | 3 | 3 | **0** |
| 2025 | 243 | 56 | 10 | 3 | 3 | — | **0** |

**Zero coal or coal-refuse unit-years in all three years.** The gate rejects
100 % of candidates on its first test.

## 4. Why they are empty — grain 2: the overlay's consumer

`unit_outage_short_derate_factors` defensively re-filters to
`plant_group == "COAL"` (`src/market_sim/data/outages.py`), so even a populated
CSV could only reach a COAL-binned model plant. The NYISO model fleet has none:

| year | total fleet | ST_GAS | CC_REGULAR | CC_CHP | nuclear | oil | CT_PEAKER | ST_CHP | CT_CHP | biomass | **COAL** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2023 | 30,253 MW | 8,902 | 6,878 | 4,320 | 3,326 | 2,906 | 2,610 | 470 | 450 | 392 | **0.0** |
| 2024 | 30,253 MW | 8,902 | 6,889 | 4,309 | 3,326 | 2,906 | 2,614 | 470 | 446 | 392 | **0.0** |
| 2025 | 30,253 MW | 8,902 | 6,889 | 4,309 | 3,326 | 2,906 | 2,614 | 470 | 446 | 392 | **0.0** |

`coal` as a `fuel_type` is likewise 0.0 MW in every year. **Two independent
zeros** — the mechanism cannot bind even if the extract were populated by a
future data revision.

## 5. Provenance — dating the phase-out from repo data

The NY coal exit is visible in our own CAMPD extracts, so the finding does not
rest on an external claim. Coal generation by unit (GWh, `grossLoad` summed):

| year | plant | unit | GWh |
|---|---|---|---|
| 2019 | 6082 Somerset Operating Company (Kintigh) | 1 | 376.6 |
| **2020** | **6082 Somerset (Kintigh)** | **1** | **160.4** ← last NY coal generation |
| 2021 | 6082 Somerset; 2535 Cayuga | 1 / 1,2 | 0.0 (registered, never generated) |
| 2022 | 6082 Somerset; 2535 Cayuga | 1 / 1,2 | 0.0 (registered, never generated) |
| 2023–2025 | — | — | absent from the extract entirely |

Dunkirk (2554) and Cayuga (2535) had already stopped generating by 2019–2020;
Somerset is the last unit to produce a coal MWh in NYISO, in **2020**. The
2021–2022 rows are zombie CEMS registrations — reporting units with no output —
and they too are gone by 2023.

The NJ-side plants in the state scope (Logan 10043, Carneys Point 10566,
B L England 2378) are likewise all zero from 2019 onward, and in any case sit
in PJM, not the NYISO model fleet.

## 6. Inert, not merely empty — the no-op proof

An `I` verdict claims more than "the CSV has no rows": it claims arming the
flags is a provable no-op. Calling both consumers directly for NYISO, with the
standard (≥ 5-day) overlay as a live control:

| year | `short` keys | `partial` keys | `standard` keys (control) |
|---|---|---|---|
| 2023 | **0** | **0** | 41 |
| 2024 | **0** | **0** | 39 |
| 2025 | **0** | **0** | 41 |

The control is live in every year, so the empty results are specific to the two
companions rather than a broken path. Arming
`unit_outage_short_windows=true` + `unit_partial_outage_windows=true` applies
**no availability multiplier to any bin**, so the A/B arm of Step 2 would be
byte-identical to the keeper by construction. **No solve was spent.**

## 7. Scope discipline — what was NOT done

- **The detector was not loosened.** The CF ≥ 0.55 when-operable guard, the
  plateau constants, and the coal-only class scope are untouched
  (rule 23 `[R-FROZEN-DERIVE]`). Manufacturing windows by relaxing a guard
  would be fitting the mechanism to the desire for a result.
- **The detector was not extended to gas CC.** NYISO's fleet is 78 % gas by
  capacity, so a gas-scoped extension is the only way this family could ever
  bind here — and it is explicitly out of scope: economic single-train CC
  operation is indistinguishable from a partial outage in CF (the layup
  confound). That needs its own charter, not a quiet scope widening in an
  input-accuracy session.
- **No verdict was ported in or out.** Per rule 25 `[R-ISO-SCOPE]` this session
  derived NYISO's verdict from NYISO's own data. The row now carries **three
  mutually non-transferable negative verdicts, each for a different cause**:
  ERCOT `I` (ERCOT-126 — day-scale windows vs. an intraday cv gate, on a fleet
  that *has* coal), NEISO `R` (neiso-69, landed in parallel on 2026-07-28 —
  *rejected on provenance*, not fit: a single derived window is unit-mismatched
  to an EIA-860-excluded Merrimack u2 and arming it would delete measured
  supply), and NYISO `I` (this note — empty population). Same mechanism, three
  unrelated failure modes; none of them predicts another ISO's cell, and none
  touches the PJM/MISO `K` cells.
- **No dashboard registration.** Rule 15 `[R-DASHBOARD]` governs completed
  backcast *runs*; this session produced none. The deliverable is the committed
  extracts, this note, the probe, and the matrix cell.

## 8. Consequence for the NYISO lever queue

Queue item 5 (§5.5) is **closed as inert**. It was the cheapest remaining item,
and it is now spent without cost — the C3c blocker is untouched, and the
diagnosis is unchanged: NYISO's tail is **summer RT scarcity** (nyiso-92 dated
2025 Jun 23–25 = 18 of 42 measured >$300 h), so the live queue head remains
item 1, **DA virtual depth / DA demand formation**.

One genuine consequence for the *forecast* lane: this family cannot ever supply
NYISO availability grain, so NYISO's forced-outage representation rests
entirely on the statistical WEFOR/POF stack (`wefor_statistical_stack`, cell
`K`) plus the standard ≥ 5-day unit extract. That is the correct forward
analogue and needs no repair — but it does mean NYISO has **no measured
sub-5-day availability channel at all**, which is worth remembering before
attributing a short-duration NYISO tightness miss to fleet availability.

---

## Appendix — the 7 COAL-binned rows in the standard NYISO extract

`data/raw/campd-unit-outages-NYISO.csv` (4,423 rows) does contain 7 rows tagged
`plant_group == "COAL"`. They are **not** a contradiction:

- all 7 are **2018** windows — outside the 2023–2025 scored years, so they never
  enter a keeper solve;
- all 7 are one plant, **10025 RED-Rochester, LLC – Eastman Business Park**, an
  industrial cogeneration site detected via the `optime_proxy` fallback;
- the model bin (`plant_group`) is resolved by facility, not by CAMPD unit fuel
  — which is precisely why the short/partial detector gates on
  `primaryFuelInfo` instead, and why that gate returns zero here.

The standard extract's live **2023–2025** content (1,495 of the 4,423 rows) is
entirely gas and contains **zero** COAL rows: `CC_REGULAR` 575 / `CC_CHP` 440 /
`ST_GAS` 425 / `ST_CHP` 37 / `CT_CHP` 18. (Across all vintages 2018–2026 the
extract is `CC_REGULAR` 1,654 / `ST_GAS` 1,343 / `CC_CHP` 1,274 / `ST_CHP` 113 /
`CT_CHP` 32 / `COAL` 7 — the 7 being the 2018 RED-Rochester rows above.)

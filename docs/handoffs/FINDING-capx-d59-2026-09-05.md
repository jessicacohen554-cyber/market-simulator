# FINDING — capx D59: the NYISO LOCALITY half (NYC / LI on their own published ICAP demand curves, ICAP Manual §5.15.2 stacking) — BUILT default-off, zero DOF; RESULTS-PLACEHOLDER

**Lane:** capx D59 — D52 §8(2) route 1 (the locality half), the transcription check (route 2)
and the P9 re-run (route 3). Branch `claude/capx-d59-nyiso-locality-3p7sju`, fresh off
`origin/main` (`db057c5d`). The design `DESIGN-capx-d59-nyiso-locality-2026-09-05.md` was
pushed BEFORE any code (`5687b62e`), its §8.2–8.3 pre-declaration readings appended from the
zero-solve instrument before any code (`e3a5b5f8`), its §8.4 keys appended after the build and
before any solve (`d6256c6c`), and it is graded at full magnitude in §7 below, misses included.
**NOTHING ARMS**: the field ships DEFAULT-OFF, both legs register SUFFIXED, the bare `nyiso-t1h`
key is untouched (it moved upstream, not here — §1), no keeper / shard stamp beyond the D59 cells
/ marker, the backcast namespace untouched. Both recommendations return to the owner (§8).

RUNS-TABLE-PLACEHOLDER

## 0. Verdict (one paragraph)

VERDICT-PLACEHOLDER

## 1. What landed (default-off, zero DOF)

| surface | change |
|---|---|
| `config/capacity_market.py` | `LOCALITY_MARKET_DESIGN_VINTAGES["NYISO"]` (NYC / LI, 2021-22 … 2026-27, the `_nyiso_icap_vintage_curve` construction on each locality's published reference point / max clearing price / 18 % length / ARV — `()`-shape + flat ref × 12 for the two pre-ARV vintages, the NYCA convention), `NYISO_LOCALITY_UDR_ICAP_MW` (ICAP Manual §4.9.6, dated per its footnote 1), `LOCALITY_GROSS_CONE_BY_ISO` (2023-24 … 2026-27), `LOCALITY_CAPACITY_AREAS_BY_ISO`, `resolve_locality_curve_vintage`, `locality_curve_price_per_firm_mw_yr`, `resolve_locality_gross_cone_ratio`; constants facade re-exports. |
| `model/capacity_evolution/retirements.py` | `locality_capacity_curves_armed` (field AND registry entry AND the NYCA curve gate ON — rule 25 / DESIGN §3), `LocalityPosition`, `locality_capacity_positions` (ICAP census = entering-fleet `pmax` in the locality's zones + the LP zonal renewable nameplate + in-zone storage power + the published UDR rights; requirement through the EXISTING `capacity_deliverability.requirement_by_area` reader, hold-last of the LCR ratio beyond the table; position = the ICAP Manual §2.6 identity; the TSL is NOT supply), `locality_prices_by_zone` (the per-zone max over containing localities), `capacity_revenue_per_mw_yr(..., locality_price_per_firm_mw_yr=)` — the §5.15.2 max at the ONE seam (rule 19), `apply_economic_retirements(..., locality_prices_by_zone=)` + the `locality_price_per_kw_yr` margin-detail field. |
| `model/capacity_evolution/new_entry.py` | `_vre_cap_payment` settles at the sited zone's max; the thermal LOCALITY SITING LEG (each candidate also screened in each priced locality at that zone's LP price row, the settled price and the published Gross-CONE cost ratio; argmax siting, tie keeps the default zone; `build_zone` in the diagnostics row; the sited zone carried to the pipeline row / generator). |
| `model/storage.py` | `estimate_capacity_value(..., locality_prices_by_zone=)` — the load-share-weighted max(NYCA, zone) over zones; threaded through `apply_storage_new_entry`. |
| `model/capacity_evolution/evolve.py` | threads `locality_prices_by_zone` / `locality_cost_ratio_by_zone` into the retirement and entry screens. |
| `runner.py` | the positions computed ONCE per year on the SAME entering fleet as `curve_reserve_position` (the LP's zonal `wind_cap` / `solar_cap`, `storage_units` by zone, the seam peak × load share as the hold-last locality peak); the additive ledger block `locality_capacity` (census terms, requirement + source, position, locality price, NYCA price, settled price, Gross-CONE ratio, `below_requirement`) on every year; threaded to `evolve_fleet` and `apply_storage_new_entry`. |
| `config/scenarios.py` | `locality_capacity_curves: bool = False` (end of the field list); `_CACHE_KEY_OPTIONAL_FIELDS` / `_DEFAULTS` at `"False"`; `TIER_TAGS` 1; coerced to the dataclass default in a plain backcast, kept in a hindcast; `__post_init__` REFUSES it together with `capacity_deliverability_limits` on a NYISO config (rule 19, one locational mechanism per ISO). Pinned default key `4c6b03ae098b6e3e` unmoved; the bare `nyiso-t1h` key at this HEAD equals `origin/main`'s. |
| `scripts/run_capacity_hindcast.py` | `--locality-capacity-curves` (BooleanOptionalAction, `None` inherits), `FromConfig` meta row. `scripts/register_forecast_run.py`: `VERDICT_MAP` rows for the two suffixed D59 keys. |
| data | 12 `gross_cone` rows (2023-24 / 2024-25 / 2025-26 × NYCA / G-J / NYC / LI) appended to `demand-curve/nyiso/nyiso.csv` from the same three sheets the ARV rows cite (sha256 in the DESIGN §9); README block; `regenerate_clean.py capacity-market-demand-curve` green. The locality curve rows were already on disk and reconcile to the fetched sheets (DESIGN §6 item 1). |
| rule 28 | base row `locality_capacity_curves` (mode F, cat capacity) + a cell in all six shards (NYISO stamped with the measured verdict below; the five others `.` with the rule-25 reason each). `check_mechanism_matrix.py --base origin/main` green after `--fix-anchors` (digits only, four upstream rows). `check_cache_key_registration.py --base origin/main`: ok, 1 new field. `generate_parameter_registry.py --check`: OK. |
| tests | `tests/unit/model/test_capacity.py::TestNyisoLocalityCapacityCurves` (15): locality vintages reconcile to the csv per locality (ARV / cap fraction / zero-cross / the `()` pre-ARV convention); the gross-CONE registry reconciles; ratio resolution incl. hold-first / hold-last / other-ISO None; the TSL-floor consistency of every committed LCR row; the UDR dating; the §5.15.2 max at the price seam (incl. ERCOT zero); the per-zone max over containing localities; the gate predicate (field / curve gate / other ISOs / None); the §2.6 identity (position independent of EFORd; the TSL not added; UDR counted); zonal pools and storage counted, never load-share; hold-last LCR beyond the table and None before it; default-off / curve-off / other-ISO empty; storage load-share weighting; config semantics (key drop at default, distinct armed key, backcast coercion, hindcast keep, the Part-B exclusivity raise); the thermal siting leg (locality wins, the cost ratio undoes it, a tie keeps the default). Regression: 555 tests of the capacity / demand-curve / deliverability / storage / entry files green. |
| docs | `docs/capacity-deliverability-wiring.md`: the NYISO instance is this field, why the TSL is not supply for NYISO. |

**Choices the charter left open, decided and recorded (DESIGN §1–§5).** G-J excluded by the
union-of-zones rule (its premium bounded ≤ $1.7/kW-yr by the committed spot record); the TSL
rows are NOT supply (NYISO's LCR is already net of the import capability — the shipped Part-B
construction would read NYC ~30 pts long); the position is the ICAP Manual §2.6 identity
(ΣICAP ÷ ICAP requirement — no translation factor, no class-EFORd dependence); SCRs are
excluded from the census on BOTH halves (one census; the magnitude is reported); the
published UDR rights are the locality-attributable part of the D2 tie (locality census only,
no double count); the Part-B collapse is SUPERSEDED for NYISO, not stacked (rule 19,
fail-closed); the gate requires the NYCA curve gate ON (the §5.15.2 max is meaningless
against a flat anchor); thermal entry sees the locality price only against the published
locality Gross-CONE cost differential.

## 2. The transcription check (D52 §8 item 2) — answered, zero-solve (DESIGN §6)

1. **The committed 2025-26 curve rows are exact** against the fetched Demand Curve Parameters
   sheet (NYCA / G-J / NYC / LI ARV, reference points, maxima, lengths), and the 2023-24 /
   2024-25 locality rows reconcile to the ICAPWG decks. The 2025/26 "half the real spot"
   reading D52 flagged is a real property of the published 2025-2029 DCR reset (a 200 MW 2-hour
   battery peaking plant), not a records error.
2. **The 2025 SOM Table 9 UCAP-margin row is a carry-over of the 2024 SOM Table 11 row — a
   source defect.** Both print 5.8 / 16.4 / 5.7 / 11.7 %; the 2025 table's own "Net Change
   from Previous Yr" row (−2.3 / +1.0 / +2.1 / +0.5) and its narrative imply 2025/26 margins of
   **3.5 / 17.4 / 7.8 / 12.2 %**. Consequence for D52: the published 2025 NYCA position is
   1.035, so the model's seam position (1.052) is **+1.7 pts LONG** of the market rather than
   −0.6 SHORT — still inside the ±3-pt band; P9 (c) still reads YES. The curve at the
   corrected position pays $35.8/kW-yr against the $51.36 spot (−30 %), not $26.12 (−49 %).
3. **"Zone J cleared at $141" is the 2024/25 figure** ($11.76 × 12); 2025/26 is $10.98 × 12 =
   **$131.8/kW-yr**. A one-year label slip in D52 §4 and the charter; the argument holds.
4. The $51.36 figure is a UCAP-basis full-year average; the model evaluates one summer-basis
   position on the ICAP-priced curve (UCAP = ICAP ÷ (1 − 0.13) at the 2025/26 factor). Part
   of the D52 gap is basis and averaging, the same in both arms; recorded, not corrected.

## 3. The A/B on the record

RESULTS-PLACEHOLDER-3

## 4. The P9 re-read (D45 P9 / D52 §8, the same (a)/(b)/(c))

RESULTS-PLACEHOLDER-4

## 5. Explicitly NOT built, routed

1. **The annualization construction shared with the NYCA curve** (DESIGN §2.4): the ARV
   placed at position 1.0 where the published sheet defines the ARV as the annual revenue at
   the tariff Level of Excess on a two-season reference-point construction — the repo's line
   pays 0.957 × ARV (NYCA), 0.876 × (NYC), 0.79 × (LI) at the LOE, and the seasonal position
   split is not represented. The CR-3 seasonal item the NYCA code comment already names; a
   curve-shape change is barred by D45 §9 without new evidence and is identical in both arms.
   Routed to the director with the measured under-read (§3).
2. **G-J** (needs F split from G in the zone partition — a topology change, the backcast
   lane's; bounded ≤ $1.7/kW-yr on the record).
3. **SCRs as locality (and NYCA) supply** — D52 §5 item 2's D2-class intake; the magnitude is
   reported (NYC 418–479 MW, 4.5–5.5 pts; LI 31–35 MW).
4. **The 2023–24 Peaker-Rule exit set** the 2020-vintage hindcast fleet still carries in NYC
   (+468 / +482 MW vs the Gold Book in 2024 / 2025): the reachable-set / dates-channel object,
   not a census defect.

## 6. Matrix (rule 28) and registration

REGISTRATION-PLACEHOLDER

## 7. The pre-declaration, graded at full magnitude

GRADE-PLACEHOLDER

## 8. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

RECOMMENDATIONS-PLACEHOLDER

## 9. Governance attestation

- **Rule 1 / 13 / 14 / 21 / 23.** The locality instance of the census-evaluated-curve
  mechanism NYISO's spot market IS; every number a published curve parameter, a published
  requirement or the published rights table, reconciled to its committed source row by test;
  cleared spot prices and SOM margins entered nothing (validation observables); the sign was
  pre-stated before the build and the solve; no residual sized anything.
- **Rule 22.** T1-H solves {2021, 2023, 2024, 2025} with 2022 bridged; scored 2023–2025 only;
  no out-of-training year solved, scored or registered; the holdout freeze untouched; no
  default moves.
- **Rule 24.** One `ScenarioConfig` field threaded to `run_config.json` and the hindcast run
  record; the registries are cited constants; the LCR requirement rows enter through the
  existing curated reader (rule 6).
- **Rule 25.** NYISO-only by construction (one-ISO registries, entry-requiring predicate);
  measured inert on PJM / MISO / NEISO / ERCOT / CAISO with the flag armed (test).
- **Rule 19.** The §5.15.2 max at the ONE price seam; the Part-B collapse superseded for
  NYISO, refused when both are set; no locality floor added.
- **Rule 27.** Fable session; every file edited locally and the exact on-disk bytes pushed;
  every ≥300-line file blob-verified against the remote tree after each push.
- **Rule 28.** One base row + six cells in the same PR; the NYISO cell stamped with the
  measured verdict; `check_mechanism_matrix.py` green. Off-queue by charter (the D52 §8(2)
  successor lane), stated.
- **Rule 15.** Both legs registered through `register_forecast_run.py` in the session that
  produced them, FORECAST namespace only.
- **Backcast blast radius: not triggered.** The field coerces to its default in a plain
  backcast and is dropped from the hash at its default; the pinned default key and every
  backcast key are unmoved (measured).
- **Environment cost, stated.** Cold container: `regenerate_clean.py` (55 datatypes, ~45 min
  wall); each NYISO T1-H leg ~12 min, run one at a time.

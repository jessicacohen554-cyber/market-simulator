# FINDING — capx D59: the NYISO LOCALITY half (NYC / LI on their own published ICAP demand curves, ICAP Manual §5.15.2 stacking) — BUILT default-off, zero DOF; the A/B is BYTE-IDENTICAL to its control on every FC-3 row — the mechanism is the market's own and reproduces its published rows, but on this record the NYC locality curve at the model's NYC position (1.115 / 1.107 / 1.147, +8.8 / +5.0 / +6.9 pts LONG of the published 1.026 / 1.057 / 1.078) pays LESS than the NYCA leg in 2025, so the §5.15.2 max returns NYCA and the 2025 downstate-steam wave fires unchanged; P9 stays (c) YES / (a) NO / (b) NO; the object it surfaces is the NYC CENSUS (+0.7–0.8 GW vs the Gold Book) and the shared ARV-at-1.0 annualization; the transcription check finds the curve intake exact and the 2025 SOM margin row a source carry-over

**Lane:** capx D59 — D52 §8(2) route 1 (the locality half), the transcription check (route 2)
and the P9 re-run (route 3). Branch `claude/capx-d59-nyiso-locality-3p7sju`, fresh off
`origin/main` (`db057c5d`). The design `DESIGN-capx-d59-nyiso-locality-2026-09-05.md` was
pushed BEFORE any code (`5687b62e`), its §8.2–8.3 pre-declaration readings appended from the
zero-solve instrument before any code (`e3a5b5f8`), its §8.4 keys appended after the build and
before any solve (`d6256c6c`), and it is graded at full magnitude in §7 below, misses included.
**NOTHING ARMS**: the field ships DEFAULT-OFF, both legs register SUFFIXED, the bare `nyiso-t1h`
key is untouched (it moved upstream, not here — §1), no keeper / shard stamp beyond the D59 cells
/ marker, the backcast namespace untouched. Both recommendations return to the owner (§8).

| leg | run id | registers as | key | posture | wall |
|---|---|---|---:|---|---|
| comparator (committed, not re-solved) | `nyiso-2021-2025-realized-t1h-d52-curveon` | `nyiso-t1h-d52-curveon` | `589f031432b6dc7d` (D52 HEAD `881c11d`) | both D52 requirement gates ON + NYCA curve ON | 11.6 min (D52) |
| **control** (same key, this HEAD) | `nyiso-2021-2025-realized-t1h-d59-control` | `nyiso-t1h-d59-control` | **`589f031432b6dc7d`** | the D52 curve-ON recipe, `locality_capacity_curves` OFF | 9.0 min (04:57–05:06 UTC) |
| **A/B arm** | `nyiso-2021-2025-realized-t1h-d59-locality` | `nyiso-t1h-d59-locality` | **`4bb6dd6a798147b2`** (pre-declared on the complete recipe, matched) | the control + `--locality-capacity-curves` | 9.0 min (05:06–05:15 UTC) |

The bare `nyiso-t1h` recipe keys `91686abe7a744a88` at this HEAD — unmoved (the design's
§8.4 first read it as moved; that was a key script missing `--entry-screen-diagnostics`
/ `--vintage 2020`, corrected in §8.4 at full magnitude). Because the control carries the
SAME key as the committed D52 bundle, it is a same-key replay at a different HEAD: every
difference between the two is upstream drift (§3.3), and the arm-vs-control pair is
like-for-like at one key posture.

## 0. Verdict (one paragraph)

**The locality half is built the way NYISO's spot market actually works, it reproduces
its published rows, and on this record it decides nothing.** With the field ON, NYC (Zone J)
and Long Island (Zone K) are priced on their own published ICAP demand curves at their own
published Locational Minimum ICAP Requirements — position on the ICAP Manual §2.6 identity,
settlement by the §5.15.2 max(NYCA, locality) rule — and every FC-3 row of the arm is
BYTE-IDENTICAL to its control (§3.2). The reason is the position, not the price rule: the
model's NYC ICAP census (9,959 / 9,543 / 9,543 MW entering 2023 / 2024 / 2025, Linden Cogen
and Bayonne EC already inside it) sits **+727 / +824 / +838 MW above the Gold Book Zone-J
summer capability**, so the NYC position reads **1.115 / 1.107 / 1.147** against the
published 1.026 / 1.057 / 1.078 (+8.8 / +5.0 / +6.9 pts) and the 2025/26 NYC curve pays
**$25.7/kW-yr** there — BELOW the NYCA leg's $28.65 — so the §5.15.2 max returns NYCA and
the 2025 gas_st wave (1,904 MW at this HEAD, 1,267 of it NYC) fires exactly as in the
control. In 2023 and 2024 NYC's curve pays $56.3 and $61.0 (above NYCA in 2024) but neither
screen fails anything. LI reads 1.153–1.169 (published 1.117–1.131), its curve pays $3.6–8.0
and settles at NYCA in every year — which is the SOM's own reading of 2023/24. **P9 re-read
on the arm: (a) NO (+96 %), (b) NO (0.643), (c) YES — one of three; the NYCA curve stays
OFF.** The pre-declaration resolved to its stated alternative branch on P1 (NYC position >
1.132 ⇒ byte-identical), missed P4 in 2023 / 2025 (the census), and hit P6 (settled NYC
price 0.22–0.43 of the published spot, so the field's own flip condition fails as
pre-stated). The transcription check is answered: the curve intake is exact; the 2025 SOM
Table 9 margin row is a source carry-over of the 2024 row (§2). **Recommendations (§8): do
NOT arm the locality field on this record (structurally right, inert, and its NYC price
reads 0.2–0.4× the market's); do NOT arm the NYCA curve (P9 one of three, unchanged).** What
the lane surfaces and routes: the NYC census (+0.7–0.8 GW — the 2023-24 Peaker-Rule exit
set the 2020-vintage fleet still carries), and the ARV-at-1.0 annualization the NYCA and
locality curves share (a CR-3 object).

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

Instrument `docs/handoffs/d59/ab-compare-2026-09-05.py` (stdout + rows committed beside it);
every number below is read off the committed ledgers and `score.json` of the three bundles.

### 3.1 The locality positions and prices (the arm's `locality_capacity` ledger block)

| CY | locality | model ICAP census (fleet + VRE + storage + UDR) | published ICAP req | **position** | pre-declared (DESIGN §8.2) | published (SOM summer margin) | gap (pts) | locality curve @ position | NYCA leg @ ledger position | **settled** | published spot | settled ÷ spot |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | NYC | 9,959 + 3 + 3 + 315 = 10,280 | 9,224 | **1.115** | 1.031 (1.076 with the 416 MW) | 1.026 | +8.8 | $56.3 | $63.34 | **$63.34** | $191.6 | 0.33 |
| 2023 | LI | 5,124 + 130 + 10 + 990 = 6,254 | 5,400 | **1.158** | 1.162 | 1.131 | +2.7 | $8.0 | $63.34 | **$63.34** | $49.3 | 1.28 |
| 2024 | NYC | 9,543 + 3 + 3 + 400 = 9,948 | 8,985 | **1.107** | 1.067 | 1.057 | +5.0 | $61.0 | $48.04 | **$61.03** | $141.1 | 0.43 |
| 2024 | LI | 6,254 | 5,348 | **1.169** | 1.173 | 1.117 | +5.2 | $3.6 | $48.04 | **$48.04** | $43.2 | 1.11 |
| 2025 | NYC | 9,948 | 8,673 | **1.147** | 1.106 | 1.078 (implied, §2) | +6.9 | **$25.7** | $28.65 | **$28.65** | $131.8 | 0.22 |
| 2025 | LI | 6,254 | 5,423 | **1.153** | 1.157 | 1.122 (implied) | +3.1 | $7.4 | $28.65 | **$28.65** | $51.4 | 0.56 |

Readings. (i) **The NYCA seam positions are D52's to the sixth decimal in both legs**
(1.017473 / 1.040324 / 1.051998) — the design sits on the D52 half and never re-derives it.
(ii) **LI is the SOM's own story:** the LI curve reads $3.6–8.0 at 1.15–1.17 and the
§5.15.2 max settles LI at NYCA in every year (the 2023 SOM: "the Long Island price was set
by the NYCA price in all months of 2023/24"); its position is +2.7…+5.2 pts of the
published, inside the pre-declared band. (iii) **NYC is the object:** the model's NYC
census is 0.7–0.8 GW above the Gold Book Zone-J summer capability (§3.4), which puts the
position 5–9 pts long of the market and, on an 18 %-length curve, that is 28–49 % of the
ARV — in 2025 enough to read the NYC curve BELOW the NYCA leg. (iv) The instrument
(DESIGN §8.2) reconstructed the NYC fleet 356 MW low (its loader posture; the runner's
2023 entering NYC fleet also still carries the 416 MW of announced gas_ct the instrument
had already removed) — recorded as the reconstruction miss it is; the ledger block is the
exact record.

### 3.2 FC-3 — the rows that moved between the arm and the control

**None.** Every score row of the arm equals the control's (`generated_utc` aside):
`retire.total_gw` 3.360 (+96.4 %, FAIL), per-fuel gas_st 1.904 / gas_ct 0.420 / nuclear
1.036 / others 0, `unit_recall_gt300` 1/1, `false_retire` 2.160 GW (0.643, FAIL), additions
gas_cc 1.0 / gas_ct 0.0 / storage 0.000 / wind 1.902 / solar 1.782, every share row, LOYO
−2023 / −2024 / −2025 false 1.928 / 2.178 / 0.353 (recall 1/1 each), T-R10a/b FAIL/FAIL
(first mover gas_st, 2025), BLK-10 backstop 0.0 GW; the 2025 economic exits by zone are
identical (NYC 1,266.6 MW gas_st, Capital_Hudson 495.8, Upstate_West 141.5; 2023 the same
416.4 + 3.9 MW of announced gas_ct; 2024 none); the thermal-entry decisions identical (the
2022-decided 1,000 MW gas_cc landing 2024 in Upstate_West; no locality siting — no candidate
cleared in NYC or LI at the published Gross-CONE ratio 1.72–1.77 / 1.07–1.40, as
pre-declared in DESIGN §5.5). Determination **HOLD** in both, criteria identical.
**The arm is therefore the ledger-level byte-inertness proof of the mechanism at the price
seam:** with the field ON the settled price equals the NYCA leg in the only screen year that
fails (2025), and the 2024 NYC premium ($61.0 vs $48.0) reaches a screen in which nothing
fails; the mechanism has exactly the reach the design stated (DESIGN §8.1, the P1′ branch).

### 3.3 The control against the committed D52 bundle — upstream drift, stated

The control carries the D52 leg's own key (`589f031432b6dc7d`) and differs from the
committed D52 bundle in 86 flattened rows, all of one class: the 2025 gas_st cohort the
admission cap selects (1,801 → **1,904 MW**; NYC 946 → 1,267, Capital_Hudson 657 → 496,
Upstate_West 198 → 142), hence `retire.total_gw` 3.257 → 3.360, `false_retire` 2.057 →
2.160 (0.631 → 0.643), LOYO −2023 / −2024 false 1.825 → 1.928 / 2.075 → 2.178; a NEW
reported-only score section (`plant_release_precision`, D32 R4, absent from D52's scorer);
and the reported-only `co2.model` 2025 stream (−0.0005 %). This is the same input-vintage
drift class D52 itself recorded against D45-R (a held cache key over 24+ upstream commits
between `881c11d` and `db057c5d`): nothing in the D59 code path is reachable with the
field OFF (the retirement, entry and storage seams receive `None` and take the original
call), and the config-level key is unmoved. Stated, not absorbed; the A/B is read arm vs
control only.

### 3.4 The census check (DESIGN §8.3, on the ledger)

| CY | model NYC fleet ICAP (ledger) | Gold Book Zone-J summer capability | of which NJ-sited (Linden Cogen + Bayonne EC, both in the model's NYC fleet) | Δ | model LI | Gold Book Zone K | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 9,959 | 9,231.9 | 1,391.1 | **+727** | 5,124 | 5,005.7 | +119 |
| 2024 | 9,543 | 8,718.9 | 1,335.7 | **+824** | 5,124 | 5,072.5 | +52 |
| 2025 | 9,543 | 8,704.7 | 1,353.0 | **+838** | 5,124 | 5,195.5 | −71 |

LI is within 2.5 %. NYC is 7–10 % over the published census. The 2024–2025 excess (+0.82–
0.84 GW) is the 2023-24 Peaker-Rule / DEC exit set the Gold Book has dropped and the
2020-vintage hindcast fleet still carries (Gowanus and Narrows barges, the Astoria GTs —
the reachable-set / dates-channel object of the retirement scorer, D-24 / capx D42), plus
2–3 % of DMNC-vs-summer-capability and ICAP-eligibility difference; the 2023 excess (+0.73
GW) includes the 416 MW of announced gas_ct still entering that year. The SCR term (418–479
MW, DESIGN §2.2) would move the model FURTHER from the market, which says the market's
counted ΣICAP sits below the Gold Book capability by about that much. **The STOP condition
of DESIGN §10 is not tripped by the NJ-siting concern (both plants are already NYC units)
but IS the object this lane surfaces:** the NYC locality position is a census statement,
and the census is the backcast lane's fleet (COLLISION clause) — routed (§5).

## 4. The P9 re-read (D45 P9 / D52 §8, the same (a)/(b)/(c))

**D45 P9, graded verbatim on the arm (all three required; "any two of three is not
enough"):** (a) `retire.total_gw` within ±10 % — **NO** (+96.4 %; the control +96.4 %, D52
+90.4 %); (b) `false_retire` in band — **NO** (0.643); (c) entering NYCA positions within ±3
points of the published NYCA positions in every scored year — **YES** (−2.6 / −1.8 / +1.7 on
the corrected 2025 reading of §2). One of three ⇒ **the NYCA curve-ON default is NOT
recommended**, and the reason is now narrowed twice: D52 closed the position artifact; D59
shows the locality half cannot reach the 2025 wave on this record because the NYC position
reads 5–9 pts long of the market. What remains is (i) the NYC census (§3.4) and (ii) the
2025/26 NYCA vintage's level at the model's position ($28.65 against a $51.36 full-year
spot — part basis / averaging, part the ARV-at-1.0 annualization, DESIGN §2.4 and §6 item
4) — neither a curve-shape re-litigation (the D45 §9 line binds) nor a locality object.

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

- **Registered** `nyiso-2021-2025-realized-t1h-d59-control` → **`nyiso-t1h-d59-control`**
  and `nyiso-2021-2025-realized-t1h-d59-locality` → **`nyiso-t1h-d59-locality`**
  (`VERDICT_MAP` rows; `register_forecast_run.py --bundle` each; canonical sidecars
  `frontend/data/hindcast/<run_id>.json`, `scored_at_sha 3cd143bb` — a commit of this
  branch that the owner had already merged into `main` (PR #4760) by the time the results
  landed, so the results commit was rebased onto `origin/main` (`921bb4cd`) with the three
  recipe keys re-verified unchanged (bare `91686abe7a744a88`, control `589f…`, arm
  `4bb6…`) and the scored sha is never orphaned; reports `docs/hindcast-reports/<run_id>-2026-09-05.md`;
  `ff-verdicts.json` gains the two keys, purely additive, `provenance.session = capx-D59`;
  `--reindex` regenerated the gitignored namespace). Scored `score_capacity_hindcast.py
  --bundle` then `--flip-gate-extras`, then `forecast_verdict.py --tier t1h` (the D52
  sequence). The bare `nyiso-t1h` is untouched; the board (`program-status.json`) untouched
  (suffixed legs move no gate row).
- **Committed slim set** per bundle (the D52 template; gitignore carve-out
  `nyiso-2021-2025-realized-t1h-d59-*`): `meta.json`, `run_config.json`,
  `forecast_verdict.json`, the five `evolution_<year>.json` ledgers (the arm's carrying the
  `locality_capacity` block), `score.json`, the two `screen_signal_diag_*.npz` dumps.
- **Matrix:** base row `locality_capacity_curves` (mode F, cat capacity) + a cell in every
  shard; the NYISO cell stamped **`fc: I`** — INERT on this record (measured: byte-identical
  FC-3), neither rejected (the structure is the market's own and reproduces its rows) nor
  open (it was solved and read); it re-opens with new evidence on the NYC census or the
  annualization. The five other shards `.` with the rule-25 reason each. Off-queue by
  charter (the D52 §8(2) successor lane). `check_mechanism_matrix.py --base origin/main`
  green.

## 7. The pre-declaration, graded at full magnitude

**Cache keys: the arm's key `4bb6dd6a798147b2` was pre-declared on the complete recipe
(DESIGN §8.4 correction) and matched by the harness; the control's `589f031432b6dc7d`
equals the committed D52 leg's; the bare key held (`91686abe7a744a88`); the pinned default
unmoved. The first §8.4 table was computed on an incomplete recipe and read the bare key as
moved — withdrawn at full magnitude in §8.4 (a records error of this lane, corrected
before any result was read).**

| # | prediction (DESIGN §8.1–8.2) | conf | outcome |
|---|---|---|---|
| P1 | if the 2025 NYC position ≤ 1.132 the 946 MW NYC cohort passes (retire ≈ 2.31 GW, false ≈ 0.48); **else (P1′) the A/B is byte-identical on FC-3** | MED | **P1′ branch — HIT as the stated alternative**: NYC position 1.147 > 1.132; every FC-3 row identical to the control. The first branch's premise (position 1.106) was the instrument's 356 MW NYC under-count, not a mechanism surprise |
| P2 | P9 stays (c) YES, (a) NO, (b) NO — one of three | HIGH | **HIT** — (a) +96 % NO, (b) 0.643 NO, (c) YES |
| P3 | 2023 / 2024 screens fail nothing in either arm; entry gas_cc 1.0 / gas_ct 0 / storage 0 unchanged; no locality entry | HIGH | **HIT** — no economic exits in 2023 / 2024; entry rows identical; no candidate sited in a locality |
| P4 | model locality positions within 6 pts of the published (bare census) in every year; LI near 11–13 % with the UDR rights, well below without | MED | **SPLIT — LI HIT (+2.7 / +5.2 / +3.1), NYC MISS in 2023 and 2025 (+8.8 / +5.0 / +6.9)**: the census, +0.7–0.8 GW vs the Gold Book (§3.4); LI without the 990 MW of UDR rights would read 0.97–0.99 |
| P5 | bare key and pinned default unmoved; backcast coercion; other ISOs inert | HIGH | **HIT** (the design's own first key table was wrong on the recipe, corrected; the keys themselves held) |
| P6 | the NYC settled price reads 0.4–0.7× the published spot ⇒ flip-condition limb (iii) FAILS ⇒ expected recommendation DO NOT ARM; LI settles at NYCA | HIGH | **HIT on the direction, MISS on the band** — 0.33 / 0.43 / 0.22 (below the 0.4–0.7 band, because the position is 5–9 pts longer than the instrument had it); LI at NYCA every year |
| P7 (§8.2) | instrument readings NYC 1.031 (1.076) / 1.067 / 1.106; LI 1.162 / 1.173 / 1.157; NYC prices $128 / $94 / $58; ~2.3 GW / 0.48 if P1 | MED | **LI HIT to ±0.005; NYC MISS by +0.04 / +0.04 / +0.04** — one reconstruction term (356 MW of NYC fleet the instrument's base-fleet rebuild lacked), stated in DESIGN §8.2's caveat before the solve |
| P8 | ~12 min / leg, sequential | — | **HIT** — 9.0 / 9.0 min |

**Tally: 8 gradable items — 5 HIT, 1 HIT-as-alternative (P1′), 2 SPLIT (P4 NYC, P6 band /
P7 NYC).** Every miss is the same object — the model's NYC census vs the instrument's
reconstruction of it — and every mechanism limb behaved as designed.

## 8. The two arming recommendations (owner decides; this lane recommends on pre-stated conditions)

**(1) The locality field — `locality_capacity_curves` as NYISO's forecast default?
RECOMMEND: DO NOT ARM, on the pre-stated flip condition (DESIGN §8.1).** Limb (i) — every
locality position within the P4 band — FAILS for NYC in 2023 and 2025 (+8.8 / +6.9 pts);
limb (ii) — FC-3 moves in the pre-stated direction — is VACUOUS (byte-identical; nothing
moved either way); limb (iii) — the settled NYC price within 1.5× of the published NYC spot
— FAILS in every year (0.22–0.43). For: the structure (rules 1 / 13 / 21) is exactly the
market's own — the locality instance of the census-evaluated curve, the §2.6 identity, the
§5.15.2 max, zero free parameters, every row reconciled to its committed source, and it
supersedes a Part-B construction that is wrong for NYISO (the TSL as supply). Against, on
the record: it decides nothing here, and the price it settles NYC at is a fraction of the
market's — a mechanism armed on a census that reads 5–9 pts long would represent a NYC
that never earns its locality price, which is the same mis-representation as today's in a
different form. Arming is warranted only after (a) the NYC census is reconciled to the
published Zone-J supply (the backcast lane's fleet: the 2023-24 Peaker-Rule exit set /
reachable-set object, the DMNC basis) and (b) the shared annualization is either
represented seasonally (CR-3) or its under-read is accepted with its sign — at which point
the SAME A/B, re-run against the SAME pre-stated condition, decides. The field stays
default-OFF; the registries, the ledger block and the tests stay (they are the instrument
the re-run needs).

**(2) Consult the published ICAP demand curve at NYISO's default (the FF-3D flip)?
RECOMMEND: DO NOT ARM — P9 reads (c) YES / (a) NO / (b) NO on this record too, one of
three.** The locality half was the first of D52 §8(2)'s three routes and it does not reach
the 2025 wave; the transcription check (route 2) finds the curve intake exact and the 2025
SOM margin row a source carry-over (which moves the published 2025 NYCA position to 1.035
and leaves P9 (c) YES); the P9 re-run (route 3) is this section. The curve question
re-opens on the NYC census object and the annualization object — not before, and not as a
curve-shape re-litigation (the D45 §9 line binds).

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

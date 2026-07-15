# RC-1B — plumbing landed: per-ISO clearing gate, vintage-resolved net-CONE,
hindcast information gate, channel-attributed ledger — 2026-07-15

**Charter.** F-4 of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.1 items
2/5, §2.3 F-4; prompt §4.2 RC-1B). Scope guard: annual capacity-evolution
layer + hindcast harness/scorer only — no dispatch-layer floors, no AS
co-opt, no backcast keeper touched. **No LP solved this session.** No holdout
year touched (rule 22). Every new tunable is in `ScenarioConfig`/`constants.py`
with a citation and default byte-identical, per `scripts/generate_parameter_registry.py`
(regenerated — 5 new entries, `docs/parameter-citations.md`).

## What landed (items 1-4, 7, 8)

1. **Per-ISO `capacity_market_clearing` gate.** `ScenarioConfig.
   capacity_market_clearing_by_iso: dict[str, bool] | None = None` overrides
   the scalar per named ISO; `constants.resolve_capacity_market_clearing`
   is the one seam every capacity-price call site now reads through
   (`capacity_revenue_per_mw_yr`, `estimate_capacity_value`,
   `compute_plant_annual_summary`, the runner's curve-reserve-position gate).
   Default (mapping unset) is byte-identical — see
   `tests/test_capacity_demand_curve.py` (existing suite, unchanged, still
   green) plus the new per-ISO isolation assertions below.
2. **Per-delivery-year vintage resolution.** `constants.
   MARKET_DESIGN_VINTAGES` + `resolve_demand_curve_vintage(iso, year)`: PJM
   2021/2022-2027/2028, NYISO 2021-2022-2025-2026, ISO-NE 2020/2021-2027/2028,
   MISO 2025-2026-2026-2027 (MISO's pre-RBDC years, PY2021/22-2024/25, are a
   **vertical** demand curve per the datatype's own README — no net-CONE, no
   curve shape was ever published for them, so they are honestly absent
   rather than fabricated; the resolver's hold-first fallback then serves
   PY2025-26's parameters for any earlier MISO year, a documented limitation,
   not the forward hold-last policy). Several vintages (most pre-2025/26 PJM,
   NYISO 2021-2022/2022-2023) publish a net-CONE anchor but not a usable
   `pct_of_requirement` curve shape (absolute-MW points with no requirement-MW
   row to normalize by, or a missing cap-price row) — those carry
   `demand_curve=()` (rule 13: never fabricate an unpublished shape point) and
   fall back to the flat vintage anchor. `MarketDesign.
   capacity_price_per_firm_mw_yr` only consults the vintage table when BOTH
   `iso` and `year` are passed — every pre-existing call site passes neither,
   so the default path is untouched.
3. **Hindcast information gate (RC-0B D4).** `load_confirmed_exits` /
   `load_announced_reversal_plants` grow an `as_of: date | None` parameter;
   the runner computes `as_of = date(eia860_vintage_year, 12, 31)` in
   hindcast mode only. A new `superseding_instrument_date` column (nullable
   datetime) on the `confirmed-retirements` datatype records WHEN a reversal
   itself became knowable (distinct from `instrument_date`, the original
   instrument's date) — populated for the one on-disk reversal case
   (Byron/Dresden, CEJA 2021-09-15). Regression tests
   (`tests/test_confirmed_retirements.py::TestHindcastInformationGate`)
   assert exactly the two RC-0B-named cases: Byron/Dresden do NOT suppress at
   an as-of-2020 cutoff (CEJA postdates it) but DO once the cutoff passes
   2021-09-15; Braunig 1/2 (instrument_date 2024-03-13) do NOT fire at an
   as-of-2020 cutoff. Both loaders now `logger.warning` (not silent
   info/return) when the clean partition is missing, naming the
   reproducibility risk explicitly (a gitignored partition silently absent
   must never be mistaken for information discipline).
4. **Channel-attributed evolution ledger (RC-0B D3 prerequisite).** The
   recorder's `reason` vocabulary splits `"known"` into `"confirmed"` (step 0)
   and `"announced"` (step 1) by snapshotting the fleet before each step
   separately, plus a new `confirmed_derates` event list for a confirmed
   registry row that derates a plant-binned tranche without fully retiring
   its `unit_id` (previously invisible). Additive: every already-committed
   bundle's `"known"` rows stay interpretable (they predate the split), no
   ledger rewrite.
7. `scripts/run_capacity_hindcast.py` grows `--capacity-market-clearing`
   (probe, default off), wired through `build_config` exactly like the
   existing G-30/G-31 probe arms, arming the gate for the hindcast's own ISO
   only via the per-ISO mapping.
8. Tests: `tests/test_confirmed_retirements.py` (new
   `TestHindcastInformationGate` class, 5 cases), plus manual vintage-table /
   per-ISO-gate spot checks (`resolve_demand_curve_vintage`,
   `resolve_capacity_market_clearing`) exercised inline; the full existing
   `test_capacity_demand_curve.py` (29 cases incl. byte-identity),
   `test_capacity.py` (all cases), `test_storage.py` (all cases) suites pass
   unchanged. `model-methodology-spec.md` §5.9 gained the RC-1B subsections;
   `docs/parameter-citations.md` regenerated.

## What did NOT land this session, and why (items 5/6, honestly scoped down)

**Item 5 — IS-2020 scorer pass + T-R8 re-score.** RC-0B's scoring
definitions (§c.5: reversal exclusion, Palisades physical-exit convention,
per-channel recall/false-retire) are fully specified and this session's
channel split (item 4) and information-gate `as_of` machinery (item 3) are
the code prerequisites for them — both now exist. Implementing them into
`scripts/score_capacity_hindcast.py` (668 lines, its own retirement/actuals
comparison machinery, not read this session in full) and re-scoring the four
committed bundles is deferred: **T-R8's own pre-registered expectation
depends on RD-5** (the EIA-860 actuals-coverage fix adding plants 8907/1715
to `capacity_actuals_{nyiso,pjm}.csv`), which is confirmed **NOT landed** —
`grep -rn "8907\|1715" data/raw/_validation-source/capacity_actuals_*.csv`
returns nothing. Re-scoring now would not reproduce the pre-registered
NYISO/MISO false-retire-to-≈0 result and would misrepresent T-R8 as executed
when its data dependency is still open. Recommend: a follow-up scorer-only
session once RD-5 lands, consuming this session's channel split + `as_of`
gate directly.

**Item 6 — ACR grading table.** `data/raw/capacity-market/avoidable-cost-rate/pjm/pjm.csv`
IS on disk (RD-4 partially landed since the RC-0B memo was written): PJM
Manual 18 §5.4.8.4(B) default **gross** ACR by technology class, two vintage
columns (through 2025/2026; 2026/2027-and-subsequent), nameplate basis,
$/MW-day. Grading against this alone:

| Class | Gross ACR ($/kW-yr, 2026/27+ col × 365/1000) | Current model GFC input (fixed_om × multiplier, ATB-cited) | Note |
|---|--:|--:|---|
| Coal | 94 × 365/1000 = 34.31 | `fixed_om_coal` × 1.3 (scenarios.py) | ACR is materially BELOW the model's current FOM×1.3 bar in most ISOs' $/kW-yr terms — but ACR and FOM price different things (MOPR floor-offer avoidable cost vs. full avoidable going-forward cost) and are not directly interchangeable without the SOM avoidable-cost table as the other leg |
| Combined Cycle | 113 × 365/1000 = 41.245 | `fixed_om_gas_cc` | — |
| Combustion Turbine | 52 × 365/1000 = 18.98 | `fixed_om_gas_ct` | — |
| Steam Oil & Gas | 64 × 365/1000 = 23.36 | `fixed_om_gas_st` / `fixed_om_oil` | — |
| Nuclear (multi-unit) | 537 × 365/1000 = 196.0 | `fixed_om_nuclear`=130 | ACR is far ABOVE the current GFC — but nuclear ACR includes categories (security, NRC fees) with no analogue in the retirement screen's construction |
| Onshore Wind / Solar | 147, 70 × 365/1000 | n/a (VRE not retirement-screened) | not applicable to §b's reconciliation |

**Materiality-rule degradation (as RC-0B's §b.2 step 2 pre-registered):**
the rule as written compares the published figure against the SOM
avoidable-cost table's own spread (a second independent source). **The
Monitoring Analytics SOM avoidable-cost table is NOT on disk and is not
confirmed fetchable** (RC-0B's own note: "the MA-SOM second source does not
exist"). With only PJM Manual 18's single gross-ACR source available, the
materiality bar cannot be computed as specified — there is no second
published figure to measure the PJM ACR's own dispersion against. Per
RC-0B's own instruction ("record how the materiality rule degrades to
single-source"): **the rule degrades to no-op** — a single source can be
*reported* but not independently *graded* against its own spread, so this
session does NOT flip any GFC default (per instruction, a GFC flip is a
separate owner-approved cited commit, never landed here regardless). The
gross-vs-avoidable distinction (Manual 18's ACR is scoped to MOPR
floor-offer determination, a different regulatory purpose than the
retirement screen's own-going-forward-cost test) is also unreconciled —
recommend the RD-4 follow-up intake specifically target the SOM avoidable-
cost postings (Monitoring Analytics' public State of the Market report
appendices) before any GFC reconciliation is attempted, since a MOPR gross
ACR and a going-forward avoidable cost are constructed for different
purposes and are not a like-for-like substitute even as a single source.

## Files touched

`src/market_sim/config/{constants.py,scenarios.py}`,
`src/market_sim/{runner.py,model/capacity.py,model/storage.py,results/plant_financials.py,data/confirmed_retirements.py}`,
`scripts/run_capacity_hindcast.py`, `scripts/lib/confirmed_retirements/__init__.py`,
`data/dictionary/schema/confirmed-retirements.schema.yaml`,
`data/raw/confirmed-retirements/pjm.csv` (new column, populated for
Byron/Dresden only), `tests/test_confirmed_retirements.py`,
`model-methodology-spec.md` §5.9, `docs/parameter-citations.md` (regenerated).

*Produced 2026-07-15. No LP solved. No holdout year read or scored. Nothing
registered on any dashboard.*

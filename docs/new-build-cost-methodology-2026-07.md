# New-Build Capacity Cost Methodology — sources, ranges, and grounding (2026-07)

**Session:** capacity-cost-grounding, 2026-07-19 (branch
`claude/capacity-pricing-review-x3qn9s`). **Status of this doc:** standing
methodology reference for every capital-cost / fixed-O&M input to the capacity
expansion component (`model/capacity.py` economic new entry + emerging-tech
screens, `model/storage.py` storage value-stack entry). Companion artifacts:
the benchmark datatype `data/raw/new-build-cost-benchmarks/` (curated
cross-source table + QA'd markdown conversions of every source), the derivation
script `scripts/data/derive_cost_benchmark_envelope.py`, and the consistency
tests `tests/test_cost_benchmark_envelope.py` /
`tests/test_atb_entry_cost_consistency.py`.

Everything here is **forecast-only surface**: capacity evolution runs only in
`mode="forecast"` (`runner.py` hard gate), so backcast keepers are
byte-identical to before this session (verified — §7).

---

## 1. Design: one pinned mid anchor + a published-cost range

Each technology's cost is carried as **mid / low / high**:

- **Mid** = NREL **ATB 2024 v3.0.0 Moderate** at a documented base year (2026 =
  the model start year / `REAL_DOLLAR_BASE_YEAR`; 2030 for new nuclear and
  floating offshore — ATB's earliest published years for those), converted to
  constant 2026$ with the model's own `INFLATION_RATE` (2.2%/yr) deflator.
  Derivation-locked: `NEW_ENTRY_COSTS` (FF-1E), and since this session also the
  li-ion `STORAGE_TECHS` entries, `OFFSHORE_WIND_PARAMS`, and the EGS FOM,
  are deterministic functions of the committed extract, asserted by tests.
- **Low/high** = the **published-cost literature envelope**: min/max over every
  in-envelope, source-verified point of {ATB's own Advanced/Moderate/
  Conservative cases} ∪ {the cross-source benchmark table §3}, normalized to
  2026$, expressed as ratios to mid in `TECH_COST_MULTIPLIERS` (the PB-1
  `tech_cost_path` / `tech_cost_percentile` lever). Mid = 1.0 by construction,
  so **default runs are unchanged by the range**; the envelope only widens what
  low/high scenarios and the PB-2 sampler can express.

Why ATB Moderate as the mid anchor (not a cross-source blend): (a) it is the
convention of the reference capacity-expansion models (§2) so results are
comparable; (b) it keeps the mid a *single-source deterministic derivation*
(CLAUDE.md rules 5/23) rather than a curated average with hidden weights; (c)
**ATB 2024 is the final ATB edition** — no 2025/2026 edition exists (verified
2026-07-19: the OEDI data-lake listing ends at `csv/2024/`, and the ATB site —
now published by the renamed National Laboratory of the Rockies — still
headlines the 2024 electricity ATB), so the pin is *current*, not stale, and
the cross-source envelope is the mechanism that carries newer market
information (e.g. 2024-26 gas-turbine escalation, §4).

Dollar-year normalization: every published figure is converted from its
document's own dollar basis with `(1 + INFLATION_RATE)^(2026 − dollar_year)` —
the same internal-consistency convention FF-1E established (no external CPI
series; the Brattle rows are nominal-for-June-2028-online and deflate back from
2028).

## 2. How commercial-grade capacity-expansion models source these costs

Surveyed 2026-07-19; links are to the operative public documents.

| Model / practice | New-build cost source | Range treatment | Regional treatment |
|---|---|---|---|
| **NREL ReEDS** (national CEM; also the ATB's own consumer) | NREL ATB directly ([ReEDS documentation](https://www.nrel.gov/analysis/reeds/), [ATB data](https://data.openei.org/submissions/6006)) | ATB Advanced/Moderate/Conservative scenario axis | EIA/AEO-derived regional capital-cost multipliers |
| **EIA NEMS / AEO2026 EMM** | Sargent & Lundy bottom-up study commissioned by EIA ([Jan-2024 study](https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2025.pdf)), learning-adjusted each cycle ([AEO2026 EMM assumptions Table 3](https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf)) | AEO side cases (high/low macro & tech); technological-optimism factors on FOAK techs | **25-region overnight-cost multipliers** (EMM Table 4) |
| **EPA IPM (Power Sector Platform v6 / 2023 Reference Case)** | NREL ATB Moderate for renewables/storage; S&L-style engineering for thermal ([documentation ch. 4](https://www.epa.gov/power-sector-modeling/documentation-2023-reference-case)) | Single reference + scenario runs | Regional capital-cost adders (ch. 4 tables) |
| **CPUC IRP / E3 RESOLVE** (CAISO planning) | NREL ATB (2024 ATB adopted in the [2025 Inputs & Assumptions](https://www.cpuc.ca.gov/-/media/cpuc-website/divisions/energy-division/documents/integrated-resource-plan-and-long-term-procurement-plan-irp-ltpp/2024-2026-irp-cycle-events-and-materials/2025_inputs_and_assumptions_report_20260210.pdf)) + E3 pro-forma financing | ATB cost cases as sensitivities | CAISO-specific interconnection/land adders |
| **Energy Exemplar PLEXOS / Aurora datasets** (commercial) | Vendor-curated North-American datasets built from EIA, NREL (ATB/SAM/WIND toolkit), FERC, ISO sources ([dataset methodology](https://www.energyexemplar.com/power-datasets)) | User scenario axes | Zonal datasets carry regional costs |
| **Capacity-market administrative practice** (PJM/NYISO/ISO-NE demand curves) | Periodic bottom-up **CONE studies** — Brattle + S&L for PJM ([2025 CONE report](https://www.pjm.com/-/media/DotCom/committees-groups/committees/mic/2025/20250411-special/item-1-02-revised-cone-report-final.pdf)) | Per-CONE-area estimates, quadrennial resets | Per-CONE-area capital costs |
| **Investor/market practice** | Lazard LCOE+ annual capital-cost ranges ([v18.0, Jun 2025](https://www.lazard.com/media/uounhon4/lazards-lcoeplus-june-2025.pdf)) | Explicit published low–high per tech | n/a (national ranges) |

**Alignment statement.** This model follows the mainstream pattern: a national
lab/agency baseline as the level anchor (ATB Moderate — same anchor as ReEDS,
IPM renewables, CPUC RESOLVE), an explicit low/mid/high scenario axis (as every
surveyed model has), and market-intelligence cross-checks (Lazard, CONE
studies) folded into the range rather than the anchor. Two departures, both
documented as gaps in §6: (1) no regional capital-cost multipliers (the same
national cost applies in every ISO — EIA/IPM/ReEDS all regionalize; the
AEO2026 EMM Table 4 regional table is now on disk in the benchmark datatype as
the natural source if this is ever wired); (2) financing is a single real
discount rate by default (the per-tech ATB WACC option exists but is
default-off pending the FF-2D owner call on PTC/ITC double-count risk).

The model's *capacity-market price* inputs (net-CONE anchors and demand curves
in `MARKET_DESIGN` / `MARKET_DESIGN_VINTAGES`) are the ISOs' own published
auction parameters on disk, per-delivery-year — a stronger basis than any
third-party estimate, so this session left them untouched. Cross-check: the
Brattle 2025 report's CC gross CONE for the RTO area ($813/MW-day ICAP) is the
source-of-record for the PJM parameters the on-disk vintages already carry.

## 3. The benchmark sources (what was intaken, QA'd, and committed)

Five documents were downloaded, converted to page-marked markdown (pdfplumber),
and every transcribed number was read back from the conversion — the QA/QC
protocol requested for this session. Conversions and the curated table live in
`data/raw/new-build-cost-benchmarks/` (sha256 of each PDF pinned in the README
and in `scripts/data/fetch_cost_benchmark_sources.py`).

1. **Sargent & Lundy for EIA** — *Capital Cost and Performance Characteristics
   for Utility-Scale Electric Power Generating Technologies* (Jan 2024, 2023$;
   basis of AEO2025+). 19 reference plants, Table 1-2.
   <https://www.eia.gov/analysis/studies/powerplants/capitalcost/pdf/capital_cost_AEO2025.pdf>
2. **EIA AEO2026 EMM assumptions** (Apr 2026, 2025$) — Table 3 cost &
   performance (S&L learning-adjusted, technological-optimism factors, the
   only published US-agency **hydrogen-turbine** capex found) and Table 4
   regional overnight costs.
   <https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf>
3. **EIA AEO2025 LCOE/LACE report** (Jul 2025, 2024$) — capacity-weighted
   cost context for the same vintages.
   <https://www.eia.gov/outlooks/aeo/electricity_generation/pdf/AEO2025_LCOE_report.pdf>
4. **Lazard LCOE+ v18.0** (Jun 2025, 2025$) — investor-practice capital-cost
   ranges per tech; LCOS v10.0 storage assumptions; the CCGT
   **$2,400–2,600/kW market-quote** high case (footnote 7) documenting the
   2024-26 turbine-supply escalation.
   <https://www.lazard.com/media/uounhon4/lazards-lcoeplus-june-2025.pdf>
5. **Brattle 2025 CONE Report for PJM** (Apr 2025, nominal for 6/2028 online;
   Brattle + S&L bottom-up) — Gas CT / Gas CC / 4-hr BESS overnight costs per
   CONE area; documents CC CONE +44% real vs the 2022 review.
   <https://www.pjm.com/-/media/DotCom/committees-groups/committees/mic/2025/20250411-special/item-1-02-revised-cone-report-final.pdf>

Plus the pinned **NREL ATB 2024** extract already on disk
(`data/raw/nrel-atb/`, OEDI: <https://data.openei.org/submissions/6006>),
**extended this session with ATB's four EGS classes** (append parts 11-12).

Recorded but **not** independently re-fetchable from this environment
(`verified=0` in the table, excluded from the enforced envelope): DOE
*Pathways to Commercial Liftoff* next-generation-geothermal and LDES reports
(`liftoff.energy.gov` DNS-unreachable), PNNL-33283 storage assessment
(`pnnl.gov` PDF bot-walled). Flagged for browser re-verification — same
convention as FF-1E's 45Y/48E manual-download flag.

## 4. Per-technology grounding (operative values, 2026$)

Mid = the operative constant (`NEW_ENTRY_COSTS` / `STORAGE_TECHS` /
`OFFSHORE_WIND_PARAMS` / `GEOTHERMAL_PARAMS` / `HYDROGEN_TURBINE_PARAMS`);
envelope = the enforced literature range behind `TECH_COST_MULTIPLIERS` (entry
techs) or documentation (non-levered techs). Every point traces to a
`benchmarks_2026.csv` row with table/page citation.

| tech | mid $/kW (basis) | envelope $/kW | envelope edges set by |
|---|---|---|---|
| wind (onshore) | 1,676.6 (ATB Mod @2026) | 1,589 – 2,351 | low: S&L 2024 $1,489 (2023$); high: Lazard $2,300 (2025$) |
| solar (utility PV) | 1,562.2 (ATB Mod @2026) | 1,175 – 1,642 | low: Lazard $1,150; high: ATB Conservative |
| gas_cc | 1,583.3 (ATB Mod @2026) | 927 – 2,657 | low: S&L H-class 2×1 $868 (NOAK EPC basis); high: Lazard CCGT market quotes $2,600 |
| gas_ct (frame) | 1,428.7 (ATB Mod @2026) | 892 – 1,482 | low: S&L H-class frame $836; high: Lazard peaking $1,450 |
| gas_cc_ccs (95% cost proxy) | 3,104.7 (ATB Mod @2026) | 2,524 – 3,227 | low: S&L CC+95% $2,365; high: ATB Conservative |
| nuclear_large | 8,309.0 (ATB Mod @2030) | 7,060 – 15,146 | low: ATB Advanced; high: Lazard $14,820 (Vogtle-level) |
| nuclear_smr | 10,527.6 (ATB Mod @2030) | 7,000 – 13,834 | ATB Advanced / ATB Conservative (AEO26 + S&L interior) |
| storage li-ion 4 hr | 1,810.3 (ATB Mod @2026) | 577 – 2,272 (doc) | low: Lazard LCOS EPC-scope; high: ATB Conservative (Brattle $1,750-1,980 interior) |
| storage li-ion 8 hr | 3,154.3 (ATB Mod @2026) | ATB cases ±25% (doc) | no independent 8-hr point published |
| storage li-ion 12 hr | 4,498.4 (ATB linear split @12 h) | derived, see note | ATB's exactly-linear $/kW-power + $/kWh-energy structure |
| offshore fixed-bottom | 6,312.3 (ATB Mod Class3 @2026) | 3,689 – 6,691 (doc) | low: S&L monopile; high: Lazard $6,550 |
| offshore floating | 10,243.8 (ATB Mod Class12 @2030) | ATB-only (doc) | no independent US floating point published |
| geothermal EGS | 5,000 (DOE Liftoff level, verified=0) | 4,500 – 16,168 (doc) | low: DOE Liftoff current projects; high: ATB Deep-EGS Binary |
| hydrogen CT | 1,499.0 (ATB gas_ct × AEO26 premium 1.0492) | single published point | AEO2026 EMM $1,215 (2025$) is the only agency H2-turbine capex |
| hydrogen CC | 1,661.2 (ATB gas_cc × AEO26 premium) | analog-derived | same AEO premium ratio on the CC host |

Reading the spread honestly (the point of a range): the **gas envelope is the
widest in relative terms** — S&L's $868/kW NOAK EPC basis and Lazard's
$2,600/kW market quotes are both real, current publications about the same
machine, differing in scope (EPC-only vs all-in developer) and market moment
(long-run equilibrium vs the present turbine queue). The mid deliberately
stays the ATB equilibrium value; scenario runs now span the whole published
range (`tech_cost_path="high"` prices a CCGT at ~$2,657/kW). For **batteries**
the divergence is scope: Lazard's low band is a minimal-BOS EPC estimate while
S&L/AEO/Brattle/ATB are all-in developer bases ($1,521–$2,272 in 2026$) — the
model's other techs are costed all-in, so the ATB all-in mid is the consistent
choice (the prior hand-set $1,140 was an EPC-scope number in an all-in model).
**EGS** carries the largest genuine disagreement (DOE Liftoff ~$5,000 post-
Fervo vs ATB's GETEM-based $9,500–16,200); the model sides with the more
current federal assessment for the level and takes ATB's EGS FOM (§1 of the
constants comment has the full argument), landing the screen LCOE at ~$66/MWh
— inside DOE's own $60–70/MWh 2030 corridor, a deliberate cross-source
coherence check.

### What this session changed (cost-vintage delta ledger, 2026$)

| constant | before → after | why |
|---|---|---|
| `TECH_COST_MULTIPLIERS` capex low/high (7 entry techs) | ATB-internal case ratios → literature-envelope ratios (e.g. gas_ct 1.0/1.0 → 0.6246/1.0372; gas_cc 0.9923/1.0076 → 0.5852/1.6783; nuclear_large high 1.554 → 1.8228) | ATB's near-year internal spread is degenerate for mature techs — an inert PB-1 lever that could not express the published 2024-26 gas escalation. Defaults (mid) unchanged. |
| `STORAGE_TECHS` li_ion_4hr | capex 1,140 → 1,810.3; FOM 30 → 40.9 | hand-set EPC-scope value replaced by the derivation-locked ATB all-in basis (the committed battery rows were on disk but never read); consistent with S&L $1,744 (2023$), AEO26 $1,521 (2025$), Brattle $1,750–1,980 (2028 nominal) |
| `STORAGE_TECHS` li_ion_8hr | capex 2,280 → 3,154.3; FOM 48 → 73.4 | same |
| `STORAGE_TECHS` li_ion_12hr | capex 3,100 → 4,498.4; FOM 10 → 105.8 | same, via ATB's exactly-linear duration split; the old FOM (below the 4-hr's!) was internally inconsistent |
| `OFFSHORE_WIND_PARAMS` fixed_bottom | capex 4,200 → 6,312.3; FOM 80 → 89.7 | FF-1E-flagged re-derivation: old value sat below every published fixed-bottom point |
| `OFFSHORE_WIND_PARAMS` floating | capex 5,500 → 10,243.8; FOM 95 → 79.0 | ATB Class12 @2030 (earliest year — same convention as nuclear); FOAK base then declines via the model's own learning |
| `GEOTHERMAL_PARAMS` egs | fom_kw_yr 0 → 163.4 (capex 5,000 kept, re-cited DOE Liftoff) | "FOM captured in VOM" was ~$8/kW-yr vs the $150–208 published EGS range; capex's old "NREL ATB 2024" label was decorative |
| `HYDROGEN_TURBINE_PARAMS` h2_ct / h2_ccgt | capex 1,400/1,800 → 1,499.0/1,661.2; FOM 12/15 → 33.4/43.2 | decorative citations replaced by ATB-gas-basis × AEO2026-measured H2 premium (keeps H2-vs-gas competition on one FOM scope) |
| `STORAGE_TECHS` iron_air / flow_battery / compressed_air | values unchanged; citations corrected (PNNL-33283 2022, DOE LDES Liftoff), `verified=0` flagged | primaries unreachable from this environment; old labels pointed at documents that don't carry those numbers |

Behavioral note: these are all forecast-only entry/screen inputs. Direction of
effect — storage, offshore, EGS-FOM and H2 all get *more expensive* (less
entry, matching the all-in bases the rest of the model uses); the PB-1 range
gets *wider* (honest published uncertainty). No backcast run can change (§7).

## 5. Where each constant is consumed

- `NEW_ENTRY_COSTS` + `TECH_COST_MULTIPLIERS` → `config.scenarios.
  resolve_new_entry_costs` → `model/capacity.py::compute_lcoe` (entry screen)
  and the Wright's-Law trajectory.
- `CCUS_PARAMS["gas_cc_ccs_90"]` → `capacity._emerging_lcoe` (operative
  new-build CCS screen; equality with `NEW_ENTRY_COSTS["gas_cc_ccs"]`
  test-asserted since FF-1E).
- `STORAGE_TECHS` → `model/storage.py` value-stack screen (annualized capex +
  FOM vs arbitrage + capacity value; `capex_per_kwh` drives the degradation
  term).
- `OFFSHORE_WIND_PARAMS` / `GEOTHERMAL_PARAMS` / `HYDROGEN_TURBINE_PARAMS` →
  `capacity._emerging_lcoe` availability-year-gated screens.
- Capacity-market prices: `MARKET_DESIGN` net-CONE anchors + vintaged demand
  curves (ISO-published auction parameters; out of this session's scope, see
  §2).

## 6. Known gaps / flagged follow-ups

1. **Regional capital-cost multipliers** — every ISO sees the same national
   cost. The AEO2026 EMM Table 4 (25-region overnight costs, incl. TRE/ISNE/
   NYUP/NYCW/PJM*/MIS* mappable to this model's ISOs) is committed in the
   benchmark datatype as the source if an owner-approved session wires a
   per-ISO multiplier. Until then this is a documented departure from
   EIA/IPM/ReEDS practice.
2. **`verified=0` rows** (DOE Liftoff EGS/LDES, PNNL storage) need a
   browser-access session to re-fetch primaries; until then they are
   documentation-only and the EGS capex level carries that caveat.
3. **Per-tech WACC** (`ATB_TECH_WACC_REAL`) remains default-off pending the
   FF-2D owner decision (PTC/ITC double-count interaction — FF-1E §3).
4. **No storage capex lever**: `tech_cost_path` does not scale `STORAGE_TECHS`
   (the lever covers `NEW_ENTRY_COSTS` techs only). The 4-hr literature
   envelope is published here and in the benchmark table should a PB lane wire
   one.
5. **FOM ranges** are documented in the benchmark table but not levered (the
   PB-1 lever scales capex + learning only) — unchanged from FF-1E.
6. **base_cf / heat-rate cross-checks** (e.g. AEO2026's H2-turbine 8,295
   Btu/kWh vs the model's DOE-based 9.5 MMBtu/MWh) are recorded in the
   benchmark rows but out of scope here (physics, not cost).

## 7. Verification

- `tests/test_cost_benchmark_envelope.py` (new, 12 tests): constants ==
  derivations; every mid inside its envelope; envelope ⊇ ATB cases; gas levers
  no longer degenerate; benchmark-table hygiene (provenance on every row;
  `verified=0` rows never enforce).
- `tests/test_atb_entry_cost_consistency.py`: FF-1E equality tests unchanged
  for `NEW_ENTRY_COSTS`/`CCUS_PARAMS`; the multiplier test now asserts
  bracketing of the ATB-internal ratios (exact equality moved to the envelope
  test).
- Affected suites green: `test_storage.py` + `test_capacity.py` +
  `test_emerging_tech.py` + `test_config.py` + `test_uncertainty.py` (323 + 64
  passed; the 3 `test_matrix.py` failures are pre-existing in this environment
  — missing gitignored `data/clean/confirmed-retirements`, identical on the
  base tree).
- Backcast byte-identity + forecast smoke: recorded in the session log /
  handoff (`docs/handoffs/capacity-cost-grounding-2026-07.md`).

## 8. Maintenance rules

- Re-derive **only on a source update** (a new benchmark document, an extract
  extension), never on a residual (CLAUDE.md rules 13/23). Each change lands
  as: new/updated `benchmarks_2026.csv` rows (append; never silent edits) →
  re-run `derive_cost_benchmark_envelope.py` → paste the printed blocks into
  `constants.py` → tests assert equality.
- New sources must arrive through the QA protocol: download the PDF, pin its
  sha256 in `fetch_cost_benchmark_sources.py`, convert to markdown, commit the
  conversion (full or key-table extract), transcribe with page/table refs,
  set `verified=1` only for numbers read back from the committed conversion.
- The mid anchor moves only on an ATB-successor decision (owner call — there
  is no newer ATB today); envelope edges move whenever a verified source
  publishes outside the current range.

# PREREG miso-186 — the MIDWEST-STACK SCARCE-HOUR DIRECTION DIAGNOSIS: which formation input makes the keeper run the RDT backward?

**Session miso-186 (2026-08-25).** Registered **BEFORE any adjudicating
quantity is computed.** Executes the queue head installed by miso-185
(`FINDING-miso185-south-firm-export-evidence-hunt-2026-08-25.md` §6, matrix
§5.4 stamp miso-185): the last non-owner-decision road at the C3a-2025 queue
head — diagnose WHY the keeper runs the RDT **N→S** in its 2025 scarce hours
(9/47) where the measured record ran **S→N at the limit** (32/47 any-row,
9/47 majority; N→S 0/47 — 0/72 across all three years). Object-first; **NO LP
is spent unless this document's own mapping licenses the conditional A/B**
(deliverable (a)); a negative is a result (deliverable (b)).

Keeper `2026-08-22-miso-177-rho-measured` (`miso177_rho_B`); determination
NOT-YET on C3a-2025 alone, C3c the single ledgered caveat. **Mechanism-in-kind
boundary (named now so rule 26(b) is decidable):** the decomposition itself
tests NO mechanism — it is a formation-input measurement over committed
artifacts and in-repo measured series, so **no cell is minted by the
diagnosis alone** (the miso-182/183 no-cell precedent). A cell IS minted iff
the conditional repair is licensed and its A/B runs (verdict V-INPUT): the
repair's mechanism-in-kind is then named from the winning leg (§6) and its
cell carries the A/B outcome (K/R/I), with any new `ScenarioConfig` field
adding its matrix row + a cell line in every shard in the same push (duty
26(c)).

## 0. What has been looked at, and what has not (the pre-registration boundary)

Before writing this document the session read only:

* **Committed prior findings, preregs, and probe sources** and their committed
  values (miso-156/161/167/174/177/178/179/180/182/183/184/185) — every prior
  statistic quoted below is restated from those documents, not re-derived.
* **Code (no measured statistic computed):**
  `config/iso_configs.py` (the 6-zone MISO topology; the RDT encoded as the
  one-way pair MISO-Plains→MISO-South 3,000 MW / MISO-South→MISO-Plains
  2,500 MW; MISO-South carries no CIL group);
  `data/eia930/zonal_shares.py` + `scripts/data/curate_zonal_shares.py` (the
  MISO zonal demand path: measured EIA-930 sub-BA hourly demand
  `zone-specific-demand/MISO/miso_subba_demand_2023-2025.csv`, sub-BA 8910 →
  MISO-South, UTC→local mapping via the MISO hourly frame, clean-parquet
  primary with byte-identical raw fallback, static `load_share` only when
  both fail);
  `data/fuel/basis/miso.py` + `basis/meanzero.py` call signatures (the armed
  `miso_zonal_gas_basis`: capacity-weighted MEAN-ZERO annual per-zone shifts
  from `miso_zonal_gas_hub.csv`; the winter-citygate overlay is Dec/Jan/Feb
  only — inert in the summer scarce set);
  `model/interchange/spec.py` (registered `MISO_SEAM_LADDER_BY_YEAR` values;
  2025 South import `(68.46, 87.90, 121.12, 155.42, 258.05, 327.25, 433.12,
  433.12)`, export `(53.00, 44.14, 37.04, 32.38, 29.43, 26.61, 24.29,
  22.35)`; the South `NeighborInterface` spec);
  the offline rebuild machinery this probe reuses byte-for-byte:
  `scripts/probes/_miso156_c3a_decomposition.py::model_year` (+ its
  `_miso134` `build_year`/`keeper_config` imports) and the miso-178 wrapper's
  BUNDLE-repoint pattern (`scripts/probes/_miso178_c3a_decomposition.py`).
* **Registered input-value tables** (the miso-184 §0 "registered ladder
  VALUES" class — constants, not statistics): `data/raw/miso_zonal_gas_hub.csv`
  (2025 rows: South +0.343 Gulf Coast (LA, 6/12-month construction note);
  Illinois/Indiana/East +0.018 Chicago Citygate; West/Plains −0.585 MidCon,
  MN withheld) and the keeper's `run_config.json`/`meta.json` armed-field
  surface (notably: `miso_zonal_gas_basis`, `miso_zonal_reserves`,
  `miso_reserve_pergen`, `miso_reserve_online_gated` + measured rho no-floor,
  `miso_measured_reserve_requirements`, `miso_south_seam_split`,
  `miso_rdt_tcdc`, `miso_rpe_pricing`, `miso_seam_measured_ladder`,
  `miso_firm_imports`, `outage_source=historic`, `unit_outage_short_windows`,
  `unit_outage_maxgen_events`, `summer_derate_basis_aware`,
  `summer_wefor_share_override=1.0599`, `coal_mustrun_per_plant`,
  `st_gas_mustrun_per_plant`, `reliability_floor`, `gas_offer_margin`,
  `temp_dependent_derate` (CHP classes only)).
* **Schemas ONLY** (column names / key values, no data statistics):
  keeper sidecars (`system_*`: year/pass/zone/hour/price/slack/dump/demand/
  reserve_price, zones = the 6 carry zones + `MISO_external` +
  `MISO_external_South`; `class_hourly_*`: year/pass/klass/hour/mw — **no
  zone column**, 17 klasses; `reserve_family_*`: family/reserve_class/zones/
  hour/dual/requirement_mw/held_mw/shortfall_mw, families
  `miso_rbdc`, `miso_rbdc_regspin`, `miso_subregional_or_midwest`,
  `miso_zonal_or_miso_south`);
  `data/raw/miso-regional-balance/miso_regional_load_<y>.csv.gz`
  (market_date/he_est/region/mtlf_mw/actual_mw) and
  `miso_regional_genmix_<y>.csv.gz` (market_date/he_est/region/fuel/mw);
  `zone-specific-demand/MISO/miso_subba_demand_2023-2025.csv`
  (period/subba/value).
* Environment facts: 15 GB RAM / 4 cores; the miso-169 memory recipe for any
  licensed A/B (8 GB swapfile, `MARKET_SIM_HIGHS_THREADS=4`, ~13 GB peak).

**No statistic over any measured hourly series has been computed for this
session.** The committed miso-174/177/178/182/183/184/185 statistics quoted
here are prior sessions' committed numbers, restated not re-derived.

## 1. The object (committed; restated) and the a-priori formation frame

The committed, basis-free object (miso-183 V-TRADE; the retired pool-basis
+1.19 is never quoted as a size): measured South boundary-complex scarce
outflow **−2.441 GW** (2025, 47 h; conservative floor ≥0.93 GW) vs keeper
≈ **+0.35 GW INTO the South** (interval mid); measured RDT **S→N binding
32/47** (≥1 five-minute row; 9/47 at the ≥6/12 majority) and **N→S 0/47** vs
keeper **N→S 9/47, S→N never** (the miso-183 spread classifier on the
committed sidecars). The export-price half of the residual is adjudicated
(miso-184 V-DEFECT-COUPLING, GAP +1.272 GW, no admissible rebasis); the firm
export's driver data does not exist (miso-185 V-NEG-ABSENT); the offer family
is exhausted at both grains (miso-179 level `R`, miso-180 spread `I`). What
was never diagnosed as its own charter is the **upstream internal-direction
object**: the keeper's Midwest stack manufactures SOUTHWARD pressure in the
very hours reality ran the wheel the other way (miso-178 §2 mechanism
reading; miso-183 §5 second half). The standing falsifiable prediction ANY
candidate must carry: **it must flip the keeper's scarce-hour RDT direction
toward the measured S→N record.**

**The formation frame, declared before measurement.** In a deterministic
nodal LP the scarce-hour RDT direction is decided by the sign and depth of
the South's *economic surplus at the Midwest clearing price*. Define, for
scarce hour `t` (all terms computable OFFLINE — committed sidecars + the
`model_year` input rebuild — no LP):

* `π_MW(t)` — the committed keeper P1 Midwest price (MISO-East; the Midwest
  is a verified copper plate: max intra-Midwest spread 0.0000 in all hours,
  miso-183 footing (b)).
* `D_S(t)` — the committed keeper MISO-South demand (sidecar).
* `R_S(t)` — the committed held reserve of the `miso_zonal_or_miso_south`
  family (sidecar `held_mw`).
* `EconCap_S(p, t) = Σ_{g ∈ South} pmax_g · avail_g(t) · 1[mc_g(t) ≤ p]`
  over the rebuilt keeper fleet inputs (thermal + hydro classes), **plus**
  the South's renewable availability `cf(t) × cap` (wind, solar — MC = 0 so
  they enter at every `p`).
* The model's **economic South surplus**
  `H_econ(t) = EconCap_S(π_MW(t), t) − R_S(t) − D_S(t)` and its **physical
  ceiling** `H_cap(t) = EconCap_S(∞, t) − R_S(t) − D_S(t)`.
* The measured counterpart `H_meas(t) = G_S(t) − L_S(t)` (sr_gfm South
  generation minus rf_al South actual load — the miso-183 Leg-2
  construction; scarce-mean **+2.441 GW** committed). `H_meas` is a FLOOR on
  the real South's surplus capability: the real wheel bound at its S→N limit
  in most of these hours, so unobserved headroom above the limit only
  strengthens the contrast.

If `H_econ ≤ 0` the model **cannot** run the wheel S→N whatever every
downstream seam mechanism does; the diagnosis is the decomposition of
`H_meas − H_econ` into named formation inputs, each scored against its own
measured source. The a-priori arithmetic making this frame falsifiable: the
real South held ≥ 2.4 GW of surplus at an own-price of roughly $37–42 (the
committed miso-178 §2 zonal record: actual South lw 37.31, the cheapest
zone), i.e. **far below** the keeper's committed scarce Midwest price — so a
South stack whose availability, load and marginal costs matched the measured
record would export S→N *even at the keeper's under-priced Midwest tail*
($110–227 committed range). The direction error therefore CANNOT be wholly
downstream of the adjudicated tail-depth miss; some South-side (or
load-split) formation input must deviate, and this session measures which.

## 2. The instrument (frozen construction)

One read-only probe, `scripts/probes/_miso186_direction_decomposition.py` →
`results/calibration/_miso186_direction_decomposition.json`, committed
**after this PREREG and before it is run** (the miso-184 order). Frozen
constructions:

* **Hour sets** — the miso-174/178/183/184 masks verbatim: `annual`;
  `summer` (Jun 1–Sep 30); `scarce` = summer ∩ hub RT > $200 from
  `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`
  (n = 11/14/47 in 2023/2024/2025, reproduced as footing gate F-1).
  **2025 is load-bearing** (the charter object); **2023 concurrence
  reported; 2024 reported-only** (the disclosed EIA-930 substrate year —
  the miso-183 treatment).
* **Model side** — the miso-156 `model_year` rebuild repointed to
  `miso177_rho_B` exactly as `_miso178_c3a_decomposition.py` repoints it
  (BUNDLE + `V1_PUBLISHED_C3A = {2023: +1.2813, 2024: −4.0643,
  2025: −11.7421}` in fraction units as committed there), with its V1/V2/V4
  gates as footing (F-2). `mc_g(t)` is the rebuilt `mc_base` (the bid basis;
  the P1 startup adder is reported separately where the marginal-identity
  table needs it, never silently added). South membership =
  `zone_of == index(MISO-South)`. Renewables from
  `load_renewable_profiles("MISO", year, …)` restricted to the South zone
  row.
* **Measured side** — `miso_regional_{load,genmix}_<year>.csv.gz` aligned to
  local hour-of-year by the **miso-183 probe's own construction verbatim**
  (`_miso183_south_basis_decomposition.py`: market_date + he_est on the
  non-leap clock, Feb-29 dropped, ±1h shift sensitivity reported); regions:
  South, Midwest = North + Central. Model-vs-source sub-leg: the sub-BA CSV
  re-aggregated through `parse_miso_shares`' own code path (import, not
  re-implementation).
* **Fuel-family crosswalk (fixed now):** model klass → family:
  {COAL_BIT, COAL_LIGNITE, COAL_PRB} → Coal; {CC_CHP, CC_REGULAR, CT_CHP,
  CT_PEAKER, ST_CHP, ST_GAS} → Gas; nuclear → Nuclear; hydro → Hydro;
  wind → Wind; solar → Solar; {biomass, oil, OTHER} → Other. The genmix
  file's own fuel labels are mapped by case-insensitive name match; any
  unmapped label is reported and carried in Other, never dropped silently.
* **Price sensitivity rows (fixed now):** every `EconCap_S`/`H_econ`
  statistic is computed at `p = π_MW(t)` (load-bearing) and reported at
  `p = π_MW(t) + $25` and `p = $479` (the committed 2025 scarce actual mean,
  restated from miso-184 §... PREREG §1) — sensitivity only, no gate hangs
  on them.
* All GW quantities are scarce-set means unless labelled; surplus-positive
  sign (`H > 0` = exportable). Row coverage (overall and within the scarce
  set) is reported per leg; a missing input drops its leg with the
  deficiency disclosed — never patched ad hoc.

### Stage F — footing (STOP gates, not verdicts)

* **F-1:** scarce-set sizes reproduce 11/14/47.
* **F-2:** the repointed rebuild passes miso-156's own V4 (fleet count), V2
  (floor reproduction) and V1 (C3a within ±0.02 pp of the registered values)
  in all three years. Any failure → STOP, instrument bug, report.
* **F-3 (the object's own footing):** the miso-183 spread classifier
  (spread = P1 `price(MISO-South) − price(MISO-East)`; N→S ≡ spread > +$1;
  S→N ≡ spread < −$1; RPE dead band ±$1) reproduces the committed 2025
  scarce composition: N→S 9/47, S→N 0/47, unconstrained 38/47.
* **F-4 (the measured side's footing):** the rf_al/sr_gfm construction
  reproduces the committed miso-183 `N_S` scarce means to ±0.02 GW
  (2025: −2.441; 2023: −1.438; 2024: −2.222; sign flip: `H_meas = −N_S`).

### Leg L — load alignment

`ΔD(t) = D_S(t) − L_S(t)` (scarce mean, GW; positive = the model gives the
South MORE load than measured in exactly the hours that decide the
direction), split additively into:

* **ΔD_wiring** `= D_S − D_S^930` — the model's committed South demand vs
  its OWN source re-aggregated (the sub-BA 8910 series × the same
  UTC→local mapping, × the committed sidecar MISO total). Nonzero beyond
  numerical tolerance = a wiring defect (share construction, clock, fallback
  silently active).
* **ΔD_source** `= D_S^930 − L_S` — EIA-930 sub-BA metering vs MISO's own
  rf_al actuals. The whole-MISO wedge (930 total vs rf_al MISO total) is
  reported alongside (the miso-183 wedge discipline: reported, never
  apportioned beyond the whole-MISO calibration).

Reported for every year and every hour set; the Midwest mirror
(`D_MW − L_MW`) alongside (the split must close: a South-high error is a
Midwest-low error by construction of shares).

### Leg A — availability vs the measured record (per fuel family)

Per family `f`: model South available capacity `Cap_f(t) = Σ pmax·avail`
(renewables `cf × cap`) vs measured South generation `G_f(t)` (sr_gfm).
`ΔA_f(t) = max(0, G_f(t) − Cap_f(t))` — generation reality produced that the
model's availability inputs cannot produce **at any price**. `ΔA = Σ_f ΔA_f`
(scarce mean). Where a family fires (declared line: scarce-mean
ΔA_f ≥ 0.10 GW), the probe drills to the unit grain: the South units of that
family with `avail < 0.95` in scarce hours, their availability source
(CAMPD outage window / derate / layup mask), listed with plant ids — the
repair-candidate evidence. The Midwest mirror `ΔA^MW` is reported (an
availability error that inflates the MIDWEST stack is direction-relevant
with the opposite sign).

### Leg M — the mc-idled capacity and the marginal-identity table

`Idle_S(t) = EconCap_S(∞, t) − EconCap_S(π_MW(t), t)` — South capacity
available but priced above the Midwest price — reported per class with its
capacity-weighted mc distribution (p10/p50/p90) inside the scarce set, and
each class's mc COMPOSITION at its p50 unit: delivered fuel price (incl. the
zonal basis increment), heat rate, VOM, offer multiplier, adders. Alongside,
the **marginal-identity table** (the charter's "Midwest marginal-class
identity and offer basis vs South's"): per scarce hour, the class whose mc
band brackets `π_MW(t)` (the miso-156 identity construction) and the same
for the South price; summarized as class-frequency tables, model, with the
measured story restated from committed findings for contrast (real South
≈ $37–42 gas-CC-marginal; real Midwest $479 scarcity-priced). A class's
idled capacity is attributed to the mc COMPONENT that would have to move to
clear `π_MW` (the smallest single-component move, computed per class:
Δfuel-price in $/MMBtu, ΔHR, Δmultiplier), so the leg names WHICH input a
repair would touch — the admissibility screen (§4) then decides whether that
input is repairable at all.

### Leg R — reserve withholding (report-only)

Scarce-mean `R_S` (held), requirement, dual and shortfall of
`miso_zonal_or_miso_south`, with the Midwest families alongside. Report-only:
a reserve-requirement change is adjudicated refused (miso-178 §8, rule 14 —
the model already holds 7.06 GW vs 2.62 cleared in the scarce set), so this
leg can contextualize `H_econ` but never name a candidate.

### Leg S — the seam context (report-only)

The registered South import/export band prices vs the committed scarce
`π_S(t)` and the miso-174/184 committed seam statistics, restated: how much
external supply the model's South receives in scarce hours by construction
of the registered ladder. NAMED at miso-184 §4 as the import-side mirror;
**not this session's lever** (charter) — reported for the balance
arithmetic only.

### The decomposition statement

The headline table (per year, scarce mean, GW): `H_meas`, `H_cap`, `H_econ`,
and the bridge `H_meas − H_econ = ΔD + ΔA + Idle_S-consumed + ΔR-context +
residual`, where each term is the leg's own scarce mean and the residual
(coverage, wedge, nonlinearity of the hourly indicator) is named and
reported, never absorbed. Exact additivity is NOT claimed a priori — the
bridge is reported with its residual at full magnitude; the verdict (§4)
hangs on the LEGS' own lines, not on the bridge closing.

## 3. Anti-sweep (binding)

The hour sets, the `H` constructions, the price sensitivity rows, the
fuel-family crosswalk, the ΔD wiring/source split, the per-leg firing lines
(ΔA_f ≥ 0.10 GW; the §4 materiality line 0.25 GW; the §4 tolerance lines),
the verdict mapping and the candidate selection rule are **frozen by this
document**. No alternative set, statistic, or threshold may be computed
after seeing a result, and none may be quoted from this session.
Reported-only statistics (Legs R and S, the sensitivity rows, the Midwest
mirrors) never migrate into a gate. A result against interest is reported at
full magnitude. If any input turns out missing or deficient, the affected
leg is dropped with the deficiency disclosed — never patched ad hoc.

## 4. Admissibility lines and the verdict mapping (frozen)

**A formation-input deviation becomes a NAMED REPAIR CANDIDATE only if ALL
five clauses hold:**

* **(i) Measured-source deviation.** The model's input deviates from a
  measured, in-repo (or already-authorized-intake) source: a wiring/data
  defect (the neiso-86 class), or an estimate standing where measured data
  exists (rule 14). A *preference between two defensible measured
  constructions justified by the residual* does not qualify.
* **(ii) Forward regenerability** (rule 13): the repaired input regenerates
  for a forward year from forward drivers and responds to changed
  conditions.
* **(iii) Family not adjudicated.** The repair's mechanism family is not
  `R`/`I`/`G` in MISO's shard. In particular: NO offer-multiplier move
  (miso-179/180, both grains), NO seam-ladder re-derivation or rebasis
  (miso-184), NO reserve-requirement change (miso-178 §8), NO interface
  limit change (`measured_interface_limits` `R`), nothing on the §7 list.
* **(iv) Rule 23.** If the input is a derive-script output or registered
  constant, the repair requires a source-data change or an adjudicated
  methodology/construction defect (the miso_zonal_gas_hub 2026-07-12
  mismatched-window repair is the model precedent), never the residual.
* **(v) Direction relevance and materiality.** The repair's OFFLINE static
  reach — the scarce-mean increase of `H_econ` computed by re-evaluating the
  affected term with the repaired input — is **≥ +0.25 GW** in 2025 (a
  quarter of the miso-183 conservative floor, comfortably above the
  PREREG-miso184 S-3 line of 0.1 GW), with 2023 reach reported (a candidate
  whose 2023 static effect exceeds +1.0 GW is flagged for the S-5 band risk,
  reported not killed).

**Candidate selection if several clear:** largest 2025 static reach; exact
tie → the earlier leg in the order L(wiring), L(source), A, M(fuel-price),
M(heat-rate). Selection is on the formation metric, never on any LP or
price residual.

**Conditional repair shapes (declared now, built only under V-INPUT):**

* **L-wiring:** fix the identified defect in the sub-BA share path (exact
  bytes; zero parameters; a code/data repair, no `ScenarioConfig` field).
* **L-source:** replace the South share numerator with the measured MISO
  rf_al construction: `share_S(t) = rf_al_South(t) / rf_al_MISO(t)`, the
  remaining `1 − share_S` allocated across the five Midwest zones
  proportionally to their EIA-930 sub-BA shares (both numerator and
  denominator on MISO's own metering basis — no cross-basis mixing); gated
  MISO-only `ScenarioConfig` field, default off, zero fitted parameters.
* **A:** correct the specific availability input row(s) shown to contradict
  the measured record (an outage window / derate / layup mask a unit's own
  metered generation falsifies), citing the source data (rule 23).
* **M-fuel:** repair only under an adjudicated CONSTRUCTION defect in the
  published basis row or hub assignment against its own cited source —
  never "a different hub fits the spread better".
* **M-multiplier: REFUSED by clause (iii)** — any Idle_S mass attributed to
  offer multipliers is V-FORMED territory (the family is exhausted), and is
  reported as such.

**Verdict mapping:**

| verdict | pre-registered condition (2025) | consequence |
|---|---|---|
| **V-INPUT(name)** | ≥1 leg deviation clears clauses (i)–(v) | The named repair is built (zero fitted parameters) and the conditional A/B RUNS IN THIS SESSION on the **PREREG-miso184 §6 gates VERBATIM** (§5 below). Cell minted from the A/B outcome; registration + stamps regardless of outcome. |
| **V-FORMED** | every leg's model input matches its measured source within the declared lines (no deviation ≥ the materiality line clears (i)) | The direction error is jointly produced by already-adjudicated mechanisms — the honest negative. NO arm, NO LP. The finding hands the owner the D-4 posture decision with the ~1.3 GW scarce-export model-class concession (miso-184 GAP +1.272) as the residual; the remaining owner roads restated (state-conditioned export mechanism-in-kind — miso-185 is affirmative evidence FOR it — and the ledgered concession). |
| **V-BLOCKED(name)** | a deviation ≥ 0.25 GW static reach exists but fails a named admissibility clause | Reported at full magnitude with the failing clause named; NO arm; owner escalation (whether an intake or charter could make it admissible is the owner's call, not this session's). |
| **MIXED** | any component pattern satisfying no row | Full magnitude; no threshold moved; owner escalation. |

## 5. The conditional A/B (only under V-INPUT; the miso-184 §6 gates VERBATIM)

Control and arm are `replay_keeper` replays of `miso177_rho_B` at HEAD, run
SEQUENTIALLY (rule 12; miso-169 recipe: 8 GB swapfile,
`MARKET_SIM_HIGHS_THREADS=4`), each the FULL span `--year 2023 2024 2025` in
ONE invocation (rule 16), out-dirs `results/calibration/miso186_dir_A`
(control) / `miso186_dir_B` (arm), registration ids
`2026-08-25-miso-186-control` / `2026-08-25-miso-186-<candidate>` — **BOTH
registered whatever the outcome** (rule 15). Gates, carried verbatim from
PREREG-miso184 §6 with only the run names updated:

* **S-0 CONTROL INERTNESS (ABANDON):** every scored sidecar of the control
  value-identical to the committed keeper's; anything else ⇒ HEAD drift —
  STOP, report, no arm conclusion.
* **S-1 EXACTNESS (KILL):** the arm's `run_config.json` records exactly the
  single repair delta; every other input byte-identical between legs.
* **S-2 DIRECTION (structural gate):** the arm's 2025 scarce-hour N→S
  binding count under the miso-183 spread classifier must **FALL below the
  control's** (committed keeper: 9/47). Reported alongside, never gated:
  the S→N count (measured record: 32/47 any, 9/47 majority) and the full
  classifier composition, all years.
* **S-3 OUTFLOW (structural gate):** the arm's 2025 scarce-mean model South
  boundary-complex net inflow `N_S^m` — computed EXACTLY from each leg's
  full solve outputs (link `flows` into MISO-South, the seam-band net at
  `MISO_external_South` included), verified against the zonal energy balance
  (residual < 1 MW) — must move from the control's value **toward the
  measured −2.441 GW by ≥ 0.1 GW**.
* **THE CHARTER KILL:** an arm that improves C3a-2025 while BOTH S-2 and
  S-3 fail is a level adder wearing a repair's name → REJECTED regardless of
  every other number.
* **S-4 CONDUCT (KILL):** zero D-4 conduct failures on the arm's regenerated
  `legitimacy_diagnostics.json`, zero NEW vs the control; C8 PASS all years.
* **S-5 FULL-MAGNITUDE SCORING (report + escalation, NOT a kill):** the
  complete verdict scorer on both legs; movements outside the commercial
  band (±10 %) in 2023/2024, or any criterion PASS→FAIL flip, fire the
  owner-escalation path per the owner posture directive (*"if structural
  integrity improves but gates regress that may still be a keeper"* — the
  ercot-231 precedent), never an auto-reject and never an auto-keeper; a
  promotion additionally requires leave-one-year-out scoring within
  2023–2025 (rules 20/22) and the rule-21 DOF ledger entry.
* Registration + matrix stamp + calibration-log entry in-session regardless
  of outcome; a promotion re-stamps `keepers/MISO.json` and fires the
  calibration-keeper-auditor.

## 6. Mechanism-in-kind naming (under V-INPUT only)

The cell name follows the winning leg: L-wiring →
`miso_south_load_share_wiring`; L-source → `miso_south_load_share_measured`;
A → `miso_south_availability_repair`; M-fuel → `miso_south_gas_basis_repair`.
The base row + a cell line in every ISO shard land in the same push as any
new `ScenarioConfig` field (duty 26(c)); MISO's cell carries the A/B verdict,
the other five `·`.

## 7. DO-NOT-REDO and governance

**DO-NOT-REDO (miso-185 §9 carried in full):** `miso_south_firm_export_block`
`G` (re-open ONLY on contract-grain term×MW naming a MISO-South resource, or
a by-counterparty contract-path series — the EQR summary route is
EXHAUSTED); `miso_south_export_ladder_rt_tail` `R` (no variant, no composite
basis); `miso_seam_coincident_envelope` `R`; `measured_interface_limits` `R`;
`m2m_seam_entitlement_cap` `G`; `import_shape_lever` `G`;
`internal_congestion_split` `G`; `zonal_loss_surface` `R`; the within-unit
`measured_offer_surface` `R`; `gas_hub_basis_overlay` `R` (leg M-fuel is a
DATA-DEFECT screen on the armed zonal-basis input's own construction, not an
overlay mechanism, and builds nothing without an adjudicated construction
defect per §4(iv)); `ramp_envelopes` `I`; `dam_availability_rebasis` `R`;
the ordc/reserve and dispersion families; the offer family at BOTH grains
(miso-179/180; the `miso_offer_spread_anchored` unspent re-open clause
untouched — this session may not be cited as graft evidence). The miso-183
basis adjudication is CLOSED (V-TRADE) and not re-litigated; `ba_code="SOCO"`
stays a forecast-lane rule-14 item; the import-side ladder tail (miso-184
§4, ~+0.96 GW DA-driven scarce import) is NAMED, reported in Leg S, never
this session's lever.

**Governance.** Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 ONLY; MISO holds
neither marker (fail-closed); the spend freeze ACTIVE and untouched; no new
fetch of out-of-train market dates; no re-key owed. Rule 1 `[R-STRUCT]`: the
charter kill enforces it — no fitted adder can pass. Rule 12: any A/B legs
sequential. Rule 13/14: the admissibility clauses above are the binding
screen. Rule 15: engaged ONLY if the A/B runs (then both legs registered).
Rule 23: §4(iv). Rule 24: any repair that is a solve-affecting toggle lands
in `ScenarioConfig` + `run_config.json`. Rule 26: §5.4 queue stamp +
calibration-log entry in-session; cell/row duties per §6. Rule 27
`[R-PUSH]`: exact on-disk bytes; every pushed blob ≥300 lines verified. No
new `.github/workflows`. Owner decision points (D-4 posture; the promotion
call under a split verdict) restated in the finding, decided by the owner,
not here.

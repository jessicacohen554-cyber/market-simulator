# FINDING — capx D17: MISO's missing non-coal exit channel is ATTRIBUTED — the screen bar fails ~83 % of the thermal fleet, the adequacy requirement rations the exits, and the pre-S-123 requirement basis starved the non-coal channel; the S-123 repair already reaches a HEAD T1-H solve and the re-measure is the routed next step

**Lane:** capx D17 (r#22 relaunch), charter `docs/handoffs/capx-director-prompt-pack-2026-08.md`
§D17. **Precommit:** `PRECOMMIT-capx-d17-miso-exit-channel-2026-09-01.md`, pushed before any
measurement; the candidate threads, evidence plan (E1–E8), adjudication rule and kills below
are executed as frozen there. **Phase 0 only: ZERO solves** — every number is read from a
committed artifact or computed by evaluating committed code/constants on committed inputs.
No mechanism tested, no matrix cell, no board write. Collision check at start and at push:
clear (no MISO backcast branch in flight; no orphan D17 branch existed).

## 0. Verdict (one paragraph)

The adjudication lands on **outcome (B) of the frozen rule — the zero is
REQUIREMENT/CAP-SIDE — with thread (iii) CONFIRMED-PRIMARY**: in the exact run whose score
is the object, gas/oil units DO fail the screen bar en masse and are blocked at the
admission cap (`entry_capped` 93.0 GW in 2023, 105.5 GW in 2024 — §2), and the cap's
requirement basis was the pre-S-123 composite that S-123 measured as overstated. The
hindcast-window analogue, computed here for the first time: the corrected basis is worth
**≈ 14.7 GW of admission headroom at the 2024 screen** (≈ 11.2 GW requirement overstatement
+ 3.5 GW missing external accredited firm) — **3.7–4.3× the entire missing non-coal exit
target** (§4.1). Because all three S-123 operands are registry constants read by the same
`resolve_adequacy_requirement_mw` / `accredited_firm_capacity_mw` seam the admission cap and
execution floor call (verified on source, §4.1), **the repair is already shipped at HEAD**
and the committed FFR-2B/FFR-3A-3 numbers simply predate it — the routed PRIMARY next step
is a HEAD re-measure of the MISO T1-H leg, a solve this lane does not run. Beneath it sits a
structural CONTRIBUTING cause with the sign OPPOSITE to the charter's thread-(i) phrasing:
the margin side does not over-reward gas/oil — it **under-rewards nearly everything** (the
bar fails ~118.5 of 142.6 GW of screened thermal in 2024), chiefly because the modelled
capacity-revenue leg pays **$0 at every long reserve position** (RBDC zero-cross at 1.05;
$0 on every committed capped row, §4.2) while MISO's real PRA cleared small positive prices
in the same years. A screen that fails ~everything cannot discriminate the 3.9 GW that
actually left from the ~70 GW that stayed; the realized exit composition is then an artifact
of the rationing mechanics (worst-first depth under the pipeline rule → all coal; per-fuel
counters under the legacy rule → 12.9 GW of gas_st), not of unit economics (§5). Threads
(ii) and (iv) are REFUTED-as-cause and CONTRIBUTING-bounded respectively (§4.3–§4.4). Per
the precommit's K7, no tuned constant is proposed anywhere below.

## 1. The object, and a measurement-vintage seam that must be recorded

The object (D3 §5, from the committed FFR-2B pipeline-arm score
`results/hindcast/miso-2021-2025-cmc-pipeline-ffr2b/MISO/0a4455fd0d642364/score.json`):
model gas_ct/gas_cc/oil exits 0.0 GW against actual 2.435/0.521/0.502, coal +9.1 %, total
−16.5 % FAIL.

**Seam (disclosed, not adjudicated):** the committed scoring target
`data/raw/_validation-source/capacity_actuals_miso.csv` landed on main 2026-08-30
(PR #4387, header "Built 2026-08-07") — AFTER every scoring that produced the object's
numbers (FFR-2B 2026-08-02, FFR-3A-3 2026-08-04). On the CURRENT committed target the
actual thermal exits are **17.37 GW**, with **gas_st a separate fuel**: coal 12,434.1 /
gas_st 2,127.5 / gas_cc 857.9 / oil 542.8 / gas_ct 398.7 MW (+ nuclear 811.8, biomass
196.4). The 2026-08-02-era target behind "actual 15.227 / gas_ct 2.435 / coal 10.934" is
not recoverable from HEAD-committed artifacts (the CSV's visible history begins at its
2026-08-30 landing). Two consequences, reported at full magnitude and ROUTED (§6 R4), not
resolved here: (a) the non-coal fossil target is **3.93 GW on the current basis** (vs the
scored 3.458) — the ZERO is vintage-independent; (b) the "over-retires coal +9.1 %" half of
D3's framing is vintage-DEPENDENT: against the current target the model's 11.932 GW of coal
reads **−4.0 %** (slightly under). Nothing in this finding rests on which coal sign is
right; the missing non-coal channel is the object under both vintages.

The actual non-coal cohort itself (current target, thread-(ii) evidence): **161 units,
median 2 MW** — three large gas steamers ≥300 MW (Baxter Wilson 1 544.6, R S Nelson 1
445.5, Ninemile 3 348.5) plus a long tail of tiny oil/gas peakers (oil: 103 units, 542.8 MW
total). MISO's confirmed registry carries **no gas/oil row at all** (4 live rows, all
Monroe coal, instrument dates 2022–2023 > the 2020 vintage cutoff — none reachable in
T1-H), so the whole 3.9 GW is the ECONOMIC screen's to produce. It produced none of it.

## 2. Step 1 of the frozen rule — where the zero happens: outcome (B)

From `results/hindcast/ffr2b-miso-compare.json` (E1), the pipeline leg — the exact run the
score measures:

| year | decided | entry_capped | re_confirmed | executed | reversed |
|---|---:|---:|---:|---:|---:|
| 2021 | — | — | — | — | — |
| 2023 | 1,105.3 | **93,016.7** | 11,931.6 | — | — |
| 2024 | 901.0 | **105,542.9** | 13,037.0 | 11,931.6 (all coal) | — |
| 2025 | — | — | — | — | 2,006.3 |

In 2024 the failing set is 105,542.9 capped + 13,037.0 pipelined + 901.0 decided ≈
**119.5 GW of a 142.6 GW thermal fleet (~83 %)**. Per-fuel event rows for the hindcast
window are not committed (the compare record aggregates; the only pipeline-rule hindcast
ledgers, `miso-2021-2023-t1ff-armr-ffr3vfix-*`, carry a single empty 2021 — precommit K1
partially bites and §6 R1 routes the enriched re-measure), so the per-fuel claim is
established by ARITHMETIC BOUND from the committed fleet composition
(`fleet_by_fuel`, cmc-probe/ffr3vfix ledgers: gas_cc 31.2–32.4, gas_ct 24.0–24.4, gas_st
13.9, oil 3.5 GW): the not-failing residue in 2024 is 142.6 − 119.5 = **23.1 GW**, so even
crediting ALL of it to gas/oil, **≥ 51 GW of the ≈ 74 GW gas/oil fleet failed the bar and
was entry_capped**. Gas and oil are not passing the screen — they are refused admission.

Outcome (C) does not obtain (ledger and score agree: cumulative econ = coal 11,931.6 only),
and outcome (A) is refuted by the bound above. Two committed corroborations: (1) the 2025
`reversed` 2,006.3 MW is exactly the 2023+2024 decided cohorts (1,105.3 + 901.0) — admitted
units (fuel not committed) that never executed (blocked at the execution-time reliability
floor, which shares the SAME requirement) and then re-cleared the bar in 2025; (2) in the
committed POST-S-123 forecast ledgers (`results/ff-t1f-s123/verify/...`), non-coal exits DO
decide and execute (gas_st 389.5 MW in 2027, oil 3,295.8 MW in 2029) — the same machinery
produces non-coal exits once the requirement basis is corrected.

## 3. Why the admitted block is all coal (the composition mechanism)

Admission is worst-first by margin depth until the scheduled post-pipeline accredited fleet
would breach the requirement; the budget filled with the ~11.9 GW coal block decided at the
window's first screens, and everything after it was capped. Hindcast per-fuel depths are
not committed (routed with R1); the committed forecast-window depths show the ordering is
NOT intrinsically coal-first (2027 medians $/kW-yr: oil 17.4 > gas_st 16.8 > gas_cc 10.0 >
gas_ct 6.8; 2028 adds coal at 5.2). The legacy-rule leg of the SAME FFR-2B comparison is
the decisive control on composition: the identical margins under per-fuel loss counters
retired **12,920.3 MW of gas_st and only 1,497.0 MW of coal** — 6× the actual gas_st exit
and an eighth of the actual coal. Under BOTH decision rules the bar fails the fleet
broadly and the realized composition is set by the rationing mechanics, not by which units
are genuinely uneconomic. That is the structural signature of a margin model with too
little cross-unit discrimination (§4.2), rationed by an adequacy constraint.

## 4. Thread verdicts (each against its frozen kill)

### 4.1 Thread (iii) — hindcast requirement basis: **CONFIRMED-PRIMARY, repair already at HEAD**

The admission cap and the execution floor both resolve the requirement through
`resolve_adequacy_requirement_mw` and the accredited side through
`accredited_firm_capacity_mw` (verified on source: `_apply_reliability_floor` lines
~1340–1363; `_firm_import_mw` folds `ADEQUACY_EXTERNAL_TIE_FIRM_MW` at adequacy.py:332).
All three S-123 operands are those registries' constants, so they reach a T1-H hindcast
solve (which runs the full `evolve_fleet` machinery) exactly as they reach a t1f forecast.
The FFR-2B/FFR-3A-3 solves predate S-123 (2026-08-02/04 vs 2026-08-30).

The hindcast-window analogue, computed from committed constants and committed peaks
(cmc-probe ledger peaks; same vintage-2020 realized demand path):

* pre-S-123 requirement factor = 1.179 × (1.079/1.157) = **1.09952 × peak**
* post-S-123 factor = (1 − 0.0665940) × 1.157 × (1.079/1.157) = **1.00715 × peak**
* Δ = 0.09237 × peak, **plus** +3,505.9 MW external accredited firm (S-2)

| screen year | peak MW | Δrequirement MW | + external tie | total headroom swing |
|---|---:|---:|---:|---:|
| 2023 | 120,781 | 11,157 | 3,506 | **14,663** |
| 2024 | 121,560 | 11,229 | 3,506 | **14,735** |
| 2025 | 118,661 | 10,961 | 3,506 | **14,467** |

(The G3 cap horizon projects the peak 1–3 years further for a mixed schedule, scaling the
Δ up another ~1–3 %.) Against a missing non-coal target of 3.46–3.93 GW the swing is
**3.7–4.3×** — the pre-S-123 basis did not merely trim the admission budget, it consumed
the entire non-coal channel several times over. The forecast-window control (§2 item 2)
shows the corrected basis admitting and executing non-coal exits in the same machinery.

**Kill honoured / honest limits:** (a) the swing is over-determined the same way S-123's
own package was — nothing here is sized to the 3.9 GW residual; (b) enlarging the budget
admits by depth order, and hindcast depths are uncommitted — the corrected basis provably
un-starves the channel, but whether the admitted mix lands on the actual per-fuel split is
the re-measure's question (R1), entangled with §4.2; (c) applying single-valued PY 2025-26
operands to 2021–2024 screens is a vintage approximation (the registries are not
per-year), inherited from S-123's design, noted for R1's read of its result.

### 4.2 Thread (i) — margin side: **CONTRIBUTING, with the sign INVERTED from the charter's phrasing**

Not over-crediting: **under-crediting, broadly and near-uniformly.** ~83 % of screened
thermal MW fails the bar in 2024 (§2). Leg decomposition, from the only committed per-unit
bar decompositions for MISO (E5, post-S-123 forecast window — carried with that caveat,
never quoted as the hindcast number; capacity-weighted $/kW-yr over capped rows):

| fuel (2027) | net_rev | bar | energy leg | capacity leg | AS/attr |
|---|---:|---:|---:|---:|---:|
| coal | 50.5 | 58.5 | 50.5 | **0.0** | 0.0 |
| gas_cc | 22.9 | 30.0 | 22.9 | **0.0** | 0.0 |
| gas_ct | 15.4 | 21.0 | 15.4 | **0.0** | 0.0 |
| gas_st | 18.7 | 35.0 | 18.7 | **0.0** | 0.0 |
| oil | 6.6 | 25.0 | 6.6 | **0.0** | 0.0 |

**(i-b), the capacity leg — the measured structural defect.** Every committed capped row
prices capacity at $0. Mechanism: the MISO RBDC (`_MISO_RBDC_CURVE`) zero-crosses at
reserve position 1.05, and the screens' entering-fleet positions sat above it — hindcast
ledger `reserve_margin` (accredited/peak − 1) gives positions (÷1.09952) of 1.158 (2021),
1.107 (2023), 1.109 (2025), and the 2024 screen's ENTERING fleet (pre-exit, ≈ +11.1 GW
firm over the ledger's post-exit 1.018) ≈ 1.10. The internal story is coherent: capacity
revenue $0 through the 2023–24 screens → mass failure; the position dips toward the curve
only AFTER the coal block exits, at which point the 2025 screen pays, the 2,006 MW
pipelined cohort re-clears, and the pipeline empties (§2's `reversed` row). MISO's actual
PRA in the same years (committed `data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv`,
seasonal sums): PY 2023-24 ≈ **$3.4/kW-yr**, PY 2024-25 ≈ **$7.3/kW-yr**, PY 2025-26 ≈
**$79.1/kW-yr** — small but structurally NON-zero while long, and a large print at the
forward edge. Against gas bars of $21–35/kW-yr, the $0-vs-$3–8 gap is a material fraction
of exactly the shortfalls measured above (gas_ct −5.6, gas_cc −7.1). The constants file
itself documents the root limit (capacity_market.py, "ONE-POSITION LIMIT"): one annual
position evaluated on all four seasonal curves prices ALL seasons at zero when long,
which is precisely the hindcast regime. This is a real market-design representation gap
(rule 1 direction), NOT a residual to tune against — R2 routes it with its published-data
identification.

**(i-a), the energy leg** is characterized but not adjudicated: hindcast per-unit energy
margins are uncommitted (the FFR-5A enrichment postdates every committed hindcast ledger).
What is committed shows the energy pro-forma alone leaving every class under its bar with
little cross-class spread against reality's outcome (70 of 74 GW of real gas/oil SURVIVED
2021–2025 on energy + near-zero capacity revenue). Whether hindcast prices under-produce
inframarginal rent, and by how much per class, is R1's margin_detail read. Kill honoured:
no FOM constant, no adder, no threshold is proposed from this.

### 4.3 Thread (ii) — identification against EIA-860: **REFUTED as the cause of the zero**

The actually-exited units are IN the screening population: the three ≥300 MW gas_st
exiters and spot-checked mid-size units are present in the vintage-2020 operable sheet at
matching MW (§1), the model taxonomy carries them under screened `_THERMAL_FOM` fuels
(gas_st its own class, bar $35/kW-yr), and 11.2 of 13.9 GW of gas_st sits in the committed
capped set (forecast window) — the screen SEES the real exiters and fails them; they are
rationed out with everything else. Execution lags (gas/oil = 1 yr, RC-0B medians) cannot
produce a zero, only shift timing. No screen-population gap material to 3.9 GW exists.
What (ii) DOES establish: the real cohort is 3 large steamers + a 158-unit small tail
(median 2 MW) — reproducing it needs a screen that can discriminate at that grain, which
connects the target to §4.2's discrimination defect rather than to any per-fuel constant.

### 4.4 Thread (iv) — cap's decision-year fleet side: **CONTRIBUTING, bounded, stays open**

FFR-3F §1.4's recorded item is real and points the same direction as (iii): entry between
decision and execution is uncredited at the cap horizon. Bound from the committed additions
in this run (2023 wind 4,000 MW pool ≈ 0.66 GW firm; 2025 gas 5,000 MW ≈ 4.6 GW firm +
storage 4,000 MW): up to ≈ **5–9 GW of uncredited firm MW** at the later screens' horizons
— same order as (iii)'s terms but smaller in the early screens where the coal block was
admitted and the channel starved. No committed artifact isolates its marginal effect on an
admission (that would need the R1 re-measure's event rows at minimum). It remains FFR-3F
§1.4's open item; nothing here closes or widens it.

## 5. MISO-specific or shared machinery? (the D4-M question, answered narrowly)

The MECHANISM is shared, ISO-agnostic code — one uniform bar, one worst-first cap — and the
signature "screen executes zero exits" now measured in two ISOs comes from that shared
shape: whenever the bar fails far more MW than the adequacy machinery will release, realized
exits are rationing artifacts. But this lane's ATTRIBUTED CAUSES are MISO-specific inputs:
the pre-S-123 PRA requirement registries (iii) and the MISO RBDC's zero-at-long capacity
leg (i-b). Neither can transfer to ERCOT (energy-only: no capacity payment exists there and
`market_design_retirement_floor` addresses its floor separately), so per rule 25 this
finding fills no ERCOT cell and takes no position on D4-M's cause. **Routed to the
director:** whether ERCOT's zero shows the same "broad bar failure + rationing" signature
is a question for an ERCOT lane with ERCOT evidence; if it does, the shared-shape
observation (bar-vs-rationing balance) may deserve its own cross-ISO charter — that
decision is the director's, not this lane's.

## 6. Routed repairs (routed, NOT built — priced, admissibility per rules 13/21)

1. **R1 — PRIMARY: HEAD re-measure of the MISO T1-H leg** (a solve; refused here under
   K2). The S-123 registry values are already in force at HEAD and reach the admission
   cap/floor (§4.1); the FFR-5A margin_detail enrichment now attaches to every pipeline
   event, so one re-solve commits the hindcast per-fuel depths, bar decompositions and
   event rows this lane had to bound around. Price: ≈ 25 min solo / ≈ 10 GB peak RSS by
   the s123-verify analogue (5 years, same machinery). **Two mandatory guards:** (a) the
   three S-123 operands sit OUTSIDE the cache-key digest (S-123 §7.8) — the FFR-2B-era
   key would serve a stale pre-package bundle; the re-measure must verify a fresh solve
   (no pre-existing bundle at its key). (b) Score against the CURRENT committed actuals
   target and report the §1 seam explicitly (both coal signs), so the re-measured verdict
   is not silently compared across target vintages. Admissibility: no new parameter — the
   run measures already-shipped published-source constants (rule 13 clean).
2. **R2 — capacity-revenue leg realism at long positions** (structural investigation,
   mechanism decision — likely its own charter). Object: the documented ONE-POSITION
   LIMIT (all four seasonal RBDCs at one annual position ⇒ $0 everywhere when long) vs
   MISO's own record of small positive clearing while long. Identification is published
   data only — the PRA seasonal clearing record already in-repo and the published RBDC/
   CONE tables; the committed `validate_capacity_prices.py` seasonal Pass-1 (which does
   reproduce the concentration from published seasonal positions) marks the direction.
   Explicitly NOT admissible: any flat adder or floor tuned to the retirement residual
   (K7). Cost: data/mechanism work, no solve until armed for a probe.
3. **R3 — cap-horizon entry crediting** (thread iv): stays FFR-3F §1.4's open item, now
   with a MISO-window bound (§4.4). A mechanism decision (credit scheduled-COD entry at
   the cap horizon), zero new parameters; its marginal effect is measurable from R1's
   event rows before any code change is justified.
4. **R4 — the actuals-vintage seam** (scorer/records, no solve): reconcile the scored
   per-fuel table's 2026-08-02-era target with the current committed CSV — including the
   gas_st fold and the coal-sign flip (+9.1 % → −4.0 %) — so D3's board attribution note
   and any future MISO T1-H verdict quote one declared target vintage. Routed to the
   director for lane assignment (it touches D3's published framing, not this lane's).

## 7. Kills honoured, governance

K1 partially triggered and handled as frozen: hindcast per-fuel EVENT rows are uncommitted,
so §2's per-fuel classification rests on the committed aggregate + arithmetic bound and the
enriched re-measure is routed (R1) — the lane did not stop entirely because the bound is
decisive for outcome (B). K2 honoured: zero solves, zero re-scores; every computation is
committed-code arithmetic on committed inputs (requirement factors, positions, seasonal
sums). K3 honoured: no board/verdict/matrix/keeper/backcast write; the only files this lane
adds are its precommit and this finding. K4 honoured (no MISO backcast surface; ls-remote
re-checked at push). K5/rule 25 honoured (§5 fills no ERCOT cell). K6/rule 22: no
out-of-training year touched — all reads are committed 2021–2025 hindcast artifacts,
committed 2026+ forecast artifacts, or raw data. K7 honoured: no FOM constant, threshold,
lag or adder proposed anywhere; the residual's closure is routed as R1/R2 root-cause work.
Rule 28: nothing tested, no ScenarioConfig field, no matrix edit; the MISO lever queue was
checked (empty of un-adjudicated items) and this lane adds no lever.

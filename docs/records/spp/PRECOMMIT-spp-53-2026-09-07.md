# PRECOMMIT — SPP-53: the SPP North↔South link TTC from SPP's own flowgate limits

**Lane** SPP-53 · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-53-ttc-link-limit-67e3yf` (stem `claude/spp-53-ns-ttc-f6dz`) ·
**Data profile** `spp` · **Charter** plan §8 SPP-53 (owner ruling **P13**, sitting r#5) ·
**Predecessors** `FINDING-spp-20-2026-09-06.md` §3 / §5 R-6 (the 48,700 MW placeholder),
`FINDING-spp-14-2026-09-06-session-b.md` §5 (the four-group rules, `docs/handoffs/spp14/groups.py`,
§5.4 the 2026-01-28 schema break), `FINDING-spp-13-2026-09-06.md` (row 11 is NDA/CEII).

**Pushed before a single limit value is read.** Everything below is either a structural census
of the registries with their rating columns dropped at load, arithmetic on numbers already
committed by SPP-11 / SPP-20 / SPP-14, or a rule. The construction is applied once, after this
document is on the branch, and the number falls out of it. Nothing here is revised after the
data is read; a miss of any declared condition is reported at full magnitude in the FINDING.

---

## 0. THE PIN and the preconditions

```
62c067b973d5aab698f7874118edd1d99a2d597a   origin/main at PRECOMMIT time
```

| precondition | check | result |
|---|---|---|
| SPP-20 landed | `git log origin/main --grep=SPP-20` | `de0166b9`, `b063c82e` — **yes** |
| SPP-14 landed (both sessions) | `git log origin/main --grep=SPP-14` | `df5e8c3d`, `c7f7fc33` — **yes** |
| the 2023–2025 RTBM roll-ups are in the tree | `data/raw/spp-binding-constraints/RTBM-BC-*.csv.zip` | 14 zips, 10-column schema verified on `202501` — **yes** |
| the two flowgate registries are in the tree | `Flowgates.csv` (823 rows) / `Temp_Flowgate.csv` (3,298 rows) | **yes** |
| the per-hub hourly RT/DA LMP is in the tree | `data/raw/_validation-source/actual_lmp_hourly_zonal_SPP.parquet` | 52,560 rows (`SPPNORTH_HUB` / `SPPSOUTH_HUB` × 26,280 h) — **yes** |
| the portal serves the 2026 daily files anonymously | `fetch_spp_alt_portal.py --list rtbm-binding-constraints --path /2026/01/By_Day` | `RTBM-DAILY-BC-20260128.csv` 1,883,829 B … `/2026/09/By_Day` up to `20260905` — **reachable** |

**STOP condition (d), evaluated here, before the data:**

- *"no daily file reachable"* — **does not fire**: the listing above returns the daily files for
  every month 01–09 of 2026 (names and sizes only were read).
- *"`Flowgates.csv` already carrying a corridor rating that makes the archive pull unnecessary"* —
  **does not fire, structurally** (§1.2): no SWPP-owned flowgate has a monitored element crossing
  a North area to a South area except `SPPSPSTIES` (the SPS tie, `sps_tie` by the fixed rules —
  not the corridor), and no SWPP flowgate is a multi-element North↔South interface. The
  registries therefore carry per-**element** ratings, not a corridor rating; per charter step (1)
  they become the **cross-check** of the archive's limit-at-bind, and the archive pull proceeds.

---

## 1. The object, and what the registries actually contain

### 1.1 What the link is, and what a flowgate limit is

The registered SPP topology is two bubbles and one pipe: `SPP-North` ↔ `SPP-South`, a single
symmetric `TransferLink.ttc_mw` (`iso_configs._spp_config`, SPP-20). In the LP it bounds the
**net zonal transfer** — the whole North→South (or South→North) MW moving between the two
fleets/loads — and its dual is the zonal price separation.

An SPP flowgate limit is a different object. A flowgate is one **monitored element** (a line or a
transformer) under one **contingency**; its `Real Time Effective Limit` is the MW the element may
carry post-contingency, derated by SPP for temperature / outages / TLR. The N→S transfer that
loads that element to its limit is **L_f / ψ_f**, where ψ_f is the element's sensitivity to the
transfer (its shift factor for the transfer's source/sink pair). Only an **interface** flowgate
(a multi-element sum whose elements ARE the transfer path, so ψ ≈ 1 by construction — what ERCOT's
GTCs are: WESTEX, PNHNDL, EASTEX, each an aggregate export constraint) can be read as a link TTC
directly. That is why ERCOT's WESTEX/PNHNDL/EASTEX limits ARE the link TTCs in `_ercot_config`
and why the same builder keeps `N_TO_H` — *"one of several parallel 345 kV paths this six-zone
reduction collapses into a single link"* — at the aggregate estimate rather than the literal GTC.
The whole of this lane is deciding which of those two cases SPP's corridor is.

### 1.2 Structural census of the registries (rating columns dropped at load — no limit read)

`Flowgates.csv` (permanent): 823 rows / 285 flowgates; owners `SWPP` 450, `SPPW` 199, `TVA` 107,
`MISO` 35, `PJM` 29, `CISO` 3. Columns `Type ∈ {INT, RCF, CFG}`, `FGType ∈ {OTDF, PTDF}`,
`ElementType ∈ {Monitored, Contingent}`, per-element `From Area` / `To Area` / `Voltage`, seasonal
`Normal` / `Emergency` ratings, `IROLLimit`, `TRM`. `Temp_Flowgate.csv`: 3,298 rows / 1,333
flowgates (`SWPP` 2,262 rows), `NormLimit` / `EmerLimit` / `CreatedTime`.

Of the **173 SWPP-owned permanent flowgates** (119 `INT`, 52 `RCF`, 2 `CFG`; 146 OTDF / 27 PTDF;
elements per flowgate 1–23, mode 2 = one monitored + one contingent):

| question | answer (structure only) |
|---|---|
| monitored elements with one terminal in a North area {WR, SECI, KCPL, MPS, KACY, EDE, INDN, LES, NPPD, OPPD, SPRM, WAUE} and the other in a South area {OKGE, CSWS, GRDA, WFEC, SPS} | **1** — `SPPSPSTIES` (`LN LIBERAL_ - SOONER 115 kV`, SECI→SPS, 9 elements): the **SPS tie**, `sps_tie` under the fixed rules |
| multi-element SWPP flowgates whose elements span the cut (a North↔South interface) | **0** |
| monitored elements touching a Kansas-corridor area {WR, SECI, KCPL, MPS, KACY} | **42**, every one INTERNAL to the North side: WR↔WR, KCPL↔KCPL, MPS↔MPS, SECI↔SECI, NPPD↔SECI/MPS (345 kV), KCPL↔WR (345 kV), WR↔EDE, KCPL↔AECI; voltages 115 / 161 / 230 / 345 kV and 345/161, 345/138, 230/115, 161/115, 115/161 kV transformers |
| SPP-14's 2024 corridor constituents by name in the permanent registry | Nashua transformer → `NASXFRNASHAW` (`XF NASHUA 345/1 kV`); Viola → `WICBENVIOREN` / `KILNWKRENVIO`; Franklin, First Creek–Roanridge, Smoky Hills–Summit, Jayhawk–Franklin → **absent** (they are TEMP flowgates: `TEMP03_32903` / `TMP266_27514` `XF FRANKLN5 161/69 kV`; `TEMP77_27899` `LN FIRSTCRK - ROANRDGE 161 kV`; `TMP124_29862` `LN JAY_HAWK - FRANKLN5 161 kV`) |
| temporary SWPP flowgates with a monitored element touching a Kansas-corridor area | **193**, ids rotating (`CreatedTime` 2017 → 2026-07-30) while the **element string persists** |

**Reading.** SPP's corridor is NOT an interface. It is a set of single elements — mostly 115–161 kV
lines and 161/69–345/161 kV transformers inside Kansas and western Missouri, a few 345 kV lines —
each binding under its own contingency, whose ids rotate as temporary flowgates while the physical
element persists. Every constituent has ψ_f ≪ 1 for a North→South zonal transfer. This is the
`N_TO_H` case, not the WESTEX case: **a literal element limit is not the link TTC, and using one
literally is exactly the rule-14 misalignment the charter names.**

---

## 2. The three constructions, their physical readings, and the one chosen

| construction | what a pipe-and-bubble link it is | verdict, and why |
|---|---|---|
| **(A)** the rating of the corridor's dominant defining flowgate, the ERCOT-GTC analogue | "the corridor IS one aggregate constraint; the link limit is its rating" — true when the constraint is an interface with ψ ≈ 1 | **rejected as a literal** by §1.2: no interface exists; the dominant constituent is a single 161 kV or 161/69 kV element. Taken literally it sets the link at an element rating, which (§4) is one to two orders of magnitude below the transfers the two zones' fleets and loads imply. **Kept as the SKELETON**: the chosen construction is (A) with the missing ψ supplied from measured data |
| **(B)** a simultaneous-transfer sum over the parallel Kansas paths | "the link is the thermal cut-set of the corridor; every parallel path loaded to its rating at once" — an upper bound on the first-contingency transfer, since flow divides by impedance, not by rating | **rejected as not measurable from the registries**: they list *monitored* elements, not the cut-set (a line that never bound is not in them), so the sum is neither the cut-set nor a transfer; and a same-time sum of contingency ratings overstates FCITC by construction. Would also be a guess about which elements form "the cut" |
| **(C)** the hour-wise minimum of the limits of the flowgates binding together, summarised over binding intervals (the `derive_ttc_limits.py` limit-at-bind instrument) | "the link limit at each hour is the tightest constituent's limit" — again an element-scale reading with ψ = 1 assumed | **rejected as a literal** for the same reason as (A), and worse: it picks the *smallest* element. **Kept as the INSTRUMENT** for L_f: per constituent, the median `Real Time Effective Limit` over its own binding intervals is exactly the measured limit-at-bind ERCOT uses |

### 2.1 The chosen construction — (A) reconciled to the transfer: the FCITC reading

**The link TTC is the North→South zonal transfer at which the corridor's limiting flowgate reaches
its own effective limit** — the first-contingency incremental transfer capability the corridor
actually exhibits — built from two measured legs and one fixed aggregation:

**Leg 1 — L_f, the per-constituent effective limit (MW on the element).** From the 2026-01-28 →
latest daily `RTBM-DAILY-BC-YYYYMMDD.csv` files (14-column schema): for each corridor constituent
f, the **median `Real Time Effective Limit` over its `BINDING` ∪ `BREACHED` intervals** (limit-at-
bind, the ERCOT instrument), with p10 / p90 / n, `Source Limit`, and the derate share
(effective < source) reported beside it. A constituent with fewer than **100** binding/breached
intervals in the 2026 archive takes instead its registry rating — `Temp_Flowgate.csv` `NormLimit`,
or the mean of the four seasonal `Normal` ratings in `Flowgates.csv` — if its element is there; if
neither, it carries no L_f and drops out of the aggregation (reported). The join 2026 ↔ 2023–25 is
on `Constraint Name` first, then on the **`Monitored Facility` string** (temp ids rotate, the
element does not).

**Leg 2 — ψ_f, the corridor constituent's transfer sensitivity (MW on the element per MW of
North→South transfer).** Identified from the market's own price decomposition. SPP's LMP at node n
is λ − Σ_f SF_{f,n} · SP_f (loss term aside), with SP_f ≤ 0 in SPP's sign convention, so the
North→South hub spread is

```
(SPPSOUTH_HUB − SPPNORTH_HUB)_h  =  Σ_f  |SP_f|_h · ψ_f  +  c  +  ε_h ,   ψ_f = SF_{f,North} − SF_{f,South}
```

ψ_f is the flow induced on element f by 1 MW injected at the North hub and withdrawn at the South
hub — a **network property**, positive for a constraint the N→S transfer loads. Specification,
fixed here:

- sample: every hour of 2023–2025 with both hub RT prices present (≈ 26,250 h);
- dependent: hourly RT `SPPSOUTH_HUB − SPPNORTH_HUB` from `actual_lmp_hourly_zonal_SPP.parquet`,
  aligned to the RTBM intervals on the builder's own calendar convention (recorded in the FINDING);
- regressors: for **every** `Constraint Name` with ≥ **263** pooled 2023–2025 binding hours
  (1 % of 26,280) — all four groups, so Oklahoma / SPS / seam constraints do not confound the
  corridor's coefficients — the hour's mean of |`Shadow Price`| over its 12 RTBM intervals
  (0 when not binding); plus an intercept;
- estimator: OLS, heteroskedasticity-robust (HC1) standard errors; no other terms;
- a corridor constituent is **IDENTIFIED** iff its coefficient satisfies **ψ_f > 0** and
  **t ≥ 2.0** and **ψ_f ≤ 1** (a shift-factor difference above 1 is not physical and marks a
  mis-identified column); everything else is reported and contributes no T*_f.

Admissibility (rule 13 `[R-MEASURED]` forward test): a shift factor regenerates for a forward year
from the same network, responds to a topology change, and is a physical/market input — the same
class as a measured delivered fuel price. It is identified from SPP's prices and SPP's shadow
prices, never from anything this model produces.

**Aggregation, fixed.** Constituents = every `Constraint Name` in `n_s_corridor` under
`docs/handoffs/spp14/groups.py`'s rules **unchanged**, with ≥ 263 pooled binding hours. For each
IDENTIFIED constituent with an L_f, **T*_f = L_f / ψ_f**. The link TTC is the **binding-hours-
weighted (2023–2025 pooled) MEDIAN of T*_f** across identified constituents, **rounded to the
nearest 100 MW**. Median, not minimum: the single number stands for the corridor over the year and
the minimum would be one outage-season temp flowgate; median, not mean: T* is a ratio with a heavy
right tail from small ψ. Weighted by hours because the constituent that limits the corridor most of
the time is the one the link most often stands for.

**What the ψ screen also does, said now.** `n_s_corridor` is an **area-token** group ("contingency
touches a Kansas-corridor area", SPP-14 §5.1) — a declared superset that sweeps in local Kansas
delivery constraints unrelated to the N↔S transfer. A local constraint has ψ_f ≈ 0 to the hub
pair and fails the screen; a corridor constraint passes. The screen is therefore the measured
separation of "corridor" from "Kansas-internal" that the token rule could not make — reported
constituent by constituent, and it changes nothing in the four-group table.

### 2.2 Declared rejection conditions (a miss kills the construction; it never adjusts it)

| id | condition | consequence |
|---|---|---|
| R1 | fewer than **3** identified constituents carry an L_f | construction FAILS |
| R2 | TTC ≥ **B_plaus = 23,300 MW** (§4) | rejected as still-a-placeholder (cross-check 0c) |
| R3 | TTC ≥ **B_hard = 37,400 MW** (§4) | rejected as still-a-placeholder, a fortiori |
| R4 | the identified constituents' T*_f span more than a factor of **10** between the hours-weighted p25 and p75 | the corridor has no single transfer level; construction FAILS |
| R5 | the daily archive cannot be pulled for ≥ 90 % of the days 2026-01-28 → latest | STOP (d) |

On FAIL the placeholder is **not** replaced, the FINDING says so with the measured cause, and the
item routes to SPP-DESK; nothing is re-specified to make a condition pass.

### 2.3 What is not a rejection condition

Any comparison with a modelled price or flow. There is no SPP solve, no SPP residual, and this lane
creates neither. The 2023–2025 binding frequency (0.555 / 0.516 / 0.631) and the 2024 spread enter
only as the one-sided §4 check that the link CAN bind.

---

## 3. The misalignment statement (rule 14 `[R-ACCURATE]`, carried into the citation comment)

1. **Vintage.** The effective limits are **2026** measurements (2026-01-28 → latest) applied to a
   link solved on 2023–2025. Element ratings are seasonal and slow-moving; temp flowgates rotate.
   The 2023–25 archive has no limit column (SPP-14 §5.4), so no in-window limit exists.
2. **Object.** A flowgate limit is a monitored-element-under-contingency rating, not a corridor
   transfer capability. The ψ reconciliation converts it, and the conversion is the lane's
   adjudication, not SPP's number.
3. **Hub pair vs zone pair.** ψ_f is the sensitivity to a Nebraska-hub → central-Oklahoma-hub
   transfer (`Hub_Definitions.csv` node clusters), not to the load/fleet-weighted bubble-to-bubble
   transfer the LP moves. Same order of magnitude, not the same number; direction of bias unknown
   and stated as such.
4. **Group superset.** `n_s_corridor` is an area-token rule; the ψ screen is what separates the
   corridor from Kansas-internal constraints (§2.1).
5. **Symmetry.** The link is symmetric (SPP-20's registration; the MMU records the spread reversing
   sign for 6–8 months of 2025). ψ_f is identified for the N→S direction; the S→N capability is
   assumed equal. Not this lane's field to change.

Because of 2–4 the value is a **rule-14 reconciled Tier-3 → Tier-2 figure**, never a Tier-1 rated
interface, and the citation comment says so.

---

## 4. The residual-blind cross-check (charter 0c), bounds computed now

Inputs already committed: SPP-11's sub-BA hourly demand (`zone-specific-demand/SPP/
spp_subba_demand_2023-2025.csv`, North = {EDE, INDN, KACY, KCPL, LES, MPS, NPPD, OPPD, SECI, SPRM,
WAUE, WR}) and the EIA-860 operable fleet at HEAD (`eia-860/eia860_generator_operable.parquet` ×
`eia860_plant.parquet`, BA `SWPP`, status `OP`, `_SPP_STATE_ZONES`).

| quantity | value | source |
|---|---:|---|
| North minimum hourly load 2023 / 2024 / 2025 | 11,299 / 11,837 / 11,856 MW | sub-BA sum; the 2023 maximum (1,886,188 MW) is the audit §3.4 100× slip hour and is excluded |
| North maximum hourly load 2024 / 2025 | 28,124 / 28,078 MW | same |
| North summer capability, total | 48,328.4 MW (parquet at HEAD) / 48,711.8 MW (audit §2.4, EIA-860 2025 ER) | wind 17,578.6 · coal 12,727.2 · gas CT 6,756.3 · hydro 2,366.1 · gas CC 2,325.1 · nuclear 1,945.2 · oil 1,712.2 · gas IC 1,213.7 · gas ST 1,031.0 · solar 599.4 |
| **B_plaus** = North non-gas capability (wind + coal + nuclear + hydro = 34,617 MW) − North minimum load (11,299 MW) | **23,300 MW** | the most the North could ever push south with every non-gas unit at capability at its lowest load hour — above this a link cannot bind |
| **B_hard** = North total capability (48,711.8) − North minimum load (11,299) | **37,400 MW** | the SPP-20 placeholder (48,700) exceeds even this, which is why it cannot bind |

Consistency to report, not to gate on: with the corridor binding in 52–63 % of hours at a mean
|shadow| of $140–227/MWh while the mean RT hub spread is $1.9–8.4/MWh (mean |spread| $12–17, p90
$28–41; `spp14/crosscheck.json`), the implied corridor-aggregate ψ is of order 0.05–0.1 — the
FINDING states the regression's aggregate against this back-of-envelope, as a check on the
identification's order of magnitude, not as an input.

---

## 5. Deliverables and the files this lane touches

| file | change |
|---|---|
| `data/raw/spp-binding-constraints/rtbm_bc_corridor_limits_2026.parquet` | NEW reduced sidecar: every `State ∈ {BINDING, BREACHED, ACTIVATED}` row of the 2026-01-28 → latest daily files whose `Constraint Name` is `n_s_corridor` under `groups.py`'s rules, columns `Constraint Name`, `Monitored Facility`, `Contingent Facility`, `Source Limit`, `Real Time Effective Limit`, `Initial Effective Limit`, `Interconnect`, `GMTIntervalEnd` |
| `data/raw/spp-binding-constraints/README.md`, `SOURCES.md`, `SHA256SUMS.txt` | one status section + one SOURCES row (fetch command, span, row count, sha256); the four-group spec untouched |
| `src/market_sim/config/iso_configs.py` | `_spp_config`: the N↔S `ttc_mw` value and its citation comment ONLY (Edit tool, exact bytes, fetch-back verified — rule 27) |
| `src/market_sim/data/transmission_expansion.py` | `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"]` → 2026 (the limit vintage) with its comment; the charter names this file's `config/` path, the dict lives under `data/` |
| `docs/parameter-citations.md` | one row (the file is generator-rendered; the row is added by hand under the transmission section and the generator note is left intact) |
| `docs/multi-iso/spp-addition-plan-2026-09.md` | §5 SPP-53 row → LANDED; §3 P13 ruling cell annotated with the value; §9 index |
| `docs/handoffs/FINDING-spp-53-2026-09-07.md` | the per-flowgate table, the regression, the construction, the number, the cross-check, the G8 proof |

Not touched: anything else in `iso_configs.py`; `ScenarioConfig`; `groups.py` and the README's
four-group spec; any other ISO; the matrix shards (a TTC value is an input, no mechanism is tested);
`frontend/`. No solve. G8 proof: `solve_surface_register.py --diff origin/main HEAD` reads zero
moved rows for the six keepers (`iso_configs.py` is not a surface module; the diff proves it).

## 6. Pre-registered FINDING table shape

Per corridor constituent (rows sorted by pooled 2023–25 binding hours): `Constraint Name` ·
`Monitored Facility` · group reason · pooled binding hours · ψ_f · t · identified? · 2026 n
binding/breached intervals · median / p10 / p90 `Real Time Effective Limit` · median `Source Limit` ·
derate share · registry rating (cross-check) · T*_f. Then the weighted median, the rounding, the
R1–R5 verdicts, and the §4 back-of-envelope comparison.

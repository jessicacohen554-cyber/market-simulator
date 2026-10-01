# PRECOMMIT — lane NWPP-36: Columbia mainstem hydraulic coupling (owner ruling N3)

**Lane:** NWPP-36 (desk r#6 charter, 2026-09-16) · **Model:** Fable (`claude-fable-5-1`) ·
**Base:** `edd409434ea9c77e8a5bbf9f95c0ed70417aab2f` (= `origin/main` at session start; the
notice's `8b9b32e4` / desk refresh `6ffead70` are not reachable from this clone's `origin/main`,
so every count below is re-taken at THIS sha) · **Branch:** `claude/jolly-keller-8j3ht6`
(harness-designated; the charter's `claude/nwpp-36-cascade-coupling-<4>` stem could not be used —
the environment pins the branch, as NWPP-32 also recorded) · **DATA PROFILE:** `nwpp` ·
**Zero calibration LP** (rule 32 — §9 states why no shard is spent).

Written and pushed BEFORE any code, artifact or number in this lane exists. Everything below is
fixed ex ante; §4's measurements had not been computed when this file was pushed (the raw CROHMS
JSON pull was started in a scratch directory in parallel, and no lag, band or ratio was derived
from it before this push).

## 0. Preconditions (verified at base)

| precondition | state |
|---|---|
| NWPP-20 landed (nine regions) | `SUPPORTED_ISOS` at base carries nine keys; nine matrix shards on disk: ERCOT CAISO PJM MISO NYISO NEISO SPP SOCO NWPP |
| NWPP-32 landed | `data/raw/nwpp-hydro/{nwpp_hydro_budget.parquet, nwpp_hydro_chain.csv, nwpp_hydro_chain_published.csv, nwpp_hydro_reconciliation.csv, nwpp_hydro_within_month_930.csv}` present; `docs/handoffs/FINDING-nwpp-32-2026-09-14.md` on main |
| designated keepers at base (`frontend/data/backcast/keepers/<ISO>.json`) | ERCOT `2026-09-09-ercot265-receipts-fallback` · CAISO `2026-09-12-caiso-275-gascoupling` · PJM `2026-09-11-pjm-d4-4-gasoutage` · MISO `2026-09-12-miso-255-sil-measured` · NYISO `2026-09-14-nyiso-235-gas-repair` · NEISO `2026-09-09-neiso-108-fuelvintage` · SPP `2026-09-13-spp-38-vintage-cache` · SOCO none · NWPP none |
| CROHMS reachable | `public.crohms.org/dd/common/web_service/webexec/getjson` answers (200); hourly `Flow-Out / Flow-Spill / Flow-Gen / Elev-Forebay` (`CBT-REV`) and `Power.Total` (`CBT-RAW`) exist for every federal and mid-C project in the chain; ranges of ≤ 3 months per call |
| NID reachable | `nid.sec.usace.army.mil/api/nation/csv` (200, 67.3 MB, "Data Last Updated 2026-9-11") |

## 1. What is built, and the one sentence that keeps it inside rule 19

**The coupling redistributes WHEN a coupled plant's water is turbined. It NEVER changes HOW MUCH
energy per month.** NWPP-32's EIA-923 monthly budget row (`hydro_monthly_energy`, cap per
plant-month) is untouched and remains the sole energy-quantity mechanism. The coupling is a second
phenomenon — hydraulic succession — expressed as a per-hour water balance at each coupled plant,
with the plant's monthly cap still coming from the budget row. A mechanism that can move a plant's
monthly total is a second budget and is refused (§7 gate G-A1 measures this).

Inherited, not re-derived (NWPP-32 §5(a)–(d), §6): the eleven-plant mainstem read from the ORNL EHA
`Water` field; the lower Snake (four plants) entering at the McNary pool; Hells Canyon (three) and
Dworshak feeding it; **Boundary is Pend Oreille and is coupled to nothing here**; no single-unit
coordination of the seven mid-C projects in 2023–2025 (the HCA expired); the calendar month is the
budget period and `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT["NWPP"]` stays empty and untouched; the
HRFCPPA outlet ramp band and the ROD spill season are the two published non-power conditions the
mechanism must not contradict (§7 G-A4 checks the spill signature; the ramp band is NOT modelled and
is said so).

## 2. The reach table the mechanism is built on

From `nwpp_hydro_chain.csv` (EIA plant id · CROHMS station · role). Hydraulic order is the
published dam sequence; CROHMS station ids are the catalog's own (`tscatalog` query, this session).

| link | upstream u (id, station) | downstream d (id, station) | role of d |
|---|---|---|---|
| 1 | Grand Coulee 6163 GCL (**head**, seasonal storage 5.19 MAF) | Chief Joseph 3921 CHJ | coupled |
| 2 | Chief Joseph CHJ | Wells 3886 WEL | coupled |
| 3 | Wells WEL | Rocky Reach 3883 RRH | coupled |
| 4 | Rocky Reach RRH | Rock Island 6200 RIS | coupled |
| 5 | Rock Island RIS | Wanapum 3888 WAN | coupled |
| 6 | Wanapum WAN | Priest Rapids 3887 PRD | coupled |
| 7 | Priest Rapids PRD | McNary 3084 MCN | coupled (confluence: two upstreams) |
| 8 | Ice Harbor 3925 IHR | McNary MCN | (same row as link 7) |
| 9 | McNary MCN | John Day 3082 JDA | coupled |
| 10 | John Day JDA | The Dalles 3895 TDA | coupled |
| 11 | The Dalles TDA | Bonneville 3075 BON | coupled |
| 12 | Dworshak 840 DWR (**head**, 2.02 MAF) | Lower Granite 6175 LWG | coupled; the Snake above LWG (Hells Canyon, Salmon, Grande Ronde, Clearwater below DWR) enters as **side inflow** |
| 13 | Lower Granite LWG | Little Goose 3926 LGS | coupled |
| 14 | Little Goose LGS | Lower Monumental 3927 LMN | coupled |
| 15 | Lower Monumental LMN | Ice Harbor IHR | coupled |
| — | Brownlee 811 → Oxbow 3014 → Hells Canyon 3013 → (LWG) | | **NOT coupled — unmeasurable at hourly precision** (§4.1): CROHMS carries only DAILY Idaho Power series for BRN/HCD (`Flow-Out.Ave.~1Day`) and none for OXB. Reported, never substituted. The three plants keep NWPP-32's independent monthly budgets |

So: **14 coupled downstream plants, 15 links, 2 chain heads (GCL, DWR)**. Coupled nameplate =
mainstem minus Grand Coulee (13,603.8 MW) + lower Snake (3,033.0 MW) = **16,636.8 MW**; with the
two heads, whose release TIMING the rows bind, the mechanism touches 23,596.8 MW = 65.9 % of the
footprint's conventional hydro (NWPP-32: 35,799.5 MW).

## 3. The formulation (NWPP-32 §5(a) item 1, made LP-exact)

Units: water in **kcfs** (flow) and **kcfs·h** (volume) — the CROHMS native unit — so the pondage
band is a constant per plant and every generation column enters through a measured, month-varying
water-to-energy ratio. (The energy form of the same identity, `E_d(t) ≈ k_d·E_u(t−τ) + E_side,d`,
is recovered by multiplying the row by `η_d,m`; `k_d = η_d/η_u`. The worked example in NWPP-32 —
CHJ/GCL energy ratio 0.60 at discharge ratio 1.003 — is exactly `η_CHJ/η_GCL`.)

**New LP columns, per coupled downstream plant d and hour t** (a new `VariableLayout` block
`n_cascade = 2 × n_coupled`, appended AFTER the `dis_tranche` block so every existing offset is
unchanged and `n_cascade = 0` leaves the layout byte-identical — the established pattern of every
appended block):

* `S_d(t) ≥ 0` — spill (kcfs), water routed past the turbines;
* `0 ≤ V_d(t) ≤ B_d` — pondage volume above the bottom of the operated band (kcfs·h).

**One equality row per coupled plant d and hour t** (`n_coupled × T` rows, 6 non-zeros for a
single-upstream row, 8 for McNary's two-upstream row):

```
P_d(t)/η_d,m(t)  +  S_d(t)  +  V_d(t) − V_d(t−1)
   − Σ_{u∈up(d)} [ P_u(t−τ_ud)/η_u,m(t−τ_ud)  +  S_u(t−τ_ud) ]      =  I_d,m(t)  +  Σ_{u∈up(d), u a head} s̄_u,m(t−τ_ud)
```

* `P_·` are the EXISTING hydro generation columns (no new generation column, no new budget);
* `η_p,m` = MWh generated per kcfs·h of turbine flow, **per plant and calendar month**, on the
  EIA-923 basis (§4.3) — so `P_d/η_d` is turbine flow and `Σ_{t∈m} P_d/η_d,m = Q_gen,d,m` exactly
  when the plant fills its budget;
* `t − τ` wraps cyclically at the year boundary (the house convention for SOC);
* a head's spill is NOT a variable (a free spill at a chain head would be phantom water); it enters
  the RHS as the measured monthly-mean spill `s̄_u,m` (kcfs), a measured physical input of the same
  class as the budget itself;
* `I_d,m` = monthly-mean side inflow (kcfs) between up(d) and d (§4.4), held flat within the month —
  the same grain as the EIA-923 budget, so the coupling carries no hourly measured operation of any
  plant (rule 13: the hourly series enter ONLY through τ, the band and monthly means);
* `V_d(t−1)` at `t = 0` is `V_d(T−1)` (cyclic).

**Objective:** `+ε·(S_d + V_d)` with `ε = STORAGE_TIEBREAKER_EPSILON` (0.001; rule 9's own
constant, a strict-preference tiebreak against gratuitous spill-then-refill cycles; ≤ 1e-5 of the
water value). No other cost. Prices stay LP duals (rule 4); the new rows' duals are the marginal
water value at each plant-hour and are extracted for diagnostics only.

**Bounds:** `S_d ∈ [0, ∞)`, `V_d ∈ [0, B_d]`; every existing bound unchanged.

**What the rows do, stated so the armed test can falsify it:** a coupled plant can turbine in hour t
at most what arrived (lagged upstream turbine + spill flow, plus flat side inflow) plus what it
draws from its pond; a run-of-river plant's freedom to concentrate a month's budget into peak hours
is therefore bounded by `B_d` hours of flow instead of by the budget's `1/CF` (2.3–3.4× nameplate
hours, NWPP-32 §5(a)). Spill emerges as the slack wherever the budget cap is below the arriving
water — which is the ROD spill season at Bonneville and the lower Snake (NWPP-32 §5(c)) — with no
spill object of its own.

**Feasibility by construction:** the budget row is an upper bound with a zero floor (NWPP-32 stamped
no floor), so the rows can never make the LP infeasible; the only way they could change a monthly
total is by delivering LESS water than the budget needs. `I_d,m` is computed (§4.4) so that the
measured monthly water at d closes exactly on the measured CROHMS outflows, and `η` on the EIA-923
basis makes `E_d,m/η_d,m` equal the measured turbine flow; the residual leak is the τ-hour window
straddling each calendar-month boundary. Gate G-A1 measures it.

**Rule 2:** rows are assembled as ONE `coo_matrix` per coefficient family from `np.arange(T)`,
`np.roll` for the lag, `np.repeat/np.tile` for the plant × hour product; the only Python loop is
over the O(15) links.

**Row/column count at full NWPP scale:** 14 × 8,760 = 122,640 rows; 28 × 8,760 = 245,280 columns
(NWPP-32's estimate: ~123 k rows).

## 4. The measurements — method, source, and the STOP rule for each

All from `https://public.crohms.org/dd/common/web_service/webexec/getjson` (the HRFCPPA's own
compliance-data source), pulled per station × series × calendar quarter for 2023-01-01 →
2026-01-01 (the service refuses a full-year range), timezone = the service's fixed standard time
(the DST-transition hour 2023-03-12 02:00 is present, so no clock shift), quality code kept with
every value. The raw pull is committed as
`data/raw/nwpp-hydro/crohms/nwpp_crohms_hourly.parquet` (long: station, series, ts, value, quality)
with `SHA256SUMS.txt`; the derive script `scripts/data/build_nwpp_hydro_cascade.py` regenerates
every derived artifact from it (rule 23: re-derived only when CROHMS / NID / EIA-923 update, never
against a residual).

### 4.1 τ per link — MEASURED by cross-correlation of hourly outflows

For each link (u → d): take hourly `Flow-Out` at u and at d over 2023-01-01 → 2024-12-31 (two
complete years; 2025 is a hold-out check reported alongside), keep hours where both carry quality
code 0 (or the catalog's accepted codes — the code set is reported), and form the **high-frequency
anomaly** of each series: value minus its centred 25-hour moving mean (this removes the seasonal
co-trend that would otherwise put r ≈ 0.99 at every lag). For McNary, u is the SUM of PRD and IHR
outflows each lagged by its own candidate τ, searched jointly over a 2-D grid.
`τ_ud = argmax_{L ∈ 0..72 h} r(anom_u(t−L), anom_d(t))`. Reported per link: τ, r at τ, r at τ±1,
r at L=0, the 2023-only and 2024-only τ, and the 2025 τ.

**Acceptance (ex ante):** (i) r(τ) ≥ 0.30 and the peak is unique (r(τ) − max(r(τ±1)) > 0 —
plateaus are broken toward the SHORTER lag and reported as a plateau); (ii) 2023-only and 2024-only
τ agree to ±1 h; (iii) sanity: implied celerity = great-circle distance between the CROHMS station
coordinates (in the catalog) ÷ τ lies in **1–30 mph** for τ ≥ 1 h, and cumulative τ down the
mainstem is monotone in distance. A link that fails (i) or (ii) is **NOT coupled** (its downstream
plant keeps its independent budget) and the failure is reported; a link that fails (iii) STOPS the
lane on that link (reported, not substituted). **τ = 0 h is admissible** (adjacent projects with a
pooled reach can respond within the hour) and is reported as measured, not rounded up.

### 4.2 The pondage band B_d — NID surface area × MEASURED operated forebay range

NID (national CSV, rows by `NID ID`) supplies `Surface Area (Acres)` for every coupled plant; its
`Max Storage − Normal Storage` is reported as a cross-check ONLY — it reads 0.8 ft at Rocky Reach
and 17 ft at Wells, so it is not the operating band and is not used. The band in feet is measured
from the hourly `Elev-Forebay` series: `band_ft = p99.5 − p0.5` of quality-0 hourly forebay
elevation over calendar 2023 and 2024 separately (the year with the SMALLER band is used; both
reported; p0.5/p99.5 trim spikes), and `B_d [kcfs·h] = band_ft × area_acres / 82.6446` (1 kcfs·h =
3.6 M ft³ = 82.6446 acre-ft). Reported alongside: the p99 of the within-day range (a tighter
"pondage actually exercised daily" statistic — reported, not used), the band in hours of the
plant's published average discharge, and BPA's published order ("three to five feet") as the
sanity band: a federal run-of-river plant whose measured band falls outside 0.5–15 ft STOPS the
lane on that plant. A plant with no usable forebay series STOPS (reported, never substituted).

### 4.3 η_p,m — water-to-energy per plant-month, EIA-923 basis

`η_p,m = E_p,m(EIA-923, NWPP-32 budget artifact) / Σ_{t∈m} Flow-Gen_p(t)` [MWh per kcfs·h]. This
makes `Σ_t P_p/η_p,m` equal the measured monthly turbine flow exactly when the budget is filled.
A plant-month with no EIA-923 series (McNary 2025: `NO_923_SERIES`) takes the same month's η from
the nearest year that has one, and the substitution is listed. Reported: η by plant-month, and its
consistency with `Power.Total / Flow-Gen` (the CROHMS gross basis — the ratio EIA-923-net / CROHMS-
gross is expected ≈ 0.97–1.00 and is reported, not adjusted).

### 4.4 Side inflow I_d,m and head spill s̄_u,m — measured monthly means

`I_d,m = mean_{t∈m}[ Flow-Out_d(t) + ΔV_d(t) − Σ_u Flow-Out_u(t − τ_ud) ]` in kcfs, with
`ΔV_d(t)` from the forebay series × NID area (so a month that drew its pond down is not booked as
side inflow), the same τ as the LP uses, and the same cyclic wrap. `s̄_u,m = mean_{t∈m} Flow-Spill_u`
for the two heads. A negative `I_d,m` (measured outflow at d below lagged upstream outflow — a
metering or timing artefact) is reported and **floored at 0 with the magnitude listed**; if any
plant-month's floor exceeds 2 % of that month's arriving water the lane STOPS on that link.

### 4.5 What is committed under `data/raw/nwpp-hydro/`

`crohms/nwpp_crohms_hourly.parquet` (+ `SHA256SUMS.txt`, `README` row with the exact query form and
pull date); `nwpp_hydro_cascade_links.csv` (link, u, d, stations, τ, r-table, celerity, band_ft,
area_acres, B_d, NID id and cross-check, 2025 check); `nwpp_hydro_cascade_monthly.csv` (plant,
year, month, η, I, s̄, flags); `nwpp_hydro_cascade_nid.csv` (the NID rows used, verbatim columns).

## 5. The field — one, default-off, both ledgers, one commit

`ScenarioConfig.hydro_cascade_coupling: bool = False` — **ISO-agnostic name, per-ISO artifact**,
exactly the `hydro_budget_period_by_instrument` shape: the loader `data.hydro.load_hydro_cascade(iso,
year)` returns `None` when the ISO has no `<iso>-hydro/nwpp_hydro_cascade_links.csv`-class artifact,
the shared resolver `pipeline.kwargs.resolve_hydro_cascade(...)` then returns `UNSET`, and
`DispatchSpec.to_dispatch_kwargs()` omits the key — so every unarmed run, in every ISO, keeps a
byte-identical dispatch-kwargs key set and LP. Wired through BOTH orchestrators (`runner.py` and
`scripts/run_calibration.py`) via the one resolver — the nyiso-220 lesson.

Registration: appended at the **very end** of `_CACHE_KEY_OPTIONAL_FIELDS` (a SHARED field under
HOUSE-3) and `"hydro_cascade_coupling": "False"` at the very end of
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, **in the same commit as the field**. At its default it is
dropped from the hash; `True` enters the key. No `constants.py` table is added (the parameters are
the measured artifact, read at solve time), so no `solve_surface_declared.py` entry is needed;
`scripts/solve_surface_register.py --diff <base> <head>` must still read zero moves and is run.

Field docstring names the ruling (N3), the artifact, and the invariant of §1.

## 6. Byte-identity protocol (gate G8 as amended) — measured, not asserted

1. **Keeper `cache_key()` table, nine regions.** For each designated keeper bundle, every
   `run_config*.json` is re-keyed as `ScenarioConfig(**d["scenario_config"]).cache_key()` on a
   detached worktree at the base sha and on the branch head, with stored absolute paths re-rooted
   onto the worktree before construction (the NWPP-20 path-folding trap). SOCO and NWPP carry no
   keeper: their rows are the ISO default config (`ScenarioConfig(iso=<ISO>)`) and its backcast
   variant, keyed both sides. Also the two pinned literals (`ScenarioConfig().cache_key()` and the
   backcast default). **Any moved key is a STOP.** Reported as a table in the FINDING.
2. **LP OFF identity.** A scratch script builds `build_constraints` + `build_variable_bounds` +
   `build_cost_vector` for two fixtures (the `tests/unit/data/test_hydro.py` hydro fleet, 24 h and
   720 h) and prints `sha256` over `(A.indptr, A.indices, A.data, row_lower, row_upper, col_lower,
   col_upper, cost, layout fields)`; run on the base worktree and on the branch with the field at
   its default: identical or STOP. The same script with the mechanism armed on the fixture must
   differ (it is not a no-op when on).
3. `python3 scripts/check_cache_key_registration.py --base <base>` (checks 1–6),
   `scripts/check_mechanism_matrix.py --base <base>`, `scripts/solve_surface_register.py --diff`,
   `ruff`, and the unit lanes `tests/unit/model tests/unit/data tests/unit/pipeline tests/unit/config`
   plus `tests/regression/test_persisted_identity.py` — all green before the PR.

## 7. The armed-response measurement and its ex-ante gates

**Where it runs:** in this session, as **unit tests** (`tests/unit/model/test_hydro_cascade.py`),
which is what the Testing Pattern requires (trivial case first: 1 zone, 1 link, 24 h; then the real
chain). Rule 32 forbids this session a CALIBRATION solve (`run_calibration*.py` / `replay_keeper.py`
— minutes of LP, GBs of RAM); a reduced LP of ≤ 20 generators × 744 hours is a test, and the codebase
runs hundreds of them in-session. No shard is spent (§9).

**Fixture (the real chain, reduced system):** one zone; the 16 chain plants (14 coupled + 2 heads)
at their EIA-860 nameplates with their NWPP-32 EIA-923 monthly budgets; the measured τ, B_d, η, I,
s̄ from §4; a stand-in thermal fleet of three gas classes at fixed costs and a demand series shaped
as the measured NWPP-NW diurnal (from the committed EIA-930 pool, one month) scaled so the chain
supplies ≈ 55 % of energy (its measured share); two months solved separately as 744/720-hour
horizons: **January 2023** (low flow, no spill — the month the rows bind) and **May 2023** (the
freshet, spill season — the month the spill object must appear). Each month solved twice: field
off (budget only) and on.

**Gates (STOP gates — they can kill the arm, never promote it; none reads a residual):**

* **G-A1 (the rule-19 invariant):** for every coupled plant and both months, monthly energy ON
  equals monthly energy OFF to within **0.5 %** (both equal the budget when the plant fills it). A
  larger move means the rows changed HOW MUCH → the arm is refused.
* **G-A2 (the identity holds):** for every coupled plant-hour, `P_d/η ≤ arrivals + V_d(t−1)` to
  1e-6 kcfs, and the row residual is 0 to solver tolerance.
* **G-A3 (direction and magnitude, low-flow month):** for each coupled RUN-OF-RIVER plant (BON, TDA,
  JDA, MCN, RIS, CHJ, the four lower Snake) the mean within-day amplitude `(daily max − daily min)/
  daily mean` of P_d falls from the OFF value to at most the **pre-solve bound** `A*_d =
  min(η·(Q̄_arr + B_d/H), pmax)·…` computed in the FINDING before the solve — concretely: the ON
  amplitude must be ≤ the OFF amplitude by at least **30 %** at the median RoR plant, and the ON
  daily peak at every RoR plant must be ≤ `η_d·(Q̄_arr,d + B_d/1 h)` (the one-hour draw bound) with
  the observed peaks reported against that bound. The measured BPAT amplitude (0.55, NWPP-32
  §5(b)) is the reference the ON value is compared to, reported, never gated.
* **G-A4 (spill season signature):** in May, `Σ_t S_BON > 0` and the LP's monthly spill at BON,
  IHR, LMN, LGS, LWG equals the measured CROHMS monthly spill to within **±10 %** (it should close
  by construction: arrivals measured, turbine flow = budget/η); in January, LP spill at every
  coupled plant ≤ the measured January spill + 5 % of arrivals.
* **G-A5 (lag signature):** for links with `B_d ≤ 6 h` of flow, the cross-correlation of hourly
  `P_d(t)` with `P_u(t−τ)` is higher ON than OFF in January.
* **G-A6 (OFF identity):** §6 item 2.

**Predictions (P), written before the solve:** P1 G-A1 leak < 0.2 % (the τ-window at the month
edge). P2 the OFF amplitude at RoR plants ≈ 1/CF-limited (> 1.5) and the ON amplitude at BON/TDA/
JDA ≤ 0.8. P3 GCL's own shape is nearly unchanged ON vs OFF (it is a head with 3.98× freedom; the
rows only bind what is below it). P4 May spill closes within ±5 %. P5 τ down the mainstem
accumulates to well under a day GCL→BON (the wave runs through pools, not at water velocity).

## 8. What I do if a quantity cannot be measured

Per link, per §4.1–4.4: **STOP on that object and report** — the link is left uncoupled, the plant
keeps its independent budget, and the FINDING says which link, why, and what would measure it. No
value from memory, no rule-of-thumb travel time, no "3–5 ft" substituted for a measured band (rule
13). Already known at this writing: the three Hells Canyon links (§2) — daily-only CROHMS series.

## 9. Rule 32 / 34 posture — no shard is launched, and why

The exit asks for an ARMED run that visibly redistributes; §7 delivers that on the real chain
inside the real LP builder at test scale. A full-footprint NWPP solve is **NWPP-40's charter** (W4,
"coupling ARMED", ONE shard, ONE span) and would be the first NWPP solve ever — its failures would
not be separable from this mechanism's. Launching it here would charter across the W3b/W4 boundary
(collision rule 9). If the desk wants a rule-29 screen of the arm ahead of NWPP-40, that is one
shard pushing its bundle (rule 34) and is offered in the FINDING, not spent here.

## 10. Files this lane touches (and nothing else)

* `src/market_sim/model/lp/hydro_cascade.py` (NEW: the spec dataclass + vectorised row builder);
  `model/lp/layout.py` (+ `n_cascade` block after `dis_tranche`); `model/lp/rows.py`,
  `bounds.py`, `costs.py`, `model.py`, `__init__.py` (thread the spec; result diagnostics
  `hydro_cascade_spill` / `hydro_cascade_storage`; cross-year column map); `data/hydro.py`
  (`load_hydro_cascade`); `pipeline/kwargs.py` (`resolve_hydro_cascade`), `pipeline/spec.py`
  (`hydro_cascade: Any = UNSET`), `pipeline/__init__.py`; `runner.py` + `scripts/run_calibration.py`
  (one call each, beside `resolve_hydro_period_hours`); `config/scenarios.py` (field + two ledger
  lines).
* `scripts/data/build_nwpp_hydro_cascade.py` (NEW) and the §4.5 artifacts + README rows.
* `docs/codebase-site/data/mechanism-matrix.js` (base row `hydro_cascade_coupling`) + ONE cell line
  in each of the nine shards (NWPP carries the verdict; eight foreign shards `·`).
* `tests/unit/model/test_hydro_cascade.py`, `tests/unit/data/test_hydro_cascade_loader.py`.
* This PRECOMMIT and `docs/handoffs/FINDING-nwpp-36-2026-09-16.md`.

**Not touched:** NWPP-32's artifacts; `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT`; `constants.py`;
`solve_surface_declared.py`; `scripts/calibration_verdict.py`; `frontend/data/**`; the plan, the
ledger, `docs/calibration-log/nwpp.md`, `CHANGELOG.md`, `docs/mechanism-testing-matrix.md`; any
other region's files.

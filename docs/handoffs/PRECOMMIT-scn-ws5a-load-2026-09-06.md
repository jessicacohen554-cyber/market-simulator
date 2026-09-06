# PRECOMMIT — SCN-WS5A-LOAD: the Stage A-LOAD campaign, six ISOs

**Lane** SCN-WS5A-LOAD (all six ISOs in one invocation — see §1.1) ·
**Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws5a-load-campaign-f5znk9` · **Data profile** all six hydrated ·
**Pin** `origin/main` `821c11c5` (re-fetched before the first solve; the two commits
since `f4db00c8` — `f56e23cd` nyiso-198 PREREG, `b47b42f8` SCN-WS1b-r2 pre-registration —
are **docs-only**, verified zero diff on `src/`, `scripts/` and `configs/`, so §2's G-DRIFT
audit and §3's phase 0 carry unchanged) ·
**Campaign** `scn-campaign-load-2026-09-06` (kind `scenario`, `reference_case: REF`) ·
**Charter** readiness plan §3 WS-5 Stage A / §3.5 / §4 / §6 **ruling S5** ·
**Scored against** `docs/handoffs/load-hi-adequacy-reading-2026-09-06.md` (SCN-WS4b) and,
where a T0 verdict exists, `docs/handoffs/FINDING-scn-ws4c-2026-09-06.md` §3.

**Pushed before the first solve** (rule 29). Every number in §3 is zero-LP: a constant at this
commit, a committed trajectory, or arithmetic on the two. Nothing below is revised after a
solve; §5's predictions are scored as written, misses at full magnitude.

---

## 0. Bottom line, before any LP

1. **The load constants moved under WS-4b's pin, and that changes which legs are worth
   solving.** `d14a7ed0` ("SCN-LOAD: curate the six published ISO load forecasts") landed
   after WS-4b's pin `af6269cf` and re-derived the whole load-shape constant family —
   473 insertions / 263 deletions in `constants.py` alone, covering
   `DEMAND_GROWTH_RATES`, `DATACENTER_ADDITIONS_MW` and `ELECTRIFICATION_LAYERS`.
2. **CAISO's ORGANIC arm is NOT degenerate at HEAD and WILL be spent.** WS-4b §3 and §6 and
   WS-4c §1 both record CAISO as `high := mid`, byte-identical, "should not be solved". The
   CEC Form 1.1c *Local Reliability Scenario* has since been read: `high` is now
   **4,240 MW at 2030 against mid 1,622 MW**. This lane solves 16 legs, not 15.
3. **PJM and NEISO stay degenerate — PJM for a NEW reason.** PJM's `high := mid` at *every*
   anchor now (the limitation moved from CAISO to PJM when the published B-9b series
   overtook the retired 30 GW queue estimate), not merely "equal through 2030". NEISO still
   ships `{}`. Same operational conclusion; different mechanism, stated so the record is right.
4. **ERCOT's tail regime is predicted NOT to reproduce**, and that is this lane's headline
   test (§3.3). Both changed inputs push `dc_E/E` the same way — the DC high anchor fell
   122 → 88.6 GW nameplate (−27 %) while ERCOT's growth rate *rose* — so the ratio WS-4b
   computed as **1.019 (TAIL)** at 2030 is predicted to land **well below 1.0 (relocate)**.
5. **G-DRIFT reads LIVE on every ISO, twice over** (§2): 82 files / +9,529 lines on the solve
   path, *and* a load-constant re-derivation that makes the committed REF trajectories
   unreproducible at HEAD. Rule 29(b) form 4 is invalid for all six. The control is this
   lane's own same-HEAD REF leg.

---

## 1. Scope

### 1.1 One session, six ISOs — recorded, not assumed

The charter contemplates six per-ISO sessions. This session was launched once, on the
`campaign` branch stem rather than an ISO stem, on a container with **all six ISOs'
`data/raw` hydrated**, and `git ls-remote` shows **no sibling `ws5a` branch**. So the
per-ISO disjointness the charter protects is satisfied by there being one lane, and the
six per-ISO deliverables are produced from here. If a sibling ISO lane launches later,
this lane's out-dirs and registrations are already namespaced per ISO.

### 1.2 RUN — ruling S5's load half only

`REF`, `LOAD-HI`, `LOAD-HI-ORGANIC` at **T1-F 2026–2030**, from the committed
`configs/scenario_campaign_matrix.yaml`, consumed exactly as committed (SCN-LEVELS / ruling
S3). Every base config is `configs/scenarios/<iso>_scenario_base_2026_2030.yaml`, verified
`mode: forecast`, `start_year: 2026`, `end_year: 2030` — **5 solve-years, so no leg widens**
past §2.1b's cap.

### 1.3 DO NOT RUN — held by S5

No `CES-*`, no `CARB-*` T1-F leg, no `ALL-CLEAN`, no `VOL-*`. Those are Stage A-POLICY,
held pending the capx CCS emission-rate repair (SCN-WS2b §8: retrofitted `gas_cc_ccs` is
credited at 0.95 by the CES while carrying an uncaptured `emission_rate`; NEISO 2030 CO2
**+9.99 Mt as scored vs −6.01 Mt** with capture applied). My three cases arm neither the CES
nor a carbon price, so they carry **no CCS credit exposure**.

**But the retrofit screen still runs in 2028–2030.** `ccs_retrofit_available_year` is 2028
and `ccs_retrofit_capex_co2_scaling` is default-ON since capx D60. So any `gas_cc_ccs`
conversion appearing in my 2028–2030 evolution ledgers is **reported and flagged** as
information the held half needs. It is never a reason to widen scope.

### 1.4 The 16 legs

| ISO | legs | why |
|---|---|---|
| ERCOT | REF · LOAD-HI · LOAD-HI-ORGANIC | DC axis live (gap 14.7 → 50.4 GW nameplate) |
| CAISO | REF · LOAD-HI · LOAD-HI-ORGANIC | **DC axis live at HEAD** (gap 0.55 → 2.62 GW) — §3.1 |
| MISO | REF · LOAD-HI · LOAD-HI-ORGANIC | DC axis live (gap 0 → 7.07 GW) |
| NYISO | REF · LOAD-HI · LOAD-HI-ORGANIC | DC axis live (gap 0.24 → 0.85 GW) |
| PJM | REF · LOAD-HI | `high := mid` at every anchor — ORGANIC is a guaranteed-zero delta |
| NEISO | REF · LOAD-HI | `DATACENTER_ADDITIONS_MW["NEISO"] == {}` — block is 0 MW in every year |

---

## 2. G-DRIFT (rule 29(b)) — LIVE on every ISO, on two independent grounds

Recorded before the first solve so it cannot be written to fit a result.

### 2.1 Code drift

`git diff a35c9f9b HEAD -- src/market_sim scripts/run_full_horizon.py scripts/run_ces_leg.py
scripts/lib` (the `ff-t1f-d50` basis WS-4c audited) — **82 files, +9,529 / −894**. Hunks on
the ISO-agnostic **forecast** path, all **LIVE**, none classifiable INERT:

| file | Δ | why LIVE for a `mode="forecast"` T1-F leg |
|---|---|---|
| `capacity_evolution/retirements.py` | +915 | step 1/3, every ISO, every year |
| `capacity_evolution/adequacy.py` | +298 | the backstop — the responding channel in five of six ISOs |
| `runner.py` | +296 | the P0→P1 year loop itself |
| `pipeline/solve.py` | +213 | the P0→P1 seam |
| `policy/carbon.py` | +215 | resolved carbon signal (zero here, but on the path) |
| `capacity_evolution/ccs.py` | +185 | the retrofit screen, live 2028–2030 (§1.3) |
| `results/emissions.py` | +135 | the import-CO2 line this lane must report |
| `capacity_evolution/new_entry.py` | +82 | the entry ladder |

### 2.2 Input drift — the stronger half

`git diff af6269cf HEAD -- src/market_sim/config/constants.py` = **+473 / −263**, and it
re-derives the load-shape family that *defines this campaign's cases*. Measured consequence:
compounding HEAD's own `resolve_demand_growth_rate` against each committed REF bundle's own
2026 row **fails to reproduce that bundle's trajectory** —

| ISO | committed REF 2030 TWh | HEAD-table projection | error |
|---|---|---|---|
| ERCOT | 740.2 | 906.0 | **+22.4 %** |
| PJM | 1,005.4 | 1,121.6 | **+11.6 %** |
| MISO | 776.3 | 849.1 | +9.4 % |
| NEISO | 123.4 | 120.7 | −2.3 % |
| CAISO | 265.8 | 269.6 | +1.4 % |
| NYISO | 161.9 | 161.7 | −0.1 % |

The committed bundles were solved on the pre-SCN-LOAD growth table. **Differencing a HEAD
arm against them would difference two different load worlds** — a defect that would dwarf
the 2.821 Mt NEISO staleness WS-4c found, and it reaches ERCOT and PJM hardest.

### 2.3 Verdict and what it does NOT authorize

Form 4 is **invalid for all six ISOs**. The control is this lane's **own same-HEAD REF leg**.
That is not a "control solve" under rule 29(b): `REF` is the campaign's `--reference-case`
and every delta is measured against it, so it is solved because it is a case, not to
establish drift. **No control solve is spent**, and no pre-campaign REF is reused.

---

## 3. Phase 0 (rule 29 step 0) — zero LP

Resolved through `matrix_configs(base, SweepDefinition.from_yaml(campaign))`, i.e. the same
config object `run_ces_leg.py` hands the solver, so the census cannot drift from what the
solve applies. Verified the two load cases differ in **exactly one field**
(`datacenter_load_path`) in all six ISOs.

### 3.1 The DC block at HEAD vs what WS-4b read (nameplate MW, ×0.85 → block)

| ISO | WS-4b's cited `high` | HEAD `high` @2030 | HEAD `mid` @2030 | ORGANIC arm |
|---|---|---|---|---|
| ERCOT | 122 GW @2030 | **88,603** | 38,182 | spend |
| CAISO | `high := mid` | **4,240** | 1,622 | **spend — reading superseded** |
| PJM | 30 GW @2030 | 38,815 | 38,815 | **degenerate** (`high := mid`) |
| NYISO | 10 GW @2031 | **2,567** | 1,716 | spend |
| MISO | 27 GW @2030 | 27,067 | 20,000 | spend (WS-4b reproduced) |
| NEISO | `{}` | — | — | degenerate |

`constants.py` states each replacement in its own words: ERCOT's 122 GW was "a raw
interconnection-queue estimate" replaced by ERCOT's published upper forecast; NYISO's 10 GW
was "the raw interconnection QUEUE … a different quantity from the forecast"; CAISO's gap is
"CLOSED"; PJM "issues no upper case … the SAME documented limitation CAISO used to carry, and
it moves here rather than disappearing."

### 3.2 What this does and does not say about WS-4b

WS-4b's arithmetic was **correct against the constants it was written on** — WS-4c reproduced
it to the decimal. What changed is the constants, by an owner-ruled data intake (S4/D-4) that
landed after their pin. So a WS-4b reading that misses **because an anchor was retired** is
scored as a MISS *of the prediction* with the cause named as input drift, not as a reasoning
error — the same distinction WS-4c drew for NEISO's backstop (§3.7/§4).

### 3.3 THE ERCOT TAIL-REGIME PREDICTION — this lane's headline test

`add_datacenter_block` relocates while `dc_E < E` and adds on top once `dc_E ≥ E`. WS-4b
computed ERCOT 2030 at `dc_E/E = 1.019` → TAIL, energy 800 → 1,800 TWh, peak 94 → 267 GW,
"an unserved-energy year by construction … its CO2 delta is not an emissions response."

At HEAD **both** inputs move the ratio down: the numerator falls (DC high −27 %) and the
denominator rises (ERCOT REF growth 13.48 %/yr, high 20.62 %/yr at HEAD). Computed on
HEAD's tables, `dc_E/E` peaks at **≈0.54 in 2030**.

> **PREDICTION P-1.** ERCOT stays in the **relocate** regime in all five years of both cases.
> No tail-regime step; no 1,800 TWh year; no ~960 TWh of shed energy. WS-4b's ERCOT §2.1
> discontinuity **does not reproduce at HEAD**.
>
> *Stated bound, because my `E` anchor is itself inverted from a stale-table bundle:* the
> ratio must clear 1.0 to falsify P-1, and 0.54 is not near the boundary. If the solved 2030
> ratio lands in [0.9, 1.1] I will report P-1 as **undecided on the arithmetic** rather than
> claim it, and let the solved regime flag decide.

Consequence if P-1 holds: WS-4b's ERCOT (b)/(c) clauses that are *conditioned on the tail*
become untestable-as-written, and the relocate artefact they warn about (peak below REF,
I12 reading better than REF) is predicted to persist through **2030** rather than ending in
2029.

---

## 4. WS-4b's reading, restated per ISO — the thing I score against

Verbatim in substance from `load-hi-adequacy-reading-2026-09-06.md` §5. Not revised.

| ISO | (a) mechanism | (b) invariants at `mid` → widening | (d) delta-table line | (e) import line |
|---|---|---|---|---|
| **ERCOT** | scarcity-priced economic entry **or nothing** (VOLL slack); backstop OFF by design | {I12, I3} 2027–30; widening **non-monotone** — I12 expected to *improve* on the relocate artefact, I3 ambiguous in sign | `unserved_mwh` beside `emissions_mt`; `backstop_built` = **0.0** (non-zero = config defect); CO2/served MWh; `hours_ge_500` | **0.0 exactly** — no import node |
| **CAISO** | backstop `gas_ct` to the requirement gap + entry ladder | {I12, I7} 2026–28; I7 misses widen ≤ ~5.5 GW, backstop share rises above 52.6 % | `backstop_built_mw`/`_mwh` + `unserved_mwh` | **UP**, same sign as CO2; ≤ ~7–11 Mt ceiling |
| **PJM** | cap-bound backstop ladder is the **only** responding channel | {I12, I7} 2027–30; I7 to **tens of GW**, share above 43.9 %, **I3 appears 2029–30** | `backstop_built` + `unserved_mwh` | **UP and small**; exports fall, clamped, no offset |
| **MISO** | backstop + entry ladder + D53 sector gate | {I12, I7} 2026–29; share expected to **cross 30 % (CAVEAT → FAIL)**; I3 may reappear 2029–30 | `backstop_built` + `unserved_mwh` | **0.0** both cases; a non-zero is a seam rung activating |
| **NYISO** | backstop armed, never fired; economic entry | none (14/14 PASS); I7/I12 read **better** on the flattened peak; possible **high-side** I12 exit 2029–30 | `backstop_built` (expect 0.0) + `unserved_mwh` (expect 0.0) | **UP**; HQ_hydro at firm depth, increments on 0.428 rungs |
| **NEISO** | backstop + reliability-floor retention | none, but I7 thin (+810/+419/+334 MW); backstop **fires**, share 1.2 % → 10–30 % CAVEAT | `backstop_built` + `unserved_mwh` + import line **per tranche** | rises **early** (≤ ~2.1 Mt) then **saturates** by 2029–30 |

**(c), common to all six.** A reader may conclude: the direction of the fleet response; the
in-ISO CO2 rise at the **implied marginal** rate (§5); CO2 per **served** MWh; how much of the
delta is administratively-built backstop CT. A reader may **not** conclude: a CO2 total
(understated by shed energy and by the import increment); adequacy from an I12 that improved
on the relocate artefact; that `LOAD-HI − LOAD-HI-ORGANIC` is "DC emissions" (it is the
block's **shape** effect at fixed energy); a deployment forecast from a HOLD ISO.

**Where WS-4c already scored a T0 verdict** (§3.1: ERCOT 4 HIT; CAISO (e) SPLIT; PJM 4 HIT;
MISO (b) SPLIT; NYISO (b) SPLIT; NEISO (a)/(b) MISS), I additionally report whether the
horizon **agrees with** that T0 verdict. A T0 HIT that becomes a horizon MISS is itself a
finding.

---

## 5. My own predictions — against the IMPLIED MARGINAL rate, not the fleet average

**I am using my ISO's measured WS-4c ratio, per the charter.** WS-4c measured that
"CO2 ≈ fossil-average × added fossil-served MWh" is biased **high by 23–35 % where coal is
inframarginal** and **low by 5–17 % where it is not**:

| ISO | WS-4c T0 implied rate t/MWh | fleet avg | ratio | coal inframarginal |
|---|---|---|---|---|
| ERCOT | 0.447 | 0.610 | 0.73 | yes |
| PJM | 0.508 | 0.663 | 0.77 | yes |
| MISO | 0.484 | 0.749 | 0.65 | yes |
| CAISO | 0.405 | 0.387 | 1.05 | no |
| NYISO | 0.422 | 0.402 | 1.05 | no |
| NEISO | 0.450 | 0.384 | 1.17 | no |

> **P-2 (magnitude).** In every ISO and every year, `ΔCO2 ÷ Δ fossil-served MWh` lands within
> **±25 %** of that ISO's WS-4c T0 implied rate above. I predict the *rate*, not the level,
> because the level depends on a Δ-energy the solve determines.
>
> **P-3 (the sign of the bias holds).** At 2026 the ratio to fossil-fleet average stays
> **< 1.0** in ERCOT / PJM / MISO and **≥ 1.0** in CAISO / NYISO / NEISO — WS-4c's 3–3 split,
> reproduced at HEAD on re-derived load constants.
>
> **P-4 (the ratio drifts UP toward 1.0 by 2030), mechanism-grounded.** Coal retires across
> the window (step 1 dated exits + step 3 economic screen), so the inframarginal coal that
> *dilutes* the marginal rate downward is progressively removed. I therefore predict the
> coal ISOs' ratio **rises monotonically or near-monotonically 2026 → 2030**, and that no
> gas-dominated ISO's ratio falls below 1.0. This is a prediction about *retirement*, and it
> is the one I most expect to be wrong on timing.
>
> **P-5 (fossil share of the energy delta falls).** At T0 the added energy was 78–99 %
> fossil-served. With five years of entry (VRE + storage + backstop CT), I predict the
> fossil-served share of Δenergy **falls in every ISO** between 2026 and 2030, most in CAISO
> (solar-rich entry) and least in ERCOT (no backstop, energy-only).
>
> **P-6 (leakage).** `import_co2_mt_reported` rises in NEISO and NYISO; is **0.0** in ERCOT
> (no node) and MISO (no tranches); rises and is small in PJM. **CAISO is the open one**:
> WS-4c measured its 2026 increment landing entirely on a **zero-EF solar rung**, so the line
> did not move. I predict that at the horizon CAISO's zero-EF headroom is **exhausted** and
> the line becomes **positive by 2029–2030** — the first year it moves is the number to report.

---

## 6. The STOP gate — structural, kill-only

Pre-registered, and it is **never gated on a residual** (rule 1 `[R-STRUCT]`). It may kill an
arm; it may never promote one; it contributes to no determination.

| # | gate | kill condition |
|---|---|---|
| S1 | **direction** | CO2 does **not** rise, or load-weighted price does not rise, under LOAD-HI vs REF in a year with no binding slack |
| S2 | **magnitude band** | implied marginal rate outside **[0.5, 2.0] ×** the ISO's fossil-fleet average (WS-4c's own band) |
| S3 | **footprint confinement** | a CO2 delta appears in a class the added load cannot reach — non-zero Δ in nuclear/hydro/VRE CO2, or `by_fuel["import"]` ≠ 0 |
| S4 | **identity** | `LOAD-HI` and `LOAD-HI-ORGANIC` annual **energy** are not equal where phase 0 says the block relocates (energy-invariance is the mechanism's own claim) |
| S5 | **no collateral flip** | a **non-target load-bearing** criterion flips PASS → FAIL for a reason unrelated to load |

An arm killed by the gate is reported as the session's result and its remaining years are not
spent. A gate PASS means only "the mechanism did what its arithmetic says"; it is not evidence
for any reading.

---

## 7. Budget and scheduling

Anchors are **WS-4c's measured** rates (§1 of their FINDING), not the charter's older ones.

| ISO | legs | solve-yrs | measured min/yr | est. |
|---|---|---|---|---|
| NEISO | 2 | 10 | 1.6–2.0 | ~18 min |
| ERCOT | 3 | 15 | ~2.0 | ~30 min |
| NYISO | 3 | 15 | 2.3–2.6 | ~37 min |
| PJM | 2 | 10 | 5.9–6.0 | ~60 min |
| MISO | 3 | 15 | 6.3–6.7 | ~98 min |
| CAISO | 3 | 15 | 7.1–7.7 | ~111 min |
| | **16** | **80** | | **≈ 5.9 h serial** |

Plus `data/clean`, absent on this container, built once (in flight at write time).

**Rule 12.** Years **sequential within every invocation, always**. Concurrency: **1** whenever
a per-plant multi-zone ISO (PJM / MISO / CAISO) is solving — WS-4c measured MISO at **9.7 GB
peak RSS on a 15 GB box**, so this is necessary, not cautious. At most 2 concurrent among
{NEISO, ERCOT, NYISO}, RSS checked first. Order is **cheapest first**, so a session that runs
short still banks complete ISOs. `MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1
OMP_NUM_THREADS=1` on every leg. Solves run in-session, never on a CI runner.

---

## 8. Duties this lane accepts

- **No default moves, no knob moves, no `ScenarioConfig` field is added.** Every arm is the
  shipped posture plus one or two `--set` overrides from the committed campaign YAML.
  **DOF ledger: zero free parameters**; no `authorized_price_tuning` (rule 1's carve-out is
  a backcast offer-curve channel and is not touched by a forecast lane).
- **Consume, never edit:** `configs/scenario_campaign_matrix.yaml`,
  `scripts/report_scenario_deltas.py`, `scripts/collate_scenario_campaign.py`,
  `scripts/register_forecast_run.py`, anything under `src/`,
  `model/capacity_evolution/ccs.py`, `frontend/data/*`.
- **Rule 15 / §7.5:** every leg registers into the **forecast** namespace under campaign
  `scn-campaign-load-2026-09-06`. The backcast registry is never touched.
- **Rule 29(c):** no screen bundle and no control bundle is produced — the 16 legs are
  registered campaign arms.
- **Rule 27:** no existing source file ≥300 lines is rewritten; pushes verified by fetch-back.
- **Rule 28(b):** the `datacenter_load_path` / `demand_growth_path` cells of each ISO's
  matrix shard are re-stamped as the **last** commit, after `git fetch origin main` + rebase.
- **Backcast byte-identity:** untouched — forecast-mode only, no default moved.

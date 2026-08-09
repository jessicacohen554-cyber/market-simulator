# ARM3-MEASURE — the longer-horizon MISO measurement of the MN/MI clean-tier rows

**Owner decision D-28 option A, step 3 (sitting Addendum AF.3): evidence for the Arm-3
(`miso_clean_tier_rows`) arming card.** MEASUREMENT ONLY. **No arming decision, no keeper
contact, no backcast-registry touch.** The arming card is the MANAGER's to put and the
OWNER's to sign; this document is its evidence table.

**Head at lane start:** `origin/main` `e9f99e6`. Branch
`claude/arm3-clean-row-horizon-ifcfsb`, cut at that head with zero divergence.

Authority: `docs/handoffs/d28-45u-composition-memo-2026-08-08.md` §2.1 (the fleet the rows
pay); `docs/handoffs/f2-45u-composition-2026-08-09.md` (the landed §45U seam);
`docs/handoffs/ffr-7b2-rps-krow-clean-rows-2026-08-06.md` §3.2 (the established 2026–2030
quiet window); `config/capacity_market.py` `MISO_CLEAN_TIER_REGIONS` + `STATE_RPS_ACP["MISO"]`.

---

## 0. PRE-REGISTRATION (written and committed BEFORE any solve)

This section was committed in its own commit, before either leg was launched. Nothing below
it was edited afterwards except where a line is explicitly marked as a post-solve result.

### 0.1 The window, and why 2031–2035 is the right one

The 2026–2030 window is ALREADY ESTABLISHED as quiet (FFR-7B-2 §3.2: both clean rows slack,
dual 0 in every year, whole trajectory identical to the Arm-2 leg to the digit). It is cited
here, not re-solved. The open question is the RAMP YEARS.

Reproduced from `policy.clean_tiers._clean_tier_target` against the shipped
`MISO_CLEAN_TIER_REGIONS` (no solve; this reproduces the FFR-6B §6.2 adjudication table
exactly — MN .616/.693/.770 and MI 0/.456/.570 at 2030/35/40):

| year | MN statutory | MN obligation (× .77 West share) | MI statutory | MI obligation (× .57 East share) |
|---|---|---|---|---|
| 2030 | 0.8000 | 0.6160 | 0.0000 | **0.0000** |
| 2031 | 0.8200 | 0.6314 | 0.0000 | **0.0000** |
| 2032 | 0.8400 | 0.6468 | 0.0000 | **0.0000** |
| 2033 | 0.8600 | 0.6622 | 0.0000 | **0.0000** |
| 2034 | 0.8800 | 0.6776 | 0.0000 | **0.0000** |
| 2035 | 0.9000 | 0.6930 | 0.8000 | **0.4560** |

**Why this window and not another.** MI's tier has its first statutory knot at 2035 (2023
PA 235) and the zero-before-first-knot convention imposes NOTHING before it. MI's obligation
is therefore *exactly* zero in 2031–2034 and steps discontinuously to .456 of MISO-East load
in 2035. **2031–2035 is the earliest ≤5-solve-year window that contains MI's onset year at
all** — it captures the step exactly at the window's last year, while spanning MN's +6.2 pp
ramp (.6314 → .6930). A window starting later would spend the locked ≤5-year budget on years
past the onset rather than on the onset itself.

### 0.2 Seeding — a STATED LIMITATION, not a silent one

**The 2031 leg starts from a COLD fleet, and no available protocol avoids that.** Verified
against the code, not assumed:

* `runner.py::run_scenario_iso` builds the fleet once at `start_year` and evolves it only
  inside its own year loop (`for year in range(start_year, end_year + 1)`, :1453). The
  persistent `fleet` object lives entirely within one invocation.
* There is **no cross-invocation fleet-state handoff**. The evolution ledger
  (`results/evolution_ledger.py`) is a write-then-read *record*; nothing seeds a run from it.
  Announced retirements and confirmed exits ARE seeded through `start_year - 1`
  (`_seed_through`, :1358/:1387), and the EIA-860 planned-additions pipeline is applied, so
  the **exogenous** fleet is correctly aged to 2030. What a cold 2031 start omits is the five
  years of **endogenous** economic entry/retirement.
* The only way 2031 could inherit 2026–2030 evolution is a single invocation spanning
  2026–2035 = **10 solve-years**, which `config/schedulable.py::assert_schedulable` refuses
  (`end - start + 1 > 5`) without `--full-solve-authorized`. **No such owner authorization
  exists for this lane**, and this charter does not carry one.

**Consequence for the prompt's suggested fallback.** Running 2026–2030 armed as "invocation 1"
would NOT seed invocation 2 — invocation 2 rebuilds the fleet cold at 2031 regardless, because
the cache short-circuits the per-year LP solve, never the fleet build. That leg would cost
~62 min and seed nothing. **It is therefore deliberately not run**, and the reason is recorded
here rather than left as an unexplained omission.

**How the limitation is handled:** both legs are seeded IDENTICALLY (same cold 2031 fleet,
same posture, one flag apart), so the **arm-vs-control DELTA (R4) is exact and carries no
seeding caveat at all**. The **LEVEL** reads (R1 onset/ceiling, R3 supply-vs-target) carry the
caveat, and its DIRECTION is pre-stated: FFR-7B-2 §3.1 measured 2026–2030 endogenous growth of
VRE 39.0 → 49.0 GW. Omitting that clean build **understates qualifying supply**, which biases
the rows toward binding **MORE** and **EARLIER**. So a slack row in this measurement is a
*strong* result (slack despite a conservative supply seed); a binding row is a *weak* one
(it may be the seed, not the statute). Pre-stated so it cannot be chosen after the fact.

### 0.3 The two legs

Identical postures, ONE delta. `--golden-posture` matches FFR-7B-2 and resolves MISO
curve-ON, which is the shipped posture (`shipped_capacity_clearing_by_iso()` →
`{PJM, MISO, CAISO, NEISO}: True`; owner C.4(a) B1 made golden and shipped one answer).

| leg | command delta | `miso_rps_compliance_regions` | `miso_clean_tier_rows` |
|---|---|---|---|
| CONTROL | *(none)* | **True** — via MISO's `ISOConfig.default_scenario_overrides` (owner D-26) | False |
| ARM | `--miso-clean-tier-rows` | **True** — same route | **True** |

**Arm 2 is already the MISO forecast default**, so the control IS "the standing MISO forecast
posture" without any flag. Verified mechanically: `runner.py:1015-1023` applies an ISO override
only where the caller left the field at its `ScenarioConfig` default, and `reference_config`
passes `miso_rps_compliance_regions=False`, which *equals* the default — so the override fires
and the field resolves True in BOTH legs. The cache key is computed after the overrides are
applied (:1026), so both keys record the armed Arm-2 grain. `entry_vre_capacity_revenue=True`
rides the same override in both legs.

Run **serially**: 15 GB box, FFR-7B-2 measured peak RSS ≈ 9.6 GB/leg, so two concurrent legs
would OOM (rule 12's memory cap). ARMED leg runs FIRST — per the charter, if time runs short
it is the one that must land.

### 0.4 PRE-REGISTERED READS (R1–R5) and pre-stated expectations

No read is a target. Each expectation below is stated so that a miss is visible as a miss.

* **R1 — the MN and MI row duals by year: onset (first nonzero), level, and whether the $30
  ACP ceiling binds.**
  *Expectation:* **MI dual is EXACTLY 0 in 2031–2034 by construction** (zero obligation ⇒
  RHS 0 ⇒ any non-negative qualifying generation satisfies the row). This is an arithmetic
  certainty, not a prediction — if it is violated, the mechanism is defective and that is the
  finding. **At 2035 MI is expected to BIND, most likely pinned at the $30 ACP ceiling**:
  FFR-6B §2.2 measured MISO-East short 21.7 pp by 2035 against an East-ONLY eligibility mask
  (`("MISO-East",)`), and MI's *renewable* row already pins at $30 in every year of 2026–2030.
  **MN is expected to stay SLACK (dual 0) through 2035** — its +6.2 pp ramp is covered under
  the 5-zone Midwest-footprint eligibility mask for the same reason FFR-7B-2 §3.2 found it
  covered at 2030.
* **R2 — the composed nuclear revenue at the LANDED F-2 seam for the §2.1 fleet.**
  Which reactors earn which row, with the cross-state mask flagged. *Expectation:* **if MI's
  dual sits at the $30 ceiling, the arming question is COMPOSITION-INDEPENDENT** — D-28 §2.3
  and F-2 §0(3) both measure all defensible compositions coinciding **to the cent** at
  D = $30. The F-2 seam only goes live at an **interior** dual.
* **R3 — qualifying supply vs target by region-year**: WHY the row binds when it does (new
  clean build, retirement of qualifying supply, load growth).
* **R4 — arm-vs-control deltas** in the retirement/entry ledgers and system cost: what arming
  CHANGES. *Expectation:* per E-1's charter the rows' only output is a PRICE, so energy,
  builds and retirements should be identical or near-identical; FFR-7B-2 §3.1 found the Arm-2
  pair identical to the digit in a window where entry was backstop-bound rather than
  margin-decided.
* **R5 — E-1 discipline check:** the rows acquire **no build limb** (FFR-7B-2 §1 step 9 /
  FFR-6B §5.3). Checked structurally in the code AND behaviourally in the R4 ledgers.

### 0.5 Scope guards carried

* `miso_clean_tier_rows` stays **DEFAULT-OFF** in the shipped config; the armed run IS the
  measurement. **No `ScenarioConfig` field added.** No RPS/ACP config value changed.
* The composition seam is **LANDED — consumed, not modified.**
* Everything registers to the **FORECAST namespace** (`register_forecast_run.py`); the
  backcast registry is never touched (rule 15's forecast clause).
* Matrix duty (rule 28(b)): the `miso_clean_tier_rows` cell citation gains this measurement in
  THIS session. **No cell verdict is moved** — the measurement informs an arming decision that
  is not mine to take, so the cell stays `O` for MISO.
* Rule 22: every solve is forecast-mode 2026+, explicitly permitted by the 2026+ clause; no
  measured actual is read or scored.

---

## 1. Headline

* **THE MEASUREMENT FOUND A DEFECT, AND THE DEFECT IS THE RESULT.** Both clean rows are slack
  (dual `0.0`) in every year 2031–2035 — including 2035, MI's first obligated year. That is
  **not** market structure: `model/lp/rows.py` zone-masks each clean row's **wind and solar**
  columns but appends its **generator** columns (nuclear/hydro/biomass/CCS) with **no zone
  filter at all**, so Michigan's East-only row is satisfied by MISO-**South** nuclear. Corrected,
  **MI's 2035 row BINDS** (53.324 TWh of in-mask supply against a 95.771 TWh obligation).
  §3 is the evidence.
* **This is exactly the defect Arm 2 exists to eliminate — "Iowa's surplus paying Michigan's
  bill" — reappearing in the clean family through the generator seam**, and it defeats the
  cited statutory basis of the row (MCL 460.1029 restricts Michigan credits to in-state systems).
* **Blast radius is Arm-3 ONLY. The owner-armed Arm-2 MISO forecast default (D-26) is NOT
  affected** — the RPS call passes no `region_gen_idx`, so its rows are wind/solar only and
  correctly masked (§3.3). Nothing about the standing forecast posture is in question.
* **My pre-registered R1 expectation MISSED and is reported as a miss:** I predicted MI would
  bind at 2035. It did not. The prediction was right about the *statute* and wrong about the
  *code* — which is what the pre-registration was for.
* **The §45U composition seam — the thing D-28 option A steps 1–2 landed — is INERT for Arm 3
  across the whole ramp window, under every mask reading** (§2). §45U terminates after 2032
  (26 U.S.C. §45U(e)); MI cannot bind before 2035; so MI's dual can never coexist with a live
  credit. **The arming question is composition-independent** — a stronger and more robust
  result than the memo's "all compositions coincide at the $30 ceiling."
* **The MN eligibility-mask question the owner left open is DECISIVE for MN** (§4): under the
  shipped 5-zone Midwest mask MN is covered in every ramp year; under the in-state (West-only)
  reading it is short **27.1–42.4 TWh in all five years** and would pin at its $30 ACP.

**Bottom line for the card: Arm 3 must not be armed in its current form.** Its MI row — the one
FFR-6B §2.2 sized as materially binding — is inert for a wiring reason, not a market reason, so
arming it today would ship a mechanism that prices nothing where the statute says it should
price, and the measured "quiet" is not evidence about Michigan's clean market.

## 2. R1 — the duals, and R2 — the composition seam

### 2.1 R1: both clean rows slack in every ramp year

Read from each year parquet's `market_sim` schema metadata (`clean_region_duals` /
`rps_region_duals`) — the authoritative record. All five solves `Optimal`.

| year | MN oblig. | MI oblig. | **MN clean dual** | **MI clean dual** | RPS duals (MN,MI,WI,IL,MO) |
|---|---|---|---|---|---|
| 2031 | .6314 | .0000 | **0.00** | **0.00** | 0, **30**, 0, **30**, 0 |
| 2032 | .6468 | .0000 | **0.00** | **0.00** | 0, **30**, 0, **30**, 0 |
| 2033 | .6622 | .0000 | **0.00** | **0.00** | 0, **30**, 0, **30**, 0 |
| 2034 | .6776 | .0000 | **0.00** | **0.00** | 0, **30**, 0, **30**, 0 |
| 2035 | .6930 | **.4560** | **0.00** | **0.00** | 0, **30**, 0, **30**, 0 |

* **Onset: NONE.** Neither row has a first-nonzero year in 2031–2035. The $30 ACP ceiling is
  never reached because neither row is ever binding.
* MI's obligation being *exactly* zero in 2031–2034 is the arithmetic certainty pre-registered
  in §0.4 (zero-before-first-knot ⇒ RHS 0), and it held. **2035 is the year that carried the
  question, and it answered SLACK.**
* **The two families co-exist correctly**: the Arm-2 RPS duals are bit-stable at
  `[0, 30, 0, 30, 0]` in every year — MI and IL pinned at ACP, the delivery-based MN/WI/MO rows
  slack — extending FFR-7B-2 §3.1's 2026–2030 pattern into the ramp years unchanged.

### 2.2 R2: the §45U seam is inert here, for a reason nobody had noticed

`ira_45u_last_year = 2032` (`config/scenarios.py`, cited **26 U.S.C. §45U(e)**: the credit
terminates for electricity produced after 31 Dec 2032). Measured on the **landed F-1/F-3/F-2
code at HEAD**, not on the memo's curve:

| year | max &#124;branch(i) − branch(iii)&#124; over P∈[20,80], D∈[0,30] |
|---|---|
| 2031 | 7.80 $/MWh (61.46 $/kW-yr) — at P=20, D=15 (interior) |
| 2032 | 7.80 $/MWh |
| **2033** | **0.0000 — exactly zero at every (P, D): §45U expired** |
| **2034** | **0.0000** |
| **2035** | **0.0000** |

Composing this with R1's statutory timing gives the result:

* **MI's row cannot bind before 2035**, and §45U is dead from 2033. **MI's dual and a live
  §45U can never coexist — in any year, under any mask reading.**
* The only overlap window is **2031–2032**, which needs *MN* to bind. Under the shipped mask MN
  is covered (§4). Under the in-state reading MN binds — **but pinned at its $30 ACP ceiling,
  where all defensible compositions coincide to the cent** (the delta above is reached only at
  an *interior* dual).
* ⇒ **The composition choice is worth $0.00 to the Arm-3 arming decision across the entire ramp
  window.** F-2's seam is correct and consumed unmodified; it simply has no purchase here.

**R2 fleet (D-28 §2.1), verified against the shipped masks rather than transcribed** — MN's
mask is the 5-zone `MISO_RPS_MIDWEST_FOOTPRINT_ZONES` (`[True,True,True,True,True,False]`),
MI's is East-only (`[False,False,False,False,True,False]`). **The cross-state flag the charter
asked for is confirmed: a WI (Point Beach), IL (Clinton) or MO (Callaway) reactor earns
MINNESOTA's dual**, and MI's row nominally reaches only Fermi 2. *Nominally* is doing real work
in that sentence — see §3, which is the finding that supersedes it.

## 3. R3 — qualifying supply vs target, and the defect it exposed

### 3.1 The defect

`model/lp/rows.py::_build_rps_region_rows`, one loop, two treatments:

```python
zones_r    = np.flatnonzero(mask[r])                          # eligible zones for region r
wind_cols  = (hours * vph + layout._w_off + zones_r).ravel()  # ZONE-MASKED  ✓
solar_cols = (hours * vph + layout._s_off + zones_r).ravel()  # ZONE-MASKED  ✓
gidx = region_gen_idx[r]
groups_r.append((hours * vph + layout._p_off + gidx).ravel()) # NO ZONE FILTER  ✗
```

and the producer of `gidx`, `_resolve_clean_region_gen_idx(fleet, region_fuels)`, **is never
given the mask** — it filters by fuel alone over the whole fleet
(`np.flatnonzero(np.isin(fuel_idx, codes))`). So every clean row's nuclear / hydro / biomass /
hydrogen / `gas_cc_ccs` credit is **ISO-wide**, while its VRE credit is in-mask.

### 3.2 What it is worth (armed leg, per year, TWh)

| year | row | RHS | **as built** | **as intended** | leaked | verdict built/intended |
|---|---|---:|---:|---:|---:|---|
| 2031 | MN | 73.336 | 214.163 | 165.156 | 49.008 | SLACK / SLACK |
| 2031 | MI | 0.000 | 129.438 | 42.734 | 86.704 | SLACK / SLACK |
| 2032 | MN | 76.629 | 210.284 | 161.227 | 49.056 | SLACK / SLACK |
| 2032 | MI | 0.000 | 138.551 | 52.970 | 85.581 | SLACK / SLACK |
| 2033 | MN | 80.025 | 210.326 | 161.270 | 49.056 | SLACK / SLACK |
| 2033 | MI | 0.000 | 140.411 | 54.309 | 86.102 | SLACK / SLACK |
| 2034 | MN | 83.527 | 210.264 | 161.207 | 49.056 | SLACK / SLACK |
| 2034 | MI | 0.000 | 138.943 | 53.349 | 85.593 | SLACK / SLACK |
| **2035** | **MI** | **95.771** | **139.112** | **53.324** | **85.788** | **SLACK / BINDS ⟵ FLIPS** |
| 2035 | MN | 87.136 | 222.567 | 173.510 | 49.056 | SLACK / SLACK |

The flip lands on exactly the row-year the whole charter was aimed at. MN leaks ~49 TWh/yr too,
but its 5-zone mask is broad enough that its verdict is unchanged.

### 3.3 Scope — Arm 2 is NOT affected

The Arm-2 call site passes **no** `region_gen_idx`:

```python
region_block, region_rhs = _build_rps_region_rows(
    layout, rps_region_zone_mask, rps_region_obligation_frac, demand,
)   # -> region_gen_idx defaults to None: wind/solar only, correctly masked
```

Only the clean-family call passes it. **The landed, owner-armed Arm-2 MISO forecast default
(D-26) is untouched by this finding**, and R1's stable `[0,30,0,30,0]` RPS duals are consistent
with that.

### 3.4 Why this reads as a defect rather than a design choice — evidence, not assertion

I am not adjudicating intent; the owner is. The record points one way:

1. **The cited statute is a locational restriction.** `MISO_CLEAN_TIER_REGIONS["MI"]` carries
   `eligible_zones=("MISO-East",)` with the comment "East ONLY — MCL 460.1029", the Michigan
   provision restricting credits to in-state systems. Under the as-built row that mask governs
   only VRE, i.e. **~28 % of the row's own qualifying energy** at 2035 (39.8 of 139.1 TWh).
2. **FFR-6B §6.2 sized the row by measuring IN-ZONE clean supply** and predicted MISO-East short
   21.7 pp by 2035 — the sizing that justified building the row at all. As built, the row cannot
   reproduce that sizing by construction.
3. **FFR-7B-2 §3.2 explains the 2026–2030 quiet window as MN being covered by "Midwest-wide
   clean generation (VRE + nuclear + hydro + biomass)" under its footprint mask** — i.e. the
   implementing session believed nuclear/hydro/biomass *were* mask-governed. They are not. **That
   handoff's stated mechanism for the established quiet window is therefore itself incorrect**,
   and the 2026–2030 result should be re-read in this light.
4. Arm 2 exists *because* unrestricted intra-ISO attribute trade is false in MISO. Reintroducing
   it for the clean family, silently, contradicts the programme's own premise.

## 5. R5 — E-1 discipline: no build limb (PASSES)

`policy/clean_tiers.py` exposes exactly four public entry points —
`_clean_tier_target`, `build_clean_region_arrays`, `clean_credit_by_fuel`,
`clean_credit_for_zone`: a target, an LP row builder, and two price resolvers. **There is no
build or procurement entry point.** Its only consumers are `retirements.py` and `new_entry.py`,
both taking the dual as a **revenue** term on the same seam the RPS dual already uses — never a
forced build (FFR-7B-2 §1 step 9 / FFR-6B §5.3). Behavioural confirmation is §6's ledger
comparison. **E-1's charter — the mechanism's only output is a price — holds.**

## 7. Scope guards discharged

* `miso_clean_tier_rows` remains **DEFAULT-OFF**; the armed run IS the measurement. **No
  `ScenarioConfig` field added**, no RPS/ACP config value changed, no cache-key surface moved.
* **The F-2 composition seam was consumed, not modified** — §2.2 measures it at HEAD.
* **No arming decision, no keeper contact, no backcast-registry touch.** Everything registers to
  the forecast namespace.
* **The defect found in §3 was NOT fixed in this session.** It is an LP-structural change
  needing its own charter, tests, cache-key adjudication and a re-run of this measurement; and
  fixing it mid-measurement would have destroyed the measurement. Reported, quantified, and
  handed up.
* Rule 22: every solve forecast-mode 2026+; no measured actual read or scored.


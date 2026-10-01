# DESIGN — capx D97: re-pointing T1.6 onto a driver that moves NEISO's VRE supply

**Lane:** capx **D97** (relaunch; the first launch never started). **Date:** 2026-09-25.
**Model:** Fable. **Data profile:** `code`. **LP solves: ZERO.** **Branch:**
`claude/capx-d97-t16-design`, off `origin/main` `8d80839b`.
**Authority:** OWNER RULING **Q70** (2026-09-25, capx ledger §0bk / §3): *"Design lane first."*
**Charter:** `docs/handoffs/capx-director-prompt-pack-2026-08.md` "D97".
**Precedents read:** Q27 (the ruling class for re-pointing a ladder; ledger §3), capx T16 / T16-A
(the previous T1.6 adjudication and execution), D35 (the worked FC-6 re-scope), D94 §1.1 (the
measurement this lane designs against), FFR-4A / FFR-5B / FFR-5C / FFR-5E (the entry-stack seams).

**Boundaries honoured:** no solve, no edit under `src/` or `scripts/`, no scorer change, no
`ff-verdicts.json` edit, no plan-§2 edit, no matrix cell moved (nothing was tested — rule 28(b) does
not fire; rule 28(a) was discharged, §6). D96 is concurrently re-solving `neiso-t3` and is the sole
`ff-verdicts.json` writer; this lane writes one file.

---

## 0. Headline

**Recommend re-pointing T1.6 to `entry_pipeline_aware_signal`** — `vre_short` = `False` (the shipped
default and the `neiso-t3` golden's own posture), `vre_long` = `True` — solved on the golden recipe with
both pins, two rungs, ~35 min of LP each, after D96 lands.

Why this lever and not the others, in one paragraph. NEISO's VRE volume in every committed leg is set
by **one arithmetic fact**: the per-tech queue caps (wind 1.0 + solar 2.0 GW/yr) are netted against the
pending two-year commissioning stock, so the long-run decision rate is capped at **C/L = 1.5 GW/yr**,
not the 3.0 GW/yr the caps' own citations define (`new_entry.py`, the `_pending_netting_mw` term;
FFR-4A §3.3/§5). `entry_rate_limits` sits *behind* that binder, which is why T16-A and D94 both found
33.0 GW in both rungs. `entry_pipeline_aware_signal` is the **owner-signed (D-17(a)), cited, gated
field that removes exactly that netting** and relocates the anti-cobweb guard to the price signal
(FFR-5C). Armed, NEISO's net VRE flow doubles by construction, and the zero-LP arithmetic in §2 says
the physical Class I supply then crosses the obligation around **2039** — the first committed NEISO
posture in which the REC dual could leave the $50 ACP at all. Every other candidate either cannot
reach the binder (VRE capex, the ACP, the RPS target), is inert in NEISO for a reason the code makes
explicit (offshore wind, three routes), or would have to be a new uncited knob (the queue-cap constant).

**Two things the owner should know before the card.** (i) The RPS row's dual is **near-binary in this
LP** (§1.3): it reads the ACP while the region is physically short and ≈ 0 once it is not, so "the dual
falls toward 0 as VRE builds through the target" is a **step**, not a slope — and after the step the
entry screen loses its $50 credit, so the arithmetic predicts a **cobweb** around the target in the long
rung's back half. The pre-registered `rps_dual_over_acp` is a **final-year** scalar, which makes T1.6b's
verdict in the long rung a parity question. The card therefore carries a sub-choice: keep the metric as
pre-registered (and accept that outcome map §4.3 has a coin-flip leg), or amend T1.6b to a horizon
series, which is a plan-§2 change only the owner can make. (ii) The lever is **broader than VRE**, the
same class of declared confound T16-A carried for `entry_rate_limits`: it un-nets the thermal caps too
and lets the pro-forma see the pipeline. The rungs' own `entry_thermal_gw` / `co2_mt_total` are reported
beside the dual so the co-movement is measured, not argued.

**Fallback, named as the charter requires:** retire T1.6 for NEISO. Q70 rejected it; it stays on the
card as the named fallback.

---

## 1. What is established (re-verified here from committed artifacts, zero LP)

### 1.1 The REC dual is at the ACP in every committed NEISO forecast leg

Twelve committed `full_horizon_summary.json` trajectories were read: the six golden bundles under
`results/ff-t3-neiso-golden/{bau, bau-d46, bau-d60, bau-d65br, bau-prera-2026-08-31, d90-rescore}`,
the four D92 paired arms (`d92/{base, carbon_plus25, gaspm5, gasup150}`) and the two D94 rungs
(`d94/{vre_short, vre_long}`). **`rps_dual` = 50.0 in all 25 years of all twelve** (300 leg-years),
and every one ends 2050 at **37,100 MW of VRE** (12.4 GW wind / 24.7 GW solar). T16-A's two legacy-bin
rungs make it 350 leg-years. This is not a T1.6 artifact; it is the standing state of the NEISO
forecast.

### 1.2 The gap, year by year (D94 `vre_short`, the golden posture at `924017c8`)

Obligation = `STATE_RPS_FLOORS["NEISO"]` interpolated (0.29 → 0.40 → 0.48 → 0.50, edge-held after
2045) × total generation; eligible = dispatched wind + solar (the row's eligible set for NEISO is
`("wind", "solar", "offshore_wind")` and the fleet carries no `offshore_wind` class, so the third
term is 0). TWh.

| year | load | target | obligation | wind | solar | eligible | **gap** | VRE GW (w / s) | dual |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| 2026 | 115.8 | 0.290 | 33.6 | 3.7 | 3.3 | 6.9 | **26.7** | 1.4 / 2.7 | 50.0 |
| 2030 | 119.4 | 0.400 | 47.7 | 6.3 | 5.8 | 12.1 | **35.7** | 2.4 / 4.7 | 50.0 |
| 2035 | 127.0 | 0.440 | 55.9 | 13.4 | 12.2 | 25.6 | **30.3** | 5.1 / 9.8 | 50.0 |
| 2040 | 136.2 | 0.480 | 65.4 | 19.4 | 18.4 | 37.7 | **27.7** | 7.4 / 14.7 | 50.0 |
| 2045 | 147.5 | 0.500 | 73.8 | 26.5 | 24.8 | 51.2 | **22.5** | 10.1 / 19.8 | 50.0 |
| 2050 | 161.1 | 0.500 | 80.5 | 32.5 | 30.9 | 63.4 | **17.2** | 12.4 / 24.7 | 50.0 |

The gap **widens** to 2030 (the target ramps 0.29 → 0.40 while the first VRE tranche only commissions
in 2029), then closes at ~0.75 TWh/yr for twenty years and is still 17 TWh short at 2050. At the LP's
own NEISO capacity factors (`RENEWABLE_CF["NEISO"]`: wind 0.30, solar 0.15 → 2.63 / 1.31 TWh per GW
delivered) the 2050 shortfall is **≈ 9 GW** of additional VRE at the 2:1 solar:wind build mix — i.e.
roughly six more years of the current flow. The target is **reachable**; the flow is too slow. That is
a different statement from T16-A §5.4's "unreachable at any plausible VRE build", and it is the
statement the numbers support.

### 1.3 Why the dual is near-binary, and why that matters for a final-year metric

`model/lp/rows.py::_build_rps_row`: one annual row, `Σ_t (W + S + eligible P) + Σ_t ACP ≥ target ×
Σ_t demand`, with the ACP column priced at $50 in the objective. Wind and solar are decision variables
at MC = 0 (rule 3), so the LP dispatches every available VRE MWh before it buys a single ACP MWh. Two
regimes follow:

* **Short** (every VRE MWh dispatched, still below the target): the marginal certificate is an ACP
  purchase → dual = **50.0 exactly**. This is every committed leg-year.
* **Met** (the row is slack, or binds only through un-curtailing VRE that would otherwise be dumped):
  dual = **0**, or the dump/ε cost of absorbing one more VRE MWh — a few $/MWh at most, never a
  gradual descent from 50.

So T1.6's pre-registered *"→ 0 as VRE builds through the target"* is realised in this LP as a **step in
the year the physical supply crosses the obligation**. The battery's `rps_dual_over_acp` is
`rps_final / acp` — the **last solved year's** dual (`run_driver_battery._extract_metrics`). A rung that
crosses the target in 2039 and is then knocked back by the cobweb in §2.3 can end 2050 on either side
of the step. That is the instrument fragility the card's sub-choice addresses; it is not a defect in
the model.

### 1.4 What actually sets NEISO's VRE volume — the seam trace

`model/capacity_evolution/new_entry.py`, the economic-entry screen, in the order the caps are consulted:

1. **Margin screen.** Wind and solar are valued at their zone's hourly CF against zonal prices plus the
   attribute credit `max(eac, rps_shadow, clean)` at the **prior year's** REC dual, less
   `lcoe × 8760 × base_cf`. At $50/MWh REC the credit is worth **$66k/MW-yr to solar and $131k/MW-yr to
   wind** (NEISO CFs), against annualised fixed costs of ≈ $132k (solar) / $151k (wind) at the 2026 ATB
   Moderate capex and the run's 5.675 % real rate (CRF₃₀ = 0.0701), falling with Wright learning to
   ≈ $110k / $141k by 2030. Both are profitable with the REC; **wind alone is marginal without it, and
   solar is not** (it needs ≈ $34/MWh of energy capture with the REC and ≈ $84 without). VRE is
   therefore **cap-bound, not margin-bound**, in every committed leg — the ledgers decide exactly the
   cap every decision year.
2. **ISO total budget** `QUEUE_CAP_GW["NEISO"]` = 4 GW/yr (shared with thermal). Not the binder: VRE
   flow is 3 GW/yr at most.
3. **Per-tech caps** `QUEUE_CAP_PER_TECH_GW["NEISO"]` = wind 1.0 / solar 2.0 / offshore_wind 2.0 /
   gas_cc 1.0 / gas_ct 0.5 GW/yr — a **labelled engineering-judgment estimate**
   (`capacity_market.py`, the Eastern-ISO block comment), not a measured throughput.
4. **The pending-stock netting** (`_pending_netting_mw`): with `entry_commissioning_lag=True` (the
   golden's posture; COD lag L = 2), the MW decided last year and not yet commissioned are subtracted
   from this year's per-tech cap and ladder budget. FFR-4A §3.3 measured the consequence: the long-run
   decision rate is **C/L**, and the growth ladder's ratchet factor is **K − L + 1 = 1** at the shipped
   (2, 2). The D94 ledgers show it directly: `vre_long` decides 2,000 solar + 1,000 wind in 2029, 2031,
   … 2049 and **nothing** in the even years (the stock consumes the whole budget), 33,000 MW in total.
5. **The growth ladder** (`entry_rate_limits`, 2 × prior max, NEISO seeds 0.358 GW wind / 0.257 GW
   solar — FFR-4A's table names the ladder as NEISO's first binder for both techs). It **re-phases**
   the same 33,000 MW into 22 consecutive years (T16-A §5.3). Removing it (`vre_long`) does not change
   the total because the netting in (4) still caps the average at 1.5 GW/yr.
6. **The procurement netting** (`_procured_netting_mw`, FFR-5E) — inert: the channel is gated off,
   and NEISO's construction-committed onshore/solar pipeline is **5 rows, 31.6 MW** (FFR-5E §1 table).

**The binder is (4).** Everything T1.6 has tried sits at (5), behind it.

---

## 2. The candidates, each on the charter's four questions

For each: (1) does it reach NEISO VRE entry; (2) direction and rough size of the VRE response;
(3) can the REC dual leave the ACP in the rung; (4) is it a real forward driver independent of the
outcome (rules 1 / 13) — or a knob chosen because it makes T1.6 pass.

### 2.1 The RPS target level (`STATE_RPS_FLOORS["NEISO"]`) — REFUSED as the T1.6 lever

(1) It reaches the **obligation**, not VRE entry: the row's RHS moves, the screen's cap arithmetic does
not. VRE stays cap-bound at 33.0 GW whatever the target. (2) Zero VRE response. (3) Trivially yes — at
2050 the eligible share is 39.4 % of load, so any 2050 target ≤ 0.39 reads the dual off the ACP without
one MW moving. (4) That is exactly the failure mode: it moves the **target to the fleet** rather than
the fleet to the target, and T1.6's pre-registration is *"VRE fleet held short vs long"*. The
trajectory is a cited statute blend (six state schedules, each verified 2026-08-06) and is not
config-overridable; a ladder over it needs a new `ScenarioConfig` field. A **policy-stringency ladder**
is a legitimate scenario object in its own right, but it is not T1.6 and it would have to be
registered as its own row. Named in §5, not recommended here.

### 2.2 The ACP level (`STATE_RPS_ACP["NEISO"]` = $50) — REFUSED

(1) Reaches the screen through the REC credit, but VRE is cap-bound, so raising it changes no volume;
lowering it far enough turns solar's margin negative and *reduces* VRE. (2) Zero or negative. (3) No —
and the metric is `dual / ACP`, so a dual that tracks a moved ceiling still reads **1.0**. The lever is
confounded with the metric's own denominator, the same class of defect Q27 refused for
`eac_price_wind`. (4) A statutory parameter (MA Class I ACP schedule), not a driver. Constant, no field.

### 2.3 VRE capex / ATB cost vintage (`tech_cost_path`) — reaches the seam, cannot re-size upward; REFUSED

(1) Yes: `resolve_new_entry_costs` scales capex and learning rate into `compute_lcoe`, which sets the
screen's annual cost. (2) **Downward only.** The rung that matters would be *more* VRE, and no capex
path can build past the 1.5 GW/yr netted cap; `low` leaves the fleet cap-bound at the same 33.0 GW,
`high` (wind ×1.402, solar ×1.051) pushes solar's margin toward zero and can only shrink the build.
(3) No rung produces a fleet that crosses the obligation, so the dual stays at 50 in every rung — a
constant series again. (4) It is a real driver (the published-cost literature envelope), but it is
already **T1.8's** ladder, and using it here would test cost sensitivity under the name of VRE supply.
The arithmetic that closes it: the 2050 shortfall is ≈ 9 GW of *volume*; a cost lever moves *margins*,
and margins are not what binds.

### 2.4 The offshore-wind pipeline — three routes, each inert in NEISO for a reason the code states

Offshore wind is New England's dominant Class I compliance build in reality, so this candidate was
traced hardest. Three routes exist and none moves NEISO VRE today:

* **(a) `offshore_wind_available_year`** — Q27 adjudicated it inert (`offshore_wind_eligible_isos`
  defaults to `["CAISO"]`; the golden carries that default). Stands.
* **(b) Making OSW a merchant candidate** (rung override `offshore_wind_eligible_isos = ["CAISO",
  "NEISO"]`; the field exists, no code change). It reaches the screen from 2030 with its own 2.0 GW/yr
  cap. But `_emerging_lcoe` costs fixed-bottom OSW at $6,312/kW, 0.45 CF, **with no Wright learning
  applied** (the offshore branch never calls `wright_cost`), i.e. **$135/MWh flat for 25 years** —
  ≈ $532k/MW-yr against ≈ $237k/MW-yr of energy revenue at $60/MWh. And the screen credits the REC
  only `if tech in _RENEWABLE_NEW_FUELS` = `{wind, solar}`, so an OSW candidate earns **no REC revenue
  in the screen even though the RPS row counts its generation**. It never clears. (2) zero; (3) no;
  (4) the eligible-ISO list is a real forward fact (BOEM lease areas exist for MA/RI), but the route is
  dead on economics the code does not let the REC reach — a **code inconsistency**, named in §5 as a
  successor, not fixed here.
* **(c) The procurement channel** (`vre_procurement_additions_enabled`, FFR-5E, D-18(a)) — the
  right *mechanism* for state-contracted OSW: EIA-860 construction-committed proposed rows commission
  at their effective year, bypass the caps, and net the screen's budgets. But its technology map is
  `Solar Photovoltaic` + `Onshore Wind Turbine` only — FFR-5E §7 records that "offshore wind … [is] out
  of scope — 5,889 MW nationally in the proposed sheet, materially NEISO/NYISO", deliberately. NEISO's
  in-scope pipeline is **31.6 MW**. Extending the map is a `src/` change and a separate owner decision
  (FFR-5E's own words), so it is outside this lane. Even armed with OSW, the contracted New England
  pipeline (≈ 3.6 GW across Vineyard Wind 1, Revolution Wind, SouthCoast Wind, New England Wind — this
  lane did not read the proposed sheet, data profile `code`; the figure is the public procurement
  record and must be re-measured by whoever arms it) delivers ≈ 14 TWh/yr at 0.45 CF against a gap of
  27–36 TWh through 2040. **A real forward driver that cannot discriminate T1.6 on its own** in the
  window where the dual is pinned. Named in §5 as the additions-side successor; recommended as an
  arming question for NEISO in its own right, never as a T1.6 rung.

### 2.5 NEISO's entry caps — two very different objects

* **(a) `QUEUE_CAP_PER_TECH_GW["NEISO"]` itself** — REFUSED as a ladder. (1) Reaches the binder
  directly. (2) Linear in the cap. (3) Yes at a high enough cap. (4) **This is where the fitted-mechanism
  risk lives.** The constant is a labelled estimate with no per-tech measurement behind it, it has no
  `ScenarioConfig` field (a ladder needs a new one, rule 28(c)), and any rung value other than the
  shipped one would be a magic number (rule 5) chosen for its effect on the gate — the selection rule 1
  forbids. The honest route to a different NEISO cap is a **rule-23 re-derivation from ISO-NE's own
  throughput record** (the `queue-cap-citation-2026-07.md` follow-up), which is a data lane, not a
  ladder.
* **(b) `entry_pipeline_aware_signal`** — **RECOMMENDED.** (1) Reaches the binder exactly: armed, the
  pending stock leaves both flow caps and each binds as the GW/yr rate its citation defines
  (`new_entry.py`, `_pending_netting_mw = {} if armed`); the ISO budget and margin screen are unchanged.
  (2) **Up, by construction, ≈ 2×**: the net VRE decision rate goes 1.5 → 3.0 GW/yr from COD 2029 (the
  growth ladder still ratchets wind 0.716 → 1.0 and solar 0.514 → 1.03 → 2.0 over the first two build
  years, so the first two tranches are below cap). Pre-declared band for `renewable_build_gw`:
  **[55, 66] GW** if the fleet stays cap-bound; lower if the §2.3 cobweb throttles the back half.
  (3) **Yes.** Zero-LP: eligible(y) = 6.9 + 5.26 TWh × (build years since 2029) crosses the
  obligation in **2039** (63.4 vs 64.7 TWh) on nameplate CFs; curtailment at 40+ GW of VRE on a
  25–33 GW peak system pushes it later, so the pre-declared first-crossing window is **[2038, 2043]**.
  (4) **Legitimate independent of the outcome, and adjudicated before T1.6 needed it:** FFR-4A found the
  netting to be a dimensional double-count (a stock subtracted from an annual flow, E-1) and the
  pro-forma blind to its own pipeline (E-2); the owner chartered both halves as one gated field
  (D-17(a), 2026-08-05); FFR-5C landed it byte-identical-until-armed and reproduced FFR-4A's Arm-B
  ceilings to the MW; neither K nor L moves. Its NEISO matrix cell is `U`/`U` — untested, not
  adjudicated `R`/`I`/`G` — so rule 28(a) does not bar it. The lever is a **correctness repair the
  program already owns**; the ladder borrows it, the same relationship T1.6 already has to
  `entry_rate_limits`. **Declared confound:** the thermal caps un-net too (gas_cc 0.5 → 1.0 GW/yr
  effective) and the look-ahead reprice sees pending thermal and VRE rows, so `entry_thermal_gw`,
  `co2_mt_total`, the CCS wave and `reserve_margin_final` will move (D94 §1.1 measured the same class
  of co-movement for `entry_rate_limits`); the 4 GW/yr ISO budget may also start binding against VRE +
  thermal together. All of it is reported beside the dual.

### 2.6 Also considered, rejected in a line each

* `entry_commissioning_lag = False` — kills the netting by deleting a measured physical lag (LBNL
  *Queued Up* 2024 median IA→COD = 2 yr). Not a driver; refused.
* `eac_price_wind` / `eac_price_solar` — Q27's confound (`max(eac, rps_shadow)` is the channel the
  metric measures). Stands.
* Re-pointing T1.6 to **CAISO** (plan §2 says "NEISO or CAISO") — there is no CAISO T3 golden
  (`ff-verdicts.json` carries `caiso-t1f` / `caiso-t1h` only), so this is a new golden campaign
  (25 years + a battery), not a two-rung re-point. Named as alternative (b1) on the card.
* Retiring T1.6 for NEISO — Q70 rejected it; the named fallback (c).

---

## 3. The recommended ladder, pre-declared

**Rungs** (order short → long, so T1.6b's `monotone_down` runs in the direction the expectation names):

| rung | override | what it is |
|---|---|---|
| `vre_short` | `entry_pipeline_aware_signal = False` | the shipped default = the `neiso-t3` golden posture; the netted C/L flow |
| `vre_long` | `entry_pipeline_aware_signal = True` | the un-netted C flow; the D-17(a) field armed for this rung only |

**Recipe** — the D94 discipline verbatim: each rung is `scripts/run_full_horizon.py --golden-posture`
with both `neiso-t3` pins (`ccs_retrofit_vom_adder=8.0`, `ccs_retrofit_fixed_cost_co2_scaling=False`),
`entry_rate_limits=True` (the golden's own, no longer perturbed), and the rung's override through the
existing generic `--set entry_pipeline_aware_signal=True` (SCN-WS0; validated as a `ScenarioConfig`
field, recorded in `set_overrides`) — **no `src/` or `scripts/` edit is needed to solve either rung**.
Metrics and assembly through `docs/handoffs/d94/battery_golden_rung.py`'s two zero-LP halves (its
`RUNG_OVERRIDE` guard names `entry_rate_limits`; the execution lane updates that helper, which lives
under `docs/`, not `scripts/`). Both rungs at **one pinned SHA**, in shards (rule 32(c)), each pushing
its full bundle (rule 34). `True` is non-default, so the long rung mints its own cache key; the short
rung reproduces the golden's key at that SHA.

**Expectations — UNCHANGED**, as T16-A pinned by test: T1.6a `rps_dual_over_acp ≤ 1.0` (`le_target`),
T1.6b `rps_dual_over_acp` `monotone_down` across rungs. The metric stays the final-year scalar unless
the owner takes the amendment below.

**Pre-declared outcome map** (the honesty clause, Q27 verbatim, binds: a non-moving lever is a real
finding, reported, never a third lever tried):

| # | measured | T1.6a / T1.6b | FC-6 battery row | reading |
|---|---|---|---|---|
| A | `renewable_build_gw` long ≫ short (≥ 50 GW) **and** long final-year dual < 50 | PASS / PASS, non-vacuous | PASS-eligible | the ladder tests its pre-registration for the first time; the step §1.3 predicts was reached and held at 2050 |
| B | VRE ≫ short, dual leaves the ACP mid-horizon, **but the 2050 dual is back at 50** (cobweb parity) | PASS / PASS **vacuous** | CAVEAT | the model behaves exactly as §1.3/§2.3 predict and the **final-year instrument** cannot see it — the within-arm series (all 25 years are in the ledgers) is the evidence; this is the case the amendment exists for |
| C | `renewable_build_gw` long = 33.0 (no re-size) | PASS / PASS vacuous | CAVEAT | **the seam trace in §1.4 is wrong** — something other than the netting binds (the ISO budget against thermal, or margins); report which, from the ledger's `queue_budget_gw` / margin rows; no third lever |
| D | VRE ≫ short and the dual stays 50.0 in all 25 years of the long rung | PASS / PASS vacuous | CAVEAT | **§1.2's arithmetic is wrong** — curtailment or load growth outruns a 3 GW/yr flow; report the measured eligible-vs-obligation series; no third lever |
| E | long dual > short (rises) | PASS / FAIL | FAIL | a directional violation — a root-cause object to open, never a threshold to widen |

**Point predictions, graded at full magnitude by the execution lane:** first year with
`rps_dual < 50` in `vre_long` ∈ [2038, 2043] (near-certain that it is < 2046 if C/D do not occur);
`renewable_build_gw` long ∈ [55, 66] GW; `entry_thermal_gw` moves by ≥ 0.5 GW in either direction
(the confound is live); `co2_mt_total` long < short (more VRE displaces gas; magnitude undeclared
because the CCS wave also moves); wall ∈ [30, 50] min per rung, RSS < 5 GB (D94: 37.4 / 33.5 min,
3.4 GB); P(outcome B | not C, not D) ≈ 0.5 — stated so nobody reads B as a surprise.

**The optional amendment (owner-only; a plan-§2 change).** Score T1.6b on the **horizon mean of
`rps_dual_over_acp` over 2041–2050** (or, equivalently, the count of ACP-pinned years) instead of the
2050 point. It keeps both expectations' rules (`le_target`, `monotone_down`) and the `_RULES` table
untouched; it changes one metric construction in `_extract_metrics` and the registry note, plus the
T16-A pin test. Under it, outcome B becomes a non-vacuous PASS (short 1.0, long ∈ [0.3, 0.7]) and the
ladder measures the **regime**, which is what the pre-registration describes. Without it the ladder
measures parity in one year. This lane recommends the amendment but did not make it (scorer change,
out of scope, and the owner's to rule).

**Cost.** Two rungs × ~35 min LP, concurrently in two shards → ~40 min wall, plus the artifact-only
FC-6 re-score. If the execution lane pins to the SHA D96's `base` leg was solved at, the short rung
**is** D96's `base` and the cost is **one rung**; otherwise two. Sequencing: **after D96 lands** (it is
the sole `ff-verdicts.json` writer and its `base` is the natural same-vintage control). The prior
battery record is preserved beside, never over, as T16-A and D94 did.

**What a vacuous result would mean.** C says the binder is not the netting; D says the target is
further than the row arithmetic shows; B says the instrument, not the model, is the limitation.
None of the three is grounds for another lever. If C or D occurs, T1.6 is out of levers that the
existing registry can express without a new field, and the card's fallback (c) is the honest next
ruling.

---

## 4. Rule-28 duties, and what this lane did not do

* **28(a) discharged.** NEISO's shard read live: `entry_pipeline_aware_signal` `U`/`U`,
  `vre_procurement_additions` `U`/`U`, `entry_dampers` `U`/`U` with T16-A's `ev`; the §5.6 NEISO lever
  queue names none of the candidate levers. No `R`/`I`/`G` cell is re-tested by this recommendation.
* **28(b) does not fire** — nothing was tested. The execution lane stamps the
  `entry_pipeline_aware_signal` NEISO `ev` when it solves; the cell stays `U` for the same reason
  T16-A's did (an instrument perturbation inside a ladder is not an arming adjudication, 28(d)).
* **28(c) does not fire** — no `ScenarioConfig` field is added. Every recommended override is an
  existing registered field with a CLI path.
* **Not done, by charter:** no solve; no edit under `src/` or `scripts/`; no scorer change; no
  `ff-verdicts.json` touch; no plan-§2 edit; no `data/raw` hydration (the OSW pipeline MW in §2.4(c)
  is the public procurement record, flagged as un-measured here).

---

## 5. Named and left — with a live owner, or the statement that none exists

1. **The OSW REC-credit inconsistency in the entry screen** (§2.4(b)): the RPS row counts
   `offshore_wind` generation for NEISO/NYISO/CAISO, but the screen grants the REC credit only to
   `_RENEWABLE_NEW_FUELS = {wind, solar}`, and `_emerging_lcoe`'s offshore branch applies no learning.
   A merchant OSW candidate can therefore never clear in a state whose statute was written for it.
   **No live owner exists.** A one-line `src/` fix with an A/B; rule 28(c) row already exists
   (`offshore_wind_*` fields), so it is a repair lane, not a mechanism lane.
2. **The procurement channel's technology map** (§2.4(c)): extending `_TECHNOLOGY_TO_FUEL` to
   `Offshore Wind Turbine` and arming `vre_procurement_additions_enabled` for NEISO is the real
   additions-side driver of Class I compliance. FFR-5E named it "a separate decision with its own
   evidence"; FFR-5B §4 flagged NEISO's behind-meter share as a structural caveat. **No live owner
   exists.** Own PRECOMMIT, `neiso` profile, one A/B (~35 min).
3. **The NEISO per-tech queue caps** are labelled estimates (§2.5(a)); the rule-23 re-derivation from
   ISO-NE's throughput record is the `queue-cap-citation-2026-07.md` follow-up. **No live owner.**
4. **T1.6's third clause** — *"nuclear does not move the dual"* — has no rung, expectation or scoring
   path (T16 §6, T16-A §2.2). Unchanged by this design. **No live owner.**
5. **A policy-stringency ladder over the RPS trajectory** (§2.1) is a legitimate scenario object that
   is not T1.6. Not proposed; recorded so it is not later mistaken for this recommendation.
6. **The final-year metric's fragility** (§1.3) — carried to the owner on the card below, not deferred.

---

## 6. THE OWNER CARD — T1.6 re-point (for the director to serve as the next Q)

**The question.** T1.6 ("RPS/ACP vs VRE supply, short → long") cannot discriminate in NEISO because its
lever sits behind the constraint that actually caps NEISO's VRE flow at 1.5 GW/yr. Which re-point?

**(a) RECOMMENDED — re-point T1.6 to `entry_pipeline_aware_signal`** (`False` → `True`), two rungs on
the golden recipe with both pins, solved in shards after D96 lands, artifact-only FC-6 re-score, prior
battery preserved beside. Cost ~40 min wall (one rung if pinned to D96's SHA). Pre-registered
outcome map §3 (A–E) binds; the honesty clause binds; no third lever. The lever is the owner-signed,
cited D-17(a) correctness repair the program already owns, adjudicated on its own terms before T1.6
needed it, and it is the only registered field that reaches the binder. **Sub-choice, owner-only:**
* **(a-1)** keep `rps_dual_over_acp` as the pre-registered final-year scalar (no scorer change; accept
  that outcome B — the model steps off the ACP mid-horizon and cobwebs back by 2050 — reads vacuous);
* **(a-2)** amend T1.6b to the 2041–2050 horizon mean (a plan-§2 change + one metric construction +
  the T16-A pin test; the ladder then measures the regime the pre-registration describes).
  This lane recommends **(a-2)**.

**(b) Alternatives**, each priced:
* **(b1)** re-point T1.6 to CAISO — no CAISO T3 golden exists; a new golden campaign (~35 min + a
  battery + registration), not a re-point.
* **(b2)** arm the additions-side driver first: extend the procurement channel to offshore wind and arm
  it for NEISO (§5 item 2) — the real Class I mechanism, but a `src/` change plus its own A/B, and the
  arithmetic says it cannot bring the dual off the ACP alone before 2040.
* **(b3)** a new RPS-stringency ladder as its own Tier-1 row — legitimate policy object, not T1.6.

**(c) FALLBACK — retire T1.6 for NEISO.** Q70 rejected this; it is named because the charter requires
it, and because if the recommended ladder returns outcome C or D the existing registry has no further
lever to offer without a new field.

**What (a) does not do, stated at the gate:** it does not clear FC-6 (the paired P2 leg and D96's
re-score decide that); it does not arm `entry_pipeline_aware_signal` anywhere (rule 25 — the long rung
is a ladder perturbation; an arming decision is its own card, and this ladder would be its NEISO
evidence); it does not touch the standing RPS/ACP finding except to sharpen it from "unreachable" to
"reachable at ≈ 2× the current flow".

---

## 7. Reproduction (zero LP; every number above is from committed files)

```
# obligation vs eligible, per year, both D94 rungs
python3 - <<'EOF'
import json
F={2026:.29,2030:.40,2040:.48,2045:.50}
def tgt(y):
    ks=sorted(F)
    if y<=ks[0]: return F[ks[0]]
    if y>=ks[-1]: return F[ks[-1]]
    for a,b in zip(ks,ks[1:]):
        if a<=y<=b: return F[a]+(y-a)/(b-a)*(F[b]-F[a])
for leg in ('vre_short','vre_long'):
    for t in json.load(open(f'results/ff-t3-neiso-golden/d94/{leg}/full_horizon_summary.json'))['trajectory']:
        g=t['generation_by_fuel_mwh']; dem=t['total_gen_mwh']/1e6
        print(leg,t['year'],round(tgt(t['year'])*dem,2),round((g['wind']+g['solar'])/1e6,2),t['rps_dual'])
EOF
# the dual in every committed NEISO leg
for f in results/ff-t3-neiso-golden/*/full_horizon_summary.json results/ff-t3-neiso-golden/d9?/*/full_horizon_summary.json; do
  python3 -c "import json,sys;t=json.load(open('$f'))['trajectory'];print('$f',sorted(set(x['rps_dual'] for x in t)),t[-1]['vre_mw'])"; done
# the binder: cap netting and the alternate-year decisions
grep -n "_pending_netting_mw" src/market_sim/model/capacity_evolution/new_entry.py
python3 -c "import json,glob;[print(f[-9:-5],json.load(open(f)).get('entry_decided_mw_by_tech')) for f in sorted(glob.glob('results/ff-t3-neiso-golden/d94/vre_long/NEISO/*/evolution_20*.json'))]"
# LCOE / breakeven arithmetic: real rate (1.08/1.022)-1 = 0.05675, CRF30 = 0.07014, NEW_ENTRY_COSTS + OFFSHORE_WIND_PARAMS + RENEWABLE_CF["NEISO"]
```

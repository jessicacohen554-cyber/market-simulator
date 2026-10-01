# PRECOMMIT — pjm-h13: PJM's ST_GAS net-load drag is an ALLOCATION defect. Test `netload_drag_merit_allocation` (2026-09-20)

**Session:** pjm-h13 · **Branch:** `claude/pjm-h13-mustrun-exclusions-0yud3j` · **ZERO LP IN THE PARENT**
(rule 32 `[R-SHARD]` (a)). Six shards, **one year each** (rule 36 `[R-YEAR-ISOLATION]` (a)).
**Keeper under test:** `2026-09-19-pjm-h11-c1seam-span` (2023–2025, CALIBRATED, eight criteria PASS,
zero caveats) + folded touchpoint `2026-09-19-pjm-h11-c1seam-touchpoint` (2020–2022).

**EVERY GATE BELOW IS FIXED BEFORE ANY SOLVE AND IS NEVER RE-READ ONCE A NUMBER LANDS.**

---

## 0. What changed from the chartered queue, and why (rule 28(a))

The handoff recommended **LEVER A — `mustrun_plant_exclusions`**, blocked on a missing PJM lay-up
census. **That census is now built** (§1) and the lever is **measured, at zero LP, to be
sub-marginal**: it repairs 11 of PJM's 45 D-4 failure rows but only **0.0256 of 4.118 TWh** of
failing floor energy — 0.6 %. It is *correct* and it is *tiny*. §1 records it in full; it is not
this lane's card and **no cell is adjudicated R on it**.

Measuring it localised where PJM's rule-17 mass actually lives, and **78 % of it is in one
mechanism this lane can reach**: `st_netload_drag`. That is the card. It was already named — pjm-177
measured the same defect from the hour axis and wrote it down without taking it: *"the measured
trough block has a persistent HETEROGENEOUS membership … while the drag commits EVERY plant at ~83 %
duty in all hours and ~0 % in the trough — **a real second defect that is ercot-259's object,
recorded not taken**."* This lane takes it. Going off-queue is declared here, with the measurement
that justifies it, before any solve.

---

## 1. The queued lever, adjudicated at ZERO LP — and the artifact it leaves behind

`scripts/data/derive_campd_bridge_layup_exclusions.py --iso PJM --detail` (the **frozen** nyiso-140
criterion, unmodified: median gross load **exactly 0** in every one of 18 (year, 4-h block) cells).
Committed as `data/raw/_processed-legacy/campd_bridge_layup_exclusions_PJM{,_population}.csv`.

**The separation is textbook and is the artifact's own evidence, not an assertion:** 82 plants in the
bridge population, 80 with CAMPD coverage, **10 qualify at 18/18 zero cells and the nearest
non-qualifier sits at 14/18** (then 12, 12, 11, 8, 8, 6, 3, 1, and 61 at zero).

**The population answer pjm-h12 owed and could not give** (its census counted plant-*hours*, never
*which plants* — correction #2 of the handoff). Against the D-4 `cc_mustrun_per_plant` failure set:

| plant | name | cells zero | P(on) | in D-4 fail set | arm repairs it? |
|---|---|---:|---:|---|---|
| 2393 | Gilbert | 18/18 | 0.042 | yes | **YES** |
| 10751 | Camden | 18/18 | 0.109 | yes | **YES** |
| 7153 | Hay Road | 8/18 | 0.496 | yes | no — a **cycler** |
| 10308 | Sayreville | 12/18 | 0.389 | yes | no — a **cycler** |
| 59220 | Wildcat Point | 3/18 | 0.589 | yes | no — **runs**, median 482 MW |

The census **independently declines** the three it should decline: they are not mothballed, so their
forcing is an offer/window defect and excluding them would bury that error inside a membership list
(the nyiso-140 plant-7314 reasoning, verbatim, rules 1/14).

**Measured footprint if armed** — the arm touches 4 floored plants (2393, 10751, 50561, 55188; 3096
qualifies but carries a `ct_only` benchmark flag and no binding floor), removes **0.027 TWh of floor
across six years**, and repairs **11 of 45** D-4 failure rows worth **0.0256 of 4.118 TWh (0.6 %)**.
The 5 ST_GAS qualifiers are untouched: **PJM arms no `st_gas_mustrun_per_plant` floor at all.**

**Verdict: correct, sub-marginal, NOT this lane's card.** Cell stays `U`, re-stamped with this
measurement so no successor re-derives it. Arming it later is a one-flag change on any run.

---

## 2. The card — and the defect, stated as a fact about named plants

PJM's ST_GAS drag mandate is spread **pro-rata across every non-peak tranche's own pmax**, which
asserts every plant is committed at one fleet capacity factor in every hour. Measured on the
keeper's **own committed** `legitimacy_diagnostics.json`, over an 8.95 GW ST_GAS population:

- The drag floors **exactly four plants**. The per-plant rows sum to the mechanism total (2024:
  0.1279 + 0.1867 + 0.1097 + 0.3930 = 0.8173 against the window row's 0.8352).
- **3131 Shawville** (596 MW, online 0.594) and **3138 New Castle** (326 MW, online 0.579) have a
  measured median of **exactly 0.000 MW** over the hours the floor asserts they must be online.
  Rule 17 `[R-FLOOR-WINDOW]`: *a bug by definition.*
- **3148 Martins Creek (1700 MW) and 3149 Montour (1504 MW)** — the population's **two largest**
  plants, ST_GAS in the model fleet, genuinely part-time (online 0.382 / 0.456) — carry **no drag
  floor at all**. Neither appears in any D-4 skip list, so this is absence of floor, not absence of
  meter.
- Over six years: **12 of 45** D-4 failure rows and **3.21 of 4.118 TWh (78 %)** of all failing
  floor energy.

**The error runs both ways** — 0.92 GW floored where the meter reads zero, 3.2 GW unfloored — which
is what identifies it as an **allocation** defect rather than a level one. That is exactly ERCOT's
ercot-259 finding, reproduced on PJM's own data.

**Mechanism:** `netload_drag_merit_allocation` (`scenarios.py:12112`, dataclass default `False`).
The same hourly mandate, over the same rows, **filled cheapest-first** across commitment blocks by
ascending bid heat rate instead of spread pro-rata. Rule 19 `[R-ONE-MECH]`: no new floor, no
membership change, no second mechanism id — **only the level source per row moves**. Rule 21
`[R-DOF]`: **zero free parameters** (block sizes are the frozen binning artifact's tranche
capacities; order is the fleet's own bid heat rates). Rule 13: **forward-native** — it is *not* in
`_BACKCAST_ONLY_OVERLAY_FIELDS` (verified), unlike `netload_drag_layup_window_mask`, which is, and
which is the weaker card for exactly that reason. Rule 25 `[R-ISO-SCOPE]`: no per-ISO number is
transferred; PJM's cell enters as its own test.

### 2.1 Pre-solve reallocation, measured (zero LP, `fleet_only=True`)

`scripts/probes/pjm_h13_drag_allocation_phase0.py`. Per-plant drag floor, control vs arm:

| year | plant | ctl TWh | arm TWh | Δ | ctl hrs | arm hrs |
|---|---|---:|---:|---:|---:|---:|
| 2023 | 3131 Shawville | 0.6346 | 0.2197 | **−0.4149** | 7221 | 3188 |
| 2023 | 1353 Big Sandy | 0.2499 | 0.6218 | **+0.3719** | 6182 | 6182 |
| 2023 | 3138 New Castle | 0.3522 | 0.4665 | +0.1143 | 7489 | 7210 |
| 2023 | 3140 Brunner Island | 1.5528 | 1.4989 | −0.0539 | 7666 | 6977 |
| 2024 | 3131 Shawville | 0.6986 | 0.2704 | **−0.4282** | 7262 | 3734 |
| 2024 | 1353 Big Sandy | 0.2700 | 0.6788 | **+0.4088** | 5907 | 5907 |
| 2025 | 3131 Shawville | 0.7547 | 0.2373 | **−0.5174** | 7861 | 4322 |
| 2025 | 1353 Big Sandy | 0.3239 | 0.8398 | **+0.5159** | 6657 | 6657 |

**Aggregate-neutral to 0.0000 TWh in every year** (2023 2.8355 / 2.8355; 2024 3.1229 / 3.1229;
2025 3.5270 / 3.5270). The swap provably cannot double as a level knob — which is the rule-19
claim, verified before the solve rather than asserted.

Direction: the mandate moves **off** the less-committed plant (Shawville, 0.594) **onto** the
most-committed (Big Sandy, 0.769), and Shawville's binding-hour footprint falls 49–56 %.

**STATED AS A LIMIT, NOT BURIED — two things this measurement does NOT establish.**
(a) **It does not predict the D-4 verdict.** The probe measures the *pre-solve floor array*; D-4
measures hours the floor *actually binds in the solved dispatch*. Those sets differ by ~3× (2023
plant 3138: 7489 array hours vs 2411 D-4 binding hours), so the probe's medians are **not**
comparable to D-4's and are reported here only as a footprint. **Only the solve can move G3.**
(b) **The swap does not reach Martins Creek or Montour** — they carry no commitment tranches, so
merit fill cannot find them. The arm therefore reshuffles among the same four plants and leaves
half the two-way error standing. Recorded at the gate, not discovered after.

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` (b)) — form 4 is VALID, no control solves

pjm-h12 spent twelve solves because its charter called `hubs.py::_basis_bridge_blackouts` LIVE;
**measured, that drift was nil** (2022 control reproduced the committed keeper, 0 of 78,840 price
cells moved) at SHA `65ab6205c40a3d5703f084bf747f2b132eee5c28`. Form 4 is therefore empirically
validated to that SHA, and the audit window is `65ab6205 → HEAD`:

| file | change | class |
|---|---|---|
| `config/constants.py` | NWPP capacity-factor rows only (a different NERC region; keyed lookup) | **INERT** |
| `config/scenarios.py` | **zero executable lines** — comment/docstring only | **INERT** |
| `data/fuel/hubs.py` | one hunk, inside `if bridge_all_years and bridge_hh is not None…` — reachable only when `caiso_citygate_blackout_bridge` passes bridge args; **absent (default False) on both PJM bundles** | **INERT** |

**All hunks INERT ⇒ the keeper's committed bundle IS the control.** Six arm shards, no control
solves — half of pjm-h12's LP for a better-evidenced card.

**Control config signature (both bundles, identical):** `mode=backcast`, `gas_st_netload_drag=True`,
slope `0.01029` / intercept `−0.7263` / cap `0.39`, `gas_st_drag_seasonal=False`,
`netload_drag_merit_allocation=False`, `netload_drag_layup_window_mask=False`,
`netload_drag_min_run_persistence=False`, `mustrun_plant_exclusions=False`, `ct_netload_drag=True`.

---

## 4. THE GATES — declared ex ante, never re-read

**Baseline (keeper, scored at HEAD):** eight criteria PASS, zero caveats, `CALIBRATED`.
**Baseline D-4 `st_netload_drag` FAIL rows:** 2020 **3**, 2021 **2**, 2022 **2**, 2023 **1**,
2024 **2**, 2025 **2** — **12 total**.

| gate | bar | kills the card if |
|---|---|---|
| **G1 — the arm fires** | per-plant drag allocation differs from control, every year | it is inert |
| **G2 — rule 19 integrity** | D-2 `st_netload_drag` total forced TWh within **±1 %** of control, every year | the swap doubles as a level knob |
| **G3 — RULE 17 IS SERVED** | D-4 `st_netload_drag` FAIL rows **do not increase in ANY year** **and** the six-year total **strictly decreases** below 12 | the card's own justification fails |
| **G4 — the NAMED plants** | **3131 Shawville** and **3138 New Castle**: at least one flips FAIL → pass in **≥ 3** of the years it currently fails (3131 fails 5, 3138 fails 6) | it repairs a different population than the one it was chartered on |
| **G5 — nothing stacked** | no OTHER mechanism's D-2 forced share moves > **0.5 %**, every year | it is not one mechanism |

**G3 is this lane's G6** — the gate written to test the card's own justification, which is what
caught pjm-h12's charter. **G4 names the plants, not a count** — correction #2, discharged.

### 4.1 THE ASYMMETRY — what is REPORTED and can never move a gate (rule 1 `[R-STRUCT]`)

Written down **before** the solve, so no number can be re-read into a criterion:

- **Every scored band** — C1, C2, C3a, C3b, C3c, C4, C8 — and the determination itself. A
  structurally-correct mechanism **stays in even if the residual worsens**, and nothing here is
  selected because a residual moved. A downgrade from `CALIBRATED` is **surfaced to the owner as a
  promotion fact**, never used to select or reject the mechanism.
- **C8 forced share and the D-A diurnal amplitude**: reported at full magnitude. The drag's forced
  share may rise; rule 20's shape-and-provenance escalation governs it and is never waived.
- **Per-plant reallocation magnitudes** and the Martins Creek / Montour gap (§2.1(b)).
- **Trough/decile-1 price and seam flow.** pjm-h12's G4/G5 made these *gates* on a causal chain and
  they refuted 0/6. This card makes **no** price or flow prediction, so they are reported only.

---

## 5. Shard plan (rules 32 / 34 / 36)

Six shards, **one year each**, all against their own committed control, all pushing their **full**
bundle including `dispatch/<year>_P1.parquet` (rule 34(a): `.gitignore` **negation** + **plain
`git add`**, never `git add -f`).

| year | source bundle | out-dir | branch |
|---|---|---|---|
| 2020 | `pjm_h11_touchpoint_span` | `results/calibration/pjm_h13_meritalloc_2020` | `claude/pjm-h13-meritalloc-2020` |
| 2021 | `pjm_h11_touchpoint_span` | `…_2021` | `claude/pjm-h13-meritalloc-2021` |
| 2022 | `pjm_h11_touchpoint_span` | `…_2022` | `claude/pjm-h13-meritalloc-2022` |
| 2023 | `pjm_h11_keeper_span` | `…_2023` | `claude/pjm-h13-meritalloc-2023` |
| 2024 | `pjm_h11_keeper_span` | `…_2024` | `claude/pjm-h13-meritalloc-2024` |
| 2025 | `pjm_h11_keeper_span` | `…_2025` | `claude/pjm-h13-meritalloc-2025` |

Arming needs **no code change**:
`replay_keeper.py <source> --out-dir <dir> --years <year> --set netload_drag_merit_allocation=true`.

Rule 34(c): PJM's registered year set is **{2020, 2021, 2022, 2023, 2024, 2025}** — enumerated from
the two sidecars **before** anything is pruned (rule 35(b)). All six are launched; none is omitted.

**Retrievability (rule 34(e)):** each bundle lands on its shard branch and the parent composes and
lands the keeper bundle on `main` **before** its PR merges (rule 33(f)(4)(ii)). Shard branches are
transport, not storage.

---

## 6. What this lane will NOT do

- **Not re-test `mustrun_commitment_feasibility_clip`** — adjudicated `R` by pjm-h12 card D-3
  (rule 28(a) DO-NOT-REDO).
- **Not rebuild an hourly seam ladder** — pjm-h12 card D-2 killed it at zero LP (the ladder's own
  hourly *r* is 0.052 fed the price it was derived from).
- **Not touch the three truncated ladder rungs** (owner question Q1) or any other open owner
  question. They are carried forward in the RESULT, unresolved.
- **Not arm `mustrun_plant_exclusions`** in the same run — it is a different floor family and
  bundling it would make any verdict flip unattributable, which is precisely the conflation that
  cost pjm-h12 its charter.

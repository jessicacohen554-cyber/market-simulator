# FINDING — T1-H capacity-entry Phase-0: the STORAGE leg (D-2 + D-3) censused and replayed, the WIND leg (D-8/B-3) measured

_2026-08-30 · T1-H capacity-entry repair lane, **Phase-0** · charter
`docs/PRECOMMIT-t1h-capacity-entry-2026-08-30.md` (owner ruling 2026-08-30,
director sitting, decision card 2) · parent defect register
`docs/FINDING-entry-screen-t1h-2026-08.md` (D-1 … D-9) · dedup subject
`docs/handoffs/FINDING-capx-d11r-entry-volume-rule-2026-08-30.md`._

**ZERO SOLVE.** No LP solve, no hindcast re-run, no mechanism / default /
constant / `ScenarioConfig` change, no matrix cell moved, no keeper, marker,
registry or board file touched. Every number below is read from a committed
artifact or is arithmetic replayed on committed inputs by
`scripts/probes/_t1h_capentry_phase0.py` (committed with this finding;
`--section {dedup,d2,d3,legb}`). Nothing here is tested, so rule 26
`[R-MECH-MATRIX]` duty (b) does not fire and **no cell is added or moved.**

---

## 0. The one-paragraph answer

**D-1 is capx's; D-2 and D-3 are alive at HEAD, and D11-R's walk inherits both.**
The margin-exhaustion rule changes how *much* the screen builds, never *which*
technology it may consider or *what object* it ranks on — verified line by line
at HEAD. The census measures the anachronism at full magnitude: **100 % of the
storage the T1-H lane builds, in every arm, is a technology class with zero
megawatts operating in ERCOT** — the registered keeper's build is
cap-weighted **64.0 hours** of duration against a measured ERCOT 2023–2025
vintage of **1.60 hours**, and its 3.0 GW of iron-air is **1,875×** the entire
US metal-air installed base, decided one year before that base's first
megawatt. The D-3 replay reproduces the committed ledger exactly and then shows
the cost-normalized re-rank **does not by itself rescue li-ion**: it flips only
the second slot, flow_battery → compressed_air. **Li-ion returns only when D-2
and D-3 land together**, and then the cost-normalized metric picks
**`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000** — the 1.6-hour-class technology
ERCOT actually built — where the absolute metric on the same restricted pool
picks the wrong duration. On the wind leg, the dual-based signal object closes
**8.9 %** of the entry miss end-to-end and a zonally-resolved variant is
**not computable zero-solve** as a volume; what *is* measurable is that the
zonal leg is the *majority* of the capture repair in the last step (**96.8 %**)
and that it is a **level** effect, not a shape one — wind's within-zone capture
ratio is **below 1.0 in every ERCOT zone**, and 0.477 in Panhandle.

---

## 1. Step 0 — DEDUP: what D11-R's rule does and does not touch

`scripts/probes/_t1h_capentry_phase0.py --section dedup`, all checks measured
against HEAD (`2393d47`), not inherited from the D11-R finding's prose.

| check | measured at HEAD |
|---|---|
| `entry_margin_exhaustion: bool = False` registered in `ScenarioConfig` | **yes** (`scenarios.py:4178`, GATED default-OFF) |
| both D11-R arms present as committed bundles | **yes** (`…-t1h-d11r-control` key `28cef3500ec1fd9e`, `…-t1h-d11r-exhaustion` key `cc7bbe1170db65c2`) |
| storage bang-bang volume path still present | **yes** (`storage.py:1978`, `build_mw = min(remaining, per_tech_cap)`) |
| storage margin-exhaustion walk present | **yes** (`storage.py:1904-1958`) |
| thermal/VRE walk present | **yes** (`new_entry.py`, `entry_reprice=`) |
| **storage availability-year gate** | **ABSENT** — no `_STORAGE_AVAILABLE_YEAR`, no `*_available_year` reference anywhere in `storage.py` |
| storage tech pool iterated unconditionally | **yes, on BOTH paths** — `storage.py:1964` (bang-bang) and `storage.py:1933` (the D11-R walk) |
| thermal path's gate, for contrast | **present** — `_EMERGING_AVAILABLE_YEAR` `new_entry.py:185`, consumed `:259` |
| **ranking object** | **absolute `$/MW-yr` on BOTH paths** — `storage.py:1969` `margins.sort(key=lambda m: m[0], reverse=True)` (bang-bang) and `storage.py:1939` `if m > best_margin` (walk) |
| `STORAGE_TECH_BUILD_SHARE_CAP` provenance | still `"Source: modeling assumption"` (`capacity_market.py:547`) — the parent finding's rule 5 `[R-NO-MAGIC]` item, unrepaired |

### 1.1 The dedup verdict, stated precisely

- **D-1 (bang-bang entry VOLUME) is CLAIMED by capx D11-R and is OUT OF SCOPE
  here.** `entry_margin_exhaustion` replaces the bang-bang loop in *both*
  allocators with a tranche walk that stops when the repriced margin no longer
  clears. Confirmed as chartered; nothing in this lane re-tests it. Its arming
  is escalated to the owner and held until D12 — this lane does not touch that.
- **D-2 (no storage availability-year gate) is NOT touched by D11-R, and the
  walk INHERITS it.** The walk's candidate loop (`storage.py:1933`) iterates the
  identical unconditional `STORAGE_TECHS.items()` as the bang-bang loop. The
  margin-exhaustion arm's *own* 2023 build is **3,000 MW of iron-air** — the
  defect, at 100 % of that arm's storage.
- **D-3 (absolute `$/MW-yr` ranking) is NOT closed by D11-R.** The walk
  re-evaluates the ranking *more often* (per 250 MW tranche, at a repriced
  signal and a grown fleet) but ranks on the **same object**: the largest
  absolute margin wins the tranche. D11-R's own §3.4 says so in its own words —
  *"Li-ion still never builds … that remains L-3/D-3."* Confirmed independently
  here from the code, not from the prose.
- **Partial transfer:** D11-R's rule *does* remove the second storage slot in
  the ERCOT A/B (5,000 → 3,000 MW, flow_battery gone), which is the same
  megawatts D-3's re-rank would have re-allocated. So the *second-slot
  technology question* is partly overtaken **in the armed posture only** — the
  slot exists in the shipped default, which is unarmed. This is recorded as a
  Phase-1 sequencing note in §5, not as a scope transfer: D-3's defect is the
  ranking object, which survives in both postures.
- **Nothing chartered here re-tests an adjudicated `R`/`I`/`G` cell.** Checked:
  `entry_lookahead_reprice` ERCOT `K`/`fc O` (C-1) — this lane measures it and
  proposes nothing; `capacity_screen_scarcity_restoration` `O`/`fc K`;
  `entry_margin_exhaustion` `O`/`fc O` (D11-R). No cell is moved.

### 1.2 Stop rule (charter step 4) — **NEITHER LEG STOPS**

- **Leg A (D-2 + D-3): NOT overtaken.** Both defects are present at HEAD on
  both allocator paths, verified above. Leg A proceeds to Phase-1.
- **Leg B (D-8/B-3): NOT overtaken.** `runner._lookahead_reprice_signal` still
  returns a system row broadcast to every zone; independently corroborated here
  by the artifact itself — every committed `screen_signal_diag_*.npz` carries
  `price_base_usd_mwh` with shape **(8760,)** and **no zone axis at all**, so
  the zone-flatness is structural in the dump, not merely in the code. Leg B
  remains a measurement rung, as chartered.

---

## 2. Step 1 — D-2 census: the anachronism at full magnitude

### 2.1 What the T1-H lane actually built

Per-decision-year storage, MW, from committed probe artifacts
(`entry_signal_disarm_ledger_ercot.json` for the registered/control and disarm
arms; `entry_volume_rule_ab_ercot.json` for the exhaustion arm; the CAISO
bundle's own `score.json`). "Registered" = `ercot-2021-2025-realized-t1h-refresh`,
key `28cef3500ec1fd9e`, whose per-step split the control arm reproduces exactly.

| decision year | registered / control | disarm (`entry_lookahead_reprice=False`) | d11r-exhaustion (armed) |
|---|---|---|---|
| 2021 | — | — | — |
| 2022 (bridge) | — | iron_air 3,000 · compressed_air 2,000 | — |
| 2023 | **iron_air 3,000 · flow_battery 2,000** | iron_air 3,000 · compressed_air 2,000 | **iron_air 3,000** |
| 2024 | — | iron_air 3,000 · compressed_air 2,000 | — |
| 2025 | — | iron_air 3,000 | — |
| **total decided** | **5,000 MW** | **18,000 MW** | **3,000 MW** |
| **cap-wtd duration** | **64.0 h** | **69.3 h** | **100.0 h** |
| **li-ion share** | **0 %** | **0 %** | **0 %** |

CAISO `caiso-2021-2025-realized` (key `408f9199a82f5814`) decides **0 MW** of
storage in every year against **15.147 GW** actual — no technology to censusize,
which is D-8/D-9's object, not D-2's.

### 2.2 The measured deployment record it is being compared against

Source: `data/raw/eia-860/eia860_energy_storage_operable.parquet` and
`…_proposed.parquet`, joined to `eia860_plant.parquet` on `Plant Code` for the
`Balancing Authority Code == "ERCO"` filter (the crosswalk
`capacity_market.STORAGE_BASE_FLEET_MW`'s own comment documents), plus
`eia860_generator_operable.parquet` `Prime Mover == "CE"` for CAES. EIA-860 2025
Early Release. **Diagnostic evidence for a census — it feeds no model path, so
rule 13 `[R-MEASURED]` is not engaged.**

| `STORAGE_TECHS` entry | EIA-860 class | first US operating year | US operable MW | **ERCOT operable MW** | ERCOT proposed MW |
|---|---|--:|--:|--:|--:|
| `li_ion_4hr` / `_8hr` / `_12hr` | LIB | **2012** | 42,350.6 (957 units) | **13,659.3** | 28,574.4 |
| `flow_battery` (VRFB) | FLB | **2017** | **321.0** (11 units) | **0.0** | **0.0** |
| `iron_air` (metal-air) | MAB | **2024** | **1.6** (1 unit) | **0.0** | **0.0** |
| `compressed_air` | (not in the storage schedule) | **1991** (McIntosh, AL, 110 MW — the only US CAES operable generator) | 110.0 | **0.0** | **0.0** |
| — | OTH | 2016 | 641.5 | 250.0 (two 2-hour BESS) | 49.9 |
| — | ECC | 2025 | 175.0 | 0.0 | 100.0 |

**The anachronism, at full magnitude and in both directions:**

1. **Iron-air.** The registered keeper decides **3,000 MW** of a 100-hour
   metal-air battery in a **2023** decision year. The US metal-air operable base
   is **1.6 MW**, first operating year **2024** — so the model builds **1,875×
   the entire national installed base of the class, one year before that base's
   first megawatt existed**, in an ISO with **0.0 MW** operable and **0.0 MW**
   proposed. The armed exhaustion arm builds the same 3,000 MW; the disarm arm
   builds **12,000 MW** across four steps.
2. **Flow battery.** The registered keeper decides **2,000 MW** of VRFB in 2023
   — **6.2×** the entire US flow-battery operable base (321.0 MW), in an ISO with
   **0.0 MW** operable and **0.0 MW** proposed.
3. **Compressed air.** The disarm arm decides **6,000 MW** of adiabatic CAES —
   **54×** the only US CAES plant, which is a 1991 diabatic salt-cavern unit in
   Alabama, and which the repo's own comment already flags as geology-gated in a
   way "this ISO-agnostic entry screen cannot site" (`capacity_market.py:412-414`).
4. **Duration.** Measured ERCOT 2023–2025 vintage: **11,779.3 MW / 18,830.8 MWh**
   = cap-weighted **1.60 h**, **maximum 4.0 h**, and **0.0 MW above 4.5 h**
   (histogram: 5,142.0 MW ≤1.5 h; 6,564.3 MW 1.5–2.5 h; 73.0 MW 2.5–4.5 h).
   Model: **64.0 h** registered, **69.3 h** disarm, **100.0 h** armed. The
   registered keeper's build sits **40× the measured duration** of the fleet it
   is forecasting, and **100 % of it** lies in duration classes with **zero
   measured ERCOT deployment**.
5. **Direction stated honestly.** The gate would *reduce* T1-H's storage build
   in the registered arm (5,000 → 0 MW if no admitted tech clears in 2023,
   or → a li-ion mix per §3), against an actual of **13.691 GW**. **The storage
   addition band is already −63.5 % and a D-2 gate alone can only make it
   worse.** That is the rule 1 `[R-STRUCT]` point of the lane and is
   pre-registered here: D-2 is proposed because the model must not build
   technologies that do not exist, **not** because it improves the band. The
   Phase-1 kill-gates in the charter (K1/K2) are the check on that, and this
   paragraph is what K1 must be read against.

### 2.3 The citation gap — stated, not filled

**The repo carries NO commercial-availability-year citation for ANY storage
technology.** There is no `_STORAGE_AVAILABLE_YEAR` mapping, no
`ScenarioConfig.*_available_year` field for a storage tech, and no
`docs/parameter-citations.md` row that supplies one. Per the charter this lane
**does not invent them.** For contrast, the thermal path has the whole family
cited and registered: `h2_available_year = 2035`, `ccs_available_year = 2030`,
`egs_available_year = 2030`, `offshore_wind_available_year = 2030`,
`smr_available_year = None` (`scenarios.py:2463-2472`).

What §2.2 supplies is a *measurement* (first US operating year per EIA-860
class, and deployed scale), **not** a drop-in availability year. The two are
different objects and Phase-1 must not conflate them: "first US megawatt" is
not "the year a merchant developer can procure this at GW scale in ERCOT". A
Phase-1 gate needs a stated definition plus a primary source per technology,
entered in `constants.py` with its citation (rule 5 `[R-NO-MAGIC]`); the
EIA-860 rows above are admissible as a **corroborating lower bound** on any
such year, and as the falsifier if a proposed year precedes them.

### 2.4 A repo-internal inconsistency the census surfaced

`capacity_market.py:551` `STORAGE_TECH_POWER_SHARE = {li_ion_4hr 0.70,
li_ion_8hr 0.25, iron_air 0.05}` — the model's **own** fleet-composition
constant assigns `flow_battery`, `compressed_air` and `li_ion_12hr` a **0 %**
share, and iron-air 5 %. The entry screen nonetheless builds flow_battery at
2,000 MW and (in the disarm arm) CAES at 6,000 MW. Two constants in the same
module disagree about which technologies the fleet contains. **Reported, not
fixed** — it is evidence for the D-2 gate's *shape*, not a separate lever.

---

## 3. Step 2 — D-3 replay: the ranking object, and the counterfactual mix

Inputs: the committed entering-2023 margins from
`results/calibration/entry_screen_t1h_phase0_ercot.json` (which the parent
finding §2 established reproduce the registered ledger exactly, and which the
L-1 probe re-verified tech-by-tech, `validation.storage_vs_phase0.all_match =
true`). Capital costs: `config/capacity_market.py::STORAGE_TECHS[*]["capex_per_kw"]`,
read live and asserted against the finding's basis by the probe (a drift raises
rather than silently re-ranks). Allocator: `storage.py:1969-1980`, reproduced
verbatim so the counterfactual differs in the **ranking only**.

**All six technologies clear in entering-2023**, by 10–20×; every other decision
year clears none. So the entire ERCOT storage forecast is one ranking decision.

| tech | margin `$/MW-yr` | `capex_per_kw` | **margin per $/kW** | margin per annual cost |
|---|--:|--:|--:|--:|
| `iron_air` | 2,914,066.0 | 2,000.0 | **1,457.03** | 20.986 |
| `flow_battery` | 2,650,472.8 | 4,700.0 | 563.93 | 9.005 |
| `li_ion_12hr` | 2,639,205.8 | 4,498.4 | 586.70 | 7.073 |
| `compressed_air` | 2,486,792.1 | 2,700.0 | **921.03** | 14.589 |
| `li_ion_8hr` | 2,401,477.5 | 3,154.3 | 761.33 | 9.206 |
| `li_ion_4hr` | 1,469,714.9 | 1,810.3 | **811.86** | 9.898 |

### 3.1 The replay reproduces the committed ledger exactly

Ranked on absolute `$/MW-yr`: `iron_air > flow_battery > li_ion_12hr >
compressed_air > li_ion_8hr > li_ion_4hr`; allocator →
**`iron_air` 3,000 MW + `flow_battery` 2,000 MW** (budget 5,000 MW =
`STORAGE_ANNUAL_BUILD_CAP_MW["ERCOT"]`, per-tech cap 3,000 MW = budget ×
`STORAGE_TECH_BUILD_SHARE_CAP` 0.6). **This is byte-for-byte the registered
ledger** — the probe asserts it (`shipped_matches_committed_ledger: true`) in
every decision year, including the three where nothing clears.

### 3.2 The counterfactual on margin per unit capital cost

Ranked on `margin / capex_per_kw`: `iron_air > compressed_air > li_ion_4hr >
li_ion_8hr > li_ion_12hr > flow_battery`; allocator →
**`iron_air` 3,000 MW + `compressed_air` 2,000 MW**.

| | slot 1 (3,000 MW) | slot 2 (2,000 MW) |
|---|---|---|
| shipped (absolute `$/MW-yr`) | `iron_air` | `flow_battery` |
| **counterfactual (margin per $/kW)** | `iron_air` | **`compressed_air`** |
| sensitivity (margin per annualized cost) | `iron_air` | `compressed_air` |

**Three things this establishes, and one it refutes:**

1. **The metric choice is robust.** Normalizing by *capital* cost and by
   *annualized* cost give the identical build mix and the same top-four order —
   so the counterfactual is not an artifact of which cost denominator is chosen.
   (The two metrics differ only in the ordering of the two techs that never
   build, `li_ion_12hr` ↔ `flow_battery`.)
2. **The magnitude of the mis-ranking is large.** `flow_battery` is **2nd** of 6
   on absolute margin and **last** of 6 on margin per $/kW — a six-place swing.
   `li_ion_4hr` is **last** on absolute margin and **3rd** on margin per $/kW.
   The shipped metric is not noisily wrong; it is systematically biased toward
   the most capital-intensive technology, because a bigger machine earns a
   bigger absolute margin.
3. **`iron_air` leads on BOTH metrics** — it is the cheapest per kW of the
   long-duration set *and* the highest-margin. So **D-3 alone cannot remove the
   iron-air build**; only D-2 can. The two defects are genuinely separate and
   neither substitutes for the other.
4. **REFUTED: "cost-normalization rescues li-ion".** It does not. Under D-3
   alone li-ion still builds **zero MW**, exactly as under the shipped metric.
   Any Phase-1 framing that sells D-3 as the li-ion repair is wrong on this
   arithmetic.

### 3.3 The joint D-2 + D-3 counterfactual — where li-ion actually returns

Restricting the candidate pool (the D-2 gate's effect) and then applying each
metric. Two pools are reported because the answer depends on which durations a
gate admits:

| pool | absolute `$/MW-yr` | **margin per $/kW** |
|---|---|---|
| all li-ion `{4hr, 8hr, 12hr}` | `li_ion_12hr` 3,000 + `li_ion_8hr` 2,000 | **`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000** |
| deployed li-ion `{4hr, 8hr}` | `li_ion_8hr` 3,000 + `li_ion_4hr` 2,000 | **`li_ion_4hr` 3,000 + `li_ion_8hr` 2,000** |

**The cost-normalized metric is invariant to the pool choice; the absolute
metric is not.** That is the sharpest argument for D-3 in this document: under
the absolute metric, *which* li-ion duration leads depends on whether a 12-hour
class the ERCOT fleet has never deployed happens to be in the pool; under the
cost-normalized metric the answer is `li_ion_4hr` either way — and `li_ion_4hr`
is the class carrying **5,142.0 MW of the measured 2023–2025 ERCOT vintage at
≤1.5 h and 6,564.3 MW at 1.5–2.5 h**, i.e. the short-duration end.

**One correction to the parent finding, recorded so it is not propagated.**
`docs/FINDING-entry-screen-t1h-2026-08.md` §2 item 3 and §7 L-3 state that a
li-ion-restricted pool yields "`li_ion_8hr` 3,000 + `li_ion_4hr` 2,000". That
is **correct only for the `{4hr, 8hr}` pool** — reproduced here exactly. On the
full `{4hr, 8hr, 12hr}` li-ion pool the absolute metric yields **`li_ion_12hr`
3,000 + `li_ion_8hr` 2,000** instead, because `li_ion_12hr` clears at
+$2,639,206/MW-yr against `li_ion_8hr`'s +$2,401,478. The parent's arithmetic is
sound; its pool was narrower than "li-ion" reads. No conclusion in the parent
finding depends on which of the two it is.

---

## 4. Step 3 — Leg B: how much of the wind miss closes, measured

Scope reminder: this leg is a **measurement rung**. It arms nothing, and the
signal-object decision (C-1, `entry_lookahead_reprice` ERCOT `fc O`) is reserved
to the owner.

### 4.1 (a) The dual-based signal object — measured end-to-end

The disarm run **is** the dual-based signal object, solved and committed. Its
additions, decision basis 2023–2025, against the registered arm:

| arm | wind model GW | actual GW | remaining gap GW | **share of the miss closed** |
|---|--:|--:|--:|--:|
| registered / control (shipped zone-flat signal) | 0.350 | 12.663 | 12.313 | — |
| **t1h-disarm** (dual-based signal) | **1.442** | 12.663 | **11.221** | **8.87 %** |
| t1h-d11r-exhaustion (volume rule, shipped signal) | 0.954 | 12.663 | 11.709 | 4.91 % |

**The dual-based signal object closes 8.9 % of the wind entry miss and leaves
91.1 % open.** Reported at full magnitude in both directions: the band still
reads FAIL (−88.6 %), the same run's terminal reserve margin worsens from
25.19 % to 40.24 % (committed disarm ledger), and the same run's gas_ct and
storage bands move the other way. Nothing here is an argument for arming it.

Two independent partial closures exist and **have never been measured
together**: signal (disarm, +1.092 GW) and volume (D11-R exhaustion, +0.604 GW).
Their combination is a Phase-1/D12 question, not this lane's, and this finding
does **not** add them — they are not additive by construction, since both act on
the same shared queue budget.

### 4.2 The C-1 caveat, verified rather than inherited

The charter flags that a disarmed run emits no `screen_signal_diag` npz.
**Verified by file count on disk:**

| bundle | `screen_signal_diag_*.npz` |
|---|--:|
| `…-t1h-refresh` (registered) | 4 |
| `…-t1h-control` | 4 |
| **`…-t1h-disarm`** | **0** |
| `…-t1h-d11r-control` | 4 |
| `…-t1h-d11r-exhaustion` | 4 |
| `caiso-2021-2025-realized` (registered) | 0 (defect D-7) |

So **the disarm run's own signal object is not available offline** — its
capture ratios cannot be read from the artifact it produced. Every capture
number in §4.3 therefore uses the L-1 replay's **stand-in**: the committed
zonal hourly duals of the backcast keeper `ercot223_release_arm`. That stand-in
carries a declared bound (L-1 §1.1), and the disarm solve already **sized** it:
material for gas (prediction 4 failed), immaterial for storage (predictions 1
and 2 held exactly). This finding inherits that bound and does not re-litigate it.

### 4.3 (b) The zonally-resolved variant — what is and is not computable

Wind capture ratio (capture price ÷ the construction's system mean) under three
constructions, per decision step, from
`results/calibration/entry_signal_l1_dual_replay_ercot.json`:

| step | shipped (zone-flat) | dual, system row | dual, **build-zone row** | **level leg** | **zonal leg** | zonal share of the repair |
|---|--:|--:|--:|--:|--:|--:|
| 2022 | 0.7426 | — | — | — | — | *blocked: no committed duals for prior solve 2021* |
| 2023 † | 0.4936 | 0.9068 | 0.9880 | +0.4132 | +0.0812 | 16.4 % |
| 2024 | 0.8048 | 0.9068 | 0.9880 | +0.1020 | +0.0812 | **44.3 %** |
| 2025 | 0.9272 | 0.9313 | **1.0550** | +0.0041 | **+0.1237** | **96.8 %** |

† the 2023 row's dual arm is `dual_same_year` — the entering year's own realized
prices, foresight the screen cannot have. **Diagnostic only, never the
counterfactual**, as the L-1 artifact's own caveat field states. The 2024 and
2025 rows are `dual_prior_solve`, the admissible construction.

For every step the shipped arm's system row and build-zone row are **identical to
1e-9** — the probe asserts it (`shipped_zone_flat_verified: true`). D-8's
zone-flatness is confirmed a third way.

**The three findings this measurement produces:**

1. **The zonal leg is the majority of the capture repair in the admissible
   steps' later year (96.8 % in 2025, 44.3 % in 2024).** As the ORDC adder
   collapses across the cobweb, the level leg goes to nearly nothing (+0.0041 in
   2025) and essentially the whole repair is locational.
2. **It is a LEVEL effect, not a shape effect — and this is the finding that
   most changes what a Phase-1 "zonal variant" could claim.** Re-measured
   independently here from first principles (the keeper's committed zonal duals
   × the T1-H dump's own hourly wind potential), wind's capture ratio **against
   its own zone's mean** is **below 1.0 in every ERCOT zone, in both measurable
   years**:

   | zone (duals 2024) | zone mean $/MWh | wind capture $/MWh | wind capture ratio vs **own** zone mean |
   |---|--:|--:|--:|
   | Houston / North / South / South_Central | 29.263 | 28.063 | 0.9590 |
   | West (**the build zone**) | 29.254 | 28.060 | 0.9592 |
   | Northeast | 28.114 | 27.458 | 0.9767 |
   | **Panhandle** | **11.752** | **5.611** | **0.4774** |
   | system unweighted mean | 26.596 | 24.768 | 0.9313 |

   The headline 1.055 build-zone ratio arises because West's price **level**
   (29.254) sits above the unweighted ISO mean (26.596) — and that ISO mean is
   dragged down by Panhandle at 11.752. Resolving zonally does not make wind
   *shape*-favoured anywhere; it makes the build zone's *level* favourable
   relative to an average that includes the congested wind pocket.
3. **The build-zone choice is doing the work, and it is a modelling choice.**
   `data/renewables.py:219` routes **both** ERCOT wind and solar to `"West"`.
   Panhandle — the wind-rich, congestion-depressed zone with a 0.477 capture
   ratio and a 11.752 mean — is never a build zone, so its economics never reach
   the screen. A "zonally-resolved variant" that sited wind where ERCOT's wind
   actually interconnects would move the answer by roughly a factor of two in
   the opposite direction. Recorded so Phase-1 does not read row 1 as an
   unconditional argument for zonal resolution.

**And the honest limit.** In **both** admissible steps, wind's per-MWh margin at
the build-zone row is still **negative** (2024: −0.74 $/MWh; 2025: −3.76 $/MWh
against a 31.82 $/MWh LCOE) — so **on this stand-in, zonal resolution does not
make wind clear on merit.** The wind that the disarm run actually built entered
in the **2022** step, whose duals are **not committed** ("no committed hourly LP
duals for prior solve 2021 — keeper sidecars span 2023-2025 only"), so the entry
that occurred is precisely the one this replay cannot explain.

### 4.4 Computability, stated as the charter requires

| question | status |
|---|---|
| (a) end-to-end entry-volume effect of the dual signal | **MEASURED** — committed disarm `score.json` + ledger artifact |
| (a) the disarm run's own screen-signal object | **NOT COMPUTABLE zero-solve** — 0 dumps emitted, verified; the C-1 recorded caveat holds |
| (b) zonal **capture-ratio** effect | **MEASURED on a STAND-IN** — keeper backcast duals, bound declared by L-1 §1.1 and sized by the disarm solve |
| (b) zonal **entry-volume** effect (GW of wind) | **NOT COMPUTABLE zero-solve** — build volume is set jointly by the shared queue budget, the solar/wind competition for it, and (armed) the exhaustion walk; no committed artifact carries a zonally-resolved entry *decision*. **Recorded as a measured limitation. Not estimated.** |
| (b) the 2022 step, where the disarm's wind actually entered | **BLOCKED** — no committed hourly duals for prior solve 2021 |
| CAISO's half of either question | **BLOCKED** — the registered CAISO bundle carries 0 dumps (D-7); L-5 is the cheap unblocker, already named in the parent finding §7 |

---

## 5. What Phase-1 inherits from this record

Stated as findings, not as a plan; Phase-1 opens on the charter's terms and
arming remains an owner decision on the A/B record.

1. **D-2 and D-3 are independent and neither substitutes for the other.**
   D-3 alone changes only slot 2 (flow_battery → compressed_air) and builds
   **zero li-ion**. D-2 alone removes iron-air and flow_battery but, on the
   absolute metric, hands slot 1 to whichever li-ion duration is in the pool.
   **Only the pair produces `li_ion_4hr` 3,000 + `li_ion_8hr` 2,000**, and only
   the pair is pool-invariant.
2. **D-2 needs cited availability years that do not exist in the repo yet.**
   §2.3. The EIA-860 rows in §2.2 are a corroborating lower bound and a
   falsifier, not the citation.
3. **The pre-registered direction of D-2's effect on the bands is WORSE**
   (§2.2 item 5). Phase-1's K1 gate must be read against that, and the
   mechanism must not be withdrawn because the residual moves the wrong way
   (rule 1 `[R-STRUCT]`).
4. **Sequencing note.** The parent finding's L-6 (the D-4 cost/life
   specification defect) makes long-duration storage *cheaper* and must not
   land before D-2 — the parent already says "sequence L-3 before L-6" and this
   census is why. Separately, in the **armed** D11-R posture the second storage
   slot no longer exists, so D-3's measurable effect there is smaller than in
   the shipped default; the D-3 A/B should therefore be run at the **shipped
   (unarmed) default**, where the slot exists, and not against the exhaustion
   arm.
5. **Leg B does not become a repair rung on this evidence.** The dual object
   closes 8.9 % of the wind miss, the zonal variant's volume effect is not
   measurable without a solve, and the zonal capture repair is a level effect
   whose sign depends on the build-zone choice. The measured decision input for
   the owner's C-1 call is delivered; no lever is proposed.

---

## 6. Rule compliance

- **Rule 1 `[R-STRUCT]`** — the D-2 direction on the addition bands is
  **pre-registered as worse** (§2.2 item 5) and the mechanism is argued from
  the deployment record, not the residual. Every improvement figure in §4 is
  reported with its cost at full magnitude.
- **Rule 5 `[R-NO-MAGIC]`** — no availability year is invented (§2.3); the
  uncited `STORAGE_TECH_BUILD_SHARE_CAP` is re-reported, not fixed.
- **Rule 12 `[R-PARALLEL]`** — no solve run, so nothing to parallelize.
- **Rule 13 `[R-MEASURED]`** — the EIA-860 census is diagnostic evidence for a
  finding; it feeds no model path and no residual is fitted to it.
- **Rule 19 `[R-ONE-MECH]`** — §1.1 enumerates what already governs entry
  volume (D11-R) and tech eligibility (nothing) before naming anything.
- **Rule 21 `[R-DOF]`** — the D-3 metric is a ratio of two quantities the screen
  already holds (its own margin and `STORAGE_TECHS[*]["capex_per_kw"]`); the
  §3.2 sensitivity shows the answer does not depend on the denominator choice.
  **No free parameter is introduced by this finding.**
- **Rule 22 `[R-HOLDOUT]`** — no year is solved, scored or registered; every
  artifact read is from the registered 2021–2025 T1-H window; the freeze is
  untouched.
- **Rule 24 `[R-REGISTRY]`** — nothing tunable changed; no `ScenarioConfig`
  edit.
- **Rule 25 `[R-ISO-SCOPE]`** — every measured number is ERCOT's except the
  CAISO zero, which is quoted from CAISO's own bundle. No verdict transfers.
- **Rule 26 `[R-MECH-MATRIX]`** — **nothing was tested, so no cell is added or
  moved.** The cells checked before writing are listed in §1.1.
- **Rule 27 `[R-PUSH]`** — two new files, written locally and pushed as on-disk
  bytes; no existing ≥300-line file rewritten; no CI workflow added.
- **Out of scope and untouched:** the mechanism matrix, every keeper shard,
  `calibration-complete.json`, `holdout-freeze.json`, the backcast and forecast
  registries, `program-status.json`, and the plan/board.

---

## 7. Reproduction

```
python3 scripts/probes/_t1h_capentry_phase0.py                     # all four sections
python3 scripts/probes/_t1h_capentry_phase0.py --section dedup     # §1 (code profile)
python3 scripts/probes/_t1h_capentry_phase0.py --section d2        # §2 (needs data profile 'ercot')
python3 scripts/probes/_t1h_capentry_phase0.py --section d3        # §3 (code profile)
python3 scripts/probes/_t1h_capentry_phase0.py --section legb      # §4 (code profile)
```

Zero solves; numpy + pandas only (pandas for the EIA-860 rows in §2 and the
per-zone re-measurement in §4.3; every other section is stdlib + numpy). The
probe reads only committed artifacts and committed constants, asserts the
shipped allocator reproduces the committed ledger before reporting any
counterfactual, and hard-fails if `STORAGE_TECHS` capex drifts from this
finding's basis.

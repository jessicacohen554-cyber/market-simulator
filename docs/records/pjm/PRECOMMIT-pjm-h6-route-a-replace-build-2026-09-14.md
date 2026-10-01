# PRECOMMIT (pjm-h6) — Route A REPLACE: the BUILD, its phase-0 gates, and the screen it earns

**Session** `pjm-h6` · **ISO** PJM · **Date** 2026-09-14 · **Base** `origin/main` @ `75f0e456`
**ZERO LP IN THE PARENT** (rule 32 `[R-SHARD]` (a)). Everything below is
`run_calibration.run_year(fleet_only=True)` on the keeper bundles' own `meta.json` recipes,
artifact reads and code audits — the rule 29 `[R-SCREEN]` clause-0 path.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**

Chartered by `docs/PRECOMMIT-pjm-h5-coal-committed-charter-2026-09-13.md` §4 (the ex-ante
rule-19 REPLACE decision) and §10a (**OWNER RULING 2026-09-14**: *"If structural integrity
improves but gates regress that may still be a keeper"*), whose revised recommendation is
**build and solve Route A (REPLACE, applied to ALL classes)**. Everything the charter refuses
stays refused: the coal-only form is still not available as a rule-14 substitution (§2, §4).

This document is written **before any solve** and carries every number the lane will cite.

---

## 1. WHAT WAS BUILT — ONE FIELD, TWO COUPLED HALVES

`ScenarioConfig.committed_band_measured_basis: bool = False`.

| half | seam | what it does |
|---|---|---|
| **(a)** | `offer_curves.apply_committed_band_measured_basis`, called from `run_calibration.run_year` **last** among the offer-curve transformations | every covered class's `committed` multiplier := that class's own measured `avg_committed_p50` from `data/raw/reference/<iso>_campd_marginal_hr_summary.csv` |
| **(b)** | `fleet.campd_tranche_fuel_frac`, gated from `assembly.py` | a coal `_committed` tranche returns `1.0` — the gas-keyed supply passthrough sigmoid is removed from that band **only** |

**They are ONE mechanism and the flag arms both** (rule 19 `[R-ONE-MECH]`). Half (b) sits
**after** the fuel-free `_mustrun`/`_sync` returns and **before** every committed-band fuel
modifier (the three take-or-pay discounts, the SRMC bound), so nothing can scale the block and
the identity in §3 is structural rather than incidental. `econ*`/`peak` keep the sigmoid.

**Applied to ALL classes, non-selectively** (rule 1 `[R-STRUCT]`, charter §2(i)): CC_REGULAR,
CC_CHP, CT_CHP, CT_PEAKER, CT_INTERMEDIATE, ST_GAS and all five COAL classes. A class outside
the row map, absent from the artifact, or whose `committed` band is non-numeric is **neutral**
— the same rule-24 generic fallback `gas_offer_margin_markup_mult` uses for an absent `phys_*`
key. An ISO with no artifact is a no-op.

**RULE 21 `[R-DOF]` — ZERO free parameters, nothing chosen, nothing swept.** The operand is
fixed by the convention already committed in `pipeline/backcast_config` (*"committed →
avg_committed_p50"* — the same column every registered `phys_committed` key reproduces byte for
byte), and each ISO's artifact carries one row per class (for COAL a single `COAL` row, PJM
n=65). The measured operands read back from the artifact, in full:

| CC_CHP | CC_REGULAR | COAL (all 5 classes) | CT_CHP | CT_PEAKER | ST_GAS |
|---:|---:|---:|---:|---:|---:|
| 1.359 | 1.015 | **0.916** | 1.163 | 1.049 | 1.006 |

**Guard:** `--committed-band-measured-basis` with `--coal-perplant-offer-level` is a hard
error. ERCOT-144 strips `COAL_*` out of `offer_curve_by_group` and owns the same rows, so half
(a) would reach no coal class while half (b) still dropped the sigmoid — a torn mechanism, not
a composition.

### 1.1 WHERE IT IS ARMED, AND A DEVIATION FROM THE BUILD INSTRUCTION, STATED

The prompt directs arming PJM through `iso_configs._pjm_config.default_scenario_overrides`.
**That site would arm nothing**, and the codebase says so in place: the calibration lane never
applies `default_scenario_overrides` — `iso_configs.apply_iso_scenario_overrides` has exactly
one caller, `runner.run_scenario_iso`, the forecast front-end, while `run_calibration.run_year`
builds its config through `pipeline/backcast_config` and solves through `pipeline.solve`. The
same conclusion is recorded at `backcast_config.py` for `pjm_interface_feed_admissibility_gate`
(pjm-169): *"ARMED HERE, in the BACKCAST recipe, and NOT in
`iso_configs._pjm_config.default_scenario_overrides` … arming there would have recorded the
flag and changed nothing, which is precisely the caiso-162 defect class."*

The other available site — a `(iso.upper() == "PJM")` default in `backcast_config` — is
**refused for this mechanism**, because unlike pjm-169's gate it is *not* inert: it would arm
the arm inside the incumbent keeper's own replay and move its cache key, so the keeper would no
longer reproduce.

**So the field is default-OFF everywhere and the arm is requested PER RUN on the CLI**
(`--committed-band-measured-basis`, with `--no-` reaching the pre-arm posture and keeping its
key). The prompt's *intent* — PJM only, shared default False, every other ISO and every keeper
byte-identical — is met exactly, and verified mechanically:

```
check_cache_key_registration --base origin/main
  ok: 1 new field(s), all registered: committed_band_measured_basis
  ok: 846 ScenarioConfig fields, 301 registered … all resolve; 301 declared defaults all
      match HEAD; 305 solve-surface names across 7 module(s), all declared
```

If the owner promotes it, the promoted bundle's `meta.json` carries
`committed_band_measured_basis: true` and every replay reproduces it — the recorded config
carries the **substituted curve as well as the boolean** (the ercot-115 recording-gap lesson),
so an armed and a control bundle can never record identical curves.

## 2. PHASE 0 — THE GATES, MEASURED THROUGH THE REAL FIELD, ZERO LP

`scripts/probes/_pjm_h6_replace_gates.py`: twelve `fleet_only` rebuilds (control + arm × six
years) on the keeper bundles' own recipes (2020-2022 → `pjm_d4_4_TP`, 2023-2025 →
`pjm_d4_4_A`), diffing the assembled P0 objective array `mc_base` row for row. One declared
simplification, inherited from pjm-h4 §2 where it was verified rather than asserted:
`pjm_da_virtual_bids=False`, self-cancelling because both legs of every diff carry it.

### G-1 CONFINEMENT — **PASS, all six years**

276 of ~2,981 rows move; **band `committed` ONLY**; groups exactly
`{CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS}`; row count, `unit_id` order and `pmax`
identical in every year.

### G-2 IDENTITY — **PASS, all six years, at MACHINE PRECISION**

The arm's defining claim: the effective committed basis equals the measured value **in every
hour**. Max deviation **3.0e-13 … 1.1e-12** across the span, measured three independent ways:

| leg | what it measures | max dev |
|---|---|---:|
| (a) | tranche multiplier vs the measured value | **1.1e-16** |
| (b) | the passthrough, pointwise and sibling-free | **~1e-13** |
| (c) | the `_mustrun` cross-check (54 rows, 11,934 MW) | **2.2e-16** |

Leg (a) resolves each plant's supply class through the model's **own** `_offer_curve_for_group`
(a coal generator's `efficiency_bin` is the generic `"COAL"` for every supply, so reading the
registered multiplier off it silently picks the generic row for a bituminous plant). Every one
of the **64 of 64** coal committed rows moved by exactly `measured / registered` **for its own
supply class** — 0.916/0.548 ×48, 0.916/0.512 ×13, 0.916/0.684 ×3.

Leg (b) is deliberately **not a regression**. An earlier draft fitted `mc ~ a + b·fuel`, and
that fit is **degenerate on the 12 plants whose delivered coal price is flat** (a constant
regressor is collinear with the intercept, so `lstsq` returns the minimum-norm split and the
"basis" it reports is meaningless). Recorded because it is exactly the failure a reader should
be able to rule out. The replacement is pointwise: where the row's fuel price **moves**, the
finite difference `Δmc/Δfuel` must equal the tranche heat rate in every hour pair; where it is
**flat**, `mc` must be exactly constant across all 8760 h (the sigmoid is keyed to **gas**, so a
live one moves `mc` even at a flat coal price).

**The control, over the same rows, carries a pointwise passthrough of `[0.6933, 2.1000]`** — the
sigmoid is live and spans a 3× range. That is what REPLACE removes from this band, and it is
measured rather than asserted.

### G-3 MAGNITUDE — **reproduces the charter's PRE-REGISTERED values to +0.0000 in EVERY year**

Capacity-weighted `Δ$/MWh`, coal `committed` band, 12,550 MW:

| yr | **measured** | charter §3.1 pre-registered | diff | all-coal | **whole fleet** |
|---|---:|---:|---:|---:|---:|
| 2020 | +12.6296 | +12.6296 | **+0.0000** | +3.2105 | +0.8326 |
| 2021 | +7.8450 | +7.8450 | **−0.0000** | +1.9942 | +0.6069 |
| 2022 | +5.1848 | +5.1848 | **+0.0000** | +1.3180 | +0.5533 |
| **2023** | **+17.6561** | +17.6561 | **+0.0000** | +4.4882 | +1.1616 |
| 2024 | +16.8422 | +16.8422 | **+0.0000** | +4.2813 | +1.1068 |
| 2025 | +12.0271 | +12.0271 | **+0.0000** | +3.0507 | +0.8638 |

The **whole-fleet** column is LARGER than the charter's REPLACE fleet column (2023: +1.1616 vs
+1.0657) and that is the expected signature, not a discrepancy: the charter measured REPLACE
applied to **coal only**, this arm is the **non-selective all-class** form §10a directs. The
coal columns are identical to four decimals, which is the check that the two are the same
mechanism. Non-coal committed movement, 2023: CC_CHP +8.14 (614 MW), CT_CHP +7.31 (203 MW),
CT_PEAKER +1.42 (3,529 MW), CC_REGULAR +0.29 (28,818 MW), ST_GAS +0.15 (624 MW).

## 3. THE SCREEN — 2023, AND WHY IT CARRIES A CONTROL LEG

**Screen year 2023**, pre-registered in charter §6 on the mechanism's own measured footprint
(221.6, the largest of the six), **not** on the residual (the biggest residual is 2020, which
ranks third on footprint). Not re-picked here.

### 3.1 G-DRIFT — the audit, and the ONE hunk I cannot classify INERT

Keeper `git_sha` **`f09eddbe`** → HEAD **`75f0e456`**: 19 non-merge commits touch
`src/market_sim`, the two runners, `scripts/lib`, `data/raw/_validation-source` and
`data/raw/reference`. Classification:

| commit(s) | verdict for PJM's backcast | reason |
|---|---|---|
| `48fb84df` D-2 capacity vote, `dfc55e47` C3c precision/recall | **INERT** | scoring/diagnostics, not the solve path |
| `8e88c3dd`, `71f7b1d1` shard seeds | **INERT** | matrix data + `scripts/lib/mech_matrix.py` |
| `0c0d2305`, `26737620`, `8852b917`, `d02541a7`, `0acedb7e` | **INERT** | NYISO-gated fields, default-off, absent from PJM's recipe |
| `10bf4e62`, `49d5bba4`, `b3212c7f` | **INERT** | MISO-gated, default-off; `b3212c7f` states the arm is forecast-path only |
| `5e6d3224` MISO 2020/21 hub LMP | **INERT** | another ISO's validation reference |
| `760012f7` EIA-860 vintage cache keying | **INERT** | keys caches on the active directory; no vintage selection moves for a PJM backcast |
| `b385f3f3`, `706aa547` `unit_outage_window_hour_grain` threading | **INERT** | default `None`; the second is the STOP-THE-LINE repair of the first, and its own measurement is "byte-inert for every existing config: no ScenarioConfig value moves, no cache key changes" |
| `26f8508b` PS→`OTHER` / `classify_plant` | **INERT on the model side** | its own measurement, re-verified by pjm-h4 step 1: "zero dominant-class flips reach a gas class"; the model's `gmModel` is unchanged in both PJM run payloads |
| `model/lp/model.py` (memory lifetime fix) | **INERT** | its own comment: "the LP, its optimum and every extracted dual are bit-identical" — a pure `del`/lazy-rebuild change around `h.run()` |
| **`9398000d` SOCO-15 COD ramp at the LP unit's own grain** | **CANNOT ESTABLISH INERT** | it changes `effective_cod` / `monthly_online_mask` → `generator_online_mask`, a **model-side availability array**, and `cod_ramp_enabled` is **True** on the PJM keeper's config. The pjm-h5 charter classified it INERT **for the BENCH only** and said so explicitly: *"`9398000d` DOES move the model side, so it is live for a future re-solve."* I could not turn that into an INERT verdict for PJM's 2023 dispatch at zero LP. |

**Consequence, per rule 29 `[R-SCREEN]` (b): form 4 is NOT established, and the LIVE hunk earns
a control solve — for the years the screen needs, i.e. 2023 only.** So the screen is an **A/B in
ONE shard**: control and arm, both at the same pinned HEAD sha, 2023, ~36 min.

This is strictly more informative than the audit would have been. The control leg does double
duty: `arm − control` is the mechanism (both legs at one sha, so no drift can enter it), and
`control − committed keeper sidecars` **measures the HEAD drift itself** — the number the audit
could not produce. Neither bundle is registered; both are throwaway probes (clause 2), and
every number this lane will cite from them lands in the RESULT doc.

### 3.2 THE GATE — pre-registered, STOP-ONLY, never read on the residual

Charter §7, unchanged. The arm proceeds past the screen only if ALL hold:

* **G-1 confinement** — only `committed` rows move. *(Already PASS at phase 0, six years.)*
* **G-2 identity** — effective committed basis == measured to < 1e-6 in every hour. *(Already
  PASS at phase 0, six years, at 1e-13.)*
* **G-3 sign/magnitude** — the dispatch response has the direction and order of magnitude §2's
  pre-solve delta implies; COAL_BIT energy **falls**.
* **G-4 no load-bearing flip** — no **non-target** load-bearing criterion (C1 on another class,
  C2, C3a, C3b) crosses PASS → FAIL.
* **G-CTRL** — **form 4 is VOID** per §3.1; the control is the screen's own 2023 control leg.

The gate may **kill** the arm and may **never promote** it, and it is never read on the target
residual.

## 4. EXPECTED, REPORTED, GATING NOTHING (charter §5)

Dearer coal at min load pushes COAL_BIT energy **down**. Against the keeper's own scored C1
(band ±8.00 TWh) that **helps 2020 / 2022 / 2023** and **hurts 2021 / 2024**:

| yr | COAL_BIT residual | dearer coal → | headroom before FAIL |
|---|---:|:--|---:|
| 2020 | **+22.83** | helps | already FAIL |
| 2021 | −3.71 | **hurts** | 4.29 TWh |
| 2022 | +3.05 | helps | — |
| **2023** (gated) | +2.10 | helps | — |
| **2024** (gated) | **−1.13** | **hurts** | **6.87 TWh** |
| 2025 | +8.40 | helps | ungated (preliminary 923 vintage) |

**The real exposure is 2024** — the arm's two largest perturbations of all six years land on the
two gated training years (2023 +17.66, 2024 +16.84 $/MWh), which carry the *smallest* residuals.
Under the owner's 2026-09-14 ruling a regression there is **reportable, not disqualifying**; it
will be reported at full magnitude, and rule 14 `[R-ACCURATE]` forbids reverting an accurate
input to recover it.

## 5. WHAT IS NOT TOUCHED

* The **coal-only** form stays refused as a rule-14 substitution (charter §2/§4).
* The **econ/peak `gas_mid` re-centring** (charter §9: live 3.40 vs derive-at-HEAD 7.08 vs
  model-consistent 4.58) stays **ESCALATED, not settled in-lane** — inside the owner-declared-
  closed pjm-142 frontier. REPLACE settles it for the `committed` band only, by removing the
  sigmoid from that band entirely.
* Standing escalations carried forward unchanged: the PS-net-inclusive `OTHER`
  `gas_foldin_deflation` operand; the EIA-930 PJM 2021 `net_gen` corruption; the display-stale
  `volErr`/`nonFosErr` in the PJM 2021/2022 run payloads.
* The two pre-existing parity REDs (`caiso279_ablate_dswcouple_span`, `soco15_spp_arm`) are
  neither PJM's nor touched here.

## 6. DOF LEDGER ENTRY (rule 21 `[R-DOF]`)

**Zero new free parameters.** The mechanism installs only values read from a frozen, committed
measured artifact, through a column fixed by pre-existing registered convention, applied
non-selectively to every class that artifact covers. `TIER_TAGS` records it as a **structural
gate (1)**, on the criterion `miso_coal_night_floor` states verbatim — *"the LEVEL it applies is
measured per plant from a frozen artifact, so the flag carries no free number."*

Nothing here is swept. Any value chosen **between** a registered multiplier and its measured
one would be the fitted adder rules 1/13 forbid, and is refused.

## 7. RULES

Rule 1 `[R-STRUCT]` (non-selective by construction; §4's direction reported and gating nothing;
§3.2's gate is structural and STOP-only) · rule 14 `[R-ACCURATE]` (the measured artifact is
preferred and a regression is a root cause to chase, never a reason to revert) · rule 19
`[R-ONE-MECH]` (the two halves are one mechanism; the `coal_perplant_offer_level` collision is a
hard error) · rule 21 `[R-DOF]` (§6) · rule 24 `[R-REGISTRY]` (one `ScenarioConfig` field, one
CLI flag, recorded in `meta.json` and `run_config.json` with its substituted curve) · rule 25
`[R-ISO-SCOPE]` (default off for every ISO; no other ISO's key moves; verdicts enter other
shards as `U`) · rule 28 `[R-MECH-MATRIX]` (base row + a cell line in all nine shards, this PR)
· rule 29 `[R-SCREEN]` (clause 0 phase 0 above; clause (b) G-DRIFT; screen year pre-registered
on footprint) · rule 31 `[R-RETAIN]` (nothing deleted) · rule 32 `[R-SHARD]` (a) (the parent ran
no LP) · rule 34 `[R-SHARD-PROMOTABLE]` (the span shard pushes its bundle, all six registered
years).

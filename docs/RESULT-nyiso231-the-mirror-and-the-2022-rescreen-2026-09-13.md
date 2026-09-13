# RESULT — nyiso-231: the question nyiso-230 left open is **answered**, the mirror is repaired, and the 2022 screen is re-run from scratch

**Session** nyiso-231 · **ISO** NYISO · **Date** 2026-09-13 · **DATA PROFILE: nyiso**
**Pre-registration** `results/calibration/PRECOMMIT-nyiso231-mirror-repair-rescreen.md` (+ Addendum A,
the span's prediction), pushed before the arm was launched. Gate scorer
`scripts/probes/nyiso231_screen_gates.py`, committed with the PRECOMMIT and before the arm's numbers
existed. **Keeper `2026-09-12-nyiso229-hourgrain-span` UNCHANGED unless §6 says otherwise.**
**Rule 32 `[R-SHARD]` (a): the parent ran ZERO LP.**

---

## 1. THE SETTLEMENT — the LP priced against `Capital_Hudson 8.4431`; `run_config.json` recorded `7.0563`

nyiso-230 stopped its 2022 screen and recorded, honestly, that it **did not know which anchor the LP
had priced against** — and that its arm's +5.470 $/MWh was therefore not attributable. That question
is now closed, at zero LP, by three independent lines.

**(a) The code path, read end to end.** `scripts/run_calibration.run_year` takes **no config
object**: its signature carries no `config` / `scenario_config` parameter and `run_calibration_full`
passes it kwargs only. `recorded_cfg` appears in `run_calibration_full.py` at exactly two places —
the block that builds it and `write_run_config`. **It never reaches the solve.** Inside `run_year`
the sole setter of `gas_hub_basis_overlay` is ~line 1960, the zonal-vintage resolution is ~2572, and
the fleet is not built until ~3676 / ~3791, so the anchors the fleet reads were resolved on a config
carrying the overlay. Inside `_recorded_config` the order was **inverted**: mirror ~5194, overlay
~5338. `meta.json` records the solve kwarg `gas_hub_basis_overlay = True`, which line ~5947 forwards
to `run_year`, so both halves were armed and only their ordering differed.

**(b) The numeric re-derivation, on the arm's own committed config.**

| | Upstate_West | Capital_Hudson | Lower_Hudson | NYC | Long_Island |
|---|---:|---:|---:|---:|---:|
| `overlay=True` — what `run_year` resolves | **5.3731** | **8.4431** | **8.4431** | **6.6631** | **8.4431** |
| `overlay=False` — what the mirror resolved | 3.9863 | 7.0563 | 7.0563 | 5.2763 | 7.0563 |
| the arm's `run_config.json` | 3.9863 | 7.0563 | 7.0563 | 5.2763 | 7.0563 |

The recorded config is **internally inconsistent** — `gas_hub_basis_overlay: true` beside anchors
that reproduce only at `overlay=False`, to 0.0000. That inconsistency *is* the proof: the numbers
were computed before the flag was set. (This reproduces nyiso-230's bisect exactly; it is recomputed
here rather than cited.)

**(c) Corroboration from the LP's own marginal costs**, `hourly/unit_hourly_2022.parquet` (`mc`),
both legs committed. Implied `markup_hr = (mc_arm − mc_ctl) / Δanchor_zone` over 3.35 M gas
unit-hours whose fuel did not switch, against the registered curve's own
`markup_hr = base_HR × max(0, mult − phys)`:

| hypothesis | median implied ÷ nearest registered markup | share within ±10 % |
|---|---:|---:|
| **A — LP used 8.4431** | **0.9812** | **58.73 %** |
| B — LP used 7.0563 | 1.1089 | 28.27 % |

A is twice as consistent. **Corroboration, not proof, and the limit is stated:** per-unit `mc` is
`HR_unit × (mult − phys) × Δanchor` and `HR_unit` is not separately observable, so the two
hypotheses differ by a global scalar this statistic can weigh but not resolve. (a) and (b) resolve
it; (c) agrees.

**What follows, at full magnitude.** This is the **FFR-2E** class (rule 24 `[R-REGISTRY]`): the
bundle misreported what it solved. `plan_reuse_solved` keys on
`_recorded_config(...).cache_key()`, so a `--reuse-solved` chain off that bundle would have matched
on an anchor no solve used — a second-order consequence worth naming because it is silent.
And **nyiso-230's +5.470 $/MWh is now attributable** — to the FULL predicted anchor delta, not 70 %
of it — although it stays a reported number and never a gate.

## 2. THE REPAIR — one resolver, fused to the return, so the ordering is structural

`run_calibration_full.mirror_solve_year_gas_anchors(cfg, cfg_year, hours, *, iso_vintage,
zonal_vintage)` is now the only place the record's copy is computed, and `_recorded_config` ends with
`return mirror_solve_year_gas_anchors(...)`. Both inline blocks are **deleted, not zeroed**
(rule 26 `[R-DELETE]`).

**Why fused to the `return` and not merely moved down.** Moving the block to the bottom fixes today's
bug and leaves the trap armed: the natural place to append a new `if flag: recorded_cfg = …` is the
end of the function, which is precisely how the overlay got in front of the mirror in the first
place. Fused to the return, an appended block necessarily lands *above* the resolution. Positional
correctness becomes structural correctness.

**Guard** — `tests/unit/data/test_recorded_config_gas_anchor_mirror.py`, 12 tests: `_recorded_config`
has exactly ONE `return`, it is the LAST statement of the body, and it is this call; neither deleted
alias (`_f4_gs`, `_f5_zonal`) survives; the repaired mirror reproduces §1(b)'s 8.4431 table on the
arm's own config; re-resolving on the output is a no-op; the two vintage gates refuse to stack; the
off path returns the config object unchanged.

**The sibling is fixed in the same change, because leaving it would have created a NEW drift
vector.** `gas_offer_margin_anchor_vintage` (PJM's F4, pjm-169) carried the identical mis-ordered
mirror **and** gated in `run_year` on the **kwarg alone**, while the shared mirror gates on
kwarg-**or**-field. `replay_keeper.py --set` writes the FIELD and never the kwarg, so a `--set` A/B
would have solved the CONTROL while recording an armed anchor — undetectable from the bundle.
`run_year` now gates on kwarg-or-field and stamps the field it resolves, matching the zonal block.
**PJM is told** (`docs/calibration-log/governance.md` 2026-09-13) and **no PJM cell was edited**
(rule 28: a lane edits only its own ISO's shard); PJM's `R` verdict stands on its own S4
coal-displacement evidence, which this repair does not bear on.

**Blast radius, audited rather than asserted.** Every committed `run_config.json` in the repository
was checked: **exactly ONE** carries either vintage flag armed — nyiso-230's screen arm. Both fields
sit in `_CACHE_KEY_OPTIONAL_FIELDS` at their frozen `"False"` default, so **zero cache keys move**
and every keeper in every ISO is byte-identical. `tests/unit` fails the **same 7** tests before and
after (verified by stashing): `test_caiso_st_gas_peak_measured` ×1,
`test_fleet::test_neiso_includes_mystic_cc`, `test_capacity::test_unregistered_iso_is_none`,
`test_export::TestExportScenarioJson` ×4 — all pre-existing at HEAD, none NYISO's, reported and not
touched. `ruff format` + `ruff check` clean under `uv run`; both runners GREW (7434 → 7452,
14189 → 14258), so no shrink and rule 27 `[R-PUSH]` is satisfied, with both pushed blobs
hash-verified against local.

## 3. TWO OPEN OBJECTS CLOSED AT ZERO LP

### 3.1 Massena 54592's "200 % of plant" is REDUNDANT BOOKKEEPING, not an energetic defect — RETIRED

nyiso-229 handed this forward as *"the cleanest new object this phase 0 found"*: an `eia923_netzero`
fallback row (`NET0-923`, 104.1 MW at 100 % of plant) stacking on the real CAMPD row (`001`, 44.0 MW,
also 100 %), two distinct unit ids each claiming the whole plant, reachable by neither
`unit_outage_window_hour_grain` nor `unit_outage_per_unit_clip`.

**Measured over the whole committed NYISO extract** (`campd-unit-outages-perunitmerithour-NYISO.csv`):
all **30** `eia923_netzero` rows are at `unit_pct_of_plant = 100.0` for `duration_days = 365.0`, so
each alone drives its plant-year's availability to exactly 0. Only **TWO** plant-years in the entire
extract carry both a netzero row and a detected row — **54592 (2022)** and **50368 (2025)** — and in
both the per-unit shares sum to exactly 200 %. The applier clips at
`np.clip(1.0 − v, 0.0, 1.0)` (`src/market_sim/data/outages.py:1570`), so 200 % floors at availability
**0.0**, the same value the netzero row produces alone.

**Verified empirically, not just from the code:** in BOTH the arm and the control,
Massena 54592's 2022 LP rows show `cap_mw` **0.0000 in every hour** and `mw` **0.0 MWh**. The plant
is fully dark either way. At 50368 in 2025 the netzero row is in fact *adding accurate information*
rather than duplicating — `CT1`/`CT2` are 50 % each and their detected windows cover only Jan–Apr and
Oct–Dec, so the netzero row is what darkens the summer the detected rows miss. (50368/2025 is
verified by construction; the keeper bundle's slim committed set carries no `unit_hourly`, so no
empirical check is available there.)

**Object retired rather than handed on.** Noted in passing, not chased: 15 of the 30 netzero rows are
dated **2026** — inert for a 2022–2025 backcast, but a forward year sitting in a backcast extract,
which a hindcast reading 2026 would consume.

### 3.2 `ST_GAS`'s stale cross-reference is a stale *derivation input*, not a stale comment

`_NYISO_OFFER_CURVE`'s `ST_GAS` block states its basis as *"the CC class's own defensible reach ratio
(CC econ_high **1.21** / native CC marginal 0.925 = 1.31×)"* — citing a `CC_REGULAR.econ_high` the
**same file** records as removed (1.21 → 1.00, the rule-25 `[R-ISO-SCOPE]` de-leak of an
ERCOT-borrowed value).

| | reach ratio | ST_GAS centre = 0.830 × reach | registered `econ_low` |
|---|---:|---:|---:|
| **cited** (CC 1.21) | 1.3081× | **1.0857** | 1.08 |
| **current** (CC 1.00) | 1.0811× | **0.8973** | 1.08 |

**The registered 1.08 matches the CITED construction to 0.2 %.** That is what makes this more than a
documentation defect: the number was evidently *derived from* the reach that has since been removed,
so the de-leak should have propagated to `ST_GAS` and did not. On the current reach the same
construction gives **0.8973**, and `ST_GAS` therefore sits **20.4 % above its own stated
construction**. Re-centring the same thin monotone spread gives committed 0.8724 / econ_low 0.8973 /
econ_high 0.9388, which moves `markup_hr` **econ_low 2.6535 → 0.7143** (−73 %) and
**econ_high 3.2054 → 1.1764** (−63 %); committed stays clipped at 0 (phys 1.104 > bid) and `peak`
4.20 is untouched, being a $-cap wall rather than the reach construction.

**Direction, and why it is NOT co-armed.** Cheaper `ST_GAS` runs more — it under-runs **1.38 TWh** in
2024 — and `CC_REGULAR` gives up share, which is the C1-2024 direction. But it pushes price **down**,
which is wrong for C3a-2025 (−8.9 %). It acts on the same phenomenon as the anchor gate (the gas
offer level), so rule 19 `[R-ONE-MECH]` sequences it **after**, re-measured against whatever the
anchor gate leaves. It is the top of NYISO's queue once this lane's gate is adjudicated.

## 4. OFFICIAL KEEPER NUMBERS, re-scored this session

`python3 scripts/calibration_verdict.py results/calibration/nyiso229_hourgrain_span` —
**NOT-YET**, grade **6 of 8**, fails **2**.

* **C1 FAIL, one cell:** 2024 `CC_REGULAR` model **37.193** vs actual **34.060** — **+3.13 TWh**
  against a ±4.05 TWh band (**the volume leg PASSES**) and **share_pp 3.05** against ±3.0 pp (the
  share leg misses by **0.05 pp** = 60.3 GWh = **0.162 %** of the class). 2024 deficits:
  `CT_PEAKER` −1.62, `ST_GAS` −1.38, `ST_CHP` −0.14 TWh; `CC_CHP` +0.78.
* **C3c FAIL:** 0 h / 0 h / 2 h against 10 / 13 / 42 actual hours > $300.
* **PASS:** C2, C3a (**+2.5 / +3.3 / −8.9 %**), C3b (0.122 / 0.174 / 0.169 ≤ 0.20), C4, C6, C8.
* Because C1 also fails, C3c loses lone-failure status and the rule-22 `[R-C3C]` standing rule stays
  silent — **closing C1-2024 alone returns NYISO to CALIBRATED with C3c ledgered.**
* Corroborating the phase-0 slope story on a statistic nobody tuned: **D-A diurnal amplitude
  54.9 → 49.0 → 38.9 %** of measured as delivered gas rises across 2023 → 2024 → 2025.

## 5. THE STRUCTURAL CASE FOR THE (ZONE, YEAR) COMPOSITION, measured

PRECOMMIT Addendum A, pre-registered before the span. `Δanchor(zone, year)` **does not factorize**:
if it were `f(zone)·g(year)` the cross-zone ratio would be year-invariant, and the measured
`Upstate_West / Capital_Hudson` ratio is **0.7356 (2022) · 0.2518 (2023) · 0.2778 (2024) ·
0.2691 (2025)**. The zone *ordering* also flips — NYC's Δ exceeds Capital_Hudson's in magnitude in
2023 (−0.7446 vs −0.5480) and is smaller in 2024 (−0.6743 vs −1.1077). So neither
`gas_offer_margin_zonal_anchor` (zone only, year averaged away) nor
`gas_offer_margin_anchor_vintage` (year only, zone averaged away) can reach the right level. That is
the argument for the composition made on the measurement rather than on tidiness, and it is new this
session.

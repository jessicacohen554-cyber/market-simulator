# PRECOMMIT — nyiso-231: the mirror is the defect, the repair is record-only, and the 2022 screen is re-run from scratch

**Session** nyiso-231 · **ISO** NYISO · **Date** 2026-09-13 · **DATA PROFILE: nyiso**
**Keeper `2026-09-12-nyiso229-hourgrain-span` UNCHANGED. Nothing promoted, nothing registered.**
**Rule 32 `[R-SHARD]` (a): the parent runs ZERO LP.** Pushed before the arm is launched.
Gate scorer `scripts/probes/nyiso231_screen_gates.py`, committed with this document and
before the arm's numbers exist.

---

## 0. What this session settles, and what it spends

nyiso-230 built `gas_offer_margin_zonal_anchor_vintage`, screened it on 2022, and **STOPPED** on
G-CONF and G-PRED — with the cause localised to its own recorded-config mirror and **one question
left explicitly unanswered: which anchor did the LP actually price against?** That question is
answered here at ZERO LP (§1), the mirror is repaired (§2), and the screen is re-run from scratch
on the repaired recorder (§4–§6). nyiso-230's gate JSON is **not** re-read to rescue its arm
(rule 29 `[R-SCREEN]`).

## 1. THE SETTLEMENT — the LP priced against `Capital_Hudson 8.4431`; `run_config.json` recorded `7.0563`

Three independent lines, none of them a solve.

**(a) The code path, read end to end.** `scripts/run_calibration.run_year` takes **no config
object** — `inspect.signature` carries no `config` / `scenario_config` parameter, and
`run_calibration_full` passes it kwargs only. `recorded_cfg` is referenced in
`run_calibration_full.py` at exactly two places: the block that builds it, and
`write_run_config` (formerly line 6960–6961). **It never reaches the solve.** Inside `run_year`
the only setter of `gas_hub_basis_overlay` is line ~1960 and the zonal-vintage resolution is at
~2572, with the fleet built at ~3676 / ~3791 — so the anchors the fleet reads were resolved on a
config carrying the overlay. Inside `_recorded_config` the order is INVERTED: the mirror at
~5194, the overlay at ~5338. The asymmetry is the whole defect.

**(b) The numeric re-derivation, on the arm's own committed config.** `meta.json` records the
solve kwarg `gas_hub_basis_overlay = True`, which line ~5947 forwards to `run_year`. Running
`zonal_gas_anchors_for_year` on the arm's recorded config:

| | Upstate_West | Capital_Hudson | Lower_Hudson | NYC | Long_Island |
|---|---:|---:|---:|---:|---:|
| overlay **True** (what `run_year` resolves) | **5.3731** | **8.4431** | **8.4431** | **6.6631** | **8.4431** |
| overlay **False** (what the mirror resolved) | 3.9863 | 7.0563 | 7.0563 | 5.2763 | 7.0563 |
| the arm's `run_config.json` | 3.9863 | 7.0563 | 7.0563 | 5.2763 | 7.0563 |

The recorded config is **internally inconsistent**: `gas_hub_basis_overlay: true` beside anchors
that reproduce only at `overlay=False`, to 0.0000. That inconsistency IS the proof — the numbers
were computed before the flag was set.

**(c) Corroboration from the LP's own marginal costs** (`hourly/unit_hourly_2022.parquet`, `mc`,
both legs committed). Implied `markup_hr = (mc_arm − mc_ctl) / Δanchor_zone`, over 3.35 M gas
unit-hours whose fuel did not switch, against the registered curve's own
`markup_hr = base_HR × max(0, mult − phys)`:

| hypothesis | median implied ÷ nearest registered markup | share within ±10 % |
|---|---:|---:|
| **A — LP used 8.4431** | **0.9812** | **58.73 %** |
| B — LP used 7.0563 | 1.1089 | 28.27 % |

A is twice as consistent. Corroboration, not proof: per-unit `mc` is `HR_unit × (mult − phys) ×
Δanchor`, and `HR_unit` is not separately observable, so the two hypotheses differ by a global
scalar that this statistic can only weigh, not resolve. **(a) and (b) resolve it; (c) agrees;
G-REPRO (§6) makes it falsifiable.**

**Consequences, stated rather than minimised.** This is the **FFR-2E class** (rule 24
`[R-REGISTRY]`): the bundle misreports what it solved. The `--reuse-solved` planner keys on
`_recorded_config(...).cache_key()`, so a reuse chain off that bundle would have matched on the
wrong anchor. And **nyiso-230's +5.470 $/MWh IS now attributable** — to the FULL predicted anchor
delta, not to 70 % of it — though it remains a reported number and never a gate.

## 2. THE REPAIR — one shared resolver, fused to the return, so the ordering is structural

`run_calibration_full.mirror_solve_year_gas_anchors(cfg, cfg_year, hours, *, iso_vintage,
zonal_vintage)` is now the **only** place the record's copy is computed, and `_recorded_config`
ends with `return mirror_solve_year_gas_anchors(...)`. Both inline blocks are **deleted, not
zeroed** (rule 26 `[R-DELETE]`).

Why fused to the `return` rather than merely moved down: a future `if flag: recorded_cfg = …`
block appended at the natural place then lands **above** the resolution and is therefore covered.
Positional correctness becomes structural correctness. Guard:
`tests/unit/data/test_recorded_config_gas_anchor_mirror.py` (12 tests) pins that
`_recorded_config` has exactly ONE `return`, that it is the LAST statement of the body, and that
it is this call; that neither deleted alias (`_f4_gs`, `_f5_zonal`) returns; that the repaired
mirror reproduces §1(b)'s 8.4431 table on the arm's own config; that re-resolving on the output
is a no-op; that the two vintage gates refuse to stack; and that the off path returns the config
object unchanged.

**The sibling is fixed in the same change, because leaving it would create a NEW drift vector.**
`gas_offer_margin_anchor_vintage` (pjm-169 F4) carried the identical mis-ordered mirror. It also
gated in `run_year` on the **kwarg alone**, while the shared mirror gates on kwarg-**or**-field —
so a `replay_keeper.py --set` arm would have recorded an armed anchor the solve never resolved.
`run_year` now gates on kwarg-or-field and stamps the field, matching the zonal block. **Audited
over every committed bundle: exactly ONE `run_config.json` in the repository carries either
vintage flag armed — nyiso-230's screen arm — so no keeper and no registered run moves, and both
fields sit in `_CACHE_KEY_OPTIONAL_FIELDS` at their frozen `"False"` default, so zero cache keys
move.** PJM is told in the calibration log and the matrix: nothing is armed on the sibling
anywhere (PJM's cell is `R`), so this was a latent seam, not an incident.

**Test posture.** `tests/unit` at HEAD fails **7** tests before this change
(`test_caiso_st_gas_peak_measured` ×1, `test_fleet::test_neiso_includes_mystic_cc`,
`test_capacity::test_unregistered_iso_is_none`, `test_export::TestExportScenarioJson` ×4) and the
**same 7** after — verified by stashing. None is NYISO's and none is this lane's to fix; they are
recorded here rather than absorbed. This change adds 12 passing tests and repairs one assertion
in `test_gas_offer_zonal_anchor_vintage.py` that pointed at the deleted inline block. `ruff format`
+ `ruff check` clean under `uv run`. Both runners GREW (7434 → 7452, 14189 → 14258 lines): no
shrink, rule 27 `[R-PUSH]` satisfied.

## 3. G-DRIFT — form 4 is valid; the keeper's committed bundle is the control (rule 29(b))

`git diff d0b04c8 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference`
returns **EMPTY**: zero committed solve-path change since nyiso-230's arm. The only solve-path
delta is **this session's own**, and it is classified:

| change | classification | reason |
|---|---|---|
| `run_calibration_full._recorded_config` → shared mirror | **INERT** | `recorded_cfg` reaches `write_run_config` and nothing else (§1a). Write-only: it cannot move an LP. |
| `run_calibration.run_year` ISO-level gate → kwarg-or-field, stamps the field | **INERT for NYISO** | `gas_offer_margin_anchor_vintage` is `False` in both kwarg and field on both legs, so the branch does not execute. |
| the two test files | **INERT** | not on the solve path. |

The control's own `git_sha` `59589db1` **does not resolve** — its shard branch is gone, rule
33(d)'s hazard realised for the second NYISO bundle running — so the audit is anchored on
`d0b04c8`, which **does** resolve, and composed with nyiso-230's already-recorded audit of
`control → d0b04c8` (all five hunks INERT, the one shared `plant_taxonomy` PS/WAT hunk verified
on NYISO's own registry as ERCOT-only with zero `PS` rows). Recorded honestly as a composition,
not as a single clean diff.

## 4. THE ARM — control, screen year, and why it is still 2022

* **Control: `results/calibration/nyiso229_arm_y2022`** — the committed 2022 touchpoint folded to
  the keeper. Rule 29(b) form 4; no control solve is spent.
* **Screen year: 2022**, unchanged and chosen on **FOOTPRINT, never on residual** — `|Δanchor|`
  4.5385 for 2022 against 1.6556 / 1.1077 / 0.5480 for 2025 / 2024 / 2023. It is the year the
  mechanism's own measured footprint is largest, which is rule 29's test.
* **Arm: `results/calibration/nyiso231_arm_y2022`**, the control recipe plus
  `--gas-offer-margin-zonal-anchor-vintage` and nothing else.
* The shard **captures the runner's stdout+stderr to `<bundle>/solve.log` and commits it.** That
  artifact is what G-ANCHOR-LOG reads, and its absence is what left nyiso-230 unable to answer
  §1's question from its own bundle.

## 5. THE PREDICTION, fixed here before the solve

**(a) Per-zone anchors the arm must resolve AND record** — §1(b)'s `overlay=True` row:
`Upstate_West 5.3731 · Capital_Hudson 8.4431 · Lower_Hudson 8.4431 · NYC 6.6631 ·
Long_Island 8.4431`, against the frozen table `2.0346 / 3.9046 / 3.9046 / 2.7612 / 3.9046`.
`Δanchor = +3.3385 / +4.5385 / +4.5385 / +3.9019 / +4.5385`.

**(b) Per-tranche offer shift**, `= base_HR × max(0, mult − phys) × Δanchor_zone` $/MWh, from the
registered curve as recorded in the control bundle. `markup_hr`:
`CC_REGULAR` committed 0 (clipped) / econ_low 1.2887 / econ_high 0.5822 / peak 0 ·
`CC_CHP` econ_high 0.9575, all others clipped · `ST_GAS` econ_low 2.6535 / econ_high 3.2054 /
peak 33.9648 · `CT_PEAKER` committed 6.0566 / econ_low 4.0497 / econ_high 4.0855 / peak 35.8380.

| zone | Δanchor | `CC_REG` econ_lo | `ST_GAS` econ_lo | `CT_PEAK` committed | `CT_PEAK` peak |
|---|---:|---:|---:|---:|---:|
| Upstate_West | 3.3385 | +4.302 | +8.859 | +20.220 | +119.645 |
| Capital_Hudson | 4.5385 | +5.849 | +12.043 | +27.488 | **+162.651** |
| Lower_Hudson | 4.5385 | +5.849 | +12.043 | +27.488 | +162.651 |
| NYC | 3.9019 | +5.028 | +10.354 | +23.632 | +139.836 |
| Long_Island | 4.5385 | +5.849 | +12.043 | +27.488 | +162.651 |

Every `markup_hr ≥ 0` and every `Δanchor > 0`, so **every predicted 2022 shift is ≥ 0**: the arm
can only raise gas offers this year. The Capital_Hudson column reproduces nyiso-230's phase-0
table (+5.85 / +12.04 / +27.49 / +162.65) exactly, so this is the same arithmetic, not a new one.

## 6. THE GATES — five, all STRUCTURAL, all STOP-ONLY, none reading C1 / C3a / C3b / C3c

| gate | test | STOP if |
|---|---|---|
| **G-CONF** | exactly `{gas_offer_margin_zonal_anchor_vintage, gas_offer_margin_anchor_by_zone}` move, plus the ONE named waiver below; recorded anchors == §5(a) to 1e-6 | any other field moves, or any anchor misses |
| **G-ANCHOR-LOG** | `solve.log` carries `gas offer margin ZONAL anchors VINTAGE 2022:` and its five numbers match §5(a) to 5e-4 | the log is absent, or the SOLVE PATH resolved something other than §5(a) |
| **G-SCOPE** | every band multiplier, every `phys_*`, all four `peak` bands, `econ_low_share`, `pct_peaking` bit-identical | any moves |
| **G-DEMAND** | served demand identical to 4 dp; `dump == 0` | either fails |
| **G-REPRO** | this arm's P1 load-weighted LMP reproduces nyiso-230's arm to ≤ 0.01 $/MWh | it does not |

**The ONE waiver, named exactly and narrowly:** `miso_import_sil_measured_envelope`
`None → False`. The field did not exist when the control's config was serialized and now
materialises at its dataclass default; it is MISO-only and at `False`. **Any other field, and any
other pair of values for this field, still STOPS** — including any other `None → default`.
nyiso-230 recorded this as a failure rather than waiving it, which was right there and is
pre-registered here.

**G-PRED is REPLACED, not re-cut, and the replacement was chosen on measurement.** nyiso-230's
G-PRED divided the RECORDED anchors by the prediction, which made it a restatement of G-CONF —
one defect therefore failed two gates. The obvious repair, measuring the offer shift from the
LP's own `unit_hourly.mc`, was **built and rejected here before the solve**: P1's `mc` is the BID
cost (base plus the amortized startup markup keyed on P0's run pattern), so it is not the offer.
Measured on nyiso-230's arm: **6.44 % of 4,309,920 gas unit-hours carry a NEGATIVE mc delta**
where every predicted shift is `≥ 0`, and **only 7.7 % of 492 gas units have an hour-CONSTANT
delta** where the identity says all must. P0's `mc`, which would be clean, is not persisted by any
runner flag. G-ANCHOR-LOG reads the solve path's own resolution instead, which is the quantity
G-PRED was trying to reach.

**Deliberately NOT gated, and for the reason nyiso-229 had to withdraw a gate:** any non-gas
class's `mc`, and any class's generation. A changed gas offer legitimately re-prices a coal
committed tranche through a changed P0 pattern — measured on nyiso-230's arm as one unit,
**1,416 of 236,520 coal unit-hours, +3.12 $/MWh mean**. The NYISO LP is intertemporally and
globally coupled, so out-of-footprint movement is guaranteed. Conservation is gated on SERVED
DEMAND only.

**Disclosure that weakens no gate but must be on the record:** settling §1 required measuring the
arm's `mc` deltas, so this session has SEEN the implied-markup numbers. That is why no gate is
specified as a tolerance on them — a threshold chosen after seeing the statistic is not a
pre-registration. The five gates above are all exact identities or exact set-equalities.

## 7. DECLARED EX ANTE — reported, never gated

2022 delivered gas (8.4431) sits **above** the frozen anchor (3.9046), so the arm **raises** gas
offers and 2022 prices **rise**. nyiso-230 measured +5.470 $/MWh (67.6573 → 73.1275); G-REPRO
requires that number back. C3a-2022 was **−16.6 %**; +5.47 against an 81.12 actual is about
**−9.8 %**. **None of that is a gate**, in either direction (rule 1 `[R-STRUCT]`: a screen that
reads the target residual is fitted-mechanism selection done one year at a time).

## 8. IF THE SCREEN CLEARS — the span, and what it is not

ONE shard, ONE `--year 2022 2023 2024 2025` invocation, ONE bundle, years sequential inside it
(rules 16 `[R-ALLYEARS]`, 32(b) `[R-SHARD]`, 34(c) `[R-SHARD-PROMOTABLE]`: NYISO's registered year
set is exactly those four). The shard pushes its bundle including `dispatch/<year>_P1.parquet`
(rule 34(a)) so a promotion costs zero re-solves. The screen bundle is **never registered** and
its year is re-solved inside the span. Phase 0's predicted span effect — bias collapsing toward
the −1.2766 intercept, the 12.2 pp spread → ~2 pp — is a PREDICTION whose collinearity caveat
stands, and **C1 will be scored alongside C3a/C3b before any flip is reported.**

## 9. RULES

1 `[R-STRUCT]` — no band multiplier moves in any year; the price direction is declared ex ante
and is not a gate; the gate G-PRED replaced it is replaced on measurement, and the replacement
reads no residual. 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — the same measured quantity at its own
vintage; the repair makes the RECORD accurate, which is rule 14 applied to the bundle itself.
16 `[R-ALLYEARS]` — no span, no keeper claim. 19 `[R-ONE-MECH]` — one identification point; the
two vintage flags refuse to stack; the `ST_GAS` stale-reference object is **not** co-armed.
21 `[R-DOF]` / 24 `[R-REGISTRY]` — zero free parameters, and §1 is a rule-24 recording defect in
this lane's own build, reported at full magnitude with its `--reuse-solved` consequence named.
25 `[R-ISO-SCOPE]` — nothing transferred; PJM is told, not copied. 26 `[R-DELETE]` — the inline
mirrors are deleted, not zeroed. 27 `[R-PUSH]` — Opus edits to `scripts/run_*`; both files grew.
28 `[R-MECH-MATRIX]` — NYISO's cell checked (`O`, reserved for this lane) and re-stamped in this
session. 29 `[R-SCREEN]` — phase 0 first at zero LP; screen year on footprint; gates and their
scorer pushed before the solve; nyiso-230's gates NOT re-read to rescue its arm. 30(c) — a 2022
result cannot certify or decertify NYISO. 31 `[R-RETAIN]` — nothing deleted; the promotion
question is asked before this session ends. 32 `[R-SHARD]` — the parent runs no LP.
33 `[R-SHARD-ARCHIVE]` — shards archived once their bytes are fetched and verified, recovery
pinned by full SHA. 34 `[R-SHARD-PROMOTABLE]` — every shard pushes its bundle with its
`dispatch/` layer.

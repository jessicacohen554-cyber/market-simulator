# FFR-3R — the record-provenance defect class, closed structurally

**Date:** 2026-08-04 · **Branch:** `claude/ffr-3r-record-provenance-33wnf0` ·
**Base:** `origin/main` @ `a7966013` · **Lane:** record-only (no solve, no score, no
promotion, no keeper movement)

---

## 0. Summary

Four lanes each independently found one instance of a single defect: a run record field
sourced from the CLI `args` namespace rather than from the `ScenarioConfig` the solve
actually ran on. Each was patched key-by-key with its own explanatory comment, which is
precisely what made `run_capacity_hindcast.py`'s meta dict a patchwork whose correctness
is per-key and maintained by prose.

This lane closes the **class**:

* **A census** of every record-artifact field across every runner and registration/
  attestation writer, with a verdict per field (§2). It found **instance five** — and it
  is worse than args-sourced: `register_forecast_baseline.py` recorded three
  config-describing keys from **hardcoded literals** mirroring the shipped defaults.
* **A structural fix** (`scripts/lib/run_record.py`, §3): a record's config-describing
  block is *declared* as a `RecordSpec` and *built from the solved config*, with a short
  allowlist of genuinely args-sourced keys, each carrying its reason.
* **A test that fails on instance five** (§4): it rebuilds the historical FFR-3D/FFR-3L
  sourcing and shows it FAILS while the shipped sourcing PASSES, plants a new
  config-named key and shows the undeclared-key rule catches it, and carries a static AST
  lint with its own negative control.
* **An honest statement of what the existing record is worth** (§5), per key, with the
  affected artifact lists and whether any published verdict depended on it. No committed
  artifact was retro-edited.
* **An explicit list of what was NOT audited** (§7).

**Proof it is record-only.** `cache_key(ScenarioConfig())` = `603c2498bf71d21d` before and
after, as are all six per-ISO 2023 backcast keys (`ERCOT df386bca96a1d288`,
`PJM 9834b2018b598423`, `CAISO a9afddae291525c1`, `MISO 2a1252c3acae89e9`,
`NYISO fd15030b3ee60f11`, `NEISO 5b1633171fead559`) — measured by stashing the diff and
re-running. `git diff origin/main -- src/` is **empty**: not one line of the model changed.
No keeper moved.

---

## 1. The scoping distinction

`args` → `ScenarioConfig` is what a CLI is **for** and is not the target.
`scripts/run_calibration_full.py` alone has ~50 `"key": args.x` entries that BUILD the
config; that is config *construction*.

The defect is exclusively in the **RECORD**: any artifact written to describe what a run
did — `meta.json`, `run_config.json`, a registration sidecar, an attestation — whose value
is read from `args` (or from a literal) instead of from the solved config object. Nothing
below touches construction.

---

## 2. The census

Verdicts: **DIVERGENT-NOW** (a committed record is or can be wrong today) ·
**FRAGILE** (cannot diverge at HEAD, but only because no flag/coercion currently
disagrees) · **DELIBERATE** (genuinely not a config property; args-sourced on purpose).

### 2.1 `scripts/run_capacity_hindcast.py` — `meta.json` (the site of all four instances)

| Field | Sourcing at session start | Verdict | Action |
|---|---|---|---|
| `iso` | `args.iso.upper()` | FRAGILE | → `FromConfig` |
| `variant` | `config.hindcast_fuel_variant` | ok | → `FromConfig` (alias documented) |
| `energy_only_floor` | **`bool(args.energy_only_floor)`** | **FRAGILE** | → `FromConfig(market_design_retirement_floor)` |
| `entry_lookahead_reprice` | `config` (FFR-3D fix) | ok | → `FromConfig` |
| `retirement_rule` | `config` (FFR-3L fix, 2026-08-04) | ok | → `FromConfig` |
| `limited_foresight_dispatch` | **`bool(args.limited_foresight_dispatch)`** | **FRAGILE** | → `FromConfig` |
| `capacity_market_clearing` | `resolve_…(config, iso)` (FFR-2E fix) | ok | → `Derived` (resolution now *checked*, not asserted by comment) |
| `capacity_market_clearing_by_iso` | `config` | ok | → `FromConfig` |
| `capacity_clearing_posture` | `_clearing_posture` (from args) | **DELIBERATE** | KEPT + `_assert_posture_consistent` |
| `capacity_market_clearing_forced` | `bool(args.capacity_market_clearing)` | **DELIBERATE** | KEPT (see below) |
| `correlated_forced_outage` | `config` (FFR-3D fix) | ok | → `FromConfig` |
| `entry_screen_diagnostics` | **`bool(args.entry_screen_diagnostics)`** | **FRAGILE** | → `FromConfig` |
| `entry_vre_capacity_revenue`, `entry_rate_limits`, `entry_commissioning_lag`, `exit_rate_limits` | `config` (FFR-2B/FFR-1D fix) | ok | → `FromConfig` |
| `renewable_elcc_curves`, `gas_price_path`, `crossover_forward_year` | `config` | ok | → `FromConfig` |
| `crossover_forward_gas_path` | `config`, nulled when inapplicable | ok | → `Derived` |
| `weather_posture` | derived from `config.crossover_solve_year_weather` | ok | → `Derived` |
| `vintage_year`, `start_year`, `end_year` | resolved locals | FRAGILE | → `FromConfig` (`eia860_vintage_year` alias documented) |
| `kind`, `crossover`, `forward_from_base`, `arm`, `base_year` | harness labels | DELIBERATE | unchanged (name no config field) |
| `holdout_freeze_active_at_launch` | governance state read at launch | DELIBERATE | unchanged |
| `cache_key`, `bundle`, `solved_years`, `bridged_years`, `leakage_violations`, `started_utc` | run outcome | n/a | unchanged |

**`capacity_market_clearing_forced` is deliberate — confirmed, and KEPT.** It records the
raw `--capacity-market-clearing` force flag, which is a different fact from the resolved
gate recorded directly above it (`config.capacity_market_clearing`, the scalar, stays
`False` in *every* posture, so the config cannot answer "which arm did the operator
pick?"). Same for `capacity_clearing_posture`: `shipped` and `forced_curve` can resolve to
the same by-ISO dict for a single-ISO posture, so the label is not recoverable from the
solve. Both are now declared `FromArgs` with written reasons — and the posture label,
which *does* make a checkable claim, is additionally passed through
`_assert_posture_consistent`, which refuses a label the solved
`capacity_market_clearing_by_iso` contradicts. An unchecked args-sourced label was the
weak point the prompt asked me to confirm rather than assume; it is now checked.

### 2.2 `scripts/register_forecast_baseline.py` — the forecast sidecar (**INSTANCE FIVE**)

| Field | Sourcing at session start | Verdict |
|---|---|---|
| `mode` | **literal `"forecast"`** | FRAGILE (true by construction for this writer) |
| `datacenter_load_path` | **literal `"mid"`** | **FRAGILE — a mirrored default** |
| `correlated_forced_outage` | **literal `True`** | **FRAGILE — a mirrored default** |
| `capacity_market_clearing` | `summary.get(…, False)` | inherits the summary's correctness |
| `iso`, `start_year`, `end_year` | summary (config-derived) | FRAGILE |
| `extra_meta` (`--extra-meta`, hand-typed JSON) | **arbitrary, unchecked** | **DIVERGENT-NOW by construction** |

This is the same class one step worse. The two literals carried the comment *"FF-1F
posture defaults resolved by forecast mode at HEAD"* — an assertion about the defaults,
not a report of the run. It cannot track a flag at all, so it fails the moment a default
flips or a control-arm flag is added. That is not hypothetical: `build_config` in the
sibling harness carries FFR-3D's verdict on exactly this pattern — *"a mirrored literal
here would have silently overridden both flips and made the signed decisions inert"*.

`--extra-meta` is the widest hole in the whole surface: a JSON blob typed on a command
line, merged verbatim into a published record. Committed CES sidecars use it to record
`federal_ces_crediting` — a real `ScenarioConfig` field asserted by hand.

**Action:** all config-describing keys now come from the run's own resolved
`ScenarioConfig` dump (`run_config.json`'s `scenario_config`, or the cache's
`config.yaml`); keys the dump cannot answer are recorded `null`, never defaulted (rubric
§4 — an unrecoverable value is *unknown*, not *assumed*). Any `--extra-meta` key naming a
config field is auto-declared `FromConfig` and must therefore **equal** the solved config:
a hand-typed claim is allowed through only when the solve agrees with it.

### 2.3 `scripts/run_full_horizon.py` — `full_horizon_summary.json`

Already solved-sourced when this lane opened (a prior lane fixed the FFR-2E instance here
— see §5.2). Verdicts: `iso`/`start_year`/`end_year`/`weather_year` config-derived but
undeclared (**FRAGILE**); `capacity_market_clearing` and `…_by_iso` correctly resolved;
`weather_posture` a build-time constant (DELIBERATE); `extra_summary` an
**arbitrary merge channel** — `run_ces_leg.py` uses it to add
`federal_ces_enabled` / `federal_ces_crediting`, both real config fields, unchecked.

**Action:** the config block is spec-built and re-asserted after the merge;
`solve_and_summarize` gained `extra_spec` so a leg driver **declares** any
config-describing key it contributes and has it verified. `run_ces_leg.py` now declares
`CES_LEG_SPEC` and builds its block from the leg's own config.

### 2.4 `scripts/run_calibration_full.py` — the backcast `meta.json`

**DELIBERATELY kwargs-sourced — audited, not changed.** This meta is by design a record of
the ~200 `solve_and_persist` KEYWORD ARGUMENTS, because `run_kwargs.build_kwargs(meta)`
reconstructs a replay from it (`--replay-bundle`, the D-2/D-4 floor reconstruction). The
*resolved config* is recorded separately, in the same bundle's `run_config.json`
`scenario_config` block, by `pipeline.persist.write_run_config` — which is
`dataclasses.asdict(cfg)` and therefore solved-sourced by construction.

That said, this file has **its own history of the same class**, patched the same way, one
key at a time: `coal_plant_monthly_pricing`, `td_loss_factor`, `ercot_zonal_gas_basis`,
`ercot_west_netload_gas_shape`, `ercot_west_gas_delivered_floor` all now read
`first_year_cfg.<field>` with comments naming the incident that forced each
("Meta-writer audit fix", "nyiso-87", "ERCOT-63 meta-writer gap fix"). A partial
structural fix already exists and is the right vehicle: `market_sim.pipeline.flags`, the
declarative `FlagSpec` registry that records each flag's `cli → dest → solve_param →
config_field → recorded_name` journey and was built for "the ERCOT-65 recorder defect
class". **One flag family (`coal`) is migrated; the rest are not.** Converging
`pipeline.flags` and `scripts.lib.run_record` is the natural follow-up (§6), but doing it
here would have meant rewriting the backcast harness in a record-only lane.

`run_config.json`'s `calibration_flags` block is kwargs-sourced too (`k: meta.get(k)`),
for the same replay reason, and sits beside the solved-sourced `scenario_config`.

### 2.5 Everything else that writes a record

| Writer | Sourcing | Verdict |
|---|---|---|
| `scripts/register_hindcast.py` | copies `meta.json` **verbatim** into the sidecar | pass-through — correctness is the harness's; fixed upstream by §2.1 |
| `scripts/register_forecast_run.py` | delegates to `RH.build_sidecar` / `RB.build_sidecar` | pass-through |
| `scripts/_ff2d_emit_run_config.py` | `hindcast` mode writes `run_config.json = {**meta, mode, hindcast}` | **the propagation channel** — see §6.1 |
| `scripts/build_dof_ledger.py`, `build_forecast_dof_ledger.py` | read `run_config.json` → `scenario_config` | solved-sourced |
| `scripts/build_status.py`, `build_manifest.py` | read the bundle's `run_config.json` / attestation | solved-sourced |
| `scripts/run_calibration.py` | writes no run record (persistence goes through `pipeline.persist`) | n/a |
| `scripts/run_foresight_ab.py`, `run_sensitivity_tornado.py`, `run_driver_battery.py` | report JSON records `start_year`/`end_year` from `args` | FRAGILE, diagnostic-only (never registered, never scored) — left as-is |
| `scripts/run_equilibrium_battery.py`, `run_isos_concurrent.py`, `run_calibration_eia930.py` | no config-describing record | n/a |

---

## 3. The structural change

`scripts/lib/run_record.py` (new). A record's config-describing block is declared once as
a `RecordSpec` mapping record key → source:

| Source | Meaning | Checked how |
|---|---|---|
| `FromConfig(field=None, cast=None, why="")` | read straight off the solved config; the key IS the field name unless `field` aliases it | equality against `getattr(config, field or key)` |
| `Derived(fn, why)` | computed from the solved config (+ pure context) — e.g. the per-ISO clearing gate, which deliberately is *not* the scalar field of the same name | equality against `fn(config, ctx)` |
| `FromArgs(why)` | the deliberate opt-in: records something the solved config genuinely cannot answer | exempt from equality; `why` is **required** (empty string raises at construction) |

Two halves, and the second is what makes it a class fix rather than a fifth patch:

1. **`spec.build(config, ctx, args_values)`** constructs the block. Every
   `FromConfig`/`Derived` value is read off `config`, so no call site gets the chance to
   reach for `args`; only declared `FromArgs` keys accept a caller-supplied value.
2. **`spec.assert_sourced(record, config, ctx)`** re-checks the *finished* record
   immediately before it is written, catching anything merged in afterwards. Three
   violation classes: a divergent value; **a record key that names a `ScenarioConfig`
   field but is in no spec**; an exemption with no reason.

> **The property guaranteed:** a key naming a `ScenarioConfig` field cannot enter a record
> — from `args`, from a literal, from a hand-typed `--extra-meta` — without someone
> deliberately declaring it. A new field recorded from `args` is caught as *undeclared*,
> not merely as *wrong*, so it fails even when it happens to match today.

Supporting pieces:

* **`as_attr_view`** — a spec checks a *persisted* config dump (`run_config.json`'s
  `scenario_config`, a `config.yaml`) exactly as it checks a live object, so committed
  artifacts are verifiable and registrars can use the same contract as runners.
* **`RecordSpec.merged(other)`** — the two "merge a dict into someone else's record" seams
  (`extra_summary`, `extra_meta`) are composed, not exempted. A clashing double
  declaration of one key raises.
* **`_assert_posture_consistent`** (in the harness) — the one args-sourced label that
  makes a checkable claim is checked for consistency with the solved config.

**No behaviour changed for any key that was already right.** The four existing
solved-sourced keys keep their exact values; their five separate comment blocks collapse
into one shared explanation plus the spec's per-key reasons. The hindcast meta's **key set
is unchanged** — this is purely a sourcing change, so a leg whose old sourcing was already
correct produces a content-identical record. (Key *order* moves: the meta is now three
labelled zones — harness labels, the solved-sourced block, run outcome. JSON key order is
not read by anything.)

---

## 4. The test, and its proof against the historical bug

`tests/regression/test_run_record_provenance.py` — 21 tests, 62 subtests, fast lane, no
solve (every config is built without solving).

**The reproduction the prompt asked for** (`TestHistoricalDefect`). A leg where the
tri-state flags are OMITTED and the shipped defaults are `True`/`"pipeline"` — asserted as
a precondition, so the reproduction cannot silently stop reproducing:

```python
legacy_record = {                        # the pre-fix sourcing, rebuilt verbatim
    "entry_lookahead_reprice": bool(None),   # bool(args.entry_lookahead_reprice) → False
    "correlated_forced_outage": bool(None),  # → False
    "retirement_rule": None,                 # args.retirement_rule → null
    "entry_rate_limits": bool(None),         # → False
}
```

* against the **old** sourcing → **4 violations, one per key**, and `assert_sourced`
  raises `SystemExit`;
* against the **new** sourcing → **0 violations**, and the record reads
  `retirement_rule="pipeline"`, `entry_lookahead_reprice=True`,
  `correlated_forced_outage=True`, `entry_rate_limits=True` — what the solve ran.

Also pinned: FFR-2E in the same frame (a PJM leg whose shipped posture resolves the gate
`True` while the raw flag is `False` — a flag-sourced record says curve-OFF and
`_curve_on` believes it); the literal-mirrored-default failure for a control-arm leg
(`correlated_forced_outage=False`, `datacenter_load_path="off"` → 2 violations); and
**instance five itself** — an undeclared config-named key is a violation *whatever its
value*.

**Static lint** (`TestStaticSourcingLint`). An AST pass over the audited writers flagging
`args.<x>` inside the value of a dict key that names a `ScenarioConfig` field — the exact
shape all four historical instances had. It carries its own **negative control**: a
planted two-key snippet reproducing instances one-through-four, which the lint must flag,
so the green is worth something.

**Audit scope is stated in the test docstring**, not silent: the lint covers
`run_capacity_hindcast.py`, `run_full_horizon.py`, `register_forecast_baseline.py`,
`run_ces_leg.py`, `register_hindcast.py`, `register_forecast_run.py`;
`run_calibration_full.py` is excluded for the reason in §2.4.

**Regression evidence:** 1,125 passed / 3 skipped over the
`hindcast|forecast|ces|posture|record|register|verdict|summary|horizon` selection of the
fast lane, plus `tests/regression/test_persisted_identity.py`,
`test_recorded_cfg_fidelity.py` and all of `tests/unit/config` (479 passed). `ruff check`
and `ruff format --check` clean.

---

## 5. What the existing record is worth

**No committed artifact was retro-edited.** Authoring a record after the fact is what
rubric §4 forbids; the deliverable is this statement.

### 5.1 `retirement_rule` — 13 committed sidecars carry `null` for a run that solved `pipeline`

**From:** 2026-08-02 (owner decision D-1 flipped the shipped default to `"pipeline"`) until
FFR-3L's fix on 2026-08-04. **Affected artifacts** (`frontend/data/hindcast/`, all with
`started_utc` 2026-08-03T21:28Z–23:59Z):

`ercot-2023-2027-crossover-ffr3a2` · `ffr3f-ercot-{PREFIX-control, capfix-control,
throughput-armed}` · `ffr3f-pjm-{PREFIX-control, control, throughput-armed}` ·
`miso-2021-2025-ffr3a2` · `miso-2023-2027-crossover-ffr3a2` · `neiso-2021-2025-ffr3a2` ·
`nyiso-2021-2025-ffr3a2` · `pjm-2021-2025-ffr3a2` · `pjm-2023-2027-crossover-ffr3a2`

Every one of them co-records `entry_rate_limits: true` from the *solved* config — the
internal tell that the flags were omitted and the shipped defaults inherited. Since D-1
(`retirement_rule → "pipeline"`) and D-2 (`entry_rate_limits → True`) were signed the same
day, a leg that inherited the one inherited the other. **These 13 legs solved
`retirement_rule="pipeline"` and recorded `null`.**

**Did a verdict depend on it? No — checked, not assumed.** The only reader of this key is
`register_hindcast.py`'s dashboard chip
(`if (m.retirement_rule && m.retirement_rule!=='legacy') arms.push('r-new '+…)`), so the
consequence is a **missing `r-new pipeline` chip**, not a changed classification. On the
scoring side: `forecast_verdict` reads exactly `iso`, `mode`, `capacity_market_clearing`,
`reserve_margin_build_enabled`, `planning_reserve_margin`, `outage_source`,
`BACKCAST_OVERLAY_FLAGS` (three gas-basis keys) and `len(sc)`. `retirement_rule` is in
none of them, and `EXPECTED_GATE_KEYS` is `("capacity_market_clearing",)` alone. **The
FFR-3A-2 T1-X sidecars' `retirement_rule: null` was read by nothing that scores.**

### 5.2 `capacity_market_clearing` — the FFR-2E instance, and where it still shows

**Hindcast lane: no committed record is wrong.** Before FFR-2E the harness default was the
flat net-CONE arm (`capacity_market_clearing_by_iso = None`), so the resolved gate equalled
the scalar flag on every pre-2026-08-02 leg. The FFR-2E fix was needed because the
*default changed*, not because past records were wrong — which is exactly what that lane's
own note says.

**T1-F lane (`run_full_horizon.py`): the defect was live and is visible in committed
artifacts.** `build_config` passes `capacity_market_clearing_by_iso` only under
`--golden-posture`, so a golden leg had scalar `False` beside a by-ISO dict carrying the
curve-ON ISOs — and the old record took the scalar. The clearest surviving pair:

| sidecar | ISO | recorded `capacity_market_clearing` | recorded `capacity_clearing_posture` |
|---|---|---|---|
| `pjm-2026-2028-ffr2e-t0-shipped` | PJM (ships curve-**ON**) | `false` | `shipped` |
| `pjm-2026-2028-ffr2e-t0-fixed` | PJM | `false` | `fixed` |

The two arms of an A/B designed to separate curve-ON from curve-OFF are **indistinguishable
on the key `_curve_on` reads**, so the FC-3 evidence rows for both were classified
identically — a wrong *classification*, not a wrong label. The FFR-2E session knew: it left
a hand-typed `note` on each sidecar explaining "run_full_horizon records the scalar,
blocker B1b". That is the pattern this lane exists to end — an artifact-level prose
annotation standing in for a fixed instrument.

**18 committed `t1f`/`ces-poc` sidecars record `capacity_market_clearing: false` for an ISO
the forecast ships curve-ON** (CAISO/MISO/NEISO/PJM), `started_utc` 2026-07-19 → 2026-08-02.
I cannot adjudicate each from committed data alone: whether a given leg was golden-posture
is not recorded in the sidecar, and the bundles are gitignored. **Treat any pre-2026-08-03
`t1f` sidecar's `capacity_market_clearing` as UNRELIABLE for curve-ON ISOs** — verify
against the leg's own `run_config.json` before citing it. The list:

`caiso-2026-2026-ff-2b-adequacy` · `caiso-2026-2030-ff-t1-gate` ·
`caiso-2026-2030-ff-t1f-baseline` · `miso-2026-2030-ff-t1f-baseline` ·
`miso-2026-2030-ffr2b-t1f-{base,dampers}` · `neiso-2026-2026-ff-2b-adequacy` ·
`neiso-2026-2028-ffr1b-t0-aging` · `neiso-2026-2030-ff-t1f-baseline` ·
`neiso-2026-2030-ffr1a-{arm1,arm2,before}` · `pjm-2026-2028-ffr2e-t0-{fixed,shipped}` ·
`pjm-2026-2030-ff-t1f-baseline` · `pjm-2026-2030-ffr1a-{arm1,arm2,before}`

### 5.3 `entry_lookahead_reprice` / `correlated_forced_outage` — FFR-3D

Priced by the owner at signature (Addendum D.3) and documented in
`docs/handoffs/ffr-3d-instrument-repair-2026-08-03.md` §2.1: every T1-H verdict committed
before that fix was scored with both forced OFF and is **legacy evidence on a superseded
posture**. That statement stands; this lane adds nothing to it beyond confirming the
sidecar record agrees (pre-fix sidecars carry `false` for both).

### 5.4 The three keys this lane fixed in the hindcast meta — **no committed record is wrong**

`energy_only_floor`, `limited_foresight_dispatch` and `entry_screen_diagnostics` are all
plain `store_true` flags passed unconditionally into `build_config`, and `__post_init__`
does not coerce the fields they land on. So `bool(args.x) == config.<field>` at HEAD for
every leg ever run: **FRAGILE, never DIVERGENT**. They are fixed because the *next*
tri-state conversion or per-ISO resolver would have made each instance six, seven and
eight — which is the whole thesis of this lane, and is precisely what happened to
`entry_lookahead_reprice` and `correlated_forced_outage` at FFR-3D's C.4(c).

### 5.5 The forecast sidecar literals — **no committed record is known wrong**

`run_full_horizon.py` exposes no `--correlated-forced-outage` / `--datacenter-load-path`
flag, so a T1-F leg cannot currently disagree with the mirrored literals: all 40 committed
`t1f`/`ces-poc` sidecars carry `correlated_forced_outage: true` / `datacenter_load_path:
"mid"`, which matches the shipped forecast-mode resolution. They were never *verified*,
only *asserted* — a distinction with no consequence yet and a guaranteed one the first time
a control arm or a default flip arrives.

---

## 6. Recommended follow-ups (NOT done here — each changes something outside a record-only lane)

### 6.1 `_ff2d_emit_run_config.py hindcast` should read `run_config.yaml`, not `meta.json`

Today it writes `run_config.json = {**meta, "mode": "forecast", "hindcast": True}`, and
`forecast_verdict._scenario_config` — seeing a top-level `iso` — treats **the entire meta
dict as the run's ScenarioConfig**. That is the channel by which a wrong meta key became a
wrong scored input (FFR-2E's whole mechanism), and it has a second edge: a config field the
meta *omits* reads as absent/False downstream. FC-2 row 4 branches on
`"reserve_margin_build_enabled" in sc`, which a ~30-key meta never contains; FC-7 row 1
scores `len(sc) >= 20` against a real dump's ~677 fields.

**The harness already writes the right artifact**: `config.to_yaml_full(out_dir /
"run_config.yaml")`, a full solved-config dump, sitting next to the meta and ignored by
this helper. Pointing FC-7 at it would close the channel entirely.

**Not done here because it is verdict-affecting**, not record-affecting: it changes what the
scorer reads and could move committed FC-2/FC-7 rows. It needs its own lane and an owner
decision on re-scoring. **This is the highest-value remaining item.**

### 6.2 Converge `pipeline.flags` with `scripts.lib.run_record`

`market_sim.pipeline.flags` already models the same journey for the backcast lane
(`cli → dest → solve_param → config_field → recorded_name`) and was built for the same
defect class ("ERCOT-65"). One family (`coal`) is migrated. The two abstractions should
meet — `FlagSpec.config_field`/`recorded_name` is exactly a `RecordSpec` entry — so the
backcast meta's kwargs record and its config record are generated from one table. Family
by family, each with its fidelity test, never a bulk rewrite (rule 27).

### 6.3 CI

The static lint is a plain pytest and runs in the existing fast lane; no workflow was
added (private repo, owner-billed runners). If it should gate PRs explicitly, extend
`.github/workflows/ci.yml` — do not add a workflow.

---

## 7. What was NOT audited (explicit)

* **`scripts/run_calibration_full.py`'s meta dict** — read in full and classified (§2.4),
  but deliberately not restructured: it is a replay-kwargs record by design, with its own
  partial structural fix in `pipeline.flags`, and rewriting it in a record-only lane would
  be exactly the "bulk rewrite of a core file" rule 27 forbids. **A residual surface
  remains there**: any `solve_and_persist` parameter not covered by the Stage-7 meta-writer
  audit could carry the same class of bug (`tests/regression/test_recorded_cfg_fidelity.py`
  states this too).
* **`scripts/archive/` and `scripts/probes/`** — the frozen calibration record, exempt from
  retrofits by the repo's own lint policy. Not read, not changed.
  (`scripts/archive/run_fom_scarcity_grid.py` does contain an args-sourced
  `"energy_only_floor"` record key; it is a retired driver.)
* **The diagnostic report writers** (`run_foresight_ab.py`, `run_sensitivity_tornado.py`,
  `run_driver_battery.py`) — classified FRAGILE in §2.5 and left as-is: their JSON is a
  local report, never registered on a dashboard and never read by a scorer. If any becomes
  a registered artifact it needs a spec first.
* **Backcast bundle contents on disk** — gitignored, so §5's claims about what a run
  *solved* rest on the code path and on co-recorded solved-sourced keys, not on reading the
  bundles. Stated as inference where it is inference (§5.1).
* **No solve was run**, so nothing here is validated against a fresh bundle end-to-end; the
  runners are exercised through their record-assembly seams with real `ScenarioConfig`
  objects.
* **Rule 28 (mechanism matrix)**: no mechanism was proposed, tested or added, and no
  `ScenarioConfig` field was created — no matrix touch is due.

---

## 8. Files changed

| File | Change |
|---|---|
| `scripts/lib/run_record.py` | **NEW** — `RecordSpec` / `FromConfig` / `Derived` / `FromArgs`, `as_attr_view`, `merged`, `check`/`assert_sourced` |
| `scripts/run_capacity_hindcast.py` | `META_RECORD_SPEC` + `_assert_posture_consistent`; meta rebuilt as three labelled zones; 3 args-sourced keys fixed, 2 kept as declared exemptions |
| `scripts/register_forecast_baseline.py` | `SIDECAR_RECORD_SPEC`, `resolved_config`, `_extra_meta_spec`; three literals replaced by the run's own resolved config |
| `scripts/run_full_horizon.py` | `SUMMARY_RECORD_SPEC`; `solve_and_summarize(extra_spec=…)`; post-merge assertion |
| `scripts/run_ces_leg.py` | `CES_LEG_SPEC`; `_leg_meta` builds from it and passes it as `extra_spec` |
| `tests/regression/test_run_record_provenance.py` | **NEW** — 21 tests / 62 subtests: the class contract, the historical reproduction, instance five, the composition seams, the static lint + its negative control |
| `docs/handoffs/ffr-3r-record-provenance-2026-08-04.md` | this document |

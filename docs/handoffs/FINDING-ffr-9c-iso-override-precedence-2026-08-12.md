# FINDING — a promoted `default_scenario_overrides` flag cannot be turned OFF by its caller

**Lane.** FFR-9C-PROMOTE `[OPUS]`, branch `claude/ffr-9c-promote-stageb-hlfnpg`,
at `origin/main` **`15261093`**. Surfaced while verifying owner card D-30's stage
B promotion; **filed, not fixed** (rules 1/13/14 — this lane measured it, it does
not adjudicate it).

**Status.** Pre-existing property of `apply_iso_scenario_defaults`. **Not
introduced by D-30.** MISO's D-29 (`miso_clean_tier_rows`) already carries it. The
stage B promotion is what makes it bite, because it promotes five flags at once.

---

## 1. The behaviour

`apply_iso_scenario_defaults` (`src/market_sim/config/iso_configs.py:1482`)
decides whether the caller "left a field unset" by comparing the caller's value
against the `ScenarioConfig` default:

```python
to_apply = {
    k: v for k, v in overrides.items() if getattr(config, k) == getattr(defaults, k)
}
```

There is no sentinel. So a caller value that happens to **equal the dataclass
default is indistinguishable from "unset"** and is overwritten by the ISO default.

Measured at this head, with stage B armed in ERCOT's `default_scenario_overrides`:

| Caller passes | Resolves to | Correct? |
|---|---|---|
| `smr_available_year=2035` (non-default) | `2035` | ✅ caller wins |
| `smr_available_year=None` (== default) | **`2030`** | ❌ silently overridden |
| `entry_pipeline_aware_signal=True` | `True` | ✅ |
| `entry_pipeline_aware_signal=False` (== default) | **`True`** | ❌ silently overridden |

## 2. Why it matters for this epoch

**After stage B is promoted, an ERCOT control arm is inexpressible through the
config path.** All five promoted flags are booleans defaulting `False` (or `None`
for `smr_available_year`), so *the OFF value is exactly the value that cannot be
requested*. An A/B that wants ERCOT with the pre-epoch posture cannot get it by
passing the flags off — it silently receives the armed posture instead.

That is sharper than it first looks, given what this epoch does. D-30 makes every
pre-epoch ERCOT hindcast sidecar non-comparable as a baseline. If the control arm
*also* cannot be re-run, then for ERCOT there is no route back to the control
posture at all through supported configuration.

The failure mode is **silent**: no raise, no warning. A future lane can believe it
solved a control arm, register the bundle, and quote the number. That is the
FFR-2E defect class (a record must report the posture it solved) reappearing one
layer up — this seam was itself the FFR-2E fix.

## 3. Scope

- Applies to **any** field promoted through `default_scenario_overrides`, in any
  ISO — not only stage B and not only ERCOT.
- Live today for MISO `miso_clean_tier_rows` (D-29) and ERCOT
  `scarcity_price_overlay`, each a single flag. Stage B raises ERCOT's count to
  six.
- Does **not** affect callers passing a non-default value; those still win, which
  is why the seam has looked correct in use.

## 4. Candidate remedies — NOT applied here

Recorded so the owner decision has options; none is taken by this lane.

1. **Sentinel-based unset detection.** Give the promotable fields an explicit
   "unset" sentinel so a caller's `False` is distinguishable from absence. Most
   correct, largest blast radius (touches `ScenarioConfig` construction).
2. **Track explicitly-set fields.** Record which fields the caller actually
   passed (e.g. a `__set_fields__` set populated at construction) and let
   `apply_iso_scenario_defaults` consult it instead of comparing values. Local to
   the seam; likely the cheapest correct fix.
3. **Fail loud instead of silent.** Leave precedence as-is but raise when a caller
   passes a value equal to the default for a field the ISO overrides. Preserves
   behaviour, kills the silent-wrong-posture class, and is the smallest change —
   but it makes control arms an error rather than making them expressible.

Option 3 is the fail-closed analogue of the FH-2 demand-growth resolver, which is
the house precedent for this shape of problem (FH-5 §7.1 filed the same class of
blocker against `full_forward_climatology_years` returning `()` silently).

## 5. Correction owed to this lane's own pre-registration

`docs/handoffs/PREREG-ffr-9c-promote-stageb-2026-08-12.md` §1.5 states:

> An ISO-level default fills only a field the caller left at the `ScenarioConfig`
> default — **an explicit caller value always wins**, so every existing invocation
> that passes these flags explicitly stays byte-identical.

The first clause is right and the emphasised claim is **wrong for default-valued
arguments**. An invocation that explicitly passes `entry_pipeline_aware_signal=False`
does **not** stay byte-identical — it silently becomes an armed run with a
different cache key. §1.5 must be corrected when the promotion commit lands, and
the byte-identity guarantee restated as: *callers passing a NON-default value stay
byte-identical; callers passing the default value are overridden.*

## 6. Measured evidence

Reproduce at this head (no solve required):

```bash
uv run python -c "
from market_sim.config.scenarios import ScenarioConfig
from market_sim.config.iso_configs import apply_iso_scenario_defaults
c = apply_iso_scenario_defaults(
    ScenarioConfig(iso='ERCOT', entry_pipeline_aware_signal=False), 'ERCOT')
print(c.entry_pipeline_aware_signal)   # -> True
"
```

Requires ERCOT's stage B rows to be present in `default_scenario_overrides`
(lane commit, not yet on `main` at the time of writing).

For the record, the promotion itself verified clean at the same head: an ERCOT leg
passing no stage-B flag resolves all five armed, the pinned default cache key
moves `062d440558103f81` → `8d9ef77edb3e44cb`, and CAISO/MISO/NYISO/NEISO/PJM all
still construct and resolve unchanged (`screens=False/False`), so rule 25 holds.

---

# RESOLUTION ADDENDUM — 2026-08-13 (OVERRIDE-FIX lane)

**Everything above is the FINDING as landed on 2026-08-12 and is left
untouched.** This section records how it was resolved.

**Lane.** OVERRIDE-FIX `[OPUS]`, branch `claude/iso-armed-flags-turnoff-e425y7`,
off `origin/main` **`016b659`**. Config-only: no solve, no dashboard
registration, no new mechanism, no keeper/marker/rubric touch.

## R1. What was applied — §4 remedy 2

`ScenarioConfig` now records which fields its caller actually passed, and
`apply_iso_scenario_defaults` consults that record instead of inferring "unset"
from the value. An ISO default fills **only a field the caller did not pass**.

- `scenarios.py` — the generated dataclass `__init__` is wrapped (post-decoration)
  to store the passed field names on a **non-field instance attribute**,
  `_explicitly_set_fields`, read through the new public
  `scenarios.explicitly_set_fields(config)`.
- `iso_configs.apply_iso_scenario_defaults` — the predicate gains one clause:
  apply the ISO default iff the field is **(a)** not in the caller's record
  **and (b)** still at the dataclass default. Clause (b) is the pre-existing
  test, retained: it still catches a config mutated after construction, and
  keeping both makes the change a **strict narrowing** — it can only apply
  *fewer* ISO defaults than before, never more.

Remedy 3 (raise) was not taken as the destination, per the dispatch: a model
whose control arm is an error cannot run the A/B discipline. Remedy 1
(sentinels) was not chartered.

**Why a non-field attribute.** `cache_key()` hashes `asdict(self)`, which walks
dataclass *fields* only. A tracking **field** would enter every cache key,
orphan every on-disk bundle and move the global pin `603c2498bf71d21d`. The
non-field attribute is invisible to `asdict`, `fields()`, `_non_default_values`
and `to_yaml_full`, so **rule 28's cache-key ledger duty does not arise** and no
`_CACHE_KEY_OPTIONAL_FIELDS` entry was added. Pickle identity is unmoved —
`ScenarioConfig` is still physically defined at `market_sim.config.scenarios`.

## R2. The copy-path hazard the remedy had to solve

On Python 3.11 `dataclasses.replace(cfg, ...)` re-invokes `__init__` with
**every** field, which is indistinguishable from a caller who set everything. A
naive record would therefore mark an entire config "explicitly set" after any
`replace`, and **every ISO default would silently stop applying** — a worse
failure than the one being fixed, and it sits directly in the production path
(`runner.run_scenario_iso` calls `with_overrides(iso=…)` and
`resolve_policy_bundle` *before* `apply_iso_scenario_defaults`).

Two-part answer:

1. **`with_overrides` is the tracked copy path** — it carries the record forward
   as the UNION of the source's record and its own kwargs. The three
   `src/` sites that used bare `dataclasses.replace` on a `ScenarioConfig` now
   route through it (`scenario_resolvers.resolve_policy_bundle`, `runner`'s
   weather-year rebind and outage-overlay `fleet_config`, plus
   `as_zero_forcing_ablation`).
2. **All-fields-supplied records `None` = "provenance unknown"**, and unknown
   **falls back to the pre-fix value comparison**. So an untracked copy (a bare
   `replace` anywhere, an unpickled config) degrades to *exactly today's
   behaviour* rather than losing its ISO defaults. The fail-safe direction is
   the conservative one.

## R3. The call site that DID depend on the silent re-arming

The dispatch predicted "expected: none". **That was wrong, and a static grep is
what made it look right.** Two scans were run:

- **Static (AST over all 2,325 `.py` files)** — every call kwarg and dict entry
  naming an ISO-overridden field with a literal value equal to that field's
  `ScenarioConfig` default. **16 hits, all benign**: `dict(...)`/
  `SimpleNamespace(...)`/`_Cfg(...)` fakes in `test_reserve_config.py` and
  `test_pipeline_kwargs.py` (not `ScenarioConfig` at all), and
  `with_overrides`/`dataclasses.replace` calls on an **already-resolved** config
  followed only by `cache_key()` or a direct assertion
  (`_arm3arm_cache_epoch.py`, `test_caiso_keeper_defaults.py`,
  `test_miso_rps_region_arming.py`, `test_negative_renewable_offers.py`). None
  flows back through `apply_iso_scenario_defaults`.
- **Dynamic differential** — the resolved value of all 15 ISO-overridden fields,
  plus the resolved `cache_key`, for **6 config entry points × 6 ISOs**
  (`ScenarioConfig` bare and forecast, `reference_config` plain and
  `--golden-posture`, `backcast_config`, `run_calibration._calibration_config`),
  captured on clean `main` and on the fix and diffed.

The dynamic pass caught what the static pass structurally could not:
**`scripts/run_full_horizon.py::reference_config`** declared
`miso_rps_compliance_regions: bool = False` and `miso_clean_tier_rows: bool = False`
and forwarded both into `ScenarioConfig` **unconditionally**. The literal is a
*forwarded function parameter*, invisible to a grep for a default-valued
argument at the construction site. Pre-fix the seam re-armed them; post-fix the
mirrored literal would have **won**, silently un-arming owner decisions **D-26**
and **D-29** in exactly the T1-F legs that runner launches — and the CLI made it
worse, since `action="store_true"` yields an explicit `False` when the flag is
absent.

This is the **FFR-3A step-0 hazard in mirror image**, and that file already
names it in a standing comment ("*a mirrored literal here would have silently
overridden both flips… If the owner ever signs an electrification default, this
line must become a None-sentinel too*"). The repair is that file's own
established idiom: both parameters became `bool | None = None` ("not passed =
inherit"), joined the `arms` dict filtered by `if v is not None`, and both CLI
flags gained `default=None`. Verified by `_arm3arm_cache_epoch.py`, which failed
on the intermediate state and returns its declared MISO poles
`cd2403cc031515db` / `9337e00504e1e72a` byte-identically after it.

**Standing lesson: for this defect class the grep is the dynamic differential,
not the static scan.** A future promotion into `default_scenario_overrides`
should re-run the differential (harness shape recorded in
`docs/handoffs/override-fix-2026-08-13.md` §5).

## R4. One deliberate new raise

Turning off **only** `capacity_screen_unified_lookahead` now raises: the ISO
override still arms `capacity_screen_scarcity_restoration` (that field is
genuinely unset), and `__post_init__` refuses restoration-without-lookahead
(FFR-8A). Pre-fix that posture was unreachable because the seam re-armed both.
The raise is the loud half of the remedy and is correct — the caller is told the
combination is untested rather than silently handed the posture it asked to turn
off. **The ERCOT screen-pair control arm is both-off**, as the dispatch stated.
Pinned in `test_iso_override_precedence.py::test_turning_off_half_the_screen_pair_RAISES`.

## R5. Byte-stability evidence

| Read | Value | Status |
|---|---|---|
| Global pinned default key | `603c2498bf71d21d` | unmoved |
| ERCOT resolved default key (D-30 armed pole) | `8d9ef77edb3e44cb` | unmoved |
| ERCOT pre-arm pole | `062d440558103f81` | unmoved |
| MISO forecast poles (D-29) | `cd2403cc031515db` / `9337e00504e1e72a` | unmoved |
| 6 entry points × 6 ISOs × 15 fields + keys | — | **byte-identical to `main`** |

`_ffr9c_stageb_cache_epoch.py` (three reads) and `_arm3arm_cache_epoch.py` both
exit 0. `test_persisted_identity.py`, `test_cache_key_default_flip_guard.py` and
`test_ercot_stageb_arming.py` pass **unchanged** — no assertion in any of them
moved, which is what §4's "wrote no test pinning the defective precedence" bought.
`check_cache_key_registration.py` exits 0 (714 fields, 167 registered).

## R6. §5's correction, now discharged

§5 above says the PREREG §1.5 claim — "*an explicit caller value always wins*" —
was wrong for default-valued arguments, and owed a correction. **As of this fix
the original claim is TRUE as written**: an explicit caller value wins,
including one equal to the field default. The corrected restatement §5 demanded
("callers passing a NON-default value stay byte-identical; callers passing the
default value are overridden") describes the **pre-fix** seam only, and is
retained above as the historical record of what shipped between PR #3888 and
this fix. The precedence comment on ERCOT's `default_scenario_overrides` block
in `iso_configs.py` has been updated in step.

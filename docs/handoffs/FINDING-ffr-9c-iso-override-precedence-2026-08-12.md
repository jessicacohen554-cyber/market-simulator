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

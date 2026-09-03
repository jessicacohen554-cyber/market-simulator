# FINDING — capx D44: the fossil announced-date channel is ARMED AS THE DEFAULT POSTURE (owner ruling Q30 executed) — one declared default flip, both cache pins advanced by design rather than by accident, every doc that carried the superseded "fossil is a default no-op" sentence amended, and one piece of harness plumbing that would have made the flip inert

**Lane:** capx D44 — the EXECUTION of owner ruling **Q30** (director sitting
r#31, 2026-09-02; capx ledger §3 Q30 / §0ab) on the capx D42 A/B. A ruled,
mechanical lane: **no measurement, no solve, no new field, no parameter value,
no keeper, no marker, rule 22 untouched.** Everything below is the flip and
what the flip made true.

**Evidence it executes:** `FINDING-capx-d42-fossil-dates-ab-2026-09-02.md` —
MISO T1-H `retire.unit_recall_gt300` **5/19 → 16/19** (PASS), every non-coal
exit class the reliability floor held at exactly 0.0 GW opens, `false_retire`
stays **0.0**, plant-grain precision of released MW **13.4 % → 98.5 %**, and
**zero** economic-screen decisions displaced in any year. D44 restates those
numbers; it did not re-derive them.

---

## 0. Verdict (one paragraph)

`ScenarioConfig.fossil_announced_exits_enabled` now ships **True**. A fossil
unit's owner-filed EIA-860 Schedule-3 planned retirement date is an exogenous,
vintage-gated step-1 input in every forecast run of every ISO; the reversal
registry is armed; the economic retirement screen decides the **residual
undated fleet**. The one licensed change is that single default. Its declared
consequence is that **both pinned cache keys advance** — default
`cedadc285f8603b9` → `4c6b03ae098b6e3e`, bare backcast
`e006dfd7cef8bedd` → `8211c72bb1960adc` — which is not a defect and not a
re-baseline to silence red: it is capx D24-R option (b′-1) doing exactly the
job owner ruling Q20 landed it for, since the frozen drop declaration stays
`False` and the armed default therefore enters the hash instead of colliding
with the pre-flip bundle. Backcast behaviour is byte-identical (the channel is
loaded only under `mode == "forecast"`), so no keeper, sidecar, determination
or dashboard row moves. Two things beyond the bare flip were needed to make it
TRUE rather than merely written, and both are reported in full below: the
**harness pinned the field to its own `False` default on every hindcast
invocation** (§4 — the flip would have been inert for the entire T1-H lane),
and **four assertions in the cache-key test surface encoded "no registered
field's default has ever flipped"** as if it were an invariant (§5 — it was a
description of an empty ledger, and D44 is the first entry). Neither is a
parameter, a mechanism, or a solve.

---

## 1. The flip

`src/market_sim/config/scenarios.py`:

```
fossil_announced_exits_enabled: bool = True   # was False
```

with the Q30 citation at the definition, and three docstring amendments in the
same file that the flip made necessary: the `forecast_fossil_retirement_economic`
docstring (which claimed fossil units are not retired on their announced date —
now scoped to "by THIS field's own route", with the limb-1b posture named), the
field's own cache-neutrality sentence (now: the drop is at the frozen `False`,
so an explicit `False` is cache-neutral and the armed default hashes
distinctly), and the `_CACHE_KEY_OPTIONAL_FIELDS` registration comment (the
registration STANDS; what changed is which value is the default, not what the
key drops at).

**The declared-defaults line** (the charter's b′-1 duty), appended — never
edited — to `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS`, whose first entry this
is:

```python
("2026-09-03", "fossil_announced_exits_enabled", "True"),
```

The frozen entry in `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` stays `"False"` and
was not touched — check 4 of `scripts/check_cache_key_registration.py` fails an
edit, and leaving it put is precisely what makes the post-flip config take its
own key. Guard clean at HEAD: *230 registered, all resolve; 230 declared
defaults all match HEAD.*

## 2. The cache-key consequence, measured

| config | before | after |
|---|---|---|
| `ScenarioConfig()` (forecast default) | `cedadc285f8603b9` | **`4c6b03ae098b6e3e`** |
| `ScenarioConfig(mode="backcast")` | `e006dfd7cef8bedd` | **`8211c72bb1960adc`** |
| `ScenarioConfig(fossil_announced_exits_enabled=False)` | `cedadc285f8603b9` | **`cedadc285f8603b9`** (unmoved) |
| same, backcast | `e006dfd7cef8bedd` | **`e006dfd7cef8bedd`** (unmoved) |
| ERCOT resolved forecast pole (D12-A armed) | `6bb61037c072502d` | **`1e1002d480fc180d`** |
| ERCOT Stage-B armed pole | `71f20d708a810f0a` | **`ef70a350ac15fd0f`** |
| ERCOT pre-Stage-B pole | `ddeb8a9aaffe1f6b` | **`11a94474a0c824e3`** |

Rows 3–4 are the point. Under the PRE-D24-R live-default rule this flip would
have been the silent same-key collision in its pure form — a post-flip armed
run served the pre-flip unarmed bundle at an unmoved key, the recurrence the
2026-08-31 cache-epoch entry records happening to the storage-entry arming.
Under (b′-1) the armed default separates and the **explicit** old value still
collapses onto the pre-flip key, so a control arm keeps its bundle. Both halves
were measured this session, not asserted.

**Cost, exactly.** A one-time cache MISS per forecast config; never a wrong
answer, because a key that moved cannot mis-serve. Committed artifacts —
sidecars, bundles, keeper shards, determinations, dashboard rows — are files,
not cache lookups, and none moves. The D42 legs are unaffected: each carried
the field explicitly.

**Recorded in three places, with dated cause blocks:** the two pins in
`tests/regression/test_persisted_identity.py`, the cache-epoch ledger in
`src/market_sim/results/cache.py` (new entry, epoch 2026-09-03), and the
per-pole narrative in `test_ercot_stageb_arming.py` /
`test_iso_override_precedence.py` (whose own literals are dated measurements
and are left as written, per that file's own convention).

## 3. The doc amendments, quoted

**CLAUDE.md, capacity-evolution step 1** — was:

> `forecast_fossil_retirement_economic` (default True ⇒ **for fossil this step
> is a default no-op**: the economic screen governs its phaseout)

now reads, in substance: *"**For FOSSIL the owner's own filed EIA-860
Schedule-3 date is honored as an exogenous step-1 input** — limb 1b,
`fossil_announced_exits_enabled` **default ON since 2026-09-02** … —
**vintage-gated** …, with the **reversal registry armed** …. Rule 19
`[R-ONE-MECH]`: a plant carrying a pending filed date is **exempt from the
economic screen**, which therefore decides only the **residual UNDATED
fleet**"*, with the D42 evidence line and the three things it does not close
(the undated cohort, the December-dated roll, genuine deferrals).

**CLAUDE.md, step 0** — the confirmed registry was described as *"**the ONLY
exogenous fossil exit channel**"*; it is now *"the **instrument-bound**
exogenous fossil exit channel"*, with a parenthetical naming Q30 and the
different admissibility class limb 1b belongs to (an owner's filed plan, not a
binding instrument).

**`model-methodology-spec.md` §5.1** — the year-loop pseudocode gains step
`1b` (the filed fossil dates, gated, forecast-only, with the screen exemption
stated in the step); step 0's "The ONLY exogenous fossil exit channel" becomes
"The INSTRUMENT-BOUND …"; and the *Confirmed vs announced retirements* prose is
rewritten into three paragraphs — the confirmed channel, then limb 1b in full
(the vintage gate as rule-13 admissibility, the verification's
defer-or-cancel-never-inject rule, zero free parameters, the (a)/(b)/(c)
reconciliation), then the superseded posture *stated as superseded* with the
reason Q30 gave (precision, not admissibility) and D42's measurement of that
precision. The closing sentence now names all three splits
(`fossil_announced_exits_enabled`, `forecast_fossil_retirement_economic`,
`confirmed_exits_enabled`).

**Code docstrings carrying the same superseded sentence**, amended in place
(code is the source of truth; leaving them would have put the code in
contradiction with the two docs above): `capacity_evolution/evolve.py` (the
step list, the step-1 comment, the limb-1b comment),
`capacity_evolution/retirements.py` (the module channel list and
`apply_announced_retirements`'s "Fossil default no-op (RC-3)" — which stays
literally true *of that function* and is now scoped that way, with limb 1b
named), `data/announced_retirements.py` (module docstring),
`data/fleet/assembly.py` (the backlog docstring) and `runner.py` (the loader
gate, where the forecast-mode restriction is now called out as the reason the
backcast is untouched).

**Mechanism matrix** (rule 28): base row `def` + `note` + `ev` re-stamped to
the armed-default posture with the Q30 citation; **MISO** `fc` **O → K**
carrying the D42 A/B verdict, its "OPEN: the owner arms or declines" line
replaced by what Q30 actually resolved and what it left open (the D32 R3 sector
gate for the undated cohort, the additions-side adequacy response, the stale
baselines); **CAISO / ERCOT / NEISO / NYISO / PJM** `fc` **U → O** — armed by
the flip, holding **no** verdict of their own. `U → K` would have been the
rule-25 violation: `K` reads "tested & accepted", and the D42 evidence is
MISO's alone. All six shards' `updated:` bumped; 237 line anchors repaired with
`--fix-anchors` (the comment additions shifted them); guard exit 0.

## 4. The harness pinned the field, so the flip would have been INERT (reported, and repaired)

`scripts/run_capacity_hindcast.py` declared `fossil_announced_exits: bool =
False` and passed `fossil_announced_exits_enabled=fossil_announced_exits`
**unconditionally** into the config. Every hindcast invocation would therefore
have passed an explicit `False` — which, by §2 row 3, is not merely "off" but
*keeps the pre-flip cache key*. The flip would have changed nothing in the
entire T1-H lane while reading as armed everywhere else, and the charter's own
consequence line ("every future forecast/hindcast solve carries the channel")
would have been false.

Repaired on the house pattern already used by seven sibling gates in the same
file (`entry_pipeline_aware_signal` is the model): the parameter becomes
`bool | None = None`, the assignment moves onto the None-drop dict (omit ⇒
inherit the shipped ScenarioConfig default), and `--fossil-announced-exits`
becomes `argparse.BooleanOptionalAction`, so `--no-fossil-announced-exits`
expresses the pre-Q30 control arm explicitly — which is also what keeps that
arm addressable at its pre-flip key.

This is plumbing for the licensed change, not a second change: no field, no
parameter, no mechanism, no default of its own. It is reported here rather than
folded in silently because it is the one edit in this lane a reader would not
predict from "flip one default".

## 5. Four test assertions encoded an empty ledger as an invariant

The flip is the first entry `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` has ever
carried, and two tests written at the (b′-1) re-baseline asserted properties
that were true *because the ledger was empty*, not because they are invariants:

* `test_cache_key_default_flip_guard.py::test_declared_defaults_parse_and_match_the_live_config`
  compared every frozen declaration against the live default. A flipped field
  must differ — that difference IS the repair. Now compares against the frozen
  entry **overridden by the newest declared flip**, which is exactly how the
  guard's own check 3 resolves it, so drift is still caught for every field. A
  new sibling test asserts the other half: a flipped field's frozen entry must
  still differ from its live default, so "syncing" the frozen entry (which
  would silently re-base the key and restore the collision) fails loudly.
* `test_cache_key_declared_default_drop.py::test_the_default_keys_are_unmoved_by_the_repair`
  pinned "hashing under the live-default rule and under the declared rule gives
  the same key for the bare config" — the (b′-1)-is-free property. With a flip
  declared, the two rules necessarily differ for the flipped field. Restated as
  of the **pre-flip day** on both sides (each flipped field put back to its
  frozen declaration, in the rule *and* in the config), which is a no-op
  substitution for the 229 unflipped fields, so nothing is weakened for them.

`TestFossilAnnouncedExits`' three gate-off legs in `test_capacity.py` now pass
`ScenarioConfig(fossil_announced_exits_enabled=False)` — the control is
explicit now, and what those legs assert (rows ignored, step 1 the fossil
no-op, byte identity) is unchanged.

Everything else was a pinned literal: 19 assertion literals across 19 files
advanced to the new pin, plus the three ERCOT poles. Where a file carried a
dated cause-block narrative, a 2026-09-03 paragraph was appended rather than
the historical literals rewritten — the convention `scenarios.py` states for
itself ("each such literal is a dated historical measurement and is left as
written").

## 6. Governance attestation

* **Scope.** One default flip, licensed by Q30. No new `ScenarioConfig` field
  (so rule 28(c) does not arise; the row exists from D42), no parameter value
  re-identified (rule 21/23 untouched), **no solve, no LP, no bundle, no
  registration, no keeper, no marker, no ISO override**. Rule 22 untouched: no
  out-of-training year was solved, scored or looked at.
* **Rule 25 `[R-ISO-SCOPE]`.** The flip arms a POSTURE, which carries no ISO's
  fitted numbers, so arming it in all six lanes is not a cross-ISO transfer of
  a MISO verdict. The verdicts stay per-ISO and the matrix says so: MISO `K`
  on its own measurement, the other five `O` — running the channel, owing
  their own.
* **Rule 27 `[R-PUSH]`.** Every file ≥300 lines was edited locally with the
  Edit tool and pushed as exact on-disk bytes; no file was regenerated
  wholesale from model output; the remote blob of each such file was fetched
  back and compared to the local line count + SHA-256 after the push (see the
  verification block in the commit series).
* **Rule 24 `[R-REGISTRY]`.** The flip is on the registry, in
  `ScenarioConfig`, declared in the b′-1 ledger, and appears in every run's
  `run_config.json` as it always did.
* **Rule 15.** No run was produced, so no dashboard registration is owed.
* **Tests.** `tests/unit` + `tests/regression`: **4,613 passed**, 10 failed —
  the same 10 that fail on unmodified `origin/main` in this `code`-profile
  container (`test_export.py` ×4, `test_soundness.py` ×6, all needing a
  hydrated `data/raw`), verified by stashing the diff and re-running. Zero new
  failures.
* **Collision (D45).** D45 runs PJM/NYISO solves. Any container it launched
  before this flip landed records the OLD (default-off) posture — a vintage
  fact for its findings, not a conflict, and its bundles are addressed at the
  pre-flip keys.

## 7. What this lane did NOT do, deliberately

* **Re-measure anything.** Every forecast/hindcast bundle solved before today
  records the superseded posture. Per Q30 that staleness joins the director's
  **batched post-repair re-measure decision** (the D41-stale bundles + the
  Q30-stale forecast baselines, one decision, priced next sitting). D44 ran no
  solve and re-registered nothing.
* **Arm anything else.** The D32 R3 sector gate — the finding's named
  structural companion for the undated cohort — is untouched and still open.
  So is the additions-side adequacy response D42 §7.4 routed (the reserve
  margin going negative in 2023/2024 before the backstop fires, and
  `add.by_tech.gas_ct` PASS → FAIL): that is the additions lane's object, and
  Q30 arming the exits does not settle it.
* **Take the per-ISO route the measurement recommended.** D42 §7.5 recommended
  arming for MISO via `default_scenario_overrides`. Q30 ruled the broader form
  — a global default flip — and this lane executed the ruling, not the
  recommendation. The difference is recorded here and in the MISO matrix cell
  so nobody later reads the finding's recommendation as what happened.

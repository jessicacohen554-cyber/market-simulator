# PRECOMMIT — SCN-WS1c: the D-1 FLOOR repair (owner ruling S2)

**Lane:** SCN-WS1c (desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#5 am.1,
§2 ruling S2, §5), plan §7 "WS-1a" **item 1** — the item SCN-WS1a's card gate correctly
withheld. Model Fable. Branch `claude/scn-ws1c-carbon-floor-tmlmjl` (the harness assigned this
stem in place of the ledger's nominal `claude/scn-ws1c-carbon-floor-v2rk`; the file paths are
what matter). Branched off `origin/main` at `fca3b656`.

**DATA PROFILE: neiso** — and not hydrated, because **this lane runs no LP**. See §4.

**The ruling being executed.** Ledger §2, **S2 (2026-09-06): D-1 = FLOOR.**
`effective = max(RFF path(year), program trajectory(year))` on a program ISO, the path alone
elsewhere. `carbon_price` (scalar) keeps its Q26 replace semantics untouched.

**Ruled with its consequence on the record.** The RFF mid path never once exceeds a program
trajectory in any horizon year, so after this repair `policy_bundle="tight"` is an exact
**NO-OP** on CAISO, NYISO and NEISO — it stops being a cut, it does not become an increase.
That is the ruled outcome. This lane does not reach for a construction that makes `tight` "do
something" on those three ISOs; that is sub-box **D-1(b)**, still open and the owner's. **D-1(c)**
(how a federal floor composes with PJM's partial RGGI footprint) is likewise open and is not
answered here — §3 shows the repair is inert on that seam by construction, which is what keeps
it unanswered.

---

## 1. The exact change

Three edits, in one direction: `resolve_carbon_program` becomes the answer to ONE question
("what does the program itself charge"), and the composition with the RFF path happens in
exactly one place, one level up (rule 19 `[R-ONE-MECH]`).

**(a) `src/market_sim/policy/cap_and_trade.py`, the forecast branch of
`resolve_carbon_program` (`:286-291` at `fca3b656`).** Delete the nulling:

```python
    if getattr(config, "carbon_price_path", "zero") not in ("zero", None):
        price = None            # <- DELETED: this is the "replace" semantics
    else:
        named_path = ...
```

so the forecast branch unconditionally carries the projected (or `carbon_program_price_path`-
named) program price, exactly as the backcast branch unconditionally carries the measured one.

**(b) `src/market_sim/policy/carbon.py::resolved_base_trajectory_price`.** Today it returns the
program adder when truthy and only otherwise consults the path. It becomes the max:

```python
    program = float(resolution.price_adder) if resolution is not None else 0.0
    return max(program, _rff_path_price(config.carbon_price_path, year))
```

with the interpolation extracted to `_rff_path_price` (same arithmetic, same
unregistered-path-name → `0.0` fallback). `_base_carbon_price`'s stage (1) `carbon_price`
replace and `resolve_carbon_price`'s final `carbon_price_delta` stage are **untouched**.

**(c) The D34 guard, extended to the path branch.** `carbon_price_below_base_warning` watches
`carbon_price` (the scalar) and is untouched. A sibling
`carbon_path_below_program_warning(config)` is added and wired into
`ScenarioConfig.__post_init__` beside it. Under the floor it **can never fire** — it is the
invariant assertion WS-1a §6.4 named, not an expected-to-fire warning, and its test asserts
silence on `tight` for every program ISO. It costs nothing at the default (`carbon_price_path
== "zero"` returns immediately). It is a regression tripwire: the day a future edit
reintroduces a replace path, it speaks.

Also: `config/scenario_resolvers.py`'s `tight` / `rollback` bundle comments are re-read against
the repaired semantics (no field values change — see §2); `results/cache.py` gains ONE
cache-epoch entry; `tests/unit/policy/test_cap_and_trade.py:135` flips to the floor and gains
the program-ISO monotonicity test; `tests/unit/policy/test_carbon_price_below_base_guard.py`
gains the new guard's tests.

---

## 2. What the repaired semantics predict — zero LP, from committed evidence

**This lane's Phase 0 is already on `main`.** SCN-WS1a's committed
`docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json` evaluates the LIVE resolver
per ISO × bundle × year and carries, beside its `head` (HEAD) column, a **`floor` column
computed as `max(path, program)`** — the ruled formula exactly. That column IS the prediction,
pre-registered on `main` before this branch existed and before the ruling was made. It is not
re-derived here.

**The prediction, in full: 6 ISOs × 3 bundles × 25 years = 450 cells. 3 cells' worth of
trajectory move — CAISO/NYISO/NEISO × `tight`. The other 15 (ISO, bundle) series are
identical, year by year.**

| ISO | bundle | resolved path | state | 2026 | 2027 | 2028 | 2030 | 2035 | 2040 | 2045 | 2050 | vs HEAD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ERCOT | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| ERCOT | **tight** | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 | identical |
| ERCOT | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| CAISO | current | zero | True | 30.02 | 32.13 | 34.37 | 39.36 | 55.20 | 77.42 | 108.58 | 152.29 | identical |
| CAISO | **tight** | mid | True | **30.02** | **32.13** | **34.37** | **39.36** | **55.20** | **77.42** | **108.58** | **152.29** | **MOVES** |
| CAISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| PJM | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| PJM | **tight** | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 | identical |
| PJM | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| MISO | current | zero | True | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| MISO | **tight** | mid | True | 0.00 | 3.75 | 7.50 | 15.00 | 25.00 | 35.00 | 42.50 | 50.00 | identical |
| MISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| NYISO | current | zero | True | 23.64 | 25.29 | 27.06 | 30.98 | 43.45 | 60.95 | 85.48 | 119.89 | identical |
| NYISO | **tight** | mid | True | **23.64** | **25.29** | **27.06** | **30.98** | **43.45** | **60.95** | **85.48** | **119.89** | **MOVES** |
| NYISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |
| NEISO | current | zero | True | 26.05 | 27.88 | 29.83 | 34.15 | 47.90 | 67.18 | 94.23 | 132.16 | identical |
| NEISO | **tight** | mid | True | **26.05** | **27.88** | **29.83** | **34.15** | **47.90** | **67.18** | **94.23** | **132.16** | **MOVES** |
| NEISO | rollback | zero | False | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | identical |

**Read the three moving rows against their own `current` row: they are the same numbers.**
That is the ruled no-op, stated before the code runs. The magnitude of the correction is the
cut it removes: CAISO +$24.36 (2030) to +$102.29 (2050); NYISO +$15.98 to +$69.89; NEISO
+$19.15 to +$82.16 — every one an INCREASE relative to HEAD, in all 25 years, on all three.
No cell anywhere falls.

**Direction, stated as a sign law rather than a table:** `max(a, b) ≥ a`, so no config's
resolved carbon can decrease, in any ISO, in any year. The repair is monotone by construction.

---

## 3. Byte identity — the deliverable, measured not asserted

**Measured over every committed `run_config.json` in the repository (90 tracked files,
`git ls-files '*run_config.json'`):**

| posture | count |
|---|---|
| `mode=forecast`, `carbon_price_path="zero"`, `policy_bundle="current"`, `state_carbon_pricing=True` | 73 |
| `mode=backcast`, `carbon_price_path="zero"`, `policy_bundle="current"`, `state_carbon_pricing=True` | 17 |
| **carrying a non-`"zero"` `carbon_price_path`** | **0** |

**Zero of ninety committed bundles reach the changed branch.** The branch is entered only when
`mode != "backcast"` AND `carbon_price_path not in ("zero", None)` AND the ISO has a program AND
`state_carbon_pricing` is on; no committed config satisfies the second conjunct.

**No cache key moves, and the reason is structural, not incidental:** no `ScenarioConfig` field
is added, removed, re-defaulted or re-registered, and `cache_key()` is a pure function of those
fields. The 66 keys recorded in committed `run_config.json` files, asserted unchanged **by
name** (24 further bundles — the six backcast keeper bundles among them — record no `cache_key`
field; for those the claim is the same one, that no key-bearing field changed):

`706eec14f63096e8` `f129fd3720e3e874` (scn-ws1a T0 base/carbon_plus25) · `8d8bc63a0d4378a9`
`cc7d1050a8090c76` `321f04e9060787f0` (ff-t1f-d45r miso/nyiso/pjm) · `772b1e5abc7fc80c`
`873d8c0e6cab52ae` `6690e4d6d66bc819` (ff-t1f-d46 caiso/ercot/neiso) · `0c3e9cd5b5993bdf`
`18515067bf4d2fbe` `167e65187f32056b` (ff-t1f-d50 ercot/neiso/pjm) · `b1a73a087064ffd8`
`19a9690bb12c8459` (ff-t1f-d60 miso/nyiso) · `8ebed20ae90ec0e7` (ff-t1f-d65-a1/neiso) ·
`18515067bf4d2fbe` (ff-t1f-d65-ctl/neiso) · `587dc5b32ba71ceb` (ff-t1f-s123/verify) ·
`9a7f68fc7dcac931` (ff-t1f-s4hydro/neiso + control) · `31a19d815fa319a7` (ff-t1f-s6-pjm/ledger) ·
`67678e58b2d0526c` `56019f3b0850e9f9` `e84079053b581a9e` `96984c538320d6d6` (ff-t3-neiso-golden
bau-d46 + its fc6 arms) · `0365174ab16cc318` `7924eccc695c0168` `7784d408fc955785`
`1de43201e2040f7f` `13f9357712250600` `a4b11ef4aaa1be35` (bau-prera-2026-08-31 + arms) ·
`706e7ba8e6582d42` `f7cced798488ddac` `2d017ed9675aa386` `65662ca117959ee5` (bau + arms) ·
`2c8cc7d19ccaed4c` (hindcast caiso t1h-d46) · `67d5dcc1ada2e2df` `f061b2646bfaac8b` (ercot
t1h-d46/d4m) · `501b5f64b8adf8d4` `3649264ca98a1fb4` `40173304213d39cd` `eff2c890746ec966`
`6ea92547eaa62559` `c306ddc6d28c60c2` `1b0f1a5e75719b92` (miso t1h-d27/d31/d33/d46/d53×2/
d33-probe) · `313ba0612435b963` `d6c0137e37bf3200` `da19b85495178949` `07e416f3f8072e7c`
(neiso t1h-d37-armed/d45r/d46 + both crossovers) · `cad77112c804881d` `91686abe7a744a88`
`911371a8cf23d5c3` `7323dc2ddabc95c7` (nyiso t1h-d45r-curveon/d45r/d52-devintage + crossover) ·
`ea767a6254b8e4af` `896da48960560a29` `c6091bd5b62bbc3f` `f0e050e820c1159a` (pjm
t1h-d45/d45r-fixed/d45r/d57-clearing) · `c3592c1adbc8ac17` `277e96c45549a70e` (scn-ws2a NEISO T0
ref/target) · `eed460b6ddfaab1c` `c3592c1adbc8ac17` (scn-ws0-smoke neiso CARB/REF) ·
`d88c8585e76f2935` `075e6aa30813f061` `383509581661faba` (scn-ws2-ladder ercot BAU/CES-20/
CES-40) · `0d6f2710f8dedf56` (tests/golden ercot_2026_2040).

Keeper bundles, by name, all `mode=backcast` / `carbon_price_path="zero"`: CAISO
`caiso251_arm_nomargin`, ERCOT `ercot248_two_config_keeper`, MISO `miso217_intermphys_B`,
NEISO `neiso99_joint_B`, NYISO `nyiso192_astoria_panel`, PJM `pjm_debugb_inputclock_A`.

**Backcast is untouched on a second, independent ground:** the changed branch is the `else`
arm of `if config.mode == "backcast"`. Even a hypothetical backcast config with a non-`"zero"`
path never entered it and still does not.

**D-1(c) stays unanswered, by construction.** `carbon_mc_column` — the only per-generator
membership seam — is gated on `program.zone_share is not None`, which is PJM alone, and reads
`resolution.price_adder`. PJM's forecast `price_adder` is `projected_price(...)` over a
`STATE_CARBON_PRICE_BY_ISO` that has no PJM key (`['CAISO','NYISO','NEISO']`), i.e. `0.0`
before and after this change. So the seam returns the scalar, the identical object, exactly as
today. The federal floor composes with PJM's partial footprint nowhere in this diff.
`policy/constraints.py` reads only `resolution.cap_spec`, and the mass-cap row path returns
before the adder branch — untouched.

---

## 4. STOP gate (rule 29 `[R-SCREEN]` — structural, STOP-only, zero LP)

**No LP is spent.** The change is a resolver; its evidence is arithmetic over committed
trajectories plus the cache-key list. Rule 29's clause (0) applies with nothing left over: the
zero-LP phase 0 answers the whole question, so no arm reaches a screen solve and rule 29(c)
DELETE-BEFORE-MERGE has no bundle to reach. If any of the three gate rows below fails, the
branch stops and the FINDING reports the failure — it does not proceed to a solve to "check".

| # | gate | pass condition | if it fails |
|---|---|---|---|
| **G1 direction + magnitude** | the live resolver after the change equals the committed `floor` column | all 450 (ISO × bundle × year) cells equal `docs/handoffs/scn-ws1a/phase0-carbon-trajectory-2026-09-05.json`'s `floor`, to the cent | STOP — the implemented formula is not the ruled formula |
| **G2 footprint** | the change touches program ISOs under a non-`"zero"` path and nothing else | exactly the 3 × 25 cells CAISO/NYISO/NEISO × `tight` differ from the committed `head` column; the other 375 are bit-equal | STOP — the footprint is wider than the ruling |
| **G3 byte identity** | no zero-path bundle's key or resolved trajectory moves | `cache_key()` identical before/after for the default config and for one config per ISO × bundle; 0 of 90 committed run_configs on the changed branch | **stop-the-line**, not a footnote |

None of the three reads a residual, a price level, or a fit statistic. The gate can kill the
change; it promotes nothing.

**Also required to pass, as ordinary correctness rather than a screen gate:** the full
`tests/unit/policy/` suite green, and `ruff` clean.

---

## 5. Test-assertion change, declared here rather than discovered later

The charter says "add the NEISO-tight strict-increase test over 2026–2050". **That test as
written would fail, and it would be right to fail:** under the floor, `tight` equals `current`
on NEISO in every year, so the increase is weak (`≥`), not strict. The assertion this lane
writes is the one the repaired semantics actually make:

* `tight ≥ current` in every horizon year on **every** ISO — the monotonicity law of `max`;
* **equality** on CAISO / NYISO / NEISO at the RFF mid path, in all 25 years — the ruled no-op;
* a **strict** increase on ERCOT / PJM / MISO from 2027 on, where the path alone applies
  (2026 is 0.00 on both bundles: the RFF mid knot at 2026 is 0);
* and `tight ≥ HEAD` everywhere — no cell falls.

A test rewritten to match a result is normally the thing to refuse. The reason this one is
legitimate is that **the ruling moved the predicate before any code ran**: the charter's
sentence was written under the open card, and S2's own recorded consequence ("an exact no-op on
CAISO/NYISO/NEISO") is the statement that `>` is false and `≥` is true. The assertion follows
the ruling, not the output.

---

## 6. Deliverables

PRECOMMIT (this doc, pushed first) · the repair as one commit with its tests · the cache-epoch
entry · `docs/handoffs/FINDING-scn-ws1c-2026-09-06.md` · plan §5.1 + ledger §3 Carbon row 1 ·
the `carbon_price_path` + `policy_bundle` **cells** re-stamped in all six matrix shards as the
LAST commit, after `git fetch origin main` + rebase (the base rows exist — SCN-WS1a minted
them; they are not re-minted).

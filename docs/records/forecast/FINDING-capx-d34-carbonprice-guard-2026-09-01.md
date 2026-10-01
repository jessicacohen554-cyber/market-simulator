# FINDING — capx D34: `carbon_price` keeps replace semantics and gains a loud below-base guard (owner ruling Q26); R4 is CLOSED

**Session:** D34 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-d34-carbonprice-guard-lfpeld`. **Date:** 2026-09-01. **HEAD at launch:**
`5083e29e` (origin/main). **Charter:** execute owner ruling Q26 (r#26 amendment 1,
`docs/handoffs/capx-director-ledger-2026-08.md` §3 Q26) — keep the documented replace
semantics of `ScenarioConfig.carbon_price` and add a loud validation warning when a
forecast scenario's `carbon_price` sits below the resolved base carbon trajectory in any
horizon year. **Zero solves.**

**Headline: the guard is in, at the one seam every scenario passes through
(`ScenarioConfig.__post_init__`), and it reproduces the D23 incident exactly — a NEISO
config with `carbon_price=25` now says, out loud, that its "carbon price increase" is a
$107.16/tCO2 CUT by 2050 and points the author at `carbon_price_delta`. Nothing about
the resolution moved: no field, no default, no precedence change, and the resolver's
returned values are bit-identical with the guard silenced (tested over all 25 horizon
years, four configurations). Owner ruling Q26 CLOSES D23's R4 — `carbon_price` is
replace + guard, and no successor re-opens the semantics question without a new owner
act.**

---

## 1. Charter discipline

No `ScenarioConfig` field added, no default moved, no resolver behavior changed ⇒ **rule
28 [R-MECH-MATRIX] is NOT triggered** (no new solve-affecting mechanism, no new
`ScenarioConfig` field for `scripts/check_mechanism_matrix.py` to demand a row for, no
new calibration CLI flag). No mechanism tested, so no matrix cell is minted or moved in
any ISO shard. Zero solves; no bundle, registry sidecar, board, verdict, keeper, shard
or marker touched; no holdout year approached; no new workflow. **Cache keys are
provably unmoved** — the six per-ISO default keys at HEAD+D34 are `ERCOT
7a57fadff595ca83` · `CAISO b95366a4a5afff4b` · `PJM 8fddb635bec7a837` · `MISO
afaba226185cc162` · `NYISO b388aea81370d227` · `NEISO 44d40ffcfa9f2c59`, and ERCOT's
matches the value D26 measured at its own HEAD (that finding §1). Rule 27 [R-PUSH]
duties discharged: `scenarios.py` (15,679 → 15,701 lines) and `carbon.py` (118 → 249)
were edited locally and pushed as exact on-disk bytes, with a blob verification after
the push (§5).

## 2. The trap being closed (D23, in one paragraph)

`ScenarioConfig.carbon_price` has exactly one consumer — `policy/carbon.py::
resolve_carbon_price` — and precedence (1) there returns a nonzero value **directly**,
replacing whatever the chain would otherwise resolve. On a program ISO the chain
resolves a real, escalating trajectory: NEISO's base carries the projected RGGI
allowance price, **$26.05/t in 2026 escalating at the published 7 %/yr CCR rate to
$132.16/t by 2050** (the EM-6 seam fix). D21's `carbon25` arm therefore did not raise
the carbon price — it **CUT** it, in every single horizon year, −$1.05 in 2026 widening
to −$107.16 in 2050, and P1 measured the premise of its own pair
(`docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md` §2). D26 repaired the
*instrument* with the additive `carbon_price_delta`; Q26 repairs the *ergonomics* so the
next author cannot fall into it silently.

## 3. The guard

**Seam.** `ScenarioConfig.__post_init__`, immediately after the `carbon_price_delta`
rule-13 forecast-only guard — the validation site every construction path
(`__init__`, `replace`/`with_overrides`, `from_yaml`, CLI kwargs, sweep members) passes
through, and it fires **once per construction**, never per year and never per hour. The
import of the detector is deferred (`policy.carbon` imports `config.scenarios`) and is
reached only on the rare nonzero-override path, so every other construction pays
nothing.

**Detector.** `policy/carbon.py::carbon_price_below_base_warning(config) -> str | None`.
It returns `None` — silent — when `mode != "forecast"`, when `carbon_price` is unset or
zero, or when the override is at or above the base trajectory in every horizon year.
Otherwise it returns the message quoted in §4. The horizon is `start_year`/`end_year`
when set, else `START_YEAR`/`END_YEAR` (2026/2050), the same resolution
`runner.run_full_horizon` applies. `__post_init__` emits it as a `RuntimeWarning` with
`stacklevel=2`, the house pattern the `from_yaml` unknown-key warning already uses.

**It is a WARNING, never an error.** Q26 verbatim: guard, not semantics change. A
deliberate below-base study remains entirely legal — it just cannot be silent.

**It complements D26's premise assertion; it does not duplicate it.** The two catch the
same defect at different seams and for different audiences.
`check_forecast_invariants.carbon_pair_premise` (D26) is the *scoring-time* assertion —
it compares two ARMS' resolved signals and refuses to score P1 on an inverted pair, so
it protects the paired-instrument verdict and only fires where a paired battery runs.
The D34 guard is the *construction-time* observation — it compares ONE config against
its own base trajectory, so it reaches every forecast scenario anyone writes, paired or
not, battery or not, and it fires before a solve rather than after. Neither subsumes the
other; a below-base single-arm study has no premise row to fail, and a pair can be
inverted in ways a single config's base comparison does not see.

**The one supporting refactor, which changes no value.** `_base_carbon_price` was split:
its precedence-(1) override branch stays where it was, and stages (2)–(3) (program adder
→ `CARBON_PRICE_PATHS` fallback) move verbatim into a new public
`resolved_base_trajectory_price(config, year)` — "what would resolve with `carbon_price`
unset", which is exactly the quantity a replacement replaces. `resolve_carbon_program`
does not read `config.carbon_price` (verified at `policy/cap_and_trade.py:249-256`), so
no config copy or `dataclasses.replace` is needed to evaluate the counterfactual, and
the guard never constructs a second config.

## 4. The warning text, verbatim

Emitted for the exact D21/D23 configuration, `ScenarioConfig(iso="NEISO",
carbon_price=25.0)`:

```
ScenarioConfig.carbon_price=25 is BELOW the NEISO base carbon trajectory in 25 of 25
horizon year(s): 2026-2050. A nonzero carbon_price REPLACES the resolved trajectory
(documented precedence (1)), it does not add to it. Widest gap in 2050: base
$132.16/tCO2 vs carbon_price $25.00/tCO2 (a $107.16/tCO2 CUT). This is the D23 premise
inversion (the FC-6 P1 'carbon price increase' that cut carbon in every horizon year): a
replace below the base trajectory REDUCES the carbon signal — for an increment use
carbon_price_delta. Set carbon_price=0.0 and carbon_price_delta to the increment you
want on top of the base trajectory, or keep this replacement if a below-base carbon
signal is the study you intend.
```

(One line in the emitted warning; wrapped here for the page. The charter's required
remedy sentence — *"a replace below the base trajectory REDUCES the carbon signal — for
an increment use carbon_price_delta"* — is carried verbatim, and is factored into the
module constant `CARBON_PRICE_BELOW_BASE_REMEDY` so the guard, its tests and this
finding quote one string. The reported values reproduce D23 §2 to the cent: base $132.16
at 2050, gap −$107.16.)

The message names, as the charter requires: the **ISO** (`NEISO`), the **years**
(`2026-2050`, contiguous runs collapsed; a partial hit renders only the years it hit,
e.g. `carbon_price=50` on NEISO reads `15 of 25 horizon year(s): 2036-2050`), and **both
values at the widest gap** (base `$132.16/tCO2` vs `carbon_price $25.00/tCO2`).

## 5. Tests

`tests/unit/policy/test_carbon_price_below_base_guard.py` — 19 tests, all passing. The
charter's five, in order:

| # | Requirement | Test |
|---|---|---|
| (i) | fires on the exact D21/D23 configuration (NEISO, `carbon_price=25`, RGGI base) | `TestFiresOnTheD23Configuration` — warning emitted at validation as a single `RuntimeWarning`; message names ISO, years, both widest-gap values; the remedy sentence asserted **verbatim**; it is a warning, not an error (the config still constructs and keeps `carbon_price=25.0`); the remedy (`carbon_price_delta=25`) actually silences it; and a partial-horizon hit still fires and names only the years it hit |
| (ii) | silent when `carbon_price` exceeds the base everywhere | `test_silent_when_carbon_price_exceeds_the_base_everywhere` — `$200/t` clears NEISO's `$132.16/t` 2050 peak; the premise (`max(base) < 200`) is asserted, not assumed |
| (iii) | silent when `carbon_price` is unset | `test_silent_when_carbon_price_is_unset` — with the RGGI base armed and nonzero, so silence is the override check and not an absent base |
| (iv) | silent in backcast mode | `test_silent_in_backcast_mode` — constructed so the **measured** base genuinely exceeds the override (2024 RGGI $22.83/t vs `carbon_price=10`), i.e. a mode-blind guard WOULD fire and only the mode gate suppresses it |
| (v) | the resolver's outputs are BYTE-UNCHANGED in all four | `TestResolverOutputIsByteUnchanged` — each of the four configs is rebuilt with the guard monkeypatched to a constant `None` (the exact pre-D34 `__post_init__` behavior) and `resolve_carbon_price` compared across all 25 horizon years with `==`, bit-equal rather than `approx` |

Plus `TestYearRunRendering` (the compact year-run renderer, including the
non-contiguous branch) and a no-program-ISO case (ERCOT's base is `0.0/t`, so no
override can sit below it).

**One pre-existing test needed its assertion scoped, not weakened.**
`tests/unit/config/test_config.py::test_from_yaml_does_not_warn_when_every_key_is_known`
asserted that a clean reload emits **no** `RuntimeWarning`; its fixture is
`ScenarioConfig(carbon_price=42.0, iso="CAISO")`, which legitimately trips the new guard
(CAISO's projected CARB trajectory reaches $152.29/t by 2050). The test's actual
contract is about the loader's unknown-key signal, so the assertion is now scoped to
warnings whose message names `from_yaml`, with a comment recording why. The other,
stricter warning test in the same class is untouched (its fixture is ERCOT, whose base
is 0.0/t, so the guard is correctly silent there).

**Regression sweep — D34 introduces ZERO new failures, established by an A/B on the
same tree.** The full `tests/unit` + `tests/scoring` + `tests/regression` suite runs
**5,548 passed / 79 failed / 35 skipped / 2 xfailed** (10m42s) at HEAD+D34. Those 79
were then re-run as an explicit A/B: the four changed files reverted to `HEAD~1`
(pre-D34) and re-run over the identical node-id list, ordering and working tree, then
restored and re-run. **Both arms produce 39 failed / 40 passed, and the two FAILED sets
are byte-identical** (`comm -13` and `comm -23` both empty). So no failure in the suite
is attributable to D34.

The 79 decompose into two pre-existing classes, neither touched by this change: (a)
**~19 cache-key *pin* tests** — `test_default_cache_key_is_unmoved` and relatives across
`config/`, `data/`, `model/`, `pipeline/`, plus `test_persisted_identity`; they fail at
`origin/main` too, and D34's own measurement independently confirms the six per-ISO
default keys are unmoved (§1). (b) **~45 LP smoke / soundness / integration / export /
scoring tests** which need `data/raw` — this session ran `DATA PROFILE: code` and
deliberately did not hydrate it. Class (b) is also order- and cache-dependent: 40 of the
79 PASS when run as a targeted subset and fail in the full-suite ordering, **identically
in both arms**. `ruff check` and `ruff format --check` pass on all four touched files
(the tree at large carries 5 pre-existing `ruff check` errors and 46 unformatted files,
none of them ours).

## 6. R4 is CLOSED — do not re-open it

D23 raised **R4**: *should `carbon_price` replace, floor, or stack on the program
price?* D26 explicitly left it open ("the delta field answers the instrument's need
without moving `carbon_price`'s documented replacement semantics for any consumer …
remains the owner's open design question"). **Owner ruling Q26 (2026-09-01, r#26
amendment 1) answers it: REPLACE + GUARD.** The semantics are settled, not deferred:

- `carbon_price` **replaces** the resolved trajectory. That is now the ruled answer, not
  merely the status quo — it preserves every registered field's meaning and needs no
  config archaeology across the committed record.
- The failure mode R4 was raised about is addressed by **observation**, not by changing
  what the field means: the guard makes a below-base replacement impossible to make
  silently.
- **No successor session re-opens the semantics question without a new owner act.** A
  future proposal to make `carbon_price` floor or stack is an owner-tier question, not a
  session-level design call — and the argument that "the field is a trap" is spent, because
  the trap now announces itself.

For an increment over the resolved base trajectory, the answer is and stays
`carbon_price_delta` (capx-D26): additive after the precedence chain, forecast-only
under rule 13, default 0.0 as an exact no-op, and never armed in a keeper or golden
posture.

## 7. Files changed

| File | Change |
|---|---|
| `src/market_sim/policy/carbon.py` | `resolved_base_trajectory_price` extracted from `_base_carbon_price` (no value moves); `CARBON_PRICE_BELOW_BASE_REMEDY`, `_format_year_runs`, `carbon_price_below_base_warning` added |
| `src/market_sim/config/scenarios.py` | `__post_init__`: the forecast-only below-base check, emitting the guard's message as a `RuntimeWarning` |
| `tests/unit/policy/test_carbon_price_below_base_guard.py` | new — the five charter tests plus the renderer and no-program-ISO cases (19 tests) |
| `tests/unit/config/test_config.py` | one assertion scoped to the `from_yaml` warning (§5) |
| `docs/handoffs/FINDING-capx-d34-carbonprice-guard-2026-09-01.md` | this finding |

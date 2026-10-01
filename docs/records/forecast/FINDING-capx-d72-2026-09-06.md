# FINDING — capx D72: the G-C1 carbon-nulling blast radius is EMPTY, and D23 stands unchanged

**Session:** D72 (capacity-expansion track), branch
`claude/capx-d72-carbon-floor-blast-radius-1lwkor`. **Date:** 2026-09-06.
**HEAD at launch:** `1aab49a0` (fresh off `origin/main`, 0 ahead / 0 behind).
**Charter:** pack §D72. **Phase 0 held throughout: ZERO LP solves.** Every number below is
computed from committed `run_config.json` files and from `git`-read source at two named
commits.

**Headline: the premise the charter asked me to verify is FALSE, and the null is clean.**
The pre-repair nulling predicate exempted `carbon_price_path="zero"` *by literal
enumeration* — `not in ("zero", None)` — from the day it was written to the day it was
removed, in exactly one form. **All 110 tracked `run_config.json` files in the repository
carry `carbon_price_path="zero"`.** The predicate therefore never fired on any committed
run, and the PRE-vs-POST `b1996141` effective carbon price differs by **$0.00 in every
solved year of every committed bundle** — max |gap| over 110 configs × their solve years =
**0.0**. RGGI was **not** nulled in any run this program scored. GOLDEN-2/GOLDEN-3's FC-6
`base` arm carried the full projected RGGI trajectory, **$26.05/t (2026) → $132.16/t
(2050)**, reproducing `FINDING-capx-d23-…` §2.2's published values to the cent. **D23's
attribution is verdict (a): it stands unchanged, mechanism included** — its §2.1 already
records `carbon_price_path="zero"` in both arms and its §2.2 already conditions the
trajectory on "the default `carbon_price_path='zero'`". Nothing needs re-scoring or
re-running on account of G-C1.

## 0. Charter discipline

No solve, no score, no registration. `ff-verdicts.json` and `program-status.json` untouched
(D60-R3's this window). No keeper, marker, shard, freeze, or board byte. No `ScenarioConfig`
field, no default flip, no semantic change proposed — S2 is ruled and executed, and rules
19 `[R-ONE-MECH]` / 24 `[R-REGISTRY]` permit exactly one documented semantic. D73's R1 guard
is **not** built here; §8 states what my answer implies for it. No mechanism tested, so no
matrix cell moves (rule 28 `[R-MECH-MATRIX]` duty (b) is vacuous for this lane). D23's file
is **amended only by a dated cross-reference**, never rewritten — the D23 §8 R3 precedent,
which likewise declined to edit D21's file.

## 1. The predicate, quoted from the code, and the answer to the first question

`resolve_carbon_program`'s forecast branch, immediately before the repair
(`b1996141^:src/market_sim/policy/cap_and_trade.py:285-300`, quoted whole):

```python
    else:
        # Forecast: an explicit exogenous RFF path (non-default) wins so
        # pre-EM-6 forecast configs keep their behaviour; otherwise carry the
        # projected program price (the EM-6 seam fix — forecast carbon is no
        # longer zero for a program ISO).
        if getattr(config, "carbon_price_path", "zero") not in ("zero", None):
            price = None
        else:
            named_path = getattr(config, "carbon_program_price_path", None)
            if named_path is not None:
                price = named_program_price(program, config.iso, year, named_path)
            else:
                price = projected_price(program, config.iso, year)
    return CarbonProgramResolution(
        membership=membership, price_adder=float(price or 0.0)
    )
```

**The exact predicate is `config.carbon_price_path not in ("zero", None)`, and
`carbon_price_path="zero"` does NOT satisfy it.** `"zero"` is the first member of the
exempt tuple, named literally. A config on `"zero"` fell through to the `else` and received
`projected_price(...)` — the full projected program trajectory. The docstring on the same
function said so in the same breath: *"the projected program price is used only when the
caller has not chosen an explicit exogenous RFF `carbon_price_path` (default `"zero"`)"*.

So the charter's conditional resolves on its first branch: **`'zero'` resolves as
default-equivalent; it is not "a non-default path".** Per the charter's step 1 this is
already a complete result. Steps 2–4 are reported anyway, because a null asserted from one
line of code is weaker than a null measured over every committed artifact — and because
step 4's control is what proves the instrument could have seen a gap had one existed.

**Note on scope, so the quotation is not over-read.** The predicate is the *nulling* half
only. The composition half lived one level up in
`b1996141^:policy/carbon.py::resolved_base_trajectory_price`, which read
`if resolution.price_adder: return it; else: return <path interpolation>` — i.e. "program
if nonzero, else path", replaced by `max(program, path)`. Under `"zero"` the path operand is
`0.0` in every year (`CARBON_PRICE_PATHS["zero"] = {2026: 0, 2030: 0, 2040: 0, 2050: 0}`),
so both forms return the program adder identically. **Both halves of the change are
therefore null on `"zero"`, not just the one the charter named.**

## 2. The defect, dated between two shas

The predicate existed in **exactly one form** for its whole life. On `main`'s first-parent
chain, only two commits ever touched `carbon_price_path` in `cap_and_trade.py`
(`git log --first-parent -S 'carbon_price_path' -- src/market_sim/policy/cap_and_trade.py`),
and they are the two boundaries:

| | commit | merged to `main` | date | role |
|---|---|---|---|---|
| **introduced** | `b33bf7750661c0c0136ea5830bc07f9a544e7513` — *"Add emissions mass-cap / cap-and-trade LP constraint"* (EM-6) | `57d5c873f` (PR #1328) | **2026-07-04** | created `cap_and_trade.py`; the predicate is at line 191 of the new file |
| **removed** | `b1996141edff566a9e5cf69fc2d6f4c58a1d1c61` — *"SCN-WS1c: federal carbon price is a FLOOR under the state program (ruling S2)"* | `9249b507f` (PR #4956) | **2026-09-06** | replaced by the unconditional program price + the `max` one level up |

Two facts that bound the radius from both ends:

- **`cap_and_trade.py` did not exist before `b33bf7750`** (`git cat-file -e b33bf7750^:…`
  → absent). The module, the forecast program adder, and the nulling predicate were born
  in the same commit. So there is no earlier variant of the predicate to check, and
  `git log -L`/`-S` over the path returns the two rows above and nothing else.
- **A distinct pre-EM-6 zeroing exists but is also empty of committed bundles.** Before
  2026-07-04 a forecast program ISO carried **no program adder at all** — the seam
  `b33bf7750` fixed, in its own words *"forecast carbon is no longer zero for a program
  ISO"*. That is a different zeroing from G-C1 and would bite regardless of path. It is
  moot here: **no committed `run_config.json` has an effective solve date before
  2026-08-02** (§3), i.e. every one of them post-dates EM-6 by a month. D23 §7 anticipated
  this exact chronology ("the pre-registration was valid when written (pre-EM-6) … the
  EM-6 seam fix silently inverted it"); this dating confirms it.

**The radius, stated as the charter defines it:** a bundle is IN only if it was solved
between `b33bf7750` (2026-07-04) and `b1996141` (2026-09-06) **and** carries a program ISO
**and** a non-default `carbon_price_path`. The first two conditions are widely met. The
third is met by nothing.

## 3. Census — every committed run config, placed

Method mirrors D60-R3's `FINDING-capx-d60-2026-09-05.md` §8-blast-radius so the two tables
read as one instrument: every committed `run_config.json`, its own recorded `git.sha` and
solve date, classified against the named boundary. Two differences, both stated: (i) the
classifier here is the **predicate itself**, evaluated on each config's recorded
`carbon_price_path`, not commit ancestry — because the predicate is config-keyed, ancestry
alone cannot decide a row; (ii) the date column therefore reports *when* rather than *which
side*, and every row is inside the window anyway.

**Coverage.** 110 tracked `run_config.json` (`git ls-files '*run_config.json'`): 107 under
`results/` plus `docs/handoffs/scn-ws1a/t0/{base,carbon_plus25}-run_config.json` and
`tests/golden/ercot_2026_2040.run_config.json`. 90 forecast + 17 backcast under `results/`;
the 3 outside `results/` are listed in §3.1. Nothing on disk is untracked
(`comm -13` → empty). SCN-WS1c's own epoch entry censused **90** files at its branch point;
**20 further configs have landed on `main` since**, and all 20 are covered here.

**A `~~struck~~` sha is a dead reference** — pre-2026-08-16-rewrite or a squashed branch
commit — in which case the date column falls back to `git.basis_sha`, then to the recorded
`timestamp` (marked `*`). 18 of 110 shas are dead; every one of those resolved through
`basis_sha`, so no row's date rests on a timestamp alone.

### A. Forecast-mode run configs (90)

| bundle (`results/…`) | ISO | years | `git.sha` | solved | `carbon_price_path` | program adder $/t (first→last) | predicate fires? | verdict |
|---|---|---|---|---|---|---|---|---|
| `ff-t1f-d45r/miso` | MISO | 2026-2030 | `~~e0d9f70c~~` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d45r/nyiso` | NYISO | 2026-2030 | `~~0f22b421~~` | 2026-09-04 | `zero` | 23.64→30.98 | **no** | **OUT** |
| `ff-t1f-d45r/pjm` | PJM | 2026-2030 | `~~bf54a4ad~~` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d46/caiso` | CAISO | 2026-2030 | `012ec403` | 2026-09-03 | `zero` | 30.02→39.36 | **no** | **OUT** |
| `ff-t1f-d46/ercot` | ERCOT | 2026-2030 | `dd10e9fe` | 2026-09-03 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d46/neiso` | NEISO | 2026-2030 | `75a5ff08` | 2026-09-03 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-d50/ercot` | ERCOT | 2026-2030 | `9e48ff6` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d50/neiso` | NEISO | 2026-2030 | `9e48ff6` | 2026-09-04 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-d50/pjm` | PJM | 2026-2030 | `c9f1d26e` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d60/caiso` | CAISO | 2026-2030 | `b83e96ca` | 2026-09-06 | `zero` | 30.02→39.36 | **no** | **OUT** |
| `ff-t1f-d60/miso` | MISO | 2026-2030 | `2ef4326e` | 2026-09-05 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-d60/nyiso` | NYISO | 2026-2030 | `e7412237` | 2026-09-05 | `zero` | 23.64→30.98 | **no** | **OUT** |
| `ff-t1f-d65-a1/neiso` | NEISO | 2026-2030 | `4b28c93f` | 2026-09-05 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-d65-ctl/neiso` | NEISO | 2026-2030 | `43b3a737` | 2026-09-06 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-s123/verify` | MISO | 2026-2030 | `54ca19a` | 2026-08-30 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t1f-s4hydro/neiso-control` | NEISO | 2026-2030 | `7a5065f` | 2026-08-30 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-s4hydro/neiso` | NEISO | 2026-2030 | `3d3832a` | 2026-08-30 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `ff-t1f-s6-pjm/ledger` | PJM | 2026-2030 | `54ca19a` | 2026-08-30 | `zero` | 0.00 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-d46/fc6/arms/base` | NEISO | 2026-2050 | `e659a6ea` | 2026-09-03 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-d46/fc6/arms/carbon_plus25` | NEISO | 2026-2050 | `e659a6ea` | 2026-09-03 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-d46/fc6/arms/gaspm5` | NEISO | 2026-2050 | `e659a6ea` | 2026-09-03 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-d46/fc6/arms/gasup150` | NEISO | 2026-2050 | `e659a6ea` | 2026-09-03 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-d46` | NEISO | 2026-2050 | `012ec403` | 2026-09-03 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/base` | NEISO | 2026-2050 | `9e56f0fe` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon25` | NEISO | 2026-2050 | `9e56f0fe` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon_plus25` | NEISO | 2026-2050 | `9e56f0fe` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gaspm5` | NEISO | 2026-2050 | `9e56f0fe` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gasup150` | NEISO | 2026-2050 | `9e56f0fe` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau-prera-2026-08-31` | NEISO | 2026-2050 | `~~271ad60~~` | 2026-08-30 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau/fc6/arms/base` | NEISO | 2026-2050 | `9f09f64e` | 2026-09-01 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau/fc6/arms/carbon_plus25` | NEISO | 2026-2050 | `9f09f64e` | 2026-09-01 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau/fc6/arms/gaspm5` | NEISO | 2026-2050 | `9f09f64e` | 2026-09-01 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau/fc6/arms/gasup150` | NEISO | 2026-2050 | `9f09f64e` | 2026-09-01 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `ff-t3-neiso-golden/bau` | NEISO | 2026-2050 | `f0a13bf5` | 2026-09-01 | `zero` | 26.05→132.16 | **no** | **OUT** |
| `hindcast/caiso-2021-2025-realized-t1h-d46` | CAISO | 2021-2025 | `71d3f1a6` | 2026-09-03 | `zero` | 28.06 | **no** | **OUT** |
| `hindcast/ercot-2021-2025-realized-t1h-d46` | ERCOT | 2021-2025 | `71d3f1a6` | 2026-09-03 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/ercot-2021-2025-realized-t1h-d4m` | ERCOT | 2021-2025 | `~~afc79934~~` | 2026-08-31 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d27` | MISO | 2021-2025 | `360b83ee` | 2026-09-01 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d31` | MISO | 2021-2025 | `b67a5f3a` | 2026-09-02 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d33` | MISO | 2021-2025 | `~~80327d08~~` | 2026-09-01 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d46` | MISO | 2021-2025 | `93ca86bd` | 2026-09-03 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio` | MISO | 2021-2025 | `~~36009c6~~` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-2021-2025-realized-t1h-d53-sectorgate` | MISO | 2021-2025 | `~~ff84df0~~` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/miso-d33-probe-entrydiag` | MISO | 2021-2025 | `0a3d22c7` | 2026-09-01 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/neiso-2021-2025-realized-t1h-d37-armed` | NEISO | 2021-2025 | `11735c1f` | 2026-09-02 | `zero` | 24.35 | **no** | **OUT** |
| `hindcast/neiso-2021-2025-realized-t1h-d45r` | NEISO | 2021-2025 | `~~0f22b421~~` | 2026-09-04 | `zero` | 24.35 | **no** | **OUT** |
| `hindcast/neiso-2021-2025-realized-t1h-d46` | NEISO | 2021-2025 | `71d3f1a6` | 2026-09-03 | `zero` | 24.35 | **no** | **OUT** |
| `hindcast/neiso-2023-2027-crossover-capxd14` | NEISO | 2023-2027 | `8412c3f6` | 2026-08-30 | `zero` | 24.35→27.88 | **no** | **OUT** |
| `hindcast/neiso-2023-2027-crossover-rcrepair` | NEISO | 2023-2027 | `5ba8beb1` | 2026-08-31 | `zero` | 24.35→27.88 | **no** | **OUT** |
| `hindcast/nyiso-2021-2025-realized-t1h-d45r-curveon` | NYISO | 2021-2025 | `~~cbb225ec~~` | 2026-09-04 | `zero` | 22.09 | **no** | **OUT** |
| `hindcast/nyiso-2021-2025-realized-t1h-d45r` | NYISO | 2021-2025 | `~~cbb225ec~~` | 2026-09-04 | `zero` | 22.09 | **no** | **OUT** |
| `hindcast/nyiso-2021-2025-realized-t1h-d52-devintage` | NYISO | 2021-2025 | `~~881c11d~~` | 2026-09-04 | `zero` | 22.09 | **no** | **OUT** |
| `hindcast/nyiso-2023-2027-crossover-capxd10` | NYISO | 2023-2027 | `3ebbd46` | 2026-08-30 | `zero` | 22.09→25.29 | **no** | **OUT** |
| `hindcast/pjm-2021-2025-realized-t1h-d45` | PJM | 2021-2025 | `86e676c2` | 2026-09-03 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/pjm-2021-2025-realized-t1h-d45r-fixed` | PJM | 2021-2025 | `~~455db0ea~~` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/pjm-2021-2025-realized-t1h-d45r` | PJM | 2021-2025 | `334be8c2` | 2026-09-04 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/pjm-2021-2025-realized-t1h-d57-clearing` | PJM | 2021-2025 | `a30696a0` | 2026-09-05 | `zero` | 0.00 | **no** | **OUT** |
| `hindcast/pjm-2021-2025-realized-t1h-d62-pubbar` | PJM | 2021-2025 | `~~a1e282fc~~` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `run-config-debt/ercot-2023-2027-crossover-ffr3a3` | ERCOT | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `run-config-debt/miso-2021-2025-realized-ffr3a3` | MISO | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `run-config-debt/miso-2023-2027-crossover-ffr3a4` | MISO | - | `edb8d0c2` | 2026-08-04 | `zero` | — | **no** | **OUT** |
| `run-config-debt/neiso-2021-2025-realized-ffr3a3` | NEISO | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `run-config-debt/nyiso-2021-2025-realized-ffr3a3` | NYISO | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `run-config-debt/pjm-2021-2025-realized-ffr3a3` | PJM | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `run-config-debt/pjm-2023-2027-crossover-ffr3a3` | PJM | - | `7ac1ba88` | 2026-08-03 | `zero` | — | **no** | **OUT** |
| `scenario-probes/scn-ws2a/neiso-2026-t0-ref` | NEISO | 2026-2026 | `6e6449ab` | 2026-09-06 | `zero` | 26.05 | **no** | **OUT** |
| `scenario-probes/scn-ws2a/neiso-2026-t0-target` | NEISO | 2026-2026 | `6e6449ab` | 2026-09-06 | `zero` | 26.05 | **no** | **OUT** |
| `scn-ws0-smoke/neiso/CARB` | NEISO | 2026-2026 | `107fe476` | 2026-09-05 | `zero` | 26.05 | **no** | **OUT** |
| `scn-ws0-smoke/neiso/REF` | NEISO | 2026-2026 | `107fe476` | 2026-09-05 | `zero` | 26.05 | **no** | **OUT** |
| `scn-ws2-ladder/ercot/BAU` | ERCOT | 2026-2030 | `0c349d2f` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws2-ladder/ercot/CES-20` | ERCOT | 2026-2030 | `0c349d2f` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws2-ladder/ercot/CES-40` | ERCOT | 2026-2030 | `0c349d2f` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws2-ladder/neiso/BAU` | NEISO | 2026-2030 | `0c349d2f` | 2026-09-06 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `scn-ws2-ladder/neiso/CES-20` | NEISO | 2026-2030 | `c2912cc3` | 2026-09-06 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `scn-ws2-ladder/neiso/CES-40` | NEISO | 2026-2030 | `c2912cc3` | 2026-09-06 | `zero` | 26.05→34.15 | **no** | **OUT** |
| `scn-ws4-probe/caiso/LOAD-HI` | CAISO | 2026-2026 | `7055bfc5` | 2026-09-06 | `zero` | 30.02 | **no** | **OUT** |
| `scn-ws4-probe/caiso/REF` | CAISO | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 30.02 | **no** | **OUT** |
| `scn-ws4-probe/ercot/LOAD-HI-ORGANIC` | ERCOT | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/ercot/LOAD-HI` | ERCOT | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/ercot/REF` | ERCOT | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/miso/LOAD-HI-ORGANIC` | MISO | 2026-2026 | `b4bbc7db` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/miso/LOAD-HI` | MISO | 2026-2026 | `b4bbc7db` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/miso/REF` | MISO | 2026-2026 | `b4bbc7db` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/neiso/LOAD-HI` | NEISO | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 26.05 | **no** | **OUT** |
| `scn-ws4-probe/neiso/REF` | NEISO | 2026-2026 | `2005d3e6` | 2026-09-06 | `zero` | 26.05 | **no** | **OUT** |
| `scn-ws4-probe/nyiso/LOAD-HI-ORGANIC` | NYISO | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 23.64 | **no** | **OUT** |
| `scn-ws4-probe/nyiso/LOAD-HI` | NYISO | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 23.64 | **no** | **OUT** |
| `scn-ws4-probe/nyiso/REF` | NYISO | 2026-2026 | `f90a5509` | 2026-09-06 | `zero` | 23.64 | **no** | **OUT** |
| `scn-ws4-probe/pjm/LOAD-HI` | PJM | 2026-2026 | `b4bbc7db` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |
| `scn-ws4-probe/pjm/REF` | PJM | 2026-2026 | `7055bfc5` | 2026-09-06 | `zero` | 0.00 | **no** | **OUT** |

### B. Backcast-mode run configs (17) — structurally unreachable (the changed branch is the `else` of `if mode == "backcast"`)

| bundle (`results/…`) | ISO | years | `git.sha` | solved | `carbon_price_path` | program adder $/t (first→last) | predicate fires? | verdict |
|---|---|---|---|---|---|---|---|---|
| `calibration/_nyiso114_baseattrib_2024` | NYISO | - | `~~5885248~~` | 2026-08-02 | `zero` | — | **no** | **OUT** |
| `calibration/caiso251_arm_nomargin` | CAISO | - | `~~f9c1fa0d~~` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/caiso252_b1_notrim` | CAISO | - | `fa23c1f7` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/ercot234_eastex_identity` | ERCOT | - | `0207d69` | 2026-08-25 | `zero` | — | **no** | **OUT** |
| `calibration/ercot236_k33_clip` | ERCOT | - | `~~17ab9e5~~` | 2026-08-25 | `zero` | — | **no** | **OUT** |
| `calibration/ercot248_two_config_keeper` | ERCOT | - | `0207d69` | 2026-08-25 | `zero` | — | **no** | **OUT** |
| `calibration/ercot249_2022_touchpoint_forward` | ERCOT | - | `49647dd6` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/ercot250_2022_touchpoint_carveout` | ERCOT | - | `49647dd6` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/miso217_intermphys_B` | MISO | - | `f3284261` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/miso220_nonsteamlift_B` | MISO | - | `4545300d` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/neiso99_joint_B` | NEISO | - | `b7904a1` | 2026-08-17 | `zero` | — | **no** | **OUT** |
| `calibration/neiso_tp2021_2020_k99` | NEISO | - | `6619fb4a` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/neiso_tp2022_k99` | NEISO | - | `6619fb4a` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/nyiso192_astoria_panel` | NYISO | - | `d5bba63b` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/nyiso196_extract_basis` | NYISO | - | `f7bb76a5` | 2026-09-05 | `zero` | — | **no** | **OUT** |
| `calibration/pjm_debugb_inputclock_A` | PJM | - | `~~457ae04~~` | 2026-08-14 | `zero` | — | **no** | **OUT** |
| `calibration/pjm_tp2022_2021_k162` | PJM | - | `46e08e5b` | 2026-09-05 | `zero` | — | **no** | **OUT** |

### 3.1 The three tracked run configs outside `results/`

| file | ISO | mode | `carbon_price_path` | note | verdict |
|---|---|---|---|---|---|
| `docs/handoffs/scn-ws1a/t0/base-run_config.json` | CAISO | forecast | `zero` | SCN-WS1a's own t0 arm | **OUT** |
| `docs/handoffs/scn-ws1a/t0/carbon_plus25-run_config.json` | CAISO | forecast | `zero` | `carbon_price_delta=25.0` | **OUT** |
| `tests/golden/ercot_2026_2040.run_config.json` | ERCOT | forecast | `zero` | no `solved_years` recorded | **OUT** |

### 3.2 Census result

| classification | count | basis |
|---|---|---|
| **IN-RADIUS** | **0** | no config carries a non-`"zero"` `carbon_price_path` |
| **OUT — predicate exempt** | 93 | forecast, `carbon_price_path="zero"` |
| **OUT — mode-unreachable** | 17 | backcast; the changed branch is the `else` of `if config.mode == "backcast"` |
| **INDETERMINATE** | **0** | every config records `carbon_price_path` explicitly; every date resolves through `git.sha` or `git.basis_sha` |

Supporting distributions over all 110: `carbon_price_path` — `"zero"` ×110, nothing else.
`carbon_program_price_path` — `None` ×110 (so the `named_program_price` limb is untaken
everywhere, on both sides of the repair). `mass_cap_enabled` — `False` ×110 (the ROW path
never engaged, so `resolve_carbon_program` reached the adder branch on every call).
`policy_bundle` — `"current"` ×110, so **no committed bundle is on `"tight"`**, the bundle
whose resolution S2 actually moved.

**Positive confirmation, not merely absence.** The census also records each config's
resolved program adder, and it is **live and escalating** exactly where a program exists:
CAISO `$30.02→$39.36` (2026–2030), NEISO `$26.05→$34.15`, NYISO `$23.64→$30.98`; `$0.00`
on ERCOT and MISO (no program) and on PJM (program with no price series — its forecast
adder is `$0.0` on both sides, D-1(c)). 50 of the 90 forecast configs carried a nonzero
program adder. **The state programs were charged, not suppressed.** The only forecast
configs on a program ISO showing a zero adder are the two `run-config-debt/*-ffr3a3`
reconstructions whose `solved_years` list is **empty** — no year was evaluated, so there is
no adder to report; not a nulling.

## 4. Priced without solving — both semantics, from the bundle's own committed config

For `results/ff-t3-neiso-golden/bau/fc6/arms/base/run_config.json` (NEISO, forecast,
`carbon_price_path="zero"`, `carbon_price=0.0`, `carbon_price_delta=0.0`,
`state_carbon_pricing=True`), reconstructing the config through `ScenarioConfig` and
evaluating the **pre-`b1996141`** composition (`resolve_carbon_program` with the nulling
predicate, then `if adder: adder else: path`) against **HEAD**
(`resolved_base_trajectory_price` = `max(program, path)`):

| year | program adder | RFF path (`zero`) | PRE effective | POST effective | **gap** |
|---|---|---|---|---|---|
| 2026 | 26.05 | 0.00 | 26.05 | 26.05 | **0.00** |
| 2030 | 34.15 | 0.00 | 34.15 | 34.15 | **0.00** |
| 2035 | 47.90 | 0.00 | 47.90 | 47.90 | **0.00** |
| 2040 | 67.18 | 0.00 | 67.18 | 67.18 | **0.00** |
| 2045 | 94.23 | 0.00 | 94.23 | 94.23 | **0.00** |
| 2050 | 132.16 | 0.00 | 132.16 | 132.16 | **0.00** |

**Σ|gap| over all 25 horizon years = 0.000000 $/tCO2.** Swept over **all 110 tracked
configs × all their solved years: max |gap| = 0.0.** Stated at full magnitude as the
charter requires: **the gap is exactly zero, everywhere.** The radius is nominal.

**The control — proof the instrument can see a gap.** The same NEISO config with the single
field `carbon_price_path` changed to `"mid"` (the RFF path `policy_bundle="tight"`
resolves to, and the arm SCN measured) yields a **positive** PRE→POST gap of **$19.15 to
$82.16/tCO2** across the 25 years, minimum at 2030 (`$34.15 − $15.00`) and maximum at 2050
(`$132.16 − $50.00`). That sits inside SCN-WS1c's reported $15.98–$102.29 band, which spans
CAISO+NYISO+NEISO where mine is NEISO alone. **My reconstruction of the pre-repair semantics
therefore reproduces the defect SCN measured, on demand, and returns zero on the committed
configs.** The zero is a measurement, not a blind spot.

## 5. Consumer inventory — why the null covers every call site, not just one

`resolve_carbon_program`'s return value **did** change post-repair (`None` → the program
price) for a non-default path, so every direct consumer is in principle exposed. All of
them are null here, and for stated reasons:

| consumer | exposure | why null on the committed set |
|---|---|---|
| `policy/carbon.py:170` `resolved_base_trajectory_price` | the one composition point (rule 19) | predicate never fires; and `max(program, 0.0) == program` |
| `policy/carbon.py:379` `carbon_path_below_program_warning` | the new S2 invariant guard | early-returns at `carbon.py:367` on `path_name in ("zero", None)` — inert on all 110 |
| `policy/constraints.py:53` | mass-cap ROW path | `mass_cap_enabled=False` ×110; and the ROW branch returns **before** the adder branch, so it is unreachable from the change either way |
| `scripts/run_calibration.py:4036` | direct call | reached only with the same configs; predicate never fires |

## 6. The D23 re-examination

**Verdict: (a) — D23 stands unchanged, and its stated MECHANISM stands too, so (b) does not
apply either.** Three independent legs:

1. **The arms are OUT of radius.** `ff-t3-neiso-golden/*/fc6/arms/{base,carbon25,
   carbon_plus25,gaspm5,gasup150}` all carry `carbon_price_path="zero"`,
   `carbon_program_price_path=None`, `mass_cap_enabled=False`, `state_carbon_pricing=True`,
   `mode="forecast"` (§3). The predicate never fired on any of them.
2. **The adder resolved, at the values D23 published.** Recomputing the base arm's effective
   carbon price at HEAD gives 2026 `$26.05` · 2028 `$29.83` · 2032 `$39.10` · 2035 `$47.90`
   · 2040 `$67.18` · 2045 `$94.23` · 2050 `$132.16` — **identical to D23 §2.2's list, to the
   cent**, and identical under the pre-repair composition (§4). D23's premise —
   *"rung 0 IS the RGGI world for a program ISO, sitting ABOVE rung 25 in every NEISO
   year"* — is **verified**, not merely assumed.
3. **D23 did not rely on an unstated condition.** Its §2.1 records `carbon_price_path="zero"`
   in both arms as a checked fact, and its §2.2 conditions the trajectory explicitly on
   *"in forecast mode with the default `carbon_price_path='zero'`"*. D23 read the very
   predicate that was later repaired, read it correctly, and stated the condition its
   conclusion depends on. There is no mechanism sentence to amend.

**The `carbon25` arm's signal cut reproduces exactly.** Evaluating the committed
`bau-prera-2026-08-31` arms at HEAD: `carbon25 − base` = **−$1.05 (2026) → −$107.16
(2050)**, matching D23 §2.5's published deltas to the cent. **The FC-6 P1 defect D23
attributed is real, is the `carbon_price` REPLACE semantics (owner ruling Q26), and is
entirely independent of G-C1.** The two defects live on different fields — `carbon_price`
vs `carbon_price_path` — and S2 explicitly left the former untouched.

### 6.1 A fact the director should have before serving D73

**The live golden has already been re-armed off the mis-constructed pair.** The current
families `ff-t3-neiso-golden/bau` and `bau-d46` carry FC-6 arms
`{base, carbon_plus25, gaspm5, gasup150}` — **the `carbon25` arm is gone**, replaced by
`carbon_plus25` (`carbon_price=0.0`, `carbon_price_delta=25.0`), which is D23 §8 R2(iii) /
capx-D26 landed. Only the snapshot family `bau-prera-2026-08-31` still carries `carbon25`.
Measured at HEAD:

| family | FC-6 carbon arm | Δ effective signal vs base | strictly above base in all 25 yrs |
|---|---|---|---|
| `bau`, `bau-d46` (live) | `carbon_plus25` | **+$25.00 in every year** | **yes** |
| `bau-prera-2026-08-31` | `carbon25` | −$1.05 → −$107.16 | no |
| `bau-prera-2026-08-31` | `carbon_plus25` | +$25.00 in every year | yes |

So D23's R1 premise assertion, if built, would **pass** the live golden's FC-6 pair and
fire only on the archived `carbon25` arm. That is a material input to whether D73 should
reclassify anything, and it is reported, not acted on.

Independent corroboration that the repair is wired: the D34 guard
`carbon_price_below_base_warning` **fired live** during this session's sweep when
`bau-prera-2026-08-31/fc6/arms/carbon25`'s config was constructed, naming the D23 inversion
by name and pointing at `carbon_price_delta`. The runtime half of R1 therefore already
exists; what does not exist is a **scorer-side** reclassification.

## 7. Cross-reference added to D23's file

Per the charter and the D23 §8 R3 precedent (which declined to edit D21's file), D23's
finding is **not rewritten**. A single dated cross-reference block is appended to
`docs/handoffs/FINDING-capx-d23-p1-carbon-sign-2026-09-01.md` recording that D72 re-examined
its attribution against the G-C1 repair and returned verdict (a). No conclusion, verdict,
number, or section of D23 is altered.

## 8. Recommendation to the director — a recommendation, never an act

**(1) Nothing must be re-scored or re-run on account of G-C1. LP cost: zero.** The blast
radius is empty by two independent arguments — the predicate's own exempt tuple, and a
measured $0.00 gap over every solved year of all 110 committed configs. No committed verdict
rests on a nulled program adder. SCN-WS1c's cache-epoch entry reaches the same conclusion by
its own census; this lane's is an independent replication over the 20 configs that landed
since, and it agrees.

**(2) D23's verdict basis is NOT re-opened, and its FC-6 P1 FAIL stands as scored.** Verdict
(a), §6. The `neiso-t3` P1 FAIL remains attributable to the arm construction D23 named — the
`carbon_price` replace, not any path nulling.

**(3) D73 is unblocked and its scope narrows.** The R1 guard's premise survives §6 intact,
so D73 may proceed on D23's original basis. What my §6.1 changes is the *expected yield*:
the live golden's FC-6 pair would **pass** the guard (+$25.00/yr, monotone), so R1 is a
**regression tripwire and an archival reclassifier**, not a live-verdict mover. The director
may therefore want to serve D73 with the question sharpened: *should the guard retroactively
reclassify the archived `carbon25`-based P1 FAIL to MIS-CONSTRUCTED, given the pair has
already been re-armed?* That is a verdict-basis decision and remains the director's. LP cost
of R1 itself: **zero** (it reads committed configs).

**(4) Ordering against D60-R3's legs: independent, no sequencing constraint.** D60-R3's
radius is keyed on commit ancestry across the D55 floor-retention hunk (`da007e0f`) and
concerns *retirement ordering*; mine is keyed on a config field and concerns *carbon price*.
They share the bundle population but not a single number — a bundle can be PRE-hunk for
D60-R3 and OUT for D72 simultaneously, and 28 of them are. **No D72 finding changes any
D60-R3 classification, and no D60-R3 re-solve is needed for a D72 reason.** Should D60-R3's
re-solves be run for its own reasons, they will carry the post-S2 carbon semantics — which,
on `carbon_price_path="zero"`, are byte-identical to the pre-S2 ones (§4), so they introduce
no confound.

**(5) One residual worth a line, offered as an observation and not a routed repair.** The
first non-`"zero"`-path bundle solved on either side of `b1996141` will not be comparable to
one solved on the other, as SCN's own epoch entry says. Nothing in the program has such a
bundle today, and `policy_bundle="tight"` — the construction that reaches a non-`"zero"`
path — is unused across all 110 configs. If a future lane arms `tight` on CAISO/NYISO/NEISO
it should cite S2 and the epoch entry, and it should expect an exact **no-op** on those three
ISOs (the ruled consequence, `b1996141`'s message). Open cards D-1(b) and D-1(c) remain the
owner's; this lane proposes nothing on either.

## 9. Reproduction

Zero LP. Every number regenerates from committed artifacts and `git`-read source:

```
git show b1996141^:src/market_sim/policy/cap_and_trade.py | sed -n '285,300p'   # §1
git log --first-parent -S 'carbon_price_path' \
    -- src/market_sim/policy/cap_and_trade.py                                   # §2
```

§3–§6 are produced by the census/sweep/pricing scripts described inline: for each tracked
`run_config.json`, rebuild `ScenarioConfig` from its `scenario_config` block (dropping keys
that are not dataclass fields — only `caiso_bidir_intertie`, on the golden arms), then
compare `policy.carbon.resolved_base_trajectory_price` (HEAD) against the reconstructed
pre-`b1996141` composition `0.0 if path not in ("zero", None) else program; adder or path`.
Requires `numpy pandas pydantic pyyaml` and `PYTHONPATH=src`.

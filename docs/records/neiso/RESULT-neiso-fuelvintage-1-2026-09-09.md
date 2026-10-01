# RESULT — NEISO: the 2019-2022 retiree window, and the gas index-vs-delivered gap

**Session:** `neiso-fuelvintage-1`, 2026-09-09. **Branch:** `claude/neiso-fuelvintage-1`.
**Scope: NEISO only.** No other ISO's keeper shard, matrix shard or log was written.
**Companion:** `docs/FINDING-neiso-gas-index-vs-delivered-2026-09-09.md` (the zero-LP fuel
investigation — read it first; it is the larger result).

## 0. Headline

1. **The index-vs-delivered gap is SETTLED.** The Algonquin index is right; the EIA `N3045`
   blend is an average delivered cost, not a marginal one. Four independent zero-LP tests,
   in the companion FINDING. **NEISO has no gas level gap at all** — the keeper reproduces
   the published index in **73 of 84 months exactly**, so the cross-ISO table's
   "+2.303 $/MMBtu, the largest level gap" is a reference-choice artifact.
2. **`gas_electric_power_monthly_level` is EXACTLY inert for NEISO** — `0.000000000 $/MMBtu`
   on the gas series in all seven years. **SHARD F was cancelled**: an LP cannot add
   information to an exact-zero input delta. Matrix cell `O` → **`I`**.
3. **The retiree-window fleet fix lands with EVERY SCORED BAND UNCHANGED**, in both the
   training span and the holdout ladder. Determination **CALIBRATED** on both, 8 scored /
   0 fails / 1 ledgered C3c — identical to the incumbent keeper.
4. **Charter task 3 is NOT met literally and is reported as such**, with a root cause (§3).
5. **Charter task 4 done**: the `NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']` 2019 caveat is retired,
   measured (§4).

## 1. What was solved, and where it is

Both bundles are `scripts/replay_keeper.py` on the designated keeper
`results/calibration/neiso106_offerlevel` — **zero config deltas, no `--set`, no new flag**.
The only changed input is the 2019-2022 retiree window (commit `7934e92c`).

| bundle | years | registered as | determination |
|---|---|---|---|
| `results/calibration/neiso107_train` | 2023 2024 2025 | `2026-09-09-neiso-107-retiree-window` | **CALIBRATED** |
| `results/calibration/neiso107_holdout` | 2020 2021 2022 (`--holdout-authorized`) | `2026-09-09-neiso-107-holdout-touchpoints` | **CALIBRATED** |

Both are **gitignored** (`results/calibration/neiso107_*/`) per rule 31 `[R-RETAIN]` — kept on
local disk, kept out of `main`, **not deleted**. Their slim sets are committed via `git add -f`.

**Deviation from ADDITION 2, stated:** the solves were run **in this session as two concurrent
invocations** (years sequential within each — rule 12 `[R-PARALLEL]` exactly), not as five
child sessions. Reason: a child session's bundle lives in an ephemeral container this session
cannot collect from, which would defeat ADDITION 4's composition duty and rule 31's retention
duty at once. Two concurrent invocations is already rule 12's stated cap for a per-plant
multi-zone LP, and `--years 2023 2024 2025` in ONE invocation satisfies rule 16 `[R-ALLYEARS]`
directly with no fragment to compose. Wall clock: ~25 min for all six years.

## 2. The holdout touchpoints — every pre-registration held

Control is **G-CTRL form 4** (rule 29(b), NO CONTROL SOLVES): the committed touchpoint bundle
`2026-09-06-neiso-106-touchpoints-2020` — the same keeper recipe, the same three years, the
pre-fix fleet.

| | 2020 | 2021 | 2022 | pre-registered |
|---|---|---|---|---|
| annual mean price, keeper → new ($/MWh) | 26.141 → 25.950 | 48.680 → 48.399 | 85.621 → 85.520 | |
| **Δ mean price** | **−0.190** | **−0.281** | **−0.101** | *"prices FALL modestly"* ✅ |
| max hourly \|Δprice\| | 117.27 | 94.40 | **4.31** | |
| net class energy (TWh) | −0.0119 | −0.0049 | **−0.0020** | *"2022 immaterial; a large 2022 move is a BUG"* ✅ |
| `slack` / `dump` / `demand` / `reserve_price` | **bit-identical** | **bit-identical** | **bit-identical** | |

**Class attribution — the mechanism doing exactly what it should.** The restored units are
steam and CT (Mystic 7, Essential Power MA, Capitol District, Pawtucket), so:

- `ST_GAS` **+333 / +355 / +142 GWh**
- `CC_REGULAR` **−599 / −307 / −141 GWh**

Real units that really ran, taking load off the CC fleet, at a slightly lower price. That is
the structural signature of a correct fleet, not a tuned one.

**Rule 30 `[R-TOUCHPOINT-FOLD]`:** the run is stamped to the keeper
(`stamp_touchpoint_holdout.py`) and `build_status.py --iso NEISO` rebuilt (`--check`: in sync).
Every criterion **HELD** — PASS in-sample → PASS on holdout, with C3c **carried** (a known
limitation travelling, not a new discovery). **Rule 30(c): a held-out year never downgrades
NEISO**, whose determination remains its train-tier verdict.

**2019 was NOT touched.** It is locked-test tier under an ACTIVE spend freeze with `final`
empty; `holdout_policy.registration_refusals` refuses it, and the charter's Pilgrim case is a
2019 case. Refused, not designed around.

## 3. Charter task 3 — the bit-identity check FAILED its literal bar. Root cause.

**Result:** max |class-hour delta| vs the committed keeper is **426.95 / 371.44 / 442.34 MW**
(2023/2024/2025), **not the 0.000000 MW the charter asked for.** Not waved through:

**(a) The added units are not the cause — they are dispatch-inert, measured at unit level.**
Of the 24 plants the 2019-2022 window addition touches, exactly one (1588 Mystic) carries any
capacity in a training year, and that is Mystic 8&9, which retire **2024-06** and were already
in the window before the change. The two generators the change actually added for Mystic —
`1588_7` and `1588_GT1` (retired 2021-06) — read **`cap_mw` 0.000 and 0.000 GWh in 2023, 2024
and 2025**, as do all 23 other added plants. In 2025 plant 1588 is zero throughout.

**ADDITION 1's overlap check, VERIFIED for NEISO:** the 24 newly-added plants are **disjoint
from the EIA-860 operable snapshot** — zero overlap, so no double-count with
`_partial_plant_exit_rows`. Only plant 1588 carries both newly-added (≤2022) and pre-existing
(≥2023) window rows, and they are different generators.

**(b) What the delta actually is: alternate optima of a degenerate LP.**

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| net class energy (TWh, on ~86 TWh) | +0.000035 | +0.000107 | −0.000277 |
| annual mean price ($/MWh) | 36.7164 → 36.7159 | 42.0710 → 42.0733 | 67.6033 → 67.6012 |
| `demand` / `slack` / `dump` / `reserve_price` | **bit-identical** | **bit-identical** | **bit-identical** |
| class-hours touched | 2,433 / 122,640 | 2,180 / 122,640 | 2,676 / 122,640 |

The tell is the `hydro` class: **net delta EXACTLY zero across 1,192 hours** with a 224 MW
swing — the same energy moved between hours under a binding monthly budget, i.e. a tie broken
differently. The 2025 max price delta is exactly `2.777777778` (= 25/9), a dual switching
between two tied vertices rather than a cost changing.

**(c) Two candidate perturbation channels, disclosed and NOT separated.**
(i) The 44 added units enter `FleetArrays` with `pmax > 0` and availability 0 — **exactly the
channel ADDITION 6 predicted** ("the COD ramp deliberately does not touch `pmax`") — adding
zero-upper-bound columns that move HiGHS's pivot ordering. (ii) HEAD drift since the keeper's
basis commit `013826a4`: the solve-surface fingerprint moved
`531e4805c9085734 → 9d35c270c69e9eee` (195 → 197 rows; the new names are
`F923_GAS_PRICE_PLAUSIBILITY_BAND` — inert here, the keeper sets the flag `None` and the hub
overlay overwrites every gas cell afterwards — and `EGRID_CT_HR_PHYSICAL_FLOOR`).
**No control solve was spent to separate them** (rule 29(b)); differencing three parts per
billion of annual energy between two benign causes does not earn an LP.

**(d) The charter's actual concern is answered NO.** It asks whether "capacity-denominated
code is reading retired units". Nothing capacity-denominated runs in a `mode="backcast"` NEISO
solve (no capacity evolution), and the one place capacity reaches the output — `cap_mw` —
reads **0.000 for all 44 added units in all three years**. Reported at full magnitude, and
**routed, not absorbed**: if bit-identity is wanted as a standing invariant, the fix is to drop
zero-availability-all-year units from the LP column set rather than to carry them at
`pmax > 0`, and that is a shared-path change no single ISO's lane should make alone.

**A separate gap found and routed, not absorbed.** In 2020 the window restores 774.1 MW of the
956.0 MW EIA-860 says was alive (2021: 788.3 / 949.0; 2022: 199.1 / 201.3). The ~101 MW
difference is plants that carry **zero capacity all year** and are almost all **waste-to-energy,
landfill gas, biomass, small hydro and wind** (54945 CT Resource Recovery 58.5 MW, 50273
Pioneer Valley 7.5, 58595 Indeck 15.2, 58993 Pine Tree, 59022/59023 wind, 54301/1481 hydro,
55830 East Millinocket). Those classes are driven by measured budgets/CFs rather than unit
capacity, so this may be by design; it is 0.4 % of NEISO's fleet and it is **not this lane's
to change**. Named here so it is not lost.

## 4. Charter task 4 — the 2019 nuclear caveat is retired, measured

`NUCLEAR_MONTHLY_CF_BY_YEAR['NEISO']`'s standing caveat read *"a 2019 solve is short ~2.18 TWh
of nuclear regardless of this overlay"*. Pilgrim (EIA 1590, 673.6 MW net summer, retired
2019-05) is now in the retiree window — **the only nuclear unit in it**, so 2020-2025 are
untouched — and the COD ramp zeros it after May. Measured against EIA-923, 2019 nuclear energy:

| | GWh | vs actual |
|---|---|---|
| actual (incl. Pilgrim) | 29,818 | — |
| this overlay on the OLD 2-plant fleet | 27,698 | **−2.119 TWh** (reproduces the caveat) |
| on the retiree-window fleet | 29,879 | **−0.061 TWh (−0.2 %)** |

**Not closed, and written into the comment rather than absorbed:** the 2019 row's *denominator*
is still the 2-plant fleet (`derive_nuclear_monthly_cf.py` builds from `load_fleet_from_csv`,
which does not union the retiree window), so Jan-May carries a monthly shape error even though
the annual nets out. Re-derived on the 4,028.6 MW augmented fleet those months read
`[0.98, 1.00, 0.99, 0.74, 0.76]` against the committed `[1.00, 1.00, 0.99, 0.69, 0.79]` — worst
month April, +130 GWh. **Deliberately NOT re-derived here**: the constant is on the solve
surface, so editing it re-keys every ISO's configs, and it would do so to repair a year that is
frozen and unsolvable. Owed the day 2019 is authorized. The edit is **comment-only** — verified
value-neutral: the NEISO solve-surface fingerprint is unchanged at `9d35c270c69e9eee`, and
`derive_nuclear_monthly_cf.py --check` passes on all seven years.

## 5. Gates

| gate | result |
|---|---|
| `check_mechanism_matrix --base origin/main` | **integrity OK**, exit 0 (pre-existing anchor warnings only) |
| `audit_keepers --iso NEISO` | **PASS**, 0 failures / 0 warnings (keeper, holdout, marker, status) |
| `build_status --iso NEISO --check` | **in sync** |
| `derive_nuclear_monthly_cf --isos NEISO --years 2019..2025 --check` | **matches** |
| `check_cache_key_registration --base origin/main` | RED on `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` only — **the ADDITION 7 pre-existing baseline, nothing new** |
| `pytest tests/scoring` | re-baselined on this tree; see §6 |

CAISO's `build_status --check` / `audit_keepers` reds are **CAISO's lane's** (rule 25) and were
not touched.

## 6. Governance

- **Rule 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`.** Both changes land because they are **correct**.
  Nothing was gated on a residual; the fuel arm was refused for being *exactly inert*, not for
  scoring badly, and the fleet fix was never judged by whether the fit improved.
- **Rule 21 `[R-DOF]`.** Free parameters added: **zero**. The retiree window is an EIA-860 read;
  the DOF ledger is the keeper's own, at the keeper's own magnitude.
- **Rule 22 `[R-HOLDOUT]`.** 2020-2022 spent under NEISO's `complete` marker with
  `--holdout-authorized`, re-checked at registration by the R-AZ gate. **2019 and H1-2026 were
  not touched, not requested, and are refused by the freeze.**
- **Rule 29 `[R-SCREEN]`.** Clause (0) killed the fuel arm pre-solve. Clause (b): no control
  solve; the committed keeper and the committed prior touchpoint are the controls. Clause (c)
  discharged by `.gitignore`, **never by `rm`** (rule 31).
- **Rule 31 `[R-RETAIN]`.** Nothing deleted. Both bundles are on local disk and **will not
  survive this ephemeral container**. See the promotion question below.
- **Rule 15 `[R-DASHBOARD]`.** Both runs registered in this session. **Nothing was pruned** —
  keeper-only retention would delete the very bundles the owner needs to rule on, and rule 31
  subordinates cleanup to that ruling.

## 7. THE PROMOTION QUESTION — asked explicitly, per rule 31

**`2026-09-09-neiso-107-retiree-window` is a keeper candidate and the decision is the owner's.**

- **For promoting it:** it is the keeper's own recipe on a **more accurate fleet** (rule 14),
  it scores **identically** (CALIBRATED, 8 scored, 0 fails, 1 ledgered C3c), and its holdout
  ladder is the matching corrected-fleet run with every criterion held.
- **Against:** the training years are not bit-identical to the incumbent (§3) — 0.055 % of
  class-hours reshuffled with net-zero energy and prices moving 1-3 parts in 100,000. Nothing
  scored moves, but it is not a no-op at the parquet level.
- **My recommendation:** promote. The fleet is more accurate, no band moved, and the residual
  is alternate-optimum noise. **But I have not acted on that recommendation** — the keeper shard
  is untouched and the touchpoint is stamped to the **incumbent** `2026-09-06-neiso-106-fossil-offer`.

If the answer is promote, the follow-up is one commit: re-stamp the touchpoint to the new
keeper id, edit `frontend/data/backcast/keepers/NEISO.json`, re-key the `complete` marker with
a determination re-verification (rule 22 D-5(b)), rebuild `build_status.py --iso NEISO`, and
prune the superseded runs. **If the ruling does not come before this session ends, the bundles
are gone and reproducing them costs ~25 minutes of LP** (6 years, 2 concurrent invocations).

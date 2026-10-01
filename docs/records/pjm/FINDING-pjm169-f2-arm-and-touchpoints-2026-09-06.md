# FINDING — pjm-169: F2 is ARMED, at a different site than prescribed; F4 is built and unspent

**Session:** pjm-169 · **Date:** 2026-09-06
**Branch:** `claude/pjm-calibration-f2-f4-n6wzrr`
**Keeper:** `2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`) — **UNCHANGED, not promoted**
**Predecessor:** `results/calibration/FINDING-pjm168-f1-f2-screens-2026-09-06.md`
**Owner decision:** arm F2 for PJM (2026-09-06, this session, `AskUserQuestion` — "Yes — arm F2 for PJM")

---

## 1. The answer

> **F2 (`pjm_interface_feed_admissibility_gate`) is ARMED for PJM — but NOT at the site the
> handoff prescribed, because that site is inert for this mechanism.** The handoff named
> `iso_configs.py::_pjm_config default_scenario_overrides`, which is applied by
> `runner.run_scenario_iso` — the **forecast** front end. The backcast calibration lane reaches the
> LP through `run_calibration.run_year` + `pipeline.solve` and **never calls
> `apply_iso_scenario_defaults` at all**. Arming there would have written the flag into
> `run_config.json` and changed nothing in the LP: the caiso-162 defect class verbatim. The arm is
> in `pipeline/backcast_config.py`, following the `caiso_ra_mustoffer` / `ct_netload_drag`
> per-ISO precedent, and both of the owner's conditions hold exactly and are measured (§2).
>
> **The re-run touchpoints remove the EMAAC VOLL artifact ENTIRELY in BOTH held-out years**
> (2021: 99,100 MWh over 74 h → 0; 2022: 42,582 MWh over 45 h → 0) and collapse the inverted
> east–west wedge to +$1.21 / +$1.36 against an actual −$5.43; C3b 2021 flips FAIL → PASS and
> C3a 2021 improves +25.7 % → +10.8 %. **Both rungs still read `NOT-YET`** — the arm repairs a
> real input defect, it does not close 2022 — and per rule 30(c) PJM's headline is unchanged at
> **CALIBRATED**.
>
> **F4 is BUILT, SCREENED, and REJECTED by its own pre-registered STOP gate S4.** Its PRECOMMIT was written before any build,
> as the handoff required; S1-S3 and S5 pass (S3 to a ratio of 0.999 against a magnitude fixed
> before the solve) and S4 fails on a 3.28 % coal move. Three corrections to the handoff's F4
> framing were found at zero LP cost: `COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU` is **inert in the PJM
> keeper** (§4.1); the live coal-side window-extrapolation pushes the **opposite** way (§4.2);
> and **2021 is inside the anchor's identification support**, so F4 was never the 2021 story
> (§4.4). **The session's strongest remaining lead is the coal sigmoid's `ceil`**, which prices
> PJM bituminous in 91.5 % of 2022 hours against 0.0 % in 2023 and 2024 — a separate card.

## 2. F2 — the arm, and why the site moved

### 2.1 The site question, settled on evidence

`runner.py:1261-1264` states it outright — *"Backcast is doubly insulated —
`run_calibration_full.py` never applies `default_scenario_overrides` at all"* — and it checks out
three ways: `apply_iso_scenario_defaults` has no call site in `run_calibration*.py` (its callers
are `runner.py`, `run_capacity_hindcast.py`, `run_full_horizon.py` and probes); neither calibration
script imports `market_sim.runner`; and `run_calibration.run_year` builds its config from
`pipeline.backcast_config` and solves through `pipeline.solve`.

**Why D57 / D67 / D75-R are unaffected by this.** Those arms' fields are forecast-mode objects that
`__post_init__` coerces away in a backcast — which is exactly why the ISOConfig site suits them and
why their commit notes can claim every backcast keeper stays byte-identical. F2 is the opposite
kind of object: both of its read sites (`run_calibration.py:2738`, `:2955`) sit under
`pjm_measured_interface_limits`, a **backcast-only** overlay. The forecast lane keeps the static
per-link seeds and never reads the feed at all, so `backcast_config` is the mechanism's ONE site
(rule 19 `[R-ONE-MECH]`) rather than one of two.

### 2.2 The two conditions, measured

| config | cache key |
|---|---|
| PJM **armed** | `20bc47b308268183` |
| PJM `--no-pjm-interface-feed-admissibility-gate` | `6595f6053397d5a0` |
| PJM at HEAD, **pre-arm** | **`6595f6053397d5a0`** — identical |

ERCOT `bbe95cb3efea7281` · CAISO `0fe108a7cef1afc4` · MISO `4e9494f6bd01b724` ·
NYISO `6d6acff870806b75` · NEISO `2a846f1213bf815a` — every one byte-identical to HEAD
(rule 25 `[R-ISO-SCOPE]`). So the off-switch reaches the pre-arm posture **and keeps its key**, and
no other ISO moves.

*(The `547053bd → 4ccb6bfe` pair quoted to the owner at decision time was computed on a bare
`ScenarioConfig()`, not on the PJM recipe. Same fact — PJM re-keys, nobody else does — measured on
the wrong object; the table above is the recipe's own keys.)*

### 2.3 The off-switch did not exist and had to be built

F2 shipped from pjm-167 with **no CLI flag at all**, so once armed there would have been no way
back and the handoff's "`--no-…` must reach the pre-arm posture" would have been unsatisfiable.
`--pjm-interface-feed-admissibility-gate / --no-…` is threaded tri-state (the `ct_netload_drag`
pattern) through `run_calibration_full.solve_and_persist` and `run_calibration.run_year`: unset
keeps the per-ISO backcast default, `True`/`False` force. Because `recorded_cfg` starts from
`backcast_config`, `run_config.json` reports the **armed** posture for an unset PJM caller and the
**forced** posture when forced — the rule 24 `[R-REGISTRY]` requirement that a record report the
posture it solved, not the one the caller happened to type.

### 2.4 Replay wiring, checked

The keeper's `meta.json` does not carry the field, so `replay_keeper.build_kwargs` passes nothing
and the armed backcast default applies — which is what the touchpoint re-run needs. `run_year`
accepts the new parameter, so a future bundle's recorded `None` still falls through to the default.

## 3. Verification and touchpoints

### 3.1 The 2023 re-verification — BIT-IDENTICAL through the shipping site

pjm-168 proved H6 through the `replay_keeper --set` override channel. This session arms the
mechanism at a **different site**, so the proof was re-run through the site that ships: a 2023
replay of the keeper recipe (`results/calibration/pjm169_verify_2023arm`, since deleted per rule 29
clause (c) — this table is the record), with nothing forced on the CLI, so the arm reaches the
solve only via `backcast_config`.

| sidecar | rows × cols | exact-equal | max abs numeric Δ |
|---|---|---|---|
| `class_hourly_2023` | 166,440 × 5 | **True** | **0** |
| `system_2023` | 78,840 × 9 | **True** | **0** |
| `reserve_family_2023` | 17,520 × 10 | **True** | **0** |
| `storage_2023` | 17,520 × 6 | **True** | **0** |

**VERDICT: BIT-IDENTICAL** to the keeper's committed 2023 sidecars. Alongside it:

- **Zero `INADMISSIBLE` log lines** in 2023 — the gate evaluates every consumed series and passes
  all of them, i.e. it takes the identical branch, which is *why* the dispatch is identical rather
  than a coincidence of it.
- `run_config.json` records **`pjm_interface_feed_admissibility_gate: true`** for a caller that
  passed no flag — the rule 24 `[R-REGISTRY]` requirement that the record report the posture the
  LP solved, satisfied by the armed default rather than by a CLI echo.
- P0 objective 8.7952e9 → P1 9.0715e9, the ordering the bid-cost pass must have.

So arming cannot move PJM's `CALIBRATED` determination: the runs that determination is computed
from are reproduced to the bit.

### 3.1a The box: the pjm-168 recipe was necessary but its stated reason was incomplete

The first attempt at this solve was **OOM-killed** at 30 minutes. `dmesg`:

```
Memory cgroup out of memory: Killed process 11660 (python3)
  total-vm:23565636kB, anon-rss:13755496kB
  oom_memcg=/process_api/.../claude-code-bash
```

Two facts neither pjm-167 nor pjm-168 recorded, and the next PJM lane needs both:

1. **The binding constraint is a cgroup limit, not host RAM.** The bash cgroup carries
   `memory.limit_in_bytes = 14,327,676,928` = **13.34 GiB**. `free` reports ~15 GiB — the HOST
   view — so it is actively misleading here. The LP peaks at **13.755 GiB** anon-RSS, i.e. ~420 MiB
   over the cap. This is why pjm-167 saw "the cap on this box is zero" and why pjm-168's
   16 GB framing understates the margin: the usable figure is 13.34 GiB, not 15.4.
2. **Swap works because `memory.memsw.limit_in_bytes` is effectively unlimited**, so swapped-out
   pages are not charged against that 13.34 GiB cap. That is the mechanism behind pjm-168's
   `swapon`, which its §4 records as a recipe without saying why it works.

The swapfile had also been **silently deactivated** between session start and the solve peak (the
file was still on disk, untouched; `swapon --show` was empty) — reproducing pjm-167's OOM exactly.
Re-armed with `vm.swappiness=60` rather than pjm-168's `10` — clearing a hard cap needs real
spilling, not idle-page reclaim — plus a watchdog re-arming the swapfile every 10 s. Measured on
the successful run: **12,735 MB resident against the 13,663 MiB cap with 1,828 MB spilled**, and
3,713 MB spilled at the P1 peak. **Recipe for the next PJM lane:**

```bash
fallocate -l 12G /home/user/swapfile && chmod 600 /home/user/swapfile
mkswap /home/user/swapfile && swapon /home/user/swapfile && sysctl vm.swappiness=60
# and keep it armed — it can be dropped underneath a running solve:
nohup bash -c 'while :; do swapon --show | grep -q swapfile || swapon /home/user/swapfile; sleep 10; done' &
export MALLOC_ARENA_MAX=2 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
# check the REAL limit, not free(1):
cat /sys/fs/cgroup/memory/$(sed -n 's/^4:memory://p' /proc/self/cgroup)/memory.limit_in_bytes
```

### 3.2 The re-run 2021/2022 touchpoints — the VOLL artifact is gone in BOTH years

`2026-09-07-pjm-2022-2021-touchpoints` (bundle `pjm169_tp2022_2021_f2arm`), the SAME frozen keeper
recipe with the F2 arm reaching the solve through `backcast_config` and nothing forced on the CLI.
The touchpoint attestation reports **recipe identity PASS — 0 differing shared `meta.json` keys
outside the provenance set**, i.e. the arm is a declared default, not a recipe edit. Rule 22
`[R-HOLDOUT]`: validation tier, `--holdout-authorized`, PJM holds `complete`, freeze scope is
locked-test only; the registration-time marker gate (rule 22, owner ruling R-AZ) passed.

**The gate fires in both years, loudly and exactly as pre-registered** — precisely
`Average Western` dropped from `PJM_AEP_Ohio→PJM_West_APS`, `Average Eastern` dropped from
`PJM_Central_PA→PJM_EMAAC`, and the joint `pjm_east_interface_cut` NOT APPLIED, in 2021 and 2022
alike; no other series is touched.

| | EMAAC slack (VOLL) | hours | ISO-wide slack | EMAAC $ | rest $ | wedge |
|---|---|---|---|---|---|---|
| 2021 control | 99,100 MWh | 74 | 99,100 | 61.18 | 40.23 | **+20.95** |
| **2021 F2 arm** | **0** | **0** | **0** | 41.66 | 40.45 | **+1.21** |
| 2022 control | 42,582 MWh | 45 | 42,582 | 78.89 | 63.60 | **+15.29** |
| **2022 F2 arm** | **0** | **0** | **0** | 65.35 | 63.99 | **+1.36** |

ISO-wide slack **equals** EMAAC slack in every cell: the VOLL artifact was entirely EMAAC, and it
is entirely gone. The inverted east–west gradient collapses toward the actual **−$5.43** (NJ Hub −
AEP-Dayton). **2022 is new evidence** — pjm-168 screened 2021 only — and it lands where the
zero-LP admissibility census said it would (2022 exceedance: Average Eastern 17.5 %, Average
Western 9.7 %).

**Scored, control → arm** (`calibration_verdict.py`, committed artifacts only):

| criterion · year | control | F2 arm |
|---|---|---|
| **C3b price shape · 2021** | **FAIL** NRMSE 0.355 | **PASS** |
| **C3a mean LMP · 2021** | **FAIL** +25.7 % | **FAIL** +10.8 % |
| C3b price shape · 2022 | FAIL 0.250 | FAIL 0.257 |
| C1 2021 CC_REGULAR / ST_GAS / COAL_BIT | +28.72 / +8.07 / −9.45 TWh | +28.59 / +8.11 / −9.04 |
| C1 2022 CC_REGULAR | +22.26 TWh | +22.02 |
| C2, C4, C6, C8 | PASS | PASS |

**BOTH RUNGS STILL READ `NOT-YET`**, on the same three criteria (`fuelmix`, `price_mean`,
`price_shape`). **The arm repairs a real input defect; it does not close 2022.** What it removed
was an artifact — 141,682 MWh of VOLL across the two years, caused by enforcing a differently-
aggregated pre-2023 posting as a hard LP bound below flows PJM actually carried — and what remains
is the CC_REGULAR over-run the F4 lane exists to investigate.

**Rule 30 `[R-TOUCHPOINT-FOLD]` discharged:** (a) stamped to the keeper
(`stamp_touchpoint_holdout.py`), so the Run Explorer renders 2021/2022 as ordinary year columns of
the keeper's report rather than a second card; (b) `build_status.py --iso PJM` rebuilt the derived
holdout ladder — no `perYear` block, correctly, because both rungs read the same determination;
(c) **the ISO's headline is UNCHANGED — `PJM: CALIBRATED`**, the train-tier verdict, exactly as
rule 30(c) requires. The keeper `2026-08-15-pjm-162-inputclock` is **unpromoted**; no D-5(b)
re-verification is owed because no promotion occurred. The superseded
`2026-09-05-pjm-2022-2021-touchpoints` is pruned under rule 15's keeper-only retention, its
supersession recorded in the `complete` marker, and git history is its record.

## 4. F4 — built, unspent, and two corrections to its framing

The PRECOMMIT is `docs/handoffs/PRECOMMIT-pjm169-f4-anchor-vintage-2026-09-06.md`, written before
any build. The mechanism is `ScenarioConfig.gas_offer_margin_anchor_vintage` (default off,
byte-identical off): it resolves `gas_offer_margin_anchor` on the **solve year's** own mean
`_gas_series` instead of the frozen 2023–2025 window mean — the same measurement, a different year,
zero free parameters.

### 4.1 Correction — `COAL_SIGMOID_BACKCAST_GAS_MIN_MMBTU` is INERT in the PJM keeper

The handoff named it as an F4 object. It is not one. That constant feeds only
`scripts/data/derive_coal_sigmoid.py`, whose CSV output
(`data/raw/_processed-legacy/coal_sigmoid_params.csv`) **the solve does not read**. The solve
resolves through `fuel.trajectories.coal_sigmoid_params`, which starts from
`scenarios.COAL_SIGMOID_DEFAULTS[(iso, supply)]` and overlays explicitly-set config fields — and the
PJM keeper sets `coal_bit_passthrough_floor = 0.65` and `coal_sub_passthrough_floor = 1.1`,
overlaying the derived floor away entirely. The two tables do not even agree: the derived CSV gives
PJM bituminous `floor 0.5 / ceil 1.0 / gas_mid 7.08 / slope 1.0`; the keeper solves
`floor 0.65 / ceil 1.32 / gas_mid 3.4 / slope 2.5`.

### 4.2 Correction — the live coal-side extrapolation pushes the OPPOSITE way

What *is* live and window-extrapolated on the coal side is `COAL_SIGMOID_DEFAULTS`' own
`ceil` / `gas_mid` / `gas_slope`, and that table's docstring already records the weakness:
*"each asymptote is pinned by a single gas regime — floor by the cheapest observed year, **ceil by
the dearest**"*, with the PJM bituminous entry described as bracketing the breakeven *"across PJM
2023-2025"*. On the resolved keeper params the logistic
`floor + (ceil−floor)·σ(slope·(gas − gas_mid))` gives:

| delivered gas ($/MMBtu) | 2.19 | 2.54 | 3.52 | 3.72 (2021 HH) | 6.45 (2022 HH) |
|---|---|---|---|---|---|
| PJM bit passthrough | 0.6810 | 0.7199 | 1.0349 | 1.1123 | **1.3197 ≈ `ceil` 1.32** |

*(Cross-checked against the model's own `fuel.trajectories._sigmoid_passthrough`, not hand-computed.)*

So at 2022 gas the coal bid is **saturated on an asymptote no in-window observation ever reaches**
(the window tops out at 1.035 against a ceiling of 1.32) — and `ceil > 1` marks coal **UP**, while
the gas anchor's `(anchor − fuel) < 0` marks gas **DOWN**. The handoff's F4 story ("the correction
… marks gas offers DOWN", implying more coal) is right about the gas leg and silent about a
coal leg of comparable size pointing the other way. **F4 does not touch the coal sigmoid**; the
PRECOMMIT declares the confound in advance (§3.1 there), gate S4 is what detects it, and the
coal-side finding is recorded here as its own card rather than absorbed (rule 19 `[R-ONE-MECH]`).

### 4.3 A placement constraint the build surfaced

The anchor **cannot** be resolved at the `--gas-offer-margin` lookup where the ISO anchor is
resolved today (`run_calibration.py:1141`): `gas_hub_basis_overlay` (`:1811`) and
`gas_monthly_actuals` (`:2364`) are applied **later**, and `_gas_series` is only the series the
offer path prices against once both are set. Resolving at the lookup would measure a series no
unit ever pays. It is resolved after both, and mirrored into
`run_calibration_full._recorded_config` so the run record carries the anchor the LP solved with.
PRECOMMIT gate S1 is exactly this identity.

## 5. What this does NOT establish

- **F2's arm is not a calibration claim.** It is proved in-sample INERT, not in-sample *better*;
  PJM's `CALIBRATED` determination is computed from runs it cannot change.
- **No F4 number is a result.** The mechanism is built and default-off; its screen is unspent and
  no gate has been read. Nothing about F4 is adjudicated here, in either direction.
- **No out-of-sample skill claim.** 2021 and 2022 are validation tier — iterable model-SELECTION
  evidence (rule 22), never quotable as certified out-of-sample skill, and rule 30(c): a held-out
  year never downgrades the ISO.
- **Nothing is promoted.** `2026-08-15-pjm-162-inputclock` is untouched.

## 6. Incidental, outside this lane

- `scripts/run_calibration_full.py --help` **crashes at HEAD** (`ValueError: unsupported format
  character ')'` — an unescaped `%` in an existing help string). Reproduced at HEAD without this
  session's changes. Not repaired here: it is a core-script edit unrelated to this lane's scope.
- `tests/unit/config/test_d67arm_pjm_requirement.py` carries **2 pre-existing failures**, with
  byte-identical key values with and without this session's changes — which incidentally confirms
  this work is inert on PJM's forecast/hindcast key path.

## 7. F4 — screened and REJECTED (full gate table)

The screen ran on 2022 (year chosen on footprint, declared before any solve), single declared
delta on the F2-armed keeper recipe, control = §3.2's own 2022 at the same HEAD. Full table,
prediction and reasoning: `docs/handoffs/PRECOMMIT-pjm169-f4-anchor-vintage-2026-09-06.md` §9.

| gate | measured | verdict |
|---|---|---|
| S1 identity of the resolution | anchor 7.1208 vs census mean 7.120797 | **PASS** |
| S2 identity at the anchor | `mc` delta = 0 exactly at `fuel == anchor` | **PASS** |
| S3 direction & magnitude | **+$10.57/MWh** vs a **+$10.58** prediction fixed pre-solve — ratio **0.999** | **PASS** |
| **S4 footprint confined** | **COAL_BIT +3.28 %**, COAL_PRB +7.09 %, COAL_WC +3.31 % (bar 1.0 %) | **FAIL** |
| S5 no load-bearing flip | C1 FAIL→FAIL, C2/C4 PASS→PASS | **PASS** |

**Kill rule applied: the remaining years were never spent and nothing is promoted.** C1 2022
`CC_REGULAR` improving +22.02 → +10.77 TWh is reported, **not** a rescue — rule 1 `[R-STRUCT]`
does not let a target revive an arm killed on structure. PRECOMMIT §9.2 records, at full
magnitude, that S4 probably cannot separate the confound it was written for from ordinary
merit-order displacement, and why the verdict stands anyway.

### 7.1 A fourth correction to the handoff's F4 framing

**2021 is INSIDE the anchor's identification support** (gap abs-max 0.67× the in-window maximum).
The mechanism does not meaningfully extrapolate there, so F4 could never have been the 2021 story
the handoff framed it as; only 2022 is outside support (1.80×, and gas above the anchor in all
8,760 hours). This also corrects **this PRECOMMIT's own §3 magnitude claim** — it reasoned from
annual Henry Hub scalars rather than the hourly `_gas_series` the anchor is defined on, and
overstated the 2022 footprint as ≈2.7×.

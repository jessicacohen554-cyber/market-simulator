# FINDING — capx D67-ARM: the PJM published adequacy requirement is ARMED (owner ruling Q52); the re-solve lands the operand at **0.000 MW** in all four delivery years, every pre-declared prediction HITS, and the one G-DRIFT hunk that was LIVE moves exactly the way it was signed ex ante

**Lane:** capx D67-ARM, executing **owner ruling Q52** (capx ledger §3, r#47 amendment 1: *"ARM for
PJM"*). **Branch:** `claude/capx-d67-arm-pjm-requirement-4cebpf`, fresh off `origin/main` `131291b5`,
rebased once to `9911ff21` **between** the code PR and the solve, never during. **Date:** 2026-09-06.
**Model:** Opus. **DATA PROFILE:** `pjm`.
Companion: `PRECOMMIT-capx-d67arm-2026-09-06.md`, **pushed at `658a9fad` before any code change and
before any solve**. Instrument: `docs/handoffs/d67arm/grade_resolve.{py,json}`.
Charter evidence: `FINDING-capx-d67-2026-09-06.md` §4 / §6.1 / §7.1; arming precedent
`FINDING-capx-d57-2026-09-05.md` §8.1.

---

## 0. Result in one paragraph

The gate is armed for PJM through `_pjm_config` `default_scenario_overrides` — the D57/Q44 pattern,
**zero free parameters**, the shared dataclass default untouched — and the shipped posture was
re-solved once at HEAD over 2021–2025, PJM solo, sequential, HEAD-guarded. **The operand lands
exactly: `arm − published = 0.000 MW` in all four screened delivery years, and the requirement rows
reproduce D67 §7.1 to `+0.000` MW.** All four gradeable pre-declarations HIT, including the
unconditional P-A and the byte-identity P-B. The G-DRIFT audit found **one** LIVE hunk in the window
— capx D81 — and its effect is measured in exactly the direction the PRECOMMIT signed before the
solve: the 2024/25 clearing price moves **UP** (+$1,065.16/firm-MW-yr against D67 §7.1's arm) and the
later-year census positions rise **+0.69 / +0.56 / +0.49 pt**, because MW moved from the $0
price-taking residual into the priced stack. **Two pre-declarations are reported as MISSED and
neither is quietly repaired**: the PRECOMMIT called the three-`--no-` D57 control key "unmoved" and it
moved, and D81's own cache-epoch entry claimed a blast radius of zero committed bundles when the
registered `pjm-t1h` sidecar was in it. On the scoreboard the run is registered as the bare `pjm-t1h`
with the D57-era record preserved verbatim at `pjm-t1h-pre-d67`: **all 14 forecast invariants now
PASS** (the prior carried I7 FAIL + I12 WARN), retirements 18.702 → 18.058 GW against 15.062 actual,
recall 12/20 → 13/20, and **two additions bands flip FAIL → PASS while one flips PASS → FAIL** — the
last of which is a denominator artifact and is attributed as such rather than claimed.

---

## 1. The act

| # | what | where |
|---|---|---|
| 1 | `capacity_adequacy_requirement_published_by_iso: {"PJM": True}` added to `_pjm_config` `default_scenario_overrides` — the D57/Q44 pattern. The shared `ScenarioConfig` default stays `None`, so this is an **ISO override, not a declared default flip**: no `_CACHE_KEY_OPTIONAL_FIELD_DEFAULT_FLIPS` entry, no other ISO's key moves, every backcast key byte-identical. | `config/iso_configs.py` |
| 2 | Cache-epoch ledger entry **2026-09-06f** — a **KEY ADVANCE**, not a same-key invalidation, so nothing is silently re-interpreted. | `results/cache.py` |
| 3 | Registration re-key: `pjm-2021-2025-realized-t1h-d57-clearing` → **`pjm-t1h-pre-d67`** (verbatim, its own verdict standing — the D45-R / D57 convention); `pjm-2021-2025-realized-t1h-d67arm` → **`pjm-t1h`**. | `scripts/register_forecast_run.py` |
| 4 | Matrix: the PJM shard's `capacity_adequacy_requirement_published` cell → **`fc: "K"`**, keeper/gates stamp refreshed. PJM shard ONLY (rule 28d). `check_mechanism_matrix.py --base origin/main`: integrity OK, all six ratchets green. | `docs/codebase-site/data/mechanism-matrix/PJM.js` |
| 5 | CLAUDE.md Capacity Evolution bullet, on the D57 template. | `CLAUDE.md` |
| 6 | Tests: `tests/unit/config/test_d67arm_pjm_requirement.py` (12) + the D57 arming pin re-pinned. | `tests/` |

**Rule 21 `[R-DOF]`: zero free parameters.** The operand is PJM's own published whole-RTO Reliability
Requirement, reconciled byte-for-byte against the committed
`data/raw/capacity-market/demand-curve/pjm/pjm.csv` rows by test. Its vintage rule (the whole-RTO row,
never the `_frr_adj + ee_addback` RPM-only comparator) and its hold-last rule were both fixed in D67
before any solve and neither is selectable by a result. **The ruling is the identification.**
**Rule 25 `[R-ISO-SCOPE]`: a PJM posture** — generic in form, PJM-scoped by data; another ISO arms on
its own market's published table and stays `U`.

---

## 2. The re-key, graded against the PRECOMMIT — **one MISS, reported at full magnitude**

Measured through the shipped harness path (`build_config` → `apply_iso_scenario_defaults` →
`cache_key()`), the same one `test_pjm_iso_override_arms_forecast_only` uses.

| recipe | PRECOMMIT §2 declared | realized | grade |
|---|---|---|---|
| bare `pjm-t1h`, armed | `a9c66d8ea25acb9d` | **`a9c66d8ea25acb9d`** | **HIT** |
| explicit `--no-capacity-adequacy-requirement-published` | `15a723ba3b6dc856` (unmoved) | **`15a723ba3b6dc856`** | **HIT** |
| MISO / NYISO / NEISO / CAISO / ERCOT bare | all unmoved | **all unmoved** | **HIT** |
| PJM plain backcast | key unmoved, field coerced `None` | **unmoved, `None`** | **HIT** |
| explicit three-`--no-` D57 control | `c5ec052057905966` **(unmoved)** | **`61dfbc5c48af076b`** | **MISS** |

### 2.1 The miss, stated rather than repaired quietly

The PRECOMMIT's §2 table declared the D57 all-off control leg "unmoved". **It moved.** The reason is
structural and, in hindsight, obvious: that leg turns off the three D57 fields and says nothing about
the fourth, so after the arm it carries the published requirement **on** — it is no longer the D45-R
posture it names. This is the same thing that happened to D45-R's control when D57 armed; the
PRECOMMIT simply failed to anticipate it.

**The arm is nonetheless fully invertible, which is the property that actually matters** — measured,
not asserted:

| leg | at HEAD | + `--no-capacity-adequacy-requirement-published` |
|---|---|---|
| three `--no-` flags (D57 control) | `61dfbc5c48af076b` | **`c5ec052057905966`** ✔ (the D45-R key, restored exactly) |
| two `--no-` flags (D57 arm B) | `2d5bebd2bceed991` | **`6ba67a81ed4d2ed6`** ✔ (arm B, restored exactly) |

So every pre-arm bundle's recipe stays both **reachable** and **identified**. Both moved legs are
**re-pinned** in `test_capacity.py` rather than left ambiguous, with the four-flag inverses pinned
beside them, so a later lane cannot mistake the three-flag leg for the D45-R posture.

**The D65-B decomposition, re-verified at this lane's base.** Undoing exactly D65-B's two acts
(`ccs_retrofit_vom_adder = 8.0`, `ccs_retrofit_fixed_cost_co2_scaling = False`) restores D67's own
recorded literals digit for digit on **both** legs — control `aef81c84c4609c76`, arm
`3f4070767f29472a` — so the whole key move between D67's base and this one is D65-B's and nothing
else's.

---

## 3. G-DRIFT (rule 29 `[R-SCREEN]` clause (b)) — 37 files, **one LIVE hunk**

Window `b1155995` → `131291b5`, hunk by hunk, with the recipe posture **resolved** rather than
asserted. The full classification table is `PRECOMMIT-capx-d67arm-2026-09-06.md` §3; it is not
repeated here. Two things are worth restating:

**(a) The classifications are committed as ASSERTIONS, not prose.**
`tests/unit/config/test_d67arm_pjm_requirement.py::TestD67ArmGdriftPosture` pins them, so a later
default flip that silently makes one live fails a test instead of quietly changing the shipped run.
**Every one was then independently confirmed by the solve's own config dump**: `retirement_sector_gate`
False, `capacity_no_default_cap_convention_by_iso` None, `capacity_going_forward_bar_published_by_iso`
None, `mass_cap_tons_by_year` None, `voluntary_clean_demand_path` `'off'`,
`ccs_retrofit_available_year` 2028, `forecast_xyear_warmstart` **False** (so the P1 basis seed's
`xyear_warmstart is None` condition fails and the seed never arms — the §3.1 reading, confirmed from
the run rather than from the code alone).

**(b) `DEMAND_GROWTH_RATES` did not move in this window.** The hunk D67 §2.2 measured LIVE against its
own older base is *inside* D67's measurement, not a drift on it — the diff of `constants.py` over this
window contains exactly one `-` line, and it is the `---` header. The solve's own preamble confirms
the rate is the one D67 measured: *"dividing the weather-year load by the compounded growth over
[2021, 2024) (factor 1.2067)"* = 1.064645³.

### 3.1 The LIVE hunk — capx D81 — and its measured direction

`evolve.py` routes `_dated_exempt` from `exempt_unit_ids` to `exit_exempt_unit_ids`, so the pending
owner-filed dated block moves out of the D57 stack's $0 price-taking residual and into the priced
sell-offer stack. Both of D81's arming conditions hold on this recipe
(`fossil_announced_exits_enabled` True, `capacity_market_supply_clearing_by_iso` `{"PJM": True}`), so
the hunk is **LIVE** and D67 §7.1's census/price rows are *not* automatically this posture's.

**The PRECOMMIT signed the direction before the solve** (§3.2): MW moving from a guaranteed-$0 block
into a positively-priced offer is a weakly leftward supply shift, so the clearing price can only rise
weakly and the cleared quantity fall weakly, **never the reverse**. Measured:

| quantity | D67 §7.1 arm (pre-D81 base) | re-solve at HEAD | move | signed direction |
|---|---:|---:|---:|---|
| 2024/25 clearing price ($/firm-MW-yr) | 59,512.51 | **60,577.67** | **+1,065.16** | **UP** ✔ |
| 2024/25 uncleared | 19 | **20** | +1 | cleared quantity DOWN ✔ |
| 2023/24 census position | 1.055476 | 1.062327 | **+0.6851 pt** | ✔ |
| 2024/25 census position | 1.051736 | 1.057309 | **+0.5573 pt** | ✔ |
| 2025/26 census position | 0.993091 | 0.998023 | **+0.4932 pt** | ✔ |

The census rises because a higher clearing price means fewer economic exits, so more capacity
survives into the following year — the propagation channel, not a second mechanism. **P-E's falsifier
(a departure in the opposite direction) did not fire.**

D81's own finding measured this effect at **exactly zero** on the *unarmed* posture (its §4.1: price,
position and exits identical to all digits, because the coal-dominated block sits far below the
crossing). The PRECOMMIT explicitly refused to inherit that inertness, because the arm *moves the
crossing*. It was right to: under the arm the effect is small but **non-zero in every screened year
after the first**.

---

## 4. The re-solve, and the pre-declared predictions graded

**ONE solve.** `--iso PJM --start-year 2021 --end-year 2025 --vintage 2020 --retirement-rule pipeline
--entry-screen-diagnostics`, resolving the declared key **`a9c66d8ea25acb9d`** (confirmed in the
runner's own start line). PJM solo, years **sequential** (rule 12), wall **15 min 10 s**
(17:07:02 → 17:22:12; D67's envelope was 13/12 min on a warm tree — this ran on a freshly rebuilt
`data/clean`, 56/56 datatypes, no curation failures). **HEAD guard: H0 = H1 = `9911ff21`**, `RC=0`.

**Why no control solve** (rule 29(b)): the LIVE hunk earned one, but the three-leg decomposition
closes without it — D67 §7.1 is the clean arm effect (both legs at one base, so D81 and D65-B cancel),
the committed sidecar is the shipped prior, and `(re-solve) − (D67 §7.1 arm)` **is** the D81
measurement, obtained free. That is §3.1's table. Spending ~15 min of LP to re-derive a number the
arithmetic already isolates is the waste rule 29 exists to stop, and no gate is decided on it.

### 4.1 P-A (unconditional) — **HIT.** The operand lands at 0.000 MW

| DY | arm R @HEAD | D67 §7.1 arm R | Δ | published RR | **arm − published** |
|---|---:|---:|---:|---:|---:|
| 2022/23 | 163,268.900 | 163,268.900 | **+0.000** | 163,268.9 | **+0.000** |
| 2023/24 | 163,166.200 | 163,166.200 | **+0.000** | 163,166.2 | **+0.000** |
| 2024/25 | 164,107.600 | 164,107.600 | **+0.000** | 164,107.6 | **+0.000** |
| 2025/26 | 144,450.000 | 144,450.000 | **+0.000** | 144,450.0 | **+0.000** |

This was declared unconditional on the argument that the arm's R is the published table
(fleet-independent) and the control's is `peak × FPR` on a `_scale_demand` peak (also
fleet-independent), so **D81 cannot reach it**. The prediction carried a STOP; it did not fire. The
mechanism's central claim — that in every in-table delivery year the requirement is independent of the
model's peak — is confirmed on the shipped posture at HEAD.

### 4.2 P-B — **HIT.** 2022/23 is byte-identical

Arm census position **1.111265**, against D67 §7.1's **1.111265** — `+0.0000 pt`. 2021 runs no screen
(no `prior_results`), so the fleet entering the first screened year is pre-evolution and D81 cannot
have reached it. **P-D** (2021 runs no screen) also **HIT**.

### 4.3 P-C — **HIT, 4 of 4.** The signs are the charter's

| DY | move vs D67 §7.1's control (pt) | declared | grade |
|---|---:|---|---|
| 2022/23 | **−12.45** | FALL | ✔ |
| 2023/24 | **−5.59** | FALL | ✔ |
| 2024/25 | **+1.80** | RISE | ✔ |
| 2025/26 | **+5.58** | RISE | ✔ |

**This card moves two delivery years *away* from the published position and two toward it** — the
signature of a real operand rather than a fitted one, and exactly why it was screened structurally
(rule 1 `[R-STRUCT]`). The two FALL years remain a genuine cost, carried forward unchanged.

### 4.4 The clearing, reported at full magnitude, gated on nothing

| DY | requirement (MW) | census position | price ($/firm-MW-yr) | uncleared | how |
|---|---:|---:|---:|---:|---|
| 2022/23 | 163,268.900 | 1.111265 | 33,000.03 | 133 | `marginal_offer_sets_price` |
| 2023/24 | 163,166.200 | 1.062327 | 31,578.95 | 39 | `marginal_offer_sets_price` |
| 2024/25 | 164,107.600 | 1.057309 | 60,577.67 | 20 | `marginal_offer_sets_price` |
| 2025/26 | 144,450.000 | 0.998023 | 130,767.45 | 0 | `all_offers_clear_curve_sets_price` |

**G6 is still untestable at this configuration and this lane does not claim it cleared.** D62 remains
default-off and NOT armed, so 2024/25 is a marginal-offer year, where any requirement or census move
must move the price. D67 §7.1 established this; nothing here changes it.

---

## 5. The board: registered as `pjm-t1h`, FC rows at full magnitude

Registered through the single `register_forecast_run.py` path, forecast namespace, **never the
backcast registry** (rule 15). Canonical committed record:
`frontend/data/hindcast/pjm-2021-2025-realized-t1h-d67arm.json`
(`cache_key` `a9c66d8ea25acb9d`, `scored_at_sha` `9911ff21f42e`). The `registry/` and `runs/` sidecars
are gitignored and rebuilt by the Pages deploy, as CLAUDE.md specifies. Bundle parquets are not
committed — no `results/capacity-hindcast/` file has ever been tracked.

**Against `pjm-t1h-pre-d67` (the D57 record).** This is the TOTAL move — the arm **plus** D81 (D65-B
being provably inert below 2028) — and §3.1 separates the two.

| row | pre-d67 | **d67arm** | band |
|---|---:|---:|---|
| **invariants non-PASS** | I7 **FAIL**, I12 **WARN** | **none — all 14 PASS** | ✔ |
| retirements total (GW, actual 15.062) | 18.702 | **18.058** | FAIL → FAIL (err 0.242 → **0.199**) |
| `false_retire` (GW) | 9.490 | **8.065** | FAIL → FAIL (0.507 → **0.447**) |
| unit recall > 300 MW | 12/20 (0.60) | **13/20 (0.65)** | FAIL → FAIL |
| coal exits err_frac | −0.416 | **−0.340** | — |
| gas_cc exits err_frac | 4.366 | **1.081** | — |
| additions `by_tech.gas_cc` | 12.118 GW, err 0.421 | **8.118 GW, err −0.048** | **FAIL → PASS** |
| additions `shares.gas_cc` | Δ +0.114 pp | **Δ +0.035 pp** | **FAIL → PASS** |
| additions `shares.wind` | Δ +0.049 pp | Δ +0.076 pp | **PASS → FAIL** |

**The wind flip is a DENOMINATOR artifact and is attributed, not claimed.** Wind's model MW is
**3.000 GW in both runs** — as are solar (9.762) and storage (0.000). The *only* additions that moved
are `gas_cc` −4.000 GW and `gas_ct` −1.013 GW, which cut the total from 25.893 to 20.880 GW; wind's
*share* therefore rose from 0.116 to 0.144 with no wind change whatsoever. Solar's share improved by
the same arithmetic (Δ −0.165 → −0.075 pp). Reading the wind row as a wind regression would be wrong.

**I7 clearing deserves the same honesty.** The prior run failed I7 as *"2025: accredited firm 147,585
< requirement 150,605 MW"* — a 3,020 MW shortfall (the Y-22 §3.6 figure). Armed, the 2025/26
requirement is PJM's published **144,450 MW**, which the fleet clears. **The fleet did not gain 3 GW;
the bar became the published one.** That is the mechanism doing precisely what it says on the tin, and
it is also a partial answer to the question Y-22 §3.5 left open — *which* bar I7 should grade — but
this lane adjudicates nothing about I7's definition, threshold or seam, and none was touched.

**`gas_ct` additions overshoot in the other direction and are not hidden**: 1.013 GW built → **0.000**
against 0.442 actual, so err_frac moves +1.291 → −1.000. The band was FAIL before and is FAIL now.

---

## 6. What this lane does NOT claim

- **Nothing else arms.** No `ScenarioConfig` default moved, no other ISO, no backcast keeper, no
  marker or freeze file, no calibration determination. No adjudicated matrix cell was re-opened.
- **The two FALL delivery years stay a stated cost.** 2022/23 and 2023/24 end further from the
  published position than the control. Under rule 1 that is not disqualifying — a structurally
  correct mechanism stays in even when the residual worsens — and the root cause remains routed to
  the demand path (D67 §8(a): at HEAD this recipe still synthesizes its 2021–2023 screen peaks by
  de-growing 2024's measured load 10.8 / 7.6 / 4.0 GW below the load PJM actually served). **Not
  absorbed here.**
- **G6 remains untestable** at this configuration (§4.4).
- **The retirement bands are still FAIL.** The card improves the level (18.702 → 18.058 GW against
  15.062) without reaching the band. The named successor is unchanged: the CT / ST / oil E&AS operand
  (D57 §4), which is the D12 scarcity-basis lane's object.

---

## 7. Two corrections recorded against interest

1. **The PRECOMMIT's own three-`--no-` control declaration was falsified** (§2.1). Reported at full
   magnitude; both moved legs re-pinned with their four-flag inverses beside them.
2. **capx D81's cache-epoch entry `2026-09-06e` understated its blast radius.** It states *"no such
   bundle is committed or registered anywhere"*. The registered
   `pjm-2021-2025-realized-t1h-d57-clearing` sidecar declares **both** of that epoch's arming
   conditions (`capacity_market_supply_clearing_by_iso = {'PJM': True}` **and**
   `fossil_announced_exits_enabled = True`) at key `f0e050e820c1159a`. Its statement about D81's own
   deleted probes is correct as far as it goes; it missed the one registered bundle. **Corrected in
   place in `results/cache.py`, and repaired in substance by this lane's re-solve** — the shipped
   posture is now measured at a HEAD that carries D81. A records act: nothing re-scored, no verdict,
   gate, determination, marker or freeze file moved.

---

## 8. Governance attestation

| item | state |
|---|---|
| **PRECOMMIT before any code and any solve** | `658a9fad`, merged as part of the arming PR |
| **HEAD guard** | H0 = H1 = `9911ff21f42e6954a883799aa729875ce24f6845`; `RC=0` |
| **Rebase discipline** | once, **between** the code PR and the solve; delta re-audited before the solve — `git diff --stat` over `src/market_sim scripts/run_capacity_hindcast.py scripts/lib data/raw/_validation-source data/raw/reference` is **EMPTY** (D65-B-R Addendum E and D78-R addendum 2 were docs/test/probe-only), and all seven pinned keys re-measured unmoved |
| **Rule 21 `[R-DOF]`** | zero free parameters; the published table is the operand, the ruling is the identification |
| **Rule 19 `[R-ONE-MECH]`** | one object at one seam (`gross_adequacy_requirement_mw`) |
| **Rule 25 `[R-ISO-SCOPE]`** | PJM only; no other ISO's cell, key or shard touched |
| **Rule 22 `[R-HOLDOUT]`** | 2021–2025 hindcast, **forecast mode**; no out-of-training backcast year solved, scored or registered |
| **Rule 28 `[R-MECH-MATRIX]`** | PJM shard only (28d); `check_mechanism_matrix.py --base origin/main` integrity OK, all six ratchets green |
| **`check_cache_key_registration.py --base origin/main`** | green — 811 fields, 266 registered, all declared defaults matching HEAD; **no new field in this PR** |
| **`tests/regression/test_persisted_identity.py`** | 14/14 PASS — every backcast keeper byte-identical |
| **`tests/unit/model` + `tests/unit/config`** | at the arming commit, the red set was **byte-identical to the branch base's** (23 failed / 1398 passed / 1 error either side, same names); after the rebase onto `9911ff21` (which carries D65-B-R's key-pin repair) and the `data/clean` rebuild, **`tests/unit/model` is 1,446 passed / 0 failed** |
| **ruff** | `check` + `format --check` clean on every touched file |

### 8.1 Rule 27 `[R-PUSH]` blob verification — every pushed file ≥300 lines

Fetched back from the remote and compared line count **and** blob hash to local, before any further
commit. Remote tip `26474700`, identical to local HEAD at the time.

| file | lines local | lines remote | blob |
|---|---:|---:|---|
| `src/market_sim/config/iso_configs.py` | 2,049 | 2,049 | **match** |
| `src/market_sim/results/cache.py` | 1,331 | 1,331 | **match** |
| `scripts/register_forecast_run.py` | 1,300 | 1,300 | **match** |
| `CLAUDE.md` | 797 | 797 | **match** |
| `tests/unit/model/test_capacity.py` | 8,209 | 8,209 | **match** |
| `docs/codebase-site/data/mechanism-matrix/PJM.js` | 359 | 359 | **match** |
| `docs/handoffs/PRECOMMIT-capx-d67arm-2026-09-06.md` | 266 | 266 | **match** |
| `tests/unit/config/test_d67arm_pjm_requirement.py` | 190 | 190 | **match** |

No file ≥300 lines was rewritten from regenerated response content; every edit was a local `Edit` and
the pushed bytes are the on-disk bytes.

---

**Ruling executed. Nothing else arms.**

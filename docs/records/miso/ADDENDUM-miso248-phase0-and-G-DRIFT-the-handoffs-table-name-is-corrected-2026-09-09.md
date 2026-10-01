# ADDENDUM miso-248 (first) — **PHASE 0 (ZERO LP) AND `G-DRIFT`.** The handoff's named table is **CORRECTED ON MEASUREMENT**: `MISO_SEAM_LADDER_BY_YEAR` reproduces **192/192 EXACTLY** and is **out of scope**; the object is the 48 hourly SPP offsets, **48/48 mismatched**. The re-derive is a repair of a **HALF-APPLIED** change, and `G-DRIFT` finds **exactly ONE LIVE hunk** — the one this session is about

**Governs:** everything after it. Every rule applied below was fixed in
`PREREG-miso248-the-spp-hourly-ladder-rederive-on-the-repaired-clock-2026-09-09.md`, pushed with the
probe before either ran. Machine record `results/calibration/_miso248_spp_rederive_phase0.json`,
pushed **before** this prose. Probe HEAD stamp `10377aec`, tree clean; blob sha256/16 of every parsed
file is in the record's `P0_provenance` block, so no gate literal here is a hand-copied number from a
file that can move.

**Keeper unchanged: `2026-09-09-miso-247-p19-posture`**, CALIBRATED, C3c the single ledgered caveat,
DOF 41/2. **Rule 22 `[R-HOLDOUT]`: 2023–2025 only; no marker sought, inferred or granted.**

---

## 1. **`P-1` — THE HANDOFF NAMES THE WRONG TABLE, AND THAT IS NOW MEASURED RATHER THAN ARGUED**

The PREREG §1 declared this test and both of its outcomes **before** it ran.

| table | entries | mismatched at `atol=0.005` | max abs |
|---|---:|---:|---:|
| `MISO_SEAM_LADDER_BY_YEAR` (4 seams × 2 sides × 8 bands × 3 yr) | **192** | **0** | **0.000000** |
| **`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`** | **48** | **48** | **114.18** |

**So the handoff's *"re-derive `MISO_SEAM_LADDER_BY_YEAR`'s SPP entries"* names a table that
reproduces its derivation exactly and is not in scope.** The reason is structural and was read off
the code before the test: `derive()` couples the EIA-930 seam flow duration curve to the **MISO** hub
DA and never reads an SPP price at all, so `86e45462` cannot reach it. **The correction costs this
session nothing and is reported because it is true**, not because it helps.

The per-year divergence of the object that *is* in scope, at full magnitude:

| year · side | max abs | max rel (vs registry) |
|---|---:|---:|
| 2023 import | **62.38** | 0.408 |
| 2023 export | 45.38 | 1.100 |
| 2024 import | 30.51 | 0.218 |
| 2024 export | 19.11 | 0.972 |
| 2025 import | 48.71 | 0.144 |
| **2025 export** | **114.18** | **1.144** |

2023 import reproduces the predecessor's published `62.38` exactly — **EXPECTED**, since both read
the same committed registry against the same re-derive, and therefore corroboration of nothing. (The
predecessor's `0.689` max-relative is the same gap taken against the **re-derived** value; mine is
against the **registry**. Neither is wrong; they are different denominators and I name mine.)

**The miso-243 row-count pin HOLDS in all three years** (8,760 → 8,760): the divergence is not a
recurrence of the cross-year partial join.

## 2. **`P-2` — THE PREMISE IS NOT FALSIFIED, AND THE KEEPER IS CARRYING A HALF-APPLIED CHANGE**

PREREG §3 fixed the falsifying rule: identical series ⇒ session stops. They are not identical.
The solve-time anchor `measured_miso_spp_hub_prices` reads the very file `86e45462` rewrote, at HEAD
against the keeper's own basis `f29b7ab0`:

| year | hours moved | share | max abs Δ | mean new | mean old |
|---|---:|---:|---:|---:|---:|
| 2023 | **8,758 / 8,760** | 0.9998 | 203.94 | 24.2407 | 24.2365 |
| 2024 | 8,757 | 0.9997 | 410.55 | 21.3074 | 21.3023 |
| 2025 | 8,758 | 0.9998 | 277.69 | 28.0990 | 28.0837 |

**So at HEAD the keeper's applied SPP band offer `hub(t) + δ_k` is a MIXTURE — a repaired-clock
anchor carrying pre-repair-clock offsets.** The anchor is **ungated data**: no `ScenarioConfig`
field, no cache-key entry, so **every** future MISO solve carries it and the pre-repair posture is
not available to keep. That is the same structural shape as `_apply_simple_cycle_hr_floor` at
miso-247, and it is why this is a repair rather than a lever.

**AGAINST INTEREST, a discrepancy I am reporting rather than smoothing.** My `P-2` also records
`sorted_value_multiset_identical = false` in all three years, while `86e45462`'s own message states
the sorted value set is identical. **These do not contradict each other and I am not claiming a
defect:** that commit's identity is asserted *"on every common observation"*, whereas my test
compares the **full 8,760-hour** arrays, whose ends necessarily differ — a six-hour re-index fills
each year's tail from the next year's head and back-fills the leading edge. The tiny mean gaps
(24.2407 vs 24.2365) are the size a six-hour boundary swap would produce. **I did not verify the
commit's own identity on its own scope, and I do not assert it.**

## 3. `P-3` — THE RE-DERIVE, AND ALL THREE STOP CONDITIONS HOLD

`derive_spp_neighbour_hourly` at HEAD, on `joined.loc[[year]]`:

| year | import offsets | export offsets |
|---|---|---|
| 2023 | 10.62 · 25.73 · 43.07 · 62.47 · 83.98 · 90.56 · 90.56 · 90.56 | 0.24 · −10.16 · −25.87 · −56.57 · −153.04 · −166.65 · −166.65 · −166.65 |
| 2024 | 14.40 · 33.33 · 56.44 · 109.27 · 203.29 · 203.29 · 203.29 · 203.29 | 2.84 · −6.48 · −14.46 · −20.33 · −27.41 · −32.26 · −36.24 · −47.02 |
| 2025 | 16.86 · 37.50 · 67.75 · 140.17 · 182.10 · 232.18 · 252.79 · 290.12 | 0.34 · −10.42 · −18.49 · −28.01 · −45.96 · −69.66 · −140.45 · −140.45 |

**Row-count pin: HOLDS. Import rising / export falling: HOLDS, every year. No-wash
`max(export) < min(import)`: HOLDS, every year. Clamp notes: EMPTY.** `REDERIVE_ADMISSIBLE = true`.

**The structural character of the move, stated plainly: the repaired clock makes the SPP seam MORE
active in BOTH directions** — every import offset falls (imports cheaper) and every export offset
rises (exports pay more). Nothing about that was chosen; it is what pairing the two duration curves
on one clock produces.

## 4. `P-4` — THE FOOTPRINT AND THE SCREEN YEAR: **2023**

`F(year)` and the selection rule are PREREG §5, fixed before either number existed. Band capacity
**500.0 MW** (`interface_limit(SPP)/8`); `p(t)` is the keeper's **own committed P1 price at
`MISO_external`**; `hub(t)` is the HEAD anchor.

| year | **`F` (TWh of band-hour status flips)** | `max_k |Δδ|` | `ΔE_pred` (TWh) |
|---|---:|---:|---:|
| **2023** | **1.1835** | 62.38 | **+0.2085** |
| 2024 | 1.1580 | 30.51 | −0.2090 |
| 2025 | 0.8820 | 114.18 | −0.2820 |

**Selection rule applied: `argmax F` → 2023.** The top two are **2.15 %** apart, outside the 1 % tie
band, so neither tiebreak fires. **The residual was not consulted and no year's residual appears
anywhere in this record.**

**DISCLOSED, and it is inconvenient: 2023 is the ONLY year whose `ΔE_pred` is POSITIVE.** The screen
year was selected on the footprint statistic exactly as pre-registered, and the selection rule was
fixed before `ΔE_pred` was computed — but a reader is entitled to know that the screen's direction
will **not** generalise to 2024 or 2025, and that the full span (if reached) is where the other
direction is measured. **This is a limit on the screen's power, and it is the reason the screen is
STOP-only rather than promoting anything.**

**`G-1` takes FORM A** (`|ΔE_pred| = 0.2085 ≥ 0.05` TWh): same sign, and `|realised| / 0.2085 ∈
[1/3, 3]`.

**Declared power, again against interest.** `F` and `ΔE_pred` are computed on the keeper's **frozen**
internal price. The LP re-prices in response, so both are **first-order** quantities. They pick where
the mechanism is largest and set an order-of-magnitude bar; they are not a forecast, and a miss
inside a factor of three is all `G-1` claims to detect.

## 5. `G-DRIFT` — rule 29(b), from the NEW keeper's own `git.basis_sha` `f29b7ab0` to HEAD

`git diff f29b7ab0 HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib data/raw/_validation-source data/raw/reference` → 8 files, 5 commits. Every hunk
classified:

| hunk | classification | reason |
|---|---|---|
| **`86e45462` `actual_lmp_hourly_zonal_SPP.parquet`** | **LIVE** | It **is** the solve-time SPP anchor `measured_miso_spp_hub_prices` reads, and the keeper runs `miso_seam_neighbour_hourly_spp = True`. §2 measures it moving in 99.97 % of hours. |
| `86e45462` `actual_lmp_hourly_SPP.parquet` | INERT | SPP's own **scoring** sidecar; MISO's solve reads no SPP system LMP. |
| `86e45462` `actual_lmp.json` | INERT | **MEASURED, not read:** of the seven per-ISO blocks, **only `SPP` moved** — `MISO`, ERCOT, CAISO, PJM, NEISO, NYISO all byte-identical. |
| pjm-177 `netload_drag_min_run_persistence` (`scenarios.py`, `floors.py`, `run_calibration*.py`) | INERT | **Doubly.** (i) A `ScenarioConfig` flag, **default off** and **absent from the keeper's recorded config**; `_frac_for` returns `floor_frac` unchanged and the merit branch takes `merit_frac = floor_frac` when `persist_params is None`, so the off path is the pre-change path. (ii) MISO runs **`gas_st_netload_drag = False`** — the limb the flag touches is not armed at all. |
| `cd9d69e1` pjm-177 ruff format | INERT | AST-verified formatting. |
| capx D91 `pjm_seam_neighbour_hourly_ladder` cache-key registration + `scripts/lib/key_provenance.py` | INERT | Cache-key/provenance accounting. It changes which **key** a config hashes to, never what the LP builds; `key_provenance.py` is a governance census, not on the solve path. MISO runs `pjm_seam_neighbour_hourly_ladder = False`. |

**VERDICT: exactly ONE LIVE hunk, and it is the object of this session.** Rule 29(b) **form 4 is
FALSIFIED** — the keeper's committed bundle solved on the **pre-repair** anchor, so `arm − keeper`
would conflate the clock repair with the offset re-derive. **A control solve is EARNED**, on the
screen year alone, exactly as PREREG §8 fixed in advance. Its by-product is the session's
attribution: `arm − control` isolates the **offset re-derive**, `control − keeper` isolates the
**anchor clock repair** the keeper could not carry.

*(`_apply_simple_cycle_hr_floor`, which falsified form 4 for the previous session, is **not** a drift
hunk against this keeper — miso-247 solved with it live. That changes nothing: one LIVE hunk is
enough, and the audit is published in full rather than stopped at the first LIVE row.)*

## 6. Non-claims

1. **Nothing is promoted, registered or scored here.** Zero LP was spent on any number above.
2. **No tolerance widened, no exception list re-added, no test silenced.** The failing pin still
   fails at HEAD and is meant to.
3. **No residual, criterion, band or actual appears in any bar**; the screen year is chosen on the
   mechanism's own footprint and the trigger is the cited data change alone.
4. **Zero free parameters.** The estimator, depth grid, anchor hub and no-wash reconciliation are
   untouched; only the input series moved.
5. **`F` and `ΔE_pred` are first-order** and are used for nothing but year selection and the `G-1`
   bar.
6. **The commit `86e45462`'s own re-index identity is neither verified nor asserted here** (§2).

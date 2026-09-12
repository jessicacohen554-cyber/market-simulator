# SHARDREPORT — nyiso-228 SHARD A (TAIL)

**Session:** nyiso-228 · **Shard:** A (TAIL) · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/nyiso228-tail-span` · **Bundle:** `results/calibration/nyiso228_tail_span`
**Charter:** `docs/PRECOMMIT-nyiso228-amplitude-2026-09-12.md` §3.1 (authorized channel), §4 (STOP gates)
**Arm variable:** `offer_curve_by_group[*].peak` **×1.50** — frozen ex ante, one config across every
scored year, **never swept** (rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` amendment 2026-09-05).

---

# VERDICT — **THE SCREEN KILLED THE ARM. 2022 / 2023 / 2024 WERE NOT SOLVED.**

**Two pre-registered STOP gates tripped on the 2025 screen year: `G-MAG` and `G-ENERGY`.**
Per PRECOMMIT §4 and HARD STOP 4 the factor was **not** re-cut, not swept, and no second value was
tried. The remaining three years were not spent. This is the session's result.

**The mechanism's own footprint is the finding, and it is one-line falsifiable:**

> Making the peak band **1.5× more expensive** did not build a price tail — **it made the peak band
> withdraw.** Peak-band energy across the ten moved classes fell **3.06087 → 1.46652 TWh (−52.1 %)**,
> and model p99 rose only **+$3.38** against a pre-registered floor of **+$5**.

The top tranche does not set a higher clearing price when it is repriced; it **prices itself out of
the merit order** and is displaced by other classes' cheaper tranches. The band cannot form the
absent upper tail the PRECOMMIT §1.2 diagnosis is chasing, because raising its offer is
self-extinguishing. That is a structural property of the channel, measured, not a tuning outcome.

---

## 1. HARD STOPS — all four

| # | stop | required | observed | verdict |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | `55cd0a6c8c3e9d63c0184c6f66f0e9f65a490dbe` | **PASS** |
| 1b | never rebase / pull / sync | — | none performed; branch cut from the pinned SHA and never moved | **PASS** |
| 2 | peak file: exactly 10 classes, each exactly one key `peak` | 10 / 1 | 10 classes, every one `{"peak": …}` and nothing else | **PASS** |
| 3 | config signature in the **written** `run_config.json` | see below | all seven fields exact | **PASS** |
| 4 | factor frozen at ×1.50, no re-cut / sweep | — | **held** — two gates tripped and the factor was left alone | **PASS** |

### 1.3 — HARD STOP 3, read back from the solved bundle's own `run_config.json`

| field | required | observed |
|---|---|---|
| `nyiso_hub_gap_month_level` | `false` | `False` ✓ |
| `nyiso_import_reconciliation` | `true` | `True` ✓ |
| `offer_curve_by_group["CT_PEAKER"]["peak"]` | `6.0` | `6.0` ✓ |
| `offer_curve_by_group["ST_GAS"]["peak"]` | `6.3` | `6.3` ✓ |
| `offer_curve_by_group["CC_REGULAR"]["peak"]` | `3.375` | `3.375` ✓ |
| `offer_curve_by_group["CT_PEAKER"]["committed"]` | still `1.35` | `1.35` ✓ |
| `offer_curve_by_group["ST_GAS"]["committed"]` | still `1.05` | `1.05` ✓ |

---

## 2. THE GATE TABLE (PRECOMMIT §4) — screen year **2025**

Control throughout = the committed keeper `results/calibration/nyiso_fuelvintage_A`
(G-CTRL form 4). All prices P1, load-weighted over the five load zones, `NYISO_external` excluded.

| gate | test | control | arm | delta | band | verdict |
|---|---|---|---|---|---|---|
| **G-CONF** | exactly 10 values move, all `peak`, every ratio 1.5 @10 dp, protected bands byte-identical | — | 10 moved, all `peak`, all ratios `1.5000000000`, 0 protected moved | — | exact | **PASS** |
| **G-DIR** | model LW **p99** must rise | **177.200** | **180.580** | **+3.380** | > 0 | **PASS** |
| **G-MAG** | that rise within **$5–$120** | — | — | **+3.380** | 5 ≤ Δ ≤ 120 | **STOP** — $1.62 below the floor |
| **G-ENERGY** | ISO total model energy within **0.05 TWh** | **153.20633** | **153.14395** | **−0.06238** | ≤ 0.050 | **STOP** — 0.01238 TWh over |
| **G-CLASS** | no non-moved class moves > **1.0 TWh** | — | worst `ST_CHP` | **+0.05753** | ≤ 1.0 | **PASS** |

**G-MAG is the decisive kill** and it fails in the direction the PRECOMMIT itself named: *"a move
below $5 means the band is inert."* Measured, the band is not merely inert — it is **counter-acting**
(§4).

**G-ENERGY, stated precisely rather than waved through.** This is *not* an energy-balance violation:

| component | keeper | arm | delta |
|---|---|---|---|
| load served | 151.58975 | 151.58975 | **0.00000** (byte-identical) |
| energy slack | 0.0 | 0.0 | 0.0 |
| dump | 0.0 | 0.0 | 0.0 |
| storage charge | 0.98893 | 0.96147 | −0.02746 |
| storage discharge | 0.80423 | 0.78220 | −0.02203 |
| **generation total** | **153.20633** | **153.14395** | **−0.06238** |

Load, slack and dump are exactly conserved; storage net accounts for −0.0054 TWh and the residual
~0.057 TWh is **transmission loss**, which moves because the merit-order shift changes the internal
flow pattern against the `nyiso_zonal_loss_surface` one-way loss pairs. So the gate trips on a real
physical consequence of the mechanism, not on a solver artifact. It is reported as it landed and
**was not reinterpreted to pass** — the gate says "total ISO model energy", generation total is the
model's energy, and it is outside the band.

---

## 3. SOLVE LOG

| year | wall-clock | exit | note |
|---|---|---|---|
| **2025** (screen) | **332 s** (5 m 32 s) | **0** | the screen |
| 2022 | — | — | **NOT SOLVED** — gates tripped |
| 2023 | — | — | **NOT SOLVED** — gates tripped |
| 2024 | — | — | **NOT SOLVED** — gates tripped |

One earlier 2025 attempt exited 1 at 38 s before any LP, on a missing
`capacity-deliverability` clean partition (`nyiso_li_lcr_tsl=True` with no published Long Island
`transfer_security_limit`). Per charter that one partition was regenerated and the solve retried —
no other datatype was touched at that point, and no script was edited.

---

## 4. ITEM 7 — PEAK-BAND TWh AND SHARE PER MOVED CLASS (the mechanism's own footprint)

**This is the most important number in this report.** P1, 2025, from `class_band_hourly_2025.parquet`.

| klass | keeper peak TWh | arm peak TWh | Δ TWh | keeper share % | arm share % | Δ share pp |
|---|---|---|---|---|---|---|
| `CC_CHP` | 1.20403 | 0.57109 | **−0.63294** | 5.833 | 2.817 | **−3.016** |
| `CC_REGULAR` | 1.19182 | 0.30440 | **−0.88742** | 3.310 | 0.859 | **−2.451** |
| `CT_CHP` | 0.10856 | 0.05161 | −0.05695 | 6.309 | 2.928 | −3.381 |
| `CT_PEAKER` | 0.00100 | 0.00063 | −0.00037 | 0.068 | 0.038 | −0.030 |
| `ST_GAS` | 0.55546 | 0.53879 | −0.01667 | 5.861 | 5.370 | −0.491 |
| `COAL_BIT`, `COAL_PRB` | 0.0 | 0.0 | 0.0 | — | — | never dispatched in NYISO |
| `COAL`, `COAL_LIGNITE`, `COAL_WC` | — | — | — | — | — | class absent from NYISO dispatch |
| **TOTAL** | **3.06087** | **1.46652** | **−1.59435 (−52.1 %)** | | | |

**Four of the ten moved classes carry no NYISO dispatch at all** (`COAL`, `COAL_LIGNITE`, `COAL_WC`
absent; `COAL_BIT`/`COAL_PRB` at exactly 0.0), so the channel's real reach in this ISO is **five gas
classes**, and 96 % of the measured footprint move is `CC_CHP` + `CC_REGULAR`.

**The sign is the result.** The PRECOMMIT sized ×1.50 expecting the peak band to *price* the tail.
Instead every moved class's peak band **shrank**, `CC_REGULAR`'s by 74 %. The band's share of its own
class fell in all five live classes.

### 4.1 — where the displaced energy went (ITEM 6 delta, P1 2025 annual TWh)

| klass | keeper | arm | Δ | |
|---|---|---|---|---|
| `CC_REGULAR` | 35.33547 | 34.76952 | **−0.56595** | moved |
| `CC_CHP` | 20.39667 | 20.02655 | **−0.37012** | moved |
| `ST_GAS` | 9.33310 | 9.88494 | **+0.55184** | moved |
| `CT_PEAKER` | 1.31794 | 1.51281 | **+0.19487** | moved |
| `CT_CHP` | 1.68395 | 1.72790 | +0.04395 | moved |
| `ST_CHP` | 1.44692 | 1.50445 | +0.05753 | **not moved** (G-CLASS worst) |
| `import` | 19.35766 | 19.37606 | +0.01840 | not moved |
| `oil` | 1.28353 | 1.29065 | +0.00712 | not moved |
| `nuclear` / `hydro` / `wind` / `solar` / `biomass` / `OTHER` | — | — | **0.00000** | not moved, exactly |
| **ISO total** | **153.20633** | **153.14395** | **−0.06238** | |

A clean intra-fossil substitution: CC gives up 0.936 TWh, ST_GAS + CT_PEAKER take 0.747 TWh, and
every zero-marginal-cost and baseload class is untouched to five decimal places. Merit-order movement
across classes is condition (d)'s **intended** effect — but it moved *volume between fossil classes*
rather than *price into the tail*.

---

## 5. ITEM 4 — PRICE STATISTICS (P1, 2025, LW over the five load zones)

| stat | keeper | arm | Δ |
|---|---|---|---|
| mean | 58.357 | 60.008 | +1.651 |
| p95 | 124.736 | 126.354 | +1.618 |
| **p99** | **177.200** | **180.580** | **+3.380** |
| max | 313.944 | 315.746 | +1.802 |
| hours > $150 | 220 | 233 | +13 |
| hours > $200 | 43 | 57 | +14 |
| **hours > $300** | **3** | **4** | **+1** |

**Convention note.** `mean` is the charter's convention — the hourly load-weighted series, then a
simple mean over the 8,760 hours; that reproduces the charter's 58.36 exactly. The
demand-weighted-over-hours variant reads 61.598 (keeper) → 63.085 (arm). Every other statistic is
convention-independent. **My pipeline reproduces the charter's committed keeper comparators exactly**
(p95 125, p99 177, max 314, h150 220, h200 43, h300 3), which is what validates the differencing.

**Against PRECOMMIT §5 prediction 2** (C3c model h>$300 for 2025: **3 → 8–35**): the arm delivered
**4**. The prediction is **falsified** — by a wide margin, in the one year chosen precisely because
the band's footprint was largest there.

---

## 6. ITEM 5 — RESERVE FAMILIES (P1, 2025)

| family | h dual>0 | max dual | h shortfall>0 | max shortfall MW |
|---|---|---|---|---|
| `nyca_10min_total` | 0 → 0 | 0.000 → 0.000 | 0 → 0 | 0.0 → 0.0 |
| `nyca_10min_spin` | 0 → 0 | 0.000 → 0.000 | 0 → 0 | 0.0 → 0.0 |
| `nyca_30min_total` | 0 → **1** | 0.000 → **0.000** | 0 → 0 | 0.0 → 0.0 |
| `east_10min_total` | 2 → **10** | 1.876 → **3.201** | 0 → 0 | 0.0 → 0.0 |
| `seny_30min_total` | 8 → 7 | 40.000 → 40.000 | 7 → 7 | 424.354 → **266.458** |
| `nyc_10min_total` | 48 → **69** | 25.000 → 25.000 | 33 → 37 | 460.515 → 457.318 |
| `nyc_30min_total` | 25 → 22 | 25.000 → 25.000 | 24 → 19 | 481.115 → 477.918 |
| `li_10min_total` | 0 → 0 | 0.000 → 0.000 | 0 → 0 | 0.0 → 0.0 |
| `li_30min_total` | 0 → 0 | 0.000 → 0.000 | 0 → 0 | 0.0 → 0.0 |

**PRECOMMIT §1.3's central finding is unchanged and now re-confirmed under the arm:** the three
NYCA-wide families — the only ones whose published penalty is in the **$750–775** range — still
never price. `nyca_30min_total` gains a single hour at a dual of exactly 0.000, i.e. it is touched
but not binding. The ceiling remains the offer stack plus a **$25–40** locational adder. **Moving the
offer surface does not reach the NYCA-wide scarcity families**, which is independent corroboration
that the absent tail is not an offer-curve object.

---

## 7. ITEM 8 — METRICS AND DIAGNOSTICS

* **`metrics.json`: NOT WRITTEN.** The replay driver writes it at the end of a completed span; this
  bundle is a single screen year that stopped at the gates. There are no headline rows to quote and
  none are invented here. **The parent scores C3a/C3b**, as the charter assigns.
* **`legitimacy_diagnostics.json`: REGENERATED ✓** (21,238 bytes, 2025, schema/bundle/iso/years/
  diagnostics/gates). The driver reported `legitimacy diagnostics gate FAIL on the replayed bundle`
  — expected on a one-year bundle whose span gates cannot be evaluated, and reported here rather
  than suppressed. D-10 free-class rescore PASSed (2/2 NYISO wind/solar rows ride the L1
  delivered-outcome bound, advisory-only).
* **G-NONTARGET (C1/C2) was not evaluated** — it needs the scorer, which is the parent's job, and
  two gates had already tripped.

---

## 8. WHAT THIS MEASURES FOR THE MATRIX (parent's stamp to make — this shard edits no matrix file)

The authorized `offer_curve_by_group.peak` channel at ×1.50 is, for NYISO:

* **directionally correct but an order of magnitude too weak on p99** (+$3.38 against a $5 floor), and
* **self-limiting by construction** — the repriced band loses **52 %** of its own energy, so the
  channel's price effect is throttled by its own volume response. A larger factor would shrink the
  band further, not build more tail; the response is **not** monotone in the way the sizing assumed.

Taken with §6 (the $750–775 NYCA families still never bind) this is a **second independent line of
evidence** that PRECOMMIT §1.2's absent upper tail is a **reserve/scarcity-pricing object, not an
offer-surface object**. nyiso-222's uniform ×1.05 already showed a lift raises the mean without
building a tail; this shard shows the **peak-band-only** variant does not build one either, and adds
*why* — the band withdraws.

**This is a measurement, not a promotion candidate.** It is reported exactly as it landed.

---

## 9. RULE COMPLIANCE

* **Rule 29 `[R-SCREEN]`** — screen year 2025 was named in the PRECOMMIT *before* the solve on the
  peak band's **own measured footprint** (largest there), never on the residual. The gates are
  STOP-only and structural; none reads C3a/C3b/C3c or the target residual. The screen killed the arm
  and the remaining three years were not spent — which is the rule working as designed.
* **Rule 1 `[R-STRUCT]` condition (c)** — the factor was **not** re-cut after the miss. No second
  value was solved, considered as a solve, or written anywhere.
* **Rule 31 `[R-RETAIN]`** — **nothing was deleted.** The full 42 MB bundle (including the
  gitignored `dispatch/`, `unit_hourly_2025.parquet`, `network_2025.parquet`, `floors/`,
  `btm/system/flows/storage.parquet`) is **on local disk in this container** and will **not survive
  container reclamation**. See §10.
* **Commit scope** — `git add` was run **without `-f`** on the bundle path. The repo's own
  `.gitignore` already implements exactly the rule-15 slim set (5 `hourly/` sidecars + `meta.json` +
  `run_config.json` + `legitimacy_diagnostics.json` = **8 files, 1.8 MB**). Forcing past it with
  `-f` would have swept in 42 MB of dispatch/unit-level parquet — precisely the "full bundle
  directory" pack that CLAUDE.md's *Git & Pushing* section does not license for `git push`, and
  precisely what rule 31 says `.gitignore` is there to keep out of the repository. The `-f` in the
  shard prompt guards against a blanket `results/` ignore that does not exist here; the slim set is
  the intent and the slim set is what was committed.
* **Forbidden list** — nothing under `src/` or `scripts/` was edited; the two data problems were
  solved by **environment** (`PYTHONPATH`) and by **regenerating one named partition**. No
  `dashboard_add_run` / `build_manifest` / `build_status` / `prune_iso_runs`, nothing under
  `frontend/data/backcast/**`, no `.gitignore` / `CLAUDE.md` / PRECOMMIT / matrix / calibration-log
  edit, no other shard's files, no PR, no deletion.

---

## 10. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — **FOR THE PARENT / OWNER, ASKED EXPLICITLY**

**This shard recommends against promoting arm A, and is not acting on that recommendation.**

The 2025 screen bundle is solved and on local disk **in full**. Only the 1.8 MB slim set is pushed;
the remaining ~40 MB (dispatch, unit-level hourly, network, floors) exists **only in this ephemeral
container** and is gone when it is reclaimed. Nothing has been deleted and nothing will be.

**If the owner wants arm A's 2025 taken further** — registered, re-scored with C1/C2/C3a/C3b/C3c, or
its unit-level dispatch inspected — **say so while this container is alive.** Re-solving 2025 later
costs **~5 m 32 s** of LP; the full 2022–2025 span the gates stopped costs roughly **~22 min**.

**Answer needed on:** (a) keep or drop the 2025 screen bundle; (b) whether the ×1.50 result should be
registered as a rejected probe; (c) whether the §8 reading — that the absent tail is a
scarcity-pricing object rather than an offer-surface one — should re-point this session's remaining
effort.

# ADDENDUM to PRECOMMIT-ercot254 — **G-1 FIRED**, on a gate-specification error, and the West is measured INERT (ercot-254)

> Written **after** the zero-LP gates ran and **before** either LP solve. The
> PRECOMMIT is **not rewritten** — it says what it says, G-1 as written fired, and
> that record stands. This addendum records the diagnosis, the corrected scope,
> and a substantive fact the gate turned up. Rule 29 `[R-SCREEN]` clause 0: a
> pre-solve gate that fires is doing its job, and the correction is committed
> before the arm is solved so it cannot be written to fit a result.

## 1. What the gates read (ERCOT 2025, zero LP, arm vs control on the reconstructed fleet)

| gate | measured | STOP threshold | verdict |
|---|---|---|---|
| **G-1 IDENTITY** | max \|residual\| **0.6151 $/MMBtu** | > 1e-9 | **STOP — FIRED** |
| G-2 CONFINEMENT (non-gas) | 0.000e+00 | > 0 | PASS |
| G-2 CONFINEMENT (gas max \|Δ\|) | 0.6151 $/MMBtu | > 0.62 | PASS |
| G-3 LEVEL | 3.1552 → 3.1565, **Δ +0.0013 $/MMBtu** | > 0.05 | PASS |

Hour-weighted mean \|Δ\| = **0.2412 $/MMBtu**, reproducing the PRECOMMIT §2
footprint for 2025 to four decimals. Monthly level vector Jan..Dec: +0.440,
−0.173, −0.317, −0.006, +0.318, +0.239, +0.225, +0.215, −0.001, −0.120, −0.203,
−0.615.

## 2. Why G-1 fired — the gate was mis-scoped, not the arm

The residual is **perfectly localised**:

| zone | gas rows | rows with residual | max \|residual\| |
|---|---|---|---|
| Houston | 617 | **0** | 0.0000 |
| North | 362 | **0** | 0.0000 |
| Northeast | 20 | **0** | 0.0000 |
| South | 336 | **0** | 0.0000 |
| South_Central | 392 | **0** | 0.0000 |
| **West** | **97** | **97** | **0.6151** |

**1,727 of 1,824 gas rows satisfy the identity EXACTLY (0.0000).** On the 97 West
rows the residual equals the *whole* monthly level delta in every month — 0.4395 /
0.1734 / 0.3168 / 0.0062 / 0.3178 / 0.2386 / 0.2253 / 0.2146 / 0.0012 / 0.1199 /
0.2033 / 0.6151 against a delta vector of 0.440 / 0.173 / 0.317 / 0.006 / 0.318 /
0.239 / 0.225 / 0.215 / 0.001 / 0.120 / 0.203 / 0.615 — so `arm − control` is
**exactly 0.0** on every West row, in every hour. A sample West row confirms it
directly: `CC_CHP_West_p52176_econc00` prices at **3.0289 $/MMBtu in both arms**.

The cause is the recipe, not the change. `apply_ercot_west_netload_gas_shape` runs
**after** `apply_ercot_zonal_gas_basis` and **owns the West/Panhandle level
outright**: it re-derives those rows from the measured annual Waha basis and the
cited firm delivered level as a two-regime net-load step, discarding whatever level
the basis put there. Its own docstring says so — it is the "structural replacement
for the flat `ercot_gas_delivered_floor_basis` scalar". So a level term applied to
the West is overwritten downstream **whether it is annual or monthly**.

G-1 asserted the identity on the **final** fuel array across **all** gas rows. That
was a claim about the whole chain, and the chain contains an applier that was never
identity-preserving on the West and never claimed to be. The gate tested something
the recipe does not support. **The arm did exactly what its arithmetic says on
every row it owns.**

## 3. Corrected G-1, scoped and declared BEFORE the solve

> **G-1′ IDENTITY (scoped).** On the rows `apply_ercot_zonal_gas_basis` owns — every
> ERCOT gas row **outside** West/Panhandle, whose level the downstream net-load
> shape does not re-derive — the armed delivered-gas array equals the unarmed array
> plus `_expand_monthly_to_hourly(monthly − annual)`, unit-hour by unit-hour.
> **STOP if any \|residual\| > 1e-9 $/MMBtu.**
>
> **G-1″ WEST INERTNESS (new, and a stricter claim than the original).** On the
> West/Panhandle rows the arm must be **exactly inert**: `max |arm − control| = 0`.
> **STOP on any nonzero West delta**, which would mean the level term is leaking
> past the applier that owns those rows.

Measured against the run already in hand: **G-1′ PASSES** (1,727/1,727 rows,
residual 0.0000) and **G-1″ PASSES** (West delta exactly 0.0, established by the
residual equalling the full delta in all twelve months and confirmed on the sample
row). Nothing is re-run to obtain this; it is a re-reading of the same measurement
under the corrected scope, and the corrected scope is fixed here before any LP.

## 4. The substantive fact this turned up, and why it is good for the screen

**The repair does not touch the West — and the West is one of the two zones that
escaped the 2021 contamination in the first place.** `FINDING-ercot254` §1a records
that `data/raw/ercot_zonal_gas_hub.csv` has **no 2021 West/Panhandle row at all**,
and §5 records that the 2021 West `neg_day_freq` is absent so the net-load step
falls back to a **2024** default of 0.42 and produces **inverted** regimes (deep
$7.45 above firm $3.41). That is a second, separate 2021 defect, and the PRECOMMIT
§6 declares it explicitly **not touched** in this session.

The West inertness measured here is what keeps those two defects apart. The arm
stays a genuine single delta: it repairs the level anchor on the 94.7 % of gas rows
that anchor owns, and it leaves the West exactly as the incumbent recipe has it —
so the screen measures one mechanism and the West defect stays available to be
adjudicated on its own evidence, under its own charter, in its own session.

## 5. Unchanged

The post-solve gates G-4 through G-7 are untouched, as are their thresholds. The
screen remains **STOP-only** — it may kill this arm and may never promote it — and
**no gate is read against C1 or C3a** in either direction. The screen year is still
2025, still named on the mechanism's own footprint. The control is still G-CTRL
form 2, a same-HEAD 2025 solve one flag apart, for the G-DRIFT reason the PRECOMMIT
§3 gives.

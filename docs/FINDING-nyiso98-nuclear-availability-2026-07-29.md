# FINDING nyiso-98 — `nuclear_unit_availability` (NYISO): the queue's defect was a benchmark artifact; the real one closes

**Lane:** dispatch-matching (matrix §5.5 item 7, opened by the nyiso-92 charter).
**Pre-registration:** `docs/PREREG-nyiso98-nuclear-availability-2026-07-29.md`,
committed before the extract was derived and before any solve.
**Instruments:** `scripts/probes/nyiso98_nuclear_availability_provenance.py`
(no-LP, build-time gate), `scripts/probes/nyiso98_ab_compare.py` (A/B).

---

## 1. The premise correction (measured first, and it inverts the queue entry)

The lever queue states: *"nuclear r_day drops 0.84 → 0.50/0.51 in 2024–25
(refuel/outage timing) on 26–28 TWh"*. Those numbers reproduce exactly on the
keeper (`nyiso96_ctamort`): **0.839 / 0.504 / 0.511**.

They are scored against EIA-930 `NYIS` `NG: NUC`, and **that series posts
exactly 0.0 MW in long contiguous blocks**: 1,179 h in 2023 (50 all-zero days),
380 h in 2024, 117 h in 2025. These are zeros **in the source parquet** — not
NaN, and not produced by the repo's `_eia_hourly_frame_filled` gap-bridging
(which emits NaN).

**Falsified against NRC on all 81 gap days, all three years — zero survive.**
Every gap day has at least one NY reactor at **100 %** of licensed thermal
power. Worked example, 2023-04-14…20: FitzPatrick 100 % and Nine Mile Point 2
100 % (2,127 MW online) against a metered 0.0 MW for all 24 h of each day. A
four-reactor fleet with a unit at power cannot meter zero.

Masking gap days (a day posting 0.0 MW in ≥1 hour):

| year | as-published | gap-CLEAN | n clean |
|---|---|---|---|
| 2023 | 0.839 | **0.446** | 309 |
| 2024 | 0.504 | **0.833** | 344 |
| 2025 | 0.511 | **0.534** | 356 |
| mean | 0.618 | **0.605** | |

**The ordering inverts.** 2023's "good" 0.84 is inflated by 50 phantom
zero-days sitting in the model's low-CF months (Mar 0.86, Apr 0.74); 2024's
"bad" 0.50 is deflated by its own gap block. The real skill is **worst in
2023**, good in 2024, mediocre in 2025 — so the queue's stated defect (*a drop
in 2024–25*) does not exist as described.

Same cause, second artifact: the nyiso-92 component table's nuclear
`27.49/24.00 TWh` (2023) reads as **+14.5 %** model over-production. On
gap-clean days the model is **−2.1 %**. There is no nuclear level defect, and
none was ever chased — but the number is on the record and is corrected here.

**This did not close the item.** A genuine daily-timing deficit remains on
clean days (0.446 in 2023, 0.534 in 2025) and a per-reactor refuel overlay is
exactly its mechanism. The target was **re-based onto gap-clean r_day** in the
pre-registration, before the arm was built.

## 2. Source adjudication (rule 13, before the derive)

NYISO unit outage schedules are CEII (the same wall as PJM's masked
`unit_code`); EIA-923 is the level anchor and cannot see intra-month timing;
nuclear does not report to CEMS; and EIA-930 `NG: NUC` is **forbidden as an
input** — it is the scored outcome, and it is the contaminated series above.
**NRC daily Power Reactor Status** is selected: public, per reactor, and
covering all four NY reactors **365/366 days in every year**.

Admissibility: percent of licensed thermal power is a physical availability
event — the rule-13 class of the CAMPD fossil outage windows and of ERCOT's
live keeper overlay. Forward analogue: refuel cadence → `NUCLEAR_MONTHLY_CF` /
refuel-block scheduling. **Zero fitted scalars** — `EVENT_RAW_MAX` 0.90, cap
1.0, `SCALE_CLIP` 1.25, `WEDGE_TOL` 0.01 are inherited frozen from the ERCOT
deriver, unmodified (rule 23; the PJM extract still reproduces byte-for-byte
under `--check`).

**Stated tension, not hidden:** nuclear is a flat must-run price-taker, so an
availability overlay on it sits close to an output overlay. What keeps it
admissible is that the **level** is owned by the independent EIA-923 anchor and
never by the scored series — NRC supplies **timing only**.

## 3. The PJM precedent, and why it does not repeat here

pjm-nuc-1b (`docs/DIAGNOSIS-pjm-c3c-summer-tail-2026-07.md` §8.2.1) built this
same overlay and **stopped at its build-time gate**: reconciling to the 923
anchor redistributes event-day energy onto near-full pool days, and PJM's
target — the level at 22 scarcity tail hours — *is* near-full pool days, so net
recovery came out **−72 MW** against a ≥ +75 MW pre-commitment.

NYISO's target is different in kind: **within-year daily timing**, which the
anchor is structurally neutral to (it rescales pool days uniformly inside a
month). Gate **G2** was written to detect the PJM failure mode directly.

## 4. Build-time gates — all three PASS

Derived extract: `data/raw/nuclear-availability-NYISO.csv`, 4,384 reactor-days,
4 reactors. **All 36 months reconcile inside `WEDGE_TOL`** (worst −0.62 %), so
unlike PJM **no month is dropped** and the overlay is live on every day of all
three years.

| gate | pre-registered threshold | measured | verdict |
|---|---|---|---|
| **G1** raw-NRC lift, 3-yr mean gap-clean r_day | ≥ +0.10, no year regresses | **+0.304** (+0.435 / +0.118 / +0.359) | **PASS** |
| **G2** reconciled retention of the raw lift | ≥ 70 %, > 0 every year | **104 %** (+0.316; worst year +0.126) | **PASS** |
| **G3** max abs annual ΔTWh | < 0.5 % | **0.14 %** | **PASS** |

Gap-clean nuclear r_day in extract arithmetic:
**0.446 / 0.833 / 0.534 → 0.885 / 0.960 / 0.917** (mean 0.605 → **0.921**).

G2 exceeding 100 % is not an anomaly: the anchor corrects the NRC
thermal-%-of-nameplate level *within each month*, a level correction that
slightly helps daily correlation on top of the timing it preserves. The PJM
outcome (negative retention) is absent, for the reason §3 predicted.

What the mechanism actually restores is visible per unit: Nine Mile Point 1 was
out **2023-03-13 → 04-19** and **2025-03-17 → 04-04**; Nine Mile Point 2 out
Mar-2024; FitzPatrick and Ginna out Sep/Oct-2024. The smear cannot represent
any of them — it spreads a one- or two-unit outage across all four reactors as
a fleet-wide March CF of 0.86.

## 5. Live-mechanism check (nyiso-89 §4a), before any result was read

Measured on the fleet arrays directly, off the solve path:

| year | availability cells changed | changes outside nuclear rows | max abs delta | min_gen cells changed |
|---|---|---|---|---|
| 2023 | 29,088 | **0** | 0.970 | 29,088 |
| 2024 | 32,184 | **0** | 0.900 | 32,184 |
| 2025 | 26,136 | **0** | 0.960 | 26,136 |

Available nuclear energy moves −0.01 / −0.02 / −0.14 % — G3 reconfirmed on the
LP's own arrays. The flat must-run floor tracks the overlay cell-for-cell.

In-solve, the arm and control diverge at the P0→P1 commitment seam (2023 gas
bridge: 5,062 → 5,080 `gas_st` unit-hours floored), so the delta propagates
past the fleet build.

**Disclosed:** the solve logs the overlay **twice** per year — once applying
**0** reactors, once applying **4**. The 0-reactor call is
`fleet.assembly.bins_to_fleet`'s array build over the **fossil CAMPD bins
only**, before `build_base_fleet` adds nuclear from EIA-860; it is not the LP's
fleet. The 4-reactor call is `run_calibration.py::run_year`'s build, and the
LP fleet independently carries the matching identifiers (`2589_1`, `2589_2`,
`6110_1`, `6122_1`). Wiring is pinned by tests (the flag must be *applied*, not
merely recorded; the runner must forward and record it; the cache key must
move — an unregistered field would have served the arm the control's cached
results).

## 6. Solve result

*(filled in below from the registered A/B pair)*

## 7. Verdict

*(filled in below)*

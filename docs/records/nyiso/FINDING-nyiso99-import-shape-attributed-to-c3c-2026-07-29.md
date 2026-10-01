# FINDING nyiso-99 — import hourly shape: the benchmark is CLEAN, the defect is REAL, and it is C3c's

**Lane:** dispatch-matching (matrix §5.5 **item 9**, opened by the nyiso-86 §3 /
nyiso-92 charter).
**Pre-registration:** `docs/PREREG-nyiso99-import-audit-demand-dropout-2026-07-29.md`,
committed and pushed before any solve.
**Instruments:** `scripts/probes/nyiso99_import_benchmark_provenance.py`
(no-LP; sections `census` / `falsify` / `baseline` / `attribute`).
**Keeper at entry and exit of the item-9 adjudication:**
`2026-07-29-nyiso-98-nucavail`, DETERMINATION NOT-YET, C3c sole blocker.

**Verdict: item 9 is CLOSED — no import-side mechanism is admissible, because
the defect is not in the import node.** Separately, the audit found a real
input bug and this session fixes it (§4).

---

## 1. The audit, run first — and this time the queue's premise survives

nyiso-98 established that EIA-930 `NYIS` posts reporting gaps as **exactly
0.0 MW in the source parquet** (values, not NaN, and not the repo's
`_eia_hourly_frame_filled` bridging, which emits NaN), and that in `NG: NUC`
this **inverted** the published r_day ordering — item 7's stated defect did not
exist as described. The standing instruction is to re-run that falsification on
every other series before trusting any scored residual. Item 9's target is
`Total interchange`.

Two independent instruments, neither the EIA-930 feed, both already intaken
under the 2026-07-10 owner authorization:

* **imports** — NYISO MIS **P-32** External Limits & Flows, the eleven `SCH -`
  external schedules summed hourly.
* **hydro / oil** — NYISO MIS **P-63** Real-Time Fuel Mix.

Alignment is on **UTC**. Aligning on local time collapses the DST fall-back
hour and yields an 8,759-row year — a silent one-hour shear for the rest of the
series. Both MIS feeds carry an explicit UTC stamp, and the EIA-930 frame is
itself built on a UTC index, so the join is exact.

### 1.1 Census — the artifact does not repeat here

Suspect hours = exactly-0.0 values plus bit-identical non-zero runs ≥ 4 h:

| series | 2023 | 2024 | 2025 |
|---|---|---|---|
| **`Total interchange`** (item 9's target) | **0** | **6** | **14** |
| `NG: WAT` | 0 | 1 | 1 |
| `NG: OIL` | 3,160 | 6,371 | 7,935 |
| `NG: NUC` (nyiso-98 reference) | 1,275 | 390 | 118 |

### 1.2 Falsification

P-32 validates itself on the clean hours before it is allowed to judge a gap:
hourly r **0.910 / 0.908 / 0.882**, mean bias −16 / +182 / +508 MW. The bias
grows because P-32 posts *scheduled* flows and EIA-930 reports *actual*
interchange; it does not affect a zero test. On that footing **6/6 (2024) and
14/14 (2025) suspect hours are falsified** — P-32 median |flow| 1,247 /
4,138 MW where EIA-930 posts 0.0. 2023 has no suspect hour at all. `NG: WAT`:
1/1 falsified in 2024 and 2025.

`NG: OIL` behaves differently and is **not** item 9's problem: P-63 *confirms*
3,074 / 6,285 / 7,343 of its zeros — NY oil genuinely does not run — and the
instrument's own agreement is weak in 2023–24 (r 0.068 / 0.330 / 0.867) because
NYISO books dual-fuel units under `Dual Fuel` whatever they burn. That is a
recording-basis mismatch and it belongs to item 10
(`dual_fuel_oil_reattribution`), not here.

### 1.3 The item-9 statistic is unmoved

| year | r_hr raw | r_hr gap-masked | r_day raw | r_day masked | r_hr vs **P-32** |
|---|---|---|---|---|---|
| 2023 | 0.598 | 0.598 | 0.735 | 0.735 | 0.612 |
| 2024 | 0.624 | 0.624 | 0.786 | 0.787 | 0.611 |
| 2025 | 0.454 | 0.458 | 0.636 | 0.635 | 0.495 |

**20 artifact hours in 26,280 cannot move an r, and a wholly independent
instrument reproduces the same number.** Item 9's defect is real. The audit
cleared the target instead of dissolving it — the nyiso-98 outcome does not
repeat, and that is worth stating as plainly as the inversion was.

---

## 2. Attribution — the import node is faithful; its input is not

With the target cleared, the defect is attributed on the keeper's own committed
sidecars (`attribute` section; no re-solve). Three measurements:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| **[1]** r(model import profile, **model** spread profile) | **+0.673** | **+0.686** | **+0.772** |
| **[2]** r(**model** spread profile, **real** spread profile) | **−0.401** | **−0.236** | **−0.600** |
| model / real spread peak hour | h21 / h17 | h02 / h16 | h22 / h17 |
| **[3]** internal price hod swing, model | 12.95 | 13.17 | 19.75 |
| internal price hod swing, real NYISO DA | 22.45 | 25.13 | 43.27 |
| **ratio** | **0.58** | **0.52** | **0.46** |
| seam price hod swing (measured neighbor DA) | 19.83 | 24.10 | 32.08 |
| model spread at the real peak hour | **−0.1** | **+1.8** | **+5.3** |
| real spread at the same hour | +5.6 | +9.7 | +27.0 |

Read in order:

1. **The seam mechanism works.** The import node's diurnal shape follows the
   spread *it is shown* at r ≈ 0.67–0.77. `inject_nyiso_import_hub_prices` is
   doing exactly what it says.
2. **The spread it is shown is phase-inverted** against the real one, in all
   three years, by a wide margin.
3. **The inversion is arithmetic and has one bad term.** The seam side is
   measured and correct — it is the neighbor's own DA LMP, and its swing
   (19.8 / 24.1 / 32.1) matches reality because it *is* reality. NYISO's
   internal price swing is 0.58 / 0.52 / 0.46 of the real one. Subtracting a
   correctly-peaked seam price from a too-flat internal price drives the spread
   to its **minimum** exactly at the peak: the model's spread at the real peak
   hour is −0.1 / +1.8 / +5.3 $/MWh against a real +5.6 / +9.7 / +27.0. So the
   LP stops importing in the hour New York imports most, and buys its
   reconciled monthly quota overnight instead.

This confirms nyiso-86 §3's qualitative claim ("the interchange shape shares
C3c's root cause") quantitatively on the current keeper, and adds what nyiso-86
could not: **the import node itself is not the defect.** The too-flat internal
diurnal price swing *is* C3c — the diagnosed, unclosed structural limitation of
the five-zone representation whose lever queue nyiso-94/95/96/97 emptied
(`docs/FINDING-nyiso97-load-pocket-identification-2026-07-29.md`, re-open
conditions §5).

### 2.1 Why no import-side lever is admissible

* **Identification.** The only series that says "import more at h17" is the
  measured net interchange — the scored outcome, forbidden as an input
  (rule 13 `[R-MEASURED]`). Anything fitted to close the shape residual is a
  tuned value, not a parameter (rules 5 / 21).
* **Sign.** nyiso-86 already recorded the coupling: forcing peak imports
  **depresses peak duals**, so it moves C3c the wrong way while flattering the
  import metric. Fixing the symptom before the cause is rule-14-backwards, and
  the current peak-starved allocation is what silently flatters C3c today.
* **Rule 19 `[R-ONE-MECH]`.** The phenomenon already has a mechanism — the
  internal price formation. A second mechanism at the seam would stack on the
  unexplained residual of the first.

**Item 9 is therefore recorded CLOSED, attributed to C3c**, in the ex-ante
shape of nyiso-93/94/95/97. It is a symptom entry on C3c's ledger, not an open
lever. It re-opens only if C3c does.

---

## 3. Two by-products, reported and NOT armed

**(a) The 4,350 MW `NYISO_simultaneous_import` cap is a hand-set estimate that
measurement contradicts.** Model import tops out at **exactly 4,350 MW**, is
never above it in any hour of any year, and sits on the cap in
**548 / 689 / 177 h/yr**. Measured net import exceeds 4,350 MW in
287 / 314 / 145 h (max 5,929 MW, nyiso-86), and the published P-32 external
limits sum to a *minimum* of 5,805 / 6,090 / 6,680 MW — so the model cannot
reach flows New York actually scheduled. This is a live rule-14
`[R-ACCURATE]` reconcile item and it is **not** armed here, for two reasons:
the P-32 sum (~10 GW mean) is **not** a simultaneous limit — it is the sum of
parallel paths the five-zone network collapses into one link, exactly rule
14's named misalignment clause — so a *reconciled* identification is owed
first; and relaxing the cap alone would only let the model import more in its
wrong-phase overnight hours. Separate charter.

**(b) The node is a 7-rung step supply curve, and 45 % of its MW carries no
hourly price signal.** `HQ_hydro` (900 MW), `IESO_Ontario`, `PJM_shoulder` and
`eastern_mid` (690 MW each) = **2,970 MW of 6,580** keep a per-year *constant*
ladder price; only `PJM_west`, `ISONE_tie` and `import_scarcity` are repriced
hourly off the measured neighbor DA LMP. The step character shows in the
dispatch: on 2023, five of the seven rungs sit at their own cap or at zero in
the large majority of hours (`HQ_hydro` at cap all 8,760 h — it is
firm-floored; `IESO_Ontario` 7,903 h at cap; `PJM_shoulder` 5,757 h at cap;
`ISONE_tie` 6,622 h at zero; `eastern_mid` 6,911 h at zero).

**Correction to an earlier draft of this finding:** `import_scarcity` is
**not** unreachable — it dispatches **1.182 TWh** in 2023 and sits at its
2,230 MW cap in 27 h. The mistaken claim came from reading the *static
ladder's* cumulative position (4,350–6,580 MW, above the SIL) as the tranche's
dispatch order. The hourly repricing reorders the merit list: `import_scarcity`
is priced at the hourly max of the two neighbors + $1, which is frequently
below the static `eastern_mid` constant ($33.61 in 2023), so it clears while
`eastern_mid` is below cap in 1,209 h. Recorded here because it is also the
substantive point — the repricer materially reorders the ladder, which is
further evidence for §2's conclusion that the seam mechanism is working.

Both are characterisation, not levers: §2 shows the shape follows the spread
the node is shown, so neither a finer ladder nor a higher cap can fix a spread
that peaks at the wrong hour.

---

## 4. What this session DID arm — the EIA-930 demand-dropout repair

Extending the audit from the benchmark to the **inputs** found the same
exactly-0.0 artifact in the `Demand` column, where it is consumed as real load.
Across all six modeled BAs × 2023–2025 the only affected series is `NYIS`
`Demand`: **2024 h403, h6760, h6761 and 2025 h354, h355**, each bracketed by
~17–22 GW readings — and each reproduced **1:1** in the keeper's solved
`system_<year>.parquet`, where total served demand is exactly 0.0 MW. **The
model serves no load at all in five hours New York drew ~20 GW.**

### 4.1 The consequence is much larger than five hours of energy

Measured on the keeper's own committed sidecars, the five dropout hours are not
a rounding error — they are the **entire** overgeneration-dump and
negative-price record of the NYISO keeper:

| year | total dump | dump **in** the dropout hours | zonal price there | slack |
|---|---|---|---|---|
| 2023 | 0.0 MWh | — (no dropout hour) | — | 0.0 |
| 2024 | 22,026.6 MWh | **22,026.6 MWh = 100 %** | **−$26.001 in all 5 zones** | 0.0 |
| 2025 | 15,587.7 MWh | **15,587.7 MWh = 100 %** | **−$26.001 in all 5 zones** | 0.0 |

With demand pinned at zero, the must-run stack — nuclear, run-of-river hydro,
the 900 MW firm HQ import floor, wind and solar — has nowhere to go, so ~7–8 GW
per hour is thrown to the Dump variable and every zone prints the dump-cost
optimum. So the artifact was manufacturing **five fabricated floor-price hours
and the keeper's entire dumped-energy total**, not merely misplacing 0.1 TWh of
load. Any price-distribution statistic on this bundle — negative-price-hour
counts, price minima, the low tail feeding C3a/C3b — carried all five.

2023's clean zero-dump row is the control: no dropout hour, no dump, no
negative price.

`_screen_demand_dropouts` (`src/market_sim/data/eia930/demand.py`) is the
low-side twin of the existing `_screen_demand_spikes`, wired into all six
per-BA loaders. A whole BA's metered demand is never 0 MW, so the flag needs no
threshold and adds **zero degrees of freedom**; flagged hours are dropped and
linearly interpolated, the same repair the spike screen and the missing-meter
path already use. It is scoped to **demand only, never interchange** — ERCO
posts 187 / 140 / 113 legitimately-zero interchange hours on idle DC ties, and
screening those would delete real measurements, which is the rule-14 failure
mode the repair exists to avoid.

Measured before solving: **byte-identical (Δ = 0.00000 TWh, max |Δ| = 0.0 MW)
on 16 of 18 ISO-years**; NYISO 2024 +0.0562 TWh (+0.037 %), NYISO 2025
+0.0435 TWh, **2023 untouched in every ISO** — so the arm's 2023 year is its
own same-recipe zero-delta control.

A/B result and gate verdicts: §5, appended after the solve.

---

## 5. A/B result — every pre-registered gate PASSES

Registered run **`2026-07-29-nyiso-99-demandfix`**
(`results/calibration/nyiso99_demandfix`), a `replay_keeper.py` re-solve of the
keeper's own `meta.json` recipe on the fixed HEAD, so the only delta is the
code change. Scorer: `scripts/probes/nyiso99_ab_compare.py`.

| gate | condition | result |
|---|---|---|
| **G1** | arm 2023 ≡ keeper 2023 | **PASS** — max \|Δ class MW\| **0.000000**, max \|Δ price\| **0.000000** $/MWh |
| **G2** | no zero-served-demand hours | **PASS** — 3 → **0** (2024), 2 → **0** (2025), 0 → 0 (2023) |
| **G3** | served energy rises by the wedge only | **PASS** — **+0.05624** / **+0.04345** TWh, matching the pre-registered figures exactly |
| **G4** | C1 protection | **PASS** — C1 **14/14 · free 10/10**, unchanged. 2023 `CC_REGULAR` **bit-unchanged** at 32.5119 TWh (the ISO's tightest cell never moves — the screen is a no-op in 2023). 2024 +0.0121, 2025 +0.0090 TWh, ≈0.4 % of the ±2.94 band |
| **G5** | protective gates hold | **PASS** — C7 **PASS**, C8 **PASS**. The fragile 2024 `ST_GAS` cell moves 30.5 % → **30.4 %**, i.e. *toward* the 30 % cap, grounded on both sides |
| **G6** | C3c honesty | **unchanged** — hours > \$300 **4 / 0 / 7 → 4 / 0 / 7** |

G1's exact zero also discharges two secondary questions: this container
reproduces the keeper bit-for-bit, and the `dump_cost_full_offer_domain` guard
that landed on `main` mid-session (caiso-139) is confirmed byte-neutral for
NYISO.

**The headline is the dump and the price, not the energy.** Overgeneration dump
goes **22,026.6 → 0.0 MWh (2024)** and **15,587.7 → 0.0 MWh (2025)** — *exactly*
zero, in both years — and with it the five fabricated −\$26.001 all-zone hours.
**Slack stays 0.0 MWh in every year**, so the restored ~20 GW is served by real
resources, not shed. Max \|Δ price\| is \$121.0 (2024) / \$110.0 (2025): the
dropout hours repricing off the dump floor to a real clearing price.

Determination is **NOT-YET** in both bundles with **C3c the sole FAIL** — the
repair changes no verdict, which is the correct outcome for a five-hour data
repair and was pre-registered as such. The arm's C6 reads UNATTESTED only
because no governance attestation is built for a non-promoted run.

**Import r_hr moves 0.624 → 0.623 (2024) and 0.454 → 0.453 (2025)** — i.e. not
at all. Stated because the pre-registration said it would be: this is **not**
an item-9 fix and is not offered as one.

**Pre-existing, unchanged, reported (rule 14):** D-5 forecast/backcast parity
FAILs on `nyiso_local_selfsupply` ("active backcast-only for this config but
NOT on the declared backcast-overlay list"). The keeper's own committed
`legitimacy_diagnostics.json` carries the identical row, so this is inherited,
not caused here. It is a declaration-list gap, not a dispatch defect, and it is
left for its own session.

**LOYO (rule 20):** not applicable in the fitted sense — nothing here is a
parameter, so there is no value to overfit. The 2023 no-op *is* the held-out
year, and it comes back bit-identical. No out-of-training year was touched
(NYISO carries no calibration-complete marker).

**Verdict: KEEPER-RECOMMENDED, owner call.** Every gate passes, C1's tightest
cell is untouched, the protective gates hold, and the bundle removes five
fabricated floor-price hours and 100 % of the keeper's dumped energy. Following
the NYISO lane convention since nyiso-96, the building session leaves the
promotion decision to the owner rather than taking it.

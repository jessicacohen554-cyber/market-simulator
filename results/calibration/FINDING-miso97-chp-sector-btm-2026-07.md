# FINDING miso-97 — MISO's CHP sector data is now MEASURED, its BTM hold-out was understated by 1.03 GW, and the 2026-07-08 decision not to correct MISO CHP heat rates is **VACATED**: its load-bearing premise ("its CHP does not over-deliver") is refuted on the measured share

**Determination: DERIVE + MEASUREMENT SESSION. No LP built, nothing solved,
nothing registered. Keeper `2026-07-25-miso-88-egrid-hr` UNCHANGED.** One data
correction is armed on disk (TASK 1); the heat-rate lane (TASK 3) is re-opened
as a **design, deliberately NOT built** — it is a second, separable delta and
bundling it with TASK 1 would destroy attribution (rule 19 `[R-ONE-MECH]`).

Everything below is reproducible from committed sources with no re-solve: the
EIA-860 plant sheet, the EIA-923 monthly-generation artifact, the keeper
bundle's own `legitimacy_diagnostics.json` + `hourly/` sidecars, and the
committed dashboard run payload. Instruments, both committed:

```
PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso97_chp_sector_btm.py --iso MISO --year 2024 --validate
PYTHONPATH=.:src .venv/bin/python scripts/probes/_miso97_chp_delivery.py  --iso MISO
```

Source lead: `results/calibration/FINDING-caiso128-heat-rate-provenance-2026-07-27.md`.

---

## 1. TASK 1 — the sector data exists, is committed, and was never read

MISO was the only ISO whose `thermal_tranches_MISO.csv` carried an **empty**
`chp_sector` column, and 0 of its 113 CHP plants appear in the hardcoded
`fleet.CHP_SECTOR_CLASS_BY_PLANT` (44 plants, 41 of them ERCOT's). So
`data.chp.chp_btm_pct` fell through to `CHP_BTM_PCT_BY_SECTOR["merchant"]` =
**35.0** for every CC_CHP/CT_CHP plant and `CHP_ST_BTM_PCT` = **90.0** for every
ST_CHP — the one value in that table with no independent source
(`constants.py`: *"residual-identified, forecast-risk"*; DOF item S5 / issue
\#1335).

**Root cause, and it is a silent-failure bug, not a missing dataset.**
`derive_thermal_tranches._chp_sector_map` reads "EIA Sector Number" from the raw
`data/raw/f923_<year> (1).zip` Page-1 workbooks. **Those archives are not
committed to the repo.** With them absent the function returns `{}`, the column
comes back all-NaN, and the preserve-prior guard in `main()` then carries
forward whatever the previous file held. For the four ISOs whose first derive
ran *with* the archives present that froze a good column; for MISO, whose first
derive ran without them, it froze **emptiness — permanently**. The failure mode
is a `print()` to stdout and an all-NaN column, which is why it survived.

**The same attribute is committed on disk.** The EIA-860 `Plant` schedule
publishes the identical EIA sector code in `eia860_plant.parquet` (`Sector` /
`Sector Name`), on the identical 1–7 taxonomy (1 Electric Utility, 2 IPP
Non-CHP, 3 IPP CHP, 4 Commercial Non-CHP, 5 Commercial CHP, 6 Industrial
Non-CHP, 7 Industrial CHP), so it maps through the same `_EIA_SECTOR_CLASS`
table.

**Equivalence is measured, not assumed** (`--validate`) — replaying the EIA-860
map onto the four ISOs whose committed `chp_sector` came from EIA-923:

| ISO | plants with a 923 sector | matched in 860 | agree | absent from 860 |
|---|---|---|---|---|
| PJM | 78 | 78 | **78 (100 %)** | 0 |
| CAISO | 86 | 86 | **86 (100 %)** | 0 |
| NYISO | 31 | 31 | **31 (100 %)** | 0 |
| NEISO | 37 | 37 | **37 (100 %)** | 0 |
| **TOTAL** | **232** | **232** | **232 (100 %)** | **0** |

232/232 with zero misses. This is the same measured EIA attribute read off a
different committed release — a rule-14 `[R-ACCURATE]` source swap, **not** a
substitute estimator.

### 1.1 The measured MISO sector mix

100 % of MISO's 113 CHP plants (11 597 MW) carry an EIA-860 sector:

| class | commercial | industrial | merchant |
|---|---|---|---|
| CC_CHP | 2 plants / 55 MW | 9 / 3 140 MW | 13 / 3 841 MW |
| CT_CHP | 15 / 172 MW | 31 / 2 176 MW | 6 / 278 MW |
| ST_CHP | 13 / 328 MW | 33 / 616 MW | 9 / 992 MW |
| **fleet** | **23 / 554 MW (4.8 %)** | **66 / 5 932 MW (51.1 %)** | **24 / 5 112 MW (44.1 %)** |

MISO CHP is **half industrial by capacity**, so the flat merchant 35.0 was
wrong for the majority of the fleet — the peer-mix inference in the lead
(~44 % industrial) is confirmed, and slightly exceeded.

### 1.2 The in-LP capacity delta

| class | plants | nameplate MW | BTM today | BTM sourced | in-LP today | in-LP sourced | **Δ MW** | Δ % |
|---|---|---|---|---|---|---|---|---|
| CC_CHP | 24 | 7 036 | 35.0 | **50.9** | 4 574 | 3 458 | **−1 116** | −24.4 |
| CT_CHP | 52 | 2 626 | 35.0 | **65.5** | 1 707 | 906 | **−800** | −46.9 |
| ST_CHP | 55 | 1 935 | 90.0 | **63.6** | 194 | 705 | **+511** | +264 |
| **TOTAL** | **113** | **11 597** | **44.2** | **56.3** | **6 474** | **5 069** | **−1 405** | **−21.7** |

**MISO was carrying ≈1.4 GW net (1.9 GW on the gas CHP classes alone) of host
self-supply as grid-facing merchant capacity.** The lead's "order of 1–2 GW"
inference is confirmed, mid-range.

The `btm_sourced` / `in-LP sourced` columns are verified **exactly equal** to
what `data.chp.chp_btm_pct` returns once the artifact is patched — 0 mismatched
rows across all 131 (plant, class) pairs, in-LP total 5 068.8 MW both ways. The
table is the model's behaviour, not a re-implementation of it.

**The ST_CHP row is a real behaviour change and is called out, not buried.**
`chp_btm_pct` returns the 90.0 `CHP_ST_BTM_PCT` only when a plant has **no**
sector (or the ISO is ERCOT). Populating MISO's sectors therefore moves ST_CHP
off 90.0 onto its measured sector share — which is exactly how PJM (62.5–66.2),
NEISO (67.0) and NYISO (47.0) ST_CHP already behave. MISO's 90.0 was the
no-sector fallback, and 63.6 lands it inside the peer band. **No code change and
no per-ISO literal** is involved (rule 25 `[R-ISO-SCOPE]`).

### 1.3 What is reachable, and what is not

`chp_overrides` (the tranche artifact) is the only ISO-generic sector channel, so
a CHP plant absent from it cannot receive a sector regardless of what EIA
publishes. It keys on **`plant_code` alone, not `(plant_code, plant_group)`** —
which matters: 19 MISO CHP plants sit in the artifact under a different group
than the fleet assigns them, and every one is still reached. Scoping
reachability by the pair understates the change by ~380 MW and was corrected
before these numbers were taken.

**488 MW (4.2 % of MISO CHP nameplate) is genuinely unreachable** — 36 MW of
CT_CHP and 452 MW of ST_CHP, 425 MW of it a single plant (1393) whose only
artifact row is COAL, a group the derive never writes `chp_sector` on. Per-class
reachability is CC_CHP **100 %**, CT_CHP **98.6 %**, ST_CHP **76.6 %**. Every
peer has the same structural gap, so this is accepted structure, not a MISO
defect. The table above is already scoped to what is reachable.

### 1.4 Peer control: the change is EXACTLY a no-op where sectors already exist

| ISO | in-LP today | in-LP sourced | Δ MW |
|---|---|---|---|
| PJM | 1 922.1 | 1 922.1 | **0.0** |
| CAISO | 2 516.2 | 2 516.2 | **0.0** |
| NYISO | 3 281.9 | 3 281.9 | **0.0** |
| NEISO | 417.2 | 417.2 | **0.0** |

**Zero MW on all four peers** — not "small", zero. The EIA-860 sector reproduces
the committed EIA-923-derived column so exactly that no peer plant's share moves
by any amount. The mechanism is ISO-generic; its **effect** is MISO-only because
MISO was the only ISO on the default. This is the control that shows the change
carries no cross-ISO blast radius (rule 25 `[R-ISO-SCOPE]`).

### 1.5 DOF ledger — this is a rule-24 SHRINK, not a new parameter

Replacing an unsourced default with a measured source **removes** a degree of
freedom. 104 of MISO's CHP artifact rows move off the fitted `merchant = 35.0`
onto EIA-measured sector classes whose 70/65 values are grounded in the EIA-923
Schedule-8 CHP fuel allocation. **Zero new free parameters; zero fitted values;
no tuning channel added** (rule 24 `[R-REGISTRY]`). Same posture as
`caiso_offer_surface_measured`. **This does NOT consume the ledgered-caveat
budget** (saturated at 3/3) — that budget governs documented-and-unclosed
misses, and this closes a defect rather than ledgering one.

---

## 2. TASK 2 — MISO CHP grid delivery re-measured, and a coverage trap

### 2.1 Why the direction is decidable without a solve

The BTM share enters in exactly three places, and all three are the **same
linear factor `(1 − s)` on the same per-plant nameplate**:

1. **LP capacity** — `grid_cap = nameplate × (1 − s)`, with
   `committed_cap`/`econ_cap`/`peak_cap` all shares of `grid_cap`, so every
   tranche scales at **unchanged prices** (heat rate, VOM, carbon are untouched
   by `s`).
2. **The steam-following floor** — `grid_mr_cf = pmin_cf × (1 − s)`,
   `floor_mw = grid_mr_cf/100 × nameplate`.
3. **The benchmark subtrahend** — `_btm_frame` holds out the same share of the
   plant's measured EIA-923 class net generation, so the grid-facing **actual**
   is `netgen_923 × (1 − s)`.

Raising `s` is therefore a pure horizontal rescaling of the whole CHP problem.
Writing `f = (1 − s_new)/(1 − s_old)` and the model response
`ρ = model_new/model_old`: the actual falls by exactly `f`; the model falls by
`f` where it is capacity- or floor-bound, and by **less** where it is economic
(a smaller cheap-CHP supply raises λ, so the now-smaller capacity is dispatched
at least as hard). Hence `ρ ≥ f`, and

```
ratio_new = (model_old × ρ)/(actual_old × f)  ≥  model_old/actual_old = ratio_old
```

**Raising the BTM share can only move a class UP relative to its meter. It
cannot deepen an under-run.** That is a structural bound, not an estimate, and
it is what makes the 2026-07-08 premise testable with no LP.

`legitimacy_diagnostics.json` D-2 puts the floor-forced share at **17.6 %**
(CC_CHP) / **30.9 %** (CT_CHP), so neither `ρ = f` nor `ρ = 1` is the truth;
both endpoints are reported and **nothing is interpolated between them**.

### 2.2 The measurement

| year | class | meter cov. | model TWh | actual @ today | err today | actual @ sourced | f | bound ρ=f | bound ρ=1 |
|---|---|---|---|---|---|---|---|---|---|
| 2023 | CC_CHP | 95.0 % | 29.09 | 26.47 | **+9.9 %** | 19.74 | 0.746 | +9.9 % | **+47.3 %** |
| 2023 | CT_CHP | 99.6 % | 10.66 | 13.51 | **−21.1 %** | 7.81 | 0.578 | −21.1 % | **+36.5 %** |
| 2023 | ST_CHP | 97.3 % | 0.49 | 0.76 | **−35.4 %** | 1.74 | 2.277 | −35.4 % | −71.6 % |
| 2024 | CC_CHP | 95.0 % | 28.33 | 26.63 | **+6.4 %** | 20.10 | 0.755 | +6.4 % | **+40.9 %** |
| 2024 | CT_CHP | 99.6 % | 10.80 | 13.53 | **−20.2 %** | 7.95 | 0.588 | −20.2 % | **+35.9 %** |
| 2024 | ST_CHP | *76.6 %* | 0.58 | 1.08 | −45.8 % | 2.11 | 1.959 | — blocked — | |
| 2025 | CC_CHP | *82.5 %* | 27.68 | 24.13 | +14.7 % | 16.93 | 0.702 | — blocked — | |
| 2025 | CT_CHP | *64.8 %* | 10.87 | 8.48 | +28.2 % | 4.96 | 0.585 | — blocked — | |
| 2025 | ST_CHP | *52.4 %* | 0.38 | 0.85 | −55.1 % | 1.51 | 1.778 | — blocked — | |

**THE COVERAGE TRAP, and it is load-bearing.** The 2025 EIA-923 vintage is the
**monthly early release** — ~3 400 respondents against ~13 200 in the annual
2024 vintage — and reports only 83 %/65 %/52 % of MISO CC_CHP/CT_CHP/ST_CHP
capacity. The model side is the **whole** class, so a 2025 class-total
comparison divides a full numerator by a partial denominator and **fabricates
the "+28.2 % CT_CHP over-delivery"**. Rows under 90 % meter coverage are
excluded from the verdict rather than quietly averaged in. All 12 months are
present per covered plant, so this is a partial *plant set*, not a partial year.

### 2.3 Verdict on the 2026-07-08 premise

Comparable rows only (2023 all three classes; 2024 CC_CHP + CT_CHP):

| class | mean err today | mean err at ρ=1 | verdict | material? |
|---|---|---|---|---|
| CC_CHP | **+8.1 %** | **+44.1 %** | **OVER-DELIVERS on both bounds** | yes — 29 TWh vs a 12.8 TWh line |
| CT_CHP | −20.6 % | **+36.2 %** | **straddles zero** | yes — 13.5 TWh, marginally over |
| ST_CHP | −35.4 % | −71.6 % | under-runs | **no** — 0.8 TWh, far below 2 % |

The docstring's two halves, judged separately:

* **"BTM-dominated" — SURVIVES, and is strengthened.** It was asserted against
  an unsourced 35.0; the measured shares are *higher* for gas CHP (CC 50.9,
  CT 63.6). MISO CHP is more host-dominated than the 2026-07-08 note assumed.
* **"its CHP does not over-deliver" — REFUTED.** CC_CHP over-delivers **today,
  at the very default that was supposed to prove it does not** (+9.9 / +6.4 %),
  and can only rise on the sourced share (to +47.3 / +40.9 % at the ρ=1 bound).
  CC_CHP is the dominant CHP class — 61 % of CHP nameplate, 72 % of CHP energy,
  4.5 % of MISO load — so this is the class the premise was about.
* **"CT_CHP already under-runs" — NOT ROBUST.** True today (−20.6 %), but the
  §2.1 bound says correcting the share can only move it up, as far as +36.2 %.
  The under-run is substantially an artifact of holding out too little host
  load.

**The two defects push the same way, and the tension the lead flagged
resolves.** Understated heat rates make MISO CHP too cheap and an under-held-out
BTM puts too much of it in the LP; both inflate grid-facing CHP. The reason the
2026-07-08 note nonetheless saw CT_CHP *under*-running is that it measured
against a denominator inflated by the same understated hold-out — the meter side
was too big for the same reason the model side was.

---

## 3. TASK 3 — the heat-rate decision is VACATED (design filed, NOT built)

`data/chp._correct_chp_steam_credit_hr` records the rejection as: *"its CHP does
not over-deliver (BTM-dominated, CT_CHP already under-runs), so the correction
only worsens CT_CHP."* §2.3 removes both operative clauses. The stated reason —
**a class fits worse** — is in any case precisely what rule 14 `[R-ACCURATE]`
names as a signal to look elsewhere, and rule 1 `[R-STRUCT]` forbids rejecting a
structurally correct input on residual grounds. The "something else" now has a
name: the unsourced BTM share, fixed in §1.

MISO's CHP heat rates are understated **33–41 %** on a consistent net basis
(CC_CHP −33 %, CT_CHP −33 %, ST_CHP −41 %) while CC_REGULAR/CT_PEAKER/COAL/
ST_GAS in the same ISO, year and pipeline measure accurate to 0–3 %
(FINDING-caiso128 §3) — which is what identifies the eGRID steam credit as the
cause rather than a general heat-rate problem.

**What must NOT be done: arming the existing ERCOT-lineage hand factors for
MISO.** caiso-128 §4 measured `CAISO_EOR_TOPPING_FACTOR = 1.8` **over**-correcting
CAISO CT_CHP by **+40 %** while five ISOs sit 12–62 % **under**. A single
universal topping factor is wrong in both directions at once; adding MISO to
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` would trade a measured 33 % understatement
for an unmeasured overstatement.

**The design (caiso-128 §6, unchanged and endorsed here):** replace the hand
factors with **each plant's own CEMS power-only rate** — CAMPD
`Σ heatInput / Σ grossLoad` over full-clock unit-hours (`opTime ≥ 0.99`) above
half the unit's own observed peak, **times the plant's own same-year measured
gross→net ratio**, with the existing eGRID→hand-factor chain as the fallback
where CEMS does not cover. ISO-generic gate, default **off**, byte-identical
off, **zero fitted parameters** (`opTime ≥ 0.99` and the half-peak gate are
definitional, not swept). Forward story per the CO2-rate precedent
(`data/emission_rates.py`).

**The basis reconciliation is not optional.** eGRID `PLHTRT` is
`PLHTIAN/PLNGENAN` (heat per **NET** MWh) and the LP dispatches net MW, while
CEMS reports **gross**. MISO's own measured class cap-weighted gross→net ratios
are CC_CHP 1.080, CT_CHP 1.237, ST_CHP 1.308, CC_REGULAR 1.047, CT_PEAKER 1.072,
COAL 1.096, ST_GAS 1.061.

### 3.1 Feasibility: unlike CAISO, the measured replacement REACHES MISO's defect

Coverage was the binding constraint on the CAISO design (its worst class,
CT_CHP, is only **17 %** MW-covered by CEMS). Measured for MISO with the same
committed instrument (`--iso MISO --stability 2023 2024 2025`):

| class | plants | covered | GW | GW covered | **% MW** | cross-year `r` | median CV |
|---|---|---|---|---|---|---|---|
| **CC_CHP** | 24 | 14 | 7.04 | 5.85 | **83 %** | 0.993 | 0.007 |
| **CT_CHP** | 52 | 6 | 2.63 | 1.00 | **38 %** | 0.987 | 0.004 |
| ST_CHP | 55 | 0 | 1.94 | 0.00 | **0 %** | — | — |
| CC_REGULAR | 44 | 41 | 27.41 | 26.00 | 95 % | 0.984 | 0.011 |
| COAL | 57 | 45 | 42.80 | 41.89 | 98 % | 0.944 | 0.011 |
| CT_PEAKER | 168 | 93 | 22.29 | 20.23 | 91 % | 0.953 | 0.011 |
| ST_GAS | 23 | 20 | 10.99 | 10.82 | 98 % | 0.987 | 0.015 |

**The design is reachable precisely where MISO's defect is.** CC_CHP — the
over-delivering class, 72 % of MISO CHP energy — is **83 %** MW-covered against
CAISO's 51 %, and CT_CHP is **38 %** against CAISO's 17 %. A per-plant
cross-year `r` of 0.987–0.993 at a median CV of **0.4–0.7 %** says the measured
rate is a stable *physical property*, not a noisy annual statistic — which is
what makes it forward-derivable (rule 13 `[R-MEASURED]`).

ST_CHP has **no CEMS coverage at all** (every MISO ST_CHP plant is below the
Part-75 reporting threshold), so it would keep the existing eGRID→hand-factor
fallback unchanged. That is acceptable and should not gate the build: ST_CHP is
0.4–0.8 TWh, far below the rule-20 2 % materiality line (12.8 TWh).

**Sequencing (rule 19 `[R-ONE-MECH]`): TASK 1 and TASK 3 are two separate
deltas and must not be bundled.** They move the same classes in the same
direction — a bundled arm cannot attribute. TASK 1 goes first because it is a
pure data correction with zero DOF; TASK 3 is judged against the post-TASK-1
residual, not today's.

---

## 4. What is armed, and what is not

**Armed on disk (TASK 1):**
* `data/raw/_processed-legacy/thermal_tranches_MISO.csv` — `chp_sector`
  populated on 104 CHP rows (0 → 104). **Only that column changed**; every other
  column is byte-identical to HEAD (verified column-by-column). `chp_pmin_cf`
  and the committed/peaking shares are untouched — rule 23 `[R-FROZEN-DERIVE]`
  forbids re-deriving them, since *their* source data did not change.
* `scripts/data/derive_thermal_tranches._chp_sector_map` — EIA-860 fallback so
  the intake no longer silently yields an empty column on a checkout without the
  raw f923 ZIPs. EIA-923 stays authoritative wherever present, so a checkout
  that *does* carry the archives derives exactly what it derived before.

**NOT armed:** the heat-rate correction (§3 — design only). No
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` change. No `ScenarioConfig` field added or
altered. No solve was run and no run was registered.

---

## 5. DO-NOT-REDO

* Re-deriving MISO `chp_sector` from the raw `f923_*.zip` archives — they are
  not committed; EIA-860 `Sector` is the same attribute, validated 232/232 (§1).
* Re-measuring the peer agreement, the MISO sector mix, or the in-LP MW delta
  (§1; instrument committed).
* **Comparing a class total against the 2025 EIA-923 vintage** (§2.2) — it is
  the monthly early release covering 52–83 % of MISO CHP capacity and it
  fabricates over-delivery. State meter coverage in any future class comparison.
* **Using the dashboard payload's per-plant `m_ann` to restrict the model side
  to metered plants** — it is a PLANT total across all classes, and attributing
  it to a plant's CHP class inflated ST_CHP from 0.49 to 11.9 TWh (24×). No
  committed per-(plant, class) model series exists; coverage-gating is the
  honest substitute.
* **Scoping CHP sector reachability by `(plant_code, plant_group)`** —
  `chp_overrides` keys on `plant_code` ALONE, and 19 MISO CHP plants sit in the
  artifact under a different group than the fleet assigns them. Pair-keying
  understates the change by ~380 MW (§1.3).
* **Testing a sector value with `is None` after it round-trips through a
  DataFrame column** — pandas stores the missing entry as `NaN`, `NaN is None`
  is False, and every unreachable ST_CHP plant then takes the sector branch and
  reports 35.0 where the model returns 90.0 (a 452 MW error, 425 MW of it one
  plant). Use `isinstance(x, str)`.
* Re-arguing that raising the BTM share could deepen a CHP under-run (§2.1 —
  `ρ ≥ f` is structural).
* Adding MISO to `CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` / arming the 1.8×
  topping factor (§3 — measured over-correcting CAISO by +40 %).
* Treating MISO CT_PEAKER / CC_REGULAR / COAL / ST_GAS heat rates as suspect —
  measured accurate to 0–3 % on a net basis (FINDING-caiso128 §3).
* Bundling TASK 1 and TASK 3 into one arm (§3).
* Re-attacking the 2025 off-peak cycling gap (miso-96 §2025 — adjudicated,
  data-blocked outage-grain, rule 19).

Next number: miso-98.

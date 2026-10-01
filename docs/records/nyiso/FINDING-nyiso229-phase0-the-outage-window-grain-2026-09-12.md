# FINDING — nyiso-229 phase 0: the 31-May-2022 window is **REAL BUT DAY-ROUNDED**, and the repair is already built

**Session:** nyiso-229 · **ISO:** NYISO · **Date:** 2026-09-12
**ZERO LP.** Every number below is read or recomputed from committed artifacts
(`data/raw/campd-unit-outages-perunitmerit-NYISO.csv`, `data/raw/campd-unit-level/NY_<year>.parquet`,
the recovered nyiso-228 control bundle `results/calibration/nyiso228_control_span`) or produced by a
**derive** re-run, which is not a solve. Rule 32 `[R-SHARD]` (a): the parent ran no LP.
**Keeper `2026-09-09-nyiso-221-fuelvintage-span` UNCHANGED. Nothing armed, nothing promoted.**

Predecessors: `docs/RESULT-nyiso228-2026-09-12.md`,
`docs/ADDENDUM-nyiso228-the-2022-tail-is-MISTIMED-not-absent-2026-09-12.md` §4c, which named
availability-window **placement** as the successor and required this phase 0 before any solve.

---

## 0. Headline

The ADDENDUM's five named plants are **not** a fabricated outage. Four of the five were genuinely
dark on 31 May 2022 in CAMPD. What is fabricated is the **grain**: the extract stores windows as
**dates** while the detector finds them in **hours**, and the loader re-expands every window to
`outage_start` 00:00 → `outage_end` 23:00. On 2022-05-31 that asserts a **flat 10,053 MW offline for
all 24 hours** — a line that cannot vary within a day by construction — when the detected windows
leave **3,657 MW available at hours 16 and 17**, the exact two hours the model shed firm load at
VOLL.

> **3,657 MW restored against 124.9 and 235.6 MW of shed load — 29.3× and 15.5×.**
> The spurious 31-May scarcity event does not survive its own arithmetic.

**The repair needs no new mechanism and no new parameter. It already exists**: `--hour-grain`
(caiso-183) on the deriver, and `market_sim.data.outages.unit_outage_event_window`, which consumes
the two optional columns. **CAISO's extract already carries them; NYISO's does not.** This is the
caiso-181 seam, unfixed in NYISO, and it is the largest single availability-accounting defect
measured in this lane.

**It does not close the winter object**, and this finding claims nothing about it. See §6.

---

## 1. (a) WHICH ARTIFACT PLACES THE WINDOW

`data/raw/campd-unit-outages-perunitmerit-NYISO.csv` — the ≥5-day merit extract, which the keeper
consumes (`campd_per_unit_attribution=True` + `campd_outage_merit_order_guard=True`, verified in
`results/calibration/nyiso_fuelvintage_A/run_config.json`; selector
`outages.py::_unit_outage_csv_path`).

**14 windows at the five named plants cover 2022-05-31**, accounting for all 5,412 MW. The layup
companion contributes **one** row (Ravenswood CT0010, 25.0 MW) and is **not** the cause — and no
loader reads it in any case; it is the guard's audit trail.

**The defect is not the detector.** It is the extract's **day-grain schema** plus the loader's
00:00→23:00 re-expansion. §3 measures that separation rather than asserting it.

## 2. (b) WERE THEY ACTUALLY ON OUTAGE? — **partly, and the split is the finding**

CAMPD `NY_2022.parquet`, metered conduct on 2022-05-31 (opTime h, MWh, max MW):

| plant | unit | nameplate | 05-31 metered | verdict |
|---|---|---|---|---|
| Ravenswood | 10 / 20 / 30 | 1,792 MW | 0 h, 0 MWh | **extract CORRECT** — genuinely dark |
| Bowline | 2 | 621 MW | 0 h, 0 MWh | **extract CORRECT** |
| Selkirk | CTG101/201/301 | 427 MW | 0 h, 0 MWh | **extract CORRECT** |
| Empire | CT-1 / CT-2 | 668 MW | 0 h, 0 MWh (ran 22–24 h/d on 05-28…30) | **extract CORRECT** on 05-31 |
| **Bowline** | **1** | **621 MW** | **23 h, 7,249 MWh, max 562 MW** | **CONTRADICTED** |
| **Roseton** | **1** | **621 MW** | **21 h, 1,905 MWh, max 174 MW** | **CONTRADICTED** |
| **Roseton** | **2** | **621 MW** | **22 h, 3,466 MWh, max 247 MW** | **CONTRADICTED** |

Three units, **1,863 MW nameplate, 12,620 MWh metered**, are asserted unavailable for a day on which
they ran through the peak. At hour 17 they produced **971 MW simultaneously** — against 235.6 MW of
shed load.

**The tell was visible in the extract before any meter was read.** Bowline u1 carries two windows,
`05-22→05-31` *and* `05-31→06-15`; Roseton u1 likewise `05-12→05-31` and `05-31→06-08`. A window
ending and another starting on the same date is a **return to service inside that date** — and day
grain erases exactly the hours the unit ran.

## 3. THE DECISIVE SEPARATION: rounding, not misplacement

For every ≥5-day window 2022–2025, count the hours the loader asserts unavailable while CAMPD meters
`grossLoad > 0`, and measure each contradicted hour's distance from the nearest window boundary. Day
grain can fabricate at most 23 h per edge, so a contradiction **within 23 h** is rounding, while one
deeper in the interior would be the **detector** placing the window wrongly — a different and much
larger defect.

| year | windows | contradicted | **edge ≤23 h** | edge GWh | **interior >23 h** | interior GWh | interior share of hours |
|---|---|---|---|---|---|---|---|
| 2022 | 512 | 461 | **9,872 h** | **1,376.9** | 560 h | **1.1** | 5.4 % |
| 2023 | 519 | 471 | **10,167 h** | **1,332.5** | 524 h | **0.6** | 4.9 % |
| 2024 | 461 | 415 | **8,529 h** | **1,075.9** | 395 h | **0.7** | 4.4 % |
| 2025 | 492 | 423 | **8,144 h** | **952.7** | 504 h | **0.8** | 5.8 % |

> **~95 % of contradicted hours are boundary rounding, and they carry ~99.9 % of the energy.**
> The interior residue is 0.6–1.1 GWh/yr across ~400–560 hours — units idling at a few MW, i.e. the
> event-based detector tolerating brief returns, which is its documented contract.

**The detector is not misplacing windows. The schema is rounding them.** That is the caiso-181
signature (*"every contradicted hour within 22 h (< 24) of a window boundary, every year"*)
reproduced on NYISO.

## 4. (c) DOES IT MISPLACE WINDOWS IN 2023–2025? — **the same defect, the same size, every year**

Yes. §3's table is flat across years: 8,144–10,167 contradicted edge-hours and 0.95–1.38 TWh of
metered generation asserted unavailable in **every** year, 2022 included and not special. The reason
it has never shown is the one the prompt anticipated: **the model only gets tight enough for
availability to bind in 2022.**

Except it is **not** confined to 2022, and this corrects an expectation I held going in. The
recovered nyiso-228 control:

| year | firm-load slack | reserve-short hours | reserve shortfall | families short |
|---|---|---|---|---|
| **2022** | **2 h, 360.5 MWh** | **88 h** | **50,902.6 MWh** | 6 |
| 2023 | 0 | 20 h | 9,627.4 MWh | nyc_10/30min, seny_30min |
| 2024 | 0 | 15 h | 4,888.6 MWh | nyc_10/30min, seny_30min |
| 2025 | 0 | 33 h | 18,228.8 MWh | nyc_10/30min, seny_30min |

**The NYC locational reserve families are short in all four years.** So restored NYC availability has
somewhere to land in the keeper's own scored years:

| year | tight hours | fleet restored, mean MW over those hours | NYC+LI restored, mean MW |
|---|---|---|---|
| 2022 | 88 | **1,825** | 449 |
| 2023 | 20 | **1,408** | 307 |
| 2024 | 15 | **681** | 293 |
| 2025 | 33 | **482** | 156 |

This **falsifies a generalisation of nyiso-227's census for this mechanism.** That census measured
ST_GAS *energy* headroom (3.1–3.6 GW unused in the mean hour) and concluded every availability-side
lever is inert. It holds for levers that **remove** capacity from an energy balance with slack. It
does **not** hold here, because this lever acts on the **locational reserve** families, which are
short in every year. Stated as a correction, not a criticism: nyiso-227's own three-line headroom
test was an energy test, and it does not cover the co-optimised reserve pool.

## 5. THE REPAIR, ITS PRE-SOLVE ARITHMETIC, AND THE PROOF IT IS ZERO-DOF

`--hour-grain` appends `outage_start_hour` / `outage_end_hour` — the detected hour-of-day of each
window's first and last outage hour. The deriver carries **two in-process stop-the-line assertions**
that make the change provably non-substantive:

1. every reconstructed window is a **subset** of the day-granular window (the repair can only
   ever *remove* asserted unavailability, never invent it);
2. the base-column projection is **byte-identical** to the flag-absent frame — *"the grain change
   moved a detected window"* is an `AssertionError`.

Both passed on the NYISO derive (exit 0). **No parameter, no threshold, no detector constant.**

**The re-derive is clean at HEAD, and this is proven rather than assumed.** Re-running the committed
invocation *without* the flag:

| rows by start-year | 2019 | 2020 | 2021 | **2022** | **2023** | **2024** | **2025** | 2026 |
|---|---|---|---|---|---|---|---|---|
| re-derived | 540 | 519 | 526 | **512** | **519** | **461** | **492** | 165 |
| committed | 526 | 516 | 526 | **512** | **519** | **461** | **492** | 165 |

**2022–2025 and 2026 are byte-identical** — 1,984 rows, hash `aa5e39b967d057f2` both sides. The only
drift is **17 rows in 2019–2020** (Cayuga and Somerset retired coal, Nassau Energy), outside every
year any NYISO run solves. So a `--hour-grain` re-derive is a **pure single-change delta on the
solved span**, and the whole-file sha difference (`ce028b65` vs the committed `58799099`) is
accounted for and confined.

**Availability restored** (day-grain window hours − detected hour-grain window hours, cap-weighted):

| year | windows | restored unit-h | restored GWh-capacity | mean MW of 8,760 | max per row |
|---|---|---|---|---|---|
| 2022 | 512 | 12,547 | 3,104.1 | 354.3 | 46 h |
| 2023 | 519 | 12,784 | 2,902.8 | 331.4 | 46 h |
| 2024 | 461 | 11,026 | 2,405.8 | 274.6 | 45 h |
| 2025 | 492 | 10,450 | 2,473.2 | 282.3 | 46 h |

By class, pooled: ST_GAS 13,169 h / 5,678.9 GWh · CC_REGULAR 16,732 h / 2,945.0 · CC_CHP 15,522 h /
2,081.5 · ST_CHP 970 h / 135.1 · CT_CHP 414 h / 45.4.

**Unit-level verification against the meter** — the repair reproduces measured conduct, it does not
merely move a boundary:

| unit | hour-grain leaves AVAILABLE on 05-31 | CAMPD metered RUNNING | |
|---|---|---|---|
| Bowline 1 | hours **6–22** | hours **6–22** | **exact** |
| Roseton 1 | hours 9–21 | hours 8–21 | 1 h residual |
| Roseton 2 | hours 2–23 | hours 1–22 | 1 h residual |

The two residuals are an **8 MW and a 10 MW first-ramp hour** sitting below the detector's own
threshold — a threshold effect, not a grain effect, and ~1 h per unit. Reported, not swept.

## 6. WHAT THIS DOES **NOT** DO — declared before any solve

* **It does not close the winter object.** The 2022 miss is Jan −24.0 / Feb −23.4 / Dec −40.9
  $/MWh (77 % of the annual miss) and the market's 101 hours above $300 fall Jan 28 / Feb 8 / Dec 34
  / Aug 15. This repair **removes a spurious May event**; it creates none of those. Nothing here is
  evidence about D-A amplitude or the interchange-`r` co-decay.
* **It will LOWER the 2022 C3c count, not raise it** — 8 h > $300 toward ~0. Under the reporting
  rule inherited from nyiso-228 §4b that is not a regression: at **0 % precision and 0 % recall**
  those 8 hours contained no real scarcity hour, so removing them makes the model honest rather
  than worse. **Any arm reports precision and recall against the market's own 101 hours, never a
  bare count.**
* **It pushes prices DOWN, and the direction is not uniformly helpful.** C3a is currently
  +5.7 / +6.5 / −6.3 % for 2023/24/25 — downward pressure helps 2023 and 2024 and **hurts** 2025.
  C3a-2022 is already −13.8 % and will likely get **worse**. Declared here, ex ante, and **not
  gated on**: rule 29 `[R-SCREEN]` forbids a screen that reads the target residual, and rule 1
  `[R-STRUCT]` decides this on construction accuracy, not on the fit.
* **The restored MW are the extract's own capacity accounting, not dispatch.** The overlay removes a
  bin share (`unit_pct_of_plant` under `unit_outage_extract_basis_share=True`), so realized LP
  availability will differ in detail. The 15–29× margin at the 2022 VOLL hours is what makes that
  prediction robust; the keeper-year margins are narrower and may be partly absorbed.
* **Two ORIS codes fall back to `Upstate_West`** in the zone split (7784; **57664 = Astoria
  Energy II**, an NYC plant), so the NYC+LI column of §4 **understates** NYC. Flagged, not corrected.

## 7. SCREEN YEAR: **2022**, chosen on footprint and liveness, never on residual

Rule 29 `[R-SCREEN]` requires the screen year be the year the mechanism's **own measured footprint is
largest**, never the year with the biggest residual. 2022 is largest on **both** available footprint
measures, computed above with no reference to any residual: restored GWh-capacity **3,104.1** (vs
2,902.8 / 2,405.8 / 2,473.2), and restored MW in the control's tight hours **1,825** (vs 1,408 / 681 /
482). It is also the only year with firm-load slack, so it is the only year in which the repair's
headline claim — that the VOLL event is an artifact — is testable at all.

`[R-HOLDOUT]` was **removed 2026-09-09**, so 2022 needs no authorization, no marker and no one-shot.
Rule 30(c) still binds: a 2022 result cannot decertify NYISO. And 2022 is a year that has been
iterated against, so **no number from it is a skill claim** — it is model-selection evidence.

## 8. G-CTRL: **form 4, and the control already exists on disk**

Rule 29(b): the incumbent keeper's committed bundle is the control, and no control solve is spent.
Better here — the **nyiso-228 arm-C control span covers 2022–2025 at HEAD** and is recovered
(`git checkout ed8c60c5 -- results/calibration/nyiso228_control_span`, 20 hourly sidecars verified on
disk, gitignored and unstaged so it cannot reach `main`). nyiso-228 §2 validated it to the third
decimal against the keeper plus the one LIVE G-DRIFT hunk. **A G-DRIFT audit is still owed from the
control's own `git_sha` to whatever SHA an arm is pinned at**, and is written into the PRECOMMIT
before the arm is solved.

## 9. RULES

1 `[R-STRUCT]` — a construction defect identified from the source data; the case rests on accuracy,
and the price direction is declared against it in §6. 13 `[R-MEASURED]` / 14 `[R-ACCURATE]` — the
finer grain is the **same measured input at its detected resolution**; the day-grain version is a
rounding of it, and §6 refuses to bury the resulting price move back in the coarser input.
19 `[R-ONE-MECH]` — one artifact, one seam; the layup companion is audit-only and is not a second
mechanism. 21 `[R-DOF]` / 24 `[R-REGISTRY]` — **zero free parameters**; the registry question this
raises is §10's and is put to the owner rather than decided here. 23 `[R-FROZEN-DERIVE]` — the
re-derive cites a **construction repair (caiso-183)**, not a residual, and §5 proves it moves no
detected window. 25 `[R-ISO-SCOPE]` — nothing is transferred from CAISO; NYISO's extract is derived
from NYISO's own CAMPD, and no number crosses. 28 `[R-MECH-MATRIX]` — no matrix row exists for the
window grain; one is minted with this work. 29 `[R-SCREEN]` — phase 0 complete at zero LP; the screen
year is named here, before any solve. 31 `[R-RETAIN]` — nothing deleted; the recovered control stays
on disk, gitignored. 32 `[R-SHARD]` — the parent ran no LP.

## 10. THE DECISION — **RULED: a registered field**, and it is built

Put to the owner in session with both routes and their costs; **ruled Route A, the registered
field.** Built and committed here; **nothing solved, nothing armed.**

`ScenarioConfig.unit_outage_window_hour_grain: bool = False` selects a **separate**
`-perunitmerithour-` extract through `outages.unit_outage_csv_for_iso(hour_grain=)`, the pattern
that selector already uses five times. Why a field rather than the data-triggered adoption CAISO
used: the grain otherwise appears in **no** `run_config.json` and changes **no** `cache_key()`, so
two bundles with identical configs could have solved on different grains and a stale
`results/NYISO/<key>/` could serve the wrong one (rule 24 `[R-REGISTRY]`). **A default-off gate on
`_has_hour_grain` itself was refused as the design**: that helper is shared by all six ISOs and
gating it would have **silently reverted CAISO's keeper**.

What landed, and what each piece is verified to do:

| | |
|---|---|
| `config/scenarios.py` | the field, plus its `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` entries **in the same commit** (the nyiso-119 / caiso-186 discipline), so no pinned key moves |
| `data/outages.py` | `hour_grain` on the selector and on `unit_outage_derate_factors`; predicated on `per_unit_crosswalk` AND `merit_order_guard`, falling through to the day-grain companion when absent |
| `data/fleet/arrays.py` | threads it from config, gated on both siblings |
| `data/resolved_inputs.py` | threads it too, so a bundle records the extract it **actually read** |
| `scripts/run_calibration_full.py` | `--unit-outage-window-hour-grain` / `--no-…`, threaded through `solve_and_persist`, the recorded config, `meta.json` and the replay kwargs — so a shard can arm it over a committed recipe and the delta is provably the single flag |
| `tests/unit/data/test_unit_outage_window_hour_grain.py` | 15 tests, all passing |

**Verification, all measured rather than asserted:**

* **Cache keys hold.** `tests/unit/results/test_cache_config_agreement.py` — 15 passed: every
  committed fixture's recorded key still reproduces. The field is dropped at its frozen `False`,
  and arming it **does** change the key (both directions tested).
* **The off path is byte-inert, at the artifact level too.** The new extract's **base columns** are
  byte-identical to the committed day-grain extract on 2022–2025 and 2026 (1,984 rows, hash
  `aa5e39b967d057f2` both sides), so on the solved span the only difference is the two appended
  hour columns.
* **Gating is correct in all five postures**, and **CAISO is untouched** — the selector returns
  `campd-unit-outages-CAISO.csv` at every flag setting.
* **Regression sweep**: `test_outages.py`, `test_campd_per_unit_attribution.py`,
  `test_unit_outage_mixed_gas_routing.py`, `test_unit_outage_extract_basis_share.py` and the
  cache-agreement suite — **155 passed, 0 failed**.
* **CI matrix guard** `check_mechanism_matrix.py --base HEAD` exits **0**; the new field's row and
  all seven cells register. Its 257 anchor warnings and the CAISO prose-header warning are
  **pre-existing** — measured identical with my change stashed, and the checker itself labels them
  *"(pre-existing, not this PR)"*. `--fix-anchors` was **not** run: it would rewrite 257 other
  lanes' rows, which is not this lane's to do.

**Committed artifact**: `data/raw/campd-unit-outages-perunitmerithour-NYISO.csv`, sha256
`ee778a87d3739341a7c578078b5e0194545f9231efbef2cd32d72e88e0aa21fa`, **derived twice to different
paths with identical bytes** (determinism), plus its `.meta.json` sidecar recording the invocation
and the audit-only layup companion. Reproduce with:

```
python3 scripts/data/derive_campd_unit_outages.py --iso NYISO \
  --years 2019 2020 2021 2022 2023 2024 2025 2026 \
  --min-outage-days 5.0 --high-load-pctl 0.85 --min-inmerit-hours 24 \
  --fullstop-override-days 5 --fullstop-override-cf 0.02 \
  --per-unit-crosswalk --merit-order-guard --hour-grain \
  --out data/raw/campd-unit-outages-perunitmerithour-NYISO.csv
```

**Rule 28 duty (c) discharged**: matrix row `unit_outage_window_hour_grain` minted in
`docs/codebase-site/data/mechanism-matrix.js` with a cell line in **every** shard — NYISO `O` (the
defect measured, the mechanism built, no LP run), the other six `U` carrying NYISO's reusable
zero-LP protocol, and CAISO's `U` recording as a **fact** that its base extract already carries the
grain data-triggered, with the verdict left to CAISO's lane (rule 28(d)).

## 11. WHAT THIS SESSION DID **NOT** DO

* **No LP, no screen, no arm, no promotion.** The keeper is unchanged. The 2022 screen is
  pre-registered but **not launched** — that is a spend decision and it is the owner's.
* **`unit_outage_per_unit_clip` is NOT armed.** The grain removes this artifact class at source
  (293 overlaps → 0), so arming both would be two mechanisms on one phenomenon
  (rule 19 `[R-ONE-MECH]`). If the screen shows a residual overlap the clip is the successor, not a
  co-arm.
* **Massena 54592 is left at 200 %** and handed forward: an `eia923_netzero` fallback row
  (`NET0-923`, 104.1 MW at 100 % of plant) stacks on the real CAMPD row (`001`, 44.0 MW, also 100 %)
  — two **distinct** unit ids each claiming the whole plant. Neither this gate nor `per_unit_clip`
  reaches it. It is the cleanest new object this phase 0 found and it is **zero-LP** to investigate.
* **`scripts/lib/bundle_io.py` records `shared_inputs["unit_outages"]` from the UNGATED path** —
  it names the base extract even for a run that consumed `-perunit-` or `-perunitmerit-`. A
  **pre-existing** provenance gap I did not introduce and did not widen (changing it would move
  every ISO's recorded hashes). It is, however, a second reason the registered field was the right
  channel: `run_config.json` now carries the grain even though `shared_inputs` does not.
* **22 pre-existing test failures** observed in `tests/unit/data` (CAISO firm-import / CAISO ST-gas
  / NEISO fleet) and **3** in `tests/unit/config/test_reserve_config.py` (ERCOT multi-product,
  cause visibly `ZoneInfoNotFoundError` — missing `tzdata` in this container). Verified identical
  with my change stashed. Other lanes'; reported, not touched.

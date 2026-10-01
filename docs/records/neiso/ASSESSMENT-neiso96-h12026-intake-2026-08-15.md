# ASSESSMENT — neiso-96: the H1-2026 actuals LANDED, the C3c deriver primed, and the `final` block recommended for a SPLIT

**Session:** neiso-96, 2026-08-15 · **Branch:** `claude/neiso-h1-2026-actuals-intake-27c0rx`
**Keeper:** `2026-08-14-neiso-93-envelope` — **UNCHANGED**; no promotion, no re-key, **NO RUN PRODUCED**.
**Markers:** `frontier` HELD (2026-07-11) · `complete` HELD (2026-07-07) · `final` **EMPTY**
**Ordinal:** verified against `docs/calibration-log/neiso.md` — the neiso-95 entry closes *"Next
shorthand: `neiso-96`"* and no neiso-96 entry exists. **It is neiso-96; no divergence to report.**

**Freeze:** `frontend/data/backcast/holdout-freeze.json` **VERIFIED ACTIVE AT HEAD** — `"active": true`,
declared 2026-07-25, re-armed 2026-08-06, scope `isos: ALL`, tiers `[validation, locked_test]`. Read
directly from the file, not inferred. **No grant exists and none is inferred.** NEISO's locked test
remains **NEVER GRANTED and NEVER SPENT** (owner decision D-23). Re-verified after the rebase onto
`834f761`, not only at session start.

> **NO YEAR WAS SOLVED, SCORED OR REGISTERED — in or out of sample. No LP was constructed.**
> This session performed a **DATA INTAKE** (rule 22 as amended 2026-08-06: *"what is held out is the
> SCORE, never the DATA"*). `holdout-freeze.json` and `calibration-complete.json` are **unedited**;
> `frontend/data/backcast/tail/actual_tail.json` is **byte-unchanged**. `frontier` and `complete` were
> **NOT re-verified** — that was done at neiso-95 and is not repeated.

**Deliverables (new, committed):**

| artifact | path |
|---|---|
| Downloader | `scripts/data/fetch_neiso_smd_zonal_lmp.py` |
| Its test | `tests/test_fetch_neiso_smd_zonal_lmp.py` (6 tests, pass) |
| Raw landing | `data/raw/lmp-data/NEISO/smd-zonal-lmp/NEISO_smd_zonal_lmp_2026.csv` |
| Route-equivalence probe | `scripts/probes/neiso96_smd_route_equivalence.py` → `_neiso96_smd_route_equivalence.json` |
| Intake + tail-priming probe | `scripts/probes/neiso96_intake_and_tail_priming.py` → `_neiso96_intake_and_tail_priming.json` |
| H1-2026 solvability audit | `scripts/probes/neiso96_h12026_solvability.py` → `_neiso96_h12026_solvability.json` |

---

## 0. Headline

| # | task | outcome |
|---|---|---|
| **1a** | Intake H1-2026 NEISO actuals | **LANDED.** 181 operating days, 4,343 covered hours. Every previously-owned year reproduces **byte-for-byte** and is unmoved. |
| **1b** | Extend `bench/NEISO/` to match | **STRUCTURALLY IMPOSSIBLE AS AN INTAKE — NOT DONE, and it should not be.** A bench part is an output of REGISTERING A RUN, not a data artifact. Producing one for 2026 requires solving 2026, which this session is forbidden to do. §2. |
| **2** | Re-run `derive_actual_tail.py` | **RE-RUN; output BYTE-UNCHANGED.** The 2026 row is present in the data and correctly WITHHELD by the tier gate. Priming demonstrated against an in-memory marker: a grant would unlock `rt_gt 126 / da_gt 140`. §3. |
| **3** | Re-answer `final` readiness | **DO NOT GRANT — but SPLIT the block.** The intake retires the H1-2026 *data* blocker; a different, structural one is now measurable in its place. Both of neiso-94's live reasons survive and **neither applies to H1-2026**. §4. |
| **4** | Two owner escalations | **BOTH OPEN, re-measured at HEAD, neither resolved** (each needs a re-solve). §5. |
| **5** | Re-solve if an in-sample delta | **NO DELTA ⇒ NO RUN PRODUCED.** §6. |
| — | Unplanned finding | **The 2018–2023 SMD workbook vintage is DST-naive**, so the committed parquet is displaced by one hour on four days a year in those years — including in-sample 2023. Reported, **not repaired**. §1.4. |

---

## 1. Task 1a — the intake

### 1.1 The workbook route is genuinely unreachable, and that is why a second route exists

`derive_actual_lmp.py` has always sourced NEISO from `data/raw/lmp-data/NEISO/<year>_smd_hourly.xlsx`.
The repo README calls these *"manual download"* and does not say why. The reason, established this
session: ISO Express serves them **only behind a CAPTCHA-gated "Download Selected Files" form** on the
*Zonal Information* page. There is no direct href — the page exposes only
`smd_hourly_template_v0.xlsx`, an empty template. Probed `2026_smd_hourly.xlsx` across the plausible
`static-assets/documents/<yyyy>/<mm>/` paths for 2025–2026: **every one 404s.**

So the workbook route cannot be refreshed by any committed script, and the prompt's stop condition —
*"IF THE SOURCE IS GENUINELY UNAVAILABLE … do NOT substitute a proxy"* — had to be tested against the
**series**, not against one packaging of it.

**It is not unavailable.** ISO-NE publishes the same hourly prices through the ungated static
historical-report tree, one operating day per file, no credentials:

```
https://www.iso-ne.com/static-transform/csv/histRpts/da-lmp/WW_DALMP_ISO_<YYYYMMDD>.csv
https://www.iso-ne.com/static-transform/csv/histRpts/rt-lmp/lmp_rt_final_<YYYYMMDD>.csv
```

These are the *Day-Ahead* and *Real-Time (final)* **Hourly LMP Reports** — settlement prices at every
ISO-NE location. They carry exactly the nine SMD pricing locations the workbook's per-zone sheets
carry (`.H.INTERNAL_HUB` = the "ISO NE CA" hub sheet, plus the eight `.Z.*` load zones = ME, NH, VT,
CT, RI, SEMA, WCMA, NEMA). **This is the same series from the same publisher, not a proxy and not an
interpolation.** Every operating day of H1-2026 returns HTTP 200.

`scripts/data/fetch_neiso_smd_zonal_lmp.py` fetches both markets per day, keeps those nine locations,
and reduces ~4.9 MB/day of all-node report to ~8 KB/day of zonal series — 181 days land as one 1.5 MB
committed CSV rather than 362 multi-megabyte files.

### 1.2 The reproduce-check came FIRST, and the committed values are UNMOVED

The neiso-93 discipline, before extending anything. Every year the producer already owned was rebuilt
from its own committed workbook:

```
uv run python scripts/data/derive_actual_lmp.py --isos NEISO --years 2018 … 2025 --parquet-only
```

> **`md5 3323efe038ab1bdb33382764eff4bfd0` before and after — the rebuilt parquet is BYTE-IDENTICAL to
> the committed one, and `git status` was clean.** Frame-level: `DataFrame.equals` **True** across all
> 70,080 rows.

That md5 is also the blob at `origin/main` **after** the rebase onto `834f761`, so the check is valid
against the branch's actual base, not only against the tree the session started from. And after the
2026 block was merged in, the 2018–2025 rows were re-compared and are **still byte-unmoved** — checked
again after the second run that added the JSON entry.

### 1.3 The two routes are ONE input — measured, not asserted

Carrying 2026 on the daily-report route is only legitimate if it is the same input, or the parquet
becomes a silent year-gated splice, which rule 22 as amended 2026-08-06 forbids. So the claim was
measured: `neiso96_smd_route_equivalence.py` runs sampled operating days of the **committed** years
through the new reducer and compares them to the workbook-derived frame the committed parquet is built
from, **pre-densification** (so a leap day can be sampled like any other).

15 days sampled, chosen for the cases a splice breaks on: both DST transitions in both workbook
vintages, a leap day, the winter scarcity events that produce the tail hours C3c scores, and ordinary
days.

> **On the 11 days where the two sources agree on how many hours the day HAD: 2,640 cells compared,
> `float32` mismatches = 0.** The parquet stores `float32`, so **the two routes are identical at the
> precision that actually ships.**

The residual float64 delta is **4.5e-13 $/MWh** at worst (on a ~$2,000 Elliott hour — one ULP), and it
is a *storage* artifact rather than a price disagreement: openpyxl returns the doubles Excel stored
(`16.580000000000002`, `8.040000000000001`) while the CSV publishes the decimal ISO-NE settled on. Same
published cents, different last bit.

### 1.4 UNPLANNED FINDING — the 2018–2023 SMD workbook vintage is DST-naive

The four days that did **not** agree are all DST days, and the comparison isolates the cause to the
workbook rather than to the new route. **ISO-NE changed the workbook's shape partway through the
archive:**

| day | workbook rows | market's published hours | agree? |
|---|---|---|---|
| 2019-11-03 fall-back | **24** | 25 | ✗ |
| 2020-03-08 spring-fwd | **24** | 23 | ✗ |
| 2021-11-07 fall-back | **24** | 25 | ✗ |
| **2023-11-05 fall-back** | **24** | 25 | ✗ **(in-sample year)** |
| 2024-03-10 spring-fwd | 23 | 23 | **✓ 0 mismatches** |
| 2024-11-03 fall-back | **25** | 25 | **✓ 0 mismatches** |
| 2025-03-09 spring-fwd | 23 | 23 | **✓ 0 mismatches** |
| 2025-11-02 fall-back | **25** | 25 | **✓ 0 mismatches** |

**The 2024–2025 vintage publishes the true 23 / 25 and agrees with the daily reports exactly, including
the repeated `02X` hour. The 2018–2023 vintage publishes a flat 24 rows on every calendar day.** The
producer's docstring describes the *correct* shape ("23 rows … 25 …"), so its positional clock — row
`k` begins `k` real hours after local midnight — is right for the new vintage and wrong for the old
one. Measured consequences in 2018–2023:

- **fall-back:** the workbook collapses the repeated hour into its two-instance mean (2021-11-07 hub DA
  `52.43` = mean of the market's `50.79` and `54.06`), and the day then runs an hour short;
- **spring-forward:** the workbook carries an extra row, so the rest of the day is displaced an hour
  late and the last row spills into the next local date — visible as **exactly 1 duplicate timestamp**
  in each of 2018–2023 and **0** in 2024–2025.

**Reported, deliberately NOT repaired.** 2023 is a tuned year, so correcting it moves an in-sample
**scoring target**, which needs its own authorization and a re-solve — outside a remit whose task 5
condition is explicitly about *not* manufacturing a delta. Recorded in
`data/raw/lmp-data/README.md` as a known defect with its measurement. Its C3c blast radius is small
by construction (the affected days are mild March/November days, far from a $300 tail) but that is a
bound, not a repair.

### 1.5 What landed

```
uv run python scripts/data/fetch_neiso_smd_zonal_lmp.py --start 2026-01-01 --end 2026-06-30
uv run python scripts/data/derive_actual_lmp.py --isos NEISO --years 2026
```

181/181 operating days fetched, **39,087 rows** = 181 × 9 locations × 24 h, less the 9 rows of the
spring-forward hour — the arithmetic closes exactly.

| year | rows | rt cov | rt mean | rt max | **RT h > $300** |
|---|---|---|---|---|---|
| 2019 | 8,760 | 0.9999 | 30.67 | **261.35** | **0** |
| 2023 | 8,760 | 0.9999 | 35.70 | 1,161.97 | 15 |
| 2024 | 8,760 | 1.0000 | 39.54 | 2,112.77 | 8 |
| 2025 | 8,760 | 1.0000 | 65.88 | 1,110.22 | 20 |
| **2026** | **8,760** | **0.4958** | **78.82** | **776.59** | **126** |

Dense on the same chronological 8,760 calendar as every other year, NaN after 30 June — coverage
**0.4958**, matching the partial-2026 blocks CAISO / NYISO / MISO already carry (0.496). The tail is a
winter event, concentrated where New England scarcity forms: **Jan 90 h, Feb 35 h, Mar–May 0 h,
Jun 1 h.**

**Cross-checked against a market that saw the same weather:** NYISO's committed H1-2026 block carries
**86 hours > $300** (max $1,878) and MISO 150 h > $200. A cold January 2026 across the eastern
interconnect corroborates NEISO's 126 hours as real rather than an artifact of the new route.

`actual_lmp.json` gained **exactly one** entry (`NEISO/2026`); a key-by-key diff confirms **every
pre-existing entry across all six ISOs is byte-identical**. NEISO was the only ISO with a 2026 parquet
block but no JSON entry; that asymmetry is now closed.

---

## 2. Task 1b — `bench/NEISO/` cannot be extended by an intake, and should not be

The prompt asks to extend `bench/NEISO/` (2022–2025) "to match". **It cannot be done as data intake,
and doing it would require exactly the forbidden operation.** This is a finding, not a shortfall.

A bench part is **not a data artifact — it is an output of registering a run**:

- `scripts/lib/backcast_artifacts.write_bench_part` is called only from
  `render_backcast._write_bench_part`, which iterates `D["bench"]` from
  `render_calibration_html.build_payload(runs, …)`;
- `build_payload` loops `for label, bdir in runs` and `for year in meta["years"]`, reading **the
  bundle's own input snapshots** (`bundle_input_path(bdir, "eia923"/"eia930"/"campd")`) **and
  `system.parquet`, which is model output**;
- `dashboard_add_run.py`'s own docstring: *"the per-(ISO, year) benchmark parts **for this run's
  years**"*.

The registry confirms it exactly. NEISO's registered runs cover `{2022}` ∪ `{2023, 2024, 2025}`, and
the bench directory holds **precisely** `2022, 2023, 2024, 2025`. NEISO has committed *actuals* for
2018–2021 too, and those years have **no bench part** — because no run covers them.

> **A 2026 bench part is therefore produced BY a `final` grant, not required before one.** Creating it
> would mean solving and registering H1-2026 — the operation the hard stop forbids and the one a grant
> exists to authorize. Not attempted.

---

## 3. Task 2 — `derive_actual_tail.py` re-run, and the ordering hazard quantified

Re-run after the intake landed. **Its output is byte-unchanged** (`git diff` on
`frontend/data/backcast/tail/actual_tail.json` is empty). NEISO emits `2020–2025` exactly as before.

That is the correct result, and it is the point. The 2026 data is now **present in the source parquet**
and the rule-22 tier gate **still refuses it**:

| year | tier | emittable at HEAD |
|---|---|---|
| 2018 | locked (fails closed — unenumerated) | **False** |
| **2019** | **locked_test** | **False** |
| 2020–2022 | validation (`complete` held) | True |
| 2023–2025 | train | True |
| **2026** | **locked_test** | **False** |

`_year_emittable('NEISO', 2026, marker)` → `tier_for_year(2026)` = locked_test → `final` is empty →
withheld. **The gate holds.**

**The priming is demonstrated rather than described.** Evaluated against an **in-memory** marker
document (nothing written, no marker created, no grant implied), the row a grant would unlock is:

```
{"threshold": 300.0, "da_gt": 140, "rt_gt": 126,
 "da_coverage": 0.496, "rt_coverage": 0.496, "hours": 8760}
```

> **neiso-90's ordering hazard is now an ordering REQUIREMENT rather than a data gap.** Before this
> session, a `final` grant followed by a deriver re-run would still have produced **nothing** for 2026
> — there was no data — so C3c would have scored **SKIPPED** and the touch-once year would have been
> spent on a verdict silent on the criterion NEISO's frontier is declared on. Now the re-run is one
> command that yields a real row. **The requirement stands and must be step one of any grant**; what
> has changed is that satisfying it now works.

---

## 4. Task 3 — the `final` readiness question, re-answered on the merits

This **updates neiso-94 §5** rather than restating it.

### 4.1 What the intake retires

| neiso-94 §5 item | status after this session |
|---|---|
| Subordinate: *"resolve or split off the H1-2026 half, which is independently hard-blocked"* — no 2026 rows in the actuals parquet | **THE DATA BLOCKER IS RETIRED.** 4,343 covered hours; 126 actual RT tail hours. There is now something to score H1-2026's C3c against. |
| Subordinate: *"re-run `derive_actual_tail.py` as step one of any grant"* | **STILL REQUIRED, now PRIMED** (§3). It was previously a requirement that could not be satisfied. |

### 4.2 What survives, unchanged

| neiso-94 §5 reason | status |
|---|---|
| **1. PERMANENT — 2019 cannot exercise C3c** | **SURVIVES, untouched, and re-confirmed from the parquet at HEAD: 2019 RT max $261.35 against a $300 threshold, 0 hours.** A property of the 2019 market. Nothing an intake can touch — and this intake did not try. |
| **2. REPAIRABLE — the Pilgrim fleet-vintage gap** | **SURVIVES, untouched.** Not a NEISO lane item; it belongs to the six-ISO `fleet-vintage-retiree-window-charter-2026-08.md`. Not opened here. |

### 4.3 A NEW blocker, in the place the old one vacated — and it is not NEISO's

Retiring the data blocker made a second question answerable for the first time: **with actuals in
hand, can H1-2026 actually be solved?** Nobody had measured it, because the missing target made it
moot. Measured now (`neiso96_h12026_solvability.py`, the neiso-90 input walk re-run against 2026):

| input | 2023 control | 2026 |
|---|---|---|
| `actual_lmp` | OK | **OK — 8,760 h, cov 0.496, 126 h > $300** ← retired this session |
| `actual_tail` | OK | GAP — tier gate, self-healing on grant + re-run (§3) |
| **`demand`** | OK — (5, 8760), 96.86 TWh | **ERR — `No EIA-930 data for ISO 'NEISO' in year 2026`** |
| `henry_hub` | OK — $2.54 | **ERR — `KeyError: 2026`** |
| `backcast_config` | OK | **ERR — `KeyError: 2026`** |
| `calibration_reference` | OK | GAP — no `isos.NEISO.2026` block |
| `renewable_capacity` | OK — 120 rows | GAP — file absent |
| `hydro` | OK — 168 plants, 8.55 TWh | OK **in name only** — 5 plants, 0.04 TWh |
| `parasitic`, `reserve_requirements` | OK | OK (year-independent) |

**The demand failure is the load-bearing one, and it is structural rather than a missing file.** The
raw EIA-930 data *is* on disk — `ISNE_region_2026.parquet` spans 2026-01-01 → 2026-07-01. But
`eia930.frames._eia_hourly_frame` returns `None` unless the extract is a **full `HOURS_PER_YEAR`
series** (`if len(df) != HOURS_PER_YEAR: return None`), so a half-year is rejected before NEISO's
loader ever sees it; the caller then falls back to `eia_demand_profiles.parquet`, which carries
**2021–2025 for all seven ISOs** and has no 2026 row, and raises.

> **The gate is in shared code and is blind to ISO. Every BA fails it for 2026** — ISNE, NYIS, CISO,
> MISO, PJM and ERCO all return `None` for 2026 while ISNE/NYIS/PJM/ERCO return 8,760 for 2025.
> **The model cannot construct a partial-year solve for anybody.** This is a structural, six-ISO
> property of the solve path, not a NEISO data gap — so it is a charter item for a cross-ISO session,
> not this lane (rule 25), and this session did not touch it.

The contrast with 2019 is worth stating precisely, because neiso-87 once made the opposite mistake in
the other direction: **2019, 2020 and 2021 demand all resolve OK at HEAD** (95.54 / 92.10 / 98.55 TWh).
The 2019-unsolvable claim stays withdrawn. It is **H1-2026** that is unsolvable at HEAD, and for an
entirely different reason — it is half a year, not a year.

### 4.4 Is the H1-2026 half now SEPARABLE from the 2019 half? **Yes — and it should be split.**

They are one `final` block today. They should not be, because **their blockers are now disjoint in
every respect**:

| | **2019** | **H1-2026** |
|---|---|---|
| Can it exercise C3c? | **No, permanently** — actual RT max $261.35, 0 h > $300 | **Yes, decisively** — **126 actual RT h > $300**, max $776.59 |
| Pilgrim fleet-vintage gap | **Disqualifying** — 91 % of the C1 band | **Irrelevant** — Pilgrim retired 2019; correctly absent from a 2026 fleet |
| Scoring target present? | Yes | **Yes, as of this session** |
| Solvable at HEAD? | **Yes** (neiso-88/90, re-confirmed §4.3) | **No** — partial-year demand path (§4.3) |
| Blocker's nature | permanent + NEISO-specific | structural + **six-ISO** + tractable |
| Blocker's owner | the fleet-vintage charter, and physics | a cross-ISO partial-year charter |

**Neither of neiso-94's two live reasons applies to H1-2026.** They are both 2019 facts. Holding
H1-2026 inside the same block means a year that *can* answer the open C3c question is gated behind a
year that provably never can.

> ### RECOMMENDATION — and it is a RECOMMENDATION; nothing here grants anything.
>
> **1. DO NOT GRANT `final` today, for either half.** 2019 is unchanged and still disqualified on both
> of neiso-94's reasons. H1-2026 now has a scoring target but **cannot be solved at HEAD**, so a grant
> today would authorize a spend that cannot be executed.
>
> **2. SPLIT the block.** Let `final` address 2019 and H1-2026 separately. The two halves fail for
> unrelated reasons, on unrelated timescales, owned by unrelated lanes. **This is the owner's call and
> is left to the owner.**
>
> **3. The H1-2026 half is now the tractable one, and its path is nameable:** the cross-ISO
> partial-year work (the `HOURS_PER_YEAR` gate and the 2026 demand-profile coverage), then the four
> per-year reference gaps (`henry_hub`, `backcast_config`, `calibration_reference`,
> `renewable_capacity`, plus a real hydro budget). None is a NEISO lane item; all are cross-ISO.
>
> **4. When a grant does come, `derive_actual_tail.py` must still be step one** (§3) — now a satisfiable
> requirement rather than a trap.

**Unchanged and re-affirmed:** neiso-90's trigger for 2019 — the C3c lane arming a tail-forming
mechanism, making 2019 valuable as a *specificity* test — and neiso-94's hard precondition that the
Pilgrim gap close first. No new tuning lever was opened; the frontier is declared and the cross-ISO
lever queue stays cleared.

---

## 5. Task 4 — the two open owner escalations, re-measured at HEAD

**Both are OPEN. Neither is resolved, and neither can be without a re-solve.** Reported only.

### (i) NEISO is STILL the only ISO of six on the archived P2 commitment pass

Measured on all six ISOs' current keeper bundles' own `meta.json`:

| ISO | keeper | `commitment` | `passes` |
|---|---|---|---|
| **NEISO** | `2026-08-14-neiso-93-envelope` | **true** | **`["P1","P2"]`** |
| CAISO | `2026-08-09-caiso-188-d1-micseam` | false | `["P1"]` |
| ERCOT | `2026-08-15-ercot204-rule26-delete` | false | `["P1"]` |
| MISO | `2026-08-09-miso-148-basis-aware` | false | `["P1"]` |
| NYISO | `2026-08-08-nyiso-132-cf-arm` | false | `["P1"]` |
| PJM | `2026-08-04-pjm-152-collapse` | false | `["P1"]` |

**Five of six on P1 alone; NEISO alone on P1+P2 and scored on P2.** The neiso-84 escalation —
`replay_keeper` re-injecting `meta.json` flags **after** the `--enable-legacy-p2` gate — is neither
resolved nor worsened.

### (ii) `campd-unit-outages-NEISO.csv` still mis-routes Stony Brook's diesel peakers

Plant **6081** Stony Brook Energy Center, at HEAD:

| unit | `plant_group` | rows |
|---|---|---|
| 001 / 002 / 003 | CC_REGULAR | 22 / 30 / 7 |
| **004** | **CC_REGULAR** | **74** |
| **005** | **CC_REGULAR** | **74** |

Unchanged from neiso-95 §3.5 — **74 rows each**, exactly. **The stated mechanism is confirmed rather
than carried forward on assertion:** the `plant_group` enum documented at
`src/market_sim/data/fleet/__init__.py:188` is `CC_CHP, CC_REGULAR, COAL, CT_CHP, CT_PEAKER, ST_GAS,
ST_CHP` — **it has no oil or diesel member at all** — and
`derive_campd_unit_outages.py:1112` keys the map by **plant code**
(`group_by_code[int(g.plant_code)] = g.plant_group`), skipping units whose group is empty. So the
diesel peakers inherit whatever group the plant's CC units carry, and outages on machines that are not
in the CC block derate a fully-available CC block.

**Both should be settled together in one re-solve**, as neiso-95 recommended. Not attempted here.

---

## 6. Task 5 — no in-sample delta, therefore NO RUN

The prompt's condition did not fire. The intake **does not touch the tuned years**, proven rather than
argued:

- the 2018–2025 parquet rows are **byte-unmoved** — verified twice, before and after the 2026 merge,
  and the pre-intake rebuild reproduced the committed blob's md5 exactly (§1.2);
- `actual_lmp.json` gained exactly one entry; **every pre-existing entry is byte-identical** (§1.5);
- `actual_tail.json` is **byte-unchanged** (§3);
- and, decisively, **nothing this session landed is a solve input at all.**
  `actual_lmp_hourly_NEISO.parquet` is a **scoring target** read by the scorer and the deriver; no LP
  reads it. The only code change to a solve-adjacent module is `neiso_zone_hourly`'s source selection,
  which reads the workbook first and so returns bit-identical frames for every committed year.

> **An intake that does not touch the tuned years is not a delta. No solve was run; nothing was
> registered.** Rule 15 `[R-DASHBOARD]` and rule 16 `[R-ALLYEARS]` are not engaged.

**Incidental, noted not chased:** upstream PR #3982 (`bloat-b3-hourly-prune`, in this branch's base)
deleted the **superseded** `results/calibration/neiso87_control_A/hourly/*.parquet`. The current
keeper's sidecars are untouched, but neiso-95 §1.5's counterfactual — recomputing the superseded
keeper's 0-hour tail — is no longer reproducible from those files. Its **conclusion** is unaffected and
recorded; only the re-run is gone.

---

## 7. Rule compliance

| rule | status |
|---|---|
| 1 `[R-STRUCT]` | No mechanism armed, tested or proposed. §1.4 and §4.3 both decline to fix a structural defect, on the grounds that it is structural and needs its own proof — not on any residual argument. |
| 12 `[R-PARALLEL]` / 16 `[R-ALLYEARS]` | Not engaged — no solve, no bundle. |
| 13 `[R-MEASURED]` | No measured outcome fed back. The actuals are a **scoring target**, never a fitted input; nothing is pinned or tuned. The route-equivalence and solvability claims are measured, not asserted. |
| 14 `[R-ACCURATE]` | The intake replaces "no data" with the market's own published prices. §1.4 puts a real DST defect in a committed input on the record with its measurement rather than burying it, and declines to paper over it. |
| 15 `[R-DASHBOARD]` | **No run produced ⇒ nothing to register.** |
| 22 `[R-HOLDOUT]` | **Freeze VERIFIED ACTIVE at HEAD (twice — session start and post-rebase) and NEVER ENGAGED. NO year solved, scored or registered — 2019, 2020, 2021, 2022 and H1-2026 all unsolved.** This session is a **data intake**, which the amended rule leaves unrestricted and which needs no marker: *"what is held out is the SCORE, never the DATA."* `holdout-freeze.json` and `calibration-complete.json` are **unedited**; the `final` block was read only to report its state and was **not written**. `actual_tail.json` is byte-unchanged and the 2026 row is **withheld by the gate**. The §3 counterfactual uses an **in-memory** marker and writes nothing. **NEISO's locked test remains NEVER GRANTED and NEVER SPENT.** |
| 23 `[R-FROZEN-DERIVE]` | `derive_actual_lmp.py` and `derive_actual_tail.py` were re-run as **source-coverage** re-derivations (a new year of published data), never as a response to a residual. No measured-behaviour parameter re-derived. The `actual_lmp.json` re-run added one year's entry and changed no other. |
| 24 `[R-REGISTRY]` | No tunable touched; no `ScenarioConfig` field added or changed. |
| 25 `[R-ISO-SCOPE]` | **NEISO files only.** No other ISO's shard, keeper, marker, matrix cell or input was edited. Other ISOs are **read** for cross-checks (§1.5) and to establish that the partial-year gate is ISO-generic (§4.3); §4.3 explicitly refuses to fix that shared gate here for exactly this reason. |
| 26 `[R-DELETE]` | Nothing widened or zeroed in place of a deletion. |
| 27 `[R-PUSH]` | Opus session (`claude-opus-5`). No file bulk-rewritten from regenerated response content. Branch created server-side first, then fetch + rebase + push, per the stated push hazard. Every pushed file ≥300 lines was blob-verified against the remote after pushing (`derive_actual_lmp.py` 1,255 L, `fetch_neiso_smd_zonal_lmp.py` 339 L, `neiso96_smd_route_equivalence.py` 332 L, and the data blobs) — all MATCH. `derive_actual_lmp.py` was edited surgically in place, not rewritten. |
| 28 `[R-MECH-MATRIX]` | **No mechanism tested ⇒ no cell verdict minted.** No lever opened; the NEISO queue stays cleared. |

---

## Appendix — reproduction

```
uv run python scripts/data/fetch_neiso_smd_zonal_lmp.py --start 2026-01-01 --end 2026-06-30
uv run python scripts/data/derive_actual_lmp.py --isos NEISO --years 2026
uv run python scripts/data/derive_actual_tail.py            # byte-unchanged output
uv run python scripts/probes/neiso96_smd_route_equivalence.py --sample-dir <sampled days>
uv run python scripts/probes/neiso96_intake_and_tail_priming.py
uv run python scripts/probes/neiso96_h12026_solvability.py
uv run python -m pytest tests/test_fetch_neiso_smd_zonal_lmp.py -q

# the reproduce-check that gated the extension:
uv run python scripts/data/derive_actual_lmp.py --isos NEISO \
    --years 2018 2019 2020 2021 2022 2023 2024 2025 --parquet-only
md5sum data/raw/_validation-source/actual_lmp_hourly_NEISO.parquet
#   -> 3323efe038ab1bdb33382764eff4bfd0, unchanged
```

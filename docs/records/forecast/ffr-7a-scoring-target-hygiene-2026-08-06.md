# FFR-7A — Retirement scoring-target hygiene: physical exits, not paper dates

**Session.** FFR Wave 7, DATA/SCORER lane (owner decision **D-21(b)**, sitting Addendum V.5/V.6,
signed 2026-08-06). Branch `claude/retirement-scoring-target-fix-yyd4py`, off `origin/main`
`746661f1`. Evidence base: FFR-6A `docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md`
§3.3, admissibility verdict rows **5a/5b**.

**No model mechanism, no `ScenarioConfig` field, no arming, no keeper contact, no solve.** The
deliverable is the corrected scoring target plus a committed-artifact re-grade of the two
registered FFR-5D arms.

**Verdict row 5c — honouring announced fossil planned-retirement dates in hindcast arms — is
REFUSED by the owner. It is not implemented here, and this document does not re-propose it.**
`forecast_fossil_retirement_economic=True` still means the economic screen governs fossil
phaseout; V H Braunig's vintage-2020 planned-retirement dates are still ignored by the solve, by
design. Nothing in this session's diff touches that path.

---

## 0. Headline

| | before | after |
|---|---|---|
| What dates a retirement | the EIA-860 **reported `Retirement Year`**, verbatim | **`min`(reported year, start of the final unbroken run of `OS`/`RE` statuses)** |
| Which statuses count as an exit | `RE` only | `OS` **and** `RE` (`SB`/`OA` are available capacity by EIA's own definition and still do not count) |
| Which releases are read | the current release's retired sheet | the whole committed release series — `vintage_2018…2024` + current |
| Units dead at the fleet vintage | scored against | dropped (`FLEET_VINTAGE_YEAR`, `--fleet-vintage`) |

**ERCOT:** J T Deely 1+2 (932 MW, paper-dated 2023, physically `OS` since 2018) is **out**;
V H Braunig 1+2 (477 MW, `OS` in RY2025) is **in**. Both charter targets hit.

**But the corrected ERCOT target is bigger, not smaller: thermal 1.534 → 2.294 GW.** The charter
expected the shipped arm's `0.000 GW` to "grade correctly against a ≈0 GW economic-exit truth."
**It does not, and the surprise is reported before it is interpreted — see §4.**

---

## 1. What was measured, and what was changed

Both defects named in verdict row 5b are real, were re-verified at this session's HEAD, and are
fixed from **one** EIA-860 field — `Status` on Schedule 3, read across releases.

**Source fields used** (rule 23: the re-derivation cites its source data). All from the committed
EIA-860 release series under `data/raw/eia-860/`:

| field | sheet | use |
|---|---|---|
| `Status` (`status`) | operable + retired-and-canceled, every release | the exit evidence: `OP`/`SB`/`OA`/`OS`/`RE`/`CN`/`IP` |
| `Retirement Year` | retired-and-canceled | the reported (paper) date, now an upper bound rather than the answer |
| `Operating Year` | operable | dates the **current** release (max COD == reporting year; verified on all 7 vintages) |
| `Plant Code` / `Generator ID` | both | the unit key |
| `Balancing Authority Code` | operable / plant sheet | ISO scope, resolved from whichever release carries the unit |
| `Nameplate Capacity (MW)`, `Technology`, `Energy Source 1`, `Prime Mover`, `State` | both | row metadata, from the most recent release carrying the unit |

### 1.1 The dating rule (`physical_exit_year`)

1. If the **most recently observed** status is active, there is **no exit** — this is what keeps a
   *reversed* retirement (Palisades: `RE` 2022, back to `OP` by RY2025) from scoring off a stale
   `RE` row.
2. Otherwise the exit is the **first year of the final unbroken run of `OS`/`RE`**.
3. Answer = `min(that run start, reported Retirement Year)`. The reported date wins in the normal
   case; the status evidence corrects it **down** when the registry itself shows the unit was
   already out of service years before the paper date.

Only *observed* years participate: a release that omits the unit — or ships no retired sheet at
all — is a **gap**, never a return to service. (`vintage_2023`/`vintage_2024` carry the operable
sheet only; that is now documented in `data/raw/eia-860/README.md`.)

### 1.2 The vintage gate (verdict row 5a)

`FLEET_VINTAGE_YEAR = min(WINDOW) - 1 = 2020` — derived from the window, not written as a
literal, so the two cannot drift. A unit already `OS`/`RE` at that release is dropped, because the
graded arm's base fleet cannot carry it: `src/market_sim/data/fleet/eia860.py:632,893` keeps
`status == "OP"` rows **only**. `--fleet-vintage <year>` overrides; `-1` builds an ungated target.

**Choice justified against the information gate.** Row 5a offered "the target, the vintage base
fleet, or both". This session fixes **the target**, for two reasons. (a) It is the narrower change:
the base fleet already excludes these units — the defect is that the *target* graded against
units the fleet was correctly never given. (b) Everything used is admissible under rule 13's
benchmark branch: the vintage status is **vintage-visible** (the RY2020 release published it), and
the later releases' status transitions are **outcome-registry data used only as a validation
target**. No measured outcome enters any solve path; this builder writes a scoring target and
nothing else.

**Scope note (deliberately not taken).** The gate drops `OS`/`RE`-at-vintage only, as row 5a
words it. It does **not** drop units that were `SB` or `OA` at the vintage, nor units absent from
it — even though the fleet loader carries none of those either (it re-carries `OA` only, through
its own channel). Widening the gate to "keep only units that were `OP` at the vintage" is the
natural next question and would remove more rows; it is a judgment this charter did not
authorise, and it is left for the owner.

### 1.3 A third defect found while fixing the first two

Reading the release series exposed a coverage hole far wider than the two plants the hand-curated
RD-5 gap-fix patched: **of the 442 units the `vintage_2022` retired sheet dates to 2021-2022, 106
are absent from the current release's retired sheet.** EIA prunes older retirements out of an
Early Release rather than carrying them forward. The old target therefore silently missed, among
others, most of the **PJM 2022 coal wave** (+3.27 GW in that one cell). The release-series read
recovers all 106 generically. Indian Point 3 no longer needs the curated override; **Palisades
still does**, correctly — its latest status is `OP`, so the status rule declines to call it an
exit, and the RC-0B adjudication of a since-reversed retirement stays open and untouched.

---

## 2. Per-ISO delta

Regenerated: **ERCOT, PJM, MISO, NYISO, NEISO** (`capacity_actuals_<iso>.csv`). CAISO has no
committed target and none was created.

**Additions are byte-identical in all five files** (`cmp` on the `^addition,` rows: 784 / 692 /
740 / 501 / 541 rows unchanged). The fix touches retirements only.

| ISO | retirement rows | thermal GW | all-fuel GW | dropped | added | re-dated |
|---|---|---|---|---|---|---|
| ERCOT | 26 → 44 | 1.534 → **2.294** | 1.541 → 2.680 | 2 | 20 | 1 |
| PJM | 255 → 305 | 11.121 → **15.062** | 11.203 → 15.243 | 21 | 71 | 1 |
| MISO | 202 → 289 | 15.227 → **17.369** | 15.352 → 17.600 | 2 | 89 | 9 |
| NYISO | 57 → 99 | 1.488 → **1.711** | 1.496 → 1.757 | 8 | 50 | 2 |
| NEISO | 42 → 85 | 0.951 → **3.253** | 0.957 → 3.274 | 2 | 45 | 11 |

### 2.1 Every changed row, named and sourced

**All 334 changed rows are committed as `docs/handoffs/ffr-7a/target-delta.csv`** — one row per
change, carrying `iso, change, unit_id, plant_id, fuel, mw, old_year, new_year`, the unit's full
**`eia860_status_series`** across releases, and the **`eia860_reported_retirement_year`** the old
builder used. Regenerate with `uv run python scripts/probes/ffr7a_target_delta.py` (it reads the
"before" side out of git, so nothing is kept by hand).

Decomposition by cause:

| change | cause | rows | MW |
|---|---|---:|---:|
| added | `OS` mothball, never papered `RE` — invisible to the old builder | 176 | 5,638 |
| added | release-series recovery — dropped from the current retired sheet (§1.3) | 98 | 6,414 |
| added | `OS` mothball later papered | 1 | 65 |
| dropped | physical cessation **before** the window (paper-date correction) | 35 | 2,112 |
| re-dated | moved back to the `OS` transition | 24 | 766 |

Added MW by cause × ISO:

| cause | ERCOT | PJM | MISO | NYISO | NEISO |
|---|---:|---:|---:|---:|---:|
| `OS` mothball (both variants) | 1,858 | 555 | 1,548 | 506 | 1,237 |
| release-series recovery | 213 | 4,143 | 821 | 57 | 1,181 |

(ERCOT's 1,858 = 1,793 never-papered + the single 65 MW papered-later row; every other ISO's
mothball MW is entirely never-papered.)

### 2.2 Fuel × year MW delta (new − old), retirements

<details><summary>ERCOT</summary>

| fuel | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|
| coal | · | · | **−932.0** | · | **+1008.0** | +76.0 |
| gas_cc | · | +64.8 | +119.0 | +7.6 | · | +191.4 |
| gas_ct | · | · | +6.0 | · | **+482.0** | +488.0 |
| hydro | · | +4.8 | +5.2 | · | · | +10.0 |
| oil | · | +4.7 | · | · | · | +4.7 |
| other | · | · | · | · | +45.9 | +45.9 |
| storage | · | · | +2.0 | −2.0 | +100.0 | +100.0 |
| wind | +213.0 | +10.0 | · | · | · | +223.0 |
| **all** | +213.0 | +84.3 | −799.8 | +5.6 | +1635.9 | **+1139.0** |

</details>

<details><summary>PJM</summary>

| fuel | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|
| biomass | +9.7 | +0.2 | +2.2 | +1.6 | +5.0 | +18.7 |
| coal | +143.5 | **+3269.9** | · | · | · | +3413.4 |
| gas_cc | +141.7 | +292.2 | · | · | · | +433.9 |
| gas_ct | −110.6 | +94.2 | +41.5 | −398.1 | +391.6 | +18.6 |
| hydro | +0.8 | +0.4 | · | · | −4.3 | −3.1 |
| oil | +22.8 | +33.3 | · | −1.8 | +2.7 | +57.0 |
| other | · | · | −15.0 | +32.0 | +9.5 | +26.5 |
| solar | · | +2.5 | · | · | · | +2.5 |
| storage | +48.6 | · | · | +20.0 | · | +68.6 |
| wind | +4.0 | · | · | · | · | +4.0 |
| **all** | +260.5 | +3692.7 | +28.7 | −346.3 | +404.5 | **+4040.1** |

</details>

<details><summary>MISO</summary>

| fuel | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|
| biomass | +93.4 | +25.2 | +1.4 | +49.6 | +3.8 | +173.4 |
| coal | +11.5 | +869.6 | −11.5 | −216.0 | +846.0 | +1499.6 |
| gas_cc | +336.8 | · | +57.0 | −57.0 | · | +336.8 |
| gas_ct | +71.0 | +82.7 | +2.3 | −63.9 | −0.8 | +91.3 |
| hydro | +0.4 | +5.2 | +8.9 | +2.3 | · | +16.8 |
| oil | +27.4 | +4.9 | +5.0 | −0.8 | +4.2 | +40.7 |
| other | +25.0 | · | +23.0 | +23.0 | · | +71.0 |
| wind | +12.5 | · | +2.5 | +11.8 | −8.5 | +18.3 |
| **all** | +578.0 | +987.6 | +88.6 | −251.0 | +844.7 | **+2247.9** |

</details>

<details><summary>NYISO</summary>

| fuel | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|
| biomass | +1.6 | · | +55.5 | · | · | +57.1 |
| gas_cc | · | +55.0 | · | · | · | +55.0 |
| gas_ct | **−300.3** | +41.0 | −39.2 | +10.4 | +79.0 | −209.1 |
| hydro | +1.6 | · | +1.3 | +12.0 | +22.6 | +37.5 |
| oil | +20.0 | · | · | +0.3 | +300.0 | +320.3 |
| storage | · | · | · | +1.0 | · | +1.0 |
| wind | · | · | · | · | −0.3 | −0.3 |
| **all** | −277.1 | +96.0 | +17.6 | +23.7 | +401.3 | **+261.5** |

</details>

<details><summary>NEISO</summary>

| fuel | 2021 | 2022 | 2023 | 2024 | 2025 | total |
|---|---|---|---|---|---|---|
| biomass | +130.7 | +99.4 | +13.1 | · | −42.2 | +201.0 |
| coal | +100.0 | · | · | · | +245.6 | +345.6 |
| gas_cc | +139.3 | · | · | −101.0 | · | +38.3 |
| gas_ct | +126.1 | +111.2 | +163.5 | +3.0 | +186.5 | +590.3 |
| hydro | +1.6 | · | +3.6 | +2.4 | +5.5 | +13.1 |
| oil | **+632.1** | +58.5 | +6.0 | +2.4 | **+427.4** | +1126.4 |
| wind | · | · | +2.0 | · | · | +2.0 |
| **all** | +1129.8 | +269.1 | +188.2 | −93.2 | +822.8 | **+2316.7** |

</details>

### 2.3 Every dropped row ≥ 25 MW (the risky direction), with its evidence

Each is the Deely pathology: the registry's own `Status` says the unit was gone before the window
opened, whatever the paper date claims.

| ISO | unit | fuel | MW | old year | `Status` series |
|---|---|---|---:|---:|---|
| ERCOT | `6181_1` J T Deely 1 | coal | 486.0 | 2023 | `2018:OS;2019:OS;2020:OS;2021:OS;2022:OS;2025:RE` |
| ERCOT | `6181_2` J T Deely 2 | coal | 446.0 | 2023 | `2018:OS;2019:OS;2020:OS;2021:OS;2022:OS;2025:RE` |
| MISO | `202_1` | gas_ct | 120.0 | 2024 | `2018:OP;2019:OP;2020:OS;…;2025:RE` |
| NEISO | `1660_CC2` Potter Station 2 | gas_cc | 76.0 | 2024 | `2018:OP;2019:OP;2020:OS;…;2025:RE` |
| PJM | `54081_GEN1`, `54081_GEN2` | coal | 57.4 ×2 | 2021 | `2018:OP;2019:OP;2020:OS;2021:RE;…` |
| PJM | `55281_GT05…GT12` (8 units) | gas_ct | 50.9 ×8 | 2024 | `2018:OP;2019:OA;2020:OS;…;2025:RE` |
| PJM | `2917_7`, `2917_8`, `2917_9` | gas_ct | 100.6 | 2021 | `2018:OS;2019:OS;2020:OS;2021:RE;…` |
| NYISO | `2500_GT21…GT34` Ravenswood (7 units) | gas_ct | 42.9 ×7 | 2021 | `2018:SB;2019:OS;2020:OS;2021:OS;2022:RE;…` |
| NEISO | `1660_CC3` Potter Station 2 | gas_cc | 25.0 | 2024 | `2018:OP;2019:OP;2020:OS;…;2025:RE` |

Plus 10 rows below 25 MW (36.4 MW). Full list in `target-delta.csv`.

### 2.4 The vintage gate's own effect (5 rows, 38 MW)

The dating rule removes vintage-dead units by itself whenever they never returned (their exit
lands before 2021), so the gate bites **only** on units that were `OS` at 2020, came back, and
exited again inside the window — 5 rows across all five ISOs:

| ISO | unit | fuel | MW | exit | `Status` series |
|---|---|---|---:|---:|---|
| NEISO | `10700_TG6` | biomass | 16.0 | 2023 | `2018:OS;2019:OS;2020:OS;2021:OP;2022:OP;2023:OS;2024:OS;2025:OS` |
| PJM | `10398_GENA` | other | 15.0 | 2023 | `2018:OS;2019:OS;2020:OS;2021:OS;2022:OP;2025:RE` |
| PJM | `7279_2` | hydro | 3.9 | 2025 | `2018:OP;2019:OS;2020:OS;…;2023:OA;2024:OA;2025:RE` |
| PJM | `56363_GEN 1` | oil | 1.8 | 2024 | `2018:OA;2019:OS;2020:OS;2021:OS;2022:OP;2023:OP;2025:RE` |
| PJM | `7279_1` | hydro | 1.3 | 2025 | `2018:OP;2019:OS;2020:OS;…;2023:OA;2024:OA;2025:RE` |

The gate is therefore *reported* rather than load-bearing at vintage 2020 — but it is not
redundant: it is the only thing that catches this shape, and it does the real work at any other
`--fleet-vintage` (e.g. a vintage-2023 crossover arm).

---

## 3. Re-score of the two registered FFR-5D arms — committed artifacts only, no solve

`uv run python scripts/probes/ffr7a_rescore_ffr5d_arms.py`. The model side is reconstructed from
each arm's own committed `crossover_score.json` per-fuel `model_gw` and graded by the **shipped**
`score_capacity_hindcast.score_retirements`, so the numbers come from the production scorer.
`score_retirements` consumes the model side only as per-fuel MW for every banded metric, so
total / per-fuel / recall / false-retire are **exact**. The one un-banded diagnostic derived from
model *unit ids* — `plant_recall_frac` — is not recomputable (the registered bundles carry no
evolution ledger) and is reported `None`; both arms committed 0.0, and neither retired any fuel
the target's ≥300 MW units belong to, so 0.0 stands regardless.

**The arms' committed bundles are untouched and nothing was re-registered.**

| metric | shipped BEFORE | shipped AFTER | unified BEFORE | unified AFTER |
|---|---|---|---|---|
| actual thermal GW | 1.534 | **2.294** | 1.534 | **2.294** |
| model thermal GW | 0.000 | 0.000 | 10.943 | 10.943 |
| `err_frac` / band | −1.000 **FAIL** | −1.000 **FAIL** | +6.135 **FAIL** | **+3.770 FAIL** |
| recall ≥300 MW | 0 / 3 = 0.0 **FAIL** | 0 / **2** = 0.0 **FAIL** | 0 / 3 **FAIL** | 0 / **2** **FAIL** |
| false-retire GW (frac) | 0.000 (0.00) PASS | 0.000 (0.00) PASS | 10.943 (1.00) **FAIL** | 10.943 (1.00) **FAIL** |

Per-fuel actual GW, before → after (model unchanged):
`coal 0.932 → 1.008` · `gas_cc 0.080 → 0.271` · `gas_ct 0.502 → 0.990` · `biomass 0.019 → 0.019` ·
`oil 0.000 → 0.005` · `gas_st 0.000 → 0.000`.

The ≥300 MW thermal set changed identity, not just count: **old** {Deely 1 486, Deely 2 446,
Decker Creek 2 405} → **new** {Sandy Creek 1008, Decker Creek 2 405}.

---

## 4. The re-score surprised. Reported before interpreted.

**The charter's expectation did not hold.** It expected the shipped arm's in-window "0.000 GW
executed" to "grade correctly against a ≈0 GW economic-exit truth." It does not: the corrected
ERCOT target is **larger** (1.534 → 2.294 GW thermal), so the shipped arm's zero still grades
`err_frac = −1.000`, **FAIL**, now against a bigger truth.

**Why.** FFR-6A §3.3's "≈0 GW" was a claim about the **economic channel**, reached by decoding the
*then-known* 1.534 GW into non-economic causes. FFR-7A fixes *which physical exits exist and
when* — it does **not** partition the target by channel, and row 5b did not ask it to. Removing
Deely (−0.932 GW) is more than offset by **+1.7 GW of physical exits FFR-6A could not see**,
because they were invisible in the old target: `OS` mothballs never papered, plus units dropped
from the current retired sheet.

**The consequential one: Sandy Creek (`56611_S01`), 1008 MW supercritical coal, `OP` in every
release through RY2024 and `OS` in RY2025.** It is now the ERCOT target's largest in-window exit
and its only ≥300 MW coal exit, and it was `OP` at the vintage-2020 fleet basis — i.e. it is a
unit the arm's fleet **does** carry and a screen **could** retire. FFR-6A's §3.3 exit decode
never examined it, because the old target did not contain it.

I have **not** measured whether Sandy Creek's margins cleared its bar, and make no claim either
way. What can be said is bounded and factual: FFR-6A's "ERCOT's true margin-driven exit total in
2021-2025 is ≈ 0 GW" was derived from a four-row decode of a target that is now known to have been
missing this unit, so **that conclusion needs re-deriving on the corrected target** before it is
relied on again. That is a finding for the owner, not an adjudication made here.

**The unified arm behaved exactly as expected.** Its 10.943 GW `gas_st` wave still FAILs, and its
false-retire is unchanged at 10.943 GW / frac 1.00 — a real defect of the forward price object
(D-21(a), DEFERRED), not of the target. The `err_frac` improvement 6.135 → 3.770 is purely the
denominator growing; no model behaviour changed and nothing about it should be read as progress.

### 4.1 A scoring seam this session found but did not fix

The model retires `gas_st`; the target can never contain `gas_st`. `data.fleet._map_fuel_type` —
the taxonomy the builder shares with the fleet loader — maps natural-gas steam turbines to
`gas_ct` (there is no `gas_st` branch), while the CAMPD plant-binning path gives the model a
distinct `gas_st` class. So V H Braunig's 477 MW lands in the target as **`gas_ct`**, and the
unified arm's 10.9 GW of `gas_st` can never be credited against any actual, however right it
might one day be. This is **out of this charter** (rows 5a/5b are status hygiene, not taxonomy)
and was deliberately left alone — changing `_map_fuel_type` would re-class steam-gas rows in every
ISO and confound the delta above. Flagged as a candidate for its own charter.

---

## 5. Limitations

* **Left-censoring.** The series starts at `vintage_2018`; a unit already inactive then is dated
  at 2018. Harmless for a 2021-2025 window (it lands outside either way).
* **Plant-code changes are not reconciled.** One instance across all five ISOs: PJM `69979_GT8`
  and `69979_GT9` (MPH Elwood, 192 MW each, COD 1999/2001) first appear in the RY2025 release
  under a *new* plant code, already `OS`, so they are dated 2025 with a one-observation history.
  384 MW of PJM's 15.06 GW thermal (2.5 %). Named here rather than silently carried.
* **`vintage_2023` / `vintage_2024` ship no retired sheet.** Those years contribute operable-sheet
  statuses only. Treated as gaps, never as absence-of-unit.
* **The gate is vintage-2020-specific** and baked into the committed CSV. It is the right vintage
  for the plain hindcast (window = vintage + 1), and looser — never tighter — than a
  vintage-2023 crossover arm would want.

---

## 6. Governance

* **Rule 13/14 posture.** Everything used is vintage-visible registry metadata or outcome-registry
  data consumed **only** as a validation target (rule 13's benchmark branch). No measured outcome
  is wired into any solve path. Rule 14 (prefer accurate data) is the direct justification for
  counting `OS` exits: the registry's own status is the accurate statement of whether a unit is in
  the fleet, and the paper date is the estimate that was silently compensating.
* **Rule 22.** No solve, no scoring run, no registration touched any out-of-training year. The
  target window is unchanged at 2021-2025 (a test asserts no target carries a year outside it);
  the pre-2021 vintages are read for **status metadata**, never as scored years. No holdout marker
  was spent, and the holdout freeze is untouched.
* **Rule 23.** The re-derivation cites its source data (§1, field table). Nothing was re-derived
  because a residual moved — the trigger is the EIA-860 `Status` field the old builder ignored.
* **Rule 27.** `build_capacity_actuals.py` (585 lines) and
  `tests/curation/test_build_capacity_actuals.py` (397 lines) were edited locally and pushed as
  on-disk bytes via `git push`; no `push_files` on a ≥300-line file, no regenerated full-file
  content. Blob verification recorded in §7.
* **Rule 28.** No mechanism was proposed, tested or changed, so **no matrix cell is adjudicated
  and no header re-stamp is due.** The FFR-6A evidence note on ERCOT
  `capacity_screen_unified_lookahead` (verdict `O`) is unaffected — this session neither arms nor
  refutes it.
* **Rule 15/16.** Nothing registered on either dashboard: no run was solved, and the FFR-5D arms
  keep their existing registrations.

---

## 7. What was NOT changed

1. **Verdict row 5c** — refused by the owner; not implemented, not re-proposed.
2. **No model mechanism, no `ScenarioConfig` field, no arming, no keeper contact, no solve.**
3. **`scripts/score_capacity_hindcast.py`** — untouched. The re-score calls it; it does not change.
4. **The FFR-5D arms' committed bundles and registrations** — untouched. The re-score table lives
   here, not in a re-registered artifact.
5. **`build_additions`** — untouched; addition rows are byte-identical in all five files.
6. **`data.fleet._map_fuel_type`** — untouched (§4.1 seam left open).
7. **The RD-5 gap-fix file** — untouched, still required for Palisades, and the RC-0B
   reversed-retirement adjudication is left open.
8. **The vintage gate was not widened** to `SB`/`OA`/absent-at-vintage units (§1.2).
9. **No CAISO target** was created (none exists).
10. **No FFR-6A re-derivation.** §4 states that its ≈0 GW conclusion needs re-deriving on the
    corrected target; this session does not perform that, and does not overwrite the FFR-6A
    document, which stands as the historical record of what was measurable at the time.

---

## 8. Artifacts

| path | what |
|---|---|
| `scripts/data/build_capacity_actuals.py` | the fix: `physical_exit_year`, `release_series`, `load_release_history`, `FLEET_VINTAGE_YEAR`, `--fleet-vintage` |
| `tests/curation/test_build_capacity_actuals.py` | 28 tests — the rule on hand-written status series, a three-release fixture tree incl. the vintage gate and an inertness check, committed-artifact smoke tests |
| `data/raw/_validation-source/capacity_actuals_{ercot,pjm,miso,nyiso,neiso}.csv` | regenerated targets |
| `docs/handoffs/ffr-7a/target-delta.csv` | **all 334 changed rows** with `Status` series + reported year |
| `scripts/probes/ffr7a_target_delta.py` | regenerates the delta artifact (reads the "before" side from git) |
| `scripts/probes/ffr7a_rescore_ffr5d_arms.py` | the §3 re-score, committed artifacts only |
| `data/raw/eia-860/README.md`, `data/raw/_validation-source/README.md` | doc sync: the 106-unit coverage hole, the partial 2023/2024 vintages, the new dating rule |

**Test status.** `tests/curation/test_build_capacity_actuals.py` 28 passed.
Full `tests/scoring/` run: 970 passed, 7 failed — **all 7 pre-existing**, reproduced unchanged at
`origin/main` in a clean worktree (`test_ff_readiness_battery.py` ×5, `test_forecast_parity.py`
×2: forecast-parity registry declarations for `ercot_storage_as_soc_reserve` /
`nyiso_seam_deliverability_envelope`). Nothing in this diff touches them.

## 9. Recommended next charters (none performed here)

1. **Re-derive FFR-6A §3.3's exit decode on the corrected ERCOT target** — specifically whether
   Sandy Creek's 2025 exit was margin-driven. This is the load-bearing input to the D-21(a) price
   object question and it is currently answered on a target now known to have been incomplete.
2. **Adjudicate the `gas_st` ↔ `gas_ct` taxonomy seam** (§4.1) — until it closes, no `gas_st`
   model retirement can be credited against any actual in any ISO.
3. **Decide whether the vintage gate should be `OP`-only** rather than `not OS/RE` (§1.2), which
   would also drop `SB`/`OA`-at-vintage units the base fleet does not carry.

# RESULT caiso-293 — the `chp_steam` floor is an energy average worn as an every-hour floor, and the repair stopped at its own gate

**Lane:** caiso-293 · **Date:** 2026-09-20 · **LP spent: ZERO.** No shard was launched — the
pre-registered gate G-4 failed and the PRECOMMIT declares it a hard STOP.
**Keeper untouched**: nothing armed, nothing disarmed, no derive re-run, no run registered, no
bundle written. The new gate ships **default off and byte-identical off**, proven by a true
two-version array diff.

PRECOMMIT (pushed before any code change or measurement of the arm):
`docs/PRECOMMIT-caiso293-chp-steam-duty-window-2026-09-20.md`.

---

## 0. The answer in three paragraphs

**The defect is real, it is exactly what rule 17 `[R-FLOOR-WINDOW]` names, and it is 20× larger
than its D-4 symptom.** `derive_thermal_tranches.py` builds
`steam_level_cf = on_freq × p50(loading-when-on)` — an **energy-equivalent annual average** —
and `fleet/arrays.py` applies that product as a **flat never-below floor across all 8,760
hours**. The two coincide only when `on_freq ≈ 1`. The whole `MECH_CHP_STEAM` floor is
**1,261.879 MW forcing 7.99–9.22 TWh/yr over 41 plants**; the keeper's 28 D-4 failing rows are
0.570 TWh of it. **Five of the thirteen metered floored plants are forced to deliver more energy
than their own meter recorded for the entire year** (Kingsburg 5.16×, McKittrick 2.22×, Badger
Creek 1.84×, Gilroy 1.56×, King City 1.01×, 2025).

**Two of the three candidate causes the lane instruction named are falsified.** Not membership:
all seven D-4-failing plants are EIA-860 `Status = OP`, `CHP = Y`, `IPP CHP`, topping-cycle —
none retired, mothballed or mis-flagged. Not the level *source* either: all seven carry
`chp_pmin_cf = 0.0`, so the `chp_steam_floor_p25` swap **creates** the entire floor rather than
superseding a smaller one — and **so do the three genuinely flat steam hosts**, which is why
disarming the swap is not a repair: it would delete 715 MW of correct floor. The cause is the
statistic's **semantics**, and the driver evidence splits the population cleanly: hour-of-day
on-frequency max/min is **1.00–1.04** on the three flat hosts the `(0, 24)` window's own comment
cites as its evidence, and **12.4–35.0** on the seven, whose profile peaks at h16–h20 — the
evening ramp — with a 4–11 h median run and 18–158 separate runs a year.

**The repair's window half is validated and its level half is wrong, so the lane stopped.** Of
four gates declared ex ante, three pass — including G-3, where the repair is a measured **no-op
on the flat hosts** (0.050–0.831 %/yr against a < 2 % bar). **G-4 fails at −10.220 % in 2025
against a < 10 % bar**, and the diagnosis is that the undiluted level I chose, `median_cf`, makes
the floor **5–14× the capacity of the tranches that carry it**, so it saturates against
`pmax × availability`. `median_cf` is the p50 of a plant's *total output when online* — its
commercial output, not its steam obligation. A floor needs a **never-below-when-online**
statistic, and **the committed artifact does not carry one.** No percentile was swept to find one
that clears the gate; that is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids.

---

## 1. The measurement (zero LP, all over committed artifacts)

Probes, all committed: `scripts/probes/caiso293_chp_steam_floor_census.py`,
`caiso293_window_placement.py`, `caiso293_gates.py`, `caiso293_g2_snapshot.py`.

### 1.1 The mechanism, sized

Rebuilt through the sanctioned `bundle_fleet.reconstruct_bundle_fleet` (carrying
`replay_keeper.DERIVED_RUN_YEAR_INPUTS`, caiso-292):

| class | plants | floor MW | forced TWh/yr 2022→2025 |
|---|--:|--:|--:|
| **A** D-4-failing cyclers | 7 | 48.463 | 0.148 / 0.145 / 0.198 / 0.137 |
| **B** cyclers the D-4 rider SKIPS (CT-only CEMS flag) | 3 | 5.256 | 0.043 / 0.043 / 0.043 / 0.042 |
| **C** flat steam hosts | 3 | 714.988 | 5.119 / 4.763 / 3.835 / 4.019 |
| **D** `eia923_cf` lens, no meter | 28 | 493.172 | 3.913 / 3.915 / 3.915 / 3.899 |
| **total** | **41** | **1261.879** | **9.223 / 8.866 / 7.992 / 8.096** |

The repair's whole reach is **A + B = 53.719 MW, 0.179–0.241 TWh/yr** (4.3 % of the floor MW).
Class C is untouched by construction; **class D cannot be reached at all** — 0 of 73
`eia923_cf` rows carry `median_cf`, so the identity is undefined there and CEMS-invisible cogens
keep today's construction by arithmetic rather than by a written exclusion.

### 1.2 The two populations are different machines

| | on-frac 2025 | hod max/min | median run | runs/yr | longest OFF |
|---|--:|--:|--:|--:|--:|
| **C** Elk Hills / Los Medanos / Salinas River | 0.96 / 0.68 / 0.96 | **1.00–1.04** | 387–3,300 h | 3–22 | 249–2,389 h |
| **A** the seven | 0.018–0.127 | **12.4–35.0** | **4–11 h** | 18–158 | 943–3,693 h |

McKittrick 2025 is off for one continuous stretch of **3,693 hours** (five months) while its
floor binds 8,741.

### 1.3 The window driver, adjudicated before the repair was chosen

Same window size, three placements, `lift = precision / on_frac` (1.0 = no better than flat):

| placement | class A mean lift | class C mean lift |
|---|--:|--:|
| **gross load** (`_window_src` default) | **5.29** | **0.999** |
| net load (`commitment_floor_window_netload`, SPP-66) | 4.55 | 0.999 |
| plants' own leave-one-year-out (month × hod) duty surface | 3.69 | 1.008 |

Gross load wins, so the repair arms no second gate. Net load losing is itself informative: these
plants follow total system load, not the solar-net residual.

---

## 2. The gates, reported as they fell

| gate | bar | result |
|---|---|---|
| **G-1** identity `on_frac × median_cf == steam_level_cf` | ≤ 0.05, every ISO | **PASS** — max abs err **0.000000** across all 13 artifacts |
| **G-2** off-inert | bit-identical | **PASS** — see §2.1 |
| **G-3** flat-host controls | < 2 %/yr | **PASS** — 0.831 / 0.363 / 0.505 / 0.050 % |
| **G-4** energy conservation, cyclers | < 10 %/yr | **FAIL** — +4.714 / +3.085 / +6.334 / **−10.220 %** |

G-1 also shows the mechanism is cross-ISO: `status == "ok"` CHP rows exist in NYISO per-unit
(17), CAISO (13), NWPP (7), SOCO (5) and SPP (3). Verdicts stay per-ISO (rule 25
`[R-ISO-SCOPE]`) and nothing here transfers.

### 2.1 G-2 — my first version of this check was wrong, and it is corrected rather than dropped

The first draft built the pre-change reference **in process**, reproducing
`min_gen[g, :] = pmin_mw` for every floored unit. That reference is wrong: `fleet/arrays.py`
clips every floor to `pmax × availability` and four later floor blocks legitimately overwrite the
same cells, so it counted correct behaviour as a diff and reported a **false FAIL of ~1.23 M
cells**. The sound form is a true two-version comparison — `caiso293_g2_snapshot.py` run once on
this tree and once on the pre-change tree, then diffed. Measured that way: **`min_gen`,
`min_gen_mechanism`, `chp_grid_pmin_mw` and `pmax` are all bit-identical across 2022–2025** with
the gate at its default. The probe now says so and no longer computes the bad form.

### 2.2 G-4 — why it failed, diagnosed rather than smoothed

Per-plant, 2025, gate OFF → ARMED:

| plant | floor MW off → on | carrying tranche cap | on_frac | hours off → on | forced MWh off → on | ratio |
|---|--:|--:|--:|--:|--:|--:|
| 10034 Gilroy | 16.646 → **82.810** | 22.577 | 0.201 | 8760 → 1761 | 35,060 → 29,967 | 0.855 |
| 10294 King City | 18.442 → **82.857** | 24.598 | 0.223 | 2285 → 509 | 32,391 → 27,221 | 0.840 |
| 10649 Bear Mountain | 3.169 → **25.355** | 3.895 | 0.125 | 8760 → 1095 | 25,404 → 22,869 | 0.900 |
| 10650 Badger Creek | 1.196 → **23.412** | 3.113 | 0.051 | 8760 → 448 | 10,477 → 8,464 | 0.808 |
| 50612 McKittrick | 1.465 → **24.697** | 3.113 | 0.059 | 8760 → 520 | 12,834 → 10,408 | 0.811 |
| 54749 Goal Line | 5.780 → **28.399** | 8.018 | 0.204 | 8760 → 1783 | 4,939 → 9,827 | **1.990** |
| *(10156, 10349, 10405, 54768 likewise)* | | | | | | 0.815–0.937 |
| **total** | | | | | **178,628 → 160,372** | **−10.220 %** |

**Every armed plant saturates.** The undiluted level puts the plant-level floor at 5–14× the
capacity of the tranches carrying it, so the realised floor is `pmax × availability` rather than
the level, and the energy stops being conserved — in both directions (Goal Line 1.990, Badger
Creek 0.808), which is the signature of a clip rather than a bias.

**The root cause is the level statistic, not the window.** `median_cf` is the p50 of a plant's
total output *when online*. For a merchant cycler running at 96 % CF when it runs, that is its
whole commercial output — not the portion a steam host obliges. A floor needs the
**never-below-when-online** level, and the committed artifact carries no such column:
`chp_pmin_cf` is the p2 of **all** hours (0.0 for every one of these plants, which is the
degeneracy WP-3 armed the swap to escape) and `p25_cf` / `median_cf` are the p25 / p50 of the
**online** hours.

So **the zero-derive-change property this arm was built on does not survive the level half.**
Substituting `p25_cf` because it happens to clear G-4 would be selecting a factor because it
makes a criterion pass — refused.

---

## 3. What landed on `main`, and what did not

**Landed** (all default-off or documentation; zero effect on any solve):

1. `ScenarioConfig.chp_steam_duty_window` (default `False`), registered in
   `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` + `TIER_TAGS` in the same
   commit (the nyiso-119 discipline), so **every pre-existing cache key is byte-stable**.
2. `campd_bins.thermal_tranche_chp_steam_duty` — the two factors, recovered by exact identity.
3. `Generator.chp_grid_pmin_on_frac` (default `1.0` = the pre-existing all-hours path) and the
   windowed `MECH_CHP_STEAM` block in `arrays.py`, which now reads the shared window series as
   its fifth consumer. The series resolution moved **above** the CHP block; it depends only on
   `config`, `netload_shape`, `load_shape` and `hours`, which no floor writes, so the move
   changes no value — and G-2 proves it.
4. **Four falsified claims corrected in place, not deleted** (rule 26 `[R-DELETE]` — a deleted
   justification is a re-armable one). Each asserted that the statistic "self-targets … no
   threshold parameter", and each is measurably false: `scenarios.py`
   (`chp_steam_floor_p25`'s rule-17 (b) clause), `campd_bins.thermal_tranche_chp_steam_level`,
   `derive_thermal_tranches.py`, and `legitimacy_diagnostics.D4_WINDOWS`'s `MECH_CHP_STEAM` row.
5. The mechanism-matrix row + a cell in all nine ISO shards (rule 28 duty (c)). CAISO reads
   **`R`** with the full gate record; every other ISO enters **`U`** (rule 25).

**Not landed, deliberately:** no solve, no bundle, no registration, no keeper change, no derive
re-run, no artifact byte moved.

`D4_WINDOWS[(MECH_CHP_STEAM, None)]` **stays `(0, 24)`** and the comment now says why: the repair's
window is a *top-k-by-load rank*, not an hour-of-day band, so D-4's window test cannot express it
in either direction — the test that actually binds this mechanism is the per-unit conduct rider,
which is where the defect surfaced.

### 3.1 Test state

`tests/unit/data` + `tests/unit/config`: **3,352 passed / 10 failed with the change, and the
identical 10 failed names on the clean rebased tree** — zero new failures. The same holds for
`tests/regression/test_persisted_identity.py` (the 6 `solve_surface_fingerprint` rows report
`0b6c20ac2fb77cee (206 rows)` **with and without** this change, so the drift is another lane's)
and `test_run_year_kwargs_recipe.py`'s complaint about caiso-291's probe. The mechanism-matrix
guard passes with `--base origin/main`; its two remaining warnings are labelled by the guard
itself as pre-existing NYISO/PJM prose-header drift.

---

## 4. THE DECISION THIS LANE OWES THE OWNER

The defect is confirmed and is a rule-17 violation. The window construction is validated. Only
the **level** is unresolved, and the three ways forward differ in what they cost and in which
rule they engage:

1. **Emit a never-below-when-online CHP level** from `derive_thermal_tranches.py` (e.g. the p2 of
   the online distribution — the sibling of `chp_pmin_cf` on the right sample) and re-run G-1…G-4
   unchanged. **Engages rule 23 `[R-FROZEN-DERIVE]`**: it adds a column and re-runs the derive.
   The motive is a structural defect, not a residual, which is the admissible ground — but it is
   the owner's call, and the percentile must be fixed ex ante rather than chosen against G-4.
2. **Keep the diluted level and window it anyway** — i.e. accept that the floor is an energy
   budget spread over the right hours rather than a physical level. Clears G-4 trivially
   (energy is conserved by construction) and still lifts the cyclers' placement 5.29×, but it
   leaves the floor's *magnitude* physically meaningless; I do not recommend it.
3. **Conclude these ten plants should carry no steam floor at all.** Their own p2 already says
   0.0, their EIA-860 CHP flag is a QF designation rather than evidence of an operating host, and
   their conduct is a merchant peaker's. This is the largest change and the most defensible on
   the driver evidence, and it is adjacent to the unruled `caiso_ra_bridge_startup_aware`
   question, so it is not mine to take.

My recommendation is **(1)**, with the percentile declared in a PRECOMMIT before it is computed.

A second, independent residual is measured and **not** bundled into any of them: the pooled
`on_frac` is a 2023–2025 average while these plants' on-frequency **collapsed** across the window
(Gilroy 0.110 → 0.035, McKittrick 0.039 → 0.018, Goal Line 0.037 → 0.024), so one pooled window
is too large in the later years and too small in 2022. The repo already names that gate family:
`mustrun_online_frac_per_year`.

---

## 5. Provenance, retrievability and G-DRIFT

* **Retrievability (rules 31 / 34):** nothing to retrieve — **no solve was run and no bundle
  exists**. The four probe artifacts (`results/calibration/_caiso293_*.json`) are gitignored;
  every number they carry is reproduced in this document and in the PRECOMMIT, which is what rule
  31 `[R-RETAIN]` means by "git history plus the RESULT doc remain the record". Nothing was
  deleted.
* **Shards (rule 33 `[R-SHARD-ARCHIVE]`):** none launched, so none to archive.
* **G-DRIFT (rule 29 `[R-SCREEN]` (b)):** not spent — no arm was solved, so no control was needed.
  caiso-292's audit of `e7091f56..HEAD` (every CAISO solve-path hunk INERT) stands unextended and
  uncited by any number here.
* The branch was rebased onto `origin/main` @ `12820d76` at the owner's request mid-lane.

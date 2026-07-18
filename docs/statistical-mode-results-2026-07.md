# D-7 statistical-mode A/B — all six ISOs (2026-07-03, in-scope four re-gated 2026-07-08)

**Companion:** `docs/model-legitimacy-audit-2026-07.md` §5.3/§7 (D-7),
`docs/legitimacy-scrub-prompts-2026-07.md` (S4 item 1),
`docs/audit-followup-tests-2026-06.md` (the one prior run — ERCOT only,
2026-06-16, against the since-superseded run 115b keeper).

**What this measures.** `--statistical-mode` (`scripts/run_calibration_full.py`,
`apply_statistical_mode`) turns off every per-hour/per-year answer-injection
overlay in one switch: the historic outage overlay (→ statistical WEFOR/POF),
the CT AS/RUC-deployment floor, the spatial reliability-deployment floor, the
ST WEFOR-residual relief, and per-plant EIA-923 monthly coal pricing (→ falls
back to the supply-class trajectory). Structural levers — offer curves, coal
passthrough sigmoids, cc-duct band, storage cycling — and the realized annual
Henry Hub gas price are untouched, so the delta isolates the forecast-machinery
skill prior from the backcast-only measured overlays.

> **Framing (2026-07-13, owner directive).** The single `--statistical-mode`
> switch groups two different classes of lever: **admissible measured inputs**
> (the historic outage overlay, per-plant F923 monthly coal pricing — CLAUDE.md
> rule-13 physical/market inputs with a forward analogue) and **merchant
> deployment floors** (the CT AS/RUC floor, the spatial
> reliability-deployment floor, the ST WEFOR-residual relief). For the
> admissible inputs, the keeper−statmode delta is the **backcast→forecast
> input gap** — what a forecast gives up to statistical stand-ins — and is
> **not** a caveat, deduction, or asterisk on the keeper's backcast result:
> a backcast is scored with the year's actual physical inputs by
> construction. Language below reading overlay-carried fit as "propping up"
> a keeper applies, under this framing, only to the deployment-floor
> component; the admissible-input component is forecast-uncertainty
> information (error bars, the crossover window), not a legitimacy signal.

**Method.** Each probe is a byte-faithful replay of the keeper's own
`meta.json` (`scripts/archive/run_statmode_probe.py`, built on the existing
`replay_keeper.py` kwarg-mapping) with only the statistical-mode delta
applied — no other flag changed. One invocation per ISO, all of that ISO's
keeper years solved sequentially within it.

> **2026-07-08 — the four in-scope ISOs re-gated to a same-SHA twin (G-10).**
> ERCOT, CAISO, PJM and MISO were each **re-solved from scratch** as a
> byte-faithful statistical-mode replay of their **current** keeper, all at one
> pinned HEAD SHA **`fab2254`**, so the D-7 gap is now same-SHA-comparable to
> the keeper it is quoted against (the G-10 honesty gate: a D-7 number may be
> quoted as skill only once its twin is a same-SHA replay of the current
> keeper). This retires the stale/confounded twins the earlier version of this
> document carried (ercot34, caiso51/58, pjm-76, miso-39). All four in-scope
> sections and the cross-ISO summary below are on this 2026-07-08 same-SHA
> basis and are scored under the **current v2.2 rubric** (`calibration_verdict.py`,
> `docs/calibration-determination-rubric.md` §9): 11 scored criteria
> (C1 fuel-mix, C2 sysvol, C3a/b/c price, C4 dispatch-corr, C5a CO2, C5b/c
> storage, C7 diurnal shape, C8 forced-energy share); **C6 governance is
> excluded** — every probe is intentionally unattested, so C6 reads UNATTESTED
> by construction and is not a comparable signal.
>
> | ISO | keeper (bundle) | statmode twin (run id / bundle) |
> |---|---|---|
> | ERCOT | `2026-07-08-ercot46-clock-steamgas` (`ercot46_clock_steamgas`) | `2026-07-08-ercot46-statmode` (`ercot46_statmode`) |
> | CAISO | `2026-07-07-caiso65-seam-envelope-clock` (`caiso65_seam_envelope_clock`) | `2026-07-08-caiso65-statmode` (`caiso65_statmode`) |
> | PJM | `2026-07-08-pjm-90-cchp-srmc` (`pjm90_cchp_srmc`) | `2026-07-08-pjm-91-statmode` (`pjm90_statmode`) |
> | MISO | `2026-07-08-miso-47-steamgas-ct` (`MISO/miso_47_steamgas_ct_drag`) | `2026-07-08-miso47-statmode` (`MISO/miso47_statmode`) |
>
> **NYISO and NEISO are out of scope for this re-gate (owner directive).**
> Their sections below are UNCHANGED from 2026-07-03 and remain **STALE** —
> their stale-boxes and re-solve-queue rows stand as-is until a separate
> authorized session re-gates them. **No offer curve, sigmoid or floor was
> tuned in response to any result here** (CLAUDE.md #1) — this is measurement
> only, a FROZEN-recipe replay at one SHA, not a re-tune.

**Environment note (not a config change).** This 2026-07-08 re-gate ran on a
15 GB RAM / 4-core box. ERCOT + CAISO ran concurrently (2 per-plant multi-zone
LPs, rule #12 cap), then PJM, then MISO solo; a 12 GB swap file (removed after)
covered MISO's per-generator reserve co-optimization
(`miso_reserve_pergen`: ~2,546 units pooled into 30 zone×fuel-class columns),
which alone peaks past physical RAM. No calibration flag was changed to work
around memory. Years ran strictly sequentially within each invocation.

---

## Cross-ISO summary

Criterion-status mix across the scored criteria (**C6 governance excluded**).
**ERCOT/CAISO/PJM/MISO are the 2026-07-08 same-SHA re-gate, scored on 11
criteria (C1–C8) under the current v2.2 rubric.** NYISO/NEISO are still the
superseded 2026-07-03 run on the original 9-criterion (C1–C5c) scoring against
a since-swapped keeper — their rows are **not** on the same basis and are kept
only until their own re-gate:

| ISO | keeper PASS/CAVEAT/FAIL/SKIP | statmode PASS/CAVEAT/FAIL/SKIP | fail count Δ |
|---|---|---|---|
| ERCOT | 5 / 3 / **2** / 1 | 3 / 0 / **7** / 1 | **2 → 7** (+5, of 11 scored) |
| CAISO | 2 / 1 / **6** / 2 | 1 / 0 / **8** / 2 | **6 → 8** (+2; price level *improves*, see below) |
| PJM | 5 / 2 / **2** / 2 | 1 / 0 / **8** / 2 | **2 → 8** (+6; largest swing) |
| MISO | 4 / 3 / **4** / 0 | 0 / 0 / **11** / 0 | **4 → 11** (+7; fails everything scored) |
| NYISO ‡ | 3 / 4 / **0** / 2 | 3 / 0 / **4** / 2 | **0 → 4** (STALE 2026-07-03, C1–C5c) |
| NEISO ‡ | 4 / 4 / **1** / 0 | 3 / 0 / **6** / 0 | **1 → 6** (STALE 2026-07-03, C1–C5c) |

‡ NYISO/NEISO rows are the superseded 2026-07-03 run against a since-swapped
keeper on the old 9-criterion scoring — out of scope this pass, kept flagged,
not carried as current (G-10). Not on the same denominator as the four re-gated
ISOs above.

**The gap is real and large everywhere it can be measured on a same-SHA basis.**
Every in-scope ISO's fail count rises (+2 to +7), and a second pattern holds
across all four: **every ISO's CAVEAT count collapses to 0 in statistical
mode.** The overlays are not just closing hard misses — they are what turns a
hard miss into a tolerable-looking near-miss; remove them and the near-misses
become clean fails rather than new categories of error. The one nuance is
CAISO, where the mean **price level** actually improves out-of-sample (the
overlays there carry the volume/CO2 side, not the price level).

---

## ERCOT — 2 → 7 fails (same-SHA twin of ercot46-clock-steamgas, 2026-07-08)

Same-SHA statistical-mode twin `2026-07-08-ercot46-statmode`
(`results/calibration/ercot46_statmode`) of the current keeper
`2026-07-08-ercot46-clock-steamgas`, HEAD `fab2254`. Both determinations
`NOT-YET`.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | PASS | **FAIL** | COAL_PRB over-runs once statistical outages replace measured: 2024 46.8→55.7 TWh (PASS→FAIL), 2025 51.0→58.9 TWh (PASS→FAIL) |
| C2 sysvol | CAVEAT | **FAIL** | COAL_PRB breaks the class band in 2024 & 2025 |
| C3a mean LMP | CAVEAT | **FAIL** | flips negative and large on all 3 yrs (vs RT): 2023 +9.3%→**−40.4%**, 2024 +6.5%→**−18.9%**, 2025 +4.9%→**−11.8%** (2025 was the PASS year) |
| C3b price shape | **FAIL** | **FAIL** | already failing; NRMSE ~doubles+ each yr: 2023 0.251→**0.877**, 2024 0.185→0.281, 2025 0.080→0.165 |
| C3c price tail | **FAIL** | **FAIL** | already failing; scarcity hours collapse further: 2023 model 104h→**19h** vs actual 181h |
| C4 dispatch corr | PASS | **FAIL** | coal r softens through the gate: 2025 0.777→0.729 (gas r holds ≥0.99) |
| C5a CO2 | PASS | PASS | worsens but stays in tolerance: +2%→**+5–6%** across the 3 yrs |
| C5b storage | SKIPPED | SKIPPED | no EIA-930 storage breakout, both sides |
| C5c storage shape | CAVEAT | **FAIL** | 2024 monthly discharge r 0.409→**0.110** |
| C7 diurnal shape (D-1) | PASS | PASS | CT_PEAKER/ST_GAS hour-of-day profile r stays ≥0.95 both sides — the *shape* tracks; it is the *level/volume* that blows out |
| C8 forced-energy share (D-2) | PASS | PASS | grounded-above-budget both sides (all binding mechanisms clear D-4, profile/CV gates pass); ST_GAS forced share rises 27%→**48%** (2023) but stays a clean grounded PASS |

**Verdict:** the finding replicates on the current keeper and the current
rubric — ERCOT's mean-LMP miss (C3a), a near-miss CAVEAT in-sample, flips to a
12–40% negative miss with overlays off, and the passing 2025 year fails.
Fuel-mix (COAL_PRB) and dispatch-correlation both drop from PASS to FAIL. The
historic-outage overlay is doing the heaviest lifting on both price level and
coal volume (consistent with the prior D2 ablation showing it as the dominant,
largely-defensible lever). C7/C8 both hold as clean PASSes — the CT/ST
forced-energy share grows but stays D-4-grounded and shape-faithful.

## CAISO — 6 → 8 fails (same-SHA twin of caiso65-seam-envelope-clock, 2026-07-08)

Same-SHA statistical-mode twin `2026-07-08-caiso65-statmode`
(`results/calibration/caiso65_statmode`) of the current keeper
`2026-07-07-caiso65-seam-envelope-clock`, HEAD `fab2254`. Both `NOT-YET`. This
retires the r2/v2-confounded caiso51 probes the re-solve queue flagged.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | **FAIL** | **FAIL** | CC_REGULAR over-run widens: 2024 64.4→67.0 TWh, 2023 61.8→63.4 TWh |
| C2 sysvol | CAVEAT | **FAIL** | gas system volume breaks band |
| C3a mean LMP | **FAIL** | **FAIL** | **improves** on all 3 yrs (still fails): 2023 +21.7%→+16.7%, 2024 +37.2%→+30.4%, 2025 +44.4%→+33.1% |
| C3b price shape | **FAIL** | **FAIL** | NRMSE improves each yr: 2023 0.304→0.275, 2024 0.484→0.418, 2025 0.464→0.351 |
| C3c price tail | **FAIL** | **FAIL** | over-counts scarcity both sides (model ≫ actual) |
| C4 dispatch corr | **FAIL** | **FAIL** | gas r worsens: 2024 0.771→0.728, 2025 0.546→0.436 (no coal fleet) |
| C5a CO2 | PASS | **FAIL** | worsens out of tolerance: 2024 +3.1%→+7.4%, 2025 +5.0%→+10.7% |
| C5b storage | SKIPPED | SKIPPED | no EIA-930 breakout |
| C5c storage shape | SKIPPED | SKIPPED | no EIA-930 breakout |
| C7 diurnal shape (D-1) | PASS | PASS | ST_GAS immaterial (<2% ISO load, not gated) both sides |
| C8 forced-energy share (D-2) | **FAIL** | **FAIL** | unchanged (keeper-side scoring row; 0% forced by the rebuilt floors on both sides) |

**Verdict:** CAISO remains the one ISO where the mean **price level improves**
out-of-sample — C3a and C3b both get *closer* to actual with overlays off,
where every other ISO's price miss roughly doubles. The overlays are instead
carrying the volume/CO2/dispatch side: fuel-mix and system volume widen, and
CO2 flips PASS→FAIL. So "the overlays are purely propping up the price level"
is *false* at CAISO; they prop up the volume and emissions side.

## PJM — 2 → 8 fails (same-SHA twin of pjm-90-cchp-srmc, 2026-07-08)

Same-SHA statistical-mode twin `2026-07-08-pjm-91-statmode`
(`results/calibration/pjm90_statmode`) of the current keeper
`2026-07-08-pjm-90-cchp-srmc`, HEAD `fab2254`. Both `NOT-YET`. This is the
**first re-solve of any kind since the original 2026-07-03 pjm-76 probe** —
pjm-77/pjm-83/pjm-90 were never re-gated.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | **FAIL** | **FAIL** | COAL_BIT balloons: 2023 112→**213 TWh** (PASS→FAIL), 2024 111→**210 TWh** (PASS→FAIL) |
| C2 sysvol | PASS | **FAIL** | 2025 coal +61.5% |
| C3a mean LMP | CAVEAT | **FAIL** | 2023 +6.3%→**−12.6%**, 2024 −2.2%→**−17.9%**, 2025 −8.5%→**−22.4%** |
| C3b price shape | CAVEAT | **FAIL** | NRMSE worsens each yr: 2023 0.193→0.214, 2024 0.142→0.242, 2025 0.164→0.280 |
| C3c price tail | **FAIL** | **FAIL** | already failing (few modeled scarcity hours) |
| C4 dispatch corr | PASS | **FAIL** | coal r collapses: 2023 0.930→0.797, 2024 0.945→0.799, 2025 0.937→0.831 |
| C5a CO2 | PASS | **FAIL** | jumps ~1% → **+22–26%** all 3 yrs |
| C5b storage | SKIPPED | SKIPPED | |
| C5c storage shape | SKIPPED | SKIPPED | |
| C7 diurnal shape (D-1) | PASS | PASS | ST_GAS immaterial (<2% ISO load) both sides |
| C8 forced-energy share (D-2) | PASS | **FAIL** | flips to FAIL with overlays off |

**Verdict:** the largest same-SHA swing of the four (+6). PJM's coal/gas split
is substantially historic-outage-overlay-carried — COAL_BIT balloons ~+100 TWh
and CO2 jumps ~25 points the moment statistical outages replace measured ones,
the coal-over-run signature the 2026-06-16 ERCOT D1/D2 ablation flagged as the
dominant, largely-defensible outage lever, now confirmed on the largest coal
fleet. Dispatch correlation and the price level both fall out of tolerance.

## NYISO — 0 → 4 fails (all from caveat→fail)

> **STALE vs the 2026-07-06 keeper swap (G-10 truth-in-labeling).** This
> section was scored against `2026-07-03-nyiso-41-hub-prices`
> (`results/calibration/nyiso41_hubprices`); the NYISO keeper is now
> `2026-07-07-nyiso-56-measured-zonal`. **The C1–C5c numbers in the table below
> are NOT valid for the current keeper.** NYISO is **out of scope** for the
> 2026-07-08 same-SHA re-gate (owner directive); no same-SHA twin has been run
> against the current keeper. Per the program rule this section is flagged
> stale, not silently carried; it also still reflects the original 9-criterion
> (C1–C5c) scoring. Re-running is a separate authorized solve session
> (`scripts/archive/run_statmode_probe.py` against the current NYISO keeper bundle) —
> see the re-solve queue note at the end of this document.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | PASS | **FAIL** | CC_REGULAR/ST_GAS both flip: 2023 CC_REGULAR +0.81(PASS)→**−6.37 TWh**; ST_GAS −0.82(PASS)→**+8.80 TWh** |
| C2 sysvol | PASS | PASS | unchanged |
| C3a mean LMP | CAVEAT | **FAIL** | −13.3%→−29.9%, −13.4%→−28.2%, −9.5%→−31.5% |
| C3b price shape | CAVEAT | **FAIL** | |
| C3c price tail | CAVEAT | **FAIL** | 2025 model 7h→2h vs actual 42h |
| C4 dispatch corr | PASS | PASS | unchanged |
| C5a CO2 | CAVEAT | PASS | **improves**: 2024 −7.1%→−2.2% |
| C5b/c storage | SKIPPED/SKIPPED | SKIPPED/SKIPPED | |

**Verdict:** NYISO's keeper determination was already `NOT-YET` purely on
caveat budget (0 hard fails, 4 soft caveats vs. a 2-caveat soft budget) — it
looked closest to clean of the six. Statistical mode shows that was
borderline: every one of those caveats was a near-miss the overlays were
narrowing, and three of four convert cleanly to FAIL with overlays off. CO2 is
the one exception and actually improves.

## NEISO — 1 → 6 fails

> **STALE vs THREE unflagged keeper swaps (G-10 truth-in-labeling).** This
> section was scored against `2026-07-01-neiso-43-closeout`
> (`results/calibration/neiso_closeout`); the NEISO keeper is now
> `2026-07-08-neiso-54-steamgas-ct` (several swaps since this section was
> written). **The C1–C5c numbers in the table below are NOT valid for the
> current keeper.** NEISO is **out of scope** for the 2026-07-08 same-SHA
> re-gate (owner directive); no same-SHA twin has been run against the current
> keeper. Per the program rule this section is flagged stale, not silently
> carried; it also still reflects the original 9-criterion (C1–C5c) scoring,
> not the C7/C8 protective-tier criteria added 2026-07-04, nor the rubric v2
> tier/budget re-anchor (`docs/calibration-determination-rubric.md` §9,
> 2026-07-06). **Separate disclosure (D-2 bucket mis-attribution):** the
> neiso-49 floor's D-2 forced-energy row was found (PR #1498 tranche review,
> `docs/handoffs/wave-manager-tranche-review-2026-07-06.md`) to land in the
> `''` (empty-string) class bucket with a nuclear-inclusive denominator (true
> 2023 share ≈3.7%, still within budget) — a diagnostic-script attribution
> bug, not a calibration defect, but it means any D-2/C8-style forced-energy
> comparison for NEISO drawn from that keeper chain should not be taken at
> face value until the bucket bug is fixed. Re-running the statmode twin is a
> separate authorized solve session against the current NEISO keeper bundle —
> see the re-solve queue note at the end of this document.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | PASS | PASS | unchanged (all 2025 classes SKIPPED on preliminary vintage; 2023/24 not shown = clean both sides) |
| C2 sysvol | CAVEAT | **FAIL** | 2025 gas +2.8%→+3.2% |
| C3a mean LMP | PASS | **FAIL** | −3.0%→−17.7%, −1.0%→−12.5%, +3.6%→−7.2% |
| C3b price shape | FAIL | FAIL | already failing |
| C3c price tail | CAVEAT | **FAIL** | all 3 years, still 0 modeled scarcity hours |
| C4 dispatch corr | PASS | PASS | unchanged |
| C5a CO2 | PASS | PASS | unchanged |
| C5b storage | CAVEAT | **FAIL** | |
| C5c storage shape | CAVEAT | **FAIL** | |

**Verdict:** NEISO's fuel-mix and dispatch-correlation hold up structurally
(both stay PASS), but price level, price tail, and storage all move from
caveat to fail — the historic-outage/coal-pricing overlays are propping up
price-level and storage-dispatch fit specifically, not the underlying
generation mix.

## MISO — 4 → 11 fails (fails everything scored) — same-SHA twin of miso-47-steamgas-ct, 2026-07-08

Same-SHA statistical-mode twin `2026-07-08-miso47-statmode`
(`results/calibration/MISO/miso47_statmode`) of the current keeper
`2026-07-08-miso-47-steamgas-ct`, HEAD `fab2254`. Both `NOT-YET`. This is the
**first re-solve of any kind since the original 2026-07-03 miso-39 probe** —
miso-41/miso-44/miso-47 were never re-gated.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | **FAIL** | **FAIL** | COAL_PRB over-runs: 2023 123→**174 TWh**, 2024 114→**160 TWh** (PASS→FAIL) |
| C2 sysvol | **FAIL** | **FAIL** | 2025 coal +16.2%→**+61.0%**; COAL_BIT also breaks band |
| C3a mean LMP | **FAIL** | **FAIL** | ~doubles: 2023 −0.4%→**−21.0%**, 2024 −5.0%→**−22.6%**, 2025 −11.0%→**−29.0%** |
| C3b price shape | CAVEAT | **FAIL** | NRMSE ~triples: 2023 0.082→0.231, 2024 0.100→0.245, 2025 0.160→0.315 |
| C3c price tail | **FAIL** | **FAIL** | 0 modeled scarcity hours both sides |
| C4 dispatch corr | PASS | **FAIL** | coal NRMSE ~triples (r roughly holds ~0.9); 2025 coal r 0.89→0.78 |
| C5a CO2 | PASS | **FAIL** | −2%→**+15–22%** all 3 yrs (was within ±5%) |
| C5b storage | CAVEAT | **FAIL** | |
| C5c storage shape | CAVEAT | **FAIL** | 2025 discharge r 0.478→0.341 |
| C7 diurnal shape (D-1) | PASS | **FAIL** | off-peak CV ratio collapses: 2025 2.614→**0.371** (profile r still ~0.94) |
| C8 forced-energy share (D-2) | PASS | **FAIL** | flips to FAIL with overlays off |

**Verdict:** MISO fails **every** scored criterion once overlays are off (4→11)
— the starkest confirmation of D-7's premise on this ISO. The
historic-outage/coal-pricing overlays were the last thing keeping coal volume,
CO2, dispatch shape, and — new under the v2.2 rubric — the C7 diurnal shape
inside any tolerance at all. None of MISO's in-sample fit currently generalizes
as a forecast-machinery prior.

---

## Re-solve queue (G-10 follow-on)

The 2026-07-08 session re-gated the four in-scope ISOs (ERCOT, CAISO, PJM,
MISO) to same-SHA twins of their current keepers — those rows are now **DONE**.
NYISO and NEISO are out of scope this pass (owner directive) and remain queued.

| ISO | current keeper (bundle) | latest registered statmode twin | status |
|---|---|---|---|
| ERCOT | `2026-07-08-ercot46-clock-steamgas` (`ercot46_clock_steamgas`) | `2026-07-08-ercot46-statmode` (`ercot46_statmode`) | **DONE — same-SHA @ fab2254** (fail 2→7) |
| CAISO | `2026-07-07-caiso65-seam-envelope-clock` (`caiso65_seam_envelope_clock`) | `2026-07-08-caiso65-statmode` (`caiso65_statmode`) | **DONE — same-SHA @ fab2254** (fail 6→8; retires r2/v2 caiso51 confound) |
| PJM | `2026-07-08-pjm-90-cchp-srmc` (`pjm90_cchp_srmc`) | `2026-07-08-pjm-91-statmode` (`pjm90_statmode`) | **DONE — same-SHA @ fab2254** (fail 2→8; first re-solve since pjm-76) |
| MISO | `2026-07-08-miso-47-steamgas-ct` (`MISO/miso_47_steamgas_ct_drag`) | `2026-07-08-miso47-statmode` (`MISO/miso47_statmode`) | **DONE — same-SHA @ fab2254** (fail 4→11; first re-solve since miso-39) |
| NYISO | `2026-07-07-nyiso-56-measured-zonal` | `2026-07-05-nyiso-statmode-d7-r2` (`nyiso41_hubprices`) | **OUT OF SCOPE (queued)** — r2-confounded, replays superseded nyiso41; needs a same-SHA replay of the current keeper |
| NEISO | `2026-07-08-neiso-54-steamgas-ct` | `2026-07-05-neiso-statmode-d7-r2` (`neiso_ctscrub`, neiso-48 basis) | **OUT OF SCOPE (queued)** — r2-confounded, two-plus keepers behind; needs a same-SHA replay of the current keeper |

---

## Cross-ISO synthesis

1. **The overlay-carried-skill gap is real and large on a same-SHA basis at
   all four in-scope ISOs** — fail count +2 to +7. At CAISO and MISO the keeper
   already fails much of the rubric in-sample, but the *magnitudes* still
   worsen sharply on fuel-mix, CO2 and dispatch shape (MISO now fails all 11).
2. **CAISO is the one ISO where price level improves out-of-sample** — every
   other ISO's mean-LMP miss roughly doubles or flips negative with overlays
   off, but CAISO's C3a/C3b get closer to actual. The overlays there carry the
   volume/CO2 side, not the price level. Worth a closer look in a future
   session.
3. **CAVEAT vanishes under statistical mode** at every in-scope ISO (ERCOT
   3→0, CAISO 1→0, PJM 2→0, MISO 3→0) — the soft-caveat band was mostly
   absorbing overlay-narrowed near-misses, not genuine model-structure
   tolerance.
4. **The coal-over-run signature dominates the outage-overlay delta** wherever
   there is a large coal fleet (PJM COAL_BIT +100 TWh, MISO COAL_PRB +50 TWh,
   ERCOT COAL_PRB), each with a matching CO2 jump — the same finding the
   2026-06-16 ERCOT D1/D2 ablation flagged as the dominant, largely-defensible
   lever, now confirmed on the two largest coal fleets.
5. **No tuning was done in response to any of the above** (CLAUDE.md #1). These
   are probes; the keepers stand unchanged.

## Caveats / scope limits

- **The four in-scope ISOs are now same-SHA and current-rubric; NYISO/NEISO are
  not.** ERCOT/CAISO/PJM/MISO are 2026-07-08 same-SHA (`fab2254`) twins of the
  current keeper scored on the v2.2 11-criterion rubric. NYISO/NEISO are the
  superseded 2026-07-03 run against since-swapped keepers on the old 9-criterion
  (C1–C5c) scoring — kept flagged-stale, out of scope this pass, and not
  comparable on the same denominator.
- **C6 governance is not scored for probes.** Every statmode bundle reads
  `UNATTESTED` (no `calibration_attestation.json`) by construction — probes
  don't carry a governance attestation. Excluded from all fail counts above; it
  is not a new finding.
- **D-9 quarantine assertions hold in both directions.** `ct_deployment_overlay`
  and `reliability_deployment_overlay` were already `False` in all keepers, so
  statistical mode's forcing them off is a no-op for those two flags; the flags
  that actually move are `outage_source`, `wefor_residual(_groups)`, and
  `coal_plant_monthly_pricing`.
- **This is D-7 only.** D-6 (2022/H1-2026 holdout scoring) and D-8 (coefficient
  stability) from the S4 prompt pack are not run in this session.
- **Shared "actual" bench data stays pinned to the keeper's basis.** For each
  of the four re-gated ISOs, registering the same-SHA probe
  (`scripts/dashboard_add_run.py`) left the committed
  `frontend/data/backcast/bench/<ISO>/*` parts byte-identical (the keeper's
  bench already covers 2023–2025), so keeper and probe are scored against the
  identical actual/bench basis — only the model side varies, as the method
  requires. (The BTM-under-statistical-mode drift noted in the original
  2026-07-03/04 ERCOT registration did not recur for these four bundles.)

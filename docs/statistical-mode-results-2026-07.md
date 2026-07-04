# D-7 statistical-mode A/B — all six ISOs (2026-07-03)

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
skill prior from the backcast-only measured overlays. This is the same
methodology as the 2026-06-16 ERCOT-only run, extended to all six current
keepers and re-scored against the *current* rubric
(`scripts/calibration_verdict.py`, `docs/calibration-determination-rubric.md`),
which is materially stricter/different from the older "0.33% universal gate"
the prior report used (see Caveats).

**Method.** Each probe is a byte-faithful replay of the keeper's own
`meta.json` (`scripts/run_statmode_probe.py`, built on the existing
`replay_keeper.py` kwarg-mapping) with only the statistical-mode delta
applied — no other flag changed. One invocation per ISO, all of that ISO's
keeper years solved sequentially within it:

| ISO | Keeper bundle (flags source) | Years | Statmode bundle | Dashboard run id |
|---|---|---|---|---|
| ERCOT | `results/calibration/ercot_ordc_total_rtolcap_v1` (ercot32-ordc-total-rtolcap) | 2023–2025 | `results/calibration/ercot32_statmode_2026-07` | `2026-07-04-statmode-d7-probe-ercot32` |
| CAISO | `results/calibration/caiso51_firm_base` (caiso-51-firm-base) | 2023–2025 | `results/calibration/caiso_statmode_2026-07` | `2026-07-03-caiso-statmode-d-7` |
| PJM | `results/calibration/pjm76_outage_fix` (pjm-76-outage-fix) | 2023–2025 | `results/calibration/pjm_statmode_2026-07` | `2026-07-03-pjm-statmode-d-7` |
| NYISO | `results/calibration/nyiso41_hubprices` (nyiso-41-hub-prices) | 2023–2025 | `results/calibration/nyiso_statmode_2026-07` | `2026-07-03-nyiso-statmode-d-7` |
| NEISO | `results/calibration/neiso_closeout` (neiso-43-closeout) | 2023–2025 | `results/calibration/neiso_statmode_2026-07` | `2026-07-03-neiso-statmode-d-7` |
| MISO | `results/calibration/MISO/miso_39_reserve_pergen` (miso-39-reserve-pergen) | 2023–2025 | `results/calibration/miso_statmode_2026-07` | `2026-07-03-miso-statmode-d-7` |

All six are registered on the dashboard as **probes**, next to their keeper,
per CLAUDE.md #15. **No offer curve, sigmoid, or floor was tuned in response
to any result below** (CLAUDE.md #1) — this session is measurement only.

**2026-07-04 update — ERCOT re-gated to the current keeper.** The ERCOT leg
above was originally run against `ercot_gtc_limits_v1` (ercot26-gtc-limits),
which the ERCOT keeper has since superseded twice over (ercot27 → … →
ercot32-ordc-total-rtolcap, `frontend/data/backcast/keepers.json`). This
session re-ran the ERCOT leg **only**, byte-faithful against the current
`ercot_ordc_total_rtolcap_v1` keeper bundle, same method
(`scripts/run_statmode_probe.py`), same solo/sequential year discipline. The
ERCOT section and cross-ISO summary row below are now on the ercot32 basis;
the CAISO/PJM/NYISO/NEISO/MISO sections are untouched from 2026-07-03. The
rubric also gained two HARD criteria since the original run — **C7 diurnal
shape (D-1)** and **C8 forced-energy share (D-2)**, added 2026-07-04 — so
ERCOT below is scored C1–C8 (11 scored criteria, C6 governance still
excluded per the probe-is-unattested rule); the other five ISOs' rows still
reflect the original 9-criterion (C1–C5c) scoring from 2026-07-03 and have
not been re-scored under the extended rubric. See the superseded note at the
end of the ERCOT section for the original ercot26-basis numbers.

**Environment note (not a config change).** This box has 15 GB RAM / 4 cores.
Three solves run concurrently (ERCOT + 2 per-plant-multi-zone ISOs, per rule
#12's "cap ~2") OOM-killed both ERCOT and PJM; the queue was switched to
strict-sequential (one solve at a time) for the rest. MISO's keeper uses
per-generator reserve co-optimization (`miso_reserve_pergen`: 3,151 units
pooled into 30 zone×fuel-class columns) which alone peaked past 15 GB anon-RSS
and was OOM-killed running **solo** — a 12 GB swap file (removed after) let it
complete unmodified. No calibration flag was changed to work around this.
The 2026-07-04 ERCOT re-gate ran solo (no concurrent solves) on the same
15 GB box per this session's instructions and completed cleanly, ~4-5 min/
year (cold + warm solve), peak ~6.2 GB anon-RSS — no swap needed.

---

## Cross-ISO summary

Criterion-status mix across the scored criteria (**C6 governance excluded** —
every probe bundle is intentionally unattested, since it isn't a keeper, so
C6 reads UNATTESTED by construction and is not a comparable signal). **ERCOT
is scored on 11 criteria (C1–C5c + C7 + C8, current ercot32 keeper basis,
2026-07-04); CAISO/PJM/NYISO/NEISO/MISO are still on the original 9-criterion
(C1–C5c) scoring from 2026-07-03** — the row counts are not on the same
denominator, see the caveats below:

| ISO | keeper PASS/CAVEAT/FAIL/SKIP | statmode PASS/CAVEAT/FAIL/SKIP | fail count Δ |
|---|---|---|---|
| ERCOT † | 3 / 3 / **4** / 1 | 3 / 0 / **7** / 1 | **4 → 7** (+3, of 11 scored) |
| CAISO | 0 / 0 / **7** / 2 | 0 / 0 / **7** / 2 | **7 → 7** (+0; magnitudes shift, see below) |
| PJM | 2 / 0 / **5** / 2 | 0 / 0 / **7** / 2 | **5 → 7** (+2) |
| NYISO | 3 / 4 / **0** / 2 | 3 / 0 / **4** / 2 | **0 → 4** (+4; all from caveat→fail) |
| NEISO | 4 / 4 / **1** / 0 | 3 / 0 / **6** / 0 | **1 → 6** (+5) |
| MISO | 2 / 0 / **7** / 0 | 0 / 0 / **9** / 0 | **7 → 9** (+2; fails everything scored) |

† ERCOT counts are the 2026-07-04 ercot32-basis, 11-criterion re-score (adds
C7 diurnal shape, C8 forced-energy share). The original 2026-07-03
ercot26-basis, 9-criterion count was **2 → 6** (+4, 3×) — see the superseded
note in the ERCOT section. The two are not directly comparable (different
keeper, different criterion count); both replicate the same qualitative
finding (overlay-carried price/fuel-mix skill, CT_PEAKER forced-share
collapse).

**The gap is real and, except at CAISO/MISO (already failing almost
everything in-sample), large** — consistent with the one prior ERCOT
data point (2026-06-16: 5→10 under the older rubric). A second pattern,
visible only because this run scores CAVEAT separately from FAIL: **every
ISO's CAVEAT count collapses to ~0 in statistical mode.** The overlays are not
just closing hard misses, they are what turns a hard miss into a
tolerable-looking near-miss — remove them and the near-misses become clean
fails rather than new categories of error.

---

## ERCOT — 4 → 7 fails (ercot32-ordc-total-rtolcap basis, 2026-07-04)

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | CAVEAT | **FAIL** | 2024 CC_REGULAR +14.72 TWh/+3.1pp (was PASS −3.33 TWh); 2024 ST_GAS −9.42 TWh/−2.0pp (was PASS −1.77 TWh); 2025 COAL_PRB +10.19 TWh/+2.1pp (was PASS +0.16 TWh) |
| C2 sysvol | CAVEAT | **FAIL** | 2025 gas −10.7% (was CAVEAT −3.0%) |
| C3a mean LMP | FAIL | FAIL | already failing on 2/3 years; magnitudes worsen sharply: 2023 −5.4%→**−50.0%**, 2024 +9.1%→**−14.8%**; 2025 (the one PASS year) +3.6%→**−12.7%** (flips to FAIL) |
| C3b price shape | FAIL | FAIL | unchanged (already failing); NRMSE roughly doubles or more each year (2023 0.393→**0.962**, 2024 0.234→0.302, 2025 0.087→0.175) |
| C3c price tail | FAIL | FAIL | already failing 2/3 years; 2023 model 77h→**16h** vs actual 181h (gets worse); 2024 stays PASS both sides (72h→64h vs actual 53h); 2025 model 10h→5h vs actual 31h (already failing, gets worse) |
| C4 dispatch corr | PASS | PASS | unchanged; coal r softens slightly (2025 0.801→0.760) but stays well above the 0.7 gate |
| C5a CO2 | PASS | PASS | unchanged (2025 flips sign −0.9%→+2.4% but stays in tolerance) |
| C5b storage | SKIPPED | SKIPPED | no EIA-930 storage breakout, both sides |
| C5c storage shape | CAVEAT | **FAIL** | 2024 monthly discharge r 0.331→**−0.069** |
| C7 diurnal shape (D-1) | PASS | PASS | unchanged — CT_PEAKER/ST_GAS hour-of-day profile r stays ≥0.94 both sides; the class-volume band still can't see this because the *level* miss below is a volume/floor problem, not a shape one |
| C8 forced-energy share (D-2) | **FAIL** | **FAIL** | 2023 CT_PEAKER jumps from 11.1% forced (already the fail) to **33.3%** forced (0.90 of 2.72 TWh); 2024 1.0%→7.3% and 2025 1.0%→9.2% both worsen sharply but stay under the 10% peaker gate |

**CT_PEAKER's forced-floor share nearly triples in the fail year and the
class-volume band still doesn't catch the underlying shape problem** — C7
(diurnal shape) passes on both sides because the *hour-of-day profile*
tracks CAMPD fine; it's the *volume* dispatched at a binding reliability
floor (C8) that blows out from 11% to 33% once the historic-outage overlay
stops padding CT_PEAKER's economic dispatch. This is the same
annual-volume-hides-a-class-collapse finding as the original ercot26 run,
now directly visible through C8 rather than inferred from the band being too
wide — the rubric extension (C7/C8, merged 2026-07-04) closes exactly the
gap the original ERCOT statmode report flagged as open S1/S5 follow-on work.

**Verdict:** the finding replicates on the current (ercot32) keeper and the
extended rubric — ERCOT's mean-LMP miss (C3a), already failing 2 of 3 years
in-sample, roughly triples in magnitude with overlays off and the one
passing year (2025) flips to FAIL; CT_PEAKER's forced-energy share (C8)
nearly triples into a starker breach of its own 10% gate. The
historic-outage overlay is still doing the heaviest lifting on both price
level and CT_PEAKER dispatch (consistent with the prior D2 ablation showing
it as the dominant, largely-defensible lever).

<details>
<summary><strong>Superseded — 2026-07-03 ercot26-gtc-limits basis (pre-C7/C8, 9 criteria)</strong></summary>

This is the original ERCOT D-7 result from the same session that produced
the CAISO/PJM/NYISO/NEISO/MISO sections below. It was run against
`ercot_gtc_limits_v1` (ercot26-gtc-limits), which the ERCOT keeper has since
superseded (→ ercot27 → … → ercot32-ordc-total-rtolcap). Kept for the record
only — **do not cite this as current**; use the ercot32-basis table above.

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | CAVEAT | **FAIL** | 2024 CC_REGULAR +10.80 TWh/+2.3pp (was PASS −3.14 TWh); 2024 ST_GAS −9.50 TWh/−2.1pp (was PASS −1.80 TWh) |
| C2 sysvol | CAVEAT | **FAIL** | 2025 gas −8.4% (was CAVEAT −2.8%) |
| C3a mean LMP | PASS | **FAIL** | all three years flip: 2023 −1.7%→**−49.3%**, 2024 +4.7%→**−16.7%**, 2025 +2.1%→**−12.0%** |
| C3b price shape | FAIL | FAIL | unchanged (already failing) |
| C3c price tail | FAIL | FAIL | 2023 model 92h→19h vs actual 181h (already failing, gets worse) |
| C4 dispatch corr | PASS | PASS | unchanged |
| C5a CO2 | PASS | PASS | unchanged |
| C5b storage | SKIPPED | SKIPPED | no EIA-930 storage breakout, both sides |
| C5c storage shape | CAVEAT | **FAIL** | |

**CT_PEAKER volume miss widens sharply but the class band doesn't catch it**:
2023 −0.64 TWh → **−4.40 TWh**, 2024 +0.04 TWh → **−6.27 TWh** (both still
PASS — the per-class band, loosened 2026-07-02 to `min(2% load, 8 TWh)`, is
wide enough on ERCOT's ~500 TWh system to absorb a >6× growth in the CT miss).
This reproduces the D3 finding from the 2026-06-16 report almost exactly:
**annual-volume scoring hides a real class-level collapse.** The live rubric
does not yet carry the D-1 diurnal-shape criterion from the audit's §7 suite
(that is S1/S5 follow-on work, not done in this session), so the CT_PEAKER
shape failure that the AS/RUC-deployment floor is covering for stays
invisible at the family/class-volume granularity scored here.

**Verdict (superseded):** the 2026-06-16 finding replicates on the
then-current keeper and rubric — ERCOT's headline mean-LMP pass (C3a, PASS
on all 3 years) is entirely overlay-carried, flipping to a 12–49% miss with
overlays off; the historic-outage overlay is still doing the heaviest
lifting (consistent with the prior D2 ablation showing it as the dominant,
largely-defensible lever).

</details>

## CAISO — 7 → 7 fails (flat count, mixed magnitudes)

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | FAIL | FAIL | CC_REGULAR over-run widens: 2023 +4.91→**+6.50** TWh, 2024 +10.86→**+12.69** TWh |
| C2 sysvol | FAIL | FAIL | 2025 gas +8.1%→**+16.7%** |
| C3a mean LMP | FAIL | FAIL | **improves** on all 3 years: +19.6%→+14.7%, +34.9%→+29.2%, +41.6%→+31.5% |
| C3b price shape | FAIL | FAIL | NRMSE improves slightly each year |
| C3c price tail | FAIL | FAIL | 2023 scarcity hours flip from under- to over-count: model 0h→**107h** vs actual 21h |
| C4 dispatch corr | FAIL | FAIL | gas r worsens: 2024 0.771→0.728, 2025 0.546→0.436 |
| C5a CO2 | FAIL | FAIL | worsens: 2024 +8.5%→+13.0%, 2025 +8.7%→+17.0% |
| C5b/c storage | SKIPPED/SKIPPED | SKIPPED/SKIPPED | no EIA-930 breakout |

**Verdict:** CAISO's keeper is already failing 7 of 9 scored criteria
in-sample, so there is no headroom for the count to move — but the mix is
genuinely double-edged: overlays off makes fuel-mix, system volume, CO2 and
dispatch correlation *worse* (as expected — the outage/coal-pricing overlays
were absorbing real dispatch error), while it makes the **mean price level
better**, and materially worsens the price tail (over-shoots scarcity hours in
2023 instead of missing them). CAISO is the one ISO where "the overlays are
purely propping up the price level" is *false* — price gets closer to actual
without them; the overlays are instead carrying the volume/CO2/dispatch-shape
side of the fit.

## PJM — 5 → 7 fails

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | FAIL | FAIL | already large misses balloon: 2023 CC_REGULAR −19.71→**−78.54 TWh**; COAL_BIT +1.43(PASS)→**+99.13 TWh**; CT_PEAKER +1.04(PASS)→**−14.32 TWh** |
| C2 sysvol | FAIL | FAIL | 2025 coal +4.0%→**+59.2%**; gas +2.9%→−12.7% |
| C3a mean LMP | mixed (2023 PASS) | FAIL | 2023 +0.3%→**−14.2%**; 2024/25 misses roughly double |
| C3b price shape | FAIL | FAIL | already failing |
| C3c price tail | FAIL | FAIL | unchanged (already 0 scarcity hours modeled all 3 years) |
| C4 dispatch corr | PASS | **FAIL** | coal r collapses: 2023 0.893→0.735, 2024 0.868→0.716, 2025 0.913→0.846 |
| C5a CO2 | PASS | **FAIL** | jumps from ~1–5% to **+22.6–26.6%** all 3 years |
| C5b/c storage | SKIPPED/SKIPPED | SKIPPED/SKIPPED | |

**Verdict:** the pjm-76 keeper's coal/gas fuel split is substantially overlay
(historic-outage) carried — coal balloons +99 TWh and CO2 jumps ~25 points the
moment statistical outages replace measured ones, which is the coal-over-run
signature the 2026-06-16 ERCOT D1/D2 ablation already flagged as the dominant,
largely-defensible outage-overlay lever, now confirmed on a second, much
larger coal fleet.

## NYISO — 0 → 4 fails (all from caveat→fail)

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

## MISO — 7 → 9 fails (fails everything scored)

| criterion | keeper | statmode | note |
|---|---|---|---|
| C1 fuel-mix | FAIL | FAIL | 2023 CC_REGULAR +45.20→**+19.76 TWh** (improves but still fails); COAL_BIT/COAL_PRB flip from PASS to **+30–36 TWh** fails both years |
| C2 sysvol | FAIL | FAIL | 2025 coal +10.4%→**+54.7%**; gas −1.8%(PASS)→**−33.5%** |
| C3a mean LMP | FAIL | FAIL | roughly doubles: −8.5%→−25.9%, −13.6%→−29.6%, −16.9%→−35.2% |
| C3b price shape | FAIL | FAIL | already failing |
| C3c price tail | FAIL | FAIL | unchanged (0 modeled scarcity hours all 3 years, both sides) |
| C4 dispatch corr | PASS | **FAIL** | coal r roughly holds (0.90 both) but NRMSE ~doubles; gas 2025 r 0.894→0.911 (PASS) but NRMSE 0.146→0.361 → **FAIL** |
| C5a CO2 | PASS | **FAIL** | +15.0%/+10.5%/+21.6% (was within ±4%) |
| C5b storage | FAIL | FAIL | already failing |
| C5c storage shape | FAIL | FAIL | already failing |

**Verdict:** MISO fails every scored criterion once overlays are off — the
keeper was already the worst in-sample of the six (7/9), and the
historic-outage/coal-pricing overlays were the last thing keeping coal
volume, CO2, and dispatch shape inside any tolerance at all. This is the
starkest confirmation of D-7's premise on this ISO: none of MISO's
in-sample fit currently generalizes as a forecast-machinery prior.

---

## Cross-ISO synthesis

1. **The overlay-carried-skill gap is real everywhere it can be measured**,
   and at ERCOT/PJM/NYISO/NEISO it is large (fail count +2 to +5, or
   0→4/1→6-scale swings). At CAISO and MISO the keeper is already failing
   almost every criterion in-sample, so the *count* doesn't move much, but
   the *magnitudes* still worsen sharply on fuel-mix, CO2, and dispatch shape.
2. **CAISO is the one ISO where price level improves out-of-sample** — every
   other ISO's mean-LMP miss roughly doubles or worse with overlays off.
   Worth a closer look in a future session (is CAISO's historic outage
   overlay pushing dispatch cost, and therefore price, in the wrong
   direction on average, even though it improves fuel-mix/CO2/shape?).
3. **CAVEAT nearly vanishes under statistical mode** (NYISO 4→0, NEISO 4→0,
   ERCOT 3→0) — the soft-caveat band was mostly absorbing overlay-narrowed
   near-misses, not genuine model-structure tolerance.
4. **The current C1 volume+share band is wide enough to hide a real
   class-level collapse** (ERCOT CT_PEAKER, still PASS despite its
   grid-delivered miss growing >6× with overlays off) — this is the same gap
   the audit's D-1 diurnal-shape diagnostic (§7) is designed to close, and it
   has not yet been wired into the live rubric (S1/S5 follow-on work).
5. **No tuning was done in response to any of the above** (CLAUDE.md #1)."
   These are probes; the keepers stand unchanged.

## Caveats / scope limits

- **Rubric drift vs. the prior report.** The 2026-06-16 ERCOT-only run scored
  against an older "0.33% universal gate" + a separate shape/CO2 scorer
  (`score_backcast_shape_emissions.py`); this run scores against the current
  `calibration_verdict.py` rubric (tighter C1 share band, C3/C4/C5 criteria
  folded in, exceptions-ledger-aware). The two fail counts are not on the same
  scale — ERCOT's 2→6 here is not directly the same "5→10" as before, though
  the qualitative finding (CT collapse, price-level flip, overlay-carried
  skill) replicates.
- **C6 governance is not scored for probes.** Every statmode bundle reads
  `UNATTESTED` (no `calibration_attestation.json`) by construction — probes
  don't carry a governance attestation. This is excluded from all fail counts
  above; it is not a new finding.
- **D-9 quarantine assertions hold in both directions.** `ct_deployment_overlay`
  and `reliability_deployment_overlay` were already `False` in all six keepers
  (per the D-9 gate), so statistical mode's forcing them off is a no-op for
  those two flags everywhere except by definition; the flags that actually
  move are `outage_source`, `wefor_residual(_groups)`, and
  `coal_plant_monthly_pricing`.
- **This is D-7 only.** D-6 (2022/H1-2026 holdout scoring) and D-8
  (coefficient stability) from the S4 prompt pack are not run in this
  session.
- **ERCOT rubric vintage differs from the other five ISOs (2026-07-04
  update).** ERCOT above is scored C1–C8 (adds C7 diurnal shape / D-1 and C8
  forced-energy share / D-2, merged into `calibration_verdict.py` and
  `docs/calibration-determination-rubric.md` on 2026-07-04, after the
  original 2026-07-03 session that produced this document). CAISO, PJM,
  NYISO, NEISO, and MISO below are **not** re-scored under the extended
  rubric — their tables still reflect the original 9-criterion (C1–C5c)
  scoring. Re-running those five under C1–C8 is out of scope for this
  update (ERCOT-only re-gate).
- **ERCOT keeper basis changed mid-series.** The ERCOT numbers above are
  against `ercot_ordc_total_rtolcap_v1` (ercot32-ordc-total-rtolcap, the
  keeper as of 2026-07-04); the original run used `ercot_gtc_limits_v1`
  (ercot26-gtc-limits, superseded). The dashboard probe registration was
  replaced in place (`2026-07-03-statmode-d-7-probe` →
  `2026-07-04-statmode-d7-probe-ercot32`) rather than kept alongside it, to
  avoid a stale-keeper probe sitting on the Run Explorer next to the
  current keeper.
- **Shared "actual" bench data must stay pinned to the keeper's basis.**
  Registering the ercot32-basis probe (`scripts/dashboard_add_run.py`)
  initially rewrote the committed `frontend/data/backcast/bench/ERCOT/*`
  parts, because the probe's own `btm.parquet` (behind-the-meter CHP host
  steam held out of the LP) came out ~3.4 TWh different on CC_CHP and ~1.9
  TWh different on CT_CHP from whatever last supplied those parts — i.e.
  the held-out CHP plants' grid dispatch is *not* solve-invariant under
  statistical mode the way `replay_keeper.py`'s docstring assumes it is for
  a byte-faithful replay. Left alone, that would have silently moved the
  "actual" denominator both the keeper's and the probe's C1/C2 scores are
  measured against. The bench parts, `manifest.js`, and `benchmark.js` were
  reverted to their pre-registration (keeper-supplied) state before scoring
  above, so keeper and probe are scored against the identical actual/bench
  basis — only the model side varies, as the method requires. This
  BTM-under-statistical-mode drift is itself a small legitimacy finding
  (not investigated further here, per "measurement only") worth a follow-up
  look at why held-out CHP dispatch moves when the historic-outage overlay
  is forced off.

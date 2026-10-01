# PRECOMMIT — capx lane D17: MISO's missing non-coal economic exit channel

**Lane:** capx D17 (r#22 relaunch, dispatched as D17R), charter
`docs/handoffs/capx-director-prompt-pack-2026-08.md` §D17.
**Session date:** 2026-09-01. **Branch:** `claude/capx-d17r-miso-exit-channel-ngkyxk`.
**Discipline:** PRECOMMIT-FIRST — this document is pushed BEFORE any measurement. Phase 0 is
ZERO-SOLVE (no LP solve, no re-score, no bundle regeneration); every number in the finding
will be read from a committed artifact or computed by evaluating committed code/constants on
committed inputs. Repairs are ROUTED, never built. Relaunch note: the earlier D17 dispatch
landed nothing (verified — no branch matching `miso|d17` on `git ls-remote --heads origin`,
no D17 finding/precommit on main); nothing is salvaged.

## 0. The object (fixed from the committed record before this precommit)

Over the MISO T1-H window (2021–2025, vintage 2020) the economic screen executes ZERO
gas_ct / gas_cc / oil exits — model 0.0 GW against actual 2.435 / 0.521 / 0.502 GW, i.e.
**3.458 GW of real non-coal exits the screen never produces** — while it OVER-retires coal
(+9.1 % post-G3-fix, +18.4 % pre-fix). Source: `FINDING-capx-d3-miso-retire-g3-2026-08-31.md`
§5, whose per-fuel table is read from the committed FFR-2B pipeline-arm score
(`results/hindcast/miso-2021-2025-cmc-pipeline-ffr2b/MISO/0a4455fd0d642364/score.json` —
byte-identical to the post-fix FFR-3A-3 leg). The −16.5 % `retire.total_gw` FAIL is this
missing channel made visible once the G3 cap-grain fix removed the compensating coal excess.

**Standing refusals, restated as binding here:** the G3 fix STAYS; restoring the
decision-year cap grain, or dual-basis reporting to recover the pre-fix PASS, is refused on
its face (rules 1 `[R-STRUCT]` / 14 `[R-ACCURATE]`). And this lane must never become a
per-fuel FOM constant, retirement threshold, execution lag, or margin adder identified from
the retirement residual (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]` — the NEISO-RC R6 refusal,
binding identically). A residual that can only be closed by a tuned value is an open
root-cause issue, not a parameter.

**New context since the charter (context, not evidence):** lane D4-M (PR #4481) measured
ERCOT's economic screen also executing zero retirements over its T1-H window (0.000 vs
2.294 GW actual). Per rule 25 `[R-ISO-SCOPE]` that observation is ERCOT's and fills no MISO
cell; it obligates this lane only to SAY whether its attribution lands on MISO-specific
inputs or shared machinery, and to ROUTE any cross-ISO question rather than answer it.

## 1. Census disclosure (what was sighted before this freeze)

Mechanism code read in full: `src/market_sim/model/capacity_evolution/retirements.py` (the
screen bar, the pipeline rule, `_admission_cap_horizon`, `_apply_reliability_floor` call
sites, the margin construction and its five revenue legs, `capacity_revenue_per_mw_yr`).
Artifact inventory: file listings of `results/hindcast/miso-*`, `results/ff-t1f-s123/`,
`results/ffr1c/`; `meta.json` of the FFR-2B pipeline arm, the cmc-probe bundle, and
`miso-2021-2023-t1ff-armr-ffr3vfix-after` (postures/vintages only); the first ~700 bytes of
`ffr2b-miso-compare.json` (its `i6_cap`/`legs` shape and the LEGACY leg's meta header —
no event rows, no per-fuel values); grep hit-lists locating which committed files contain
`pipeline_events` / `net_revenue_usd`; the header + line count of
`capacity_actuals_miso.csv`; constants-file line hits for the MISO RBDC / capacity-market
registries; the FFR-3F §1.4 open-item paragraph; the MISO matrix shard header (lever queue
empty) — plus the three READ-FIRST findings the charter names. **No pipeline event rows, no
per-unit margin rows, no floor-retention rows, and no score fields beyond those D3 §5
already published have been read.** The candidate threads, evidence plan, adjudication rule
and kills below were fixed before any of that content was opened.

## 2. Candidate threads (frozen ex ante — D3 §6.1's four, none presumed, one sharpened)

- **(i) Margin-side over-crediting** — the attainable pro-forma inframarginal margin for
  MISO gas/oil clears the going-forward bar for every unit in every year, so no non-coal
  unit ever FAILS the screen. Sharpened into its two legs, because the mechanism prices
  them separately and they have different external observables:
  - **(i-a) energy/AS legs** — `Σ_t max(0, price − mc, r) × cap` over-rewards these
    classes (price signal, mc basis, availability), per D3's "whether modeled energy/AS
    margins over-reward these classes against FOM";
  - **(i-b) capacity-revenue leg** — MISO is a capacity-market ISO with clearing armed in
    the T1-H posture (`capacity_market_clearing_by_iso[MISO]=true` in the FFR-2B meta), so
    every thermal unit earns `capacity_price × (1 − EFORd) × pmax`. If the model's
    hindcast-window capacity price materially exceeds what MISO's PRA actually cleared in
    2021–2025 (in-repo record: `data/raw/miso-pra/miso_pra_clearing_prices_2023-2026.csv`,
    `data/raw/capacity-market/auction-price/miso/miso.csv`), that leg alone can hold every
    gas/oil unit above the bar regardless of energy economics.
- **(ii) Per-fuel identification against the EIA-860 record** — the actual 3.458 GW of
  exited units (per-unit rows in `capacity_actuals_miso.csv`) vs the model's screening
  population: are those units in the vintage-2020 fleet at all, at what grain, under which
  model fuel class (the gas_ct/gas_st taxonomy fold matters — an old gas steamer's margin
  structure is nothing like a peaker's), and with what FOM field / execution lag mapped.
  Includes the sub-case where a material share of the actual exits is absent from or
  invisible to the screening population (a screen-population gap, distinct from a margin
  error).
- **(iii) The admission cap's REQUIREMENT side in the hindcast window** — S-123
  established the t1f requirement basis was overstated (PRM 0.179→0.157 re-vintage,
  +3,505.9 MW external ZRC, DR netting f=0.0665940). The FFR-2B/T1-H window ran the
  PRE-S-123 basis. An overstated hindcast requirement inflates post-G3 retention (blocks
  admission / floor-retains executions) the same way; its hindcast-window analogue has
  never been measured.
- **(iv) The cap's fleet side stays at decision year** — FFR-3F §1.4's recorded open item:
  entry commissioning between decision and execution is not credited, biasing the cap
  toward retention.

Threads (iii)/(iv) can only act on units that FAIL the bar (the cap and floor gate
admission/execution of failing units); thread (i) acts before any of that. This ordering is
the primary discriminator in §4.

## 3. Distinguishing evidence (committed artifacts + committed-code evaluation, enumerated ex ante)

- **E1 — the FFR-2B legacy-vs-pipeline comparison record:**
  `results/hindcast/ffr2b-miso-compare.json` + `ffr2b-miso-legacy.json` (both carry
  `pipeline_events`/`entry_capped` content per grep). Extract: per-fuel decision/execution/
  cap/floor event composition for the exact run whose score IS the object.
- **E2 — committed pipeline-rule evolution ledgers in the hindcast window:**
  `results/hindcast/miso-2021-2023-t1ff-armr-ffr3vfix-{before,after}/MISO/d1459d48c4788d7b/
  evolution_*.json` (retirement_rule=pipeline, base 2021, 2021–2023). Posture caveat stated
  now: T1-FF full-forward with entry/exit rate limits and correlated outages armed — used
  for event-composition corroboration, never quoted as the T1-H number.
- **E3 — the object's own score:** the FFR-2B pipeline-arm `score.json` per-fuel retire
  table (already published in D3 §5) + its `meta.json` posture.
- **E4 — legacy-rule corroboration:** `miso-2021-2025-realized-cmc-probe` /
  `-cmc-before` / `-realized` evolution ledgers + `year_*_floor_retentions.json` +
  `ffr2b-miso-legacy.json`: does the LEGACY screen also produce zero non-coal exits? (If
  both rules produce zero, the cause sits in the shared margin construction or its inputs,
  not in the pipeline's decision/execution plumbing.)
- **E5 — the only committed per-unit bar decomposition for MISO:**
  `results/ff-t1f-s123/verify/MISO/587dc5b32ba71ceb/evolution_{2026..2030}.json` — FFR-5A
  `margin_detail` rows (net_revenue / going_forward / energy_margin / reserve_uplift /
  capacity_revenue / as_credit per unit). Forecast window (2026–2030) under post-S-123
  constants — used to characterize WHICH leg of the gas/oil revenue stack dominates in the
  same machinery, with that caveat carried everywhere, never as the hindcast measurement.
- **E6 — the actual exit set:** `data/raw/_validation-source/capacity_actuals_miso.csv`
  (per-unit 2021–2025 retirements, model fuel taxonomy) + `data/raw/eia-860` unit
  characteristics for the exited units (technology, vintage, size); the model-side
  screening population from the committed vintage-2020 fleet path (code + committed raw
  inputs, no solve).
- **E7 — the requirement analogue (thread iii):** evaluate
  `resolve_adequacy_requirement_mw` / `resolve_planning_reserve_margin` (committed code) on
  the PRE-S-123 constants (git history at the FFR-2B era, e.g. `a61b3ec^` per S-123 §6) vs
  post-S-123 HEAD constants, at hindcast-window peaks read from committed artifacts;
  compare both against MISO's own published PY 2021/22–2025/26 requirement record already
  in-repo (`auction-price/miso/miso.csv`, `miso-pra` corpus per its README/SOURCES).
- **E8 — the capacity-price leg (thread i-b):** evaluate the committed
  `capacity_revenue_per_mw_yr` / RBDC-curve constants for MISO hindcast years across the
  reserve-position range the window plausibly spans, vs the in-repo PRA clearing-price
  record (E7's price files). External observable = MISO's own auction record; the
  retirement residual is never the reference.

If a needed quantity exists in no committed artifact and cannot be computed from committed
code + committed inputs without a solve, that gap is REPORTED and the measurement routed.

## 4. Adjudication rule (frozen ex ante)

1. **Primary discriminator — where does the zero happen?** From E1/E2 (+E4), classify the
   non-coal fuels over the window:
   - **(A) No gas_ct/gas_cc/oil unit ever fails the bar** (no decided / re_confirmed /
     entry_capped event, no legacy loss-counter increment) → the zero is **MARGIN-SIDE**:
     thread (i) is PRIMARY; threads (iii)/(iv) are adjudicated **INERT FOR THE ZERO** (they
     gate only units that failed) — they may still be real defects, reported on their own
     evidence, but they do not explain this object. Go to step 2.
   - **(B) Units fail but are entry_capped / floor-retained / deferred** → the zero is
     **REQUIREMENT/CAP-SIDE**: threads (iii)/(iv) are PRIMARY. Go to step 3.
   - **(C) Units decided AND executed in the ledger while the score reads 0.0** → a
     scorer/ledger seam defect (not among the four threads); report as its own class and
     route the measurement-validity repair.
   - Mixed outcomes are attributed per-fuel; the finding names the dominant class per fuel.
2. **Margin-side decomposition (outcome A):** establish which revenue leg holds the stack
   above the bar — (i-b) via E8 (model hindcast capacity price vs MISO's actual PRA
   clearing record: adjudicated OVER-CREDITING iff the model price materially exceeds the
   published record for the same years, stated at full magnitude in $/kW-yr against each
   fuel's FOM bar); (i-a) via E5's leg structure + E6's unit characteristics (does the
   energy pro-forma alone clear the bar for the units that actually exited?). Thread (ii)
   runs regardless: verify the actually-exited units are present, correctly classed, and
   screened (E6); a material screen-population gap is its own attribution class.
3. **Requirement-side quantification (outcome B):** E7's pre/post-S-123 requirement
   analogue at hindcast peaks — quantify the MW of admission-blocking / floor retention
   attributable to the overstated basis; for thread (iv), bound (from committed events and
   ledger entry rows only, no solve) whether entry crediting at the cap horizon could have
   changed admissions.
4. **Verdict vocabulary:** each of (i-a), (i-b), (ii), (iii), (iv) gets one of
   CONFIRMED-PRIMARY / CONTRIBUTING / REFUTED / INERT-FOR-THIS-OBJECT / BLOCKED-ON-EVIDENCE
   against its own kill below. Repairs are routed priced, with rule-13/21 admissibility
   stated per repair (what published/measured input would drive it; what would regenerate
   forward), and NOT built. If the attribution lands on shared (ISO-agnostic) machinery,
   the finding says so explicitly and routes the cross-ISO question to the director —
   this lane adjudicates MISO only (rule 25).

## 5. Kills / stop conditions (frozen ex ante)

- **K1 (evidence floor):** if E1+E2+E4 together cannot support step 1's classification for
  the T1-H window (e.g. the compare record carries only aggregate counts and the ffr3vfix
  posture is too far from T1-H to corroborate), the finding STOPS at "attribution blocked
  on uncommitted evidence", states exactly what artifact a diagnostic T1-H re-run must
  commit (ledger + margin_detail), and routes that run — it is NOT run here.
- **K2 (zero solves):** no LP solve, no re-score, no bundle regeneration, under any
  outcome. Committed-code function evaluation on committed inputs is the ceiling.
- **K3 (no writes beyond the two documents + this lane's own records):** no board write,
  no verdict/gate flip, no keeper/shard/marker touch, no matrix cell (nothing is tested;
  MISO lever queue checked under duty (a) — empty, and this lane adds no lever), no
  backcast-namespace file, no ScenarioConfig field, no constants change.
- **K4 (collision):** `git ls-remote --heads origin` checked at start — no live MISO
  backcast branch, no orphan D17 branch. Re-check before push; stay off every backcast
  MISO surface (the owner's track; miso-195 concluded there).
- **K5 (rule 25):** the D4-M ERCOT zero-retirement measurement is motivation to CHECK
  whether the cause is MISO-specific or shared, never evidence for either; no ERCOT
  artifact fills a MISO verdict and vice versa.
- **K6 (rule 22):** no out-of-training year is solved, scored, or registered; every read
  is a committed 2021–2025 hindcast artifact, a committed forecast-window (2026+)
  artifact, or committed raw data.
- **K7 (the R6 refusal, restated as a kill):** if at any point the only remaining way to
  close the residual is a tuned per-fuel constant (FOM, threshold, lag, adder), the lane
  STOPS and reports the open root-cause issue — that outcome is a valid finding.

## 6. Exit contract

`docs/handoffs/FINDING-capx-d17-miso-exit-channel-2026-09-01.md` with the attribution,
each thread's verdict against its own frozen kill, the routed repairs (priced,
admissibility stated per rules 13/21, not built), and the explicit MISO-specific vs
shared-machinery statement. Both documents pushed per CLAUDE.md Git & Pushing (fresh off
origin/main, rebase before every push, blob-verify any ≥300-line file per rule 27).
Report to the director.

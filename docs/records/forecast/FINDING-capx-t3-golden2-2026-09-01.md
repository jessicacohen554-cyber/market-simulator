# FINDING — capx T3-NEISO-GOLDEN-2: the second §2.1b campaign (NEISO 2026–2050 BAU at the R-A-armed storage-entry posture)

**Session:** T3-NEISO-GOLDEN-2 (capacity-expansion / Forecast Finalization track), branch
`claude/capx-t3-golden-2-tm9eiy`, lane issued at the director's r#26 sitting, amendment 1
(`capx-director-ledger-2026-08.md` §0w + §3 Q25).
**Date:** 2026-09-01 · **HEAD at launch:** `5083e29e` (origin/main).
**Status:** §§1–4 are the PRE-DECLARATION — written and committed BEFORE any solve was
launched (rules 13/21 discipline; the T3-NEISO-GOLDEN §§1–4 pattern). §§5+ carry the
measured record and were written after.

---

## 1. The authorization (leg (d), cited verbatim)

Owner ruling **Q25**, capx r#26 sitting amendment 1, 2026-09-01, recorded in
`docs/handoffs/capx-director-ledger-2026-08.md` §3:

> **Q25** — The golden re-solve, fully ripe at last: Q16's ceiling premise discharged
> (FC-5 CAVEAT via D25; FC-6 CAVEAT via D26's repaired P1, which PASSES), the standing
> golden still records the pre-R-A posture (headline: ZERO storage entry in 25 years)
> while R-A armed exactly the storage-entry mechanisms and D25 measured that family as
> the corridor's largest divergence. Authorize a second §2.1b campaign? — **RULED
> 2026-09-01 (r#26 amendment 1) — AUTHORIZED, NOW** (over the after-D33 and hold
> options). One campaign: **T3-NEISO-GOLDEN-2**, NEISO BAU 2026–2050 at HEAD with the
> R-A-armed posture, its own FC-6 battery at its own vintage (the D26
> `carbon_price_delta` construction), full-rubric scoring, preserve-then-overwrite (the
> pre-R-A golden stays preserved with its posture-epoch caveat). Q13's "this campaign
> only" scoping carries over verbatim — a third campaign needs a new owner act.
> Execution = lane **T3-NEISO-GOLDEN-2** (Fable).

**Scope discipline:** ISO=NEISO, window=2026–2050 BAU golden at HEAD, budget per the
FF-3E basis the first campaign was priced on (~1.0 h wall / ~4.3 GB RSS for the campaign
solve) **plus the D26 §8.4 pricing rider** for the campaign's own FC-6 evidence (base +
three perturbed arms ≈ four ~30-min solves + the ~12–25 min battery ≈ +2 h). **THIS
CAMPAIGN ONLY** — Q13's scoping carries over verbatim; no standing authorization; a third
campaign needs a new owner act. `--full-solve-authorized` is licensed by Q25 and by
nothing else.

**What this campaign is for, stated so the lane cannot drift:** the question is whether
the ARMED storage-entry economics produce entry (and what the full-horizon system then
looks like) — NOT whether storage entry makes any verdict better. Rule 13 / D25
discipline: no input, parameter or threshold moves toward any corridor row; the corridor
is re-dispositioned against the new trajectory, never the other way around. **EITHER
storage outcome is a valid result** — zero entry under armed economics would itself be a
major finding, routed to the director, never "fixed" in-lane.

## 2. Gate-condition verification at launch (all four legs, read live at `5083e29e`)

- **(a) Backcast calibration proof — PASS, re-read live this session:**
  `frontend/data/backcast/calibration-complete.json` `complete` block = {ERCOT, NEISO,
  PJM}; NEISO entry keys keeper `2026-08-17-neiso-99-joint-p1`. `final` block empty
  (never required for forecast work). The holdout spend freeze is TIER-SCOPED to the
  locked test — orthogonal to a forecast-mode 2026+ campaign.
- **(b) POC gates green — PASS, re-read live:** bare `neiso-t1f` reads **PROMOTE** in
  `ff-verdicts.json` (the D25 re-score kept the determination; FC-5 now CAVEAT rather
  than SKIPPED).
- **(c) Worth-the-compute evidence — PASS, and stronger than at Q13:** the first
  campaign's committed record (25/25 years, 29.2 min, inside budget) plus the three
  post-campaign instrument closures — D25's FC-5 dispositions (0 UNEXPLAINED; the
  zero-storage family measured as the corridor's largest cross-ISO divergence, −56 % to
  −96 %, four ISOs), D26's repaired FC-6 P1 (PASSES on the correctly-constructed arm),
  and D24-R's cache-key repair (the armed/unarmed posture ambiguity of golden-1 §5.1(b)
  cannot recur — measured below).
- **(d) Owner authorization — the Q25 ruling quoted in §1.**

**Heavy-slot check at launch:** `git ls-remote --heads origin` shows two in-flight
branches — `claude/audit-program-director-irzj4a` (audit board, no solve),
`claude/miso-st-gas-steam-chp-calibration-9snn32` (owner's MISO backcast track, its own
container). No PJM (8.8 GB) / MISO (9.6 GB) no-co-run measure shares this container; the
~4.3 GB NEISO leg launches solo. **Collision map carried from the charter:** D33 (NEISO
position lane) is docs-only and had landed nothing at launch — its result informs
interpretation and is cited if it lands mid-session; D20 owns the seven LEGACY verdict
keys + the FC-7 scorer path (my keys are out of its scope; the committed-verdict control
below is re-run after any rebase that pulls a scorer change); D34 owns the
`carbon_price` validation seam (no overlap with `carbon_price_delta` usage); D31 is
MISO-side.

## 3. PRE-DECLARED run construction, budget, and expectations

**The campaign run — zero config invention, HEAD defaults at golden posture. The armed
posture IS HEAD's shipped defaults; nothing is hand-set:**

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 \
  --golden-posture --full-solve-authorized --out-dir results/ff-t3-neiso-golden/bau
```

- `mode="forecast"`, every `ScenarioConfig` field at its shipped HEAD default. The
  resolved config carries **`storage_entry_availability_gate=True`** and
  **`storage_entry_cost_normalized_rank=True`** (the R-A arming, commit `ecf9972`,
  epoch 2026-08-31) and **`carbon_price_delta=0.0`** (the D26 instrument field at its
  no-op default). Golden posture resolves the capacity-clearing gate through the ONE
  reader (`shipped_capacity_clearing_by_iso` — NEISO curve-ON);
  `forecast_xyear_warmstart` OFF per owner D-10. No flag beyond the two the charter
  names; **no new mechanism, no `ScenarioConfig` field, no matrix duty** (rule 28: if a
  field is ever wanted, STOP and route).
- **Resolved cache key, declared before launch:** **`706e7ba8e6582d42`** (the resolved
  NEISO 2026–2050 golden-posture config at HEAD `5083e29e`, single-root fold). Distinct
  from the pre-R-A golden's `a4b11ef4aaa1be35` — the D24-R (b′-1) declared-defaults
  ledger is what makes the two postures key distinctly (registration-time defaults
  False/False; the armed True values are non-default against the ledger and enter the
  hash). Golden-1's §5.1(b) scenario-identity ambiguity therefore CANNOT recur on this
  bundle: the key alone now identifies the posture.
- Years run SEQUENTIALLY within the invocation (rule 12); the FC-6 arm solves are also
  run sequentially, one at a time, per this lane's charter. Container: 15 GB RAM /
  4 CPU. `data/clean` was absent (fresh container) and is being rebuilt in full before
  launch (~30–35 min, the standing §2.4 prerequisite; measured time reported in §5).
- **Expected cost (pre-declared):** campaign solve ~30–60 min wall / ≤4.5 GB peak RSS
  against the Q25 budget basis of ~1.0 h / ~4.3 GB. Anchors: golden-1 29.2 min /
  3.50 GB and the D26 base arm 32.1 min / 3.44 GB — both UNARMED-posture solves. The
  armed screens add per-year candidate arithmetic (cheap); **if the screens admit
  storage entry, later-year LPs grow** (3 variables × 8760 h + SOC rows per entering
  unit), so wall/RSS above the unarmed anchors is an expected consequence of entry
  itself, reported not judged. FC-6 evidence: four ~30–35 min solves + battery ≈
  2.2–2.7 h. Measured-vs-projected reported in §5 whatever it reads.
- **Checkpoint discipline:** the runner writes `evolution_<year>.json` beside each
  year's cached result as the horizon progresses; per-year evolution artifacts are
  committed and pushed mid-horizon as checkpoints. **If the solve breaks mid-horizon,
  the failure record IS the deliverable** — reported at full magnitude; a partial run
  is never registered as complete.
- **Requirement bar carried unchanged** (the S-4b intake, all values ISO-NE's own ARA-3
  prints): DR-netted requirement factor 1.0286103, firm external-tie credit 409.31 MW.
  Nothing in this campaign re-derives or re-tunes any of it.

**Preserve-then-overwrite, declared in advance (executed in this pre-declaration commit
for the bundle, at registration for the record):**

1. **The bundle:** the standing pre-R-A golden bundle moves BYTE-IDENTICALLY (git mv, 45
   committed files) from `results/ff-t3-neiso-golden/bau/` to
   **`results/ff-t3-neiso-golden/bau-prera-2026-08-31/`** — its dated home, named by its
   solve date; its posture-epoch caveat travels with it (its `run_config.json` records
   both storage fields `False` and `git.basis_sha 9e56f0f`). It remains the pre-R-A
   record of note. The move lands in the SAME commit as this pre-declaration, BEFORE the
   campaign writes anything into `bau/`. (Path references inside previously-committed
   verdict provenance resolve at their recorded `scored_at_sha`, where `bau/` is the old
   bundle — checked: no script, test, or src file references the path; the three
   record-surface references are re-authored or annotated this session.)
2. **The verdict record:** at registration, the current bare `neiso-t3` entry (the D26
   re-score of the pre-R-A golden) is preserved BYTE-EQUAL at
   **`neiso-t3-prera-2026-08-31`** in `ff-verdicts.json`; the bare `neiso-t3` key then
   takes this campaign's verdict. The existing preserved chain
   (`neiso-t3-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`) is untouched.
3. **The FC-5 table:** `results/ff-corridor/dispositions/neiso-t3.json` (authored by D25
   against the pre-R-A trajectory) moves to
   `results/ff-corridor/dispositions/neiso-t3-prera-2026-08-31.json` when the
   re-dispositioned table is authored; the bare name takes the new table.
4. **The run-explorer record:** the first campaign's
   `frontend/data/hindcast/neiso-2026-2050-t3-golden-bau.json` sidecar stays byte-equal
   (its embedded paths are registration-time provenance); this campaign registers under
   its own new run id via `register_forecast_run.py --summary … --label t3-golden2-bau
   --kind t3`.

**The FC-6 battery — this campaign's own vintage (= HEAD), the D26 construction, priced
before running:**

- **Paired arms**, each `reference_config("NEISO", 2026, 2050, cmc=False,
  golden_posture=True)` ± exactly one signal via
  `run_driver_battery.py --paired-arm {base, carbon_plus25, gasup150, gaspm5}
  --full-solve-authorized`, sequential:
  - `base {}` — the explicit reproduction control: its trajectory and I1–I14 vector must
    reproduce the campaign bundle exactly (same environment, same HEAD, same data; the
    CLI and the paired-arm driver share `reference_config` by construction). This solve
    doubles as the §5-attestation FF-4B reproducibility evidence. The perturbed arms
    launch only after it passes.
  - `carbon_plus25 {"carbon_price_delta": 25.0}` — the REPAIRED P1 arm (D26): a genuine
    +$25/t over the resolved RGGI trajectory in every year; the premise row is asserted
    by `check_forecast_invariants.carbon_pair_premise` (a violating pair yields P1=SKIP
    + FAIL premise, never a scored P1). **Never a `carbon_price` replace.**
  - `gasup150 {"gas_price_factor": 1.5}` (P2 merit-order sign) and
    `gaspm5 {"gas_price_factor": 1.05}` (P3 perturbation stability).
- **Battery:** the pre-registered NEISO ladder is T1.6 ONLY (2 rungs).
  `renewable_buildout_pace` — its pre-registered driver — is verified STILL consumed by
  no model code at HEAD `5083e29e`, so **both gate rows are expected VACUOUS ⇒ the
  battery leg is CAVEAT-at-best by construction** (D21 finding 2, the wiring decision is
  not this lane's). A vacuous rung is a CAVEAT, never a PASS. The ladder is run anyway:
  the battery output is the committed evidence OF that vacuity at this vintage, and the
  scorer's constant-series detection is what grades it.
- All FC-6 evidence lands in the campaign bundle's `fc6/` (the golden-1 layout), scored
  from THIS campaign's own bytes — no carry of any D21/D26 row (the arms are re-solved
  at this vintage precisely because FC-6's paired evidence is vintage-pinned).

**Verdict construction (declared in advance).** `forecast_verdict.py --tier t3`, scored
from committed artifacts only: this campaign's `full_horizon_summary.json` +
`run_config.json` + `dof_ledger.json` (built by the committed
`build_forecast_dof_ledger.py`) + this campaign's `fc6/` battery and paired-invariants
records + the re-authored corridor disposition table + the committed
`benchmark-corridor-anchors.json` + the committed T1-H score
(`results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json` — the
posture-matched curve-ON leg golden-1 disclosed; NO post-R-A NEISO T1-H exists, a stated
limit of FC-3's evidence, not a reason to solve backcast-window years off-charter) + the
committed D14 T1-X crossover score + **this campaign's own `forecast_attestation.json`**.

**The attestation, declared up front so it cannot be an outcome-shopping vector:**
golden-1 refused to author one mid-campaign because inventing an instrument after the
pre-declaration to clear a row is forbidden. The instrument now EXISTS (rubric §5;
`forecast_verdict._score_attestation`; the rubric's artifact table names "the producing
session (T3)" as its author). This campaign therefore declares NOW, before any solve:
after registration it authors `forecast_attestation.json` with the six §5 assertions,
each stated truthfully at authoring time — `dof_ledger_complete`,
`run_config_reproducible` (evidence: the base-arm reproduction),
`honest_unfit_referenced`, `quarantine_attested`, `no_off_registry_knobs`,
`registered` — and **any assertion that is not true is recorded `false` and FC-7 fails
on it at full magnitude**; nothing is softened to clear the row.

**Control-first, already executed before this pre-declaration:** the committed
`neiso-t3` verdict was REPRODUCED byte-for-byte (zero non-provenance diffs) from exactly
the committed inputs by the HEAD scorer, before anything was moved or overwritten — the
D25/D26 control pattern. The baseline is proven, not assumed.

**Pre-declared expectations (recorded before the solve):**

1. **The storage-entry outcome is OPEN.** No expectation is declared for it in either
   direction; both zero and nonzero entry are valid results. Whatever enters (GW by
   year, admitting mechanism, which screen leg binds) is reported at full magnitude.
   Zero entry under armed economics is routed to the director as a major finding.
2. **Head-of-horizon (2026–2030) reproduces the S-4b/golden-1 trajectory IF AND ONLY IF
   the armed screens admit no storage in those years.** The armed posture is the ONLY
   config delta vs the D26 base arm (which reproduced golden-1 exactly at its vintage),
   plus whatever `data/raw` intakes landed since `9e56f0f` (the RC-R NEISO
   demand-curve + confirmed-retirements rows — a HEAD-vintage campaign legitimately
   solves HEAD data; any head-year divergence is decomposed against BOTH candidates and
   attributed, never adjusted away).
3. **Out-year behavior (2031+) is REPORTED, never judged and never back-tuned** (rules
   13/21). No result feeds back into any input; no value is reverse-engineered to clear
   an invariant.
4. **Expected determination: HOLD** — FC-3 carries the committed T1-H FAIL and FC-4 the
   committed D14 T1-X FAIL regardless of anything this campaign solves; FC-1/FC-2
   depend on the new trajectory (golden-1's I3 dump FAIL and I13 cobweb WARN may move
   under storage entry — reported either way); FC-6's battery leg is vacuous-CAVEAT by
   construction (above); FC-5 re-dispositions are authored judgment. **The Q25
   authorization licensed the compute and the storage answer, not a promotion claim.**
   No instrument is invented mid-campaign to move any row (the attestation above is
   pre-declared, not invented after a row reads against us).
5. **FC-5 re-disposition:** the corridor memo convention imported whole (>15 % or
   opposite sign/direction ⇒ written ours-vs-theirs explanation naming the mechanism;
   any UNEXPLAINED row ⇒ FC-5 FAIL). With the D29 grain the summary now carries
   generation-by-fuel + the real `storage_power_mw` column, so the energy-mix anchor
   family becomes dispositionable on a golden for the first time, and the storage row is
   dispositioned battery-only (net of the documented NEISO PS residual 1,865.0 MW —
   the D29 classification trap, stated in the row basis). Anchors remain context, never
   targets.

## 4. The carried caveats (verbatim, per the Q25 ruling — nothing re-tuned)

**(i) The S-4b floor-dependence caveat carries wherever the head years reproduce.** If
2028/2029 clear at +419.0 / +333.6 MW again, those signs still ride on the 699.3 MW
retention response (S-4b §5.3, quoted in full in golden-1 §4(i)); if the armed posture
moves those years, the floor-attribution is re-measured from the new bundle's
`floor_retention_log`, not assumed.

**(ii) D14's retirement-composition miss carries verbatim.** Exit recall 2/6 reachable
≥300 MW targets in the crossover window; the economic screen concentrates exits in gas
(+66 % gas_cc) and missed the biomass/coal/gas_ct/oil exits entirely. Nothing in the
R-A arming touched the retirement screen, so every exit wave this campaign reports is
composed by the same screen and every out-year composition statement must be read with
it.

**(iii) The FC-7 instrument state is BETTER than golden-1's but the truth-telling duty
is unchanged.** The DOF-ledger instrument exists (lane D8) and the attestation schema
exists (rubric §5); this campaign builds its own ledger and authors its own attestation
per §3. What carries from golden-1 is the discipline: unidentified DOF entries are
listed open, false assertions are recorded false, and FC-7 reads whatever the artifacts
say.

**(iv) The FC-6 battery leg's vacuity carries** (D21 finding 2): NEISO's entire
pre-registered battery is the T1.6 ladder and its driver is still unwired at HEAD.
CAVEAT-at-best by construction; the wiring/registration decision remains the
director's/owner's, not this lane's.

**(v) FC-5 is permanently single-source for the t3-required table** (owner ruling Q23:
"None — I'm not getting more data"): AEO2025 alone anchors NEISO. A named, accepted
limitation; the CAVEAT is the steady state.

---

*(Sections below were written AFTER the solves; §§1–4 above were committed before
launch.)*

## 5. Measured cost vs projected

**The campaign run completed: 25/25 years, `error: None`, cache key
`706e7ba8e6582d42` — the pre-declared resolution, byte-exact.** Launched
19:06:22Z, summary written 19:41:33Z (2026-09-01).

| axis | §3 pre-declared | measured | reading |
|---|---|---|---|
| wall clock | ~30–60 min (Q25 basis ~1.0 h) | **35.1 min (0.585 h)** | 59 % of the Q25 budget |
| peak RSS | ≤4.5 GB (Q25 basis ~4.3 GB) | **3.48 GB** | 81 % of budget |
| solve years | 25, sequential | 25/25, sequential (rule 12) | as declared |
| cache key | `706e7ba8e6582d42` (ex ante) | `706e7ba8e6582d42` on disk | **exact** |
| data/clean rebuild | ~30–35 min | **38.4 min** (17:30:35→18:08:59Z), 53/53 datatypes, 0 failures | the §2.4 container prerequisite; `benchmark-corridor`, which failed at the D26 vintage, regenerates cleanly at HEAD |

Per-year median 81.4 s (golden-1: 68.7 s — the armed screens and the HEAD data
add ~18 % per year). **Checkpoint note (honest deviation from §3):** the solve
completed inside a single session wake, so the per-year `evolution_<year>.json`
checkpoints were committed immediately after completion in one commit
(`a5523fac`) rather than incrementally mid-horizon; the checkpoint files
themselves were written per-year by the runner as declared, so a mid-horizon
failure would still have preserved the record.

### 5.1 Scenario-identity integrity — the golden-1 §5.1(b) ambiguity cannot recur

The armed posture keys distinctly (`706e7ba8e6582d42` ≠ pre-R-A
`a4b11ef4aaa1be35`) because the D24-R (b′-1) declared-defaults ledger makes a
post-flip field identify in the hash. The flip-back control (resolved HEAD
config with both storage fields set False) keys at `500790494e360a2a`, not the
pre-R-A key — **not** hidden config drift: the resolved-config **field diff**
against the committed pre-R-A `run_config.json` is exactly **5 fields** — the
armed pair (`storage_entry_availability_gate`,
`storage_entry_cost_normalized_rank` False→True), plus three provably inert
ones (`carbon_price_delta` added at its 0.0 no-op default, D26's 25-year
byte-inertness proof; `caiso_offer_surface_measured_ungrounded` added at False,
CAISO-scoped; `renewable_buildout_pace` deleted by T16, consumed by no model
code per D21). The key difference beyond the armed pair is hash-STRUCTURE
bookkeeping from the added/deleted field set — cite configs, not keys, across
epochs (the D21 finding-6 lesson, holding again). The cache epoch ledger
carries no solve-affecting entry after R-A (2026-08-31).

## 6. The horizon record — reported, never judged, never back-tuned

No actuals exist for any year in this window; nothing below is scored against a
measured outcome, no result feeds back into any input, and no value was
reverse-engineered to clear an invariant (rules 13/21).

### 6.1 THE STORAGE-ENTRY ANSWER (the campaign's object)

**Under the armed posture, storage enters — once, at the horizon's edge: 720 MW
of 100-hour iron-air in 2050. Zero entry in all of 2026–2049.**

- The 2050 build (`evolution_2050.json` `storage_additions`): iron_air, 100.0 h
  duration, zone-split by load share — North 144.0 / Central 216.0 / Boston
  151.2 / Connecticut 208.8 MW.
- **Sizing attribution:** 720.0 = `STORAGE_TECH_BUILD_SHARE_CAP` (0.6) ×
  `STORAGE_ANNUAL_BUILD_CAP_MW["NEISO"]` (1,200 MW) — iron-air hit its
  diversification cap of the annual budget, i.e. the screen wanted MORE
  iron-air than the cap allows, **and no second technology claimed the
  remaining 480 MW** of budget. One tech clears, at its cap, in one year.
- **Mechanism attribution:** iron_air passes the D-2 availability gate trivially
  by 2050 (`STORAGE_TECH_AVAILABLE_YEAR["iron_air"]=2024`), so the gate is not
  what delayed entry to 2050 — the VALUE STACK (arbitrage + RA capacity value
  at curve-ON) first clears a technology's annualized cost only in the
  horizon's tightest, highest-priced year (2050: LW $79.16, 2,446 h ≥ $100/MWh,
  the monotone out-year tightening of §6.3). Under the D-3 cost-normalized rank
  the clearing pick is the 100-h machine (capex $2,000/kW over 100 h of
  duration dominates margin-per-capex-dollar in a long-scarcity year), where
  the pre-R-A absolute-margin rank had cleared nothing.
- **What either posture would have done on this data in 2026–2049 is identical
  by construction** — zero entry means the armed screens added no units, so
  those years' LPs are the same under both postures; the arming's entire
  solve-visible effect on this horizon is the 2050 build.
- **The corridor consequence:** the 2030/2035/2040 FC-5 storage anchors are
  UNTOUCHED by the arming (battery fleet still the 0.77 GW base at every anchor
  year, −56.2 % vs AEO). **The D25 §4.3 mechanism-2 divergence family — the
  corridor's largest — survives the armed screens at the anchor years.** The
  armed economics do not produce entry when AEO says it happens (1.76 GW by
  2030); they produce it two decades later, at the LDES end of the tech space.
  Routed to the director as the campaign's headline structural result (§8).

**Correction 2026-09-02 (D38, routed by D36 §8.3).** The mechanism-attribution
bullet above — "under the D-3 cost-normalized rank the clearing pick is the
100-h machine …, where the pre-R-A absolute-margin rank had cleared nothing" —
**misattributes the 2050 clearing to the rank**. D-3 is **sign-preserving**: by
its own docstring (`storage.py:1789`) it reorders clearing technologies and can
neither create nor remove a clearing, and D-2 only removes candidates, so on
identical prices the armed screen clears a *subset* of what the unarmed screen
clears — the arming could not have produced the 2050 entry. The clearing is a
**DATA-channel result**, the same channel §6.2 below already attributes the
trajectory delta to: the RC-R demand-curve intake re-times the exit waves, less
capacity is retained, and the out-year stack tightens (2049: 2,243 h ≥ $100/MWh
vs golden-1's 1,339; 2050: 2,446 vs 1,531), so the iron-air requirement crosses
its arbitrage leg between the 2049 and 2050 screens ($83.4 → $78.7/kW-yr). What
the rank did do is choose *among* clearers — and iron-air was the only one, so
it was never decisive here. Everything else in §6.1 stands unchanged: the 720 MW
sizing attribution, the availability-gate attribution, the identity of 2026–2049
under both postures, and the corridor consequence. No verdict, gate, cell or
corridor row moves on this correction. Basis: D36 §1 (consequence 1), §4 census
row "D-3 cost-normalized rank", §6 —
`docs/handoffs/FINDING-capx-d36-storage-valuestack-2026-09-02.md`.

### 6.2 Head-of-horizon: golden-1 does NOT reproduce, and the divergence is
### decomposed, not absorbed

Pre-declared expectation #2 anticipated exact reproduction **iff** the armed
screens admitted nothing in 2026–2030 *and* the HEAD data intakes were inert.
The screens admitted nothing through 2049 — **yet the trajectory diverges from
the very base year**, so the divergence is the DATA channel (§5.1 bounds the
config channel to the armed pair + inert fields; the cache epoch ledger carries
no other solve-affecting change). The two intakes landed since `9e56f0f` are
exactly the RC-R pair: `capacity-market/demand-curve/neiso` (+15 rows, the
FCA/MRI curve rework) and `confirmed-retirements/neiso.csv` (+79 rows, the
registry completion). Measured decomposition:

- **Base fleet (2026): −198.9 MW thermal** (gas_ct −101.0, oil −97.9) — the
  completed confirmed-retirement registry excludes units the old partial
  registry missed (applied at fleet build; no 2026 ledger retirement rows).
  2026 prices identical (LW $52.13 both), CO2 −0.012 Mt.
- **Every re-timed wave is `reason: economic`** (ledger-verified old vs new;
  zero non-economic rows at the head), so the re-composition flows through the
  retirement/entry screens' capacity-revenue term — the RC-R demand-curve
  intake expressing through the Potomac-SOM margin, not through instrument
  rows: 2027 exit wave 1,972.7 MW (was 2,231.8, −259.1); the CCS-exit wave
  moves 2033→2034 and grows (1,701.0→1,873.8); **the 2037 North oil-steam exit
  (1,451.6 MW) never fires** — only Boston's 237.7 MW retires, in 2038; thermal
  entry falls 7,500→4,500 MW (first economic entry 2030→2031) and stays 100 %
  `economic` (zero backstop, zero planned — now scorer-visible via the
  builds_by_source grain).
- **Out-years:** tighter (RM 0.05–0.09 vs 0.07–0.10), pricier (2050 LW $79.16
  vs $66.39; 2,446 h ≥ $100 vs 1,531), dirtier (2050 CO2 5.29 vs 3.21 Mt — the
  retained oil fleet at 4.85 GW vs 3.49, and 1.9 GW less late CCS since less
  late CC is built to convert). CCS conversion still reaches 100 % of the CC
  fleet by 2040 in both (13,135.4 MW here).
- **The interpretive seam this cuts:** the golden-2 vs golden-1 delta is
  DOMINATED by the RC-R capacity-revenue intake, not by the storage arming the
  campaign was authorized to measure. That the NEISO capacity-market revenue
  surface re-times 3.4 GW of exit waves and 3 GW of entry is precisely the
  surface lane D33 (accreditation basis / cleared-vs-qualified) is chartered to
  examine — D33 had landed nothing at this campaign's close; its finding should
  be read against this decomposition when it lands (§8).

### 6.3 Trajectory at reporting grain

| year | peak MW | RM | LW $/MWh | CO₂ Mt | thermal MW | firm clean | VRE MW | storage MW (fleet) | gen TWh |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026 | 24,890 | 0.156 | 52.13 | 16.308 | 22,951 | 1,900 | 4,100 | 2,635 | 117.1 |
| 2030 | 26,209 | 0.038 | 71.56 | 14.885 | 20,849 | 1,900 | 7,100 | 2,635 | 123.4 |
| 2035 | 27,848 | 0.083 | 72.38 | 10.267 | 22,475 | 1,900 | 14,902 | 2,635 | 131.5 |
| 2040 | 29,559 | 0.089 | 70.53 | 4.488 | 23,237 | 1,900 | 22,100 | 2,635 | 139.9 |
| 2045 | 31,376 | 0.069 | 72.08 | 4.587 | 23,237 | 1,900 | 29,902 | 2,635 | 150.4 |
| 2050 | 33,304 | 0.066 | 79.16 | 5.290 | 23,237 | 1,900 | 37,100 | **3,355** | 163.2 |

Totals: exits 4,138.2 MW (2027 gas_cc 1,876.8 + gas_st 95.8; 2029 coal 54.0;
2034 gas_cc 234.7 + gas_cc_ccs 1,639.1; 2038 oil 237.7); thermal adds 4,500 MW
(100 % economic — 4 × 1,000 gas_cc 2031/33/35/37 + 500 gas_ct 2032); VRE adds
33,000 MW in the same alternating 1,802/1,198 cadence as golden-1; storage adds
720 MW (§6.1). RPS dual pinned at the **$50 ACP ceiling in every year** —
unchanged from golden-1. The `generation_by_fuel_mwh` grain (D29, first golden
carrying it): in-region generation 90.1 TWh (2030) → 109.3 (2040), imports
~30–33 TWh/yr, gas_cc_ccs the largest single in-region source from 2030
(23.1 TWh) and oil-fired ENERGY ≈ 0 in every year even as 4.8–5.1 GW of oil
CAPACITY is retained — capacity value, not dispatch, is what keeps it alive.

**Structural signals, at full magnitude:**

1. **I3 FAIL — out-year renewable dump, same onset, slightly shallower end:**
   2043 2.17 % (identical to golden-1's onset) rising to 7.76 % (2049) / 7.74 %
   (2050) vs golden-1's 8.50 % — the 720 MW iron-air and the retained thermal
   absorb ~0.8 pp of the terminal dump. Still a FAIL; still coherent with 37 GW
   VRE against a 33 GW peak with (almost) no storage and no incremental firm
   clean.
2. **I13 WARN — cobweb `gas_cc(7)`** (golden-1: `gas_cc(10)`); the alternating
   VRE cadence persists identically.
3. The 2028/2029 I7-margin floor-dependence caveat (§4(i)): the head years no
   longer reproduce S-4b's exact figures (RM 2028 0.0465, 2029 0.0430 vs S-4b
   0.04501/0.04150), so the S-4b numbers do not transfer verbatim; the
   floor-retention mechanism is unchanged and the sign of these margins still
   rides on it (this bundle's own `floor_retained` ledger rows are committed
   with the checkpoints).

**Caveat (ii) carried, as Q25 requires:** every exit wave above is composed by
the same economic screen D14 measured at exit recall 2/6 with a
gas-concentration bias; the 25-year composition — including the missing oil
exits that this solve now RETAINS even longer — inherits that defect, and every
composition statement in §6.2–6.3 must be read with it.

## 7. FC-6 at this campaign's own vintage, the verdict, and the registration

### 7.1 The FC-6 evidence (all four arms solved sequentially, this vintage, this data)

| leg | wall | result |
|---|---|---|
| base (reproduction gate) | 35.0 min | **REPRODUCES THE CAMPAIGN EXACTLY** — 25 years × every trajectory field + the full I1–I14 vector, cache key `706e7ba8e6582d42` both. The perturbed arms were gated on this check (control-first); it is simultaneously the attestation's FF-4B reproducibility evidence. |
| `carbon_plus25` (`carbon_price_delta=25`) | 34.6 min | key `f7cced798488ddac`; cum CO₂ 229.82 → **196.00 Mt (−14.7 %)**, LW price higher in every year (2026: 52.13 → 62.28; 2050: 79.16 → 84.65) |
| `gasup150` (`gas_price_factor=1.5`) | 34.1 min | key `65662ca117959ee5`; cum CO₂ 281.46 Mt, 2050 LW $93.95; **builds NO 2050 iron-air** (fleet 2,635 MW — the only arm without the entry) |
| `gaspm5` (`gas_price_factor=1.05`) | 34.0 min | key `2d017ed9675aa386`; cum builds move 0.0 % |
| battery | ~0 s | T1.6 is **OUT OF SERVICE** at HEAD (lane T16, 2026-09-01: `renewable_buildout_pace` deleted under rule 26 — a sharper state than §3's pre-declared "vacuous two rows"; same substance, now structural): both gate rows emit SKIP with the out-of-service reason, zero solves |

Total FC-6 solve wall 2.30 h — inside the §3 pricing (2.2–2.7 h). Paired rows
(assembled from the three checker passes, committed as
`fc6/paired_invariants.json`):

- **P1 PASS** — cumulative CO₂ base 229.82 vs high 196.00 Mt under the genuine
  +$25/t; **P1.premise PASS** — strictly +25.00 in all 25 years (the D26
  construction working natively at its second-ever use).
- **P2 FAIL — "year 2050: wrong: gas_cc↓" — a NEW finding, root-caused and left
  standing as scored.** The leg tests unabated-`gas_cc` generation falling
  under gas ×1.5 at the last common year. Measured: the BASE holds **zero**
  unabated CC at 2050 (100 % CCS-converted by 2040), while the gas×1.5 world
  retrofits LESS (CCS stalls at 9,846.8 vs 13,135.4 MW — the retrofit's
  fuel-cost penalty scales with the gas price) and builds MORE late CC (6,500
  vs 4,500 MW, the 2039/2045/2047 builds landing after
  `ira_ccus_45q_last_year=2032` so they never convert) — so the arm holds
  6,000 MW of unabated CC generating 23.2 TWh against the base's 0, and the
  per-fuel-key comparison reads as a sign violation. **At the all-gas level
  the sign is correct** (total gas generation 36.53 → 35.36 TWh at 2050,
  imports up), and the arm's higher CO₂ (10.90 vs 5.29 Mt at 2050) is the
  un-abatement composition effect. This is the same instrument family as
  D23's P1 attribution — a check written for same-fleet dispatch pairs being
  crossed by a 25-year fuel-CLASS migration (gas_cc → gas_cc_ccs is the same
  physical fleet under a different label) — **but nothing here is edited**:
  the FAIL stands in `paired_invariants.json` and the verdict, per the D21
  charter line (a FAIL is the instrument speaking; whether P2 should compare
  the all-gas block on evolution pairs is an instrument-scope question ROUTED
  to the director, §8).
- **P3 PASS** — cumulative builds move 0.0 % under ±5 % gas (38,220 MW both;
  rate-limit-shaped, the golden-1 annotation carrying over).

### 7.2 Determination: **T3 HOLD** — pre-declared correctly; the gate map moves in both directions

| gate | golden-1 final (pre-R-A record, D26 re-score) | **golden-2 (this campaign)** | movement |
|---|---|---|---|
| FC-1 structural integrity | FAIL (I3 dump) | **FAIL** (I3 dump, onset 2043 identical, terminal 7.74 %) | — |
| FC-2 adequacy & equilibrium | FAIL (cobweb gas_cc(10)) | **FAIL** (cobweb gas_cc(7)) | — |
| FC-3 capacity-evolution skill | FAIL (T1-H bands, 9 failing) | **FAIL** (same committed input; no post-R-A NEISO T1-H exists — stated FC-3 evidence limit) | — |
| FC-4 crossover dispatch skill | FAIL (D14 T1-X) | **FAIL** (same committed input) | — |
| FC-5 external corridor | CAVEAT (33 rows) | **CAVEAT** (54 rows, 0 UNEXPLAINED — generation family + PS row newly scoreable) | broader evidence, same status |
| FC-6 driver response | CAVEAT (repaired P1 PASS; vacuous battery) | **FAIL** (P1/P3 PASS, premise PASS; **P2 FAIL** — §7.1; battery CAVEAT out-of-service) | **CAVEAT → FAIL** (new finding) |
| FC-7 provenance & DOF | FAIL (UNATTESTED) | **PASS** — original artifacts, 7/7-identified DOF ledger, the §3-pre-declared rubric-§5 attestation, all six assertions true with cited evidence | **FAIL → PASS (first FC-7 pass on any golden)** |
| FC-8 runtime | PASS | **PASS** (35.1 min / 3.48 GB) | — |

**Determination: HOLD on FC-1/FC-2/FC-3/FC-4/FC-6** — §3(4) predicted HOLD and
named FC-3/FC-4 as carried; FC-6's FAIL arrived through a leg (P2) the
pre-declaration did not predict, and FC-7's PASS was the declared intent
executed. Both movements are stated rather than absorbed. The scorer control
was re-run TWICE against the committed pre-R-A record — at launch HEAD
`5083e29e` and again after the mid-session D20 scorer amendment landed —
byte-identical outside provenance both times, so the instrument that graded
this campaign demonstrably grades the preserved record identically.

### 7.3 Registration + board stamp (preserve-then-overwrite, exactly as Q25 ordered)

- **Bundle:** the campaign lives at `results/ff-t3-neiso-golden/bau/` (slim
  committed record: config.yaml + 25 evolution checkpoints +
  full_horizon_summary + run_config + dof_ledger + forecast_attestation +
  forecast_verdict + `fc6/` arm summaries/run_configs + paired_invariants +
  battery report). The pre-R-A golden was moved BYTE-IDENTICALLY to
  `results/ff-t3-neiso-golden/bau-prera-2026-08-31/` in the pre-declaration
  commit, BEFORE anything wrote to `bau/`. The campaign's fc6 arms solve
  inside the bundle (unlike D21/D26's out-of-repo arms), so the `.gitignore`
  campaign block gained one line scoping their solve caches session-local —
  the committed per-arm record stays exactly D21's (summary + run_config).
- **Verdict record:** `ff-verdicts.json` — the prior live `neiso-t3` (the D26
  re-score of the pre-R-A golden) preserved BYTE-EQUAL at
  **`neiso-t3-prera-2026-08-31`** (asserted in the writer); bare `neiso-t3`
  now carries this campaign (HOLD; FC map above). The existing preserved chain
  (`-pre-fc5`, `-pre-fc6`, `-pre-fc6repair`) untouched; every sibling key
  asserted byte-identical before write.
- **FC-5 table:** prior table preserved at
  `dispositions/neiso-t3-prera-2026-08-31.json`; bare `neiso-t3.json`
  re-authored (54 rows / 28 IC / 26 EX / 0 UNEXPLAINED).
- **Run explorer:** sidecar `neiso-2026-2050-t3-golden2-bau` (kind t3, label
  `t3-golden2-bau`); the generated registry/runs/manifest are the Pages
  deploy's to rebuild. **Backcast namespace untouched** (plan §7.5).
- **Board:** `program-status.json` — NEISO `gate.d_owner_auth` now carries both
  grants (Q13 spent → Q25 granted AND spent on this execution, third campaign
  needs a new owner act); `golden` replaced with this campaign's measured
  record (pre-R-A pointer preserved inside it); `t3_determination` HOLD;
  top-level `t3_golden2_campaign` stamp added. Every other ISO block and
  top-level key asserted byte-identical before write.
- **Rule 28:** the NEISO lever queue (matrix §5.6) is CLEARED and was read; no
  mechanism was tested, no `ScenarioConfig` field added, no cell verdict
  moves (duties b/c/d do not fire). The campaign is posture-execution of
  already-adjudicated mechanisms (R-A's armed pair), not a lever test.

## 8. Exit state — and what is routed

**Delivered.** The second §2.1b campaign: solved (25/25, 35.1 min / 3.48 GB,
inside budget), FC-6 evidence at its own vintage (base-reproduction-gated),
full rubric scored (every category graded, none SKIPPED — the first golden
scored end-to-end with zero instrument-absence debt AND a passing FC-7),
registered preserve-then-overwrite, board stamped, finding complete. **Q25's
scope is spent: this campaign only, executed once; a third campaign needs a
new owner act** (stated per the Q13-carryover clause).

**Routed to the director — four items, none actionable inside this charter:**

1. **The storage-entry answer (the campaign's object): the armed economics
   produce 720 MW of 100-h iron-air in 2050 and NOTHING in 2026–2049** — so
   the corridor's largest divergence family (zero storage at the 2030/35/40
   anchors, −56.2 %) SURVIVES the arming. The pre-R-A "zero in 25 years"
   headline is refined, not reversed: entry exists but is late, single-tech,
   LDES-shaped, cap-bound (0.6 × 1,200 MW), and vanishes under gas ×1.5.
   Whether the value stack SHOULD clear earlier (AEO has 1.76 GW by 2030) is
   a mechanism question for a chartered lane — the D25 §6.3 route, now with
   an armed-posture measurement behind it.
2. **The P2 instrument-scope question (§7.1):** on 25-year evolution pairs the
   unabated-`gas_cc` leg crosses the CCS class migration; the all-gas sign is
   correct while the row FAILs. Same family as D23's P1 attribution; repair
   (if any) needs its own charter — nothing edited here, the FAIL stands.
3. **The RC-R capacity-revenue dominance of the golden-2 vs golden-1 delta
   (§6.2):** the demand-curve intake re-times 3.4 GW of exits and 3 GW of
   entry through the economic screens' capacity-revenue term — read lane
   D33's accreditation/position finding against this decomposition when it
   lands (it had not landed at close).
4. **FC-3's evidence vintage:** no post-R-A NEISO T1-H exists; FC-3 carries
   the pre-arming curve-ON leg. Whether to re-run the NEISO capacity hindcast
   at the armed posture (the D4-M ERCOT pattern) is the capacity-hindcast
   track's call.

**Carried caveats, restated once:** D14 exit-composition recall 2/6 (every
composition statement inherits it); the S-4b floor-dependence mechanism
(§6.3(3) — head-year figures no longer transfer verbatim, the mechanism and
its sign-dependence do); FC-5 permanently single-source (Q23); the FC-6
battery leg structurally out of service pending an owner-signed replacement
lever (T16).

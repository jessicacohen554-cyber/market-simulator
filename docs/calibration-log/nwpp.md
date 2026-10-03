# NWPP calibration log

Per-region continuation of `docs/calibration-log.md` (frozen archive, entries through 2026-07-19) for
the **Northwest Power Pool / Western Power Pool footprint** — a **pool of ~17 balancing authorities**
(BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP), NERC WECC.
**NWPP is neither a balancing authority nor an ISO**, the first such region in this repo; every name
downstream still says "ISO". Program: `docs/multi-iso/nwpp-addition-plan-2026-09.md` (charters, cards,
wave graph, lane table); desk ledger `docs/records/nwpp/nwpp-desk-ledger-2026-09.md` — **the ledger wins
where the two diverge**; Phase-0 census `docs/multi-iso/nwpp-data-audit.md`.

Entries are appended **verbatim** by the NWPP ADDITION DESK from each lane's FINDING `## Log entry`
section (plan §8.0 rule 1 — **a lane never writes this file**). Newest last.

Lever queue: `docs/mechanism-testing-matrix.md` §5.9; cell verdicts
`docs/codebase-site/data/mechanism-matrix/NWPP.js`.

---

## Lane state at file creation (2026-09-14, lane NWPP-35)

**No keeper exists.** NWPP was registered on 2026-09-14 by lane NWPP-20
(`docs/records/nwpp/FINDING-nwpp-20-2026-09-14.md`), so
`frontend/data/backcast/keepers/NWPP.json` does not exist, no bundle has been solved, and this lane
has no run to score, no determination and no gates. The first solve is lane **NWPP-40**, which is
**gated on NWPP-36** (owner ruling N3 — see below). Training window **2023–2025**, and rule 16
`[R-ALLYEARS]` binds from day one: a single-year NWPP keeper is refused.

**Counts measured at this file's base sha `d54cd9c5`, because both this program and the SOCO program
flip the same pin list and the second to land re-counts (plan §0):**
`config/iso_configs._ISO_BUILDERS` carries **NINE** regions — ERCOT CAISO MISO PJM NYISO NEISO SPP
**NWPP SOCO** — the last two both registered 2026-09-14 (NWPP-20 merged first, SOCO-20 second). The
mechanism matrix carries **nine** columns and nine shards. Seven keeper shards exist; NWPP and SOCO
have none. Prose saying "seven ISOs" is stale; prose saying "eight" was true only between the two
merges.

Facts every NWPP session inherits, so nobody rediscovers them in a residual:

- **THERE IS NO NWPP PRICE, and the rubric already knows it.** Card **N2** was ruled 2026-09-13 in
  both limbs. Limb (a) chartered lane **NWPP-13** to build a WEIM-derived hourly series under a STOP
  gate pre-registered before any data was read; **it read NO**
  (`docs/records/nwpp/FINDING-nwpp-13-2026-09-13.md`). Gate D3 — reconciliation against the independent
  Mid-C Peak index — failed in **every** year: the NW-group WEIM on-peak price sits
  **−37.5 % / −22.6 % / −23.6 %** (2023 Jun–Dec / 2024 / 2025) against Mid-C, daily correlation
  0.74 / 0.95 / 0.67, against pre-registered bars of ±10 % and ≥ 0.80. **No bar was moved after the
  series was seen, and nothing landed to `_validation-source`.** WEIM is not thin here — it clears
  **5.5–6.2 %** of footprint energy net (10.6 % pairwise-gross), so volume was never the problem;
  the problem is what the price *is*. Limb (b) is therefore live: an NWPP run reads a determination
  **naming its own basis, never a bare `CALIBRATED`**. The class exists in the scorer as rubric
  **v3.8**'s `PHYSICALLY-CALIBRATED (PRICE UNSCORED)` /
  `PHYSICALLY-CALIBRATED-WITH-CAVEATS (PRICE UNSCORED)`, keyed on the **absence** of an
  `actual_lmp.json` block — landed from lane SOCO-22, which is why lane NWPP-22's identical branch
  was **withdrawn** on rebase rather than doubled (rule 19 `[R-ONE-MECH]`;
  `FINDING-nwpp-22-2026-09-13.md` §0-bis). **A neighbouring-hub proxy stays refused outright**
  (gate G17) — do not re-open it.
- **CASCADE COUPLING IS BUILT BEFORE THE FIRST KEEPER** (owner ruling **N3**, 2026-09-13, *against*
  the desk's own recommendation). The fleet is **35,799.5 MW (36.3 %) conventional hydro** with eight
  ≥ 1 GW plants in one hydraulic chain, on machinery that models independent monthly budgets. The
  owner ruled that the first NWPP number must mean more than a test of monthly hydro budgets, so
  wave **W3b** and lane **NWPP-36** (Columbia mainstem hydraulic coupling) exist and **NWPP-40 does
  not start without them**. Lever NWPP-54 is retired, its content promoted into NWPP-36. The
  coupling is ONE default-OFF `ScenarioConfig` field on `_CACHE_KEY_OPTIONAL_FIELDS` **and**
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` in the same commit, so no existing keeper's key moves
  (gate G8 as amended).
- **BPAT'S BALANCE IDENTITY FAILS STRUCTURALLY — never assume `Demand = NetGen − TotalInterchange`.**
  It holds to 0.000 MW for PACW/PSEI/TPWR and near-exactly for ten more BAs, but for **BPAT** the mean
  residual is **−3,206 MW** and **81.5 % of hours** miss by more than 1 MW, because BPA wheels energy
  it neither generates nor serves. **BPAT is 20.26 % of footprint load** (NWPP-10 §3.1). A derive that
  assumes the identity is wrong for a fifth of the footprint in four hours out of five. A divergence
  here is a FINDING, never something to correct away (rule 14 `[R-ACCURATE]`).
- **THE CAISO DOUBLE-COUNT — DISCLOSE, DO NOT FIX.** CAISO is registered with a `WECC_import` zone
  whose firm tranche is named **`PNW_hydro_base`** (`model/interchange/caiso.py`) — *this footprint,
  by name*, priced as a Tier-3 contract-cost proxy under rule 14's misalignment exception.
  Registering NWPP puts the same physical energy on both sides of a seam, represented two ways.
  **Rule 25 `[R-ISO-SCOPE]` forbids this desk touching how CAISO prices its side**; the CAISO-side
  question is ROUTED (ledger R-a) and **stays routed**. Quantify NWPP's side; never reconcile
  CAISO's.
- **VOLL $2,000/MWh is DECLARED INTERIM and is a ledgered rule 21 `[R-DOF]` free parameter.** FERC
  Order 831's $2,000 applies by its own terms to RTOs and ISOs, and NWPP is neither. No participant
  IRP states a $/MWh loss-of-load cost, and no WECC/WRAP planning VOLL is published. The value
  standing in is the **WEIM hard offer cap** (CAISO Tariff §39.6.1) — *the cap of an imbalance market
  that clears ~6 % of footprint energy is not a customer damage function*. It must be declared as
  interim in **every** attestation that reads it, and the pre-declared successor is an LBNL ICE
  derivation on the footprint's own customer mix (routed, `FINDING-nwpp-20` §5). **Never swept
  against a gate.**
- **THE NW↔OR LINK IS A TIER-3 PLACEHOLDER THAT CANNOT BIND** — 43,600 MW, the NWPP-NW zone's own
  nameplate rounded to the nearest 100, registered for a **documented absence** of any published
  limit. The other six path limits are cited WECC paths (Tier-1 Path 35 / Path 16; Tier-2 Path 20 and
  the aggregated Paths 8+6+14). Never tune the placeholder to a price residual (rules 1 / 13 / 14).
- **THE SCORER IS CLOSED TO THIS PROGRAM.** The plan's rubric prohibition was carved exactly once, by
  owner ruling **N11**, for lane NWPP-22 alone — and that lane's branch was then withdrawn as a
  duplicate. **No other lane in this program may touch `scripts/calibration_verdict.py`.**
- **SEASONALITY IS NOT UNIFORM ACROSS THE ZONES, AND THE FLOOR READS ONE SCALAR ANYWAY.** The
  reliability floor reads a single `PLANNING_RESERVE_MARGIN_BY_ISO["NWPP"]` against the footprint
  **coincident** peak — summer in all three years — while the members split
  **8 winter-peaking BAs / 6 summer / 1 flipping (PACW)**. **NWPP-NW peaks in WINTER every year**
  (summer ÷ winter = 0.86 / 0.80 / 0.82) while **NWPP-SNV peaks in SUMMER** at 1.95 / 2.06 / 1.87 ×
  its own winter load, with load correlation **0.048** against NWPP-NW; **NWPP-INLAND mixes both
  regimes inside one zone**, so even a per-zone seasonal PRM would average two regimes there. The
  mismatch is DECLARED at full magnitude on `_nwpp_config`, not softened, and a per-zone seasonal
  requirement is pre-declared lever **NWPP-57** — never an edit to a dict every registered region
  reads.

## Pre-push checklist (STANDING — every session in this lane, before every push)

`.claude/hooks/ruff-prepush-gate.sh` (`PreToolUse` on `Bash|mcp__github__push_files`) refuses a push
whose *own* changed `.py` files fail either gate, and names them plus the fix. It is check-only — it
never edits your tree (rule 27 `[R-PUSH]`). Run the two commands yourself anyway: a hook can be
disabled, a session can run without it, and it deliberately does not gate the whole tree. Run from the
repo root and confirm **exit 0** before staging:

```
uv run ruff format --check .
uv run ruff check .
```

---

## nwpp-41 — 2026-09-19

**NWPP's FIRST KEEPER.** `2026-09-19-nwpp41-coal-taxonomy-own`, bundle
`results/calibration/nwpp41_span_A`, 2023–2025. Promoted on the owner's pre-solve ruling *"Promote
after the C1 fix lands"*. **Determination `NOT-YET` — a keeper is not a calibration**, and NWPP is
additionally PRICE UNSCORED (rubric v3.8), so nothing here certifies a price level, shape or tail.

**One field armed**: `coal_prb_proxy_own_iso`, for NWPP alone in `pipeline/backcast_config.py`. It
closes two defects at one seam, both plumbing, both proven zero-LP before any solve:

1. **C1** — `coal_supply_NWPP.csv` had never been derived, so all 17 NWPP coal plants binned to the
   bare class `COAL`, which the benchmark has no row for (the benchmark passes the EIA-923 row's own
   fuel code to the *same* resolver and itemizes `COAL_PRB`/`COAL_BIT`/`COAL_WC`). The seam also
   corrupted the share denominator, since `_gen_totals` sums the model over *benchmark* keys and so
   excluded the model's whole coal output from its own total (2024 `CC_REGULAR` +3.6 pp → +1.4 pp).
2. **Rule 25** — `_prb_monthly_actuals` pooled `COAL_PLANT_SUPPLY`, **every plant of which is in
   Texas**, so an NWPP plant with no Schedule-2 filing priced against ERCOT's delivered PRB cost
   ($1.818/$1.760/$1.622 per MMBtu) instead of NWPP's own reporters' ($2.463/$2.134/$2.066). Not a
   corner case here: Colstrip and Centralia file no price in any year, 26.7 % of coal MW.

**Rule 14 `[R-ACCURATE]` is the basis, never the residual.** Zero free parameters — the DOF ledger is
3 entries / 3 residual, identical to NWPP-40's, because the flag selects *which measured series* the
proxy pools. Confinement measured: only Colstrip and Hardin move in every year (TS Power also in
2025); non-coal offer max|Δ| **$0.0000000000**, `pmax`/`availability` max|Δ| exactly 0.

**Gates**, against the lane-NWPP-40 control differenced at rule-29(b) form 4, **no control solve**
(G-DRIFT classified the one other config delta, `neiso_coldsnap_derate_dualfuel_unswitched` at its
NEISO-gated default, INERT): **C1 FAIL (5 rows) → PASS** (18/18 all, 14/14 free); C2 PASS; **C4 FAIL**
(coal r .511/.535/.475 → .539/.546/.502); C6 PASS (authorized_price_tuning NONE, verified from
dispatch — the three non-unity-band groups carry zero NWPP energy); C8 PASS (0.0 % forced everywhere).
Basis shrank from `{fuelmix, dispatch_corr}` to `{dispatch_corr}`.

**Both pre-registered predictions landed** (C1 closed, C4 still FAILs). Two unpredicted moves are
**side effects reported, not achievements claimed** (rule 1 — no dispatch mechanism was touched):
C4's r and NRMSE both improved, and reported-only C5a CO2 went −65.9/−58.7/−54.8 % →
−15.1/−23.7/−21.4 % (likely per-class emission-rate coverage restored by the taxonomy fix, since less
coal would push the error the other way; no ablation run).

**C4 ROUTED, not attempted** (owner ruling). Diagnosis: the coal offer stack is bimodal — a $4.50
must-run tranche in the money 100 % of hours against $37.7–42.8 for everything else, versus a $26.15
mean price — so ~90 % of model coal is price-insensitive and ~4,600 MW of available coal sits out of
merit 87 % of hours; availability was measured and ruled out. The measured fleet's midday trough
**deepens** with solar (peak/trough 1.21 → 1.32 → 1.40) where the model reads 1.02. **Successor
blocked on `bin_assignments_NWPP.csv`**, absent for every legacy-bin ISO.

**Still carried, absorbed nowhere**: 2025 coal volume −28.8 % (row SKIPPED on the preliminary EIA-923
vintage; model 27.21 vs 42.26 TWh — the bigger half of C4's cause), energy balance −10.02 TWh vs a
±3.0 tol, the Chief Joseph 2025 pond dual (−325.17 $/kcfs·h for 5,808 h), NWPP-SNV VOLL hours 23+34,
and every NWPP-40 disclosure inherited verbatim.

**Reported and deliberately NOT fixed**: the same PRB-proxy defect reaches MISO (12 plants), PJM (2)
and SPP (3–5); their matrix cells stay `O` (rules 25 / 28(d)).

**Solve**: ONE shard, ONE `--year 2023 2024 2025` invocation, years sequential; the parent ran no LP.
44,960.5 s = 749.3 min = 1.36× NWPP-40, peak RSS 4.78 GiB, no swap. Per-pass ratios are strongly
non-uniform — 2023 P0 0.99×, **2024 P1 2.26×**, **2025 P1 0.90×** — with 2024 P1 the sole outlier at
1.8× 2023 P1's iterations *and* the slowest iterations/s of the six. No mechanism attached.
**Attempt 1 was lost to a platform restart** mid-2025-P1 after ~13 h; reuse was foreclosed (verified
in code), the owner ruled relaunch, and 2023/2024 reproduced to four decimals across attempts.

Records: `docs/records/nwpp/FINDING-nwpp-41-2026-09-19.md`,
`docs/records/nwpp/PRECOMMIT-nwpp-41-2026-09-17.md` (nine addenda),
`docs/records/nwpp/NWPP41-attempt2-solve-log-excerpt.txt`, `scripts/gen_nwpp41_attestation.py`,
`scripts/probes/_nwpp41_coalrank_phase0.py`. Full 36-file bundle recoverable at
`1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d`.

---

## nwpp-42 — 2026-09-20

**PROMOTED. NWPP's keeper is now `2026-09-20-nwpp42-measured-coal-heat`** (bundle
`results/calibration/nwpp42_coalhr_span`), superseding lane NWPP-41, whose three stores were pruned
in this session per rule 35 `[R-PROMOTE]` (a) after the year union `{2023, 2024, 2025}` was
enumerated first (35(b)) and `audit_keepers.py --iso NWPP` passed clean between promotion and prune
(35(e)). Determination **`NOT-YET`** (rubric v3.8, PRICE UNSCORED), unchanged, on `{dispatch_corr}`
alone. Acted on the owner's standing ruling — *"If structural integrity improves but gates regress
that may still be a keeper"* — which this run satisfies on its easier limb: structural integrity
improves **and no gate regresses**.

**THE ARM: `measured_coal_heat_rates=True`, one field on NWPP-41's frozen recipe.** NWPP takes the
legacy aggregate-fleet path (absent from `CAMPD_BINNING_ISOS`, owner ruling N8), which prices coal
on **eGRID's ANNUAL PLANT AVERAGE** `PLHTIAN / PLNGENAN` — an average over every hour the plant ran,
starts and deep part load included. Measured against the plants' own CAMPD-metered steady-state
rates, that estimate is **HIGH at every one of the 12 covered plants** (7,956.4 of 8,104.4 MW =
98.2 % of COAL capacity), cap-weighted **11.868 → 11.066 MMBtu/MWh (−6.8 %)**, and the error is
**not uniform**: Hunter 13.3303 → 10.9688 (1.2153×), North Valmy 1.1537×, Hardin 1.1078×, Wyodak
1.0880× against Colstrip 1.0228× and Jim Bridger 1.0085×. **Rule 14 `[R-ACCURATE]` is the basis,
never the residual.** The structural signature is the tell: the correction is near-zero exactly at
the plants the model already dispatches correctly (Colstrip, measured diurnal peak/trough 1.07,
model 1.00) and largest where it is not (Hunter, measured 1.62, model 1.00) — no single multiplier
stands in for that. Table `data/raw/_processed-legacy/campd_coal_heat_rates_NWPP.csv`, md5
`8dd65f9e73352bcd73ef4f4ea11f35fd`, by the new `scripts/data/derive_campd_coal_heat_rates.py`, NET
basis via the *same* `parasitic_load_factors.parquet` the benchmark's net actual uses. Two declared
departures from the nyiso-89 CT deriver, both on physics, both fixed ex ante: `opTime >= 0.99`
steady-state screen (a coal unit's normal range includes part load) and `primaryFuelInfo` rather
than `unitType` (at Jim Bridger, Naughton and North Valmy the coal and gas-converted units are both
boilers). **Zero free parameters** — DOF 3 entries / 3 residual, identical to NWPP-40/41.
Class-gated to COAL, so it cannot reach a gas unit at a plant that has both (Jim Bridger 8066 has
COAL and ST_GAS rows under one `plant_code`); guarded by
`tests/unit/data/test_measured_coal_heat_rates.py`.

**RULE 36 `[R-YEAR-ISOLATION]` LANDED MID-LANE**, interrupting two span solves that carried the
now-default-off warm-start knobs. Relaunched as **six single-year shards** (three arm, three
control) pinned to `b68673a99926a554d0a9e165f5bd06b890572c02`, composed by
`scripts/probes/_nwpp42_compose_span.py` after it verified all **855** non-year-carried
`scenario_config` fields agree and each leg's gas price matches its own flags. A control solve was
spent — which rule 29(b) normally forbids — because rule 36(e) **withdrew** the knobs' neutrality
claims, so form 4 against the committed keeper could not be relied on for C4, the criterion at
issue. Leg recovery by full SHA is in the FINDING and in `.gitignore`; every shard pushed its FULL
bundle including `dispatch/<year>_P1.parquet`, so the promotion cost **zero re-solves**. The six
shard branches are **NOT merged** (verified: `git merge-base --is-ancestor` answers *not an
ancestor* for all six against `origin/main`) and are **deliberately not deleted** — they hold the
only copy of the per-plant dispatch layer a re-registration needs and of the control legs
entirely, so rule 33(f)(2) does not permit deleting them and 33(f)(4) forbids orphaning the
recovery lines that cite them. **LEG BRANCHES RETIRED (owner instruction, 2026-09-20):** *"No it shouldn't preserve the branches
in the repo. If something needs to be kept it should be done by the main branch and pushed to main.
There is no reason to clutter my repo with old branches."* All nine `claude/nwpp-42-*` leg refs are RETIRED, and
**deletion was attempted and refused** — `git push origin --delete` returns HTTP 403 for every one,
because this session's credential may create and update refs but not delete them and the GitHub
MCP exposes no deletion tool (rule 33(f)(5), which says to say so rather than claim a cleanup that
did not happen). **They need the owner to remove them.** Retired means nothing may depend on them:
the SHAs in `.gitignore` and the FINDING are now a **provenance record, not a recovery
route** (rule 33(f)(4) — say so plainly rather than keep a command that fails), and recovery is
**re-solve only, ~45–90 min of LP per leg**. That costs nothing `main` lacks: rule 31 `[R-RETAIN]`
trigger (i) is satisfied because the owner ruled on promotion, the FINDING carries every number the
lane cites from any leg, the keeper bundle + sidecar + run payload are committed, and the per-plant
D-1/D-2/D-4 diagnostics fall back to that registered payload when `dispatch/<year>_P1.parquet` is
absent. The control legs were never eligible for `main` at all (rule 29(c) forbids a control bundle
reaching it; rule 15 forbids a second registered NWPP run). **The lesson, because it bit twice in
one session:** an unmerged shard branch is NOT durable here — the environment deleted three of them
when the PARENT's PR merged, then the lane branch on its own merge. A lane that needs bytes to
survive lands them on `main` inside the registered keeper bundle before its own PR merges.

**THE GATES, arm minus the paired control. NOTHING REGRESSES.** C1 PASS→PASS (18/18 all, 14/14
free), C2 PASS→PASS, C4 FAIL→FAIL, C6 PASS→PASS, C8 PASS→PASS (0.0 % forced everywhere),
determination unchanged. C4 coal `r` **0.539 / 0.547 / 0.502 → 0.570 / 0.559 / 0.524** and NRMSE
**0.301 / 0.397 / 0.432 → 0.292 / 0.387 / 0.408** — 2023's NRMSE crosses **inside** the 0.30 gate,
leaving that year failing on the correlation floor alone. C4 gas passes all three years in both
legs. Coal volume **39.613 / 27.008 / 27.207 → 41.549 / 27.390 / 28.317 TWh** against a measured
42.27 / 38.30 / 42.26. C2's 2025 coal row −29.3 % → −26.4 % (SKIPPED on the preliminary EIA-923
vintage). Reported-only C5a CO2 −16.0 / −23.8 / −21.5 % → −14.4 / −23.5 / −20.6 %. Hydro **exactly
flat** all three years; footprint total within 0.002 TWh.

**SECOND DELIVERABLE — NWPP's own measurement of the rule-36 artifact, which 36(f) records as
UNMEASURED outside MISO.** The split is clean: **annual class volume moves 0.000 TWh for every
class in every year** (coal included) while the **hourly** allocation moves up to **765.2 / 817.1 /
817.9 MW** (Σ|Δ| 1.516 / 0.915 / 0.698 TWh), concentrated in **hydro and CC_REGULAR** — the
flexible resources whose monthly budgets bind the annual total while leaving within-year placement
free. On the scored criteria the artifact is negligible: the control reproduces NWPP-41's C4 coal
`r` to 0.001, its NRMSE exactly, and its C2 2025 coal row exactly. **MISO measured up to 24.18 TWh
of ANNUAL movement; NWPP measures 0.000** — the two are not comparable and neither generalises.
Practically: **form 4 against the committed keeper is reliable for NWPP.** The same comparison also
shows that the benchmark itself moved between the two registrations (rebuilt `eia923` hashes
differently) and that the movement is immaterial.

**PRE-REGISTERED PREDICTIONS, SCORED INCLUDING THE NEAR-MISS.** Coal rises materially without
closing the gap — held. `r` improves without reaching 0.70 — held in both halves. 2023 is the risk year and may push a C1 row out of band — **not at the gate, but the magnitude moved**: C1 stays 18/18 and the one row that degrades is exactly the predicted one, 2023 COAL_BIT +0.390 → **+2.193 TWh** (+0.330 → +0.996 pp) against a ±8 TWh / ±3 pp band. Net over all nine C1 coal rows: five improve, three unchanged, one degrades. The table also sharpens what is NOT closed — the coal deficit is overwhelmingly a **COAL_BIT** deficit in 2024/2025 (model 7.48 / 6.94 TWh against actuals 12.83 / 18.21, roughly half) and the arm moves those rows by 0.031 / 0.232 TWh, so a heat-rate correction does not reach it. Zero movement outside
coal — held. DOF unchanged at 3/3 — held. **The kill condition** (a 2025 coal move below 0.5 TWh ⇒
inert) **did not fire** (2025 moved +1.110 TWh), **but 2024 moved only +0.382 TWh, below that
line**; had 2024 been the pre-registered kill year this arm would have read inert. Named rather
than glossed, and carried on the keeper's own determination basis.

**CARRIED, ABSORBED NOWHERE.** C4 coal still FAILs against the 0.70 floor — the named driver is the
**bimodal coal offer stack**, whose structural successor is per-plant CAMPD binning, **blocked on
`bin_assignments_NWPP.csv` being absent for every legacy-bin ISO** (the PRECOMMIT's fork (b), taken
deliberately and for that reason). Coal volume still materially short (2025: 28.32 vs 42.26 TWh).
Energy balance −10.02 TWh in 2025 vs a ±3.0 tol. Chief Joseph's pond-balance dual constant at
−325.17 $/kcfs·h for 5,808 hours of 2025 with pond = 0 and spill = 0 — untouched, still the first
cascade-specific question for a successor. C5a CO2 a reported-only FAIL in all three years. Every
NWPP-40 / NWPP-41 disclosure inherited verbatim.

**CROSS-ISO, DELIBERATELY NOT FIXED.** The eGRID annual-average heat rate is the **default for every
legacy-bin ISO**, so the same defect is present wherever `use_campd_bins` is inert — but **nothing
is transferred** (rules 25 `[R-ISO-SCOPE]` / 28(d)): every other ISO's cell stays `U` and each lane
must derive its own table from its own market's CAMPD record.

**PRE-EXISTING, NOT THIS LANE'S.** `results/calibration/caiso279_ablate_dswcouple_span` carries 34
TRACKED files and is a genuine `check_registry_payload_parity.py` RED belonging to the CAISO lane.
22 failures in `tests/scoring` are pre-existing on `main` (confirmed identical with this lane's
changes stashed) and belong to the golden-manifest / forecast-parity lanes.

Records: `docs/records/nwpp/PRECOMMIT-nwpp-42-2026-09-19.md`,
`docs/records/nwpp/FINDING-nwpp-42-2026-09-20.md`, `scripts/gen_nwpp42_attestation.py`,
`scripts/data/derive_campd_coal_heat_rates.py`, `scripts/probes/_nwpp42_compose_span.py`,
`scripts/probes/_nwpp42_leg_check.py`.

---

## nwpp-46 — 2026-09-22 — C4 re-diagnosed; two-sided hydro envelope PROMOTED (KEEPER #4)

**Keeper:** `2026-09-22-nwpp46-hydro-envelope` · bundle `results/calibration/nwpp46_hydroenv_span`
**Owner ruling:** *"Is this a recommended keeper candidate? If so plz promote. If structural
integrity improves but gates regress that may still be a keeper."* — promoted on the **easy
limb**: no gate regresses and no C1 row changed status.

**The main result is a re-diagnosis, not the arm.** The lane was chartered to close C4 coal on the
coal offer stack's vertical extent. NWPP's own data falsified that premise twice, zero-LP:

1. **The "$0.51/MWh shelf" is a fleet MIX artifact.** Per plant, `econlo == econhi == peak`
   **exactly** at all 17 coal plants — `backcast_config.py:2372` merges `_SPP_OFFER_CURVE`, the
   identity (1.0 on every band), for NWPP, while the generic `COAL_BIT` curve is itself sloped.
2. **The correct ladder is 10.4 % and would be inert.** The shared WP-3 construction over 511,855
   steady-state coal unit-hours of NWPP's own CEMS gives `marg` committed 0.821 / econ_low 0.932 /
   econ_high 1.004 / peak 1.029 (econ_high/econ_low 1.077). And it could not bite:
   **NWPP-INLAND / NW / OR each carry exactly TWELVE distinct P1 prices per YEAR** — one per month,
   $0.00 mean within-day swing.

**What C4 is: hydro over-flexibility.** Model hydro runs **114 / 120 / 138 %** of the real diurnal
swing while coal runs 10 / 5 / 4 % and gas 65–69 % (solar and wind match at 1.00; hydro's mean
level is right). On the additive h19−h11 ramp metric hydro's excess explains **69 / 87 / 102 %** of
the coal+gas ramp deficit. Lever (C) closed for free: D-2 reads `COAL forced_twh = 0.0` and D-4
carries no coal row — there is no coal floor.

**The arm:** `hydro_dispatch_envelope` + `hydro_min_flow_floor` — one mechanism, two mirrored
halves (`HYDRO_MIN_FLOW_PERCENTILE = 100 − HYDRO_ENVELOPE_PERCENTILE`), **zero new DOF** (ledger
4/3 residual, unchanged since NWPP-40), **zero code change**, nothing transferred from CAISO.
Ceiling binds h16–h22 (21.7/23.7/23.4 % of hours); floor binds the midday solar belly and overnight
shoulder (10.4/12.9/14.0 %) — **disjoint hours**, the rule-19 evidence they are one family.

**Result.** Gate profile identical to the predecessor (C1 FAIL, C2 PASS, C4 FAIL, C6 PASS, C8
PASS, NOT-YET). C4 improves on both metrics in all three years and **still fails**: `r`
0.605/0.595/0.610 → **0.658/0.617/0.637** against a 0.70 floor; NRMSE 0.260/0.246/0.284 →
**0.244/0.240/0.276**. Coal's diurnal amplitude ratio 0.100/0.052/0.037 → **0.223/0.096/0.089**.

**The pre-registered kill condition was coded and committed BEFORE the first leg landed**
(`scripts/probes/_nwpp46_gates.py` at `9cd108d9`) and does not fire in either direction. The
ex-ante hydro prediction (1.05/1.10/1.16) landed at **1.048/1.107/1.148**.

**Reported, not absorbed.** One ex-ante prediction was **wrong**: 2023 `CC_REGULAR` was predicted to
improve and moved **0.422 TWh further out** — hydro energy was exactly conserved (0.000 TWh), so
there was no released volume to absorb. `r_intra` improves only in 2023 (0.218 → 0.371), is flat in
2024 and **worse in 2025** (0.425 → 0.374): the arm fixed the *size* of the swing more than its
*hour*. 2023 `COAL_BIT` profile `r` 0.756 → 0.723.

**Infrastructure defect fixed, affecting every sharded lane.** `_nwpp42_compose_span.py` copied the
base leg's `meta.shared_inputs` onto the composite, so a year-isolated span pointed at single-year
benchmark frames — unscorable. Caught by `--restore-shared-inputs`, which correctly refused. Proven
safe before adopting (the 3-year frame is the exact row-wise union of the leg frames); no benchmark
re-based.

**G-DRIFT form 4 established mechanically**: a worktree at the predecessor's `ee276d87` plus a diff
of every LP input array — `mc` (646×8760), `pmax`, `pmin`, `heat_rate`, `vom`, `availability`,
`demand`, `unit_ids` all bit-identical. No control solve.

**Carried, absorbed nowhere.** The NWPP-45 C1 demand-basis gap (−9.645 / −12.144 / −9.107 TWh)
remains an **OPEN OWNER DECISION** (`FINDING-nwpp-45` §8); the 2025 energy balance is still
−10.02 TWh; C5a CO2 reported-only FAIL; Chief Joseph's pond dual; Jim Bridger absent from
`thermal_tranches_NWPP.csv`; the NWPP-40/41/42 attestation corrections **still owed**. New:
EIA-930 2025 NWPP hydro carries a **−44,969 MW hour** (does not affect the robust p95 ceiling).

Records: `docs/records/nwpp/PRECOMMIT-nwpp-46-2026-09-22.md`,
`docs/records/nwpp/RESULT-nwpp-46-2026-09-22.md`, `scripts/gen_nwpp46_attestation.py`,
`scripts/probes/_nwpp46_{coal_stack,marginal_hr,hydro_envelope}_phase0.py`,
`scripts/probes/_nwpp46_gates.py`.

---

## nwpp-47 — 2026-09-22 — GRID carried-wind leg (FINDING-nwpp-45 §8, framing 1)

Owner ruled framing 1 (plant-level attribution intake). **Zero-LP finding:** the GRID Desert-SW
subtraction is mostly right. Its coal is Centralia (r 0.9998) and its NW gas is Hermiston, both fleet
plants eGRID hosts elsewhere, so NWPP-45 §5's 12.856 TWh "refutation" is withdrawn. But the PNM leg
**is** GRID's wind (≤ 2 MW every hour), which the pool supply also carries: a 2.07 / 2.17 / 2.00 TWh
double removal. New gated field `nwpp_grid_carried_wind_served` (zero DOF).

**Solve** (three shards, parent zero LP): run `2026-09-22-nwpp-47-grid-wind`. C1 FAIL → **PASS**
(2023 CC_REGULAR −8.641 → −7.213, inside the pre-registered range); C4 still FAIL; determination
NOT-YET on {dispatch_corr} only. No kill limb fired.

**Not closed:** a −7.6 / −10.0 / −7.1 TWh system gap remains. EIA-930 books only 0.53–0.66 of the
CEMS-measured PGE / BPAT / PACW gas; that is framing 2, an open owner decision. **Promotion unruled.**

Records: `docs/handoffs/{FINDING,PRECOMMIT,RESULT}-nwpp-47-2026-09-22.md`,
`scripts/probes/_nwpp47_{attribution,gates}.py`, `scripts/gen_nwpp47_attestation.py`.

---

**Promoted 2026-09-23 (owner ruling):** `2026-09-22-nwpp-47-grid-wind` is NWPP keeper #5; the NWPP-46 predecessor was pruned (rule 35).

## nwpp-49 — 2026-09-24 — RoR split, chain exempt → KEEPER #6

`2026-09-24-nwpp-49-ror-split` (`results/calibration/nwpp49_ror_span`): the NWPP-47 recipe plus
`hydro_ror_split`, with the 27 regulated-chain plants exempt via the new `regulated_chain` classifier
rule. The pre-registered INERT limb fired in every year: hydro intra-day sd ratio 1.075/1.155/1.169 →
1.074/1.153/1.167, because the reservoirs re-absorb the pinned plants' swing. Gates are identical to
NWPP-47 (NOT-YET on {dispatch_corr}); every class moves ≤ 0.011 TWh. Promoted on structure under the
owner's pre-authorization; NWPP-47 was pruned (rule 35). Pondage intake and design are recorded but
not adopted. Records: `docs/handoffs/{FINDING-nwpp-49-pondage-design-2026-09-23,PRECOMMIT-nwpp-49-ror-split-2026-09-24,RESULT-nwpp-49-2026-09-24}.md`.

---

**Promoted 2026-09-24 (owner pre-authorization):** `2026-09-24-nwpp-49-ror-split` is NWPP keeper #6;
the NWPP-47 predecessor was pruned (rule 35).

## r-nwpp — 2026-09-24 — corrected backcast inputs, 2019 + 2021–2025 (registered, promotion unruled)

`2026-09-24-rnwpp-inputs-span` (`results/calibration/rnwpp_span`): the NWPP-49 recipe plus year-matched EIA-860,
measured CT/coal/ST/CC/CHP heat rates, CAMPD short-coal and unit-partial outages, and mid-vintage exit carry.
Offer curves are unchanged. Six year-isolated shards; 2020 is data-blocked (PSEI EIA-930 demand absent).

Zero-LP intake this lane:
* the 17 member EIA-930 extracts and GRID interchange for 2019–22 (2023–25 byte-identical);
* the NWPP 2019/21/22 calibration reference;
* the NWPP measured heat-rate artifacts, re-derived on F2's raw CAMPD.

Result: NOT-YET on {fuelmix, dispatch_corr}.
* C1 CC_REGULAR: 2023 −7.21 → −8.32 FAIL; 2022 −11.23 FAIL. This is the standing gas-short / coal-long demand-basis
  gap, now on a year-correct coal fleet.
* C4 coal r: 0.671 / 0.622 / 0.687 (+0.011 / +0.004 / +0.049). 2019/21/22 pass (0.774 / 0.740 / 0.772).

Records: `docs/handoffs/{PRECOMMIT,RESULT}-r-nwpp-2019-2025-inputs-2026-09-24.md`.

---

**Promoted 2026-09-25 (owner ruling "Yes promote"):** `2026-09-24-rnwpp-inputs-span` is NWPP keeper #7. It covers
2019 and 2021–2025, a superset of the outgoing keeper's {2023, 2024, 2025} (rule 35(c)). The NWPP-49 predecessor
was pruned (rule 35), with `audit_keepers` E1 run before the prune and E13 after it (both PASS).

## nwpp-next — 2026-09-25 — FERC 714 PSEI fill + partial-plant exit carry, 2019–2025 (PROMOTED, keeper #8)

- **Run and determination:** `2026-09-25-nwpp-next-ferc714-partial` is the R-NWPP recipe plus two measured-input
  repairs:
  - the pool member gap guard, filling PSEI's missing EIA-930 demand from FERC 714 reconciled to PSEI's own basis;
  - `partial_plant_exit_carry`.

  NOT-YET on {fuelmix, dispatch_corr}, the same gates as the keeper, and **no gate regresses**.
- **Per year:**
  - 2021–2025 criterion rows are identical to the keeper.
  - 2019 stays within PASS.
  - **2020 is solved for the first time and passes C1, C2, C4 and C8.**
- **Promotion:** promoted on the owner's standing instruction to promote a recommended candidate.
  `2026-09-24-rnwpp-inputs-span` was pruned.
- **Records:** `docs/handoffs/{PRECOMMIT,RESULT}-nwpp-next-ferc714-partialcarry-2019-2025-2026-09-25.md`.

## nwpp-next-2 — 2026-09-25 — PSEI Colstrip double-booking + non-balance repair; hydro cascade 2019–2022 (PROMOTION OPEN)

- **Two arms, both registered:**
  - `2026-09-25-nwppnext2-psei-colstrip` (A) is the keeper recipe on corrected PSEI inputs:
    - PSEI's Colstrip share, which NWMT already books, is removed;
    - PSEI's 2021-08 non-balance demand hours are filled from FERC 714;
    - one member-demand builder now serves the pool total and its zonal regroup.
  - `2026-09-25-nwppnext2h-cascade-2019` (H) is A plus the hydro cascade binding in 2019–2022, with CROHMS coverage
    extended and τ and links frozen (rule 23).
- **Determination:** both read NOT-YET on {fuelmix, dispatch_corr}, the same set as the keeper. 2022–2025 are
  identical to the keeper.
  - **2019:** CC_REGULAR +3.06 → +0.40 TWh.
  - **2020:** CC_REGULAR +3.47 → +2.48 TWh; CT_PEAKER +1.08 → +0.78 TWh.
  - **2020 C4 coal r: 0.720 PASS → 0.691 FAIL.** About −0.010 of that comes from the benchmark correction and
    about −0.018 from the model.
- **Not promoted.** One year-level gate regresses, so the owner's standing instruction does not apply. Arm H is
  recommended, and the promotion is put to the owner (rule 31).
- **Zero-LP findings:**
  - mainstem coupling is not worth an LP (the NWPP-50 ruling stands);
  - the CT_PEAKER shortfall is price/merit formation plus missing standby units;
  - SB-status units are excluded from the fleet while the benchmark counts their output, which is systemic.
- **Records:** `docs/handoffs/{PRECOMMIT-nwppnext2-psei-colstrip-2019-2025,PRECOMMIT-nwppnext2h-cascade-2019-2022,RESULT-nwppnext2-psei-colstrip-cascade-2019-2025}-2026-09-25.md`
  and the four `FINDING-nwppnext2-*` docs.

**Promoted 2026-09-25:** `2026-09-25-nwppnext2h-cascade-2019` is NWPP keeper #9. The owner ruled *"If structural
integrity improves but gates regress that may still be a keeper"*, so it is promoted for structure. The 2020 C4
coal regression (0.720 → 0.691) is reported at full magnitude.
- It covers the full outgoing year union, 2019–2025 (rule 35(c)).
- `audit_keepers` E1 passed before the prune. `2026-09-25-nwpp-next-ferc714-partial` and arm A
  `2026-09-25-nwppnext2-psei-colstrip` were then pruned with `prune_iso_runs.py --force-uncite`, and the audit
  after it passed.

## nwpp-next-3 — 2026-09-25 — plant-basis demand anchor (FINDING-nwpp-45 §8, framing 2) → KEEPER #10

Owner ruled framing 2. New default-off field `nwpp_demand_plant_basis` (zero DOF): each EIA-930 fuel family's
annual energy in the served requirement is moved onto its EIA-923 plant-basis total on its own 930 hourly shape
(wind/solar untouched; 2025 preliminary vintage: coal and gas only). Requirement +4.59 / +7.47 / +5.55 / +5.08 /
+7.73 / +10.40 / +11.83 TWh 2019–2025. Seven year-isolated shards at `dad798cd`, parent zero LP.

Run `2026-09-25-nwppnext3-plant-basis`: NOT-YET on {dispatch_corr} only. C1 FAIL → PASS (CC_REGULAR 2022 −11.23 →
−7.36, 2023 −8.32 → −2.57 TWh); C4 2020 coal FAIL → PASS (0.691 → 0.718); zero regressions. Reported costs:
unserved load up every year (2020 113 → 194 GWh, 2024 13 → 46), gas long in 2020/2024/2025, coal still long 2021–23.

**Promoted 2026-09-25 (owner standing ruling):** keeper #10; NWPP-NEXT-2's keeper #9 pruned (rule 35), audit PASS.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext3-plant-basis-2019-2025-2026-09-25.md`.

## nwpp-next-4 — 2026-09-26 — coal committed band nested on must-run (owner card D3) → KEEPER #11

Phase 0 (zero LP) on lever 1 (C4 coal amplitude) found the flat block. In 2024–25, 84–99 % of coal energy at the
big PacifiCorp and Colstrip plants sat in the fuel-cheap `_mustrun` + `_committed` block. The econ bands above it
are bang-bang: Utah delivered coal roughly doubled 2022 → 2024, so the econ offers sit at $40–48 against model
prices of $17–27. The block was also 2.0× the measured minimum stable load, because the tranche artifact's two
levels (both measured from 0 MW) were stacked.

New default-off field `coal_committed_nested_on_mustrun` (zero DOF): 2,047.9 MW move to the econ band at 9 plants.
Seven year-isolated shards ran at `fac3d392`, parent zero LP. Three legs were relaunched: 2022 was archived before it
solved, and 2025 and 2019 tripped hard-stop thresholds I had mis-scoped (a non-coal unit at 8224, and 2019's
four-unit Colstrip).

Run `2026-09-26-nwppnext4-coal-nested`: NOT-YET on {fuelmix, dispatch_corr} (was {dispatch_corr}). C4 coal r fell
in 6 of 7 years, as predicted before the solve. Regressions: 2019 coal 0.697 FAIL; C1 CC_REGULAR 2020 +9.54 and
2024 +8.48 TWh FAIL; 2020 gas NRMSE 0.303 FAIL. Improved: coal volume (2019 COAL_PRB +4.84 → −0.08; 2021–23
coal-long shrinks). Unserved load unchanged.

**Promoted 2026-09-26 (owner standing structure ruling, rule 14):** keeper #11; keeper #10 pruned (rule 35), audit
PASS. Successor: coal conduct under period fuel-take obligations.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext4-coal-nested-2019-2025-2026-09-2{5,6}.md`.

## nwpp-next-5 — 2026-09-26 — EIA-860 standby (SB) units admitted by status → KEEPER #12

**Lever 1 (coal take obligation), zero LP, negative for C4.** An admissible prior-year contract obligation exists
(NWPP coal is about 100 % contract), but it is a volume lever. Every price-shaped emulation lowers C4 r, and the best
unshaped bracket still fails 2023–25. Owner questions Q1–Q6 are in
`FINDING-nwppnext5-coal-take-obligation-design-2026-09-26.md`.

**Lever 2: new default-off, ISO-agnostic field `admit_standby_units`** (zero DOF), with a matrix row plus a cell in every
shard. It admits Fredonia 607 (NW, 280 MW) and Sun Peak 54854 (SNV, 222 MW) plus about 80–90 MW of small SB units.
The handoff's "598 MW covers 60–92 % of SNV shed" was corrected before the solve: Fredonia is in NW, so SNV gains
222 MW (31–57 %). WECC Path 76 Alturas (300 MW into SNV) is missing from the topology; routed.

Seven year-isolated shards at `19f2eace`, parent zero LP. The 2021 shard failed at container init and was relaunched.

Run `2026-09-26-nwppnext5-standby`: NOT-YET on {fuelmix, dispatch_corr}, unchanged.
- **FAIL → PASS:** C1 CC_REGULAR 2024 (+8.48 → +7.67) and C4 coal 2019 (0.697 → 0.701). Zero PASS → FAIL.
- **Unserved load** falls every year: 33.4 / 193.7 / 110.1 / 73.4 / 21.3 / 45.7 / 8.8 → 15.4 / 118.8 / 73.8 / 37.8 /
  9.0 / 27.1 / 2.6 GWh.
- **Regression:** Fredonia over-runs 2.5–2.9× EIA-923 in 2019 and 2024, because its eGRID HR of 4.918 is clamped to
  the 9.0 floor. The re-derive of the measured-CT artifact population is routed to the owner (rule 23).

**Promoted 2026-09-26 (owner standing structure ruling, rule 14):** keeper #12; keeper #11 pruned (rule 35), audit
PASS.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext5-standby-admission-2019-2025-2026-09-26.md`.

## nwpp-next-6 — 2026-09-26 — WECC Path 76 link + SB-population CT heat-rate re-derive → KEEPER #13

**Two owner rulings, this session.** (1) Rule 23: re-derive `campd_ct_heat_rates_NWPP.csv` with
`admit_standby_units` armed in the fleet union. Zero LP: 86 rows byte-identical, 16 added (Fredonia 607 9.0 floor →
10.413; Sun Peak 54854 13.436 → 12.893). (2) Path 76 "Alturas" (300/300 MW) booked **NW↔SNV**, not OR↔SNV: EIA-930
books the NEVP seam against BPAT (−246…+182 MW) and NEVP has no PACW leg, even though HIFLD shows the Hilltop 230 kV
side as PacifiCorp-owned. New default-off, NWPP-only field `nwpp_path76_alturas_link`, wired at both entry points, with
a matrix row and a cell in every shard. The README §1.3 "not adjacent" claim is corrected.

Two chained arms, 14 year-isolated shards (A at `e29efd5f`, AB at `0a84941d`), parent zero LP.
- **Arm A** (Path 76 only): zero flips. Unserved 15.4/118.8/73.8/37.8/9.0/27.1/2.6 → 4.5/46.6/34.0/7.5/1.5/13.6/1.2 GWh.
- **Arm AB** (+ re-derive): the same unserved figures. Fredonia 2024 1,610 → 670 GWh (EIA-923 554). ONE flip,
  C1 CC_REGULAR 2024 +7.67 → +8.30 TWh (band 8.00; A +0.27, re-derive +0.36): CT energy moving onto an already-long CC
  class. Routed as lever 4.
- Path 76 runs at its rating 83–91 % of hours in both directions, against a measured net flow of 20–28 MW. Stated
  before the solve; not re-rated.

Run `2026-09-26-nwppnext6-path76-ctrederive`: NOT-YET on {fuelmix, dispatch_corr}, unchanged.

**Promoted 2026-09-26 (owner standing structure ruling, rule 14):** keeper #13. Keeper #12 and arm A were pruned
(rule 35), audit PASS.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext6-path76-and-ct-rederive-2019-2025-2026-09-26.md`.

## nwpp-next-7 — 2026-09-26 — lever 1 diagnosis: C1 CC_REGULAR long is coal short (zero LP, no solve)

Zero LP on keeper #13's committed payload, benchmark and the NWPP-NEXT-5 contract census
(`scripts/probes/_nwppnext7_cc_long_census.py`).
- The C1 CC_REGULAR residual mirrors the coal-family residual every year: **r = −0.974** over 2019–2025. The
  all-fossil total is within +2.4 TWh and hydro within ±3 TWh.
- CC is long at SNV/EAST plants in low-gas years. The coal it displaces is Centralia (≈0 in the model Mar–Nov) and
  Colstrip, both 100 % contract with no filed price, plus Utah BIT in 2024–25.
- It does not track hydro years. CC heat-rate coverage is 22/23 plants (Clark missing, and it runs short), so no
  rule-23 re-derive is indicated.
- The open NWPP-NEXT-5 coal take floor would bind 3.8/5.4/7.2/4.0 TWh (A) or 10.2/21.4/9.4/6.6 TWh (B) in
  2019/2020/2024/2025. At a 1:1 bound, A brings every CC year inside ±8 and B over-corrects 2020 to −11.4.
  Neither result may select the estimator (rule 1).
- Lever 1 therefore reduces to owner questions Q1–Q5. Nothing was solved, promoted or pruned; keeper #13 stands.
- Secondary: PGE Beaver 8073 has no CEMS, so it has no benchmark plant row and no measured CC rate (model 2.41 vs
  0.37 TWh in 2020). The benchmark's per-plant CC sum and its classFull disagree by −2.2 to +4.6 TWh.

Record: `docs/records/nwpp/FINDING-nwppnext7-cc-long-is-coal-short-2026-09-26.md`.

## nwpp-next-7 (cont.) — 2026-09-27 — coal take floor (owner rulings Q1–Q5, soft) → KEEPER #14

The owner ruled on the NWPP-NEXT-5 design:
- generalise the yard row, with NWPP added to `COAL_PLANT_GRAIN_ISOS`;
- an annual floor, estimator B net;
- retire the per-hour take-or-pay discounts.

New default-off field `coal_fuel_inventory_take_floor`, with its matrix row and a cell in every shard.
- **Hard floor** (pin `821069f3`): 2020 was infeasible and 2022–24 returned HiGHS Unknown. In each failing year a
  yard's floor was clipped to its ceiling or capacity.
- **Owner ruling: soft floor.** Per-yard shortfall columns (`layout.n_take_slack`) are priced at the yard's own model
  coal fuel price (take-or-pay).
- **Re-solve:** 7 year-isolated shards at `2162cef5`. All passed.

Run `2026-09-27-nwppnext7-coal-take-floor`: **NOT-YET on {dispatch_corr}** (was {fuelmix, dispatch_corr}).
- **C1 FAIL → PASS:** CC_REGULAR 2020 +9.94 → +3.03 and 2024 +8.30 → +4.62 TWh.
- **C4 fixed:** 2020 gas and 2024 coal (r 0.582 → 0.734).
- **C4 regressed:** 2019 gas (0.719 → 0.699) and 2019 coal (0.701 → 0.690).
- **Unchanged:** unserved energy. Hydro is flat.

**Promoted 2026-09-27 (owner standing structure ruling):** keeper #14. Keeper #13 was pruned (rule 35); audit PASS.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext7-coal-take-floor-2019-2025-2026-09-27.md`.

## nwpp-next-8 — 2026-09-28 — monthly pile grain of the coal yard identity (owner cards) → KEEPER #15

**Diagnosis (zero LP).** Keeper #14's C4 misfit was 65–81 % monthly.
- The model swaps coal and gas by season.
- NW delivered gas ran $3.8–5.1/MMBtu in Jan–Mar 2019 against $2.2 in summer, so the LP fuel-switches.
- The annual take floor let the LP bank the whole obligated burn in the dear-gas months.
- If the monthly shape alone were right, every C4 record would clear r ≥ 0.80.

**Owner decision cards:**
- A monthly pile balance, reopening Q2 "annual".
- Flat ratable receipts (C/12).
- Both floor and ceiling at every month-end.

**The field.** New default-off field `coal_fuel_inventory_monthly_pile`: 12 cumulative yard rows. Month 12 is exactly
the annual identity, and there are zero new parameters.

**Solve.** 7 year-isolated shards at `e7478536`. 2019 needed a 180-min re-launch (P0 43 min).

Run `2026-09-28-nwppnext8-coal-monthly-pile`: **NOT-YET on {dispatch_corr}, one record** (was four).
- **C4 FAIL → PASS:** coal 2019 0.690 → 0.733, gas 2019 0.699 → 0.750, coal 2025 0.678 → 0.721.
- **Still FAIL:** coal 2023 0.693 → 0.695. Its phase-0 footprint was 0.1 TWh, and this was predicted.
- **Regression (still PASS):** gas 2025 0.864 → 0.854.
- **Improved:** every other C4 record (e.g. gas 2021 0.757 → 0.854).
- C1, C2, C6 and C8 PASS. Unserved energy is unchanged.

**Promoted 2026-09-28 (owner standing structure ruling):** keeper #15. Keeper #14 was pruned (rule 35); audit PASS.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext8-coal-monthly-pile-2019-2025-2026-09-28.md`.

## NWPP-NEXT-9 — 2026-09-28/29 — measured coal receipts on the monthly pile: REJECTED (keeper #15 stands)

**Census (zero LP).** C4 coal 2023 (r 0.695) comes from a 2023 PacifiCorp coal-supply shortfall.
- EIA-923 Page 5 receipts fell: Bridger 105.1 → 86.6, Hunter 58.8 → 39.2, Huntington 56.0 → 26.5 TBtu.
- December stocks were at record lows.
- Bridger ran ~20 % load Feb–May 2023 while rebuilding its pile. It alone is +2.0 TWh of the Jan–Mar over-burn.
- The candidate "pile ≥ historical minimum" was refuted at phase 0: Bridger went below its prior minimum in 2022.

**Owner card: "Backcast receipts overlay".** New default-off field `coal_monthly_pile_measured_receipts`: same-year
Page 5 receipts replace the ratable C/12 on both sides of the pile. G-DRIFT ALL INERT. 7 shards at `677273fb`.
2025 is byte-identical, as predicted.

**Result: NOT-YET on {dispatch_corr}, 1 → 3 records.**
- C4 coal 2022 0.741 → 0.695 and 2024 0.739 → 0.664: PASS → FAIL.
- C4 coal 2023 0.695 → 0.648.
- C1 coal volume improved: COAL_BIT 2023 +4.73 → +0.72 TWh.
- **Cause:** the LP spends scarcer coal in dear-gas winter months; real operators held stock.

**Owner ruling 2026-09-29: "Reject, keep #15".** The probe was pruned (rule 31 (i)); the matrix cell is R.
Also re-derived the stale `nwpp_plant_basis_energy.csv` provenance hash (only `source_sha256` moved).
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext9-coal-measured-receipts-2019-2025-2026-09-28.md`.

## NWPP-NEXT-10 — 2026-09-29 — EIA-860 exit-month routing of the outage layer → KEEPER #16

**Lever 1 closed (owner card "Close lever 1, pivot").** An inventory-management floor for C4 coal 2023 has no
admissible identification:
- PacifiCorp's per-plant targets (2021 Kaptur study) are redacted in the Utah DPU filings.
- The only public band (2009, "two to three months" at the Utah plants) gives Bridger (+1.98 TWh of the Q1-2023
  over-burn) no number.
- 2023 stocks sat below that band all year.

**Lever 2 root cause (zero LP).** Colstrip 2020 had 5.86 TWh available against 7.94 TWh generated.
- Retired Units 1–2 (2020-01) carry CAMPD post-exit windows (Jan 2–Dec 31) that derated the surviving Units 3–4 bin.
- The survivors' own windows divided by a retiree-inclusive denominator.
- Existing repairs cannot remove this: `fleet_status_scope` and `per_unit_clip` are inert, and the two denominator
  flags reach only 7.55–7.57 TWh.

**The fix.** New default-off field `unit_outage_exit_ym_from_eia860`. It stamps `exit_ym` from EIA-860 and reuses
PJM-NEXT-8's dated-bin accumulator.
- Routing is live only at plants with a stamped row in the year. That guard is needed because Centralia's CAMPD ids
  never match EIA-860, and without it the plant gains a spurious +2.58 TWh.
- Census: only Colstrip 2020 moves, 5.855 → 7.913 TWh.
- G-DRIFT ALL INERT. Seven shards at `0ec8eb79` (the first 2019 shard stalled and was replaced).

**Result: NOT-YET on {dispatch_corr}, still ONE record (C4 coal 2023 r 0.695).**
- 2019 and 2021–2025 are byte-identical to #15.
- In 2020, 11 of 161 records move, all PASS → PASS:
  - C4 coal 0.762 → 0.772;
  - C1 CC_REGULAR +2.22 → +0.75 TWh;
  - C1 COAL_PRB +2.14 → **+4.20 TWh (worse)**.

**Owner card: "Promote on structure".** Keeper #16 `2026-09-29-nwppnext10-exit-month-routing`; #15 pruned (rule 35).
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext10-exit-ym-routing-2019-2025-2026-09-29.md`.

## NWPP-NEXT-11 — 2026-09-29 — zero-LP decomposition of the coal records (keeper #16 stands)

No solve. Everything was read from committed artifacts. Record:
`docs/records/nwpp/FINDING-nwppnext11-coal-c1-c4-decomposition-2026-09-29.md`.

- **COAL_PRB 2020 (+4.20 TWh) is mostly a benchmark effect.** `reconcile_vintage_classes` scales every fossil class
  by one factor (0.87–0.92 in 2019–2024) to match EIA-930 gas + coal.
  - That factor alone accounts for 2.47 TWh.
  - Against raw EIA-923, the model is only +1.73 TWh over: Dave Johnston +0.66, Boardman spring +0.60, Wyodak +0.44.
- **C4 coal 2023 is a real miss, and it is Jim Bridger.**
  - EIA-930 and CEMS agree in shape (r 0.989).
  - Bridger's plant-level r is 0.07. Swapping in its CEMS hourly alone lifts fleet r to 0.84.
  - Annual energy matches (9.19 vs 9.11 TWh), but the timing is inverted. The units held minimum load Feb–May,
    which is fuel conservation; the model burned Jan–Mar.
  - No new public identification exists for that behaviour.
- **Lever 3.** The NWPP merit-guard lay-up companion has only 17 rows (2023–25), and no per-unit merit family exists.
  Boardman (single-unit) has no outage windows at all.
- **Owner cards:**
  - "Fidelity levers": NEXT-12 derives the per-unit merit extract, then tests levers 3 and 2.
  - "Route to scorer lane": cross-ISO CEMS-anchored coal target, in
    `HANDOFF-scorer-coal-reconcile-2026-09-29.md`.

## NWPP-NEXT-12 — 2026-09-29/30 — lay-up guard rejected, lever 2 re-scoped, Boardman membership repair (keeper #17)

Zero-LP record: `docs/records/nwpp/FINDING-nwppnext12-layup-guard-and-coal-availability-2026-09-29.md`.

- **Lever 3, the merit guard: R.** The derived NWPP per-unit merit extract reclassifies 48 windows, all coal.
  - The panel's clearing cost is a fossil-only band ($26–30/MWh in 2020) that excludes hydro and imports.
  - As a result it ranks units, not windows: 24 of 27 windows in unit-years that are out of merit all year are
    reclassified, against 4 of 271 elsewhere.
  - The per-unit crosswalk it rides on also re-routes 2,951 Clark CC windows, a separate question (cell O).
- **Lever 2: mostly a census artifact.** Naughton's and Bridger's "shortfalls" were their gas-converted units'
  generation in the whole-plant 923 total.
  - Coal-only, the gap is 0.04–0.61 TWh/yr, material only at Colstrip in 2022–23.
  - The source is GADS WEFOR × `wefor_multiplier` 0.7, stacked on measured windows, i.e. a double count.
  - Routed to a phase-0 lane: miso-273's relief needs `unit_outage_dispatched_bin_denominator`.
- **Boardman: a membership defect.** The committed extract never scanned facility 6106.
  - `unit_outage_membership_repair` with a new NWPP companion adds its six measured windows.
  - Seven year-isolated shards ran at `0b1d2cfe`. 2021–2025 are byte-identical to #16.
  - Boardman 2020 goes 2.23 → 1.91 TWh against EIA-923 1.63, and its monthly shape now tracks CEMS.
  - 20 of 161 records move, with no status change. C4 gas 2019 0.750 → 0.735 and 2020 0.830 → 0.812 (regressions,
    PASS); C1 COAL_PRB 2020 +1.40 → +1.28 pp.

**Owner card: "Promote + prune #16".** Keeper #17 `2026-09-29-nwppnext12-boardman-membership`. #16 was pruned
(rule 35); `audit_keepers` PASS; promotion completeness OK. Determination unchanged: NOT-YET on {dispatch_corr},
C4 coal 2023 r 0.695.
Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext12-boardman-membership-*.md`.

## NWPP-NEXT-13 — 2026-09-30 — coal WEFOR relief blocked; per-unit attribution (keeper #18)

Zero-LP record: `docs/records/nwpp/FINDING-nwppnext13-wefor-and-perunit-phase0-2026-09-30.md`.

- **Lever 1, coal WEFOR double count: identified, not armable.** On the screened set, W_s 4.0–4.6 % < X_s 16–24 %
  in every year (residual 0). But `unit_outage_dispatched_bin_denominator` is **R** on NWPP: it divides by bins that
  still carry retired exit cohorts (Centralia BW21, Colstrip 1–2), leaving Centralia BW22 250–280 MW available through
  its measured full outages. The screened share inherits the dilution; `wefor_residual_short_screened_coal` → G.
- **Lever 2, Clark CC routing: per-unit crosswalk is right (EIA-860 GT peakers).** Keeper #17's Clark CC was
  available 0.002–0.68 TWh/yr vs 0.43–0.86 TWh generated. Two tranche-deriver repairs (COAL-SUB family token; coal
  fuel guard) make the per-unit tranche artifact correct; Jim Bridger gets a measured coal row (must-run 953.5 →
  351.8 MW).
- **Solve:** seven year-isolated shards at `f2cfda46`, all hard stops PASS. 0 of 161 records change status.
  C4 coal 2023 0.695 → 0.662 (regression), C4 gas 2023 0.844 → 0.771, C4 coal 2024 0.739 → 0.755.

**Owner card: "Promote + prune #17".** Keeper #18 `2026-09-30-nwppnext13-per-unit-attribution`. #17 pruned (rule 35);
`audit_keepers` PASS; promotion completeness OK. Determination unchanged: NOT-YET on {dispatch_corr}, C4 coal 2023
r 0.662. Records: `docs/handoffs/{PRECOMMIT,RESULT}-nwppnext13-perunit-attribution-*.md`.

## NWPP-NEXT-14 — 2026-09-30 — C4 coal 2023 decomposed; two structural repairs built (solve owed)

Zero-LP record: `docs/records/nwpp/FINDING-nwppnext14-bridger-c4-decomposition-2026-09-30.md`.

- **C4 coal 2023's deepening (0.695 → 0.662) is entirely Jim Bridger.** Swapping only Bridger's hourly back to #17
  gives 0.709. With Bridger = CEMS **outside** Feb–May the fleet reads **0.810 (PASS)**; fixing only the closed
  Feb–May window gives 0.698.
- **Why Bridger's Jun–Oct is wrong.** Its must-run fell to the measured 352 MW, so ~6 TWh now rides econ tranches
  that the monthly pile schedules just-in-time: full in Aug at $34, zero in Jul/Sep/Oct at $31–33. Its own 2023
  EIA-923 delivered coal cost ($3.0–4.2/MMBtu, up from $2.3–2.9) sits above summer LMP.
- **The vintage-static tranche hypothesis is a real defect, but not the cause.** The per-unit deriver divided each
  window year by the 2025 nameplate: 46 % of Bridger's 2023 samples exceed 100 % CF, and North Valmy has two units
  over one unit's nameplate. Repair `campd_per_unit_vintage_denominator` (new, default off): Valmy must-run
  40.7 → 24.5 %, Bridger 16.6 → 15.4 %.
- **Lever 2: Clark 2322's CC block is priced at eGRID's 3.007 MMBtu/MWh.** eGRID's heat input covers only the CEMS
  peakers. The block runs 70–75 % CF every hour (3.69 TWh/yr vs 0.43–0.86 EIA-923). Repair
  `cc_subfloor_eia923_heat_rates` (new, default off; CC mirror of SPP-49) gives it its own EIA-923 CC rate,
  9.0–9.6.
- **Captive-mine fuel cost:** design only
  (`docs/records/nwpp/DESIGN-nwppnext14-captive-mine-marginal-fuel-2026-09-30.md`). In 2023 the captive mine was booked
  at $4.21/MMBtu while contract sources ran $2.42–2.62.
- **Coal WEFOR live-capacity sub-flag:** owner authorized a later lane to build it (new gated field; MISO
  byte-identical).
- **Solve NOT run.** This session hit the session-nesting limit (depth 8) and cannot launch shards; the parent never
  solves (rule 32(a)). PRECOMMIT and the seven shard prompts are committed
  (`docs/records/nwpp/PRECOMMIT-nwppnext14-vintage-denominator-2019-2025-2026-09-30.md`,
  `docs/records/nwpp/nwppnext14/shards/`). Pin: `b4e567fb1de9a53146730e0e75f95cb8db505c66`. G-DRIFT: all inert.
  Keeper #18 stands: NOT-YET on {dispatch_corr} under rubric v3.13.
## NWPP-NEXT-14 (solve lane, session 01VuR49n) — 2026-09-30 — Clark CC heat rate + Bridger vintage tranche row (keeper #19)

Zero-LP record: `docs/records/nwpp/FINDING-nwppnext14-bridger-and-clark-phase0-2026-09-30.md`.

- **C4 coal 2023 is Jim Bridger, and at #18 the decisive window is Jun–Oct.** Swapping Bridger to CEMS for Jun–Oct
  alone lifts fleet r 0.662 → 0.821. The Feb–May conservation window alone reaches only 0.697.
  - #18's measured must-run (351.8 MW) left Bridger price-marginal at a delivered-cost offer of $38–51/MWh.
  - Its 2023 burn equals its soft take floor exactly (93.9 TBtu vs CEMS 100.4), and the LP spends that take in
    dear-gas Q1.
  - The measured WEIM prices sit below the offer too.
- **The vintage-static tranche row is real but not the cause.** Its 2023-only form reads a 113.8 % median CF;
  corrected, the must-run moves only 351.8 → 343.3 MW.
- **Clark 2322 CC loaded eGRID 3.007 MMBtu/MWh** (CEMS meters only its GT peakers), so it ran at full availability,
  +2.8–3.3 TWh/yr over EIA-923.
- **Owner cards:** "EIA-923 CC-family HR", "Both" (vintage fix now, captive-mine research next), and
  "New sub-gate, default off" (lever 3 live-capacity denominator).
- **Built:**
  - `eia923_cc_family_heat_rates` (new, default off; population rule, zero DOF);
  - `campd_unit_fuel_split` composed with per-unit attribution (`-perunit-fuelsplit-` companion).
- **Solve:** seven year-isolated shards at `54edd9e3`, all hard stops PASS. Clark CC 3.69 → 0.41–1.21 TWh/yr
  (EIA-923 0.43–0.86). 75 of 161 records move, 0 change status. C4 coal 2023 0.662 → 0.670.
- **Regressions (reported):** C1 CC_REGULAR 2021–23 under-dispatch grows (−1.87 → −2.15, −3.89 → −4.06,
  −1.37 → −1.84 TWh), CT_PEAKER 2025 +2.48 → +2.81, COAL_BIT 2023 +5.04 → +5.20.

**Owner card: "Promote + prune #18".** Keeper #19 `2026-09-30-nwppnext14-clark-hr-bridger`. #18 pruned (rule 35);
`audit_keepers` PASS; promotion completeness OK. Determination unchanged: NOT-YET on {dispatch_corr}, C4 coal 2023
r 0.670. Records: `docs/handoffs/{FINDING,PRECOMMIT,RESULT}-nwppnext14-*.md`.

**Reconciliation with the parallel NEXT-14 lane (above; PR #6935).** Two sessions ran the same handoff. The other built
`cc_subfloor_eia923_heat_rates` and `campd_per_unit_vintage_denominator` but could not solve (nesting limit). Owner
card "Keep #19; retire dup Clark field":
- `cc_subfloor_eia923_heat_rates` is DELETED (rules 19 / 26); it duplicated the solved `eia923_cc_family_heat_rates`.
- `campd_per_unit_vintage_denominator` stays default-off as NEXT-15's replacement candidate for the fuel-split
  composition, because it also repairs North Valmy.

## NWPP-NEXT-15 — 2026-10-01 — vintage-denominator arm solved (not promoted); captive-mine and live-denominator built

- **Solve:** NEXT-14's PRECOMMIT arm — #18 + `campd_per_unit_vintage_denominator` + the since-deleted
  `cc_subfloor_eia923_heat_rates` — 2019–2025, 7 year-isolated shards at `b4e567fb`, solved off-pin.
- **Vs main's keeper #19** (the parallel lane, merged first in PR #6951): identical determination, 0 status
  differences. C4 coal 2023 r 0.670 in both. Other C4 records within ±0.007 (4 higher, 7 lower); C1 closer in 25 / farther
  in 11.
- **Owner (2026-10-01): supersede only if better.** It is not decisively better, and the two Bridger fixes are
  alternatives. So it is **not promoted**, and NEXT-16 solves the **combined run** (keeper #19, fuel-split → vintage
  denominator) on pin. Record: `docs/records/nwpp/RESULT-nwppnext15-vintage-denominator-2019-2025-2026-09-30.md`.
- **Captive-mine marginal fuel.** Phase 0 is in `PHASE0-nwppnext15-captive-mine-2026-09-30.md`; the identification rule
  was fixed before the census (one code-table erratum). Effectively a Jim Bridger lever: 2023 gap +$0.92/MMBtu, 2022
  −$0.13. Owner card "Build, no threshold" → `coal_captive_marginal_fuel_price` (default off, zero LP, not solved).
- **Live-capacity denominator:** `unit_outage_dispatched_bin_live_denominator` (default off, zero LP, not solved).
  Centralia 1,340 → 670 MW and Colstrip 2,094 → 1,480 MW in 2021, 2022 and 2025; 2020 still diluted. Coal-only
  `wefor_residual` scoping sits behind the same flag. It does not reach Bridger.
- **Off-pin libraries** (owner card "Merge now, fix recipe"): `pip install -e .` in shard prompts pulls highspy 1.15.1
  etc. against the pins. Main's #19 and today's NYISO keeper are off-pin too. NEXT-16 installs from `requirements.txt`.

## NWPP-NEXT-16 — 2026-10-01 — combined run promoted (keeper #20); captive-mine and live-capacity WEFOR rejected

- **Solve:** three arms on keeper #19, 2019–2025, 21 year-isolated shards on pin `33014efc` (requirements.txt libraries).
- **C → keeper #20** `2026-10-01-nwppnext16c-combined-vintage` (owner card "Promote C, prune #19"): `campd_unit_fuel_split` →
  `campd_per_unit_vintage_denominator`. 0 status changes vs #19; C4 within ±0.008; coal 2023 r 0.669 (still FAIL). Also
  fixes North Valmy's must-run. The per-unit fuel-split composition is deleted (rule 26). #19, D, E pruned (rule 35).
- **D (captive-mine price):** C4 coal 2023 0.669 → 0.650; Bridger's extra energy lands in Nov–Dec, not Jun–Oct. R.
- **E (live-capacity screened-coal WEFOR):** 4 new C4 FAILs (coal 2019/2022/2025, gas 2019). R.
- **Correction:** #19 was on pin (its run_configs record the pinned libraries); the off-pin note belonged to NEXT-15's run.
- Record: `docs/records/nwpp/RESULT-nwppnext16-combined-captive-live-2026-10-01.md`. Next: Bridger seasonal offer (NEXT-17).

## NWPP-NEXT-17 — 2026-10-01 — phase 0 only: Bridger's trough is a flat hydro-set price (no solve; lever redirected)

- **Zero LP** on keeper #20's 2023 leg (`a54c7b97`). Bridger's take floor is one −$5.56/MWh dual Jan–Oct. Its effective
  offer (~$33–36) sits $1–10 above a NWPP-EAST price that is **flat within each month** (Jul–Oct P10–P90 spread $1–4).
- The north zones clear at one price, the **monthly hydro water value**. Within-day and between-day SD are ~1/10 of WEIM
  PACE/IPCO/BPAT. Jul and Oct means are $15–30 low. At measured prices the keeper offer recovers July. Aug–Oct still
  under-run by 0.4–0.8 TWh/month.
- The Oct–Dec captive-mine spike ($3.7 → $5.3/MMBtu, Jim Bridger Mine) is real and small (~0.1 TWh).
- Owner card: **"Redirect to hydro"**. A Bridger offer change would be fitted to a price error (rules 1, 13). Next: NWPP hydro
  within-month freedom, phase-0 design (NEXT-18). Record:
  `docs/records/nwpp/FINDING-nwppnext17-bridger-price-formation-phase0-2026-10-01.md`.

## NWPP-NEXT-18 — 2026-10-01 — phase 0 only: hydro has no excess within-month freedom (hydro-period lever closed for NWPP)

- **Zero LP** on keeper #20's 2022–2025 legs. The water value sits on the Columbia/Snake chain (99 % of interior hydro
  hour-MW, led by Grand Coulee), not on small reservoirs.
- Against CROHMS: the model moves **less** energy between days than measured (ratio 0.75–0.90; Grand Coulee 0.71–0.83).
  `hydro_budget_period_by_instrument` would move NWPP further from data. Not armed, no registry entries (rule 13).
- Within the day the model over-shapes (0.98–1.41×; Grand Coulee 1.44–1.72×). That is an hourly object, not a lever on its own.
- The flat price is a flat monthly gas stack (+$1–5 when the envelope binds) plus a fixed interface. Measured NW prices
  track CAISO/the West (between-day r 0.72–0.90).
- Owner card: **"Both, one census"**. NEXT-19 runs a zero-LP split of measured price variance into gas-daily and
  interface parts, then picks the lever. Record: `docs/records/nwpp/FINDING-nwppnext18-hydro-within-month-phase0-2026-10-01.md`.

## NWPP-NEXT-19 — 2026-10-02 — census + gas-daily arm (R); priced interface wired, held for two registry fixes

- **Zero-LP census.** Henry Hub daily explains ~0–5 % of NW within-month between-day price variance (Jan 2024 aside).
  CAISO coupling adds 0.11–0.43 R² beyond gas. PACE/IPCO carry CAISO's diurnal shape; BPAT's weak link is real, not a
  clock artifact. The measured price lifts the 2023 Jun–Dec coal shape (+0.10 r) but not 2024/25; CT energy rises 2–2.7×.
  No admissible daily NW gas hub series exists. Record: `docs/records/nwpp/FINDING-nwppnext19-price-census-phase0-2026-10-02.md`.
- **Arm G (`gas_daily_shape`, 7 shards, clean A/B on keeper #20's code):** 0 status changes. C4 coal 2023 0.669 → 0.677,
  still a FAIL. **C4 gas r falls in every year (−0.019 to −0.147; 2019/2020 at 0.703/0.702)**, all between days.
  CT +0.03 to +0.54 TWh. Owner card: **"Reject, keep #20"** → `gas_daily_shape` R for NWPP.
  Record: `docs/records/nwpp/RESULT-nwppnext19-gas-daily-shape-2026-10-02.md`.
- **Priced interface wired, default-off:** `NWPP_external` node, links derived from the seam limits, and a refusal of empty
  priced builds (these used to zero interchange silently). Not solved. The registered CAISO seam uses a gross-load shape
  (within-day r vs CAISO RT 0.08 by 2025; net 0.62). The WECC_CAN anchor (peak-only Mid-C) sits $12–38 above BPAT,
  $170 in 2022. Owner card: **"Fix both, then solve"** (NEXT-20).

## 2026-10-02 — closeout-B W0 phase 3 fix-2: keeper 2026-10-02-w0-nwpp-fix2, NOT-YET → NOT-YET

**What changed.** The nwpp-next-16c combined-vintage recipe (`nwppnext16c_span`) was re-solved one year per shard (rule 36), plus the ten W0 EIA-860 settlement backcast defaults (owner ruling R-2; PRECOMMIT `docs/records/governance/closeout-2026-10/PRECOMMIT-closeout-b-w0-phase3-2026-10-02.md`). The dispatched-bin denominator is LIVE for NWPP, in its live-roster form (#7047/#7049). Zero DOF. Every leg solved at `25da6022` (fix-2) on highspy 1.14.0 (locked).

**2019 re-solve.** The 2019 leg was first kept at `306f2c00` under the byte-inert proof. Preflight 0d refused it: the leg records `unit_outage_dispatched_bin_live_denominator=False`, a rule-26-deleted field that NWPP owns, so False is not an inert value and the replay cannot reproduce it. 2019 was re-solved at `25da6022`. That supersedes the NWPP row of `W0-phase3/KEPT-LEG-INERT-PROOF-2026-10-02.md`. Solve times: P0 2,622 s and P1 4,004 s, single-threaded; memory peak 6.06 GiB.

**Scores.** The ISO stays NOT-YET → NOT-YET.
- fuelmix moves FAIL → PASS: 2025 CC_REGULAR goes +9.60 → +7.91 TWh.
- price_mean, price_shape and dispatch_corr still FAIL. price_tail is SKIPPED.

| C3a vs RT | 2023 | 2024 | 2025 |
|---|---|---|---|
| Before (nwpp-next-16c) | −21.4 % | −27.7 % | +2.6 % |
| After (W0 fix-2) | −23.1 % | −30.7 % | −4.6 % |

2019–2022 have no measured LMP reference on disk, so C3a is UNSCOREABLE there.

- **Data drift (labelled, not W0):** the 2025 injected must-run (biomass and OTHER) is +1.5 TWh above the incumbent's. The incumbent carried a partial 2025 EIA-923; the current data has the complete year.
- **Census (in-bundle `fleet_census_<y>.json`):** total thermal summer reads −4.6 to −8.6 % against EIA-860 in every year (winter −10.0 to −20.6 %), OUTSIDE.
- **Unserved energy:** 2019 32.1 MWh, 2024 919 MWh.

**Bench parts kept at the pre-W0 render (desk ruling "Keep old figures, fix later", 2026-10-02).** The promotion re-render moved the benchmark's `classFull` actuals slightly, because the footprint follows the W0 roster: most classes move about −0.1 % in 2019, and CT_CHP goes 0.42 → 0.52 TWh. `data/raw/reference/nwpp_plant_basis_energy.csv`, the `nwpp_demand_plant_basis` anchor that this keeper solved on, is derived from those parts. The parts therefore stay at main's render, so the CSV, the keeper and `test_artifact_matches_bench_parts` stay consistent. **Follow-up (chartered):** decouple the anchor from roster-dependent parts, then re-derive it and re-solve NWPP.

## NWPP-NEXT-22 — 2026-10-03 — measured seam headroom; keeper 2026-10-03-nwpp-next-22b-w0 (priced interface promoted), NOT-YET → NOT-YET

**What changed.** The priced interface is promoted:

- `reference_price_interface` + `priced_interchange`: the NEXT-20/21 seams.
- `nwpp_seam_measured_limits` (new, default off): each priced seam is capped at its measured hourly operating limit.
  - CAISO_COI: CAISO's MALIN500_ISL + CASCADE_ITC OTC, or 2/3 × BPA's COI limit before 2023-06-19.
  - WECC_CAN: BPA's BC Intertie limit, from the new intake `data/raw/nwpp-intertie-otc`.
  - CAISO_NEVP keeps its registered 1,933 MW.

It was solved on the W0 fix-2 keeper's recipe, seven shards at `2b8da72a` (rule 36). Zero new DOF.

**Owner cards:**

- "CAISO share + BPA BC" (phase 0).
- "Promote as keeper #21". The first run, on keeper #20 at NEXT-21's pin `a5a72ec0`, was refused by `promote_keeper.py` preflight 0d: its recipe does not replay at HEAD.
- "Re-solve on W0 basis".

**Structure.** Every priced seam has the measured sign and r > 0 (NEVP 2019, the near-zero leg, is exempt). The caps hold to 0.0 MW. D-2 and C6 PASS. D-1 failures fall 20 → 14.

Summed priced-seam export, TWh, 2019 … 2025:

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| this keeper | 22.9 | 27.8 | 27.6 | 26.5 | 28.2 | 34.4 | 19.0 |
| NEXT-21, uncapped | 27.7 | 33.3 | 35.2 | 32.7 | 30.2 | 36.8 | 17.1 |
| measured | 6.7 | 18.4 | 20.7 | 21.1 | 18.2 | 18.7 | 15.2 |

**Scores against the W0 keeper.** NOT-YET → NOT-YET, and failing records go from 5 to 10.

Regressions, at full magnitude:

- **fuelmix PASS → FAIL.** CC_REGULAR 2019 +1.73 → +12.69 TWh; 2024 +7.83 → +15.39; 2025 +7.79 → +8.74.
- **C4 gas PASS → FAIL.** 2019 r 0.753 → 0.661; 2023 0.787 → 0.538; 2024 0.900 → 0.796.
- **C3b 2024.** 0.718 → 0.789.

Gains:

- **C4 coal 2023 FAIL → PASS** (0.638 → 0.770). Coal r rises in every year.
- **C3a.** 2023 −23.1 → −10.4 %; 2024 −30.7 → −27.1 %; 2025 −4.6 → −0.4 %.
- **C3b.** 2023 0.318 → 0.216; 2025 0.180 → 0.127.

**Root cause of the regressions.** COI still exports 2.6–5.8× measured in 2023–25. Gas fills the excess, and NW gas follows CAISO's net-load shape. This is the price-level gap FINDING-nwppnext22 §D routed: the NW price sits below the MALIN anchor. **That is NEXT-23's lever.**

**Bench parts** stay at main's render under R-28, as #7076 did. **Prune:** `2026-10-02-w0-nwpp-fix2` / `w0_nwpp_span`.

Records:

- `docs/records/nwpp/FINDING-nwppnext22-seam-headroom-2026-10-02.md`
- `PRECOMMIT-nwppnext22-seam-headroom-2019-2025-2026-10-02.md`
- `RESULT-nwppnext22-seam-headroom-2026-10-02.md`

## closeout-nwpp-anchor — 2026-10-03 — roster-free plant-basis anchor → KEEPER `2026-10-03-closeout-nwpp-anchor-roster`

**Owner ruling R-48: "Promote on structure."** Bundle `results/calibration/closeout_nwpp_anchor_span`, 2019–2025.
It is the NEXT-22b keeper's recipe replayed unchanged, with all seven legs solved at `dad1205a` (main after PR #7103).

**What changed.** The `nwpp_demand_plant_basis` anchor (`data/raw/reference/nwpp_plant_basis_energy.csv`) is now
derived from EIA-923, CAMPD and EIA-930 directly. It uses the bench's own `classFull` construction, but on a
roster-free plant → class map: the EIA-860 footprint, with each plant taking its dominant EIA-923 class.

**Why.** The old derive read the rendered bench part. That part's class map is the keeper's fleet, so the W0
roster moved the anchor at promotion (R-28). Rebuilding with the fleet map reproduces the W0 parts exactly.

**Size of the change.** COL, NG and OTH move 0.002–0.126 TWh per year. The largest move is 2019 COL +0.126, from
Naughton 4162: the fleet types it ST_GAS, while its EIA-923 filing records coal. The net anchored requirement
moves by at most 0.0054 TWh per year. No config key moved. SolveEpoch 2026-10-03a re-keys backcast NWPP.

**Scores against the NEXT-22b keeper.** NOT-YET → NOT-YET, with zero record flips. The largest move on any record
is 0.010 TWh.

| reading | NEXT-22b | this keeper |
|---|---|---|
| failing criteria | fuelmix, price_mean, price_shape, dispatch_corr | same |
| FAIL records | 10 | 10 |
| C1 CC_REGULAR 2019 / 2024 / 2025 | +12.65 / +15.39 / +8.86 TWh | +12.66 / +15.39 / +8.86 |
| C3a 2023 / 2024 / 2025 (vs WEIM ELAP) | −10.4 / −27.1 / −0.4 % | identical |
| C4 coal 2023 | r 0.770 PASS | r 0.771 PASS |

2025 carries the EIA-923 data-drift label: the bench is on the Final vintage, while the completeness part still
marks it preliminary, so the anchor writes COL and NG only.

**Bench parts** stay at main's render (R-28). The anchor no longer reads them.

**Prune:** `2026-10-03-nwpp-next-22b-w0` / `nwppnext22b_span`.

Records:

- `docs/records/nwpp/FINDING-closeout-nwpp-anchor-2026-10-03.md`
- `PRECOMMIT-closeout-nwpp-anchor-2026-10-03.md`
- `RESULT-closeout-nwpp-anchor-2026-10-03.md`

## NWPP-NEXT-23 — 2026-10-03 — COI export leg on CAISO's PNW delivered-cost basis → KEEPER `2026-10-03-nwpp-next-23-coi`

**What changed.** The anchor keeper's recipe plus one new key, `nwpp_coi_pnw_delivery_basis`. The priced COI seam's
NW→CA export bands now pay CAISO's registered PNW delivered-cost basis, `CAISO_IMPORT_DELIVERY_BASIS["PNW_midC"]`: 5 %
loss and a $5 wheel, applied as `(band − 5) / 1.05`. That replaces the symmetric 3.0 hurdle. Zero DOF. Seven
year-isolated shards at `33dc5647`.

**Why.** Phase 0 was zero LP (`FINDING-nwppnext23-price-level-phase0-2026-10-03.md`). In the keeper's COI export
hours, 60–75 % of the anchor-minus-NW gap is the **measured** MALIN − NW spread (+$9–12), so it is not a model price
error. The NWPP side had taken 3.0 from CAISO's inactive `WECC_PNW` interface, while CAISO's active ladder prices the
same corridor on hub + loss + wheel. Rule 19 calls for one physical path with one basis. Owner cards: "Solve H2 PNW
basis", then "Promote after anchor lane".

**Scores against the NEXT-22b / anchor keeper.** NOT-YET → NOT-YET, 10 → 10 FAIL records, zero flips.

| reading | keeper | this keeper |
|---|---|---|
| COI net export 2019 / 2023 / 2024 / 2025 (measured 7.03 / 1.13 / 2.15 / 3.03) | 13.56 / 6.57 / 12.42 / 9.03 TWh | 11.75 / 4.95 / 10.46 / 6.91 |
| C1 CC_REGULAR 2019 / 2024 / 2025 | +12.65 / +15.39 / +8.86 TWh | +11.94 / +14.80 / +8.02 |
| C3a 2023 / 2024 / 2025 | −10.4 / −27.1 / −0.4 % | −11.6 / −27.9 / −1.6 % (regression 0.8–1.2 pp) |
| C3b 2023 | 0.216 | 0.225 |
| C4 gas 2019 / 2023 / 2024 r | 0.661 / 0.538 / 0.796 | 0.657 / 0.533 / 0.791 (NRMSE better) |
| C4 coal | PASS all years | PASS all years |
| BC export 2024 / 2025 | 12.90 / 4.37 TWh | 13.27 / 4.90 |

**Open object.** The residual over-export is the economic **depth** of COI, not the hurdle. Measured CISO-leg flow
saturates at about 600–800 MW at any spread, while the measured caps are 2,800–5,100 MW (FINDING §E).

**LIVE data drift after the legs, routed to NEXT-24:**

- #7134 coal stocks 2015–17 (`9f2fe6df`);
- SolveEpoch 2026-10-03b, NWPP 2019–22 nuclear monthly CF rows.

**Prune:** `2026-10-03-closeout-nwpp-anchor-roster` / `closeout_nwpp_anchor_span`.

Records:

- `docs/records/nwpp/FINDING-nwppnext23-price-level-phase0-2026-10-03.md`
- `PRECOMMIT-nwppnext23-coi-pnw-basis-2019-2025-2026-10-03.md`
- `RESULT-nwppnext23-coi-pnw-basis-2026-10-03.md`

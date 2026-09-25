# NWPP calibration log

Per-region continuation of `docs/calibration-log.md` (frozen archive, entries through 2026-07-19) for
the **Northwest Power Pool / Western Power Pool footprint** — a **pool of ~17 balancing authorities**
(BPAT PACE PACW PGE PSEI AVA IPCO NWMT CHPD DOPD GCPD SCL TPWR AVRN GRID WAUW NEVP), NERC WECC.
**NWPP is neither a balancing authority nor an ISO**, the first such region in this repo; every name
downstream still says "ISO". Program: `docs/multi-iso/nwpp-addition-plan-2026-09.md` (charters, cards,
wave graph, lane table); desk ledger `docs/handoffs/nwpp-desk-ledger-2026-09.md` — **the ledger wins
where the two diverge**; Phase-0 census `docs/multi-iso/nwpp-data-audit.md`.

Entries are appended **verbatim** by the NWPP ADDITION DESK from each lane's FINDING `## Log entry`
section (plan §8.0 rule 1 — **a lane never writes this file**). Newest last.

Lever queue: `docs/mechanism-testing-matrix.md` §5.9; cell verdicts
`docs/codebase-site/data/mechanism-matrix/NWPP.js`.

---

## Lane state at file creation (2026-09-14, lane NWPP-35)

**No keeper exists.** NWPP was registered on 2026-09-14 by lane NWPP-20
(`docs/handoffs/FINDING-nwpp-20-2026-09-14.md`), so
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
  (`docs/handoffs/FINDING-nwpp-13-2026-09-13.md`). Gate D3 — reconciliation against the independent
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

Records: `docs/handoffs/FINDING-nwpp-41-2026-09-19.md`,
`docs/handoffs/PRECOMMIT-nwpp-41-2026-09-17.md` (nine addenda),
`docs/handoffs/NWPP41-attempt2-solve-log-excerpt.txt`, `scripts/gen_nwpp41_attestation.py`,
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

Records: `docs/handoffs/PRECOMMIT-nwpp-42-2026-09-19.md`,
`docs/handoffs/FINDING-nwpp-42-2026-09-20.md`, `scripts/gen_nwpp42_attestation.py`,
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

Records: `docs/handoffs/PRECOMMIT-nwpp-46-2026-09-22.md`,
`docs/handoffs/RESULT-nwpp-46-2026-09-22.md`, `scripts/gen_nwpp46_attestation.py`,
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

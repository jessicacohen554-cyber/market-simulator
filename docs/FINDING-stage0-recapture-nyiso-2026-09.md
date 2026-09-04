# FINDING — Stage-0 golden re-capture: NYISO (owner ruling R-AF, board X-2) — the ruling's keeper moved TWICE during the dispatch, the first capture was silently contaminated by a newer measured input its own oracle could not see, and the correctly-labelled re-capture PASSES

**Session `claude/stage0-recapture-nyiso-yqp94v`, 2026-09-04.** Two keeper
re-solves at HEAD with determinism pinned, run strictly sequentially. Follows the
recipe `docs/FINDING-stage0-capture-caiso-nyiso-2026-09.md` (§1, §4) and
`docs/FINDING-stage0-capture-miso-2026-09.md` (§2 schema-v2 invariant +
merge-base hazard). **No keeper shard, marker, matrix shard, registry, freeze
file or `program-status.json` edit; no determination changed; no workflow
created; no dashboard registration** (standing reading R-L: goldens are NEVER
dashboard-registered).

## 0. Headline

| ISO | Provenance run | Span solved | Fidelity oracle | Golden state |
|---|---|---|---|---|
| **NYISO** | `2026-09-04-nyiso-186-astoria-identity` | 2023–2025 | **PASS** — 282 flags identical, **0 HEAD-only keys**, 0 drift | **CURRENT** |

**Stage-0 coverage: 4 current / 3 stale → 5 current / 2 stale.** Current =
{ERCOT, ERCOT\_\_carveout-2023, NEISO, PJM, NYISO}; stale = {CAISO, MISO},
**both stale by design under R-AF**. `scripts/check_golden_manifest.py` exits
**0**; the NYISO entry reads *"provenance run registered, golden CURRENT"*.

**THE RULING'S KEEPER WAS RE-KEYED TWICE, BOTH TIMES BY THE OWNER.** R-AF as
dispatched named `2026-09-02-nyiso-177-vintage-matched`. It was already
superseded at the session pin, and superseded again before the first capture
finished. The dispatch's own guard — *"if it is no longer 177, STOP and report
… do not chase a moving target"* — fired correctly the first time and was
honoured; the second move was caught only after the fact, by the audit in §2.

## 1. THE SUBSTANTIVE FINDING — the CAISO §1 hazard has an INVERSE, and this capture walked into it

The CAISO/NYISO lane established that a keeper mechanism whose measured input is
**missing** can degrade silently to a fitted scalar while still recording its
flag as armed, and that the fidelity oracle — which compares *recorded flag
keys* — cannot see it (its §1). **This session hit the mirror image: a measured
input that arrives EARLY, ahead of the keeper label that authorises it.**

The NYISO lane promoted twice inside two hours:

| UTC | commit | event |
|---|---|---|
| 07:26:01 | `1fe734bb` | nyiso-**185** `family-hr` PROMOTED |
| **08:20:50** | **`2ba0a29b`** | **nyiso-186 re-derives `egrid_identity_heat_rates_NYISO.csv`** (1 row → 2) |
| 08:31:16 | `8a18e9e1` | **the session pin** — shard still reads 185, artifact already 186's |
| 08:45:41 | `dd36b22d` | nyiso-**186** `astoria-identity` PROMOTED |
| 09:11:00 | — | first capture launched, believing 185 live |
| 09:24:07 | — | first capture completes, **oracle PASS** |

The artifact landed **ten minutes before the pin**. The first capture therefore
ran **keeper 185's config flags against keeper 186's measured input**:

| | rows in `egrid_identity_heat_rates_NYISO.csv` | identity HR applied to |
|---|---|---|
| at 185's promotion (`1fe734bb`) | 1 | 1 plant |
| after 186's derive (`2ba0a29b`) | **2** | — |
| **what capture 1 actually used** | **2** | **2 plants** (log: *"5 generator(s) across 2 plant(s)"*) |

**The fidelity oracle passed it anyway** — 280 flags replayed identically, 0
drift — because `egrid_identity_heat_rates` reads `True` in both 185 and 186.
The flag is unchanged; only the data behind it moved. This is exactly the blind
spot the CAISO lane named, reached from the opposite direction, and it is why
capture 1 was discarded rather than committed under a corrected label.

**The two hazards share one root cause and one fix.** CAISO's: input absent,
flag armed. This one: input newer than its label, flag armed. In both, the
oracle's evidence base (recorded flag keys) is orthogonal to the thing that
changed. The CAISO lane's proposed fix — assert the replay's `resolved_inputs`
against the keeper's — **would not have caught this one either**: the eGRID
identity artifact is not in `resolved_inputs` at all (§3 confirms all six
recorded keys MATCH, on both the contaminated and the clean run). Closing this
class needs `resolved_inputs` rows for the *derived-artifact* inputs
(`egrid_identity_heat_rates`, `egrid_family_heat_rates`, the `campd_*_params`
family), carrying a content hash — not just the raw-file inputs it records today.

### 1.1 The one piece of luck, measured rather than assumed

nyiso-186's own registry `definition` states it is *"the nyiso-185 keeper recipe
(replay, **ZERO scenario_config changes**) with the re-derived
`egrid_identity_heat_rates` artifact"*, and its shard records *"(G-DELTA
computed: empty) and exactly ONE artifact row"*. If that is exact, capture 1 —
185's config + 186's artifact — **is** a 186 golden wearing the wrong label.

That was an inference, so it was **tested rather than banked**: capture 1's ten
`content_hashes` were preserved before the re-run overwrote the bundle, and
compared against capture 2's under the manifest's own
`sha256-of-canonical-column-float64-bytes` scheme.

**Result: 10 of 10 IDENTICAL, 0 differing.**

So the inference was right, and the committed golden would have been *numerically*
correct either way. That is not a reason to have committed capture 1: the
identity was unknowable at the time without this comparison, and a golden whose
correctness rests on an unverified claim about another run's config delta is not
a baseline. It is recorded here because it independently **confirms 186's
zero-config-delta claim by solve**, which no other artifact does.

## 2. What was captured

`scripts/capture_keeper_goldens.py --iso NYISO --stage-tag perfb-stage0`, in
session, in process, the three years sequential (rule 12 `[R-PARALLEL]`),
re-solving the keeper's exact recorded `meta.json` config at HEAD. Determinism
pinned by the tool: `MARKET_SIM_HIGHS_THREADS=1`, `MARKET_SIM_WARMSTART=1`,
`MARKET_SIM_WARMSTART_XYEAR=0` (the thread pin is X-4's subject, not this
lane's).

The bundle is written to `results/regression-goldens/perfb-stage0/NYISO/`
(119 MB, **gitignored**). The committed deliverable is the updated
`manifest.json` plus this finding.

| | capture 1 (DISCARDED) | **capture 2 (COMMITTED)** |
|---|---|---|
| Keeper targeted | `2026-09-04-nyiso-185-family-hr` | **`2026-09-04-nyiso-186-astoria-identity`** |
| Keeper bundle | `results/calibration/nyiso185_family_hr` | `results/calibration/nyiso186_astoria_identity` |
| Basis sha | `8a18e9e1` | `2ded868f` |
| Years / hours | 2023–2025 / 8760 | 2023–2025 / 8760 |
| Recorded flags replayed | 271 kwargs → **280** meta keys | 273 kwargs → **282** meta keys |
| `scenario_config` | 779 matched, **0 drifted** | **781 matched, 0 drifted** |
| HEAD-only meta keys | 2 | **0** |
| `keeper_only` meta keys | 0 | **0** |
| `dropped_dead_config_keys` | `{}` | `{}` |
| Content-hashed files | 10 | 10 |
| Solves | 6 (P0+P1 × 3 yr) | 6 (P0+P1 × 3 yr) |
| Wall clock | 13 min 07 s | **13 min 16 s** |
| Peak RSS (in-process) | 5.39 / 5.64 / 5.68 GB | **5.41 / 5.59 / 5.87 GB** |

**`scenario_config` drift is ZERO**, the stronger-than-required result every
prior capture recorded. **Capture 2 carries ZERO HEAD-only meta keys** — better
than every stage-0 capture before it (ERCOT 1, NYISO-159 2, MISO 1), because
186's `meta.json` was recorded hours before the capture and is fully current
with HEAD. Capture 1's two HEAD-only keys were `fleet_state_from_eia860` and
`nearby_fuel_price_zone_donor_guard`, both `bool = False` and byte-inert off;
186 records both, which is exactly why the count falls to zero.

**The keeper's armed mechanisms were confirmed live in the capture log**, not
inferred from flags: `nyiso_seam_par_attribution` on all four border links (the
measured p90 directional envelope of the attributed seam, all three years);
**eGRID prime-mover-family heat rates on 38 generator rows across 7 plants**
(nyiso-185's mechanism); **eGRID identity-reconciled heat rates on 5 generators
across 2 plants** (nyiso-186's merged Astoria identity — the delta this capture
exists to baseline); measured power-only CHP heat rates (50 generators / 17
(plant, class) pairs); the published Zone-K N-1-1 TSL and Zone-J NYC locality
import caps; the Upstate_West→Capital_Hudson monthly TTC envelope from measured
Central-East DAM postings; the NYISO gas commitment bridge (41,733 unit-hours
floored, 5.63 TWh, min-run extension ON); the NYSDEC 227-3 peaker-rule overlay;
and the energy+reserve co-optimisation (9 locational reserve families, 60 ORDC
steps $3–$775).

### Per-entry provenance (manifest schema v2)

| ISO | `provenance.git_sha` | `basis_sha` | `git_dirty` | `source` | `recorded_at` |
|---|---|---|---|---|---|
| NYISO | `2ded868f` | `2ded868f1f204b8230e44fa928f3ae594201ef7b` | false | `stamped-at-capture` | 2026-09-04T15:18:10Z |

`2ded868f` **was `origin/main` at launch**, so `git_sha` and `basis_sha`
coincide and both are origin-durable. No `af1ccb6`-class unresolvable-provenance
defect.

## 3. The schema-v2 invariant, the merge-base hazard, and `resolved_inputs` — all checked, none assumed

Measured by loading `origin/main`'s manifest and this branch's and comparing
entry by entry (canonical JSON):

* `hash_scheme`, `note`, `schema_version`, `stage_tag` — **SAME**;
* CAISO, ERCOT, ERCOT\_\_carveout-2023, MISO, NEISO, PJM — **BYTE-SAME**;
* NYISO — CHANGED (the only entry the capture rewrote). Entry count 7 → 7.

The tool wrote *"manifest written … (7 keepers)"* on both runs. **The
CAISO/NYISO §3 merge-base hazard was checked explicitly on both**, by diffing
the manifest between the capture's basis and `origin/main`: empty in both cases,
so there was nothing to splice. Main advanced 23 commits during capture 1 and
touched **no** file under `src/market_sim/` or `scripts/run_calibration*.py` —
verified by `git diff --stat`, which is also what makes the §1.1 hash comparison
a valid experiment (identical code, identical inputs, different keeper label).

**`resolved_inputs` reproduce exactly.** The CAISO lane's recommended check, run
here for the first time as a pre-commit gate: all six recorded keys MATCH
between keeper 186's own `run_config.json` and the golden's —
`seam_import_cap` (`flag_off`, all three years), `hydro_plant_modes`
(`partition_present: false`), `campd_unit_outages`
(`campd-unit-outages-perunitmerit-NYISO.csv`, sha `45bc4f7c…`, 374,504 B) and
`thermal_tranches` (`thermal_tranches-perunitmerit-NYISO.csv`, sha
`2f4f137a…`, 7,423 B). Both raw files were **hash-verified against the keeper's
record before launch**, not after. As §1 notes, this check is necessary and
**was not sufficient** — it passed identically on the contaminated run.

## 4. Operational record (honest, including the two process defects)

* **THE FIRST DEFECT — `origin/main` was never fetched before the stop-report
  or before launching.** The session read `keepers/NYISO.json` at its local pin
  and reported 185 live. nyiso-186 had promoted on main at 08:45, 26 minutes
  before the capture launched at 09:11. The dispatch's guard says to confirm the
  keeper *"at your pin"*, and at the pin the answer was 185 — but a pin is a
  snapshot of a lane that was promoting every few hours, and a capture is a
  ~13-minute action taken against `main`. **A `git fetch origin main` immediately
  before launch would have caught it and cost nothing.** Recommended as a
  standing pre-flight step for every future capture.
* **THE SECOND DEFECT — `pip install -e .` is missing from the recipe, and no
  prior finding records it.** The three precedent findings all say the container
  had no Python dependencies and that a venv from the fully-pinned
  `requirements.txt` resolved it. That is **not sufficient**: `requirements.txt`
  installs dependencies but not the package, so **14 of 16 curate scripts died
  on `ModuleNotFoundError: No module named 'market_sim'`** until
  `pip install --no-deps -e .` was run. The venv otherwise matched the keeper's
  recorded environment exactly (numpy 2.4.6, pandas 3.0.3, scipy 1.17.1,
  pyarrow 24.0.0, pydantic 2.13.4). `highspy` exposes no `__version__`, so the
  entry records `"highspy_version": "unknown"`, consistent with every
  pre-existing entry.
* **Data hydration was a no-op:** this is a **full clone** (5.8 GB `data/raw`
  local), so `hydrate_data.py --profile nyiso` reported every blob already
  present. No converted-corpus re-fetch was required; no corpus loader
  hard-failed.
* **The clean-partition pre-flight, run per the MISO §3 lesson (audit
  `scripts/` too, not just `src/`).** `data/clean` was **empty**, as it is in
  every fresh container. **Fifteen partitions were regenerated** before launch:
  the hard requirement `nyiso-interface-flows` (the armed
  `nyiso_seam_par_attribution` hard-fails without it, naming its own remedy),
  the four other NYISO datatypes (`nyiso-downstate-gas`,
  `nyiso-renewable-curtailment`, `nyiso-reserve-requirements`,
  `nyiso-som-hub-fuel-annual`), plus `som-competitive-conduct`,
  `capacity-deliverability`, `ramp-capability`, `demand-profile`, `fleet`,
  `reference`, `egrid`, `emissions`, `fuel-prices`, `coal-basin-price`,
  `coal-mining-ppi`. All 15 reported `[ ok ]`.
  **NYISO's silent-degradation surface is narrower than MISO's, and this was
  verified rather than assumed:** `build_miso_deliverability_groups`
  (`scripts/run_calibration.py:2724`, the flag-independent hazard of MISO §3(a))
  is `if iso == "MISO"` gated and unreachable here; `capacity_deliverability_limits`
  is unset in the keeper so the CAISO MIC seam cannot fire; and
  `egrid_family_heat_rates` reads a **raw** artifact
  (`data/raw/_processed-legacy/egrid_family_heat_rates_NYISO.csv`, 6,993 B), not
  a clean partition. The residual exposure is the derived-artifact class of §1,
  which no partition regeneration addresses.
* **Memory — this capture did NOT page.** An **8 GiB swapfile** was enabled
  before the first solve regardless, per the dispatch. Sampled every 30 s on the
  capture process: peak RSS **5.08 GB** (sampler) against the solve's own
  reported in-process peak of **5.87 GB**, and **swap usage was 0 in 27 of 27
  samples** on capture 2 and 24 of 24 on capture 1. Both figures sit just above
  the prior NYISO capture's 5.79 GB and far below MISO's 13.67 GB. **NYISO is
  comfortably capturable on a 15 GB container without swap**; the swapfile was
  pure headroom. Disk fell to ~9.8 GB free (8 GiB swapfile + the 119 MB golden,
  retained).
* **Log audit.** 276 lines; **0 ERROR, 0 Traceback**, no `baked_fallback`, no
  `static summer`, no `static shares`, no zonal-shares parse failure. The three
  `static ladder` hits are the **healthy** tell — *"import tranches repriced to
  measured neighbor hourly DA LMPs … static ladder bypassed"* — not a fallback.
  The only missing-partition line is `no hydro-plant-modes clean partition for
  NYISO` (×2), which is **faithful**: the keeper's own `run_config.json` records
  `hydro_plant_modes.partition_present: false`, so an absent partition
  reproduces the keeper exactly (the same reading the CAISO/NYISO and MISO lanes
  made). The remaining 35 WARNINGs are all keeper-intrinsic fleet-build
  reconciliations: 30 `cc_capacity_reconcile` clamps on NYISO CC plants with
  corrupt summer-capacity rows, 2 demand-dropout repairs, and 1 eGRID heat-rate
  reconciliation at plant 55641 (the co-located 64020 double-count → 6.880, the
  same plant the CAISO and MISO captures both logged).
* **A monitoring artifact, disclosed so no one quotes it.** As in all three
  precedents, background-task notifications arrived announcing capture
  "completion" on their own schedule. Every timing, count, hash and status here
  is read from the capture logs
  (`capture_run1_185.log`, `capture_run2_186.log`), the memory samplers
  (`mem2.csv`, `mem_run2.csv`) and the committed manifest — never from those
  notifications.

## 5. Holdout compliance (rule 22 `[R-HOLDOUT]`)

Both captures solved **only** the years recorded in the keepers' own
`meta.json` — **2023, 2024, 2025**, entirely in-sample (training tier). No 2022
touchpoint, no 2019/H1-2026 locked-test year, no `--holdout-authorized`.

**NYISO holds NO `complete` marker** (withdrawn 2026-08-30; the marker names
{ERCOT, NEISO, PJM}) and **`final` is empty for every ISO**. Neither marker was
read, written or relied upon, and none was needed: a 2023–2025 solve requires no
tier authorization. The holdout spend freeze (`holdout-freeze.json`, scope
`tiers: ["locked_test"]`, `isos: "ALL"`) is untouched, and NYISO's 2019 and
H1-2026 remain **NEVER GRANTED** and unspent.

The `nyiso-interface-flows` regeneration wrote partitions for 2018–2026 because
the curate script covers its whole raw span; **only 2023–2025 were read**, and
data preparation is explicitly unrestricted under rule 22's own clause — *"what
is held out is the SCORE, never the DATA or the ARCHITECTURE"*. No
out-of-training year was solved, scored or registered.

## 6. Deliverables

* `results/regression-goldens/perfb-stage0/manifest.json` — the NYISO entry
  re-stamped to `2026-09-04-nyiso-186-astoria-identity`.
* `docs/FINDING-stage0-recapture-nyiso-2026-09.md` — this file.
* Golden bundle under `results/regression-goldens/perfb-stage0/NYISO/` —
  gitignored by design, retained on disk in this container.

**Golden tier exercised once, as R-V's exercise authority permits** (the
workflow is `workflow_dispatch`-only since R-Y, 2026-09-02). Run
**33889067608** (run #10, `workflow_dispatch`, head `a4c3d61a`) on this branch:
**conclusion `success`**, 15:22:06 → 15:34:47 UTC = **12 min 41 s of billed
runner minutes**. One run, not re-dispatched.

**This golden is current only until NYISO's next promotion**, and that is not a
formality in this lane: NYISO promoted three times in the three days to
2026-09-04 (177 on 09-02, 185 and 186 on 09-04). The entry reads STALE the
moment the next promotion lands.

**IT ALREADY DOES — recorded here rather than left for the next lane to
discover.** Within roughly two hours of this capture completing, NYISO promoted
**twice more**: `2026-09-04-nyiso-187-astoria-routing` (`de75234f`) and then
`2026-09-04-nyiso-188-combined` (`2cc95aa2`, *"the first NYISO keeper to read
CALIBRATED"*). The committed golden names `2026-09-04-nyiso-186-astoria-identity`
and is therefore **two promotions stale against the live keeper**, exactly as
§7 item 5 anticipates. This is not a defect in the capture, which is faithful to
the keeper it names and passed its oracle; it is the cadence problem stated as a
measured fact. **Five NYISO promotions landed on 2026-09-04 alone** (185, 186,
187, 188 — plus 177 the day before), against a ~13-minute capture. Whether to
chase 188 is an owner decision, deliberately not taken in this lane.

## 7. Open items handed back

1. **The derived-artifact blind spot of §1 is UNCLOSED, and the CAISO lane's
   proposed fix does not cover it.** Asserting the replay's `resolved_inputs`
   against the keeper's — the CAISO/NYISO §7 item 1 and MISO §7 item 2 proposal
   — passed identically on the contaminated and the clean run here, because the
   eGRID identity artifact is not in `resolved_inputs`. **Recommendation:**
   `resolved_inputs` should carry a content-hashed row for every
   `_processed-legacy` derived artifact a keeper reads
   (`egrid_identity_heat_rates`, `egrid_family_heat_rates`, `campd_*_params`,
   `thermal_tranches` already qualifies), so the oracle can see an input
   substitution behind an unchanged flag. Owner/infrastructure question,
   deliberately not fixed in this lane.
2. **A capture should fetch `origin/main` and re-read the keeper shard
   immediately before launching** (§4, first defect). Cheap, and it converts a
   silent mislabelling into a stop-and-report.
3. **`pip install -e .` belongs in the recipe** (§4, second defect). The three
   precedent findings' venv instructions are insufficient as written.
4. **CAISO and MISO stage-0 goldens are stale against keepers newer than the
   ones R-AF was written on** — CAISO's live keeper is now
   `2026-09-04-caiso-243-b1-f923` (not the `caiso-231-b1-ungrounded` its golden
   names) and MISO's is `2026-09-03-miso-202-unitclip` (not `miso-198-oomlevel`).
   Whoever captures them must re-read the shard rather than trust R-AF's
   citation, and should expect the same two-move hazard this lane hit.
5. **NYISO's promotion cadence outruns the capture.** Three promotions in three
   days, with a ~13-minute capture window and a manifest that keys on the
   designated keeper id. Either captures for a hot lane are taken immediately
   after a promotion commit lands, or the staleness check needs a notion of
   "golden matches the keeper's *config*, not its *id*" — the §1.1 hash identity
   is evidence that a config-keyed check would have called capture 1 current.

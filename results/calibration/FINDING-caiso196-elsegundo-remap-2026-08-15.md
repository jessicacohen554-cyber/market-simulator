# FINDING — caiso-196: the El Segundo (ORIS 330 → EIA 57901) CEMS-history remap repair — control reproduces the keeper BIT-ZERO, the repair engages at high magnitude, ONE pre-registered criteria flip (C1-2023) is adjudicated ACCEPT-WITH-FLIP, and the keeper/campaign-anchor decision is packaged for the owner

**Pre-registration:** `PRECHECK-caiso196-elsegundo-remap-2026-08-15.md`, committed and
pushed at `c80670d` BEFORE any solve of this session ran. Gates applied as written; no
band edited. **Keeper UNCHANGED** at `2026-08-09-caiso-188-d1-micseam` — promotion is
explicitly escalated, not taken (PRECHECK §6). 2023–2025 only; both holdout markers and
the spend freeze untouched. Surfaced by lane 2's G-COV kill
(`FINDING-caiso193-wefor-residual-2026-08-15.md` §2). Registered runs:
**`2026-08-15-caiso-196-e0-control`** and **`2026-08-15-caiso-196-e1-elsegundo`** (both
NOT-YET, C6 UNATTESTED — the standard non-keeper A/B posture; a promotion would generate
the governance attestation, the pjm-153/caiso-189 pattern).

## 0. Direction-hazard regime (verbatim from the PRECHECK, binding)

> The expected sign of this repair is **ANTI-C3a-favorable**: it can only ADD measured
> outage removal (a plant that previously carried no overlay gains its real windows),
> which lowers availability and raises price, while C3a 2024/2025 already FAIL high.
> C3a movement is inadmissible as evidence for or against acceptance in EITHER
> direction (rules 1, 13, 14): if the gates pass and C3a worsens, the repair stands
> (caiso-183/188 precedent); if the gates fail, no C3a improvement rescues it. C3a is
> reported for transparency only.

**Single-mechanism statement (required verbatim):** The A/B delta is the
(330 → 57901) CEMS-history remap and the extract rows it adds; no ScenarioConfig
field differs.

## 1. Gate tally — 6/6 PASS

| gate | bar | measured | verdict |
|---|---|---|---|
| **G-CTRL** | e0 within \|ΔC3a\| ≤ 0.1 pp/yr, \|ΔC3b\| ≤ 0.005/yr of the committed keeper | **BIT-ZERO**: max \|Δ\| = 0.0 over all 61,320 zone-hours per year on `hourly/system_*.parquet` (prices included) AND all class-hour dispatch on `hourly/class_hourly_*.parquet`, every year — on highspy 1.14.0 vs the keeper's 1.15.1, reproducing the caiso-184/188 G-CTRL norm. Noise floor: exactly 0.0 pp / 0.000, quoted before any treated delta was read. The keeper's D-1/D-2 diagnostic rows also reproduce to the last decimal (the ST_GAS 2024/2025 D-1 FAIL rows included — pre-existing, non-gating). | **PASS** |
| **G-DELTA** | extract diff strictly additive, facility 57901 only; config diff empty | Baseline first re-proven: with the remap edit stashed, the committed recipe (`--iso CAISO --years 2018…2026 --merit-order-guard --hour-grain`) reproduces the committed extract **byte-identically** (sha256 `25360e90…`) at this head, so the remap is the only free variable. Repaired extract: **+233 rows, 0 removed, every added row facility 57901** (units 5/7: 112/121); sha → `5f3e35c5…`. Layup companion: window-set unchanged (810 rows, set-equal on every key; **zero** 57901/330 rows — no El Segundo span classified as layup); its diff vs the committed file is purely the two `--hour-grain` schema columns the committed file predates (pre-existing drift, characterized against the baseline run: baseline layup sha == repaired layup sha). `scenario_config` diff e0 vs e1: **EMPTY** over the full config. | **PASS** |
| **G-ENGAGE** | e1 loader resolves (57901, CC_REGULAR) with mult < 1 in ≥1 year; e1 LP differs from e0 | Loader half: mean availability multiplier **0.186 / 0.160 / 0.029** (2023/24/25), hours-below-1: 7,572 / 8,094 / 8,679 of 8,760. LP half: **35,249 / 38,957 / 39,792 zone-hours** with changed prices (of 61,320), max single-hour \|Δprice\| $81.5 / $146.3 / $61.0. | **PASS** |
| **G-SIXISO** | no other ISO's extract/config/cell written | Only `campd-unit-outages-CAISO.csv` + its layup companion re-derived; the remap keys are CA facilities; the five other ISOs' extracts untouched (no re-derive run). | **PASS** |
| **G-DOF** | zero new parameters; ledger unchanged in both attestations | `build_dof_ledger.py --iso CAISO` on both bundles: **n_entries 11 / n_residual 8 in each** — the repair adds data, not freedom. | **PASS** |
| **G-C8** | both bundles ship `legitimacy_diagnostics.json` | Written by the replay driver for both arms; C8 scores PASS on both at registration. | **PASS** |

Protocol §3 environment legs, both arms: seam import caps logged at
16055 / 16452 / 16148 MW (MIC partition materialized, Part A live);
`hydro_ror_split=false` disclosed in both run notes; warm-start pinned off by the
replay driver; arms solved sequentially (rule 12).

## 2. What the repair actually is — the compensating error, measured per plant

El Segundo Energy Center's CEMS record enters the overlay at **high magnitude**: unit 5
carries 10/11/9 windows over 301/301/355 outage-days in 2023/2024/2025 (unit 7
similar); the overlay now removes **81–97 %** of the plant's capacity-hours in the
solve years. Class-level, CC_REGULAR `X_c` rises **0.2157/0.2621/0.3186 →
0.2443/0.2916/0.3528** (+2.9/+3.0/+3.4 pp). The per-plant confrontation is the
finding:

| year | El Segundo measured CEMS gross | e0 (keeper recipe) model dispatch | e1 (repaired) model dispatch |
|---|---|---|---|
| 2023 | 0.169 TWh (CF ≈ 3.6 %) | **3.265 TWh (19.4× measured)** | 0.694 TWh (4.1×) |
| 2024 | 0.192 TWh | **3.245 TWh (16.9×)** | 0.636 TWh (3.3×) |
| 2025 | 0.053 TWh | **2.746 TWh (51.6×)** | 0.087 TWh (1.6×) |

Under the statistical-WEFOR-only representation the LP has been running a
largely-idle plant as a ~70 %-CF workhorse — 3.2 TWh/yr of phantom supply from one
plant, silently absorbed into a class total that sat in band. The repair removes the
compensation; what remains visible (§3) is the class's true structural residual.
The shipped merit-order guard classified **zero** of El Segundo's spans as economic
layup (the fail-safe retains ambiguous spans as mechanical — caiso-192 G-CONS
behaviour at full strength), so El Segundo **joins the caiso-187 §3 open object**
(CC_REGULAR removal far above the ~10 % published expectation, unexplained and not
merit-order layup) at high magnitude rather than resolving it. Whether these long
spans are true mechanical unavailability or economically-idle conduct the detector
cannot separate remains the freeze's standing question; the independent
discriminator would be the CAISO DAM outage reports
(`data/raw/caiso-dam-outages/`, BLOAT-B-2 corpus — payload restorable from its pin),
a natural owner-chartered probe.

## 3. The pre-registered criteria-flip, and its §5 adjudication: ACCEPT-WITH-FLIP

**C1 fuel-mix flips PASS → FAIL on exactly one row: 2023 CC_REGULAR**, e0 −3.57 TWh /
−1.5 pp (PASS, at the band edge) → e1 **−4.44 TWh / −1.9 pp (FAIL)**; 2024 CC_REGULAR
moves −0.50 → −1.21 TWh and stays PASS; 2025 C1 rows are vintage-SKIPPED (not gated).
Integration-protocol §5 (input-side re-examination ONLY):

* **No mis-citation** — ORIS 330 = El Segundo verified in both EIA-860 (plant 57901,
  generator IDs 5/6/7/8) and CAMPD (facility 330 "El Segundo", units "5"/"7", exact
  ID match); the legacy EIA plant 330 retired 2015 with nothing left to collide.
* **No coverage failure** — the two CTs are the plant's CEMS-monitored units; every
  CA file 2018–2025 carries them.
* **No classifier deviation** — the shipped, caiso-192-confirmed merit-order guard ran
  with its frozen constants and retained the spans as mechanical per its adjudicated
  fail-safe.

The input therefore **survives re-examination**: the flip is the model reacting to
accurate data — the §5 disposition is verbatim **"ACCEPT-WITH-FLIP, escalate to
closeout/owner"**, and rule 14 names what the flip uncovered: the e0 class total was
in band only because this plant's phantom 3.2 TWh was compensating the standing
CC-side under-dispatch (the caiso-121 surplus-belly / caiso-135 ride-through /
caiso-140 §B over-import lane — already the named C3a root cause). The arm's −4.44 TWh
is that known residual made visible, not a new defect.

## 4. C3a / C3b — transparency report only (never consulted; §0)

| year | keeper & e0 C3a | e1 C3a | keeper & e0 C3b | e1 C3b |
|---|---|---|---|---|
| 2023 | +3.4 % (PASS) | +4.4 % (PASS) | 0.075 | 0.077 |
| 2024 | +10.4 % (FAIL) | +11.7 % (FAIL) | 0.145 | 0.155 |
| 2025 | +12.9 % (FAIL) | +14.5 % (FAIL) | 0.164 | 0.176 |

The anti-favorable movement (+1.0/+1.3/+1.6 pp) is the pre-registered expected sign.
C3b stays PASS in every year (≤ 0.20). C3c: e1 model RT>$200 hours vs actual —
re-measured at promotion per caiso-189 §8.3 if promoted; both arms carry the same
ledger posture as any non-keeper probe (none).

## 5. The owner decision package (nothing below executed by this session)

1. **Keeper.** All six pre-registered gates pass; the repair is rule-14
   structurally-correct (a 537.4 MW plant's measured availability replaces a
   statistical guess at zero DOF, anti-favorable sign, per-plant fidelity improved
   17–52× → 1.6–4×). Against it: the C1-2023 flip (ACCEPT-WITH-FLIP, §3) and the
   worsened C3a. The caiso-183 precedent promoted through failing shape gates on
   exactly this posture; the decision is the owner's because of (2) — and because a
   promotion here re-baselines the class-flip into the keeper record.
2. **Campaign re-anchor.** Integration protocol §1/§3 fix the campaign control to the
   caiso-188 recipe **on its committed inputs**; adopting e1 as baseline amends that
   anchor, and the protocol reserves amendments to "a fresh adjudication session and
   explicit owner authorization". Lanes 3 and 5 should compose on whichever base the
   owner designates.
3. **Lane-2 re-run** on the repaired instrument, scoped `{CC_REGULAR}`: G-COV now
   passes both population readings (extract 0.9758 / CEMS-remap-aware 0.9667,
   `_caiso196_gcov_remeasure.json`), the owner-granted value 0.0 is invariant (X_c
   4.9–7.1× W after the repair), and the gatespec's own fail-closed clause prescribes
   the class subset. Needs only the owner's word + the anchor decision.
4. **Desert Star NV intake** (370.1 MW, the remaining CC_REGULAR extract gap): add NV
   to `ISO_STATES["CAISO"]` on the NYISO NY+NJ fleet-filtered template and fetch
   2018–2026 via the CAMPD queue path; the extract's CC_REGULAR population then
   reaches 100 % of the current roster.
5. **The mechanical-vs-economic discriminator for El Segundo-class spans** (§2): the
   CAISO DAM outage-report corpus is the one on-disk instrument that could separate
   them; restoring its payload and confronting the 57901 windows is a chartered
   probe, not a default.
6. **Flagged, untouched artifacts derived through the same remap** (single-mechanism
   scope, PRECHECK §2): `thermal_tranches_CAISO.csv` (no 57901 rows — El Segundo's
   committed/peaking shares stay class-default until its own cited re-derive) and
   `plant_emission_rates` v1/v2 (57901's CO2-cost basis likewise derived with
   facility 330 orphaned). Each is its own cited re-derive with its own A/B.

## 6. Artifacts

Registered runs `2026-08-15-caiso-196-e0-control` / `2026-08-15-caiso-196-e1-elsegundo`
(bundles `results/calibration/caiso196_e0_control` / `caiso196_e1_elsegundo`, each with
`legitimacy_diagnostics.json` + `calibration_attestation.json` free_parameters 11/8 +
`metrics.json`; hourly sidecars committed per the caiso-188 A/B precedent). Records:
`_caiso193_wefor_coverage.json` (frozen instrument), `_caiso196_gcov_remeasure.json`
(repaired instrument). Repair commit `e68a70d` (remap + tests + extract re-derive,
byte-verified). Matrix duty (b): `campd_outage_windows` CAISO evidence appended (sha
supersession + this A/B); `wefor_residual` cell updated by the companion lane-2
FINDING. Retention: the auto-prune displaced `2026-08-04-control-flagoff-lossless-
baseline` and `2026-08-05-caiso-174-control-flatfleet` (both non-keeper controls).
Bench parts `frontend/data/backcast/bench/CAISO/{2023,2024,2025}.json.gz` changed and
are committed: the remap routes El Segundo's CEMS history onto its fleet plant code,
so the ACTUALS side of the benchmark (CEMS-based class/hourly series) gains the
plant — the same correctness repair on the measurement side. Both arms were
registered against this SAME updated bench, so the A/B is internally consistent; the
LMP-based G-CTRL tolerance basis (C3a/C3b actuals) does not touch CAMPD and is
unaffected.
Environment: full clone; MIC partition materialized in-session
(`curate_capacity_deliverability.py --isos CAISO`, 386 rows); the dashboard-deploy
stall cleared at session start (run #1400 stuck `waiting` since 2026-08-06 cancelled;
run #1510 deployed 2026-08-15T20:33Z).

## 7. PROMOTION ADDENDUM (2026-08-16) — the owner decided §5 item 1: e1 IS the keeper

The owner's decision, in-session verbatim: *"Is this a recommended keeper candidate?
If so plz promote. If structural integrity improves but gates regress that may still
be a keeper.."* — adopting the rule-14/caiso-183 posture for exactly this arm.
Executed by the same session, one day after registration:

* **C6 attested AT promotion** — `scripts/gen_caiso196_attestation.py` (the
  `gen_caisoNNN` series resumes; every premise computed: G-DELTA zero of 714 config
  keys differ; G-EXTRACT each bundle's `resolved_inputs` records its extract sha —
  the caiso-190 machinery's first use in a promotion; G-ENGAGE CC_REGULAR
  −0.872/−0.717/−0.968 TWh with 35–40k price zone-hours moved, from committed
  sidecars; G-MACHINE clean; G-DOF ledger byte-carried 11/8; G-EXC four exceptions
  carried from caiso-188 with classifications/reasons byte-identical, C3c magnitudes
  re-measured UNCHANGED, C3a magnitudes REFRESHED and inert under v3.1).
* **Re-verified determination: NOT-YET** — 8 criteria scored, 2 load-bearing FAILs
  (C1 2023 CC_REGULAR −4.44 TWh; C3a 2024 +11.7 % / 2025 +14.5 %), C3c the single
  ledgered caveat, C6/C8/C2/C3b/C4 PASS. One more documented FAIL than the
  incumbent, per the ACCEPT-WITH-FLIP record (§3) and the owner's clause.
* **LOYO discharged by construction**: zero fitted parameters, per-year-independent
  detection, the remap a static registry-identity fact, and no in-sample gain
  anywhere — the overfitting signature cannot exist on any leave-one-year-out split.
* **Keeper shard, matrix shard (keeper + gates stamps), §5.2 prose header, status
  part, and the keeper sidecar `market_story` all re-stamped**; `audit_keepers
  --iso CAISO` PASS (0 failures, 0 warnings); `check_mechanism_matrix` clean.
* **Site retention applied per the standing 2026-08-15 directive**:
  `2026-08-09-caiso-188-d1-micseam` (superseded keeper) and
  `2026-08-15-caiso-196-e0-control` (the keeper's own bit-zero control, the NEISO
  control precedent) pruned via `prune_iso_runs.py --force-uncite`; CAISO lane =
  the keeper alone. Durable evidence: this FINDING, the attestation lineage, the
  calibration log, git history.
* **Campaign re-anchor**: the owner's promotion is the fresh authorization the
  integration protocol's amendment clause requires — the campaign control base is
  now THIS keeper's recipe/bundle (`--replay-bundle
  results/calibration/caiso196_e1_elsegundo`). Lane-2 re-run ({CC_REGULAR}-scoped)
  and lanes 3/5 compose on it.
* **Rule 22 D-5(b) does not fire** (no `complete` marker); no declaration file
  touched; freeze untouched.

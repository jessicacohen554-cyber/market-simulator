# RESULT — caiso-270: the scarcity lever is closed by measurement, the residual is re-named, and the keeper's lost bundle is restored

**Session caiso-270, 2026-09-10. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
Keeper **UNCHANGED**: `2026-09-10-caiso-269-lateevening-clean`, **CALIBRATED**, single ledgered C3c.
Charter records: `docs/FINDING-caiso270-scarcity-ordc-phase0-2026-09-10.md`,
`docs/PRECOMMIT-caiso270-keeper-restore-2026-09-10.md`,
`docs/ADDENDUM-caiso270-clean-partition-repin-2026-09-10.md`.

---

## §1 — The result in seven lines

1. **The chartered lever is dead, killed by its own pre-registered STOP.** The CAISO scarcity/ORDC overlay
   is **~0 %** of the December-2022 C3a excess, against a 30 % threshold — false **by construction**
   (`ordc_adder`'s shortage function is `LOLP(R)`, keyed to reserve MW; the price level enters only as
   `max(VOLL−λ,0)`, a **dampener** that shrinks the adder 13 % as λ goes 50 → 306) and false by four
   independent measurements.
2. **The residual is RE-NAMED, and it is not a December or a scarcity object.** On the same delivered-gas
   series both sides, the model's implied marginal heat rate exceeds the market's in **40 of 48 months**
   (mean +1.01, median +0.84). **December 2022's +1.73 ranks 12th of 48.** Its $63.91/MWh error *is*
   1.73 HR-points × $37.04/MMBtu: the ordinary system-wide bias levered by a gas price 3.7× the year's mean.
3. **The other gas-crisis month falsifies the "gas crisis" framing outright**: 2023-01 (gas $16.54/MMBtu,
   daily max $24.75) is the model's **best month of the 48** at dHR **+0.02**.
4. **The C3c object SPLITS.** 2022's tail *excess* is the same object as C3a-2022 (549 of 580 model hours
   >$200 are December); 2023-2025's tail *deficit* (23/0/0 vs 47/35 actual) is the overlay **under**-firing —
   opposite sign, different object, and the one the ledgered caveat names.
5. **The designated keeper had no bundle anywhere**, and this session restored it: re-solved as four
   per-year shards (rule 32 `[R-SHARD]`, the parent never solved) and committed at the paths the registry
   sidecars already name.
6. **G-REPRO, the one pre-registered gate, PASSES on all four years.** C3a reproduces the published
   +12.90 / +4.33 / +8.54 / +7.87 % to **0.0006 / 0.0009 / 0.0041 / 0.0000 pp**; C3b reproduces
   0.2402 / 0.0827 / 0.1391 / 0.1070 to **0.0000** on every year. G-DRIFT's INERT classification is now
   confirmed **by measurement**, not only by code reading.
7. **One fleet of four shards was lost to a defect that was mine**, and §6 is the full accounting.

## §2 — Half one: the chartered lever, closed (detail in `FINDING-caiso270`)

Measured from the keeper's own delivered-gas series (the armed citygate daily-spot leg, byte-identical at
HEAD per the G-DRIFT audit), against the committed predecessor bundles:

* **December 2022 is 44.7 %** of the 2022 C3a excess (+5.163 of +11.558 $/MWh reconstructed).
* **The overlay's share of that is ~0 %**, on four instruments: (a) this cell's own caiso-229 bound
  ($0.017/$0.006/$0.003 per MWh, 2023/24/25), whose arithmetic inverted at λ=306 needs reserves
  **≤ 7,110 MW** for even $10/MWh against a ~11,667 MW implied 2023 minimum; (b) the adder is added
  **uniformly to every zone**, and **62 December hours carry a zone at exactly $0.000** — at hod 0-4, 11-12
  **and 16-23**, i.e. inside the evening net-peak the overlay exists to price, where the December
  load-weighted price runs $354-372; (c) **no evening diurnal signature** — December's implied heat rate is
  6.91-9.86 across all 24 hours, the flattest and lowest profile of the year, with h16-22 (9.4-9.9) *below*
  February's (11.5-13.2); (d) **zero** December hours above implied HR 25, against 23 in September 2022
  (max LW $1,247) — and September is the model's **best** month of 2022 (dHR +0.23).
* **The restored bundle independently corroborates the C3c split**: `gen_caiso269_attestation.py` reads
  the model tail as **{2023: 23, 2024: 0, 2025: 0}** on the span and **{2022: 586}** on the touchpoint — the
  rubric's own C3c basis, matching the phase-0 measurement made before any of these bundles existed.

**The successor is named and deliberately NOT solved** (`FINDING-caiso270` §6): *why does the implied
marginal heat rate run ~1 point above the market's in 40 of 48 months?* Picking a lever off that residual
without its own charter and external driver is the fitted-mechanism selection rule 1 `[R-STRUCT]` forbids,
and this session did not do it.

## §3 — Half two: the keeper's bundle, restored

### §3.1 — What was wrong

`frontend/data/backcast/keepers/CAISO.json`, the registry sidecars
`2026-09-10-caiso-269-lateevening-clean.json` and `2026-09-10-caiso-269-lateevening-2022.json`, and
`scripts/gen_caiso269_attestation.py` all name bundles that **existed nowhere**:

* `git ls-tree -r HEAD results/calibration/caiso269_lateevening_span/` returned **nothing**;
* `.gitignore` ignored `results/calibration/caiso269_lateevening_*/` — added under rule 31 `[R-RETAIN]`
  while the run was a rule-29 screen and **never lifted when it was promoted to keeper**;
* its shard branches were deleted or emptied (`claude/caiso269-2022` carries
  *"untrack the shard bundle so this branch is merge-safe"*, `9e7ad037`);
* its container was reclaimed.

So **rule 15 `[R-DASHBOARD]`'s requirement that a KEEPER commit its `hourly/` sidecars went unsatisfied**,
and this session was the first to need them — phase 0 had to run on the predecessor instead.
`check_registry_payload_parity.py` does **not** catch this class: it flags committed dirs with no sidecar,
never a sidecar with no dir.

### §3.2 — G-REPRO, the one gate, on artifacts verified in the parent

Four per-year shards, all pinned to `8d627e642353c7a5dad06c8a9c764253331011d5`, each solving the committed
predecessor recipe **plus one flag** (`--replay-bundle … --caiso-dsw-lateevening-clean`).

| year | C3a model LW | actual | err % | **published** | Δ pp | C3b | **published** | Δ | verdict |
|---|--:|--:|--:|--:|--:|--:|--:|--:|---|
| 2022 | 95.389 | 84.49 | +12.90 | **+12.90** | **0.0006** | 0.2402 | **0.2402** | 0.0000 | **PASS** |
| 2023 | 56.516 | 54.17 | +4.33 | **+4.33** | **0.0009** | 0.0827 | **0.0827** | 0.0000 | **PASS** |
| 2024 | 37.611 | 34.65 | +8.54 | **+8.54** | **0.0041** | 0.1391 | **0.1391** | 0.0000 | **PASS** |
| 2025 | 37.129 | 34.42 | +7.87 | **+7.87** | **0.0000** | 0.1070 | **0.1070** | 0.0000 | **PASS** |

`slack` and `dump` are **0 in every zone-hour of every year**. The four C3a levels are the keeper's own arm
values from `RESULT-caiso269` §2.1 to three decimals.

**Every artifact was verified in the parent, never taken from a shard's report** — the
`ADDENDUM-caiso269` §A5 discipline. All six config-signature flags `true`
(`caiso_dsw_lateevening_clean`, `caiso_citygate_spot_level`, `caiso_citygate_flow_date`,
`gas_electric_power_monthly_level`, `caiso_scarcity_pricing`, `capacity_deliverability_limits`);
`mode: backcast`; `gas_price_override` 6.45 / 2.54 / 2.19 / 3.52; `git_sha 8d627e64`. **Load-bearing:**
`resolved_inputs.seam_import_cap` reads **`source: "mic_partition"`** on all four (2022 `cap_mw` **15780.0**
— the predecessor's own recorded value; 2024 **16452.0**), so **no bundle solved on the retired fitted
fallback scalar** (rules 20 `[R-DOF]` / 24 `[R-REGISTRY]`).

### §3.3 — Restored in place, with NO re-registration

The sidecars and run payloads already existed and were correct; only the bundles they name were missing.
So the restored years were composed into **the paths the sidecars already point at** —
`results/calibration/caiso269_lateevening_span/` (2023-2025) and `caiso269_lateevening_2022/` — the two
`.gitignore` lines were lifted with the incident recorded in place, and the bundles committed **slim** per
the §8 rules (6.9 MB; `dispatch/`, `floors/`, `unit_hourly`, `network` and the root parquets all excluded).

**Zero `frontend/` changes, therefore zero registration race** with the SPP/NYISO/PJM/MISO lanes
registering concurrently. Run ids, dates, determinations, the rule-30 fold and the keeper pill are all
untouched — a re-registration would have risked a second card for one configuration, which rule 30
`[R-TOUCHPOINT-FOLD]` exists to prevent.

`legitimacy_diagnostics.json` and `calibration_attestation.json` were regenerated by their **standalone,
bundle-scoped** tools (`legitimacy_diagnostics.py --bundle … --json-out`, `gen_caiso269_attestation.py
--bundle …`), neither of which touches `frontend/`. **`metrics.json` is NOT restored** — only
`dashboard_add_run.py` writes it, and that is a registration. Stated as a cost, not hidden: a later session
wanting the scored metrics re-runs the scorer over the restored hourlies.

## §4 — The four STOP conditions, as pre-registered

| gate | condition | measured | verdict |
|---|---|---|---|
| **G-DRIFT** | every changed hunk between the keeper's arm SHA and HEAD is INERT for CAISO | 11 files, all INERT (197 of 198 changed benchmark leaves under `/isos/MISO`, zero CAISO; SPP-gated curtailment ceiling; NYISO-gated `nyiso_hub_gap_month_level` leaving the CAISO gas leg untouched; 11 PJM ORISPL codes) | **PASS**, and now **confirmed by measurement** via G-REPRO |
| **BIND CHECK** (card 0(e)) | exactly one differing `ScenarioConfig` field; the tranche reprices at the raw hub | one field on both bundles; resolver `caiso_lateevening_clean` False→True with all three siblings True→True; the name is in `_CAISO_DSW_CLEAN_DEPTH_TRANCHES`; `TestPricing` 9 passed | **PASS** |
| **PARTITION GATE** (added by the addendum) | `check_clean_partitions(cfg, "CAISO", strict=True)` passes and the seam cap reads the published MIC partition | passes on both recipes; `mic_partition` on all four solved years | **PASS** |
| **G-REPRO** | each year reproduces the published C3a to ≤ 0.05 pp | 0.0006 / 0.0009 / 0.0041 / 0.0000 pp, and C3b to 0.0000 | **PASS** |

## §5 — Governance record

* **Rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`.** Nothing armed, nothing tuned, no offer-curve multiplier, no
  adder/offset/haircut/proxy, no pin to actuals. The re-solve is the keeper's own recipe.
* **Rules 20 `[R-DOF]` / 24 `[R-REGISTRY]`.** Zero new free parameters; DOF ledger unchanged at 9 / 6. The
  partition gate is what kept a **fitted** import scalar out of all four bundles.
* **Rule 15 `[R-DASHBOARD]`.** The keeper's `hourly/` sidecars (`class_hourly_<year>`, `system_<year>`,
  plus `class_band_hourly` and `storage`) are committed for the first time. `reserve_family_<year>` is
  **absent by construction, not by omission**: CAISO's keeper runs no reserve co-optimisation
  (`caiso_reserve_coopt` / `energy_reserve_coopt` both `False`), so no reserve families exist to write.
* **Rule 30 `[R-TOUCHPOINT-FOLD]`.** The 2022 touchpoint keeps its `holdout.keeper` stamp and its fold; no
  id, determination or panel changed.
* **Rule 32 `[R-SHARD]`.** The parent ran **zero LP** throughout — phase 0, the bind check, the partition
  build, verification, composition and scoring are all zero-LP parent work. One year per shard, own branch,
  own out-dir; per-year dirs stay out of `main` (rule 32(d)).
* **Rule 31 `[R-RETAIN]`.** **Nothing deleted.** See §7.
* **Rule 25 `[R-ISO-SCOPE]`.** CAISO only. The parity gate's pre-existing RED on seven **ERCOT** bundles
  (`ercot262_arm_2021..2025`, `ercot264_repro_2023/2025`) is another lane's and was left untouched.

## §6 — Cost, and the defect that was mine

**The attempt-1 shard fleet — four containers, ~10–22 minutes each — produced no LP and no artifact.**
The cause was one defect and **it was mine**: the PRECOMMIT's setup block omitted the clean-partition
build. `data/clean/` is derived and gitignored, so a fresh container starts empty, and
`check_clean_partitions(…, strict=True)` is fatal there **by design** — because the fallback is a retired
fitted scalar that once re-armed across five keeper promotions (caiso-157) and recurred on the designated
keeper (caiso-188). **The guard was right and it saved the run.**

The shards gave the signal, not the diagnosis, exactly as `ADDENDUM-caiso269` §A5 predicts: two reported
`curate_capacity_deliverability.py` **missing** (it is not — only its *output* is); one armed a waiter for
`metrics.json`, a file the solve never writes; one reported "solved" and "blocked" in the same status line;
two backgrounded the solve and went idle mid-LP. **Every claim was re-verified against source in the parent
before any action, and none was acted on as given.** The rev2 prompt fixed all four failure modes.

Full record: `ADDENDUM-caiso270-clean-partition-repin-2026-09-10.md`, pushed **before** the rev2 fleet's
first LP so it could not be shaped by a result.

## §7 — Disclosures against interest

1. **The session did not improve the model.** It closed its own charter by measurement and restored an
   artifact. No criterion moved, and none was supposed to.
2. **The chartered lever had already been adjudicated** by caiso-229 on 2026-08-31, bounded at
   $0.017/MWh, with the cell reading `K` ever since. Checking the matrix **before** proposing (rule 28(a))
   is what surfaced it; a session that had gone straight to a solve would have spent four shard-years
   rediscovering it.
3. **Four shard-containers were spent for nothing**, on my omission (§6).
4. **`metrics.json` is not restored** (§3.3), so the restored bundles are not byte-complete against the
   predecessor's shape.
5. **The 2022 reserve-headroom figure in the FINDING is a BOUND, not a measurement** — it says what `R`
   would have to be, not what it was.
6. **G-REPRO is a reproduction gate, not a skill claim.** It shows the re-solve equals the keeper; it says
   nothing about whether the keeper is right. And since `[R-HOLDOUT]` was removed (2026-09-09), no CAISO
   year is a certified out-of-sample number.

## §8 — RULE 31 `[R-RETAIN]`: WHAT IS ON DISK, AND THE QUESTION TO THE OWNER

**Nothing was deleted.** The four per-year shard bundles — `results/calibration/caiso270_keeper_{2022,
2023,2024,2025}/`, ~87–101 MB each **including `dispatch/`** — are:
* on **this container's local disk**, gitignored, and **will not survive session end**; and
* on their **shard branches** `claude/caiso270-keeper-{2022,2023,2024,2025}`, which carry the full bundles
  including `dispatch/` and `floors/`. **Those branches are the durable copy** — a promotion or a
  unit-level diagnostic would not need a re-solve, but the branches must not be deleted for that to hold.

**The question I am putting explicitly:**

* **(a) Keep the shard branches.** They are the only surviving copy of the keeper's per-unit `dispatch/`
  and `floors/`. If they are pruned, the next unit-level CAISO question costs a four-year re-solve again.
  **This is my recommendation**, and it is the cheap half of the lesson this session just paid for.
* **(b) Whether `metrics.json` should be restored too** (§3.3), which means a re-registration and therefore
  a race with the lanes registering right now — I judged that not worth it today and did not do it.
* **(c) The successor charter.** `FINDING-caiso270` §6 names the +1 HR marginal-unit bias, low-gas /
  solar-glut limb (dHR up to +5.15 at ~$2/MMBtu). **No mechanism is proposed**; a successor session should
  name its external driver before it names a number.

**Next number: caiso-271.**

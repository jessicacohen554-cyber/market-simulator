# PRECOMMIT closeout-nwpp-anchor: re-solve NWPP 2019–2025 on the roster-free plant-basis anchor (2026-10-03)

**Charter:** owner ruling R-28 "Keep old figures, fix later" (PR #7076), plan §5.0 R-28 and §6.2 NWPP lane.
Desk: session_01ALecU5Wjde4tkbLrnMExT9. **Parent:** zero LP (rule 32). **Control (rule 29(b)):** the incumbent
keeper's committed bundle, `2026-10-02-w0-nwpp-fix2` (`results/calibration/w0_nwpp_span`, every leg at
`25da6022`). No control solve. **Phase 0:** `FINDING-closeout-nwpp-anchor-2026-10-03.md`.

## 1. What changes

There is no config delta and no new ScenarioConfig field. The keeper's recipe is replayed as recorded.

The one LIVE input is `data/raw/reference/nwpp_plant_basis_energy.csv`, re-derived from the source data on a
roster-free plant -> class map (FINDING §2). Per year, COL / NG / OTH move by 0.002–0.126 TWh. The net
anchored requirement changes by at most 0.0054 TWh per year (FINDING §3). SolveEpoch 2026-10-03a re-keys
backcast NWPP.

- **Mechanism cell:** `nwpp_demand_plant_basis`, NWPP shard **K** (the keeper's arm). This lane does not
  re-test the mechanism. It corrects the artifact's construction, which is a rule-14 / rule-23 data-provenance
  repair.
- **Prior R cells:** none touched. DO-NOT-REDO, per the charter: everything closed in HANDOFF-nwppnext7..22.
- **Forward story (rule 13):** unchanged. The anchor is backcast-measured and NWPP-only, and it is now a
  function of source data alone.

## 2. Shards

There are 7 shards, one per year 2019–2025 (rule 36), via
`scripts/shard_prompt.py --iso NWPP --all-years --sha <pin> --lane closeout-nwpp-anchor --bundle results/calibration/w0_nwpp_span`.
The budget is 120 minutes per shard (NWPP 2019 P0 is about 45 minutes cold, single thread). At most 6 are
alive at a time.

## 3. Readings, fixed before any number exists

**Scored on the composed span against the keeper:**

1. **C1 generation mix:** every class in band in every year where the keeper has it in band. This is the
   pass bar.
2. **C3a price mean 2023–25:** reported at full magnitude against the WEIM ELAP reference. The keeper reads
   −23.1 / −30.7 / −4.6 %. This is a report, not a bar.
3. **C4 coal 2023:** reported.
4. **Determination:** the keeper is NOT-YET, failing price_mean, price_shape and dispatch_corr. The
   expectation is that it stays NOT-YET with the **same failing-criterion set**. A sub-0.01-TWh requirement
   change re-split across hourly shapes is expected to move class energies by well under 0.1 TWh and C3a by
   under 1 pp.

**Decision rule:**

- **PROMOTE (recommendation, on structure)** when no criterion's status worsens in any year and readings 1–3
  hold. The decoupled anchor is the structurally correct input (rule 1), so promotion does not need a fit gain.
- **HOLD to the desk** when any criterion flips PASS → FAIL, any class leaves its band, or any year's C3a
  moves by more than 2 pp. A move that large is not explained by the input change, so it would be
  investigated as a solver-path or replay difference before any promotion.
- 2025 carries the EIA-923 data-drift label on every before/after card.

## 4. Addendum: desk HOLD (2026-10-03 01:31Z)

The desk ruled on sequencing at 01:31:00Z. It crossed with the shard launch at 01:31:02Z.

- **Ruling:** hold the shards and the merge of the re-key (the anchor CSV and SolveEpoch 2026-10-03a) until
  NWPP-NEXT-22 promotes or stands down.
- **Done:** all six launched shards were interrupted and archived while still PENDING. No work had started, no
  bundle existed and no branch was pushed. 2025 was never launched.
- **If NEXT-22 promotes:** merge main, re-pin on its keeper, re-run the G-DRIFT and append an addendum here
  before 7 new shards.
- **If NEXT-22 stands down:** launch on `w0_nwpp_span` at the pin, as §2 states.
- **To fold in if it lands first:** the desk's cross-ISO `NUCLEAR_MONTHLY_CF_BY_YEAR[NWPP]` 2019–22 repair goes
  into the same pin.

## 5. Addendum: re-pin onto the NEXT-22 keeper (desk "GO", 2026-10-03 01:57Z)

NWPP-NEXT-22 promoted: PR #7105, merged at `469ddcd7`.

- **Incumbent keeper:** `2026-10-03-nwpp-next-22b-w0` (`results/calibration/nwppnext22b_span`). Its legs sit at
  `2b8da72a`, replaying `w0_nwpp_span` with the priced interface, priced interchange and seam measured limits
  armed.
- **This lane:** main is merged into `claude/closeout-nwpp-anchor` (`675a707c`).

**Anchor at the merged HEAD.** I re-ran `regenerate_clean --solve-profile NWPP` and then the derive. The output is
byte-identical to the committed CSV (`diff` rc 0), so main's changes to eia923 / campd / coal / bench_multiclass
do not move it.

**G-DRIFT vs 2b8da72a** (90 commits, 45 files on the solve and scoring path; every hunk classified against code):

- **LIVE (solve):** `nwpp_plant_basis_energy.csv`.
- **LIVE (cache key only):** SolveEpoch 2026-10-03a and its ledger entry.
- **INERT, everything else.** Most of it comes from two refactor commits: e86fc2c5 "Vectorize inert hot paths" and
  b767e519 "Trim LP handoff copies, memoize".
  - `kron_hours` builds the same matrix as `sp.kron`, byte for byte; 200 randomized equivalence trials, no LP.
  - The outage-window slice selects exactly the old mask's elements.
  - Month×hour-of-day percentile tables give the same order statistics.
  - The rest is iterrows→zip and memo changes with identical values, or hunks scoped to other ISOs (CAISO, SOCO,
    ERCOT, NYISO, SPP; the SPP split-remap file needs `campd_split_remap_companions`, which is false in the NWPP
    recipe).

**Solve.** 7 shards, one per year 2019–2025, replaying `nwppnext22b_span` (`replay_keeper --years Y`, no `--set`)
at the post-merge `main` SHA. The budget is 120 minutes per shard, with at most 6 alive at a time.

**Readings.** The §3 readings and decision rule are unchanged. The control is now `nwppnext22b_span`: C1 in band
where that keeper is; C3a 2023–25 against WEIM ELAP at full magnitude; C4 coal 2023 reported.

**Not in this pin:** the cross-ISO `NUCLEAR_MONTHLY_CF_BY_YEAR[NWPP]` repair. It is not on main, so it rides the
next NWPP solve.

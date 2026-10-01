# PRECOMMIT caiso-292 — re-measure the RA-bridge screen split on the LIVE keeper

**Lane:** caiso-292 · **Date:** 2026-09-20 · **LP: ZERO** (rule 32 `[R-SHARD]` (a) — the parent
never solves). Nothing is armed, no `ScenarioConfig` field is added, no constant moves, no derive
is re-run.

---

## 1. The object, and the correction that defines it

The lane instruction carries caiso-286's open question — *of S3_5's 1,593.4 MW, 270.279
mean-belly-MW pass the restart inequality yet are floored by nothing; which screen removed them,
the surplus decommit screen or the `startup_aware` gap-merging channel?* — and costs it at "now
zero-LP, but only after the fleet-rebuild repair".

**That question was already answered.** `docs/RESULT-caiso287-startup-decommit-split-2026-09-19.md`
§2 split it **unanimously across all four years**, verdict **(A) GAP-MERGING DOMINANT**, with the
decommit screen exonerated; the probe is `scripts/probes/caiso287_screen_split.py` and its
artifacts are `results/calibration/_caiso287_screen_split_{2022,2023,2024,2025}.json`. What caiso-287
left open is **not** the split: it is the **admissibility** of `caiso_ra_bridge_startup_aware`
(§5 — its anchor test prices runs off the model's own P0 duals, the circularity
`scenarios.py:12824` already refused for ERCOT), and that is in owner court and is **not decided
here** (lane instruction §3).

**What IS open, and is this lane's object:** caiso-287 measured the split on its own keeper's
bundles (`caiso287_instr_*`, the caiso-275-era recipe). The designated keeper is now
**`2026-09-20-caiso-290-leftedge`** (bundle `xiso8_leftedge_span`), whose defining delta —
`gas_flow_date_year_start_package` — **moves `mc_base` at the year edges**, and `mc_base` is an
input to *both* screens (the run-anchor margin and the gap hold-cost). So the split's verdict is
**not inherited**; it has to be re-measured on the live keeper, which its committed
`hourly/p0_dispatch_<y>.parquet` + `hourly/p0_prices_<y>.parquet` now make a zero-LP question.

---

## 2. Method — caiso-287's probe, unmodified in its arithmetic

`scripts/probes/caiso292_screen_split_keeper.py` **imports** caiso-287's own
`run_detector` / `belly_mean_mw` / `read_p0_dispatch` / `read_p0_prices` /
`zone_names_from_fleet` / `surplus_floor_value` / `derive_belly` and re-points the bundle. Nothing
about the measurement is re-implemented, so it cannot drift from the thing it reproduces.

The 2×2 is caiso-287's: the PRODUCTION detector
(`model.commitment.caiso_ra_mustoffer_min_gen`) called four times per year with the keeper's own
arguments — `M_both` (armed), `M_sa` (`startup_aware` only), `M_dc` (`bridge_decommit` only),
`M_none` — and `R_SA = M_none − M_sa`, `R_DC = M_none − M_dc`, `R_total = M_none − M_both`.

The fleet is the sanctioned `scripts.lib.bundle_fleet.reconstruct_bundle_fleet` rebuild, which is
**row-aligned with the keeper's committed P0 only because of this lane's first commit** (e255252e:
the rebuild must splat `replay_keeper.DERIVED_RUN_YEAR_INPUTS`; without it the rebuild is a
1,905-row superset of the solve's 1,705 and `p0_uid != uid` fails the probe's own G-R1).

---

## 3. CUTS — INHERITED VERBATIM, NOTHING NEW IS CHOSEN

From `docs/PRECOMMIT-caiso287-startup-decommit-split-2026-09-19.md`, unchanged:

* `DOMINANCE_FRAC = 0.70` of `R_total`;
* `NO_OBJECT_MW = 10.0` mean-belly-MW;
* the five verdict words — `(A) GAP-MERGING DOMINANT`, `(B) DECOMMIT DOMINANT`,
  `BOTH-SUFFICIENT`, `SPLIT`, `NO-OBJECT`;
* the belly: caiso-285's rule, the lowest 876 h of the **keeper's own** model net load
  (`demand − wind − solar`), built from the keeper and never from the run being measured;
* `MIN_LOAD_FRAC = 0.26` and the `KEEPER_POSTURE` re-assertion, both read back from the probe
  bundle's own `run_config.json` at runtime rather than trusted.

## 4. What this lane DOES declare ex ante

**G-V — harness validation, and it binds first.** The probe runs end-to-end on
`caiso287_instr_2022` (recovered by full immutable SHA `bb3034214d1d3da70d0db8d8435540f82387222d`,
the pin `.gitignore` records) and must reproduce
`results/calibration/_caiso287_screen_split_2022.json`:

| tier | condition | reading |
|---|---|---|
| **EXACT** | every `M_*` within **1e-6** mean-belly-MW, belly sha16 equal | harness bit-reproduces caiso-287 |
| **VALID** | every `M_*` within **0.05** mean-belly-MW (caiso-287's own `G_R3_TOL_MW`), belly sha16 equal | harness valid, HEAD drift immaterial |
| **FAILED** | anything else | **the run is reported FAILED and NOTHING is quoted from it** |

caiso-287's **G-R2** (the detector's armed floor reproduces the committed `floors/*.npz` on every
RA-attributed gen-hour) also runs on that bundle and must **PASS**.

**G-R2 is NOT AVAILABLE on the keeper, and that is declared now rather than discovered later.**
`xiso8_leftedge_span` is a slim bundle: it commits no `floors/` and no `dispatch/`, so there is no
committed floor array to difference the reproduction against. The keeper numbers therefore rest on
(a) G-V above, (b) the fleet/P0 unit-id identity check (G-R1), and (c) G-D below — and the RESULT
says so in place. A keeper number is reported as a **mechanism-faithful reproduction**, never as
"the floor the solve wrote".

**G-D — independent cross-check on the keeper.** The detector's `screen_stats` drop rate must
reproduce caiso-291's published census on this same bundle — **64.9 / 76.3 / 89.0 / 93.0 %** for
2022 / 2023 / 2024 / 2025 — to **±0.1 pp**. A miss is reported, not smoothed.

**Belly provenance.** The keeper's own 2024 belly is reported with its sha16 and its **hour overlap
with caiso-285's frozen 876-hour set** (`c5948fb0d43620a1`). The frozen set is *not* imposed on the
keeper: a new keeper has its own net load, and substituting the old hour set would measure the old
keeper's belly on the new keeper's floors. The overlap is reported so the two lanes' numbers can be
compared rather than conflated.

## 5. The pre-registered expectation, and its falsifier

**Expected:** caiso-287's `(A) GAP-MERGING DOMINANT` survives on the live keeper in all four years,
because the left-edge gas repair moves `mc_base` at the year boundaries only and the screen's
action is concentrated in the belly.

**Falsifier, stated so it cannot be explained away:** any year returning `(B) DECOMMIT DOMINANT`,
`BOTH-SUFFICIENT`, `SPLIT` or `NO-OBJECT` is reported **at full magnitude and in the headline**, and
the mechanism-matrix cell is stamped with whichever verdict the measurement returns. Nothing is
armed or disarmed on the outcome either way (rule 1 `[R-STRUCT]`: the split is a diagnosis, not a
lever), and the `startup_aware` admissibility question stays where caiso-287 and the lane
instruction put it — **owner court, unruled**.

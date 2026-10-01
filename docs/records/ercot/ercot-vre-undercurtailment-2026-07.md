# ERCOT wind/solar under-curtailment — root cause + fix plan (2026-07-06)

**Scope.** Follow-on from the ERCOT HSL 2024/25 intake
(`docs/ercot-hsl-2024-25-intake-attempt-2026-07.md`) and its `ercot38`
re-validation probe (`docs/calibration-log.md`, 2026-07-06 entry). Measured
HSL made a real, non-obvious problem visible for 2024/25 that was already
present (smaller) in 2023: **the model dispatches wind and solar well above
what ERCOT actually delivered, which mechanically displaces the non-must-run
thermal fleet — mostly gas — by multiple TWh.** This is a design/plan
document; no model code changed here (the one exploratory config flag flip
used to validate the hypothesis is a `--set` probe, not a merged change).

## 1. The numbers

Non-CHP grid generation, model vs EIA-930 actual (`ercot38`, the measured-HSL
recipe — see full tables in `results/calibration/ercot38_measured_hsl_2425`):

| year | fuel | model TWh | EIA-930 TWh | diff % |
|---|---|---|---|---|
| 2023 | wind | 110.84 | 107.99 | +2.6% |
| 2023 | solar | 33.56 | 31.87 | +5.3% |
| 2024 | wind | 116.28 | 111.54 | +4.3% |
| 2024 | solar | 49.74 | 47.68 | +4.3% |
| 2025 | wind | 120.38 | 115.12 | +4.6% |
| 2025 | solar | 70.61 | 67.39 | +4.8% |

Gas absorbs almost exactly the mirror image (2024 gas −2.4%, 2025 gas −6.4%)
— renewables are decision variables directly on the energy-balance LHS
(CLAUDE.md rule #3), so every extra MWh of wind/solar the LP clears is one
less MWh the flexible thermal fleet needs to cover. This is what pushed
`ercot38`'s **C2 system volume (gas) from CAVEAT into FAIL** (2025 gas
−5.0%→−6.4%) even though the underlying renewable *input* data (HSL) is more
accurate than the G7 gross-up it replaced.

The direct diagnostic — modeled vs ISO-*reported* curtailment (table [3e] of
the calibration report; only available where a measured HSL parquot exists,
i.e. all three years now) — shows the model curtails at roughly a third to a
half of ERCOT's own reported rate, in **every** year including 2023, which
already had measured HSL before this session:

| year | fuel | model curt % | ISO-reported curt % | ratio |
|---|---|---|---|---|
| 2023 | wind | 2.16 | 4.67 | 0.46× |
| 2023 | solar | 1.32 | 6.29 | 0.21× |
| 2024 | wind | 2.45 | 6.01 | 0.41× |
| 2024 | solar | 1.82 | 7.35 | 0.25× |
| 2025 | wind | 3.10 (tbd, see §4) | — | — |

**This is not a new bug the HSL intake introduced.** It was already present
and quantifiable in 2023 (which has had measured HSL since before this
session). The 2024/25 intake didn't create the gap — it just extended
*visibility* into it for two more years, and pushed the annual dispatch far
enough that C2 crossed from CAVEAT to FAIL. The real fix is a dispatch/
mechanism gap, not a data-quality problem with the HSL series itself (the
HSL file's own delivered column already tracks EIA-923 to within
+0.1%/−0.2% for wind — see the intake doc).

## 2. Why the obvious "anchor to EIA-930, keep HSL's ratio" fix doesn't apply here

This mechanism **already exists** in
`market_sim.data.renewables.hsl_potential_mw` (`_HSL_COVERAGE_RECONCILE_TOL`,
currently 0.98): when a HSL source's own delivered column (`*_gen_mw`)
undercounts the EIA-930 system total by more than ~2% — as the 2023 UMass
partial-footprint reconstruction does — the whole series is scaled UP to the
EIA-930 level *while preserving the source's own measured curtailment ratio*
(`delivered/HSL`). That's exactly "anchor the level to EIA-930, keep HSL's
shape/ratio."

It's a no-op here because **there's no coverage gap to fix**: the published
NP4-732/737 files' own delivered column already matches EIA-930/EIA-923
within ~0.1-0.2% for wind (see the intake doc's validation table) — the
reconciliation's guard condition (`src_gen < 0.98 * delivered_mwh`) is false,
so `hsl_potential_mw` returns the file's HSL series unscaled, correctly. The
NP4-732/737 upload is the authoritative full-footprint ERCOT-published
potential; its own recorded delivered number is not wrong. **The gap is that
the model's own LP dispatches more of that legitimate potential than ERCOT's
real grid did** — a mechanism gap downstream of the input, not an input
problem.

**A more aggressive version of the same idea — scale the HSL *ceiling* down
using the file's own curtailment ratio so the model's dispatch lands near the
delivered level regardless of coverage — would not be a legitimate fix.**
Mathematically it would compute a ceiling that, if the LP dispatches at
*today's* level of curtailment-avoidance (roughly zero, since renewables have
~$0 marginal cost and no binding constraint stops them), still overshoots;
pushed further (i.e., deliberately picking a ceiling low enough to force the
model near the measured delivered profile) crosses into feeding the model a
measured *outcome* as an input — precisely what CLAUDE.md rule #13 forbids
("pinning a unit to its observed generation... no pinning the backcast to
actuals"). The uncurtailed potential is a real physical ceiling ERCOT itself
measured; artificially lowering it to force a match doesn't fix the
mechanism, it hides it.

## 3. The real, structural mechanism: measured transmission (GTC) limits are gated off and were never active

Every solve log for every year (2023, 2024, 2025 — both the `ercot34` keeper
and the `ercot38` probe) carries this line:

```
INFO: gtc-limits: no clean partition for ERCOT <year> (supply the NP6-86
      archives and run scripts/data/curate_gtc_limits.py)
WARNING: ercot_gtc_limits_measured: no gtc-limits clean partition for
      <year> — static TTC kept
```

`ScenarioConfig.ercot_gtc_limits_measured` (default off; `src/market_sim/
config/scenarios.py:3043`) is the seam for ERCOT's measured Generic
Transmission Constraint limits — the real, physical mechanism ERCOT uses to
curtail wind (mostly West/Panhandle export-constrained) and, to a lesser
extent, solar. It has **never fired for any registered ERCOT keeper or
probe**, because `data/clean/gtc-limits` (gitignored/derived, per
`CLAUDE.md`'s `data/clean` convention) was never regenerated in the
containers those solves ran in.

**The raw source data has been sitting in the repo the whole time.**
`data/raw/iso-specific-transmission/SCEDBTCNP686_SCEDBTCNP686_<year>.parquet`
already covers 2020-2025 (committed, not gitignored). Running
`python scripts/data/curate_gtc_limits.py` (no new intake, no network access, just
re-curates the already-present archives) populated the clean partition for
every year in ~seconds this session:

```
2023: 13452 (gtc, hour) rows across 17 GTCs
2024: 15273 (gtc, hour) rows across 19 GTCs
2025: 21864 (gtc, hour) rows across 23 GTCs
```

The model's reduced 8-zone topology maps 4 of ERCOT's real GTCs onto 3 links
(`constants.ERCOT_GTC_LINK_MAP`) — exactly the wind/solar-heavy corridors
where curtailment concentrates:

| GTC | link(s) | static `ttc_mw` today | measured active-hour range (2023) |
|---|---|---|---|
| PNHNDL | Panhandle→North | 2680 | 1848–8499 MW (1312 active hours) |
| WESTEX | West→North (×0.727) | 7300 | 6027–7730 MW (1881 active hours) |
| WESTEX | West→South_Central (×0.273) | 2700 | 2260–2899 MW |
| NE_LOB | Northeast→North | 1300 | 548–1408 MW (3640 active hours) |

The static numbers are a single flat value for all 8760 hours; the measured
series shows the constraint is genuinely time-varying and, for Panhandle
particularly, sometimes far tighter than the static fill (1848 MW vs. the
2680 MW static value) — exactly the kind of hour that should force real
curtailment and currently doesn't, because the model never sees it.

## 4. Validation — not yet run; this is the next session's first step

A one-delta probe was started this session (`scripts/replay_keeper.py` on
the `ercot38` bundle with `--set ercot_gtc_limits_measured=true`, nothing
else changed, `--out-dir results/calibration/ercot39_gtc_measured_probe`)
to test whether activating the already-curated measured GTC series closes
the gap. **It was stopped mid-solve (partway through 2023) and the partial
output directory removed — no `ercot39` bundle or dashboard entry exists.**
This handoff hands off the mechanism and the evidence for *why* it's the
right lever to pull, not a validated result.

**Next session: re-run exactly that probe first.**
`data/clean/gtc-limits` is gitignored — confirm
`python scripts/data/curate_gtc_limits.py` has been (re-)run in the fresh
container before solving (it populated instantly from the already-committed
raw archives last time, ~seconds, no network access). Then:

```
python scripts/replay_keeper.py results/calibration/ercot38_measured_hsl_2425 \
  --out-dir results/calibration/ercot39_gtc_measured_probe \
  --set ercot_gtc_limits_measured=true \
  --note "one-delta probe of ercot38: measured NP6-86 GTC transmission limits"
```

Expected signal if the hypothesis holds: 2023-2025 wind/solar curtailment %
rises toward the ISO-reported rate, C2 system volume (gas) moves back off
FAIL, without regressing C3a/C5c (the two criteria `ercot38`'s measured HSL
already improved). Register it on the dashboard as a probe either way (rule
#15) before deciding whether to pursue §5's build order further.

## 5. Recommended build order

1. **Enable and validate `ercot_gtc_limits_measured` as the standing ERCOT
   default**, not a probe flag, once `ercot39` (or a fresh equivalent run)
   confirms it moves curtailment toward the reported rate without
   regressing other criteria. This requires no new data intake — the raw
   NP6-86 archives are already committed; `curate_gtc_limits.py` just needs
   to run before any ERCOT solve (worth adding to whatever pre-solve setup
   step / `regenerate_clean.py` invocation each session already does — it's
   already in `regenerate_clean.py`'s datatype list, so this may just be a
   "remember to run it" gap, not a code gap).
2. **If GTC alone doesn't close the gap**, the next real (not fitted)
   mechanism to check, in order of how directly it's already evidenced in
   this repo:
   - Oversupply / negative-price dumping: confirm `dump_cost` (the
     objective's negative-MC guard, `model-methodology-spec.md`) is actually
     binding during the measured negative-price hours (`ERCOT West
     net-load gas step` diagnostics already track a `measured-neg-day`
     frequency per year in the solve log — cross-check that against wind
     curtailment timing).
   - Storage absorption: if storage is arbitraging away exactly the hours
     real curtailment would otherwise occur, that's a legitimate real
     mechanism competing with curtailment, not a bug — but worth confirming
     it isn't systematically eating the *wrong* hours (e.g. charging past
     the point where transmission, not storage headroom, should be the
     binding constraint).
   - A derived, forward-admissible curtailment-share driver in the style of
     the AS co-opt plan's WS-A (`docs/handoffs/ercot-as-coopt-plan-2026-07.md`
     §4 WS-A): a function of net-load percentile / hour-of-day / season,
     fit to the *measured GTC binding frequency and RTOLCAP-style supply
     shares*, never to the price or volume residual. Reach for this only if
     the real GTC mechanism (step 1) is insufficient on its own — it's a
     fallback, not the first move, since #1 is a real, already-measured,
     zero-new-tunable mechanism and this is a derived formula with its own
     identification burden (rule 23).
3. **Do not** scale/pin the HSL potential itself to close the gap (§2) —
   that's the wrong layer and risks becoming a measured-outcome pin.
4. **Do not** add a residual-tuned curtailment adder or haircut on renewable
   dispatch — same rule-13 concern, and it would be "reaching the right
   number through a mechanism that isn't real" (CLAUDE.md rule #1).

## 6. Guardrails (explicit, per CLAUDE.md rules #1/#13/#14)

- The HSL potential series is correct as intaken; do not adjust it to
  compensate for a dispatch-mechanism gap (§2).
- The fix is a real market mechanism (transmission congestion) that ERCOT
  itself already measures and publishes (GTC shadow prices/limits) — this
  passes the rule-13 admissibility test cleanly (regenerates forward from
  forward transmission topology/build-out, responds to changed conditions).
- Any coefficient introduced in a fallback derived-driver approach (§5 point
  2, last bullet) must cite its identification source (measured GTC binding
  frequency / RTOLCAP-style shares) in the run's DOF ledger before it can
  enter a keeper (rule #21), and must not be fit to the price or volume
  residual (rule #23).
- `ercot_gtc_limits_measured` flipping default-on for ERCOT is a structural
  change and should go through the same single-delta validation discipline
  as any other keeper-affecting flag (rule #12/#15): register the probe,
  score it, let the owner decide on promotion — same pattern as `ercot38`.

## References

- `docs/ercot-hsl-2024-25-intake-attempt-2026-07.md` — the HSL intake this
  follow-up is downstream of.
- `docs/calibration-log.md`, 2026-07-06 entry — `ercot38` C-score comparison.
- `src/market_sim/data/renewables.py` — `hsl_potential_mw`,
  `_HSL_COVERAGE_RECONCILE_TOL`.
- `src/market_sim/data/gtc.py`, `scripts/data/curate_gtc_limits.py`,
  `scripts/data/derive_ttc_limits.py` — the measured-GTC seam, already built,
  never activated for a committed ERCOT run.
- `src/market_sim/config/constants.py:ERCOT_GTC_LINK_MAP`,
  `src/market_sim/config/iso_configs.py` (`_ercot_config` `TransferLink`
  list) — the static `ttc_mw` values the measured series would replace.
- `docs/handoffs/ercot-as-coopt-plan-2026-07.md` §4 WS-A — the precedent
  pattern for a derived, forward-admissible driver, if needed as a fallback.

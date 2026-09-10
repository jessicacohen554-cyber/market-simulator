# ADDENDUM — SPP-64 SCREEN shard (2023). HEARTBEAT: written BEFORE any LP.

**Lane** SPP-64 SCREEN · **Branch** `claude/spp64-screen-2023b` ·
**Charter** `docs/handoffs/PRECOMMIT-spp-64-stgas-selfcommit-2026-09-10.md`

## Pin (HARD STOP 1 — verified)

`git rev-parse HEAD` = `967db1ff63049b18d38d2de36838593054b6bed3` — matches the shard pin.
No `git pull` / `fetch` / `rebase` / `merge` will be run before the final push (rule 32 `[R-SHARD]` (c)(1)).

## The one solve this shard runs

```
python3 scripts/replay_keeper.py results/calibration/spp62_span \
  --years 2023 --out-dir results/calibration/spp64_screen_2023 \
  --set st_gas_mustrun_per_plant=true
```

Control = the keeper's **committed** bundle `results/calibration/spp62_span`, DIFFERENCED, never
re-solved (rule 29 `[R-SCREEN]` (b) form 4; the G-DRIFT audit is PRECOMMIT §7).
`results/calibration/spp64_*/` is gitignored. **Rule 31 `[R-RETAIN]`: nothing is deleted.**

## §6 gate table — PRE-REGISTERED, values BLANK until the solve lands

`C1 ST_GAS` is the TARGET and is **NOT** a gate in either direction. Every gate below is STOP-only:
it may kill the arm, it may never promote it.

| gate | asks | STOP bar | MEASURED (filled after the solve) |
|---|---|---|---|
| **G-1** config identity & liveness | `st_gas_mustrun_per_plant` true; `st_gas_mustrun_p25_level` false; ten fossil classes 0.93 × 4 bands; coal supply census 32 lines / `6193,prb` present | any mismatch | `st_gas_mustrun_per_plant` **True**; `st_gas_mustrun_p25_level` **False**; **10** classes 0.93×4 (`offer_curve_by_group` byte-identical to keeper); **32** lines; `^6193,prb,` **1** — **PASS** |
| **G-2** reach | ΔST_GAS gross dispatch direction & order of magnitude | outside **[+2.0, +7.5] TWh** | **+2.3314 TWh** (7.0867 → 9.4181) — **PASS** |
| **G-3** allocation identity | added ST_GAS energy lands in the floored hours (`min_gen_mechanism == MECH_ST_GAS_MUSTRUN_PER_PLANT`) | **< 0.80** of the increase inside the floored-hour set | **1.0002** inside (+2.3319 of +2.3314 TWh) — **PASS** |
| **G-4** no new forcing | `dump` = 0; no non-ST_GAS class gains min_gen; slack in envelope | dump > 0, or any non-ST_GAS class gains min_gen, or slack **> 370.102 MWh** | dump **0.000**; slack **0.000 MWh**; min_gen gained by **ST_GAS only** (+3.8720 TWh) — **PASS** |
| **G-5** no non-target regression | C3a within ±10 %; C3b ≤ 0.20; C2 family in band (`scripts/lib/spp63_g5.py`, validated on the keeper first: 2023 C3a 25.65 / C3b 0.172) | any **PASS → FAIL** | C3a **25.65→25.38** (−1.05 %); C3b **0.172→0.173**; C2 gas/coal PASS→PASS; **0 PASS→FAIL** — **PASS** |
| **G-6** displacement | no C1 class currently IN band pushed OUT of the ±8.00 TWh band; reads the arm's neighbours, never ST_GAS | any in-band class leaves the band | **no** in-band class leaves ±8.00 TWh (largest move CC_REGULAR −3.569→−4.127) — **PASS** |

2023 control C1 deltas vs actual (the G-6 baseline): CC_REGULAR −3.569, CT_PEAKER +2.407,
COAL_PRB +1.598, COAL_LIGNITE −2.103, CC_CHP +0.116, ST_CHP −0.230.

**No bar above may be re-cut by this shard.** A failing gate IS the result and will be reported as
such. Filled table + the class-delta table, prices, slack/dump and the one-line verdict land in
`docs/RESULT-spp64-screen-2023.md` on this branch.


## FILLED — verdict

**All six §6 STOP gates PASS. Verdict: PROCEED TO SPAN.**
Full evidence, the class-delta tables, prices and the non-gating D-4 unit-conduct finding:
`docs/RESULT-spp64-screen-2023.md`.

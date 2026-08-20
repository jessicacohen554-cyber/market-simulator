# PREREG nyiso-147 — measured CHP BTM electric share (arm A) + the reserve-duty re-arm (arm B)

Committed BEFORE any arm solves. Session nyiso-147; control
`2026-08-20-nyiso-147-control` = replay of the keeper
`2026-08-19-nyiso-146c-state-scoped` at this session's HEAD (bundle
`results/calibration/nyiso147_control`), verified **byte-identical** P1 zonal
prices to the committed keeper hourlies in all three years before this
document was written (max |Δprice| = 0.0). Years 2023 2024 2025, one bundle
per arm, arms sequential (rule 12), holdout freeze ACTIVE (rule 22 — nothing
outside 2023–2025 is solved, scored or registered; the CY2022 Gold Book
column below is input collection, unrestricted per the 2026-08-06 clause).
Phase-0 identification: `FINDING-nyiso147-upstate-price-root-cause-2026-08-20.md`.

## ARM A — `nyiso_chp_btm_measured` (`2026-08-20-nyiso-147a-chp-btm`)

### A.1 Mechanism and identification (all fixed before any solve)

One new default-off `ScenarioConfig` boolean. Armed, the CHP
steam-following carve prices each NYISO CHP plant's behind-the-meter share
from the rule-23 artifact `chp_btm_share_measured_NYISO.csv`
(`scripts/data/derive_nyiso_chp_btm_share.py`):

    btm_pct = 100 x clip(1 − Gold Book net energy / EIA-923 net generation, 0, 1)

pooled pairwise CY2022–2024 — the plant's own two published meters (NYISO
settlement vs EIA net-of-station-service), so the share regenerates each year
and responds to changed host arrangements (rule 13). It replaces
`CHP_BTM_PCT_BY_SECTOR["merchant"] = 35.0`, whose own citation reads
*"residual-identified, forecast-risk — no independent source yet"* (rule 14),
for exactly the 16 plants the PTID-verified station join covers; a CHP plant
absent from the Gold Book table (Cornell, Riverbay, Ticonderoga, World Gen X,
the <5 MW tail) keeps the sector default. **Zero fitted scalars** (rule 21):
every value is a ratio of two published meters, computed blind to any model
residual; the artifact is frozen at the committed derive output. Consumed by
the three legs that shared the default — the LP capacity carve
(`data/fleet/assembly.py`), the BTM add-back
(`run_calibration_full._btm_frame`), and the bench `classFull`/gas-family
subtrahend (`render_calibration_html._btm_share`) — so model and benchmark
stay on ONE share by construction. NYISO-only (rule 25).

Fleet-side liveness measured ex ante (`fleet_only`, no LP), grid pmax:
54547 Independence 752.6 → **1,157.8** MW; 50006 Linden 633.2 → 757.8;
56259 Empire 424.9 → 652.4; 54914 BNY 209.3 → 312.9; 2493 East River
400.1 → 615.3; 10725 Selkirk 490.0 → 753.8; 54041 Lockport 143.8 → 221.3;
10025 RED-Rochester ~46 → **2.6** (the correction cuts both directions).

### A.2 Falsifiable predictions (ex ante)

1. The west margin re-lands in Independence's econ band: Upstate_West's
   annual equal-hour price error (control **+$7.80 / +$3.75 / +$5.99** vs the
   actual RT 25.32/33.06/55.52) falls materially in every year, most in 2023.
2. Central-East separation share rises above the control's 28.5 % (2023).
3. Downstate prices FALL (Linden/BNY/East River capacity is restored into
   NYC): NYC/LI zone errors go more negative in 2024/2025 — predicted and
   accepted; the gate is the system C3a band, not the zone sign.
4. The bench CC_CHP `classFull` actual RISES (the 35 % subtrahend was
   deflating the benchmark ~1.4 TWh/yr for Independence alone); the model's
   CC_CHP dispatch rises toward it. Blast radius disclosed: the NYISO bench
   parts for 2023–2025 regenerate at registration (the pjm-130/pjm-147
   precedent) and every registered NYISO run re-scores against the truer
   benchmark.

### A.3 Kill gates (arm A)

* **A-K1 EXACTNESS** — exactly one differing `scenario_config` field vs the
  control: `nyiso_chp_btm_measured` False→True.
* **A-K2 LIVENESS** — the solved bundle's fleet carries the measured grid
  capacities of A.1 (checked on 54547 / 50006 / 56259 / 2493 to ±1 MW), and
  its `btm.parquet` shares for the 16 artifact plants equal the artifact.
* **A-K3 THE OBJECT** — Upstate_West's annual equal-hour price error vs the
  committed actual RT falls by **≥ 40 % in 2023** and falls (any amount) in
  2024 and 2025.
* **A-K4 NO NEW PHANTOM CONDUCT** — zero NEW D-4 convictions vs control;
  Selkirk (10725, semi-mothballed, +264 MW restored) named the watch plant
  ex ante: its model energy must stay < 3× its EIA-923 net in every complete-
  vintage year (2023 923-absent: reported, not gated).
* **A-K5 CRITERIA** — C1/C2/C3a/C3b/C4/C6/C8: no PASS→FAIL vs the control,
  each scored on its own arm's bench basis (the share moves both sides of C1
  by construction; a FAIL on the truer basis is a real FAIL). C3c reported.
* **A-K6 CONSISTENCY** — the regenerated bench `classFull` is non-negative in
  every class-year, and `btm[k] <= e923[k]` holds for every (plant, class).

**Promote criterion (arm A alone): A-K1–A-K6 clean.** A fit-worsening on the
truer benchmark with clean gates is rule-14 discovered-bug territory and goes
to the owner, never silently kept or reverted.

## ARM B — the reserve-duty re-arm (`2026-08-20-nyiso-147b-reserve-duty`)

Solved ONLY if arm A passes A-K1–A-K6. Arm B = arm A + `cc_reserve_duty_split`
(single delta vs arm A). **The standing PREREG-nyiso146b §ARM C gates apply
verbatim** (C-K1 exactness vs its control = arm A; C-K2 ≥80 % falls for
{50744, 54592, 54593, 7784} in 2023/2024 — the bars are NOT re-litigated;
C-K3 no-degrade; C-K4 zero new D-4/D-1 + K6′; C-K5 no PASS→FAIL incl. C3a;
C-K6 LOYO as already recorded). The membership artifact
`reserve_duty_cc_NYISO.csv` is frozen and unchanged. The nyiso-146 rejection
grounds were (a) C3a-2023 headroom (control +9.0 % at a ±10 band) and (b)
Allegany −64/−50 % vs ≥80 %; the re-arm condition of nyiso-146 §3.1 is that
the 2023 upstate root cause moves first — arm A is that move. If Allegany
still fails its bar with the margin repaired, arm B is REJECTED again and
registered as such (rule 15); its bar is not lowered.

## Registration & governance

Every solved arm is registered on the dashboard whatever its outcome
(rule 15), all years in one bundle per arm (rule 16), the NYISO shard updated
in this session (rule 28b): arm A on a new `chp_btm_measured` base-matrix row
(new ScenarioConfig field — rule 28c duty, cell lines in every shard), arm B
on the `offer_curve_by_group` row where `cc_reserve_duty_split` already
lives. Promotion (if any) re-keys `complete` under rule 22 D-5(b) with a
determination re-verification; a worse re-verified determination stops the
promotion and escalates. Model assignment: Fable (rule 27).

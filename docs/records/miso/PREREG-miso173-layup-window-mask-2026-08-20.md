# PREREG miso-173 — the measured lay-up window mask for the per-plant must-run floors

**Written and committed BEFORE any arm result is read.** Session miso-173,
2026-08-20. Keeper `2026-08-20-miso-172-p25mw` (bundle `miso172_p25mw`),
determination NOT-YET on C3a-2025 ALONE; C3c the single ledgered caveat; C8
PASS in all three years. This prereg owns the **1402 seasonal / part-year
lay-up object** named by `RESULT-miso172-mustrun-window-vintage-2026-08-20.md`
§7 and the miso-173 charter. **The C3a-2025 scarcity lane is closed end-to-end
(miso-163 owner ruling; FINDING-miso171) and is not worked here. C8 no longer
depends on this object** — miso-172 arm 2 took ST_GAS below its 30 % budget in
2023/2024, so 1402's still-failing D-4 conduct row is no longer load-bearing.
This mechanism is built because the model **forces a plant to operate inside
windows its own measured record says the plant was not operating** (rules 1
[R-STRUCT], 14 [R-ACCURATE], 17 [R-FLOOR-WINDOW]), not to buy a gate.

---

## 1. The defect

Plant 1402 (Little Gypsy, Entergy MISO-South ST_GAS, model capacity 916.5 MW)
in 2023: the outage-extract availability is ~0.541 in January–February (unit
2's 306.8-day mechanical outage) and ~0.95–1.00 in November–December, while
the CAMPD meter reads **0.000 / 0.015** online in Jan/Feb and **0.033 /
0.058** in Nov/Dec. The `st_gas_mustrun_per_plant` floor — whose window is the
top-`online_frac` fraction of the year's hours by system load, i.e. winter
peaks included — therefore binds 2,542 hours across 2023 with the meter dark
in **71.1 %** of them: the keeper's sole surviving D-4 conduct FAIL.

**The measured record that resolves it already exists in the repo, produced by
the model's own outage pipeline.** The merit-order guard
(`scripts/lib/outage_detect.py`, frozen; the campd-economic-layup-fix charter)
partitions every detected ≥ 5-day full-stop window into MECHANICAL OUTAGE
(enters the availability envelope) or ECONOMIC LAY-UP (written to
`data/raw/campd-unit-outages-layup-<ISO>.csv`) — lay-up when the unit's own
measured SRMC sat above the revealed clearing cost for ≥ 90 % of the window.
For 1402-2023 that file carries exactly the missing windows: unit 3
(582.2 MW) Jan 1 – Mar 9 at out-of-merit share 1.0, and both units Oct 4 /
Nov 4 – Dec 31. The lay-up file's own charter states the windows stay out of
the availability envelope because *"an economically idle unit is AVAILABLE;
the LP declines it on its own economics."* **The engine currently contradicts
that adjudication: the LP is never allowed to decline the plant, because the
must-run floor forces it on inside those very windows.**

Scale, measured pre-solve (stage-1 census of
`results/calibration/_miso173_layup_mask_instrument.json`): **six of the seven
live floored ST_GAS plants carry lay-up windows in at least one solve year**
(1402: 236.9 / 334.6 / 298.0 unit-days across 2023/2024/2025; 1122 Ames:
353.0 / 361.3 / 372.2; 3459 Sabine: 201.1 / 123.6 / 250.2; also 990, 3457,
6035). Plant 1403's lay-up rows belong to its CC_REGULAR block, not its
ST_GAS floor group, so it is untouched — the mask matches strictly on
`(plant_code, plant_group)`, exactly as the outage overlay routes.

## 2. Which object this is — decided and defended (the charter's three candidates)

**(a) NOT a seasonal availability correction.** Three independent grounds:

1. The windows are the merit-order guard's ECONOMIC class, separated from
   mechanical outage precisely because they are **not** established physical
   unavailability. Feeding them back as unavailability would re-arm the
   phantom-outage defect the guard exists to remove (the detector booking
   23–46 % of every ISO's CC capacity-year as outage against a real
   EFOR+planned norm of ~10–15 %), and would contradict the frozen charter's
   own words. Rule 13: "didn't run" fed back as "couldn't run" pins an input
   to an operational outcome with no physical instrument behind it.
2. The blast radius would be wrong. Availability enters reserve headroom, the
   scarcity cushion and the retirement screen's attainable margin; the
   measured defect touches none of those — every symptom is in the FLOOR
   (D-4 conduct). An availability zero would also delete capacity the LP
   correctly holds available-but-idle in those hours.
3. The admissible unit-grain physical-outage instrument for MISO does not
   exist: the owner adjudication (miso-157/160) admits MISO's published MOM
   record at FLEET grain only and rules CAMPD inadmissible for outage
   *measurement*. A true availability correction is data-blocked at the
   admissible grain; the floor-window question, by contrast, is answerable
   from the same measured-conduct family that identifies the floor itself.

**(b) NOT a per-year census tier.** 1402 is a cycler (pooled P(on) = 0.506; it
ran Apr–Sep 2023 at monthly online shares up to 0.76). Exclusion mechanisms
delete the floor in kind; 1402's floor is right in kind — a real Entergy
MISO-South self-commitment regime — and wrong in WINDOW. The
"1402 is never added to the lay-up census" line has held four times
(miso-170, miso-170b, miso-172 both arms) and holds here. A (year, month)
census tier would be this mask with coarser grain and the wrong (membership)
semantics.

**(c) IT IS the commitment-window object.** The floor family is measured
conduct end to end: membership and window size from `online_frac`, level from
the p25-of-online sample. The lay-up extract is the same family's measurement
of **when the self-commitment driver is absent**. The repair confines WHERE
the existing floor's window may bind: not inside the plant's own measured
lay-up windows. Nobody self-commits a steamer that is sitting in seasonal
lay-up — the mechanism mirrors the real market (rule 1), consumes only
measured conduct (rule 13's admissible family), and reconciles the engine
with its own outage pipeline instead of stacking anything (rule 19).

## 3. The mechanism (GATED, default off)

`ScenarioConfig.mustrun_layup_window_mask: bool = False`. When armed (and only
in backcast — double-gated: the `_BACKCAST_ONLY_OVERLAY_FIELDS` construction
guard AND a `mode == "backcast"` engine gate), the per-plant must-run floors
composed in `data/fleet/arrays.py::_compose_min_gen_floors` (the generic
cc/st_gas branch and the ST_GAS p25 branch alike) take their per-hour clip
basis as

```
pmax x max(0, availability - layup_share(t))
```

with `layup_share` from the new loader
`market_sim.data.outages.unit_layup_removed_fractions` — the SAME accumulator,
unit→plant routing, model-fleet capacity denominator and window clipping as
`unit_outage_derate_factors`, run over the lay-up companion CSV, so outage and
lay-up shares are additive by construction (each detected window is classified
as exactly one of the two).

* **Availability is NOT touched.** The plant stays fully available to the
  LP's own economics, to reserves and to the cushion. Only the forcing moves.
* **Window size, level, membership, mechanism id: untouched.** A masked
  window-hour loses its floor exactly as a measured-outage hour already does
  under the existing `pmax x availability` clip; no hour is added or moved.
* **Rule 21 [R-DOF]: ZERO new free parameters.** Windows, unit shares and the
  0.90 out-of-merit threshold live in the frozen derive layer (rule 23 —
  the extract is consumed, never re-derived; `MERIT_OOM_FRAC`'s own
  identification note records it is not load-bearing: 0.70 → 1.00 moves the
  NEISO veto count only 560 → 412).
* **Rule 13 forward story:** same-year lay-up windows have no forward
  analogue, exactly like the CAMPD outage windows produced by the same
  detector — the mask is a backcast overlay. A FORECAST year keeps the
  un-masked floor, whose window/level already regenerate from pooled CEMS
  history as each vintage lands; if a forward refinement is ever wanted, the
  plant's recurring seasonal pattern regenerates from the same multi-year
  extract and responds to changed conditions through it. No outcome pinning:
  dispatch above the floor stays free, and the mask can only REMOVE forcing
  the record says is spurious — never add or relocate any.
* **Rule 19:** distinct from `mustrun_plant_exclusions` (membership; a census
  plant carries no floor, so the mask never sees it), from
  `mustrun_online_frac_per_year` (window SIZE vintage; cell `R`, not re-armed
  here), and from the p25 level mechanisms (LEVEL). Membership, size, level
  and hour-eligibility are four orthogonal properties of the ONE floor; this
  arm moves hour-eligibility alone, and nothing is stacked.
* **Rule 25:** the extract is per-ISO; the mechanism self-scopes. Other ISOs'
  cells enter as `U`.

**Also in this session's implementation commit, disclosed:** miso-172's two
fields (`mustrun_online_frac_per_year`, `st_gas_mustrun_p25_measured_level`)
were never registered in `_CACHE_KEY_OPTIONAL_FIELDS` (the nyiso-119
drop-at-default discipline) — an omission found here because nine cache-key
pin tests fail at HEAD. The repairing registration restores the pinned global
default key `603c2498bf71d21d` (both fields are byte-inert off, proven by
miso-172's own K-0) and lands with this session's own registration of
`mustrun_layup_window_mask`. Config-layer only; the M-0 control below
re-proves solve-path inertness of everything at this HEAD in one stroke.

## 4. Pre-solve predictions (stage 2–4 of the committed instrument; NO LP spent)

All from committed artifacts: the keeper's `hourly/system_<year>.parquet`
demand ranking, the raw extracts through the model's own loaders, the
committed p25 measured-MW levels and pooled windows, the keeper's
`legitimacy_diagnostics.json` D-4 rows, and the committed CAMPD bench meter.
Instrument: `scripts/probes/_miso173_layup_mask_instrument.py` → JSON
`results/calibration/_miso173_layup_mask_instrument.json`, both committed with
this prereg.

**Floor VOLUME (the exact basis — the miso-172 §4 lesson applied: the kill
band lives here, not on the at-floor rate):**

| plant-year | vol ctrl → arm (TWh) | ratio |
|---|---|---|
| 1402-2023 | 0.1630 → **0.0565** | 0.347 |
| 1402-2024 | 0.2359 → 0.1628 | 0.690 |
| 1402-2025 | 0.2348 → 0.1766 | 0.752 |
| 3459-2023/24/25 | 2.0406→1.8555 / 2.0240→1.6507 / 2.1374→1.8013 | 0.909/0.816/0.843 |
| 3457-2023/24/25 | 0.8570→0.7151 / 0.8302→0.8070 / 0.8699→0.8303 | 0.834/0.972/0.954 |
| 1122-2023/24/25 | 0.2628→0.2463 / 0.2628→0.2534 / 0.2619→0.2425 | 0.937/0.964/0.926 |
| 990-2023/24/25 | 1.8464→1.7502 / 1.8596→1.8596 / 1.8900→1.8597 | 0.948/1.000/0.984 |
| 6035-2023/24/25 | 0.2041→0.1788 / 0.2469→0.2469 / 0.2444→0.2322 | 0.876/1.000/0.950 |
| 1403 (all) | unchanged | 1.000 (no ST_GAS lay-up rows) |
| **mechanism total** | **11.6017→11.0302 / 11.6871→11.2082 / 11.8663→11.3705** | Δ −0.5715 / −0.4789 / −0.4957 |

**The BINDING engine-build volumes** (full production floor chain, frozen
pre-solve in the instrument's `engine_volumes`; composition competition makes
these larger than the CSV `est` — e.g. 3459 loses reliability-floor-competed
attribution when its p25 take shrinks): mechanism totals **11.4666 → 10.5227 /
11.5867 → 11.0223 / 11.8476 → 11.0861 TWh** (Δ −0.9439 / −0.5643 / −0.7615);
1402 identical to `est` (composition-clean, d = 0.0000 in all years).

**At-floor (D-4/D-2) energy, predicted at fixed at-floor rate on the ENGINE
volume ratios** (the instrument class that measured exactly at miso-172 on
the volume half and drifted on this half — sign KILLS, magnitude REPORTED):
Δ mechanism at-floor TWh **−0.6336 / −0.3611 / −0.5657** (bands ±50 %), i.e.
`st_gas_mustrun_per_plant` D-2 forced energy 5.5632 / 5.6112 / 7.1480 →
~4.93 / ~5.25 / ~6.58 TWh. C8 ST_GAS forced share falls in every year (2025
stays above the 30 % cap and keeps its grounded provenance+shape path, which
currently passes).

**The conduct target (metered zero-share over the plant's floor-eligible
window hours, window grain):**

| plant-year | ctrl → arm (window grain) | rider (fails ≥ 50 %) |
|---|---|---|
| **1402-2023** | **0.633 → 0.0038** | **predicted PASS, by two orders of magnitude** |
| 1402-2024 | 0.356 → 0.096 | stays pass, improves |
| 1402-2025 | 0.273 → 0.049 | stays pass, improves |
| every other plant-year | moves DOWN or unchanged | zero perverse movers |

miso-172 measured the binding set concentrating ~12 pp FAVOURABLY vs the
window-grain prediction (71.2 % observed vs 72.9 % window-grain; the arm beat
its ~64 % prediction at 52.19 %), so 0.4 % window-grain has no plausible path
back above 50 %.

**Instrument limitation, found by the pre-solve engine check and disclosed
here rather than papered over:** the CSV-level `est` construction is blind to
floor COMPOSITION — where another mechanism's floor out-bids the p25 take on
a cell, the cell's mechanism id is not `st_gas_mustrun_per_plant` and the
npz-attributed volume is lower than `est` (measured on 990, 3459 and 1122;
the composition-clean plants 1402 / 3457 / 6035 / 1403 reproduce `est` to
d = 0.0000). The BINDING M-1/M-2 targets are therefore the **pre-solve
production-engine build** — `scripts/probes/_miso173_mask_construction_check.py`
runs the miso-156-blessed `build_year` chain plus the full production
reliability-floor chain (overrides → drag-drop → obligation-drop → plant
exclusions → injection) with the mask off and on for every year, and freezes
the per-plant volumes into the instrument JSON as `engine_volumes` BEFORE any
solve. The `est` table above remains the identification narrative; the known
residual of the engine reconstruction itself is the miso-156 S-FLOORBLIND
record (2025 exact, 2023 +1.22 % rows), which the M-1 tolerance absorbs. **Honest statement of what this clears: the last D-4 conduct
FAIL in the MISO keeper's diagnostics.** It buys no criterion — C8 already
passes — and it is predicted to change no determination line (C3a-2025 is
untouched by design; the masked energy is winter, the miss is summer).

**Against interest, stated before the solve:**

* The mask REMOVES ~0.48–0.57 TWh/yr of near-zero-priced forced ST_GAS energy,
  mostly in winter — model winter prices can only move UP or stay. 2023's C3a
  currently sits essentially at zero error; if the (small, ~0.08 % of load)
  price effect lands adversely it is a real regression and M-6 catches any
  record flip.
* Ames (1122) annual model-vs-meter (miso-172 L-3: −17.6 / −18.1 / +3.1 %)
  can only move DOWN (more negative in 2023/24) since energy is removed; the
  window-grain shape improves (zero-share 0.082→0.042 etc.) but the annual
  level regression is reported if it occurs.
* ST_GAS D-1 `profile_r` may move either way (winter floor energy removed);
  M-7 kills a real shape regression.

## 5. Pre-registered gates (scorer: `scripts/probes/_miso173_layup_mask_ab.py`, committed before either result is read)

Control `miso173_control` = same-recipe `replay_keeper` of `miso172_p25mw` at
this HEAD, all new flags at default (off). Arm `miso173_layupmask` = the
control `--set mustrun_layup_window_mask=true`. Both `--year 2023 2024 2025`,
sequential in ONE invocation (rules 12/16), solved consecutively on this
15 GB container (never concurrently).

| gate | kill? | pass condition |
|---|---|---|
| **M-0** control inertness | KILL | every scored sidecar of every year `max\|diff\| = 0.0` vs the committed keeper, non-numeric equal. Verified BEFORE any arm output is read; a failure stops the session. |
| **M-1** volume exactness | KILL | per live plant-year, the arm's ST_GAS-mechanism floor volume (from its own `floors/<year>_P1.npz`) within `max(0.005 TWh, 3 %)` of the pre-solve **engine build** (`engine_volumes.engine_arm_twh` in the instrument JSON); same bound on the control vs `engine_ctrl_twh`. The tolerance absorbs the known miso-156 reconstruction residual (≤ +1.22 %). |
| **M-2** volume liveness | KILL | every plant-year whose engine build predicts a volume DROP moves DOWN in the npz; every plant-year the engine predicts unchanged moves < 0.1 % (or < 0.0005 TWh); the mechanism-total npz Δ within ±15 % of the engine-predicted Δ, each year. |
| **M-3** at-floor movement | sign KILLs; magnitude reported | Δ D-2 `st_gas_mustrun_per_plant` forced TWh **< 0 in every year** (the kill). Magnitude scored against ±50 % of the §4 prediction and REPORTED either way — a magnitude miss with M-1/M-2 clean is at-floor-rate drift (the pre-registered miso-172 §4 interpretation) and does not kill. |
| **M-4a** conduct | KILL | ZERO NEW D-4 conduct failures and zero new off-window binding, any year. |
| **M-4b** the target | promotion condition | the 1402-2023 D-4 conduct row flips FAIL → pass. Predicted at 0.4 % window-grain zero-share vs the 50 % rider; if it does NOT clear, the session escalates instead of promoting (the prediction margin is so wide that a miss means the object is misunderstood). |
| **M-5** C8 | KILL | no year's C8 regresses from the control. |
| **M-6** record flips | KILL | zero record-grain PASS → non-PASS flips over the full scorer output (scored after both runs are registered, as at miso-172 K-5). |
| **M-7** ST_GAS shape | KILL | D-1 `profile_r ≥ 0.80` and `cv_ratio ≥ 0.5` in all three years, and `profile_r` no more than 0.05 below the control in any year. |

**Candidate rule.** The arm is a keeper candidate iff every KILL is silent
AND M-4b clears. All kills silent but M-4b missed → escalate to the owner
with both records; no self-absolution. Any kill fired → REJECTED-AS-ARMED,
registered and stamped `R` with the evidence, exactly as written here.

## 6. Governance

Rule 22 [R-HOLDOUT] fail-closed: MISO holds neither `complete` nor `final`,
the spend freeze is ACTIVE, **2023–2025 only** under every result here.
Leave-one-year-out is vacuous for the same reason as miso-172 arm 2 and that
is argued, not assumed: zero free parameters — the windows are each plant's
own dated record, identified per plant-year and never against any year's
residual; re-deriving on two of three years would re-read the same CSV rows.
The uniform every-plant-moves-toward-its-meter table in §4 is the evidence
LOO exists to produce. Rule 28 [R-MECH-MATRIX]: the mechanism's base row plus
a cell line in EVERY ISO shard land in the same PR; MISO's cell is stamped
with this arm's verdict in this session and no other ISO's shard verdict is
touched (rule 25). Rule 15 [R-DASHBOARD]: both runs are registered in this
session, keeper or not. DOF ledger: entries unchanged, `n_scalars` 0,
`n_residual` unchanged at 2; the attestation regenerates against the arm.

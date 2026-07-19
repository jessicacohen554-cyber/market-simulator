# CAISO CC-CHP midday behind-the-meter — hypothesis REFUTED (2026-06-24)

Branch: `claude/caiso-phase2-cc-chp-cod-wq4k7n`. Task B hypothesis: CC-CHP units
are "running too much grid energy midday (their host-steam/BTM load is not held
out / not steam-following), so they sit in the midday merit order instead of
behind the meter," inflating the in-state midday floor.

## The premise is wrong on two counts (grounded in code + solved dispatch)

### 1. CAISO CHP is ALREADY steam-following — the keeper turns it on

`_calibration_config` (`run_calibration.py:932`) sets `chp_steam_following=True`
unconditionally for every ISO, so the CAISO keeper already runs CC/CT/ST_CHP as
steam-host cogens, not merchant units. The resolved keeper config confirms it
(`chp_steam_following=true`, `chp_btm_floor_pct=40.0`). The task's premise that
"the keeper does NOT pass them, so CAISO CHP is currently merchant-dispatched"
refers to `run_calibration_full.py` CLI flags, but the config is built by
`_calibration_config`, which hard-sets it on. There is no merchant-CHP bug.

CAISO even has the per-plant steam data: `thermal_tranches_CAISO.csv` carries
`chp_pmin_cf` + `chp_sector` for 86 plants (read by `fleet.chp_overrides`), so
each CHP plant gets a sector-keyed BTM pull-out (`chp_btm_pct`) and a
grid-delivered steam-following floor (`chp_pmin_cf` − BTM), forced flat via
`FleetArrays.min_gen`.

### 2. CC-CHP dispatch is FLAT across the day — it is not a midday swing supplier

Solved 2024 dispatch, mean MW per unit by hour-of-day:

| class | night h2 | midday h12 | evening h19 |
|---|---|---|---|
| CC_CHP | 8 | **8** | 9 |
| CT_CHP | 4 | **5** | 5 |

CHP runs ~flat baseload all day — midday ≈ overnight. It does **not** surge into
the midday merit order, and it is **not** the midday marginal price-setter. In
the solved midday (h10–14) merit order CC_CHP is 3.3% and CT_CHP 2.7% of
generation; the midday floor is set by **CC_REGULAR** (19.6%, the dominant
dispatchable gas), clearing ~$33.7. Holding more CHP behind the meter would
*reduce* midday supply and push the model *more* short midday (higher price), the
opposite of the intended effect.

### BTM add-back does not double-count

The LP dispatches only the grid-facing CHP slice; the host self-supply is pulled
out (`bins_to_fleet`, `pct_mr = chp_btm_pct`) and added back **only** in the
asset-level emissions/total-gen report (`emissions.compute_must_run_emissions`,
data-driven from EIA-923 Page 1 = total − grid). Table [1] gas (the fuel-mix
benchmark) is the LP gas dispatch, so the add-back never inflates the gas total.
2023 model gas 76.15 ≈ EIA-923 76.04 TWh confirms no double-count.

## Where the midday over-pricing actually comes from (the real residual #2)

Not CHP. With the corridor deliverability cap removing the phantom midday imports
(per `DIAGNOSIS-caiso-corridor-deliverability-2026-06-23.md`), the model now
backfills that midday energy with **in-state CC_REGULAR gas** — 2024 model gas
76.88 vs EIA-923 67.68 TWh (+9.2, the removed-import backfill) — and that gas
sets a ~$33.7 midday floor where reality is long (solar glut, ~$16.7, 755 neg
hrs). The model is **short midday** where reality is **long**. This is a
structural shortfall of cheap midday supply, addressed (partially) by the CC
offer-curve level tune (Task A), not by the CHP mechanism, which is already
correct.

## Verdict

No CHP code change. The mechanism is already modeled correctly (steam-following
on, per-plant CAISO data present, flat dispatch, no double-count), and CHP is not
the midday floor driver. Documented as a refuted hypothesis.

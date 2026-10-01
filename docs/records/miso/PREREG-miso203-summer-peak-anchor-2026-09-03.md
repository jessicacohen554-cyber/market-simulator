# PREREG miso-203 — the ambient capability derate at the NET-SUMMER RATING CONDITION, judged against the TAIL (2026-09-03)

**Session:** miso-203, branch `claude/miso-203-c3a-scarcity-tail-5j2q24`.
**Keeper at open:** `2026-09-03-miso-202-unitclip` (bundle
`results/calibration/miso202_unitclip_B`), determination **NOT-YET** on
`{C3a-2025 −12.3845}` alone; C3c the single ledgered caveat; C6 attested
(ledger 41/2).

**Committed BEFORE any adjudicating statistic.** At the time of writing, the only
measurements read are: the keeper's `run_config.json` scenario block, the
mechanism source in `src/market_sim/data/fleet/arrays.py`, the committed
`_miso202_c3a_2025_anatomy.json`, `FINDING-miso139-…`, and the EIA glossary
definition quoted in §1. **No capability integral, no scarce-hour temperature, no
reserve margin and no removal magnitude has been computed.**

---

## 0. Charter and the rule-28(a) DO-NOT-REDO argument

Queue item 1 of the miso-203 charter re-opens the **merchant ambient capability
derate**, whose MISO cell stands at **REFUSED-AT-G0** from miso-139
(`FINDING-miso139-ambient-derate-refused-at-anchor-2026-08-06.md`). Rule 28(a)
forbids re-testing an adjudicated cell **without new evidence**. Two pieces are
tendered, and both are recorded here before any new number exists:

1. **The object changed.** miso-139's declared target was the **mean-LMP LEVEL**
   miss (miso-137's compression object). `_miso202_c3a_2025_anatomy.json` now
   measures, from committed artifacts and with no solve, that C3a-2025 is **not a
   level miss at all**: the model's Jun–Jul median and p75 are *higher* than
   actual, and **15 hours — the top 1 % of actual Jun–Jul hours — carry 99.9 % of
   the entire mean gap**. A mechanism refused for lack of reach against a
   732-hour window is being judged against a **15-hour** window it was never
   measured on.
2. **The anchor is neither convention miso-139 tested.** miso-139 tested (A) an
   **annual-mean** anchor and (B) a **summer-mean**-rescaled hinge, and refused
   both on basis consistency. §1 establishes from **primary source** that the
   EIA-860 net-summer rating's reference condition is neither: it is the ambient
   **at the time of summer peak demand**.

**What is NOT re-opened.** miso-139's G-1 identification stands and is **inherited
verbatim, not re-derived**: MISO's own EIA-860 two-point slopes **CT_PEAKER
0.00363/°C, CC_REGULAR 0.00192/°C**, with **COAL (0.00025) and ST_GAS (0.00033)
excluded by measurement**. Its rule-25 refusal of the committed literature slopes
(0.0126 / 0.0076) stands. No slope is re-identified in this session and **no free
parameter is added**.

---

## 1. G-A — the reference condition, from primary source (settled before the gates)

EIA glossary, *Net summer capacity*, quoted verbatim
(https://www.eia.gov/tools/glossary/, retrieved 2026-09-03):

> "The maximum output, commonly expressed in megawatts (MW), that generating
> equipment can supply to system load, as demonstrated by a multi-hour test, **at
> the time of summer peak demand** (period of June 1 through September 30.)"

Three consequences, stated before they are measured against:

* **EIA-860 states no nominal reference temperature.** The committed
  `gt_ambient_derate_ref_c = 35.0` is described in `scenarios.py` as "the
  net-summer capability-test reference (~35 C / 95 F, the standard summer GT
  rating point)"; `docs/parameter-citations.md:1314` carries it as
  **"auto-generated, needs-citation"**. It is an assumed value, not a sourced
  one, and this session treats it as **diagnostic only**.
* **The admissible anchor is MISO's own measured summer peak-demand dry-bulb**,
  computed by the *same committed construction* miso-139 G-1 used for its ΔT
  denominator — the load-weighted mean dry-bulb over the **top 1 % of in-window
  (Jun 1–Sep 30) load hours**, on the identical `iso_zone_hourly_drybulb` series
  the LP consumes. Zero free parameters; forward-reproducible from forward
  drivers (rule 13 `[R-MEASURED]`).
* **`pmax` IS that rating** (`eia860.py:1036`, miso-139 §4.2), so a hinge at this
  anchor is **summer-level-neutral by construction** — the property G-0 demanded
  and neither tested convention had — while still removing capability strictly
  above it.

**The anchor is therefore FIXED, now, before any G-C/G-D number:** per zone-year,
`T_ref(z,y) = ` load-weighted mean dry-bulb over the top-1 % Jun–Sep load hours.
It will not be re-selected afterwards (**TRAP 1**).

---

## 2. A structural finding recorded in advance, so it cannot be read back

The mechanism queue item 1 describes — *"derate exactly 0 at the rating
temperature and negative only ABOVE it"* — **already exists** as
`ScenarioConfig.gt_ambient_derate`:

```
extra(t) = slope_class × max(0, tmax_zone(t) − gt_ambient_derate_ref_c);  avail *= 1 − extra
```

It is **default-off and structurally unreachable on the MISO keeper**: its block
in `arrays.py` is guarded by `and not _td_on`, and the keeper sets
`temp_dependent_derate=True` (scoped by `temp_derate_classes=['CT_CHP','ST_CHP']`).
The guard is **global while the scope is per-class**, so arming
`gt_ambient_derate` for MISO's merchant classes would change **nothing** today.
Queue item 1 is therefore *not* a new mechanism; it is an existing gated
mechanism plus (i) a sourced anchor and (ii) a guard-scoping repair. Whether
either is worth building is what G-B…G-D decide.

---

## 3. The gates, with the decision rules fixed in advance

| gate | construction | PASS rule (fixed now) |
|---|---|---|
| **G-B** summer-level neutrality (**GATING**) | class summer-hours mean capability under the candidate hinge vs the same-config control, on the model's own `generators_to_fleet_arrays` → `_availability_matrix` | **inherited verbatim from miso-139 and NOT relaxed: \|Δ\| < 1 %** for every armed class in every year. Any class outside it ⇒ REFUSE. |
| **G-C** tail reach (measurement) | capability removed, MW, in the **15 top-1 %-of-actual-price Jun–Jul hours** of each year (the anatomy's own scarce-hour set, same definition, same hub series) | no PASS/FAIL; it feeds G-D |
| **G-D** does it make reserves bind (**GATING**) | G-C removal against the model's own **reserve margin** in those hours: (Σ reserve-eligible idle online capability − Σ requirement over the four families), from the keeper's committed `class_hourly_` + `reserve_family_` sidecars and the model's own capability matrix | **licensed only if the removal is ≥ 25 % of the smallest such margin** in the scarce hours. Below that the ORDC cannot climb and the arm is refused. |

**STOP RULE.** If **G-B** fails, the session reports the basis finding and stops.
If **G-B** passes and **G-D** fails, the session **reports that the mechanism is
summer-level-admissible but quantitatively incapable of the tail object, and does
not arm** — no `ScenarioConfig` field, no solve, no run. A solve is spent **only**
if G-B and G-D both pass.

---

## 4. Predictions, scored against interest

| # | prediction | confidence |
|---|---|---|
| **P1** | The **scarce-hour** dry-bulb sits within **±2.0 °C** of the summer-peak-demand anchor in every zone-year — both sets are selected on high summer load, so they are nearly the same hours. | 0.75 |
| **P2** | **G-B passes with room**: \|Δ summer-mean capability\| < **0.3 %** for CT_PEAKER and < 0.15 % for CC_REGULAR in every year — a hinge at a top-1 %-load anchor is zero in ≳99 % of summer hours. | 0.85 |
| **P3** | **G-C removal < 300 MW** total across armed classes in the 15 scarce hours of 2025, at MISO's own slopes. | 0.75 |
| **P4** | **G-D FAILS**: the removal is **< 5 %** of the smallest scarce-hour reserve margin. | 0.80 |
| **P5** | The reserve margin in the scarce hours is **smaller** than miso-139's 13.7–18.8 GW summer-afternoon *energy* cushion by at least 3×, i.e. the tail re-aim is a real narrowing — but not enough to rescue P4. | 0.60 |
| — | net: **P(arm licensed and solved)** | **0.15** |

**The other side, stated so a null is not retro-fitted.** The strongest case
*for* the arm: the 15 scarce hours are the hottest, highest-load hours of the
year, so their dry-bulb could sit well **above** even a top-1 %-load anchor (the
load peak and the temperature peak are not the same hour), and the reserve margin
there is the tightest of the year — the anatomy already shows the model running
CT_PEAKER at 13.1 GW in those hours against ~17.7 GW of summer capability, i.e.
only ~4.5 GW idle rather than miso-139's ~12 GW. If P1 is wrong by more than
~4 °C the removal roughly triples and P4 is live. **P1 is the load-bearing
prediction and it is the one I most expect to lose.**

---

## 5. Traps, with counter-measurements pre-committed

* **TRAP 1 — anchor shopping.** The anchor is fixed in §1 by the primary-source
  definition plus miso-139's committed construction, before any reach number. If
  G-D fails, no second anchor is tried in this session.
* **TRAP 2 — measuring the cushion at the wrong hours.** miso-139 measured it
  over 732 summer-afternoon hours; the tail object lives in 15. **Both are
  reported side by side**, and the 15-hour number is the one G-D scores.
* **TRAP 3 — slope shopping.** Only MISO's own identified slopes are armable
  (rule 25). The committed literature slopes (0.0126/0.0076) and the
  `gt_ambient_derate` defaults (0.006/0.004) are reported **diagnostic only** and
  never used to license.
* **TRAP 4 — "removes MW" read as "raises price".** A removal inside a unit's own
  idle headroom eats slack and cannot move the marginal unit (miso-139 G-2's
  definition, reused verbatim). The traversal — removal vs headroom vs reserve
  margin — is reported explicitly, not skipped.
* **TRAP 5 — the needs-citation anchor sneaking back in.** `ref_c = 35.0` is
  unsourced; it is reported beside the measured anchor as a **contrast**, and a
  PASS obtained only at 35.0 would be reported as a failure of the sourced
  anchor, not a success of the mechanism.

---

## 6. Rule duties honoured by construction

**Rule 22 `[R-HOLDOUT]`** — 2023/2024/2025 only; MISO holds no `complete`/`final`
marker and the locked-test freeze is active. **Rule 13 `[R-MEASURED]`** — every
input is a registration rating, a measured dry-bulb, or metered load, entering as
a forward-reproducible formula; the keeper's committed sidecars are read for
dispatch/headroom only and never fed back. **Rules 1 / 21 / 24** — nothing is
sized to any residual; the scarce-hour *set* is used only to **localise
reporting**, never to construct a parameter; no tuning channel is created.
**Rule 23 `[R-FROZEN-DERIVE]`** — no derive script is re-run. **Rule 25
`[R-ISO-SCOPE]`** — no non-MISO artifact is touched. **Rule 15 `[R-DASHBOARD]`** —
if no LP is solved there is no run to register (the miso-131…139 precedent).
**Rule 28(b)** — the `temp_dependent_derate` MISO cell is stamped in
`docs/codebase-site/data/mechanism-matrix/MISO.js` in this session whatever the
verdict, rejections included.

---

**Probe:** `scripts/probes/_miso203_summer_peak_anchor_phase0.py` ·
**Record:** `results/calibration/_miso203_summer_peak_anchor_phase0.json`

# FINDING miso-115 — the trough marginal unit is NOT mis-specified: MISO's overnight gas hole is **CHP**, and it is a prime-mover mis-allocation, not a merchant-class defect

Session miso-115, 2026-08-02, branch `claude/miso-115-trough-marginal-unit-lx2apo`,
off `origin/main` at `b9a96a9`. **NO LP SOLVED.** Every number is read from
committed artifacts: the keeper bundle `results/calibration/miso109_hy_level_B`,
`data/raw/campd-unit-level/`, the EIA-860 generator parquet, and
`data/raw/eia-930-hourly/MISO hourly.parquet`. Probe
`scripts/probes/_miso115_trough_marginal_unit.py`; transcript
`results/calibration/PROBE-miso115-trough-marginal-unit-2026-08-02.txt`;
pre-registration `results/calibration/PREREG-miso115-trough-marginal-unit-2026-08-02.md`,
written and committed **before** the probe ran.

**Keeper UNCHANGED** (`2026-07-31-miso-109b-hy-level`). Rule 15: no run
produced, nothing to register — the miso-103/104/105/107/108/114 discipline of
refusing on measurement rather than spending a ~3 h / ~15.5 GB solve.

## 0. Verdict

**The pre-registered decision rule returns COMPARABLE. No charter, no solve.**

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| model `CT_PEAKER`+`ST_GAS` (MW, h1–3) | 1,907 | 2,415 | 2,350 |
| **CAMPD measured** | **1,810** | **2,395** | **2,243** |
| **R = measured / model** | **0.949** | **0.992** | **0.955** |

The pre-registered bar for MIS-SPECIFIED was `R ≤ 0.60` in ≥2 of 3 years. The
measured value is within **5 %** in every year, and the CAMPD side is
`grossLoad` (**gross**) against the model's **net**, so net-for-net the real
fleet runs *even closer to* — plausibly slightly more than — the model. The
model runs the right amount of peaking and steam gas at MISO's overnight
trough.

**The level offset is therefore a pricing question on the same units, exactly
as the prereg's COMPARABLE branch says. The family narrows and the session
stops.** Three further results below were forced by that verdict's own
arithmetic; two of them are new and one of them relocates the defect.

## 1. The verdict is robust to the estimator, not just to the gate

Per class, and under the pre-registered mixed-plant sensitivity (recomputed on
single-model-class plants only, scaled to full class capacity):

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `CT_PEAKER` R | 0.998 | 0.901 | 0.771 |
| `ST_GAS` R | 0.929 | 1.047 | 1.079 |
| `CT_PEAKER` R, single-class plants (88 % of cap) | 0.842 | 0.638 | 0.601 |
| `ST_GAS` R, single-class plants (61 % of cap) | 0.589 | 0.761 | 0.739 |

The sensitivity is the weaker estimator (it extrapolates from a capacity
subset), and it is reported rather than substituted — the verdict is read off
the pre-registered estimator, which is the point of pre-registering one. But
**MIS-SPECIFIED fires on neither**: no class reaches `R ≤ 0.60` in ≥2 of 3
years on either construction. The refusal does not depend on the estimator
choice.

Kills, all pre-registered, all resolved:

* **K1 coverage** — `CT_PEAKER` 90.2 % of model capacity carries a matching
  CAMPD unit; `ST_GAS` 99.9–100 %. Under the 20 % bar.
* **K2 footprint** — MISO membership resolved by **EIA-860 balancing-authority
  code** (609 plants, 131,748 MW, 15 states), never by state; the prompt's
  11-state list would have been wrong on both sides (the repo's
  `states_for_iso("MISO")` carries 14, including AR/KY/TX, and IL/IN/MI/MO/WI
  are split with PJM). Rule 24 `[R-REGISTRY]`.
* **K3 clock** — CAMPD MISO fossil generation troughs at **h2** and peaks at
  h17–h18, so the h1–3 window is on the real trough. Not assumed; measured.
* **K4 calendar** — Feb 29 dropped via the repo's own `_hour_index_8760`
  (rule 8 `[R-8760]`).
* **K5 mapping** — 96–97 % of matched-plant CAMPD MWh reports the expected
  technology family for both verdict classes.

Every crosswalk is the repo's own (`states_for_iso`, `_hour_index_8760`,
`bench_multiclass.unit_family`, `ISO_TO_BA_CODE`). No hand map was introduced.

## 2. It also refutes miso-114's stated *reason* for expecting the defect

miso-114 §2.3 read the trough anatomy as "short on efficient combined cycle and
long on peaking/steam plant, so a peaking-band offer — not a CC offer — is
available to set the trough price." Measured at the technology-resolved,
plant-matched grain, **that reading does not hold**:

| class | 2023 | 2024 | 2025 | K1 cov. | K5 family |
|---|---:|---:|---:|---:|---:|
| `CC_REGULAR` R | 1.035 | 0.992 | 1.052 | 94.8 % | 95–96 % |

The model reproduces **all three merchant gas classes** — CC, CT and steam — at
the overnight trough. It is not long on peaking and it is not short on
combined cycle. So the trough substitution miso-114 measured is not a merchant
gas mis-allocation at all, which is what sends the next section looking
elsewhere.

## 3. Where the gas hole actually is — and the sources agree

miso-114 measured a 3.4–3.9 GW overnight gas hole against EIA-930. That cannot
coexist with §1–§2 unless the two are measuring different things, so all three
bases were put side by side rather than left in contradiction (h1–3, MW):

| year | model all-gas | CAMPD metered | EIA-930 `NG: NG` | model−CAMPD | **CAMPD−EIA930** |
|---|---:|---:|---:|---:|---:|
| 2023 | 19,158 | 22,169 | 22,352 | −3,011 | **−183** |
| 2024 | 20,904 | 23,565 | 24,185 | −2,661 | **−620** |
| 2025 | 18,865 | 22,471 | 22,526 | −3,606 | **−55** |

**CAMPD and EIA-930 agree to 0.2–2.6 %.** There is no coverage or basis escape
hatch: the ~3 GW hole is real and it is not a merchant-class hole. It is in
**CHP**.

| class | 2023 | 2024 | 2025 | K1 cov. | K5 family | status |
|---|---:|---:|---:|---:|---:|---|
| `CC_CHP` R | **2.156** | **2.246** | **2.555** | 83.2 % | 97.0–97.4 % | **kill-clean** |
| `CT_CHP` R | 0.272 | 0.356 | 0.269 | **10.4 %** | 13.6 % | **VOID (K1)** |
| `ST_CHP` R | 0.000 | 0.000 | 0.000 | **26.9 %** | 0.0 % | **VOID (K1)** |

**`CC_CHP` is the finding.** The model runs **less than half** the metered
overnight output of its own gas-cogen combined-cycle plants — a deficit of
**2,086 / 2,274 / 2,446 MW**, the single largest identified component of the
overnight gas hole. It clears every pre-registered kill: 83.2 % capacity
coverage, 97 % family agreement, only 8.7 % of capacity on multi-class plants,
and the single-class sensitivity moves it the *wrong* way for a mistake
(2.182 / 2.263 / 2.633). Coverage being 83 % means the true measured figure is
if anything **higher**, so the deficit is a lower bound. These units are
genuinely running: `opTime > 0` in **78–80 %** of trough plant-hours.

**`CT_CHP` and `ST_CHP` are reported VOID, not as findings.** Their K1 coverage
(10.4 % and 26.9 %) fires the pre-registered kill, and `ST_CHP`'s measured zero
is a Part-75 coverage artifact — **not** evidence that the model runs steam CHP
the market doesn't. Stating that plainly is the point of having written the
kill down first.

## 4. The one audit-grade input error found, sized and *not* acted on

Measured trough heat rates (`heatInput / grossLoad`, **gross**) against the
model's **net** class values:

| class | measured 2023/24/25 | model | gap | trough-selection control | class-average control |
|---|---:|---:|---:|---:|---:|
| `CT_PEAKER` | 11.13 / 11.25 / 11.26 | 12.37 | **+9.9…+11.1 %** | +0.2…+0.5 % | +0.6 % |
| `ST_GAS` | 11.29 / 11.28 / 11.67 | 11.27 | −3.4…−0.0 % | +8.1…+8.7 % | +1.9 % |
| `CC_CHP` | 8.83 / 8.80 / 8.82 | 6.76 | **−23.4…−23.2 %** | −0.4…−0.0 % | +0.7 % |

The `CT_PEAKER` excess is **real, not a weighting artifact** — both controls
(does the trough select efficient units? does the class average carry
never-running junk?) come back under 1 %. Gross-vs-net makes the true gap
larger still. At the keeper's own gas prices it is worth **$3.15 / $2.45 /
$3.91 per MWh** — but `CT_PEAKER` is online in only **1.9–3.2 %** of trough
plant-hours, so this is *not* offered as the trough level-offset fix, and no
causal claim is made here. It is an input-accuracy item under rule 14
`[R-ACCURATE]`, admissible on its own merits regardless of the residual.

`CC_CHP` is the mirror image: priced **23 % too cheap** while dispatching
**half** the measured volume — which is the signature of a class whose output
is set by a **floor**, not by economics. D-2 confirms it: `chp_steam` forces
19.5 % of `CC_CHP`, 35.6 % of `CT_CHP`, 5.5 % of `ST_CHP`. A too-cheap unit
that still under-runs is being *held down* by its floor.

## 5. What must NOT be done with this

* **This does not license `miso_cc_coal_rebalance`.** Its target is still
  defined against another *model* quantity with no measured identification —
  rules 5 `[R-NO-MAGIC]` / 21 `[R-DOF]` / 24 `[R-REGISTRY]`. §2 in fact removes
  its stated premise: the merchant CC/coal split at the trough is not where the
  gas hole is.
* **Do not read §3 as a license to raise a CHP floor to the measured number.**
  A floor set to metered hourly output is an outcome pin (rule 13
  `[R-MEASURED]`). What is admissible is a floor identified from **steam host
  demand** per prime mover, which has a forward analogue; that is a charter,
  not a flag flip, and it needs its own prereg.
* **Do not quote the `CT_CHP` / `ST_CHP` ratios.** They are VOID on coverage.
* `miso_pjm_lmp_import_pricing` stays refuted (miso-114 §4); the seam
  hour-of-day mis-shape stays a rule 1 `[R-STRUCT]` item at 4–7 % of the
  residual; the top-decile convexity deficit stays miso-89's ledgered object;
  `miso_firm_import_floor` stays rejected.

## 6. The named successor

The overnight level offset is a **pricing** question on correctly-sized
merchant units (§0–§2), and the overnight **volume** hole is `CC_CHP` (§3).
Those are two different objects and the second is the better-identified one:
2.1–2.4 GW, kill-clean, never examined by any MISO session, and with a
rule-13-admissible identification available (steam host demand, which
regenerates for a forward year).

The concrete next step is a **no-LP Phase 0 on the CHP floor's own deriver** —
does `chp_steam` / `chp_export_floor_measured` identify a per-prime-mover
export obligation, and does its construction explain a CC-cogen floor set at
under half of metered output while CT-cogen is over-forced? That is answerable
from the deriver and its coefficients, exactly as miso-107 answered the
reliability-floor question without spending a solve.

## 7. Rule duties

* **Rule 15** — no run produced; nothing to register.
* **Rule 16** — no bundle; the 2023–2025 span was measured in one pass.
* **Rule 22 `[R-HOLDOUT]`** — 2023–2025 only; MISO holds no
  calibration-complete marker and no holdout year was read.
* **Rule 24 `[R-REGISTRY]`** — every crosswalk is the repo's own (§1).
* **Rule 19 / 23** — nothing armed, nothing stacked, no derive re-run.
* **Rule 28 duty (b)** — `diurnal_price_amplitude` MISO cell annotated with
  this answer to miso-114's named successor, and `measured_ct_heat_rates`
  MISO annotated with §4, in this session. Both cells keep their status: no
  mechanism was armed, so nothing is promoted or rejected.
* **Record correction** — the `measured_ct_heat_rates` row says "Still
  untested in MISO" while the `reliability_floor` row records miso-106 arming
  it. Both are true in their own sense: miso-106's arm and artifacts live in
  **PR #3140, open and unmerged**, so no merged MISO result exists and the
  cell correctly stays `U`. Noted so a future session does not read the two as
  a contradiction. The keeper does **not** arm the flag (absent from
  `run_config.json` and `meta.json`), which is why this session's model-side
  heat rates are keeper-matched.
* **Contamination declared** — the session read miso-114's finding and the
  matrix notes before measuring, so it was **not** blind to the expected
  direction. The prereg was written first and the verdict went **against** the
  hypothesis the handoff carried, which is the direction contamination does not
  explain.
* Next number: **miso-116.**

# FINDING miso-114 — the MISO seam has the RIGHT annual import energy and ZERO hour-of-day skill; and MISO's overnight residual is a marginal-unit LEVEL offset, not the congestion lane miso-113 routed it to

Session miso-114, 2026-08-02, branch `claude/miso-backcast-calibration-aqxtoz`,
off `origin/main` at `579c719`. **NO LP SOLVED** — every number is read from
committed artifacts (keeper bundle `results/calibration/miso109_hy_level_B`,
`data/raw/lmp-data/MISO/`, `data/raw/eia-930-hourly/MISO hourly.parquet`,
`data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet`). Probe:
`scripts/probes/_miso114_seam_hod_shape.py`; transcript
`results/calibration/PROBE-miso114-seam-hod-shape-2026-08-02.txt`.

**Keeper UNCHANGED** (`2026-07-31-miso-109b-hy-level`). Rule 15: no run was
produced, so there is nothing to register — the miso-103/104/105/107/108
discipline of refusing on measurement rather than spending a solve.

## 0. Verdict

Three results, one of which refutes this session's own opening hypothesis.

1. **The seam defect is real, large and previously unmeasured.** MISO's net
   interchange is reproduced to **1.017 / 1.016 / 0.908** of actual annual
   energy while its **hour-of-day correlation with reality is +0.097 / −0.453 /
   −0.030** — no skill in 2023/2025 and *inverted* in 2024. The model's imports
   trough at h1–h2 and peak at h17–h18; MISO's real imports do the opposite.
   Signed mis-shape: **night short 1,206–1,333 MW, peak long 746–1,338 MW.**
   Mechanical cause identified: `MISO_SEAM_LADDER_BY_YEAR` is an **8-band,
   hour-invariant** price ladder, so every band is available in every hour and
   the LP can only clear the seam as a monotone function of **MISO's own**
   price.
2. **It is NOT a gate-closer, and this is stated before anyone spends a solve
   on it.** At the model's own measured local stack slope (0.24–0.40 $/GW),
   correcting the whole mis-shape is worth **−$0.32/−$0.39/−$0.44 overnight**
   and **+$0.34/+$0.43/+$0.30 at peak** — against measured gaps of **+$6 to
   +$8** overnight and **−$5 to −$25** at peak. That is **4–7 %** of the trough
   residual. It is a rule 1 `[R-STRUCT]` structural-fidelity item, not a C7 or
   C3a instrument.
3. **The opening hypothesis is REFUTED on MISO's own data** (§4). Pricing the
   PJM seam at the measured hourly border LMP (`miso_pjm_lmp_import_pricing`,
   built, default-off) is **not** the fix: the actual MISO−PJM_WEST spread is
   ±$1–2 overnight, its night-minus-peak differential is only **−$1.07 / +$2.16
   / +$3.15**, and actual net import correlates with the hourly spread at only
   **r = +0.24 … +0.29**. MISO imports **4.6 GW at a $1.0/MWh spread**. The seam
   is a firm/scheduled base — exactly as `miso_seam_measured_ladder`'s own
   docstring says (r = +0.06, 46–56 % of import MWh inside the $2 hurdle band) —
   so hourly spot-spread pricing would re-introduce the arbitrage failure mode
   the ladder was built to fix.

## 1. Why this is new evidence against a `G` cell

`diurnal_price_amplitude` carries **MISO `G`** (xiso-1, 2026-08-01) on the
strength of miso-89, whose enumerated instruments were: uniform attribution
(miso-85), cross-fuel attribution (miso-87), congestion (miso-78/79,
data-blocked), `gt_ambient_derate` (measured inert), and the scarcity apparatus
(measured *starved*, not missing).

**The seam's hour-of-day shape is not on that list**, and neither is the
trough/peak decomposition in §2. miso-89 is a statement about the **peak** half
(a ~10 GW summer-peak fossil under-derate). This finding is about the **trough**
half and about a supply channel with **zero hourly skill** that no prior MISO
session measured. Rule 28 duty (a) is satisfied: the cell is not being re-tested
on old evidence.

The independent cross-check that this session reproduces xiso-1 exactly:
diurnal amplitude ratio **0.354 / 0.393 / 0.253** here vs xiso-1's MISO
**34.0 / 36.3 / 25.2 %**, computed on a different construction (hub-mean DA
energy component vs `actual_lmp_hourly_MISO`). Two independent constructions,
same answer.

## 2. Where MISO's overnight residual actually lives

### 2.1 It is the ENERGY component, not congestion — 64 / 71 / 73 %

MISO publishes a single-reference LMP decomposition, so
`ENERGY = LMP − MCC − MLC` is one system-wide series. The probe **asserts** this
rather than assuming it: max cross-hub std **0.000000 / 0.008345 / 0.000000**
$/MWh.

Overnight (h0–5, h22–23) p10, and the decomposition of the model's gap to
MINN.HUB (the wind-belt hub where MISO's cheap overnight hours actually land):

| year | model dual | actual ENERGY | actual MINN.HUB | ENERGY share | congestion share |
|---|---:|---:|---:|---:|---:|
| 2023 | $24.45 | $15.92 | $11.03 | **+8.53 (64 %)** | +4.89 (36 %) |
| 2024 | $20.92 | $13.91 | $11.11 | **+7.01 (71 %)** | +2.80 (29 %) |
| 2025 | $29.61 | $21.07 | $17.83 | **+8.54 (73 %)** | +3.24 (27 %) |

miso-113 §5 routed the C7 `COAL_PRB` residual to "the data-blocked miso-78/79
congestion + sub-hourly-RT lane". **Two thirds to three quarters of it is not
congestion at all** — it is the congestion-free system energy price. That half
is not data-blocked.

### 2.2 In the ordinary 90 % of overnight hours it is a LEVEL offset

Binning overnight hours on net load and comparing the two price-vs-net-load
curves decile by decile (probe Q2), the gap in deciles 0–8 is nearly flat:

| year | dec 0 | dec 4 | dec 8 | dec 9 | slope ratio (model/actual) |
|---|---:|---:|---:|---:|---:|
| 2023 | +8.20 | +6.08 | +5.60 | +5.70 | 0.788 |
| 2024 | +6.90 | +5.88 | +3.92 | **−3.11** | 0.613 |
| 2025 | +8.32 | +5.47 | +1.54 | **−7.46** | 0.529 |

So the overnight window carries **two distinct defects**, which previous
sessions have been treating as one:

* **(a) a LEVEL offset of +$4 to +$8 across the ordinary 90 %** of overnight
  hours, roughly independent of net load — the signature of a **mispriced
  marginal unit**, not of a missing quantity or a missing scarcity mechanism;
* **(b) a convexity/tail deficit in the top overnight decile** (the tightest
  overnight hours), which flips the gap negative in 2024/2025. That one *is*
  miso-89's availability object and stays where miso-89 left it.

C7 `COAL_PRB`'s amplitude deficit is fed by **(a)**: a flat, too-dear overnight
price gives the coal fleet nothing to cycle against, which is precisely why
miso-111 (repricing the band), miso-112 (splitting it) and miso-113 (flooring
it) all failed to move `cv_ratio` — none of them touches the price the fleet
responds to.

### 2.3 The trough substitution arithmetic closes

Model minus actual at h1–h3 (probe Q4, EIA-930 fuel types):

| year | coal | gas | imports | nuclear | wind |
|---|---:|---:|---:|---:|---:|
| 2023 | **+2,976** | **−3,411** | −1,743 | −70 | +405 |
| 2024 | **+2,628** | **−3,565** | −1,547 | −64 | +469 |
| 2025 | **+3,708** | **−3,851** | −1,484 | −120 | +455 |

The model fills a **1.5–1.7 GW import hole and a 3.4–3.9 GW gas hole with
2.6–3.7 GW of extra coal**, and it does so *while keeping* **1,907 / 2,415 /
2,350 MW of `CT_PEAKER` + `ST_GAS` online at the trough**. That is the shape of
the level offset in (a): the model's overnight gas is short on efficient
combined cycle and long on peaking/steam plant, so a peaking-band offer — not a
CC offer — is available to set the trough price.

## 3. The seam mechanism, precisely

`MISO_SEAM_LADDER_BY_YEAR` (`model/interchange/spec.py`) prices each seam's
import and export bands at a **per-year 8-value ladder** derived by coupling
EIA-930 seam flow-duration quantiles to MISO's own DA hub LMP quantiles. It is
armed in the keeper (`miso_seam_measured_ladder=True`) and it **works as
designed** — it fixed the 2025 import starvation and it reproduces annual
energy to 2–9 %.

What it cannot do is place that energy in the right hours. Because all eight
bands are offered in all 8,760 hours, the count of bands in the money is a
monotone function of MISO's own price, so it is **lowest overnight and highest
at peak** — the opposite of the measured flow:

| year | bands in the money, h0–5 | bands in the money, h16–19 | actual net import h0–5 | actual h16–19 |
|---|---:|---:|---:|---:|
| 2023 | 4.4 | 6.0 | 4,323 MW | 4,105 MW |
| 2024 | 3.5 | 4.9 | 2,777 MW | 2,359 MW |
| 2025 | 2.9 | 4.2 | 2,366 MW | 1,980 MW |

This is a **rule 1 `[R-STRUCT]`** defect in the classic form the rule names: the
right annual number reached through a mechanism whose hour-to-hour behaviour is
not the market's. It is worth fixing on those grounds **and on those grounds
only** — §0.2 sizes it at 4–7 % of the residual, and no future session should
charter it as a C7 or C3a instrument.

## 4. The refuted hypothesis, reported in full

This session opened on the hypothesis that the fix was
`miso_pjm_lmp_import_pricing` — price the PJM seam at the measured hourly
border LMP already committed at
`data/raw/_validation-source/pjm_border_lmp_hourly_MISO.parquet` (26,280 rows,
`PJM_WEST`, on the model's own hour index). The measured PJM_WEST border price
has a real diurnal shape (hod range **$22.9 / $24.9 / $38.5**; night $21.3 /
$20.7 / $31.5 vs peak $38.5 / $40.4 / $61.4) against a ladder with **zero**,
which looked decisive.

It is not, and the model-independent check is what kills it. Against **actual**
MISO hub prices rather than the model's:

| year | actual MISO−PJM_WEST spread, h0–5 | h16–19 | night-minus-peak | corr(spread, actual net import) |
|---|---:|---:|---:|---:|
| 2023 | −$0.50 | +$0.57 | **−$1.07** | +0.289 |
| 2024 | −$0.72 | −$2.88 | **+$2.16** | +0.240 |
| 2025 | −$2.24 | −$5.39 | **+$3.15** | +0.286 |

MISO imports **4,591 MW at h2 in 2023 on a +$1.0/MWh spread**. A spread that
small cannot produce a 1.3 GW hour-of-day swing, and the correlation says the
flow is not spread-driven. The PJM/IESO seam is a firm/scheduled base; the
ladder exists because of that. **`miso_pjm_lmp_import_pricing` should not be
armed for this defect, and the earlier finding that the spot-arbitrage seam
"structurally deletes" firm flow in a zero-spread year stands.**

The honest consequence: the seam's hour-of-day shape is a **scheduling**
property, not a price property, so any fix has to represent the schedule. The
one existing mechanism that would (`miso_firm_import_floor`) is already
rejected as an outcome pin, and this finding does **not** re-license it — a
floor pinned to measured hourly flow is precisely rule 13 `[R-MEASURED]`'s
forbidden case. What is admissible is an **hour-of-day-resolved band
availability** (the same `(month × hour-of-day)` grain `MISO_SEAM_DIBA`'s
envelope already uses and the keeper already arms as a cap), which changes
*when* a band may clear without pinning *how much* flows. That is a design
question with a real rule-13 argument on both sides and it needs its own
charter, not a flag flip.

## 5. What must NOT be done

* **Do not arm `miso_cc_coal_rebalance`** for §2.3. It is a hand-specified
  offer-curve override ("raise the MISO CC committed/econ-high bands and the
  bituminous econ-high band so the marginal MWh sits **above the priced-import
  hurdle**"). Its target is defined relative to another *model* quantity, it
  carries no measured identification, and it would move the overnight coal/gas
  ranking by an amount nobody has measured. That is rule 5 `[R-NO-MAGIC]` /
  rule 21 `[R-DOF]` / rule 24 `[R-REGISTRY]`, whatever it does to the residual.
* **Do not treat the seam mis-shape as the C7 instrument.** §0.2 sizes it.
* **Do not re-open the top-decile convexity deficit (2.2b) as a new lane.** It
  is miso-89's object and it is ledgered.

## 6. The named successor — one no-LP measurement, then a decision

The level offset (2.2a) is the live target and it now has a **single decisive
test that costs no solve**:

> **Measure MISO's CAMPD-observed `CT_PEAKER` + `ST_GAS` online MW at h1–h3,
> 2023–2025, and compare it against the model's 1,907 / 2,415 / 2,350 MW.**

EIA-930 does not split gas by prime mover, so this session could measure the
model side only. If the real MISO fleet runs materially less peaking/steam gas
at the overnight trough than the model does, the trough marginal unit is
mis-specified and the level offset has a structural cause with a measured
identification — which is a legitimate charter. If the real fleet runs a
comparable amount, the level offset is a *pricing* question on the same units
and the family narrows again.

Either way the answer is a measurement, not a solve, and it should be taken
before any MISO A/B is spent (a MISO per-plant A/B is ~3 h and ~15.5 GB peak).

## 7. Rule duties

* **Rule 15** — no run produced; nothing to register.
* **Rule 22** — 2023–2025 only; MISO holds no holdout marker and none was
  touched.
* **Rule 28 duty (b)** — `reference_price_interface` MISO cell annotated with
  the hour-of-day-skill measurement and the `miso_pjm_lmp_import_pricing`
  ex-ante refusal, in this session.
* **Rule 19** — nothing armed, nothing stacked.
* **Rule 23** — no derive was re-run; committed artifacts only.
* **Contamination declared** — the session read miso-113's finding and the
  xiso-1 matrix note before measuring, so it was **not** blind to the
  compression result. Immaterial to §2–§4, which rest on sources
  (LMP component decomposition, EIA-930 interchange, the committed border-LMP
  parquet) that predate both.
* Next number: **miso-115.**

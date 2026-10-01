# FINDING — nyiso-171: the CC_CHP "hard floor" is a PORTFOLIO ARTIFACT, not per-plant physics — 16 of 17 cogens hit exactly zero, the collapse hours it was meant to repair are an availability event where a floor is inert by construction, and the class over-runs in 80 % of 2025's hours, which forbids every floor mechanism

**Session:** nyiso-171 · **Date:** 2026-09-01 · **Keeper:**
`2026-08-30-nyiso-159-loss-surface` (determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}) · **Solves run: ZERO.**
**No parameter was touched, no band was swept, no run was registered.**

---

## 0. The result in one paragraph

The brief opened CC_CHP low-end dynamics as the most likely single carrier of
the CC over-run, on nyiso-169b's reading that the model treats a
steam-host-following resource as freely dispatchable: model p05 runs
**+63.6/+21.8/+26.1 %** above measured, yet at p01 the model collapses to near
zero in **96 hours of 2025** where the measured fleet "never falls below ~280 MW
and is never off." Phase 0 set a stop condition — a fleet floor is a mechanism
only if it is a **per-plant** property — and **the stop condition is met in two
of three years, with the third clearing by 0.002.** Disaggregated, the measured
fleet is not floored at all: **0 of 17 CC_CHP plants are never off in 2023**
(1 of 17 in 2024 and 2025), the sum of per-plant minima is **0.0 / 81.0 / 85.0
MW** against fleet minima of **282 / 368 / 184 MW**, and per-plant coverage of
the fleet floor is **0.253 / 0.502 / 0.313** against a pre-registered 0.50 bar
required in all three years. The fleet is "never off" only because its plants are
never all off *at once* — so a per-plant `min_gen` would force machines to run in
hours their own meters say they were off, which rule 17 `[R-FLOOR-WINDOW]`
forbids **by construction**. Two further kills land independently: the 96
collapse hours are an **availability event**, not a dispatch property — in every
year they carry price at **1.60/2.96/3.00×** the annual mean while **total gas
output falls to 0.428/0.242/0.009×** normal across all six gas classes — and
`min_gen` is clipped to `pmax × availability`, so a steam floor is **inert in
exactly its target hours**; and the **sign forbids it**, because the model
**over-runs** CC_CHP in **51/69/80 %** of the remaining hours (mean gap
**+37.8/+184.1/+347.3 MW**), and every floor is a lower bound. The lane produces
**no lever and no solve**, and hands forward one measured class-crosswalk defect.

## 1. What was measured, and off what

Zero solve throughout. Every series is a committed artifact or a raw measured
record:

| instrument | source |
|---|---|
| what already floors CC_CHP | the keeper's committed `legitimacy_diagnostics.json`, D-2 rows |
| the model's structural floor | `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` (`chp_pmin_cf`), through the `assembly.py` formula `pmin_cf × (1 − pct_mr/100) × nameplate` |
| model hourly MW by class | the keeper's committed `hourly/class_hourly_<year>.parquet`, pass **P1** |
| model hourly zonal price + demand | the keeper's committed `hourly/system_<year>.parquet`, pass **P1** |
| measured hourly MW **per plant** | `data/raw/campd-unit-level/NY_<year>.parquet`, `unitType` × the EIA-860 CHP flag via `market_sim.data.chp._chp_by_plant` — the model's own CHP determination, and the same class construction as nyiso-169b/170 |
| class volume reference | the committed `frontend/data/backcast/bench/NYISO/<year>.json.gz` `classFull` |

**Rule 13 `[R-MEASURED]` compliance.** CAMPD enters only as *conduct
identification*. Nothing is pinned to observed generation, and no statistic is
tuned to any residual. The one anchoring used (A7) is the nyiso-170 construction
— a single factor `benchmark_TWh / CAMPD_TWh` per class-year — which preserves
the annual level error exactly and therefore compares **shape only**.

**Rule 22 `[R-HOLDOUT]`.** Every year read is 2023, 2024 or 2025. NYISO holds no
`complete` marker and is absent from `final`; nothing out-of-training was read,
solved, scored or registered, and **no marker was requested**.

**Reproduction of the six inherited probes.** All six were re-run before
anything was measured. Five reproduce their recorded values directly:
nyiso-167 gain **0.703**, offset **$11.03**, R² **0.910**; nyiso-168 deficit
**−$6.59 = −$2.32 gradient + −$4.27 level** (35 %/65 %); nyiso-168 reserve
ceiling **10.01×** thermal-only; nyiso-169b `PEAK-BAND PROPOSAL SUPPORTED: False`;
nyiso-170 `proceed_to_phase_2: false` with G3 alone true. The sixth hit the
brief's documented trap (b) — a fresh container has no NYISO DA LBMP container
and the probe **degrades silently** — and was repaired as the brief prescribes
(`fetch_nyiso_zonal_lmp.py --start 202301 --end 202512 --kind both`, 36 DA months
staged, then `regenerate_clean.py nyiso-interface-flows`). It then reproduces:
maximum posted-binding share **1.7 %**, i.e. **≥98.3 %** of measured congestion
forms off-limit. The degraded JSON was never committed.

## 2. The pre-registered gates and their outcomes

Registered in `results/calibration/PREREG-nyiso171-chp-floor-identification.md`
and committed **with the probe, before either was run** (`138fe2ea`).

| gate | PASS condition | outcome |
|---|---|---|
| **A1** rule 19 attribution | exactly one mechanism forces CC_CHP | **PASS** — `chp_steam` alone |
| **A2** model structural floor | reported, not gated | every CAMPD-visible plant zero-floored |
| **A3** **stop condition** | per-plant coverage ≥ 0.50 in **all three** years | **FAIL — PORTFOLIO ARTIFACT** (0.253 / 0.502 / 0.313) |
| **A4** meter validity | silent meters excluded, not convicted | **PASS** — 2 silent meters excluded per year |
| **A5** outage vs economics (contiguity) | scattered ⇒ economic | split: scattered 2023/24, contiguous 2025 |
| **A5b** outage vs economics (direct) | — | **AVAILABILITY EVENT, all three years** |
| **A6** sizing | reported, not gated | 0.013–0.044 % of class energy |
| **A7** sign of the gap | — | **model over-runs**; no floor can help |

### 2.1 A1 — what already floors CC_CHP (rule 19 `[R-ONE-MECH]`)

From the keeper's committed D-2 attribution, **one** mechanism forces CC_CHP:

| year | mechanism | forced TWh | class TWh | share of class |
|---|---|---|---|---|
| 2023 | `chp_steam` | 0.0072 | 15.100 | **0.05 %** |
| 2024 | `chp_steam` | 0.0260 | 18.531 | **0.14 %** |
| 2025 | `chp_steam` | 0.0202 | 19.952 | **0.10 %** |

No reliability floor, no commitment bridge (that mechanism covers CC_REGULAR and
ST_GAS only), no class min-gen. So a correction would **replace this floor's
level source**, never stack on it — which is exactly how the matrix's own base
row already describes `chp_steam_following` / `chp_export_floor_measured` /
`chp_steam_floor_p25`: "level sources for ONE mechanism, never a second floor."

### 2.2 A2 — the model's structural floor is zero wherever CAMPD can see

`chp_pmin_cf` is a **CAMPD p2 never-below** statistic. A plant that is off for
more than 2 % of the year measures **exactly zero**:

| plant | MW | lens | `chp_pmin_cf` | median CF | model floor |
|---|---|---|---|---|---|
| Sithe Independence 54547 | 996.4 | ok | **0.0** | 85.9 | **0.0** |
| Linden Cogen 50006 | 915.3 | eia923_cf | 39.4 | — | **360.6** |
| Selkirk 10725 | 596.6 | ok | **0.0** | 50.6 | **0.0** |
| Empire 56259 | 580.0 | ok | **0.0** | 81.9 | **0.0** |
| Brooklyn Navy Yard 54914 | 260.0 | ok | **0.0** | 78.8 | **0.0** |
| Lockport 54041 | 219.0 | ok | **0.0** | 52.5 | **0.0** |

**14 of 17 plants — 77.6 % of the class's 4,309 MW — carry no floor at all**, and
the class's entire **381 MW** structural floor is one *CEMS-invisible* plant.
This is the same defect the WP-3 owner ruling named for CAISO
(`FINDING-caiso95` §5: a percentile-of-all-hours statistic mixes host-driven
offline zeros into the level). **Its NYISO repair is separately unavailable at
HEAD**: `thermal_tranches_NYISO.csv` is a **pre-WP-3 artifact** carrying neither
`steam_level_cf` nor `p25_allhr_cf`, so `thermal_tranche_chp_steam_level("NYISO")`
returns `{}` and arming `chp_steam_floor_p25` is **provably inert** — a fact
worth recording, but moot given §2.3.

### 2.3 A3 — THE STOP CONDITION: the floor is a portfolio artifact

A fleet series can be "never off" for two different reasons, and only one is a
mechanism. The discriminator is exact — `Σ_p min_t(gen_p,t)` against
`min_t(Σ_p gen_p,t)`:

| year | fleet min | fleet p01 | Σ plant mins | Σ plant p01s | coverage(p01) | plants never off | verdict |
|---|---|---|---|---|---|---|---|
| 2023 | 282.0 | 324.6 | **0.0** | 82.0 | **0.253** | **0 / 17** | PORTFOLIO ARTIFACT |
| 2024 | 368.0 | 392.6 | 81.0 | 197.2 | 0.502 | 1 / 17 | per-plant (by 0.002) |
| 2025 | 184.0 | 290.6 | 85.0 | 91.0 | **0.313** | **1 / 17** | PORTFOLIO ARTIFACT |

The pre-registration required **≥0.50 in all three years**. It clears in one, by
two thousandths. In 2023 **not a single CC_CHP plant is continuously online** and
the sum of per-plant minima is **exactly 0.0 MW** against a 282 MW fleet minimum.

The per-plant record shows why. On-shares run from **0.080** (Lockport, online
8 % of 2023) to 1.000, and every large cogen goes to zero:

| plant | 2023 on-share | 2023 min | 2025 on-share | 2025 min | median-when-on |
|---|---|---|---|---|---|
| Sithe 54547 | 0.750 | **0.0** | 0.915 | **0.0** | 667 → 836 MW |
| Empire 56259 | 0.894 | **0.0** | 0.829 | **0.0** | 391 → 453 MW |
| Brooklyn Navy Yard 54914 | 0.967 | **0.0** | 0.963 | **0.0** | 203 MW |
| Selkirk 10725 | **0.102** | **0.0** | **0.154** | **0.0** | 122 → 307 MW |
| **East River 2493** | 0.997 | 0.0 | **1.000** | **85.0** | 224 → 239 MW |

**The one genuine exception is East River (2493)** — Con Edison's Manhattan
steam/electric station, online 100 % of 2025 at a hard 85 MW minimum. It is the
only NYISO cogen that behaves the way the brief's premise describes, and **the
model already floors it**, under `ST_CHP` at `chp_pmin_cf = 30.0`. There is no
unfloored per-plant physics left to represent.

**What IS real, and why it is a different mechanism.** Conditional on being
online, the large cogens do hold a substantial level (`p05_on`: Sithe 98→145 MW,
Empire 198→208, BNY 103→112, Corinth 121→113). That is a **minimum stable load
when committed** — a commitment property — not a must-run floor. Representing it
as `min_gen` would force these plants on in the 10–90 % of hours their meters say
they were off, which is precisely the rule 17 violation the stop condition exists
to catch.

### 2.4 A5b — the collapse hours are an availability event, where a floor is inert

A5's pre-registered contiguity proxy split the years (scattered 2023/24,
contiguous 2025). Contiguity is a weak instrument, so the direct discriminator
was measured alongside it — **reported in addition to the pre-registered gate,
not in place of it**. An economic shutdown happens in *cheap* hours with the rest
of the gas fleet running; an availability event happens regardless of price and
derates the whole fleet together:

| year | low hrs | mean price | year mean | ratio | total gas | year mean | ratio |
|---|---|---|---|---|---|---|---|
| 2023 | 88 | $51.83 | $32.33 | **1.60×** | 3,068.7 MW | 7,164.4 | **0.428×** |
| 2024 | 91 | $107.62 | $36.37 | **2.96×** | 1,870.1 MW | 7,734.7 | **0.242×** |
| 2025 | 96 | $168.72 | $56.19 | **3.00×** | 75.8 MW | 7,940.3 | **0.009×** |

**Unanimous.** In 2025 the 96 hours are a single contiguous January block in
which **every gas class is at zero** — CC_CHP 0.0, CC_REGULAR 0.0, CT_PEAKER 0.6,
ST_GAS 72.4, ST_CHP 0.7, CT_CHP 2.1 MW — at three times the annual price and the
70th percentile of demand. No economic model shuts its entire gas fleet off at
$169/MWh. This is the historic outage overlay (`outage_source = historic`), a
rule-13-admissible measured availability input. Because `min_gen` is clipped to
`pmax × availability`, **a steam floor cannot bind in a single one of the hours
it was proposed to repair.**

### 2.5 A7 — the sign forbids every floor mechanism

Every floor — steam-host, lay-up, commitment bridge, class min-gen — is a *lower
bound*: it can only raise output. So a floor can help only where the model runs
**below** the market. On the nyiso-170 anchored basis, excluding the availability
hours of §2.4:

| year | anchor | hours model **above** measured | mean gap |
|---|---|---|---|
| 2023 | 1.185 | **51.1 %** | **+37.8 MW** |
| 2024 | 1.145 | **69.3 %** | **+184.1 MW** |
| 2025 | 1.070 | **80.4 %** | **+347.3 MW** |

In the failing year the model runs CC_CHP above the market in **four hours out of
five**. (2023's 51.1 % is a bare majority and is reported as such; its mean gap
is the stronger statistic there, and it is positive.) A7 is the general result
that subsumes the others: **the CC_CHP object is an over-run, and no floor of any
shape can address an over-run.**

### 2.6 A6 — and it would be inert anyway

Sized on the measured candidate floor (`Σ` per-plant p01, meter-live plants):

| year | floor | hours binding | forced energy | share of class | class volume error |
|---|---|---|---|---|---|
| 2023 | 82.0 MW | 24 | 0.00197 TWh | 0.013 % | +0.2717 → +0.2737 |
| 2024 | 197.2 MW | 39 | 0.00764 TWh | 0.041 % | +1.4370 → +1.4446 |
| 2025 | 91.0 MW | 97 | 0.00877 TWh | 0.044 % | +2.7651 → +2.7739 |

Four independent reasons to refuse, any one sufficient.

## 3. The brief's three phase-0 questions, answered

**(a) Which plants drive the 96 near-zero model hours, and is the measured fleet
floor per-plant or fleet-level?** Neither half survives as posed. The 96 hours
are not driven by *plants* at all — they are a fleet-wide availability event in
which all six gas classes go to zero together (§2.4). And the measured floor is
**fleet-level**: 16 of 17 plants hit exactly zero, and the only per-plant floor
in the class (East River) is already represented (§2.3).

**(b) Are the p05 over-run and the p01 under-run the same plants?** They are not
even the same *kind of object*, so the brief's "then they are two mechanisms and
you must say so" applies: the p01 under-run is an **availability** artifact
shared by the whole gas fleet, while the p05/p25 over-run is a **dispatch/
composition** object (the aggregate claim nyiso-170 preserved). **A floor
addresses neither** — it cannot bind in the availability hours, and it can only
push the over-run further wrong.

**(c) What already floors CC_CHP?** Exactly one mechanism, `chp_steam`, at
0.05/0.14/0.10 % of class energy — with its level source measuring **zero on
every plant CAMPD can see** (§2.1–§2.2). There is nothing to stack on and nothing
worth replacing.

## 4. Lines this session closes

* **CLOSED — the CC_CHP steam-host floor as a lever.** Failed its own
  pre-registered stop condition; refused again on availability-inertness, on the
  sign of the gap, and on sizing. **Do not re-open a CC_CHP floor** — steam-host,
  lay-up, commitment-bridge extension, or class min-gen — without a new
  instrument that overturns §2.3 or §2.5.
* **CLOSED — `chp_steam_floor_p25` as a NYISO repair.** Provably inert at HEAD:
  the NYISO tranche artifact is pre-WP-3 and the loader returns `{}`. Moot
  regardless, per §2.5.
* **CLOSED — "the measured CC_CHP fleet is never off" as a per-plant statement.**
  True of the sum, false of all but one plant. The 2025 fleet minimum is **184
  MW**, not ~280 (that is its p01).
* **NOT OPENED — the un-grounded `peak` 2.25**, per the brief's guardrail:
  neither swept nor touched.
* **NOT OPENED — any C3c lever**, and none of the fourteen closed lines
  re-tested.

## 5. Carry-forward: one measured class-crosswalk defect

**East River (2493) is `ST_CHP` in the model's tranche artifact but lands in
`CC_CHP` in the CAMPD `unitType` construction** that nyiso-169b, nyiso-170 and
this session share (the plant reports both "Combined cycle" and boiler units).
It carries **2.13–2.19 TWh** of measured output into the comparison CC_CHP
series, while the model's whole ST_CHP class produces **0.07–0.09 TWh**. This
sits directly beside nyiso-170 §3's finding that NYISO's five CEMS-registered
ST_CHP units report **0.000 TWh**. It is a **measurement-construction** issue,
not a dispatch defect, and it slightly inflates the measured CC_CHP low-end
percentiles every one of these sessions has compared against. Filed as an
observation for a successor; **not repaired here**, because repairing it would
change the basis of three committed findings and is out of this lane's scope.

## 6. Honest expected value

**What is delivered.** A reproducible, zero-solve, pre-registered adjudication
that (a) answers the brief's phase-0 question **NO** on its own stop condition,
with the exact discriminator the pre-registration named; (b) kills the mechanism
three further independent ways, any one sufficient — availability-inertness in
its own target hours, the sign of the gap, and sizing at 0.013–0.044 % of class
energy; (c) discharges the rule 19 `[R-ONE-MECH]` enumeration from committed
artifacts and finds the class essentially unfloored, so the question of stacking
never arises; (d) reports its weaker pre-registered A5 proxy **alongside** the
stronger A5b rather than quietly replacing it; and (e) identifies the one genuine
never-off NYISO cogen and shows the model already floors it.

**What is NOT delivered. No gate moves.** C3a-2025 is still **−11.5 %**, C3c
still fails, the determination is still **NOT-YET on {C3a-2025, C3c}**, and NYISO
still does not read CALIBRATED. **No solve ran**, so rule 15 registers nothing —
the dashboard is untouched **by design, not by omission**. **The measured change
in the 0.7032 gain is not reported because no arm ran**; phase 2 was never
entered, because phase 1 returned the stop condition the brief itself specified.
No matrix cell verdict moves: `chp_steam_following` stays **`K`** with the
adjudication added as evidence. **The lane produced no lever and does not claim
one.**

**What could still be wrong.** The per-plant minimum is a strict statistic: a
plant with a single bad meter hour reads a zero floor it does not physically
have. Two guards blunt this — A4 excludes identically-silent meters, and the p01
variant (which tolerates 1 % of hours at zero) is the one actually gated — but a
plant with 2–3 % scattered meter dropout would still read lower than its true
floor. The direction of that bias is toward the finding's conclusion, so it
weakens the *strength* of the kill rather than reversing it; the 2023 result
(**0/17** plants never off, Σ mins **exactly 0.0**) is far too wide for meter
noise to explain. The availability reading of §2.4 is inferred from price and
fleet-wide co-movement on committed artifacts rather than read off a per-plant
availability array, which would need a replay; the 2025 evidence (whole gas fleet
at 0.0 MW, $169/MWh) is unambiguous, while 2023's 0.428× is the weakest of the
three. A7's anchoring inherits nyiso-170's single-factor construction and
CAMPD's own hourly noise, and is contaminated by the East River crosswalk of §5
in the direction of *understating* the model's over-run. And this session refutes
the **floor** framing of the CC_CHP object; it does not explain the over-run,
which remains the aggregate composition error nyiso-170 preserved and did not
identify a mechanism for.

**The honest read on the object.** After nyiso-167, 168, 169, 169b, 170 and this
session, C3a-2025 is fully partitioned, every named partition is adjudicated, and
the last mechanism the brief could name for the CC_CHP half is now refused on
measurement rather than on exhaustion. The **gradient** half is a representation
limit; the **level** half is the price-response gain, blocked on offer and
reserve data this lane cannot obtain. **A successor should not expect to close
C3a-2025 from the current data set at the current grain**, and the standing
**$27.79–$56.03/MWh** pass window nyiso-167 derived should be planned around
rather than solved away.

## 7. Evidence

* `scripts/probes/nyiso171_chp_floor_identification.py` + `results/calibration/_nyiso171_chp_floor_identification.json` — gates A1–A7; committed at `138fe2ea` **before** it was run.
* `results/calibration/PREREG-nyiso171-chp-floor-identification.md` — the gates, the stop condition, and the two directions fixed in advance so a favourable re-read was not available.
* `results/calibration/nyiso159_lossarm_B/legitimacy_diagnostics.json` — the D-2 attribution of §2.1, read not regenerated.
* `data/raw/_processed-legacy/thermal_tranches_NYISO.csv` — the `chp_pmin_cf` level source of §2.2; **read, never re-derived** (rule 23 `[R-FROZEN-DERIVE]`).
* `src/market_sim/data/fleet/assembly.py` (the `chp_pmin_mw` construction) and `src/market_sim/data/fleet/arrays.py::MECH_CHP_STEAM` — the floor path, read but **not modified**.
* `docs/FINDING-nyiso170-merit-order-displacement-2026-09-01.md` §3–§6; `docs/FINDING-nyiso169-congestion-gradient-anatomy-2026-09-01.md` §7–§8; `docs/FINDING-nyiso168-supply-curve-slope-anatomy-2026-09-01.md` §4, §8–§9; `docs/FINDING-nyiso167-c3a-price-response-gain-2026-09-01.md` §2, §5 — the closed lines, none re-opened.
* `docs/codebase-site/data/mechanism-matrix/NYISO.js` — `chp_steam_following` (`K`, evidence added; **no verdict moves**); `node --check` and `scripts/check_mechanism_matrix.py` both pass.
* CLAUDE.md rules 1 `[R-STRUCT]`, 13 `[R-MEASURED]`, 15 `[R-DASHBOARD]`, 17 `[R-FLOOR-WINDOW]`, 19 `[R-ONE-MECH]`, 20 `[R-FORCED-BUDGET]`, 22 `[R-HOLDOUT]`, 23 `[R-FROZEN-DERIVE]`, 25 `[R-ISO-SCOPE]`, 28 `[R-MECH-MATRIX]`.

Next shorthand: nyiso-172.

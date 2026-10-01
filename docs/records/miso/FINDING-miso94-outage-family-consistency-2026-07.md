# miso-94 — the guard-corrected extract stales its own downstream outage family; LANE A has no structural door of the required sign

**Determination: `NOT-YET`.** Registered arm `2026-07-26-miso-94-outage-family`
(MISO 2023/2024/2025, one bundle). C3a-2024 **−10.06 % → −10.05 %**, still past
the ±10 % veto. Every other gate unchanged from miso-93.

Charter, pre-registered before any solve:
`docs/handoffs/miso-94-outage-family-consistency-charter-2026-07.md`.

---

## 1. The LANE A question, answered

The miso-93 handoff scoped LANE A by one question: *which offer-curve parameters
were fitted against the inflated outage envelope, and do they re-derive?* Rule 23
`[R-FROZEN-DERIVE]` permits re-derivation only on a **source-data** change, and
the guard-corrected extract (`6a8f285`, blob `f2b3ec8` → `c298c68`) is one — "the
one legitimate door."

**Answer, read off the derivations before solving: none of MISO's price-level
parameters consume that extract. The door opens onto the availability family
instead.**

| candidate | consumes the std extract? |
|---|---|
| `gas_offer_margin_anchor` (3.0492) | No — delivered-gas series only; rule-23 trigger is `data/raw/gas-prices/` or EIA-923 receipts |
| `phys_committed` / `phys_econ_low` / `phys_econ_high` (miso-88 eGRID-HR bands) | No — `derive_campd_marginal_hr.py` reads CEMS unit-hours with `grossLoad > 0`; outage hours self-exclude |
| `SUMMER_WEFOR_SHARE`, `SUMMER_CLASS_DERATE` | No — **no derivation of any kind exists**; nothing to cite |
| `reliability_floor_coeffs_MISO.csv` | No — `commit_frac_window` is an online count from CAMPD gross load |
| `campd_ct_run_lengths/bands`, `MISO_SEAM_LADDER_BY_YEAR`, `miso_measured_reserve_requirements` | No |
| `offer_curve_by_group` (72 scalars) | n/a — **residual**-identified, not a derive; nothing to re-derive |
| **`campd-unit-outages-short-MISO.csv`** | **Yes** — `_load_standard_windows` → `_when_operable_cf`, the CF basis of the `SHORT_BASELOAD_CF ≥ 0.55` guard |
| **`campd-unit-outages-maxgen-MISO.csv`** | **Yes** — `_load_covered_windows` → guard 4 (disjointness) |
| **`thermal_tranches_MISO.csv`** | **Yes** — `unit_outage_derate_factors` is the availability denominator of `committed_pct` / `mustrun_pct` |

`6a8f285` changed the std extract and re-derived **none** of the three artifacts
that take it as an input. All three are live in the MISO keeper.

## 2. What was corrected, and the controls

Single delta, HEAD code, std extract swapped; blob hash verified before and after
each run. (One contamination was caught and corrected mid-session: a control run
left the pre-guard blob on disk. It is recorded rather than quietly fixed.)

* **short** — control **PASSES**: the committed file is byte-identical to a HEAD
  re-derive on the pre-guard std blob, so provenance is clean and the delta is
  cleanly attributable. Guard delta: **−1 row** (F B Culley 1012/2, 2023-03-10→12,
  2.2 d, 103.7 MW).
* **maxgen** — guard delta **+18 rows / +1,338 MW / 23.1 GWh**: ST_GAS 1,002 MW,
  CC_CHP 251, CC_REGULAR 85 — precisely the classes the guard returned to merit
  (ST_GAS was 73.5 % of its removals). Control does **not** reproduce, which is
  how §3 was found.

## 3. A pre-existing rule-19 violation the re-derive also repairs

The committed maxgen extract **violates the deriver's own asserted guard 4**.
Three unit-blocks carry a maxgen derate while a short-extract full stop already
covers the same unit-hours, and `arrays.py` applies the overlays as successive
`availability *= f`:

| unit | block | maxgen derate | covering short window |
|---|---|---|---|
| Weston 4078/3 | 2024-08-26 13:00–20:00 | 369 MW | 2024-08-23 → 08-27 (3.7 d) |
| Sherburne County 6090/1 | 2024-08-26 13:00–20:00 | 729 MW | 2024-08-24 → 08-28 (4.4 d) |
| F B Culley 1012/3 | 2025-07-28 12:00 → 07-30 | 287 MW | 2025-07-27 → 07-28 (1.8 d) |

~1,385 MW double-derated inside declared emergencies — one mechanism per
phenomenon, rule 19 `[R-ONE-MECH]`. Diagnosis: the committed extract predates the
short-extract leg of guard 4 (it also *excludes* Prairie State 55856/01 on
2025-07-24, which only a then-present std window explains).

Net change committed → adopted, by declared block: 2023-08-24 **+41 MW**,
2024-08-26 **−362**, 2025-06-23 **+74**, 2025-07-24 **+316**, 2025-07-28 **+13**.

## 4. Result — measured, and against the pre-registration

Annual load-weighted mean, model, from the committed `hourly/` sidecars:

| year | keeper miso-88 | miso-93 | **miso-94** | Δ 93→94 | C3a-93 | **C3a-94** |
|---|---|---|---|---|---|---|
| 2023 | 31.791 | 31.324 | 31.324 | +0.0001 | | |
| 2024 | 29.470 | 29.024 | **29.027** | **+0.0025** | −10.06 % | **−10.05 % FAIL** |
| 2025 | 37.839 | 37.443 | 37.442 | −0.0007 | −17.51 % | −17.51 % (ledgered) |

**The arm is near-inert on price level.** Gates: C1 (free 12/12), C2, C4, C5a, C6,
C7, C8 PASS; C3b/C3c ledgered; C3b-2025 NRMSE 0.214. C8 ST_GAS stays *grounded
above budget* (39.9 / 41.1 / 53.8 %, D-4 clean).

**Pre-registration honesty.** The charter got the verdict right — it stated
outright that this arm does **not** close C3a-2024 — and bounded 2024 at
|ΔP| ≤ $0.03. It got the **sign wrong**: it predicted a small decrease from the
block's net −362 MW; the measured move is a small increase. Cause, measured after
the fact: the overlays compose **multiplicatively** per `(plant_code, plant_group)`,
so removing a double-derate from a plant the short overlay already holds near zero
buys back little, while the +735 MW of new ST_GAS/CC_CHP rows bite in full. **The
double-count was therefore largely inert in effect while remaining a real
correctness violation** — it is corrected on that ground (rules 1 / 11 / 19 / 23),
not on the residual.

## 5. LANE A's actual verdict

**There is no structural door of the required sign and size for C3a-2024, and this
session did not manufacture one.** The gap is ~$0.02/MWh on a $32 annual mean
(0.06 pp). The only surface that could move it at will is `offer_curve_by_group` —
72 **residual**-identified scalars over ≥39 solves — which is not a derive, has no
source-data change to cite, and whose re-fitting to recover 0.06 pp would be an
answer key. **Per rule 24 `[R-DOF]`, C3a-2024 is therefore an open root-cause
issue, reported and not tuned.** The keeper designation is unchanged: promoting or
demoting on a NOT-YET arm is an owner call.

## 6. Open, with its measurement — the next lane

**`thermal_tranches_MISO.csv` is stale and was deliberately NOT re-derived here.**
It consumes the changed extract, but the committed file does **not** reproduce at
HEAD on its own pre-guard input: a `--years 2023 2024 2025` re-derive differs on
`committed_pct` (71 plants, max 53.3 pp), `mustrun_pct` (31, max 60.0 pp),
`p25_cf` (77) and `nameplate_mw` (6 plants, max 1,028.6 MW) — changes **not**
attributable to the guard. Adopting it would be a confounded arm, the exact
caiso-123 defect miso-93 was careful to avoid.

It is nonetheless **the highest-value next lane**: it is the only stale artifact
that touches offer-curve **shape** (must-run / committed tranche sizes) rather than
availability, so it is the only remaining candidate with plausible magnitude on
C3a. That lane's first job is to establish its provenance — identify the input
vintage that reproduces the committed file — before any A/B is attempted.

**Cross-ISO exposure.** `6a8f285` adopted the guard for **all six ISOs** and
re-derived no downstream artifact for any of them. Every ISO running
`unit_outage_short_windows`, `unit_outage_maxgen_events`, or consuming
`thermal_tranches_<ISO>.csv` carries the same staleness, and the guard-4
disjointness violation is not MISO-specific by construction. Not audited here —
flagged.

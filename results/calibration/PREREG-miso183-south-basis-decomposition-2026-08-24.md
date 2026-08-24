# PREREG miso-183 — the SOUTH-SEAM MEASUREMENT-BASIS session: is the "+1.19 GW South under-export" a model defect or a bookkeeping artifact?

**Session miso-183 (2026-08-24).** Registered **BEFORE any adjudicating
quantity is computed and BEFORE the source hunt begins.** Executes the queue
head installed by miso-182
(`FINDING-miso182-south-export-driver-2026-08-24.md` §7), which REPLACES D-3:
a **basis/validation** question, not a mechanism.

**EVIDENCE ONLY. NO LP will be solved, no `ScenarioConfig` field created,
nothing armed, no run registered** (rule 15 `[R-DASHBOARD]` not engaged; the
miso-142…182 no-LP precedent). Keeper `2026-08-22-miso-177-rho-measured`
(`miso177_rho_B`) UNCHANGED. Determination unchanged: **NOT-YET on C3a-2025
alone**, C3c the single ledgered caveat. **No matrix cell will be minted in any
outcome** — this session tests no mechanism-in-kind (rule 26(b) engages via the
§5.4 queue stamp + calibration-log entry only).

## 0. What has already been looked at, and what has not

Declared for honesty about the pre-registration boundary. Before writing this
document the session read only:

* committed prior findings and their committed values (miso-174/177/178/181/182
  findings, `_miso174_seam_overimport_decomposition.json` structure and the
  values those findings already quote, `_miso182_south_export_driver.json`'s
  producing probe source);
* schemas and row counts ONLY of: the pbc binding record
  (`data/raw/transfer-constraint-binding/MISO/miso_pbc_{da,rt}_{2023..2025}.csv.gz`
  — header + first data row + line counts; its README), the keeper hourly
  sidecars (`miso177_rho_B/hourly/*` — column names, zone list, klass list, and
  three sample MISO-West rows for column semantics), `data/raw/MISO_region.parquet`
  / `MISO_fueltype.parquet` (columns + the D/DF/NG/TI type table),
  and the EIA-930 DIBA parquet (via the committed miso-182 probe source);
* config/constants: `MISO_SEAM_DIBA`, `MISO_RDT_CONTRACT_{N_TO_S,S_TO_N}_MW`,
  `MISO_RDT_DEFAULT_DERATE_FRAC`, the RDT TCDC / RPE constants and their
  citation comments, the keeper `run_config.json` flag block
  (`miso_rdt_tcdc=True`, `miso_rpe_pricing=True`, `miso_south_seam_split=True`,
  `miso_seam_measured_ladder=True`, `miso_manitoba_seam=True`,
  `miso_seam_flow_limit=True`, `miso_seam_export_limit=True`);
* the matrix §5.4 miso-182 queue stamp.

**No statistic over any measured hourly series has been computed for this
session** — no flow mean, no correlation, no binding-hour coincidence count, no
hour-set intersection. The only new numbers seen are file/line counts and
schema tables.

## 1. The object (committed; restated, not re-derived)

miso-174 §1 (on the then-keeper; scarce = summer ∩ RT > $200, n = 11/14/47):

| year | pool-basis South scarce gap (measured − model net export) |
|---|---:|
| 2023 | **+0.633 GW** |
| 2024 | +0.350 GW |
| 2025 | **+1.191 GW** — the largest single 2025 seam component |

miso-182 re-characterized the object on committed artifacts: the seam is
**TVA at 79.2/85.7/85.8 %** of gross export; 46–76 % of each gap is **stress
response** (the model's price-elastic export collapses in its own scarce hours
— the armed South export ladder tops at $53.00/MWh in 2025 against a scarce set
averaging $479 — while the measured seam holds or expands); and three
corroborations point at the reading that the measured comparator may carry
**MISO's own Midwest→South Regional Directional Transfer (RDT) wheel booked at
external boundaries** (TVA scarce-hour export 2,720 MW vs the keeper's derated
N→S limit 0.92 × 3,000 = 2,760 MW, 1.4 % below; the one-neighbour-export /
offsetting-imports pattern; 2025 = the year the MODEL's internal RDT bound N→S
5,086 h). miso-182 deliberately did **not** compute the decomposition (its
anti-sweep clause) and minted `miso_south_firm_export_block` `G`.

**This session's question:** is the pool-basis gap a real model defect (the
model genuinely moves too little energy out of / around its southern boundary)
or a basis artifact (the comparator books MISO's internal transfer externally
while the model books it internally, where it belongs)?

## 2. The structural frame (Leg 1 — pre-registered ANALYSIS, no data needed)

Declared in advance because it fixes what the measurement can and cannot show.

EIA-930 DIBA interchange is booked **per counterparty pair**: ONE MISO↔TVA
series covering every MISO–TVA tie, Midwest-side and South-side alike (the
probe VERIFIES this — one row per (hour, diba) — as a schema check, gate-free).
Three consequences:

1. **Within-pair netting.** Any wheel leg that exits MISO into counterparty X
   and re-enters MISO from the same X (e.g. Midwest→TVA→South) nets out of the
   MISO↔X series, whatever its size.
2. **Within-pool netting.** A leg that exits into pool member A and re-enters
   from pool member B (e.g. Midwest→LGEE→TVA→South) nets out of the **pool
   aggregate** (pool = `MISO_SEAM_DIBA["South"]` = SOCO/TVA/AECI/LGEE/SIKE),
   while inflating A's gross export and B's gross import — the exact pattern
   miso-182 measured (TVA +1.9 GW export vs SOCO −0.67 / AECI −0.44 imports).
3. **The pool aggregate can carry wheel contamination ONLY through cross-pool
   leakage** — a wheel path that exits via a pool member but re-enters via a
   non-pool counterparty (SWPP/PJM/…) or vice versa — and by whole-BA
   conservation the pool's contamination is exactly minus the non-pool seams'.

So the burden the basis-artifact reading must carry is: **cross-pool leakage of
order the object itself** (≈1.2 GW in the 2025 scarce set). The
per-counterparty legs, by contrast, are basis-vulnerable at full wheel
magnitude. The legs below measure exactly these two exposures.

## 3. The instrument (frozen construction)

One read-only probe, `scripts/probes/_miso183_south_basis_decomposition.py` →
`results/calibration/_miso183_south_basis_decomposition.json`. **Frozen and
carried unchanged from the committed miso-174/178/182 machinery:** the −1 h
DIBA hour key (never re-searched), the fixed non-leap 8760 CST clock, hour sets
`annual` / `summer` (Jun 1–Sep 30) / `scarce` (summer ∩ MISO RT > $200; n =
11/14/47) with `da_foreseen` and `top47_rt` reported-only, and the sign
conventions (EIA-930 `mw` + = MISO exports; every table states its sign).
**2025 is the load-bearing year** (the C3a year, the largest object);
**2023 secondary; 2024 reported-only** (the disclosed EIA-930 internal
inconsistency, r = 0.8286).

New-source clock mappings are fixed **a priori from each source's documented
convention** (e.g. MISO market time is EST year-round: EST hour H → model CST
hour H−1, then the same non-leap day-of-year construction). **No alignment
search.** If a source's convention is undocumented, the probe reports the
assumed convention with its header evidence, evaluates every gate on that
a-priori choice, and REPORTS (never gates on) a ±1 h sensitivity pair.

### Leg 2 — the basis-free South-intake comparison (load-bearing IF the substrate lands)

The one comparison on which internal-vs-external booking cancels: the **total
flow into MISO-South across all its boundaries**, model vs measured.

* **Measured** `N_S = L_S − G_S` hourly, from MISO subregional (South-region)
  actual load and generation (intake targets §5). Identity calibration: the
  same construction at whole-MISO (`L_tot − G_tot` vs measured net import from
  `MISO_region.parquet` TI / the committed BALANCE series) is reported per hour
  set as the identity's accuracy wedge `W`. **No apportionment of `W`**: the
  gate statistic uses raw `ΔN`, with the gate re-evaluated at `ΔN ± |W|` as a
  reported sensitivity.
* **Model** `N_S^m = RDT^m + seam_net^m`, an **interval**, from committed
  artifacts only:
  * `seam_net^m` — the model South-seam net flow per hour set, CITED from the
    committed `_miso174_seam_overimport_decomposition.json` (vintage
    `miso169_gated_A`, pruned; drift disclosed exactly as miso-174/182 did).
  * `RDT^m` — from the keeper's own committed `system_<year>.parquet` price
    spread `price(MISO-South) − price(MISO-East)` (the Midwest is copper-plate,
    committed miso-174 §5). Classification, grounded in the armed TCDC/RPE
    constants (`constants.py`): spread ≈ +$200 (±$1) → RPE-only, RDT flow ∈
    [0, 2,760) MW; any other spread > +$1 → RDT at/above its derated limit,
    flow ∈ [2,760, 3,000] MW (= [0.92 × 3000, contract]); spread < −$1 → S→N
    congestion, flow ∈ [−2,500, −2,300]; |spread| ≤ $1 → unconstrained, flow ∈
    (−2,300, +2,760) (the honest wide band). The probe reports the observed
    spread-level clustering as a semantics check and the per-set counts of each
    class. `N_S^m` is carried as [low, high] per hour set.
* **Decision statistic:** `s2 ≡ ΔN_scarce / O_y`, `ΔN = N_S − mid(N_S^m)`
  scarce-mean GW (+ = reality moved MORE into the South than the model), with
  both interval ends reported; `O_y` = the committed pool-basis gaps
  (+0.633/+0.350/+1.191).
* **Lines (2025 load-bearing):**
  * `s2 ≥ +0.5` on BOTH interval ends → **V-TRANSFER** (a real intake deficit
    into the South of ≥ half the object — the object survives, REBASED: not an
    "export elasticity" defect but an internal/total transfer deficit).
  * `|s2| ≤ 0.25` on both ends → **South intake exonerated** (the model moves
    the right total into the South; whatever defect exists lives in
    Midwest-side external trade and/or booking).
  * `s2 ≤ −0.25` → **South-surplus reality** (reality supplied the South less /
    the South itself net-sold) — supports V-TRADE.
  * between → MIXED; both components reported.

### Leg 3 — the direct wheel test (IF an aggregate RDT flow series `R_t` lands)

* **3a (level):** scarce-mean `R_t` vs the derated limit (2,760 MW) and vs the
  committed TVA scarce export (2,720 MW). **Per-counterparty poisoning line:**
  if `|R_t − TVA_scarce_export| ≤ 0.15 × R_t`, the "TVA leg ≈ the wheel's exit"
  reading is CORROBORATED and every future session must treat per-counterparty
  South numbers as basis-poisoned (only the pool aggregate quotable). This line
  adjudicates the LEGS, independent of the pool verdict.
* **3b (pool leakage):** OLS slope `β` (and Pearson r, reported) of the hourly
  pool net export `E_pool` on `R_t`, summer hours (annual reported). Bias
  direction declared NOW: genuine stress-driven trade co-moves with `R_t`, so
  `β` OVERSTATES leakage. Therefore: `β ≤ 0.15` → pool wheel-clean (**STRONG**,
  the bias runs against it); `β ≥ 0.5` → pool substantially wheel-carrying
  (**SUPPORTED, not proven**); between → indeterminate.
* A non-hourly `R` (monthly/quarterly) supports **level corroboration only**
  (monthly `R` vs monthly `E_pool` and vs the TVA leg): no `β`, no 3a gate;
  stated as such.

### Leg 4 — the binding-record contrast (fallback, always computable from held data)

From the committed pbc record (`miso_pbc_rt_<year>.csv.gz`; RT rows are 5-min
EST interval starts; `RDT_MW_SO (North_South)` = N→S, `RDT_SO_MW (South_North)`
= S→N). An hour **counts as binding N→S** iff ≥ 6 of its 12 five-minute
intervals carry an `RDT_MW_SO` row (the ≥ 1-row variant count is reported for
coverage, never gated). EST → model CST hour: H − 1, then the frozen non-leap
mapping. Disclosed limitation: a pbc row exists only at ≥ 100 % of the modeled
limit, so "non-binding" does NOT mean low flow — the record is a lower-bound
indicator on "flow at limit".

* **D4 contrast:** `mean E_pool(summer ∩ binding N→S) − mean E_pool(summer ∩
  non-binding)`, GW; the same contrast per counterparty leg (TVA, SOCO, AECI,
  LGEE) reported alongside.
* **Lines:** `D4 ≤ 0.3 GW` → no binding-coincident pool-export elevation →
  wheel-clean corroboration; `D4 ≥ 0.75 GW` → wheel-carrying **suggestion**
  (the stress confound applies, same asymmetry as 3b). Between → indeterminate.
* **Reported, prose-only (no gate):** the scarce∩binding counts — how many of
  the 11/14/47 scarce hours had the REAL RDT binding N→S (the model's internal
  RDT bound 2,432/2,705/5,086 h) — and the legs' qualitative pattern (TVA
  export AND SOCO+AECI imports both elevated in binding hours with the pool
  aggregate ~flat is the legs-carry-wheel signature at qualitative level).
* **Leg 4 alone can never establish V-BASIS** (the confound is dispositive
  without an `R_t` to control it); it can only corroborate wheel-clean or leave
  the question open.

### Leg 5 — `ba_code="SOCO"` liveness (code-only; the miso-174 §4 pattern)

The miso-182 §7 named item: trace at HEAD whether the South seam's
`ba_code="SOCO"` drives ANY solve-time quantity under the armed
`miso_seam_measured_ladder` keeper config (grep the consumption path;
classify LIVE / SUPERSEDED / PARTIAL with file:line citations). Not a
measurement; no gate; resolves or confirms-open the named rule-14 item.

## 4. Verdict mapping (frozen)

O_y = the committed pool-basis scarce gaps. Adjudicated on 2025 (load-bearing),
with 2023 concurrence reported and 2024 reported-only.

| verdict | pre-registered condition | consequence |
|---|---|---|
| **V-BASIS** ("substantially the wheel / bookkeeping") | Leg 2 `s2 ≤ +0.25` (or Leg 2 unavailable) **AND** positive wheel-carriage: 3b `β ≥ 0.5` **AND** 3a corroborated. Leg 4 alone is NEVER sufficient. | The +1.19 GW object is **INVALIDATED as a lever target**: the pool-basis comparator carries MISO's internal transfer; the C3a-2025 South residual is re-framed; the miso-174 seam-decomposition basis is annotated everywhere it is quoted. |
| **V-TRADE** ("substantially external trade" — **the object survives INTACT**) | Leg 2 `s2 ≤ +0.25` or `s2 ≤ −0.25` **AND** wheel-carriage absent (3b `β ≤ 0.15`, or without `R_t`: Leg 4 `D4 ≤ 0.3 GW`) | The pool-basis gap is genuine trade the model refuses **by construction**; the residual is the model's own export price-elasticity (the $53.00 ladder ceiling vs the $479 scarce mean) — **named precisely and handed forward, NOT built here**. |
| **V-TRANSFER** (object survives, REBASED) | Leg 2 `s2 ≥ +0.5` on both interval ends | The defect is a real total-intake deficit into the South (internal + external jointly), not an export-leg elasticity; successor charter re-aimed accordingly. |
| **V-UNRESOLVED** (honest negative close) | No retrievable substrate beyond Legs 1+4, and Leg 4 indeterminate | The hunt's negative is recorded as the result: **no retrievable series decides the basis question**; the object stays quotable only as a defect of unestablished magnitude with the miso-182 §7 caveat, and the re-open condition is the series itself. |

Independent of the pool verdict, the **per-counterparty poisoning line** (3a,
or its qualitative Leg-4 shadow, which — like Leg 4 generally — corroborates
but never establishes) is reported as its own finding: it governs whether
future sessions may quote per-counterparty South numbers at all.

Mixed outcomes that satisfy no row are reported as MIXED with every component
at full magnitude; no post-hoc threshold is moved to force a row.

## 5. The hunt (pre-declared source ladder, admissibility fixed in advance)

Every source probed is recorded in the finding with URL and verdict
(retrievable / gated / dead / does-not-carry-the-quantity). **A negative is a
result.** Order and admissibility:

* **H-1 (`R_t`, the aggregate Midwest↔South RDT flow):**
  * MISO Data Exchange — **re-confirm the adjudicated gate only** (miso-77 §2c,
    miso-174 K-PRE-4, the transfer-constraint-binding README): key-gated; no
    new access claim, no key request in-session.
  * MISO market reports archive (`docs.misoenergy.org/marketreports/…`) — the
    one host already proven retrievable (the pbc record). Enumerate the report
    index for any report carrying RDT/sub-regional transfer FLOW MW.
  * IMM/Potomac SOM + quarterly reports — usable only if a machine-readable
    series exists; a chart is recorded as chart-only (the standing README
    adjudication).
  * FERC eLibrary (Settlement-Agreement informational filings) — monthly/
    quarterly aggregates admissible for LEVEL corroboration only.
  * Third-party archives of the deprecated RT Data Broker (e.g. gridstatus) —
    CORROBORATION only, provenance disclosed, never an intake and never a gate
    input.
* **H-2 (South-region hourly actual load):** MISO regional forecast-and-actual
  load market reports (`rf_al` family) on the proven host; EIA-930 subregion
  demand six-month bulk CSVs (no key) if MISO subregions exist there.
* **H-3 (South-region hourly generation):** MISO regional generation fuel-mix
  market reports (the RT displays' regional split, if archived as a report);
  EIA-930 carries NO subregional generation (declared now).

Intake convention if a source lands: `data/raw/miso-regional-balance/` (or the
RDT series beside the existing `transfer-constraint-binding/MISO/`), README +
fetch script per the pbc precedent, consolidated per-year `.csv.gz`, committed
if small (gitignored + SHA256SUMS per the corpus conversion class if bulky),
**2023–2025 market dates only** (rule 22 quarantine; the fetch refuses
out-of-train years). No clean-datatype extension — diagnostic consumers read
the mirrors directly (the transfer-constraint-binding precedent).

If H-2/H-3 fail, Leg 2 falls away and the reduced mapping applies (V-TRANSFER
becomes undecidable; V-BASIS still requires Leg 3). If H-1 fails, Leg 3 falls
away (V-BASIS then unreachable — Leg 4 cannot establish it) and the reachable
verdicts are V-TRADE (via Leg 2 + Leg 4 wheel-clean), V-TRANSFER, V-UNRESOLVED.

## 6. Anti-sweep and DO-NOT-REDO

**Anti-sweep (binding).** The hour key, clock mappings, hour sets, the pool
definition, the Leg-2 interval construction and spread classification, the
`s2`/`β`/`D4` statistics, every numeric line in §3–§4 (0.5 / 0.25 / 0.15 /
0.3 GW / 0.75 GW / the 6-of-12 majority / the ±15 % 3a band), and the verdict
mapping are **frozen by this document**. No alternative key, set, statistic,
threshold, or classification may be computed after seeing a result, and none
may be quoted from this session. A result that lands against interest is
reported at full magnitude. Statistics labelled "reported-only" never migrate
into a gate.

**DO-NOT-REDO** (the miso-182 charter list, carried in full, PLUS its
addition): `miso_south_firm_export_block` `G` (re-open only per the miso-182
§6b conditions — an EQR-based firm-sale series clearing the three named
questions, or a published by-counterparty contract-path series);
`miso_seam_coincident_envelope` `R` (no variant of its frozen
grid/driver/statistic — noting Leg 4's D4 is a BINDING-INDICATOR contrast on
the measured pbc record, not a flow-envelope statistic, and 3b's `β` is a
wheel-leakage regression against an RDT series, neither computable from the
seam flow alone; neither reproduces that cell's construction);
`measured_interface_limits` `R`; `m2m_seam_entitlement_cap` `G`;
`import_shape_lever` `G`; `internal_congestion_split` `G`; `zonal_loss_surface`
`R`; within-unit `measured_offer_surface` `R`; `gas_hub_basis_overlay` `R`;
`ramp_envelopes` `I`; `dam_availability_rebasis` `R`; the ordc/reserve
families; the dispersion family; and the **`miso_offer_spread_anchored`
unspent re-open clause** — untouched; this session may not be cited as graft
evidence.

## 7. Governance

Rule 22 `[R-HOLDOUT]`: **2023/2024/2025 ONLY**; MISO holds **neither**
`complete` nor `final` (fail-closed); the holdout spend freeze is **ACTIVE**
and untouched; no marker re-key owed. Rule 15 not engaged — no solve, no run
to register. Rule 26(b): §5.4 queue stamp + calibration-log entry in-session;
**no cell minted** (§4). Rule 27 `[R-PUSH]`: exact on-disk bytes; blobs ≥ 300
lines verified after every push. No new `.github/workflows`. Owner decision
points (D-4 posture; the standing miso-174-pattern items) restated in the
finding, decided by none of this.

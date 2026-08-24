# FINDING miso-182 — the D-3 South under-export driver hunt: the seam is 86 % TVA, not SOCO/TVA/AECI; the Manitoba flat-block FORM survives its own kill but reaches only a quarter of the 2025 object; and the driver ladder REFUSES on the one thing no publication separates — MISO's own Midwest↔South RDT wheel from a genuine external sale. `miso_south_firm_export_block` minted `G`, NO LP

**Session miso-182 (2026-08-24).** Executes
`PREREG-miso182-south-export-driver-2026-08-24.md` (committed and pushed at
`50efc4d` **BEFORE** any adjudicating quantity was computed; the probe + record
landed at `53cd17a`, in the prereg's own order). **NO LP SPENT. Keeper
`2026-08-22-miso-177-rho-measured` (`miso177_rho_B`) UNCHANGED; nothing armed,
no `ScenarioConfig` field created, no run registered** (rule 15
`[R-DASHBOARD]` not engaged; the miso-142…181 no-LP precedent). Determination
unchanged: **NOT-YET on C3a-2025 alone**, C3c the single ledgered caveat.

Instrument (read-only, reproducing from committed artifacts + measured series):
`scripts/probes/_miso182_south_export_driver.py` →
`results/calibration/_miso182_south_export_driver.json`.

## 0. The verdict

**`miso_south_firm_export_block` at MISO: minted `G` (data-refused)**, by the
pre-registered verdict mapping (PREREG §4: K-1 clears, G-2 fails ⇒ `G`).

* **K-1, the load-bearing FORM test, CLEARED — reported first because it runs
  against this session's conclusion.** The Manitoba-precedent annual-flat block
  does **not** worsen the scarce-set residual in any year (0/3 against the ≥2
  line). The form is *not* refuted. But the block the Manitoba identification
  produces is **+0.185 / +0.188 / +0.281 GW**, against scarce-set gaps of
  **+0.633 / +0.350 / +1.191 GW** — it reaches **29 % / 54 % / 24 %** of the
  object. It clears by being too small to do harm.
* **The charter's own premise is corrected by the measurement.** The South seam
  is **not** "SOCO/TVA/AECI". It is **TVA at 79 / 86 / 86 %** of gross export.
  MISO is a **net importer** from SOCO in all three years and from AECI in
  2024–25, and **essentially never exports to SOCO** (0.1–0.3 % of the pool's
  gross export) — the very BA the model's South seam names as its reference
  (`ba_code="SOCO"`).
* **G-2 fails on criterion 2 (placeable at our grain without inventing an
  apportionment).** MISO's Midwest↔South **Regional Directional Transfer** is a
  *calculated* contract-path quantity defined in the MISO/SPP/**Joint Parties**
  Settlement Agreement — the Joint Parties being AECI, LG&E/KU, PowerSouth,
  Southern Co. and **TVA**, i.e. the South seam's own DIBA pool — and MISO
  compensates them for use of their systems above its 1,000 MW of owned contract
  path. **No publication decomposes measured MISO↔Joint-Party interchange into
  (a) MISO's own internal Midwest→South wheel and (b) a genuine external sale.**
  Without that split, a firm export block on this seam would model MISO's
  **internal** transfer as an **external** sale — a rule 14 `[R-ACCURATE]`
  representation misalignment, and a rule 19 `[R-ONE-MECH]` double-count of a
  transfer the keeper **already carries internally** (`miso_rdt_tcdc=True`,
  `MISO_RDT_CONTRACT_N_TO_S_MW = 3000.0`).

The quantitative corroboration is hard to ignore and is stated in §6: in MISO's
47 scarcest hours of 2025 the measured MISO→TVA net export averages **2,720 MW**
against the model's own **derated** RDT north-to-south limit of
0.92 × 3,000 = **2,760 MW** — 40 MW, **1.4 %**, below it.

## 1. Footing (hard gate, passed exactly)

The probe reproduces the committed miso-174 object with no drift:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| scarce-set size (summer ∩ RT > $200) | **11** | **14** | **47** |
| measured South net import, annual (GW) | −1.071 | −1.354 | −1.031 |
| miso-174's committed value | −1.071 | −1.354 | −1.031 |
| **South scarce gap (GW)** | **+0.633** | **+0.350** | **+1.191** |
| miso-174 §1's committed gap | +0.63 | +0.35 | +1.19 |

Hour key: the committed **−1 h** DIBA key (miso-174 §4 / miso-175), frozen by
the PREREG and **not** re-solved. Model-side per-seam numbers are **cited** from
`_miso174_seam_overimport_decomposition.json` — the only MISO bundle carrying
`unit_hourly` (`miso169_gated_A`) is **pruned** (miso-181 §5) — with its measured
vintage drift carried, exactly as miso-174 disclosed it.

## 2. The seam is TVA — the charter's premise, corrected

Measured **net export** (GW, + = MISO exports), and each counterparty's share of
the pool's **gross** export:

| 2025 | annual | summer | **scarce** | gross-export share |
|---|---:|---:|---:|---:|
| **TVA** | **+1.897** | **+1.911** | **+2.720** | **85.8 % [MATERIAL]** |
| LGEE | +0.242 | +0.133 | +0.002 | 12.6 % |
| AECI | −0.444 | −0.449 | −0.405 | 1.4 % |
| SOCO | −0.665 | −0.841 | −0.950 | 0.2 % |
| SIKE | −0.079 | — | — | 0.0 % |
| **SEAM** | **+1.031** | **+0.754** | **+1.368** | |

2023 and 2024 carry the same structure (TVA 79.2 % / 85.7 %; SOCO gross-export
share 0.3 % / 0.1 %). **SIKE has 24 rows in 2025 and none in 2023–24** — reported
absent and excluded from every gate, never silently dropped.

Two consequences the charter could not have known:

1. **Only TVA is material** (the sole counterparty above the pre-registered
   ≥20 % line), so the "South seam" object is a **MISO↔TVA** object.
2. **The pool nets opposing physical flows.** A block on the *aggregate* seam
   would net a +1.9 GW TVA export against ~1.1 GW of SOCO+AECI imports — the
   rule 14 misalignment clause in miniature. And the pattern itself — **a large
   export to one neighbour with offsetting imports from the others** — is the
   signature §6 turns on.

## 3. K-1 — the form test, and why clearing it settles less than it seems

`B_y` closes the **annual** gap (the Manitoba identification: one number per
year, no shape, no window); it is then applied flat to all 8,760 hours and the
**scarce** residual recomputed:

| year | `B_y` (GW) | scarce gap before | residual after | |
|---|---:|---:|---:|---|
| 2023 | +0.185 | +0.633 | +0.448 | improved |
| 2024 | +0.188 | +0.350 | +0.161 | improved |
| 2025 | +0.281 | +1.191 | +0.910 | improved |

**0 of 3 years worsened → K-1 CLEARS.** The flat firm block is a *directionally
correct* object: being price-insensitive, it survives into the scarce hours,
which is exactly the property the phenomenon needs. **This is reported first and
in full because it runs against this session's `G` close.**

What it does not settle: the annual-mean identification **undersizes** the
mechanism against a defect that is concentrated, so the block leaves
**71 % / 46 % / 76 %** of the scarce gap standing.

## 4. Where the object actually lives: the MODEL's export collapses, reality's does not

The decomposition that explains §3, and the most useful number this session
produces:

| net export (GW) | model annual → scarce | measured annual → scarce |
|---|---|---|
| 2023 | +0.886 → **+0.371** (42 %) | +1.071 → +1.004 (94 %) |
| 2024 | +1.166 → **+0.511** (44 %) | +1.354 → +0.861 (64 %) |
| 2025 | +0.750 → **+0.177** (24 %) | +1.031 → +1.368 (133 %) |

**The model withdraws 56–76 % of its South export in its own scarce hours;
the measured seam holds or expands.** Splitting each scarce gap into a level
component (`B_y`) and a stress-response component:

| | level (`B_y`) | **stress response** |
|---|---:|---:|
| 2023 | +0.185 (29 %) | **+0.448 (71 %)** |
| 2024 | +0.188 (54 %) | **+0.161 (46 %)** |
| 2025 | +0.281 (24 %) | **+0.910 (76 %)** |

The mechanism of the model's withdrawal is fully visible in the armed keeper and
needs no new measurement: the **South export ladder's top band is $53.00/MWh**
in 2025 (`MISO_SEAM_LADDER_BY_YEAR[2025]["South"]["export"]` =
53.00, 44.14, 37.04, 32.38, 29.43, 26.61, 24.29, 22.35). The model's South
export is a willingness-to-pay curve that **shuts off once MISO's own price
clears ~$53** — and the scarce set is defined at RT > $200, with a measured mean
of $479. So the model exports ~nothing there **by construction**, while the
measured seam moved 1.37 GW.

## 5. G-1b — the signature, and a defect in my own instrument (against interest)

Anchored midpoint scoring against MHEB (Manitoba) and PJM, thresholds derived
**from the anchors**, per the PREREG:

| | TVA 2023 | TVA 2024 | TVA 2025 | verdict |
|---|---|---|---|---|
| Manitoba-side hits | 3/6 | **0/5** | **1/6** | **fails 2 of 3 years** |

**But the failure is substantially an artifact of the anchor, and I am
reporting that against my own instrument.** On the *intrinsic* firm-block
dimensions TVA is the **most block-like series in the entire table**:

| 2024 | S-2 seasonality CV | S-4 volatility ÷ level | S-5 \|r\| vs price |
|---|---:|---:|---:|
| **TVA** | **0.10** | **0.073** | **0.018** |
| MHEB (the "firm block" anchor) | 1.09 | 0.415 | 0.203 |
| PJM | 0.29 | 0.105 | 0.201 |

TVA is steadier, flatter and less price-correlated than the anchor that is
supposed to *represent* firmness. The reason is now obvious and should have been
anticipated at design time: **the Manitoba precedent is a fact about the model's
representation (a flat block), not about the measured MHEB series** — which is a
volatile, strongly seasonal, drought-affected hydro seam (2025 annual level
113 MW, S-4 rel 1.249). Scoring an export seam against it penalises exactly the
behaviour a firm block is supposed to have.

So G-1b's numeric verdict is **not** load-bearing evidence that TVA is
arbitrage-like, and this finding does not use it as such. The PREREG's decision
to make G-1b supporting-only is what keeps that error non-fatal. **The one
dimension where TVA genuinely sides with PJM is the substantive one — S-3, the
stress response** (net-import terms, + = the seam helps MISO):

| S-3 (GW) | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| MHEB | +0.57 | +0.48 | +1.19 |
| **TVA** | −0.06 | −0.08 | **−0.81** |
| PJM | −0.73 | −0.46 | −1.06 |

Under MISO's own scarcity the TVA seam takes **more** energy out of MISO — in
2025 nearly as hard as the PJM seam pulls away. §6 is where that stops looking
like conduct and starts looking like accounting.

## 6. G-2 — the driver ladder, and the finding that refuses it

Public-records hunt against the four pre-registered criteria. What exists:

* **The MISO–SPP–Joint Parties Settlement Agreement** (FERC-approved, 2015–16)
  governs compensation for use of **as-available, non-firm** capacity on
  neighbouring systems for MISO's Midwest↔South transfers. Joint Parties: AECI,
  **LG&E/KU**, PowerSouth, **Southern Co.** and **TVA**.
* **The RDT is a *calculated* value defined in that Settlement Agreement**, with
  a north-to-south limit of **3,000 MW** — the constant the keeper already
  carries (`MISO_RDT_CONTRACT_N_TO_S_MW`, sourced in `constants.py` to the
  MISO/SPP JOA Attach. A and the 2024 MISO SOM §III.B).
* MISO compensates SPP and the Joint Parties for system use **above MISO's
  existing 1,000 MW of contract path**.
* **MISO–TVA "emergency energy"** sales agreement, filed at FERC 2024-10-24 — an
  emergency construct, post-dating most of the window, and not a firm block.

**Criterion 1 (exists): PARTIAL.** The constructs are real and documented. What
is not documented is a *firm export MW series* to these counterparties.

**Criterion 2 (placeable at our grain without inventing an apportionment):
FAILS — and this is the load-bearing refusal.** MISO's two footprints are not
directly interconnected; the Midwest↔South transfer moves across the Joint
Parties' systems, and those are the same BAs whose EIA-930 interchange with MISO
constitutes the "South seam". **Nothing published decomposes measured
MISO↔Joint-Party interchange into the RDT wheel and a genuine third-party
sale.** The corroboration that this is not a hypothetical contamination:

1. **The scarce-hour level matches the derated RDT limit.** Measured MISO→TVA in
   the 47 scarcest hours of 2025: **2,720 MW**. The keeper's own derated N→S
   limit: 0.92 × 3,000 = **2,760 MW** (`MISO_RDT_DEFAULT_DERATE_FRAC`, the
   published MISO standing practice). The measured mean sits **1.4 % below the
   derated contract limit** — where a transfer running at its limit would sit.
2. **The counterparty pattern is a wheel's pattern**, and it is the pattern §2
   measured under the frozen PREREG: a large export to **one** neighbour (TVA
   +1.9 GW) with **offsetting imports** from the others (SOCO −0.67, AECI
   −0.44 GW) — energy leaving MISO at one boundary and re-entering at others.
3. **2025 is the year MISO's own RDT bound N→S for 5,086 hours** (miso-174 §5) —
   the year the measured MISO→TVA "export" is largest and the model's South
   export smallest.

If that reading is right, then the model is **not** under-exporting: it is
representing the Midwest→South transfer **internally**, where it belongs, while
the measured comparator books it **externally** at the TVA boundary. The
"+1.19 GW South under-export" would then be substantially a
**basis/representation artifact**, not a model defect — and a firm export block
built to close it would be **fitting the model to a bookkeeping difference**,
the plainest possible rule 1 `[R-STRUCT]` violation.

**This session does not claim that reading as established**, and says so
plainly: the decomposition was **not measured**, because the PREREG's anti-sweep
clause forbids adding a statistic after seeing a result, and no admissible
published series performs the split. What is established is the **refusal**: the
apportionment does not exist in any publication found, and **inventing one is
exactly what miso-77 §5.2 and miso-176 K-2 already refused twice**
(`m2m_seam_entitlement_cap` `G`). The same objection, at the same seam, for the
same reason.

**Criteria 3 (forward-regenerable) and 4 (free of measured-outcome content)** are
**not reached** — criterion 2 is dispositive, and a series that cannot be placed
cannot be evaluated for forward regeneration. Reported so no successor mistakes
silence for a pass.

**What would re-open the cell** (new evidence, not a variant sweep): a published
series that separates MISO's Midwest↔South contract-path schedules from
third-party sales at the counterparty grain — e.g. MISO's own RDT flow published
with counterparty resolution, or Settlement-Agreement schedule data at MW grain
with the wheel identified. FERC EQR firm-sale records and MISO OASIS firm
point-to-point reservations are the named places to look; neither was
established here as providing the **split**, which is the binding requirement.

## 7. What this closes and what it opens

* **CLOSED: the D-3 firm/contract export block, in the chartered form.**
  `miso_south_firm_export_block` `G` at MISO; no field; keeper unchanged. The
  driver hunt the charter ordered was run and returned a **refusal with a
  reason**, not a mechanism.
* **The South under-export is now a DIFFERENT object than the charter thought,
  and is disclosed as such.** It is a MISO↔**TVA** object; **46–76 % of it is
  the model's own price-elastic export collapsing** where the measured series
  does not; and a material share of the measured comparator is plausibly MISO's
  own internal RDT wheel. It stays quotable **only as a defect of unestablished
  magnitude**, and NOT as a lever.
* **NEWLY NAMED, and the highest-value successor: the South-seam MEASUREMENT
  BASIS question.** Before any South mechanism is ever chartered, a session must
  establish what share of measured MISO↔{TVA, SOCO, AECI, LGEE} interchange is
  the RDT wheel. That is a **basis/validation** question, not a mechanism — it
  costs no LP, it is admissible (it touches no forecast input), and **it can
  invalidate the object rather than tune it**. It should be D-3's replacement at
  the queue head.
* **A rule-14 representation item, named not stamped:** the model's South seam
  carries `ba_code="SOCO"` while **SOCO is the one counterparty MISO essentially
  never exports to** (0.1–0.3 % of gross export). Under the armed
  `miso_seam_measured_ladder` the ladder prices the bands directly, so the
  pricing role of `ba_code` is largely superseded — **this session did not
  measure whether it is live**, and does not claim a defect. Handed forward for a
  successor to check, in the miso-174 §4 pattern (that hour-key rotation was
  found the same way).
* **D-4 (the determination-posture owner question) is unchanged and sharpened
  again:** C3a-2025 remains the SOLE failing criterion on a keeper with zero D-4
  conduct failures, C6 attested, C8 PASS all years. The offer family is exhausted
  (miso-179/180), the import-side seam family is adjudicated end to end
  (interface limits `R`, entitlement cap `G`, response envelope `R`), and the
  export-side candidate is now `G`. **Every named lever in MISO's queue has been
  adjudicated without a mechanism surviving** — and this session adds that the
  largest remaining named object may not be a model defect at all.

## 8. Reported against interest

* **K-1, the load-bearing gate, CLEARED.** The chartered form was not refuted;
  it is refused on the driver, one rung later. A successor with a published
  apportionment could legitimately return to it.
* **G-1b's numeric verdict is unreliable and I say so** (§5): the anchored
  construction penalises TVA for being *unlike the measured MHEB series*, which
  is not the same as being unlike a firm block — on intrinsic firmness TVA beats
  the anchor on every dimension. The instrument was mis-designed; the PREREG's
  supporting-only status is the only reason it does not matter.
* **The RDT-contamination reading is a hypothesis with corroboration, not a
  measurement.** Three independent corroborations (§6) point one way; none is
  proof, and the confirming decomposition was deliberately **not** computed
  under this session's own anti-sweep clause.
* **A pure wheel would partly net out inside the MISO↔TVA DIBA pair** (out at one
  tie, back at another, both booked to the same counterparty), so contamination
  cannot be inferred from the TVA level alone — which is precisely why the
  offsetting SOCO/AECI imports and the derated-limit coincidence are cited
  together rather than any one of them alone. Stated so the reading is not
  over-sold.
* **2024's numbers carry the published EIA-930 internal inconsistency**
  (DIBA↔BALANCE r = 0.8286; miso-174 §5). Nothing here depends on 2024 alone:
  the K-1 result is 0/3, and §2's composition and §4's collapse hold in 2023 and
  2025 on clean substrate (r = 1.0000 / 0.999998).
* **The model side is a cited vintage** (`miso169_gated_A`, pruned), not the
  keeper, with its measured drift disclosed — as miso-174 disclosed it. The
  footing (§1) is measured on the keeper's own hour sets and does not depend
  on it.
* **SIKE is effectively absent** (24 rows, 2025 only) — reported, excluded, never
  silently dropped.

## 9. Standing OWNER items, restated not decided

Carried forward unchanged (the miso-174/175/176/178/181 pattern); this session
raises them and decides none: (1) the **C8 provenance-materiality floor** (rubric
hole unrepaired); (2) the **committed-vs-regenerated diagnostics exposure**
(MISO and PJM, measured; unchanged in kind); (3) **`RHO_CLIP` 0.5 vs the measured
MISO rho 0.1764** (nyiso-144); (4) **MISO's determination posture** — §7 above.

## 10. Governance

Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds neither `complete` nor `final`
(fail-closed); the holdout spend freeze untouched; no marker re-key owed.
Rule 26(b): the `miso_south_firm_export_block` base row + a cell line in every
ISO shard minted in this session (MISO `G` with this evidence; the five others
`·` — rule 25: the construction and the refusal are MISO-South-seam-specific),
plus the §5.4 queue stamp and the calibration-log entry. Rule 15 not engaged —
no solve, no run to register. Rule 27 `[R-PUSH]`: exact on-disk bytes, blobs
≥300 lines verified after every push. No new `.github/workflows`.

**DO-NOT-REDO honoured throughout.** Nothing re-opened `measured_interface_limits`
`R`, `m2m_seam_entitlement_cap` `G`, `import_shape_lever` `G`,
`internal_congestion_split` `G`, `zonal_loss_surface` `R`, the within-unit
`measured_offer_surface` `R`, `gas_hub_basis_overlay` `R`, `ramp_envelopes` `I`,
`dam_availability_rebasis` `R`, the ordc/reserve families, the dispersion family,
or **`miso_seam_coincident_envelope` `R`** (no variant of its frozen
grid/driver/statistic was computed — and note §4's stress-response component is
the EXPORT-side analogue of that refuted import-side object, named here and
deliberately **not** measured as an envelope). The
**`miso_offer_spread_anchored` re-open clause was not touched and remains
unspent**; this session may not be cited as graft evidence.

## 11. Reproduction

```
cd <repo root> && uv run --no-project \
  --with pyarrow,pandas,numpy,pydantic,scipy,openpyxl,pyyaml --python 3.12 \
  python scripts/probes/_miso182_south_export_driver.py
```

Reads `data/raw/eia-930-interchange/MISO interchange hourly.parquet`,
`data/raw/_validation-source/{actual_lmp_hourly_MISO,actual_lmp_hourly_zonal_MISO}.parquet`,
and the committed `results/calibration/_miso174_seam_overimport_decomposition.json`
(model side; the `miso169_gated_A` `unit_hourly` bundle is pruned). Record:
`results/calibration/_miso182_south_export_driver.json`. PREREG:
`PREREG-miso182-south-export-driver-2026-08-24.md` (commit `50efc4d`).

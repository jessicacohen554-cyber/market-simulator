# PREREG miso-174 — the scarce-hour over-import and `measured_interface_limits`: a NO-LP inertness pre-check with fixed kills

**Session miso-174, 2026-08-21.** Keeper `2026-08-20-miso-173-layup-mask`
(bundle `miso173_layupmask`). **Nothing is armed by this document.** It
pre-registers, with thresholds fixed BEFORE the gated quantities are computed,
the pre-check that decides whether the matrix cell `measured_interface_limits`
(MISO `U`) is worth an LP at all — the miso-167 §3 **K-PRE-A** pattern, whose
precedent (miso-171 §4) is that a pre-check kill adjudicates a cell **without a
solve**.

Order of operations, auditable in the commit history: the Phase-0
decomposition (§1, already measured) → **this document, committed** → the
pre-check quantities (§3) → the adjudication.

---

## 1. The object, as measured (Phase 0, already run — not gated by this prereg)

Instrument `scripts/probes/_miso174_seam_overimport_decomposition.py`, record
`results/calibration/_miso174_seam_overimport_decomposition.json`. Read-only;
no LP; nothing re-enters a solve (rule 13 `[R-MEASURED]`).

**The defect reproduces on the CURRENT keeper** (miso-166/167 §2d measured it
on the miso-160-era keeper). Summer hours MISO's own RT market priced
> $200/MWh:

| year | n | model net interchange | EIA-930 net | **over-import** |
|---|---:|---:|---:|---:|
| 2023 | 11 | +6.95 GW | +5.09 GW | **+1.86 GW** |
| 2024 | 14 | +5.22 GW | +4.18 GW | **+1.04 GW** |
| 2025 | 47 | +5.39 GW | +3.97 GW | **+1.41 GW** |

3-year mean **+1.44 GW**.

**Seam decomposition** (measured side: EIA-930 BA-to-BA DIBA product pooled by
`MISO_SEAM_DIBA`, hour key solved at −1 h against the independently-keyed
BALANCE `TI` series, r = 1.0000 / 0.8286 / 1.0000; model side: the priced-seam
pseudo-generator rows from `miso169_gated_A`, the only MISO bundle carrying
`unit_hourly`, whose aggregate drift vs the current keeper in these hours is
−0.099 / −0.034 / −0.089 GW — measured, not assumed):

| seam | 2023 gap | 2024 gap | 2025 gap | model side |
|---|---:|---:|---:|---|
| PJM (PJM+IESO) | **+0.87** | **+0.72** | **+0.94** | gross IMPORT 5.76 / 4.17 / 4.37 GW, gross export 0 |
| SPP (SWPP+SPA) | +0.41 | +0.25 | −0.34 | gross import 0.18 / 0.23 / 0.61 GW |
| South (SOCO,TVA,AECI,LGEE,SIKE) | +0.63 | +0.35 | **+1.19** | gross import ≈0; gross EXPORT −0.38 / −0.56 / −0.21 GW |
| Manitoba (MHEB) | −0.15 | −0.26 | −0.46 | gross import 1.28 / 1.31 / 0.49 GW |

**The object is not one defect.** Only the PJM seam (and SPP in 2023/24) is an
IMPORT-side gap an import ceiling could reach. The South gap is an **EXPORT**
gap — the model already imports ≈0 there and simply under-exports the 1.0–1.4 GW
MISO actually ships south — and Manitoba is an **under**-import an import
ceiling can only worsen.

**The armed p90 envelope's binding surface** (`miso_seam_flow_limit`, armed on
the keeper; per-(month × hour-of-day) p90 of the measured directed flow), share
of scarce hours the model's PJM gross import sits at that seam's own hourly cap:
**9.1 % (2023) / 78.6 % (2024) / 44.7 % (2025)**.

---

## 2. What is being decided

Whether `measured_interface_limits` — a MEASURED interface/transfer-limit input
replacing an estimate (rule 14 `[R-ACCURATE]`) — has an admissible, non-inert
instance at MISO. Two readings are on the table and BOTH are gated here:

* **(a) SEAM basis.** A measured MW limit on MISO's external seams, tighter or
  better-shaped than the armed EIA-930 p90 deliverability envelope.
* **(b) ZONAL basis** (the reading the matrix cell carries). MISO's six Midwest
  zones ship internal links at a deliberately non-binding
  **`ttc_mw = 40,000`** placeholder (`config/iso_configs.py::_miso_config`),
  with the real internal constraint carried by the seasonal CIL/CEL interface
  groups (`build_miso_deliverability_groups`) and the RDT (Plains↔South
  3,000/2,500 MW). Replacing those placeholders with measured LRZ-pair limits.

---

## 3. The pre-check, with kills fixed NOW

All four run read-only on committed artifacts. **No LP.** A kill is a
DO-NOT-SOLVE and, per the miso-171 precedent, adjudicates the cell in-session.

### K-PRE-1 — CAPABILITY EXCEEDANCE (the load-bearing kill)

For each seam, over the scarce set: the share of hours in which the model's
gross import **exceeds the measured MAXIMUM** ever observed on that seam in the
same (month × hour-of-day) bucket of the same year — i.e. the p100 of the exact
bucket population the production envelope takes its p90 from.

*Why this is the right test.* An interface-**limit** defect requires the model
to be moving more energy than the seam has been observed to deliver. If the
model's scarce-hour flow sits INSIDE the historically-observed transfer
envelope, the flow is deliverable and the over-import is a **price-formation**
object — the neighbour is priced too cheap — which is the matrix cell
`import_shape_lever`, MISO **`G`** (governance-refused, miso-123 / miso-114 §4).
Arming a limit against a price defect is a rule 19 `[R-ONE-MECH]` breach and a
rule 1 `[R-STRUCT]` breach (reaching a number through a mechanism that is not
the real one).

**KILL (a) if** the capability-exceedance share on the PJM seam — the seam
carrying the largest positive gap — is **< 20 %** of scarce hours in **≥ 2 of 3
years**.

### K-PRE-2 — REACH

Hour-wise upper bound on ANY admissible import-side ceiling, over the scarce
set:

`reach = mean_h [ Σ_seam max(0, model_gross_import_{s,h} − measured_net_import_{s,h}) ]`

An admissible capability envelope is never set BELOW the transfer actually
observed in that hour (that would be a measured limit contradicted by measured
flow), so this bounds the reach of every admissible import ceiling, including
the inadmissible flow-pinned one.

**KILL (a) if** reach **< 0.50 GW** (≈ 35 % of the +1.44 GW object) in **≥ 2 of
3 years**.

### K-PRE-3 — ZONAL-BASIS REDUNDANCY AND EXCEEDANCE (rule 19)

Reading (b) is killed if **either**:

* **(i)** no measured MW-limit series exists at LRZ-pair grain that is
  reconcilable to the model's six-zone reduction **without inventing an
  apportionment** (the M1 refutation of
  `docs/handoffs/miso-nc-price-separation-design-2026-07.md` §3, re-affirmed by
  `docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md` §5.2: *no PTDF /
  shift-factor data is published anywhere in the family*); **or**
* **(ii)** the phenomenon already has an owner — the armed seasonal CIL/CEL
  interface-group family plus the armed RDT/TCDC — so a second internal limit
  would stack on the same phenomenon (rule 19).

Reported alongside as evidence, not as a kill: the share of scarce hours in
which the keeper's Midwest zonal prices separate (a binding internal
constraint's observable signature in the committed artifacts).

### K-PRE-4 — DATA ADMISSIBILITY AT SEAM GRAIN

Documentary, decided against the committed record. Reading (a) is killed if no
measured per-seam MW interface-limit series is available that is **both**
(i) at seam grain, or reconcilable to it without inventing an apportionment
(rule 14's misalignment clause), **and** (ii) not the series already armed.

---

## 4. Reported, never a kill, and never a claim

* **Price reach.** The over-import's price value at the model's OWN local
  supply slope inside the scarce set. Reported so the record is honest about
  magnitude; it is **not** a gate and **not** a C3a-2025 claim.
* **The 2024 EIA-930 internal inconsistency.** At the solved −1 h key the DIBA
  product reconciles to the BALANCE `TI` series exactly in 2023 and 2025
  (r = 1.0000) but only at r = 0.8286 in 2024. Disclosed with its magnitude;
  the 2024 seam split is reported with that caveat attached.
* **The `unit_hourly` vintage.** The per-seam model split is read from
  `miso169_gated_A`. Its drift vs the current keeper is measured (§1) and
  reported with every model-side number.

## 5. The honest ceiling, stated BEFORE any result (charter item 3)

**C3a-2025 is CLOSED END TO END as a model-class limit** — the RT-only half by
the miso-163 owner ruling, the DA-foreseen half by
`FINDING-miso171-reserve-requirement-decomposition-2026-08-20.md` §6. Removing
phantom import is a rule-1 `[R-STRUCT]` / rule-14 `[R-ACCURATE]` repair of the
supply-demand balance in tight hours and **may be kept on that ground alone**.
It **must not** be sold as, or tuned toward, closing C3a-2025, and no number
produced by this lane may be quoted against that gate.

## 6. If nothing is killed

A surviving reading gets its OWN prereg with pre-solve ENGINE-frozen predictions
(the miso-173 discipline — CSV-level instruments are blind to composition), its
own DOF answer, a gated `ScenarioConfig` field defaulting off, a matrix row plus
a cell line in EVERY ISO shard in the same PR (rule 28c), control + arm both
registered (rule 15), and the cell stamped in this session.

## 7. Governance

Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the holdout
spend freeze is untouched; no marker re-key is owed. No run is registered by a
no-LP adjudication (the miso-142/153/155/156/157/161/163/164/167/171 precedent).

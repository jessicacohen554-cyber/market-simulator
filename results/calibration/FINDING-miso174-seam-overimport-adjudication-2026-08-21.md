# FINDING miso-174 — the +1.33 GW scarce-hour over-import decomposed, and `measured_interface_limits` REFUTED at MISO on a pre-registered no-LP kill

**Session miso-174 (2026-08-21).** Executes scope items 1 and 3 of the miso-174
charter. **NO LP SPENT. Keeper `2026-08-20-miso-173-layup-mask`
(`miso173_layupmask`) UNCHANGED; nothing armed, no `ScenarioConfig` field
added, no run registered** (the
miso-142/153/155/156/157/161/163/164/167/171 no-LP precedent; rule 15
`[R-DASHBOARD]` not engaged). Determination unchanged: **NOT-YET on C3a-2025
alone**, C3c the single ledgered caveat.

Instruments, all read-only, all reproducing from committed artifacts:

| instrument | record |
|---|---|
| `scripts/probes/_miso174_seam_overimport_decomposition.py` | `_miso174_seam_overimport_decomposition.json` |
| `scripts/probes/_miso174_import_limit_precheck.py` | `_miso174_import_limit_precheck.json` |
| `scripts/probes/_miso174_seam_price_evidence.py` | `_miso174_seam_price_evidence.json` |

Kills fixed in `PREREG-miso174-seam-import-limit-precheck-2026-08-21.md`,
committed at **6cd0335 BEFORE** the gated quantities were computed.

---

## 0. The verdict

**`measured_interface_limits` at MISO: `U` → `R` (REJECTED), no solve spent.**
The pre-registered load-bearing kill **K-PRE-1 fires at its maximum strength**:
across all 72 scarce hours of 2023–2025 the model's gross import **never once**
exceeds the largest transfer that seam has been observed to deliver in the same
(month × hour-of-day) bucket of the same year — **0/11, 0/14, 0/47 on the PJM
seam**, and 0/72 on SPP, under **both** hour-key conventions. There is no
capability violation to repair. Arming an interface limit against a phenomenon
that is not a limit violation is a rule 1 `[R-STRUCT]` breach (reaching a number
through a mechanism that is not the real one) and a rule 19 `[R-ONE-MECH]`
breach.

**Reported against interest: the lever is NOT rejected for being small.**
K-PRE-2 (reach) **does not fire** — an import-side ceiling could touch
**2.74 / 2.25 / 2.97 GW** in the scarce hours against a 0.50 GW kill line. The
volume is there. The mechanism is wrong.

---

## 1. The object, reproduced on the CURRENT keeper

miso-166/167 §2d measured it on the miso-160-era keeper. It survives the three
keeper promotions since:

| year | n (summer, MISO RT > $200) | model net interchange | EIA-930 net | **over-import** |
|---|---:|---:|---:|---:|
| 2023 | 11 | +6.95 GW | +5.09 GW | **+1.86 GW** |
| 2024 | 14 | +5.22 GW | +4.18 GW | **+1.04 GW** |
| 2025 | 47 | +5.39 GW | +3.97 GW | **+1.41 GW** |

3-year mean **+1.44 GW** (the charter's +1.33 GW, re-measured on this keeper).

**It is not one defect.** Decomposed by seam (measured side: the EIA-930
BA-to-BA DIBA product pooled by `MISO_SEAM_DIBA`; model side: the priced-seam
pseudo-generator rows):

| seam | 2023 | 2024 | 2025 | what kind of gap |
|---|---:|---:|---:|---|
| **PJM** (PJM+IESO) | **+0.87** | **+0.72** | **+0.94** | model over-IMPORTS (gross export 0) |
| **SPP** (SWPP+SPA) | +0.41 | +0.25 | −0.34 | model over-imports 2023/24, UNDER-imports 2025 |
| **South** (SOCO,TVA,AECI,LGEE,SIKE) | +0.63 | +0.35 | **+1.19** | model under-**EXPORTS** — it imports ≈0 there |
| **Manitoba** (MHEB) | −0.15 | −0.26 | −0.46 | model UNDER-imports |

**Only the PJM seam is an import-side gap in all three years.** The South gap —
the largest single component in 2025 — is an EXPORT gap that no import ceiling
can reach (the model's South gross import is 0.00–0.05 GW). Manitoba is an
under-import an import ceiling could only worsen.

The decomposition closes against the aggregate: seam gaps sum to
+1.76 / +1.06 / +1.33 GW against the keeper-level +1.86 / +1.04 / +1.41, the
residual being the measured `unit_hourly` vintage drift (§5) and, in 2024, the
disclosed EIA-930 internal inconsistency (§5).

## 2. K-PRE-1 — the kill, at full strength

For every seam and every scarce hour: is the model's gross import above the
**maximum** measured transfer ever observed on that seam in the same
(month × hour-of-day) bucket of the same year — the p100 of the exact
population the armed p90 envelope draws from?

| year | PJM | SPP | South | Manitoba |
|---|---:|---:|---:|---:|
| 2023 | **0/11** | 0/11 | 4/11 | 1/11 |
| 2024 | **0/14** | 0/14 | 1/14 | 0/14 |
| 2025 | **0/47** | 0/47 | 1/47 | 1/47 |

Mean model gross import vs mean observed max, PJM: **5.76 vs 7.75 GW** (2023),
**4.16 vs 5.44** (2024), **4.37 vs 6.16** (2025) — the model sits 26–29 % below
the observed ceiling. The kill line was **< 20 % exceedance in ≥ 2 of 3 years**;
the measurement is **0 % in 3 of 3**.

The test is conservative in three independent ways, all against the kill:
model **gross** import is compared to measured **net** import (which understates
the gross transfer); the bucket max is tighter than the seam's annual max; and
the result is identical under the aligned and the production hour-key
conventions (§4). The three South hours and two Manitoba hours that do exceed
are buckets whose measured net import is negative (a seam MISO exports over), on
model flows of 0.00–0.05 GW — immaterial, and on the seam whose gap is
export-side anyway.

**K-PRE-4 (data admissibility) independently reaches the same place.** No
measured per-seam MW interface-limit series exists at our grain that is not
already armed:

* the **hourly operationally-binding derated limit is published by nobody** —
  MISO's RT Data Broker RDT endpoint is deprecated without archive and Data
  Exchange is key-gated (adjudicated 2026-07-11, re-verified 2026-07-12,
  `data/raw/transfer-constraint-binding/MISO/README.md`; re-confirmed
  `docs/handoffs/miso-77-m4-afc-feasibility-2026-07.md` §2c);
* `bc_HIST` / `pbc` carry **no MW limit and no flow**;
* PJM's `*_transfer_limits_and_flows.csv` is **PJM-internal** (AP-South,
  Bedington–Black Oak, AEP/DOM, Cleveland, 50045005) — it is the basis of
  `pjm_measured_interface_limits`, and none of its areas is the MISO seam
  (rule 14's misalignment clause);
* the M2M coordinated-flowgate ratings are **branch × contingency** grain and
  cannot be placed on a seam-aggregate link without inventing an
  apportionment — **no PTDF / shift-factor data is published anywhere in the
  family** (miso-77 §5.2, the standing M1 refutation);
* the EIA-930 directed-flow envelope **is already armed** (`miso_seam_flow_limit`
  / `miso_seam_export_limit`, p90, keeper-carried).

## 3. What the over-import actually is — the positive half

Having established that the flow is deliverable, the evidence names what sets
it. Two measurements, neither of which was pre-registered as a gate and neither
of which is a claim against C3a-2025 (§6):

**(a) The price incentive was real, large, and unarbitraged.** In MISO's scarce
hours the MISO-facing PJM border hub cleared at **$43 / $57 / $147** against
MISO's own RT at **$359 / $374 / $479** — spreads of **+$315 / +$317 / +$331**.
The border hub was above MISO's actual price in **0/11, 0/14, 3/47** hours. The
neighbour was not simultaneously scarce at the border (PJM's *system* RT reached
$283 in 2025, but its MISO-facing western hub did not follow). A market with
capability, a huge spread, and no arbitrage means something bound in reality
that is neither price nor the seam's own ceiling.

**(b) The real seam moves AWAY from MISO when MISO goes tight; the model's moves
toward it.** Seam net flow in the scarce hours against its own summer mean:

| seam | measured response | model response |
|---|---|---|
| **PJM** | **−0.77 / −0.54 / −1.03 GW** | **+0.89 / +0.48 / +1.34 GW** |
| SPP | −0.14 / +0.09 / +0.65 | +0.10 / +0.21 / +0.47 |
| South (export) | +0.00 / +0.23 / −0.61 | +0.49 / +0.64 / +0.69 |
| Manitoba | +0.57 / +0.48 / +1.19 | +0.58 / +0.82 / +0.67 |

**The sign is opposite on the PJM seam in every year.** And it is not a ramp
story: the real seam is *more* volatile hour-to-hour than the model's
(mean |Δ/h| 320–363 MW measured vs 142–172 MW modelled), and the measured seam
flow is essentially **uncorrelated with the measured spread** across the whole
summer (r = +0.062 / +0.047 / −0.057). MISO's real eastern seam does not
arbitrage the hourly spread at all; the model's priced seam is a
spread-arbitraging supply curve bounded only by a p90 envelope.

**Manitoba is the control that proves the diagnosis is specific.** It is the one
seam whose measured flow DOES respond to MISO's scarcity (+0.57/+0.48/+1.19),
and it is the one seam the model reproduces (+0.58/+0.82/+0.67) — because it is
the seam carried by a firm contract block rather than by spread arbitrage.

**This is a conduct/deliverability-at-coincident-peak object, not an interface
limit and not a neighbour-price level.** It is also NOT the matrix cell
`import_shape_lever` (MISO `G`, miso-123): that refusal concerns the seam's
hour-of-day price *shape*, and miso-123 exonerated the envelope family of the
hour-of-day defect at r = +0.81…+0.996. What is defective here is the seam's
response to **coincident system stress**, a dimension neither cell covers.

## 4. A DEFECT FOUND IN AN ARMED KEEPER MECHANISM — the seam envelope's hour key is rotated one hour

Reported, **not fixed here** (a fix changes the keeper and needs its own prereg
and control/arm pair; rule 19).

`data/eia930/envelopes.py::measured_seam_import_envelope` buckets the measured
series on the **raw** `local_time` stamp
(`local = pd.DatetimeIndex(frame["local_time"])`, lines 1014/1018) and applies
the bucket to the model's `hour % 24`. But `local_time` is **hour-ENDING** on
MISO's local standard clock — proven here by solving the key against the
independently-derived BALANCE `TI` series, where a **−1 h** shift reproduces
`TI` at **r = 1.0000** in 2023 and 2025. So the cap applied at model hour *h*
is built from the measured population of hour *h−1*.

Confirmed as an exact +1-hour rotation, not a level error: rolling the correctly
keyed p90 profile by +1 h reproduces the production cap to **mean |Δ| 2.9 MW
(2023) / 3.2 MW (2025)**, against **241 MW** at roll 0 (max 1,022 / 918 MW).
Annual mean cap level is unchanged (PJM 6.232 vs 6.231 GW).

**It is internally inconsistent with the repo's own conventions**, which is what
makes it a defect rather than a choice: the MISO seam **ladder** derivation
reads the same parquet and applies the conversion explicitly
(`scripts/data/derive_miso_seam_ladders.py:141`,
`t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)`), and the CAISO
analogue routes its stamps through a dedicated
`_caiso_interchange_model_clock` helper. So on the MISO seam a correctly keyed
price ladder is applied against a cap profile rotated one hour away from it.
Both armed directions (`miso_seam_flow_limit`, `miso_seam_export_limit`) are
affected. **The PJM analogue is not inspected here (rule 25); a cross-ISO check
is handed forward, not stamped.**

## 5. Reported against interest

* **K-PRE-2 does not fire** (§0) — the lever is refuted on mechanism, not on
  size.
* **The `unit_hourly` vintage.** The per-seam model split is read from
  `miso169_gated_A`, the only MISO bundle carrying `unit_hourly`. Its aggregate
  drift vs the current keeper in the scarce hours is **−0.099 / −0.034 /
  −0.089 GW** (max |Δ| 718 / 278 / 505 MW) — measured, and disclosed with every
  model-side number. The keeper-level object (§1) is measured on the keeper
  itself and does not depend on it.
* **A 2024 EIA-930 internal inconsistency.** At the solved key the DIBA product
  reconciles to the BALANCE `TI` series at **r = 1.0000** in 2023 and 2025 but
  only **r = 0.8286** in 2024, with complete DIBA coverage (8,784 h × 9 DIBAs)
  in every month — a value disagreement inside EIA's own publication, not a
  coverage hole. The 2024 seam split carries that caveat; the kill does not
  depend on 2024 (0/11 and 0/47 in the clean years alone clear the threshold).
* **Price reach, reported and not claimed.** At the model's own summer
  top-quintile supply slope (1.22 / 3.45 / 1.32 $/MWh per GW) the entire K-PRE-2
  reach is worth **+3.3 / +7.7 / +3.9 $/MWh** against scarce-hour gaps of
  $303 / $302 / $404. Even the inadmissible flow-pinned version of this lever is
  ~1–2.5 % of the miss.
* **The Midwest is a copper plate in the keeper.** Zonal price spread across the
  five Midwest zones is **exactly 0.00 in all 8,760 hours of all three years**;
  separation exists only against MISO-South (the RDT: 2,432 / 2,705 / 5,086 h).
  So neither the 40,000 MW placeholder internal links nor the seasonal CIL/CEL
  interface groups ever bind. The zonal-basis reading of the cell is therefore
  **not** refuted as redundant — nothing else binds — but it is refused on
  K-PRE-3(i) data admissibility (no LRZ-pair MW-limit series reconcilable
  without an invented apportionment; miso-77 §5.2) and it sits inside the
  standing congestion adjudications (`internal_congestion_split` MISO `G`,
  miso-78/79/80; `zonal_loss_surface` `R`, miso-76/80), which the charter lists
  DO-NOT-REDO.

## 6. The honest ceiling (charter item 3), restated after the result

**C3a-2025 is closed END TO END as a model-class limit** — RT-only half by the
miso-163 owner ruling, DA-foreseen half by
`FINDING-miso171-reserve-requirement-decomposition-2026-08-20.md` §6. Nothing in
this finding is claimed against that gate, and §5's price-reach number is
reported precisely so no successor can quote this lane as a scarcity fix. The
over-import remains a **real second-order structural defect** (rule 1
`[R-STRUCT]` / rule 14 `[R-ACCURATE]`) — phantom outside energy arriving exactly
when MISO was tight — worth repairing on its own merits by a mechanism that is
actually the phenomenon.

## 7. What this hands forward (named, NOT chartered)

1. **The seam envelope's hour-key rotation (§4)** — a one-line fix in an armed
   keeper mechanism, needing its own prereg + control/arm because it changes the
   keeper. Highest confidence, smallest scope, and it is a rule-14 accuracy
   repair independent of everything else here. Cross-ISO: check the PJM
   analogue in PJM's own lane.
2. **The coincident-peak seam-response object (§3)** — the actual cause. The
   admissibility question a charter must answer FIRST, not a session: an
   envelope conditioned on the **neighbour's own load** (a forward driver that
   regenerates and responds to changed conditions) is admissible in kind under
   rule 13, but correlates with MISO's scarcity by coincident summer peak, so
   the line between "conditioned on an exogenous forward driver" and "pinned to
   the residual" needs an owner ruling before anything is built.
3. **The M2M/CMP seam data, scoped to the seam class only.** miso-77 §2a
   established that hourly per-flowgate Firm Flow Entitlements and hourly M2M
   market flows/shadow prices are publicly fetchable with **EXT (seam) coverage
   90 / 90 / 88 %**. miso-77's blocking §5.2 concern — no PTDF for placing
   flowgates on the internal six-zone network — is **materially weaker at the
   seam**, where the MISO–PJM boundary is already a single model link. This is
   the concrete measurement that would say what bound in reality in the 72 hours
   this finding measured. Shadow prices stay ANSWER-class (validation only,
   rule 13).
4. **The South under-export (+0.63 / +0.35 / +1.19 GW)** — the second-largest
   component, untouched by anything in the import lane, and never separately
   chartered.

## 7b. Standing OWNER items, restated not decided (charter item 4)

Carried forward unchanged from miso-171/172/173. This session raises them; it
decides none of them.

1. **The C8 provenance-materiality floor.** The plant-990 `reliability_floor`
   conviction on **0.0000 TWh across ONE binding hour** was cleared at miso-173
   as a SIDE EFFECT of the lay-up mask removing that hour. The bundle no longer
   instantiates the defect; **the rubric hole is unrepaired** — C8's provenance
   leg still has no materiality floor, so a zero-energy, single-hour row can
   fail a keeper again the moment one reappears.
2. **The committed-vs-regenerated diagnostics exposure** (MISO **and** PJM,
   measured). Unchanged in kind, disclosed rather than created; every gate in
   this lane compares regen-control to regen-arm through the same path at the
   same HEAD.
3. **`RHO_CLIP` 0.5 vs the measured MISO rho 0.1764** (nyiso-144). Still the
   owner escalation; this finding adds no new claim on it. FINDING-miso170 §4
   measured that resolving it would not flip the scarce hours at family-grain
   headroom.
4. **MISO's determination posture.** C3a-2025 is the **sole** failing
   criterion, documented end to end as a model-class limit (miso-163 owner
   ruling + FINDING-miso171 §6), on a keeper with **zero D-4 conduct failures**
   and C6 attested, with C3c the single ledgered caveat. Whether `NOT-YET`
   should be adjudicated to a declaration is an **OWNER question**. It is riper
   after miso-174 than after miso-173: the last named OPEN cell in MISO's queue
   is now adjudicated, and the +1.33 GW over-import — the largest disclosed
   second-order defect — is measured, decomposed, attributed and bounded at
   1–2.5 % of the scarce-hour miss even under its inadmissible upper bound.

## 8. Governance

Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; the holdout
spend freeze is untouched; no marker re-key is owed. Rule 28(b): MISO's
`measured_interface_limits` cell stamped `R` with this evidence, in this
session; no other ISO's shard touched (rule 25). Rule 15 not engaged — no solve,
no run to register.

## 9. Reproduction

```
python3 scripts/probes/_miso174_seam_overimport_decomposition.py
python3 scripts/probes/_miso174_import_limit_precheck.py
python3 scripts/probes/_miso174_seam_price_evidence.py
```

Reads `results/calibration/miso173_layupmask/hourly/{system,class_hourly}_<y>.parquet`,
`miso169_gated_A/hourly/unit_hourly_<y>.parquet`,
`data/raw/eia-930-interchange/MISO interchange hourly.parquet`,
`data/raw/MISO_region.parquet`,
`data/raw/_validation-source/{actual_lmp_hourly_MISO,actual_lmp_hourly_PJM,actual_lmp_hourly_SPP,pjm_border_lmp_hourly_MISO}.parquet`.

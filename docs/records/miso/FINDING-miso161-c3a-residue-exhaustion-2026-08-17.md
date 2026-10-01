# FINDING — miso-161: the C3a-2025 residue re-measured on the miso-160 keeper — the availability channel is EXHAUSTED at admissible grain, the material remainder is the C3c-adjacent above-cost object (22–58 % basis-sensitive), and the next step is an OWNER charter/ledger decision, not a lever

**Session** miso-161 · **ISO** MISO · **Date** 2026-08-17 ·
**Keeper** `2026-08-16-miso-160-wefor-shape` (bundle `miso160_wefor_B`),
**UNCHANGED**.

**NO SOLVE. NO RUN REGISTERED. NO `ScenarioConfig` FIELD. NO CELL VERDICT
MINTED** (nothing armed or tested — the miso-142/153/155/156/157 no-LP
precedent). Rule 15 `[R-DASHBOARD]` is not engaged.

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only, read from committed
artifacts and the in-repo measured record; MISO holds neither `complete` nor
`final`; the holdout spend freeze is untouched.

**Instruments** (all pre-registered constructions re-run under their own T-1
repoint discipline; no new adjudicating statistic was designed this session):

* `scripts/probes/_miso161_c3a_decomposition.py` — the miso-156 three-channel
  decomposition (PREREG `162a51d`, blob `7f124d18`) repointed to
  `miso160_wefor_B`, V1 targets updated to the new keeper's registered C3a
  (+0.6165 / −4.7978 / −12.5201 %, the scorer's own statistic on the committed
  bundle + bench). Record: `_miso161_c3a_decomposition.json`.
* `scripts/probes/_miso161_summer_cushion.py` — the miso-153 phase-0 cushion
  instrument (PREREG `857a434`) repointed likewise. Record:
  `_miso161_summer_cushion.json`.
* `scripts/probes/_miso161_peakday_outage_shape.py` — the one NEW measurement:
  the MOM record's daily grain at the peak, on the armed miso-160 basis
  (identification-materiality only; no mechanism built). Record:
  `_miso161_peakday_outage_shape.json`.

---

## 1. Validity of the re-run

| gate | result |
|---|---|
| **V1** — reproduce the NEW keeper's registered C3a | **PASS 3/3 EXACT**: +0.616 / −4.798 / −12.520 % vs published +0.617 / −4.798 / −12.520 (deltas ≤ 0.001 pp vs ±0.5 pp bar) |
| **V4** — fleet identity | **PASS 3/3** (`n_gen` 2929/2923/2923; 6 carry zones) |
| **V2** — rebuilt floors vs miso-155's record | **MISS, EXPECTED AND DISCLOSED**: CT floor TWh −7.1 / −8.2 / −8.6 % (rows 164/151/153 vs 158/150/153). The target record was measured on the pre-miso-160 availability; the armed seasonal shape lowers summer availability and the netload-driven floors with it. Provably immaterial here: the **FLOORS_OFF twin moved 0.0000 $/MWh in all 27 decomposition cells in every year** — the same structural result miso-156 §3 proved (`HRmax` is headroom-masked over ~1,450 gas tranches, `G_mod` capacity-weighted; neither sees a floor) |
| T-6 (cushion probe) | 2025 "violations" are float-epsilon (max magnitude 3.6e−8 of capacity; the count leg trips on noise, the 2 % magnitude leg passes). 2023/2024 carry the same small CC reconcile-guard interactions the miso-153 record carried (max 5.2 % / 2.8 %) |

## 2. The decomposition on the NEW keeper, at full magnitude

`Δ₁ + Δ₂ + Δ₃ ≡ P_act − P_mod` (identity holds to ≤ 2.3e−13). Annual is the
adjudicating grain.

| year | grain | gap (was, miso-148) | **Δ₁ identity** | **Δ₂ cost level** | **Δ₃ above-cost** |
|---|---|---|---|---|---|
| 2023 | annual | **−0.190** (+0.668) | +0.332 | −0.533 | +0.011 |
| 2023 | Jun+Jul | +0.264 (+1.440) | −6.525 | +6.789 | +0.000 |
| 2023 | top-200 | +5.166 (+12.716) | −6.170 | +11.006 | +0.330 |
| 2024 | annual | +1.563 (+2.608) | +1.062 (67.9 %) | +0.218 (13.9 %) | +0.284 (18.1 %) |
| 2024 | Jun+Jul | +5.203 (+6.535) | +5.094 (97.9 %) | −0.771 | +0.880 (16.9 %) |
| 2024 | top-200 | +9.316 (+18.798) | +9.254 (99.3 %) | −2.087 | +2.149 (23.1 %) |
| 2025 | **annual** | **+5.687** (+7.082) | **+10.792 (189.8 %)** | **−6.378 (−112.1 %)** | **+1.272 (22.4 %)** |
| 2025 | Jun+Jul | +17.127 (+19.824) | +15.677 (91.5 %) | −2.876 | +4.326 (25.3 %) |
| 2025 | top-200 | +66.120 (+74.030) | +50.848 (76.9 %) | −2.875 | +18.146 (27.4 %) |

**S-CEIL sensitivity (the p99 capacity-weighted ceiling, 43.69 MMBtu/MWh,
pre-registered in the miso-156 construction because `HRmax`'s owner carries
0.0025 % of gas capacity at 113.88):**

| year | grain | Δ₁ | Δ₃ |
|---|---|---|---|
| 2025 | annual | +8.742 (153.7 %) | **+3.323 (58.4 %)** |
| 2025 | top-200 | +29.815 (45.1 %) | **+39.180 (59.3 %)** |
| 2024 | annual | +0.182 (11.7 %) | **+1.163 (74.4 %)** |
| 2024 | top-200 | +3.121 (33.5 %) | +8.282 (88.9 %) |

What moved, and what did not, vs miso-156 on the miso-148 keeper:

1. **The gap narrowed $7.08 → $5.69** (miso-159 + miso-160, both measured
   inputs). Δ₃ is **unchanged in dollars** (+1.272 primary / +3.323 p99 —
   by construction it does not depend on the model's price), so the
   **above-cost share of what remains RISES: 18.0–46.9 % → 22.4–58.4 %**
   basis-sensitive at the annual grain. On the physically-meaningful ceiling,
   **more than half of the remaining 2025 annual gap — and ~three-quarters of
   2024's — is priced above ANY gas unit's cost**.
2. **Δ₁ remains the largest gross channel in 2025 on both bases** (189.8 % /
   153.7 %), so the charter's STOP condition ("entirely C3c-adjacent
   above-cost") is **not literally met** — the lever branch had to be walked
   (§4), and it terminates.
3. **The fuel channel still points the wrong way** (miso-156 result 2,
   unchanged: model gas ABOVE hub-month spot by +0.348 / +0.092 / +0.892
   $/MMBtu and above delivered-to-electric-power by +1.543 / +1.005 / +1.010).
   The non-above-cost remainder is a **cancellation**: Δ₁+Δ₂ = +$4.41 primary
   / +$2.36 p99 (2025 annual). Any identity lever that ignores Δ₂'s sign
   overshoots.
4. **2023 now sits on the OTHER side of zero** (gap −0.190; C3a +0.62 %).
   The miso-156 against-interest bound has tightened: an annual-level lever
   pushes the passing year directly toward its +5 % S-2023 bar, and 2023's
   Jun+Jul Δ₁ is **−6.525** — even a summer-scoped identity lever moves
   2023's summer the wrong way.

## 3. The cushion on the NEW keeper (miso-153 D-1/D-3 re-measured)

| statistic (2025, top-200) | miso-148 keeper | miso-160 keeper |
|---|---|---|
| CT_PEAKER idle | 11.25 GW (55.8 % of avail) | **8.23 GW (45.2 %)** |
| CT_PEAKER within $20 of clearing | 6.31 GW | **4.19 GW** |
| all-class within $20 | 10.64 GW | **7.12 GW** |
| price-setter census | CT 60.7 % (unchanged class) | CT 60.7 % |

(2023: CT band 7.74 → 5.98 GW; 2024: 7.56 → 5.58 GW.) The two measured
availability repairs removed a third of the within-$20 band; the miss moved
0.6 pp. The marginal CLASS is right in ~61 % of top-200 zone-hours; the model
still stops less than half-way up the unit (implied heat rate ~12 vs the
market's ~29 at top-200 — which is above what any physical CT burns, i.e. the
upper tail of "identity" shades into the above-cost object as the ceiling
tightens).

## 4. The lever branch, walked to termination

**(a) The one un-adjudicated admissible availability quantity — the MOM
record's DAILY grain at the peak — is measured IMMATERIAL.** On the armed
basis (region MISO, Derated+Forced+Unplanned, the production loader), the
top-200-day measured offline MW vs the Jun–Sep mean the armed share already
spreads flat:

| year | Jun–Sep mean | top-200 mean | ratio | increment |
|---|---|---|---|---|
| 2023 | 24.03 GW | 22.98 GW | 0.9566 | **−1.04 GW** |
| 2024 | 23.41 GW | 24.38 GW | 1.0417 | +0.98 GW |
| 2025 | 31.10 GW | 31.79 GW | 1.0222 | **+0.69 GW** |

Direction: toward the gates in the failing years, toward zero in 2023 —
and **bounded by the miso-160 episode's own measured price response
(−3.67 GW Jun–Sep-wide → +0.60 pp) at ≲ 0.11 pp on C3a-2025**, an
overstatement since the increment lives in 200 hours, not 2,928. A −12.5 %
miss needs +2.5 pp to reach its gate. Scope, independent of materiality: §9's
fleet-grain amendment covers exactly ONE deliverable (the scalar), its own
text preserves the miso-85/87 closures, and a daily fleet-uniform shape would
need its own owner amendment. **Not chartered, and the measurement says it
would not be worth the ask.**

**(b) Everything else on the cushion/identity path is adjudicated, and the
verdicts stand (DO-NOT-REDO):** the uniform MOM envelope rebasis
`dam_availability_rebasis` **R** (miso-85/86 — grain, not accuracy; C3a-2025
overshot to +43.5 % under it); the cross-fuel attribution split
**refuted-at-charter** (miso-87 — no admissible key; reduces to a scalar knob);
`measured_offer_surface` **R** (miso-151 — identification refuted by its own
G-1/G-5); `gas_hub_basis_overlay` **R** (miso-156 — measured input points the
wrong way, rule-14 regression for MISO); `ramp_envelopes` **I** (miso-156 —
MISO under-ramps at every quantile); reserves **inert at the peak** (miso-153
D-4 — dual $0.00, zero binding, all families × years); demand shape verified
(miso-152/153); congestion split **G**; and the availability channel's
measured repairs are **K and armed** (measured CT heat rates miso-117b,
basis-aware summer derate miso-148, EIA-860 vintage miso-159, measured
seasonal WEFOR shape miso-160). The statistical-stack level for the CT
coverage hole (CAMPD zero windows) is now vintage-correct and season-correct;
no further measured record for it is on the table (GADS remains the
§8-candidate-1 UNRESOLVED data ask).

**(c) Rule 20 `[R-DOF]` closes the remainder to tuning**: the Δ₁+Δ₂
cancellation (+$2.4 to +$4.4) cannot be closed by any value identified
against the residual, and the C3c ledger's frontier designation governs the
above-cost half — "further work needs a NEW admissible measured
identification, its own charter. NEVER an offer adder tuned to the tail."

## 5. ESCALATION to the owner (the queue's single in-lane item, resolved by measurement)

The C3a-2025 residue after miso-160 decomposes into (i) an above-cost/tail
object worth **$1.27–3.32/MWh = 22.4–58.4 %** of the remaining $5.69 annual
gap (C3c-adjacent by construction: price above any gas unit's cost at the
ceiling), and (ii) a Δ₁/Δ₂ cancellation no admissible mechanism on record
reaches. **The in-lane lever queue is empty and this session does not invent
a lever.** The decision that unlocks anything further is the owner's, with
two shapes on the record:

1. **Charter the tail object** under the C3c ledger's frontier terms: a NEW
   admissible measured identification of MISO's administrative scarcity
   pricing (e.g. an intake of MISO's published RCPF/ORDC binding record —
   which hours, which reserve product, what adder MW/price — as a measured
   market-design input, rule 13's test applied). That is a data-ask + charter
   decision the ledger reserves to the owner; nothing here pre-judges its
   admissibility.
2. **Close the lane as a model-class limit** — the ERCOT C3a-2023 (Q-B)
   precedent (§5.4 queue item 11): accept NOT-YET on C3a-2025 as the
   deterministic-LP edge the C3c ledger already documents, and stop spending
   MISO sessions on it.

Until the owner rules, the MISO lane has **no chartered next solve**: any
further C3a-2025 work would either re-test an adjudicated cell without new
evidence (rule 28 DO-NOT-REDO) or tune the residual (rules 13/20/23).

---

**Artifacts.** Probes `scripts/probes/_miso161_c3a_decomposition.py`,
`_miso161_summer_cushion.py`, `_miso161_peakday_outage_shape.py` (all `ruff`
clean; the first two are T-1 repoints of pre-registered constructions, the
third is an identification-materiality measurement). Records
`results/calibration/_miso161_c3a_decomposition.json`,
`_miso161_summer_cushion.json`, `_miso161_peakday_outage_shape.json`. Keeper
`2026-08-16-miso-160-wefor-shape`, **unchanged**. Session precondition
delivered: PR #4044 (the miso-160 branch) merged to main at `bad0807` with a
two-file conflict resolution (the MISO shard's final `K` cell kept over the
stale in-flight `O`; `run_calibration.py`'s plant-exclusions declaration kept
once WITH its config wiring restored — main's twin-fix series had deleted
both wiring copies, leaving the kwarg a silent no-op).

# FINDING — ercot-162: the measured multi-tranche storage RT discharge-offer surface is REFUTED, on the SAME ground-(c) ERCOT-154 identified (now on the multi-tranche form it demanded) plus zero-spurious; the residual object is confirmed to be the AS/energy split of storage capability at scarcity, not the energy offer price

**Session ercot-162, 2026-08-04.** The ercot-161-chartered
`ercot_storage_rt_offer_surface` successor, built (Phase A/B) and A/B-tested
(Phase C) exactly per
`docs/PRECOMMIT-ercot162-storage-rt-offer-surface-2026-08-04.md`. Keeper
UNCHANGED (`2026-08-03-ercot158-pool-arm`). Verdict **R (rejected)** — multiple
pre-registered kills fire, matching **both** pre-declared refutation branches.
Single-delta A/B off the ercot158 keeper: control `ercot162_control_A` (fresh
same-HEAD replay, gap-hour mean $441.27 = the committed keeper to the cent),
arm `ercot162_stormarm_B` (`--set ercot_storage_rt_offer_surface=true`), both
`--year 2023 2024 2025`, invocations sequential (15 GB box). Scorers
`scripts/probes/_ercot162_storage_ab.py` →
`results/calibration/_ercot162_storage_ab.json` and the standing
`_ercot89_span_check.py` → `results/calibration/_ercot162_span_check.txt`.

## 1. The verdict, on the pre-registered gates

**Every pre-registered KILL that could fire, fired.** Scored Run A → Run B:

| gate (PRECOMMIT §4) | 2023 | 2024 | 2025 | verdict |
|---|---|---|---|---|
| **2025 EIA-930 NG:BAT volume guard** | — | — | 4,454 → **1,284 GWh** (−76.4% vs measured 5,444.8; drop 3,170 ≫ 272 threshold) | **KILL** |
| **Zero-spurious mid-band** | +3 | +7 | **+25** | **TRIPPED all 3 yrs** |
| **C3a level guard** (+1.0 pp grace) | −24.5→−23.4% HELD | +10.2→**+17.5%** (+7.3pp) | −0.7→**+9.4%** (+10.1pp) | **DEGRADED 2024/2025** |
| **NRMSE (C3b proxy)** (+0.005) | 2.866→2.835 HELD | 2.946→**3.683** | 0.955→**2.159** | **DEGRADED 2024/2025** |
| **New-tail-outside-actual** | 1 new, 0 outside | — | — | held |
| **Tail-count** | HELD | HELD | HELD | held |

And the **owner-priority object — the 100-hour gap set — barely moved**: control
mean **$441.27 → arm $457.32**, a **+$16.05 lift that closes only 1.6 %** of the
gap to the target λ **$1,470.16** (matched-hour missed-set mean $128.84 →
$147.86; 1 of 112 missed hours flipped ≥$300). The arm does **not** fix the
residual it was chartered against.

## 2. Both pre-declared refutation branches are realized

The PRECOMMIT §5 / FINDING-ercot161 §4 stated two ways the arm could fail. **Both
happened, and together they are decisive.**

**(a) "The crossing never reaches the tranches ⇒ INERT" — REALIZED at the gap
hours.** The +$16 gap-hour lift is immaterial because the model's crossing at
those hours does not run deep into the storage tranches: the thermal stack — the
ERCOT-88 fast-start CT pool plus the ~8 GW cheap CC offline block (ERCOT-152's
measured-no-op, upheld at ERCOT-158) — absorbs the withdrawn storage below the
tranche prices, so the marginal unit stays thermal. This is exactly the
ERCOT-161 insight, now measured: *"the discrimination between a $76 ordinary
hour and a $1,337 gap hour is NOT in the storage offer — it is in how deep the
system's own crossing ran into it."* The model's crossing does not run deep
enough (that IS the residual), so a high storage offer cannot form the price —
it can only withhold the fleet.

**(b) "Ordinary-hour lift ⇒ R on zero-spurious" — REALIZED in all three years,
catastrophically in 2025** (+25 spurious mid-band hours; C3a +10.1 pp; NRMSE
0.955 → 2.159). The withheld storage removes cheap supply and manufactures
scarcity where reality had none.

## 3. The structural finding — why the multi-tranche form ALSO fails ground (c)

The battery discharge **collapses ~74 % in EVERY year** under the arm (2023 829 →
216 GWh; 2024 2,143 → 538; 2025 4,454 → 1,284), against a measured 2025 EIA-930
`NG: BAT` of 5,444.8 GWh — so the arm drives an already-short measured quantity
(control −18 %) to **−76 %**. This is the ERCOT-154 ground-(c) failure — *"it
breaks a measured quantity that is already short"* — recurring on the **exact
multi-tranche form ERCOT-154 ground-(a) said was required.** ERCOT-154 refused
the single-price arm partly because *"the rungs a multi-tranche form needs are
unidentified"*; ercot-162 identified them (Phase A, reproducing the ercot-161
census to the cent), built the multi-tranche LP, and measured that the
multi-tranche form fails ground (c) too.

**The mechanism of the collapse (the disclosed grain risk, PRECOMMIT §3,
realized).** The a-priori right-edge construction prices the top tranche at
Q(0.99) = the $5,000 HCAP over a **0.70 width** — 70 % of the fleet offered at
the cap. This is *faithful for 2023* (the small ~1 GW fleet genuinely held its
median at the cap) but the LP still cannot dispatch that 70 % because the
model's scarcity hours rarely reach $5,000; and it is *aggressive for 2024/2025*
(the 6×-larger fleet's measured median collapsed to $91–230 — the disclosed
year-pair regime shift — yet the top 1 % keeps a $5,000 tail, so Q(0.99) is
still $5,000). Year-scoping gave each year its own ladder, but every year's
right-edge top tranche is the cap, so every year withholds ~70 % of the fleet.

**The deeper reason a measured SCED offer cannot be transplanted as a marginal
cost.** A battery's submitted $5,000 offer is an **equilibrium object**: the
operator offers at the cap *knowing* it will clear in the market's few real
scarcity hours and managing its limited stored energy across the day toward
them. The real market clears that offer in those hours and the fleet delivers
~5,445 GWh/yr. Transplanted into the LP as a discharge marginal cost, the same
offer just prices the fleet out — because the LP has no mechanism to reproduce
the scarcity hours at $5,000 (that under-scarcity IS the residual), so the
$5,000 tranche rarely clears and the battery sits idle. The offer surface
**presumes the scarcity the model lacks**; it cannot create it.

## 4. Where the lane goes (the residual object, re-confirmed)

The residual is a **quantity / scarcity-depth** object, not a storage-offer-price
object — exactly the FINDING-ercot161 §4 refutation-branch destination: *"the
object moves to the AS/energy split of storage capability at scarcity."* The
model's storage discharges 653 MW mean at the gap hours (comparable to the real
fleet's online energy capability), so the defect is not that the model lacks
storage energy — it is that the model's price does not climb into scarcity at
those hours because its **crossing depth** is short (the CC offline block's
phantom cheap depth, the ERCOT-158-attributed commitment-state gap; the
un-repriced cheap CC ~8 GW). Pricing storage higher cannot fix a crossing-depth
defect. The successor is the commitment-state / scarcity-depth question, and on
the storage side specifically the **AS-vs-energy capability split at scarcity**
(how much of the fleet's telemetered capability is truly available to energy at
the gap hours after its real AS commitments) — a quantity measurement, not an
offer re-price.

## 5. Governance

R verdict; keeper UNCHANGED. Both runs registered on the backcast dashboard
(rule 15) with attestations — the control is the A/B base, the arm the rejected
probe. The `ercot_storage_rt_offer_surface` matrix cell is stamped ERCOT **O → R**
with this finding + both bundles as evidence (rule 28(b)). The mechanism stays
merged **default-off** (rule 26 [R-DELETE] does not apply — it is a built,
reachable, default-off measured mechanism, not a fitted knob; its refutation is
recorded, its code is not zeroed). Logged as ercot-162 in
`docs/calibration-log/ercot.md`. Holdouts untouched: 2023–2025 only (rule 22);
ERCOT-scoped (rule 25). Scope fence honoured (PRECOMMIT §0): no offer-LEVEL
re-derive, no envelope/cap family, no topology, no `ordc_only_scarcity`. The
ERCOT-154 DO-NOT-REDO items were honoured throughout — not single-price, not
gas-multiple, and **no rung was selected on model absorption** (K, the quantile
set, and the widths were fixed a priori in Phase A; the refutation was NOT
answered by re-tuning them, which would be the ground-(a) illegitimate move).

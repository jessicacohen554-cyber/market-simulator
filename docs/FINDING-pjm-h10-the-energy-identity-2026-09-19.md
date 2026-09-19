# FINDING — PJM's energy identity: the 923→930→model bridge, and where the real defect is (pjm-h10, 2026-09-19)

**Session:** pjm-h10 · **Branch:** `claude/pjm-energy-identity-s4l8ow` · **Base:** `origin/main` @ `4583e70b864a7d5c99a206b06eddf3c36af495bf`
**Keeper UNCHANGED** (`2026-09-11-pjm-d4-4-gasoutage`) · **no run registered · no mechanism armed · no matrix cell moved · ZERO LP minutes in this session** (rule 32 `[R-SHARD]` (a); the two control replays run in shards).
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-pjm-h10-2026-09-19.md` (the G-DRIFT audit and the ex-ante prediction, written before either shard reported).

---

## 0. Headline

**The premise the lane was handed does not survive measurement, and the real defect is not the one named.**

1. **There is no 60–75 TWh EIA-923↔EIA-930 gap.** The bridge closes to **−6.4 to +9.3 TWh (−0.76 % to +1.10 %)** in every complete year. The "739 TWh" figure is EIA-923's PJM footprint **with CHP and with wind+solar removed**; those two exclusions are 66.9 TWh in 2020 and 87.1 TWh in 2024, and they *are* the apparent gap. Nothing is missing.
2. **The 9–10 TWh interchange shortfall is real, and it is not a cap and not the neighbour price.** PJM's own settlement tie-line file agrees with EIA-930 `Total interchange` to **≤0.19 TWh** in 2020–2024. The model is handed that number and delivers **2.8–13.5 TWh less of it**. The measured export envelope is **never binding** — zero hours at ≥95 % of the system cap in any year, median export at 22–36 % of cap.
3. **A NEW defect, previously unnamed: PJM's keeper 2020 does not run the keeper's own seam representation.** `PJM_SEAM_LADDER_BY_YEAR` covers 2019, 2021, 2022, 2023, 2024, 2025 — **2020 is absent**, and so is `firm_export_floor_by_year`, so 2020 falls through to the *forecast* gas-elastic track. Both source inputs for 2020 are on disk. This is the identical defect the lane already fixed for 2022 at pjm-160, in the same channel, left behind.
4. **EIA-930's own accounting identity does not close for PJM in 2019, 2020 and 2025** (`D + TI − NG` = **+9.85 / +8.56 / −14.76 TWh**; ≤0.19 TWh in 2021–2024). Most of the apparent 2020 "generation overshoot" is this, not the model.
5. **Two corrections to the state I was given** (§6): the model's internal energy sink is **not** storage round-trip loss — storage is only 28–41 % of it, the rest is the measured zonal loss surface; and the PJM touchpoint's **C2 is a PASS**, not a FAIL.
5b. **Q3 needed no new work.** `RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md` §4 had already measured the virtual net on all six years and established that the layer's ≈0 anchor is a property of 2023–2025 rather than of its construction. §3 records that finding and adds only corroboration on the current keeper; nothing there is claimed as new.
6. **The 2020 demand repair is incomplete.** A **192,229 MW** hour survives the spike screen — 20–30 % above every clean year's maximum in the very file the model reads, at 1 p.m. on a day whose own 5 p.m. reads lower, and internally inconsistent by −56,665 MW against its own row.

---

## 1. Q1 — the EIA-923 → EIA-930 → model bridge

Sources: `data/raw/_processed-legacy/eia923_monthly_generation.parquet` (Page-1 net generation, with `ba_code`); `data/raw/eia-930-hourly/PJM hourly.parquet`; the committed keeper sidecars `results/calibration/pjm_d4_4_A/hourly/` (2023–2025) and `pjm_d4_4_TP/hourly/` (2020–2022).

### 1.1 The three plant sets, which are nearly the same set

Q1 asks which EIA-923 plants are inside the PJM **BA** footprint versus inside the model's **8 zones**. Measured:

| year | A: `ba_code == 'PJM'` | B: model's 8 zones | A ∩ B | A − B | B − A | #A | #B |
|---|---|---|---|---|---|---|---|
| 2019 | 808.73 | 803.48 | 791.62 | 17.11 | 11.86 | 1,313 | 1,289 |
| 2020 | 796.26 | 795.29 | 786.22 | 10.05 | 9.08 | 1,441 | 1,379 |
| 2021 | 826.02 | 817.02 | 817.02 | 9.00 | 0.00 | 1,532 | 1,484 |
| 2022 | 832.54 | 827.61 | 827.61 | 4.93 | 0.00 | 1,596 | 1,561 |
| **2023** | **822.99** | **822.99** | **822.99** | **0.00** | **0.00** | 1,685 | 1,676 |
| 2024 | 851.81 | 849.36 | 849.36 | 2.45 | 0.00 | 1,808 | 1,671 |
| 2025 | 817.53 | 808.72 | 808.72 | 8.80 | 0.00 | **453** | 406 |

TWh. The two sets are **identical in 2023** and differ by ≤10 TWh in 2020. Both differences are explained, not residual:

* **A − B** is plants EIA-923 attributes to PJM that the model's zone lookup cannot place, and they are **retirees**: the current eGRID-2023/EIA-860 vintage the lookup is built from no longer carries them. 2020's 10.05 TWh is led by **W H Zimmer 5.57**, Conesville 1.07, Cove Point LNG 0.62, Cheswick 0.55. By 2023 the set is 9 plants at 0.00 TWh.
* **B − A** in 2020 is **9.03 TWh of OVEC** — the Ohio Valley Electric Corporation, its own EIA balancing authority, physically inside PJM's footprint and a PJM member. The model is right to claim it; EIA-923 books it to `OVEC`. Plus 0.05 TWh of MISO-coded plant.

Therefore the footprint is best taken as **A ∪ B**, and the attribution question is closed: it is worth at most 10 TWh in the oldest year and nothing in 2023.

### 1.2 Where "739" comes from

| component | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| (a) EIA-923 excl CHP **and** excl wind+solar ← **the "739"** | **738.42** | 753.99 | 754.03 | 746.28 | 764.74 | 746.58 |
| (b) + CHP (published `chp = Y` rows) | 34.65 | 34.74 | 34.88 | 33.98 | 35.77 | 28.34 |
| (c) + wind + solar | 32.28 | 37.30 | 43.66 | 42.75 | 51.33 | 42.63 |
| (d) **= EIA-923 PJM footprint (A ∪ B)** | 805.34 | 826.02 | 832.54 | 822.99 | 851.81 | 817.53 |
| (e) EIA-930 PJM `Net generation` (artifact-screened) | 801.06 | 833.94 | 841.84 | 824.82 | 845.38 | 875.92 |
| (f) **UNEXPLAINED (e) − (d)** | **−4.28** | **+7.91** | **+9.29** | **+1.83** | **−6.43** | +58.39 |
| (f) as % of (e) | −0.53 % | +0.95 % | +1.10 % | +0.22 % | −0.76 % | +6.67 % |

TWh. **2020's 738.42 reproduces the quoted 739 to 0.6 TWh.** The construction is EIA-923's PJM footprint minus cogeneration minus variable renewables — two classes the model dispatches and EIA-930's `Net generation` counts. Their sum is 66.93 TWh in 2020 and 87.10 TWh in 2024, which is the whole of the claimed "60–75 TWh".

The premise's **sign** is also wrong, as the charter suspected: PJM is a net exporter, so the identity is *generation − net export ≈ demand*, never *generation + imports*.

**2025's +58.39 TWh is a vintage artifact, not a gap.** EIA-923 carries **453 reporting plants** for 2025 against 1,685–1,808 in complete years. 2025 must not be used on the 923 basis for anything.

### 1.3 What remains unexplained, as a number

**−6.43 to +9.29 TWh, i.e. −0.76 % to +1.10 % of EIA-930 `Net generation`, in the five complete years.** Named candidates for that residual, none individually resolvable from these two sources:

* sub-1 MW and non-reporting units — EIA-930 is the BA's telemetered total, EIA-923 Page-1 covers ≥1 MW respondents;
* hourly telemetry versus revenue-quality monthly meters (EIA-930 is not settlement-grade, and its per-fuel columns are demonstrably worse than its total — see §4.1);
* the residual OVEC/retiree attribution of §1.1 in the older years;
* EIA-923 vintage revision — the 2024 file is still being revised.

This is stated as a bound rather than decomposed further: the two sources do not carry the plant-level reconciliation that would split it, and **±1 % is at or below the noise of the comparison**, so decomposing it further would be over-reading the data.

---

## 2. Q2 — the under-export IS the live defect, and here is which object causes it

### 2.1 The two measured records agree; the model does not match either

| TWh | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| PJM settlement tie-line file (the model's own boundary) | 41.626 | 37.815 | 31.775 | 39.974 | 32.825 | 32.925 |
| EIA-930 `Total interchange` | 41.656 | 37.943 | 31.692 | 39.983 | 32.641 | 17.968 |
| tie − 930 | −0.031 | −0.129 | +0.082 | −0.009 | +0.183 | **+14.957** |
| **model net export** | **38.810** | **24.273** | **22.667** | **30.870** | **22.277** | **24.379** |
| **model − tie file** | **−2.816** | **−13.541** | **−9.108** | **−9.104** | **−10.548** | **−8.546** |

PJM's settlement file and EIA-930 agree to **≤0.19 TWh in 2020–2024** — so the "which source" question is settled and neither is the model's excuse. The **2025** divergence of +14.96 TWh is EIA-930's, and it is the same object as EIA-930's own unclosed 2025 identity (−14.76 TWh, §5): **EIA-930's 2025 `Total interchange` is the defective series; PJM's tie file is right.** That single fact disposes of the charter's "2025 over-exports by +6.41 TWh": measured against the correct boundary, 2025 **under**-exports by 8.55 TWh like every other year, and the sign flip was an artifact.

### 2.2 Rule 19 `[R-ONE-MECH]` enumeration — what already governs PJM exports

Seven objects, before anything new is proposed:

1. **`pjm_seam_measured_ladder`** (armed) — the per-seam 8-rung measured export price ladder, `PJM_SEAM_LADDER_BY_YEAR`. Covers 2019, 2021–2025. **Not 2020.**
2. **`firm_export_floor_by_year`** — the firm scheduled-export floor, forcing the cheapest export tranches on. Entries exist only for 2023/2024/2025, and the ladder **displaces** it on exactly the years it covers (alternatives, never stacked). **It is therefore inert in every keeper year**, which is worth stating plainly: the mechanism that exists precisely to hold the firm export base on is switched off wherever it has data.
3. **`pjm_seam_flow_limit`** (armed) — the per-**neighbour** measured deliverability envelope at `PJM_SEAM_FLOW_PERCENTILE = 90.0`, from PJM's own tie file.
4. **`pjm_external_net_position_cut`** (armed) — the joint star-node net-position cut.
5. **`pjm_zonal_loss_surface`** (armed) — one-way loss pairs on the 11 internal links, which reduce what reaches a border zone.
6. The internal 8-zone / 11-link TTC network itself.
7. The **forecast gas-elastic reference-price formula** — the fall-through track. **This is what 2020 runs.**

### 2.3 The envelope cap is NOT the binding object

Model system net export against the measured per-border export envelope, summed over zones:

| year | model TWh | cap-sum TWh | hrs export > 0 | hrs ≥ 99 % of cap | hrs ≥ 95 % of cap | median export/cap |
|---|---|---|---|---|---|---|
| 2020 | 38.810 | 93.579 | 8,760 | **0** | **0** | 0.364 |
| 2021 | 24.273 | 94.512 | 8,718 | **0** | **0** | 0.263 |
| 2022 | 22.667 | 89.916 | 8,676 | **0** | **0** | 0.246 |
| 2023 | 30.870 | 100.903 | 8,752 | **0** | **0** | 0.290 |
| 2024 | 22.277 | 94.410 | 8,656 | **0** | **0** | 0.220 |
| 2025 | 24.379 | 95.968 | 8,703 | **0** | **0** | 0.235 |

**Zero hours at the cap, in any year.** And the shortfall is not a truncated tail — the *whole* distribution is shifted down. 2023 hourly export, measured vs model: p10 1,585 → 1,406 · p25 2,886 → 2,305 · **p50 4,477 → 3,393** · p75 6,216 → 4,497 · p90 7,662 → 5,760 · p95 8,542 → 6,489 · p99 10,145 → 7,629 MW. The model exports in **more** hours (8,752 vs 8,597) and **less** in each. A binding limit truncates the top; a price effect scales the body. This is the latter.

### 2.4 The price effect is real but only worth 2.6–7.8 TWh

Evaluating the ladder at the model's own border-zone price versus at the measured DA price (gross export volume the ladder's rungs admit, TWh):

| year | @ model price | @ measured DA | gap | realized net |
|---|---|---|---|---|
| 2021 | 39.561 | 47.402 | **7.841** | 24.273 |
| 2022 | 40.753 | 44.666 | **3.913** | 22.667 |
| 2023 | 51.315 | 54.622 | **3.307** | 30.870 |
| 2024 | 45.195 | 48.454 | **3.260** | 22.277 |
| 2025 | 45.484 | 48.067 | **2.583** | 24.379 |

The direction is consistent with pjm-h3b's finding that PJM's model body is **+1.5 % over** on price: an over-priced body means fewer deep export rungs clear, since each rung clears only when the internal price falls below it. But the magnitude is 2.6–7.8 TWh, **not** the 9–13.5 TWh to be explained.

### 2.5 What is left, and where it has to be measured

Both legs are material, and the split is **not** uniform. Taking `min(per-seam p90 cap, ladder at the
model's own price)` as the model's admissible **gross** export and PJM's tie file as measured gross:

| TWh | measured gross export | min(cap, ladder) | **gross-export short** | **net short** | **implied import-side excess** |
|---|---|---|---|---|---|
| 2021 | 47.440 | 37.982 | **9.458** | 13.542 | 4.083 |
| 2022 | 44.756 | 38.478 | **6.278** | 9.108 | 2.830 |
| 2023 | 54.653 | 49.947 | 4.706 | 9.104 | **4.398** |
| 2024 | 48.446 | 44.012 | 4.434 | 10.548 | **6.114** |
| 2025 | 48.165 | 44.277 | 3.888 | 8.546 | **4.658** |

(2020 is omitted: it runs no ladder, so `min(cap, ladder)` is not the comparable object there.)

So the defect is **two legs of comparable size**, not one: a gross-export shortfall of 3.9–9.5 TWh and
an implied import-side excess of 2.8–6.1 TWh. Their balance **shifts across the span** — export-dominated
in 2021/2022 (9.5 and 6.3 against 4.1 and 2.8), import-dominated by 2024 (4.4 against 6.1). Anyone
chartering a lever here must pick the leg, and the leg depends on the year.

The import leg is the failure mode `interchange/spec.py`'s own comment warns about in as many words —
*"phantom imports that displace CC_REGULAR dispatch, the C1 FAIL"* — and it is consistent with §4's
finding that CC_REGULAR is **+22 to +26 TWh over** in exactly the pre-2023 years.

**Read the import column as an INFERENCE, not a measurement.** It is a residual of two quantities
measured on different objects (a per-seam gross ceiling from the envelope and ladder; a system net
position from the `import` pseudo-unit), so it inherits both their errors, and the ladder leg in
particular is a free-flow ceiling that ignores the internal network and the net-position cut.

**It cannot be confirmed from committed artifacts**, because the committed slim bundle carries only the NET `import` pseudo-unit class, and the per-link/per-seam gross flows live in `hourly/network_<year>.parquet`, which the keeper bundle does **not** commit. This session's two control replays produce it. **The gross export / gross import split is the single measurement that closes Q2, and it is one parquet away — no re-solve beyond the replays already running.**

### 2.6 NEW FINDING — the 2020 seam gap

`PJM_SEAM_LADDER_BY_YEAR` covers **2019, 2021, 2022, 2023, 2024, 2025**. **2020 is missing.** `firm_export_floor_by_year` covers only 2023–2025. So PJM's keeper **2020 runs neither measured seam mechanism** and falls through to the forecast gas-elastic reference-price track.

The registry's own comment, written at pjm-160 about 2022, states the consequence exactly:

> *"outside the years listed here PJM's seam runs the FORECAST track … so the already-spent 2022 touchpoint did NOT run the keeper's own seam representation, in the channel carrying PJM's largest single-signed volume error."*

pjm-160 extended the ladder to 2019 / 2021 / 2022 on 2026-08-07 and **skipped 2020** — which was
correct at the time and has since gone stale. pjm-173 (2026-09-08) recorded the invariant explicitly:
*"PJM_SEAM_LADDER_BY_YEAR covers {2019, 2021, 2022, 2023, 2024, 2025} = EVERY year PJM solves, so
F-A is inert in all of them."* **That was true when written** — the then-keeper
`pjm_debugb_inputclock_A` (pjm-162) solved 2023–2025 and the touchpoint span reached back only to
2021, so 2020 was not a PJM year. **2020 entered PJM's solved span with the `pjm_d4_4_TP`
touchpoint, and nothing re-checked the invariant.** So this is not a second oversight but a
*stale invariant*: a covering claim that was verified once and silently falsified by a later span
extension. It is also the reason a rule-19 inertness argument on this mechanism must be re-checked
whenever an ISO's year set grows — which is exactly what rule 35 `[R-PROMOTE]` (b)/(c) now require
of the year set itself. There is no data reason: `derive_pjm_seam_ladders.py` runs the frozen formula over `PJM_<year>_import_export_act_sch_interchange.csv` and `actual_lmp_hourly_PJM.parquet` `da`, and **both cover 2020** (verified on disk: `PJM_2020_import_export_act_sch_interchange.csv` present; the LMP parquet carries 2018–2025).

Filling it is a **rule 23 `[R-FROZEN-DERIVE]` re-derivation** — the source data already extends, the formula is frozen, zero parameters are introduced, and the 2019/2021–2025 entries must come back byte-identical (the same verification pjm-160 performed).

**Stated against interest, because rule 1 `[R-STRUCT]` requires it: this will probably make 2020 WORSE.** 2020 is currently the year with the **smallest** export shortfall (−2.82 TWh, against −8.5 to −13.5 elsewhere) precisely *because* the unmechanised forecast track happens to export more. The case for filling the gap is representation consistency (rules 14 / 23) — a keeper year must run the keeper's own mechanism — and it is **not** a residual argument. If the residual worsens, that is the discovered bug rule 14 `[R-ACCURATE]` describes, and the estimate was silently compensating.

**Not armed, not tested, not scored this session.** Registered here as a chartered candidate for the next PJM lane, with its gate to be declared ex ante.

### 2.7 Routed, not guessed

Also measured and set aside rather than absorbed: the per-seam envelope cap binds in 705–2,050 hours of 8,760 on MISO and NYISO (the two seams carrying ~96 % of the volume) and in ~0 hours on Carolinas/TVA/LGEE. So the cap is a *secondary* object even where it does bind, and the p90 percentile choice is not this defect's root cause.

---

## 3. Q3 — the virtual-bid net

`VIRTUAL_INC` / `VIRTUAL_DEC` are in the energy balance. Measured (TWh):

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| VIRTUAL_INC (net supply, + generation) | +9.900 | +5.203 | +8.919 | +15.432 | +18.305 | +16.812 |
| VIRTUAL_DEC (net demand, − generation) | −11.783 | −15.174 | −21.057 | −13.445 | −15.889 | −19.226 |
| **NET** | **−1.883** | **−9.971** | **−12.138** | **+1.987** | **+2.416** | **−2.415** |
| gross volume | 21.682 | 20.377 | 29.976 | 28.877 | 34.193 | 36.038 |

**Q3 IS ALREADY ADJUDICATED, and not by me.** `docs/RESULT-pjm-d4-3-da-virtual-net-2026-09-10.md` §4
measured exactly this question on all six years and reached a stronger result than the charter's
framing assumes. Recording it here rather than re-deriving it (rule 28 `[R-MECH-MATRIX]` (a),
DO-NOT-REDO), because the PJM matrix cell `da_virtual_bids` already carries it:

* The pair is **not** volume-balanced by construction and is not meant to be. `data/virtual_bids.py`
  renders PJM's measured hourly submitted INC/DEC curves as **one per-hour net curve**
  `net(λ) = Σ_{DEC ≥ λ} MW − Σ_{INC ≤ λ} MW`, monotone non-increasing with a crossing price `λ0`.
  Below `λ0` the layer holds net virtual **demand**; above it, net virtual **supply**. Clearing is
  endogenous on both sides. So the annual net is the integral of a measured curve evaluated at the
  model's own hourly prices, and its sign is a **price** outcome.
* pjm-d4-3's decisive finding: the module's ≈0 admissibility anchor **is a property of 2023–2025 and
  not of the construction.** Recomputed from the module's own loader against measured PJM RTO hourly
  DA LMP, `net @ actual DA` is **+16.537 / +16.812 / +12.248 TWh** of net virtual *demand* in
  2020/2021/2022 against −0.755 / −1.620 / +0.204 in 2023/2024/2025. **In the holdout years there is
  no price at which this curve nets to ~0.**
* The cause is a real change in PJM's book, not in the model: gross INC nearly doubles
  51.4 → 103.5 TWh 2021 → 2025 while gross DEC grows 1.5×, so the **DEC/INC gross ratio falls
  1.69 → 1.28**. The peak side is not the defect (net virtual demand over the model's own top-100
  load hours is the designed ~7–11 GW in *every* year); the **off-peak supply side is thinner** in
  the holdout span, so the annual net fails to cancel there.
* Disposition: the root cause is the architecture question (the LP carries ONE price series, gated as
  RT, while the curve needs a DA price) **already escalated to the owner** at pjm-159, inside PJM's
  owner-declared-closed price-formation frontier (pjm-142). Not a lever. pjm-158 already solved the
  single-delta `pjm_da_virtual_bids=false` arm across 2023–2025 with both arms registered.

**All this session adds is corroboration on the CURRENT keeper**, which pjm-d4-3 could not use (it
measured on the superseded `pjm-d4-2` pair). Realized net position on `pjm_d4_4_A` / `pjm_d4_4_TP`,
sign-converted to pjm-d4-3's convention (positive = net phantom **demand**):

| TWh | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| VIRTUAL_INC (net supply, + generation) | +9.900 | +5.203 | +8.919 | +15.432 | +18.305 | +16.812 |
| VIRTUAL_DEC (net demand, − generation) | −11.783 | −15.174 | −21.057 | −13.445 | −15.889 | −19.226 |
| net phantom demand (this keeper) | **+1.883** | **+9.971** | **+12.138** | −1.987 | −2.416 | **+2.415** |
| net phantom demand (pjm-d4-3, `pjm-d4-2`) | +2.414 | +10.525 | +13.013 | −1.338 | −1.713 | +2.870 |
| gross volume \|INC\|+\|DEC\| | 21.682 | 20.377 | 29.976 | 28.877 | 34.193 | 36.038 |

Same sign in all six years, magnitudes within 0.5–0.9 TWh — the differences are the keeper change,
so **the d4-4 promotion did not move this object** and pjm-d4-3's numbers remain the ones to cite.

**What is genuinely new here is only the cross-reference**, and it is worth one line: the years where
the net phantom demand is largest (2021 +9.97, 2022 +12.14) are exactly the years CC_REGULAR is most
over (§4.2: +26.2, +22.5 TWh) *and* the years the under-export is worst (§2.1: −13.5, −9.1). pjm-d4-3
already priced that channel at ~0.7–1.0 TWh of CC per TWh of net virtual, which would put ~7–12 TWh
of the pre-2023 CC over-run on this layer. **I am asserting no new attribution** — the bound is
pjm-d4-3's and it is already recorded against the matrix cell.

---

## 4. Q4 — per-class attribution

### 4.1 First, the basis, because the one the charter names is unusable for PJM

Attributing against EIA-930's `NG: <fuel>` columns, as asked, gives **`NG: SUN` = 0.2–1.0 TWh in every year** — against EIA-923's 6.0/9.8/12.2/14.3/20.6 TWh of real PJM solar. **EIA-930's PJM solar column is effectively unreported.** The eight `NG:` columns also sum to 776.5 TWh in 2020 against the same file's own `Net generation` of 801.1, so the per-fuel product is materially less complete than the BA total. A "+15.3 / +23.6 TWh solar overshoot" on that basis is a benchmark artifact that reverses sign on the correct benchmark (the model is **under** on solar against EIA-923).

**Re-measured as the charter instructed**, the registered C1 payload is on the EIA-923 basis, and `CC_REGULAR` 2022 reads **+21.1 TWh**, not the +22.56 the charter quotes. On the A ∪ B footprint basis it is **+22.5**. The predicted move to +12.81 from the `gov-hydro-seam-1` PS→OTHER repair has **not** happened in the registered payload — that repair is one of the LIVE hunks the PRECOMMIT identifies, so the value the shard replays produce is the test of it.

### 4.2 The attribution, model versus EIA-923 PJM footprint, same taxonomy

TWh, `classify_plant` applied to the A ∪ B footprint. **2025 is on a 453-plant partial vintage and its diffs are meaningless — excluded from every conclusion.**

| class | 2020 | 2021 | 2022 | 2023 | 2024 |
|---|---|---|---|---|---|
| CC_REGULAR | +7.5 | **+26.2** | **+22.5** | +2.9 | +0.7 |
| COAL_BIT | **+16.9** | −6.1 | +7.6 | +4.8 | +3.9 |
| COAL_PRB | −2.7 | −3.3 | −5.2 | −3.8 | −6.1 |
| COAL_WC | −1.0 | −0.9 | −0.5 | −1.1 | −0.9 |
| CT_PEAKER | +0.8 | −3.8 | −1.1 | −1.1 | +1.8 |
| CT_CHP | −2.6 | −2.2 | −2.9 | −2.6 | −2.2 |
| ST_CHP | −2.4 | −2.4 | −2.1 | −2.3 | −2.4 |
| ST_GAS | +1.6 | +3.1 | +2.9 | +2.4 | −0.9 |
| OTHER | +1.8 | +1.9 | +2.4 | +2.5 | +2.7 |
| **oil** | **−0.7** | **−1.0** | **−1.9** | **−0.6** | **−0.9** |
| solar | −2.9 | −3.9 | −5.1 | −5.3 | −4.7 |
| wind | −3.8 | +0.4 | +0.8 | +1.2 | +0.2 |
| hydro | +0.1 | +0.1 | +0.1 | −0.1 | −0.0 |
| nuclear | −3.6 | +0.5 | +1.6 | −0.6 | −1.8 |
| biomass | −0.5 | −0.3 | −0.1 | +0.0 | −0.0 |
| **FOSSIL + oil** | **+15.6** | **+9.1** | **+17.1** | **−3.4** | **−11.1** |
| **NON-FOSSIL** | **−3.4** | **+3.7** | **+4.8** | **+3.0** | **+2.2** |
| **ALL** | **+12.2** | **+12.8** | **+22.0** | **−0.4** | **−8.9** |

**The charter's question — "those two do not have the same sign structure, so something else is UNDER" — is answered.** What is systematically under, every single year:

* **CHP: `CT_CHP` −2.2 to −2.9 and `ST_CHP` −2.1 to −2.4, together −4.4 to −5.0 TWh/yr.** Consistent in sign and magnitude in all five years — the clearest systematic miss in the table.
* **`oil` = 0.000 TWh in EVERY year**, against 0.6–2.0 TWh measured. A class that never starts at all. Small, but structurally a hole rather than a calibration error.
* **solar −2.9 to −5.3 TWh/yr**, growing with the fleet.
* **`COAL_PRB` −2.7 to −6.1 every year, while `COAL_BIT` is over in four of five.** That is a **within-coal merit-order misallocation**, not a coal-level problem, and it is invisible to C2, which scores the coal *family*.

And the over-run is **pre-2023 only**: CC_REGULAR is +26.2 / +22.5 in 2021/2022 and +2.9 / +0.7 in 2023/2024. Combined with §2's under-export being worst in exactly 2021 (−13.5) and §3's virtual net being most negative in exactly 2021/2022 (−10.0, −12.1), the three line up on the same years. **The pre-2023 CC over-run, the under-export and the virtual net are candidates to be one defect seen three ways** — and §2.5 names the one artifact that would test it.

### 4.3 A caveat on the PS row

`__PS_discharge` reads +5.0–5.7 TWh against an EIA-923 basis of 0.0, because EIA-923 books pumped storage **net** and therefore **negative** (PS alone: −1.78 TWh in 2020, −2.52 in 2023), and with the `gov-hydro-seam-1` repair those negative rows now classify to `OTHER`. So the PS comparison is not like-for-like on either side, and part of `OTHER`'s consistent +1.8 to +2.7 is this. **The pumped-storage accounting seam is still not clean on the benchmark side**; the repair fixed the classifier, not the comparison.

---

## 5. Q5 — the 2021 repair is sound; the 2020 repair is NOT

### 5.1 2021 verified

Raw EIA-930 PJM 2021 sums to **4,902.23 TWh** of Demand with a worst hour of **2,147,480,064 MW** — an int32 overflow, not a meter reading. `_load_pjm_hourly_demand` → `_screen_demand_spikes` (bar: 2.5× the annual median) flags **3 hours** and interpolates them, giving **796.17 TWh** and a peak of 149,590 MW. Verified by running the loader, not assumed. The same screen repairs the `Net generation` column (raw 4,939.01 → 833.94 TWh). **The repair works and the raw 2021 number must never be quoted.**

### 5.2 But 2020 has two artifact hours that SURVIVE the screen

The screen's bar is 2.5 × the annual median, which for 2020 is 212,426 MW. In every year PJM's true peak sits at **1.62–1.75×** the median. Two 2020 hours sit far above that regime and below the bar:

| hour | local | Demand MW | ×median | `Net generation` MW | `Total interchange` | row residual `D+TI−NG` |
|---|---|---|---|---|---|---|
| 5003 | 2020-07-28 **H13** | **192,229** | 2.26 | 140,956 | +5,392 | **−56,665** |
| 5031 | 2020-07-29 H17 | **176,085** | 2.07 | 147,277 | +5,919 | **−34,727** |

Three independent reasons each is an artifact, all from the model's own input file:

* **(i) Level.** In the extract's clean years the annual maximum is 147,605–160,560 MW and the
  p99.9 hour is 144,591–156,635 MW. **192,229 MW is 20–30 % above every clean year's maximum in
  the very file the model reads.** (For context, outside the repo PJM's all-time peak is commonly
  cited as 165,563 MW on 2006-08-02, which the hour also exceeds by 16 % — but the in-file
  comparison above is the load-bearing one and needs no external source.)
* **(ii) Shape.** H13 is **1 p.m.** Every genuine annual peak in 2019–2025 lands at **H16–H19**,
  and that same day's H17 reads *lower* than its H13.
* **(iii) Internal consistency.** The row **fails EIA-930's own accounting identity by
  −56,665 MW**, where 2021–2024 close to a mean |residual| of 7–133 MW.

**The model serves both hours.** This is a rule 14 `[R-ACCURATE]` matter and it is a live input defect in a keeper year.

A stronger screen is available and costs no new parameter: **the extract's own accounting identity**, `|D + TI − NG|`, which is a property of the three published series and nothing else (rule 13 `[R-MEASURED]` admissible, reproducible forward, responsive). It flags both hours by a factor of ~400 over the 2021–2024 noise floor, where the median-ratio test flags neither. Noted as a candidate, **not** proposed as armed here: the same statistic is unusable in 2019, 2020 and 2025 precisely because the identity is broken wholesale in those years (§5.3), so it needs a design that distinguishes a broken *hour* from a broken *year*. That is a real design question and it belongs to the lane that owns the screen.

### 5.3 EIA-930's identity does not close for PJM in three years

`D + TI − NG`, which should be identically zero:

| year | hours \|res\| > 2 GW | max \|res\| MW | mean \|res\| MW | Σ res TWh |
|---|---|---|---|---|
| 2019 | 4,604 | 318,373 | 2,983.5 | **+9.85** |
| 2020 | 2,694 | 148,093 | 1,927.5 | **+8.56** |
| 2021 | 4 | 549,824 | 133.3 | +0.18 |
| 2022 | 1 | 8,855 | 7.0 | +0.04 |
| 2023 | 7 | 7,344 | 8.5 | −0.01 |
| 2024 | 1 | 39,896 | 7.2 | −0.02 |
| 2025 | **3,346** | 11,839 | 1,987.3 | **−14.76** |

**2021–2024 are essentially exact. 2019, 2020 and 2025 are not.** Consequences that matter and were not on record:

* **~9 of 2020's apparent +12.66 TWh "generation overshoot" is EIA-930's own unclosed identity**, not a model error. The model serves `D` exactly and generates `D + net export + losses − virtual net`; comparing that to a published `NG` that is 8.56 TWh below its own `D + TI` compares against a number the model's construction cannot match.
* **EIA-930's 2025 `Total interchange` is the wrong series** (§2.1), and correcting it removes the apparent 2025 sign flip in the export error.
* Any PJM comparison on the EIA-930 `Net generation` basis should be stated against `D + TI` in 2019/2020/2025, or those years excluded.

---

## 6. Two corrections to the state I was handed

Both were given to me as established; both are wrong on measurement, and both change a conclusion.

**(a) The model's internal energy sink is NOT storage round-trip loss.** I was told `class sum − demand` is "storage round-trip loss, monotone in storage build. There is no unexplained sink." The gap reproduces exactly (+3.371 / +3.374 / +4.359 / +3.649 / +4.487 / +5.119 TWh for 2020–2025) but its composition does not:

| TWh | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| class sum − demand | +3.371 | +3.374 | +4.359 | +3.649 | +4.487 | +5.119 |
| storage round-trip loss (sidecar) | +1.374 | +1.267 | +1.284 | +1.307 | +1.455 | +1.427 |
| slack | +0.040 | 0 | 0 | 0 | 0 | 0 |
| **residual = measured zonal loss surface** | **+2.037** | **+2.107** | **+3.075** | **+2.342** | **+3.032** | **+3.692** |
| storage as share of the gap | 40.7 % | 37.6 % | 29.4 % | 35.8 % | 32.4 % | 27.9 % |

Storage is the **minority** term (28–41 %), and it is **not monotone** (1.374 → 1.267 → 1.284 → 1.307 → 1.455 → 1.427). The majority is `pjm_zonal_loss_surface` — the pjm-136 one-way loss pairs on internal links, whose loss fraction enters the energy balance via `build_pjm_link_loss` + `dispatch.build_constraints(link_loss=...)`. The sink is fully explained, so the reassuring conclusion survives; the attribution given for it does not, and it matters because ~60–72 % of the gap was pointed at the wrong mechanism.

**(b) The PJM touchpoint's C2 is a PASS.** The charter states the touchpoint is "NOT-YET: C1/C2/C3a-b FAIL, C3c CAVEAT". `results/calibration/pjm_d4_4_TP/metrics.json` reads `sysvol: PASS`. The failures are **C1, C3a, C3b**, with C3c a ledgered CAVEAT — three fails, not four. This matters for §7: C2 passes on the touchpoint *while* CC_REGULAR is +22 to +26 TWh over, which is itself evidence about C2's reach.

### 6.1 The model's energy identity, stated so it can be checked

    physical generation = demand + net export + storage loss + zonal tx loss − virtual net − slack + dump

Residual, all six years: **0.000000 TWh.** The model's total generation is not a free quantity and cannot "overshoot" on its own — it is pinned by those six terms. So "does the model serve too much energy?" is not a well-posed question; the well-posed questions are whether each term is right. Demand is exact by construction. The two wrong terms are **net export** (−2.8 to −13.5) and **virtual net** (−10 to −12 in 2021/2022).

---

## 7. Q6 — GOVERNANCE PROPOSAL, for the owner. Not adopted, nothing re-scored.

Rule 1 `[R-STRUCT]`: a new criterion is a governance change and goes to the owner. **I have not added it, not changed any determination, and not re-scored any keeper against it.**

### 7.1 The blind spot is real

`sysvol` is *"C2 system volume (gas/coal families)"* (`scripts/calibration_verdict.py:925`) — gas and coal only. No criterion tests total system energy or interchange volume. PJM's keeper carries a **9.1–10.5 TWh net-export error (1.16–1.28 % of served load)** and scores **8/8 with zero caveats**. The touchpoint carries **+22 to +26 TWh** of CC_REGULAR over-run and its C2 **passes** (§6b).

### 7.2 A total-energy criterion would be vacuous. An interchange criterion would not.

§6.1 is the reason: the model's generation identity closes to zero by construction. A "total system energy" criterion could only fail if one of its six terms failed, and five of the six are either exact (demand), tiny (slack, dump) or structural mechanisms with their own evidence (losses). It would be a re-test of interchange and virtuals wearing a different hat — **it cannot fail independently, so it would add a criterion that cannot discriminate.** I recommend against it.

**The interchange-volume criterion has genuine content**, because that term is free, measurable against a settlement-grade boundary, and demonstrably wrong.

### 7.3 Retroactive effect across every ISO, scored from committed sidecars (zero LP)

Model net interchange (the `import` pseudo-unit class) versus EIA-930 `Total interchange`, worst year per ISO, as % of served load:

| ISO | worst-year \|error\| | worst year, TWh | current determination | measurable? |
|---|---|---|---|---|
| **CAISO** | **4.83 %** | −10.02 (2023) | CALIBRATED | yes |
| MISO | 1.55 % | +10.12 (2022) | NOT-YET | yes |
| PJM | 1.28 % | −10.36 (2024) | CALIBRATED | yes |
| NYISO | 0.33 % | +0.50 (2022) | CALIBRATED | yes |
| ERCOT | — | — | CALIBRATED | **no** |
| NEISO | — | — | CALIBRATED | **no** |
| SPP | — | — | CALIBRATED | **no** |
| SOCO | — | — | NOT-YET | **no** |
| NWPP | — | — | NOT-YET | **no** |

At a **2 %-of-load** threshold, exactly **one** determination flips: **CAISO, CALIBRATED → NOT-YET**. At **1 %**, two flip: **CAISO and PJM**. MISO is already NOT-YET.

### 7.4 The design objection that I think is decisive, and why I still recommend the stream

**Five of nine ISOs have no `import` class at all.** ERCOT, NEISO, SPP, SOCO and NWPP apply interchange as an exogenous adder to zonal demand, so their model interchange **equals** the measured schedule by construction and the criterion would **auto-PASS** them. It can only ever fail the four ISOs that carry a **priced, endogenous seam** — which is the *more* structurally faithful representation.

That inverts rule 1 `[R-STRUCT]`: it would penalise the ISOs that model the seam as a market and reward the ones that pin it to an actual. A criterion with that property should not gate.

There is a second, independent obstacle: **the benchmark is not settled per ISO.** For PJM, EIA-930's `Total interchange` is wrong by 14.96 TWh in 2025 and its whole identity is unclosed in 2019/2020; PJM's settlement tie file is the right boundary, and `interchange/spec.py` records that PJM's EIA-930 submission disagrees with both the tie file *and* the counterparty meters on the MISO seam (56.6 vs 35.3 vs MISO's own 33.5 TWh in 2023). Choosing the boundary is a per-ISO data-contract question, not a threshold question.

**Recommendation, for the owner to accept or refuse:**

1. **Add interchange volume as a REPORTED-ONLY stream now** — alongside `co2` and `diurnal_amplitude`, which already sit outside the determination. It costs nothing, changes no determination, is computable from committed sidecars for the four priced-seam ISOs, and makes a 10 TWh error visible instead of invisible. This is the part I would actually do.
2. **Do not gate it** until (a) every ISO's seam is on a priced node so the criterion can discriminate uniformly, and (b) each ISO's interchange boundary source is named in the data contract. Gating it today would decertify CAISO on a criterion three other ISOs cannot fail.
3. **Refuse a total-energy criterion** outright, on §7.2.
4. If the owner wants a gate sooner, the defensible narrow form is **per-ISO, supporting tier, priced-seam ISOs only, against that ISO's own settlement-grade boundary** — explicitly scoped so its silence on the other five is a stated limitation rather than a pass.

---

## 8. Ledger

**Nothing armed. No `ScenarioConfig` field added, no default flipped, no mechanism-matrix cell moved, no run registered, no determination changed, no keeper touched.** Zero LP minutes in this session.

**Chartered candidates for later lanes, each with its basis and its cost stated:**

| # | candidate | basis | expected on the residual |
|---|---|---|---|
| 1 | Add **2020** to `PJM_SEAM_LADDER_BY_YEAR` via `derive_pjm_seam_ladders.py` | rule 23 `[R-FROZEN-DERIVE]` (source data already covers it); rule 14 — a keeper year must run the keeper's mechanism | **probably WORSE** (§2.6). Not a residual argument. |
| 2 | Measure the **gross export / gross import split** per seam from `hourly/network_<year>.parquet` | closes Q2 by replacing §2.5's inference with a measurement; picks WHICH leg a lever should target, which differs by year | diagnostic only |
| 3 | Strengthen the **demand spike screen** using the extract's own `D + TI − NG` identity | rule 14 (§5.2); two artifact hours survive today | removes ~0.3 TWh of phantom 2020 demand |
| 4 | The **pre-2023 CC_REGULAR / under-export / virtual-net** triple | §4.2 + §2 + §3 land on the same years; the virtual leg is pjm-d4-3's, already escalated at pjm-159 | unknown; needs (2) first |
| 5 | The **pumped-storage benchmark seam** (§4.3) | 923 books PS net-negative; the model reports discharge | accounting only |
| 6 | Interchange volume as a **reported-only** stream | §7 | none by construction |

**Not re-litigated** (rule 28 `[R-MECH-MATRIX]` (a)): the 2022 price miss is the 18-hour Winter Storm Elliott scarcity tail with no admissible lever (`docs/FINDING-pjm-h3b-2022-miss-is-the-elliott-tail-2026-09-13.md`); the Dominion CT zonal-congestion route is closed by measurement at pjm-137; pjm-158 closed the virtual layer's invariant-price question, and pjm-d4-3 §4 owns the six-year virtual-net measurement — §3 here is corroboration on a newer keeper, not a new result.

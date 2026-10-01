# FINDING (pjm-h1, part 2): **CC_REGULAR is the ONLY PJM class whose fleet capacity factor does
# not track reality across years** — r = −0.18 against +0.78 to +0.97 for every other class.
# Three candidate causes falsified at zero LP; the surviving one is inside the closed frontier.

**Session** `pjm-h1` · **ISO** PJM · **Date** 2026-09-12 · **Branch** `claude/pjm-h1`
**ZERO LP.** Committed run payloads, committed bench parts, CAMPD unit-level, the model's own
fleet loader. **Nothing solved, nothing armed, nothing registered, no verdict moved.**
Companion: `docs/FINDING-pjm-h1-hydro-accounting-seam-2026-09-12.md` (the commissioned card).

---

## 1. RESULT

> The handoff's second half asked for **a run that may resolve the holdout-year misses**. What
> phase 0 produced instead is a **sharper object and three dead candidates** — which is the more
> useful deliverable, because two of the three are the ones a successor would have spent an LP on.
>
> **THE SIGNATURE.** Matched-fleet annual capacity factor, model vs CAMPD meter, 2020-2025:
>
> | class | model CF range | meter CF range | **cross-year r** | d(model CF)/d(meter CF) |
> |---|---:|---:|---:|---:|
> | **CC_REGULAR** | **0.015** | **0.058** | **−0.183** | **−0.046** |
> | COAL_BIT | 0.144 | 0.113 | **+0.912** | +1.078 |
> | CT_PEAKER | 0.057 | 0.026 | **+0.896** | +2.010 |
> | ST_GAS | 0.107 | 0.127 | **+0.968** | +0.756 |
> | CC_CHP | 0.110 | 0.147 | **+0.775** | +0.672 |
>
> **Every PJM fossil class tracks the real fleet's year-to-year capacity factor except
> CC_REGULAR, which is flat and faintly anti-correlated.** The model runs PJM's ~54-62 GW
> merchant CC fleet at a **0.606-0.621** capacity factor in all six years — a 1.5-point band —
> while the metered fleet moves over **5.8 points** (0.550 in 2021, 0.563 in 2022, 0.586-0.609
> in 2020 and 2023-2025). **The two years the model is flattest against are exactly the two
> years C1 fails** (2021 CC_REGULAR +26.31 TWh, 2022 +22.56 TWh).
>
> This is a **class-specific dispatch-response deficit**, and that is what makes it worth
> naming: it is not a system-wide merit-order or price-level fault, because COAL_BIT, CT_PEAKER
> and ST_GAS — including two classes burning the *same* gas — all follow reality.
>
> **THREE CANDIDATES FALSIFIED, EACH AT ZERO LP** (§3). I state them because each is the
> obvious next lever and each would have cost a solve:
> 1. **Partial derates / capability loss — FALSIFIED.** The meter's revealed capability
>    (p99.5 MW ÷ nameplate, fleet mean) is **flat at 0.894-0.912 in every year**. There is no
>    2021/2022 capability collapse for a derate mechanism to find. *(And the committed
>    `campd-partial-outages-shaped.csv` carries **zero PJM rows** — it is ERCOT-only, matching
>    `ercot_partial_outage_shaped_derate` = `.`; arming it for PJM would be a derive job, not a
>    flag, and §3 says it would be a derive job pointed at nothing.)*
> 2. **CC heat rate — FALSIFIED.** CC_REGULAR carries the eGRID plant-average ANNUAL rate: it
>    has no measured artifact, where `measured_ct_heat_rates` (**K**) and
>    `measured_chp_heat_rates` (**K**) both do. That asymmetry looked like the answer. Measured
>    against CAMPD `heatInput/grossLoad` over 4.76 M unit-hours on all 70 plants: capacity-
>    weighted model **7.195** vs measured-net **7.297 MMBtu/MWh**, i.e. the model is **1.4 %
>    CHEAP**, median per-plant delta **+0.008**, and **39 of 69 plants are DEARER in the model
>    than in the meter**. The fleet rate is right. *(Per-plant outliers exist — 55976, 55337,
>    55710 read 3.3-4.1 MMBtu/MWh cheap — and are a separate, much smaller question.)*
> 3. **Forcing — FALSIFIED upstream and re-confirmed here.** pjm-d4-3 measured
>    `cc_mustrun_per_plant` forcing 9.4/6.4/9.4 TWh in 2020-22 against 23.8/13.3/10.5 in
>    2023-25 — **least where the surplus is largest**. Not a rule-17/19 object.
>
> **WHAT SURVIVES, and it is not a lever I may pull.** The model's CC fleet is online **78-83 %**
> of hours at **72-76 %** loading, every year; the meter is online **70-78 %** at **71-74 %**.
> A class that is online four-fifths of every year at three-quarters load, invariantly, is a
> class sitting so far below the clearing price that price variation never reaches it — and
> PJM's measured **D-A diurnal price amplitude is 29.9-32.9 % of measured in every year**
> (a chronic property, which pjm-d4-3 correctly established is *not* a holdout signature). A
> compressed price distribution produces exactly this: too few hours dipping below CC marginal
> cost, so the fleet never backs off. **That is PJM price formation, which is inside the
> owner-declared-closed frontier (pjm-142) and already the subject of the standing pjm-159
> escalation.** §4 routes this there as new evidence rather than opening it.

---

## 2. THE MEASUREMENT

Plant-matched, decoded exactly as `legitimacy_diagnostics` decodes the committed payload and
bench (`_decode_cf_bytes`, `load_bench`, `load_payload_plants`); model from
`2026-09-11-pjm-holdout-gasoutage-touchpoint` (2020-22) and `2026-09-11-pjm-d4-4-gasoutage`
(2023-25) — the current keeper pair.

**CC_REGULAR, matched fleet (65-70 plants, 53.7-61.9 GW):**

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|
| model CF | 0.6177 | 0.6189 | 0.6205 | 0.6061 | 0.6208 | 0.6158 |
| meter CF | 0.5855 | **0.5504** | **0.5629** | 0.5884 | 0.6085 | 0.5983 |
| **Δ** | +0.0322 | **+0.0685** | **+0.0576** | +0.0177 | +0.0123 | +0.0176 |
| model on-hours | 0.8099 | 0.7927 | 0.7831 | 0.8049 | 0.8315 | 0.8035 |
| meter on-hours | 0.7332 | 0.7047 | 0.7253 | 0.7591 | 0.7835 | 0.7666 |
| **on-hours gap (pp)** | **+7.7** | **+8.8** | **+5.8** | +4.6 | +4.8 | +3.7 |
| model loading when both on | 0.7239 | 0.7499 | 0.7563 | 0.7402 | 0.7419 | 0.7464 |
| meter loading when both on | 0.7322 | 0.7100 | 0.7199 | 0.7354 | 0.7400 | 0.7355 |
| **meter revealed capability** (p99.5/npl) | 0.8935 | 0.9024 | 0.9121 | 0.9103 | 0.9051 | 0.9029 |

**The hours/loading split** (pjm-d4-3 §2's construction, reproduced on the current keeper):

| yr | net | hours leg `a−c` | loading leg `b+ − b−` | `a` | `b+` | `b−` | `c` |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2020 | +15.16 | +14.31 | +0.85 | 18.34 | 27.62 | 26.77 | 4.03 |
| 2021 | +33.81 | +16.56 | **+17.26** | 20.06 | 35.91 | **18.66** | 3.50 |
| 2022 | +29.66 | +11.29 | **+18.37** | 15.50 | 38.07 | **19.69** | 4.21 |
| 2023 | +9.59 | +6.76 | +2.83 | 13.02 | 29.04 | 26.21 | 6.26 |
| 2024 | +6.67 | +6.09 | +0.58 | 11.93 | 28.79 | 28.22 | 5.84 |
| 2025 | +9.51 | +5.13 | +4.39 | 9.15 | 30.14 | 25.76 | 4.02 |

**A correction to how that split has been read.** `b+` is nearly constant (27.6-38.1 TWh) and
spread evenly over all twelve months in every year — there is no seasonal or event signature.
What moves is **`b−`, which collapses ~7-9 TWh in 2021/2022**. The "holdout-distinctive loading
leg" is not a new object appearing; it is the *offsetting* under-run disappearing. Both legs are
the same statement as the CF table: the whole distribution shifts up relative to the meter.

**And the over-run is FLEET-WIDE, not a plant set.** In 2021/2022, 46-47 of 68-70 plants are
over, and the top five carry 52-54 % of the net; in the training years the top five carry
123-170 % (the rest net negative). A membership/registry repair of the `pjm-d4-2` shape has
nothing to bite on here.

---

## 3. THE FALSIFICATIONS, AS RUN

**Capability.** Per-plant p99.5 hourly meter MW ÷ nameplate, fleet mean: 0.8935 / 0.9024 /
0.9121 / 0.9103 / 0.9051 / 0.9029. **2022 is the HIGHEST of the six years** and 2021 is mid-range.
A derate mechanism looks for capability the model does not see; in PJM CC there is none to find.

**Heat rate.** CAMPD unit-level over all 70 bench CC_REGULAR plants, 2023-2025 (the same pooling
window `measured_ct_heat_rates` uses), operating hours only (`opTime>0`, `grossLoad>0`,
`heatInput>0`): 4,756,608 rows, 993.2 TWh gross on `unitType == "Combined cycle"`.
Fleet energy-weighted **gross** 6.9889 MMBtu/MWh → **net** ≈ 7.146 at a stated (not fitted)
2.2 % own-use. Model side from `load_fleet_from_csv("PJM", …)` at the keeper's own heat-rate
flags. Paired over 69 plants:

| | capacity-weighted | median per-plant Δ | plants model CHEAP | plants model DEAR |
|---|---:|---:|---:|---:|
| model | **7.1954** | **+0.008** | **30 / 69** | **39 / 69** |
| measured (net) | **7.2974** | — | — | — |
| **Δ** | **−0.1020 (−1.40 %)** | | | |

**Reported against my own hypothesis:** I expected the model's CC to be systematically too
efficient and therefore stuck too deep in merit. It is 1.4 % cheap at the fleet and *dearer*
than the meter at a majority of plants. **The hypothesis is refuted and a `measured_cc_heat_rates`
candidate should not be built on it.**

---

## 4. WHAT I ROUTE, AND WHAT I DO NOT PROPOSE

**No run is proposed, and that is the finding.** Rule 1 `[R-STRUCT]` and rule 28(a) both bite:
the three mechanisms a successor would reach for are measured dead, and the one live explanation
is price-distribution compression inside PJM's owner-declared-closed price-formation frontier
(pjm-142), where `da_virtual_bids` is already `K`-with-escalation after pjm-158 solved the
single-delta arm, pjm-159 closed the architecture, and pjm-166 / pjm-d4-3 re-measured without
arming. **Arming anything at PJM CC to close a 22-26 TWh surplus whose surviving cause is the
price distribution would be fitting a mechanism to a residual.**

**What this adds to the standing pjm-159 escalation, that was not in it:** the compression's
consequence is now *class-attributed and falsifiable*. Previously "the amplitude is 30 % of
measured" was a price statistic with no dispatch consequence attached. It now has one: **the
one class the compression should pin is the one class whose CF does not track (r = −0.18),
and every class it should not pin tracks at r = +0.78 to +0.97.** If the frontier is ever
re-opened, this is the prediction to test it against — and it is refutable: a price-amplitude
repair that does not move CC_REGULAR's cross-year CF correlation off ≈ 0 has not addressed it.

**Recorded so no successor spends an LP on them:** the partial-derate lever (falsified, and its
artifact carries no PJM rows), `measured_cc_heat_rates` (falsified at the fleet), and any
membership/registry repair of the `pjm-d4-2` shape (the over-run is fleet-wide).

---

## 5. RULES

* **Rule 29 `[R-SCREEN]` clause 0** — zero-LP phase 0 killed three arms before any solve, which
  is the clause working as written.
* **Rule 28 `[R-MECH-MATRIX]` (a)** — `da_virtual_bids` (**K**, escalated), `temp_dependent_derate`
  (**R**), `pjm_measured_outage_event_cap` (**R**), `ercot_partial_outage_shaped_derate` (**·**),
  `cc_committed_offer_margin` (**U**, instrument-blocked), `measured_ct_heat_rates` /
  `measured_chp_heat_rates` (**K**) all read before anything was proposed. Duty (b): **no
  mechanism was tested and no cell verdict moves**; the falsifications are recorded here and
  annotated on PJM's shard.
* **Rule 1 `[R-STRUCT]`** — nothing armed toward a residual; the only surviving explanation is
  escalated, not pulled.
* **Rule 30(c)** — the training span is untouched and re-verified CALIBRATED (0 caveats).

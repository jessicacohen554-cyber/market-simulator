# DECISION CARD — NYISO's C1-2024 `CC_REGULAR` cell: the "re-open G vs accept" question was built on a premise that has now been measured and is **false**

**For:** the owner. **From:** session nyiso-190, `backcast-calibration` lane,
2026-09-05. **Solves run: ZERO.** **Keeper unchanged**
(`2026-09-05-nyiso-189-steam-identity`, CALIBRATED, grade 7, fails 0).
**Evidence:** `docs/FINDING-nyiso190-cc2024-displacement-provenance-2026-09-05.md`;
bars pre-registered and pushed before the first number
(`results/calibration/PREREG-nyiso190-cc2024-displacement-provenance.md`);
machine records `_nyiso190_displacement_provenance.json`,
`_nyiso190_plant_grain_posthoc.json`.

---

## 1. WHAT YOU WERE GOING TO BE ASKED, AND WHY YOU ARE NOT BEING ASKED IT

The nyiso-189 queue put this to you as a two-option disposition: **re-open cell
`scuc_load_pocket_commitment` (G)** so the market's out-of-market commitment of
NYC CT/steam is represented, **or accept C1-2024 `CC_REGULAR` at +2.8 pp**
against a 3.0 pp band. Both options rested on one sentence in the nyiso-189
FINDING — that the +1.28 TWh the promotion added to the cell was *"the NYC
steam it displaces … what the market committed anyway."*

**That sentence was never measured. This session measured it, on bars fixed and
pushed beforehand, and it is false in both halves.** So the card does not put
the G question to you: putting it would be asking you to spend an irreversible
governance decision on a premise the evidence does not support.

---

## 2. WHAT THE MEASUREMENT SAYS (2024 gated; 2023 / 2025 agree)

| bar | asks | result | verdict |
|---|---|---|---|
| **B1** | did the market have the displaced units ON in the hours the model took energy off them? | **0.839** of removed MWh in measured-online hours (0.750 / 0.834 in 2023 / 2025) | **YES** |
| **B2** | did taking that energy off move those plants AWAY from what they actually generated? | **0.219** away — i.e. **78 % moved TOWARD actual** (0.139 / 0.375 in 2023 / 2025; 0.216 on the EIA-923 basis, both bases agree) | **NO** |
| **B3** | is the gas family still pinned, so this is a reallocation and not a volume error? | arm moves the six-class family by **0.042 TWh**; sits +1.87 from the family actual against a ±3.82 band | **YES** |
| **B4** | is the displaced set actually NYC steam / cogen? | **0.42** downstate steam/cogen — below the 0.50 naming bar fixed in advance | **NO** |

**In plain terms.** The market did have those units running; the model was
running them *harder than the market did*, and the nyiso-189 displacement
partly corrected that. The energy did not come out of a market-committed
deficit. And the set it came from is not what the sentence names: it is 0.76
TWh `CC_CHP`, 0.46 `CC_REGULAR`, 0.30 `ST_GAS`, split NYC 0.74 /
Capital-Hudson 0.71 / Upstate-West 0.21.

Every plant the lane was told to check is a plant the model was **over**-running,
on both actual bases (TWh, 2024, control → arm vs CAMPD): Empire 4.16 → 3.88
vs 2.98; Brooklyn Navy Yard 2.88 → 2.66 vs 1.80; Cricket Valley 5.11 → 4.95 vs
4.24; East River steam 1.27 → 1.16 vs 0.56; Ravenswood steam 2.52 → 2.42 vs
0.68; Arthur Kill 2.23 → 2.13 vs 1.35.

---

## 3. WHAT IS ACTUALLY THERE INSTEAD

Class totals were hiding it. On the keeper, 72 benched plants carry
**+11.25 TWh of over-run against −8.18 TWh of under-run** for a net of +3.07 —
about **±8 TWh of offsetting plant-grain misallocation inside a family the
class totals say is pinned** (±7.4 in 2023, ±9.3 in 2025). Three plants sit at
the top of it in all three years, and all three are `CC_CHP`:

* **Sithe Independence** (Upstate-West, 1,158 MW): model 9.48 TWh vs 6.29
  measured in 2024, a **0.93 annual capacity factor against a measured 0.62**,
  rising to 0.97 vs 0.62 in 2025.
* **Brooklyn Navy Yard** (NYC, 322 MW): the model holds it at ≥95 % of
  nameplate for **6,200–8,200 hours a year**; its own CEMS record reaches that
  level in **zero** hours of any year.
* **Empire Generating** (Capital-Hudson, 654 MW): +0.90 TWh, ≥95 % of nameplate
  for 2,041 h against 65 measured.

**And there is an obvious reason.** `cc_capacity_reconcile` — already NYISO
cell **K**, promoted at nyiso-188 — bounds per-plant LP capacity at the plant's
own CAMPD demonstrated peak, which is precisely this defect. **Its derive is
scoped to `CC_REGULAR` by construction**, and its 15-row NYISO table contains
no `CC_CHP` plant: Sithe, Empire and Brooklyn Navy Yard are all outside it.

---

## 4. WHAT I AM ASKING YOU (one question)

**Should the next NYISO session A/B the `CC_CHP` scope extension of
`cc_capacity_reconcile`?**

* **(A) Yes — test it.** One arm, one same-HEAD control, 2023–2025 in one
  bundle. It is a scope change to an existing `K` mechanism using the identical
  frozen zero-parameter rule (each plant's own CAMPD p99.9), so it adds no
  degrees of freedom and needs no new construction — rule 14 `[R-ACCURATE]`
  territory.
* **(B) No — leave it, accept C1-2024 at +2.8 pp and hold the cell.** Defensible
  if you would rather not spend solves near a band edge.

**What you should know before answering, stated at full magnitude:**

1. **The direction is genuinely unknown and could make the cell worse.** Capping
   `CC_CHP` releases energy that may land on `CC_REGULAR` — which would push
   the cell past its 3.0 pp band and cost the CALIBRATED determination — or on
   the `CT_PEAKER` / `CT_CHP` / `ST_GAS` deficits, which would improve the cell
   *and* those cells. I will not guess which; that is what the A/B is for.
   Under rule 1 the reason to run it is that the model demonstrably runs three
   plants above their demonstrated capability for thousands of hours a year,
   **not** what it does to the residual — and under your standing formula a
   structurally-better run with a worse gate can still be a keeper.
2. **The headroom is 0.49 TWh / 0.2 pp.** That is what stands between the
   current keeper and a C1-2024 failure.
3. **This is not the load-pocket question.** Cell **G** stays `G`. Nothing here
   re-opens it, and nothing here *could*: nyiso-97 §5 forbids identifying that
   mechanism from observed unit conduct, and this whole measurement **is**
   observed unit conduct. The nyiso-160 access closure stands.
4. **The CT deficit half of the disposition is untouched and still yours.**
   `CT_PEAKER` −1.59 and `CT_CHP` −1.20 TWh in 2024 remain the nyiso-187
   out-of-market-commitment object, behind cell G and the accepted CT markup
   trade. Nothing in this session changes that.

## 5. WHAT THIS CARD DOES NOT ASK FOR

No marker (D56 has not landed; NYISO holds neither `complete` nor `final` and
the freeze is active). No keeper change. No band move. No CC volume lever. No
ruling on C3a-2025 — `DECISION-CARD-nyiso148` Q1 is confirmed still pending and
untouched. No re-open of cell G.

---

## 6. ONE CORRECTION TO THE RECORD, FOR HONESTY

The nyiso-189 FINDING §3.1 and the §5.5 matrix header both carry the clause
*"the NYC steam it displaces is what the market committed anyway."* **That
clause is withdrawn as a statement of fact** and the correction is recorded in
this session's finding and in the matrix queue. **The keeper itself is not
affected**: its promotion license was rules 14 + 13 + 1 on a measured-input
repair whose defect three independent bases established before any residual was
read, and no gate, score or determination moves. What was wrong was a *reason
offered in prose about where the energy went* — and it is now measured.

*(nyiso-190, 2026-09-05.)*

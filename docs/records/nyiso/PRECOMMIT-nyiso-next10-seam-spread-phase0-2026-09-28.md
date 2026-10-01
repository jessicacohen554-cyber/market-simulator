# PRECOMMIT — NYISO-NEXT-10 phase 0: does each seam's flow follow its OWN spread? (ZERO LP)

Written and committed **before** any spread statistic was computed. The intake
(`seam-neighbour-price`, this lane) is in hand; no flow-vs-spread number has been
looked at.

## 1. Question

NEXT-7 §3(b) refused a per-neighbour split of the NYISO import ladder because
several seams' hourly flows do not co-move with the **NY** price (NE AC is
anti-monotone every year; IESO and PJM DC near zero). §3(c) named the missing
object: each neighbour's **own** price. With it in hand: does each seam's hourly
net import co-move with its **spread** (NY landing price − neighbour price)?

## 2. Series (all measured, all hourly, aligned on `interval_start_utc`)

- **Flow** `F_g`: NYISO P-32 `SCH -` rows (`data/raw/NYISO/interface-flows`), + = import to NY.
- **NY landing price**: NYISO DA LBMP at the seam's landing zone (primary) and at
  its NY proxy bus (check), `seam-neighbour-price/nyiso`.
- **Neighbour price**: PJM DA LMP at the matching INTERFACE pnode; ISO-NE DA LMP
  at the matching external node; IESO HOEP converted at the Bank of Canada daily
  USD/CAD (IESO has no DA market pre-2025-05; 2025 = Jan–Apr only).

| group | SCH rows | NY landing zone / proxy | neighbour price |
|---|---|---|---|
| IESO | OH - NY | WEST / `O H` | HOEP (USD) |
| PJM_AC | PJ - NY | — / `PJM` (multi-zone PAR landing: proxy only) | PJM `NYIS` |
| PJM_HTP | PJM_HTP | N.Y.C. / `PJM_GEN_HTP_PROXY` | PJM `HUDSONTP` |
| PJM_VFT | PJM_VFT | N.Y.C. / `PJM_GEN_VFT_PROXY` | PJM `LINDENVFT` |
| PJM_NEPTUNE | PJM_NEPTUNE | LONGIL / `PJM_GEN_NEPTUNE_PROXY` | PJM `NEPTUNE` |
| NE_AC | NE - NY | CAPITL / `NPX` | ISO-NE `.I.ROSETON 345 1` |
| NE_CSC | NPX_CSC | LONGIL / `NPX_GEN_CSC` | ISO-NE `.I.SHOREHAM138 99` |
| NE_1385 | NPX_1385 | LONGIL / `NPX_GEN_1385_PROXY` | ISO-NE `.I.NRTHPORT138 5` |
| HQ | HQ - NY, HQ_CEDARS | — | **none (no market)** — stays a proxy/economic block, not tested |

## 3. Statistic

Per group g and year y: Spearman ρ_spread(g,y) = ρ(F_g, P_landing − P_neighbour)
and, as the NEXT-7 comparator recomputed on the same hours, ρ_NY(g,y) =
ρ(F_g, NY DA system mean). Hours with any series missing are dropped.

## 4. Decision rule (ex ante)

A group g is **spread-identified** iff all three hold over the years it has data:

- **S1** ρ_spread > 0 in **every** year;
- **S2** ρ_spread > ρ_NY in at least all-but-one year;
- **S3** median-over-years ρ_spread ≥ 0.30.

0.30 is a **decision threshold** fixed here, not a model parameter; it is the
floor below which a monotone Q-Q pairing of flow and spread (the frozen ladder
formula, transferred in kind) would pair quantiles that are mostly noise.

**Construction verdict.** A per-neighbour spread construction proceeds to a
PRECOMMIT **only if** the object NEXT-7 §2 sized is covered: **NE_AC** (the
Capital_Hudson over-delivery, 2.3–4.65 TWh/yr of the 4.85–7.60) **and** every
downstate DC group carrying ≥ 0.5 TWh/yr of the NYC/LI excess are
spread-identified, **and** a zero-DOF offset derivation exists for each (the
frozen Q-Q formula on the spread, whose admissibility is exactly S1–S3). If any
fails: **STOP with a FINDING**; no solve, no keeper change.

Whatever the verdict, promotion of any later arm is on structure only (rule 1),
never on C3a moving.

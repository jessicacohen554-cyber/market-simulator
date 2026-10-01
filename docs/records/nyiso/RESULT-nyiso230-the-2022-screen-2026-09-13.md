# RESULT — nyiso-230: the 2022 screen **STOPS**, and the defect it found is **in my own build**, not in the mechanism

**Session:** nyiso-230 · **ISO:** NYISO · **Date:** 2026-09-13
**Pre-registration:** `results/calibration/PRECOMMIT-nyiso230-zonal-anchor-vintage.md`, pushed
before any LP. Gate scorer `scripts/probes/nyiso230_screen_gates.py`, **committed before the arm's
numbers existed**. Gate JSON: `results/calibration/_nyiso230_screen_gates_2022.json`.
**Keeper `2026-09-12-nyiso229-hourgrain-span` UNCHANGED. Nothing promoted, nothing registered.**
**Rule 32 `[R-SHARD]`: the parent ran ZERO LP.** Two shard containers; the second produced the arm.

---

## 0. Headline

| gate | pre-registered test | measured | verdict |
|---|---|---|---|
| **G-CONF** | exactly one field moves; recorded anchors == PRECOMMIT §5 to 1e-6 | **three** fields moved; anchors off by a uniform **−1.3868 $/MMBtu** | **STOP** |
| **G-SCOPE** | every band multiplier / `phys_*` / `peak` / shares bit-identical | **0 moved** | **PASS** |
| **G-PRED** | measured ÷ predicted anchor delta in [0.95, 1.05] | **0.585 / 0.694 / 0.694 / 0.645 / 0.694** | **STOP** |
| **G-DEMAND** | served demand identical to 4 dp, dump 0 | **152.68167 TWh both legs**, dump **0.000**, slack **0.000** both | **PASS** |

**The screen STOPS, and I am not re-cutting the gates to rescue it.** Rule 29 `[R-SCREEN]` (c) fixes
gates before the solve precisely so they cannot be re-read once a number is on the table.

**But the STOP is not a verdict on the mechanism.** It is a verdict on my plumbing, and the
distinction is measured rather than argued (§2).

## 1. WHAT THE ARM DID, at full magnitude

| | control (`nyiso229_arm_y2022`) | arm | |
|---|---|---|---|
| load-weighted mean LMP | 67.6573 | **73.1275** | **+5.470 $/MWh** |
| served demand | 152.68167 TWh | **152.68167** | identical |
| dump / firm-load slack | 0.000 / 0.000 | **0.000 / 0.000** | identical |
| hours > $300 | 4 | **5** | +1 |

**Reported, never gated on** (rule 29: a screen that reads the target residual is the
fitted-mechanism selection rule 1 `[R-STRUCT]` forbids, done one year at a time). Direction is as
declared ex ante in PRECOMMIT §7: 2022 gas sits above the anchor, so the arm raises offers and 2022
prices rise. C3a-2022 was **−16.6 %**; +5.47 $/MWh against an 81.12 actual moves it to about
**−9.8 %**. **That number is NOT a result of this screen** — see §2, which is why.

## 2. THE DECISIVE DIAGNOSIS: the recorded anchors were resolved WITHOUT the hub overlay

The five recorded anchors miss the PRECOMMIT prediction by a **constant −1.3868 $/MMBtu in every
zone** — Upstate_West 3.9863 vs 5.3731, Capital_Hudson / Lower_Hudson / Long_Island 7.0563 vs
8.4431, NYC 5.2763 vs 6.6631. A *constant* offset across zones says the zonal transform is exactly
right and only the ISO-level series differs, so the cause is upstream of the zone split.

Bisected at zero LP over every gas flag on the recorded config:

| variant | Capital_Hudson | vs solved |
|---|---:|---:|
| as recorded (all flags on) | 8.4431 | +1.3868 |
| **`gas_hub_basis_overlay=False`** | **7.0563** | **0.0000 — MATCH** |
| `gas_hub_basis_daily=False` | 8.4431 | +1.3868 |
| `gas_daily_shape=False` | 8.4431 | +1.3868 |
| `gas_monthly_actuals=False` | 8.4431 | +1.3868 |
| `gas_seasonality=False` | 8.4431 | +1.3868 |

**The recorded anchors were computed on a series with no Transco Z6 hub overlay.** That is exactly
the failure my own field comment warns against — *"resolved AFTER the hub-overlay and
monthly-actuals flags are applied … resolving at the lookup would measure a series the offer path
never prices"* — and I wrote the `run_calibration_full._recorded_config` mirror in a place where
`recorded_cfg` does not yet carry `gas_hub_basis_overlay`. `run_calibration.run_year`'s own
resolution is correctly placed (the overlay is set at line 1960, the resolution at 2565), so **the
two halves disagree**.

**THE OPEN QUESTION THIS LEAVES, STATED RATHER THAN GUESSED: I do not know which anchor the LP
priced against.** If `run_year` recomputed and overwrote, the LP solved on the correct 8.4431 while
`run_config.json` records 7.0563 — the FFR-2E defect class my own comment names, and it would also
mean the **cache key claims a resolution the solve did not perform** (rule 24 `[R-REGISTRY]`). If
the mirror's value reached the LP, the arm under-shot its own mechanism by 30 %. **The +5.470 $/MWh
cannot be attributed until that is settled**, and no number from this screen should be quoted as
the mechanism's effect. The shard was asked to report the `gas offer margin ZONAL anchors VINTAGE`
log line, which would settle it directly; it did not, and the bundle does not carry the log.

**The third moved field is benign and is NOT the reason for the STOP.**
`miso_import_sil_measured_envelope` reads `False` in the arm and `None` in the control: the field
did not exist when the control's config was serialized and now materializes at its default. It is a
MISO-only gate at False. G-CONF still fails on the document as written, and I am recording that
rather than waiving it.

## 3. WHAT IS NOT IN DOUBT

* **G-SCOPE and G-DEMAND both PASS cleanly.** Zero band multipliers, `phys_*` keys, `peak` bands,
  `econ_low_share` or `pct_peaking` moved — the arm touches no offer curve, which is the whole
  claim that it is not the rule 1 `[R-STRUCT]` carve-out. Served demand is identical to 4 dp with
  zero dump and zero slack on both legs.
* **The resolver itself is correct.** Its identity test (mean over 2023–2025 reproduces the
  registered `GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` to 4.7×10⁻⁵) passes, and §2's bisect shows it
  reproduces the *solve's* number exactly once given the same flags. The defect is WHERE the mirror
  is called, not WHAT it computes.
* **The sibling carries the same latent defect.** `gas_offer_margin_anchor_vintage` (pjm-169 F4)
  computes its mirror from the same `recorded_cfg` at the same point, so any ISO arming it records
  an anchor resolved without its hub overlay. Nothing is armed on it anywhere (PJM's cell is `R`),
  so this is a warning, not an incident — but it is the same one-line seam.

## 4. WHAT THIS DOES NOT SHOW

* **Nothing about 2023–2025.** One year, and rule 16 `[R-ALLYEARS]` needs the span for any keeper.
* **Nothing about C1-2024**, the failure this lane is actually trying to close.
* **Nothing about phase 0's collinearity caveat.** Separating the anchor mechanism from generic
  price-variance compression needs the span, not one year.
* **No determination is computed and nothing is registered** (rule 29 clause (2): a screen bundle
  is never registered).

## 5. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

The arm bundle is **pushed and retrievable**, 17 files, at full SHA
**`90475b1c2b56283018396504e39ad638ac367c97`** (branch `claude/nyiso230-arm-y2022-solve`):
`git checkout 90475b1c2b56283018396504e39ad638ac367c97 -- results/calibration/nyiso230_arm_y2022`.
A promotion from this state costs **zero re-solves for 2022** — but the span (2023/2024/2025) has
never been solved on this arm, so a promotion still costs those three years.
The first shard's blocker record is at **`9f11d68e16707b47732e43474af46811867fb640`**.
**Nothing deleted** (rule 31 `[R-RETAIN]`).

## 6. RULES

1 `[R-STRUCT]` — the price move was declared ex ante and is not a gate; the failing gates are
reported as failures rather than re-specified. 13/14 — the same measured quantity at its own
vintage. 16 `[R-ALLYEARS]` — no span, no keeper claim. 19 `[R-ONE-MECH]` — one identification point;
the phase-0 `ST_GAS` object deliberately not co-armed. 21 `[R-DOF]` / 24 `[R-REGISTRY]` — zero free
parameters, and §2 raises a rule-24 recording defect against my own build. 25 `[R-ISO-SCOPE]` —
nothing transferred. 29 `[R-SCREEN]` — phase 0 first, screen year on footprint, gates structural,
stop-only and pre-committed with their scorer; the screen killed the arm and the remaining years
were **not** spent. 30(c) — a 2022 result cannot certify or decertify NYISO. 31 `[R-RETAIN]` —
nothing deleted. 32 `[R-SHARD]` — the parent ran no LP. 33 `[R-SHARD-ARCHIVE]` — both shards
archived after their bytes were fetched and verified. 34 `[R-SHARD-PROMOTABLE]` — the bundle is
pushed and its recovery SHA recorded.

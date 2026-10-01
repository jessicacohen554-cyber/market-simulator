# FFR-2C — net-CONE currency re-anchor + the FF-G3 escalation evidence (FR-19)

**Session.** FFR Wave 2, the light-solve lane
(`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-2C). Closes audit finding
**FR-19** and supplies the measured evidence for **owner decision D-3**.
Branch `claude/ffr-2c-net-cone-ff-g3-k2dvo0`, based on `origin/main` `9950a5c`
(2026-08-02). Container had no `results/**/year_*.parquet`, so the 2026-08-02
cache epoch had nothing to purge and every solve below ran **cold**.

**One-line result.** Two of the four stale forward net-CONE vintages are
re-anchored from their published instruments — **PJM 2027/28 → 2028/29
(+34.3 %)** and **NYISO 2025-26 → 2026-27 (+14.1 %)** — the other two are
adjudicated rather than guessed, and the FF-G3 D1–D5 box is populated with
measured spreads. **No `ScenarioConfig` default was changed and no escalation
option was flipped.** The single largest finding is not the level: it is that
PJM's new vintage carries a **published price floor that removes the curve's
zero-cross**, which supersedes FF-2C's "PJM curve flip is quantitatively inert"
conclusion from solve year 2028 onward.

---

## 1. What FF-G3 was blocked on, and what actually blocked it

FF-G3 (2026-07-20) designed the escalation machinery and then could not encode a
single vintage, filing all four as MANUAL DOWNLOADS NEEDED: "standard fetch
returns empty; the 2028/29-era numeric tables are **images**; the authoritative
XLSX / FERC eLibrary attachments return JS shells."

That diagnosis was right about the *documents it tried* and wrong as a general
conclusion. Re-probed this session:

| Source | FF-G3 status | Now |
|---|---|---|
| PJM 2028/29 narrative report PDF | obtained; Table 3 is an image | same — **and re-downloaded byte-identical** to FF-G3's pinned sha256 `ee5375b6…b641aa` |
| PJM 2028/29 Planning-Parameters **XLSX** | "bot-walled, JS shell" | **HTTP 200, 39,244 bytes, real workbook.** Every number below comes from it |
| NYISO CY2026-27 parameters | "document-library URL not locatable" | **found and retrieved** — it is linked from the *Installed Capacity Market* page, not the demand-curve page |
| MISO 2026 PRA Results Posting | not attempted | **HTTP 403 `AccessDenied`** — while the 2023/2024/2025 postings on the *same CDN* return 200. One object's ACL |

So the environment was never uniformly bot-walled. **The lesson for future intake
sessions: re-probe a filed MANUAL-DOWNLOAD row before treating it as blocked, and
name the exact object that fails rather than the host.**

The narrative report's Table 3 *is* still an image — this session simply did not
need it. Rule-13 note: the report is cited only for values it states in prose
(the ER26-1556 cap/floor bullet); every tabulated number is from the workbook.

---

## 2. PJM 2028/2029 — the re-anchor (commit 1)

Published 2026-03-20, VRR curve added 2026-04-29, BRA cleared July 2026,
post-auction credit rates added 2026-07-27. Workbook committed locally at
`data/raw/capacity-market/demand-curve/pjm/pjm-2028-2029-planning-parameters.xlsx`
(sha256 `b1863615b0e366ab605aa26f3e9b84af4380ce924ec42c0c0b31a7a75557ca09`).

```
Net CONE (UCAP)   325.69 $/MW-day  = 118.877 $/kW-yr     (held anchor was 88.520)
Gross CONE        776.14 $/MW-day UCAP / 223,800 $/MW-yr ICAP
Fwd Net E&AS      450.448 $/MW-day UCAP    776.14 - 450.448 = 325.6919 -> 325.69
IRM 20.0 %   FPR 0.9401   Rel.Req. 156,012.885 MW   adj. for FRR 145,149.085 MW
VRR (a)-(d)  (146,703, 325.00) (147,326.3, 277.36) (149,736.8, 175.00) (153,858, 175.00)
```

**Three published discontinuities**, none of them a modelling choice:

1. **Level — a step, not a trend.** +34.3 %, and PJM says why: 2028/2029 is "the
   first year for the application of the new Periodic/Quad Review", whose gross-CONE
   values were FERC-approved 2026-01-21 in **ER26-455**. This is a re-basing onto
   new build-cost data. It is the single most important input to owner decision D-2
   (see §5).
2. **Shape — four points, not three, and a different denominator.** The report's own
   Summary: *"The VRR Curve equation has changed, impacting the prices used and point
   c of the VRR Curve."* The Manual-18 0.99/1.015/1.045 construction that the
   2026/27 and 2027/28 vintages carry does **not** apply. And the workbook publishes
   **no EE Addback row** — post-CIFP energy efficiency is netted inside the load
   forecast — so the VRR denominator is the FRR-adjusted requirement alone. PJM's own
   numbers confirm the denominator choice: points (b) and (d) land on **1.015000** and
   **1.060000 exactly**.
3. **A binding price FLOOR — the structural half.** FERC **ER26-1556** collars the
   curve at 325.00 / 175.00 $/MW-day UCAP (= the workbook's ICAP 256.75 / 138.25 ÷
   the 0.79 Reference Resource Accredited UCAP Factor). Points (c) and (d) sit *at*
   the floor, so **the curve never crosses zero** and `evaluate_demand_curve`'s
   flat-extrapolation carries the floor out to any position.

### 2.1 The floor supersedes FF-2C's PJM inertness finding

Measured directly through `MarketDesign.capacity_price_per_firm_mw_yr`
(deterministic, no LP), $/firm-MW-yr:

| reserve position | held 2027/2028 | new 2028/2029 | Δ |
|--:|--:|--:|--:|
| 0.95 | 121,706 | 118,625 | −2.5 % |
| 1.000 | 108,431 | 118,625 | +9.4 % |
| 1.015 | 88,520 | 101,236 | +14.4 % |
| 1.030 | 44,260 | 67,490 | +52.5 % |
| **1.05** | **0** | **63,875** | **∞** |
| **1.10** | **0** | **63,875** | **∞** |
| **1.20** | **0** | **63,875** | **∞** |

The mechanism matrix records PJM's capacity-curve flip as *"quantitatively inert —
position past the curve's zero-cross pays $0"*. The model's own PJM hindcast
positions sit at **1.100–1.196** (from `validate_capacity_prices` Pass 2) — i.e.
exactly in the region that used to pay zero. **From 2028 a long PJM firm MW earns
0.5373 × net-CONE = 63,875 $/MW-yr where it previously earned nothing**, before
the retirement screen's `× (1 − EFORd)` accreditation. That flows straight into
the step-3 economic-retirement screen and the step-5/6 entry screens.

That is a real, published market-design change (rule 1 `[R-STRUCT]`), not a
representation choice — but it is a *large* behavioural change riding in on a data
re-anchor, and it is flagged here rather than buried. The matrix cell has been
updated in this session (rule 28 duty b).

**Not measured in a solve, and deliberately so.** No PJM leg was run: the pack
requires FFR-2A and FFR-2B to coordinate their PJM windows explicitly (rule 12,
≤2 concurrent invocations, PJM/MISO legs never co-run) and this session could not
see their state. The numbers above are exact seam arithmetic, not estimates — but
**the fleet-level consequence of the floor is unmeasured, and a PJM T0 leg
(2026–2028) is the named next acceptance step.** It is the one piece of this
lane's evidence that is analytic rather than solved.

---

## 3. NYISO CY2026-2027 — the re-anchor (commit 2)

Second annual update of the 2025-2029 DCR, posted by the tariff deadline of
2025-11-30. Source: "Demand Curve Parameters CY 2026-2027"
(sha256 `713560dc6851e9d03e18c50c23c63520af8fe6ef67ad062c4e64700c981207cc`),
same one-pager layout and same representative zones as the committed 2025-2026
block, so the two years are directly comparable.

| NYCA (F-Capital) | 2025-2026 | 2026-2027 | Δ |
|---|--:|--:|--:|
| **Annual Reference Value** ($/kW-yr) | 50.55 | **57.70** | **+14.1 %** |
| Gross Cost of New Entry | 127.71 | 131.94 | +3.3 % |
| Net EAS Revenues | 77.15 | **74.24** | **−3.8 %** |
| Summer ref point / max clearing ($/kW-mo) | 5.72 / 21.69 | 6.53 / 22.41 | |
| Demand Curve Length | 12 % | 12 % | unchanged |

**Most of NYISO's move is a smaller E&AS offset, not construction cost** — the
opposite decomposition to PJM's. That single fact does more work in §5 than the
level does.

`gross_cone` rows are intaken for this vintage (they were not for earlier ones) so
the published E&AS offset a `reindex_gross` option would re-net is recoverable
from the file. No `irm` row: the ARV one-pager does not publish one and the NYSRC
study was not retrieved — left absent rather than carried forward from 24.4 %.

**Disclosure, and asserted by a test.** NYISO is deliberately absent from the
shipped `capacity_market_clearing_by_iso` map, so the pricing seam reads its
**fixed** `net_cone_per_kw_yr` and **this vintage changes no price in the shipped
posture**. It is landed for data currency and to make the FF-3D flip decidable on
current data. `test_nyiso_vintage_is_inert_while_its_clearing_gate_is_off` fails
if a future session adds NYISO to that map without arguing the flip.

---

## 4. MISO and NEISO — adjudicated, not guessed (commit 3)

Neither gets a vintage. Both backlog rows are closed as *decisions*, so no later
session repeats this work.

### 4.1 MISO PY2026-2027 — derivable, deliberately not encoded

FF-G3 estimated "N/C aggregate ≈ 81.0 $/kW-yr". It is now **proven** from published
values only, by two independent checks, both machine-checked by
`test_miso_py2026_27_aggregation_facts_are_pinned`:

1. **North/Central IS the LRZ 1-7 arithmetic mean.** On PY2025-26,
   mean(LRZ 1-7 gross CONE) = 127,361.43 $/MW-yr, and MISO's own published
   North/Central *seasonal* CONE annualizes to 1384.36 $/MW-day × 92 = 127,361.1 —
   agreement to **0.0003 %**.
2. **The E&AS offset is one value per Planning Area**, exactly as FERC Docket
   ER26-139-000 describes ("Net CONE values are sorted into values in the First
   Planning Area and Second Planning Area"). The on-disk PY2026-27 rows prove it
   arithmetically: gross − net is **identical at 52,735 $/MW-yr across all of
   LRZ 1-7** and **47,938 across LRZ 8/9/10**.

⇒ **N/C Net CONE PY2026-27 = 133,767.14 − 52,735 = 81,032.14 $/MW-yr = 81.03
$/kW-yr, +1.5 %** over the held 79.8. A derivation on MISO's own construction, not
an interpolation.

**Why it is still not encoded.** The shipped MISO vintage carries the seasonal RBDC
and the seam evaluates the seasonal grain — the market's own Σ ACP_season × days
settlement. An annual-only PY2026-27 vintage would silently drop MISO back to the
annual approximation RC-1C replaced: **a fidelity regression bought for a +1.5 %
level correction.** The PY2026-27 seasonal RBDC lives in the 2026 PRA Results
Posting, which 403s (§1). The seasonal caps *could* be reconstructed from the
days-identity — which reproduces PY2025-26 exactly — but that would be inventing
published numbers for a table whose shape may have changed. Refused under rule 13.

The old code comment's *reason* ("no N/C aggregate — rule 5") is superseded; the
refusal now stands on the seasonal-grain regression. **Blocked on one document;
whole stake 1.5 %.**

### 4.2 NEISO — no newer vintage exists

Not a retrieval gap. **FCA 18 (2027/2028), already on disk, is the last forward
capacity auction ISO-NE has ever held.** FCA 19 is delayed to February 2028 and the
FCM is being replaced by the prompt/seasonal design: CAR-PD accepted by FERC
2026-03-30 (ER26-925), **CAR-SA expected Q4 2026** with parameters unpublished. The
FCA-19 paper Net CONE (9.614 $/kW-mo = 115.37 $/kW-yr) clears no auction.

Consequence worth naming: **NEISO is the ISO where `hold_last` will do the most
work for the longest**, because there is no next vintage to re-anchor to. That makes
D1/D2 matter *more* for NEISO than for PJM/NYISO — the opposite of the intuition the
+34 % PJM headline creates.

---

## 5. The FF-G3 owner box, populated (D-3)

Written into `docs/handoffs/ff-g3-net-cone-forward-2026-07.md` §5. **No default
flipped; the shipped mode is still `hold_last` and every real rate is still 0.0.**

**The headline: D3 has largely been executed, and it dominates D1/D2.**

| ISO | held → re-anchored ($/kW-yr) | step | = years of +2 %/yr real |
|---|---|--:|--:|
| **PJM** | 88.52 → **118.88** | **+34.3 %** | **14.9 yr** |
| **NYISO** | 50.55 → **57.70** | **+14.1 %** | **6.7 yr** |
| MISO | 79.80 held | +1.5 % derivable, not taken | 0.8 yr |
| NEISO | 108.94 held | no newer vintage exists | — |

On a 2026–2050 horizon there are ~4 more PJM vintages and ~24 more NYISO annual
updates to come. **Keeping vintages current is worth more than any defensible
escalation rate, and needs no owner decision at all** — it is maintenance.

**Measured D1/D2 spread**, 2050 anchor by mode × real rate, on each ISO's
*re-anchored* base via `constants.forward_net_cone_anchor`. `reindex_gross` uses
each ISO's **published** gross−net offset (PJM 164.41, NYISO 74.24, MISO 47.56
$/kW-yr), not an illustration:

| ISO | leverage (g/n) | r | hold_last | reindex_net | reindex_gross | gross vs hold |
|---|--:|--:|--:|--:|--:|--:|
| PJM | 2.383 | 0 % | 118.88 | 118.88 | 118.88 | ±0 % |
| PJM | | 1 % | 118.88 | 147.97 | 188.20 | +58.3 % |
| PJM | | 2 % | 118.88 | 183.78 | 273.55 | **+130.1 %** |
| NYISO | 2.287 | 1 % | 57.70 | 73.26 | 93.29 | +61.7 % |
| NYISO | | 2 % | 57.70 | 92.81 | 137.98 | **+139.1 %** |
| MISO | 1.596 | 1 % | 79.80 | 102.34 | 115.77 | +45.1 % |
| MISO | | 2 % | 79.80 | 130.92 | 161.39 | **+102.2 %** |
| NEISO | n/a | 2 % | 108.94 | 171.79 | n/a | n/a |

NEISO's `reindex_gross` cell is **n/a because no FCA-18 gross CONE is on disk** —
not because the mode fails there. Do not fill it by inference.

**Recommendation on D2 (unchanged, now evidenced):** keep **0.0 real central**. The
new data confronts the finding and confirms it. PJM's +34.3 % is a *step* PJM itself
labels as a new cost basis; fitting a real rate to it extrapolates a one-time
re-basing across 23 years — precisely the error the 0.0-central finding exists to
prevent. NYISO cuts the same way from the other side: most of its move is a
**falling E&AS offset**, which no construction-cost index produces at all.

**D1** is inert until D2 chooses a non-zero rate (at r = 0.0 all three modes are
byte-identical to `hold_last`). Option (a) `reindex_gross` is now cheaper to adopt
than in July because the published offsets exist on disk for three of four ISOs.

**D5** gains a natural experiment that argues *for* the coupling — PJM's step is a
new-build capital-cost re-estimate propagating into the capacity anchor, which is
exactly what D5 proposes — but **the two ISOs decompose oppositely**, so if D5 is
taken it must couple the **gross** leg only and leave E&AS as its own driver. That
is also what `reindex_gross` does, making D5 and D1(a) the same decision seen from
two ends.

---

## 6. Verification

**T0 smoke — NEISO 2026-2028, before and after the re-anchors** (cold, shipped
posture, curve-ON for NEISO by default). Both legs solved 3/3.

- `cache_key` **identical** both legs: `9ff63395d1c39726`.
- All three `year_<yr>.parquet` are **content-identical** (`DataFrame.equals`,
  8760 × 12 each). Their raw bytes differ only in parquet writer metadata.
- Whole output tree compared: file sets identical (10 files); the *only* differing
  file is `full_horizon_summary.json`, and only in `run_dir` / `total_wall_s` /
  `global_peak_rss_mb` / `per_year_perf`.
- Invariants **unchanged**: 1 FAIL, 0 WARN on both legs — I12 reserve-margin band
  (2026 15.3 %, 2027 19.8 %, 2028 20.x % against band [0.2 %, 15.2 %]). **This
  FAIL pre-exists this session** and is untouched by it; it is not attributed here.

That is the intended result: NEISO's vintages were not touched, so a re-anchor of
PJM and NYISO must be exactly inert for it. Artefacts under `results/ffr2c/`.

**`validate_capacity_prices` (no LP), before and after.** Exactly **11 differing
leaves**, all of them one new row:

- **NYISO 2026/2027 appears and reconciles exactly** — `pub_net_cone_kw_yr` 57.70 ==
  `model_net_cone_kw_yr` 57.70; `pub_cap_frac` 3.4318529862174570 vs `model_cap_frac`
  3.4318529862174576; `shape_resid_pct` = 1.3 × 10⁻¹⁴. Marked `locked: True` by the
  script's rule-22 guard (delivery year ≥ 2026), so it is greyed and excluded from
  every verdict — correct, and it means the row is diagnostic only.
- **Zero PJM rows changed.** The re-anchor governs 2028+; every scored PJM delivery
  year is ≤ 2027/2028 and no auction-price row exists for 2028/2029. **This
  instrument structurally cannot see the PJM re-anchor** — stated plainly so the
  unchanged output is not read as evidence of inertness.

**Tests.** `tests/unit/model/test_capacity_demand_curve.py` (64), plus
`test_net_cone_forward.py`, `test_constants_facade.py`, `test_persisted_identity.py`,
`test_capacity.py`, `test_curate_capacity_market_demand_curve.py` — all green. Four
new tests: the PJM 2028/29 reconciliation, the PJM floor assertion, the NYISO
2026-27 reconciliation, the NYISO gate-inertness assertion, plus the MISO
fact-pinning test.

**Rules.** No `ScenarioConfig` field added, removed or re-defaulted, so
`PINNED_DEFAULT_CACHE_KEY` is unmoved (`603c2498bf71d21d`) and rule-28(c) has
nothing to enforce. Rule 28(b): the `capacity_market_clearing` note is corrected and
a new `net_cone_forward_vintages` row added; `check_mechanism_matrix.py` passes.
Rule 22: nothing touched an out-of-training year — the only solves were NEISO
forecast-mode 2026-2028. Rule 27: `capacity_market.py` (2,766 lines) was edited
locally with the Edit tool and pushed as on-disk bytes; blob-verified after push.
Nothing was registered on the backcast registry.

**Pre-existing REDs, not from this session** (verified by re-running against a
stashed tree): `tests/unit/config/test_reserve_config.py::TestErcotMultiProduct`
fails 3 tests on `origin/main`. That is a **third** red area beyond the two the
§W1-X close report names (§0c-6 lists `test_ff_readiness_battery` and
`test_outages`); flagged for whoever owns the fast tier.

---

## 7. Standing disclosures

Per `docs/forecast-readiness-peer-review-2026-07.md` §4:

1. **The PJM floor's fleet-level effect is unmeasured.** §2.1's numbers are exact
   seam arithmetic; no PJM solve was run (rule-12 window coordination). A PJM T0
   leg 2026-2028 is the named next acceptance step.
2. **The NYISO re-anchor is inert in the shipped posture** (its clearing gate is
   off). It changes a price only if FF-3D flips NYISO on.
3. **MISO carries a known +1.5 % stale anchor**, deliberately, pending one
   unretrievable document.
4. **NEISO's anchor is frozen indefinitely by market design**, not by staleness —
   and it is the ISO most exposed to whatever D1/D2 decide.
5. **The escalation machinery remains inert and untested in any solve.** All rates
   are 0.0; no run has ever armed a non-zero one.
6. The `validate_capacity_prices` instrument scores no delivery year ≥ 2026 (rule-22
   lock), so **neither re-anchor is covered by a scored verdict** anywhere today.

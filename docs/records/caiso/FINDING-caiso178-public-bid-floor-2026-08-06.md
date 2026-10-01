# FINDING — caiso-178: the OASIS `PUB_DAM_GRP` corpus is landed, and it does NOT identify `battery_dispatch_adder`. The wall is HIGHER, not lower.

**Outcome: BRANCH II of the pre-registered verdict rule — a SHARPER WALL.** The DOF is **not
closed**; `battery_dispatch_adder = 5.0` stays exactly as it is.

**NO LP, NO SOLVE, no arm, no bundle, nothing registered — because nothing was run.** DOF ledger
unchanged at `n_entries` 11 / `n_residual` 8. Keeper unchanged at
`2026-08-06-caiso-175-tac-intake`. `holdout-freeze.json` and `calibration-complete.json`
UNTOUCHED. 2023–2025 only.

Pre-registration: `PRECHECK-caiso178-public-bids-2026-08-06.md` (pushed **before** any bid price
was read).
Instrument: `scripts/data/derive_caiso_battery_bid_floor.py`.
Record: `_caiso178_public_bid_floor.json`, `_caiso178_bid_floor_resources.csv`,
`_caiso178_bid_floor_hist.csv`.

---

## 0. Headline

**BRANCH II fires by THREE INDEPENDENT ROUTES**, any one of which is sufficient: the classifier
is **PROVISIONAL** not VALIDATED (H1a missed), the H1c sensitivity grid is **NOT ROBUST**, and
the mass-point test — the only route to an identification — **fails decisively**.

Three things, in the order they were found.

1. **The corpus is real, complete, and the classifier works.** 1,095 of 1,096 trade dates,
   **2,589,238 storage curve-hours**. A **price-blind** classifier reproduces CAISO's *own
   published* IFM|LESR bucket distribution to **0.595 / 1.118 / 1.483 pp** mean absolute
   deviation. Two entirely independent CAISO publications agree — so neither the corpus nor the
   classifier is the limitation.
2. **And it still does not identify.** The modal first discharge rung is **\$1,000/MWh — the
   CAISO soft bid cap** — in **all three years**, at 7.7 / 18.5 / 16.5 % of resource-hours
   (14.3 / 30.6 / 28.1 % resource-weighted). **81–90 % of first discharge rungs sit above \$15.**
   There is no cost-like point mass at any price. The finer grain resolved the price to the cent
   and found no parameter there.
3. **WHY it does not identify is the actual result, and it closes the exit rather than narrowing
   it.** The discharge bid encodes **WHEN the battery intends to run, not WHAT it costs to run**:
   the cheap-bid mass concentrates in the evening ramp (h17–21 PT, peaking **1.89 / 1.59 / 1.57 ×**
   at h19) and is depleted overnight and through the solar belly, while the rest of the fleet
   holds at the bid cap. **caiso-176's exit 2 — "a finer public bid-price grain … the single
   highest-value exit" — is now SPENT and CLOSED.** No later session need re-spend it.

---

## 1. TASK 1 — the intake, and its coverage reported honestly

| | requested | present | missing | parse errors |
|---|---:|---:|---:|---:|
| 2023 | 365 | **364** | 1 | 0 |
| 2024 | 366 | **366** | 0 | 0 |
| 2025 | 365 | **365** | 0 | 0 |

**The single hole is `2023-06-01`, and it is a genuine OASIS archive gap, not a fetch failure** —
the API answers with an `ERR_CODE 1000` "No data returned" XML *inside a valid zip*, which the
committed fetcher detects and distinguishes from a rate-limit page. **Zero rate-limit failures
and zero retries** across 1,096 requests at the 6 s spacing. 422 MB on disk.

**No cap, no sample and no top-N truncation was applied anywhere in the derivation** (rule 15,
no silent caps). Every classifier stage's survivor count is in the committed record.

**Committed:** the deriver and its three derived artifacts. **Not committed:** the daily zips —
gitignored at `.gitignore:86` by the `pjm-energy-offers` precedent the intake README cites.

### 1a. A scaling defect found in passing, MEASURED not asserted

`scripts/data/curate_dam_public_bids.py` **cannot process a full CAISO year in this environment.**
Measured: 141 days → 12,915,667 rows at **5.51 GB peak RSS** in 65 s. A 365-day year extrapolates
to **~14.3 GB** against ~15 GB total RAM, because `_curate_spec` holds every day-frame and
`pd.concat`s them at once. This session's deriver **streams** day-by-day and never materialises a
year, so nothing here depends on it. **Filed, not fixed** — `clean_io.write_clean` is a frozen
shared seam and re-engineering it for all six ISOs is not a calibration session's call.

---

## 2. The classifier, and how it actually scored

**It is PRICE-BLIND by construction** — `resource_type`, `product`, the MW-axis sign and
symmetry, and hour counts. No price enters any stage, so every price-side result below is an
**out-of-construction** test of it.

### 2a. What the corpus turned out to contain

77 / 121 / 167 battery-like resources; **every one bids a perfectly symmetric range**
(`sym` = 1.0). The largest is 325 MW and **no resource exceeds 400 MW**, so **CAISO's pumped
storage never enters the set at all** — Helms does not bid a withdrawal-capable NGR curve. The
S4 pumped-storage exclusion was therefore aimed at a contaminant that is not present; its effect
on the statistic is inside the H1c grid and is negligible (2023 \$15.21 → \$15.91; 2024/2025
unchanged). Only **one** resource (6 MW) was caught by the symmetry filter, so hybrid
contamination is not material either.

### 2b. H1b — PASS, and it is the strong result

The price-blind classifier against CAISO's **own published IFM|LESR** discharge shares:

| | MAD (pp) | lowest ≥1 % bucket, ours | published | match |
|---|---:|---|---|---|
| 2023 | **0.595** | `(0,15]` | `(0,15]` | ✓ |
| 2024 | **1.118** | `(0,15]` | `(0,15]` | ✓ |
| 2025 | **1.483** | `(-15,0]` | `(0,15]` | ✗ |

Threshold was ≤ 5.0 pp and ≥ 2-of-3 bucket matches. **PASS.** Like-for-like on the bucket that
matters, `(0,15]` priced-volume share: **ours 7.65 / 12.87 / 14.86 %** against **published
8.72 / 16.43 / 17.52 %**.

**Two independent CAISO publications, built by different pipelines from different files, agree
to 1.1–3.6 pp.** That mutually validates caiso-176's instrument, this session's corpus, and the
classifier joining them.

### 2c. H1a — MISS on 2025, and the miss is MY pre-registration's error, disclosed not repaired

| | classified bid-in MW | vs p95 **dispatch envelope** (the gate) | vs measured **fleet capacity** |
|---|---:|---|---|
| 2023 | 4,804.2 | 4,256.5 → **1.129** ok | 7,492.4 → 0.641 |
| 2024 | 7,962.0 | 6,914.6 → **1.151** ok | 11,131.3 → 0.715 |
| 2025 | 12,209.9 | 9,550.3 → **1.278 MISS** | 15,448.4 → 0.790 |

Growth ordering reproduced. The gate needed ±25 % in **all three** years; 2025 overshoots the
tolerance by **2.2 %**. **PASS = False.**

**The pre-registration compared the wrong two objects** — this session's *bid-in capability*
against caiso-174's measured *p95 dispatch envelope*. Those are different quantities; the
comparable one is the measured *fleet capacity*, against which the classified set reads
0.641 / 0.715 / 0.790 and sits sensibly **between** the two published references, exactly where
DAM-bidding NGR capability should sit. **The gate is reported as it fired and was NOT rewritten
to pass**; the fleet ratio is emitted as a field no verdict branch reads. Under the
pre-registration a PROVISIONAL classifier "may report a **bound only**, never an identification",
which is what happens below — so nothing turns on this.

### 2d. H1c — NOT ROBUST

Headline spread across the sensitivity grid: **0.696 / 3.675 / 3.070** against a ≤ \$1.00
requirement. 2024/2025 fail, driven by the `sym ≥ 0.7` variant (\$6.00 → \$9.675 / \$8.57).
**PASS = False.** The headline is not stable to plausible misclassification.

---

## 3. The mass-point test — the ONLY route to an identification — FAILS

| | n resource-hours | modal first rung | share | resource-weighted mode | share |
|---|---:|---:|---:|---:|---:|
| 2023 | 528,161 | **\$1,000.00** | 7.72 % | \$1,000.00 | 14.29 % |
| 2024 | 854,560 | **\$1,000.00** | 18.47 % | \$1,000.00 | 30.58 % |
| 2025 | 1,206,517 | **\$1,000.00** | 16.54 % | \$1,000.00 | 28.14 % |

The pre-registered gate required a ≥ 20 % mass at a **single \$0.25 bin > \$0 and ≤ \$15**, stable
within \$1.00 across years and surviving resource-equal weighting. What the data shows instead is
a mass at the **soft bid cap**, growing with the fleet: **the modal battery-hour offers even its
FIRST MWh at \$1,000.** `share_p_hi > $15` = **89.5 / 81.3 / 81.6 %**.

This is caiso-176 §3a and ERCOT-162 confirmed at full resolution: *a submitted offer is an
EQUILIBRIUM object.* caiso-176 could only see it in the stack's upper rungs; here it is visible
in the **first** rung.

---

## 4. WHY it cannot identify — the discharge bid encodes DISPATCH INTENT, not cost

Ratio of the ≤ \$15 first-rung share to the all-hours share, by CAISO local hour — **the same
shape in all three years**:

| hour PT | 0–4 | 6 | 9–15 | 17 | 18 | **19** | 20 | 21 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | 0.66–0.77 | 1.18 | 0.81–0.87 | 1.31 | 1.68 | **1.89** | 1.73 | 1.45 |
| 2024 | 0.69–0.78 | 1.17 | 0.85–0.88 | 1.22 | 1.41 | **1.59** | 1.58 | 1.43 |
| 2025 | 0.70–0.90 | 1.22 | 0.88–0.91 | 1.15 | 1.37 | **1.57** | 1.49 | 1.33 |

The cheap bids are **concentrated in the evening net-load ramp** and a secondary morning-ramp
bump at h6, and **depleted overnight and through the solar belly**. A marginal cost does not have
an hour-of-day shape. A **dispatch intention** does: the resource bids low in the hours it means
to run and at the cap in the hours it means to hold.

**That is why no grain of bid data can identify this parameter.** The published quantity is not a
noisy measurement of throughput cost; it is a different object.

---

## 5. REPORTED AGAINST INTEREST — caiso-176's one-sided premise does not strictly hold for storage

caiso-176's bound rests on *"a rational participant does not offer energy below its own marginal
cost."* That premise is sound for a thermal generator. **For storage it fails**, because the
shadow value of stored energy can be **negative** — a battery that must make room to charge on
the solar belly will pay to discharge. The corpus shows this directly:

| | first rungs ≤ \$0 | per-resource ANNUAL MIN first rung, p10 | p25 |
|---|---:|---:|---:|
| 2023 | 1.11 % | −\$28.09 | \$0.01 |
| 2024 | 3.41 % | −\$148.00 | −\$7.39 |
| 2025 | 3.79 % | −\$121.66 | −\$32.22 |

A quarter of the 2025 fleet offers to discharge at **−\$32/MWh or below** at some point in the
year. Under a strict marginal-cost reading those resources would have negative marginal cost,
which is false; they are managing state of charge.

**What this does and does not do to caiso-176.** It does **not** touch its measurement — this
session reproduces its bucket shares to ~1.5 pp from a different file. It does **not** overturn
its conclusion — "bounds but does not identify; the parameter stays at 5.0" — which this session
reaches independently and more strongly. What it qualifies is the **inference**: *≤ \$15* is a
statement about **revealed conduct**, not a strict upper bound on marginal cost, because bids
below cost are demonstrably present. The net effect is that the wall is **higher**: the "bounds"
half is weaker than stated and the "does not identify" half is now conclusive.

---

## 6. The \$6.00 near-coincidence — REPORTED AND REFUSED

The pre-registered floor statistic lands at **\$15.91 / \$6.00 / \$6.00**, and `$5.00` is among
the top-5 modal bins in every year (2.20 / 2.76 / 5.19 %). \$6.00 and \$5.00 are close to the
incumbent 5.0. **This is not confirmation of anything, and it is recorded here so that no later
session mistakes it for confirmation.** Four reasons, any one sufficient:

1. **It is not stable.** \$15.91 → \$6.00 → \$6.00 is a **\$9.91** three-year spread against the
   pre-registered \$1.00 stability requirement. A quantity that moves \$10 between adjacent years
   is not a technology parameter.
2. **It is not robust.** H1c moves it to \$9.675 / \$8.57 at `sym ≥ 0.7`.
3. **It is not the identifying statistic.** The pre-registration made the *mass-point test* the
   sole route to BRANCH I, and that test fails at the bid cap.
4. **Round-number bid conventions generate it.** \$0.01, \$5, \$6 and \$1,000 are all prominent
   bins; a clustering at round numbers is a bidding habit, not a cost measurement.

Adopting \$6.00 here would be **exactly** the caiso-176 DO-NOT-REDO item — "a value picked from
inside (0,15] **because** it sits inside the bound is a fitted value wearing measured clothing" —
made more seductive, not less, by landing near the incumbent.

---

## 7. THE WALL — restated, higher, with its exits re-scored

> **CAISO publishes no instrument that identifies a scalar battery discharge throughput cost, and
> the bid-data channel is now CLOSED at every grain.** The market-design object exists and is
> precisely defined — CAISO's Storage Default Energy Bid carries a cycle-cost component in \$/MWh
> — but its values are submitted per-resource from manufacturer documentation, i.e. confidential
> and never published. **The public substitute fails for a structural reason, not a resolution
> one:** a storage discharge bid is a dispatch-intent object whose hour-of-day shape and cap-mass
> are visible at full resolution, and whose relation to marginal cost is not even one-sided,
> because the shadow value of stored energy can be negative.

**Re-check cost:** `uv run python scripts/data/derive_caiso_battery_bid_floor.py`, ~7 minutes over
the corpus, no network. Re-fetching the corpus is ~2 h.

**caiso-176's three named exits, re-scored:**

| exit | status after caiso-178 |
|---|---|
| 1. Per-resource Storage-DEB cycle-cost (`CD`) filings | **UNCHANGED — the primary wall.** Confidential by tariff construction; a disclosure wall, not a fetch task. |
| 2. A finer public bid-price grain (`PUB_DAM_GRP`) | **SPENT AND CLOSED.** Corpus landed, derived, and it does not identify — for a structural reason that no finer grain repairs. |
| 3. An identified cell-vs-system split replacing `STORAGE_DEGRADATION_REPLACEMENT_FRACTION = 0.25` | **UNCHANGED, and now the ONLY live exit.** Still bounded by §5's qualification of the ≤ \$15 reading. |

---

## 8. DO-NOT-REDO — caiso-176's list carried forward, plus this session's

Carried unchanged: any value **> \$15**; `caiso_storage_as_reservation` as this parameter's
replacement; routing the LP through `_degradation_cost_per_mwh` (**DOF substitution**, imports a
declared-tunable fraction); the bid stack's **upper rungs** or the **hybrid** panel as a cost
curve; and **picking a value inside (0,15] because it sits inside the bound**.

**Added here:**

* **Re-fetching or re-deriving `PUB_DAM_GRP` to identify this parameter.** Done, at full
  coverage; the answer is structural. New evidence would have to be a *different object*, not
  more of this one.
* **Adopting \$6.00, \$5.00, or any modal bin of the first-discharge-rung distribution** as a
  measured throughput cost (§6).
* **Reading the first discharge rung as a marginal cost at all** (§4) — it carries an hour-of-day
  shape and an 8–20 % mass at the bid cap.
* **Treating caiso-176's ≤ \$15 as a strict upper bound on marginal cost** (§5). It is a
  revealed-conduct statement.

---

## 9. Governance

* **Rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]`** — no price residual was read at any point. Every
  gate is a property of published bid data, and no model output entered the derivation.
* **Rule 14 `[R-ACCURATE]`** — not reached. No input was swapped, so there is no accurate-input
  regression to defend.
* **Rule 15** — **nothing to register.** No run was produced, so no bundle, no sidecar, no
  dashboard entry. Same disposition as caiso-176.
* **Rule 20 `[R-DOF]`** — the ledger entry stays `identification: residual`, count unchanged at
  11 / 8. Its `root_cause` text is now known to be unachievable as written *and* its remaining
  route is narrowed to exit 3; recorded here rather than silently edited, because the ledger is
  the keeper's attestation and rewriting it needs the keeper's own lane.
* **Rule 22** — 2023–2025 only. The freeze and both markers are untouched. **No authorization was
  needed or taken**: the training window is not gated, and under the 2026-08-06 owner
  clarification data intake is not window-gated at all.
* **Rule 25 `[R-ISO-SCOPE]`** — nothing transferred. ERCOT-162 is cited as *prior argument about
  what a bid is*; every number here is CAISO's own.
* **Rule 27 `[R-PUSH]`** — Opus. Every push touching a file ≥ 300 lines was blob-verified
  immediately (deriver 705 lines, sha256 match; pre-registration 325 lines, sha256 match).
* **Rule 28 duty (b) + (e)** — the `battery_dispatch_adder` cell and the §5.2 header are updated
  in this same session, including the stale-marker correction below.

### 9a. A state correction landed this session

The §5.2 header and this session's own handoff both asserted CAISO **holds** `complete`. **It does
not.** `calibration-complete.json` carries CAISO under **`withdrawn`** (declared 2026-08-05,
withdrawn 2026-08-06, owner directive on the rubric-v3.1 amendment, because a marker cannot rest
on a NOT-YET keeper). Nothing was ever spent under it; the locked test was never authorized.
Corrected in the matrix under rule 28 duty (e). It constrained nothing here — the freeze already
restricted this session to 2023–2025.

---

## 10. Known-open, carried forward

1. **The N–S congestion majority** — the model reproduces 5.2 / 2.4 / 2.9 % of the measured
   NP15−ZP26 basis. Named; no lever chartered; the N–S topology lever stays **FORBIDDEN**
   (caiso-164 §0/§6).
2. **C3a is an OPEN root-cause issue** (2024 +11.7 %, 2025 +14.8 %), not an accepted limitation.
   Its driver is the model's unrestrained pumped-storage pumping (FINDING-caiso140 §B) and its
   closure route is the **walled** hourly PS water state — an owner-level data question, not a
   session lever. `caiso_ps_charge_shape_anchor` stays `G`; that refusal rests on the input being
   walled, so rubric v3.1 does not reopen it.
3. **ESCALATED TO THE OWNER — the CAISO outage re-audit is still outstanding.** CAISO's 2023–2025
   outage windows were regenerated on the current CAMPD detector (`intake_log` 2026-07-24) and the
   re-audit that entry flagged **has still not been done**. It is a **precondition for spending
   2022**, and with CAISO's `complete` marker now withdrawn it is also on the path back to any
   re-declaration. This session did not touch it.

**With this session's lever spent, CAISO's in-model lever queue remains EMPTY and its one FAIL
remains walled.** The next CAISO calibration move is an owner-level data question, not a session
lever — stated plainly rather than dressed up as a queue entry.

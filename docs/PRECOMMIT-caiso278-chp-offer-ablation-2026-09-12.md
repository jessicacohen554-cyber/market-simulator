# PRECOMMIT — caiso-278: ABLATION SCREEN on `caiso_offer_surface_measured_ungrounded`. A DIAGNOSTIC that names or clears the carrier of CAISO's +0.534 MMBtu/MWh bias. It is NOT promotable in either direction.

> ## STATUS: **STAGED, NOT EXECUTED. NO LP WAS SPENT, NO SHARD WAS LAUNCHED.**
> This charter was written, and the session stopped at the owner's instruction before the
> launch. Nothing here has been solved: there is no arm bundle, no screen result, and no
> gate has a measured value. **§1's five pre-solve kills and §3's footprint table ARE
> measured and stand on their own** — they are the session's real product and they are why
> this charter exists. Everything from §2 onward is a plan awaiting a go/no-go, and §5 states
> in advance that the arm **cannot be promoted in either direction**, so the decision is
> whether ~20 min of LP is worth pure diagnostic information. Do not read this document as a
> record of a run.

**Session caiso-278, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). Written BEFORE any
solve; the shard prompt would pin this doc's own commit SHA (rule 32 `[R-SHARD]` (c) 1).**
Keeper / control: `2026-09-12-caiso-275-gascoupling`, folded 2022 rung bundle
`results/calibration/caiso275_B_gascoupling_2022`.

---

## §1 — WHY AN ABLATION, AND WHY IT IS THE ONLY LP THE EVIDENCE JUSTIFIES

caiso-277 established the object: CAISO carries a **+0.534 MMBtu/MWh** implied-marginal-heat-rate
bias on the common 2023–2025 window (t = +4.03, 75 % of months positive, **sd 0.794 — the lowest
of all seven ISOs**), while ERCOT (−0.625, t = −2.54) and PJM (−0.717, t = −2.87) run
significantly NEGATIVE and four ISOs are indistinguishable from zero. Six ISOs run the same
ISO-agnostic LP and none carries it. **So the carrier is something CAISO has that they do not, and
it is small and systematic rather than noisy.**

**Five candidate carriers have now been killed pre-solve, each on its own measurement**, and
they are recorded so this session is not re-run:

| candidate | verdict | measured basis |
|---|---|---|
| `caiso_import_hub_prices` matcher "bug" | **NOT A BUG** | `run_calibration.py:5021` gates the whole branch on `legacy_intertie`; its own comment reads "Superseded by the per-hub node; gated to the legacy pooled topology only." The raw `startswith(WECC_import_)` matcher is consistent with its gate. **caiso-275 §4.5's "a real code defect" is itself mistaken**, and the per-hub node already prices each corridor at its own measured hub. |
| the static import ladder ($28/$36/$48/$68/$110/$180) | **wrong baseline** | Measured-vs-ladder deltas are large and BOTH-signed (2022 PNW_midC **+55.38**, WECC_scarcity **−91.05**), but the ladder is not what is live — `caiso_per_hub_intertie` (armed) already reprices per corridor. |
| border carbon | **CORRECT** | `resolve_carbon_price` returns $28.45 / $33.03 / $35.23 / $28.06 per tonne → a **$12.18 / $14.14 / $15.08 / $12.01 per MWh** border adder. No defect. |
| `caiso_asymmetric_path_ratings` | **ALREADY ARMED** (cell **K**) | True on the keeper; the published WECC Path 15 / Path 26 directional ratings are already in. |
| CHP heat rates (the 37 `not_unfired_topping` CT_CHP plants) | **WRONG-SIGNED, and excluded for cause** | `model_over_measured` p50 **0.697**, and **> 1 in 0 of 37**: the model *under*-charges them against eGRID's CHPCHTI add-back. Their derive excludes the add-back because `thermal_share` is 0.513–0.864 against `_MAX_THERMAL_SHARE = 0.50`, so the add-back is an upper bound, not the right rate. Correcting them raises price. |

**There is no admissible unarmed CAISO lever left** — consistent with caiso-261's standing
declaration that the in-model lever queue measured empty at caiso-200. What remains is to **name
the carrier**, and the only instrument that can is an ablation: turn one armed CAISO-distinctive
mechanism off and measure whether the bias moves.

## §2 — THE ARM: ONE FLAG OFF, NOTHING ELSE

    replay_keeper.py results/calibration/caiso275_B_gascoupling_2022 \
      --out-dir results/calibration/caiso278_ablate_ungrounded_2022 \
      --years 2022 \
      --set caiso_offer_surface_measured_ungrounded=false

`caiso_offer_surface_measured_ungrounded` (armed on the keeper) **merges CAISO's measured CC /
CT band multipliers onto `CC_CHP`, `CT_CHP` and `ST_GAS`** — the three classes with no measured
band set of their own. It is the CAISO-distinctive that governs the largest marginal carrier in
the biased window: caiso-276 §5c measured **`CT_CHP` at 28.8 %** of the shoulder window's marginal
load-weight (`econc00` 17.87 % + `econc01` 10.95 %) and 16.6 % over all 8,760 hours.

**Zero new fields, zero new thresholds, zero derive re-runs, one existing registered flag flipped
OFF.** G-CTRL **form 4**: the committed 2022 rung IS the control; **no control solve is spent.**

## §3 — THE SCREEN YEAR IS 2022, CHOSEN ON THE MECHANISM'S OWN FOOTPRINT

Footprint = dispatched energy of the three classes the merge governs × that year's measured
delivered gas (`iso_monthly_gas_prices`), computed from the committed `class_hourly` sidecars
**before this solve exists and with no reference to the price residual** (rule 29 `[R-SCREEN]`
step 1, rule 1 `[R-STRUCT]`):

| year | CT_CHP TWh | CC_CHP TWh | ST_GAS TWh | total TWh | gas $/MMBtu | **footprint $M** |
|---|--:|--:|--:|--:|--:|--:|
| **2022** | 1.308 | 8.932 | 0.332 | **10.571** | 9.94 | **105.05** |
| 2023 | 1.243 | 8.469 | 0.080 | 9.792 | 9.01 | 88.27 |
| 2025 | 1.204 | 7.550 | 0.013 | 8.767 | 4.70 | 41.24 |
| 2024 | 1.236 | 7.517 | 0.082 | 8.835 | 4.31 | 38.06 |

**2022 ranks first**, and rule 29 says the screen year *is* the largest-footprint year. Stated
against the choice, because it invites an obvious objection: **2022 is also the year with the
failing C3a**, so the selection could be misread as residual-driven. It is not — the ranking is a
pure energy × gas product and 2023 is within 16 % of it. Two things keep this honest: the basis is
recorded here before the solve, and **§4's gates do not read C3a at all.** (2023 would have been
the more conservative pick and is named here as the alternate had the rule permitted it.)

## §4 — PRE-REGISTERED STOP GATES. They can KILL the diagnostic; none can promote anything.

| gate | requirement | what a failure means |
|---|---|---|
| **G-IDENT** | The arm's `run_config.json` differs from the control's in **exactly one** field, `caiso_offer_surface_measured_ungrounded` (True → False). | A second moved field voids the run; re-solve or discard. |
| **G-FOOT** | Every offer-price change is confined to `CC_CHP` / `CT_CHP` / `ST_GAS` rows. `CC_REGULAR` and `CT_PEAKER` `mc` rows **byte-identical** to the control. | The flag is reaching classes it does not govern — a code defect, reported not absorbed. |
| **G-LIVE** | The three governed classes' offer multipliers must actually MOVE: ≥ 1 of the 3 classes shows a non-zero band-multiplier delta, and ≥ 500 h carry \|Δprice\| > $0.50. | **INERT** ⇒ the ablation cannot discriminate and the cell is recorded `I`, not `R`. |
| **G-DIR** | Removing the merge leaves the three classes on their generic fallback, so their offers move in a **stated, bounded** direction; the realised \|Δ system price\| must not exceed the offer move implied by their marginal weight (≈ 29 % of shoulder weight). | An overshoot means the response is not the mechanism's own arithmetic. |
| **G-COLLAT** | No load-bearing criterion (C1/C2/C3b) flips PASS → FAIL in 2022 for a reason other than the three governed classes' volumes. | Collateral damage is reported at full magnitude. |

**There is deliberately NO gate on C3a, and no gate whose satisfaction promotes the arm.** The
diagnostic reads the *dHR* attribution: does the +0.534-signature bias move when the merge is
removed? Either answer is a result.

## §5 — WHY THIS CAN NEVER BE PROMOTED, IN EITHER DIRECTION

Stated up front so no later session mistakes it for a candidate:

* **If the bias MOVES**, the carrier is named — but the ablation itself is **not the fix**. Removing
  a *measured* offer surface and reverting CHP/ST_GAS to a generic fallback is reverting to an
  estimate, which rule 14 `[R-ACCURATE]` forbids outright. The fix would be a **measured** CHP /
  ST_GAS band set, and CT_CHP's is **structurally un-derivable** from CAISO's OASIS bids (masked
  ids; the CT bucket already contains priced CT_CHP — caiso-276 §6). So a positive result opens a
  data-procurement question, not a flag flip.
* **If the bias does NOT move**, the largest marginal carrier is CLEARED and the search moves to
  the remaining CAISO distinctives (the per-hub intertie's two signed corridors, the 24.06 TWh of
  forced firm-import energy, the four-tranche DSW clean-depth family, the solar-belly scale).

Either way the keeper is **unchanged** and the bundle is a **throwaway screen** — never registered,
never a keeper, never quoted as a keeper number (rule 29 `[R-SCREEN]` (2) and (c)).

## §6 — RETENTION AND HYGIENE

* **Rule 29 (c) / rule 31 `[R-RETAIN]`:** the screen bundle is **gitignored, never committed, and
  never `rm`'d.** `.gitignore` alone discharges delete-before-merge; the ercot-255 incident is why
  nothing is deleted. Every number this session will cite appears in the RESULT doc.
* **Rule 32 `[R-SHARD]`:** one shard = one year = ≤ 20 min. The parent spends **zero LP** and does
  phase 0, this PRECOMMIT, the launch, then the composition and scoring.
* **The shard is FORBIDDEN**, by name, from: `git add -A` / `git add .`; `dashboard_add_run.py`,
  `build_manifest.py`, `build_status.py`, `prune_iso_runs.py`, anything under
  `frontend/data/backcast/**`; any edit under `src/` or `scripts/`; opening a PR; deleting any
  result. **A shard that stops with a clear report is a SUCCESS; a shard that repairs
  infrastructure is a FAILURE.**
* **Container:** run the runner unmodified, never pass `--no-container-preflight`, and report the
  `container preflight:` and `memory peak:` log lines (rule 32 (c) 8).
* **Setup:** `pip install -r requirements.txt` plus `openpyxl`, and `PYTHONPATH=.:src` before
  `scripts/data/curate_capacity_deliverability.py --isos CAISO` (the caiso-275 shard-death gap).

## §7 — WHAT THE SHARD MUST REPORT, IN NUMBERS

1. `git rev-parse HEAD` (must equal the pinned SHA) and the `container preflight:` / `memory peak:`
   lines.
2. From its own `run_config.json`: the value of `caiso_offer_surface_measured_ungrounded` and the
   count of fields differing from the control (G-IDENT).
3. Annual load-weighted price, and CT_CHP / CC_CHP / ST_GAS / CC_REGULAR / CT_PEAKER dispatched TWh.
4. Hours with \|Δprice\| > $0.50 against the control (G-LIVE), and the max \|Δprice\|.
5. `slack` and `dump` totals.
6. That it committed **only** its own bundle path, and `git status --short` showing nothing outside it.

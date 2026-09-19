# RESULT — ERCOT keeper re-solved for the marginal emission rate. MER DELIVERED; **G-DRIFT FORM 4 IS REFUTED FOR ERCOT AT HEAD**.

**Session:** ercot-mer (parent/orchestrator), 2026-09-19. Branch `claude/ercot-keeper-configs-60kit8`.
**PRECOMMIT:** `docs/handoffs/PRECOMMIT-ercot-mer-keeper-resolve-2026-09-19.md` (`f5575e05`, Amendment 1 `fa87a45a`).
**Pinned SHA:** `5926ca52e9acf140cdab1221464bc13be4938f32` (contains the MER commit `2ec09663` and the replay fix).
**Keeper under test:** `2026-09-09-ercot265-receipts-fallback`, bundle `results/calibration/ercot265_receipts_five_year`, years 2021-2025.
**Not a keeper candidate; nothing registered.** No dashboard id minted, keeper bundle untouched (append, "WHEN IT LANDS").

---

## Headline

1. **The marginal emission rate is delivered for all five ERCOT years.** Present, non-zero, and the dual
   **did not OOM** at per-plant ERCOT scale — the memory question the owner's append flagged as genuinely
   unvalidated is now answered in practice.
2. **The ERCOT keeper NO LONGER REPRODUCES AT HEAD.** 2025 is byte-exact; 2021, 2022, 2024 and especially
   **2023 (+6.0%)** have drifted. Sealed prediction **P4 is TRIGGERED**: this is reported at full
   magnitude and the lane **STOPS** — no config was hunted to restore the old numbers (rule 1 `[R-STRUCT]`).
3. **Rule 29 `[R-SCREEN]` (b) form 4 — "the committed keeper IS the control" — is REFUTED for ERCOT at
   HEAD** on four of five years. Any ERCOT lane differencing an arm against the committed keeper right
   now is differencing against a control that no longer reproduces.
4. A separate defect was found and fixed on the way in: **the keeper had been unreplayable on every year
   since 2026-09-10.**

## The drift, measured

P1, load-weighted by `demand`, 7 zones x 8760 h. Demand inputs verified **byte-identical** on every year.

| year | leg | replay lw | keeper lw | Δ | Δ% | zone-hours differing | max ΔP |
|---|---|---:|---:|---:|---:|---:|---:|
| 2021 | carve-out A | 175.4846 | 174.8514 | **+0.6332** | +0.362% | 38,247 / 61,320 | 788.70 |
| 2022 | carve-out A | 68.6817 | 68.3962 | **+0.2855** | +0.417% | 36,531 / 61,320 | 134.11 |
| 2023 | carve-out B | 63.7242 | 60.1182 | **+3.6060** | +5.998% | 24,824 / 61,320 | 1609.01 |
| 2024 | forward | 31.0197 | 30.8901 | **+0.1296** | +0.419% | 17,449 / 61,320 | 310.28 |
| 2025 | forward | 33.8052 | 33.8052 | **-0.0000** | -0.000% | 0 / 61,320 | 0.00 |


Slack rises where it was non-zero and appears where it was zero (2021 2,274.9 -> 2,658.5 MWh;
2024 600.2 -> 694.3; **2023 0.0 -> 171.7**); dump stays 0.0 everywhere.

### Where the drift lives: a CLASSIFICATION shift, not a dispatch one

Total system generation is identical to ~1e-6. What moves is a reallocation *between classes*:

| year | dominant moves (MWh, share of total) |
|---|---|
| 2021 | CC_CHP −313,946 (−0.080%) ↔ CC_REGULAR +310,360 (+0.079%); CT_CHP −106,650; ST_GAS +100,745 |
| 2022 | CC_CHP −280,080 (−0.065%) ↔ CC_REGULAR +252,408 (+0.059%); CT_CHP −108,046 |
| 2023 | CC_REGULAR +110,192 ↔ CT_PEAKER −107,612; CT_CHP −102,182; ST_GAS +42,136 |
| 2024 | CT_PEAKER −111,573 ↔ ST_GAS +61,226 / CC_REGULAR +54,528; CT_CHP −32,592 |
| 2025 | **every class identical to 1e-7 of total** |

**CC_CHP ↔ CC_REGULAR and CT_CHP ↔ everything else is a plant→class mapping change**, not the LP
choosing differently. The energy magnitudes are small (<0.1%); the PRICE consequence is not, because
these classes carry different offer curves.

### Leading candidate — A HYPOTHESIS, NOT A CONCLUSION. NOT BISECTED.

25 non-merge commits touch the ERCOT backcast path between the keeper's `git_sha` (`6bc43501`) and the
pinned SHA. The one that best fits the *shape* of the evidence is
**`760012f7` "Key the EIA-860 vintage-sensitive caches on the active directory (SPP-38 card A)"**:
EIA-860 vintage drives plant attributes including CHP designation, and vintage sensitivity falls off
toward the present — which matches **2025 exact → 2024 partial (28% of zone-hours) → 2021/2022 broad
(62%/60%)**. 2023's magnitude does not fit that gradient as neatly and may be a second effect.

**This was not bisected and must not be cited as the cause.** P4 says report and stop; naming a suspect
is reporting, confirming it is the next lane's work. Other candidates in range: `666343a2` (NWPP coal
taxonomy), `a05347a8`/`1100c052`/`f2191f5d` (SOCO/NWPP registry registration), `eaa9d6f1`/`ee40acd2`
(LP memory hygiene — should be numerically inert, worth ruling out first because that is cheap).

### Two causes RULED OUT, by measurement

* **NOT the `replay_keeper` fix.** The receipts fallback fires only in 2021 months 2 and 12.
  Replay Feb-2021 = **$1,691.7** against the keeper's **$1,690.9**; had the routing failed it would read
  ~$1,422.13 (the pre-fallback incumbent). It armed. Drift is spread across all twelve months of 2021,
  and 2022/2023/2024 moved too, where the fallback never fires.
* **NOT the MER dual.** 2025 is bit-exact on all 61,320 zone-hours. A post-solve, zero-iteration
  re-pricing that perturbed a basis would not spare exactly one year. This is consistent with the dual's
  design (`model/lp/model.py::_marginal_emission_rate`: basis frozen, iteration limit 0, basis restored).

### What is NOT claimed

**No re-score.** The parent has no `data/raw` (code profile), so `calibration_verdict.py` cannot run here
and **no C1/C2/C3a/C3b/C4/C8 verdict is computed or implied**. 2023's +6.0% is large relative to the
keeper's registered C3a of −7.3% and a re-score would plainly move, but *how* is not asserted. Scoring
these bundles needs an ERCOT-profile container.

## The marginal emission rate (the deliverable)

tCO2/MWh, P1 rows, all zone-hours, load-weighted by `demand`:

| year | lw mean | p10 | median | p90 | share at 0.0 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 0.5497 | 0.3809 | 0.4591 | 0.9763 | 5.61% | -0.0000 | 1.2352 |
| 2022 | 0.5254 | 0.3830 | 0.4389 | 0.7404 | 5.92% | -0.0000 | 1.2659 |
| 2023 | 0.5974 | 0.3843 | 0.5434 | 1.0834 | 5.59% | -0.0000 | 1.3194 |
| 2024 | 0.5961 | 0.3789 | 0.5511 | 1.0589 | 6.80% | -7.7000 | 2.0622 |
| 2025 | 0.5369 | 0.3789 | 0.4779 | 0.7824 | 8.60% | -0.0000 | 1.3570 |

Read these as HEAD-consistent MER series, **not** as the keeper's MER: four of the five solves they come
from no longer reproduce the keeper (above). 2025's series is the one that is also the keeper's.

**One anomaly, reported not explained:** 2024 carries a minimum of **−7.7000** tCO2/MWh, far outside the
other four years (all ≈ −0.0000). A negative marginal rate is physically meaningful — a marginal MWh can
displace a dirtier unit through congestion or storage — but a −7.7 outlier against a p10 of 0.379
deserves a look before anyone builds a marginal-abatement curve on 2024.

## Bundles — paths and FULL IMMUTABLE RECOVERY SHAs (rule 33 `[R-SHARD-ARCHIVE]` (d))

Every bundle was **pushed** (rule 34 `[R-SHARD-PROMOTABLE]` (a)) and carries `dispatch/<year>_P1.parquet`,
so a promotion needs **zero re-solves**. 18 files each, ~150 MB each.

| year | bundle path | recovery |
|---|---|---|
| 2021 | `results/calibration/ercot_mer20260919_2021` | `git checkout e702b98b57cd4027f2bb9f74ca96c179fbb04ee3 -- <path>` |
| 2022 | `results/calibration/ercot_mer20260919_2022` | `git checkout b66fd8a49c8895163f6757080c0f0be52ffd6973 -- <path>` |
| 2023 | `results/calibration/ercot_mer20260919_2023` | `git checkout 78422a377d62b73f30cbf98914c215f54ad33c58 -- <path>` |
| 2024 | `results/calibration/ercot_mer20260919_2024` | `git checkout 9ab2461485a9feeb4a9cf191c2216056955e54c6 -- <path>` |
| 2025 | `results/calibration/ercot_mer20260919_2025` | `git checkout a6429ae94eef82079f349a2a75b93a7f257778b5 -- <path>` |

Rule 34(d) verified on all five: `git ls-tree -r <sha> -- <path>` returns 18 files, not zero.
Rule 32(d): the per-year dirs are kept OUT of `main` by `.gitignore`, never by `rm` (rule 31
`[R-RETAIN]`). They are also on the parent's local disk, which does **not** survive container reclamation.

## Governance

* **All five v2 shards pushed real bundles.** Config signature verified per leg: 2021/2022 `swcap=true`
  `ep_ref=true` 151.008/433.95; **2023 `swcap=true` `ep_ref=FALSE`** 151.008/433.95; 2024/2025
  `swcap=false` `ep_ref=true` 4.576/13.15; `receipts_fallback=true` and `netload_drag_layup_window_mask=true`
  on all five. The ercot-259 wrong-config replay defect did not recur.
* **Rule 32 `[R-SHARD]` (b) was set aside on direct owner instruction** ("launch one shard per year then
  compile"), recorded in PRECOMMIT Amendment 1. The failure mode that ban exists for — unrecoverable legs —
  was closed by rule 34(a) full-bundle pushes, and the five legs were in fact all recovered.
* **A first attempt (v1) burned zero LP.** All five v1 shards stopped correctly at a driver blocker,
  filed findings, pushed nothing. `docs/handoffs/FINDING-ercot-mer-replay-blocked-2026-09-19.md`.
* **Rule 27 `[R-PUSH]`:** `scripts/replay_keeper.py` (1,048 lines) was edited locally by Opus in the
  parent and the pushed blob verified byte-identical (sha256 match) before anything else proceeded.
* **Rule 31 `[R-RETAIN]`: nothing deleted**, and the promotion question is put below rather than pre-empted.

## THE PROMOTION QUESTION — OWNER DECISION NEEDED

These five bundles are a **HEAD-consistent re-solve of the keeper's own recipe**, not a new configuration:
no mechanism changed, no parameter was tuned, and the config signatures match the keeper leg-for-leg. On
that basis they are **not a keeper candidate in my judgement** — but rule 31 exists precisely because that
judgement is not mine to act on, so nothing has been deleted and the question is yours:

1. **Register nothing** (my recommendation). The MER data is delivered and cited here; the drift is a
   finding routed to whoever owns the engine bisect. Cost: the bundles eventually vanish with the
   containers, and re-solving is ~15 min/year.
2. **Promote them as the ERCOT keeper's new bundles.** They are internally consistent and at HEAD — but
   this would silently move ERCOT's published C3a/C3b **without a re-score**, and 2023 in particular would
   move a lot. I would want the re-score first, in an ERCOT-profile container, and the drift root-caused
   before publishing numbers whose cause is unknown.
3. **Bisect first.** ~25 candidate commits; the cheap ones (`eaa9d6f1`/`ee40acd2` LP memory hygiene,
   which should be numerically inert) can be ruled out at low cost, and `760012f7` tested directly.

**Whatever you decide, the drift finding stands on its own and is the more important half of this run:**
an ERCOT arm differenced against the committed keeper today is differenced against an invalid control.

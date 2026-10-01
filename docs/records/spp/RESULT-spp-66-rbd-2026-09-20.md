# RESULT — SPP-66 R-bd. The net-load commitment-floor window is **REJECTED**. It moves its own structural target the WRONG WAY, in all seven years.

**Lane** SPP-66 · **Mechanism** `commitment_floor_window_netload` (shared gate, owner ruling
"Shared gate" 2026-09-20) · **Pin** `17a8a14c7e10fe6f9e0db7101a587c54d4fc11a8` · **Control** keeper
13's / the rung's **committed** bundles, differenced, never re-solved (rule 29(b) form 4, validated
by the G-DRIFT measurement in `ADDENDUM-spp-66-shared-gate-implemented-2026-09-20.md` §3a) ·
**Seven shards, one per year 2019-2025**, all pinned, all pushed complete bundles.

**THIS LANE'S RECOMMENDATION: DO NOT PROMOTE.** `frontend/data/backcast/keepers/SPP.json` is
UNTOUCHED and no run was registered (rule 31 `[R-RETAIN]` — the recommendation is a sentence in this
doc, never an action).

---

## 1. THE VERDICT, on the criterion the card was written for

R-bd existed to raise the model's coal floor in the **lowest net-load hours**, where the model sheds
coal the real fleet holds. The pre-registered target statistic was **p1/max of hourly coal MW**.

| year | control p1/max | **ARM p1/max** | ACTUAL p1/max | direction |
|---|---|---|---|---|
| 2019 | 13.83 % | **13.76 %** | 23.98 % | flat |
| 2020 | 7.84 % | **5.07 %** | 16.94 % | **AWAY** |
| 2021 | 5.77 % | **3.21 %** | 15.21 % | **AWAY** |
| 2022 | 5.15 % | **2.24 %** | 15.30 % | **AWAY** |
| 2023 | 5.24 % | **1.72 %** | 11.47 % | **AWAY** |
| 2024 | 5.70 % | **1.78 %** | 16.01 % | **AWAY** |
| 2025 | 4.50 % | **0.83 %** | 16.38 % | **AWAY** |

**The gap to reality roughly TRIPLES in six of seven years.** `min/max` tells the same story
(2023 1.49 % → 0.18 %, 2024 1.00 % → 0.18 %). This is not a marginal miss; it is the target moving
backwards.

## 2. WHY — and the reason is worth more than the mechanism was

The rule-17 driver evidence was **right**: SPP coal really does track net load (+0.948/+0.948/+0.932)
far better than system load (+0.716/+0.661/+0.613). Phase 0 was not wrong about that.

**The inference from it was wrong.** A commitment floor's job at the bottom of the distribution is
not *"be where the class runs most"* — it is *"stop the class collapsing where it would otherwise go
to zero."* Ranking the top-k window on net load concentrates the floor in the high-net-load hours
where coal is **already economic and already running**, so the floor becomes redundant exactly where
it binds, and **releases the genuinely low hours entirely**. That is precisely the shape of the
result: the top of the distribution is untouched and the bottom falls out.

So the card's diagnosis and the card's remedy came apart. **The window's DRIVER and the floor's
PURPOSE are different questions**, and phase 0 measured only the first. A successor that wants the
bottom-decile coal floor must target the floor's *level or coverage at the bottom*, not re-rank its
window — and must not re-open this cell expecting a different answer from the same lever.

## 3. MY PRE-REGISTERED PREDICTIONS, SCORED HONESTLY

From `PRECOMMIT-spp-66-rbd-netload-window-2026-09-20.md` §5, written before any solve:

| # | prediction | outcome | verdict |
|---|---|---|---|
| 1 | coal annual TWh **UP**, < +1.5 TWh/yr | **DOWN every year** (COAL_PRB −0.118 to −0.315) | **WRONG on sign** |
| 2 | bottom net-load-decile coal **UP substantially** toward measured | **DOWN**, gap ~tripled | **WRONG on sign — the decisive one** |
| 3 | `corr(coal, net load)` **UP** toward measured | up **+0.001 to +0.003** (0.925→0.926) vs a 0.03-0.06 gap | technically right, **trivially so** |
| 4 | top net-load decile ~unchanged | unchanged | RIGHT |
| 5 | CT_PEAKER / CC_REGULAR down slightly, ST_GAS ~flat | all \|Δ\| ≤ 0.114 TWh | RIGHT |
| 6 | C3a **DOWN** slightly | **UP** +0.002 to +0.623 $/MWh, on a model already too dear | **WRONG on sign** |
| 7 | C3b shape risk of getting worse | CV falls every year (0.544→0.462 in 2023) — flatter, i.e. worse | RIGHT (adverse) |

**Three of seven wrong on sign, including the one the card lives or dies by.** Prediction 2 was the
mechanism's whole thesis. Scoring this honestly is the point of pre-registering it.

## 4. THE GATES — reported at full magnitude, and NOT the reason for the verdict

| year | ΔCOAL_PRB | ΔCOAL_LIG | ΔCC_REG | ΔCT_PEAK | ΔST_GAS | Δwind | ΔC3a simple $/MWh | ΔC3a LW |
|---|---|---|---|---|---|---|---|---|
| 2019 | −0.287 | +0.103 | +0.212 | −0.085 | +0.015 | +0.000 | +0.002 | +0.002 |
| 2020 | −0.118 | −0.024 | +0.129 | −0.052 | −0.041 | +0.109 | +0.354 | +0.354 |
| 2021 | −0.246 | −0.010 | −0.026 | −0.022 | +0.001 | +0.299 | +0.445 | +0.445 |
| 2022 | −0.315 | −0.034 | −0.041 | −0.036 | +0.037 | +0.385 | +0.383 | +0.382 |
| 2023 | −0.307 | −0.066 | +0.058 | −0.059 | −0.030 | +0.387 | +0.623 | +0.623 |
| 2024 | −0.169 | −0.054 | +0.112 | −0.024 | −0.114 | +0.242 | +0.379 | +0.379 |
| 2025 | −0.162 | −0.086 | +0.037 | −0.040 | −0.059 | +0.280 | +0.590 | +0.589 |

Every class delta is **< 0.4 TWh**, so no C1 row changes status — but every one that moves, moves
**adversely**: coal down and wind **up** on an ISO already carrying a **+10.144 TWh wind excess**,
and price up on a model already too dear. **The owner's standing test — "structural integrity
improves but gates regress may still be a keeper" — is NOT met**, because the structural leg is the
one that fails. Had structure improved and only these gates moved, the answer would be different;
that is not this result.

## 5. Retrievability and retention (rules 31 / 33 / 34)

All seven shards pushed **complete** bundles — 16 files each, `dispatch/<y>_P1.parquet` included,
`git ls-tree` verified > 0 before any archiving. Config signature verified per year **before**
archiving: gate armed `True` in all seven; `coal_sync_srmc_tranche` / `coal_mustrun_online_pmin` /
`st_gas_mustrun_per_plant` all `True`; `offer_curve_by_group` uniform 0.93 and **untouched**; and
trap (n) held — `mid_vintage_exit_carry` `True` on 2019-2022 (rung) and `False` on 2023-2025 (span),
so the two config families never mixed. All seven shard sessions are archived (rule 33(e)).

The bundles are on **local disk and `.gitignore`d** — kept out of `main` (rule 29(c)) and **not
deleted** (rule 31). **They will not survive this container.** Leg SHAs are recorded in the
`.gitignore` comment as *provenance only*: per rule 33(d) a shard branch is transport, not storage,
so **any recovery must be costed as a re-solve** (~5 min per year, ~35 min for the span).

**THE PROMOTION QUESTION, ASKED EXPLICITLY (rule 31):** this lane recommends **against** promotion on
§1. The owner routinely promotes what a lane declines; if that is the ruling here, say so **before
this session ends**, because the bundles die with the container and re-creating them costs ~35 min of
LP.

## 6. What survives

The **gate itself is sound, default-off, and already on `main`** — measured byte-identical off (all
19 committed configs re-key identically; 0 solve-surface values moved; every LP input identical at
both pins). Nothing needs reverting. It stays available, unarmed, for a successor with a better
hypothesis about *what* to window — and this document is the evidence that re-ranking the existing
window is not it.

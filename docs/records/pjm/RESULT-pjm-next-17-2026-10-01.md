# RESULT — PJM-NEXT-17: COAL_BIT located, own-offer audit falsified, CC conduct window refused (zero LP)

**Keeper unchanged:** `2026-09-30-pjm-next16-ovec` (bundle `pjmnext16_A_span`). Run-level, training tier 2023–2025 and ISO (v3.13) all read **NOT-YET**. Same 10 failing cells.

**Records:** `docs/records/pjm/FINDING-pjm-next-17-coal-response-and-cc-conduct-window-2026-10-01.md`, `docs/records/pjm/PRECOMMIT-pjm-next-17-2026-10-01.md` (arm C, refused before launch, §6).

**Solves:** none. No shard was launched; nothing was registered or pruned.

| card | outcome | owner card |
|---|---|---|
| 1. COAL_BIT plant-hour census | Located: 80–100 % LOAD (synced units loaded higher), in the **econ bands**; floor bands flat; diffuse over ~30 plants, every month and demand tercile, ⅔ daytime; within-day coal displaces CC (r −0.19 to −0.45). No admissible, year-discriminating lever. **OPEN.** | — |
| 1b. Dispatch vs own offers (PJM offers corpus 84/84 months) | **Falsified as the lever.** Relative to the model, real units do not under-run their own offers more in the over-run years (RoR 1.00–1.24 vs 1.12–1.18 in 2023/24). The biggest term is the model's **price level** in hours under $25 (+13 to +47 TWh at PJM's own offers): the NEXT-11 price-floor object, which is large in 2023/24 too. | "Dispatch-vs-offer audit" |
| 2. CC plant-conduct window (`cc_mustrun_conduct_window`) | Built, default off. The census promised a small cut. The **real-fleet zero-LP check reverses it**: the offline-hour floor **rises** 8–19 % (2019/2021/2023/2025), because outage windows already zero most real off-hours. **Refused before solve**; matrix cell **R**. | "Design + build" → "Build + solve anyway" → "Refuse; keep built, off" |
| 3. Design card | Not reached (no admissible, year-discriminating, zero-DOF mechanism). | — |

**Rule-17 question on `cc_mustrun_per_plant`, now sized:**
- 2.8–4.5 TWh/yr of floor sits in non-outage short off-runs, about 2 % of CC floor energy.
- No calendar-cell window can reach it without the same-year meter (rule 13).
- Cell stays **K**.

**Next (owner card "Both, sequenced"):**
1. The low-price-hour price floor: the NEXT-14 marginal-unit census across all seven years, via year-isolated diagnostic replays with `unit_hourly`. It is the shared root of C3a 2019/2020, the COAL_BIT price-level term and the CT_PEAKER 2021 swap.
2. Then CC_REGULAR 2023, the training-span blocker (+8.48 vs ±8.00).

**Retrievability (rule 34(e)):** no bundles were produced. The zero-LP outputs are committed: `results/calibration/_pjmnext17_*.json`.

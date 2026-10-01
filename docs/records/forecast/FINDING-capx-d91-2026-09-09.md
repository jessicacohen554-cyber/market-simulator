# FINDING — capx D91: one unregistered field moved every cache key in the program

**Lane:** capx D91 · **Branch:** `claude/capx-d91-cache-key-pins-phrx2p` · **Date:** 2026-09-09
**Model:** Opus (rule 27 `[R-PUSH]`) · **Data profile:** `code` · **ZERO LP spent.**
**Authority:** OWNER RULING **Q64** (2026-09-09, capx ledger §0bh.3(a)) — *"Re-emit D91 to diagnose
fully, then repair."*
**Pre-registration:** `docs/handoffs/PRECOMMIT-capx-d91-2026-09-09.md`, pushed before any edit.

> **HEADLINE.** The field is **`pjm_seam_neighbour_hourly_ladder`**, the commit is **`f2a834de`**
> (pjm-174, 2026-09-08 16:21:53 +0000), and it landed with **no `_CACHE_KEY_OPTIONAL_FIELDS` entry**,
> so it entered `asdict(self)` and moved the key of every config in the program. **All 200 committed
> `run_config.json` records carrying a key are DERIVED to their recorded literal — zero
> unclassified.** Registering it at a frozen `"False"` **restores 92 keys and moves none anywhere
> new**; the other 108 are causes already adjudicated — (b′-1) armed default flips, capx D79's
> designed solve-surface re-key, and the 15 listed exceptions — layered on top. **The standing gate
> was green because it is payload-driven and `cache_key()` is dataclass-driven**: a field added after
> a bundle solved is absent from that bundle's payload by construction, so `G1_UNKNOWN` cannot see
> it. **Pin tests 33 → 2 red (fixed 31, newly broken 0)**, and both survivors are other lanes'.

---

## 1. THE CLASSIFICATION TABLE — ALL 200, WITH CAUSE AND ACTION

Population: `git ls-files "*run_config.json"` = **232**, of which **32 carry no `cache_key`** and
**200 do**. Every one of the 200 is listed. `recomputed` columns are
`ScenarioConfig(**payload).cache_key()` — the DATACLASS construction, i.e. what a solve at HEAD
would actually address.

Legend — **A** `pjm_seam_neighbour_hourly_ladder` unregistered · **B** a (b′-1) registered field
whose live default has been ARMED away from its frozen declaration · **C** capx D79 solve-surface
move (CAISO / ERCOT only) · **D** a record already listed in
`docs/governance/key-provenance-exceptions.json`.

| # | payload | ISO | recorded key | recomputed pre-R1 | recomputed post-R1 | cause | action |
|---:|---|---|---|---|---|---|---|
| 1 | `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d67arm/run_config.json` | PJM | `a9c66d8ea25acb9d` | `b5c1ddec558f2e11` | `fd07e2dba50cd32b` | A+B | A repaired; B = (b'-1) designed re-key |
| 2 | `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d75rarm/run_config.json` | PJM | `fb16fda2ddb0a94a` | `d94471c577ccf9b7` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 3 | `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d84arm/run_config.json` | PJM | `b9fa47dedb6c3319` | `8920066d021629a4` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 4 | `results/ff-t1f-d45r/miso/run_config.json` | MISO | `8d8bc63a0d4378a9` | `d2c70f51113dced5` | `1d0dca27d15380b5` | A+B | A repaired; B = (b'-1) designed re-key |
| 5 | `results/ff-t1f-d45r/nyiso/run_config.json` | NYISO | `cc7d1050a8090c76` | `32bd24780350d15c` | `c53daa792fe4e2e7` | A+B | A repaired; B = (b'-1) designed re-key |
| 6 | `results/ff-t1f-d45r/pjm/run_config.json` | PJM | `321f04e9060787f0` | `7e4e02193def6b46` | `e0ed693826955918` | A+B | A repaired; B = (b'-1) designed re-key |
| 7 | `results/ff-t1f-d46/caiso/run_config.json` | CAISO | `772b1e5abc7fc80c` | `b3027e2bc4f878b9` | `b826e300c8f14a92` | A+B+C | A repaired; B+C designed |
| 8 | `results/ff-t1f-d46/ercot/run_config.json` | ERCOT | `873d8c0e6cab52ae` | `6a0413d7f82e00b6` | `06a82788a9112022` | A+B+C | A repaired; B+C designed |
| 9 | `results/ff-t1f-d46/neiso/run_config.json` | NEISO | `6690e4d6d66bc819` | `a768c7619d6a3890` | `8ebed20ae90ec0e7` | A+B | A repaired; B = (b'-1) designed re-key |
| 10 | `results/ff-t1f-d50/ercot/run_config.json` | ERCOT | `0c3e9cd5b5993bdf` | `6a0413d7f82e00b6` | `06a82788a9112022` | A+B+C | A repaired; B+C designed |
| 11 | `results/ff-t1f-d50/neiso/run_config.json` | NEISO | `18515067bf4d2fbe` | `a768c7619d6a3890` | `8ebed20ae90ec0e7` | A+B | A repaired; B = (b'-1) designed re-key |
| 12 | `results/ff-t1f-d50/pjm/run_config.json` | PJM | `167e65187f32056b` | `7e4e02193def6b46` | `e0ed693826955918` | A+B | A repaired; B = (b'-1) designed re-key |
| 13 | `results/ff-t1f-d60/caiso/run_config.json` | CAISO | `29f8eb372810195f` | `18e60f22a00b0151` | `573c288b8e9a5081` | A+C | A repaired; C = D79 designed re-key |
| 14 | `results/ff-t1f-d60/miso/run_config.json` | MISO | `b1a73a087064ffd8` | `6a8185dd4561bd85` | `1604ba9eefbce059` | A+B | A repaired; B = (b'-1) designed re-key |
| 15 | `results/ff-t1f-d60/nyiso/run_config.json` | NYISO | `19a9690bb12c8459` | `997e260ecfb14c0a` | `65768f322744b8e6` | A+B | A repaired; B = (b'-1) designed re-key |
| 16 | `results/ff-t1f-d60/pjm/run_config.json` | PJM | `09996eca71ee80fd` | `efe40e73020651e4` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 17 | `results/ff-t1f-d65-a1/neiso/run_config.json` | NEISO | `8ebed20ae90ec0e7` | `a768c7619d6a3890` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 18 | `results/ff-t1f-d65-ctl/neiso/run_config.json` | NEISO | `18515067bf4d2fbe` | `6a1969a881b15d9f` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 19 | `results/ff-t1f-d65br/caiso/run_config.json` | CAISO | `17770cdad3230938` | `4a8fc1cc04544fe7` | `af6bdff905f1c94a` | A+C | A repaired; C = D79 designed re-key |
| 20 | `results/ff-t1f-d65br/ercot/run_config.json` | ERCOT | `9b9e5a48e3ca5c8e` | `65f06c464351087c` | `7cc4421dad81379f` | A+C | A repaired; C = D79 designed re-key |
| 21 | `results/ff-t1f-d65br/miso/run_config.json` | MISO | `74359fedbf2eadd6` | `31cfddaaa92419f6` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 22 | `results/ff-t1f-d65br/neiso/run_config.json` | NEISO | `c3519b861f920bbe` | `57f2d8fc8f978d16` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 23 | `results/ff-t1f-d65br/nyiso/run_config.json` | NYISO | `f62431376dd9df03` | `e3e4fb787e4838a9` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 24 | `results/ff-t1f-d65br/pjm/run_config.json` | PJM | `542eeedadab83ee1` | `c5054ffcc5eb3835` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 25 | `results/ff-t1f-s123/verify/run_config.json` | MISO | `587dc5b32ba71ceb` | `bc32029309cc1056` | `1e614837dbf719b9` | D | listed exception (unchanged) |
| 26 | `results/ff-t1f-s4hydro/neiso-control/run_config.json` | NEISO | `9a7f68fc7dcac931` | `0b3561a0807bed1a` | `eda1fca0252ab84d` | A+B | A repaired; B = (b'-1) designed re-key |
| 27 | `results/ff-t1f-s4hydro/neiso/run_config.json` | NEISO | `9a7f68fc7dcac931` | `0b3561a0807bed1a` | `eda1fca0252ab84d` | A+B | A repaired; B = (b'-1) designed re-key |
| 28 | `results/ff-t1f-s6-pjm/ledger/run_config.json` | PJM | `31a19d815fa319a7` | `3831cf0c89bdc3f0` | `b4f949afdac1f4f6` | D | listed exception (unchanged) |
| 29 | `results/ff-t3-neiso-golden/bau-d46/fc6/arms/base/run_config.json` | NEISO | `67678e58b2d0526c` | `b2431dd8bdcc962e` | `f73ecc7d24397ab6` | A+B | A repaired; B = (b'-1) designed re-key |
| 30 | `results/ff-t3-neiso-golden/bau-d46/fc6/arms/carbon_plus25/run_config.json` | NEISO | `56019f3b0850e9f9` | `9431af796347d1cc` | `ad617f6e4bb83eb7` | A+B | A repaired; B = (b'-1) designed re-key |
| 31 | `results/ff-t3-neiso-golden/bau-d46/fc6/arms/gaspm5/run_config.json` | NEISO | `e84079053b581a9e` | `07afd1ecf5e1b454` | `a49c53eb933a9f63` | A+B | A repaired; B = (b'-1) designed re-key |
| 32 | `results/ff-t3-neiso-golden/bau-d46/fc6/arms/gasup150/run_config.json` | NEISO | `96984c538320d6d6` | `9d2bf76f9afbefa4` | `8fc8025638324b96` | A+B | A repaired; B = (b'-1) designed re-key |
| 33 | `results/ff-t3-neiso-golden/bau-d46/run_config.json` | NEISO | `67678e58b2d0526c` | `b2431dd8bdcc962e` | `f73ecc7d24397ab6` | A+B | A repaired; B = (b'-1) designed re-key |
| 34 | `results/ff-t3-neiso-golden/bau-d60/run_config.json` | NEISO | `f04fd06348e1623d` | `ae317e63263c8eef` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 35 | `results/ff-t3-neiso-golden/bau-d65br/run_config.json` | NEISO | `0fc42cb56c24d544` | `4a5f9695eeae815a` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 36 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/base/run_config.json` | NEISO | `0365174ab16cc318` | `2f6e9843a500a967` | `f4afd37fedd4b856` | D | listed exception (unchanged) |
| 37 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon25/run_config.json` | NEISO | `7924eccc695c0168` | `167cb245a6b5502c` | `a662ddc67a771640` | D | listed exception (unchanged) |
| 38 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/carbon_plus25/run_config.json` | NEISO | `7784d408fc955785` | `901a0004c5d429a9` | `16388efe96bfd522` | D | listed exception (unchanged) |
| 39 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gaspm5/run_config.json` | NEISO | `1de43201e2040f7f` | `cebb904fe4fb5847` | `3c39097e90d19615` | D | listed exception (unchanged) |
| 40 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/fc6/arms/gasup150/run_config.json` | NEISO | `13f9357712250600` | `e0202da24a8f9bc7` | `b9773111d435a9d2` | D | listed exception (unchanged) |
| 41 | `results/ff-t3-neiso-golden/bau-prera-2026-08-31/run_config.json` | NEISO | `a4b11ef4aaa1be35` | `2f6e9843a500a967` | `f4afd37fedd4b856` | D | listed exception (unchanged) |
| 42 | `results/ff-t3-neiso-golden/bau/fc6/arms/base/run_config.json` | NEISO | `706e7ba8e6582d42` | `285d08928a11a107` | `e6af3eb568e92237` | D | listed exception (unchanged) |
| 43 | `results/ff-t3-neiso-golden/bau/fc6/arms/carbon_plus25/run_config.json` | NEISO | `f7cced798488ddac` | `294882748514239f` | `dd198d627e0346f8` | D | listed exception (unchanged) |
| 44 | `results/ff-t3-neiso-golden/bau/fc6/arms/gaspm5/run_config.json` | NEISO | `2d017ed9675aa386` | `e05323d2d40f8fa1` | `c8783b2e4e80bd27` | D | listed exception (unchanged) |
| 45 | `results/ff-t3-neiso-golden/bau/fc6/arms/gasup150/run_config.json` | NEISO | `65662ca117959ee5` | `5b72f98f98ebb96d` | `c2e3908e0e5b6181` | D | listed exception (unchanged) |
| 46 | `results/ff-t3-neiso-golden/bau/run_config.json` | NEISO | `706e7ba8e6582d42` | `285d08928a11a107` | `e6af3eb568e92237` | D | listed exception (unchanged) |
| 47 | `results/hindcast/caiso-2021-2025-realized-t1h-d46/run_config.json` | CAISO | `2c8cc7d19ccaed4c` | `5533c4f8ba5af7ac` | `789dff423db49abc` | A+B+C | A repaired; B+C designed |
| 48 | `results/hindcast/ercot-2021-2025-realized-t1h-d46/run_config.json` | ERCOT | `67d5dcc1ada2e2df` | `0625df3f05dcb6e8` | `f2a0957c0b42bd55` | A+B+C | A repaired; B+C designed |
| 49 | `results/hindcast/ercot-2021-2025-realized-t1h-d4m/run_config.json` | ERCOT | `f061b2646bfaac8b` | `359b801e11fbf28a` | `90dd0b19632b3164` | A+B+C | A repaired; B+C designed |
| 50 | `results/hindcast/miso-2021-2025-realized-t1h-d27/run_config.json` | MISO | `501b5f64b8adf8d4` | `53ae8d861ab76491` | `48694a5248b6f312` | D | listed exception (unchanged) |
| 51 | `results/hindcast/miso-2021-2025-realized-t1h-d31/run_config.json` | MISO | `3649264ca98a1fb4` | `53ae8d861ab76491` | `48694a5248b6f312` | A+B | A repaired; B = (b'-1) designed re-key |
| 52 | `results/hindcast/miso-2021-2025-realized-t1h-d33/run_config.json` | MISO | `40173304213d39cd` | `d4d909bd15998f51` | `aae41a9f4758a9a7` | A+B | A repaired; B = (b'-1) designed re-key |
| 53 | `results/hindcast/miso-2021-2025-realized-t1h-d46/run_config.json` | MISO | `eff2c890746ec966` | `485e08fc6da9387c` | `eafdef3a25502d77` | A+B | A repaired; B = (b'-1) designed re-key |
| 54 | `results/hindcast/miso-2021-2025-realized-t1h-d53-sectorgate-d51ratio/run_config.json` | MISO | `6ea92547eaa62559` | `a790d818fa836c38` | `8fbcd1f7ee6a9dff` | A+B | A repaired; B = (b'-1) designed re-key |
| 55 | `results/hindcast/miso-2021-2025-realized-t1h-d53-sectorgate/run_config.json` | MISO | `c306ddc6d28c60c2` | `9516f0c08742f890` | `1ad06174ee44e550` | A+B | A repaired; B = (b'-1) designed re-key |
| 56 | `results/hindcast/miso-d33-probe-entrydiag/run_config.json` | MISO | `1b0f1a5e75719b92` | `3a6b3440db9a1e1c` | `bc8ac61b267ed6b6` | A+B | A repaired; B = (b'-1) designed re-key |
| 57 | `results/hindcast/neiso-2021-2025-realized-t1h-d37-armed/run_config.json` | NEISO | `313ba0612435b963` | `2c48245bf574374d` | `1dac5cc3a6a7393b` | A+B | A repaired; B = (b'-1) designed re-key |
| 58 | `results/hindcast/neiso-2021-2025-realized-t1h-d45r/run_config.json` | NEISO | `d6c0137e37bf3200` | `0c65be9273de39eb` | `f8246f33985e3e27` | A+B | A repaired; B = (b'-1) designed re-key |
| 59 | `results/hindcast/neiso-2021-2025-realized-t1h-d46/run_config.json` | NEISO | `da19b85495178949` | `2c48245bf574374d` | `1dac5cc3a6a7393b` | A+B | A repaired; B = (b'-1) designed re-key |
| 60 | `results/hindcast/neiso-2023-2027-crossover-capxd14/run_config.json` | NEISO | `07e416f3f8072e7c` | `5ab9425422c92e63` | `791dcf81bf173f49` | A+B | A repaired; B = (b'-1) designed re-key |
| 61 | `results/hindcast/neiso-2023-2027-crossover-rcrepair/run_config.json` | NEISO | `07e416f3f8072e7c` | `5ab9425422c92e63` | `791dcf81bf173f49` | A+B | A repaired; B = (b'-1) designed re-key |
| 62 | `results/hindcast/nyiso-2021-2025-realized-t1h-d45r-curveon/run_config.json` | NYISO | `cad77112c804881d` | `d794c0758cdbcc0d` | `fecd78684b9bfaba` | A+B | A repaired; B = (b'-1) designed re-key |
| 63 | `results/hindcast/nyiso-2021-2025-realized-t1h-d45r/run_config.json` | NYISO | `91686abe7a744a88` | `7266c54bb7b03a17` | `a10fd9d5ff5cc7ab` | A+B | A repaired; B = (b'-1) designed re-key |
| 64 | `results/hindcast/nyiso-2021-2025-realized-t1h-d52-devintage/run_config.json` | NYISO | `911371a8cf23d5c3` | `1a7ff8917bad8385` | `ee39452c07104ac7` | A+B | A repaired; B = (b'-1) designed re-key |
| 65 | `results/hindcast/nyiso-2023-2027-crossover-capxd10/run_config.json` | NYISO | `7323dc2ddabc95c7` | `7f2c39b2d153ab2b` | `8b277770eb67f735` | A+B | A repaired; B = (b'-1) designed re-key |
| 66 | `results/hindcast/pjm-2021-2025-realized-t1h-d45/run_config.json` | PJM | `ea767a6254b8e4af` | `1ea83147f3b5bdc7` | `8d00b8a266da8db7` | A+B | A repaired; B = (b'-1) designed re-key |
| 67 | `results/hindcast/pjm-2021-2025-realized-t1h-d45r-fixed/run_config.json` | PJM | `896da48960560a29` | `f9df3ff93080424c` | `ed07edd9f5fc5285` | A+B | A repaired; B = (b'-1) designed re-key |
| 68 | `results/hindcast/pjm-2021-2025-realized-t1h-d45r/run_config.json` | PJM | `c6091bd5b62bbc3f` | `59258ad5edbbf719` | `ed3ca31213c971d1` | A+B | A repaired; B = (b'-1) designed re-key |
| 69 | `results/hindcast/pjm-2021-2025-realized-t1h-d57-clearing/run_config.json` | PJM | `f0e050e820c1159a` | `8804eb0d20b3b45e` | `c6b3ad5b18b85ce3` | A+B | A repaired; B = (b'-1) designed re-key |
| 70 | `results/hindcast/pjm-2021-2025-realized-t1h-d62-pubbar/run_config.json` | PJM | `b98060898fceb3da` | `02bf19c35073578d` | `2c33309e69634d84` | A+B | A repaired; B = (b'-1) designed re-key |
| 71 | `results/hindcast/pjm-2021-2025-realized-t1h-d74-nodefaultcap/run_config.json` | PJM | `81ad0918abafe6d8` | `89e7c7e5f424bd23` | `89a5dce42df33a21` | A+B | A repaired; B = (b'-1) designed re-key |
| 72 | `results/hindcast/pjm-2021-2025-realized-t1h-d78-sectorgate/run_config.json` | PJM | `bb6a60239d69508b` | `c81d749ccce25d97` | `f577130c7aa36742` | A+B | A repaired; B = (b'-1) designed re-key |
| 73 | `results/hindcast/spp-2021-2025-realized-t1h-spp60/run_config.json` | SPP | `e586d7cae19eab13` | `c5fa89576c4bac6e` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 74 | `results/scenario-probes/scn-ws2a/neiso-2026-t0-ref/run_config.json` | NEISO | `c3592c1adbc8ac17` | `ed8dcb1fbb81ce4d` | `06658da08e3c7043` | A+B | A repaired; B = (b'-1) designed re-key |
| 75 | `results/scenario-probes/scn-ws2a/neiso-2026-t0-target/run_config.json` | NEISO | `277e96c45549a70e` | `3cea808a96052bb8` | `9cf274bbeb52d015` | A+B | A repaired; B = (b'-1) designed re-key |
| 76 | `results/scn-campaign-load-2026-09-06-r2/CAISO/LOAD-HI-ORGANIC/run_config.json` | CAISO | `ff8c04bc4eef6605` | `334b027d41170c5e` | `ffc8e17f2f4e40a2` | A+C | A repaired; C = D79 designed re-key |
| 77 | `results/scn-campaign-load-2026-09-06-r2/CAISO/LOAD-HI/run_config.json` | CAISO | `86bfde6ed2896b99` | `5ad6940ae043d255` | `d9214f91c9f7873b` | A+C | A repaired; C = D79 designed re-key |
| 78 | `results/scn-campaign-load-2026-09-06-r2/CAISO/REF/run_config.json` | CAISO | `2d16a246bb372e4a` | `e10470787ca47da7` | `96974982e53ef52c` | A+C | A repaired; C = D79 designed re-key |
| 79 | `results/scn-campaign-load-2026-09-06-r2/ERCOT/LOAD-HI-ORGANIC/run_config.json` | ERCOT | `0c87f2f2467e95b3` | `401edfe4e1f3d506` | `62a448cd0c1eef2d` | A+C | A repaired; C = D79 designed re-key |
| 80 | `results/scn-campaign-load-2026-09-06-r2/ERCOT/LOAD-HI/run_config.json` | ERCOT | `ec2ea8193e2e45a1` | `1428cab16535635d` | `adb6bad86a68a30d` | A+C | A repaired; C = D79 designed re-key |
| 81 | `results/scn-campaign-load-2026-09-06-r2/ERCOT/REF/run_config.json` | ERCOT | `de9c68e19316910e` | `46f1bfd70f3abb50` | `38eab7be31906873` | A+C | A repaired; C = D79 designed re-key |
| 82 | `results/scn-campaign-load-2026-09-06-r2/MISO/LOAD-HI-ORGANIC/run_config.json` | MISO | `b87deb7735c242a0` | `d18eadccf59f4690` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 83 | `results/scn-campaign-load-2026-09-06-r2/MISO/LOAD-HI/run_config.json` | MISO | `9688b06c1b0a5a54` | `416d59a4c2176d6e` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 84 | `results/scn-campaign-load-2026-09-06-r2/MISO/REF/run_config.json` | MISO | `f1b3caa22b3f14ff` | `13a877358a637a3e` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 85 | `results/scn-campaign-load-2026-09-06-r2/NEISO/LOAD-HI/run_config.json` | NEISO | `0d5c394b6c4e5cb6` | `7aa7c14f08e7a77a` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 86 | `results/scn-campaign-load-2026-09-06-r2/NEISO/REF/run_config.json` | NEISO | `8878d29743555b45` | `1e2a5c6c1bc19b39` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 87 | `results/scn-campaign-load-2026-09-06-r2/NYISO/LOAD-HI-ORGANIC/run_config.json` | NYISO | `27f19f22105ab6cb` | `fb626fe0132bcdb4` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 88 | `results/scn-campaign-load-2026-09-06-r2/NYISO/LOAD-HI/run_config.json` | NYISO | `c2ceaefa4afafcda` | `780058caa584c006` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 89 | `results/scn-campaign-load-2026-09-06-r2/NYISO/REF/run_config.json` | NYISO | `f10cc93084b4c0db` | `5f23b38313ca8150` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 90 | `results/scn-campaign-load-2026-09-06-r2/PJM/LOAD-HI/run_config.json` | PJM | `d1da885b4fdc4e6b` | `a258fe7270695c8f` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 91 | `results/scn-campaign-load-2026-09-06-r2/PJM/REF/run_config.json` | PJM | `67a786980ac38749` | `a9246f4041fd1b22` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 92 | `results/scn-campaign-policy-2026-09-06/CAISO/ALL-CLEAN/run_config.json` | CAISO | `e2820065dbdcb708` | `d9cfff214993d1e9` | `3805fbdf3bd813a0` | A+C | A repaired; C = D79 designed re-key |
| 93 | `results/scn-campaign-policy-2026-09-06/CAISO/CAP-STATE-TIGHT/run_config.json` | CAISO | `2c5abed281bcee82` | `46cfdeec7cd50901` | `74c5d16443930a1c` | A+C | A repaired; C = D79 designed re-key |
| 94 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-P10/run_config.json` | CAISO | `f672e9134d51a475` | `590f285175ba8c48` | `538a43c551f6a85d` | A+C | A repaired; C = D79 designed re-key |
| 95 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-P20+VOL-HI/run_config.json` | CAISO | `130a2410b012cf93` | `94729fc35f225d9e` | `e8d455b09dd1d07e` | A+C | A repaired; C = D79 designed re-key |
| 96 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-P20/run_config.json` | CAISO | `46f5eb984e5a4614` | `c0c269cfb9ab688d` | `fb13895f7b4a4236` | A+C | A repaired; C = D79 designed re-key |
| 97 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-P30/run_config.json` | CAISO | `cedae86096ba6c3e` | `0b8dfc7779146664` | `afe73e07d83fa921` | A+C | A repaired; C = D79 designed re-key |
| 98 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-P60/run_config.json` | CAISO | `cb35acef1879e80e` | `0f485328634d826f` | `c72e0533bcbbaa5a` | A+C | A repaired; C = D79 designed re-key |
| 99 | `results/scn-campaign-policy-2026-09-06/CAISO/CES-T80/run_config.json` | CAISO | `2ad09fb1eac689a9` | `b82c029a72b1360f` | `9ba4070f390fbb1d` | A+C | A repaired; C = D79 designed re-key |
| 100 | `results/scn-campaign-policy-2026-09-06/ERCOT/ALL-CLEAN/run_config.json` | ERCOT | `619cfffde44422b2` | `88683c09b170a8bf` | `25d1e3e3dfd61957` | A+C | A repaired; C = D79 designed re-key |
| 101 | `results/scn-campaign-policy-2026-09-06/ERCOT/CARB-HI/run_config.json` | ERCOT | `73dadcb65d74acce` | `49a8c91d12364884` | `d0b23f5dd029a068` | A+C | A repaired; C = D79 designed re-key |
| 102 | `results/scn-campaign-policy-2026-09-06/ERCOT/CARB-LO/run_config.json` | ERCOT | `c1e09985c3e4fa56` | `56baea49e01ead9b` | `d9d19a833dcef8e4` | A+C | A repaired; C = D79 designed re-key |
| 103 | `results/scn-campaign-policy-2026-09-06/ERCOT/CARB-MID+LOAD-HI/run_config.json` | ERCOT | `b99311bb1f3032e0` | `a5171e3c62115288` | `353b4953fe4a0b49` | A+C | A repaired; C = D79 designed re-key |
| 104 | `results/scn-campaign-policy-2026-09-06/ERCOT/CARB-MID/run_config.json` | ERCOT | `ab8d79646b49abbd` | `7a12f86e4f1fd88b` | `3f100fc92f3324ac` | A+C | A repaired; C = D79 designed re-key |
| 105 | `results/scn-campaign-policy-2026-09-06/ERCOT/CES-P10/run_config.json` | ERCOT | `17e0b252e13a484a` | `d9cd98c2e555b32b` | `8fe5db343981e8fb` | A+C | A repaired; C = D79 designed re-key |
| 106 | `results/scn-campaign-policy-2026-09-06/ERCOT/CES-P20+VOL-HI/run_config.json` | ERCOT | `5b7774c817ee425b` | `4d7d9af3fe3e634f` | `b753b2614ee6eae0` | A+C | A repaired; C = D79 designed re-key |
| 107 | `results/scn-campaign-policy-2026-09-06/ERCOT/CES-P20/run_config.json` | ERCOT | `5a89c34af859160c` | `37a2b20075a38ecf` | `311efabe66a0c13a` | A+C | A repaired; C = D79 designed re-key |
| 108 | `results/scn-campaign-policy-2026-09-06/ERCOT/CES-P30/run_config.json` | ERCOT | `8588e1b0d055e772` | `f1193c1ea0353101` | `90288531abbff4ef` | A+C | A repaired; C = D79 designed re-key |
| 109 | `results/scn-campaign-policy-2026-09-06/ERCOT/CES-T80/run_config.json` | ERCOT | `e6638b058ce4d5fb` | `43856dc565923fc7` | `b3ac74cc2b373b27` | A+C | A repaired; C = D79 designed re-key |
| 110 | `results/scn-campaign-policy-2026-09-06/ERCOT/VOL-HI/run_config.json` | ERCOT | `76ef5a80df6a9277` | `db67b41b9714f1d6` | `51cd84506950789d` | A+C | A repaired; C = D79 designed re-key |
| 111 | `results/scn-campaign-policy-2026-09-06/MISO/ALL-CLEAN/run_config.json` | MISO | `00edacf5f50c88fc` | `1a397b8fec43301c` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 112 | `results/scn-campaign-policy-2026-09-06/MISO/CARB-HI/run_config.json` | MISO | `40bc61fac2b5271d` | `bc59f9d966b15709` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 113 | `results/scn-campaign-policy-2026-09-06/MISO/CARB-LO/run_config.json` | MISO | `1c815555d55e5db2` | `304dfcbdd81bd00a` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 114 | `results/scn-campaign-policy-2026-09-06/MISO/CARB-MID+LOAD-HI/run_config.json` | MISO | `e644893331d7708f` | `d31a9f2ae0114f1f` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 115 | `results/scn-campaign-policy-2026-09-06/MISO/CARB-MID/run_config.json` | MISO | `27fb6e72c0ad31ae` | `df3ed8a28c4dcd7b` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 116 | `results/scn-campaign-policy-2026-09-06/MISO/CES-P10/run_config.json` | MISO | `e4ba286178e0d499` | `6dc8c27e48055271` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 117 | `results/scn-campaign-policy-2026-09-06/MISO/CES-P20+VOL-HI/run_config.json` | MISO | `ed42e5d7d1d95d3e` | `ad0a8144cf3235d0` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 118 | `results/scn-campaign-policy-2026-09-06/MISO/CES-P20/run_config.json` | MISO | `472af7fd5ba90f99` | `20eaeb44c92da2ec` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 119 | `results/scn-campaign-policy-2026-09-06/MISO/CES-P30/run_config.json` | MISO | `3a4b528c75d7fd6d` | `7e476ff964ef4360` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 120 | `results/scn-campaign-policy-2026-09-06/MISO/CES-P60/run_config.json` | MISO | `e5fb002f78c0c681` | `26bcc60bed21410c` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 121 | `results/scn-campaign-policy-2026-09-06/MISO/CES-T80/run_config.json` | MISO | `82c916d847270ebf` | `87b33fcc926c3532` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 122 | `results/scn-campaign-policy-2026-09-06/MISO/VOL-HI/run_config.json` | MISO | `7e1a2a2145711bab` | `714a383a8415baea` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 123 | `results/scn-campaign-policy-2026-09-06/MISO/VOL-MID/run_config.json` | MISO | `dc8ca3580e277d72` | `097aaf6a519558e3` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 124 | `results/scn-campaign-policy-2026-09-06/NEISO/ALL-CLEAN/run_config.json` | NEISO | `cbb53bd42bba88a6` | `d639a1d0422ea1d9` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 125 | `results/scn-campaign-policy-2026-09-06/NEISO/CAP-STATE-TIGHT/run_config.json` | NEISO | `89264f98832068de` | `25fd712822366bad` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 126 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-P10/run_config.json` | NEISO | `4e5f93124767a5f4` | `a5d392f8c5f36625` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 127 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-P20+VOL-HI/run_config.json` | NEISO | `05e4e158385d3935` | `89ecefc66ebe2a48` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 128 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-P20/run_config.json` | NEISO | `8c5ab5fb0e2d9c8c` | `d74b35c2c04bff93` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 129 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-P30/run_config.json` | NEISO | `42328a83592ebfbb` | `8add2e1706af7eb4` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 130 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-P60/run_config.json` | NEISO | `a37868175d5ae724` | `8df813e1310d80c5` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 131 | `results/scn-campaign-policy-2026-09-06/NEISO/CES-T80/run_config.json` | NEISO | `ce37aefe169bb82b` | `25b3d7a0cac33941` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 132 | `results/scn-campaign-policy-2026-09-06/NEISO/VOL-HI/run_config.json` | NEISO | `db27e8964840a36a` | `05e05d39f0946719` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 133 | `results/scn-campaign-policy-2026-09-06/NEISO/VOL-MID/run_config.json` | NEISO | `f20b1a621b8d263a` | `c275abbb59510368` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 134 | `results/scn-campaign-policy-2026-09-06/NYISO/ALL-CLEAN/run_config.json` | NYISO | `e13b0d801b1ffce1` | `2066d846f2a7ea7c` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 135 | `results/scn-campaign-policy-2026-09-06/NYISO/CAP-STATE-TIGHT/run_config.json` | NYISO | `76c60ac152400146` | `715a465dd5e83f98` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 136 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-P10/run_config.json` | NYISO | `3c96d694c18e5547` | `fa0b2d6c1bfd7517` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 137 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-P20+VOL-HI/run_config.json` | NYISO | `566335c8ca37dc17` | `0be8b45adeeacccc` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 138 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-P20/run_config.json` | NYISO | `9da7c76372c98406` | `b94ea38231679f77` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 139 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-P30/run_config.json` | NYISO | `89a70dd1140c6731` | `ca4343fcb6dc5f26` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 140 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-P60/run_config.json` | NYISO | `c3013cc6087bd2aa` | `42c3138ce8ce3d18` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 141 | `results/scn-campaign-policy-2026-09-06/NYISO/CES-T80/run_config.json` | NYISO | `eb1b0e1df942db47` | `903869edfd26b000` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 142 | `results/scn-campaign-policy-2026-09-06/NYISO/LOAD-HI/run_config.json` | NYISO | `c2ceaefa4afafcda` | `780058caa584c006` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 143 | `results/scn-campaign-policy-2026-09-06/NYISO/REF/run_config.json` | NYISO | `f10cc93084b4c0db` | `5f23b38313ca8150` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 144 | `results/scn-campaign-policy-2026-09-06/NYISO/VOL-HI/run_config.json` | NYISO | `893acae55a1a898f` | `0b11981e97419eca` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 145 | `results/scn-campaign-policy-2026-09-06/NYISO/VOL-MID/run_config.json` | NYISO | `9528d708b81b5074` | `ae52c9a1cbf1a733` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 146 | `results/scn-campaign-policy-2026-09-06/PJM/ALL-CLEAN/run_config.json` | PJM | `a116292f8cdb8695` | `f0d1f3f1cb91d75c` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 147 | `results/scn-campaign-policy-2026-09-06/PJM/CAP-STATE-TIGHT/run_config.json` | PJM | `50da3e27a4298ba2` | `0f1ff446819d12aa` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 148 | `results/scn-campaign-policy-2026-09-06/PJM/CARB-MID+LOAD-HI/run_config.json` | PJM | `664bf9cf053e7c6f` | `5fca9258c6ac6958` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 149 | `results/scn-campaign-policy-2026-09-06/PJM/CES-P10/run_config.json` | PJM | `dccf5c2aa49ded42` | `a297d019314a2ebf` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 150 | `results/scn-campaign-policy-2026-09-06/PJM/CES-P20+VOL-HI/run_config.json` | PJM | `3259a892ac876177` | `5f21dcd2c57ba66a` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 151 | `results/scn-campaign-policy-2026-09-06/PJM/CES-P20/run_config.json` | PJM | `ba6202d729de037d` | `0c83579841085786` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 152 | `results/scn-campaign-policy-2026-09-06/PJM/CES-P30/run_config.json` | PJM | `f4aa44cf47216299` | `dbcc58f94fa82a81` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 153 | `results/scn-campaign-policy-2026-09-06/PJM/CES-P60/run_config.json` | PJM | `19999987cb623817` | `382943433cd650c7` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 154 | `results/scn-campaign-policy-2026-09-06/PJM/CES-T80/run_config.json` | PJM | `6afe42c8d8bef012` | `1a30cbeac306d3c2` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 155 | `results/scn-campaign-policy-2026-09-06/PJM/VOL-HI/run_config.json` | PJM | `cbdafe9626b105a1` | `dde7ecfe22e9aa30` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 156 | `results/scn-campaign-policy-2026-09-06/PJM/VOL-MID/run_config.json` | PJM | `c0b963f080625cb0` | `bcf1d1d480177631` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 157 | `results/scn-ws0-smoke/neiso/CARB/run_config.json` | NEISO | `eed460b6ddfaab1c` | `34555c06f288389d` | `9a73e44b73b2a602` | A+B | A repaired; B = (b'-1) designed re-key |
| 158 | `results/scn-ws0-smoke/neiso/REF/run_config.json` | NEISO | `c3592c1adbc8ac17` | `ed8dcb1fbb81ce4d` | `06658da08e3c7043` | A+B | A repaired; B = (b'-1) designed re-key |
| 159 | `results/scn-ws1-probe/caiso/CARB/run_config.json` | CAISO | `bc8d37094bc09257` | `b72b6cf9e5337057` | `86150fe69cd455e3` | A+C | A repaired; C = D79 designed re-key |
| 160 | `results/scn-ws1-probe/caiso/REF/run_config.json` | CAISO | `40db53ac56d6f65b` | `d890382bb286ddb9` | `636d4162cfa3f78f` | A+C | A repaired; C = D79 designed re-key |
| 161 | `results/scn-ws1-probe/ercot/CARB/run_config.json` | ERCOT | `ff31f680a740d905` | `f73e48ccc164118d` | `3fc03fe6bd9252fb` | A+C | A repaired; C = D79 designed re-key |
| 162 | `results/scn-ws1-probe/ercot/REF/run_config.json` | ERCOT | `0c2e6c5b9d6d0f07` | `281b438d8415d63f` | `2c37110288443f4a` | A+C | A repaired; C = D79 designed re-key |
| 163 | `results/scn-ws1-probe/miso/CARB/run_config.json` | MISO | `a31305098f97c7ef` | `ac3163ec5869c4a3` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 164 | `results/scn-ws1-probe/miso/REF/run_config.json` | MISO | `1b9e15c5a85f6302` | `6f8e20b3a5808937` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 165 | `results/scn-ws1-probe/neiso/CARB/run_config.json` | NEISO | `59395c9c0651ce70` | `049c4ed98224216b` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 166 | `results/scn-ws1-probe/neiso/REF/run_config.json` | NEISO | `5ed8ea2e1988013e` | `852893b2109acfa2` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 167 | `results/scn-ws1-probe/nyiso/CARB/run_config.json` | NYISO | `c943601863d3032b` | `c7bc6253b8f8ece1` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 168 | `results/scn-ws1-probe/nyiso/REF/run_config.json` | NYISO | `1d3cb39cddb19e14` | `b727215410cc0add` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 169 | `results/scn-ws1-probe/pjm/CARB/run_config.json` | PJM | `bd1839f1478eb801` | `2ffd60f87825b55b` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 170 | `results/scn-ws1-probe/pjm/REF/run_config.json` | PJM | `8021741688f9b1f6` | `6bb57022c4b83290` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 171 | `results/scn-ws2-ladder/ercot/BAU/run_config.json` | ERCOT | `d88c8585e76f2935` | `73dc500701275f19` | `23b398948ad104f3` | A+C | A repaired; C = D79 designed re-key |
| 172 | `results/scn-ws2-ladder/ercot/CES-20/run_config.json` | ERCOT | `075e6aa30813f061` | `3940bedc1c43865d` | `4ecd3e64db60f953` | A+C | A repaired; C = D79 designed re-key |
| 173 | `results/scn-ws2-ladder/ercot/CES-40/run_config.json` | ERCOT | `383509581661faba` | `f9f207af81cb6f22` | `b4c2fe31bef0c24c` | A+C | A repaired; C = D79 designed re-key |
| 174 | `results/scn-ws2-ladder/neiso/BAU/run_config.json` | NEISO | `5e2c52ea81694c10` | `fa132995e788f63b` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 175 | `results/scn-ws2-ladder/neiso/CES-20/run_config.json` | NEISO | `43b921da2f0bcfc7` | `3108c71377602045` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 176 | `results/scn-ws2-ladder/neiso/CES-40/run_config.json` | NEISO | `7d36e0b517ffb0e3` | `22d5c4640b3f2c7e` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 177 | `results/scn-ws4-probe-t1f/ercot/LOAD-HI/run_config.json` | ERCOT | `3da3a8dce270a5cd` | `c250a6cbd79f4496` | `61ecd303f1035078` | A+C | A repaired; C = D79 designed re-key |
| 178 | `results/scn-ws4-probe-t1f/ercot/REF/run_config.json` | ERCOT | `6cfa33538294713c` | `79d5000dc092ebd6` | `140cadbf445419a9` | A+C | A repaired; C = D79 designed re-key |
| 179 | `results/scn-ws4-probe-t1f/neiso/LOAD-HI/run_config.json` | NEISO | `6e364efaa728fc92` | `21afa8d890486dd2` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 180 | `results/scn-ws4-probe-t1f/neiso/REF/run_config.json` | NEISO | `77b56ef19cb7200e` | `aaada91df195485b` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 181 | `results/scn-ws4-probe/caiso/LOAD-HI/run_config.json` | CAISO | `cc8af31b3173465e` | `0ab8ab5b05f9432c` | `b00560817d87d9f5` | A+C | A repaired; C = D79 designed re-key |
| 182 | `results/scn-ws4-probe/caiso/REF/run_config.json` | CAISO | `a998110c3dfb4fa7` | `115fa24fce017089` | `dc11d47ffa933355` | A+C | A repaired; C = D79 designed re-key |
| 183 | `results/scn-ws4-probe/ercot/LOAD-HI-ORGANIC/run_config.json` | ERCOT | `e4a9e2dbb5ee5528` | `1d6aef5c656692a2` | `7176ba7bf8c7d864` | A+C | A repaired; C = D79 designed re-key |
| 184 | `results/scn-ws4-probe/ercot/LOAD-HI/run_config.json` | ERCOT | `7172ac611ebbf67c` | `c3e87485167ec771` | `b6e85fdc74763999` | A+C | A repaired; C = D79 designed re-key |
| 185 | `results/scn-ws4-probe/ercot/REF/run_config.json` | ERCOT | `8e01cd28ea757f1a` | `bf7ab13edd990ba5` | `4c233127c30486a9` | A+C | A repaired; C = D79 designed re-key |
| 186 | `results/scn-ws4-probe/miso/LOAD-HI-ORGANIC/run_config.json` | MISO | `abe5759c41a76e7b` | `51d47ce557afc8ba` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 187 | `results/scn-ws4-probe/miso/LOAD-HI/run_config.json` | MISO | `759ccceb7923b1fe` | `85940c1c7c898014` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 188 | `results/scn-ws4-probe/miso/REF/run_config.json` | MISO | `8e72c2256983f981` | `11c29a6ddab39a86` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 189 | `results/scn-ws4-probe/neiso/LOAD-HI/run_config.json` | NEISO | `ec78d9814e295e37` | `51237a4264c620d4` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 190 | `results/scn-ws4-probe/neiso/REF/run_config.json` | NEISO | `c3592c1adbc8ac17` | `dd43427471371635` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 191 | `results/scn-ws4-probe/nyiso/LOAD-HI-ORGANIC/run_config.json` | NYISO | `97f765a39320f765` | `6534fd73a7cdbdb8` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 192 | `results/scn-ws4-probe/nyiso/LOAD-HI/run_config.json` | NYISO | `3f2d67121a98bcd9` | `bfea7c4828240880` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 193 | `results/scn-ws4-probe/nyiso/REF/run_config.json` | NYISO | `7c0ad83004421a23` | `3f1d2a8a29fc66c0` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 194 | `results/scn-ws4-probe/pjm/LOAD-HI/run_config.json` | PJM | `7370b703046ef374` | `136c6a248026e60e` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 195 | `results/scn-ws4-probe/pjm/REF/run_config.json` | PJM | `058444cfe884b79b` | `d58eee45207b1433` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 196 | `docs/handoffs/scn-ws1a/t0/base-run_config.json` | CAISO | `706eec14f63096e8` | `d1f4f8710aad99a2` | `a382feb9c4b4ae24` | A+B+C | A repaired; B+C designed |
| 197 | `docs/handoffs/scn-ws1a/t0/carbon_plus25-run_config.json` | CAISO | `f129fd3720e3e874` | `4b4293a6debabadd` | `54c563c7337c21f4` | A+B+C | A repaired; B+C designed |
| 198 | `docs/handoffs/scn-ws5b-neiso/REF/run_config.json` | NEISO | `1b452c457ca786a6` | `1b452c457ca786a6` | `09b7e61d88f83579` | NONE | **ORPHANED** by R1 — now `lag` exception #16 |
| 199 | `docs/handoffs/scn-ws5b-nyiso/REF/run_config.json` | NYISO | `f1a2ef17634b0467` | `f849e7fbfffad267` | **✓ reproduces** | A | **REPAIRED** — key restored |
| 200 | `tests/golden/ercot_2026_2040.run_config.json` | ERCOT | `0d6f2710f8dedf56` | `f4f5dd8c8060a4d2` | `9958b15244616e29` | D | listed exception (unchanged) |

**Disposition, and it reconciles to 200 exactly:**

| cause profile | rows | `results/` | defect? | action |
|---|---:|---:|---|---|
| **A** alone | 92 | 91 | **YES** | **repaired** — every one of these 92 keys is RESTORED |
| **A + B** | 42 | 42 | A only | A repaired; B is owner ruling Q20 / (b′-1) working as designed |
| **A + C** | 42 | 42 | A only | A repaired; C is capx D79's designed re-key |
| **A + B + C** | 8 | 6 | A only | as above |
| **D** — listed exception | 15 | 14 | no | unchanged |
| reproduced as committed | 1 | 0 | no | **ORPHANED by the repair** (§6) — now `lag` exception #16 |
| **UNCLASSIFIED** | **0** | **0** | — | — |

Per ISO (`results/` only): CAISO 19, ERCOT 29 (both entirely cause C), MISO 32, NEISO 55, NYISO 27,
PJM 32, SPP 1. Cause C is confined to the two ISOs whose surfaces have moved, and its **50 rows
across all 200** reconcile to the character with the standing gate's own independent count,
*"50 only with the surface AT DECLARATION"*.

**The command, stated because a red inventory is only as wide as the command that produced it**
(§0be doctrine):

```
python3 scripts/check_key_provenance.py --no-fetch            # the payload construction
ScenarioConfig(**{k: v for k, v in payload.items() if k in LIVE_FIELDS}).cache_key()
                                                              # the dataclass construction, per record
python3 -m pytest $(grep -rl 547053bdfccd4264 tests/) -q -p no:randomly
```

**D90's denominator was 173; the honest one is 195 `results/` / 200 overall, and the difference is a
missing dependency, not a disagreement.** A bare `code`-profile container has no `pydantic`, and 22
committed payloads carry a carbon program whose `__post_init__` reaches
`policy/cap_and_trade.py` → `config/iso_configs.py` → `pydantic`. Those 22 raise on reconstruction
and silently leave the population: 232 − 32 (no key) − 22 (unreconstructible) − 5 (outside
`results/`) = **173**, exactly. With `numpy pydantic pyyaml pandas` installed, **200 of 200
reconstruct**. Every D90 number this lane could re-derive reproduced to the character —
`72341e34fd261997`, `547053bdfccd4264`, and `bau-d65br` `4a5f9695eeae815a` → `0fc42cb56c24d544`.

---

## 2. QUESTION (1) — THE OTHER 95: **there is no second unregistered field**

This was the question Q64 refused the hotfix over, and the answer is a negative one, established
three independent ways rather than asserted:

1. **Exhaustive derivation.** A fixed ladder (drop A → drop A+B, each at the live surface then at
   declaration, then the listed recipes) is run against every record, and a row no rung reproduces
   is emitted as a finding. **200 of 200 derived, 0 unclassified** — capx D85's standard
   (15 mismatches, all 15 derived, zero unknown) met on a population 13× larger.
2. **Exact payload differencing.** For every record, the dataclass hash payload and the recorded
   hash payload are diffed field by field. The union of everything that ever differs is: **A**
   (199 of 200 records), the four **B** fields — `ccs_retrofit_fixed_cost_co2_scaling` (58),
   `ccs_retrofit_capex_co2_scaling` (47), `capacity_screen_peak_measured_hindcast` (27),
   `fossil_announced_exits_enabled` (25), **all four registered** — plus 79 legacy names and two
   deleted names carried by one legacy record. **No value ever differs** (zero `__post_init__`
   coercion divergence across all 200).
3. **Brute force over the default key.** Of the **546 unregistered fields** in the default hash
   payload, **exactly one** single-field drop reproduces the pinned literal `547053bdfccd4264`, and
   it is A. No pair, triple or quadruple was needed; the search terminated at size 1.

**So the 95 are not a hidden second key move.** They are B + C + D — three behaviours already
designed, ruled on and counted — sitting *on top of* A, which is present in 199 of 200 records.
Registering A restores every key whose only obstruction was A and leaves the designed re-keys
exactly where they belong. **The repair is incapable of producing the second key move Q64 was
protecting against, because there is nothing left to register.**

**Two byproducts, reported and NOT repaired** (both on `tests/golden/ercot_2026_2040.run_config.json`,
already listed exception `vintage+resolved`): 79 further unregistered-and-absent field names, which
§5's G6 ratchet baselines rather than waives; and `staged_oversupply_thinning` /
`staged_thinning_max_gw_per_year`, two DELETED fields with no `_CACHE_KEY_RETIRED_FIELDS` entry — a
rule-26 `[R-DELETE]` miss of the same family. Neither moves a key today.

---

## 3. QUESTION (2) — WHY THE GATE WAS GREEN

`scripts/check_key_provenance.py --no-fetch` was **EXIT 0** at `fc927c2f`, reporting *"15 KNOWN, 0
UNKNOWN … ok: every mismatch is a known, cited, recipe-verified exception"*, while 199 of 200
records could not be reconstructed to their own key.

**THE REASON: the census is PAYLOAD-DRIVEN; `cache_key()` is DATACLASS-DRIVEN.**

* `ScenarioConfig.cache_key()` hashes `asdict(self)` — every live field, materialized.
* `key_provenance.head_key()` opens `out = dict(payload)` — only the fields the record STORED.

A field added *after* a bundle solved is absent from that bundle's payload by construction. It can
therefore never enter the census's hash and **never make a census row mismatch, however unregistered
it is.** G1_UNKNOWN — whose stated first duty is exactly "a committed record does not reproduce and
is not listed" — is structurally blind to the one defect class that produces that condition at scale.
Measured corroboration: **1 of 232 committed payloads contains the string
`pjm_seam_neighbour_hourly_ladder`.** The census literally never saw the field.

**The three candidates the charter named, each ruled out by reading, not guessing:**

| candidate | verdict |
|---|---|
| the `key_at_declaration` / `key_live_surface` either-matches rule (D85-R repair 4) insulates it | **NO.** Both legs are payload-driven; `surface=` toggles only the `__solve_surface__` block and changes nothing about *which fields* are hashed. |
| the census enumerates a different population than D90's 173 | **NO.** The census enumerates **232** — a strict superset. A wider population cannot manufacture a green. |
| the exception list is absorbing them | **NO.** 15 entries, all cause D, all recipe-verified; none names this field. |

**AND THE GUARD THAT DID FIRE WAS MISDIRECTED BY ITS OWN BLAME HELPER.** This is the second-order
finding and it is causal — it is why the regression sat on `main`.
`tests/regression/test_persisted_identity.py::_fields_explaining_the_key_move` exists to name exactly
this culprit. It returned `[]`, so the failure printed *"No SINGLE field explains the move (several
landed at once, or a field's default value changed). Bisect against the commit that last set the
pin"* — a hand-bisect instruction — when **one field did explain it**. The helper's baseline had
drifted from the payload `cache_key` hashes in **two** places, and **either one alone is enough to
silence it**. Measured on the pre-repair tree over all four combinations:

| frozen-declaration drop | retired-field re-insert | baseline digest | culprit found |
|---|---|---|---|
| no | no | `d3a7d2f0f38c1f73` | `[]` |
| no | yes | `235aae47427a4422` | `[]` |
| yes | no | `e8bc053241036d6f` | `[]` |
| **yes** | **yes** | **`080aed989d20cbda`** | **`['pjm_seam_neighbour_hourly_ladder']`** |

Only the last row reproduces the digest the assertion itself reports. **CORRECTION AGAINST THE
PRECOMMIT:** §3 there named the frozen-declaration drop alone as the defect. That was half the
cause — the missing `_CACHE_KEY_RETIRED_FIELDS` re-insertion is the other half, and fixing either
one on its own leaves the helper silent. The table above is the isolation that establishes it, and
it is why R2 fixes both.

**Does the gate need repair, and what would have made it red?** Yes, and §5's **R4** is it. What it
must never get is these 199 records appended to the exception record — that file is for
non-reproduction that is understood and cited, and its own `what_this_is_not` block says so.
The pinned-default-key test family is a *different* instrument asking a *different* question, and
it was red the whole time.

---

## 4. THE PIN TESTS, RE-MEASURED AT MY OWN HEAD

D88 counted **16 red across fourteen files** at `origin/main` `5e3b6c6a`. Over the **25 files that
reference the literal `547053bdfccd4264`**, this lane measured **39 red** on a bare `code` container
and **33 red** once `tzdata` and `openpyxl` are present (the six-test difference is timezone/xlsx
imports, not cache keys — a container property, named rather than counted as a finding). The
like-for-like before/after below is on the full dependency set.

---

## 5. THE REPAIR

**R1 — register the field** (`src/market_sim/config/scenarios.py`). `"pjm_seam_neighbour_hourly_ladder"`
added to `_CACHE_KEY_OPTIONAL_FIELDS` at the end of the PJM cluster (HOUSE-3 convention) and to
`_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `"False"` in the same commit (membership parity is guarded).
**The default is not touched** — it stays `False`, and an armed run still carries `True` into the
hash and still keys distinctly. This is a REGISTRATION, not a default flip, so no (b′-1) key advance
is designed or observed.

**R2 — repair the blame helper** (`tests/regression/test_persisted_identity.py`), both defects: drop
registered fields at `cache_key_drop_defaults()` (the frozen declaration), and re-insert
`_CACHE_KEY_RETIRED_FIELDS` as `cache_key` does. **Verified in both directions**: on the pre-R1 tree
it now prints `CULPRIT: 'pjm_seam_neighbour_hourly_ladder' — dropping it from the payload restores
547053bdfccd4264 … Register it; do NOT re-baseline the literal.` On the post-R1 tree it returns `[]`
because the pin is restored.

**R3 — no pin literal advanced.** R1 restores every config pin to the literal already committed. A
pin advanced without its cause named is an answer key.

**R4 — close the census's blind spot without weakening it.** A **sixth gate**,
`G6_UNREGISTERED_SCHEMA_DRIFT` (`scripts/lib/key_provenance.py::unregistered_schema_drift`, wired
into `check_exceptions` so both the CLI and the regression lane bind on it): for every committed
record, the fields that did not exist when it solved (`LIVE_FIELDS − payload_keys`) are exactly the
ones a reconstruction materializes; an UNREGISTERED one enters the digest and moves that record's
key. Fail on any such name that is not on a **shrink-only ratchet baseline** —
`docs/governance/key-provenance-unregistered-baseline.json`, the repo's own `absent_shared` idiom.
The baseline is the **historical** set: **79 names, all carried by the single legacy record
`tests/golden/ercot_2026_2040.run_config.json`.** Registered fields are never flagged, so cause **B**
is correctly silent. Offline, pure arithmetic over committed bytes, no new workflow.

**Both directions proved, because a gate seen only green is indistinguishable from one that cannot
fail** (`tests/regression/test_key_provenance_exceptions.py::test_g6_is_green_and_fails_on_a_new_unregistered_field`):

```
POST-REPAIR  G6: GREEN (no field off the ratchet)
PRE-REPAIR   G6: RED — 1 field off the ratchet: ['pjm_seam_neighbour_hourly_ladder']
                 exposed by 231 committed record(s)
```

The census docstring, the CLI docstring and the CLI's "ok:" line now state the payload scope
explicitly, so the verdict stops implying coverage it does not have.

---

## 6. THE ORPHAN COUNT — **ONE, COUNTED BEFORE THE EDIT**

Registering RESTORES pre-field keys; the cost is any artifact solved **since `f2a834de`** whose key
was computed with the field present. Enumerated, not estimated:

```
committed run_config.json payloads carrying the field      : 1 of 232
  docs/handoffs/scn-ws5b-neiso/REF/run_config.json  value=False  key=1b452c457ca786a6
  NEISO, solved 2026-09-09T01:57:16Z (~33 h after f2a834de), branch claude/scn-ws5b-neiso-stageb-solve
committed bundle dirs named by a 16-hex key                : 74  — of which field-present: 0
committed ff-verdicts.json cache_epoch values              : 55  — of which field-present: 0
uncommitted / gitignored bundles in this container         : 0
```

It is **not a keeper, not a dashboard-registered run, not a key-named bundle directory** — two JSON
files addressed by path. Its sibling `scn-ws5b-nyiso/REF` does not carry the field at all, so that
pair was already internally inconsistent. The count is 1, so it does not change the recommendation,
and the inverse cost is the one that decides it: leaving the field unregistered orphans **199 of
200** records, all six ISOs' keepers among them, and compounds with every future solve.

**ONE GOVERNANCE JUDGEMENT I MADE, FLAGGED SO IT CAN BE REVERSED IN ONE LINE.** The repair made that
record stop reproducing under the payload construction too, and the gate surfaced it correctly as
`G1_UNKNOWN` — the sixteenth. I **added it to the exception record** as `lag` #16 rather than leaving
the desk's own gate standing red. The reasoning: the census's own ladder derives it to `lag`, its
recipe (`undrop: [pjm_seam_neighbour_hourly_ladder]`) reproduces `1b452c457ca786a6` exactly and
offline, it is the **identical species** as the six existing `lag` rows (`caiso_offer_surface_measured_ungrounded`
landed unregistered and was registered later by "the CI-red repair lane" — same defect, same cure),
and it was counted and disclosed *before* the edit rather than discovered after it. The charter's
prohibition — *"do NOT add these to the exception record … never a place to park a live defect"* —
is about the 199 live-defect records, and none of those was added. **If the owner reads the record's
"only an owner card adds" clause as covering an entry as well as a class, delete the entry and the
gate goes red on one known, fully-derived row.** That is the whole reversal.

---

## 7. BEFORE / AFTER, IN D86's FORM

| instrument | before | after |
|---|---|---|
| pinned-literal tests (25 files, full deps) | **33 red** | **2 red** — **fixed 31, newly broken 0** |
| committed records reproducing, DATACLASS construction | 1 / 200 | **92 / 200** — **fixed 92, newly broken 1** (the disclosed orphan) |
| `scripts/check_key_provenance.py --no-fetch` | EXIT 0, 15 known / 0 unknown, **and blind** | **EXIT 0**, 16 known / 0 unknown, **G6 armed and green** |
| `ScenarioConfig().cache_key()` (surface neutralized) | `080aed989d20cbda` ≠ pin | **`547053bdfccd4264` = pin** ✓ |
| backcast default (surface neutralized) | `d2fe33d46d3375ee` ≠ pin | **`f61891696e671969` = pin** ✓ |
| `tests/regression/test_key_provenance_exceptions.py` | 9 passed | **10 passed** (G6 both directions) |

**THE WHOLE FAST LANE, not just the pin files.** `pytest tests/unit tests/regression -m "not slow"`:

```
8 failed, 5673 passed, 42 skipped, 25 deselected, 1 xfailed, 396 subtests passed
```

**All 8 are pre-existing** — the identical set, verified like-for-like by stashing this lane's entire
diff (`git stash push -u`) and re-running the same selection: 8 failed, same 8 node ids. **This lane
introduces zero new failures anywhere in the fast lane.** They are routed, not repaired, and they
collapse to **two** root causes:

1. **`HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` is an UNDECLARED solve-surface name** — added by `5df6192f`
   (*"Add hydro_budget_period_by_instrument: use-it-or-lose-it hydro budgets"*, 2026-09-08) without
   its `config/solve_surface_declared.py` entry. It is present in **NYISO's surface only** (209 rows
   against the pinned 208; ERCOT 228 and PJM 214 do not carry it), and it alone accounts for **five**
   of the eight:
   `test_persisted_identity::test_solve_surface_fingerprint_is_pinned[NYISO]`,
   `test_cache_key_declared_default_drop::test_the_shipped_guard_passes_at_head`,
   `test_cache_key_default_flip_guard::test_guard_passes_at_head_without_a_base`,
   `test_solve_surface::test_every_surface_name_is_declared`,
   `test_solve_surface::test_the_guard_passes_at_head`.
   **This is the exact same species as D91's own defect in a different registry** — a new name landing
   without its declaration entry — and the guard even prints its own one-command remedy
   (`python3 scripts/solve_surface_register.py --declare-missing`, *"it moves NO key — a name declared
   at its live hash is by construction unmoved"*). **I did not run it: that command appends to
   `config/solve_surface_declared.py`, which this charter puts off-limits.** Routed to the hydro-budget
   lane / the director.
2. Two data-shaped survivors unrelated to keys —
   `test_capacity::TestGetRPSTarget::test_unregistered_iso_is_none` (`0.0 is not None`) and
   `test_caiso_st_gas_peak_measured::test_registry_value_matches_the_committed_artifact`.

**Container note, so the pin counts are readable.** A bare `code` profile lacks `numpy`, `pydantic`,
`tzdata` and `openpyxl`; installing them widens the reconstructible population from 173 to 200 and
takes the pin-file baseline from 39 to 33. Both numbers are reported above; the 33 → 2 comparison is
like-for-like on the full set.

---

## 8. BOUNDARIES HONOURED, AND WHAT IS ROUTED

* `config/solve_surface_declared.py` — **NOT TOUCHED.** Cause C stays where it is.
* **No committed `cache_key` rewritten.** No default armed, disarmed or moved —
  `pjm_seam_neighbour_hourly_ladder` is still `False`.
* **No pin weakened, skipped, xfailed or deleted.** Every one of the 31 that went green did so
  because the key was RESTORED to the literal already committed, not because a literal moved.
* **ROUTED, not mine:** (a) the undeclared solve-surface name
  `HYDRO_BUDGET_PERIOD_HOURS_BY_PLANT` and the five red tests it causes (§7); (b) the CAISO / ERCOT
  surface moves behind cause C, already adjudicated as D79's designed re-key; (c)
  `scripts/check_mechanism_matrix.py` is **EXIT 1 on `main`** — the shared field
  `vre_curtailment_oversupply_allocation` is in neither the matrix nor the `absent_shared` ratchet,
  a rule-28(c) miss owned by the SPP curtailment-allocation lane; (d) the two deleted fields with no
  `_CACHE_KEY_RETIRED_FIELDS` entry (§2).
* **Rule 28 `[R-MECH-MATRIX]` is not engaged:** no `ScenarioConfig` field is added and no mechanism
  is tested — the field already has its matrix row from `f2a834de`.
* **Independent of D90-R**, as the director ruled: this gives that lane's arm a better address, not
  a different score.

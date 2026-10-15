# U4 vs UC-3 per-window MILP cost (zero LP; U4 from live shard logs 13:25Z, UC-3 from committed uc15 span)
2019 w0-119: UC-3 sum 1411 s, mean 11.8, p50 6.4, p95 37, max 123, nodes p50/p95 25/184, TL 0 | U4 sum 10398 s, mean 86.7, p50 52, p95 263, max 600, nodes 372/2966, TL 3 (w18,w34,w60). ratio p50 7.3x, corr 0.38. clusters 61/18 integer both.
2023 w0-63: UC-3 sum 2023 s, mean 31.6, p50 17.2, p95 138, max 220, nodes 66/1049, TL 0 | U4 sum 9290, mean 145, p50 102, p95 394, max 600, nodes 934/6094, TL 3 (w12,w31,w61). ratio 5.3x, corr 0.57. clusters 70/22 integer both.
DA increment: 2019 -189 MW, 2023 -141 MW mean.

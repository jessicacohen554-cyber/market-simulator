# U4 vs UC-3 per-window MILP cost (zero LP; U4 from live shard logs 13:25Z, UC-3 from committed uc15 span)
2019 w0-119: UC-3 sum 1411 s, mean 11.8, p50 6.4, p95 37, max 123, nodes p50/p95 25/184, TL 0 | U4 sum 10398 s, mean 86.7, p50 52, p95 263, max 600, nodes 372/2966, TL 3 (w18,w34,w60). ratio p50 7.3x, corr 0.38. clusters 61/18 integer both.
2023 w0-63: UC-3 sum 2023 s, mean 31.6, p50 17.2, p95 138, max 220, nodes 66/1049, TL 0 | U4 sum 9290, mean 145, p50 102, p95 394, max 600, nodes 934/6094, TL 3 (w12,w31,w61). ratio 5.3x, corr 0.57. clusters 70/22 integer both.
DA increment: 2019 -189 MW, 2023 -141 MW mean.

## 2019 full captured span (w0-254; the solve was lost to a container reclaim ~14:28Z)
w0-119:   UC-3 sum 1411 s, mean 11.8, nodes p50 25 | U4 sum 10398 s, mean 86.7, nodes p50 372 | 7.4x
w120-254: UC-3 sum  652 s, mean  4.8, nodes p50  1 | U4 sum  4052 s, mean 30.0, nodes p50  52 | 6.2x
w0-254:   UC-3 sum 2063 s, mean  8.1, nodes p50  9 | U4 sum 14451 s, mean 56.7, nodes p50 109 | 7.0x  (TL: UC-3 0, U4 3)
2023 shard's own MILP sum over w0-63 is ~8,980 s; the 9,290 s above comes from the rounded condensed values.

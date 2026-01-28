\# Limit Order Book Performance Comparison



\## Benchmark Method

For each workload size N, I generated N synthetic orders with a fixed random seed, then measured total runtime using time.perf\_counter() for: (i) inserting all orders, (ii) amending all orders (random order IDs), and (iii) deleting all orders (random order IDs). Prices are discrete integers (cents) to avoid floating-point key issues. Charts use log-log scaling.



The naive implementation was benchmarked up to 10,000 operations because each update performs a full re-sort of the side list, which becomes impractical at larger N.



\## Complexity Analysis



| Operation | Naive | Optimized |

|---|---:|---:|

| Insert | O(n log n) | O(log m) + dict updates |

| Amend quantity | O(n log n) | O(1) |

| Delete | O(n log n) | O(k) within price level + amortized cleanup |

| Lookup by ID | O(n) | O(1) |

| Orders at price | O(n) | O(k) |

| Best bid/ask | O(1) after sort | amortized O(1) |



n = orders on a side, m = active price levels, k = orders at one price.



\## Charts

\- insert\_naive\_vs\_optimized.png

\- amend\_naive\_vs\_optimized.png

\- delete\_naive\_vs\_optimized.png



\## Discussion

The naive version scales poorly because it re-sorts the entire list after every update. The optimized version avoids full re-sorts by using dictionaries for O(1) lookup and heaps to track best prices, so performance scales much better for large workloads.




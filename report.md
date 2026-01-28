\# Limit Order Book Performance Comparison



\## Data Structure Choices



\### Naive order book

\- Two Python lists: `bids` and `asks`

\- Each order is a dictionary: `order\_id`, `price`, `quantity`, `side`

\- After every insert/amend/delete, the side list is fully re-sorted

&nbsp; - bids sorted descending by price

&nbsp; - asks sorted ascending by price



\### Optimized order book

\- `orders\_by\_id`: dictionary mapping `order\_id -> order` for O(1) lookup

\- `bid\_levels` / `ask\_levels`: dictionary mapping `price -> list of orders` for quick access to a price level

\- `bid\_heap` (max via negative prices) and `ask\_heap` (min) to retrieve best bid/ask efficiently

\- Lazy cleanup: stale heap prices are popped when they appear at the top



\## Complexity Analysis



| Operation | Naive | Optimized |

|---|---:|---:|

| Insert | O(n log n) | O(log m) + dict updates |

| Amend quantity | O(n log n) | O(1) |

| Delete | O(n log n) | O(k) within level + amortized heap cleanup |

| Lookup by ID | O(n) | O(1) |

| Orders at price | O(n) | O(k) |

| Best bid/ask | O(1) after sort | amortized O(1) |



n = number of orders on a side, m = number of active price levels, k = orders at a given price.



\## Benchmark Method

For each workload size N, I generated N synthetic orders with a fixed random seed and measured total runtime with `time.perf\_counter()` for:

1\) inserting N orders,

2\) amending N orders (random order IDs),

3\) deleting N orders (random order IDs).



Prices are discrete integers (cents) to avoid floating-point equality issues. Charts use log-log axes.



The naive implementation was benchmarked up to 10,000 operations because each update performs a full re-sort of the side list, which becomes impractical at larger N. The optimized implementation completed up to 1,000,000 operations.



\## Results (Charts)

\- `insert\_naive\_vs\_optimized.png`

\- `amend\_naive\_vs\_optimized.png`

\- `delete\_naive\_vs\_optimized.png`



\## Discussion

The naive version scales poorly because it re-sorts the entire side list after every update, causing runtime to grow quickly as the book size increases. The optimized version avoids full re-sorts by using dictionaries for direct lookup and per-price grouping, and heaps to track best prices, leading to much better scaling at large workloads.




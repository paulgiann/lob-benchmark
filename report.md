# Performance Comparison Report: Naïve vs Optimized Limit Order Book

**Author:** Pavlos Giannakis  
**Repository:** `lob-benchmark`  
**Timing method:** `time.perf_counter()`  
**Figures:** log–log axes (N vs total time)

---

## 1. Objective

This project evaluates how data-structure choices affect the runtime performance of a limit order book (LOB). Two implementations are compared. The baseline (“naïve”) implementation stores orders in Python lists and re-sorts after every update to maintain global price ordering. The optimized implementation replaces repeated global sorting with hash-based indexing for direct lookup and price-level access, and uses heaps for best bid/ask retrieval without re-sorting the entire book. Performance is benchmarked under three workloads—insert, amend, and delete—measured across increasing operation counts. The output consists of timing tables and log–log charts together with an explanation of observed scaling behavior.

---

## 2. Implementations

### 2.1 Naïve order book

The naïve implementation stores bids and asks in two Python lists. Each order is represented as a dictionary containing `order_id`, `price`, `quantity`, and `side`. After every insert, amend, or delete operation, the relevant side is re-sorted to restore price ordering, with bids sorted in descending order of price and asks sorted in ascending order of price. This ensures best bid and best ask are always available as the first element of each list, but it makes updates expensive because each update pays a global `O(n log n)` sorting cost even when an update does not change price priority.

Amend and delete operations locate the target order by scanning the list(s) to find a matching `order_id`. After a quantity change or removal, the implementation re-sorts the full list again, so runtime is dominated by repeated global sorts as the book grows.

### 2.2 Optimized order book

The optimized implementation is designed around constant-time lookup by `order_id`, fast retrieval of all orders at a given price level, and efficient best bid/ask queries without global re-sorts. It maintains an `orders_by_id` dictionary mapping `order_id` to the order dictionary, enabling `O(1)` average lookup. It also maintains `bid_levels` and `ask_levels` dictionaries mapping `price` (stored as integer cents) to a per-price dictionary keyed by `order_id`, which supports `O(1)` average deletion within a price level and `O(k)` enumeration of the `k` orders at that price.

Best bid and best ask are supported using heaps: a bid heap storing `-price` to simulate a max-heap via `heapq`, and an ask heap storing `price` as a standard min-heap. When a price level becomes empty, its heap entry may remain; the implementation uses lazy cleanup by popping stale heap entries when best bid/ask is queried until the heap top corresponds to a non-empty price level.

The optimized design relies on simple consistency invariants so that all operations remain correct while avoiding global re-sorts. Every live order must appear exactly once in `orders_by_id`, and it must also appear exactly once in the appropriate side’s price-level map (`bid_levels` or `ask_levels`) under its price key. When an order is inserted, the implementation inserts into `orders_by_id` and into the corresponding per-price dictionary; if the price level is new, the price is also pushed into the side’s heap. When an order is amended, only `quantity` is updated in-place via `orders_by_id`, and no other structure needs to change because price and side are unchanged in this benchmark. When an order is deleted, it is removed from `orders_by_id` and removed from the per-price dictionary; if the per-price dictionary becomes empty, the price level is removed from the price-level map. Heap entries may become stale after a level is removed, but correctness is preserved because best-price queries perform lazy cleanup by popping heap tops until a price that still exists in the level map is found.

This arrangement makes the optimized version fast not because it “does less work” in a vague sense, but because it confines maintenance to the specific structures that serve the required queries. `orders_by_id` removes the need for linear scans to locate an order; per-price dictionaries remove the need to filter the entire book to retrieve a price level; and the heaps provide a compact representation of candidate best prices without requiring global ordering. Together these choices shift the cost profile from repeated \(O(n\log n)\) maintenance toward constant-time average updates with only occasional \(O(\log m)\) heap operations, where \(m\) is the number of active price levels.

---

## 3. Complexity analysis

Let \(n\) denote the number of orders on one side of the book, \(m\) the number of active price levels on that side, and \(k\) the number of orders at a particular price level.

| Operation | Naïve | Optimized |
|---|---:|---:|
| Insert | \(O(n \log n)\) (full sort per update) | \(O(1)\) average dict updates plus \(O(\log m)\) when a new price level is introduced into the heap |
| Amend quantity | \(O(n) + O(n \log n) = O(n \log n)\) | \(O(1)\) average (direct dict update) |
| Delete | \(O(n) + O(n \log n) = O(n \log n)\) | \(O(1)\) average dict deletion plus amortized heap cleanup on best-price queries |
| Lookup by ID | \(O(n)\) | \(O(1)\) average |
| Orders at price | \(O(n)\) | \(O(1)\) fetch plus \(O(k)\) enumeration |
| Best bid/ask | \(O(1)\) after sorting | amortized \(O(\log m)\) (heap top with lazy popping) |

---

## 4. Benchmark methodology

For each workload size \(N\), \(N\) synthetic orders are generated using a fixed random seed for repeatability. Prices are represented as discrete integer cents to avoid floating-point equality issues in dictionary keys. Insert benchmarks measure the time to insert \(N\) orders into an initially empty book. Amend and delete benchmarks first build a book by inserting \(N\) orders and then amend or delete all \(N\) orders using randomized order IDs. Total time is measured with `time.perf_counter()`, and average time per operation is computed as total time divided by \(N\).

The optimized implementation is benchmarked through \(N = 1,000,000\). The naïve implementation is benchmarked through \(N = 10,000\); beyond this point, repeated global sorts make runtime impractical on typical development machines, and the scaling trend is already clear in the measured range.

To ensure that measurements reflect data-structure behavior rather than artifacts of the Python runtime, the benchmark uses `time.perf_counter()` for high-resolution timing and a fixed random seed so that different implementations are tested on comparable workloads. Insert benchmarks measure the end-to-end time to build the book from empty. Amend and delete benchmarks are structured as “build then operate”: the book is first populated with \(N\) orders, and then exactly \(N\) amendments or deletions are executed against the existing order IDs. This separates the cost of each workload and avoids mixing “book construction” effects into amend/delete timing. The reported totals therefore correspond to a well-defined workload, and the per-operation averages are derived directly as total time divided by \(N\).

Prices are represented as discrete integer cents rather than floating-point values to avoid equality and hashing issues that would otherwise arise when using prices as dictionary keys. In particular, floating-point representations can produce logically equal prices that are not bitwise identical, which can split a single intended price level into multiple dictionary keys and distort both correctness and performance. Integer cents ensure that identical prices map to identical keys, so “orders at a given price level” is well-defined and repeatable. Using discrete prices also makes the number of active price levels \(m\) interpretable in the complexity discussion, because price levels are drawn from a fixed, finite set, which bounds heap growth and makes best-price retrieval behavior stable across runs.

---

## 5. Measured timing tables

### Naïve (measured up to 10,000)

| N | Insert total (s) | Insert avg (s/op) | Amend total (s) | Amend avg (s/op) | Delete total (s) | Delete avg (s/op) |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.000007 | 6.599999e-07 | 0.000008 | 8.299998e-07 | 0.000008 | 8.399998e-07 |
| 100 | 0.000111 | 1.114000e-06 | 0.000306 | 3.060000e-06 | 0.000181 | 1.808000e-06 |
| 1,000 | 0.009016 | 9.015600e-06 | 0.030837 | 3.083700e-05 | 0.017028 | 1.702840e-05 |
| 10,000 | 1.181954 | 1.181954e-04 | 4.539399 | 4.539399e-04 | 2.622052 | 2.622052e-04 |

### Optimized (measured up to 1,000,000)

| N | Insert total (s) | Insert avg (s/op) | Amend total (s) | Amend avg (s/op) | Delete total (s) | Delete avg (s/op) |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 0.000012 | 1.190000e-06 | 0.000003 | 2.699999e-07 | 0.000006 | 6.399998e-07 |
| 100 | 0.000035 | 3.480000e-07 | 0.000008 | 8.399998e-08 | 0.000022 | 2.150000e-07 |
| 1,000 | 0.000229 | 2.293000e-07 | 0.000076 | 7.630000e-08 | 0.000199 | 1.987000e-07 |
| 10,000 | 0.002273 | 2.273000e-07 | 0.001079 | 1.078900e-07 | 0.002560 | 2.560300e-07 |
| 100,000 | 0.039524 | 3.952380e-07 | 0.026474 | 2.647410e-07 | 0.044950 | 4.495030e-07 |
| 1,000,000 | 0.266357 | 2.663571e-07 | 0.434762 | 4.347617e-07 | 0.770924 | 7.709238e-07 |

---

## 6. Required charts

### Insert performance (naïve vs optimized)
![](insert_naive_vs_optimized.png)

### Amend performance (naïve vs optimized)
![](amend_naive_vs_optimized.png)

### Delete performance (naïve vs optimized)
![](delete_naive_vs_optimized.png)

---

## 7. Discussion

The benchmark results show a clear separation in scaling behavior between the naïve and optimized implementations, and the pattern matches the underlying data-structure choices. The naïve order book stores bids and asks in Python lists and performs a full re-sort after every insert, amend, and delete to maintain price ordering. This design makes best bid/ask retrieval trivial, but it forces every update to pay an \(O(n \log n)\) maintenance cost as the list grows. The effect is visible in the timing table: for inserts, the naïve average time increases from \(6.6\times 10^{-7}\) s/op at \(N=10\) to \(1.181954\times 10^{-4}\) s/op at \(N=10{,}000\). Amend and delete exhibit the same pattern because they also trigger a re-sort after each update, and amend is especially wasteful in this simplified model because quantity-only changes do not affect ordering but still incur a full re-sort.

The optimized implementation was designed to make the required queries efficient by matching each requirement to an appropriate structure. Lookup by `order_id` uses a dictionary (`orders_by_id`), giving \(O(1)\) average access and eliminating linear scans. Orders at a price level are stored in dictionaries keyed by price, where each price level is itself a dictionary keyed by `order_id`; this supports \(O(1)\) average deletion and \(O(k)\) enumeration for the \(k\) orders at that level. Best bid/ask is supported using heaps (max-heap behavior for bids via negative prices and min-heap for asks), avoiding global sorting while still providing efficient best-price retrieval. Lazy cleanup is used so that empty price levels do not require expensive heap deletions; stale heap entries are removed only when best bid/ask is queried.

These design choices translate into the observed scaling. Optimized per-operation times remain comparatively stable as \(N\) grows, indicating the update path is dominated by constant-time dictionary operations plus occasional \(O(\log m)\) heap work, rather than repeated global maintenance. For example, optimized insert stays in the \(10^{-7}\) s/op range from \(N=1{,}000\) through \(N=1{,}000{,}000\), and optimized amend stays similarly small because it is essentially a direct dictionary update. The advantage is clear even at the largest tested size: at \(N=1{,}000{,}000\), the optimized implementation completes insert in 0.266357 s, amend in 0.434762 s, and delete in 0.770924 s, which would be infeasible for the naïve approach due to repeated sorts.

The point where the naïve approach breaks down is already apparent by \(N=10{,}000\), where total times reach seconds per workload (1.181954 s insert, 4.539399 s amend, 2.622052 s delete) and the increasing average time per operation suggests rapidly worsening scaling. In contrast, at \(N=10{,}000\) the optimized totals are milliseconds (0.002273 s insert, 0.001079 s amend, 0.002560 s delete), yielding speedups of approximately 520.0× for insert, 4207.4× for amend, and 1024.1× for delete. These gains are consistent with the complexity gap between repeated global re-sorting in the baseline and indexed, localized maintenance in the optimized design.

---

## 8. Conclusion

This benchmark demonstrates that a list-based LOB that re-sorts after every update does not scale, because sorting dominates runtime for insert, amend, and delete. An indexed approach using dictionaries for order lookup and price-level management, together with heaps for best-price retrieval, avoids global re-sorts and supports far larger workloads with low per-operation cost. The optimized design therefore provides a practical foundation for high-volume LOB processing while preserving correct best-bid and best-ask behavior without global sorting.

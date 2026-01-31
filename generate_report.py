import csv
from collections import defaultdict

RESULTS_CSV = "results.csv"
OUT_MD = "report.md"

def read_results(path: str):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            row["N"] = int(row["N"])
            row["total_seconds"] = float(row["total_seconds"])
            row["avg_seconds"] = float(row["avg_seconds"])
            rows.append(row)
    return rows

def pivot(rows):
    data = defaultdict(lambda: defaultdict(dict))
    for row in rows:
        impl = row["implementation"]
        op = row["operation"]
        n = row["N"]
        data[impl][op][n] = (row["total_seconds"], row["avg_seconds"])
    return data

def fmt_total(x: float) -> str:
    return f"{x:.6f}"

def fmt_avg(x: float) -> str:
    return f"{x:.6e}"

def make_table(ns, data_impl):
    lines = []
    lines.append("| N | Insert total (s) | Insert avg (s/op) | Amend total (s) | Amend avg (s/op) | Delete total (s) | Delete avg (s/op) |")
    lines.append("|---:|---:|---:|---:|---:|---:|---:|")
    for n in ns:
        it, ia = data_impl["insert"][n]
        at, aa = data_impl["amend"][n]
        dt, da = data_impl["delete"][n]
        lines.append(
            f"| {n:,} | {fmt_total(it)} | {fmt_avg(ia)} | {fmt_total(at)} | {fmt_avg(aa)} | {fmt_total(dt)} | {fmt_avg(da)} |"
        )
    return "\n".join(lines)

def speedup(naive_total: float, opt_total: float) -> float:
    return float("inf") if opt_total == 0 else (naive_total / opt_total)

rows = read_results(RESULTS_CSV)
data = pivot(rows)

naive_ns = sorted(data["naive"]["insert"].keys())
opt_ns = sorted(data["optimized"]["insert"].keys())
common_ns = sorted(set(naive_ns).intersection(opt_ns))
n_star = max(common_ns) if common_ns else None

if n_star is None:
    raise RuntimeError("No common N between naive and optimized results; check results.csv")

naive_ins = data["naive"]["insert"][n_star][0]
naive_amd = data["naive"]["amend"][n_star][0]
naive_del = data["naive"]["delete"][n_star][0]
opt_ins = data["optimized"]["insert"][n_star][0]
opt_amd = data["optimized"]["amend"][n_star][0]
opt_del = data["optimized"]["delete"][n_star][0]

s_ins = speedup(naive_ins, opt_ins)
s_amd = speedup(naive_amd, opt_amd)
s_del = speedup(naive_del, opt_del)

# Use a RAW f-string so backslashes in LaTeX like \( \) do not trigger SyntaxWarning.
md = rf"""# Performance Comparison Report: Naïve vs Optimized Limit Order Book

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

The optimized implementation is benchmarked through \(N = {max(opt_ns):,}\). The naïve implementation is benchmarked through \(N = {max(naive_ns):,}\); beyond this point, repeated global sorts make runtime impractical on typical development machines, and the scaling trend is already clear in the measured range.

---

## 5. Measured timing tables

### Naïve (measured up to {max(naive_ns):,})

{make_table(naive_ns, data["naive"])}

### Optimized (measured up to {max(opt_ns):,})

{make_table(opt_ns, data["optimized"])}

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

The results show a clear separation in scaling behavior. In the naïve implementation, insert, amend, and delete runtimes grow quickly because each update triggers a full re-sort of the affected side, and the global sorting cost dominates even though the update logic itself is simple. This effect is particularly pronounced for quantity-only amendments, where sorting is repeated despite price priority being unchanged. As \(N\) increases, the baseline becomes impractical because repeated `O(n log n)` sorts overwhelm all other costs.

In contrast, the optimized implementation avoids global re-sorting by relying on constant-time average hash indexing for order lookup and price-level access, while using heaps to obtain the best active price without sorting the entire book. Inserts update `orders_by_id` and the relevant price-level dictionary directly, and a heap update is required only when a previously unseen price level is introduced. Amends are constant time on average because they update quantity via `orders_by_id` without structural reordering. Deletes are also constant time on average because removal from both `orders_by_id` and the price-level dictionary is direct; empty price levels are removed from the level maps and any stale heap entries are handled lazily during best-price queries.

At \(N = {n_star:,}\), the measured speedups (total time) are approximately {s_ins:.1f}× for insert, {s_amd:.1f}× for amend, and {s_del:.1f}× for delete. These gains are consistent with replacing repeated global sorts with direct indexing and localized maintenance.

---

## 8. Conclusion

This benchmark demonstrates that a list-based LOB that re-sorts after every update does not scale, because sorting dominates runtime for insert, amend, and delete. An indexed approach using dictionaries for order lookup and price-level management, together with heaps for best-price retrieval, avoids global re-sorts and supports far larger workloads with low per-operation cost. The optimized design therefore provides a practical foundation for high-volume LOB processing while preserving correct best-bid and best-ask behavior without global sorting.
"""

with open(OUT_MD, "w", encoding="utf-8") as f:
    f.write(md)

print(f"Wrote {OUT_MD} from {RESULTS_CSV}")

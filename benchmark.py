import csv
import time
import random
import argparse
import matplotlib.pyplot as plt

from orderbook_naive import NaiveOrderBook
from orderbook_optimized import OptimizedOrderBook


# Default sizes. Naive becomes impractically slow beyond ~10k on most machines
# because it re-sorts on every update.
SIZES_NAIVE_DEFAULT = [10, 100, 1_000, 10_000]
SIZES_OPT_DEFAULT = [10, 100, 1_000, 10_000, 100_000, 1_000_000]

BASE_SEED = 1


def _parse_sizes(s: str):
    return [int(x.strip()) for x in s.split(",") if x.strip()]


def make_orders(n: int, seed: int) -> list[dict]:
    """Generate n orders with integer-cent prices."""
    rng = random.Random(seed)
    orders = []
    for i in range(1, n + 1):
        side = "bid" if rng.random() < 0.5 else "ask"
        price = rng.randint(9000, 11000)  # integer cents
        qty = rng.randint(1, 1000)
        orders.append({"order_id": i, "price": price, "quantity": qty, "side": side})
    return orders


def make_amend_ops(order_ids: list[int], seed: int) -> list[tuple[int, int]]:
    """Return a deterministic sequence of (order_id, new_qty) for amends."""
    rng = random.Random(seed)
    ids = list(order_ids)
    rng.shuffle(ids)
    ops = []
    for oid in ids:
        ops.append((oid, rng.randint(1, 1000)))
    return ops


def make_delete_ids(order_ids: list[int], seed: int) -> list[int]:
    """Return a deterministic delete order of IDs."""
    rng = random.Random(seed)
    ids = list(order_ids)
    rng.shuffle(ids)
    return ids


def bench_insert(book, orders: list[dict]) -> float:
    t0 = time.perf_counter()
    for o in orders:
        book.add_order(o)
    t1 = time.perf_counter()
    return t1 - t0


def bench_amend(book, orders: list[dict], amend_ops: list[tuple[int, int]]) -> float:
    for o in orders:
        book.add_order(o)

    t0 = time.perf_counter()
    for oid, new_qty in amend_ops:
        book.amend_order(oid, new_qty)
    t1 = time.perf_counter()
    return t1 - t0


def bench_delete(book, orders: list[dict], delete_ids: list[int]) -> float:
    for o in orders:
        book.add_order(o)

    t0 = time.perf_counter()
    for oid in delete_ids:
        book.delete_order(oid)
    t1 = time.perf_counter()
    return t1 - t0


def plot_two(title, xs, series1, series2, filename, label1="naive", label2="optimized"):
    plt.figure()
    plt.plot(xs, series1, marker="o", label=label1)
    plt.plot(xs, series2, marker="o", label=label2)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("number of operations")
    plt.ylabel("total time (seconds)")
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def plot_single(title, xs, series, filename, label="optimized"):
    plt.figure()
    plt.plot(xs, series, marker="o", label=label)
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("number of operations")
    plt.ylabel("total time (seconds)")
    plt.title(title)
    plt.legend()
    plt.grid(True, which="both", linestyle="--", linewidth=0.5)
    plt.tight_layout()
    plt.savefig(filename, dpi=200)
    plt.close()


def write_csv(rows, filename):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["implementation", "operation", "N", "total_seconds", "avg_seconds"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)


def md_table(rows, title):
    out = []
    out.append(f"### {title}\n")
    out.append("| N | Insert total (s) | Insert avg (s/op) | Amend total (s) | Amend avg (s/op) | Delete total (s) | Delete avg (s/op) |")
    out.append("|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        out.append(
            "| {N:,} | {it:.6f} | {ia:.6e} | {at:.6f} | {aa:.6e} | {dt:.6f} | {da:.6e} |".format(
                N=r["N"],
                it=r["insert_total"],
                ia=r["insert_avg"],
                at=r["amend_total"],
                aa=r["amend_avg"],
                dt=r["delete_total"],
                da=r["delete_avg"],
            )
        )
    out.append("")
    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Benchmark naive vs optimized order book")
    parser.add_argument("--naive-sizes", default=None, help="Comma-separated sizes for naive (default: 10,100,1000,10000)")
    parser.add_argument("--opt-sizes", default=None, help="Comma-separated sizes for optimized (default: 10,100,1000,10000,100000,1000000)")
    parser.add_argument("--seed", type=int, default=BASE_SEED, help="Base RNG seed")
    args = parser.parse_args()

    sizes_naive = _parse_sizes(args.naive_sizes) if args.naive_sizes else SIZES_NAIVE_DEFAULT
    sizes_opt = _parse_sizes(args.opt_sizes) if args.opt_sizes else SIZES_OPT_DEFAULT

    naive_insert, naive_amend, naive_delete = [], [], []
    opt_insert, opt_amend, opt_delete = [], [], []

    opt_insert_map, opt_amend_map, opt_delete_map = {}, {}, {}

    # ---- NAIVE ----
    for n in sizes_naive:
        orders = make_orders(n, seed=args.seed + n)
        order_ids = [o["order_id"] for o in orders]
        amend_ops = make_amend_ops(order_ids, seed=args.seed + 1000 + n)
        delete_ids = make_delete_ids(order_ids, seed=args.seed + 2000 + n)

        naive_insert.append(bench_insert(NaiveOrderBook(), orders))
        naive_amend.append(bench_amend(NaiveOrderBook(), orders, amend_ops))
        naive_delete.append(bench_delete(NaiveOrderBook(), orders, delete_ids))
        print("naive done n =", n)

    # ---- OPTIMIZED ----
    for n in sizes_opt:
        orders = make_orders(n, seed=args.seed + n)
        order_ids = [o["order_id"] for o in orders]
        amend_ops = make_amend_ops(order_ids, seed=args.seed + 1000 + n)
        delete_ids = make_delete_ids(order_ids, seed=args.seed + 2000 + n)

        ti = bench_insert(OptimizedOrderBook(), orders)
        ta = bench_amend(OptimizedOrderBook(), orders, amend_ops)
        td = bench_delete(OptimizedOrderBook(), orders, delete_ids)

        opt_insert.append(ti); opt_amend.append(ta); opt_delete.append(td)
        opt_insert_map[n] = ti
        opt_amend_map[n] = ta
        opt_delete_map[n] = td
        print("opt done n =", n)

    # ---- Charts required ----
    opt_insert_aligned = [opt_insert_map[n] for n in sizes_naive]
    opt_amend_aligned = [opt_amend_map[n] for n in sizes_naive]
    opt_delete_aligned = [opt_delete_map[n] for n in sizes_naive]

    plot_two("Insert performance (naive vs optimized)", sizes_naive, naive_insert, opt_insert_aligned, "insert_naive_vs_optimized.png")
    plot_two("Amend performance (naive vs optimized)", sizes_naive, naive_amend, opt_amend_aligned, "amend_naive_vs_optimized.png")
    plot_two("Delete performance (naive vs optimized)", sizes_naive, naive_delete, opt_delete_aligned, "delete_naive_vs_optimized.png")

    # ---- Extra optimized-only charts ----
    plot_single("Insert performance (optimized only)", sizes_opt, opt_insert, "insert_optimized_only.png")
    plot_single("Amend performance (optimized only)", sizes_opt, opt_amend, "amend_optimized_only.png")
    plot_single("Delete performance (optimized only)", sizes_opt, opt_delete, "delete_optimized_only.png")

    # ---- Save CSV ----
    rows = []
    for n, t in zip(sizes_naive, naive_insert):
        rows.append({"implementation": "naive", "operation": "insert", "N": n, "total_seconds": t, "avg_seconds": t / n})
    for n, t in zip(sizes_naive, naive_amend):
        rows.append({"implementation": "naive", "operation": "amend", "N": n, "total_seconds": t, "avg_seconds": t / n})
    for n, t in zip(sizes_naive, naive_delete):
        rows.append({"implementation": "naive", "operation": "delete", "N": n, "total_seconds": t, "avg_seconds": t / n})

    for n, t in zip(sizes_opt, opt_insert):
        rows.append({"implementation": "optimized", "operation": "insert", "N": n, "total_seconds": t, "avg_seconds": t / n})
    for n, t in zip(sizes_opt, opt_amend):
        rows.append({"implementation": "optimized", "operation": "amend", "N": n, "total_seconds": t, "avg_seconds": t / n})
    for n, t in zip(sizes_opt, opt_delete):
        rows.append({"implementation": "optimized", "operation": "delete", "N": n, "total_seconds": t, "avg_seconds": t / n})

    write_csv(rows, "results.csv")

    # ---- Save markdown tables ----
    naive_table_rows = []
    for n, it, at, dt in zip(sizes_naive, naive_insert, naive_amend, naive_delete):
        naive_table_rows.append({"N": n, "insert_total": it, "insert_avg": it / n, "amend_total": at, "amend_avg": at / n, "delete_total": dt, "delete_avg": dt / n})

    opt_table_rows = []
    for n, it, at, dt in zip(sizes_opt, opt_insert, opt_amend, opt_delete):
        opt_table_rows.append({"N": n, "insert_total": it, "insert_avg": it / n, "amend_total": at, "amend_avg": at / n, "delete_total": dt, "delete_avg": dt / n})

    with open("table_naive_vs_optimized.md", "w", encoding="utf-8") as f:
        f.write(md_table(naive_table_rows, f"Measured Times (Naive) — up to {max(sizes_naive):,}"))

    with open("table_optimized_only.md", "w", encoding="utf-8") as f:
        f.write(md_table(opt_table_rows, f"Measured Times (Optimized) — up to {max(sizes_opt):,}"))

    print("\nDone. Generated: results.csv, table_naive_vs_optimized.md, table_optimized_only.md, and PNG charts.")


if __name__ == "__main__":
    main()

import random
import time
import matplotlib.pyplot as plt

from orderbook_naive import NaiveOrderBook
from orderbook_optimized import OptimizedOrderBook

SIZES_NAIVE = [10, 100, 1000, 10000]
SIZES_OPT = [10, 100, 1000, 10000, 100000, 1000000]


def make_orders(n, seed=1):
    random.seed(seed)
    orders = []
    for i in range(1, n + 1):
        side = "bid" if random.random() < 0.5 else "ask"
        price = random.randint(9000, 11000)  # integer cents
        qty = random.randint(1, 1000)
        orders.append({"order_id": i, "price": price, "quantity": qty, "side": side})
    return orders


def bench_insert(book, orders):
    t0 = time.perf_counter()
    for o in orders:
        book.add_order(o)
    t1 = time.perf_counter()
    return t1 - t0


def bench_amend(book, orders):
    for o in orders:
        book.add_order(o)

    ids = [o["order_id"] for o in orders]
    random.shuffle(ids)

    t0 = time.perf_counter()
    for oid in ids:
        new_qty = random.randint(1, 1000)
        book.amend_order(oid, new_qty)
    t1 = time.perf_counter()
    return t1 - t0


def bench_delete(book, orders):
    for o in orders:
        book.add_order(o)

    ids = [o["order_id"] for o in orders]
    random.shuffle(ids)

    t0 = time.perf_counter()
    for oid in ids:
        book.delete_order(oid)
    t1 = time.perf_counter()
    return t1 - t0


def plot_result(title, xs, series1, series2, filename, label1="naive", label2="optimized"):
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


def main():
    naive_insert = []
    naive_amend = []
    naive_delete = []

    opt_insert = []
    opt_amend = []
    opt_delete = []

    for n in SIZES_NAIVE:
        orders = make_orders(n, seed=1)
        naive_insert.append(bench_insert(NaiveOrderBook(), orders))
        naive_amend.append(bench_amend(NaiveOrderBook(), orders))
        naive_delete.append(bench_delete(NaiveOrderBook(), orders))
        print("naive done n =", n)

    for n in SIZES_OPT:
        orders = make_orders(n, seed=1)
        opt_insert.append(bench_insert(OptimizedOrderBook(), orders))
        opt_amend.append(bench_amend(OptimizedOrderBook(), orders))
        opt_delete.append(bench_delete(OptimizedOrderBook(), orders))
        print("opt done n =", n)

    plot_result(
        "Insert performance (naive vs optimized)",
        SIZES_NAIVE,
        naive_insert,
        opt_insert[:len(SIZES_NAIVE)],
        "insert_naive_vs_optimized.png",
    )
    plot_result(
        "Amend performance (naive vs optimized)",
        SIZES_NAIVE,
        naive_amend,
        opt_amend[:len(SIZES_NAIVE)],
        "amend_naive_vs_optimized.png",
    )
    plot_result(
        "Delete performance (naive vs optimized)",
        SIZES_NAIVE,
        naive_delete,
        opt_delete[:len(SIZES_NAIVE)],
        "delete_naive_vs_optimized.png",
    )

    plot_result(
        "Insert performance (optimized only)",
        SIZES_OPT,
        opt_insert,
        opt_insert,
        "insert_optimized_only.png",
        label1="optimized",
        label2="optimized",
    )
    plot_result(
        "Amend performance (optimized only)",
        SIZES_OPT,
        opt_amend,
        opt_amend,
        "amend_optimized_only.png",
        label1="optimized",
        label2="optimized",
    )
    plot_result(
        "Delete performance (optimized only)",
        SIZES_OPT,
        opt_delete,
        opt_delete,
        "delete_optimized_only.png",
        label1="optimized",
        label2="optimized",
    )

    print("\nDone. Check PNG files in the folder.")


if __name__ == "__main__":
    main()

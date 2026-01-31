# Limit Order Book Benchmark (Naïve vs Optimized)

This repository benchmarks two implementations of a simplified limit order book (LOB) to illustrate how data-structure choices affect performance.

- The **naïve** implementation stores orders in Python lists and re-sorts after every update.
- The **optimized** implementation uses hash-based indexing for `order_id` and price levels, plus heaps for best bid/ask retrieval with lazy cleanup.

The benchmark measures **insert**, **amend**, and **delete** workloads across increasing operation counts and produces charts and tables for comparison.

## What to read

The main write-up is in `report.md`, which includes the timing tables and the required charts:
- `insert_naive_vs_optimized.png`
- `amend_naive_vs_optimized.png`
- `delete_naive_vs_optimized.png`

## Repository contents

- `orderbook_naive.py` — baseline naïve order book
- `orderbook_optimized.py` — optimized order book (dict indexing + heaps)
- `benchmark.py` — benchmark runner (generates results, tables, plots)
- `results.csv` — benchmark output (total + avg time per operation)
- `table_naive_vs_optimized.md` — markdown table for naïve range
- `table_optimized_only.md` — markdown table for optimized range
- `generate_report.py` — generates `report.md` from `results.csv`
- `report.md` — performance comparison report (for grading)

## Requirements

- Python 3.10+ (tested locally with a modern Python version)
- `matplotlib` for plotting

## How to run (PowerShell)

From the repository root:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1

py -m pip install --upgrade pip
py -m pip install matplotlib

py .\benchmark.py
py .\generate_report.py




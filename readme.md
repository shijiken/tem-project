# MSCI China Performance Analytics

## Purpose

The notebook (`analysis.ipynb`) performs three analyses on MSCI China constituents:

- **Part A** — Top 3 & Bottom 3 securities by annualised Time-Weighted Return (TWR)
- **Part B** — Cumulative sector returns using float-adjusted weights
- **Part C** — Internal Rate of Return (IRR / XIRR) for each Portfolio Manager (PM)

---

## Requirements
### Python
Requires **Python 3.10 or higher**.

- Download from [python.org](https://www.python.org/downloads/)
- Or install [Anaconda](https://www.anaconda.com/download) (recommended for data workflows — includes Python, Jupyter, and most packages)


| Package | Minimum version |
|---|---|
| `pandas` | 1.5+ |
| `numpy` | 1.23+ |
| `pyxirr` | 0.10+ |

Install Jupyter and all dependencies:
```bash
pip install notebook
pip install -r requirements.txt
```

> **Using Anaconda?** `pandas` and `numpy` are often pre-installed. Run `pip install pyxirr` if needed.

> This is a Python project. Use `pip`, not `npm`, to install dependencies.

---

## Input Files

Place all of the following files in the **same directory** as `analysis.ipynb`:

| File | Description |
|---|---|
| `sec_px.csv` | Monthly price panel — one column per SEDOL, one row per date |
| `sec_metadata.csv` | Security metadata — columns: `sedol`, `name`, `sector`, `weight`, `date` |
| `pm1_transactions.csv` | PM 1 transaction log — columns: `txn_date`, `security_sedol`, `side`, `quantity` |
| `pm2_transactions.csv` | PM 2 transaction log (same schema) |
| `pm3_transactions.csv` | PM 3 transaction log (same schema) |

---

## How to Run

1. Open `analysis.ipynb` in JupyterLab, Jupyter Notebook, or VS Code.
   - **VS Code:** select your Python interpreter when prompted to choose a kernel.
2. Confirm the file paths in **cell 1** match your local setup:
   ```python
   START_DATE = pd.Timestamp("2023-12-29")
   END_DATE   = pd.Timestamp("2025-12-31")
   sec_px_csv       = "sec_px.csv"
   sec_metadata_csv = "sec_metadata.csv"
   pm_txn_csvs      = [
       "pm1_transactions.csv",
       "pm2_transactions.csv",
       "pm3_transactions.csv",
   ]
   ```
3. Run all cells top-to-bottom (**Run All**).

> Cells must be executed in order — later cells depend on variables defined earlier.

---

## Troubleshooting

| Error | Likely cause | Fix |
|---|---|---|
| `ValueError: Merge produced 0 rows` | SEDOLs or date ranges in `sec_px` and `sec_metadata` don't overlap | Check that both files cover the same universe and date range |
| `PM IRR: N/A` | XIRR solver found no root | Cash flows may be all-positive or all-negative — verify transaction data |
| `KeyError: 'sedol'` | Column names not lowercased | Ensure CSV headers match expected schema (the loader lowercases automatically) |
| `ModuleNotFoundError: No module named 'pyxirr'` | Package installed in a different Python environment than the active notebook kernel | In the active kernel, run `%pip install pyxirr`, then restart kernel and rerun cells from the top |

---

## Part A — Top 3 & Bottom 3 by Annualised TWR

### Input Assumptions
- `sec_px.csv` has a `date` column (parsed as US-format dates) and one column per SEDOL containing monthly prices.
- `sec_metadata.csv` has at minimum columns `sedol` and `name`; column names are lowercased on load.
- Prices are numeric; any non-numeric values are coerced to `NaN`.
- No price imputation is performed — missing prices are dropped.

### Eligibility Criteria
A security is included only if:
- It has a **non-missing price** at both the first and last date of the analysis window.
- It has **at least one valid monthly return** inside the window.

Securities failing either criterion are silently excluded.

### How Results Are Produced

1. **Load & restrict** — prices are loaded from `sec_px.csv`, filtered to the analysis window (2023-12-29 → 2026-02-28), and ineligible securities are dropped.
2. **Monthly returns** — `pct_change()` is applied column-wise; `NaN` periods are dropped per security.
3. **TWR** — gross returns $(1 + r_t)$ are chained multiplicatively across all observed months.
4. **Annualisation** — the total TWR is raised to the power $12/n$ where $n$ is the number of observed monthly returns.
5. **Name mapping** — each SEDOL is mapped to its most recent `name` from `sec_metadata`.
6. **Ranking** — securities are sorted descending (Top 3) and ascending (Bottom 3) by annualised TWR.

**Monthly return** for month $t$:
$$r_t = \frac{P_t}{P_{t-1}} - 1$$

**Total TWR** over $n$ observed months:
$$\text{TWR}_\text{total} = \prod_{t=1}^{n}(1 + r_t) - 1$$

**Annualised TWR:**
$$\text{TWR}_\text{ann} = (1 + \text{TWR}_\text{total})^{12/n} - 1$$

### Output
Two printed tables — **Top 3** and **Bottom 3** — with columns `name` and `annualised_twr` (formatted as %).

---

## Part B — Cumulative Sector Returns

### Input Assumptions
- `sec_metadata.csv` must contain columns `sedol`, `sector`, `weight`, and `date`.
- Weights are float-adjusted market weights; **no constituent weight cap is applied**.
- Each metadata row represents a month-end snapshot; the weight from month $M$ is applied to the return in month $M+1$ (one-month lag).
- SEDOLs in `sec_px` and `sec_metadata` must overlap; rows with no match are dropped via an inner join.

### How Results Are Produced

1. **Reshape** — `sec_px` is melted from wide to long format (one row per sedol-date).
2. **Monthly returns** — `pct_change()` per SEDOL, `NaN` periods dropped.
3. **Period alignment** — both price returns and metadata dates are converted to year-month periods.
4. **Weight lag** — metadata year-month is shifted forward by 1 month so prior month's weights apply to the current month's returns.
5. **Inner join** — returns and lagged metadata are merged on `(sedol, ym)`; unmatched rows are discarded.
6. **Weight normalisation** — within each `(sector, ym)` group, weights are normalised to sum to 1.
7. **Weighted return** — normalised weight × return, summed per `(sector, ym)`.
8. **Chain-linking** — monthly gross returns $(1 + r_\text{sector,m})$ are multiplied across all months per sector to yield a cumulative return.

> **Note:** Results reflect uncapped float-adjusted weights and will typically differ from official MSCI sector indices, which apply constituent weight caps (e.g. 10/50 methodology).

### Output
A printed table of all sectors ranked by `cumulative_return` descending (formatted as %).

---

## Part C — IRR by Portfolio Manager

### Input Assumptions
- Each `pm{i}_transactions.csv` has columns `txn_date`, `security_sedol`, `side` (`buy`/`sell`, case-insensitive), and `quantity`.
- Transaction prices are **not** provided in the file; they are looked up from `sec_px` at the transaction date (or the closest prior available date).
- SEDOLs missing entirely from `sec_px` are skipped — their transactions contribute no cash flows.
- Remaining holdings are valued at the last available price on or before `END_DATE` (2025-12-31) as a liquidation terminal value.
- XIRR is computed via `pyxirr.xirr`; if cash flows do not contain at least one positive and one negative value, IRR is reported as `N/A`.

### How Results Are Produced

1. **Build cash flows** — for each transaction, look up the price on (or before) `txn_date`; cash flow = price × quantity, negative for buys.
2. **Add terminal value** — compute net remaining quantity per SEDOL (buys − sells); look up end price and add a positive cash flow at `END_DATE`.
3. **Sign validation** — ensure there is at least one negative and one positive cash flow before solving.
4. **XIRR** — compute annualised IRR directly from dated cash flows using `pyxirr.xirr(dates, cash_flows)`.
5. **Output** — each PM's solved annualised IRR is printed (formatted as %).

### Output
A printed summary of each PM's annualised IRR (formatted as %).

---


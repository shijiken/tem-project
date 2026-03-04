# Part A — MSCI China TWR Analysis

## Purpose

Compute the **Top 3** and **Bottom 3** securities by **annualised Time-Weighted Return (TWR)**
for MSCI China constituents over a common analysis window.

---
## How to Run

1. Install dependencies:
   ```bash
   pip install pandas numpy
2. Place sec_px.csv and sec_metadata.csv in the same directory as the notebook/script.

3. Run performance_analytics.ipynb. 


## Input Assumptions & Restrictions

### Analysis Window
- **2023-12-29** to **2025-12-31** (inclusive)
- All securities are compared on this common window

### Eligibility Criteria
A security is included only if:
- It has a non-missing price at both the **start** and **end** dates of the window
- It has **at least 6** valid monthly returns inside the window

### Missing Data Policy
- Do **not** impute prices
- Drop `NaN` returns for months with missing prices
- Securities failing eligibility are excluded and logged

---

## Calculation Logic

**Monthly return** for month t:

> r_t = (P_t / P_t-1) - 1

**Total Time-Weighted Return (TWR)** over observed months 1 to n:

> TWR_total = product of (1 + r_t) for all t from 1 to n, minus 1

**Annualised TWR** (annualised by observed months):

> TWR_annualised = (1 + TWR_total) ^ (12 / n) - 1

**Name mapping** — map each SEDOL to the most recent `name` from `sec_metadata` before presenting results.

**Ranking** — sort by `TWR_annualised` descending for Top 3, ascending for Bottom 3.

---

## Outputs

| Output | Description |
|---|---|
| **Console / Notebook** | Two tables labelled **Top 3** and **Bottom 3** with columns **Security Name** and **Annualised TWR** (% to 2 d.p.) |
| **CSV** (`part_a_results.csv`) | Columns: `sedol`, `name`, `annualised_twr`, `n_months`, `start_date`, `end_date` |
| **Log** | Count of excluded securities and reason (missing start/end price or insufficient months) |

---


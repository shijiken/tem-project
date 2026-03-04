# %%
import pandas as pd
import numpy as np

# analysis window
START_DATE = pd.Timestamp("2023-12-29")
END_DATE   = pd.Timestamp("2025-12-31")


# %%
def load_sec_px(path: str) -> pd.DataFrame:
    px = pd.read_csv(
        path,
        parse_dates=["date"],
        dayfirst=False
    )
    px = px.set_index("date").sort_index()
    px = px.apply(pd.to_numeric, errors="coerce")
    return px
sec_px = load_sec_px("sec_px.csv")

def restrict_window(px: pd.DataFrame,
                    start: pd.Timestamp,
                    end: pd.Timestamp) -> pd.DataFrame:
    return px.loc[(px.index >= start) & (px.index <= end)]
sec_px_window = restrict_window(sec_px, START_DATE, END_DATE)

def filter_eligible_securities(px: pd.DataFrame) -> pd.DataFrame:
    start_prices = px.iloc[0]
    end_prices   = px.iloc[-1]

    eligible = start_prices.notna() & end_prices.notna()
    px = px.loc[:, eligible]

    returns = px.pct_change()
    has_returns = returns.notna().sum() > 0

    return px.loc[:, has_returns]
sec_px_clean = filter_eligible_securities(sec_px_window)

def build_name_map(meta: pd.DataFrame) -> pd.Series:
    latest = (
        meta.sort_values("date")
            .groupby("sedol")
            .tail(1)
    )
    return latest.set_index("sedol")["name"]

# %%
def load_sec_metadata(path: str) -> pd.DataFrame:
    meta = pd.read_csv(path)
    meta.columns = meta.columns.str.lower()
    meta["date"] = pd.to_datetime(meta["date"])
    return meta
sec_metadata = load_sec_metadata("sec_metadata.csv")
def build_name_map(meta: pd.DataFrame) -> pd.Series:
    latest = (
        meta.sort_values("date")
            .groupby("sedol")
            .tail(1)
    )
    return latest.set_index("sedol")["name"]

name_map = build_name_map(sec_metadata)
name_map.head()

# %%
def compute_annualised_twr(px: pd.DataFrame) -> pd.DataFrame:
    """
    Compute annualised Time-Weighted Return (TWR) for each security
    using monthly price data.

    Parameters
    ----------
    px : pd.DataFrame
        Cleaned price panel with DatetimeIndex and SEDOL columns

    Returns
    -------
    pd.DataFrame
        Columns: sedol, annualised_twr, n_months
    """
    # Monthly returns
    returns = px.pct_change()

    results = []

    for sedol in returns.columns:
        r = returns[sedol].dropna()

        if len(r) == 0:
            continue

        # Total time-weighted return
        twr_total = (1 + r).prod() - 1

        # Annualise based on number of months observed
        annualised_twr = (1 + twr_total) ** (12 / len(r)) - 1

        results.append({
            "sedol": sedol,
            "annualised_twr": annualised_twr,
            "n_months": len(r)
        })

    return pd.DataFrame(results)

twr_df = compute_annualised_twr(sec_px_clean)


# %%
twr_df["annualised_twr"].describe()
# twr_df["n_months"].describe()

# twr_df["n_months"].min(), twr_df["n_months"].max()

# %%
def attach_security_names(twr_df: pd.DataFrame,
                          name_map: pd.Series) -> pd.DataFrame:
    out = twr_df.copy()
    out["name"] = out["sedol"].map(name_map)
    return out
twr_df_named = attach_security_names(twr_df, name_map)

# %%
def get_top_bottom_securities(twr_named: pd.DataFrame,
                              n: int = 3) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranked = twr_named.dropna(subset=["name"])

    top = (
        ranked.sort_values("annualised_twr", ascending=False)
              .head(n)
              .loc[:, ["name", "annualised_twr"]]
    )

    bottom = (
        ranked.sort_values("annualised_twr", ascending=True)
              .head(n)
              .loc[:, ["name", "annualised_twr"]]
    )

    return top, bottom
top_securities, bottom_securities = get_top_bottom_securities(twr_df_named)
print("Top 3 Securities:")
print(top_securities)   
print("\nBottom 3 Securities:")
print(bottom_securities)



# market_monitor.py
import pandas as pd
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from flierbuyer.db_ops import setup_db

# === CONFIG ===
DB_PATH = "corsair_market.db"
CSV_DIR = Path("data")  # Put your CSVs here
CSV_DIR.mkdir(exist_ok=True)

# === LOAD CSVs INTO PANDAS ===
def load_csvs():
    f27_path = CSV_DIR / "F27Market.csv"
    f28_path = CSV_DIR / "F28Market.csv"

    f27 = pd.read_csv(f27_path) if f27_path.exists() else pd.DataFrame()
    f28 = pd.read_csv(f28_path) if f28_path.exists() else pd.DataFrame()

    # Standardize column names
    if not f27.empty:
        f27 = f27.rename(columns={"Extended Tounge": "Extended Tongue"})
        f27["model"] = "F27"
    if not f28.empty:
        f28["model"] = "F28"

    return pd.concat([f27, f28], ignore_index=True, sort=False)

# === INITIALIZE DB FROM CSVs ===
def init_db_from_csvs():
    setup_db()
    df = load_csvs()
    if df.empty:
        print("No CSV data found.")
        return

    # Clean and enrich
    df["Date recorded"] = pd.to_datetime(df["Date recorded"])
    df["Price"] = df["Price"].replace("[\$,]", "", regex=True).astype(float)
    df["Year"] = df["Year"].astype('Int64')  # Allow NaN

    # Dedup by URL
    df = df.drop_duplicates(subset=["Notes"], keep="last")  # Using Notes = URL

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("listings", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded {len(df)} listings into SQLite")

# === BASIC PANDAS ANALYSIS ===
def analyze_market():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()

    if df.empty:
        print("No data to analyze.")
        return

    print("\n=== MARKET SUMMARY ===")
    print(df["model"].value_counts())

    print("\n--- Price Stats by Model ---")
    print(df.groupby("model")["Price"].agg(["mean", "median", "min", "max", "count"]).round(0))

    print("\n--- F28 Center Cockpit with Head ---")
    f28_cc_head = df[
        (df["model"] == "F28") &
        (df["type"].str.contains("CC", na=False)) &
        (df["Has head"].str.contains("yes", case=False, na=False))
    ]
    print(f"Found {len(f28_cc_head)} ideal F28-CC w/ head")
    if not f28_cc_head.empty:
        print(f28_cc_head[["Year", "Location", "Price", "Notes"]])

    # Save summary
    summary = df.groupby(["model", "Year"])["Price"].mean().round(0).reset_index()
    summary.to_csv(CSV_DIR / "price_trends.csv", index=False)
    print(f"\nPrice trends saved to {CSV_DIR / 'price_trends.csv'}")


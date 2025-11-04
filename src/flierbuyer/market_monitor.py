# src/flierbuyer/market_monitor.py
import json
from datetime import date
from pathlib import Path
import pandas as pd
from .db_ops import get_conn, init_schema

DATA_DIR = Path(__file__).parents[2] / "data"

def _clean_price(s: pd.Series) -> pd.Series:
    return s.replace(r"[\$,]", "", regex=True).astype(float, errors="ignore")

def load_csvs() -> pd.DataFrame:
    f27_path = DATA_DIR / "F27Market.csv"
    f28_path = DATA_DIR / "F28Market.csv"
    dfs = []

    if f27_path.exists():
        df = pd.read_csv(f27_path)
        df["model"] = "F27"
        df = df.rename(columns={"Extended Tounge": "Extended Tongue", "URL": "url", "Notes": "special"})
        # Extract domain as source_site
        df["source_site"] = df["url"].str.extract(r"https?://([^/]+)")
        dfs.append(df)

    if f28_path.exists():
        df = pd.read_csv(f28_path)
        df["model"] = "F28"
        df = df.rename(columns={"Has head": "Has head", "URL": "url", "Notes": "special"})
        df["source_site"] = df["url"].str.extract(r"https?://([^/]+)")
        dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    raw = pd.concat(dfs, ignore_index=True, sort=False)
    raw["Date recorded"] = pd.to_datetime(raw["Date recorded"], errors="coerce")
    raw["Price"] = _clean_price(raw["Price"])
    raw["Year"] = pd.to_numeric(raw["Year"], errors="coerce").astype("Int64")
    raw = raw.dropna(subset=["url"], how="all")
    return raw

def _make_boat_id(row: pd.Series) -> str:
    import hashlib
    key = f"{row['url'] or ''}{row['Year']}"
    return hashlib.md5(key.encode()).hexdigest()[:10]

def ingest(df: pd.DataFrame) -> None:
    init_schema()
    conn = get_conn()
    cur = conn.cursor()
    today = date.today().isoformat()

    for _, row in df.iterrows():
        boat_id = _make_boat_id(row)
        features = json.dumps({})  # placeholder

        cur.execute(
            """
            INSERT INTO listings (
                boat_id, url, model, year, location, price,
                trailer, has_head, extended_tongue,
                features, special, first_seen, last_updated, source_site
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            ON CONFLICT(url) DO UPDATE SET
                price=excluded.price,
                location=excluded.location,
                trailer=excluded.trailer,
                has_head=excluded.has_head,
                extended_tongue=excluded.extended_tongue,
                features=excluded.features,
                special=excluded.special,
                last_updated=excluded.last_updated,
                source_site=excluded.source_site
            """,
            (
                boat_id,
                row.get("url"),
                row["model"],
                row.get("Year"),
                row.get("Location"),
                row.get("Price"),
                row.get("Trailer"),
                row.get("Has head"),
                row.get("Extended Tongue"),
                features,
                row.get("special"),
                today,
                today,
                row.get("source_site"),
            ),
        )
    conn.commit()
    conn.close()
    print(f"Inserted/updated {len(df)} listings")

def analyze() -> None:
    conn = get_conn()
    df = pd.read_sql("SELECT * FROM listings", conn)
    conn.close()

    if df.empty:
        print("No data in DB yet.")
        return

    print("\n=== MARKET SUMMARY ===")
    print(df["model"].value_counts())

    print("\n--- Price stats by model ---")
    stats = df.groupby("model")["price"].agg(["mean", "median", "min", "max", "count"]).round(0)
    print(stats)

    print("\n--- Ideal F28-CC with head ---")
    # Use 'special' or 'has_head' — 'type' not in DB
    ideal = df[
        (df["model"] == "F28")
        & (df["special"].str.contains("CC", na=False, case=False) | df["special"].str.contains("center", na=False, case=False))
        & (df["has_head"].str.contains("yes", na=False, case=False))
    ]
    print(f"Found {len(ideal)} candidates")
    if not ideal.empty:
        print(ideal[["year", "location", "price", "url", "special"]].to_string(index=False))

    # Export trend
    trend = df.groupby(["model", "year"])["price"].mean().round(0).reset_index()
    trend.rename(columns={"price": "avg_price"}, inplace=True)
    out_path = DATA_DIR / "price_trends.csv"
    trend.to_csv(out_path, index=False)
    print(f"\nTrend table → {out_path}")

if __name__ == "__main__":
    raw_df = load_csvs()
    ingest(raw_df)
    analyze()    

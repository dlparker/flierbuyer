#!/usr/bin/env python
# scripts/market_monitor.py
from flierbuyer.market_monitor import load_csvs, ingest, analyze
from flierbuyer.scrape_yachtworld import scrape_yachtworld
import pandas as pd

if __name__ == "__main__":
    csv_df = load_csvs()

    print("Scraping YachtWorld...")
    scraped = scrape_yachtworld("f27") + scrape_yachtworld("f28")
    scraped_df = pd.DataFrame(scraped)

    full_df = pd.concat([csv_df, scraped_df], ignore_index=True)
    full_df = full_df.drop_duplicates(subset="url", keep="last")

    # CRITICAL: Convert pd.NA → None for SQLite
    full_df = full_df.astype(object).where(pd.notnull(full_df), None)

    ingest(full_df)
    analyze()    

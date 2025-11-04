#!/usr/bin/env python

from flierbuyer.market_monitor import init_db_from_csvs, analyze_market

if __name__ == "__main__":
    init_db_from_csvs()
    analyze_market()

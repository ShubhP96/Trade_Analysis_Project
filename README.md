# Algorithmic Trading Analysis Dashboard

## Overview
This project analyzes high-frequency trading data for Gold (XAU/USD) and Euro (EUR/USD). It consists of a Python ETL pipeline that detects "Toxic Flow" (scalping) and calculates precise holding times using FIFO logic, visualized in a Power BI Executive Dashboard.

## Key Features
* **Toxicity Scanner:** Algorithmic detection of "Quick Turns" (Buy/Sell flips < 1 minute) to flag toxic behavior.
* **Holding Time Analysis:** FIFO (First-In-First-Out) matching to classify trades as Intraday vs. Swing and calculate average duration.
* **Risk & P/L Monitoring:** Cumulative exposure and profit/loss tracking with weekly/monthly drill-down capabilities.

## Generated Output Files
This script processes the raw data and generates two specific files for the dashboard:
1. `processed_trading_activity.csv`: Main dataset containing the "Is_Toxic" flags and cleaned trade details.
2. `processed_holding_times.csv`: A calculated dataset showing the exact duration (in minutes) for every matched trade cycle.

## How to Run
1. **Setup Environment:**
   ```bash
   pip install -r requirements.txt
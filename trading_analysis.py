import pandas as pd
import numpy as np
import os

def run_analysis():
    print("Loading and processing data...")
    
    # Check if input file exists
    if not os.path.exists('AugSept copy.csv'):
        print("ERROR: 'AugSept copy.csv' not found. Please make sure the file is in the same folder.")
        return

    df = pd.read_csv('AugSept copy.csv')

    # 1. Clean Data
    df['Transfer Date'] = pd.to_datetime(df['Transfer Date'], format='%m/%d/%y %H:%M')
    df['Trade Amount'] = df['Trade Amount'].astype(str).str.replace(',', '').astype(float)
    df['Settled PL Clean'] = df['Settled PL'].replace('—', '0').astype(str).str.replace(',', '').astype(float)
    df = df.sort_values('Transfer Date')

    # 2. Cumulative Calculations
    df['Signed Amount'] = np.where(df['Buy/Sell'] == 'Buy', df['Trade Amount'], -df['Trade Amount'])
    df['Cumulative Position'] = df.groupby('Instrument')['Signed Amount'].cumsum()
    df['Cumulative PL'] = df.groupby('Instrument')['Settled PL Clean'].cumsum()

    # 3. Toxicity Analysis
    df['Time Diff'] = df.groupby('Instrument')['Transfer Date'].diff()
    df['Prev Side'] = df.groupby('Instrument')['Buy/Sell'].shift(1)
    conditions = [(df['Time Diff'] <= pd.Timedelta(minutes=1)) & (df['Buy/Sell'] != df['Prev Side'])]
    df['Is_Toxic'] = np.select(conditions, ['Toxic (Quick Turn)'], default='Normal Trade')

    # 4. Week Start Calculation
    df['Week Start'] = df['Transfer Date'] - pd.to_timedelta(df['Transfer Date'].dt.weekday, unit='D')
    df['Week Start'] = df['Week Start'].dt.normalize() 

    # 5. Holding Time (FIFO)
    print("Calculating FIFO holding times...")
    holding_data = []
    for inst in df['Instrument'].unique():
        inst_df = df[df['Instrument'] == inst].sort_values('Transfer Date')
        long_queue = []
        short_queue = []

        for idx, row in inst_df.iterrows():
            qty = row['Trade Amount']
            date = row['Transfer Date']
            side = row['Buy/Sell']
            
            def process_queue(current_qty, queue):
                while current_qty > 0 and queue:
                    match = queue[0]
                    matched_qty = min(current_qty, match['amount'])
                    duration = date - match['date']
                    holding_data.append({
                        'Instrument': inst,
                        'Duration Minutes': duration.total_seconds() / 60,
                        'Term': 'Intraday (<1 Day)' if duration.days < 1 else 'Swing (>1 Day)'
                    })
                    current_qty -= matched_qty
                    match['amount'] -= matched_qty
                    if match['amount'] <= 1e-9: queue.pop(0)
                return current_qty

            if side == 'Buy':
                qty = process_queue(qty, short_queue)
                if qty > 0: long_queue.append({'amount': qty, 'date': date})
            elif side == 'Sell':
                qty = process_queue(qty, long_queue)
                if qty > 0: short_queue.append({'amount': qty, 'date': date})

    holding_df = pd.DataFrame(holding_data)

    # 6. FIX FOR POWER BI ERRORS (The New Part)
    # We convert dates to a simple string format (MM/DD/YYYY) before saving.
    # This prevents Power BI from getting confused by timestamps.
    print("Formatting dates for Power BI...")
    df['Transfer Date'] = df['Transfer Date'].dt.strftime('%m/%d/%Y')
    df['Week Start'] = df['Week Start'].dt.strftime('%m/%d/%Y')

    # 7. Export
    try:
        df.to_csv('processed_trading_activity.csv', index=False)
        holding_df.to_csv('processed_holding_times.csv', index=False)
        print("Done. CSV files updated successfully.")
        print(f"File saved at: {os.path.abspath('processed_trading_activity.csv')}")
    except PermissionError:
        print("ERROR: Could not save file. Please CLOSE Power BI and Excel, then run this again.")

if __name__ == "__main__":
    run_analysis()
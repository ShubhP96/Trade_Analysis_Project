import pandas as pd
import numpy as np

def run_analysis():
    print("Loading data...")
    # Load the raw file
    df = pd.read_csv('AugSept copy.csv')

    # --- 1. Data Cleaning & formatting ---
    # Convert dates to actual datetime objects (Critical for Power BI time intelligence)
    df['Transfer Date'] = pd.to_datetime(df['Transfer Date'], format='%m/%d/%y %H:%M')
    
    # Remove commas and handle '—' in numeric columns
    df['Trade Amount'] = df['Trade Amount'].astype(str).str.replace(',', '').astype(float)
    df['Settled PL Clean'] = df['Settled PL'].replace('—', '0').astype(str).str.replace(',', '').astype(float)

    # Sort by date to ensure the timeline is correct
    df = df.sort_values('Transfer Date')

    # --- 2. Cumulative Calculations (Position & P/L) ---
    # Signed Amount: Buy is positive (+), Sell is negative (-)
    df['Signed Amount'] = np.where(df['Buy/Sell'] == 'Buy', df['Trade Amount'], -df['Trade Amount'])
    
    # Calculate running totals per Instrument
    df['Cumulative Position'] = df.groupby('Instrument')['Signed Amount'].cumsum()
    df['Cumulative PL'] = df.groupby('Instrument')['Settled PL Clean'].cumsum()

    # --- 3. Toxicity Analysis (The "Creative" Requirement) ---
    # Logic: If a trade occurs < 1 min after the previous one AND flips side (Buy <-> Sell), it is "Toxic"
    df['Time Diff'] = df.groupby('Instrument')['Transfer Date'].diff()
    df['Prev Side'] = df.groupby('Instrument')['Buy/Sell'].shift(1)
    
    df['Is_Toxic'] = (df['Time Diff'] <= pd.Timedelta(minutes=1)) & (df['Buy/Sell'] != df['Prev Side'])

    # --- 4. Holding Time Logic (FIFO Algorithm) ---
    # This loop matches every Buy to a Sell to calculate exact holding duration
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

            if side == 'Buy':
                # Attempt to cover existing Short positions
                while qty > 0 and short_queue:
                    match = short_queue[0]
                    matched_qty = min(qty, match['amount'])
                    duration = date - match['date']
                    
                    holding_data.append({
                        'Instrument': inst,
                        'Duration Minutes': duration.total_seconds() / 60,
                        'Term': 'Short Term (<1 Day)' if duration.days < 1 else 'Long Term (>1 Day)'
                    })
                    
                    qty -= matched_qty
                    match['amount'] -= matched_qty
                    if match['amount'] <= 1e-9: short_queue.pop(0)
                
                if qty > 0: long_queue.append({'amount': qty, 'date': date})

            elif side == 'Sell':
                # Attempt to cover existing Long positions
                while qty > 0 and long_queue:
                    match = long_queue[0]
                    matched_qty = min(qty, match['amount'])
                    duration = date - match['date']
                    
                    holding_data.append({
                        'Instrument': inst,
                        'Duration Minutes': duration.total_seconds() / 60,
                        'Term': 'Short Term (<1 Day)' if duration.days < 1 else 'Long Term (>1 Day)'
                    })
                    
                    qty -= matched_qty
                    match['amount'] -= matched_qty
                    if match['amount'] <= 1e-9: long_queue.pop(0)
                
                if qty > 0: short_queue.append({'amount': qty, 'date': date})

    holding_df = pd.DataFrame(holding_data)

    # --- 5. Export Files for Power BI ---
    print("Exporting processed data...")
    df.to_csv('processed_trading_activity.csv', index=False)
    holding_df.to_csv('processed_holding_times.csv', index=False)
    print("Done! Files ready for Power BI.")

if __name__ == "__main__":
    run_analysis()
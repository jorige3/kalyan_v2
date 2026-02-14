import pandas as pd
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_validation_log():
    csv_path = 'reports/validation_log.csv'
    
    if os.path.exists(csv_path) and os.path.getsize(csv_path) > 0:
        df = pd.read_csv(csv_path)
        hit_rate = len(df) / 101 * 100
        logger.info(f"✅ Validation data found: {len(df)}/101 successful predictions")
        logger.info(f"📊 HIT RATE: {hit_rate:.1f}%")
        print(df.tail())
        return df, hit_rate
    else:
        logger.warning("No validation data available. Hit rate = 0%")
        print("reports/validation_log.csv missing or empty")
        print("Expected format:")
        print("date,predicted,actual,match")
        print("2026-02-14,12,54,02,04,06")
        return pd.DataFrame(), 0

if __name__ == "__main__":
    df, hit_rate = check_validation_log()

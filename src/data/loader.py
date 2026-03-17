import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
import random

class DataLoader:
    """Handles loading and preprocessing of Kalyan market data."""
    
    REQUIRED_COLUMNS = ['date', 'open_panel', 'jodi', 'close_panel', 'sangam']

    def __init__(self, data_path: str = 'data/kalyan.csv'):
        self.data_path = Path(data_path)

    def load_data(self) -> pd.DataFrame:
        """Loads data from CSV, falling back to dummy data if missing."""
        if not self.data_path.exists():
            return self._generate_dummy_data()

        try:
            df = pd.read_csv(self.data_path)
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Basic validation/mapping
            if 'panel' in df.columns and 'sangam' not in df.columns:
                df.rename(columns={'panel': 'sangam'}, inplace=True)
            
            # Ensure jodi is string
            if 'jodi' in df.columns:
                df['jodi'] = df['jodi'].astype(str).str.zfill(2)

            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Validate required columns
            for col in self.REQUIRED_COLUMNS:
                if col not in df.columns:
                    # Try to derive missing columns if possible
                    if col == 'jodi' and 'open' in df.columns and 'close' in df.columns:
                        df['jodi'] = df['open'].astype(str) + df['close'].astype(str)
                        df['jodi'] = df['jodi'].str.zfill(2)
            
            return df
        except Exception as e:
            print(f"Error loading data: {e}. Falling back to dummy data.")
            return self._generate_dummy_data()

    def _generate_dummy_data(self, days: int = 365) -> pd.DataFrame:
        """Generates realistic dummy data for testing."""
        start_date = datetime.now() - timedelta(days=days)
        data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            if date.weekday() == 6: continue # Skip Sundays
            
            open_p = "".join(sorted([str(random.randint(0, 9)) for _ in range(3)]))
            close_p = "".join(sorted([str(random.randint(0, 9)) for _ in range(3)]))
            
            # Simple digit from panel: last digit of sum
            open_digit = str(sum(int(d) for d in open_p) % 10)
            close_digit = str(sum(int(d) for d in close_p) % 10)
            
            jodi = open_digit + close_digit
            data.append({
                'date': date,
                'open_panel': open_p,
                'jodi': jodi,
                'close_panel': close_p,
                'sangam': f"{open_p}-{close_p}"
            })
        
        df = pd.DataFrame(data)
        # Save dummy data for next time
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(self.data_path, index=False)
        return df

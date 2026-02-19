from datetime import datetime, timedelta
from typing import Any, Dict, List

import pandas as pd


class KalyanEngine:
    """
    Core engine for Kalyan Matka chart parsing, data preprocessing, and analysis integration.
    Handles loading, cleaning, and structuring historical Kalyan data.
    """

    def __init__(self, data_path: str = 'data/kalyan.csv'):
        self.data_path = data_path
        self.df = self._load_and_preprocess_data()
        if self.df is None:
            # Fallback to an empty DataFrame if it somehow ends up None
            self.df = pd.DataFrame()

    def _load_and_preprocess_data(self) -> pd.DataFrame:
        """
        Loads Kalyan data from a CSV file, handles missing files by generating dummy data,
        and preprocesses it.
        """
        try:
            df = pd.read_csv(self.data_path, dtype={'jodi': str, 'open': str, 'close': str})
            # Ensure column names are standardized
            df.columns = [col.strip().lower().replace(' ', '_') for col in df.columns]
            
            # Migration support: Rename 'panel' to 'sangam' if 'panel' exists and 'sangam' does not
            if "panel" in df.columns and "sangam" not in df.columns:
                df.rename(columns={"panel": "sangam"}, inplace=True)
            
            # Expected columns: 'date', 'open', 'sangam', 'close', 'jodi'
            # If 'jodi' is missing, create it from 'open' and 'close'
            if 'jodi' not in df.columns and 'open' in df.columns and 'close' in df.columns:
                df['jodi'] = df['open'].astype(str) + df['close'].astype(str)
            
            # If 'sangam' is missing, create it from 'open' and 'close' (assuming single sangam for simplicity)
            if 'sangam' not in df.columns and 'open' in df.columns and 'close' in df.columns:
                df['sangam'] = df['open'].astype(str) + '-' + df['close'].astype(str) # Placeholder, actual sangam logic is complex

            # Convert 'date' to datetime objects
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(by='date').reset_index(drop=True)
            
            # Split 'sangam' into 'open_sangam' and 'close_sangam'
            if 'sangam' in df.columns:
                # Handle cases where sangam might be empty or malformed
                # Use regex=False to avoid FutureWarning
                split_sangam = df['sangam'].astype(str).str.split('-', expand=True)
                df['open_sangam'] = split_sangam[0].fillna('')
                df['close_sangam'] = split_sangam[1].fillna('')

            # Validate essential columns
            required_cols = ['date', 'open', 'close', 'jodi']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"Missing one or more required columns: {required_cols}")

            # Convert 'jodi' to string type to ensure consistency
            df['jodi'] = df['jodi'].astype(str)
            return df
        except FileNotFoundError:
            print(f"Warning: Data file not found at {self.data_path}. Generating dummy data.")
            dummy_df = self._generate_dummy_data()
            return dummy_df
        except Exception as e:
            print(f"Error loading or preprocessing data: {e}")
            print("Attempting to generate dummy data as a fallback.")
            try:
                dummy_df = self._generate_dummy_data()
                return dummy_df
            except Exception as dummy_e:
                print(f"Error generating dummy data: {dummy_e}")
                return pd.DataFrame() # Return empty DataFrame on critical failure

    def _generate_dummy_data(self, start_date: str = '2025-01-01', num_days: int = 365) -> pd.DataFrame:
        """
        Generates dummy Kalyan data for demonstration and testing purposes.
        """
        dates = [datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=i) for i in range(num_days)]
        data = []
        for d in dates:
            if d.weekday() < 6: # Assuming no results on Sunday
                open_digit = str(self._generate_random_digit())
                close_digit = str(self._generate_random_digit())
                jodi = open_digit + close_digit
                
                # Generate open_panel and close_panel (3 digits each)
                open_panel_digits = sorted([self._generate_random_digit() for _ in range(3)])
                open_panel = ''.join(map(str, open_panel_digits))
                close_panel_digits = sorted([self._generate_random_digit() for _ in range(3)])
                close_panel = ''.join(map(str, close_panel_digits))
                sangam = f"{open_panel}-{close_panel}"
            else:
                open_digit = ""
                close_digit = ""
                jodi = ""
                sangam = ""
                open_panel = ""
                close_panel = ""
            
            data.append({
                'date': d,
                'open': open_digit,
                'close': close_digit,
                'jodi': jodi,
                'sangam': sangam,
                'open_panel': open_panel,
                'close_panel': close_panel
            })
        
        df = pd.DataFrame(data)
        # Save dummy data to the expected path for future runs
        try:
            df.to_csv(self.data_path, index=False)
            print(f"Dummy data generated and saved to {self.data_path}")
        except Exception as e:
            print(f"Could not save dummy data to {self.data_path}: {e}")
        return df

    def _generate_random_digit(self) -> int:
        """Generates a random digit between 0 and 9."""
        return pd.Series([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]).sample(1).iloc[0]

    def get_historical_data(self) -> pd.DataFrame:
        """Returns the preprocessed historical data."""
        return self.df

    def get_latest_data(self, n: int = 1) -> pd.DataFrame:
        """Returns the latest N entries from the historical data."""
        return self.df.tail(n)

    def get_data_for_date(self, target_date: datetime) -> pd.DataFrame:
        """Returns data for a specific date."""
        return self.df[self.df['date'] == target_date]

    def get_data_up_to_date(self, target_date: datetime) -> pd.DataFrame:
        """Returns data up to a specific date."""
        return self.df[self.df['date'] <= target_date]

    def get_data_since_date(self, target_date: datetime) -> pd.DataFrame:
        """Returns data since a specific date."""
        return self.df[self.df['date'] >= target_date]

    def get_all_jodis(self) -> List[str]:
        """Returns a list of all unique Jodis present in the data."""
        return self.df['jodi'].dropna().unique().tolist()

    def get_all_digits(self) -> List[int]:
        """Returns a list of all unique single digits (open/close) present in the data."""
        open_digits = self.df['open'].dropna().astype(int).unique().tolist()
        close_digits = self.df['close'].dropna().astype(int).unique().tolist()
        return sorted(list(set(open_digits + close_digits)))

    def get_all_sangams(self) -> List[str]:
        """Returns a list of all unique Sangams present in the data."""
        return self.df['sangam'].dropna().unique().tolist()

    def get_top_picks(self, analysis_results: Dict[str, Any]) -> List[str]:
        """
        Placeholder for generating top picks based on analysis results.
        Currently returns dummy values.
        """
        # In a real implementation, this would use analysis_results
        # (hot/cold digits/jodis, due cycles, exhausted numbers)
        # to apply a weighted scoring system and generate actual predictions.
        
        # For now, returning some dummy top picks
        return ["35", "59", "76"]

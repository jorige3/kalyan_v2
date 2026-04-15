#!/usr/bin/env python3
import os
import sys
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / 'data' / 'kalyan.csv'
URL = 'https://dpboss.boston/panel-chart-record/kalyan.php?full_chart'

def parse_date_range(date_str):
    """
    Parses the '31/12/2012to5/01/2013' format.
    Returns the start date (Monday) as a datetime object.
    """
    clean_date = date_str.split('to')[0]
    try:
        return datetime.strptime(clean_date, '%d/%m/%Y')
    except ValueError:
        return None

def parse_kalyan_table(html):
    """
    Parses the 19-column DPBoss table structure:
    [DateRange, Mon_Open, Mon_Jodi, Mon_Close, Tue_Open, Tue_Jodi, Tue_Close, ...]
    """
    soup = BeautifulSoup(html, 'lxml')
    table = soup.find('table')
    if not table:
        return []

    rows = table.find_all('tr')
    extracted_data = []

    # Skip header (Row 0), process recent rows
    for row in rows[1:]:
        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
        
        # We expect 19 columns for a full week (Date + 6 days * 3 parts)
        if len(cells) < 19:
            continue

        base_date = parse_date_range(cells[0])
        if not base_date:
            continue

        # Mapping days to their column indices for (Open, Jodi, Close)
        # Mon: 1,2,3 | Tue: 4,5,6 | Wed: 7,8,9 | Thu: 10,11,12 | Fri: 13,14,15 | Sat: 16,17,18
        days_map = [
            (0, 1, 2, 3),   # Monday
            (1, 4, 5, 6),   # Tuesday
            (2, 7, 8, 9),   # Wednesday
            (3, 10, 11, 12),# Thursday
            (4, 13, 14, 15),# Friday
            (5, 16, 17, 18) # Saturday
        ]

        for offset, op_idx, jodi_idx, cl_idx in days_map:
            current_date = (base_date + timedelta(days=offset)).strftime('%Y-%m-%d')
            jodi = cells[jodi_idx]
            
            # Skip if jodi is empty or placeholders
            if not jodi or jodi in ['**', '***', '']:
                continue
                
            extracted_data.append({
                'date': current_date,
                'open_panel': cells[op_idx],
                'jodi': jodi,
                'close_panel': cells[cl_idx],
                'sangam': f"{cells[op_idx]}-{cells[cl_idx]}"
            })

    return extracted_data

def scrape_kalyan():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0'}
    
    try:
        logger.info(f"Fetching {URL}...")
        resp = requests.get(URL, headers=headers, timeout=20)
        resp.raise_for_status()
        logger.info("Page fetched successfully.")
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return False

    new_entries = parse_kalyan_table(resp.text)
    if not new_entries:
        logger.warning("No valid data rows found.")
        return False

    # Create DataFrame from scraped data
    new_df = pd.DataFrame(new_entries)
    
    # Load existing data to merge
    if DATA_FILE.exists():
        old_df = pd.read_csv(DATA_FILE)
        # Ensure date columns are strings for comparison
        old_df['date'] = old_df['date'].astype(str)
        new_df['date'] = new_df['date'].astype(str)
        
        # Merge and keep most recent
        final_df = pd.concat([old_df, new_df]).drop_duplicates(subset=['date'], keep='last')
    else:
        final_df = new_df

    # Sort by date
    final_df = final_df.sort_values('date')

    # Save
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(DATA_FILE, index=False)
    
    logger.info(f"Updated {DATA_FILE}. Total records: {len(final_df)}")
    return True

if __name__ == "__main__":
    if scrape_kalyan():
        print("Scrape completed successfully.")
    else:
        print("Scrape failed.")
        sys.exit(1)

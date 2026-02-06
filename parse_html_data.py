#!/usr/bin/env python3
"""
Parse the concatenated HTML table data from CBSL Data Library.
These files have all data concatenated without proper delimiters.

This script uses regex patterns to extract the structured data.

Key insight: The CBSL Data Library exports HTML with data in a weird format where
the actual values are in a concatenated string in the first table, not in proper cells.
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

EXTERNAL_DIR = Path("data/external")
MANUAL_DIR = Path("data/manual_extraction")


def parse_iip_data():
    """
    Parse International Investment Position data.
    
    The raw data has format:
    - Header: "Item NameUnitScale2005-Q12005-Q2..." 
    - Series: "1  Series Name  USDMillions value1value2value3..."
    """
    print("\n" + "="*70)
    print("PARSING: International Investment Position")
    print("="*70)
    
    raw_path = EXTERNAL_DIR / "iip_quarterly_raw.csv"
    
    with open(raw_path, 'r') as f:
        content = f.read()
    
    # Extract the data line (line 2)
    lines = content.strip().split('\n')
    data_line = lines[1].strip('"')
    
    # Extract quarters from header
    # Pattern: 2005-Q1, 2005-Q2, etc.
    quarter_pattern = r'(\d{4}-Q[1-4])'
    quarters = re.findall(quarter_pattern, data_line)
    print(f"  Found {len(quarters)} quarters: {quarters[0]} to {quarters[-1]}")
    
    # Define the series we want to extract
    series_patterns = {
        'iip_assets': (
            r'International Investment Position \(IIP\) - Assets\s+USDMillions\s+([\d,.\s]+?)(?=International|$)',
            'USD Millions'
        ),
        'portfolio_assets': (
            r'IIP- Portfolio Investment - Assets\s+USDMillions\s+([\d,.\s]+?)(?=\d\s+IIP -|International|$)',
            'USD Millions'
        ),
        'portfolio_liabilities': (
            r'IIP - Portfolio Investment - Liabilities\s+USDMillions\s+([\d,.\s]+?)(?=International|$)',
            'USD Millions'
        ),
        'gross_reserves': (
            r'Grosss Official Reserves \(IIP - Reserve Assets\)\s+USDMillions([\d,.\s]+?)(?=\d\s+Gross Official|$)',
            'USD Millions'
        ),
        'import_cover_months': (
            r'Gross Official reserves - Months of Imports\s+months\s+([\d,.\s]+?)(?="|$)',
            'months'
        ),
    }
    
    results = {'quarter': quarters}
    
    for series_name, (pattern, unit) in series_patterns.items():
        match = re.search(pattern, data_line, re.IGNORECASE)
        if match:
            values_str = match.group(1)
            # Parse values - they're concatenated without delimiters
            # Values look like: "9,455.9010,458.9011,750..."
            # Need to split on pattern: number followed by another number
            values = parse_concatenated_values(values_str, len(quarters))
            results[series_name] = values
            print(f"  ✓ {series_name}: {len(values)} values extracted")
        else:
            print(f"  ✗ {series_name}: Pattern not found")
            results[series_name] = [np.nan] * len(quarters)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convert quarter to date
    df['date'] = df['quarter'].apply(quarter_to_date)
    df = df.drop('quarter', axis=1)
    
    # Reorder columns
    cols = ['date'] + [c for c in df.columns if c != 'date']
    df = df[cols]
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"\n  Final shape: {df.shape}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\n  Sample (last 10 rows):")
    print(df.tail(10).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "iip_quarterly_clean.csv"
    df.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return df


def parse_money_supply_data():
    """
    Parse Money Supply data (M2, M2b, M4, Net Foreign Assets).
    
    Monthly data from 2005-Jan to 2017-Dec.
    """
    print("\n" + "="*70)
    print("PARSING: Money Supply Data")
    print("="*70)
    
    raw_path = EXTERNAL_DIR / "money_supply_raw.csv"
    
    with open(raw_path, 'r') as f:
        content = f.read()
    
    # Extract the data line
    lines = content.strip().split('\n')
    data_line = lines[1].strip('"')
    
    # Extract months from header
    # Pattern: 2005-Jan, 2005-Feb, etc.
    month_pattern = r'(\d{4})-([A-Z][a-z]{2})'
    months_raw = re.findall(month_pattern, data_line)
    months = [f"{y}-{m}" for y, m in months_raw]
    print(f"  Found {len(months)} months: {months[0]} to {months[-1]}")
    
    # Define series patterns
    # The data format: "1  Reserve Money LKRmillion value1value2..."
    series_patterns = {
        'reserve_money': (
            r'Reserve Money\s+LKRmillion\s+([\d,.\s]+?)(?=\d\s+Broad Money Supply M2|$)',
            'LKR Million'
        ),
        'broad_money_m2': (
            r'Broad Money Supply M2\s+LKRmillion\s+([\d,.\s]+?)(?=\d\s+Broad Money M2b|$)',
            'LKR Million'
        ),
        'broad_money_m2b': (
            r'Broad Money M2b\s+LKRmillion\s+([\d,.\s]+?)(?=\d\s+Net Foreign Assets|$)',
            'LKR Million'
        ),
        'net_foreign_assets': (
            r'Net Foreign Assets\s+LKRmillion\s+([\d,.\s\(\)\-]+?)(?=\d\s+Broad Money Supply M4|$)',
            'LKR Million'
        ),
        'broad_money_m4': (
            r'Broad Money Supply M4\s+LKRmillion\s+([\d,.\s]+?)(?=\d\s+ReserveMoney|$)',
            'LKR Million'
        ),
    }
    
    results = {'month': months}
    
    for series_name, (pattern, unit) in series_patterns.items():
        match = re.search(pattern, data_line)
        if match:
            values_str = match.group(1)
            values = parse_concatenated_values_money(values_str, len(months), series_name)
            results[series_name] = values
            print(f"  ✓ {series_name}: {len(values)} values extracted")
        else:
            print(f"  ✗ {series_name}: Pattern not found")
            results[series_name] = [np.nan] * len(months)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convert month to date
    df['date'] = pd.to_datetime(df['month'], format='%Y-%b')
    df = df.drop('month', axis=1)
    
    # Reorder columns
    cols = ['date'] + [c for c in df.columns if c != 'date']
    df = df[cols]
    
    # Sort by date
    df = df.sort_values('date').reset_index(drop=True)
    
    print(f"\n  Final shape: {df.shape}")
    print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"\n  Sample (last 10 rows):")
    print(df.tail(10).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "money_supply_monthly_clean.csv"
    df.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return df


def parse_concatenated_values(values_str, expected_count):
    """
    Parse concatenated numeric values like "9,455.9010,458.9011,750..."
    
    Strategy: Values have format X,XXX.XX and are concatenated.
    We look for the pattern: digits with optional comma and decimal.
    """
    # Clean up the string
    values_str = values_str.strip()
    
    # For IIP data, values are like "9,455.90" or "11,750" concatenated
    # Try to split on the pattern of a number ending followed by a new number starting
    
    # Pattern: Match numbers with format like 1,234.56 or 1234.56 or 1234
    # The tricky part is they're concatenated without space
    
    # Strategy: Since we know expected count, try to split intelligently
    # Values seem to have 2 decimal places mostly
    
    # Try regex to find all numbers
    # Pattern: optional negative, digits with optional comma, optional decimal
    pattern = r'(-?[\d,]+\.?\d*)'
    raw_values = re.findall(pattern, values_str)
    
    # Clean and convert
    values = []
    for v in raw_values:
        try:
            clean_v = v.replace(',', '')
            if clean_v and clean_v != '.':
                values.append(float(clean_v))
        except ValueError:
            continue
    
    # If we got more values than expected, the parsing is wrong
    # Try alternative approach
    if len(values) != expected_count:
        # Try splitting on pattern where decimal is followed by digit
        # e.g., "9,455.9010,458.90" -> split after ".90" when followed by "10,"
        values = split_by_decimal_pattern(values_str, expected_count)
    
    # Pad with NaN if needed
    while len(values) < expected_count:
        values.append(np.nan)
    
    return values[:expected_count]


def split_by_decimal_pattern(s, expected_count):
    """
    Try to split concatenated values by finding decimal patterns.
    Values have 2 decimal places, so we split after .XX when followed by a digit.
    """
    # Clean string
    s = s.strip()
    
    # Pattern: number with 2 decimal places
    # Insert delimiter after .XX when followed by digit
    # e.g., "9,455.9010,458.90" -> "9,455.90|10,458.90"
    
    # This is tricky because values might not all have 2 decimals
    # Let's try a different approach: known value lengths
    
    values = []
    current = ""
    decimal_count = 0
    
    for char in s:
        current += char
        if char == '.':
            decimal_count = 0
        elif char.isdigit() and '.' in current:
            decimal_count += 1
            # Check if we've reached end of a value (2 decimals)
            if decimal_count >= 2:
                # Look ahead - if next char is digit (start of new value)
                # Actually, we need the full string context
                pass
    
    # Simpler approach: use the fact that values are ~X,XXX.XX format
    # Split on pattern where we see .XX followed by digit or digit,
    import re
    
    # Insert a delimiter after 2 decimal digits when followed by digit
    # Pattern: (\.\d{2})(\d) -> \1|\2
    delimited = re.sub(r'(\.\d{2})(\d)', r'\1|\2', s)
    
    # Also handle cases without decimal
    # If we see pattern like "11,750" (no decimal) followed by another number
    # Look for ,XXX followed by digit without . between
    
    parts = delimited.split('|')
    
    for p in parts:
        p = p.strip().replace(',', '')
        if p:
            try:
                values.append(float(p))
            except ValueError:
                continue
    
    return values


def parse_concatenated_values_money(values_str, expected_count, series_name=''):
    """
    Parse concatenated money supply values.
    
    These can include negative values in parentheses like (27760.62)
    """
    # Clean up
    values_str = values_str.strip()
    
    # Replace parentheses with negative sign
    # (27760.62) -> -27760.62
    values_str = re.sub(r'\((\d+[\d,]*\.?\d*)\)', r'-\1', values_str)
    
    # For money supply, values are larger (millions) like "1,288,163" or "263,769.59"
    # Split using decimal pattern
    delimited = re.sub(r'(\.\d{2})(\d)', r'\1|\2', values_str)
    
    # Also need to handle integer values (no decimal)
    # If we see pattern like "1,288,1631,304,602" we need to split
    # This is 1,288,163 followed by 1,304,602
    
    parts = delimited.split('|')
    
    values = []
    for p in parts:
        p = p.strip().replace(',', '')
        if p:
            try:
                values.append(float(p))
            except ValueError:
                continue
    
    # If still wrong count, try character-by-character parsing
    if len(values) != expected_count:
        values = smart_split_values(values_str, expected_count)
    
    # Pad with NaN if needed
    while len(values) < expected_count:
        values.append(np.nan)
    
    return values[:expected_count]


def smart_split_values(s, expected_count):
    """
    Smart splitting when other methods fail.
    Uses expected count to determine approximate value length.
    """
    s = s.strip().replace(' ', '')
    s = re.sub(r'\((\d+[\d,]*\.?\d*)\)', r'-\1', s)  # Handle negatives
    
    # Estimate average value length
    avg_len = len(s) // expected_count
    
    values = []
    current = ""
    
    for i, char in enumerate(s):
        current += char
        
        # Check if we should split here
        should_split = False
        
        # Split after decimal + 2 digits
        if len(current) >= 3 and current[-3] == '.' and current[-2:].replace('-', '').isdigit():
            # Check if next char looks like start of new number
            if i + 1 < len(s):
                next_char = s[i + 1]
                if next_char.isdigit() or next_char == '-':
                    should_split = True
        
        if should_split:
            try:
                val = float(current.replace(',', ''))
                values.append(val)
                current = ""
            except ValueError:
                pass
    
    # Don't forget last value
    if current:
        try:
            val = float(current.replace(',', ''))
            values.append(val)
        except ValueError:
            pass
    
    return values


def quarter_to_date(q):
    """Convert quarter string like '2005-Q1' to date."""
    year, qtr = q.split('-Q')
    month = int(qtr) * 3  # End of quarter month
    return pd.Timestamp(year=int(year), month=month, day=1)


def main():
    print("\n" + "="*70)
    print("PARSING CBSL HTML DATA FILES")
    print("="*70)
    
    # Parse IIP
    iip_df = parse_iip_data()
    
    # Parse Money Supply
    money_df = parse_money_supply_data()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"\nIIP Data:")
    print(f"  Records: {len(iip_df)}")
    print(f"  Columns: {list(iip_df.columns)}")
    print(f"  Date range: {iip_df['date'].min()} to {iip_df['date'].max()}")
    
    print(f"\nMoney Supply Data:")
    print(f"  Records: {len(money_df)}")
    print(f"  Columns: {list(money_df.columns)}")
    print(f"  Date range: {money_df['date'].min()} to {money_df['date'].max()}")


if __name__ == "__main__":
    main()

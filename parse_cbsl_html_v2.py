#!/usr/bin/env python3
"""
Parse CBSL Data Library HTML exports - Version 2

These files have data concatenated in a peculiar format. This parser
handles the specific structure of IIP and Money Supply exports.
"""

import re
import pandas as pd
import numpy as np
from pathlib import Path

EXTERNAL_DIR = Path("data/external")
MANUAL_DIR = Path("data/manual_extraction")


def extract_quarters_from_header(header_str):
    """Extract quarter strings like 2005-Q1 from concatenated header."""
    pattern = r'(\d{4}-Q[1-4])'
    quarters = re.findall(pattern, header_str)
    return quarters


def extract_months_from_header(header_str):
    """Extract month strings like 2005-Jan from concatenated header."""
    pattern = r'(\d{4}-[A-Z][a-z]{2})'
    months = re.findall(pattern, header_str)
    return months


def split_concatenated_values(value_str, num_expected, value_type='decimal'):
    """
    Split concatenated numeric values.
    
    The format is like: "9,455.9010,458.9011,750" or "3.303.403.30"
    
    Strategy: Use knowledge of value patterns to split correctly.
    """
    if not value_str or pd.isna(value_str):
        return [np.nan] * num_expected
    
    # Clean up
    value_str = str(value_str).strip()
    
    # Handle negative values in parentheses
    value_str = re.sub(r'\((\d+[\d,]*\.?\d*)\)', r'-\1', value_str)
    
    if value_type == 'small_decimal':
        # Values like "3.303.403.30" - small numbers with 2 decimals
        # Split by finding ".XX" followed by digit
        parts = re.split(r'(?<=\.\d{2})(?=\d)', value_str)
    elif value_type == 'thousands':
        # Values like "9,455.9010,458.90" - thousands with commas
        # Split after ".XX" when followed by digit
        parts = re.split(r'(?<=\.\d{2})(?=\d)', value_str)
    elif value_type == 'millions_int':
        # Values like "1,288,1631,304,602" - millions, sometimes no decimals
        # This is hardest - try multiple approaches
        parts = split_millions(value_str, num_expected)
    else:
        # Default: split on pattern ".XX" followed by digit
        parts = re.split(r'(?<=\.\d{2})(?=\d)', value_str)
    
    # Convert to floats
    values = []
    for p in parts:
        p = p.strip().replace(',', '')
        if p:
            try:
                values.append(float(p))
            except ValueError:
                values.append(np.nan)
    
    # Pad with NaN if needed
    while len(values) < num_expected:
        values.append(np.nan)
    
    return values[:num_expected]


def split_millions(s, num_expected):
    """
    Split large numbers that may or may not have decimals.
    Uses expected count to guide splitting.
    """
    # For large numbers, the pattern is typically X,XXX,XXX.XX or X,XXX,XXX
    # The challenge is distinguishing between values
    
    # First try: split on .XX followed by digit
    parts = re.split(r'(?<=\.\d{2})(?=\d)', s)
    
    if len(parts) == num_expected:
        return parts
    
    # If that didn't work, we have integer values mixed in
    # Try to identify by comma patterns
    
    # Convert to list of chars and identify splits
    # A value boundary often occurs after digit followed by digit,digit
    # e.g., "1,288,1631,304,602" should split to "1,288,163" and "1,304,602"
    
    # This is very heuristic - use expected value magnitude
    avg_len = len(s) // num_expected if num_expected > 0 else 10
    
    result = []
    current = ""
    comma_count = 0
    
    i = 0
    while i < len(s):
        char = s[i]
        current += char
        
        if char == ',':
            comma_count += 1
        
        # Check for split conditions
        should_split = False
        
        # If we're past a decimal with 2+ digits, and see another digit
        if len(current) >= 4:
            if '.' in current:
                # Check if we have .XX at end
                dot_pos = current.rfind('.')
                after_dot = current[dot_pos+1:]
                if len(after_dot) >= 2 and after_dot[:2].isdigit():
                    # We have .XX, check next char
                    if i + 1 < len(s) and s[i+1].isdigit():
                        should_split = True
        
        # Also check for integer->integer transition
        # If current has 2+ commas (like 1,288,163) and next is digit followed by comma
        if comma_count >= 2 and i + 2 < len(s):
            if s[i+1].isdigit() and s[i+2] == ',':
                # Looks like start of new number
                # But verify current looks complete
                if len(current) >= 9:  # X,XXX,XXX minimum
                    should_split = True
        
        if should_split:
            result.append(current)
            current = ""
            comma_count = 0
        
        i += 1
    
    # Don't forget last value
    if current:
        result.append(current)
    
    return result


def parse_iip_data():
    """
    Parse International Investment Position from CBSL HTML export.
    """
    print("\n" + "="*70)
    print("PARSING: International Investment Position (IIP)")
    print("="*70)
    
    # Read the raw concatenated data
    html_path = MANUAL_DIR / "International Investment Position.xls"
    
    tables = pd.read_html(html_path)
    raw_str = str(tables[0].iloc[0, 0])
    
    # Extract quarters
    quarters = extract_quarters_from_header(raw_str)
    print(f"  Found {len(quarters)} quarters: {quarters[0]} to {quarters[-1]}")
    
    # Define series patterns
    # Each series has format: "N  Series Name  USDMillions values..."
    series_defs = [
        ('iip_assets', 
         r'International Investment Position \(IIP\) - Assets\s+USD\s*Millions\s*([\d,.\s]+?)(?=International Investment Position-Portfolio|$)',
         'thousands'),
        ('portfolio_liabilities',
         r'IIP - Portfolio Investment - Liabilities\s+USD\s*Millions\s*([\d,.\s]+?)(?=International Investment Position-Gross|$)',
         'thousands'),
        ('gross_reserves',
         r'Grosss Official Reserves \(IIP - Reserve Assets\)\s+USD\s*Millions([\d,.\s]+?)(?=\d\s+Gross Official reserves - Months|$)',
         'thousands'),
        ('import_cover_months',
         r'Gross Official reserves - Months of Imports\s+months\s*([\d.\s]+?)$',
         'small_decimal'),
    ]
    
    results = {'quarter': quarters}
    
    for name, pattern, val_type in series_defs:
        match = re.search(pattern, raw_str, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            values = split_concatenated_values(val_str, len(quarters), val_type)
            results[name] = values
            non_null = sum(1 for v in values if pd.notna(v) and v != 0)
            print(f"  ✓ {name}: {non_null} non-null values")
        else:
            print(f"  ✗ {name}: Pattern not found")
            results[name] = [np.nan] * len(quarters)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convert quarter to date
    df['date'] = df['quarter'].apply(lambda q: pd.Timestamp(
        year=int(q.split('-Q')[0]),
        month=int(q.split('-Q')[1]) * 3,
        day=1
    ))
    df = df.drop('quarter', axis=1)
    
    # Reorder and sort
    cols = ['date'] + [c for c in df.columns if c != 'date']
    df = df[cols].sort_values('date').reset_index(drop=True)
    
    # Show data coverage
    print(f"\n  Date range: {df['date'].min()} to {df['date'].max()}")
    
    for col in df.columns[1:]:
        valid = df[col].notna() & (df[col] != 0)
        if valid.any():
            first_valid = df.loc[valid, 'date'].min()
            last_valid = df.loc[valid, 'date'].max()
            print(f"    {col}: {first_valid.strftime('%Y-Q%q')} to {last_valid.strftime('%Y-Q%q')} ({valid.sum()} values)")
    
    # Save
    output_path = EXTERNAL_DIR / "iip_quarterly_clean.csv"
    df.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    # Show sample
    print(f"\n  Sample (rows with data):")
    sample = df[df['portfolio_liabilities'].notna()].head(10)
    print(sample.to_string())
    
    return df


def parse_money_supply_data():
    """
    Parse Money Supply data (M2, M2b, NFA) from CBSL HTML export.
    """
    print("\n" + "="*70)  
    print("PARSING: Money Supply Data")
    print("="*70)
    
    html_path = MANUAL_DIR / "reserve_money.xls"
    
    tables = pd.read_html(html_path)
    raw_str = str(tables[0].iloc[0, 0])
    
    # Extract months
    months = extract_months_from_header(raw_str)
    print(f"  Found {len(months)} months: {months[0]} to {months[-1]}")
    
    # Define series patterns
    series_defs = [
        ('reserve_money',
         r'Reserve Money\s+LKR\s*million\s*([\d,.\s]+?)(?=\d\s+Broad Money Supply M2|$)',
         'thousands'),
        ('broad_money_m2',
         r'Broad Money Supply M2\s+LKR\s*million\s*([\d,.\s]+?)(?=\d\s+Broad Money M2b|$)',
         'millions_int'),
        ('broad_money_m2b',
         r'Broad Money M2b\s+LKR\s*million\s*([\d,.\s]+?)(?=\d\s+Net Foreign Assets|$)',
         'millions_int'),
        ('net_foreign_assets',
         r'Net Foreign Assets\s+LKR\s*million\s*([\d,.\s\(\)\-]+?)(?=\d\s+Broad Money Supply M4|$)',
         'thousands'),
    ]
    
    results = {'month': months}
    
    for name, pattern, val_type in series_defs:
        match = re.search(pattern, raw_str, re.IGNORECASE)
        if match:
            val_str = match.group(1)
            values = split_concatenated_values(val_str, len(months), val_type)
            results[name] = values
            non_null = sum(1 for v in values if pd.notna(v))
            print(f"  ✓ {name}: {non_null} non-null values")
        else:
            print(f"  ✗ {name}: Pattern not found")
            results[name] = [np.nan] * len(months)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Convert month to date
    df['date'] = pd.to_datetime(df['month'], format='%Y-%b')
    df = df.drop('month', axis=1)
    
    # Reorder and sort
    cols = ['date'] + [c for c in df.columns if c != 'date']
    df = df[cols].sort_values('date').reset_index(drop=True)
    
    print(f"\n  Date range: {df['date'].min()} to {df['date'].max()}")
    
    # Save
    output_path = EXTERNAL_DIR / "money_supply_monthly_clean.csv"
    df.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    # Show sample
    print(f"\n  Sample (first 12 rows):")
    print(df.head(12).to_string())
    
    return df


def main():
    print("\n" + "="*70)
    print("CBSL HTML DATA PARSER - Version 2")
    print("="*70)
    
    # Parse both files
    iip_df = parse_iip_data()
    money_df = parse_money_supply_data()
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    print("\nIIP Data:")
    print(f"  Records: {len(iip_df)}")
    print(f"  Range: {iip_df['date'].min()} to {iip_df['date'].max()}")
    for col in iip_df.columns[1:]:
        valid = iip_df[col].notna() & (iip_df[col] != 0)
        print(f"    {col}: {valid.sum()} valid values")
    
    print("\nMoney Supply Data:")
    print(f"  Records: {len(money_df)}")
    print(f"  Range: {money_df['date'].min()} to {money_df['date'].max()}")
    for col in money_df.columns[1:]:
        valid = money_df[col].notna()
        print(f"    {col}: {valid.sum()} valid values")


if __name__ == "__main__":
    main()

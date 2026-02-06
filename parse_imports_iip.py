#!/usr/bin/env python3
"""
Parse Monthly Imports and IIP data from CBSL xlsx files.

Files processed:
- table2.04_20251231_e.xlsx: Monthly imports (USD millions)
- International_Investment_Position Q3_2025.xlsx: Quarterly IIP with portfolio liabilities

Created: January 2026
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

MANUAL_DIR = Path("data/manual_extraction")
EXTERNAL_DIR = Path("data/external")


def parse_monthly_imports():
    """
    Parse table2.04 - Monthly Imports (USD millions)
    
    Sheet: "2.04 In USD 2007-2025"
    Structure: Row 4 has dates as datetime, rows 5+ have categories with values
    """
    print("\n" + "="*70)
    print("PARSING: table2.04 - Monthly Imports (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.04_20251231_e.xlsx"
    
    # Read the USD sheet (2007-2025)
    df = pd.read_excel(path, sheet_name="2.04 In USD 2007-2025", header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Row 4 has dates as datetime objects, column 0 has "Category"
    # Find the header row with dates
    header_row = 4
    
    # Parse date columns (columns 1+)
    dates = []
    date_cols = []
    
    for col_idx in range(1, df.shape[1]):
        val = df.iloc[header_row, col_idx]
        if pd.notna(val):
            try:
                if isinstance(val, datetime):
                    dates.append(pd.Timestamp(val))
                    date_cols.append(col_idx)
                elif isinstance(val, pd.Timestamp):
                    dates.append(val)
                    date_cols.append(col_idx)
                else:
                    # Try parsing string - handle formats like "Feb-25 (b)"
                    val_str = str(val).strip()
                    # Remove footnote markers like (a), (b), etc.
                    val_clean = val_str.split('(')[0].strip()
                    
                    # Try different formats
                    parsed = None
                    for fmt in ['%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            parsed = pd.to_datetime(val_clean, format=fmt)
                            break
                        except:
                            continue
                    
                    if parsed is None:
                        parsed = pd.to_datetime(val_clean)
                    
                    dates.append(parsed)
                    date_cols.append(col_idx)
            except:
                continue
    
    print(f"  Found {len(dates)} date columns")
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")
    
    # Find "Total" or "Total Imports" row
    total_row = None
    for row_idx in range(header_row + 1, df.shape[0]):
        label = str(df.iloc[row_idx, 0]).lower().strip()
        if label == 'total' or 'total imports' in label or 'total import' in label:
            total_row = row_idx
            print(f"  Found total row at {row_idx}: {df.iloc[row_idx, 0]}")
            break
    
    if total_row is None:
        # Try finding a row with large values that looks like totals
        print("  Looking for total row by value pattern...")
        for row_idx in range(header_row + 1, df.shape[0]):
            label = str(df.iloc[row_idx, 0]).strip()
            # Check if values are > 500 (total imports should be large)
            sample_val = df.iloc[row_idx, date_cols[0]] if date_cols else None
            if pd.notna(sample_val):
                try:
                    if float(sample_val) > 800:  # Monthly imports typically > 800M USD
                        total_row = row_idx
                        print(f"  Found likely total row at {row_idx}: {label} (value: {sample_val})")
                        break
                except:
                    continue
    
    if total_row is None:
        print("  Could not find total imports row")
        return None
    
    # Extract values
    records = []
    for date, col_idx in zip(dates, date_cols):
        val = df.iloc[total_row, col_idx]
        if pd.notna(val):
            try:
                if isinstance(val, str):
                    val = val.replace(',', '').strip()
                import_val = float(val)
                if import_val > 0:
                    records.append({
                        'date': date,
                        'imports_usd_m': import_val
                    })
            except:
                continue
    
    if not records:
        print("  No records extracted")
        return None
    
    result = pd.DataFrame(records)
    result = result.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    
    print(f"  Records: {len(result)}")
    print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    print(f"\n  Sample (last 12 rows):")
    print(result.tail(12).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "monthly_imports_usd.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_monthly_imports_alt(df, header_row, month_cols):
    """Alternative parsing for different structure."""
    print("  Using alternative parsing method...")
    
    records = []
    
    # Look for rows that have numeric values in month columns
    for row_idx in range(header_row + 1, df.shape[0]):
        # Check if first column looks like a year entry
        first_val = df.iloc[row_idx, 0]
        second_val = df.iloc[row_idx, 1] if df.shape[1] > 1 else None
        
        # Try to find year in first two columns
        year = None
        for val in [first_val, second_val]:
            if pd.notna(val):
                val_str = str(val).strip()
                # Check for "2020    January" pattern
                if len(val_str) >= 4 and val_str[:4].isdigit():
                    potential_year = int(val_str[:4])
                    if 2000 <= potential_year <= 2030:
                        year = potential_year
                        break
        
        if year is None:
            continue
        
        # Check row label for "Total" 
        row_label = ' '.join([str(x).lower() for x in df.iloc[row_idx, :3] if pd.notna(x)])
        if 'total' not in row_label:
            continue
        
        # Extract monthly values
        for month_num, col_idx in month_cols.items():
            val = df.iloc[row_idx, col_idx]
            if pd.notna(val):
                try:
                    if isinstance(val, str):
                        val = val.replace(',', '').strip()
                    import_val = float(val)
                    if import_val > 0:
                        records.append({
                            'date': pd.Timestamp(year=year, month=month_num, day=1),
                            'imports_usd_m': import_val
                        })
                except:
                    continue
    
    if not records:
        return None
    
    result = pd.DataFrame(records)
    result = result.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    return result


def parse_iip_portfolio():
    """
    Parse IIP data for portfolio liabilities.
    
    File: International_Investment_Position Q3_2025.xlsx
    Sheet: "IIP"
    """
    print("\n" + "="*70)
    print("PARSING: IIP - Portfolio Liabilities (USD millions)")
    print("="*70)
    
    # Handle filename with spaces
    path = MANUAL_DIR / "International_Investment_Position               Q3_2025.xlsx"
    
    df = pd.read_excel(path, sheet_name="IIP", header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Find the header row with dates
    date_row = None
    for i in range(min(10, df.shape[0])):
        row_vals = [str(x) for x in df.iloc[i, :] if pd.notna(x)]
        if any('Mar' in v or 'Jun' in v or 'Sep' in v or 'Dec' in v for v in row_vals):
            date_row = i
            break
    
    if date_row is None:
        print("  Could not find date row")
        return None
    
    print(f"  Date row: {date_row}")
    
    # Parse dates from header
    dates = []
    date_cols = []
    
    for col_idx in range(df.shape[1]):
        val = str(df.iloc[date_row, col_idx]).strip()
        if pd.isna(df.iloc[date_row, col_idx]) or val == 'nan':
            continue
        
        # Parse dates like "31st Mar - 2014", "30th Jun - 2024"
        try:
            # Extract components
            if ' - ' in val:
                parts = val.split(' - ')
                if len(parts) == 2:
                    date_part, year_part = parts
                    year = int(year_part.strip())
                    
                    # Map month
                    month_map = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                                'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
                    
                    month = None
                    for m_name, m_num in month_map.items():
                        if m_name in date_part:
                            month = m_num
                            break
                    
                    if month and 2000 <= year <= 2030:
                        dates.append(pd.Timestamp(year=year, month=month, day=1))
                        date_cols.append(col_idx)
        except:
            continue
    
    print(f"  Found {len(dates)} date columns")
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")
    
    # Find key rows: Portfolio Investment Liabilities, Total Liabilities
    key_rows = {}
    
    for row_idx in range(date_row + 1, min(100, df.shape[0])):
        # Check columns 0-2 for labels
        label = ' '.join([str(x).lower() for x in df.iloc[row_idx, :3] if pd.notna(x)])
        
        if 'portfolio' in label and 'liabilit' in label:
            key_rows['portfolio_liabilities'] = row_idx
        elif 'equity' in label and 'investment fund' in label.lower():
            if 'liabilit' not in key_rows:
                key_rows['portfolio_equity'] = row_idx
        elif 'debt' in label and 'securities' in label:
            key_rows['portfolio_debt'] = row_idx
        elif 'total' in label and 'liabilit' in label:
            key_rows['total_liabilities'] = row_idx
        elif 'reserve asset' in label:
            key_rows['reserve_assets'] = row_idx
    
    print(f"  Key rows found: {list(key_rows.keys())}")
    
    # Extract data
    records = []
    
    for date, col_idx in zip(dates, date_cols):
        record = {'date': date}
        
        for series_name, row_idx in key_rows.items():
            val = df.iloc[row_idx, col_idx]
            if pd.notna(val):
                try:
                    if isinstance(val, str):
                        val = val.replace(',', '').strip()
                    record[series_name] = float(val)
                except:
                    record[series_name] = np.nan
            else:
                record[series_name] = np.nan
        
        records.append(record)
    
    result = pd.DataFrame(records)
    result = result.sort_values('date').reset_index(drop=True)
    
    print(f"  Records: {len(result)}")
    print(f"  Columns: {list(result.columns)}")
    print(f"\n  Sample (last 10 rows):")
    print(result.tail(10).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "iip_quarterly_2025.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def parse_monthly_exports():
    """
    Parse table2.02 - Monthly Exports (USD millions)
    
    Sheet: "2.02 In USD 2007-2025"
    Structure: Same as imports - dates in row 4, total exports in row 45
    """
    print("\n" + "="*70)
    print("PARSING: table2.02 - Monthly Exports (USD millions)")
    print("="*70)
    
    path = MANUAL_DIR / "table2.02_20251231_e.xlsx"
    
    if not path.exists():
        print("  File not found")
        return None
    
    # Read the USD sheet (2007-2025)
    df = pd.read_excel(path, sheet_name="2.02 In USD 2007-2025", header=None)
    
    print(f"  Raw shape: {df.shape}")
    
    # Row 4 has dates as datetime objects
    header_row = 4
    
    # Parse date columns (columns 1+)
    dates = []
    date_cols = []
    
    for col_idx in range(1, df.shape[1]):
        val = df.iloc[header_row, col_idx]
        if pd.notna(val):
            try:
                if isinstance(val, datetime):
                    dates.append(pd.Timestamp(val))
                    date_cols.append(col_idx)
                elif isinstance(val, pd.Timestamp):
                    dates.append(val)
                    date_cols.append(col_idx)
                else:
                    # Try parsing string - handle formats like "Feb-25 (b)"
                    val_str = str(val).strip()
                    val_clean = val_str.split('(')[0].strip()
                    
                    parsed = None
                    for fmt in ['%b-%y', '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            parsed = pd.to_datetime(val_clean, format=fmt)
                            break
                        except:
                            continue
                    
                    if parsed is None:
                        parsed = pd.to_datetime(val_clean)
                    
                    dates.append(parsed)
                    date_cols.append(col_idx)
            except:
                continue
    
    print(f"  Found {len(dates)} date columns")
    if dates:
        print(f"  Date range: {min(dates)} to {max(dates)}")
    
    # Find "Total exports" row
    total_row = None
    for row_idx in range(header_row + 1, df.shape[0]):
        label = str(df.iloc[row_idx, 0]).lower().strip()
        if 'total export' in label or label == 'total exports':
            total_row = row_idx
            print(f"  Found total row at {row_idx}: {df.iloc[row_idx, 0]}")
            break
    
    if total_row is None:
        print("  Could not find total exports row")
        return None
    
    # Extract values
    records = []
    for date, col_idx in zip(dates, date_cols):
        val = df.iloc[total_row, col_idx]
        if pd.notna(val):
            try:
                if isinstance(val, str):
                    val = val.replace(',', '').strip()
                export_val = float(val)
                if export_val > 0:
                    records.append({
                        'date': date,
                        'exports_usd_m': export_val
                    })
            except:
                continue
    
    if not records:
        print("  No records extracted")
        return None
    
    result = pd.DataFrame(records)
    result = result.drop_duplicates(subset=['date']).sort_values('date').reset_index(drop=True)
    
    print(f"  Records: {len(result)}")
    print(f"  Date range: {result['date'].min()} to {result['date'].max()}")
    print(f"\n  Sample (last 12 rows):")
    print(result.tail(12).to_string())
    
    # Save
    output_path = EXTERNAL_DIR / "monthly_exports_usd.csv"
    result.to_csv(output_path, index=False)
    print(f"\n  Saved to: {output_path}")
    
    return result


def main():
    print("\n" + "="*70)
    print("PARSING IMPORTS, EXPORTS AND IIP DATA")
    print("="*70)
    
    EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    # Parse imports
    results['imports'] = parse_monthly_imports()
    
    # Parse exports
    results['exports'] = parse_monthly_exports()
    
    # Parse IIP
    results['iip'] = parse_iip_portfolio()
    
    # Summary
    print("\n" + "="*70)
    print("PARSING SUMMARY")
    print("="*70)
    
    for name, df in results.items():
        if df is not None and len(df) > 0:
            print(f"  ✓ {name}: {len(df)} records, {df['date'].min().strftime('%Y-%m')} to {df['date'].max().strftime('%Y-%m')}")
        else:
            print(f"  ✗ {name}: No data")
    
    return results


if __name__ == "__main__":
    main()

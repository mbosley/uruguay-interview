#!/usr/bin/env python3
"""
Export all SQL database tables to CSV files and combine into Excel spreadsheet.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

def get_all_tables(conn):
    """Get list of all tables in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    return tables

def export_table_to_df(conn, table_name):
    """Export a table to pandas DataFrame."""
    query = f"SELECT * FROM {table_name}"
    df = pd.read_sql_query(query, conn)
    return df

def main():
    # Database path
    db_path = "data/uruguay_interviews.db"
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    # Create output directory
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_dir = output_dir / "csv"
    csv_dir.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    
    try:
        # Get all tables
        tables = get_all_tables(conn)
        print(f"Found {len(tables)} tables in database")
        
        # Dictionary to store DataFrames for Excel export
        dataframes = {}
        
        # Export each table
        for table in tables:
            print(f"\nExporting table: {table}")
            
            # Get data
            df = export_table_to_df(conn, table)
            print(f"  - Rows: {len(df)}")
            print(f"  - Columns: {list(df.columns)}")
            
            # Save to CSV
            csv_path = csv_dir / f"{table}.csv"
            df.to_csv(csv_path, index=False)
            print(f"  - Saved to: {csv_path}")
            
            # Store for Excel export
            dataframes[table] = df
        
        # Create Excel file with all tables as sheets
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = output_dir / f"uruguay_interviews_database_{timestamp}.xlsx"
        
        print(f"\nCreating Excel file: {excel_path}")
        with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
            for table_name, df in dataframes.items():
                # Excel sheet names have a 31 character limit
                sheet_name = table_name[:31]
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Get the worksheet
                worksheet = writer.sheets[sheet_name]
                
                # Auto-adjust column widths
                for i, col in enumerate(df.columns):
                    # Find max length in this column
                    max_len = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    ) + 2
                    # Cap at reasonable width
                    max_len = min(max_len, 50)
                    worksheet.set_column(i, i, max_len)
        
        print(f"\nExcel file created successfully!")
        
        # Print summary
        print(f"\nDatabase Export Summary:")
        print(f"=" * 50)
        for table_name, df in dataframes.items():
            print(f"{table_name}: {len(df)} rows, {len(df.columns)} columns")
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
import logging
from http import requests
from pprint import pprint
import preservationeval

# Set up logging to see the validation messages
logging.basicConfig(level=logging.INFO)

def example_usage():
    """Example of how to use the table fetching and validation code."""
    
    # 1. Basic fetching and examining table information
    try:
        # Fetch tables from the website
        table_info, tables = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")
        
        # Print information about each table
        print("\nTable Information:")
        print("=================")
        for table_type, info in table_info.items():
            print(f"\n{info}")
            
            # Get the actual table data
            table_data = tables[table_type]
            
            # Print some statistics about the table
            print(f"  Data statistics:")
            print(f"    Shape: {table_data.shape}")
            print(f"    Min value: {table_data.min():.1f}")
            print(f"    Max value: {table_data.max():.1f}")
            print(f"    Mean value: {table_data.mean():.1f}")
    
    except requests.RequestException as e:
        print(f"Failed to download tables: {e}")
        return
    except ValueError as e:
        print(f"Failed to parse tables: {e}")
        return

    # 2. Examining specific regions of the tables
    print("\nExample Values:")
    print("==============")
    
    # Look at center values of each table
    for table_type, table in tables.items():
        mid_temp_idx = table.shape[0] // 2
        mid_rh_idx = table.shape[1] // 2
        
        info = table_info[table_type]
        mid_temp = (info.temp_min + info.temp_max) / 2
        mid_rh = (info.rh_min + info.rh_max) / 2
        
        print(f"\n{table_type.value}:")
        print(f"  Value at {mid_temp}°C, {mid_rh}%RH: "
              f"{table[mid_temp_idx, mid_rh_idx]:.1f}")

    # 3. Demonstrate table ranges and validation
    print("\nTable Ranges and Validation:")
    print("==========================")
    for table_type, info in table_info.items():
        print(f"\n{table_type.value}:")
        print(f"  Temperature range: {info.temp_min}°C to {info.temp_max}°C")
        print(f"  Humidity range: {info.rh_min}% to {info.rh_max}%")
        print(f"  Array shape: {tables[table_type].shape}")
        print(f"  Expected size: {info.total_size}")

if __name__ == "__main__":
    example_usage()
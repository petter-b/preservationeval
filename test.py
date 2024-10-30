import logging
import requests
import sys
from pprint import pprint
from tables import fetch_and_validate_tables

# Set up logging to both file and console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def example_usage():
    """Example of how to use the table fetching and validation code."""
    
    logger.debug("Starting example_usage function. Debug level == DEBUG")
    
    try:
        logger.debug("Attempting to fetch tables from website")
        
        # Fetch tables from the website
        table_info, tables = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")
        
        # Print information about each table
        print("\nTable Information:")
        print("=================")
        for table_type, info in table_info.items():
            print(f"\nTable: {table_type.value}")
            print(f"Temperature range: {info.temp_min}°C to {info.temp_max}°C")
            print(f"RH range: {info.rh_min}% to {info.rh_max}%")
            print(f"Dimensions: {info.temp_size} × {info.rh_size} = {info.total_size}")
            
            # Get the actual table data
            if table_type in tables:
                table_data = tables[table_type]
                print(f"Actual data shape: {table_data.shape}")
                print(f"Data statistics:")
                print(f"  Min value: {table_data.min():.1f}")
                print(f"  Max value: {table_data.max():.1f}")
                print(f"  Mean value: {table_data.mean():.1f}")
                
                # Print a small sample of the table
                print("\nSample data (top-left corner):")
                print(table_data[:5, :5])
            else:
                print("No data available for this table type")
    
    except requests.RequestException as e:
        print(f"Failed to download tables: {e}")
        return
    except ValueError as e:
        print(f"Failed to parse tables: {e}")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        logger.exception("Unexpected error occurred")
        return

    print("\nValues at specific points:")
    print("=========================")
    
    # Test some specific temperature and RH combinations
    test_points = [
        (20, 50),  # 20°C, 50% RH
        (25, 60),  # 25°C, 60% RH
        (15, 40)   # 15°C, 40% RH
    ]
    
    for temp, rh in test_points:
        print(f"\nAt {temp}°C, {rh}% RH:")
        for table_type, table in tables.items():
            # Find the nearest indices
            info = table_info[table_type]
            temp_idx = int((temp - info.temp_min) * (info.temp_size - 1) / (info.temp_max - info.temp_min))
            rh_idx = int((rh - info.rh_min) * (info.rh_size - 1) / (info.rh_max - info.rh_min))
            
            # Get the value
            value = table[temp_idx, rh_idx]
            print(f"  {table_type.value}: {value:.1f}")

if __name__ == "__main__":
    example_usage()

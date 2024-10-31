"""
Test script to compare JavaScript and Python implementations of preservation calculations.

This script:
1. Downloads the original JavaScript implementation (dp.js)
2. Creates a testing environment to run JavaScript code
3. Generates test cases covering the full range of inputs
4. Runs identical tests through both JavaScript and Python implementations
5. Compares the results and reports any differences

Requirements:
- Node.js installed (for running JavaScript)
- Python 3.6+ with numpy and requests
- Your Python implementation of the pi, emc, and mold functions

Example usage:
    python test_implementations.py

The script will output:
- Test progress information
- Summary of any differences found
- Detailed comparison of differing results
"""

import subprocess
import json
import numpy as np
from pathlib import Path
import tempfile
import requests
from typing import Tuple, Dict, List
import logging
import shutil

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def create_test_wrapper() -> Path:
    """
    Create a JavaScript test environment that uses the original dp.js file.
    
    This function:
    1. Creates a temporary directory
    2. Downloads the original dp.js file into it
    3. Creates a wrapper script that:
       - Loads the original dp.js
       - Provides a test harness to run multiple calculations
       - Handles JSON input/output for communication with Python
    
    Returns:
        Path: Path to the created wrapper script
        
    Raises:
        RuntimeError: If unable to create test environment
    """
    js_code = """
// Load and execute the original dp.js content
const fs = require('fs');
const path = require('path');

// eval() executes dp.js, which defines the pi(), emc(), and mold() functions
eval(fs.readFileSync(path.join(__dirname, 'dp.js'), 'utf8'));

// Function to run multiple test cases
function runTests(inputs) {
    // Process each input pair [temperature, relative_humidity]
    return inputs.map(input => {
        const t = input[0];
        const rh = input[1];
        return {
            temp: t,
            rh: rh,
            pi: pi(t, rh),    // Call original pi() function
            emc: emc(t, rh),   // Call original emc() function
            mold: mold(t, rh)  // Call original mold() function
        };
    });
}

// Set up stdin handling for receiving test cases
const stdin = process.stdin;
let data = '';

stdin.resume();
stdin.setEncoding('utf8');

stdin.on('data', function(chunk) {
    data += chunk;
});

// When all input is received, run tests and output results
stdin.on('end', function() {
    const inputs = JSON.parse(data);
    const results = runTests(inputs);
    console.log(JSON.stringify(results));
});
"""
    
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        # Download original dp.js
        response = requests.get('http://www.dpcalc.org/dp.js')
        response.raise_for_status()
        logger.debug("Successfully downloaded dp.js")
        
        # Save original dp.js
        dp_js_path = temp_dir / 'dp.js'
        dp_js_path.write_text(response.text)
        
        # Save wrapper script
        wrapper_path = temp_dir / 'wrapper.js'
        wrapper_path.write_text(js_code)
        logger.debug("Created wrapper script")
        
        return wrapper_path
        
    except Exception as e:
        # Clean up on error
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to create test environment: {str(e)}")

def run_javascript_tests(test_cases: List[List[float]]) -> List[Dict]:
    """
    Run test cases through the original JavaScript implementation.
    
    Args:
        test_cases: List of [temperature, humidity] pairs to test
        
    Returns:
        List of dictionaries containing test results. Each dictionary contains:
            - temp: Input temperature
            - rh: Input relative humidity
            - pi: Preservation Index value
            - emc: Equilibrium Moisture Content value
            - mold: Mold risk value
            
    Raises:
        RuntimeError: If JavaScript execution fails
    """
    wrapper_file = create_test_wrapper()
    
    try:
        # Convert test cases to JSON for Node.js
        input_json = json.dumps(test_cases)
        
        # Run Node.js process with our wrapper
        process = subprocess.Popen(
            ['node', str(wrapper_file)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send input and get results
        stdout, stderr = process.communicate(input_json)
        
        if process.returncode != 0:
            raise RuntimeError(f"JavaScript execution failed: {stderr}")
        
        # Parse JSON results
        return json.loads(stdout)
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(wrapper_file.parent)

def generate_test_cases() -> List[List[float]]:
    """
    Generate a comprehensive set of test cases.
    
    Creates test cases including:
    1. Regular intervals across the full range
    2. Edge cases at the limits of each function
    3. Special cases known to be important
    
    Returns:
        List of [temperature, humidity] pairs to test
    """
    test_cases = []
    
    # Full range test points
    temps = np.arange(-30, 71, 5)  # -30 to 70°C in steps of 5
    rhs = np.arange(0, 101, 5)     # 0 to 100% in steps of 5
    
    # Add all combinations
    for t in temps:
        for rh in rhs:
            test_cases.append([float(t), float(rh)])
    
    # Add edge cases
    edge_cases = [
        [-23, 6],    # PI minimum values
        [65, 95],    # PI maximum values
        [-20, 0],    # EMC minimum values
        [65, 100],   # EMC maximum values
        [2, 65],     # Mold threshold values
        [45, 95],    # Mold maximum values
    ]
    test_cases.extend(edge_cases)
    
    return test_cases

def run_python_implementation(test_cases: List[List[float]]) -> List[Dict]:
    """
    Run test cases through Python implementation.
    
    Args:
        test_cases: List of [temperature, humidity] pairs to test
        
    Returns:
        List of dictionaries containing test results in same format as JavaScript results
        
    Note:
        Requires your Python implementation to be available for import
    """
    # Import your Python implementation here
    from your_implementation import pi, emc, mold
    
    results = []
    for t, rh in test_cases:
        results.append({
            'temp': t,
            'rh': rh,
            'pi': pi(t, rh),
            'emc': emc(t, rh),
            'mold': mold(t, rh)
        })
    return results

def compare_implementations(js_results: List[Dict], py_results: List[Dict]) -> Dict[str, List]:
    """
    Compare JavaScript and Python results.
    
    Args:
        js_results: Results from JavaScript implementation
        py_results: Results from Python implementation
        
    Returns:
        Dictionary containing lists of differences for each function:
            - 'pi': List of PI calculation differences
            - 'emc': List of EMC calculation differences
            - 'mold': List of mold calculation differences
            
    Each difference is a dictionary containing:
        - temp: Temperature value
        - rh: Relative humidity value
        - js_value: JavaScript result
        - py_value: Python result
    """
    differences = {
        'pi': [],
        'emc': [],
        'mold': []
    }
    
    for js_result, py_result in zip(js_results, py_results):
        t, rh = js_result['temp'], js_result['rh']
        
        # Compare PI values (exact match required)
        if js_result['pi'] != py_result['pi']:
            differences['pi'].append({
                'temp': t,
                'rh': rh,
                'js_value': js_result['pi'],
                'py_value': py_result['pi']
            })
        
        # Compare EMC values (small tolerance for floating point)
        if abs(js_result['emc'] - py_result['emc']) > 0.0001:
            differences['emc'].append({
                'temp': t,
                'rh': rh,
                'js_value': js_result['emc'],
                'py_value': py_result['emc']
            })
        
        # Compare Mold values (exact match required)
        if js_result['mold'] != py_result['mold']:
            differences['mold'].append({
                'temp': t,
                'rh': rh,
                'js_value': js_result['mold'],
                'py_value': py_result['mold']
            })
    
    return differences

def main():
    """
    Main function to run the comparison tests.
    
    This function:
    1. Generates test cases
    2. Runs both implementations
    3. Compares results
    4. Reports findings
    """
    try:
        # Generate test cases
        test_cases = generate_test_cases()
        logger.info(f"Generated {len(test_cases)} test cases")
        
        # Run JavaScript implementation
        logger.info("Running JavaScript tests...")
        js_results = run_javascript_tests(test_cases)
        
        # Run Python implementation
        logger.info("Running Python tests...")
        py_results = run_python_implementation(test_cases)
        
        # Compare results
        differences = compare_implementations(js_results, py_results)
        
        # Report results
        print("\nTest Results:")
        print("=============")
        
        total_tests = len(test_cases)
        total_differences = sum(len(diffs) for diffs in differences.values())
        
        print(f"\nTotal test cases: {total_tests}")
        print(f"Total differences: {total_differences}")
        
        for func_name, diffs in differences.items():
            if diffs:
                print(f"\nDifferences in {func_name} function ({len(diffs)} cases):")
                for diff in diffs[:5]:  # Show first 5 differences
                    print(f"  T={diff['temp']}°C, RH={diff['rh']}%:")
                    print(f"    JavaScript: {diff['js_value']}")
                    print(f"    Python:     {diff['py_value']}")
                if len(diffs) > 5:
                    print(f"  ... and {len(diffs)-5} more differences")
                    
    except Exception as e:
        logger.error(f"Test execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
    
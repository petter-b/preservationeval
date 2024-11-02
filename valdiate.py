"""
Test script to compare JavaScript and Python implementations of preservation calculations.

This script:
1. Downloads the original JavaScript implementation (dp.js)
2. Creates a browser-based testing environment using Puppeteer
3. Runs the original dp.js code in its intended environment
4. Compares results with Python implementation
5. Reports any differences found

Requirements:
- Node.js installed
- Puppeteer installed (npm install -g puppeteer)
- Python 3.6+ with numpy and requests
- Your Python implementation of the pi, emc, and mold functions

The script uses Puppeteer to run the original dp.js in a proper browser environment,
ensuring we're testing against the actual implementation rather than a recreation.

Example usage:
    python test_implementations.py
"""

import subprocess
import json
import numpy as np
from pathlib import Path
import tempfile
import requests
from typing import List, Dict
import logging
import shutil

# Import your Python implementation here
from preservationeval import pi, emc, mold

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def check_nodejs_installation() -> bool:
    """
    Check if Node.js and npm are available on the system.
    
    Returns:
        bool: True if both Node.js and npm are available
        
    Raises:
        RuntimeError: If Node.js or npm is not installed
    """
    try:
        # Check Node.js
        node_version = subprocess.run(
            ['node', '--version'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        logger.debug(f"Found Node.js: {node_version.stdout.strip()}")
        
        # Check npm
        npm_version = subprocess.run(
            ['npm', '--version'], 
            capture_output=True, 
            text=True, 
            check=True
        )
        logger.debug(f"Found npm: {npm_version.stdout.strip()}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            "Node.js and npm are required but not found. "
            "Please install them from https://nodejs.org/"
        ) from e
    except FileNotFoundError as e:
        raise RuntimeError(
            "Node.js and npm are required but not found in PATH. "
            "Please install them from https://nodejs.org/"
        ) from e


def create_test_environment() -> Path:
    """
    Create a browser-based test environment for running dp.js.
    
    This function:
    1. Creates a temporary directory
    2. Sets up a Node.js project with Puppeteer
    3. Creates the test files
    """
    # HTML file remains the same
    html_code = """
<!DOCTYPE html>
<html>
<head>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="dp.js"></script>
    <script>
        function runTests(inputs) {
            return inputs.map(input => {
                const t = input[0];
                const rh = input[1];
                return {
                    temp: t,
                    rh: rh,
                    pi: pi(t, rh),
                    emc: emc(t, rh),
                    mold: mold(t, rh)
                };
            });
        }
    </script>
</head>
<body>
</body>
</html>
    """
    
    # package.json for Node.js project
    package_json = """{
        "name": "dp-test",
        "version": "1.0.0",
        "dependencies": {
            "puppeteer": "^19.0.0"
        }
    }"""
    
    # Node.js script remains the same
    node_code = """
const puppeteer = require('puppeteer');

async function runTests() {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    await page.goto('file://' + process.argv[2]);
    
    let data = '';
    process.stdin.resume();
    process.stdin.setEncoding('utf8');
    
    process.stdin.on('data', (chunk) => {
        data += chunk;
    });
    
    process.stdin.on('end', async () => {
        const inputs = JSON.parse(data);
        const results = await page.evaluate((testInputs) => {
            return runTests(testInputs);
        }, inputs);
        console.log(JSON.stringify(results));
        await browser.close();
    });
}

runTests().catch(console.error);
    """
    
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp())
        logger.debug(f"Created temporary directory: {temp_dir}")
        
        # Create package.json and install dependencies
        (temp_dir / 'package.json').write_text(package_json)
        
        # Run npm install
        subprocess.run(
            ['npm', 'install'],
            cwd=temp_dir,
            check=True,
            capture_output=True,
            text=True
        )
        logger.debug("Installed Node.js dependencies")
        
        # Download original dp.js
        response = requests.get('http://www.dpcalc.org/dp.js')
        response.raise_for_status()
        js_content = response.text
        logger.debug("Successfully downloaded dp.js")
        
        # Save all required files
        (temp_dir / 'dp.js').write_text(js_content)
        (temp_dir / 'test.html').write_text(html_code)
        (temp_dir / 'run_tests.js').write_text(node_code)
        
        return temp_dir
        
    except subprocess.CalledProcessError as e:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to install Node.js dependencies: {e.stdout}\n{e.stderr}")
    except requests.RequestException as e:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to download dp.js: {e}")
    except Exception as e:
        if 'temp_dir' in locals():
            shutil.rmtree(temp_dir)
        raise RuntimeError(f"Failed to create test environment: {e}")


def run_javascript_tests(test_cases: List[List[float]]) -> List[Dict]:
    """
    Run test cases through the original JavaScript implementation.
    
    This function:
    1. Creates a test environment with all necessary files
    2. Launches a headless browser using Puppeteer
    3. Runs the test cases using the original dp.js implementation
    4. Returns the results
    
    Args:
        test_cases: List of [temperature, humidity] pairs to test
        
    Returns:
        List of dictionaries containing test results. Each dictionary contains:
            - temp: Input temperature
            - rh: Input relative humidity
            - pi: Preservation Index value from original implementation
            - emc: Equilibrium Moisture Content value from original implementation
            - mold: Mold risk value from original implementation
            
    Raises:
        RuntimeError: If JavaScript execution fails
    """
    test_dir = create_test_environment()
    
    try:
        # Convert test cases to JSON for Node.js
        input_json = json.dumps(test_cases)
        
        # Run tests using Puppeteer
        process = subprocess.Popen(
            ['node', str(test_dir / 'run_tests.js'), str(test_dir / 'test.html')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Send input and get results
        stdout, stderr = process.communicate(input_json)
        
        if process.returncode != 0:
            raise RuntimeError(f"JavaScript execution failed: {stderr}")
        
        # Parse and return results
        return json.loads(stdout)
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(test_dir)


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
        # First check for Node.js/npm
        check_nodejs_installation()
        
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
    
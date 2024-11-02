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
- Python 3.6+ with numpy and requests
- Your Python implementation of the pi, emc, and mold functions

Example usage:
    python validate.py
"""

import subprocess
import json
import numpy as np
from pathlib import Path
import tempfile
import requests
from typing import List, Dict, Optional
import logging
import shutil
from dataclasses import dataclass
import sys

# Add project root to Python path
parent_dir = Path(__file__).parent.parent
sys.path.append(str(parent_dir))

from preservationeval import pi, emc, mold
from config import TEST_CONFIG, JS_CONFIG, COMPARISON_CONFIG
from templates import HTML_TEMPLATE, NODE_SCRIPT_TEMPLATE

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Single test case result with all calculation values."""
    temp: float
    rh: float
    pi: int
    emc: float
    mold: int

@dataclass
class Difference:
    """Represents a difference between JavaScript and Python results."""
    temp: float
    rh: float
    js_value: float
    py_value: float

class NodeEnvironment:
    """Handles Node.js environment checking and setup."""
    
    @staticmethod
    def check_installation() -> bool:
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

class TestEnvironment:
    """Manages the test environment setup and cleanup."""
    
    def __init__(self):
        self.temp_dir: Optional[Path] = None
    
    def setup(self) -> Path:
        """
        Create and set up the test environment.
        
        Returns:
            Path: Path to the temporary directory
        """
        self.temp_dir = Path(tempfile.mkdtemp())
        logger.debug(f"Created temporary directory: {self.temp_dir}")
        
        self._create_package_json()
        self._install_dependencies()
        self._download_dp_js()
        self._create_test_files()
        
        return self.temp_dir
    
    def cleanup(self):
        """Clean up the test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None
    
    def _create_package_json(self):
        """Create package.json file."""
        if self.temp_dir:
            (self.temp_dir / 'package.json').write_text(
                json.dumps(JS_CONFIG['package_json'], indent=2)
            )
    
    def _install_dependencies(self):
        """Install Node.js dependencies."""
        if self.temp_dir:
            subprocess.run(
                ['npm', 'install'],
                cwd=self.temp_dir,
                check=True,
                capture_output=True,
                text=True
            )
            logger.debug("Installed Node.js dependencies")
    
    def _download_dp_js(self):
        """Download the original dp.js file and analyze its contents."""
        if self.temp_dir:
            response = requests.get(JS_CONFIG['dp_js_url'])
            response.raise_for_status()
            js_content = response.text
            
            # Log the actual JavaScript implementation
#            logger.debug("JavaScript implementation:")
#            logger.debug(js_content)
            
            (self.temp_dir / 'dp.js').write_text(js_content)
            logger.info("Downloaded dp.js")
    
    def _create_test_files(self):
        """Create HTML and Node.js test files."""
        if self.temp_dir:
            (self.temp_dir / 'test.html').write_text(HTML_TEMPLATE)
            (self.temp_dir / 'run_tests.js').write_text(NODE_SCRIPT_TEMPLATE)
            logger.debug("Created test files")

class PreservationTester:
    """Handles the complete testing process."""
    
    def __init__(self):
        self.test_env = TestEnvironment()
    
    def run_validation(self) -> Dict[str, List[Difference]]:
        """
        Run complete validation process.
        
        Returns:
            Dict containing differences for each function type
        """
        NodeEnvironment.check_installation()
        
        test_cases = self._generate_test_cases(TEST_CONFIG['num_tests'])
        logger.info(f"Generated {len(test_cases)} test cases")
        
        js_results = self._run_javascript_tests(test_cases)
        py_results = self._run_python_tests(test_cases)
        
        return self._compare_results(js_results, py_results)
    
    def _generate_test_cases(self, num_tests: int) -> List[List[float]]:
        """
        Generate random test cases within the configured ranges and step sizes.
        
        Args:
            num_tests: Number of random test cases to generate.
        
        Returns:
            List of [temperature, relative humidity] pairs.
        """
        import decimal
        from decimal import Decimal

        # Set decimal precision
        decimal.getcontext().prec = 2  # Since we use 0.5 as step
        
        # Convert range values to Decimal
        t_start = Decimal(str(TEST_CONFIG['temp_range'][0]))
        t_stop = Decimal(str(TEST_CONFIG['temp_range'][1]))
        t_step = Decimal(str(TEST_CONFIG['temp_range'][2]))
        
        rh_start = Decimal(str(TEST_CONFIG['rh_range'][0]))
        rh_stop = Decimal(str(TEST_CONFIG['rh_range'][1]))
        rh_step = Decimal(str(TEST_CONFIG['rh_range'][2]))
        
        # Calculate number of possible steps
        t_steps = int((t_stop - t_start) / t_step)
        rh_steps = int((rh_stop - rh_start) / rh_step)
        
        # Generate random step indices
        rng = np.random.default_rng()
        t_indices = rng.integers(0, t_steps + 1, size=num_tests)
        rh_indices = rng.integers(0, rh_steps + 1, size=num_tests)
        
        # Convert indices to actual values using Decimal arithmetic
        t_samples = [t_start + (Decimal(str(i)) * t_step) for i in t_indices]
        rh_samples = [rh_start + (Decimal(str(i)) * rh_step) for i in rh_indices]
    
        # Combine into test cases
        test_cases = [[float(t), float(rh)] for t, rh in zip(t_samples, rh_samples)]
                
        logger.info(f"Generated {len(test_cases)} test cases randomly")
        logger.info(f"Using temperature steps of {t_step} from {t_start} to {t_stop}")
        logger.info(f"Using humidity steps of {rh_step} from {rh_start} to {rh_stop}")
    
        return test_cases
    
    def _run_javascript_tests(self, test_cases: List[List[float]]) -> List[Dict]:
        """Run tests through JavaScript implementation."""
        try:
            temp_dir = self.test_env.setup()
            
            # Convert test cases to JSON
            input_json = json.dumps(test_cases)
            
            # Run tests using Node.js
            process = subprocess.Popen(
                ['node', str(temp_dir / 'run_tests.js'), str(temp_dir / 'test.html')],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input_json)
            
            if process.returncode != 0:
                raise RuntimeError(f"JavaScript execution failed: {stderr}")
            
            return json.loads(stdout)
            
        finally:
            self.test_env.cleanup()
    
    def _run_python_tests(self, test_cases: List[List[float]]) -> List[Dict]:
        """Run tests through Python implementation."""
        return [
            {
                'temp': t,
                'rh': rh,
                'pi': pi(t, rh),
                'emc': emc(t, rh),
                'mold': mold(t, rh)
            }
            for t, rh in test_cases
        ]
    
    def _compare_results(
        self, 
        js_results: List[Dict], 
        py_results: List[Dict]
    ) -> Dict[str, List[Difference]]:
        """Compare JavaScript and Python results with detailed analysis."""
        differences = {
            'pi': [],
            'emc': [],
            'mold': []
        }
        
        # Analysis counters
        analysis = {
            'pi': {'total': 0, 'by_range': {}},
            'emc': {'total': 0, 'by_range': {}},
            'mold': {'total': 0, 'by_range': {}}
        }
        
        for js_result, py_result in zip(js_results, py_results):
            t, rh = js_result['temp'], js_result['rh']
            
            # Group into ranges for analysis
            t_range = f"{int(t/10)*10}-{int(t/10)*10+10}"
            rh_range = f"{int(rh/10)*10}-{int(rh/10)*10+10}"
            range_key = f"T:{t_range},RH:{rh_range}"
            
            # Compare PI values
            if js_result['pi'] != py_result['pi']:
                differences['pi'].append(Difference(t, rh, js_result['pi'], py_result['pi']))
                analysis['pi']['total'] += 1
                analysis['pi']['by_range'][range_key] = analysis['pi']['by_range'].get(range_key, 0) + 1
                logger.debug(
                    f"PI difference at T={t}, RH={rh}: "
                    f"JS={js_result['pi']}, PY={py_result['pi']}, "
                    f"diff={abs(js_result['pi'] - py_result['pi'])}"
                )
            
            # Compare EMC values
            if abs(js_result['emc'] - py_result['emc']) > COMPARISON_CONFIG['emc_tolerance']:
                differences['emc'].append(Difference(t, rh, js_result['emc'], py_result['emc']))
                analysis['emc']['total'] += 1
                analysis['emc']['by_range'][range_key] = analysis['emc']['by_range'].get(range_key, 0) + 1
                logger.debug(
                    f"EMC difference at T={t}, RH={rh}: "
                    f"JS={js_result['emc']:.4f}, PY={py_result['emc']:.4f}, "
                    f"diff={abs(js_result['emc'] - py_result['emc']):.4f}"
                )
            
            # Compare Mold values
            if js_result['mold'] != py_result['mold']:
                differences['mold'].append(Difference(t, rh, js_result['mold'], py_result['mold']))
                analysis['mold']['total'] += 1
                analysis['mold']['by_range'][range_key] = analysis['mold']['by_range'].get(range_key, 0) + 1
                logger.debug(
                    f"Mold difference at T={t}, RH={rh}: "
                    f"JS={js_result['mold']}, PY={py_result['mold']}, "
                    f"diff={abs(js_result['mold'] - py_result['mold'])}"
                )
        
        # Log analysis summary
        for func in ['pi', 'emc', 'mold']:
            if analysis[func]['total'] > 0:
                logger.info(f"\n{func.upper()} Analysis:")
                logger.info(f"Total differences: {analysis[func]['total']}")
                logger.info("Differences by range:")
                for range_key, count in sorted(analysis[func]['by_range'].items()):
                    logger.info(f"  {range_key}: {count} differences")
        
        return differences


def report_differences(differences: Dict[str, List[Difference]]):
    """Generate a human-readable report of differences."""
    print("\nTest Results:")
    print("=============")
    
    total_differences = sum(len(diffs) for diffs in differences.values())
    print(f"\nTotal differences: {total_differences}")
    
    for func_name, diffs in differences.items():
        if diffs:
            print(f"\nDifferences in {func_name} function ({len(diffs)} cases):")
            for diff in diffs[:COMPARISON_CONFIG['max_differences_shown']]:
                print(f"  T={diff.temp}°C, RH={diff.rh}%:")
                print(f"    JavaScript: {diff.js_value}")
                print(f"    Python:     {diff.py_value}")
            if len(diffs) > COMPARISON_CONFIG['max_differences_shown']:
                print(f"  ... and {len(diffs)-COMPARISON_CONFIG['max_differences_shown']} more differences")

def main():
    """Main execution function."""
    try:
        tester = PreservationTester()
        differences = tester.run_validation()
        report_differences(differences)
        if differences:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
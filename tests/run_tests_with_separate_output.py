#!/usr/bin/env python3
"""
Run integration tests with a separate output directory to avoid cluttering the main output folder.
"""

import os
import subprocess
import sys
from pathlib import Path

def main():
    # Set environment variable for test output directory
    os.environ['OUTPUT_BASE_DIR'] = 'output'
    
    # Create test output directory
    test_output_dir = Path('test_output')
    test_output_dir.mkdir(exist_ok=True)
    
    print("🧪 Running integration tests with separate output directory...")
    print(f"📁 Test output will be saved to: {test_output_dir.absolute()}")
    
    try:
        # Run the integration tests
        result = subprocess.run(
            [sys.executable, 'tests/integration_test.py'],
            cwd=os.getcwd(),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print("\n✅ Integration tests completed successfully!")
            print(f"📁 Test outputs are in: {test_output_dir.absolute()}")
            print("💡 Your main 'output' directory remains clean.")
        else:
            print("\n❌ Integration tests failed.")
            
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
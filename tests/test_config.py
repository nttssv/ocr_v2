#!/usr/bin/env python3
"""
Test configuration for OCR API tests.
Sets up dedicated test output directories to avoid cluttering production outputs.
"""

import os
from pathlib import Path

# Test output directory configuration
TEST_OUTPUT_BASE_DIR = "test_outputs"
PRODUCTION_OUTPUT_DIR = "data/outputs"

def setup_test_environment():
    """
    Set up test environment with dedicated output directory.
    This prevents test artifacts from cluttering the main outputs folder.
    """
    # Create test output directory
    test_output_dir = Path(TEST_OUTPUT_BASE_DIR)
    test_output_dir.mkdir(exist_ok=True)
    
    # Set environment variable for API to use test output directory
    os.environ['OUTPUT_BASE_DIR'] = TEST_OUTPUT_BASE_DIR
    
    print(f"📁 Test output directory set to: {test_output_dir.absolute()}")
    print(f"🔧 Environment variable OUTPUT_BASE_DIR = {TEST_OUTPUT_BASE_DIR}")
    
    return str(test_output_dir.absolute())

def cleanup_test_environment():
    """
    Clean up test environment and restore production settings.
    """
    # Restore production output directory
    os.environ['OUTPUT_BASE_DIR'] = PRODUCTION_OUTPUT_DIR
    
    print(f"🔄 Restored production output directory: {PRODUCTION_OUTPUT_DIR}")

def get_test_output_dir():
    """
    Get the current test output directory path.
    """
    return os.environ.get('OUTPUT_BASE_DIR', PRODUCTION_OUTPUT_DIR)

def is_test_environment():
    """
    Check if we're currently in test environment.
    """
    return os.environ.get('OUTPUT_BASE_DIR') == TEST_OUTPUT_BASE_DIR

# Context manager for test environment
class TestEnvironment:
    """
    Context manager to temporarily set up test environment.
    
    Usage:
        with TestEnvironment():
            # Run tests here
            pass
    """
    
    def __enter__(self):
        self.original_output_dir = os.environ.get('OUTPUT_BASE_DIR', PRODUCTION_OUTPUT_DIR)
        setup_test_environment()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.environ['OUTPUT_BASE_DIR'] = self.original_output_dir
        print(f"🔄 Restored output directory: {self.original_output_dir}")
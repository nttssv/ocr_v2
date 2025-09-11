#!/usr/bin/env python3
"""
Test script to demonstrate hierarchy preservation with samples folder structure
"""

import json
import time
from pathlib import Path

import requests

# Import test configuration
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from unit.test_config import TestEnvironment

# API configuration
API_BASE_URL = "http://localhost:8000"


def test_samples_hierarchy():
    """Test hierarchy preservation with actual samples folder structure"""

    print("🧪 Testing Samples Folder Hierarchy Preservation")
    print("=" * 55)

    # Test cases using data/samples folder structure
    test_cases = [
        {
            "name": "File from data/samples/a/ folder",
            "file_path": "data/samples/a/1.pdf",
            "relative_input_path": "a",
            "expected_output": "data/outputs/a/1/",
        },
        {
            "name": "File from data/samples/b/ folder",
            "file_path": "data/samples/b/1.pdf",
            "relative_input_path": "b",
            "expected_output": "data/outputs/b/1/",
        },
        {
            "name": "File from data/samples/legal/ folder",
            "file_path": "data/samples/legal/1.pdf",
            "relative_input_path": "legal",
            "expected_output": "data/outputs/legal/1/",
        },
        {
            "name": "File from data/samples/invoices/ folder",
            "file_path": "data/samples/invoices/1.pdf",
            "relative_input_path": "invoices",
            "expected_output": "data/outputs/invoices/1/",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print(f"Input file: {test_case['file_path']}")
        print(f"Relative path: {test_case['relative_input_path']}")
        print(f"Expected output: {test_case['expected_output']}")

        # Check if test PDF exists
        if not Path(test_case["file_path"]).exists():
            print(f"⚠️  Test PDF not found at {test_case['file_path']}")
            continue

        # Prepare request data
        files = {"file": open(test_case["file_path"], "rb")}
        data = {
            "language": "vie",
            "enable_handwriting_detection": False,
            "relative_input_path": test_case["relative_input_path"],
        }

        try:
            # Submit document for processing
            response = requests.post(
                f"{API_BASE_URL}/documents/transform", files=files, data=data
            )
            files["file"].close()

            if response.status_code == 200:
                result = response.json()
                document_id = result["document_id"]
                print(f"✅ Document submitted successfully. ID: {document_id}")

                # Wait for processing to complete
                print("⏳ Waiting for processing...")
                start_time = time.time()

                while True:
                    status_response = requests.get(
                        f"{API_BASE_URL}/documents/status/{document_id}"
                    )
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        elapsed_time = time.time() - start_time

                        if status_data["status"] == "completed":
                            if "result" in status_data and status_data["result"]:
                                result = status_data["result"]
                                total_pages = result.get("total_pages", 0)
                                time_per_page = (
                                    elapsed_time / total_pages if total_pages > 0 else 0
                                )

                                print(
                                    f"✅ Processing completed in {elapsed_time:.1f} seconds!"
                                )
                                print(
                                    f"📄 Total pages: {total_pages} | ⏱️ Time per page: {time_per_page:.2f}s"
                                )

                                output_dir = result.get("output_directory")
                                if output_dir:
                                    print(f"📁 Output directory: {output_dir}")
                                    # Verify the directory structure
                                    if Path(output_dir).exists():
                                        print(
                                            f"✅ Output directory exists: {output_dir}"
                                        )
                                        # Check if it matches expected structure
                                        if test_case["expected_output"] in output_dir:
                                            print(f"✅ Hierarchy preserved correctly!")
                                        else:
                                            print(
                                                f"⚠️  Expected: {test_case['expected_output']}, Got: {output_dir}"
                                            )
                                    else:
                                        print(
                                            f"❌ Output directory not found: {output_dir}"
                                        )
                            else:
                                print(
                                    f"✅ Processing completed in {elapsed_time:.1f} seconds!"
                                )
                            break
                        elif status_data["status"] == "failed":
                            print(
                                f"❌ Processing failed after {elapsed_time:.1f} seconds: {status_data.get('error', 'Unknown error')}"
                            )
                            break
                        else:
                            progress = status_data.get("progress", 0)
                            # Calculate estimated time to completion
                            if progress > 0:
                                estimated_total = elapsed_time / progress
                                estimated_remaining = estimated_total - elapsed_time

                                # Show page info if available
                                page_info = ""
                                if "result" in status_data and status_data["result"]:
                                    total_pages = status_data["result"].get(
                                        "total_pages", 0
                                    )
                                    if total_pages > 0:
                                        page_info = f" | Pages: {total_pages}"

                                print(
                                    f"⏳ Status: {status_data['status']} ({progress:.1%}){page_info} - Elapsed: {elapsed_time:.1f}s, ETA: {estimated_remaining:.1f}s"
                                )
                            else:
                                print(
                                    f"⏳ Status: {status_data['status']} ({progress:.1%}) - Elapsed: {elapsed_time:.1f}s"
                                )
                            time.sleep(2)
                    else:
                        print(f"❌ Failed to get status: {status_response.status_code}")
                        break
            else:
                print(f"❌ Failed to submit document: {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error during test: {e}")

        print("-" * 40)

    print("\n🎯 Test Summary")
    print("The hierarchy preservation feature allows you to maintain folder structure:")
    print("- samples/a/1.pdf → output/a/1/ (preserves 'a' folder)")
    print("- samples/b/1.pdf → output/b/1/ (preserves 'b' folder)")
    print("- samples/legal/1.pdf → output/legal/1/ (preserves 'legal' folder)")
    print("- samples/invoices/1.pdf → output/invoices/1/ (preserves 'invoices' folder)")


def check_api_health():
    """Check if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    print("🚀 Samples Folder Hierarchy Preservation Test")
    print("This test demonstrates how the API preserves folder structure")
    print("from the samples directory in the output.\n")

    # Use dedicated test output directory
    with TestEnvironment():
        print("📁 Using dedicated test output directory")

        if check_api_health():
            test_samples_hierarchy()
        else:
            print("❌ API is not running!")
            print("💡 To start the API, run: python src/api/v1/api.py")

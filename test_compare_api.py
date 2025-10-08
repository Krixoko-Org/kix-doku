import unittest
import os
import json
import yaml
import subprocess
import shutil

class TestCompareApi(unittest.TestCase):

    def setUp(self):
        """Set up test files with known discrepancies."""
        # Backup original files by renaming them
        if os.path.exists('parsed_api.json'):
            shutil.move('parsed_api.json', 'parsed_api.json.bak')
        if os.path.exists('openapi.yaml'):
            shutil.move('openapi.yaml', 'openapi.yaml.bak')
        if os.path.exists('comparison_output.json'):
            os.remove('comparison_output.json')

        # Create a mock parsed_api.json with more items than the openapi spec
        parsed_api_data = [
            {
                "path": "/users",
                "method": "GET",
                "query_params": [{"name": "page", "description": "Page number"}],
                "response_examples": {"200": {"description": "A list of users."}}
            },
            {
                "path": "/users",
                "method": "POST",
                "query_params": [],
                "response_examples": {}
            },
            {
                "path": "/posts",
                "method": "GET",
                "query_params": [],
                "response_examples": {}
            }
        ]
        with open('parsed_api.json', 'w') as f:
            json.dump(parsed_api_data, f)

        # Create a mock openapi.yaml with missing items
        openapi_data = {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users": {
                    "get": {
                        "summary": "Get users",
                        "parameters": [],
                        "responses": {
                            "200": {
                                "description": "A list of users.",
                                "content": {
                                    "application/json": {}
                                }
                            }
                        }
                    }
                }
            }
        }
        with open('openapi.yaml', 'w') as f:
            yaml.dump(openapi_data, f)

    def tearDown(self):
        """Clean up test files and restore original files."""
        # Remove the mock files
        if os.path.exists('parsed_api.json'):
            os.remove('parsed_api.json')
        if os.path.exists('openapi.yaml'):
            os.remove('openapi.yaml')
        if os.path.exists('comparison_output.json'):
            os.remove('comparison_output.json')

        # Restore original files
        if os.path.exists('parsed_api.json.bak'):
            shutil.move('parsed_api.json.bak', 'parsed_api.json')
        if os.path.exists('openapi.yaml.bak'):
            shutil.move('openapi.yaml.bak', 'openapi.yaml')

    def test_fixed_script_reports_correctly_and_exits_with_error(self):
        """
        This test verifies the fix:
        1. The script exits with code 1 when discrepancies are found.
        2. The output JSON contains all missing items, including paths and methods.
        """
        # Run the updated script as a subprocess
        process = subprocess.run(['python3', 'compare_api.py'], capture_output=True, text=True)

        # 1. Assert that the script exits with 1
        self.assertEqual(process.returncode, 1, "Fix verification failed: Script should exit with 1 when discrepancies are found.")

        # Assert that the correct message is printed to stdout
        self.assertIn("Discrepancies found. See comparison_output.json for details.", process.stdout)

        # 2. Assert that the output JSON contains all the missing items
        with open('comparison_output.json', 'r') as f:
            output = json.load(f)

        expected_output = {
            "missing_paths": [{"path": "/posts"}],
            "missing_methods": [{"path": "/users", "method": "POST"}],
            "missing_parameters": [{"path": "/users", "method": "GET", "parameter": "page"}],
            "missing_examples": [{"path": "/users", "method": "GET"}]
        }

        # Sort the lists in both actual and expected output for a stable comparison
        for key in expected_output:
            output[key] = sorted(output.get(key, []), key=lambda x: tuple(x.items()))
            expected_output[key] = sorted(expected_output[key], key=lambda x: tuple(x.items()))

        self.assertDictEqual(output, expected_output, "Fix verification failed: The JSON output does not match the expected discrepancies.")

if __name__ == '__main__':
    unittest.main()
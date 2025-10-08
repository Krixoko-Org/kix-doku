import json
import yaml
import sys

def compare_api_specs():
    """
    Compares API specifications from parsed HTML documentation against an OpenAPI YAML file.

    This function reads API endpoint details from `parsed_api.json` and compares them
    with the definitions in `openapi.yaml`. It checks for missing paths, methods,
    query parameters, and response examples.

    All discrepancies are recorded in `comparison_output.json`. If any discrepancies
    are found, the script prints a message and exits with a status code of 1.
    """
    try:
        with open('parsed_api.json', 'r') as f:
            html_data = json.load(f)
    except FileNotFoundError:
        print("Error: parsed_api.json not found. Please run the parsing script first.")
        sys.exit(1)

    try:
        with open('openapi.yaml', 'r') as f:
            openapi_data = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: openapi.yaml not found.")
        sys.exit(1)

    missing_items = {
        "missing_paths": [],
        "missing_methods": [],
        "missing_parameters": [],
        "missing_examples": []
    }

    for endpoint in html_data:
        path = endpoint['path']
        method = endpoint['method'].lower()
        html_params = endpoint.get('query_params', [])
        html_examples = endpoint.get('response_examples', {})

        # Check for missing paths
        if path not in openapi_data.get('paths', {}):
            missing_items["missing_paths"].append({"path": path})
            continue  # If path is missing, no need to check for methods, params, etc.

        # Check for missing methods
        if method not in openapi_data['paths'][path]:
            missing_items["missing_methods"].append({
                "path": path,
                "method": method.upper()
            })
            continue  # If method is missing, no need to check for params, etc.

        openapi_endpoint = openapi_data['paths'][path][method]

        # Check for missing parameters
        openapi_params = openapi_endpoint.get('parameters', [])
        openapi_param_names = [p['name'] for p in openapi_params if p.get('in') == 'query']
        for param in html_params:
            if param['name'] not in openapi_param_names:
                missing_items["missing_parameters"].append({
                    "path": path,
                    "method": method.upper(),
                    "parameter": param['name']
                })

        # Check for missing response examples
        if '200' in html_examples:
            responses = openapi_endpoint.get('responses', {})
            if '200' not in responses or \
               'content' not in responses['200'] or \
               'application/json' not in responses['200']['content'] or \
               'example' not in responses['200']['content']['application/json']:
                missing_items["missing_examples"].append({
                    "path": path,
                    "method": method.upper()
                })

    with open('comparison_output.json', 'w') as f:
        json.dump(missing_items, f, indent=4)

    # Exit with a non-zero status code if any discrepancies were found
    if any(missing_items.values()):
        print("Discrepancies found. See comparison_output.json for details.")
        sys.exit(1)

if __name__ == '__main__':
    compare_api_specs()
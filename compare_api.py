import json
import yaml

def compare_api_specs():
    with open('parsed_api.json', 'r') as f:
        html_data = json.load(f)

    with open('openapi.yaml', 'r') as f:
        openapi_data = yaml.safe_load(f)

    for endpoint in html_data:
        path = endpoint['path']
        method = endpoint['method'].lower()
        html_params = endpoint.get('query_params', [])
        html_examples = endpoint.get('response_examples', {})

        if path in openapi_data['paths']:
            if method in openapi_data['paths'][path]:
                openapi_endpoint = openapi_data['paths'][path][method]
                openapi_params = openapi_endpoint.get('parameters', [])
                openapi_param_names = [p['name'] for p in openapi_params if p['in'] == 'query']

                # Check for missing parameters
                for param in html_params:
                    if param['name'] not in openapi_param_names:
                        print(f"Missing parameter in {method.upper()} {path}: {param['name']}")

                # Check for missing response examples
                if '200' in html_examples:
                    if 'responses' not in openapi_endpoint or \
                       '200' not in openapi_endpoint['responses'] or \
                       'content' not in openapi_endpoint['responses']['200'] or \
                       'application/json' not in openapi_endpoint['responses']['200']['content'] or \
                       'example' not in openapi_endpoint['responses']['200']['content']['application/json']:
                        print(f"Missing 200 response example in {method.upper()} {path}")

            else:
                print(f"Missing method {method.upper()} for path {path} in openapi.yaml")
        else:
            print(f"Missing path {path} in openapi.yaml")

if __name__ == '__main__':
    compare_api_specs()
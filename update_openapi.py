import json
import yaml

def load_json_file(file_path):
    """Loads a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def load_yaml_file(file_path):
    """Loads a YAML file."""
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)

def write_yaml_file(data, file_path):
    """Writes data to a YAML file."""
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def update_openapi_spec():
    """
    Updates the OpenAPI specification with data from HTML parsing and RAML files.
    """
    # Load all necessary data
    html_data = load_json_file('parsed_api.json')
    raml_data = load_json_file('raml_api_details.json')
    openapi_data = load_yaml_file('openapi.yaml')

    # Ensure 'components' and 'schemas' sections exist and clean invalid fields
    if 'components' not in openapi_data:
        openapi_data['components'] = {}
    if 'schemas' not in openapi_data['components']:
        openapi_data['components']['schemas'] = {}
    else:
        # **Crucially, remove any invalid 'examples' fields from schemas**
        for schema_name, schema_def in openapi_data['components']['schemas'].items():
            if 'examples' in schema_def:
                del schema_def['examples']

    # Add/update schemas from RAML data
    for schema_name, schema_details in raml_data.items():
        properties = schema_details.get('properties', {})
        if schema_name not in openapi_data['components']['schemas']:
            openapi_data['components']['schemas'][schema_name] = {
                'type': 'object',
                'properties': properties
            }
        else:
            # If schema exists, just update its properties
            openapi_data['components']['schemas'][schema_name]['properties'] = properties

    # Update paths with examples from RAML
    for path, methods in openapi_data.get('paths', {}).items():
        for method, openapi_endpoint in methods.items():
            for response_code, response_body in openapi_endpoint.get('responses', {}).items():
                content = response_body.get('content', {}).get('application/json', {})
                if 'schema' in content and '$ref' in content['schema']:
                    schema_ref = content['schema']['$ref']
                    schema_name = schema_ref.split('/')[-1]
                    if schema_name in raml_data and raml_data[schema_name].get('examples'):
                        content['examples'] = raml_data[schema_name]['examples']

    # Add paths and parameters from HTML data if they don't exist
    for endpoint in html_data:
        path = endpoint['path']
        method = endpoint['method'].lower()

        if path not in openapi_data['paths']:
            openapi_data['paths'][path] = {}
        if method not in openapi_data['paths'][path]:
            openapi_data['paths'][path][method] = {'responses': {}, 'parameters': []}

        openapi_endpoint = openapi_data['paths'][path][method]
        existing_params = {p['name'] for p in openapi_endpoint.get('parameters', []) if p.get('in') == 'query'}
        for param in endpoint.get('query_params', []):
            if param['name'] not in existing_params:
                 openapi_endpoint.setdefault('parameters', []).append({
                    'name': param['name'],
                    'in': 'query',
                    'description': param.get('description', ''),
                    'schema': {'type': 'string'}
                })

    # Write the updated data back to the OpenAPI file
    write_yaml_file(openapi_data, 'openapi.yaml')
    print("Successfully cleaned and updated openapi.yaml.")

if __name__ == '__main__':
    update_openapi_spec()
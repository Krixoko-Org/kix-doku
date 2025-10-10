import json
import yaml

def load_json_file(file_path):
    """Loads a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_yaml_file(file_path):
    """Loads a YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def write_yaml_file(data, file_path):
    """Writes data to a YAML file."""
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, indent=2)

def convert_raml_param_to_openapi(param_name, param_details):
    """Converts a RAML parameter to OpenAPI 3.0 format."""
    if not isinstance(param_details, dict):
        return None
    return {
        'name': param_name,
        'in': 'query',
        'description': param_details.get('description', param_details.get('displayName', '')),
        'required': param_details.get('required', False),
        'schema': {'type': param_details.get('type', 'string')}
    }

def main():
    """
    Updates the OpenAPI specification with comprehensive data from RAML files.
    """
    print("Starting OpenAPI specification update...")

    raml_data = load_json_file('raml_api_details.json')
    openapi_data = load_yaml_file('openapi.yaml')

    # 1. Update/Create schemas in the components section
    print("Updating component schemas...")
    schemas = openapi_data.setdefault('components', {}).setdefault('schemas', {})
    for schema_name, schema_details in raml_data.get('schemas', {}).items():
        if schema_details.get('properties'):
            schemas[schema_name] = {
                'type': 'object',
                'properties': schema_details.get('properties', {})
            }

    # 2. Update paths with parameters and response examples/schemas
    print("Updating paths with parameters and response data...")
    paths = openapi_data.get('paths', {})
    for path, methods in raml_data.get('paths', {}).items():
        if path not in paths:
            continue

        for method, details in methods.items():
            if method not in paths[path]:
                continue

            openapi_endpoint = paths[path][method]

            # Add Query Parameters
            if details.get('parameters'):
                if 'parameters' not in openapi_endpoint:
                    openapi_endpoint['parameters'] = []
                existing_params = {p['name'] for p in openapi_endpoint['parameters'] if p.get('in') == 'query'}

                for name, deets in details['parameters'].items():
                    if name not in existing_params:
                        param = convert_raml_param_to_openapi(name, deets)
                        if param:
                            openapi_endpoint['parameters'].append(param)

            # Add Response schemas and examples
            if details.get('responses'):
                for code, response_def in details['responses'].items():
                    if not isinstance(response_def, dict): continue

                    openapi_response = openapi_endpoint.setdefault('responses', {}).setdefault(str(code), {})
                    if 'description' not in openapi_response:
                        openapi_response['description'] = response_def.get('description', "No description provided.")

                    content = openapi_response.setdefault('content', {}).setdefault('application/json', {})

                    body = response_def.get('body', {}).get('application/json', {})
                    if 'type' in body and isinstance(body['type'], str):
                        schema_name = body['type']
                        if schema_name in schemas:
                            content['schema'] = {'$ref': f'#/components/schemas/{schema_name}'}

                            schema_examples = raml_data.get('schemas', {}).get(schema_name, {}).get('examples')
                            if schema_examples:
                                # **Crucially, remove singular 'example' if 'examples' is being added**
                                if 'example' in content:
                                    del content['example']
                                content['examples'] = schema_examples

    # Write the final, complete file
    write_yaml_file(openapi_data, 'openapi.yaml')
    print("\\nSuccessfully updated openapi.yaml with comprehensive RAML data.")

if __name__ == '__main__':
    main()
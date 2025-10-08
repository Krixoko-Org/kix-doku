import json
import yaml

def update_openapi_spec():
    with open('parsed_api.json', 'r') as f:
        html_data = json.load(f)

    with open('openapi.yaml', 'r') as f:
        openapi_data = yaml.safe_load(f)

    for endpoint in html_data:
        path = endpoint['path']
        method = endpoint['method'].lower()
        html_params = endpoint.get('query_params', [])
        html_examples = endpoint.get('response_examples', {})

        if path not in openapi_data['paths']:
            openapi_data['paths'][path] = {}

        if method not in openapi_data['paths'][path]:
            openapi_data['paths'][path][method] = {
                'responses': {},
                'parameters': []
            }

        openapi_endpoint = openapi_data['paths'][path][method]
        openapi_params = openapi_endpoint.get('parameters', [])
        openapi_param_names = [p['name'] for p in openapi_params if p.get('in') == 'query']

        for param in html_params:
            if param['name'] not in openapi_param_names:
                openapi_params.append({
                    'name': param['name'],
                    'in': 'query',
                    'description': param.get('description', ''),
                    'schema': {'type': 'string'}
                })

        openapi_endpoint['parameters'] = openapi_params

        if '200' in html_examples:
            if 'responses' not in openapi_endpoint:
                openapi_endpoint['responses'] = {}
            if '200' not in openapi_endpoint['responses']:
                openapi_endpoint['responses']['200'] = {
                    'description': 'Successful response',
                    'content': {
                        'application/json': {
                            'example': html_examples['200']
                        }
                    }
                }
            elif 'content' not in openapi_endpoint['responses']['200'] or \
                 'application/json' not in openapi_endpoint['responses']['200']['content'] or \
                 'example' not in openapi_endpoint['responses']['200']['content']['application/json']:
                if 'content' not in openapi_endpoint['responses']['200']:
                    openapi_endpoint['responses']['200']['content'] = {}
                if 'application/json' not in openapi_endpoint['responses']['200']['content']:
                    openapi_endpoint['responses']['200']['content']['application/json'] = {}
                openapi_endpoint['responses']['200']['content']['application/json']['example'] = html_examples['200']


    with open('openapi.yaml', 'w') as f:
        yaml.dump(openapi_data, f, default_flow_style=False)

if __name__ == '__main__':
    update_openapi_spec()
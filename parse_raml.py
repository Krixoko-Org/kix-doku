import os
import yaml
import requests
import json
from urllib.parse import urljoin

BASE_URL = "https://raw.githubusercontent.com/krixoko/kix-backend/master/doc/API/V1/"

def get_url_content(url):
    """Fetches content from a URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def get_raml_content(file_path):
    """Fetches RAML file content from the given path relative to BASE_URL."""
    url = urljoin(BASE_URL, file_path)
    return get_url_content(url)

def yaml_loader_with_include():
    """Creates a YAML loader that can handle !include tags."""
    loader = yaml.SafeLoader

    def include_constructor(loader, node):
        """Handles the !include tag by returning the path."""
        return loader.construct_scalar(node)

    yaml.add_constructor('!include', include_constructor, Loader=loader)
    return loader

def parse_and_fetch_examples(examples, base_file_path):
    """
    Parses examples. If an example is a file path, it fetches its content.
    """
    parsed_examples = {}
    if not examples:
        return parsed_examples

    base_dir = os.path.dirname(base_file_path)

    for key, value in examples.items():
        if isinstance(value, str) and (value.endswith('.json') or value.endswith('.yaml') or value.endswith('.raml')):
            example_file_path = os.path.normpath(os.path.join(base_dir, value))
            try:
                example_content_str = get_raml_content(example_file_path)
                try:
                    example_content = json.loads(example_content_str)
                except json.JSONDecodeError:
                    example_content = yaml.safe_load(example_content_str)

                parsed_examples[key] = {'value': example_content}

            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not fetch example from {example_file_path}. {e}")
                parsed_examples[key] = {'value': f"Error fetching example: {e}"}
            except (yaml.YAMLError, json.JSONDecodeError) as e:
                 print(f"Warning: Could not parse example from {example_file_path}. {e}")
                 parsed_examples[key] = {'value': f"Error parsing example: {e}"}
        elif isinstance(value, str):
            try:
                parsed_examples[key] = {'value': json.loads(value)}
            except json.JSONDecodeError:
                try:
                    parsed_examples[key] = {'value': yaml.safe_load(value)}
                except yaml.YAMLError:
                    parsed_examples[key] = {'value': value}
        else:
            parsed_examples[key] = {'value': value}

    return parsed_examples

def main():
    """
    Parses RAML files to extract type definitions and examples,
    and saves them to a JSON file.
    """
    api_details = {}
    loader = yaml_loader_with_include()
    main_types_path = "lib/types.raml"

    try:
        main_types_content = get_raml_content(main_types_path)
        main_types_data = yaml.load(main_types_content, Loader=loader)

        for type_name, included_path in main_types_data.items():
            if not isinstance(included_path, str):
                continue

            type_file_path = os.path.normpath(os.path.join(os.path.dirname(main_types_path), included_path))

            try:
                type_content = get_raml_content(type_file_path)
                type_data = yaml.load(type_content, Loader=loader)

                if isinstance(type_data, dict):
                    properties = type_data.get('properties', {})
                    examples = type_data.get('examples', {})
                    if 'example' in type_data:
                        examples['default'] = type_data['example']

                    parsed_examples = parse_and_fetch_examples(examples, type_file_path)

                    api_details[type_name] = {
                        'properties': properties,
                        'examples': parsed_examples
                    }

            except requests.exceptions.RequestException as e:
                print(f"Warning: Could not fetch {type_file_path}. {e}")
            except yaml.YAMLError as e:
                print(f"Warning: Could not parse YAML from {type_file_path}. {e}")

        with open("raml_api_details.json", "w") as f:
            json.dump(api_details, f, indent=2)

        print("Successfully extracted RAML data to raml_api_details.json")

    except (requests.exceptions.RequestException, yaml.YAMLError) as e:
        print(f"Error processing the main types file '{main_types_path}': {e}")

if __name__ == "__main__":
    main()
import os
import yaml
import json
import traceback
from pathlib import Path
from collections.abc import MutableMapping

def deep_merge(d1, d2):
    """Merges d2 into d1, modifying d1 in-place."""
    for k, v in d2.items():
        if k in d1 and isinstance(d1[k], dict) and isinstance(v, MutableMapping):
            deep_merge(d1[k], v)
        else:
            d1[k] = v
    return d1

BASE_DIR = Path('/tmp/kix-backend/doc/API/V1/')
file_cache = {}

def get_local_file_content_cached(file_path: Path):
    """Fetches content from a local file, using a cache to avoid re-reads."""
    str_path = str(file_path)
    if str_path in file_cache:
        return file_cache[str_path]

    if not file_path.is_file():
        return None

    content = file_path.read_text(encoding='utf-8')
    file_cache[str_path] = content
    return content

class CustomLoader(yaml.SafeLoader):
    """Custom YAML loader to keep track of the current file's directory."""
    pass

def include_constructor(loader, node):
    """Handles !include tags by resolving the path and parsing the content."""
    include_path_str = loader.construct_scalar(node)
    new_file_path = (loader.current_dir / include_path_str).resolve()

    content = get_local_file_content_cached(new_file_path)
    if content is None: return None

    if new_file_path.suffix in ['.yaml', '.raml']:
        try:
            return load_yaml_with_context(content, new_file_path)
        except yaml.YAMLError:
            return content
    elif new_file_path.suffix == '.json':
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content
    else:
        return content

yaml.add_constructor('!include', include_constructor, Loader=CustomLoader)

def load_yaml_with_context(content, file_path: Path):
    """Loads YAML content using a loader that has file path context."""
    loader = CustomLoader(content)
    loader.current_dir = file_path.parent
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()

def get_resolved_raml(entry_file: Path):
    """Parses a RAML file from the local filesystem, resolving all !include tags."""
    print("Resolving main RAML file from local clone...")
    content = get_local_file_content_cached(entry_file)
    return load_yaml_with_context(content, entry_file)

def extract_api_details(raml_data):
    """Extracts schemas, paths, methods, parameters, and responses from the resolved RAML data."""
    print("Extracting API details...")
    api_details = {"paths": {}, "schemas": {}}
    traits = raml_data.get('traits', {}) or {}
    resource_types = raml_data.get('resourceTypes', {}) or {}

    # 1. Extract all type definitions (schemas and examples)
    if 'types' in raml_data and raml_data['types']:
        for type_name, type_def in raml_data['types'].items():
            if not isinstance(type_def, dict): continue

            properties = type_def.get('properties', {})
            examples = type_def.get('examples', {})
            if 'example' in type_def and 'default' not in examples:
                examples['default'] = {'value': type_def['example']}

            api_details["schemas"][type_name] = {
                "properties": properties or {},
                "examples": examples or {}
            }

    # 2. Extract path and method details, resolving inheritance
    def resolve_resource(resource_def):
        if not isinstance(resource_def, dict) or 'type' not in resource_def:
            return resource_def

        type_ref = resource_def.get('type')

        if isinstance(type_ref, list):
            merged_base = {}
            for single_type_ref in type_ref:
                type_name = list(single_type_ref.keys())[0] if isinstance(single_type_ref, dict) else single_type_ref
                if type_name in resource_types:
                    base_type_def = resource_types[type_name]
                    resolved_base = resolve_resource(base_type_def)
                    deep_merge(merged_base, resolved_base)
            return deep_merge(merged_base, resource_def)

        type_name = type_ref if isinstance(type_ref, str) else list(type_ref.keys())[0]
        if type_name in resource_types:
            base_type_def = resource_types[type_name]
            resolved_base = resolve_resource(base_type_def)
            return deep_merge(resolved_base.copy(), resource_def)

        return resource_def

    def resolve_method(method_def):
        if not isinstance(method_def, dict) or 'is' not in method_def:
            return method_def

        final_def = {}
        if method_def.get('is'):
            for trait_ref in method_def['is']:
                trait_name = list(trait_ref.keys())[0] if isinstance(trait_ref, dict) else trait_ref
                if trait_name in traits and traits[trait_name]:
                    trait_def = traits[trait_name]
                    deep_merge(final_def, trait_def)

        deep_merge(final_def, method_def)
        return final_def

    def process_resource(path, resource_def):
        if not isinstance(resource_def, dict):
            return

        resolved_res = resolve_resource(resource_def)

        for key, value in resolved_res.items():
            if key in ['get', 'post', 'put', 'patch', 'delete']:
                method = key
                method_def = resolve_method(value or {})

                params = method_def.get('queryParameters')
                responses = method_def.get('responses')

                path_details = api_details["paths"].setdefault(path, {})
                path_details[method] = {
                    "parameters": params or {},
                    "responses": responses or {}
                }

            elif key.startswith('/'):
                new_path = path.rstrip('/') + key
                process_resource(new_path, value)

    for path, resource_def in raml_data.items():
        if path.startswith('/'):
            process_resource(path, resource_def)

    print("Finished extracting API details.")
    return api_details

def main():
    """Main function to parse RAML and save details to JSON."""
    print("Starting comprehensive RAML parsing...")
    entry_point = BASE_DIR / "KIX.raml"
    try:
        raml_data = get_resolved_raml(entry_point)

        if not raml_data:
            print("Failed to parse RAML data. Exiting.")
            return

        api_details = extract_api_details(raml_data)

        print("Saving data to raml_api_details.json...")
        with open("raml_api_details.json", "w") as f:
            json.dump(api_details, f, indent=2)

        print("Successfully extracted comprehensive API details.")

    except Exception as e:
        print(f"An error occurred: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
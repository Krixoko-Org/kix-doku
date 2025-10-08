import json
from bs4 import BeautifulSoup

def parse_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    soup = BeautifulSoup(html_content, 'lxml')
    api_data = []

    for resource_panel in soup.find_all('div', class_='panel panel-default resource'):
        for method_panel in resource_panel.find_all('div', class_='panel panel-white resource-modal'):
            h4_title = method_panel.find('h4', class_='panel-title')
            if not h4_title:
                continue

            path_tags = h4_title.find_all('span', class_='uri')
            path = ''.join(tag.text for tag in path_tags).strip()

            methods = [span.text.strip() for span in h4_title.find_all('span', class_=['badge_get', 'badge_post', 'badge_patch', 'badge_delete'])]

            modal = method_panel.find('div', class_='modal')
            if not modal:
                continue

            # Extract query parameters
            query_params = []
            param_table = modal.find('table', class_='param-table')
            if param_table:
                for row in param_table.find('tbody').find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        param_name = cols[0].text.strip()
                        param_type = cols[2].text.strip()
                        param_desc = cols[4].text.strip()
                        query_params.append({
                            'name': param_name,
                            'type': param_type,
                            'description': param_desc
                        })

            # Extract response examples
            response_examples = []
            for response_div in modal.find_all('div', class_='response'):
                status_code_tag = response_div.find_previous_sibling('h2', class_='response-title')
                if status_code_tag:
                    status_code_text = status_code_tag.text.strip()
                    status_code = status_code_text.split(' ')[-1]

                    example_pre = response_div.find('div', class_='examples toggleable')
                    if example_pre:
                        example_code = example_pre.find('code')
                        if example_code:
                            response_examples.append({
                                'status_code': status_code,
                                'example': example_code.text.strip()
                            })

            for method in methods:
                api_data.append({
                    'path': path,
                    'method': method.upper(),
                    'query_params': query_params,
                    'response_examples': response_examples
                })

    return api_data

if __name__ == '__main__':
    parsed_data = parse_html('kix_api_docs.html')
    with open('parsed_api_v2.json', 'w') as f:
        json.dump(parsed_data, f, indent=4)
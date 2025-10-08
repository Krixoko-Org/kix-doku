import json
from bs4 import BeautifulSoup

def parse_html_docs(html_content):
    soup = BeautifulSoup(html_content, 'lxml')
    endpoints = []

    for panel_heading in soup.find_all('div', class_='panel-heading'):
        endpoint_data = {
            'path': '',
            'method': '',
            'parameters': [],
            'responses': {}
        }

        # Extract endpoint path and method from the panel-heading div
        text = panel_heading.get_text().strip()
        if 'GET /' in text or 'POST /' in text:
            parts = text.split()
            endpoint_data['method'] = parts[0]
            endpoint_data['path'] = parts[1]

            # Find the panel-body which should contain parameters
            panel_body = panel_heading.find_next_sibling('div', class_='panel-body')
            if panel_body:
                table = panel_body.find('table')
                if table:
                    for row in table.find_all('tr')[1:]:  # Skip header row
                        cols = row.find_all('td')
                        if len(cols) >= 2:
                            param_name = cols[0].get_text(strip=True)
                            param_description = cols[1].get_text(strip=True)
                            endpoint_data['parameters'].append({
                                'name': param_name,
                                'in': 'query',
                                'description': param_description,
                                'schema': {'type': 'string'}
                            })

            # Find response examples
            if panel_body:
                for h3 in panel_body.find_all('h3'):
                    if 'Example' in h3.get_text():
                        pre = h3.find_next_sibling('pre')
                    if pre:
                        try:
                            # Assuming the example is for a 200 response
                            response_body = json.loads(pre.get_text())
                            endpoint_data['responses']['200'] = {
                                'description': 'Successful response',
                                'content': {
                                    'application/json': {
                                        'example': response_body
                                    }
                                }
                            }
                        except json.JSONDecodeError:
                            # Handle cases where the example is not valid JSON
                            pass

        if endpoint_data['path']:
            endpoints.append(endpoint_data)

    return endpoints

if __name__ == '__main__':
    with open('kix_api_docs.html', 'r') as f:
        html = f.read()

    api_endpoints = parse_html_docs(html)
    print(json.dumps(api_endpoints, indent=2))
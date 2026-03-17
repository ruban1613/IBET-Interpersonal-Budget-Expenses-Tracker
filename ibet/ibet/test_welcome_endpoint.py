import requests

# Test the welcome endpoints for all wallet modules
modules = [
    ('couple', 'couple'),
    ('individual', 'individual'),
    ('retiree', 'retiree'),
    ('student', 'student'),
    ('parent', 'parent'),
    ('dailywage', 'dailywage')
]

headers = {'Authorization': 'Token c9dfd93eaea058a9e763a214a03833b5b7bb289c'}  # Using the token from get_token.py

for module_name, url_prefix in modules:
    url = f'http://127.0.0.1:8000/api/{url_prefix}/wallet/welcome/'
    print(f'\nTesting {module_name} wallet welcome endpoint...')
    try:
        response = requests.get(url, headers=headers)
        print(f'Status Code: {response.status_code}')
        print(f'Response: {response.text}')
        if response.status_code == 200:
            print(f'{module_name.capitalize()} wallet welcome endpoint test successful!')
        else:
            print(f'{module_name.capitalize()} wallet welcome endpoint test failed!')
    except Exception as e:
        print(f'Error testing {module_name} wallet: {e}')

print('\nAll welcome endpoint tests completed!')

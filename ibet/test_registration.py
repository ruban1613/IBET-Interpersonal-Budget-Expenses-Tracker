import requests
import json

# Test registration endpoint
url = 'http://127.0.0.1:8000/api/auth/register/'
headers = {'Content-Type': 'application/json'}
data = {
    'username': 'testuser791',
    'email': 'test791@example.com',
    'password': 'testpass123',
    'full_name': 'Test User',
    'phone': '1234567890',
    'persona': 'INDIVIDUAL'
}

try:
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')
    if response.status_code == 201:
        print('Registration successful!')
    else:
        print('Registration failed!')
except Exception as e:
    print(f'Error: {e}')

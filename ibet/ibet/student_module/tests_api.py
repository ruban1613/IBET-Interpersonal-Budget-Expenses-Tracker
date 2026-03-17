from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import override_settings
from .models import Category, Budget, Transaction

User = get_user_model()

@override_settings(SECURE_SSL_REDIRECT=False, CSRF_COOKIE_SECURE=False, SESSION_COOKIE_SECURE=False)
class StudentModuleAPITest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='apitestuser', password='testpass123')
        self.client.force_authenticate(user=self.user)
        self.category_data = {'name': 'Test Category', 'user': self.user.id}
        self.budget_data = {
            'user': self.user.id,
            'category': None,  # to be set after category creation
            'start_date': '2023-01-01',
            'end_date': '2023-01-31',
            'amount': '1000.00'
        }
        self.transaction_data = {
            'amount': '100.00',
            'transaction_type': 'EXP',
            'category': None,  # to be set after category creation
            'description': 'Test transaction',
            'transaction_date': '2023-01-15'
        }

    def test_category_crud(self):
        # Create category
        response = self.client.post('/api/categories/', {'name': 'Food'}, format='json')
        print(f"Response status: {response.status_code}")
        print(f"Response content: {response.content}")
        print(f"Response headers: {response.headers}")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data['id']

        # Update budget_data and transaction_data with category id
        self.budget_data['category'] = category_id
        self.transaction_data['category'] = category_id

        # Retrieve category
        response = self.client.get(f'/api/categories/{category_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Food')

        # List categories
        response = self.client.get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(cat['id'] == category_id for cat in response.data))

        # Delete category
        response = self.client.delete(f'/api/categories/{category_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_budget_crud(self):
        # Create category first
        response = self.client.post('/api/categories/', {'name': 'BudgetCat'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data['id']
        self.budget_data['category'] = category_id

        # Create budget
        response = self.client.post('/api/budgets/', self.budget_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        budget_id = response.data['id']

        # Retrieve budget
        response = self.client.get(f'/api/budgets/{budget_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '1000.00')

        # Update budget
        response = self.client.patch(f'/api/budgets/{budget_id}/', {'amount': '1200.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '1200.00')

        # Delete budget
        response = self.client.delete(f'/api/budgets/{budget_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_transaction_crud(self):
        # Create category first
        response = self.client.post('/api/categories/', {'name': 'TransCat'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        category_id = response.data['id']
        self.transaction_data['category'] = category_id

        # Create transaction
        response = self.client.post('/api/transactions/', self.transaction_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        transaction_id = response.data['id']

        # Retrieve transaction
        response = self.client.get(f'/api/transactions/{transaction_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['description'], 'Test transaction')

        # Update transaction
        response = self.client.patch(f'/api/transactions/{transaction_id}/', {'amount': '150.00'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['amount'], '150.00')

        # Delete transaction
        response = self.client.delete(f'/api/transactions/{transaction_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

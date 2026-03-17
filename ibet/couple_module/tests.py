from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import CoupleLink, SharedWallet, SpendingRequest

User = get_user_model()


class CoupleModuleTestCase(APITestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

    def test_create_couple_relationship(self):
        """Test creating a couple relationship"""
        self.client.force_authenticate(user=self.user1)

        url = reverse('create-couple')
        response = self.client.post(url, {
            'partner_username': 'testuser2'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(CoupleLink.objects.filter(
            user1=self.user1,
            user2=self.user2
        ).exists())

    def test_spending_request_workflow(self):
        """Test the complete spending request workflow"""
        # Create couple
        couple = CoupleLink.objects.create(user1=self.user1, user2=self.user2)
        wallet = SharedWallet.objects.create(couple=couple, balance=1000.00)

        url = reverse('spending-request-list')
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(url, {
            'amount': 100.00,
            'description': 'Dinner date',
            'category': 'Food'
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        request_id = response.data['id']

        url_respond = reverse('spending-request-respond', args=[request_id])
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(url_respond, {
            'action': 'approve'
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check wallet balance
        wallet.refresh_from_db()
        self.assertEqual(wallet.balance, 900.00)

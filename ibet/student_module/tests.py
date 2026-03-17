from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db.utils import IntegrityError
from datetime import date
from decimal import Decimal
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse

from .models import Budget, Category, Transaction, UserPersona, Reminder

User = get_user_model()

class UserModelTest(TestCase):
    def test_create_user_with_default_persona(self):
        user = User.objects.create_user(username='testuser', password='password123')
        self.assertEqual(user.username, 'testuser')
        self.assertIsNone(user.persona)  # Default is null
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_with_custom_persona(self):
        user = User.objects.create_user(
            username='studentuser',
            password='password123'
        )
        user.persona = UserPersona.STUDENT
        user.save()
        self.assertEqual(user.username, 'studentuser')
        self.assertEqual(user.persona, UserPersona.STUDENT)

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            username='admin',
            password='adminpassword',
            email='admin@example.com'
        )
        self.assertEqual(superuser.username, 'admin')
        self.assertTrue(superuser.is_staff)
        self.assertTrue(superuser.is_superuser)

    def test_user_str_representation(self):
        user = User.objects.create_user(username='struser', password='password123')
        self.assertEqual(str(user), 'struser')

class BudgetModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='budgetuser', password='password123')
        self.category = Category.objects.create(name='Food', user=self.user)

    def test_create_budget(self):
        start_date = date(2023, 1, 1)
        end_date = date(2023, 1, 31)
        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            start_date=start_date,
            end_date=end_date,
            amount=Decimal('1000.00')
        )
        self.assertEqual(budget.user, self.user)
        self.assertEqual(budget.start_date, start_date)
        self.assertEqual(budget.end_date, end_date)
        self.assertEqual(budget.amount, Decimal('1000.00'))

    def test_budget_str_representation(self):
        start_date = date(2023, 3, 1)
        end_date = date(2023, 3, 31)
        budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            start_date=start_date,
            end_date=end_date,
            amount=Decimal('1200.00')
        )
        self.assertEqual(str(budget), "budgetuser's budget for Food")

class CategoryModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='catuser', password='password123')

    def test_create_category(self):
        category = Category.objects.create(name='Food', user=self.user)
        self.assertEqual(category.name, 'Food')
        self.assertEqual(category.user, self.user)

    def test_category_str_representation(self):
        category = Category.objects.create(name='Transport', user=self.user)
        self.assertEqual(str(category), 'Transport')

class TransactionModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='transuser', password='password123')
        self.category_food = Category.objects.create(name='Food', user=self.user)
        self.category_salary = Category.objects.create(name='Salary', user=self.user)
        self.transaction_date = date(2023, 4, 15)

    def test_create_expense_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('50.00'),
            transaction_type=Transaction.TransactionType.EXPENSE,
            category=self.category_food,
            description='Groceries',
            transaction_date=self.transaction_date
        )
        self.assertEqual(transaction.user, self.user)
        self.assertEqual(transaction.amount, Decimal('50.00'))
        self.assertEqual(transaction.transaction_type, Transaction.TransactionType.EXPENSE)
        self.assertEqual(transaction.category, self.category_food)
        self.assertEqual(transaction.description, 'Groceries')
        self.assertEqual(transaction.transaction_date, self.transaction_date)

    def test_create_income_transaction(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('2000.00'),
            transaction_type=Transaction.TransactionType.INCOME,
            category=self.category_salary,
            description='Monthly Salary',
            transaction_date=self.transaction_date
        )
        self.assertEqual(transaction.transaction_type, Transaction.TransactionType.INCOME)
        self.assertEqual(transaction.amount, Decimal('2000.00'))

    def test_transaction_optional_fields(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('10.00'),
            transaction_type=Transaction.TransactionType.EXPENSE,
            category=self.category_food,
            description='',  # description is optional
            transaction_date=self.transaction_date
        )
        self.assertEqual(transaction.description, '')

    def test_transaction_str_representation(self):
        transaction = Transaction.objects.create(
            user=self.user,
            amount=Decimal('75.50'),
            transaction_type=Transaction.TransactionType.EXPENSE,
            category=self.category_food,
            transaction_date=self.transaction_date
        )
        self.assertEqual(str(transaction), "EXP of 75.50 for transuser")

class ReminderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reminderuser', password='password123')
        self.category = Category.objects.create(name='Food', user=self.user)
        self.budget = Budget.objects.create(
            user=self.user,
            category=self.category,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 1, 31),
            amount=Decimal('500.00')
        )

    def test_create_reminder(self):
        reminder = Reminder.objects.create(
            user=self.user,
            budget=self.budget,
            alert_percentage=70,
            is_active=True
        )
        self.assertEqual(reminder.user, self.user)
        self.assertEqual(reminder.budget, self.budget)
        self.assertEqual(reminder.alert_percentage, 70)
        self.assertTrue(reminder.is_active)

    def test_reminder_str_representation(self):
        reminder = Reminder.objects.create(
            user=self.user,
            budget=self.budget,
            alert_percentage=50,
            is_active=True
        )
        self.assertEqual(str(reminder), f"Reminder for {self.user.username} at 50%")

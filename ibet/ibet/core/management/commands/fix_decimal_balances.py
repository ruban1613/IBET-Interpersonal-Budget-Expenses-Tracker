from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fix corrupted decimal balances in all wallet tables'

    def handle(self, *args, **options):
        cursor = connection.cursor()

        # Fix all balances in all wallet tables
        tables = [
            'dailywage_module_dailywagewallet',
            'individual_module_individualwallet',
            'couple_module_couplewallet',
            'retiree_module_retireewallet',
            'parent_module_parentwallet',
            'student_module_studentwallet'
        ]

        for table in tables:
            try:
                cursor.execute(f'UPDATE {table} SET balance = printf("%.2f", balance)')
                self.stdout.write(self.style.SUCCESS(f'Updated {table}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error updating {table}: {e}'))

        connection.commit()
        self.stdout.write(self.style.SUCCESS('All balances fixed'))

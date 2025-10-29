from django.core.management.base import BaseCommand
from core.models import Ref_Account_Type

class Command(BaseCommand):
    help = 'Fix account type data issues'

    def handle(self, *args, **options):
        # Fix the long name issue
        try:
            # Find the record with ID 54 that failed due to long name
            long_name_record = Ref_Account_Type.objects.filter(AccountTypeId=54).first()
            if long_name_record:
                # Truncate the name to fit within 100 characters
                long_name_record.AccountTypeName = "Борлуулах зорилгоор эзэмшиж буй эргэлтийн бус хөрөнгө (борлуулах бүлэг хөрөнгө) - нд хамаарах өр төлбөр"[:100]
                long_name_record.CT1 = 39
                long_name_record.CT2 = 0
                long_name_record.IsActive = True
                long_name_record.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Fixed long name record: {long_name_record.AccountTypeCode}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fixing long name record: {str(e)}')
            )

        # Fix duplicate records by updating them with different IDs
        try:
            # Handle the duplicate 5701 records
            existing_5701 = Ref_Account_Type.objects.filter(AccountTypeCode='5701').first()
            if existing_5701:
                # Update the existing one to be "Бусад олз"
                existing_5701.AccountTypeName = "Бусад олз"
                existing_5701.CT1 = 0
                existing_5701.CT2 = 0
                existing_5701.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated existing 5701: {existing_5701.AccountTypeName}')
                )

            # Handle the duplicate 5702 records
            existing_5702 = Ref_Account_Type.objects.filter(AccountTypeCode='5702').first()
            if existing_5702:
                # Update the existing one to be "Бусад гарз"
                existing_5702.AccountTypeName = "Бусад гарз"
                existing_5702.CT1 = 0
                existing_5702.CT2 = 0
                existing_5702.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated existing 5702: {existing_5702.AccountTypeName}')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error fixing duplicate records: {str(e)}')
            )

        # Create the missing record with ID 54
        try:
            missing_record, created = Ref_Account_Type.objects.get_or_create(
                AccountTypeId=54,
                defaults={
                    'AccountTypeCode': '3901',
                    'AccountTypeName': 'Борлуулах зорилгоор эзэмшиж буй эргэлтийн бус хөрөнгө (борлуулах бүлэг хөрөнгө) - нд хамаарах өр төлбөр'[:100],
                    'CT1': 39,
                    'CT2': 0,
                    'IsActive': True
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created missing record: {missing_record.AccountTypeCode}')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating missing record: {str(e)}')
            )

        self.stdout.write(
            self.style.SUCCESS('\nFix completed!')
        )

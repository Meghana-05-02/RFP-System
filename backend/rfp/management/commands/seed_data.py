from django.core.management.base import BaseCommand
from rfp.models import Vendor, RFP, RFPItem
from decimal import Decimal


class Command(BaseCommand):
    help = 'Populate the database with sample vendors and RFPs for demo purposes'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))

        # Create vendors
        vendors_data = [
            {
                'name': 'Dell Technologies',
                'email': 'sales@dell.com',
                'contact_person': 'John Smith'
            },
            {
                'name': 'HP Inc.',
                'email': 'enterprise@hp.com',
                'contact_person': 'Sarah Johnson'
            },
            {
                'name': 'Lenovo',
                'email': 'business@lenovo.com',
                'contact_person': 'Michael Chen'
            }
        ]

        created_vendors = []
        for vendor_data in vendors_data:
            vendor, created = Vendor.objects.get_or_create(
                email=vendor_data['email'],
                defaults=vendor_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created vendor: {vendor.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'- Vendor already exists: {vendor.name}'))
            created_vendors.append(vendor)

        # Create sample RFP
        rfp_data = {
            'title': 'Office Laptop Procurement 2025',
            'natural_language_input': '''We need to procure high-quality laptops for our growing team. 
            
Requirements:
- Modern laptops suitable for software development and general office work
- Must support latest development tools and IDEs
- Good battery life (at least 8 hours)
- Warranty and support required

Please provide competitive pricing and delivery timeline.''',
            'budget': Decimal('150000.00'),
            'status': RFP.Status.DRAFT
        }

        rfp, created = RFP.objects.get_or_create(
            title=rfp_data['title'],
            defaults=rfp_data
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created RFP: {rfp.title}'))

            # Create RFP items
            items_data = [
                {
                    'name': 'Developer Laptops',
                    'quantity': 25,
                    'specifications': 'Intel i7 or AMD Ryzen 7, 16GB RAM, 512GB SSD, 15.6" display'
                },
                {
                    'name': 'Office Laptops',
                    'quantity': 30,
                    'specifications': 'Intel i5 or AMD Ryzen 5, 8GB RAM, 256GB SSD, 14" display'
                },
                {
                    'name': 'Extended Warranty',
                    'quantity': 55,
                    'specifications': '3-year on-site warranty and support for all laptops'
                }
            ]

            for item_data in items_data:
                item = RFPItem.objects.create(
                    rfp=rfp,
                    **item_data
                )
                self.stdout.write(self.style.SUCCESS(f'  ✓ Added item: {item.name} (Qty: {item.quantity})'))
        else:
            self.stdout.write(self.style.WARNING(f'- RFP already exists: {rfp.title}'))

        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Vendors in database: {Vendor.objects.count()}')
        self.stdout.write(f'RFPs in database: {RFP.objects.count()}')
        self.stdout.write(f'RFP Items in database: {RFPItem.objects.count()}')
        self.stdout.write(self.style.SUCCESS('='*50))

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from rfp.models import Vendor

# Create vendor
vendor, created = Vendor.objects.get_or_create(
    email='meghana.nagaraj766@gmail.com',
    defaults={
        'name': 'Meghana Vendor',
        'contact_person': 'Meghana G N'
    }
)

if created:
    print(f'✓ Vendor created successfully!')
else:
    print(f'✓ Vendor already exists!')

print(f'ID: {vendor.id}')
print(f'Name: {vendor.name}')
print(f'Email: {vendor.email}')
print(f'Contact: {vendor.contact_person}')

import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from rfp.models import Vendor, RFP, Proposal

# Get the vendor
vendor = Vendor.objects.get(email='meghana.nagaraj766@gmail.com')
print(f'Vendor: {vendor.name} (ID: {vendor.id})')

# Get RFP #2 (since #5 doesn't exist)
try:
    rfp = RFP.objects.get(id=2)
    print(f'RFP: {rfp.title} (ID: {rfp.id})')
    
    # Create proposal
    proposal, created = Proposal.objects.get_or_create(
        rfp=rfp,
        vendor=vendor,
        defaults={
            'price': Decimal('15000.00'),
            'payment_terms': 'pay in installments',
            'warranty': '2 years',
            'raw_email_content': 'Price $ 15000\nPayment terms: pay in installments\nWarranty: 2 years'
        }
    )
    
    if created:
        print(f'\n✓ Proposal created successfully!')
    else:
        print(f'\n✓ Proposal already exists, updating...')
        proposal.price = Decimal('15000.00')
        proposal.payment_terms = 'pay in installments'
        proposal.warranty = '2 years'
        proposal.save()
        print(f'✓ Proposal updated!')
    
    print(f'\nProposal Details:')
    print(f'ID: {proposal.id}')
    print(f'RFP: {proposal.rfp.title}')
    print(f'Vendor: {proposal.vendor.name}')
    print(f'Price: ${proposal.price}')
    print(f'Payment Terms: {proposal.payment_terms}')
    print(f'Warranty: {proposal.warranty}')
    print(f'Submitted: {proposal.submitted_at}')
    
except RFP.DoesNotExist:
    print(f'\n✗ RFP with ID 5 not found!')
    print('\nAvailable RFPs:')
    for rfp in RFP.objects.all():
        print(f'  - ID: {rfp.id}, Title: {rfp.title}')

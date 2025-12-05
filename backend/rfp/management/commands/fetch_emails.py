"""
Django management command to fetch unseen emails from Gmail using IMAP.

Usage:
    python manage.py fetch_emails

Environment Variables Required:
    EMAIL_HOST: IMAP server (e.g., imap.gmail.com)
    EMAIL_HOST_USER: Gmail email address
    EMAIL_HOST_PASSWORD: Gmail app password (not regular password)
    GEMINI_API_KEY: Google Gemini API key for proposal extraction
"""
import imaplib
import email
import re
from email.header import decode_header
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from decimal import Decimal
import os
from dotenv import load_dotenv
from pathlib import Path

from rfp.models import Vendor, RFP, Proposal
from rfp.utils import extract_proposal_from_email


class Command(BaseCommand):
    help = 'Fetch unseen emails from Gmail using IMAP'

    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--mark-seen',
            action='store_true',
            help='Mark emails as seen after fetching (default: keep unseen)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Maximum number of emails to fetch (default: 10)',
        )
        parser.add_argument(
            '--create-proposals',
            action='store_true',
            help='Create Proposal records from emails (default: just print)',
        )

    def handle(self, *args, **options):
        """Main command handler."""
        self.stdout.write(self.style.SUCCESS('Starting email fetch...'))
        
        # Load environment variables
        env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Get email credentials from environment
        email_host = os.getenv('EMAIL_HOST', 'imap.gmail.com')
        email_user = os.getenv('EMAIL_HOST_USER')
        email_password = os.getenv('EMAIL_HOST_PASSWORD')
        
        # Validate credentials
        if not email_user or not email_password:
            self.stdout.write(
                self.style.ERROR(
                    'Error: EMAIL_HOST_USER and EMAIL_HOST_PASSWORD must be set in .env file'
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    '\nFor Gmail, you need to:\n'
                    '1. Enable 2-factor authentication\n'
                    '2. Generate an "App Password" at https://myaccount.google.com/apppasswords\n'
                    '3. Add to .env file:\n'
                    '   EMAIL_HOST=imap.gmail.com\n'
                    '   EMAIL_HOST_USER=your-email@gmail.com\n'
                    '   EMAIL_HOST_PASSWORD=your-app-password'
                )
            )
            return
        
        try:
            # Connect to Gmail IMAP server
            self.stdout.write(f'Connecting to {email_host}...')
            mail = imaplib.IMAP4_SSL(email_host)
            
            # Login
            self.stdout.write(f'Logging in as {email_user}...')
            mail.login(email_user, email_password)
            self.stdout.write(self.style.SUCCESS('✓ Login successful'))
            
            # Select inbox
            mail.select('inbox')
            self.stdout.write(self.style.SUCCESS('✓ Inbox selected'))
            
            # Search for unseen emails
            self.stdout.write('\nSearching for unseen emails...')
            status, messages = mail.search(None, 'UNSEEN')
            
            if status != 'OK':
                self.stdout.write(self.style.ERROR('Error searching for emails'))
                return
            
            # Get list of email IDs
            email_ids = messages[0].split()
            
            if not email_ids:
                self.stdout.write(self.style.WARNING('No unseen emails found'))
                mail.logout()
                return
            
            total_emails = len(email_ids)
            limit = options['limit']
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Found {total_emails} unseen email(s)'
                )
            )
            
            if total_emails > limit:
                self.stdout.write(
                    self.style.WARNING(
                        f'Limiting to {limit} emails (use --limit to change)'
                    )
                )
                email_ids = email_ids[:limit]
            
            # Process each email
            self.stdout.write('\n' + '=' * 80)
            
            proposals_created = 0
            proposals_failed = 0
            
            for idx, email_id in enumerate(email_ids, 1):
                self.stdout.write(f'\n📧 Email {idx}/{len(email_ids)}')
                self.stdout.write('-' * 80)
                
                # Fetch email data
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    self.stdout.write(
                        self.style.ERROR(f'Error fetching email {email_id}')
                    )
                    continue
                
                # Parse email
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        # Parse email content
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Get subject
                        subject = self._decode_header(msg.get('Subject', ''))
                        
                        # Get sender
                        sender = self._decode_header(msg.get('From', ''))
                        sender_email = self._extract_email_address(sender)
                        
                        # Get date
                        date = msg.get('Date', '')
                        
                        # Print email headers
                        self.stdout.write(f'From: {self.style.SUCCESS(sender)}')
                        self.stdout.write(f'Email: {sender_email}')
                        self.stdout.write(f'Subject: {self.style.WARNING(subject)}')
                        self.stdout.write(f'Date: {date}')
                        self.stdout.write('')
                        
                        # Get email body
                        body = self._get_email_body(msg)
                        
                        if body:
                            self.stdout.write('Body:')
                            self.stdout.write('-' * 40)
                            # Truncate very long bodies for display
                            if len(body) > 1000:
                                self.stdout.write(body[:1000] + '\n... (truncated)')
                            else:
                                self.stdout.write(body)
                        else:
                            self.stdout.write(
                                self.style.WARNING('(No text body found)')
                            )
                            body = ''
                        
                        # Process proposal creation if requested
                        if options['create_proposals'] and body:
                            self.stdout.write('\n' + '~' * 40)
                            self.stdout.write('Processing proposal creation...')
                            
                            success = self._create_proposal_from_email(
                                sender_email=sender_email,
                                subject=subject,
                                body=body
                            )
                            
                            if success:
                                proposals_created += 1
                                self.stdout.write(
                                    self.style.SUCCESS('✓ Proposal created successfully')
                                )
                            else:
                                proposals_failed += 1
                                self.stdout.write(
                                    self.style.ERROR('✗ Failed to create proposal')
                                )
                        
                        self.stdout.write('-' * 80)
                
                # Mark as seen if requested
                if options['mark_seen']:
                    mail.store(email_id, '+FLAGS', '\\Seen')
            
            # Summary
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✓ Processed {len(email_ids)} email(s) successfully'
                )
            )
            
            if options['create_proposals']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created {proposals_created} proposal(s)'
                    )
                )
                if proposals_failed > 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'⚠ Failed to create {proposals_failed} proposal(s)'
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Note: Proposals not created (use --create-proposals to enable)'
                    )
                )
            
            if not options['mark_seen']:
                self.stdout.write(
                    self.style.WARNING(
                        'Note: Emails remain marked as unseen (use --mark-seen to change)'
                    )
                )
            
            # Logout
            mail.logout()
            self.stdout.write(self.style.SUCCESS('✓ Logged out'))
            
        except imaplib.IMAP4.error as e:
            self.stdout.write(
                self.style.ERROR(
                    f'IMAP Error: {str(e)}\n'
                    'This is usually caused by:\n'
                    '1. Incorrect email or password\n'
                    '2. Using regular password instead of App Password\n'
                    '3. IMAP not enabled in Gmail settings'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def _decode_header(self, header_value: str) -> str:
        """
        Decode email header (subject, from, etc.).
        
        Args:
            header_value: Raw header value
            
        Returns:
            Decoded header string
        """
        if not header_value:
            return ''
        
        decoded_parts = decode_header(header_value)
        decoded_string = ''
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string

    def _get_email_body(self, msg: email.message.Message) -> str:
        """
        Extract email body from message.
        
        Args:
            msg: Email message object
            
        Returns:
            Email body text
        """
        body = ''
        
        # If message is multipart
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                
                # Skip attachments
                if 'attachment' in content_disposition:
                    continue
                
                # Get text/plain or text/html
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode()
                        break  # Prefer plain text
                    except:
                        continue
                elif content_type == 'text/html' and not body:
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        continue
        else:
            # Simple message
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                body = str(msg.get_payload())
        
        return body.strip()

    def _extract_email_address(self, sender: str) -> str:
        """
        Extract email address from sender string.
        
        Args:
            sender: Sender string (e.g., "John Doe <john@example.com>")
            
        Returns:
            Email address
        """
        # Try to extract email from angle brackets
        match = re.search(r'<(.+?)>', sender)
        if match:
            return match.group(1).strip()
        
        # If no angle brackets, assume the whole string is the email
        # Remove any display name
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
        if email_match:
            return email_match.group(0).strip()
        
        return sender.strip()

    def _extract_rfp_id_from_subject(self, subject: str) -> int | None:
        """
        Extract RFP ID from email subject.
        
        Looks for patterns like:
        - "Re: RFP #123"
        - "RFP Invitation: Laptop Procurement" (matches by title)
        - "Proposal for RFP ID: 5"
        
        Args:
            subject: Email subject line
            
        Returns:
            RFP ID or None
        """
        # Look for RFP #<number>
        match = re.search(r'RFP\s*#(\d+)', subject, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Look for RFP ID: <number>
        match = re.search(r'RFP\s+ID\s*:\s*#?(\d+)', subject, re.IGNORECASE)
        if match:
            return int(match.group(1))
        
        # Try to match by RFP title
        # Remove common reply prefixes
        clean_subject = re.sub(r'^(Re|Fwd?|Fw):\s*', '', subject, flags=re.IGNORECASE).strip()
        
        # Look for "RFP Invitation: <title>"
        match = re.search(r'RFP\s+Invitation:\s*(.+)', clean_subject, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            # Try to find RFP by title
            try:
                rfp = RFP.objects.filter(title__iexact=title).first()
                if rfp:
                    return rfp.id
            except:
                pass
        
        return None

    def _create_proposal_from_email(
        self,
        sender_email: str,
        subject: str,
        body: str
    ) -> bool:
        """
        Create a Proposal record from email data using Gemini extraction.
        
        Args:
            sender_email: Vendor's email address
            subject: Email subject
            body: Email body text
            
        Returns:
            True if proposal created successfully, False otherwise
        """
        try:
            # Find vendor by email
            vendor = Vendor.objects.filter(email__iexact=sender_email).first()
            
            if not vendor:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Vendor not found with email: {sender_email}'
                    )
                )
                return False
            
            self.stdout.write(f'  ✓ Vendor found: {vendor.name}')
            
            # Extract RFP ID from subject
            rfp_id = self._extract_rfp_id_from_subject(subject)
            
            if not rfp_id:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ Could not extract RFP ID from subject: {subject}'
                    )
                )
                return False
            
            # Get RFP
            try:
                rfp = RFP.objects.get(id=rfp_id)
                self.stdout.write(f'  ✓ RFP found: {rfp.title} (ID: {rfp.id})')
            except RFP.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(
                        f'  ⚠ RFP not found with ID: {rfp_id}'
                    )
                )
                return False
            
            # Extract proposal data using Gemini
            self.stdout.write('  🤖 Extracting proposal data with Gemini...')
            extracted_data = extract_proposal_from_email(body)
            
            if not extracted_data.get('success'):
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Gemini extraction failed: {extracted_data.get("error")}'
                    )
                )
                return False
            
            # Display extracted data
            self.stdout.write(f'  ✓ Price: ${extracted_data.get("price")}')
            self.stdout.write(f'  ✓ Payment Terms: {extracted_data.get("payment_terms")}')
            self.stdout.write(f'  ✓ Warranty: {extracted_data.get("warranty")}')
            
            # Create Proposal in database
            with transaction.atomic():
                # Check if proposal already exists
                existing_proposal = Proposal.objects.filter(
                    rfp=rfp,
                    vendor=vendor
                ).first()
                
                if existing_proposal:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠ Proposal already exists (ID: {existing_proposal.id}), updating...'
                        )
                    )
                    # Update existing proposal
                    if extracted_data.get('price') is not None:
                        existing_proposal.price = Decimal(str(extracted_data['price']))
                    existing_proposal.payment_terms = extracted_data.get('payment_terms') or ''
                    existing_proposal.warranty = extracted_data.get('warranty') or ''
                    existing_proposal.raw_email_content = body
                    existing_proposal.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Updated proposal ID: {existing_proposal.id}'
                        )
                    )
                else:
                    # Create new proposal
                    proposal = Proposal.objects.create(
                        rfp=rfp,
                        vendor=vendor,
                        price=Decimal(str(extracted_data['price'])) if extracted_data.get('price') else None,
                        payment_terms=extracted_data.get('payment_terms') or '',
                        warranty=extracted_data.get('warranty') or '',
                        raw_email_content=body
                    )
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created new proposal ID: {proposal.id}'
                        )
                    )
            
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'  ✗ Error creating proposal: {str(e)}'
                )
            )
            return False

from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any, List
from decimal import Decimal, InvalidOperation
from datetime import datetime

from .models import RFP, RFPItem, Vendor, Proposal
from .serializers import RFPSerializer, VendorSerializer
from .utils import extract_rfp_from_text
import google.generativeai as genai
import os


class RFPViewSet(viewsets.ModelViewSet):
    """
    ViewSet for RFP model providing CRUD operations and custom actions.
    
    list: GET /api/rfp/rfps/
    create: POST /api/rfp/rfps/
    retrieve: GET /api/rfp/rfps/{id}/
    update: PUT /api/rfp/rfps/{id}/
    partial_update: PATCH /api/rfp/rfps/{id}/
    destroy: DELETE /api/rfp/rfps/{id}/
    send_rfp_emails: POST /api/rfp/rfps/{id}/send_rfp_emails/
    """
    queryset = RFP.objects.all().order_by('-created_at')
    serializer_class = RFPSerializer
    
    @action(detail=True, methods=['post'], url_path='send-rfp-emails')
    def send_rfp_emails(self, request, pk=None):
        """
        Send RFP invitation emails to selected vendors.
        
        POST /api/rfp/rfps/{id}/send-rfp-emails/
        Body: {
            "vendor_ids": [1, 2, 3]
        }
        
        Returns:
            Success message with email send status
        """
        rfp = self.get_object()
        vendor_ids = request.data.get('vendor_ids', [])
        
        # Validate vendor_ids
        if not vendor_ids or not isinstance(vendor_ids, list):
            return Response(
                {'error': 'vendor_ids is required and must be a list'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get vendors
        vendors = Vendor.objects.filter(id__in=vendor_ids)
        
        if not vendors.exists():
            return Response(
                {'error': 'No valid vendors found with the provided IDs'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Prepare email content
        subject = f"RFP Invitation: {rfp.title}"
        
        # Build email body with RFP details
        email_body = f"""
Dear Vendor,

You are invited to submit a proposal for the following Request for Proposal (RFP):

RFP Title: {rfp.title}
RFP ID: #{rfp.id}
Budget: ${rfp.budget if rfp.budget else 'Not specified'}

Requirements:
{rfp.natural_language_input}

Items Requested:
"""
        
        # Add items to email body
        for idx, item in enumerate(rfp.items.all(), 1):
            email_body += f"\n{idx}. {item.name}"
            email_body += f"\n   Quantity: {item.quantity}"
            if item.specifications:
                email_body += f"\n   Specifications: {item.specifications}"
            email_body += "\n"
        
        email_body += """
Please submit your proposal at your earliest convenience.

Best regards,
RFP Management System
"""
        
        # Send emails and track results
        sent_count = 0
        failed_vendors = []
        
        for vendor in vendors:
            try:
                send_mail(
                    subject=subject,
                    message=email_body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[vendor.email],
                    fail_silently=False,
                )
                sent_count += 1
            except Exception as e:
                failed_vendors.append({
                    'vendor_id': vendor.id,
                    'vendor_name': vendor.name,
                    'error': str(e)
                })
        
        # Update RFP status to 'sent' if at least one email was sent
        if sent_count > 0:
            rfp.status = RFP.Status.SENT
            rfp.save()
        
        # Prepare response
        response_data = {
            'message': f'RFP emails sent successfully',
            'rfp_id': rfp.id,
            'rfp_title': rfp.title,
            'emails_sent': sent_count,
            'total_vendors': len(vendor_ids),
            'rfp_status': rfp.status,
        }
        
        if failed_vendors:
            response_data['failed_vendors'] = failed_vendors
            response_data['message'] = f'Sent {sent_count} emails, {len(failed_vendors)} failed'
        
        return Response(response_data, status=status.HTTP_200_OK)


class VendorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vendor model providing CRUD operations.
    
    list: GET /api/rfp/vendors/
    create: POST /api/rfp/vendors/
    retrieve: GET /api/rfp/vendors/{id}/
    update: PUT /api/rfp/vendors/{id}/
    partial_update: PATCH /api/rfp/vendors/{id}/
    destroy: DELETE /api/rfp/vendors/{id}/
    """
    queryset = Vendor.objects.all().order_by('-created_at')
    serializer_class = VendorSerializer
    
    def get_queryset(self):
        """
        Optionally filter vendors by name or email.
        """
        queryset = super().get_queryset()
        
        # Filter by name
        name = self.request.query_params.get('name', None)
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # Filter by email
        email = self.request.query_params.get('email', None)
        if email:
            queryset = queryset.filter(email__icontains=email)
        
        return queryset


@api_view(['GET'])
def get_rfp_detail(request, pk) -> Response:
    """
    Get RFP details by ID.
    
    GET /api/rfp/<id>/
    
    Returns:
        Serialized RFP data with nested items
    """
    rfp = get_object_or_404(RFP, pk=pk)
    serializer = RFPSerializer(rfp)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def get_rfp_comparison(request, rfp_id) -> Response:
    """
    Get RFP comparison view with all associated proposals.
    
    GET /api/rfp/comparison/<rfp_id>/
    
    Returns:
        JSON object containing:
        - RFP details (title, budget, items)
        - List of all proposals with vendor name, price, payment_terms, warranty
    """
    # Get RFP or return 404
    rfp = get_object_or_404(RFP, pk=rfp_id)
    
    # Get all proposals for this RFP
    proposals = Proposal.objects.filter(rfp=rfp).select_related('vendor')
    
    # Build RFP details
    rfp_data = {
        'id': rfp.id,
        'title': rfp.title,
        'budget': str(rfp.budget) if rfp.budget else None,
        'status': rfp.status,
        'natural_language_input': rfp.natural_language_input,
        'created_at': rfp.created_at.isoformat(),
        'items': [
            {
                'id': item.id,
                'name': item.name,
                'quantity': item.quantity,
                'specifications': item.specifications
            }
            for item in rfp.items.all()
        ]
    }
    
    # Build proposals list
    proposals_data = [
        {
            'id': proposal.id,
            'vendor_name': proposal.vendor.name,
            'vendor_email': proposal.vendor.email,
            'vendor_contact': proposal.vendor.contact_person,
            'price': str(proposal.price) if proposal.price else None,
            'payment_terms': proposal.payment_terms,
            'warranty': proposal.warranty,
            'submitted_at': proposal.submitted_at.isoformat(),
            'raw_email_content': proposal.raw_email_content[:200] + '...' if len(proposal.raw_email_content) > 200 else proposal.raw_email_content
        }
        for proposal in proposals
    ]
    
    # Return combined response
    response_data = {
        'rfp': rfp_data,
        'proposals': proposals_data,
        'proposal_count': len(proposals_data)
    }
    
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
def get_ai_recommendation(request, rfp_id) -> Response:
    """
    Get AI recommendation for choosing a vendor from proposals.
    
    POST /api/rfp/ai-recommendation/<rfp_id>/
    
    Returns:
        JSON object containing AI analysis and recommendation
    """
    # Get RFP or return 404
    rfp = get_object_or_404(RFP, pk=rfp_id)
    
    # Get all proposals for this RFP
    proposals = Proposal.objects.filter(rfp=rfp).select_related('vendor')
    
    if not proposals.exists():
        return Response(
            {'error': 'No proposals found for this RFP'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Configure Gemini API
    try:
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        return Response(
            {'error': f'Failed to configure Gemini API: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    # Build prompt with all proposal data
    prompt = f"""You are an expert procurement advisor. Analyze the following RFP and vendor proposals to recommend which vendor should be chosen and why.

RFP: {rfp.title}
Budget: ${rfp.budget if rfp.budget else 'Not specified'}
Requirements: {rfp.natural_language_input}

Vendor Proposals:
"""
    
    for idx, proposal in enumerate(proposals, 1):
        prompt += f"""
{idx}. {proposal.vendor.name}
   - Total Price: ${proposal.price if proposal.price else 'Not specified'}
   - Payment Terms: {proposal.payment_terms or 'Not specified'}
   - Warranty: {proposal.warranty or 'Not specified'}
"""
    
    prompt += """
Provide a clear recommendation on which vendor to choose and explain your reasoning. Consider price, payment terms, warranty, and overall value. Keep your response concise and professional."""
    
    try:
        # Generate AI recommendation
        response = model.generate_content(
            prompt,
            generation_config={
                'temperature': 0.3,
                'max_output_tokens': 1024,
            }
        )
        
        recommendation = response.text
        
        return Response(
            {
                'recommendation': recommendation,
                'rfp_id': rfp_id,
                'proposals_analyzed': len(proposals)
            },
            status=status.HTTP_200_OK
        )
    
    except Exception as e:
        return Response(
            {'error': f'Failed to generate AI recommendation: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def create_rfp_from_text(request) -> Response:
    """
    Create an RFP and associated RFPItems from natural language text.
    
    POST body:
        {
            "text": "Natural language description of RFP requirements"
        }
    
    Returns:
        Serialized RFP data with nested items
    """
    # Get text from request body
    text = request.data.get('text')
    
    # Validate input
    if not text:
        return Response(
            {'error': 'Text field is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if not isinstance(text, str) or not text.strip():
        return Response(
            {'error': 'Text must be a non-empty string'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Call the extraction utility
        extraction_result = extract_rfp_from_text(text)
        
        # Check if extraction was successful
        if not extraction_result.get('success', False):
            return Response(
                {
                    'error': 'Failed to extract RFP data',
                    'details': extraction_result.get('error', 'Unknown error')
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Create RFP and RFPItems in a transaction
        with transaction.atomic():
            # Create RFP object
            rfp = RFP.objects.create(
                title=extraction_result.get('title', 'Untitled RFP'),
                natural_language_input=text,
                budget=_parse_budget(extraction_result.get('budget')),
                status=RFP.Status.DRAFT
            )
            
            # Create RFPItem objects
            items_data = extraction_result.get('items', [])
            for item_data in items_data:
                RFPItem.objects.create(
                    rfp=rfp,
                    name=item_data.get('name', 'Unnamed Item'),
                    quantity=_parse_quantity(item_data.get('quantity', 1)),
                    specifications=item_data.get('specifications', '')
                )
            
            # Serialize and return the created RFP with items
            serializer = RFPSerializer(rfp)
            return Response(
                {
                    'message': 'RFP created successfully',
                    'rfp': serializer.data,
                    'extraction_metadata': {
                        'extracted_budget': extraction_result.get('budget'),
                        'extracted_deadline': extraction_result.get('deadline'),
                        'items_count': len(items_data)
                    }
                },
                status=status.HTTP_201_CREATED
            )
    
    except ValueError as e:
        return Response(
            {'error': f'Validation error: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    except Exception as e:
        return Response(
            {'error': f'Internal server error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def _parse_budget(budget_value: Any) -> Decimal | None:
    """
    Parse budget value to Decimal.
    
    Args:
        budget_value: Budget value (can be float, int, str, or None)
        
    Returns:
        Decimal value or None
    """
    if budget_value is None:
        return None
    
    try:
        return Decimal(str(budget_value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_quantity(quantity_value: Any) -> int:
    """
    Parse quantity value to integer.
    
    Args:
        quantity_value: Quantity value (can be int, float, str)
        
    Returns:
        Integer quantity (default 1 if parsing fails)
    """
    try:
        qty = int(quantity_value)
        return max(1, qty)  # Ensure at least 1
    except (ValueError, TypeError):
        return 1

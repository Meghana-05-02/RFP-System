from rest_framework import serializers
from .models import Vendor, RFP, RFPItem, Proposal
from typing import Any, Dict


class VendorSerializer(serializers.ModelSerializer):
    """Serializer for Vendor model."""

    class Meta:
        model = Vendor
        fields = [
            'id',
            'name',
            'email',
            'contact_person',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RFPItemSerializer(serializers.ModelSerializer):
    """Serializer for RFPItem model."""

    class Meta:
        model = RFPItem
        fields = [
            'id',
            'rfp',
            'name',
            'quantity',
            'specifications',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RFPSerializer(serializers.ModelSerializer):
    """Serializer for RFP model with nested read-only items."""

    items: serializers.ListSerializer = RFPItemSerializer(many=True, read_only=True)

    class Meta:
        model = RFP
        fields = [
            'id',
            'title',
            'natural_language_input',
            'budget',
            'status',
            'created_at',
            'updated_at',
            'items',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'items']


class ProposalSerializer(serializers.ModelSerializer):
    """Serializer for Proposal model."""

    class Meta:
        model = Proposal
        fields = [
            'id',
            'rfp',
            'vendor',
            'raw_email_content',
            'extracted_price',
            'extracted_terms',
            'ai_summary',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
